"""5.3.1 Prüfung Adapter 28 (altes UPS HAT) im unveränderten Gehäuse v5.3: Kollisionen, Höhe unter dem Deckel, Stecker durch
das Service-Fenster, LEDs durch die Lüftungsschlitze, Luft über dem Active Cooler, Kabelwege.
python3 check531.py            (Abstand < 0 = Überschneidung in mm; Werte hängen an den NACHMESSEN-Parametern in upsalt531.py)"""
import sys, numpy as np
import v5, v52, v53
import upsalt531 as u
from csg import box, cyl_y, T, R

H = 0.6


def shell_points(node, h=H, band=None):
    """Punkte im Inneren nahe der Oberfläche (Schale) eines Teils"""
    lo, hi = node.bbox()
    xs, ys, zs = [np.arange(lo[i] + h / 2, hi[i], h) for i in range(3)]
    out = []
    X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
    for z in zs:
        P = np.column_stack([XY, np.full(len(XY), z)])
        d = node.sdf(P)
        m = (d < 0.05) & (d > -(band or 1.5 * h))
        out.append(P[m])
    return np.concatenate(out) if out else np.zeros((0, 3))


def clearance(pts, other):
    if len(pts) == 0:
        return 99.0, None
    d = other.sdf(pts)
    i = int(np.argmin(d))
    return float(d[i]), pts[i]


P = u.placed()
STAPEL = ("adapter", "pi", "cooler", "camconn", "standoff", "hat", "hatunder", "holder18650", "hatled")
FEST = ("tub", "lid", "hatch", "feet", "pca", "hub", "soundcard", "servo1", "sdext", "sdplug", "mosfet", "buck", "relay", "jacks", "relayjack",
        "resjack", "resplug", "btn", "mic", "pir", "lampdrv", "fuseh", "wcam", "irled", "speaker", "probe")
NICHT = {"shelf": T([0, 0, v5.SHELF_Z - v5.SHELF_T], v5.part_shelf()), "duct": v53.part_duct(),
         "charger": box(126, 135.5, 62, 80, v5.SHELF_Z, v5.SHELF_Z + 25.4), "pam": box(137, 155, 62, 80, v5.SHELF_Z, v5.SHELF_Z + 6),
         "stopfen10": T([(v52.SVC_X0 + v52.SVC_X1) / 2, -v5.WALL - 1.5, v5.PI_Z + 4], R([-90, 0, 0], v52.part_service_plug()))}
probleme = []

print("== Stapel (Höhen) ==")
print("  Pi unten z %.2f | Kühler oben %.2f | HAT unten %.2f | Zellen oben %.2f | Deckel unten %.2f" % (u.PZ, u.PZ + 1.6 + u.COOL_H, u.ZH, u.TOP, v5.TOPZ))
print("  Luft Zellen -> Deckel %.2f mm, Luft Lüfter -> HAT %.2f mm" % (v5.TOPZ - u.TOP, u.ZH - u.PZ - 1.6 - u.COOL_H))
if v5.TOPZ - u.TOP < 0.5:
    probleme.append("Zellen zu hoch für den Deckel (%.2f mm)" % (v5.TOPZ - u.TOP))

print("== Kollisionen Stapel <-> Gehäuse v5.3 (unverändert) ==")
pts = {k: shell_points(P[k]) for k in STAPEL}
for k in STAPEL:
    worst = []
    for f in FEST:
        if f not in P:
            continue
        lo1, hi1 = P[k].bbox(); lo2, hi2 = P[f].bbox()
        if np.any(hi1 + 3 < lo2) or np.any(hi2 + 3 < lo1):
            continue
        d, p = clearance(pts[k], P[f])
        worst.append((d, f, p))
    worst.sort(key=lambda t: t[0])
    txt = ", ".join("%s %.2f" % (f, d) for d, f, p in worst[:4]) or "nichts in der Nähe"
    print("  %-12s %s" % (k, txt))
    for d, f, p in worst:
        klemm = k == "adapter" and f == "tub" and d >= -(0.1 + v52.SOCK_CLAMP) and any(abs(p[1] - yc) <= 2.1 for yc in (20.0, 60.0)) and p[2] < v5.ZF + 3.6
        if klemm:
            print("  %-12s (Klemmrippe drückt %.2f mm gegen den Akku-Zaun – gewollt wie Sockel 13)" % ("", -d))
        if d < 0.0 and not klemm:
            probleme.append("%s schneidet %s (%.2f mm bei %s)" % (k, f, d, np.round(p, 1).tolist()))

