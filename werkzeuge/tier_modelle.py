#!/usr/bin/env python3
"""Tier-Modelle mit Skelett und Bewegungen für den Simulator («Flora und Fauna», Idee Nr. 5, Phase 1: der Fuchs).

Quelle: Quaternius «Ultimate Animated Animals» (Juli 2021), Datei glTF/Fox.gltf, Lizenz CC0 1.0
(gemeinfrei, https://creativecommons.org/publicdomain/zero/1.0/), https://quaternius.com – dasselbe Paket wie Maggie
(ShibaInu, SHA-256 gleich wie in werkzeuge/maggie_modell.py). Bezogen am 07.11.2026 aus derselben öffentlichen
GitHub-Kopie (laoniutoushx/TD-demo-2024-04-03, «Asserts/Models/ulitimate animals/glTF/»).
SHA-256 der benutzten Datei Fox.gltf: 2f36e3c9c75ecddda85c5f9944e98ee1e88e7c679a546534aff1cea8ecde64c7

Was das Werkzeug macht (alles im Code, keine Handarbeit):
  1. Die fünf Teile (Fell, Schwarz, Augen, Hell, Grau) werden EIN Netz (ein Zeichenaufruf) mit Vertex-Farben.
  2. Fell wie ein echter Rotfuchs: rostrot, Rücken etwas dunkler, Flanke heller und gelblicher, Bauch, Kehle und
     Schwanzspitze weiss, Beine und Ohrrücken schwarz (aus den Teilen des Modells), leichte Unruhe im Fell.
  3. Weiche Normalen (gleiche Punkte zusammengeführt), die Ruhelage jedes Punkts in UV / UV2 (Fellstruktur im Shader
     wandert nicht mit der Bewegung, wie shaders/maggie_fell.gdshader).
  4. Nur die Bewegungen, die der Simulator braucht (Gehen, Galopp, Sprung, Stehen, Kopf tief, Fressen).
Ausgabe: simulator3d/modelle/fuchs_glb.bin (GLB; Endung .bin, damit Godot es nicht importiert – geladen mit
GLTFDocument.append_from_buffer, wie Maggie).

Aufruf: python3 werkzeuge/tier_modelle.py PFAD/Fox.gltf [AUSGABE]
"""
import base64
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

SHA = "2f36e3c9c75ecddda85c5f9944e98ee1e88e7c679a546534aff1cea8ecde64c7"
OUT = Path(__file__).resolve().parent.parent / "simulator3d" / "modelle" / "fuchs_glb.bin"
KEEP_ANIM = ["Walk", "Gallop", "Gallop_Jump", "Idle", "Idle_2", "Idle_2_HeadLow", "Eating"]

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

# Farben (linear, wie Godot Vertex-Farben im Shader liest)
ROST = np.array([0.50, 0.17, 0.045])        # Rotfuchs, Flanke / Rumpf
RUECKEN = np.array([0.34, 0.10, 0.03])      # dunkler Rücken
GELB = np.array([0.58, 0.30, 0.10])         # hellere, gelbliche Flanke und Wangen
WEISS = np.array([0.72, 0.70, 0.64])        # Kehle, Bauch, Schwanzspitze
SCHWARZ = np.array([0.025, 0.022, 0.02])    # Beine, Ohrrücken


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
            arr = np.array([np.frombuffer(buf, dt, n, off + k * stride) for k in range(a["count"])])
        else:
            arr = np.frombuffer(buf, dt, a["count"] * n, off).reshape(a["count"], n) if n > 1 else \
                np.frombuffer(buf, dt, a["count"], off)
        if a.get("normalized") and dt != np.float32:
            arr = arr.astype(np.float64) / np.iinfo(dt).max
        return np.array(arr)
    return d, acc


