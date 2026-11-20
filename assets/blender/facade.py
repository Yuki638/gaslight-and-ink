import bpy
import bmesh
import math
import json
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "export")
RENDER_DIR = os.path.join(ROOT, "renders")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

BUDGETS = {"SashWindow": 1500, "Door": 2000, "ChimneyStack": 1500}
SMOOTH_ANGLE = math.radians(35.0)

# Grounded Victorian London 1890s dark palette (used for preview renders)
MAT_DEFS = {
    "Stone": ((0.33, 0.305, 0.27), 0.0, 0.78),
    "Wood": ((0.085, 0.042, 0.022), 0.0, 0.58),
    "Glass": ((0.045, 0.095, 0.135), 0.05, 0.08),
    "Brass": ((0.74, 0.50, 0.16), 0.78, 0.24),
    "Brick": ((0.16, 0.052, 0.036), 0.0, 0.88),
    "Clay": ((0.38, 0.145, 0.068), 0.0, 0.72),
}


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.curves,
    ):
        for b in list(coll):
            coll.remove(b)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def make_material(name):
    color, metal, rough = MAT_DEFS[name]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    if not mat.node_tree:
        mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    return mat


# ---------------------------------------------------------------------------
# Geometry helpers: explicit outward winding, hidden faces omitted,
# 2-segment bevels on visible hard edges, pure quads/tris, Smooth by Angle.
# ---------------------------------------------------------------------------

class Asset:
    def __init__(self, name):
        self.name = name
        self.parts = {}

    def bm(self, mat):
        if mat not in self.parts:
            self.parts[mat] = bmesh.new()
        return self.parts[mat]


def poly_area(poly):
    return 0.5 * sum(
        poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
        for i in range(len(poly))
    )


def bevel_and_merge(tmp, dst, bevel, segments=2):
    tmp.normal_update()
    if bevel > 0.0:
        edges = [
            e
            for e in tmp.edges
            if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(30.0)
        ]
        if edges:
            bmesh.ops.bevel(
                tmp,
                geom=edges,
                offset=bevel,
                offset_type="OFFSET",
                segments=segments,
                profile=0.5,
                affect="EDGES",
                clamp_overlap=True,
            )
    vmap = {}
    for v in tmp.verts:
        vmap[v] = dst.verts.new(v.co)
    for f in tmp.faces:
        try:
            dst.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            pass
    tmp.free()


def prism(asset, mat, poly, y_back, y_front, skip_sides=(), back=False, front=True, bevel=0.0, segs=2):
    """Extrude an XZ polygon from y_back to y_front (y_front < y_back, i.e. toward -Y street).
    Side i is the face along poly edge i -> i+1."""
    if poly_area(poly) < 0:
        poly = list(reversed(poly))
        n = len(poly)
        skip_sides = {(n - 2 - i) % n for i in skip_sides}
    n = len(poly)
    tmp = bmesh.new()
    F = [tmp.verts.new((x, y_front, z)) for x, z in poly]
    B = [tmp.verts.new((x, y_back, z)) for x, z in poly]
    if front:
        tmp.faces.new(F)
    if back:
        tmp.faces.new(list(reversed(B)))
    for i in range(n):
        j = (i + 1) % n
        if i not in skip_sides:
            tmp.faces.new([F[i], B[i], B[j], F[j]])
    bevel_and_merge(tmp, asset.bm(mat), bevel, segments=segs)


SIDE = {"-z": 0, "+x": 1, "+z": 2, "-x": 3}


def box(asset, mat, x0, x1, z0, z1, y_front, y_back=0.0, skip=("+y",), bevel=0.0, segs=2):
    poly = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    prism(
        asset,
        mat,
        poly,
        y_back,
        y_front,
        skip_sides={SIDE[s] for s in skip if s in SIDE},
        back="+y" not in skip,
        front="-y" not in skip,
        bevel=bevel,
        segs=segs,
    )


