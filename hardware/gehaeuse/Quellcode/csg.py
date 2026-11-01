"""Tiny CSG library on signed distance fields (numpy only).
Leaves: Cube, Cyl (incl. cone / hexagon), RBox (rounded-corner box), Prism (convex polygon).
Nodes: U (union), D (difference), I (intersection), T (translate), R (rotate, OpenSCAD order).
"""
import math
import numpy as np

MARGIN = 1.5  # mm: outside node bbox + margin we return the bbox distance (a lower bound)


def _sd_box(P, lo, hi):
    c = (lo + hi) * 0.5
    h = (hi - lo) * 0.5
    q = np.abs(P - c) - h
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)


def _ext(d2, dz):
    return np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2) + np.minimum(np.maximum(d2, dz), 0)


def rotm(a):
    ax, ay, az = [math.radians(v) for v in a]
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    M = Rz @ Ry @ Rx
    M[np.abs(M) < 1e-12] = 0
    return M


class N:
    def __add__(s, o): return U(s, o)
    def __sub__(s, o): return D(s, o)
    def __mul__(s, o): return I(s, o)

    def sdf(self, P):
        lo, hi = self.bbox()
        m = np.all((P >= lo - MARGIN) & (P <= hi + MARGIN), axis=1)
        out = np.empty(len(P), np.float64)
        if (~m).any():
            out[~m] = _sd_box(P[~m], lo, hi)
        if m.any():
            out[m] = self._sdf(P[m])
        return out


class Cube(N):
    def __init__(s, lo, hi):
        s.lo = np.array(lo, float); s.hi = np.array(hi, float)
    def bbox(s): return s.lo, s.hi
    def _sdf(s, P): return _sd_box(P, s.lo, s.hi)


def box(x0, x1, y0, y1, z0, z1):
    return Cube([min(x0, x1), min(y0, y1), min(z0, z1)], [max(x0, x1), max(y0, y1), max(z0, z1)])


