import bpy
import bmesh
import math
import os

print("=== Generating StudySense V6 Pro (V4-Refined Master Architecture) ===")

# Reset scene completely
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001 # 1 unit = 1 mm

# Set up studio world with soft ambient illumination
world = bpy.data.worlds.new('Studio_World')
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get('Background')
if bg_node:
    bg_node.inputs['Color'].default_value = (0.94, 0.95, 0.97, 1.0)
    bg_node.inputs['Strength'].default_value = 1.0

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
STL_DIR = os.path.join(OUTPUT_DIR, "v6_pro_stl")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STL_DIR, exist_ok=True)

# -------------------------------------------------------------
# Color & Material Palette (Exact V4 Master Match)
# -------------------------------------------------------------
def make_mat(name, color, roughness=0.30, metallic=0.0, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if emission:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = emission
                bsdf.inputs['Emission Strength'].default_value = emission_strength
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = emission
    return mat

mat_white  = make_mat("Matte_White_Silk",   (0.96, 0.96, 0.98, 1.0), roughness=0.22)
mat_black  = make_mat("Matte_Carbon_Black", (0.04, 0.04, 0.05, 1.0), roughness=0.45)
mat_orange = make_mat("Accent_Orange",      (1.00, 0.22, 0.01, 1.0), roughness=0.18)
mat_metal  = make_mat("Sensor_Metal",       (0.88, 0.88, 0.91, 1.0), roughness=0.15, metallic=0.92)
mat_mesh   = make_mat("Transducer_Mesh",    (0.02, 0.02, 0.02, 1.0), roughness=0.70)
mat_pcb    = make_mat("Sensor_Blue_PCB",    (0.02, 0.22, 0.65, 1.0), roughness=0.30)
mat_pir    = make_mat("PIR_Fresnel_Dome",   (0.96, 0.96, 1.0, 1.0),  roughness=0.15)
mat_desk   = make_mat("Desk_Wood",          (0.70, 0.52, 0.35, 1.0), roughness=0.55)
mat_pad    = make_mat("Desk_Felt_Pad",      (0.12, 0.14, 0.18, 1.0), roughness=0.85)

mat_led_g  = make_mat("LED_Green", (0.10, 0.95, 0.30, 1.0), roughness=0.1, emission=(0.10, 0.95, 0.30, 1.0), emission_strength=8.0)
mat_led_b  = make_mat("LED_Blue",  (0.15, 0.50, 0.98, 1.0), roughness=0.1, emission=(0.15, 0.50, 0.98, 1.0), emission_strength=8.0)
mat_led_r  = make_mat("LED_Red",   (0.98, 0.08, 0.12, 1.0), roughness=0.1, emission=(0.98, 0.08, 0.12, 1.0), emission_strength=8.0)

def set_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

def smooth_obj(obj, angle_deg=35.0):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))
    except Exception:
        pass

def apply_bool(target, tool, operation='DIFFERENCE', solver='EXACT'):
    mod = target.modifiers.new(name="Bool", type='BOOLEAN')
    mod.operation = operation
    mod.object = tool
    mod.solver = solver
    bpy.context.view_layer.objects.active = target
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception:
        mod.solver = 'FLOAT'
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool, do_unlink=True)

