# SPDX-License-Identifier: GPL-3.0-or-later
"""Operators."""

import os

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty

from . import backdrop, camera, grade, lighting, motion, output, product, studio, utils
from .data_looks import FORMATS
from .utils import settings

PARTS = [("CAMERA", "Camera", ""), ("LIGHTS", "Lights", ""), ("SET", "Set", ""), ("GRADE", "Grade", ""),
         ("ALL", "Everything", "")]


def _need_product(op, context):
    if not studio.has_product(context.scene):
        op.report({"ERROR"}, "Set a product first: select it and press Create Studio")
        return False
    return True


def _look_through(context):
    screen = context.screen
    if screen is None:
        return
    for area in screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.region_3d.view_perspective = "CAMERA"
            if space.shading.type in {"WIREFRAME", "SOLID"}:
                space.shading.type = "MATERIAL"
            break


class LUMINA_OT_create_studio(bpy.types.Operator):
    """Turn the selected object(s) into a product and build a complete studio around them"""
    bl_idname = "lumina.create_studio"
    bl_label = "Create Studio"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        s = settings(scene)
        selected = [o for o in context.selected_objects if o.get(utils.ROLE) is None]
        if selected:
            motion.remove(scene)
            product.set_product(context, selected)
        if not studio.has_product(scene):
            self.report({"ERROR"}, "Select the object(s) that make up your product first")
            return {"CANCELLED"}
        studio.apply_style(scene, s.style)
        output.apply_quality(scene)
        _look_through(context)
        self.report({"INFO"}, f"Studio ready for {s.product_name}")
        return {"FINISHED"}


class LUMINA_OT_set_product(bpy.types.Operator):
    """Use the selected object(s) as the product"""
    bl_idname = "lumina.set_product"
    bl_label = "Set Product from Selection"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        scene = context.scene
        motion.remove(scene)
        if not product.set_product(context, context.selected_objects):
            self.report({"ERROR"}, "Nothing usable selected")
            return {"CANCELLED"}
        if settings(scene).studio_built:
            studio.build_all(scene)
        return {"FINISHED"}


class LUMINA_OT_remeasure(bpy.types.Operator):
    """Measure the product again (after editing or scaling it) and refit everything"""
    bl_idname = "lumina.remeasure"
    bl_label = "Refit to Product"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        if not _need_product(self, context):
            return {"CANCELLED"}
        was_active = motion.is_active(scene)
        motion.remove(scene)
        context.view_layer.update()
        product.measure(scene, context.evaluated_depsgraph_get())
        if settings(scene).studio_built:
            studio.build_all(scene)
        if was_active:
            motion.apply(scene)
        return {"FINISHED"}


class LUMINA_OT_drop_to_floor(bpy.types.Operator):
    """Move the product so it rests on Z = 0"""
    bl_idname = "lumina.drop_to_floor"
    bl_label = "Drop to Floor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        if not _need_product(self, context):
            return {"CANCELLED"}
        was_active = motion.is_active(scene)
        motion.remove(scene)
        context.view_layer.update()
        product.drop_to_floor(context)
        if settings(scene).studio_built:
            studio.build_all(scene)
        if was_active:
            motion.apply(scene)
        return {"FINISHED"}


class LUMINA_OT_clear_product(bpy.types.Operator):
    """Forget the product (does not delete it)"""
    bl_idname = "lumina.clear_product"
    bl_label = "Clear Product"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        motion.remove(context.scene)
        product.clear_product(context.scene)
        return {"FINISHED"}


class LUMINA_OT_apply_style(bpy.types.Operator):
    """Apply the selected style: lighting, backdrop, stage, set dressing and grade"""
    bl_idname = "lumina.apply_style"
    bl_label = "Apply Style"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not _need_product(self, context):
            return {"CANCELLED"}
        studio.apply_style(context.scene, settings(context.scene).style)
        return {"FINISHED"}


class LUMINA_OT_build(bpy.types.Operator):
    """Build or rebuild part of the studio"""
    bl_idname = "lumina.build"
    bl_label = "Build"
    bl_options = {"REGISTER", "UNDO"}

    part: EnumProperty(items=PARTS, default="ALL")

    def execute(self, context):
        scene = context.scene
        if not _need_product(self, context):
            return {"CANCELLED"}
        with utils.suspend_updates():
            if self.part == "ALL":
                studio.build_all(scene)
            elif self.part == "CAMERA":
                camera.build(scene)
                _look_through(context)
            elif self.part == "LIGHTS":
                lighting.build(scene)
            elif self.part == "SET":
                backdrop.build(scene)
                if lighting.exists(scene):
                    lighting.build_backdrop_lights(scene)
            elif self.part == "GRADE":
                grade.apply(scene)
        return {"FINISHED"}


