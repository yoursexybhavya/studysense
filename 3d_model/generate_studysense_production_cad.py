import bpy
import bmesh
import math
import os

print("=== Starting StudySense Production CAD Engine v3.5 (Bambu Studio Optimized) ===")

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001 # 1 unit = 1 mm

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
STL_DIR = os.path.join(OUTPUT_DIR, "stl")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STL_DIR, exist_ok=True)

# -------------------------------------------------------------
# Materials Setup
# -------------------------------------------------------------
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

mat_white  = make_mat("Matte_White_Silk",   (0.96, 0.96, 0.98, 1.0), roughness=0.25)
mat_black  = make_mat("Matte_Carbon_Black", (0.04, 0.04, 0.05, 1.0), roughness=0.45)
mat_orange = make_mat("Accent_Orange",      (0.98, 0.28, 0.02, 1.0), roughness=0.20)
mat_metal  = make_mat("Sensor_Metal",       (0.85, 0.85, 0.88, 1.0), roughness=0.15, metallic=0.9)
mat_mesh   = make_mat("Transducer_Mesh",    (0.03, 0.03, 0.03, 1.0), roughness=0.6)
mat_pir    = make_mat("PIR_Fresnel_Dome",   (0.96, 0.96, 1.0, 1.0),  roughness=0.15)
mat_desk   = make_mat("Desk_Wood",          (0.68, 0.50, 0.32, 1.0), roughness=0.5)
mat_mat    = make_mat("Desk_Felt_Pad",      (0.12, 0.14, 0.18, 1.0), roughness=0.8)

mat_led_g  = make_mat("LED_Green_Glow", (0.10, 0.95, 0.30, 1.0), roughness=0.1, emission=(0.10, 0.95, 0.30, 1.0), emission_strength=6.0)
mat_led_b  = make_mat("LED_Blue_Glow",  (0.15, 0.50, 0.98, 1.0), roughness=0.1, emission=(0.15, 0.50, 0.98, 1.0), emission_strength=6.0)
mat_led_r  = make_mat("LED_Red_Glow",   (0.98, 0.08, 0.12, 1.0), roughness=0.1, emission=(0.98, 0.08, 0.12, 1.0), emission_strength=6.0)

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

# -------------------------------------------------------------
# GEOMETRIC CONSTANTS
# -------------------------------------------------------------
HEAD_Z = 152.0
HEAD_Y = 0.0
TILT_DEG = 7.0
TILT_RAD = math.radians(TILT_DEG)
ROT_X = math.radians(90.0 + TILT_DEG)

HEAD_RADIUS = 37.0 # 74mm OD
HEAD_DEPTH = 32.0  # 32mm deep circular pod
FRONT_OFFSET = HEAD_DEPTH / 2.0 # 16mm forward along local axis

# Front face center of head pod
FACE_Y = HEAD_Y - FRONT_OFFSET * math.cos(TILT_RAD) # ~ -15.88mm
FACE_Z = HEAD_Z - FRONT_OFFSET * math.sin(TILT_RAD) # ~ 150.05mm

print(f"Pod Center: (0, {HEAD_Y}, {HEAD_Z}) | Front Face: (0, {FACE_Y:.2f}, {FACE_Z:.2f})")

# -------------------------------------------------------------
# PART 1: 01_Base_Lower_Stand
# -------------------------------------------------------------
print("Crafting Part 1: Base Lower Stand...")

# Base front body: 74mm width, 46mm depth, 40mm height (Z=0 to 40)
base_front = add_cube("Base_Front", (74.0, 46.0, 40.0), loc=(0, 6.0, 20.0))

# Rear foot extension (stabilizer desk foot): 50mm width, 48mm depth, 16mm height (Z=0 to 16)
base_rear = add_cube("Base_Rear", (50.0, 48.0, 16.0), loc=(0, 48.0, 8.0))
apply_bool(base_front, base_rear, operation='UNION')
base_obj = base_front
base_obj.name = "01_Base_Lower_Stand"

# Smooth rounded bevel on exterior perimeter
bev_base = base_obj.modifiers.new(name="Bevel", type='BEVEL')
bev_base.width = 3.2
bev_base.segments = 4
bpy.context.view_layer.objects.active = base_obj
bpy.ops.object.modifier_apply(modifier=bev_base.name)

