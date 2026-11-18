# StudySense – Smart Study Companion

A Progressive Web & Hybrid companion app + ESP32 firmware for a smart desk study monitor with circular Pomodoro timer, multi-user profiles, HC-SR04 posture monitoring, PIR presence auto-pause, WS2812B LED ring status, buzzer alerts, ambient focus audio, and an interactive PC Hardware Simulator.

**Live Web App (Vercel):** https://studysense-eight.vercel.app  
**Direct Android APK Download:** https://studysense-eight.vercel.app/StudySense.apk

## Project Structure

```
├── index.html                  # Complete Web & PWA Companion App + PC Hardware Simulator
├── StudySense.apk              # Signed, installable native Android APK (exact same app)
├── manifest.json               # PWA manifest
├── sw.js                       # Service worker for offline shell caching
├── icon.svg                    # App icon
├── vercel.json                 # Serves StudySense.apk with Android MIME type & download header
├── esp32/
│   └── StudySense_ESP32.ino    # Matching ESP32 Arduino firmware (Wi-Fi + NVS flash + sensors)
└── android/
    ├── AndroidManifest.xml
    ├── build-apk.sh            # One-command script to rebuild & sign StudySense.apk
    ├── res/                    # App theme & launcher icons
    └── src/com/studysense/app/MainActivity.java
```

## Quick Start

### 1. Run on PC
- Visit **https://studysense-eight.vercel.app**, or double-click `index.html` locally in Chrome/Edge.
- Use the **PC Hardware Simulator** panel to drag the **HC-SR04 Student Distance** slider below `30 cm` (triggers red LED ring, posture banner, and buzzer) or toggle **PIR Motion** off (auto-pauses timer and switches LED ring to amber).

### 2. Install on Android
- **Direct APK Install (Recommended):** Click **Download Android APK** on the web app (or open `https://studysense-eight.vercel.app/StudySense.apk`), tap the downloaded `StudySense.apk`, and allow installation from your browser.
- **Rebuild the APK locally:** Run `./android/build-apk.sh` (requires JDK + Android SDK build-tools). It bundles the latest `index.html` into `StudySense.apk` and signs it automatically.

### 3. Flash ESP32 Firmware (`esp32/StudySense_ESP32.ino`)
1. Open `esp32/StudySense_ESP32.ino` in **Arduino IDE**.
2. Install libraries via Library Manager:
   - **ArduinoJson** (v6 or v7)
   - **Adafruit NeoPixel**
3. Set `WIFI_SSID` and `WIFI_PASSWORD` at the top of the sketch and upload to your ESP32 board.
4. Open Serial Monitor (`115200 baud`) to see the ESP32's local IP address (e.g., `192.168.1.100`), then enter it in the **ESP32 Link** tab of the app.

> **Note on HTTPS vs local ESP32 IP:** Modern browsers block `http://192.168.x.x` requests from `https://` pages (Mixed Content). To sync directly over local Wi-Fi with the ESP32, open `index.html` locally on your PC or run via the Android Studio WebView APK.

#### Default ESP32 Pinout

| Component | Pin | Notes |
| --- | --- | --- |
| HC-SR04 `TRIG` | `GPIO 5` | Ultrasonic Trigger |
| HC-SR04 `ECHO` | `GPIO 18` | Use a 1kΩ / 2kΩ voltage divider to step 5V down to 3.3V |
| PIR `OUT` | `GPIO 19` | HC-SR501 motion sensor |
| LED Ring `DIN` | `GPIO 13` | WS2812B / NeoPixel (`LED_COUNT = 16`) |
| Buzzer `+` | `GPIO 23` | Piezo buzzer |
| Push Button | `GPIO 4` | Wired to `GND` (`INPUT_PULLUP`) |

#### ESP32 HTTP API
- `POST /config` — Saves active student's profile (`studentName`, `studyDurationMins`, `breakDurationMins`, `minPostureDistCm`, `postureAlertEnabled`, `buzzerEnabled`, `ledEnabled`) to ESP32 NVS flash (`Preferences`).
- `GET /status` — Returns live sensor readings (`distanceCm`, `pirPresent`, `postureAlert`, `timerRunning`, `timerMode`, `timeLeftSec`, `ledColor`).
- `POST /timer` — Controls the onboard timer (`start`, `pause`, `reset`, `toggle`).
