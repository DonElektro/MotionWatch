#!/usr/bin/env python3
"""Menschen-Paket für den 3D-Simulator bauen («Figuren menschlicher», 01.11.2026): echte Körper aus MakeHuman (CC0).

Liest die freien Daten von MakeHuman / MPFB2 (GitHub makehumancommunity/mpfb2, Ordner src/mpfb/data, Lizenz der Daten:
CC0 1.0): Grundkörper `3dobjs/base.obj` (Gesicht, Hände mit Daumen, Füsse, Hilfsformen für Augen und Wimpern), die
Makro-Formen `targets/macrodetails` (Geschlecht, Alter, Muskeln, Gewicht, Grösse, Herkunft), das Skelett
`rigs/standard/rig.game_engine.json` und seine Gewichte `weights.game_engine.json` (gleiche Knochennamen wie die
Quaternius-Animationen: pelvis, spine_01 …) und die Masken `textures/mpfb_lips.jpg` … (Lippen, Nägel, Lider, Ohren).

Daraus entstehen 8 Körper (Mann / Frau schlank und kräftig, Ältere, Kinder) als .glb mit Skelett:
  * das Skelett hat die Knochen und **die Ruhe-Ausrichtung der Quaternius-Animationen** (anim_1.glb / anim_2.glb aus
    figuren_v1.zip, CC0) - darum laufen deren Bewegungen ohne Umrechnen (Retarget beim Bauen): Ruhe = Haltung der
    Quaternius-Figur mit den Knochenlängen des MakeHuman-Körpers, Bindehaltung = A-Haltung des MakeHuman-Körpers
    (inverse Bind-Matrizen), Gewichte von MPFB.
  * Teile (eigene Netze, im Simulator zusammengesetzt): Haut (Kopf, Hände, nackte Unterarme / Unterschenkel), Jacke,
    Ärmel, Hose, Hosenbeine, Schuhe (aus dem Körper nach aussen versetzt, Säume dunkler, Sohle), Haare (kurz, lang, Dutt,
    Kranz), Kapuze, Augen (Iris, Pupille), Brauen, Wimpern. Farben pro Ecke (Lippen, Nägel, Saum); die Kleiderfarbe
    und die Stoffstruktur setzt der Simulator (figur_mensch.gd).

    python3 werkzeuge/menschen_paket.py MPFB_DATA figuren_v1.zip AUSGABE.zip

MPFB_DATA: z. B. `git clone --depth 1 --filter=blob:none --sparse https://github.com/makehumancommunity/mpfb2` und
`git sparse-checkout set src/mpfb/data/3dobjs src/mpfb/data/rigs/standard src/mpfb/data/targets/macrodetails
src/mpfb/data/textures`. Das ZIP gehört NICHT ins Simulator-ZIP (nachladbar wie figuren_v1.zip).
"""
import gzip
import io
import json
import math
import os
import struct
import sys
import zipfile

import numpy as np
from PIL import Image

VERSION = 1
SCALE = 0.1                                   # MakeHuman: Dezimeter -> Meter

# Körper: Geschlecht (1 Mann), Alter (Jahre), Muskeln, Gewicht, Grösse (0..1), Herkunft, Augenfarbe
BODIES = {
    "m_schlank": dict(g=1.0, age=31, mus=0.55, wei=0.36, hgt=0.5, race=(0.85, 0.1, 0.05), sex="m", alter="erw", bau="schlank", eye=(0.28, 0.42, 0.62)),
    "m_kraeftig": dict(g=1.0, age=43, mus=0.62, wei=0.8, hgt=0.5, race=(0.8, 0.05, 0.15), sex="m", alter="erw", bau="kraeftig", eye=(0.36, 0.24, 0.12)),
    "f_schlank": dict(g=0.0, age=28, mus=0.45, wei=0.36, hgt=0.6, race=(0.85, 0.05, 0.1), sex="f", alter="erw", bau="schlank", eye=(0.33, 0.45, 0.33)),
    "f_kraeftig": dict(g=0.0, age=46, mus=0.5, wei=0.78, hgt=0.45, race=(0.8, 0.15, 0.05), sex="f", alter="erw", bau="kraeftig", eye=(0.3, 0.2, 0.1)),
    "m_alt": dict(g=1.0, age=73, mus=0.4, wei=0.62, hgt=0.4, race=(0.9, 0.05, 0.05), sex="m", alter="alt", bau="normal", eye=(0.42, 0.5, 0.58)),
    "f_alt": dict(g=0.0, age=71, mus=0.35, wei=0.62, hgt=0.35, race=(0.9, 0.05, 0.05), sex="f", alter="alt", bau="normal", eye=(0.35, 0.3, 0.2)),
    "k_m": dict(g=1.0, age=9, mus=0.5, wei=0.45, hgt=0.5, race=(0.85, 0.1, 0.05), sex="m", alter="kind", bau="normal", eye=(0.3, 0.45, 0.6)),
    "k_f": dict(g=0.0, age=9, mus=0.5, wei=0.42, hgt=0.5, race=(0.85, 0.05, 0.1), sex="f", alter="kind", bau="normal", eye=(0.35, 0.22, 0.1)),
}
RACES = ("caucasian", "african", "asian")
# Haare pro Körper (der Simulator wählt eines)
HAIRS = {"m": ["kurz", "kurz2", "lang"], "f": ["lang", "dutt", "kurz2"], "alt_m": ["kranz", "kurz"], "alt_f": ["kurz2", "dutt"]}
NAME_MAP = {"Root": "root", "head": "Head"}

# ---------------------------------------------------------------------------------------------------- quaternions
def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


def qinv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]]) / np.dot(q, q)


