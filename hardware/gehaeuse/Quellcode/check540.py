"""5.4.0 Prüfung 29 Transportsicherung (Haube über Kopf und Lampen) am unveränderten Gehäuse v5.3, Kopf in Grundstellung
(pan 180, tilt 0):
  1 Abstände Haube <-> jedes Teil (Anlage: Kopf PASS / DACH_LUFT, Lampenbecher 0 = Rastlippe liegt an, alles andere mit Luft)
  2 Sichtkegel: Kamera (gerechnet mit Weitwinkel 102° × 67° + 2°), Wärmebild (90° + 2°), Lampen (120°), Weitwinkel v5.2 vorne
  3 Kabel: Schlaufe Kopf -> Kamin, Lampenkabel
  4 Aufsetzen von oben: kein Teil des Geräts liegt über der Haube (Spalten-Abtastung; nur die Rastlippen greifen unter die Becher)
  5 Sperre: ab welchem Winkel stösst der Kopf beim Neigen an (Spiel); Schwenken
  6 Masse, Volumen, Gewicht
python3 check540.py [--beine]   (--beine: Variante mit Pan-Beinen an den Deckel-Seiten; Abstand < 0 = Überschneidung in mm)"""
import sys, time, numpy as np
import v5, v52, v53
import pantilt as pt
import kappe540 as k
import csg
from csg import U, I, box

if "--beine" in sys.argv:
    k.PAN_BEINE = True
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
print("Haube%s: %d Prüfpunkte (Schale, Raster %.1f mm)  %.0fs" % (" mit Pan-Beinen" if k.PAN_BEINE else "", len(pts), H, time.time() - t0), flush=True)

# ---------------------------------------------------------------- 1 Abstände
print("== 1 Abstände Haube <-> Teile (mm) ==")
ANLAGE = {"head": k.PASS, "side": k.PASS, "lamp1": 0.0, "lamp2": 0.0, "diff": k.DIFF_PASS,
          "lid": -k.BEIN_KLEMM, "tub": -k.BEIN_KLEMM}
SOLL_LUFT = 1.0                                   # alles, was keine Anlagefläche ist
reihen = []
for name, node in P.items():
    if name == "kappe":
        continue
    d, p = naechst(pts, node)
    if d >= 30:
        continue
    reihen.append((d, name, p))
for d, name, p in sorted(reihen, key=lambda r: r[0]):
    soll = ANLAGE.get(name, SOLL_LUFT)
    ok = d >= soll - 0.26                          # Raster 0,5 mm: ± 0,25
    print("  %-10s %6.2f mm  bei %s%s" % (name, d, np.round(p, 1).tolist(), "" if ok else "   <-- zu nah (Soll >= %.1f)" % soll))
    if not ok:
        probleme.append("Haube zu nah an %s: %.2f mm bei %s" % (name, d, np.round(p, 1).tolist()))
print("  Anlage: Dach -> Kopf oben %.2f mm, Rückwand -> Kopf hinten %.2f mm, Diffusor %.2f mm, Seitenwand -> Becher %.2f mm,"
      " Rastlippe %.1f mm unter der dicksten Stelle (z %.1f)" % (k.DACH_Z0 - k.KOPF_OBEN, (k.H_X1 - k.WAND) - k.KOPF_HINTEN,
                                                                k.DIFF_PASS, k.D_WI - k.LAMPE_R, k.RAST, k.LIPPE_Z))

# ---------------------------------------------------------------- 2 Sichtkegel
print("== 2 Sichtkegel (Abstand > 0 = Haube ausserhalb) ==")
print("  vorderstes Material der Haube x %.2f, Linsen vorne x %s" % (pts[:, 0].min(), {a: round(b, 2) for a, b in k.LINSE_X.items()}))
for nm, L, a, h, u, wh, wv, r0 in k.sichtkegel():
    cone = k.kegel_node(L, a, h, u, wh, wv, r0)
    dd = cone.sdf(pts)
    i = int(np.argmin(dd))
    hinter = (pts - L) @ a                          # < 0: hinter der Linsen-Ebene
    print("  %-20s ± %.1f° / ± %.1f°: kleinster Abstand %.2f mm (bei %s), alles Material %.2f mm hinter der Linsen-Ebene"
          % (nm, wh, wv, dd[i], np.round(pts[i], 1).tolist(), -hinter.max()))
    if dd[i] <= 0:
        probleme.append("Haube im Sichtfeld: " + nm)
