"""5.5.0: Schicht-Prüfung (schwebende Inseln, Überhänge) in Druckrichtung (Methode wie printcheck540.py) für die Schutzschale:
31 vordere Hälfte und 33 Stopfen mit der Stirnseite auf dem Bett, 32 hintere Hälfte mit der Rückseite auf dem Bett.
Dazu eine Schätzung aus den Schichten (kein Slicer): Volumen, Masse PETG und Druckzeit X2D (0,4-mm-Düse, 0,2-mm-Schicht).
python3 printcheck550.py [h] [teil ...]   (h = seitliches Raster, Standard 0,4 mm; teil = vorne, hinten, stopfen)"""
import numpy as np, sys, time
from scipy import ndimage
import schale550 as s
from csg import R, T

# Schätzung Druckzeit: Linien 0,42 × 0,2 mm, mittlere Geschwindigkeit inkl. Beschleunigung und Wege (PETG am X2D, Wände
# begrenzt durch den Durchfluss ca. 12 mm³/s), dazu Schichtwechsel. Die Schale ist dünnwandig: Wände (2,4 mm) werden voll
# gedruckt, darum Masse ~ Volumen.
LINIE, V_MITTEL, T_SCHICHT, DICHTE = 0.42 * 0.2, 90.0, 4.0, 1.27
TEILE = {"vorne": ("31_Schutzschale_vorne", s.part_vorne, [0, -90, 0]),
         "hinten": ("32_Schutzschale_hinten", s.part_hinten, [0, 90, 0]),
         "stopfen": ("33_Schutzschale_Stopfen", s.part_stopfen, [0, -90, 0])}

args = [a for a in sys.argv[1:] if not a.startswith("--")]
h = float(args[0]) if args and args[0][0].isdigit() else 0.4
wahl = [a for a in args if a in TEILE] or list(TEILE)
lh = 0.2
for key in wahl:
    name, fn, rot = TEILE[key]
    t0 = time.time()
    n = R(rot, fn()); lo, hi = n.bbox(); n = T(-lo, n); lo, hi = n.bbox()
    xs = np.arange(0, hi[0] + h, h); ys = np.arange(0, hi[1] + h, h); zs = np.arange(lh / 2, hi[2], lh)
    X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
    prev = None; islands = []; worst = []; first = None; vol = 0.0; nsch = 0; zmax = 0.0
    it = max(1, int(round(0.6 / h)))                  # 0,6 mm seitliche Selbsttragung (wie v5: 2 x 0,3)
    k = -1
    for z in zs:
        lay = (n.sdf(np.column_stack([XY, np.full(len(XY), z)])) < 0).reshape(X.shape)
        a_l = lay.sum() * h * h
        if k < 0 and a_l == 0:                        # bbox der CSG-Knoten ist grosszügig: leere Schichten unter dem Teil
            continue
        k += 1
        if a_l > 0:
            vol += a_l * lh; nsch += 1; zmax = z
        if k == 0:
            first = a_l; z_bett = z - lh / 2
        else:
            sup = ndimage.binary_dilation(prev, iterations=it)
            lab, nl = ndimage.label(lay)
            for i in range(1, nl + 1):
                comp = lab == i
                if not (comp & prev).any() and comp.sum() * h * h > 0.3:
                    c = np.argwhere(comp).mean(0) * h
                    islands.append((round(z - z_bett, 1), round(comp.sum() * h * h, 1), tuple(c.round(0))))
            un = lay & ~sup
            a = un.sum() * h * h
            if a > 4:
                c = np.argwhere(un).mean(0) * h
                worst.append((round(a), round(z - z_bett, 1), tuple(c.round(0))))
        prev = lay
    worst.sort(reverse=True)
    std = (vol / LINIE / V_MITTEL + nsch * T_SCHICHT) / 3600.0
    print(f"{name:26s} Auflage {first:6.0f} mm²  Höhe {zmax + lh / 2 - z_bett:5.1f}  Inseln: {islands[:8] or 'keine'}  "
          f"Überhänge>4mm²: {worst[:8] or 'keine'}", flush=True)
    print(f"{'':26s} Schätzung: {vol / 1000:.1f} cm³ -> {vol / 1000 * DICHTE:.0f} g PETG, {nsch} Schichten, ca. {std:.1f} h  "
          f"(Grundfläche {hi[0]:.0f} × {hi[1]:.0f} mm, {time.time() - t0:.0f}s)", flush=True)
