import os
import base64
import subprocess

print("=== Generating StudySense V5.0 Comprehensive Assembly & Parts PDF Guide ===")

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
HTML_PATH = os.path.join(OUTPUT_DIR, "StudySense_V5_Compact_Assembly_Guide.html")
PDF_PATH = os.path.join(OUTPUT_DIR, "StudySense_V5_Compact_Parts_and_Assembly_Guide.pdf")

# Read images and encode in base64
def img_b64(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""

b64_hero = img_b64("render_v5_isometric_hero.png")
b64_exploded = img_b64("render_v5_exploded_assembly.png")
b64_front = img_b64("render_v5_front_view.png")
b64_rear = img_b64("render_v5_rear_view.png")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>StudySense V5.0 Compact Enclosure Guide</title>
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

  /* Header styles */
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

  /* Key Metrics Grid */
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

  /* Images */
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

  /* Section Title */
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

  /* Highlights Box */
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

  /* Footer */
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

  /* Tables */
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

  /* Steps Grid */
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
          <h1>StudySense V5.0 Compact</h1>
          <p>Production Enclosure & Assembly Guide</p>
        </div>
      </div>
      <div class="doc-badge">
        <div class="tag">Release Spec</div>
        <div class="val">V5.0 Compact (&le;11cm)</div>
      </div>
    </div>

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">Max Total Height</div>
        <div class="metric-value">104.0 mm</div>
        <div class="metric-sub">&le; 11.0 cm Wire Constraint</div>
      </div>
      <div class="metric-card green">
        <div class="metric-label">Wire Path Distance</div>
        <div class="metric-value">82.0 mm</div>
        <div class="metric-sub">28mm Comfortable Slack</div>
      </div>
      <div class="metric-card blue">
        <div class="metric-label">Base Solid Floor</div>
        <div class="metric-value">3.0 mm Flat</div>
        <div class="metric-sub">Zero Floating Overhangs</div>
      </div>
      <div class="metric-card purple">
        <div class="metric-label">Slicer Compatibility</div>
        <div class="metric-value">Bambu Studio</div>
        <div class="metric-sub">100% Support-Free Printing</div>
      </div>
    </div>

    <div class="hero-img-box">
      <img src="{b64_hero}" alt="StudySense V5 Hero Isometric View">
      <div class="hero-caption">StudySense V5.0 Compact Desktop Assembly &bull; Hero Isometric View</div>
    </div>

    <div class="highlights-box">
      <h3>Key Engineering Upgrades in Version 5.0 Compact</h3>
      <p>
        <strong>1. Wire Length Calibration:</strong> Overall assembly height reduced to 104mm to ensure full compatibility with the 11cm PIR sensor wire harness. The wire path from the ESP32 cradle to the head pod is only 82mm, leaving 28mm of slack with zero strain.<br>
        <strong>2. Solid Integrated Base Floor:</strong> Eliminated the detached bottom plate. The base pedestal now features a solid 3.0mm flat foundation printed directly on the bed, providing a rigid cradle for hot-glue ESP32 installation and eliminating Bambu Studio floating region warnings.
      </p>
    </div>
  </div>

  <div class="footer">
    <span>StudySense Hardware Engineering Documentation &bull; Project ID: SS-V5-COMPACT</span>
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
          <p>StudySense V5.0 Compact 3D Model</p>
        </div>
      </div>
      <div class="doc-badge">
        <div class="tag">Total Printable Parts</div>
        <div class="val">6 Precision Components</div>
      </div>
    </div>

    <div class="hero-img-box" style="height: 105mm; margin-bottom: 12px;">
      <img src="{b64_exploded}" alt="StudySense V5 Exploded Diagram">
      <div class="hero-caption">Exploded Assembly Architecture &bull; Toolless Interlocking Detents</div>
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
          <td>44.6 &times; 67.6 &times; 22.0 mm</td>
          <td>Solid 3mm bed floor, ESP32 hot-glue pocket, rear USB cutout, sloped StudySense logo.</td>
        </tr>
        <tr>
          <td><strong>02_Neck_and_Head_Pod.stl</strong></td>
          <td><span class="badge badge-white">Matte White Silk</span></td>
          <td>54.0 &times; 30.4 &times; 89.2 mm</td>
          <td>Lofted organic neck, &Oslash;54mm head pod, top fin, hollow wire conduit, 3x LED holes.</td>
        </tr>
        <tr>
          <td><strong>03_Sensor_Faceplate_Black.stl</strong></td>
          <td><span class="badge badge-black">Carbon Black</span></td>
          <td>47.6 &times; 47.0 &times; 2.0 mm</td>
          <td>&Oslash;19mm PIR dome aperture, 2x &Oslash;14mm HC-SR04 transducer eye ports, snap tabs.</td>
        </tr>
        <tr>
          <td><strong>04_Accent_Ring_Orange.stl</strong></td>
          <td><span class="badge badge-orange">Accent Orange</span></td>
          <td>50.6 &times; 50.6 &times; 1.8 mm</td>
          <td>Iconic circular halo ring, chamfered edge, snaps into head pod lip.</td>
        </tr>
        <tr>
          <td><strong>05_Rear_Foot_Lid.stl</strong></td>
          <td><span class="badge badge-white">Matte White Silk</span></td>
          <td>30.6 &times; 47.6 &times; 3.5 mm</td>
          <td>Flush snap-on service cover for rear ESP32 chamber with finger pry notch.</td>
        </tr>
        <tr>
          <td><strong>06_Button_Cap.stl</strong></td>
          <td><span class="badge badge-orange">Accent Orange</span></td>
          <td>6.0 &times; 6.0 &times; 7.3 mm</td>
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
    <span>StudySense Hardware Engineering Documentation &bull; Project ID: SS-V5-COMPACT</span>
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
        Place the ESP32 board directly onto the solid 3mm floor of <code>01_Base_Pedestal</code>. Align the Micro-USB / Type-C port with the rear rectangular cutout (12.0 &times; 6.5mm). Apply 3-4 drops of hot glue gun adhesive along the corner alignment tabs. The board adheres instantly and firmly to the solid floor.
      </div>
    </div>

    <div class="step-card">
      <div class="step-header">
        <div class="step-num">2</div>
        <div class="step-title">Rear Push-Button & Lid Installation</div>
      </div>
      <div class="step-desc">
        Insert the orange <code>06_Button_Cap</code> through the &Oslash;6.5mm hole on the rear transition wall. Connect the button signal wires to the ESP32. Once wiring is checked, press <code>05_Rear_Foot_Lid</code> over the rear chamber until all 4 corner detents snap flush into the base.
      </div>
    </div>

    <div class="step-card">
      <div class="step-header">
        <div class="step-num">3</div>
        <div class="step-title">Status LED Push-Fit Mounting</div>
      </div>
      <div class="step-desc">
        Insert the 3 wired status LEDs from the inside through the front neck ports: <strong>Green LED</strong> at the top (Z=44mm, Study Mode), <strong>Blue LED</strong> in the middle (Z=36mm, Break Mode), and <strong>Red LED</strong> at the bottom (Z=28mm, Posture Alert). The 4.8mm counterbores provide a snug friction fit.
      </div>
    </div>

    <div class="step-card">
      <div class="step-header">
        <div class="step-num">4</div>
        <div class="step-title">Wire Harness Routing & Neck Docking</div>
      </div>
      <div class="step-desc">
        Route the sensor wires up through the hollow conduit (13.0 &times; 8.5mm) of <code>02_Neck_and_Head_Pod</code> into the head chamber. With the 82mm wire path, the 11cm sensor harness has 28mm of comfortable slack. Press the lower neck tenon firmly into the base pedestal socket until it clicks flush.
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
        <strong>Preset:</strong> 0.20mm Standard @BBL H2S / X1C / P1S &bull; <strong>Walls:</strong> 3 loops &bull; <strong>Infill:</strong> 15% Gyroid &bull; <strong>Supports:</strong> NONE required. All parts print flat on the build plate with zero floating regions. Native project file: <code>StudySense_V5_Compact_BambuStudio.3mf</code>.
      </p>
    </div>
  </div>

  <div class="footer">
    <span>StudySense Hardware Engineering Documentation &bull; Project ID: SS-V5-COMPACT</span>
    <span>Page 3 of 3</span>
  </div>
</div>

</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Saved HTML template: {HTML_PATH}")

# Convert HTML to PDF using Chrome Headless
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
print("Chrome output:", res.stdout, res.stderr)

if os.path.exists(PDF_PATH):
    print(f"SUCCESS! Generated PDF: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")
else:
    print("PDF generation failed.")
