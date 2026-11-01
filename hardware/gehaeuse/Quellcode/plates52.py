"""v5.2: 3MF-Platten für den Bambu Lab X2D (Nutzfläche 230 x 249, Packung 224 x 246 mit Rand).
Geänderte/neue Teile aus out52, unveränderte aus out51 – fehlt out51, kommen sie aus der 3MF-Platte v5.1 im Repository
(Druckdateien/MotionWatch_v5-1_Platte_*.3mf, gleiche Netze).
python3 plates52.py        -> Platte A (Unterteil v5.2, Zwischenboden, HDMI-Stopfen, Füsse, Blindstopfen)
python3 plates52.py A B    -> auch Platte B (braucht out52/06_Kamerakopf_v52, 14, 15)
python3 plates52.py A B C  -> dazu Platte C «Stopfen» (nur wenn Stopfen auf A / B keinen Platz haben)
01.11.2026: Stopfen 19–21 auf Platte A, 18 auf Platte B (Pakete: Basis braucht 19–21, 18 ist für einen Kopf ohne Wärmebild).
Fehlt ein Teil v5.2 in out52 (z. B. das Unterteil, Export ca. 30 min), kommt es aus der 3MF-Platte v5.2 im Repository."""
import os, sys, re, zipfile, numpy as np
from export import write_3mf
HIER = os.path.dirname(os.path.abspath(__file__))
V51 = {"A": os.path.join(HIER, "..", "Druckdateien", "MotionWatch_v5-1_Platte_A_Unterteil.3mf"),
       "B": os.path.join(HIER, "..", "Druckdateien", "MotionWatch_v5-1_Platte_B_Deckel_Kopf.3mf")}
V52 = {"A": os.path.join(HIER, "..", "Druckdateien", "v5-2", "MotionWatch_v5-2_Platte_A_Unterteil.3mf"),
       "B": os.path.join(HIER, "..", "Druckdateien", "v5-2", "MotionWatch_v5-2_Platte_B_Deckel_Kopf.3mf")}
_cache = {}


def from_3mf(name, quellen=None):
    """ein Teil (Objekt-Name) aus den 3MF-Platten v5.1 lesen: Netz wie in out51 (schon in Druckrichtung)"""
    for fn in (quellen or V51).values():
        if not os.path.exists(fn):
            continue
        if fn not in _cache:
            with zipfile.ZipFile(fn) as z:
                _cache[fn] = z.read("3D/3dmodel.model").decode()
        xml = _cache[fn]
        m = re.search(r'<object id="\d+" name="%s(?:_1)?" type="model"><mesh><vertices>(.*?)</vertices><triangles>(.*?)</triangles>' % re.escape(name), xml)
        if m:
            v = np.array(re.findall(r'x="([-\d.]+)" y="([-\d.]+)" z="([-\d.]+)"', m.group(1)), float)
            f = np.array(re.findall(r'v1="(\d+)" v2="(\d+)" v3="(\d+)"', m.group(2)), int)
            return v, f
    raise FileNotFoundError(name)
BW, BH, GAP = 224.0, 246.0, 5.0
NEW = {"01_Unterteil_v52", "06_Kamerakopf_v52", "10_Stopfen_HDMI_USB_v52", "16_Stopfen_SD_v52", "13_Entwicklungs_Sockel", "17_Blindstopfen_Reserve", "12_Blindstopfen_Weitwinkel", "13_Stopfen_IR_LED", "14_Diffusor_Status_LED", "15_Pupillenring",
       "18_Stopfen_Waermebild", "19_Stopfen_IR_Modul", "20_Stopfen_DS18B20", "21_Stopfen_Relais"}
def load(n):
    p = f"{'out52' if n in NEW else 'out51'}/{n}.npz"
    if n not in NEW and not os.path.exists(p):
        return from_3mf(n)
    if n in NEW and not os.path.exists(p):
        return from_3mf(n, V52)
    d = np.load(p); return d["v"], d["f"]
