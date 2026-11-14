"""MoveEye Gehäuse 5.4.0 – 29 Transportsicherung: kleine Haube, die von oben über den Kopf und die beiden Lampenbecher
geschoben wird und an den Lampenbechern einrastet. Sie sperrt das Neigen (Tilt); das Schwenken (Pan) hält der Servo.
Auftrag des Besitzers vom 14.11.2026 (Zweig geh-transportkappe), Runde 2: die erste Kappe (bis zum Kabelkamin, 82 × 131 × 86 mm)
war zu gross für den Rucksack -> so klein wie möglich, nur über Kopf und Lampen. Nur ein ZUSÄTZLICHES Teil: alle Teile v5.3
(und v5.1 / v5.2: Kopf, Gabel und Lampen sind dort gleich) bleiben genau wie sie sind. v53.py, v52.py, v5.py und pantilt.py werden
nur importiert; jedes Mass unten ist aus deren Parametern abgeleitet.

Aufbau (Kopf in Grundstellung: schaut nach vorne zur Stirnseite mit PIR und Mikrofon, pan 180, tilt 0):
  - Dach auf dem Kopf (Luft DACH_LUFT) mit Loch für den Diffusor der Status-LED (Passung: hält die Haube vorne / hinten),
    Rückwand hinter dem Kopf (Luft PASS) zwischen den Armen, über und unter der Kippachse, über dem Kabelschlitz.
  - Vom Dachrand 45° schräg nach aussen über die Arme und Lampen, dann kurze Seitenwände aussen an den Lampenbechern mit je
    einer Rastlippe, die unter die dickste Stelle des Bechers schnappt (beide Seitenwände federn beim Aufschieben aus).
  - Die Lampen sind an die Arme der Gabel geschraubt: Kopf (Dach, Rückwand) gegen Lampen = Kopf gegen Gabel -> Neigen gesperrt.
  - Vorne ist alles offen: kein Material vor X_VORNE (1 mm hinter der vordersten Linsen-Ebene, Lampen). Kamera (auch
    Weitwinkel), Wärmebild und Lampen sehen nichts von der Haube (check540.py rechnet die Sichtkegel trotzdem nach).
  - Hinten endet die Haube über den Lampen vor dem Kabelschlitz der Lampenhalter (die Lampenkabel bleiben frei).
  - Schwenken: kein festes Teil in kurzer Reichweite. Variante PAN_BEINE = True (nur Vorschlag, nicht als Druckdatei): 2 Beine
    hinter den Lampen bis an die Längsseiten des Deckels (klemmen) – die Haube wird dann deutlich höher.
  - Aufsetzen und Abnehmen mit einer Hand: aufdrücken bis es klickt, zum Abnehmen gerade nach oben ziehen.
Druck: umgedreht, Dach unten (Schrägen 45°, Wände senkrecht, Rastlippen mit 45°-Flächen), ohne Stützen.
Koordinaten wie v5.py (Unterteil: x 0 = Stirnwand innen, Kopf schaut nach -x, z = 0 Bodenunterseite). Masse in mm.
Ändern -> python3 export540.py, prüfen -> python3 check540.py [--beine], Bilder -> python3 prev540.py
"""
import math
import numpy as np
from csg import *
import csg
import pantilt as pt
import v5
import v52
import v53
from v5 import (AX, AY, LIDTOP, Plane)

