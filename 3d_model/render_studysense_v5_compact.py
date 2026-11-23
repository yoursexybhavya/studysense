import bpy
import bmesh
import math
import os

print("=== Rendering StudySense V5.0 Compact (Studio Quality) ===")

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
BLEND_FILE = os.path.join(OUTPUT_DIR, "StudySense_V5_Compact.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)
scene = bpy.context.scene

# Ensure EEVEE or Workbench
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine = 'BLENDER_EEVEE'

scene.render.resolution_x = 1920
scene.render.resolution_y = 1920
scene.render.film_transparent = False

# Materials
def get_or_make_mat(name, color, roughness=0.30, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = color
            bsdf.inputs['Roughness'].default_value = roughness
            bsdf.inputs['Metallic'].default_value = metallic
    return mat

mat_desk = get_or_make_mat("Studio_Desk_Wood", (0.72, 0.54, 0.36, 1.0), roughness=0.55)
mat_pad  = get_or_make_mat("Studio_Felt_Mat",  (0.14, 0.16, 0.20, 1.0), roughness=0.85)

# Add Studio Desk Surface & Felt Mat
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 20.0, -5.0))
desk = bpy.context.active_object
desk.name = "Studio_Desk"
desk.scale = (350.0, 300.0, 10.0)
bpy.ops.object.transform_apply(scale=True)
desk.data.materials.clear()
desk.data.materials.append(mat_desk)

# Rounded Desk Mat
bpy.ops.mesh.primitive_cylinder_add(radius=110.0, depth=2.0, location=(0, 24.0, 0.5), vertices=64)
mat_cyl = bpy.context.active_object
mat_cyl.name = "Studio_Felt_Pad"
mat_cyl.scale = (1.1, 0.85, 1.0)
bpy.ops.object.transform_apply(scale=True)
mat_cyl.data.materials.clear()
mat_cyl.data.materials.append(mat_pad)

# Camera Target at Center of Compact Assembly (Z=52.0mm)
cam_target = bpy.data.objects.get("Cam_Target")
if not cam_target:
    cam_target = bpy.data.objects.new("Cam_Target", None)
    scene.collection.objects.link(cam_target)
cam_target.location = (0, 6.0, 52.0)

# Lights
for obj in list(scene.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)

def add_sun(name, energy, rot):
    sd = bpy.data.lights.new(name=name, type='SUN')
    sd.energy = energy
    so = bpy.data.objects.new(name=name, object_data=sd)
    scene.collection.objects.link(so)
    so.rotation_euler = rot
    return so

add_sun("Key_Light",  5.5, (math.radians(48), math.radians(14), math.radians(-38)))
add_sun("Fill_Light", 2.8, (math.radians(32), math.radians(-22), math.radians(48)))
add_sun("Rim_Light",  3.5, (math.radians(-42), math.radians(18), math.radians(165)))

# Camera Setup
cam = bpy.data.objects.get("Main_Camera")
if not cam:
    cam_data = bpy.data.cameras.new(name="Main_Camera")
    cam = bpy.data.objects.new(name="Main_Camera", object_data=cam_data)
    scene.collection.objects.link(cam)

cam.data.lens = 65.0
scene.camera = cam

if not cam.constraints.get('TRACK_TO'):
    track = cam.constraints.new(type='TRACK_TO')
    track.target = cam_target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
else:
    cam.constraints['TRACK_TO'].target = cam_target

# 1. Render Hero Isometric View (Matching User Reference Image media_1795442255498_dc9a2c34.png)
cam.location = (-115.0, -195.0, 110.0)
hero_png = os.path.join(OUTPUT_DIR, "render_v5_isometric_hero.png")
scene.render.filepath = hero_png
print(f"Rendering Hero Isometric View -> {hero_png}...")
bpy.ops.render.render(write_still=True)
print("Hero render complete!")

# 2. Render Front View
cam.location = (0.0, -250.0, 52.0)
front_png = os.path.join(OUTPUT_DIR, "render_v5_front_view.png")
scene.render.filepath = front_png
print(f"Rendering Front View -> {front_png}...")
bpy.ops.render.render(write_still=True)
print("Front render complete!")

# 3. Render Rear View
cam.location = (0.0, 250.0, 52.0)
rear_png = os.path.join(OUTPUT_DIR, "render_v5_rear_view.png")
scene.render.filepath = rear_png
print(f"Rendering Rear View -> {rear_png}...")
bpy.ops.render.render(write_still=True)
print("Rear render complete!")

# 4. Render Exploded Assembly View
print("Arranging Exploded Assembly View...")
desk.hide_render = True
mat_cyl.hide_render = True

# Part offsets for exploded view
# Head/Neck shifts up
neck_obj = bpy.data.objects.get("02_Neck_and_Head_Pod")
if neck_obj:
    neck_obj.location.z += 25.0

# Accent ring shifts forward along local axis
ring_obj = bpy.data.objects.get("04_Accent_Ring_Orange")
if ring_obj:
    ring_obj.location.z += 25.0
    ring_obj.location.y -= 20.0

# Faceplate shifts forward
face_obj = bpy.data.objects.get("03_Sensor_Faceplate_Black")
if face_obj:
    face_obj.location.z += 25.0
    face_obj.location.y -= 38.0

# Rear Foot Lid shifts up
lid_obj = bpy.data.objects.get("05_Rear_Foot_Lid")
if lid_obj:
    lid_obj.location.z += 22.0

# Button cap shifts back
btn_obj = bpy.data.objects.get("06_Button_Cap")
if btn_obj:
    btn_obj.location.y += 18.0

# Hardware stubs shift with faceplate
for obj in scene.objects:
    if "Vis_PIR" in obj.name or "Vis_Can" in obj.name or "Vis_Mesh" in obj.name:
        obj.location.z += 25.0
        obj.location.y -= 38.0
    elif "Vis_LED" in obj.name:
        obj.location.z += 25.0

cam_target.location = (0, 6.0, 65.0)
cam.location = (-135.0, -215.0, 125.0)
exploded_png = os.path.join(OUTPUT_DIR, "render_v5_exploded_assembly.png")
scene.render.filepath = exploded_png
print(f"Rendering Exploded Assembly View -> {exploded_png}...")
bpy.ops.render.render(write_still=True)
print("Exploded assembly render complete!")

print("=== All V5 Compact Studio Renders Successfully Generated! ===")
