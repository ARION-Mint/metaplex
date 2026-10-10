# SPDX-License-Identifier: GPL-3.0-or-later
"""Product motion library.

Every motion is a pure function of normalised time ``t`` (0..1) and a
parameter object ``p``. It returns a pose relative to the product's rest pose,
expressed in *camera space* so that "slide in from the left" always means the
left of the frame, whatever the camera angle:

    x  -> towards image right      (product sizes)
    y  -> away from the camera     (product sizes)
    z  -> world up                 (product sizes)
    rx -> tilt about the image-right axis (degrees, + tips the top away)
    ry -> roll about the view axis        (degrees)
    rz -> spin about world up             (degrees)
    s  -> uniform scale, or sx/sy/sz for squash & stretch

``pivot`` is "CENTER" or "BASE" (bottom centre of the product).
``loop`` marks motions whose first and last frame match, so they cycle
seamlessly when the timeline repeats (great for social media loops).
"""

import math

from .utils import (
    damped, in_cubic, in_out_cubic, in_out_sine, in_quad, out_back, out_bounce,
    out_cubic, out_elastic, out_expo, out_quint, seg, smooth,
)

TAU = 2.0 * math.pi


def P(**kw):
    pose = dict(x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0, s=1.0, sx=1.0, sy=1.0, sz=1.0)
    pose.update(kw)
    return pose


def _frac(v):
    return v - math.floor(v)


def _parabola(t):
    return 4.0 * t * (1.0 - t)


def _turns(p):
    return max(1, int(round(p.turns)))


# --------------------------------------------------------------------------
# Entrances: end on the rest pose
# --------------------------------------------------------------------------

def rise(t, p):
    return P(z=-1.1 * p.k * (1 - out_cubic(t)))


def soft_drop(t, p):
    e = out_back(t, 0.9 * p.overshoot)
    return P(z=1.4 * p.k * (1 - e), rz=-12 * (1 - out_cubic(t)))


def gravity_drop(t, p):
    return P(z=2.2 * p.k * (1 - out_bounce(t)))


def slide_in(t, p):
    return P(x=-p.dir * 3.0 * p.k * (1 - out_quint(t)), rz=p.dir * 18 * (1 - out_cubic(t)))


def diagonal_in(t, p):
    e = out_cubic(t)
    return P(x=-p.dir * 2.4 * p.k * (1 - e), z=1.2 * p.k * (1 - e), rz=-p.dir * 35 * (1 - e))


def depth_arrival(t, p):
    e = out_expo(t)
    return P(y=9.0 * p.k * (1 - e), rz=-90 * p.turns * (1 - e))


def float_in(t, p):
    e = in_out_sine(t)
    return P(x=-p.dir * 2.0 * p.k * (1 - e), z=0.35 * p.k * math.sin(math.pi * t) * (1 - t),
             rz=p.dir * 25 * (1 - e), ry=-p.dir * 6 * math.sin(math.pi * t))


def pop_in(t, p):
    s = max(0.001, out_back(t, 1.70158 * p.overshoot))
    return P(s=s, rz=-20 * (1 - out_cubic(t)))


def spin_in(t, p):
    e = out_cubic(t)
    return P(s=max(0.001, e), rz=-p.dir * 360 * p.turns * (1 - e))


def twirl_up(t, p):
    e = out_cubic(t)
    a = TAU * 1.5 * e
    r = 0.7 * p.k * (1 - e)
    return P(x=r * math.sin(a), y=r * (math.cos(a) - 1) * -1, z=-1.0 * p.k * (1 - e), rz=-p.dir * 360 * p.turns * (1 - e))


def emerge(t, p):
    return P(z=-1.7 * p.k * (1 - out_cubic(t)))


def flip_in(t, p):
    e = out_cubic(t)
    return P(rx=-360 * p.turns * (1 - e), z=1.0 * p.k * math.sin(math.pi * e) * (1 - e) + 1.2 * p.k * (1 - e) ** 2, s=0.4 + 0.6 * e)


def stand_up(t, p):
    return P(rx=-90 * (1 - out_back(t, 1.2 * p.overshoot)))


def tilt_reveal(t, p):
    e = out_back(t, 1.1 * p.overshoot)
    return P(ry=p.dir * 30 * (1 - e), rz=-p.dir * 40 * (1 - out_cubic(t)))


