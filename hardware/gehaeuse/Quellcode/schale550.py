"""MoveEye Gehäuse 5.5.0 – Schutzschale 31 / 32 mit Stopfen 33: zweiteilige Schale (VORNE 31 / HINTEN 32) über den ganzen Kopf
mit Gabel, Lampen, Arm 2 und Drehteller bis auf den Deckel, damit MoveEye tief im Rucksack liegen kann (bis 5 kg obendrauf).
Auftrag des Besitzers vom 14.11.2026 (Zweig geh-schutzschale), Vorschau vom Besitzer freigegeben (ein Fenster mit einem
Stopfen, Stirnwand als Rand, Lampen abgedeckt). Nur zusätzliche Teile; v5.3 bleibt unverändert. Masse aus v5 / pantilt /
kappe540 abgeleitet. Prüfung: check550.py, printcheck550.py, druckcheck550.py; Export: export550.py; Bilder: prev550.py.

Aufbau (Kopf in Grundstellung, pan 180):
  - Hülle auf dem Deckel: Seitenwände stehen auf den Deckelrändern, Schürzen aussen an den Längsseiten des Deckels; Stirnwand
    vor dem Schirm des Kopfs, Rückwand hinter dem Kabelkamin. Die Last geht über Dach, Wände und Rippen in den Deckel, nie auf
    den Kopf (Dach 3,4 mm über dem Diffusor).
  - Seitliche Ausbuchtungen über den Lampen (unten 45°), bis zur Stirnseite: Lampen abgedeckt.
  - Rippen auf dem Dach in Längsrichtung (x) – nur so sind sie in beiden Hälften ohne Stützen druckbar.
  - Teilung bei x = TEIL_X (mitten durch die Lampenbecher): vordere Hälfte von vorne aufschieben, hintere von hinten (stösst an
    den Kabelkamin). Gedruckte Steckzapfen in Böcken an der Teilung, Gummiring in einer Nut rundum unten.
  - Sperre: 2 Rippen in der hinteren Hälfte liegen hinten am Kopf an (über und unter der Kippachse, PASS) -> Neigen und
    Schwenken; die Seitenwände der Ausbuchtungen liegen an den Lampenbechern an (PASS) -> Schwenken.
  - Sichtfenster vorne für Kamera (gerechnet mit Weitwinkel) und Wärmebild: die beiden Sichtkegel überschneiden sich an der
    Stirnwand -> ein gemeinsames Fenster mit einem Stopfen (dünne Platte mit Rahmen und Kreuzrippe, rastet ein, Öse für die
    Halteschnur).
Druck: vordere Hälfte und Stopfen mit der Stirnseite auf dem Bett, hintere Hälfte mit der Rückseite; alle Rippen senkrecht,
Schrägen 45°.
"""
import math
import numpy as np
from csg import *
import pantilt as pt
import v5
import v52
import v53
import kappe540 as k
from v5 import (AX, AY, LIDTOP, Plane)

# ======================= PARAMETER =======================================
PASS = 0.3
WAND = 2.4
DACH_LUFT = 3.4                      # Dach innen über dem höchsten Punkt (Diffusor) – grösser als die Durchbiegung unter Last
SCHIRM_LUFT = 1.0                    # Stirnwand innen vor dem Schirm des Kopfs
RIPPE_H, RIPPE_T, RIPPE_Y = 8.0, 2.0, (4.0, 16.0, 28.0, 40.0, 52.0, 64.0, 76.0, 88.0)
LAMPE_LUFT_OBEN = 4.6                # Ausbuchtung oben über Lampenhalter (Kabel kommt oben aus dem Becher)
SCHRAEG_Z0 = 76.0                    # Ausbuchtung: 45°-Unterseite beginnt an der Seitenwand aussen hier
TEIL_X = 32.0                        # Teilung vorne / hinten (mitten durch die Lampenbecher x 22..42)
DACH_X_KNICK = 58.0                  # hinter dem Kopf fällt das Dach mit 45° zur Rückwand ab
SCHUERZE_Z1 = 78.0                   # Schürze aussen an den Deckel-Längsseiten bis hier (trägt die Nut; Lippe über der Nut 2 mm)
NUT = (73.5, 76.0, 1.2)              # Gummiring-Nut rundum: z von, bis, Tiefe
RIPPE_KOPF_Y = ((19.0, 21.0), (71.0, 73.0))   # Sperr-Rippen hinten am Kopf (y)
SPERR_LUFT_KABEL = 4.5               # Sperr-Rippen enden so weit über dem Kabelschlitz im Kopf
BOCK = 8.0                           # Böcke an der Teilung für die Steckzapfen
ZAPFEN_D, ZAPFEN_L, ZAPFEN_SPIEL = 4.0, 5.0, 0.2
FENSTER_RAND = 1.0                   # Fenster so viel grösser als die Sichtkegel an der Stirnwand
STOPFEN_SPIEL, STOPFEN_FLANSCH, STOPFEN_FL_T = 0.25, 2.5, 1.4
STOPFEN_RAHMEN, STOPFEN_RIPPE = 1.6, 1.4       # Stopfen: Rahmen im Fenster und Kreuzrippe (statt voll)
BOCK_FASE = 4.0                      # Böcke: 45° zur Wand hin (stützenfrei in Druckrichtung x)
OESE_D = 3.6

