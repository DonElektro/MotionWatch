"""5.4.0: Schicht-Prüfung (schwebende Inseln, Überhänge) der Transportsicherung 29 in Druckrichtung (umgedreht, Dach unten;
Methode wie printcheck531.py).   python3 printcheck540.py [h]   (h = seitliches Raster, Standard 0,4 mm; ca. 5 min)"""
import numpy as np, sys
from scipy import ndimage
import kappe540
from csg import R, T

h = float(sys.argv[1]) if len(sys.argv) > 1 else 0.4
lh = 0.2
for name, fn, rot in [("K_Transportsicherung_29", kappe540.part_kappe, [180, 0, 0])]:
    n = R(rot, fn()); lo, hi = n.bbox(); n = T(-lo, n); lo, hi = n.bbox()
    xs = np.arange(0, hi[0] + h, h); ys = np.arange(0, hi[1] + h, h); zs = np.arange(lh / 2, hi[2], lh)
    X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
    prev = None; islands = []; worst = []; first = None
    it = max(1, int(round(0.6 / h)))                  # 0,6 mm seitliche Selbsttragung (wie v5: 2 x 0,3)
    for k, z in enumerate(zs):
        lay = (n.sdf(np.column_stack([XY, np.full(len(XY), z)])) < 0).reshape(X.shape)
        if k == 0:
            first = lay.sum() * h * h
        else:
            sup = ndimage.binary_dilation(prev, iterations=it)
            lab, nl = ndimage.label(lay)
            for i in range(1, nl + 1):
                comp = lab == i
                if not (comp & prev).any() and comp.sum() * h * h > 0.3:
                    c = np.argwhere(comp).mean(0) * h
                    islands.append((round(z, 1), round(comp.sum() * h * h, 1), tuple(c.round(0))))
            un = lay & ~sup
            a = un.sum() * h * h
            if a > 4:
                c = np.argwhere(un).mean(0) * h
                worst.append((round(a), round(z, 1), tuple(c.round(0))))
        prev = lay
    worst.sort(reverse=True)
    print(f"{name:24s} Auflage {first:7.0f} mm²  Höhe {hi[2]:5.1f}  Inseln: {islands[:8] or 'keine'}  Überhänge>4mm²: {worst[:8] or 'keine'}", flush=True)