class LUMINA_OT_remove(bpy.types.Operator):
    """Remove part of the studio"""
    bl_idname = "lumina.remove"
    bl_label = "Remove"
    bl_options = {"REGISTER", "UNDO"}

    part: EnumProperty(items=PARTS, default="ALL")

    def invoke(self, context, event):
        if self.part == "ALL":
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        if self.part == "ALL":
            studio.remove_all(scene)
        elif self.part == "CAMERA":
            camera.remove(scene)
        elif self.part == "LIGHTS":
            lighting.remove(scene)
        elif self.part == "SET":
            backdrop.remove(scene, restore_film=True)
            utils.delete_roles(scene, lighting.BG_LIGHT)
        elif self.part == "GRADE":
            grade.remove_compositor(scene)
        return {"FINISHED"}


class LUMINA_OT_cycle(bpy.types.Operator):
    """Step to the previous or next preset"""
    bl_idname = "lumina.cycle"
    bl_label = "Cycle Preset"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    prop: StringProperty()
    step: IntProperty(default=1)

    def execute(self, context):
        s = settings(context.scene)
        prop = s.bl_rna.properties.get(self.prop)
        if prop is None:
            return {"CANCELLED"}
        ids = [i.identifier for i in prop.enum_items if i.identifier]
        current = getattr(s, self.prop)
        idx = ids.index(current) if current in ids else 0
        setattr(s, self.prop, ids[(idx + self.step) % len(ids)])
        if self.prop == "style" and studio.has_product(context.scene):
            studio.apply_style(context.scene, s.style)
        return {"FINISHED"}


class LUMINA_OT_place(bpy.types.Operator):
    """Quick composition: place the product in the frame, leaving copy space"""
    bl_idname = "lumina.place"
    bl_label = "Place in Frame"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    x: bpy.props.FloatProperty(default=0.0)
    y: bpy.props.FloatProperty(default=0.0)

    def execute(self, context):
        s = settings(context.scene)
        with utils.suspend_updates():
            s.pos_x = self.x
        s.pos_y = self.y
        return {"FINISHED"}


class LUMINA_OT_look_through(bpy.types.Operator):
    """View the scene through the Lumina camera"""
    bl_idname = "lumina.look_through"
    bl_label = "Look Through Camera"

    def execute(self, context):
        cam = camera.get_camera(context.scene)
        if cam is not None:
            context.scene.camera = cam
        _look_through(context)
        return {"FINISHED"}


class LUMINA_OT_reset_focus(bpy.types.Operator):
    """Move the focus target back to the product"""
    bl_idname = "lumina.reset_focus"
    bl_label = "Reset Focus"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        camera.reset_focus(context.scene)
        return {"FINISHED"}


class LUMINA_OT_select_role(bpy.types.Operator):
    """Select this studio element"""
    bl_idname = "lumina.select"
    bl_label = "Select"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    name: StringProperty()

    def execute(self, context):
        obj = context.scene.objects.get(self.name)
        if obj is None:
            return {"CANCELLED"}
        for o in context.selected_objects:
            o.select_set(False)
        obj.hide_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class LUMINA_OT_apply_motion(bpy.types.Operator):
    """Animate the product with the selected motion (non-destructive)"""
    bl_idname = "lumina.apply_motion"
    bl_label = "Animate Product"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not _need_product(self, context):
            return {"CANCELLED"}
        scene = context.scene
        motion.apply(scene)
        if camera.exists(scene):
            motion.refresh_camera_move(scene)
        scene.frame_set(settings(scene).start_frame)
        return {"FINISHED"}


class LUMINA_OT_remove_motion(bpy.types.Operator):
    """Remove the product motion and restore the product exactly"""
    bl_idname = "lumina.remove_motion"
    bl_label = "Remove Motion"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        motion.remove(context.scene)
        return {"FINISHED"}


class LUMINA_OT_play(bpy.types.Operator):
    """Play / pause the animation"""
    bl_idname = "lumina.play"
    bl_label = "Play"

    def execute(self, context):
        if context.screen is not None and not context.screen.is_animation_playing:
            context.scene.frame_set(context.scene.frame_start)
        bpy.ops.screen.animation_play()
        return {"FINISHED"}


class LUMINA_OT_save_style(bpy.types.Operator):
    """Save the current lighting, set, camera and grade as a reusable style"""
    bl_idname = "lumina.save_style"
    bl_label = "Save Style"

    def execute(self, context):
        s = settings(context.scene)
        name = s.user_style_name.strip()
        if not name:
            self.report({"ERROR"}, "Give the style a name")
            return {"CANCELLED"}
        fname = studio.save_user_style(context.scene, name)
        self.report({"INFO"}, f"Saved style '{name}' ({fname})")
        return {"FINISHED"}


class LUMINA_OT_load_style(bpy.types.Operator):
    """Load a saved style"""
    bl_idname = "lumina.load_style"
    bl_label = "Load Style"
    bl_options = {"REGISTER", "UNDO"}

    name: StringProperty()

    def execute(self, context):
        if not studio.load_user_style(context.scene, self.name):
            self.report({"ERROR"}, f"Style '{self.name}' not found")
            return {"CANCELLED"}
        return {"FINISHED"}


class LUMINA_OT_delete_style(bpy.types.Operator):
    """Delete a saved style from disk"""
    bl_idname = "lumina.delete_style"
    bl_label = "Delete Style"

    name: StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        studio.delete_user_style(self.name)
        return {"FINISHED"}