# ======================= ABGELEITET ======================================
DECKEL_X0 = -v5.WALL                                     # Deckel aussen vorne
DECKEL_Y = (-v5.WALL, v5.LY + v5.WALL)
KOPF_VORNE = AX - (pt.HX1 + pt.VIS_L)                    # Schirm vorne (x 2,5)
DIFF_OBEN = k.KOPF_OBEN + v52.DIFF_H + 0.3
DACH_Z0 = DIFF_OBEN + DACH_LUFT                          # Dach innen
DACH_Z1 = DACH_Z0 + WAND
X0 = KOPF_VORNE - SCHIRM_LUFT - WAND                     # Stirnwand aussen
X0_IN = X0 + WAND
KA_X1 = v5.CHIM_X + 8.0
X1_IN = KA_X1 + PASS                                     # Rückwand innen (am Kabelkamin)
X1 = X1_IN + WAND
Y_W = ((DECKEL_Y[0] - PASS, DECKEL_Y[0] - PASS + WAND), (DECKEL_Y[1] + PASS - WAND, DECKEL_Y[1] + PASS))   # Seitenwände auf dem Deckel
Y_S = (DECKEL_Y[0] - PASS - WAND, DECKEL_Y[1] + PASS + WAND)                                            # Schürzen aussen
LAMPE_D = k.LAMPE_R + PASS                               # Ausbuchtung innen ab AY
LAMPE_DA = LAMPE_D + WAND
LAMPE_OBEN = v5.PAN_Z0 + v5.LAMP_Z + 14.0                # Oberkante Lampenhalter (Lasche ± 14)
AUS_Z1_IN = LAMPE_OBEN + LAMPE_LUFT_OBEN
AUS_Z1 = AUS_Z1_IN + WAND
AUS_X1 = AX - v5.LAMP_TAB_X0 + PASS + (LAMPE_DA - (AY - Y_W[0][0])) + WAND * math.sqrt(2.0)   # hintere 45°-Fase
SPERR_Z0 = k.KOPF_SCHLITZ_OBEN + SPERR_LUFT_KABEL
T45 = WAND * math.sqrt(2.0)


def dach_oben(x):
    """Dach aussen (flach bis DACH_X_KNICK, dann 45° nach hinten unten)"""
    return DACH_Z1 - max(0.0, x - DACH_X_KNICK)


def prisma_yz(pts, x0, x1):
    """konvexes Polygon in (y, z) (gegen den Uhrzeigersinn), entlang x von x0 bis x1"""
    p = np.array(pts, float)
    e1, e2 = p[1] - p[0], p[2] - p[1]
    if e1[0] * e2[1] - e1[1] * e2[0] < 0:
        p = p[::-1]
    return T([x0, 0, 0], RM([[0, 0, 1], [1, 0, 0], [0, 1, 0]], Prism(p, x1 - x0)))


def _ausbuchtung(s, off):
    """Ausbuchtung über der Lampe auf Seite s (off = 0: Körper aussen, off = WAND: Hohlraum). Profil in (d, z), d = |y - AY|:
    unten 45° von der Seitenwand nach aussen, oben flach über dem Lampenhalter; hinten 45° (Druck mit der Rückseite unten)."""
    d_w = AY - Y_W[0][0]                                             # Seitenwand aussen (beide Seiten gleich)
    if off == 0:
        d0, d1, zt, zb = d_w - WAND, LAMPE_DA, AUS_Z1, 0.0
    else:
        d0, d1, zt, zb = d_w - WAND - 1.0, LAMPE_D, AUS_Z1_IN, T45
    zs = lambda d: SCHRAEG_Z0 + max(0.0, d - d_w) + zb
    pts = [(AY + s * d0, zs(d0)), (AY + s * d1, zs(d1)), (AY + s * d1, zt), (AY + s * d0, zt)]
    x0 = X0 if off == 0 else X0_IN
    x1 = AUS_X1 - (T45 if off else 0.0)
    body = prisma_yz(pts, x0, x1 + 40.0)
    return I(body, Plane([1, s, 0], x1 + d_w + s * AY))             # Ausladung (d - d_w) <= x1 - x


