# SPDX-License-Identifier: GPL-3.0-or-later
"""Camera shot and camera-move libraries (pure data, no bpy)."""

import math

from .utils import in_out_cubic, in_out_sine, out_cubic, smooth

# az: degrees around the product (0 = front, + = towards image right)
# el: degrees above the product centre, lens: focal length (mm), roll: degrees
SHOTS = {
    "HERO":    dict(label="Hero 3/4",     icon="VIEW_PERSPECTIVE", az=32,  el=12,  lens=70,  roll=0,  desc="Classic three-quarter commercial hero angle"),
    "FRONT":   dict(label="Front",        icon="VIEW_ORTHO",       az=0,   el=4,   lens=85,  roll=0,  desc="Straight-on catalogue packshot"),
    "PROFILE": dict(label="Profile",      icon="ARROW_LEFTRIGHT",  az=90,  el=3,   lens=85,  roll=0,  desc="Clean side silhouette"),
    "BACK34":  dict(label="Back 3/4",     icon="LOOP_BACK",        az=145, el=12,  lens=70,  roll=0,  desc="Rear three-quarter detail view"),
    "LOW":     dict(label="Low Hero",     icon="TRIA_UP",          az=24,  el=-5,  lens=50,  roll=0,  desc="Low, powerful angle looking up at the product"),
    "HIGH":    dict(label="High Angle",   icon="TRIA_DOWN",        az=28,  el=35,  lens=70,  roll=0,  desc="Elevated view that shows the top surface"),
    "TOP":     dict(label="Top Down",     icon="AXIS_TOP",         az=0,   el=89,  lens=70,  roll=0,  desc="Flat-lay overhead view"),
    "MACRO":   dict(label="Macro Detail", icon="ZOOM_IN",          az=20,  el=10,  lens=105, roll=0,  desc="Long lens for tight detail and texture"),
    "DUTCH":   dict(label="Dutch Tilt",   icon="DRIVER_ROTATIONAL_DIFFERENCE", az=30, el=10, lens=50, roll=12, desc="Energetic tilted horizon"),
    "WIDE":    dict(label="Wide Editorial", icon="FULLSCREEN_ENTER", az=24, el=8,  lens=35,  roll=0,  desc="Wider lens with more environment and perspective"),
    "WORM":    dict(label="Worm's Eye",   icon="SORT_DESC",        az=15,  el=-16, lens=28,  roll=0,  desc="Extreme low angle for monumental scale"),
}

SHOT_ORDER = ["HERO", "FRONT", "PROFILE", "BACK34", "LOW", "HIGH", "TOP", "MACRO", "DUTCH", "WIDE", "WORM"]


def shot_items():
    return [(k, SHOTS[k]["label"], SHOTS[k]["desc"], SHOTS[k]["icon"], i) for i, k in enumerate(SHOT_ORDER)]


# Camera moves -------------------------------------------------------------
# Each move maps normalised time t (0..1) and intensity k to offsets:
#   orbit  : degrees around the product      tilt : degrees of elevation
#   dolly  : fraction of the framed distance (+ = further away)
#   truck  : sideways, in product sizes      pedestal : vertical, in product sizes
#   roll   : degrees                          zoom : focal length multiplier
#   vertigo: True -> focal length follows distance (dolly zoom)

def _m(**kw):
    return kw


