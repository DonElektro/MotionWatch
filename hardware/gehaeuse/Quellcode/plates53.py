"""v5.3: 3MF-Platten für den Bambu Lab X2D (wie plates52.py). Geänderte / neue Teile aus out53 (export53.py), alle übrigen
aus den Platten v5.2 im Repository (Druckdateien/v5-2/, gleiche Netze).
python3 plates53.py          -> Platten A (Unterteil v5.3 …), B (Deckel v5.3, Kopf …) und C (Halter Wand / Baum)
Fehlt ein Teil v5.3 in out53, kommt es aus der Platte v5.3 im Repository (Druckdateien/v5-3/)."""
import os, sys, numpy as np
from export import write_3mf
import plates52 as p52
HIER = os.path.dirname(os.path.abspath(__file__))
DD = os.environ.get("GEH_DRUCKDATEIEN") or os.path.join(HIER, "..", "Druckdateien")   # gehaeuse_bauen.py --druck53 setzt den Ordner
p52.V52 = {k: os.path.join(DD, "v5-2", os.path.basename(v)) for k, v in p52.V52.items()}
V53 = {k: os.path.join(DD, "v5-3", "MotionWatch_v5-3_Platte_%s.3mf" % n)
       for k, n in (("A", "A_Unterteil"), ("B", "B_Deckel_Kopf"), ("C", "C_Halter"))}
NEW = {"01_Unterteil_v53", "02_Deckel_v53", "25_Halter_Wand_Baum", "26_Akkuklappe", "27_Luftkanal"}
PLATTEN = {
    "A": ["01_Unterteil_v53", "09_Zwischenboden", "10_Stopfen_HDMI_USB_v52", "11_Fuss_4x", "12_Blindstopfen_Weitwinkel", "16_Stopfen_SD_v52",
          "17_Blindstopfen_Reserve", "19_Stopfen_IR_Modul", "20_Stopfen_DS18B20", "21_Stopfen_Relais", "23_Stopfen_Mikrofon",
          "24_Stopfen_Lichtleiter", "27_Luftkanal"],
    "B": ["02_Deckel_v53", "03_Drehteller", "04_Gabel_mit_Arm1", "05_Arm2_Lagerseite", "06_Kamerakopf_v52", "07_Seitendeckel",
          "08_Lampenhalter_2x", "14_Diffusor_Status_LED", "15_Pupillenring", "18_Stopfen_Waermebild"],
    "C": ["25_Halter_Wand_Baum", "26_Akkuklappe"],
}
NAMEN = {"A": "MotionWatch_v5-3_Platte_A_Unterteil.3mf", "B": "MotionWatch_v5-3_Platte_B_Deckel_Kopf.3mf", "C": "MotionWatch_v5-3_Platte_C_Halter.3mf"}


def load(n):
    if n in NEW:
        p = f"out53/{n}.npz"
        if os.path.exists(p):
            d = np.load(p); return d["v"], d["f"]
        return p52.from_3mf(n, V53)
    return p52.from_3mf(n, p52.V52)


def expand(names):
    res = []
    for n in names:
        v, f = load(n)
        k = 4 if n.endswith("_4x") else 2 if n.endswith("_2x") else 1
        res += [(n if k == 1 else f"{n}_{i+1}", v, f) for i in range(k)]
    return res


if __name__ == "__main__":
    os.makedirs("out53", exist_ok=True)
    for nm in (sys.argv[1:] or list(PLATTEN)):
        P = p52.pack(expand(PLATTEN[nm]))
        fn = "out53/" + NAMEN[nm]
        write_3mf(fn, P)
        R = [(np.array(o) - (v.max(0) - v.min(0))[:2] / 2, np.array(o) + (v.max(0) - v.min(0))[:2] / 2) for n, v, f, o in P]
        xs = [r[0][0] for r in R] + [r[1][0] for r in R]; ys = [r[0][1] for r in R] + [r[1][1] for r in R]
        print(nm, "belegt x %.1f..%.1f  y %.1f..%.1f (Platte 230 x 249)" % (min(xs), max(xs), min(ys), max(ys)), fn, os.path.getsize(fn) // 1024, "KB", flush=True)
        assert max(xs) <= 230 and max(ys) <= 249 and min(xs) >= 0 and min(ys) >= 0
        for i in range(len(R)):
            for j in range(i + 1, len(R)):
                assert np.any(R[i][1] <= R[j][0]) or np.any(R[j][1] <= R[i][0]), (P[i][0], P[j][0])
