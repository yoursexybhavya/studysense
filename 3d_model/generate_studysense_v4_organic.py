import bpy
import bmesh
import math
import os

print("=== Generating StudySense V4.2 Perfect Organic CAD (Reference Parity) ===")

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
    bg_node.inputs['Color'].default_value = (0.93, 0.94, 0.96, 1.0)
    bg_node.inputs['Strength'].default_value = 1.0

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
STL_DIR = os.path.join(OUTPUT_DIR, "v4_organic_stl")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STL_DIR, exist_ok=True)

# -------------------------------------------------------------
# Color & Material Palette (Exact Reference Match)
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
        mod.solver = 'FAST'
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
    """Generates a high-precision rounded rectangular prism with bmesh."""
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
    """Generates a lofted tapered capsule column for the organic neck."""
    bm = bmesh.new()
    # Bottom loop
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
    
    # Top loop
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
    
    # Bottom face
    bm.faces.new(verts_b)
    # Top face
    bm.faces.new(reversed(verts_t))
    # Side quads
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
# GEOMETRIC PARAMETERS & POSTURE ALIGNMENT
# -------------------------------------------------------------
TILT_DEG = 7.0
TILT_RAD = math.radians(TILT_DEG)
ROT_X = math.radians(90.0 + TILT_DEG)

HEAD_RADIUS = 36.0  # 72mm Outer Diameter (Silky circular pod)
HEAD_DEPTH = 30.0   # 30mm depth
HEAD_Z = 146.0      # Center of circular head
HEAD_Y = 2.0        # Center Y

# Position of the front faceplate
FRONT_OFFSET = HEAD_DEPTH / 2.0 # 15mm forward along local Z
FACE_Y = HEAD_Y - FRONT_OFFSET * math.cos(TILT_RAD)
FACE_Z = HEAD_Z - FRONT_OFFSET * math.sin(TILT_RAD)

print(f"Pod Center: (0, {HEAD_Y}, {HEAD_Z}) | Front Face: (0, {FACE_Y:.2f}, {FACE_Z:.2f})")

# =============================================================
# PART 1: 01_Base_Pedestal (Organic L-Shaped Foot with Logo)
# =============================================================
print("Constructing Part 1: Base Pedestal...")

# 1. Front Pedestal Body (W: 60mm at bottom tapering to 52mm at top, D: 36mm, H: 36mm)
base_front = add_rounded_box("Base_Front", w=60.0, d=36.0, h=36.0, r=6.0, segs=12, loc=(0, 6.0, 0))

# Side taper cutter to taper front pedestal from 60mm to 52mm at top
base_taper_l = add_cube("Base_Tap_L", (20.0, 50.0, 45.0), loc=(-36.0, 6.0, 18.0), rot=(0, math.radians(6.5), 0))
apply_bool(base_front, base_taper_l, operation='DIFFERENCE')
base_taper_r = add_cube("Base_Tap_R", (20.0, 50.0, 45.0), loc=(36.0, 6.0, 18.0), rot=(0, math.radians(-6.5), 0))
apply_bool(base_front, base_taper_r, operation='DIFFERENCE')

# 2. Rear Foot Extension (W: 46mm, D: 46mm, H: 14mm, R: 8mm)
# Total footprint depth = 36mm + 46mm = 82mm
base_foot = add_rounded_box("Base_Foot", w=46.0, d=46.0, h=14.0, r=8.0, segs=12, loc=(0, 46.0, 0))
apply_bool(base_front, base_foot, operation='UNION')
base_obj = base_front
base_obj.name = "01_Base_Pedestal"

# 3. 15-degree sloping front ramp (Display face for logo)
ramp = add_cube("Ramp_Cutter", (80.0, 24.0, 60.0), loc=(0, -18.5, 22.0), rot=(math.radians(15), 0, 0))
apply_bool(base_obj, ramp, operation='DIFFERENCE')

# 4. Internal ESP32 & Wiring Chamber (Hollowed from bottom)
cavity = add_rounded_box("Base_Internal_Chamber", w=38.0, d=64.0, h=28.0, r=4.0, segs=8, loc=(0, 32.0, 0))
apply_bool(base_obj, cavity, operation='DIFFERENCE')

