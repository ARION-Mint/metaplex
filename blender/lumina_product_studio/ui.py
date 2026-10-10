# SPDX-License-Identifier: GPL-3.0-or-later
"""Sidebar UI: one panel with tabs, plus a pie menu."""

import bpy

from . import backdrop, camera, data_camera, data_lighting, data_looks, data_motion, grade, lighting, motion, studio, utils
from .utils import settings


def _cycler(layout, s, prop, text=None):
    row = layout.row(align=True)
    op = row.operator("lumina.cycle", text="", icon="TRIA_LEFT")
    op.prop, op.step = prop, -1
    row.prop(s, prop, text=text if text is not None else "")
    op = row.operator("lumina.cycle", text="", icon="TRIA_RIGHT")
    op.prop, op.step = prop, 1
    return row


def _wrap(layout, text, width=42):
    words = text.split()
    line = ""
    col = layout.column(align=True)
    col.scale_y = 0.75
    for w in words:
        if len(line) + len(w) + 1 > width:
            col.label(text=line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        col.label(text=line)


def _part_row(layout, label, icon, part, built):
    row = layout.row(align=True)
    row.label(text=label, icon=icon)
    sub = row.row(align=True)
    sub.operator("lumina.build", text="Rebuild" if built else "Build", icon="FILE_REFRESH" if built else "ADD").part = part
    rem = sub.row(align=True)
    rem.enabled = built
    rem.operator("lumina.remove", text="", icon="X").part = part


def _section(layout, title, icon):
    box = layout.box()
    box.label(text=title, icon=icon)
    return box


class LUMINA_PT_studio(bpy.types.Panel):
    bl_label = "Lumina Product Studio"
    bl_idname = "LUMINA_PT_studio"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lumina"

    def draw_header(self, context):
        self.layout.label(text="", icon="LIGHT_AREA")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        s = settings(scene)
        ready = studio.has_product(scene)

        if not ready:
            self.draw_welcome(layout, context, s)
            return

        row = layout.row(align=True)
        row.prop(s, "ui_tab", expand=True, icon_only=True)
        tab = s.ui_tab
        labels = {"STUDIO": "Studio", "CAMERA": "Camera", "LIGHT": "Lighting", "SET": "Set & Backdrop",
                  "MOTION": "Motion", "LOOK": "Look & Grade", "OUTPUT": "Output"}
        header = layout.row()
        header.label(text=labels[tab])
        header.operator("lumina.look_through", text="", icon="CAMERA_DATA", emboss=False)
        getattr(self, "draw_" + tab.lower())(layout, context, s)

    # ------------------------------------------------------------------
    def draw_welcome(self, layout, context, s):
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Product studio in one click", icon="INFO")
        col.separator()
        col.label(text="1. Select your product object(s)")
        col.label(text="2. Pick a style")
        col.label(text="3. Press Create Studio")
        layout.separator()
        layout.label(text="Style")
        _cycler(layout, s, "style")
        style = data_looks.STYLES.get(s.style)
        if style:
            _wrap(layout, style["desc"])
        layout.prop(s, "include_children")
        row = layout.row()
        row.scale_y = 1.8
        row.enabled = bool(context.selected_objects)
        row.operator("lumina.create_studio", icon="RENDER_STILL")
        if not context.selected_objects:
            layout.label(text="Select an object to begin", icon="RESTRICT_SELECT_OFF")

    # ------------------------------------------------------------------
    def draw_studio(self, layout, context, s):
        scene = context.scene
        lo, hi, center, dims, size = utils.stored_bounds(scene)
        box = _section(layout, s.product_name or "Product", "PACKAGE")
        unit = scene.unit_settings.scale_length or 1.0
        box.label(text=f"{dims.x * unit:.3g} x {dims.y * unit:.3g} x {dims.z * unit:.3g} m")
        row = box.row(align=True)
        row.operator("lumina.set_product", text="Replace", icon="RESTRICT_SELECT_OFF")
        row.operator("lumina.remeasure", text="Refit", icon="FULLSCREEN_EXIT")
        row.operator("lumina.drop_to_floor", text="Floor", icon="TRIA_DOWN_BAR")
        row.operator("lumina.clear_product", text="", icon="X")

        box = _section(layout, "Style", "BRUSHES_ALL")
        _cycler(box, s, "style")
        style = data_looks.STYLES.get(s.style)
        if style:
            _wrap(box, style["desc"])
        row = box.row()
        row.scale_y = 1.3
        row.operator("lumina.apply_style", icon="CHECKMARK")

        box = _section(layout, "Studio Parts", "OUTLINER")
        col = box.column(align=True)
        _part_row(col, "Camera", "CAMERA_DATA", "CAMERA", camera.exists(scene))
        _part_row(col, "Lights", "LIGHT", "LIGHTS", lighting.exists(scene))
        _part_row(col, "Set", "MESH_PLANE", "SET", backdrop.exists(scene))
        _part_row(col, "Grade", "COLOR", "GRADE", True)
        row = box.row(align=True)
        row.operator("lumina.build", text="Rebuild All", icon="FILE_REFRESH").part = "ALL"
        row.operator("lumina.remove", text="Remove Studio", icon="TRASH").part = "ALL"

        box = _section(layout, "My Styles", "BOOKMARKS")
        row = box.row(align=True)
        row.prop(s, "user_style_name", text="")
        row.operator("lumina.save_style", text="", icon="FILE_TICK")
        row.operator("lumina.open_styles_folder", text="", icon="FILE_FOLDER")
        names = studio.list_user_styles()
        if not names:
            box.label(text="Save a look to reuse it on any product")
        for name in names:
            row = box.row(align=True)
            row.operator("lumina.load_style", text=name, icon="IMPORT").name = name
            row.operator("lumina.delete_style", text="", icon="TRASH").name = name

    # ------------------------------------------------------------------
    def draw_camera(self, layout, context, s):
        scene = context.scene
        if not camera.exists(scene):
            layout.operator("lumina.build", text="Build Camera", icon="ADD").part = "CAMERA"
            return
        box = _section(layout, "Shot", "VIEW_CAMERA")
        grid = box.grid_flow(row_major=True, columns=3, even_columns=True, align=True)
        grid.prop(s, "shot", expand=True)
        shot = data_camera.SHOTS[s.shot]
        box.label(text=shot["desc"], icon="INFO")
        col = box.column(align=True)
        col.prop(s, "orbit_offset", text="Orbit")
        col.prop(s, "height_offset", text="Height")
        col.prop(s, "roll", text="Roll")

        box = _section(layout, "Lens & Framing", "OUTLINER_OB_CAMERA")
        row = box.row(align=True)
        row.prop(s, "lens_override", text="", icon="DECORATE_KEYFRAME" if s.lens_override else "DECORATE_ANIMATE")
        sub = row.row(align=True)
        sub.enabled = s.lens_override
        sub.prop(s, "lens", text=f"Lens  (shot: {shot['lens']}mm)" if not s.lens_override else "Lens")
        box.prop(s, "fill", slider=True)
        box.label(text="Product placement (copy space)")
        row = box.row(align=True)
        for label, x, y in (("Left", -1.0, 0.0), ("Center", 0.0, 0.0), ("Right", 1.0, 0.0)):
            op = row.operator("lumina.place", text=label)
            op.x, op.y = x, y
        row = box.row(align=True)
        for label, x, y in (("Top", 0.0, 1.0), ("Bottom", 0.0, -1.0)):
            op = row.operator("lumina.place", text=label)
            op.x, op.y = x, y
        col = box.column(align=True)
        col.prop(s, "pos_x", slider=True)
        col.prop(s, "pos_y", slider=True)
        col.prop(s, "aim_height", slider=True)
        row = box.row(align=True)
        row.prop(s, "ortho", toggle=True)
        row.prop(s, "show_thirds", toggle=True)

        box = _section(layout, "Focus", "CON_OBJECTSOLVER")
        row = box.row(align=True)
        row.prop(s, "dof", toggle=True)
        sub = row.row(align=True)
        sub.enabled = s.dof
        sub.prop(s, "fstop")
        if s.dof:
            focus = utils.first_with_role(scene, camera.FOCUS)
            row = box.row(align=True)
            if focus is not None:
                row.operator("lumina.select", text="Select Focus Target", icon="RESTRICT_SELECT_OFF").name = focus.name
            row.operator("lumina.reset_focus", text="", icon="LOOP_BACK")
            box.label(text="Move the focus target to rack focus")

    # ------------------------------------------------------------------
    def draw_light(self, layout, context, s):
        scene = context.scene
        box = _section(layout, "Lighting Rig", "LIGHT_AREA")
        _cycler(box, s, "rig")
        rig = data_lighting.RIGS.get(s.rig)
        if rig:
            _wrap(box, rig["desc"])
            uses_accent = any(l.get("c") in {"A", "B"} for l in rig["lights"])
        else:
            uses_accent = False
        if not lighting.exists(scene):
            box.operator("lumina.build", text="Build Lights", icon="ADD").part = "LIGHTS"
        col = box.column(align=True)
        col.prop(s, "light_power", slider=True)
        col.prop(s, "softness", slider=True)
        col.prop(s, "contrast", slider=True)
        col.prop(s, "rim", slider=True)
        col.prop(s, "warmth", slider=True)
        col.prop(s, "light_distance", slider=True)
        col.prop(s, "rig_rotation", slider=True)
        row = box.row(align=True)
        row.prop(s, "accent_a", text="")
        row.prop(s, "accent_b", text="")
        if uses_accent:
            box.label(text="This rig uses the accent colours", icon="COLOR")
        row = box.row(align=True)
        row.prop(s, "use_lights", toggle=True)
        row.prop(s, "product_only_lights", toggle=True)

        lights = lighting.rig_lights(scene)
        if lights:
            box = _section(layout, "Light Mixer", "NODE_COMPOSITING")
            for obj in lights:
                row = box.row(align=True)
                row.operator("lumina.select", text="", icon="RESTRICT_SELECT_OFF", emboss=False).name = obj.name
                row.prop(obj, "hide_render", text="", icon="HIDE_OFF" if not obj.hide_render else "HIDE_ON", emboss=False)
                row.label(text=obj.name.replace("Lumina ", ""))
                row.prop(obj.data, "energy", text="")
                row.prop(obj.data, "color", text="")
            box.label(text="Mixer edits are reset when the rig rebuilds", icon="INFO")

        box = _section(layout, "Backdrop Light", "LIGHT_SPOT")
        box.prop(s, "bg_light", text="")
        if s.bg_light != "OFF":
            col = box.column(align=True)
            col.prop(s, "bg_light_power", slider=True)
            col.prop(s, "bg_light_height", slider=True)
            if s.bg_light != "DUO":
                col.prop(s, "bg_light_color")

        box = _section(layout, "World", "WORLD")
        box.prop(s, "world_mode", expand=True)
        if s.world_mode == "COLOR":
            box.prop(s, "world_color")
        if s.world_mode == "HDRI":
            box.prop(s, "hdri")
            box.prop(s, "hdri_rotation", slider=True)
            box.prop(s, "hdri_visible")
        box.prop(s, "world_strength", slider=True)

    # ------------------------------------------------------------------
    def draw_set(self, layout, context, s):
        scene = context.scene
        box = _section(layout, "Backdrop", "MOD_CURVE")
        box.prop(s, "backdrop", text="")
        if s.backdrop == "CATCHER":
            box.label(text="Shadow catcher needs Cycles", icon="INFO")
        if s.backdrop not in {"NONE", "CATCHER"}:
            row = box.row(align=True)
            row.prop(s, "color_a", text="")
            row.prop(s, "color_b", text="")
            box.prop(s, "gradient", expand=True)
            col = box.column(align=True)
            if s.gradient != "SOLID":
                if s.gradient == "LINEAR" and s.backdrop != "DOME":
                    col.prop(s, "gradient_angle", slider=True)
                col.prop(s, "gradient_span", slider=True)
                col.prop(s, "gradient_offset", slider=True)
            col.prop(s, "glow", slider=True)
            ramp = None
            for mat in bpy.data.materials:
                if mat.get("lumina_scene") == scene.name_full and mat.get("lumina_kind") == backdrop.MAT_PREFIX:
                    ramp = mat.node_tree.nodes.get("Lumina Ramp") if mat.node_tree else None
            if ramp is not None and s.gradient != "SOLID":
                sub = box.box()
                sub.label(text="Gradient Stops (multi-colour)", icon="NODE_TEXTURE")
                sub.template_color_ramp(ramp, "color_ramp", expand=True)

            box.label(text="Floor")
            box.prop(s, "floor_finish", expand=True)
            row = box.row(align=True)
            row.prop(s, "floor_roughness", slider=True)
            row.prop(s, "matte_wall", text="", icon="MESH_PLANE")
            col = box.column(align=True)
            if s.backdrop in {"COVE", "DOME", "CORNER"}:
                col.prop(s, "wall_distance", slider=True)
            if s.backdrop in {"COVE", "DOME"}:
                col.prop(s, "curve_radius", slider=True)
            col.prop(s, "studio_scale", slider=True)
        if not backdrop.exists(scene) and s.backdrop != "NONE":
            box.operator("lumina.build", text="Build Set", icon="ADD").part = "SET"

        if s.camera_move.startswith("ORBIT") and s.backdrop in {"COVE", "CORNER"}:
            layout.label(text="Tip: use 360 Dome for orbit moves", icon="INFO")

        box = _section(layout, "Stage", "MESH_CYLINDER")
        box.prop(s, "stage", text="")
        if s.stage != "NONE":
            col = box.column(align=True)
            col.prop(s, "stage_scale", slider=True)
            col.prop(s, "stage_height", slider=True)
            row = box.row(align=True)
            row.prop(s, "stage_color", text="")
            row.prop(s, "stage_finish", text="")

        box = _section(layout, "Set Dressing", "SCENE_DATA")
        box.prop(s, "decor", text="")
        if s.decor != "NONE":
            row = box.row(align=True)
            row.prop(s, "decor_color", text="")
            row.prop(s, "decor_glow")
            col = box.column(align=True)
            col.prop(s, "decor_scale", slider=True)
            col.prop(s, "decor_seed")

    # ------------------------------------------------------------------
    def draw_motion(self, layout, context, s):
        scene = context.scene
        box = _section(layout, "Product Motion", "ANIM")
        _cycler(box, s, "motion")
        entry = data_motion.MOTIONS.get(s.motion)
        if entry:
            guide = box.box()
            row = guide.row()
            row.label(text=data_motion.category_label(entry[1]), icon="FILE_REFRESH" if entry[4] else "IPO_EASE_IN_OUT")
            if entry[4]:
                row.label(text="Seamless loop")
            big = guide.row()
            big.scale_y = 1.3
            big.alignment = "CENTER"
            big.label(text=entry[5])
            _wrap(guide, entry[6])
        col = box.column(align=True)
        col.row(align=True).prop(s, "direction", expand=True)
        col.prop(s, "strength", slider=True)
        col.prop(s, "turns")
        col.prop(s, "cycles")
        col.prop(s, "overshoot", slider=True)
        box.prop(s, "reverse")
        row = box.row(align=True)
        row.scale_y = 1.3
        active = motion.is_active(scene)
        row.operator("lumina.apply_motion", text="Update Motion" if active else "Animate Product", icon="PLAY" if not active else "FILE_REFRESH")
        sub = row.row(align=True)
        sub.enabled = active
        sub.operator("lumina.remove_motion", text="", icon="X")
        if active:
            box.label(text="Changes update the animation live", icon="CHECKMARK")

        box = _section(layout, "Camera Move", "CON_CAMERASOLVER")
        _cycler(box, s, "camera_move")
        move = data_camera.CAMERA_MOVES.get(s.camera_move)
        if move:
            box.label(text=move[1])
        col = box.column(align=True)
        col.prop(s, "camera_intensity", slider=True)
        row = box.row(align=True)
        row.prop(s, "handheld", toggle=True)
        sub = row.row(align=True)
        sub.enabled = s.handheld
        sub.prop(s, "handheld_amount", slider=True)
        if not camera.exists(scene):
            box.label(text="Build the camera to use camera moves", icon="ERROR")

        box = _section(layout, "Timing", "TIME")
        row = box.row(align=True)
        row.prop(s, "start_frame")
        row.prop(s, "duration")
        fps = scene.render.fps / max(scene.render.fps_base, 1e-6)
        row = box.row(align=True)
        row.label(text=f"{s.duration / fps:.2f} s at {fps:.3g} fps")
        row.prop(scene.render, "fps", text="")
        box.prop(s, "fit_timeline")
        row = box.row()
        row.scale_y = 1.2
        playing = context.screen is not None and context.screen.is_animation_playing
        row.operator("lumina.play", text="Pause" if playing else "Play", icon="PAUSE" if playing else "PLAY")

    # ------------------------------------------------------------------
    def draw_look(self, layout, context, s):
        scene = context.scene
        box = _section(layout, "Grade", "COLOR")
        _cycler(box, s, "grade")
        g = data_looks.GRADES.get(s.grade)
        if g:
            _wrap(box, g["desc"])
        col = box.column(align=True)
        col.prop(s, "view_transform")
        sub = col.column(align=True)
        sub.enabled = s.view_transform == "AgX"
        sub.prop(s, "look")
        col = box.column(align=True)
        col.prop(s, "exposure", slider=True)
        col.prop(s, "gamma", slider=True)
        if hasattr(scene.view_settings, "use_white_balance"):
            col.prop(s, "wb_temperature", slider=True)
            col.prop(s, "wb_tint", slider=True)

        box = _section(layout, "Lens FX", "SHADERFX")
        box.prop(s, "use_fx")
        col = box.column(align=True)
        col.enabled = s.use_fx
        col.prop(s, "bloom", slider=True)
        col.prop(s, "bloom_size", slider=True)
        col.prop(s, "vignette", slider=True)
        col.prop(s, "aberration", slider=True)
        col.prop(s, "saturation", slider=True)
        col.prop(s, "contrast_fx", slider=True)
        if grade.compositor_blocked(scene):
            box.label(text="Scene has its own compositor: FX skipped", icon="ERROR")
        elif s.use_fx and grade.fx_needed(scene):
            box.label(text="FX show in Rendered view and renders", icon="INFO")

    # ------------------------------------------------------------------
    def draw_output(self, layout, context, s):
        scene = context.scene
        box = _section(layout, "Format", "IMAGE_DATA")
        box.prop(s, "format", text="")
        r = scene.render
        row = box.row(align=True)
        row.prop(s, "resolution_scale")
        row.label(text=f"{r.resolution_x * s.resolution_scale // 100} x {r.resolution_y * s.resolution_scale // 100}")

        box = _section(layout, "Quality", "RENDER_STILL")
        box.prop(s, "engine", expand=True)
        box.prop(s, "quality", expand=True)
        row = box.row(align=True)
        row.prop(s, "transparent", toggle=True)
        row.prop(s, "motion_blur", toggle=True)
        box.prop(s, "output_dir")
        row = box.row(align=True)
        row.scale_y = 1.4
        row.operator("lumina.render", text="Render Image", icon="RENDER_STILL").animation = False
        row.operator("lumina.render", text="Render Video", icon="RENDER_ANIMATION").animation = True

        box = _section(layout, "Batch: Every Platform", "DOCUMENTS")
        grid = box.grid_flow(columns=2, even_columns=True, align=True)
        grid.prop(s, "batch_formats", expand=True)
        box.operator("lumina.render_batch", icon="RENDERLAYERS")

        box = _section(layout, "360 Spin Set", "DRIVER_ROTATIONAL_DIFFERENCE")
        box.prop(s, "spin_frames")
        box.operator("lumina.render_spin", icon="FILE_REFRESH")


class LUMINA_MT_pie(bpy.types.Menu):
    bl_label = "Lumina"
    bl_idname = "LUMINA_MT_pie"

    def draw(self, context):
        pie = self.layout.menu_pie()
        ready = studio.has_product(context.scene)
        pie.operator("lumina.create_studio", icon="RENDER_STILL")
        if ready:
            op = pie.operator("lumina.cycle", text="Next Lighting", icon="LIGHT_AREA")
            op.prop, op.step = "rig", 1
            op = pie.operator("lumina.cycle", text="Next Style", icon="BRUSHES_ALL")
            op.prop, op.step = "style", 1
            op = pie.operator("lumina.cycle", text="Next Shot", icon="VIEW_CAMERA")
            op.prop, op.step = "shot", 1
            pie.operator("lumina.look_through", icon="CAMERA_DATA")
            pie.operator("lumina.apply_motion", icon="ANIM")
            pie.operator("lumina.play", icon="PLAY")
            pie.operator("lumina.render", text="Render Image", icon="RENDER_STILL").animation = False


CLASSES = (LUMINA_PT_studio, LUMINA_MT_pie)
