# StudySense – Smart Study Companion

A Progressive Web & Hybrid companion app + ESP32 firmware for a smart desk study monitor with circular Pomodoro timer, multi-user profiles, HC-SR04 posture monitoring, PIR presence auto-pause, WS2812B LED ring status, buzzer alerts, ambient focus audio, and an interactive PC Hardware Simulator.

**Live Web App (Vercel):** https://studysense-eight.vercel.app

## Project Structure

```
├── index.html                  # Complete Web & PWA Companion App + PC Hardware Simulator
├── manifest.json               # PWA manifest (installable on Android & Desktop)
├── sw.js                       # Service worker for offline shell caching
├── icon.svg                    # App icon
├── esp32/
│   └── StudySense_ESP32.ino    # Matching ESP32 Arduino firmware (Wi-Fi + NVS flash + sensors)
└── android/
    └── MainActivity.java       # Drop-in Android Studio WebView wrapper
```

## Quick Start

### 1. Run on PC
- Visit **https://studysense-eight.vercel.app**, or double-click `index.html` locally in Chrome/Edge.
- Use the **PC Hardware Simulator** panel to drag the **HC-SR04 Student Distance** slider below `30 cm` (triggers red LED ring, posture banner, and buzzer) or toggle **PIR Motion** off (auto-pauses timer and switches LED ring to amber).

### 2. Install on Android
- **Option A — Instant PWA (Recommended):** Open `https://studysense-eight.vercel.app` in Chrome on Android, tap the menu (`⋮`), and choose **Add to Home screen / Install app**.
- **Option B — Native Android Studio Wrapper:** Create an Empty Views Activity project, place `index.html` inside `app/src/main/assets/index.html`, copy `android/MainActivity.java`, and add `<uses-permission android:name="android.permission.INTERNET" />` plus `android:usesCleartextTraffic="true"` on `<application>` in `AndroidManifest.xml`.

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
