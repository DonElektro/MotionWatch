import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import v5, concept_render as cr
cr.COL.update({"lamp1": (0.95,0.55,0.15), "lamp2": (0.95,0.55,0.15), "servo2": (0.15,0.25,0.6), "horn1": (0.9,0.9,0.9), "horn2": (0.9,0.9,0.9),
               "shelf": (0.3,0.5,0.8), "feet": (0.2,0.2,0.2), "relay": (0.2,0.35,0.85), "hub": (0.15,0.15,0.15), "ina": (0.1,0.3,0.8),
               "relayjack": (0.3,0.3,0.3), "probe": (0.75,0.75,0.78)})
from concept_render import render
P = v5.placed(-10, 160)
img, _ = render(P, [-1.25, -1.0, 0.6], W=900, H=780); plt.imsave("v51_a.png", img)
inner = {k: P[k] for k in ("tub","ups","pi","cooler","pca","speaker","mosfet","buck","relay","hub","soundcard","charger","pam","ina","mic","pir","jacks","relayjack","plug","servo1","shelf","feet","probe")}
img, _ = render(inner, [-0.3, -0.55, 1.5], W=1000, H=760); plt.imsave("v51_b.png", img)
P0 = v5.placed(0, 180)
img, _ = render({k: P0[k] for k in ("tub","lid","turntable","yoke","arm2","head","side","lamp1","lamp2","lens_w","lens_ir","feet","plug","probe")}, [1.3, -0.9, 0.45], W=800, H=800); plt.imsave("v51_c.png", img)
