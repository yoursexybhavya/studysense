import bpy
import bmesh
import math
import os

print("=== Generating Upgraded StudySense CAD Geometry v3.0 ===")

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001 # 1 mm

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"

def make_mat(name, color, roughness=0.35, metallic=0.0, emission=None, emission_strength=1.0):
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

mat_white  = make_mat("Matte_White",  (0.96, 0.96, 0.98, 1.0), roughness=0.25)
mat_black  = make_mat("Matte_Black",  (0.04, 0.04, 0.05, 1.0), roughness=0.45)
mat_orange = make_mat("Accent_Orange", (0.98, 0.28, 0.02, 1.0), roughness=0.20)
mat_metal  = make_mat("Metal_Silver", (0.85, 0.85, 0.88, 1.0), roughness=0.15, metallic=0.9)
mat_mesh   = make_mat("Mesh_Dark",    (0.03, 0.03, 0.03, 1.0), roughness=0.6)
mat_pir    = make_mat("PIR_Dome",     (0.96, 0.96, 1.0, 1.0),  roughness=0.15)
mat_desk   = make_mat("Desk_Wood",    (0.68, 0.50, 0.32, 1.0), roughness=0.5)
mat_mat    = make_mat("Desk_Pad",     (0.12, 0.14, 0.18, 1.0), roughness=0.8)

mat_led_g  = make_mat("LED_G", (0.1, 0.95, 0.3, 1.0), roughness=0.1, emission=(0.1, 0.95, 0.3, 1.0), emission_strength=6.0)
mat_led_b  = make_mat("LED_B", (0.15, 0.5, 0.98, 1.0), roughness=0.1, emission=(0.15, 0.5, 0.98, 1.0), emission_strength=6.0)
mat_led_r  = make_mat("LED_R", (0.98, 0.08, 0.12, 1.0), roughness=0.1, emission=(0.98, 0.08, 0.12, 1.0), emission_strength=6.0)

def set_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

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

def add_cyl(name, r, h, loc=(0,0,0), rot=(0,0,0), segs=64):
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

# -------------------------------------------------------------
# GEOMETRY ENGINE: KEY COORDINATES
# -------------------------------------------------------------
# Head center: X = 0, Y = 0, Z = 152.0 mm
# Head tilt: 7 degrees tilted backwards (rot_x = 97 degrees)
HEAD_Z = 152.0
HEAD_Y = 0.0
TILT_DEG = 7.0
TILT_RAD = math.radians(TILT_DEG)
ROT_X = math.radians(90.0 + TILT_DEG)

HEAD_RADIUS = 37.0 # 74mm OD
HEAD_DEPTH = 32.0  # 32mm deep cylinder
FRONT_OFFSET = HEAD_DEPTH / 2.0 # 16mm forward along local axis

# Front face center of head pod:
# Local Z is tilted: forward displacement is (-16*sin(7), -16*cos(7))
FACE_Y = HEAD_Y - FRONT_OFFSET * math.cos(TILT_RAD) # ~ -15.88mm
FACE_Z = HEAD_Z - FRONT_OFFSET * math.sin(TILT_RAD) # ~ 150.05mm

print(f"Head Center: Y={HEAD_Y}, Z={HEAD_Z} | Front Face: Y={FACE_Y:.2f}, Z={FACE_Z:.2f}")

# 1. HEAD CUP (Outer cylinder)
head_cyl = add_cyl("Head_Cyl", r=HEAD_RADIUS, h=HEAD_DEPTH, loc=(0, HEAD_Y, HEAD_Z), rot=(ROT_X, 0, 0), segs=96)

# Head rear spherical dome cap (for beautiful organic curve on back)
head_dome = bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=HEAD_RADIUS, location=(0, HEAD_Y + 5.0, HEAD_Z))
dome_obj = bpy.context.active_object
dome_obj.scale = (1.0, 0.45, 1.0)
bpy.ops.object.transform_apply(scale=True)
apply_bool(head_cyl, dome_obj, operation='UNION')

