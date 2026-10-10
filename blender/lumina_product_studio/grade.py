# SPDX-License-Identifier: GPL-3.0-or-later
"""Colour grading: colour management plus an optional compositor FX chain.

Works with both compositor APIs:
  * Blender 4.2 - 4.5: scene.use_nodes / scene.node_tree with a Composite node
  * Blender 5.0+:      scene.compositing_node_group with a Group Output
"""

import bpy

from . import utils
from .data_looks import GRADES
from .utils import settings

TREE_NAME = "Lumina Compositor"
PREFIX = "Lumina "


# --------------------------------------------------------------------------
# Colour management
# --------------------------------------------------------------------------

def apply_color_management(scene):
    s = settings(scene)
    vs = scene.view_settings
    if not utils.try_set(vs, "view_transform", s.view_transform):
        utils.try_set(vs, "view_transform", "AgX") or utils.try_set(vs, "view_transform", "Filmic")
    look = s.look if s.look != "NONE" else ""
    applied = False
    if look:
        for candidate in (f"{vs.view_transform} - {look}", f"AgX - {look}", look):
            if utils.try_set(vs, "look", candidate):
                applied = True
                break
    if not applied:
        utils.try_set(vs, "look", "None")
    vs.exposure = s.exposure
    vs.gamma = s.gamma
    if hasattr(vs, "use_white_balance"):
        neutral = abs(s.wb_temperature - 6500.0) < 1 and abs(s.wb_tint - 10.0) < 0.01
        vs.use_white_balance = not neutral
        vs.white_balance_temperature = s.wb_temperature
        vs.white_balance_tint = s.wb_tint


def load_preset(scene, key):
    """Copy a grade preset into the editable settings (no rebuild)."""
    g = GRADES.get(key)
    if g is None:
        return
    s = settings(scene)
    with utils.suspend_updates():
        s.view_transform = g["view"]
        s.look = g["look"] or "NONE"
        s.exposure = g["exposure"]
        s.gamma = g["gamma"]
        s.wb_temperature = g["temp"]
        s.wb_tint = g["tint"]
        s.bloom = g["bloom"]
        s.bloom_size = g["bloom_size"]
        s.vignette = g["vignette"]
        s.aberration = g["aberration"]
        s.saturation = g["saturation"]
        s.contrast_fx = g["contrast"]


def apply(scene):
    apply_color_management(scene)
    if fx_needed(scene):
        build_compositor(scene)
    else:
        remove_compositor(scene)


def fx_needed(scene):
    s = settings(scene)
    return s.use_fx and (s.bloom > 0 or s.vignette > 0 or s.aberration > 0
                         or abs(s.saturation - 1.0) > 1e-3 or abs(s.contrast_fx) > 1e-3)


# --------------------------------------------------------------------------
# Compositor helpers (version tolerant)
# --------------------------------------------------------------------------

def _new_api(scene):
    return hasattr(scene, "compositing_node_group")


def _socket(sockets, name, kind=None):
    for sock in sockets:
        if sock.name == name and (kind is None or sock.type == kind) and sock.enabled:
            return sock
    for sock in sockets:
        if sock.name == name and (kind is None or sock.type == kind):
            return sock
    return None


def _set(node, value, *names, kind=None):
    """Set an input socket (new API) or a node property (old API)."""
    for name in names:
        sock = _socket(node.inputs, name, kind)
        if sock is not None and hasattr(sock, "default_value"):
            try:
                sock.default_value = value
                return True
            except (TypeError, ValueError):
                continue
        attr = name.lower().replace(" ", "_")
        if hasattr(node, attr):
            try:
                setattr(node, attr, value)
                return True
            except (TypeError, ValueError):
                continue
    return False


def _image_in(node):
    return _socket(node.inputs, "Image", "RGBA") or node.inputs[0]


def _image_out(node):
    return _socket(node.outputs, "Image", "RGBA") or _socket(node.outputs, "Result", "RGBA") or node.outputs[0]


def _get_tree(scene, create=True):
    if _new_api(scene):
        tree = scene.compositing_node_group
        if tree is not None and tree.get("lumina") != scene.name_full:
            return None  # user tree: leave it alone
        if tree is None and create:
            tree = bpy.data.node_groups.new(TREE_NAME, "CompositorNodeTree")
            tree["lumina"] = scene.name_full
            tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            scene.compositing_node_group = tree
        return tree
    tree = scene.node_tree
    if tree is None:
        if not create:
            return None
        scene.use_nodes = True
        tree = scene.node_tree
    foreign = [n for n in tree.nodes if not n.name.startswith(PREFIX)
               and n.bl_idname not in {"CompositorNodeRLayers", "CompositorNodeComposite", "CompositorNodeViewer"}]
    if foreign:
        return None
    if create:
        scene.use_nodes = True
    return tree


def compositor_blocked(scene):
    """True when the scene already has a hand-made compositor we must not touch."""
    if _new_api(scene):
        tree = scene.compositing_node_group
        return tree is not None and tree.get("lumina") != scene.name_full
    tree = scene.node_tree
    if tree is None or not scene.use_nodes:
        return False
    return any(not n.name.startswith(PREFIX) and n.bl_idname not in
               {"CompositorNodeRLayers", "CompositorNodeComposite", "CompositorNodeViewer"} for n in tree.nodes)


