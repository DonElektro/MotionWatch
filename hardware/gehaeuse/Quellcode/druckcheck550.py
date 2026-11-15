"""5.5.0 Druck-Check: kleinste Wandstärke der Schutzschale 31 / 32 und des Stopfens 33 (Methode druckcheck52.thickness).
python3 druckcheck550.py [vorne] [hinten] [stopfen]"""
import sys, time, numpy as np
import schale550 as s
from druckcheck52 import thickness

PARTS = {"vorne": (s.part_vorne, 0.4), "hinten": (s.part_hinten, 0.4), "stopfen": (s.part_stopfen, 0.25)}

if __name__ == "__main__":
    for k in (sys.argv[1:] or list(PARTS)):
        fn, h = PARTS[k]
        t0 = time.time()
        w, p = thickness(fn(), h)
        thin = w < 1.2
        print(f"{k:10s} min {w[0]:.2f} mm bei {np.round(p[0], 1).tolist()}  5% {np.percentile(w, 5):.2f}  "
              f"Punkte <1,2 mm: {int(thin.sum())} von {len(w)}  Orte: {[np.round(x, 0).tolist() for x in p[:6]]}  ({time.time() - t0:.0f}s)", flush=True)
