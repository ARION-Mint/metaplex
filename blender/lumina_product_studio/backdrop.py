# SPDX-License-Identifier: GPL-3.0-or-later
"""Backdrops (cove, dome, corner, floor, shadow catcher), stage and set dressing.

All backdrop geometry is generated in a local frame where the product sits
at the origin, +Y points away from the camera and Z=0 is the floor. The
objects are then rotated to face the current shot, so changing the shot only
updates a transform instead of rebuilding meshes.
"""

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import utils
from .utils import settings

BACKDROP = "BACKDROP"
STAGE = "STAGE"
DECOR = "DECOR"

FINISH_ROUGHNESS = {"MATTE": 0.75, "SATIN": 0.38, "GLOSS": 0.12, "MIRROR": 0.02}
WALL_ROUGHNESS = 0.9


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------

def _mesh(name, verts, faces, face_uvs, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uv = me.uv_layers.new(name="UVMap")
    loop = 0
    for poly, uvs in zip(me.polygons, face_uvs):
        for i in range(poly.loop_total):
            uv.data[poly.loop_start + i].uv = uvs[i]
        loop += poly.loop_total
    for poly in me.polygons:
        poly.use_smooth = smooth
    me.update()
    return me


def _profile_cove(front, wall, radius, height, samples=28):
    """(y, z) profile: floor -> quarter fillet -> wall. Returns points, arc lengths."""
    radius = max(1e-4, min(radius, wall + front - 1e-3, height - 1e-3))
    pts = [Vector((-front, 0.0))]
    y0 = wall - radius
    if y0 > -front:
        pts.append(Vector((y0, 0.0)))
    for i in range(1, samples + 1):
        th = (math.pi / 2) * i / samples
        pts.append(Vector((y0 + radius * math.sin(th), radius - radius * math.cos(th))))
    pts.append(Vector((wall, height)))
    arcs = [0.0]
    for a, b in zip(pts, pts[1:]):
        arcs.append(arcs[-1] + (b - a).length)
    return pts, arcs


def _extrude_profile(name, pts, arcs, width, columns=6):
    verts = []
    for j in range(columns + 1):
        x = -width / 2 + width * j / columns
        for p in pts:
            verts.append((x, p.x, p.y))
    n = len(pts)
    total = arcs[-1]
    faces, uvs = [], []
    for j in range(columns):
        for i in range(n - 1):
            a = j * n + i
            b = (j + 1) * n + i
            faces.append((a, b, b + 1, a + 1))
            u0, u1 = j / columns, (j + 1) / columns
            v0, v1 = arcs[i] / total, arcs[i + 1] / total
            uvs.append(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
    return _mesh(name, verts, faces, uvs)


def _profile_dome(radius, fillet, wall_h, samples=24):
    """(r, z) profile for a closed dome: floor -> fillet -> wall -> cap."""
    fillet = max(1e-4, min(fillet, radius * 0.9, wall_h * 0.9))
    pts = [Vector((radius * 0.002, 0.0)), Vector((radius - fillet, 0.0))]
    for i in range(1, samples + 1):
        th = (math.pi / 2) * i / samples
        pts.append(Vector((radius - fillet + fillet * math.sin(th), fillet - fillet * math.cos(th))))
    pts.append(Vector((radius, wall_h)))
    for i in range(1, samples + 1):
        ph = (math.pi / 2) * i / samples
        pts.append(Vector((max(radius * 0.002, radius * math.cos(ph)), wall_h + radius * math.sin(ph))))
    arcs = [0.0]
    for a, b in zip(pts, pts[1:]):
        arcs.append(arcs[-1] + (b - a).length)
    return pts, arcs


def _revolve(name, pts, arcs, segments=128, planar_uv=False):
    verts = []
    for j in range(segments):
        ang = 2 * math.pi * j / segments
        c, s_ = math.cos(ang), math.sin(ang)
        for p in pts:
            verts.append((p.x * c, p.x * s_, p.y))
    n = len(pts)
    total = arcs[-1]
    rmax = max(p.x for p in pts)
    faces, uvs = [], []
    for j in range(segments):
        jn = (j + 1) % segments
        for i in range(n - 1):
            a, b = j * n + i, jn * n + i
            faces.append((a, a + 1, b + 1, b))
            if planar_uv:
                quad = [verts[k] for k in (a, a + 1, b + 1, b)]
                uvs.append(tuple((v[0] / (2 * rmax) + 0.5, v[1] / (2 * rmax) + 0.5) for v in quad))
            else:
                u0, u1 = j / segments, (j + 1) / segments
                v0, v1 = arcs[i] / total, arcs[i + 1] / total
                uvs.append(((u0, v0), (u0, v1), (u1, v1), (u1, v0)))
    return _mesh(name, verts, faces, uvs)


# --------------------------------------------------------------------------
# Frame / placement
# --------------------------------------------------------------------------

def stage_height(scene):
    s = settings(scene)
    b = utils.stored_bounds(scene)
    if b is None or s.stage == "NONE":
        return 0.0
    return s.stage_height * b[4]


def floor_z(scene):
    b = utils.stored_bounds(scene)
    return (b[0].z if b else 0.0) - stage_height(scene)


def backdrop_azimuth(scene):
    from . import camera
    return camera.shot_angles(scene)[0]


def wall_frame(scene):
    """origin (floor under product), right, away, wall distance, floor z."""
    b = utils.stored_bounds(scene)
    if b is None:
        return None
    s = settings(scene)
    size = b[4]
    az = backdrop_azimuth(scene)
    right, away, _up = utils.view_basis(az)
    fz = floor_z(scene)
    origin = Vector((b[2].x, b[2].y, fz))
    return origin, right, away, s.wall_distance * size, fz


def _place(scene, obj):
    b = utils.stored_bounds(scene)
    obj.location = (b[2].x, b[2].y, floor_z(scene))
    obj.rotation_euler = (0.0, 0.0, backdrop_azimuth(scene))


def update_orientation(scene):
    for obj in utils.objects_with_role(scene, BACKDROP, STAGE, DECOR):
        _place(scene, obj)


def exists(scene):
    return bool(utils.objects_with_role(scene, BACKDROP, STAGE, DECOR))


# --------------------------------------------------------------------------
# Backdrop material
# --------------------------------------------------------------------------

MAT_PREFIX = "Lumina Backdrop"


def _material(scene, prefix):
    for mat in bpy.data.materials:
        if mat.get("lumina_scene") == scene.name_full and mat.get("lumina_kind") == prefix:
            return mat
    mat = bpy.data.materials.new(prefix)
    mat["lumina_scene"] = scene.name_full
    mat["lumina_kind"] = prefix
    if hasattr(mat, "use_nodes"):
        try:
            mat.use_nodes = True
        except AttributeError:
            pass
    return mat


def _capture_ramp(mat):
    nt = mat.node_tree
    node = nt.nodes.get("Lumina Ramp") if nt else None
    if node is None:
        return None
    cr = node.color_ramp
    return dict(interp=cr.interpolation,
                stops=[(e.position, tuple(e.color)) for e in cr.elements])


def _restore_ramp(node, state):
    cr = node.color_ramp
    cr.interpolation = state["interp"]
    stops = state["stops"]
    while len(cr.elements) > len(stops):
        cr.elements.remove(cr.elements[-1])
    while len(cr.elements) < len(stops):
        cr.elements.new(0.5)
    for e, (pos, col) in zip(cr.elements, stops):
        e.position = pos
        e.color = col


def _math(nt, op, a=None, b=None, loc=(0, 0), name=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.location = loc
    n.use_clamp = clamp
    if name:
        n.name = name
        n.label = name
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n


def build_material(scene, geo, reset_ramp=False):
    """geo: dict(W, L, u0, v0, yc, yfe, arc) in metres for the gradient maths."""
    s = settings(scene)
    mat = _material(scene, MAT_PREFIX)
    state = None if reset_ramp else _capture_ramp(mat)
    for k, v in geo.items():
        mat[k] = v
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (1400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.name = "Lumina BSDF"
    bsdf.location = (1100, 0)
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])

    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-900, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-700, 0)
    nt.links.new(tc.outputs["UV"], sep.inputs[0])

    X = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", sep.outputs["X"], geo["u0"], (-500, 120)).outputs[0], geo["W"], (-320, 120), "Lumina X")
    Y = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", sep.outputs["Y"], geo["v0"], (-500, -80)).outputs[0], geo["L"], (-320, -80), "Lumina Y")

    if s.gradient == "LINEAR":
        a = math.radians(s.gradient_angle)
        px = _math(nt, "MULTIPLY", X.outputs[0], math.sin(a), (-140, 120), "Lumina SinA")
        py = _math(nt, "MULTIPLY", Y.outputs[0], math.cos(a), (-140, -80), "Lumina CosA")
        g = _math(nt, "ADD", px.outputs[0], py.outputs[0], (40, 0))
    elif s.gradient == "RADIAL":
        dy = _math(nt, "SUBTRACT", Y.outputs[0], geo["yc"], (-140, -80), "Lumina Yc")
        x2 = _math(nt, "MULTIPLY", X.outputs[0], X.outputs[0], (40, 120))
        y2 = _math(nt, "MULTIPLY", dy.outputs[0], dy.outputs[0], (40, -80))
        g = _math(nt, "SQRT", _math(nt, "ADD", x2.outputs[0], y2.outputs[0], (200, 0)).outputs[0], None, (340, 0))
    else:
        g = _math(nt, "MULTIPLY", X.outputs[0], 0.0, (40, 0))
    size = utils.stored_bounds(scene)[4]
    span = _math(nt, "DIVIDE", g.outputs[0], max(1e-4, s.gradient_span * size), (500, 0), "Lumina Span")
    off = _math(nt, "ADD", span.outputs[0], s.gradient_offset, (650, 0), "Lumina Offset", clamp=True)

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.name = "Lumina Ramp"
    ramp.label = "Backdrop Gradient"
    ramp.location = (800, 0)
    nt.links.new(off.outputs[0], ramp.inputs["Fac"])
    if state is not None:
        _restore_ramp(ramp, state)
    else:
        sync_ramp_colors(scene, ramp)
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    # Self glow is seen by the camera only, so it cleans up the backdrop
    # without turning the whole set into a giant light that washes out the product.
    path = nt.nodes.new("ShaderNodeLightPath")
    path.location = (800, 300)
    glow = _math(nt, "MULTIPLY", path.outputs["Is Camera Ray"], s.glow, (950, 300), "Lumina Glow")
    nt.links.new(glow.outputs[0], bsdf.inputs["Emission Strength"])

    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.name = "Lumina Roughness"
    rough.location = (800, -300)
    rough.clamp = True
    nt.links.new(Y.outputs[0], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    update_material_values(scene)
    return mat


def sync_ramp_colors(scene, ramp=None):
    s = settings(scene)
    if ramp is None:
        mat = _material(scene, MAT_PREFIX)
        ramp = mat.node_tree.nodes.get("Lumina Ramp") if mat.node_tree else None
        if ramp is None:
            return
    cr = ramp.color_ramp
    first, last = cr.elements[0], cr.elements[-1]
    first.color = (*tuple(s.color_a), 1.0)
    last.color = (*tuple(s.color_b), 1.0)
    if len(cr.elements) == 2:
        first.position = 0.0
        last.position = 1.0


def update_material_values(scene):
    s = settings(scene)
    mat = None
    for m in bpy.data.materials:
        if m.get("lumina_scene") == scene.name_full and m.get("lumina_kind") == MAT_PREFIX:
            mat = m
    if mat is None or mat.node_tree is None or utils.stored_bounds(scene) is None:
        return
    nodes = mat.node_tree.nodes
    size = utils.stored_bounds(scene)[4]
    if "Lumina Glow" in nodes:
        nodes["Lumina Glow"].inputs[1].default_value = s.glow
    a = math.radians(s.gradient_angle)
    if "Lumina SinA" in nodes:
        nodes["Lumina SinA"].inputs[1].default_value = math.sin(a)
        nodes["Lumina CosA"].inputs[1].default_value = math.cos(a)
    if "Lumina Span" in nodes:
        nodes["Lumina Span"].inputs[1].default_value = max(1e-4, s.gradient_span * size)
        nodes["Lumina Offset"].inputs[1].default_value = s.gradient_offset
    rough = nodes.get("Lumina Roughness")
    if rough is not None:
        yfe = mat.get("yfe", 1e6)
        rough.inputs["From Min"].default_value = yfe
        rough.inputs["From Max"].default_value = yfe + max(1e-4, mat.get("arc", 1.0))
        rough.inputs["To Min"].default_value = s.floor_roughness
        rough.inputs["To Max"].default_value = WALL_ROUGHNESS if s.matte_wall else s.floor_roughness


# --------------------------------------------------------------------------
# Backdrop builders
# --------------------------------------------------------------------------

def _dims(scene):
    s = settings(scene)
    lo, hi, center, dims, size = utils.stored_bounds(scene)
    scale = s.studio_scale
    cam_d = max(s.cam_distance, size * 3.0)
    return size, scale, cam_d, dims


def _build_cove(scene, corner=False):
    s = settings(scene)
    size, scale, cam_d, dims = _dims(scene)
    wall = s.wall_distance * size
    radius = (0.02 * size) if corner else s.curve_radius * size
    front = max(14.0 * size, cam_d * 2.5) * scale
    height = max(10.0 * size, cam_d * 1.5) * scale
    width = max(24.0 * size, cam_d * 3.0) * scale
    pts, arcs = _profile_cove(front, wall, radius, height)
    me = _extrude_profile("Lumina Cove", pts, arcs, width)
    y_floor_end = arcs[1] if len(pts) > 2 else 0.0
    arc = (math.pi / 2) * radius
    # wall point level with the product centre (glow centre)
    zc = utils.stored_bounds(scene)[2].z - floor_z(scene)
    yc = y_floor_end + arc + max(0.0, zc - radius) if zc > radius else y_floor_end + radius * math.acos(max(-1, min(1, 1 - zc / radius)))
    geo = dict(W=width, L=arcs[-1], u0=0.5, v0=front / arcs[-1], yc=yc - front, yfe=y_floor_end - front, arc=arc)
    return me, geo


def _build_dome(scene):
    s = settings(scene)
    size, scale, cam_d, dims = _dims(scene)
    radius = max(s.wall_distance * size, cam_d * 1.6) * scale
    fillet = s.curve_radius * size
    wall_h = max(radius * 0.6, size * 4.0)
    pts, arcs = _profile_dome(radius, fillet, wall_h)
    me = _revolve("Lumina Dome", pts, arcs)
    y_floor_end = arcs[1]
    arc = (math.pi / 2) * fillet
    zc = utils.stored_bounds(scene)[2].z - floor_z(scene)
    yc = y_floor_end + arc + max(0.0, zc - fillet)
    geo = dict(W=0.0, L=arcs[-1], u0=0.5, v0=0.0, yc=yc, yfe=y_floor_end, arc=arc)
    return me, geo


def _build_floor(scene, catcher=False):
    size, scale, cam_d, dims = _dims(scene)
    radius = max(30.0 * size, cam_d * 6.0) * scale
    pts = [Vector((radius * 0.002, 0.0))] + [Vector((radius * (i / 12) ** 1.5, 0.0)) for i in range(1, 13)]
    arcs = [p.x for p in pts]
    me = _revolve("Lumina Floor", pts, arcs, segments=96, planar_uv=True)
    geo = dict(W=2 * radius, L=2 * radius, u0=0.5, v0=0.5, yc=0.0, yfe=1e6, arc=1.0)
    return me, geo


def build(scene, reset_ramp=False):
    remove(scene)
    s = settings(scene)
    if utils.stored_bounds(scene) is None:
        return
    kind = s.backdrop
    if kind != "NONE":
        if kind in {"COVE", "CORNER"}:
            me, geo = _build_cove(scene, corner=(kind == "CORNER"))
        elif kind == "DOME":
            me, geo = _build_dome(scene)
        else:
            me, geo = _build_floor(scene, catcher=(kind == "CATCHER"))
        obj = utils.new_object(scene, "Lumina " + kind.title(), me, BACKDROP, "BACKDROP")
        _place(scene, obj)
        if kind == "CATCHER":
            obj.is_shadow_catcher = True
            if s.prev_film_transparent < 0:
                s.prev_film_transparent = int(scene.render.film_transparent)
            scene.render.film_transparent = True
            mat = _material(scene, "Lumina Catcher")
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf is not None:
                bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
            me.materials.append(mat)
        else:
            mat = build_material(scene, geo, reset_ramp=reset_ramp)
            me.materials.append(mat)
    build_stage(scene)
    build_decor(scene)


def remove(scene, restore_film=False):
    utils.delete_roles(scene, BACKDROP, STAGE, DECOR)
    s = settings(scene)
    if s.prev_film_transparent >= 0 and (restore_film or s.backdrop != "CATCHER"):
        scene.render.film_transparent = bool(s.prev_film_transparent)
        s.prev_film_transparent = -1


# --------------------------------------------------------------------------
# Stage (podium the product stands on)
# --------------------------------------------------------------------------

STAGE_FINISH = {
    "MATTE": dict(rough=0.7),
    "SATIN": dict(rough=0.35),
    "GLOSS": dict(rough=0.08),
    "METAL": dict(rough=0.22, metal=1.0),
    "GLASS": dict(rough=0.02, trans=1.0),
}


def _simple_material(scene, kind, color, rough=0.5, metal=0.0, trans=0.0, glow=0.0):
    mat = _material(scene, kind)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        mat.node_tree.nodes.clear()
        out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        mat.node_tree.links.new(bsdf.outputs[0], out.inputs["Surface"])
    col = (*tuple(color), 1.0)
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Transmission Weight"].default_value = trans
    bsdf.inputs["Emission Color"].default_value = col
    bsdf.inputs["Emission Strength"].default_value = glow
    mat.diffuse_color = col
    return mat


def stage_material(scene):
    s = settings(scene)
    return _simple_material(scene, "Lumina Stage", s.stage_color, **STAGE_FINISH.get(s.stage_finish, {}))


def _smooth_sides(bm):
    for f in bm.faces:
        f.smooth = abs(f.normal.z) < 0.5


def build_stage(scene):
    utils.delete_roles(scene, STAGE)
    s = settings(scene)
    b = utils.stored_bounds(scene)
    if b is None or s.stage == "NONE":
        return
    lo, hi, center, dims, size = b
    h = stage_height(scene)
    r = max(dims.x, dims.y) * 0.5 * s.stage_scale
    bm = bmesh.new()
    kind = s.stage
    if kind == "CYLINDER":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=r, radius2=r, depth=h,
                              matrix=Matrix.Translation((0, 0, h / 2)))
    elif kind == "STEPS":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=r * 1.35, radius2=r * 1.35, depth=h * 0.5,
                              matrix=Matrix.Translation((0, 0, h * 0.25)))
        bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=r, radius2=r, depth=h * 0.5,
                              matrix=Matrix.Translation((0, 0, h * 0.75)))
    elif kind == "HEX":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r, depth=h,
                              matrix=Matrix.Translation((0, 0, h / 2)))
    elif kind == "SLAB":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=128, radius1=r * 1.6, radius2=r * 1.6, depth=h,
                              matrix=Matrix.Translation((0, 0, h / 2)))
    else:  # BLOCK
        side = r * 1.8
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, h / 2)) @ Matrix.Diagonal((side, side, h, 1)))
    bm.normal_update()
    _smooth_sides(bm)
    if kind in {"HEX", "BLOCK"}:
        for f in bm.faces:
            f.smooth = False
    me = bpy.data.meshes.new("Lumina Stage")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(stage_material(scene))
    obj = utils.new_object(scene, "Lumina Stage", me, STAGE, "BACKDROP")
    bev = obj.modifiers.new("Soft Edges", "BEVEL")
    bev.width = min(h, r) * 0.04
    bev.segments = 3
    bev.limit_method = "ANGLE"
    if hasattr(bev, "harden_normals"):
        bev.harden_normals = False
    _place(scene, obj)


