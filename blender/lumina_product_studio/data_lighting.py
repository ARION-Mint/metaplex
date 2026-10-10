# SPDX-License-Identifier: GPL-3.0-or-later
"""Declarative lighting rigs.

Every light is described relative to the camera so a rig always looks the
same in frame, whatever the shot:

    az     degrees around the product, 0 = from the camera side,
           +90 = image right, 180 = directly behind the product
    el     degrees of elevation above the product centre
    d      distance from the product centre, in product sizes
    p      power ratio (1.0 = a normal key light)
    w, h   emitter size in product sizes (area lights)
    shape  RECTANGLE / SQUARE / DISK / ELLIPSE
    k      colour temperature in Kelvin   (or)
    c      "A" / "B" accent colour slots, or a hex colour string
    role   key / fill / rim / kick / top / accent / bounce (drives the
           Contrast and Rim controls)
    type   AREA (default) / SPOT / POINT
    spread area-light spread in degrees (smaller = more like a grid)
    cone   spot cone angle in degrees
"""

def L(n, role, az, el, d, p, w=1.0, h=None, shape="RECTANGLE", k=6500, c=None, type="AREA", spread=None, cone=40, blend=0.4):
    return dict(n=n, role=role, az=az, el=el, d=d, p=p, w=w, h=w if h is None else h, shape=shape,
                k=k, c=c, type=type, spread=spread, cone=cone, blend=blend)


CATEGORIES = [
    ("ESSENTIAL", "Studio Essentials", "LIGHT_AREA"),
    ("BEAUTY", "Beauty & Cosmetics", "MATSHADERBALL"),
    ("GLASS", "Glass & Liquids", "MOD_FLUIDSIM"),
    ("METAL", "Metal & Gloss", "MESH_CYLINDER"),
    ("JEWELRY", "Jewelry & Watches", "SHADING_RENDERED"),
    ("DARK", "Dark & Dramatic", "LIGHT_SPOT"),
    ("TECH", "Tech & Color", "LIGHT_POINT"),
    ("NATURAL", "Natural Light", "LIGHT_SUN"),
]