# ======================= PARAMETER 5.4.0 ================================
PASS = 0.3                           # Passung PETG an den Anlageflächen (Kopf hinten, Lampenbecher)
DACH_LUFT = 0.5                      # Dach über dem Kopf: etwas mehr (Höhen addieren sich über Laufring, Kugeln, Gabel, Kopf)
DIFF_PASS = 0.3                      # Loch um den Diffusor der Status-LED (hält die Haube in x / y auf dem Kopf)
WAND = 2.0                           # Wandstärke
VORNE_RESERVE = 1.0                  # kein Material vor der hintersten Linsen-Ebene minus diese Reserve
RAST = 1.4                           # Rastlippe greift so weit unter die dickste Stelle des Lampenbechers
RUECK_MITTE_LUFT = 4.5               # Rückwand (zwischen den Armen) endet so weit über dem Kabelschlitz im Kopf
ARM_LUFT = 2.0                       # Rückwand <-> Innenseite der Arme
KABEL_LUFT = 0.5                     # Haube endet über den Lampen so weit vor dem Kabelschlitz der Lampenhalter
FASE = 1.2                           # Einführschräge innen unten an der Rückwand
# Variante mit Pan-Sperre (nur Vorschlag): Beine hinter den Lampen bis an die Längsseiten des Deckels
PAN_BEINE = False
BEIN_X = (49.5, 52.3)                # hinter den Lampenhaltern (enden bei x 48,7)
BEIN_T = 3.0                         # Dicke des Beins (federt beim Aufsetzen)
BEIN_KLEMM = 0.2                     # Übermass an der Deckel-Seite (klemmt)
BEIN_TIEF = 4.0                      # Bein reicht so weit unter die Deckel-Oberseite (Deckel 3 mm + 1 mm Unterteil)

# ======================= ABGELEITET (aus v5 / v52 / pantilt) =============
Z_KIPP = v5.PAN_Z0 + pt.AXZ                              # Kippachse
KOPF_OBEN = Z_KIPP + pt.HH / 2
KOPF_HINTEN = AX - pt.HX0
KOPF_D = pt.HW / 2                                       # halbe Kopfbreite (y ab AY)
LAMPE_Z = v5.PAN_Z0 + v5.LAMP_Z                          # Lampenachse
BECHER_R = v5.CUP_OD / 2
LAMPE_R = v5.LAMP_Y + BECHER_R                           # Becher aussen ab AY
LINSE_X = {"lampe": AX - (v5.CUP_X0 + v5.CUP_BACK + 2.5 + v5.LAMP_MOD_L),
           "kamera": AX - (pt.FB + 1.0), "waermebild": AX - (pt.FB - pt.THERM_STAND + 7.0)}
X_VORNE = max(LINSE_X.values()) + VORNE_RESERVE
LAMPE_SCHLITZ_X = AX - v5.CUP_X0                         # Kabelschlitz in der Schürze des Lampenhalters beginnt hier
DIFF_XY = (AX - v52.SLED_X, AY - v52.SLED_Y)
KOPF_SCHLITZ_OBEN = Z_KIPP - pt.HH / 2 + 8.5 + 3.0      # Oberkante Kabelschlitz in der Kopf-Rückwand (pantilt.part_head)
D_DECKEL = v5.LY / 2 + v5.WALL                           # Längsseiten des Deckels ab AY (AY = LY / 2)

H_X0 = X_VORNE
H_X1 = KOPF_HINTEN + PASS + WAND                         # hinten (Rückwand)
S_X1 = LAMPE_SCHLITZ_X - KABEL_LUFT                      # Schrägen und Seitenwände enden hier
DACH_Z0 = KOPF_OBEN + DACH_LUFT
DACH_Z1 = DACH_Z0 + WAND
RUECK_MITTE_Z0 = KOPF_SCHLITZ_OBEN + RUECK_MITTE_LUFT
RUECK_Y = (AY - pt.A1 + ARM_LUFT, AY + pt.A1 - ARM_LUFT)
SCHRAEG_T = WAND * math.sqrt(2.0)                        # senkrechte Dicke der 45°-Schräge
# Seitenwand (Abstand d ab AY) und Rastlippe
D_WI = LAMPE_R + PASS                                    # Innenseite Seitenwand
D_WA = D_WI + WAND
D_LIPPE = LAMPE_R - RAST                                 # Spitze der Lippe
LIPPE_H = D_WI - D_LIPPE                                 # 45°-Flächen oben und unten
LIPPE_Z = LAMPE_Z - math.sqrt(BECHER_R ** 2 - (D_LIPPE - v5.LAMP_Y) ** 2)   # Spitze liegt auf dem Becher
WAND_Z0 = LIPPE_Z - LIPPE_H                              # Unterkante Seitenwand


