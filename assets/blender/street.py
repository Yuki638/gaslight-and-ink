import bpy
import bmesh
import math
import json
import os
from mathutils import Vector, Matrix, Euler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "export")
RENDER_DIR = os.path.join(ROOT, "renders")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

BUDGETS = {
    "Barrel": 1200,
    "Crate": 800,
    "Bench": 2500,
    "PillarBox": 1500,
    "HandCart": 3000,
}

# ---------------------------------------------------------------------------
# Scene & Material Helpers
# ---------------------------------------------------------------------------

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.materials,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def make_material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Metallic"].default_value = metallic
            bsdf.inputs["Roughness"].default_value = roughness
    return mat


def create_materials():
    return {
        "Iron": make_material("Iron", (0.072, 0.086, 0.110), metallic=0.80, roughness=0.35),
        "Wood": make_material("Wood", (0.120, 0.058, 0.026), metallic=0.0, roughness=0.68),
        "Brass": make_material("Brass", (0.62, 0.39, 0.12), metallic=0.82, roughness=0.27),
    }


# ---------------------------------------------------------------------------
# BMesh Geometry Builders (pure quads/tris, outward normals, clean bevels)
# ---------------------------------------------------------------------------

def finalize_bmesh(bm, name, material, smooth_angle_deg=35.0):
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=list(bm.edges))
    bm.normal_update()

    # Triangulate any n-gons (keeps quads intact, eliminates n-gons everywhere)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="BEAUTY")

    # Apply smooth shading + Smooth by Angle (~35 deg) via sharp edges
    threshold = math.radians(smooth_angle_deg)
    for f in bm.faces:
        f.smooth = True
    bm.edges.ensure_lookup_table()
    for e in bm.edges:
        if len(e.link_faces) == 2:
            ang = e.calc_face_angle(0.0)
            e.smooth = ang <= threshold
        else:
            e.smooth = False

    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_box(bm, center, size, rot=None, bevel=0.0, bevel_segs=2, skip_faces=None):
    """Add an oriented box with optional 2-segment bevel and optional hidden-face removal."""
    sx, sy, sz = size
    cx, cy, cz = center
    rot_m = Euler(rot, "XYZ").to_matrix().to_4x4() if rot else Matrix.Identity(4)
    xf = Matrix.Translation(Vector((cx, cy, cz))) @ rot_m

    sub = bmesh.new()
    bmesh.ops.create_cube(sub, size=1.0)
    for v in sub.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bmesh.ops.recalc_face_normals(sub, faces=list(sub.faces))

    if bevel > 0.0:
        bmesh.ops.bevel(
            sub,
            geom=list(sub.edges),
            offset=bevel,
            offset_type="OFFSET",
            segments=bevel_segs,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
        )

    if skip_faces:
        to_del = []
        dir_map = {
            "+x": Vector((1, 0, 0)),
            "-x": Vector((-1, 0, 0)),
            "+y": Vector((0, 1, 0)),
            "-y": Vector((0, -1, 0)),
            "+z": Vector((0, 0, 1)),
            "-z": Vector((0, 0, -1)),
        }
        sub.normal_update()
        for f in sub.faces:
            for key in skip_faces:
                if f.normal.dot(dir_map[key]) > 0.95:
                    to_del.append(f)
                    break
        if to_del:
            bmesh.ops.delete(sub, geom=to_del, context="FACES")

    bmesh.ops.transform(sub, matrix=xf, verts=list(sub.verts))
    merge_bmesh(bm, sub)
    sub.free()


def merge_bmesh(dst, src):
    vert_map = {}
    for v in src.verts:
        vert_map[v] = dst.verts.new(v.co)
    for f in src.faces:
        try:
            nf = dst.faces.new([vert_map[v] for v in f.verts])
            nf.smooth = f.smooth
        except ValueError:
            pass


def add_cylinder(bm, center, radius1, radius2, depth, segs=16, rot=None, cap_ends=True, bevel_ends=0.0):
    """Add a clean tapered cylinder/cone with optional beveled ends and no n-gons."""
    sub = bmesh.new()
    z0 = -depth * 0.5
    z1 = depth * 0.5

    if bevel_ends > 0.0 and depth > bevel_ends * 2.5:
        b = bevel_ends
        profile = [
            (z0, max(0.002, radius1 - b)),
            (z0 + b * 0.35, max(0.002, radius1 - b * 0.3)),
            (z0 + b, radius1),
            (z1 - b, radius2),
            (z1 - b * 0.35, max(0.002, radius2 - b * 0.3)),
            (z1, max(0.002, radius2 - b)),
        ]
    else:
        profile = [(z0, radius1), (z1, radius2)]

    rings = []
    for z, r in profile:
        ring = []
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            ring.append(sub.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)

    for j in range(len(rings) - 1):
        r0, r1 = rings[j], rings[j + 1]
        for i in range(segs):
            ni = (i + 1) % segs
            sub.faces.new((r0[i], r0[ni], r1[ni], r1[i]))

    if cap_ends:
        bot_c = sub.verts.new((0.0, 0.0, z0))
        top_c = sub.verts.new((0.0, 0.0, z1))
        for i in range(segs):
            ni = (i + 1) % segs
            sub.faces.new((bot_c, rings[0][ni], rings[0][i]))
            sub.faces.new((top_c, rings[-1][i], rings[-1][ni]))

    rot_m = Euler(rot, "XYZ").to_matrix().to_4x4() if rot else Matrix.Identity(4)
    xf = Matrix.Translation(Vector(center)) @ rot_m
    bmesh.ops.transform(sub, matrix=xf, verts=list(sub.verts))
    merge_bmesh(bm, sub)
    sub.free()


def add_beam(bm, p0, p1, w, h=None, bevel=0.0, bevel_segs=2, skip_ends=False):
    if h is None:
        h = w
    a = Vector(p0)
    b = Vector(p1)
    vec = b - a
    length = vec.length
    if length < 1e-6:
        return
    mid = (a + b) * 0.5
    rot = vec.to_track_quat("Z", "Y").to_euler()
    skip = {"+z", "-z"} if skip_ends else None
    add_box(bm, mid, (w, h, length), rot=rot, bevel=bevel, bevel_segs=bevel_segs, skip_faces=skip)


def add_lathe_rings(bm, profile, segs=24, cap_bottom=True, cap_top=True, phase=0.0):
    """Profile: list of (z, r). Caps use clean triangle fans (no n-gons)."""
    sub = bmesh.new()
    rings = []
    for z, r in profile:
        ring = []
        for i in range(segs):
            a = 2.0 * math.pi * i / segs + phase
            ring.append(sub.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)

    for j in range(len(rings) - 1):
        r0, r1 = rings[j], rings[j + 1]
        for i in range(segs):
            ni = (i + 1) % segs
            sub.faces.new((r0[i], r0[ni], r1[ni], r1[i]))

    if cap_bottom and profile[0][1] > 1e-5:
        c = sub.verts.new((0.0, 0.0, profile[0][0]))
        for i in range(segs):
            ni = (i + 1) % segs
            sub.faces.new((c, rings[0][ni], rings[0][i]))

    if cap_top and profile[-1][1] > 1e-5:
        c = sub.verts.new((0.0, 0.0, profile[-1][0]))
        for i in range(segs):
            ni = (i + 1) % segs
            sub.faces.new((c, rings[-1][i], rings[-1][ni]))

    merge_bmesh(bm, sub)
    sub.free()


