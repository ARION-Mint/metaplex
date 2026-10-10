# SPDX-License-Identifier: GPL-3.0-or-later
"""Grades, output formats and one-click studio styles."""

# --------------------------------------------------------------------------
# Grades: colour management + optional compositor FX
# --------------------------------------------------------------------------
# view: view transform, look: AgX look suffix ("" = none)
# exposure/gamma: colour management, temp/tint: white balance
# bloom, vignette, aberration: compositor FX (0 = off)
# saturation/contrast: compositor colour (1.0 / 0.0 = neutral)

def G(label, desc, view="AgX", look="", exposure=0.0, gamma=1.0, temp=6500.0, tint=10.0,
      bloom=0.0, bloom_size=0.6, vignette=0.0, aberration=0.0, saturation=1.0, contrast=0.0):
    return dict(label=label, desc=desc, view=view, look=look, exposure=exposure, gamma=gamma,
                temp=temp, tint=tint, bloom=bloom, bloom_size=bloom_size, vignette=vignette,
                aberration=aberration, saturation=saturation, contrast=contrast)


GRADES = {
    "TRUE_COLOR":  G("True Color", "Khronos PBR Neutral: product colours exactly as authored (best for e-commerce)", view="Khronos PBR Neutral"),
    "CLEAN":       G("Clean", "Neutral AgX with gentle highlight roll-off"),
    "PUNCHY":      G("Punchy", "More saturation and contrast for social feeds", look="Punchy", saturation=1.05),
    "HIGH_KEY":    G("High Key", "Bright and airy", look="Medium Low Contrast", exposure=0.35, saturation=0.95),
    "SOFT_GLOW":   G("Soft Glow", "Dreamy bloom on highlights", look="Base Contrast", bloom=0.35, bloom_size=0.75, vignette=0.15),
    "LUXURY":      G("Luxury", "Deep contrast, warm highlights, subtle bloom", look="Medium High Contrast", temp=5900, bloom=0.25, vignette=0.35),
    "NOIR":        G("Noir", "Inky blacks and bright edges", look="High Contrast", exposure=-0.2, saturation=0.85, vignette=0.45, bloom=0.15),
    "WARM_GOLD":   G("Warm Gold", "Golden warmth for beauty and fragrance", look="Medium High Contrast", temp=5200, tint=14, bloom=0.2, vignette=0.2),
    "COOL_STEEL":  G("Cool Steel", "Cool, technical, precise", look="Medium High Contrast", temp=7800, saturation=0.9, vignette=0.2),
    "NEON":        G("Neon Night", "Strong bloom and colour for tech and nightlife", look="Punchy", bloom=0.6, bloom_size=0.8, vignette=0.4, aberration=0.012, saturation=1.15),
    "FILMIC_FADE": G("Film Fade", "Soft, desaturated cinematic finish", look="Low Contrast", saturation=0.85, vignette=0.3, gamma=1.05),
    "EDITORIAL":   G("Editorial", "Magazine finish: crisp and slightly matte", look="Base Contrast", saturation=0.92, contrast=8, vignette=0.15),
    "VIVID_POP":   G("Vivid Pop", "Bold saturated colour for playful brands", look="Punchy", saturation=1.25, contrast=6),
}

GRADE_ORDER = list(GRADES.keys())

AGX_LOOKS = ["", "Punchy", "Very High Contrast", "High Contrast", "Medium High Contrast", "Base Contrast",
             "Medium Low Contrast", "Low Contrast", "Very Low Contrast", "Greyscale"]


def grade_items():
    return [(k, GRADES[k]["label"], GRADES[k]["desc"], i) for i, k in enumerate(GRADE_ORDER)]


# --------------------------------------------------------------------------
# Output formats
# --------------------------------------------------------------------------
FORMAT_GROUPS = [
    ("Social", [
        ("STORY", "Story / Reel / TikTok 9:16", 1080, 1920),
        ("FEED_45", "Feed Portrait 4:5", 1080, 1350),
        ("SQUARE", "Square 1:1", 1080, 1080),
        ("PIN", "Pinterest 2:3", 1000, 1500),
        ("LANDSCAPE", "YouTube / Landscape 16:9", 1920, 1080),
        ("LINK", "Link Preview 1.91:1", 1200, 628),
    ]),
    ("E-commerce", [
        ("AMAZON", "Marketplace Square 2000px", 2000, 2000),
        ("SHOP", "Store Square 2048px", 2048, 2048),
        ("PDP_45", "Product Page 4:5", 1600, 2000),
        ("BANNER", "Web Banner 21:9", 2560, 1080),
    ]),
    ("Film & Print", [
        ("HD", "Full HD 1920x1080", 1920, 1080),
        ("UHD", "4K UHD 3840x2160", 3840, 2160),
        ("SCOPE", "Cinema Scope 2.39:1", 2048, 858),
        ("CLASSIC", "Classic 4:3", 1600, 1200),
        ("A4", "A4 Print Portrait (300 dpi)", 2480, 3508),
    ]),
]

