#!/usr/bin/env python3
"""Figuren-Paket für den 3D-Simulator bauen (F5, 31.10.2026): Quaternius-Figuren (CC0) mit Skelett und Animationen.

Liest die glTF-Dateien von Quaternius (Universal Base Characters, Modular Character Outfits – Fantasy, Universal
Animation Library 1 + 2, alle CC0 1.0) und schreibt ein kleines, nachladbares ZIP für den Simulator:

    figuren.json            Liste der Figuren, Haare, Animationen (Name -> Datei), Version, Lizenz
    kopf_m.glb / kopf_f.glb nur Kopf + Hals + Augen + Brauen der Grundfigur (der Körper steckt in der Kleidung)
    kleid_*.glb             Kleidung (Peasant / Ranger, Mann / Frau) mit Händen, ohne Fantasy-Zubehör
    haar_*.glb              Haare (mit Skelett, gleiche Knochennamen)
    anim_1.glb, anim_2.glb  nur das Skelett + die gebrauchten Animationen (nur Drehungen + Becken-Weg)
    LIZENZ.txt              CC0-Hinweis der drei Pakete

Bilder werden auf 512 px verkleinert (JPEG), Normal- und Rauheitskarten weggelassen; die Kleidung wird hell-grau
(Muster bleibt), damit der Simulator sie pro Figur einfärben kann (Jacke, Hose, Schuhe wie bei den alten Figuren).

    python3 werkzeuge/figuren_paket.py QUELLORDNER AUSGABE.zip

QUELLORDNER: die ausgepackten glTF-Exporte (Ordner base/, outfits/, hair/, gaits.glb, animations.glb, textures/), z. B.
aus dem Download von quaternius.com (Standard-Version) oder einem Spiegel. Das ZIP gehört NICHT ins Simulator-ZIP:
der Simulator lädt es bei Bedarf (Einstellungen → System → Grafik → «Figuren») oder nimmt einen Ordner `figuren/`
neben der .exe.
"""
import hashlib
import io
import json
import os
import struct
import sys
import zipfile

import numpy as np
from PIL import Image

VERSION = 1
TEX = 512
COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

# Kleidung: Datei, weggelassene Teile (Fantasy-Zubehör)
OUTFITS = {
    "kleid_m_peasant": ("outfits/Male_Peasant.gltf", [], "m"),
    "kleid_f_peasant": ("outfits/Female_Peasant.gltf", [], "f"),
    "kleid_m_ranger": ("outfits/Male_Ranger.gltf", ["Acc_Pauldron"], "m"),
    "kleid_f_ranger": ("outfits/Female_Ranger.gltf", ["Acc_Pauldrons", "Arms_Bracer"], "f"),
}
HEADS = {"kopf_m": "base/Superhero_Male_FullBody.gltf", "kopf_f": "base/Superhero_Female_FullBody.gltf"}
HAIRS = {"haar_kurz": "hair/Hair_Buzzed.gltf", "haar_scheitel": "hair/Hair_SimpleParted.gltf",
         "haar_bart": "hair/Hair_Beard.gltf", "haar_lang": "hair/Hair_Long.gltf", "haar_dutt": "hair/Hair_Buns.gltf",
         "haar_kurz_f": "hair/Hair_BuzzedFemale.gltf"}
# Animationen: Datei -> gebrauchte Namen (Gehen, Rennen, Schleichen, Stehen, Sitzen, Telefon, Tragen …)
ANIMS = {
    "anim_1": ("gaits.glb", ["Idle_Loop", "Walk_Loop", "Jog_Fwd_Loop", "Sprint_Loop", "Crouch_Fwd_Loop", "Crouch_Idle_Loop",
                             "Sitting_Idle_Loop", "Sitting_Enter", "Sitting_Exit", "Idle_Talking_Loop", "Walk_Formal_Loop",
                             "Interact", "PickUp_Table", "Push_Loop", "Driving_Loop"]),
    "anim_2": ("animations.glb", ["Idle_TalkingPhone_Loop", "Idle_FoldArms_Loop", "Walk_Carry_Loop", "Idle_Lantern_Loop",
                                  "Yes", "Idle_No_Loop", "LayToIdle"]),
}