def add_swept_bar_yz(bm, points_yz, x_center, thickness_x, width_yz, closed=False, cap_ends=True):
    """Sweep a rectangular bar along a 2D polyline in the YZ plane at X = x_center."""
    sub = bmesh.new()
    n = len(points_yz)
    if n < 2:
        sub.free()
        return

    hx = thickness_x * 0.5
    hw = width_yz * 0.5
    rings = []

    for i, (y, z) in enumerate(points_yz):
        if closed:
            p_prev = Vector((0.0, points_yz[(i - 1) % n][0], points_yz[(i - 1) % n][1]))
            p_next = Vector((0.0, points_yz[(i + 1) % n][0], points_yz[(i + 1) % n][1]))
            t1 = (Vector((0.0, y, z)) - p_prev).normalized()
            t2 = (p_next - Vector((0.0, y, z))).normalized()
            tang = (t1 + t2)
            tang = tang.normalized() if tang.length > 1e-6 else t1
        elif i == 0:
            tang = (Vector((0.0, points_yz[1][0], points_yz[1][1])) - Vector((0.0, y, z))).normalized()
        elif i == n - 1:
            tang = (Vector((0.0, y, z)) - Vector((0.0, points_yz[-2][0], points_yz[-2][1]))).normalized()
        else:
            t1 = (Vector((0.0, y, z)) - Vector((0.0, points_yz[i - 1][0], points_yz[i - 1][1]))).normalized()
            t2 = (Vector((0.0, points_yz[i + 1][0], points_yz[i + 1][1])) - Vector((0.0, y, z))).normalized()
            tang = t1 + t2
            tang = tang.normalized() if tang.length > 1e-6 else t1

        # Normal in YZ plane perpendicular to tangent
        norm = Vector((0.0, -tang.z, tang.y)).normalized()
        p = Vector((x_center, y, z))

        # 4 corners of cross-section ordered CCW around +tangent
        v0 = sub.verts.new(p + Vector((-hx, 0, 0)) - norm * hw)
        v1 = sub.verts.new(p + Vector((hx, 0, 0)) - norm * hw)
        v2 = sub.verts.new(p + Vector((hx, 0, 0)) + norm * hw)
        v3 = sub.verts.new(p + Vector((-hx, 0, 0)) + norm * hw)
        rings.append((v0, v1, v2, v3))

    seg_count = n if closed else n - 1
    for j in range(seg_count):
        r0 = rings[j]
        r1 = rings[(j + 1) % n]
        for k in range(4):
            nk = (k + 1) % 4
            sub.faces.new((r0[k], r0[nk], r1[nk], r1[k]))

    if not closed and cap_ends:
        sub.faces.new((rings[0][3], rings[0][2], rings[0][1], rings[0][0]))
        sub.faces.new((rings[-1][0], rings[-1][1], rings[-1][2], rings[-1][3]))

    bmesh.ops.recalc_face_normals(sub, faces=list(sub.faces))
    merge_bmesh(bm, sub)
    sub.free()


def add_curved_plate(bm, r_inner, r_outer, z0, z1, ang_start, ang_end, segs=6):
    """Curved cylindrical shell segment (solid manifold block conforming to Z-cylinder)."""
    sub = bmesh.new()
    verts = []  # [s][4]: (in_bot, out_bot, out_top, in_top)
    for s in range(segs + 1):
        a = ang_start + (ang_end - ang_start) * (s / segs)
        ca, sa = math.cos(a), math.sin(a)
        v_ib = sub.verts.new((r_inner * ca, r_inner * sa, z0))
        v_ob = sub.verts.new((r_outer * ca, r_outer * sa, z0))
        v_ot = sub.verts.new((r_outer * ca, r_outer * sa, z1))
        v_it = sub.verts.new((r_inner * ca, r_inner * sa, z1))
        verts.append((v_ib, v_ob, v_ot, v_it))

    for s in range(segs):
        a0 = verts[s]
        a1 = verts[s + 1]
        # outer face
        sub.faces.new((a0[1], a1[1], a1[2], a0[2]))
        # top face
        sub.faces.new((a0[2], a1[2], a1[3], a0[3]))
        # bottom face
        sub.faces.new((a0[0], a0[1], a1[1], a1[0]))
        # omit inner face? Keep if needed; since r_inner is embedded in shaft, omit inner hidden face!

    # End caps (left and right sides)
    sub.faces.new((verts[0][0], verts[0][3], verts[0][2], verts[0][1]))
    sub.faces.new((verts[-1][1], verts[-1][2], verts[-1][3], verts[-1][0]))

    merge_bmesh(bm, sub)
    sub.free()


def add_beveled_slat(bm, x0, x1, y_center, z_center, width, thickness, tilt_rad=0.0):
    """Extruded wooden bench slat along X with 2-segment beveled long edges and crisp ends."""
    sub = bmesh.new()
    hw = width * 0.5
    ht = thickness * 0.5
    b = min(hw, ht) * 0.28

    # 12-point rounded rectangle in YZ plane (2-segment bevel on all 4 corners)
    c45 = 0.70710678
    k = b * (1.0 - c45)
    pts_2d = [
        (hw - b, -ht),
        (hw - k, -ht + k),
        (hw, -ht + b),
        (hw, ht - b),
        (hw - k, ht - k),
        (hw - b, ht),
        (-hw + b, ht),
        (-hw + k, ht - k),
        (-hw, ht - b),
        (-hw, -ht + b),
        (-hw + k, -ht + k),
        (-hw + b, -ht),
    ]
    ct = math.cos(tilt_rad)
    st = math.sin(tilt_rad)

    def xform(x, py, pz):
        ry = py * ct - pz * st + y_center
        rz = py * st + pz * ct + z_center
        return (x, ry, rz)

    # Two end stations (keeps 2-segment beveled long profile while staying lean on tris)
    x_stations = [
        (x0, 1.0),
        (x1, 1.0),
    ]

    rings = []
    for xs, sc in x_stations:
        ring = [sub.verts.new(xform(xs, py * sc, pz * sc)) for (py, pz) in pts_2d]
        rings.append(ring)

    m = len(pts_2d)
    for j in range(len(rings) - 1):
        r0, r1 = rings[j], rings[j + 1]
        for i in range(m):
            ni = (i + 1) % m
            sub.faces.new((r0[i], r0[ni], r1[ni], r1[i]))

    # Cap ends with triangle fan from center
    c_left = sub.verts.new(xform(x0, 0.0, 0.0))
    c_right = sub.verts.new(xform(x1, 0.0, 0.0))
    for i in range(m):
        ni = (i + 1) % m
        sub.faces.new((c_left, rings[0][ni], rings[0][i]))
        sub.faces.new((c_right, rings[-1][i], rings[-1][ni]))

    bmesh.ops.recalc_face_normals(sub, faces=list(sub.faces))
    merge_bmesh(bm, sub)
    sub.free()


# ---------------------------------------------------------------------------
# 1. BARREL (<= 1200 tris) — Barrel_Wood, Barrel_Iron
# ---------------------------------------------------------------------------

