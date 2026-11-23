import bpy
import bmesh
import math
import os
from mathutils import Vector

print("=== Starting StudySense Production 3D CAD Generator v2.0 ===")

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001 # 1 unit = 1 mm

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# Materials Setup
# ---------------------------------------------------------
def make_mat(name, color, roughness=0.35, metallic=0.0, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
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

mat_white     = make_mat("Matte_White_Silk",   (0.95, 0.95, 0.97, 1.0), roughness=0.28)
mat_black     = make_mat("Matte_Carbon_Black", (0.05, 0.05, 0.06, 1.0), roughness=0.45)
mat_orange    = make_mat("Accent_Orange",      (0.98, 0.28, 0.02, 1.0), roughness=0.22)
mat_metal     = make_mat("Sensor_Metal",       (0.85, 0.85, 0.88, 1.0), roughness=0.2, metallic=0.9)
mat_mesh      = make_mat("Transducer_Mesh",    (0.04, 0.04, 0.04, 1.0), roughness=0.6)
mat_pir_dome  = make_mat("PIR_Dome_White",     (0.98, 0.98, 1.0, 1.0),  roughness=0.15)
mat_desk_wood = make_mat("Desk_Wood",          (0.70, 0.52, 0.35, 1.0), roughness=0.45)
mat_desk_mat  = make_mat("Desk_Felt_Mat",      (0.10, 0.12, 0.15, 1.0), roughness=0.8)

mat_led_g  = make_mat("LED_Green_Glow", (0.1, 0.95, 0.3, 1.0), roughness=0.1, emission=(0.1, 0.95, 0.3, 1.0), emission_strength=5.0)
mat_led_b  = make_mat("LED_Blue_Glow",  (0.15, 0.5, 0.98, 1.0), roughness=0.1, emission=(0.15, 0.5, 0.98, 1.0), emission_strength=5.0)
mat_led_r  = make_mat("LED_Red_Glow",   (0.98, 0.08, 0.12, 1.0), roughness=0.1, emission=(0.98, 0.08, 0.12, 1.0), emission_strength=5.0)

def set_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# Helper: Apply boolean
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

# Helper: create cylinder
def add_cyl(name, r, h, loc=(0,0,0), rot=(0,0,0), segs=64):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=segs, radius=r, depth=h,
        location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj

# Helper: create cube
def add_cube(name, size, loc=(0,0,0), rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj

# ---------------------------------------------------------
# PART 1: 01_Base_Lower_Stand
# ---------------------------------------------------------
print("Generating Part 1: Base Lower Stand...")

# Front block: width 74mm, depth 44mm, height 42mm
base_front = add_cube("Base_Front", (74.0, 44.0, 42.0), loc=(0, 0, 21.0))

# Rear foot extension (L-shape stabilizer): width 48mm, depth 48mm, height 18mm
base_rear = add_cube("Base_Rear", (48.0, 48.0, 18.0), loc=(0, 42.0, 9.0))
apply_bool(base_front, base_rear, operation='UNION')
base_obj = base_front
base_obj.name = "01_Base_Lower_Stand"

# Bevel exterior desk corners
bev = base_obj.modifiers.new(name="Bevel", type='BEVEL')
bev.width = 3.0
bev.segments = 4
bpy.context.view_layer.objects.active = base_obj
bpy.ops.object.modifier_apply(modifier=bev.name)

# Incline the front face (~13 deg backwards)
incline_cutter = add_cube("Incline_Cutter", (85.0, 24.0, 60.0), loc=(0, -29.0, 28.0), rot=(math.radians(13), 0, 0))
apply_bool(base_obj, incline_cutter, operation='DIFFERENCE')

# Internal cavity: starts at Z=3.0 (solid 3mm bottom floor!)
base_cavity = add_cube("Base_Cavity", (58.0, 66.0, 35.0), loc=(0, 20.0, 20.5))
apply_bool(base_obj, base_cavity, operation='DIFFERENCE')

# ESP32 Cradle inside base cavity
esp_bed = add_cube("ESP32_Bed", (34.0, 56.0, 5.0), loc=(0, 28.0, 5.5))
apply_bool(base_obj, esp_bed, operation='UNION')

esp_pocket = add_cube("ESP32_Pocket", (29.2, 53.0, 8.0), loc=(0, 28.0, 8.5))
apply_bool(base_obj, esp_pocket, operation='DIFFERENCE')

# Rear USB-C / Micro-USB port cutout (at Y=66mm, Z=8.5mm)
usb_hole = add_cube("USB_Hole", (13.0, 20.0, 7.5), loc=(0, 60.0, 8.5))
apply_bool(base_obj, usb_hole, operation='DIFFERENCE')

# Rear Push Button Cutout (GPIO 22) on the rear upper slope (Z=32mm)
btn_hole = add_cyl("Btn_Hole", r=3.5, h=25.0, loc=(0, 21.0, 32.0), rot=(math.radians(90), 0, 0))
apply_bool(base_obj, btn_hole, operation='DIFFERENCE')

# Vertical wire pass-through opening at top seam (Z=42mm)
wire_ch = add_cube("Base_Wire_Channel", (22.0, 16.0, 15.0), loc=(0, -2.0, 38.0))
apply_bool(base_obj, wire_ch, operation='DIFFERENCE')

# Upward alignment collar (male rim for snap-fit) Z from 42 to 46mm
collar = add_cube("Base_Collar", (32.0, 24.0, 5.0), loc=(0, -2.0, 44.5))
apply_bool(base_obj, collar, operation='UNION')

collar_hollow = add_cube("Collar_Hollow", (25.0, 17.0, 12.0), loc=(0, -2.0, 45.0))
apply_bool(base_obj, collar_hollow, operation='DIFFERENCE')

# Snap detent ribs on collar sides
detent_l = add_cube("Detent_L", (1.0, 8.0, 2.0), loc=(-16.0, -2.0, 44.5))
apply_bool(base_obj, detent_l, operation='UNION')
detent_r = add_cube("Detent_R", (1.0, 8.0, 2.0), loc=(16.0, -2.0, 44.5))
apply_bool(base_obj, detent_r, operation='UNION')

# Front StudySense Logo Emblem (Halo + 6 motif)
logo_cyl = add_cyl("Logo_Rim", r=7.5, h=1.8, loc=(0, -18.8, 14.0), rot=(math.radians(103), 0, 0))
logo_inner = add_cyl("Logo_Inner", r=4.8, h=2.5, loc=(0, -18.8, 14.0), rot=(math.radians(103), 0, 0))
apply_bool(logo_cyl, logo_inner, operation='DIFFERENCE')
logo_dot = add_cyl("Logo_Dot", r=2.5, h=1.8, loc=(0, -19.2, 14.0), rot=(math.radians(103), 0, 0))
apply_bool(logo_cyl, logo_dot, operation='UNION')
apply_bool(base_obj, logo_cyl, operation='UNION')

set_mat(base_obj, mat_white)
print("Part 1 complete.")

# ---------------------------------------------------------
# PART 2: 02_Neck_and_Head_Shell (Solidify Cup Method)
# ---------------------------------------------------------
print("Generating Part 2: Neck and Head Shell...")

# 1. Head Open Cup: Circle extruded forward by 26mm, solidified inwards by 3.5mm
# Back wall is at Y = +9.0, Z = 145.0, tilted 7 deg back (rot=97 deg)
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=38.0, fill_type='NGON', location=(0, 9.0, 145.0), rotation=(math.radians(97), 0, 0))
head_shell = bpy.context.active_object
head_shell.name = "Head_Cup_Base"

bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(head_shell.data)
boundary_edges = [e for e in bm.edges if e.is_boundary]
res = bmesh.ops.extrude_edge_only(bm, edges=boundary_edges)
verts = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
bmesh.ops.translate(bm, vec=(0, 0, 26.0), verts=verts) # Local Z extrudes forward (-Y in world)
bmesh.update_edit_mesh(head_shell.data)
bpy.ops.object.mode_set(mode='OBJECT')

sol = head_shell.modifiers.new(name="Solidify", type='SOLIDIFY')
sol.thickness = 3.5
sol.offset = -1.0 # Inwards: leaves outer r=38.0, inner r=34.5
bpy.ops.object.modifier_apply(modifier=sol.name)

# 2. Neck column (Cube: 36x28x88 from Z=42 up to Z=130 to solidly merge into the head!)
neck_outer = add_cube("Neck_Outer", (36.0, 28.0, 88.0), loc=(0, -2.5, 86.0))

# Aerodynamic neck taper
neck_taper_l = add_cube("Neck_Taper_Cutter_L", (20.0, 40.0, 95.0), loc=(-24.5, -2.5, 95.0), rot=(0, math.radians(4.8), 0))
apply_bool(neck_outer, neck_taper_l, operation='DIFFERENCE')
neck_taper_r = add_cube("Neck_Taper_Cutter_R", (20.0, 40.0, 95.0), loc=(24.5, -2.5, 95.0), rot=(0, math.radians(-4.8), 0))
apply_bool(neck_outer, neck_taper_r, operation='DIFFERENCE')

# Union neck + head cup
apply_bool(neck_outer, head_shell, operation='UNION')
neck_head_obj = neck_outer
neck_head_obj.name = "02_Neck_and_Head_Shell"

# Top decorative tab / rear ear
top_tab = add_cube("Top_Tab", (18.0, 8.0, 20.0), loc=(0, 4.0, 185.0), rot=(math.radians(7), 0, 0))
apply_bool(neck_head_obj, top_tab, operation='UNION')

# Female mating socket at bottom of neck (snaps over base collar)
socket = add_cube("Neck_Socket", (32.8, 24.8, 5.5), loc=(0, -2.0, 44.2))
apply_bool(neck_head_obj, socket, operation='DIFFERENCE')

# Snap detent grooves inside female socket
detent_groove_l = add_cube("Detent_G_L", (1.6, 9.0, 2.6), loc=(-16.0, -2.0, 44.5))
apply_bool(neck_head_obj, detent_groove_l, operation='DIFFERENCE')
detent_groove_r = add_cube("Detent_G_R", (1.6, 9.0, 2.6), loc=(16.0, -2.0, 44.5))
apply_bool(neck_head_obj, detent_groove_r, operation='DIFFERENCE')

# Internal hollow wire conduit up the neck (Z from 44 to 128)
wire_duct = add_cube("Neck_Wire_Duct", (18.0, 14.0, 84.0), loc=(0, -2.5, 86.0))
apply_bool(neck_head_obj, wire_duct, operation='DIFFERENCE')

# Duct into head cup
duct_to_head = add_cube("Duct_To_Head", (18.0, 14.0, 25.0), loc=(0, -2.0, 126.0))
apply_bool(neck_head_obj, duct_to_head, operation='DIFFERENCE')

# 3x LED Mounting Holes on Front Neck Face (Ø5.2mm each for 5mm LEDs)
led_z_coords = [94.0, 82.0, 70.0]
for idx, z in enumerate(led_z_coords):
    hole = add_cyl(f"LED_Hole_{idx}", r=2.6, h=25.0, loc=(0, -16.0, z), rot=(math.radians(90), 0, 0))
    apply_bool(neck_head_obj, hole, operation='DIFFERENCE')
    cbore = add_cyl(f"LED_Cbore_{idx}", r=3.6, h=10.0, loc=(0, -9.0, z), rot=(math.radians(90), 0, 0))
    apply_bool(neck_head_obj, cbore, operation='DIFFERENCE')

# Internal sensor mounting shelves inside head cup
hc_shelf_l = add_cube("HC_Shelf_L", (6.0, 12.0, 3.5), loc=(-23.0, -2.0, 133.0), rot=(math.radians(7), 0, 0))
apply_bool(neck_head_obj, hc_shelf_l, operation='UNION')
hc_shelf_r = add_cube("HC_Shelf_R", (6.0, 12.0, 3.5), loc=(23.0, -2.0, 133.0), rot=(math.radians(7), 0, 0))
apply_bool(neck_head_obj, hc_shelf_r, operation='UNION')

pir_shelf_l = add_cube("PIR_Shelf_L", (6.0, 12.0, 3.5), loc=(-18.0, -2.0, 158.0), rot=(math.radians(7), 0, 0))
apply_bool(neck_head_obj, pir_shelf_l, operation='UNION')
pir_shelf_r = add_cube("PIR_Shelf_R", (6.0, 12.0, 3.5), loc=(18.0, -2.0, 158.0), rot=(math.radians(7), 0, 0))
apply_bool(neck_head_obj, pir_shelf_r, operation='UNION')

set_mat(neck_head_obj, mat_white)
print("Part 2 complete.")

# ---------------------------------------------------------
# PART 3: 03_Sensor_Faceplate_Black
# ---------------------------------------------------------
print("Generating Part 3: Sensor Faceplate...")

# Head cup inner radius is 34.5.
# Faceplate disc fits inside the orange accent ring (radius 31.0mm, thickness 2.5mm)
# Front rim of head cup is at Y = -16.8, Z = 145.0
face_disc = add_cyl("03_Sensor_Faceplate_Black", r=31.0, h=2.5, loc=(0, -16.5, 145.0), rot=(math.radians(97), 0, 0))

# PIR Fresnel dome circular cutout (Ø23.6mm, centered at +11.5mm above head center)
pir_dome_hole = add_cyl("PIR_Dome_Hole", r=11.8, h=10.0, loc=(0, -17.9, 156.5), rot=(math.radians(97), 0, 0))
apply_bool(face_disc, pir_dome_hole, operation='DIFFERENCE')

# HC-SR04 Dual Eye cutouts (2x Ø16.5mm spaced 26.0mm center-to-center, centered at -11.0mm below head center)
hc_eye_l = add_cyl("HC_Eye_L", r=8.25, h=10.0, loc=(-13.0, -15.1, 134.0), rot=(math.radians(97), 0, 0))
apply_bool(face_disc, hc_eye_l, operation='DIFFERENCE')
hc_eye_r = add_cyl("HC_Eye_R", r=8.25, h=10.0, loc=(13.0, -15.1, 134.0), rot=(math.radians(97), 0, 0))
apply_bool(face_disc, hc_eye_r, operation='DIFFERENCE')

# Center crystal bridge slot
hc_slot = add_cube("HC_Slot", (7.0, 10.0, 3.8), loc=(0, -15.1, 134.0), rot=(math.radians(7), 0, 0))
apply_bool(face_disc, hc_slot, operation='DIFFERENCE')

# 4 Perimeter snap tabs on faceplate
for angle_deg in [0, 90, 180, 270]:
    rad = math.radians(angle_deg)
    tab_x = 31.2 * math.cos(rad)
    tab_z = 31.2 * math.sin(rad)
    tab = add_cube(f"Tab_{angle_deg}", (1.5, 1.8, 3.5), loc=(tab_x, -16.5, 145.0 + tab_z), rot=(math.radians(7), 0, rad))
    apply_bool(face_disc, tab, operation='UNION')

set_mat(face_disc, mat_black)
print("Part 3 complete.")

# ---------------------------------------------------------
# PART 4: 04_Accent_Ring_Orange
# ---------------------------------------------------------
print("Generating Part 4: Accent Ring...")

# Ring: outer radius 34.3mm (snugs inside the 34.5mm head opening)
# Inner radius 31.2mm (frames the black faceplate)
# Thickness 2.8mm, seated flush at Y = -16.5
ring_outer = add_cyl("04_Accent_Ring_Orange", r=34.3, h=2.8, loc=(0, -16.5, 145.0), rot=(math.radians(97), 0, 0))
ring_inner = add_cyl("Ring_Inner_Cutter", r=31.2, h=8.0, loc=(0, -16.5, 145.0), rot=(math.radians(97), 0, 0))
apply_bool(ring_outer, ring_inner, operation='DIFFERENCE')

set_mat(ring_outer, mat_orange)
print("Part 4 complete.")

# ---------------------------------------------------------
# PART 5: 05_Button_Cap
# ---------------------------------------------------------
print("Generating Part 5: Push Button Cap...")

btn_head = add_cyl("05_Button_Cap", r=3.1, h=5.5, loc=(0, 23.0, 32.0), rot=(math.radians(90), 0, 0))
btn_flange = add_cyl("Btn_Flange", r=4.6, h=1.5, loc=(0, 19.5, 32.0), rot=(math.radians(90), 0, 0))
apply_bool(btn_head, btn_flange, operation='UNION')
btn_post = add_cyl("Btn_Post", r=1.8, h=2.5, loc=(0, 17.5, 32.0), rot=(math.radians(90), 0, 0))
apply_bool(btn_head, btn_post, operation='UNION')

set_mat(btn_head, mat_white)
print("Part 5 complete.")

# ---------------------------------------------------------
# SENSOR & LED PREVIEW MOCKUPS (For Photorealistic Renders)
# ---------------------------------------------------------
preview_objs = []

# PIR Dome (white dome protruding through the hole)
pir_dome = add_cyl("Mock_PIR_Dome", r=11.2, h=9.0, loc=(0, -18.8, 156.5), rot=(math.radians(97), 0, 0), segs=32)
set_mat(pir_dome, mat_pir_dome)
preview_objs.append(pir_dome)

# HC-SR04 Transducers (2 silver metallic cans with black mesh fronts)
for eye_x, name in [(-13.0, "HC_Eye_Left"), (13.0, "HC_Eye_Right")]:
    can = add_cyl(f"Mock_{name}_Can", r=8.0, h=10.0, loc=(eye_x, -16.5, 134.0), rot=(math.radians(97), 0, 0), segs=32)
    set_mat(can, mat_metal)
    preview_objs.append(can)
    mesh = add_cyl(f"Mock_{name}_Mesh", r=7.2, h=1.2, loc=(eye_x, -21.0, 134.0), rot=(math.radians(97), 0, 0), segs=32)
    set_mat(mesh, mat_mesh)
    preview_objs.append(mesh)

# 3 Glowing LEDs on Neck (Green, Blue, Red)
led_colors = [(94.0, mat_led_g, "Green"), (82.0, mat_led_b, "Blue"), (70.0, mat_led_r, "Red")]
for z, mat, cname in led_colors:
    led_bead = add_cyl(f"Mock_LED_{cname}", r=2.5, h=4.0, loc=(0, -17.5, z), rot=(math.radians(90), 0, 0), segs=24)
    set_mat(led_bead, mat)
    preview_objs.append(led_bead)

# Desk Tabletop & Mat
desk = add_cube("Mock_Desk_Wood", (400.0, 300.0, 12.0), loc=(0, 20.0, -6.0))
set_mat(desk, mat_desk_wood)
preview_objs.append(desk)

mat_pad = add_cube("Mock_Desk_Mat", (220.0, 180.0, 2.0), loc=(0, 15.0, 1.0))
set_mat(mat_pad, mat_desk_mat)
preview_objs.append(mat_pad)

# ---------------------------------------------------------
# STUDIO LIGHTING & CAMERA SETUP
# ---------------------------------------------------------
print("Setting up Professional Studio 3-Point Sun Lighting and Tracking Camera...")

target = bpy.data.objects.new("Cam_Target", None)
scene.collection.objects.link(target)
target.location = (0, 0, 95.0)

def add_sun(name, energy, rot):
    sun_data = bpy.data.lights.new(name=name, type='SUN')
    sun_data.energy = energy
    sun_obj = bpy.data.objects.new(name=name, object_data=sun_data)
    scene.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = rot
    return sun_obj

add_sun("Key_Sun", 6.0, (math.radians(45), math.radians(20), math.radians(-35)))
add_sun("Fill_Sun", 3.0, (math.radians(40), math.radians(-25), math.radians(45)))
add_sun("Rim_Sun", 3.5, (math.radians(-55), math.radians(10), math.radians(175)))

if scene.world:
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.88, 0.90, 0.92, 1.0)
        bg.inputs['Strength'].default_value = 1.0

