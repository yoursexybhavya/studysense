import bpy
import bmesh
import math
import os

print("=== Rendering StudySense V7 Final (Calibrated <=11cm Height Architecture) ===")

OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model"
BLEND_FILE = os.path.join(OUTPUT_DIR, "StudySense_V7_Final.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)
scene = bpy.context.scene

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

# Studio Desk Surface & Felt Mat
desk = bpy.data.objects.get("Mock_Studio_Desk")
mat_cyl = bpy.data.objects.get("Mock_Desk_Mat")

# Camera Target at Center of V7 Assembly (Z=52.0mm)
cam_target = bpy.data.objects.get("Cam_Target")
if not cam_target:
    cam_target = bpy.data.objects.new("Cam_Target", None)
    scene.collection.objects.link(cam_target)
cam_target.location = (0, 8.0, 52.0)

# Studio Lights
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
cam.location = (-115.0, -190.0, 105.0)
hero_png = os.path.join(OUTPUT_DIR, "render_v7_isometric_hero.png")
scene.render.filepath = hero_png
print(f"Rendering Hero Isometric View -> {hero_png}...")
bpy.ops.render.render(write_still=True)
print("Hero render complete!")

# 2. Render Front View
cam.location = (0.0, -240.0, 52.0)
front_png = os.path.join(OUTPUT_DIR, "render_v7_front_view.png")
scene.render.filepath = front_png
print(f"Rendering Front View -> {front_png}...")
bpy.ops.render.render(write_still=True)
print("Front render complete!")

# 3. Render Rear View
cam.location = (0.0, 240.0, 52.0)
rear_png = os.path.join(OUTPUT_DIR, "render_v7_rear_view.png")
scene.render.filepath = rear_png
print(f"Rendering Rear View -> {rear_png}...")
bpy.ops.render.render(write_still=True)
print("Rear render complete!")

# 4. Render Exploded Assembly View
print("Arranging Exploded Assembly View...")
if desk: desk.hide_render = True
if mat_cyl: mat_cyl.hide_render = True

# Part offsets for exploded view
# Lower cover drops downward
bot_cov = bpy.data.objects.get("05_Base_Bottom_Cover")
if bot_cov:
    bot_cov.location.z -= 18.0

# Neck and head pod rises upward
neck_obj = bpy.data.objects.get("02_Neck_and_Head_Pod")
if neck_obj:
    neck_obj.location.z += 22.0

# Accent ring moves forward
ring_obj = bpy.data.objects.get("04_Accent_Ring_Orange")
if ring_obj:
    ring_obj.location.z += 22.0
    ring_obj.location.y -= 18.0

# Sensor Faceplate moves further forward
face_obj = bpy.data.objects.get("03_Sensor_Faceplate_Black")
if face_obj:
    face_obj.location.z += 22.0
    face_obj.location.y -= 36.0

# Push button moves backward
btn_obj = bpy.data.objects.get("06_Button_Cap")
if btn_obj:
    btn_obj.location.y += 18.0

# Mock sensors move with faceplate
for obj in scene.objects:
    if "Mock_PIR" in obj.name or "Mock_Eye" in obj.name or "Mock_Mesh" in obj.name or "Mock_Blue_PCB" in obj.name:
        obj.location.z += 22.0
        obj.location.y -= 36.0
    elif "Mock_LED" in obj.name:
        obj.location.z += 22.0

cam_target.location = (0, 8.0, 55.0)
cam.location = (-130.0, -210.0, 120.0)
exploded_png = os.path.join(OUTPUT_DIR, "render_v7_exploded_assembly.png")
scene.render.filepath = exploded_png
print(f"Rendering Exploded Assembly View -> {exploded_png}...")
bpy.ops.render.render(write_still=True)
print("Exploded assembly render complete!")

print("=== All V7 Final Studio Renders Successfully Generated! ===")
