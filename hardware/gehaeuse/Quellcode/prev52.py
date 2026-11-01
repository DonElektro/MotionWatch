"""v5.2: Vorschaubilder -> out52/Vorschau_v5-2_*.png   (python3 prev52.py 2 3 7 8 = nur diese)"""
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import v52, concept_render as cr
from csg import I, box, U, T, R
cr.COL.update({"lamp1": (0.95, 0.55, 0.15), "lamp2": (0.95, 0.55, 0.15), "servo2": (0.15, 0.25, 0.6), "horn1": (0.9, 0.9, 0.9), "horn2": (0.9, 0.9, 0.9),
               "shelf": (0.3, 0.5, 0.8), "feet": (0.2, 0.2, 0.2), "relay": (0.2, 0.35, 0.85), "hub": (0.15, 0.15, 0.15), "ina": (0.1, 0.3, 0.8),
               "relayjack": (0.3, 0.3, 0.3), "probe": (0.75, 0.75, 0.78),
               "wcam": (0.1, 0.55, 0.2), "irled": (0.75, 0.1, 0.1), "btn": (0.1, 0.1, 0.1), "sled": (0.9, 0.9, 0.9), "diff": (0.97, 0.97, 0.92),
               "blind_w": (0.95, 0.75, 0.1), "blind_ir": (0.95, 0.75, 0.1),
               "cam1": (0.85, 0.76, 0.48), "cam0": (0.85, 0.76, 0.48), "cooler": (0.12, 0.12, 0.12), "pi": (0.15, 0.55, 0.25)})
import os
os.makedirs("out52", exist_ok=True)
from concept_render import render
sel = sys.argv[1:]
def save(name, img):
    plt.imsave(f"out52/Vorschau_v5-2_{name}.png", img); print(name, flush=True)
def clipd(P, keys, bx):
    return {k: I(P[k], bx) for k in keys}
if not sel or "1" in sel:                              # Gesamtansicht
    P = v52.placed(-10, 160)
    img, _ = render(P, [-1.25, -1.0, 0.6], W=900, H=780); save("1_Gesamt", img)
if not sel or "2" in sel:                              # Stirnseite nah: Weitwinkel, IR-LED, PIR
    P = v52.placed(0, 180)
    bx = box(-12, 40, 4, 78, 22, 74)
    img, _ = render(clipd(P, ["tub", "wcam", "irled", "pir", "mic", "buck"], bx), [-1.0, -0.35, 0.25], W=900, H=800); save("2_Front_Weitwinkel", img)
if not sel or "3" in sel:                              # Schnitt durch die Kamera (y = 46)
    P = v52.placed(0, 180)
    bx = box(-12, 30, 20, 46, 22, 74)
    img, _ = render(clipd(P, ["tub", "wcam", "pir", "lid", "cam1"], bx), [-0.15, 1.0, 0.1], W=800, H=800); save("3_Schnitt_Weitwinkel", img)
if not sel or "7" in sel:                              # ganzes Unterteil v5.2 von vorne (PIR-Seite), ohne Deckel
    P = v52.placed(0, 180)
    img, _ = render({k: P[k] for k in ("tub", "wcam", "irled", "pir", "feet")}, [-1.0, -0.55, 0.45], W=1000, H=760); save("7_Unterteil_vorne", img)
if not sel or "8" in sel:                              # von oben: Kabelwege CAM0 / CAM1, Kabelkamm, Lüfter frei
    P = v52.placed(0, 180)
    img, _ = render({k: P[k] for k in ("tub", "wcam", "irled", "pir", "pi", "cooler", "ups", "pca", "speaker", "servo1", "cam1", "cam0", "mosfet", "soundcard", "hub")},
                    [-0.25, -0.45, 1.5], W=1100, H=760); save("8_Kabelwege_oben", img)
if not sel or "4" in sel:                              # Stirnseite mit Blindstopfen
    P = v52.placed(0, 180, blinds=True)
    bx = box(-12, 40, 14, 78, 22, 74)
    img, _ = render(clipd(P, ["tub", "blind_w", "blind_ir", "pir", "lid"], bx), [-1.0, -0.35, 0.25], W=900, H=800); save("4_Front_Blindstopfen", img)
if not sel or "5" in sel:                              # Kopf mit Status-LED
    P = v52.placed(0, 135)
    keys = ["head", "side", "diff", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "turntable"]
    img, _ = render({k: P[k] for k in keys}, [-0.6, -0.9, 1.0], W=900, H=800); save("5_Kopf_Status_LED", img)
if not sel or "6" in sel:                              # Rückseite mit Tasten
    P = v52.placed(0, 180)
    bx = box(150, 200, -6, 98, -1, 74)
    img, _ = render(clipd(P, ["tub", "btn", "relayjack", "jacks", "lid"], bx), [1.0, -0.45, 0.3], W=1000, H=760); save("6_Rueckseite_Tasten", img)