def _node(tree, idname, name, loc):
    n = tree.nodes.new(idname)
    n.name = PREFIX + name
    n.label = name
    n.location = loc
    return n


def _mix_multiply(tree, name, loc, new):
    if new:
        n = _node(tree, "ShaderNodeMix", name, loc)
        n.data_type = "RGBA"
        n.blend_type = "MULTIPLY"
        return n, _socket(n.inputs, "Factor", "VALUE"), _socket(n.inputs, "A", "RGBA"), _socket(n.inputs, "B", "RGBA"), _socket(n.outputs, "Result", "RGBA")
    n = _node(tree, "CompositorNodeMixRGB", name, loc)
    n.blend_type = "MULTIPLY"
    return n, n.inputs[0], n.inputs[1], n.inputs[2], n.outputs[0]


def build_compositor(scene):
    tree = _get_tree(scene)
    if tree is None:
        return False
    s = settings(scene)
    tree.nodes.clear()
    new = _new_api(scene)
    x = 0
    rl = _node(tree, "CompositorNodeRLayers", "Render", (x, 0))
    rl.scene = scene
    img = _image_out(rl)

    if s.bloom > 0:
        x += 250
        glare = _node(tree, "CompositorNodeGlare", "Bloom", (x, 0))
        if new:
            _set(glare, "Fog Glow", "Type")
            _set(glare, "High", "Quality")
            _set(glare, 0.85, "Threshold")
            _set(glare, s.bloom, "Strength")
            _set(glare, s.bloom_size, "Size")
        else:
            glare.glare_type = "FOG_GLOW"
            glare.quality = "HIGH"
            glare.threshold = 0.85
            glare.mix = max(-1.0, min(1.0, -1.0 + 2.0 * s.bloom))
            glare.size = max(6, min(9, int(round(6 + 3 * s.bloom_size))))
        tree.links.new(img, _image_in(glare))
        img = _image_out(glare)

    if abs(s.saturation - 1.0) > 1e-3:
        x += 250
        hs = _node(tree, "CompositorNodeHueSat", "Saturation", (x, 0))
        _set(hs, s.saturation, "Saturation")
        tree.links.new(img, _image_in(hs))
        img = _image_out(hs)

    if abs(s.contrast_fx) > 1e-3:
        x += 250
        bc = _node(tree, "CompositorNodeBrightContrast", "Contrast", (x, 0))
        _set(bc, s.contrast_fx, "Contrast")
        tree.links.new(img, _image_in(bc))
        img = _image_out(bc)

    if s.aberration > 0:
        x += 250
        lens = _node(tree, "CompositorNodeLensdist", "Chromatic Aberration", (x, 0))
        _set(lens, s.aberration, "Dispersion")
        _set(lens, True, "Fit", "Use Fit")
        tree.links.new(img, _image_in(lens))
        img = _image_out(lens)

    if s.vignette > 0:
        x += 250
        mask = _node(tree, "CompositorNodeEllipseMask", "Vignette Shape", (x, -300))
        blur = _node(tree, "CompositorNodeBlur", "Vignette Softness", (x + 200, -300))
        r = scene.render
        px = max(r.resolution_x, r.resolution_y) * r.resolution_percentage / 100.0
        if new:
            _set(mask, (0.5, 0.5), "Position")
            _set(mask, (0.92, 0.92), "Size")
            _set(blur, (px * 0.18, px * 0.18), "Size")
        else:
            mask.x, mask.y, mask.width, mask.height = 0.5, 0.5, 0.92, 0.92
            blur.filter_type = "GAUSS"
            blur.use_relative = True
            blur.factor_x = blur.factor_y = 18.0
        tree.links.new(_socket(mask.outputs, "Mask"), _image_in(blur))
        mix, fac, a, b, out = _mix_multiply(tree, "Vignette", (x + 420, 0), new)
        fac.default_value = s.vignette
        tree.links.new(img, a)
        tree.links.new(_image_out(blur), b)
        img = out
        x += 420

    x += 250
    if new:
        out = _node(tree, "NodeGroupOutput", "Output", (x, 0))
        tree.links.new(img, out.inputs[0])
    else:
        comp = _node(tree, "CompositorNodeComposite", "Composite", (x, 0))
        tree.links.new(img, comp.inputs[0])
    viewer = _node(tree, "CompositorNodeViewer", "Viewer", (x, -200))
    tree.links.new(img, viewer.inputs[0])
    if hasattr(scene.render, "use_compositing"):
        scene.render.use_compositing = True
    return True


def remove_compositor(scene):
    if _new_api(scene):
        tree = scene.compositing_node_group
        if tree is not None and tree.get("lumina") == scene.name_full:
            scene.compositing_node_group = None
            if tree.users == 0:
                bpy.data.node_groups.remove(tree)
        return
    tree = scene.node_tree
    if tree is None:
        return
    if any(n.name.startswith(PREFIX) for n in tree.nodes) and not compositor_blocked(scene):
        tree.nodes.clear()
        scene.use_nodes = False
