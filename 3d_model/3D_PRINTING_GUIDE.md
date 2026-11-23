# StudySense™ Smart Study Monitor — 3D Printing & Enclosure Assembly Guide
**Target 3D Printer:** Bambu Lab X1-Carbon / P1S / P1P / A1 / A1 mini (Bambu Studio)  
**Hardware Revision:** Rev 2.0 (Snap-Fit Modular Enclosure with Neck LEDs & Rear Plunger)

---

## 1. Overview & Enclosure Architecture

The **StudySense Enclosure** has been parametrically modeled in 3D to match the sleek, desktop-lamp industrial design of the reference prototype while accommodating the **exact physical components and soldered wiring harness** of your project:

- **01_Base_Lower_Stand.stl**: L-shaped weighted desk base with 13° forward incline, embossed StudySense logo, internal ESP32 cradle, rear USB-C/Micro-USB cutout, and rear push-button port.
- **02_Neck_and_Head_Shell.stl**: Tapered neck column with internal 18×14mm wire conduit, 3x precision Ø5.2mm LED ports (Green, Blue, Red), and an open-cup spherical head angled 7° backward for optimal facial/desk posture tracking.
- **03_Sensor_Faceplate_Black.stl**: Tool-free snap-in faceplate with precision bezels for the HC-SR04 ultrasonic transducers (2× Ø16.5mm) and PIR Fresnel dome (Ø23.6mm).
- **04_Accent_Ring_Orange.stl**: Signature halo accent ring locking between the head shell and faceplate.
- **05_Button_Cap.stl**: Ergonomic plunger with retention flange that snaps onto the rear 6×6mm tactile push button.

```
       [ Head & Sensors: PIR (Top) + HC-SR04 (Bottom) ]
                      \  [ Orange Accent Ring ]
                       \ [ Matte Black Faceplate ]
                        |
                 [ Neck Column ]
                   - Green LED (Optimal)
                   - Blue LED (Standby)
                   - Red LED (Alert)
                        |
               [ Tool-Free Snap Joint ]
                        |
                 [ Base Stand ]
                   - Push Button (Rear)
                   - ESP32 Cradle (Internal)
                   - USB Port Cutout (Bottom Rear)
```

---

## 2. Real Component Dimensions & Tolerances

All cutouts feature calibrated FDM 3D printing tolerances (+0.3mm to +0.5mm clearance) so parts slide in cleanly without filing or post-processing:

| Component | Physical Size | Enclosure Cutout | Fit Type |
|---|---|---|---|
| **ESP32 DevKit (30-pin)** | 51.5 × 28.2 × 12.0 mm | 53.0 × 29.2 × 8.0 mm cradle | Friction fit with bottom guide rails |
| **PIR Sensor (HC-SR501/Mini)** | Dome Ø23.0 mm | Port Ø23.6 mm | Protruding bezel with rear PCB shelf |
| **HC-SR04 Ultrasonic** | Dual Cans Ø16.0 mm, 26.0mm C-C | 2× Port Ø16.5 mm, 26.0mm C-C | Snug flush fit with crystal slot |
| **Neck Indicator LEDs (3x)** | Standard 5mm T-1¾ LEDs | 3× Ø5.2 mm with 7.0mm internal counterbore | Retaining lip prevents push-through |
| **Tactile Push Button** | 6.0 × 6.0 × 5.0 mm | Ø7.0 mm port with internal stop | Actuated via 05_Button_Cap plunger |
| **USB Power Cable** | Standard Type-C / Micro-USB head | 13.0 × 7.5 mm rear cutout | Flush clearance for cable connector |
| **Wire Harness Conduit** | 11 cm harness length | Internal vertical run: ~105 mm | Ample slack, zero tension on solder joints |

---

## 3. Bambu Studio Slicing & Printing Profiles

### Recommended Filaments:
- **Body & Neck (Parts 1 & 2):** Bambu PLA Basic (Jade White) or Matte White PLA / PETG.
- **Faceplate (Part 3):** Bambu PLA Matte (Charcoal / Black) or Carbon Fiber PLA.
- **Accent Ring (Part 4):** Bambu PLA Basic (Mandarin Orange) or PETG Orange.
- **Button Cap (Part 5):** Bambu PLA Basic (Orange or White).

---

### Detailed Plate Setup in Bambu Studio:

#### Plate 1: `01_Base_Lower_Stand.stl`
- **Orientation:** Lay flat on the bottom surface (Z=0).
- **Layer Height:** 0.20 mm Standard.
- **Wall Loops:** 3 (for structural rigidity and screw/snap strength).
- **Top/Bottom Layers:** 4 top, 4 bottom.
- **Infill:** 15% Gyroid (provides balanced weight and prevents desk sliding).
- **Supports:** **Disabled** (all overhangs and internal bridges are within 45°).
- **Brim:** None needed on Textured PEI Plate.