cam_data = bpy.data.cameras.new(name="Main_Camera")
cam_data.lens = 85.0
cam_obj = bpy.data.objects.new(name="Main_Camera", object_data=cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

track = cam_obj.constraints.new(type='TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

cam_obj.location = (-220.0, -280.0, 165.0)

scene.render.resolution_x = 1920
scene.render.resolution_y = 1920
scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'RenderSettings') and 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'

# ---------------------------------------------------------
# EXPORT STL & OBJ FILES (Bambu Studio Ready)
# ---------------------------------------------------------
print("Exporting individual STL files for Bambu Studio...")

part_names = [
    "01_Base_Lower_Stand",
    "02_Neck_and_Head_Shell",
    "03_Sensor_Faceplate_Black",
    "04_Accent_Ring_Orange",
    "05_Button_Cap"
]

for name in part_names:
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    obj = bpy.data.objects.get(name)
    if obj:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        filepath = os.path.join(OUTPUT_DIR, f"{name}.stl")
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True, global_scale=1.0)
        print(f" -> Exported {name}.stl ({os.path.getsize(filepath):,} bytes)")

# Export Complete Assembly STL (Printing parts only, no mockups)
for obj in bpy.context.scene.objects:
    obj.select_set(obj.name in part_names)
full_stl_path = os.path.join(OUTPUT_DIR, "StudySense_Complete_Assembly.stl")
bpy.ops.wm.stl_export(filepath=full_stl_path, export_selected_objects=True, global_scale=1.0)
print(f" -> Exported Complete Assembly STL ({os.path.getsize(full_stl_path):,} bytes)")

