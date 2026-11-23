/*
 * ======================================================================================
 * Project: StudySense / Smart Study Monitor (Edge IoT Firmware v3.0)
 * Target:  ESP32 DevKit (Dual-Core Xtensa LX6 @ 240MHz)
 * Architecture: Non-blocking FreeRTOS loop, Multi-Sensor Fusion, Dual-Tier Alert Engine
 *
 * Hardware Pinout (Matches Physical Breadboard):
 *  - PIR Motion Sensor:    GPIO 27
 *  - HC-SR04 TRIG:         GPIO 13
 *  - HC-SR04 ECHO:         GPIO 14 (via 1kΩ/2kΩ voltage divider to 3.3V)
 *  - Push Button:          GPIO 22 (Active LOW, internal INPUT_PULLUP)
 *  - Active Buzzer:        GPIO 23 (via BC547 NPN transistor driver)
 *  - Green LED:            GPIO 26 (Study Active / Good Posture)
 *  - Blue LED:             GPIO 25 (Standby / Pause / Break Indicator)
 *  - Red LED:              GPIO 33 (Posture Warning & Absence Alarm)
 *
 * Behavioral Engine (Smart Journey Upgrades):
 *  1. Power-On: BLUE LED glows first (Standby). Starts in Manual Mode by default.
 *     Student must press the physical button to begin study.
 *  2. Button Tap (Normal): Toggle Study (Green ON) / Pause (Blue ON).
 *  3. Smart Fusion: PIR body movement + Ultrasonic distance eliminates false alarms
 *     from small static objects (cups, books, stationery).
 *  4. Posture Alert (Tier 1): If student leans < minPostureCm (<30cm), RED glows for
 *     exactly 3 seconds with a beep, then turns OFF waiting for clearance back to safe range.
 *  5. Absence Alarm (Tier 2): If student walks away during study:
 *     - RED glows 5 seconds (study timer paused, remaining time preserved).
 *     - 3 seconds grace period.
 *     - CONTINUOUS BUZZER + RED LED until student returns OR taps button!
 *  6. Single Button Tap during alarm immediately STOPS buzzer & resumes study session!
 * ======================================================================================
 */

#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ======================= 1. HARDWARE PIN DEFINITIONS =======================
constexpr uint8_t PIN_PIR       = 27;
constexpr uint8_t PIN_TRIG      = 13;
constexpr uint8_t PIN_ECHO      = 14; // Via 1k/2k voltage divider
constexpr uint8_t PIN_BUTTON    = 22; // Active LOW (INPUT_PULLUP)
constexpr uint8_t PIN_BUZZER    = 23; // Active Buzzer (BC547 base)
constexpr uint8_t PIN_LED_GREEN = 26; // Green LED (Optimal Study)
constexpr uint8_t PIN_LED_BLUE  = 25; // Blue LED (Standby / Break)
constexpr uint8_t PIN_LED_RED   = 33; // Red LED (Posture / Absence Alert)
constexpr uint8_t PIN_ONBOARD_LED = 2; // Onboard ESP32 Blue LED (Heartbeat / Diagnostic)

// ======================= 2. WI-FI & BLE CONFIGURATION ======================
const char* AP_SSID = "StudyMonitor";
const char* AP_PASS = "study1234";

IPAddress local_IP(192, 168, 4, 1);
IPAddress gateway(192, 168, 4, 1);
IPAddress subnet(255, 255, 255, 0);

WebServer server(80);
Preferences prefs;

// BLE UUIDs
#define BLE_SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define BLE_CHAR_STATUS_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a8" // Read & Notify
#define BLE_CHAR_COMMAND_UUID   "82896244-0853-4e43-996c-850c5a6c7b21" // Write Commands

BLEServer* pServer = nullptr;
BLECharacteristic* pStatusChar = nullptr;
BLECharacteristic* pCommandChar = nullptr;
bool bleClientConnected = false;

// ======================= 3. USER PROFILE STRUCTURE ========================
struct UserProfile {
  String name;
  uint16_t studyMins;       // Study duration (minutes)
  uint16_t breakMins;       // Break duration (minutes)
  uint16_t minPostureCm;    // Minimum safe posture distance (cm)
  uint16_t maxPresenceCm;   // Maximum desk distance for human presence (cm)
  bool buzzerEnabled;       // Buzzer alert toggle
  uint32_t studiedSecsToday;// Accumulated study seconds
};

UserProfile profiles[3] = {
  {"Student 1", 25, 5,  30, 85, true, 0},
  {"Student 2", 45, 10, 35, 85, true, 0},
  {"Student 3", 30, 5,  25, 85, true, 0}
};

uint8_t activeProfileIdx = 0; // 0, 1, or 2
bool isAutoMode = false;      // Manual Mode by default (Standby on boot)

// Session States
enum SessionState {
  STATE_IDLE = 0,   // Power-on / Standby (Blue LED)
  STATE_STUDY,      // Active studying (Green LED)
  STATE_PAUSED,     // Manually paused (Blue LED)
  STATE_BREAK       // Break time (Blue LED)
};

SessionState currentState = STATE_IDLE;
uint32_t remainingSeconds = 25 * 60;
uint32_t totalSessionSeconds = 25 * 60;

// ======================= 4. SMART ALERT STATE MACHINES =====================
// Alert Tier 1: Posture Warning (Slouching / Too Close)
enum PostureState {
  POSTURE_NORMAL = 0,
  POSTURE_WARNING_ACTIVE,    // RED LED ON for 3 seconds + alert beep
  POSTURE_WAITING_CLEARANCE  // RED LED OFF, waiting for safe distance clearance
};
PostureState postureState = POSTURE_NORMAL;
unsigned long postureWarningStartMs = 0;
unsigned long badPostureDebounceMs  = 0;
unsigned long safeDistanceClearMs   = 0;

