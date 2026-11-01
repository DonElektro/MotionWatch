#!/usr/bin/env python3
"""Gehäuse v5.1 – eine Quelle (hardware/gehaeuse/) für Druckdateien, Simulator-Modelle, Vorschaubilder und Texte.

Quelle: hardware/gehaeuse/Quellcode/*.py (Daniels parametrisches Modell: v5.py, pantilt.py, csg.py, decimate.py …) und
hardware/gehaeuse/bau.json (Teile, Materialliste, Montageschritte, Texte in de/en/fr/it/rm). Daraus:

    python3 werkzeuge/gehaeuse_bauen.py --sim      # Simulator: simulator3d/inhalte/gehaeuse/gehaeuse.glb (alle Teile, Werkstatt)
                                                   #   + gehaeuse_lite.glb (nur die äusseren Teile, gröber, für Lite) + modelle.json,
                                                   #   dazu --texte (ca. 3–5 min auf 2 Kernen)
    python3 werkzeuge/gehaeuse_bauen.py --texte    # nur die Texte: simulator3d/scripts/werkstatt_daten.gd, Übersetzungen in
                                                   #   simulator3d/i18n/texte.json, quelle/639v_daten_gehaeuse.py (Sekunden)
    python3 werkzeuge/gehaeuse_bauen.py --druck    # STL + 3MF neu (export5.py + plates5.py in einem Arbeitsordner): 3MF nach
                                                   #   hardware/gehaeuse/Druckdateien/, STL als ZIP nach --ziel (Standard
                                                   #   /tmp/gehaeuse_dist) – dauert lange (Unterteil allein ca. 20–25 min)
    python3 werkzeuge/gehaeuse_bauen.py --bilder   # Vorschaubilder mit prev51.py -> hardware/gehaeuse/Bilder/Vorschau_v5-1_*.png
    python3 werkzeuge/gehaeuse_bauen.py --pruefen  # passen Simulator-Modelle und Daten zur Quelle? (Exit 1 sonst; auch im
                                                   #   Selbsttest von MoveEye, Teil 639w)

Vereinfachen: das SDF-Modell wird grob abgetastet (export.mesh, Marching Cubes) und mit decimate.cluster_qem (Daniels
Vertex-Clustering) vereinfacht. Koordinaten im Simulator: Meter, Ursprung = Kippachse auf der Pan-Achse (main.head /
main.head_pitch), Godot X = Modell y − AY, Y = Modell z − Kippachse, Z = Modell x − AX (vorne = PIR-Seite = −Z wie der Blick
des Kopfes in Grundstellung, v5.placed(0, 180)). Gruppen: base (Unterteil, dreht nicht), pan (dreht mit main.head),
tilt (kippt mit main.head_pitch). Prüfsumme: SHA-256 über Quellcode/*.py, bau.json und diese Datei (QUELLE_SHA).
Benötigt: numpy, scipy, scikit-image (wie das Modell selbst).
"""
import argparse
import glob
import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
GEH = os.path.join(REPO, "hardware", "gehaeuse")
QUELL = os.path.join(GEH, "Quellcode")
BAU = os.path.join(GEH, "bau.json")
SIMDIR = os.path.join(REPO, "simulator3d", "inhalte", "gehaeuse")
GD_OUT = os.path.join(REPO, "simulator3d", "scripts", "werkstatt_daten.gd")
TEXTE = os.path.join(REPO, "simulator3d", "i18n", "texte.json")
MW_OUT = os.path.join(REPO, "quelle", "639v_daten_gehaeuse.py")
LANGS = ("de", "en", "fr", "it", "rm")

