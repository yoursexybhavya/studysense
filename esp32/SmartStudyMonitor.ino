/*
 * ==============================================================================
 * Project: Smart Study Monitor – ESP32 Based Multi-User Monitoring System
 * ==============================================================================
 * Hardware Configuration:
 *   - PIR Motion Sensor OUT       -> GPIO 27
 *   - HC-SR04 Ultrasonic TRIG     -> GPIO 13
 *   - HC-SR04 Ultrasonic ECHO     -> GPIO 14 (via 5V -> 3.3V Voltage Divider)
 *   - Push Button                 -> GPIO 22 (to GND, INPUT_PULLUP)
 *   - Active Buzzer (BC547 Base)  -> GPIO 23 (through 1k resistor)
 *   - Green LED Indicator         -> GPIO 26 (through 220-330R resistor)
 *   - Blue LED Indicator          -> GPIO 25 (through 220-330R resistor)
 *   - Red LED Indicator           -> GPIO 33 (through 220-330R resistor)
 *
 * Connectivity:
 *   - Wi-Fi Access Point: SSID "StudyMonitor", Password "study1234"
 *   - Web Dashboard:      http://192.168.4.1
 *   - BLE Device Name:    "StudyMonitor"
 *
 * Storage:
 *   - Preferences.h (ESP32 NVS Flash) retains 3 independent User Profiles:
 *     Name, Distance Threshold, Buzzer Enable, and Monitoring Active status.
 * ==============================================================================
 */

#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ======================= PIN ASSIGNMENTS =======================
#define PIN_PIR        27
#define PIN_TRIG       13
#define PIN_ECHO       14
#define PIN_BUTTON     22
#define PIN_BUZZER     23
#define PIN_LED_GREEN  26
#define PIN_LED_BLUE   25
#define PIN_LED_RED    33

// ======================= NETWORK & BLE CONFIG ==================
const char* AP_SSID     = "StudyMonitor";
const char* AP_PASSWORD = "study1234";
const IPAddress AP_IP(192, 168, 4, 1);
const IPAddress AP_GATEWAY(192, 168, 4, 1);
const IPAddress AP_SUBNET(255, 255, 255, 0);

#define BLE_SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define BLE_CHAR_STATUS_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define BLE_CHAR_COMMAND_UUID   "1c95d5e3-d8f7-413a-bf3d-7a2e5d7be87e"

// ======================= USER PROFILE STRUCTURE ================
struct UserProfile {
  char name[24];
  int  distanceThreshold;  // cm (default 30)
  bool buzzerEnabled;
  bool monitoringActive;
};

#define NUM_PROFILES 3
UserProfile profiles[NUM_PROFILES] = {
  { "Student 1", 30, true,  true },
  { "Student 2", 35, false, true },
  { "Student 3", 25, true,  true }
};

int activeProfile = 0;
bool autoMode = true; // true = Auto, false = Manual

// Manual mode LED states
bool manualGreen = false;
bool manualBlue  = false;
bool manualRed   = false;

// Sensor & Alarm Live States
float liveDistance       = 45.0;
bool  livePir            = false;
bool  alarmState         = false;
bool  bleDeviceConnected = false;

// Non-blocking Timing
unsigned long lastSensorReadTime = 0;
unsigned long lastButtonTime     = 0;
unsigned long lastBleNotifyTime  = 0;
unsigned long lastBuzzerToggle   = 0;
bool buzzerPulseState            = false;

const unsigned long SENSOR_INTERVAL_MS = 200;
const unsigned long BLE_NOTIFY_MS      = 1000;
const unsigned long DEBOUNCE_DELAY_MS  = 200;

// Hardware & Service Handles
WebServer server(80);
Preferences prefs;
BLEServer* pBleServer = nullptr;
BLECharacteristic* pStatusChar = nullptr;
BLECharacteristic* pCommandChar = nullptr;