// Alert Tier 2: Absence Warning & Continuous Alarm (Left Desk)
enum AbsenceState {
  ABSENCE_NORMAL = 0,
  ABSENCE_STAGE_WARNING,     // RED LED ON for 5 seconds (study timer paused)
  ABSENCE_STAGE_GRACE,       // 3 seconds extra grace period
  ABSENCE_CONTINUOUS_ALARM   // Continuous buzzer & RED LED until returned or button pressed
};
AbsenceState absenceState = ABSENCE_NORMAL;
unsigned long absenceStageStartMs = 0;

// Live Sensor Readings
float liveDistanceCm = 45.0f;
bool livePirMotion = false;
bool studentPresent = false;

// Timing Trackers (Non-blocking millis)
unsigned long lastSensorReadMs   = 0;
unsigned long lastSecondTickMs   = 0;
unsigned long lastPresenceSeenMs = 0;
unsigned long lastPirMotionMs    = 0;
unsigned long lastBleNotifyMs    = 0;

constexpr unsigned long SENSOR_INTERVAL_MS = 80; // High speed 12.5Hz sampling

// Button Debounce & Timing
bool lastBtnReading = HIGH;
bool btnState = HIGH;
unsigned long btnPressStartMs = 0;
bool longPressHandled = false;

// Non-Blocking Active Buzzer Engine
struct BuzzerJob {
  uint8_t beepsRemaining = 0;
  uint16_t onDurationMs = 100;
  uint16_t offDurationMs = 100;
  bool pinCurrentlyHigh = false;
  unsigned long lastToggleMs = 0;
} buzzer;

// Forward Declarations
void triggerBuzzer(uint8_t beeps, uint16_t onMs, uint16_t offMs);
void updateBuzzerEngine();
void handleShortButtonPress();
void handleLongButtonPress();
void setTimerForState(SessionState newState);
void updateLEDs(bool& outGreen, bool& outBlue, bool& outRed);
void saveProfileToPrefs(uint8_t idx);
void loadAllProfilesFromPrefs();
void saveSystemStateToPrefs();
void setupWebServer();
void sendCorsHeaders();
float readUltrasonicCm();
const char* getStateString(SessionState s);

// ======================= 5. BLE SERVER & COMMAND CALLBACKS =================
class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    bleClientConnected = true;
    Serial.println("[BLE] Client Connected");
  }
  void onDisconnect(BLEServer* pServer) override {
    bleClientConnected = false;
    Serial.println("[BLE] Client Disconnected -> Restarting Advertising");
    BLEDevice::startAdvertising();
  }
};

class CommandCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* pChar) override {
    String rx = pChar->getValue();
    if (rx.length() == 0) return;
    rx.trim();
    Serial.print("[BLE RX]: ");
    Serial.println(rx);

    if (rx == "START" || rx == "RESUME") {
      if (currentState == STATE_IDLE || currentState == STATE_PAUSED) {
        handleShortButtonPress();
      }
    } else if (rx == "PAUSE") {
      if (currentState == STATE_STUDY) {
        handleShortButtonPress();
      }
    } else if (rx == "DISMISS") {
      handleShortButtonPress();
    } else if (rx == "MODE_AUTO") {
      isAutoMode = true;
      saveSystemStateToPrefs();
      triggerBuzzer(2, 100, 80);
    } else if (rx == "MODE_MANUAL") {
      isAutoMode = false;
      saveSystemStateToPrefs();
      triggerBuzzer(1, 100, 80);
    } else if (rx.startsWith("SET_PROF:")) {
      int pIdx = rx.substring(9).toInt();
      if (pIdx >= 0 && pIdx < 3) {
        activeProfileIdx = pIdx;
        setTimerForState(STATE_IDLE);
        saveSystemStateToPrefs();
        triggerBuzzer(2, 60, 60);
      }
    }
  }
};

// ======================= 6. BUZZER DRIVER =================================
void triggerBuzzer(uint8_t beeps, uint16_t onMs, uint16_t offMs) {
  if (!profiles[activeProfileIdx].buzzerEnabled) return;
  buzzer.beepsRemaining = beeps;
  buzzer.onDurationMs = onMs;
  buzzer.offDurationMs = offMs;
  buzzer.pinCurrentlyHigh = true;
  buzzer.lastToggleMs = millis();
  digitalWrite(PIN_BUZZER, HIGH);
}

void updateBuzzerEngine() {
  // If continuous alarm is firing, keep buzzer active
  if (absenceState == ABSENCE_CONTINUOUS_ALARM && profiles[activeProfileIdx].buzzerEnabled) {
    digitalWrite(PIN_BUZZER, HIGH);
    return;
  }

  if (buzzer.beepsRemaining == 0) {
    digitalWrite(PIN_BUZZER, LOW);
    return;
  }

  unsigned long now = millis();
  if (buzzer.pinCurrentlyHigh) {
    if (now - buzzer.lastToggleMs >= buzzer.onDurationMs) {
      digitalWrite(PIN_BUZZER, LOW);
      buzzer.pinCurrentlyHigh = false;
      buzzer.lastToggleMs = now;
      buzzer.beepsRemaining--;
    }
  } else {
    if (now - buzzer.lastToggleMs >= buzzer.offDurationMs) {
      digitalWrite(PIN_BUZZER, HIGH);
      buzzer.pinCurrentlyHigh = true;
      buzzer.lastToggleMs = now;
    }
  }
}

// ======================= 7. SENSOR SAMPLING & FUSION =======================
float readUltrasonicCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  long duration = pulseIn(PIN_ECHO, HIGH, 25000); // 25ms timeout (~4.2m)
  if (duration == 0) return 400.0f; // Nothing in range / timeout
  float cm = (float)duration * 0.0343f / 2.0f;
  if (cm < 2.0f || cm > 400.0f) return 400.0f;
  return cm;
}

