"""MoveEye Gehäuse 5.3.1 – PROVISORISCH: Adapter 28 für das alte Waveshare «UPS HAT» (SKU 18306, UPS HAT (EU), später auch
als UPS HAT (A) verkauft; 2 × 18650 in Serie, INA219 auf I2C 0x42) im unveränderten Gehäuse v5.3.
Auftrag des Besitzers vom 08.11.2026 (Zweig geh-ups-alt). Nur ein ZUSÄTZLICHES Teil: alle Teile v5.3 bleiben genau wie sie
sind. v53.py, v52.py und v5.py werden nur importiert.

Aufbau (Stapel von unten): Adapter 28 im Akku-Zaun (statt UPS HAT (E) + 4 × 21700, wie der Entwicklungs-Sockel 13) → Pi 5 mit
Active Cooler auf 4 Bolzen → Abstandsbolzen M2,5 × 17 + GPIO-Verlängerung → UPS HAT (Buchsenleiste unten, Bauteile unten:
8,4-V-Buchse, USB-A, Schalter, Spule) → Halter mit 2 × 18650 oben.

Die Höhe des Stapels ist durch zwei feste Dinge vorgegeben: die 8,4-V-Buchse muss im Service-Fenster (z 35,5–51,5) liegen,
die Zellen müssen unter den Deckel (Unterseite z 68,5). Darum steht der HAT so tief wie möglich (Stecker gerade noch frei)
und der Pi darunter so tief, wie die Abstandsbolzen es verlangen. Der Pi liegt 6 mm weiter links (x) und 5 mm weiter
innen (y) als in v5.3: so liegen 8,4-V-Buchse, USB-A und Schalter im Service-Fenster, und der Batteriehalter bleibt vom
Kabelkamm (x 121–128 an der Lüftungswand) frei.

Lage in x/y aus der Masszeichnung von Waveshare (Draufsicht, Bild des Besitzers vom 08.11.2026; Pixel ausgemessen, ca. ±0,5 mm).
Masse mit «NACHMESSEN» sind geschätzt (Höhen: die Zeichnung hat keine). Geprüft (Waveshare-Wiki / Produktseite 18306):
Platine 56 × 85 mm, Befestigungslöcher Ø 3,0, 2 × 18650 (Zellenlänge < 67 mm), Ladegerät 8,4 V / 2 A, Ausgang 5 V bis
2,5 A, Gesamthöhe «42,05 mm nach dem Aufstecken auf den Pi» (Bezug unklar – siehe HAT_TOP_H).
Koordinaten wie v5.py (Unterteil: x 0..LX innen, x = 0 Stirnwand innen, y = 0 Lüftungswand innen, z = 0 Bodenunterseite).
Ändern -> python3 export531.py, prüfen -> python3 check531.py, Bilder -> python3 prev531.py
"""
import math
import numpy as np
from csg import *
import csg
import v5
import v52
import v53
from v5 import (LX, LY, WALL, ZF, TOPZ, Plane)

# ======================= PARAMETER 5.3.1 ================================
# --- altes UPS HAT (geprüft: Waveshare-Wiki «UPS HAT», Produktseite SKU 18306)
HAT_L, HAT_W = 85.0, 56.0            # Platine (x entlang des Pi, y quer) – Waveshare
HAT_HOLE_D = 3.0                     # Befestigungslöcher – Waveshare
HAT_HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]   # Lochbild wie Pi (58 × 49; 23,5 / 3,5 / 3,5) – Masszeichnung
CELL_D, CELL_L = 18.4, 65.2          # 18650 (Waveshare: Länge < 67 mm, Zellen ohne Schutzplatine)
HAT_T = 1.6                          # NACHMESSEN: Platinendicke
# --- Oberseite: Batteriehalter mit 2 × 18650 (lokal: x ab der Pi-Seite ohne USB, y ab der Kante mit den Buchsen)
HOLDER_X0, HOLDER_X1 = 1.7, 84.4     # Halter entlang x – Masszeichnung (fast die ganze Länge)
HOLDER_Y0, HOLDER_Y1 = 7.6, 49.8     # Halter quer – Masszeichnung (zwischen Buchsen-Reihe und Stiftleiste)
HAT_TOP_H = 22.0                     # NACHMESSEN: Unterseite HAT-Platine -> Oberkante Zellen (1,6 + Halterboden + Ø 18,4 + Wand)
                                     #   Waveshare nennt 42,05 mm Gesamthöhe auf dem Pi – mit der normalen Buchsenleiste
                                     #   (ca. 11 mm Abstand) wären das bis 27,9 mm; dann passt der Stapel NICHT unter den Deckel.