def frustum(asset, mat, bottom_half, top_half, z0, z1, bevel=0.0, segs=2):
    tmp = bmesh.new()
    (bx, by), (tx, ty) = bottom_half, top_half
    Bv = [tmp.verts.new(c) for c in [(-bx, -by, z0), (bx, -by, z0), (bx, by, z0), (-bx, by, z0)]]
    Tv = [tmp.verts.new(c) for c in [(-tx, -ty, z1), (tx, -ty, z1), (tx, ty, z1), (-tx, ty, z1)]]
    tmp.faces.new(Tv)
    for i in range(4):
        j = (i + 1) % 4
        tmp.faces.new([Bv[i], Bv[j], Tv[j], Tv[i]])
    bevel_and_merge(tmp, asset.bm(mat), bevel, segments=segs)


def lathe(asset, mat, profile, center, segs, floor=True):
    """profile: list of (r, z). Bottom ring left open (sits on stack)."""
    cx, cy, cz = center
    tmp = bmesh.new()
    rings = []
    for r, z in profile:
        rings.append(
            [
                tmp.verts.new(
                    (
                        cx + r * math.cos(2 * math.pi * k / segs),
                        cy + r * math.sin(2 * math.pi * k / segs),
                        cz + z,
                    )
                )
                for k in range(segs)
            ]
        )
    for i in range(len(rings) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            tmp.faces.new([rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]])
    if floor:
        c = tmp.verts.new((cx, cy, cz + profile[-1][1]))
        last = rings[-1]
        for k in range(segs):
            tmp.faces.new([last[k], last[(k + 1) % segs], c])
    bevel_and_merge(tmp, asset.bm(mat), 0.0)


def ngon_poly(cx, cz, r, n, start=math.pi / 8):
    return [
        (cx + r * math.cos(start + 2 * math.pi * k / n), cz + r * math.sin(start + 2 * math.pi * k / n))
        for k in range(n)
    ]


