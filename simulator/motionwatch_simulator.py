#!/usr/bin/env python3
"""
MW Sim · Basis – the camping simulator of Motion Watch (separate program, protocol: motionwatch_sim_interface.py in the same folder)

Tests Motion Watch without hardware:
  * real 3D: the cameras look into a 360° world with a depth for every pixel (a drawn camping place or YOUR OWN 360° photo);
    camera 0 turns with the servos of Motion Watch, camera 1 is fixed on the caravan, the thermal camera sits next to camera 0,
  * ground with perspective texture, clouds, sun and its glare, haze and fog that grow with the distance,
  * light that falls off with the distance: floodlight cone, infrared light (NoIR camera), headlights, the open caravan door,
  * time of day with its own clock, dusk, moon, stars; weather: clear, cloudy, rain, fog, snow; wind moves the trees,
  * visitors on the ground in real distances: people, fox, wild boar, deer, cat - or your own cut-out photos (PNG);
    animals flee from the siren or the white light at night,
  * false-alarm makers: car headlights, insects in the IR light, branches in the wind,
  * camera: auto exposure, noise and colour noise at night, vignetting, a little lens distortion, glare (bloom),
    motion blur while the head turns; dew / spider web / a hand on the lens,
  * thermal camera with physics: cold sky (clear sky much colder than a cloudy one), ground warm in the sun and cooling
    at night, warm walls in the evening, people with clothes (face warmer than the jacket), animals with fur, a hot engine,
  * sensors: caravan door, PIR at the tent, gas, bike tag; a ready-made night test,
  * keeps itself up to date: Motion Watch tells which version it carries, the simulator fetches it and restarts.

Start:   python3 motionwatch_simulator.py                 (window with the controls)
         python3 motionwatch_simulator.py --pano my_360_photo.jpg
         python3 motionwatch_simulator.py --no-window --port 8765        (--no-update: never update itself)
Own pictures in the folder "sim_assets" next to this file: pano.jpg (360° photo, 2:1), person/*.png, fox/*.png, boar/*.png,
deer/*.png, cat/*.png (cut-out photos with a transparent background).
Needs: python3-numpy, python3-opencv; for the window python3-tk and python3-pil.imagetk.
"""
import argparse
import glob
import hashlib
import io
import math
import os
import random
import sys
import threading
import time
import urllib.request
import zipfile

import cv2
import numpy as np

from motionwatch_sim_interface import SimServer, SimInfo, CamInfo, SimReply, DEFAULT_PORT

SIM_VERSION = "3.7"
SIM_NAME = "MW Sim · Basis"          # the simulators are called MW Sim · Basis / 3D / Welt (3.7)
SIM_ICON = ('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'
            'gg==')   # 64 px PNG: the radar eye with the grey badge
HERE = os.path.dirname(os.path.abspath(__file__))


