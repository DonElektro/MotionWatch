#!/usr/bin/env python3
"""
Motion Watch – simulator  (separate program, protocol: motionwatch_sim_interface.py in the same folder)

A camping place to test Motion Watch without hardware:
  * camera 0 on the pan / tilt head (follows the servo positions of Motion Watch), camera 1 fixed on the caravan,
  * thermal camera (temperatures in °C) next to camera 0,
  * day / dusk / night, white light (cone) and infrared light (NoIR camera: grey picture),
  * people and animals (fox, wild boar, deer) walking by - animals flee from the siren or the white light at night,
  * wind (trees move = test for false alarms), air temperature, air pressure,
  * sensors: caravan door, PIR at the tent, gas detector, Bluetooth tag on the bike.

Start:   python3 motionwatch_simulator.py            (window with the controls)
         python3 motionwatch_simulator.py --no-window --port 8765
Motion Watch: Settings → System & network → Simulator → address http://<this PC>:8765, then the switch «Simulation».
Needs: python3-numpy, python3-opencv; for the window python3-tk and python3-pil.imagetk (preview).
"""
import argparse
import math
import random
import threading
import time

import cv2
import numpy as np

from motionwatch_sim_interface import SimServer, SimInfo, CamInfo, SimReply, DEFAULT_PORT

WORLD_DEG = 240.0            # the panorama covers 240 degrees around the head
PW, PH = 4800, 1600          # panorama pixels  (20 px per degree)
PPD = PW / WORLD_DEG
GROUND = 820                 # horizon line in the panorama
KINDS = {                    # size (height in px at the front), speed (px/s), body temperature
    "person": (330, 90, 34.0), "fox": (95, 160, 37.5), "boar": (130, 110, 38.0), "deer": (230, 140, 38.5)}


class Walker:
    def __init__(self, kind, t):
        self.kind = kind; self.t0 = t
        self.dir = random.choice((-1, 1))
        self.depth = random.uniform(0.45, 1.0)                    # 1 = close to the camera, lower = further away
        self.x = -200.0 if self.dir > 0 else PW + 200.0
        self.speed = KINDS[kind][1] * random.uniform(0.8, 1.2)
        self.fled = False
        self.done = False

    def step(self, dt, scare):
        if scare and not self.fled and self.kind != "person":
            self.dir = -self.dir; self.speed *= 2.2; self.fled = True    # deterrence works: the animal runs away
        self.x += self.dir * self.speed * self.depth * dt
        if self.x < -400 or self.x > PW + 400:
            self.done = True

    def foot_y(self):
        return int(GROUND + 120 + (self.depth - 0.45) / 0.55 * 600)

    def height(self):
        return int(KINDS[self.kind][0] * (0.45 + 0.55 * self.depth))


