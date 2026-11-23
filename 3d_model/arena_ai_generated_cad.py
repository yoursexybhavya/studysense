import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

# ==============================================================================
# 1. GLOBAL DIMENSIONS & TOLERANCES (1 Blender Unit = 1.0 mm for Bambu Studio)
# ==============================================================================
TOLERANCE = 0.15  # 0.2mm nozzle radial clearance

# Head Unit (Full 360° Circular Pod)
HEAD_OD = 70.0
HEAD_R = HEAD_OD / 2.0        # 35.0 mm
HEAD_DEPTH = 30.0             # Y: -15.0 (front) to +15.0 (rear)
HEAD_CENTER_Z = 150.0
HEAD_FRONT_Y = -15.0
HEAD_REAR_Y = 15.0

# Accent Halo Ring (Orange/Red)
RING_OD = 65.0
RING_ID = 61.8
RING_THICK = 2.5

# Front Faceplate (Black)
FACE_NOMINAL_D = 62.0
FACE_MATING_D = RING_ID - (TOLERANCE * 1.5)  # 61.57 mm (slides cleanly inside Ring)
FACE_THICK = 2.5
PIR_HOLE_D = 23.4
PIR_OFFSET_Z = 11.5           # Z = 161.5 mm
US_HOLE_D = 16.3
US_SPACING_X = 26.0           # +/- 13.0 mm center-to-center
US_OFFSET_Z = -9.5            # Z = 140.5 mm
BRIDGE_W = 7.0
BRIDGE_H = 4.0
BRIDGE_OFFSET_Z = -1.5        # Z = 148.5 mm

# Vertical Neck / Stem (105 mm tall from Z=36 to Z=141)
BASE_HEIGHT = 36.0
NECK_HEIGHT = 105.0
NECK_TOP_Z = BASE_HEIGHT + NECK_HEIGHT  # 141.0 mm
CONDUIT_W = 20.0
CONDUIT_D = 14.0
LED_HOLE_D = 5.2
LED_Z_POSITIONS = [72.0, 82.0, 92.0]    # 10 mm vertical spacing

# Base & Desktop Stand (76mm W x 88mm D x 36mm H)
BASE_W = 76.0
BASE_D = 88.0                 # Y: -26.0 (front toe) to +62.0 (rear heel)
BASE_SLOPE_DEG = 14.0
ESP32_W = 28.5
ESP32_L = 52.0
ESP32_H = 12.0
USB_SLOT_W = 13.0
USB_SLOT_H = 7.5
BTN_HOLE_D = 7.0
BTN_Z = 24.0

# Output directory inside project
OUTPUT_DIR = "/Users/krishnajangid/Documents/Idea Lab/3d_model/arena_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = 'MILLIMETERS'

def get_or_create_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col

def create_obj_from_bmesh(name, bm, collection):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def boolean_op(target_obj, cutter_obj, operation='DIFFERENCE', solver='EXACT', delete_cutter=True):
    bpy.context.view_layer.objects.active = target_obj
    target_obj.select_set(True)
    mod = target_obj.modifiers.new(name=f"Bool_{operation}", type='BOOLEAN')
    mod.operation = operation
    mod.object = cutter_obj
    mod.solver = solver
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception:
        mod.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if delete_cutter:
        bpy.data.objects.remove(cutter_obj, do_unlink=True)

def apply_sharp_edges_and_smooth(obj, angle_deg=35.0):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for f in obj.data.polygons:
        f.use_smooth = True
    if hasattr(obj.data, "use_auto_smooth"):
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians(angle_deg)

def make_cylinder_y(name, radius, y_start, y_end, cx=0.0, cz=0.0, segs=96, collection=None):
    bm = bmesh.new()
    length = abs(y_end - y_start)
    y_mid = (y_start + y_end) / 2.0
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segs,
        radius1=radius, radius2=radius, depth=length,
        matrix=Matrix.Rotation(math.radians(90.0), 4, 'X') @ Matrix.Translation(Vector((cx, cz, 0.0)))
    )
    for v in bm.verts:
        v.co.y += y_mid
    return create_obj_from_bmesh(name, bm, collection)

def make_cube_centered(name, sx, sy, sz, collection):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    return create_obj_from_bmesh(name, bm, collection)