pl, *_ = v52.wc_window()
wcone = I(box(-400, 1.0, -400, 500, -300, 400), *pl)
dd = wcone.sdf(pts)
print("  %-20s (v52.wc_window, ± %.1f° / ± %.1f°): kleinster Abstand %.2f mm" % ("Weitwinkel v5.2 vorne", v52.WC_FOV_H, v52.WC_FOV_V, dd.min()))
if dd.min() <= 0:
    probleme.append("Haube im Sichtfeld der Weitwinkel-Kamera v5.2")
for nm, node in (("PIR", P["pir"]), ("Mikrofon", P["mic"])):
    print("  %-20s Abstand %.1f mm" % (nm, naechst(pts, node, 300)[0]))

# ---------------------------------------------------------------- 3 Kabel
print("== 3 Kabel (Modell: Schlaufe Ø 8, Lampenkabel Ø 4) ==")
KABEL = {"Schlaufe Kopf -> Kamin": k.kabel_node(k.schlaufe_pts(), 8.0),
         "Lampenkabel weiss": k.kabel_node(k.lampenkabel_pts(+1), 4.0),
         "Lampenkabel IR": k.kabel_node(k.lampenkabel_pts(-1), 4.0)}
for nm, node in KABEL.items():
    d, p = naechst(pts, node, 60)
    print("  %-32s %6.2f mm  bei %s" % (nm, d, np.round(p, 1).tolist() if p is not None else "-"))
    if d < 0.5:
        probleme.append("Haube drückt auf Kabel: %s (%.2f mm)" % (nm, d))
for nm in ("servo1", "servo2", "horn1", "horn2", "cam3", "therm", "diff", "sled"):
    print("  %-32s %6.2f mm" % (nm, naechst(pts, P[nm], 200)[0]))

# ---------------------------------------------------------------- 4 Aufsetzen von oben
csg.MARGIN = MARGIN_ALT    # ab hier nur «berührt / berührt nicht» – schnell
print("== 4 Aufsetzen / Abnehmen senkrecht (Spalten-Abtastung 0,75 mm, z 0,25 mm) ==", flush=True)
GERAET = U(*[P[n] for n in ("lid", "tub", "turntable", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "alu", "head", "side",
                            "diff", "cam3", "therm", "horn2", "balls")])
lo, hi = kap.bbox()
xs = np.arange(lo[0] + 0.375, hi[0], 0.75); ys = np.arange(lo[1] + 0.375, hi[1], 0.75)
X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
cmin = np.full(len(XY), np.inf); amax = np.full(len(XY), -np.inf)
for z in np.arange(max(lo[2], v5.LIDTOP - 6) + 0.125, hi[2] + 0.5, 0.25):
    Q = np.column_stack([XY, np.full(len(XY), z)])
    c = kap.sdf(Q) < 0
    cmin[c] = np.minimum(cmin[c], z)
    a = GERAET.sdf(Q) < 0
    amax[a] = np.maximum(amax[a], z)
ueber = amax - cmin                                   # > 0: Gerät liegt in dieser Spalte über Material der Haube
d_ = np.abs(XY[:, 1] - k.AY)
rast = (XY[:, 0] < k.S_X1 + 0.4) & (d_ > k.D_LIPPE - 0.4) & (d_ < k.D_WI + 0.4)
klemm = np.zeros(len(XY), bool)
if k.PAN_BEINE:
    klemm = (XY[:, 0] > k.BEIN_X[0] - 0.4) & (d_ > k.D_DECKEL - k.BEIN_KLEMM - 0.4) & (d_ < k.D_DECKEL + 0.4)