# ESP32 Cradle Rails (Holds board snugly at Z=2.0mm above bottom plate)
rail_l = add_cube("Rail_L", (4.0, 50.0, 4.0), loc=(-14.0, 36.0, 4.0))
apply_bool(base_obj, rail_l, operation='UNION')
rail_r = add_cube("Rail_R", (4.0, 50.0, 4.0), loc=(14.0, 36.0, 4.0))
apply_bool(base_obj, rail_r, operation='UNION')

# 5. Rear USB Port Opening (12.5mm x 7.0mm at Y=70mm, Z=7.0mm)
usb_cut = add_rounded_box("USB_Port", w=12.5, d=20.0, h=7.0, r=1.5, segs=6, loc=(0, 65.0, 3.5))
apply_bool(base_obj, usb_cut, operation='DIFFERENCE')

# 6. Rear Push Button Mount Hole (Ø6.5mm on rear transition at Y=24mm, Z=26mm)
btn_cut = add_cyl("Btn_Hole", r=3.25, h=25.0, loc=(0, 24.0, 26.0), rot=(math.radians(90), 0, 0), segs=32)
apply_bool(base_obj, btn_cut, operation='DIFFERENCE')

# 7. Top Mating Socket for Neck Docking (W: 34.5mm, D: 21.5mm, Depth: 8.0mm at Z=28 to 36)
socket_cut = add_rounded_box("Neck_Socket", w=34.5, d=21.5, h=10.0, r=4.0, segs=8, loc=(0, 6.0, 28.0))
apply_bool(base_obj, socket_cut, operation='DIFFERENCE')

# Wire through-hole connecting socket directly to internal chamber
wire_hole = add_cube("Wire_Through_Hole", (20.0, 12.0, 15.0), loc=(0, 6.0, 22.0))
apply_bool(base_obj, wire_hole, operation='DIFFERENCE')

# Snap Detent Grooves inside socket
snap_groove_l = add_cube("Snap_G_L", (1.4, 7.0, 2.0), loc=(-17.2, 6.0, 32.0))
apply_bool(base_obj, snap_groove_l, operation='DIFFERENCE')
snap_groove_r = add_cube("Snap_G_R", (1.4, 7.0, 2.0), loc=(17.2, 6.0, 32.0))
apply_bool(base_obj, snap_groove_r, operation='DIFFERENCE')

# 8. Embossed StudySense Logo on sloped front face
# Front ramp face is at Y ~ -8.2mm (Z=22) and Y ~ -10.2mm (Z=14)
# Halo ring at Z=22mm
logo_ring = add_cyl("Logo_Ring", r=6.0, h=1.4, loc=(0, -8.2, 22.0), rot=(math.radians(105), 0, 0), segs=48)
logo_hole = add_cyl("Logo_Ring_Hole", r=3.6, h=2.5, loc=(0, -8.2, 22.0), rot=(math.radians(105), 0, 0), segs=48)
apply_bool(logo_ring, logo_hole, operation='DIFFERENCE')

# Stylized 'S' core loop at Z=14mm
logo_s_outer = add_cyl("Logo_S_Outer", r=4.4, h=1.4, loc=(0, -10.2, 14.0), rot=(math.radians(105), 0, 0), segs=48)
logo_s_inner = add_cyl("Logo_S_Inner", r=2.4, h=2.5, loc=(0, -10.2, 14.0), rot=(math.radians(105), 0, 0), segs=48)
apply_bool(logo_s_outer, logo_s_inner, operation='DIFFERENCE')
apply_bool(logo_ring, logo_s_outer, operation='UNION')
apply_bool(base_obj, logo_ring, operation='UNION')

# Bottom Plate Snap Grooves (4 corner clips)
for bx, by in [(-16.0, 6.0), (16.0, 6.0), (-14.0, 56.0), (14.0, 56.0)]:
    clip_slot = add_cube(f"Clip_Slot_{bx}_{by}", (2.8, 2.8, 2.0), loc=(bx, by, 1.0))
    apply_bool(base_obj, clip_slot, operation='DIFFERENCE')

smooth_obj(base_obj, 35.0)
set_mat(base_obj, mat_white)
print("Part 1: Base Pedestal created successfully.")

