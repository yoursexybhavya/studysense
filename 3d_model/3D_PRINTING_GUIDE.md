# StudySense 3D Printing & Hardware Enclosure Guide
**Official Manufacturing Specs for Bambu Studio & Bambu Lab 3D Printers (H2S, X1C, P1S, A1, A1 Mini)**

---

## 🌟 Quick Overview: StudySense V5.0 Compact (&le; 11 cm)
**StudySense V5.0 Compact** is the definitive production enclosure engineered to solve physical desktop and wire harness constraints:
- **Strict Height Constraint (&le; 11 cm):** Overall height is exactly **104.0 mm** (10.4 cm). The physical wire harness measured at 11 cm reaches easily from the ESP32 in the base to the PIR sensor in the head with **28 mm of comfortable slack**.
- **Integrated Solid Floor (Glue-Gun Ready):** `01_Base_Pedestal.stl` features a solid **3.0 mm flat bottom layer** resting directly on the print bed. Zero floating regions, zero slicing warnings in Bambu Studio! The interior floor provides a flat pocket with corner alignment tabs where you can drop the ESP32 and apply hot glue gun adhesive directly.
- **Support-Free 3D Printing:** 100% manifold, support-free printing on all components with local origins resting flat on $Z=0$.
- **Toolless Modular Assembly:** 6 precision interlocking components that snap together with positive detents.

---

## 📐 Mechanical Dimensions (V5.0 Compact)

| Dimension / Metric | Value | Engineering Purpose |
| :--- | :--- | :--- |
| **Total Assembled Height** | **104.0 mm** (10.4 cm) | Strict &le; 11.0 cm constraint; eliminates wire tension |
| **Base Footprint** | 44.6 mm (W) &times; 67.6 mm (D) &times; 22.0 mm (H) | Compact desk footprint with low-profile rear foot |
| **Base Floor Thickness** | **3.0 mm Solid** | 100% solid bottom on bed; hot-glue gun adhesion bed |
| **Internal ESP32 Chamber** | 31.0 mm &times; 48.0 mm &times; 9.0 mm | Sized for standard ESP32 NodeMCU / DevKit boards |
| **Rear USB Cutout** | 12.0 mm &times; 6.5 mm | Direct access for Micro-USB or USB-C power cables |
| **Rear Push Button Port** | &Oslash; 6.5 mm with `06_Button_Cap` | Rear mode/reset switch |
| **Neck Column Height** | 28.0 mm visible (30.0 mm total) | Lofted organic neck with 13 &times; 8.5 mm wire conduit |
| **Status LED Ports** | 3&times; &Oslash; 3.2 mm (&Oslash; 4.8 mm counterbore) | Green (Z=44mm), Blue (Z=36mm), Red (Z=28mm) |
| **Head Pod Outer Diameter**| &Oslash; 54.0 mm circular pod | 7.0&deg; ergonomic upward desk incline |
| **Top Stalk / Fin Height** | Reaches exactly **Z = 104.0 mm** | Iconic handle / antenna aesthetic feature |
| **PIR Sensor Aperture** | &Oslash; 19.0 mm (fits dome lens) | Upper quadrant centered at local Z = +9.2 mm |
| **HC-SR04 Eye Apertures** | 2&times; &Oslash; 14.0 mm (pitch 22.0 mm) | Dual ultrasonic transceiver cans at local Z = -9.0 mm |

---

## 🖨️ Part Manifest & Bambu Studio Filaments

| Part File Name | Recommended Color / Filament | Dimensions (X &times; Y &times; Z) | Slicing Orientation |
| :--- | :--- | :--- | :--- |
| `01_Base_Pedestal.stl` | Bambu PLA Matte White / Ivory | 44.6 &times; 67.6 &times; 22.0 mm | Flat on solid bottom (Z=0) |
| `02_Neck_and_Head_Pod.stl` | Bambu PLA Matte White / Ivory | 54.0 &times; 30.4 &times; 89.2 mm | Flat on tenon bottom |
| `03_Sensor_Faceplate_Black.stl`| Bambu PLA Matte Carbon Black | 47.6 &times; 47.0 &times; 2.0 mm | Flat on back face |
| `04_Accent_Ring_Orange.stl` | Bambu PLA Basic / Matte Orange | 50.6 &times; 50.6 &times; 1.8 mm | Flat on bed |
| `05_Rear_Foot_Lid.stl` | Bambu PLA Matte White | 30.6 &times; 47.6 &times; 3.5 mm | Flat on bed |
| `06_Button_Cap.stl` | Bambu PLA Basic Orange | 6.0 &times; 6.0 &times; 7.3 mm | Flat on head |

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
- **Bambu Studio Project File:** `StudySense_V5_Compact_BambuStudio.3mf` (All 6 parts pre-arranged on plate)

---

## 🔧 Step-by-Step Hardware Assembly

### Step 1: ESP32 Hot-Glue Installation in Base Pedestal
1. Lay `01_Base_Pedestal` on your workbench. Notice the solid 3mm integrated floor inside.
2. Drop your ESP32 board into the cradle pocket.
3. Slide it back so the Micro-USB / Type-C port aligns with the rear 12.0 &times; 6.5 mm slot.
4. Using your hot glue gun, deposit 3-4 drops of glue into the corners and along the perimeter tabs. The board bonds firmly to the solid floor.

### Step 2: Rear Push Button & Service Lid
1. Push `06_Button_Cap` into the &Oslash;6.5 mm hole on the rear transition face.
2. Wire the tactile switch to GPIO 22 and GND.
3. Once wiring is verified, snap `05_Rear_Foot_Lid` into place over the rear foot. All 4 corner snap clips click flush.

### Step 3: Status LED Push-Fit Installation
1. From inside the neck, insert the three 3mm/5mm wired LEDs into the front neck ports:
   - **Top Hole (Z=44mm):** Green LED (Study Mode)
   - **Middle Hole (Z=36mm):** Blue LED (Break Mode)
   - **Bottom Hole (Z=28mm):** Red LED (Posture Alert)
2. The precision 4.8mm counterbores hold each LED securely without glue.

### Step 4: Wire Routing & Neck Docking
1. Feed the sensor wires up through the 13 &times; 8.5 mm neck conduit into the head pod.
2. The total wire path is only 82 mm, giving you **28 mm of comfortable wire slack** from your 11 cm harness!
3. Press the lower tenon of `02_Neck_and_Head_Pod` into the top collar of the base pedestal until it docks flush.

### Step 5: Head Pod Sensor Mating & Faceplate Closure
1. Insert the HC-SR04 ultrasonic sensor and PIR sensor into `03_Sensor_Faceplate_Black`.
2. Snap `04_Accent_Ring_Orange` onto the faceplate rim.
3. Align the perimeter snap tabs and press the complete faceplate assembly into the front of the head pod.

---

## 📁 Deliverables & File Index
- `StudySense_V5_Compact_Parts_and_Assembly_Guide.pdf`: Full 3-page publication PDF with graphics, exploded diagrams, and instructions.
- `StudySense_V5_Compact_BambuStudio.3mf`: Native multi-part project for Bambu Studio.
- `StudySense_V5_Compact_3D_Print_Pack.zip`: Complete distribution archive.
- `v5_compact_stl/`: Directory containing all 6 individual production STLs.
- `render_v5_isometric_hero.png`: Studio hero render.
- `render_v5_exploded_assembly.png`: Exploded assembly diagram.
- `render_v5_front_view.png`: Front elevation.
- `render_v5_rear_view.png`: Rear elevation.
