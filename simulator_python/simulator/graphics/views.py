"""The two map views of the panel: a top-down map and a 3D view you can orbit around. Both turn a mouse position
into a point on the ground, so the panel can send visitors there, place / move things and move the camera."""
import math

import cv2
import numpy as np

from simulator.scene import maps
from simulator.config import SIM
from simulator.graphics.render import CamModel, Renderer, _ipt, _noise_tex, cull
from simulator.scene.world import KINDS, VEHICLES

_TEX = {}

ICON_COL = {"person": (60, 60, 230), "dog": (40, 110, 200), "cat": (160, 160, 170), "bear": (30, 45, 90), "horse": (50, 120, 170),
            "sheep": (230, 230, 230), "bird": (20, 20, 20), "car": (200, 120, 30), "truck": (150, 80, 20), "bicycle": (40, 180, 220),
            "motorcycle": (100, 30, 160), "plane": (240, 240, 240)}
LETTER = {"person": "P", "dog": "D", "cat": "C", "bear": "B", "horse": "H", "sheep": "S", "bird": "b", "car": "car",
          "truck": "T", "bicycle": "bi", "motorcycle": "M", "plane": "plane"}


def ground_colour(gx, gy, m, cx=None, cy=None, sharp=True):
    """Colour of the ground of map m at world points gx, gy (arrays), like in the panorama (without haze)."""
    from simulator.scene import ground
    if "f" not in _TEX:
        _TEX["f"] = _noise_tex(1024, 7, 21); _TEX["c"] = _noise_tex(512, 5, 22)
    gx = gx.astype(np.float32); gy = gy.astype(np.float32)
    fine = cv2.remap(_TEX["f"], (gx / 0.05) % 1024, (gy / 0.05) % 1024, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    coarse = cv2.remap(_TEX["c"], (gx / 1.8) % 512, (gy / 1.8) % 512, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    cls = ground.classes(m, gx, gy, cx, cy, sharp=sharp and cx is not None)
    return np.clip(ground.colour(m, cls, fine, coarse), 0, 255).astype(np.uint8)


def nearest(eng, x, y, radius=2.0, what=("ent", "plant", "prop", "camera")):
    """The thing closest to a ground point: ("ent" | "plant" | "prop" | "camera", object)."""
    best, bd = None, radius
    if "camera" in what:
        d = math.hypot(SIM["cam_x"] - x, SIM["cam_y"] - y)
        if d < bd:
            best, bd = ("camera", None), d
    if "ent" in what:
        for e in eng.world.snapshot():
            d = math.hypot(e.x - x, e.y - y)
            if d < bd:
                best, bd = ("ent", e), d
    if "plant" in what:
        for p in eng.world.plants:
            d = math.hypot(p.x - x, p.y - y) - (p.crown * 0.5 if p.kind == "tree" else p.crown)
            if d < bd:
                best, bd = ("plant", p), max(0.0, d)
    if "prop" in what:
        for pr in eng.world.props:
            dx = max(0.0, abs(x - pr.x) - pr.w / 2); dy = max(0.0, abs(y - pr.y) - pr.d / 2)
            d = math.hypot(dx, dy)
            if d < bd:
                best, bd = ("prop", pr), d
    return best


# =====================================================================================================================
class TopView:
    """Map from above. Centre + metres per pixel; the ground picture is cached until the view or the map changes."""
    def __init__(self, w=560, h=520):
        self.W, self.H = w, h
        self.cx, self.cy = 0.0, 14.0
        self.mpp = 0.11                      # metres per pixel
        self._key = None; self._bg = None

    def to_world(self, px, py):
        return self.cx + (px - self.W / 2) * self.mpp, self.cy - (py - self.H / 2) * self.mpp

    def to_px(self, x, y):
        return (self.W / 2 + (x - self.cx) / self.mpp, self.H / 2 - (y - self.cy) / self.mpp)

    def zoom(self, f, px=None, py=None):
        if px is not None:
            wx, wy = self.to_world(px, py)
        self.mpp = max(0.03, min(20.0, self.mpp * f))
        if px is not None:
            nx, ny = self.to_world(px, py)
            self.cx += wx - nx; self.cy += wy - ny

    def render(self, eng, sel=None, hover=None):
        m = eng.world.map
        st = {1: 3, 2: 2, 3: 1, 4: 1}.get(int(SIM["quality"]), 2)
        key = (m.name, round(self.cx, 2), round(self.cy, 2), round(self.mpp, 4), self.W, self.H, st)
        if key != self._key:
            ys, xs = np.mgrid[0:self.H // st, 0:self.W // st].astype(np.float32) * float(st)
            gx = self.cx + (xs - self.W / 2) * self.mpp; gy = self.cy - (ys - self.H / 2) * self.mpp
            g = ground_colour(gx, gy, m, self.cx, self.cy, sharp=self.mpp < 0.6)
            self._bg = cv2.resize(g, (self.W, self.H), interpolation=cv2.INTER_NEAREST if self.mpp > 1.5 else cv2.INTER_LINEAR)
            self._key = key
        img = self._bg.copy()
        P = lambda x, y: _ipt(self.to_px(x, y))
        s = 1.0 / self.mpp
        # walking area
        # field of view of the camera and of the thermal camera
        camx, camy = SIM["cam_x"], SIM["cam_y"]
        yaw = eng.pose[0]
        for fov, col, th in ((SIM["thermal_hfov"], (0, 140, 255), 1), (SIM["cam_hfov"], (0, 255, 255), 2)):
            for sgn in (-1, 1):
                a = math.radians(yaw + sgn * fov / 2)
                cv2.line(img, P(camx, camy), P(camx + math.sin(a) * 60, camy + math.cos(a) * 60), col, th, cv2.LINE_AA)
        # servo travel (where the head CAN look)
        half = eng.servos["pan"].half
        base = SIM["mount_yaw"]
        if half < 179:
            cv2.ellipse(img, P(camx, camy), (int(3.0 * s), int(3.0 * s)), 0, base - half - 90, base + half - 90, (200, 200, 255), 1, cv2.LINE_AA)
        # props, plants
        vx0, vy1 = self.to_world(-40, -40); vx1, vy0 = self.to_world(self.W + 40, self.H + 40)
        inside = lambda o, r=0: vx0 - r < o.x < vx1 + r and vy0 - r < o.y < vy1 + r
        half = max(self.W, self.H) * self.mpp * 0.75 + 40
        props_v, plants_v = eng.world.nearby_props(self.cx, self.cy, half), eng.world.nearby_plants(self.cx, self.cy, half)
        for pr in eng.world.landmarks():                                 # mountains: contour rings
            for k, f in enumerate((1.0, 0.75, 0.5, 0.28, 0.12)):
                col = (70, 120, 80) if k < 2 else ((110, 115, 120) if k < 4 else (235, 236, 240))
                cv2.circle(img, P(pr.x, pr.y), max(2, int(pr.w / 2 * f * s)), col, -1 if k else 2, cv2.LINE_AA)
            cv2.putText(img, f"Mountain {pr.h:.0f} m", (P(pr.x, pr.y)[0] + 8, P(pr.x, pr.y)[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                        (255, 255, 255), 1, cv2.LINE_AA)
        for pr in props_v:
            if pr.name == "mountain" or not inside(pr, max(pr.w, pr.d)):
                continue
            a, b = P(pr.x - pr.w / 2, pr.y + pr.d / 2), P(pr.x + pr.w / 2, pr.y - pr.d / 2)
            cv2.rectangle(img, a, b, pr.color, -1); cv2.rectangle(img, a, b, (30, 30, 30), 1)
        for p in (plants_v if len(plants_v) < 6000 else plants_v[::max(1, len(plants_v) // 6000)]):
            if not inside(p, 10):
                continue
            r = max(2, int((p.crown if p.kind == "tree" else p.crown) * s))
            cv2.circle(img, P(p.x, p.y), r, p.color, -1, cv2.LINE_AA)
            cv2.circle(img, P(p.x, p.y), r, (20, 50, 20), 1, cv2.LINE_AA)
        # what is moving + where it walks
        seen = {t["id"] for t in eng.truth if t["inside"] > 0.3}
        for e in eng.world.snapshot():
            col = ICON_COL.get(e.kind, (255, 0, 255))
            c = P(e.x, e.y)
            tgt = next((t for t in e.tasks if t[0] == "goto"), None)
            if tgt:
                cv2.line(img, c, P(tgt[1], tgt[2]), (240, 240, 240), 1, cv2.LINE_AA)
            r = max(4, int(max(e.length, e.width) * s / 2)) if e.kind in VEHICLES else 6
            cv2.circle(img, c, r + 2, (0, 0, 255) if e.id in seen else (255, 255, 255), 2, cv2.LINE_AA)
            cv2.circle(img, c, r, col, -1, cv2.LINE_AA)
            hx, hy = c[0] + int(math.sin(e.heading) * (r + 6)), c[1] - int(math.cos(e.heading) * (r + 6))
            cv2.line(img, c, (hx, hy), (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(img, LETTER.get(e.kind, "?"), (c[0] + r + 3, c[1] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(img, LETTER.get(e.kind, "?"), (c[0] + r + 3, c[1] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        # places of interest (the 📍 selector)
        for q in maps.pois(m):
            if vx0 - 60 < q["x"] < vx1 + 60 and vy0 - 60 < q["y"] < vy1 + 60:
                c = P(q["x"], q["y"])
                pts = np.array([(c[0], c[1] - 9), (c[0] + 6, c[1]), (c[0], c[1] + 9), (c[0] - 6, c[1])], np.int32)
                cv2.fillConvexPoly(img, pts, (66, 140, 255), cv2.LINE_AA)
                cv2.polylines(img, [pts], True, (20, 20, 20), 1, cv2.LINE_AA)
                cv2.putText(img, q["name"], (c[0] + 9, c[1] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(img, q["name"], (c[0] + 9, c[1] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (66, 200, 255), 1, cv2.LINE_AA)
        # the camera head
        cpt = P(camx, camy)
        cv2.circle(img, cpt, 9, (30, 30, 30), -1, cv2.LINE_AA); cv2.circle(img, cpt, 9, (0, 220, 255), 2, cv2.LINE_AA)
        a = math.radians(yaw)
        cv2.line(img, cpt, (cpt[0] + int(math.sin(a) * 16), cpt[1] - int(math.cos(a) * 16)), (0, 220, 255), 3, cv2.LINE_AA)
        cv2.ellipse(img, cpt, (int(SIM["pir_range"] * s),) * 2, 0, base - 55 - 90, base + 55 - 90, (180, 120, 255), 1, cv2.LINE_AA)   # PIR range
        if sel is not None:
            self._mark(img, sel, (0, 0, 255))
        if SIM.get("_camera_tool"):                                     # big instruction while placing the camera
            cv2.rectangle(img, (0, 0), (self.W, 34), (0, 140, 255), -1)
            cv2.putText(img, "CLICK where the camera should stand - drag to turn it", (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                        (20, 20, 20), 2, cv2.LINE_AA)
        if hover is not None:
            self._mark(img, hover, (255, 255, 0))
        # scale bar
        L = next((v for v in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000) if v * s >= 70), 5000)
        cv2.line(img, (12, self.H - 14), (12 + int(L * s), self.H - 14), (255, 255, 255), 3)
        cv2.putText(img, f"{L} m" if L < 1000 else f"{L // 1000} km", (14, self.H - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (255, 255, 255), 1, cv2.LINE_AA)
        return img

    def _mark(self, img, item, col):
        kind, o = item
        if kind == "camera":
            x, y = SIM["cam_x"], SIM["cam_y"]
        else:
            x, y = o.x, o.y
        cv2.circle(img, _ipt(self.to_px(x, y)), 16, col, 2, cv2.LINE_AA)


# =====================================================================================================================
class View3D:
    """Orbit view: right-drag turns, wheel zooms, middle-drag (or shift + right-drag) moves the centre."""
    def __init__(self, w=560, h=420):
        self.W, self.H = w, h
        self.tx, self.ty = 0.0, 12.0          # point looked at
        self.yaw = 20.0                       # degrees, 0 = looking along +y
        self.pitch = 32.0                     # degrees down
        self.dist = 34.0
        self.r = Renderer()
        self.cam = CamModel(w, h, 60.0)

    def set_size(self, w, h):
        if (w, h) != (self.W, self.H) and w > 50 and h > 50:
            self.W, self.H = w, h
            self.cam = CamModel(w, h, 60.0); self._key = None
        self._key = None; self._ground = None; self._rays = None

    def eye(self):
        a, p = math.radians(self.yaw), math.radians(self.pitch)
        ex = self.tx - math.sin(a) * math.cos(p) * self.dist
        ey = self.ty - math.cos(a) * math.cos(p) * self.dist
        ez = max(0.4, math.sin(p) * self.dist)
        return ex, ey, ez

    def _setup(self):
        ex, ey, ez = self.eye()
        self.cam.set_pose(self.yaw, -self.pitch, pos=(ex, ey)); self.cam.height = ez

    def pick(self, px, py):
        """Ground point under the mouse (or None above the horizon)."""
        self._setup()
        c = self.cam
        a = (px - c.cx) / c.f; b = -(py - c.cy) / c.f
        dx = c.fw[0] + a * c.rt[0] + b * c.up[0]
        dy = c.fw[1] + a * c.rt[1] + b * c.up[1]
        dz = c.fw[2] + b * c.up[2]
        if dz >= -1e-4:
            return None
        t = -c.height / dz
        if t > 400:
            return None
        return c.px + dx * t, c.py + dy * t

    def render(self, eng, sel=None, hover=None):
        self._setup()
        cam = self.cam
        m = eng.world.map
        st = {1: 4, 2: 3, 3: 2, 4: 1}.get(int(SIM["quality"]), 3)
        key = (m.name, round(self.yaw, 2), round(self.pitch, 2), round(self.dist, 2), round(self.tx, 2), round(self.ty, 2), self.W, self.H, st)
        if key != self._key:
            nx, ny = self.W // st, self.H // st
            dx, dy, dz, _a, _b = cam.rays(nx, ny)
            with np.errstate(divide="ignore", invalid="ignore"):
                t = np.where(dz < -1e-4, -cam.height / dz, np.inf)
            gnd = np.isfinite(t) & (t < 6000)
            gx = np.where(gnd, cam.px + dx * t, 0.0); gy = np.where(gnd, cam.py + dy * t, 0.0)
            col = ground_colour(gx, gy, m, self.tx, self.ty, sharp=self.dist < 250).astype(np.float32)
            hz = (1 - np.exp(-np.where(gnd, t, 1e5) / max(1500.0, self.dist * 3.0)))[..., None]
            col = col * (1 - hz) + np.array([210, 200, 190], np.float32) * hz
            pit = np.degrees(np.arctan2(dz, np.hypot(dx, dy)))
            k = np.clip(pit / 50.0, 0, 1)[..., None]
            sky = np.array([228, 210, 190], np.float32) * (1 - k) + np.array([175, 110, 55], np.float32) * k
            col = np.where(gnd[..., None], col, sky)
            self._ground = cv2.resize(col.astype(np.uint8), (self.W, self.H), interpolation=cv2.INTER_LINEAR)
            self._key = key
        img = self._ground.copy()
        r = self.r
        r.cam = cam
        env = eng.env or {"t": 0.0, "wind": SIM["wind"], "sun": (45.0, 3.0)}
        ex, ey, _ez = self.eye()
        D = lambda o: math.hypot(o.x - ex, o.y - ey)
        # field of view of the motion camera on the ground
        camx, camy, h = SIM["cam_x"], SIM["cam_y"], SIM["mount_height"]
        yaw = eng.pose[0]
        for fov, col in ((SIM["thermal_hfov"], (0, 140, 255)), (SIM["cam_hfov"], (0, 255, 255))):
            pts = []
            for k in range(-8, 9):
                a = math.radians(yaw + k / 8.0 * fov / 2)
                pts.append((camx + math.sin(a) * 30, camy + math.cos(a) * 30))
            poly = [cam.project(camx, camy, 0.02)] + [cam.project(x, y, 0.02) for x, y in pts]
            if all(poly):
                cv2.polylines(img, [np.array([_ipt(p) for p in poly], np.int32)], True, col, 2 if col[1] == 255 else 1, cv2.LINE_AA)
        R = max(300.0, self.dist * 3.0)
        near = eng.world.nearby_plants(self.tx, self.ty, min(R, 3000.0))
        near = near[::max(1, len(near) // 2500)]                         # zoomed far out: a sample of the trees is enough
        plants = [p for p in near if not cull(p, cam, p.crown * 1.8 + 1, 3500.0)]
        props = eng.world.landmarks() + [pr for pr in eng.world.nearby_props(self.tx, self.ty, R + 600.0)
                 if (pr.h > 25 or math.hypot(pr.x - self.tx, pr.y - self.ty) < R) and not cull(pr, cam, math.hypot(pr.w, pr.d) / 2 + 1, 4000.0)]
        ents = [e for e in eng.world.snapshot() if not cull(e, cam, 3.0, 900.0)]
        things = [(D(p), "plant", p) for p in plants] + [(D(pr), "prop", pr) for pr in props] +                  [(D(e), "ent", e) for e in ents] + [(math.hypot(camx - ex, camy - ey), "camera", None)]
        things.sort(key=lambda t: -t[0])
        for d, typ, o in things:
            try:
                if typ == "plant":
                    r._plant(img, o, env)
                elif typ == "prop":
                    r._prop(img, o, env)
                elif typ == "camera":
                    self._head(img, camx, camy, h, yaw, eng.pose[1])
                elif o.kind == "plane":
                    r._plane(img, o)
                elif o.kind == "person":
                    r._person(img, o)
                elif o.kind in VEHICLES or o.kind == "bicycle":
                    r._vehicle(img, o)
                else:
                    r._animal(img, o)
            except (cv2.error, OverflowError, ValueError):
                pass
        for q in maps.pois(m):                                           # places of interest: pin + name
            a = cam.project(q["x"], q["y"], 0.0, near=1.0); b = cam.project(q["x"], q["y"], max(6.0, self.dist * 0.04), near=1.0)
            if a and b and 0 <= b[0] < self.W and 0 <= b[1] < self.H:
                cv2.line(img, _ipt(a), _ipt(b), (66, 140, 255), 1, cv2.LINE_AA)
                cv2.circle(img, _ipt(b), 4, (66, 140, 255), -1, cv2.LINE_AA)
                cv2.putText(img, q["name"], (int(b[0]) + 6, int(b[1]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(img, q["name"], (int(b[0]) + 6, int(b[1]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (66, 200, 255), 1, cv2.LINE_AA)
        for item, col in ((sel, (0, 0, 255)), (hover, (255, 255, 0))):
            if item is not None:
                kind, o = item
                x, y = (camx, camy) if kind == "camera" else (o.x, o.y)
                ring = [cam.project(x + math.sin(k / 12 * math.pi) * 1.2, y + math.cos(k / 12 * math.pi) * 1.2, 0.03) for k in range(24)]
                if all(ring):
                    cv2.polylines(img, [np.array([_ipt(p) for p in ring], np.int32)], True, col, 2, cv2.LINE_AA)
        if SIM.get("_camera_tool"):
            cv2.rectangle(img, (0, 0), (self.W, 34), (0, 140, 255), -1)
            cv2.putText(img, "CLICK where the camera should stand - drag to turn it", (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                        (20, 20, 20), 2, cv2.LINE_AA)
        cv2.putText(img, "right-drag: turn   wheel: zoom   middle-drag / shift+right-drag: move", (8, self.H - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
        return img

    def _head(self, img, x, y, h, yaw, pitch):
        cam = self.cam
        a, b = cam.project(x, y, 0.0), cam.project(x, y, h - 0.15)
        if not (a and b):
            return
        s = cam.f / b[2]
        cv2.line(img, _ipt(a), _ipt(b), (60, 60, 60), max(2, int(0.08 * s)), cv2.LINE_AA)
        fx, fy = math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)), math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))
        c = cam.project(x, y, h)
        lens = cam.project(x + fx * 0.6, y + fy * 0.6, h + math.sin(math.radians(pitch)) * 0.6)
        if c and lens:
            cv2.circle(img, _ipt(c), max(4, int(0.18 * s)), (40, 40, 40), -1, cv2.LINE_AA)
            cv2.line(img, _ipt(c), _ipt(lens), (0, 200, 255), max(2, int(0.08 * s)), cv2.LINE_AA)
            cv2.circle(img, _ipt(c), max(4, int(0.18 * s)), (0, 200, 255), 2, cv2.LINE_AA)