# ---- Geometrie der Simulator-Teile -----------------------------------------------------------------------------------------
# id: (Gruppe, Abtastung h mm, Zellgrösse c mm, Farbe, aussen (am Gerät in der Szene), Explosion: Höhe mm, Streuung)
GEO = {
    "tub": ("base", 1.0, 4.0, "#3a73bf", True, 0, 0.0), "feet": ("base", 0.6, 2.0, "#333333", True, -35, 0.3),
    "tripod": ("base", 0.5, 1.0, "#b8b8bc", False, -18, 0.0), "speaker": ("base", 0.8, 1.6, "#e6d933", False, 95, 0.6),
    "pca": ("base", 0.5, 0.7, "#1a4db3", False, 120, 0.8), "elko": ("base", 0.5, 1.0, "#222a55", False, 120, 1.0),
    "pir": ("base", 0.5, 1.0, "#f7f7e6", False, 115, 1.0), "mic": ("base", 0.5, 1.0, "#1accc9", False, 120, 1.0),
    "ups": ("base", 0.8, 1.6, "#8cbf40", False, 100, 0.3), "pi": ("base", 0.5, 0.8, "#268c40", False, 150, 0.3),
    "cooler": ("base", 0.6, 1.2, "#1f1f1f", False, 180, 0.3), "shelf": ("base", 0.6, 1.6, "#4d80cc", False, 125, 0.9),
    "charger": ("base", 0.5, 0.8, "#1a8c4d", False, 150, 0.9), "pam": ("base", 0.5, 0.8, "#d94d99", False, 150, 0.9),
    "ina": ("base", 0.5, 0.8, "#1a4dcc", False, 150, 0.9), "mosfet": ("base", 0.5, 0.7, "#8c5933", False, 135, 1.2),
    "buck": ("base", 0.5, 0.7, "#d93333", False, 135, 1.2), "relay": ("base", 0.5, 0.7, "#3359d9", False, 140, 1.1),
    "hub": ("base", 0.6, 1.2, "#66666f", False, 130, 0.9), "soundcard": ("base", 0.5, 1.0, "#f2f2f2", False, 145, 0.9),
    "mpu": ("base", 0.5, 0.7, "#8033cc", False, 90, 1.0), "bme": ("base", 0.5, 0.7, "#991a99", False, 135, 1.2),
    "cable_usb": ("base", 0.7, 1.4, "#202020", False, 165, 0.5), "cable_power": ("base", 0.7, 1.4, "#c0392b", False, 110, 0.5),
    "jacks": ("base", 0.6, 1.2, "#4d4d4d", True, 30, 1.6), "fuse": ("base", 0.5, 1.0, "#e74c3c", False, 150, 1.0),
    "ledlight": ("base", 0.4, 0.8, "#2ecc71", True, 30, 1.6), "relayjack": ("base", 0.6, 1.2, "#4d4d4d", True, 20, 1.6),
    "probe": ("base", 0.6, 1.2, "#bfbfc7", True, -60, 0.0), "plug": ("base", 0.5, 1.6, "#262626", True, 0, 1.5),
    "lid": ("base", 0.8, 3.5, "#5999e6", True, 230, 0.0), "servo1": ("base", 0.6, 1.2, "#264099", False, 205, 0.0),
    "balls": ("base", 0.6, 1.4, "#ccccd1", False, 258, 0.0), "cable_servo": ("base", 0.7, 1.4, "#e67e22", False, 200, 0.5),
    "horn1": ("pan", 0.4, 0.8, "#e6e6e6", False, 272, 0.0), "turntable": ("pan", 0.7, 2.5, "#f28c26", True, 290, 0.0),
    "yoke": ("pan", 0.6, 2.2, "#f28c26", True, 330, 0.0), "horn2": ("pan", 0.4, 0.8, "#e6e6e6", False, 330, 1.4),
    "arm2": ("pan", 0.6, 2.2, "#f28c26", True, 335, 1.2), "lamp1": ("pan", 0.5, 1.8, "#f28c26", True, 335, 1.4),
    "lamp2": ("pan", 0.5, 1.8, "#f28c26", True, 335, 1.4), "alu": ("pan", 0.4, 0.8, "#bfbfc7", False, 335, 1.8),
    "lens_w": ("pan", 0.5, 1.0, "#fff299", True, 335, 2.1), "lens_ir": ("pan", 0.5, 1.0, "#bf1a1a", True, 335, 2.1),
    "cable_cam": ("base", 0.7, 1.4, "#d9c27a", False, 280, 0.0),
    "head": ("tilt", 0.6, 2.2, "#38383f", True, 400, 0.0), "side": ("tilt", 0.6, 2.2, "#595961", True, 400, 2.5),
    "servo2": ("tilt", 0.6, 1.2, "#264099", False, 400, 1.5), "cam3": ("tilt", 0.4, 0.8, "#991a1a", True, 400, 3.0),
    "therm": ("tilt", 0.4, 0.8, "#8c268c", True, 400, 3.0),
    "wide": ("base", 0.4, 0.8, "#b33333", False, 115, 1.5), "irled": ("base", 0.4, 0.8, "#7f1a1a", False, 115, 1.5),
    "buttons": ("base", 0.5, 1.0, "#e6b800", False, 40, 1.5), "sled": ("tilt", 0.4, 0.8, "#f2f2f2", False, 450, 0.0),
}
LITE_K = 2.3                         # Lite: Zellen so viel grösser


def quelle_dateien():
    fs = sorted(glob.glob(os.path.join(QUELL, "*.py"))) + [BAU, os.path.abspath(__file__)]
    return fs


def quelle_sha():
    """SHA-256 über die Quelle: Name + Inhalt jeder Datei (Quellcode/*.py, bau.json, dieses Werkzeug)"""
    h = hashlib.sha256()
    for p in quelle_dateien():
        h.update(os.path.relpath(p, REPO).replace(os.sep, "/").encode() + b"\0")
        with open(p, "rb") as f:
            h.update(f.read())
        h.update(b"\0")
    return h.hexdigest()