#### Plate 2: `02_Neck_and_Head_Shell.stl`
- **Orientation:** Upright with the bottom neck socket resting flat on the build plate.
- **Layer Height:** 0.16 mm Optimal or 0.20 mm Standard.
- **Wall Loops:** 3.
- **Infill:** 15%–20% Gyroid.
- **Supports:** **Enable Tree Supports (Auto)**.
  - *Support Type:* Tree (Auto)
  - *Threshold Angle:* 30°
  - *Tree Support Branch Angle:* 45°
  - *Note:* Tree supports will lightly cradle the bottom curve of the head cup and easily pop off cleanly.
- **Brim:** Auto / 5mm Mouse-ear brim recommended for bed adhesion during tall print.

#### Plate 3: `03_Sensor_Faceplate_Black.stl`
- **Orientation:** Lay completely flat with the **front face touching the Textured PEI Plate**.
  - *Pro-Tip:* Printing front-face down on a Textured PEI sheet gives the front bezel a gorgeous, high-end matte textured finish identical to commercial electronics!
- **Layer Height:** 0.16 mm High Quality.
- **Wall Loops:** 3.
- **Infill:** 20% Rectilinear.
- **Supports:** **Disabled**.

#### Plate 4: `04_Accent_Ring_Orange.stl`
- **Orientation:** Lay flat on the build plate.
- **Layer Height:** 0.16 mm High Quality.
- **Wall Loops:** 4 (makes the thin ring 100% solid perimeter walls).
- **Infill:** 100%.
- **Supports:** **Disabled**.

#### Plate 5: `05_Button_Cap.stl`
- **Orientation:** Lay flat with the wide retaining flange face down.
- **Layer Height:** 0.12 mm Fine or 0.16 mm.
- **Infill:** 100%.
- **Brim:** 3mm Outer Brim (ensures the small part doesn't detach).

---

## 4. Multi-Color (Bambu AMS) vs Single-Color Printing

- **With Bambu AMS:** You can load all 5 models into a single project or multi-plate project, assign White (Spool 1), Black (Spool 2), and Orange (Spool 3), and click *Print All*. Because each part is an independent STL file, there is **zero purge tower waste**!
- **Without AMS (Single Spool):** Print Plate 1 and Plate 2 in White. Change spool to Black and print Plate 3. Change spool to Orange and print Plate 4 and Plate 5.

---

## 5. Step-by-Step Enclosure Assembly Instructions

### Step 1: Prep & Push-Button Installation
1. Take `01_Base_Lower_Stand`.
2. Insert `05_Button_Cap` from the inside of the base through the rear Ø7.0mm hole so the cap protrudes outward and the flange rests against the interior wall.
3. Position your tactile push button (GPIO 22) against the plunger and secure with a dab of hot glue or adhesive tape into the internal button shelf.

### Step 2: ESP32 Installation
1. Slide the ESP32 DevKit into the base cradle rails.
2. Ensure the USB port points directly through the rear USB cutout.
3. Plug in your USB cable to verify smooth insertion and solid seating.
4. Position the breadboard/perfboard junction strip inside the hollow base chamber.

### Step 3: Neck LED Installation
1. Guide the 3 LED wires up through the bottom of `02_Neck_and_Head_Shell`.
2. Push the **Red LED** into the bottom hole (Z=70mm).
3. Push the **Blue LED** into the middle hole (Z=82mm).
4. Push the **Green LED** into the top hole (Z=94mm).
5. The 5.2mm counterbores hold them firmly; secure with a tiny bead of hot glue behind each LED if desired.

### Step 4: Sensor & Faceplate Assembly
1. Thread the HC-SR04 and PIR sensor cables up the neck and into the open head cup.
2. Insert the two metal cans of the **HC-SR04** into the lower 16.5mm openings of `03_Sensor_Faceplate_Black`.
3. Insert the white Fresnel dome of the **PIR sensor** into the upper 23.6mm opening.
4. Slide `04_Accent_Ring_Orange` over the faceplate perimeter bezel.
5. Press the assembled sensor unit into the front of the head shell until the 4 perimeter snap tabs click securely into place.

### Step 5: Final Join (Base + Neck)
1. Tuck any excess wire slack neatly into the wide central neck cavity (the 11cm harness length provides the exact vertical span needed).
2. Align the male alignment collar of the base with the female socket of the neck.
3. Press firmly until the tool-free snap detents click together.
4. Plug in power and power up your **StudySense**!
