# StudySense — Project Photos & Visual Asset Archive

This directory contains the complete visual archive of the **StudySense (Smart Study Monitor)** project, including reference designs, physical hardware wiring photographs, sensor component closeups, and Bambu Studio slicer iteration logs.

---

## 📁 Directory Structure

```
project_photos/
├── README.md                           # This visual catalog and hardware index
├── curated/                            # High-resolution, categorized photos with clear filenames
│   ├── 01_hardware_and_wiring/         # ESP32 breadboard, wiring, 11cm scale, HC-SR04 & PIR
│   ├── 02_design_references/           # Aesthetic design reference photos & CAD concepts
│   └── 03_slicer_and_cad_feedback/     # Bambu Studio slicer screenshots & iteration feedback
└── raw_uploads/                        # Complete 30-file archive of all raw user-uploaded photos
```

---

## 📸 Curated Photo Gallery

### 1. Design References & Industrial Aesthetics

| Photo | Filename | Description |
| :--- | :--- | :--- |
| <img src="curated/02_design_references/01_studysense_hero_reference_photo.jpg" width="220" alt="Hero Reference" /> | `01_studysense_hero_reference_photo.jpg` | **Primary Hero Reference:** Desktop monitor featuring spherical head, recessed black sensor faceplate, bright orange accent ring, vertical ergonomic neck, and angled pedestal. |
| <img src="curated/02_design_references/02_studysense_hero_reference_highres.png" width="220" alt="Hero High-Res" /> | `02_studysense_hero_reference_highres.png` | **High-Definition Front Profile:** Clean view of sensor alignment (top PIR dome, dual HC-SR04 ultrasonic transducers, status LEDs, and front logo). |
| <img src="curated/02_design_references/03_studysense_reference_variation.jpg" width="220" alt="Reference Variation" /> | `03_studysense_reference_variation.jpg` | **Desk Environment View:** Demonstrating posture detection angle and desktop footprint. |
| <img src="curated/02_design_references/04_cad_concept_front_elevation.png" width="220" alt="CAD Front" /> | `04_cad_concept_front_elevation.png` | **Front Elevation CAD Concept:** Dimensional layout of sensor faceplate aperture and neck transitions. |
| <img src="curated/02_design_references/05_cad_concept_isometric_angle.png" width="220" alt="CAD Isometric" /> | `05_cad_concept_isometric_angle.png` | **Isometric CAD Concept:** 3D perspective showing rear shell depth and front chamfers. |

---

### 2. Hardware Assembly, Sensors & Circuit Wiring

