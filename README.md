# StudySense – Smart Study Companion

A Progressive Web & Hybrid companion app + ESP32 firmware for a smart desk study monitor with circular Pomodoro timer, multi-user profiles, HC-SR04 posture monitoring, PIR presence auto-pause, WS2812B LED ring status, buzzer alerts, ambient focus audio, and an interactive PC Hardware Simulator.

**Live Web App (Vercel):** https://studysense-eight.vercel.app  
**Direct Android APK Download:** https://studysense-eight.vercel.app/StudySense.apk  
**Complete Project Guide (PDF):** [StudySense_Complete_Project_Guide.pdf](file:///Users/krishnajangid/Documents/Idea%20Lab/StudySense_Complete_Project_Guide.pdf) (or [View Online](https://studysense-eight.vercel.app/StudySense_Complete_Project_Guide.pdf))

## Project Structure

```
├── index.html                  # Complete Web & PWA Companion App + PC Hardware Simulator
├── StudySense.apk              # Signed, installable native Android APK (exact same app)
├── manifest.json               # PWA manifest
├── sw.js                       # Service worker for offline shell caching
├── icon.svg                    # App icon
├── vercel.json                 # Serves StudySense.apk with Android MIME type & download header
├── esp32/
│   └── SmartStudyMonitor/      # Arduino sketch uploaded to ESP32 DevKit
│       └── SmartStudyMonitor.ino # SoftAP (192.168.4.1), BLE, 3 Profiles, Auto/Manual modes
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

#### Hardware GPIO Pinout (ESP32 DevKit)

| Component | Pin | Circuit Notes |
| --- | --- | --- |
| PIR Motion Sensor `OUT` | `GPIO 27` | High when motion detected |
| HC-SR04 `TRIG` | `GPIO 13` | Ultrasonic trigger |
| HC-SR04 `ECHO` | `GPIO 14` | Step down 5V to ~3.3V via voltage divider |
| Push Button | `GPIO 22` | Wired to `GND` (`INPUT_PULLUP`). Short press = Study/Pause, Long press = Auto/Manual mode |
| Active Buzzer | `GPIO 23` | BC547 NPN transistor base driven via 1kΩ resistor |
| Green LED | `GPIO 26` | Connected via 220–330Ω resistor (Optimal Posture / Active) |
| Blue LED | `GPIO 25` | Connected via 220–330Ω resistor (Student Away / Standby) |
| Red LED | `GPIO 33` | Connected via 220–330Ω resistor (Posture Warning < threshold) |

#### Wi-Fi & Bluetooth
- **Wi-Fi SoftAP SSID:** `StudyMonitor`
- **Wi-Fi Password:** `study1234`
- **Embedded Web Dashboard:** `http://192.168.4.1`
- **BLE Device Name:** `StudyMonitor` (UUID Service: `4fafc201-1fb5-459e-8fcc-c5c9c331914b`)

#### ESP32 HTTP API
- `POST /config` — Saves active student's profile (`studentName`, `studyDurationMins`, `breakDurationMins`, `minPostureDistCm`, `postureAlertEnabled`, `buzzerEnabled`, `ledEnabled`) to ESP32 NVS flash (`Preferences`).
- `GET /status` — Returns live sensor readings (`distanceCm`, `pirPresent`, `postureAlert`, `timerRunning`, `timerMode`, `timeLeftSec`, `ledColor`).
- `POST /timer` — Controls the onboard timer (`start`, `pause`, `reset`, `toggle`).

## Contributors

- [@yoursexybhavya](https://github.com/yoursexybhavya)
- [@Abhi4Federal](https://github.com/Abhi4Federal) (`@mi35ju-ui`)
- [@babooshki](https://github.com/babooshki)