def build_objects(asset, mats):
    objs = []
    for mat_name, bm in asset.parts.items():
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=list(bm.edges))
        bm.normal_update()
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="BEAUTY")
        bm.normal_update()
        for f in bm.faces:
            f.smooth = True
        for e in bm.edges:
            if len(e.link_faces) == 2:
                e.smooth = e.calc_face_angle(math.pi) <= SMOOTH_ANGLE
            else:
                e.smooth = False
        name = f"{asset.name}_{mat_name}"
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.update()
        ob = bpy.data.objects.new(name, me)
        me.materials.append(mats[mat_name])
        objs.append(ob)
    coll = bpy.data.collections.new(asset.name)
    bpy.context.scene.collection.children.link(coll)
    for ob in objs:
        coll.objects.link(ob)
    return objs


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def build_sash_window():
    """Georgian sash window: 4.6 W x 5.8 H x 1.0 D, back flat at Y=0, origin bottom center."""
    a = Asset("SashWindow")
    S, W, G = "Stone", "Wood", "Glass"
    bs = 0.04

    # Projecting stepped limestone sill (grounded sub-sill + bold projecting sill slab)
    box(a, S, -2.14, 2.14, 0.00, 0.10, -0.88, skip=("+y", "+z"), bevel=0.025)
    box(a, S, -2.30, 2.30, 0.10, 0.42, -1.00, skip=("+y",), bevel=bs)

    # Stone jambs (architrave sides with subtle stepped outer shoulder)
    for sgn in (-1, 1):
        outer = "-x" if sgn < 0 else "+x"
        inner = "+x" if sgn < 0 else "-x"
        x0, x1 = sorted((sgn * 1.42, sgn * 1.98))
        box(a, S, x0, x1, 0.42, 4.94, -0.52, skip=("+y", "-z", "+z"), bevel=bs)
        o0, o1 = sorted((sgn * 1.98, sgn * 2.08))
        box(a, S, o0, o1, 0.42, 4.94, -0.34, skip=("+y", "-z", "+z", inner), bevel=0.025)

    # Keystone lintel: tapered dropped keystone flanked by stone lintel halves
    kb, kt, lz0, lz1 = 0.30, 0.42, 4.94, 5.56
    prism(a, S, [(-2.18, lz0), (-kb, lz0), (-kt, lz1), (-2.18, lz1)], 0.0, -0.60, skip_sides={1, 2}, bevel=bs)
    prism(a, S, [(kb, lz0), (2.18, lz0), (2.18, lz1), (kt, lz1)], 0.0, -0.60, skip_sides={2, 3}, bevel=bs)
    # Dropped keystone projects forward & slightly below lintel soffit for clear Georgian silhouette
    prism(a, S, [(-kb + 0.01, lz0 - 0.08), (kb - 0.01, lz0 - 0.08), (kt, lz1), (-kt, lz1)],
          0.0, -0.76, skip_sides={2}, bevel=0.035)

    # Cornice hood cap (top at Z=5.80)
    box(a, S, -2.30, 2.30, 5.56, 5.80, -0.84, skip=("+y",), bevel=bs)

    # Recessed wooden box frame
    bw = 0.025
    box(a, W, -1.42, -1.25, 0.42, 4.94, -0.36, skip=("+y", "-x", "-z", "+z"), bevel=bw)
    box(a, W, 1.25, 1.42, 0.42, 4.94, -0.36, skip=("+y", "+x", "-z", "+z"), bevel=bw)
    box(a, W, -1.25, 1.25, 4.78, 4.94, -0.36, skip=("+y", "+z", "-x", "+x"), bevel=bw)
    box(a, W, -1.25, 1.25, 0.42, 0.56, -0.36, skip=("+y", "-z", "-x", "+x"), bevel=bw)

    # Two sashes: lower (inner, y=-0.20) and upper (outer, y=-0.28) with crisp meeting rail
    bsh = 0.018
    zl0, zm, zu1 = 0.56, 2.68, 4.78
    for sgn in (-1, 1):
        x0, x1 = sorted((sgn * 1.25, sgn * 1.13))
        outer = "-x" if sgn < 0 else "+x"
        box(a, W, x0, x1, zl0, zm, -0.20, skip=("+y", outer, "-z", "+z"), bevel=bsh)
        box(a, W, x0, x1, zm, zu1, -0.28, skip=("+y", outer, "+z"), bevel=bsh)
    # Bottom rail, lower meeting rail, upper meeting rail, top rail
    box(a, W, -1.13, 1.13, zl0, 0.76, -0.20, skip=("+y", "-z", "-x", "+x"), bevel=bsh)
    box(a, W, -1.13, 1.13, 2.58, zm, -0.20, skip=("+y", "+z", "-x", "+x"), bevel=bsh)
    box(a, W, -1.13, 1.13, zm, 2.79, -0.28, skip=("+y", "-x", "+x"), bevel=bsh)
    box(a, W, -1.13, 1.13, 4.65, zu1, -0.28, skip=("+y", "+z", "-x", "+x"), bevel=bsh)

    # Glass panes (ONE separate object) + 6-over-6 glazing bars cleanly in front
    for (gz0, gz1, gy, by) in ((0.76, 2.58, -0.09, -0.17), (2.79, 4.65, -0.14, -0.23)):
        box(a, G, -1.13, 1.13, gz0, gz1, gy, y_back=gy, skip=("+y", "-x", "+x", "-z", "+z"))
        half = 0.032
        cols = [-1.13 + 2.26 * k / 3.0 for k in (1, 2)]
        for cx in cols:
            box(a, W, cx - half, cx + half, gz0, gz1, by, y_back=gy, skip=("+y", "-z", "+z"), bevel=0.008)
        zc = 0.5 * (gz0 + gz1)
        edges = [-1.13, cols[0] - half, cols[0] + half, cols[1] - half, cols[1] + half, 1.13]
        for k in range(0, 6, 2):
            box(a, W, edges[k], edges[k + 1], zc - half, zc + half, by, y_back=gy,
                skip=("+y", "-x", "+x"), bevel=0.008)
    return a