| Photo | Filename | Description |
| :--- | :--- | :--- |
| <img src="curated/01_hardware_and_wiring/07_hardware_wire_harness_11cm_scale.jpg" width="220" alt="11cm Scale" /> | `07_hardware_wire_harness_11cm_scale.jpg` | **Critical 11 cm Wire Harness Constraint:** Physical measurement showing sensor harness length $\le 11\text{ cm}$. Enclosure height was strictly engineered to $104.38\text{ mm}$ to ensure wire slack. |
| <img src="curated/01_hardware_and_wiring/09_hc_sr04_ultrasonic_sensor_closeup.jpg" width="220" alt="HC-SR04 Closeup" /> | `09_hc_sr04_ultrasonic_sensor_closeup.jpg` | **HC-SR04 Ultrasonic Sensor Closeup:** Handheld inspection verifying dimensions ($45.2 \times 20.4\text{ mm}$, dual $16\text{ mm}$ transducers, $26\text{ mm}$ pitch, 4-pin header with voltage divider). |
| <img src="curated/01_hardware_and_wiring/10_pir_hc_sr501_motion_sensor_closeup.jpg" width="220" alt="PIR HC-SR501 Closeup" /> | `10_pir_hc_sr501_motion_sensor_closeup.jpg` | **HC-SR501 PIR Motion Sensor Closeup:** Handheld inspection verifying $23\text{ mm}$ diameter Fresnel dome lens and $32.2 \times 24.3\text{ mm}$ PCB footprint. |
| <img src="curated/01_hardware_and_wiring/05_hardware_assembly_top_view.jpg" width="220" alt="Assembly Top" /> | `05_hardware_assembly_top_view.jpg` | **Hardware Assembly Top View:** Assembled breadboard circuit with ESP32 DevKit, status LEDs, buzzer driver, and sensor jumper cables. |
| <img src="curated/01_hardware_and_wiring/06_hardware_assembly_desk_view.jpg" width="220" alt="Assembly Desk" /> | `06_hardware_assembly_desk_view.jpg` | **Desk Testing Setup:** Live circuit connected to USB-C power hub during firmware testing. |
| <img src="curated/01_hardware_and_wiring/08_hardware_desk_scale_angle.jpg" width="220" alt="Desk Scale" /> | `08_hardware_desk_scale_angle.jpg` | **Bench Scale Angle:** Wire harness layout and component orientation on desk. |
| <img src="curated/01_hardware_and_wiring/01_circuit_schematic_early.jpg" width="220" alt="Early Schematic" /> | `01_circuit_schematic_early.jpg` | **Early Project Circuit Schematic:** Initial wiring diagram establishing GPIO pins for ESP32. |
| <img src="curated/01_hardware_and_wiring/02_circuit_breadboard_wiring.jpg" width="220" alt="Breadboard Wiring" /> | `02_circuit_breadboard_wiring.jpg` | **Breadboard Component Layout:** Placement of resistors, NPN transistor, and status LEDs. |
| <img src="curated/01_hardware_and_wiring/03_circuit_pinout_details.jpg" width="220" alt="Pinout Details" /> | `03_circuit_pinout_details.jpg` | **ESP32 DevKit Pinout Reference:** Close view of power rails (VIN 5V, 3.3V, GND) and signal pins. |
| <img src="curated/01_hardware_and_wiring/04_circuit_wiring_closeup.jpg" width="220" alt="Wiring Closeup" /> | `04_circuit_wiring_closeup.jpg` | **Circuit Wiring Closeup:** Detail of ECHO voltage divider ($1\text{k}\Omega / 2\text{k}\Omega$) for 3.3V GPIO protection. |

---

### 3. Bambu Studio Slicer Feedback & Iteration Journey

| Photo | Filename | Description |
| :--- | :--- | :--- |
| <img src="curated/03_slicer_and_cad_feedback/01_v4_base_opening_red_arrow.png" width="220" alt="V4 Base Feedback" /> | `01_v4_base_opening_red_arrow.png` | **V4 Base Opening Request (Red Arrow):** User feedback requesting a solid base with glue-gun mounting for ESP32 and a bottom access cover. |
| <img src="curated/03_slicer_and_cad_feedback/02_v4_floating_regions_warning.png" width="220" alt="Floating Regions" /> | `02_v4_floating_regions_warning.png` | **Bambu Studio Floating Overhang Warning:** Slicer warning detected on early V4 overhangs, resolved in V6/V7 with $45^\circ$ self-supporting chamfers. |
| <img src="curated/03_slicer_and_cad_feedback/03_v6_height_limit_boundary_error.png" width="220" alt="Height Limit Error" /> | `03_v6_height_limit_boundary_error.png` | **V6 Height Boundary Error:** Slicer alert indicating head pod exceeded build volume height limit ($>100\text{ mm}$), leading to the V7/V8 compact redesign ($85.2\text{ mm}$ single-part max, $104.38\text{ mm}$ assembled). |
| <img src="curated/03_slicer_and_cad_feedback/04_v7_rear_foot_feedback_red_circle.png" width="220" alt="V7 Foot Feedback" /> | `04_v7_rear_foot_feedback_red_circle.png` | **V7 Rear Foot Feedback (Red Circle):** User marked the extended rear stage as too bulky, prompting the sleek single-stage base with integrated rear-wall USB port in V8 Master. |
| <img src="curated/03_slicer_and_cad_feedback/05_v7_side_view_bambu_studio.png" width="220" alt="V7 Side View" /> | `05_v7_side_view_bambu_studio.png` | **V7 Side Profile on Build Plate:** Inspection of neck slant angle ($5^\circ$ backward tilt) and bed footprint. |
| <img src="curated/03_slicer_and_cad_feedback/06_v8_no_geometry_data_dialog.jpg" width="220" alt="No Geometry Data" /> | `06_v8_no_geometry_data_dialog.jpg` | **Bambu Studio XML Namespace Parsing Alert:** Diagnosed to Python `xml.etree` prefixing `<ns0:model>` in 3MF export. |
| <img src="curated/03_slicer_and_cad_feedback/07_v8_invalid_config_dialog.jpg" width="220" alt="Invalid Config Dialog" /> | `07_v8_invalid_config_dialog.jpg` | **Bambu Studio 3MF Config Prompt:** Fixed by compiling directly with native Bambu Studio CLI exporter for 100% clean loading. |

