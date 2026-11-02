#!/usr/bin/env python3
"""Druck-Lage: wie jedes Druckteil auf der Druckplatte liegt (Einzelteil-Vorschau «Bauen», Paket real-einzelteil-vorschau, 01.11.2026).

Liest das Modell der Werkstatt (simulator3d/inhalte/gehaeuse/gehaeuse.glb: ein Netz pro Teil, in Einbaulage, Godot-Meter) und die
3MF in hardware/gehaeuse/Druckdateien/ (Einzelteile: schon in Druckrichtung gedreht, Platten A / B: alle Teile verteilt) und sucht
pro Druckteil die Drehung (eine der 24 rechtwinkligen), die das Netz der Werkstatt am besten auf das Netz der 3MF legt
(Abstand von Stichproben-Punkten). Daraus entsteht eine kleine Datei – die Werkstatt dreht nur ihr vorhandenes Netz, es kommen
keine weiteren Modelle dazu:

    simulator3d/inhalte/gehaeuse/druck_lage.json   (Simulator: werkstatt.gd)
    quelle/639wb_daten_druck_lage.py               (MoveEye «Bauen»: GEH_DRUCK_LAGE, 639wc)

Koordinaten (wie die Werkstatt, Godot / three.js): Meter, Y oben. «r» (3 × 3, zeilenweise) und «t»: p' = r · p + t legt das Teil
so, wie es gedruckt wird: Mitte über (0, 0), Unterseite auf y = 0. Platte: x / y in mm wie in der 3MF (0 … 256), in der Werkstatt
X = x − 128, Z = 128 − y. «g»: Grösse in mm (x, y, z der Druckplatte), «f»: mittlere Abweichung in mm (Kontrolle).
Teile der Platte ohne eigenes Netz in der Werkstatt (z. B. kleine Stopfen) zeigt die Vorschau als Quader mit «g».

    python3 werkzeuge/druck_lage.py            # neu rechnen und schreiben
    python3 werkzeuge/druck_lage.py --pruefen  # nur prüfen (Exit 1, wenn die Dateien nicht zum Modell / zu den 3MF passen)
"""
import argparse
import hashlib
import itertools
import json
import os
import re
import struct
import sys
import zipfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEH = os.path.join(ROOT, "hardware", "gehaeuse")
DD = os.path.join(GEH, "Druckdateien")
GLB = os.path.join(ROOT, "simulator3d", "inhalte", "gehaeuse", "gehaeuse.glb")
OUT_SIM = os.path.join(ROOT, "simulator3d", "inhalte", "gehaeuse", "druck_lage.json")
OUT_MW = os.path.join(ROOT, "quelle", "639wb_daten_druck_lage.py")
PLATTE_MM = 256
VARIANTEN = {"v52": ("v5-2/", "v5-2/MoveEye_v5-2_"), "v51": ("", "MoveEye_v5-1_"),
             "v53": ("v5-3/", "v5-3/MoveEye_v5-3_")}          # real-gehaeuse-v53 (v5.3 baut auf v5.2 auf; Reihenfolge = Vorrang)


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def lies_glb(p):
    """{name: Ecken (N, 3) float64, Godot-Meter}"""
    with open(p, "rb") as f:
        b = f.read()
    n_js = struct.unpack_from("<I", b, 12)[0]
    js = json.loads(b[20:20 + n_js])
    o = 20 + n_js
    n_bin = struct.unpack_from("<I", b, o)[0]
    binb = b[o + 8:o + 8 + n_bin]
    out = {}
    for nd in js["nodes"]:
        if "mesh" not in nd:
            continue
        acc = js["accessors"][js["meshes"][nd["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
        bv = js["bufferViews"][acc["bufferView"]]
        a = np.frombuffer(binb, np.float32, acc["count"] * 3, bv.get("byteOffset", 0) + acc.get("byteOffset", 0)).reshape(-1, 3)
        out[nd["name"]] = a.astype(np.float64)
    return out


_V = re.compile(rb'<vertex x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"\s*/>')
_T = re.compile(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"')


def volumen_3mf(p):
    """Volumen des ersten Objekts in cm³ (geschlossenes Netz, Divergenz-Satz)"""
    with zipfile.ZipFile(p) as z:
        x = z.read("3D/3dmodel.model")
    m = re.search(rb'<object id="\d+"[^>]*>(.*?)</object>', x, re.S)
    v = np.array(_V.findall(m.group(1)), dtype=np.float64)
    f = np.array(_T.findall(m.group(1)), dtype=np.int64)
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    return abs(float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0) / 1000.0


def lies_3mf(p):
    """[(Objekt-Name, Ecken mm (N, 3), Verschiebung (x, y, z) mm)] in der Reihenfolge der Platte"""
    with zipfile.ZipFile(p) as z:
        x = z.read("3D/3dmodel.model")
    objs = {}
    for m in re.finditer(rb'<object id="(\d+)"[^>]*name="([^"]*)"[^>]*>(.*?)</object>', x, re.S):
        v = np.array(_V.findall(m.group(3)), dtype=np.float64)
        objs[m.group(1).decode()] = (m.group(2).decode(), v)
    out = []
    for m in re.finditer(rb'<item objectid="(\d+)"[^>]*?(?:transform="([^"]*)")?\s*/>', x):
        tr = [float(s) for s in (m.group(2) or b"1 0 0 0 1 0 0 0 1 0 0 0").split()]
        nm, v = objs[m.group(1).decode()]
        out.append((nm, v, tr[9:12]))
    return out


def drehungen():
    """die 24 rechtwinkligen Drehungen (Determinante +1)"""
    rs = []
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            m = np.zeros((3, 3))
            for i in range(3):
                m[i, perm[i]] = sg[i]
            if round(np.linalg.det(m)) == 1:
                rs.append(m)
    return rs


# Druckplatte (3MF, mm, z oben) -> Werkstatt (Godot / three, m, Y oben): X = x, Y = z, Z = -y
Q = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])


def stichprobe(v, n=1500, seed=1):
    if len(v) <= n:
        return v
    return v[np.random.default_rng(seed).choice(len(v), n, replace=False)]


def lege(v):
    """Mitte der Grundfläche auf (0, 0), Unterseite auf z = 0 (wie export.orient)"""
    v = v.copy()
    v[:, 2] -= v[:, 2].min()
    v[:, :2] -= (v[:, :2].min(0) + v[:, :2].max(0)) / 2
    return v


def abstand(a, b):
    from scipy.spatial import cKDTree
    return float((cKDTree(b).query(a)[0].mean() + cKDTree(a).query(b)[0].mean()) / 2)


def beste_lage(glb_m, ziel_mm):
    """Drehung r (Werkstatt -> Werkstatt, gedruckt) und t, mittlere Abweichung in mm"""
    a0 = stichprobe(glb_m * 1000.0)
    b = stichprobe(lege(ziel_mm))
    ext_b = b.max(0) - b.min(0)
    best = None
    for R in drehungen():            # R: Werkstatt-Achsen -> 3MF-Achsen
        a = lege(a0 @ R.T)
        if np.abs((a.max(0) - a.min(0)) - ext_b).max() > 6.0:
            continue
        f = abstand(a, b)
        if best is None or f < best[0]:
            best = (f, R)
    if best is None:
        return None
    f, R = best
    full = Q @ R                      # Werkstatt -> 3MF -> Werkstatt (gedruckt)
    p = glb_m @ full.T
    t = np.array([-(p[:, 0].min() + p[:, 0].max()) / 2, -p[:, 1].min(), -(p[:, 2].min() + p[:, 2].max()) / 2])
    return full, t, f


def rechnen():
    bau = json.load(open(os.path.join(GEH, "bau.json"), encoding="utf-8"))
    netze = lies_glb(GLB)
    teile = bau["teile"]
    einzeln = set(bau.get("druckdateien_einzeln") or [])
    lage, meld = {}, []
    for t in teile:
        d = t.get("datei")
        if not d or t["id"] not in netze:
            continue
        for var, (pre, pre1) in VARIANTEN.items():
            f = pre1 + d + ".3mf"
            if f in einzeln and os.path.isfile(os.path.join(DD, f)):
                break
        else:
            meld.append("keine 3MF für " + t["id"])
            continue
        objs = lies_3mf(os.path.join(DD, f))
        v = objs[0][1] if len(objs) == 1 else None
        if v is None:                  # mehrere Stück in einer Datei (z. B. 4 Füsse): das erste
            v = objs[0][1]
        r = beste_lage(netze[t["id"]], v)
        if r is None:                  # e.g. the 4 feet are one net in the model, 4 objects in the 3MF: as built (pin up)
            meld.append("keine passende Lage, wie eingebaut: %s (%s)" % (t["id"], f))
            p = netze[t["id"]]
            r = (np.eye(3), np.array([-(p[:, 0].min() + p[:, 0].max()) / 2, -p[:, 1].min(), -(p[:, 2].min() + p[:, 2].max()) / 2]), 99.0)
        full, tt, fe = r
        g = np.ptp(netze[t["id"]] @ full.T, axis=0) * 1000.0          # Werkstatt X, Y (oben), Z -> Platte x, y, z
        lage[t["id"]] = {"datei": d, "r": [round(float(x), 6) for x in full.ravel()], "t": [round(float(x), 6) for x in tt],
                         "g": [round(float(g[0]), 1), round(float(g[2]), 1), round(float(g[1]), 1)], "f": round(fe, 2)}
        if fe > 5.0:
            lage[t["id"]]["unsicher"] = True
            meld.append("Lage unsicher (%.1f mm): %s" % (fe, t["id"]))
    # pro Druckdatei: Farbe (wie werkzeuge/bausatz.py druck_farbe) und Gewicht (Schätzung aus dem Volumen, PETG 1,27 g/cm³)
    kopf = set((bau.get("farben") or {}).get("kopf_teile") or [])
    dateien = {}
    for p in (bau.get("druck") or {}).get("teile") or []:
        d = p["datei"]
        f = next((pre1 + d + ".3mf" for var, (pre, pre1) in VARIANTEN.items() if pre1 + d + ".3mf" in einzeln
                  and os.path.isfile(os.path.join(DD, pre1 + d + ".3mf"))), None)
        ids = [t["id"] for t in teile if t.get("datei") == d]
        farbe = "natur" if d.startswith("14_") else "schwarz" if d.startswith("15_") else "orange" if any(i in kopf for i in ids) else "grau"
        e = {"farbe": farbe}
        if f:
            vol = volumen_3mf(os.path.join(DD, f))
            k = min(1.0, 0.35 + 0.65 * float(p.get("fuellung", 20)) / 100.0)
            e["vol_cm3"] = round(vol, 1)
            e["gramm"] = max(1, int(round(vol * 1.27 * k)))
        dateien[d] = e
    # Grösse jedes Teils der Werkstatt (Bounding Box in Einbaulage, mm: Länge x, Breite y, Höhe z des Modells)
    masse = {}
    for k, v in sorted(netze.items()):
        e = np.ptp(v, axis=0) * 1000.0                       # Godot X = Modell y, Y = z, Z = x
        masse[k] = [round(float(e[2]), 1), round(float(e[0]), 1), round(float(e[1]), 1)]
    # Platten
    platten = {}
    for var, (pre, pre1) in VARIANTEN.items():
        out = []
        for f in bau.get("druckdateien") or []:
            if (f.split("/")[0] + "/" if "/" in f else "") != pre:
                continue
            items = []
            for nm, v, off in lies_3mf(os.path.join(DD, f)):
                ext = v.max(0) - v.min(0)
                cen = (v.max(0) + v.min(0)) / 2
                datei = re.sub(r"_\d+$", "", nm) if not any(x.get("datei") == nm for x in teile) else nm
                nr = re.search(r"_(\d+)$", nm)
                cand = [x["id"] for x in teile if x.get("datei") == datei and (var in ("v52", "v53") or x.get("art") != "v52")
                        and (var == "v53" or x.get("art") != "v53") and not (var == "v51" and x.get("art") == "dev")]
                for va in (("v53", "v52") if var == "v53" else ("v52",) if var == "v52" else ()):
                    cv = [c for c in cand if next(x for x in teile if x["id"] == c).get("art") == va]   # the part of the variant (01_Unterteil_v52 -> tub52)
                    if cv:
                        cand = cv
                        break
                pid = ""
                if cand:
                    pid = cand[int(nr.group(1)) - 1] if nr and datei != nm and len(cand) > 1 and int(nr.group(1)) <= len(cand) else cand[0]
                it = {"o": nm, "datei": datei, "x": round(float(off[0] + cen[0]), 2), "y": round(float(off[1] + cen[1]), 2),
                      "g": [round(float(e), 1) for e in ext]}
                multi = len(cand) == 1 and nr and datei != nm       # e.g. one of 4 feet: the model has all 4 in one net
                if pid and pid in lage and not multi:
                    it["id"] = pid
                elif pid:
                    it["teil"] = pid                                   # the part (info, 3MF) - shown as a box
                items.append(it)
            m = re.search(r"Platte_([A-Z])_", f)
            out.append({"name": m.group(1) if m else str(len(out) + 1), "datei": f, "teile": items})
        platten[var] = out
    return {"_hinweis": "Erzeugt von werkzeuge/druck_lage.py aus gehaeuse.glb und den 3MF in hardware/gehaeuse/Druckdateien/ – nicht "
                        "von Hand ändern. lage[id]: r (3 × 3) und t (m): so liegt das Teil auf der Druckplatte (Werkstatt-Achsen, Y oben, "
                        "Mitte auf 0, Unterseite y = 0), g = Grösse mm, f = Abweichung mm. dateien[datei]: farbe (orange / grau / natur / schwarz), vol_cm3, gramm (Schätzung pro Stück: Volumen × 1,27 g/cm³ × (0,35 + 0,65 × Füllung)). masse[id]: Grösse mm (Länge, Breite, Höhe in Einbaulage). platten: x / y mm wie in der 3MF (0 … 256).",
            "glb_sha256": sha(GLB), "platte_mm": PLATTE_MM, "lage": lage, "dateien": dateien, "masse": masse, "platten": platten}, meld


def als_python(d):
    js = json.dumps(d, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return ("#@ MoveEye – Teil 639wb: Daten Druck-Lage (wie jedes Druckteil auf der Druckplatte liegt, die Platten A / B je Variante) für die "
            "Einzelteil-Vorschau und die Ansicht «Druckplatten» der Seite «Bauen» (639wc). Erzeugt von werkzeuge/druck_lage.py – NICHT VON HAND "
            "ÄNDERN. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.\n"
            "# ----------------------------------------------------------------------------\n"
            "# Dieselben Daten liegen für den Simulator in simulator3d/inhalte/gehaeuse/druck_lage.json (werkstatt.gd).\n"
            "# ----------------------------------------------------------------------------\n"
            "GEH_DRUCK_LAGE = json.loads(r\"\"\"" + js + "\"\"\")\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pruefen", action="store_true")
    a = ap.parse_args()
    d, meld = rechnen()
    sim = json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    py = als_python(d)
    if a.pruefen:
        bad = []
        for p, s in ((OUT_SIM, sim), (OUT_MW, py)):
            if not os.path.isfile(p) or open(p, encoding="utf-8").read() != s:
                bad.append(os.path.relpath(p, ROOT))
        if bad:
            print("Druck-Lage nicht aktuell:", ", ".join(bad), "– python3 werkzeuge/druck_lage.py")
            return 1
        print("Druck-Lage: OK (%d Teile, Platten %s)" % (len(d["lage"]), ", ".join("%s %d" % (k, len(v)) for k, v in d["platten"].items())))
        return 0
    for p, s in ((OUT_SIM, sim), (OUT_MW, py)):
        with open(p, "w", encoding="utf-8") as f:
            f.write(s)
    for k, v in sorted(d["lage"].items()):
        print("%-10s %-28s f=%.2f mm  g=%s%s" % (k, v["datei"], v["f"], v["g"], "  UNSICHER" if v.get("unsicher") else ""))
    for var, ps in d["platten"].items():
        for p in ps:
            print(var, p["name"], [(i["o"], i.get("id") or ("[" + i.get("teil", "") + "]")) for i in p["teile"]])
    for m in meld:
        print("Hinweis:", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
