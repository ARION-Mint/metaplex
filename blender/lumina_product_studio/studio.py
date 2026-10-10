# SPDX-License-Identifier: GPL-3.0-or-later
"""High-level orchestration: build / remove everything, styles, user presets."""

import json
import os

import bpy

from . import backdrop, camera, grade, lighting, motion, output, product, utils
from .data_looks import STYLES
from .utils import settings


def has_product(scene):
    return utils.stored_bounds(scene) is not None and bool(utils.product_objects(scene))


def build_all(scene, reset_ramp=False):
    if not has_product(scene):
        return False
    s = settings(scene)
    output.apply_format(scene)
    camera.build(scene)
    backdrop.build(scene, reset_ramp=reset_ramp)
    lighting.build(scene)
    grade.apply(scene)
    if motion.is_active(scene):
        motion.refresh(scene)
    s.studio_built = True
    return True


def refresh_orientation(scene):
    """Shot or orbit changed: everything that is camera-relative follows."""
    if camera.exists(scene):
        camera.frame(scene)
    backdrop.update_orientation(scene)
    lighting.update_orientation(scene)
    if settings(scene).world_mode == "HDRI" and lighting.exists(scene):
        lighting.apply_world(scene)
    if motion.is_active(scene):
        motion.refresh(scene)


def remove_all(scene):
    s = settings(scene)
    motion.remove(scene)
    camera.remove(scene)
    lighting.remove(scene)
    backdrop.remove(scene, restore_film=True)
    grade.remove_compositor(scene)
    product.clear_product(scene)
    utils.remove_studio_collections(scene)
    for mat in list(bpy.data.materials):
        if mat.get("lumina_scene") == scene.name_full and mat.users == 0:
            bpy.data.materials.remove(mat)
    s.studio_built = False


# --------------------------------------------------------------------------
# Built-in styles
# --------------------------------------------------------------------------

STYLE_DEFAULTS = dict(stage_color="#f2f2f2", stage_finish="MATTE", decor_color="#d0d0d0", decor_glow=0.0,
                      accent_a="#38c6ff", accent_b="#ff3d9a", hdri="studio.exr", span=8.0, ramp_pos=None,
                      gradient_angle=0.0)


def apply_style(scene, key):
    style = STYLES.get(key)
    if style is None:
        return False
    st = dict(STYLE_DEFAULTS)
    st.update(style)
    s = settings(scene)
    with utils.suspend_updates():
        s.rig = st["rig"]
        s.backdrop = st["backdrop"]
        s.gradient = st["gradient"]
        s.gradient_angle = st["gradient_angle"]
        s.gradient_span = st["span"] if st.get("ramp_pos") is None else 4.0 + 10.0 * st["ramp_pos"]
        s.gradient_offset = 0.0
        s.color_a = utils.hex_to_linear(st["color_a"])
        s.color_b = utils.hex_to_linear(st["color_b"])
        s.glow = st["glow"]
        s.floor_finish = st["floor_finish"]
        s.floor_roughness = backdrop.FINISH_ROUGHNESS[st["floor_finish"]]
        s.stage = st["stage"]
        s.stage_color = utils.hex_to_linear(st["stage_color"])
        s.stage_finish = st["stage_finish"]
        s.decor = st["decor"]
        s.decor_color = utils.hex_to_linear(st["decor_color"])
        s.decor_glow = st["decor_glow"]
        s.bg_light = st["bg_light"]
        s.accent_a = utils.hex_to_linear(st["accent_a"])
        s.accent_b = utils.hex_to_linear(st["accent_b"])
        s.world_mode = st["world_mode"]
        if st["world_mode"] == "HDRI":
            try:
                s.hdri = st["hdri"]
            except TypeError:
                pass
        s.grade = st["grade"]
        grade.load_preset(scene, st["grade"])
    if has_product(scene):
        build_all(scene, reset_ramp=True)
    return True


# --------------------------------------------------------------------------
# User styles (JSON on disk)
# --------------------------------------------------------------------------

USER_FIELDS = [
    # lighting
    "use_lights", "rig", "light_power", "softness", "contrast", "rim", "warmth", "light_distance", "rig_rotation",
    "accent_a", "accent_b", "bg_light", "bg_light_power", "bg_light_color", "bg_light_height",
    "world_mode", "world_color", "world_strength", "hdri", "hdri_rotation", "hdri_visible",
    # backdrop
    "backdrop", "gradient", "color_a", "color_b", "gradient_angle", "gradient_span", "gradient_offset", "glow",
    "floor_finish", "floor_roughness", "matte_wall", "wall_distance", "curve_radius", "studio_scale",
    "stage", "stage_scale", "stage_height", "stage_color", "stage_finish",
    "decor", "decor_color", "decor_glow", "decor_scale", "decor_seed",
    # camera
    "shot", "orbit_offset", "height_offset", "roll", "lens_override", "lens", "fill", "pos_x", "pos_y",
    "aim_height", "ortho", "dof", "fstop",
    # grade
    "grade", "view_transform", "look", "exposure", "gamma", "wb_temperature", "wb_tint", "use_fx",
    "bloom", "bloom_size", "vignette", "aberration", "saturation", "contrast_fx",
]


def styles_dir():
    path = None
    pkg = __package__
    if hasattr(bpy.utils, "extension_path_user"):
        try:
            path = bpy.utils.extension_path_user(pkg, path="styles", create=True)
        except (ValueError, RuntimeError, KeyError):
            path = None
    if not path:
        path = bpy.utils.user_resource("CONFIG", path=os.path.join("lumina_product_studio", "styles"), create=True)
    os.makedirs(path, exist_ok=True)
    return path


def list_user_styles():
    try:
        folder = styles_dir()
    except OSError:
        return []
    return sorted(os.path.splitext(f)[0] for f in os.listdir(folder) if f.endswith(".json"))


def _value(v):
    if hasattr(v, "__len__") and not isinstance(v, str):
        return list(v)
    return v


def save_user_style(scene, name):
    s = settings(scene)
    data = {"lumina_style": 1, "name": name}
    for field in USER_FIELDS:
        if hasattr(s, field):
            data[field] = _value(getattr(s, field))
    ramp = None
    for mat in bpy.data.materials:
        if mat.get("lumina_scene") == scene.name_full and mat.get("lumina_kind") == backdrop.MAT_PREFIX:
            ramp = backdrop._capture_ramp(mat)
    if ramp is not None:
        data["ramp"] = ramp
    fname = output.safe_name(name) + ".json"
    with open(os.path.join(styles_dir(), fname), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return fname


def load_user_style(scene, name):
    path = os.path.join(styles_dir(), name + ".json")
    if not os.path.isfile(path):
        return False
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    s = settings(scene)
    with utils.suspend_updates():
        for field in USER_FIELDS:
            if field in data and hasattr(s, field):
                try:
                    setattr(s, field, data[field])
                except (TypeError, ValueError):
                    pass
    if has_product(scene):
        build_all(scene, reset_ramp=True)
        if "ramp" in data:
            for mat in bpy.data.materials:
                if mat.get("lumina_scene") == scene.name_full and mat.get("lumina_kind") == backdrop.MAT_PREFIX:
                    node = mat.node_tree.nodes.get("Lumina Ramp")
                    if node is not None:
                        backdrop._restore_ramp(node, data["ramp"])
    return True


def delete_user_style(name):
    path = os.path.join(styles_dir(), name + ".json")
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False
