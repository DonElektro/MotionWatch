#!/usr/bin/env python3
"""MoveEye: das Kartenpaket «Bergtal» (Teil 639zzzzzt) aus den Daten des Simulators.

Stufe 1 (Godot, ohne Bild): werkzeuge/bergkarte/export.gd schreibt hoehen.f32, land.u8 und bergtal.json (Höhenkarte,
Bodenart, Orte, Wege, Bäche, Seen, Strasse, geheime Orte) - genau die Zahlen von bergtal.gd.
Stufe 2 (hier, nur Python ohne Zusatzpakete): eine ZIP «bergtal-karte-N.zip» für MapLibre GL JS in MoveEye:

  bergkarte.json     Kopf: Tag, Format, Sim-Version, Gitter, Grenzen, Zoom der Höhen-Kacheln, Zahlen, Stichproben
  hoehen.f32         die Höhenkarte (wie export) - MoveEye rechnet daraus Auf- / Abstieg und Profil der Touren
  dem/Z/X/Y.png      Höhen als terrarium-PNG (256 px) für Relief (hillshade) und 3D-Gelände
  land.png           Wald / Fels / Geröll / Gletscher / Moor in den Farben der Schweizer Landeskarte (hell), land_dunkel.png
  vektor.json        GeoJSON (öffentlich): Höhenlinien (10 m, «lvl» 100 / 50 / 20 / 10, «gl» auf Gletschern), Wanderwege
                     (g 1 gelb / 2 rot / 3 blau), Bäche, Seen, Strasse, alle Orte mit Art und Höhe
  geheim.json        die geheimen Orte / Wege / Seen mit den Kennungen des Entdeckungsbuchs - MoveEye gibt davon nur heraus,
                     was der verbundene Simulator als gefunden meldet (nie die Datei selbst)
  touren.json        vorgeschlagene Touren (auf den Wanderwegen gesucht), z. B. Hospiz → Pass → Biwak
  stil.json / stil_dunkel.json   der Kartenstil (Farben und Linien wie die Topo-Karte, werkzeuge/karten/stil.py)
  web/…              MapLibre GL JS + Schriften aus karte-web-N.zip (Teil 639zzq, gleiche Prüfsumme) - das Paket braucht
                     die Schweizer Karte NICHT (Homepage / Host: 2 GB Platte)
  LIZENZEN.txt

Koordinaten: ein eigenes Gitter in Metern ab der Mitte des Tals (x = Osten, z = Süden). Für MapLibre (Web-Mercator) wird
es um 0° / 0° gelegt: lon = x / M, lat = -z / M mit M = 111195.08 m pro Grad (Erdradius 6371008.8 m - so rechnet MoveEye
mit seiner Formel genau Meter). Die Seite zeigt nie Grad, nur «O 120 m · N 340 m» - nie mit der Schweiz zu verwechseln.

  python3 -I werkzeuge/bergkarte/paket.py --export EXP --web-zip karte-web-2.zip --aus OUT     # baut OUT/bergtal-karte-N.zip
  python3 -I werkzeuge/bergkarte/paket.py --export EXP --ohne-web --aus OUT                  # ohne MapLibre (nur Tests, bergkarte_test.gd)
  python3 -I werkzeuge/bergkarte/paket.py --pruefen OUT --export EXP                          # Paket = Simulator (Test)
  python3 -I werkzeuge/bergkarte/paket.py --pins --aus OUT                                    # OUT/pins_bergkarte.txt
  python3 -I werkzeuge/bergkarte/paket.py --eintragen OUT/pins_bergkarte.txt                  # BK_FILE in quelle/639zzzzzt
Gleiche Eingabe = gleiche Bytes (sortierte Namen, feste Zeitstempel).

Release (nur der Integrator; zwei Stufen wie die Offline-Karten 3.81.0, CLAUDE.md «Release in zwei Stufen»):
  Stufe 1  Quelle (Teil 639zzzzzt mit BK_FILE size 0 = «kommt mit einem Update») + gebaute Datei + Workflow auf main, OHNE
           Eintrag in versions.json, dazu vorstufe.json. Workflow «Bergtal-Karte» von main mit release=echt, tag=bergkarte-1:
           baut aus dem Simulator dieses Stands, prüft (paket.py --pruefen, bergkarte_test.gd), legt Release + Asset an.
  Stufe 2  pins_bergkarte.txt (Release-Notiz / Artefakt) -> `paket.py --eintragen pins_bergkarte.txt`, MoveEye bauen,
           signieren (die Prüfsumme steht damit in der signierten Hauptdatei), vorstufe.json löschen.
  Ein neues Bergtal im Simulator (Sim-Release): der Workflow läuft danach von selbst (nur bauen + prüfen). Ändert sich die
  Prüfsumme, TAG und BK_TAG auf bergkarte-N+1 erhöhen und wieder beide Stufen (ein Release wird nie überschrieben).
  Die Live-Teile (Lage, Figur, gefundene Geheimnisse, «Tour im Sim nachlaufen») brauchen den Simulator mit bergkarte.gd
  (world_reply / control «bkarte») - ein Sim-Release; ein älterer Simulator: die Karte geht, Geheimnisse bleiben verborgen.
"""
import argparse
import array
import hashlib
import heapq
import io
import json
import math
import os
import re
import struct
import sys
import zipfile
import zlib

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HIER))
TAG = "bergkarte-1"
NAME = "bergtal-karte-%s.zip" % TAG.split("-")[1]
FORMAT = 1
QUELLE_TEIL = os.path.join(REPO, "quelle", "639zzzzzt_bergtal_karte.py")
M = 6371008.8 * math.pi / 180.0                  # metres per degree (lat and lon at 0° / 0°)
DEM_Z = (11, 15)                                 # zoom levels of the height tiles (z15 ≈ 4.7 m per pixel, the grid is 4 m)
LAND_PX = 1024                                   # land.png: 2 m per pixel over the 2048 m of the grid
FIX_TIME = (1980, 1, 1, 0, 0, 0)
WEB_FILES = ("maplibre-gl.js", "maplibre-gl.js.gz", "maplibre-gl.css", "maplibre-gl.css.gz")
FONTS = ("Noto Sans Regular", "Noto Sans Medium", "Noto Sans Italic")
RANGES = ("0-255", "256-511", "8192-8447")
SUGGEST = [   # suggested tours: names of places (bergtal.json «places»), walked on the trails
    ("Hospiz → Pass → Biwak", ["Furggapass mit Hospiz", "Passchanzle Furgga", "Biwak Chüebodehorn"]),
    ("Rund um den Gumpisee", ["Alp Tschuggen", "Seeblick Gumpisee", "Chanzle über dem Gumpisee", "Alp Tschuggen"]),
    ("Zum Gletscherseeli", ["Alp Tschuggen", "Obri Stafelhütte (Seilbahn)", "Gletscherseeli"]),
    ("Kapelle St. Jodern", ["Alp Tschuggen", "Hängebrücke Tüfelsschlund", "Kapelle St. Jodern"]),
    ("Riedmoos und Ruine Altstafel", ["Alp Tschuggen", "Riedmoos (Wollgras)", "Ruine Altstafel"]),
]


