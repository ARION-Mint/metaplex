# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared helpers: tagging, collections, bounds, colour, easing and baking."""

import math

import bpy
from mathutils import Euler, Matrix, Vector

ROLE = "lumina_role"          # custom property on every generated object
PRODUCT = "lumina_product"    # custom property on objects that form the product
ORIG_PARENT = "lumina_orig_parent"

ROOT_COLLECTION = "Lumina Studio"
SUB_COLLECTIONS = {
    "RIG": "Lumina Rig",
    "LIGHTS": "Lumina Lights",
    "BACKDROP": "Lumina Backdrop",
}

_BOUNDABLE = {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "POINTCLOUD", "VOLUME", "GREASEPENCIL", "GPENCIL"}


# --------------------------------------------------------------------------
# Settings access / batching of live updates
# --------------------------------------------------------------------------

class _UpdateGuard:
    depth = 0


def updates_suspended():
    return _UpdateGuard.depth > 0


class suspend_updates:
    """Context manager: property callbacks become no-ops while active."""

    def __enter__(self):
        _UpdateGuard.depth += 1

    def __exit__(self, *exc):
        _UpdateGuard.depth -= 1
        return False


def settings(scene):
    return scene.lumina


# --------------------------------------------------------------------------
# Collections and generated objects
# --------------------------------------------------------------------------

def _find_child(parent, name_prefix, scene_tag):
    for child in parent.children:
        if child.get("lumina_scene") == scene_tag and child.name.startswith(name_prefix):
            return child
    return None


def studio_collection(scene, sub=None, create=True):
    """Return the scene's Lumina collection (or one of its sub collections)."""
    tag = scene.name_full
    root = _find_child(scene.collection, ROOT_COLLECTION, tag)
    if root is None:
        if not create:
            return None
        root = bpy.data.collections.new(ROOT_COLLECTION)
        root["lumina_scene"] = tag
        scene.collection.children.link(root)
    if sub is None:
        return root
    name = SUB_COLLECTIONS[sub]
    coll = _find_child(root, name, tag)
    if coll is None:
        if not create:
            return None
        coll = bpy.data.collections.new(name)
        coll["lumina_scene"] = tag
        root.children.link(coll)
    return coll


def new_object(scene, name, data, role, sub):
    obj = bpy.data.objects.new(name, data)
    obj[ROLE] = role
    studio_collection(scene, sub).objects.link(obj)
    return obj


def new_empty(scene, name, role, sub="RIG", display="PLAIN_AXES", size=0.25, location=(0, 0, 0)):
    obj = new_object(scene, name, None, role, sub)
    obj.empty_display_type = display
    obj.empty_display_size = size
    obj.location = location
    return obj


def objects_with_role(scene, *roles):
    roles = set(roles)
    return [o for o in scene.objects if o.get(ROLE) in roles]


def first_with_role(scene, role):
    for o in scene.objects:
        if o.get(ROLE) == role:
            return o
    return None


def delete_object(obj):
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is None or data.users:
        return
    for kind, coll in ((bpy.types.Mesh, bpy.data.meshes), (bpy.types.Light, bpy.data.lights),
                       (bpy.types.Camera, bpy.data.cameras), (bpy.types.Curve, bpy.data.curves)):
        if isinstance(data, kind):
            coll.remove(data)
            return


def delete_roles(scene, *roles):
    for obj in objects_with_role(scene, *roles):
        delete_object(obj)


def purge_material(name):
    mat = bpy.data.materials.get(name)
    if mat is not None and mat.users == 0:
        bpy.data.materials.remove(mat)


def remove_studio_collections(scene):
    root = studio_collection(scene, create=False)
    if root is None:
        return
    for child in list(root.children):
        if not child.objects and not child.children:
            bpy.data.collections.remove(child)
    if not root.objects and not root.children:
        bpy.data.collections.remove(root)


# --------------------------------------------------------------------------
# Product
# --------------------------------------------------------------------------

def product_objects(scene):
    return [o for o in scene.objects if o.get(PRODUCT)]


