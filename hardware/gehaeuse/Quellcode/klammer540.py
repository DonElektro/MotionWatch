"""MoveEye Gehäuse 5.4.0 – 30 Drehsperre-Klammer: sperrt das Schwenken (Pan) für den Transport, zusammen mit der Haube 29
(kappe540.py, sperrt das Neigen). Wunsch des Besitzers vom 14.11.2026 (Zweig geh-transportkappe, Vorschau freigegeben).
Nur ein ZUSÄTZLICHES Teil: alle Teile v5.3 bleiben genau wie sie sind (passt auch auf v5.1 / v5.2: Deckel mit Kabelkamin,
Drehteller und Gabel sind gleich). v5.py und pantilt.py werden nur importiert; jedes Mass unten ist aus deren Parametern abgeleitet.

Aufbau (flach auf dem Deckel, Kopf in Grundstellung pan 180):
  - U um den Kabelkamin: 2 Seitenwände und Rückwand (Luft PASS) halten die Klammer in x / y; je eine Rastnase an den Seitenwänden
    schnappt vor die runden vorderen Kamin-Ecken (die Seitenwände federn NASE aus). Der Kabeleingang vorne im Kamin bleibt frei.
  - 2 schmale Arme auf dem Deckel aussen an der Kabelschlaufe vorbei zu 2 Pfosten, die neben dem Drehteller-Rand an den hinteren
    Ecken des Gabelbodens stehen (Luft PASS): dreht der Kopf, stösst der Gabelboden an einen der Pfosten.
  - Die Pfosten stehen unter den Kabelbügeln an den Armen der Gabel: die Klammer wird darum von HINTEN flach über den Deckel
    eingeschoben und kann nicht nach oben abgehoben werden. Abnehmen: an der Öse hinten nach hinten ziehen (Rastnasen 45°).
  - Öse hinten (Ø OESE_D) für eine Schnur zur Haube 29.
Druck: flach wie eingebaut (Unterseite auf dem Bett), alle Wände senkrecht, Stützen der Pfosten 45°, ohne Stützmaterial.
Koordinaten wie v5.py (Unterteil: x 0 = Stirnwand innen, z = 0 Bodenunterseite). Masse in mm.
Ändern -> python3 export540.py, prüfen -> python3 check540.py, Bilder -> python3 prev540.py
"""
import math
import numpy as np
from csg import *
import pantilt as pt
import v5
import v53
from v5 import (AX, AY, LIDTOP, Plane)

# ======================= PARAMETER =======================================
PASS = 0.3                           # Passung PETG (Kamin, Gabelboden, Drehteller-Rand)
WAND = 2.0
ARM_B = 4.5                          # Breite der Arme auf dem Deckel
POST_T = 4.8                         # Pfosten: Tiefe in x (ab 1,5 mm vor der Hinterkante des Gabelbodens)
POST_B = 4.5                         # Pfosten: Breite in y
NASE = 1.0                           # Rastnase vor der vorderen Kamin-Ecke (Seitenwand federt so weit aus)
NASE_FASE = 0.8                      # 45°-Fasen an der Nase (vorne: Einführung, hinten: lösbar durch Ziehen)
NASE_L = 2.7                         # Länge der Nase in x (vor der Kamin-Ecke; Seitenwand beginnt dort)
STUETZE = 6.0                        # 45°-Stütze hinter dem Pfosten
OESE_D = 3.6                         # Loch für Schnur / Schlüsselring
OESE_RING = 3.0                      # Material um das Loch
OESE_L = 9.0                         # Lasche ragt so weit hinter die Rückwand

# ======================= ABGELEITET ======================================
TT_R = pt.TT_R + PASS                                     # Drehteller-Rand + Luft
KA_X = (v5.CHIM_X - 8.0, v5.CHIM_X + 8.0)                 # Kabelkamin (v5.part_lid: RBox 16 × 30 × 9, r 3)
KA_Y = (AY - 15.0, AY + 15.0)
KA_OBEN = LIDTOP + 9.0
GB_X = (AX - 15.0, AX + 15.0)                             # Gabelboden (pantilt.part_yoke: RBox 30 × …, r 5) in Grundstellung
GB_Y = (AY - pt.BASE_Y1, AY - pt.BASE_Y0)
GB_Z = (v5.PAN_Z0, v5.PAN_Z0 + pt.BASE_T)
GB_R = 5.0
POST_X = (GB_X[1] - 1.5, GB_X[1] + PASS + POST_T - 1.5)
POST_Z1 = GB_Z[1] - 0.3                                   # unter der Oberkante des Gabelbodens (darüber die Kabelbügel)
X_RUECK = KA_X[1] + PASS                                  # Innenseite der Rückwand
X1 = X_RUECK + WAND


def gabelboden_luft():
    cx, cy = (GB_X[0] + GB_X[1]) / 2, (GB_Y[0] + GB_Y[1]) / 2
    return T([cx, cy, LIDTOP - 1], RBox((GB_X[1] - GB_X[0]) + 2 * PASS, (GB_Y[1] - GB_Y[0]) + 2 * PASS, 30, GB_R + PASS))