def log(*a):
    print(*a, flush=True)


# ---- the grid --------------------------------------------------------------------------------------------------------------------
class Gitter:
    def __init__(self, exp):
        self.d = json.load(open(os.path.join(exp, "bergtal.json"), encoding="utf-8"))
        g = self.d["grid"]
        self.lo, self.step, self.n, self.alt0 = float(g["lo"]), float(g["step"]), int(g["n"]), float(g["alt0"])
        self.h = array.array("f")
        with open(os.path.join(exp, "hoehen.f32"), "rb") as f:
            self.h.frombytes(f.read())
        if sys.byteorder != "little":
            self.h.byteswap()
        self.land = open(os.path.join(exp, "land.u8"), "rb").read()
        if len(self.h) != self.n * self.n or len(self.land) != self.n * self.n:
            raise SystemExit("export: Grösse passt nicht (%d Höhen, %d Bodenarten, n=%d)" % (len(self.h), len(self.land), self.n))
        self.hi = -self.lo

    def H(self, x, z):
        """exactly bergtal.gd H(): bilinear in the grid, outside the edge rises (0.35 × step per cell)"""
        n, st = self.n, self.step
        fx = (x - self.lo) / st
        fz = (z - self.lo) / st
        out = 0.0
        if fx < 0.0 or fz < 0.0 or fx > n - 1 or fz > n - 1:
            out = max(max(-fx, fx - (n - 1)), max(-fz, fz - (n - 1))) * st * 0.35
            fx = min(max(fx, 0.0), n - 1.001)
            fz = min(max(fz, 0.0), n - 1.001)
        i = min(int(fx), n - 2)
        j = min(int(fz), n - 2)
        u = fx - i
        v = fz - j
        k = j * n + i
        h = self.h
        a = h[k] + (h[k + 1] - h[k]) * u
        b = h[k + n] + (h[k + n + 1] - h[k + n]) * u
        return a + (b - a) * v + out

    def cls(self, x, z):
        i = min(max(int(round((x - self.lo) / self.step)), 0), self.n - 1)
        j = min(max(int(round((z - self.lo) / self.step)), 0), self.n - 1)
        return self.land[j * self.n + i]


def ll(x, z):
    return [round(x / M, 7), round(-z / M, 7)]


def xz(lon, lat):
    return lon * M, -lat * M