# =============================================================
# PART 2: 02_Neck_and_Head_Pod (Organic Unified Upper Assembly)
# =============================================================
print("Constructing Part 2: Neck and Head Pod...")

# 1. Circular Head Pod Outer Cylinder (OD: 72mm, Depth: 30mm)
head_pod = add_cyl("Head_Outer", r=HEAD_RADIUS, h=HEAD_DEPTH, loc=(0, HEAD_Y, HEAD_Z), rot=(ROT_X, 0, 0), segs=96)

# 2. Smooth Spherical Dome Back
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=HEAD_RADIUS, location=(0, HEAD_Y + 5.0, HEAD_Z))
dome = bpy.context.active_object
dome.name = "Dome_Back"
dome.scale = (1.0, 0.42, 1.0)
bpy.ops.object.transform_apply(scale=True)
apply_bool(head_pod, dome, operation='UNION')

# 3. Top Stalk / Fin (The iconic handle/antenna feature on top rear - fully visible in hero views)
# Placed high enough to peek elegantly over the top rim of the head pod
fin = add_rounded_box("Top_Fin", w=16.0, d=10.0, h=38.0, r=4.8, segs=12, 
                      loc=(0, HEAD_Y + 9.5, HEAD_Z + 24.0), rot=(math.radians(14), 0, 0))
apply_bool(head_pod, fin, operation='UNION')

# 4. Organic Tapered Neck Stem (Lofted from Z=36 to Z=116)
# Bottom: W=36mm, D=22mm. Top: W=28mm, D=20mm (Smooth upward draft)
neck_h = 78.0 # Z=36 to 114
neck = add_tapered_capsule_column("Neck_Stem", w_bot=36.0, d_bot=22.0, w_top=28.0, d_top=20.0, 
                                  h=neck_h, r_bot=5.5, r_top=4.5, segs=12, loc=(0, 6.0, 36.0))

# Union Neck with Head Pod
apply_bool(neck, head_pod, operation='UNION')
head_neck_obj = neck
head_neck_obj.name = "02_Neck_and_Head_Pod"

# 5. Hollow Wire Conduit through Neck (16.0mm x 11.0mm)
# Leaves solid 3.0mm front, side, and rear walls!
conduit = add_rounded_box("Wire_Conduit", w=16.0, d=11.0, h=neck_h + 16.0, r=2.5, segs=6, loc=(0, 7.5, 34.0))
apply_bool(head_neck_obj, conduit, operation='DIFFERENCE')

# Internal head cavity connection
conduit_head = add_cube("Conduit_Head", (16.0, 12.0, 24.0), loc=(0, 5.0, 114.0))
apply_bool(head_neck_obj, conduit_head, operation='DIFFERENCE')

