# SPDX-License-Identifier: GPL-3.0-or-later
"""Non-destructive product motion and camera moves.

Product motion is baked onto a "Motion Rig" empty. The product's root
objects are parented to it, so the product's own transforms and animation
are never touched; removing the motion restores the original parenting
exactly.
"""

import math

import bpy
from mathutils import Matrix, Vector

from . import data_camera, data_motion, utils
from .utils import settings

RIG = "MOTION_RIG"
ORIG_BASIS = "lumina_orig_basis"
ORIG_PINV = "lumina_orig_pinv"


def _flat(m):
    return [m[i][j] for i in range(4) for j in range(4)]


def _unflat(values):
    return Matrix([values[i * 4:(i + 1) * 4] for i in range(4)])


def motion_rig(scene):
    return utils.first_with_role(scene, RIG)


def is_active(scene):
    return motion_rig(scene) is not None


def frame_range(scene):
    s = settings(scene)
    start = s.start_frame
    return start, start + max(2, s.duration)


# --------------------------------------------------------------------------
# Attach / detach
# --------------------------------------------------------------------------

def _attach(scene, rig, rest):
    objs = utils.product_objects(scene)
    for obj in utils.product_roots(objs):
        # Compute from the basis: matrix_world may still hold a stale animated pose
        if obj.parent is not None:
            world = obj.parent.matrix_world @ obj.matrix_parent_inverse @ obj.matrix_basis
        else:
            world = obj.matrix_basis.copy()
        obj[utils.ORIG_PARENT] = obj.parent.name if obj.parent else ""
        obj[ORIG_BASIS] = _flat(obj.matrix_basis)
        obj[ORIG_PINV] = _flat(obj.matrix_parent_inverse)
        obj.parent = rig
        obj.matrix_parent_inverse = rest.inverted()
        obj.matrix_basis = world


def _detach(scene):
    for obj in utils.product_objects(scene):
        if utils.ORIG_PARENT not in obj:
            continue
        name = obj[utils.ORIG_PARENT]
        obj.parent = bpy.data.objects.get(name) if name else None
        obj.matrix_parent_inverse = _unflat(list(obj[ORIG_PINV]))
        obj.matrix_basis = _unflat(list(obj[ORIG_BASIS]))
        for key in (utils.ORIG_PARENT, ORIG_BASIS, ORIG_PINV):
            del obj[key]


# --------------------------------------------------------------------------
# Product motion
# --------------------------------------------------------------------------

def params(scene):
    s = settings(scene)
    return data_motion.Params(k=s.strength, turns=s.turns, direction=1.0 if s.direction == "LEFT" else -1.0,
                              cycles=s.cycles, overshoot=s.overshoot)


def sample_pose(scene, t):
    s = settings(scene)
    if s.reverse:
        t = 1.0 - t
    return data_motion.evaluate(s.motion, t, params(scene))


def apply(scene):
    """(Re)build the product motion from the current settings."""
    remove(scene, keep_timeline=True)
    b = utils.stored_bounds(scene)
    if b is None or not utils.product_objects(scene):
        return False
    s = settings(scene)
    lo, hi, center, dims, size = b
    entry = data_motion.MOTIONS.get(s.motion)
    if entry is None:
        return False
    pivot = Vector((center.x, center.y, lo.z)) if entry[3] == "BASE" else center.copy()
    rest = Matrix.Translation(pivot)
    rig = utils.new_empty(scene, "Lumina Motion Rig", RIG, display="ARROWS", size=size * 0.6, location=pivot)
    rig.rotation_mode = "XYZ"
    _attach(scene, rig, rest)

    bake_product(scene, rig, pivot, size)
    if s.fit_timeline:
        fit_timeline(scene)
    return True


def bake_product(scene, rig, pivot, size):
    start, end = frame_range(scene)
    from . import camera
    az = camera.shot_angles(scene)[0]
    right, away, up = utils.view_basis(az)
    basis = Matrix((right, away, up)).transposed()  # columns = view axes in world
    basis_inv = basis.transposed()

    frames = list(range(start, end + 1))
    span = float(end - start)
    rots = []
    locs = []
    scales = []
    for f in frames:
        pose = sample_pose(scene, (f - start) / span)
        offset = basis @ Vector((pose["x"], pose["y"], pose["z"])) * size
        locs.append(pivot + offset)
        r_view = utils.rotation_matrix(math.radians(pose["rx"]), math.radians(pose["ry"]), math.radians(pose["rz"]))
        rots.append(basis @ r_view @ basis_inv)
        scales.append((pose["sx"], pose["sy"], pose["sz"]))
    eulers = utils.euler_sequence(rots)

    channels = {}
    for i in range(3):
        channels[("location", i)] = [l[i] for l in locs]
        channels[("rotation_euler", i)] = [e[i] for e in eulers]
        channels[("scale", i)] = [sc[i] for sc in scales]
    utils.bake_samples(rig, frames, channels, action_name="Lumina Product Motion")


def refresh(scene):
    if is_active(scene):
        apply(scene)


def remove(scene, keep_timeline=False):
    rig = motion_rig(scene)
    if rig is None:
        return
    utils.clear_animation(rig)
    _detach(scene)
    utils.delete_object(rig)


