# StudySense – Smart Study Companion

A Progressive Web & Hybrid companion app + ESP32 firmware for a smart desk study monitor with circular Pomodoro timer, multi-user profiles, HC-SR04 posture monitoring, PIR presence auto-pause, WS2812B LED ring status, buzzer alerts, ambient focus audio, and an interactive PC Hardware Simulator.

**Live Web App (Vercel):** https://studysense-eight.vercel.app  
**Direct Android APK Download:** https://studysense-eight.vercel.app/StudySense.apk  
**Direct iOS App Download (IPA):** https://studysense-eight.vercel.app/StudySense.ipa  
**Complete Project Guide (PDF):** [StudySense_Complete_Project_Guide.pdf](file:///Users/krishnajangid/Documents/Idea%20Lab/StudySense_Complete_Project_Guide.pdf) (or [View Online](https://studysense-eight.vercel.app/StudySense_Complete_Project_Guide.pdf))  
**Final 3D Component (Bambu Studio 3MF):** [StudySense_V4_Target_BambuStudio.3mf](file:///Users/krishnajangid/Documents/Idea%20Lab/3d_model/StudySense_V4_Target_BambuStudio.3mf)  
**Final 3D Parts & Assembly Guide (PDF):** [StudySense_V4_Target_Parts_Joining_Guide.pdf](file:///Users/krishnajangid/Documents/Idea%20Lab/3d_model/StudySense_V4_Target_Parts_Joining_Guide.pdf)  
**Final Build Plate Render:** [render_v4_target_build_plate.png](file:///Users/krishnajangid/Documents/Idea%20Lab/3d_model/render_v4_target_build_plate.png)  
**Project Photos & Hardware Archive:** [project_photos/README.md](file:///Users/krishnajangid/Documents/Idea%20Lab/project_photos/README.md) (All 30 raw and curated photos)

## Project Structure

```
├── index.html                  # Complete Web & PWA Companion App + PC Hardware Simulator
├── StudySense.apk              # Signed, installable native Android APK (exact same app)
├── StudySense.ipa              # Signed, installable native iOS IPA (Apple Developer signed)
├── manifest.json               # PWA manifest
├── sw.js                       # Service worker for offline shell caching
├── icon.svg                    # App icon
├── vercel.json                 # Serves StudySense.apk & StudySense.ipa with correct MIME types
├── 3d_model/                   # Final 3D Component (Bambu Studio 3MF, Parts Joining Guide PDF & STLs)
├── project_photos/             # Full photographic archive (raw uploads + curated categories)
│   ├── curated/                # Hardware wiring, design references, and slicer feedback
│   └── raw_uploads/            # All 30 raw user-uploaded project photos
├── ios/                        # Native Swift & SwiftUI iOS application
│   ├── StudySense.xcodeproj   # Xcode project (iOS 16+)
│   ├── project.yml             # XcodeGen project specification
│   ├── build-and-install.sh    # One-command script to build, sign & install to iPhone
│   └── Sources/                # SwiftUI App, WKWebView, Taptic Engine bridge, Assets, Info.plist
├── esp32/
│   └── SmartStudyMonitor/      # Arduino sketch uploaded to ESP32 DevKit
│       └── SmartStudyMonitor.ino # SoftAP (192.168.4.1), BLE, 3 Profiles, Auto/Manual modes
└── android/
    ├── AndroidManifest.xml
    ├── build-apk.sh            # One-command script to rebuild & sign StudySense.apk
    ├── res/                    # App theme & launcher icons
    └── src/com/studysense/app/MainActivity.java
```

## Visual Archive & Hardware Reference Photos

A comprehensive catalog of physical hardware wiring, sensor calibration measurements, and 3D industrial design references is available in [`project_photos/`](project_photos/):

- **[Curated Gallery (`project_photos/curated/`)](project_photos/curated/):**
  - **Hardware & Wiring:** ESP32 breadboard schematics, 11 cm wire harness scale, HC-SR04 ultrasonic & HC-SR501 PIR sensor closeups.
  - **Design References:** High-resolution product renders and industrial aesthetic guidelines.
  - **Slicer & CAD Feedback:** Bambu Studio slicing screenshots, bed volume limits, and iterative geometry optimizations.
- **[Raw Uploads (`project_photos/raw_uploads/`)](project_photos/raw_uploads/):** Complete 30-file verbatim archive of every photo shared during development.
- **[Full Photo Documentation](project_photos/README.md):** Complete catalog with thumbnails, sensor specifications, and hardware notes.

## Quick Start

### 1. Run on PC
- Visit **https://studysense-eight.vercel.app**, or double-click `index.html` locally in Chrome/Edge.
- Use the **PC Hardware Simulator** panel to drag the **HC-SR04 Student Distance** slider below `30 cm` (triggers red LED ring, posture banner, and buzzer) or toggle **PIR Motion** off (auto-pauses timer and switches LED ring to amber).

### 2. Install on Android
- **Direct APK Install (Recommended):** Click **Download Android APK** on the web app (or open `https://studysense-eight.vercel.app/StudySense.apk`), tap the downloaded `StudySense.apk`, and allow installation from your browser.
- **Rebuild the APK locally:** Run `./android/build-apk.sh` (requires JDK + Android SDK build-tools). It bundles the latest `index.html` into `StudySense.apk` and signs it automatically.

### 3. Install on iPhone (iOS)
- **Direct Device Install (Connected iPhone):** Run `./ios/build-and-install.sh`. It automatically compiles the Swift app, codesigns with your Apple ID, packages `StudySense.ipa`, and installs it directly onto your connected iPhone (`Krishna’s iPhone 16`) over USB.
- **First-Time Developer Trust (Required by Apple):** On your iPhone, open **Settings** → **General** → **VPN & Device Management** → tap your developer certificate (`krishnajangid6781@gmail.com`) → tap **Trust "Apple Development: krishnajangid6781@gmail.com"**. You can now launch StudySense directly from your home screen!
- **Download Pre-Packaged IPA:** [`StudySense.ipa`](https://studysense-eight.vercel.app/StudySense.ipa) can also be installed using any iOS installer (AltStore, Sideloadly, TrollStore).
- **Safari Instant PWA:** Open `https://studysense-eight.vercel.app` in Safari on your iPhone, tap **Share** (square with arrow), and tap **Add to Home Screen**.

### 4. Flash ESP32 Firmware (`esp32/SmartStudyMonitor/SmartStudyMonitor.ino`)
1. Open `esp32/SmartStudyMonitor/SmartStudyMonitor.ino` in **Arduino IDE**.
2. Select board **ESP32 Dev Module** and set Partition Scheme to **Huge APP (3MB No OTA / 1MB SPIFFS)**.
3. Upload to your connected ESP32 board over USB Serial (`115200 baud`).

### 5. 3D Print the Desktop Enclosure (Bambu Studio)
- **One-Click Print (Final 3D Component):** Open [`StudySense_V4_Target_BambuStudio.3mf`](file:///Users/krishnajangid/Documents/Idea%20Lab/3d_model/StudySense_V4_Target_BambuStudio.3mf) directly in **Bambu Studio** on your Mac. All 6 parts load pre-arranged on the build plate.
- **Parts & Assembly Guide (PDF):** See [`StudySense_V4_Target_Parts_Joining_Guide.pdf`](file:///Users/krishnajangid/Documents/Idea%20Lab/3d_model/StudySense_V4_Target_Parts_Joining_Guide.pdf) for the complete visual assembly manual, exploded diagrams, and joining steps.
- **Individual STL Files:** Available in [`3d_model/individual_stl/`](file:///Users/krishnajangid/Documents/Idea%20Lab/3d_model/individual_stl) (Base Pedestal, Neck & Head Pod, Sensor Faceplate, Accent Ring, Base Bottom Plate, and Button Cap).

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
- [@babooshki](https://github.com/babooshki) / [@babooshkirussian](https://github.com/babooshkirussian)
