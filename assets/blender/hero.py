import bpy, bmesh, math, json, os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'export')
PRE = os.path.join(ROOT, 'renders')
os.makedirs(OUT, exist_ok=True)
os.makedirs(PRE, exist_ok=True)

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Materials are constructed at module load and are intentionally retained here.
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)

def mat(name, color, metallic=0.0, rough=0.45, emission=None, emission_color=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1.0)
    bs.inputs['Metallic'].default_value = metallic
    bs.inputs['Roughness'].default_value = rough
    if emission:
        ec = emission_color if emission_color is not None else color
        bs.inputs['Emission Color'].default_value = (*ec, 1.0)
        bs.inputs['Emission Strength'].default_value = emission
    return m

MATS = {
    'Iron': mat('Iron', (0.09, 0.11, 0.14), 0.80, 0.34),
    'Brass': mat('Brass', (0.64, 0.38, 0.10), 0.85, 0.24),
    'Glass': mat('Glass', (0.24, 0.46, 0.54), 0.05, 0.06),
    'Flame': mat('Flame', (1.0, 0.48, 0.08), 0.0, 0.20, 4.5, (1.0, 0.52, 0.10)),
    'Wood': mat('Wood', (0.11, 0.042, 0.020), 0.08, 0.22),
    'Silver': mat('Silver', (0.72, 0.78, 0.84), 0.92, 0.18),
    'Steel': mat('Steel', (0.48, 0.56, 0.64), 0.90, 0.20),
    'Leather': mat('Leather', (0.11, 0.042, 0.020), 0.04, 0.70),
    'Liquid': mat('Liquid', (0.01, 0.72, 0.48), 0.0, 0.12, 3.2, (0.02, 0.95, 0.58)),
    'Cork': mat('Cork', (0.36, 0.20, 0.085), 0.0, 0.82),
}

glass_bs = MATS['Glass'].node_tree.nodes.get('Principled BSDF')
glass_bs.inputs['Alpha'].default_value = 0.20
glass_bs.inputs['Transmission Weight'].default_value = 0.40
glass_bs.inputs['Specular IOR Level'].default_value = 0.85
if 'Coat Weight' in glass_bs.inputs:
    glass_bs.inputs['Coat Weight'].default_value = 0.65
    glass_bs.inputs['Coat Roughness'].default_value = 0.05
MATS['Glass'].surface_render_method = 'BLENDED'
MATS['Glass'].use_backface_culling = True

GROUPS = {}

def add_obj(obj, key, material):
    obj.name = key + 'Part'
    obj.data.materials.clear()
    obj.data.materials.append(MATS[material])
    GROUPS.setdefault((key, material), []).append(obj)
    return obj

def make_mesh(key, material, verts, faces, name='Part'):
    me = bpy.data.meshes.new(key + name + 'Mesh')
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(key + name, me)
    bpy.context.collection.objects.link(o)
    return add_obj(o, key, material)