def huelle():
    """geschlossene Hülle (beide Hälften), ohne Fenster"""
    aussen = U(I(box(X0, X1, Y_W[0][0], Y_W[1][1], LIDTOP, DACH_Z1), Plane([1, 0, 1], DACH_Z1 + DACH_X_KNICK)),
               box(X0, X1, Y_S[0], Y_S[1], v5.TOPZ + PASS, SCHUERZE_Z1),
               _ausbuchtung(-1, 0.0), _ausbuchtung(+1, 0.0))
    innen = U(I(box(X0_IN, X1_IN, Y_W[0][1], Y_W[1][0], LIDTOP - 1, DACH_Z0), Plane([1, 0, 1], DACH_Z1 + DACH_X_KNICK - T45)),
              box(X0 - 5, X1 + 5, DECKEL_Y[0] - PASS, DECKEL_Y[1] + PASS, v5.TOPZ, LIDTOP),     # Deckel
              _ausbuchtung(-1, WAND), _ausbuchtung(+1, WAND))
    rippen = []
    for y in RIPPE_Y:
        r = I(box(X0, X1, y - RIPPE_T / 2, y + RIPPE_T / 2, DACH_Z1 - 1, DACH_Z1 + RIPPE_H),
              Plane([1, 0, 1], DACH_Z1 + RIPPE_H + DACH_X_KNICK))
        rippen.append(D(r, I(box(X0 - 1, X1 + 1, -50, 150, 0, 300), Plane([-1, 0, -1], -(DACH_Z1 + DACH_X_KNICK - 0.5)))))
    sperr = [I(box(k.KOPF_HINTEN + PASS, X1_IN + 0.5, y0, y1, SPERR_Z0, DACH_Z0 + 0.5), Plane([1, 0, 1], DACH_Z1 + DACH_X_KNICK - T45 + 0.5))
             for y0, y1 in RIPPE_KOPF_Y]
    # U um den Kabelkamin (hintere Hälfte): Seitenwände
    kamin = [box(v5.CHIM_X - 5.0, X1_IN + 0.5, AY - 15.0 - PASS - WAND, AY - 15.0 - PASS, LIDTOP, LIDTOP + 9.3),
             box(v5.CHIM_X - 5.0, X1_IN + 0.5, AY + 15.0 + PASS, AY + 15.0 + PASS + WAND, LIDTOP, LIDTOP + 9.3)]
    # Nut für den Gummiring: an den Längsseiten rechteckig, an Stirn- und Rückseite als 45°-V (dort liegt die Nut beim Druck
    # quer zur Druckrichtung – ein flacher Nutgrund wäre eine Brücke)
    zm, t = (NUT[0] + NUT[1]) / 2, NUT[2]
    band = box(X0 - 5, X1 + 5, Y_S[0] - 5, Y_S[1] + 5, zm - t - 1, zm + t + 1)
    nut = U(box(X0 - 5, X1 + 5, Y_S[0] - 5, Y_S[0] + t, NUT[0], NUT[1]),
            box(X0 - 5, X1 + 5, Y_S[1] - t, Y_S[1] + 5, NUT[0], NUT[1]),
            I(band, Plane([1, 0, 1], X0 + t + zm), Plane([1, 0, -1], X0 + t - zm)),
            I(band, Plane([-1, 0, 1], -(X1 - t) + zm), Plane([-1, 0, -1], -(X1 - t) - zm)))
    return D(U(D(aussen, innen), *rippen, *sperr, *kamin), nut)


# ======================= FENSTER UND STOPFEN =============================
def fenster_rechtecke():
    """Querschnitte der Sichtkegel Kamera und Wärmebild an der Stirnwand aussen (+ FENSTER_RAND) als Rechtecke (y0, y1, z0, z1)"""
    out = []
    for nm, L, a, h, u, wh, wv, r0 in k.sichtkegel()[:2]:
        t = L[0] - X0
        hy = r0 + t * math.tan(math.radians(wh)) + FENSTER_RAND
        hz = r0 + t * math.tan(math.radians(wv)) + FENSTER_RAND
        y0, y1 = L[1] - hy, min(L[1] + hy, Y_W[1][0])
        z0, z1 = L[2] - hz, min(L[2] + hz, DACH_Z0 - 1.0)
        out.append((nm, y0, y1, z0, z1))
    return out


