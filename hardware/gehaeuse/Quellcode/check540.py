"""5.4.0 Prüfung 29 Transportsicherung (Kappe) am unveränderten Gehäuse v5.3, Kopf in Grundstellung (pan 180, tilt 0):
  1 Abstände Kappe <-> jedes Teil (Anlageflächen = PASS / DACH_LUFT, alles andere mit Luft)
  2 Sichtkegel: Kamera (gerechnet mit Weitwinkel 102° × 67° + 2°), Wärmebild (90° + 2°), Lampen (120°), Weitwinkel v5.2 vorne
  3 Kabel: Schlaufe Kopf -> Kamin, Flachkabel auf der Öse im Kamin (16 mm breit), Lampenkabel
  4 Aufsetzen von oben: kein Teil des Geräts liegt über der Kappe (Spalten-Abtastung; nur die Rastnasen greifen unter das Dach)
  5 Sperre: ab welchem Winkel stösst der Kopf beim Schwenken / Neigen an (Spiel)
  6 Masse, Volumen, Gewicht
python3 check540.py            (Abstand < 0 = Überschneidung in mm; Werte hängen an den Annahmen in kappe540.py)"""
import sys, time, numpy as np
import v5, v52, v53
import pantilt as pt
import kappe540 as k
import csg
from csg import U, I, box

H = 0.5
t0 = time.time()
MARGIN_ALT = csg.MARGIN
csg.MARGIN = 40.0          # Abschnitte 1–3: genaue Abstände (sonst gibt csg ausserhalb der Bounding Box + 1,5 mm nur eine untere Grenze)


def shell_points(node, h=H, band=None):
    """Punkte im Inneren nahe der Oberfläche (Schale) eines Teils (wie check531.py)"""
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


def naechst(pts, other, rand=6.0):
    lo, hi = other.bbox()
    m = np.all((pts > lo - rand) & (pts < hi + rand), axis=1)
    if not m.any():
        return 99.0, None
    q = pts[m]
    d = other.sdf(q)
    i = int(np.argmin(d))
    return float(d[i]), q[i]


P = k.placed()
kap = P["kappe"]
pts = shell_points(kap)
probleme = []
print("Kappe: %d Prüfpunkte (Schale, Raster %.1f mm)  %.0fs" % (len(pts), H, time.time() - t0), flush=True)

# ---------------------------------------------------------------- 1 Abstände
print("== 1 Abstände Kappe <-> Teile (mm) ==")
ANLAGE = {"head": k.PASS, "side": k.PASS, "lamp1": k.PASS, "lamp2": k.PASS, "lid": 0.0}
SOLL_LUFT = 1.0                                   # alles, was keine Anlagefläche ist
fuss = pts[:, 2] < v5.LIDTOP + 0.3                 # Wangen / Rückwand stehen auf dem Deckel (gewollt)
reihen = []
for name, node in P.items():
    if name == "kappe":
        continue
    d, p = naechst(pts[~fuss] if name in ("lid", "tub") else pts, node)
    if d >= 30:
        continue
    reihen.append((d, name, p))
for d, name, p in sorted(reihen, key=lambda r: r[0]):
    soll = ANLAGE.get(name, SOLL_LUFT)
    ok = d >= soll - 0.26                          # Raster 0,5 mm: ± 0,25
    print("  %-10s %6.2f mm  bei %s%s" % (name, d, np.round(p, 1).tolist(), "" if ok else "   <-- zu nah (Soll >= %.1f)" % soll))
    if not ok:
        probleme.append("Kappe zu nah an %s: %.2f mm bei %s" % (name, d, np.round(p, 1).tolist()))
d, p = naechst(pts[fuss], P["lid"])
print("  (Wangen / Rückwand stehen auf dem Deckel: Abstand %.2f mm – gewollt)" % d)

# Anlageflächen gezielt (feines Raster)
print("  Anlage Dach -> Kopf oben: %.2f mm (Soll %.1f), Rückwand -> Kopf hinten: %.2f mm, Seitenwände -> Lampenbecher: %.2f / %.2f mm"
      % (k.DACH_Z0 - k.KOPF_OBEN, k.DACH_LUFT, (k.H_X1 - k.WAND) - k.KOPF_HINTEN,
         (k.AY - k.LAMPE_R) - (k.H_Y0 + k.WAND), (k.H_Y1 - k.WAND) - (k.AY + k.LAMPE_R)))