# world: (strength, hex colour) used when the World mode is "Rig Ambient"
RIGS = {
    # ------------------------------------------------------------------ essentials
    "THREE_POINT": dict(label="Soft Three-Point", cat="ESSENTIAL", world=(0.15, "#9aa0a8"),
        desc="Reliable key, fill and rim. A great starting point for anything",
        lights=[L("Key", "key", 40, 30, 3.0, 1.0, 1.6, 1.6),
                L("Fill", "fill", -55, 12, 3.4, 0.35, 2.2, 2.2),
                L("Rim", "rim", 155, 35, 2.8, 0.8, 0.35, 2.2)]),
    "SOFTBOX_WRAP": dict(label="Softbox Wrap", cat="ESSENTIAL", world=(0.2, "#b5b9c0"),
        desc="Huge soft key that wraps around the form; flattering and forgiving",
        lights=[L("Key", "key", 35, 25, 2.6, 1.0, 3.0, 3.0),
                L("Fill", "fill", -70, 5, 3.0, 0.45, 3.0, 3.0),
                L("Top", "top", 0, 80, 3.0, 0.35, 2.0, 2.0),
                L("Kick", "rim", 140, 20, 3.0, 0.45, 0.4, 2.5)]),
    "HIGH_KEY_TENT": dict(label="High-Key Tent", cat="ESSENTIAL", world=(0.2, "#ffffff"),
        desc="Even, nearly shadowless light for e-commerce on white",
        lights=[L("Left", "key", -70, 20, 2.8, 0.45, 3.5, 3.5),
                L("Right", "key", 70, 20, 2.8, 0.35, 3.5, 3.5),
                L("Top", "top", 0, 85, 2.6, 0.4, 3.5, 3.5),
                L("Front", "fill", 0, 10, 3.5, 0.15, 3.0, 2.0)]),
    "CLAMSHELL": dict(label="Clamshell", cat="ESSENTIAL", world=(0.15, "#a0a0a0"),
        desc="Key above and bounce below the lens; clean frontal read",
        lights=[L("Key", "key", 0, 40, 3.0, 1.0, 2.6, 1.2),
                L("Bounce", "fill", 0, -20, 3.0, 0.4, 2.6, 0.8),
                L("Rim L", "rim", -140, 25, 2.8, 0.45, 0.3, 2.2),
                L("Rim R", "rim", 140, 25, 2.8, 0.45, 0.3, 2.2)]),
    "SHADOWLESS": dict(label="Shadowless Packshot", cat="ESSENTIAL", world=(0.3, "#ffffff"),
        desc="Flat, bright catalogue light from every side",
        lights=[L("Front", "key", 0, 15, 3.0, 0.6, 4.0, 4.0),
                L("Left", "fill", -90, 15, 3.0, 0.5, 4.0, 4.0),
                L("Right", "fill", 90, 15, 3.0, 0.5, 4.0, 4.0),
                L("Top", "top", 0, 88, 3.0, 0.6, 4.0, 4.0)]),
    "WINDOW": dict(label="Window Light", cat="ESSENTIAL", world=(0.12, "#c8d4e6"),
        desc="Single large side window with natural falloff",
        lights=[L("Window", "key", 80, 15, 3.0, 1.3, 2.4, 3.6, k=6200),
                L("Bounce", "fill", -80, 0, 3.5, 0.15, 3.0, 3.0, k=5200)]),

    # ------------------------------------------------------------------ beauty
    "BEAUTY_DISH": dict(label="Beauty Dish", cat="BEAUTY", world=(0.15, "#c9b9b3"),
        desc="Round, crisp-yet-soft frontal key with luminous edges",
        lights=[L("Dish", "key", 10, 35, 2.6, 1.0, 1.4, shape="DISK", spread=60),
                L("Fill", "fill", -40, 0, 3.2, 0.3, 2.5, 2.5),
                L("Hair", "rim", 170, 50, 2.6, 0.55, 1.2, 1.2)]),
    "BUTTERFLY": dict(label="Butterfly Glow", cat="BEAUTY", world=(0.18, "#d8c8c0"),
        desc="High frontal key with a soft under-fill for cosmetics",
        lights=[L("Key", "key", 0, 50, 2.6, 1.0, 1.8, 1.8, k=5400),
                L("Under", "fill", 0, -25, 2.6, 0.35, 2.0, 0.6, k=5000),
                L("Strip L", "rim", -120, 15, 2.6, 0.4, 0.3, 2.4),
                L("Strip R", "rim", 120, 15, 2.6, 0.4, 0.3, 2.4)]),
    "TOP_GLOSS": dict(label="Top Gloss", cat="BEAUTY", world=(0.12, "#b0b0b0"),
        desc="Big overhead source for glossy caps, jars and lids",
        lights=[L("Top", "key", 0, 75, 2.4, 1.0, 3.0, 2.0),
                L("Front", "fill", 0, 10, 3.4, 0.3, 2.0, 1.0),
                L("Back", "rim", 180, 30, 2.6, 0.5, 2.5, 0.5)]),
    "PASTEL_SOFT": dict(label="Pastel Soft", cat="BEAUTY", world=(0.3, "#f2d9e0"),
        desc="Airy, low-contrast light with a hint of colour in the shadows",
        lights=[L("Key", "key", 35, 30, 2.8, 0.9, 3.0, 3.0, k=5800),
                L("Fill", "fill", -60, 10, 3.0, 0.5, 3.0, 3.0, c="A"),
                L("Rim", "rim", 160, 30, 2.8, 0.5, 0.6, 2.4, k=6500)]),

    # ------------------------------------------------------------------ glass
    "BACKLIT_GLOW": dict(label="Backlit Glow", cat="GLASS", world=(0.05, "#808080"),
        desc="Big diffused source behind the product: liquids glow from within",
        lights=[L("Back Panel", "key", 180, 8, 2.4, 1.6, 3.0, 3.0),
                L("Front Kiss", "fill", 0, 20, 3.4, 0.12, 1.5, 1.5),
                L("Top Strip", "top", 0, 80, 2.6, 0.25, 2.0, 0.3)]),
    "DARK_FIELD": dict(label="Dark Field Glass", cat="GLASS", world=(0.0, "#000000"),
        desc="Glass on black defined only by bright edge lines",
        lights=[L("Edge L", "rim", -150, 10, 2.4, 1.0, 0.3, 3.2, spread=30),
                L("Edge R", "rim", 150, 10, 2.4, 1.0, 0.3, 3.2, spread=30),
                L("Top Line", "top", 180, 60, 2.4, 0.4, 2.2, 0.25, spread=30)]),
    "BRIGHT_FIELD": dict(label="Bright Field Glass", cat="GLASS", world=(0.2, "#ffffff"),
        desc="Glass on white with dark, graphic outlines",
        lights=[L("Back Wall", "key", 180, 5, 3.0, 1.4, 4.0, 4.0),
                L("Front", "fill", 0, 15, 3.4, 0.2, 2.0, 2.0)]),
    "STRIP_CONTOURS": dict(label="Strip Contours", cat="GLASS", world=(0.03, "#606060"),
        desc="Long vertical strips trace the silhouette of bottles",
        lights=[L("Strip L", "rim", -110, 5, 2.4, 0.9, 0.35, 3.4),
                L("Strip R", "rim", 110, 5, 2.4, 0.9, 0.35, 3.4),
                L("Label", "key", 15, 15, 3.4, 0.35, 1.2, 1.2),
                L("Halo", "kick", 180, 10, 3.0, 0.5, 1.8, 1.8, shape="DISK")]),
    "LIQUID_HALO": dict(label="Liquid Halo", cat="GLASS", world=(0.04, "#706060"),
        desc="Warm halo behind translucent liquids plus clean side shaping",
        lights=[L("Halo", "key", 180, 12, 2.6, 1.3, 2.2, shape="DISK", k=4300),
                L("Side L", "rim", -95, 10, 2.6, 0.45, 0.4, 3.0),
                L("Side R", "rim", 95, 10, 2.6, 0.45, 0.4, 3.0),
                L("Front", "fill", 0, 20, 3.4, 0.15, 1.5, 1.5)]),
    "DISPERSION": dict(label="Prism Dispersion", cat="GLASS", world=(0.0, "#000000"),
        desc="Red, green and blue rear strips split into rainbow edges in glass",
        lights=[L("Red", "rim", -140, 25, 2.6, 0.8, 0.12, 2.8, c="#ff1a0a"),
                L("Green", "rim", 180, 35, 2.6, 0.65, 0.12, 2.6, c="#14ff2a"),
                L("Blue", "rim", 140, 25, 2.6, 0.85, 0.12, 2.8, c="#1440ff"),
                L("Label", "fill", 0, 15, 3.6, 0.08, 1.2, 1.2)]),

    # ------------------------------------------------------------------ metal
    "TWIN_STRIPS": dict(label="Twin Strips", cat="METAL", world=(0.02, "#505050"),
        desc="Two tall strips give chrome and cans crisp vertical highlights",
        lights=[L("Strip L", "key", -45, 10, 2.4, 1.0, 0.35, 3.6),
                L("Strip R", "key", 50, 10, 2.4, 0.8, 0.35, 3.6),
                L("Top", "top", 0, 85, 2.6, 0.35, 2.2, 0.4)]),
    "GRADIENT_SWEEP": dict(label="Gradient Sweep", cat="METAL", world=(0.03, "#606060"),
        desc="One huge overhead-front panel for smooth gradient reflections",
        lights=[L("Sweep", "key", 0, 55, 2.4, 1.0, 4.0, 2.5, spread=120),
                L("Kick L", "rim", -130, 15, 2.6, 0.5, 0.3, 2.6),
                L("Kick R", "rim", 130, 15, 2.6, 0.5, 0.3, 2.6)]),
    "HARD_STRIP": dict(label="Hard Strip Hero", cat="METAL", world=(0.01, "#404040"),
        desc="Tight gridded strips for precise, graphic specular lines",
        lights=[L("Hard L", "key", -60, 20, 2.4, 1.0, 0.18, 3.0, spread=20),
                L("Hard R", "rim", 120, 25, 2.4, 0.8, 0.18, 3.0, spread=20),
                L("Fill", "fill", 10, 5, 3.6, 0.12, 2.5, 2.5)]),
    "TOP_BAR": dict(label="Top Bar", cat="METAL", world=(0.02, "#505050"),
        desc="Single overhead bar with dark sides: sleek and minimal",
        lights=[L("Bar", "key", 0, 70, 2.4, 1.0, 3.2, 0.35, spread=45),
                L("Fill", "fill", 0, 5, 3.6, 0.08, 2.0, 2.0)]),

    # ------------------------------------------------------------------ jewelry
    "SPARKLE": dict(label="Gem Sparkle", cat="JEWELRY", world=(0.1, "#909090"),
        desc="Soft base light plus tiny hard sources that make facets sparkle",
        lights=[L("Soft Base", "key", 20, 45, 2.6, 0.8, 3.0, 3.0),
                L("Pin 1", "accent", -60, 40, 2.2, 0.35, type="SPOT", cone=12, blend=0.05),
                L("Pin 2", "accent", 75, 30, 2.2, 0.35, type="SPOT", cone=12, blend=0.05),
                L("Pin 3", "accent", 160, 55, 2.2, 0.3, type="SPOT", cone=12, blend=0.05),
                L("Pin 4", "accent", -150, 20, 2.2, 0.25, type="SPOT", cone=12, blend=0.05)]),
    "WATCH_HERO": dict(label="Watch Hero", cat="JEWELRY", world=(0.03, "#606060"),
        desc="Gradient on the crystal, crisp edges on the case",
        lights=[L("Crystal", "key", 0, 60, 2.4, 0.9, 2.6, 1.2, spread=90),
                L("Edge L", "rim", -110, 15, 2.4, 0.6, 0.25, 2.4),
                L("Edge R", "rim", 110, 15, 2.4, 0.6, 0.25, 2.4),
                L("Pin", "accent", 40, 25, 2.2, 0.3, type="SPOT", cone=10, blend=0.05)]),
    "DIFFUSION_TENT": dict(label="Diffusion Tent", cat="JEWELRY", world=(0.5, "#ffffff"),
        desc="Enveloping white tent for polished metals without dark reflections",
        lights=[L("Dome", "key", 0, 70, 2.4, 0.8, 5.0, 5.0),
                L("Ring L", "fill", -90, 20, 2.6, 0.5, 4.0, 3.0),
                L("Ring R", "fill", 90, 20, 2.6, 0.5, 4.0, 3.0),
                L("Back", "rim", 180, 20, 2.6, 0.4, 4.0, 3.0)]),

    # ------------------------------------------------------------------ dark
    "RIM_ONLY": dict(label="Rim Only", cat="DARK", world=(0.0, "#000000"),
        desc="Pure edge definition from behind; no frontal light",
        lights=[L("Rim L", "rim", -145, 20, 2.6, 1.0, 0.35, 3.0),
                L("Rim R", "rim", 145, 20, 2.6, 1.0, 0.35, 3.0)]),
    "SILHOUETTE": dict(label="Silhouette Edge", cat="DARK", world=(0.0, "#000000"),
        desc="Dark hero with a glowing outline and a whisper of front light",
        lights=[L("Back", "kick", 180, 10, 2.8, 1.0, 2.5, 2.5),
                L("Edge L", "rim", -130, 20, 2.6, 0.7, 0.3, 3.0),
                L("Edge R", "rim", 130, 20, 2.6, 0.7, 0.3, 3.0),
                L("Whisper", "fill", 10, 15, 3.6, 0.05, 2.0, 2.0)]),
    "LOW_KEY_SPOT": dict(label="Low-Key Spot", cat="DARK", world=(0.0, "#000000"),
        desc="Theatrical top spotlight with deep falloff",
        lights=[L("Spot", "key", 15, 65, 3.0, 1.3, type="SPOT", cone=30, blend=0.6, k=4800),
                L("Rim", "rim", 170, 25, 2.6, 0.45, 0.3, 2.4)]),
    "CHIAROSCURO": dict(label="Chiaroscuro", cat="DARK", world=(0.0, "#000000"),
        desc="Painterly single side key with dramatic shadow",
        lights=[L("Key", "key", 85, 25, 2.6, 1.2, 1.2, 1.6, spread=70, k=4600),
                L("Kicker", "rim", -150, 20, 2.8, 0.35, 0.3, 2.2, k=7000)]),
    "PREMIUM_DARK": dict(label="Premium Dark", cat="DARK", world=(0.01, "#202020"),
        desc="Low-key luxury: restrained key, bright contours",
        lights=[L("Key", "key", 45, 35, 2.8, 0.6, 1.4, 1.4),
                L("Contour L", "rim", -120, 15, 2.4, 0.8, 0.25, 3.0),
                L("Contour R", "rim", 125, 15, 2.4, 0.8, 0.25, 3.0),
                L("Top", "top", 180, 70, 2.6, 0.3, 2.0, 0.3)]),

    # ------------------------------------------------------------------ tech & colour
    "NEON_DUO": dict(label="Neon Duo", cat="TECH", world=(0.0, "#000000"),
        desc="Two coloured edge lights (Accent A / B) for campaign looks",
        lights=[L("Accent A", "rim", -115, 15, 2.4, 1.1, 0.3, 3.2, c="A"),
                L("Accent B", "rim", 115, 15, 2.4, 1.1, 0.3, 3.2, c="B"),
                L("Fill", "fill", 0, 20, 3.6, 0.1, 2.0, 2.0)]),
    "COLOR_SPLIT": dict(label="Color Split", cat="TECH", world=(0.0, "#000000"),
        desc="Accent A from the left, Accent B from the right, meeting on the face",
        lights=[L("Accent A", "key", -60, 20, 2.6, 0.9, 1.6, 2.4, c="A"),
                L("Accent B", "key", 60, 20, 2.6, 0.9, 1.6, 2.4, c="B"),
                L("Top", "top", 180, 60, 2.6, 0.3, 1.5, 0.3)]),
    "SCREEN_EDGE": dict(label="Screen Edge", cat="TECH", world=(0.01, "#303030"),
        desc="Crisp edge lights for phones, tablets and laptops",
        lights=[L("Edge L", "rim", -100, 25, 2.4, 0.8, 0.2, 3.2, spread=30),
                L("Edge R", "rim", 100, 25, 2.4, 0.8, 0.2, 3.2, spread=30),
                L("Top", "top", 0, 75, 2.6, 0.45, 2.5, 0.5),
                L("Front", "fill", 0, 10, 3.6, 0.1, 2.0, 2.0)]),
    "CYBER_GLOW": dict(label="Cyber Glow", cat="TECH", world=(0.0, "#000000"),
        desc="Accent B underglow, Accent A rim and a cool key",
        lights=[L("Under", "accent", 0, -40, 2.4, 0.7, 2.0, 2.0, c="B"),
                L("Rim", "rim", 160, 25, 2.4, 1.0, 0.3, 3.0, c="A"),
                L("Key", "key", 40, 30, 3.0, 0.45, 1.4, 1.4, k=9000)]),

    # ------------------------------------------------------------------ natural
    "GOLDEN_HOUR": dict(label="Golden Hour", cat="NATURAL", world=(0.25, "#7d9cc9"),
        desc="Low warm sun with cool sky fill",
        lights=[L("Sun", "key", 75, 12, 3.2, 1.4, 0.8, 0.8, k=3200, spread=20),
                L("Sky", "fill", -60, 50, 3.4, 0.35, 4.0, 4.0, k=10000)]),
    "OVERCAST": dict(label="Overcast Day", cat="NATURAL", world=(0.6, "#c4cad4"),
        desc="Soft, even daylight from a bright sky",
        lights=[L("Sky", "key", 20, 70, 3.0, 0.9, 5.0, 5.0, k=6800),
                L("Ground Bounce", "fill", 0, -30, 3.2, 0.12, 4.0, 4.0, k=5000)]),
    "HARD_SUN": dict(label="Hard Noon Sun", cat="NATURAL", world=(0.4, "#88a6d6"),
        desc="Crisp sunlight with sharp graphic shadows",
        lights=[L("Sun", "key", 35, 60, 4.0, 0.8, 0.15, 0.15, k=5600, spread=5),
                L("Sky", "fill", -100, 40, 3.6, 0.2, 4.0, 4.0, k=11000)]),
}

