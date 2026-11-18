/*
 * StudySense – Smart Study Companion (ESP32 Firmware)
 * ---------------------------------------------------
 * Matches the StudySense Companion Web/Android App.
 *
 * Required Arduino Libraries:
 *   1. ArduinoJson (v6 or v7) by Benoit Blanchon
 *   2. Adafruit NeoPixel by Adafruit
 *   (WiFi, WebServer, and Preferences are built into the ESP32 Arduino Core)
 *
 * HTTP Endpoints (with CORS enabled):
 *   POST /config -> Receives student profile JSON and persists it to NVS flash
 *   GET  /status -> Returns live HC-SR04 distance, PIR state, and timer status
 *   POST /timer  -> Controls timer ("start" | "pause" | "reset" | "toggle")
 */

#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

// ===================== USER CONFIGURATION =====================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Hardware Pins (adjust to match your wiring)
#define TRIG_PIN       5    // HC-SR04 Ultrasonic Trigger
#define ECHO_PIN       18   // HC-SR04 Ultrasonic Echo (use voltage divider to 3.3V!)
#define PIR_PIN        19   // HC-SR501 PIR Motion Sensor OUT
#define LED_PIN        13   // WS2812B / NeoPixel LED Ring DIN
#define LED_COUNT      16   // Number of LEDs in ring (12 or 16)
#define BUZZER_PIN     23   // Piezo Buzzer (+)
#define BUTTON_PIN     4    // Physical Start/Stop push button (wired to GND)

// Timing Constants
const unsigned long SENSOR_INTERVAL_MS     = 250;
const unsigned long PIR_AWAY_GRACE_MS      = 5000;  // Pause timer if no motion for 5s
const unsigned long BUZZER_COOLDOWN_MS     = 1500;
const unsigned long BUTTON_DEBOUNCE_MS     = 250;

// ===================== GLOBALS =====================
WebServer server(80);
Preferences prefs;
Adafruit_NeoPixel ring(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

struct ProfileConfig {
  String studentName         = "Aarav";
  int    studyDurationMins   = 25;
  int    breakDurationMins   = 5;
  int    minPostureDistCm    = 30;
  bool   postureAlertEnabled = true;
  bool   buzzerEnabled       = true;
  bool   ledEnabled          = true;
};

ProfileConfig cfg;

// Live Runtime State
float liveDistanceCm       = 45.0;
bool  pirPresent           = true;
bool  postureWarningActive = false;
bool  timerRunning         = false;
bool  inBreakMode          = false;
int   timeLeftSec          = 25 * 60;
String currentLedColor     = "green";

unsigned long lastSensorReadMs = 0;
unsigned long lastTimerTickMs  = 0;
unsigned long lastPirHighMs    = 0;
unsigned long lastBeepMs       = 0;
unsigned long lastButtonMs     = 0;

// ===================== HELPERS =====================
void sendCorsHeaders() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

void handleOptions() {
  sendCorsHeaders();
  server.send(204);
}

void setRingColor(uint8_t r, uint8_t g, uint8_t b, const char* name) {
  currentLedColor = name;
  uint32_t color = cfg.ledEnabled ? ring.Color(r, g, b) : ring.Color(0, 0, 0);
  for (int i = 0; i < LED_COUNT; i++) {
    ring.setPixelColor(i, color);
  }
  ring.show();
}

void beep(int freqHz, int durationMs) {
  if (!cfg.buzzerEnabled) return;
  tone(BUZZER_PIN, freqHz, durationMs);
}

float readUltrasonicCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // 25ms timeout (~4.2m max) so the web server never stalls
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 25000UL);
  if (duration == 0) return liveDistanceCm; // Keep last valid reading on timeout
  float cm = (duration * 0.0343f) / 2.0f;
  return constrain(cm, 2.0f, 300.0f);
}

