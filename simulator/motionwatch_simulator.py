#!/usr/bin/env python3
"""
Motion Watch – camping simulator 2  (separate program, protocol: motionwatch_sim_interface.py in the same folder)

Tests Motion Watch without hardware - as real as a small Python program can be:
  * real 3D view: the cameras look into a 360° world (a drawn camping place, or YOUR OWN 360° photo / phone panorama),
    camera 0 turns with the servos of Motion Watch, camera 1 is fixed on the caravan, thermal camera next to camera 0,
  * time of day with its own clock (set the hour, let time run faster), sun, dusk, stars, moon,
  * weather: clear, rain, fog, snow; wind moves the trees; temperature, humidity, air pressure ("storm comes"),
  * visitors walk on the ground in real distances: person, fox, wild boar, deer, cat - or your own cut-out photos (PNG),
    animals flee from the siren or the white light at night,
  * false-alarm makers: car headlights, insects in the infrared light, branches in the wind,
  * camera effects: auto exposure, noise at night, vignetting, motion blur while the head turns, dew / spider web on the
    lens (lens check), covered camera (sabotage alarm),
  * sensors: caravan door, PIR at the tent, gas, bike tag; a ready-made night test that runs by itself.

Start:   python3 motionwatch_simulator.py                 (window with the controls)
         python3 motionwatch_simulator.py --pano my_360_photo.jpg
         python3 motionwatch_simulator.py --no-window --port 8765
Own pictures: put a 360° photo (equirectangular, 2:1, e.g. from a 360 camera or the phone panorama) and / or cut-out
PNG pictures with transparency into the folder "sim_assets" next to this file: sim_assets/pano.jpg, sim_assets/person/*.png,
sim_assets/fox/*.png, sim_assets/boar/*.png, sim_assets/deer/*.png, sim_assets/cat/*.png.
Needs: python3-numpy, python3-opencv; for the window python3-tk and python3-pil.imagetk.
"""
import argparse
import glob
import math
import os
import random
import threading
import time

import cv2
import numpy as np

from motionwatch_sim_interface import SimServer, SimInfo, CamInfo, SimReply, DEFAULT_PORT

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "sim_assets")
CAM_H = 1.6                                   # height of the cameras above the ground (m)
EQ_W, EQ_H = 4096, 2048                       # the drawn 360° world (equirectangular)
# kind: height (m), length (m), speed (m/s), body temperature, colour (BGR)
KINDS = {"person": (1.75, 0.45, 1.3, 34.0, (70, 70, 150)), "fox": (0.42, 0.75, 2.2, 37.5, (40, 105, 215)),
         "boar": (0.85, 1.3, 1.6, 38.0, (45, 50, 62)), "deer": (1.2, 1.3, 2.0, 38.5, (55, 100, 150)),
         "cat": (0.28, 0.5, 1.5, 38.0, (90, 90, 95))}
OBJECTS = {"caravan": (-28.0, 9.0), "tent": (14.0, 7.0), "bike": (32.0, 6.0), "road": (0.0, 28.0)}   # azimuth (deg), distance (m)


# ----------------------------------------------------------------------------------------------------------------------
# geometry: a camera looks along (yaw, pitch); world directions are (azimuth, elevation) in degrees
# ----------------------------------------------------------------------------------------------------------------------
class View:
    def __init__(self, W, H, fov_h, yaw, pitch):
        self.W, self.H = W, H
        self.f = (W / 2.0) / math.tan(math.radians(fov_h) / 2.0)
        self.yaw, self.pitch = math.radians(yaw), math.radians(pitch)
        cy, sy, cp, sp = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.pitch), math.sin(self.pitch)
        # camera -> world rotation (first pitch around x, then yaw around y)
        self.R = np.array([[cy, sy * sp, sy * cp], [0, cp, -sp], [-sy, cy * sp, cy * cp]], np.float64)

    def project(self, az, el):
        """World direction -> pixel (x, y) or None (behind the camera)."""
        a, e = math.radians(az), math.radians(el)
        d = np.array([math.cos(e) * math.sin(a), math.sin(e), math.cos(e) * math.cos(a)])
        c = self.R.T @ d
        if c[2] <= 0.05:
            return None
        return self.W / 2.0 + self.f * c[0] / c[2], self.H / 2.0 - self.f * c[1] / c[2]

    def ground(self, az, dist, height=0.0):
        """A point on the ground (or `height` m above it) at azimuth / distance -> pixel."""
        return self.project(az, math.degrees(math.atan2(height - CAM_H, dist)))


_MAPS = {}


def eq_maps(W, H, fov_h, yaw, pitch, pw, ph):
    """Lookup tables for cv2.remap: the part of a 360° picture this camera sees (cached per position)."""
    key = (W, H, round(fov_h, 1), round(yaw, 1), round(pitch, 1), pw, ph)
    m = _MAPS.get(key)
    if m is None:
        v = View(W, H, fov_h, yaw, pitch)
        u, w_ = np.meshgrid(np.arange(W, dtype=np.float64), np.arange(H, dtype=np.float64))
        rays = np.stack([(u - W / 2) / v.f, -(w_ - H / 2) / v.f, np.ones_like(u)], axis=-1)
        rays /= np.linalg.norm(rays, axis=-1, keepdims=True)
        d = rays @ v.R.T
        lon = np.arctan2(d[..., 0], d[..., 2]); lat = np.arcsin(np.clip(d[..., 1], -1, 1))
        mx = ((lon + math.pi) / (2 * math.pi) * pw).astype(np.float32) % pw
        my = ((math.pi / 2 - lat) / math.pi * ph).astype(np.float32)
        m = (mx, my)
        if len(_MAPS) > 60:
            _MAPS.clear()
        _MAPS[key] = m
    return m


