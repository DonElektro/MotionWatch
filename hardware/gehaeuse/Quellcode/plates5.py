import numpy as np, zipfile, shutil, glob, os
from export import write_3mf
BW, BH, GAP = 224.0, 246.0, 5.0
def load(n):
    d = np.load(f"out51/{n}.npz"); return d["v"], d["f"]
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
A = pack(expand(["01_Unterteil", "09_Zwischenboden", "10_HDMI_Stopfen", "11_Fuss_4x"]))
B = pack(expand(["02_Deckel_mit_Laufring", "03_Drehteller", "04_Gabel_mit_Arm1", "05_Arm2_Lagerseite", "06_Kamerakopf", "07_Seitendeckel", "08_Lampenhalter_2x"]))
write_3mf("out51/MotionWatch_v5-1_Platte_A_Unterteil.3mf", A)
write_3mf("out51/MotionWatch_v5-1_Platte_B_Deckel_Kopf.3mf", B)
for nm, P in (("A", A), ("B", B)):
    for n, v, f, o in P: print(nm, n, np.round(o, 1), np.round(v.max(0) - v.min(0), 1))