CAMERA_MOVES = {
    "NONE":        ("Locked Off",       "Static camera",                                           lambda t, k: _m()),
    "PUSH_IN":     ("Push In",          "Slow cinematic dolly towards the product",               lambda t, k: _m(dolly=-0.35 * k * in_out_sine(t))),
    "PULL_OUT":    ("Pull Out",         "Dolly away to reveal the product",                       lambda t, k: _m(dolly=0.45 * k * in_out_sine(t) - 0.25 * k)),
    "CREEP":       ("Slow Creep",       "Barely-there push for luxury pacing",                    lambda t, k: _m(dolly=-0.12 * k * t)),
    "TRUCK_L":     ("Truck Left",       "Slide sideways for parallax",                            lambda t, k: _m(truck=(0.6 - 1.2 * in_out_sine(t)) * k)),
    "TRUCK_R":     ("Truck Right",      "Slide sideways for parallax",                            lambda t, k: _m(truck=(-0.6 + 1.2 * in_out_sine(t)) * k)),
    "PEDESTAL_UP": ("Pedestal Up",      "Camera rises vertically",                                lambda t, k: _m(pedestal=(-0.4 + 0.8 * in_out_sine(t)) * k)),
    "PEDESTAL_DN": ("Pedestal Down",    "Camera lowers vertically",                               lambda t, k: _m(pedestal=(0.4 - 0.8 * in_out_sine(t)) * k)),
    "CRANE_UP":    ("Crane Up",         "Rise while tilting down over the product",               lambda t, k: _m(tilt=(-8 + 30 * in_out_cubic(t)) * k, dolly=0.08 * k * t)),
    "CRANE_DOWN":  ("Crane Down",       "Descend from above into a hero angle",                   lambda t, k: _m(tilt=(30 - 34 * in_out_cubic(t)) * k)),
    "ARC_L":       ("Arc Left",         "Gentle 40 degree arc",                                   lambda t, k: _m(orbit=(20 - 40 * in_out_sine(t)) * k)),
    "ARC_R":       ("Arc Right",        "Gentle 40 degree arc",                                   lambda t, k: _m(orbit=(-20 + 40 * in_out_sine(t)) * k)),
    "REVEAL_L":    ("Reveal Arc Left",  "Wide arc that ends on the hero angle",                   lambda t, k: _m(orbit=95 * k * (1 - out_cubic(t)), dolly=0.25 * k * (1 - out_cubic(t)))),
    "REVEAL_R":    ("Reveal Arc Right", "Wide arc that ends on the hero angle",                   lambda t, k: _m(orbit=-95 * k * (1 - out_cubic(t)), dolly=0.25 * k * (1 - out_cubic(t)))),
    "ORBIT_90":    ("Orbit 90",         "Quarter orbit",                                          lambda t, k: _m(orbit=90 * k * in_out_sine(t))),
    "ORBIT_180":   ("Orbit 180",        "Half orbit",                                             lambda t, k: _m(orbit=180 * k * in_out_sine(t))),
    "ORBIT_360":   ("Orbit 360",        "Seamless full orbit (loops perfectly)",                  lambda t, k: _m(orbit=360.0 * t)),
    "PUSH_ARC":    ("Push + Arc",       "Dolly in while arcing around the product",               lambda t, k: _m(orbit=45 * k * in_out_sine(t), dolly=-0.3 * k * in_out_sine(t))),
    "SPIRAL_IN":   ("Spiral In",        "Orbit and push in a single sweeping move",               lambda t, k: _m(orbit=120 * k * (1 - out_cubic(t)), dolly=0.6 * k * (1 - out_cubic(t)), tilt=12 * k * (1 - out_cubic(t)))),
    "RISE_ORBIT":  ("Rising Orbit",     "Orbit while climbing",                                   lambda t, k: _m(orbit=90 * k * in_out_sine(t), tilt=22 * k * in_out_sine(t) - 6 * k)),
    "TOP_REVEAL":  ("Top-Down Reveal",  "Start overhead and swing down to eye level",             lambda t, k: _m(tilt=(70 - 70 * in_out_cubic(t)) * min(k, 1.2), dolly=0.15 * k * (1 - t))),
    "VERTIGO_IN":  ("Dolly Zoom In",    "Hitchcock zoom: background stretches, product stays",   lambda t, k: _m(dolly=-0.45 * k * in_out_sine(t), vertigo=True)),
    "VERTIGO_OUT": ("Dolly Zoom Out",   "Reverse dolly zoom: background compresses",              lambda t, k: _m(dolly=0.9 * k * in_out_sine(t), vertigo=True)),
    "ROLL_IN":     ("Roll Into Frame",  "Dutch roll that settles level",                          lambda t, k: _m(roll=-18 * k * (1 - out_cubic(t)), dolly=-0.12 * k * t)),
    "WHIP":        ("Whip Orbit",       "Fast eased swing for transitions",                       lambda t, k: _m(orbit=-140 * k * (1 - smooth(t) ** 0.35))),
    "FLOAT":       ("Floating Cam",     "Slow drifting camera (loops)",                           lambda t, k: _m(truck=0.15 * k * math.sin(2 * math.pi * t), pedestal=0.1 * k * math.sin(4 * math.pi * t), orbit=4 * k * math.sin(2 * math.pi * t))),
}

CAMERA_MOVE_ORDER = list(CAMERA_MOVES.keys())


def camera_move_items():
    return [(k, CAMERA_MOVES[k][0], CAMERA_MOVES[k][1], i) for i, k in enumerate(CAMERA_MOVE_ORDER)]


def evaluate_move(move_id, t, intensity):
    entry = CAMERA_MOVES.get(move_id, CAMERA_MOVES["NONE"])
    out = dict(orbit=0.0, tilt=0.0, dolly=0.0, truck=0.0, pedestal=0.0, roll=0.0, zoom=1.0, vertigo=False)
    out.update(entry[2](t, intensity))
    return out