# 6. Head Pod Interior Sensor Chamber (Diameter: 56mm, Depth: 20mm)
head_interior = add_cyl("Head_Chamber", r=28.0, h=20.0, loc=(0, HEAD_Y - 1.5, HEAD_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(head_neck_obj, head_interior, operation='DIFFERENCE')

# 7. Front Recesses for Faceplate Assembly:
# Recess 1: Orange Accent Ring Lip (Ø66.8mm, Depth: 2.2mm)
ring_recess = add_cyl("Ring_Lip", r=33.4, h=3.0, loc=(0, FACE_Y + 0.6, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(head_neck_obj, ring_recess, operation='DIFFERENCE')

# Recess 2: Black Faceplate Rim (Ø61.4mm, Depth: 4.2mm)
face_recess = add_cyl("Face_Rim", r=30.7, h=5.0, loc=(0, FACE_Y + 1.2, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(head_neck_obj, face_recess, operation='DIFFERENCE')

# 8. 3x Status LED Mounting Holes on Front Neck Face (Ø3.2mm clean holes with Ø5.0mm counterbore)
# Green (Z=94mm - Study Mode), Blue (Z=80mm - Break Mode), Red (Z=66mm - Posture Alert)
for z_led in [94.0, 80.0, 66.0]:
    led_h = add_cyl(f"LED_Thru_{z_led}", r=1.6, h=10.0, loc=(0, -4.0, z_led), rot=(math.radians(90), 0, 0), segs=32)
    apply_bool(head_neck_obj, led_h, operation='DIFFERENCE')
    led_cb = add_cyl(f"LED_CB_{z_led}", r=2.5, h=6.0, loc=(0, 1.5, z_led), rot=(math.radians(90), 0, 0), segs=32)
    apply_bool(head_neck_obj, led_cb, operation='DIFFERENCE')

# 9. Lower Male Mounting Tenon (Docks into Base Socket at Z=30 to 36mm)
tenon = add_rounded_box("Neck_Tenon", w=33.8, d=20.8, h=7.5, r=3.8, segs=8, loc=(0, 6.0, 28.5))
tenon_hol = add_cube("Tenon_Hollow", (18.0, 11.0, 12.0), loc=(0, 6.0, 28.5))
apply_bool(tenon, tenon_hol, operation='DIFFERENCE')

snap_l = add_cube("Snap_L", (1.2, 6.0, 1.8), loc=(-16.8, 6.0, 32.0))
apply_bool(tenon, snap_l, operation='UNION')
snap_r = add_cube("Snap_R", (1.2, 6.0, 1.8), loc=(16.8, 6.0, 32.0))
apply_bool(tenon, snap_r, operation='UNION')

apply_bool(head_neck_obj, tenon, operation='UNION')

# Internal sensor support ledges inside head cavity
shelf_hc = add_cube("Shelf_HC", (45.0, 10.0, 2.5), loc=(0, 1.0, HEAD_Z - 14.0), rot=(ROT_X, 0, 0))
shelf_hc_hol = add_cube("Shelf_HC_Hol", (30.0, 12.0, 4.0), loc=(0, 1.0, HEAD_Z - 14.0), rot=(ROT_X, 0, 0))
apply_bool(shelf_hc, shelf_hc_hol, operation='DIFFERENCE')
apply_bool(head_neck_obj, shelf_hc, operation='UNION')

shelf_pir = add_cube("Shelf_PIR", (32.0, 10.0, 2.5), loc=(0, 1.0, HEAD_Z + 14.0), rot=(ROT_X, 0, 0))
shelf_pir_hol = add_cube("Shelf_PIR_Hol", (20.0, 12.0, 4.0), loc=(0, 1.0, HEAD_Z + 14.0), rot=(ROT_X, 0, 0))
apply_bool(shelf_pir, shelf_pir_hol, operation='DIFFERENCE')
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
# PART 5: 05_Base_Bottom_Plate (Snap-in Service Cover)
# =============================================================
print("Constructing Part 5: Base Bottom Plate...")

bot_plate = add_rounded_box("05_Base_Bottom_Plate", w=37.4, d=63.4, h=2.0, r=3.8, segs=8, loc=(0, 32.0, 0))

# 4 Rubber non-slip foot pockets (Ø8.0mm x 0.8mm deep)
for fx, fy in [(-12.0, 8.0), (12.0, 8.0), (-12.0, 54.0), (12.0, 54.0)]:
    pocket = add_cyl(f"Foot_Pocket_{fx}_{fy}", r=4.0, h=1.4, loc=(fx, fy, 0.4), segs=32)
    apply_bool(bot_plate, pocket, operation='DIFFERENCE')

# 4 Perimeter snap tabs matching base slots
for bx, by in [(-16.0, 6.0), (16.0, 6.0), (-14.0, 56.0), (14.0, 56.0)]:
    tab = add_cube(f"Bot_Tab_{bx}_{by}", (2.4, 2.4, 1.8), loc=(bx, by, 1.7))
    apply_bool(bot_plate, tab, operation='UNION')

smooth_obj(bot_plate, 35.0)
set_mat(bot_plate, mat_white)
print("Part 5: Base Bottom Plate created successfully.")

# =============================================================
# PART 6: 06_Button_Cap (Rear Reset / Timer Button Cap)
# =============================================================
print("Constructing Part 6: Button Cap...")

btn_cap = add_cyl("06_Button_Cap", r=3.0, h=4.5, loc=(0, 24.0, 26.0), rot=(math.radians(90), 0, 0), segs=32)
btn_top = add_cyl("Btn_Top", r=3.5, h=1.5, loc=(0, 21.5, 26.0), rot=(math.radians(90), 0, 0), segs=32)
apply_bool(btn_cap, btn_top, operation='UNION')
smooth_obj(btn_cap, 35.0)
set_mat(btn_cap, mat_orange)
print("Part 6: Button Cap created successfully.")

# -------------------------------------------------------------
# MOCK HARDWARE MOCKUPS (For Photorealistic Hero Renders)
# -------------------------------------------------------------
preview_hardware = []

# 1. PIR Geodesic Dome (White faceted hemisphere)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=11.2, location=(0, pir_y - 2.5, pir_z))
pir_dome = bpy.context.active_object
pir_dome.name = "Mock_PIR_Dome"
pir_dome.rotation_euler = (ROT_X, 0, 0)
set_mat(pir_dome, mat_pir)
preview_hardware.append(pir_dome)

# 2. HC-SR04 Ultrasonic Transducers (Dual aluminum cans + black mesh)
for eye_x in [-13.0, 13.0]:
    can = add_cyl(f"Mock_Eye_Can_{eye_x}", r=7.95, h=12.0, loc=(eye_x, hc_y - 2.0, hc_z), rot=(ROT_X, 0, 0), segs=48)
    smooth_obj(can, 35.0)
    set_mat(can, mat_metal)
    preview_hardware.append(can)
    mesh_disc = add_cyl(f"Mock_Mesh_{eye_x}", r=7.0, h=0.4, loc=(eye_x, hc_y - 7.9, hc_z), rot=(ROT_X, 0, 0), segs=48)
    set_mat(mesh_disc, mat_mesh)
    preview_hardware.append(mesh_disc)

# Blue PCB background visible through crystal slot
pcb_rect = add_cube("Mock_Blue_PCB", (44.0, 1.6, 20.0), loc=(0, hc_y + 2.5, hc_z), rot=(ROT_X, 0, 0))
set_mat(pcb_rect, mat_pcb)
preview_hardware.append(pcb_rect)

# 3 Glowing Status LEDs on Neck (Green, Blue, Red)
led_preview_data = [(94.0, mat_led_g, "Green"), (80.0, mat_led_b, "Blue"), (66.0, mat_led_r, "Red")]
for z_led, l_mat, cname in led_preview_data:
    led_bead = add_cyl(f"Mock_LED_{cname}", r=1.55, h=2.0, loc=(0, -4.0, z_led), rot=(math.radians(90), 0, 0), segs=32)
    set_mat(led_bead, l_mat)
    preview_hardware.append(led_bead)

# Studio Desk Surface & Desk Mat (Matching Reference Photo)
desk = add_cube("Mock_Studio_Desk", (450.0, 360.0, 14.0), loc=(0, 35.0, -7.0))
set_mat(desk, mat_desk)
preview_hardware.append(desk)

desk_pad = add_rounded_box("Mock_Desk_Mat", w=260.0, d=210.0, h=2.5, r=12.0, segs=12, loc=(0, 30.0, 0.0))
set_mat(desk_pad, mat_pad)
preview_hardware.append(desk_pad)

# -------------------------------------------------------------
# LIGHTING & CAMERA SETUP (Calibrated to Reference Photo)
# -------------------------------------------------------------
cam_target = bpy.data.objects.new("Cam_Target", None)
scene.collection.objects.link(cam_target)
cam_target.location = (0, 8.0, 105.0)

def add_sun(name, energy, rot):
    sd = bpy.data.lights.new(name=name, type='SUN')
    sd.energy = energy
    so = bpy.data.objects.new(name=name, object_data=sd)
    scene.collection.objects.link(so)
    so.rotation_euler = rot
    return so

add_sun("Key_Sun", 5.2, (math.radians(50), math.radians(15), math.radians(-35)))
add_sun("Fill_Sun", 2.6, (math.radians(35), math.radians(-25), math.radians(45)))
add_sun("Rim_Sun", 3.2, (math.radians(-45), math.radians(20), math.radians(170)))

cam_data = bpy.data.cameras.new(name="Main_Camera")
cam_data.lens = 62.0
cam = bpy.data.objects.new(name="Main_Camera", object_data=cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

track = cam.constraints.new(type='TRACK_TO')
track.target = cam_target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

# Hero Isometric View (Exact framing of media_1795442319940_ec56b73f.jpg)
cam.location = (-170.0, -290.0, 160.0)
scene.render.resolution_x = 1920
scene.render.resolution_y = 1920
scene.render.engine = 'BLENDER_EEVEE'

# Save Blender Project
blend_file = os.path.join(OUTPUT_DIR, "StudySense_V4_Organic.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_file)
print(f"Saved Blender Project: {blend_file}")

# Render Hero Shot
hero_png = os.path.join(OUTPUT_DIR, "render_v4_isometric_hero.png")
scene.render.filepath = hero_png
try:
    print(f"Rendering Hero View -> {hero_png}...")
    bpy.ops.render.render(write_still=True)
    print("Hero render complete!")
except Exception as e:
    print(f"Render warning: {e}")

# Render Front View
cam.location = (0.0, -360.0, 105.0)
front_png = os.path.join(OUTPUT_DIR, "render_v4_front_view.png")
scene.render.filepath = front_png
try:
    bpy.ops.render.render(write_still=True)
    print("Front render complete!")
except Exception as e:
    print(f"Front render warning: {e}")

# Render Rear View
cam.location = (0.0, 360.0, 105.0)
rear_png = os.path.join(OUTPUT_DIR, "render_v4_rear_view.png")
scene.render.filepath = rear_png
try:
    bpy.ops.render.render(write_still=True)
    print("Rear render complete!")
except Exception as e:
    print(f"Rear render warning: {e}")

# =============================================================
# EXPORT PRODUCTION STLS (Bambu Studio Optimized: Centered & Flat on Bed)
# =============================================================
print("--- Exporting Production STLs with Normalized Coordinates for Bambu Studio ---")

production_parts = [
    "01_Base_Pedestal",
    "02_Neck_and_Head_Pod",
    "03_Sensor_Faceplate_Black",
    "04_Accent_Ring_Orange",
    "05_Base_Bottom_Plate",
    "06_Button_Cap"
]

# Export Assembled STL (In-situ for 3D viewers)
for obj in bpy.context.scene.objects: obj.select_set(obj.name in production_parts)
full_stl = os.path.join(OUTPUT_DIR, "StudySense_V4_Complete_Assembly.stl")
bpy.ops.wm.stl_export(filepath=full_stl, export_selected_objects=True)
print(f"Exported Complete Assembly: {full_stl}")

# Export each part individually, centered at (X=0, Y=0) and resting on Z=0
for name in production_parts:
    obj = bpy.data.objects.get(name)
    if not obj:
        continue
    
    dup_obj = obj.copy()
    dup_obj.data = obj.data.copy()
    scene.collection.objects.link(dup_obj)
    
    # Apply all existing transforms first to flatten world transforms
    bpy.context.view_layer.objects.active = dup_obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    if "03_Sensor_Faceplate" in name or "04_Accent_Ring" in name:
        dup_obj.rotation_euler = (0, 0, 0)
        bpy.ops.object.transform_apply(rotation=True)
    
    min_x = min([v.co.x for v in dup_obj.data.vertices])
    max_x = max([v.co.x for v in dup_obj.data.vertices])
    min_y = min([v.co.y for v in dup_obj.data.vertices])
    max_y = max([v.co.y for v in dup_obj.data.vertices])
    min_z = min([v.co.z for v in dup_obj.data.vertices])
    
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    
    for v in dup_obj.data.vertices:
        v.co.x -= cx
        v.co.y -= cy
        v.co.z -= min_z
    dup_obj.data.update()
    
    for o in scene.objects: o.select_set(False)
    dup_obj.select_set(True)
    bpy.context.view_layer.objects.active = dup_obj
    
    stl_path = os.path.join(STL_DIR, f"{name}.stl")
    root_stl_path = os.path.join(OUTPUT_DIR, f"{name}.stl")
    bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True)
    bpy.ops.wm.stl_export(filepath=root_stl_path, export_selected_objects=True)
    
    z_height = round(max([v.co.z for v in dup_obj.data.vertices]), 1)
    w_x = round(max_x - min_x, 1)
    d_y = round(max_y - min_y, 1)
    print(f" -> Exported {name}.stl: Centered (0,0), Dim=[{w_x} x {d_y} x {z_height}mm]")
    
    bpy.data.objects.remove(dup_obj, do_unlink=True)

print("=== StudySense V4.0 CAD Generation Completed Successfully! ===")
