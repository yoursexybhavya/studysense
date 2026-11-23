# StudySense V4.0 Organic 3D Printing & Assembly Guide
**Engineered for Bambu Studio & Bambu Lab 3D Printers (H2S, X1-Carbon, P1S, A1, A1 Mini)**

---

## 🌟 Overview & Aesthetic Design
StudySense V4.0 Organic is a sleek, injection-molded style desk enclosure designed with organic fillets, soft pill/capsule contours, and zero sharp boxy facets. It perfectly houses all StudySense IoT components with zero wire strain and tool-less snap-fit assembly.

### 📐 Mechanical Specifications
- **Overall Dimensions:** 72.0 mm (W) × 88.7 mm (D) × 172.1 mm (H)
- **Base Footprint:** 56.0 mm × 88.7 mm with low-profile rear stabilizer foot (14 mm H)
- **Head Pod Diameter:** 72.0 mm circular pod with 7.0° ergonomic desk incline
- **Internal Wire Conduit:** 16.0 mm × 11.0 mm hollow channel through neck (comfortably fits the 11 cm wire harness)
- **Build Plate Clearance:** Fits 100% within standard 256×256 mm Bambu build plates with verified 0 error CLI slicing.

---

## 🖨️ Part Manifest & Filament Color Recommendations

| Part File | Part Name | Recommended Filament | Dimensions (X × Y × Z) | Est. Print Time |
| :--- | :--- | :--- | :--- | :--- |
| `01_Base_Pedestal.stl` | Base Stand & Pedestal | Bambu PLA Matte White / Ivory Silk | 56.0 × 88.7 × 36.0 mm | ~1h 15m |
| `02_Neck_and_Head_Pod.stl` | Neck Stem & Head Pod | Bambu PLA Matte White / Ivory Silk | 72.0 × 39.4 × 172.1 mm | ~2h 45m |
| `03_Sensor_Faceplate_Black.stl` | Sensor Faceplate | Bambu PLA Matte Charcoal / Carbon Black | 62.6 × 9.9 × 61.6 mm | ~25m |
| `04_Accent_Ring_Orange.stl` | Accent Halo Ring | Bambu PLA Basic / Matte Orange | 66.6 × 10.2 × 66.3 mm | ~18m |
| `05_Base_Bottom_Plate.stl` | Base Service Cover | Bambu PLA Matte White | 37.4 × 63.4 × 2.6 mm | ~20m |
| `06_Button_Cap.stl` | Rear Tactile Button Cap | Bambu PLA Orange | 7.0 × 5.5 × 7.0 mm | ~6m |

---

## ⚙️ Recommended Bambu Studio Print Settings
- **Printer Profiles:** Bambu Lab H2S / X1-Carbon / P1S / A1 / A1 Mini
- **Nozzle Diameter:** 0.4 mm (or 0.2 mm for ultra-fine logo detail)
- **Layer Height:** `0.16 mm Optimal` or `0.20 mm Standard`
- **First Layer Height:** `0.20 mm`
- **Wall Loops:** `3` (for solid, durable outer shells)
- **Top / Bottom Shells:** `4` top layers, `4` bottom layers
- **Sparse Infill:** `15% Gyroid` (provides uniform multi-directional strength)
- **Supports:**
  - `01_Base_Pedestal`: Support **None** (prints flat on base bottom).
  - `02_Neck_and_Head_Pod`: **Tree Support (Auto)** with 25° threshold angle under neck overhang.
  - `03_Sensor_Faceplate`: Support **None** (prints flat on bed).
  - `04_Accent_Ring`: Support **None** (prints flat on bed).
  - `05_Base_Bottom_Plate`: Support **None** (prints flat on bed).
- **Bed Adhesion:** Smooth or Textured PEI Plate with 5 mm outer brim on `02_Neck_and_Head_Pod`.

---

## 🔧 Step-by-Step Hardware Assembly

### Step 1: Base & ESP32 Installation
1. Flip `01_Base_Pedestal` upside down.
2. Slide your ESP32 DevKit into the internal cradle rails.
3. Ensure the Micro-USB / USB-C port aligns perfectly with the rear 12.5 mm × 7.0 mm slot.
4. Mount the rear tactile push button (GPIO 22) into the Ø6.5 mm rear hole and snap `06_Button_Cap` on from the outside.

### Step 2: Wire Routing Through Neck
1. Route the 11 cm sensor wire harness up through the base socket opening and into the 16 mm × 11 mm neck conduit.
2. Dock `02_Neck_and_Head_Pod` into the top collar of `01_Base_Pedestal`. The snap detents will click firmly into place.
3. Press the three 5 mm or 3 mm status LEDs (Green, Blue, Red) into their respective mounting ports on the front face of the neck.

### Step 3: Sensor Head Pod Assembly
1. Connect the 4-pin jumper wires to the HC-SR04 ultrasonic sensor and 3-pin wires to the PIR motion sensor.
2. Rest the HC-SR04 PCB on the lower internal shelf and the PIR sensor on the upper internal shelf.
3. Press `03_Sensor_Faceplate_Black` over the sensors:
   - The white geodesic PIR dome protrudes through the upper Ø23.2 mm aperture.
   - The two aluminum transducer eyes push through the dual Ø16.2 mm apertures.
   - The crystal oscillator sits centered in the middle window.
4. Snap `04_Accent_Ring_Orange` into the outer perimeter recess. It seats flush between the white outer head bezel and the black faceplate.

### Step 4: Base Closure & Rubber Feet
1. Tuck any excess wire slack into the base cavity.
2. Snap `05_Base_Bottom_Plate` into the bottom of the base.
3. (Optional) Apply 4 self-adhesive rubber non-slip bumper pads into the 4 pre-molded Ø8.0 mm pockets on the bottom plate for desk grip.

---

## 📁 File Package Structure
- `StudySense_V4_Organic_BambuStudio.3mf`: Native multi-part project pre-arranged for Bambu Studio.
- `v4_organic_stl/`: Individual normalized STL files for custom slicers.
- `StudySense_V4_Complete_Assembly.stl`: Combined full 3D assembly.
- `StudySense_V4_Complete_Assembly.obj`: 3D textured mesh with materials.
- `render_v4_isometric_hero.png`: Photorealistic studio hero render.
- `render_v4_front_view.png`: Orthographic front view showing sensor alignment.
- `render_v4_exploded_assembly.png`: Exploded assembly showing internal modular structure.
