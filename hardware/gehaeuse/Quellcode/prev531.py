"""5.3.1: Vorschaubilder Adapter 28 (altes UPS HAT, Variante «tief, gedreht») -> out531/Vorschau_*.png  (python3 prev531.py 1 3)
1 Adapter allein   2 Einbau von oben (ohne Deckel; Zellen im schlimmsten Fall 38 mm ab Platine)
3 Schnitt durch die 8,4-V-Buchse mit Winkelstecker (x = Buchsenmitte)   4 Rückwand von aussen: Ladebuchse in der Reserve-Öffnung
5 Schnitt durch die Zellen (y = Zellenachse): Höhe unter dem Deckel.   Bilder nur zum Ansehen."""
import os, sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import upsalt531 as u, concept_render as cr
from csg import I, box, T

cr.COL.update({"adapter": (0.95, 0.75, 0.1), "hat": (0.05, 0.3, 0.6), "hatunder": (0.15, 0.15, 0.15), "holder18650": (0.55, 0.85, 0.25),
               "hatled": (0.95, 0.1, 0.1), "standoff": (0.8, 0.7, 0.3), "camconn": (0.9, 0.9, 0.9), "cam0": (0.85, 0.76, 0.48),
               "cam1": (0.85, 0.76, 0.48), "plugdummy": (0.1, 0.1, 0.1), "usbplug": (0.75, 0.75, 0.78), "feet": (0.2, 0.2, 0.2),
               "hatch": (0.95, 0.75, 0.1), "relay": (0.2, 0.35, 0.85), "relayjack": (0.3, 0.3, 0.3), "probe": (0.75, 0.75, 0.78),
               "sdext": (0.1, 0.4, 0.2), "sdplug": (0.15, 0.15, 0.15), "btn": (0.1, 0.1, 0.1), "resjack": (0.3, 0.3, 0.3),
               "resplug": (0.15, 0.15, 0.15), "wcam": (0.1, 0.55, 0.2), "irled": (0.75, 0.1, 0.1), "lampdrv": (0.5, 0.5, 0.5),
               "fuseh": (0.9, 0.3, 0.1), "lid": (0.6, 0.62, 0.66), "plug90": (0.1, 0.1, 0.1), "dcsocket": (0.75, 0.75, 0.78),
               "pigtail": (0.85, 0.15, 0.15), "shelf": (0.3, 0.5, 0.8), "charger": (0.1, 0.55, 0.3), "ina": (0.1, 0.3, 0.8)})
os.makedirs("out531", exist_ok=True)
sel = sys.argv[1:]
W, H = 760, 600
STAPEL = ("adapter", "pi", "cooler", "camconn", "standoff", "hat", "hatunder", "holder18650", "hatled")


def save(name, img):
    plt.imsave(f"out531/Vorschau_{name}.png", img); print(name, flush=True)


P = u.placed(0, 180)
STAPEL = STAPEL + ("plug90", "dcsocket", "pigtail")
if not sel or "1" in sel:
    save("1_Adapter", cr.render({"adapter": u.part_adapter()}, [-0.8, -1.0, 0.75], W=W, H=H)[0])
if not sel or "2" in sel:
    keys = ("tub", "hatch", "feet", "pca", "hub", "speaker", "mosfet", "sdext", "relay", "jacks", "btn", "wcam", "irled", "pir", "mic",
            "shelf", "charger", "pam", "ina", "cam0", "cam1") + STAPEL
    save("2_Einbau_oben", cr.render({k: P[k] for k in keys if k in P}, [-0.55, 0.9, 1.3], W=W, H=H)[0])
if not sel or "3" in sel:
    xc = u.jack_world()[0]
    bx = box(xc, 185, -14, 95, 0, 80)
    keys = ("tub", "lid", "shelf", "charger") + STAPEL
    save("3_Schnitt_Buchse", cr.render({k: I(P[k], bx) for k in keys}, [-1.0, 0.35, 0.3], W=W, H=H)[0])
if not sel or "4" in sel:
    bx = box(150, 190, -6, 98, 0, 72)
    keys = ("tub", "lid", "dcsocket", "btn", "jacks", "relayjack")
    save("4_Rueckwand_aussen", cr.render({k: I(P[k], bx) for k in keys if k in P}, [1.0, 0.15, 0.12], W=W, H=H)[0])
if not sel or "5" in sel:
    yc = u.to_world(0, u.HOLDER_Y0 + (u.HOLDER_Y1 - u.HOLDER_Y0) / 4)[1]
    bx = box(30, 182, -14, yc, -8, 90)
    keys = ("tub", "lid", "hatch", "feet", "turntable", "cam0") + STAPEL
    save("5_Schnitt_Hoehe", cr.render({k: I(P[k], bx) for k in keys}, [0.0, 1.0, 0.08], W=W, H=H)[0])