FORMATS = {fid: (label, w, h) for _g, items in FORMAT_GROUPS for fid, label, w, h in items}


def format_items():
    items = []
    index = 0
    for group, entries in FORMAT_GROUPS:
        items.append(("", group, ""))
        for fid, label, w, h in entries:
            index += 1
            items.append((fid, label, f"{w} x {h}", index))
    items.append(("", "Other", ""))
    items.append(("CUSTOM", "Custom", "Keep the scene's current resolution", 999))
    return items


# --------------------------------------------------------------------------
# Studio styles: one click sets lighting, backdrop, stage, decor and grade
# --------------------------------------------------------------------------
# Values are written to scene.lumina; colours are sRGB hex.

STYLES = {
    "CLEAN_WHITE": dict(label="Clean White", desc="Bright, minimal studio on white. Safe for any product",
        rig="SOFTBOX_WRAP", backdrop="COVE", gradient="LINEAR", color_a="#ffffff", color_b="#d9dbe0", ramp_pos=0.55,
        glow=0.35, floor_finish="SATIN", stage="NONE", decor="NONE", grade="CLEAN", bg_light="OFF", world_mode="RIG"),
    "PURE_ECOM": dict(label="Pure E-commerce", desc="Pure white background and true colours for marketplaces",
        rig="HIGH_KEY_TENT", backdrop="COVE", gradient="SOLID", color_a="#ffffff", color_b="#ffffff",
        glow=0.8, floor_finish="MATTE", stage="NONE", decor="NONE", grade="TRUE_COLOR", bg_light="OFF", world_mode="RIG"),
    "SOFT_GRAY": dict(label="Soft Gray", desc="Calm product-launch gray with a spotlit wall",
        rig="THREE_POINT", backdrop="COVE", gradient="RADIAL", color_a="#c7c9cc", color_b="#55585e", ramp_pos=0.6,
        glow=0.25, floor_finish="SATIN", stage="NONE", decor="NONE", grade="CLEAN", bg_light="GLOW", world_mode="RIG"),
    "LUXURY_NOIR": dict(label="Luxury Noir", desc="Black-on-black luxury with glossy reflections",
        rig="PREMIUM_DARK", backdrop="COVE", gradient="RADIAL", color_a="#2a2a2e", color_b="#030303", ramp_pos=0.7,
        glow=0.15, floor_finish="GLOSS", stage="CYLINDER", stage_color="#0b0b0c", stage_finish="GLOSS",
        decor="NONE", grade="LUXURY", bg_light="GLOW", accent_a="#ffd9a0", world_mode="RIG"),
    "PERFUME_GOLD": dict(label="Perfume Gold", desc="Warm amber glow for fragrance and beauty",
        rig="LIQUID_HALO", backdrop="COVE", gradient="RADIAL", color_a="#d9a35b", color_b="#2b1606", ramp_pos=0.75,
        glow=0.35, floor_finish="GLOSS", stage="CYLINDER", stage_color="#e8d3b5", stage_finish="SATIN",
        decor="NONE", grade="WARM_GOLD", bg_light="GLOW", world_mode="RIG"),
    "PASTEL_ARCH": dict(label="Pastel Arch", desc="Trendy pastel set with an arch and podium",
        rig="PASTEL_SOFT", backdrop="COVE", gradient="SOLID", color_a="#f4d3d8", color_b="#f4d3d8",
        glow=0.25, floor_finish="MATTE", stage="CYLINDER", stage_color="#fbeef0", stage_finish="MATTE",
        decor="ARCH", decor_color="#eab3bd", grade="HIGH_KEY", bg_light="OFF", accent_a="#ffc6d0", world_mode="RIG"),
    "TECH_NEON": dict(label="Tech Neon", desc="Cyan and magenta rim light on a black mirror floor",
        rig="NEON_DUO", backdrop="COVE", gradient="RADIAL", color_a="#14101f", color_b="#000000", ramp_pos=0.6,
        glow=0.1, floor_finish="MIRROR", stage="NONE", decor="RINGS", decor_color="#00e5ff", decor_glow=6.0,
        grade="NEON", bg_light="DUO", accent_a="#00e5ff", accent_b="#ff2bd6", world_mode="RIG"),
    "CYBER": dict(label="Cyber Pop", desc="Underglow and saturated accents for gadgets and gaming",
        rig="CYBER_GLOW", backdrop="COVE", gradient="LINEAR", color_a="#1b0f33", color_b="#05020c", ramp_pos=0.5,
        glow=0.2, floor_finish="GLOSS", stage="HEX", stage_color="#121018", stage_finish="GLOSS",
        decor="PANELS", decor_color="#7c4dff", decor_glow=2.0, grade="NEON", bg_light="DUO",
        accent_a="#7c4dff", accent_b="#00ffa3", world_mode="RIG"),
    "GOLDEN_HOUR": dict(label="Golden Hour", desc="Warm low sun on a sandy backdrop",
        rig="GOLDEN_HOUR", backdrop="COVE", gradient="LINEAR", color_a="#f2d2a9", color_b="#c98d5b", ramp_pos=0.5,
        glow=0.2, floor_finish="MATTE", stage="BLOCK", stage_color="#e6c9a2", stage_finish="MATTE",
        decor="PILLARS", decor_color="#e9c79c", grade="WARM_GOLD", bg_light="SIDE_R", world_mode="RIG"),
    "ARCTIC": dict(label="Arctic Blue", desc="Icy blue gradient for skincare and tech",
        rig="BUTTERFLY", backdrop="COVE", gradient="LINEAR", color_a="#eaf4ff", color_b="#7aa7d9", ramp_pos=0.45,
        glow=0.35, floor_finish="GLOSS", stage="CYLINDER", stage_color="#f4f8ff", stage_finish="GLOSS",
        decor="ORBS", decor_color="#cfe3ff", grade="COOL_STEEL", bg_light="TOP_FADE", world_mode="RIG"),
    "SPOTLIGHT": dict(label="Spotlight Stage", desc="Theatrical spot on a dark stage",
        rig="LOW_KEY_SPOT", backdrop="COVE", gradient="SOLID", color_a="#1d1d20", color_b="#1d1d20",
        glow=0.0, floor_finish="SATIN", stage="STEPS", stage_color="#18181a", stage_finish="SATIN",
        decor="NONE", grade="NOIR", bg_light="SPOT", world_mode="RIG"),
    "BOLD_COLOR": dict(label="Bold Color", desc="Saturated single-colour pop set",
        rig="HARD_SUN", backdrop="COVE", gradient="SOLID", color_a="#ffcc00", color_b="#ffcc00",
        glow=0.2, floor_finish="MATTE", stage="BLOCK", stage_color="#ff4f9a", stage_finish="MATTE",
        decor="BLOCKS", decor_color="#2f6bff", grade="VIVID_POP", bg_light="OFF", world_mode="RIG"),
    "EDITORIAL_BEIGE": dict(label="Editorial Beige", desc="Calm, natural magazine tones",
        rig="WINDOW", backdrop="COVE", gradient="LINEAR", color_a="#efe6da", color_b="#cdbba3", ramp_pos=0.55,
        glow=0.2, floor_finish="MATTE", stage="BLOCK", stage_color="#d8c6ad", stage_finish="MATTE",
        decor="ARCH", decor_color="#c9b294", grade="EDITORIAL", bg_light="SIDE_L", world_mode="RIG"),
    "GLASS_ON_BLACK": dict(label="Glass on Black", desc="Dark-field contour lighting for bottles and glassware",
        rig="DARK_FIELD", backdrop="COVE", gradient="SOLID", color_a="#000000", color_b="#000000",
        glow=0.0, floor_finish="MIRROR", stage="NONE", decor="NONE", grade="NOIR", bg_light="OFF", world_mode="RIG"),
    "NATURAL_HDRI": dict(label="Natural HDRI", desc="Real-world reflections from a built-in HDRI on a soft floor",
        rig="OVERCAST", backdrop="FLOOR", gradient="RADIAL", color_a="#e9e6e1", color_b="#bdb8b0", ramp_pos=0.8,
        glow=0.1, floor_finish="SATIN", stage="NONE", decor="NONE", grade="CLEAN", bg_light="OFF",
        world_mode="HDRI", hdri="courtyard.exr"),
}

STYLE_ORDER = list(STYLES.keys())


def style_items():
    return [(k, STYLES[k]["label"], STYLES[k]["desc"], i) for i, k in enumerate(STYLE_ORDER)]