def elastic_slide(t, p):
    return P(x=-p.dir * 2.8 * p.k * (1 - out_elastic(t, 0.4)))


def zoom_through(t, p):
    e = out_expo(t)
    return P(y=-3.2 * p.k * (1 - e), rz=p.dir * 60 * (1 - e))


def spring_pop(t, p):
    e = out_elastic(t, 0.35)
    return P(z=-0.9 * p.k * (1 - e), sz=1 + 0.25 * (1 - e) * p.k, sx=1 - 0.1 * (1 - e), sy=1 - 0.1 * (1 - e))


# --------------------------------------------------------------------------
# Hero loops: seamless
# --------------------------------------------------------------------------

def turntable(t, p):
    return P(rz=p.dir * 360 * _turns(p) * t)


def luxury_spin(t, p):
    return P(rz=p.dir * 360 * _turns(p) * t, z=0.05 * p.k * math.sin(TAU * t))


def hover(t, p):
    return P(z=0.12 * p.k * math.sin(TAU * p.cycles * t))


def hover_spin(t, p):
    return P(z=0.1 * p.k * math.sin(TAU * p.cycles * t), rz=p.dir * 360 * _turns(p) * t)


def pendulum(t, p):
    return P(ry=8 * p.k * math.sin(TAU * p.cycles * t))


def breathe(t, p):
    return P(s=1 + 0.04 * p.k * math.sin(TAU * p.cycles * t))


def levitate(t, p):
    a = TAU * p.cycles * t
    return P(z=0.12 * p.k * math.sin(a), rx=5 * p.k * math.sin(a + 1.2), ry=4 * p.k * math.sin(2 * a + 0.5))


def figure_eight(t, p):
    return P(x=0.5 * p.k * math.sin(TAU * t), y=0.25 * p.k * math.sin(2 * TAU * t), rz=12 * p.k * math.sin(TAU * t))


def orbit_drift(t, p):
    a = TAU * t
    return P(x=0.3 * p.k * math.sin(a), y=0.3 * p.k * (1 - math.cos(a)), rz=8 * p.k * math.sin(a))


def zero_g(t, p):
    a = TAU * t
    return P(rx=18 * p.k * math.sin(a), ry=10 * p.k * math.sin(2 * a), rz=p.dir * 360 * t, z=0.12 * p.k * math.sin(a))


def showcase_rock(t, p):
    return P(rx=14 * p.k * math.sin(TAU * p.cycles * t))


def wobble_loop(t, p):
    a = TAU * p.cycles * t
    return P(ry=6 * p.k * math.sin(2 * a), rz=6 * p.k * math.sin(a))


def step_turn(t, p):
    steps = 4
    i = math.floor(t * steps)
    f = smooth(seg(_frac(t * steps), 0.0, 0.4))
    if t >= 1.0:
        i, f = steps, 0.0
    return P(rz=p.dir * 90 * (i + f))


# --------------------------------------------------------------------------
# Rotation
# --------------------------------------------------------------------------

def flip_loop(t, p):
    return P(rx=-360 * _turns(p) * t)


def barrel_roll(t, p):
    return P(ry=p.dir * 360 * _turns(p) * in_out_cubic(t), z=0.4 * p.k * math.sin(math.pi * t))


def bottle_flip(t, p):
    a = seg(t, 0.05, 0.75)
    z = 1.5 * p.k * _parabola(a)
    land = seg(t, 0.75, 1.0)
    squash = 0.12 * p.k * damped(land, 1.5, 5) if t > 0.75 else 0.0
    return P(z=z, rx=-360 * _turns(p) * in_out_cubic(a), sz=1 - squash, sx=1 + squash * 0.5, sy=1 + squash * 0.5)


def spin_reveal(t, p):
    return P(rz=p.dir * 180 * (1 - in_out_cubic(t)))


def snap_turn(t, p):
    return P(rz=-p.dir * 90 * (1 - out_back(t, 2.6 * p.overshoot)))


def tumble(t, p):
    e = in_out_cubic(t)
    return P(rx=360 * e, rz=p.dir * 180 * e, z=0.6 * p.k * math.sin(math.pi * t))


def snap_settle(t, p):
    return P(rz=p.dir * 70 * p.k * damped(t, 1.6, 5.5))


