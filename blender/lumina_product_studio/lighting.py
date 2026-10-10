# SPDX-License-Identifier: GPL-3.0-or-later
"""Lighting rigs, backdrop accent lights and the studio world."""

import math
import os

import bpy
from mathutils import Vector

from . import product, utils
from .data_lighting import BACKDROP_LIGHTS, RIGS
from .utils import settings

RIG = "LIGHT_RIG"
LIGHT = "LIGHT"
BG_LIGHT = "BG_LIGHT"
WORLD_NAME = "Lumina World"

# Power calibration: an area key with p=1 at distance d (metres) gets
# BASE_POWER * d^2 watts, which keeps exposure independent of product scale.
BASE_POWER = 40.0
SPOT_FACTOR = 3.0


def rig_object(scene):
    return utils.first_with_role(scene, RIG)


def rig_lights(scene):
    return utils.objects_with_role(scene, LIGHT)


def exists(scene):
    return rig_object(scene) is not None


def _accent(s, key):
    if key == "A":
        return tuple(s.accent_a)
    if key == "B":
        return tuple(s.accent_b)
    return utils.hex_to_linear(key)


def light_color(s, spec):
    if spec.get("c"):
        return _accent(s, spec["c"])
    kelvin = spec.get("k", 6500) - s.warmth * 1800.0
    return utils.kelvin_to_rgb(kelvin)


def _role_mult(s, role):
    if role in {"fill", "bounce"}:
        return 2.0 * (1.0 - s.contrast)
    if role in {"rim", "kick"}:
        return s.rim
    return 1.0


def rig_orientation(scene):
    s = settings(scene)
    from . import camera
    az = camera.shot_angles(scene)[0]
    return az + math.radians(s.rig_rotation)


def update_orientation(scene):
    rig = rig_object(scene)
    if rig is not None:
        rig.rotation_euler = (0.0, 0.0, rig_orientation(scene))
    if utils.objects_with_role(scene, BG_LIGHT):
        build_backdrop_lights(scene)


def build(scene):
    remove(scene, keep_world=True)
    b = utils.stored_bounds(scene)
    if b is None:
        return
    s = settings(scene)
    lo, hi, center, dims, size = b
    rig_def = RIGS.get(s.rig, RIGS["THREE_POINT"])

    rig = utils.new_empty(scene, "Lumina Light Rig", RIG, sub="LIGHTS", display="CIRCLE", size=size * 0.9,
                          location=center)
    rig.rotation_euler = (0.0, 0.0, rig_orientation(scene))
    rig.hide_render = True

    receivers = product.sync_link_collection(scene) if s.product_only_lights else None

    if s.use_lights:
        for spec in rig_def["lights"]:
            _create_light(scene, rig, spec, size, receivers)

    apply_world(scene)
    build_backdrop_lights(scene)


def _create_light(scene, rig, spec, size, receivers):
    s = settings(scene)
    kind = spec.get("type", "AREA")
    dist = spec["d"] * size * s.light_distance
    direction = utils.direction_from_angles(math.radians(spec["az"]), math.radians(spec["el"]))
    local = direction * dist

    data = bpy.data.lights.new("Lumina " + spec["n"], kind)
    power = BASE_POWER * spec["p"] * s.light_power * _role_mult(s, spec["role"]) * dist * dist
    if kind == "AREA":
        data.shape = spec.get("shape", "RECTANGLE")
        data.size = max(1e-4, spec["w"] * size * s.softness)
        if data.shape in {"RECTANGLE", "ELLIPSE"}:
            data.size_y = max(1e-4, spec["h"] * size * s.softness)
        if spec.get("spread") is not None:
            data.spread = math.radians(spec["spread"])
    elif kind == "SPOT":
        data.spot_size = math.radians(spec.get("cone", 40))
        data.spot_blend = spec.get("blend", 0.4)
        data.shadow_soft_size = size * 0.01 * s.softness
        power *= SPOT_FACTOR
    else:
        data.shadow_soft_size = size * 0.05 * s.softness
        power *= SPOT_FACTOR
    data.energy = power
    data.color = light_color(s, spec)
    data["lumina_role"] = spec["role"]

    obj = utils.new_object(scene, "Lumina " + spec["n"], data, LIGHT, "LIGHTS")
    obj.parent = rig
    obj.location = local
    obj.rotation_euler = utils.look_rotation(local, Vector((0, 0, 0)))
    if receivers is not None and hasattr(obj, "light_linking"):
        obj.light_linking.receiver_collection = receivers
    return obj


def refresh_values(scene):
    """Cheap live update when only power/colour/softness changed."""
    build(scene)


# --------------------------------------------------------------------------
# Backdrop accent lights
# --------------------------------------------------------------------------