# --------------------------------------------------------------------------
# Set dressing
# --------------------------------------------------------------------------

def decor_material(scene):
    s = settings(scene)
    return _simple_material(scene, "Lumina Decor", s.decor_color, rough=0.45, glow=s.decor_glow)


def _torus(bm, major, minor, matrix, seg=96, ring=16):
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        row = []
        for j in range(ring):
            b = 2 * math.pi * j / ring
            p = Vector(((major + minor * math.cos(b)) * math.cos(a),
                        (major + minor * math.cos(b)) * math.sin(a),
                        minor * math.sin(b)))
            row.append(bm.verts.new(matrix @ p))
        verts.append(row)
    for i in range(seg):
        for j in range(ring):
            f = bm.faces.new((verts[i][j], verts[(i + 1) % seg][j], verts[(i + 1) % seg][(j + 1) % ring], verts[i][(j + 1) % ring]))
            f.smooth = True


def _arch(bm, half_w, straight_h, depth, matrix, samples=48):
    outline = [Vector((half_w, 0.0))]
    for i in range(samples + 1):
        th = math.pi * i / samples
        outline.append(Vector((half_w * math.cos(th), straight_h + half_w * math.sin(th))))
    outline.append(Vector((-half_w, 0.0)))
    front = [bm.verts.new(matrix @ Vector((p.x, -depth / 2, p.y))) for p in outline]
    back = [bm.verts.new(matrix @ Vector((p.x, depth / 2, p.y))) for p in outline]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((front[i], back[i], back[j], front[j]))
        f.smooth = 0 < i < n - 2


