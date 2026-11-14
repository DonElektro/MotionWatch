"""5.4.0 Druck-Check: kleinste Wandstärke der Transportsicherung 29 und der Klammer 30 (Methode druckcheck52.thickness).   python3 druckcheck540.py"""
import sys, time, numpy as np
import kappe540, klammer540
from druckcheck52 import thickness

PARTS = {"kappe": (kappe540.part_kappe, 0.35), "klammer": (klammer540.part_klammer, 0.25)}

if __name__ == "__main__":
    for k in (sys.argv[1:] or list(PARTS)):
        fn, h = PARTS[k]
        t0 = time.time()
        w, p = thickness(fn(), h)
        thin = w < 1.2
        print(f"{k:10s} min {w[0]:.2f} mm bei {np.round(p[0], 1).tolist()}  5% {np.percentile(w, 5):.2f}  "
              f"Punkte <1,2 mm: {int(thin.sum())} von {len(w)}  Orte: {[np.round(x, 0).tolist() for x in p[:4]]}  ({time.time() - t0:.0f}s)", flush=True)