def load(path):
    if path.endswith(".glb"):
        b = open(path, "rb").read()
        n = struct.unpack("<I", b[12:16])[0]
        j = json.loads(b[20:20 + n])
        off = 20 + n
        bl = struct.unpack("<I", b[off:off + 4])[0]
        return j, b[off + 8:off + 8 + bl]
    j = json.load(open(path))
    uri = j["buffers"][0]["uri"]
    return j, open(os.path.join(os.path.dirname(path), uri), "rb").read()


class Out:
    """a new glTF: copies what is used from the old one and writes a .glb"""

    def __init__(self, j, binb, src_dir):
        self.j = j
        self.b = binb
        self.src_dir = src_dir
        self.views = []
        self.data = bytearray()
        self.acc = []
        self.acc_map = {}

    def _view(self, raw, target=None):
        while len(self.data) % 4:
            self.data += b"\0"
        v = {"buffer": 0, "byteOffset": len(self.data), "byteLength": len(raw)}
        if target:
            v["target"] = target
        self.data += raw
        self.views.append(v)
        return len(self.views) - 1

    def read(self, ai):
        a = self.j["accessors"][ai]
        v = self.j["bufferViews"][a["bufferView"]]
        dt = COMP[a["componentType"]]
        nc = NCOMP[a["type"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", 0)
        isz = np.dtype(dt).itemsize * nc
        if stride and stride != isz:
            rows = [np.frombuffer(self.b, dt, nc, off + i * stride) for i in range(a["count"])]
            return np.array(rows, dt)
        arr = np.frombuffer(self.b, dt, a["count"] * nc, off)
        return arr.reshape(a["count"], nc) if nc > 1 else arr

    def acc_from(self, ai, arr=None):
        """copy accessor ai (or new data arr with the same type) and return the new index"""
        if arr is None and ai in self.acc_map:
            return self.acc_map[ai]
        a = dict(self.j["accessors"][ai])
        if arr is None:
            arr = self.read(ai)
        arr = np.ascontiguousarray(arr)
        tgt = 34963 if a.get("type") == "SCALAR" and a["componentType"] in (5121, 5123, 5125) and arr.ndim == 1 and ai in self._idx_set else None
        a.pop("byteOffset", None)
        a.pop("sparse", None)
        a["bufferView"] = self._view(arr.tobytes(), tgt)
        a["count"] = int(arr.shape[0])
        if "min" in a and arr.dtype == np.float32:
            mn = arr.min(axis=0) if arr.ndim > 1 else np.array([arr.min()])
            mx = arr.max(axis=0) if arr.ndim > 1 else np.array([arr.max()])
            a["min"] = [float(x) for x in np.atleast_1d(mn)]
            a["max"] = [float(x) for x in np.atleast_1d(mx)]
        self.acc.append(a)
        n = len(self.acc) - 1
        if arr is not None and ai not in self.acc_map:
            self.acc_map[ai] = n
        return n

    _idx_set = set()


def image_bytes(j, binb, src_dir, ii, grey=False):
    im = j["images"][ii]
    if "uri" in im:
        raw = open(os.path.normpath(os.path.join(src_dir, im["uri"])), "rb").read()
    else:
        v = j["bufferViews"][im["bufferView"]]
        raw = binb[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = img.resize((TEX, TEX), Image.LANCZOS)
    if grey:
        # light grey with the pattern kept: the simulator colours it (jacket, trousers, shoes)
        a = np.asarray(img).astype(np.float32) / 255.0
        lum = 0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]
        m = max(1e-3, float(np.percentile(lum, 60)))
        g = np.clip(lum / m * 0.78, 0.0, 1.0)
        img = Image.fromarray((np.stack([g, g, g], -1) * 255).astype(np.uint8))
    bio = io.BytesIO()
    img.save(bio, "JPEG", quality=82, optimize=True)
    return bio.getvalue()


def build_model(path, drop_parts=(), head_only=False, grey_mats=()):
    """a skinned model: nodes (skeleton) as they are, the meshes copied (head_only: only triangles of head and neck),
    materials only with the base colour (small JPEG)"""
    j, binb = load(path)
    src_dir = os.path.dirname(path)
    o = Out(j, binb, src_dir)
    Out._idx_set = {p["indices"] for m in j["meshes"] for p in m["primitives"] if "indices" in p}
    joints = j["skins"][0]["joints"] if j.get("skins") else []
    head_j = [joints.index(i) for i in joints if j["nodes"][i].get("name") in ("Head", "neck_01")]
    nodes = json.loads(json.dumps(j["nodes"]))
    keep_mesh = {}
    meshes = []
    for ni, n in enumerate(nodes):
        if "mesh" not in n:
            continue
        nm = n.get("name", "")
        if any(d in nm for d in drop_parts):
            n.pop("mesh")
            n.pop("skin", None)
            continue
        src = j["meshes"][n["mesh"]]
        prims = []
        for p in src["primitives"]:
            attrs = {}
            for k, ai in p["attributes"].items():
                if k in ("POSITION", "NORMAL", "TEXCOORD_0", "JOINTS_0", "WEIGHTS_0"):
                    attrs[k] = ai
            ind = o.read(p["indices"]).astype(np.uint32)
            if head_only and "Retopology" in src.get("name", "") or (head_only and nm.startswith("SuperHero")):
                jn = o.read(p["attributes"]["JOINTS_0"]).astype(np.int64)
                wt = o.read(p["attributes"]["WEIGHTS_0"]).astype(np.float32)
                if wt.dtype != np.float32 or wt.max() > 1.5:
                    wt = wt / 255.0
                hw = np.zeros(len(jn), np.float32)
                for hj in head_j:
                    hw += (wt * (jn == hj)).sum(axis=1)
                tri = ind.reshape(-1, 3)
                ok = (hw[tri] > 0.5).all(axis=1)
                ind = tri[ok].reshape(-1)
            np_ = {"attributes": {k: o.acc_from(ai) for k, ai in attrs.items()}, "mode": p.get("mode", 4)}
            ia = dict(j["accessors"][p["indices"]])
            ia.pop("byteOffset", None)
            ia["componentType"] = 5125 if ind.max(initial=0) > 65535 else 5123
            arr = ind.astype(np.uint32 if ia["componentType"] == 5125 else np.uint16)
            ia["bufferView"] = o._view(arr.tobytes(), 34963)
            ia["count"] = int(arr.shape[0])
            ia.pop("min", None)
            ia.pop("max", None)
            o.acc.append(ia)
            np_["indices"] = len(o.acc) - 1
            if "material" in p:
                np_["material"] = p["material"]
            prims.append(np_)
        meshes.append({"name": src.get("name", nm), "primitives": prims})
        n["mesh"] = len(meshes) - 1
    # materials: base colour only
    mats = []
    images = []
    textures = []
    for mi, m in enumerate(j.get("materials", [])):
        nm = m.get("name", "")
        pbr = m.get("pbrMetallicRoughness", {})
        nmat = {"name": nm, "doubleSided": bool(m.get("doubleSided", False)),
                "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": float(pbr.get("roughnessFactor", 0.85))}}
        if "baseColorTexture" in pbr:
            ti = pbr["baseColorTexture"]["index"]
            ii = j["textures"][ti]["source"]
            raw = image_bytes(j, binb, src_dir, ii, grey=any(g in nm for g in grey_mats))
            images.append({"bufferView": o._view(raw), "mimeType": "image/jpeg", "name": nm})
            textures.append({"source": len(images) - 1})
            nmat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": len(textures) - 1}
        if m.get("alphaMode"):
            nmat["alphaMode"] = m["alphaMode"]
        if "alphaCutoff" in m:
            nmat["alphaCutoff"] = m["alphaCutoff"]
        mats.append(nmat)
    skins = []
    for s in j.get("skins", []):
        ns = dict(s)
        if "inverseBindMatrices" in s:
            ns["inverseBindMatrices"] = o.acc_from(s["inverseBindMatrices"])
        skins.append(ns)
    out = {"asset": {"version": "2.0", "generator": "MoveEye figuren_paket.py (Quaternius CC0)"},
           "scene": 0, "scenes": j["scenes"], "nodes": nodes, "meshes": meshes, "materials": mats, "skins": skins,
           "accessors": o.acc, "bufferViews": o.views, "buffers": [{"byteLength": len(o.data)}]}
    if images:
        out["images"] = images
        out["textures"] = textures
        out["samplers"] = [{"magFilter": 9729, "minFilter": 9987}]
        for t in textures:
            t["sampler"] = 0
    return glb(out, o.data)


def build_anims(path, names):
    """only the skeleton (no mesh) and the wanted animations: rotations + the way of the pelvis"""
    j, binb = load(path)
    o = Out(j, binb, os.path.dirname(path))
    Out._idx_set = set()
    nodes = json.loads(json.dumps(j["nodes"]))
    for n in nodes:
        n.pop("mesh", None)
        n.pop("skin", None)
    anims = []
    found = []
    for a in j["animations"]:
        if a["name"] not in names:
            continue
        chans = []
        samps = []
        for c in a["channels"]:
            nm = j["nodes"][c["target"]["node"]].get("name", "")
            path_ = c["target"]["path"]
            if path_ == "scale" or (path_ == "translation" and nm != "pelvis"):
                continue
            s = a["samplers"][c["sampler"]]
            samps.append({"input": o.acc_from(s["input"]), "output": o.acc_from(s["output"]),
                          "interpolation": s.get("interpolation", "LINEAR")})
            chans.append({"sampler": len(samps) - 1, "target": {"node": c["target"]["node"], "path": path_}})
        anims.append({"name": a["name"], "channels": chans, "samplers": samps})
        found.append(a["name"])
    miss = [n for n in names if n not in found]
    if miss:
        print("  fehlt:", miss)
    out = {"asset": {"version": "2.0", "generator": "MoveEye figuren_paket.py (Quaternius CC0)"},
           "scene": 0, "scenes": j["scenes"], "nodes": nodes, "animations": anims,
           "accessors": o.acc, "bufferViews": o.views, "buffers": [{"byteLength": len(o.data)}]}
    return glb(out, o.data), found


def glb(j, data):
    js = json.dumps(j, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    data = bytes(data)
    while len(data) % 4:
        data += b"\0"
    total = 12 + 8 + len(js) + 8 + len(data)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(data), 0x004E4942) + data)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    src, dst = sys.argv[1], sys.argv[2]
    files = {}
    man = {"version": VERSION, "name": "Quaternius-Figuren", "license": "CC0 1.0 (Quaternius)",
           "kleider": {}, "koepfe": {}, "haare": {}, "anims": {}}
    for k, p in HEADS.items():
        files[k + ".glb"] = build_model(os.path.join(src, p), head_only=True)
        man["koepfe"][k[-1]] = k + ".glb"
    for k, (p, drop, sex) in OUTFITS.items():
        files[k + ".glb"] = build_model(os.path.join(src, p), drop, grey_mats=("Peasant", "Ranger"))
        man["kleider"][k] = {"file": k + ".glb", "sex": sex, "hood": "ranger" in k}
    for k, p in HAIRS.items():
        files[k + ".glb"] = build_model(os.path.join(src, p))
        man["haare"][k] = {"file": k + ".glb", "sex": "f" if ("lang" in k or "dutt" in k or k.endswith("_f")) else "m"}
    for k, (p, names) in ANIMS.items():
        data, found = build_anims(os.path.join(src, p), names)
        files[k + ".glb"] = data
        for n in found:
            man["anims"][n] = k + ".glb"
    lic = ""
    for f in ["base-license.txt", "outfits-license.txt", "animations-license.txt"]:
        fp = os.path.join(src, f)
        if os.path.exists(fp):
            lic += "== " + f + "\n" + open(fp, encoding="utf-8", errors="replace").read() + "\n"
    files["LIZENZ.txt"] = ("Quaternius – Universal Base Characters, Modular Character Outfits (Fantasy), Universal Animation "
                           "Library 1 + 2 (Standard). CC0 1.0 Universal (Public Domain). https://quaternius.com\n"
                           "Für den MoveEye-3D-Simulator verkleinert (werkzeuge/figuren_paket.py).\n\n" + lic).encode()
    man["files"] = {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}
    files["figuren.json"] = json.dumps(man, indent=1, ensure_ascii=False).encode()
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for k, v in files.items():
            z.writestr(k, v)
    tot = sum(len(v) for v in files.values())
    print("%s: %d Dateien, %.1f MB ausgepackt, ZIP %.1f MB" % (dst, len(files), tot / 1e6, os.path.getsize(dst) / 1e6))
    for k, v in sorted(files.items()):
        print("  %-22s %8.0f KB" % (k, len(v) / 1024))


if __name__ == "__main__":
    main()