def rounded_rect_pts(w, d, r, cx=0.0, cy=0.0, n_corner=8):
    r = min(r, w * 0.49, d * 0.49)
    hw = (w / 2.0) - r
    hd = (d / 2.0) - r
    pts = []
    corners = [
        (hw, hd, 0.0, math.pi * 0.5),
        (-hw, hd, math.pi * 0.5, math.pi),
        (-hw, -hd, math.pi, math.pi * 1.5),
        (hw, -hd, math.pi * 1.5, math.pi * 2.0)
    ]
    for ocx, ocy, a_start, a_end in corners:
        for i in range(n_corner):
            ang = a_start + (a_end - a_start) * (i / float(n_corner))
            pts.append(Vector((cx + ocx + r * math.cos(ang), cy + ocy + r * math.sin(ang))))
    return pts

def build_lofted_solid(name, z_sections, collection):
    bm = bmesh.new()
    ring_loops = []
    for z_elev, poly in z_sections:
        verts = [bm.verts.new((p.x, p.y, z_elev)) for p in poly]
        ring_loops.append(verts)
    bm.faces.new(list(reversed(ring_loops[0])))
    n_pts = len(ring_loops[0])
    for s_idx in range(len(ring_loops) - 1):
        r_curr = ring_loops[s_idx]
        r_next = ring_loops[s_idx + 1]
        for i in range(n_pts):
            ni = (i + 1) % n_pts
            bm.faces.new((r_curr[i], r_curr[ni], r_next[ni], r_next[i]))
    bm.faces.new(ring_loops[-1])
    return create_obj_from_bmesh(name, bm, collection)

def make_rounded_box_y(name, w, h, r, y_start, y_end, cx=0.0, cz=0.0, n_corner=8, collection=None):
    pts_xz = rounded_rect_pts(w, h, r, cx=cx, cy=cz, n_corner=n_corner)
    bm = bmesh.new()
    r0 = [bm.verts.new((p.x, y_start, p.y)) for p in pts_xz]
    r1 = [bm.verts.new((p.x, y_end, p.y)) for p in pts_xz]
    bm.faces.new(list(reversed(r0)))
    n_pts = len(pts_xz)
    for i in range(n_pts):
        ni = (i + 1) % n_pts
        bm.faces.new((r0[i], r0[ni], r1[ni], r1[i]))
    bm.faces.new(r1)
    return create_obj_from_bmesh(name, bm, collection)

def build_part_01_base(col):
    base_sections = [
        (0.0, rounded_rect_pts(BASE_W, BASE_D, 8.5, cx=0.0, cy=18.0)),
        (10.0, rounded_rect_pts(BASE_W, BASE_D - 1.5, 8.0, cx=0.0, cy=18.0)),
        (20.0, rounded_rect_pts(BASE_W - 4.0, BASE_D - 8.0, 7.5, cx=0.0, cy=15.0)),
        (28.0, rounded_rect_pts(BASE_W - 8.0, BASE_D - 16.0, 7.0, cx=0.0, cy=12.0)),
        (BASE_HEIGHT, rounded_rect_pts(BASE_W - 14.0, 36.0, 6.5, cx=0.0, cy=2.0)),
    ]
    base_obj = build_lofted_solid("01_Base_Lower_Stand", base_sections, col)

    toe_cut = make_cube_centered("Temp_Toe_Cut", 84.0, 32.0, 30.0, col)
    toe_cut.rotation_euler = (math.radians(-BASE_SLOPE_DEG), 0.0, 0.0)
    toe_cut.location = (0.0, -18.0, 22.0)
    boolean_op(base_obj, toe_cut, operation='DIFFERENCE', delete_cutter=True)

    pocket_sections = [
        (2.5,  rounded_rect_pts(BASE_W - 12.0, BASE_D - 20.0, 5.0, cx=0.0, cy=24.0)),
        (24.0, rounded_rect_pts(BASE_W - 16.0, BASE_D - 28.0, 5.0, cx=0.0, cy=20.0)),
        (BASE_HEIGHT - 3.0, rounded_rect_pts(BASE_W - 24.0, 26.0, 4.0, cx=0.0, cy=4.0)),
    ]
    cavity_cutter = build_lofted_solid("Temp_Base_Cavity", pocket_sections, col)
    boolean_op(base_obj, cavity_cutter, operation='DIFFERENCE', delete_cutter=True)

    usb_slot = make_rounded_box_y(
        "Temp_USB_Slot", USB_SLOT_W, USB_SLOT_H, 1.5,
        y_start=50.0, y_end=64.0, cx=0.0, cz=4.95, collection=col
    )
    boolean_op(base_obj, usb_slot, operation='DIFFERENCE', delete_cutter=True)

    btn_hole = make_cylinder_y(
        "Temp_Btn_Hole", BTN_HOLE_D * 0.5,
        y_start=28.0, y_end=58.0,
        cx=0.0, cz=BTN_Z, segs=48, collection=col
    )
    boolean_op(base_obj, btn_hole, operation='DIFFERENCE', delete_cutter=True)

    apply_sharp_edges_and_smooth(base_obj, angle_deg=35.0)
    return base_obj

