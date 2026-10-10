# SPDX-License-Identifier: GPL-3.0-or-later
"""Lumina Product Studio: one-click product photography and motion for Blender."""

import bpy

from . import operators, props, ui

_keymaps = []


class LUMINA_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        layout.label(text="Open the studio from the 3D Viewport sidebar (N) > Lumina tab.")
        layout.label(text="Pie menu: Shift + Alt + L in the 3D Viewport (change it in Keymap preferences).")


def register():
    props.register()
    for cls in operators.CLASSES + ui.CLASSES + (LUMINA_Preferences,):
        bpy.utils.register_class(cls)
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is not None:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new("wm.call_menu_pie", "L", "PRESS", shift=True, alt=True)
        kmi.properties.name = "LUMINA_MT_pie"
        _keymaps.append((km, kmi))


def unregister():
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
    for cls in reversed(operators.CLASSES + ui.CLASSES + (LUMINA_Preferences,)):
        bpy.utils.unregister_class(cls)
    props.unregister()
