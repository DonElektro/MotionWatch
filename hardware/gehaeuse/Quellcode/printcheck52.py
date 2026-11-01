"""v5.2: Schicht-Prüfung (schwebende Inseln, Überhänge) der geänderten / neuen Teile, in Druckrichtung.
python3 printcheck52.py 1 6 C D E F"""
import numpy as np, sys
from scipy import ndimage
import v52
from csg import R, T
jobs = [("1_Unterteil", v52.part_tub, [0, 0, 0], 0.3), ("6_Kopf", v52.part_head, [-90, 0, 0], 0.3),
        ("C_Blindstopfen_WW", v52.blind_wide, [0, -90, 0], 0.1), ("D_Stopfen_IR", v52.blind_ir, [0, 0, 0], 0.1),
        ("E_Diffusor", v52.part_diffuser, [0, 0, 0], 0.1), ("F_Pupillenring", v52.part_pupil, [0, 0, 0], 0.1)]
sel = sys.argv[1:]
lh = 0.2
for name, fn, rot, h in jobs:
    if sel and name[0] not in sel: continue
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
    print(f"{name:20s} Auflage {first:7.0f} mm²  Höhe {hi[2]:5.1f}  Inseln: {islands[:8] or 'keine'}  Überhänge>4mm²: {worst[:8] or 'keine'}", flush=True)
