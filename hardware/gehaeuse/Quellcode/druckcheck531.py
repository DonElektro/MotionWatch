"""5.3.1 Druck-Check: kleinste Wandstärke des Adapters 28 (Methode druckcheck52.thickness).   python3 druckcheck531.py"""
import sys, time, numpy as np
import upsalt531
from druckcheck52 import thickness

PARTS = {"adapter": (upsalt531.part_adapter, 0.2)}

if __name__ == "__main__":
    for k in (sys.argv[1:] or list(PARTS)):
        fn, h = PARTS[k]
        t0 = time.time()
        w, p = thickness(fn(), h)
        thin = w < 1.2
        print(f"{k:10s} min {w[0]:.2f} mm bei {np.round(p[0], 1).tolist()}  5% {np.percentile(w, 5):.2f}  "
              f"Punkte <1,2 mm: {int(thin.sum())} von {len(w)}  Orte: {[np.round(x, 0).tolist() for x in p[:4]]}  ({time.time() - t0:.0f}s)", flush=True)
