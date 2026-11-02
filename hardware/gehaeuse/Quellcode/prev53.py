"""v5.3: Vorschaubilder vorher (v5.2) / nachher (v5.3) -> out53/Vorschau_*.png   (python3 prev53.py 1 3 = nur diese)
1 Gesamtansicht (v5.3 auf dem Halter)   2 Explosion   3 Unterseite / Akkuklappe offen   4 Halter allein
5 Schnitt durch Luftkanal und Active Cooler (x = 112)   Bilder nur zum Ansehen – Druckdateien: export53.py / plates53.py"""
import os, sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import v5, v52, v53, concept_render as cr
from csg import I, box, T
cr.COL.update({"lamp1": (0.95, 0.55, 0.15), "lamp2": (0.95, 0.55, 0.15), "servo2": (0.15, 0.25, 0.6), "horn1": (0.9, 0.9, 0.9), "horn2": (0.9, 0.9, 0.9),
               "shelf": (0.3, 0.5, 0.8), "feet": (0.2, 0.2, 0.2), "relay": (0.2, 0.35, 0.85), "ina": (0.1, 0.3, 0.8), "relayjack": (0.3, 0.3, 0.3),
               "probe": (0.75, 0.75, 0.78), "wcam": (0.1, 0.55, 0.2), "irled": (0.75, 0.1, 0.1), "btn": (0.1, 0.1, 0.1), "sled": (0.9, 0.9, 0.9),
               "diff": (0.97, 0.97, 0.92), "cam1": (0.85, 0.76, 0.48), "cam0": (0.85, 0.76, 0.48), "hatch": (0.95, 0.75, 0.1),
               "duct": (0.95, 0.35, 0.1), "holder": (0.55, 0.57, 0.62), "tscrew": (0.8, 0.8, 0.8), "cells": (0.25, 0.55, 0.95), "sdext": (0.1, 0.4, 0.2)})
os.makedirs("out53", exist_ok=True)
sel = sys.argv[1:]
W, H = 760, 600
AUSSEN = ("tub", "lid", "turntable", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "head", "side", "diff", "feet", "wcam", "irled", "btn", "jacks", "relayjack")


def save(name, img):
    plt.imsave(f"out53/Vorschau_{name}.png", img); print(name, flush=True)


def P52():
    return v52.placed(-10, 160)


def P53(**k):
    return v53.placed(-10, 160, **k)


if not sel or "1" in sel:
    P = P52(); save("1_Gesamt_v52", cr.render({k: P[k] for k in AUSSEN}, [-1.25, -1.0, 0.6], W=W, H=H)[0])
    P = P53(halter=True); save("1_Gesamt_v53", cr.render({k: P[k] for k in AUSSEN + ("hatch", "holder")}, [-1.25, -1.0, 0.6], W=W, H=H)[0])
if not sel or "2" in sel:
    EXP = {"feet": -30, "hatch": -55, "holder": -110, "tscrew": -110, "ups": 20, "pi": 45, "cooler": 60, "duct": 85, "shelf": 30, "lid": 125,
           "turntable": 160, "yoke": 175, "arm2": 175, "lamp1": 175, "lamp2": 175, "lens_w": 175, "lens_ir": 175, "head": 195, "side": 195, "diff": 195}
    for nm, P, keys in (("2_Explosion_v52", v52.placed(0, 160), ("tub", "lid", "feet", "ups", "pi", "cooler", "shelf", "turntable", "yoke", "arm2", "lamp1", "lamp2", "head", "side", "diff")),
                        ("2_Explosion_v53", v53.placed(0, 160, halter=True), ("tub", "lid", "feet", "hatch", "holder", "tscrew", "ups", "pi", "cooler", "duct", "shelf",
                                                                               "turntable", "yoke", "arm2", "lamp1", "lamp2", "head", "side", "diff"))):
        save(nm, cr.render({k: T([0, 0, EXP.get(k, 0)], P[k]) for k in keys}, [-1.2, -1.0, 0.45], W=W, H=int(H * 1.25))[0])
if not sel or "3" in sel:
    P = v52.placed(0, 180)
    save("3_Unterseite_v52", cr.render({k: P[k] for k in ("tub", "feet")}, [-0.55, -0.8, -1.0], W=W, H=H)[0])
    P = v53.placed(0, 180, klappe_offen=True)
    P["cells"] = v53.cells_dummy()
    save("3_Akkuklappe_offen_v53", cr.render({k: P[k] for k in ("tub", "feet", "hatch", "cells")}, [-0.55, -0.8, -1.0], W=W, H=H)[0])
if not sel or "4" in sel:
    save("4_Halter_v53", cr.render({"holder": v53.part_holder()}, [-0.8, -1.0, 0.75], W=W, H=H)[0])
    P = v53.placed(0, 200, halter=True)
    save("4_Halter_Rueckseite_v53", cr.render({k: P[k] for k in AUSSEN + ("hatch", "holder")}, [0.6, 1.2, 0.35], W=W, H=H)[0])
if not sel or "5" in sel:
    bx = box(60, 112, -12, 70, 30, 75)                         # Schnitt bei x = 112 (Blick von +x), Teile vor dem Schnitt weg
    keys = ("tub", "lid", "pi", "cooler", "duct", "cam0", "cam1", "ups", "plug")
    for nm, P in (("5_Schnitt_Luft_v52", v52.placed(0, 180)), ("5_Schnitt_Luft_v53", v53.placed(0, 180))):
        save(nm, cr.render({k: I(P[k], bx) for k in keys if k in P}, [1.0, -0.35, 0.3], W=W, H=H)[0])
