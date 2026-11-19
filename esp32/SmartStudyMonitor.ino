/*
 * ======================================================================================
 * Project: StudySense / Smart Study Behaviour Monitor
 * Target:  ESP32 (Arduino C++)
 * Generated via: Arena AI (gemini-4-argon-high)
 *
 * Features:
 *  - Hardware: PIR (GPIO 27), HC-SR04 (TRIG 13, ECHO 14), Button (GPIO 22),
 *              Active Buzzer (GPIO 23), Green LED (26), Blue LED (25), Red LED (33)
 *  - Wi-Fi SoftAP: SSID "StudyMonitor", Pass "study1234", Static IP 192.168.4.1
 *  - BLE Peripheral: Device Name "StudyMonitor" (Live JSON Telemetry + Command Input)
 *  - NVS Storage (Preferences): 3 Persistent User Profiles + Active Mode Persistence
 *  - Modes: AUTO Mode (presence-triggered timer) & MANUAL Mode (button/app-triggered)
 *  - Offline Responsive Web Dashboard served directly at http://192.168.4.1/
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
constexpr uint8_t PIN_ECHO      = 14; // Via 5V -> 3.3V voltage divider
constexpr uint8_t PIN_BUTTON    = 22; // Active LOW (INPUT_PULLUP)
constexpr uint8_t PIN_BUZZER    = 23; // Active Buzzer (HIGH = ON)
constexpr uint8_t PIN_LED_GREEN = 26; // Study Active / Good Posture
constexpr uint8_t PIN_LED_BLUE  = 25; // Break / Standby
constexpr uint8_t PIN_LED_RED   = 33; // Posture Warning / Alert

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

// ======================= 3. DATA STRUCTURES & STATE ========================
struct UserProfile {
  String name;
  uint16_t studyMins;       // Target study session duration (minutes)
  uint16_t breakMins;       // Target break session duration (minutes)
  uint16_t minPostureCm;    // Minimum safe eye/desk distance (cm)
  uint16_t maxPresenceCm;   // Maximum desk presence distance (cm)
  bool buzzerEnabled;       // Enable/disable buzzer reminders
  uint32_t studiedSecsToday;// Accumulated study time (seconds)
};

// 3 Stored User Profiles
UserProfile profiles[3] = {
  {"Student 1", 25, 5,  30, 85, true, 0},
  {"Student 2", 45, 10, 35, 85, true, 0},
  {"Student 3", 30, 5,  25, 85, true, 0}
};

uint8_t activeProfileIdx = 0; // 0, 1, or 2
bool isAutoMode = true;       // true = AUTO mode, false = MANUAL mode

enum SessionState {
  STATE_IDLE = 0,
  STATE_STUDY,
  STATE_PAUSED,
  STATE_BREAK
};

SessionState currentState = STATE_IDLE;
uint32_t remainingSeconds = 25 * 60;
uint32_t totalSessionSeconds = 25 * 60;

// Live Sensor & Alert Variables
float liveDistanceCm = 45.0;
bool livePirMotion = false;
bool studentPresent = false;
bool postureAlertActive = false;

// Timing Trackers (Non-blocking millis)
unsigned long lastSensorReadMs   = 0;
unsigned long lastSecondTickMs   = 0;
unsigned long lastPresenceSeenMs = 0;
unsigned long badPostureStartMs  = 0;
unsigned long lastPostureBeepMs  = 0;
unsigned long lastBleNotifyMs    = 0;

constexpr unsigned long PRESENCE_TIMEOUT_MS = 12000; // 12s grace period before auto-pause
constexpr unsigned long POSTURE_DEBOUNCE_MS = 1500;  // 1.5s leaning close triggers alert

// Button Debounce & Long-Press State
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

// ======================= 4. FORWARD DECLARATIONS ===========================
void loadAllProfilesFromPrefs();
void saveProfileToPrefs(uint8_t idx);
void saveSystemStateToPrefs();
void selectProfile(uint8_t idx);
void triggerBuzzer(uint8_t count, uint16_t onMs, uint16_t offMs);
void updateBuzzerEngine();
void setTimerForState(SessionState newState);
void handleShortButtonPress();
void toggleOperatingMode();
String buildStatusJson();

// ======================= 5. EMBEDDED HTML DASHBOARD ========================
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>StudyMonitor – Smart ESP32 Dashboard</title>
<style>
  :root {
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --text: #f8fafc; --muted: #94a3b8;
    --cyan: #06b6d4; --green: #10b981; --blue: #3b82f6; --red: #f43f5e; --amber: #f59e0b;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: var(--bg); color: var(--text); padding: 14px; max-width: 540px; margin: 0 auto; }
  .header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; border-bottom: 1px solid var(--border); margin-bottom: 14px; }
  .title h1 { font-size: 1.2rem; font-weight: 700; color: #fff; }
  .title p { font-size: 0.75rem; color: var(--muted); }
  .badge { padding: 5px 10px; border-radius: 99px; font-size: 0.72rem; font-weight: 700; background: rgba(16,185,129,0.15); color: var(--green); border: 1px solid rgba(16,185,129,0.4); }
  .alert-box { display: none; background: rgba(244,63,94,0.2); border: 1px solid var(--red); color: #fda4af; padding: 10px 12px; border-radius: 12px; font-size: 0.82rem; font-weight: 600; margin-bottom: 12px; text-align: center; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 14px; margin-bottom: 12px; }
  .card-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); font-weight: 700; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
  .profiles-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .prof-btn { background: #0f172a; border: 1px solid var(--border); color: var(--text); padding: 10px 6px; border-radius: 12px; cursor: pointer; text-align: center; transition: 0.2s; }
  .prof-btn.active { border-color: var(--cyan); background: rgba(6,182,212,0.15); }
  .prof-btn strong { display: block; font-size: 0.85rem; }
  .prof-btn span { font-size: 0.68rem; color: var(--muted); }
  .timer-wrap { text-align: center; padding: 12px 0; }
  .state-pill { display: inline-block; padding: 4px 12px; border-radius: 99px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; background: #0f172a; color: var(--cyan); margin-bottom: 6px; }
  .timer-digits { font-size: 3.6rem; font-weight: 800; font-variant-numeric: tabular-nums; letter-spacing: -1px; line-height: 1.1; margin: 6px 0; }
  .btn-row { display: flex; gap: 8px; justify-content: center; margin-top: 10px; }
  .btn { flex: 1; padding: 11px 14px; border: none; border-radius: 12px; font-weight: 700; font-size: 0.85rem; cursor: pointer; color: #fff; transition: 0.15s; }
  .btn:active { transform: scale(0.97); }
  .btn-primary { background: linear-gradient(135deg, var(--cyan), var(--blue)); }
  .btn-sec { background: #334155; }
  .btn-mode { background: rgba(245,158,11,0.18); border: 1px solid var(--amber); color: #fcd34d; padding: 5px 10px; border-radius: 8px; font-size: 0.72rem; cursor: pointer; font-weight: 700; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .stat-box { background: #0f172a; border: 1px solid var(--border); border-radius: 12px; padding: 10px 12px; }
  .stat-label { font-size: 0.7rem; color: var(--muted); }
  .stat-val { font-size: 1.15rem; font-weight: 700; margin-top: 3px; }
  .leds-row { display: flex; gap: 12px; align-items: center; justify-content: space-around; padding: 6px 0; }
  .led-item { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: var(--muted); }
  .led-dot { width: 14px; height: 14px; border-radius: 50%; background: #334155; transition: 0.2s; }
  .led-green.on { background: var(--green); box-shadow: 0 0 10px var(--green); }
  .led-blue.on { background: var(--blue); box-shadow: 0 0 10px var(--blue); }
  .led-red.on { background: var(--red); box-shadow: 0 0 10px var(--red); }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
  .field label { display: block; font-size: 0.7rem; color: var(--muted); margin-bottom: 3px; }
  .field input { width: 100%; padding: 8px; border-radius: 8px; border: 1px solid var(--border); background: #0f172a; color: #fff; font-size: 0.85rem; }
  .chk-row { display: flex; align-items: center; justify-content: space-between; font-size: 0.82rem; padding: 6px 0; }
</style>
</head>
<body>

  <div class="header">
    <div class="title">
      <h1>StudyMonitor</h1>
      <p>Smart Study Behaviour Monitor (192.168.4.1)</p>
    </div>
    <div class="badge" id="bleBadge">AP Online</div>
  </div>

  <div class="alert-box" id="alertBanner">⚠️ Posture Warning: Too close to desk! Sit back slightly.</div>

  <!-- Profiles Selector -->
  <div class="card">
    <div class="card-title">
      <span>Select Student Profile (NVS Stored)</span>
      <button class="btn-mode" id="modeBtn" onclick="sendCmd('toggleMode')">MODE: AUTO</button>
    </div>
    <div class="profiles-row" id="profilesContainer">
      <button class="prof-btn active" onclick="selectProfile(0)"><strong id="pName0">Student 1</strong><span id="pInfo0">25m / 5m</span></button>
      <button class="prof-btn" onclick="selectProfile(1)"><strong id="pName1">Student 2</strong><span id="pInfo1">45m / 10m</span></button>
      <button class="prof-btn" onclick="selectProfile(2)"><strong id="pName2">Student 3</strong><span id="pInfo2">30m / 5m</span></button>
    </div>
  </div>

  <!-- Main Study Timer -->
  <div class="card timer-wrap">
    <div class="state-pill" id="stateLabel">IDLE / READY</div>
    <div class="timer-digits" id="timerDisplay">25:00</div>
    <p style="font-size:0.75rem;color:var(--muted)" id="activeStudentSub">Active: Student 1</p>
    <div class="btn-row">
      <button class="btn btn-primary" id="startPauseBtn" onclick="sendCmd('startPause')">Start / Pause</button>
      <button class="btn btn-sec" onclick="sendCmd('reset')">Reset</button>
      <button class="btn btn-sec" onclick="sendCmd('skipMode')">Study/Break</button>
    </div>
  </div>

  <!-- Live Hardware Sensors -->
  <div class="card">
    <div class="card-title"><span>Live Hardware Telemetry</span></div>
    <div class="grid-2">
      <div class="stat-box">
        <div class="stat-label">HC-SR04 Distance</div>
        <div class="stat-val" id="distVal">45.0 cm</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">PIR Motion & Presence</div>
        <div class="stat-val" id="pirVal" style="color:var(--green)">Present</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Posture Status</div>
        <div class="stat-val" id="postureVal" style="color:var(--green)">Good</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Studied Today</div>
        <div class="stat-val" id="studiedTodayVal">0 mins</div>
      </div>
    </div>

    <div class="leds-row" style="margin-top:12px;">
      <div class="led-item"><div class="led-dot led-green" id="ledG"></div><span>Green (GPIO 26)</span></div>
      <div class="led-item"><div class="led-dot led-blue" id="ledB"></div><span>Blue (GPIO 25)</span></div>
      <div class="led-item"><div class="led-dot led-red" id="ledR"></div><span>Red (GPIO 33)</span></div>
    </div>
  </div>

  <!-- Edit Active Profile Settings -->
  <div class="card">
    <div class="card-title"><span>Customize Active Profile</span></div>
    <div class="form-row">
      <div class="field"><label>Student Name</label><input type="text" id="inName" maxlength="15"></div>
      <div class="field"><label>Min Posture Dist (cm)</label><input type="number" id="inMinCm" min="10" max="60"></div>
    </div>
    <div class="form-row">
      <div class="field"><label>Study Time (mins)</label><input type="number" id="inStudyM" min="1" max="120"></div>
      <div class="field"><label>Break Time (mins)</label><input type="number" id="inBreakM" min="1" max="60"></div>
    </div>
    <div class="chk-row">
      <span>Active Buzzer Alerts (GPIO 23)</span>
      <input type="checkbox" id="inBuzzer" style="width:18px;height:18px;">
    </div>
    <button class="btn btn-primary" style="width:100%;margin-top:8px;" onclick="saveProfile()">Save to ESP32 Flash</button>
  </div>

<script>
  let currentLoadedProfile = -1;

  function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
  }

  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      const d = await res.json();

      document.getElementById('timerDisplay').innerText = formatTime(d.remainingSecs);
      document.getElementById('stateLabel').innerText = d.stateStr + ' (' + (d.autoMode ? 'AUTO' : 'MANUAL') + ')';
      document.getElementById('modeBtn').innerText = 'MODE: ' + (d.autoMode ? 'AUTO' : 'MANUAL');
      document.getElementById('bleBadge').innerText = d.bleConnected ? 'BLE + Wi-Fi' : 'Wi-Fi AP Online';

      document.getElementById('distVal').innerText = d.distanceCm.toFixed(1) + ' cm';
      const pirEl = document.getElementById('pirVal');
      pirEl.innerText = d.studentPresent ? (d.pirMotion ? 'Motion Active' : 'Present') : 'Away';
      pirEl.style.color = d.studentPresent ? 'var(--green)' : 'var(--amber)';

      const posEl = document.getElementById('postureVal');
      const alertBox = document.getElementById('alertBanner');
      if (d.postureAlert) {
        posEl.innerText = 'Too Close! (<' + d.profiles[d.activeProfile].minCm + 'cm)';
        posEl.style.color = 'var(--red)';
        alertBox.style.display = 'block';
      } else {
        posEl.innerText = 'Good Posture';
        posEl.style.color = 'var(--green)';
        alertBox.style.display = 'none';
      }

      const activeP = d.profiles[d.activeProfile];
      document.getElementById('activeStudentSub').innerText = 'Active Profile: ' + activeP.name + ' (Min Dist: ' + activeP.minCm + 'cm)';
      document.getElementById('studiedTodayVal').innerText = Math.floor(activeP.studiedSecs / 60) + ' mins';

      // LED Indicators
      document.getElementById('ledG').className = 'led-dot led-green' + (d.ledGreen ? ' on' : '');
      document.getElementById('ledB').className = 'led-dot led-blue'  + (d.ledBlue  ? ' on' : '');
      document.getElementById('ledR').className = 'led-dot led-red'   + (d.ledRed   ? ' on' : '');

      // Update profile buttons
      const btns = document.querySelectorAll('.prof-btn');
      d.profiles.forEach((p, idx) => {
        document.getElementById('pName' + idx).innerText = p.name;
        document.getElementById('pInfo' + idx).innerText = p.studyM + 'm / ' + p.breakM + 'm';
        btns[idx].className = 'prof-btn' + (idx === d.activeProfile ? ' active' : '');
      });

      // Populate form when profile switches
      if (currentLoadedProfile !== d.activeProfile) {
        currentLoadedProfile = d.activeProfile;
        document.getElementById('inName').value = activeP.name;
        document.getElementById('inStudyM').value = activeP.studyM;
        document.getElementById('inBreakM').value = activeP.breakM;
        document.getElementById('inMinCm').value = activeP.minCm;
        document.getElementById('inBuzzer').checked = activeP.buzzer;
      }
    } catch (e) {}
  }

  async function sendCmd(action) {
    await fetch('/api/control?action=' + action, { method: 'POST' });
    fetchStatus();
  }

  async function selectProfile(idx) {
    currentLoadedProfile = -1;
    await fetch('/api/control?action=profile&idx=' + idx, { method: 'POST' });
    fetchStatus();
  }

  async function saveProfile() {
    const params = new URLSearchParams({
      idx: currentLoadedProfile,
      name: document.getElementById('inName').value,
      studyM: document.getElementById('inStudyM').value,
      breakM: document.getElementById('inBreakM').value,
      minCm: document.getElementById('inMinCm').value,
      buzzer: document.getElementById('inBuzzer').checked ? '1' : '0'
    });
    await fetch('/api/profile?' + params.toString(), { method: 'POST' });
    alert('Profile saved to ESP32 Flash!');
    fetchStatus();
  }

  setInterval(fetchStatus, 1000);
  fetchStatus();
</script>
</body>
</html>
)rawliteral";

// ======================= 6. BLE CALLBACKS ==================================
class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    bleClientConnected = true;
  }
  void onDisconnect(BLEServer* pServer) override {
    bleClientConnected = false;
    BLEDevice::startAdvertising(); // Restart advertising so phone can reconnect
  }
};

/*
 * BLE Command Characteristic supports simple text commands from any BLE app:
 *  - "START" / "PAUSE" / "TOGGLE" -> Starts or pauses session
 *  - "RESET"                      -> Resets session timer
 *  - "MODE:AUTO" / "MODE:MANUAL"  -> Switches operating mode
 *  - "PROFILE:0" / "PROFILE:1" / "PROFILE:2" -> Switches active user profile
 */
class CommandCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* pCharacteristic) override {
    String cmd = pCharacteristic->getValue().c_str();
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "START" || cmd == "PAUSE" || cmd == "TOGGLE") {
      handleShortButtonPress();
    } else if (cmd == "RESET") {
      setTimerForState(STATE_IDLE);
      triggerBuzzer(1, 80, 50);
    } else if (cmd == "MODE:AUTO") {
      isAutoMode = true;
      saveSystemStateToPrefs();
      triggerBuzzer(2, 80, 80);
    } else if (cmd == "MODE:MANUAL") {
      isAutoMode = false;
      saveSystemStateToPrefs();
      triggerBuzzer(2, 80, 80);
    } else if (cmd.startsWith("PROFILE:")) {
      int idx = cmd.substring(8).toInt();
      if (idx >= 0 && idx < 3) selectProfile(idx);
    }
  }
};

// ======================= 7. NVS PREFERENCES STORAGE ========================
void loadAllProfilesFromPrefs() {
  prefs.begin("studymon", false);
  activeProfileIdx = prefs.getUChar("activeProf", 0);
  if (activeProfileIdx > 2) activeProfileIdx = 0;
  isAutoMode = prefs.getBool("autoMode", true);

  for (uint8_t i = 0; i < 3; i++) {
    String prefix = "p" + String(i) + "_";
    profiles[i].name          = prefs.getString((prefix + "name").c_str(), profiles[i].name);
    profiles[i].studyMins     = prefs.getUShort((prefix + "study").c_str(), profiles[i].studyMins);
    profiles[i].breakMins     = prefs.getUShort((prefix + "break").c_str(), profiles[i].breakMins);
    profiles[i].minPostureCm  = prefs.getUShort((prefix + "minCm").c_str(), profiles[i].minPostureCm);
    profiles[i].maxPresenceCm = prefs.getUShort((prefix + "maxCm").c_str(), profiles[i].maxPresenceCm);
    profiles[i].buzzerEnabled = prefs.getBool((prefix + "buzz").c_str(), profiles[i].buzzerEnabled);
    profiles[i].studiedSecsToday = prefs.getULong((prefix + "secs").c_str(), 0);
  }
  prefs.end();
}