def _file_sha(n):
    try:
        with open(os.path.join(HERE, n), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return ""


RUN_SHA = {n: _file_sha(n) for n in ("motionwatch_simulator.py", "motionwatch_sim_interface.py", "motionwatch_demo_scenes.py")}   # what is running now
ASSETS = os.path.join(HERE, "sim_assets")
CAM_H = 1.6                                   # height of the cameras above the ground (m)
EQ_W, EQ_H = 3072, 1536                       # the drawn 360° world (equirectangular)
FAR = 5000.0                                  # "distance" of the sky
# kind: height (m), length (m), speed (m/s), skin / fur temperature, colours
KINDS = {"person": (1.75, 0.45, 1.3, 33.0), "fox": (0.42, 0.75, 2.2, 30.0), "boar": (0.85, 1.3, 1.6, 29.0),
         "deer": (1.2, 1.3, 2.0, 30.0), "cat": (0.28, 0.5, 1.5, 31.0)}
JACKETS = [(60, 60, 150), (130, 80, 40), (40, 110, 60), (150, 150, 150), (40, 40, 40), (30, 90, 180)]
OBJECTS = {"caravan": (-28.0, 9.0), "tent": (14.0, 7.0), "bike": (32.0, 6.0), "road": (0.0, 28.0)}   # azimuth (deg), distance (m)
VISIBILITY = {"clear": 6000.0, "cloudy": 4000.0, "rain": 500.0, "fog": 45.0, "snow": 250.0}


def fbm(shape, scales, seed):
    """Smooth random pattern (sum of blurred noise at several sizes), roughly -1..1."""
    rng = np.random.default_rng(seed); out = np.zeros(shape, np.float32); amp = 1.0; tot = 0.0
    for sc in scales:
        small = rng.normal(0, 1, (max(2, shape[0] // sc), max(2, shape[1] // sc))).astype(np.float32)
        out += cv2.resize(small, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp; amp *= 0.55
    return out / tot


# ----------------------------------------------------------------------------------------------------------------------
# geometry: a camera looks along (yaw, pitch); world directions are (azimuth, elevation) in degrees
# ----------------------------------------------------------------------------------------------------------------------
class View:
    K1 = -0.06                                 # a little barrel distortion like a real wide lens

    def __init__(self, W, H, fov_h, yaw, pitch):
        self.W, self.H = W, H
        self.f = (W / 2.0) / math.tan(math.radians(fov_h) / 2.0)
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(-pitch)), math.sin(math.radians(-pitch))     # pitch > 0 = looking up
        self.R = np.array([[cy, sy * sp, sy * cp], [0, cp, -sp], [-sy, cy * sp, cy * cp]], np.float64)

    def project(self, az, el):
        a, e = math.radians(az), math.radians(el)
        c = self.R.T @ np.array([math.cos(e) * math.sin(a), math.sin(e), math.cos(e) * math.cos(a)])
        if c[2] <= 0.05:
            return None
        x, y = c[0] / c[2], c[1] / c[2]
        r2 = min(3.0, (x * x + y * y) * (self.f / (self.W / 2)) ** 2)     # far outside the picture: no fold-back
        k = 1 + self.K1 * r2
        return self.W / 2.0 + self.f * x * k, self.H / 2.0 - self.f * y * k

    def ground(self, az, dist, height=0.0):
        return self.project(az, math.degrees(math.atan2(height - CAM_H, dist)))


_MAPS = {}


def eq_maps(W, H, fov_h, yaw, pitch, pw, ph):
    """Lookup tables for cv2.remap (with the lens distortion), cached per camera position."""
    key = (W, H, round(fov_h, 1), round(yaw, 1), round(pitch, 1), pw, ph)
    m = _MAPS.get(key)
    if m is None:
        v = View(W, H, fov_h, yaw, pitch)
        u, w_ = np.meshgrid(np.arange(W, dtype=np.float64), np.arange(H, dtype=np.float64))
        xd, yd = (u - W / 2) / v.f, -(w_ - H / 2) / v.f
        r2 = (xd * xd + yd * yd) * (v.f / (W / 2)) ** 2
        xu, yu = xd / (1 + View.K1 * r2), yd / (1 + View.K1 * r2)           # undo the distortion (good enough)
        rays = np.stack([xu, yu, np.ones_like(u)], axis=-1)
        rays /= np.linalg.norm(rays, axis=-1, keepdims=True)
        d = rays @ v.R.T
        lon = np.arctan2(d[..., 0], d[..., 2]); lat = np.arcsin(np.clip(d[..., 1], -1, 1))
        mx = ((lon + math.pi) / (2 * math.pi) * pw).astype(np.float32) % pw
        my = ((math.pi / 2 - lat) / math.pi * ph).astype(np.float32)
        # axis angle of every pixel (for the light cone)
        ang = np.degrees(np.arccos(np.clip(1.0 / np.sqrt(xu * xu + yu * yu + 1.0), -1, 1))).astype(np.float32)
        m = (mx, my, ang)
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
        self.x = -self.dir * (self.z * 1.6 + 6)
        self.speed = KINDS[kind][2] * random.uniform(0.8, 1.2)
        self.fled = False; self.done = False; self.pir = False; self.phase = random.random() * 6
        self.jacket = random.choice(JACKETS); self.trousers = random.choice(((50, 45, 40), (90, 60, 40), (40, 40, 60)))
        self.sprite = None
        files = glob.glob(os.path.join(ASSETS, kind, "*.png"))
        if files:
            img = cv2.imread(random.choice(files), cv2.IMREAD_UNCHANGED)
            if img is not None and img.ndim == 3 and img.shape[2] == 4:
                self.sprite = img

    def step(self, dt, scare):
        if scare and not self.fled and self.kind != "person":
            self.dir = -self.dir; self.speed *= 2.5; self.fled = True
        self.x += self.dir * self.speed * dt; self.phase += dt * self.speed * 3.2
        if abs(self.x) > self.z * 2.0 + 12:
            self.done = True

    def az_dist(self):
        return math.degrees(math.atan2(self.x, self.z)), math.hypot(self.x, self.z)



# ----------------------------------------------------------------------------------------------------------------------
# 360° video scenarios: a real filmed scene instead of the drawn world (cheap for the CPU, real pictures for the AI)
# ----------------------------------------------------------------------------------------------------------------------
VIDEO_DIR = os.path.join(ASSETS, "videos")
VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")
EQ_VW = 2048                                   # width of the 360° picture made from a video (2048 x 1024)


def video_list():
    """All videos in sim_assets/videos: [(name shown, path)]."""
    out = []
    for p in sorted(glob.glob(os.path.join(VIDEO_DIR, "*"))):
        if p.lower().endswith(VIDEO_EXT) and os.path.isfile(p):
            out.append((VideoScene.read_meta(p).get("name") or os.path.splitext(os.path.basename(p))[0], p))
    return out


class VideoScene:
    """Plays a video in a loop as the world of the simulation.
    360° video (equirectangular, 2:1): the cameras look around in it. A normal video: it fills "fov" degrees straight ahead.
    Optional settings next to the video, same name with .json, e.g. wald_nacht.json:
      {"name": "Wald in der Nacht", "night": true, "hour": 23, "ambient": 9, "fov": 90, "yaw": 0,
       "events": [{"t": 12.5, "sensor": "PIR Zelt", "kind": "pir"}, {"t": 40, "sensor": "Wohnwagen-Tür", "kind": "door", "active": true}]}
    night: true/false (otherwise guessed from the brightness), yaw: which direction of the video is straight ahead (degrees),
    events: sensor messages at these seconds of the video (every loop)."""

    def __init__(self, path, sim):
        self.path = path; self.sim = sim; self.meta = self.read_meta(path)
        self.name = self.meta.get("name") or os.path.splitext(os.path.basename(path))[0]
        self.frame = None; self.moving = None; self.lum = 128.0; self.t = 0.0; self.length = 0.0
        self.equi = None; self.stop_ = False; self.msg = "wird geöffnet …"; self.small = False
        self.bg = cv2.createBackgroundSubtractorMOG2(history=150, varThreshold=24, detectShadows=False)
        threading.Thread(target=self._run, daemon=True).start()

    @staticmethod
    def read_meta(path):
        try:
            import json
            with open(os.path.splitext(path)[0] + ".json", encoding="utf-8") as f:
                m = json.load(f)
            return m if isinstance(m, dict) else {}
        except (OSError, ValueError):
            return {}

    def ok(self):
        return self.frame is not None and not self.stop_

    def stop(self):
        self.stop_ = True

    def night(self):
        n = self.meta.get("night")
        return bool(n) if n is not None else self.lum < 50

    def light(self):
        return 0.03 if self.night() else float(np.clip((self.lum - 20) / 110.0, 0.13, 1.0))

    def _prepared(self, cap):
        """Big videos (4K) cost much CPU to decode: once made smaller with ffmpeg (2048 wide, 15 pictures/s) and kept."""
        import shutil, subprocess
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0; fps = cap.get(cv2.CAP_PROP_FPS) or 25
        if (w <= EQ_VW and fps <= 16) or not shutil.which("ffmpeg"):
            return None
        d = os.path.join(os.path.dirname(self.path), ".klein"); os.makedirs(d, exist_ok=True)
        out = os.path.join(d, os.path.splitext(os.path.basename(self.path))[0] + ".mp4")
        if os.path.isfile(out) and os.path.getmtime(out) >= os.path.getmtime(self.path):
            return out
        self.msg = "wird für den Pi verkleinert (einmalig, kann einige Minuten dauern) …"
        tmp = out + ".tmp.mp4"
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", self.path, "-vf", f"scale='min({EQ_VW},iw)':-2,fps=15",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-an", tmp], capture_output=True)
        if r.returncode == 0 and os.path.isfile(tmp):
            os.replace(tmp, out); return out
        return None

    def _canvas(self, fr):
        """A video picture -> 360° picture (2048 x 1024)."""
        h, w = fr.shape[:2]
        if self.equi is None:
            e = self.meta.get("equirect")
            self.equi = bool(e) if e is not None else abs(w - 2 * h) <= h * 0.04
        if self.equi:
            c = cv2.resize(fr, (EQ_VW, EQ_VW // 2), interpolation=cv2.INTER_AREA) if w != EQ_VW else fr
        else:                                       # a normal video straight ahead (flat, as filmed), around it a dim blurred rest
            if getattr(self, "_gm", None) is None or self._gm[0] != (w, h):
                fov = math.radians(min(150.0, max(20.0, float(self.meta.get("fov", 90)))))
                fl = (w / 2.0) / math.tan(fov / 2.0); PW, PH = EQ_VW, EQ_VW // 2
                lon = ((np.arange(PW, dtype=np.float32) + 0.5) / PW * 2 * math.pi - math.pi)[None, :]
                lat = (math.pi / 2 - (np.arange(PH, dtype=np.float32) + 0.5) / PH * math.pi)[:, None]
                dx, dy, dz = np.cos(lat) * np.sin(lon), np.sin(lat) * np.ones_like(lon), np.cos(lat) * np.cos(lon)
                front = dz > 0.05; dz = np.where(front, dz, 1.0)
                mx = np.where(front, w / 2.0 + fl * dx / dz, -10).astype(np.float32)
                my = np.where(front, h / 2.0 - fl * dy / dz, -10).astype(np.float32)
                inside = ((mx >= 0) & (mx < w - 1) & (my >= 0) & (my < h - 1)).astype(np.float32)
                self._gm = ((w, h), mx, my, cv2.GaussianBlur(inside, (0, 0), 2.0)[..., None])
            _k, mx, my, alpha = self._gm
            pic = cv2.remap(fr, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
            rest = cv2.resize(cv2.resize(fr, (32, 16), interpolation=cv2.INTER_AREA), (EQ_VW, EQ_VW // 2)).astype(np.float32) * 0.5
            c = (pic * alpha + rest * (1 - alpha)).astype(np.uint8)
        yaw = float(self.meta.get("yaw", 0) or 0)
        if yaw:
            c = np.roll(c, -int(yaw / 360.0 * EQ_VW), axis=1)
        return c

    def _run(self):
        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            self.msg = "Video lässt sich nicht öffnen"; return
        p = self._prepared(cap)
        if p:
            cap.release(); cap = cv2.VideoCapture(p); self.small = True
        fps = min(25.0, cap.get(cv2.CAP_PROP_FPS) or 25.0); n = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        self.length = n / fps if n > 0 else 0.0
        if self.meta.get("hour") is not None:
            self.sim.set_hour(float(self.meta["hour"]))
        if self.meta.get("ambient") is not None:
            self.sim.ambient = float(self.meta["ambient"])
        evs = [e for e in (self.meta.get("events") or []) if isinstance(e, dict) and "t" in e]
        idx = 0; t0 = time.time(); last_t = -1.0
        while not self.stop_:
            ok, fr = cap.read()
            if not ok:                                               # end: from the start again
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0); idx = 0; t0 = time.time(); last_t = -1.0
                ok, fr = cap.read()
                if not ok:
                    self.msg = "Video lässt sich nicht lesen"; return
            vt = idx / fps; idx += 1
            for e in evs:                                            # sensor messages of the scenario
                if last_t < float(e["t"]) <= vt:
                    self.sim.add_event(str(e.get("sensor", "Sensor")), str(e.get("kind", "other")), e.get("active"))
            last_t = vt
            c = self._canvas(fr)
            sm = cv2.resize(c, (256, 128), interpolation=cv2.INTER_AREA)
            m = self.bg.apply(cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY))  # what moves = warm (people, animals) for the thermal picture
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
            self.moving = cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), 1.2)
            fs = cv2.resize(fr, (128, 64), interpolation=cv2.INTER_AREA)                     # brightness of the filmed picture
            self.lum = float(cv2.cvtColor(fs[32:] if self.equi else fs, cv2.COLOR_BGR2GRAY).mean())
            self.frame = c; self.t = vt
            self.msg = (f"läuft {int(vt // 60):02d}:{int(vt % 60):02d}" + (f" / {int(self.length // 60):02d}:{int(self.length % 60):02d}" if self.length else "")
                        + (" · 360°" if self.equi else f" · normales Video ({int(float(self.meta.get('fov', 90)))}°)")
                        + (" · verkleinert" if self.small else "") + (" · Nacht" if self.night() else " · Tag"))
            time.sleep(max(0.0, t0 + idx / fps - time.time()))
        cap.release()

    def temp_map(self, amb, cl, sun):
        """Rough temperature picture (256 x 128, °C) made from the video: sky cold, ground about the air, moving things warm."""
        c = self.frame; mv = self.moving
        if c is None:
            return None
        sm = cv2.resize(c, (256, 128), interpolation=cv2.INTER_AREA).astype(np.float32)
        b, g, r = sm[..., 0], sm[..., 1], sm[..., 2]; lum = (b + g + r) / 3.0
        T = np.full((128, 256), amb, np.float32)
        T += (lum - lum.mean()) / 255.0 * (6.0 * sun)                         # by day dark things in the sun are warmer
        upper = np.zeros((128, 256), bool); upper[:64] = True
        skym = upper & (((b > r + 8) & (lum > 90)) | (lum > 170) | (self.night() & (lum < 40)))
        T[skym] = amb - (35.0 * (1 - cl) + 4.0 * cl) * 0.8
        if mv is not None:
            T = T * (1 - mv) + 30.0 * mv
        return cv2.GaussianBlur(T, (0, 0), 0.8)

# ----------------------------------------------------------------------------------------------------------------------
# the simulator
# ----------------------------------------------------------------------------------------------------------------------
class CampingSim(SimServer):
    def __init__(self, port=DEFAULT_PORT, pano=None, autoupdate=True, hd=False):
        # normal: a size that is plenty for motion detection and the AI and keeps the CPU of a Pi cool; --hd: bigger pictures
        w0, h0, w1, h1 = (1280, 720, 960, 540) if hd else (960, 540, 640, 360)
        info = SimInfo(name=f"{SIM_NAME} {SIM_VERSION}",
                       cameras=[CamInfo(0, "Head camera (NoIR)", w0, h0, 12.0, 66.0, 41.0, True, True),
                                CamInfo(1, "Caravan camera", w1, h1, 8.0, 100.0, 62.0, False, False)],
                       thermal={"w": 80, "h": 62, "fps": 8.0, "fov_h": 45.0, "fov_v": 35.0, "unit": "C", "on_head": True},
                       sensors=[{"name": "Wohnwagen-Tür", "kind": "door"}, {"name": "PIR Zelt", "kind": "pir"},
                                {"name": "Gas Wohnwagen", "kind": "gas"}, {"name": "Velo", "kind": "tag"}])
        super().__init__(info, port=port)
        self.clock0 = time.time(); lt = time.localtime(); self.hour0 = lt.tm_hour + lt.tm_min / 60.0; self.speed = 1.0
        self.moon = 0.5; self.weather = "clear"; self.wind = 8.0; self.ambient = 14.0; self.humidity = 70.0; self.pressure = 1013.0
        self.storm_t = 0.0
        self.auto_walkers = True; self.insects = 0.6; self.dew = 0.0; self.web = False; self.covered = False
        self.noise = 1.0; self.osd = True; self.cam1_yaw = -12.0
        self.walkers = []; self.cars = []; self.door_open = False
        self.wlock = threading.Lock(); self.last = time.time(); self.next_auto = time.time() + 20
        self.exposure = {0: 1.0, 1: 1.0}; self._cache = {}; self._bugs = []
        self.pano_file = pano or (os.path.join(ASSETS, "pano.jpg") if os.path.isfile(os.path.join(ASSETS, "pano.jpg")) else None)
        self._photo = None; self._world = None; self._world_key = None
        self.video = None; self.video_figures = False                  # 360° video scenario; also draw visitors on it
        rng = random.Random(7)
        self.trees = [(rng.uniform(-170, 170), rng.uniform(16, 50), rng.uniform(0.8, 1.35)) for _ in range(34)]
        self.stones = [(rng.uniform(-60, 60), rng.uniform(4, 15)) for _ in range(6)]
        self.update_msg = ""; self.autoupdate = autoupdate; self.gas_on = False; self.demo_msg = ""
        self._register_controls()
        threading.Thread(target=self._life, daemon=True).start()
        if autoupdate:
            threading.Thread(target=self._updater, daemon=True).start()

    # ---- automatic update -------------------------------------------------------------------------------------------
    @staticmethod
    def _sha(path):
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except OSError:
            return ""

    def _updater(self):
        """Motion Watch sends the checksums of the simulator files it carries. Different = fetch them, check them, restart."""
        time.sleep(15)
        while True:
            try:
                want = dict(self.state.sim_files or {})
                if want and self.mw_addr:
                    old = [n for n, h in want.items() if RUN_SHA.get(n) != h]          # the version that RUNS (not the one on disk)
                    if old and all(self._sha(os.path.join(HERE, n)) == h for n, h in want.items()):
                        self.update_msg = "Neue Version ist schon da (von Motion Watch installiert) - startet neu …"
                        print("Simulator files were updated - restarting"); time.sleep(1.0)
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                    if old:
                        self.update_msg = "Neue Version von Motion Watch wird geladen …"
                        url = f"{self.state.mw_scheme}://{self.mw_addr}:{self.state.mw_port}/sim/simulator.zip"
                        import ssl
                        ctx = ssl._create_unverified_context() if self.state.mw_scheme == "https" else None   # its own certificate
                        with urllib.request.urlopen(url, timeout=20, context=ctx) as r:
                            data = r.read()
                        z = zipfile.ZipFile(io.BytesIO(data)); files = {}
                        for n in want:
                            b = z.read(n)
                            if hashlib.sha256(b).hexdigest() != want[n]:
                                raise ValueError(f"checksum of {n} does not match - not installed")
                            files[n] = b
                        for n in z.namelist():
                            if n.endswith(".md"):
                                files[n] = z.read(n)
                        for n, b in files.items():
                            with open(os.path.join(HERE, n + ".new"), "wb") as f:
                                f.write(b)
                            os.replace(os.path.join(HERE, n + ".new"), os.path.join(HERE, n))
                        self.update_msg = "Aktualisiert - startet neu …"
                        print("Simulator updated from Motion Watch - restarting")
                        time.sleep(1.0)
                        os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                self.update_msg = f"Aktualisierung nicht möglich: {e}"[:120]
            time.sleep(60)

    # ---- time, light, weather ----------------------------------------------------------------------------------------
    def hour(self, t=None):
        t = time.time() if t is None else t
        return (self.hour0 + (t - self.clock0) * self.speed / 3600.0) % 24.0

    def set_hour(self, h):
        self.hour0 = float(h) % 24.0; self.clock0 = time.time()

    def sun_el(self, t=None):
        """Height of the sun in degrees (simple: highest 50° at 13:00, sunrise ~6:30, sunset ~19:30)."""
        return 50.0 * math.sin((self.hour(t) - 6.5) / 13.0 * math.pi) if 6.5 <= self.hour(t) <= 19.5 else -20.0 * math.sin((self.hour(t) - 19.5) / 11.0 * math.pi) if self.hour(t) > 19.5 else -20.0 * math.sin((self.hour(t) + 4.5) / 11.0 * math.pi)

    def sun(self, t=None):
        return float(np.clip((self.sun_el(t) + 6.0) / 18.0, 0.0, 1.0))           # 0 below -6° (night) .. 1 above 12°

    def clouds(self):
        return {"clear": 0.15, "cloudy": 0.75, "rain": 0.95, "fog": 0.6, "snow": 0.9}.get(self.weather, 0.2)

    def sky_k(self, t=None):
        return max(0.04, min(1.0, 0.1 + self.sun(t) * 0.95 + 0.04 * self.moon))

    def ambient_k(self, t=None):
        """How much daylight falls on things (1 = full day)."""
        lv = self.light_level(t)
        return min(1.0, 0.1 + lv) if lv > 0.1 else lv * 2.0

    def load_video(self, path):
        """Play a video scenario (path) - None: back to the drawn world / the photo."""
        if self.video is not None:
            self.video.stop()
        self.video = VideoScene(path, self) if path else None

    # ---- switched from the web page of Motion Watch (CONTROL protocol, see motionwatch_sim_interface.py) ----------------
    def _register_controls(self):
        A = self.add_control
        A("slider", "hour", "Uhrzeit", lambda: round(self.hour(), 2), self.set_hour, "Szene", min=0, max=23.75, step=0.25, unit="h")
        A("slider", "speed", "Zeit läuft x-fach", lambda: self.speed, lambda v: (self.set_hour(self.hour()), setattr(self, "speed", v)),
          "Szene", min=1, max=120, step=1, unit="×")
        A("slider", "moon", "Mond", lambda: self.moon, lambda v: setattr(self, "moon", v), "Szene", min=0, max=1, step=0.1)
        A("slider", "cam1_yaw", "Kamera 1: Richtung", lambda: self.cam1_yaw, lambda v: setattr(self, "cam1_yaw", v), "Szene", min=-90, max=90, step=1, unit="°")
        A("select", "weather", "Wetter", lambda: self.weather, lambda v: setattr(self, "weather", v), "Wetter",
          options=[["clear", "klar"], ["cloudy", "bewölkt"], ["rain", "Regen"], ["fog", "Nebel"], ["snow", "Schnee"]])
        A("slider", "wind", "Wind", lambda: self.wind, lambda v: setattr(self, "wind", v), "Wetter", min=0, max=120, step=1, unit="km/h")
        A("slider", "ambient", "Temperatur", lambda: self.ambient, lambda v: setattr(self, "ambient", v), "Wetter", min=-15, max=40, step=0.5, unit="°C")
        A("slider", "pressure", "Luftdruck", lambda: self.pressure, lambda v: setattr(self, "pressure", v), "Wetter", min=960, max=1040, step=0.5, unit="hPa")
        A("button", "storm", "Sturm zieht auf", None, lambda: setattr(self, "storm_t", time.time()), "Wetter")
        for k, l in (("person", "Person"), ("fox", "Fuchs"), ("boar", "Wildschwein"), ("deer", "Reh"), ("cat", "Katze")):
            A("button", "spawn_" + k, l, None, lambda k=k: self.spawn(k), "Besuch")
        A("button", "car", "Auto", None, self.car, "Besuch")
        A("toggle", "auto", "ab und zu Besuch von selbst", lambda: self.auto_walkers, lambda v: setattr(self, "auto_walkers", v), "Besuch")
        A("toggle", "figures", "gezeichnete Besucher auch im Video", lambda: self.video_figures, lambda v: setattr(self, "video_figures", v), "Besuch")
        A("toggle", "door", "Wohnwagentür offen", lambda: self.door_open, self.door, "Sensoren")
        A("toggle", "gas", "Gas / Rauch", lambda: self.gas_on, self.gas, "Sensoren")
        A("button", "pir", "PIR Zelt auslösen", None, lambda: self.add_event("PIR Zelt", "pir", None), "Sensoren")
        A("button", "bike", "Velo bewegen", None, lambda: self.add_event("Velo", "tag", None), "Sensoren")
        A("button", "nighttest", "Nacht-Test starten (2 Min.)", None, self.night_test, "Sensoren")
        A("slider", "dew", "Tau auf der Linse", lambda: self.dew, lambda v: setattr(self, "dew", v), "Kamera", min=0, max=1, step=0.05)
        A("toggle", "web", "Spinnennetz vor der Linse", lambda: self.web, lambda v: setattr(self, "web", v), "Kamera")
        A("toggle", "covered", "Kamera abgedeckt", lambda: self.covered, lambda v: setattr(self, "covered", v), "Kamera")
        A("slider", "insects", "Insekten im IR-Licht", lambda: self.insects, lambda v: setattr(self, "insects", v), "Kamera", min=0, max=1, step=0.1)
        A("slider", "noise", "Bildrauschen", lambda: self.noise, lambda v: setattr(self, "noise", v), "Kamera", min=0, max=3, step=0.1)
        A("button", "make_demos", "Beispiel-Videoszenen erzeugen (dauert einige Minuten)", None, self.make_demos, "Szenarien")

    def scenarios(self):
        out = [{"id": "drawn", "name": "Gezeichnete Camping-Welt (3D)", "kind": "world", "deletable": False}]
        out += [{"id": "video:" + os.path.basename(p), "name": "🎬 " + n, "kind": "video", "deletable": True} for n, p in video_list()]
        return out

    def scenario(self):
        return ("video:" + os.path.basename(self.video.path)) if self.video is not None else "drawn"

    def load_scenario(self, id_):
        if id_ == "drawn":
            self.load_video(None); return True, ""
        if id_.startswith("video:"):
            f = os.path.basename(id_[6:]); p = os.path.join(VIDEO_DIR, f)
            if not os.path.isfile(p):
                return False, "video not found"
            self.load_video(p); return True, ""
        return False, "unknown scenario"

    def delete_scenario(self, id_):
        if not id_.startswith("video:"):
            return False, "cannot be deleted"
        f = os.path.basename(id_[6:]); p = os.path.join(VIDEO_DIR, f)
        if not f.lower().endswith(VIDEO_EXT) or not os.path.isfile(p):
            return False, "video not found"
        if self.video is not None and os.path.basename(self.video.path) == f:
            self.load_video(None)
        for x in (p, os.path.splitext(p)[0] + ".json", os.path.join(VIDEO_DIR, ".klein", os.path.splitext(f)[0] + ".mp4")):
            try:
                os.remove(x)
            except OSError:
                pass
        return True, ""

    def status_text(self):
        h = self.hour(); wr = self.world(time.time())
        t = f"{int(h):02d}:{int(h % 1 * 60):02d} · {'Nacht' if wr.dark else 'Tag'} · {self.weather} · {wr.ambient_c} °C · Besucher {len(self.walkers)}"
        if self.video is not None:
            t = f"🎬 {self.video.name}: {self.video.msg}\n" + t
        if self.demo_msg:
            t += "\n" + self.demo_msg
        return t

    def upload_info(self):
        return {"accept": list(VIDEO_EXT) + [".json"], "max_mb": 4096, "label": "Video (360° oder normal) in den Video-Ordner"}

    def make_demos(self):
        """Render the example 360° video scenes into sim_assets/videos (in the background)."""
        if getattr(self, "_demo_busy", False):
            return
        self._demo_busy = True

        def run():
            try:
                import motionwatch_demo_scenes as D
                D.make_all(VIDEO_DIR, lambda m: setattr(self, "demo_msg", m))
            except Exception as e:
                self.demo_msg = f"Beispiel-Szenen: Fehler {e}"[:160]
            self._demo_busy = False
        threading.Thread(target=run, daemon=True).start()

    def upload(self, name, rfile, length):
        import re as _re
        name = os.path.basename(name or "")
        base, ext = os.path.splitext(name)
        base = _re.sub(r"[^\w\-]+", "_", base)[:60].strip("_") or "video"
        if ext.lower() not in VIDEO_EXT + (".json",):
            return {"ok": False, "error": "only videos (mp4, mov, mkv, webm, avi) or .json"}
        if length <= 0 or length > 4 * 1024 ** 3:
            return {"ok": False, "error": "file empty or bigger than 4 GB"}
        os.makedirs(VIDEO_DIR, exist_ok=True)
        dst = os.path.join(VIDEO_DIR, base + ext.lower()); tmp = dst + ".part"; left = length
        with open(tmp, "wb") as f:
            while left > 0:
                b = rfile.read(min(1 << 20, left))
                if not b:
                    break
                f.write(b); left -= len(b)
        if left:
            os.remove(tmp); return {"ok": False, "error": "upload interrupted"}
        os.replace(tmp, dst)
        return dict(self.control_info(), saved=os.path.basename(dst))

    def _vid(self):
        v = self.video
        return v if v is not None and v.ok() else None

    def light_level(self, t=None):
        if self._vid() is not None:
            return self.video.light()
        lv = 0.015 + 0.04 * self.moon * (1 - self.clouds()) + 0.95 * self.sun(t) * (1 - 0.45 * self.clouds())
        return float(lv)

    def sim_epoch(self, t):
        lt = time.localtime(t); base = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))
        return base + self.hour(t) * 3600.0

    def world(self, t):
        press = self.pressure
        if self.storm_t:
            press -= min(6.0, (t - self.storm_t) / 180.0 * 6.0)
        return SimReply(sim_time=self.sim_epoch(t), dark=self.light_level(t) < 0.12, ambient_c=round(self.ambient, 1),
                        pressure_hpa=round(press, 1), wind_kmh=round(self.wind, 1), weather=self.weather, humidity=round(self.humidity),
                        last_event=self.events[-1].id if self.events else 0)

    # ---- life -------------------------------------------------------------------------------------------------------
    def spawn(self, kind, path=None):
        with self.wlock:
            self.walkers.append(Walker(kind, path))

    def car(self):
        with self.wlock:
            self.cars.append({"x": -70.0, "dir": 1, "speed": random.uniform(8, 14)})

    def _life(self):
        while True:
            now = time.time(); dt = min(0.2, now - self.last); self.last = now
            st = self.state
            scare = bool(st.sound) or (st.lights.white and self.light_level(now) < 0.12)
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
        self.gas_on = bool(on); self.add_event("Gas Wohnwagen", "gas", bool(on))

    def load_pano(self, path):
        self.pano_file = path; self._photo = None; _MAPS.clear()

    # ---- the 360° world: colour, distance and temperature for every direction ---------------------------------------
    def _static(self):
        """What does not change: ground distance, ground pattern, mountains (computed once)."""
        if "static" in self._cache:
            return self._cache["static"]
        W, H = EQ_W, EQ_H; hz = H // 2
        lat = (math.pi / 2 - (np.arange(H, dtype=np.float32) + 0.5) / H * math.pi)[:, None]
        lon = ((np.arange(W, dtype=np.float32) + 0.5) / W * 2 * math.pi - math.pi)[None, :]
        dist = np.full((H, W), FAR, np.float32)
        below = (lat < -0.0005)[:, 0]
        dist[below] = np.broadcast_to(CAM_H / np.tan(-lat[below]), (int(below.sum()), W))
        dist = np.minimum(dist, FAR)
        # the ground pattern in ground coordinates (perspective comes by itself): grass blades, patches, worn paths
        gx = np.clip(dist * np.sin(lon), -400, 400); gz = np.clip(dist * np.cos(lon), -400, 400)
        big = fbm((512, 512), (64, 16), 1); small = fbm((512, 512), (4, 2), 2)
        mir = lambda q: 511 - np.abs(np.floor(q).astype(np.int64) % 1022 - 511)       # mirrored tiles: no visible seams
        ix, iz = mir(gx * 9.0), mir(gz * 9.0); jx, jz = mir(gx * 1.2 + 77), mir(gz * 1.2 + 31)              # 1 texel ~ 11 cm
        pat = small[iz, ix] * 0.6 + big[jz, jx] * 1.0
        # mountains: a ridge around the whole world
        rng = np.random.default_rng(5); xs = np.arange(W)
        ridge = (0.07 + 0.045 * np.sin(xs / W * 2 * math.pi * 3 + 1) + 0.03 * np.sin(xs / W * 2 * math.pi * 7 + 2)
                 + 0.02 * fbm((1, W), (40, 8), 6)[0])
        ridge_y = (hz - ridge * H).astype(int)
        mount = np.zeros((H, W), bool)
        for x in range(W):
            mount[ridge_y[x]:hz, x] = True
        rock = fbm((H, W), (64, 12, 3), 8)
        dist[mount] = 3000.0
        self._cache["static"] = (dist, pat, mount, ridge_y, rock, lat, lon)
        return self._cache["static"]

    def _world_colour(self, t):
        """The coloured 360° world for the present sun, clouds and weather (recomputed when they change)."""
        key = (round(self.sun_el(t), 0), self.weather, round(self.moon, 1))
        if self._world is not None and self._world_key == key:
            return self._world
        dist, pat, mount, ridge_y, rock, lat, lon = self._static()
        H, W = dist.shape; hz = H // 2
        sun_el = self.sun_el(t); day = self.sun(t); cl = self.clouds()
        # sky: deep blue at the top, pale at the horizon, orange at dusk, grey with clouds
        el = np.clip(lat[:hz] / (math.pi / 2), 0, 1)
        top = np.array([170, 110, 50], np.float32); hor = np.array([235, 215, 190], np.float32)
        dusk = max(0.0, 1.0 - abs(sun_el - 2.0) / 10.0) if sun_el > -8 else 0.0
        hor = hor * (1 - dusk) + np.array([120, 160, 245], np.float32) * dusk
        sky = hor[None, None] * (1 - el[..., None] ** 0.6) + top[None, None] * el[..., None] ** 0.6
        grey = np.array([175, 175, 172], np.float32)
        sky = sky * (1 - cl * 0.8) + grey * cl * 0.8
        cloud = np.clip(fbm((hz, W), (96, 32, 8), 11) * 1.4 + (cl - 0.45) * 2.0, 0, 1)
        sky = sky * (1 - cloud[..., None] * 0.8) + np.array([235, 235, 235], np.float32) * cloud[..., None] * 0.8
        sky = np.broadcast_to(sky, (hz, W, 3)).copy()
        if sun_el > -2 and cl < 0.9:                                   # the sun and its glare (south-west, follows the time)
            sx = int((math.radians(-60 + (self.hour(t) - 13) * 15) + math.pi) / (2 * math.pi) * W) % W
            sy = int(hz - math.radians(max(sun_el, 0.5)) / math.pi * H)
            g = np.zeros((hz, W), np.float32); cv2.circle(g, (sx, sy), 6, 1.0, -1)
            g = cv2.GaussianBlur(g, (0, 0), 25) * 6 * (1 - cl)
            sky += g[..., None] * np.array([200, 235, 255], np.float32)
        img = np.zeros((H, W, 3), np.float32); img[:hz] = sky
        # ground: grass with patches; snow covers it
        grass = np.array([58, 122, 70], np.float32); dry = np.array([70, 128, 140], np.float32)
        gmix = np.clip(pat * 0.9 + 0.35, 0, 1)[..., None]
        ground = grass * (1 - gmix * 0.6) + dry * gmix * 0.6 + pat[..., None] * 14
        if self.weather == "snow":
            ground = ground * 0.25 + np.array([235, 235, 238], np.float32) * 0.75 + pat[..., None] * 6
        img[hz:] = ground[hz:]
        # mountains: rock, snow on the peaks, bluish with the distance
        mcol = np.array([112, 112, 108], np.float32)[None, None] + rock[..., None] * 18
        snowline = np.zeros((H, W), bool)
        for x in range(0, W):
            if ridge_y[x] < hz - 0.09 * H:
                snowline[ridge_y[x]:ridge_y[x] + int(0.02 * H), x] = True
        mcol = np.where(snowline[..., None], np.array([235, 235, 240], np.float32), mcol)
        img = np.where(mount[..., None], mcol * 0.7 + np.array([200, 175, 150], np.float32) * 0.3, img)
        # the sky shines by itself; ground and mountains keep their daylight colour (the light comes in render_camera)
        sky_k = self.sky_k(t)
        skym = ~mount; skym[hz:] = False
        img[skym] *= sky_k
        if day < 0.15:                                                  # stars on a clear night
            rng = np.random.default_rng(3); n = int(900 * (1 - cl))
            ys, xs = rng.integers(0, int(hz * 0.9), n), rng.integers(0, W, n)
            img[ys, xs] = 190 * (1 - day * 6)
            mx, my = int(0.62 * W), int(hz * 0.45)
            if self.moon > 0.1 and cl < 0.8:
                cv2.circle(img, (mx, my), 7, (210 * self.moon + 30,) * 3, -1, cv2.LINE_AA)
        self._world = np.clip(img, 0, 255).astype(np.uint8); self._world_key = key
        return self._world

    def _world_temp(self, t):
        """Temperature of every direction (°C): sky, ground (sun-warmed by day, cooled at night), mountains."""
        key = (round(self.sun_el(t), 0), self.weather, round(self.ambient, 0))
        if self._cache.get("tkey") == key:
            return self._cache["temp"]
        dist, pat, mount, ridge_y, rock, lat, lon = self._static()
        H, W = dist.shape; hz = H // 2; amb = self.ambient; cl = self.clouds()
        sky_drop = 35.0 * (1 - cl) + 4.0 * cl                          # a clear sky is very cold, clouds are almost air-warm
        el = np.clip(lat[:hz] / (math.pi / 2), 0, 1)
        T = np.zeros((H, W), np.float32)
        T[:hz] = amb - sky_drop * (0.35 + 0.65 * el ** 0.5)
        sun = max(0.0, self.sun_el(t)) / 50.0
        night = 1.0 if self.sun_el(t) < 0 else 0.0
        ground = amb + 10.0 * sun * (1 - cl) - 3.5 * night * (1 - cl) + pat * 1.2
        if self.weather == "rain":
            ground = amb - 1.0 + pat * 0.4
        if self.weather == "snow":
            ground = np.minimum(ground, 0.0) + pat * 0.3
        # far ground looks colder (the air between, and the flat angle)
        haze = 1 - np.exp(-dist / 800.0)
        T[hz:] = (ground * (1 - haze) + (amb - 4) * haze)[hz:]
        T = np.where(mount, amb - 6 + rock * 1.5, T)
        self._cache["temp"] = T.astype(np.float32); self._cache["tkey"] = key
        return self._cache["temp"]

    def _photo_world(self):
        if self._photo is None and self.pano_file and os.path.isfile(self.pano_file):
            img = cv2.imread(self.pano_file)
            if img is not None:
                if abs(img.shape[1] - img.shape[0] * 2) > img.shape[0] * 0.05:      # a phone panorama: put it into a 360° frame
                    w = img.shape[1]; h2 = w // 2; can = np.full((h2, w, 3), 150, np.uint8)
                    y0 = max(0, h2 // 2 - img.shape[0] // 2); can[y0:y0 + min(img.shape[0], h2)] = img[:h2]
                    img = can
                self._photo = cv2.resize(img, (min(6000, img.shape[1]), min(3000, img.shape[1] // 2)))
        return self._photo

    # ---- drawing with a depth buffer --------------------------------------------------------------------------------
    @staticmethod
    def _poly(img, dep, v, pts, col, d):
        q = [v.ground(az, dd, h) for az, dd, h in pts]
        if all(x is not None for x in q):
            p = np.array(q, np.int32)
            cv2.fillPoly(img, [p], col, cv2.LINE_AA); cv2.fillPoly(dep, [p], float(d))

    @staticmethod
    def _shade(col, k):
        return tuple(int(max(0, min(255, c * k))) for c in col)

    def _drawables(self, v, t):
        out = [(OBJECTS["road"][1] + 2, lambda im, dp: self._road(im, dp, v))]
        for tr_ in self.trees:
            out.append((tr_[1], lambda im, dp, tr_=tr_: self._tree(im, dp, v, t, tr_)))
        for name in ("tent", "caravan", "bike"):
            out.append((OBJECTS[name][1], lambda im, dp, n=name: getattr(self, "_" + n)(im, dp, v)))
        for st_ in self.stones:
            out.append((st_[1], lambda im, dp, st_=st_: self._stone(im, dp, v, st_)))
        return out

    def _road(self, img, dep, v):
        d = OBJECTS["road"][1]
        for a0 in range(-80, 80, 8):                                    # in pieces, so it is drawn when only a part is in view
            self._poly(img, dep, v, [(a0, d, 0), (a0 + 8.5, d, 0), (a0 + 8.5, d + 3, 0), (a0, d + 3, 0)], (110, 130, 140), d + 1.5)

    def _stone(self, img, dep, v, st_):
        az, d = st_; c = v.ground(az, d, 0.12)
        if c:
            r = max(2, int(v.f * 0.25 / d)); ctr = (int(c[0]), int(c[1]))
            cv2.ellipse(img, ctr, (r, int(r * 0.6)), 0, 0, 360, (118, 120, 118), -1, cv2.LINE_AA)
            cv2.ellipse(img, (ctr[0] - r // 4, ctr[1] - r // 5), (r // 2, int(r * 0.25)), 0, 0, 360, (150, 152, 150), -1, cv2.LINE_AA)
            cv2.ellipse(dep, ctr, (r, int(r * 0.6)), 0, 0, 360, d, -1)

    def _tree(self, img, dep, v, t, tr_):
        az, d, s = tr_
        base = v.ground(az, d); top = v.ground(az, d, 6.0 * s)
        if base is None or top is None or not (-400 < base[0] < v.W + 400):
            return
        hpx = base[1] - top[1]; r = max(2, int(hpx * 0.3)); bx, by = int(base[0]), int(base[1])
        sway = self.wind / 60.0; dx = int(sway * r * 0.45 * math.sin(t * (1.3 + s) + az))
        cv2.line(img, (bx, by), (bx + dx // 3, int(by - hpx * 0.5)), (35, 55, 80), max(1, r // 4), cv2.LINE_AA)
        cv2.line(dep, (bx, by), (bx + dx // 3, int(by - hpx * 0.5)), d, max(1, r // 4))
        rng = random.Random(int(az * 100))
        cx, cy = int(top[0]) + dx, int(top[1] + r * 1.0)
        for k in range(9):                                              # a crown out of shaded blobs
            ox, oy = rng.uniform(-0.7, 0.7) * r, rng.uniform(-0.6, 0.7) * r
            rr = int(r * rng.uniform(0.45, 0.7)); light = 0.7 + 0.5 * (-oy / r) * 0.5 + rng.uniform(-0.1, 0.1)
            col = self._shade((40, 104, 48), light)
            cv2.circle(img, (int(cx + ox + dx * (oy < 0) * 0.3), int(cy + oy)), rr, col, -1, cv2.LINE_AA)
            cv2.circle(dep, (int(cx + ox), int(cy + oy)), rr, d, -1)

    def _tent(self, img, dep, v):
        az, d = OBJECTS["tent"]
        self._poly(img, dep, v, [(az - 9, d, 0), (az, d, 1.6), (az + 9, d, 0)], (40, 125, 225), d)
        self._poly(img, dep, v, [(az, d, 1.6), (az + 9, d, 0), (az + 11, d + 1.5, 0)], (30, 95, 175), d + 0.5)
        self._poly(img, dep, v, [(az - 2, d - 0.1, 0), (az, d - 0.1, 1.1), (az + 2, d - 0.1, 0)], (25, 70, 130), d - 0.1)

    def _caravan(self, img, dep, v):
        az, d = OBJECTS["caravan"]
        self._poly(img, dep, v, [(az - 14, d, 0.3), (az + 14, d, 0.3), (az + 14, d, 2.6), (az - 14, d, 2.6)], (212, 215, 220), d)
        self._poly(img, dep, v, [(az - 14, d, 2.4), (az + 14, d, 2.4), (az + 14, d, 2.6), (az - 14, d, 2.6)], (170, 172, 176), d)
        self._poly(img, dep, v, [(az - 14, d, 0.3), (az + 14, d, 0.3), (az + 14, d, 0.5), (az - 14, d, 0.5)], (90, 92, 96), d)
        lit = self.light_level() < 0.12
        self._poly(img, dep, v, [(az - 11, d - 0.05, 1.3), (az - 4, d - 0.05, 1.3), (az - 4, d - 0.05, 2.0), (az - 11, d - 0.05, 2.0)],
                   (40, 120, 200) if lit else (120, 90, 60), -(d - 0.05) if lit else d - 0.05)            # window (lit at night)
        door = [(az + 6, d - 0.05, 0.4), (az + 11, d - 0.05, 0.4), (az + 11, d - 0.05, 2.3), (az + 6, d - 0.05, 2.3)]
        self._poly(img, dep, v, door, (90, 180, 240) if self.door_open and lit else (25, 25, 25) if self.door_open else (80, 80, 92),
                   -(d - 0.05) if self.door_open and lit else d - 0.05)
        if self.door_open:
            self._poly(img, dep, v, [(az + 11, d - 0.05, 0.4), (az + 13.5, d - 1.0, 0.4), (az + 13.5, d - 1.0, 2.3), (az + 11, d - 0.05, 2.3)], (80, 80, 92), d - 0.5)
        for k in (-9, 9):
            c = v.ground(az + k, d - 0.3, 0.3)
            if c:
                r = max(2, int(v.f * 0.3 / d)); cv2.circle(img, (int(c[0]), int(c[1])), r, (25, 25, 25), -1, cv2.LINE_AA)

    def _bike(self, img, dep, v):
        az, d = OBJECTS["bike"]
        pts = [v.ground(az + k, d, 0.35) for k in (-1.3, 1.3)]
        if all(pts):
            r = max(2, int(v.f * 0.35 / d)); w = max(1, r // 7)
            for p in pts:
                cv2.circle(img, (int(p[0]), int(p[1])), r, (30, 30, 30), w, cv2.LINE_AA)
            top = v.ground(az, d, 0.9)
            if top:
                for p in pts:
                    cv2.line(img, (int(p[0]), int(p[1])), (int(top[0]), int(top[1])), (40, 40, 160), w, cv2.LINE_AA)
            cv2.rectangle(dep, (int(pts[0][0]) - r, int(pts[0][1]) - r * 2), (int(pts[1][0]) + r, int(pts[1][1]) + r), d, -1)

    def _walker(self, img, dep, v, w):
        az, d = w.az_dist()
        foot = v.ground(az, d); top = v.ground(az, d, KINDS[w.kind][0])
        if foot is None or top is None:
            return
        hpx = max(2.0, foot[1] - top[1]); x, y = int(foot[0]), int(foot[1])
        if not (-hpx * 3 < x < v.W + hpx * 3):
            return
        cv2.ellipse(img, (x, y), (int(hpx * 0.35), max(1, int(hpx * 0.05))), 0, 0, 360, (25, 45, 28), -1, cv2.LINE_AA)
        if w.sprite is not None:
            s = w.sprite if w.dir > 0 else cv2.flip(w.sprite, 1)
            k = hpx / s.shape[0]; sw, sh = max(1, int(s.shape[1] * k)), max(1, int(hpx))
            s = cv2.resize(s, (sw, sh), interpolation=cv2.INTER_AREA)
            x0, y0 = x - sw // 2, y - sh
            a0, a1 = max(0, -x0), min(sw, img.shape[1] - x0); b0, b1 = max(0, -y0), min(sh, img.shape[0] - y0)
            if a1 > a0 and b1 > b0:
                al = s[b0:b1, a0:a1, 3:4].astype(np.float32) / 255.0
                roi = img[y0 + b0:y0 + b1, x0 + a0:x0 + a1]
                roi[:] = (roi * (1 - al) + s[b0:b1, a0:a1, :3] * al).astype(np.uint8)
                dr = dep[y0 + b0:y0 + b1, x0 + a0:x0 + a1]; dr[al[..., 0] > 0.5] = d
            return
        L = KINDS[w.kind][1] / KINDS[w.kind][0] * hpx; sw_ = math.sin(w.phase)
        lw = lambda f: max(1, int(hpx * f))
        layers = []
        if w.kind == "person":
            hip = (x, int(y - hpx * 0.48)); sh_ = (x, int(y - hpx * 0.80)); head = (x, int(y - hpx * 0.91))
            for k, c in ((1, self._shade(w.trousers, 0.75)), (-1, w.trousers)):            # legs (far one darker)
                knee = (int(x + k * sw_ * hpx * 0.07), int(y - hpx * 0.25)); foot_ = (int(x + k * sw_ * hpx * 0.14), y)
                layers += [("l", hip, knee, c, lw(0.085)), ("l", knee, foot_, c, lw(0.075)), ("l", foot_, (foot_[0] + w.dir * lw(0.06), y), (30, 30, 30), lw(0.04))]
            layers += [("l", hip, sh_, w.jacket, lw(0.2)), ("l", (x, int(y - hpx * 0.5)), sh_, self._shade(w.jacket, 1.15), lw(0.12))]
            for k, c in ((1, self._shade(w.jacket, 0.75)), (-1, w.jacket)):                  # arms swing against the legs
                el_ = (int(x - k * sw_ * hpx * 0.07), int(y - hpx * 0.62))
                layers += [("l", sh_, el_, c, lw(0.06)), ("l", el_, (int(el_[0] - k * sw_ * hpx * 0.04 + w.dir * hpx * 0.02), int(y - hpx * 0.47)), (140, 165, 205), lw(0.045))]
            layers += [("c", (head[0], head[1] + lw(0.02)), lw(0.035), (140, 165, 205)), ("c", head, lw(0.065), (140, 165, 205)),
                       ("c", (head[0] - w.dir * lw(0.01), head[1] - lw(0.03)), lw(0.06), (40, 45, 55))]
        else:
            col = {"fox": (45, 100, 205), "boar": (48, 52, 62), "deer": (60, 105, 150), "cat": (85, 88, 95)}[w.kind]
            dark = self._shade(col, 0.7); belly = (220, 225, 230) if w.kind in ("fox", "deer") else self._shade(col, 1.1)
            bh = hpx * (0.45 if w.kind not in ("deer",) else 0.36); by = int(y - hpx * (0.55 if w.kind != "deer" else 0.66))
            for k, c in ((0.33, dark), (-0.33, dark), (0.28, col), (-0.38, col)):              # four legs, walking
                hipx = int(x + k * L); ph_ = sw_ if k > 0 else -sw_
                layers.append(("l", (hipx, by), (int(hipx + ph_ * hpx * 0.12 * w.dir), y), c, lw(0.07 if w.kind == "boar" else 0.05)))
            layers.append(("e", (x, by), (max(2, int(L / 2)), max(1, int(bh / 2))), col))
            layers.append(("e", (x, int(by + bh * 0.22)), (max(2, int(L * 0.38)), max(1, int(bh * 0.18))), belly))
            hx = int(x + w.dir * L * 0.55)
            if w.kind == "deer":
                nx, ny = int(x + w.dir * L * 0.42), int(by - bh * 1.25)
                layers += [("l", (int(x + w.dir * L * 0.35), by), (nx, ny), col, lw(0.12)), ("e", (int(nx + w.dir * hpx * 0.08), ny), (max(2, lw(0.1)), max(1, lw(0.055))), col),
                           ("l", (nx, ny - lw(0.04)), (nx - w.dir * lw(0.03), ny - lw(0.14)), dark, lw(0.025))]
            elif w.kind == "boar":
                layers += [("e", (hx, int(by + bh * 0.05)), (max(2, int(bh * 0.55)), max(1, int(bh * 0.42))), col),
                           ("c", (int(hx + w.dir * bh * 0.55), int(by + bh * 0.15)), max(1, int(bh * 0.14)), (90, 90, 110))]
            else:
                hy = int(by - bh * 0.35)
                layers += [("c", (hx, hy), max(2, int(bh * 0.42)), col),
                           ("p", [(hx - lw(0.06), hy - lw(0.09)), (hx - lw(0.02), hy - lw(0.3)), (hx + lw(0.02), hy - lw(0.08))], dark),
                           ("p", [(int(hx + w.dir * bh * 0.3), hy - lw(0.02)), (int(hx + w.dir * bh * 0.85), hy + lw(0.06)), (int(hx + w.dir * bh * 0.3), hy + lw(0.12))], col)]
                tail_end = (int(x - w.dir * L * 1.0), int(by + bh * (0.5 if w.kind == "fox" else -0.4)))
                layers += [("l", (int(x - w.dir * L / 2), by), tail_end, col, max(2, int(bh * (0.38 if w.kind == "fox" else 0.15))))]
                if w.kind == "fox":
                    layers.append(("c", tail_end, max(1, int(bh * 0.17)), (225, 228, 232)))
        for L_ in layers:
            if L_[0] == "l":
                cv2.line(img, L_[1], L_[2], L_[3], L_[4], cv2.LINE_AA); cv2.line(dep, L_[1], L_[2], d, L_[4])
            elif L_[0] == "c":
                cv2.circle(img, L_[1], L_[2], L_[3], -1, cv2.LINE_AA); cv2.circle(dep, L_[1], L_[2], d, -1)
            elif L_[0] == "e":
                cv2.ellipse(img, L_[1], L_[2], 0, 0, 360, L_[3], -1, cv2.LINE_AA); cv2.ellipse(dep, L_[1], L_[2], 0, 0, 360, d, -1)
            elif L_[0] == "p":
                p = np.array(L_[1], np.int32); cv2.fillPoly(img, [p], L_[2], cv2.LINE_AA); cv2.fillPoly(dep, [p], d)

    def _car(self, img, dep, v, c):
        d = OBJECTS["road"][1] + 1.5; az = math.degrees(math.atan2(c["x"], d))
        p0 = v.ground(az - math.degrees(2.2 / d), d, 0.0); p1 = v.ground(az + math.degrees(2.2 / d), d, 1.45)
        if not p0 or not p1:
            return
        x0, x1 = sorted((int(p0[0]), int(p1[0]))); y1, y0 = int(p0[1]), int(p1[1]); hgt = y1 - y0
        cv2.rectangle(img, (x0, y0 + hgt // 3), (x1, y1 - hgt // 6), (60, 60, 140), -1)
        cv2.rectangle(img, (x0 + (x1 - x0) // 5, y0), (x1 - (x1 - x0) // 4, y0 + hgt // 3), (55, 55, 120), -1)
        cv2.rectangle(img, (x0 + (x1 - x0) // 4, y0 + hgt // 12), (x1 - (x1 - x0) // 3, y0 + hgt // 3), (90, 80, 70), -1)
        for k in (0.2, 0.8):
            cv2.circle(img, (int(x0 + (x1 - x0) * k), y1 - hgt // 6), max(1, hgt // 5), (20, 20, 20), -1)
        cv2.rectangle(dep, (x0, y0), (x1, y1), d, -1)
        c["_scr"] = ((x1 if c["dir"] > 0 else x0), y1 - hgt // 3, max(2, hgt // 6), d)

    # ---- the cameras --------------------------------------------------------------------------------------------------
    def render_camera(self, cam, st, t):
        info = self.info.cameras[cam]; W, H = info.w, info.h
        if self.covered and cam == 0:
            return np.clip(np.random.default_rng().normal(8, 3, (H, W, 3)), 0, 255).astype(np.uint8)
        yaw, pitch = (st.servo.pan_deg, st.servo.tilt_deg - 6.0) if info.on_head else (self.cam1_yaw, -10.0)
        v = View(W, H, info.fov_h, yaw, pitch)
        vid = self._vid()
        photo = vid.frame if vid is not None else self._photo_world()
        dist = self._static()[0]
        src = photo if photo is not None else self._world_colour(t)
        mx, my, ang = eq_maps(W, H, info.fov_h, yaw, pitch, src.shape[1], src.shape[0])
        img = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        dmx, dmy = (mx * (dist.shape[1] / src.shape[1]), my * (dist.shape[0] / src.shape[0])) if src.shape != dist.shape[:2] + (3,) else (mx, my)
        dep = cv2.remap(dist, dmx, dmy, cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)
        lv = self.light_level(t); dark = lv < 0.12
        with self.wlock:
            ws = list(self.walkers); cars = list(self.cars)
        if vid is not None and not self.video_figures:
            ws, cars = [], []                                            # the video brings its own visitors
        items = [(w.az_dist()[1], lambda im, dp, w=w: self._walker(im, dp, v, w)) for w in ws]
        items += [(OBJECTS["road"][1] + 1.5, lambda im, dp, c=c: self._car(im, dp, v, c)) for c in cars]
        if photo is None:
            items += self._drawables(v, t)
        for _d, fn in sorted(items, key=lambda x: -x[0]):
            fn(img, dep)
        emit = dep < 0; dep = np.abs(dep)                                # things that shine by themselves (a lit window)
        sky = dep >= FAR * 0.9
        alb = img.astype(np.float32)                                     # colours as in daylight
        if vid is not None:
            k = np.ones((H, W), np.float32)                              # a video is already as bright as it was filmed
        else:
            k = np.where(sky, self.sky_k(t) if photo is not None else 1.0, self.ambient_k(t)).astype(np.float32)
        k[emit] = 1.0
        f = alb * k[..., None]
        # artificial light: falls off with the distance (depth buffer), only where the lamp shines
        if dark or lv < 0.4:
            add = np.zeros((H, W), np.float32); warm = None
            dd = np.maximum(dep, 1.5)
            if st.lights.white and info.on_head:
                cone = np.clip(1.0 - ang / 38.0, 0, 1) ** 1.5
                add += 2.2 * cone * np.minimum(1.0, (5.0 / dd) ** 2) * float(st.lights.white_level)
            if st.lights.ir and info.noir:
                cone = np.clip(1.0 - ang / 55.0, 0, 1)
                add += 1.6 * cone * np.minimum(1.0, (4.0 / dd) ** 2) * float(st.lights.ir_level)
            if self.door_open and lv < 0.12:                          # light from the open caravan door
                az, d = OBJECTS["caravan"]; p = v.ground(az + 8.5, d - 1, 0.0)
                if p:
                    g = np.zeros((H, W), np.float32); cv2.circle(g, (int(p[0]), int(p[1])), int(v.f * 2.5 / d), 1.0, -1)
                    add += cv2.GaussianBlur(g, (0, 0), v.f * 1.2 / d + 1) * 0.6 * (dep < 60)
            if vid is not None:                                          # dark video: the lamp brings out what is near
                f = f + (alb * 2.5 + 22.0) * 0.55 * add[..., None] * (~sky & ~emit)[..., None]
            else:
                f = f + alb * 0.55 * add[..., None] * (~sky & ~emit)[..., None]       # the sky gets no lamp light
        # haze and fog grow with the distance
        vis = VISIBILITY.get(self.weather, 6000.0)
        haze = np.where(dep >= FAR * 0.9, 1.0 - math.exp(-300.0 / vis), 1.0 - np.exp(-dep / vis)).astype(np.float32)
        hcol = np.array([182, 180, 176], np.float32) * max(0.04, min(1.0, lv * 1.2))
        if vid is None or self.weather not in ("clear", "cloudy"):        # a video already has its own haze
            f = f * (1 - haze[..., None]) + hcol * haze[..., None]
        img = np.clip(f, 0, 255).astype(np.uint8)
        for c in cars if dark else []:                               # headlights: bright points with glare
            if c.get("_scr"):
                x, y, r, d = c["_scr"]
                g = np.zeros_like(img); cv2.circle(g, (x, y), r * 4, (210, 230, 240), -1)
                img = cv2.addWeighted(img, 1.0, cv2.GaussianBlur(g, (0, 0), r + 1), 0.7, 0)
                cv2.circle(img, (x, y), max(2, r // 2), (245, 252, 255), -1, cv2.LINE_AA)
        if info.noir and st.lights.ir and dark and not st.lights.white:
            g_ = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); img = cv2.cvtColor(g_, cv2.COLOR_GRAY2BGR)
        img = self._weather(img, dep, dark)
        img = self._lens(img, cam, dark, st.lights.ir)
        out = self._camera(img, cam, st.servo.moving and info.on_head, dark)
        if self.osd:
            hh = self.hour(t)
            txt = time.strftime("%d.%m.%Y ", time.localtime(t)) + "%02d:%02d:%02d" % (int(hh), int(hh % 1 * 60), int(hh * 3600 % 60))
            txt += f"  CAM {cam}" + (f"  P{st.servo.pan:.0f} T{st.servo.tilt:.0f}" if info.on_head else "")
            cv2.putText(out, txt, (11, H - 11), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(out, txt, (10, H - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1, cv2.LINE_AA)
        return out

    def _weather(self, img, dep, dark):
        H, W = img.shape[:2]; rng = np.random.default_rng()
        if self.weather == "rain":
            ov = np.zeros((H, W), np.uint8)
            for _ in range(int(W * H / 1800)):
                x, y = int(rng.integers(0, W)), int(rng.integers(0, H)); L = int(rng.integers(6, 28))
                cv2.line(ov, (x, y), (x + L // 6 + int(self.wind / 15), y + L), 255, 1 if L < 20 else 2, cv2.LINE_AA)
            ov = cv2.GaussianBlur(ov, (0, 0), 0.8).astype(np.float32)[..., None] / 255.0
            img = np.clip(img.astype(np.float32) * 0.82 + ov * (90 if not dark else 35), 0, 255).astype(np.uint8)
        elif self.weather == "snow":
            ov = np.zeros((H, W), np.uint8)
            for _ in range(int(W * H / 1500)):
                x, y = int(rng.integers(0, W)), int(rng.integers(0, H)); cv2.circle(ov, (x, y), int(rng.integers(1, 4)), 255, -1, cv2.LINE_AA)
            ov = cv2.GaussianBlur(ov, (0, 0), 0.7).astype(np.float32)[..., None] / 255.0
            img = np.clip(img.astype(np.float32) * (1 - ov * 0.9) + 235 * ov * 0.9 * (1 if not dark else 0.35), 0, 255).astype(np.uint8)
        return img

    def _lens(self, img, cam, dark, ir):
        H, W = img.shape[:2]
        if ir and dark and self.insects > 0 and cam == 0:
            if len(self._bugs) < int(14 * self.insects):
                self._bugs.append([random.uniform(0, W), random.uniform(0, H), random.uniform(-30, 30), random.uniform(-30, 30), random.uniform(2, 12)])
            ov = np.zeros((H, W), np.uint8)
            for b in self._bugs:
                b[0] += b[2] + random.uniform(-10, 10); b[1] += b[3] + random.uniform(-10, 10)
                cv2.circle(ov, (int(b[0]), int(b[1])), int(b[4]), 255, -1, cv2.LINE_AA)
            self._bugs = [b for b in self._bugs if -50 < b[0] < W + 50 and -50 < b[1] < H + 50]
            ov = cv2.GaussianBlur(ov, (0, 0), 4).astype(np.float32)[..., None] / 255.0       # out of focus: soft bright blobs
            img = np.clip(img.astype(np.float32) + ov * 220, 0, 255).astype(np.uint8)
        if self.web and cam == 0:
            k = ("web", W, H)
            if k not in self._cache:
                m = np.zeros((H, W), np.uint8); cx, cy = int(W * 0.18), int(H * 0.2)
                for a in range(0, 360, 28):
                    cv2.line(m, (cx, cy), (int(cx + 450 * math.cos(math.radians(a))), int(cy + 450 * math.sin(math.radians(a)))), 255, 1, cv2.LINE_AA)
                for r in range(25, 450, 34):
                    pts = [(int(cx + r * (1 + 0.08 * math.sin(a * 3)) * math.cos(math.radians(a))), int(cy + r * math.sin(math.radians(a)))) for a in range(0, 361, 10)]
                    cv2.polylines(m, [np.array(pts, np.int32)], False, 255, 1, cv2.LINE_AA)
                self._cache[k] = cv2.GaussianBlur(m, (0, 0), 2.0)
            m = self._cache[k][..., None].astype(np.float32) / 255.0
            img = np.clip(img * (1 - 0.5 * m) + 230 * 0.5 * m * (0.5 if dark else 1), 0, 255).astype(np.uint8)
        if self.dew > 0 and cam == 0:
            b = cv2.GaussianBlur(img, (0, 0), 2 + 16 * self.dew)
            img = cv2.addWeighted(b, 1 - 0.4 * self.dew, np.full_like(img, 170 if not dark else 55), 0.4 * self.dew, 0)
        return img

    def _noise_bank(self, W, H):
        k = ("noise", W, H)
        if k not in self._cache:
            rng = np.random.default_rng(1)
            self._cache[k] = ([rng.normal(0, 1, (H, W)).astype(np.float32) for _ in range(3)],
                              [cv2.resize(rng.normal(0, 1, (H // 2, W // 2, 3)).astype(np.float32), (W, H)) for _ in range(4)])
        return self._cache[k]

    def _camera(self, img, cam, moving, dark):
        """Auto exposure (with a little delay), glare, noise (stronger and coloured at night), vignetting, motion blur."""
        H, W = img.shape[:2]
        f = img.astype(np.float32)
        mean = max(1.0, float(f[H // 3::12, ::12].mean()))               # metering on the lower part (where things happen)
        want = float(np.clip(100.0 / mean, 0.6, 6.0))
        self.exposure[cam] += (want - self.exposure[cam]) * 0.12
        g = self.exposure[cam]
        f *= g
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if cv2.minMaxLoc(gray)[1] > 200:                                # glare around really bright light (computed small)
            sm = cv2.resize(gray, (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
            bright = np.clip(sm * g - 235, 0, None) * (sm > 200)
            f += cv2.resize(cv2.GaussianBlur(bright, (0, 0), 2.3), (W, H))[..., None] * 1.2
        k = ("vig", W, H)
        if k not in self._cache:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
            self._cache[k] = (1.0 - 0.3 * r ** 2.2)[..., None]
        f *= self._cache[k]
        sig = self.noise * (1.2 + 3.0 * g)
        nb = self._noise_bank(W, H)                                    # pre-made noise (making new noise costs much CPU)
        n1 = nb[0][random.randrange(len(nb[0]))]
        f += (np.roll(n1, (random.randrange(H), random.randrange(W)), (0, 1)) * sig)[..., None]   # brightness noise
        if g > 2.0:
            f += nb[1][random.randrange(len(nb[1]))] * (sig * 0.6)                           # colour noise (blotchy)
        out = np.clip(f, 0, 255).astype(np.uint8)
        if moving:
            out = cv2.blur(out, (17, 1))
        return out

    # ---- the thermal camera -----------------------------------------------------------------------------------------
    def render_thermal(self, st, t):
        th = self.info.thermal; w, h = th["w"], th["h"]
        S = 4; W, H = w * S, h * S                                      # drawn 4x finer, then the optics blur it down
        yaw, pitch = st.servo.pan_deg, st.servo.tilt_deg - 6.0
        v = View(W, H, th["fov_h"], yaw, pitch)
        vid = self._vid()
        T = vid.temp_map(self.ambient, self.clouds(), 0.0 if vid.night() else 0.8) if vid is not None else None
        if T is None:
            T = self._world_temp(t); vid = None
        mx, my, _a = eq_maps(W, H, th["fov_h"], yaw, pitch, T.shape[1], T.shape[0])
        a = cv2.remap(T, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        amb = self.ambient; sun = max(0.0, self.sun_el(t)) / 50.0; hour = self.hour(t)
        evening = 1.0 if 17 <= hour or hour < 1 else 0.0
        wet = 2.0 if self.weather == "rain" else 0.0
        dep = np.full((H, W), FAR, np.float32)
        items = []
        for tr_ in self.trees:                                          # trees: cooler than the ground by day, warmer than the sky
            def tree(az=tr_[0], d=tr_[1], s=tr_[2]):
                base = v.ground(az, d); top = v.ground(az, d, 6.0 * s)
                if base and top:
                    r = max(1, int((base[1] - top[1]) * 0.33)); c = (int(top[0]), int(top[1] + r))
                    cv2.circle(a, c, r, amb - 2 + 2 * (1 - sun) - wet, -1); cv2.line(a, (int(base[0]), int(base[1])), c, amb - 1, max(1, r // 4))
            items.append((tr_[1], tree))
        az, d = OBJECTS["caravan"]
        def caravan():
            q = [v.ground(az + k, d, hh) for k, hh in ((-14, 0.3), (14, 0.3), (14, 2.6), (-14, 2.6))]
            if all(q):
                tw = amb + 6 * sun + 3.0 * evening - wet                 # walls: warm from the sun, inside heated in the evening
                cv2.fillPoly(a, [np.array(q, np.int32)], tw)
                win = [v.ground(az + k, d - 0.05, hh) for k, hh in ((-11, 1.3), (-4, 1.3), (-4, 2.0), (-11, 2.0))]
                if all(win):
                    cv2.fillPoly(a, [np.array(win, np.int32)], tw + 3)
                if self.door_open:
                    dr = [v.ground(az + k, d - 0.05, hh) for k, hh in ((6, 0.4), (11, 0.4), (11, 2.3), (6, 2.3))]
                    if all(dr):
                        cv2.fillPoly(a, [np.array(dr, np.int32)], 21.0)   # warm air from inside
        items.append((d, caravan))
        az2, d2 = OBJECTS["tent"]
        def tent():
            q = [v.ground(az2 + k, d2, hh) for k, hh in ((-9, 0), (0, 1.6), (9, 0))]
            if all(q):
                cv2.fillPoly(a, [np.array(q, np.int32)], amb + 4 * sun + 1.5 - wet)
        items.append((d2, tent))
        for az3, d3 in self.stones:                                     # stones: hot in the sun, they give it back in the evening
            def stone(az3=az3, d3=d3):
                c = v.ground(az3, d3, 0.1)
                if c:
                    cv2.circle(a, (int(c[0]), int(c[1])), max(1, int(v.f * 0.25 / d3)), amb + 14 * sun + 4 * evening * (1 - sun) - wet, -1)
            items.append((d3, stone))
        with self.wlock:
            ws = list(self.walkers); cars = list(self.cars)
        if vid is not None:                                             # the video: no drawn caravan, tent, trees
            items = []
            if not self.video_figures:
                ws, cars = [], []
        for wk in ws:
            def body(wk=wk):
                az4, d4 = wk.az_dist(); foot = v.ground(az4, d4); top = v.ground(az4, d4, KINDS[wk.kind][0])
                if not foot or not top:
                    return
                hp = max(1.0, foot[1] - top[1]); x, y = int(foot[0]), int(foot[1]); skin = KINDS[wk.kind][3] - wet
                if wk.kind == "person":
                    cloth = skin - 7.0 - (amb < 10) * 3.0              # a jacket is much cooler than the face
                    cv2.line(a, (x, int(y - hp * 0.48)), (x, y), cloth - 1.5, max(1, int(hp * 0.16)))
                    cv2.line(a, (x, int(y - hp * 0.48)), (x, int(y - hp * 0.8)), cloth, max(1, int(hp * 0.22)))
                    cv2.circle(a, (x, int(y - hp * 0.91)), max(1, int(hp * 0.07)), skin + 1.0, -1)
                    for k in (-1, 1):
                        cv2.circle(a, (x + k * int(hp * 0.1), int(y - hp * 0.48)), max(1, int(hp * 0.03)), skin - 2, -1)   # hands
                else:
                    L = KINDS[wk.kind][1] / KINDS[wk.kind][0] * hp; by = int(y - hp * 0.55)
                    cv2.ellipse(a, (x, by), (max(1, int(L * 0.5)), max(1, int(hp * 0.22))), 0, 0, 360, skin - 3, -1)
                    for k in (-0.33, 0.33):
                        cv2.line(a, (int(x + k * L), by), (int(x + k * L), y), skin - 6, max(1, int(hp * 0.06)))
                    hx = int(x + wk.dir * L * 0.55); cv2.circle(a, (hx, int(by - hp * 0.12)), max(1, int(hp * 0.16)), skin, -1)
                    cv2.circle(a, (hx + wk.dir * max(1, int(hp * 0.06)), int(by - hp * 0.16)), max(1, int(hp * 0.04)), 36.5, -1)     # eye
            items.append((wk.az_dist()[1], body))
        for c in cars:
            def car(c=c):
                d5 = OBJECTS["road"][1] + 1.5; az5 = math.degrees(math.atan2(c["x"], d5))
                p0 = v.ground(az5 - math.degrees(2.2 / d5), d5, 0.0); p1 = v.ground(az5 + math.degrees(2.2 / d5), d5, 1.45)
                if p0 and p1:
                    x0, x1 = sorted((int(p0[0]), int(p1[0]))); y1, y0 = int(p0[1]), int(p1[1])
                    cv2.rectangle(a, (x0, y0), (x1, y1), amb + 4, -1)
                    eng = (x1 - (x1 - x0) // 5, (y0 + y1) // 2) if c["dir"] > 0 else (x0 + (x1 - x0) // 5, (y0 + y1) // 2)
                    cv2.circle(a, eng, max(1, (y1 - y0) // 3), amb + 45, -1)                       # hot engine
                    cv2.circle(a, ((x0 if c["dir"] > 0 else x1), y1 - 2), max(1, (y1 - y0) // 6), amb + 60, -1)   # exhaust
            items.append((OBJECTS["road"][1] + 1.5, car))
        for _d, fn in sorted(items, key=lambda x: -x[0]):
            fn()
        if st.lights.white:
            cv2.circle(a, (W // 2, 6), 8, amb + 35, -1)                 # the floodlight housing gets warm
        vis = VISIBILITY.get(self.weather, 6000.0)
        if vis < 1000:                                                  # fog / rain: everything closer to the air temperature
            a = amb + (a - amb) * (0.35 if vis < 100 else 0.7)
        a = cv2.GaussianBlur(a, (0, 0), S * 0.7)                        # optics
        a = cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA)
        rng = np.random.default_rng(); a += rng.normal(0, 0.08, a.shape).astype(np.float32)        # sensor noise (NETD)
        if "fpn" not in self._cache:
            self._cache["fpn"] = (np.random.default_rng(9).normal(0, 0.04, (1, w)) + np.random.default_rng(10).normal(0, 0.02, (h, 1))).astype(np.float32)
        a += self._cache["fpn"]                                        # stripes of the sensor (fixed pattern)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        a -= 0.6 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)            # slightly cooler edges
        return a.astype(np.float32)


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
    root = tk.Tk(); root.title(f"{SIM_NAME} {SIM_VERSION}"); root.configure(bg=BG)
    try:
        root._icon = tk.PhotoImage(data=SIM_ICON); root.iconphoto(True, root._icon)
    except Exception:
        pass
    sty = ttk.Style(); sty.theme_use("clam")
    left = tk.Frame(root, bg=BG); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
    right = tk.Frame(root, bg=BG); right.pack(side="right", fill="y", padx=8, pady=8)
    prev = [tk.Label(left, bg="#000"), None, None]
    prev[0].pack(fill="x"); row = tk.Frame(left, bg=BG); row.pack(fill="x", pady=(6, 0))
    prev[1] = tk.Label(row, bg="#000"); prev[1].pack(side="left"); prev[2] = tk.Label(row, bg="#000"); prev[2].pack(side="left", padx=(6, 0))
    status = tk.Label(left, text="", bg=BG, fg=FG, justify="left", anchor="w", font=("DejaVu Sans Mono", 9)); status.pack(fill="x", pady=(6, 0))
    upd = tk.Label(left, text="", bg=BG, fg="#d29922", anchor="w"); upd.pack(fill="x")
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

    t1 = tab("Szene")
    lab(t1, "UHRZEIT")
    hs = slider(t1, "Stunde", 0, 23.75, lambda: round(sim.hour(), 2), sim.set_hour, 0.25)
    bf = tk.Frame(t1, bg=BG); bf.pack(fill="x")
    for txt, h in (("Mittag", 12.5), ("Abend", 19.4), ("Nacht", 23.0), ("Morgen", 6.4)):
        ttk.Button(bf, text=txt, command=lambda h=h: (sim.set_hour(h), hs.set(h))).pack(side="left", expand=True, fill="x")
    slider(t1, "Zeit läuft x-fach", 1, 120, lambda: sim.speed, lambda v: (sim.set_hour(sim.hour()), setattr(sim, "speed", v)), 1)
    slider(t1, "Mond", 0, 1, lambda: sim.moon, lambda v: setattr(sim, "moon", v), 0.1)
    lab(t1, "BESUCH")
    g = tk.Frame(t1, bg=BG); g.pack(fill="x")
    for i, (k, l) in enumerate((("person", "Person"), ("fox", "Fuchs"), ("boar", "Wildschwein"), ("deer", "Reh"), ("cat", "Katze"))):
        ttk.Button(g, text=l, command=lambda k=k: sim.spawn(k)).grid(row=i // 3, column=i % 3, sticky="ew", padx=1, pady=1)
    ttk.Button(g, text="Auto", command=sim.car).grid(row=1, column=2, sticky="ew", padx=1, pady=1)
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
    lab(t1, "MOTION WATCH AUF HANDY / TABLET")

    def preview():
        if not sim.mw_addr:
            sim.update_msg = "Motion Watch ist noch nicht verbunden - zuerst in Motion Watch die Simulation einschalten."
            return
        import webbrowser
        st_ = sim.state
        webbrowser.open(f"{st_.mw_scheme}://{sim.mw_addr}:{st_.mw_port}/preview")
    ttk.Button(t1, text="Handy- / Tablet-Ansicht öffnen (Browser)", command=preview).pack(fill="x")
    lab(t1, "VIDEO-SZENARIO (360° ODER NORMAL)")
    vids = {}
    vcb = ttk.Combobox(t1, state="readonly", width=34)

    def refresh_videos():
        vids.clear(); vids.update({n: p for n, p in video_list()})
        vcb["values"] = list(vids) or ["(keine Videos im Ordner sim_assets/videos)"]
        if vids and not vcb.get() in vids:
            vcb.set(next(iter(vids)))
    refresh_videos(); vcb.pack(fill="x")

    def play():
        if vcb.get() in vids:
            sim.load_video(vids[vcb.get()])

    def pick_video():
        p = filedialog.askopenfilename(title="Video-Szenario", filetypes=[("Videos", " ".join("*" + e for e in VIDEO_EXT))])
        if p:
            sim.load_video(p)
    vf = tk.Frame(t1, bg=BG); vf.pack(fill="x")
    ttk.Button(vf, text="Abspielen", command=play).pack(side="left", expand=True, fill="x")
    ttk.Button(vf, text="Anderes …", command=pick_video).pack(side="left", expand=True, fill="x")
    ttk.Button(vf, text="Stopp", command=lambda: sim.load_video(None)).pack(side="left", expand=True, fill="x")
    ttk.Button(vf, text="↻", width=3, command=refresh_videos).pack(side="left")

    def open_folder():
        import subprocess
        os.makedirs(VIDEO_DIR, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(VIDEO_DIR)
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", VIDEO_DIR])
        except Exception:
            pass
    ttk.Button(t1, text="Video-Ordner öffnen", command=open_folder).pack(fill="x")
    ttk.Button(t1, text="Beispiel-Videoszenen erzeugen (Wald, Parkplatz, Camping)", command=sim.make_demos).pack(fill="x")
    check(t1, "gezeichnete Besucher zusätzlich ins Video", lambda: sim.video_figures, lambda v: setattr(sim, "video_figures", v))
    vmsg = tk.Label(t1, text="", bg=BG, fg=MUT, anchor="w", justify="left", wraplength=330); vmsg.pack(fill="x")
    t2 = tab("Wetter")
    lab(t2, "WETTER")
    wv = tk.StringVar(value=sim.weather)
    for v_, l in (("clear", "klar"), ("cloudy", "bewölkt"), ("rain", "Regen"), ("fog", "Nebel"), ("snow", "Schnee")):
        ttk.Radiobutton(t2, text=l, value=v_, variable=wv, command=lambda: setattr(sim, "weather", wv.get())).pack(anchor="w")
    slider(t2, "Wind km/h", 0, 120, lambda: sim.wind, lambda v: setattr(sim, "wind", v), 1)
    slider(t2, "Temperatur °C", -15, 40, lambda: sim.ambient, lambda v: setattr(sim, "ambient", v))
    slider(t2, "Feuchte %", 10, 100, lambda: sim.humidity, lambda v: setattr(sim, "humidity", v), 1)
    slider(t2, "Luftdruck hPa", 960, 1040, lambda: sim.pressure, lambda v: setattr(sim, "pressure", v))
    ttk.Button(t2, text="Sturm zieht auf (Luftdruck fällt)", command=lambda: setattr(sim, "storm_t", time.time())).pack(fill="x", pady=(6, 0))
    ttk.Button(t2, text="Sturm vorbei", command=lambda: setattr(sim, "storm_t", 0.0)).pack(fill="x")
    t3 = tab("Kamera")
    lab(t3, "LINSE (Linsen-Prüfung, Sabotage)")
    slider(t3, "Tau / beschlagen", 0, 1, lambda: sim.dew, lambda v: setattr(sim, "dew", v), 0.05)
    check(t3, "Spinnennetz vor der Linse", lambda: sim.web, lambda v: setattr(sim, "web", v))
    check(t3, "Kamera abgedeckt (Hand davor)", lambda: sim.covered, lambda v: setattr(sim, "covered", v))
    lab(t3, "FEHLALARM-MACHER")
    slider(t3, "Insekten im IR-Licht", 0, 1, lambda: sim.insects, lambda v: setattr(sim, "insects", v), 0.1)
    lab(t3, "BILD")
    slider(t3, "Bildrauschen", 0, 3, lambda: sim.noise, lambda v: setattr(sim, "noise", v), 0.1)
    check(t3, "Datum / Zeit im Bild", lambda: sim.osd, lambda v: setattr(sim, "osd", v))
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
                im = cv2.cvtColor(sim.frame(i), cv2.COLOR_BGR2RGB)
                im = cv2.resize(im, (w_, int(im.shape[0] * w_ / im.shape[1])))
                ph = ImageTk.PhotoImage(Image.fromarray(im)); prev[i].configure(image=ph); prev[i].image = ph
            th = sim.thermal_frame(); lo, hi = np.percentile(th, (1, 99.5))
            g8 = np.clip((th - lo) / max(0.5, hi - lo) * 255, 0, 255).astype(np.uint8)
            im = cv2.cvtColor(cv2.applyColorMap(cv2.resize(g8, (232, 180), interpolation=cv2.INTER_LINEAR), cv2.COLORMAP_INFERNO), cv2.COLOR_BGR2RGB)
            ph = ImageTk.PhotoImage(Image.fromarray(im)); prev[2].configure(image=ph); prev[2].image = ph
        rl = ", ".join(f"{r.name}={'AN' if r.on else 'aus'}" for r in st.relays) or "-"
        wr = sim.world(t)
        fr = " · ".join(f"K{c}: {sim.fps_out(c):.0f}/s" for c in (0, 1)) + f" · Wärme: {sim.fps_out('th'):.0f}/s"
        status.configure(text=(f"Motion Watch: {'verbunden (' + st.device + ')' if age is not None and age < 3 else 'NICHT verbunden'}   Port {sim.port}   Simulator {SIM_VERSION}\n"
                               f"Abgeholte Bilder: {fr}\n"
                               f"Servos: Schwenk {st.servo.pan:.1f} % ({st.servo.pan_deg:+.0f}°)  Neigung {st.servo.tilt:.1f} % ({st.servo.tilt_deg:+.0f}°)\n"
                               f"Licht: weiss {'AN' if st.lights.white else 'aus'} · IR {'AN' if st.lights.ir else 'aus'}   Relais: {rl}\n"
                               f"Ton: {st.sound or '-'}   Scharf: {'ja' if st.armed else 'nein'}\n"
                               f"Welt: {int(sim.hour()):02d}:{int(sim.hour() % 1 * 60):02d} {'Nacht' if wr.dark else 'Tag'} · {sim.weather} · "
                               f"{wr.ambient_c} °C · {wr.pressure_hpa} hPa · Wind {wr.wind_kmh} km/h · Besucher {len(sim.walkers)}"))
        upd.configure(text=sim.update_msg)
        if sim.video is not None and vcb.get() != sim.video.name and sim.video.name in vids:
            vcb.set(sim.video.name)
        vmsg.configure(text=(f"{sim.video.name}: {sim.video.msg}" if sim.video is not None else "aus – gezeichnete Welt oder 360°-Foto")
                       + (f"\n{sim.demo_msg}" if sim.demo_msg else ""))
        if sim.demo_msg.startswith("Beispiel-Videoszenen fertig") and not getattr(sim, "_demo_shown", False):
            sim._demo_shown = True; refresh_videos()
        root.after(500, tick)
    tick()
    root.mainloop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=f"{SIM_NAME} {SIM_VERSION}")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--no-window", action="store_true", help="without the control window")
    ap.add_argument("--no-update", action="store_true", help="never update itself from Motion Watch")
    ap.add_argument("--hd", action="store_true", help="bigger camera pictures (needs much more CPU)")
    ap.add_argument("--pano", help="own 360° photo (equirectangular 2:1) or a panorama")
    ap.add_argument("--video", help="play this video scenario (360° video or a normal video)")
    ap.add_argument("--hour", type=float, help="start at this hour (e.g. 22.5)")
    ap.add_argument("--night", action="store_true"); ap.add_argument("--day", action="store_true")
    a = ap.parse_args()
    try:
        os.makedirs(VIDEO_DIR, exist_ok=True)                          # here go the video scenarios
    except OSError:
        pass
    sim = CampingSim(a.port, a.pano, autoupdate=not a.no_update, hd=a.hd)
    if a.video:
        sim.load_video(a.video)
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