def build_barrel(mats):
    bm_wood = bmesh.new()
    bm_iron = bmesh.new()

    H = 3.2
    r_mid = 1.06
    r_end = 0.83
    n_staves = 12

    def barrel_r(z):
        t = (z - H * 0.5) / (H * 0.5)
        return r_mid - (r_mid - r_end) * (t * t)

    # Angular profile: 3 verts per stave (seam groove + left stave shoulder + right stave shoulder)
    ang_profile = []
    dtheta = 2.0 * math.pi / n_staves
    for i in range(n_staves):
        base = i * dtheta
        ang_profile.append((base, 0.964))                  # visible recessed stave seam
        ang_profile.append((base + 0.13 * dtheta, 1.000))  # stave left edge
        ang_profile.append((base + 0.87 * dtheta, 1.000))  # stave right edge
    n_rad = len(ang_profile)  # 36

    # Vertical stations for outer bulged wall + recessed top chime (6 rings -> smooth bulge under 1200 tris)
    z_outer = [0.0, 0.52, 1.22, 1.98, 2.68, 3.20]
    rings = []
    for z in z_outer:
        rz = barrel_r(z)
        ring = []
        for ang, scale in ang_profile:
            r = rz * scale
            ring.append(bm_wood.verts.new((r * math.cos(ang), r * math.sin(ang), z)))
        rings.append(ring)

    # Top chime inner lip & recessed lid
    r_chime_in = r_end - 0.09
    z_lid = H - 0.16
    ring_lip = []
    ring_lid = []
    for ang, _ in ang_profile:
        ring_lip.append(bm_wood.verts.new((r_chime_in * math.cos(ang), r_chime_in * math.sin(ang), H)))
        ring_lid.append(bm_wood.verts.new((r_chime_in * math.cos(ang), r_chime_in * math.sin(ang), z_lid)))
    rings.append(ring_lip)
    rings.append(ring_lid)

    for j in range(len(rings) - 1):
        r0, r1 = rings[j], rings[j + 1]
        for i in range(n_rad):
            ni = (i + 1) % n_rad
            bm_wood.faces.new((r0[i], r0[ni], r1[ni], r1[i]))

    # Recessed top head & flat bottom cap (clean triangle fans, no n-gons)
    top_c = bm_wood.verts.new((0.0, 0.0, z_lid))
    bot_c = bm_wood.verts.new((0.0, 0.0, 0.0))
    for i in range(n_rad):
        ni = (i + 1) % n_rad
        bm_wood.faces.new((top_c, rings[-1][i], rings[-1][ni]))
        bm_wood.faces.new((bot_c, rings[0][ni], rings[0][i]))

    # Small tapered wooden bung plug set cleanly off-center on the recessed top head
    add_cylinder(
        bm_wood,
        center=(0.24, -0.26, z_lid + 0.032),
        radius1=0.092,
        radius2=0.078,
        depth=0.07,
        segs=8,
        cap_ends=True,
    )

    # 3 Iron hoops conforming tightly to the barrel bulge (bottom, bilge, top)
    hoop_specs = [
        (0.28, 0.20, 0.042),
        (1.60, 0.21, 0.044),
        (2.92, 0.20, 0.042),
    ]
    hoop_segs = 22
    for z_mid, h_hoop, proud in hoop_specs:
        z_bot = z_mid - h_hoop * 0.5
        z_top = z_mid + h_hoop * 0.5
        rb_in = barrel_r(z_bot) - 0.035
        rb_out = barrel_r(z_bot) + proud
        rt_out = barrel_r(z_top) + proud
        rt_in = barrel_r(z_top) - 0.035

        # Beveled hoop profile (5 points -> 4 quad strips, inner face omitted as buried in wood)
        bev = 0.018
        prof = [
            (z_bot, rb_in),
            (z_bot, rb_out - bev),
            (z_bot + bev, rb_out),
            (z_top - bev, rt_out),
            (z_top, rt_out - bev),
            (z_top, rt_in),
        ]
        # Wait: 5 strips * 22 * 2 = 220 tris per hoop -> 660 tris -> keep 4 strips for budget!
        prof = [
            (z_bot, rb_in),
            (z_bot + bev * 0.6, rb_out),
            (z_top - bev * 0.6, rt_out),
            (z_top, rt_in),
        ]
        # Actually 3 strips (bottom bevel lip, outer band, top bevel lip) = 3 * 22 * 2 = 132 tris/hoop -> 396 tris!
        # Let's use 4 strips with a crisp top & bottom chamfer: 4 * 20 * 2 = 160 tris/hoop -> 480 tris!
        prof = [
            (z_bot, rb_in),
            (z_bot, rb_out - bev),
            (z_bot + bev, rb_out),
            (z_top - bev, rt_out),
            (z_top, rt_out - bev),
            (z_top, rt_in),
        ]
        # 5 strips * 18 segs * 2 = 180 tris/hoop * 3 = 540 tris!
        # Wood is 576 + 24 = 600 tris. 600 + 540 = 1140 tris (< 1200)!
        sub = bmesh.new()
        h_segs = 18
        h_rings = []
        for z, r in prof:
            ring = []
            for i in range(h_segs):
                a = 2.0 * math.pi * i / h_segs
                ring.append(sub.verts.new((r * math.cos(a), r * math.sin(a), z)))
            h_rings.append(ring)
        for j in range(len(h_rings) - 1):
            r0, r1 = h_rings[j], h_rings[j + 1]
            for i in range(h_segs):
                ni = (i + 1) % h_segs
                sub.faces.new((r0[i], r0[ni], r1[ni], r1[i]))
        merge_bmesh(bm_iron, sub)
        sub.free()

    obj_wood = finalize_bmesh(bm_wood, "Barrel_Wood", mats["Wood"], smooth_angle_deg=35.0)
    obj_iron = finalize_bmesh(bm_iron, "Barrel_Iron", mats["Iron"], smooth_angle_deg=35.0)
    return [obj_wood, obj_iron]


# ---------------------------------------------------------------------------
# 2. CRATE (<= 800 tris) — Crate_Wood, Crate_Iron
# ---------------------------------------------------------------------------