// ======================= 8. BUTTON HANDLING JOURNEY =======================
void handleShortButtonPress() {
  // HIGHEST PRIORITY 1: Dismiss active absence alarm or continuous buzzer
  if (absenceState != ABSENCE_NORMAL) {
    absenceState = ABSENCE_NORMAL;
    digitalWrite(PIN_BUZZER, LOW);
    lastPresenceSeenMs = millis();
    studentPresent = true;
    currentState = STATE_STUDY; // Resume study session with EXACT remaining seconds
    triggerBuzzer(1, 80, 50);
    return;
  }

  // PRIORITY 2: Dismiss active posture alert
  if (postureState != POSTURE_NORMAL) {
    postureState = POSTURE_NORMAL;
    badPostureDebounceMs = 0;
    triggerBuzzer(1, 80, 50);
    return;
  }

  // NORMAL JOURNEY STAGES:
  if (currentState == STATE_IDLE) {
    // Stage 1: From Standby (Blue) -> Start Study (Green)
    totalSessionSeconds = profiles[activeProfileIdx].studyMins * 60UL;
    remainingSeconds = totalSessionSeconds;
    currentState = STATE_STUDY;
    lastPresenceSeenMs = millis();
    studentPresent = true;
    triggerBuzzer(1, 80, 50);
  } else if (currentState == STATE_STUDY) {
    // Stage 2: From Study (Green) -> Pause Study (Blue), save time
    currentState = STATE_PAUSED;
    triggerBuzzer(1, 80, 50);
  } else if (currentState == STATE_PAUSED) {
    // Stage 3: From Paused (Blue) -> Resume Study (Green), same remaining time
    currentState = STATE_STUDY;
    lastPresenceSeenMs = millis();
    triggerBuzzer(1, 80, 50);
  } else if (currentState == STATE_BREAK) {
    // Break -> Skip break and start fresh study session
    setTimerForState(STATE_IDLE);
    triggerBuzzer(1, 80, 50);
  }
}

void handleLongButtonPress() {
  // During an active alarm, treat long press as alarm dismissal only (prevent accidental mode switch)
  if (absenceState != ABSENCE_NORMAL || postureState != POSTURE_NORMAL) {
    handleShortButtonPress();
    return;
  }

  // Toggle Operating Mode (Auto <-> Manual)
  isAutoMode = !isAutoMode;
  saveSystemStateToPrefs();
  triggerBuzzer(2, 160, 100); // 2 confirmation beeps
  Serial.print("[MODE TOGGLED]: ");
  Serial.println(isAutoMode ? "AUTOMATIC" : "MANUAL");
}

void setTimerForState(SessionState newState) {
  currentState = newState;
  UserProfile& p = profiles[activeProfileIdx];

  if (newState == STATE_IDLE || newState == STATE_STUDY) {
    totalSessionSeconds = p.studyMins * 60UL;
    remainingSeconds = totalSessionSeconds;
  } else if (newState == STATE_BREAK) {
    totalSessionSeconds = p.breakMins * 60UL;
    remainingSeconds = totalSessionSeconds;
  }
}

// ======================= 9. LED INDICATION ENGINE =========================
void updateLEDs(bool& outGreen, bool& outBlue, bool& outRed) {
  outGreen = false;
  outBlue  = false;
  outRed   = false;

  if (currentState == STATE_IDLE || currentState == STATE_PAUSED || currentState == STATE_BREAK) {
    // Standby / Paused / Break: BLUE LED ON
    outBlue  = true;
    outGreen = false;
    outRed   = false;
  } else if (currentState == STATE_STUDY) {
    if (absenceState == ABSENCE_STAGE_WARNING || absenceState == ABSENCE_CONTINUOUS_ALARM) {
      // Absence Warning (5s) or Continuous Alarm: RED LED ON
      outRed   = true;
      outGreen = false;
      outBlue  = false;
    } else if (absenceState == ABSENCE_STAGE_GRACE) {
      // 3s grace gap: Red OFF, Green OFF
      outRed   = false;
      outGreen = false;
      outBlue  = false;
    } else if (postureState == POSTURE_WARNING_ACTIVE) {
      // Posture Alert (3s): RED LED ON
      outRed   = true;
      outGreen = false;
      outBlue  = false;
    } else if (postureState == POSTURE_WAITING_CLEARANCE) {
      // Clearance wait: Red OFF, Green OFF
      outRed   = false;
      outGreen = false;
      outBlue  = false;
    } else {
      // Optimal studying: GREEN LED ON!
      outGreen = true;
      outBlue  = false;
      outRed   = false;
    }
  }

  digitalWrite(PIN_LED_GREEN, outGreen ? HIGH : LOW);
  digitalWrite(PIN_LED_BLUE,  outBlue  ? HIGH : LOW);
  digitalWrite(PIN_LED_RED,   outRed   ? HIGH : LOW);
}

// ======================= 10. PREFERENCES & FLASH STORAGE ===================
void saveProfileToPrefs(uint8_t idx) {
  if (idx >= 3) return;
  String prefix = "p" + String(idx) + "_";
  prefs.putString((prefix + "name").c_str(), profiles[idx].name);
  prefs.putUShort((prefix + "studyM").c_str(), profiles[idx].studyMins);
  prefs.putUShort((prefix + "breakM").c_str(), profiles[idx].breakMins);
  prefs.putUShort((prefix + "minCm").c_str(), profiles[idx].minPostureCm);
  prefs.putUShort((prefix + "maxCm").c_str(), profiles[idx].maxPresenceCm);
  prefs.putBool((prefix + "buzzer").c_str(), profiles[idx].buzzerEnabled);
  prefs.putUInt((prefix + "secs").c_str(), profiles[idx].studiedSecsToday);
}

