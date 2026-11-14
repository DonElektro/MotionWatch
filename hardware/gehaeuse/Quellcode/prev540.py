"""5.4.0: Vorschaubilder 29 Transportsicherung -> ../Bilder/Vorschau_v5-4-0_*.png  (python3 prev540.py 1 3)
1 Kappe allein   2 aufgesetzt (Gerät v5.3, Kopf in Grundstellung)   3 Schnitt durch eine Rastzunge am Kabelkamin (y = Zungenmitte)
Bilder nur zum Ansehen."""
import os, sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import kappe540 as k, concept_render as cr
from csg import I, box

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.environ.get("GEH_BILDER") or os.path.join(HIER, "..", "Bilder")
cr.COL.update({"kappe": (0.62, 0.64, 0.68), "lamp1": (0.95, 0.55, 0.15), "lamp2": (0.95, 0.55, 0.15), "diff": (0.95, 0.95, 0.95),
               "sled": (0.9, 0.9, 0.9), "servo2": (0.15, 0.25, 0.6), "horn1": (0.9, 0.9, 0.9), "horn2": (0.9, 0.9, 0.9),
               "feet": (0.2, 0.2, 0.2), "hatch": (0.6, 0.62, 0.66), "wcam": (0.1, 0.55, 0.2), "irled": (0.75, 0.1, 0.1),
               "btn": (0.1, 0.1, 0.1), "sdplug": (0.15, 0.15, 0.15), "resplug": (0.15, 0.15, 0.15), "relayjack": (0.3, 0.3, 0.3),
               "probe": (0.75, 0.75, 0.78), "kabel": (0.85, 0.76, 0.48)})
os.makedirs(ZIEL, exist_ok=True)
sel = sys.argv[1:]
W, H = 760, 600


def save(name, img):
    plt.imsave(os.path.join(ZIEL, f"Vorschau_v5-4-0_{name}.png"), img); print(name, flush=True)


P = k.placed(0, 180)
GERAET = ("tub", "lid", "feet", "hatch", "turntable", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "head", "side", "cam3",
          "therm", "diff", "wcam", "irled", "pir", "jacks", "btn", "sdplug", "plug", "resplug", "relayjack", "probe")
if not sel or "1" in sel:
    save("1_Kappe", cr.render({"kappe": k.part_kappe()}, [-0.8, -1.0, 0.75], W=W, H=H)[0])
if not sel or "2" in sel:
    save("2_aufgesetzt", cr.render({n: P[n] for n in GERAET + ("kappe",) if n in P}, [-0.85, -0.9, 0.55], W=W, H=H)[0])
if not sel or "3" in sel:
    y0, y1 = k.zungen_y(-1)
    yc = (y0 + y1) / 2
    bx = box(k.H_X1 - 6, k.R_X1 + 6, -20, yc, k.v5.LIDTOP - 6, k.DACH_Z1 + 2)
    teile = {n: I(P[n], bx) for n in ("lid", "kappe", "turntable", "yoke", "head", "side")}
    save("3_Schnitt_Rastzunge", cr.render(teile, [0.0, 1.0, 0.12], W=W, H=H)[0])