# ----------------------------------------------------------------------------------------------------------------------
# visitors
# ----------------------------------------------------------------------------------------------------------------------
class Walker:
    def __init__(self, kind, path=None):
        self.kind = kind
        self.z = random.uniform(5.0, 22.0) if path is None else path[0]          # distance of the walking line (m)
        self.dir = random.choice((-1, 1)) if path is None else path[1]
        self.x = -self.dir * (self.z * 1.6 + 6)                                   # starts outside the view
        self.speed = KINDS[kind][2] * random.uniform(0.8, 1.2)
        self.fled = False; self.done = False; self.pir = False; self.phase = random.random() * 6
        self.sprite = None
        files = glob.glob(os.path.join(ASSETS, kind, "*.png"))
        if files:
            img = cv2.imread(random.choice(files), cv2.IMREAD_UNCHANGED)
            if img is not None and img.ndim == 3 and img.shape[2] == 4:
                self.sprite = img

    def step(self, dt, scare):
        if scare and not self.fled and self.kind != "person":
            self.dir = -self.dir; self.speed *= 2.5; self.fled = True             # deterrence works: it runs away
        self.x += self.dir * self.speed * dt; self.phase += dt * self.speed * 3
        if abs(self.x) > self.z * 2.0 + 12:
            self.done = True

    def az_dist(self):
        return math.degrees(math.atan2(self.x, self.z)), math.hypot(self.x, self.z)