def post_y(s):
    """y-Bereich des Pfostens: ganz ausserhalb des Drehteller-Randes, an der Hinterkante des Gabelbodens (x = GB_X[1] + PASS)"""
    dy = math.sqrt(TT_R ** 2 - (GB_X[1] + PASS - AX) ** 2)          # |y - AY| am Rand
    return (AY - dy - POST_B, AY - dy) if s < 0 else (AY + dy, AY + dy + POST_B)


def nase_y(s):
    wy0, wy1 = wand_y(s)
    return (wy1, wy1 + NASE) if s < 0 else (wy0 - NASE, wy0)


def wand_y(s):
    return (KA_Y[0] - PASS - WAND, KA_Y[0] - PASS) if s < 0 else (KA_Y[1] + PASS, KA_Y[1] + PASS + WAND)


def oese_lasche(x0, yc, z0, z1, d=OESE_D, ring=OESE_RING, lang=OESE_L):
    """flache Lasche mit Loch (senkrecht), ab x0 nach +x, Ende rund"""
    r = d / 2 + ring
    lasche = U(box(x0 - 0.5, x0 + lang - r, yc - r, yc + r, z0, z1), cyl_z(x0 + lang - r, yc, z0, z1, 2 * r))
    return D(lasche, cyl_z(x0 + lang - r, yc, z0 - 1, z1 + 1, d))


# ======================= TEIL 30 DREHSPERRE-KLAMMER =====================
def part_klammer():
    """30 Drehsperre-Klammer in Einbaulage (Unterteil-Koordinaten). Druck: so wie sie liegt, ohne Stützen."""
    teile = []
    frei = U(gabelboden_luft(), cyl_z(AX, AY, LIDTOP - 1, LIDTOP + 40, 2 * TT_R))
    for s in (-1, 1):
        py0, py1 = post_y(s)
        post = D(box(POST_X[0], POST_X[1], py0, py1, LIDTOP, POST_Z1), frei)
        stuetze = D(I(box(POST_X[1] - 0.01, POST_X[1] + STUETZE, py0, py1, LIDTOP, POST_Z1 - 4),
                      Plane([1, 0, 1], POST_X[1] + POST_Z1 - 4)), frei)              # 45° nach hinten
        ay0, ay1 = (py0, py0 + ARM_B) if s < 0 else (py1 - ARM_B, py1)
        arm = D(box(POST_X[0], X1, ay0, ay1, LIDTOP, LIDTOP + WAND), frei)
        wy0, wy1 = wand_y(s)
        wand = box(KA_X[0] - PASS - NASE_L, X1, wy0, wy1, LIDTOP, KA_OBEN)
        quer = box(KA_X[1] - 6.0, X1, min(ay0, wy0), max(ay1, wy1), LIDTOP, LIDTOP + WAND)
        # Rastnase vor der runden vorderen Ecke: 45°-Fasen vorne und hinten (in x), damit sie über den Kamin gleitet
        ny0, ny1 = nase_y(s)
        xa, xb = KA_X[0] - PASS - NASE_L, KA_X[0] - PASS
        f = NASE_FASE
        w_in = wy1 if s < 0 else wy0                                         # Innenseite der Seitenwand
        nase = I(box(xa, xb, ny0, ny1, LIDTOP + 1.0, KA_OBEN - 1.5),
                 Plane([1, -s, 0], NASE + xb - f - s * w_in),                # hinten 45° (lösen durch Ziehen nach hinten)
                 Plane([-1, -s, 0], NASE - xa - f - s * w_in))               # vorne 45° (Einschieben von hinten)
        teile += [post, stuetze, arm, wand, quer, nase]
    rueck = box(X_RUECK, X1, KA_Y[0] - PASS - WAND, KA_Y[1] + PASS + WAND, LIDTOP, KA_OBEN + 0.3)
    oese = oese_lasche(X1, AY, LIDTOP, LIDTOP + WAND)
    return U(*teile, rueck, oese)


def placed(tilt=0.0, pan=180.0):
    """Gehäuse v5.3 unverändert (Kopf in Grundstellung) mit Haube 29 und Klammer 30"""
    import kappe540
    P = kappe540.placed(tilt, pan)
    P["klammer"] = part_klammer()
    return P


if __name__ == "__main__":
    lo, hi = part_klammer().bbox()
    print("Klammer 30: Bounding Box", np.round(lo, 1), np.round(hi, 1), " Grösse", np.round(hi - lo, 1))
    print("Pfosten x %.1f..%.1f, y %s / %s, z bis %.1f (Kabelbügel ab z %.1f)" % (*POST_X, np.round(post_y(-1), 2),
          np.round(post_y(1), 2), POST_Z1, v5.PAN_Z0 + 6.0))
    print("Rastnasen y %s / %s vor den Kamin-Ecken x %.1f, Öse Ø %.1f hinter x %.1f" % (np.round(nase_y(-1), 2), np.round(nase_y(1), 2),
          KA_X[0], OESE_D, X1))
