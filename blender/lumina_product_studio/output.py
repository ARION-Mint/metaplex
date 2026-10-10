# SPDX-License-Identifier: GPL-3.0-or-later
"""Formats, render quality, batch and 360 spin-set rendering."""

import os

import bpy

from . import utils
from .data_looks import FORMATS
from .utils import settings


def apply_format(scene, fmt=None):
    s = settings(scene)
    fmt = fmt or s.format
    if fmt in FORMATS:
        _label, w, h = FORMATS[fmt]
        scene.render.resolution_x = w
        scene.render.resolution_y = h
        scene.render.pixel_aspect_x = 1.0
        scene.render.pixel_aspect_y = 1.0
    scene.render.resolution_percentage = s.resolution_scale


QUALITY = {
    # eevee samples, cycles samples, cycles adaptive threshold
    "DRAFT": (16, 64, 0.1),
    "PREVIEW": (48, 192, 0.05),
    "FINAL": (128, 512, 0.02),
    "ULTRA": (256, 2048, 0.008),
}


def apply_quality(scene):
    s = settings(scene)
    ee, cy, thr = QUALITY.get(s.quality, QUALITY["FINAL"])
    r = scene.render
    if s.engine == "CYCLES":
        r.engine = "CYCLES"
        c = scene.cycles
        c.samples = cy
        utils.try_set(c, "use_adaptive_sampling", True)
        utils.try_set(c, "adaptive_threshold", thr)
        utils.try_set(c, "use_denoising", True)
        utils.try_set(c, "preview_samples", max(16, cy // 8))
        utils.try_set(c, "max_bounces", 12 if s.quality in {"FINAL", "ULTRA"} else 8)
        utils.try_set(c, "transmission_bounces", 12 if s.quality in {"FINAL", "ULTRA"} else 8)
        utils.try_set(c, "caustics_reflective", False)
    else:
        r.engine = utils.eevee_engine_id()
        e = scene.eevee
        utils.try_set(e, "taa_render_samples", ee)
        utils.try_set(e, "use_raytracing", s.quality != "DRAFT")
        utils.try_set(e, "use_shadows", True)
        utils.try_set(e, "use_gtao", True)
        if hasattr(e, "ray_tracing_options"):
            utils.try_set(e.ray_tracing_options, "resolution_scale", "1" if s.quality in {"FINAL", "ULTRA"} else "2")
            utils.try_set(e.ray_tracing_options, "use_denoise", True)
        utils.try_set(e, "shadow_ray_count", 2 if s.quality in {"FINAL", "ULTRA"} else 1)
        utils.try_set(e, "shadow_step_count", 8 if s.quality in {"FINAL", "ULTRA"} else 6)
    r.use_motion_blur = s.motion_blur
    if s.backdrop != "CATCHER":
        r.film_transparent = s.transparent


def output_dir(scene):
    s = settings(scene)
    path = bpy.path.abspath(s.output_dir or "//lumina_renders/")
    os.makedirs(path, exist_ok=True)
    return path


def safe_name(text):
    keep = "".join(c if c.isalnum() or c in "-_" else "_" for c in text)
    return keep.strip("_") or "render"
