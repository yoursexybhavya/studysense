import os
import base64
import subprocess

print("=== Generating StudySense V8 Master Comprehensive Assembly & Parts PDF Guide ===")

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
HTML_PATH = os.path.join(OUTPUT_DIR, "StudySense_V8_Master_Assembly_Guide.html")
PDF_PATH = os.path.join(OUTPUT_DIR, "StudySense_V8_Master_Parts_and_Assembly_Guide.pdf")

def img_b64(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""

b64_hero = img_b64("render_v8_isometric_hero.png")
b64_exploded = img_b64("render_v8_exploded_assembly.png")
b64_front = img_b64("render_v8_front_view.png")
b64_rear = img_b64("render_v8_rear_view.png")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>StudySense V8 Master Assembly Guide</title>
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
      <h1>StudySense V8 Master</h1>
      <p>Streamlined Single-Stage Pedestal • Calibrated &le;11cm Height</p>
    </div>
    <div class="doc-badge">
      <strong>PRODUCTION SPECIFICATION</strong>
      REV 8.0 • BAMBU LAB H2S / X1 / P1 / A1
    </div>
  </div>

  <div class="hero-grid">
    <div class="hero-img-box">
      <img src="{b64_hero}" alt="StudySense V8 Master Hero View">
    </div>

    <div>
      <div class="spec-card">
        <h3>Calibrated Height & Proportions</h3>
        <table class="spec-table">
          <tr><td>Total Assembled Height</td><td>104.4 mm (&le;11.0 cm)</td></tr>
          <tr><td>Wire Travel Distance</td><td>~75.0 mm (3.5cm slack)</td></tr>
          <tr><td>Head Pod Diameter</td><td>58.0 mm (OD)</td></tr>
          <tr><td>Head Pod Depth</td><td>25.0 mm</td></tr>
          <tr><td>Base Pedestal Stage</td><td>38.5 x 37.5 x 25.0 mm</td></tr>
          <tr><td>Max Individual Part Z</td><td>85.2 mm (Neck Pod)</td></tr>
          <tr><td>USB Port Location</td><td>Main Tower Rear Wall</td></tr>
          <tr><td>Rear Push Button</td><td>Main Tower Rear Wall</td></tr>
        </table>
      </div>

      <div class="spec-card">
        <h3>Physical Sensor Matching</h3>
        <table class="spec-table">
          <tr><td>PIR Dome Aperture</td><td>&Oslash;23.2 mm (HC-SR501)</td></tr>
          <tr><td>Ultrasonic Transducers</td><td>2x &Oslash;16.3 mm (HC-SR04)</td></tr>
          <tr><td>Transducer Eye Pitch</td><td>26.0 mm (Center-to-Center)</td></tr>
          <tr><td>Crystal Oscillator Slot</td><td>11.8 x 4.8 mm Clearance</td></tr>
          <tr><td>Flared Neck Conduit</td><td>20.0 x 14.0 mm Throat</td></tr>
          <tr><td>Status LED Apertures</td><td>3x &Oslash;3.2 mm (G, B, R)</td></tr>
          <tr><td>Lower Cover Snap Lip</td><td>34.4 x 38.4 x 1.8 mm</td></tr>
        </table>
      </div>

      <div class="alert-box">
        <strong>&check; Streamlined Single-Stage Pedestal:</strong><br>
        The bulky rear box has been completely removed. The base is now a compact, elegant monolithic pedestal matching the reference photo. The USB port and tactile push button mount directly on the rear wall of the main tower!
      </div>

      <div class="alert-box" style="margin-top:6px; background:#f0fdf4; border-color:#bbf7d0; border-left-color:#22c55e; color:#166534;">
        <strong>&check; Multi-Filament Colors in Bambu Studio:</strong><br>
        Configured with 3 filaments (White, Neon Orange, Matte Black). In Bambu Studio, each part now displays in its true real-world color instead of generic solid green!
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
        <td>38.5 x 37.5 x 25.0 mm</td>
        <td><span class="tag tag-white">White PLA</span></td>
        <td>Streamlined stand tower, logo ramp, rear USB cutout, top socket</td>
      </tr>
      <tr>
        <td><code>02</code></td>
        <td><strong>02_Neck_and_Head_Pod.stl</strong></td>
        <td>58.0 x 32.4 x 85.2 mm</td>
        <td><span class="tag tag-white">White PLA</span></td>
        <td>58mm head pod, slanted neck, flared conduit, 3 LED ports, top fin</td>
      </tr>
      <tr>
        <td><code>03</code></td>
        <td><strong>03_Sensor_Faceplate_Black.stl</strong></td>
        <td>50.4 x 50.4 x 2.6 mm</td>
        <td><span class="tag tag-black">Matte Black</span></td>
        <td>Holds HC-SR04 ultrasonic eyes &amp; &Oslash;23.2mm PIR dome</td>
      </tr>
      <tr>
        <td><code>04</code></td>
        <td><strong>04_Accent_Ring_Orange.stl</strong></td>
        <td>53.2 x 53.2 x 2.0 mm</td>
        <td><span class="tag tag-orange">Neon Orange</span></td>
        <td>Front halo ring with silky smooth chamfer highlight</td>
      </tr>
      <tr>
        <td><code>05</code></td>
        <td><strong>05_Base_Bottom_Cover.stl</strong></td>
        <td>35.5 x 38.0 x 1.8 mm</td>
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
      <div class="step-title"><span class="step-num">1</span> Base &amp; ESP32 Hot-Glue Mounting</div>
      <p>Orient <code>01_Base_Pedestal</code> upside down. Insert the ESP32 into the bottom pocket. Align the Micro-USB port flush with the rear tower cutout. Apply 2-3 dabs of hot-melt glue along the corners to anchor firmly to the internal stops.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">2</span> Wire Routing Through Flared Neck</div>
      <p>Feed the 11 cm wiring bundle upward through the <code>16x11mm</code> conduit in <code>02_Neck_and_Head_Pod</code>. The flared <code>20x14mm</code> throat at the top allows wires to fan out easily into the sensor chamber with <strong>~3.5 cm of slack</strong>.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">3</span> Neck Docking into Base Socket</div>
      <p>Insert the male spigot at the bottom of the neck into the mating socket on top of <code>01_Base_Pedestal</code>. Press firmly for a snug slip-fit. For permanent bonding, apply a drop of cyanoacrylate or hot glue along the joint.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">4</span> Snap-Fit Lower Cover Sealing</div>
      <p>Snap <code>05_Base_Bottom_Cover</code> flush into the bottom recess of the base pedestal until the 4 perimeter tabs click into place. Attach rubber adhesive pads into the 4 non-slip corner recesses.</p>
    </div>

    <div class="step-card">
      <div class="step-title"><span class="step-num">5</span> Sensor Faceplate Black Installation</div>
      <p>Press the 2 silver ultrasonic eyes through the lower &Oslash;16.3mm ports and seat the white PIR dome into the upper &Oslash;23.2mm port. Press <code>03_Sensor_Faceplate_Black</code> firmly into the head pod front recess.</p>
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