# --------------------------------------------------------------------------
# Path / travel
# --------------------------------------------------------------------------

def arc_pass(t, p):
    return P(x=p.dir * (-3.0 + 6.0 * t) * p.k, z=1.0 * p.k * math.sin(math.pi * t), rz=p.dir * 90 * t)


def s_curve(t, p):
    e = in_out_sine(t)
    return P(x=-p.dir * 2.6 * p.k * (1 - e), y=1.2 * p.k * math.sin(TAU * e) * (1 - e), rz=p.dir * 30 * (1 - e))


def wave_path(t, p):
    return P(x=p.dir * (-3.0 + 6.0 * t) * p.k, z=0.4 * p.k * math.sin(2 * TAU * t), rx=10 * math.cos(2 * TAU * t))


def boomerang(t, p):
    e = math.sin(math.pi * in_out_sine(t))
    return P(x=p.dir * 2.4 * p.k * e, y=0.8 * p.k * e, rz=p.dir * 60 * e)


def flyby(t, p):
    return P(x=p.dir * (-4.0 + 8.0 * t) * p.k, y=-2.6 * p.k, rz=p.dir * 180 * t)


def whip_pass(t, p):
    e = in_out_cubic(t) ** 1.2
    return P(x=p.dir * (-9.0 + 18.0 * e) * p.k, y=-1.4 * p.k, ry=-p.dir * 10)


def helix_rise(t, p):
    e = in_out_sine(t)
    a = TAU * p.cycles * e
    r = 0.8 * p.k * (1 - e)
    return P(x=r * math.sin(a), y=r * (1 - math.cos(a)), z=-1.2 * p.k * (1 - e), rz=p.dir * 360 * _turns(p) * e)


def circle_path(t, p):
    a = TAU * t
    return P(x=1.1 * p.k * math.sin(a) * p.dir, y=1.1 * p.k * (1 - math.cos(a)), rz=p.dir * 360 * t)


def pull_back(t, p):
    return P(y=3.0 * p.k * in_out_sine(t))


def push_to_camera(t, p):
    return P(y=-2.0 * p.k * in_out_sine(t), rz=p.dir * 30 * in_out_sine(t))


# --------------------------------------------------------------------------
# Impact / rhythm
# --------------------------------------------------------------------------

def beat_bounce(t, p):
    ph = _frac(t * p.cycles) if t < 1 else 0.0
    up = _parabola(ph)
    squash = 0.16 * p.k * (math.exp(-ph * 22) + math.exp(-(1 - ph) * 22))
    stretch = 0.08 * p.k * up
    sz = 1 - squash + stretch
    return P(z=0.55 * p.k * up, sz=sz, sx=1 + (1 - sz) * 0.5, sy=1 + (1 - sz) * 0.5)


def beat_pulse(t, p):
    ph = _frac(t * p.cycles) if t < 1 else 0.0
    return P(s=1 + 0.12 * p.k * math.exp(-8 * ph) * (1 - ph))


def heartbeat(t, p):
    ph = _frac(t * p.cycles) if t < 1 else 0.0
    a = math.exp(-60 * (ph - 0.08) ** 2)
    b = math.exp(-60 * (ph - 0.28) ** 2) * 0.7
    return P(s=1 + 0.1 * p.k * (a + b))


def jump_land(t, p):
    a = seg(t, 0.12, 0.62)
    crouch = 0.1 * p.k * math.sin(math.pi * seg(t, 0.0, 0.12))
    land = seg(t, 0.62, 1.0)
    squash = 0.14 * p.k * damped(land, 1.6, 5) if t > 0.62 else 0.0
    sz = 1 - crouch - squash + 0.08 * p.k * math.sin(math.pi * a)
    return P(z=1.3 * p.k * _parabola(a), rz=p.dir * 180 * in_out_cubic(a), sz=sz, sx=1 + (1 - sz) * 0.5, sy=1 + (1 - sz) * 0.5)


def squash_drop(t, p):
    fall = seg(t, 0.0, 0.35)
    z = 2.0 * p.k * (1 - in_quad(fall))
    stretch = 0.15 * p.k * in_quad(fall) if t < 0.35 else 0.0
    land = seg(t, 0.35, 1.0)
    squash = 0.2 * p.k * damped(land, 2.0, 5.5) if t >= 0.35 else 0.0
    sz = 1 + stretch - squash
    return P(z=z, sz=sz, sx=1 + (1 - sz) * 0.5, sy=1 + (1 - sz) * 0.5)


