# SPDX-License-Identifier: GPL-3.0-or-later
"""Camera rig: pivot (orbit/tilt) -> camera (dolly/truck/pedestal/roll).

The pivot sits at the aim point. The camera is parented to it on the pivot's
-Y axis looking down +Y, so orbiting and tilting is a single rotation and
dolly / truck / pedestal are plain local translations. Framing is solved
exactly against the product's bounding box (perspective or orthographic),
including lens shift used for copy-space composition.
"""

import math

import bpy
from mathutils import Matrix, Vector

from . import utils
from .data_camera import SHOTS
from .utils import settings

CAMERA = "CAMERA"
PIVOT = "CAM_PIVOT"
FOCUS = "FOCUS"

SENSOR = 36.0


def get_camera(scene):
    return utils.first_with_role(scene, CAMERA)


def get_pivot(scene):
    return utils.first_with_role(scene, PIVOT)


def exists(scene):
    return get_camera(scene) is not None


def shot_angles(scene):
    s = settings(scene)
    shot = SHOTS.get(s.shot, SHOTS["HERO"])
    az = math.radians(shot["az"] + s.orbit_offset)
    el = math.radians(max(-80.0, min(89.5, shot["el"] + s.height_offset)))
    lens = s.lens if s.lens_override else shot["lens"]
    roll = math.radians(shot["roll"] + s.roll)
    return az, el, lens, roll


def aim_point(scene):
    b = utils.stored_bounds(scene)
    lo, hi, center, dims, size = b
    s = settings(scene)
    return center + Vector((0.0, 0.0, s.aim_height * dims.z * 0.5))


def _frustum(scene, lens):
    r = scene.render
    w = r.resolution_x * r.pixel_aspect_x
    h = r.resolution_y * r.pixel_aspect_y
    big = max(w, h)
    half = (SENSOR * 0.5) / lens
    return half, half * w / big, half * h / big


def _local_points(scene, aim, az, el):
    rot = utils.rotation_matrix(-el, 0.0, az)
    inv = rot.transposed()
    return [inv @ (p - aim) for p in utils.stored_corners(scene)]


def _screen(p, roll):
    # local pivot frame: x = right, y = forward (away from camera), z = up
    c, s_ = math.cos(roll), math.sin(roll)
    u = p.x * c - p.z * s_
    v = p.x * s_ + p.z * c
    return u, v


def solve_distance(scene, pts, lens, roll, fill, pos_x, pos_y):
    """Smallest camera distance that keeps every point inside the fill box."""
    half, hx, hy = _frustum(scene, lens)
    cx = -pos_x * 0.5 * hx
    cy = -pos_y * 0.5 * hy
    ax, ay = hx * fill, hy * fill
    proj = [(_screen(p, roll), p.y) for p in pts]

    def fits(d):
        for (u, v), y in proj:
            depth = y + d
            if depth <= 1e-6:
                return False
            if abs(u / depth - cx) > ax or abs(v / depth - cy) > ay:
                return False
        return True

    size = max((p.length for p in pts), default=1.0) or 1.0
    lo = max(-y for _uv, y in proj) + size * 0.01
    hi = lo + size * 4.0
    steps = 0
    while not fits(hi) and steps < 40:
        hi *= 2.0
        steps += 1
    if not fits(hi):
        return hi, (cx, cy, half)
    if fits(lo):
        return lo, (cx, cy, half)
    for _ in range(60):
        mid = (lo + hi) * 0.5
        if fits(mid):
            hi = mid
        else:
            lo = mid
    return hi, (cx, cy, half)


def solve_ortho(scene, pts, roll, fill, pos_x, pos_y):
    r = scene.render
    w = r.resolution_x * r.pixel_aspect_x
    h = r.resolution_y * r.pixel_aspect_y
    big = max(w, h)
    fx, fy = w / big, h / big
    uv = [_screen(p, roll) for p in pts]

    def fits(scale):
        hx, hy = scale * fx * 0.5, scale * fy * 0.5
        cx, cy = -pos_x * 0.5 * hx, -pos_y * 0.5 * hy
        return all(abs(u - cx) <= hx * fill and abs(v - cy) <= hy * fill for u, v in uv)

    lo, hi = 1e-4, max((abs(c) for u, v in uv for c in (u, v)), default=1.0) * 8 + 1e-3
    while not fits(hi):
        hi *= 2.0
    for _ in range(60):
        mid = (lo + hi) * 0.5
        if fits(mid):
            hi = mid
        else:
            lo = mid
    return hi