def qrot(q, v):
    p = np.array([v[0], v[1], v[2], 0.0])
    return qmul(qmul(q, p), qinv(q))[:3]


def qmat(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def qswing(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    c = np.cross(a, b)
    d = float(np.dot(a, b))
    if d < -0.9999:
        ax = np.cross(a, [1, 0, 0])
        if np.linalg.norm(ax) < 1e-3:
            ax = np.cross(a, [0, 0, 1])
        ax /= np.linalg.norm(ax)
        return np.array([ax[0], ax[1], ax[2], 0.0])
    q = np.array([c[0], c[1], c[2], 1.0 + d])
    return q / np.linalg.norm(q)


# ---------------------------------------------------------------------------------------------------- MakeHuman data
def load_obj(path):
    V, VT, faces = [], [], []
    grp = ""
    for line in open(path):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("vt "):
            VT.append([float(x) for x in line.split()[1:3]])
        elif line.startswith("g "):
            grp = line.split()[1]
        elif line.startswith("f "):
            c = []
            for t in line.split()[1:]:
                p = t.split("/")
                c.append((int(p[0]) - 1, int(p[1]) - 1 if len(p) > 1 and p[1] else -1))
            faces.append((grp, c))
    return np.array(V), np.array(VT), faces


_tcache = {}


def target(data, rel):
    if rel in _tcache:
        return _tcache[rel]
    p = os.path.join(data, "targets", "macrodetails", rel + ".target.gz")
    out = None
    if os.path.exists(p):
        idx, d = [], []
        for line in gzip.open(p, "rt"):
            s = line.split()
            if len(s) == 4 and not line.startswith("#"):
                idx.append(int(s[0]))
                d.append([float(s[1]), float(s[2]), float(s[3])])
        if idx:
            out = (np.array(idx), np.array(d))
    _tcache[rel] = out
    return out


def two(v, lo, hi):
    """MakeHuman macro slider 0..1 -> weights of the low / average / high target"""
    if v < 0.5:
        return {lo: 1.0 - 2.0 * v, "average" + lo[3:]: 2.0 * v}
    return {"average" + lo[3:]: 2.0 - 2.0 * v, hi: 2.0 * v - 1.0}


def morph(data, V, b):
    g = b["g"]
    gw = {"male": g, "female": 1.0 - g}
    yrs = b["age"]
    if yrs < 11:
        a = 0.1875 * (yrs - 1) / 10.0
    elif yrs < 25:
        a = 0.1875 + (yrs - 11) / 14.0 * (0.5 - 0.1875)
    else:
        a = 0.5 + 0.5 * (yrs - 25) / 65.0
    if a < 0.1875:
        aw = {"baby": 1.0 - a / 0.1875, "child": a / 0.1875}
    elif a < 0.5:
        c = (0.5 - a) / (0.5 - 0.1875)
        aw = {"child": c, "young": 1.0 - c}
    else:
        y = (1.0 - a) / 0.5
        aw = {"young": y, "old": 1.0 - y}
    mw = two(b["mus"], "minmuscle", "maxmuscle")
    ww = two(b["wei"], "minweight", "maxweight")
    h = b["hgt"]
    hw = {"minheight": 1.0 - 2.0 * h} if h < 0.5 else {"maxheight": 2.0 * h - 1.0}
    out = V.copy()

    def add(rel, w):
        if w <= 1e-4:
            return
        t = target(data, rel)
        if t is not None:
            out[t[0]] += t[1] * w
    for gk, gv in gw.items():
        for ak, av in aw.items():
            for ri, rk in enumerate(RACES):
                add("%s-%s-%s" % (rk, gk, ak), b["race"][ri] * gv * av)
            for mk, mv in mw.items():
                for wk, wv in ww.items():
                    add("universal-%s-%s-%s-%s" % (gk, ak, mk, wk), gv * av * mv * wv)
                    for hk, hv in hw.items():
                        add("height/%s-%s-%s-%s-%s" % (gk, ak, mk, wk, hk), gv * av * mv * wv * hv)
    return out


def normals(P, tris):
    n = np.zeros_like(P)
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    fn = np.cross(b - a, c - a)
    for k in range(3):
        np.add.at(n, tris[:, k], fn)
    ln = np.linalg.norm(n, axis=1)
    ln[ln < 1e-12] = 1.0
    return n / ln[:, None]


def tri_of(faces_c):
    t = []
    for c in faces_c:
        for k in range(1, len(c) - 1):
            t.append((c[0], c[k], c[k + 1]))
    return t


# ---------------------------------------------------------------------------------------------------- Quaternius rest
def glb_json(b):
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n])


def quaternius_rest(fig_zip):
    z = zipfile.ZipFile(fig_zip)
    j = glb_json(z.read("anim_1.glb"))
    nodes = j["nodes"]
    parent = {}
    for i, nd in enumerate(nodes):
        for c in nd.get("children", []):
            parent[c] = i
    G, L, T = {}, {}, {}

    def glob(i):
        nd = nodes[i]
        q = np.array(nd.get("rotation", [0, 0, 0, 1.0]))
        if i in parent:
            return qmul(glob(parent[i]), q)
        return q
    names = {}
    for i, nd in enumerate(nodes):
        nm = nd.get("name", "")
        names[nm] = i
        G[nm] = glob(i)
        L[nm] = np.array(nd.get("rotation", [0, 0, 0, 1.0]))
        T[nm] = np.array(nd.get("translation", [0, 0, 0.0]))
    par = {nodes[i].get("name"): nodes[p].get("name") for i, p in parent.items()}
    return G, L, T, par


