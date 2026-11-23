import os
import base64
import subprocess

print("=== Generating StudySense V7 Final Comprehensive Assembly & Parts PDF Guide ===")

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
HTML_PATH = os.path.join(OUTPUT_DIR, "StudySense_V7_Final_Assembly_Guide.html")
PDF_PATH = os.path.join(OUTPUT_DIR, "StudySense_V7_Final_Parts_and_Assembly_Guide.pdf")

def img_b64(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""

b64_hero = img_b64("render_v7_isometric_hero.png")
b64_exploded = img_b64("render_v7_exploded_assembly.png")
b64_front = img_b64("render_v7_front_view.png")
b64_rear = img_b64("render_v7_rear_view.png")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>StudySense V7 Final Master Assembly Guide</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  @page {{
    size: A4 portrait;
    margin: 0;
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    color: #0f172a;
    background-color: #ffffff;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  .page {{
    width: 210mm;
    height: 297mm;
    padding: 16mm 18mm;
    page-break-after: always;
    position: relative;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}

  .header {{
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}

  .title-area h1 {{
    font-size: 24px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
  }}

  .title-area p {{
    font-size: 11px;
    font-weight: 600;
    color: #ea580c;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
  }}

  .doc-badge {{
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #64748b;
  }}

  .doc-badge strong {{
    color: #0f172a;
    display: block;
    font-size: 11px;
  }}

  .footer {{
    border-top: 1px solid #e2e8f0;
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
    font-size: 9px;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
  }}

  .section-title {{
    font-size: 13px;
    font-weight: 700;
    color: #0f172a;
    border-left: 4px solid #ea580c;
    padding-left: 8px;
    margin: 12px 0 8px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  /* Page 1 Specific */
  .hero-grid {{
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 16px;
    margin-top: 10px;
  }}

  .hero-img-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 195mm;
  }}

  .hero-img-box img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
  }}

  .spec-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 8px;
  }}

  .spec-card h3 {{
    font-size: 11px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 6px;
  }}

  .spec-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5px;
  }}

  .spec-table td {{
    padding: 3px 0;
    border-bottom: 1px solid #edf2f7;
  }}

  .spec-table td:first-child {{
    color: #64748b;
    font-weight: 500;
    width: 48%;
  }}

  .spec-table td:last-child {{
    color: #0f172a;
    font-weight: 700;
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
  }}

  .alert-box {{
    background: #fff7ed;
    border: 1px solid #ffedd5;
    border-left: 3px solid #ea580c;
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 9.5px;
    color: #9a3412;
    line-height: 1.4;
    margin-top: 6px;
  }}

  /* Page 2 Specific */
  .parts-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9px;
    margin-top: 6px;
  }}

  .parts-table th {{
    background: #0f172a;
    color: #ffffff;
    text-align: left;
    padding: 5px 8px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }}

  .parts-table td {{
    padding: 5px 8px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: middle;
  }}

  .parts-table tr:nth-child(even) td {{
    background: #f8fafc;
  }}

  .tag {{
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 8px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
  }}

  .tag-white {{ background: #e2e8f0; color: #334155; }}
  .tag-black {{ background: #1e293b; color: #f8fafc; }}
  .tag-orange {{ background: #ea580c; color: #ffffff; }}

  .exploded-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    height: 125mm;
    margin-top: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  .exploded-box img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
  }}

  /* Page 3 Specific */
  .steps-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 8px;
  }}

  .step-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 9px 11px;
    position: relative;
  }}

  .step-num {{
    background: #ea580c;
    color: #ffffff;
    font-size: 9px;
    font-weight: 800;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 6px;
    font-family: 'JetBrains Mono', monospace;
  }}

  .step-title {{
    font-size: 10.5px;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    margin-bottom: 4px;
  }}

  .step-card p {{
    font-size: 9px;
    color: #475569;
    line-height: 1.4;
  }}

  .step-card code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    background: #e2e8f0;
    padding: 1px 4px;
    border-radius: 3px;
    color: #0f172a;
  }}

  .views-duo {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 8px;
  }}

  .view-img-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    height: 60mm;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  .view-img-box img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
  }}
</style>
</head>
<body>