def build_door():
    """Victorian four-panel front door: 5.6 W x 1.2 D x 8.3 H (0.5 step + 5.2 x 7.8 surround),
    semicircular-looking fanlight inside the 7.8 surround, brass knob, letter plate & knocker."""
    a = Asset("Door")
    S, W, B, G = "Stone", "Wood", "Brass", "Glass"
    bs = 0.04

    # Stone step: 5.6 wide x 0.5 tall x 1.2 deep
    box(a, S, -2.80, 2.80, 0.00, 0.50, -1.20, skip=("+y",), bevel=0.045)

    # Pilasters (plinth, shaft with raised fillet, capital) flush at X=+-2.00 inside 5.2 x 7.8 surround
    for sgn in (-1, 1):
        p0, p1 = sorted((sgn * 2.00, sgn * 2.54))
        s0, s1 = sorted((sgn * 2.00, sgn * 2.46))
        c0, c1 = sorted((sgn * 2.00, sgn * 2.56))
        box(a, S, p0, p1, 0.50, 1.25, -0.56, skip=("+y", "-z"), bevel=bs)
        box(a, S, s0, s1, 1.25, 7.76, -0.46, skip=("+y", "-z", "+z"), bevel=bs)
        box(a, S, c0, c1, 7.76, 8.00, -0.58, skip=("+y", "+z"), bevel=0.032)
        # Fluted/panelled vertical strip on pilaster shaft
        f0, f1 = sorted((sgn * 2.13, sgn * 2.33))
        box(a, S, f0, f1, 1.50, 7.50, -0.52, y_back=-0.46, skip=("+y",), bevel=0.018)

    # Cornice hood (two stepped tiers reaching Z=8.30, width 5.20)
    box(a, S, -2.54, 2.54, 8.00, 8.12, -0.70, skip=("+y", "+z"), bevel=0.028)
    box(a, S, -2.60, 2.60, 8.12, 8.30, -0.90, skip=("+y",), bevel=bs)

    # Semicircular-looking fanlight inside the 7.8 surround height (Z=6.96..7.90, span 3.12, height 0.94)
    N = 12
    cz, ax, bz = 6.96, 1.56, 0.94
    ty = 8.00
    arc = [(-ax * math.cos(math.pi * k / N), cz + bz * math.sin(math.pi * k / N)) for k in range(N + 1)]
    outer = [(-2.00, cz), (-2.00, ty)] + [(arc[k][0], ty) for k in range(2, N - 1)] + [(2.00, ty), (2.00, cz)]

    tmp = bmesh.new()
    yf = -0.38
    AF = [tmp.verts.new((x, yf, z)) for x, z in arc]
    AB = [tmp.verts.new((x, 0.0, z)) for x, z in arc]
    OF = [tmp.verts.new((x, yf, z)) for x, z in outer]
    for k in range(N):
        tmp.faces.new([AF[k], AF[k + 1], OF[k + 1], OF[k]])
        tmp.faces.new([AF[k], AB[k], AB[k + 1], AF[k + 1]])
    # Soffit undersides resting on transom
    for (af, ab, of) in ((AF[0], AB[0], OF[0]), (AF[N], AB[N], OF[N])):
        ob = tmp.verts.new((of.co.x, 0.0, cz))
        f = tmp.faces.new([af, ab, ob, of])
        f.normal_update()
        if f.normal.z > 0:
            f.normal_flip()
    bevel_and_merge(tmp, a.bm(S), 0.025)

    # Small projecting stone keystone at apex of fanlight arch
    prism(a, S, [(-0.18, 7.82), (0.18, 7.82), (0.24, 8.00), (-0.24, 8.00)],
          -0.38, -0.48, skip_sides={2}, bevel=0.02)

    # Fanlight glass (single smooth fan surface) + wooden semicircular hub & 5 radial spokes
    gy, sy = -0.15, -0.24
    tmp = bmesh.new()
    c = tmp.verts.new((0.0, gy, cz))
    ring = [tmp.verts.new((x, gy, z)) for x, z in arc]
    for k in range(N):
        tmp.faces.new([c, ring[k + 1], ring[k]])
    bevel_and_merge(tmp, a.bm(G), 0.0)

    hub_r = (0.38, 0.24)
    hub = [(hub_r[0] * math.cos(math.pi * k / 6), cz + hub_r[1] * math.sin(math.pi * k / 6)) for k in range(7)]
    prism(a, W, hub, gy, sy, skip_sides={6}, bevel=0.01)
    for k in (2, 4, 6, 8, 10):
        t = math.pi * k / N
        dx, dz = -math.cos(t), math.sin(t)
        p0 = (hub_r[0] * dx * 0.94, cz + hub_r[1] * dz * 0.94)
        p1 = (ax * dx * 0.99, cz + bz * dz * 0.99)
        vx, vz = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(vx, vz)
        nx, nz = -vz / ln * 0.028, vx / ln * 0.028
        prism(
            a,
            W,
            [(p0[0] - nx, p0[1] - nz), (p1[0] - nx, p1[1] - nz),
             (p1[0] + nx, p1[1] + nz), (p0[0] + nx, p0[1] + nz)],
            gy,
            sy,
            skip_sides={0, 2},
        )

    # Crisp wooden transom bar dividing door leaf from fanlight
    box(a, W, -2.00, 2.00, 6.80, cz, -0.34, skip=("+y", "-x", "+x"), bevel=0.02)

    # Four-panel Victorian door leaf (4.0 wide, Z=0.50..6.80)
    bw = 0.025
    ld = -0.26
    # Outer stiles, top rail, lock rail, bottom kick rail, center mullions
    box(a, W, -2.00, -1.60, 0.50, 6.80, ld, skip=("+y", "-x", "-z", "+z"), bevel=bw)
    box(a, W, 1.60, 2.00, 0.50, 6.80, ld, skip=("+y", "+x", "-z", "+z"), bevel=bw)
    box(a, W, -1.60, 1.60, 6.42, 6.80, ld, skip=("+y", "+z", "-x", "+x"), bevel=bw)
    box(a, W, -1.60, 1.60, 3.24, 3.76, ld, skip=("+y", "-x", "+x"), bevel=bw)
    box(a, W, -1.60, 1.60, 0.50, 1.16, ld, skip=("+y", "-z", "-x", "+x"), bevel=bw)
    box(a, W, -0.18, 0.18, 1.16, 3.24, ld, skip=("+y", "-z", "+z"), bevel=bw)
    box(a, W, -0.18, 0.18, 3.76, 6.42, ld, skip=("+y", "-z", "+z"), bevel=bw)

    # Four recessed + raised chamfered panels
    for (x0, x1) in ((-1.60, -0.18), (0.18, 1.60)):
        for (z0, z1) in ((1.16, 3.24), (3.76, 6.42)):
            box(a, W, x0, x1, z0, z1, -0.11, skip=("+y", "-x", "+x", "-z", "+z"))
            box(a, W, x0 + 0.15, x1 - 0.15, z0 + 0.15, z1 - 0.15, -0.20, y_back=-0.11,
                skip=("+y",), bevel=0.048)

    # Brass hardware: letter plate, octagonal Victorian knob, readable stirrup knocker
    # 1. Letter plate (centered on lock rail Z=3.50)
    box(a, B, -0.54, 0.54, 3.35, 3.65, -0.31, y_back=ld, skip=("+y",), bevel=0.015)
    box(a, B, -0.44, 0.44, 3.43, 3.56, -0.35, y_back=-0.31, skip=("+y",), bevel=0.012)

    # 2. Doorknob (right stile X=1.78, Z=3.50; faceted octagonal knob = non-uniform-scale friendly)
    box(a, B, 1.68, 1.88, 3.30, 3.70, -0.30, y_back=ld, skip=("+y",), bevel=0.012)
    prism(a, B, ngon_poly(1.78, 3.50, 0.046, 8), -0.30, -0.39, back=False, front=False)
    prism(a, B, ngon_poly(1.78, 3.50, 0.105, 8), -0.39, -0.51, back=True, front=True, bevel=0.025)

    # 3. Door knocker (centered on upper mullion Z=4.86..5.66)
    box(a, B, -0.17, 0.17, 4.92, 5.66, -0.31, y_back=ld, skip=("+y",), bevel=0.015)
    # Top hinge boss
    box(a, B, -0.16, 0.16, 5.46, 5.58, -0.41, y_back=-0.31, skip=("+y",), bevel=0.012)
    # Side arms of hanging stirrup clapper (clear open window in center!)
    for sgn in (-1, 1):
        ax0, ax1 = sorted((sgn * 0.10, sgn * 0.16))
        box(a, B, ax0, ax1, 5.06, 5.48, -0.41, y_back=-0.35, skip=("-z", "+z"), bevel=0.01)
    # Weighted bottom hammer bar
    box(a, B, -0.17, 0.17, 4.92, 5.07, -0.44, y_back=-0.34, skip=(), bevel=0.016)
    # Strike stud on backplate behind hammer
    box(a, B, -0.05, 0.05, 4.97, 5.05, -0.34, y_back=-0.31, skip=("+y",))
    return a