def quaternius_pos(qr):
    """global rest positions of the Quaternius bones (model space, y up)"""
    GQ, LQ, TQ, PQ = qr
    pos = {}

    def gp(n):
        if n in pos:
            return pos[n]
        p = PQ.get(n)
        if p is None or p in ("Armature", "Mannequin"):
            pos[n] = np.zeros(3)
        else:
            pos[n] = gp(p) + qrot(GQ[p], TQ[n])
        return pos[n]
    for n in GQ:
        gp(n)
    return pos


# ---------------------------------------------------------------------------------------------------- glb writer
class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.j = {"asset": {"version": "2.0", "generator": "MoveEye menschen_paket.py"}, "buffers": [{}], "bufferViews": [],
                  "accessors": [], "nodes": [], "meshes": [], "materials": [], "skins": [], "scenes": [{"nodes": [0]}], "scene": 0}
        self.mats = {}

    def acc(self, arr, ctype, typ, normalized=False, target=None, minmax=False):
        raw = arr.tobytes()
        while len(self.bin) % 4:
            self.bin.append(0)
        bv = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(raw)}
        if target:
            bv["target"] = target
        self.bin += raw
        self.j["bufferViews"].append(bv)
        a = {"bufferView": len(self.j["bufferViews"]) - 1, "componentType": ctype, "count": int(arr.shape[0]), "type": typ}
        if normalized:
            a["normalized"] = True
        if minmax:
            a["min"] = [float(x) for x in arr.min(axis=0)]
            a["max"] = [float(x) for x in arr.max(axis=0)]
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def mat(self, name):
        if name not in self.mats:
            self.j["materials"].append({"name": name, "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0.0,
                                                                                "roughnessFactor": 0.8}})
            self.mats[name] = len(self.j["materials"]) - 1
        return self.mats[name]

    def write(self):
        self.j["buffers"][0]["byteLength"] = len(self.bin)
        js = json.dumps(self.j, separators=(",", ":")).encode()
        while len(js) % 4:
            js += b" "
        data = bytes(self.bin)
        while len(data) % 4:
            data += b"\0"
        total = 12 + 8 + len(js) + 8 + len(data)
        return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
                + struct.pack("<II", len(data), 0x004E4942) + data)