# 14-degree sloping front ramp
ramp = add_cube("Ramp_Cutter", (85.0, 26.0, 50.0), loc=(0, -25.0, 22.0), rot=(math.radians(14), 0, 0))
apply_bool(base_obj, ramp, operation='DIFFERENCE')

# Internal ESP32 & Wiring Cavity (Solid 4mm front wall, solid 3mm floor)
# Starts at Y = -1.0 to Y = 65.0 (depth 66mm, center Y=32.0)
base_cavity = add_cube("Base_Cavity", (58.0, 64.0, 34.0), loc=(0, 32.0, 20.0))
apply_bool(base_obj, base_cavity, operation='DIFFERENCE')

# ESP32 Cradle Bed
esp_bed = add_cube("ESP_Bed", (34.0, 56.0, 5.0), loc=(0, 36.0, 5.5))
apply_bool(base_obj, esp_bed, operation='UNION')
esp_pocket = add_cube("ESP_Pocket", (29.2, 53.0, 8.0), loc=(0, 36.0, 8.5))
apply_bool(base_obj, esp_pocket, operation='DIFFERENCE')

# Rear USB Power Port (Slot: 13.5mm x 8.0mm at Y=71mm, Z=8.5mm)
usb_slot = add_cube("USB_Slot", (13.5, 20.0, 8.0), loc=(0, 70.0, 8.5))
apply_bool(base_obj, usb_slot, operation='DIFFERENCE')

# Rear Push Button Cutout (GPIO 22) on rear upper slope (Z=28mm)
btn_hole = add_cyl("Btn_Hole", r=3.5, h=25.0, loc=(0, 28.0, 28.0), rot=(math.radians(90), 0, 0))
apply_bool(base_obj, btn_hole, operation='DIFFERENCE')

# Top Male Alignment Collar (Z=40 to 45mm)
collar = add_cube("Base_Collar", (32.0, 24.2, 5.0), loc=(0, 6.0, 42.5))
apply_bool(base_obj, collar, operation='UNION')
collar_hol = add_cube("Collar_Hollow", (24.0, 17.0, 12.0), loc=(0, 6.0, 42.5))
apply_bool(base_obj, collar_hol, operation='DIFFERENCE')

# Snap Detent Ribs on Collar
detent_l = add_cube("Detent_L", (1.2, 8.0, 2.2), loc=(-16.0, 6.0, 42.5))
apply_bool(base_obj, detent_l, operation='UNION')
detent_r = add_cube("Detent_R", (1.2, 8.0, 2.2), loc=(16.0, 6.0, 42.5))
apply_bool(base_obj, detent_r, operation='UNION')

# Embossed StudySense Logo (Emblem: concentric halo ring + inner core)
logo_ring = add_cyl("Logo_Ring", r=7.2, h=1.8, loc=(0, -14.6, 12.5), rot=(math.radians(104), 0, 0), segs=48)
logo_hole = add_cyl("Logo_Hole", r=4.5, h=2.5, loc=(0, -14.6, 12.5), rot=(math.radians(104), 0, 0), segs=48)
apply_bool(logo_ring, logo_hole, operation='DIFFERENCE')
logo_dot  = add_cyl("Logo_Dot", r=2.2, h=1.8, loc=(0, -14.6, 12.5), rot=(math.radians(104), 0, 0), segs=32)
apply_bool(logo_ring, logo_dot, operation='UNION')
apply_bool(base_obj, logo_ring, operation='UNION')

set_mat(base_obj, mat_white)
print("Part 1 created successfully.")

# -------------------------------------------------------------
# PART 2: 02_Neck_and_Head_Shell
# -------------------------------------------------------------
print("Crafting Part 2: Neck and Head Shell...")

# 1. Circular Head Cup
head_cyl = add_cyl("Head_Cyl", r=HEAD_RADIUS, h=HEAD_DEPTH, loc=(0, HEAD_Y, HEAD_Z), rot=(ROT_X, 0, 0), segs=96)