def build_crate(mats):
    bm_wood = bmesh.new()
    bm_iron = bmesh.new()

    # Exact 3 x 3 x 3 studs (X: -1.5..1.5, Y: -1.5..1.5, Z: 0.0..3.0)
    # Recessed inner wooden core behind plank gaps so crate is solid with shadowed gaps
    add_box(bm_wood, (0.0, 0.0, 1.5), (2.62, 2.62, 2.62))

    # Plank faces with visible gaps (4 planks per side wall + 4 planks on top)
    # Planks sit at +/-1.365 (recessed slightly inside the 3.0 outer corner battens)
    plank_span = 2.48
    plank_thick = 0.11
    plank_w = 0.54
    gap = 0.06
    pitch = plank_w + gap  # 0.60 -> 4 planks cover 2.34 inside the 2.48 opening

    for idx in range(4):
        offset = -1.5 * pitch + idx * pitch
        z_p = 1.5 + offset
        # Front (-Y) and Back (+Y)
        add_box(bm_wood, (0.0, -1.355, z_p), (plank_span, plank_thick, plank_w), skip_faces={"+y"})
        add_box(bm_wood, (0.0, 1.355, z_p), (plank_span, plank_thick, plank_w), skip_faces={"-y"})
        # Left (-X) and Right (+X)
        add_box(bm_wood, (-1.355, 0.0, z_p), (plank_thick, plank_span, plank_w), skip_faces={"+x"})
        add_box(bm_wood, (1.355, 0.0, z_p), (plank_thick, plank_span, plank_w), skip_faces={"-x"})
        # Top (+Z) planks running along X
        add_box(bm_wood, (0.0, offset, 2.855), (plank_span, plank_w, plank_thick), skip_faces={"-z"})

    # Outer wooden frame: corner battens + top/bottom perimeter rails (spans exact 3.0 x 3.0 x 3.0)
    # Keep wooden frame slightly inset (2.94) so iron corner brackets bring outer bounds to exact 3.00!
    batten_w = 0.28
    half_f = 1.47  # wood outer face at +/-1.47, Z: 0.03..2.97 -> iron brackets reach +/-1.50, Z: 0.0..3.0!
    # Wait: let wood bottom sit at Z=0.02 and iron corner brackets at Z=0.00..3.00 so exact 3x3x3!
    z_lo = 0.02
    z_hi = 2.98
    h_full = z_hi - z_lo

    # 4 vertical corner posts
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = sx * (half_f - batten_w * 0.5)
            cy = sy * (half_f - batten_w * 0.5)
            add_box(bm_wood, (cx, cy, 1.5), (batten_w, batten_w, h_full))

    # 8 horizontal top & bottom perimeter rails between corner posts
    rail_len = (half_f - batten_w) * 2.0
    for sz_c in (z_lo + batten_w * 0.5, z_hi - batten_w * 0.5):
        for sy in (-1, 1):
            add_box(
                bm_wood,
                (0.0, sy * (half_f - batten_w * 0.5), sz_c),
                (rail_len, batten_w, batten_w),
                skip_faces={"+x", "-x"},
            )
        for sx in (-1, 1):
            add_box(
                bm_wood,
                (sx * (half_f - batten_w * 0.5), 0.0, sz_c),
                (batten_w, rail_len, batten_w),
                skip_faces={"+y", "-y"},
            )

    # 4 diagonal wooden cross-braces on the 4 vertical faces (explicit wall-aligned orientation, flush inside 3x3x3)
    diag_len = (half_f - batten_w) * 2.0 * math.sqrt(2.0) - 0.08
    brace_d = 0.085
    brace_w = 0.22
    brace_offset = half_f - 0.045  # outer face at 1.4675 < 1.50
    # Front (-Y) and Back (+Y): rotate 45 deg around Y
    add_box(bm_wood, (0.0, -brace_offset, 1.5), (diag_len, brace_d, brace_w), rot=(0.0, math.radians(-45.0), 0.0), skip_faces={"+y", "+x", "-x"})
    add_box(bm_wood, (0.0, brace_offset, 1.5), (diag_len, brace_d, brace_w), rot=(0.0, math.radians(45.0), 0.0), skip_faces={"-y", "+x", "-x"})
    # Right (+X) and Left (-X): rotate 45 deg around X
    add_box(bm_wood, (brace_offset, 0.0, 1.5), (brace_d, diag_len, brace_w), rot=(math.radians(45.0), 0.0, 0.0), skip_faces={"-x", "+y", "-y"})
    add_box(bm_wood, (-brace_offset, 0.0, 1.5), (brace_d, diag_len, brace_w), rot=(math.radians(-45.0), 0.0, 0.0), skip_faces={"+x", "+y", "-y"})

    # 8 Iron corner brackets (Crate_Iron): unified 3-way wraparound steel/iron L-brackets at every corner
    # Outer corner sits at (+/-1.50, +/-1.50, 0.00 / 3.00) -> exact 3.0 x 3.0 x 3.0 dimensions!
    arm_len = 0.52
    strap_w = 0.22
    thick = 0.032

    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                ox = sx * 1.50
                oy = sy * 1.50
                oz = 1.50 + sz * 1.50  # 0.0 or 3.0

                # 3 orthogonal outer strap legs meeting cleanly at the corner cube
                # Corner cube (flush with all 3 legs)
                # Build each arm as a clean box wrapping the outer edge (no z-fighting between arms)
                # Arm along X (on outer Y and outer Z faces): wrap as L-angle iron?
                # Even cleaner & ultra low-poly: 3 flush iron plates at each corner with exact non-overlapping joins!
                # Plate 1 (normal Z, covering corner + X arm + Y arm): 2 boxes
                zc = oz - sz * (thick * 0.5)
                add_box(
                    bm_iron,
                    (ox - sx * (arm_len * 0.5), oy - sy * (strap_w * 0.5), zc),
                    (arm_len, strap_w, thick),
                    skip_faces={"-z" if sz > 0 else "+z"},
                )
                add_box(
                    bm_iron,
                    (ox - sx * (strap_w * 0.5), oy - sy * (strap_w + (arm_len - strap_w) * 0.5), zc),
                    (strap_w, arm_len - strap_w, thick),
                    skip_faces={"-z" if sz > 0 else "+z", "+y" if sy > 0 else "-y"},
                )

                # Plate 2 (normal Y, extending down Z and along X, below Plate 1)
                yc = oy - sy * (thick * 0.5)
                z_start = oz - sz * thick
                add_box(
                    bm_iron,
                    (ox - sx * (strap_w * 0.5), yc, z_start - sz * ((arm_len - thick) * 0.5)),
                    (strap_w, thick, arm_len - thick),
                    skip_faces={"-y" if sy > 0 else "+y", "+z" if sz > 0 else "-z"},
                )
                add_box(
                    bm_iron,
                    (ox - sx * (strap_w + (arm_len - strap_w) * 0.5), yc, z_start - sz * ((strap_w - thick) * 0.5)),
                    (arm_len - strap_w, thick, strap_w - thick),
                    skip_faces={"-y" if sy > 0 else "+y", "+x" if sx > 0 else "-x", "+z" if sz > 0 else "-z"},
                )

                # Plate 3 (normal X, extending down Z and along Y, inside Y & Z thickness)
                xc = ox - sx * (thick * 0.5)
                y_start = oy - sy * thick
                add_box(
                    bm_iron,
                    (xc, y_start - sy * ((strap_w - thick) * 0.5), z_start - sz * ((arm_len - thick) * 0.5)),
                    (thick, strap_w - thick, arm_len - thick),
                    skip_faces={"-x" if sx > 0 else "+x", "+y" if sy > 0 else "-y", "+z" if sz > 0 else "-z"},
                )
                add_box(
                    bm_iron,
                    (xc, oy - sy * (strap_w + (arm_len - strap_w) * 0.5), z_start - sz * ((strap_w - thick) * 0.5)),
                    (thick, arm_len - strap_w, strap_w - thick),
                    skip_faces={"-x" if sx > 0 else "+x", "+y" if sy > 0 else "-y", "+z" if sz > 0 else "-z"},
                )

    obj_wood = finalize_bmesh(bm_wood, "Crate_Wood", mats["Wood"], smooth_angle_deg=35.0)
    obj_iron = finalize_bmesh(bm_iron, "Crate_Iron", mats["Iron"], smooth_angle_deg=35.0)
    return [obj_wood, obj_iron]


# ---------------------------------------------------------------------------
# 3. BENCH (<= 2500 tris) — Bench_Iron, Bench_Wood
# ---------------------------------------------------------------------------

def sample_cubic_bezier(p0, p1, p2, p3, steps):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        y = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        z = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((y, z))
    return pts