def pack(items):
    """items: list of (name, v, f); einfache Reihen-Packung, grösstes zuerst."""
    items = sorted(items, key=lambda t: -(t[1].max(0)[1] - t[1].min(0)[1]) * 1000 - (t[1].max(0)[0] - t[1].min(0)[0]))
    x = y = rowh = 0.0; out = []
    for name, v, f in items:
        w, h = (v.max(0) - v.min(0))[:2]
        if x + w > BW:
            x = 0; y += rowh + GAP; rowh = 0
        assert y + h <= BH, f"{name} passt nicht"
        out.append((name, v, f, (x + w / 2 + 3, y + h / 2 + 3)))
        x += w + GAP; rowh = max(rowh, h)
    return out
def expand(names):
    res = []
    for n in names:
        v, f = load(n)
        k = 4 if n.endswith("_4x") else 2 if n.endswith("_2x") else 1
        res += [(n if k == 1 else f"{n}_{i+1}", v, f) for i in range(k)]
    return res
if __name__ == "__main__":
    import v52
    sel = sys.argv[1:] or ["A"]
    plates = {}
    if "A" in sel:
        a = ["01_Unterteil_v52", "09_Zwischenboden", "10_Stopfen_HDMI_USB_v52", "11_Fuss_4x", "12_Blindstopfen_Weitwinkel", "16_Stopfen_SD_v52", "17_Blindstopfen_Reserve",
             "19_Stopfen_IR_Modul", "20_Stopfen_DS18B20", "21_Stopfen_Relais"]
        if v52.IR_TYP == "5mm":
            a.append("13_Stopfen_IR_LED")
        plates["A"] = ("out52/MotionWatch_v5-2_Platte_A_Unterteil.3mf", pack(expand(a)))
    if "B" in sel:
        plates["B"] = ("out52/MotionWatch_v5-2_Platte_B_Deckel_Kopf.3mf",
                       pack(expand(["02_Deckel_mit_Laufring", "03_Drehteller", "04_Gabel_mit_Arm1", "05_Arm2_Lagerseite", "06_Kamerakopf_v52",
                                    "07_Seitendeckel", "08_Lampenhalter_2x", "14_Diffusor_Status_LED", "15_Pupillenring", "18_Stopfen_Waermebild"])))
    if "C" in sel:                                       # Ausweich-Platte «Stopfen» (alle Stopfen 12, 17–21)
        plates["C"] = ("out52/MotionWatch_v5-2_Platte_C_Stopfen.3mf",
                       pack(expand(["12_Blindstopfen_Weitwinkel", "17_Blindstopfen_Reserve", "18_Stopfen_Waermebild", "19_Stopfen_IR_Modul",
                                    "20_Stopfen_DS18B20", "21_Stopfen_Relais"])))
    for nm, (fn, P) in plates.items():
        write_3mf(fn, P)
        xs = []; ys = []
        for n, v, f, o in P:
            e = v.max(0) - v.min(0); lo = np.array(o) - e[:2] / 2; hi = np.array(o) + e[:2] / 2
            xs += [lo[0], hi[0]]; ys += [lo[1], hi[1]]
            print(nm, n, np.round(o, 1), np.round(e, 1))
        print(nm, "belegt x %.1f..%.1f  y %.1f..%.1f (Platte 230 x 249)" % (min(xs), max(xs), min(ys), max(ys)), fn, os.path.getsize(fn) // 1024, "KB")
        assert max(xs) <= 230 and max(ys) <= 249 and min(xs) >= 0 and min(ys) >= 0
        R = [(np.array(o) - (v.max(0) - v.min(0))[:2] / 2, np.array(o) + (v.max(0) - v.min(0))[:2] / 2) for n, v, f, o in P]
        for i in range(len(R)):
            for j in range(i + 1, len(R)):
                assert np.any(R[i][1] <= R[j][0]) or np.any(R[j][1] <= R[i][0]), (P[i][0], P[j][0])