# ---------------------------------------------------------------------------------------------------- one body
def build_body(data, key, b, base, rig, wts, masks, qr):
    V0, VT, faces = base
    V = morph(data, V0, b) * SCALE
    groups = {}
    for gi, (g, c) in enumerate(faces):
        groups.setdefault(g, []).append(gi)

    def gverts(g):
        s = set()
        for fi in groups.get(g, []):
            for v, _t in faces[fi][1]:
                s.add(v)
        return sorted(s)
    body_f = [faces[i][1] for i in groups["body"]]
    body_v = np.array(gverts("body"))
    # ground: lowest point of the feet; the shoe sole (1 cm) stands on y = 0
    V[:, 1] -= V[body_v, 1].min() - 0.012
    # joints
    cube = {}

    def jpos(e):
        if e["strategy"] == "CUBE":
            nm = e["cube_name"]
            if nm not in cube:
                cube[nm] = V[gverts(nm)].mean(axis=0)
            return cube[nm]
        if e["strategy"] == "MEAN":
            return V[e["vertex_indices"]].mean(axis=0)
        return np.array(e.get("default_position", [0, 0, 0]))
    bones = {}
    for bn, d in rig.items():
        nm = NAME_MAP.get(bn, bn)
        par = NAME_MAP.get(d["parent"], d["parent"]) if d["parent"] else ""
        bones[nm] = {"head": jpos(d["head"]), "tail": jpos(d["tail"]), "parent": par, "src": bn}
    bones["root"]["head"] = np.array([0.0, 0.0, 0.0])
    GQ, LQ, TQ, PQ = qr
    # the spine like the Quaternius skeleton: its joints at the same share of the way pelvis -> neck (MPFB has a long
    # spine_03 that ends 20 cm below the neck - with the clips that bent the head far forward)
    qp = quaternius_pos(qr)
    p0 = bones["pelvis"]["head"]
    n0 = bones["neck_01"]["head"]
    span = qp["neck_01"][1] - qp["pelvis"][1]
    chain = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01"]
    for nm in chain[1:4]:
        f = (qp[nm][1] - qp["pelvis"][1]) / span
        bones[nm]["head"] = p0 + (n0 - p0) * f
    for a_, b_ in zip(chain[:-1], chain[1:]):
        bones[a_]["tail"] = bones[b_]["head"].copy()
    order = []

    def visit(nm):
        if nm in order:
            return
        p = bones[nm]["parent"]
        if p:
            visit(p)
        order.append(nm)
    for nm in bones:
        visit(nm)
    B = {}
    for nm in order:
        if nm == "root":
            B[nm] = GQ["root"]
            continue
        dq = qrot(GQ[nm], [0, 1, 0])
        dm = bones[nm]["tail"] - bones[nm]["head"]
        B[nm] = qmul(qswing(dq, dm), GQ[nm]) if np.linalg.norm(dm) > 1e-5 else GQ[nm]
    # leaf bones of the animations (no weights): their place from the Quaternius rest
    extra = [n for n in GQ if n not in bones and (n.endswith("_leaf_l") or n.endswith("_leaf_r"))]
    joints = order + extra
    jidx = {n: i for i, n in enumerate(joints)}
    # weights: top 4 per vertex
    nV = V.shape[0]
    W = np.zeros((nV, len(joints)))
    for bn, lst in wts.items():
        nm = NAME_MAP.get(bn, bn)
        if nm not in jidx:
            continue
        for vi, w in lst:
            W[vi, jidx[nm]] = w
    top = np.argsort(-W, axis=1)[:, :4]
    tw = np.take_along_axis(W, top, axis=1)
    s = tw.sum(axis=1)
    s[s < 1e-9] = 1.0
    tw = tw / s[:, None]
    dom = top[:, 0]
    # ---- classes of the body vertices
    def isb(nm_list):
        ids = [jidx[n] for n in nm_list if n in jidx]
        return np.isin(dom, ids)
    yv = V[:, 1]
    pel = bones["pelvis"]["head"][1]
    hgt = V[body_v, 1].max()
    k = hgt / 1.75
    waist = pel + 0.07 * k
    ankle = bones["foot_l"]["head"][1]
    HEAD = isb(["Head", "neck_01"])
    HAND = isb([n for n in joints if n.startswith(("hand_", "thumb_", "index_", "middle_", "ring_", "pinky_"))])
    FORE = isb(["lowerarm_l", "lowerarm_r"])
    UPPER = isb(["upperarm_l", "upperarm_r", "clavicle_l", "clavicle_r", "spine_01", "spine_02", "spine_03"])
    PELV = isb(["pelvis"])
    THIGH = isb(["thigh_l", "thigh_r"])
    CALF = isb(["calf_l", "calf_r"])
    FOOT = isb(["foot_l", "foot_r", "ball_l", "ball_r"])
    neck_low = bones["neck_01"]["head"][1]
    member = {
        "Skin": HEAD | (UPPER & (yv > neck_low - 0.012 * k)),
        "Skin_Hand": HAND,
        "Bare_Arm": FORE,
        "Bare_Leg": (CALF & (yv > ankle + 0.03 * k)) | (THIGH & (yv < bones["calf_l"]["head"][1] + 0.12 * k)),
        "Jacke": UPPER | (HEAD & (yv < neck_low + 0.025 * k)) | (PELV & (yv > waist - 0.09 * k)),
        "Aermel": FORE,
        "Hose": THIGH | (PELV & (yv < waist + 0.02 * k)),
        "Hosenbein": CALF & (yv > ankle - 0.01 * k),
        "Schuh": FOOT | (CALF & (yv < ankle + 0.045 * k)),
    }
    offs = {"Skin": 0.0, "Skin_Hand": 0.0, "Bare_Arm": 0.0, "Bare_Leg": 0.0, "Jacke": 0.02, "Aermel": 0.017,
            "Hose": 0.012, "Hosenbein": 0.012, "Schuh": 0.012}
    body_tris = np.array(tri_of([[v for v, _ in c] for c in body_f]))
    N = normals(V, body_tris)
    parts = {}
    for pn, mem in member.items():
        fl = []
        for c in body_f:
            m = [mem[v] for v, _ in c]
            if (pn.startswith(("Skin", "Bare")) and any(m)) or (not pn.startswith(("Skin", "Bare")) and sum(m) * 2 > len(m)):
                fl.append(c)
        parts[pn] = fl
    # shorts / short sleeves: the trousers end above the knee, the bare leg starts there
    out = {}
    # ---- vertex colours of the skin (masks in the UV space of MakeHuman)
    def mask(name, uv):
        im = masks[name]
        w, h = im.shape[1], im.shape[0]
        x = np.clip((uv[:, 0] * (w - 1)).astype(int), 0, w - 1)
        y = np.clip(((1.0 - uv[:, 1]) * (h - 1)).astype(int), 0, h - 1)
        return im[y, x] / 255.0
    eye_c = {s: V[gverts("helper-%s-eye" % s)].mean(axis=0) for s in "lr"}
    for pn, fl in parts.items():
        if not fl:
            continue
        corners = sorted({(v, t) for c in fl for v, t in c})
        ci = {c: i for i, c in enumerate(corners)}
        vi = np.array([v for v, _ in corners])
        uv = np.array([VT[t] if t >= 0 else [0, 0] for _, t in corners])
        tris = np.array([(ci[a], ci[b2], ci[c2]) for c in fl for a, b2, c2 in tri_of([c])])
        off = np.full(len(vi), offs[pn])
        if pn == "Aermel":                              # the sleeve narrower to the wrist (same as the jacket at the elbow)
            for sd in "lr":
                e = bones["lowerarm_" + sd]["head"]
                w_ = bones["hand_" + sd]["head"]
                ax = w_ - e
                t_ = np.clip(((V[vi] - e) @ ax) / max(1e-6, ax @ ax), 0, 1)
                side = (V[vi, 0] > 0) == (e[0] > 0)
                off[side] = offs["Jacke"] - 0.008 * t_[side]
        P = V[vi] + N[vi] * off[:, None]
        col = np.ones((len(vi), 3)) * 0.8
        if pn.startswith(("Skin", "Bare")):
            lips = mask("lips", uv)
            nails = np.maximum(mask("fingernails", uv), mask("toenails", uv))
            lids = mask("eyelids", uv)
            ears = mask("ears", uv)
            lipc = np.array([0.8, 0.52, 0.52]) if b["sex"] == "f" else np.array([0.78, 0.58, 0.56])
            col = col * (1 - lips[:, None]) + lipc * lips[:, None]
            col = col * (1 - nails[:, None] * 0.6) + np.array([0.9, 0.78, 0.76]) * nails[:, None] * 0.6
            col = col * (1 - lids[:, None] * 0.35) + np.array([0.68, 0.6, 0.58]) * lids[:, None] * 0.35
            col = col * (1 - ears[:, None] * 0.3) + np.array([0.82, 0.66, 0.64]) * ears[:, None] * 0.3
            # cheeks a little rosy, brows a little darker (under the hair of the brows)
            for s in "lr":
                ec = eye_c[s]
                d = np.linalg.norm((V[vi] - (ec + np.array([0.0, -0.035 * k, 0.012]))) * [1.0, 1.3, 1.0], axis=1)
                ch = np.clip(1.0 - d / (0.03 * k), 0, 1)[:, None] * 0.25
                col = col * (1 - ch) + np.array([0.84, 0.6, 0.58]) * ch
            if b["sex"] == "m" and b["alter"] != "kind":   # a shadow of a beard (shaved)
                jaw = bones["Head"]["head"]
                below = (V[vi, 1] < jaw[1] + 0.035 * k) & (V[vi, 2] > jaw[2] + 0.02) & HEAD[vi]
                col[below] *= np.array([0.92, 0.9, 0.9])
        else:
            # hem: darker on the border (vertices of the part that touch a face outside of it), seam of the zip
            used = np.zeros(len(V), bool)
            used[vi] = True
            edge = {}
            for c in fl:
                for k2 in range(len(c)):
                    e = tuple(sorted((c[k2][0], c[(k2 + 1) % len(c)][0])))
                    edge[e] = edge.get(e, 0) + 1
            border = set()
            for e, n in edge.items():
                if n == 1:
                    border.update(e)
            bd = np.array([v in border for v in vi])
            col[bd] *= 0.62
            # second ring lighter dark: neighbours of the border
            ring = set()
            for c in fl:
                vs = [v for v, _ in c]
                if any(v in border for v in vs):
                    ring.update(vs)
            rg = np.array([(v in ring) and (v not in border) for v in vi])
            col[rg] *= 0.85
            # gradient: a little lighter on the shoulders, darker to the hem (light from above, fabric folds)
            yy = V[vi, 1]
            col *= np.clip(0.88 + 0.12 * (yy - yy.min()) / max(1e-3, yy.max() - yy.min()), 0.85, 1.0)[:, None]
            if pn == "Jacke":
                zip_ = (np.abs(V[vi, 0]) < 0.006) & (V[vi, 2] > 0.0) & (V[vi, 1] > waist - 0.08 * k) & (V[vi, 1] < neck_low)
                col[zip_] *= 0.55
            if pn == "Schuh":
                sole = V[vi, 1] < 0.03 * k
                col[sole] = np.array([0.18, 0.17, 0.16])
                P[sole, 1] = np.maximum(P[sole, 1] - 0.004, 0.0)
        Nn = normals(P, tris) if offs[pn] > 0 else N[vi]
        out[pn] = {"P": P, "N": Nn, "UV": uv, "C": col, "J": top[vi], "W": tw[vi], "T": tris, "mat": pn}
    # ---- head grid: hair, hood, brows
    headv = body_v[HEAD[body_v] & (yv[body_v] > bones["neck_01"]["tail"][1] - 0.01 * k)]
    hp = V[headv]
    lo, hi = hp.min(axis=0), hp.max(axis=0)
    c0 = np.array([(lo[0] + hi[0]) / 2, lo[1] + (hi[1] - lo[1]) * 0.55, (lo[2] + hi[2]) / 2 - 0.004])
    dv = hp - c0
    dl = np.linalg.norm(dv, axis=1)
    du = dv / dl[:, None]
    jh = jidx["Head"]
    jn = jidx["neck_01"]
    js3 = jidx["spine_03"]

    def rad(d):
        """head radius in direction d (unit, many directions at once)"""
        cos = du @ d.T                                   # (nv, nd)
        r = np.where(cos > 0.97, dl[:, None] * cos, 0.0).max(axis=0)
        r2 = np.where(cos > 0.9, dl[:, None] * cos, 0.0).max(axis=0)
        return np.where(r > 0, r, r2)
    NT, NP = 40, 22
    th = np.linspace(0, 2 * np.pi, NT + 1)[:-1]
    ph = np.linspace(-0.62 * np.pi / 2, np.pi / 2, NP)      # from below the ear to the crown
    D = np.array([[math.cos(p) * math.sin(t), math.sin(p), math.cos(p) * math.cos(t)] for p in ph for t in th])
    R = rad(D)
    for i in range(len(R)):
        if R[i] <= 0:
            R[i] = R[i - 1] if i > 0 else 0.1

    def grid_mesh(maskf, thick, mat, extra_rows=0, weight_neck=False):
        """a shell over the head: the cells whose 4 corners are in the mask; thinner at the border"""
        idx = {}
        P, Nn, UV, C, J, Wt = [], [], [], [], [], []
        inm = np.array([maskf(D[i]) for i in range(len(D))])
        tris = []
        for ip in range(NP - 1):
            for it in range(NT):
                a = ip * NT + it
                b2 = ip * NT + (it + 1) % NT
                c2 = (ip + 1) * NT + (it + 1) % NT
                d2 = (ip + 1) * NT + it
                if inm[a] and inm[b2] and inm[c2] and inm[d2]:
                    for q in (a, b2, c2, d2):
                        if q not in idx:
                            idx[q] = len(P)
                            P.append(None)
                    tris += [(idx[a], idx[b2], idx[c2]), (idx[a], idx[c2], idx[d2])]
        # border: corners with a neighbour outside the mask
        for q, i in idx.items():
            ip, it = divmod(q, NT)
            nb = [(ip + dp) * NT + (it + dt) % NT for dp, dt in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= ip + dp < NP]
            border = any(not inm[n] for n in nb) or ip == NP - 1 and False
            t = thick * (0.35 if border else 1.0)
            d = D[q]
            P[i] = c0 + d * (R[q] + t)
            Nn.append(d)
            UV.append([it / NT * 6.0, ip / NP * 2.0])
            C.append([0.8, 0.8, 0.8] if not border else [0.7, 0.7, 0.7])
            J.append([jh, jn, 0, 0])
            Wt.append([1.0, 0.0, 0, 0] if not weight_neck or d[1] > -0.2 else [0.7, 0.3, 0, 0])
        return {"P": np.array(P), "N": np.array(Nn), "UV": np.array(UV), "C": np.array(C), "J": np.array(J), "W": np.array(Wt),
                "T": np.array(tris), "mat": mat}

    def front(d):
        return d[2]
    def hair_short(d, low=-0.05, front_y=0.42):
        if d[1] > 0.6:
            return True
        if d[2] > 0.28:
            return d[1] > front_y
        if abs(d[0]) > 0.55 and d[2] > -0.25:
            return d[1] > 0.1 + 0.25 * max(0.0, d[2])
        return d[1] > low - 0.45 * max(0.0, -d[2])
    hairs = {}
    hairs["kurz"] = grid_mesh(lambda d: hair_short(d, 0.0, 0.45), 0.008 * k, "Hair")
    hairs["kurz2"] = grid_mesh(lambda d: hair_short(d, -0.1, 0.36), 0.016 * k, "Hair")
    hairs["kranz"] = grid_mesh(lambda d: (-0.38 < d[1] < 0.28) and d[2] < 0.3 and not (abs(d[0]) > 0.6 and d[1] < -0.05 and d[2] > -0.2), 0.006 * k, "Hair")
    lang = grid_mesh(lambda d: hair_short(d, -0.25, 0.33) or (d[2] < 0.15 and d[1] > -0.55), 0.02 * k, "Hair", weight_neck=True)
    # the long hair: a curtain below the back of the head down to the shoulders
    cur_P, cur_UV, cur_T, cur_J, cur_W = [], [], [], [], []
    ts = [t for t in th if math.cos(t) < 0.25]
    rows = 6
    eq = {t: rad(np.array([[math.sin(t), -0.35, math.cos(t)]]) / np.linalg.norm([math.sin(t), -0.35, math.cos(t)]))[0] for t in ts}
    for r_ in range(rows):
        f = r_ / (rows - 1)
        for t in ts:
            dd = np.array([math.sin(t), 0, math.cos(t)])
            rr = eq[t] * (0.95 + 0.25 * f) + 0.018 * k
            p = c0 + dd * rr + np.array([0, -0.035 * k - f * 0.2 * k, 0])
            cur_P.append(p)
            cur_UV.append([t / (2 * np.pi) * 6.0, 2.0 + f * 1.5])
            cur_J.append([jh, js3, jn, 0])
            cur_W.append([max(0.0, 1.0 - f * 1.2), min(1.0, f * 1.2) * 0.6, min(1.0, f * 1.2) * 0.4, 0])
    nt = len(ts)
    for r_ in range(rows - 1):
        for i in range(nt - 1):
            a = r_ * nt + i
            cur_T += [(a, a + nt, a + 1), (a + 1, a + nt, a + nt + 1)]
    off = len(lang["P"])
    CP = np.array(cur_P)
    cn = CP - (c0 + np.array([0, -0.1 * k, 0]))
    cn[:, 1] = 0
    cn /= np.maximum(1e-6, np.linalg.norm(cn, axis=1))[:, None]
    CW = np.array(cur_W)
    CW /= CW.sum(axis=1)[:, None]
    lang = {"P": np.vstack([lang["P"], CP]), "N": np.vstack([lang["N"], cn]), "UV": np.vstack([lang["UV"], cur_UV]),
            "C": np.vstack([lang["C"], np.full((len(CP), 3), 0.75)]), "J": np.vstack([lang["J"], cur_J]),
            "W": np.vstack([lang["W"], CW]), "T": np.vstack([lang["T"], np.array(cur_T) + off]), "mat": "Hair"}
    hairs["lang"] = lang
    # bun: a ball at the back of the crown
    dutt = grid_mesh(lambda d: hair_short(d, -0.05, 0.4), 0.01 * k, "Hair")
    bc = c0 + np.array([0, 0.055 * k, -0.095 * k])
    br = 0.042 * k
    bP, bT, bUV = [], [], []
    for i in range(9):
        for j2 in range(12):
            p_ = np.pi * i / 8
            t_ = 2 * np.pi * j2 / 12
            bP.append(bc + br * np.array([math.sin(p_) * math.cos(t_), math.cos(p_), math.sin(p_) * math.sin(t_)]))
            bUV.append([j2 / 12 * 3, i / 8])
    for i in range(8):
        for j2 in range(12):
            a = i * 12 + j2
            b2 = i * 12 + (j2 + 1) % 12
            bT += [(a, b2, a + 12), (b2, b2 + 12, a + 12)]
    bP = np.array(bP)
    o2 = len(dutt["P"])
    bn_ = (bP - bc) / br
    dutt = {"P": np.vstack([dutt["P"], bP]), "N": np.vstack([dutt["N"], bn_]), "UV": np.vstack([dutt["UV"], bUV]),
            "C": np.vstack([dutt["C"], np.full((len(bP), 3), 0.75)]), "J": np.vstack([dutt["J"], np.tile([jh, 0, 0, 0], (len(bP), 1))]),
            "W": np.vstack([dutt["W"], np.tile([1.0, 0, 0, 0], (len(bP), 1))]), "T": np.vstack([dutt["T"], np.array(bT) + o2]), "mat": "Hair"}
    hairs["dutt"] = dutt
    hk = ("alt_" + b["sex"]) if b["alter"] == "alt" else b["sex"]
    for hn in HAIRS[hk]:
        out["Haar_" + hn] = hairs[hn]
    # hood: all round the head except the face, thick
    out["Kapuze"] = grid_mesh(lambda d: d[1] > 0.5 or (d[2] < 0.12 and d[1] > -0.62) or (d[2] < 0.35 and d[1] > 0.2), 0.024 * k, "Kapuze", weight_neck=True)
    # brows: a strip above each eye on the skin
    bro_P, bro_T, bro_UV = [], [], []
    for s, sx in (("l", 1.0), ("r", -1.0)):
        ec = eye_c[s]
        n0 = len(bro_P)
        n_ = 7
        for i in range(n_):
            f = i / (n_ - 1)
            x = ec[0] + sx * (-0.012 + f * 0.042) * k
            y = ec[1] + (0.018 + 0.006 * math.sin(f * math.pi)) * k - 0.002 * f * k
            for w_ in (-1, 1):
                yy = y + w_ * (0.0035 - 0.0015 * f) * k
                # on the skin: the most forward head vertex near (x, yy)
                near = np.abs(hp[:, 0] - x) + np.abs(hp[:, 1] - yy)
                cand = hp[near < 0.008 * k]
                zz = cand[:, 2].max() if len(cand) else ec[2] + 0.012
                bro_P.append([x, yy, zz + 0.0018])
                bro_UV.append([f, (w_ + 1) / 2])
        for i in range(n_ - 1):
            a = n0 + i * 2
            if sx > 0:
                bro_T += [(a, a + 2, a + 1), (a + 1, a + 2, a + 3)]
            else:
                bro_T += [(a, a + 1, a + 2), (a + 1, a + 3, a + 2)]
    bro_P = np.array(bro_P)
    out["Brauen"] = {"P": bro_P, "N": np.tile([0, 0.3, 0.95], (len(bro_P), 1)), "UV": np.array(bro_UV),
                     "C": np.full((len(bro_P), 3), 0.55), "J": np.tile([jh, 0, 0, 0], (len(bro_P), 1)),
                     "W": np.tile([1.0, 0, 0, 0], (len(bro_P), 1)), "T": np.array(bro_T), "mat": "Hair"}
    # eyes: balls with iris and pupil (looking to +z), eyelashes from the helpers
    eP, eN, eC, eT, eUV = [], [], [], [], []
    for s in "lr":
        hv = V[gverts("helper-%s-eye" % s)]
        ec = hv.mean(axis=0)
        er = np.linalg.norm(hv - ec, axis=1).mean() * 0.97
        n0 = len(eP)
        NR, NS = 12, 16
        for i in range(NR + 1):
            a_ = np.pi * i / NR                        # 0 = front (pupil)
            for j2 in range(NS):
                t_ = 2 * np.pi * j2 / NS
                d = np.array([math.sin(a_) * math.cos(t_), math.sin(a_) * math.sin(t_), math.cos(a_)])
                eP.append(ec + d * er)
                eN.append(d)
                eUV.append([j2 / NS, i / NR])
                if a_ < 0.2:
                    eC.append([0.04, 0.04, 0.04])
                elif a_ < 0.5:
                    ic = np.array(b["eye"])
                    eC.append(list(ic * (0.75 if a_ > 0.42 else 1.0)))
                else:
                    eC.append([0.86, 0.84, 0.8])
        for i in range(NR):
            for j2 in range(NS):
                a = n0 + i * NS + j2
                b2 = n0 + i * NS + (j2 + 1) % NS
                eT += [(a, a + NS, b2), (b2, a + NS, b2 + NS)]
    eP = np.array(eP)
    out["Augen"] = {"P": eP, "N": np.array(eN), "UV": np.array(eUV), "C": np.array(eC), "J": np.tile([jh, 0, 0, 0], (len(eP), 1)),
                    "W": np.tile([1.0, 0, 0, 0], (len(eP), 1)), "T": np.array(eT), "mat": "Eye"}
    lf = [faces[i][1] for g in groups if g.startswith("helper-") and "eyelashes" in g for i in groups[g]]
    if lf:
        corners = sorted({(v, t) for c in lf for v, t in c})
        ci = {c: i for i, c in enumerate(corners)}
        vi = np.array([v for v, _ in corners])
        tris = np.array([(ci[a], ci[b2], ci[c2]) for c in lf for a, b2, c2 in tri_of([c])])
        P = V[vi]
        out["Wimpern"] = {"P": P, "N": normals(P, tris), "UV": np.array([VT[t] if t >= 0 else [0, 0] for _, t in corners]),
                          "C": np.full((len(vi), 3), 0.35), "J": top[vi], "W": tw[vi], "T": tris, "mat": "Hair"}
    # ---- skeleton nodes (rest = Quaternius pose with these bone lengths) and inverse bind matrices (A pose of the body)
    glb = GLB()
    nodes = glb.j["nodes"]
    nodes.append({"name": "Armature", "children": []})
    node_of = {}
    for nm in joints:
        node_of[nm] = len(nodes)
        nodes.append({"name": nm})
    bind = {}
    for nm in joints:
        if nm in bones:
            p = bones[nm]["parent"]
            if nm == "root":
                r = GQ["root"]
                t = np.zeros(3)
            else:
                r = qmul(qinv(GQ[p]), GQ[nm])
                t = qrot(qinv(B[p]), bones[nm]["head"] - bones[p]["head"])
            bind[nm] = (B[nm], bones[nm]["head"])
        else:
            p = PQ[nm]
            r = LQ[nm]
            t = TQ[nm]
            pb = bind[p]
            bind[nm] = (qmul(pb[0], r), pb[1] + qrot(pb[0], t))
        nd = nodes[node_of[nm]]
        nd["rotation"] = [float(x) for x in (r / np.linalg.norm(r))]
        nd["translation"] = [float(x) for x in t]
        if nm == "root":
            nodes[0]["children"].append(node_of[nm])
        else:
            nodes[node_of[p]].setdefault("children", []).append(node_of[nm])
    ibm = []
    for nm in joints:
        q, pos = bind[nm]
        M = np.eye(4)
        M[:3, :3] = qmat(q)
        M[:3, 3] = pos
        ibm.append(np.linalg.inv(M).T.reshape(-1))          # column-major
    ibm_acc = glb.acc(np.array(ibm, np.float32), 5126, "MAT4")
    glb.j["skins"].append({"joints": [node_of[n] for n in joints], "inverseBindMatrices": ibm_acc, "skeleton": node_of["root"]})
    nverts = 0
    ntris = 0
    for pn, d in out.items():
        P = d["P"].astype(np.float32)
        Wq = np.round(np.clip(d["W"], 0, 1) * 255).astype(np.int32)
        diff = 255 - Wq.sum(axis=1)
        Wq[np.arange(len(Wq)), np.argmax(Wq, axis=1)] += diff
        Jq = np.array(d["J"], np.int64)
        Jq[Wq == 0] = 0
        cols = np.clip(np.hstack([np.array(d["C"]), np.ones((len(P), 1))]) * 255, 0, 255).astype(np.uint8)
        nn = np.array(d["N"], np.float32)
        nn /= np.maximum(1e-6, np.linalg.norm(nn, axis=1))[:, None]
        T = np.array(d["T"], np.uint16 if len(P) < 65535 else np.uint32).reshape(-1)
        attrs = {"POSITION": glb.acc(P, 5126, "VEC3", target=34962, minmax=True),
                 "NORMAL": glb.acc(nn, 5126, "VEC3", target=34962),
                 "TEXCOORD_0": glb.acc(np.array(d["UV"], np.float32), 5126, "VEC2", target=34962),
                 "COLOR_0": glb.acc(cols, 5121, "VEC4", normalized=True, target=34962),
                 "JOINTS_0": glb.acc(Jq.astype(np.uint8), 5121, "VEC4", target=34962),
                 "WEIGHTS_0": glb.acc(Wq.astype(np.uint8), 5121, "VEC4", normalized=True, target=34962)}
        ia = glb.acc(T, 5123 if T.dtype == np.uint16 else 5125, "SCALAR", target=34963)
        glb.j["meshes"].append({"name": pn, "primitives": [{"attributes": attrs, "indices": ia, "material": glb.mat(d["mat"])}]})
        nodes.append({"name": pn, "mesh": len(glb.j["meshes"]) - 1, "skin": 0})
        nodes[0]["children"].append(len(nodes) - 1)
        nverts += len(P)
        ntris += len(T) // 3
    info = {"sex": b["sex"], "alter": b["alter"], "bau": b["bau"], "hoehe": round(float(hgt), 3),
            "becken": round(float(qrot(qinv(GQ["root"]), bones["pelvis"]["head"])[2]), 4),
            "haare": HAIRS[hk], "ecken": nverts, "dreiecke": ntris}
    return glb.write(), info