def build_chimney():
    """Brick chimney stack: 3.0 x 2.6 footprint, 5.4 tall + corbelled stone/brick cap band
    + 3 clay chimney pots (0.8 dia, 1.8 tall, slight flare at top). Origin bottom center."""
    a = Asset("ChimneyStack")
    K, S, C = "Brick", "Stone", "Clay"
    bb = 0.035

    # Base plinth (exact 3.0 x 2.6 footprint at roof line Z=0)
    box(a, K, -1.50, 1.50, 0.00, 0.36, -1.30, y_back=1.30, skip=("-z",), bevel=bb)
    # Main brick shaft (slight 0.06 set-in above plinth for clean Victorian shoulder)
    box(a, K, -1.44, 1.44, 0.36, 3.74, -1.24, y_back=1.24, skip=("-z", "+z"), bevel=bb)
    # Brick necking band to break up tall shaft silhouette
    box(a, K, -1.52, 1.52, 3.74, 3.94, -1.32, y_back=1.32, skip=(), bevel=0.03)
    # Upper neck shaft under corbels
    box(a, K, -1.44, 1.44, 3.94, 4.30, -1.24, y_back=1.24, skip=("-z", "+z"), bevel=bb)
    # Corbelled brick courses flaring out under stone cap
    box(a, K, -1.56, 1.56, 4.30, 4.54, -1.36, y_back=1.36, skip=("+z",), bevel=bb)
    box(a, K, -1.68, 1.68, 4.54, 4.78, -1.48, y_back=1.48, skip=("+z",), bevel=bb)
    # Projecting limestone cap band
    box(a, S, -1.76, 1.76, 4.78, 5.06, -1.56, y_back=1.56, skip=(), bevel=0.04)
    # Upper brick curb above cap band
    box(a, K, -1.48, 1.48, 5.06, 5.26, -1.28, y_back=1.28, skip=("-z",), bevel=0.03)
    # Sloped stone flaunching crown reaching Z=5.40
    frustum(a, S, (1.44, 1.08), (1.38, 0.56), 5.26, 5.40, bevel=0.025)

    # 3 Victorian terracotta chimney pots: 0.80 max diameter, 1.80 tall, neck collar + top flare
    profile = [
        (0.39, 0.00),
        (0.36, 0.14),
        (0.34, 1.05),
        (0.33, 1.34),
        (0.365, 1.43),
        (0.34, 1.51),
        (0.40, 1.70),
        (0.40, 1.78),
        (0.37, 1.80),
        (0.30, 1.80),
        (0.28, 1.44),
    ]
    for px in (-0.98, 0.0, 0.98):
        lathe(a, C, profile, (px, 0.0, 5.40), 12)
    return a