<!-- PAGE 1: ENGINEERING OVERVIEW & HERO -->
<div class="page">
  <div class="header">
    <div class="title-area">
      <h1>StudySense V7 Final</h1>
      <p>Precision Desktop AI Companion • Calibrated &le;11cm Height</p>
    </div>
    <div class="doc-badge">
      <strong>SPECIFICATION SHEET</strong>
      REV 7.0 • BAMBU LAB H2S / X1 / P1
    </div>
  </div>

  <div class="hero-grid">
    <div class="hero-img-box">
      <img src="{b64_hero}" alt="StudySense V7 Final Hero View">
    </div>

    <div>
      <div class="spec-card">
        <h3>Calibrated Height & Sizing</h3>
        <table class="spec-table">
          <tr><td>Total Assembled Height</td><td>104.3 mm (&le;11.0 cm)</td></tr>
          <tr><td>Wire Travel Distance</td><td>~78.0 mm (3.2cm slack)</td></tr>
          <tr><td>Head Pod Diameter</td><td>58.0 mm (OD)</td></tr>
          <tr><td>Head Pod Depth</td><td>25.0 mm</td></tr>
          <tr><td>Base Pedestal Footprint</td><td>42.2 x 69.1 x 24.0 mm</td></tr>
          <tr><td>Max Individual Part Z</td><td>86.3 mm (Neck Pod)</td></tr>
          <tr><td>Bambu Studio Volume</td><td>256 x 256 x 256 mm</td></tr>
          <tr><td>Bed Adhesion Area</td><td>Zero Floating Regions</td></tr>
        </table>
      </div>

      <div class="spec-card">
        <h3>Sensor & Electronics Ports</h3>
        <table class="spec-table">
          <tr><td>PIR Dome Aperture</td><td>&Oslash;22.5 mm Fresnel</td></tr>
          <tr><td>Ultrasonic Transducers</td><td>2x &Oslash;16.2 mm (Pitch 26mm)</td></tr>
          <tr><td>Oscillator Clearance</td><td>10.0 x 4.2 mm Slot</td></tr>
          <tr><td>Status LED Apertures</td><td>3x &Oslash;3.2 mm (G, B, R)</td></tr>
          <tr><td>Rear Push Button</td><td>&Oslash;6.5 mm Wall Port</td></tr>
          <tr><td>USB Power Cutout</td><td>11.5 x 6.5 mm Rear</td></tr>
          <tr><td>Lower Cover Recess</td><td>34.4 x 58.4 x 1.8 mm</td></tr>
        </table>
      </div>

      <div class="alert-box">
        <strong>&check; Calibrated 11 cm Wire Harness Compatibility:</strong><br>
        The total assembled height has been calibrated to 104.3 mm (10.4 cm). The internal wire conduit requires only ~78 mm of travel, providing <strong>~3.2 cm of slack</strong> for your 11 cm soldered wire harness. Zero tension, zero stretching!
      </div>

      <div class="alert-box" style="margin-top:6px; background:#f0fdf4; border-color:#bbf7d0; border-left-color:#22c55e; color:#166534;">
        <strong>&check; Dedicated Lower Cover Plate:</strong><br>
        The base stand features an open bottom pocket for direct ESP32 hot-glue installation. The snap-in <code>05_Base_Bottom_Cover.stl</code> seals the bottom cleanly with non-slip foot pockets.
      </div>
    </div>
  </div>

  <div class="footer">
    <span>STUDYSENSE AI LAB • 3D HARDWARE DIVISION</span>
    <span>CONFIDENTIAL &amp; PROPRIETARY</span>
    <span>PAGE 1 OF 3</span>
  </div>
</div>

<!-- PAGE 2: EXPLODED VIEW & PARTS ROSTER -->
<div class="page">
  <div class="header">
    <div class="title-area">
      <h1>Parts Roster & Exploded Diagram</h1>
      <p>Modular 6-Component Architecture • Snap-Fit & Hot-Glue Assembly</p>
    </div>
    <div class="doc-badge">
      <strong>BILL OF MATERIALS</strong>
      6 PARTS • 100% MANIFOLD
    </div>
  </div>

  <table class="parts-table">
    <thead>
      <tr>
        <th>PART ID</th>
        <th>NAME & DESCRIPTION</th>
        <th>DIMENSIONS (WxDxH)</th>
        <th>FILAMENT</th>
        <th>FUNCTION</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>01</code></td>
        <td><strong>01_Base_Pedestal.stl</strong></td>
        <td>42.2 x 69.1 x 24.0 mm</td>
        <td><span class="tag tag-white">White PLA</span></td>
        <td>Stand tower, logo ramp, ESP32 pocket, rear USB cutout</td>
      </tr>
      <tr>
        <td><code>02</code></td>
        <td><strong>02_Neck_and_Head_Pod.stl</strong></td>
        <td>58.0 x 31.9 x 86.3 mm</td>
        <td><span class="tag tag-white">White PLA</span></td>
        <td>72mm head pod, neck conduit, 3 LED ports, top aesthetic fin</td>
      </tr>
      <tr>
        <td><code>03</code></td>
        <td><strong>03_Sensor_Faceplate_Black.stl</strong></td>
        <td>50.0 x 50.0 x 2.7 mm</td>
        <td><span class="tag tag-black">Matte Black</span></td>
        <td>Retains HC-SR04 ultrasonic eyes &amp; &Oslash;22.5mm PIR Fresnel dome</td>
      </tr>
      <tr>
        <td><code>04</code></td>
        <td><strong>04_Accent_Ring_Orange.stl</strong></td>
        <td>52.6 x 52.6 x 2.0 mm</td>
        <td><span class="tag tag-orange">Neon Orange</span></td>
        <td>Concentric front halo ring with silky smooth outer chamfer</td>
      </tr>
      <tr>
        <td><code>05</code></td>
        <td><strong>05_Base_Bottom_Cover.stl</strong></td>
        <td>35.5 x 58.0 x 1.8 mm</td>
        <td><span class="tag tag-white">White PLA</span></td>
        <td>The Lower Cover: snaps into bottom to seal the ESP32 cradle</td>
      </tr>
      <tr>
        <td><code>06</code></td>
        <td><strong>06_Button_Cap.stl</strong></td>
        <td>7.8 x 7.8 x 4.5 mm</td>
        <td><span class="tag tag-black">Matte Black</span></td>
        <td>Tactile push plunger cap for rear reset / timer button</td>
      </tr>
    </tbody>
  </table>

  <div class="section-title">Exploded Mechanical Assembly Diagram</div>
  <div class="exploded-box">
    <img src="{b64_exploded}" alt="Exploded Modular Assembly Diagram">
  </div>

  <div class="footer">
    <span>STUDYSENSE AI LAB • 3D HARDWARE DIVISION</span>
    <span>CONFIDENTIAL &amp; PROPRIETARY</span>
    <span>PAGE 2 OF 3</span>
  </div>