def buzz(t, p):
    env = sum(math.exp(-200 * (_frac(t * p.cycles) - c) ** 2) for c in (0.15, 0.3))
    return P(x=0.025 * p.k * math.sin(TAU * 38 * t) * env, rz=3 * p.k * math.sin(TAU * 29 * t) * env)


def wobble_settle(t, p):
    return P(ry=22 * p.k * damped(t, 3.0, 4.5))


def stomp(t, p):
    fall = seg(t, 0.0, 0.3)
    land = seg(t, 0.3, 1.0)
    squash = 0.22 * p.k * damped(land, 2.2, 6) if t >= 0.3 else 0.0
    sz = 1 - squash
    return P(z=1.4 * p.k * (1 - in_cubic(fall)), sz=sz, sx=1 + (1 - sz) * 0.6, sy=1 + (1 - sz) * 0.6)


# --------------------------------------------------------------------------
# Exits: start on the rest pose
# --------------------------------------------------------------------------

def rise_out(t, p):
    return P(z=3.0 * p.k * in_cubic(t), rz=p.dir * 45 * in_cubic(t))


def sink_out(t, p):
    return P(z=-1.8 * p.k * in_cubic(t))


def slide_out(t, p):
    return P(x=p.dir * 4.0 * p.k * in_cubic(t), rz=-p.dir * 20 * in_cubic(t))


def spin_out(t, p):
    e = in_cubic(t)
    return P(s=max(0.001, 1 - e), rz=p.dir * 360 * p.turns * e)


def fly_to_camera(t, p):
    return P(y=-5.0 * p.k * in_cubic(t), rz=p.dir * 40 * in_cubic(t))


# --------------------------------------------------------------------------
# Stylised combos
# --------------------------------------------------------------------------

def hero_sequence(t, p):
    a = seg(t, 0.0, 0.35)
    b = seg(t, 0.35, 0.6)
    c = seg(t, 0.6, 1.0)
    z = -1.0 * p.k * (1 - out_cubic(a)) + 0.08 * p.k * math.sin(TAU * c) * c
    rz = -p.dir * 270 * (1 - out_cubic(a)) + p.dir * 90 * (out_back(b, 2.0) - 1) + 0.0 * c
    return P(z=z, rz=rz, s=0.6 + 0.4 * out_back(a, 1.4))


def dance(t, p):
    a = TAU * p.cycles * t
    return P(rz=20 * p.k * math.sin(a), ry=10 * p.k * math.sin(2 * a), z=0.15 * p.k * abs(math.sin(a)))


def launch_hover(t, p):
    a = seg(t, 0.0, 0.4)
    c = seg(t, 0.4, 1.0)
    return P(x=-p.dir * 5.0 * p.k * (1 - out_expo(a)), z=0.1 * p.k * math.sin(TAU * c), ry=-p.dir * 12 * (1 - out_cubic(a)))


def dynamic_hero(t, p):
    e = out_cubic(seg(t, 0, 0.6))
    c = seg(t, 0.6, 1.0)
    return P(z=-0.8 * p.k * (1 - e) + 0.06 * p.k * math.sin(TAU * c), rz=-p.dir * 120 * (1 - e), rx=10 * (1 - e))


# --------------------------------------------------------------------------
# Library table
# --------------------------------------------------------------------------
# id: (label, category, function, pivot, loop, guide, description)

CATEGORIES = [
    ("ENTRANCE", "Entrances", "IMPORT"),
    ("LOOP", "Hero Loops", "FILE_REFRESH"),
    ("ROTATE", "Spins & Flips", "DRIVER_ROTATIONAL_DIFFERENCE"),
    ("PATH", "Paths & Travel", "CURVE_PATH"),
    ("RHYTHM", "Impact & Rhythm", "SOUND"),
    ("EXIT", "Exits", "EXPORT"),
    ("STYLE", "Stylised", "SHADERFX"),
]

