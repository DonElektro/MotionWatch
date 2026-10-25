#!/usr/bin/env python3
"""
Motion Watch – example 360° video scenes for the simulator (made on your own computer, nothing is downloaded).

Makes three 360° videos (2048 x 1024, 15 pictures per second, about 40 s, played in a loop) with a .json each:
  wald_nacht.mp4        forest at night, filmed with infrared light: fox, two deer, a wild boar (eyes shine)
  parkplatz_nacht.mp4   car park at night with street lamps: a passer-by, then somebody who tries car doors and runs away
  camping_morgen.mp4    camping place on a misty morning: tent, caravan, a deer grazing, a person with a dog, a cat

Start:   python3 motionwatch_demo_scenes.py [folder]      (default: sim_assets/videos next to this file)
or in the simulator: «Beispiel-Videoszenen erzeugen» (window, or the web page of Motion Watch).
Uses ffmpeg (H.264) when it is there, otherwise OpenCV (bigger files).
"""
import json
import math
import os
import shutil
import subprocess
import sys
import time

import cv2
import numpy as np

W, H, FPS = 2048, 1024, 15
CAM_H = 1.6
HZ = H // 2


# ---- 360° geometry: azimuth (deg, 0 = ahead, + right), elevation (deg) -> pixel -------------------------------------
def px(az):
    return (az + 180.0) / 360.0 * W


def py(el):
    return (90.0 - el) / 180.0 * H


def polar(x, z):
    """world position on the ground (m, x right, z ahead) -> azimuth (deg), distance (m)"""
    return math.degrees(math.atan2(x, z)), max(0.3, math.hypot(x, z))


def el_of(h, d):
    return math.degrees(math.atan2(h - CAM_H, d))


def ground_dist():
    """distance of the ground for every picture row (rows above the horizon: far)"""
    rows = np.arange(H, dtype=np.float32) + 0.5
    el = 90.0 - rows / H * 180.0
    d = np.full(H, 5000.0, np.float32)
    below = el < -0.05
    d[below] = CAM_H / np.tan(np.radians(-el[below]))
    return np.minimum(d, 5000.0)