# ---- PNG (zlib only) -------------------------------------------------------------------------------------------------------------
def png(w, h, rows, alpha=False):
    """rows: list of bytes (w × 3 or 4); filter «Up» for each row (smaller files for smooth pictures)"""
    bpp = 4 if alpha else 3
    raw = bytearray()
    prev = bytes(w * bpp)
    for r in rows:
        raw.append(2)
        raw += bytes((a - b) & 255 for a, b in zip(r, prev))
        prev = r
    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6 if alpha else 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def png_read(b):
    """the PNGs written above (RGB / RGBA, 8 bit, any filter) -> (w, h, bpp, rows) - for the check"""
    assert b[:8] == b"\x89PNG\r\n\x1a\n"
    p, idat, w = 8, b"", 0
    while p < len(b):
        n, t = struct.unpack(">I4s", b[p:p + 8])
        c = b[p + 8:p + 8 + n]
        if t == b"IHDR":
            w, h, _, ct = struct.unpack(">IIBB", c[:10])
        elif t == b"IDAT":
            idat += c
        p += 12 + n
    bpp = 4 if ct == 6 else 3
    raw = zlib.decompress(idat)
    rows, prev, s = [], bytearray(w * bpp), w * bpp
    for y in range(h):
        f = raw[y * (s + 1)]
        r = bytearray(raw[y * (s + 1) + 1:(y + 1) * (s + 1)])
        for i in range(s):
            a = r[i - bpp] if i >= bpp else 0
            up = prev[i]
            c_ = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                r[i] = (r[i] + a) & 255
            elif f == 2:
                r[i] = (r[i] + up) & 255
            elif f == 3:
                r[i] = (r[i] + (a + up) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(up - c_), abs(a - c_), abs(a + up - 2 * c_)
                r[i] = (r[i] + (a if pa <= pb and pa <= pc else up if pb <= pc else c_)) & 255
        rows.append(bytes(r))
        prev = r
    return w, h, bpp, rows


# ---- height tiles (terrarium) ----------------------------------------------------------------------------------------------------
def tile_range(z, g):
    def tx(lon):
        return int(math.floor((lon + 180.0) / 360.0 * (1 << z)))

    def ty(lat):
        r = math.radians(lat)
        return int(math.floor((1.0 - math.log(math.tan(r) + 1.0 / math.cos(r)) / math.pi) / 2.0 * (1 << z)))
    a = ll(g.lo, g.lo)                                   # north-west corner: x = lo, z = lo (north)
    b = ll(g.hi, g.hi)
    return tx(a[0]), tx(b[0]), ty(a[1]), ty(b[1])


def dem_tiles(g):
    out = {}
    for z in range(DEM_Z[0], DEM_Z[1] + 1):
        x0, x1, y0, y1 = tile_range(z, g)
        n = 1 << z
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                rows = []
                for py in range(256):
                    yy = (ty * 256 + py + 0.5) / (256.0 * n)
                    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yy))))
                    zz = -lat * M
                    r = bytearray()
                    for px in range(256):
                        lon = (tx * 256 + px + 0.5) / (256.0 * n) * 360.0 - 180.0
                        v = round((g.alt0 + g.H(lon * M, zz)) * 10.0) / 10.0 + 32768.0
                        r += bytes((int(v // 256) & 255, int(v % 256) & 255, int((v - math.floor(v)) * 256) & 255))
                    rows.append(bytes(r))
                out["dem/%d/%d/%d.png" % (z, tx, ty)] = png(256, 256, rows)
    return out


def dem_height(files, lon, lat, z=DEM_Z[1]):
    """the height in the package at lon / lat (nearest pixel of the zoom z) - for the check"""
    n = 1 << z
    fx = (lon + 180.0) / 360.0 * n
    r = math.radians(lat)
    fy = (1.0 - math.log(math.tan(r) + 1.0 / math.cos(r)) / math.pi) / 2.0 * n
    tx, ty = int(fx), int(fy)
    b = files.get("dem/%d/%d/%d.png" % (z, tx, ty))
    if b is None:
        return None
    w, h, bpp, rows = png_read(b)
    px, py = min(255, int((fx - tx) * 256)), min(255, int((fy - ty) * 256))
    R, G, B = rows[py][px * bpp:px * bpp + 3]
    clon = (tx * 256 + px + 0.5) / (256.0 * n) * 360.0 - 180.0          # the centre of that pixel (where it was computed)
    clat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty * 256 + py + 0.5) / (256.0 * n)))))
    return R * 256 + G + B / 256.0 - 32768.0, clon, clat


# ---- contour lines -----------------------------------------------------------------------------------------------------------------
def contours(g, iv=10.0):
    """marching squares on the grid (absolute heights): {(level, glacier): [polylines in valley metres]}"""
    n, st, lo, a0, h, land = g.n, g.step, g.lo, g.alt0, g.h, g.land
    segs = {}
    for j in range(n - 1):
        for i in range(n - 1):
            k = j * n + i
            v = (h[k] + a0, h[k + 1] + a0, h[k + n + 1] + a0, h[k + n] + a0)   # corners: tl, tr, br, bl
            mn, mx = min(v), max(v)
            L0 = math.floor(mn / iv) + 1
            L1 = math.floor(mx / iv)
            if L1 < L0:
                continue
            gl = 1 if land[k] == 4 else 0
            x0, z0 = lo + i * st, lo + j * st
            P = ((x0, z0), (x0 + st, z0), (x0 + st, z0 + st), (x0, z0 + st))
            for L in range(L0, L1 + 1):
                lv = L * iv
                c = (1 if v[0] >= lv else 0) | (2 if v[1] >= lv else 0) | (4 if v[2] >= lv else 0) | (8 if v[3] >= lv else 0)
                if c in (0, 15):
                    continue
                def e(a, b):
                    if P[a] > P[b]:                          # the same edge of two cells gives exactly the same point
                        a, b = b, a
                    t = (lv - v[a]) / ((v[b] - v[a]) or 1e-9)
                    return (round(P[a][0] + (P[b][0] - P[a][0]) * t, 2), round(P[a][1] + (P[b][1] - P[a][1]) * t, 2))
                E = {0: lambda: e(0, 1), 1: lambda: e(1, 2), 2: lambda: e(2, 3), 3: lambda: e(3, 0)}
                pairs = {1: [(3, 0)], 2: [(0, 1)], 3: [(3, 1)], 4: [(1, 2)], 5: [(3, 0), (1, 2)], 6: [(0, 2)], 7: [(3, 2)], 8: [(2, 3)],
                         9: [(0, 2)], 10: [(0, 1), (2, 3)], 11: [(1, 2)], 12: [(1, 3)], 13: [(0, 1)], 14: [(3, 0)]}[c]
                for ea, eb in pairs:
                    segs.setdefault((lv, gl), []).append((E[ea](), E[eb]()))
    out = {}
    for key, S in segs.items():
        out[key] = [simplify(p, 0.8) for p in join(S)]
    return out


def join(S):
    """segments -> polylines (endpoints match exactly: the same edge gives the same point)"""
    ends = {}
    for idx, (a, b) in enumerate(S):
        ends.setdefault(a, []).append(idx)
        ends.setdefault(b, []).append(idx)
    used = bytearray(len(S))
    lines = []
    for s0 in range(len(S)):
        if used[s0]:
            continue
        used[s0] = 1
        line = [S[s0][0], S[s0][1]]
        for direction in (1, 0):
            while True:
                tip = line[-1] if direction else line[0]
                nxt = None
                for idx in ends.get(tip, ()):
                    if not used[idx]:
                        nxt = idx
                        break
                if nxt is None:
                    break
                used[nxt] = 1
                a, b = S[nxt]
                o = b if a == tip else a
                if direction:
                    line.append(o)
                else:
                    line.insert(0, o)
        lines.append(line)
    return lines