# ---------------------------------------------------------------------------
# Validation, FBX export, EEVEE preview
# ---------------------------------------------------------------------------

def tri_count(objs):
    return sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)


def world_bounds(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def check(name, objs, wall_piece):
    problems = []
    tris = tri_count(objs)
    if tris > BUDGETS[name]:
        problems.append(f"over budget {tris}>{BUDGETS[name]}")
    if len(objs) > 4:
        problems.append("more than 4 materials")
    for o in objs:
        me = o.data
        ngons = sum(1 for p in me.polygons if len(p.vertices) > 4)
        if ngons:
            problems.append(f"{o.name}: {ngons} n-gons")
        zero = sum(1 for p in me.polygons if p.area < 1e-7)
        if zero:
            problems.append(f"{o.name}: {zero} zero-area faces")
        if wall_piece:
            back = sum(1 for p in me.polygons if p.center.y > -1e-4 and p.normal.y > 0.5)
            behind = sum(1 for v in me.vertices if v.co.y > 1e-4)
            if back or behind:
                problems.append(f"{o.name}: geometry behind wall plane")
    mn, mx = world_bounds(objs)
    if abs(mn.z) > 1e-4:
        problems.append(f"min z {mn.z:.4f} != 0")
    if abs((mn.x + mx.x) * 0.5) > 1e-4:
        problems.append(f"x center {(mn.x + mx.x) * 0.5:.4f} != 0")
    if wall_piece:
        if abs(mx.y) > 1e-4:
            problems.append(f"max y {mx.y:.4f} != 0")
    else:
        if abs((mn.y + mx.y) * 0.5) > 1e-4:
            problems.append(f"y center {(mn.y + mx.y) * 0.5:.4f} != 0")
    return tris, problems


def export_fbx(name, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT_DIR, name + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="EDGE",
        bake_anim=False,
    )


def point_at(obj, target):
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_render_scene():
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE"
    except TypeError:
        scene.render.engine = "BLENDER_WORKBENCH"
    if scene.render.engine == "BLENDER_EEVEE":
        scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.0

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    if not world.node_tree:
        world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.026, 0.040, 0.064, 1.0)
    bg.inputs["Strength"].default_value = 0.75

    cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
    cam.data.lens = 50.0
    scene.collection.objects.link(cam)
    scene.camera = cam

    key = bpy.data.objects.new("WarmKey", bpy.data.lights.new("WarmKey", "AREA"))
    key.data.shape = "DISK"
    key.data.color = (1.0, 0.72, 0.44)
    rim = bpy.data.objects.new("CoolRim", bpy.data.lights.new("CoolRim", "AREA"))
    rim.data.shape = "DISK"
    rim.data.color = (0.42, 0.68, 1.0)
    for o in (key, rim):
        scene.collection.objects.link(o)
    return cam, key, rim