// ======================= BLE CALLBACKS =========================
class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    bleDeviceConnected = true;
  }
  void onDisconnect(BLEServer* pServer) {
    bleDeviceConnected = false;
    BLEDevice::startAdvertising(); // Restart advertising so other clients can connect
  }
};

class CommandCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* pChar) {
    String value = pChar->getValue();
    if (value.length() > 0) {
      char cmd = value[0];
      if (cmd == 'M') { // Toggle Mode
        autoMode = !autoMode;
      } else if (cmd == '1') { // Profile 1
        activeProfile = 0;
        saveActiveProfile();
      } else if (cmd == '2') { // Profile 2
        activeProfile = 1;
        saveActiveProfile();
      } else if (cmd == '3') { // Profile 3
        activeProfile = 2;
        saveActiveProfile();
      } else if (cmd == 'B') { // Toggle Buzzer
        profiles[activeProfile].buzzerEnabled = !profiles[activeProfile].buzzerEnabled;
        saveProfileData(activeProfile);
      } else if (cmd == 'S') { // Toggle Monitoring
        profiles[activeProfile].monitoringActive = !profiles[activeProfile].monitoringActive;
        saveProfileData(activeProfile);
      } else if (cmd == 'G' && !autoMode) { // Toggle Green
        manualGreen = !manualGreen;
      } else if (cmd == 'L' && !autoMode) { // Toggle Blue
        manualBlue = !manualBlue;
      } else if (cmd == 'R' && !autoMode) { // Toggle Red
        manualRed = !manualRed;
      }
    }
  }
};

// ======================= NVS PERSISTENT STORAGE ================
void loadPreferences() {
  prefs.begin("studymon", true); // Read-only mode
  activeProfile = prefs.getInt("active_p", 0);
  if (activeProfile < 0 || activeProfile >= NUM_PROFILES) activeProfile = 0;
  autoMode = prefs.getBool("auto_mode", true);

  for (int i = 0; i < NUM_PROFILES; i++) {
    char key[16];
    snprintf(key, sizeof(key), "name_%d", i);
    String sName = prefs.getString(key, profiles[i].name);
    strncpy(profiles[i].name, sName.c_str(), sizeof(profiles[i].name) - 1);
    profiles[i].name[sizeof(profiles[i].name) - 1] = '\0';

    snprintf(key, sizeof(key), "dist_%d", i);
    profiles[i].distanceThreshold = prefs.getInt(key, profiles[i].distanceThreshold);

    snprintf(key, sizeof(key), "buzz_%d", i);
    profiles[i].buzzerEnabled = prefs.getBool(key, profiles[i].buzzerEnabled);

    snprintf(key, sizeof(key), "mon_%d", i);
    profiles[i].monitoringActive = prefs.getBool(key, profiles[i].monitoringActive);
  }
  prefs.end();
}

void saveActiveProfile() {
  prefs.begin("studymon", false);
  prefs.putInt("active_p", activeProfile);
  prefs.putBool("auto_mode", autoMode);
  prefs.end();
}

void saveProfileData(int idx) {
  if (idx < 0 || idx >= NUM_PROFILES) return;
  prefs.begin("studymon", false);
  char key[16];
  snprintf(key, sizeof(key), "name_%d", idx);
  prefs.putString(key, profiles[idx].name);
  snprintf(key, sizeof(key), "dist_%d", idx);
  prefs.putInt(key, profiles[idx].distanceThreshold);
  snprintf(key, sizeof(key), "buzz_%d", idx);
  prefs.putBool(key, profiles[idx].buzzerEnabled);
  snprintf(key, sizeof(key), "mon_%d", idx);
  prefs.putBool(key, profiles[idx].monitoringActive);
  prefs.end();
}

// ======================= SENSOR FUNCTIONS ======================
float readDistanceCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // 25ms timeout (~400cm max) prevents locking the loop if echo is lost
  unsigned long duration = pulseIn(PIN_ECHO, HIGH, 25000UL);
  if (duration == 0) return liveDistance; // Keep last stable reading on timeout
  float cm = (duration * 0.0343f) / 2.0f;
  if (cm < 2.0f || cm > 400.0f) return liveDistance;
  return cm;
}