def simplify(p, tol):
    """Douglas-Peucker (iterative)"""
    if len(p) < 3:
        return p
    keep = bytearray(len(p))
    keep[0] = keep[-1] = 1
    stack = [(0, len(p) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, az), (bx, bz) = p[a], p[b]
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz) or 1e-9
        best, bi = 0.0, -1
        for i in range(a + 1, b):
            d = abs((p[i][0] - ax) * dz - (p[i][1] - az) * dx) / L
            if d > best:
                best, bi = d, i
        if best > tol and bi > 0:
            keep[bi] = 1
            stack += [(a, bi), (bi, b)]
    return [q for q, k in zip(p, keep) if k]


# ---- land cover picture --------------------------------------------------------------------------------------------------------
LAND_HELL = {1: (200, 223, 170, 255), 2: (214, 208, 199, 235), 3: (226, 221, 212, 215), 4: (232, 243, 251, 255), 5: (169, 211, 240, 255),
             6: (222, 236, 214, 255), 7: (0, 0, 0, 0), 0: (0, 0, 0, 0)}
LAND_DUNKEL = {1: (34, 50, 42, 255), 2: (52, 51, 50, 235), 3: (44, 44, 44, 215), 4: (42, 59, 74, 255), 5: (28, 58, 84, 255),
               6: (34, 46, 40, 255), 7: (0, 0, 0, 0), 0: (0, 0, 0, 0)}
HATCH = {"hell": (184, 177, 166, 230), "dunkel": (88, 86, 82, 235)}
MOOR_DASH = {"hell": (63, 143, 210, 255), "dunkel": (61, 127, 184, 255)}