# Hollow out the head cup from the front (leaves 3.2mm walls)
# Cavity depth 28mm, radius 33.8mm
head_cavity = add_cyl("Head_Cavity", r=33.8, h=28.0, loc=(0, HEAD_Y - 2.5, HEAD_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(head_cyl, head_cavity, operation='DIFFERENCE')

# Top rear handle / acoustic fin (tilted back 15 deg)
fin = add_cube("Top_Fin", (18.0, 10.0, 24.0), loc=(0, 10.0, HEAD_Z + 38.0), rot=(math.radians(15), 0, 0))
fin_bev = fin.modifiers.new(name="Bevel", type='BEVEL')
fin_bev.width = 3.0
fin_bev.segments = 4
bpy.context.view_layer.objects.active = fin
bpy.ops.object.modifier_apply(modifier=fin_bev.name)
apply_bool(head_cyl, fin, operation='UNION')

# 2. VERTICAL TAPERED NECK
# Crucial: Neck front must be BEHIND the head front!
# Neck top is at Z=122, connects to underside of head (bottom of head is at Z = 152 - 37 = 115)
# Neck front face is at Y = -4.0 (Head front is at Y = -16.0! A 12mm proud step-back!)
neck_h = 82.0 # From Z=40 to Z=122
neck_z = 40.0 + neck_h/2.0 # Z=81.0
neck = add_cube("Neck", (36.0, 26.0, neck_h), loc=(0, 6.0, neck_z))

# Taper neck width from 38mm at base down to 26mm at head
taper_l = add_cube("Taper_L", (20.0, 40.0, 95.0), loc=(-26.0, 6.0, neck_z), rot=(0, math.radians(4.2), 0))
apply_bool(neck, taper_l, operation='DIFFERENCE')
taper_r = add_cube("Taper_R", (20.0, 40.0, 95.0), loc=(26.0, 6.0, neck_z), rot=(0, math.radians(-4.2), 0))
apply_bool(neck, taper_r, operation='DIFFERENCE')

# Gentle backward slope on neck front face (7 degrees)
neck_incline = add_cube("Neck_Incline", (50.0, 20.0, 95.0), loc=(0, -17.0, neck_z), rot=(math.radians(7), 0, 0))
apply_bool(neck, neck_incline, operation='DIFFERENCE')

# 3 LED Indicator holes on Neck front face (Green at Z=96, Blue at Z=82, Red at Z=68)
for z_led in [96.0, 82.0, 68.0]:
    # LED hole Ø5.2mm
    led_h = add_cyl(f"LED_H_{z_led}", r=2.6, h=25.0, loc=(0, -12.0, z_led), rot=(math.radians(97), 0, 0), segs=32)
    apply_bool(neck, led_h, operation='DIFFERENCE')
    # Counterbore Ø6.4mm
    cb = add_cyl(f"LED_CB_{z_led}", r=3.2, h=10.0, loc=(0, -3.0, z_led), rot=(math.radians(97), 0, 0), segs=32)
    apply_bool(neck, cb, operation='DIFFERENCE')

# Hollow conduit inside neck for 11cm wire harness
wire_duct = add_cube("Wire_Duct", (18.0, 14.0, neck_h + 10.0), loc=(0, 6.0, neck_z))
apply_bool(neck, wire_duct, operation='DIFFERENCE')

# Union Neck with Head Cup
apply_bool(neck, head_cyl, operation='UNION')
head_neck_obj = neck
head_neck_obj.name = "02_Neck_and_Head_Shell"

# Open duct between neck and head cavity
duct_head = add_cube("Duct_Head", (18.0, 14.0, 25.0), loc=(0, 3.0, 122.0))
apply_bool(head_neck_obj, duct_head, operation='DIFFERENCE')

# Female snap socket at bottom of neck (Z=40 to 45)
socket = add_cube("Socket", (32.8, 25.0, 6.0), loc=(0, 6.0, 42.5))
apply_bool(head_neck_obj, socket, operation='DIFFERENCE')

set_mat(head_neck_obj, mat_white)

# -------------------------------------------------------------
# 3. BASE LOWER STAND
# -------------------------------------------------------------
# Base front: 74mm wide, 46mm deep, 40mm high (Z=0 to 40)
base_main = add_cube("Base_Main", (74.0, 48.0, 40.0), loc=(0, 6.0, 20.0))

# Rear foot extension (for stability): 50mm wide, 46mm deep, 16mm high (Z=0 to 16)
base_foot = add_cube("Base_Foot", (50.0, 46.0, 16.0), loc=(0, 48.0, 8.0))
apply_bool(base_main, base_foot, operation='UNION')
base_obj = base_main
base_obj.name = "01_Base_Lower_Stand"

# Round exterior corners with bevel
bev = base_obj.modifiers.new(name="Bevel", type='BEVEL')
bev.width = 3.5
bev.segments = 4
bpy.context.view_layer.objects.active = base_obj
bpy.ops.object.modifier_apply(modifier=bev.name)

# Front ramp slope (14 degrees)
incline = add_cube("Base_Ramp", (85.0, 25.0, 60.0), loc=(0, -22.0, 24.0), rot=(math.radians(14), 0, 0))
apply_bool(base_obj, incline, operation='DIFFERENCE')

# Internal ESP32 & wiring cavity (solid 3mm floor)
base_cav = add_cube("Base_Cavity", (58.0, 72.0, 34.0), loc=(0, 26.0, 20.0))
apply_bool(base_obj, base_cav, operation='DIFFERENCE')

# ESP32 mounting bed
esp_bed = add_cube("ESP_Bed", (34.0, 56.0, 5.0), loc=(0, 34.0, 5.5))
apply_bool(base_obj, esp_bed, operation='UNION')
esp_pocket = add_cube("ESP_Pocket", (29.2, 53.0, 8.0), loc=(0, 34.0, 8.5))
apply_bool(base_obj, esp_pocket, operation='DIFFERENCE')

# Rear USB-C / Micro-USB port cutout (at Y=71mm, Z=8.5mm)
usb_slot = add_cube("USB_Slot", (13.5, 20.0, 8.0), loc=(0, 68.0, 8.5))
apply_bool(base_obj, usb_slot, operation='DIFFERENCE')

# Rear Push Button Cutout (GPIO 22) on rear stand slope (Z=28mm)
btn_h = add_cyl("Btn_Hole", r=3.5, h=25.0, loc=(0, 26.0, 28.0), rot=(math.radians(90), 0, 0))
apply_bool(base_obj, btn_h, operation='DIFFERENCE')

# Male mating collar at top of base (Z=40 to 45)
collar = add_cube("Base_Collar", (32.0, 24.2, 5.0), loc=(0, 6.0, 42.5))
apply_bool(base_obj, collar, operation='UNION')
collar_hol = add_cube("Collar_Hol", (24.0, 17.0, 12.0), loc=(0, 6.0, 42.5))
apply_bool(base_obj, collar_hol, operation='DIFFERENCE')

# Embossed StudySense Logo on front ramp
logo_ring = add_cyl("Logo_Ring", r=7.2, h=1.8, loc=(0, -14.2, 12.5), rot=(math.radians(104), 0, 0), segs=48)
logo_hole = add_cyl("Logo_Hole", r=4.5, h=2.5, loc=(0, -14.2, 12.5), rot=(math.radians(104), 0, 0), segs=48)
apply_bool(logo_ring, logo_hole, operation='DIFFERENCE')
logo_dot  = add_cyl("Logo_Dot", r=2.2, h=1.8, loc=(0, -14.2, 12.5), rot=(math.radians(104), 0, 0), segs=32)
apply_bool(logo_ring, logo_dot, operation='UNION')
apply_bool(base_obj, logo_ring, operation='UNION')

set_mat(base_obj, mat_white)

# -------------------------------------------------------------
# 4. SENSOR FACEPLATE (BLACK) & ACCENT RING (ORANGE)
# -------------------------------------------------------------
# Accent Ring (Orange): Outer radius 33.6mm, inner radius 30.6mm, thickness 2.5mm
ring = add_cyl("04_Accent_Ring_Orange", r=33.6, h=2.5, loc=(0, FACE_Y, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
ring_cut = add_cyl("Ring_Cut", r=30.6, h=8.0, loc=(0, FACE_Y, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(ring, ring_cut, operation='DIFFERENCE')
set_mat(ring, mat_orange)

# Sensor Faceplate (Black Disc): radius 30.4mm, thickness 2.4mm
face = add_cyl("03_Sensor_Faceplate_Black", r=30.4, h=2.4, loc=(0, FACE_Y, FACE_Z), rot=(ROT_X, 0, 0), segs=96)

# PIR Dome cutout: Ø23.4mm centered at local Z=+11.5mm
pir_z = FACE_Z + 11.5 * math.cos(TILT_RAD)
pir_y = FACE_Y - 11.5 * math.sin(TILT_RAD)
pir_hole = add_cyl("PIR_Cut", r=11.7, h=10.0, loc=(0, pir_y, pir_z), rot=(ROT_X, 0, 0), segs=64)
apply_bool(face, pir_hole, operation='DIFFERENCE')

# HC-SR04 Dual Eyes: 2x Ø16.3mm spaced 26mm apart at local Z=-11.0mm
hc_z = FACE_Z - 11.0 * math.cos(TILT_RAD)
hc_y = FACE_Y + 11.0 * math.sin(TILT_RAD)
for eye_x in [-13.0, 13.0]:
    eye_h = add_cyl(f"Eye_Cut_{eye_x}", r=8.15, h=10.0, loc=(eye_x, hc_y, hc_z), rot=(ROT_X, 0, 0), segs=64)
    apply_bool(face, eye_h, operation='DIFFERENCE')

# Center crystal bridge slot (7mm x 3.6mm)
slot = add_cube("Slot", (7.0, 8.0, 3.6), loc=(0, hc_y, hc_z), rot=(ROT_X, 0, 0))
apply_bool(face, slot, operation='DIFFERENCE')
set_mat(face, mat_black)

# -------------------------------------------------------------
# 5. BUTTON CAP
# -------------------------------------------------------------
btn_cap = add_cyl("05_Button_Cap", r=3.2, h=6.0, loc=(0, 27.0, 28.0), rot=(math.radians(90), 0, 0), segs=32)
btn_flange = add_cyl("Btn_Flange", r=4.5, h=1.5, loc=(0, 24.5, 28.0), rot=(math.radians(90), 0, 0), segs=32)
apply_bool(btn_cap, btn_flange, operation='UNION')
set_mat(btn_cap, mat_black)

# -------------------------------------------------------------
# PHOTOREALISTIC PREVIEW MOCKUPS (Sensors, LEDs, Tabletop)
# -------------------------------------------------------------
# PIR Dome
pir_dome = add_cyl("Mock_PIR_Dome", r=11.2, h=9.0, loc=(0, pir_y - 2.0, pir_z), rot=(ROT_X, 0, 0), segs=48)
set_mat(pir_dome, mat_pir)

# HC-SR04 Transducers
for eye_x in [-13.0, 13.0]:
    can = add_cyl(f"Mock_Can_{eye_x}", r=8.0, h=10.0, loc=(eye_x, hc_y - 1.0, hc_z), rot=(ROT_X, 0, 0), segs=48)
    set_mat(can, mat_metal)
    mesh = add_cyl(f"Mock_Mesh_{eye_x}", r=7.2, h=1.2, loc=(eye_x, hc_y - 5.5, hc_z), rot=(ROT_X, 0, 0), segs=48)
    set_mat(mesh, mat_mesh)

# 3 Glowing LEDs on Neck (Green, Blue, Red)
led_preview_data = [(96.0, mat_led_g), (82.0, mat_led_b), (68.0, mat_led_r)]
for z_led, led_mat in led_preview_data:
    led_bead = add_cyl(f"Mock_LED_{z_led}", r=2.5, h=4.0, loc=(0, -11.5, z_led), rot=(math.radians(97), 0, 0), segs=32)
    set_mat(led_bead, led_mat)

# Studio Desk & Mat
desk = add_cube("Desk", (350.0, 280.0, 12.0), loc=(0, 25.0, -6.0))
set_mat(desk, mat_desk)
pad = add_cube("Pad", (220.0, 180.0, 2.0), loc=(0, 20.0, 1.0))
set_mat(pad, mat_mat)

# Studio 3-Point Lighting
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
target.location = (0, 0, 95.0)

def add_sun(name, energy, rot):
    sd = bpy.data.lights.new(name=name, type='SUN')
    sd.energy = energy
    so = bpy.data.objects.new(name=name, object_data=sd)
    scene.collection.objects.link(so)
    so.rotation_euler = rot

add_sun("Key", 5.5, (math.radians(45), math.radians(20), math.radians(-35)))
add_sun("Fill", 2.8, (math.radians(35), math.radians(-30), math.radians(50)))
add_sun("Rim", 3.5, (math.radians(-50), math.radians(15), math.radians(170)))

if scene.world:
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.92, 0.94, 0.96, 1.0)
        bg.inputs['Strength'].default_value = 1.0

cam_data = bpy.data.cameras.new(name="Cam")
cam_data.lens = 75.0
cam = bpy.data.objects.new(name="Cam", object_data=cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

track = cam.constraints.new(type='TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

cam.location = (-220.0, -290.0, 175.0)
scene.render.resolution_x = 1920
scene.render.resolution_y = 1920

# Export updated STLs
part_names = ["01_Base_Lower_Stand", "02_Neck_and_Head_Shell", "03_Sensor_Faceplate_Black", "04_Accent_Ring_Orange", "05_Button_Cap"]
for name in part_names:
    for obj in bpy.context.scene.objects: obj.select_set(False)
    obj = bpy.data.objects.get(name)
    if obj:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        path = os.path.join(OUTPUT_DIR, f"{name}.stl")
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
        print(f"Exported {name}.stl ({os.path.getsize(path):,} bytes)")

# Export Full Assembly STL
for obj in bpy.context.scene.objects: obj.select_set(obj.name in part_names)
full_path = os.path.join(OUTPUT_DIR, "StudySense_Complete_Assembly.stl")
bpy.ops.wm.stl_export(filepath=full_path, export_selected_objects=True)
print(f"Exported Complete Assembly STL ({os.path.getsize(full_path):,} bytes)")

# Render Hero View
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_isometric_hero.png")
bpy.ops.render.render(write_still=True)
print("Rendered render_isometric_hero.png successfully!")