void updateSensors() {
  liveDistance = readDistanceCm();
  livePir      = (digitalRead(PIN_PIR) == HIGH);
}

// ======================= OUTPUT CONTROL ========================
void setLeds(bool g, bool b, bool r) {
  digitalWrite(PIN_LED_GREEN, g ? HIGH : LOW);
  digitalWrite(PIN_LED_BLUE,  b ? HIGH : LOW);
  digitalWrite(PIN_LED_RED,   r ? HIGH : LOW);
}

void setBuzzer(bool state) {
  digitalWrite(PIN_BUZZER, state ? HIGH : LOW);
}

void processControlLogic() {
  UserProfile& cur = profiles[activeProfile];

  if (autoMode) {
    if (!cur.monitoringActive) {
      // Monitoring paused: All off, blue blink standby
      alarmState = false;
      setBuzzer(false);
      setLeds(false, (millis() / 800) % 2 == 0, false);
      return;
    }

    // Condition: PIR movement detected AND distance is closer than threshold
    if (livePir && liveDistance < cur.distanceThreshold) {
      alarmState = true;
      setLeds(false, false, true); // RED LED

      if (cur.buzzerEnabled) {
        // Pulsing buzzer alert (200ms on, 200ms off)
        if (millis() - lastBuzzerToggle >= 200) {
          lastBuzzerToggle = millis();
          buzzerPulseState = !buzzerPulseState;
          setBuzzer(buzzerPulseState);
        }
      } else {
        setBuzzer(false);
      }
    } else if (livePir) {
      // Movement detected, posture distance is good
      alarmState = false;
      setBuzzer(false);
      setLeds(true, false, false); // GREEN LED
    } else {
      // No movement (student away / standby)
      alarmState = false;
      setBuzzer(false);
      setLeds(false, true, false); // BLUE LED
    }
  } else {
    // Manual Mode: Direct LED control from dashboard / BLE
    alarmState = false;
    setBuzzer(false);
    setLeds(manualGreen, manualBlue, manualRed);
  }
}

