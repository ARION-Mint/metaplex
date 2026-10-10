# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene settings (scene.lumina) with live-update callbacks."""

import bpy
from bpy.props import (
    BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty,
    PointerProperty, StringProperty,
)

from . import backdrop, camera, data_camera, data_lighting, data_looks, data_motion, grade, lighting, motion, output, studio, utils

# Enum item lists must stay referenced for the lifetime of the add-on
SHOT_ITEMS = data_camera.shot_items()
MOVE_ITEMS = data_camera.camera_move_items()
RIG_ITEMS = data_lighting.rig_items()
MOTION_ITEMS = data_motion.motion_items()
GRADE_ITEMS = data_looks.grade_items()
FORMAT_ITEMS = data_looks.format_items()
STYLE_ITEMS = data_looks.style_items()
BATCH_ITEMS = [(fid, label, f"{w} x {h}") for _g, entries in data_looks.FORMAT_GROUPS for fid, label, w, h in entries]
BG_LIGHT_ITEMS = [(k, v[0], v[1]) for k, v in data_lighting.BACKDROP_LIGHTS.items()]
LOOK_ITEMS = [("NONE" if not l else l, "None" if not l else l, "") for l in data_looks.AGX_LOOKS]


def _scene(context):
    return context.scene


def _guard(fn):
    def wrapper(self, context):
        if utils.updates_suspended():
            return
        scene = self.id_data if isinstance(self.id_data, bpy.types.Scene) else context.scene
        if not studio.has_product(scene):
            return
        with utils.suspend_updates():
            fn(scene)
    return wrapper


@_guard
def upd_orientation(scene):
    studio.refresh_orientation(scene)


@_guard
def upd_framing(scene):
    if camera.exists(scene):
        camera.frame(scene)


@_guard
def upd_dof(scene):
    camera.apply_dof(scene)


@_guard
def upd_lights(scene):
    if lighting.exists(scene):
        lighting.build(scene)


@_guard
def upd_light_orientation(scene):
    lighting.update_orientation(scene)


@_guard
def upd_bg_lights(scene):
    if lighting.exists(scene):
        lighting.build_backdrop_lights(scene)


@_guard
def upd_world(scene):
    if lighting.exists(scene):
        lighting.apply_world(scene)


@_guard
def upd_backdrop(scene):
    if backdrop.exists(scene) or utils.settings(scene).studio_built:
        backdrop.build(scene)
        if lighting.exists(scene):
            lighting.build_backdrop_lights(scene)
            lighting.apply_world(scene)


@_guard
def upd_backdrop_colors(scene):
    backdrop.sync_ramp_colors(scene)
    if lighting.exists(scene):
        lighting.apply_world(scene)


@_guard
def upd_backdrop_values(scene):
    backdrop.update_material_values(scene)


@_guard
def upd_backdrop_gradient(scene):
    if backdrop.exists(scene):
        backdrop.build(scene)


def upd_floor_finish(self, context):
    if utils.updates_suspended():
        return
    with utils.suspend_updates():
        self.floor_roughness = backdrop.FINISH_ROUGHNESS[self.floor_finish]
    upd_backdrop_values(self, context)


@_guard
def upd_stage(scene):
    if backdrop.exists(scene) or utils.settings(scene).studio_built:
        # stage height moves the floor, so the whole set follows
        backdrop.build(scene)
        if camera.exists(scene):
            camera.frame(scene)
        if lighting.exists(scene):
            lighting.build_backdrop_lights(scene)


@_guard
def upd_stage_material(scene):
    if utils.objects_with_role(scene, backdrop.STAGE):
        backdrop.stage_material(scene)


@_guard
def upd_decor(scene):
    if backdrop.exists(scene) or utils.settings(scene).studio_built:
        backdrop.build_decor(scene)


@_guard
def upd_decor_material(scene):
    if utils.objects_with_role(scene, backdrop.DECOR):
        backdrop.decor_material(scene)


@_guard
def upd_motion(scene):
    if motion.is_active(scene):
        motion.apply(scene)