def schraeg_unten(d):
    """Unterseite der 45°-Schräge im Abstand d von AY (vom Dachrand über dem Kopf nach aussen unten)"""
    return DACH_Z0 - (d - KOPF_D)


WAND_Z1 = schraeg_unten(D_WI) + 1.0                      # Seitenwand oben (geht in die Schräge über)


def ebene_d(s, a_d, a_z, b):
    """Halbraum a_d·d + a_z·z <= b mit d = s·(y - AY) (s = -1: Seite y klein, +1: Seite y gross)"""
    return Plane([0, a_d * s, a_z], b + a_d * s * AY)


def y_von(s, d0, d1):
    a, b = AY + s * d0, AY + s * d1
    return min(a, b), max(a, b)


# ======================= TEIL 29 TRANSPORTSICHERUNG =====================
def _seite(s):
    """Schräge, Seitenwand und Rastlippe auf der Seite s"""
    y0, y1 = y_von(s, KOPF_D - 1.0, D_WA)
    schraeg = I(box(H_X0, S_X1, y0, y1, schraeg_unten(D_WA) - 1, DACH_Z1),
                ebene_d(s, -1, -1, -(DACH_Z0 + KOPF_D)),                      # z >= Unterseite
                ebene_d(s, 1, 1, DACH_Z0 + KOPF_D + SCHRAEG_T))              # z <= Unterseite + Dicke
    w0, w1 = y_von(s, D_WI, D_WA)
    wand = box(H_X0, S_X1, w0, w1, WAND_Z0, WAND_Z1)
    l0, l1 = y_von(s, D_LIPPE, D_WI + 0.01)
    lippe = I(box(H_X0, S_X1, l0, l1, LIPPE_Z - LIPPE_H, LIPPE_Z + LIPPE_H),
              ebene_d(s, -1, -1, -(LIPPE_Z - LIPPE_H + D_WI)),                # unten: Einführschräge 45°
              ebene_d(s, -1, 1, LIPPE_Z + LIPPE_H - D_WI))                    # oben: Rastfläche 45° (lösbar durch Ziehen)
    teile = [schraeg, wand, lippe]
    if PAN_BEINE:
        teile += _bein(s)
    return teile


def _bein(s):
    """Variante: Bein hinter dem Lampenhalter bis an die Längsseite des Deckels (klemmt mit BEIN_KLEMM). Seitenwand nach hinten
    verlängert, dann 45° nach innen unten und senkrecht an die Deckel-Seite. Alle Oberseiten 45° (Druck umgedreht)."""
    bx0, bx1 = BEIN_X
    d_in = D_DECKEL - BEIN_KLEMM
    d_aus = d_in + BEIN_T
    tb = BEIN_T * math.sqrt(2.0)
    z_a = WAND_Z0 - 1.0                                   # Oberkante des schrägen Stücks an der Seitenwand aussen
    w0, w1 = y_von(s, D_WI, D_WA)
    verl = U(I(box(S_X1 - 0.01, bx1, w0, w1, WAND_Z0, WAND_Z1), Plane([1, 0, 1], S_X1 + WAND_Z1)),
             box(bx0, bx1, w0, w1, z_a - tb - 1.0, WAND_Z0 + 0.5))
    y0, y1 = y_von(s, d_in, D_WA)
    band = I(box(bx0, bx1, y0, y1, LIDTOP - BEIN_TIEF, z_a),
             ebene_d(s, -1, 1, z_a - D_WA),                               # oben:  z <= z_a - (D_WA - d)
             ebene_d(s, 1, -1, -(z_a - D_WA - tb)))                       # unten: z >= z_a - (D_WA - d) - tb
    y2, y3 = y_von(s, d_in, d_aus)
    bein = box(bx0, bx1, y2, y3, LIDTOP - BEIN_TIEF, z_a - (D_WA - d_aus))
    return [verl, band, bein]