def build_part_02_neck_and_head(col):
    head_obj = make_cylinder_y(
        "02_Neck_and_Head_Shell", HEAD_R,
        y_start=HEAD_FRONT_Y, y_end=HEAD_REAR_Y,
        cx=0.0, cz=HEAD_CENTER_Z, segs=128, collection=col
    )

    fin_sections = [
        (HEAD_CENTER_Z + 18.0, rounded_rect_pts(11.0, 16.0, 3.0, cx=0.0, cy=12.0)),
        (HEAD_CENTER_Z + 36.0, rounded_rect_pts(9.0, 10.0, 2.5, cx=0.0, cy=16.0)),
        (HEAD_CENTER_Z + 41.0, rounded_rect_pts(7.0, 6.0, 1.8, cx=0.0, cy=18.5)),
    ]
    fin_obj = build_lofted_solid("Temp_Head_Fin", fin_sections, col)
    boolean_op(head_obj, fin_obj, operation='UNION', delete_cutter=True)

    neck_sections = [
        (31.5, rounded_rect_pts(34.0 - TOLERANCE * 2, 22.0 - TOLERANCE * 2, 6.0, cx=0.0, cy=1.0)),
        (36.0, rounded_rect_pts(46.0, 28.0, 6.8, cx=0.0, cy=1.0)),
        (65.0, rounded_rect_pts(39.0, 24.5, 6.2, cx=0.0, cy=2.0)),
        (95.0, rounded_rect_pts(33.5, 21.5, 5.6, cx=0.0, cy=3.0)),
        (118.0, rounded_rect_pts(29.5, 20.0, 5.2, cx=0.0, cy=3.8)),
        (141.0, rounded_rect_pts(27.0, 18.5, 5.0, cx=0.0, cy=4.5)),
    ]
    neck_obj = build_lofted_solid("Temp_Neck_Body", neck_sections, col)
    boolean_op(head_obj, neck_obj, operation='UNION', delete_cutter=True)

    ring_recess = make_cylinder_y(
        "Temp_Ring_Recess", (RING_OD * 0.5) + TOLERANCE,
        y_start=-16.5, y_end=HEAD_FRONT_Y + RING_THICK,
        cx=0.0, cz=HEAD_CENTER_Z, segs=128, collection=col
    )
    boolean_op(head_obj, ring_recess, operation='DIFFERENCE', delete_cutter=True)

    head_chamber = make_cylinder_y(
        "Temp_Head_Chamber", 28.8,
        y_start=-13.5, y_end=11.2,
        cx=0.0, cz=HEAD_CENTER_Z, segs=96, collection=col
    )
    boolean_op(head_obj, head_chamber, operation='DIFFERENCE', delete_cutter=True)

    conduit_sections = [
        (31.0,  rounded_rect_pts(CONDUIT_W, CONDUIT_D, 3.0, cx=0.0, cy=1.5)),
        (90.0,  rounded_rect_pts(CONDUIT_W, CONDUIT_D, 3.0, cx=0.0, cy=2.8)),
        (142.0, rounded_rect_pts(CONDUIT_W, CONDUIT_D, 3.0, cx=0.0, cy=3.5)),
    ]
    conduit_cutter = build_lofted_solid("Temp_Wire_Conduit", conduit_sections, col)
    boolean_op(head_obj, conduit_cutter, operation='DIFFERENCE', delete_cutter=True)

    for idx, led_z in enumerate(LED_Z_POSITIONS):
        led_cutter = make_cylinder_y(
            f"Temp_LED_Hole_{idx}", LED_HOLE_D * 0.5,
            y_start=-18.0, y_end=2.5,
            cx=0.0, cz=led_z, segs=48, collection=col
        )
        boolean_op(head_obj, led_cutter, operation='DIFFERENCE', delete_cutter=True)

    apply_sharp_edges_and_smooth(head_obj, angle_deg=35.0)
    return head_obj