# --- Unterseite (zum Pi hin), alle an der Kante y = 0 des HAT (= Lüftungswand-Seite)
JACK_X, JACK_W, JACK_L, JACK_H = 47.3, 9.0, 14.0, 11.0   # 8,4-V-Hohlbuchse: Mitte x – Masszeichnung; Breite, Länge, Höhe NACHMESSEN
JACK_AXIS = 6.5                      # NACHMESSEN: Achse unter der Platine (übliche Hohlbuchse 5,5 / 2,1 mm)
JACK_OUT = 2.8                       # Überstand über die Platinenkante – Masszeichnung
PLUG_D, PLUG_L = 5.5, 9.5            # Stecker 5,5 / 2,1 mm: Hülse Ø 5,5, Länge 9,5 (dahinter der dickere Griff)
USBA_X, USBA_W, USBA_L, USBA_H = 31.5, 13.2, 14.0, 7.0   # USB-A (5 V OUT): Mitte x – Masszeichnung (Lötlaschen); Rest NACHMESSEN
SW_X, SW_W, SW_L, SW_H = 16.2, 9.0, 4.5, 4.5             # Schiebeschalter ON/OFF: Mitte x – Masszeichnung; Körper NACHMESSEN
SW_OUT = 4.5                         # Schieber steht über die Kante vor – Masszeichnung
IND_X, IND_Y, IND_S, IND_H = 10.0, 18.0, 10.0, 7.0       # NACHMESSEN: hohe SMD-Spule (Mitte x, y, Kante, Höhe)
LED_X0, LED_X1, LED_Y = 69.5, 78.5, 4.8                  # WARNING-LEDs oben (Verpolung der Zellen) – Masszeichnung
# --- Stapel
HAT_GAP = 17.0                       # Pi-Platine oben -> HAT-Platine unten: Abstandsbolzen M2,5 × 17 (wie für Pi 5 + Active
                                     #   Cooler üblich) und eine GPIO-Verlängerung 2 × 20; NACHMESSEN mit den echten Teilen
COOL_H = v53.COOL_TOP - v5.PI_Z - 1.6    # Active Cooler über der Pi-Platine (Annahme v5.3: 14,4) – NACHMESSEN
PX = 68.0                            # Pi-Kante x (v5.3: 74) – damit liegt die 8,4-V-Buchse im Service-Fenster (x 78–120)
PY = 8.0                             # Pi-Kante y (v5.3: 3) – Halter (y ab PY + 7) bleibt vom Kabelkamm (y < 14) frei
SVC_Z0 = v5.PI_Z + 4 - v5.HDMI_H / 2     # Service-Fenster unten (35,5)
SVC_Z1 = v5.PI_Z + 4 + v5.HDMI_H / 2     # oben (51,5)
JACK_MARGIN = 0.5                    # Luft zwischen Stecker-Hülse und Fensterunterkante
ZH = SVC_Z0 + JACK_MARGIN + JACK_AXIS + PLUG_D / 2       # Unterseite HAT-Platine (45,25)
PZ = ZH - HAT_GAP - 1.6              # Unterseite Pi-Platine (26,65; v5.3: 39,5)
# --- Adapter 28 (wie Sockel 13: Rahmen im Akku-Zaun, Klemmrippen, Bolzen für den Pi)
AD_T = 2.5                           # Wände / Rahmen
AD_POST_D = 6.5                      # Bolzen Ø (M2,5-Kernloch 2,2 -> Wand 2,15)
AD_PILOT_D, AD_PILOT_L = 2.2, 8.0    # M2,5 selbstschneidend (Abstandsbolzen mit Aussengewinde oder Schraube M2,5 × 8)
AD_LEAN_Z0 = ZF + v5.FENCE_H + 1.5   # über dem Akku-Zaun (z 10,5) beginnen die linken Bolzen schräg nach -x
AD_LEAN_Z1 = PZ - 4.0                # ... und stehen ab hier senkrecht unter den Pi-Löchern
AD_XB = v5.BAT_X0 + 4.0              # linke Stütze unten (im Zaun, x 77)
AD_WEB_Z1 = ZF + 16.0                # Längswände (x-Richtung) unter den Bolzen-Reihen bis hier