void saveProfileToPrefs(uint8_t idx) {
  if (idx > 2) return;
  prefs.begin("studymon", false);
  String prefix = "p" + String(idx) + "_";
  prefs.putString((prefix + "name").c_str(), profiles[idx].name);
  prefs.putUShort((prefix + "study").c_str(), profiles[idx].studyMins);
  prefs.putUShort((prefix + "break").c_str(), profiles[idx].breakMins);
  prefs.putUShort((prefix + "minCm").c_str(), profiles[idx].minPostureCm);
  prefs.putUShort((prefix + "maxCm").c_str(), profiles[idx].maxPresenceCm);
  prefs.putBool((prefix + "buzz").c_str(), profiles[idx].buzzerEnabled);
  prefs.putULong((prefix + "secs").c_str(), profiles[idx].studiedSecsToday);
  prefs.end();
}

void saveSystemStateToPrefs() {
  prefs.begin("studymon", false);
  prefs.putUChar("activeProf", activeProfileIdx);
  prefs.putBool("autoMode", isAutoMode);
  prefs.end();
}

void selectProfile(uint8_t idx) {
  if (idx > 2) return;
  activeProfileIdx = idx;
  saveSystemStateToPrefs();
  setTimerForState(STATE_IDLE);
  triggerBuzzer(2, 60, 60);
}