schlecht = (ueber > 0.01) & ~rast & ~klemm
print("  Spalten mit Material der Haube: %d; davon unter einem Teil des Geräts: %d (ausser Rastlippen%s)"
      % (np.isfinite(cmin).sum(), schlecht.sum(), " und Klemmung der Beine" if k.PAN_BEINE else ""))
if schlecht.any():
    i = np.argmax(np.where(schlecht, ueber, -1))
    print("  schlimmste Spalte x %.1f y %.1f: %.2f mm" % (*XY[i], ueber[i]))
    probleme.append("Haube lässt sich nicht senkrecht aufsetzen (%d Spalten)" % schlecht.sum())
print("  Rastlippen: %d Spalten unter den Lampenbechern (gewollt, die Seitenwände federn %.1f mm aus)" % ((rast & (ueber > 0)).sum(), k.RAST))
print("  (%.0fs)" % (time.time() - t0), flush=True)

# ---------------------------------------------------------------- 5 Sperre
print("== 5 Sperre: Spiel bis zum Anschlag ==", flush=True)


def min_abstand(tilt, pan, teile):
    Q = v53.placed(tilt, pan)
    return min(naechst(pts, Q[n], 3.0)[0] for n in teile if n in Q)


def anschlag(fn):
    """kleinster Winkel (0..10°), bei dem sich Kopf und Haube berühren (Bisektion)"""
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


KOPF = ("head", "side", "diff")                      # die Haube sitzt an den Lampen = an der Gabel; nur der Kopf neigt
for nm, fn in (("Neigen +", lambda w: min_abstand(w, 180.0, KOPF)), ("Neigen -", lambda w: min_abstand(-w, 180.0, KOPF))):
    w = anschlag(fn)
    print("  %-12s Anschlag nach %s" % (nm, "%.2f°" % w if w is not None else "mehr als 10° (KEINE Sperre)"), flush=True)
    if w is None or w > 2.0:
        probleme.append("Sperre %s zu weich (%s)" % (nm, w))
if k.PAN_BEINE:
    print("  Schwenken: Rastlippen fest an den Lampenbechern, Beine klemmen mit %.1f mm Übermass an den Deckel-Seiten -> kein Spiel,"
          " federnd über die Beine (Hebel %.0f mm zur Pan-Achse)" % (k.BEIN_KLEMM, np.mean(k.BEIN_X) - k.AX))
else:
    print("  Schwenken: NICHT gesperrt – die Haube sitzt an Kopf und Lampen und dreht mit; der Pan-Servo (ohne Strom) hält den Kopf")

# ---------------------------------------------------------------- 6 Masse
print("== 6 Masse ==")
lo, hi = kap.bbox()
g = 0.5
xs_, ys_, zs_ = [np.arange(lo[i] + g / 2, hi[i], g) for i in range(3)]
X, Y = np.meshgrid(xs_, ys_, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
vol = sum(int((kap.sdf(np.column_stack([XY, np.full(len(XY), z)])) < 0).sum()) for z in zs_) * g ** 3 / 1000.0
alt = np.subtract(k.ALT_BOX[1], k.ALT_BOX[0])
print("  Grösse %.1f × %.1f × %.1f mm (x × y × z), Druckhöhe umgedreht %.1f mm; Volumen ca. %.1f cm³ -> PETG ca. %.0f g (1,27 g/cm³, voll)"
      % (*(hi - lo), hi[2] - lo[2], vol, vol * 1.27))
print("  erste Kappe (Runde 1): %.1f × %.1f × %.1f mm -> Hüllquader jetzt %.0f %% davon" % (*alt, 100 * np.prod(hi - lo) / np.prod(alt)))
print("  (%.0fs)" % (time.time() - t0))
print()
if probleme:
    print("PROBLEME:"); [print("  -", x) for x in probleme]
    sys.exit(1)
print("OK (mit den Annahmen in kappe540.py)")