class LUMINA_OT_open_styles_folder(bpy.types.Operator):
    """Open the folder where styles are saved (share them with your team)"""
    bl_idname = "lumina.open_styles_folder"
    bl_label = "Open Styles Folder"

    def execute(self, context):
        bpy.ops.wm.path_open(filepath=studio.styles_dir())
        return {"FINISHED"}


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

class LUMINA_OT_render(bpy.types.Operator):
    """Render with the Lumina camera"""
    bl_idname = "lumina.render"
    bl_label = "Render"

    animation: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        scene = context.scene
        cam = camera.get_camera(scene)
        if cam is not None:
            scene.camera = cam
        output.apply_quality(scene)
        if self.animation:
            folder = output.output_dir(scene)
            name = output.safe_name(settings(scene).product_name)
            scene.render.filepath = os.path.join(folder, f"{name}_anim_")
        bpy.ops.render.render("INVOKE_DEFAULT", animation=self.animation)
        return {"FINISHED"}


class LUMINA_OT_render_batch(bpy.types.Operator):
    """Render a still for every checked format; the camera reframes for each aspect ratio"""
    bl_idname = "lumina.render_batch"
    bl_label = "Render All Formats"

    def execute(self, context):
        scene = context.scene
        s = settings(scene)
        if not _need_product(self, context):
            return {"CANCELLED"}
        formats = [f for f in FORMATS if f in s.batch_formats]
        if not formats:
            self.report({"ERROR"}, "Tick at least one format")
            return {"CANCELLED"}
        folder = output.output_dir(scene)
        name = output.safe_name(s.product_name)
        old = (scene.render.resolution_x, scene.render.resolution_y, scene.render.filepath)
        output.apply_quality(scene)
        wm = context.window_manager
        wm.progress_begin(0, len(formats))
        written = []
        try:
            with utils.suspend_updates():
                for i, fmt in enumerate(formats):
                    output.apply_format(scene, fmt)
                    camera.frame(scene)
                    if grade.fx_needed(scene):
                        grade.apply(scene)
                    path = os.path.join(folder, f"{name}_{fmt.lower()}")
                    scene.render.filepath = path
                    bpy.ops.render.render(write_still=True)
                    written.append(path)
                    wm.progress_update(i + 1)
        finally:
            wm.progress_end()
            scene.render.resolution_x, scene.render.resolution_y, scene.render.filepath = old
            with utils.suspend_updates():
                camera.frame(scene)
                if grade.fx_needed(scene):
                    grade.apply(scene)
        self.report({"INFO"}, f"Rendered {len(written)} formats to {folder}")
        return {"FINISHED"}


class LUMINA_OT_render_spin(bpy.types.Operator):
    """Render an N-image 360 spin set for web product viewers"""
    bl_idname = "lumina.render_spin"
    bl_label = "Render 360 Spin Set"

    def execute(self, context):
        scene = context.scene
        s = settings(scene)
        if not _need_product(self, context):
            return {"CANCELLED"}
        was_active = motion.is_active(scene)
        old = (scene.frame_start, scene.frame_end, scene.frame_current, scene.render.filepath)
        folder = os.path.join(output.output_dir(scene), output.safe_name(s.product_name) + "_spin")
        os.makedirs(folder, exist_ok=True)
        output.apply_quality(scene)
        cam_anim = camera.exists(scene) and motion.camera_move_active(scene)
        if cam_anim:
            motion.remove_camera_move(scene)
        frames = motion.bake_spin(scene, s.spin_frames)
        wm = context.window_manager
        wm.progress_begin(0, len(frames))
        try:
            for i, f in enumerate(frames):
                scene.frame_set(f)
                scene.render.filepath = os.path.join(folder, f"spin_{i + 1:03d}")
                bpy.ops.render.render(write_still=True)
                wm.progress_update(i + 1)
        finally:
            wm.progress_end()
            motion.remove(scene)
            if was_active:
                motion.apply(scene)
            if cam_anim:
                motion.refresh_camera_move(scene)
            scene.frame_start, scene.frame_end = old[0], old[1]
            scene.frame_set(old[2])
            scene.render.filepath = old[3]
        self.report({"INFO"}, f"Rendered {len(frames)} spin images to {folder}")
        return {"FINISHED"}


CLASSES = (
    LUMINA_OT_create_studio, LUMINA_OT_set_product, LUMINA_OT_remeasure, LUMINA_OT_drop_to_floor,
    LUMINA_OT_clear_product, LUMINA_OT_apply_style, LUMINA_OT_build, LUMINA_OT_remove, LUMINA_OT_cycle,
    LUMINA_OT_place, LUMINA_OT_look_through, LUMINA_OT_reset_focus, LUMINA_OT_select_role,
    LUMINA_OT_apply_motion, LUMINA_OT_remove_motion, LUMINA_OT_play, LUMINA_OT_save_style,
    LUMINA_OT_load_style, LUMINA_OT_delete_style, LUMINA_OT_open_styles_folder, LUMINA_OT_render,
    LUMINA_OT_render_batch, LUMINA_OT_render_spin,
)
