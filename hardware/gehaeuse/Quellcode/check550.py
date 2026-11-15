"""5.5.0: Prüfung der Schutzschale 31 / 32 mit Stopfen 33 am Gerät v5.3 (Kopf in Grundstellung): Masse, Abstände zum Gerät,
Sichtkegel (Stopfen draussen), Passung Stopfen und Steckzapfen, Aufschieben der Hälften, Spiel von Neigen / Schwenken (Sperre)
und Schätzung der Last 5 kg auf dem Dach.   python3 check550.py   (ca. 6–8 min)"""
import sys, os, math, time, numpy as np
import csg
from csg import U, I, box, T
import v5, v53, pantilt as pt, kappe540 as k, schale550 as s
t0 = time.time()


def shell_points(node, h, band=None):
    lo, hi = node.bbox()
    lo = np.maximum(lo, [-30, -40, 60]); hi = np.minimum(hi, [130, 135, 180])
    xs, ys, zs = [np.arange(lo[i] + h / 2, hi[i], h) for i in range(3)]
    X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
    out = []
    for z in zs:
        P = np.column_stack([XY, np.full(len(XY), z)])
        d = node.sdf(P)
        out.append(P[(d < 0.05) & (d > -(band or 1.5 * h))])
    return np.concatenate(out)


def volumen(node, g=0.6):
    lo, hi = node.bbox()
    lo = np.maximum(lo, [-30, -40, 60]); hi = np.minimum(hi, [130, 135, 180])
    xs, ys, zs = [np.arange(lo[i] + g / 2, hi[i], g) for i in range(3)]
    X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.column_stack([X.ravel(), Y.ravel()])
    n = sum(int((node.sdf(np.column_stack([XY, np.full(len(XY), z)])) < 0).sum()) for z in zs)
    return n * g ** 3 / 1000.0


vorne, hinten, stopfen = s.part_vorne(), s.part_hinten(), s.part_stopfen()
P = s.placed()
GER = [n for n in P if n not in ("schale_vorne", "schale_hinten", "stopfen")]