def kegel_schnitt():
    """die Sichtkegel Kamera und Wärmebild selbst (+ FENSTER_RAND), nur vor den Linsen: so schneidet das Fenster auch die Ecke
    der Seitenwand frei, wo der Weitwinkel-Kegel sie streift"""
    out = []
    for nm, L, a, h, u, wh, wv, r0 in k.sichtkegel()[:2]:
        out.append(k.kegel_node(L, a, h, u, wh, wv, r0 + FENSTER_RAND, lang=60.0))
    # Ecke an der Seitenwand (Kamera, y gross): der Kegel öffnet dort mit 53° – beim Druck (Stirnseite unten) ein Überhang.
    # Darum schräg 45° nachschneiden: von der Kante des Kegels an der Stirnseite aus nach hinten innen.
    nm, L, a, h, u, wh, wv, r0 = k.sichtkegel()[0]
    y_kante = L[1] + r0 + FENSTER_RAND + (L[0] - X0) * math.tan(math.radians(wh))
    _, _, _, cz0, cz1 = fenster_rechtecke()[0]
    out.append(I(box(X0 - 1, X0_IN + 1, Y_W[1][0] - 0.01, Y_W[1][1] + 1, cz0, cz1), Plane([1, 1, 0], X0 + y_kante)))
    return U(*out)


def fenster_node(off=0.0, x0=None, x1=None):
    x0 = X0 - 1 if x0 is None else x0
    x1 = X0_IN + 1 if x1 is None else x1
    return U(*[box(x0, x1, y0 + off, y1 - off, z0 + off, z1 - off) for _, y0, y1, z0, z1 in fenster_rechtecke()])


def oese_huelle():
    """Loch für die Halteschnur des Stopfens: durch die Stirnwand links unter dem Fenster (y, z)"""
    r = fenster_rechtecke()
    return (min(x[1] for x in r) + 4.0, min(x[3] for x in r) - 6.0)


def part_stopfen():
    """Stopfen für das Sichtfenster (in Einbaulage): Platte aussen (Flansch), dünner Rahmen im Fenster mit 4 Rastnasen hinter
    der Stirnwand, Kreuzrippe gegen Eindrücken, Lasche mit Öse für die Halteschnur (zur Öse in der Stirnwand)"""
    nase_t = 0.6
    x_in = X0_IN + nase_t
    rahmen = D(fenster_node(STOPFEN_SPIEL, X0 - 0.01, x_in), fenster_node(STOPFEN_SPIEL + STOPFEN_RAHMEN, X0 - 1, x_in + 1))
    fl = fenster_node(-STOPFEN_FLANSCH, X0 - STOPFEN_FL_T, X0 + 0.01)
    ym, zm = oese_huelle()
    lasche = D(U(box(X0 - STOPFEN_FL_T, X0, ym - 4.0, ym + 4.0, zm, zm + 12.0), cyl_x(ym, zm, X0 - STOPFEN_FL_T, X0, 8.0)),
               cyl_x(ym, zm, X0 - STOPFEN_FL_T - 1, X0 + 1, OESE_D))
    nasen, rippen = [], []
    (_, cy0, cy1, cz0, cz1), (_, ty0, ty1, tz0, tz1) = fenster_rechtecke()
    for zz in (cz0 + 0.5 * (cz1 - cz0), cz1 - 6.0):                  # linke Kante (Kamera-Rechteck)
        nasen.append(box(X0_IN, x_in, cy0 + STOPFEN_SPIEL - 0.5, cy0 + STOPFEN_SPIEL + 0.01, zz - 2.0, zz + 2.0))
    for yy in (ty0 + 8.0, ty1 - 8.0):                                # Unterkante (Wärmebild-Rechteck)
        nasen.append(box(X0_IN, x_in, yy - 2.0, yy + 2.0, tz0 + STOPFEN_SPIEL - 0.5, tz0 + STOPFEN_SPIEL + 0.01))
    innen = fenster_node(STOPFEN_SPIEL + 0.5, X0 - 0.01, X0_IN)
    ym_f = (max(cy0, ty0) + min(cy1, ty1)) / 2
    zm_f = (max(cz0, tz0) + min(cz1, tz1)) / 2
    rippen.append(I(box(X0 - 0.01, X0_IN, ym_f - STOPFEN_RIPPE / 2, ym_f + STOPFEN_RIPPE / 2, -50, 300), innen))
    rippen.append(I(box(X0 - 0.01, X0_IN, -100, 200, zm_f - STOPFEN_RIPPE / 2, zm_f + STOPFEN_RIPPE / 2), innen))
    return U(rahmen, fl, lasche, *nasen, *rippen)