def build_bench(mats):
    bm_iron = bmesh.new()
    bm_wood = bmesh.new()

    # Width = 6.0 studs (X: -3.0..3.0), facing -Y
    # 5 seat slats + 3 backrest slats = 8 wooden slats with beveled profiles
    seat_slats = [
        # (y_center, z_center, width, tilt_rad)
        (-0.84, 1.46, 0.25, math.radians(-18.0)),  # rolled front lip slat resting on cradle
        (-0.54, 1.50, 0.26, math.radians(-3.0)),
        (-0.21, 1.48, 0.26, math.radians(4.0)),
        (0.12, 1.45, 0.26, math.radians(7.0)),
        (0.45, 1.43, 0.25, math.radians(10.0)),
    ]
    back_slats = [
        (0.71, 1.98, 0.28, math.radians(74.0)),
        (0.83, 2.38, 0.28, math.radians(73.0)),
        (0.96, 2.79, 0.30, math.radians(71.0)),
    ]

    for y_c, z_c, w, tilt in seat_slats:
        add_beveled_slat(bm_wood, -3.0, 3.0, y_c, z_c, w, 0.085, tilt_rad=tilt)
    for y_c, z_c, w, tilt in back_slats:
        add_beveled_slat(bm_wood, -3.0, 3.0, y_c, z_c, w, 0.085, tilt_rad=tilt)

    # Ornate cast-iron end frames at X = -2.42 and X = +2.42
    for x_side in (-2.42, 2.42):
        bar_x = 0.115
        bar_w = 0.105

        # 1. Front cabriole leg sweeping up into rolled Victorian armrest scroll
        front_leg = sample_cubic_bezier(
            (-0.94, 0.04), (-0.88, 0.55), (-0.72, 1.05), (-0.84, 1.56), 8
        )
        arm_rise = sample_cubic_bezier(
            (-0.84, 1.56), (-0.96, 1.88), (-0.90, 2.18), (-0.62, 2.18), 7
        )
        arm_rail = sample_cubic_bezier(
            (-0.62, 2.18), (-0.18, 2.18), (0.36, 2.08), (0.81, 1.96), 6
        )
        front_and_arm = front_leg + arm_rise[1:] + arm_rail[1:]
        add_swept_bar_yz(bm_iron, front_and_arm, x_side, bar_x, bar_w)

        # Front armrest spiral curl (tight Victorian scroll at front tip of armrest)
        arm_curl = sample_cubic_bezier(
            (-0.84, 1.98), (-1.08, 2.16), (-1.16, 1.92), (-0.96, 1.86), 6
        )
        add_swept_bar_yz(bm_iron, arm_curl, x_side, bar_x * 0.88, bar_w * 0.82)

        # 2. Rear sweeping leg continuing up BEHIND the 3 backrest slats + backward top finial scroll
        rear_leg = sample_cubic_bezier(
            (0.98, 0.04), (0.86, 0.55), (0.66, 1.05), (0.68, 1.48), 7
        )
        back_spine = sample_cubic_bezier(
            (0.68, 1.48), (0.79, 1.96), (0.93, 2.44), (1.07, 2.94), 7
        )
        top_scroll = sample_cubic_bezier(
            (1.07, 2.94), (1.16, 3.16), (1.32, 3.12), (1.22, 2.94), 6
        )
        add_swept_bar_yz(bm_iron, rear_leg + back_spine[1:] + top_scroll[1:], x_side, bar_x, bar_w)

        # 3. Seat cradle rail hugging the underside of all 5 seat slats
        seat_cradle = [
            (-0.88, 1.38),
            (-0.54, 1.43),
            (-0.21, 1.41),
            (0.12, 1.38),
            (0.45, 1.36),
            (0.68, 1.46),
        ]
        add_swept_bar_yz(bm_iron, seat_cradle, x_side, bar_x * 0.92, bar_w * 0.95)

        # 4. Ornate lower S-scroll gracefully bracing front & rear legs
        lower_s = sample_cubic_bezier(
            (-0.80, 0.44), (-0.30, 0.36), (-0.10, 1.16), (0.62, 1.20), 9
        )
        add_swept_bar_yz(bm_iron, lower_s, x_side, bar_x * 0.78, bar_w * 0.74)

        # Counter-arch scroll underneath seat for Victorian filigree balance
        counter_scroll = sample_cubic_bezier(
            (-0.68, 1.26), (-0.24, 0.80), (0.30, 0.78), (0.78, 0.50), 8
        )
        add_swept_bar_yz(bm_iron, counter_scroll, x_side, bar_x * 0.78, bar_w * 0.74)

        # 5. Decorative S-scroll filling the space cleanly between seat cradle and armrest rail
        arm_scroll = sample_cubic_bezier(
            (-0.78, 1.76), (-0.42, 2.16), (-0.18, 1.48), (0.28, 2.08), 9
        )
        add_swept_bar_yz(bm_iron, arm_scroll, x_side, bar_x * 0.74, bar_w * 0.68)

        # Small ornamental ring medallion nested inside the lower frame
        ring_pts = []
        rc_y, rc_z, rr = 0.0, 0.88, 0.19
        for i in range(10):
            a = 2.0 * math.pi * i / 10
            ring_pts.append((rc_y + rr * math.cos(a), rc_z + rr * math.sin(a)))
        add_swept_bar_yz(bm_iron, ring_pts, x_side, bar_x * 0.68, bar_w * 0.56, closed=True)

        # Flared cast-iron foot pads resting cleanly on Z = 0.0
        add_box(bm_iron, (x_side, -0.94, 0.04), (0.20, 0.28, 0.08), bevel=0.015, bevel_segs=1)
        add_box(bm_iron, (x_side, 0.98, 0.04), (0.20, 0.28, 0.08), bevel=0.015, bevel_segs=1)

    # Central iron support rib at X = 0 (runs underneath seat & behind back slats)
    center_strap = [
        (-0.84, 1.39),
        (-0.54, 1.43),
        (-0.21, 1.41),
        (0.12, 1.38),
        (0.45, 1.36),
        (0.69, 1.48),
        (0.80, 1.96),
        (0.93, 2.38),
        (1.06, 2.80),
    ]
    add_swept_bar_yz(bm_iron, center_strap, 0.0, 0.08, 0.075)

    # Under-seat iron cross stretcher & diagonal braces linking the frames
    add_beam(bm_iron, (-2.42, 0.0, 0.88), (2.42, 0.0, 0.88), 0.065, 0.065, skip_ends=True)
    add_beam(bm_iron, (-2.42, -0.35, 1.38), (0.0, 0.0, 0.88), 0.05, 0.05, skip_ends=True)
    add_beam(bm_iron, (2.42, -0.35, 1.38), (0.0, 0.0, 0.88), 0.05, 0.05, skip_ends=True)
    add_beam(bm_iron, (-2.42, 0.42, 1.36), (0.0, 0.0, 0.88), 0.05, 0.05, skip_ends=True)
    add_beam(bm_iron, (2.42, 0.42, 1.36), (0.0, 0.0, 0.88), 0.05, 0.05, skip_ends=True)

    obj_iron = finalize_bmesh(bm_iron, "Bench_Iron", mats["Iron"], smooth_angle_deg=35.0)
    obj_wood = finalize_bmesh(bm_wood, "Bench_Wood", mats["Wood"], smooth_angle_deg=35.0)
    return [obj_iron, obj_wood]


# ---------------------------------------------------------------------------
# 4. PILLAR BOX (<= 1500 tris) — PillarBox_Iron, PillarBox_Brass
# ---------------------------------------------------------------------------