if __name__ == "__main__":
    csg.MARGIN = 40.0
    pv, ph, pst = shell_points(vorne, 0.6), shell_points(hinten, 0.6), shell_points(stopfen, 0.4)
    pts = np.concatenate([pv, ph])
    print("Punkte vorne %d, hinten %d, Stopfen %d  (%.0fs)" % (len(pv), len(ph), len(pst), time.time() - t0), flush=True)
    print("== Masse ==")
    for nm, node in (("vordere Hälfte", vorne), ("hintere Hälfte", hinten), ("Stopfen", stopfen)):
        lo, hi = node.bbox()
        v = volumen(node)
        print("  %-15s Volumen %.1f cm³ -> ca. %.0f g PETG (voll)" % (nm, v, v * 1.27), flush=True)
    print("== Abstände Schale <-> Gerät (mm) ==")
    auf = pts[:, 2] < v5.LIDTOP + 0.4
    reihen = []
    for n in GER:
        q = pts[~auf] if n in ("lid", "tub") else pts
        lo, hi = P[n].bbox()
        m = np.all((q > lo - 8) & (q < hi + 8), axis=1)
        if not m.any():
            continue
        d = P[n].sdf(q[m]); i = int(np.argmin(d))
        reihen.append((float(d[i]), n, np.round(q[m][i], 1).tolist()))
    for nm, node in (("Kabelschlaufe (Ø 8)", k.kabel_node(k.schlaufe_pts(), 8.0)),
                     ("Lampenkabel weiss (Ø 4)", k.kabel_node(k.lampenkabel_pts(+1), 4.0)),
                     ("Lampenkabel IR (Ø 4)", k.kabel_node(k.lampenkabel_pts(-1), 4.0))):
        d = node.sdf(pts); i = int(np.argmin(d)); reihen.append((float(d[i]), nm, np.round(pts[i], 1).tolist()))
    for d, n, p in sorted(reihen)[:22]:
        print("  %-26s %6.2f  bei %s" % (n, d, p))
    print("  (Schale steht auf dem Deckel: %.2f)" % P["lid"].sdf(pts[auf]).min())
    st = [(float(P[n].sdf(pst).min()), n) for n in ("head", "side", "lamp1", "lamp2", "cam3", "therm", "lid", "tub", "turntable")]
    print("  Stopfen:", ", ".join("%s %.2f" % (n, d) for d, n in sorted(st)[:4]))
    print("== Passung ==")
    dv = vorne.sdf(pst); dh = hinten.sdf(pst)
    print("  Stopfen <-> vordere Hälfte: %.2f mm (Flansch liegt auf: 0), hintere Hälfte %.2f" % (dv.min(), dh.min()))
    zap = [T([s.TEIL_X - 0.01, (y0 + y1) / 2, (z0 + z1) / 2], csg.R([0, 90, 0], csg.Cyl(s.ZAPFEN_L, d=s.ZAPFEN_D)))
           for y0, y1, z0, z1, sw in s._boecke()]
    pz = shell_points(U(*zap), 0.2)
    print("  Steckzapfen <-> hintere Hälfte (Loch): %.2f mm" % hinten.sdf(pz).min())
    print("  vordere <-> hintere Hälfte: %.2f mm (Teilung liegt an: 0)" % hinten.sdf(pv).min())
    print("== Sichtkegel (Stopfen draussen) ==")
    for nm, L, a, h, u, wh, wv, r0 in k.sichtkegel():
        cone = k.kegel_node(L, a, h, u, wh, wv, r0)
        dd = cone.sdf(pts); i = int(np.argmin(dd))
        print("  %-20s ± %.1f° / ± %.1f°: kleinster Abstand %.2f mm bei %s" % (nm, wh, wv, dd[i], np.round(pts[i], 1).tolist()))
    print("== Aufschieben (vordere Hälfte von vorne, hintere von hinten) ==", flush=True)
    csg.MARGIN = 1.5
    GERAET = U(*[P[n] for n in ("lid", "tub", "turntable", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "alu", "head", "side",
                                "diff", "cam3", "therm", "horn2", "balls", "wcam", "pir", "mic")])
    for nm, q, sg, weg in (("vordere Hälfte", pv, -1, 50.0), ("hintere Hälfte", ph, +1, 90.0)):
        auf_q = q[:, 2] < v5.LIDTOP + 0.4
        schlimm = (9.0, 0.0)
        for t in np.arange(0.0, weg + 0.01, 0.5):
            d = GERAET.sdf(q + np.array([sg * t, 0, 0]))
            d[auf_q] = np.maximum(d[auf_q], 0.0)
            if d.min() < schlimm[0]:
                schlimm = (float(d.min()), float(t))
        print("  %-15s Weg %.0f mm: kleinster Abstand %.2f mm (bei %.1f mm)%s" % (nm, weg, schlimm[0], schlimm[1],
              "" if schlimm[0] > -0.05 else "  <-- stösst an"), flush=True)
    print("== Sperre ==", flush=True)

    def mind(tilt, pan, teile):
        Q2 = v53.placed(tilt, pan)
        return min(Q2[n].sdf(pts).min() for n in teile)

    def anschlag(fn, bis=5.0):
        a, b = 0.0, bis
        if fn(b) > 0:
            return None
        for _ in range(11):
            m = (a + b) / 2
            a, b = (m, b) if fn(m) > 0 else (a, m)
        return b
    PAN = ("head", "side", "lamp1", "lamp2", "yoke", "arm2", "turntable", "diff")
    for nm, fn in (("Neigen +", lambda w: mind(w, 180.0, ("head", "side", "diff"))), ("Neigen -", lambda w: mind(-w, 180.0, ("head", "side", "diff"))),
                   ("Schwenken +", lambda w: mind(0.0, 180.0 + w, PAN)), ("Schwenken -", lambda w: mind(0.0, 180.0 - w, PAN))):
        w = anschlag(fn)
        print("  %-12s Anschlag nach %s" % (nm, "%.2f°" % w if w else "> 5°"), flush=True)
    print("== Last: 5 kg auf dem Dach (Schätzung) ==")
    E, sig_c, sig_t = 2000.0, 45.0, 40.0                   # PETG gedruckt, in der Schichtebene (MPa)
    L = s.DACH_X_KNICK - s.X0                              # Rippen spannen von der Stirnwand bis zum Knick (einfach gestützt)
    b, t, h, tr = 12.0, s.WAND, s.RIPPE_H, s.RIPPE_T      # mitwirkende Breite = Rippenabstand
    A1, y1 = b * t, t / 2; A2, y2 = tr * h, t + h / 2
    yb = (A1 * y1 + A2 * y2) / (A1 + A2)
    Iy = b * t ** 3 / 12 + A1 * (yb - y1) ** 2 + tr * h ** 3 / 12 + A2 * (y2 - yb) ** 2
    for fall, F, n in (("Punktlast 5 kg auf EINER Rippe", 49.05, 1), ("5 kg auf 2 Rippen (Fläche ≥ 12 mm breit)", 49.05, 2),
                       ("Punktlast 5 kg × 2 (Stoss) auf einer Rippe", 98.1, 1)):
        Mm = F / n * L / 4
        sc, stt = Mm * (t + h - yb) / Iy, Mm * yb / Iy
        dl = F / n * L ** 3 / (48 * E * Iy)
        print("  %-42s M %.0f Nmm  Druck %.1f MPa, Zug %.1f MPa -> Sicherheit %.1f; Durchbiegung %.2f mm (Luft zum Diffusor %.1f)"
              % (fall, Mm, sc, stt, min(sig_c / sc, sig_t / stt), dl, s.DACH_LUFT))
    print("  (Spannweite %.0f mm, Rippe %.0f × %.0f mm im Abstand 12 mm auf %.1f mm Dach, I = %.0f mm⁴)" % (L, tr, h, t, Iy))
    print("  (%.0fs)" % (time.time() - t0))