# ======================= TEILE ===========================================
def _boecke():
    """(y0, y1, z0, z1, sw): Böcke an den Seitenwänden innen; sw = +1 Wand bei y0, -1 Wand bei y1"""
    out = []
    for y0, y1, sw in ((Y_W[0][1], Y_W[0][1] + BOCK, +1), (Y_W[1][0] - BOCK, Y_W[1][0], -1)):
        for z0, z1 in ((DACH_Z0 - BOCK, DACH_Z0 + 0.5), (LIDTOP + 2.0, LIDTOP + 2.0 + BOCK)):
            out.append((y0, y1, z0, z1, sw))
    return out


def _bock(y0, y1, z0, z1, sw, sx):
    """Bock an der Teilung: sx = -1 vordere Hälfte (x < TEIL_X), +1 hintere; die freie Unterseite in Druckrichtung (vorne +x,
    hinten -x) ist 45° zur Seitenwand hin gefast: in der Mitte (Zapfen) volle Tiefe BOCK, an der Wand BOCK + BOCK_FASE"""
    tief = BOCK + BOCK_FASE
    yw = y0 if sw > 0 else y1
    b = box(min(TEIL_X, TEIL_X + sx * tief), max(TEIL_X, TEIL_X + sx * tief), y0, y1, z0, z1)
    # Tiefe(d) = tief - d, d = Abstand zur Wand:  sx*(x - TEIL_X) + sw*(y - yw) <= tief
    return I(b, Plane([sx, sw, 0], tief + sx * TEIL_X + sw * yw))


def part_vorne():
    teil = I(huelle(), box(X0 - 10, TEIL_X, -100, 200, 0, 300))
    teil = D(teil, fenster_node(), kegel_schnitt(), cyl_x(*oese_huelle(), X0 - 1, X0_IN + 1, OESE_D))
    boecke, zapfen = [], []
    for y0, y1, z0, z1, sw in _boecke():
        zc = (z0 + z1) / 2
        boecke.append(_bock(y0, y1, z0, z1, sw, -1))
        zapfen.append(T([TEIL_X - 0.01, (y0 + y1) / 2, zc], R([0, 90, 0], Cyl(ZAPFEN_L, d=ZAPFEN_D))))
    return U(teil, *boecke, *zapfen)


def part_hinten():
    teil = I(huelle(), box(TEIL_X, X1 + 10, -100, 200, 0, 300))
    boecke, loecher = [], []
    for y0, y1, z0, z1, sw in _boecke():
        boecke.append(_bock(y0, y1, z0, z1, sw, +1))
        loecher.append(T([TEIL_X - 0.01, (y0 + y1) / 2, (z0 + z1) / 2], R([0, 90, 0], Cyl(ZAPFEN_L + 0.6, d=ZAPFEN_D + 2 * ZAPFEN_SPIEL))))
    return D(U(teil, *boecke), *loecher)


def placed(tilt=0.0, pan=180.0, stopfen=True, explo=0.0):
    P = v53.placed(tilt, pan)
    P["schale_vorne"] = T([-explo, 0, 0], part_vorne())
    P["schale_hinten"] = T([explo, 0, 0], part_hinten())
    if stopfen:
        P["stopfen"] = T([-explo - (12.0 if explo else 0.0), 0, 0], part_stopfen())
    return P


if __name__ == "__main__":
    for nm, f in (("vorne", part_vorne), ("hinten", part_hinten), ("stopfen", part_stopfen)):
        lo, hi = f().bbox()
        print("%-8s %s %s  Grösse %s" % (nm, np.round(lo, 1), np.round(hi, 1), np.round(hi - lo, 1)))
    print("Fenster:", [(n, round(a, 1), round(b, 1), round(c, 1), round(d, 1)) for n, a, b, c, d in fenster_rechtecke()])
    print("Dach innen z %.1f (Diffusor %.1f), Stirnwand x %.1f..%.1f, Rückwand x %.1f..%.1f, Ausbuchtung bis x %.1f, Sperr-Rippen ab z %.1f"
          % (DACH_Z0, DIFF_OBEN, X0, X0_IN, X1_IN, X1, AUS_X1, SPERR_Z0))