---

## 🗄️ Complete Raw Uploads Inventory (All 30 Files)

Every original file uploaded during the project sessions is preserved in `raw_uploads/`:

| # | Raw Filename | File Size | MD5 Checksum | Curated Mapping |
| :---: | :--- | :---: | :--- | :--- |
| 1 | `media_1794979617051_56f6f51e.jpg` | 143.7 KB | `cfac4d07916d005ac8ce2aad78a8eca1` | `01_hardware_and_wiring/01_circuit_schematic_early.jpg` |
| 2 | `media_1795057485077_29fffa73.jpg` | 247.5 KB | `91d4fd2e67201081aca205789f9082f3` | `01_hardware_and_wiring/02_circuit_breadboard_wiring.jpg` |
| 3 | `media_1795057519583_75e422b6.jpg` | 102.2 KB | `9d65817f23e8e190922095c310f6916a` | `01_hardware_and_wiring/03_circuit_pinout_details.jpg` |
| 4 | `media_1795058212778_c3804ee5.jpg` | 137.1 KB | `112382132949f04fab8939ece01e8162` | `01_hardware_and_wiring/04_circuit_wiring_closeup.jpg` |
| 5 | `media_1795434690351_b3108945.jpg` | 111.1 KB | `b3a23292be7b57a31068a4910c77640b` | `02_design_references/01_studysense_hero_reference_photo.jpg` |
| 6 | `media_1795434858851_d9878d38.jpg` | 334.1 KB | `3ce9ba2b231bd964718380a2e4da0855` | `01_hardware_and_wiring/05_hardware_assembly_top_view.jpg` |
| 7 | `media_1795435192640_3220df9c.jpg` | 152.9 KB | `0f1d604ac58373316f660837516bfe46` | `01_hardware_and_wiring/06_hardware_assembly_desk_view.jpg` |
| 8 | `media_1795437424044_2516538a.jpg` | 111.1 KB | `b3a23292be7b57a31068a4910c77640b` | *(Duplicate of #5)* |
| 9 | `media_1795437424049_c48aa33e.jpg` | 334.1 KB | `3ce9ba2b231bd964718380a2e4da0855` | *(Duplicate of #6)* |
| 10 | `media_1795437424051_8290d9b2.jpg` | 152.9 KB | `0f1d604ac58373316f660837516bfe46` | *(Duplicate of #7)* |
| 11 | `media_1795437571673_14c6c0d7.png` | 381.1 KB | `2ec76e413a44085646ad4d4c132a2aef` | `02_design_references/04_cad_concept_front_elevation.png` |
| 12 | `media_1795438263692_4f59aa84.jpg` | 111.1 KB | `b3a23292be7b57a31068a4910c77640b` | *(Duplicate of #5)* |
| 13 | `media_1795438263701_1a84857a.jpg` | 152.9 KB | `0f1d604ac58373316f660837516bfe46` | *(Duplicate of #7)* |
| 14 | `media_1795438263701_4d6cb1f9.jpg` | 334.1 KB | `3ce9ba2b231bd964718380a2e4da0855` | *(Duplicate of #6)* |
| 15 | `media_1795438263715_cb00231f.png` | 381.1 KB | `2ec76e413a44085646ad4d4c132a2aef` | *(Duplicate of #11)* |
| 16 | `media_1795442255498_dc9a2c34.png` | 307.9 KB | `a5e10f2127f96b6eed442dc3f3be8bac` | `02_design_references/02_studysense_hero_reference_highres.png` |
| 17 | `media_1795442261038_ccc3b4c1.png` | 374.6 KB | `0521ba08a94b50466bbd1ac93205b6fb` | `02_design_references/05_cad_concept_isometric_angle.png` |
| 18 | `media_1795442319940_ec56b73f.jpg` | 111.1 KB | `5292c61353be4f01158a066a3c491d64` | `02_design_references/03_studysense_reference_variation.jpg` |
| 19 | `media_1795442322903_a7e191bc.jpg` | 333.8 KB | `3e881d6789e0d0bc7b3cb33d673c2c6d` | `01_hardware_and_wiring/07_hardware_wire_harness_11cm_scale.jpg` |
| 20 | `media_1795442325119_9569fb15.jpg` | 152.8 KB | `c1085b9b6f952689da4273db2457f3fe` | `01_hardware_and_wiring/08_hardware_desk_scale_angle.jpg` |
| 21 | `media_1795444932100_524fe4e0.png` | 509.5 KB | `93ac28fe7a2a989be79b7154d99336cb` | `03_slicer_and_cad_feedback/01_v4_base_opening_red_arrow.png` |
| 22 | `media_1795445094937_4c865e61.png` | 397.1 KB | `0fe263ab0ebac5b4767c3e9f85e1b12e` | `03_slicer_and_cad_feedback/02_v4_floating_regions_warning.png` |
| 23 | `media_1795448444664_ad1f162d.png` | 390.4 KB | `a2fc5f340863c5ba79ba42769b612c59` | `03_slicer_and_cad_feedback/03_v6_height_limit_boundary_error.png` |
| 24 | `media_1795450076445_66543f0b.png` | 387.2 KB | `a926f313ee151d36e4a022d654fa7776` | `03_slicer_and_cad_feedback/04_v7_rear_foot_feedback_red_circle.png` |
| 25 | `media_1795450356521_ed8cbb7e.png` | 294.1 KB | `491b1181112c2a1231493f38bcbc3b70` | `03_slicer_and_cad_feedback/05_v7_side_view_bambu_studio.png` |
| 26 | `media_1795450502907_e4e9f203.jpg` | 168.8 KB | `ef4f7f9d8313dff9bd3e1264618607b2` | `01_hardware_and_wiring/09_hc_sr04_ultrasonic_sensor_closeup.jpg` |
| 27 | `media_1795450512081_89560869.jpg` | 160.6 KB | `ecf17b38f13317bcfab23569de5cc5bc` | `01_hardware_and_wiring/10_pir_hc_sr501_motion_sensor_closeup.jpg` |
| 28 | `media_1795450518208_42967557.jpg` | 111.1 KB | `b3a23292be7b57a31068a4910c77640b` | *(Duplicate of #5)* |
| 29 | `media_1795451201001_c8749034.jpg` | 77.5 KB | `e5c697ecc075a203f0a5acbac7ecb048` | `03_slicer_and_cad_feedback/06_v8_no_geometry_data_dialog.jpg` |
| 30 | `media_1795451250067_9508d736.jpg` | 80.2 KB | `46d73f10af5815276191cf362dbdd102` | `03_slicer_and_cad_feedback/07_v8_invalid_config_dialog.jpg` |

---

*All photos preserved for open-source reproducibility of the StudySense hardware and 3D enclosure.*
