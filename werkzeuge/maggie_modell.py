#!/usr/bin/env python3
"""Maggie (Jack Russell) aus dem freien Hundemodell «ShibaInu» von Quaternius bauen (Simulator, Grafik ab «mittel»).

Quelle: Quaternius «Ultimate Animated Animals» (Juli 2021), Datei glTF/ShibaInu.gltf, Lizenz CC0 1.0
(gemeinfrei, https://creativecommons.org/publicdomain/zero/1.0/), https://quaternius.com.
SHA-256 der benutzten Datei: 3236979b94a840eb72d9ce091b1361da327a96f5ce068e666680297480f30f6b

Was das Werkzeug macht (alles fest im Code, keine Handarbeit in Blender):
  1. Proportionen auf Jack Russell: Rumpf und Hals schmaler, Kopf schmaler mit längerer Schnauze, Beine länger und
     schlanker (hochbeinig wie Maggie), kleinere Ohren als Kippohren (Spitze nach vorne gefaltet), Schwanz weniger
     eingerollt. Die Knochen bekommen die neue Ruhelage, das Netz wird mit den Gewichten verformt (kein Scheren).
  2. Glatter: Punkte zusammenführen, eine Unterteilung (jedes Dreieck in vier), leicht geglättet (Taubin), weiche Normalen.
  3. Maggies Muster als Vertex-Farben (weiss mit brauner Rücken-/Flankenplatte und Kruppe, Kopf und Hals braun mit schmaler
     Blesse, weisse Schnauze, Schwanz aussen braun mit weisser Spitze). Die Ruhelage jedes Punkts steht in UV/UV2
     (für die Fellstruktur im Shader, sie wandert dann nicht mit der Bewegung).
  4. Ohne Animationen (Maggie bewegt sich mit der Logik von actor.gd / anim_tier.gd, maggie_rig.gd überträgt sie auf
     die Knochen). Ausgabe: simulator3d/modelle/maggie_hund_glb.bin (ein GLB; die Endung .bin, damit Godot es nicht
     importiert und es roh in den Export kommt – geladen mit GLTFDocument.append_from_buffer).

Aufruf: python3 werkzeuge/maggie_modell.py PFAD/ShibaInu.gltf [AUSGABE]
"""
import base64
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

SHA = "3236979b94a840eb72d9ce091b1361da327a96f5ce068e666680297480f30f6b"
OUT = Path(__file__).resolve().parent.parent / "simulator3d" / "modelle" / "maggie_hund_glb.bin"

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