def build_pillarbox(mats):
    bm_iron = bmesh.new()
    bm_brass = bmesh.new()

    # Victorian cylindrical cast-iron post box, exactly 5.0 studs tall (Z: 0.0..5.0)
    # Main lathe profile: stepped plinth base -> shaft -> neck collar -> overhanging cornice -> dome -> crown finial
    profile = [
        (0.00, 0.94),   # plinth ground footprint
        (0.18, 0.94),   # plinth lower step
        (0.24, 0.88),   # plinth chamfer
        (0.56, 0.86),   # plinth upper band
        (0.66, 0.77),   # plinth transition
        (0.74, 0.80),   # base torus collar
        (0.82, 0.76),   # main cylindrical shaft start
        (3.86, 0.76),   # main cylindrical shaft top
        (3.94, 0.82),   # neck ring
        (4.04, 0.79),   # under-cornice cove
        (4.12, 0.96),   # overhanging cap brim bottom
        (4.24, 0.98),   # crown ridge eaves
        (4.32, 0.91),   # dome base step
        (4.48, 0.82),   # dome curve 1
        (4.64, 0.64),   # dome curve 2
        (4.76, 0.38),   # dome curve 3
        (4.82, 0.16),   # finial collar
        (4.90, 0.21),   # crown knob widest
        (4.97, 0.11),   # crown knob top
        (5.00, 0.015),  # finial apex
    ]
    add_lathe_rings(bm_iron, profile, segs=22, cap_bottom=True, cap_top=True)

    # Crown ridge decorative ribs radiating up the dome (8 sculptural ridges tucked cleanly onto dome brim)
    dome_pts = [(4.31, 0.90), (4.48, 0.82), (4.64, 0.64), (4.76, 0.38), (4.82, 0.17)]
    n_ribs = 8
    for i in range(n_ribs):
        ang = 2.0 * math.pi * i / n_ribs
        ca, sa = math.cos(ang), math.sin(ang)
        tx, ty = -sa, ca  # tangent around cylinder
        sub = bmesh.new()
        hw = 0.032
        rings = []
        for idx, (z, r) in enumerate(dome_pts):
            # Taper ridge gently at both ends so it blends smoothly into the cornice and finial
            taper = 0.7 if idx == 0 else (1.0 - 0.35 * idx / (len(dome_pts) - 1))
            w = hw * taper
            r_in = r - 0.04
            r_out = r + (0.022 if idx == 0 else 0.032)
            v_l = sub.verts.new((r_in * ca - w * tx, r_in * sa - w * ty, z))
            v_c = sub.verts.new((r_out * ca, r_out * sa, z + 0.015))
            v_r = sub.verts.new((r_in * ca + w * tx, r_in * sa + w * ty, z))
            rings.append((v_l, v_c, v_r))
        for j in range(len(rings) - 1):
            a0, a1 = rings[j], rings[j + 1]
            sub.faces.new((a0[0], a0[1], a1[1], a1[0]))
            sub.faces.new((a0[1], a0[2], a1[2], a1[1]))
        sub.faces.new((rings[0][0], rings[0][2], rings[0][1]))
        merge_bmesh(bm_iron, sub)
        sub.free()

    # Front faces -Y -> angle = -pi/2
    front = -math.pi * 0.5
    r_shaft = 0.76

    # Raised cast-iron door outline on front (-Y) face (Z = 0.98 to 2.58, angular span +/-0.54 rad)
    d_ang = 0.54
    d_z0, d_z1 = 0.98, 2.58
    bar_t = 0.065
    bar_ang = 0.085
    # Top and bottom curved door trim bars
    add_curved_plate(bm_iron, r_shaft - 0.02, r_shaft + 0.038, d_z1 - bar_t, d_z1, front - d_ang, front + d_ang, segs=6)
    add_curved_plate(bm_iron, r_shaft - 0.02, r_shaft + 0.038, d_z0, d_z0 + bar_t, front - d_ang, front + d_ang, segs=6)
    # Left and right vertical door trim bars
    add_curved_plate(bm_iron, r_shaft - 0.02, r_shaft + 0.038, d_z0 + bar_t, d_z1 - bar_t, front - d_ang, front - d_ang + bar_ang, segs=1)
    add_curved_plate(bm_iron, r_shaft - 0.02, r_shaft + 0.038, d_z0 + bar_t, d_z1 - bar_t, front + d_ang - bar_ang, front + d_ang, segs=1)

    # Door hinges (left edge) & lock boss (right edge)
    hinge_ang = front - d_ang - 0.02
    hx, hy = (r_shaft + 0.035) * math.cos(hinge_ang), (r_shaft + 0.035) * math.sin(hinge_ang)
    add_cylinder(bm_iron, (hx, hy, 1.32), 0.042, 0.042, 0.24, segs=8)
    add_cylinder(bm_iron, (hx, hy, 2.24), 0.042, 0.042, 0.24, segs=8)

    lock_ang = front + d_ang - 0.14
    lx, ly = (r_shaft + 0.04) * math.cos(lock_ang), (r_shaft + 0.04) * math.sin(lock_ang)
    add_box(bm_iron, (lx, ly, 1.78), (0.09, 0.06, 0.18), rot=(0.0, 0.0, lock_ang + math.pi * 0.5), bevel=0.012, bevel_segs=1)

    # Curved cast-iron rain hood / brow directly above posting slot
    slot_ang = 0.56
    add_curved_plate(bm_iron, r_shaft - 0.02, r_shaft + 0.11, 3.63, 3.71, front - slot_ang, front + slot_ang, segs=6)

    # Brass posting-slot plate (PillarBox_Brass) with real recessed mail slot opening!
    # Outer brass frame spans Z = 3.24..3.63, ang = front +/- 0.52; mail slot opening Z = 3.39..3.49, ang = front +/- 0.36
    b_in = r_shaft - 0.015
    b_out = r_shaft + 0.048
    p_ang = 0.52
    s_ang = 0.36
    # Bottom brass rail of slot plate
    add_curved_plate(bm_brass, b_in, b_out, 3.24, 3.38, front - p_ang, front + p_ang, segs=6)
    # Top brass rail of slot plate
    add_curved_plate(bm_brass, b_in, b_out, 3.49, 3.63, front - p_ang, front + p_ang, segs=6)
    # Left & right brass cheeks flanking the mail slot aperture
    add_curved_plate(bm_brass, b_in, b_out, 3.38, 3.49, front - p_ang, front - s_ang, segs=2)
    add_curved_plate(bm_brass, b_in, b_out, 3.38, 3.49, front + s_ang, front + p_ang, segs=2)

    # Small brass collection-times plaque below the posting slot (classic Victorian detail)
    plq_ang = 0.24
    add_curved_plate(bm_brass, b_in, r_shaft + 0.036, 2.74, 3.12, front - plq_ang, front + plq_ang, segs=4)

    obj_iron = finalize_bmesh(bm_iron, "PillarBox_Iron", mats["Iron"], smooth_angle_deg=35.0)
    obj_brass = finalize_bmesh(bm_brass, "PillarBox_Brass", mats["Brass"], smooth_angle_deg=35.0)
    return [obj_iron, obj_brass]


# ---------------------------------------------------------------------------
# 5. HAND CART (<= 3000 tris) — HandCart_Wood, HandCart_Iron
# ---------------------------------------------------------------------------