// ===================== NVS FLASH STORAGE =====================
void loadProfileFromFlash() {
  prefs.begin("studysense", true);
  cfg.studentName         = prefs.getString("name", "Aarav");
  cfg.studyDurationMins   = prefs.getInt("studyMins", 25);
  cfg.breakDurationMins   = prefs.getInt("breakMins", 5);
  cfg.minPostureDistCm    = prefs.getInt("minDist", 30);
  cfg.postureAlertEnabled = prefs.getBool("posture", true);
  cfg.buzzerEnabled       = prefs.getBool("buzzer", true);
  cfg.ledEnabled          = prefs.getBool("led", true);
  prefs.end();

  inBreakMode  = false;
  timerRunning = false;
  timeLeftSec  = cfg.studyDurationMins * 60;
}

void saveProfileToFlash() {
  prefs.begin("studysense", false);
  prefs.putString("name", cfg.studentName);
  prefs.putInt("studyMins", cfg.studyDurationMins);
  prefs.putInt("breakMins", cfg.breakDurationMins);
  prefs.putInt("minDist", cfg.minPostureDistCm);
  prefs.putBool("posture", cfg.postureAlertEnabled);
  prefs.putBool("buzzer", cfg.buzzerEnabled);
  prefs.putBool("led", cfg.ledEnabled);
  prefs.end();
}

// ===================== HTTP ROUTES =====================
void handleConfigPost() {
  sendCorsHeaders();
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"error\":\"Missing JSON body\"}");
    return;
  }

#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<512> doc;
#endif

  DeserializationError err = deserializeJson(doc, server.arg("plain"));
  if (err) {
    server.send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
    return;
  }

  cfg.studentName         = doc["studentName"]         | cfg.studentName;
  cfg.studyDurationMins   = constrain((int)(doc["studyDurationMins"] | cfg.studyDurationMins), 1, 180);
  cfg.breakDurationMins   = constrain((int)(doc["breakDurationMins"] | cfg.breakDurationMins), 1, 60);
  cfg.minPostureDistCm    = constrain((int)(doc["minPostureDistCm"]  | cfg.minPostureDistCm), 10, 100);
  cfg.postureAlertEnabled = doc["postureAlertEnabled"] | cfg.postureAlertEnabled;
  cfg.buzzerEnabled       = doc["buzzerEnabled"]       | cfg.buzzerEnabled;
  cfg.ledEnabled          = doc["ledEnabled"]          | cfg.ledEnabled;

  saveProfileToFlash();

  // Reset timer to newly loaded student's focus duration
  inBreakMode  = false;
  timerRunning = false;
  timeLeftSec  = cfg.studyDurationMins * 60;

  Serial.printf("[StudySense] Profile synced & saved: %s (%dm study / %dm break / %dcm min)\n",
                cfg.studentName.c_str(), cfg.studyDurationMins, cfg.breakDurationMins, cfg.minPostureDistCm);

  beep(950, 90);
  server.send(200, "application/json", "{\"status\":\"ok\",\"saved\":true}");
}

void handleStatusGet() {
  sendCorsHeaders();
#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<384> doc;
#endif

  doc["studentName"]  = cfg.studentName;
  doc["distanceCm"]   = (int)round(liveDistanceCm);
  doc["pirPresent"]   = pirPresent;
  doc["postureAlert"] = postureWarningActive;
  doc["timerRunning"] = timerRunning;
  doc["timerMode"]    = inBreakMode ? "break" : "study";
  doc["timeLeftSec"]  = timeLeftSec;
  doc["ledColor"]     = cfg.ledEnabled ? currentLedColor : "off";

  String out;
  serializeJson(doc, out);
  server.send(200, "application/json", out);
}