def sha_datei(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def lade_bau():
    with open(BAU, encoding="utf-8") as f:
        return json.load(f)


def tx(v, lang):
    """ein Text aus bau.json in einer Sprache (einzelner Text = überall gleich)"""
    if isinstance(v, str):
        return v
    return v.get(lang) or (v.get("de") if lang == "rm" else v.get("en")) or v.get("de", "")


# ---- Modell: Teile in Grundstellung ---------------------------------------------------------------------------------------
def modell():
    """{id: SDF-Knoten in Modell-Koordinaten (mm)} – v5.placed(0, 180) + Kleinteile, Kabel und Variante v5.2 (nur Simulator)"""
    sys.path.insert(0, QUELL)
    import numpy as np
    import v5
    import pantilt as pt
    from csg import T, R, RM, U, D, box, cyl_x, cyl_y, cyl_z, Cyl
    P = v5.placed(0.0, 180.0)
    ZF, LX, LY, AX, AY, WALL = v5.ZF, v5.LX, v5.LY, v5.AX, v5.AY, v5.WALL

    def seg(p0, p1, d):
        p0, p1 = np.array(p0, float), np.array(p1, float)
        a = p1 - p0
        L = float(np.linalg.norm(a))
        e3 = a / L
        e1 = np.cross(e3, [0, 0, 1.0] if abs(e3[2]) < 0.9 else [1.0, 0, 0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(e3, e1)
        return T(p0, RM(np.column_stack([e1, e2, e3]), Cyl(L, d=d, fn=16)))

    def kabel(pts, d):
        return U(*[seg(pts[i], pts[i + 1], d) for i in range(len(pts) - 1)])

    tx_, ty_ = v5.TRIPOD_XY
    P["tripod"] = D(cyl_z(tx_, ty_, ZF + 0.3, ZF + 5.8, 11.0, fn=6), cyl_z(tx_, ty_, ZF, ZF + 7, 6.4))
    P["elko"] = cyl_z(60.0, 10.0, ZF + 8.0, ZF + 20.0, 8.0)
    P["mpu"] = box(52.0, 69.0, 50.0, 66.0, ZF + 0.5, ZF + 3.0)                      # flach auf dem Boden neben dem Stativdom
    P["bme"] = box(LX - 1.6, LX - 0.2, 30.0, 52.0, ZF + 30.0, ZF + 50.0)            # Lage geschätzt (Rückwand innen)
    P["fuse"] = U(box(158.0, 172.0, 83.5, 90.0, v5.SHELF_Z, v5.SHELF_Z + 7.0), cyl_x(86.7, v5.SHELF_Z + 3.5, 172.0, 176.0, 3.0))
    P["ledlight"] = U(cyl_x(v5.LED_Y, v5.LED_Z, LX - 6.0, LX + WALL + 0.5, 3.0), cyl_x(v5.LED_Y, v5.LED_Z, LX - 10.0, LX - 6.0, 3.6))
    px = v5.BAT_X0 + 1
    PI_Z = v5.PI_Z
    P["cable_cam"] = kabel([(v5.CHIM_X, AY, v5.TOPZ + 1.0), (v5.CHIM_X, AY, v5.TOPZ - 8.0), (px + 46.0, 30.0, PI_Z + 6.0), (px + 46.0, 22.0, PI_Z + 2.5)], 4.0)
    P["cable_servo"] = kabel([(AX - 14.0, AY - 7.0, v5.TOPZ - 22.0), (AX - 5.0, 20.0, ZF + 50.0), (55.0, 9.0, ZF + 49.0)], 3.0)
    P["cable_usb"] = kabel([(px + 86.0, 22.0, PI_Z + 9.0), (LX - 4.0, 30.0, PI_Z + 20.0), (100.0, 62.0, PI_Z + 22.0), (v5.HUB_X1 - 2.0, 76.0, ZF + v5.HUB_TRAY_Z + 6.0)], 4.0)
    P["cable_power"] = kabel([(v5.BAT_X0 + 2.0, 70.0, ZF + 14.0), (55.0, 70.0, ZF + 14.0), (8.0, 40.0, ZF + 22.0), (2.5, 22.0, ZF + 24.0)], 3.0)
    # Variante v5.2 (Werte aus v52.py, Gehäuse-Paket v5.2 – im Simulator nur zum Ansehen, Masse wie dort)
    t12 = math.radians(12.0)
    WA = np.array([-math.cos(t12), 0.0, -math.sin(t12)])
    WH = np.array([0.0, 1.0, 0.0])
    WU = np.array([-math.sin(t12), 0.0, math.cos(t12)])
    WL = np.array([0.5, AY, 56.0])
    WB = WL - 11.4 * WA
    WM = np.column_stack([-WA, WH, WU])
    cam_l = U(box(0.0, 1.0, -12.5, 12.5, -14.5, 9.5), T([-11.4, 0, 0], R([0, 90, 0], Cyl(11.4, d=8.5, fn=24))))
    P["wide"] = T(WB, RM(WM, cam_l))
    P["irled"] = U(cyl_x(26.0, 40.0, -2.5, 6.1, 5.0), cyl_x(26.0, 40.0, 6.1, 7.1, 5.8))
    P["buttons"] = U(*[cyl_x(y, 33.0, LX - 12.0, LX + WALL + 3.0, 12.0) for y in (10.5, 50.5)])

    def tilt_frame(n):
        return T([AX, AY, v5.PAN_Z0], R([0, 0, 180.0], T([0, 0, pt.AXZ], n)))
    P["sled"] = tilt_frame(U(cyl_z(3.0, 8.0, pt.HH / 2 - 1.0, pt.HH / 2 + 7.5, 14.0, fn=32), cyl_z(3.0, 8.0, pt.HH / 2 + 7.5, pt.HH / 2 + 8.3, 9.0, fn=32)))
    org = np.array([AX, AY, v5.PAN_Z0 + pt.AXZ])
    return P, org, {"tilt_axis_mm": round(float(v5.PAN_Z0 + pt.AXZ), 2), "feet_mm": 6.0}


def prim_mesh(node, seg=20):
    """Teile aus einfachen Körpern (Vereinigung von Quadern, Zylindern, Ringen – Platinen, Module, Kabel) direkt als Netz,
    ohne Abtasten: wenige Dreiecke, scharfe Kanten. None, wenn der Knoten Differenzen / Schnitte enthält (dann Marching
    Cubes + cluster_qem wie bei den Druckteilen)."""
    import numpy as np
    import csg
    if isinstance(node, csg.Cube):
        lo, hi = node.lo, node.hi
        v = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])], float)
        f = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6],
                      [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
        return v, f
    if isinstance(node, csg.RBox):
        return prim_mesh(csg.Cube(node.lo, node.hi))
    if isinstance(node, csg.Cyl):
        n = 6 if node.fn == 6 else seg
        a = np.arange(n) * 2 * math.pi / n
        b = np.column_stack([np.cos(a) * node.r1, np.sin(a) * node.r1, np.zeros(n)])
        t = np.column_stack([np.cos(a) * node.r2, np.sin(a) * node.r2, np.full(n, node.h)])
        v = np.vstack([b, t, [[0, 0, 0], [0, 0, node.h]]])
        f = []
        for i in range(n):
            j = (i + 1) % n
            f += [[i, j, n + j], [i, n + j, n + i], [2 * n, j, i], [2 * n + 1, n + i, n + j]]
        return v, np.array(f)
    if isinstance(node, csg.Torus):
        nu, nv = 32, 8
        u, w = np.meshgrid(np.arange(nu) * 2 * math.pi / nu, np.arange(nv) * 2 * math.pi / nv, indexing="ij")
        R_, r_ = node.R, node.r
        v = np.column_stack([((R_ + r_ * np.cos(w)) * np.cos(u)).ravel(), ((R_ + r_ * np.cos(w)) * np.sin(u)).ravel(), (r_ * np.sin(w)).ravel()])
        f = []
        for i in range(nu):
            for k in range(nv):
                a0, a1 = i * nv + k, ((i + 1) % nu) * nv + k
                b0, b1 = i * nv + (k + 1) % nv, ((i + 1) % nu) * nv + (k + 1) % nv
                f += [[a0, a1, b1], [a0, b1, b0]]
        return v, np.array(f)
    if isinstance(node, csg.T):
        m = prim_mesh(node.c, seg)
        return None if m is None else (m[0] + node.v, m[1])
    if isinstance(node, csg.R):                           # also RM: world = local @ M^T
        m = prim_mesh(node.c, seg)
        return None if m is None else (m[0] @ node.M.T, m[1])
    if isinstance(node, csg.U):
        vs, fs, k = [], [], 0
        for c in node.c:
            m = prim_mesh(c, seg)
            if m is None:
                return None
            vs.append(m[0])
            fs.append(m[1] + k)
            k += len(m[0])
        return np.vstack(vs), np.vstack(fs)
    return None


def zu_godot(v, org):
    """Modell mm -> Godot m relativ zur Kippachse: X = y, Y = z, Z = x"""
    import numpy as np
    w = (v - org) / 1000.0
    return np.column_stack([w[:, 1], w[:, 2], w[:, 0]]).astype(np.float32)


def normalen(v, f, winkel=40.0):
    """Ecken-Normalen mit Kanten ab «winkel» Grad (scharfe Kanten bleiben scharf); gibt neue v, n, f zurück"""
    import numpy as np
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    fn = np.cross(b - a, c - a)
    ar = np.linalg.norm(fn, axis=1, keepdims=True)
    fn = fn / np.maximum(ar, 1e-20)
    cw = math.cos(math.radians(winkel))
    nv = len(v)
    corner_v = f.ravel()                                  # Ecke k -> Vertex
    corner_f = np.repeat(np.arange(len(f)), 3)
    order = np.argsort(corner_v, kind="stable")
    cv, cf = corner_v[order], corner_f[order]
    start = np.searchsorted(cv, np.arange(nv + 1))
    cn = np.zeros((len(corner_v), 3))
    deg = np.diff(start)
    for d in np.unique(deg):                              # alle Vertices mit gleich vielen Ecken auf einmal
        if d == 0:
            continue
        vs = np.nonzero(deg == d)[0]
        idx = start[vs][:, None] + np.arange(d)[None, :]   # (V, d) -> Ecken-Positionen in order
        F = fn[cf[idx]]                                     # (V, d, 3)
        W = ar[cf[idx], 0][..., None]                       # Flächengewicht
        dots = np.einsum("vik,vjk->vij", F, F)              # (V, d, d)
        m = (dots >= cw).astype(float)
        s = np.einsum("vij,vjk->vik", m, F * W)
        s /= np.maximum(np.linalg.norm(s, axis=2, keepdims=True), 1e-20)
        cn[order[idx.ravel()]] = s.reshape(-1, 3)
    q = np.round(cn * 64).astype(np.int32)
    key = np.column_stack([corner_v, q])
    uk, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    nv2 = np.zeros((len(uk), 3))
    np.add.at(nv2, inv, cn)
    nv2 /= np.maximum(np.linalg.norm(nv2, axis=1, keepdims=True), 1e-20)
    return v[uk[:, 0]], nv2.astype(np.float32), inv.reshape(-1, 3)


def schreibe_glb(pfad, teile):
    """teile: [(name, v float32 (N,3), n float32 (N,3), f int (M,3), farbe '#rrggbb')] -> GLB (glTF 2.0, ein Puffer)"""
    import numpy as np
    blobs, views, accs, meshes, nodes, mats = [], [], [], [], [], []
    off = 0

    def add(arr, target, comp, typ, mn=None, mx=None):
        nonlocal off
        b = arr.tobytes()
        pad = (-len(b)) % 4
        blobs.append(b + b"\0" * pad)
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(b), "target": target})
        off += len(b) + pad
        a = {"bufferView": len(views) - 1, "componentType": comp, "count": int(arr.shape[0] if arr.ndim > 1 else arr.size), "type": typ}
        if mn is not None:
            a["min"], a["max"] = mn, mx
        accs.append(a)
        return len(accs) - 1
    for name, v, n, f, col in teile:
        ia = add(v, 34962, 5126, "VEC3", [float(x) for x in v.min(0)], [float(x) for x in v.max(0)])
        ib = add(n, 34962, 5126, "VEC3")
        big = len(v) > 65535
        idx = f.astype(np.uint32 if big else np.uint16).ravel()
        ic = add(idx, 34963, 5125 if big else 5123, "SCALAR")
        r, g, b_ = (int(col[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
        mats.append({"name": name, "pbrMetallicRoughness": {"baseColorFactor": [r, g, b_, 1.0], "metallicFactor": 0.0,
                     "roughnessFactor": 0.7}, "doubleSided": True})
        meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": ia, "NORMAL": ib}, "indices": ic, "material": len(mats) - 1}]})
        nodes.append({"name": name, "mesh": len(meshes) - 1})
    binb = b"".join(blobs)
    gl = {"asset": {"version": "2.0", "generator": "MoveEye werkzeuge/gehaeuse_bauen.py"}, "scene": 0,
          "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes, "materials": mats,
          "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(binb)}]}
    js = json.dumps(gl, separators=(",", ":")).encode()
    js += b" " * ((-len(js)) % 4)
    with open(pfad, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binb)))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        fh.write(struct.pack("<II", len(binb), 0x004E4942) + binb)


def baue_sim(nur=None):
    import numpy as np
    import time
    bau = lade_bau()
    ids = [t["id"] for t in bau["teile"]]
    fehlt = [i for i in ids if i not in GEO] + [i for i in GEO if i not in ids]
    if fehlt:
        sys.exit("bau.json und GEO passen nicht zusammen: " + ", ".join(fehlt))
    sys.path.insert(0, QUELL)
    from export import mesh
    from decimate import cluster_qem
    P, org, info = modell()
    os.makedirs(SIMDIR, exist_ok=True)
    normal, lite, meta = [], [], []
    t_all = time.time()
    tub_c = None
    for i in ids:
        grp, h, c, col, aussen, lvl, spread = GEO[i]
        t0 = time.time()
        pm = prim_mesh(P[i])
        if pm is not None:                                # simple bodies: directly (Lite: fewer segments)
            v, f = v1, f1 = pm
        else:
            v, f = mesh(P[i], h)
            v1, f1 = cluster_qem(v, f, c)
        g = zu_godot(v1, org)
        gv, gn, gf = normalen(g, f1)
        normal.append((i, gv, gn, gf, col))
        e = {"id": i, "gruppe": grp, "farbe": col, "aussen": aussen, "dreiecke": int(len(gf)),
             "mitte": [round(float(x), 4) for x in (g.min(0) + g.max(0)) / 2], "groesse": [round(float(x), 4) for x in g.max(0) - g.min(0)]}
        if aussen:
            v2, f2 = prim_mesh(P[i], 10) if pm is not None else cluster_qem(v, f, c * LITE_K)
            lv, ln, lf = normalen(zu_godot(v2, org), f2)
            lite.append((i, lv, ln, lf, col))
            e["dreiecke_lite"] = int(len(lf))
        if i == "tub":
            tub_c = e["mitte"]
        meta.append(e)
        print(f"  {i:12s} {len(f):7d} -> {len(gf):6d} Dreiecke{'  Lite ' + str(e.get('dreiecke_lite')) if aussen else ''}  {time.time() - t0:5.1f}s", flush=True)
    for e in meta:                                       # Explosion (Werkstatt): Höhe + Streuung vom Mittelpunkt der Gruppe weg
        grp, _h, _c, _col, _a, lvl, spread = GEO[e["id"]]
        ax_ = [0.0, 0.0, tub_c[2]] if grp == "base" else [0.0, 0.0, 0.0]
        e["explosion"] = [round((e["mitte"][0] - ax_[0]) * spread, 4), round(lvl / 1000.0, 4), round((e["mitte"][2] - ax_[2]) * spread, 4)]
    schreibe_glb(os.path.join(SIMDIR, "gehaeuse.glb"), normal)
    schreibe_glb(os.path.join(SIMDIR, "gehaeuse_lite.glb"), lite)
    for fn in ("gehaeuse.glb", "gehaeuse_lite.glb"):
        with open(os.path.join(SIMDIR, fn + ".import"), "w") as fh:
            fh.write('[remap]\n\nimporter="keep"\n')
    man = {"_hinweis": "Erzeugt von werkzeuge/gehaeuse_bauen.py aus hardware/gehaeuse/ – nicht von Hand ändern. "
                       "Koordinaten: Meter, Ursprung Kippachse (main.head_pitch), Godot X = Modell y, Y = z, Z = x (vorne = −Z).",
           "version": bau["version"], "quelle_sha256": quelle_sha(),
           "dateien": {fn: sha_datei(os.path.join(SIMDIR, fn)) for fn in ("gehaeuse.glb", "gehaeuse_lite.glb")},
           "dreiecke": sum(e["dreiecke"] for e in meta), "dreiecke_aussen": sum(e["dreiecke"] for e in meta if e["aussen"]),
           "dreiecke_lite": sum(e.get("dreiecke_lite", 0) for e in meta),
           "kippachse_ueber_boden_m": round(info["tilt_axis_mm"] / 1000.0, 4), "fuesse_m": info["feet_mm"] / 1000.0,
           "teile": meta}
    with open(os.path.join(SIMDIR, "modelle.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(man, ensure_ascii=False, indent=1) + "\n")
    print(f"Simulator-Modelle: {man['dreiecke']} Dreiecke (aussen {man['dreiecke_aussen']}, Lite {man['dreiecke_lite']}), "
          f"{os.path.getsize(os.path.join(SIMDIR, 'gehaeuse.glb')) // 1024} KB + {os.path.getsize(os.path.join(SIMDIR, 'gehaeuse_lite.glb')) // 1024} KB, "
          f"{time.time() - t_all:.0f}s")


# ---- Texte: Simulator (werkstatt_daten.gd + texte.json) und MoveEye (639v) -------------------------------------------------
def gd_str(s):
    return json.dumps(s, ensure_ascii=False)


def baue_texte():
    bau = lade_bau()
    bom = {b["id"]: b for b in bau["bom"]}
    sha = quelle_sha()
    for t in bau["teile"]:
        if t.get("bom") and t["bom"] not in bom:
            sys.exit(f"Teil {t['id']}: Materialliste-Eintrag {t['bom']} fehlt")
        if t.get("schritt") and not 1 <= t["schritt"] <= len(bau["schritte"]):
            sys.exit(f"Teil {t['id']}: Schritt {t['schritt']} fehlt")
    pairs = {}                                            # German -> {en, fr, it, rm}

    def de(v):
        d = tx(v, "de")
        if any(ch.isalpha() for ch in d):
            pairs[d] = {L: tx(v, L) for L in LANGS[1:]}
        return d
    L = ["extends RefCounted", "## Gehäuse v5.1 für die Werkstatt (werkstatt.gd) – erzeugt von werkzeuge/gehaeuse_bauen.py aus",
         "## hardware/gehaeuse/bau.json. NICHT VON HAND ÄNDERN (Texte dort ändern, dann «gehaeuse_bauen.py --texte»).",
         "## Texte deutsch (T.t übersetzt sie, Übersetzungen kommen aus bau.json in i18n/texte.json).", "",
         f"const QUELLE_SHA := {gd_str(sha)}", f"const VERSION := {gd_str(bau['version'])}", f"const MASSE := {gd_str(de(bau['masse']))}",
         "# Materialliste: id -> [Menge, Bezeichnung, Teilenummer, Gruppe]", "const BOM := {"]
    for b in bau["bom"]:
        for k in (b["nr"], b["menge"]):                   # part numbers and quantities: the same in every language
            if any(ch.isalpha() for ch in k):
                pairs[k] = {Lg: k for Lg in LANGS[1:]}
        L.append(f"\t{gd_str(b['id'])}: [{gd_str(b['menge'])}, {gd_str(de(b['name']))}, {gd_str(b['nr'])}, {gd_str(de(bau['bom_gruppen'][b['gruppe']]))}],")
    L += ["}", "# Teile: [id, Art (druck | teil | kabel | v52), Name, Materialliste-id, Montageschritt (0 = keiner), Druckdatei]", "const TEILE := ["]
    for t in bau["teile"]:
        if t.get("datei"):
            pairs[t["datei"]] = {Lg: t["datei"] for Lg in LANGS[1:]}
        nm = de(t["name"]) if t.get("name") else tx(bom[t["bom"]]["name"], "de")
        L.append(f"\t[{gd_str(t['id'])}, {gd_str(t['art'])}, {gd_str(nm)}, {gd_str(t.get('bom') or '')}, {int(t.get('schritt') or 0)}, {gd_str(t.get('datei', ''))}],")
    L += ["]", "# Montage v5.1: [Titel, Text]", "const SCHRITTE := ["]
    for s in bau["schritte"]:
        L.append(f"\t[{gd_str(de(s['titel']))}, {gd_str(de(s['text']))}],")
    L.append("]")
    keep_old = set()
    for k, v in (bau.get("ui_sim") or {}).items():        # texts of werkstatt.gd / mehr.gd (an existing translation stays)
        pairs[k] = {Lg: v.get(Lg, k) for Lg in LANGS[1:]}
        keep_old.add(k)
    with open(GD_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    # texte.json: Übersetzungen eintragen (das Format schreibt werkzeuge/sim_texte.py; hier nur Werte setzen)
    with open(TEXTE, encoding="utf-8") as fh:
        T = json.load(fh)
    n = 0
    for k, row in pairs.items():
        old = T.get(k) or {}
        new = {Lg: (old.get(Lg) if k in keep_old and old.get(Lg) else row.get(Lg)) or old.get(Lg, "") for Lg in LANGS[1:]}
        if old.get("?"):
            new["?"] = old["?"]
        if old != new:
            T[k] = new
            n += 1
    with open(TEXTE, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(T, ensure_ascii=False, indent=1) + "\n")
    subprocess.run([sys.executable, os.path.join(HIER, "sim_texte.py")], check=True, stdout=subprocess.DEVNULL)   # sortiert, Bericht
    # MoveEye: die Daten (alle Sprachen) und die Texte der Seite /case (englischer Schlüssel -> de / fr / it / rm)
    mw = {"version": bau["version"], "stand": bau["stand"], "masse": bau["masse"], "bom_gruppen": bau["bom_gruppen"],
          "bom": bau["bom"], "teile": [{k: t[k] for k in ("id", "art", "bom", "schritt", "name", "datei") if k in t} for t in bau["teile"]],
          "schritte": bau["schritte"], "druckdateien": bau.get("druckdateien", []), "github": bau.get("github", "")}
    ui = bau.get("ui_mw") or {}
    js = json.dumps(mw, ensure_ascii=False, separators=(",", ":"))
    assert '"""' not in js and not js.endswith("\\")
    body = ['#@ MoveEye – Teil 639v: Daten Gehäuse v5.1 (Teile, Materialliste, Montage in 5 Sprachen) für die Seite «Gehäuse & Bau» (639w). '
            'Erzeugt von werkzeuge/gehaeuse_bauen.py aus hardware/gehaeuse/bau.json – NICHT VON HAND ÄNDERN. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.',
            "# ----------------------------------------------------------------------------",
            "# GEH_QUELLE_SHA: Prüfsumme der Quelle (hardware/gehaeuse/Quellcode/*.py, bau.json, werkzeuge/gehaeuse_bauen.py) – der",
            "# Selbsttest (639w) vergleicht sie im Repository mit der Quelle und mit simulator3d/inhalte/gehaeuse/modelle.json.",
            "# ----------------------------------------------------------------------------",
            f"GEH_QUELLE_SHA = {sha!r}",
            f'GEH_BAU = json.loads(r"""{js}""")',
            "GEH_UI_DE = " + json.dumps({k: v["de"] for k, v in ui.items()}, ensure_ascii=False),
            "GEH_UI_TRX = " + json.dumps({Lg: {k: v[Lg] for k, v in ui.items()} for Lg in ("fr", "it", "rm")}, ensure_ascii=False), ""]
    with open(MW_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(body))
    print(f"Texte: {len(pairs)} (davon {n} in texte.json neu/geändert) -> werkstatt_daten.gd, texte.json, quelle/639v_daten_gehaeuse.py")


# ---- Prüfen --------------------------------------------------------------------------------------------------------------
def pruefen():
    probs = []
    sha = quelle_sha()
    mp = os.path.join(SIMDIR, "modelle.json")
    if not os.path.exists(mp):
        probs.append("simulator3d/inhalte/gehaeuse/modelle.json fehlt – gehaeuse_bauen.py --sim")
    else:
        with open(mp, encoding="utf-8") as fh:
            man = json.load(fh)
        if man.get("quelle_sha256") != sha:
            probs.append("Simulator-Modelle passen nicht zur Quelle (Prüfsumme) – gehaeuse_bauen.py --sim")
        for fn, h in (man.get("dateien") or {}).items():
            p = os.path.join(SIMDIR, fn)
            if not os.path.exists(p) or sha_datei(p) != h:
                probs.append(f"{fn}: fehlt oder verändert")
            if not os.path.exists(p + ".import"):
                probs.append(f"{fn}.import fehlt (importer keep)")
    for p, needle in ((GD_OUT, f'const QUELLE_SHA := "{sha}"'), (MW_OUT, f"GEH_QUELLE_SHA = {sha!r}")):
        if not os.path.exists(p) or needle not in open(p, encoding="utf-8").read():
            probs.append(os.path.relpath(p, REPO) + " ist nicht aktuell – gehaeuse_bauen.py --texte")
    for p in glob.glob(os.path.join(GEH, "Druckdateien", "*.3mf")):
        try:
            with zipfile.ZipFile(p) as z:
                assert "3D/3dmodel.model" in z.namelist()
        except Exception:
            probs.append(os.path.basename(p) + ": kein gültiges 3MF")
    for p in probs:
        print("FEHLER:", p)
    if not probs:
        print("Gehäuse: Simulator-Modelle und Daten passen zur Quelle (" + sha[:12] + ")")
    return not probs


# ---- Druckdateien und Bilder (langsam: ruft Daniels Skripte in einem Arbeitsordner auf) ------------------------------------
def arbeitsordner():
    w = tempfile.mkdtemp(prefix="gehaeuse_")
    for p in glob.glob(os.path.join(QUELL, "*.py")):
        shutil.copy(p, w)
    os.makedirs(os.path.join(w, "out51"), exist_ok=True)
    return w


def baue_druck(ziel, teile_sel):
    w = arbeitsordner()
    print("Arbeitsordner:", w, flush=True)
    subprocess.run([sys.executable, "export5.py"] + teile_sel, cwd=w, check=True)
    if teile_sel:
        print("nur einzelne Teile gebaut – keine Platten (3MF); STL in", os.path.join(w, "out51"))
        return
    subprocess.run([sys.executable, "plates5.py"], cwd=w, check=True)
    dd = os.path.join(GEH, "Druckdateien")
    for p in glob.glob(os.path.join(w, "out51", "*.3mf")):
        shutil.copy(p, dd)
    os.makedirs(ziel, exist_ok=True)
    zp = os.path.join(ziel, "MoveEye_Gehaeuse_v5-1_STL.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(glob.glob(os.path.join(w, "out51", "*.stl"))):
            z.write(p, "Druckdateien_v5-1/" + os.path.basename(p))
    print("3MF ->", dd, "  STL ->", zp)


def baue_bilder():
    w = arbeitsordner()
    subprocess.run([sys.executable, "prev51.py"], cwd=w, check=True)
    for k in ("a", "b", "c"):
        shutil.copy(os.path.join(w, f"v51_{k}.png"), os.path.join(GEH, "Bilder", f"Vorschau_v5-1_{k}.png"))
    print("Bilder ->", os.path.join(GEH, "Bilder"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sim", action="store_true", help="Simulator-Modelle + Texte")
    ap.add_argument("--texte", action="store_true", help="nur Texte und Daten")
    ap.add_argument("--druck", nargs="*", metavar="NR", help="STL + 3MF neu (optional nur Teile, z. B. 06 07)")
    ap.add_argument("--ziel", default="/tmp/gehaeuse_dist", help="Ordner für das STL-ZIP")
    ap.add_argument("--bilder", action="store_true", help="Vorschaubilder neu")
    ap.add_argument("--pruefen", action="store_true", help="passt alles zur Quelle?")
    a = ap.parse_args()
    if a.sim:
        baue_sim()
    if a.sim or a.texte:
        baue_texte()
        if a.sim:                                        # die Prüfsumme der Modelle zeigt auf dieselbe Quelle wie die Texte
            pass
    if a.druck is not None:
        baue_druck(a.ziel, a.druck)
    if a.bilder:
        baue_bilder()
    if a.pruefen or not (a.sim or a.texte or a.druck is not None or a.bilder):
        return 0 if pruefen() else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
