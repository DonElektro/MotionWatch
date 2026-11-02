"""v5.3 Druck-Check: kleinste Wandstärke der geänderten / neuen Teile (Methode druckcheck52.thickness, Mittelfläche des Materials).
python3 druckcheck53.py [teil ...]   (Teile: tub53 lid53 holder hatch duct)"""
import sys, time, numpy as np
import v53
from druckcheck52 import thickness

PARTS = {"tub53": (v53.part_tub, 0.45), "lid53": (v53.part_lid, 0.4), "holder": (v53.part_holder, 0.35),
         "hatch": (v53.part_hatch, 0.2), "duct": (v53.part_duct, 0.15)}

if __name__ == "__main__":
    for k in (sys.argv[1:] or list(PARTS)):
        fn, h = PARTS[k]
        t0 = time.time()
        w, p = thickness(fn(), h)
        thin = w < 1.2
        print(f"{k:10s} min {w[0]:.2f} mm bei {np.round(p[0], 1).tolist()}  5% {np.percentile(w, 5):.2f}  "
              f"Punkte <1,2 mm: {int(thin.sum())} von {len(w)}  Orte: {[np.round(x, 0).tolist() for x in p[:4]]}  ({time.time() - t0:.0f}s)", flush=True)