MOTIONS = {
    # Entrances
    "RISE":          ("Hero Rise",         "ENTRANCE", rise,          "CENTER", False, "●  ↑↑  HERO",       "Rises smoothly into the hero position"),
    "SOFT_DROP":     ("Soft Drop",         "ENTRANCE", soft_drop,     "CENTER", False, "●  ↓  settle",      "Descends gently and settles with a soft overshoot"),
    "GRAVITY_DROP":  ("Gravity Drop",      "ENTRANCE", gravity_drop,  "CENTER", False, "●  ↓↓  bounce",     "Falls with gravity and bounces to rest"),
    "SLIDE_IN":      ("Slide In",          "ENTRANCE", slide_in,      "CENTER", False, "●  ───→  HERO",     "Glides in horizontally from the chosen side"),
    "DIAGONAL_IN":   ("Diagonal Sweep",    "ENTRANCE", diagonal_in,   "CENTER", False, "●  ↘──  HERO",      "Sweeps in from an upper corner"),
    "DEPTH_ARRIVAL": ("Depth Arrival",     "ENTRANCE", depth_arrival, "CENTER", False, "far  ──→  HERO",    "Travels from deep in the scene towards camera"),
    "FLOAT_IN":      ("Float In",          "ENTRANCE", float_in,      "CENTER", False, "●  ~~→  HERO",      "Drifts in weightlessly with a gentle turn"),
    "POP_IN":        ("Pop In",            "ENTRANCE", pop_in,        "BASE",   False, "·  →  ●!  ●",       "Scales up from nothing with a springy overshoot"),
    "SPIN_IN":       ("Spin In",           "ENTRANCE", spin_in,       "BASE",   False, "·  ↻  ●",           "Grows while spinning into place"),
    "TWIRL_UP":      ("Twirl Up",          "ENTRANCE", twirl_up,      "CENTER", False, "⟲  ↑  HERO",        "Spirals upward into position"),
    "EMERGE":        ("Floor Emerge",      "ENTRANCE", emerge,        "CENTER", False, "floor  ↑↑",         "Rises up through the floor"),
    "FLIP_IN":       ("Flip In",           "ENTRANCE", flip_in,       "CENTER", False, "↻  ↓  HERO",        "Somersaults in and lands"),
    "STAND_UP":      ("Stand Up",          "ENTRANCE", stand_up,      "BASE",   False, "—  ↷  |",           "Tips up from lying down to upright"),
    "TILT_REVEAL":   ("Tilt Reveal",       "ENTRANCE", tilt_reveal,   "BASE",   False, "/  →  |",           "Starts tilted and turns upright to face camera"),
    "ELASTIC_SLIDE": ("Elastic Slide",     "ENTRANCE", elastic_slide, "CENTER", False, "→  ↔  HERO",        "Slides in with an elastic wobble"),
    "ZOOM_THROUGH":  ("Zoom Through",      "ENTRANCE", zoom_through,  "CENTER", False, "CAM  ──→  HERO",    "Starts right at the lens and settles back"),
    "SPRING_POP":    ("Spring Pop",        "ENTRANCE", spring_pop,    "BASE",   False, "↑!  ↕  HERO",       "Springs up from below with stretch"),
    # Loops
    "TURNTABLE":     ("Turntable 360",     "LOOP", turntable,      "CENTER", True, "↻ 360°",          "Constant-speed spin; loops seamlessly"),
    "LUX_SPIN":      ("Luxury Spin",       "LOOP", luxury_spin,    "CENTER", True, "slow ↻ + float",  "Slow premium spin with a breath of float"),
    "HOVER":         ("Hover",             "LOOP", hover,          "CENTER", True, "↑ ↓ ↑ ↓",         "Gentle levitation"),
    "HOVER_SPIN":    ("Hover + Spin",      "LOOP", hover_spin,     "CENTER", True, "↑↓ + ↻",          "Levitates while spinning"),
    "PENDULUM":      ("Pendulum Sway",     "LOOP", pendulum,       "BASE",   True, "↶  ↷",            "Soft side-to-side sway from the base"),
    "BREATHE":       ("Breathe",           "LOOP", breathe,        "BASE",   True, "●  ⬤  ●",          "Subtle scale pulse, like breathing"),
    "LEVITATE":      ("Levitate Tilt",     "LOOP", levitate,       "CENTER", True, "↑ ⤢ ↓",           "Floating with organic tilts"),
    "FIGURE_EIGHT":  ("Figure Eight",      "LOOP", figure_eight,   "CENTER", True, "∞",               "Drifts along a horizontal figure eight"),
    "ORBIT_DRIFT":   ("Orbit Drift",       "LOOP", orbit_drift,    "CENTER", True, "small ⟲",         "Small circular drift"),
    "ZERO_G":        ("Zero-G Tumble",     "LOOP", zero_g,         "CENTER", True, "↻ ↺ ⟲",           "Weightless multi-axis rotation"),
    "SHOWCASE_ROCK": ("Showcase Rock",     "LOOP", showcase_rock,  "BASE",   True, "⤺ ⤻",             "Rocks forward and back to show the top"),
    "WOBBLE_LOOP":   ("Wobble",            "LOOP", wobble_loop,    "BASE",   True, "↔ ↕",             "Playful continuous wobble"),
    "STEP_TURN":     ("Feature Steps",     "LOOP", step_turn,      "CENTER", True, "90° ▮ 90° ▮",     "Four quarter turns with holds: shows every side"),
    # Rotation
    "FLIP_LOOP":     ("Flip Loop",         "ROTATE", flip_loop,    "CENTER", True,  "↻ ↻ ↻",          "Continuous end-over-end flip"),
    "BARREL_ROLL":   ("Barrel Roll",       "ROTATE", barrel_roll,  "CENTER", False, "● ↻↻ ●",         "Rolls a full turn around the view axis"),
    "BOTTLE_FLIP":   ("Bottle Flip",       "ROTATE", bottle_flip,  "CENTER", False, "↑ ↻ ↓ ●",        "Jumps, flips and sticks the landing"),
    "SPIN_REVEAL":   ("Spin Reveal",       "ROTATE", spin_reveal,  "CENTER", False, "back ↻ FRONT",   "Turns from the back to the front"),
    "SNAP_TURN":     ("Snap Turn",         "ROTATE", snap_turn,    "CENTER", False, "↻!  ↩  HERO",    "Fast snappy quarter turn with overshoot"),
    "TUMBLE":        ("Tumble",            "ROTATE", tumble,       "CENTER", False, "↻ ⟲ ●",          "Single airborne multi-axis tumble"),
    "SNAP_SETTLE":   ("Snap Settle",       "ROTATE", snap_settle,  "CENTER", False, "↻ ↺ ↻ ·",        "Swings past and settles into the hero pose"),
    # Paths
    "ARC_PASS":      ("Arc Pass",          "PATH", arc_pass,       "CENTER", False, "╭────╮",         "Travels across frame on an arc"),
    "S_CURVE":       ("S-Curve Glide",     "PATH", s_curve,        "CENTER", False, "S ~~→ ●",        "Glides along an S-shaped path into position"),
    "WAVE_PATH":     ("Wave Path",         "PATH", wave_path,      "CENTER", False, "~~~~→",          "Travels across frame on a wave"),
    "BOOMERANG":     ("Boomerang",         "PATH", boomerang,      "CENTER", True,  "● ──→ ↩ ●",      "Swings out and returns"),
    "FLYBY":         ("Foreground Flyby",  "PATH", flyby,          "CENTER", False, "CAM ⇢⇢⇢",        "Passes close to the lens"),
    "WHIP_PASS":     ("Whip Pass",         "PATH", whip_pass,      "CENTER", False, "⇢⇢⇢⇢",           "Very fast transition pass"),
    "HELIX_RISE":    ("Helix Rise",        "PATH", helix_rise,     "CENTER", False, "⟲ + ↑",          "Climbs a narrowing helix into place"),
    "CIRCLE_PATH":   ("Circle Path",       "PATH", circle_path,    "CENTER", True,  "⟲",              "Travels around a circle, facing its path"),
    "PULL_BACK":     ("Pull Back",         "PATH", pull_back,      "CENTER", False, "CAM ←── ●",      "Moves away from camera"),
    "PUSH_TO_CAM":   ("Push to Camera",    "PATH", push_to_camera, "CENTER", False, "● ──→ CAM",      "Moves towards camera"),
    # Rhythm
    "BEAT_BOUNCE":   ("Beat Bounce",       "RHYTHM", beat_bounce,  "BASE", True,  "↑↓ ↑↓ ↑↓",       "Bouncing with squash & stretch, one per beat"),
    "BEAT_PULSE":    ("Beat Pulse",        "RHYTHM", beat_pulse,   "BASE", True,  "● ⬤ ● ⬤",        "Punchy scale hit on every beat"),
    "HEARTBEAT":     ("Heartbeat",         "RHYTHM", heartbeat,    "BASE", True,  "⬤⬤ · ⬤⬤ ·",      "Double pulse like a heartbeat"),
    "JUMP_LAND":     ("Jump & Land",       "RHYTHM", jump_land,    "BASE", False, "↑ ↻ ↓ squash",   "Crouches, jumps, turns and lands"),
    "SQUASH_DROP":   ("Squash Drop",       "RHYTHM", squash_drop,  "BASE", False, "↓ stretch ▬",    "Cartoon drop with stretch and squash"),
    "BUZZ":          ("Buzz",              "RHYTHM", buzz,         "BASE", True,  "≋ · ≋ ·",         "Phone-style vibration bursts"),
    "WOBBLE_SETTLE": ("Wobble Settle",     "RHYTHM", wobble_settle, "BASE", False, "↔ ↔ → still",   "Wobbles after an impact and settles"),
    "STOMP":         ("Stomp",             "RHYTHM", stomp,        "BASE", False, "↓! ▬ ●",          "Slams down with a heavy squash"),
    # Exits
    "RISE_OUT":      ("Rise Out",          "EXIT", rise_out,       "CENTER", False, "● ↑↑↑",          "Lifts up and out of frame"),
    "SINK_OUT":      ("Sink Out",          "EXIT", sink_out,       "CENTER", False, "● ↓↓ floor",     "Sinks into the floor"),
    "SLIDE_OUT":     ("Slide Out",         "EXIT", slide_out,      "CENTER", False, "● ───→",         "Slides out to the chosen side"),
    "SPIN_OUT":      ("Spin Out",          "EXIT", spin_out,       "BASE",   False, "● ↻ ·",          "Spins while shrinking away"),
    "FLY_TO_CAM":    ("Fly to Camera",     "EXIT", fly_to_camera,  "CENTER", False, "● ──→ CAM",      "Rushes into the lens"),
    # Stylised
    "HERO_SEQUENCE": ("Hero Sequence",     "STYLE", hero_sequence, "CENTER", False, "↑ ↻ snap hover", "Three-act reveal: rise, snap turn, hover"),
    "DYNAMIC_HERO":  ("Dynamic Hero",      "STYLE", dynamic_hero,  "CENTER", False, "↑ + ↻ + hover",  "Rise and turn into a floating hold"),
    "LAUNCH_HOVER":  ("Launch & Hover",    "STYLE", launch_hover,  "CENTER", False, "⇢ FAST → hover", "Rockets in and hangs in the air"),
    "DANCE":         ("Product Dance",     "STYLE", dance,         "BASE",   True,  "↖ ↻ ↘ ↺",        "Rhythmic twist and hop"),
}


def motion_items():
    items = []
    index = 0
    for cat_id, cat_label, cat_icon in CATEGORIES:
        items.append(("", cat_label, "", cat_icon, 0))
        for key, entry in MOTIONS.items():
            if entry[1] == cat_id:
                index += 1
                tag = "  (loop)" if entry[4] else ""
                items.append((key, entry[0], entry[6] + tag, "NONE", index))
    return items


def category_label(cat_id):
    for cid, label, _icon in CATEGORIES:
        if cid == cat_id:
            return label
    return ""


class Params:
    """Evaluated user parameters for a motion."""

    __slots__ = ("k", "turns", "dir", "cycles", "overshoot")

    def __init__(self, k=1.0, turns=1.0, direction=1.0, cycles=1, overshoot=1.0):
        self.k = k
        self.turns = turns
        self.dir = direction
        self.cycles = max(1, int(cycles))
        self.overshoot = overshoot


def evaluate(motion_id, t, params):
    entry = MOTIONS.get(motion_id)
    if entry is None:
        return P()
    pose = entry[2](t, params)
    if pose.get("s", 1.0) != 1.0:
        s = pose["s"]
        pose["sx"] *= s
        pose["sy"] *= s
        pose["sz"] *= s
    return pose
