"""The ground of a map as raster images instead of shapes tested pixel by pixel.

Every ground layer of a map (road, field, lake …) gets a class number. The layers are painted once into
  * a coarse raster of the whole map (2 m per pixel, for the far ground and zoomed-out views) and
  * sharp rasters around a point (0.25 m per pixel, ±450 m) built for the camera place / the map view.
A ground point then costs one look-up, however many layers the map has - that is what makes 7 km maps possible."""
import math
import threading

import cv2
import numpy as np

from simulator.scene import maps

WHITE, JOINT = 250, 251                       # extra classes: painted lines (road / parking), tile joints
OUTSIDE = 255
FINE_RES, FINE_HALF = 0.25, 450.0
ULTRA_RES, ULTRA_HALF = 0.02, 30.0             # right in front of the camera: 2 cm pixels
COARSE_RES = 2.0
_LOCK = threading.Lock()


class Raster:
    def __init__(self, m, x0, y1, w_m, h_m, res, decos=True):
        self.x0, self.y1, self.res = x0, y1, res              # top-left corner = (x0, y1); rows go south
        self.W, self.H = int(math.ceil(w_m / res)), int(math.ceil(h_m / res))
        self.cls = np.zeros((self.H, self.W), np.uint8)
        for i, (shape, params, *_r) in enumerate(m.layers):
            self._paint(shape, params, i + 1, decos)

    def _px(self, x, y):
        return (x - self.x0) / self.res, (self.y1 - y) / self.res

    def _ipx(self, x, y):
        u, v = self._px(x, y)
        return int(round(max(-1e6, min(1e6, u)))), int(round(max(-1e6, min(1e6, v))))

    def _paint(self, shape, p, c, decos):
        img, r = self.cls, self.res
        big = 1e6
        if shape == "hband":
            cv2.rectangle(img, self._ipx(self.x0 - 10, p[1]), self._ipx(self.x0 + self.W * r + 10, p[0]), c, -1)
        elif shape == "vband":
            cv2.rectangle(img, self._ipx(p[0], p[3]), self._ipx(p[1], p[2]), c, -1)
        elif shape == "rect":
            cv2.rectangle(img, self._ipx(p[0], p[3]), self._ipx(p[2], p[1]), c, -1)
        elif shape == "beyond":
            cv2.rectangle(img, self._ipx(self.x0 - 10, self.y1 + 10), self._ipx(self.x0 + self.W * r + 10, p[0]), c, -1)
        elif shape == "ellipse":
            cx, cy = self._px(p[0], p[1])
            if -big < cx < big and -big < cy < big:
                cv2.ellipse(img, (int(cx), int(cy)), (max(1, int(p[2] / r)), max(1, int(p[3] / r))), 0, 0, 360, c, -1)
        elif shape == "line":
            cv2.line(img, self._ipx(p[0], p[1]), self._ipx(p[2], p[3]), c, max(1, int(round(2 * p[4] / r))))
        elif shape == "poly":                                   # (list of (x, y) points, {})
            pts = np.array([self._ipx(x, y) for x, y in p[0]], np.int32)
            cv2.fillPoly(img, [pts], c)
        if not decos:
            return
        deco = maps.layer_deco(p)
        if deco == "road":
            self._road_lines(shape, p)
        elif deco == "parking" and shape == "rect":
            x0, y0, x1, y1 = p[:4]
            x = x0 + 1.0
            while x < x1 - 1.0:
                for ya, yb in ((y0 + 0.5, (y0 + y1) / 2 - 3.0), ((y0 + y1) / 2 + 3.0, y1 - 0.5)):
                    if yb > ya:
                        cv2.line(img, self._ipx(x, ya), self._ipx(x, yb), WHITE, 1)
                x += 2.7
        elif deco == "tiles" and shape == "rect":
            x0, y0, x1, y1 = p[:4]
            for x in np.arange(x0, x1, 0.6):
                cv2.line(img, self._ipx(x, y0), self._ipx(x, y1), JOINT, 1)
            for y in np.arange(y0, y1, 0.6):
                cv2.line(img, self._ipx(x0, y), self._ipx(x1, y), JOINT, 1)

    def _road_lines(self, shape, p):
        """Edge lines and a dashed middle line (only drawn where they are wider than nothing)."""
        if self.res > 1.0:
            return
        r = self.res
        if shape == "hband":
            y0, y1 = p[0], p[1]; mid = (y0 + y1) / 2
            xa, xb = self.x0, self.x0 + self.W * r
            for ye in (y0 + 0.25, y1 - 0.25):
                cv2.line(self.cls, self._ipx(xa, ye), self._ipx(xb, ye), WHITE, 1)
            x = math.floor(xa / 6.0) * 6.0
            while x < xb:
                cv2.line(self.cls, self._ipx(x, mid), self._ipx(x + 3.0, mid), WHITE, 1)
                x += 6.0
        elif shape == "vband":
            x0, x1, ya, yb = p[0], p[1], max(p[2], self.y1 - self.H * r), min(p[3], self.y1)
            if yb <= ya:
                return
            mid = (x0 + x1) / 2
            for xe in (x0 + 0.25, x1 - 0.25):
                cv2.line(self.cls, self._ipx(xe, ya), self._ipx(xe, yb), WHITE, 1)
            y = math.floor(ya / 6.0) * 6.0
            while y < yb:
                cv2.line(self.cls, self._ipx(mid, y), self._ipx(mid, y + 3.0), WHITE, 1)
                y += 6.0

    def lookup(self, gx, gy):
        u = ((gx - self.x0) / self.res).astype(np.float32)
        v = ((self.y1 - gy) / self.res).astype(np.float32)
        return cv2.remap(self.cls, u, v, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=OUTSIDE)


