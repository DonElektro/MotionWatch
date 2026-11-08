#!/usr/bin/env python3
"""Tier-Modelle mit Skelett und Bewegungen für den Simulator («Flora und Fauna»; Paket 3 «Tiere echt»).

Quelle: Quaternius «Ultimate Animated Animals» (Juli 2021), Lizenz CC0 1.0 (gemeinfrei,
https://creativecommons.org/publicdomain/zero/1.0/), https://quaternius.com – dasselbe Paket wie Maggie. Bezogen aus der
öffentlichen GitHub-Kopie laoniutoushx/TD-demo-2024-04-03 («Asserts/Models/ulitimate animals/glTF/»): Fuchs am 07.11.2026,
Reh, Husky, Shiba, Wolf am 08.11.2026. SHA-256 der benutzten Dateien: siehe QUELLE unten (das Werkzeug prüft sie).

Arten (ART unten): fuchs (Fox), reh (Deer), hund_husky (Husky), hund_shiba (ShibaInu), wolf (Wolf), katze, igel (mit
Stacheln), dachs, hase (aus Fox umgeformt), wildschwein (aus Wolf umgeformt). Was das Werkzeug macht (alles im Code, keine Handarbeit in Blender):
  1. Umformen (Katze, Igel …): jeder Knochen bekommt eine Länge (Faktor auf seinen Abstand zum Vater) und eine Dicke
     (Skalierung im Raum des Knochens, nur für die Haut). Die Haut wird mit ihren Gewichten in die neue Ruhelage
     gebracht, die Bind-Matrizen neu gerechnet, die Verschiebungen der Bewegungen mit derselben Länge skaliert – die
     Drehungen der Bewegungen bleiben, darum laufen alle Bewegungen des Originals weiter. Vorher kann eine Form-Funktion
     die Punkte in der alten Ruhelage verschieben (z. B. kürzere Schnauze der Katze).
  2. Alle Teile werden EIN Netz (ein Zeichenaufruf) mit Vertex-Farben (Fell wie die echte Art, leichte Unruhe), weiche
     Normalen; Zusätze (Igel-Stacheln) hängen mit den Gewichten des nächsten Hautpunkts am Skelett.
  3. Vertex-Farbe Alpha = Fell (1) / fest (0: Augen, Nase, Hufe): der Shader kann das Fell umfärben (Farbschläge von
     Hund und Katze, Winterfell des Rehs) ohne zweites Netz. UV / UV2.x = Ruhelage (Fellstruktur klebt am Fell),
     UV2.y = Wärme-Klasse für das Wärmebild (0 Fell, 1 Auge, 2 Nase, 3 kühl: Stacheln, Hufe).
  4. Nur die Bewegungen, die der Simulator braucht, mit einheitlichen Namen (Walk, Gallop, Gallop_Jump, Idle, Idle_2,
     Idle_2_HeadLow, Eating); Spuren der IK-/Hilfsknochen weg, gleichbleibende Spuren als ein Schlüssel (kleinere Datei).
  5. Kennzahlen (Rückenhöhe, Augen, Länge) stehen im GLB unter scenes[0].extras.moveeye (tier_modell.gd liest sie).
Ausgabe: simulator3d/modelle/<datei>_glb.bin (GLB; Endung .bin, damit Godot es nicht importiert – geladen mit
GLTFDocument.append_from_buffer, wie Maggie).

Aufruf: python3 werkzeuge/tier_modelle.py ORDNER_MIT_DEN_GLTF [ART …]   (ohne ART: alle)
"""
import base64
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

MODELLE = Path(__file__).resolve().parent.parent / "simulator3d" / "modelle"
QUELLE = {
    "Fox.gltf": "2f36e3c9c75ecddda85c5f9944e98ee1e88e7c679a546534aff1cea8ecde64c7",
    "Deer.gltf": "b8afd0647e7a74332ce802c8326dfefe1a2b76da67ab925a631aaddb5ae9bdd4",
    "Husky.gltf": "0cfd85ddfcc5c07caf1bdeb296b21017b0da4c8558a92086daf4a172e0bf8d97",
    "ShibaInu.gltf": "3236979b94a840eb72d9ce091b1361da327a96f5ce068e666680297480f30f6b",
    "Wolf.gltf": "cc02e9d128b5715f352ee8bea086f97a35f1d875d240de99b0f9f2775c37d415",
}
ANIM_STD = ["Walk", "Gallop", "Gallop_Jump", "Idle", "Idle_2", "Idle_2_HeadLow", "Eating"]
ANIM_ALIAS = {"Idle_Headlow": "Idle_2_HeadLow"}

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


# ---- Hilfen --------------------------------------------------------------------------------------------------------
def lesen(path):
    raw = Path(path).read_bytes()
    sha = QUELLE.get(Path(path).name)
    if sha and hashlib.sha256(raw).hexdigest() != sha:
        print("Achtung: andere Datei als die geprüfte (SHA-256 stimmt nicht):", path)
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
            arr = np.array([np.frombuffer(buf, dt, n, off + k * stride) for k in range(a["count"])])
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


def trs(n):
    m = np.eye(4)
    r = quat_mat(n.get("rotation", [0, 0, 0, 1]))
    s = np.array(n.get("scale", [1, 1, 1]))
    m[:3, :3] = r * s
    m[:3, 3] = n.get("translation", [0, 0, 0])
    return m


def noise3(P, f, seed=0.0):
    """glattes Wertrauschen 0..1 (fest, ohne Zufall)"""
    q = P * f + seed
    i = np.floor(q)
    t = q - i
    t = t * t * (3 - 2 * t)

    def h(o):
        v = (i + o) @ np.array([127.1, 311.7, 74.7])
        return np.modf(np.abs(np.sin(v) * 43758.5453))[0]
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * (t[:, 2] if dz else 1 - t[:, 2])
                out = out + w * h(np.array([dx, dy, dz]))
    return out