// ======================= 8. SENSOR & BUZZER HELPERS ========================
float readUltrasonicCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // 25,000 us timeout (~425 cm max) prevents blocking the main loop
  long duration = pulseIn(PIN_ECHO, HIGH, 25000);
  if (duration == 0) {
    return 120.0; // No obstacle within desk range
  }
  float cm = (duration * 0.0343f) / 2.0f;
  return constrain(cm, 2.0f, 300.0f);
}

void triggerBuzzer(uint8_t count, uint16_t onMs, uint16_t offMs) {
  if (!profiles[activeProfileIdx].buzzerEnabled) return;
  buzzer.beepsRemaining = count;
  buzzer.onDurationMs = onMs;
  buzzer.offDurationMs = offMs;
  buzzer.pinCurrentlyHigh = true;
  buzzer.lastToggleMs = millis();
  digitalWrite(PIN_BUZZER, HIGH);
}

void updateBuzzerEngine() {
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

// ======================= 9. TIMER & STATE MACHINE ==========================
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

void handleShortButtonPress() {
  triggerBuzzer(1, 70, 50);
  if (currentState == STATE_IDLE || currentState == STATE_PAUSED) {
    if (currentState == STATE_IDLE) {
      totalSessionSeconds = profiles[activeProfileIdx].studyMins * 60UL;
      remainingSeconds = totalSessionSeconds;
    }
    currentState = STATE_STUDY;
    lastPresenceSeenMs = millis();
  } else if (currentState == STATE_STUDY) {
    currentState = STATE_PAUSED;
  } else if (currentState == STATE_BREAK) {
    // Pressing button during break skips back to study ready
    setTimerForState(STATE_IDLE);
  }
}

void toggleOperatingMode() {
  isAutoMode = !isAutoMode;
  saveSystemStateToPrefs();
  // 2 longer beeps confirm mode switch (Auto <-> Manual)
  triggerBuzzer(2, 160, 100);
}

void updateLEDs(bool& outGreen, bool& outBlue, bool& outRed) {
  // Red LED (GPIO 33): ON when posture alert is active or student walked away during study
  outRed = postureAlertActive || (currentState == STATE_PAUSED && isAutoMode && !studentPresent);

  // Green LED (GPIO 26): ON when actively studying with good posture
  outGreen = (currentState == STATE_STUDY && !postureAlertActive);

  // Blue LED (GPIO 25): ON during Break mode or Idle/Paused standby
  outBlue = (currentState == STATE_BREAK || currentState == STATE_IDLE || currentState == STATE_PAUSED);

  digitalWrite(PIN_LED_GREEN, outGreen ? HIGH : LOW);
  digitalWrite(PIN_LED_BLUE,  outBlue  ? HIGH : LOW);
  digitalWrite(PIN_LED_RED,   outRed   ? HIGH : LOW);
}

// ======================= 10. JSON & WEB SERVER HANDLERS ====================
const char* getStateString(SessionState s) {
  switch (s) {
    case STATE_IDLE:   return "IDLE";
    case STATE_STUDY:  return "STUDYING";
    case STATE_PAUSED: return "PAUSED";
    case STATE_BREAK:  return "BREAK";
    default:           return "IDLE";
  }
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
  json += "\"postureAlert\":" + String(postureAlertActive ? "true" : "false") + ",";
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
    json += "\"studiedSecs\":" + String(profiles[i].studiedSecsToday);
    json += "}";
  }
  json += "]}";
  return json;
}