// ======================= EMBEDDED WEB DASHBOARD ================
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Smart Study Monitor</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #0b0f19; color: #f8fafc; padding: 16px; min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
    .card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 18px; width: 100%; max-width: 440px; margin-bottom: 14px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }
    .header { display: flex; justify-content: space-between; align-items: center; width: 100%; max-width: 440px; padding: 8px 4px 14px; }
    .title { font-size: 19px; font-weight: 700; color: #38bdf8; letter-spacing: -0.5px; }
    .badge { padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .badge-auto { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
    .badge-man { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .stat-box { background: rgba(15,23,42,0.8); border: 1px solid rgba(255,255,255,0.05); padding: 14px; border-radius: 14px; text-align: center; }
    .stat-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .stat-val { font-size: 26px; font-weight: 800; font-family: monospace; color: #f8fafc; }
    .alert-banner { display: none; padding: 12px; border-radius: 12px; margin-bottom: 12px; font-weight: 600; font-size: 13px; text-align: center; background: #dc2626; color: #fff; animation: pulse 1s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.75; } }
    .profiles { display: flex; gap: 8px; margin-top: 10px; }
    .prof-btn { flex: 1; padding: 10px; border-radius: 12px; border: 1px solid #334155; background: #1e293b; color: #94a3b8; font-weight: 600; font-size: 12px; cursor: pointer; transition: all 0.2s; }
    .prof-btn.active { background: #0284c7; color: #fff; border-color: #38bdf8; box-shadow: 0 4px 12px rgba(2,132,199,0.35); }
    .switch-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .switch-row:last-child { border-bottom: none; }
    .switch { position: relative; display: inline-block; width: 44px; height: 24px; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #334155; transition: .3s; border-radius: 24px; }
    .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background: white; transition: .3s; border-radius: 50%; }
    input:checked + .slider { background: #0284c7; }
    input:checked + .slider:before { transform: translateX(20px); }
    .btn-action { width: 100%; padding: 12px; border-radius: 12px; border: none; font-weight: 700; font-size: 13px; cursor: pointer; margin-top: 8px; transition: transform 0.1s; }
    .btn-mode { background: linear-gradient(135deg, #0284c7, #2563eb); color: white; }
    .btn-action:active { transform: scale(0.98); }
    .led-btn-group { display: flex; gap: 8px; margin-top: 6px; }
    .led-btn { flex: 1; padding: 10px; border-radius: 10px; font-weight: 700; font-size: 12px; border: 1px solid #334155; background: #1e293b; color: #94a3b8; cursor: pointer; }
    .led-btn.active-g { background: #15803d; color: white; border-color: #22c55e; }
    .led-btn.active-b { background: #1d4ed8; color: white; border-color: #3b82f6; }
    .led-btn.active-r { background: #b91c1c; color: white; border-color: #ef4444; }
    .range-wrap { margin: 10px 0; }
    .range-wrap input { width: 100%; accent-color: #38bdf8; }
  </style>
</head>
<body>

  <div class="header">
    <div>
      <div class="title">StudyMonitor</div>
      <div style="font-size:11px; color:#64748b;">ESP32 Multi-User Station</div>
    </div>
    <div id="modeBadge" class="badge badge-auto">Auto Mode</div>
  </div>

  <div id="alarmBanner" class="alert-banner">
    ⚠️ Posture Alert: Too close to desk!
  </div>

  <!-- Live Sensor Cards -->
  <div class="card">
    <div class="grid">
      <div class="stat-box">
        <div class="stat-label">Distance</div>
        <div id="statDist" class="stat-val">-- cm</div>
        <div id="statDistDesc" style="font-size:10px; color:#10b981; margin-top:4px;">In Range</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">PIR Movement</div>
        <div id="statPir" class="stat-val">--</div>
        <div id="statPirDesc" style="font-size:10px; color:#94a3b8; margin-top:4px;">Motion State</div>
      </div>
    </div>
  </div>

  <!-- Profiles -->
  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <span style="font-size:13px; font-weight:700;">User Profiles</span>
      <button onclick="renameActiveProfile()" style="background:none; border:none; color:#38bdf8; font-size:11px; cursor:pointer;">Rename</button>
    </div>
    <div class="profiles">
      <button id="pbtn0" class="prof-btn" onclick="selectProfile(0)">P1</button>
      <button id="pbtn1" class="prof-btn" onclick="selectProfile(1)">P2</button>
      <button id="pbtn2" class="prof-btn" onclick="selectProfile(2)">P3</button>
    </div>

    <div class="range-wrap">
      <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
        <span style="color:#94a3b8;">Alert Threshold</span>
        <span id="threshVal" style="color:#38bdf8; font-weight:700;">30 cm</span>
      </div>
      <input id="threshSlider" type="range" min="15" max="60" step="5" value="30" onchange="updateThreshold(this.value)" oninput="document.getElementById('threshVal').innerText = this.value + ' cm'">
    </div>
  </div>

  <!-- Controls -->
  <div class="card">
    <div class="switch-row">
      <span style="font-size:13px;">Buzzer Alarm</span>
      <label class="switch">
        <input id="buzzToggle" type="checkbox" onchange="toggleBuzzer(this.checked)">
        <span class="slider"></span>
      </label>
    </div>

    <div class="switch-row">
      <span style="font-size:13px;">Active Monitoring</span>
      <label class="switch">
        <input id="monToggle" type="checkbox" onchange="toggleMonitoring(this.checked)">
        <span class="slider"></span>
      </label>
    </div>

    <button id="modeToggleBtn" class="btn-action btn-mode" onclick="toggleMode()">Switch to Manual Mode</button>
  </div>

  <!-- Manual LED Controls (Hidden in Auto Mode) -->
  <div id="manualCard" class="card" style="display:none;">
    <div style="font-size:13px; font-weight:700; margin-bottom:8px;">Manual LED Control</div>
    <div class="led-btn-group">
      <button id="mGreen" class="led-btn" onclick="toggleLed('g')">Green</button>
      <button id="mBlue" class="led-btn" onclick="toggleLed('b')">Blue</button>
      <button id="mRed" class="led-btn" onclick="toggleLed('r')">Red</button>
    </div>
  </div>

  <script>
    let currentData = {};

    async function fetchStatus() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const d = await res.json();
        currentData = d;

        document.getElementById('statDist').innerText = Math.round(d.distance) + ' cm';
        document.getElementById('statPir').innerText = d.pir ? 'DETECT' : 'IDLE';
        document.getElementById('statPir').style.color = d.pir ? '#34d399' : '#94a3b8';

        // Alarm Banner
        const banner = document.getElementById('alarmBanner');
        if (d.alarm) {
          banner.style.display = 'block';
          banner.innerText = '⚠️ Posture Alert: Too close to desk (' + Math.round(d.distance) + ' cm)!';
        } else {
          banner.style.display = 'none';
        }

        // Mode Display
        const badge = document.getElementById('modeBadge');
        const modeBtn = document.getElementById('modeToggleBtn');
        const manCard = document.getElementById('manualCard');
        if (d.autoMode) {
          badge.className = 'badge badge-auto';
          badge.innerText = 'Auto Mode';
          modeBtn.innerText = 'Switch to Manual Mode';
          manCard.style.display = 'none';
        } else {
          badge.className = 'badge badge-man';
          badge.innerText = 'Manual Mode';
          modeBtn.innerText = 'Switch to Auto Mode';
          manCard.style.display = 'block';
        }

        // Profiles Buttons
        for (let i = 0; i < 3; i++) {
          const btn = document.getElementById('pbtn' + i);
          btn.innerText = d.profiles[i].name;
          if (i === d.activeProfile) {
            btn.classList.add('active');
          } else {
            btn.classList.remove('active');
          }
        }

        // Profile Specific Controls
        const curProf = d.profiles[d.activeProfile];
        document.getElementById('threshVal').innerText = curProf.threshold + ' cm';
        document.getElementById('threshSlider').value = curProf.threshold;
        document.getElementById('buzzToggle').checked = curProf.buzzer;
        document.getElementById('monToggle').checked = curProf.monitoring;

        // Manual LEDs
        document.getElementById('mGreen').className = d.leds.g ? 'led-btn active-g' : 'led-btn';
        document.getElementById('mBlue').className  = d.leds.b ? 'led-btn active-b' : 'led-btn';
        document.getElementById('mRed').className   = d.leds.r ? 'led-btn active-r' : 'led-btn';

      } catch (e) {}
    }

    async function selectProfile(idx) {
      await fetch('/api/profile?action=select&idx=' + idx, { method: 'POST' });
      fetchStatus();
    }

    async function renameActiveProfile() {
      const cur = currentData.profiles[currentData.activeProfile].name;
      const n = prompt("Enter new profile name:", cur);
      if (n && n.trim()) {
        await fetch('/api/profile?action=rename&name=' + encodeURIComponent(n.trim()), { method: 'POST' });
        fetchStatus();
      }
    }

    async function updateThreshold(val) {
      await fetch('/api/profile?action=threshold&val=' + val, { method: 'POST' });
    }

    async function toggleBuzzer(val) {
      await fetch('/api/buzzer?state=' + (val ? '1' : '0'), { method: 'POST' });
    }

    async function toggleMonitoring(val) {
      await fetch('/api/monitor?state=' + (val ? '1' : '0'), { method: 'POST' });
    }

    async function toggleMode() {
      await fetch('/api/mode', { method: 'POST' });
      fetchStatus();
    }

    async function toggleLed(color) {
      await fetch('/api/led?color=' + color, { method: 'POST' });
      fetchStatus();
    }

    setInterval(fetchStatus, 800);
    fetchStatus();
  </script>
</body>
</html>
)rawliteral";

// ======================= WEB SERVER HANDLERS ===================
void handleRoot() {
  server.send_P(200, "text/html", INDEX_HTML);
}

void handleStatusApi() {
  String json = "{";
  json += "\"distance\":" + String(liveDistance, 1) + ",";
  json += "\"pir\":" + String(livePir ? "true" : "false") + ",";
  json += "\"alarm\":" + String(alarmState ? "true" : "false") + ",";
  json += "\"autoMode\":" + String(autoMode ? "true" : "false") + ",";
  json += "\"activeProfile\":" + String(activeProfile) + ",";
  json += "\"bleConnected\":" + String(bleDeviceConnected ? "true" : "false") + ",";
  json += "\"leds\":{\"g\":" + String(digitalRead(PIN_LED_GREEN) == HIGH ? "true" : "false") + ",";
  json += "\"b\":" + String(digitalRead(PIN_LED_BLUE) == HIGH ? "true" : "false") + ",";
  json += "\"r\":" + String(digitalRead(PIN_LED_RED) == HIGH ? "true" : "false") + "},";
  json += "\"profiles\":[";
  for (int i = 0; i < NUM_PROFILES; i++) {
    json += "{\"name\":\"" + String(profiles[i].name) + "\",";
    json += "\"threshold\":" + String(profiles[i].distanceThreshold) + ",";
    json += "\"buzzer\":" + String(profiles[i].buzzerEnabled ? "true" : "false") + ",";
    json += "\"monitoring\":" + String(profiles[i].monitoringActive ? "true" : "false") + "}";
    if (i < NUM_PROFILES - 1) json += ",";
  }
  json += "]}";
  server.send(200, "application/json", json);
}

void handleProfileApi() {
  if (server.hasArg("action")) {
    String act = server.arg("action");
    if (act == "select" && server.hasArg("idx")) {
      int idx = server.arg("idx").toInt();
      if (idx >= 0 && idx < NUM_PROFILES) {
        activeProfile = idx;
        saveActiveProfile();
      }
    } else if (act == "rename" && server.hasArg("name")) {
      String newName = server.arg("name");
      strncpy(profiles[activeProfile].name, newName.c_str(), sizeof(profiles[activeProfile].name) - 1);
      profiles[activeProfile].name[sizeof(profiles[activeProfile].name) - 1] = '\0';
      saveProfileData(activeProfile);
    } else if (act == "threshold" && server.hasArg("val")) {
      profiles[activeProfile].distanceThreshold = constrain(server.arg("val").toInt(), 10, 100);
      saveProfileData(activeProfile);
    }
  }
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleBuzzerApi() {
  if (server.hasArg("state")) {
    profiles[activeProfile].buzzerEnabled = (server.arg("state") == "1");
    saveProfileData(activeProfile);
  }
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleMonitorApi() {
  if (server.hasArg("state")) {
    profiles[activeProfile].monitoringActive = (server.arg("state") == "1");
    saveProfileData(activeProfile);
  }
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleModeApi() {
  autoMode = !autoMode;
  saveActiveProfile();
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleLedApi() {
  if (!autoMode && server.hasArg("color")) {
    String c = server.arg("color");
    if (c == "g") manualGreen = !manualGreen;
    if (c == "b") manualBlue  = !manualBlue;
    if (c == "r") manualRed   = !manualRed;
  }
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

// ======================= BUTTON DEBOUNCE =======================
void checkPushButton() {
  static int lastButtonState = HIGH;
  static unsigned long lastDebounceTime = 0;
  int reading = digitalRead(PIN_BUTTON);

  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
    static int debouncedState = HIGH;
    if (reading != debouncedState) {
      debouncedState = reading;
      if (debouncedState == LOW) { // Button Pressed
        autoMode = !autoMode;
        saveActiveProfile();
        Serial.printf("[StudyMonitor] Mode toggled via push button -> %s\n",
                      autoMode ? "AUTOMATIC" : "MANUAL");
        // Quick feedback beep
        digitalWrite(PIN_BUZZER, HIGH);
        delay(60);
        digitalWrite(PIN_BUZZER, LOW);
      }
    }
  }
  lastButtonState = reading;
}

// ======================= BLE SETUP & NOTIFY ====================
void setupBLE() {
  BLEDevice::init("StudyMonitor");
  pBleServer = BLEDevice::createServer();
  pBleServer->setCallbacks(new ServerCallbacks());

  BLEService* pService = pBleServer->createService(BLE_SERVICE_UUID);

  // Status Characteristic (Read / Notify)
  pStatusChar = pService->createCharacteristic(
    BLE_CHAR_STATUS_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pStatusChar->addDescriptor(new BLE2902());

  // Command Characteristic (Write)
  pCommandChar = pService->createCharacteristic(
    BLE_CHAR_COMMAND_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );
  pCommandChar->setCallbacks(new CommandCallbacks());

  pService->start();

  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(BLE_SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06); // iPhone connection helpers
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
}

void notifyBleStatus() {
  if (bleDeviceConnected && pStatusChar != nullptr) {
    char buf[64];
    snprintf(buf, sizeof(buf), "D:%.1f|P:%d|A:%d|M:%d|P:%d",
             liveDistance, livePir ? 1 : 0, alarmState ? 1 : 0,
             autoMode ? 1 : 0, activeProfile + 1);
    pStatusChar->setValue(buf);
    pStatusChar->notify();
  }
}

// ======================= INITIAL SETUP =========================
void setup() {
  Serial.begin(115200);
  delay(100);

  // 1. Initialize GPIO Pins
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);

  setLeds(false, false, false);
  setBuzzer(false);

  // 2. Load Saved Preferences from Flash
  loadPreferences();
  Serial.println("[StudyMonitor] Loaded settings from flash memory.");

  // 3. Start Wi-Fi Access Point
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  Serial.println("[StudyMonitor] Wi-Fi AP Started.");
  Serial.printf("  SSID: %s | Pass: %s\n", AP_SSID, AP_PASSWORD);
  Serial.printf("  Dashboard URL: http://%s/\n", WiFi.softAPIP().toString().c_str());

  // 4. Setup Web Server Endpoints
  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/status", HTTP_GET, handleStatusApi);
  server.on("/api/profile", HTTP_POST, handleProfileApi);
  server.on("/api/buzzer", HTTP_POST, handleBuzzerApi);
  server.on("/api/monitor", HTTP_POST, handleMonitorApi);
  server.on("/api/mode", HTTP_POST, handleModeApi);
  server.on("/api/led", HTTP_POST, handleLedApi);
  server.begin();
  Serial.println("[StudyMonitor] HTTP Web Server started.");

  // 5. Initialize Bluetooth Low Energy (BLE)
  setupBLE();
  Serial.println("[StudyMonitor] BLE Server initialized & advertising as 'StudyMonitor'.");

  // Power-on self test: flash LEDs briefly
  setLeds(true, true, true);
  delay(300);
  setLeds(false, false, false);
}

// ======================= MAIN LOOP =============================
void loop() {
  server.handleClient();
  checkPushButton();

  unsigned long now = millis();

  // Periodic sensor sampling & state processing
  if (now - lastSensorReadTime >= SENSOR_INTERVAL_MS) {
    lastSensorReadTime = now;
    updateSensors();
    processControlLogic();
  }

  // Periodic BLE status notification
  if (now - lastBleNotifyTime >= BLE_NOTIFY_MS) {
    lastBleNotifyTime = now;
    notifyBleStatus();
  }
}