def sst(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Tier:
    """das gelesene Modell: Netz (alle Teile), Skelett, Bewegungen; Hilfen für Gewichte nach Knochen-Namen"""

    def __init__(self, path):
        d, acc = lesen(path)
        self.d, self.acc = d, acc
        mats = [m["name"] for m in d["materials"]]
        P, J, W, M, I = [], [], [], [], []
        base = 0
        for pr in d["meshes"][0]["primitives"]:
            a = pr["attributes"]
            p = acc(a["POSITION"]).astype(np.float64)
            P.append(p)
            J.append(acc(a["JOINTS_0"]).astype(np.int64))
            W.append(acc(a["WEIGHTS_0"]).astype(np.float64))
            M.append(np.full(len(p), pr["material"]))
            I.append(acc(pr["indices"]).astype(np.int64) + base)
            base += len(p)
        self.P = np.concatenate(P)
        self.J = np.concatenate(J)
        self.W = np.concatenate(W)
        self.mat = np.array(mats)[np.concatenate(M)]
        self.I = np.concatenate(I).reshape(-1, 3)
        sk = d["skins"][0]
        self.joints = sk["joints"]
        self.jn = [d["nodes"][j]["name"] for j in self.joints]
        self.parent = {}
        for i, n in enumerate(d["nodes"]):
            for c in n.get("children", []):
                self.parent[c] = i
        self.ibm = acc(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        self.stachel_spitze = np.zeros(len(self.P))

    def wsum(self, names):
        idx = [self.jn.index(n) for n in names if n in self.jn]
        out = np.zeros(len(self.P))
        for k in range(4):
            out += np.where(np.isin(self.J[:, k], idx), self.W[:, k], 0.0)
        return out

    def wpre(self, prefix):
        return self.wsum([n for n in self.jn if n.startswith(prefix)])

    def gruppen(self):
        g = {}
        g["kopf"] = self.wsum(["Head"]) + self.wpre("Ear")
        g["hals"] = self.wsum(["Neck1", "Neck2", "Neck3"])
        g["ohr"] = self.wpre("Ear")
        g["schwanz"] = self.wpre("Tail")
        g["bein_u"] = self.wsum([n for n in self.jn if "LowerLeg" in n and not n.startswith("IK")])
        g["bein"] = self.wsum([n for n in self.jn if ("Leg" in n or "Shoulder" in n) and not n.startswith("IK")])
        g["rumpf"] = self.wsum(["Body", "Back", "Torso", "Torso2", "Torso3"])
        return g


# ---- Umformen ------------------------------------------------------------------------------------------------------
def umformen(t, laenge, dicke, vorform=None):
    """laenge: {Knochen: Faktor auf den Abstand zum Vater}; dicke: {Knochen: (sx, sy, sz) im Raum des Knochens};
    vorform(P, t) -> P (in der alten Ruhelage). Ändert t.P, die Knoten (Ruhelage), die Bind-Matrizen; gibt die
    Faktoren je Knoten für die Verschiebungen der Bewegungen zurück."""
    d = t.d
    nodes = d["nodes"]
    if vorform is not None:
        t.P = vorform(t.P.copy(), t)
    # die Pfoten hängen im Original an freien IK-Knochen (ihre Lage kommt aus den Bewegungen, im Raum des Rumpfs) - beim
    # Umformen passen diese Lagen nicht mehr: die Pfoten an den Unterlauf hängen (wie maggie_modell.py)
    for ik, ziel in (("IKFrontLeg", "FrontLowerLeg"), ("FF", "FrontLowerLeg"), ("IKBackLeg", "BackLowerLeg"), ("FFB", "BackLowerLeg")):
        for s_ in ("L", "R"):
            if ik + "." + s_ in t.jn and ziel + "." + s_ in t.jn:
                t.J[t.J == t.jn.index(ik + "." + s_)] = t.jn.index(ziel + "." + s_)

    def glob(ni, tab, loc):
        if ni in tab:
            return tab[ni]
        p = t.parent.get(ni)
        m = loc(ni) if p is None else glob(p, tab, loc) @ loc(ni)
        tab[ni] = m
        return m
    G = {}
    for ni in t.joints:
        glob(ni, G, lambda k: trs(nodes[k]))
    fac = {ni: float(laenge.get(nodes[ni]["name"], 1.0)) for ni in t.joints}

    def loc_new(k):
        m = trs(nodes[k])
        if k in fac:
            m[:3, 3] *= fac[k]
        return m
    Gn = {}
    for ni in t.joints:
        glob(ni, Gn, loc_new)
    W0 = G[t.joints[0]] @ t.ibm[0]                         # Netz -> Welt in der Bindung (bei Quaternius = Einheit)
    W0i = np.linalg.inv(W0)
    Ms = []
    for j, ni in enumerate(t.joints):
        S = np.eye(4)
        s = dicke.get(nodes[ni]["name"])
        if s is not None:
            S[:3, :3] = np.diag(s)
        Ms.append(W0i @ Gn[ni] @ S @ t.ibm[j])
    Ms = np.array(Ms)
    ph = np.concatenate([t.P, np.ones((len(t.P), 1))], axis=1)
    out = np.zeros_like(t.P)
    for k in range(4):
        out += t.W[:, k:k + 1] * np.einsum("nij,nj->ni", Ms[t.J[:, k]], ph)[:, :3]
    out /= np.maximum(t.W.sum(axis=1, keepdims=True), 1e-9)
    t.P = out
    for ni in t.joints:
        if fac[ni] != 1.0:
            tr = nodes[ni].get("translation", [0, 0, 0])
            nodes[ni]["translation"] = [float(v) * fac[ni] for v in tr]
    t.ibm = np.array([np.linalg.inv(Gn[ni]) @ W0 for ni in t.joints])
    return fac


def auf_boden(t):
    """das tiefste Hautstück auf y = 0 (der Wurzel-Knochen Body wird verschoben, mit ihm die Bewegungen)"""
    lo = float(t.P[:, 1].min())
    if abs(lo) < 1e-5:
        return 0.0
    t.P[:, 1] -= lo
    nodes = t.d["nodes"]
    body = t.joints[t.jn.index("Body")]
    tr = nodes[body].get("translation", [0, 0, 0])
    nodes[body]["translation"] = [tr[0], tr[1] - lo, tr[2]]
    T = np.eye(4)
    T[1, 3] = lo
    t.ibm = np.array([m @ T for m in t.ibm])
    return lo


# ---- Zusätze: Stacheln -----------------------------------------------------------------------------------------------
def stacheln(t, maske, n_ziel, laenge, dicke, seed=7):
    """kleine dreiseitige Kegel auf der Haut (wo maske > 0.5), nach hinten / oben geneigt; Gewichte vom Hautpunkt"""
    rng = np.random.default_rng(seed)
    nrm = normalen(t.P, t.I)
    tri = t.I[np.all(maske[t.I] > 0.5, axis=1)]
    a, b, c = t.P[tri[:, 0]], t.P[tri[:, 1]], t.P[tri[:, 2]]
    ar = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    pick = rng.choice(len(tri), size=n_ziel, p=ar / ar.sum())
    u = rng.random(n_ziel)
    v = rng.random(n_ziel)
    sw = u + v > 1
    u[sw], v[sw] = 1 - u[sw], 1 - v[sw]
    base = a[pick] + (b[pick] - a[pick]) * u[:, None] + (c[pick] - a[pick]) * v[:, None]
    near = tri[pick, 0]
    nn = nrm[tri[pick, 0]] + nrm[tri[pick, 1]] + nrm[tri[pick, 2]]
    nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    back = np.array([0.0, 0.25, -1.0])                     # Stacheln liegen nach hinten an
    dirv = nn * 0.3 + back * 0.85 + rng.normal(0, 0.12, (n_ziel, 3))
    dirv /= np.linalg.norm(dirv, axis=1, keepdims=True)
    L = laenge * rng.uniform(0.75, 1.15, n_ziel)
    newP, newI, src = [], [], []
    n0 = len(t.P)
    for k in range(n_ziel):
        dv = dirv[k]
        s1 = np.cross(dv, [0.0, 1.0, 0.0])
        if np.linalg.norm(s1) < 1e-3:
            s1 = np.cross(dv, [1.0, 0.0, 0.0])
        s1 /= np.linalg.norm(s1)
        s2 = np.cross(dv, s1)
        p0 = base[k] - dv * L[k] * 0.2                    # Fuss leicht in der Haut
        ring = [p0 + (s1 * math.cos(q) + s2 * math.sin(q)) * dicke for q in (0, 2 * math.pi / 3, 4 * math.pi / 3)]
        i0 = n0 + len(newP)
        newP += ring + [base[k] + dv * L[k]]
        for q in range(3):
            newI.append([i0 + q, i0 + (q + 1) % 3, i0 + 3])
        src += [near[k]] * 4
    src = np.array(src)
    t.P = np.concatenate([t.P, np.array(newP)])
    t.J = np.concatenate([t.J, t.J[src]])
    t.W = np.concatenate([t.W, t.W[src]])
    t.mat = np.concatenate([t.mat, np.array(["Stachel"] * len(newP))])
    t.I = np.concatenate([t.I, np.array(newI)])
    tip = np.zeros(len(t.P))
    tip[n0 + 3::4] = 1.0
    t.stachel_spitze = tip


def normalen(P, I, weld=True):
    if weld:
        key = np.round(P / 1e-4).astype(np.int64)
        _, inv = np.unique(key, axis=0, return_inverse=True)
        inv = inv.reshape(-1)
    else:
        inv = np.arange(len(P))
    fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
    acc_n = np.zeros((inv.max() + 1, 3))
    for k in range(3):
        np.add.at(acc_n, inv[I[:, k]], fn)
    N = acc_n[inv]
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


# ---- Farben je Art (linear) ----------------------------------------------------------------------------------------
def farbe_fuchs(t, g, P):
    ROST = np.array([0.50, 0.17, 0.045])
    RUECKEN = np.array([0.34, 0.10, 0.03])
    GELB = np.array([0.58, 0.30, 0.10])
    WEISS = np.array([0.72, 0.70, 0.64])
    SCHWARZ = np.array([0.025, 0.022, 0.02])
    head = t.wsum(["Head", "Neck3"])
    tail = g["schwanz"]
    nz = noise3(P, 3.0)
    y, z = P[:, 1], P[:, 2]
    yn = (y - y.min()) / np.ptp(y)
    col = np.zeros((len(P), 3))
    col[t.mat == "Main"] = ROST
    col[t.mat == "Main_Light"] = WEISS
    col[t.mat == "Black"] = SCHWARZ
    col[t.mat == "Eyes"] = [0.02, 0.015, 0.01]
    col[t.mat == "Grey"] = [0.03, 0.028, 0.026]
    fur = t.mat == "Main"
    top = sst(0.62, 0.8, yn) * (1 - head) * (1 - tail)
    flank = (1 - sst(0.45, 0.62, yn)) * (1 - tail)
    c2 = ROST * (1 - top[:, None]) + RUECKEN * top[:, None]
    c2 = c2 * (1 - 0.45 * flank[:, None]) + GELB * 0.45 * flank[:, None]
    c2 = np.where(head[:, None] > 0.5, ROST * 0.6 + GELB * 0.4, c2)
    zt = (z - z.min()) / max(1e-6, np.ptp(z))
    c2 = np.where(tail[:, None] > 0.5, c2 * (1 - 0.3 * sst(0.0, 0.25, 1 - zt))[:, None], c2)
    col[fur] = c2[fur]
    col *= (1.0 + 0.10 * (nz - 0.5))[:, None]
    klasse = np.zeros(len(P))
    klasse[t.mat == "Eyes"] = 1
    klasse[t.mat == "Black"] = 2                              # «Black» ist beim Fuchs die Nase, «Grey» Beine / Ohrrücken
    fell = np.isin(t.mat, ["Main", "Main_Light", "Grey"]).astype(float)
    return col, fell, klasse


def farbe_reh(t, g, P):
    """Reh im Sommerfell: rotbraun, Rücken etwas dunkler, Bauch / Beine innen heller gelbgrau; Spiegel (Hinterteil) hell,
    Kinn und Maulspitze weiss, Nasenspiegel schwarz, dunkles Band über der Schnauze, Ohren innen hell"""
    ROT = np.array([0.36, 0.14, 0.05])
    RUECK = np.array([0.24, 0.095, 0.04])
    BAUCH = np.array([0.42, 0.30, 0.19])
    SPIEGEL = np.array([0.62, 0.56, 0.46])
    WEISS = np.array([0.72, 0.70, 0.66])
    y, z = P[:, 1], P[:, 2]
    nz = noise3(P, 3.5)
    nz2 = noise3(P, 9.0, 3.3)
    col = np.tile(ROT, (len(P), 1))
    top = sst(0.2, 0.45, y - 2.55) * (1 - np.clip(g["kopf"], 0, 1)) * (1 - g["hals"] * 0.5)
    col = col * (1 - top[:, None]) + RUECK * top[:, None]
    light = t.mat == "Main_Light"
    col[light] = BAUCH * 0.8 + ROT * 0.2
    sp = (1 - sst(0.75, 1.0, ((z + 1.45) / 0.32) ** 2 + ((y - 2.55) / 0.42) ** 2 + (P[:, 0] / 0.45) ** 2)) * (1 - g["bein_u"])
    col = col * (1 - sp[:, None]) + SPIEGEL * sp[:, None]
    kopf = np.clip(g["kopf"], 0, 1) * (1 - np.clip(g["ohr"], 0, 1))
    col = np.where(kopf[:, None] > 0.4, col * 0.85 + np.array([0.06, 0.05, 0.04]), col)
    dark = t.mat == "Main_Dark"
    col[dark] = col[dark] * 0.75                            # um die Augen: Fell, nur etwas dunkler
    col[dark & (z > 2.55)] = [0.012, 0.01, 0.009]            # Nasenspiegel schwarz
    col[(kopf > 0.4) & (y < 3.78) & (z > 2.3)] = WEISS
    col[(g["ohr"] > 0.5) & light] = [0.55, 0.48, 0.40]
    col[t.mat == "Hooves"] = [0.035, 0.03, 0.028]
    col[t.mat == "Eye_Black"] = [0.02, 0.018, 0.016]
    col[t.mat == "Eye_Lighter"] = [0.05, 0.03, 0.02]
    col[t.mat == "Eye_White"] = [0.05, 0.04, 0.03]
    col *= (1.0 + 0.10 * (nz - 0.5) + 0.05 * (nz2 - 0.5))[:, None]
    klasse = np.zeros(len(P))
    klasse[np.isin(t.mat, ["Eye_Black", "Eye_Lighter", "Eye_White"])] = 1
    klasse[dark & (z > 2.55)] = 2
    klasse[t.mat == "Hooves"] = 3
    fell = np.isin(t.mat, ["Main", "Main_Light", "Main_Dark"]).astype(float)
    return col, fell, klasse


def farbe_husky(t, g, P):
    """Husky: Rücken / Kopf-Oberseite / Schwanz-Oberseite grau bis schwarzgrau, Maske, Bauch, Beine, Brust weiss"""
    DUNKEL = np.array([0.075, 0.075, 0.08])
    GRAU = np.array([0.20, 0.20, 0.21])
    WEISS = np.array([0.74, 0.73, 0.71])
    nz = noise3(P, 3.0)
    nz2 = noise3(P, 10.0, 5.1)
    dark = t.mat == "Material"
    col = np.tile(WEISS, (len(P), 1))
    k = sst(0.3, 0.75, nz + (P[:, 1] - 2.6) * 0.9)
    dc = GRAU * (1 - k[:, None]) + DUNKEL * k[:, None]
    col[dark] = dc[dark]
    col[t.mat == "Material.006"] = [0.02, 0.02, 0.02]       # Nase
    col[t.mat == "Material.002"] = [0.01, 0.01, 0.01]       # Pupille
    col[t.mat == "Material.003"] = [0.10, 0.17, 0.30]       # Iris (blau)
    col *= (1.0 + 0.10 * (nz - 0.5) + 0.06 * (nz2 - 0.5))[:, None]
    klasse = np.zeros(len(P))
    klasse[np.isin(t.mat, ["Material.002", "Material.003"])] = 1
    klasse[t.mat == "Material.006"] = 2
    fell = np.isin(t.mat, ["Material", "Material.001"]).astype(float)
    return col, fell, klasse


def farbe_shiba(t, g, P):
    """Shiba (rot): Rücken / Flanke rotgelb, Rücken dunkler; Kehle, Brust, Bauch, Beine innen, Wangen hell («Urajiro»)"""
    ROT = np.array([0.52, 0.22, 0.07])
    RUECK = np.array([0.38, 0.15, 0.05])
    HELL = np.array([0.80, 0.70, 0.55])
    nz = noise3(P, 3.0)
    nz2 = noise3(P, 9.0, 1.7)
    col = np.tile(HELL, (len(P), 1))
    m = t.mat == "Main"
    top = sst(0.35, 0.7, nz * 0.5 + (P[:, 1] - 2.3) * 1.2) * (1 - np.clip(g["kopf"], 0, 1))
    c2 = ROT * (1 - top[:, None]) + RUECK * top[:, None]
    col[m] = c2[m]
    col[t.mat == "Black"] = [0.02, 0.018, 0.016]
    col[t.mat == "Eyes_Black"] = [0.01, 0.01, 0.01]
    col[t.mat == "Eyes_White"] = [0.08, 0.05, 0.03]
    col[t.mat == "Eyes_Pupil"] = [0.02, 0.012, 0.008]
    col *= (1.0 + 0.10 * (nz - 0.5) + 0.06 * (nz2 - 0.5))[:, None]
    klasse = np.zeros(len(P))
    klasse[np.isin(t.mat, ["Eyes_Black", "Eyes_White", "Eyes_Pupil"])] = 1
    klasse[t.mat == "Black"] = 2
    fell = np.isin(t.mat, ["Main", "Main_Light"]).astype(float)
    return col, fell, klasse


def farbe_katze(t, g, P):
    """Getigerte Hauskatze (in Grautönen – die Farbschläge macht der Shader aus der Helligkeit): dunkle Querstreifen
    über Rumpf und Beine, Ringe am Schwanz, dunkle Rückenlinie, Kehle und Bauch heller, Nase rosa"""
    BASIS = np.array([0.30, 0.29, 0.27])
    STREIF = np.array([0.07, 0.068, 0.065])
    HELL = np.array([0.55, 0.54, 0.51])
    nz = noise3(P, 2.5)
    nz2 = noise3(P, 11.0, 2.2)
    y, z = P[:, 1], P[:, 2]
    col = np.tile(BASIS, (len(P), 1))
    ph = z * 5.2 + 1.6 * nz + 0.9 * np.abs(P[:, 0]) * (1 + 0.5 * nz2)
    beine = np.clip(g["bein"] * 1.3, 0, 1)
    ph = ph * (1 - beine) + (y * 7.0 + 1.2 * nz) * beine
    sch = g["schwanz"] > 0.5
    ph = np.where(sch, z * 8.0 + nz, ph)
    streif = sst(0.35, 0.8, np.sin(ph)) * (1 - 0.6 * sst(0.0, 0.3, -(y - 1.7)) * (1 - beine))
    rueck = sst(1.9, 2.2, y) * (1 - np.clip(g["kopf"], 0, 1)) * (1 - sch)
    streif = np.maximum(streif, rueck * 0.8)
    col = col * (1 - streif[:, None]) + STREIF * streif[:, None]
    light = t.mat == "Main_Light"
    col[light] = HELL * (1 - 0.35 * streif[light, None]) + STREIF * 0.35 * streif[light, None]
    col[sch & light] = col[sch & light] * 0.0 + BASIS * (1 - streif[sch & light, None]) + STREIF * streif[sch & light, None]
    if sch.any():
        col[sch & (P[:, 2] < P[sch, 2].min() + 0.25)] = STREIF   # Schwanzspitze dunkel (beim Fuchs weiss)
    col[t.mat == "Eyes"] = [0.02, 0.015, 0.01]
    col[t.mat == "Black"] = [0.42, 0.20, 0.20]               # rosa Nase («Grey» = Beine / Ohrrücken: Fell wie oben)
    col *= (1.0 + 0.08 * (nz - 0.5) + 0.06 * (nz2 - 0.5))[:, None]
    klasse = np.zeros(len(P))
    klasse[t.mat == "Eyes"] = 1
    klasse[t.mat == "Black"] = 2
    fell = np.isin(t.mat, ["Main", "Main_Light", "Grey"]).astype(float)
    return col, fell, klasse


def farbe_igel(t, g, P):
    """Braunbrust-Igel: Stacheln dunkelbraun mit heller Spitze, Gesicht und Bauch graubraun, Nase schwarz"""
    GESICHT = np.array([0.20, 0.15, 0.10])
    BAUCH = np.array([0.24, 0.19, 0.14])
    STB = np.array([0.10, 0.07, 0.045])
    STH = np.array([0.62, 0.58, 0.50])
    col = np.tile(GESICHT, (len(P), 1))
    col[t.mat == "Main_Light"] = BAUCH
    col[t.mat == "Grey"] = GESICHT * 0.75                     # Beine
    st = t.mat == "Stachel"
    nz = noise3(P, 13.0, 4.0)
    col[t.stachel_haut] = STB * 1.4 + (STH - STB) * 0.25 * noise3(P, 20.0, 1.0)[t.stachel_haut, None]   # Haut unter den Stacheln
    col[st] = STB
    col[t.stachel_spitze > 0.5] = STH
    col[t.mat == "Eyes"] = [0.01, 0.01, 0.01]
    col[t.mat == "Black"] = [0.015, 0.012, 0.01]
    col *= (1.0 + 0.16 * (nz - 0.5))[:, None]
    klasse = np.zeros(len(P))
    klasse[t.mat == "Eyes"] = 1
    klasse[t.mat == "Black"] = 2
    klasse[st] = 3
    return col, np.zeros(len(P)), klasse


# ---- Formen ----------------------------------------------------------------------------------------------------------
def katze_vorform(P, t):
    """in der Ruhelage des Fuchses: kürzere Schnauze, etwas höhere Stirn, breiterer Kopf"""
    head = t.wsum(["Head"])
    ear = t.wpre("Ear")
    cz, cy = 2.05, 2.12                                     # Kopf-Mitte des Fuchses (Augen bei z ≈ 2.2, y ≈ 2.15)
    dz = P[:, 2] - cz
    k = np.clip(head * 1.2, 0, 1)
    vor = np.where(dz > 0, dz * (1 - 0.6 * sst(0.0, 0.45, dz)), dz)
    P[:, 2] = P[:, 2] * (1 - k) + (cz + vor) * k
    dy = P[:, 1] - cy
    P[:, 1] = P[:, 1] + k * np.where(dy > 0, dy * 0.12, 0.0) * sst(0.1, -0.2, P[:, 2] - 2.35)
    P[:, 0] = P[:, 0] * (1 + 0.10 * k * (1 - ear))
    return P


KATZE_L = {"Neck1": 0.7, "Neck2": 0.7, "Neck3": 0.8, "Ear2.L": 0.62, "Ear3.L": 0.62, "Ear4.L": 0.5,
           "Ear2.R": 0.62, "Ear3.R": 0.62, "Ear4.R": 0.5,
           "FrontUpperLeg.L": 0.75, "FrontUpperLeg.R": 0.75, "BackUpperLeg.L": 0.72, "BackUpperLeg.R": 0.72,
           "FrontLowerLeg.L": 0.7, "FrontLowerLeg.R": 0.7, "BackLowerLeg.L": 0.7, "BackLowerLeg.R": 0.7,
           "Torso": 0.92, "Torso2": 0.92,
           "Tail2": 1.05, "Tail3": 1.1, "Tail4": 1.1, "Tail5": 1.1, "Tail6": 1.1, "Tail7": 1.15, "Tail8": 1.1}
KATZE_D = {"Ear1.L": (0.66, 0.66, 0.66), "Ear1.R": (0.66, 0.66, 0.66), "Ear2.L": (0.8, 0.7, 0.8), "Ear2.R": (0.8, 0.7, 0.8),
           "Ear3.L": (0.75, 0.7, 0.75), "Ear3.R": (0.75, 0.7, 0.75), "Ear4.L": (0.6, 0.6, 0.6), "Ear4.R": (0.6, 0.6, 0.6),
           "Back": (1.0, 1.08, 1.0), "Torso": (1.0, 1.1, 1.0), "Torso2": (0.98, 1.12, 1.0), "Torso3": (0.95, 1.05, 0.95),
           "Neck1": (0.95, 1.0, 1.0), "Neck2": (0.95, 1.0, 1.0), "Head": (1.05, 1.0, 1.0)}
for _k in range(1, 9):
    KATZE_D["Tail%d" % _k] = (0.33, 1.0, 0.33)                  # dünner Katzenschwanz statt Fuchslunte
for _s in ("L", "R"):
    KATZE_D["FrontUpperLeg." + _s] = (1.05, 0.75, 1.05)
    KATZE_D["BackUpperLeg." + _s] = (1.05, 0.72, 1.05)
    KATZE_D["FrontLowerLeg." + _s] = (1.0, 0.66, 1.0)
    KATZE_D["BackLowerLeg." + _s] = (1.0, 0.68, 1.0)


def igel_vorform(P, t):
    """Fuchs -> Igel (Ruhelage): kleiner Kopf mit spitzer, schmaler Schnauze"""
    head = np.clip(t.wsum(["Head"]) * 1.2, 0, 1)
    cz, cy = 2.05, 2.05
    dz = P[:, 2] - cz
    vor = sst(0.15, 0.6, dz) * head                          # Schnauze: schmaler und tiefer
    P[:, 0] = P[:, 0] * (1 - 0.35 * vor)
    P[:, 1] = P[:, 1] - 0.08 * vor
    return P


IGEL_L = {"Neck1": 0.35, "Neck2": 0.35, "Neck3": 0.4, "Ear2.L": 0.3, "Ear3.L": 0.3, "Ear4.L": 0.25,
          "Ear2.R": 0.3, "Ear3.R": 0.3, "Ear4.R": 0.25,
          "FrontUpperLeg.L": 0.4, "FrontUpperLeg.R": 0.4, "FrontLowerLeg.L": 0.3, "FrontLowerLeg.R": 0.3,
          "BackUpperLeg.L": 0.3, "BackUpperLeg.R": 0.3, "BackLowerLeg.L": 0.3, "BackLowerLeg.R": 0.3,
          "BackLeg.L": 0.5, "BackLeg.R": 0.5, "Torso": 0.75, "Torso2": 0.8, "Torso3": 0.65}
for _k in range(2, 9):
    IGEL_L["Tail%d" % _k] = 0.15
IGEL_D = {"Back": (1.75, 1.45, 1.4), "Torso": (1.85, 1.45, 1.6), "Torso2": (1.8, 1.4, 1.6), "Torso3": (1.45, 1.2, 1.3),
          "Body": (1.6, 1.3, 1.4), "Neck1": (1.3, 1.0, 1.2), "Neck2": (1.15, 1.0, 1.05), "Neck3": (0.95, 1.0, 0.95),
          "Head": (0.78, 0.78, 0.9)}
for _e in ("Ear1", "Ear2", "Ear3", "Ear4"):
    IGEL_D[_e + ".L"] = (0.28, 0.28, 0.28)
    IGEL_D[_e + ".R"] = (0.28, 0.28, 0.28)
for _k in range(1, 9):
    IGEL_D["Tail%d" % _k] = (0.15, 0.15, 0.15)
for _s in ("L", "R"):
    for _b, _v in (("FrontShoulder", (1.0, 0.55, 1.0)), ("FrontUpperLeg", (1.0, 0.45, 1.0)), ("FrontLowerLeg", (1.1, 0.28, 1.1)),
                   ("BackShoulder", (1.0, 0.55, 1.0)), ("BackLeg", (1.0, 0.55, 1.0)), ("BackUpperLeg", (1.0, 0.3, 1.0)),
                   ("BackLowerLeg", (1.1, 0.28, 1.1))):
        IGEL_D[_b + "." + _s] = _v


# ---- Paket 3, Schritt 2: Wolf, Dachs, Wildschwein, Hase ------------------------------------------------------------
def farbe_wolf(t, g, P):
    """Grauwolf (Mitteleuropa): graubraun mit dunklerem Sattel, Rücken und Schwanzspitze dunkel, Wangen, Kehle, Bauch und
    Beine innen hell cremegrau, Beine aussen gelblich; Nase schwarz"""
    GRAU = np.array([0.27, 0.24, 0.19])
    SATTEL = np.array([0.13, 0.115, 0.095])
    GELB = np.array([0.34, 0.25, 0.15])
    HELL = np.array([0.55, 0.50, 0.42])
    y, z = P[:, 1], P[:, 2]
    nz = noise3(P, 3.0)
    nz2 = noise3(P, 11.0, 2.7)
    col = np.tile(GRAU, (len(P), 1))
    sat = sst(0.3, 0.7, (y - 1.75) * 1.6 + nz * 0.6) * (1 - np.clip(g["kopf"], 0, 1))
    col = col * (1 - sat[:, None]) + SATTEL * sat[:, None]
    bein = np.clip(g["bein_u"] * 1.3, 0, 1)
    col = col * (1 - bein[:, None]) + GELB * bein[:, None]
    light = t.mat == "Main_Light"
    col[light] = HELL
    sch = g["schwanz"] > 0.5
    if sch.any():
        col[sch & (z < z[sch].min() + 0.45)] = SATTEL * 0.6
    col[t.mat == "Nose"] = [0.012, 0.01, 0.009]
    col[t.mat == "Eyes_Black"] = [0.03, 0.022, 0.01]
    col *= (1.0 + 0.14 * (nz - 0.5) + 0.10 * (nz2 - 0.5))[:, None]
    klasse = np.zeros(len(P))
    klasse[t.mat == "Eyes_Black"] = 1
    klasse[t.mat == "Nose"] = 2
    fell = np.isin(t.mat, ["Main", "Main_Light"]).astype(float)
    return col, fell, klasse


def farbe_dachs(t, g, P):
    """Dachs: Rücken und Flanken silbergrau (grob gesprenkelt), Beine und Bauch schwarz, Kopf weiss mit zwei schwarzen
    Streifen über Augen und Ohren, Ohrränder weiss"""
    GRAU = np.array([0.32, 0.31, 0.29])
    SCHW = np.array([0.015, 0.014, 0.013])
    WEISS = np.array([0.72, 0.71, 0.68])
    y, ax = P[:, 1], np.abs(P[:, 0])
    nz = noise3(P, 14.0, 1.3)
    col = np.tile(GRAU, (len(P), 1)) * (0.75 + 0.5 * nz[:, None])
    unten = 1 - sst(0.0, 0.25, y - t.bauch_y)
    col = col * (1 - unten[:, None]) + SCHW * unten[:, None]
    bein = np.clip(g["bein"] * 1.2, 0, 1)
    col = col * (1 - bein[:, None]) + SCHW * bein[:, None]
    kopf = np.clip(t.wsum(["Head"]) + g["ohr"] * 0.0, 0, 1) > 0.4
    kopf |= (g["hals"] > 0.5) & (P[:, 2] > t.kopf_z0 - 0.25)
    streif = (ax > 0.06) & (ax < 0.19)
    col[kopf] = WEISS
    col[kopf & streif & (y > t.kinn_y - 0.05) & (P[:, 2] < t.kopf_z0 + 0.95)] = SCHW
    col[(g["ohr"] > 0.5)] = SCHW
    col[(g["ohr"] > 0.5) & (y > np.percentile(y[g["ohr"] > 0.5], 70))] = WEISS
    col[t.mat == "Eyes"] = [0.01, 0.01, 0.01]
    col[t.mat == "Black"] = [0.012, 0.011, 0.01]
    klasse = np.zeros(len(P))
    klasse[t.mat == "Eyes"] = 1
    klasse[t.mat == "Black"] = 2
    fell = np.isin(t.mat, ["Main", "Main_Light", "Grey"]).astype(float)
    return col, fell, klasse


def farbe_schwein(t, g, P):
    """Wildschwein: schwarzbraun bis grau mit Borsten (grobes Rauschen), Rückenkamm dunkler, Rüssel mit grauer Scheibe,
    Beine schwarz; Hauer weisslich (an der Schnauze)"""
    BRAUN = np.array([0.075, 0.06, 0.048])
    GRAU = np.array([0.16, 0.145, 0.13])
    SCHW = np.array([0.02, 0.018, 0.016])
    y, z = P[:, 1], P[:, 2]
    nz = noise3(P, 16.0, 0.7)
    nz2 = noise3(P, 4.0, 3.1)
    col = BRAUN * (1 - nz2[:, None]) + GRAU * nz2[:, None]
    col *= (0.6 + 0.8 * nz[:, None])
    kamm = sst(0.6, 0.95, (y - (t.rueck_y - 0.35)) / 0.35) * (1 - np.clip(g["kopf"], 0, 1))
    col = col * (1 - kamm[:, None]) + SCHW * kamm[:, None]
    bein = np.clip(g["bein_u"] * 1.4, 0, 1)
    col = col * (1 - bein[:, None]) + SCHW * bein[:, None]
    col[t.mat == "Nose"] = [0.10, 0.08, 0.075]               # Rüsselscheibe
    col[t.mat == "Eyes_Black"] = [0.012, 0.01, 0.008]
    klasse = np.zeros(len(P))
    klasse[t.mat == "Eyes_Black"] = 1
    klasse[t.mat == "Nose"] = 2
    fell = np.isin(t.mat, ["Main", "Main_Light"]).astype(float)
    return col, fell, klasse


def farbe_hase(t, g, P):
    """Feldhase: «gesprenkelt» gelbbraun (Agouti), Rücken dunkler, Flanke rötlicher, Bauch weiss, Ohrspitzen schwarz,
    Schwanz oben schwarz, unten weiss; grosse dunkle Augen"""
    BRAUN = np.array([0.25, 0.18, 0.11])
    DUNKEL = np.array([0.11, 0.08, 0.05])
    ROT = np.array([0.31, 0.20, 0.11])
    WEISS = np.array([0.66, 0.63, 0.56])
    y, z = P[:, 1], P[:, 2]
    nz = noise3(P, 18.0, 2.0)
    nz2 = noise3(P, 4.0, 5.5)
    col = BRAUN * (0.75 + 0.5 * nz[:, None])
    top = sst(0.25, 0.75, (y - (t.rueck_y - 0.4)) / 0.4 + 0.4 * (nz2 - 0.5))
    col = col * (1 - top[:, None]) + DUNKEL * top[:, None]
    flank = 1 - sst(0.3, 0.6, (y - t.bauch_y) / max(1e-6, t.rueck_y - t.bauch_y))
    col = col * (1 - 0.4 * flank[:, None]) + ROT * 0.4 * flank[:, None]
    light = t.mat == "Main_Light"
    bauch = light & (y < t.bauch_y + 0.25 * (t.rueck_y - t.bauch_y)) & (g["schwanz"] < 0.5)
    col[light & (g["schwanz"] < 0.5) & (g["ohr"] < 0.5)] = BRAUN * 1.35 + 0.04       # Wangen / Kehle: hell gelbbraun
    col[bauch] = WEISS
    ohr = g["ohr"] > 0.5
    if ohr.any():
        col[ohr & (y > np.percentile(y[ohr], 85))] = [0.015, 0.013, 0.012]
    sch = g["schwanz"] > 0.3
    col[sch] = WEISS
    col[sch & (y > np.median(y[sch])) ] = [0.02, 0.018, 0.016]
    col[t.mat == "Eyes"] = [0.03, 0.02, 0.008]
    col[t.mat == "Black"] = [0.06, 0.04, 0.03]
    klasse = np.zeros(len(P))
    klasse[t.mat == "Eyes"] = 1
    klasse[t.mat == "Black"] = 2
    fell = np.isin(t.mat, ["Main", "Main_Light", "Grey"]).astype(float)
    return col, fell, klasse


def _schnauze(P, t, cz, f_len, f_breit, senk=0.0):
    """Schnauze (Kopf vorne ab cz) länger / kürzer und schmaler / breiter, etwas tiefer"""
    head = np.clip(t.wsum(["Head"]) * 1.2, 0, 1)
    dz = P[:, 2] - cz
    vor = np.where(dz > 0, dz * f_len, dz)
    P[:, 2] = P[:, 2] * (1 - head) + (cz + vor) * head
    k = sst(0.0, 0.35, dz) * head
    P[:, 0] = P[:, 0] * (1 + (f_breit - 1) * k)
    P[:, 1] = P[:, 1] - senk * k * np.clip(dz, 0, None)
    return P


def _ohren_klein(P, t, f):
    """die Ohren zu ihrem Ansatz hin verkleinern (Punkte, die an den Ohr-Knochen hängen)"""
    w = np.clip(t.wpre("Ear") * 1.5, 0, 1)
    for sd in (1, -1):
        m = (w > 0.05) & (P[:, 0] * sd > 0)
        if not m.any():
            continue
        basis = np.array([np.median(P[m, 0]), P[m, 1].min(), np.median(P[m, 2])])
        P[m] = basis + (P[m] - basis) * (1 - (1 - f) * w[m, None])
    return P


def dachs_vorform(P, t):
    return _schnauze(_ohren_klein(P, t, 0.45), t, 2.0, 1.1, 0.8, 0.15)


def schwein_vorform(P, t):
    return _schnauze(_ohren_klein(P, t, 0.75), t, 1.9, 1.75, 1.05, 0.3)    # Wolf: lange Keilschnauze, tief


def hase_vorform(P, t):
    return _schnauze(P, t, 2.0, 0.45, 1.05, 0.0)


def _beine(d, s_front, s_back, s_dicke=1.0):
    for _s in ("L", "R"):
        d["FrontUpperLeg." + _s] = (s_dicke, s_front, s_dicke)
        d["FrontLowerLeg." + _s] = (s_dicke, s_front, s_dicke)
        d["BackUpperLeg." + _s] = (s_dicke, s_back, s_dicke)
        d["BackLowerLeg." + _s] = (s_dicke, s_back, s_dicke)
    return d


def _laengen(d, s_front, s_back):
    for _s in ("L", "R"):
        for b in ("FrontUpperLeg", "FrontLowerLeg"):
            d[b + "." + _s] = s_front
        for b in ("BackUpperLeg", "BackLowerLeg"):
            d[b + "." + _s] = s_back
    return d


def _ohren(d_l, d_d, f_l, f_d):
    for e in ("Ear2", "Ear3", "Ear4"):
        for _s in ("L", "R"):
            d_l[e + "." + _s] = f_l
    for e in ("Ear1", "Ear2", "Ear3", "Ear4"):
        for _s in ("L", "R"):
            d_d[e + "." + _s] = f_d


def _schwanz(d_l, d_d, n, f_l, f_d):
    for k in range(1, n + 1):
        if k > 1:
            d_l["Tail%d" % k] = f_l
        d_d["Tail%d" % k] = f_d


DACHS_L = _laengen({"Neck1": 0.55, "Neck2": 0.55, "Neck3": 0.7, "Torso": 1.05, "Torso2": 1.05}, 0.45, 0.42)
DACHS_D = _beine({"Back": (1.5, 1.05, 1.1), "Torso": (1.6, 1.0, 1.1), "Torso2": (1.6, 1.0, 1.1), "Torso3": (1.35, 1.0, 1.05),
                  "Body": (1.4, 1.0, 1.1), "Neck1": (1.35, 1.0, 1.2), "Neck2": (1.25, 1.0, 1.1), "Head": (1.05, 0.95, 1.0)},
                 0.45, 0.42, 1.35)
_ohren(DACHS_L, DACHS_D, 0.2, (0.38, 0.3, 0.38))
_schwanz(DACHS_L, DACHS_D, 8, 0.35, (0.45, 0.45, 0.45))
SCHWEIN_L = _laengen({"Neck1": 0.5, "Neck2": 0.5, "Neck3": 0.6, "Torso3": 1.1}, 0.62, 0.6)
SCHWEIN_D = _beine({"Back": (1.35, 1.3, 1.1), "Torso": (1.45, 1.35, 1.1), "Torso2": (1.5, 1.45, 1.1), "Torso3": (1.45, 1.5, 1.1),
                    "Body": (1.3, 1.2, 1.1), "Neck1": (1.55, 1.25, 1.4), "Neck2": (1.45, 1.2, 1.3), "Neck3": (1.25, 1.1, 1.1),
                    "Head": (1.1, 1.15, 1.0)}, 0.62, 0.6, 1.35)
_ohren(SCHWEIN_L, SCHWEIN_D, 0.75, (0.85, 0.85, 0.85))
_schwanz(SCHWEIN_L, SCHWEIN_D, 8, 0.6, (0.22, 0.22, 0.22))
HASE_L = _laengen({"Neck1": 0.5, "Neck2": 0.5, "Neck3": 0.65, "Torso": 0.8, "Torso2": 0.8}, 0.5, 0.75)
HASE_D = _beine({"Back": (1.15, 1.3, 1.1), "Torso": (1.15, 1.3, 1.15), "Torso2": (1.05, 1.2, 1.0), "Torso3": (0.95, 1.1, 0.95),
                 "Body": (1.15, 1.2, 1.1), "Head": (0.95, 1.1, 1.0), "Neck1": (1.1, 1.0, 1.1), "Neck2": (1.1, 1.0, 1.1)}, 0.5, 0.75, 1.0)
for _s in ("L", "R"):
    HASE_D["BackUpperLeg." + _s] = (1.4, 0.75, 1.4)            # kräftige Keulen
    HASE_D["BackLeg." + _s] = (1.4, 1.1, 1.4)
    HASE_D["BackLowerLeg." + _s] = (1.0, 0.95, 1.6)            # lange Hinterpfoten
_ohren(HASE_L, HASE_D, 2.6, (0.5, 1.7, 0.65))
_schwanz(HASE_L, HASE_D, 8, 0.12, (0.6, 0.6, 0.6))

TORSO = ["Torso", "Torso2", "Torso3", "Back"]
ART = {
    "fuchs": {"src": "Fox.gltf", "out": "fuchs_glb.bin", "farbe": farbe_fuchs},
    "reh": {"src": "Deer.gltf", "out": "reh_glb.bin", "farbe": farbe_reh},
    "hund_husky": {"src": "Husky.gltf", "out": "hund_husky_glb.bin", "farbe": farbe_husky},
    "hund_shiba": {"src": "ShibaInu.gltf", "out": "hund_shiba_glb.bin", "farbe": farbe_shiba},
    "katze": {"src": "Fox.gltf", "out": "katze_glb.bin", "farbe": farbe_katze, "laenge": KATZE_L, "dicke": KATZE_D,
              "vorform": katze_vorform},
    "igel": {"src": "Fox.gltf", "out": "igel_glb.bin", "farbe": farbe_igel, "laenge": IGEL_L, "dicke": IGEL_D,
             "vorform": igel_vorform, "stacheln": (3000, 0.24, 0.02), "torso": TORSO + ["Body"]},
    "wolf": {"src": "Wolf.gltf", "out": "wolf_glb.bin", "farbe": farbe_wolf},
    "dachs": {"src": "Fox.gltf", "out": "dachs_glb.bin", "farbe": farbe_dachs, "laenge": DACHS_L, "dicke": DACHS_D,
              "vorform": dachs_vorform},
    "wildschwein": {"src": "Wolf.gltf", "out": "wildschwein_glb.bin", "farbe": farbe_schwein, "laenge": SCHWEIN_L,
                    "dicke": SCHWEIN_D, "vorform": schwein_vorform},
    "hase": {"src": "Fox.gltf", "out": "hase_glb.bin", "farbe": farbe_hase, "laenge": HASE_L, "dicke": HASE_D,
             "vorform": hase_vorform},
}


# ---- schreiben -------------------------------------------------------------------------------------------------------
def bauen(art, ordner, out=None):
    cfg = ART[art]
    t = Tier(Path(ordner) / cfg["src"])
    d, acc = t.d, t.acc
    fac = {}
    if cfg.get("laenge") or cfg.get("dicke") or cfg.get("vorform"):
        fac = umformen(t, cfg.get("laenge", {}), cfg.get("dicke", {}), cfg.get("vorform"))
    if cfg.get("stacheln"):
        g0 = t.gruppen()
        hd = t.wsum(["Head"])
        stirn = (hd > 0.5) & (t.P[:, 2] < np.percentile(t.P[hd > 0.5, 2], 45)) & (t.P[:, 1] > np.percentile(t.P[hd > 0.5, 1], 55))
        mask = ((np.clip(g0["rumpf"] + g0["hals"], 0, 1) > 0.5) | stirn) & np.isin(t.mat, ["Main", "Main_Light"])
        mask &= t.P[:, 1] > t.P[mask, 1].min() + 0.12 * np.ptp(t.P[mask, 1])   # nicht am Bauch
        n_, l_, r_ = cfg["stacheln"]
        stacheln(t, mask.astype(float), n_, l_, r_)
        t.stachel_haut = np.concatenate([mask, np.zeros(len(t.P) - len(mask), bool)])
    lo = auf_boden(t)
    g = t.gruppen()
    P = t.P
    rk = (t.wsum(TORSO) > 0.5) & (t.mat != "Stachel")
    t.rueck_y = float(P[rk, 1].max()) if rk.any() else float(P[:, 1].max())
    t.bauch_y = float(np.percentile(P[rk, 1], 3)) if rk.any() else 0.0
    hk = t.wsum(["Head"]) > 0.5
    t.kopf_z0 = float(P[hk, 2].min()) if hk.any() else 0.0
    t.kinn_y = float(np.percentile(P[hk, 1], 30)) if hk.any() else 0.0
    col, fell, klasse = cfg["farbe"](t, g, P)
    col = np.clip(col, 0, 1)
    N = normalen(P, t.I)
    if cfg.get("stacheln"):
        st = t.mat == "Stachel"
        N[st] = normalen(P, t.I, weld=False)[st]
    rest = P.astype(np.float32)
    torso = t.wsum(cfg.get("torso", TORSO)) > 0.5
    ruecken = float(P[torso, 1].max())
    eye = (klasse == 1) & (P[:, 0] > 0)
    augen = P[eye].mean(axis=0) if eye.any() else np.array([0.2, 2.0, 2.0])
    nase = klasse == 2
    meta = {"art": art, "ruecken": round(ruecken, 4), "augen": [round(float(v), 4) for v in augen],
            "augen_r": round(float(np.ptp(P[eye, 1]) * 0.5) if eye.any() else 0.05, 4),
            "nase": [round(float(v), 4) for v in (P[nase].mean(axis=0) if nase.any() else augen)],
            "hoehe": round(float(P[:, 1].max()), 4), "laenge": round(float(np.ptp(P[:, 2])), 4),
            "vorne": round(float(P[:, 2].max()), 4), "hinten": round(float(P[:, 2].min()), 4),
            "breite": round(float(np.ptp(P[:, 0])), 4)}
    # Bereiche für das Wärmebild (Ruhelage, Modell-Einheiten): Kopf ab kopf_z / kopf_y, Beine unter bein_y, Schwanz hinter
    # schwanz_z; kopf_oben = Scheitel zwischen den Ohren (Geweih des Rehbocks)
    hk = (t.wsum(["Head"]) > 0.5) & (t.mat != "Stachel")
    tk = (g["schwanz"] > 0.5) & (t.mat != "Stachel")
    rk = (t.wsum(TORSO) > 0.5) & (t.mat != "Stachel")
    mitte = hk & (np.abs(P[:, 0]) < 0.12)
    meta["kopf_z"] = round(float(P[hk, 2].min()), 4) if hk.any() else 99.0
    meta["kopf_y"] = round(float(P[hk, 1].min()), 4) if hk.any() else 99.0
    meta["bein_y"] = round(float(np.percentile(P[rk, 1], 3)), 4) if rk.any() else 0.0
    meta["schwanz_z"] = round(float(P[tk, 2].max()), 4) if tk.any() else -99.0
    meta["kopf_oben"] = [0.0, round(float(P[mitte, 1].max()), 4), round(float(P[mitte][np.argmax(P[mitte, 1]), 2]), 4)] if mitte.any() else [0, 0, 0]
    print("%s: %d Punkte, %d Dreiecke; %s" % (art, len(P), len(t.I), json.dumps(meta)))

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
            a2 = a.reshape(a.shape[0], -1)
            ac["min"] = [float(x) for x in a2.min(axis=0)]
            ac["max"] = [float(x) for x in a2.max(axis=0)]
        accs.append(ac)
        return len(accs) - 1

    W = t.W / np.maximum(t.W.sum(axis=1, keepdims=True), 1e-9)
    big = len(P) >= 65535
    prim = {"attributes": {
        "POSITION": add(P.astype(np.float32), 5126, "VEC3", 34962, minmax=True),
        "NORMAL": add(N.astype(np.float32), 5126, "VEC3", 34962),
        "COLOR_0": add((np.concatenate([col, fell[:, None]], axis=1) * 255 + 0.5).astype(np.uint8), 5121, "VEC4", 34962, norm=True),
        "TEXCOORD_0": add(rest[:, [0, 1]], 5126, "VEC2", 34962),
        "TEXCOORD_1": add(np.stack([rest[:, 2], klasse.astype(np.float32)], axis=1).astype(np.float32), 5126, "VEC2", 34962),
        "JOINTS_0": add(t.J.astype(np.uint16), 5123, "VEC4", 34962),
        "WEIGHTS_0": add(W.astype(np.float32), 5126, "VEC4", 34962)},
        "indices": add(t.I.reshape(-1).astype(np.uint32 if big else np.uint16), 5125 if big else 5123, "SCALAR", 34963),
        "material": 0}
    skin = {"name": art, "joints": t.joints,
            "inverseBindMatrices": add(np.array([m.T.reshape(-1) for m in t.ibm], dtype=np.float32), 5126, "MAT4")}
    nodes = d["nodes"]
    benutzt = set(np.unique(t.J[t.W > 1e-4]).tolist())     # Knochen, an denen Haut hängt (die Pfoten am IK-Knochen!)
    hilfs = {ni for j, ni in enumerate(t.joints) if j not in benutzt and nodes[ni]["name"].startswith(("IK", "Pole", "FF"))}
    body = t.joints[t.jn.index("Body")]
    anims = []
    have = {ANIM_ALIAS.get(a["name"], a["name"]): a for a in d["animations"]}
    for nm in ANIM_STD:
        an = have.get(nm)
        if an is None:
            print("  (Bewegung fehlt: %s)" % nm)
            continue
        samplers, chans = [], []
        for c in an["channels"]:
            ni = c["target"]["node"]
            if ni in hilfs:
                continue
            s = an["samplers"][c["sampler"]]
            tin = acc(s["input"]).astype(np.float32).reshape(-1)
            val = acc(s["output"]).astype(np.float64)
            path = c["target"]["path"]
            if path == "translation":
                val = val * fac.get(ni, 1.0)
                if ni == body:
                    val = val - np.array([0.0, lo, 0.0])        # wie die Ruhelage (auf_boden)
            const = np.ptp(val, axis=0).max() < 1e-5
            if path == "scale" and const and np.abs(val[0] - 1).max() < 1e-4:
                continue                                        # Skalierung 1 ist die Ruhe
            if const:
                tin, val = tin[:1], val[:1]
            samplers.append({"input": add(tin, 5126, "SCALAR", minmax=True), "output": add(val.astype(np.float32), 5126,
                             "VEC4" if path == "rotation" else "VEC3"), "interpolation": s.get("interpolation", "LINEAR")})
            chans.append({"sampler": len(samplers) - 1, "target": {"node": ni, "path": path}})
        anims.append({"name": nm, "samplers": samplers, "channels": chans})
    mesh_node = [i for i, n in enumerate(nodes) if n.get("mesh") is not None][0]
    nodes[mesh_node]["name"] = art
    g_ = {"asset": {"version": "2.0", "generator": "MoveEye werkzeuge/tier_modelle.py",
                    "copyright": "Modell: Quaternius «Ultimate Animated Animals» %s, CC0 1.0 (angepasst für MoveEye)" % cfg["src"]},
          "scene": 0, "scenes": [dict(d["scenes"][0], extras={"moveeye": meta})], "nodes": nodes,
          "meshes": [{"name": art, "primitives": [prim]}],
          "materials": [{"name": "Fell", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 0.85}}],
          "skins": [skin], "animations": anims, "accessors": accs, "bufferViews": views,
          "buffers": [{"byteLength": len(blob)}]}
    while len(blob) % 4:
        blob.append(0)
    g_["buffers"][0]["byteLength"] = len(blob)
    js = json.dumps(g_, separators=(",", ":"), ensure_ascii=False).encode()
    while len(js) % 4:
        js += b" "
    glb = b"glTF" + struct.pack("<II", 2, 12 + 8 + len(js) + 8 + len(blob))
    glb += struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(blob)) + b"BIN\x00" + bytes(blob)
    out = Path(out) if out else MODELLE / cfg["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(glb)
    print("  geschrieben: %s (%d Bytes, Bewegungen: %s)" % (out, len(glb), ", ".join(a["name"] for a in anims)))


def main():
    ordner = sys.argv[1] if len(sys.argv) > 1 else "."
    for a in sys.argv[2:] or list(ART):
        bauen(a, ordner)


if __name__ == "__main__":
    main()