# ----------------------------------------------------------------------------------------------------------------------
# the simulator
# ----------------------------------------------------------------------------------------------------------------------
class CampingSim(SimServer):
    def __init__(self, port=DEFAULT_PORT, pano=None):
        info = SimInfo(name="Motion Watch camping simulator 2",
                       cameras=[CamInfo(0, "Head camera (NoIR)", 1280, 720, 12.0, 66.0, 41.0, True, True),
                                CamInfo(1, "Caravan camera", 960, 540, 8.0, 100.0, 62.0, False, False)],
                       thermal={"w": 80, "h": 62, "fps": 8.0, "fov_h": 45.0, "fov_v": 35.0, "unit": "C", "on_head": True},
                       sensors=[{"name": "Wohnwagen-Tür", "kind": "door"}, {"name": "PIR Zelt", "kind": "pir"},
                                {"name": "Gas Wohnwagen", "kind": "gas"}, {"name": "Velo", "kind": "tag"}])
        super().__init__(info, port=port)
        # world settings (the window changes them)
        self.clock0 = time.time(); self.hour0 = time.localtime().tm_hour + time.localtime().tm_min / 60.0; self.speed = 1.0
        self.moon = 0.5; self.weather = "clear"; self.wind = 8.0; self.ambient = 14.0; self.humidity = 70.0; self.pressure = 1013.0
        self.storm_t = 0.0
        self.auto_walkers = True; self.insects = 0.6; self.dew = 0.0; self.web = False; self.covered = False
        self.noise = 1.0; self.osd = True; self.cam1_yaw = -12.0
        self.walkers = []; self.cars = []; self.door_open = False
        self.wlock = threading.Lock(); self.last = time.time(); self.next_auto = time.time() + 20
        self.exposure = {0: 1.0, 1: 1.0}; self._vig = {}; self._webimg = {}; self._bugs = []
        self.pano_file = pano or (os.path.join(ASSETS, "pano.jpg") if os.path.isfile(os.path.join(ASSETS, "pano.jpg")) else None)
        self._photo = None; self._drawn = None
        self.trees = [(random.uniform(-150, 150), random.uniform(16, 45), random.uniform(0.8, 1.3)) for _ in range(28)]
        self.trees.sort(key=lambda t: -t[1])
        self.stones = [(random.uniform(-60, 60), random.uniform(4, 15)) for _ in range(6)]      # warm in the sun (thermal test)
        threading.Thread(target=self._life, daemon=True).start()

    # ---- time and light ---------------------------------------------------------------------------------------------
    def hour(self, t=None):
        t = time.time() if t is None else t
        return (self.hour0 + (t - self.clock0) * self.speed / 3600.0) % 24.0

    def set_hour(self, h):
        self.hour0 = float(h) % 24.0; self.clock0 = time.time()

    def sun(self, t=None):
        """Brightness of the daylight 0..1 (sunrise ~6:30, sunset ~19:30)."""
        h = self.hour(t)
        s = math.sin((h - 6.5) / 13.0 * math.pi)
        return float(np.clip(s * 1.8, 0.0, 1.0))

    def light_level(self, t=None):
        lv = 0.04 + 0.03 * self.moon + 0.93 * self.sun(t)
        if self.weather in ("rain", "fog", "snow"):
            lv *= 0.7 if self.weather != "snow" else 0.85
        return lv

    def sim_epoch(self, t):
        lt = time.localtime(t); base = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))
        return base + self.hour(t) * 3600.0

    def world(self, t):
        press = self.pressure
        if self.storm_t:                                            # "storm comes": 6 hPa less within 3 minutes
            press -= min(6.0, (t - self.storm_t) / 180.0 * 6.0)
        return SimReply(sim_time=self.sim_epoch(t), dark=self.light_level(t) < 0.3, ambient_c=round(self.ambient, 1),
                        pressure_hpa=round(press, 1), wind_kmh=round(self.wind, 1), weather=self.weather, humidity=round(self.humidity),
                        last_event=self.events[-1].id if self.events else 0)

    # ---- life ---------------------------------------------------------------------------------------------------------
    def spawn(self, kind, path=None):
        with self.wlock:
            self.walkers.append(Walker(kind, path))

    def car(self):
        with self.wlock:
            self.cars.append({"x": -60.0, "dir": 1, "speed": random.uniform(8, 14)})

    def _life(self):
        while True:
            now = time.time(); dt = min(0.2, now - self.last); self.last = now
            st = self.state
            scare = bool(st.sound) or (st.lights.white and self.light_level(now) < 0.3)
            with self.wlock:
                for w in self.walkers:
                    w.step(dt, scare)
                    az, d = w.az_dist()
                    if w.kind == "person" and not w.pir and abs(az - OBJECTS["tent"][0]) < 6 and d < 12:
                        w.pir = True; self.add_event("PIR Zelt", "pir", None)
                self.walkers = [w for w in self.walkers if not w.done]
                for c in self.cars:
                    c["x"] += c["dir"] * c["speed"] * dt
                self.cars = [c for c in self.cars if abs(c["x"]) < 80]
            if self.auto_walkers and now > self.next_auto:
                self.spawn(random.choice(("person", "fox", "fox", "boar", "deer", "cat")))
                self.next_auto = now + random.uniform(40, 120)
            time.sleep(0.05)

    def night_test(self):
        """A ready-made night: 22:30, fox, wild boar, a car, a person at the tent, the caravan door, gas - one after the other."""
        def run():
            self.set_hour(22.5); self.auto_walkers = False; self.weather = "clear"
            steps = [(5, lambda: self.spawn("fox", (8.0, 1))), (25, lambda: self.spawn("boar", (12.0, -1))), (45, self.car),
                     (60, lambda: self.spawn("person", (7.0, 1))), (80, lambda: self.door(True)), (90, lambda: self.door(False)),
                     (100, lambda: self.add_event("Velo", "tag", None)), (110, lambda: self.gas(True)), (120, lambda: self.gas(False))]
            t0 = time.time()
            for at, fn in steps:
                time.sleep(max(0.0, t0 + at - time.time())); fn()
        threading.Thread(target=run, daemon=True).start()

    def door(self, open_):
        self.door_open = bool(open_); self.add_event("Wohnwagen-Tür", "door", self.door_open)

    def gas(self, on):
        self.add_event("Gas Wohnwagen", "gas", bool(on))

    # ---- the drawn 360° world -------------------------------------------------------------------------------------
    def _drawn_world(self):
        if self._drawn is not None:
            return self._drawn
        W, H = EQ_W, EQ_H; hz = H // 2
        p = np.zeros((H, W, 3), np.uint8)
        y = np.arange(hz, dtype=np.float32)[:, None] / hz
        p[:hz] = np.stack([235 - 70 * (1 - y), 205 - 60 * (1 - y), 160 - 60 * (1 - y)], -1).astype(np.uint8).repeat(W, 1)
        rng = np.random.default_rng(5)
        xs = np.arange(W)
        ridge = hz - (90 + 60 * np.sin(xs / W * 2 * math.pi * 3 + 1) + 40 * np.sin(xs / W * 2 * math.pi * 7) + rng.normal(0, 3, W).cumsum() * 0.3)
        ridge = np.clip(ridge, hz - 260, hz - 10).astype(int)
        for x in range(W):
            p[ridge[x]:hz, x] = (118, 116, 112)
            p[ridge[x]:ridge[x] + 12, x] = (235, 235, 240) if ridge[x] < hz - 190 else (118, 116, 112)       # snow on the peaks
        g = rng.normal(0, 1, (H - hz, W)).astype(np.float32)
        g = cv2.GaussianBlur(g, (0, 0), 3) * 18
        base = np.array([62, 128, 72], np.float32)
        p[hz:] = np.clip(base + g[..., None] * np.array([0.6, 1.0, 0.6]), 0, 255).astype(np.uint8)
        self._drawn = p
        return p

    def _photo_world(self):
        if self._photo is None and self.pano_file and os.path.isfile(self.pano_file):
            img = cv2.imread(self.pano_file)
            if img is not None:
                if img.shape[1] != img.shape[0] * 2:                        # a phone panorama: put it into a 360° frame
                    w = img.shape[1]; h2 = w // 2; can = np.zeros((h2, w, 3), np.uint8); can[:] = (150, 150, 150)
                    y0 = max(0, h2 // 2 - img.shape[0] // 2); can[y0:y0 + min(img.shape[0], h2)] = img[:h2]
                    img = can
                self._photo = cv2.resize(img, (min(6000, img.shape[1]), min(3000, img.shape[1] // 2)))
        return self._photo

    def load_pano(self, path):
        self.pano_file = path; self._photo = None; _MAPS.clear()

    # ---- drawing helpers --------------------------------------------------------------------------------------------
    @staticmethod
    def _poly(img, v, pts, col):
        q = [v.ground(az, d, h) for az, d, h in pts]
        if all(x is not None for x in q):
            cv2.fillPoly(img, [np.array(q, np.int32)], col, cv2.LINE_AA)
            return True
        return False

    def _drawables(self, v, t):
        """Everything standing on the ground as (distance, draw function) - drawn from far to near (correct overlap)."""
        out = [(OBJECTS["road"][1] + 2, lambda img: self._road(img, v))]
        for tr_ in self.trees:
            out.append((tr_[1], lambda img, tr_=tr_: self._tree(img, v, t, tr_)))
        for name in ("tent", "caravan", "bike"):
            out.append((OBJECTS[name][1], lambda img, n=name: getattr(self, "_" + n)(img, v)))
        for st_ in self.stones:
            out.append((st_[1], lambda img, st_=st_: self._stone(img, v, st_)))
        return out

    def _road(self, img, v):
        az, d = OBJECTS["road"]
        self._poly(img, v, [(-80, d, 0), (80, d, 0), (80, d + 3, 0), (-80, d + 3, 0)], (95, 130, 150))

    def _stone(self, img, v, st_):
        az, d = st_; c = v.ground(az, d, 0.1)
        if c:
            r = max(2, int(v.f * 0.25 / d)); cv2.ellipse(img, (int(c[0]), int(c[1])), (r, int(r * 0.6)), 0, 0, 360, (125, 125, 120), -1)

    def _tree(self, img, v, t, tr_):
        sway = self.wind / 60.0
        for az, d, s in (tr_,):                                            # a tree (moves with the wind)
            base = v.ground(az, d); top = v.ground(az, d, 5.5 * s)
            if base is None or top is None or not (-300 < base[0] < v.W + 300):
                continue
            hpx = base[1] - top[1]; r = max(2, int(hpx * 0.32))
            dx = int(sway * r * 0.5 * math.sin(t * (1.5 + s) + az))
            cv2.line(img, (int(base[0]), int(base[1])), (int(base[0]), int(base[1] - hpx * 0.45)), (40, 60, 90), max(1, r // 4))
            cv2.circle(img, (int(top[0]) + dx, int(top[1] + r * 0.9)), r, (38, 98, 44), -1, cv2.LINE_AA)
            cv2.circle(img, (int(top[0]) + dx - r // 3, int(top[1] + r * 0.6)), int(r * 0.6), (48, 118, 54), -1, cv2.LINE_AA)

    def _tent(self, img, v):
        az, d = OBJECTS["tent"]
        self._poly(img, v, [(az - 9, d, 0), (az, d, 1.6), (az + 9, d, 0)], (40, 130, 230))
        self._poly(img, v, [(az - 2, d - 0.1, 0), (az, d - 0.1, 1.1), (az + 2, d - 0.1, 0)], (25, 80, 150))

    def _caravan(self, img, v):
        az, d = OBJECTS["caravan"]
        self._poly(img, v, [(az - 14, d, 0.3), (az + 14, d, 0.3), (az + 14, d, 2.6), (az - 14, d, 2.6)], (215, 218, 222))
        self._poly(img, v, [(az - 11, d - 0.05, 1.3), (az - 4, d - 0.05, 1.3), (az - 4, d - 0.05, 2.0), (az - 11, d - 0.05, 2.0)], (110, 85, 60))
        door = [(az + 6, d - 0.05, 0.4), (az + 11, d - 0.05, 0.4), (az + 11, d - 0.05, 2.3), (az + 6, d - 0.05, 2.3)]
        self._poly(img, v, door, (25, 25, 25) if self.door_open else (80, 80, 92))
        if self.door_open:
            self._poly(img, v, [(az + 11, d - 0.05, 0.4), (az + 13.5, d - 1.0, 0.4), (az + 13.5, d - 1.0, 2.3), (az + 11, d - 0.05, 2.3)], (80, 80, 92))

    def _bike(self, img, v):
        az, d = OBJECTS["bike"]
        for k in (-1.2, 1.2):
            c = v.ground(az + k, d, 0.35)
            if c:
                r = max(2, int(v.f * 0.35 / d)); cv2.circle(img, (int(c[0]), int(c[1])), r, (30, 30, 30), max(1, r // 6), cv2.LINE_AA)

    def _walker(self, img, v, w, t):
        az, d = w.az_dist()
        foot = v.ground(az, d); top = v.ground(az, d, KINDS[w.kind][0])
        if foot is None or top is None:
            return
        hpx = max(2.0, foot[1] - top[1]); x, y = int(foot[0]), int(foot[1])
        if not (-hpx * 3 < x < v.W + hpx * 3):
            return
        cv2.ellipse(img, (x, y), (int(hpx * 0.35), max(1, int(hpx * 0.06))), 0, 0, 360, (30, 50, 30), -1, cv2.LINE_AA)   # shadow
        if w.sprite is not None:                                           # your own cut-out photo
            s = w.sprite if w.dir > 0 else cv2.flip(w.sprite, 1)
            k = hpx / s.shape[0]; sw, sh = max(1, int(s.shape[1] * k)), max(1, int(hpx))
            s = cv2.resize(s, (sw, sh), interpolation=cv2.INTER_AREA)
            x0, y0 = x - sw // 2, y - sh
            a0, a1 = max(0, -x0), min(sw, img.shape[1] - x0); b0, b1 = max(0, -y0), min(sh, img.shape[0] - y0)
            if a1 > a0 and b1 > b0:
                al = s[b0:b1, a0:a1, 3:4].astype(np.float32) / 255.0
                roi = img[y0 + b0:y0 + b1, x0 + a0:x0 + a1]
                roi[:] = (roi * (1 - al) + s[b0:b1, a0:a1, :3] * al).astype(np.uint8)
            return
        col = KINDS[w.kind][4]; L = KINDS[w.kind][1] / KINDS[w.kind][0] * hpx
        leg = math.sin(w.phase) * 0.15
        if w.kind == "person":
            th = max(2, int(hpx * 0.12))
            for k in (-1, 1):
                cv2.line(img, (x - k * th // 2, int(y - hpx * 0.48)), (int(x + k * leg * hpx), y), (45, 45, 60), max(2, th), cv2.LINE_AA)
            cv2.rectangle(img, (x - th, int(y - hpx * 0.82)), (x + th, int(y - hpx * 0.45)), col, -1)
            cv2.line(img, (x, int(y - hpx * 0.78)), (int(x - leg * hpx * 0.8), int(y - hpx * 0.5)), col, max(2, th // 2), cv2.LINE_AA)
            cv2.circle(img, (x, int(y - hpx * 0.9)), max(2, int(hpx * 0.07)), (140, 170, 210), -1, cv2.LINE_AA)
        else:
            bh = hpx * (0.45 if w.kind != "deer" else 0.35); by = int(y - hpx * (0.5 if w.kind != "deer" else 0.62))
            cv2.ellipse(img, (x, by), (max(2, int(L / 2)), max(1, int(bh / 2))), 0, 0, 360, col, -1, cv2.LINE_AA)
            hx = int(x + w.dir * L * 0.55); hr = max(2, int(bh * (0.42 if w.kind != "boar" else 0.55)))
            cv2.circle(img, (hx, int(by - bh * (0.25 if w.kind != "deer" else 1.1))), hr, col, -1, cv2.LINE_AA)
            if w.kind == "deer":
                cv2.line(img, (int(x + w.dir * L * 0.4), by), (hx, int(by - bh * 1.1)), col, max(2, hr), cv2.LINE_AA)
            for k in (-0.35, 0.35):
                cv2.line(img, (int(x + k * L), by), (int(x + k * L + leg * hpx * w.dir), y), col, max(1, int(hpx * 0.06)), cv2.LINE_AA)
            if w.kind in ("fox", "cat"):
                cv2.line(img, (int(x - w.dir * L / 2), by), (int(x - w.dir * L * 0.95), int(by + bh * 0.3)), col, max(2, int(bh * 0.35)), cv2.LINE_AA)

    @staticmethod
    def _car_pos(v, c):
        d = OBJECTS["road"][1] + 1.5; az = math.degrees(math.atan2(c["x"], d))
        p = v.ground(az, d, 0.7)
        if p is None:
            return None
        return int(p[0]), int(p[1]), max(2, int(v.f * 0.6 / d))

    def _car(self, img, v, c):
        q = self._car_pos(v, c)
        if q:
            x, y, r = q
            cv2.rectangle(img, (x - r * 2, y - r // 2), (x + r * 2, y + r // 2), (60, 60, 140), -1)
            cv2.rectangle(img, (x - r, y - r), (x + r, y - r // 2), (50, 50, 110), -1)

    def _headlights(self, img, v, c):
        """At night the headlights shine bright - a classic false alarm."""
        q = self._car_pos(v, c)
        if not q:
            return
        x, y, r = q; hx = x + int(c["dir"] * r * 2)
        glow = np.zeros_like(img); cv2.circle(glow, (hx, y), r * 3, (200, 225, 235), -1)
        img[:] = cv2.addWeighted(img, 1.0, cv2.GaussianBlur(glow, (0, 0), r + 1), 0.55, 0)
        cv2.circle(img, (hx, y), max(2, r // 3), (235, 250, 255), -1, cv2.LINE_AA)

    def _sky(self, img, v, t, lv):
        if lv < 0.25:                                                       # stars and the moon
            rng = np.random.default_rng(int(v.yaw * 100) & 0xffff)
            hz = v.ground(0, 1e6)
            hy = int(hz[1]) if hz else v.H // 2
            for _ in range(80):
                x, y = int(rng.integers(0, v.W)), int(rng.integers(0, max(1, hy)))
                if 0 <= y < v.H:
                    img[y, x] = (200, 200, 210)
            m = v.project(40, 30)
            if m and self.moon > 0.1:
                cv2.circle(img, (int(m[0]), int(m[1])), 9, (215, 225, 230), -1, cv2.LINE_AA)

    def _weather(self, img, t, dark):
        H, W = img.shape[:2]; rng = np.random.default_rng()
        if self.weather == "rain":
            ov = np.zeros_like(img)
            for _ in range(int(W * H / 2500)):
                x, y = int(rng.integers(0, W)), int(rng.integers(0, H)); L = int(rng.integers(8, 22))
                cv2.line(ov, (x, y), (x + L // 5, y + L), (200, 200, 200), 1)
            img[:] = cv2.addWeighted((img * 0.85).astype(np.uint8), 1.0, ov, 0.35 if not dark else 0.15, 0)
        elif self.weather == "fog":
            grey = np.full_like(img, 150 if not dark else 35)
            img[:] = cv2.addWeighted(img, 0.45, grey, 0.55, 0)
        elif self.weather == "snow":
            for _ in range(int(W * H / 3000)):
                x, y = int(rng.integers(0, W)), int(rng.integers(0, H)); cv2.circle(img, (x, y), int(rng.integers(1, 3)), (235, 235, 235), -1)

    def _lens(self, img, cam, dark, ir):
        H, W = img.shape[:2]
        if ir and dark and self.insects > 0 and cam == 0:                   # insects fly into the infrared light
            if len(self._bugs) < int(12 * self.insects):
                self._bugs.append([random.uniform(0, W), random.uniform(0, H), random.uniform(-30, 30), random.uniform(-30, 30)])
            for b in self._bugs:
                b[0] += b[2] + random.uniform(-8, 8); b[1] += b[3] + random.uniform(-8, 8)
                cv2.circle(img, (int(b[0]), int(b[1])), random.randint(3, 9), (230, 230, 230), -1, cv2.LINE_AA)
            self._bugs = [b for b in self._bugs if -50 < b[0] < W + 50 and -50 < b[1] < H + 50]
        if self.web and cam == 0:
            if (W, H) not in self._webimg:
                m = np.zeros((H, W), np.uint8); cx, cy = int(W * 0.18), int(H * 0.2)
                for a in range(0, 360, 30):
                    cv2.line(m, (cx, cy), (int(cx + 420 * math.cos(math.radians(a))), int(cy + 420 * math.sin(math.radians(a)))), 255, 1, cv2.LINE_AA)
                for r in range(30, 420, 38):
                    cv2.circle(m, (cx, cy), r, 255, 1, cv2.LINE_AA)
                self._webimg[(W, H)] = cv2.GaussianBlur(m, (0, 0), 1.2)
            m = self._webimg[(W, H)][..., None].astype(np.float32) / 255.0
            img[:] = np.clip(img * (1 - 0.5 * m) + 230 * 0.5 * m, 0, 255).astype(np.uint8)
            img[:] = cv2.addWeighted(img, 0.7, cv2.GaussianBlur(img, (0, 0), 6), 0.3, 0)
        if self.dew > 0 and cam == 0:                                      # dew: milky and blurred (lens check test)
            b = cv2.GaussianBlur(img, (0, 0), 2 + 14 * self.dew)
            img[:] = cv2.addWeighted(b, 1 - 0.35 * self.dew, np.full_like(img, 170 if not dark else 60), 0.35 * self.dew, 0)

    def _camera(self, img, cam, lv, moving):
        """Auto exposure, noise (more at night), vignetting, motion blur."""
        H, W = img.shape[:2]
        f = img.astype(np.float32)
        target = 110.0; mean = max(1.0, float(f[::16, ::16].mean()))
        want = float(np.clip(target / mean, 0.7, 6.0))
        self.exposure[cam] += (want - self.exposure[cam]) * 0.15
        g = self.exposure[cam]
        f *= g
        if (W, H) not in self._vig:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
            self._vig[(W, H)] = (1.0 - 0.28 * r ** 2.2)[..., None]
        f *= self._vig[(W, H)]
        f += np.random.default_rng().normal(0, self.noise * (1.5 + 3.5 * g), f.shape).astype(np.float32)
        out = np.clip(f, 0, 255).astype(np.uint8)
        if moving and cam == 0:
            out = cv2.blur(out, (15, 1))
        return out

    # ---- the interface ---------------------------------------------------------------------------------------------
    def render_camera(self, cam, st, t):
        info = self.info.cameras[cam]; W, H = info.w, info.h
        if self.covered and cam == 0:                                      # sabotage test: hand over the lens
            return np.clip(np.random.default_rng().normal(8, 3, (H, W, 3)), 0, 255).astype(np.uint8)
        if info.on_head:
            yaw, pitch = st.servo.pan_deg, st.servo.tilt_deg - 6.0
        else:
            yaw, pitch = self.cam1_yaw, -10.0
        v = View(W, H, info.fov_h, yaw, pitch)
        photo = self._photo_world()
        src = photo if photo is not None else self._drawn_world()
        mx, my = eq_maps(W, H, info.fov_h, yaw, pitch, src.shape[1], src.shape[0])
        img = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        lv = self.light_level(t); dark = lv < 0.3
        with self.wlock:
            ws = list(self.walkers); cars = list(self.cars)
        items = [(w.az_dist()[1], lambda im, w=w: self._walker(im, v, w, t)) for w in ws]
        items += [(OBJECTS["road"][1] + 1.5, lambda im, c=c: self._car(im, v, c)) for c in cars]
        if photo is None:
            self._sky(img, v, t, lv)
            items += self._drawables(v, t)
        for _d, fn in sorted(items, key=lambda x: -x[0]):
            fn(img)
        light = np.full((H, W), lv, np.float32)
        if dark:
            if st.lights.white and info.on_head:
                if (W, H, "cone") not in self._vig:
                    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                    self._vig[(W, H, "cone")] = np.exp(-(((xx - W / 2) / (W * 0.33)) ** 2 + ((yy - H * 0.62) / (H * 0.5)) ** 2))
                light += 0.75 * self._vig[(W, H, "cone")] * float(st.lights.white_level)
            if st.lights.ir and info.noir:
                light += 0.45 * float(st.lights.ir_level)
            if not info.on_head and self.door_open:
                light += 0.25
        img = (img.astype(np.float32) * np.minimum(light, 1.2)[..., None]).astype(np.uint8)
        for c in cars if dark else []:
            self._headlights(img, v, c)
        if info.noir and st.lights.ir and dark and not st.lights.white:
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
        self._weather(img, t, dark)
        self._lens(img, cam, dark, st.lights.ir)
        out = self._camera(img, cam, lv, st.servo.moving)
        if self.osd:
            txt = time.strftime("%d.%m.%Y ", time.localtime(t)) + "%02d:%02d" % (int(self.hour(t)), int(self.hour(t) % 1 * 60))
            txt += f"  SIM {cam}" + (f"  pan {st.servo.pan:.0f}% tilt {st.servo.tilt:.0f}%" if info.on_head else "") + (f"  [{st.sound}]" if st.sound else "")
            cv2.putText(out, txt, (11, H - 11), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(out, txt, (10, H - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1, cv2.LINE_AA)
        return out

    def render_thermal(self, st, t):
        th = self.info.thermal; w, h = th["w"], th["h"]
        v = View(w, h, th["fov_h"], st.servo.pan_deg, st.servo.tilt_deg - 6.0)
        amb = self.ambient - (2.0 if self.weather == "rain" else 0.0)
        a = np.full((h, w), amb, np.float32)
        hz = v.ground(0, 1e6)
        if hz:
            a[: max(0, min(h, int(hz[1])))] = amb - 12.0                    # the sky is cold
        sun = self.sun(t)
        for az, d in self.stones:                                          # stones warmed by the sun (they do not move)
            c = v.ground(az, d, 0.1)
            if c and sun > 0.2:
                cv2.circle(a, (int(c[0]), int(c[1])), max(1, int(v.f * 0.25 / d)), amb + 12 * sun, -1)
        with self.wlock:
            ws = list(self.walkers); cars = list(self.cars)
        for wk in ws:
            az, d = wk.az_dist(); foot = v.ground(az, d); top = v.ground(az, d, KINDS[wk.kind][0])
            if not foot or not top:
                continue
            hp = max(1.0, foot[1] - top[1]); temp = KINDS[wk.kind][3] - 3.0 - (2.0 if self.weather == "rain" else 0.0)
            if wk.kind == "person":
                cv2.ellipse(a, (int(foot[0]), int(foot[1] - hp * 0.5)), (max(1, int(hp * 0.12)), max(1, int(hp * 0.45))), 0, 0, 360, temp, -1)
                cv2.circle(a, (int(foot[0]), int(foot[1] - hp * 0.9)), max(1, int(hp * 0.08)), temp + 1.5, -1)
            else:
                L = KINDS[wk.kind][1] / KINDS[wk.kind][0] * hp
                cv2.ellipse(a, (int(foot[0]), int(foot[1] - hp * 0.5)), (max(1, int(L * 0.5)), max(1, int(hp * 0.25))), 0, 0, 360, temp, -1)
        for c in cars:
            d = OBJECTS["road"][1] + 1.5; p = v.ground(math.degrees(math.atan2(c["x"], d)), d, 0.5)
            if p:
                cv2.circle(a, (int(p[0] + c["dir"] * 2), int(p[1])), 2, amb + 60, -1)          # hot engine
        if st.lights.white:
            cv2.circle(a, (w // 2, 2), 2, amb + 30, -1)
        if self.weather == "fog":
            a = amb + (a - amb) * 0.6
        a = cv2.GaussianBlur(a, (0, 0), 0.7)
        return a + np.random.default_rng().normal(0, 0.12, a.shape).astype(np.float32)


# ----------------------------------------------------------------------------------------------------------------------
# the control window (no colour emoji: they can crash Tk on the Raspberry Pi)
# ----------------------------------------------------------------------------------------------------------------------
def window(sim):
    import tkinter as tk
    from tkinter import ttk, filedialog
    try:
        from PIL import Image, ImageTk
    except ImportError:
        Image = ImageTk = None
    BG, FG, MUT = "#161b22", "#c9d1d9", "#8b949e"
    root = tk.Tk(); root.title("Motion Watch – Simulator 2"); root.configure(bg=BG)
    sty = ttk.Style(); sty.theme_use("clam")
    left = tk.Frame(root, bg=BG); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
    right = tk.Frame(root, bg=BG); right.pack(side="right", fill="y", padx=8, pady=8)
    prev = [tk.Label(left, bg="#000") for _ in range(3)]
    prev[0].pack(fill="x"); row = tk.Frame(left, bg=BG); row.pack(fill="x", pady=(6, 0))
    prev[1] = tk.Label(row, bg="#000"); prev[1].pack(side="left"); prev[2] = tk.Label(row, bg="#000"); prev[2].pack(side="left", padx=(6, 0))
    status = tk.Label(left, text="", bg=BG, fg=FG, justify="left", anchor="w", font=("DejaVu Sans Mono", 9)); status.pack(fill="x", pady=(6, 0))
    nb = ttk.Notebook(right); nb.pack(fill="both", expand=True)

    def tab(name):
        f = tk.Frame(nb, bg=BG, padx=6, pady=6); nb.add(f, text=name); return f

    def lab(p, t_):
        tk.Label(p, text=t_, bg=BG, fg=MUT, font=("DejaVu Sans", 8, "bold"), anchor="w").pack(fill="x", pady=(8, 2))

    def slider(p, text, lo, hi, get, put, res=0.5):
        f = tk.Frame(p, bg=BG); f.pack(fill="x")
        tk.Label(f, text=text, bg=BG, fg=FG, width=16, anchor="w").pack(side="left")
        s = tk.Scale(f, from_=lo, to=hi, orient="horizontal", resolution=res, bg=BG, fg=FG, highlightthickness=0, length=170,
                     command=lambda v: put(float(v)))
        s.set(get()); s.pack(side="left"); return s

    def check(p, text, get, put):
        v = tk.BooleanVar(value=get()); ttk.Checkbutton(p, text=text, variable=v, command=lambda: put(v.get())).pack(anchor="w"); return v

    # -- scene
    t1 = tab("Szene")
    lab(t1, "UHRZEIT")
    hs = slider(t1, "Stunde", 0, 23.75, lambda: round(sim.hour(), 2), sim.set_hour, 0.25)
    bf = tk.Frame(t1, bg=BG); bf.pack(fill="x")
    for txt, h in (("Mittag", 12.5), ("Abend", 19.6), ("Nacht", 23.0), ("Morgen", 6.4)):
        ttk.Button(bf, text=txt, command=lambda h=h: (sim.set_hour(h), hs.set(h))).pack(side="left", expand=True, fill="x")
    slider(t1, "Zeit läuft x-fach", 1, 120, lambda: sim.speed, lambda v: (sim.set_hour(sim.hour()), setattr(sim, "speed", v)), 1)
    slider(t1, "Mond", 0, 1, lambda: sim.moon, lambda v: setattr(sim, "moon", v), 0.1)
    lab(t1, "BESUCH")
    g = tk.Frame(t1, bg=BG); g.pack(fill="x")
    for i, (k, l) in enumerate((("person", "Person"), ("fox", "Fuchs"), ("boar", "Wildschwein"), ("deer", "Reh"), ("cat", "Katze"))):
        ttk.Button(g, text=l, command=lambda k=k: sim.spawn(k)).grid(row=i // 3, column=i % 3, sticky="ew", padx=1, pady=1)
    ttk.Button(g, text="Auto (Scheinwerfer)", command=sim.car).grid(row=1, column=2, sticky="ew", padx=1, pady=1)
    for c in range(3):
        g.columnconfigure(c, weight=1)
    check(t1, "ab und zu Besuch von selbst", lambda: sim.auto_walkers, lambda v: setattr(sim, "auto_walkers", v))
    lab(t1, "EIGENES 360°-FOTO")

    def pick():
        p = filedialog.askopenfilename(title="360°-Foto oder Panorama", filetypes=[("Bilder", "*.jpg *.jpeg *.png")])
        if p:
            sim.load_pano(p)
    pf = tk.Frame(t1, bg=BG); pf.pack(fill="x")
    ttk.Button(pf, text="Foto laden …", command=pick).pack(side="left", expand=True, fill="x")
    ttk.Button(pf, text="gezeichnete Welt", command=lambda: sim.load_pano(None)).pack(side="left", expand=True, fill="x")
    slider(t1, "Kamera 1: Richtung", -90, 90, lambda: sim.cam1_yaw, lambda v: setattr(sim, "cam1_yaw", v), 1)
    # -- weather
    t2 = tab("Wetter")
    lab(t2, "WETTER")
    wv = tk.StringVar(value=sim.weather)
    for v_, l in (("clear", "klar"), ("rain", "Regen"), ("fog", "Nebel"), ("snow", "Schnee")):
        ttk.Radiobutton(t2, text=l, value=v_, variable=wv, command=lambda: setattr(sim, "weather", wv.get())).pack(anchor="w")
    slider(t2, "Wind km/h", 0, 120, lambda: sim.wind, lambda v: setattr(sim, "wind", v), 1)
    slider(t2, "Temperatur °C", -15, 40, lambda: sim.ambient, lambda v: setattr(sim, "ambient", v))
    slider(t2, "Feuchte %", 10, 100, lambda: sim.humidity, lambda v: setattr(sim, "humidity", v), 1)
    slider(t2, "Luftdruck hPa", 960, 1040, lambda: sim.pressure, lambda v: setattr(sim, "pressure", v))
    ttk.Button(t2, text="Sturm zieht auf (Luftdruck fällt)", command=lambda: setattr(sim, "storm_t", time.time())).pack(fill="x", pady=(6, 0))
    ttk.Button(t2, text="Sturm vorbei", command=lambda: setattr(sim, "storm_t", 0.0)).pack(fill="x")
    # -- camera / lens
    t3 = tab("Kamera")
    lab(t3, "LINSE (test für Linsen-Prüfung und Sabotage)")
    slider(t3, "Tau / beschlagen", 0, 1, lambda: sim.dew, lambda v: setattr(sim, "dew", v), 0.05)
    check(t3, "Spinnennetz vor der Linse", lambda: sim.web, lambda v: setattr(sim, "web", v))
    check(t3, "Kamera abgedeckt (Hand davor)", lambda: sim.covered, lambda v: setattr(sim, "covered", v))
    lab(t3, "FEHLALARM-MACHER")
    slider(t3, "Insekten im IR-Licht", 0, 1, lambda: sim.insects, lambda v: setattr(sim, "insects", v), 0.1)
    lab(t3, "BILD")
    slider(t3, "Bildrauschen", 0, 3, lambda: sim.noise, lambda v: setattr(sim, "noise", v), 0.1)
    check(t3, "Datum / Zeit im Bild", lambda: sim.osd, lambda v: setattr(sim, "osd", v))
    # -- sensors / test
    t4 = tab("Sensoren")
    dv = tk.BooleanVar(value=False)
    ttk.Checkbutton(t4, text="Wohnwagentür offen", variable=dv, command=lambda: sim.door(dv.get())).pack(anchor="w")
    gv = tk.BooleanVar(value=False)
    ttk.Checkbutton(t4, text="Gas / Rauch", variable=gv, command=lambda: sim.gas(gv.get())).pack(anchor="w")
    ttk.Button(t4, text="Velo bewegen", command=lambda: sim.add_event("Velo", "tag", None)).pack(fill="x", pady=1)
    ttk.Button(t4, text="PIR Zelt auslösen", command=lambda: sim.add_event("PIR Zelt", "pir", None)).pack(fill="x", pady=1)
    lab(t4, "TESTABLAUF")
    tk.Label(t4, text="Nacht 22:30: Fuchs, Wildschwein, Auto, Person beim Zelt,\nWohnwagentür, Velo, Gas - ca. 2 Minuten.", bg=BG, fg=FG,
             justify="left").pack(anchor="w")
    ttk.Button(t4, text="Nacht-Test starten", command=sim.night_test).pack(fill="x", pady=(4, 0))

    def tick():
        st = sim.state; age = time.time() - sim.state_t if sim.state_t else None; t = time.time()
        if Image is not None:
            for i, w_ in ((0, 640), (1, 316)):
                im = cv2.cvtColor(sim.render_camera(i, st, t), cv2.COLOR_BGR2RGB)
                im = cv2.resize(im, (w_, int(im.shape[0] * w_ / im.shape[1])))
                ph = ImageTk.PhotoImage(Image.fromarray(im)); prev[i].configure(image=ph); prev[i].image = ph
            th = sim.render_thermal(st, t); lo, hi = float(th.min()), float(th.max())
            g8 = np.clip((th - lo) / max(0.5, hi - lo) * 255, 0, 255).astype(np.uint8)
            im = cv2.cvtColor(cv2.applyColorMap(cv2.resize(g8, (232, 180), interpolation=cv2.INTER_NEAREST), cv2.COLORMAP_INFERNO), cv2.COLOR_BGR2RGB)
            ph = ImageTk.PhotoImage(Image.fromarray(im)); prev[2].configure(image=ph); prev[2].image = ph
        rl = ", ".join(f"{r.name}={'AN' if r.on else 'aus'}" for r in st.relays) or "-"
        wr = sim.world(t)
        status.configure(text=(f"Motion Watch: {'verbunden (' + st.device + ')' if age is not None and age < 3 else 'NICHT verbunden'}   Port {sim.port}\n"
                               f"Servos: Schwenk {st.servo.pan:.1f} % ({st.servo.pan_deg:+.0f}°)  Neigung {st.servo.tilt:.1f} % ({st.servo.tilt_deg:+.0f}°)\n"
                               f"Licht: weiss {'AN' if st.lights.white else 'aus'} · IR {'AN' if st.lights.ir else 'aus'}   Relais: {rl}\n"
                               f"Ton: {st.sound or '-'}   Scharf: {'ja' if st.armed else 'nein'}\n"
                               f"Welt: {int(sim.hour()):02d}:{int(sim.hour() % 1 * 60):02d} {'Nacht' if wr.dark else 'Tag'} · {sim.weather} · "
                               f"{wr.ambient_c} °C · {wr.pressure_hpa} hPa · Wind {wr.wind_kmh} km/h · Besucher {len(sim.walkers)}"))
        root.after(500, tick)
    tick()
    root.mainloop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Motion Watch camping simulator 2")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--no-window", action="store_true", help="without the control window")
    ap.add_argument("--pano", help="own 360° photo (equirectangular 2:1) or a panorama")
    ap.add_argument("--hour", type=float, help="start at this hour (e.g. 22.5)")
    ap.add_argument("--night", action="store_true"); ap.add_argument("--day", action="store_true")
    a = ap.parse_args()
    sim = CampingSim(a.port, a.pano)
    if a.hour is not None:
        sim.set_hour(a.hour)
    elif a.night:
        sim.set_hour(23.0)
    elif a.day:
        sim.set_hour(12.5)
    if a.no_window:
        sim.serve_forever()
    else:
        threading.Thread(target=sim.serve_forever, daemon=True).start()
        window(sim)
