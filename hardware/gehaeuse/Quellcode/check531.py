"""5.3.1 Prüfung Adapter 28 (altes UPS HAT, Variante «tief, gedreht») im unveränderten Gehäuse v5.3: Kollisionen, Höhe unter
dem Deckel (schlimmster und wahrscheinlicher Fall), Ladebuchse in der Reserve-Öffnung, Luft über dem Lüfter, Kabelwege.
python3 check531.py            (Abstand < 0 = Überschneidung in mm; Werte hängen an den NACHMESSEN-Parametern in upsalt531.py)"""
import sys, numpy as np
import v5, v52, v53
import upsalt531 as u
from csg import box, T, R, cyl_x

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
STAPEL = ("adapter", "pi", "cooler", "camconn", "standoff", "hat", "hatunder", "holder18650", "hatled", "plug90", "dcsocket")
FEST = ("tub", "lid", "hatch", "feet", "pca", "hub", "soundcard", "servo1", "sdext", "sdplug", "mosfet", "buck", "relay", "jacks", "relayjack",
        "btn", "mic", "pir", "lampdrv", "fuseh", "wcam", "irled", "speaker", "probe", "shelf", "charger", "pam", "ina", "plug")
NICHT = {"duct (27)": v53.part_duct(), "resplug (17)": T([v5.LX + v5.WALL + 1.6, v52.RES_Y, v52.RES_ZC], R([0, -90, 0], v52.part_res_plug()))}
probleme = []

print("== Stapel (Höhen) ==")
print("  Pi unten z %.2f | Kühler oben %.2f | HAT unten %.2f | Zellen oben %.2f (schlimmster Fall) / %.2f (wahrscheinlich) | Deckel unten %.2f"
      % (u.PZ, u.PZ + 1.6 + u.COOL_H, u.ZH, u.TOP, u.TOP_WAHRSCH, v5.TOPZ))
print("  Luft Zellen -> Deckel %.2f / %.2f mm, Luft Lüfter -> HAT %.2f mm, Stifte oben bis z %.2f"
      % (v5.TOPZ - u.TOP, v5.TOPZ - u.TOP_WAHRSCH, u.ZH - u.PZ - 1.6 - u.COOL_H, u.ZH + u.HAT_T + u.PINS_TOP))
if v5.TOPZ - u.TOP < 0.5:
    probleme.append("Zellen zu hoch für den Deckel (schlimmster Fall, %.2f mm)" % (v5.TOPZ - u.TOP))

print("== Kollisionen Stapel <-> Gehäuse v5.3 (unverändert, schlimmster Fall) ==")
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
    print("  %-12s %s" % (k, ", ".join("%s %.2f" % (f, d) for d, f, p in worst[:4]) or "nichts in der Nähe"))
    for d, f, p in worst:
        klemm = k == "adapter" and f == "tub" and d >= -(0.1 + v52.SOCK_CLAMP) and any(abs(p[1] - yc) <= 2.1 for yc in (20.0, 60.0)) and p[2] < v5.ZF + 3.6
        wand = k == "dcsocket" and f == "tub" and p[0] > v5.LX - 0.5         # Buchse sitzt in der Wand (gewollt)
        if klemm:
            print("  %-12s (Klemmrippe drückt %.2f mm gegen den Akku-Zaun – gewollt wie Sockel 13)" % ("", -d))
        if d < 0.0 and not klemm and not wand:
            probleme.append("%s schneidet %s (%.2f mm bei %s)" % (k, f, d, np.round(p, 1).tolist()))
# Reserve-Öffnung: Gewinde Ø 11 der Buchse muss durch das Loch (Ø 12,3)
d, p = clearance(shell_points(cyl_x(u.DCB_Y, u.DCB_Z, v5.LX - 1, v5.LX + v5.WALL + 1, 11.0), 0.3), P["tub"])
print("  Ladebuchse: Gewinde Ø 11 in der Reserve-Öffnung Ø %.1f, Abstand %.2f mm" % (v52.RES_D, d))
if d < 0:
    probleme.append("Ladebuchse passt nicht in die Reserve-Öffnung")

print("== Teile v5.3, die draussen bleiben (nur Info) ==")
for n, node in NICHT.items():
    ws = [(clearance(pts[k], node)[0], k) for k in ("holder18650", "hat", "dcsocket")]
    d, k = min(ws)
    print("  %-12s kleinster Abstand %.2f mm (%s)%s" % (n, d, k, "  -> weglassen" if d < 0 else ""))

print("== Kabel CAM0 / CAM1 (Vorschlag; Modell = Stab Ø 3, gerechnet als Flachkabel 0,3 mm: Abstand + 1,35) ==")
FLACH = 1.35
for nm, pts_ in (("cam0", u.cable_cam0_pts()), ("cam1", u.cable_cam1_pts())):
    ps = shell_points(P[nm], 0.3, band=0.6)
    for f in ("lid", "tub", "holder18650", "hat", "hatunder", "plug90", "cooler", "pi", "shelf", "charger", "hub", "relay", "servo1"):
        d, p = clearance(ps, P[f])
        d += FLACH
        if d < 3.0:
            print("  %s <-> %-12s %.2f mm%s" % (nm, f, d, "" if d >= 0 else "  (bei %s)" % np.round(p, 1).tolist()))
        if d < 0:
            probleme.append("Kabel %s schneidet %s (%.2f mm bei %s)" % (nm, f, d, np.round(p, 1).tolist()))
    L = sum(np.linalg.norm(np.subtract(a, b)) for a, b in zip(pts_[:-1], pts_[1:]))
    print("  %s Länge ca. %.0f mm" % (nm, L))
pt_ = u.pigtail_pts()
print("  Ladekabel (Winkelstecker -> Einbaubuchse) ca. %.0f mm" % sum(np.linalg.norm(np.subtract(a, b)) for a, b in zip(pt_[:-1], pt_[1:])))

print("== Adapter ==")
lo, hi = P["adapter"].bbox()
print("  Bounding Box x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
print()
if probleme:
    print("PROBLEME:"); [print("  -", p) for p in probleme]
    sys.exit(1)
print("OK (mit den Annahmen NACHMESSEN)")