def add_cyl(name, r, h, loc=(0,0,0), rot=(0,0,0), segs=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segs, radius=r, depth=h, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    return obj

def add_cube(name, size, loc=(0,0,0), rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj

def add_rounded_box(name, w, d, h, r, segs=12, loc=(0,0,0), rot=(0,0,0)):
    bm = bmesh.new()
    dx = max(w/2.0 - r, 0.01)
    dy = max(d/2.0 - r, 0.01)
    corners = [
        (dx, dy, 0, math.pi/2),
        (-dx, dy, math.pi/2, math.pi),
        (-dx, -dy, math.pi, 3*math.pi/2),
        (dx, -dy, 3*math.pi/2, 2*math.pi)
    ]
    verts_bottom = []
    for cx, cy, start_ang, end_ang in corners:
        for i in range(segs):
            theta = start_ang + (end_ang - start_ang) * i / segs
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            verts_bottom.append(bm.verts.new((x, y, 0)))
    
    face_bot = bm.faces.new(verts_bottom)
    res = bmesh.ops.extrude_face_region(bm, geom=[face_bot])
    verts_extruded = [e for e in res['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, h), verts=verts_extruded)
    
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    return obj

def add_tapered_capsule_column(name, w_bot, d_bot, w_top, d_top, h, r_bot, r_top, segs=12, loc=(0,0,0)):
    bm = bmesh.new()
    dx_b = max(w_bot/2.0 - r_bot, 0.01)
    dy_b = max(d_bot/2.0 - r_bot, 0.01)
    corners_b = [
        (dx_b, dy_b, 0, math.pi/2),
        (-dx_b, dy_b, math.pi/2, math.pi),
        (-dx_b, -dy_b, math.pi, 3*math.pi/2),
        (dx_b, -dy_b, 3*math.pi/2, 2*math.pi)
    ]
    verts_b = []
    for cx, cy, sa, ea in corners_b:
        for i in range(segs):
            th = sa + (ea - sa) * i / segs
            verts_b.append(bm.verts.new((cx + r_bot * math.cos(th), cy + r_bot * math.sin(th), 0)))
    
    dx_t = max(w_top/2.0 - r_top, 0.01)
    dy_t = max(d_top/2.0 - r_top, 0.01)
    corners_t = [
        (dx_t, dy_t, 0, math.pi/2),
        (-dx_t, dy_t, math.pi/2, math.pi),
        (-dx_t, -dy_t, math.pi, 3*math.pi/2),
        (dx_t, -dy_t, 3*math.pi/2, 2*math.pi)
    ]
    verts_t = []
    for cx, cy, sa, ea in corners_t:
        for i in range(segs):
            th = sa + (ea - sa) * i / segs
            verts_t.append(bm.verts.new((cx + r_top * math.cos(th), cy + r_top * math.sin(th), h)))
    
    bm.faces.new(verts_b)
    bm.faces.new(reversed(verts_t))
    n_pts = len(verts_b)
    for i in range(n_pts):
        i_next = (i + 1) % n_pts
        bm.faces.new([verts_b[i], verts_b[i_next], verts_t[i_next], verts_t[i]])
    
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return obj

# -------------------------------------------------------------
# GEOMETRIC PARAMETERS (EXACT V4 MASTER PROPORTIONS)
# -------------------------------------------------------------
TILT_DEG = 7.0
TILT_RAD = math.radians(TILT_DEG)
ROT_X = math.radians(90.0 + TILT_DEG)

HEAD_RADIUS = 36.0  # Exact 72mm Outer Diameter (V4 Master!)
HEAD_DEPTH  = 30.0  # Exact 30mm depth
HEAD_Z      = 124.0 # Center of circular head (Proportionally balanced with V4 posture)
HEAD_Y      = 3.0   # Center Y

FRONT_OFFSET = HEAD_DEPTH / 2.0 # 15mm forward along local Z
FACE_Y = HEAD_Y - FRONT_OFFSET * math.cos(TILT_RAD)
FACE_Z = HEAD_Z - FRONT_OFFSET * math.sin(TILT_RAD)

BASE_H = 34.0  # Height of front pedestal tower
NECK_H = 58.0  # Height of neck column (Z=34 to Z=92, merges into Ø72mm head at Z=88)

print(f"StudySense V6 Pro Architecture:")
print(f"Head Diameter: {HEAD_RADIUS*2:.1f}mm (Full V4 Master Scale)")
print(f"Base Height: {BASE_H}mm | Neck Height: {NECK_H}mm")
print(f"Pod Center: (0, {HEAD_Y}, {HEAD_Z}) | Front Face: (0, {FACE_Y:.2f}, {FACE_Z:.2f})")
print(f"Total Height to Fin Peak: ~152mm (Robust 'Rost' V4 Silhouette)")

# =============================================================
# PART 1: 01_Base_Pedestal (Solid Integrated 3.0mm Floor, Hot-Glue Ready)
# =============================================================
print("Constructing Part 1: Base Pedestal (Solid 3mm Bottom Floor, Zero Floating Regions)...")

# 1. Front Pedestal Body (W: 60mm at bottom tapering to 52mm at top, D: 36mm, H: 34mm)
base_front = add_rounded_box("Base_Front", w=60.0, d=36.0, h=BASE_H, r=6.0, segs=12, loc=(0, 6.0, 0))

# Side taper cutter
base_taper_l = add_cube("Base_Tap_L", (20.0, 50.0, 45.0), loc=(-36.0, 6.0, 17.0), rot=(0, math.radians(6.5), 0))
apply_bool(base_front, base_taper_l, operation='DIFFERENCE')
base_taper_r = add_cube("Base_Tap_R", (20.0, 50.0, 45.0), loc=(36.0, 6.0, 17.0), rot=(0, math.radians(-6.5), 0))
apply_bool(base_front, base_taper_r, operation='DIFFERENCE')

# 2. Rear Foot Extension (W: 46.0mm, D: 46.0mm, H: 14.0mm, R: 8.0mm)
# Total footprint depth = 36mm + 46mm = 82mm
base_foot = add_rounded_box("Base_Foot", w=46.0, d=46.0, h=14.0, r=8.0, segs=12, loc=(0, 46.0, 0))
apply_bool(base_front, base_foot, operation='UNION')
base_obj = base_front
base_obj.name = "01_Base_Pedestal"

# 3. 15-degree sloping front ramp (Display face for logo)
ramp = add_cube("Ramp_Cutter", (80.0, 24.0, 60.0), loc=(0, -18.0, 21.0), rot=(math.radians(15), 0, 0))
apply_bool(base_obj, ramp, operation='DIFFERENCE')

# 4. SOLID INTEGRATED BASE FLOOR & ESP32 GLUE-GUN CHAMBER:
# Solid 3.0mm flat floor directly on Z=0!
# The internal cavity starts strictly at Z=3.0mm (NO cut to Z=0!).
# Rear foot chamber: W=36.0mm, D=42.0mm, H=8.0mm (Z=3.0 to 11.0mm, leaves solid 3.0mm roof on rear foot!)
rear_chamber = add_rounded_box("Rear_Chamber", w=36.0, d=42.0, h=8.0, r=3.5, segs=8, loc=(0, 44.0, 3.0))
apply_bool(base_obj, rear_chamber, operation='DIFFERENCE')

# Front tower chamber: W=38.0mm, D=24.0mm, H=23.0mm (Z=3.0 to 26.0mm, opens under neck socket)
front_chamber = add_rounded_box("Front_Chamber", w=38.0, d=24.0, h=23.0, r=3.5, segs=8, loc=(0, 10.0, 3.0))
apply_bool(base_obj, front_chamber, operation='DIFFERENCE')

# ESP32 Alignment Corner Stops (Directly on the solid floor, rising from Z=3.0 to 5.0mm)
for gx, gy in [(-15.0, 14.0), (15.0, 14.0), (-15.0, 56.0), (15.0, 56.0)]:
    stop = add_cube(f"Stop_{gx}_{gy}", (2.5, 4.0, 2.0), loc=(gx, gy, 4.0))
    apply_bool(base_obj, stop, operation='UNION')

# 5. Rear USB Port Opening (12.5mm x 7.0mm centered at Y=68mm, Z=3.0 to 10.0mm)
usb_cut = add_rounded_box("USB_Port", w=12.5, d=20.0, h=7.0, r=1.5, segs=6, loc=(0, 62.0, 3.0))
apply_bool(base_obj, usb_cut, operation='DIFFERENCE')

# 6. Rear Push Button Mount Hole (Ø6.5mm on rear transition wall at Y=23mm, Z=24mm)
btn_cut = add_cyl("Btn_Hole", r=3.25, h=25.0, loc=(0, 23.0, 24.0), rot=(math.radians(90), 0, 0), segs=32)
apply_bool(base_obj, btn_cut, operation='DIFFERENCE')

# 7. Top Mating Socket for Neck Docking (W: 34.5mm, D: 21.5mm, Depth: 8.0mm at Z=26.0 to 34.0mm)
socket_cut = add_rounded_box("Neck_Socket", w=34.5, d=21.5, h=9.0, r=4.0, segs=8, loc=(0, 6.0, 26.0))
apply_bool(base_obj, socket_cut, operation='DIFFERENCE')

# Wire through-hole connecting socket directly to internal chamber
wire_hole = add_cube("Wire_Through_Hole", (20.0, 12.0, 15.0), loc=(0, 6.0, 20.0))
apply_bool(base_obj, wire_hole, operation='DIFFERENCE')

# Snap Detent Grooves inside socket
snap_groove_l = add_cube("Snap_G_L", (1.4, 7.0, 2.0), loc=(-17.2, 6.0, 30.0))
apply_bool(base_obj, snap_groove_l, operation='DIFFERENCE')
snap_groove_r = add_cube("Snap_G_R", (1.4, 7.0, 2.0), loc=(17.2, 6.0, 30.0))
apply_bool(base_obj, snap_groove_r, operation='DIFFERENCE')

# 8. Embossed StudySense Logo on sloped front face
# Halo ring at Z=20mm
logo_ring = add_cyl("Logo_Ring", r=5.5, h=2.5, loc=(0, -8.0, 20.0), rot=(math.radians(105), 0, 0), segs=48)
logo_hole = add_cyl("Logo_Ring_Hole", r=3.4, h=3.5, loc=(0, -8.0, 20.0), rot=(math.radians(105), 0, 0), segs=48)
apply_bool(logo_ring, logo_hole, operation='DIFFERENCE')

# Stylized 'S' core loop at Z=13mm
logo_s_outer = add_cyl("Logo_S_Outer", r=4.0, h=2.5, loc=(0, -10.0, 13.0), rot=(math.radians(105), 0, 0), segs=48)
logo_s_inner = add_cyl("Logo_S_Inner", r=2.2, h=3.5, loc=(0, -10.0, 13.0), rot=(math.radians(105), 0, 0), segs=48)
apply_bool(logo_s_outer, logo_s_inner, operation='DIFFERENCE')
apply_bool(logo_ring, logo_s_outer, operation='UNION')
apply_bool(base_obj, logo_ring, operation='UNION')

smooth_obj(base_obj, 35.0)
set_mat(base_obj, mat_white)
print("Part 1: Base Pedestal created successfully (100% solid floor, zero floating regions).")

# =============================================================
# PART 2: 02_Neck_and_Head_Pod (Organic Unified Upper Assembly)
# =============================================================
print("Constructing Part 2: Neck and Head Pod (Full 72mm Diameter)...")

# 1. Circular Head Pod Outer Cylinder (OD: 72mm, Depth: 30mm)
head_pod = add_cyl("Head_Outer", r=HEAD_RADIUS, h=HEAD_DEPTH, loc=(0, HEAD_Y, HEAD_Z), rot=(ROT_X, 0, 0), segs=96)

# 2. Smooth Spherical Dome Back
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=HEAD_RADIUS, location=(0, HEAD_Y + 5.0, HEAD_Z))
dome = bpy.context.active_object
dome.name = "Dome_Back"
dome.scale = (1.0, 0.42, 1.0)
bpy.ops.object.transform_apply(scale=True)
apply_bool(head_pod, dome, operation='UNION')

# 3. Top Stalk / Fin (Iconic antenna handle - full V4 proportion)
fin = add_rounded_box("Top_Fin", w=16.0, d=10.0, h=36.0, r=4.8, segs=12, 
                      loc=(0, HEAD_Y + 9.5, HEAD_Z + 22.0), rot=(math.radians(14), 0, 0))
apply_bool(head_pod, fin, operation='UNION')

# 4. Organic Tapered Neck Stem (Lofted from Z=34 to Z=92)
# Bottom: W=36mm, D=22mm. Top: W=28mm, D=20mm (Smooth upward draft)
neck = add_tapered_capsule_column("Neck_Stem", w_bot=36.0, d_bot=22.0, w_top=28.0, d_top=20.0, 
                                  h=NECK_H, r_bot=5.5, r_top=4.5, segs=12, loc=(0, 6.0, BASE_H))

# Union Neck with Head Pod
apply_bool(neck, head_pod, operation='UNION')
head_neck_obj = neck
head_neck_obj.name = "02_Neck_and_Head_Pod"

# 5. Lower Male Mounting Tenon (Docks into Base Socket at Z=26.0 to 34.0mm)
tenon = add_rounded_box("Neck_Tenon", w=33.8, d=20.8, h=8.5, r=3.8, segs=8, loc=(0, 6.0, 25.5))
snap_l = add_cube("Snap_L", (1.2, 6.0, 1.8), loc=(-16.8, 6.0, 30.0))
apply_bool(tenon, snap_l, operation='UNION')
snap_r = add_cube("Snap_R", (1.2, 6.0, 1.8), loc=(16.8, 6.0, 30.0))
apply_bool(tenon, snap_r, operation='UNION')
apply_bool(head_neck_obj, tenon, operation='UNION')

# 6. Continuous Hollow Wire Conduit through Tenon, Neck, into Head Pod (16.0mm x 11.0mm)
conduit = add_rounded_box("Wire_Conduit", w=16.0, d=11.0, h=NECK_H + 28.0, r=2.5, segs=6, loc=(0, 6.0, 23.0))
apply_bool(head_neck_obj, conduit, operation='DIFFERENCE')

# 7. Head Pod Interior Sensor Chamber (Diameter: 56.0mm, Depth: 20.0mm)
head_interior = add_cyl("Head_Chamber", r=28.0, h=20.0, loc=(0, HEAD_Y - 1.5, HEAD_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(head_neck_obj, head_interior, operation='DIFFERENCE')

# 8. Front Recesses for Faceplate Assembly:
# Recess 1: Orange Accent Ring Lip (Ø66.8mm, Depth: 2.2mm)
ring_recess = add_cyl("Ring_Lip", r=33.4, h=3.0, loc=(0, FACE_Y + 0.6, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(head_neck_obj, ring_recess, operation='DIFFERENCE')

# Recess 2: Black Faceplate Rim (Ø61.4mm, Depth: 4.2mm)
face_recess = add_cyl("Face_Rim", r=30.7, h=5.0, loc=(0, FACE_Y + 1.2, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(head_neck_obj, face_recess, operation='DIFFERENCE')

# 9. 3x Status LED Mounting Holes on Front Neck Face (Ø3.2mm clean holes with Ø5.0mm counterbore)
# Green (Study Mode), Blue (Break Mode), Red (Posture Alert)
for z_led in [76.0, 62.0, 48.0]:
    led_h = add_cyl(f"LED_Thru_{z_led}", r=1.6, h=10.0, loc=(0, -4.0, z_led), rot=(math.radians(90), 0, 0), segs=32)
    apply_bool(head_neck_obj, led_h, operation='DIFFERENCE')
    led_cb = add_cyl(f"LED_CB_{z_led}", r=2.5, h=6.0, loc=(0, 1.5, z_led), rot=(math.radians(90), 0, 0), segs=32)
    apply_bool(head_neck_obj, led_cb, operation='DIFFERENCE')

# Internal sensor support ledges inside head cavity
shelf_hc = add_cube("Shelf_HC", (46.0, 8.0, 2.5), loc=(0, 2.0, HEAD_Z - 14.0), rot=(ROT_X, 0, 0))
apply_bool(head_neck_obj, shelf_hc, operation='UNION')

shelf_pir = add_cube("Shelf_PIR", (34.0, 8.0, 2.5), loc=(0, 2.0, HEAD_Z + 14.0), rot=(ROT_X, 0, 0))
apply_bool(head_neck_obj, shelf_pir, operation='UNION')

smooth_obj(head_neck_obj, 35.0)
set_mat(head_neck_obj, mat_white)
print("Part 2: Neck and Head Pod created successfully.")

# =============================================================
# PART 3: 03_Sensor_Faceplate_Black (Precision Matte Faceplate)
# =============================================================
print("Constructing Part 3: Sensor Faceplate...")

face_obj = add_cyl("03_Sensor_Faceplate_Black", r=30.6, h=2.4, loc=(0, FACE_Y, FACE_Z), rot=(ROT_X, 0, 0), segs=96)

# 1. PIR Dome Aperture: Ø23.2mm in upper quadrant (Z = +11.8mm local)
pir_local_z = 11.8
pir_z = FACE_Z + pir_local_z * math.cos(TILT_RAD)
pir_y = FACE_Y - pir_local_z * math.sin(TILT_RAD)
pir_cut = add_cyl("PIR_Aperture", r=11.6, h=8.0, loc=(0, pir_y, pir_z), rot=(ROT_X, 0, 0), segs=64)
apply_bool(face_obj, pir_cut, operation='DIFFERENCE')

# 2. HC-SR04 Ultrasonic Dual Transducer Eyes: 2x Ø16.2mm (pitch 26.0mm at Z = -11.0mm local)
hc_local_z = -11.0
hc_z = FACE_Z + hc_local_z * math.cos(TILT_RAD)
hc_y = FACE_Y - hc_local_z * math.sin(TILT_RAD)
for eye_x in [-13.0, 13.0]:
    eye_cut = add_cyl(f"HC_Eye_{eye_x}", r=8.10, h=8.0, loc=(eye_x, hc_y, hc_z), rot=(ROT_X, 0, 0), segs=64)
    apply_bool(face_obj, eye_cut, operation='DIFFERENCE')

# 3. Crystal Oscillator / Status Window (7.0mm x 3.5mm centered between transducers)
osc_cut = add_cube("Osc_Window", (7.0, 8.0, 3.5), loc=(0, hc_y, hc_z), rot=(ROT_X, 0, 0))
apply_bool(face_obj, osc_cut, operation='DIFFERENCE')

# 4. Snap-fit perimeter detents (4x clips at 0°, 90°, 180°, 270°)
for angle_deg in [0, 90, 180, 270]:
    rad = math.radians(angle_deg)
    tab_lx = 30.1 * math.cos(rad)
    tab_lz = 30.1 * math.sin(rad)
    tab_x = tab_lx
    tab_y = FACE_Y - tab_lz * math.sin(TILT_RAD)
    tab_z = FACE_Z + tab_lz * math.cos(TILT_RAD)
    snap_tab = add_cube(f"Snap_Tab_{angle_deg}", (2.4, 1.6, 2.4), loc=(tab_x, tab_y, tab_z), rot=(ROT_X, 0, 0))
    apply_bool(face_obj, snap_tab, operation='UNION')

smooth_obj(face_obj, 35.0)
set_mat(face_obj, mat_black)
print("Part 3: Sensor Faceplate created successfully.")

# =============================================================
# PART 4: 04_Accent_Ring_Orange (Vibrant Halo Ring)
# =============================================================
print("Constructing Part 4: Accent Ring Orange...")

ring_outer = add_cyl("04_Accent_Ring_Orange", r=33.3, h=2.2, loc=(0, FACE_Y - 0.2, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
ring_inner = add_cyl("Ring_Inner_Hole", r=30.7, h=4.0, loc=(0, FACE_Y - 0.2, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(ring_outer, ring_inner, operation='DIFFERENCE')
ring_obj = ring_outer

chamf = ring_obj.modifiers.new(name="Bevel", type='BEVEL')
chamf.width = 0.35
chamf.segments = 2
bpy.context.view_layer.objects.active = ring_obj
bpy.ops.object.modifier_apply(modifier=chamf.name)

smooth_obj(ring_obj, 35.0)
set_mat(ring_obj, mat_orange)
print("Part 4: Accent Ring Orange created successfully.")

# =============================================================
# PART 5: 05_Button_Cap (Rear Push Button Cap)
# =============================================================
print("Constructing Part 5: Button Cap...")

btn_head = add_cyl("05_Button_Cap", r=3.0, h=4.0, loc=(0, 25.0, 24.0), rot=(math.radians(90), 0, 0), segs=32)
btn_stem = add_cyl("Button_Stem", r=1.6, h=5.0, loc=(0, 22.0, 24.0), rot=(math.radians(90), 0, 0), segs=24)
apply_bool(btn_head, btn_stem, operation='UNION')
btn_obj = btn_head
smooth_obj(btn_obj, 35.0)
set_mat(btn_obj, mat_orange)
print("Part 5: Button Cap created successfully.")

# =============================================================
# HARDWARE COMPONENT STUBS (FOR PHOTO-REALISTIC HERO RENDERS)
# =============================================================
print("Adding hardware sensors for visual fidelity in renders...")

# 1. PIR White Dome
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=11.2, location=(0, pir_y - 4.5, pir_z))
pir_dome_mesh = bpy.context.active_object
pir_dome_mesh.name = "Vis_PIR_Dome"
pir_dome_mesh.scale = (1.0, 0.72, 1.0)
pir_dome_mesh.rotation_euler = (ROT_X, 0, 0)
bpy.ops.object.transform_apply(scale=True, rotation=False)
smooth_obj(pir_dome_mesh, 35.0)
set_mat(pir_dome_mesh, mat_pir)

# 2. HC-SR04 Metal Transducer Cans
vis_parts = [pir_dome_mesh]
for eye_x in [-13.0, 13.0]:
    can = add_cyl(f"Vis_Can_{eye_x}", r=8.0, h=6.5, loc=(eye_x, hc_y - 2.5, hc_z), rot=(ROT_X, 0, 0), segs=48)
    smooth_obj(can, 30.0)
    set_mat(can, mat_metal)
    mesh_in = add_cyl(f"Vis_Mesh_{eye_x}", r=6.6, h=6.6, loc=(eye_x, hc_y - 2.6, hc_z), rot=(ROT_X, 0, 0), segs=48)
    smooth_obj(mesh_in, 30.0)
    set_mat(mesh_in, mat_mesh)
    vis_parts.extend([can, mesh_in])

# 3. 3x Status LEDs in Front Neck Ports
led_colors = [(76.0, mat_led_g, "Vis_LED_Green"), (62.0, mat_led_b, "Vis_LED_Blue"), (48.0, mat_led_r, "Vis_LED_Red")]
for z_pos, m_led, led_name in led_colors:
    led_bulb = add_cyl(led_name, r=1.5, h=3.0, loc=(0, -3.8, z_pos), rot=(math.radians(90), 0, 0), segs=24)
    smooth_obj(led_bulb, 25.0)
    set_mat(led_bulb, m_led)
    vis_parts.append(led_bulb)

# =============================================================
# EXPORT PRODUCTION STLS (LOCAL ORIGINS AT Z=0 FOR BAMBU STUDIO)
# =============================================================
print("Exporting individual production STLs centered and flat at Z=0 for Bambu Studio...")

printable_components = [
    (base_obj,      "01_Base_Pedestal.stl",         (0, 0, 0)),
    (head_neck_obj, "02_Neck_and_Head_Pod.stl",     (0, 0, -25.5)), # Tenon bottom rests flat on bed
    (face_obj,      "03_Sensor_Faceplate_Black.stl", None),          # Lay flat
    (ring_obj,      "04_Accent_Ring_Orange.stl",     None),          # Lay flat
    (btn_obj,       "05_Button_Cap.stl",             None)           # Lay flat
]

for obj, filename, trans in printable_components:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.duplicate()
    exp_obj = bpy.context.active_object
    
    if "Faceplate" in filename or "Accent_Ring" in filename:
        exp_obj.rotation_euler = (0, 0, 0)
        bpy.ops.object.transform_apply(rotation=True)
        min_z = min([exp_obj.matrix_world @ v.co for v in exp_obj.data.vertices], key=lambda c: c.z).z
        exp_obj.location.z -= min_z
        bpy.ops.object.transform_apply(location=True)
    elif "Button" in filename:
        exp_obj.rotation_euler = (0, 0, 0)
        bpy.ops.object.transform_apply(rotation=True)
        min_z = min([exp_obj.matrix_world @ v.co for v in exp_obj.data.vertices], key=lambda c: c.z).z
        exp_obj.location.z -= min_z
        bpy.ops.object.transform_apply(location=True)
    elif trans:
        exp_obj.location = (exp_obj.location.x + trans[0], exp_obj.location.y + trans[1], exp_obj.location.z + trans[2])
        bpy.ops.object.transform_apply(location=True)
        min_z = min([exp_obj.matrix_world @ v.co for v in exp_obj.data.vertices], key=lambda c: c.z).z
        if abs(min_z) > 0.001:
            exp_obj.location.z -= min_z
            bpy.ops.object.transform_apply(location=True)

    stl_path = os.path.join(STL_DIR, filename)
    root_stl = os.path.join(OUTPUT_DIR, filename)
    bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True)
    bpy.ops.wm.stl_export(filepath=root_stl, export_selected_objects=True)
    print(f"Exported: {filename}")
    bpy.data.objects.remove(exp_obj, do_unlink=True)

# Export Complete Assembled STL & OBJ
bpy.ops.object.select_all(action='DESELECT')
for p in [base_obj, head_neck_obj, face_obj, ring_obj, btn_obj]:
    p.select_set(True)

asm_stl = os.path.join(OUTPUT_DIR, "StudySense_V6_Pro_Complete_Assembly.stl")
bpy.ops.wm.stl_export(filepath=asm_stl, export_selected_objects=True)
asm_obj = os.path.join(OUTPUT_DIR, "StudySense_V6_Pro_Complete_Assembly.obj")
bpy.ops.wm.obj_export(filepath=asm_obj, export_selected_objects=True)
print(f"Exported complete assemblies: {asm_stl}")

# Save master .blend file
blend_path = os.path.join(OUTPUT_DIR, "StudySense_V6_Pro.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"Saved master project: {blend_path}")

print("=== StudySense V6 Pro Generation Complete! ===")