def product_roots(objs):
    members = set(objs)
    return [o for o in objs if o.parent is None or o.parent not in members]


def world_points(objs, depsgraph=None):
    pts = []
    for obj in objs:
        if obj.type not in _BOUNDABLE:
            continue
        src = obj.evaluated_get(depsgraph) if depsgraph is not None else obj
        mw = src.matrix_world
        pts.extend(mw @ Vector(c) for c in src.bound_box)
    if not pts:
        pts = [o.matrix_world.translation.copy() for o in objs]
    return pts


def bounds(points):
    if not points:
        zero = Vector((0, 0, 0))
        return zero, zero, zero, Vector((1, 1, 1))
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi, (lo + hi) * 0.5, hi - lo


def stored_bounds(scene):
    """Rest bounds captured when the product was set (stable during animation)."""
    s = settings(scene)
    lo = Vector(s.bound_min)
    hi = Vector(s.bound_max)
    if (hi - lo).length < 1e-6:
        return None
    center = (lo + hi) * 0.5
    dims = hi - lo
    size = max(dims.x, dims.y, dims.z, 1e-3)
    return lo, hi, center, dims, size


def stored_corners(scene):
    b = stored_bounds(scene)
    if b is None:
        return []
    lo, hi = b[0], b[1]
    return [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]


# --------------------------------------------------------------------------
# Studio orientation
# --------------------------------------------------------------------------

def view_azimuth(scene):
    """Azimuth (radians) of the Lumina camera around the product.

    0 means the camera sits on -Y looking towards +Y (Blender's front view);
    positive values move the camera towards +X (image right side).
    """
    s = settings(scene)
    from . import data_camera  # local import to avoid a cycle
    shot = data_camera.SHOTS.get(s.shot, data_camera.SHOTS["HERO"])
    return math.radians(shot["az"] + s.orbit_offset)


def direction_from_angles(az, el):
    ce = math.cos(el)
    return Vector((math.sin(az) * ce, -math.cos(az) * ce, math.sin(el)))


def view_basis(az):
    """Horizontal studio basis for a camera azimuth: (right, away, up)."""
    right = Vector((math.cos(az), math.sin(az), 0.0))
    away = Vector((-math.sin(az), math.cos(az), 0.0))
    return right, away, Vector((0.0, 0.0, 1.0))


def look_rotation(src, dst, roll=0.0):
    quat = (dst - src).to_track_quat("-Z", "Y")
    if roll:
        quat = quat @ Euler((0.0, 0.0, roll)).to_quaternion()
    return quat.to_euler()


# --------------------------------------------------------------------------
# Colour
# --------------------------------------------------------------------------

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(hex_str):
    h = hex_str.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def kelvin_to_rgb(kelvin):
    """Approximate black-body colour (linear RGB, max channel = 1)."""
    t = max(1000.0, min(40000.0, kelvin)) / 100.0
    if t <= 66:
        r = 255.0
        g = 99.4708025861 * math.log(t) - 161.1195681661
        b = 0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
        b = 255.0
    rgb = [srgb_to_linear(max(0.0, min(255.0, v)) / 255.0) for v in (r, g, b)]
    peak = max(rgb) or 1.0
    return tuple(v / peak for v in rgb)


def mix_rgb(a, b, f):
    return tuple(x + (y - x) * f for x, y in zip(a, b))


# --------------------------------------------------------------------------
# Easing
# --------------------------------------------------------------------------