ORDER = [
    "THREE_POINT", "SOFTBOX_WRAP", "HIGH_KEY_TENT", "CLAMSHELL", "SHADOWLESS", "WINDOW",
    "BEAUTY_DISH", "BUTTERFLY", "TOP_GLOSS", "PASTEL_SOFT",
    "BACKLIT_GLOW", "DARK_FIELD", "BRIGHT_FIELD", "STRIP_CONTOURS", "LIQUID_HALO", "DISPERSION",
    "TWIN_STRIPS", "GRADIENT_SWEEP", "HARD_STRIP", "TOP_BAR",
    "SPARKLE", "WATCH_HERO", "DIFFUSION_TENT",
    "RIM_ONLY", "SILHOUETTE", "LOW_KEY_SPOT", "CHIAROSCURO", "PREMIUM_DARK",
    "NEON_DUO", "COLOR_SPLIT", "SCREEN_EDGE", "CYBER_GLOW",
    "GOLDEN_HOUR", "OVERCAST", "HARD_SUN",
]


def rig_items():
    items = []
    index = 0
    for cat_id, cat_label, cat_icon in CATEGORIES:
        items.append(("", cat_label, "", cat_icon, 0))
        for key in ORDER:
            rig = RIGS[key]
            if rig["cat"] == cat_id:
                index += 1
                items.append((key, rig["label"], rig["desc"], "NONE", index))
    return items