def main():
    data, fig_zip, out_zip = sys.argv[1], sys.argv[2], sys.argv[3]
    base = load_obj(os.path.join(data, "3dobjs", "base.obj"))
    rig = json.load(open(os.path.join(data, "rigs", "standard", "rig.game_engine.json")))
    wts = json.load(open(os.path.join(data, "rigs", "standard", "weights.game_engine.json")))["weights"]
    masks = {}
    for m in ("lips", "fingernails", "toenails", "eyelids", "ears"):
        im = Image.open(os.path.join(data, "textures", "mpfb_%s.jpg" % m)).convert("L").resize((512, 512))
        masks[m] = np.array(im, np.float32)
    qr = quaternius_rest(fig_zip)
    man = {"version": VERSION, "name": "MakeHuman-Menschen", "license": "CC0 1.0 (MakeHuman / MPFB2, Quaternius)",
           "koerper": {}, "anims": {}}
    fz = zipfile.ZipFile(fig_zip)
    fman = json.loads(fz.read("figuren.json"))
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for key, b in BODIES.items():
            data_glb, info = build_body(data, key, b, base, rig, wts, masks, qr)
            fn = "koerper_%s.glb" % key
            z.writestr(fn, data_glb)
            info["file"] = fn
            man["koerper"][key] = info
            print("%-12s %6d Ecken %6d Dreiecke  %.2f m  Becken %.3f  %d KB" % (key, info["ecken"], info["dreiecke"], info["hoehe"],
                                                                             info["becken"], len(data_glb) // 1024))
        for nm, f in fman["anims"].items():
            man["anims"][nm] = f
        for f in sorted(set(fman["anims"].values())):
            z.writestr(f, fz.read(f))
        lic = ("Menschen-Paket für den MoveEye-Simulator (werkzeuge/menschen_paket.py)\n\n"
               "Körper, Formen (targets), Skelett und Gewichte: MakeHuman / MPFB2, https://github.com/makehumancommunity/mpfb2\n"
               "  (src/mpfb/data, LICENSE.ASSETS.md: CC0 1.0 Universal; Copyright vor der Freigabe: Data Collection AB,\n"
               "  Joel Palmius, Jonas Hauquier).\n"
               "Bewegungen (anim_1.glb, anim_2.glb): Quaternius «Universal Animation Library» 1 + 2, CC0 1.0, https://quaternius.com\n"
               "Haare, Kleider, Augen, Brauen, Kapuze: aus den Körpern berechnet (MoveEye, gleiche Bedingungen).\n"
               "CC0: https://creativecommons.org/publicdomain/zero/1.0/\n")
        z.writestr("LIZENZ.txt", lic)
        z.writestr("menschen.json", json.dumps(man, indent=1, ensure_ascii=False))
    open(out_zip, "wb").write(zbuf.getvalue())
    print("%s: %.2f MB" % (out_zip, len(zbuf.getvalue()) / 1048576.0))


if __name__ == "__main__":
    main()
