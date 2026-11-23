# StudySense 3D Printing & Hardware Enclosure Guide
**Official Manufacturing Specs for Bambu Studio & Bambu Lab 3D Printers (H2S, X1C, P1S, A1, A1 Mini)**

---

## 🌟 Quick Overview: StudySense V6 Pro (Master Architecture)
**StudySense V6 Pro** restores the full-scale, robust ("rost") aesthetics of Version 4 with surgical mechanical fixes for the base pedestal and Bambu Studio slicing:
- **Full 72 mm Head Pod:** The iconic circular head pod (72.0 mm OD) is preserved at full master scale, providing ample room for the HC-SR04 ultrasonic transducer cans, crystal oscillator, and PIR Fresnel dome without any cramped or squished geometry.
- **Integrated Solid 3.0 mm Base Floor (Glue-Gun Ready):** `01_Base_Pedestal.stl` features a solid **3.0 mm flat bottom foundation** resting directly on the print bed ($Z=0$). Zero floating regions, zero slicing warnings in Bambu Studio! The interior floor provides a flat pocket with corner alignment tabs where you can drop the ESP32 and apply hot glue gun adhesive directly.
- **Clean 5-Component Architecture:** 4 main interlocking body pieces + 1 rear push-button cap. No messy extra lids.
- **Support-Free 3D Printing:** 100% manifold, support-free printing on all components with local origins resting flat on $Z=0$.

---

## 📐 Mechanical Dimensions (V6 Pro Master Architecture)

| Dimension / Metric | Value | Engineering Purpose |
| :--- | :--- | :--- |
| **Head Pod Diameter** | **&Oslash; 72.0 mm** circular pod | Full V4 scale; perfectly houses HC-SR04 & PIR dome |
| **Base Footprint** | 55.7 mm (W) &times; 81.2 mm (D) &times; 34.0 mm (H) | Stable, weighted desk footprint matching reference photo |
| **Base Floor Thickness** | **3.0 mm Solid** | 100% solid flat bed layer; hot-glue gun adhesion cradle |
| **Rear USB Cutout** | 12.5 mm &times; 7.0 mm | Direct access for Micro-USB or USB-C power cables |
| **Rear Push Button Port** | &Oslash; 6.5 mm with `05_Button_Cap` | Rear mode/reset switch |
| **Neck Column Height** | 58.0 mm lofted organic neck | 16.0 &times; 11.0 mm hollow continuous wire conduit |
| **Status LED Ports** | 3&times; &Oslash; 3.2 mm (&Oslash; 5.0 mm counterbore) | Green (Z=76mm), Blue (Z=62mm), Red (Z=48mm) |
| **Top Stalk / Fin Height** | Reaches **Z = 152.0 mm** | Iconic handle / antenna aesthetic feature |
| **PIR Sensor Aperture** | &Oslash; 23.2 mm in upper quadrant | Houses geodesic PIR Fresnel motion dome |
| **HC-SR04 Eye Apertures** | 2&times; &Oslash; 16.2 mm (pitch 26.0 mm) | Dual ultrasonic transceiver cans with crystal slot |

---

## 🖨️ Part Manifest & Bambu Studio Filaments

| Part File Name | Recommended Color / Filament | Dimensions (X &times; Y &times; Z) | Slicing Orientation |
| :--- | :--- | :--- | :--- |
| `01_Base_Pedestal.stl` | Bambu PLA Matte White / Ivory | 55.7 &times; 81.2 &times; 34.0 mm | Flat on solid bottom (Z=0) |
| `02_Neck_and_Head_Pod.stl` | Bambu PLA Matte White / Ivory | 72.0 &times; 39.4 &times; 148.1 mm | Flat on tenon bottom (Z=0) |
| `03_Sensor_Faceplate_Black.stl`| Bambu PLA Matte Carbon Black | 62.6 &times; 61.8 &times; 2.4 mm | Flat on back face (Z=0) |
| `04_Accent_Ring_Orange.stl` | Bambu PLA Basic / Matte Orange | 66.6 &times; 66.6 &times; 2.2 mm | Flat on bed (Z=0) |
| `05_Button_Cap.stl` | Bambu PLA Basic Orange | 6.0 &times; 6.0 &times; 7.5 mm | Flat on head (Z=0) |