void handleTimerPost() {
  sendCorsHeaders();
#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<256> doc;
#endif

  if (server.hasArg("plain") && !deserializeJson(doc, server.arg("plain"))) {
    String action = doc["action"] | "";
    String mode   = doc["mode"]   | "";
    if (mode == "study" || mode == "break") {
      inBreakMode = (mode == "break");
    }
    if (action == "start") {
      timerRunning = true;
      lastTimerTickMs = millis();
    } else if (action == "pause") {
      timerRunning = false;
    } else if (action == "reset") {
      timerRunning = false;
      timeLeftSec = (inBreakMode ? cfg.breakDurationMins : cfg.studyDurationMins) * 60;
    } else if (action == "toggle") {
      timerRunning = !timerRunning;
      lastTimerTickMs = millis();
    }
  }
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

// ===================== SETUP & LOOP =====================
void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  ring.begin();
  ring.setBrightness(65);
  ring.show();

  loadProfileFromFlash();
  lastPirHighMs = millis();

  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[StudySense] Connecting to Wi-Fi");
  setRingColor(0, 140, 255, "cyan");

  unsigned long wifiStart = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiStart < 15000) {
    delay(300);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[StudySense] Connected! Enter this IP in the app: %s\n",
                  WiFi.localIP().toString().c_str());
    setRingColor(16, 185, 129, "green");
    beep(880, 120);
  } else {
    Serial.println("\n[StudySense] Wi-Fi timeout — running offline with saved flash profile.");
    setRingColor(245, 158, 11, "amber");
  }

  server.on("/config", HTTP_OPTIONS, handleOptions);
  server.on("/config", HTTP_POST, handleConfigPost);
  server.on("/status", HTTP_OPTIONS, handleOptions);
  server.on("/status", HTTP_GET, handleStatusGet);
  server.on("/timer",  HTTP_OPTIONS, handleOptions);
  server.on("/timer",  HTTP_POST, handleTimerPost);
  server.begin();
}

void loop() {
  server.handleClient();
  unsigned long now = millis();

  // 1. Physical Push Button (Start / Pause)
  if (digitalRead(BUTTON_PIN) == LOW && (now - lastButtonMs > BUTTON_DEBOUNCE_MS)) {
    lastButtonMs = now;
    timerRunning = !timerRunning;
    lastTimerTickMs = now;
    beep(timerRunning ? 780 : 520, 80);
    Serial.printf("[StudySense] Physical button -> Timer %s\n", timerRunning ? "STARTED" : "PAUSED");
  }

  // 2. Read Ultrasonic & PIR Sensors
  if (now - lastSensorReadMs >= SENSOR_INTERVAL_MS) {
    lastSensorReadMs = now;
    liveDistanceCm = readUltrasonicCm();

    if (digitalRead(PIR_PIN) == HIGH) {
      lastPirHighMs = now;
      pirPresent = true;
    } else if (now - lastPirHighMs > PIR_AWAY_GRACE_MS) {
      pirPresent = false;
    }

    if (!pirPresent) {
      postureWarningActive = false;
      if (timerRunning) {
        timerRunning = false;
        Serial.println("[StudySense] Student away -> Timer auto-paused.");
      }
      setRingColor(245, 158, 11, "amber");
    } else if (cfg.postureAlertEnabled && liveDistanceCm < cfg.minPostureDistCm) {
      postureWarningActive = true;
      setRingColor(244, 63, 94, "red");
      if (now - lastBeepMs >= BUZZER_COOLDOWN_MS) {
        lastBeepMs = now;
        beep(520, 120);
      }
    } else {
      postureWarningActive = false;
      setRingColor(16, 185, 129, "green");
    }
  }

  // 3. Countdown Timer Tick (1 Hz)
  if (timerRunning && (now - lastTimerTickMs >= 1000)) {
    lastTimerTickMs += 1000;
    if (timeLeftSec > 0) {
      timeLeftSec--;
    } else {
      timerRunning = false;
      beep(880, 400);
      inBreakMode = !inBreakMode;
      timeLeftSec = (inBreakMode ? cfg.breakDurationMins : cfg.studyDurationMins) * 60;
      Serial.printf("[StudySense] Session complete -> Next mode: %s\n", inBreakMode ? "BREAK" : "STUDY");
    }
  }
}