# Spherical organic rear dome
head_dome = bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=HEAD_RADIUS, location=(0, HEAD_Y + 5.0, HEAD_Z))
dome_obj = bpy.context.active_object
dome_obj.scale = (1.0, 0.45, 1.0)
bpy.ops.object.transform_apply(scale=True)
apply_bool(head_cyl, dome_obj, operation='UNION')

# Hollow out the front cavity (depth 28mm, leaves 3.2mm solid wall)
head_cavity = add_cyl("Head_Cavity", r=33.8, h=28.0, loc=(0, HEAD_Y - 2.5, HEAD_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(head_cyl, head_cavity, operation='DIFFERENCE')

# Top rear acoustic fin / handle
fin = add_cube("Top_Fin", (18.0, 10.0, 24.0), loc=(0, 10.0, HEAD_Z + 38.0), rot=(math.radians(15), 0, 0))
fin_bev = fin.modifiers.new(name="Bevel", type='BEVEL')
fin_bev.width = 3.0
fin_bev.segments = 4
bpy.context.view_layer.objects.active = fin
bpy.ops.object.modifier_apply(modifier=fin_bev.name)
apply_bool(head_cyl, fin, operation='UNION')

# 2. Vertical Tapered Neck (Attaches to BOTTOM and REAR of head)
# Neck height 82mm (Z=40 to 122), center Z=81.0, center Y=6.0
neck_h = 82.0
neck_z = 40.0 + neck_h/2.0
neck = add_cube("Neck", (36.0, 26.0, neck_h), loc=(0, 6.0, neck_z))

# Lateral width taper (from 36mm down to 26mm)
taper_l = add_cube("Taper_L", (20.0, 40.0, 95.0), loc=(-26.0, 6.0, neck_z), rot=(0, math.radians(4.2), 0))
apply_bool(neck, taper_l, operation='DIFFERENCE')
taper_r = add_cube("Taper_R", (20.0, 40.0, 95.0), loc=(26.0, 6.0, neck_z), rot=(0, math.radians(-4.2), 0))
apply_bool(neck, taper_r, operation='DIFFERENCE')

# Gentle 7-degree slope on front face
neck_incline = add_cube("Neck_Incline", (50.0, 20.0, 95.0), loc=(0, -17.0, neck_z), rot=(math.radians(7), 0, 0))
apply_bool(neck, neck_incline, operation='DIFFERENCE')

# 3x Status LED Mounting Holes on Front Neck Face (Ø5.2mm with Ø6.4mm counterbore)
# Green at Z=96 (Active Study), Blue at Z=82 (Standby/Break), Red at Z=68 (Posture/Absence Alert)
for z_led in [96.0, 82.0, 68.0]:
    led_h = add_cyl(f"LED_H_{z_led}", r=2.6, h=25.0, loc=(0, -12.0, z_led), rot=(math.radians(97), 0, 0), segs=32)
    apply_bool(neck, led_h, operation='DIFFERENCE')
    cb = add_cyl(f"LED_CB_{z_led}", r=3.2, h=10.0, loc=(0, -3.0, z_led), rot=(math.radians(97), 0, 0), segs=32)
    apply_bool(neck, cb, operation='DIFFERENCE')

# Hollow conduit (18mm x 14mm) for routing 11cm wire harness
wire_duct = add_cube("Wire_Duct", (18.0, 14.0, neck_h + 10.0), loc=(0, 6.0, neck_z))
apply_bool(neck, wire_duct, operation='DIFFERENCE')

# Union Neck with Head Pod
apply_bool(neck, head_cyl, operation='UNION')
head_neck_obj = neck
head_neck_obj.name = "02_Neck_and_Head_Shell"

# Duct connection into head cavity
duct_head = add_cube("Duct_Head", (18.0, 14.0, 25.0), loc=(0, 4.0, 122.0))
apply_bool(head_neck_obj, duct_head, operation='DIFFERENCE')

# Female snap socket at neck base (mating with base collar)
socket = add_cube("Socket", (32.8, 25.0, 6.0), loc=(0, 6.0, 42.5))
apply_bool(head_neck_obj, socket, operation='DIFFERENCE')
detent_groove_l = add_cube("Detent_G_L", (1.6, 9.0, 2.6), loc=(-16.0, 6.0, 42.5))
apply_bool(head_neck_obj, detent_groove_l, operation='DIFFERENCE')
detent_groove_r = add_cube("Detent_G_R", (1.6, 9.0, 2.6), loc=(16.0, 6.0, 42.5))
apply_bool(head_neck_obj, detent_groove_r, operation='DIFFERENCE')

# Internal sensor mounting brackets
hc_shelf_l = add_cube("HC_Shelf_L", (6.0, 12.0, 3.5), loc=(-23.0, -1.0, 133.0), rot=(ROT_X, 0, 0))
apply_bool(head_neck_obj, hc_shelf_l, operation='UNION')
hc_shelf_r = add_cube("HC_Shelf_R", (6.0, 12.0, 3.5), loc=(23.0, -1.0, 133.0), rot=(ROT_X, 0, 0))
apply_bool(head_neck_obj, hc_shelf_r, operation='UNION')

pir_shelf_l = add_cube("PIR_Shelf_L", (6.0, 12.0, 3.5), loc=(-18.0, -1.0, 158.0), rot=(ROT_X, 0, 0))
apply_bool(head_neck_obj, pir_shelf_l, operation='UNION')
pir_shelf_r = add_cube("PIR_Shelf_R", (6.0, 12.0, 3.5), loc=(18.0, -1.0, 158.0), rot=(ROT_X, 0, 0))
apply_bool(head_neck_obj, pir_shelf_r, operation='UNION')

set_mat(head_neck_obj, mat_white)
print("Part 2 created successfully.")

# -------------------------------------------------------------
# PART 3: 03_Sensor_Faceplate_Black
# -------------------------------------------------------------
print("Crafting Part 3: Sensor Faceplate...")

face = add_cyl("03_Sensor_Faceplate_Black", r=30.4, h=2.4, loc=(0, FACE_Y, FACE_Z), rot=(ROT_X, 0, 0), segs=96)

# PIR Dome Aperture: Ø23.4mm at local Z=+11.5mm
pir_z = FACE_Z + 11.5 * math.cos(TILT_RAD)
pir_y = FACE_Y - 11.5 * math.sin(TILT_RAD)
pir_hole = add_cyl("PIR_Cut", r=11.7, h=10.0, loc=(0, pir_y, pir_z), rot=(ROT_X, 0, 0), segs=64)
apply_bool(face, pir_hole, operation='DIFFERENCE')

# HC-SR04 Dual Eyes: 2x Ø16.3mm spaced 26.0mm apart at local Z=-11.0mm
hc_z = FACE_Z - 11.0 * math.cos(TILT_RAD)
hc_y = FACE_Y + 11.0 * math.sin(TILT_RAD)
for eye_x in [-13.0, 13.0]:
    eye_h = add_cyl(f"Eye_Cut_{eye_x}", r=8.15, h=10.0, loc=(eye_x, hc_y, hc_z), rot=(ROT_X, 0, 0), segs=64)
    apply_bool(face, eye_h, operation='DIFFERENCE')

# Center crystal bridge slot
slot = add_cube("Slot", (7.0, 8.0, 3.6), loc=(0, hc_y, hc_z), rot=(ROT_X, 0, 0))
apply_bool(face, slot, operation='DIFFERENCE')

# 4 Perimeter alignment tabs
for angle_deg in [0, 90, 180, 270]:
    rad = math.radians(angle_deg)
    tab_x = 30.6 * math.cos(rad)
    tab_z = FACE_Z + 30.6 * math.sin(rad) * math.cos(TILT_RAD)
    tab_y = FACE_Y - 30.6 * math.sin(rad) * math.sin(TILT_RAD)
    tab = add_cube(f"Tab_{angle_deg}", (1.5, 1.8, 3.2), loc=(tab_x, tab_y, tab_z), rot=(ROT_X, 0, rad))
    apply_bool(face, tab, operation='UNION')

set_mat(face, mat_black)
print("Part 3 created successfully.")

# -------------------------------------------------------------
# PART 4: 04_Accent_Ring_Orange
# -------------------------------------------------------------
print("Crafting Part 4: Accent Halo Ring...")

# Outer radius 33.6mm, inner radius 30.6mm, thickness 2.5mm
ring = add_cyl("04_Accent_Ring_Orange", r=33.6, h=2.5, loc=(0, FACE_Y, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
ring_cut = add_cyl("Ring_Cut", r=30.6, h=8.0, loc=(0, FACE_Y, FACE_Z), rot=(ROT_X, 0, 0), segs=96)
apply_bool(ring, ring_cut, operation='DIFFERENCE')
set_mat(ring, mat_orange)
print("Part 4 created successfully.")

# -------------------------------------------------------------
# PART 5: 05_Button_Cap
# -------------------------------------------------------------
print("Crafting Part 5: Push Button Cap...")

btn_cap = add_cyl("05_Button_Cap", r=3.2, h=6.0, loc=(0, 29.0, 28.0), rot=(math.radians(90), 0, 0), segs=32)
btn_flange = add_cyl("Btn_Flange", r=4.5, h=1.5, loc=(0, 26.5, 28.0), rot=(math.radians(90), 0, 0), segs=32)
apply_bool(btn_cap, btn_flange, operation='UNION')
set_mat(btn_cap, mat_black)
print("Part 5 created successfully.")

# -------------------------------------------------------------
# SENSOR & LED PREVIEW MOCKUPS (For Studio Renders)
# -------------------------------------------------------------
preview_objs = []

# PIR Dome Mockup
pir_dome = add_cyl("Mock_PIR_Dome", r=11.2, h=9.0, loc=(0, pir_y - 2.0, pir_z), rot=(ROT_X, 0, 0), segs=48)
set_mat(pir_dome, mat_pir)
preview_objs.append(pir_dome)

# HC-SR04 Transducers Mockup (Silver metal cans + dark mesh fronts)
for eye_x in [-13.0, 13.0]:
    can = add_cyl(f"Mock_Can_{eye_x}", r=8.0, h=10.0, loc=(eye_x, hc_y - 1.0, hc_z), rot=(ROT_X, 0, 0), segs=48)
    set_mat(can, mat_metal)
    preview_objs.append(can)
    mesh = add_cyl(f"Mock_Mesh_{eye_x}", r=7.2, h=1.2, loc=(eye_x, hc_y - 5.5, hc_z), rot=(ROT_X, 0, 0), segs=48)
    set_mat(mesh, mat_mesh)
    preview_objs.append(mesh)

# 3 Glowing LEDs on Neck (Green, Blue, Red)
led_preview_data = [(96.0, mat_led_g, "Green"), (82.0, mat_led_b, "Blue"), (68.0, mat_led_r, "Red")]
for z_led, led_mat, cname in led_preview_data:
    led_bead = add_cyl(f"Mock_LED_{cname}", r=2.5, h=4.0, loc=(0, -11.5, z_led), rot=(math.radians(97), 0, 0), segs=32)
    set_mat(led_bead, led_mat)
    preview_objs.append(led_bead)

# Studio Desk & Mat
desk = add_cube("Mock_Desk_Wood", (380.0, 300.0, 12.0), loc=(0, 25.0, -6.0))
set_mat(desk, mat_desk)
preview_objs.append(desk)

pad = add_cube("Mock_Desk_Mat", (240.0, 200.0, 2.0), loc=(0, 20.0, 1.0))
set_mat(pad, mat_mat)
preview_objs.append(pad)

# -------------------------------------------------------------
# STUDIO 3-POINT LIGHTING & CAMERA
# -------------------------------------------------------------
target = bpy.data.objects.new("Cam_Target", None)
scene.collection.objects.link(target)
target.location = (0, 0, 95.0)

def add_sun(name, energy, rot):
    sd = bpy.data.lights.new(name=name, type='SUN')
    sd.energy = energy
    so = bpy.data.objects.new(name=name, object_data=sd)
    scene.collection.objects.link(so)
    so.rotation_euler = rot

add_sun("Key_Sun", 5.5, (math.radians(45), math.radians(20), math.radians(-35)))
add_sun("Fill_Sun", 2.8, (math.radians(35), math.radians(-30), math.radians(50)))
add_sun("Rim_Sun", 3.5, (math.radians(-50), math.radians(15), math.radians(170)))

if scene.world:
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.92, 0.94, 0.96, 1.0)
        bg.inputs['Strength'].default_value = 1.0

cam_data = bpy.data.cameras.new(name="Main_Camera")
cam_data.lens = 85.0
cam = bpy.data.objects.new(name="Main_Camera", object_data=cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

track = cam.constraints.new(type='TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

cam.location = (-220.0, -290.0, 175.0)
scene.render.resolution_x = 1920
scene.render.resolution_y = 1920

# -------------------------------------------------------------
# EXPORT STL FILES (Bambu Studio Production Ready)
# -------------------------------------------------------------
print("Exporting production STL files for Bambu Studio...")

part_names = [
    "01_Base_Lower_Stand",
    "02_Neck_and_Head_Shell",
    "03_Sensor_Faceplate_Black",
    "04_Accent_Ring_Orange",
    "05_Button_Cap"
]

for name in part_names:
    for obj in bpy.context.scene.objects: obj.select_set(False)
    obj = bpy.data.objects.get(name)
    if obj:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        path = os.path.join(STL_DIR, f"{name}.stl")
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
        # Also copy to root 3d_model/
        root_path = os.path.join(OUTPUT_DIR, f"{name}.stl")
        bpy.ops.wm.stl_export(filepath=root_path, export_selected_objects=True)
        print(f" -> Exported {name}.stl ({os.path.getsize(path):,} bytes)")

# Export Full Assembly STL
for obj in bpy.context.scene.objects: obj.select_set(obj.name in part_names)
full_stl = os.path.join(OUTPUT_DIR, "StudySense_Complete_Assembly.stl")
bpy.ops.wm.stl_export(filepath=full_stl, export_selected_objects=True)
full_stl_sub = os.path.join(STL_DIR, "StudySense_Full_Assembly.stl")
bpy.ops.wm.stl_export(filepath=full_stl_sub, export_selected_objects=True)
print(f" -> Exported Complete Assembly STL ({os.path.getsize(full_stl):,} bytes)")

# Export Full Assembly OBJ with MTL
full_obj = os.path.join(OUTPUT_DIR, "StudySense_Complete_Assembly.obj")
bpy.ops.wm.obj_export(filepath=full_obj, export_selected_objects=True)
print(f" -> Exported Complete Assembly OBJ ({os.path.getsize(full_obj):,} bytes)")

# Save Blender Master Project File
blend_path = os.path.join(OUTPUT_DIR, "StudySense_Enclosure.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f" -> Saved Blender Project File: {blend_path}")

# -------------------------------------------------------------
# HIGH-RESOLUTION STUDIO RENDERS
# -------------------------------------------------------------
# Render 1: Isometric Hero View (Matching user's reference photo angle!)
print("Rendering View 1: Isometric Hero View...")
cam.location = (-220.0, -290.0, 175.0)
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_isometric_hero.png")
bpy.ops.render.render(write_still=True)
print(" -> Saved render_isometric_hero.png")

# Render 2: Front Elevation View
print("Rendering View 2: Front Elevation View...")
cam.location = (0.0, -360.0, 105.0)
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_front_view.png")
bpy.ops.render.render(write_still=True)
print(" -> Saved render_front_view.png")

# Render 3: Rear View (Showing USB cutout & Button)
print("Rendering View 3: Rear View...")
cam.location = (0.0, 360.0, 105.0)
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_rear_view.png")
bpy.ops.render.render(write_still=True)
print(" -> Saved render_rear_view.png")

# Render 4: Exploded Assembly View
print("Rendering View 4: Exploded Assembly View...")
for p in preview_objs: p.hide_render = True

face_obj = bpy.data.objects.get("03_Sensor_Faceplate_Black")
ring_obj = bpy.data.objects.get("04_Accent_Ring_Orange")
neck_obj = bpy.data.objects.get("02_Neck_and_Head_Shell")
btn_obj  = bpy.data.objects.get("05_Button_Cap")

if face_obj: face_obj.location.y -= 52.0
if ring_obj: ring_obj.location.y -= 28.0
if neck_obj: neck_obj.location.z += 35.0
if btn_obj:  btn_obj.location.y += 28.0

cam.location = (-260.0, -290.0, 210.0)
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_exploded_assembly.png")
bpy.ops.render.render(write_still=True)
print(" -> Saved render_exploded_assembly.png")

print("=== StudySense Production CAD Engine v3.5 Finished Successfully! ===")