def part_kappe():
    """29 Transportsicherung in Einbaulage (Unterteil-Koordinaten). Druck: umgedreht (Dach unten), ohne Stützen."""
    dach = box(H_X0, H_X1, AY - KOPF_D - 0.5, AY + KOPF_D + 0.5, DACH_Z0, DACH_Z1)
    rueck = box(H_X1 - WAND, H_X1, RUECK_Y[0], RUECK_Y[1], RUECK_MITTE_Z0, DACH_Z1)
    body = U(dach, rueck, *_seite(-1), *_seite(+1))
    xi = H_X1 - WAND
    fase = I(box(xi - 0.01, xi + FASE + 0.01, RUECK_Y[0] - 1, RUECK_Y[1] + 1, RUECK_MITTE_Z0 - 1, RUECK_MITTE_Z0 + FASE),
             Plane([1, 0, 1], FASE + xi + RUECK_MITTE_Z0))
    cut = [cyl_z(DIFF_XY[0], DIFF_XY[1], DACH_Z0 - 1, DACH_Z1 + 1, v52.DIFF_D + 2 * DIFF_PASS),
           box(H_X0 - 5, H_X1 + 5, -100, 200, DACH_Z1, DACH_Z1 + 50), fase]
    return D(body, *cut)


# ======================= SICHTFELDER (nur Prüfung) ======================
# Kamera: Camera Module 3 NoIR (66° × 41°) – gerechnet mit der Weitwinkel-Ausführung 102° × 67° (+2° Reserve), damit auch die
# Wide-NoIR passt. Wärmebild Thermal-90: 90° (gerechnet 90° × 90° + 2°). Lampen: Abstrahlwinkel unbekannt, gerechnet 120°.
SICHT = {
    "kamera": (53.0, 35.5),
    "waermebild": (47.0, 47.0),
    "lampe": (60.0, 60.0),
}


def sichtkegel():
    """[(Name, Linse vorne (Punkt), Achse, Bild-waagrecht, Bild-oben, halber Winkel waagrecht / senkrecht, Startradius)]"""
    a, h, u = np.array([-1.0, 0, 0]), np.array([0, -1.0, 0]), np.array([0, 0, 1.0])
    cy, cz = pt.CAM3_LENS_Y, pt.CAM3_LENS_Z
    ly, lz = pt.therm_pos(*pt.THERM_LENS)
    out = [("Kamera (CM3 / Wide)", np.array([LINSE_X["kamera"], AY - cy, Z_KIPP + cz]), a, h, u, *SICHT["kamera"], 4.25),
           ("Wärmebild", np.array([LINSE_X["waermebild"], AY - ly, Z_KIPP + lz]), a, h, u, *SICHT["waermebild"], 2.5)]
    for s, nm in ((+1, "Lampe weiss"), (-1, "Lampe IR")):
        out.append((nm, np.array([LINSE_X["lampe"], AY - s * v5.LAMP_Y, LAMPE_Z]), a, h, u, *SICHT["lampe"], v5.LAMP_MOD_D / 2))
    return out


def kegel_node(L, a, h, u, wh, wv, r0, lang=400.0):
    """Sichtfeld als Pyramide ab der Linse (Startquerschnitt ± r0), wie v52.wc_window"""
    tH, tV = math.tan(math.radians(wh)), math.tan(math.radians(wv))
    pl = []
    for s in (-1, 1):
        n = s * h - tH * a; pl.append(Plane(n, r0 + n @ L))
        n = s * u - tV * a; pl.append(Plane(n, r0 + n @ L))
    pl.append(Plane(-a, -(a @ L)))
    pl.append(Plane(a, a @ L + lang))
    return I(box(*(sorted([L[0] - lang - 1, L[0] + 1])), L[1] - 2 * lang, L[1] + 2 * lang, L[2] - 2 * lang, L[2] + 2 * lang), *pl)