class CampingSim(SimServer):
    def __init__(self, port=DEFAULT_PORT):
        info = SimInfo(name="Motion Watch camping simulator",
                       cameras=[CamInfo(0, "Head camera (NoIR)", 1280, 720, 12.0, 66.0, 41.0, True, True),
                                CamInfo(1, "Caravan camera", 960, 540, 8.0, 100.0, 60.0, False, False)],
                       thermal={"w": 80, "h": 62, "fps": 8.0, "fov_h": 45.0, "fov_v": 35.0, "unit": "C", "on_head": True},
                       sensors=[{"name": "Wohnwagen-Tür", "kind": "door"}, {"name": "PIR Zelt", "kind": "pir"},
                                {"name": "Gas Wohnwagen", "kind": "gas"}, {"name": "Velo", "kind": "tag"}])
        super().__init__(info, port=port)
        self.mode = "auto"            # auto (clock) | day | dusk | night
        self.ambient = 14.0; self.pressure = 1013.0; self.wind = 5.0; self.auto_walkers = True
        self.walkers = []; self.door_open = False; self.last = time.time(); self.next_auto = time.time() + 20
        self.wlock = threading.Lock()
        self._pano = None; self._masks = {}
        threading.Thread(target=self._life, daemon=True).start()

    # ---- the world -------------------------------------------------------------------------------------------------
    def light_level(self, t):
        if self.mode == "day":
            return 1.0
        if self.mode == "night":
            return 0.06
        if self.mode == "dusk":
            return 0.35
        lt = time.localtime(t); h = lt.tm_hour + lt.tm_min / 60.0
        return float(np.clip(0.06 + 0.94 * (math.sin((h - 6.5) / 13.0 * math.pi) * 1.6), 0.06, 1.0))

    def world(self, t):
        return SimReply(sim_time=t, dark=self.light_level(t) < 0.3, ambient_c=round(self.ambient, 1), pressure_hpa=round(self.pressure, 1),
                        wind_kmh=round(self.wind, 1), last_event=self.events[-1].id if self.events else 0)

    def spawn(self, kind):
        with self.wlock:
            self.walkers.append(Walker(kind, time.time()))

    def _life(self):
        while True:
            now = time.time(); dt = now - self.last; self.last = now
            st = self.state
            scare = bool(st.sound) or (st.lights.white and self.light_level(now) < 0.3)
            with self.wlock:
                for w in self.walkers:
                    w.step(dt, scare)
                    if w.kind == "person" and not w.done and abs(w.x - self._tent_x()) < 40 and not getattr(w, "pir", False):
                        w.pir = True; self.add_event("PIR Zelt", "pir", None)         # walks past the tent
                self.walkers = [w for w in self.walkers if not w.done]
            if self.auto_walkers and now > self.next_auto:
                self.spawn(random.choice(("person", "fox", "fox", "boar", "deer")))
                self.next_auto = now + random.uniform(40, 120)
            time.sleep(0.05)

    @staticmethod
    def _tent_x():
        return PW / 2 + 12 * PPD

    def _panorama(self):
        if self._pano is not None:
            return self._pano
        p = np.zeros((PH, PW, 3), np.uint8)
        for y in range(GROUND):                                          # sky gradient
            k = y / GROUND; p[y] = (int(235 - 40 * k), int(200 - 30 * k), int(140 - 20 * k))
        p[GROUND:] = (55, 135, 65)
        rng = np.random.default_rng(3)
        for x in range(-200, PW + 200, 230):                            # mountains
            h = int(rng.integers(160, 460))
            cv2.fillPoly(p, [np.array([[x - 330, GROUND], [x, GROUND - h], [x + 330, GROUND]])], (125, 118, 108))
        noise = rng.integers(-12, 12, (PH - GROUND, PW, 1)).astype(np.int16)
        p[GROUND:] = np.clip(p[GROUND:].astype(np.int16) + noise, 0, 255).astype(np.uint8)
        cv2.rectangle(p, (0, GROUND + 330), (PW, GROUND + 380), (90, 140, 170), -1)            # gravel path
        cx = int(PW / 2)
        cv2.rectangle(p, (cx - 900, GROUND - 40), (cx - 520, GROUND + 260), (225, 225, 230), -1)   # caravan
        cv2.rectangle(p, (cx - 860, GROUND + 10), (cx - 760, GROUND + 90), (120, 90, 60), -1)
        cv2.rectangle(p, (cx - 640, GROUND + 40), (cx - 570, GROUND + 250), (80, 80, 90), -1)     # its door
        tx = int(self._tent_x())
        cv2.fillPoly(p, [np.array([[tx - 230, GROUND + 330], [tx, GROUND + 60], [tx + 230, GROUND + 330]])], (40, 130, 230))
        cv2.rectangle(p, (cx + 700, GROUND + 230), (cx + 860, GROUND + 300), (40, 40, 40), 4)          # the bike
        self.trees = [int(x) for x in rng.integers(0, PW, 26)]
        self._pano = p
        return p

    def _draw_walker(self, img, w):
        x, fy, h = int(w.x), w.foot_y(), w.height()
        if w.kind == "person":
            cv2.rectangle(img, (x - h // 8, fy - int(h * 0.75)), (x + h // 8, fy - int(h * 0.3)), (60, 60, 170), -1)
            cv2.line(img, (x - h // 14, fy - int(h * 0.3)), (x - h // 10 + int(10 * math.sin(time.time() * 6)), fy), (40, 40, 60), max(4, h // 20))
            cv2.line(img, (x + h // 14, fy - int(h * 0.3)), (x + h // 10 - int(10 * math.sin(time.time() * 6)), fy), (40, 40, 60), max(4, h // 20))
            cv2.circle(img, (x, fy - int(h * 0.86)), max(8, h // 9), (150, 180, 225), -1)
        else:
            col = {"fox": (40, 110, 220), "boar": (40, 45, 60), "deer": (50, 100, 150)}[w.kind]
            bl = int(h * (1.4 if w.kind != "deer" else 0.9)); bh = int(h * (0.45 if w.kind != "deer" else 0.35))
            top = fy - h + (0 if w.kind == "deer" else int(h * 0.3))
            body_y = fy - int(h * (0.35 if w.kind != "deer" else 0.55))
            cv2.ellipse(img, (x, body_y), (bl // 2, bh // 2), 0, 0, 360, col, -1)
            hx = x + w.dir * bl // 2
            cv2.circle(img, (hx, body_y - bh // 3), max(6, bh // 2), col, -1)
            for k in (-1, 1):
                cv2.line(img, (x + k * bl // 3, body_y), (x + k * bl // 3, fy), col, max(3, h // 18))
            if w.kind == "fox":
                cv2.line(img, (x - w.dir * bl // 2, body_y), (x - w.dir * int(bl * 0.9), body_y + bh // 3), col, max(6, h // 6))

    def _scene(self, t):
        img = self._panorama().copy()
        sway = self.wind / 50.0
        for i, x in enumerate(self.trees):                                  # trees move with the wind
            dx = int(sway * 18 * math.sin(t * 2.3 + i))
            cv2.rectangle(img, (x - 10, GROUND + 60), (x + 10, GROUND + 170), (40, 60, 90), -1)
            cv2.circle(img, (x + dx, GROUND + 25), 70, (40, 105, 45), -1)
        cx = int(PW / 2)
        if self.door_open:
            cv2.rectangle(img, (cx - 640, GROUND + 40), (cx - 570, GROUND + 250), (30, 30, 30), -1)
            cv2.rectangle(img, (cx - 700, GROUND + 40), (cx - 640, GROUND + 250), (80, 80, 90), -1)
        with self.wlock:
            ws = sorted(self.walkers, key=lambda w: w.depth)
        for w in ws:
            self._draw_walker(img, w)
        return img

    def _mask(self, W, H):
        k = (W, H)
        if k not in self._masks:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            self._masks[k] = np.exp(-(((xx - W / 2) / (W * 0.33)) ** 2 + ((yy - H * 0.62) / (H * 0.5)) ** 2))
        return self._masks[k]

    # ---- the interface ---------------------------------------------------------------------------------------------
    def render_camera(self, cam, st, t):
        info = self.info.cameras[cam]; W, H = info.w, info.h
        scene = self._scene(t)
        if info.on_head:
            cx = PW / 2 + st.servo.pan_deg * PPD; cy = GROUND + 150 - st.servo.tilt_deg * PPD
        else:
            cx, cy = PW / 2 - 300, GROUND + 200
        vw, vh = info.fov_h * PPD, info.fov_v * PPD
        x0 = int(max(0, min(PW - vw, cx - vw / 2))); y0 = int(max(0, min(PH - vh, cy - vh / 2)))
        img = cv2.resize(scene[y0:y0 + int(vh), x0:x0 + int(vw)], (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)
        lv = self.light_level(t)
        light = np.full((H, W), lv, np.float32)
        if lv < 0.5:
            if st.lights.white and info.on_head:
                light = light + 0.95 * self._mask(W, H) * float(st.lights.white_level)
            if st.lights.ir and info.noir:
                light = light + 0.5 * float(st.lights.ir_level)
            if not info.on_head and self.door_open:
                light = light + 0.3                                                  # light from the open caravan door
        img = img * np.minimum(light, 1.15)[..., None]
        if info.noir and st.lights.ir and lv < 0.5 and not st.lights.white:
            g = img.mean(axis=2); img = np.repeat(g[..., None], 3, axis=2)
        img = img + np.random.default_rng().normal(0, 7 if lv < 0.3 else 2, img.shape)
        out = np.clip(img, 0, 255).astype(np.uint8)
        txt = f"SIM {cam}  pan {st.servo.pan:.0f}%  tilt {st.servo.tilt:.0f}%" if info.on_head else f"SIM {cam}  caravan"
        if st.sound:
            txt += f"  [sound: {st.sound}]"
        cv2.putText(out, txt + time.strftime("  %H:%M:%S"), (10, H - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return out

    def render_thermal(self, st, t):
        th = self.info.thermal; w, h = th["w"], th["h"]
        a = np.full((h, w), self.ambient, np.float32)
        a[: int(h * 0.45)] -= 6.0                                                    # the sky is cold
        a += np.random.default_rng().normal(0, 0.12, (h, w)).astype(np.float32)
        cx = PW / 2 + st.servo.pan_deg * PPD; cy = GROUND + 150 - st.servo.tilt_deg * PPD
        vw, vh = th["fov_h"] * PPD, th["fov_v"] * PPD
        x0, y0 = cx - vw / 2, cy - vh / 2
        with self.wlock:
            ws = list(self.walkers)
        for wk in ws:
            fx, fy, hh = (wk.x - x0) / vw * w, (wk.foot_y() - y0) / vh * h, wk.height() / vh * h
            if -10 < fx < w + 10 and -10 < fy < h + hh:
                temp = KINDS[wk.kind][2] - 3.0 + random.uniform(-0.3, 0.3)          # skin / fur surface
                if wk.kind == "person":
                    cv2.ellipse(a, (int(fx), int(fy - hh * 0.5)), (max(1, int(hh * 0.12)), max(2, int(hh * 0.45))), 0, 0, 360, temp, -1)
                else:
                    cv2.ellipse(a, (int(fx), int(fy - hh * 0.4)), (max(2, int(hh * 0.6)), max(1, int(hh * 0.25))), 0, 0, 360, temp, -1)
        if st.lights.white:
            cv2.circle(a, (w // 2, 2), 2, self.ambient + 30, -1)
        return a

    def on_state(self, st):
        pass

    # ---- sensors ---------------------------------------------------------------------------------------------------
    def door(self, open_):
        self.door_open = bool(open_); self.add_event("Wohnwagen-Tür", "door", self.door_open)

    def gas(self, on):
        self.add_event("Gas Wohnwagen", "gas", bool(on))


# ----------------------------------------------------------------------------------------------------------------------
# The control window (no colour emoji: they can crash Tk on the Raspberry Pi)
# ----------------------------------------------------------------------------------------------------------------------
def window(sim):
    import tkinter as tk
    from tkinter import ttk
    try:
        from PIL import Image, ImageTk
    except ImportError:
        Image = ImageTk = None
    root = tk.Tk(); root.title("Motion Watch – Simulator"); root.configure(bg="#161b22")
    st_ = ttk.Style(); st_.theme_use("clam")
    left = tk.Frame(root, bg="#161b22"); left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
    right = tk.Frame(root, bg="#161b22"); right.pack(side="right", fill="y", padx=8, pady=8)
    prev = [tk.Label(left, bg="#000") for _ in range(2)]
    prev[0].pack(fill="x"); prev[1].pack(fill="x", pady=(6, 0))
    status = tk.Label(left, text="", bg="#161b22", fg="#c9d1d9", justify="left", anchor="w", font=("DejaVu Sans Mono", 9))
    status.pack(fill="x", pady=(6, 0))

    def lab(t_):
        tk.Label(right, text=t_, bg="#161b22", fg="#8b949e", font=("DejaVu Sans", 8, "bold"), anchor="w").pack(fill="x", pady=(8, 2))

    lab("TAG / NACHT")
    mv = tk.StringVar(value=sim.mode)
    for v, l in (("auto", "Uhrzeit"), ("day", "Tag"), ("dusk", "Dämmerung"), ("night", "Nacht")):
        ttk.Radiobutton(right, text=l, value=v, variable=mv, command=lambda: setattr(sim, "mode", mv.get())).pack(anchor="w")
    lab("BESUCH")
    for k, l in (("person", "Person"), ("fox", "Fuchs"), ("boar", "Wildschwein"), ("deer", "Reh")):
        ttk.Button(right, text=l, command=lambda k=k: sim.spawn(k)).pack(fill="x", pady=1)
    av = tk.BooleanVar(value=sim.auto_walkers)
    ttk.Checkbutton(right, text="ab und zu von selbst", variable=av, command=lambda: setattr(sim, "auto_walkers", av.get())).pack(anchor="w")
    lab("SENSOREN")
    dv = tk.BooleanVar(value=False)
    ttk.Checkbutton(right, text="Wohnwagentür offen", variable=dv, command=lambda: sim.door(dv.get())).pack(anchor="w")
    gv = tk.BooleanVar(value=False)
    ttk.Checkbutton(right, text="Gas / Rauch", variable=gv, command=lambda: sim.gas(gv.get())).pack(anchor="w")
    ttk.Button(right, text="Velo bewegen", command=lambda: sim.add_event("Velo", "tag", None)).pack(fill="x", pady=1)
    ttk.Button(right, text="PIR Zelt auslösen", command=lambda: sim.add_event("PIR Zelt", "pir", None)).pack(fill="x", pady=1)
    lab("WETTER")

    def slider(text, lo, hi, attr, res=0.5):
        f = tk.Frame(right, bg="#161b22"); f.pack(fill="x")
        tk.Label(f, text=text, bg="#161b22", fg="#c9d1d9", width=14, anchor="w").pack(side="left")
        s = tk.Scale(f, from_=lo, to=hi, orient="horizontal", resolution=res, bg="#161b22", fg="#c9d1d9", highlightthickness=0,
                     length=160, command=lambda v: setattr(sim, attr, float(v)))
        s.set(getattr(sim, attr)); s.pack(side="left")
    slider("Temperatur °C", -15, 40, "ambient")
    slider("Luftdruck hPa", 960, 1040, "pressure")
    slider("Wind km/h", 0, 120, "wind", 1)

    def tick():
        st = sim.state; age = time.time() - sim.state_t if sim.state_t else None
        t = time.time()
        if Image is not None:
            for i, w_ in ((0, 560), (1, 420)):
                im = cv2.cvtColor(sim.render_camera(i, st, t), cv2.COLOR_BGR2RGB)
                im = cv2.resize(im, (w_, int(im.shape[0] * w_ / im.shape[1])))
                ph = ImageTk.PhotoImage(Image.fromarray(im)); prev[i].configure(image=ph); prev[i].image = ph
        rl = ", ".join(f"{r.name}={'AN' if r.on else 'aus'}" for r in st.relays) or "–"
        status.configure(text=(f"Motion Watch: {'verbunden (' + st.device + ')' if age is not None and age < 3 else 'NICHT verbunden'}\n"
                               f"Servos: Schwenk {st.servo.pan:.1f} % ({st.servo.pan_deg:+.0f}°)  Neigung {st.servo.tilt:.1f} % ({st.servo.tilt_deg:+.0f}°)\n"
                               f"Licht: weiss {'AN' if st.lights.white else 'aus'} · IR {'AN' if st.lights.ir else 'aus'}   Relais: {rl}\n"
                               f"Ton: {st.sound or '–'}   Scharf: {'ja' if st.armed else 'nein'}   "
                               f"{'Nacht' if sim.world(t).dark else 'Tag'} · Besucher: {len(sim.walkers)}   Port {sim.port}"))
        root.after(400, tick)
    tick()
    root.mainloop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Motion Watch camping simulator")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--no-window", action="store_true", help="without the control window")
    ap.add_argument("--night", action="store_true"); ap.add_argument("--day", action="store_true")
    a = ap.parse_args()
    sim = CampingSim(a.port)
    if a.night:
        sim.mode = "night"
    elif a.day:
        sim.mode = "day"
    if a.no_window:
        sim.serve_forever()
    else:
        threading.Thread(target=sim.serve_forever, daemon=True).start()
        window(sim)