class Cyl(N):
    """Like OpenSCAD cylinder(h, r1, r2): along z from 0..h. fn=6 -> hexagon (vertex on +x)."""
    def __init__(s, h, r=None, r1=None, r2=None, d=None, fn=64):
        if d is not None: r = d / 2
        s.r1 = r if r1 is None else r1
        s.r2 = r if r2 is None else r2
        s.h = h; s.fn = fn
        R = max(s.r1, s.r2)
        s.lo = np.array([-R, -R, 0.]); s.hi = np.array([R, R, h])
    def bbox(s): return s.lo, s.hi
    def _sdf(s, P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        hh = s.h / 2
        zc = z - hh
        if s.fn == 6:
            a = s.r1 * math.cos(math.pi / 6)
            ax_, ay_ = np.abs(x), np.abs(y)
            d2 = np.maximum(ay_ - a, ax_ * math.cos(math.pi / 6) + ay_ * 0.5 - a)
            return _ext(d2, np.abs(zc) - hh)
        q = np.sqrt(x * x + y * y)
        if abs(s.r1 - s.r2) < 1e-9:
            return _ext(q - s.r1, np.abs(zc) - hh)
        # iq capped cone, z centred
        r1, r2 = s.r1, s.r2
        qy = zc
        k1x, k1y = r2, hh
        k2x, k2y = r2 - r1, 2 * hh
        cax = q - np.minimum(q, np.where(qy < 0, r1, r2))
        cay = np.abs(qy) - hh
        t = np.clip(((k1x - q) * k2x + (k1y - qy) * k2y) / (k2x * k2x + k2y * k2y), 0, 1)
        cbx = q - k1x + k2x * t
        cby = qy - k1y + k2y * t
        sgn = np.where((cbx < 0) & (cay < 0), -1.0, 1.0)
        return sgn * np.sqrt(np.minimum(cax * cax + cay * cay, cbx * cbx + cby * cby))


class RBox(N):
    """Box w x d (centred in XY), z 0..h, vertical edges rounded with r."""
    def __init__(s, w, d, h, r):
        s.w, s.d, s.h, s.r = w, d, h, r
        s.lo = np.array([-w / 2, -d / 2, 0.]); s.hi = np.array([w / 2, d / 2, h])
    def bbox(s): return s.lo, s.hi
    def _sdf(s, P):
        qx = np.abs(P[:, 0]) - (s.w / 2 - s.r)
        qy = np.abs(P[:, 1]) - (s.d / 2 - s.r)
        d2 = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - s.r
        return _ext(d2, np.abs(P[:, 2] - s.h / 2) - s.h / 2)


class Prism(N):
    """Convex CCW polygon in XY, extruded z 0..h."""
    def __init__(s, pts, h):
        s.p = np.array(pts, float); s.h = h
        s.lo = np.array([*s.p.min(0), 0.]); s.hi = np.array([*s.p.max(0), h])
    def bbox(s): return s.lo, s.hi
    def _sdf(s, P):
        d2 = None
        n = len(s.p)
        for i in range(n):
            a, b = s.p[i], s.p[(i + 1) % n]
            e = b - a
            nx, ny = e[1], -e[0]
            L = math.hypot(nx, ny)
            di = ((P[:, 0] - a[0]) * nx + (P[:, 1] - a[1]) * ny) / L
            d2 = di if d2 is None else np.maximum(d2, di)
        return _ext(d2, np.abs(P[:, 2] - s.h / 2) - s.h / 2)


class U(N):
    def __init__(s, *c):
        s.c = [x for x in c if x is not None]
        los = np.array([x.bbox()[0] for x in s.c]); his = np.array([x.bbox()[1] for x in s.c])
        s._bb = (los.min(0), his.max(0))
    def bbox(s): return s._bb
    def _sdf(s, P):
        return np.minimum.reduce([x.sdf(P) for x in s.c]) if len(s.c) > 1 else s.c[0].sdf(P)


class D(N):
    def __init__(s, a, *b):
        s.a = a; s.b = [x for x in b if x is not None]
    def bbox(s): return s.a.bbox()
    def _sdf(s, P):
        v = s.a.sdf(P)
        for x in s.b:
            v = np.maximum(v, -x.sdf(P))
        return v


class I(N):
    def __init__(s, *c):
        s.c = c
        s._bb = (np.max([x.bbox()[0] for x in c], 0), np.min([x.bbox()[1] for x in c], 0))
    def bbox(s): return s._bb
    def _sdf(s, P):
        return np.maximum.reduce([x.sdf(P) for x in s.c])


class T(N):
    def __init__(s, v, c):
        s.v = np.array(v, float); s.c = c
    def bbox(s):
        lo, hi = s.c.bbox(); return lo + s.v, hi + s.v
    def sdf(s, P): return s.c.sdf(P - s.v)


class R(N):
    def __init__(s, a, c):
        s.M = rotm(a); s.c = c
    def bbox(s):
        lo, hi = s.c.bbox()
        cs = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        w = cs @ s.M.T
        return w.min(0), w.max(0)
    def sdf(s, P): return s.c.sdf(P @ s.M)


# ---- helpers -----------------------------------------------------------
def cyl_z(x, y, z0, z1, d, fn=64):
    return T([x, y, z0], Cyl(z1 - z0, d=d, fn=fn))


def cyl_y(x, z, y0, y1, d, fn=64):
    return T([x, y0, z], R([-90, 0, 0], Cyl(y1 - y0, d=d, fn=fn)))


def cyl_x(y, z, x0, x1, d, fn=64):
    return T([x0, y, z], R([0, 90, 0], Cyl(x1 - x0, d=d, fn=fn)))


class Torus(N):
    """Torus in der xy-Ebene um z=0: Ringradius R, Querschnittsradius r."""
    def __init__(s, R, r):
        s.R, s.r = R, r
        s.lo = np.array([-R - r, -R - r, -r]); s.hi = np.array([R + r, R + r, r])
    def bbox(s): return s.lo, s.hi
    def _sdf(s, P):
        q = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - s.R
        return np.sqrt(q * q + P[:, 2] ** 2) - s.r


def rx_box(x0, x1, W, H, r, y=0.0, z=0.0):
    """Quader x0..x1, Breite W (y), Höhe H (z), Kanten entlang x gerundet."""
    return T([x0, y, z], R([0, 90, 0], RBox(H, W, x1 - x0, r)))


class RM(R):
    """Beliebige Rotationsmatrix (Spalten = Bild der lokalen Achsen)."""
    def __init__(s, M, c):
        s.M = np.array(M, float); s.c = c


def rib_yz(x0, w, y0, direction, z0, d, h):
    """Dreiecksrippe in der y-z-Ebene, Dicke w ab x0 (+x), Grundlinie d in Richtung ±y, Höhe h."""
    pts = [(0, 0), (d, 0), (0, h)] if direction > 0 else [(0, 0), (0, h), (-d, 0)]
    return T([x0, y0, z0], RM([[0, 0, 1], [1, 0, 0], [0, 1, 0]], Prism(pts, w)))