void loadAllProfilesFromPrefs() {
  prefs.begin("studymon", false);
  activeProfileIdx = prefs.getUChar("activeIdx", 0);
  if (activeProfileIdx >= 3) activeProfileIdx = 0;

  for (uint8_t i = 0; i < 3; i++) {
    String prefix = "p" + String(i) + "_";
    String defName = "Student " + String(i + 1);
    profiles[i].name = prefs.getString((prefix + "name").c_str(), defName);
    profiles[i].studyMins = prefs.getUShort((prefix + "studyM").c_str(), (i == 1 ? 45 : (i == 2 ? 30 : 25)));
    profiles[i].breakMins = prefs.getUShort((prefix + "breakM").c_str(), (i == 1 ? 10 : 5));
    profiles[i].minPostureCm = prefs.getUShort((prefix + "minCm").c_str(), (i == 1 ? 35 : (i == 2 ? 25 : 30)));
    profiles[i].maxPresenceCm = prefs.getUShort((prefix + "maxCm").c_str(), 85);
    profiles[i].buzzerEnabled = prefs.getBool((prefix + "buzzer").c_str(), true);
    profiles[i].studiedSecsToday = prefs.getUInt((prefix + "secs").c_str(), 0);
  }
}

void saveSystemStateToPrefs() {
  prefs.putUChar("activeIdx", activeProfileIdx);
  prefs.putBool("autoMode", isAutoMode);
}

// ======================= 11. EMBEDDED WEB SERVER ===========================
const char* getStateString(SessionState s) {
  switch (s) {
    case STATE_IDLE:   return "STANDBY";
    case STATE_STUDY:  return "STUDYING";
    case STATE_PAUSED: return "PAUSED";
    case STATE_BREAK:  return "BREAK";
    default:           return "STANDBY";
  }
}

void sendCorsHeaders() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

String buildStatusJson() {
  bool ledG, ledB, ledR;
  updateLEDs(ledG, ledB, ledR);

  String json = "{";
  json += "\"activeProfile\":" + String(activeProfileIdx) + ",";
  json += "\"autoMode\":" + String(isAutoMode ? "true" : "false") + ",";
  json += "\"state\":" + String((int)currentState) + ",";
  json += "\"stateStr\":\"" + String(getStateString(currentState)) + "\",";
  json += "\"remainingSecs\":" + String(remainingSeconds) + ",";
  json += "\"totalSecs\":" + String(totalSessionSeconds) + ",";
  json += "\"distanceCm\":" + String(liveDistanceCm, 1) + ",";
  json += "\"pirMotion\":" + String(livePirMotion ? "true" : "false") + ",";
  json += "\"studentPresent\":" + String(studentPresent ? "true" : "false") + ",";
  json += "\"pirPresent\":" + String(studentPresent ? "true" : "false") + ",";
  json += "\"postureAlert\":" + String(postureState == POSTURE_WARNING_ACTIVE ? "true" : "false") + ",";
  json += "\"postureWaitingClearance\":" + String(postureState == POSTURE_WAITING_CLEARANCE ? "true" : "false") + ",";
  json += "\"absenceWarning\":" + String(absenceState == ABSENCE_STAGE_WARNING ? "true" : "false") + ",";
  json += "\"continuousAlarm\":" + String(absenceState == ABSENCE_CONTINUOUS_ALARM ? "true" : "false") + ",";
  json += "\"bleConnected\":" + String(bleClientConnected ? "true" : "false") + ",";
  json += "\"ledGreen\":" + String(ledG ? "true" : "false") + ",";
  json += "\"ledBlue\":" + String(ledB ? "true" : "false") + ",";
  json += "\"ledRed\":" + String(ledR ? "true" : "false") + ",";
  json += "\"profiles\":[";
  for (int i = 0; i < 3; i++) {
    if (i > 0) json += ",";
    json += "{";
    json += "\"name\":\"" + profiles[i].name + "\",";
    json += "\"studyM\":" + String(profiles[i].studyMins) + ",";
    json += "\"breakM\":" + String(profiles[i].breakMins) + ",";
    json += "\"minCm\":" + String(profiles[i].minPostureCm) + ",";
    json += "\"buzzer\":" + String(profiles[i].buzzerEnabled ? "true" : "false") + ",";
    json += "\"studiedM\":" + String(profiles[i].studiedSecsToday / 60);
    json += "}";
  }
  json += "]}";
  return json;
}