</div>

<!-- PAGE 3: STEP-BY-STEP ASSEMBLY & ELEVATIONS -->
<div class="page">
  <div class="header">
    <div class="title-area">
      <h1>Assembly & Calibration Guide</h1>
      <p>Wiring Path, Hot-Glue Installation & Final Verification</p>
    </div>
    <div class="doc-badge">
      <strong>WORKSHOP PROTOCOL</strong>
      STEP 1 THROUGH 6
    </div>
  </div>

  <div class="steps-grid">
    <div class="step-card">
      <div class="step-title"><span class="step-num">1</span> Base &amp; ESP32 Hot-Glue Installation</div>
      <p>Orient <code>01_Base_Pedestal</code> upside down. Insert the ESP32 board into the open bottom cavity. Align the Micro-USB port flush with the rear cutout. Apply 3-4 dabs of hot-melt glue along the corners to anchor firmly to the internal stops.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">2</span> Wire Routing Through Neck Column</div>
      <p>Feed the 11 cm wiring bundle (HC-SR04, PIR dome, LEDs) upward through the hollow <code>14x9mm</code> conduit in <code>02_Neck_and_Head_Pod</code>. The total travel is only ~78 mm, giving <strong>~3.2 cm of comfortable slack</strong>.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">3</span> Neck Docking into Base Socket</div>
      <p>Insert the male spigot at the base of the neck into the mating socket on top of <code>01_Base_Pedestal</code>. Press firmly until seated flush. For permanent bonding, apply a drop of cyanoacrylate (super glue) or hot glue.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">4</span> Snap-Fit Lower Cover Sealing</div>
      <p>Take <code>05_Base_Bottom_Cover</code> and snap it flush into the bottom recess of the base pedestal until the 4 perimeter tabs click into place. Attach rubber adhesive pads into the 4 non-slip corner recesses.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">5</span> Sensor Faceplate Black Installation</div>
      <p>Press the 2 silver ultrasonic eyes through the lower &Oslash;16.2mm ports and seat the white PIR dome into the upper &Oslash;22.5mm port. Press <code>03_Sensor_Faceplate_Black</code> firmly into the head pod front recess.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">6</span> Orange Halo Accent Ring &amp; Button</div>
      <p>Snap the vibrant <code>04_Accent_Ring_Orange</code> around the faceplate groove. Insert <code>06_Button_Cap</code> into the rear &Oslash;6.5mm hole over the tactile switch. Connect USB power and verify LED status!</p>
    </div>
  </div>

  <div class="section-title" style="margin-top:10px;">Front &amp; Rear Orthographic Views</div>
  <div class="views-duo">
    <div class="view-img-box">
      <img src="{b64_front}" alt="Front Elevation View">
    </div>
    <div class="view-img-box">
      <img src="{b64_rear}" alt="Rear Elevation View">
    </div>
  </div>

  <div class="footer">
    <span>STUDYSENSE AI LAB • 3D HARDWARE DIVISION</span>
    <span>CONFIDENTIAL &amp; PROPRIETARY</span>
    <span>PAGE 3 OF 3</span>
  </div>
</div>

</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Saved HTML template -> {HTML_PATH}")

# Render to PDF via Headless Chrome
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cmd = [
    CHROME_PATH,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={PDF_PATH}",
    HTML_PATH
]

print(f"Rendering PDF with Chrome headless -> {PDF_PATH}...")
subprocess.run(cmd, check=True)
pdf_size = os.path.getsize(PDF_PATH)
print(f"Successfully generated {PDF_PATH} ({pdf_size/1024/1024:.2f} MB)")