@_guard
def upd_timing(scene):
    if motion.is_active(scene):
        motion.apply(scene)
    if camera.exists(scene):
        motion.refresh_camera_move(scene)


@_guard
def upd_camera_move(scene):
    if camera.exists(scene):
        motion.refresh_camera_move(scene)


def upd_grade_preset(self, context):
    if utils.updates_suspended():
        return
    scene = self.id_data
    grade.load_preset(scene, self.grade)
    grade.apply(scene)


def upd_grade(self, context):
    if utils.updates_suspended():
        return
    grade.apply(self.id_data)


def upd_format(self, context):
    if utils.updates_suspended():
        return
    scene = self.id_data
    output.apply_format(scene)
    if studio.has_product(scene) and camera.exists(scene):
        with utils.suspend_updates():
            camera.frame(scene)
    if grade.fx_needed(scene):
        grade.apply(scene)


def upd_quality(self, context):
    if utils.updates_suspended():
        return
    output.apply_quality(self.id_data)


def upd_thirds(self, context):
    cam = camera.get_camera(self.id_data)
    if cam is not None:
        cam.data.show_composition_thirds = self.show_thirds


def upd_hdri_list(self, context):
    upd_world(self, context)


def _color(name, default, update, desc=""):
    return FloatVectorProperty(name=name, description=desc, subtype="COLOR", size=3, min=0.0, max=1.0,
                               default=default, update=update)