# ======================= ABGELEITET =====================================
HX = [PX + a for a, b in HAT_HOLES]   # Löcher Pi / HAT (Weltkoordinaten)
HY = [PY + b for a, b in HAT_HOLES]
XL, XR = PX + 3.5, PX + 61.5          # Lochreihen x
YF, YB = PY + 3.5, PY + 52.5          # Lochreihen y
TOP = ZH + HAT_TOP_H                  # Oberkante Zellen


def rod(p0, p1, d):
    """Zylinder Ø d von Punkt p0 nach p1"""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    u = p1 - p0; L = np.linalg.norm(u); u /= L
    a = np.array([1.0, 0, 0]) if abs(u[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(u, a); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
    return T(p0, RM(np.column_stack([e1, e2, u]), Cyl(L, d=d)))


def ball(p, d):
    return T(p, Torus(0.0, d / 2))


def lean_x(x0, x1, za, zb):
    """Ebenenpaar für eine schräge Stütze: Mitte x0 bei z = za, x1 bei z = zb (dazwischen linear)"""
    a = (x1 - x0) / (zb - za)
    return a


# ======================= TEIL 28 ADAPTER ================================
def part_adapter():
    """28 Adapter altes UPS HAT: steht im Akku-Zaun (Klemmrippen wie Sockel 13); 4 Bolzen tragen den Pi 5 auf z = PZ.
    Die linken Bolzen beginnen im Zaun und neigen sich über der Zaunkante (< 30°) nach -x unter die Pi-Löcher.
    Druck: Rahmen unten, ohne Stützen."""
    x0, x1 = v5.BAT_X0 + 0.2, v5.BAT_X0 + v5.BAT_L - 0.2            # wie Sockel 13: ca. 0,7 mm Luft pro Seite im Zaun
    y0, y1 = 0.6, v5.BAT_W - 0.2
    zb, t = ZF, AD_T
    frame = D(box(x0, x1, y0, y1, zb, zb + 4.0), box(x0 + t, x1 - t, y0 + t, y1 - t, zb - 1, zb + 5))
    beams = [box(x0, x1, y - t / 2, y + t / 2, zb, zb + 4.0) for y in (YF, YB)]
    # rechte Stütze: Wand quer (y) unter der Lochreihe x = XR, senkrecht
    walls = [box(XR - t / 2, XR + t / 2, y0, YB + 3.5, zb, PZ - 3.0)]
    # linke Stütze: unten senkrecht bei AD_XB, dann schräg bis XL, oben senkrecht
    za, zc = AD_LEAN_Z0, AD_LEAN_Z1
    a = lean_x(AD_XB, XL, za, zc)
    yy0, yy1 = y0, YB + 3.5
    walls.append(box(AD_XB - t / 2, AD_XB + t / 2, yy0, yy1, zb, za + 2.0))       # Überlappung 2 mm an den Knicken:
    slab = I(box(XL - 10, AD_XB + 10, yy0, yy1, za - 1.0, zc + 1.0),               # sonst wird die Wand dort dünn
             Plane([1, 0, -a], AD_XB + t / 2 - a * za), Plane([-1, 0, a], -(AD_XB - t / 2) + a * za))
    walls.append(slab)
    walls.append(box(XL - t / 2, XL + t / 2, yy0, yy1, zc - 2.0, PZ - 3.0))
    # Längswände (x) unter den Lochreihen: steif in x, bis AD_WEB_Z1
    webs = [box(AD_XB, XR, y - t / 2, y + t / 2, zb, AD_WEB_Z1) for y in (YF, YB)]
    posts = []
    for y in (YF, YB):
        posts.append(cyl_z(XR, y, zb, PZ, AD_POST_D))
        posts.append(cyl_z(AD_XB, y, zb, za, AD_POST_D))
        posts.append(rod((AD_XB, y, za), (XL, y, zc), AD_POST_D))
        posts.append(ball((AD_XB, y, za), AD_POST_D))
        posts.append(ball((XL, y, zc), AD_POST_D))
        posts.append(cyl_z(XL, y, zc, PZ, AD_POST_D))
    clamps = []                                                       # Klemmrippen aussen an den Stirnseiten (wie Sockel 13)
    for xc, sgn in ((x0, -1), (x1, 1)):
        for yc in (20.0, 60.0):
            clamps.append(box(min(xc, xc + sgn * (0.7 + v52.SOCK_CLAMP)), max(xc, xc + sgn * (0.7 + v52.SOCK_CLAMP)), yc - 2.0, yc + 2.0, zb, zb + 3.5))
    body = U(frame, *beams, *walls, *webs, *posts, *clamps)
    body = I(body, box(min(x0, XL) - AD_POST_D, x1 + 2, y0 - 1, y1 + 1, zb, PZ))   # nichts über die Pi-Unterseite / unter den Boden
    cut = [cyl_z(x, y, PZ - AD_PILOT_L, PZ + 1, AD_PILOT_D) for x in (XL, XR) for y in (YF, YB)]
    for x in (XR,):                                                   # Fenster in der rechten Wand (Kabel, Material)
        for yc in np.arange(YF + 12.0, YB - 11.0, 11.0):
            cut.append(box(x - 2, x + 2, yc - 4.0, yc + 4.0, zb + 6.0, PZ - 8.0))
    for y in (YF, YB):                                                # Fenster in den Längswänden
        for xc in np.arange(AD_XB + 11.0, XR - 8.0, 12.0):
            cut.append(box(xc - 4.0, xc + 4.0, y - 2, y + 2, zb + 5.0, AD_WEB_Z1 - 3.0))
    return D(body, *cut)


# ======================= DUMMIES (nur Modell, nicht drucken) ============
def pi_dummy():
    """Pi 5 auf dem Adapter (wie v5.internals, verschoben): Platine, USB/Ethernet, GPIO-Stifte"""
    b = PZ + 1.6
    return U(box(PX, PX + 85, PY, PY + 56, PZ, b), box(PX + 66, PX + 87, PY + 2, PY + 54.5, b, b + 16.0),
             box(PX + 7.1, PX + 57.9, PY + 50.0, PY + 55.0, b, b + 8.5))


def cooler_dummy():
    return box(PX + 25, PX + 56, PY + 12, PY + 44, PZ + 1.6, PZ + 1.6 + COOL_H)


def camconn_dummy():
    """Buchsen CAM/DISP 0 und 1 des Pi 5 (Lage wie v52.PI_CAM*_XY, relativ zum Pi)"""
    out = []
    for cx, cy in (v52.PI_CAM1_XY, v52.PI_CAM0_XY):
        x = PX + (cx - (v5.BAT_X0 + 1)); y = PY + (cy - 3.0)
        out.append(box(x - 1.25, x + 1.25, y - 6.5, y + 6.5, PZ + 1.6, PZ + 1.6 + 5.0))
    return U(*out)


def hat_board():
    return D(box(PX, PX + HAT_L, PY, PY + HAT_W, ZH, ZH + HAT_T),
             *[cyl_z(x, y, ZH - 1, ZH + HAT_T + 1, HAT_HOLE_D) for x, y in zip(HX, HY)])


def hat_jack():
    x = PX + JACK_X
    return box(x - JACK_W / 2, x + JACK_W / 2, PY - JACK_OUT, PY - JACK_OUT + JACK_L, ZH - JACK_H, ZH)


def hat_under():
    """Bauteile unten am HAT: Hohlbuchse, USB-A, Schalter (mit Schieber), Spule, Buchsenleiste"""
    xu, xs = PX + USBA_X, PX + SW_X
    return U(hat_jack(),
             box(xu - USBA_W / 2, xu + USBA_W / 2, PY, PY + USBA_L, ZH - USBA_H, ZH),
             box(xs - SW_W / 2, xs + SW_W / 2, PY, PY + SW_L, ZH - SW_H, ZH),
             box(xs - 1.4, xs + 1.4, PY - SW_OUT, PY, ZH - SW_H + 1.0, ZH - 1.0),
             box(PX + IND_X - IND_S / 2, PX + IND_X + IND_S / 2, PY + IND_Y - IND_S / 2, PY + IND_Y + IND_S / 2, ZH - IND_H, ZH),
             box(PX + 7.1, PX + 57.9, PY + 50.0, PY + 55.0, ZH - 8.5, ZH))


def hat_holder():
    """Batteriehalter mit 2 × 18650 (oben)"""
    zb = ZH + HAT_T
    x0, x1, y0, y1 = PX + HOLDER_X0, PX + HOLDER_X1, PY + HOLDER_Y0, PY + HOLDER_Y1
    zc = TOP - CELL_D / 2
    w = (y1 - y0) / 2
    base = box(x0, x1, y0, y1, zb, zc - 2.0)
    ends = [box(x0, x0 + 3.0, y0, y1, zb, zc + 3.0), box(x1 - 3.0, x1, y0, y1, zb, zc + 3.0)]
    cells = [cyl_x(y0 + w * (i + 0.5), zc, (x0 + x1) / 2 - CELL_L / 2, (x0 + x1) / 2 + CELL_L / 2, CELL_D) for i in range(2)]
    return U(base, *ends, *cells)


def hat_leds():
    return box(PX + LED_X0, PX + LED_X1, PY + LED_Y - 1.0, PY + LED_Y + 1.0, ZH + HAT_T, ZH + HAT_T + 0.8)


def standoffs():
    """4 Abstandsbolzen M2,5 × HAT_GAP zwischen Pi und HAT, dazu die GPIO-Verlängerung"""
    return U(*[cyl_z(x, y, PZ + 1.6, ZH, 4.6, fn=6) for x, y in zip(HX, HY)],
             box(PX + 7.1, PX + 57.9, PY + 50.0, PY + 55.0, PZ + 1.6 + 8.5, ZH - 8.5))


def plug_sleeve(extra=0.0):
    """Stecker 5,5 / 2,1: Hülse von der Buchse durch das Service-Fenster nach aussen (Achse entlang y)"""
    x = PX + JACK_X
    y_face = PY - JACK_OUT
    return cyl_y(x, ZH - JACK_AXIS, y_face - PLUG_L, y_face, PLUG_D + 2 * extra)


def usb_plug(extra=0.0):
    """USB-A-Stecker: Metall 12 × 4,5 von der Buchse nach aussen"""
    x = PX + USBA_X
    zc = ZH - USBA_H / 2
    return box(x - 6.0 - extra, x + 6.0 + extra, PY - 12.0, PY, zc - 2.25 - extra, zc + 2.25 + extra)


def placed(tilt=0.0, pan=180.0):
    """Gehäuse v5.3 unverändert (ohne UPS HAT (E), Zellen, Luftkanal 27, Zwischenboden 09 und Lader) mit Adapter und Stapel"""
    P = v53.placed(tilt, pan)
    for k in ("ups", "duct", "shelf", "charger", "pam", "ina", "sockel", "plug"):   # plug: Stopfen 10 ist im Betrieb draussen
        P.pop(k, None)
    P["adapter"] = part_adapter()
    P["pi"] = pi_dummy()
    P["cooler"] = cooler_dummy()
    P["camconn"] = camconn_dummy()
    P["standoff"] = standoffs()
    P["hat"] = hat_board()
    P["hatunder"] = hat_under()
    P["holder18650"] = hat_holder()
    P["hatled"] = hat_leds()
    P["cam0"] = v52.kabel(cable_cam0_pts())
    P["cam1"] = v52.kabel(cable_cam1_pts())
    return P


# ======================= KABEL (Vorschlag) ==============================
def cam_xy(which):
    cx, cy = v52.PI_CAM0_XY if which == 0 else v52.PI_CAM1_XY
    return PX + (cx - (v5.BAT_X0 + 1)), PY + (cy - 3.0)


def cable_cam0_pts():
    """CAM0 (Kopf): Kabelkamin -> in die Mulde zwischen den Zellen -> flach über die vordere Zelle (unter dem Deckel bleiben
    nur HAT_TOP_H-abhängig ca. 1,2 mm!) -> Kabelkamm Schlitz 2 -> an der Wand hinunter -> unter der 8,4-V-Buchse flach zur
    Buchse CAM/DISP 0"""
    sx = v52.fpc_slots()[1]
    cx, cy = cam_xy(0)
    zc = TOP - CELL_D / 2                                           # Zellenachse
    ym = PY + (HOLDER_Y0 + HOLDER_Y1) / 2                           # Mulde zwischen den Zellen
    y1 = PY + HOLDER_Y0 + (HOLDER_Y1 - HOLDER_Y0) / 4               # Scheitel der vorderen Zelle
    zt = (TOP + TOPZ) / 2                                           # zwischen Zelle und Deckel
    zu = ZH - JACK_H - 1.0                                          # unter den Bauteilen des HAT
    return [(v5.CHIM_X, v5.AY, TOPZ + 1.0), (v5.CHIM_X, ym, zc + 5.0), (110.0, ym, zc + 5.0), (114.0, y1 + 5.5, zt),
            (118.0, y1, zt), (sx, y1 - 9.0, zt), (sx, 4.5, TOPZ - 2.5), (sx, 4.5, zu), (cx, 7.0, zu), (cx, cy, PZ + 1.6 + 5.0)]


def cable_cam1_pts():
    """CAM1 (Weitwinkel vorne): wie v5.2 bis unter den Pan-Servo, dann flach an der Lüftungswand (y ~ 4,5) unter dem
    Deckel-Dom (70, 3) und über dem PCA9685 -> Kabelkamm Schlitz 1 -> hinunter -> unter dem HAT zur Buchse CAM/DISP 1"""
    p = v52.cable_cam1_pts()
    sx = v52.fpc_slots()[0]
    cx, cy = cam_xy(1)
    zu = ZH - JACK_H - 1.0
    return p[:3] + [(60.0, 14.0, 53.0), (70.0, 4.5, 52.5), (sx - 3.0, 4.5, 54.0), (sx, 4.5, 50.0), (sx, 4.5, zu),
                    (cx, 7.0, zu), (cx, cy, PZ + 1.6 + 5.0)]


if __name__ == "__main__":
    print("HAT unten z %.2f, Pi unten z %.2f, Zellen oben z %.2f (Deckel unten %.1f -> Luft %.2f mm)" % (ZH, PZ, TOP, TOPZ, TOPZ - TOP))
    print("Pi x %.1f..%.1f  y %.1f..%.1f;  Löcher x %s y %s" % (PX, PX + 85, PY, PY + 56, [XL, XR], [YF, YB]))
    print("8,4-V-Buchse x %.1f (Fenster x %.0f..%.0f), Achse z %.2f (Fenster z %.1f..%.1f)" % (PX + JACK_X, v52.SVC_X0, v52.SVC_X1, ZH - JACK_AXIS, SVC_Z0, SVC_Z1))
    print("USB-A x %.1f, Schalter x %.1f, LEDs x %.1f..%.1f" % (PX + USBA_X, PX + SW_X, PX + LED_X0, PX + LED_X1))
    print("Kühler oben z %.2f, HAT unten %.2f -> Luft über dem Lüfter %.2f mm" % (PZ + 1.6 + COOL_H, ZH, ZH - PZ - 1.6 - COOL_H))