print("== Teile v5.3, die mit dem Adapter draussen bleiben (nur Info) ==")
for n, node in NICHT.items():
    ws = []
    for k in ("pi", "cooler", "hat", "hatunder", "holder18650"):
        ws.append((clearance(pts[k], node)[0], k))
    d, k = min(ws)
    print("  %-10s kleinster Abstand %.2f mm (%s)%s" % (n, d, k, "  -> weglassen" if d < 0 else ""))

print("== Zugang von aussen (Stopfen 10 draussen) ==")
tub = P["tub"]
for nm, node in (("Stecker 8,4 V (Hülse Ø 5,5 + 0,3)", u.plug_sleeve(0.3)), ("USB-A-Stecker (Metall + 0,3)", u.usb_plug(0.3))):
    d, p = clearance(shell_points(node, 0.3), tub)
    print("  %-34s Abstand zum Unterteil %.2f mm" % (nm, d))
    if d < 0:
        probleme.append(nm + " stösst an das Unterteil (%.2f mm bei %s)" % (d, np.round(p, 1).tolist()))
xs = u.PX + u.SW_X
d, p = clearance(shell_points(cyl_y(xs, u.ZH - u.SW_H / 2, -v5.WALL - 3, u.PY - u.SW_OUT, 3.0), 0.3), tub)
print("  %-34s Abstand zum Unterteil %.2f mm (Stift Ø 3 durch das Fenster)" % ("Schalter ON/OFF", d))
if d < 0:
    probleme.append("Schalter nicht erreichbar")
# LEDs: gerader Blick von aussen (-y) durch die Lüftungsschlitze
zl = u.ZH + u.HAT_T + 0.4
frei = []
for x in np.arange(u.PX + u.LED_X0, u.PX + u.LED_X1 + 0.01, 0.25):
    ray = np.array([(x, y, zl) for y in np.arange(-v5.WALL - 1, u.PY + u.LED_Y - 1.5, 0.2)])
    if tub.sdf(ray).min() > 0:
        frei.append(round(x, 2))
print("  LEDs (x %.0f..%.0f): gerade Sicht durch die Lüftungsschlitze bei x %s" % (u.PX + u.LED_X0, u.PX + u.LED_X1,
      "%.1f..%.1f (%d von %d Stellen)" % (min(frei), max(frei), len(frei), int((u.LED_X1 - u.LED_X0) / 0.25) + 1) if frei else "– keine"))
if not frei:
    probleme.append("LEDs von aussen nicht sichtbar")

print("== Kabel CAM0 / CAM1 (Vorschlag; Modell = Stab Ø 3, gerechnet als Flachkabel 0,3 mm: Abstand + 1,35) ==")
FLACH = 1.35
for nm, pts_ in (("cam0", u.cable_cam0_pts()), ("cam1", u.cable_cam1_pts())):
    kn = P[nm]
    ps = shell_points(kn, 0.3, band=0.6)
    for f in ("lid", "tub", "holder18650", "hat", "hatunder", "cooler", "pi"):
        d, p = clearance(ps, P[f])
        d += FLACH
        print("  %s <-> %-12s %.2f mm%s" % (nm, f, d, "" if d >= 0 else "  (bei %s)" % np.round(p, 1).tolist()))
        if d < 0:
            probleme.append("Kabel %s schneidet %s (%.2f mm bei %s)" % (nm, f, d, np.round(p, 1).tolist()))
    L = sum(np.linalg.norm(np.subtract(a, b)) for a, b in zip(pts_[:-1], pts_[1:]))
    print("  %s Länge ca. %.0f mm" % (nm, L))

print("== Adapter ==")
lo, hi = P["adapter"].bbox()
print("  Bounding Box x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
print()
if probleme:
    print("PROBLEME:"); [print("  -", p) for p in probleme]
    sys.exit(1)
print("OK (mit den Annahmen NACHMESSEN)")
