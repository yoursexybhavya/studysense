# StudySense 3D Enclosure — Bambu Studio Printing & Assembly Guide

This guide provides step-by-step instructions for importing, slicing, 3D printing, and assembling the **StudySense Smart Study Monitor** desktop enclosure using **Bambu Studio** and any Bambu Lab printer (A1, P1S, X1C, or H2S) with a Textured PEI Plate.

---

## 1. Quick Start: One-Click Bambu Studio Import

The package includes a native Bambu Studio project file:
📁 **`StudySense_BambuStudio_Project.3mf`**

1. Open **Bambu Studio**.
2. Go to **File → Open Project** (or press `Cmd + O` / `Ctrl + O`).
3. Select `StudySense_BambuStudio_Project.3mf`.
4. All 5 parts will load directly onto your virtual 256×256 mm build plate with correct orientations and scale.

---

## 2. Multi-Plate Print Matrix (Filament Color Separation)

If your printer does not have an AMS (Automatic Material System), you can easily print each part on a separate plate using standard single-color filament rolls:

| Part File | Color / Material | Recommended Layer Height | Infill | Supports | Est. Print Time (0.4mm nozzle) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`01_Base_Lower_Stand.stl`** | White PLA Matte | 0.20 mm | 15% Gyroid | None (flat on bottom) | ~1 hr 45 min |
| **`02_Neck_and_Head_Shell.stl`**| White PLA Matte | 0.16 mm Optimal | 15% Gyroid | Auto Tree Supports (touching buildplate only) | ~2 hrs 10 min |
| **`03_Sensor_Faceplate_Black.stl`**| Matte Carbon Black PLA | 0.16 mm | 100% Solid | None (face-down on PEI plate) | ~28 min |
| **`04_Accent_Ring_Orange.stl`**| Vibrant Orange/Red PLA | 0.16 mm | 100% Solid | None (flat on plate) | ~14 min |
| **`05_Button_Cap.stl`** | Matte Black PLA | 0.12 mm High Res | 100% Solid | None (flange down) | ~8 min |

---

## 3. Bambu Studio Slicer Settings

### Global Quality & Strength Settings
* **Layer Height:** `0.16 mm` (Recommended) or `0.20 mm Standard`.
* **First Layer Height:** `0.20 mm` for superior adhesion on the Textured PEI plate.
* **Wall Loops:** `3` (1.2 mm solid perimeter thickness for structural rigidity).
* **Top Shell Layers:** `4`
* **Bottom Shell Layers:** `4`
* **Infill Density:** `15%`
* **Infill Pattern:** `Gyroid` (provides uniform multidirectional stiffness and dampens buzzer resonance).
* **Seam Position:** `Aligned` or `Back` (keeps the front exterior surface 100% clean).

### Bed Adhesion & Temperatures
* **Bed Plate:** Bambu Textured PEI Plate.
* **Bed Temperature:** `60°C` (standard PLA) / `65°C` (first layer).
* **Nozzle Temperature:** `215°C` - `220°C` (standard PLA).
* **Brim:** `Outer brim only, 5mm` recommended for the vertical neck to prevent corner lifting.

---

## 4. Hardware Assembly & Wire Routing Instructions

Follow these steps to transfer your wired electronics into the printed enclosure:

### Step 1: Install the Base & ESP32
1. Slide the **ESP32 DevKit** board into the internal cradle of **`01_Base_Lower_Stand`**.
2. Align the ESP32's USB port with the rear rectangular slot (`13.5 × 8.0 mm`) so a charging cable can plug in flush from the desk.
3. Insert the 6×6 mm tactile push button into the rear button hole and snap **`05_Button_Cap`** over it.

### Step 2: Route Wires Through the Neck
1. Guide the **11 cm PIR motion sensor harness**, the HC-SR04 jumper wires, and the buzzer leads up through the central hollow conduit (`18 × 14 mm`) of **`02_Neck_and_Head_Shell`**.
2. Push the 3 status LEDs from the inside through the front neck holes:
   * **Top Hole:** Green LED (Study Active / Optimal Focus)
   * **Middle Hole:** Blue LED (Standby / Break Time)
   * **Bottom Hole:** Red LED (Posture Warning / Absence Alarm)
   *(The 6.4 mm internal counterbore stops the LED flange flush against the front surface).*

### Step 3: Mount the Sensors in the Head Pod
1. Place the **HC-SR04 Ultrasonic Sensor** into the lower half of the head pod. The two silver transducers will align with the dual lower cutouts.
2. Place the **PIR Motion Sensor** in the upper half of the head pod. The white round Fresnel dome aligns with the upper circular cutout.
3. Tuck the active buzzer into the acoustic pocket in the lower neck.

### Step 4: Snap On the Faceplate & Halo
1. Press the **`04_Accent_Ring_Orange`** into the circular front bezel of the head.
2. Press the **`03_Sensor_Faceplate_Black`** inside the accent ring. The internal alignment tabs ensure it sits flush with zero rotational play.
3. Mate the **`02_Neck_and_Head_Shell`** onto the **`01_Base_Lower_Stand`** by pressing the neck's female socket over the base's male alignment collar until the snap detents click firmly into place.

---

## 5. File Inventory & Specifications

| File Name | File Type | Size | Description |
| :--- | :--- | :--- | :--- |
| `StudySense_BambuStudio_Project.3mf` | Bambu 3MF Project | ~113 KB | Direct 1-click project with all parts arranged on plate |
| `01_Base_Lower_Stand.stl` | Binary STL | ~60 KB | Lower desk base with ESP32 bed, USB slot, & StudySense logo |
| `02_Neck_and_Head_Shell.stl` | Binary STL | ~158 KB | Tapered column & head pod with 3x LED ports & wire duct |
| `03_Sensor_Faceplate_Black.stl`| Binary STL | ~65 KB | Front circular plate with cutouts for PIR & HC-SR04 |
| `04_Accent_Ring_Orange.stl` | Binary STL | ~38 KB | Concentric contrast bezel ring |
| `05_Button_Cap.stl` | Binary STL | ~13 KB | Rear tactile switch plunger cap |
| `StudySense_Complete_Assembly.stl`| Binary STL | ~333 KB | Full monolithic 3D preview assembly |
| `StudySense_Complete_Assembly.obj`| Wavefront OBJ | ~408 KB | CAD 3D model with material mapping (.mtl) |
| `StudySense_Enclosure.blend` | Blender 5.2 File | ~200 KB | Parametric CAD source file with studio lighting & cameras |