def add_spoked_wheel(bm_wood, bm_iron, x_center, y_center, z_center, radius=1.22, n_spokes=12):
    """Build one costermonger spoked wheel (12 spokes, wooden felloe & hub, iron tyre & hub bands)."""
    rim_w = 0.15
    tyre_t = 0.048
    felloe_r_out = radius - tyre_t
    felloe_r_in = felloe_r_out - 0.145
    segs = 24

    def add_wheel_ring(bm, r0, r1, w, skip_inner=False, skip_outer=False):
        sub = bmesh.new()
        hw = w * 0.5
        rings = []
        # 4 corners around cross-section: (r0, -hw), (r1, -hw), (r1, +hw), (r0, +hw)
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            ca, sa = math.cos(a), math.sin(a)
            v0 = sub.verts.new((x_center - hw, y_center + r0 * ca, z_center + r0 * sa))
            v1 = sub.verts.new((x_center - hw, y_center + r1 * ca, z_center + r1 * sa))
            v2 = sub.verts.new((x_center + hw, y_center + r1 * ca, z_center + r1 * sa))
            v3 = sub.verts.new((x_center + hw, y_center + r0 * ca, z_center + r0 * sa))
            rings.append((v0, v1, v2, v3))

        for i in range(segs):
            ni = (i + 1) % segs
            a0, a1 = rings[i], rings[ni]
            # -X cheek
            sub.faces.new((a0[0], a0[1], a1[1], a1[0]))
            # outer tread
            if not skip_outer:
                sub.faces.new((a0[1], a0[2], a1[2], a1[1]))
            # +X cheek
            sub.faces.new((a0[2], a0[3], a1[3], a1[2]))
            # inner rim
            if not skip_inner:
                sub.faces.new((a0[3], a0[0], a1[0], a1[3]))

        merge_bmesh(bm, sub)
        sub.free()

    # Iron tyre (outermost, inner face buried against wooden felloe)
    add_wheel_ring(bm_iron, felloe_r_out - 0.008, radius, rim_w + 0.008, skip_inner=True, skip_outer=False)

    # Wooden felloe rim (outer face buried inside iron tyre)
    add_wheel_ring(bm_wood, felloe_r_in, felloe_r_out + 0.004, rim_w, skip_inner=False, skip_outer=True)

    # 12 tapered 6-sided wooden spokes
    hub_r = 0.20
    spoke_len = felloe_r_in - hub_r + 0.08
    for i in range(n_spokes):
        a = 2.0 * math.pi * i / n_spokes
        r_mid = (hub_r + felloe_r_in) * 0.5
        py = y_center + r_mid * math.cos(a)
        pz = z_center + r_mid * math.sin(a)
        # Spoke axis along (0, cos a, sin a)
        vec = Vector((0.0, math.cos(a), math.sin(a)))
        rot = vec.to_track_quat("Z", "X").to_euler()
        add_cylinder(
            bm_wood,
            center=(x_center, py, pz),
            radius1=0.044,
            radius2=0.032,
            depth=spoke_len,
            segs=6,
            rot=rot,
            cap_ends=False,
        )

    # Wooden nave (hub)
    add_cylinder(
        bm_wood,
        center=(x_center, y_center, z_center),
        radius1=0.22,
        radius2=0.22,
        depth=0.38,
        segs=12,
        rot=(0.0, math.radians(90), 0.0),
        cap_ends=True,
        bevel_ends=0.03,
    )

    # Iron hub binding bands & outer axle nut cap
    sign_x = 1.0 if x_center > 0 else -1.0
    for dx in (-0.13, 0.13):
        add_cylinder(
            bm_iron,
            center=(x_center + dx, y_center, z_center),
            radius1=0.232,
            radius2=0.232,
            depth=0.055,
            segs=12,
            rot=(0.0, math.radians(90), 0.0),
            cap_ends=False,
        )
    # Outer axle cap
    add_cylinder(
        bm_iron,
        center=(x_center + sign_x * 0.22, y_center, z_center),
        radius1=0.10,
        radius2=0.075,
        depth=0.10,
        segs=8,
        rot=(0.0, math.radians(90) if sign_x > 0 else math.radians(-90), 0.0),
        cap_ends=True,
    )


def build_handcart(mats):
    bm_wood = bmesh.new()
    bm_iron = bmesh.new()

    # Long axis along Y: total length = 7.0 studs (Y: -3.50 to +3.50)
    # Shafts extend forward toward -Y; bed spans Y = -0.35 to +3.45; wheels centered at Y = +1.50
    wheel_r = 1.24
    wheel_y = 1.50
    wheel_x = 1.58

    # 1. Two 12-spoke wheels with iron tyres (touching Z = 0.0)
    add_spoked_wheel(bm_wood, bm_iron, -wheel_x, wheel_y, wheel_r, radius=wheel_r, n_spokes=12)
    add_spoked_wheel(bm_wood, bm_iron, wheel_x, wheel_y, wheel_r, radius=wheel_r, n_spokes=12)

    # 2. Forged iron axle & spring/mounting blocks connecting axle up to cart frame
    add_cylinder(
        bm_iron,
        center=(0.0, wheel_y, wheel_r),
        radius1=0.075,
        radius2=0.075,
        depth=wheel_x * 2.0 + 0.12,
        segs=10,
        rot=(0.0, math.radians(90), 0.0),
        cap_ends=False,
    )
    # Wooden axle bolster & iron U-straps connecting axle (Z=1.24) to shafts (Z=1.52)
    add_box(bm_wood, (0.0, wheel_y, 1.38), (2.42, 0.22, 0.16), bevel=0.015, bevel_segs=1)
    for sx in (-1.04, 1.04):
        add_box(bm_iron, (sx, wheel_y, 1.38), (0.16, 0.26, 0.34), bevel=0.015, bevel_segs=1)

    # 3. Long pulling shafts (running under the bed and extending forward to Y = -3.50!)
    # Swept gently upward toward ergonomic handle height Z = 1.88 at Y = -3.50
    for sx in (-1.04, 1.04):
        shaft_pts = [
            (3.45, 1.52),
            (1.50, 1.52),
            (-0.35, 1.52),
            (-1.25, 1.58),
            (-2.35, 1.72),
            (-3.46, 1.86),
        ]
        add_swept_bar_yz(bm_wood, shaft_pts, sx, 0.13, 0.14)
        # Iron ferrule tip caps at Y = -3.50 (sets exact front extent Y = -3.50)
        add_box(bm_iron, (sx, -3.44, 1.86), (0.142, 0.12, 0.152), bevel=0.015, bevel_segs=1)

    # Cross-bearers under the bed
    for yb in (-0.30, 0.60, 1.50, 2.40, 3.35):
        add_box(bm_wood, (0.0, yb, 1.55), (2.48, 0.14, 0.10))

    # 4. Bed floor planks (5 longitudinal planks with visible gaps, Z = 1.60..1.68)
    bed_y0, bed_y1 = -0.36, 3.43
    bed_len = bed_y1 - bed_y0
    bed_ym = (bed_y0 + bed_y1) * 0.5
    for i in range(5):
        px = -0.98 + i * 0.49
        add_box(bm_wood, (px, bed_ym, 1.64), (0.43, bed_len, 0.08))

    # 5. Flared wooden side boards (2 stacked horizontal planks per side, plus front & rear boards!)
    # Classic costermonger barrow outward flare (~9 degrees)
    flare = math.radians(9.0)
    board_h = 0.34
    board_t = 0.08
    # Left & Right side boards (2 tiers with visible gap)
    for sx in (-1, 1):
        for tier, (z_b, x_off) in enumerate([(1.87, 1.24), (2.26, 1.30)]):
            add_box(
                bm_wood,
                (sx * x_off, bed_ym, z_b),
                (board_t, bed_len + 0.04, board_h),
                rot=(0.0, sx * flare, 0.0),
                bevel=0.012,
                bevel_segs=1,
            )
        # 4 vertical wooden stanchions outside each side board
        for ys in (-0.28, 0.92, 2.12, 3.33):
            add_box(
                bm_wood,
                (sx * 1.33, ys, 2.04),
                (0.09, 0.11, 0.94),
                rot=(0.0, sx * flare, 0.0),
            )

    # Front (-Y) and Rear (+Y) boards (2 tiers, spanning between flared side boards)
    for sy, y_pos in ((-1, bed_y0 + 0.03), (1, bed_y1 - 0.03)):
        add_box(bm_wood, (0.0, y_pos, 1.87), (2.46, board_t, board_h), bevel=0.012, bevel_segs=1)
        add_box(bm_wood, (0.0, y_pos, 2.26), (2.58, board_t, board_h), bevel=0.012, bevel_segs=1)
        # 2 vertical battens on front & rear boards
        for bx in (-0.75, 0.75):
            add_box(bm_wood, (bx, y_pos + sy * 0.06, 2.04), (0.11, 0.08, 0.90))

    # 6. Iron corner straps binding the 4 bed corners (front/rear to side boards)
    for sx in (-1, 1):
        for sy, y_c in ((-1, bed_y0 - 0.01), (1, bed_y1 + 0.01)):
            for z_s, x_s in ((1.87, 1.29), (2.26, 1.35)):
                # Side wing
                add_box(bm_iron, (sx * x_s, y_c - sy * 0.14, z_s), (0.035, 0.30, 0.10))
                # End wing
                add_box(bm_iron, (sx * (x_s - 0.15), y_c + sy * 0.02, z_s), (0.30, 0.035, 0.10))

    # 7. Prop leg (sturdy hinged costermonger A-frame wooden prop leg + iron foot shoe & stay braces)
    # Anchored under front cross-bearer (Y = -0.35, Z = 1.48), angled slightly forward to ground Z = 0.0 at Y = -0.68
    leg_top_z = 1.48
    leg_bot_z = 0.06
    leg_top_y = -0.35
    leg_bot_y = -0.68
    # Two stout angled wooden struts converging slightly downward
    add_beam(bm_wood, (-0.72, leg_top_y, leg_top_z), (-0.52, leg_bot_y, leg_bot_z), 0.11, 0.11, bevel=0.012, bevel_segs=1)
    add_beam(bm_wood, (0.72, leg_top_y, leg_top_z), (0.52, leg_bot_y, leg_bot_z), 0.11, 0.11, bevel=0.012, bevel_segs=1)
    # Wooden horizontal cross-bar bracing the prop leg
    add_beam(bm_wood, (-0.61, -0.52, 0.74), (0.61, -0.52, 0.74), 0.09, 0.09, skip_ends=True)
    # Iron ground skid / foot shoes resting cleanly on Z = 0.0
    add_box(bm_iron, (-0.52, leg_bot_y, 0.035), (0.14, 0.22, 0.07), bevel=0.01, bevel_segs=1)
    add_box(bm_iron, (0.52, leg_bot_y, 0.035), (0.14, 0.22, 0.07), bevel=0.01, bevel_segs=1)
    # Iron diagonal stay rods & pivot brackets linking prop leg to shafts
    for sx in (-1, 1):
        add_box(bm_iron, (sx * 0.72, leg_top_y, leg_top_z), (0.15, 0.16, 0.14))
        add_beam(bm_iron, (sx * 0.58, -0.55, 0.62), (sx * 1.02, -1.20, 1.54), 0.042, 0.042, skip_ends=True)

    obj_wood = finalize_bmesh(bm_wood, "HandCart_Wood", mats["Wood"], smooth_angle_deg=35.0)
    obj_iron = finalize_bmesh(bm_iron, "HandCart_Iron", mats["Iron"], smooth_angle_deg=35.0)
    return [obj_wood, obj_iron]