def coarse(m):
    """Raster of the whole map (built once per map)."""
    with _LOCK:
        r = getattr(m, "_coarse", None)
        if r is None:
            x0, x1, y0, y1 = m.extent
            r = Raster(m, x0, y1, x1 - x0, y1 - y0, COARSE_RES, decos=False)
            m._coarse = r
        return r


def fine(m, cx, cy):
    """Sharp raster around (cx, cy); the last few are kept."""
    key = (int(cx // 150), int(cy // 150))
    with _LOCK:
        cache = m.__dict__.setdefault("_fine", {})
        r = cache.get(key)
        if r is None:
            ox, oy = key[0] * 150.0 + 75.0, key[1] * 150.0 + 75.0
            r = Raster(m, ox - FINE_HALF, oy + FINE_HALF, 2 * FINE_HALF, 2 * FINE_HALF, FINE_RES)
            if len(cache) > 3:
                cache.pop(next(iter(cache)))
            cache[key] = r
        return r


def ultra(m, cx, cy):
    key = ("u", round(cx, 1), round(cy, 1))
    with _LOCK:
        cache = m.__dict__.setdefault("_ultra", {})
        r = cache.get(key)
        if r is None:
            r = Raster(m, cx - ULTRA_HALF, cy + ULTRA_HALF, 2 * ULTRA_HALF, 2 * ULTRA_HALF, ULTRA_RES)
            if len(cache) > 2:
                cache.pop(next(iter(cache)))
            cache[key] = r
        return r


def classes(m, gx, gy, cx=None, cy=None, sharp=True, very_sharp=True):
    """Class of the ground at world points gx, gy: 2 cm raster right at (cx, cy), 25 cm raster around it, 2 m
    raster for the whole map, 0 = open ground."""
    c = coarse(m).lookup(gx, gy)
    if sharp and cx is not None:
        f = fine(m, cx, cy).lookup(gx, gy)
        c = np.where(f != OUTSIDE, f, c)
        if very_sharp:
            u = ultra(m, cx, cy).lookup(gx, gy)
            c = np.where(u != OUTSIDE, u, c)
    c[c == OUTSIDE] = 0
    return c


def palette(m):
    """Per class: colour (BGR), texture strength, thermal offset by day, thermal offset at night."""
    p = getattr(m, "_palette", None)
    if p is None:
        col = np.zeros((256, 3), np.float32); tex = np.ones(256, np.float32); td = np.zeros(256, np.float32); tn = np.zeros(256, np.float32)
        col[0] = m.ground
        for i, (_s, _p, lcol, t, a, b) in enumerate(m.layers):
            col[i + 1] = lcol; tex[i + 1] = t; td[i + 1] = a; tn[i + 1] = b
        col[WHITE] = (215, 215, 215); tex[WHITE] = 0.1
        col[JOINT] = (95, 100, 108); tex[JOINT] = 0.2
        p = (col, tex, td, tn)
        m._palette = p
    return p


def colour(m, cls, fine_t, coarse_t):
    """Ground colours from classes + the two noise textures (same look as before)."""
    col, tex, _td, _tn = palette(m)
    base = col[cls]
    t = tex[cls][..., None]
    open_ = (cls == 0)[..., None]
    grass = base * (0.72 + 0.45 * coarse_t[..., None]) * (0.85 + 0.3 * fine_t[..., None])
    painted = base * ((1 - t) + t * (0.6 + 0.8 * fine_t[..., None]))
    return np.where(open_, grass, painted)
