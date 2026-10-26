"""Turns the world into camera pictures.

Main camera: the static scenery (ground, road, sky, mountains) lives in one big equirectangular panorama. A pan/tilt head
only rotates the camera around its own centre, so cutting the view out of a panorama is exactly right for every servo
position. Everything that moves or sways (people, animals, vehicles, bushes, props) is drawn on top, sorted by distance,
then light (day / night / IR / white light), weather, lens problems and sensor noise are applied.

Thermal camera: an 80 x 62 picture in degrees Celsius, rendered at 4x and averaged down (like the real sensor pixels)."""
import math
import random
import time

import cv2
import numpy as np

from simulator.config import SIM
from simulator.scene import maps
from simulator.scene.world import VEHICLES, ambient_light, sun

RES = 0.065                     # panorama degrees per pixel
YAW0, YAW1 = -180.0, 180.0
PTOP, PBOT = 72.0, -89.0
PW = int(round((YAW1 - YAW0) / RES))
PH = int(round((PTOP - PBOT) / RES))
SKY_FAR = 1.0e4
QUALITY_RES = {1: 0.09, 2: 0.065, 3: 0.05, 4: 0.038}      # degrees per panorama pixel for quality 1..4
CUBE_SIZE = {1: 896, 2: 1152, 3: 1536, 4: 1792}           # pixels per cube face for quality 1..4
CUBE_FACES = [(90.0, 0.0), (-90.0, 0.0), (0.0, 0.0), (180.0, 0.0), (0.0, 90.0), (0.0, -90.0)]   # +x -x +y -y up down
CUBE_PAD = 4
QUALITY = {"q": 3}


def set_quality(q):
    """Sharper background = smaller panorama pixels (more memory, longer to build)."""
    global RES, PW, PH
    QUALITY["q"] = int(q)
    RES = QUALITY_RES.get(int(q), 0.065)
    PW = int(round((YAW1 - YAW0) / RES))
    PH = int(round((PTOP - PBOT) / RES))
    return RES


SOLID = {"tower", "block", "house", "caravan", "shed", "hut", "wall", "mountain"}


def mountain_mesh(pr):
    """Vertices (rings x segments x 3) of a mountain prop: pr.w = foot diameter, pr.h = height, ridges from its position."""
    key = (pr.x, pr.y, pr.w, pr.h)
    cache = getattr(pr, "_mesh", None)
    if cache is not None and cache[0] == key:
        return cache[1]
    rng = np.random.default_rng(int(abs(pr.x * 3 + pr.y * 7)) % 10007)
    NR, NS = 34, 110
    R = pr.w / 2.0
    ang = np.linspace(0, 2 * np.pi, NS, endpoint=False)
    ridge = 1.0 + 0.18 * np.sin(ang * 3 + rng.uniform(0, 6)) + 0.12 * np.sin(ang * 5 + rng.uniform(0, 6)) + \
        0.07 * np.sin(ang * 11 + rng.uniform(0, 6))
    rr = np.linspace(0, 1, NR)[:, None]
    rough = 1.0 + 0.035 * rng.standard_normal((NR, NS))
    rough[0] = 1.0
    hh = pr.h * np.clip(1.0 - rr ** 1.25, 0, 1) ** 1.35 * (0.85 + 0.15 * ridge[None, :]) * rough
    hh[-1] = 0.0
    rad = R * rr * ridge[None, :]
    V = np.stack([pr.x + rad * np.sin(ang)[None, :], pr.y + rad * np.cos(ang)[None, :], hh], -1).astype(np.float32)
    pr._mesh = (key, V)
    return V
_SX = np.array([-0.5, 0.5, 0.5, -0.5, -0.5, 0.5, 0.5, -0.5], np.float32)
_SY = np.array([-0.5, -0.5, 0.5, 0.5, -0.5, -0.5, 0.5, 0.5], np.float32)
_SZ = np.array([0, 0, 0, 0, 1, 1, 1, 1], np.float32)