def _ensure_rig(scene):
    b = utils.stored_bounds(scene)
    size = b[4]
    pivot = get_pivot(scene)
    if pivot is None:
        pivot = utils.new_empty(scene, "Lumina Camera Pivot", PIVOT, display="SPHERE", size=size * 0.08)
        pivot.rotation_mode = "XYZ"
    cam = get_camera(scene)
    if cam is None:
        data = bpy.data.cameras.new("Lumina Camera")
        cam = utils.new_object(scene, "Lumina Camera", data, CAMERA, "RIG")
    if cam.parent is not pivot:
        cam.parent = pivot
        cam.matrix_parent_inverse = Matrix.Identity(4)
    focus = utils.first_with_role(scene, FOCUS)
    if focus is None:
        focus = utils.new_empty(scene, "Lumina Focus", FOCUS, display="CIRCLE", size=size * 0.25,
                                location=aim_point(scene))
        focus.empty_display_type = "SPHERE"
    return pivot, cam, focus


def build(scene):
    if utils.stored_bounds(scene) is None:
        return None
    s = settings(scene)
    if s.prev_camera is None and scene.camera is not None and scene.camera.get(utils.ROLE) is None:
        s.prev_camera = scene.camera
    pivot, cam, focus = _ensure_rig(scene)
    scene.camera = cam
    frame(scene)
    return cam


def frame(scene):
    """Apply the shot and solve framing. Re-bakes an active camera move."""
    cam = get_camera(scene)
    pivot = get_pivot(scene)
    if cam is None or pivot is None or utils.stored_bounds(scene) is None:
        return
    s = settings(scene)
    lo, hi, center, dims, size = utils.stored_bounds(scene)
    az, el, lens, roll = shot_angles(scene)
    aim = aim_point(scene)
    fill = max(0.05, s.fill / 100.0)
    floor_z = floor_height(scene)

    for _attempt in range(3):
        pts = _local_points(scene, aim, az, el)
        if s.ortho:
            ortho_scale = solve_ortho(scene, pts, roll, fill, s.pos_x, s.pos_y)
            dist = max(-p.y for p in pts) + size * 2.0
        else:
            dist, _ = solve_distance(scene, pts, lens, roll, fill, s.pos_x, s.pos_y)
        cam_z = aim.z + dist * math.sin(el)
        min_z = floor_z + size * 0.03
        if cam_z >= min_z or s.ortho or el > math.radians(85):
            break
        # keep the camera above the floor
        el = math.asin(max(-1.0, min(1.0, (min_z - aim.z) / dist)))

    pivot.location = aim
    pivot.rotation_euler = (-el, 0.0, az)
    pivot.scale = (1, 1, 1)
    cam.location = (0.0, -dist, 0.0)
    cam.rotation_euler = (math.pi / 2, roll, 0.0)
    cam.scale = (1, 1, 1)

    data = cam.data
    data.sensor_fit = "AUTO"
    data.sensor_width = SENSOR
    if s.ortho:
        data.type = "ORTHO"
        data.ortho_scale = ortho_scale
        r = scene.render
        big = max(r.resolution_x, r.resolution_y)
        hx = 0.5 * r.resolution_x / big
        hy = 0.5 * r.resolution_y / big
        data.shift_x = -s.pos_x * 0.5 * hx
        data.shift_y = -s.pos_y * 0.5 * hy
    else:
        data.type = "PERSP"
        data.lens = lens
        half, hx, hy = _frustum(scene, lens)
        # cx = 2 * half * shift  ->  shift = cx / (2 * half)
        data.shift_x = -(s.pos_x * 0.5 * hx) / (2 * half)
        data.shift_y = -(s.pos_y * 0.5 * hy) / (2 * half)
    data.clip_start = max(1e-5, min(size * 0.01, dist * 0.02))
    data.clip_end = max(size * 400.0, dist * 50.0)
    data.show_composition_thirds = s.show_thirds
    data.passepartout_alpha = 0.85

    apply_dof(scene)

    s.cam_distance = dist
    s.cam_lens = lens if not s.ortho else data.lens
    s.cam_el = el
    s.cam_az = az
    s.cam_roll = roll

    from . import motion
    motion.refresh_camera_move(scene)


def apply_dof(scene):
    cam = get_camera(scene)
    if cam is None:
        return
    s = settings(scene)
    dof = cam.data.dof
    dof.use_dof = s.dof
    dof.aperture_fstop = s.fstop
    focus = utils.first_with_role(scene, FOCUS)
    dof.focus_object = focus
    if focus is not None and utils.stored_bounds(scene) is not None:
        focus.empty_display_size = utils.stored_bounds(scene)[4] * 0.12


def reset_focus(scene):
    focus = utils.first_with_role(scene, FOCUS)
    if focus is not None and utils.stored_bounds(scene) is not None:
        focus.location = aim_point(scene)


def floor_height(scene):
    b = utils.stored_bounds(scene)
    if b is None:
        return 0.0
    from . import backdrop
    return b[0].z - backdrop.stage_height(scene)


def remove(scene):
    s = settings(scene)
    from . import motion
    motion.remove_camera_move(scene)
    utils.delete_roles(scene, CAMERA, PIVOT, FOCUS)
    if s.prev_camera is not None and s.prev_camera.name in scene.objects:
        scene.camera = s.prev_camera
    s.prev_camera = None
