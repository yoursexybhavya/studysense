# StudySense – Smart Study Companion

A Progressive Web & Hybrid companion app + ESP32 firmware for a smart desk study monitor with circular Pomodoro timer, multi-user profiles, HC-SR04 posture monitoring, PIR presence auto-pause, WS2812B LED ring status, buzzer alerts, ambient focus audio, and an interactive PC Hardware Simulator.

**Live Web App (Vercel):** https://studysense-eight.vercel.app  
**Direct Android APK Download:** https://studysense-eight.vercel.app/StudySense.apk  
**3D Print STL Pack (Bambu Studio):** https://studysense-eight.vercel.app/StudySense_3D_Print_Pack_BambuStudio.zip  
**Complete Project Guide (PDF):** [StudySense_Complete_Project_Guide.pdf](file:///Users/krishnajangid/Documents/Idea%20Lab/StudySense_Complete_Project_Guide.pdf) (or [View Online](https://studysense-eight.vercel.app/StudySense_Complete_Project_Guide.pdf))  
**Complete Team Pack (ZIP):** https://studysense-eight.vercel.app/StudySense_Complete_Team_Pack.zip

## Project Structure

```
├── index.html                  # Complete Web & PWA Companion App + PC Hardware Simulator
├── StudySense.apk              # Signed, installable native Android APK (exact same app)
├── manifest.json               # PWA manifest
├── sw.js                       # Service worker for offline shell caching
├── icon.svg                    # App icon
├── vercel.json                 # Serves StudySense.apk & STL pack with download headers
├── 3d_model/                   # Bambu Studio CAD Package & Blender Production Source
│   ├── 01_Base_Lower_Stand.stl # L-stand with ESP32 cradle & USB-C cutout
│   ├── 02_Neck_and_Head_Shell.stl # Neck with 3x LED holes & 7° angled head cup
│   ├── 03_Sensor_Faceplate_Black.stl # Bezel with HC-SR04 & PIR cutouts
│   ├── 04_Accent_Ring_Orange.stl # Halo accent ring (Bambu AMS orange)
│   ├── 05_Button_Cap.stl       # Ergonomic rear plunger button
│   ├── StudySense_Complete_Assembly.stl # Unified master STL
│   ├── StudySense_Enclosure.blend # Blender studio lighting & PBR scene
│   └── 3D_PRINTING_GUIDE.md    # Detailed Bambu Studio slicing parameters
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

### 3. Flash ESP32 Firmware (`esp32/SmartStudyMonitor/SmartStudyMonitor.ino`)
1. Open `esp32/SmartStudyMonitor/SmartStudyMonitor.ino` in **Arduino IDE**.
2. Select Board: **ESP32 Dev Module** (Partition Scheme: Default 4MB with SPIFFS or Minimal SPIFFS for BLE).
3. Connect ESP32 via USB and upload.
4. Open Serial Monitor (`115200 baud`) to observe real-time sensor heartbeats and status logs.
   - Interactive Serial Commands supported: Type `START`, `TEST`, `BEEP`, `AUTO`, or `MANUAL` into the Serial Monitor input.

### 4. 3D Print Enclosure (Bambu Studio / Bambu Lab 3D Printers)
The project includes a production-grade 5-piece modular enclosure engineered specifically for Bambu Lab printers (X1C / P1S / P1P / A1 / A1 mini) using Bambu Studio:

- **01_Base_Lower_Stand.stl**: White PLA, 0.20mm Standard, 15% gyroid infill, no supports.
- **02_Neck_and_Head_Shell.stl**: White PLA, upright, 0.16mm, Tree Supports (Auto) enabled.
- **03_Sensor_Faceplate_Black.stl**: Black Matte PLA, face-down on Textured PEI plate, no supports.
- **04_Accent_Ring_Orange.stl**: Orange PLA, 100% infill, no supports.
- **05_Button_Cap.stl**: Ergonomic plunger with retention lip, 100% infill, 3mm brim.
- **Full Guide:** Read [3D_PRINTING_GUIDE.md](file:///Users/krishnajangid/Documents/Idea%20Lab/3d_model/3D_PRINTING_GUIDE.md) for step-by-step plate setups, tolerances, and wire routing.

> **Note on Wire Slack:** The 11 cm soldered wiring harness fits the enclosure's internal vertical wire path (~105 mm) with zero tension on solder joints.

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