class LuminaSettings(bpy.types.PropertyGroup):
    # ------------------------------------------------------------ state
    product_name: StringProperty(name="Product", default="")
    bound_min: FloatVectorProperty(size=3, subtype="XYZ")
    bound_max: FloatVectorProperty(size=3, subtype="XYZ")
    include_children: BoolProperty(name="Include Children", default=True,
                                   description="Also treat child objects of the selection as part of the product")
    studio_built: BoolProperty(default=False)
    prev_camera: PointerProperty(type=bpy.types.Object)
    prev_world: PointerProperty(type=bpy.types.World)
    world_saved: BoolProperty(default=False)
    prev_film_transparent: IntProperty(default=-1)
    cam_distance: FloatProperty(default=0.0)
    cam_lens: FloatProperty(default=50.0)
    cam_el: FloatProperty(default=0.0)
    cam_az: FloatProperty(default=0.0)
    cam_roll: FloatProperty(default=0.0)
    ui_tab: EnumProperty(items=[("STUDIO", "Studio", "", "SCENE", 0), ("CAMERA", "Camera", "", "CAMERA_DATA", 1),
                                ("LIGHT", "Light", "", "LIGHT", 2), ("SET", "Set", "", "MESH_PLANE", 3),
                                ("MOTION", "Motion", "", "ANIM", 4), ("LOOK", "Look", "", "COLOR", 5),
                                ("OUTPUT", "Output", "", "OUTPUT", 6)], default="STUDIO")

    # ------------------------------------------------------------ style
    style: EnumProperty(name="Style", items=STYLE_ITEMS, default="CLEAN_WHITE",
                        description="One-click art direction: lighting, set, colours and grade")
    user_style_name: StringProperty(name="Name", default="My Style")

    # ------------------------------------------------------------ camera
    shot: EnumProperty(name="Shot", items=SHOT_ITEMS, default="HERO", update=upd_orientation)
    orbit_offset: FloatProperty(name="Orbit", description="Rotate the shot around the product (degrees)",
                                default=0.0, min=-180.0, max=180.0, update=upd_orientation)
    height_offset: FloatProperty(name="Height", description="Raise or lower the camera angle (degrees)",
                                 default=0.0, soft_min=-45.0, soft_max=60.0, min=-90.0, max=90.0, update=upd_framing)
    roll: FloatProperty(name="Roll", description="Dutch angle (degrees)", default=0.0, min=-45.0, max=45.0, update=upd_framing)
    lens_override: BoolProperty(name="Custom Lens", default=False, update=upd_framing,
                                description="Override the shot's focal length")
    lens: FloatProperty(name="Focal Length", default=70.0, min=8.0, max=400.0, soft_max=200.0, unit="CAMERA",
                        update=upd_framing)
    fill: FloatProperty(name="Fill", description="How much of the frame the product fills. Above 100% crops in for close-ups",
                        default=72.0, min=10.0, max=400.0, soft_max=200.0, subtype="PERCENTAGE", update=upd_framing)
    pos_x: FloatProperty(name="Horizontal", description="Place the product left/right in frame (leaves copy space)",
                         default=0.0, min=-1.0, max=1.0, update=upd_framing)
    pos_y: FloatProperty(name="Vertical", description="Place the product up/down in frame",
                         default=0.0, min=-1.0, max=1.0, update=upd_framing)
    aim_height: FloatProperty(name="Aim Height", description="Aim at the base (-1), centre (0) or top (1) of the product",
                              default=0.0, min=-1.0, max=1.0, update=upd_framing)
    ortho: BoolProperty(name="Orthographic", description="Flat, distortion-free catalogue projection",
                        default=False, update=upd_framing)
    show_thirds: BoolProperty(name="Thirds Guide", default=True, update=upd_thirds)
    dof: BoolProperty(name="Depth of Field", default=False, update=upd_dof)
    fstop: FloatProperty(name="F-Stop", default=2.8, min=0.5, max=64.0, soft_max=22.0, update=upd_dof)

    # ------------------------------------------------------------ lighting
    use_lights: BoolProperty(name="Product Lights", default=True, update=upd_lights)
    rig: EnumProperty(name="Lighting", items=RIG_ITEMS, default="SOFTBOX_WRAP", update=upd_lights)
    light_power: FloatProperty(name="Power", description="Overall brightness of the rig",
                               default=1.0, min=0.0, soft_max=4.0, max=50.0, update=upd_lights)
    softness: FloatProperty(name="Softness", description="Scale every light source: bigger = softer",
                            default=1.0, min=0.05, soft_max=3.0, max=10.0, update=upd_lights)
    contrast: FloatProperty(name="Contrast", description="Key-to-fill ratio: higher = deeper shadows",
                            default=0.5, min=0.0, max=1.0, subtype="FACTOR", update=upd_lights)
    rim: FloatProperty(name="Rim", description="Strength of rim and kicker lights",
                       default=1.0, min=0.0, soft_max=3.0, max=10.0, update=upd_lights)
    warmth: FloatProperty(name="Warmth", description="Shift every light warmer (+) or cooler (-)",
                          default=0.0, min=-1.5, max=1.5, update=upd_lights)
    light_distance: FloatProperty(name="Distance", description="Move all lights nearer or further",
                                  default=1.0, min=0.3, max=5.0, update=upd_lights)
    rig_rotation: FloatProperty(name="Rotate Rig", description="Swing the whole rig around the product (degrees)",
                                default=0.0, min=-180.0, max=180.0, update=upd_light_orientation)
    product_only_lights: BoolProperty(name="Light Product Only", default=False, update=upd_lights,
                                      description="Use light linking so rig lights only affect the product")
    accent_a: _color("Accent A", (0.02, 0.57, 1.0), upd_lights, "Colour used by coloured rigs and backdrop lights")
    accent_b: _color("Accent B", (1.0, 0.05, 0.32), upd_lights, "Second accent colour")
    bg_light: EnumProperty(name="Backdrop Light", items=BG_LIGHT_ITEMS, default="OFF", update=upd_bg_lights)
    bg_light_power: FloatProperty(name="Power", default=1.0, min=0.0, soft_max=5.0, max=100.0, update=upd_bg_lights)
    bg_light_color: _color("Color", (1.0, 1.0, 1.0), upd_bg_lights)
    bg_light_height: FloatProperty(name="Height", default=0.0, soft_min=-2.0, soft_max=3.0, update=upd_bg_lights)

    world_mode: EnumProperty(name="World", items=[
        ("RIG", "Rig Ambient", "Soft ambient colour designed for the lighting rig"),
        ("COLOR", "Color", "Custom ambient colour"),
        ("HDRI", "HDRI", "Built-in Blender HDRI for real-world reflections")], default="RIG", update=upd_world)
    world_color: _color("Ambient", (0.18, 0.18, 0.19), upd_world)
    world_strength: FloatProperty(name="Strength", default=1.0, min=0.0, soft_max=3.0, max=100.0, update=upd_world)
    hdri: EnumProperty(name="HDRI", items=lighting.hdri_items, update=upd_hdri_list)
    hdri_rotation: FloatProperty(name="Rotation", default=0.0, min=-180.0, max=180.0, update=upd_world)
    hdri_visible: BoolProperty(name="Show HDRI to Camera", default=False, update=upd_world)

    # ------------------------------------------------------------ backdrop
    backdrop: EnumProperty(name="Backdrop", items=[
        ("COVE", "Infinity Cove", "Seamless curved studio sweep", "MOD_CURVE", 0),
        ("DOME", "360 Dome", "Closed dome that looks clean from every angle (best for orbits)", "MESH_UVSPHERE", 1),
        ("CORNER", "Corner", "Floor and wall with a crisp edge", "MESH_PLANE", 2),
        ("FLOOR", "Floor Only", "Endless floor; the horizon shows the backdrop colour", "AXIS_TOP", 3),
        ("CATCHER", "Shadow Catcher", "Transparent background with real shadows (Cycles)", "GHOST_ENABLED", 4),
        ("NONE", "None", "No backdrop", "X", 5)], default="COVE", update=upd_backdrop)
    gradient: EnumProperty(name="Gradient", items=[
        ("SOLID", "Solid", "Single colour", "SNAP_FACE", 0),
        ("LINEAR", "Linear", "Fade from the floor up the wall", "IPO_LINEAR", 1),
        ("RADIAL", "Spotlight", "Radial glow centred behind the product", "LIGHT_POINT", 2)],
        default="LINEAR", update=upd_backdrop_gradient)
    color_a: _color("Color A", (1.0, 1.0, 1.0), upd_backdrop_colors, "Gradient start (near the product)")
    color_b: _color("Color B", (0.69, 0.7, 0.74), upd_backdrop_colors, "Gradient end; also the horizon colour")
    gradient_angle: FloatProperty(name="Angle", default=0.0, min=-180.0, max=180.0, update=upd_backdrop_values)
    gradient_span: FloatProperty(name="Spread", description="Length of the gradient, in product sizes",
                                 default=8.0, min=0.2, soft_max=30.0, max=200.0, update=upd_backdrop_values)
    gradient_offset: FloatProperty(name="Offset", default=0.0, min=-1.0, max=1.0, update=upd_backdrop_values)
    glow: FloatProperty(name="Self Glow", description="Makes the backdrop show its true colour regardless of lighting",
                        default=0.3, min=0.0, soft_max=2.0, max=20.0, update=upd_backdrop_values)
    floor_finish: EnumProperty(name="Floor Finish", items=[
        ("MATTE", "Matte", ""), ("SATIN", "Satin", ""), ("GLOSS", "Gloss", ""), ("MIRROR", "Mirror", "")],
        default="SATIN", update=upd_floor_finish)
    floor_roughness: FloatProperty(name="Roughness", default=0.38, min=0.0, max=1.0, subtype="FACTOR",
                                   update=upd_backdrop_values)
    matte_wall: BoolProperty(name="Matte Wall", default=True, update=upd_backdrop_values,
                             description="Keep the wall matte while the floor reflects")
    wall_distance: FloatProperty(name="Wall Distance", description="Distance from product to wall, in product sizes",
                                 default=3.0, min=0.6, soft_max=12.0, max=100.0, update=upd_backdrop)
    curve_radius: FloatProperty(name="Curve", description="Radius of the floor-to-wall sweep, in product sizes",
                                default=2.0, min=0.05, soft_max=8.0, max=50.0, update=upd_backdrop)
    studio_scale: FloatProperty(name="Studio Size", default=1.0, min=0.3, max=10.0, update=upd_backdrop)

    stage: EnumProperty(name="Stage", items=[
        ("NONE", "None", "", "X", 0), ("CYLINDER", "Round Plinth", "", "MESH_CYLINDER", 1),
        ("STEPS", "Two Tier", "", "SORTSIZE", 2), ("BLOCK", "Block", "", "MESH_CUBE", 3),
        ("HEX", "Hexagon", "", "SEQ_CHROMA_SCOPE", 4), ("SLAB", "Wide Disc", "", "MESH_CIRCLE", 5)],
        default="NONE", update=upd_stage)
    stage_scale: FloatProperty(name="Width", default=1.5, min=0.8, max=6.0, update=upd_stage)
    stage_height: FloatProperty(name="Height", description="In product sizes", default=0.25, min=0.01, max=3.0,
                                update=upd_stage)
    stage_color: _color("Color", (0.88, 0.88, 0.88), upd_stage_material)
    stage_finish: EnumProperty(name="Finish", items=[
        ("MATTE", "Matte", ""), ("SATIN", "Satin", ""), ("GLOSS", "Gloss", ""), ("METAL", "Metal", ""),
        ("GLASS", "Glass", "")], default="MATTE", update=upd_stage_material)

    decor: EnumProperty(name="Set Dressing", items=[
        ("NONE", "None", "", "X", 0), ("ARCH", "Arch", "", "MOD_SOLIDIFY", 1), ("RINGS", "Halo Rings", "", "MESH_TORUS", 2),
        ("ORBS", "Floating Orbs", "", "MESH_UVSPHERE", 3), ("PILLARS", "Pillars", "", "MESH_CYLINDER", 4),
        ("BLOCKS", "Blocks", "", "MESH_CUBE", 5), ("PANELS", "Panels", "", "MESH_PLANE", 6)],
        default="NONE", update=upd_decor)
    decor_color: _color("Color", (0.65, 0.65, 0.65), upd_decor_material)
    decor_glow: FloatProperty(name="Glow", default=0.0, min=0.0, soft_max=20.0, max=200.0, update=upd_decor_material)
    decor_scale: FloatProperty(name="Scale", default=1.0, min=0.2, max=5.0, update=upd_decor)
    decor_seed: IntProperty(name="Variation", default=3, min=0, max=9999, update=upd_decor)

    # ------------------------------------------------------------ motion
    motion: EnumProperty(name="Product Motion", items=MOTION_ITEMS, default="TURNTABLE", update=upd_motion)
    direction: EnumProperty(name="From", items=[("LEFT", "Left", "Enter from / spin towards the left", "BACK", 0),
                                                ("RIGHT", "Right", "Enter from / spin towards the right", "FORWARD", 1)],
                            default="LEFT", update=upd_motion)
    strength: FloatProperty(name="Strength", description="Travel distance and amplitude", default=1.0, min=0.0,
                            soft_max=3.0, max=20.0, update=upd_motion)
    turns: FloatProperty(name="Turns", description="Number of rotations for spinning motions", default=1.0,
                         min=0.25, max=20.0, update=upd_motion)
    cycles: IntProperty(name="Beats", description="Repetitions within the duration for loops and rhythm motions",
                        default=2, min=1, max=64, update=upd_motion)
    overshoot: FloatProperty(name="Overshoot", default=1.0, min=0.0, max=4.0, update=upd_motion)
    reverse: BoolProperty(name="Reverse", description="Play backwards (turns an entrance into an exit)",
                          default=False, update=upd_motion)
    start_frame: IntProperty(name="Start", default=1, min=0, update=upd_timing)
    duration: IntProperty(name="Length", description="Duration in frames", default=120, min=4, max=100000, update=upd_timing)
    fit_timeline: BoolProperty(name="Fit Timeline", default=True, update=upd_motion,
                               description="Set the scene frame range to the motion (loops end one frame early)")
    camera_move: EnumProperty(name="Camera Move", items=MOVE_ITEMS, default="NONE", update=upd_camera_move)
    camera_intensity: FloatProperty(name="Intensity", default=1.0, min=0.0, soft_max=2.0, max=5.0, update=upd_camera_move)
    handheld: BoolProperty(name="Handheld", description="Add subtle organic camera shake", default=False,
                           update=upd_camera_move)
    handheld_amount: FloatProperty(name="Shake", default=1.0, min=0.0, soft_max=3.0, max=20.0, update=upd_camera_move)

    # ------------------------------------------------------------ look
    grade: EnumProperty(name="Grade", items=GRADE_ITEMS, default="CLEAN", update=upd_grade_preset)
    view_transform: EnumProperty(name="View", items=[
        ("AgX", "AgX", "Filmic tone mapping with natural highlight roll-off"),
        ("Khronos PBR Neutral", "PBR Neutral", "Faithful product colours"),
        ("Filmic", "Filmic", "Legacy filmic"), ("Standard", "Standard", "No tone mapping")],
        default="AgX", update=upd_grade)
    look: EnumProperty(name="Contrast Look", items=LOOK_ITEMS, default="NONE", update=upd_grade)
    exposure: FloatProperty(name="Exposure", default=0.0, min=-10.0, max=10.0, soft_min=-3.0, soft_max=3.0, update=upd_grade)
    gamma: FloatProperty(name="Gamma", default=1.0, min=0.2, max=3.0, update=upd_grade)
    wb_temperature: FloatProperty(name="Temperature", default=6500.0, min=1800.0, max=16000.0, update=upd_grade)
    wb_tint: FloatProperty(name="Tint", default=10.0, min=-150.0, max=150.0, update=upd_grade)
    use_fx: BoolProperty(name="Lens FX", description="Bloom, vignette and colour in the compositor", default=True,
                         update=upd_grade)
    bloom: FloatProperty(name="Bloom", default=0.0, min=0.0, max=2.0, update=upd_grade)
    bloom_size: FloatProperty(name="Bloom Size", default=0.6, min=0.0, max=1.0, subtype="FACTOR", update=upd_grade)
    vignette: FloatProperty(name="Vignette", default=0.0, min=0.0, max=1.0, subtype="FACTOR", update=upd_grade)
    aberration: FloatProperty(name="Chromatic Aberration", default=0.0, min=0.0, max=0.1, update=upd_grade)
    saturation: FloatProperty(name="Saturation", default=1.0, min=0.0, max=2.0, update=upd_grade)
    contrast_fx: FloatProperty(name="Contrast", default=0.0, min=-50.0, max=50.0, update=upd_grade)

    # ------------------------------------------------------------ output
    format: EnumProperty(name="Format", items=FORMAT_ITEMS, default="FEED_45", update=upd_format)
    resolution_scale: IntProperty(name="Scale", default=100, min=5, max=400, subtype="PERCENTAGE", update=upd_format)
    engine: EnumProperty(name="Engine", items=[("EEVEE", "EEVEE", "Fast real-time rendering"),
                                               ("CYCLES", "Cycles", "Path tracing for perfect glass and reflections")],
                         default="EEVEE", update=upd_quality)
    quality: EnumProperty(name="Quality", items=[("DRAFT", "Draft", ""), ("PREVIEW", "Preview", ""),
                                                 ("FINAL", "Final", ""), ("ULTRA", "Ultra", "")],
                          default="FINAL", update=upd_quality)
    transparent: BoolProperty(name="Transparent Background", default=False, update=upd_quality)
    motion_blur: BoolProperty(name="Motion Blur", default=False, update=upd_quality)
    output_dir: StringProperty(name="Folder", subtype="DIR_PATH", default="//lumina_renders/")
    batch_formats: EnumProperty(name="Batch Formats", items=BATCH_ITEMS, options={"ENUM_FLAG"},
                                default={"STORY", "FEED_45", "SQUARE", "LANDSCAPE"})
    spin_frames: IntProperty(name="Frames", description="Images in a 360 spin set", default=36, min=4, max=360)


CLASSES = (LuminaSettings,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lumina = PointerProperty(type=LuminaSettings)


def unregister():
    del bpy.types.Scene.lumina
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