def land_png(g, dark=False):
    C = LAND_DUNKEL if dark else LAND_HELL
    hatch = HATCH["dunkel" if dark else "hell"]
    moor = MOOR_DASH["dunkel" if dark else "hell"]
    n = LAND_PX
    span = g.hi - g.lo
    rows = []
    for py in range(n):
        z = g.lo + (py + 0.5) / n * span
        r = bytearray()
        for px in range(n):
            x = g.lo + (px + 0.5) / n * span
            c = g.cls(x, z)
            col = C.get(c, C[0])
            if c == 2 and (px + py) % 8 == 0 and (px // 2) % 2 == 0:                # rock: fine diagonal hatching (like the rock drawing of the maps)
                col = hatch
            elif c == 3 and px % 5 == 0 and py % 5 == (px // 5) % 5:   # scree: dots
                col = hatch
            elif c == 6 and py % 6 == 0 and (px // 4) % 3 != 2:        # moor: blue dashes
                col = moor
            r += bytes(col)
        rows.append(bytes(r))
    return png(n, n, rows, alpha=True)


# ---- vector data -----------------------------------------------------------------------------------------------------------------
def feat(geom, **props):
    return {"type": "Feature", "properties": props, "geometry": geom}


def line(pts):
    return {"type": "LineString", "coordinates": [ll(p[0], p[1]) for p in pts]}


def ellipse(lk, n=56):
    cx, cz = lk["c"]
    a, b, r = lk["a"], lk["b"], lk["rot"]
    ring = []
    for k in range(n + 1):
        t = 2 * math.pi * k / n
        qx, qz = math.cos(t) * a, math.sin(t) * b
        # bergtal.gd _ell: q = (p - c).rotated(-rot)  ->  p = c + q.rotated(rot)
        ring.append(ll(cx + qx * math.cos(r) - qz * math.sin(r), cz + qx * math.sin(r) + qz * math.cos(r)))
    return {"type": "Polygon", "coordinates": [ring]}


def lvl_of(e):
    return 100 if e % 100 == 0 else 50 if e % 50 == 0 else 20 if e % 20 == 0 else 10


def vektor(g, cont):
    D = g.d
    F = []
    for (lv, gl), lines in sorted(cont.items()):
        e = int(round(lv))
        for p in lines:
            if len(p) >= 2:
                F.append(feat(line(p), t="hk", ele=e, lvl=lvl_of(e), gl=gl))
    for lk in D["lakes"]:
        if not lk["secret"]:
            F.append(feat(ellipse(lk), t="see", ele=int(round(g.alt0 + lk["level"]))))
    for s in D["streams"]:
        F.append(feat(line(s["pts"]), t="bach", w=s["w"]))
    F.append(feat(line(D["road"]), t="strasse"))
    for tr in D["trails"]:
        if not tr["secret"]:
            F.append(feat(line(tr["pts"]), t="weg", g=int(tr["level"]) + 1, name=tr["name"]))
    for p in D["places"]:
        F.append(feat({"type": "Point", "coordinates": ll(p["x"], p["z"])}, t="ort", name=p["name"], kind=p["kind"],
                      ele=int(round(g.alt0 + g.H(p["x"], p["z"])))))
    return {"type": "FeatureCollection", "features": F}


def geheim(g):
    D = g.d
    orte = [{"id": s["id"], "found": s["found"], "name": s["name"], "kind": s["kind"], "lonlat": ll(s["x"], s["z"]),
             "ele": int(round(g.alt0 + g.H(s["x"], s["z"])))} for s in D["secrets"]]
    wege = [{"name": t["name"], "found": t["secret"], "g": int(t["level"]) + 1, "coords": line(t["pts"])["coordinates"]} for t in D["trails"] if t["secret"]]
    seen = [{"found": lk["secret"], "ele": int(round(g.alt0 + lk["level"])), "ring": ellipse(lk)["coordinates"][0]} for lk in D["lakes"] if lk["secret"]]
    return {"orte": orte, "wege": wege, "seen": seen}


# ---- suggested tours: shortest way on the trails ------------------------------------------------------------------------------------
def graph(D):
    nodes, adj = [], {}

    def node(p):
        for i, q in enumerate(nodes):
            if math.hypot(q[0] - p[0], q[1] - p[1]) < 12.0:
                return i
        nodes.append((float(p[0]), float(p[1])))
        return len(nodes) - 1

    def edge(a, b, w=1.0):
        d = math.hypot(nodes[a][0] - nodes[b][0], nodes[a][1] - nodes[b][1]) * w
        adj.setdefault(a, []).append((b, d))
        adj.setdefault(b, []).append((a, d))

    for tr in D["trails"]:
        if tr["secret"]:
            continue
        ids = [node(p) for p in tr["pts"]]
        for a, b in zip(ids, ids[1:]):
            if a != b:
                edge(a, b)
    road = D["road"]
    ids = [node(p) for p in road[::3] + [road[-1]]]
    for a, b in zip(ids, ids[1:]):
        if a != b:
            edge(a, b, 1.4)                                  # the road only when it is much shorter
    return nodes, adj


def way(nodes, adj, a, b):
    dist, prev, q = {a: 0.0}, {}, [(0.0, a)]
    while q:
        d, u = heapq.heappop(q)
        if u == b:
            break
        if d > dist.get(u, 1e18):
            continue
        for v, w in adj.get(u, ()):
            nd = d + w
            if nd < dist.get(v, 1e18):
                dist[v], prev[v] = nd, u
                heapq.heappush(q, (nd, v))
    if b not in dist:
        return None
    out = [b]
    while out[-1] != a:
        out.append(prev[out[-1]])
    return [nodes[i] for i in reversed(out)]


def touren(D):
    nodes, adj = graph(D)
    P = {p["name"]: (p["x"], p["z"]) for p in D["places"]}
    out = []
    for name, stops in SUGGEST:
        if not all(s in P for s in stops):
            log("  Vorschlag «%s» ausgelassen: Ort fehlt (%s)" % (name, [s for s in stops if s not in P]))
            continue
        pts = []
        for s0, s1 in zip(stops, stops[1:]):
            a, b = P[s0], P[s1]
            na = min(range(len(nodes)), key=lambda i: math.hypot(nodes[i][0] - a[0], nodes[i][1] - a[1]))
            nb = min(range(len(nodes)), key=lambda i: math.hypot(nodes[i][0] - b[0], nodes[i][1] - b[1]))
            w = way(nodes, adj, na, nb) or []
            seg = [a] + w + [b]
            for q in seg:
                if not pts or math.hypot(pts[-1][0] - q[0], pts[-1][1] - q[1]) > 3.0:
                    pts.append((round(q[0], 1), round(q[1], 1)))
        out.append({"name": name, "stops": stops, "pts": [[ll(x, z)[1], ll(x, z)[0]] for x, z in pts]})   # [lat, lon] like the tours
    return out


# ---- style (colours of the topo map, werkzeuge/karten/stil.py) ------------------------------------------------------------------
def stil(dark, maxzoom, bounds):
    sys.path.insert(0, os.path.join(REPO, "werkzeuge", "karten"))
    import stil as ks                                    # the colours of the Swiss topo map of MoveEye
    P = ks.DUNKEL if dark else ks.HELL
    lw = lambda a, b, c: ["interpolate", ["linear"], ["zoom"], 12, a, 15, b, 18, c]
    vis = ["any", [">=", ["get", "lvl"], 100], ["all", [">=", ["zoom"], 12.5], [">=", ["get", "lvl"], 50]],
           ["all", [">=", ["zoom"], 13.5], [">=", ["get", "lvl"], 20]], [">=", ["zoom"], 14.5]]
    gl = ["==", ["get", "gl"], 1]
    t = lambda v: ["==", ["get", "t"], v]
    g_ = ["get", "g"]
    sym = {"text-font": ["Noto Sans Medium"], "text-size": ["interpolate", ["linear"], ["zoom"], 13, 10.5, 17, 13],
           "text-field": ["case", ["in", ["get", "kind"], ["literal", ["gipfel", "pass", "grat", "aussicht"]]],
                          ["concat", ["get", "name"], "\n", ["to-string", ["get", "ele"]]], ["get", "name"]],
           "text-anchor": "top", "text-offset": [0, 0.75], "text-max-width": 9, "icon-image": ["concat", "bk-", ["get", "kind"]],
           "icon-size": 1, "icon-allow-overlap": False, "text-optional": True,
           "symbol-sort-key": ["match", ["get", "kind"], "gipfel", 0, "pass", 1, "huette", 2, "see", 3, "kapelle", 4, "schlafplatz", 9, 5]}
    layers = [
        {"id": "bk-papier", "type": "background", "paint": {"background-color": P["paper"]}},
        {"id": "bk-land", "type": "raster", "source": "land", "paint": {"raster-opacity": 1, "raster-resampling": "linear", "raster-fade-duration": 0}},
        {"id": "bk-relief", "type": "hillshade", "source": "dem",
         "paint": {"hillshade-method": "igor", "hillshade-exaggeration": P["relief"], "hillshade-illumination-direction": 315,
                   "hillshade-illumination-anchor": "map", "hillshade-shadow-color": P["shadow"], "hillshade-highlight-color": P["highlight"],
                   "hillshade-accent-color": P["accent"]}},
        {"id": "bk-hk", "type": "line", "source": "bk", "filter": ["all", t("hk"), vis], "layout": {"line-join": "round"},
         "paint": {"line-color": ["case", gl, P["contour_glacier"], [">=", ["get", "lvl"], 100], P["contour_index"], P["contour"]],
                   "line-opacity": 0.75 if dark else 0.9,
                   "line-width": ["interpolate", ["linear"], ["zoom"], 12, ["case", [">=", ["get", "lvl"], 100], 0.55, 0.3],
                                  15, ["case", [">=", ["get", "lvl"], 100], 1.0, 0.45], 18, ["case", [">=", ["get", "lvl"], 100], 1.6, 0.8]]}},
        {"id": "bk-see", "type": "fill", "source": "bk", "filter": t("see"), "paint": {"fill-color": P["water"], "fill-outline-color": P["water_line"]}},
        {"id": "bk-bach", "type": "line", "source": "bk", "filter": t("bach"), "layout": {"line-cap": "round", "line-join": "round"},
         "paint": {"line-color": P["water_line"], "line-width": lw(0.8, 1.6, 3.2)}},
        {"id": "bk-strasse-r", "type": "line", "source": "bk", "filter": t("strasse"), "layout": {"line-join": "round", "line-cap": "round"},
         "paint": {"line-color": P["casing"], "line-width": lw(2.4, 4.6, 9)}},
        {"id": "bk-strasse", "type": "line", "source": "bk", "filter": t("strasse"), "layout": {"line-join": "round", "line-cap": "round"},
         "paint": {"line-color": P["road"], "line-width": lw(1.4, 3.0, 6.5)}},
        {"id": "bk-wege-r", "type": "line", "source": "bk", "filter": t("weg"), "layout": {"line-join": "round", "line-cap": "round"},
         "paint": {"line-color": ["case", ["==", g_, 1], P["weg1_casing"], P["weg_casing"]], "line-width": lw(2.3, 3.6, 5.6),
                   "line-opacity": ["case", ["==", g_, 1], 0.55, 0.85]}},
        {"id": "bk-wege-1", "type": "line", "source": "bk", "filter": ["all", t("weg"), ["==", g_, 1]], "layout": {"line-join": "round", "line-cap": "round"},
         "paint": {"line-color": P["weg1"], "line-width": lw(1.1, 1.9, 3.2)}},
        {"id": "bk-wege-23", "type": "line", "source": "bk", "filter": ["all", t("weg"), [">=", g_, 2]], "layout": {"line-join": "round"},
         "paint": {"line-color": ["case", ["==", g_, 3], P["weg3"], P["weg2"]], "line-width": lw(1.1, 1.9, 3.2), "line-dasharray": [2.4, 1.2]}},
        {"id": "bk-hk-text", "type": "symbol", "source": "bk", "minzoom": 14.5,
         "filter": ["all", t("hk"), ["any", [">=", ["get", "lvl"], 100], ["all", [">=", ["zoom"], 16], [">=", ["get", "lvl"], 50]]]],
         "layout": {"symbol-placement": "line", "text-field": ["to-string", ["get", "ele"]], "text-font": ["Noto Sans Regular"],
                    "text-size": 10, "symbol-spacing": 320, "text-max-angle": 25, "text-padding": 4},
         "paint": {"text-color": ["case", gl, P["contour_text_glacier"], P["contour_text"]], "text-halo-color": P["halo"], "text-halo-width": 1.4}},
        {"id": "bk-see-text", "type": "symbol", "source": "bk", "filter": t("see"), "minzoom": 14,
         "layout": {"text-field": ["to-string", ["get", "ele"]], "text-font": ["Noto Sans Italic"], "text-size": 10},
         "paint": {"text-color": P["water_text"], "text-halo-color": P["halo"], "text-halo-width": 1.2}},
        {"id": "bk-orte", "type": "symbol", "source": "bk", "filter": t("ort"), "layout": sym,
         "paint": {"text-color": ["match", ["get", "kind"], ["see", "gletscher", "wasserfall", "moor"], P["water_text"], "gipfel", P["peak"], P["text"]],
                   "text-halo-color": P["halo"], "text-halo-width": 1.5}},
        {"id": "bk-geheim", "type": "symbol", "source": "geheim", "filter": ["==", ["geometry-type"], "Point"],
         "layout": dict(sym, **{"icon-image": "bk-geheim", "text-field": ["get", "name"]}),
         "paint": {"text-color": "#b0479a" if not dark else "#e08ad0", "text-halo-color": P["halo"], "text-halo-width": 1.5}},
    ]
    # the secret trails / lakes: under the trails of the map
    layers.insert(5, {"id": "bk-geheim-see", "type": "fill", "source": "geheim", "filter": ["==", ["geometry-type"], "Polygon"],
                      "paint": {"fill-color": P["water"], "fill-outline-color": P["water_line"]}})
    layers.insert(-3, {"id": "bk-geheim-weg", "type": "line", "source": "geheim", "filter": ["==", ["geometry-type"], "LineString"],
                       "layout": {"line-join": "round"}, "paint": {"line-color": P["weg3"], "line-width": lw(1.1, 1.9, 3.2), "line-dasharray": [2.4, 1.2]}})
    return {"version": 8, "name": "MoveEye Bergtal (%s)" % ("dunkel" if dark else "hell"),
            "sources": {"bk": {"type": "geojson", "data": "{B}/vektor.json", "maxzoom": 17, "tolerance": 0.25},
                        "geheim": {"type": "geojson", "data": {"type": "FeatureCollection", "features": []}},
                        "dem": {"type": "raster-dem", "tiles": ["{B}/dem/{z}/{x}/{y}.png"], "tileSize": 256, "encoding": "terrarium",
                                "minzoom": DEM_Z[0], "maxzoom": maxzoom, "bounds": bounds},
                        "land": {"type": "image", "url": "{B}/" + ("land_dunkel.png" if dark else "land.png"), "coordinates": "{LANDC}"}},
            "glyphs": "{B}/web/fonts/{fontstack}/{range}.pbf", "layers": layers}


# ---- the package -----------------------------------------------------------------------------------------------------------------
def web_files(web_zip):
    out = {}
    with zipfile.ZipFile(web_zip) as z:
        names = set(z.namelist())
        for f in WEB_FILES:
            out["web/" + f] = z.read(f)
        for fo in FONTS:
            for r in RANGES:
                n = "fonts/%s/%s.pbf" % (fo, r)
                if n in names:
                    out["web/" + n] = z.read(n)
        lic = z.read("LIZENZEN.txt").decode("utf-8")
        meta = json.loads(z.read("karte.json")) if "karte.json" in names else {}
    return out, lic, meta


LIZENZ = """MoveEye – Karte «Bergtal» (%s): Quellen und Lizenzen
================================================================

KARTENDATEN (hoehen.f32, dem/, land*.png, vektor.json, geheim.json, touren.json)
  Das Bergtal ist erfunden: alle Daten stammen aus dem Simulator «MoveEye Sim» %s (simulator3d/scripts/bergtal*.gd,
  berechnet mit werkzeuge/bergkarte/export.gd und paket.py). Keine echten Koordinaten, keine Daten von swisstopo oder
  OpenStreetMap. Lizenz wie das Projekt MoveEye.

KARTENSTIL (stil.json, stil_dunkel.json): Farben der Topo-Karte von MoveEye (werkzeuge/karten/stil.py).

PROGRAMM UND SCHRIFTEN (web/): unverändert aus karte-web (MapLibre GL JS %s – BSD-3-Clause; Noto Sans – SIL Open Font
  License 1.1). Die Texte der Lizenzen: web/LIZENZEN_karte_web.txt.
"""


def bauen(exp, web_zip, aus):
    g = Gitter(exp)
    D = g.d
    files = {}
    log("Bergtal: Gitter %d × %d à %g m, %d Orte, %d geheim, %d Wege, Sim %s" % (g.n, g.n, g.step, len(D["places"]), len(D["secrets"]), len(D["trails"]), D["sim"]))
    files["hoehen.f32"] = open(os.path.join(exp, "hoehen.f32"), "rb").read()
    files.update(dem_tiles(g))
    log("  Höhen-Kacheln:", sum(1 for k in files if k.startswith("dem/")))
    cont = contours(g)
    log("  Höhenlinien:", sum(len(v) for v in cont.values()), "Linien")
    files["land.png"] = land_png(g)
    files["land_dunkel.png"] = land_png(g, True)
    vk = vektor(g, cont)
    files["vektor.json"] = json.dumps(vk, ensure_ascii=False, separators=(",", ":")).encode()
    files["geheim.json"] = json.dumps(geheim(g), ensure_ascii=False, separators=(",", ":")).encode()
    tours = touren(D)
    files["touren.json"] = json.dumps(tours, ensure_ascii=False, separators=(",", ":")).encode()
    a, b = ll(g.lo, g.lo), ll(g.hi, g.hi)
    bounds = [a[0], b[1], b[0], a[1]]                    # west, south, east, north
    for dark, nm in ((False, "stil.json"), (True, "stil_dunkel.json")):
        files[nm] = json.dumps(stil(dark, DEM_Z[1], bounds), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    wf, lic, wmeta = web_files(web_zip) if web_zip else ({}, "(ohne MapLibre gebaut - nur für Tests)\n", {})
    files.update(wf)
    files["web/LIZENZEN_karte_web.txt"] = lic.encode()
    files["LIZENZEN.txt"] = (LIZENZ % (TAG, D["sim"], wmeta.get("maplibre", "?"))).encode()
    counts = {"orte": len(D["places"]), "geheim": len(D["secrets"]), "wege": sum(1 for t in D["trails"] if not t["secret"]),
              "geheim_wege": sum(1 for t in D["trails"] if t["secret"]), "seen": sum(1 for l in D["lakes"] if not l["secret"]),
              "bach": len(D["streams"]), "touren": len(tours), "hk": sum(len(v) for v in cont.values())}
    head = {"tag": TAG, "format": FORMAT, "sim": D["sim"], "grid": D["grid"], "m_per_deg": M, "bounds": bounds,
            "landc": [ll(g.lo, g.lo), ll(g.hi, g.lo), ll(g.hi, g.hi), ll(g.lo, g.hi)], "dem": {"z": list(DEM_Z)},
            "center": ll(0, 0), "counts": counts, "maplibre": wmeta.get("maplibre", ""), "web_tag": wmeta.get("tag", "")}
    files["bergkarte.json"] = json.dumps(head, ensure_ascii=False, sort_keys=True).encode()
    os.makedirs(aus, exist_ok=True)
    zp = os.path.join(aus, NAME)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in sorted(files):
            i = zipfile.ZipInfo(n, FIX_TIME)
            i.external_attr = 0o644 << 16
            i.compress_type = zipfile.ZIP_STORED if n.endswith((".gz", ".png", ".pbf")) else zipfile.ZIP_DEFLATED
            zf.writestr(i, files[n])
    unpacked = sum(len(v) for v in files.values())
    log("PAKET %s %d Bytes (%d entpackt), %d Dateien, %s" % (zp, os.path.getsize(zp), unpacked, len(files), json.dumps(counts)))
    return zp


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pins(aus):
    zp = os.path.join(aus, NAME)
    with zipfile.ZipFile(zp) as z:
        unpacked = sum(i.file_size for i in z.infolist())
        head = json.loads(z.read("bergkarte.json"))
    line = "PIN bergkarte name=%s size=%d sha256=%s unpacked=%d tag=%s sim=%s\n" % (NAME, os.path.getsize(zp), sha256(zp), unpacked, TAG, head["sim"])
    open(os.path.join(aus, "pins_bergkarte.txt"), "w").write(line)
    log(line.strip())
    return line


def eintragen(pins_txt, teil=QUELLE_TEIL):
    src = open(teil, encoding="utf-8").read()
    m = re.search(r"^PIN bergkarte name=(\S+) size=(\d+) sha256=([0-9a-f]{64}) unpacked=(\d+) tag=(\S+) sim=(\S+)", open(pins_txt, encoding="utf-8").read(), re.M)
    if not m:
        raise SystemExit("keine Zeile «PIN bergkarte …» in " + pins_txt)
    if m.group(5) != TAG:
        raise SystemExit("Tag %s ist nicht %s" % (m.group(5), TAG))
    neu = 'BK_FILE = {"name": "%s", "size": %s, "sha256": "%s", "unpacked": %s, "sim": "%s"}' % (m.group(1), m.group(2), m.group(3), m.group(4), m.group(6))
    src, n = re.subn(r'^BK_FILE = \{"name": "[^"]*", "size": \d+, "sha256": "[0-9a-f]*", "unpacked": \d+, "sim": "[^"]*"\}', neu, src, flags=re.M)
    if n != 1:
        raise SystemExit("BK_FILE nicht genau einmal gefunden")
    open(teil, "w", encoding="utf-8").write(src)
    log("eingetragen:", neu)


# ---- the check: package = simulator --------------------------------------------------------------------------------------------------
def pruefen(aus, exp):
    """raises SystemExit on a difference; returns a short report"""
    g = Gitter(exp)
    D = g.d
    zp = os.path.join(aus, NAME)
    with zipfile.ZipFile(zp) as z:
        files = {n: z.read(n) for n in z.namelist()}
    fehler = []
    head = json.loads(files["bergkarte.json"])
    vk = json.loads(files["vektor.json"])
    gh = json.loads(files["geheim.json"])
    orte = [f for f in vk["features"] if f["properties"]["t"] == "ort"]
    if len(orte) != len(D["places"]) or head["counts"]["orte"] != len(D["places"]):
        fehler.append("Orte: %d im Paket, %d im Simulator" % (len(orte), len(D["places"])))
    names = {f["properties"]["name"] for f in orte}
    if names != {p["name"] for p in D["places"]}:
        fehler.append("Namen der Orte verschieden")
    sec_ids = {s["id"] for s in gh["orte"]}
    if sec_ids != {s["id"] for s in D["secrets"]} or any(s["name"] in names for s in D["secrets"]):
        fehler.append("geheime Orte verschieden / offen")
    txt = files["vektor.json"].decode("utf-8")
    for s in D["secrets"]:
        if s["name"] in txt:
            fehler.append("Geheimnis in vektor.json: " + s["name"])
    for t in D["trails"]:
        if t["secret"] and t["name"] in txt:
            fehler.append("geheimer Weg in vektor.json: " + t["name"])
    # heights: the f32 grid byte for byte, the DEM tiles at the sample points (nearest pixel of z15 ≈ 4.7 m: tolerance from the slope)
    if files["hoehen.f32"] != open(os.path.join(exp, "hoehen.f32"), "rb").read():
        fehler.append("hoehen.f32 ist nicht die Höhenkarte des Simulators")
    worst = 0.0
    for x, z, h in D["samples"]:
        if abs(g.H(x, z) - h) > 0.01:
            fehler.append("H(%g, %g): Python %.3f, Simulator %.3f" % (x, z, g.H(x, z), h))
        lon, lat = ll(x, z)
        r = dem_height(files, lon, lat)
        if r is None:
            fehler.append("keine Höhen-Kachel bei %g / %g" % (x, z))
            continue
        hd, clon, clat = r                                 # the pixel centre: the height there exactly (0.1-m steps)
        cx, cz = xz(clon, clat)
        dev = abs(hd - (g.alt0 + g.H(cx, cz)))
        worst = max(worst, dev)
        if dev > 0.06 or math.hypot(cx - x, cz - z) > 3.5:
            fehler.append("Höhen-Kachel bei %g / %g: %.2f statt %.2f" % (x, z, hd, g.alt0 + g.H(cx, cz)))
    st = json.loads(files["stil.json"])
    for need in ("bk-relief", "bk-hk", "bk-wege-1", "bk-wege-23", "bk-orte", "bk-geheim", "bk-land"):
        if need not in {l["id"] for l in st["layers"]}:
            fehler.append("Stil ohne " + need)
    tours = json.loads(files["touren.json"])
    if not any(t["name"].startswith("Hospiz") for t in tours):
        fehler.append("Vorschlag Hospiz → Pass → Biwak fehlt")
    for f_ in ("web/maplibre-gl.js", "web/maplibre-gl.css", "web/fonts/Noto Sans Regular/0-255.pbf", "land.png", "LIZENZEN.txt"):
        if f_ not in files and (f_.startswith(("land", "LIZ")) or head.get("maplibre")):     # without --web-zip: a package for tests
            fehler.append("fehlt: " + f_)
    rep = "PRUEFUNG %s: %d Orte, %d geheim, %d Stichproben der Höhe (grösste Abweichung der Kacheln %.3f m), %d Kacheln, Grösse %d Bytes" % (
        "OK" if not fehler else "FEHLER", len(orte), len(sec_ids), len(D["samples"]), worst, sum(1 for k in files if k.startswith("dem/")), os.path.getsize(zp))
    log(rep)
    for f_ in fehler[:30]:
        log("  ✗ " + f_)
    if fehler:
        raise SystemExit(1)
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--export")
    ap.add_argument("--web-zip")
    ap.add_argument("--ohne-web", action="store_true", help="ohne MapLibre (nur Tests)")
    ap.add_argument("--aus", default="bergkarte_aus")
    ap.add_argument("--pruefen")
    ap.add_argument("--pins", action="store_true")
    ap.add_argument("--eintragen")
    ap.add_argument("--web-pin", action="store_true", help="Name, Grösse und sha256 von karte-web in quelle/639zzq ausgeben")
    a = ap.parse_args()
    if a.web_pin:
        src = open(os.path.join(REPO, "quelle", "639zzq_offline_karten.py"), encoding="utf-8").read()
        m = re.search(r'"web": \{"name": "([^"]+)", "size": (\d+), "sha256": "([0-9a-f]{64})"', src)
        if not m:
            raise SystemExit("KQ_FILES web nicht gefunden")
        print(*m.groups())
        return
    if a.eintragen:
        eintragen(a.eintragen)
        return
    if a.pruefen:
        pruefen(a.pruefen, a.export)
        return
    if a.export:
        if not a.web_zip and not a.ohne_web:
            raise SystemExit("--web-zip karte-web-N.zip fehlt (MapLibre + Schriften; nur für Tests: --ohne-web)")
        bauen(a.export, a.web_zip, a.aus)
    if a.pins:
        pins(a.aus)


if __name__ == "__main__":
    main()