---

## ⚙️ Recommended Bambu Studio Slicer Settings

- **Printer Profiles:** Bambu Lab H2S / X1-Carbon / P1S / A1 / A1 Mini
- **Nozzle Diameter:** 0.4 mm (or 0.2 mm for ultra-fine logo relief)
- **Process Profile:** `0.20 mm Standard @BBL H2S` (or `0.16 mm Optimal`)
- **Wall Loops:** `3` (ensures sturdy, solid shells)
- **Top / Bottom Shell Layers:** `4` top, `4` bottom
- **Infill:** `15% Gyroid`
- **Supports:** **NONE (Support-Free Printing)**
- **Plate Type:** Textured PEI Plate ($55^\circ\text{C}$ bed, $220^\circ\text{C}$ nozzle)
- **Bambu Studio Project File:** `StudySense_V6_Pro_BambuStudio.3mf` (All 5 parts pre-arranged on plate)

---

## 🔧 Step-by-Step Hardware Assembly

### Step 1: ESP32 Hot-Glue Installation in Base Pedestal
1. Lay `01_Base_Pedestal` on your workbench. Notice the solid 3mm integrated floor inside.
2. Drop your ESP32 board into the cradle pocket between the corner stops.
3. Slide it back so the Micro-USB / Type-C port aligns with the rear 12.5 &times; 7.0 mm slot.
4. Using your hot glue gun, deposit 3-4 drops of glue into the corners and along the perimeter tabs. The board bonds firmly and permanently to the solid floor.

### Step 2: Rear Push Button
1. Push `05_Button_Cap` into the &Oslash;6.5 mm hole on the rear transition face.
2. Wire the tactile switch to GPIO 22 and GND.

### Step 3: Status LED Push-Fit Installation
1. From inside the neck, insert the three 3mm/5mm wired LEDs into the front neck ports:
   - **Top Hole (Z=76mm):** Green LED (Study Mode)
   - **Middle Hole (Z=62mm):** Blue LED (Break Mode)
   - **Bottom Hole (Z=48mm):** Red LED (Posture Alert)
2. The precision 5.0mm counterbores hold each LED securely without glue.

### Step 4: Wire Routing & Neck Docking
1. Feed the sensor wires up through the generous 16.0 &times; 11.0 mm neck conduit into the head pod.
2. Press the lower tenon of `02_Neck_and_Head_Pod` into the top collar of the base pedestal until it docks flush.

### Step 5: Head Pod Sensor Mating & Faceplate Closure
1. Insert the HC-SR04 ultrasonic sensor and PIR sensor into `03_Sensor_Faceplate_Black`.
2. Snap `04_Accent_Ring_Orange` onto the faceplate rim.
3. Align the perimeter snap tabs and press the complete faceplate assembly into the front of the head pod.

---

## 📁 Deliverables & File Index
- `StudySense_V6_Pro_Parts_and_Assembly_Guide.pdf`: Full 3-page publication PDF with graphics, exploded diagrams, and instructions.
- `StudySense_V6_Pro_BambuStudio.3mf`: Native multi-part project for Bambu Studio.
- `StudySense_V6_Pro_3D_Print_Pack.zip`: Complete distribution archive.
- `v6_pro_stl/`: Directory containing all 5 individual production STLs.
- `render_v6_isometric_hero.png`: Studio hero render.
- `render_v6_exploded_assembly.png`: Exploded assembly diagram.
- `render_v6_front_view.png`: Front elevation.
- `render_v6_rear_view.png`: Rear elevation.
