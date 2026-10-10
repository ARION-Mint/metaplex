# SPDX-License-Identifier: GPL-3.0-or-later
"""Product selection and measurement."""

import bpy

from . import utils
from .utils import PRODUCT, settings


def _with_children(objs):
    seen = []
    stack = list(objs)
    while stack:
        obj = stack.pop()
        if obj in seen:
            continue
        seen.append(obj)
        stack.extend(obj.children)
    return seen


def measure(scene, depsgraph=None):
    objs = utils.product_objects(scene)
    if not objs:
        return False
    if depsgraph is None:
        depsgraph = bpy.context.evaluated_depsgraph_get()
    lo, hi, _center, _dims = utils.bounds(utils.world_points(objs, depsgraph))
    s = settings(scene)
    s.bound_min = lo
    s.bound_max = hi
    return True


def set_product(context, objs):
    scene = context.scene
    s = settings(scene)
    objs = [o for o in objs if o.get(utils.ROLE) is None]
    if s.include_children:
        objs = _with_children(objs)
    if not objs:
        return False
    clear_product(scene)
    for obj in objs:
        obj[PRODUCT] = True
    roots = utils.product_roots(objs)
    s.product_name = roots[0].name if len(roots) == 1 else f"{roots[0].name} +{len(roots) - 1}"
    measure(scene, context.evaluated_depsgraph_get())
    sync_link_collection(scene)
    return True


def clear_product(scene):
    for obj in utils.product_objects(scene):
        del obj[PRODUCT]
    s = settings(scene)
    s.product_name = ""
    s.bound_min = (0, 0, 0)
    s.bound_max = (0, 0, 0)
    coll = link_collection(scene, create=False)
    if coll is not None:
        bpy.data.collections.remove(coll)


def link_collection(scene, create=True):
    """Unlinked collection holding the product; used as a light-linking receiver set."""
    name = "Lumina Product Link"
    for coll in bpy.data.collections:
        if coll.get("lumina_link") == scene.name_full:
            return coll
    if not create:
        return None
    coll = bpy.data.collections.new(name)
    coll["lumina_link"] = scene.name_full
    coll.use_fake_user = False
    return coll


def sync_link_collection(scene):
    coll = link_collection(scene)
    wanted = set(utils.product_objects(scene))
    for obj in list(coll.objects):
        if obj not in wanted:
            coll.objects.unlink(obj)
    for obj in wanted:
        if obj.name not in coll.objects:
            coll.objects.link(obj)
    return coll


def drop_to_floor(context):
    """Move the product so its lowest point rests at Z = 0."""
    scene = context.scene
    objs = utils.product_objects(scene)
    if not objs:
        return False
    measure(scene, context.evaluated_depsgraph_get())
    dz = -settings(scene).bound_min[2]
    for root in utils.product_roots(objs):
        root.location.z += dz
    context.view_layer.update()
    measure(scene, context.evaluated_depsgraph_get())
    return True