# Export Full Assembly OBJ (with material MTLLib)
full_obj_path = os.path.join(OUTPUT_DIR, "StudySense_Complete_Assembly.obj")
bpy.ops.wm.obj_export(filepath=full_obj_path, export_selected_objects=True, global_scale=1.0)
print(f" -> Exported Complete Assembly OBJ ({os.path.getsize(full_obj_path):,} bytes)")

# Save .blend file (with camera & lights intact!)
blend_path = os.path.join(OUTPUT_DIR, "StudySense_Enclosure.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f" -> Saved Blender project file: {blend_path}")

# ---------------------------------------------------------
# RENDERING PREVIEWS
# ---------------------------------------------------------
# Render 1: Front-Left Isometric Hero View (Matching user's reference photo angle!)
print("Rendering Render 1: Isometric Hero View...")
cam_obj.location = (-220.0, -280.0, 165.0)
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_isometric_hero.png")
bpy.ops.render.render(write_still=True)
print(" -> Saved render_isometric_hero.png")

# Render 2: Front Elevation View
print("Rendering Render 2: Front Elevation View...")
cam_obj.location = (0.0, -350.0, 100.0)
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_front_view.png")
bpy.ops.render.render(write_still=True)
print(" -> Saved render_front_view.png")

# Render 3: Rear View (Showing USB cutout & Button)
print("Rendering Render 3: Rear View...")
cam_obj.location = (0.0, 350.0, 100.0)
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_rear_view.png")
bpy.ops.render.render(write_still=True)
print(" -> Saved render_rear_view.png")

# Render 4: Exploded Assembly View
print("Generating and Rendering Render 4: Exploded View...")
for p in preview_objs:
    p.hide_render = True

desk_obj = bpy.data.objects.get("Mock_Desk_Wood")
if desk_obj: desk_obj.hide_render = True
mat_obj = bpy.data.objects.get("Mock_Desk_Mat")
if mat_obj: mat_obj.hide_render = True

face_obj = bpy.data.objects.get("03_Sensor_Faceplate_Black")
ring_obj = bpy.data.objects.get("04_Accent_Ring_Orange")
neck_obj = bpy.data.objects.get("02_Neck_and_Head_Shell")
btn_obj  = bpy.data.objects.get("05_Button_Cap")

if face_obj: face_obj.location.y -= 50.0
if ring_obj: ring_obj.location.y -= 28.0
if neck_obj: neck_obj.location.z += 35.0
if btn_obj:  btn_obj.location.y += 28.0

cam_obj.location = (-260.0, -290.0, 210.0)
scene.render.filepath = os.path.join(OUTPUT_DIR, "render_exploded_assembly.png")
bpy.ops.render.render(write_still=True)
print(" -> Saved render_exploded_assembly.png")

print("=== All 3D CAD Models, Assemblies, and Studio Renders Generated Successfully! ===")