const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
  <title>StudySense Dashboard</title>
  <style>
    :root {
      --bg:#080c14; --card:#0f172a; --border:#1e293b; --text:#f8fafc; --muted:#94a3b8;
      --cyan:#06b6d4; --green:#10b981; --blue:#3b82f6; --red:#f43f5e; --amber:#f59e0b;
    }
    *{box-sizing:border-box;margin:0;padding:0;}
    body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);padding:14px;max-width:480px;margin:auto;}
    .top-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--border);}
    .brand{font-size:1.15rem;font-weight:800;color:#fff;}
    .badge{font-size:0.75rem;padding:3px 8px;border-radius:20px;font-weight:600;background:rgba(6,182,212,0.15);color:var(--cyan);border:1px solid rgba(6,182,212,0.3);}
    .card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:12px;box-shadow:0 4px 14px rgba(0,0,0,0.3);}
    .timer-wrap{text-align:center;padding:18px;}
    .timer-digits{font-size:3rem;font-weight:800;font-variant-numeric:tabular-nums;letter-spacing:-1px;margin:6px 0;}
    .state-pill{display:inline-block;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;text-transform:uppercase;background:rgba(59,130,246,0.15);color:var(--blue);border:1px solid rgba(59,130,246,0.3);}
    .btn-row{display:flex;gap:8px;justify-content:center;margin-top:12px;}
    .btn{padding:9px 16px;border-radius:8px;font-weight:700;font-size:0.85rem;cursor:pointer;border:none;transition:all 0.15s;}
    .btn-primary{background:var(--cyan);color:#fff;}
    .btn-sec{background:var(--border);color:var(--text);}
    .btn-danger{background:var(--red);color:#fff;}
    .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
    .stat-box{background:rgba(15,23,42,0.7);padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.05);}
    .stat-label{font-size:0.7rem;color:var(--muted);text-transform:uppercase;}
    .stat-val{font-size:1.05rem;font-weight:800;margin-top:2px;}
    .leds-row{display:flex;justify-content:space-around;padding:10px 0;}
    .led-item{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:0.75rem;color:var(--muted);}
    .led-dot{width:16px;height:16px;border-radius:50%;background:#1e293b;border:2px solid #334155;}
    .led-green.active{background:var(--green);box-shadow:0 0 12px var(--green);border-color:#34d399;}
    .led-blue.active{background:var(--blue);box-shadow:0 0 12px var(--blue);border-color:#60a5fa;}
    .led-red.active{background:var(--red);box-shadow:0 0 12px var(--red);border-color:#fb7185;}
    .alarm-banner{background:rgba(244,63,94,0.15);border:1px solid var(--red);padding:10px;border-radius:8px;margin-bottom:12px;text-align:center;display:none;}
    .alarm-title{color:var(--red);font-weight:800;font-size:0.9rem;}
  </style>
</head>
<body>
  <div class="top-bar">
    <div class="brand">StudySense</div>
    <div class="badge" id="modeBadge">MANUAL MODE</div>
  </div>

  <div class="alarm-banner" id="alarmBox">
    <div class="alarm-title" id="alarmMsg">⚠️ ALARM ACTIVE</div>
    <button class="btn btn-danger" style="margin-top:6px;" onclick="sendCmd('dismiss')">DISMISS ALARM (RESUME STUDY)</button>
  </div>

  <div class="card timer-wrap">
    <div class="state-pill" id="stateLabel">STANDBY</div>
    <div class="timer-digits" id="timerDisplay">25:00</div>
    <div style="font-size:0.8rem;color:var(--muted)" id="studentLabel">Active: Student 1</div>
    <div class="btn-row">
      <button class="btn btn-primary" id="mainBtn" onclick="sendCmd('startPause')">Start / Pause</button>
      <button class="btn btn-sec" onclick="sendCmd('toggleMode')">Toggle Mode</button>
    </div>
  </div>

  <div class="card">
    <div class="grid-2">
      <div class="stat-box">
        <div class="stat-label">Distance (HC-SR04)</div>
        <div class="stat-val" id="distVal">-- cm</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">PIR Presence</div>
        <div class="stat-val" id="pirVal">--</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Posture Status</div>
        <div class="stat-val" id="postureVal">--</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Studied Today</div>
        <div class="stat-val" id="studiedVal">-- mins</div>
      </div>
    </div>

    <div class="leds-row" style="margin-top:10px;">
      <div class="led-item"><div class="led-dot led-green" id="dotG"></div><span>Green (26)</span></div>
      <div class="led-item"><div class="led-dot led-blue" id="dotB"></div><span>Blue (25)</span></div>
      <div class="led-item"><div class="led-dot led-red" id="dotR"></div><span>Red (33)</span></div>
    </div>
  </div>

  <script>
    function fmt(s){const m=Math.floor(s/60),sc=s%60;return String(m).padStart(2,'0')+':'+String(sc).padStart(2,'0');}
    async function update(){
      try{
        const r=await fetch('/api/status');
        const d=await r.json();
        document.getElementById('timerDisplay').innerText=fmt(d.remainingSecs);
        document.getElementById('stateLabel').innerText=d.stateStr;
        document.getElementById('modeBadge').innerText=d.autoMode?'AUTO MODE':'MANUAL MODE';
        document.getElementById('studentLabel').innerText='Active: '+d.profiles[d.activeProfile].name;
        document.getElementById('distVal').innerText=d.distanceCm.toFixed(1)+' cm';
        document.getElementById('pirVal').innerText=d.studentPresent?(d.pirMotion?'Moving':'Present'):'Away';
        document.getElementById('pirVal').style.color=d.studentPresent?'var(--green)':'var(--amber)';
        document.getElementById('studiedVal').innerText=d.profiles[d.activeProfile].studiedM+' mins';

        const pEl=document.getElementById('postureVal');
        if(d.postureAlert){
          pEl.innerText='TOO CLOSE!'; pEl.style.color='var(--red)';
        } else if(d.postureWaitingClearance){
          pEl.innerText='Awaiting Safe Dist'; pEl.style.color='var(--amber)';
        } else {
          pEl.innerText=d.studentPresent?'Optimal Posture':'--'; pEl.style.color='var(--green)';
        }

        const box=document.getElementById('alarmBox');
        if(d.continuousAlarm){
          box.style.display='block';
          document.getElementById('alarmMsg').innerText='🚨 CONTINUOUS ABSENCE ALARM!';
        } else if(d.absenceWarning){
          box.style.display='block';
          document.getElementById('alarmMsg').innerText='⚠️ Student Absence Warning (Timer Paused)';
        } else if(d.postureAlert){
          box.style.display='block';
          document.getElementById('alarmMsg').innerText='⚠️ Posture Warning: Sit Back!';
        } else {
          box.style.display='none';
        }

        document.getElementById('dotG').className='led-dot led-green'+(d.ledGreen?' active':'');
        document.getElementById('dotB').className='led-dot led-blue'+(d.ledBlue?' active':'');
        document.getElementById('dotR').className='led-dot led-red'+(d.ledRed?' active':'');
      }catch(e){}
    }
    async function sendCmd(act){
      await fetch('/api/cmd?action='+act);
      update();
    }
    setInterval(update, 350);
    update();
  </script>
</body>
</html>
)rawliteral";

void setupWebServer() {
  server.on("/", HTTP_GET, []() {
    sendCorsHeaders();
    server.send_P(200, "text/html", INDEX_HTML);
  });

  server.on("/api/status", HTTP_GET, []() {
    sendCorsHeaders();
    server.send(200, "application/json", buildStatusJson());
  });

  server.on("/status", HTTP_GET, []() {
    sendCorsHeaders();
    server.send(200, "application/json", buildStatusJson());
  });

  server.on("/api/cmd", HTTP_GET, []() {
    sendCorsHeaders();
    if (server.hasArg("action")) {
      String act = server.arg("action");
      if (act == "startPause") {
        handleShortButtonPress();
      } else if (act == "dismiss") {
        handleShortButtonPress();
      } else if (act == "toggleMode") {
        handleLongButtonPress();
      } else if (act == "reset") {
        setTimerForState(STATE_IDLE);
      }
    }
    server.send(200, "application/json", "{\"status\":\"ok\"}");
  });

  server.on("/timer", HTTP_OPTIONS, []() {
    sendCorsHeaders();
    server.send(204);
  });
  server.on("/timer", HTTP_POST, []() {
    sendCorsHeaders();
    String body = server.arg("plain");
    if (body.indexOf("\"start\"") != -1) {
      if (currentState == STATE_IDLE || currentState == STATE_PAUSED) {
        handleShortButtonPress();
      }
    } else if (body.indexOf("\"pause\"") != -1) {
      if (currentState == STATE_STUDY) {
        handleShortButtonPress();
      }
    } else if (body.indexOf("\"reset\"") != -1) {
      setTimerForState(STATE_IDLE);
      triggerBuzzer(1, 100, 50);
    } else if (body.indexOf("\"dismiss\"") != -1) {
      handleShortButtonPress();
    } else {
      handleShortButtonPress();
    }
    server.send(200, "application/json", "{\"status\":\"ok\"}");
  });

  server.on("/config", HTTP_POST, []() {
    sendCorsHeaders();
    String body = server.arg("plain");
    UserProfile& p = profiles[activeProfileIdx];
    int sIdx = body.indexOf("\"studyDurationMins\":");
    if (sIdx != -1) p.studyMins = constrain(body.substring(sIdx + 20).toInt(), 1, 180);
    int bIdx = body.indexOf("\"breakDurationMins\":");
    if (bIdx != -1) p.breakMins = constrain(body.substring(bIdx + 20).toInt(), 1, 60);
    int dIdx = body.indexOf("\"minPostureDistCm\":");
    if (dIdx != -1) p.minPostureCm = constrain(body.substring(dIdx + 19).toInt(), 10, 60);
    int zIdx = body.indexOf("\"buzzerEnabled\":");
    if (zIdx != -1) p.buzzerEnabled = body.substring(zIdx + 16, zIdx + 22).indexOf("true") != -1;
    saveProfileToPrefs(activeProfileIdx);
    if (currentState == STATE_IDLE) setTimerForState(STATE_IDLE);
    triggerBuzzer(2, 60, 60);
    server.send(200, "application/json", "{\"status\":\"synced\"}");
  });

  server.begin();
}

// ======================= 12. MAIN SETUP ====================================
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== StudySense Smart Monitor Firmware v3.0 Initializing ===");

  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_ONBOARD_LED, OUTPUT);

  digitalWrite(PIN_TRIG, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_ONBOARD_LED, HIGH);

  // 1. Startup Hardware Verification Test: Cycle LEDs and Beep Buzzer
  Serial.println("[SELF-TEST] Testing LEDs and Buzzer on boot...");
  digitalWrite(PIN_LED_GREEN, HIGH);
  delay(250);
  digitalWrite(PIN_LED_GREEN, LOW);

  digitalWrite(PIN_LED_BLUE, HIGH);
  delay(250);
  digitalWrite(PIN_LED_BLUE, LOW);

  digitalWrite(PIN_LED_RED, HIGH);
  delay(250);
  digitalWrite(PIN_LED_RED, LOW);

  // Short welcome beep
  digitalWrite(PIN_BUZZER, HIGH);
  delay(120);
  digitalWrite(PIN_BUZZER, LOW);

  // STARTUP RULE: Blue LED ON (Standby Indication)
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_BLUE, HIGH);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_ONBOARD_LED, LOW);

  // Load NVS profile data
  loadAllProfilesFromPrefs();

  // STARTUP RULE: Default to Manual Standby on boot!
  isAutoMode = false;
  currentState = STATE_IDLE;
  setTimerForState(STATE_IDLE);

  // Wi-Fi SoftAP
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(local_IP, gateway, subnet);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("[Wi-Fi AP Online] SSID: ");
  Serial.print(AP_SSID);
  Serial.print(" | IP: http://");
  Serial.println(WiFi.softAPIP());

  // Embedded Web Server
  setupWebServer();

  // BLE Peripheral
  BLEDevice::init("StudyMonitor");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());
  BLEService* pService = pServer->createService(BLE_SERVICE_UUID);
  pStatusChar = pService->createCharacteristic(
      BLE_CHAR_STATUS_UUID,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pStatusChar->addDescriptor(new BLE2902());

  pCommandChar = pService->createCharacteristic(
      BLE_CHAR_COMMAND_UUID,
      BLECharacteristic::PROPERTY_WRITE
  );
  pCommandChar->setCallbacks(new CommandCallbacks());
  pService->start();

  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(BLE_SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();

  Serial.println("[SYSTEM READY] Standby mode active. Press push button (GPIO 22) to start study!");
}

// ======================= 13. MAIN LOOP =====================================
void loop() {
  server.handleClient();
  updateBuzzerEngine();
  unsigned long now = millis();

  // 0. Interactive USB Serial Command Listener
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();
    if (cmd == "START" || cmd == "TAP") {
      Serial.println("[SERIAL CMD] Simulating Button Tap -> Starting / Pausing Session");
      handleShortButtonPress();
    } else if (cmd == "TEST") {
      Serial.println("[SERIAL CMD] Running Full Hardware Cycle Test (Green -> Blue -> Red -> Buzzer)...");
      digitalWrite(PIN_LED_GREEN, HIGH); delay(350); digitalWrite(PIN_LED_GREEN, LOW);
      digitalWrite(PIN_LED_BLUE, HIGH); delay(350); digitalWrite(PIN_LED_BLUE, LOW);
      digitalWrite(PIN_LED_RED, HIGH); delay(350); digitalWrite(PIN_LED_RED, LOW);
      triggerBuzzer(2, 120, 80);
    } else if (cmd == "BEEP") {
      Serial.println("[SERIAL CMD] Test Beep");
      triggerBuzzer(1, 100, 50);
    } else if (cmd == "AUTO") {
      isAutoMode = true;
      Serial.println("[SERIAL CMD] Switched to AUTOMATIC mode");
      saveSystemStateToPrefs();
    } else if (cmd == "MANUAL") {
      isAutoMode = false;
      Serial.println("[SERIAL CMD] Switched to MANUAL mode");
      saveSystemStateToPrefs();
    }
  }

  // 1. Physical Push Button (GPIO 22, INPUT_PULLUP, Active LOW)
  static bool lastBtnState = HIGH;
  static unsigned long btnDownTime = 0;
  static bool btnIsDown = false;
  static bool btnLongHandled = false;

  bool currentBtnReading = digitalRead(PIN_BUTTON);

  // Button pressed down (transition from HIGH to LOW)
  if (currentBtnReading == LOW && lastBtnState == HIGH) {
    delay(10); // 10ms hardware debounce
    if (digitalRead(PIN_BUTTON) == LOW) {
      btnIsDown = true;
      btnDownTime = now;
      btnLongHandled = false;
      Serial.println("[BTN] Pressed down");
    }
  }
  // Button held down (check for long press > 1.2s)
  else if (currentBtnReading == LOW && btnIsDown && !btnLongHandled) {
    if ((now - btnDownTime) >= 1200) {
      btnLongHandled = true;
      Serial.println("[BTN] Long press triggered (>1.2s)");
      handleLongButtonPress();
    }
  }
  // Button released (transition from LOW to HIGH)
  else if (currentBtnReading == HIGH && lastBtnState == LOW) {
    delay(10); // 10ms debounce
    if (digitalRead(PIN_BUTTON) == HIGH && btnIsDown) {
      btnIsDown = false;
      unsigned long duration = now - btnDownTime;
      Serial.printf("[BTN] Released after %lu ms\n", duration);
      if (!btnLongHandled && duration >= 15) {
        Serial.println("[BTN] Short press registered -> Executing action!");
        handleShortButtonPress();
      }
    }
  }
  lastBtnState = currentBtnReading;

  // 2. High-Speed Sensor Sampling & Smart Fusion (Every 80ms)
  if (now - lastSensorReadMs >= SENSOR_INTERVAL_MS) {
    lastSensorReadMs = now;
    UserProfile& p = profiles[activeProfileIdx];

    livePirMotion = (digitalRead(PIN_PIR) == HIGH);
    if (livePirMotion) {
      lastPirMotionMs = now;
    }

    float rawCm = readUltrasonicCm();
    if (rawCm < 390.0f) {
      // 35% previous, 65% new for fast agile sensing
      liveDistanceCm = (0.35f * liveDistanceCm) + (0.65f * rawCm);
    } else {
      liveDistanceCm = (0.35f * liveDistanceCm) + (0.65f * 400.0f);
    }

    // MULTI-SENSOR HUMAN FUSION:
    // Requires PIR motion + human distance (15cm to 85cm) to establish presence
    bool inHumanRange = (liveDistanceCm >= 15.0f && liveDistanceCm <= p.maxPresenceCm);

    if (livePirMotion && inHumanRange) {
      lastPresenceSeenMs = now;
      studentPresent = true;
    } else if (studentPresent) {
      // Student is seated: allow quiet studying if distance is maintained and motion seen recently
      if (inHumanRange && (now - lastPirMotionMs < 5000)) {
        lastPresenceSeenMs = now;
      } else if (now - lastPresenceSeenMs >= 2500) {
        studentPresent = false;
      }
    }

    // -------------------------------------------------------------
    // ALERT SYSTEM A: POSTURE WARNING (Slouching / Too Close)
    // -------------------------------------------------------------
    if (currentState == STATE_STUDY && studentPresent && absenceState == ABSENCE_NORMAL) {
      if (postureState == POSTURE_NORMAL) {
        if (liveDistanceCm < p.minPostureCm) {
          if (badPostureDebounceMs == 0) badPostureDebounceMs = now;
          if (now - badPostureDebounceMs >= 350) { // 350ms confirmation
            postureState = POSTURE_WARNING_ACTIVE;
            postureWarningStartMs = now;
            badPostureDebounceMs = 0;
            triggerBuzzer(1, 150, 50); // Warning alert beep
          }
        } else {
          badPostureDebounceMs = 0;
        }
      } else if (postureState == POSTURE_WARNING_ACTIVE) {
        // RED LED ON for exactly 3 seconds
        if (now - postureWarningStartMs >= 3000) {
          postureState = POSTURE_WAITING_CLEARANCE;
          safeDistanceClearMs = 0;
        }
      } else if (postureState == POSTURE_WAITING_CLEARANCE) {
        // RED OFF: Wait for safe distance clearance (> minPostureCm)
        if (liveDistanceCm >= p.minPostureCm) {
          if (safeDistanceClearMs == 0) safeDistanceClearMs = now;
          if (now - safeDistanceClearMs >= 500) { // 500ms stable safe posture
            postureState = POSTURE_NORMAL;
            safeDistanceClearMs = 0;
          }
        } else {
          safeDistanceClearMs = 0;
        }
      }
    } else {
      postureState = POSTURE_NORMAL;
      badPostureDebounceMs = 0;
    }

    // -------------------------------------------------------------
    // ALERT SYSTEM B: STUDENT ABSENCE & CONTINUOUS ALARM
    // -------------------------------------------------------------
    if (currentState == STATE_STUDY) {
      if (!studentPresent) {
        if (absenceState == ABSENCE_NORMAL) {
          absenceState = ABSENCE_STAGE_WARNING;
          absenceStageStartMs = now;
        } else if (absenceState == ABSENCE_STAGE_WARNING) {
          // Stage 1: Red LED glows for 5 seconds (study timer paused)
          if (now - absenceStageStartMs >= 5000) {
            absenceState = ABSENCE_STAGE_GRACE;
            absenceStageStartMs = now;
          }
        } else if (absenceState == ABSENCE_STAGE_GRACE) {
          // Stage 2: 3 seconds grace gap
          if (now - absenceStageStartMs >= 3000) {
            absenceState = ABSENCE_CONTINUOUS_ALARM;
            Serial.println("[ALARM] Continuous Absence Alarm Triggered!");
          }
        }
        // Stage 3: ABSENCE_CONTINUOUS_ALARM keeps buzzer and Red LED firing
      } else {
        // Student returned to desk!
        if (absenceState != ABSENCE_NORMAL) {
          absenceState = ABSENCE_NORMAL;
          digitalWrite(PIN_BUZZER, LOW);
          Serial.println("[ALARM] Student Returned -> Alarm Automatically Cleared");
        }
      }
    } else {
      absenceState = ABSENCE_NORMAL;
      if (digitalRead(PIN_BUZZER) == HIGH && buzzer.beepsRemaining == 0) {
        digitalWrite(PIN_BUZZER, LOW);
      }
    }

    // AUTO Mode Transitions (Only if user explicitly enabled Auto Mode)
    if (isAutoMode) {
      if (studentPresent && (currentState == STATE_IDLE || currentState == STATE_PAUSED)) {
        currentState = STATE_STUDY;
        triggerBuzzer(1, 60, 50);
      }
    }

    // Update Physical LEDs (Green=26, Blue=25, Red=33)
    bool g, b, r;
    updateLEDs(g, b, r);
  }

  // 3. 1-Second Countdown Timer Engine
  if (now - lastSecondTickMs >= 1000) {
    lastSecondTickMs = now;

    // Study countdown ONLY runs when student is actively present (absence freezes timer!)
    if (currentState == STATE_STUDY && absenceState == ABSENCE_NORMAL) {
      if (remainingSeconds > 0) {
        remainingSeconds--;
        profiles[activeProfileIdx].studiedSecsToday++;
        if (profiles[activeProfileIdx].studiedSecsToday % 60 == 0) {
          saveProfileToPrefs(activeProfileIdx);
        }
      } else {
        // Study interval completed (00:00)
        triggerBuzzer(3, 220, 120);
        saveProfileToPrefs(activeProfileIdx);
        setTimerForState(STATE_BREAK);
      }
    } else if (currentState == STATE_BREAK) {
      if (remainingSeconds > 0) {
        remainingSeconds--;
      } else {
        triggerBuzzer(2, 200, 100);
        setTimerForState(STATE_IDLE);
      }
    }
  }

  // 4. BLE Telemetry Notifications (Every 1000ms)
  if (bleClientConnected && (now - lastBleNotifyMs >= 1000)) {
    lastBleNotifyMs = now;
    String tele = String("P:") + activeProfileIdx +
                  ",S:" + getStateString(currentState) +
                  ",T:" + remainingSeconds +
                  ",D:" + String(liveDistanceCm, 0) +
                  ",PIR:" + (studentPresent ? "1" : "0") +
                  ",AL:" + ((postureState == POSTURE_WARNING_ACTIVE || absenceState == ABSENCE_CONTINUOUS_ALARM) ? "1" : "0");
    pStatusChar->setValue(tele.c_str());
    pStatusChar->notify();
  }

  // 5. Serial Heartbeat Diagnostics (Every 1000ms)
  static unsigned long lastHeartbeatLogMs = 0;
  static bool onboardLedState = false;
  if (now - lastHeartbeatLogMs >= 1000) {
    lastHeartbeatLogMs = now;
    onboardLedState = !onboardLedState;
    digitalWrite(PIN_ONBOARD_LED, onboardLedState ? HIGH : LOW);
    Serial.printf("[HEARTBEAT] State:%-8s | Dist:%5.1fcm | PIR:%d | Present:%d | Btn:%d | LEDs(G:%d B:%d R:%d)\n",
                  getStateString(currentState),
                  liveDistanceCm,
                  livePirMotion ? 1 : 0,
                  studentPresent ? 1 : 0,
                  digitalRead(PIN_BUTTON),
                  digitalRead(PIN_LED_GREEN),
                  digitalRead(PIN_LED_BLUE),
                  digitalRead(PIN_LED_RED));
  }
}