print("  Kamin: Wangen %.2f / Rückwand %.2f / Krallen -> runde Ecke %.2f mm; Nase unter dem Dach %.2f mm tief, Luft zur Dach-Unterseite %.2f mm"
      % (k.KA_Y[0] - (k.R_Y0 + k.WAND), (k.R_X1 - k.WAND) - k.KA_X[1],
         np.hypot(k.KA_X[0] + k.KA_R - k.KR_X[1], k.KA_Y[0] + k.KA_R - k.kralle_y(-1)) - k.KA_R,
         k.Z_X[1] + k.NASE + k.PASS - k.KA_X[0], k.NASE_SPIEL))

# ---------------------------------------------------------------- 2 Sichtkegel
print("== 2 Sichtkegel (Abstand > 0 = Kappe ausserhalb) ==")
print("  vorderstes Material der Kappe x %.2f, Linsen vorne x %s" % (pts[:, 0].min(), {a: round(b, 2) for a, b in k.LINSE_X.items()}))
for nm, L, a, h, u, wh, wv, r0 in k.sichtkegel():
    cone = k.kegel_node(L, a, h, u, wh, wv, r0)
    dd = cone.sdf(pts)
    i = int(np.argmin(dd))
    hinter = (pts - L) @ a                          # < 0: hinter der Linsen-Ebene
    print("  %-20s ± %.1f° / ± %.1f°: kleinster Abstand %.2f mm (bei %s), alles Material %.2f mm hinter der Linsen-Ebene"
          % (nm, wh, wv, dd[i], np.round(pts[i], 1).tolist(), -hinter.max()))
    if dd[i] <= 0:
        probleme.append("Kappe im Sichtfeld: " + nm)
pl, *_ = v52.wc_window()
wcone = I(box(-400, 1.0, -400, 500, -300, 400), *pl)
dd = wcone.sdf(pts)
print("  %-20s (v52.wc_window, ± %.1f° / ± %.1f°): kleinster Abstand %.2f mm" % ("Weitwinkel v5.2 vorne", v52.WC_FOV_H, v52.WC_FOV_V, dd.min()))
if dd.min() <= 0:
    probleme.append("Kappe im Sichtfeld der Weitwinkel-Kamera v5.2")
for nm, node in (("PIR", P["pir"]), ("Mikrofon", P["mic"])):
    print("  %-20s Abstand %.1f mm" % (nm, naechst(pts, node, 300)[0]))

# ---------------------------------------------------------------- 3 Kabel
print("== 3 Kabel (Modell: Schlaufe Ø 8, Lampenkabel Ø 4, Flachkabel 16 × 1,5 mm auf der Öse) ==")
KABEL = {"Schlaufe Kopf -> Kamin": k.kabel_node(k.schlaufe_pts(), 8.0),
         "Flachkabel auf der Öse (16 mm)": k.flachkabel_kamin(16.0),
         "Flachkabel auf der Öse (12 mm)": k.flachkabel_kamin(12.0),
         "Lampenkabel weiss": k.kabel_node(k.lampenkabel_pts(+1), 4.0),
         "Lampenkabel IR": k.kabel_node(k.lampenkabel_pts(-1), 4.0),
         "Öse im Kamin (Deckel)": box(*v53.TIE_LID, v5.LIDTOP - 1.05, v5.LIDTOP + 5.0)}
for nm, node in KABEL.items():
    d, p = naechst(pts, node, 60)
    print("  %-32s %6.2f mm  bei %s" % (nm, d, np.round(p, 1).tolist() if p is not None else "-"))
    if d < 0.5:
        probleme.append("Kappe drückt auf Kabel: %s (%.2f mm)" % (nm, d))
for nm in ("servo1", "servo2", "horn1", "horn2", "cam3", "therm", "diff", "sled"):
    print("  %-32s %6.2f mm" % (nm, naechst(pts, P[nm], 200)[0]))

# ---------------------------------------------------------------- 4 Aufsetzen von oben
csg.MARGIN = MARGIN_ALT    # ab hier nur «berührt / berührt nicht» – schnell
print("== 4 Aufsetzen / Abnehmen senkrecht (Spalten-Abtastung 0,75 mm, z 0,25 mm) ==", flush=True)
GERAET = U(*[P[n] for n in ("lid", "turntable", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "alu", "head", "side",
                            "diff", "cam3", "therm", "horn2", "balls")])
