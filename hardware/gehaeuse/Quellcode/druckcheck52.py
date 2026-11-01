"""v5.2 Druck-Check: kleinste Wandstärke je Druckteil (Mittelfläche des Materials, SDF-Raster) -> Tabelle.
python3 druckcheck52.py [teil ...]   (Teile: tub52 lid turntable yoke arm2 head side lamp shelf plug feet blind)
Methode: Raster mit Schritt h, Abstand zur Oberfläche t = -sdf; Punkte der Mittelfläche = lokale Maxima von t;
Wandstärke = 2 t dort. Genauigkeit ca. ± h. Gemeldet: kleinster Wert, 5-%-Wert, Fläche unter 1,2 mm (3 Linien à 0,4 mm)."""
import sys, time, numpy as np
from scipy import ndimage
import v5, v52, pantilt as pt

PARTS = {"tub52": (v52.part_tub, 0.45), "lid": (v5.part_lid, 0.4), "turntable": (pt.part_turntable, 0.3),
         "yoke": (v5.part_yoke, 0.3), "arm2": (v5.part_arm2, 0.3), "head": (pt.part_head, 0.3), "side": (pt.part_sidecover, 0.3),
         "lamp": (v5.part_lamp, 0.25), "shelf": (v5.part_shelf, 0.25), "plug": (v5.part_hdmi_plug, 0.2), "feet": (v5.part_feet, 0.2),
         "blind": (v52.blind_wide, 0.15)}


def thickness(node, h):
    lo, hi = node.bbox()
    g = [np.arange(lo[i] - h, hi[i] + h, h) for i in range(3)]
    shp = tuple(len(a) for a in g)
    t = np.empty(shp, np.float32)
    YZ = np.stack(np.meshgrid(g[1], g[2], indexing="ij"), -1).reshape(-1, 2)
    for i, x in enumerate(g[0]):
        t[i] = (-node.sdf(np.column_stack([np.full(len(YZ), x), YZ]))).reshape(shp[1:])
    mx = ndimage.maximum_filter(t, size=3)
    med = (t >= mx - 1e-6) & (t > 0.25 * h)
    idx = np.argwhere(med)
    w = 2 * t[med]
    o = np.argsort(w)
    pts = np.column_stack([g[0][idx[:, 0]], g[1][idx[:, 1]], g[2][idx[:, 2]]])
    return w[o], pts[o]


if __name__ == "__main__":
    sel = sys.argv[1:] or list(PARTS)
    for k in sel:
        fn, h = PARTS[k]
        t0 = time.time()
        w, p = thickness(fn(), h)
        thin = w < 1.2
        print(f"{k:10s} min {w[0]:.2f} mm bei {np.round(p[0], 1).tolist()}  5% {np.percentile(w, 5):.2f}  "
              f"Punkte <1,2 mm: {int(thin.sum())} von {len(w)}  Orte: {[np.round(x, 0).tolist() for x in p[:4]]}  ({time.time() - t0:.0f}s)", flush=True)