def build_backdrop_lights(scene):
    utils.delete_roles(scene, BG_LIGHT)
    s = settings(scene)
    b = utils.stored_bounds(scene)
    if b is None or s.bg_light == "OFF" or s.backdrop in {"NONE", "CATCHER"}:
        return
    lo, hi, center, dims, size = b
    from . import backdrop
    geo = backdrop.wall_frame(scene)
    if geo is None:
        return
    origin, right, away, wall_dist, floor_z = geo
    receivers = utils.studio_collection(scene, "BACKDROP")
    for i, spec in enumerate(BACKDROP_LIGHTS[s.bg_light][2]):
        target = origin + away * wall_dist + right * spec["x"] * size
        target.z = center.z + (spec["z"] + s.bg_light_height) * size
        pos = target - away * (size * 1.6)
        if spec["kind"] == "AREA":
            data = bpy.data.lights.new("Lumina Backdrop Light", "AREA")
            data.shape = "DISK"
            data.size = spec["w"] * size
            power = BASE_POWER * 0.6 * spec["p"] * s.bg_light_power * (1.6 * size) ** 2
        else:
            data = bpy.data.lights.new("Lumina Backdrop Spot", "SPOT")
            data.spot_size = math.radians(spec.get("cone", 25))
            data.spot_blend = spec.get("blend", 0.3)
            data.shadow_soft_size = size * 0.02
            pos = target - away * (size * 4.0) + Vector((0, 0, size * 1.5))
            power = BASE_POWER * 1.5 * spec["p"] * s.bg_light_power * (pos - target).length_squared
        data.energy = power
        data.color = _accent(s, spec["c"]) if spec.get("c") else tuple(s.bg_light_color)
        obj = utils.new_object(scene, data.name, data, BG_LIGHT, "LIGHTS")
        obj.location = pos
        obj.rotation_euler = utils.look_rotation(pos, target)
        if hasattr(obj, "light_linking"):
            obj.light_linking.receiver_collection = receivers
        if hasattr(obj, "visible_glossy"):
            obj.visible_glossy = False


# --------------------------------------------------------------------------
# World
# --------------------------------------------------------------------------

def hdri_folder():
    return bpy.utils.system_resource("DATAFILES", path=os.path.join("studiolights", "world"))


_HDRI_CACHE = []


def hdri_items(_self, _context):
    folder = hdri_folder() or ""
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith((".exr", ".hdr"))) if os.path.isdir(folder) else []
    items = [(f, os.path.splitext(f)[0].replace("_", " ").title(), "Built-in Blender HDRI", i) for i, f in enumerate(files)]
    if not items:
        items = [("NONE", "No HDRIs found", "", 0)]
    _HDRI_CACHE[:] = items
    return _HDRI_CACHE


def _world_rgb_strength(scene):
    s = settings(scene)
    if s.world_mode == "COLOR":
        return tuple(s.world_color), s.world_strength
    rig_def = RIGS.get(s.rig, RIGS["THREE_POINT"])
    strength, hex_col = rig_def["world"]
    return utils.hex_to_linear(hex_col), strength * s.world_strength


def apply_world(scene):
    s = settings(scene)
    world = bpy.data.worlds.get(WORLD_NAME)
    if world is None or world.get("lumina_scene") != scene.name_full:
        world = None
        for w in bpy.data.worlds:
            if w.get("lumina_scene") == scene.name_full:
                world = w
                break
    if world is None:
        world = bpy.data.worlds.new(WORLD_NAME)
        world["lumina_scene"] = scene.name_full
    if not s.world_saved:
        s.prev_world = scene.world
        s.world_saved = True
    scene.world = world
    if hasattr(world, "use_nodes"):
        try:
            world.use_nodes = True
        except AttributeError:
            pass
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (600, 0)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.location = (200, 60)

    if s.world_mode == "HDRI" and s.hdri not in {"", "NONE"}:
        path = os.path.join(hdri_folder() or "", s.hdri)
        img = bpy.data.images.load(path, check_existing=True) if os.path.isfile(path) else None
        coord = nt.nodes.new("ShaderNodeTexCoord")
        coord.location = (-600, 60)
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.location = (-400, 60)
        mapping.inputs["Rotation"].default_value[2] = math.radians(s.hdri_rotation) + rig_orientation(scene)
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.location = (-150, 60)
        env.image = img
        nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = s.world_strength
        light_shader = bg
    else:
        rgb, strength = _world_rgb_strength(scene)
        bg.inputs["Color"].default_value = (*rgb, 1.0)
        bg.inputs["Strength"].default_value = strength
        light_shader = bg

    camera_sees_world = (s.world_mode == "HDRI" and s.hdri_visible)
    if not camera_sees_world:
        # The camera sees a clean backdrop colour while lighting/reflections
        # still come from the studio world.
        cam_bg = nt.nodes.new("ShaderNodeBackground")
        cam_bg.location = (200, -120)
        cam_bg.inputs["Color"].default_value = (*tuple(s.color_b), 1.0)
        cam_bg.inputs["Strength"].default_value = 1.0
        path = nt.nodes.new("ShaderNodeLightPath")
        path.location = (0, 300)
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.location = (420, 0)
        nt.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
        nt.links.new(light_shader.outputs["Background"], mix.inputs[1])
        nt.links.new(cam_bg.outputs["Background"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    else:
        nt.links.new(light_shader.outputs["Background"], out.inputs["Surface"])


def restore_world(scene):
    s = settings(scene)
    world = scene.world
    if s.world_saved:
        scene.world = s.prev_world
    s.prev_world = None
    s.world_saved = False
    if world is not None and world.get("lumina_scene") == scene.name_full and world.users == 0:
        bpy.data.worlds.remove(world)


def remove(scene, keep_world=False):
    utils.delete_roles(scene, LIGHT, RIG, BG_LIGHT)
    if not keep_world:
        restore_world(scene)
