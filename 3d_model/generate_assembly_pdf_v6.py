import os
import base64
import subprocess

print("=== Generating StudySense V6 Pro Comprehensive Assembly & Parts PDF Guide ===")

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
HTML_PATH = os.path.join(OUTPUT_DIR, "StudySense_V6_Pro_Assembly_Guide.html")
PDF_PATH = os.path.join(OUTPUT_DIR, "StudySense_V6_Pro_Parts_and_Assembly_Guide.pdf")

def img_b64(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""

b64_hero = img_b64("render_v6_isometric_hero.png")
b64_exploded = img_b64("render_v6_exploded_assembly.png")
b64_front = img_b64("render_v6_front_view.png")
b64_rear = img_b64("render_v6_rear_view.png")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>StudySense V6 Pro Master Assembly Guide</title>
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
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 2px solid #f1f5f9;
    padding-bottom: 12px;
    margin-bottom: 14px;
  }}

  .logo-group {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}

  .logo-icon {{
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, #ff5e14, #ff8c42);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-weight: 800;
    font-size: 20px;
    box-shadow: 0 4px 12px rgba(255, 94, 20, 0.25);
  }}

  .logo-text h1 {{
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #0f172a;
  }}

  .logo-text p {{
    font-size: 11px;
    font-weight: 600;
    color: #ff5e14;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  .doc-badge {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 12px;
    text-align: right;
  }}

  .doc-badge .tag {{
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
  }}

  .doc-badge .val {{
    font-size: 12px;
    font-weight: 700;
    color: #0f172a;
  }}

  .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }}

  .metric-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 12px;
    border-left: 4px solid #ff5e14;
  }}

  .metric-card.green {{
    border-left-color: #10b981;
  }}

  .metric-card.blue {{
    border-left-color: #3b82f6;
  }}

  .metric-card.purple {{
    border-left-color: #8b5cf6;
  }}

  .metric-label {{
    font-size: 10px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    margin-bottom: 4px;
  }}

  .metric-value {{
    font-size: 16px;
    font-weight: 800;
    color: #0f172a;
  }}

  .metric-sub {{
    font-size: 9px;
    color: #94a3b8;
    margin-top: 2px;
  }}

  .hero-img-box {{
    width: 100%;
    height: 140mm;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    background: #f1f5f9;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    margin-bottom: 14px;
    position: relative;
  }}

  .hero-img-box img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
  }}

  .hero-caption {{
    position: absolute;
    bottom: 12px;
    left: 12px;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(8px);
    color: #ffffff;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
  }}

  .section-title {{
    font-size: 14px;
    font-weight: 800;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }}

  .section-title::before {{
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #ff5e14;
    border-radius: 2px;
  }}

  .highlights-box {{
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 12px;
  }}

  .highlights-box h3 {{
    font-size: 12px;
    font-weight: 700;
    color: #1e40af;
    margin-bottom: 6px;
  }}

  .highlights-box p {{
    font-size: 10.5px;
    color: #3b82f6;
    line-height: 1.5;
  }}

  .footer {{
    border-top: 1px solid #e2e8f0;
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 9px;
    color: #94a3b8;
    font-weight: 500;
  }}

  .parts-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 14px;
    font-size: 10px;
  }}

  .parts-table th {{
    background: #f8fafc;
    color: #475569;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 9px;
    padding: 8px 10px;
    border: 1px solid #e2e8f0;
    text-align: left;
  }}

  .parts-table td {{
    padding: 8px 10px;
    border: 1px solid #e2e8f0;
    color: #1e293b;
  }}

  .parts-table tr:nth-child(even) td {{
    background: #f8fafc;
  }}

  .badge {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
  }}

  .badge-white {{ background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }}
  .badge-black {{ background: #0f172a; color: #ffffff; }}
  .badge-orange {{ background: #ff5e14; color: #ffffff; }}

  .step-card {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  }}

  .step-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }}

  .step-num {{
    background: #ff5e14;
    color: #ffffff;
    font-size: 10px;
    font-weight: 800;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  .step-title {{
    font-size: 11px;
    font-weight: 700;
    color: #0f172a;
  }}

  .step-desc {{
    font-size: 10px;
    color: #475569;
    line-height: 1.5;
    padding-left: 28px;
  }}

  .alert-warning {{
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 10px;
  }}

  .alert-warning h4 {{
    font-size: 11px;
    font-weight: 700;
    color: #b45309;
    margin-bottom: 3px;
  }}

  .alert-warning p {{
    font-size: 9.5px;
    color: #92400e;
    line-height: 1.4;
  }}

  .dual-render-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 14px;
  }}

  .dual-card {{
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    background: #f8fafc;
  }}

  .dual-card img {{
    width: 100%;
    height: 70mm;
    object-fit: cover;
  }}

  .dual-card .caption {{
    padding: 8px 10px;
    font-size: 10px;
    font-weight: 700;
    color: #1e293b;
    background: #ffffff;
    border-top: 1px solid #e2e8f0;
    text-align: center;
  }}
</style>
</head>
<body>

<!-- PAGE 1: EXECUTIVE OVERVIEW & HERO -->
<div class="page">
  <div>
    <div class="header">
      <div class="logo-group">
        <div class="logo-icon">S</div>
        <div class="logo-text">
          <h1>StudySense V6 Pro</h1>
          <p>Master Enclosure & Hardware Assembly Guide</p>
        </div>
      </div>
      <div class="doc-badge">
        <div class="tag">Release Spec</div>
        <div class="val">V6 Pro (V4-Refined)</div>
      </div>
    </div>

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">Head Pod Diameter</div>
        <div class="metric-value">72.0 mm</div>
        <div class="metric-sub">Full V4 Master Proportion</div>
      </div>
      <div class="metric-card green">
        <div class="metric-label">Base Solid Floor</div>
        <div class="metric-value">3.0 mm Solid</div>
        <div class="metric-sub">Zero Floating Regions</div>
      </div>
      <div class="metric-card blue">
        <div class="metric-label">ESP32 Installation</div>
        <div class="metric-value">Glue-Gun Ready</div>
        <div class="metric-sub">Dedicated Floor Cradle</div>
      </div>
      <div class="metric-card purple">
        <div class="metric-label">Slicer Compatibility</div>
        <div class="metric-value">Bambu Studio</div>
        <div class="metric-sub">100% Support-Free Printing</div>
      </div>
    </div>

    <div class="hero-img-box">
      <img src="{b64_hero}" alt="StudySense V6 Pro Hero Isometric View">
      <div class="hero-caption">StudySense V6 Pro Desktop Assembly &bull; Full 72mm Head &bull; Hero Isometric View</div>
    </div>

    <div class="highlights-box">
      <h3>Key Engineering Upgrades in Version 6 Pro (V4 Master Refinement)</h3>
      <p>
        <strong>1. Restored V4 Robust Proportions:</strong> Fully restored the iconic 72.0mm circular head pod, 60mm sloped pedestal base, and graceful organic neck. Zero stubby compromises; exactly preserving the loved aesthetic.<br>
        <strong>2. Solid Integrated Base Floor:</strong> Solved Bambu Studio's floating regions warning by building an uninterrupted 3.0mm solid bottom floor directly at Z=0. The ESP32 drops directly onto this flat floor inside the cradle and is secured with hot glue gun adhesive.<br>
        <strong>3. Clean 5-Component Architecture:</strong> Exactly 4 main interlocking enclosure pieces + button cap. No messy extra lids.
      </p>
    </div>
  </div>

  <div class="footer">
    <span>StudySense Hardware Engineering Documentation &bull; Project ID: SS-V6-PRO</span>
    <span>Page 1 of 3</span>
  </div>
</div>

<!-- PAGE 2: EXPLODED ASSEMBLY & PARTS ROSTER -->
<div class="page">
  <div>
    <div class="header">
      <div class="logo-group">
        <div class="logo-icon">S</div>
        <div class="logo-text">
          <h1>Parts Roster & Exploded Diagram</h1>
          <p>StudySense V6 Pro Master 3D Model</p>
        </div>
      </div>
      <div class="doc-badge">
        <div class="tag">Total Printable Parts</div>
        <div class="val">5 Precision Components</div>
      </div>
    </div>

    <div class="hero-img-box" style="height: 105mm; margin-bottom: 12px;">
      <img src="{b64_exploded}" alt="StudySense V6 Pro Exploded Diagram">
      <div class="hero-caption">Exploded Assembly Architecture &bull; Clean Interlocking Tenons & Snap Detents</div>
    </div>

    <div class="section-title">Complete Printable Parts Roster</div>
    <table class="parts-table">
      <thead>
        <tr>
          <th>Part File Name</th>
          <th>Color / Material</th>
          <th>Dimensions (W &times; D &times; H)</th>
          <th>Key Functional Features</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>01_Base_Pedestal.stl</strong></td>
          <td><span class="badge badge-white">Matte White Silk</span></td>
          <td>55.7 &times; 81.2 &times; 34.0 mm</td>
          <td>Solid 3mm bed floor, ESP32 cradle pocket, rear USB cutout, sloped StudySense logo.</td>
        </tr>
        <tr>
          <td><strong>02_Neck_and_Head_Pod.stl</strong></td>
          <td><span class="badge badge-white">Matte White Silk</span></td>
          <td>72.0 &times; 39.4 &times; 148.1 mm</td>
          <td>Full &Oslash;72mm head pod, top fin, hollow wire conduit (16&times;11mm), 3x LED holes.</td>
        </tr>
        <tr>
          <td><strong>03_Sensor_Faceplate_Black.stl</strong></td>
          <td><span class="badge badge-black">Carbon Black</span></td>
          <td>62.6 &times; 61.8 &times; 2.4 mm</td>
          <td>&Oslash;23.2mm PIR dome aperture, 2x &Oslash;16.2mm ultrasonic eye ports, oscillator slot.</td>
        </tr>
        <tr>
          <td><strong>04_Accent_Ring_Orange.stl</strong></td>
          <td><span class="badge badge-orange">Accent Orange</span></td>
          <td>66.6 &times; 66.6 &times; 2.2 mm</td>
          <td>Iconic circular halo ring, chamfered rim, snaps into head pod lip.</td>
        </tr>
        <tr>
          <td><strong>05_Button_Cap.stl</strong></td>
          <td><span class="badge badge-orange">Accent Orange</span></td>
          <td>6.0 &times; 6.0 &times; 7.5 mm</td>
          <td>Tactile push button plunger cap for the rear stand mode switch.</td>
        </tr>
      </tbody>
    </table>

    <div class="dual-render-grid">
      <div class="dual-card">
        <img src="{b64_front}" alt="Front View">
        <div class="caption">Front Elevation &bull; Sensors, LEDs & Logo</div>
      </div>
      <div class="dual-card">
        <img src="{b64_rear}" alt="Rear View">
        <div class="caption">Rear Elevation &bull; USB Port & Push Button</div>
      </div>
    </div>
  </div>

  <div class="footer">
    <span>StudySense Hardware Engineering Documentation &bull; Project ID: SS-V6-PRO</span>
    <span>Page 2 of 3</span>
  </div>
</div>

<!-- PAGE 3: STEP-BY-STEP ASSEMBLY & 3D PRINTING -->
<div class="page">
  <div>
    <div class="header">
      <div class="logo-group">
        <div class="logo-icon">S</div>
        <div class="logo-text">
          <h1>Assembly Guide & Slicer Settings</h1>
          <p>Hardware Integration & Bambu Studio Profile</p>
        </div>
      </div>
      <div class="doc-badge">
        <div class="tag">Assembly Time</div>
        <div class="val">&approx; 10 Minutes</div>
      </div>
    </div>

    <div class="section-title">Step-by-Step Hardware Assembly</div>

    <div class="step-card">
      <div class="step-header">
        <div class="step-num">1</div>
        <div class="step-title">ESP32 Hot-Glue Installation in Base Pedestal</div>
      </div>
      <div class="step-desc">
        Lay <code>01_Base_Pedestal</code> on your bench. Notice the solid 3mm floor inside. Drop the ESP32 board directly onto the floor inside the corner alignment stops. Align the USB port with the rear cutout (12.5 &times; 7.0mm). Apply 3-4 drops of hot glue gun adhesive around the corners. The board bonds firmly and instantly to the solid floor.
      </div>
    </div>

    <div class="step-card">
      <div class="step-header">
        <div class="step-num">2</div>
        <div class="step-title">Rear Push-Button Installation</div>
      </div>
      <div class="step-desc">
        Insert the orange <code>05_Button_Cap</code> through the &Oslash;6.5mm hole on the rear transition wall. Wire the tactile switch to GPIO 22 and GND.
      </div>
    </div>

    <div class="step-card">
      <div class="step-header">
        <div class="step-num">3</div>
        <div class="step-title">Status LED Push-Fit Mounting</div>
      </div>
      <div class="step-desc">
        From inside the neck, insert the three 3mm/5mm wired LEDs into the front neck ports: <strong>Green LED</strong> at the top (Z=76mm, Study Mode), <strong>Blue LED</strong> in the middle (Z=62mm, Break Mode), and <strong>Red LED</strong> at the bottom (Z=48mm, Posture Alert). The 5.0mm counterbores hold them firmly.
      </div>
    </div>

    <div class="step-card">
      <div class="step-header">
        <div class="step-num">4</div>
        <div class="step-title">Wire Harness Routing & Neck Docking</div>
      </div>
      <div class="step-desc">
        Route the sensor wires up through the generous 16.0 &times; 11.0mm hollow conduit of <code>02_Neck_and_Head_Pod</code> into the head chamber. Press the lower neck tenon firmly into the base pedestal socket until it clicks flush.
      </div>
    </div>

    <div class="step-card">
      <div class="step-header">
        <div class="step-num">5</div>
        <div class="step-title">Head Pod Sensor Mating & Faceplate Closure</div>
      </div>
      <div class="step-desc">
        Mount the HC-SR04 ultrasonic transducer eyes and PIR dome into <code>03_Sensor_Faceplate_Black</code>. Snap the vibrant orange <code>04_Accent_Ring_Orange</code> around the faceplate rim. Align the perimeter snap clips and press the complete faceplate assembly into the front of the head pod.
      </div>
    </div>

    <div class="alert-warning">
      <h4>Bambu Studio 3D Printing Calibration (100% Support-Free)</h4>
      <p>
        <strong>Preset:</strong> 0.20mm Standard @BBL H2S / X1C / P1S &bull; <strong>Walls:</strong> 3 loops &bull; <strong>Infill:</strong> 15% Gyroid &bull; <strong>Supports:</strong> NONE required. All parts print flat on the build plate with zero floating regions. Native project file: <code>StudySense_V6_Pro_BambuStudio.3mf</code>.
      </p>
    </div>
  </div>

  <div class="footer">
    <span>StudySense Hardware Engineering Documentation &bull; Project ID: SS-V6-PRO</span>
    <span>Page 3 of 3</span>
  </div>
</div>

</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Saved HTML template: {HTML_PATH}")

chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cmd = [
    chrome_bin,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={PDF_PATH}",
    HTML_PATH
]

print("Executing Chrome headless PDF generation...")
res = subprocess.run(cmd, capture_output=True, text=True)
if os.path.exists(PDF_PATH):
    print(f"SUCCESS! Generated PDF: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")
else:
    print("PDF generation failed.")