# ======================= KABEL-FREIRÄUME (nur Prüfung) ==================
KOPF_SCHLITZ = (KOPF_HINTEN, AY + 3.0, Z_KIPP - pt.HH / 2 + 8.5)   # Kabelschlitz unten in der Kopf-Rückwand (pantilt.part_head)


def schlaufe_pts():
    """Kabelschlaufe Kopf -> Kabelkamin (Servo, Kamera-Flachkabel, Status-LED, Lampen), Mittellinie (Annahme, hängt durch)"""
    x, y, z = KOPF_SCHLITZ
    return [(x, y, z), (x + 10.0, y, z - 8.0), (x + 25.0, AY, z - 20.0), (v53.TIE_LID[0] + 2.0, AY, LIDTOP + 6.0),
            (v5.CHIM_X, AY, LIDTOP - 1.0)]


def lampenkabel_pts(s):
    """Lampenkabel: oben hinten aus dem Becher (Schlitz in der Schürze) -> Kabelbügel am Arm -> Gabelboden"""
    yl = AY - s * v5.LAMP_Y
    ya = AY - s * (pt.A1 + pt.ARM_T / 2)
    return [(AX - (v5.LAMP_TAB_X0 + v5.CUP_X0) / 2, yl, LAMPE_Z + BECHER_R), (AX + 12.0, (yl + ya) / 2, LAMPE_Z + 8.0),
            (AX + 16.75, ya, v5.PAN_Z0 + 26.0), (AX + 16.75, ya, v5.PAN_Z0 + 8.0), (AX + 20.0, AY, v5.PAN_Z0 + 6.0)]


def kabel_node(pts, d):
    return v52.kabel(pts, d / 3.0)                         # v52.kabel: Stab Ø 3 × w


def placed(tilt=0.0, pan=180.0):
    """Gehäuse v5.3 unverändert (Kopf in Grundstellung) mit aufgesetzter Haube"""
    P = v53.placed(tilt, pan)
    P["kappe"] = part_kappe()
    return P


# Grösse der ersten Kappe (Runde 1, Commit 9af96b4, bis zum Kabelkamin) – nur für das Vergleichsbild in prev540.py
ALT_BOX = ((24.0, -19.6, 71.5), (106.3, 111.6, 157.3))

if __name__ == "__main__":
    print("Haube x %.1f..%.1f (Schrägen bis %.1f), Dach z %.2f..%.2f (Kopf oben %.2f), Rückwand ab z %.1f, Seitenwände z %.1f..%.1f"
          % (H_X0, H_X1, S_X1, DACH_Z0, DACH_Z1, KOPF_OBEN, RUECK_MITTE_Z0, WAND_Z0, WAND_Z1))
    print("Linsen vorne x:", {k: round(v, 2) for k, v in LINSE_X.items()}, " -> kein Material vor x %.2f" % X_VORNE)
    print("Rastlippe: Spitze d %.2f (Becher aussen %.2f), z %.2f, Höhe ± %.2f; Seitenwand federt beim Aufschieben %.2f mm aus"
          % (D_LIPPE, LAMPE_R, LIPPE_Z, LIPPE_H, LAMPE_R - D_LIPPE))
    for beine in (False, True):
        PAN_BEINE = beine
        lo, hi = part_kappe().bbox()
        print("%s: Bounding Box %s %s  Grösse %s" % ("mit Pan-Beinen" if beine else "Haube", np.round(lo, 1), np.round(hi, 1),
                                                     np.round(hi - lo, 1)))
