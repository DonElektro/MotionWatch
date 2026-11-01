import numpy as np, sys
from scipy import ndimage
import v5
from csg import R, T
jobs = [("1_Unterteil", v5.part_tub, [0,0,0]), ("2_Deckel", v5.part_lid, [0,0,0]),
        ("4_Gabel", v5.part_yoke, [0,0,0]), ("5_Arm2", v5.part_arm2, [-90,0,0]), ("8_Lampe", v5.part_lamp, [0,-90,0]),
        ("6_Kopf", v5.pt.part_head, [-90,0,0]), ("7_Seitendeckel", v5.pt.part_sidecover, [90,0,0]), ("9_Zwischenboden", v5.part_shelf, [0,0,0]), ("A_HDMI", v5.part_hdmi_plug, [0,0,0]), ("B_Fuss", v5.part_feet, [0,0,0])]
sel = sys.argv[1:]
h, lh = 0.3, 0.2
for name, fn, rot in jobs:
    if sel and name[0] not in sel: continue
    n = R(rot, fn()); lo, hi = n.bbox(); n = T(-lo, n); lo, hi = n.bbox()
    xs = np.arange(0, hi[0] + h, h); ys = np.arange(0, hi[1] + h, h); zs = np.arange(lh / 2, hi[2], lh)
    X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
    prev = None; islands = []; worst = []; first = None
    for k, z in enumerate(zs):
        lay = (n.sdf(np.column_stack([XY, np.full(len(XY), z)])) < 0).reshape(X.shape)
        if k == 0:
            first = lay.sum() * h * h
        else:
            sup = ndimage.binary_dilation(prev, iterations=2)
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
    print(f"{name:16s} Auflage {first:7.0f} mm²  Höhe {hi[2]:5.1f}  Inseln: {islands[:8] or 'keine'}  Überhänge>4mm²: {worst[:6] or 'keine'}", flush=True)