# Backdrop accent lights (illuminate only the backdrop via light linking)
BACKDROP_LIGHTS = {
    "OFF":      ("Off", "No backdrop light", []),
    "GLOW":     ("Halo Glow", "Soft pool of light on the wall behind the product",
                 [dict(kind="AREA", x=0.0, z=0.6, w=2.5, p=1.0)]),
    "SPOT":     ("Spot Pool", "Hard-edged theatrical spot on the wall",
                 [dict(kind="SPOT", x=0.0, z=0.6, cone=22, blend=0.25, p=1.2)]),
    "TOP_FADE": ("Top Fade", "Bright at the top fading to dark at the floor",
                 [dict(kind="AREA", x=0.0, z=2.6, w=5.0, p=1.2)]),
    "SIDE_L":   ("Side Wash Left", "Diagonal wash from the left",
                 [dict(kind="AREA", x=-2.2, z=1.2, w=2.0, p=1.0)]),
    "SIDE_R":   ("Side Wash Right", "Diagonal wash from the right",
                 [dict(kind="AREA", x=2.2, z=1.2, w=2.0, p=1.0)]),
    "DUO":      ("Duo Tone", "Accent A and Accent B pools left and right",
                 [dict(kind="AREA", x=-1.6, z=0.8, w=2.2, p=0.9, c="A"),
                  dict(kind="AREA", x=1.6, z=0.8, w=2.2, p=0.9, c="B")]),
}