# ---- glTF lesen ------------------------------------------------------------------------------------------------------
def lesen(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        print("Achtung: andere Datei als die geprüfte (SHA-256 stimmt nicht)")
    d = json.loads(raw)
    buf = base64.b64decode(d["buffers"][0]["uri"].split(",", 1)[1])

    def acc(i):
        a = d["accessors"][i]
        bv = d["bufferViews"][a["bufferView"]]
        n = NC[a["type"]]
        dt = np.dtype(CT[a["componentType"]])
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", 0)
        if stride and stride != n * dt.itemsize:
            rows = [np.frombuffer(buf, dt, n, off + k * stride) for k in range(a["count"])]
            arr = np.array(rows)
        else:
            arr = np.frombuffer(buf, dt, a["count"] * n, off).reshape(a["count"], n) if n > 1 else \
                np.frombuffer(buf, dt, a["count"], off)
        if a.get("normalized") and dt != np.float32:
            arr = arr.astype(np.float64) / np.iinfo(dt).max
        return np.array(arr)
    return d, acc


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def mat_quat(m):
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    i = int(np.argmax([m[0, 0], m[1, 1], m[2, 2]]))
    if i == 0:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        return [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    if i == 1:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        return [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
    return [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]


def achse(ax, ang):
    ax = np.asarray(ax, float)
    ax = ax / np.linalg.norm(ax)
    x, y, z = ax
    c, s = math.cos(ang), math.sin(ang)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


# ---- Proportionen: Skalierung (im Knochen-Raum: y = entlang des Knochens) und Drehung (lokal, Grad um x/z) ------------
# x = seitlich, z = «Tiefe» des Knochens. Werte aus Daniels Fotos (Seitenansicht: Schulterhöhe ≈ Rumpflänge, schlank).
FORM = {
    "Body": {"s": (0.84, 1.0, 0.92)},
    "Back": {"s": (0.82, 0.9, 0.92)},
    "Torso": {"s": (0.8, 0.86, 0.94)},
    "Torso2": {"s": (0.82, 0.86, 0.96)},
    "Torso3": {"s": (0.82, 1.0, 0.92)},
    "Neck1": {"s": (0.8, 0.78, 0.84)},
    "Neck2": {"s": (0.8, 0.78, 0.84)},
    "Neck3": {"s": (0.78, 1.0, 0.86)},
    "Head": {"s": (1.04, 1.18, 1.06)},
    "Ear1.L": {"s": (0.8, 0.8, 0.8)}, "Ear1.R": {"s": (0.8, 0.8, 0.8)},
    "FrontShoulder.L": {"s": (1.0, 0.85, 1.0)}, "FrontShoulder.R": {"s": (1.0, 0.85, 1.0)},
    "FrontUpperLeg.L": {"s": (0.8, 1.03, 0.8)}, "FrontUpperLeg.R": {"s": (0.8, 1.03, 0.8)},
    "FrontLowerLeg.L": {"s": (0.78, 1.05, 0.78)}, "FrontLowerLeg.R": {"s": (0.78, 1.05, 0.78)},
    "BackShoulder.L": {"s": (1.0, 0.82, 1.0)}, "BackShoulder.R": {"s": (1.0, 0.82, 1.0)},
    "BackLeg.L": {"s": (0.78, 1.04, 0.8)}, "BackLeg.R": {"s": (0.78, 1.04, 0.8)},
    "BackUpperLeg.L": {"s": (0.8, 1.03, 0.8)}, "BackUpperLeg.R": {"s": (0.8, 1.03, 0.8)},
    "BackLowerLeg.L": {"s": (0.78, 1.05, 0.78)}, "BackLowerLeg.R": {"s": (0.78, 1.05, 0.78)},
    "Tail1": {"s": (0.82, 1.0, 0.82)},
    "Tail2": {"s": (0.8, 1.05, 0.8)},
    "Tail3": {"s": (0.78, 1.0, 0.78)},
}
# Kippohr: der Lappen klappt ab etwa einem Drittel nach vorne / unten (Richtung äusserer Augenwinkel), Grad
OHR = {"Ear2": 55.0, "Ear3": 40.0}
OHR_ZIEL = (0.35, -0.75, 0.55)                 # wohin die Spitze zeigt (linkes Ohr; rechts gespiegelt)


def ohr_drehung(name, R_global):
    """die Falte des Kippohrs als Drehung in Modell-Koordinaten: der Knochen dreht von seiner Richtung zum Ziel hin"""
    for k, deg in OHR.items():
        if name.startswith(k) and deg:
            side = 1.0 if name.endswith(".L") else -1.0
            yv = R_global[:, 1]
            ziel = np.array([OHR_ZIEL[0] * side, OHR_ZIEL[1], OHR_ZIEL[2]])
            ax = np.cross(yv, ziel)
            if np.linalg.norm(ax) < 1e-6:
                return np.eye(3)
            return achse(ax, math.radians(deg))
    return np.eye(3)


SCHWANZ = {"Tail1": 32.0, "Tail2": -18.0, "Tail3": -38.0}      # Grad um die Querachse (Modell-x): + = weniger eingerollt


def main():
    src = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    d, acc = lesen(src)
    nodes = d["nodes"]
    skin = d["skins"][0]
    joints = skin["joints"]
    ibm = acc(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)   # column-major
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    # ruhende globale Lage jedes Gelenks (aus den Bind-Matrizen = genau die Lage, an der die Haut hängt)
    G = {}
    for j, ni in enumerate(joints):
        G[ni] = np.linalg.inv(ibm[j])
    name = {ni: nodes[ni].get("name", str(ni)) for ni in joints}
    # die Pfoten hängen im Original an freien IK-Knochen: an den Unterlauf hängen, damit sie mit dem Bein gehen
    by = {v: k for k, v in name.items()}
    for s_ in ("L", "R"):
        parent[by["IKFrontLeg." + s_]] = by["FrontLowerLeg." + s_]
        parent[by["IKBackLeg." + s_]] = by["BackLowerLeg." + s_]

    # ---- neue Ruhelage: Drehung pflanzt sich fort, die Skalierung eines Knochens verlängert nur ihn selbst --------------
    order = []
    seen = set()

    def visit(ni):
        if ni in seen:
            return
        p = parent.get(ni)
        if p in G:
            visit(p)
        seen.add(ni)
        order.append(ni)
    for ni in joints:
        visit(ni)
    Rn, Pn, M = {}, {}, {}
    for ni in order:
        R0 = G[ni][:3, :3] / np.linalg.norm(G[ni][:3, :3], axis=0)
        p0 = G[ni][:3, 3]
        f = FORM.get(name[ni], {})
        S = np.diag(f.get("s", (1.0, 1.0, 1.0)))
        par = parent.get(ni)
        if par in G:
            Rp0 = G[par][:3, :3] / np.linalg.norm(G[par][:3, :3], axis=0)
            Sp = np.diag(FORM.get(name[par], {}).get("s", (1.0, 1.0, 1.0)))
            dR = Rn[par] @ Rp0.T                            # Drehung, die der Vater schon bekommen hat
            Rcur = dR @ R0
            Pnew = Pn[par] + Rn[par] @ Sp @ Rp0.T @ (p0 - G[par][:3, 3])
        else:
            Rcur = R0
            Pnew = p0.copy()
        Rcur = ohr_drehung(name[ni], Rcur) @ Rcur
        base = name[ni].split(".")[0]
        if base in SCHWANZ and SCHWANZ[base]:
            Rcur = achse((1, 0, 0), math.radians(SCHWANZ[base])) @ Rcur
        Rn[ni] = Rcur
        Pn[ni] = Pnew
        A = np.eye(4)
        A[:3, :3] = Rcur @ S @ R0.T
        A[:3, 3] = Pnew - A[:3, :3] @ p0
        M[ni] = A                                           # Ruhe alt -> Ruhe neu (für die Haut)

    # ---- Netz: alle Teile lesen ----------------------------------------------------------------------------------------
    prims = d["meshes"][0]["primitives"]
    teile = []
    for p in prims:
        at = p["attributes"]
        teile.append({"pos": acc(at["POSITION"]).astype(np.float64), "nrm": acc(at["NORMAL"]).astype(np.float64),
                      "jo": acc(at["JOINTS_0"]).astype(np.int64), "w": acc(at["WEIGHTS_0"]).astype(np.float64),
                      "idx": acc(p["indices"]).astype(np.int64).reshape(-1, 3), "mat": p.get("material", 0)})
    mname = [m["name"] for m in d["materials"]]
    # Gruppen: Fell (Main + Main_Light), Nase (Black), Augen (Eyes_*)
    gruppen = {"fell": [], "nase": [], "augen": []}
    for t in teile:
        n = mname[t["mat"]]
        gruppen["fell" if n.startswith("Main") else ("nase" if n == "Black" else "augen")].append(t)
    jname = [name[ni] for ni in joints]

    def zusammen(ts, weld=True):
        pos = np.concatenate([t["pos"] for t in ts])
        nrm = np.concatenate([t["nrm"] for t in ts])
        jo = np.concatenate([t["jo"] for t in ts])
        w = np.concatenate([t["w"] for t in ts])
        col = np.concatenate([np.tile(np.array(d["materials"][t["mat"]]["pbrMetallicRoughness"]["baseColorFactor"]),
                                      (len(t["pos"]), 1)) for t in ts])
        idx, off = [], 0
        for t in ts:
            idx.append(t["idx"] + off)
            off += len(t["pos"])
        idx = np.concatenate(idx)
        if weld:
            key = np.round(pos / 1e-4).astype(np.int64)
            _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
            inv = inv.reshape(-1)
            pos, jo, w, col = pos[first], jo[first], w[first], col[first]
            idx = inv[idx]
            idx = idx[(idx[:, 0] != idx[:, 1]) & (idx[:, 1] != idx[:, 2]) & (idx[:, 0] != idx[:, 2])]
            nrm = None
        return {"pos": pos, "nrm": nrm, "jo": jo, "w": w, "col": col, "idx": idx}

    def unterteilen(m):
        pos, jo, w, col, idx = m["pos"], m["jo"], m["w"], m["col"], m["idx"]
        nj = len(joints)
        W = np.zeros((len(pos), nj))
        for k in range(4):
            np.add.at(W, (np.arange(len(pos)), jo[:, k]), w[:, k])
        edges = {}
        newp, newW, newc = [pos], [W], [col]
        n0 = len(pos)
        cnt = 0
        tris = []
        mids = []
        for a, b, c in idx:
            ms = []
            for u, v in ((a, b), (b, c), (c, a)):
                k = (min(u, v), max(u, v))
                if k not in edges:
                    edges[k] = n0 + cnt
                    cnt += 1
                    mids.append(k)
                ms.append(edges[k])
            ab, bc, ca = ms
            tris += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        mids = np.array(mids)
        pos2 = np.concatenate([pos, (pos[mids[:, 0]] + pos[mids[:, 1]]) * 0.5])
        W2 = np.concatenate([W, (W[mids[:, 0]] + W[mids[:, 1]]) * 0.5])
        col2 = np.concatenate([col, (col[mids[:, 0]] + col[mids[:, 1]]) * 0.5])
        return {"pos": pos2, "W": W2, "col": col2, "idx": np.array(tris)}

    def glaetten(pos, idx, fest, it=3):
        n = len(pos)
        nb = [set() for _ in range(n)]
        for a, b, c in idx:
            nb[a] |= {b, c}
            nb[b] |= {a, c}
            nb[c] |= {a, b}
        nbl = [np.array(sorted(s)) for s in nb]
        p = pos.copy()
        for _ in range(it):
            for lam in (0.5, -0.53):
                avg = np.array([p[l].mean(axis=0) if len(l) else p[i] for i, l in enumerate(nbl)])
                step = (avg - p) * lam
                step[fest] = 0.0
                p = p + step
        return p

    def normalen(pos, idx):
        fn = np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]])
        nr = np.zeros_like(pos)
        for k in range(3):
            np.add.at(nr, idx[:, k], fn)
        ln = np.linalg.norm(nr, axis=1, keepdims=True)
        return nr / np.maximum(ln, 1e-12)

    def jidx(nm):
        return jname.index(nm)

    # ---- Fell ----------------------------------------------------------------------------------------------------------
    fell = unterteilen(zusammen(gruppen["fell"]))
    W = fell["W"]
    ohr = W[:, [jidx(n) for n in jname if n.startswith("Ear")]].sum(axis=1)
    fest = ohr > 0.3                                       # die dünnen Ohren nicht glätten (sie würden schrumpfen)
    fell["pos"] = glaetten(fell["pos"], fell["idx"], fest)

    # ---- Maggies Muster (in der alten Ruhelage, Koordinaten des Modells: vorne = +z, oben = +y) -----------------------
    WEISS = np.array([0.9, 0.885, 0.85])
    BRAUN = np.array([0.6, 0.4, 0.24])                   # Platte / Kruppe (Foto Seitenansicht, Sonne)
    KOPF = np.array([0.68, 0.48, 0.3])                    # Kopf, Hals, Ohren etwas heller
    OHRB = np.array([0.56, 0.36, 0.22])
    SCHNAUZE = np.array([0.86, 0.84, 0.8])
    rng = np.random.default_rng(345)

    def noise3(p, f):
        # glatte Pseudo-Rauschfunktion aus Sinuswellen (reproduzierbar, ohne Bibliothek)
        v = np.zeros(len(p))
        for k in range(5):
            dvec = rng.normal(size=3)
            dvec /= np.linalg.norm(dvec)
            v += np.sin(p @ dvec * f * (1.0 + 0.6 * k) + rng.uniform(0, 6.28)) / (1.0 + k)
        return v / 2.3

    def sst(a, b, x):
        t = np.clip((x - a) / (b - a), 0.0, 1.0)
        return t * t * (3 - 2 * t)

    P = fell["pos"].copy()                                 # Lage vor dem Verformen (alte Ruhelage, geglättet)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    nz = noise3(P, 6.0)
    kopfw = W[:, [jidx(n) for n in ("Head", "Neck3")]].sum(axis=1) + ohr
    halsw = W[:, [jidx(n) for n in ("Neck1", "Neck2")]].sum(axis=1)
    schw = W[:, [jidx(n) for n in ("Tail1", "Tail2", "Tail3")]].sum(axis=1)
    beinw = W[:, [jidx(n) for n in jname if "Leg" in n and "IK" not in n]].sum(axis=1)
    # 1) Rumpf: Platte über Rücken und Flanke (Ellipse in der Seitenansicht), Kruppe, oben verbunden
    platte = ((z + 0.08) / 0.62) ** 2 + ((y - 2.02) / 0.5) ** 2
    kruppe = ((z + 0.98) / 0.5) ** 2 + ((y - 1.72) / 0.72) ** 2
    oben = sst(1.86, 1.96, y) * sst(-1.0, -0.85, z) * (1 - sst(0.35, 0.5, z))
    braun_rumpf = np.maximum(np.maximum(1 - sst(0.8, 1.05, platte + 0.18 * nz), 1 - sst(0.8, 1.05, kruppe + 0.15 * nz)), oben)
    tupfen = 1 - sst(0.6, 1.0, ((x - 0.06) / 0.11) ** 2 + ((z + 0.25) / 0.14) ** 2)   # weisser Tupfen auf dem Rücken
    braun_rumpf = braun_rumpf * (1 - tupfen * sst(1.9, 2.0, y))
    # 2) Kopf und Hals braun; Kehle und Brust weiss (Linie vom Kinn schräg zur Brust)
    hals_d = (z - 1.3) * 0.85 - (y - 1.95) * 0.52           # > 0: vorne / unten am Hals
    braun_hals = (1 - sst(0.18, 0.3, hals_d + 0.04 * nz)) * sst(1.0, 1.25, z) * sst(1.85, 2.05, y + 0.25 * (z - 1.0))
    braun_kopf = np.clip(kopfw * 1.5, 0, 1)
    # weisse Schnauze (vorne, unten) und Kinn; Blesse schmal von der Stirn zur Schnauze
    schnauze = sst(2.12, 2.3, z + 0.03 * nz) * np.maximum(1 - sst(2.6, 2.7, y), sst(2.32, 2.42, z))
    kinn = sst(1.9, 2.05, z) * (1 - sst(2.42, 2.55, y))
    blesse = (1 - sst(0.02, 0.045, ax)) * sst(1.92, 2.0, z) * sst(2.72, 2.8, y)
    weiss_kopf = np.clip(schnauze + kinn + blesse, 0, 1)
    braun = np.maximum(braun_rumpf * (1 - np.clip(beinw * 1.2, 0, 1) * sst(1.25, 1.05, y)), braun_hals)
    braun = np.maximum(braun, braun_kopf * (1 - weiss_kopf))
    braun = np.maximum(braun, np.clip(halsw * 1.2, 0, 1) * (1 - sst(0.12, 0.26, hals_d)))
    # 3) Schwanz: aussen braun, Spitze weiss
    td = np.linalg.norm(P - G[joints[jidx("Tail1")]][:3, 3], axis=1)
    tl = td[schw > 0.5].max() if (schw > 0.5).any() else 1.0
    braun = np.where(schw > 0.5, 1 - sst(0.62, 0.74, td / tl + 0.03 * nz), braun)
    braun = np.clip(braun, 0, 1)[:, None]
    farbe_b = np.where(kopfw[:, None] + halsw[:, None] > 0.4, KOPF, BRAUN)
    farbe_b = np.where(ohr[:, None] > 0.5, OHRB, farbe_b)
    farbe_w = np.where((schnauze[:, None] > 0.5) & (kopfw[:, None] > 0.3), SCHNAUZE, WEISS)
    col = farbe_w * (1 - braun) + farbe_b * braun
    col *= (1.0 + 0.06 * nz)[:, None]                       # leichte Unruhe im Fell
    col = np.clip(col, 0, 1)
    fell["col"] = np.concatenate([col, np.ones((len(col), 1))], axis=1)
    fell["rest"] = P

    # ---- Nase und Augen: nur zusammenführen (weiche Normalen), Farben bleiben ------------------------------------------
    def einfach(ts):
        m = zusammen(ts)
        nj = len(joints)
        Wm = np.zeros((len(m["pos"]), nj))
        for k in range(4):
            np.add.at(Wm, (np.arange(len(m["pos"])), m["jo"][:, k]), m["w"][:, k])
        return {"pos": m["pos"], "W": Wm, "col": m["col"], "idx": m["idx"], "rest": m["pos"]}
    nase = einfach(gruppen["nase"])
    nase["col"][:] = [0.05, 0.045, 0.04, 1]
    augen = einfach(gruppen["augen"])
    hell = augen["col"][:, :3].mean(axis=1) > 0.3              # das Weisse im Auge: dunkelbraun wie bei Maggie
    augen["col"][hell, :3] = [0.16, 0.09, 0.05]

    # ---- verformen (Ruhe alt -> neu) -----------------------------------------------------------------------------------
    Ms = np.array([M[ni] for ni in joints])

    def verformen(m):
        Wm = m["W"]
        Wm = Wm / np.maximum(Wm.sum(axis=1, keepdims=True), 1e-9)
        ph = np.concatenate([m["pos"], np.ones((len(m["pos"]), 1))], axis=1)
        out = np.zeros_like(m["pos"])
        for j in np.nonzero(Wm.sum(axis=0) > 0)[0]:
            out += Wm[:, j:j + 1] * (ph @ Ms[j].T)[:, :3]
        m["pos"] = out
        m["W"] = Wm
        m["nrm"] = normalen(out, m["idx"])
        # vier stärkste Gewichte
        top = np.argsort(-Wm, axis=1)[:, :4]
        tw = np.take_along_axis(Wm, top, axis=1)
        tw = tw / np.maximum(tw.sum(axis=1, keepdims=True), 1e-9)
        m["jo"], m["w"] = top, tw
    for m in (fell, nase, augen):
        verformen(m)
    lo = min(fell["pos"][:, 1].min(), nase["pos"][:, 1].min())
    for m in (fell, nase, augen):
        m["pos"][:, 1] -= lo
    for ni in Pn:
        Pn[ni] = Pn[ni] - np.array([0.0, lo, 0.0])
    T2 = fell["W"][:, jidx("Torso2")] > 0.5
    print("Rücken (höchster Punkt am Torso2, für maggie_modell.gd RUECKEN): %.4f" % fell["pos"][T2, 1].max())
    print("Fell: %d Punkte, %d Dreiecke; Boden %.3f, Höhe %.3f, Länge %.3f" % (
        len(fell["pos"]), len(fell["idx"]), lo, fell["pos"][:, 1].max(), np.ptp(fell["pos"][:, 2])))

    # ---- neue Knoten (Ruhelage ohne Skalierung) ------------------------------------------------------------------------
    newG = {}
    for ni in joints:
        A = np.eye(4)
        A[:3, :3] = Rn[ni]
        A[:3, 3] = Pn[ni]
        newG[ni] = A
    onodes = []
    keep = [ni for ni in range(len(nodes)) if ni in G or nodes[ni].get("name") in ("AnimalArmature", "ShibaInu")]
    remap = {ni: k for k, ni in enumerate(keep)}
    for ni in keep:
        n = nodes[ni]
        o = {"name": n.get("name", "")}
        if n.get("name") == "ShibaInu":
            o["name"] = "Maggie"
            o["mesh"] = 0
            o["skin"] = 0
        if ni in G:
            par = parent.get(ni)
            L = np.linalg.inv(newG[par]) @ newG[ni] if par in G else newG[ni]
            o["translation"] = [float(v) for v in L[:3, 3]]
            o["rotation"] = [float(v) for v in mat_quat(L[:3, :3])]
        if n.get("name") == "AnimalArmature":
            ch = [remap[c] for c in keep if c != ni and parent.get(c) not in G]
        else:
            ch = [remap[c] for c in keep if parent.get(c) == ni]
        if ch:
            o["children"] = ch
        onodes.append(o)

    # ---- GLB schreiben -------------------------------------------------------------------------------------------------
    blob = bytearray()
    views, accs = [], []

    def add(arr, ctype, typ, target=None, norm=False, minmax=False):
        a = np.ascontiguousarray(arr)
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob.extend(a.tobytes())
        v = {"buffer": 0, "byteOffset": off, "byteLength": a.nbytes}
        if target:
            v["target"] = target
        views.append(v)
        ac = {"bufferView": len(views) - 1, "componentType": ctype, "count": int(a.shape[0]), "type": typ}
        if norm:
            ac["normalized"] = True
        if minmax:
            ac["min"] = [float(t) for t in a.min(axis=0)]
            ac["max"] = [float(t) for t in a.max(axis=0)]
        accs.append(ac)
        return len(accs) - 1
    oprims = []
    for k, m in enumerate((fell, nase, augen)):
        r = m["rest"]
        at = {"POSITION": add(m["pos"].astype(np.float32), 5126, "VEC3", 34962, minmax=True),
              "NORMAL": add(m["nrm"].astype(np.float32), 5126, "VEC3", 34962),
              "COLOR_0": add((np.clip(m["col"], 0, 1) * 255 + 0.5).astype(np.uint8), 5121, "VEC4", 34962, norm=True),
              "TEXCOORD_0": add(r[:, [0, 1]].astype(np.float32), 5126, "VEC2", 34962),
              "TEXCOORD_1": add(np.stack([r[:, 2], np.full(len(r), float(k))], axis=1).astype(np.float32), 5126, "VEC2", 34962),
              "JOINTS_0": add(m["jo"].astype(np.uint8), 5121, "VEC4", 34962),
              "WEIGHTS_0": add(m["w"].astype(np.float32), 5126, "VEC4", 34962)}
        ind = add(m["idx"].reshape(-1).astype(np.uint16 if len(m["pos"]) < 65535 else np.uint32),
                  5123 if len(m["pos"]) < 65535 else 5125, "SCALAR", 34963)
        oprims.append({"attributes": at, "indices": ind, "material": k})
    newibm = np.array([np.linalg.inv(newG[ni]).T.reshape(-1) for ni in joints], dtype=np.float32)
    ibm_acc = add(newibm, 5126, "MAT4")
    root = remap[[i for i, n in enumerate(nodes) if n.get("name") == "AnimalArmature"][0]]
    gl = {
        "asset": {"version": "2.0", "generator": "MoveEye werkzeuge/maggie_modell.py",
                  "copyright": "Modell: Quaternius «Ultimate Animated Animals» ShibaInu, CC0 1.0 (angepasst für MoveEye)"},
        "scene": 0, "scenes": [{"nodes": [root]}], "nodes": onodes,
        "meshes": [{"name": "Maggie", "primitives": oprims}],
        "materials": [{"name": "Fell", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 0.9}},
                      {"name": "Nase", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 0.35}},
                      {"name": "Augen", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 0.2}}],
        "skins": [{"name": "Maggie", "joints": [remap[ni] for ni in joints], "inverseBindMatrices": ibm_acc}],
        "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(blob)}],
    }
    js = json.dumps(gl, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    while len(blob) % 4:
        blob.append(0)
    glb = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob))
    glb += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(blob), 0x004E4942) + bytes(blob)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(glb)
    print("geschrieben:", out, len(glb), "Bytes")


if __name__ == "__main__":
    main()