def visible_props(props, cam, cell=16):
    """Drop props outside the picture or completely hidden behind nearer solid ones (city blocks hide most towers).
    All corners are projected at once; a coarse coverage grid is filled near to far."""
    if len(props) < 30:
        return props
    a = np.array([(pr.x, pr.y, pr.w, pr.d, pr.h) for pr in props], np.float32)
    X = a[:, :1] + a[:, 2:3] * _SX - cam.px
    Y = a[:, 1:2] + a[:, 3:4] * _SY - cam.py
    Z = a[:, 4:5] * _SZ - cam.height
    rt, up, fw = cam.rt, cam.up, cam.fw
    xc = X * rt[0] + Y * rt[1]
    yc = X * up[0] + Y * up[1] + Z * up[2]
    zc = X * fw[0] + Y * fw[1] + Z * fw[2]
    behind = (zc < 0.3).any(axis=1)                                    # partly behind the camera: keep, cannot judge
    gone = (zc < 0.3).all(axis=1)                                       # completely behind the camera
    zs = np.maximum(zc, 0.3)
    u = cam.cx + cam.f * xc / zs
    v = cam.cy - cam.f * yc / zs
    u0, u1, v0, v1 = u.min(1), u.max(1), v.min(1), v.max(1)
    off = (~behind) & ((u1 < 0) | (u0 > cam.W) | (v1 < 0) | (v0 > cam.H) | (zc.max(1) < 0.3))
    d = np.hypot(a[:, 0] - cam.px, a[:, 1] - cam.py)
    Wc, Hc = int(math.ceil(cam.W / cell)), int(math.ceil(cam.H / cell))
    cov = np.zeros((Hc, Wc), bool)
    keep = []
    for i in np.argsort(d):
        if off[i] or gone[i]:
            continue
        if behind[i]:
            keep.append(i); continue
        x0 = max(0, int(u0[i] // cell)); x1 = min(Wc - 1, int(u1[i] // cell))
        y0 = max(0, int(v0[i] // cell)); y1 = min(Hc - 1, int(v1[i] // cell))
        if x1 < x0 or y1 < y0:
            continue
        if cov[y0:y1 + 1, x0:x1 + 1].all():
            continue                                                    # completely behind nearer buildings
        keep.append(i)
        if props[i].name in SOLID:                                      # its inner part hides what is behind it
            w, h = u1[i] - u0[i], v1[i] - v0[i]
            ix0 = int(math.ceil((u0[i] + 0.12 * w) / cell)); ix1 = int((u1[i] - 0.12 * w) // cell) - 1
            iy0 = int(math.ceil((v0[i] + 0.12 * h) / cell)); iy1 = int((v1[i] - 0.05 * h) // cell) - 1
            if ix1 >= ix0 and iy1 >= iy0:
                cov[max(0, iy0):iy1 + 1, max(0, ix0):ix1 + 1] = True
    keep.sort()
    return [props[i] for i in keep]


def cull(o, cam, rad, maxd):
    """True when an object (centre o.x / o.y, radius rad) cannot be in the picture: too far or outside the view."""
    dx, dy = o.x - cam.px, o.y - cam.py
    d = math.hypot(dx, dy)
    if d > maxd:
        return True
    if d < rad + 3.0:
        return False
    p = cam.project(o.x, o.y, min(getattr(o, "h", 2.0), 30.0) * 0.5, near=0.05)
    if p is None:
        return True
    r = rad * cam.f / max(0.1, p[2]) + 40
    return p[0] < -r or p[0] > cam.W + r


def _noise_tex(n, octaves, seed):
    """Seamless (tileable) fractal noise in 0..1, made in the frequency domain - no seams where it repeats."""
    rng = np.random.default_rng(seed)
    white = np.fft.fft2(rng.standard_normal((n, n)))
    f = np.hypot(np.fft.fftfreq(n)[:, None], np.fft.fftfreq(n)[None, :])
    f[0, 0] = 1.0
    beta = 2.4 - 0.12 * octaves                 # more octaves = more fine detail
    amp = f ** -beta
    amp[0, 0] = 0.0
    amp[f < 1.0 / n * 2] *= 0.5
    out = np.real(np.fft.ifft2(white * amp)).astype(np.float32)
    out -= out.min(); out /= max(1e-6, float(out.max()))
    return out


def _fbm1d(x, seed, octaves=5):
    """Smooth 1-D noise in 0..1 for an array of angles (degrees)."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(x, dtype=np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        period = 90.0 / (2 ** o)
        k = rng.random(int(400 / period) + 4).astype(np.float32)
        u = (x - YAW0) / period
        i = np.floor(u).astype(int); f = (u - i).astype(np.float32)
        f = f * f * (3 - 2 * f)
        out += (k[i % len(k)] * (1 - f) + k[(i + 1) % len(k)] * f) * amp
        tot += amp; amp *= 0.5
    return out / tot


def build_panorama(height, m, pos=(0.0, 0.0)):
    """The static background of map m: sky + clouds, mountains / tree line / far houses, and the painted ground."""
    hzn = m.horizon
    pano = np.zeros((PH, PW, 3), np.uint8)
    yaw = (YAW0 + (np.arange(PW, dtype=np.float32) + 0.5) * RES)
    pitch_rows = PTOP - (np.arange(PH, dtype=np.float32) + 0.5) * RES
    horizon_row = int((PTOP - 0.0) / RES)

    # ---- sky ----
    sky_rows = pitch_rows[:horizon_row]
    k = np.clip(sky_rows / 60.0, 0, 1)[:, None, None]
    zen = np.array([175, 110, 55], np.float32); hor = np.array([228, 210, 190], np.float32)
    if hzn.get("snow"):
        zen = np.array([185, 150, 120], np.float32); hor = np.array([225, 222, 218], np.float32)
    sky = (hor * (1 - k) + zen * k) * np.ones((1, PW, 1), np.float32)
    cl = _noise_tex(1024, 6, 5)
    my, mx = np.meshgrid(np.clip(sky_rows, 0, 90) * 6.0, (yaw - YAW0) * 3.0, indexing="ij")
    cloud = cv2.remap(cl, (mx % 1024).astype(np.float32), (my % 1024).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    cmask = np.clip((cloud - 0.52) * 4.0, 0, 1) * np.clip(sky_rows[:, None] / 4.0, 0, 1)
    sky = sky * (1 - cmask[..., None] * 0.85) + np.array([244, 244, 246], np.float32) * cmask[..., None] * 0.85
    pano[:horizon_row] = np.clip(sky, 0, 255).astype(np.uint8)

    # ---- mountains, far houses, tree line (above the horizon, very far away) ----
    ms = float(hzn.get("mountains", 1.0))
    mh = (0.4 + 3.4 * _fbm1d(yaw, 11) ** 1.6) * ms                 # degrees
    th = (0.25 + 0.55 * _fbm1d(yaw * 3.0, 12, 4)) * float(hzn.get("treeline", 0.55)) / 0.55
    tcol = hzn.get("treeline_col", (48, 78, 52))
    snow_line = 2.2 * ms if not hzn.get("snow") else 0.3
    houses = np.zeros(PW, np.float32); hcols = np.zeros((PW, 3), np.uint8)
    if hzn.get("buildings"):
        rng = np.random.default_rng(31)
        c = 0
        while c < PW:
            w = int(rng.integers(20, 120)); h = float(rng.uniform(0.5, 2.6)) if rng.random() < 0.7 else 0.0
            houses[c:c + w] = h
            hcols[c:c + w] = rng.integers(120, 200, 3)
            c += w + int(rng.integers(0, 40))
    for c in range(PW):
        if mh[c] > 0.05:
            top = int((PTOP - mh[c]) / RES)
            r0 = max(0, top); r1 = horizon_row
            if r1 > r0:
                col = np.array([150, 135, 125], np.float32)
                g = np.linspace(0, 1, r1 - r0, dtype=np.float32)[:, None]
                pano[r0:r1, c] = (col * (1 - 0.25 * g)).astype(np.uint8)
                sn = int((PTOP - (mh[c] - 0.45)) / RES)
                if mh[c] > snow_line and sn > r0:
                    pano[r0:min(sn, r1), c] = (236, 236, 240)
        if houses[c] > 0:
            pano[int((PTOP - houses[c]) / RES):horizon_row, c] = hcols[c]
        ttop = int((PTOP - th[c]) / RES)
        if horizon_row > ttop:
            pano[ttop:horizon_row, c] = tcol

    # ---- ground: one raster look-up per pixel (sharp near the camera, coarse further out) ----
    from simulator.scene import ground
    grass_f = _noise_tex(1024, 7, 21)
    grass_c = _noise_tex(512, 5, 22)
    yaw_r = np.radians(yaw)
    sy, cy_ = np.sin(yaw_r)[None, :], np.cos(yaw_r)[None, :]
    rows = np.arange(horizon_row, PH)
    haze_col = np.array([200, 195, 185] if not hzn.get("snow") else [225, 222, 220], np.float32)
    for r0 in range(horizon_row, PH, 160):
        rr = rows[(rows >= r0) & (rows < r0 + 160)]
        p = np.radians(np.clip(-pitch_rows[rr], 0.01, 89.9))[:, None]
        dist = height / np.tan(p)                                   # metres along the ground
        gx = (pos[0] + dist * sy).astype(np.float32); gy = (pos[1] + dist * cy_).astype(np.float32)
        fine = cv2.remap(grass_f, (gx / 0.05) % 1024, (gy / 0.05) % 1024, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        coarse = cv2.remap(grass_c, (gx / 1.8) % 512, (gy / 1.8) % 512, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        far = np.clip((dist - 12.0) / 35.0, 0, 1)
        fine = fine * (1 - far) + 0.5 * far
        cls = ground.classes(m, gx, gy, pos[0], pos[1])
        col = ground.colour(m, cls, fine, coarse)
        hz = (1 - np.exp(-dist / (260.0 if (m.extent[1] - m.extent[0]) < 600 else 2200.0)))[..., None]   # haze towards the horizon
        col = col * (1 - hz) + haze_col * hz
        pano[rr] = np.clip(col, 0, 255).astype(np.uint8)
    return pano


class CamModel:
    """Pinhole camera on the pan/tilt head. yaw: + = right, pitch: + = up (degrees)."""
    def __init__(self, w, h, hfov):
        self.W, self.H, self.hfov = int(w), int(h), float(hfov)
        self.f = (self.W / 2.0) / math.tan(math.radians(self.hfov) / 2.0)
        self.cx, self.cy = self.W / 2.0, self.H / 2.0
        self.px = self.py = 0.0
        self.set_pose(0.0, 0.0)

    def set_pose(self, yaw, pitch, height=None, pos=None):
        self.yaw, self.pitch = yaw, pitch
        if pos is not None:
            self.px, self.py = pos
        if height is not None:
            self.height = height
        ps, pc = math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        ts, tc = math.sin(math.radians(pitch)), math.cos(math.radians(pitch))
        self.fw = (ps * tc, pc * tc, ts)
        self.rt = (pc, -ps, 0.0)
        self.up = (-ps * ts, -pc * ts, tc)

    def cam_xyz(self, x, y, z):
        vx, vy, vz = x - self.px, y - self.py, z - self.height
        return (vx * self.rt[0] + vy * self.rt[1],
                vx * self.up[0] + vy * self.up[1] + vz * self.up[2],
                vx * self.fw[0] + vy * self.fw[1] + vz * self.fw[2])

    def project(self, x, y, z, near=0.25):
        xc, yc, zc = self.cam_xyz(x, y, z)
        if zc < near:
            return None
        return self.cx + self.f * xc / zc, self.cy - self.f * yc / zc, zc

    def angle_to(self, x, y, z):
        """Angle in degrees between the optical axis and a world point."""
        xc, yc, zc = self.cam_xyz(x, y, z)
        n = math.sqrt(xc * xc + yc * yc + zc * zc) or 1e-9
        return math.degrees(math.acos(max(-1.0, min(1.0, zc / n))))

    def rays(self, nx, ny):
        """Ray directions of an nx x ny grid laid out like cv2.resize expects (pixel centres)."""
        px = (np.arange(nx, dtype=np.float32) + 0.5) * self.W / nx - 0.5
        py = (np.arange(ny, dtype=np.float32) + 0.5) * self.H / ny - 0.5
        a = ((px - self.cx) / self.f)[None, :]
        b = (-(py - self.cy) / self.f)[:, None]
        fw, rt, up = self.fw, self.rt, self.up
        dx = fw[0] + a * rt[0] + b * up[0]
        dy = fw[1] + a * rt[1] + b * up[1]
        dz = fw[2] + b * up[2] + 0 * a
        return dx, dy, dz, a, b


def clip_project(cam, pts, near=0.3):
    """Project a flat 3D polygon, cut off where it goes behind the camera (instead of dropping it).
    Returns an int32 array of screen points, or None if nothing is in front."""
    cs = [cam.cam_xyz(x, y, z) for x, y, z in pts]
    out = []
    n = len(cs)
    for i in range(n):
        a, b = cs[i], cs[(i + 1) % n]
        ina, inb = a[2] >= near, b[2] >= near
        if ina:
            out.append(a)
        if ina != inb:
            t = (near - a[2]) / (b[2] - a[2])
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, near))
    if len(out) < 3:
        return None
    return np.array([(int(round(max(-30000, min(30000, cam.cx + cam.f * x / z)))),
                      int(round(max(-30000, min(30000, cam.cy - cam.f * y / z))))) for x, y, z in out], np.int32)


def _ipt(p):
    return int(round(max(-30000, min(30000, p[0])))), int(round(max(-30000, min(30000, p[1]))))


def _th(v, lo=1):
    return int(max(lo, min(400, round(v))))


_drawn_owner = {"r": None}


def _shade(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c)


class Cube:
    """The static scene (ground, sky, buildings, mountains, their shadows) seen from one camera place, as six 90 degree
    pictures in one atlas (3 x 2 faces) plus depth and lit-window masks. Turning the camera only samples from it."""
    def __init__(self, F, atlas, depth, emis, faces, key, pos, map_name, height):
        self.F, self.atlas, self.depth, self.emis, self.faces = F, atlas, depth, emis, faces
        self.key, self.pos, self.map_name, self.height = key, pos, map_name, height


def _dirs_to_atlas(dx, dy, dz, F, f, half):
    """Atlas coordinates of directions (cube faces aligned with the world axes, layout see CUBE_FACES)."""
    ax, ay, az = np.abs(dx), np.abs(dy), np.abs(dz)
    isx = (ax >= ay) & (ax >= az); isy = ~isx & (ay >= az)
    c = np.where(isx, ax, np.where(isy, ay, az))
    a = np.where(isx, np.where(dx > 0, -dy, dy), np.where(isy, np.where(dy > 0, dx, -dx), dx))
    b = np.where(isx | isy, dz, np.where(dz > 0, -dy, dy))
    sel = np.where(isx, (dx <= 0).astype(np.float32), np.where(isy, 2 + (dy <= 0).astype(np.float32), 4 + (dz <= 0).astype(np.float32)))
    inv = f / np.maximum(c, 1e-6)
    mx = (half + a * inv + (sel % 3) * F).astype(np.float32)
    my = (half - b * inv + np.floor(sel / 3) * F).astype(np.float32)
    return mx, my


def cube_to_equirect(atlas, depth, emis, F, f, half, shape):
    """The static scene as one panorama (same grid as the background panorama): picture full size, depth and lit
    windows at half size. Done once per camera place, so turning the camera needs only a cheap look-up."""
    PHs, PWs = shape
    eq = np.zeros((PHs, PWs, 3), np.uint8)
    eqd = np.zeros((PHs // 2, PWs // 2), np.float32)
    eqe = np.zeros((PHs // 2, PWs // 2), np.uint8)
    res = (YAW1 - YAW0) / PWs
    yaw = np.radians(YAW0 + (np.arange(PWs, dtype=np.float32) + 0.5) * res)[None, :]
    sy, cyw = np.sin(yaw), np.cos(yaw)
    for r0 in range(0, PHs, 240):
        r1 = min(PHs, r0 + 240)
        pit = np.radians(PTOP - (np.arange(r0, r1, dtype=np.float32) + 0.5) * res)[:, None]
        cp, sp = np.cos(pit), np.sin(pit)
        mx, my = _dirs_to_atlas(sy * cp, cyw * cp, sp * np.ones_like(sy), F, f, half)
        eq[r0:r1] = cv2.remap(atlas, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        h0, h1 = r0 // 2, (r1 + 1) // 2
        mxh = cv2.resize(mx, (PWs // 2, h1 - h0), interpolation=cv2.INTER_NEAREST)
        myh = cv2.resize(my, (PWs // 2, h1 - h0), interpolation=cv2.INTER_NEAREST)
        eqd[h0:h1] = cv2.remap(depth, mxh, myh, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE)[:eqd.shape[0] - h0]
        eqe[h0:h1] = cv2.remap(emis, mxh, myh, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE)[:eqe.shape[0] - h0]
    return eq, eqd, eqe


def _face_maps(cam, pano, exact):
    """Panorama look-up for one cube face (yaw unwrapped around the face centre so a coarse grid can be resized)."""
    res = (YAW1 - YAW0) / pano.shape[1]
    n = cam.W if exact else max(16, cam.W // 8)
    dx, dy, dz, _a, _b = cam.rays(n, n)
    yaw_d = np.degrees(np.arctan2(dx, dy))
    yaw_d = cam.yaw + (yaw_d - cam.yaw + 180.0) % 360.0 - 180.0
    pit_d = np.degrees(np.arctan2(dz, np.hypot(dx, dy)))
    mx = ((yaw_d - YAW0) / res - 0.5).astype(np.float32)
    my = ((PTOP - pit_d) / res - 0.5).astype(np.float32)
    tp = np.tan(np.radians(np.clip(-pit_d, 0.02, 89.9)))
    d = np.where(pit_d < -0.02, cam.height / tp, SKY_FAR).astype(np.float32)
    if not exact:
        mx = cv2.resize(mx, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        my = cv2.resize(my, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        d = cv2.resize(d, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
    return mx % pano.shape[1], my, d


class Renderer:
    def __init__(self):
        self.map = maps.get(maps.DEFAULT); self.pano_map = None
        self.pano = None; self.pano_height = None; self.pano_pos = (0.0, 0.0)
        self.cam = None; self._cache_key = None; self.bg = None; self.depth = None
        self.gain = 1.0; self.cone = None
        self.last_out = None
        self.emis = None; self._pending_emis = []
        self._noise = None
        self.tcam = None; self._tkey = None; self._tbase = None

    # ---- setup ----
    def ensure(self, w, h, hfov, height):
        if self.pano is None:
            self.use_map(self.map, build_panorama(height, self.map, self.pano_pos), height, self.pano_pos)
        if self.cam is None or (self.cam.W, self.cam.H, self.cam.hfov) != (w, h, hfov):
            self.cam = CamModel(w, h, hfov); self._cache_key = None; self.cone = None; self._noise = None
        self.cam.height = self.pano_height
        self.cam.px, self.cam.py = self.pano_pos

    def use_map(self, m, pano, height, pos=(0.0, 0.0), cube=None):
        """Switch to a map / camera place whose panorama was built beforehand (building takes a few seconds).
        The panorama is only right for one camera position: the camera head stands where it was built for."""
        self.map = m; self.pano = pano; self.pano_map = m.name; self.pano_height = height; self.pano_pos = tuple(pos)
        self.pano_res = (YAW1 - YAW0) / pano.shape[1]
        self._cache_key = None; self._tkey = None
        if cube is not None:
            self.cube = cube; self._lookup_key = None

    def _background(self, yaw, pitch):
        key = (round(yaw, 3), round(pitch, 3), self.cam.W, self.cam.H, self.cam.hfov, self.pano_height, self.pano_map, self.pano_pos)
        if key == self._cache_key:
            return
        cam = self.cam
        cam.set_pose(yaw, pitch)
        nx, ny = max(8, cam.W // 8), max(6, cam.H // 8)
        dx, dy, dz, a, b = cam.rays(nx, ny)
        h = np.hypot(dx, dy)
        yaw_d = np.degrees(np.arctan2(dx, dy))
        pit_d = np.degrees(np.arctan2(dz, h))
        res = (YAW1 - YAW0) / self.pano.shape[1]                       # the panorama's own resolution
        mx = ((yaw_d - YAW0) / res - 0.5).astype(np.float32)
        my = ((PTOP - pit_d) / res - 0.5).astype(np.float32)
        mx = cv2.resize(mx, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        my = cv2.resize(my, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        tp = np.tan(np.radians(np.clip(-pit_d, 0.02, 89.9)))
        d = np.where(pit_d < -0.02, cam.height / tp, SKY_FAR).astype(np.float32)
        self.depth = cv2.resize(d, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        if self.cone is None:
            aa, bb = np.meshgrid(a[0], b[:, 0])
            c = np.exp(-(aa * aa + bb * bb) / (2 * 0.42 ** 2)).astype(np.float32)
            self.cone = cv2.resize(c, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        self._cache_key = key

    # ---- the static cube ----
    def cube_key(self, env, props):
        S = SIM
        elev = env["sun"][0] if env else 40.0
        sun_on = bool(S["shadows"] and elev > 4 and S["clouds"] < 0.92)
        return (CUBE_SIZE.get(QUALITY["q"], 1536), round(elev / 2.0), sun_on, round(S["clouds"], 1), len(props),
                S["draw_trees"], S["draw_buildings"], S["draw_small"], S["draw_backdrop"])

    def build_cube(self, props, env, m=None, pano=None, height=None, pos=None, plants=()):
        """Draw the static scene into the six cube faces (runs in a background thread; uses its own helper renderer)."""
        m = m or self.map; pano = self.pano if pano is None else pano
        height = height or self.pano_height; pos = tuple(pos or self.pano_pos)
        F = CUBE_SIZE.get(QUALITY["q"], 1536)
        b = Renderer(); b.use_map(m, pano, height, pos)
        hf = 2.0 * math.degrees(math.atan((F / 2.0) / (F / 2.0 - CUBE_PAD)))
        b.cam = CamModel(F, F, hf); b.cam.height = height; b.cam.px, b.cam.py = pos
        atlas = np.zeros((2 * F, 3 * F, 3), np.uint8); depth = np.zeros((2 * F, 3 * F), np.float32)
        emis = np.zeros((2 * F, 3 * F), np.uint8)
        faces = []
        props = [pr for pr in props]
        for k, (yw, pt) in enumerate(CUBE_FACES):
            b.cam.set_pose(yw, pt, pos=pos)
            mx, my, gd = _face_maps(b.cam, pano, exact=(pt != 0.0))
            bg = cv2.remap(pano, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            img, dep, em = b._draw_static(bg, gd, props, env, plants)
            r, c = divmod(k, 3)
            atlas[r * F:(r + 1) * F, c * F:(c + 1) * F] = img
            depth[r * F:(r + 1) * F, c * F:(c + 1) * F] = dep
            emis[r * F:(r + 1) * F, c * F:(c + 1) * F] = em
            faces.append((b.cam.fw, b.cam.rt, b.cam.up, b.cam.f, b.cam.cx, b.cam.cy, c * F, r * F))
        cube = Cube(F, atlas, depth, emis, faces, self.cube_key(env, props), pos, m.name, height)
        cube.eq, cube.eqd, cube.eqe = cube_to_equirect(atlas, depth, emis, F, faces[0][3], faces[0][4], pano.shape[:2])
        cube.atlas = cube.depth = cube.emis = None                    # the panorama form is all the camera needs
        return cube

    def _draw_static(self, bg, gdepth, props, env, plants=()):
        """Ground + buildings + mountains + their shadows for self.cam. Returns (picture, depth, lit-window mask)."""
        S = SIM
        cam = self.cam
        W, H = cam.W, cam.H
        D = lambda o: math.hypot(o.x - cam.px, o.y - cam.py)
        elev = env["sun"][0] if env else 40.0
        sun_on = S["shadows"] and elev > 4 and S["clouds"] < 0.92
        props_v = visible_props([pr for pr in props if D(pr) - max(pr.w, pr.d) / 2 < (9000.0 if pr.name == "mountain" else 3000.0)], cam)
        tw = sorted((pr for pr in props_v if pr.name in ("tower", "block")), key=D)
        self._detailed = {id(pr) for pr in tw[:45]}                     # facade details only for the nearest towers
        simg = bg.copy(); sdepth = gdepth.copy()
        self.emis = np.zeros((H, W), np.uint8); self._pending_emis = []
        if sun_on:
            mask = np.zeros((H, W), np.uint8)
            for pr in props_v:
                if D(pr) < 90 + pr.h * 2:
                    self._shadow(mask, pr.x, pr.y, max(pr.w, pr.d), pr.h, env)
            for pl in plants:                                            # trees stay where they are: their shadows too
                if D(pl) < 90:
                    self._shadow(mask, pl.x, pl.y, pl.crown * 1.6, pl.height, env)
            if mask.any():
                k = 0.5 * (1.0 - 0.85 * S["clouds"]) * min(1.0, (elev - 4) / 10.0)
                m = cv2.GaussianBlur(mask, (5, 5), 0).astype(np.float32) * (k / 255.0)
                simg = (simg * (1.0 - m[..., None])).astype(np.uint8)
        for pr in sorted(props_v, key=lambda o: -D(o)):
            if pr.name == "mountain":
                self._mountain(simg, pr, env, sdepth)
            elif pr.name in ("tower", "block"):
                self._tower(simg, pr, env, sdepth)
            else:
                box = self._prop_box(pr)
                if box is not None:
                    self._drawn(simg, sdepth, box, lambda pr=pr: self._prop(simg, pr, env))
        return simg, sdepth, self.emis

    def _cube_lookup(self, cube):
        """Static scene for the current camera pose: a coarse grid of directions -> panorama coordinates, resized
        (yaw unwrapped around the view so the grid never jumps at +-180 degrees)."""
        cam = self.cam
        nx, ny = max(8, cam.W // 8), max(6, cam.H // 8)
        dx, dy, dz, _a, _b = cam.rays(nx, ny)
        h = np.hypot(dx, dy)
        yaw_d = np.degrees(np.arctan2(dx, dy))
        yaw_d = cam.yaw + (yaw_d - cam.yaw + 180.0) % 360.0 - 180.0
        pit_d = np.degrees(np.arctan2(dz, h))
        PHs, PWs = cube.eq.shape[:2]
        res = (YAW1 - YAW0) / PWs
        mx = ((yaw_d - YAW0) / res - 0.5).astype(np.float32)
        my = np.clip((PTOP - pit_d) / res - 0.5, 0, PHs - 1).astype(np.float32)
        mx = cv2.resize(mx, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        my = cv2.resize(my, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        gd = np.where(pit_d < -0.02, cam.height / np.tan(np.radians(np.clip(-pit_d, 0.02, 89.9))), SKY_FAR).astype(np.float32)
        gd = cv2.resize(gd, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
        img = cv2.remap(cube.eq, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        mxh, myh = mx * 0.5, my * 0.5
        dep = cv2.remap(cube.eqd, mxh, myh, cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)
        em = cv2.remap(cube.eqe, mxh, myh, cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)
        return img, dep, em, gd

    def _ensure_cube(self, env, props, plants=()):
        """A cube for the current place: built at once the first time, later rebuilt in the background."""
        cube = getattr(self, "cube", None)
        here = (tuple(self.pano_pos), self.pano_map, self.pano_height)
        if cube is None or (cube.pos, cube.map_name, cube.height) != here:
            self.cube = self.build_cube(props, env, plants=plants)
            self._lookup_key = None
            return
        if (cube.key != self.cube_key(env, props) or getattr(self, "cube_dirty", False)) and not getattr(self, "_cube_busy", False):
            self._cube_busy = True; self.cube_dirty = False
            snap = list(props); psnap = list(plants)

            def work():
                try:
                    c = self.build_cube(snap, env, plants=psnap)
                    if (c.pos, c.map_name, c.height) == (tuple(self.pano_pos), self.pano_map, self.pano_height):
                        self.cube = c; self._lookup_key = None
                finally:
                    self._cube_busy = False
            import threading
            threading.Thread(target=work, daemon=True, name="sim-cube").start()

    # ---- drawing of single things ----
    def _plant_box(self, p):
        cam = self.cam
        base = cam.project(p.x, p.y, 0.0)
        top = cam.project(p.x, p.y, p.height + p.crown * 0.6)
        if base is None or top is None:
            return None
        s = cam.f / base[2]
        hw = (p.crown * 1.7 + 0.35 * p.height) * s
        return base[0] - hw, top[1] - 2, base[0] + hw, base[1] + 0.15 * s + 2, base[2]

    def _plant(self, img, p, env):
        cam = self.cam
        base = cam.project(p.x, p.y, 0.0)
        if base is None:
            return
        s = cam.f / base[2]
        if base[0] < -p.crown * 3 * s or base[0] > cam.W + p.crown * 3 * s:
            return
        w = env["wind"]; t = env["t"]
        gust = 0.6 + 0.4 * math.sin(t * 0.37 + p.phase * 3)
        amp = (w * w * 0.16 + w * 0.03) * p.height * gust
        sway = amp * math.sin(t * p.freq * 2 * math.pi * (0.6 + w) + p.phase)
        col = p.color
        if p.kind == "tree":
            top = cam.project(p.x, p.y, p.height * 0.55)
            if top is None:
                return
            cv2.line(img, _ipt(base), _ipt((top[0] + sway * s * 0.3, top[1])), (40, 55, 75), _th(0.35 * s),
                     cv2.LINE_AA if s > 3 else cv2.LINE_8)
            cz = p.height * 0.68
        else:
            cz = p.height * 0.45
        c = cam.project(p.x, p.y, cz)
        if c is None:
            return
        R = p.crown * s
        if R < 5:                                                       # far away: one blob is enough
            cv2.circle(img, _ipt((c[0] + sway * s * 0.5, c[1])), _th(R * 1.15), col, -1, cv2.LINE_AA)
            return
        for i, (bx, by, br) in enumerate(p.blobs):
            flick = amp * 0.5 * math.sin(t * (3.0 + i * 0.7) * (0.5 + w) + i * 1.7 + p.phase)
            cxp = c[0] + (bx * p.crown + sway * (0.5 + 0.5 * by) + flick) * s
            cyp = c[1] - by * p.crown * s
            shade = 0.82 + 0.1 * ((i * 37) % 5) / 4.0
            cv2.circle(img, _ipt((cxp, cyp)), _th(br * R), _shade(col, shade), -1, cv2.LINE_AA)

    def _prop_box(self, pr):
        cam = self.cam
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for z in (0.0, pr.h):
                    p = cam.project(pr.x + sx * pr.w / 2, pr.y + sy * pr.d / 2, z)
                    if p is None:
                        return None
                    pts.append(p)
        return (min(p[0] for p in pts) - 2, min(p[1] for p in pts) - 2, max(p[0] for p in pts) + 2, max(p[1] for p in pts) + 2,
                min(p[2] for p in pts))

    def _mountain(self, img, pr, env, depth=None, temp=None):
        """A big mountain as a shaded mesh: grass at the foot, rock above, snow on top; lit by the sun.
        Everything per quad is computed with numpy; only the final filling is a loop."""
        cam = self.cam
        V = mountain_mesh(pr)
        if temp is not None:                                            # thermal picture: 80 x 62 pixels, a coarse mesh will do
            V = V[::3, ::3]
        NR, NS = V.shape[:2]
        elev, az = env["sun"] if env else (40.0, 3.0)
        ckey = (round(elev), round(az, 1), temp is None)
        cache = getattr(pr, "_mcol", None) if temp is None else None
        if cache is None or cache[0] != ckey:
            A = V[:-1, :]; B = np.roll(V[:-1, :], -1, axis=1); C = np.roll(V[1:, :], -1, axis=1); E = V[1:, :]
            n = np.cross(C - A, B - E)
            n /= np.maximum(1e-6, np.linalg.norm(n, axis=-1, keepdims=True))
            n *= np.where(n[..., 2:3] < 0, -1.0, 1.0)
            el = math.radians(max(5.0, elev))
            sun = np.array([math.sin(az + math.pi) * math.cos(el), math.cos(az + math.pi) * math.cos(el), math.sin(el)], np.float32)
            lit = 0.45 + 0.55 * np.clip(n @ sun, 0, 1)
            hf = ((A[..., 2] + C[..., 2]) / 2) / max(1.0, pr.h)
            jj = np.arange(NS)[None, :]
            snow = hf > 0.72 + 0.04 * np.sin(jj * 1.7)
            rock = (hf > 0.3) & ~snow
            col = np.where(snow[..., None], np.array([235, 236, 240]) * (0.75 + 0.25 * lit[..., None]),
                           np.where(rock[..., None], np.array([95, 105, 115]) * lit[..., None],
                                    np.array([60, 115, 80]) * (lit * (0.9 + 0.2 * hf))[..., None]))
            cache = (ckey, np.clip(col, 0, 255).astype(np.int32), hf, (A + C) / 2)
            if temp is None:
                pr._mcol = cache
        _k, col, hf, centre = cache
        X, Y, Z = V[..., 0] - cam.px, V[..., 1] - cam.py, V[..., 2] - cam.height
        rt, up, fw = cam.rt, cam.up, cam.fw
        xc = X * rt[0] + Y * rt[1]; yc = X * up[0] + Y * up[1] + Z * up[2]; zc = X * fw[0] + Y * fw[1] + Z * fw[2]
        ok = zc > 2.0
        zs = np.maximum(zc, 2.0)
        U = np.clip(cam.cx + cam.f * xc / zs, -20000, 20000); W_ = np.clip(cam.cy - cam.f * yc / zs, -20000, 20000)
        r = lambda a: np.roll(a, -1, axis=1)
        okq = ok[:-1] & r(ok[:-1]) & ok[1:] & r(ok[1:])
        P = np.stack([np.stack([U[:-1], W_[:-1]], -1), np.stack([r(U[:-1]), r(W_[:-1])], -1),
                      np.stack([r(U[1:]), r(W_[1:])], -1), np.stack([U[1:], W_[1:]], -1)], 2)        # (NR-1, NS, 4, 2)
        x0, x1 = P[..., 0].min(-1), P[..., 0].max(-1); y0, y1 = P[..., 1].min(-1), P[..., 1].max(-1)
        okq &= (x1 >= 0) & (x0 < cam.W) & (y1 >= 0) & (y0 < cam.H)
        d = np.hypot(centre[..., 0] - cam.px, centre[..., 1] - cam.py)
        idx = np.argwhere(okq)
        if not len(idx):
            return
        order = idx[np.argsort(-d[okq])]
        P = np.round(P).astype(np.int32)
        aa = cv2.LINE_AA if temp is None else cv2.LINE_8
        for i_, j_ in order:
            poly = P[i_, j_]
            if temp is not None:
                cv2.fillConvexPoly(img, poly, float(temp - 6.0 * hf[i_, j_]), aa)
            else:
                c = col[i_, j_]
                cv2.fillConvexPoly(img, poly, (int(c[0]), int(c[1]), int(c[2])), aa)
            if depth is not None:
                cv2.fillConvexPoly(depth, poly, float(d[i_, j_]))
        if self.emis is not None and depth is not None:
            for i_, j_ in order[:: max(1, len(order) // 400)]:
                cv2.fillConvexPoly(self.emis, P[i_, j_], 0)

    def _tower(self, img, pr, env, depth=None):
        """A high-rise: the two or three sides facing the camera, each in its own shade, floor lines, window columns,
        some windows lit at night, a roof."""
        cam = self.cam
        hw, hd = pr.w / 2.0, pr.d / 2.0
        C = [(pr.x - hw, pr.y - hd), (pr.x + hw, pr.y - hd), (pr.x + hw, pr.y + hd), (pr.x - hw, pr.y + hd)]
        P = [cam.project(x, y, 0.0, near=0.3) for x, y in C]
        T = [cam.project(x, y, pr.h, near=0.3) for x, y in C]
        if any(p is None for p in P + T):                               # partly behind the camera: clipped faces only
            if all(p is None for p in P + T) and math.hypot(pr.x - cam.px, pr.y - cam.py) > max(pr.w, pr.d):
                return
            for i in range(4):
                (ax, ay), (bx, by) = C[i], C[(i + 1) % 4]
                nx, ny = (by - ay), -(bx - ax)
                if nx * (cam.px - (ax + bx) / 2) + ny * (cam.py - (ay + by) / 2) <= 0:
                    continue
                poly = clip_project(cam, [(ax, ay, 0.0), (bx, by, 0.0), (bx, by, pr.h), (ax, ay, pr.h)])
                if poly is not None:
                    shade = 0.72 + 0.28 * abs(math.cos(math.atan2(nx, ny) - 0.6))
                    cv2.fillPoly(img, [poly], _shade(pr.color, shade), cv2.LINE_AA)
                    if depth is not None:
                        cv2.fillPoly(depth, [poly], float(max(0.3, math.hypot((ax + bx) / 2 - cam.px, (ay + by) / 2 - cam.py) - 2)))
                        if self.emis is not None:
                            cv2.fillPoly(self.emis, [poly], 0)
            if cam.height > pr.h:
                poly = clip_project(cam, [(x, y, pr.h) for x, y in C])
                if poly is not None:
                    cv2.fillPoly(img, [poly], _shade(pr.color, 0.6), cv2.LINE_AA)
            return
        base = pr.color
        floors = max(1, int(pr.h / 3.4))
        seed = int(abs(pr.x * 7 + pr.y * 13)) % 997
        for i in range(4):
            j = (i + 1) % 4
            (ax, ay), (bx, by) = C[i], C[j]
            nx, ny = (by - ay), -(bx - ax)                              # outward normal of this side
            if nx * (cam.px - (ax + bx) / 2) + ny * (cam.py - (ay + by) / 2) <= 0:
                continue                                                 # faces away from the camera
            face = np.array([_ipt(P[i]), _ipt(P[j]), _ipt(T[j]), _ipt(T[i])], np.int32)
            shade = 0.72 + 0.28 * abs(math.cos(math.atan2(nx, ny) - 0.6))
            cv2.fillConvexPoly(img, face, _shade(base, shade), cv2.LINE_AA)
            if depth is not None:                                        # drawn far to near: plain overwrite is right
                cv2.fillConvexPoly(depth, face, float(min(P[i][2], P[j][2])))
                if self.emis is not None:
                    cv2.fillConvexPoly(self.emis, face, 0)
            # floors, window columns and lit windows: one perspective map per facade (u along the wall, v up)
            Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [1, 0], [1, 1], [0, 1]]),
                                             np.float32([P[i][:2], P[j][:2], T[j][:2], T[i][:2]]))
            wlen = math.hypot(bx - ax, by - ay)
            cols = max(2, int(wlen / 3.0))
            glass = _shade(base, shade * 0.55)
            px_h = abs(P[i][1] - T[i][1])
            if px_h < 30 or (depth is not None and id(pr) not in getattr(self, "_detailed", ())):                                              # far away: plain faces, a few lit windows
                if self.emis is not None and depth is not None and px_h > 6:
                    rng = np.random.default_rng(seed * 4 + i)
                    n = int(min(20 if px_h < 30 else 70, floors * cols // 8))
                    if n > 0:
                        f = rng.integers(0, floors, n).astype(np.float32); c = rng.integers(0, cols, n).astype(np.float32)
                        q = np.stack([(c + 0.5) / cols, (f + 0.5) / floors], 1).reshape(-1, 1, 2).astype(np.float32)
                        pts = cv2.perspectiveTransform(q, Hm).reshape(-1, 2)
                        xs = np.clip(pts[:, 0].astype(int), 0, self.emis.shape[1] - 1); ys = np.clip(pts[:, 1].astype(int), 0, self.emis.shape[0] - 1)
                        self.emis[ys, xs] = 255
                        if px_h > 60:                                   # a bit bigger windows when closer
                            self.emis[np.minimum(ys + 1, self.emis.shape[0] - 1), xs] = 255
                continue
            if px_h / floors > 2.0:
                step = max(1, int(floors / max(1, px_h / 6)))
                fl = np.arange(1, floors, step, dtype=np.float32) / floors
                if len(fl):
                    pts = cv2.perspectiveTransform(np.stack([np.stack([np.zeros_like(fl), fl], 1), np.stack([np.ones_like(fl), fl], 1)], 1)
                                                   .reshape(-1, 1, 2), Hm).reshape(-1, 2, 2)
                    cv2.polylines(img, list(np.round(pts).astype(np.int32)), False, glass, 1, cv2.LINE_AA)
                cl = np.arange(1, cols, dtype=np.float32) / cols
                pts = cv2.perspectiveTransform(np.stack([np.stack([cl, np.zeros_like(cl)], 1), np.stack([cl, np.ones_like(cl)], 1)], 1)
                                               .reshape(-1, 1, 2), Hm).reshape(-1, 2, 2)
                cv2.polylines(img, list(np.round(pts).astype(np.int32)), False, glass,
                              max(1, int(abs(P[j][0] - P[i][0]) / cols * 0.35)), cv2.LINE_AA)
                rng = np.random.default_rng(seed * 4 + i)
                n = min(60, floors * cols // 5) if self.emis is not None else 0
                if n > 0:                                              # some lit windows (glow at night)
                    f = rng.integers(0, floors, n).astype(np.float32); c = rng.integers(0, cols, n).astype(np.float32)
                    u0, u1 = (c + 0.2) / cols, (c + 0.8) / cols
                    v0, v1 = (f + 0.25) / floors, (f + 0.75) / floors
                    quad = np.stack([np.stack([u0, v0], 1), np.stack([u1, v0], 1), np.stack([u1, v1], 1), np.stack([u0, v1], 1)], 1)
                    pts = cv2.perspectiveTransform(quad.reshape(-1, 1, 2).astype(np.float32), Hm).reshape(-1, 4, 2)
                    if depth is not None:
                        cv2.fillPoly(self.emis, list(np.round(pts).astype(np.int32)), 255)
                    else:
                        self._pending_emis.extend(np.round(pts).astype(np.int32))
        if cam.height > pr.h:                                            # seen from above: the roof
            roof = np.array([_ipt(p) for p in T], np.int32)
            cv2.fillConvexPoly(img, roof, _shade(base, 0.6), cv2.LINE_AA)
            if depth is not None:
                cv2.fillConvexPoly(depth, roof, float(min(p[2] for p in T)))
        if pr.name == "tower" and pr.h > 60 and abs(P[0][1] - T[0][1]) > 60:   # antenna with a red light (when close enough)
            a = cam.project(pr.x, pr.y, pr.h, near=0.3); b = cam.project(pr.x, pr.y, pr.h + pr.h * 0.08, near=0.3)
            if a and b:
                cv2.line(img, _ipt(a), _ipt(b), (90, 90, 90), 1, cv2.LINE_AA)
                cv2.circle(img, _ipt(b), 2, (40, 40, 255), -1)

    def _prop(self, img, pr, env):
        cam = self.cam
        hw, hd = pr.w / 2.0, pr.d / 2.0
        corners = [(pr.x + sx * hw, pr.y + sy * hd) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        pts_lo = [cam.project(x, y, 0.0) for x, y in corners]
        if any(p is None for p in pts_lo):                              # partly behind the camera: clipped box faces
            if pr.name in ("post", "umbrella", "mountain") or math.hypot(pr.x - cam.px, pr.y - cam.py) > max(pr.w, pr.d) + 3:
                return
            for i in range(4):
                (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
                poly = clip_project(cam, [(ax, ay, 0.0), (bx, by, 0.0), (bx, by, pr.h), (ax, ay, pr.h)])
                if poly is not None:
                    cv2.fillPoly(img, [poly], _shade(pr.color, 0.8 + 0.1 * (i % 2)), cv2.LINE_AA)
            poly = clip_project(cam, [(x, y, pr.h) for x, y in corners])
            if poly is not None:
                cv2.fillPoly(img, [poly], _shade(pr.color, 0.65) if not pr.ridge else (50, 60, 120), cv2.LINE_AA)
            return
        if pr.name == "mountain":
            return self._mountain(img, pr, env)
        if pr.name in ("tower", "block"):
            return self._tower(img, pr, env)
        if pr.name == "table":
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                a = cam.project(pr.x + sx * (hw - 0.08), pr.y + sy * (hd - 0.08), 0.0)
                b = cam.project(pr.x + sx * (hw - 0.08), pr.y + sy * (hd - 0.08), pr.h - 0.05)
                if a and b:
                    cv2.line(img, _ipt(a), _ipt(b), _shade(pr.color, 0.7), _th(0.06 * cam.f / a[2]), cv2.LINE_AA)
            top = [cam.project(x, y, z) for x, y in corners for z in (pr.h - 0.05, pr.h)]
            if all(top):
                cv2.fillConvexPoly(img, cv2.convexHull(np.array([_ipt(q) for q in top], np.int32)), pr.color, cv2.LINE_AA)
            return
        if pr.name == "post" or pr.name == "umbrella":
            a, b = cam.project(pr.x, pr.y, 0.0), cam.project(pr.x, pr.y, pr.h)
            if a and b:
                s = cam.f / a[2]
                cv2.line(img, _ipt(a), _ipt(b), (100, 100, 105), _th(0.12 * s), cv2.LINE_AA)
                if pr.name == "post":
                    cv2.ellipse(img, _ipt(b), (_th(0.35 * s), _th(0.1 * s)), 0, 0, 360, (60, 60, 60), -1, cv2.LINE_AA)
                else:
                    cv2.ellipse(img, _ipt(b), (_th(1.1 * s), _th(0.35 * s)), 0, 180, 360, pr.color, -1, cv2.LINE_AA)
            return
        eave = 0.0 if pr.name == "tent" else pr.h * 0.62
        if pr.ridge:
            top = [cam.project(pr.x - hw, pr.y, pr.h), cam.project(pr.x + hw, pr.y, pr.h)]
            if eave > 0:
                top += [cam.project(x, y, eave) for x, y in corners]
        else:
            top = [cam.project(x, y, pr.h) for x, y in corners]
        if any(p is None for p in top):
            return
        pts = np.array([_ipt(p) for p in pts_lo + top], np.int32)
        hull = cv2.convexHull(pts)
        cv2.fillConvexPoly(img, hull, pr.color, cv2.LINE_AA)
        if pr.ridge and eave > 0:                                   # darker roof above the eaves
            roof = [cam.project(x, y, eave) for x, y in corners] + [cam.project(pr.x - hw, pr.y, pr.h), cam.project(pr.x + hw, pr.y, pr.h)]
            if all(roof):
                cv2.fillConvexPoly(img, cv2.convexHull(np.array([_ipt(p) for p in roof], np.int32)), (50, 60, 120), cv2.LINE_AA)
        if pr.name == "car":
            cab = [cam.project(pr.x + sx * hw * 0.9, pr.y + sy * hd * 0.5, z) for sx in (-1, 1) for sy in (-1, 1) for z in (pr.h * 0.55, pr.h)]
            if all(cab):
                cv2.fillConvexPoly(img, cv2.convexHull(np.array([_ipt(p) for p in cab], np.int32)), (70, 60, 55), cv2.LINE_AA)
        elif pr.name == "house":
            for wx in (-0.3, 0.05, 0.3):
                win = [cam.project(pr.x + wx * pr.w + dx, pr.y - hd, z) for dx, z in ((-0.5, 1.0), (0.5, 1.0), (0.5, 2.0), (-0.5, 2.0))]
                if all(win):
                    cv2.fillConvexPoly(img, np.array([_ipt(p) for p in win], np.int32), (90, 80, 60), cv2.LINE_AA)
        if pr.name == "tent":
            door = [cam.project(pr.x - 0.3, pr.y - hd, 0.0), cam.project(pr.x + 0.3, pr.y - hd, 0.0), cam.project(pr.x, pr.y - hd, pr.h * 0.8)]
            if all(door):
                cv2.fillConvexPoly(img, np.array([_ipt(p) for p in door], np.int32), _shade(pr.color, 0.45), cv2.LINE_AA)
        elif pr.name == "caravan":
            win = [cam.project(pr.x + dx, pr.y - hd, z) for dx, z in ((-1.6, 1.3), (-0.2, 1.3), (-0.2, 2.0), (-1.6, 2.0))]
            if all(win):
                cv2.fillConvexPoly(img, np.array([_ipt(p) for p in win], np.int32), (70, 60, 50), cv2.LINE_AA)
            stripe = [cam.project(pr.x + dx, pr.y - hd, z) for dx, z in ((-hw, 0.55), (hw, 0.55), (hw, 0.75), (-hw, 0.75))]
            if all(stripe):
                cv2.fillConvexPoly(img, np.array([_ipt(p) for p in stripe], np.int32), (60, 90, 180), cv2.LINE_AA)
            for wx in (-1.0, 1.0):
                wp = cam.project(pr.x + wx, pr.y - hd, 0.33)
                if wp:
                    cv2.circle(img, _ipt(wp), _th(0.33 * cam.f / wp[2]), (30, 30, 30), -1, cv2.LINE_AA)

    def _drawn_test(self, img, depth, box, fn):
        """Draw something in front of the cached buildings: only the pixels where it is nearer than what is there."""
        H, W = depth.shape
        x0, x1 = max(0, int(box[0]) - 3), min(W, int(box[2]) + 4)
        y0, y1 = max(0, int(box[1]) - 3), min(H, int(box[3]) + 4)
        if x1 <= x0 or y1 <= y0:
            return
        old = img[y0:y1, x0:x1].copy()
        fn()
        new = img[y0:y1, x0:x1]
        ch = (new != old).any(axis=2)
        dsub = depth[y0:y1, x0:x1]
        vis = ch & (dsub > box[4] * 0.75 - 0.5)                     # the ground right at its feet is a little nearer
        hid = ch & ~vis
        if hid.any():
            new[hid] = old[hid]                                      # behind a building: stays hidden
        dsub[vis] = box[4]
        if self.emis is not None:
            self.emis[y0:y1, x0:x1][vis] = 0

    def _drawn(self, img, depth, box, fn):
        _drawn_owner["r"] = self
        return Renderer._drawn_impl(img, depth, box, fn)

    @staticmethod
    def _drawn_impl(img, depth, box, fn):
        """Draw something and give exactly the pixels it covered its distance in the depth map."""
        H, W = depth.shape
        x0, x1 = max(0, int(box[0]) - 3), min(W, int(box[2]) + 4)
        y0, y1 = max(0, int(box[1]) - 3), min(H, int(box[3]) + 4)
        if x1 <= x0 or y1 <= y0:
            fn(); return
        old = img[y0:y1, x0:x1].copy()
        fn()
        ch = (img[y0:y1, x0:x1] != old).any(axis=2)
        sub = depth[y0:y1, x0:x1]
        sub[ch] = np.minimum(sub[ch], box[4])
        self_ = _drawn_owner.get("r")
        if self_ is not None and getattr(self_, "emis", None) is not None and self_.emis.shape == depth.shape:
            self_.emis[y0:y1, x0:x1][ch] = 0                         # something nearer covers lit windows behind it
            for poly in self_._pending_emis:
                cv2.fillConvexPoly(self_.emis, poly, 255)
            self_._pending_emis = []

    def _person(self, img, e, x=None, y=None, seat=None, cam=None, pal=None):
        """A walking person. seat = hip height when riding (bicycle / motorcycle). pal = other colours (thermal)."""
        cam = cam or self.cam
        pal = pal or {"pants": e.pants, "shirt": e.shirt, "skin": e.skin, "shoe": (35, 35, 35), "hair": (30, 40, 50)}
        aa = cv2.LINE_AA if img.dtype == np.uint8 else cv2.LINE_8
        x = e.x if x is None else x; y = e.y if y is None else y
        H = e.height * e.crouch
        fx, fy = math.sin(e.heading), math.cos(e.heading)
        rx, ry = fy, -fx
        sw = math.sin(e.phase) * (0.32 if e.speed > 2.5 else 0.22) * min(1.0, e.speed / 0.8) if seat is None else 0.0
        hip_z = (0.52 * H) if seat is None else seat
        sh_z = hip_z + 0.33 * e.height * (0.9 if e.crouch < 1 else 1.0)
        head_z = sh_z + 0.13 * e.height
        P = lambda dx, dy, z: cam.project(x + dx, y + dy, z)
        hip = P(0, 0, hip_z); sh = P(0, 0, sh_z); head = P(0, 0, head_z)
        if hip is None or sh is None or head is None:
            return None
        s = cam.f / hip[2]
        # legs
        if seat is None:
            feet = [P(fx * sw, fy * sw, 0.0), P(-fx * sw, -fy * sw, 0.0)]
            knees = [P(fx * sw * 0.6, fy * sw * 0.6, hip_z * 0.5), P(-fx * sw * 0.6, -fy * sw * 0.6, hip_z * 0.5)]
        else:
            pd = math.sin(e.phase) * 0.18
            feet = [P(fx * pd, fy * pd, 0.3 + pd), P(-fx * pd, -fy * pd, 0.3 - pd)]
            knees = [P(fx * 0.35, fy * 0.35, hip_z - 0.05 + pd * 0.5), P(fx * 0.35 + rx * 0.1, fy * 0.35 + ry * 0.1, hip_z - 0.05 - pd * 0.5)]
        lt = _th(0.13 * s)
        for k, ft in zip(knees, feet):
            if k and ft:
                cv2.line(img, _ipt(hip), _ipt(k), pal["pants"], lt, aa)
                cv2.line(img, _ipt(k), _ipt(ft), pal["pants"], lt, aa)
                cv2.circle(img, _ipt(ft), _th(0.06 * s), pal["shoe"], -1)
        # torso
        tw = 0.21 * s
        tor = np.array([_ipt((hip[0] - tw * 0.9, hip[1])), _ipt((hip[0] + tw * 0.9, hip[1])),
                        _ipt((sh[0] + tw, sh[1])), _ipt((sh[0] - tw, sh[1]))], np.int32)
        cv2.fillConvexPoly(img, tor, pal["shirt"], aa)
        # arms swing against the legs
        aw = -sw * 0.8
        for side in (-1, 1):
            hand = P(fx * aw * side * -1 + rx * 0.22 * side, fy * aw * side * -1 + ry * 0.22 * side, hip_z - 0.04)
            if seat is not None:
                hand = P(fx * 0.5 + rx * 0.2 * side, fy * 0.5 + ry * 0.2 * side, sh_z - 0.15)
            sp = (sh[0] + side * tw * 0.95, sh[1] + 0.03 * s)
            if hand:
                cv2.line(img, _ipt(sp), _ipt(hand), pal["shirt"], _th(0.085 * s), aa)
                cv2.circle(img, _ipt(hand), _th(0.045 * s), pal["skin"], -1)
        # neck + head
        cv2.line(img, _ipt(sh), _ipt(head), pal["skin"], _th(0.07 * s), aa)
        hr = 0.105 * s
        cv2.circle(img, _ipt((head[0], head[1] - hr * 0.5)), _th(hr), pal["skin"], -1, aa)
        cv2.ellipse(img, _ipt((head[0], head[1] - hr * 0.85)), (_th(hr), _th(hr * 0.7)), 0, 180, 360, pal["hair"], -1, aa)
        top = cam.project(x, y, head_z + 0.12)
        foot = cam.project(x, y, 0.0)
        return (hip, top, foot, s)

    def _animal(self, img, e, cam=None, pal=None):
        cam = cam or self.cam
        _sh = _shade if pal is None else (lambda c, k: c)
        aa = cv2.LINE_AA if img.dtype == np.uint8 else cv2.LINE_8
        fx, fy = math.sin(e.heading), math.cos(e.heading)
        L, H = e.length, e.height
        if e.kind == "bird":
            c = cam.project(e.x, e.y, e.z)
            if c is None:
                return
            s = cam.f / c[2]
            flap = math.sin(e.phase) * 0.25
            rx, ry = fy, -fx
            wl = cam.project(e.x - rx * 0.32, e.y - ry * 0.32, e.z + flap)
            wr = cam.project(e.x + rx * 0.32, e.y + ry * 0.32, e.z + flap)
            if wl and wr:
                cv2.line(img, _ipt(wl), _ipt(c), (pal or e.color), _th(0.05 * s), aa)
                cv2.line(img, _ipt(c), _ipt(wr), (pal or e.color), _th(0.05 * s), aa)
            cv2.circle(img, _ipt(c), _th(0.06 * s), (pal or e.color), -1, aa)
            return
        body_z = H * (0.62 if e.kind != "horse" else 0.72)
        back = cam.project(e.x - fx * L * 0.42, e.y - fy * L * 0.42, body_z)
        front = cam.project(e.x + fx * L * 0.42, e.y + fy * L * 0.42, body_z)
        if back is None or front is None:
            return
        s = cam.f / ((back[2] + front[2]) / 2)
        thick = {"bear": 0.62, "sheep": 0.55, "horse": 0.36, "dog": 0.36, "cat": 0.32}.get(e.kind, 0.4) * H
        col = pal or e.color
        # legs (drawn first, the body covers the hips)
        sw = math.sin(e.phase) * 0.18 * L * min(1.0, e.speed / 0.6)
        for i, off in enumerate((0.36, 0.28, -0.3, -0.38)):
            ph = sw if i in (0, 3) else -sw
            top = cam.project(e.x + fx * L * off, e.y + fy * L * off, body_z)
            ft = cam.project(e.x + fx * (L * off + ph), e.y + fy * (L * off + ph), 0.0)
            if top and ft:
                cv2.line(img, _ipt(top), _ipt(ft), _sh(col, 0.8 if i % 2 else 1.0), _th((0.09 if e.kind != "bear" else 0.18) * s * H / 0.7), aa)
        cv2.line(img, _ipt(back), _ipt(front), col, _th(thick * s), aa)
        # head / neck
        if e.kind == "horse":
            nk = cam.project(e.x + fx * L * 0.62, e.y + fy * L * 0.62, H * 1.25)
            if nk:
                cv2.line(img, _ipt(front), _ipt(nk), col, _th(0.16 * s), aa)
                cv2.circle(img, _ipt(nk), _th(0.12 * s), col, -1, aa)
                for side in (-0.06, 0.06):
                    ear = cam.project(e.x + fx * L * 0.6 + fy * side, e.y + fy * L * 0.6 - fx * side, H * 1.42)
                    if ear:
                        cv2.line(img, _ipt(nk), _ipt(ear), col, _th(0.05 * s), aa)
        else:
            hz = body_z + H * (0.22 if e.kind != "sheep" else 0.08)
            hd = cam.project(e.x + fx * L * 0.58, e.y + fy * L * 0.58, hz)
            if hd:
                hr = {"bear": 0.24, "dog": 0.13, "cat": 0.08, "sheep": 0.12}.get(e.kind, 0.12)
                cv2.circle(img, _ipt(hd), _th(hr * s * (H / 0.6 if e.kind == "dog" else 1.0)), _sh(col, 0.9) if e.kind != "sheep" else ((60, 60, 70) if pal is None else pal), -1, aa)
        # tail
        if e.kind in ("dog", "cat", "horse"):
            tz = body_z + (0.3 if e.kind == "cat" else 0.1) * H
            tl = cam.project(e.x - fx * L * 0.65, e.y - fy * L * 0.65, tz + 0.05 * math.sin(e.phase * 2))
            if tl:
                cv2.line(img, _ipt(back), _ipt(tl), col, _th(0.04 * s), aa)

    def _plane(self, img, e, cam=None, temp=None):
        """An airliner seen from below / the side: fuselage, swept wings, tail fin, blinking lights."""
        cam = cam or self.cam
        fx, fy = math.sin(e.heading), math.cos(e.heading)
        rx, ry = fy, -fx
        L, Wn, z = e.length, e.width, e.z
        P = lambda f, r_, dz=0.0: cam.project(e.x + fx * f + rx * r_, e.y + fy * f + ry * r_, z + dz, near=1.0)
        nose, tail = P(L * 0.5, 0), P(-L * 0.5, 0, 1.0)
        if nose is None or tail is None:
            return
        s = cam.f / ((nose[2] + tail[2]) / 2)
        body = e.color if temp is None else float(temp)
        dark = _shade(e.color, 0.75) if temp is None else float(temp)
        hot = float(temp + 25.0) if temp is not None else None
        aa = cv2.LINE_AA if temp is None else cv2.LINE_8
        for side in (-1, 1):
            wing = [P(4, 0), P(-6, 0), P(-12, side * Wn / 2), P(-8, side * Wn / 2)]
            stab = [P(-L * 0.42, 0, 0.5), P(-L * 0.5, 0, 0.8), P(-L * 0.52, side * 6.5, 0.8), P(-L * 0.47, side * 6.5, 0.6)]
            for poly, c in ((wing, dark), (stab, dark)):
                if all(poly):
                    cv2.fillConvexPoly(img, np.array([_ipt(p) for p in poly], np.int32), c, aa)
            eng = P(-1, side * Wn * 0.22, -1.2)
            if eng:
                cv2.circle(img, _ipt(eng), _th(1.2 * s), hot if hot is not None else (90, 90, 95), -1, aa)
        cv2.line(img, _ipt(tail), _ipt(nose), body, _th(3.8 * s), aa)
        fin = [P(-L * 0.38, 0, 1.5), P(-L * 0.5, 0, 1.5), P(-L * 0.5, 0, 8.5), P(-L * 0.44, 0, 8.5)]
        if all(fin):
            cv2.fillConvexPoly(img, np.array([_ipt(p) for p in fin], np.int32), body if temp is not None else (60, 60, 160), aa)
        if temp is None and int(time.time() * 1.5) % 2 == 0:              # blinking wing-tip lights
            for side, col in ((-1, (40, 40, 255)), (1, (60, 220, 60))):
                tip = P(-8, side * Wn / 2)
                if tip:
                    cv2.circle(img, _ipt(tip), max(1, _th(0.6 * s)), col, -1)

    def _vehicle(self, img, e):
        cam = self.cam
        fx, fy = math.sin(e.heading), math.cos(e.heading)
        rx, ry = fy, -fx
        if e.kind == "bicycle":
            for off in (-0.55, 0.55):
                c = cam.project(e.x + fx * off, e.y + fy * off, 0.34)
                if c:
                    s = cam.f / c[2]
                    cv2.ellipse(img, _ipt(c), (_th(0.34 * s * max(0.15, abs(math.sin(e.heading - math.atan2(e.x - cam.px, e.y - cam.py))))), _th(0.34 * s)),
                                0, 0, 360, (30, 30, 30), _th(0.04 * s), cv2.LINE_AA)
            a, b = cam.project(e.x - fx * 0.55, e.y - fy * 0.55, 0.34), cam.project(e.x + fx * 0.4, e.y + fy * 0.4, 0.9)
            if a and b:
                cv2.line(img, _ipt(a), _ipt(b), e.color, _th(0.05 * cam.f / a[2]), cv2.LINE_AA)
            self._person(img, e, seat=0.95)
            return
        L, W_, H = e.length, e.width, e.height

        def box(l0, l1, w, z0, z1):
            pts = []
            for l in (l0, l1):
                for side in (-1, 1):
                    gx = e.x + fx * l + rx * side * w / 2
                    gy = e.y + fy * l + ry * side * w / 2
                    for z in (z0, z1):
                        p = cam.project(gx, gy, z, near=0.5)
                        if p is None:
                            return None
                        pts.append(_ipt(p))
            return cv2.convexHull(np.array(pts, np.int32))
        if e.kind == "motorcycle":
            for off in (-0.7, 0.7):
                c = cam.project(e.x + fx * off, e.y + fy * off, 0.32)
                if c:
                    cv2.circle(img, _ipt(c), _th(0.32 * cam.f / c[2]), (25, 25, 25), -1, cv2.LINE_AA)
            hb = box(-0.6, 0.6, 0.35, 0.35, 0.8)
            if hb is not None:
                cv2.fillConvexPoly(img, hb, e.color, cv2.LINE_AA)
            self._person(img, e, seat=0.85)
            return
        if e.kind == "truck":
            cargo = box(-L / 2, L / 2 - 2.2, W_, 0.6, H)
            cab = box(L / 2 - 2.2, L / 2, W_, 0.5, H * 0.8)
            win = box(L / 2 - 1.2, L / 2 + 0.01, W_ * 0.9, H * 0.5, H * 0.75)
            for hull, col in ((cargo, _shade(e.color, 0.9)), (cab, e.color), (win, (60, 50, 45))):
                if hull is not None:
                    cv2.fillConvexPoly(img, hull, col, cv2.LINE_AA)
        else:
            body = box(-L / 2, L / 2, W_, 0.25, H * 0.58)
            cabin = box(-L * 0.28, L * 0.18, W_ * 0.86, H * 0.55, H)
            if body is not None:
                cv2.fillConvexPoly(img, body, e.color, cv2.LINE_AA)
            if cabin is not None:
                cv2.fillConvexPoly(img, cabin, (70, 60, 55), cv2.LINE_AA)
        wr = 0.34 if e.kind == "car" else 0.5
        for off in (-L * 0.32, L * 0.32):
            side = 1 if (rx * (cam.px - e.x) + ry * (cam.py - e.y)) > 0 else -1     # wheels on the side facing the camera
            c = cam.project(e.x + fx * off + rx * side * W_ / 2, e.y + fy * off + ry * side * W_ / 2, wr)
            if c:
                cv2.circle(img, _ipt(c), _th(wr * cam.f / c[2]), (25, 25, 25), -1, cv2.LINE_AA)

    def _shadow(self, mask, x, y, w, h, env):
        elev, az = env["sun"]
        if elev < 4:
            return
        L = min(25.0, h / math.tan(math.radians(elev)))
        dx, dy = -math.sin(az), -math.cos(az)                 # away from the sun
        px, py = dy * w / 2, -dx * w / 2
        quad = [(x + px, y + py), (x - px, y - py), (x - px + dx * L, y - py + dy * L), (x + px + dx * L, y + py + dy * L)]
        pts = [self.cam.project(qx, qy, 0.0, near=0.5) for qx, qy in quad]
        if any(p is None for p in pts):
            return
        cv2.fillConvexPoly(mask, np.array([_ipt(p) for p in pts], np.int32), 255, cv2.LINE_AA)

    # ---- the whole camera picture ----
    def render(self, yaw, pitch, entities, plants, props, env):
        S = SIM
        self.ensure(S["cam_width"], S["cam_height"], S["cam_hfov"], self.pano_height or S["mount_height"])
        self._background(yaw, pitch)
        cam = self.cam
        W, H = cam.W, cam.H

        # only what can be in the picture (big maps have hundreds of trees and buildings)
        all_plants = plants
        plants = [p for p in plants if not cull(p, cam, p.crown * 1.8 + 1, 350.0)]
        entities = [e for e in entities if not cull(e, cam, max(e.length, 1.0) + 1, 6000.0 if e.kind == "plane" else 600.0)]
        elev = env["sun"][0]
        sun_on = S["shadows"] and elev > 4 and S["clouds"] < 0.92
        D = lambda o: math.hypot(o.x - cam.px, o.y - cam.py)

        # ---- static scene from the cube (built once per camera place; turning only samples from it) ----
        self._ensure_cube(env, props, all_plants)
        cube = self.cube
        lkey = (round(yaw, 3), round(pitch, 3), W, H, cam.hfov, id(cube))
        if lkey != getattr(self, "_lookup_key", None):
            si, sd, se, gd = self._cube_lookup(cube)
            self._static = (si, sd, se)
            self.depth = gd                                              # ground only (for shadows of moving things)
            self._lookup_key = lkey
        simg, sdepth, semis = self._static
        img = simg.copy(); depth = sdepth.copy(); self.emis = semis.copy(); self._pending_emis = []

        # shadows of what moves / sways
        if sun_on:
            mask = np.zeros((H, W), np.uint8)
            for e in entities:
                if e.kind not in ("bird", "plane"):
                    self._shadow(mask, e.x, e.y, max(0.35, e.width * (1.0 if e.kind in VEHICLES else 0.8)), e.height * e.crouch, env)
            ys, xs = np.nonzero(mask[::4, ::4])
            if len(xs):                                                   # only where there are shadows
                x0, x1 = max(0, xs.min() * 4 - 8), min(W, xs.max() * 4 + 12)
                y0, y1 = max(0, ys.min() * 4 - 8), min(H, ys.max() * 4 + 12)
                sub = mask[y0:y1, x0:x1]
                sub[sdepth[y0:y1, x0:x1] < self.depth[y0:y1, x0:x1] - 0.01] = 0   # on the ground, not on the buildings
                k = 0.5 * (1.0 - 0.85 * S["clouds"]) * min(1.0, (elev - 4) / 10.0)
                m = cv2.GaussianBlur(sub, (5, 5), 0).astype(np.float32) * (k / 255.0)
                img[y0:y1, x0:x1] = (img[y0:y1, x0:x1] * (1.0 - m[..., None])).astype(np.uint8)

        # trees / bushes (they sway) and everything that moves, far to near, hidden where a building is nearer
        things = [(D(p), "plant", p) for p in plants] + [(D(e), "ent", e) for e in entities]
        things.sort(key=lambda t: -t[0])
        truth_raw = []
        for d, typ, obj in things:
            if typ == "plant":
                box = self._plant_box(obj)
                if box is not None:
                    self._drawn_test(img, depth, box, lambda obj=obj: self._plant(img, obj, env))
            else:
                e = obj
                bb = self.entity_box(e)
                if bb is None:
                    continue
                if e.kind == "plane":
                    fn = lambda e=e: self._plane(img, e)
                elif e.kind == "person":
                    fn = lambda e=e: self._person(img, e)
                elif e.kind in VEHICLES or e.kind == "bicycle":
                    fn = lambda e=e: self._vehicle(img, e)
                else:
                    fn = lambda e=e: self._animal(img, e)
                pad = (bb[3] - bb[1]) * 0.15
                self._drawn_test(img, depth, (bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad, max(0.3, bb[4])), fn)
                truth_raw.append((e, bb))

        # light: ambient through the exposure + lamps on the head (IR for a NoIR camera, white light in colour)
        amb = env["amb"]
        lights = env["lights"]
        lamp = None
        if lights.get("ir") or lights.get("white"):
            lamp = (self.cone * 2.0 / (np.minimum(depth, 1000.0) ** 2 + 16.0)).astype(np.float32)   # soft near the head
        ir_k = 14.0 if lights.get("ir") else 0.0
        wh_k = 22.0 if lights.get("white") else 0.0
        if not S["auto_exposure"]:
            self.gain = 1.0
        g = self.gain
        fog = min(1.0, S["fog"] + 0.25 * S["rain"])
        if lamp is None and fog < 0.01 and abs(amb * g - 1.0) < 0.02:
            out = img
        elif lamp is None and fog < 0.01:
            out = cv2.convertScaleAbs(img, alpha=amb * g)
        else:
            f = img.astype(np.float32)
            gl = amb * g
            if lamp is not None:
                if wh_k:
                    m = (gl + wh_k * g * lamp)[..., None]
                    out_f = f * m
                else:
                    out_f = f * gl
                if ir_k:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
                    out_f += (ir_k * g * lamp * gray)[..., None]
            else:
                out_f = f * gl
            if fog >= 0.01:
                vis = 220.0 * (1.0 - fog) ** 2 + 6.0
                fk = (1.0 - np.exp(-np.minimum(depth, 3000.0) / vis))[..., None]
                out_f = out_f * (1 - fk) + np.array([200, 200, 200], np.float32) * gl * fk
            out = np.clip(out_f, 0, 255).astype(np.uint8)
        if S["auto_exposure"]:                                         # exposure adapts within about a second
            m = float(out[::8, ::8].mean()) + 1.0
            want = max(1.0, min(24.0, self.gain * (105.0 / m)))
            self.gain = math.exp(math.log(self.gain) + (math.log(want) - math.log(self.gain)) * 0.15)
        # lit windows of buildings shine by themselves at dusk / night
        night = max(0.0, min(1.0, 1.0 - amb * 4.0))
        if night > 0.05 and self.emis.any():
            k = (self.emis.astype(np.float32) * (night * 0.9 / 255.0))[..., None]
            out = (out * (1 - k) + np.array([120, 205, 255], np.float32) * k).astype(np.uint8)
        # high gain: colours fade (the sensor is close to its limit)
        if g > 8.0:
            k = min(0.5, (g - 8.0) / 24.0)
            gray = cv2.cvtColor(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
            out = cv2.addWeighted(out, 1 - k, gray, k, 0)

        # rain streaks
        if S["rain"] > 0.01:
            n = int(S["rain"] * 1500)
            rng = np.random.default_rng()
            xs = rng.integers(0, W, n); ys = rng.integers(-40, H, n)
            ln = rng.integers(16, 44, n)
            slant = env["wind"] * 0.6
            p1 = np.stack([xs, ys], 1); p2 = np.stack([xs + (ln * slant).astype(int), ys + ln], 1)
            ov = np.zeros_like(out)
            br = int(55 + 40 * min(1.0, amb * g))
            cv2.polylines(ov, list(np.stack([p1, p2], 1).astype(np.int32)), False, (br, br, br), 2)
            out = cv2.add(out, ov)

        # lens: covered / dew
        if S["lens_cover"]:
            out = np.full_like(out, 9)
            cv2.circle(out, (W // 3, H // 2), W // 3, (14, 14, 14), -1)
            out = cv2.GaussianBlur(out, (0, 0), 25)
        elif S["lens_blur"] > 0.01:
            b = float(S["lens_blur"])
            out = cv2.GaussianBlur(out, (0, 0), 0.8 + 9.0 * b)
            out = cv2.addWeighted(out, 1 - 0.55 * b, np.full_like(out, int(out.mean())), 0.55 * b, 0)

        # sensor noise
        sigma = S["cam_noise"] * (0.8 + 0.55 * math.sqrt(g))
        if sigma > 0.3:
            if self._noise is None or self._noise.shape != out.shape:
                self._noise = np.zeros(out.shape, np.int16)
            cv2.randn(self._noise, (0, 0, 0), (sigma, sigma, sigma))
            o16 = out.astype(np.int16); o16 += self._noise
            np.clip(o16, 0, 255, out=o16)
            out = o16.astype(np.uint8)

        truth = self._truth(truth_raw, depth, env, amb * g, lamp, ir_k + wh_k)
        self.last_out = out
        return out, truth

    def entity_box(self, e, cam=None):
        """Screen box (x0, y0, x1, y1, distance) of an entity, None if behind the camera."""
        cam = cam or self.cam
        fx, fy = math.sin(e.heading), math.cos(e.heading)
        rx, ry = fy, -fx
        hl, hw = max(e.length, 0.3) / 2, max(e.width, 0.3) / 2
        z0 = e.z - 0.15 if e.kind == "bird" else (e.z - 2.0 if e.kind == "plane" else 0.0)
        z1 = e.z + 0.15 if e.kind == "bird" else (e.z + 7.0 if e.kind == "plane" else e.height * e.crouch + (0.12 if e.kind == "person" else 0.0))
        if e.kind == "horse":
            z1 = e.height * 1.45
        xs, ys, ds = [], [], []
        for l in (-hl, hl):
            for w in (-hw, hw):
                for z in (z0, z1):
                    p = cam.project(e.x + fx * l + rx * w, e.y + fy * l + ry * w, z, near=0.3)
                    if p is None:
                        return None
                    xs.append(p[0]); ys.append(p[1]); ds.append(p[2])
        return min(xs), min(ys), max(xs), max(ys), min(ds)

    def _truth(self, raw, depth, env, gl, lamp, lamp_k):
        """What is really in the picture: box (0..1), share inside the picture, distance, light on it, hidden share."""
        cam = self.cam
        W, H = cam.W, cam.H
        out = []
        for e, (x0, y0, x1, y1, d) in raw:
            area = max(1.0, (x1 - x0) * (y1 - y0))
            cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
            if cx1 <= cx0 or cy1 <= cy0:
                continue
            inside = (cx1 - cx0) * (cy1 - cy0) / area
            sub = depth[int(cy0):int(cy1) + 1, int(cx0):int(cx1) + 1]
            hidden = float((sub[::3, ::3] < d - 0.6).mean()) if sub.size else 0.0
            lit = gl
            if lamp is not None:
                lit += lamp_k * self.gain * (self.cone[int(min(H - 1, (cy0 + cy1) / 2)), int(min(W - 1, (cx0 + cx1) / 2))] * 2.0 / (d * d + 16.0))
            cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
            out.append({"id": e.id, "kind": e.kind, "coco": e.coco, "rider": e.has_rider(),
                        "box": (cx0 / W, cy0 / H, cx1 / W, cy1 / H), "full": (x0 / W, y0 / H, x1 / W, y1 / H),
                        "inside": inside, "dist": d, "px_h": (cy1 - cy0), "lit": min(2.0, lit), "hidden": hidden,
                        "center_err": math.degrees(math.atan(math.hypot(cxp - cam.cx, cyp - cam.cy) / cam.f)),
                        "moving": e.moving()})
        return out

    # ---- thermal camera ----
    def render_thermal(self, yaw, pitch, entities, plants, props, env):
        """Degrees C, 80 x 62. Grass and ground stay close to the air temperature (a little warmer in the sun, cooler on
        clear nights), the sky is very cold, people / animals / engines are much warmer than everything around them."""
        S = SIM
        TW, TH, SS = 80, 62, 4
        if self.tcam is None or self.tcam.hfov != S["thermal_hfov"]:
            self.tcam = CamModel(TW * SS, TH * SS, S["thermal_hfov"]); self._tkey = None
        tc = self.tcam
        tc.height = self.pano_height or S["mount_height"]
        tc.px, tc.py = self.pano_pos
        amb = float(S["ambient_c"])
        elev = env["sun"][0]
        sunk = max(0.0, math.sin(math.radians(max(0.0, elev)))) * (1 - 0.6 * S["clouds"]) * (1 - 0.7 * S["rain"])
        day_k = min(1.0, sunk * 2.0)
        clear_night = (1 - day_k) * (1 - S["clouds"]) * (1 - S["rain"])
        ground = amb + 3.0 * sunk - 2.5 * clear_night
        self._t = {"amb": amb, "sunk": sunk, "day_k": day_k, "ground": ground, "wet": 2.0 * S["rain"]}
        key = (round(yaw, 2), round(pitch, 2), tc.hfov, tc.height, tc.px, tc.py, round(amb, 1), round(sunk, 2),
               round(S["clouds"], 2), round(S["rain"], 2), self.map.name)
        if key != self._tkey:
            tc.set_pose(yaw, pitch)
            dx, dy, dz, _a, _b = tc.rays(tc.W, tc.H)
            h = np.hypot(dx, dy)
            pit = np.degrees(np.arctan2(dz, h))
            yw = np.arctan2(dx, dy)
            sky = amb - 20.0 + 14.0 * S["clouds"] + 6.0 * S["rain"]
            sky_t = (sky + np.clip(1.0 - pit / 25.0, 0, 1) * 8.0).astype(np.float32)        # warmer near the horizon
            gnd = pit < -0.05
            dist = np.where(gnd, tc.height / np.tan(np.radians(np.clip(-pit, 0.05, 89.9))), SKY_FAR)
            gx = tc.px + dist * np.sin(yw); gy = tc.py + dist * np.cos(yw)
            base = np.where(gnd, ground, sky_t).astype(np.float32)
            from simulator.scene import ground as G
            cls = G.classes(self.map, gx.astype(np.float32), gy.astype(np.float32), tc.px, tc.py)
            _c, _t, td, tn = G.palette(self.map)
            base = np.where(gnd, ground + 0.6 * td[cls] * day_k + 0.6 * tn[cls] * (1 - day_k), base).astype(np.float32)
            near = np.clip(1.0 - dist / 12.0, 0, 1) * gnd
            base += near * 0.3 * day_k                                         # the ground right below is sunlit
            hzn = (~gnd) & (pit < 2.5)
            base[hzn] = amb - 2.0                                               # tree line / mountains at the horizon
            self._tbase = base; self._tkey = key
        img = self._tbase.copy()
        plants = [p for p in plants if not cull(p, tc, p.crown * 1.8 + 1, 250.0)]
        tc.set_pose(yaw, pitch)
        props = visible_props([pr for pr in props if math.hypot(pr.x - tc.px, pr.y - tc.py) - max(pr.w, pr.d) / 2 < (9000.0 if pr.name == "mountain" else 2500.0)], tc, cell=24)
        entities = [e for e in entities if not cull(e, tc, max(e.length, 1.0) + 1, 400.0)]
        D = lambda o: math.hypot(o.x - tc.px, o.y - tc.py)
        things = [(D(p), "plant", p) for p in plants] + [(D(pr), "prop", pr) for pr in props] + \
                 [(D(e), "ent", e) for e in entities]
        if S["hot_stone"]:
            things.append((math.hypot(-2.5 - tc.px, 7.0 - tc.py), "stone", None))
        if S["campfire"]:
            things.append((math.hypot(3.0 - tc.px, 6.0 - tc.py), "fire", None))
        things.sort(key=lambda t: -t[0])
        T = self._t
        for d, typ, obj in things:
            if typ == "plant":
                self._t_plant(img, obj)
            elif typ == "prop" and obj.name == "mountain":
                self._mountain(img, obj, env, temp=T["amb"] - 2.0 + 2.0 * T["sunk"])
            elif typ == "prop":
                self._t_prop(img, obj)
            elif typ == "stone":
                c = tc.project(-2.5, 7.0, 0.15)
                if c:
                    cv2.ellipse(img, _ipt(c), (_th(0.4 * tc.f / c[2]), _th(0.2 * tc.f / c[2])), 0, 0, 360, float(amb + 18.0), -1)
            elif typ == "fire":
                c = tc.project(3.0, 6.0, 0.25)
                if c:
                    s_ = tc.f / c[2]
                    fl = 1.0 + 0.25 * math.sin(env["t"] * 9.0) + 0.15 * random.random()
                    cv2.ellipse(img, _ipt(c), (_th(0.6 * s_), _th(0.25 * s_)), 0, 0, 360, float(amb + 25.0), -1)
                    cv2.ellipse(img, _ipt((c[0], c[1] - 0.2 * s_ * fl)), (_th(0.3 * s_), _th(0.45 * s_ * fl)), 0, 0, 360, 250.0, -1)
            else:
                self._t_entity(img, obj, T, env)
        small = cv2.resize(img, (TW, TH), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), 0.55)                          # soft germanium lens
        if getattr(self, "_fpn", None) is None:                                 # fixed pattern: column stripes + vignette
            rng = np.random.default_rng(7)
            yy, xx = np.mgrid[0:TH, 0:TW].astype(np.float32)
            vig = -0.6 * (((xx - TW / 2) / (TW / 2)) ** 2 + ((yy - TH / 2) / (TH / 2)) ** 2)
            self._fpn = (vig + rng.normal(0, 0.06, (1, TW)).astype(np.float32)).astype(np.float32)
        small += self._fpn
        small += np.random.default_rng().normal(0, S["thermal_noise"], small.shape).astype(np.float32)
        return small

    def _t_plant(self, img, p):
        tc, T = self.tcam, self._t
        base = tc.project(p.x, p.y, 0.0)
        c = tc.project(p.x, p.y, p.height * (0.68 if p.kind == "tree" else 0.45))
        if base is None or c is None:
            return
        s = tc.f / c[2]
        leaves = T["amb"] - 1.0 + 1.2 * T["sunk"] - 0.8 * (1 - T["day_k"])     # leaves breathe: slightly cooler than the air
        if p.kind == "tree":
            cv2.line(img, _ipt(base), _ipt(c), float(T["amb"] + 0.5 * T["sunk"]), _th(0.35 * s))
        for bx, by, br in p.blobs:
            cv2.circle(img, _ipt((c[0] + bx * p.crown * s, c[1] - by * p.crown * s)), _th(br * p.crown * s), float(leaves + 0.4 * by), -1)

    def _t_prop(self, img, pr):
        tc, T = self.tcam, self._t
        warm = {"caravan": 4.0, "house": 4.0, "car": 5.0, "shed": 3.0, "hut": 3.0, "tent": 2.5, "boat": 4.0, "tower": 5.0,
                "block": 4.0}.get(pr.name, 2.0)
        heated = {"house": 1.5, "caravan": 1.0, "tower": 3.0, "block": 2.0}.get(pr.name, 0.0) * (1 - T["day_k"])     # inhabited: warm at night
        t = T["amb"] + warm * T["sunk"] + heated + pr.temp_add
        if pr.name in ("post", "umbrella"):
            a, b = tc.project(pr.x, pr.y, 0.0), tc.project(pr.x, pr.y, pr.h)
            if a and b:
                cv2.line(img, _ipt(a), _ipt(b), float(t), _th(0.12 * tc.f / a[2]))
                if pr.name == "post" and T["day_k"] < 0.5:
                    cv2.circle(img, _ipt(b), _th(0.2 * tc.f / b[2]), float(T["amb"] + 25.0), -1)     # lamp on at night
            return
        hw, hd = pr.w / 2.0, pr.d / 2.0
        pts = []
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            for z in (0.0, pr.h):
                p = tc.project(pr.x + sx * hw, pr.y + sy * hd, z)
                if p is None:
                    return
                pts.append(_ipt(p))
        cv2.fillConvexPoly(img, cv2.convexHull(np.array(pts, np.int32)), float(t))

    def _t_entity(self, img, e, T, env):
        tc = self.tcam
        amb, wet = T["amb"], T["wet"]
        if e.kind == "plane":
            self._plane(img, e, cam=tc, temp=amb - 10.0)
            return
        if e.kind in VEHICLES:
            fx, fy = math.sin(e.heading), math.cos(e.heading)
            rx, ry = fy, -fx
            pts = []
            for l in (-e.length / 2, e.length / 2):
                for w in (-e.width / 2, e.width / 2):
                    for z in (0.2, e.height):
                        p = tc.project(e.x + fx * l + rx * w, e.y + fy * l + ry * w, z, near=0.5)
                        if p is None:
                            return
                        pts.append(_ipt(p))
            cv2.fillConvexPoly(img, cv2.convexHull(np.array(pts, np.int32)), float(amb + 3.0 + 3.0 * T["sunk"]))
            eng = tc.project(e.x + fx * e.length * 0.38, e.y + fy * e.length * 0.38, e.height * 0.3)
            exh = tc.project(e.x - fx * e.length * 0.5, e.y - fy * e.length * 0.5, 0.35)
            for off in (-0.32, 0.32):                                           # warm tyres / brakes
                wpt = tc.project(e.x + fx * e.length * off, e.y + fy * e.length * off, 0.35)
                if wpt:
                    cv2.circle(img, _ipt(wpt), _th(0.33 * tc.f / wpt[2]), float(amb + 15.0), -1)
            if eng:
                s_ = tc.f / eng[2]
                cv2.ellipse(img, _ipt(eng), (_th(0.5 * s_ * min(1.6, e.length / 4.4)), _th(0.32 * s_)), 0, 0, 360,
                            float(48.0 if e.kind != "motorcycle" else 65.0), -1)
            if exh:
                cv2.circle(img, _ipt(exh), _th(0.12 * tc.f / exh[2]), 90.0, -1)
            if e.kind == "motorcycle":
                self._person(img, e, seat=0.85, cam=tc, pal=self._t_pal(e, amb, wet))
            return
        if e.kind in ("person", "bicycle"):
            self._person(img, e, seat=0.95 if e.kind == "bicycle" else None, cam=tc, pal=self._t_pal(e, amb, wet))
            return
        fur = {"dog": 30.5, "cat": 29.5, "bear": 27.0, "horse": 30.0, "sheep": 25.0, "bird": 33.0}.get(e.kind, 29.0)
        t = fur + 0.15 * (amb - 15.0) - wet
        self._animal(img, e, cam=tc, pal=(t, t, t))
        fx, fy = math.sin(e.heading), math.cos(e.heading)
        if e.kind != "bird":                                                    # eyes / nose / ears are the hottest
            hd = tc.project(e.x + fx * e.length * 0.6, e.y + fy * e.length * 0.6, e.height * (0.85 if e.kind != "horse" else 1.25))
            if hd:
                cv2.circle(img, _ipt(hd), _th(0.07 * tc.f / hd[2]), float(35.0 - wet), -1)

    @staticmethod
    def _t_pal(e, amb, wet):
        """Surface temperatures of a person: face / hands ~34 C, clothes a few degrees cooler depending on the air."""
        clothes = 30.0 + 0.12 * (amb - 15.0) - wet + (e.id % 3) * 0.5
        return {"skin": (34.0 - wet * 0.5,) * 3, "shirt": (clothes + 1.5,) * 3, "pants": (clothes,) * 3,
                "shoe": (amb + 6.0,) * 3, "hair": (31.0 - wet,) * 3}


def environment(t):
    """Everything about light and weather that one frame needs."""
    return {"t": t, "sun": sun(), "amb": ambient_light(), "wind": float(SIM["wind"]), "lights": {}}


def thermal_colour(fr, size=None):
    """Thermal frame -> colour picture for the simulator panel: fixed span from a bit below the ground to body heat,
    so warm bodies glow white / yellow and the scene stays dark (like a camera in manual range)."""
    med = float(np.median(fr))
    lo, hi = med - 6.0, max(med + 12.0, 32.0)
    g = np.clip((fr - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)
    col = cv2.applyColorMap(g, cv2.COLORMAP_INFERNO)
    if size:
        col = cv2.resize(col, size, interpolation=cv2.INTER_CUBIC)
    return col