def noise3(P, f):
    """glattes Wertrauschen 0..1 (fest, ohne Zufall)"""
    q = P * f
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


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "Fox.gltf"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    d, acc = lesen(src)
    mats = [m["name"] for m in d["materials"]]
    prims = d["meshes"][0]["primitives"]
    P, N, J, W, C, I = [], [], [], [], [], []
    base = 0
    for pr in prims:
        a = pr["attributes"]
        p = acc(a["POSITION"]).astype(np.float64)
        P.append(p)
        J.append(acc(a["JOINTS_0"]).astype(np.uint16))
        W.append(acc(a["WEIGHTS_0"]).astype(np.float64))
        C.append(np.full(len(p), mats.index(d["materials"][pr["material"]]["name"])))
        I.append(acc(pr["indices"]).astype(np.int64) + base)
        base += len(p)
    P = np.concatenate(P)
    J = np.concatenate(J)
    W = np.concatenate(W)
    M = np.concatenate(C)
    I = np.concatenate(I).reshape(-1, 3)
    # ---- weiche Normalen: gleiche Punkte (auf 1e-4) teilen sich die Normale ----
    key = np.round(P / 1e-4).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])     # Flächen-Normalen (nach Fläche gewichtet)
    acc_n = np.zeros((inv.max() + 1, 3))
    for k in range(3):
        np.add.at(acc_n, inv[I[:, k]], fn)
    Nn = acc_n[inv]
    Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
    # ---- Farben ----
    jn = [d["nodes"][j]["name"] for j in d["skins"][0]["joints"]]

    def wsum(names):
        idx = [jn.index(n) for n in names if n in jn]
        out_ = np.zeros(len(P))
        for k in range(4):
            out_ += np.where(np.isin(J[:, k], idx), W[:, k], 0.0)
        return out_
    tail = wsum([n for n in jn if n.startswith("Tail")])
    head = wsum(["Head", "Neck3"])
    nz = noise3(P, 3.0)
    y, z = P[:, 1], P[:, 2]
    ymin, ymax = y.min(), y.max()
    yn = (y - ymin) / (ymax - ymin)
    # Grundfarbe aus den Teilen des Modells
    col = np.zeros((len(P), 3))
    name = np.array(mats)[M]
    col[name == "Main"] = ROST
    col[name == "Main_Light"] = WEISS
    col[name == "Black"] = SCHWARZ
    col[name == "Eyes"] = [0.02, 0.015, 0.01]
    col[name == "Grey"] = [0.03, 0.028, 0.026]                      # Nase
    fur = name == "Main"
    # Rücken dunkler (oben am Rumpf), Flanke unten heller / gelblich, Kopf: Wangen gelblicher
    top = sst(0.62, 0.8, yn) * (1 - head) * (1 - tail)
    flank = (1 - sst(0.45, 0.62, yn)) * (1 - tail)
    c2 = ROST * (1 - top[:, None]) + RUECKEN * top[:, None]
    c2 = c2 * (1 - 0.45 * flank[:, None]) + GELB * 0.45 * flank[:, None]
    c2 = np.where(head[:, None] > 0.5, ROST * 0.6 + GELB * 0.4, c2)
    # Schwanz: zur Spitze hin dunkler mit grauem Anflug (die Spitze selbst ist «Main_Light» = weiss)
    zt = (z - z.min()) / max(1e-6, np.ptp(z))
    c2 = np.where(tail[:, None] > 0.5, c2 * (1 - 0.3 * sst(0.0, 0.25, 1 - zt))[:, None], c2)
    col[fur] = c2[fur]
    col *= (1.0 + 0.10 * (nz - 0.5))[:, None]
    col = np.clip(col, 0, 1)
    rest = P.astype(np.float32)
    lo = P[:, 1].min()
    torso = wsum(["Torso", "Torso2", "Torso3", "Back"]) > 0.5
    print("Fuchs: %d Punkte, %d Dreiecke; Höhe %.3f (über Boden %.3f), Länge %.3f, Rücken (Torso) %.4f" % (
        len(P), len(I), y.max(), lo, np.ptp(z), P[torso, 1].max()))
    print("Kopf vorne bei z = %.3f, Schwanz hinten bei z = %.3f" % (z.max(), z.min()))

    # ---- neues glTF: Knoten, Skin und Bewegungen übernehmen, ein Netz ----
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

    def copy_acc(i):
        a = d["accessors"][i]
        arr = acc(i)
        dt = CT[a["componentType"]]
        k = add(arr.astype(dt), a["componentType"], a["type"])
        for f in ("min", "max"):
            if f in a:
                accs[k][f] = a[f]
        return k
    prim = {"attributes": {
        "POSITION": add(P.astype(np.float32), 5126, "VEC3", 34962, minmax=True),
        "NORMAL": add(Nn.astype(np.float32), 5126, "VEC3", 34962),
        "COLOR_0": add((np.concatenate([col, np.ones((len(col), 1))], axis=1) * 255 + 0.5).astype(np.uint8), 5121, "VEC4", 34962, norm=True),
        "TEXCOORD_0": add(rest[:, [0, 1]], 5126, "VEC2", 34962),
        "TEXCOORD_1": add(np.stack([rest[:, 2], np.zeros(len(rest), np.float32)], axis=1), 5126, "VEC2", 34962),
        "JOINTS_0": add(J.astype(np.uint16), 5123, "VEC4", 34962),
        "WEIGHTS_0": add(W.astype(np.float32), 5126, "VEC4", 34962)},
        "indices": add(I.reshape(-1).astype(np.uint16 if len(P) < 65535 else np.uint32), 5123 if len(P) < 65535 else 5125, "SCALAR", 34963),
        "material": 0}
    skin = dict(d["skins"][0])
    skin["inverseBindMatrices"] = copy_acc(skin["inverseBindMatrices"])
    anims = []
    for an in d["animations"]:
        if an["name"] not in KEEP_ANIM:
            continue
        samplers = []
        for s in an["samplers"]:
            samplers.append({"input": copy_acc(s["input"]), "output": copy_acc(s["output"]),
                             "interpolation": s.get("interpolation", "LINEAR")})
        anims.append({"name": an["name"], "samplers": samplers, "channels": an["channels"]})
    g = {"asset": {"version": "2.0", "generator": "MoveEye werkzeuge/tier_modelle.py (Quaternius Fox, CC0)"},
         "scene": 0, "scenes": d["scenes"], "nodes": d["nodes"],
         "meshes": [{"name": "Fuchs", "primitives": [prim]}],
         "materials": [{"name": "Fell", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 0.85}}],
         "skins": [skin], "animations": anims, "accessors": accs, "bufferViews": views,
         "buffers": [{"byteLength": len(blob)}]}
    while len(blob) % 4:
        blob.append(0)
    g["buffers"][0]["byteLength"] = len(blob)
    js = json.dumps(g, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    glb = b"glTF" + struct.pack("<II", 2, 12 + 8 + len(js) + 8 + len(blob))
    glb += struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(blob)) + b"BIN\x00" + bytes(blob)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(glb)
    print("geschrieben: %s (%d Bytes, %d Bewegungen: %s)" % (out, len(glb), len(anims), ", ".join(a["name"] for a in anims)))


if __name__ == "__main__":
    main()