def build_decor(scene):
    utils.delete_roles(scene, DECOR)
    s = settings(scene)
    b = utils.stored_bounds(scene)
    if b is None or s.decor == "NONE":
        return
    lo, hi, center, dims, size = b
    rng = random.Random(s.decor_seed)
    sc = s.decor_scale
    wall = s.wall_distance * size
    sh = stage_height(scene)
    tall = dims.z + sh
    foot = max(dims.x, dims.y) * 0.5 * max(1.0, s.stage_scale if s.stage != "NONE" else 1.0)
    depth_y = max(foot * 1.6, wall * 0.55)
    bm = bmesh.new()
    T = Matrix.Translation
    kind = s.decor

    if kind == "ARCH":
        half_w = max(0.5 * tall, 1.3 * foot) * sc
        _arch(bm, half_w, 0.75 * tall * sc, size * 0.12, T((0, depth_y, 0)))
    elif kind == "RINGS":
        zc = sh + dims.z * 0.55
        for i, r in enumerate((0.85, 1.15, 1.45)):
            tilt = Matrix.Rotation(math.radians(90 + rng.uniform(-8, 8)), 4, "X") @ Matrix.Rotation(math.radians(rng.uniform(-10, 10)), 4, "Y")
            _torus(bm, r * tall * 0.65 * sc, size * 0.025 * sc, T((0, depth_y + i * size * 0.15, zc)) @ tilt)
    elif kind == "ORBS":
        for _ in range(7):
            r = rng.uniform(0.12, 0.42) * size * sc
            side = rng.choice((-1, 1))
            x = side * rng.uniform(foot + r * 1.5, foot + 2.6 * size)
            y = rng.uniform(-0.2, 0.9) * depth_y
            z = r if rng.random() < 0.4 else rng.uniform(r, 2.4 * size)
            bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=r, matrix=T((x, y, z)))
    elif kind == "PILLARS":
        for i in range(5):
            side = -1 if i % 2 == 0 else 1
            r = rng.uniform(0.16, 0.32) * size * sc
            h = rng.uniform(0.7, 2.4) * tall * sc
            x = side * (foot + r + (i // 2) * 0.8 * size * sc + rng.uniform(0.2, 0.6) * size)
            y = rng.uniform(0.3, 1.0) * depth_y
            bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=r, radius2=r, depth=h, matrix=T((x, y, h / 2)))
    elif kind == "BLOCKS":
        for i in range(6):
            side = -1 if i % 2 == 0 else 1
            e = rng.uniform(0.3, 0.85) * size * sc
            x = side * (foot + e * 0.8 + (i // 2) * 0.7 * size + rng.uniform(0, 0.4) * size)
            y = rng.uniform(-0.1, 1.0) * depth_y
            rot = Matrix.Rotation(rng.uniform(0, math.pi / 2), 4, "Z")
            bmesh.ops.create_cube(bm, size=e, matrix=T((x, y, e / 2)) @ rot)
    elif kind == "PANELS":
        for i in range(4):
            side = -1 if i % 2 == 0 else 1
            w = rng.uniform(0.7, 1.3) * size * sc
            h = rng.uniform(1.6, 2.8) * tall * sc
            x = side * (foot + 0.6 * size + (i // 2) * 1.1 * size)
            y = depth_y * (0.6 + 0.4 * (i // 2))
            rot = Matrix.Rotation(math.radians(side * rng.uniform(20, 45)), 4, "Z")
            bmesh.ops.create_cube(bm, size=1.0, matrix=T((x, y, h / 2)) @ rot @ Matrix.Diagonal((w, size * 0.05, h, 1)))

    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if kind in {"ORBS", "PILLARS"}:
        for f in bm.faces:
            f.smooth = kind == "ORBS" or abs(f.normal.z) < 0.5
    me = bpy.data.meshes.new("Lumina Decor")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(decor_material(scene))
    obj = utils.new_object(scene, "Lumina Decor", me, DECOR, "BACKDROP")
    if kind in {"BLOCKS", "PANELS", "ARCH"}:
        bev = obj.modifiers.new("Soft Edges", "BEVEL")
        bev.width = size * 0.01
        bev.segments = 2
        bev.limit_method = "ANGLE"
    _place(scene, obj)