def clamp01(t):
    return 0.0 if t < 0.0 else 1.0 if t > 1.0 else t


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, a, b):
    """Remap t from [a, b] to [0, 1] (clamped)."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp01((t - a) / (b - a))


def smooth(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def smoother(t):
    t = clamp01(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def in_out_cubic(t):
    t = clamp01(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def in_out_sine(t):
    return -(math.cos(math.pi * clamp01(t)) - 1) / 2


def out_cubic(t):
    return 1 - (1 - clamp01(t)) ** 3


def out_quint(t):
    return 1 - (1 - clamp01(t)) ** 5


def in_cubic(t):
    return clamp01(t) ** 3


def in_quad(t):
    return clamp01(t) ** 2


def out_expo(t):
    t = clamp01(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def out_back(t, s=1.70158):
    t = clamp01(t) - 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


def out_elastic(t, period=0.3):
    t = clamp01(t)
    if t in (0.0, 1.0):
        return t
    return 2 ** (-10 * t) * math.sin((t - period / 4) * (2 * math.pi) / period) + 1


def out_bounce(t):
    t = clamp01(t)
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


def damped(t, freq=3.0, decay=5.0):
    """Damped oscillation starting at 1 and settling to 0."""
    t = clamp01(t)
    return math.exp(-decay * t) * math.cos(freq * 2 * math.pi * t)


# --------------------------------------------------------------------------
# Animation baking (works with legacy and layered/slotted actions)
# --------------------------------------------------------------------------

def object_fcurves(obj):
    ad = obj.animation_data
    if ad is None or ad.action is None:
        return []
    action = ad.action
    slot = getattr(ad, "action_slot", None)
    if slot is not None:
        try:
            from bpy_extras import anim_utils
            bag = anim_utils.action_get_channelbag_for_slot(action, slot)
            if bag is not None:
                return list(bag.fcurves)
        except (ImportError, AttributeError):
            pass
    fcurves = getattr(action, "fcurves", None)
    return list(fcurves) if fcurves is not None else []


def clear_animation(obj):
    ad = obj.animation_data
    if ad is None:
        return
    action = ad.action
    obj.animation_data_clear()
    if action is not None and action.users == 0:
        bpy.data.actions.remove(action)


def bake_samples(obj, frames, channels, interpolation="LINEAR", action_name=None):
    """Write sampled values as keyframes.

    channels: {(data_path, index): [value per frame]}
    """
    clear_animation(obj)
    if not frames:
        return
    obj.animation_data_create()
    action = bpy.data.actions.new(action_name or (obj.name + " Motion"))
    obj.animation_data.action = action
    if hasattr(obj.animation_data, "action_slot") and obj.animation_data.action_slot is None:
        slots = getattr(action, "slots", None)
        if slots is not None and len(slots):
            obj.animation_data.action_slot = slots[0]

    paths = {}
    for (path, index) in channels:
        paths.setdefault(path, []).append(index)
    for path, indices in paths.items():
        for index in indices:
            obj.keyframe_insert(data_path=path, index=index, frame=frames[0])

    lookup = {(fc.data_path, fc.array_index): fc for fc in object_fcurves(obj)}
    for key, values in channels.items():
        fc = lookup.get(key)
        if fc is None:
            continue
        kps = fc.keyframe_points
        kps.clear()
        kps.add(len(frames))
        co = []
        for f, v in zip(frames, values):
            co.extend((float(f), float(v)))
        kps.foreach_set("co", co)
        for kp in kps:
            kp.interpolation = interpolation
            kp.handle_left_type = "AUTO_CLAMPED"
            kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()


def euler_sequence(matrices, order="XYZ"):
    """Convert rotation matrices to continuous Euler angles (no 360° flips)."""
    out = []
    prev = None
    for m in matrices:
        e = m.to_euler(order, prev) if prev is not None else m.to_euler(order)
        out.append(e)
        prev = e
    return out


def rotation_matrix(rx, ry, rz):
    return (Matrix.Rotation(rz, 3, "Z") @ Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X"))


# --------------------------------------------------------------------------
# Version helpers
# --------------------------------------------------------------------------

def enum_ids(struct, prop):
    try:
        return {i.identifier for i in struct.bl_rna.properties[prop].enum_items}
    except (KeyError, AttributeError):
        return set()


def eevee_engine_id():
    ids = enum_ids(bpy.types.RenderSettings, "engine")
    if "BLENDER_EEVEE_NEXT" in ids:
        return "BLENDER_EEVEE_NEXT"
    return "BLENDER_EEVEE"


def try_set(obj, attr, value):
    try:
        setattr(obj, attr, value)
        return True
    except (AttributeError, TypeError, ValueError):
        return False