def build_part_03_faceplate(col):
    face_r = FACE_MATING_D * 0.5
    face_obj = make_cylinder_y(
        "03_Sensor_Faceplate_Black", face_r,
        y_start=-14.8, y_end=-12.3,
        cx=0.0, cz=HEAD_CENTER_Z, segs=128, collection=col
    )
    pir_cut = make_cylinder_y(
        "Temp_PIR_Cut", PIR_HOLE_D * 0.5,
        y_start=-17.0, y_end=-6.0,
        cx=0.0, cz=HEAD_CENTER_Z + PIR_OFFSET_Z, segs=72, collection=col
    )
    boolean_op(face_obj, pir_cut, operation='DIFFERENCE', delete_cutter=True)

    for side in (-1, 1):
        us_cut = make_cylinder_y(
            f"Temp_US_Cut_{side}", US_HOLE_D * 0.5,
            y_start=-17.0, y_end=-4.0,
            cx=side * (US_SPACING_X * 0.5), cz=HEAD_CENTER_Z + US_OFFSET_Z, segs=64, collection=col
        )
        boolean_op(face_obj, us_cut, operation='DIFFERENCE', delete_cutter=True)

    bridge_cut = make_rounded_box_y(
        "Temp_Bridge_Cut", BRIDGE_W, BRIDGE_H, 1.2,
        y_start=-16.0, y_end=-11.0,
        cx=0.0, cz=HEAD_CENTER_Z + BRIDGE_OFFSET_Z, n_corner=8, collection=col
    )
    boolean_op(face_obj, bridge_cut, operation='DIFFERENCE', delete_cutter=True)

    apply_sharp_edges_and_smooth(face_obj, angle_deg=35.0)
    return face_obj

def build_part_04_accent_ring(col):
    segs = 128
    r_out = RING_OD * 0.5
    r_in = RING_ID * 0.5
    y_front = HEAD_FRONT_Y - 0.15
    y_back = HEAD_FRONT_Y + RING_THICK

    profile = [
        (r_in + 0.25, y_front),
        (r_out - 0.25, y_front),
        (r_out, y_front + 0.35),
        (r_out, y_back),
        (r_in, y_back),
        (r_in, y_front + 0.35),
    ]

    bm = bmesh.new()
    rings = []
    for rad, y_val in profile:
        ring = []
        for i in range(segs):
            ang = 2.0 * math.pi * i / segs
            x = rad * math.cos(ang)
            z = HEAD_CENTER_Z + rad * math.sin(ang)
            ring.append(bm.verts.new((x, y_val, z)))
        rings.append(ring)

    n_p = len(rings)
    for k in range(n_p):
        r0 = rings[k]
        r1 = rings[(k + 1) % n_p]
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((r0[i], r0[ni], r1[ni], r1[i]))

    ring_obj = create_obj_from_bmesh("04_Accent_Ring_Orange", bm, col)
    apply_sharp_edges_and_smooth(ring_obj, angle_deg=35.0)
    return ring_obj

def build_part_05_button_cap(col):
    cap_obj = make_cylinder_y(
        "05_Button_Cap", 3.3,
        y_start=15.0, y_end=21.2,
        cx=0.0, cz=BTN_Z, segs=48, collection=col
    )
    apply_sharp_edges_and_smooth(cap_obj, angle_deg=35.0)
    return cap_obj

def main():
    reset_scene()
    col = get_or_create_collection("StudySense_Arena_Model")
    p1 = build_part_01_base(col)
    p2 = build_part_02_neck_and_head(col)
    p3 = build_part_03_faceplate(col)
    p4 = build_part_04_accent_ring(col)
    p5 = build_part_05_button_cap(col)

    for obj in [p1, p2, p3, p4, p5]:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        path = os.path.join(OUTPUT_DIR, f"{obj.name}.stl")
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
        print(f"Exported Arena CAD part: {path}")

    print("=== Arena AI CAD Generation Complete ===")

if __name__ == "__main__":
    main()