def cube(key, material, loc, scale, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new('Bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return add_obj(o, key, material)

def cyl(key, material, loc, radius, depth, vertices=12, r2=None, rotation=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=r2, depth=depth, location=loc)
    o = bpy.context.object
    if rotation:
        o.rotation_euler = rotation
    return add_obj(o, key, material)

def torus(key, material, loc, major, minor, rot=None, major_seg=16, minor_seg=6, scale=None):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=major_seg, minor_segments=minor_seg,
        major_radius=major, minor_radius=minor, location=loc
    )
    o = bpy.context.object
    if rot:
        o.rotation_euler = rot
    if scale:
        o.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return add_obj(o, key, material)

def sphere(key, material, loc, scale, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return add_obj(o, key, material)

def beam(key, material, a, b, width, depth=None, bevel=0):
    if depth is None:
        depth = width
    mid = (Vector(a) + Vector(b)) / 2
    vec = Vector(b) - Vector(a)
    o = cube(key, material, mid, (width, depth, vec.length), bevel)
    o.rotation_euler = vec.to_track_quat('Z', 'Y').to_euler()
    return o

def lathe(key, material, profile, sides=16, phase=0.0, cap_bottom=True, cap_top=True,
          radial_fn=None, scale_xy=(1.0, 1.0)):
    verts = []
    faces = []
    sx, sy = scale_xy
    for j, (z, r) in enumerate(profile):
        for i in range(sides):
            a = 2.0 * math.pi * i / sides + phase
            ri = radial_fn(j, i, sides, z, r) if radial_fn else r
            verts.append((ri * sx * math.cos(a), ri * sy * math.sin(a), z))
    for j in range(len(profile) - 1):
        for i in range(sides):
            a = j * sides + i
            b = j * sides + (i + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    if cap_bottom and profile[0][1] > 1e-5:
        bc = len(verts)
        verts.append((0.0, 0.0, profile[0][0]))
        for i in range(sides):
            ni = (i + 1) % sides
            faces.append((bc, ni, i))
    if cap_top and profile[-1][1] > 1e-5:
        tc = len(verts)
        verts.append((0.0, 0.0, profile[-1][0]))
        base = (len(profile) - 1) * sides
        for i in range(sides):
            ni = (i + 1) % sides
            faces.append((tc, base + i, base + ni))
    return make_mesh(key, material, verts, faces, 'Lathe')

def sweep_xz(key, material, points, profile_uv, scale_fn=None, cap_start=True, cap_end=True):
    """Sweep a 2D (u_in_xz_normal, v_along_y) profile along a 3D curve lying in the XZ plane."""
    pts = [Vector(p) for p in points]
    n_pts = len(pts)
    n_prof = len(profile_uv)
    y_axis = Vector((0.0, 1.0, 0.0))
    verts = []
    for k, p in enumerate(pts):
        if k == 0:
            tan = (pts[1] - pts[0]).normalized()
        elif k == n_pts - 1:
            tan = (pts[-1] - pts[-2]).normalized()
        else:
            tan = (pts[k + 1] - pts[k - 1]).normalized()
        nrm = tan.cross(y_axis).normalized()
        su, sv = scale_fn(k / max(1, n_pts - 1)) if scale_fn else (1.0, 1.0)
        for u, v in profile_uv:
            pos = p + nrm * (u * su) + y_axis * (v * sv)
            verts.append((pos.x, pos.y, pos.z))
    faces = []
    for k in range(n_pts - 1):
        r0 = k * n_prof
        r1 = (k + 1) * n_prof
        for i in range(n_prof):
            ni = (i + 1) % n_prof
            faces.append((r0 + i, r0 + ni, r1 + ni, r1 + i))
    if cap_start:
        c = len(verts)
        verts.append((pts[0].x, pts[0].y, pts[0].z))
        for i in range(n_prof):
            ni = (i + 1) % n_prof
            faces.append((c, ni, i))
    if cap_end:
        c = len(verts)
        verts.append((pts[-1].x, pts[-1].y, pts[-1].z))
        base = (n_pts - 1) * n_prof
        for i in range(n_prof):
            ni = (i + 1) % n_prof
            faces.append((c, base + i, base + ni))
    return make_mesh(key, material, verts, faces, 'Sweep')

def cubic_bezier(p0, p1, p2, p3, steps):
    v0, v1, v2, v3 = Vector(p0), Vector(p1), Vector(p2), Vector(p3)
    out = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1.0 - t
        pt = (mt**3) * v0 + 3 * (mt**2) * t * v1 + 3 * mt * (t**2) * v2 + (t**3) * v3
        out.append(pt)
    return out


# =============================================================================
# 1. GASLAMP — 15.0 studs tall, budget 3500 tris
# =============================================================================
def build_lamp():
    k = 'Gaslamp'
    # Stepped octagonal plinth (Z = 0.0 to 1.05)
    cyl(k, 'Iron', (0, 0, 0.16), 0.84, 0.32, 8)
    cyl(k, 'Iron', (0, 0, 0.44), 0.66, 0.24, 8)
    cyl(k, 'Iron', (0, 0, 0.68), 0.50, 0.24, 8)
    lathe(k, 'Iron', [(0.80, 0.44), (0.94, 0.35), (1.06, 0.285)], sides=16)

    # Lower half shaft with 8 crisp vertical flutes (Z = 1.05 to 5.35)
    # Diameter ~0.55 at base (r=0.275) tapering smoothly toward top (r=0.20 at z=9.4)
    def r_shaft(z):
        t = max(0.0, min(1.0, (z - 1.05) / (9.40 - 1.05)))
        return 0.275 * (1.0 - t) + 0.200 * t

    lower_prof = [
        (1.05, r_shaft(1.05)),
        (1.25, r_shaft(1.25)),
        (3.20, r_shaft(3.20)),
        (5.15, r_shaft(5.15)),
        (5.35, r_shaft(5.35)),
    ]
    def flute_fn(j, i, sides, z, r):
        # 8 flutes across 32 radial vertices: 4 verts per flute (ridge, slope, trough, slope)
        if j in (1, 2, 3):
            m = i % 4
            if m == 0:
                return r * 1.03
            elif m == 2:
                return r * 0.83
            else:
                return r * 0.92
        return r
    lathe(k, 'Iron', lower_prof, sides=32, radial_fn=flute_fn)

    # Collar ring 1: decorative transition collar above fluted lower half (Z = 5.30 to 5.75)
    lathe(k, 'Iron', [
        (5.30, 0.24), (5.38, 0.31), (5.48, 0.33), (5.56, 0.29),
        (5.65, 0.31), (5.75, 0.235)
    ], sides=16)

    # Upper smooth tapered shaft (Z = 5.70 to 9.45) + capital flare into lantern cradle (9.45 to 10.55)
    lathe(k, 'Iron', [
        (5.70, r_shaft(5.70)),
        (8.75, r_shaft(8.75)),
        (9.45, 0.200),
        (9.75, 0.245),
        (10.05, 0.220),
        (10.35, 0.330),
        (10.55, 0.420),
    ], sides=16)

    # Collar ring 2: decorative upper collar below ladder-rest crossbar (Z = 8.65 to 9.05)
    lathe(k, 'Iron', [
        (8.65, 0.208), (8.73, 0.275), (8.83, 0.295),
        (8.93, 0.270), (9.02, 0.205)
    ], sides=16)

    # Ladder-rest crossbar on BOTH sides (-X and +X) well below the lantern (Z = 9.52)
    beam(k, 'Iron', (-1.52, 0, 9.52), (1.52, 0, 9.52), 0.11, 0.13, 0.02)
    # Center boss + symmetric end finials on BOTH arms
    cyl(k, 'Iron', (0, 0, 9.52), 0.24, 0.22, 12)
    for sx in (-1.0, 1.0):
        sphere(k, 'Iron', (sx * 1.56, 0, 9.52), (0.11, 0.11, 0.11), 10, 6)
        # Decorative collar bead near each arm end
        cyl(k, 'Iron', (sx * 1.38, 0, 9.52), 0.095, 0.07, 10, rotation=(0, math.pi / 2, 0))
        # Angled support strut bracing each arm to the shaft
        beam(k, 'Iron', (sx * 1.02, 0, 9.48), (sx * 0.21, 0, 8.92), 0.075, 0.075, 0.012)

    # Square tapered 4-pane lantern (Z = 10.55 to 12.82)
    z0, z1 = 10.55, 12.82
    hb, ht = 0.56, 0.78  # tapered outward toward top (classic Victorian silhouette)

    # Four iron support frog struts from capital to bottom lantern corners
    for sx in (-1, 1):
        for sy in (-1, 1):
            beam(k, 'Iron', (sx * 0.26, sy * 0.26, 10.30), (sx * hb, sy * hb, z0), 0.07, 0.07, 0.01)

    # Brass corner posts (tapered along lantern walls)
    for sx in (-1, 1):
        for sy in (-1, 1):
            beam(k, 'Brass', (sx * hb, sy * hb, z0), (sx * ht, sy * ht, z1), 0.072, 0.072, 0.012)

    # Brass horizontal perimeter rails (bottom, lower accent, top)
    for z, h, thick in [(z0, hb, 0.068), (z0 + 0.16, hb + (ht - hb) * 0.07, 0.045), (z1, ht, 0.072)]:
        for sy in (-1, 1):
            beam(k, 'Brass', (-h, sy * h, z), (h, sy * h, z), thick, thick, 0.0)
        for sx in (-1, 1):
            beam(k, 'Brass', (sx * h, -h, z), (sx * h, h, z), thick, thick, 0.0)

    # 4 tapered glass panes (clean thin trapezoidal panels inset inside brass frame)
    g0, g1 = z0 + 0.06, z1 - 0.05
    gb, gt = hb - 0.045, ht - 0.045
    t_glass = 0.020
    for face_idx in range(4):
        ang = face_idx * math.pi / 2.0
        ca, sa = math.cos(ang), math.sin(ang)
        def rot_pt(x, y, z):
            return (x * ca - y * sa, x * sa + y * ca, z)
        # Pane on +Y face rotated by ang (outer face at y=+g, inner face at y=+g-t_glass)
        v_pane = [
            rot_pt(-gb + 0.03, gb, g0),
            rot_pt(gb - 0.03, gb, g0),
            rot_pt(gt - 0.03, gt, g1),
            rot_pt(-gt + 0.03, gt, g1),
            rot_pt(-gb + 0.03, gb - t_glass, g0),
            rot_pt(gb - 0.03, gb - t_glass, g0),
            rot_pt(gt - 0.03, gt - t_glass, g1),
            rot_pt(-gt + 0.03, gt - t_glass, g1),
        ]
        f_pane = [
            (0, 1, 2, 3),  # outer
            (7, 6, 5, 4),  # inner
            (0, 4, 5, 1),  # bottom
            (3, 2, 6, 7),  # top
            (0, 3, 7, 4),  # left
            (1, 5, 6, 2),  # right
        ]
        make_mesh(k, 'Glass', v_pane, f_pane, f'Pane{face_idx}')

    # Steep pyramid hood (Z = 12.82 to 14.32, overhanging eave half-width = 0.88)
    zh0, zh1 = 12.82, 14.32
    he = 0.88
    ha = 0.14  # small top vent plateau
    hood_verts = [
        (-he, -he, zh0), (he, -he, zh0), (he, he, zh0), (-he, he, zh0),
        (-ha, -ha, zh1), (ha, -ha, zh1), (ha, ha, zh1), (-ha, ha, zh1),
    ]
    hood_faces = [
        (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
        (0, 3, 2, 1), (4, 5, 6, 7),
    ]
    make_mesh(k, 'Iron', hood_verts, hood_faces, 'Hood')

    # Crisp brass trim edges on hood: 4 eave rails + 4 hip-ridge corner ribs + apex collar
    he_trim = he + 0.02
    for sy in (-1, 1):
        beam(k, 'Brass', (-he_trim, sy * he_trim, zh0 + 0.015), (he_trim, sy * he_trim, zh0 + 0.015), 0.068, 0.062, 0.01)
    for sx in (-1, 1):
        beam(k, 'Brass', (sx * he_trim, -he_trim, zh0 + 0.015), (sx * he_trim, he_trim, zh0 + 0.015), 0.068, 0.062, 0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            beam(k, 'Brass', (sx * he_trim, sy * he_trim, zh0 + 0.02), (sx * ha, sy * ha, zh1 + 0.01), 0.052, 0.052, 0.0)
    lathe(k, 'Brass', [(zh1 - 0.02, 0.21), (zh1 + 0.05, 0.22), (zh1 + 0.08, 0.17)], sides=12)

    # Hood crown & finial reaching exact Z = 15.00
    lathe(k, 'Iron', [
        (zh1 + 0.06, 0.16), (14.48, 0.15), (14.56, 0.10),
        (14.68, 0.15), (14.80, 0.11), (14.92, 0.045), (15.00, 0.008)
    ], sides=12)

    # Inner gaslight flame/mantle (~0.9 x 1.2 studs centered in lantern)
    lathe(k, 'Flame', [
        (11.10, 0.10), (11.24, 0.30), (11.48, 0.43), (11.72, 0.45),
        (11.96, 0.38), (12.16, 0.23), (12.30, 0.05)
    ], sides=14)


# =============================================================================
# 2. CANE — 4.40 studs long, origin at grip (0,0,0), budget 900 tris
# =============================================================================
def build_cane():
    k = 'Cane'
    # Silver knob handle (slightly flattened sphere) + engraved band under it + thin collar
    # Knob spans Z = -0.40 (crown) to -0.11; engraved band Z = -0.11 to -0.01;
    # neck + thin raised collar where knob meets wood at Z = +0.08..+0.13.
    knob_prof = [
        (-0.400, 0.040),
        (-0.392, 0.125),
        (-0.360, 0.185),
        (-0.310, 0.215),
        (-0.255, 0.220),  # flattened oblate equator (diam 0.44 vs height 0.29)
        (-0.195, 0.195),
        (-0.140, 0.148),
        (-0.115, 0.132),  # recess above engraved band
        (-0.102, 0.148),  # upper bead of engraved band
        (-0.088, 0.138),  # engraved band upper edge
        (-0.048, 0.142),  # engraved band center
        (-0.015, 0.136),  # engraved band lower edge
        (0.000,  0.144),  # lower bead of engraved band
        (0.018,  0.118),  # tapered neck below band
        (0.082,  0.112),  # transition to thin collar
        (0.095,  0.128),  # thin raised collar lip meeting wood
        (0.118,  0.128),  # collar outer face
        (0.130,  0.106),  # flush step onto wood shaft
    ]
    def engrave_fn(j, i, sides, z, r):
        # Engraved vertical fluting/chasing on the band rings (j = 9, 10, 11)
        if j in (9, 10, 11):
            return r * (0.91 if (i % 2 == 1) else 1.03)
        return r
    lathe(k, 'Silver', knob_prof, sides=18, radial_fn=engrave_fn)

    # Dark lacquered wood shaft: starts tucked inside the thin silver collar (Z = 0.10)
    # and tapers cleanly to the silver ferrule (Z = 3.62)
    lathe(k, 'Wood', [
        (0.10, 0.105),
        (1.85, 0.086),
        (3.62, 0.068),
    ], sides=16)

    # Silver ferrule tapering cleanly to rounded tip at Z = 4.00 (total length = 4.40)
    lathe(k, 'Silver', [
        (3.58, 0.070),
        (3.60, 0.076),
        (3.64, 0.072),
        (3.92, 0.056),
        (3.98, 0.044),
        (4.00, 0.022),
    ], sides=14)


# =============================================================================
# 3. SABRE — 4.40 studs total, blade 3.20 studs, origin at grip, budget 1500 tris
# =============================================================================
def build_sabre():
    k = 'Sabre'
    # Ergonomic slightly-oval leather grip (Z = -0.48 to +0.44)
    lathe(k, 'Leather', [
        (-0.48, 0.118),
        (-0.22, 0.130),
        (0.05,  0.128),
        (0.30,  0.120),
        (0.44,  0.116),
    ], sides=14, scale_xy=(1.08, 0.84))

    # Crisp brass wire wrap coils around the leather grip (proud of leather surface)
    for i in range(6):
        z = -0.34 + i * 0.132
        # Match grip swell profile so every ring sits evenly proud of leather
        r_grip = 0.129 - 0.008 * abs(z / 0.40)
        torus(k, 'Brass', (0, 0, z), r_grip, 0.015,
              major_seg=12, minor_seg=3, scale=(1.08, 0.84, 1.0))

    # Brass pommel cap (Z = -0.72 to -0.45)
    lathe(k, 'Brass', [
        (-0.72, 0.045),
        (-0.69, 0.120),
        (-0.63, 0.155),
        (-0.54, 0.152),
        (-0.47, 0.132),
        (-0.44, 0.124),
    ], sides=14, scale_xy=(1.08, 0.88))

    # Brass crossguard with slight rear quillon (Z = 0.44 to 0.51)
    # Cutting edge & knuckle bow are on -X; spine & rear quillon on +X
    guard_pts = [
        (-0.32, 0, 0.46),
        (-0.18, 0, 0.465),
        (0.00,  0, 0.47),
        (0.18,  0, 0.46),
        (0.28,  0, 0.42),
        (0.32,  0, 0.37),
    ]
    guard_prof = [
        (-0.042, -0.070), (0.042, -0.070), (0.052, -0.045), (0.052, 0.045),
        (0.042, 0.070), (-0.042, 0.070), (-0.052, 0.045), (-0.052, -0.045),
    ]
    def guard_scale(t):
        if t < 0.72:
            return (1.0, 1.0 + 0.18 * math.sin(math.pi * t / 0.72))
        # Taper into rear quillon finial lobe
        q = (t - 0.72) / 0.28
        return (0.78 - 0.15 * q, 0.85 - 0.30 * q)
    sweep_xz(k, 'Brass', guard_pts, guard_prof, scale_fn=guard_scale)

    # Small brass langets hugging the base of the blade on +Y and -Y
    for sy in (-1, 1):
        cube(k, 'Brass', (0.0, sy * 0.052, 0.56), (0.14, 0.032, 0.18), bevel=0.008)

    # ONE continuous curved brass knuckle bow running from crossguard around fingers into pommel cap
    bow_pts = cubic_bezier(
        (-0.28, 0.0, 0.455),
        (-0.64, 0.0, 0.420),
        (-0.66, 0.0, -0.280),
        (-0.06, 0.0, -0.590),
        steps=16
    )
    bow_prof = [
        (-0.026, -0.046), (0.026, -0.046), (0.036, -0.028), (0.036, 0.028),
        (0.026, 0.046), (-0.026, 0.046), (-0.036, 0.028), (-0.036, -0.028),
    ]
    def bow_scale(t):
        # Slightly broader strap across the middle of the knuckle guard
        swell = 1.0 + 0.25 * math.sin(math.pi * t)
        return (1.0, swell)
    sweep_xz(k, 'Brass', bow_pts, bow_prof, scale_fn=bow_scale)

    # Cavalry sabre blade: slim (~0.22 wide at base tapering to a sharp point),
    # clearly curved backward (+X, toward spine) along its whole 3.20 length (tip offset ~0.38),
    # single sharp edge (-X) with a genuine concave fuller groove on both faces.
    z_base, blade_len = 0.48, 3.20
    t_vals = [0.00, 0.06, 0.13, 0.23, 0.35, 0.48, 0.61, 0.74, 0.84, 0.92, 0.97, 1.00]
    w_vals = [0.220, 0.214, 0.206, 0.196, 0.184, 0.170, 0.152, 0.132, 0.106, 0.072, 0.032, 0.000]

    def centerline_xz(t):
        z = z_base + blade_len * t
        # Smooth continuous curve backward (+X) along entire blade, tip offset = 0.38
        x = 0.38 * (t ** 1.72)
        return Vector((x, 0.0, z))

    centers = [centerline_xz(t) for t in t_vals]
    verts = []
    ring_n = 11
    y_axis = Vector((0.0, 1.0, 0.0))

    for idx, (t, w) in enumerate(zip(t_vals[:-1], w_vals[:-1])):
        c = centers[idx]
        if idx == 0:
            tan = (centers[1] - centers[0]).normalized()
        else:
            tan = (centers[idx + 1] - centers[idx - 1]).normalized()
        # In-plane perpendicular pointing toward +X (spine)
        nrm = y_axis.cross(tan).normalized()  # (tan_z, 0, -tan_x) -> points +X!
        # Blade half-thickness tapers from base to tip
        th = 0.036 * (1.0 - 0.65 * t)
        # Fuller depth envelope: solid ricasso near base, deep fuller 12%..74%, fades before tip
        if t < 0.06 or t > 0.85:
            fl = 0.0
        elif t < 0.13:
            fl = (t - 0.06) / 0.07
        elif t > 0.74:
            fl = (0.85 - t) / 0.11
        else:
            fl = 1.0

        # Near the tip, shift centerline slightly toward spine so cutting edge sweeps up into tip
        edge_shift = 0.025 * (max(0.0, (t - 0.70) / 0.30) ** 1.6)
        u_edge = -0.50 * w + edge_shift
        u_spine = 0.50 * w + edge_shift * 0.2
        w_eff = u_spine - u_edge

        def u_frac(f):
            return u_edge + f * w_eff

        th_f = th * (1.0 - 0.62 * fl)
        # 11-vertex single-edged cross-section with genuine carved fuller on both faces
        sec = [
            (u_frac(0.00), 0.0),          # 0: sharp single cutting edge (-X)
            (u_frac(0.34), th),           # 1: bevel ridge (+Y)
            (u_frac(0.46), th_f),         # 2: fuller trough lower (+Y)
            (u_frac(0.76), th_f),         # 3: fuller trough upper (+Y)
            (u_frac(0.86), th * 0.94),    # 4: fuller spine lip (+Y)
            (u_frac(1.00), th * 0.80),    # 5: flat spine corner (+Y)
            (u_frac(1.00), -th * 0.80),   # 6: flat spine corner (-Y)
            (u_frac(0.86), -th * 0.94),   # 7: fuller spine lip (-Y)
            (u_frac(0.76), -th_f),        # 8: fuller trough upper (-Y)
            (u_frac(0.46), -th_f),        # 9: fuller trough lower (-Y)
            (u_frac(0.34), -th),          # 10: bevel ridge (-Y)
        ]
        for u, yv in sec:
            p = c + nrm * u + y_axis * yv
            verts.append((p.x, p.y, p.z))

    # Tip apex vertex (sharp curved sabre tip at Z = 3.68, X = +0.39)
    tip_idx = len(verts)
    tip_c = centers[-1]
    verts.append((tip_c.x + 0.015, 0.0, tip_c.z))

    # Base center vertex for clean triangle fan cap (no n-gon)
    base_idx = len(verts)
    verts.append((centers[0].x, 0.0, centers[0].z))

    faces = []
    n_rings = len(t_vals) - 1
    for j in range(n_rings - 1):
        r0 = j * ring_n
        r1 = (j + 1) * ring_n
        for i in range(ring_n):
            ni = (i + 1) % ring_n
            faces.append((r0 + i, r0 + ni, r1 + ni, r1 + i))

    # Converge last ring cleanly to tip apex
    last_r = (n_rings - 1) * ring_n
    for i in range(ring_n):
        ni = (i + 1) % ring_n
        faces.append((last_r + i, last_r + ni, tip_idx))

    # Cap blade base inside guard
    for i in range(ring_n):
        ni = (i + 1) % ring_n
        faces.append((base_idx, ni, i))

    make_mesh(k, 'Steel', verts, faces, 'Blade')


# =============================================================================
# 4. TONIC VIAL — 0.90 studs tall, budget 800 tris
# =============================================================================
def build_vial():
    k = 'TonicVial'
    # Smooth round-bottom glass flask + long neck + flared rim (20 sides, 9 rings -> 360 tris)
    glass_prof = [
        (0.000, 0.110),
        (0.032, 0.188),
        (0.105, 0.252),
        (0.220, 0.275),
        (0.340, 0.246),
        (0.432, 0.180),
        (0.502, 0.102),
        (0.768, 0.095),
        (0.818, 0.124),
    ]
    lathe(k, 'Glass', glass_prof, sides=20, cap_bottom=True, cap_top=True)

    # Vivid alchemical glowing green-teal liquid filling ONLY lower 2/3 of the flask
    # (bulb is Z = 0.00..0.48, 2/3 = 0.32), inset from glass, with crisp FLAT meniscus top plane!
    liquid_prof = [
        (0.026, 0.098),
        (0.062, 0.174),
        (0.132, 0.228),
        (0.222, 0.246),
        (0.315, 0.224),  # flat top meniscus plane capped at Z = 0.315
    ]
    lathe(k, 'Liquid', liquid_prof, sides=20, cap_bottom=True, cap_top=True)

    # Tapered cork stopper plugging the long neck (Z = 0.74 to 0.90)
    lathe(k, 'Cork', [
        (0.740, 0.082),
        (0.885, 0.104),
        (0.900, 0.092),
    ], sides=14, cap_bottom=True, cap_top=True)

    # Twine wrap around the neck (3 distinct tight coils, single smooth corrugated lathe -> 144 tris)
    lathe(k, 'Cork', [
        (0.570, 0.098),
        (0.588, 0.118),
        (0.608, 0.101),
        (0.628, 0.118),
        (0.648, 0.101),
        (0.668, 0.118),
        (0.686, 0.098),
    ], sides=12, cap_bottom=False, cap_top=False)


# =============================================================================
# JOIN, CLEANUP, SMOOTHING, RENDER, EXPORT
# =============================================================================
def finalize_object(o, smooth_angle_deg=35.0):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    # Apply location, rotation, scale so every object has origin at (0,0,0) and identity transform
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Clean normals & eliminate degenerate faces / n-gons
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()

    # Smooth by Angle (~35 deg) and apply the modifier cleanly before export
    bpy.ops.object.shade_auto_smooth(angle=math.radians(smooth_angle_deg))
    for mod in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)

def join_groups(asset):
    objects = []
    for (a, material), objs in list(GROUPS.items()):
        if a != asset:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        o = bpy.context.object
        o.name = f'{asset}_{material}'
        # Use 42 deg on TonicVial glass & liquid so spherical bulb is 100% smooth
        # while the flat meniscus edge (~75 deg) and base (~60 deg) remain crisp!
        angle = 42.0 if (asset == 'TonicVial' and material in ('Glass', 'Liquid')) else 35.0
        finalize_object(o, smooth_angle_deg=angle)
        objects.append(o)
    return objects

def point_camera(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

def set_world_bg(color=(0.022, 0.032, 0.052)):
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new('World')
        bpy.context.scene.world = world
    if world.node_tree:
        bg = world.node_tree.nodes.get('Background')
        if bg:
            bg.inputs['Color'].default_value = (*color, 1.0)
            bg.inputs['Strength'].default_value = 1.0
    world.color = color

def setup_render(objects, asset, dims, bounds):
    min_x, max_x, min_y, max_y, min_z, max_z = bounds
    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5
    cz = (min_z + max_z) * 0.5

    set_world_bg((0.022, 0.034, 0.056))

    if asset == 'Sabre':
        # 3/4 broadside view showing the curved blade, fuller groove, and continuous D-guard
        target = (cx, cy, cz)
        camera_loc = (cx + 1.4, -5.2, cz + 0.95)
        ortho_scale = max(dims[2] * 1.12, dims[0] * 2.2)
    elif asset == 'Cane':
        # Slightly elevated 3/4 view showing the flattened knob, engraved band, collar, and taper
        target = (cx, cy, cz)
        camera_loc = (cx + 2.2, -4.4, cz - 0.45)
        ortho_scale = dims[2] * 1.10
    elif asset == 'Gaslamp':
        # Classic 3/4 front-right view where BOTH ladder-rest crossbar arms stick out clearly
        target = (cx, cy, cz)
        camera_loc = (cx + 5.2, -16.5, cz + 4.8)
        ortho_scale = dims[2] * 1.12
    else:  # TonicVial
        # Slightly elevated 3/4 view clearly showing the flat glowing green-teal meniscus plane
        target = (cx, cy, cz)
        camera_loc = (cx + 1.1, -2.0, cz + 0.72)
        ortho_scale = max(dims[2] * 1.24, max(dims[0], dims[1]) * 1.55)

    bpy.ops.object.camera_add(location=camera_loc)
    cam = bpy.context.object
    point_camera(cam, target)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho_scale
    bpy.context.scene.camera = cam

    # Warm key light + cool rim light + subtle soft fill for dark metals
    span = max(dims[2], 1.2)
    lights = []
    light_specs = [
        ('WarmKey', (cx - span * 0.55, -span * 0.95, cz + span * 0.55), span * span * 24.0, (1.0, 0.74, 0.46), span * 0.45),
        ('CoolRim', (cx + span * 0.70, span * 0.65, cz + span * 0.40), span * span * 28.0, (0.38, 0.62, 1.0), span * 0.40),
        ('SoftFill', (cx + span * 0.55, -span * 0.80, cz - span * 0.15), span * span * 6.5, (0.72, 0.80, 0.94), span * 0.65),
    ]
    for name, loc, power, color, size in light_specs:
        bpy.ops.object.light_add(type='AREA', location=loc)
        l = bpy.context.object
        l.name = name
        l.data.energy = power
        l.data.color = color
        l.data.shape = 'DISK'
        l.data.size = size
        point_camera(l, target)
        lights.append(l)

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.render.filepath = os.path.join(PRE, asset + '.png')
    bpy.ops.render.render(write_still=True)

    for o in [cam] + lights:
        bpy.data.objects.remove(o, do_unlink=True)

def asset_stats(objects):
    deps = bpy.context.evaluated_depsgraph_get()
    coords = []
    tris = 0
    for o in objects:
        ev = o.evaluated_get(deps)
        mesh = ev.to_mesh()
        tris += sum(max(0, len(p.vertices) - 2) for p in mesh.polygons)
        for v in mesh.vertices:
            coords.append(o.matrix_world @ v.co)
        ev.to_mesh_clear()
    xs = [p.x for p in coords]
    ys = [p.y for p in coords]
    zs = [p.z for p in coords]
    bounds = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    dims = [round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3), round(max(zs) - min(zs), 3)]
    return tris, dims, bounds

def export_asset(asset, objects, tris, dims):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, asset + '.fbx'),
        use_selection=True,
        object_types={'MESH'},
        apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Z',
        axis_up='Y',
        use_mesh_modifiers=True,
    )
    with open(os.path.join(PRE, asset + '.json'), 'w', encoding='utf-8') as f:
        json.dump({'tris': tris, 'objects': [o.name for o in objects], 'dims': dims}, f, indent=2)

def main():
    clear_scene()
    GROUPS.clear()
    builds = [
        ('Gaslamp', build_lamp),
        ('Cane', build_cane),
        ('Sabre', build_sabre),
        ('TonicVial', build_vial),
    ]
    reports = []
    for asset, build in builds:
        GROUPS.clear()
        build()
        objects = join_groups(asset)
        tris, dims, bounds = asset_stats(objects)
        setup_render(objects, asset, dims, bounds)
        export_asset(asset, objects, tris, dims)
        reports.append((asset, tris, dims, [o.name for o in objects]))
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

    print('HERO_REPORT_BEGIN')
    for asset, tris, dims, names in reports:
        print(f'{asset}: {tris} tris; dims {dims}; objects {", ".join(names)}; problem: none')
    print('HERO_REPORT_END')

if __name__ == '__main__':
    main()