def render_preview(name, objs, wall_piece, cam, key, rim):
    scene = bpy.context.scene
    for coll in bpy.data.collections:
        coll.hide_render = coll.name != name
    mn, mx = world_bounds(objs)
    center = (mn + mx) * 0.5
    radius = (mx - mn).length * 0.5

    if wall_piece:
        direction = Vector((0.52, -1.0, 0.28)).normalized()
    else:
        direction = Vector((0.66, -0.94, 0.46)).normalized()

    fov = 2.0 * math.atan(18.0 / cam.data.lens)
    dist = (radius / math.sin(fov * 0.5)) * 1.12
    cam.location = center + direction * dist
    cam.data.clip_start = 0.05
    cam.data.clip_end = dist * 4.0
    point_at(cam, center)

    scale_p = max(1.0, radius * radius)
    key.location = center + Vector((radius * 1.4, -radius * 2.3, radius * 1.8))
    key.data.energy = 195.0 * scale_p
    key.data.size = radius * 1.3
    point_at(key, center)

    if wall_piece:
        rim.location = center + Vector((-radius * 2.1, -radius * 0.9, radius * 1.4))
    else:
        rim.location = center + Vector((-radius * 2.0, radius * 1.5, radius * 1.5))
    rim.data.energy = 145.0 * scale_p
    rim.data.size = radius * 1.1
    point_at(rim, center)

    scene.render.filepath = os.path.join(RENDER_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)


def main():
    clear_scene()
    mats = {k: make_material(k) for k in MAT_DEFS}
    builds = [(build_sash_window(), True), (build_door(), True), (build_chimney(), False)]
    assets = [(a.name, build_objects(a, mats), wall) for a, wall in builds]
    cam, key, rim = setup_render_scene()
    report = []
    for name, objs, wall in assets:
        tris, problems = check(name, objs, wall)
        mn, mx = world_bounds(objs)
        dims = [round(v, 3) for v in (mx - mn)]
        export_fbx(name, objs)
        render_preview(name, objs, wall, cam, key, rim)
        with open(os.path.join(RENDER_DIR, name + ".json"), "w", encoding="utf-8") as fh:
            json.dump({"tris": tris, "objects": [o.name for o in objs], "dims": dims}, fh, indent=2)
        report.append(
            f"{name}: {tris}/{BUDGETS[name]} tris; dims {dims}; "
            f"objects {', '.join(o.name for o in objs)}; problems: {'; '.join(problems) or 'none'}"
        )
    print("FACADE_REPORT_BEGIN")
    for line in report:
        print(line)
    print("FACADE_REPORT_END")


if __name__ == "__main__":
    main()