# ---------------------------------------------------------------------------
# Normalization, Validation, Rendering & FBX Export
# ---------------------------------------------------------------------------

def normalize_and_validate(asset, objects):
    """Ensure bottom-center origin at (0,0,0), Z_min=0, identity transforms, and audit geometry."""
    coords = []
    for o in objects:
        for v in o.data.vertices:
            coords.append(o.matrix_world @ v.co)

    xs = [p.x for p in coords]
    ys = [p.y for p in coords]
    zs = [p.z for p in coords]
    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    min_z = min(zs)
    shift = Vector((-cx, -cy, -min_z))

    tris = 0
    ngons = 0
    zero_area = 0
    for o in objects:
        # Shift vertices into world-normalized coordinates and keep origin at (0,0,0) with identity xform
        for v in o.data.vertices:
            v.co = (o.matrix_world @ v.co) + shift
        o.location = (0.0, 0.0, 0.0)
        o.rotation_euler = (0.0, 0.0, 0.0)
        o.scale = (1.0, 1.0, 1.0)
        o.data.update()

        for p in o.data.polygons:
            nv = len(p.vertices)
            tris += max(0, nv - 2)
            if nv > 4:
                ngons += 1
            if p.area < 1e-6:
                zero_area += 1

    dims = [
        round(max(xs) - min(xs), 3),
        round(max(ys) - min(ys), 3),
        round(max(zs) - min(zs), 3),
    ]
    issues = []
    if tris > BUDGETS[asset]:
        issues.append(f"OVER BUDGET ({tris} > {BUDGETS[asset]})")
    if ngons > 0:
        issues.append(f"{ngons} n-gons")
    if zero_area > 0:
        issues.append(f"{zero_area} zero-area faces")
    return tris, dims, issues


def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_preview(asset, objects, dims):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 32

    # Dark blue-grey world background (explicitly via World shader node for Blender 5.x)
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("PreviewWorld")
        scene.world = world
    if world.node_tree:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (0.028, 0.042, 0.068, 1.0)
            bg.inputs[1].default_value = 0.85

    # Compute tight bounding sphere for clean 3/4 framing from slightly above
    dx, dy, dz = dims
    target = Vector((0.0, 0.0, dz * 0.48))
    radius = math.sqrt((dx * 0.5) ** 2 + (dy * 0.5) ** 2 + (dz * 0.5) ** 2)

    # 3/4 camera direction: front-right-above (+X, -Y, +Z)
    az = math.radians(-52.0)  # +X, -Y
    el = math.radians(24.0)   # slightly above
    if asset == "HandCart":
        az = math.radians(-38.0)  # show side profile + shafts + spoked wheel clearly
        el = math.radians(22.0)
    elif asset == "Bench":
        az = math.radians(-50.0)
        el = math.radians(22.0)

    cam_dir = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    # Fit bounding sphere nicely inside 50mm perspective lens with breathing margin
    fov_rad = 2.0 * math.atan(18.0 / 50.0)
    dist = (radius / math.sin(fov_rad * 0.5)) * 1.18
    cam_loc = target + cam_dir * dist

    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.data.lens = 50.0
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200.0
    point_at(cam, target)
    scene.camera = cam

    # Lighting: one warm key light + one cool rim light (scaled by asset radius)
    lights = []
    scale_p = max(1.0, radius * radius)
    light_defs = [
        (
            "WarmKey",
            target + Vector((radius * 1.6, -radius * 2.2, radius * 2.0)),
            180.0 * scale_p,
            (1.0, 0.72, 0.44),
            radius * 1.4,
        ),
        (
            "CoolRim",
            target + Vector((-radius * 2.0, radius * 1.6, radius * 1.4)),
            240.0 * scale_p,
            (0.42, 0.68, 1.0),
            radius * 1.1,
        ),
    ]
    for name, loc, energy, color, size in light_defs:
        bpy.ops.object.light_add(type="AREA", location=loc)
        lgt = bpy.context.object
        lgt.name = name
        lgt.data.energy = energy
        lgt.data.color = color
        lgt.data.shape = "DISK"
        lgt.data.size = size
        point_at(lgt, target)
        lights.append(lgt)

    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.35
    scene.render.filepath = os.path.join(RENDER_DIR, f"{asset}.png")

    bpy.ops.render.render(write_still=True)

    for o in [cam] + lights:
        bpy.data.objects.remove(o, do_unlink=True)


def export_asset(asset, objects, tris, dims):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    fbx_path = os.path.join(OUT_DIR, f"{asset}.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
        use_selection=True,
        object_types={"MESH"},
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="EDGE",
    )

    json_path = os.path.join(RENDER_DIR, f"{asset}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "tris": tris,
                "objects": [o.name for o in objects],
                "dims": dims,
            },
            f,
            indent=2,
        )


def main():
    clear_scene()
    mats = create_materials()

    builders = [
        ("Barrel", build_barrel),
        ("Crate", build_crate),
        ("Bench", build_bench),
        ("PillarBox", build_pillarbox),
        ("HandCart", build_handcart),
    ]

    report = []
    for asset, fn in builders:
        objects = fn(mats)
        tris, dims, issues = normalize_and_validate(asset, objects)
        render_preview(asset, objects, dims)
        export_asset(asset, objects, tris, dims)
        report.append((asset, tris, dims, [o.name for o in objects], issues))

        # Remove asset objects before building the next asset
        for o in objects:
            bpy.data.objects.remove(o, do_unlink=True)

    print("STREET_REPORT_BEGIN")
    for asset, tris, dims, names, issues in report:
        prob = ", ".join(issues) if issues else "none"
        print(f"{asset}: {tris}/{BUDGETS[asset]} tris | dims {dims} | objects {names} | issues: {prob}")
    print("STREET_REPORT_END")


if __name__ == "__main__":
    main()