lo, hi = kap.bbox()
xs = np.arange(lo[0] + 0.375, hi[0], 0.75); ys = np.arange(lo[1] + 0.375, hi[1], 0.75)
X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
cmin = np.full(len(XY), np.inf); amax = np.full(len(XY), -np.inf)
for z in np.arange(v5.LIDTOP + 0.125, hi[2] + 0.5, 0.25):
    Q = np.column_stack([XY, np.full(len(XY), z)])
    c = kap.sdf(Q) < 0
    cmin[c] = np.minimum(cmin[c], z)
    a = GERAET.sdf(Q) < 0
    amax[a] = np.maximum(amax[a], z)
ueber = amax - cmin                                   # > 0: Gerät liegt in dieser Spalte über Material der Kappe
nase = np.zeros(len(XY), bool)
for s in (-1, 1):
    y0, y1 = k.zungen_y(s)
    nase |= (XY[:, 0] > k.Z_X[1] - 0.01) & (XY[:, 0] < k.Z_X[1] + k.NASE + k.PASS + 0.4) & (XY[:, 1] > y0 - 0.4) & (XY[:, 1] < y1 + 0.4)
schlecht = (ueber > 0.01) & ~nase
print("  Spalten mit Material der Kappe: %d; davon unter einem Teil des Geräts: %d (ausser den Rastnasen)" % (np.isfinite(cmin).sum(), schlecht.sum()))
if schlecht.any():
    i = np.argmax(np.where(schlecht, ueber, -1))
    print("  schlimmste Spalte x %.1f y %.1f: %.2f mm" % (*XY[i], ueber[i]))
    probleme.append("Kappe lässt sich nicht senkrecht aufsetzen (%d Spalten)" % schlecht.sum())
nn = nase & (ueber > 0)
print("  Rastnasen: %d Spalten unter dem Kamin-Dach (gewollt, die Zungen federn %.1f mm aus)" % (nn.sum(), k.NASE))
print("  (%.0fs)" % (time.time() - t0), flush=True)

# ---------------------------------------------------------------- 5 Sperre
print("== 5 Sperre: Spiel bis zum Anschlag ==", flush=True)
BEWEGT = ("head", "side", "lamp1", "lamp2", "yoke", "arm2", "diff", "lens_w", "lens_ir")


def min_abstand(tilt, pan):
    Q = v53.placed(tilt, pan)
    return min(naechst(pts, Q[n], 3.0)[0] for n in BEWEGT if n in Q)


def anschlag(fn):
    """kleinster Winkel (0..10°), bei dem sich Kopf / Lampen und Kappe berühren (Bisektion)"""
    a, b = 0.0, 10.0
    if fn(b) > 0:
        return None
    for _ in range(12):
        m = (a + b) / 2
        if fn(m) > 0:
            a = m
        else:
            b = m
    return b


sp = {}
for nm, fn in (("Schwenken +", lambda w: min_abstand(0.0, 180.0 + w)), ("Schwenken -", lambda w: min_abstand(0.0, 180.0 - w)),
               ("Neigen +", lambda w: min_abstand(w, 180.0)), ("Neigen -", lambda w: min_abstand(-w, 180.0))):
    sp[nm] = anschlag(fn)
    print("  %-12s Anschlag nach %s" % (nm, "%.2f°" % sp[nm] if sp[nm] is not None else "mehr als 10° (KEINE Sperre)"), flush=True)
    if sp[nm] is None or sp[nm] > 2.0:
        probleme.append("Sperre %s zu weich (%s)" % (nm, sp[nm]))

# ---------------------------------------------------------------- 6 Masse
print("== 6 Masse ==")
lo, hi = kap.bbox()
g = 0.5
xs_, ys_, zs_ = [np.arange(lo[i] + g / 2, hi[i], g) for i in range(3)]
X, Y = np.meshgrid(xs_, ys_, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
vol = sum(int((kap.sdf(np.column_stack([XY, np.full(len(XY), z)])) < 0).sum()) for z in zs_) * g ** 3 / 1000.0
print("  Grösse %.1f × %.1f × %.1f mm (x × y × z), Druckhöhe umgedreht %.1f mm; Volumen ca. %.0f cm³ -> PETG ca. %.0f g (1,27 g/cm³, voll)"
      % (*(hi - lo), hi[2] - lo[2], vol, vol * 1.27))
print("  (%.0fs)" % (time.time() - t0))
print()
if probleme:
    print("PROBLEME:"); [print("  -", x) for x in probleme]
    sys.exit(1)
print("OK (mit den Annahmen in kappe540.py)")
