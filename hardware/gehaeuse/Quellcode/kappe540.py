"""MoveEye Gehäuse 5.4.0 – 29 Transportsicherung (Kappe): wird von oben über Kopf und Gabel geschoben, sperrt Schwenken (Pan)
und Neigen (Tilt) und rastet am Deckel ein (2 Rastzungen unter dem Dach des Kabelkamins), ohne Werkzeug abnehmbar.
Auftrag des Besitzers vom 14.11.2026 (Zweig geh-transportkappe). Nur ein ZUSÄTZLICHES Teil: alle Teile v5.3 (und v5.1 / v5.2:
Kopf, Gabel, Lampen und Kabelkamin sind dort gleich) bleiben genau wie sie sind. v53.py, v52.py, v5.py und pantilt.py werden nur
importiert; jedes Mass unten ist aus deren Parametern abgeleitet.

Aufbau (Kopf in Grundstellung: schaut nach vorne zur Stirnseite mit PIR und Mikrofon, pan 180, tilt 0):
  - Haube über dem Kopf: Dach auf dem Kopf (Luft DACH_LUFT), Rückwand hinter dem Kopf (Luft PASS, in der Mitte zwischen den
    Armen bis unter die Kippachse, über dem Kabelschlitz), Seitenwände aussen an den Lampenbechern (Luft PASS).
    Kopf hinten über und unter der Kippachse (+ Dach) sperrt das Neigen, Kopf hinten + Lampen sperren das Schwenken.
  - Vorne ist alles offen: kein Material vor X_VORNE (1 mm hinter der vordersten Linsen-Ebene, Lampen). Damit können Kamera
    (auch Weitwinkel), Wärmebild und beide Lampen nichts von der Kappe sehen, egal wie gross ihr Winkel ist (check540.py rechnet
    die Sichtkegel trotzdem nach). Loch im Dach für den Diffusor der Status-LED (v5.2 / v5.3).
  - Rücken (45°) über der Kabelschlaufe hinter dem Kopf zum Kabelkamin; dort kurze Wangen hinten und Rückwand um den Kamin
    (Lage), vorne 2 Pfeiler mit Krallen
    vor den vorderen Kamin-Ecken (Anschlag nach hinten) und 2 Rastzungen mit Nase unter dem Kamin-Dach (hält die Kappe unten).
    Die Kappe steht mit Wangen und Rückwand auf dem Deckel.
  - Lösen: die beiden Drücker oben an den Zungen (über dem Kamin-Dach, von der Seite erreichbar) zum Kopf hin drücken, dann die
    Kappe hinten anheben und nach oben abziehen – wie die Klammern des Sicherungshalters: drücken, frei.
  - Drücken nicht: auf Servos, Hörner, Kabel, Flachkabel; die Kabelschlaufe hinter dem Kopf und die Lampenkabel bleiben frei.
Druck: umgedreht, Dach unten (alle Wände senkrecht, Rücken 45°, kleine Fasen), ohne Stützen.
Koordinaten wie v5.py (Unterteil: x 0 = Stirnwand innen, Kopf schaut nach -x, z = 0 Bodenunterseite). Masse in mm.
Ändern -> python3 export540.py, prüfen -> python3 check540.py, Bilder -> python3 prev540.py
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
PASS = 0.3                           # Passung PETG an den Anlageflächen (Kopf hinten, Lampen, Kamin)
DACH_LUFT = 0.5                      # Dach über dem Kopf: etwas mehr (Höhen addieren sich über Laufring, Kugeln, Gabel, Kopf)
WAND = 2.0                           # Wandstärke
VORNE_RESERVE = 1.0                  # kein Material vor der hintersten Linsen-Ebene minus diese Reserve
DIFF_LUFT = 1.5                      # Luft um den Diffusor der Status-LED
RUECK_LUFT = 2.0                     # Rückwand der Haube beginnt so weit über den Armen (Kippachsen-Rundung)
RUECK_MITTE_LUFT = 4.5               # Mitte der Rückwand (zwischen den Armen) reicht bis so weit über den Kabelschlitz im Kopf:
                                     #   Anlage unter der Kippachse -> Neigen in beide Richtungen gesperrt
ARM_LUFT = 2.0                       # Mitte der Rückwand <-> Innenseite der Arme
SEITE_UNTER = 10.0                   # Seitenwände reichen so weit unter die Lampenachse (Becher ganz anliegend)
RUECKEN_NEIG = 45.0                  # Rücken (Haube -> Kamin), Grad: 45 = druckbar ohne Stützen (Druck umgedreht)
FLANSCH_H = 8.0                      # Randleisten des Rückens (versteifen, bleiben weit über der Kabelschlaufe)
KRALLE_H = 10.5                      # Krallen vor den Kamin-Ecken: Höhe über dem Deckel (an der Aussenseite, 45° zur Mitte)
WANGE_L = 5.0                        # Wangen liegen so lang an den geraden Kamin-Seiten (vor der hinteren Rundung) an
# Rastzungen (Kabelkamin: Dach-Unterseite vorne bei LIDTOP + 7, Öffnung y AY ± 12, Ecken r 3 – v5.part_lid)
ZUNGE_T = 2.2                        # Dicke (biegt in x)
ZUNGE_B = 2.6                        # Breite (y): ganz aussen in der Öffnung, die Kabel liegen in der Mitte auf der Öse
ZUNGE_RAND = 0.5                     # Luft Zunge / Nase <-> Seitenwand der Kamin-Öffnung (y)
ZUNGE_L = 23.0                       # freie Länge (Dehnung beim Einrasten unter 1 %, PETG)
NASE = 1.2                           # Nase greift so weit unter das Kamin-Dach
NASE_H = 0.8                         # senkrechte Fläche vorne an der Nase, darunter 45°-Einführschräge
NASE_SPIEL = 0.3                     # Luft Nase <-> Dach-Unterseite (Wangen stehen auf dem Deckel)
FUSS_SPIEL = 0.5                     # Krallen / Zungen über dem Deckel
DRUECKER = (2.8, 7.0)                # Drücker hinten an der Zunge über dem Kamin-Dach: Tiefe (x), Höhe (z)
DRUECKER_LUFT = 0.5                  # über dem Kamin-Dach
SPALT = 0.5                          # Schlitz zwischen Zunge und Kralle (die Kralle reicht bis vor die runde Kamin-Ecke)
FASE = 1.2                           # Einführschräge innen unten an Seitenwänden und Rückwand der Haube

# ======================= ABGELEITET (aus v5 / v52 / pantilt) =============


def pan_w(px, py, pz):
    """Pan-Koordinaten (Grundstellung pan 180) -> Unterteil"""
    return AX - px, AY - py, v5.PAN_Z0 + pz


Z_KIPP = v5.PAN_Z0 + pt.AXZ                              # Kippachse
KOPF_OBEN = Z_KIPP + pt.HH / 2
KOPF_HINTEN = AX - pt.HX0
KOPF_Y = (AY - pt.HW / 2, AY + pt.HW / 2)
ARM_OBEN = Z_KIPP + pt.ARM_W / 2
LAMPE_Z = v5.PAN_Z0 + v5.LAMP_Z                          # Lampenachse
LAMPE_R = v5.LAMP_Y + v5.CUP_OD / 2                      # Becher aussen ab AY
LAMPE_X = (AX - v5.CUP_X1, AX - v5.LAMP_TAB_X0)          # Lampenhalter vorne / hinten
LINSE_X = {"lampe": AX - (v5.CUP_X0 + v5.CUP_BACK + 2.5 + v5.LAMP_MOD_L),
           "kamera": AX - (pt.FB + 1.0), "waermebild": AX - (pt.FB - pt.THERM_STAND + 7.0)}
X_VORNE = max(LINSE_X.values()) + VORNE_RESERVE
DIFF_XY = (AX - v52.SLED_X, AY - v52.SLED_Y)
# Kabelkamin (v5.part_lid: RBox 16 × 30 × 9, r 3, vorne offen bis LIDTOP + 7 auf y AY ± 12)
KA_X = (v5.CHIM_X - 8.0, v5.CHIM_X + 8.0)
KA_Y = (AY - 15.0, AY + 15.0)
KA_R = 3.0
KA_OBEN = LIDTOP + 9.0
KA_DACH_UNTEN = LIDTOP + 7.0
KA_OFFEN_Y = (AY - 12.0, AY + 12.0)

# Haube
H_X0, H_X1 = X_VORNE, KOPF_HINTEN + PASS + WAND
H_Y0, H_Y1 = AY - LAMPE_R - PASS - WAND, AY + LAMPE_R + PASS + WAND
DACH_Z0 = KOPF_OBEN + DACH_LUFT
DACH_Z1 = DACH_Z0 + WAND
RUECK_Z0 = ARM_OBEN + RUECK_LUFT
KOPF_SCHLITZ_OBEN = Z_KIPP - pt.HH / 2 + 8.5 + 3.0      # Oberkante Kabelschlitz in der Kopf-Rückwand (pantilt.part_head)
RUECK_MITTE_Z0 = KOPF_SCHLITZ_OBEN + RUECK_MITTE_LUFT
RUECK_MITTE_Y = (AY - pt.A1 + ARM_LUFT, AY + pt.A1 - ARM_LUFT)
SEITE_Z0 = LAMPE_Z - SEITE_UNTER
# Rücken und Kamin-Teil
R_Y0, R_Y1 = KA_Y[0] - PASS - WAND, KA_Y[1] + PASS + WAND
R_X0 = KOPF_HINTEN + PASS                              # beginnt an der Innenseite der Haube-Rückwand
R_X1 = KA_X[1] + PASS + WAND
K_TAN = math.tan(math.radians(RUECKEN_NEIG))
R_DICKE_Z = WAND / math.cos(math.radians(RUECKEN_NEIG))  # senkrechte Dicke des schrägen Rückens
KR_X = (KA_X[0] - PASS - WAND, KA_X[0] - PASS)          # Pfeiler, Krallen und Zungen vor dem Kamin
WANGE_X0 = KA_X[1] - KA_R - WANGE_L                      # Wangen vorne (dazwischen das Fenster für den Finger)
Z_X = (KA_X[0] - PASS - ZUNGE_T, KA_X[0] - PASS)
NASE_Z1 = KA_DACH_UNTEN - NASE_SPIEL
NASE_Z0 = NASE_Z1 - NASE_H
ZUNGE_Z0 = NASE_Z0 - (NASE + PASS)                      # Ende der 45°-Einführschräge
ZUNGE_Z1 = ZUNGE_Z0 + ZUNGE_L                           # Wurzel


def ruecken_unten(x):
    """Unterseite des Rückens bei x (45° von der Dach-Unterseite an der Haube-Rückwand nach hinten unten)"""
    return DACH_Z0 - (x - R_X0) * K_TAN


def zungen_y(s):
    """y-Bereich der Zunge auf der Seite s = -1 (Kamin y klein) / +1"""
    if s < 0:
        y0 = KA_OFFEN_Y[0] + ZUNGE_RAND
        return y0, y0 + ZUNGE_B
    y1 = KA_OFFEN_Y[1] - ZUNGE_RAND
    return y1 - ZUNGE_B, y1


def kralle_y(s):
    """Innenkante der Kralle (vor der runden Kamin-Ecke, Schlitz SPALT zur Zunge)"""
    return zungen_y(s)[0] - SPALT if s < 0 else zungen_y(s)[1] + SPALT


# ======================= TEIL 29 TRANSPORTSICHERUNG =====================
def _haube():
    dach = box(H_X0, H_X1, H_Y0, H_Y1, DACH_Z0, DACH_Z1)
    rueck = U(box(H_X1 - WAND, H_X1, H_Y0, H_Y1, RUECK_Z0, DACH_Z1),
              box(H_X1 - WAND, H_X1, RUECK_MITTE_Y[0], RUECK_MITTE_Y[1], RUECK_MITTE_Z0, RUECK_Z0 + 1.0))
    seiten = [box(H_X0, H_X1, H_Y0, H_Y0 + WAND, SEITE_Z0, DACH_Z1), box(H_X0, H_X1, H_Y1 - WAND, H_Y1, SEITE_Z0, DACH_Z1)]
    # Einführschräge FASE × 45° innen unten an den Seitenwänden und an der Rückwand (die Kappe findet die Grundstellung selbst)
    f = FASE
    yi0, yi1, xi = H_Y0 + WAND, H_Y1 - WAND, H_X1 - WAND
    fasen = [I(box(H_X0 - 1, H_X1 + 1, yi0 - f - 0.01, yi0 + 0.01, SEITE_Z0 - 1, SEITE_Z0 + f), Plane([0, -1, 1], f - yi0 + SEITE_Z0)),
             I(box(H_X0 - 1, H_X1 + 1, yi1 - 0.01, yi1 + f + 0.01, SEITE_Z0 - 1, SEITE_Z0 + f), Plane([0, 1, 1], f + yi1 + SEITE_Z0)),
             I(box(xi - 0.01, xi + f + 0.01, H_Y0 - 1, H_Y1 + 1, RUECK_MITTE_Z0 - 1, RUECK_MITTE_Z0 + f),
               Plane([1, 0, 1], f + xi + RUECK_MITTE_Z0))]
    return U(dach, rueck, *seiten), fasen


def _ruecken():
    """schräger Rücken (45°) mit 2 Randleisten, über der Kabelschlaufe vom Kopf zum Kamin"""
    lo, hi = ruecken_unten(R_X1), DACH_Z1
    slab = I(box(R_X0, R_X1, R_Y0, R_Y1, lo - 1, hi),
             Plane([K_TAN, 0, 1], DACH_Z0 + R_DICKE_Z + R_X0 * K_TAN),       # z <= Unterseite + Dicke
             Plane([-K_TAN, 0, -1], -(DACH_Z0 + R_X0 * K_TAN)))             # z >= Unterseite
    flansch = []
    for y0 in (R_Y0, R_Y1 - WAND):
        flansch.append(I(box(R_X0, R_X1, y0, y0 + WAND, lo - FLANSCH_H - 1, hi),
                         Plane([K_TAN, 0, 1], DACH_Z0 + R_DICKE_Z + R_X0 * K_TAN),
                         Plane([-K_TAN, 0, -1], -(DACH_Z0 - FLANSCH_H + R_X0 * K_TAN))))
    return U(slab, *flansch)


def _kamin_teil():
    """Rückwand und kurze Wangen hinten (stehen auf dem Deckel), vorne 2 Pfeiler mit Krallen um den Kabelkamin. Zwischen Pfeiler
    und Wange bleibt seitlich ein Fenster: dort erreicht der Finger die Drücker. Alle Oberseiten 45° (Druck umgedreht)."""
    zt = ruecken_unten(R_X1) + R_DICKE_Z
    teile = [box(R_X1 - WAND, R_X1, R_Y0, R_Y1, LIDTOP, zt)]
    kh = LIDTOP + KRALLE_H
    for s in (-1, 1):
        y0, y1 = (R_Y0, R_Y0 + WAND) if s < 0 else (R_Y1 - WAND, R_Y1)
        # Wange: an den geraden Seiten des Kamins (vor der hinteren Rundung), Oberseite 45° nach vorne unten
        teile.append(I(box(WANGE_X0, R_X1, y0, y1, LIDTOP, zt), Plane([-1, 0, 1], zt - R_X1)))
        # Pfeiler vorne aussen: trägt die Kralle, oben im Rücken
        teile.append(box(KR_X[0], KR_X[1], y0, y1, LIDTOP + FUSS_SPIEL, ruecken_unten(KR_X[0]) + 0.5))
        # Kralle vor der runden Kamin-Ecke (Schlitz SPALT zur Zunge), Oberseite 45° zur Mitte hin: z <= kh - |y - yi|
        yi = y1 if s < 0 else y0
        ye = kralle_y(s)
        b = box(KR_X[0], KR_X[1], R_Y0 if s < 0 else ye, ye if s < 0 else R_Y1, LIDTOP + FUSS_SPIEL, kh)
        teile.append(I(b, Plane([0, -s, 1], kh - s * yi)))
    return U(*teile)


def _zunge(s):
    """Rastzunge mit Nase (unter dem Kamin-Dach), Drücker (über dem Dach) und Wurzelblock (am Rücken)"""
    y0, y1 = zungen_y(s)
    x0, x1 = Z_X
    zunge = box(x0, x1, y0, y1, ZUNGE_Z0, ZUNGE_Z1)
    # Nase: oben waagrecht (Rastfläche), vorne senkrecht NASE_H, unten 45° zurück zur Zunge (Einführschräge)
    nase = I(box(x1 - 0.01, x1 + NASE + PASS, y0, y1, ZUNGE_Z0, NASE_Z1), Plane([1, 0, -1], (x1 + NASE + PASS) - NASE_Z0))
    # Drücker hinten über dem Kamin-Dach, Oberseite 45° (Druck umgedreht)
    dz0 = KA_OBEN + DRUECKER_LUFT
    dt, dh = DRUECKER
    drueck = I(box(x1 - 0.01, x1 + dt, y0, y1, dz0, dz0 + dh + dt), Plane([1, 0, 1], x1 + dz0 + dh + dt))
    # Wurzel: dicker Block von der Zunge bis an den Rücken
    wurzel = I(box(x0 - 2.0, x1, y0, y1, ZUNGE_Z1, ruecken_unten(x0 - 2.0) + 0.5),
               Plane([K_TAN, 0, 1], DACH_Z0 + R_X0 * K_TAN + R_DICKE_Z / 2))     # endet im Rücken, nicht darüber
    return U(zunge, nase, drueck, wurzel)


def part_kappe():
    """29 Transportsicherung in Einbaulage (Unterteil-Koordinaten). Druck: umgedreht (Dach unten), ohne Stützen."""
    haube, fasen = _haube()
    body = U(haube, _ruecken(), _kamin_teil(), _zunge(-1), _zunge(+1))
    cut = [cyl_z(DIFF_XY[0], DIFF_XY[1], DACH_Z0 - 1, DACH_Z1 + 1, v52.DIFF_D + 2 * DIFF_LUFT),
           box(H_X0 - 5, R_X1 + 5, H_Y0 - 5, H_Y1 + 5, DACH_Z1, DACH_Z1 + 20), *fasen]
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


def flachkabel_kamin(breite=16.0):
    """Flachkabel CAM0 auf der Öse im Kamin (Breite: Camera Module 3 Standard 16 mm), liegt zwischen Öse und Kamin-Dach"""
    x0, x1, y0, y1 = v53.TIE_LID
    ym = (y0 + y1) / 2
    return box(x0 - 3.0, v5.CHIM_X, ym - breite / 2, ym + breite / 2, LIDTOP + 5.0, KA_DACH_UNTEN - 0.2)


def lampenkabel_pts(s):
    """Lampenkabel: oben hinten aus dem Becher (Schlitz in der Schürze) -> Kabelbügel am Arm -> Gabelboden"""
    yl = AY - s * v5.LAMP_Y
    ya = AY - s * (pt.A1 + pt.ARM_T / 2)
    return [(AX - (v5.LAMP_TAB_X0 + v5.CUP_X0) / 2, yl, LAMPE_Z + v5.CUP_OD / 2), (AX + 12.0, (yl + ya) / 2, LAMPE_Z + 8.0),
            (AX + 16.75, ya, v5.PAN_Z0 + 26.0), (AX + 16.75, ya, v5.PAN_Z0 + 8.0), (AX + 20.0, AY, v5.PAN_Z0 + 6.0)]


def kabel_node(pts, d):
    return v52.kabel(pts, d / 3.0)                         # v52.kabel: Stab Ø 3 × w


def placed(tilt=0.0, pan=180.0):
    """Gehäuse v5.3 unverändert (Kopf in Grundstellung) mit aufgesetzter Kappe"""
    P = v53.placed(tilt, pan)
    P["kappe"] = part_kappe()
    return P


if __name__ == "__main__":
    print("Haube x %.1f..%.1f y %.1f..%.1f, Dach z %.2f..%.2f (Kopf oben %.2f), Rückwand ab z %.1f (Mitte ab %.1f), Seiten ab z %.1f"
          % (H_X0, H_X1, H_Y0, H_Y1, DACH_Z0, DACH_Z1, KOPF_OBEN, RUECK_Z0, RUECK_MITTE_Z0, SEITE_Z0))
    print("Linsen vorne x:", {k: round(v, 2) for k, v in LINSE_X.items()}, " -> kein Material vor x %.2f" % X_VORNE)
    print("Rücken x %.1f..%.1f, Unterseite z %.1f..%.1f; Kamin x %s y %s, Dach unten %.1f" % (R_X0, R_X1, DACH_Z0, ruecken_unten(R_X1),
          KA_X, KA_Y, KA_DACH_UNTEN))
    print("Zungen x %.2f..%.2f, y %s / %s, z %.2f..%.2f (frei %.1f), Nase %.1f mm unter dem Dach, Spiel %.2f"
          % (*Z_X, np.round(zungen_y(-1), 2), np.round(zungen_y(1), 2), ZUNGE_Z0, ZUNGE_Z1, ZUNGE_L, NASE, NASE_SPIEL))
    eps = 1.5 * ZUNGE_T * NASE / ZUNGE_L ** 2
    I_ = ZUNGE_B * ZUNGE_T ** 3 / 12
    print("Zunge: Dehnung beim Einrasten %.2f %%, Federkraft ca. %.1f N (E 2000 MPa)" % (100 * eps, 3 * 2000 * I_ * NASE / ZUNGE_L ** 3))
    lo, hi = part_kappe().bbox()
    print("Kappe Bounding Box", np.round(lo, 1), np.round(hi, 1), " Grösse", np.round(hi - lo, 1))