def fit_timeline(scene):
    s = settings(scene)
    start, end = frame_range(scene)
    entry = data_motion.MOTIONS.get(s.motion)
    loop = bool(entry and entry[4])
    scene.frame_start = start
    # For loops the last baked frame equals the first: stop one frame early
    scene.frame_end = end - 1 if loop else end


# --------------------------------------------------------------------------
# Camera moves
# --------------------------------------------------------------------------

def camera_move_active(scene):
    s = settings(scene)
    return s.camera_move != "NONE" or s.handheld


def refresh_camera_move(scene):
    from . import camera
    cam = camera.get_camera(scene)
    pivot = camera.get_pivot(scene)
    if cam is None or pivot is None:
        return
    utils.clear_animation(pivot)
    utils.clear_animation(cam)
    utils.clear_animation(cam.data)
    if not camera_move_active(scene):
        return
    s = settings(scene)
    start, end = frame_range(scene)
    frames = list(range(start, end + 1))
    span = float(end - start)
    size = utils.stored_bounds(scene)[4]
    d0, lens0, el0, az0, roll0 = s.cam_distance, s.cam_lens, s.cam_el, s.cam_az, s.cam_roll

    piv = {("rotation_euler", 0): [], ("rotation_euler", 2): []}
    cam_ch = {("location", 0): [], ("location", 1): [], ("location", 2): [], ("rotation_euler", 1): []}
    lens_ch = {("lens", 0): []}
    for f in frames:
        m = data_camera.evaluate_move(s.camera_move, (f - start) / span, s.camera_intensity)
        el = max(math.radians(-80), min(math.radians(89.5), el0 + math.radians(m["tilt"])))
        az = az0 + math.radians(m["orbit"])
        piv[("rotation_euler", 0)].append(-el)
        piv[("rotation_euler", 2)].append(az)
        d = d0 * max(0.05, 1.0 + m["dolly"])
        cam_ch[("location", 0)].append(m["truck"] * size)
        cam_ch[("location", 1)].append(-d)
        cam_ch[("location", 2)].append(m["pedestal"] * size)
        cam_ch[("rotation_euler", 1)].append(roll0 + math.radians(m["roll"]))
        lens = lens0 * m["zoom"]
        if m["vertigo"]:
            lens = lens0 * (d / d0)
        lens_ch[("lens", 0)].append(max(1.0, lens))

    utils.bake_samples(pivot, frames, piv, action_name="Lumina Camera Orbit")
    utils.bake_samples(cam, frames, cam_ch, action_name="Lumina Camera Move")
    if cam.data.type == "PERSP" and any(abs(v - lens0) > 1e-4 for v in lens_ch[("lens", 0)]):
        # 'lens' is not an array property: key it without an index
        _bake_scalar(cam.data, "lens", frames, lens_ch[("lens", 0)])

    if s.handheld:
        _add_handheld(pivot, s.handheld_amount)


def _bake_scalar(id_data, path, frames, values):
    utils.clear_animation(id_data)
    id_data.keyframe_insert(data_path=path, frame=frames[0])
    for fc in utils.object_fcurves(id_data):
        if fc.data_path == path:
            kps = fc.keyframe_points
            kps.clear()
            kps.add(len(frames))
            co = []
            for f, v in zip(frames, values):
                co.extend((float(f), float(v)))
            kps.foreach_set("co", co)
            for kp in kps:
                kp.interpolation = "LINEAR"
            fc.update()


def _add_handheld(pivot, amount):
    for fc in utils.object_fcurves(pivot):
        if fc.data_path == "rotation_euler" and fc.array_index in (0, 2):
            mod = fc.modifiers.new("NOISE")
            mod.strength = math.radians(0.6) * amount * 2.0
            mod.scale = 22.0 if fc.array_index == 0 else 30.0
            mod.phase = 3.7 * (fc.array_index + 1)
            mod.blend_in = 0.0


def remove_camera_move(scene):
    from . import camera
    for obj in (camera.get_camera(scene), camera.get_pivot(scene)):
        if obj is not None:
            utils.clear_animation(obj)
            if obj.type == "CAMERA":
                utils.clear_animation(obj.data)


# --------------------------------------------------------------------------
# 360 spin set (e-commerce viewers)
# --------------------------------------------------------------------------

def bake_spin(scene, count):
    """Temporarily replace the product motion with an N-frame 360 spin."""
    remove(scene, keep_timeline=True)
    b = utils.stored_bounds(scene)
    lo, hi, center, dims, size = b
    rig = utils.new_empty(scene, "Lumina Motion Rig", RIG, display="ARROWS", size=size * 0.6, location=center)
    _attach(scene, rig, Matrix.Translation(center))
    frames = list(range(1, count + 1))
    channels = {("location", i): [center[i]] * count for i in range(3)}
    channels[("rotation_euler", 0)] = [0.0] * count
    channels[("rotation_euler", 1)] = [0.0] * count
    channels[("rotation_euler", 2)] = [2 * math.pi * (f - 1) / count for f in frames]
    utils.bake_samples(rig, frames, channels, action_name="Lumina Spin Set")
    return frames