def noise(shape, scale, seed):
    rng = np.random.default_rng(seed)
    small = rng.normal(0, 1, (max(2, shape[0] // scale), max(2, shape[1] // scale))).astype(np.float32)
    return cv2.resize(small, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)


def ground_tex(seed):
    """a pattern lying on the ground (grass, leaves, asphalt) - in perspective, so it gets finer with the distance"""
    d = ground_dist()[HZ:]
    az = (np.arange(W) + 0.5) / W * 360.0 - 180.0
    X = np.clip(d[:, None] * np.sin(np.radians(az))[None, :], -300, 300)
    Z = np.clip(d[:, None] * np.cos(np.radians(az))[None, :], -300, 300)
    small = noise((512, 512), 3, seed); big = noise((512, 512), 24, seed + 1)
    mir = lambda q: 511 - np.abs(np.floor(q).astype(np.int64) % 1022 - 511)
    return 0.6 * small[mir(Z * 12), mir(X * 12)] + 0.8 * big[mir(Z * 2 + 50), mir(X * 2 + 50)]


class Writer:
    def __init__(self, path):
        self.path = path; self.p = None; self.cv = None
        if shutil.which("ffmpeg"):
            self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
                                       "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
        else:
            self.cv = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))

    def write(self, img):
        if self.p is not None:
            self.p.stdin.write(img.tobytes())
        else:
            self.cv.write(img)

    def close(self):
        if self.p is not None:
            self.p.stdin.close(); self.p.wait()
        else:
            self.cv.release()


# ---- drawing in the 360° picture -----------------------------------------------------------------------------------
def light_of(d, scene):
    """how bright something at distance d is (night: lamp / infrared falls off with the distance)"""
    if scene["night"]:
        return min(1.0, scene["ir"] * (5.0 / max(d, 1.0)) ** 2) + scene["amb"]
    return 1.0


def haze(col, d, scene):
    k = 1.0 - math.exp(-d / scene["vis"])
    return tuple(c * (1 - k) + h * k for c, h in zip(col, scene["haze_col"]))


def shade(col, d, scene, extra=1.0):
    L = light_of(d, scene) * extra
    return tuple(int(max(0, min(255, c))) for c in haze(tuple(c * L for c in col), d, scene))


def box(img, x, z, w, h, col, scene, y0=0.0, extra=1.0):
    """an upright box (tree trunk, car, wall) standing at world point x, z"""
    az, d = polar(x, z)
    half = math.degrees(math.atan2(w / 2.0, d))
    a, b = px(az - half), px(az + half)
    t, u = py(el_of(y0 + h, d)), py(el_of(y0, d))
    c = shade(col, d, scene, extra)
    cv2.rectangle(img, (int(a), int(t)), (int(math.ceil(b)), int(u)), c, -1, cv2.LINE_AA)
    return az, d, (a, t, b, u)


def figure(img, kind, x, z, phase, scene, heading=1, crouch=0.0, torch=False):
    """a person or an animal at x, z (m), walking (phase), heading +1 right / -1 left"""
    az, d = polar(x, z); cx = px(az)
    m = lambda hh: py(el_of(hh, d))                                 # height in metres -> picture row
    k = (H / 180.0) * math.degrees(1.0 / d)                         # pixels per metre at this distance
    lw = lambda mm: max(1, int(mm * k))
    sw = math.sin(phase)
    S = lambda col: shade(col, d, scene)
    yg = m(0.0)
    cv2.ellipse(img, (int(cx), int(yg)), (max(1, int(0.35 * k)), max(1, int(0.06 * k))), 0, 0, 360, S((20, 25, 22)), -1)
    if kind == "person":
        hh = 1.75 * (1 - 0.42 * crouch)
        hip, sh, hd = m(0.9 * hh / 1.75 * (1 - 0.1 * crouch)), m(hh * 0.8), m(hh * 0.92)
        jacket, trousers, skin = (50, 50, 60), (40, 40, 45), (140, 160, 200)
        for s_ in (1, -1):
            cv2.line(img, (int(cx), int(hip)), (int(cx + s_ * sw * 0.18 * k), int(yg)), S(trousers), lw(0.14), cv2.LINE_AA)
        cv2.line(img, (int(cx), int(hip)), (int(cx), int(sh)), S(jacket), lw(0.36), cv2.LINE_AA)
        for s_ in (1, -1):
            cv2.line(img, (int(cx), int(sh)), (int(cx - s_ * sw * 0.15 * k + heading * crouch * 0.3 * k), int(hip + 0.1 * k)), S(jacket), lw(0.1), cv2.LINE_AA)
        cv2.circle(img, (int(cx), int(hd)), lw(0.11), S(skin), -1, cv2.LINE_AA)
        if torch:                                                   # a small torch: bright point + light on the car
            p = (int(cx + heading * 0.35 * k), int(hip))
            cv2.circle(img, p, max(2, lw(0.05)), (230, 245, 255), -1, cv2.LINE_AA)
            g = np.zeros((H, W), np.float32); cv2.circle(g, (int(cx + heading * 0.9 * k), int(hip)), max(3, lw(0.5)), 1.0, -1)
            g = cv2.GaussianBlur(g, (0, 0), max(1.0, 0.3 * k))
            img[:] = np.clip(img + g[..., None] * np.array([120, 140, 150], np.float32), 0, 255).astype(np.uint8)
        return
    spec = {"fox": (0.45, 0.8, (40, 95, 200)), "deer": (1.15, 1.3, (60, 100, 145)), "boar": (0.85, 1.25, (45, 48, 55)),
            "dog": (0.6, 0.85, (60, 75, 95)), "cat": (0.28, 0.5, (80, 85, 90))}[kind]
    hh, L, col = spec
    body_y = m(hh * 0.62); half = L * k / 2
    for i, s_ in enumerate((0.35, -0.35, 0.3, -0.4)):
        ph = sw if i % 2 == 0 else -sw
        x0 = cx + s_ * L * k
        cv2.line(img, (int(x0), int(body_y)), (int(x0 + ph * 0.15 * k * heading), int(yg)), S(tuple(c * 0.8 for c in col)), lw(0.06), cv2.LINE_AA)
    cv2.ellipse(img, (int(cx), int(body_y)), (max(2, int(half)), max(1, int(hh * 0.22 * k))), 0, 0, 360, S(col), -1, cv2.LINE_AA)
    hx = cx + heading * half * 1.05
    if kind == "deer":
        hy = m(hh * 1.08); cv2.line(img, (int(cx + heading * half * 0.7), int(body_y)), (int(hx), int(hy)), S(col), lw(0.12), cv2.LINE_AA)
    else:
        hy = m(hh * 0.72)
    cv2.circle(img, (int(hx), int(hy)), max(2, lw(0.12 if kind != "boar" else 0.18)), S(col), -1, cv2.LINE_AA)
    if kind == "fox":
        tail = (int(cx - heading * half * 1.9), int(m(hh * 0.45)))
        cv2.line(img, (int(cx - heading * half), int(body_y)), tail, S(col), lw(0.13), cv2.LINE_AA)
        cv2.circle(img, tail, lw(0.06), S((220, 225, 230)), -1, cv2.LINE_AA)
    if scene["night"]:                                              # eyes shine in the infrared light
        e = min(1.0, scene["ir"] * (6.0 / d) ** 2) * 255
        if e > 30:
            cv2.circle(img, (int(hx + heading * lw(0.05)), int(hy - lw(0.03))), max(1, lw(0.025)), (e, e, e), -1, cv2.LINE_AA)


def mover(t, t0, t1, p0, p1):
    """position on the way p0 -> p1 between t0 and t1 (None outside)"""
    if not (t0 <= t <= t1):
        return None
    f = (t - t0) / (t1 - t0)
    return p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f, (1 if p1[0] >= p0[0] else -1)


# ---- the scenes ------------------------------------------------------------------------------------------------------
def background(scene, statics):
    """the parts that do not move, drawn once (sky, ground, trees, cars, ...) - far ones first"""
    img = np.zeros((H, W, 3), np.float32)
    el = (90.0 - (np.arange(H) + 0.5) / H * 180.0)[:, None]
    sky0, sky1 = np.array(scene["sky_top"], np.float32), np.array(scene["sky_hor"], np.float32)
    f = np.clip(el[:HZ] / 60.0, 0, 1)[..., None]
    img[:HZ] = sky1 * (1 - f) + sky0 * f
    if scene.get("stars"):
        rng = np.random.default_rng(4)
        for _ in range(700):
            img[rng.integers(0, int(HZ * 0.85)), rng.integers(0, W)] = rng.uniform(90, 200)
    d = ground_dist()[HZ:, None]
    gn = ground_tex(scene["seed"])
    base = np.array(scene["ground"], np.float32)
    g = base[None, None] * (1 + scene.get("tex", 0.18) * gn[..., None])
    if scene["night"]:
        L = np.minimum(1.0, scene["ir"] * (5.0 / np.maximum(d, 1.0)) ** 2) + scene["amb"]
    else:
        L = np.ones_like(d)
    g = g * L[..., None]
    k = (1 - np.exp(-d / scene["vis"]))[..., None]
    img[HZ:] = g * (1 - k) + np.array(scene["haze_col"], np.float32) * k
    img = np.clip(img, 0, 255).astype(np.uint8)
    for _d, fn in sorted(statics, key=lambda s_: -s_[0]):
        fn(img)
    return img


def scene_forest():
    sc = dict(name="Wald in der Nacht (Infrarot)", file="wald_nacht", night=True, ir=1.6, amb=0.04, vis=60.0, haze_col=(10, 10, 10),
              sky_top=(6, 6, 6), sky_hor=(14, 14, 14), ground=(75, 75, 75), seed=11, stars=False, gray=True, hour=23, ambient=8, tex=0.25)
    rng = np.random.default_rng(3); statics = []
    for _ in range(170):
        a = rng.uniform(-180, 180); dd = rng.uniform(4.5, 45)
        if abs(a) < 50 and dd < 7:
            continue                                                # an opening in front of the camera
        x, z = dd * math.sin(math.radians(a)), dd * math.cos(math.radians(a)); w = rng.uniform(0.18, 0.5); c = rng.uniform(80, 120)
        statics.append((dd, lambda img, x=x, z=z, w=w, c=c: box(img, x, z, w, 9.0, (c, c, c), sc)))
        if rng.random() < 0.5:                                      # bushes
            bx, bz = x + rng.uniform(-1.5, 1.5), z + rng.uniform(-1.5, 1.5); bs = rng.uniform(0.6, 1.4)

            def bush(img, x=bx, z=bz, c=c, bs=bs):
                az, d = polar(x, z); k = (H / 180.0) * math.degrees(1.0 / d)
                cv2.ellipse(img, (int(px(az)), int(py(el_of(0.35 * bs, d)))), (max(2, int(0.9 * bs * k)), max(2, int(0.45 * bs * k))),
                            0, 0, 360, shade((c * 0.75,) * 3, d, sc), -1, cv2.LINE_AA)
            statics.append((math.hypot(bx, bz), bush))

    def actors(img, t):
        p = mover(t, 2, 16, (-9, 8), (9, 7))                       # fox crosses
        if p:
            figure(img, "fox", p[0], p[1], t * 9, sc, p[2])
        for dx, t0 in ((0, 14), (1.6, 15.5)):                      # two deer, slowly
            p = mover(t, t0, t0 + 18, (12 + dx, 15), (-12 + dx, 13))
            if p:
                figure(img, "deer", p[0], p[1], t * 5, sc, p[2])
        p = mover(t, 26, 39, (-7, 6), (6, 10))                     # wild boar
        if p:
            figure(img, "boar", p[0], p[1], t * 7, sc, p[2])
    return sc, statics, actors, {"night": True, "hour": 23, "ambient": 8}


def scene_carpark():
    sc = dict(name="Parkplatz in der Nacht", file="parkplatz_nacht", night=True, ir=0.0, amb=0.22, vis=400.0, haze_col=(20, 22, 26),
              sky_top=(25, 15, 10), sky_hor=(45, 40, 45), ground=(95, 95, 98), seed=21, stars=True, gray=False, hour=1, ambient=11, tex=0.12)
    lamps = [(-8, 10), (6, 12), (0, 22), (-14, -4), (12, -6)]       # street lamps (x, z)
    statics = []

    def lit(x, z):                                                  # light of the lamps at a ground point
        return sum(2.5 / (1 + ((x - lx) ** 2 + (z - lz) ** 2) / 30.0) for lx, lz in lamps)
    sc["lit"] = lit
    cars = []
    rng = np.random.default_rng(5)
    cols = [(40, 40, 160), (150, 150, 155), (30, 30, 30), (140, 90, 40), (200, 200, 205), (40, 110, 60)]
    for i, a in enumerate(range(-80, 81, 20)):                      # a row of cars in front
        dd = 9.0; x, z = dd * math.sin(math.radians(a)), dd * math.cos(math.radians(a))
        cars.append((x, z, cols[i % len(cols)]))
    for i, a in enumerate(range(110, 260, 25)):                     # and behind
        dd = 12.0; x, z = dd * math.sin(math.radians(a)), dd * math.cos(math.radians(a))
        cars.append((x, z, cols[(i + 2) % len(cols)]))
    sc["cars"] = cars
    for x, z, c in cars:
        def car(img, x=x, z=z, c=c):
            L = 0.6 + 0.8 * lit(x, z)
            box(img, x, z, 2.0, 0.9, c, sc, 0.25, L)                # body
            box(img, x, z, 1.4, 0.55, tuple(v * 0.6 for v in c), sc, 1.15, L)   # roof / windows
            for dx in (-0.65, 0.65):
                box(img, x + dx, z, 0.45, 0.45, (25, 25, 25), sc, 0.0, L)
        statics.append((math.hypot(x, z), car))
    for lx, lz in lamps:
        def lamp(img, lx=lx, lz=lz):
            box(img, lx, lz, 0.15, 5.0, (90, 90, 95), sc, 0.0, 1.0 + lit(lx, lz))
            az, d = polar(lx, lz); p = (int(px(az)), int(py(el_of(5.0, d))))
            g = np.zeros((H, W), np.float32); cv2.circle(g, p, max(3, int(40 / d)), 1.0, -1)
            g = cv2.GaussianBlur(g, (0, 0), max(2.0, 60 / d))
            img[:] = np.clip(img + g[..., None] * np.array([120, 210, 255], np.float32) * 2.0, 0, 255).astype(np.uint8)
            cv2.circle(img, p, max(2, int(18 / d)), (200, 245, 255), -1, cv2.LINE_AA)
        statics.append((math.hypot(lx, lz) - 0.1, lamp))
    for a in range(-180, 180, 4):                                   # building wall far away with a few windows
        x, z = 40 * math.sin(math.radians(a)), 40 * math.cos(math.radians(a))

        def wall(img, x=x, z=z, a=a):
            box(img, x, z, 3.0, 9.0, (70, 72, 80), sc, 0.0, 1.0)
            if a % 12 == 0:
                box(img, x, z, 1.0, 1.2, (60, 170, 220), sc, 4.0, 4.0)
        statics.append((40, wall))

    def ground_light(img):                                          # light pools of the lamps on the asphalt
        d = ground_dist()[HZ:]
        az = (np.arange(W) + 0.5) / W * 360.0 - 180.0
        X = d[:, None] * np.sin(np.radians(az))[None, :]; Z = d[:, None] * np.cos(np.radians(az))[None, :]
        L = np.zeros_like(X)
        for lx, lz in lamps:
            L += 2.5 / (1 + ((X - lx) ** 2 + (Z - lz) ** 2) / 30.0)
        part = img[HZ:].astype(np.float32)
        img[HZ:] = np.clip(part * (0.6 + L[..., None] * 1.6) + L[..., None] * np.array([6, 12, 18], np.float32), 0, 255).astype(np.uint8)
        for a in range(-80, 81, 20):                                # parking lines
            for side in (-1, 1):
                a2 = a + side * 10
                p0 = polar(7.5 * math.sin(math.radians(a2)), 7.5 * math.cos(math.radians(a2)))
                p1 = polar(10.5 * math.sin(math.radians(a2)), 10.5 * math.cos(math.radians(a2)))
                cv2.line(img, (int(px(p0[0])), int(py(el_of(0, p0[1])))), (int(px(p1[0])), int(py(el_of(0, p1[1])))), (150, 150, 150), 2, cv2.LINE_AA)
    statics.append((5000, ground_light))

    def person_light(x, z):
        return min(1.2, 0.15 + 0.35 * lit(x, z))

    def actors(img, t):
        sc_l = dict(sc)
        p = mover(t, 0, 11, (-15, 5), (15, 6))                     # an ordinary passer-by
        if p:
            sc_l["amb"] = person_light(p[0], p[1]); figure(img, "person", p[0], p[1], t * 6, sc_l, p[2])
        # the thief: comes in, goes to a car, crouches and tries the door with a torch, the next car, runs away
        path = [(12, (-14, 3.5)), (17, (-3.6, 7.3)), (24, (-3.6, 7.3)), (26, (1.2, 7.4)), (31, (1.2, 7.4)), (34, (16, 2))]
        for (t0, a), (t1, b) in zip(path, path[1:]):
            p = mover(t, t0, t1, a, b)
            if p:
                still = a == b; fast = t0 >= 31
                cr = 1.0 if still and 18 <= t <= 23.5 or still and 27 <= t <= 30.5 else 0.0
                sc_l["amb"] = person_light(p[0], p[1])
                figure(img, "person", p[0], p[1], t * (12 if fast else 6) if not still else 0, sc_l,
                       1 if t < 24 else (1 if t < 31 else 1), crouch=cr, torch=still and cr > 0 and int(t * 3) % 4 != 0)
                break
    return sc, statics, actors, {"night": True, "hour": 1, "ambient": 11,
                                 "events": [{"t": 20.0, "sensor": "Auto: Erschütterung", "kind": "vibration"},
                                            {"t": 28.0, "sensor": "Auto: Erschütterung", "kind": "vibration"}]}


def scene_camping():
    sc = dict(name="Camping am nebligen Morgen", file="camping_morgen", night=False, ir=0.0, amb=0.0, vis=70.0, haze_col=(205, 205, 200),
              sky_top=(215, 205, 195), sky_hor=(222, 220, 214), ground=(70, 130, 85), seed=31, stars=False, gray=False, hour=7, ambient=9, tex=0.2)
    statics = []
    rng = np.random.default_rng(8)
    for _ in range(60):
        a = rng.uniform(-180, 180); dd = rng.uniform(18, 60)
        x, z = dd * math.sin(math.radians(a)), dd * math.cos(math.radians(a)); s_ = rng.uniform(0.8, 1.3)

        def tree(img, x=x, z=z, s_=s_):
            box(img, x, z, 0.35 * s_, 3.0 * s_, (40, 60, 85), sc)
            az, d = polar(x, z); r = int((H / 180.0) * math.degrees(2.2 * s_ / d))
            cv2.circle(img, (int(px(az)), int(py(el_of(4.6 * s_, d)))), max(2, r), shade((45, 100, 55), d, sc), -1, cv2.LINE_AA)
        statics.append((dd, tree))

    def tent(img):                                                  # orange tent at 7 m, 15° right
        az, d = polar(7 * math.sin(math.radians(15)), 7 * math.cos(math.radians(15)))
        half = math.degrees(math.atan2(1.4, d))
        pts = np.array([(px(az - half), py(el_of(0, d))), (px(az), py(el_of(1.6, d))), (px(az + half), py(el_of(0, d)))], np.int32)
        cv2.fillPoly(img, [pts], shade((40, 125, 225), d, sc), cv2.LINE_AA)
    statics.append((7, tent))

    def caravan(img):
        x, z = 9 * math.sin(math.radians(-30)), 9 * math.cos(math.radians(-30))
        box(img, x, z, 5.5, 2.3, (215, 218, 222), sc, 0.3)
        box(img, x - 1.2, z - 0.05, 1.3, 0.7, (110, 85, 60), sc, 1.3)
        box(img, x + 1.6, z - 0.05, 0.8, 1.9, (85, 85, 95), sc, 0.4)
    statics.append((9, caravan))

    def actors(img, t):
        p = mover(t, 0, 40, (-14, 18), (10, 16))                   # a deer grazing, very slowly
        if p:
            figure(img, "deer", p[0], p[1], t * 2.5, sc, p[2])
        p = mover(t, 6, 22, (14, 5), (-14, 7))                     # a person with a dog
        if p:
            figure(img, "person", p[0], p[1], t * 6, sc, p[2])
            figure(img, "dog", p[0] - 1.2 * p[2], p[1] - 0.4, t * 9, sc, p[2])
        p = mover(t, 25, 37, (-5, 4), (4, 4.5))                    # a cat close to the camera
        if p:
            figure(img, "cat", p[0], p[1], t * 8, sc, p[2])
    return sc, statics, actors, {"night": False, "hour": 7, "ambient": 9}


SCENES = (scene_forest, scene_carpark, scene_camping)


def make(scene_fn, folder, seconds=40, progress=print):
    sc, statics, actors, meta = scene_fn()
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, sc["file"] + ".mp4")
    bg = background(sc, statics)
    w = Writer(path + ".part.mp4"); n = int(seconds * FPS); t_start = time.time()
    for i in range(n):
        t = i / FPS
        img = bg.copy()
        actors(img, t)
        # (no picture noise here: the simulator adds the noise of its camera itself, and the files stay small)
        if sc["gray"]:
            img = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        w.write(img)
        if i % FPS == 0:
            progress(f"Beispiel-Szene «{sc['name']}»: {int(100 * i / n)} %")
    w.close()
    os.replace(path + ".part.mp4", path)
    meta = dict(meta, name=sc["name"])
    with open(os.path.join(folder, sc["file"] + ".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    progress(f"Beispiel-Szene «{sc['name']}» fertig ({time.time() - t_start:.0f} s)")
    return path


def make_all(folder, progress=print):
    out = []
    for i, fn in enumerate(SCENES):
        out.append(make(fn, folder, progress=lambda m, i=i: progress(f"[{i + 1}/{len(SCENES)}] {m}")))
    progress(f"Beispiel-Videoszenen fertig: {len(out)} Videos im Video-Ordner")
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    make_all(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "sim_assets", "videos"))