void sendCorsHeaders() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

void setupWebServer() {
  // Root HTML Dashboard
  server.on("/", HTTP_GET, []() {
    server.send_P(200, "text/html", INDEX_HTML);
  });

  // Live Telemetry API
  server.on("/api/status", HTTP_GET, []() {
    sendCorsHeaders();
    server.send(200, "application/json", buildStatusJson());
  });

  // Control Actions API
  server.on("/api/control", HTTP_POST, []() {
    sendCorsHeaders();
    String action = server.arg("action");
    if (action == "startPause") {
      handleShortButtonPress();
    } else if (action == "reset") {
      setTimerForState(STATE_IDLE);
      triggerBuzzer(1, 80, 50);
    } else if (action == "toggleMode") {
      toggleOperatingMode();
    } else if (action == "skipMode") {
      if (currentState == STATE_BREAK) setTimerForState(STATE_STUDY);
      else setTimerForState(STATE_BREAK);
      triggerBuzzer(1, 80, 50);
    } else if (action == "profile") {
      int idx = server.arg("idx").toInt();
      selectProfile(idx);
    }
    server.send(200, "application/json", "{\"ok\":true}");
  });

  // Save Profile Settings API
  server.on("/api/profile", HTTP_POST, []() {
    sendCorsHeaders();
    int idx = server.arg("idx").toInt();
    if (idx >= 0 && idx < 3) {
      if (server.hasArg("name") && server.arg("name").length() > 0) {
        profiles[idx].name = server.arg("name");
      }
      if (server.hasArg("studyM")) {
        profiles[idx].studyMins = constrain(server.arg("studyM").toInt(), 1, 180);
      }
      if (server.hasArg("breakM")) {
        profiles[idx].breakMins = constrain(server.arg("breakM").toInt(), 1, 60);
      }
      if (server.hasArg("minCm")) {
        profiles[idx].minPostureCm = constrain(server.arg("minCm").toInt(), 10, 60);
      }
      if (server.hasArg("buzzer")) {
        profiles[idx].buzzerEnabled = (server.arg("buzzer") == "1" || server.arg("buzzer") == "true");
      }
      saveProfileToPrefs(idx);
      if (idx == activeProfileIdx && currentState == STATE_IDLE) {
        setTimerForState(STATE_IDLE);
      }
      triggerBuzzer(2, 60, 60);
    }
    server.send(200, "application/json", "{\"saved\":true}");
  });

  // Compatibility endpoint for external Android/PC Companion App (/config)
  server.on("/config", HTTP_OPTIONS, []() {
    sendCorsHeaders();
    server.send(204);
  });
  server.on("/config", HTTP_POST, []() {
    sendCorsHeaders();
    String body = server.arg("plain");
    UserProfile& p = profiles[activeProfileIdx];

    // Lightweight JSON key extractor
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

// ======================= 11. SETUP & INITIALIZATION ========================
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== Starting StudyMonitor ESP32 Firmware ===");

  // Configure GPIO Pins
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);

  digitalWrite(PIN_TRIG, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  // Load saved profiles & mode from NVS Preferences
  loadAllProfilesFromPrefs();
  setTimerForState(STATE_IDLE);

  // Start Wi-Fi SoftAP at 192.168.4.1
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(local_IP, gateway, subnet);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("Wi-Fi AP Started! SSID: ");
  Serial.print(AP_SSID);
  Serial.print(" | Dashboard URL: http://");
  Serial.println(WiFi.softAPIP());

  // Start Web Server
  setupWebServer();

  // Initialize BLE Peripheral ("StudyMonitor")
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
  Serial.println("BLE Peripheral 'StudyMonitor' Advertising Started.");

  // Startup LED & Buzzer Greeting
  triggerBuzzer(2, 80, 80);
  lastPresenceSeenMs = millis();
}

// ======================= 12. MAIN NON-BLOCKING LOOP ========================
void loop() {
  unsigned long now = millis();

  // 1. Process HTTP Web Server Requests
  server.handleClient();

  // 2. Process Active Buzzer Engine
  updateBuzzerEngine();

  // 3. Read Push Button (GPIO 22): Short Press = Start/Pause, Long Press = Toggle Auto/Manual
  bool reading = digitalRead(PIN_BUTTON);
  if (reading == LOW && lastBtnReading == HIGH) {
    // Button just pressed down
    btnPressStartMs = now;
    longPressHandled = false;
  } else if (reading == LOW && !longPressHandled) {
    // Button held down: check for 1.2s long press
    if (now - btnPressStartMs >= 1200) {
      longPressHandled = true;
      toggleOperatingMode();
    }
  } else if (reading == HIGH && lastBtnReading == LOW) {
    // Button released: if it wasn't a long press and held > 40ms (debounce), handle short press
    if (!longPressHandled && (now - btnPressStartMs >= 40)) {
      handleShortButtonPress();
    }
  }
  lastBtnReading = reading;

  // 4. Read PIR & Ultrasonic Sensors every 250ms
  if (now - lastSensorReadMs >= 250) {
    lastSensorReadMs = now;
    UserProfile& p = profiles[activeProfileIdx];

    livePirMotion = (digitalRead(PIN_PIR) == HIGH);
    float rawCm = readUltrasonicCm();
    // Smooth distance reading (exponential filter)
    liveDistanceCm = (0.65f * liveDistanceCm) + (0.35f * rawCm);

    // Presence logic: Student is present if PIR sees motion OR ultrasonic sees person within desk range
    bool detectedNow = livePirMotion || (liveDistanceCm <= p.maxPresenceCm);
    if (detectedNow) {
      lastPresenceSeenMs = now;
      studentPresent = true;
    } else if (now - lastPresenceSeenMs >= PRESENCE_TIMEOUT_MS) {
      studentPresent = false;
    }

    // Posture Alert Logic: Student leaning closer than profile's minPostureCm
    if (liveDistanceCm < p.minPostureCm) {
      if (badPostureStartMs == 0) badPostureStartMs = now;
      if (now - badPostureStartMs >= POSTURE_DEBOUNCE_MS) {
        postureAlertActive = true;
        // Sound warning beep every 3 seconds while leaning too close
        if (now - lastPostureBeepMs >= 3000) {
          lastPostureBeepMs = now;
          triggerBuzzer(1, 180, 100);
        }
      }
    } else {
      badPostureStartMs = 0;
      postureAlertActive = false;
    }

    // AUTO Mode State Transitions based on Presence
    if (isAutoMode) {
      if (studentPresent && (currentState == STATE_IDLE || currentState == STATE_PAUSED)) {
        // Student sat down at desk -> Auto-start or auto-resume study timer!
        currentState = STATE_STUDY;
        triggerBuzzer(1, 60, 50);
      } else if (!studentPresent && currentState == STATE_STUDY) {
        // Student walked away -> Auto-pause study timer!
        currentState = STATE_PAUSED;
        triggerBuzzer(1, 200, 100);
      }
    }

    // Update Physical LEDs (Green=26, Blue=25, Red=33)
    bool g, b, r;
    updateLEDs(g, b, r);
  }

  // 5. 1-Second Countdown Timer Engine
  if (now - lastSecondTickMs >= 1000) {
    lastSecondTickMs = now;

    if (currentState == STATE_STUDY || currentState == STATE_BREAK) {
      if (remainingSeconds > 0) {
        remainingSeconds--;

        // Track accumulated study seconds for the active profile
        if (currentState == STATE_STUDY) {
          profiles[activeProfileIdx].studiedSecsToday++;
          // Save accumulated time to Flash every 60 seconds to protect NVS wear
          if (profiles[activeProfileIdx].studiedSecsToday % 60 == 0) {
            saveProfileToPrefs(activeProfileIdx);
          }
        }
      } else {
        // Timer reached 00:00!
        triggerBuzzer(3, 220, 120);
        if (currentState == STATE_STUDY) {
          // Automatically transition from Study to Break
          saveProfileToPrefs(activeProfileIdx);
          setTimerForState(STATE_BREAK);
        } else {
          // Break finished -> Transition back to Study (if Auto & Present) or Idle
          if (isAutoMode && studentPresent) {
            setTimerForState(STATE_STUDY);
          } else {
            setTimerForState(STATE_IDLE);
          }
        }
      }
    }
  }

  // 6. Push Live BLE Notifications every 2 seconds if a BLE client is connected
  if (bleClientConnected && (now - lastBleNotifyMs >= 2000)) {
    lastBleNotifyMs = now;
    String compactTele = String("P:") + activeProfileIdx +
                         ",M:" + (isAutoMode ? "A" : "M") +
                         ",S:" + getStateString(currentState) +
                         ",T:" + remainingSeconds +
                         ",D:" + String(liveDistanceCm, 0) +
                         ",PIR:" + (studentPresent ? "1" : "0") +
                         ",AL:" + (postureAlertActive ? "1" : "0");
    pStatusChar->setValue(compactTele.c_str());
    pStatusChar->notify();
  }
}
