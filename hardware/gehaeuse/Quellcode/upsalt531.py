"""MoveEye Gehäuse 5.3.1 – PROVISORISCH: Adapter 28 für das alte Waveshare «UPS HAT» (SKU 18306, UPS HAT (EU), später auch
als UPS HAT (A) verkauft; 2 × 18650 in Serie, INA219 auf I2C 0x42) im unveränderten Gehäuse v5.3, Deckel zu.
Auftrag des Besitzers vom 08.11.2026 (Zweig geh-ups-alt). Nur ein ZUSÄTZLICHES Teil: alle Teile v5.3 bleiben genau wie sie
sind. v53.py, v52.py und v5.py werden nur importiert.

Runde 2 (08.11.2026): Der Besitzer hat 38 mm von der Unterseite des HAT bis zur Oberkante der Zellen gemessen (statt der
geschätzten 22). Damit passt das HAT nicht mehr so, dass seine 8,4-V-Buchse im Service-Fenster liegt (Stapel 83 mm hoch).
Gewählt (Variante «tief, gedreht»):
  - Adapter 28 = flacher Rahmen im Akku-Zaun mit 4 kurzen Bolzen; der Pi 5 liegt tief (Unterseite z 8), um 180° gedreht
    (Buchsen-Seite des HAT und HDMI/USB-C des Pi zeigen nach +y, ins Gehäuse-Innere; USB/Ethernet zur Stirnseite).
  - Das HAT steckt wie von Waveshare vorgesehen auf dem Pi (GPIO-Verlängerung, Abstandsbolzen), der Active Cooler bleibt.
  - Laden: Einbaubuchse 5,5/2,1 in der Reserve-Öffnung hinten (+x, statt Blindstopfen 17), kurzes Kabel mit Winkelstecker in
    die 8,4-V-Buchse des HAT. Service-Fenster mit Stopfen 10 zu, Deckel zu.
Robust: die Höhe rechnet mit 38 mm ab der HAT-Platine (schlimmster Fall). Wahrscheinlich sind die 38 mm ab der Unterkante der
Buchsenleiste (8,5 mm), dann ist die Platine -> Zellen 29,5 mm – das passt genau zu Waveshares «42,05 mm Gesamthöhe auf dem
Pi» (1,6 Pi + 2,5 Stiftleiste + 38).

Lage in x/y aus der Masszeichnung von Waveshare (Draufsicht, Bild des Besitzers vom 08.11.2026; ca. ±0,5 mm).
Masse mit «NACHMESSEN» sind geschätzt (die Zeichnung hat keine Höhen). Geprüft (Waveshare-Wiki / Produktseite 18306):
Platine 56 × 85 mm, Befestigungslöcher Ø 3,0, 2 × 18650 (Zellenlänge < 67 mm), Ladegerät 8,4 V / 2 A, Ausgang 5 V bis
2,5 A, Gesamthöhe 42,05 mm auf dem Pi.
Koordinaten wie v5.py (Unterteil: x 0..LX innen, x = 0 Stirnwand innen, y = 0 Lüftungswand innen, z = 0 Bodenunterseite).
Pi/HAT-lokal: a = ab der Pi-Seite OHNE USB (wie die Zeichnung von rechts), b = ab der Kante mit den HAT-Buchsen (HDMI-Seite).
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
# --- altes UPS HAT (geprüft: Waveshare-Wiki «UPS HAT», Produktseite SKU 18306, Masszeichnung)
HAT_L, HAT_W = 85.0, 56.0            # Platine – Waveshare
HAT_HOLE_D = 3.0                     # Befestigungslöcher – Waveshare
HAT_HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]   # Lochbild wie Pi (58 × 49; 23,5 / 3,5 / 3,5) – Masszeichnung
CELL_D, CELL_L = 18.4, 65.2          # 18650 (Waveshare: Länge < 67 mm, Zellen ohne Schutzplatine)
HAT_T = 1.6                          # NACHMESSEN: Platinendicke
HAT_MESS = 38.0                      # GEMESSEN (Besitzer 08.11.2026): Unterseite HAT -> Oberkante Zellen
HDR_H = 8.5                          # Buchsenleiste unten (Standard 8,5 mm)
HAT_TOP_H = HAT_MESS                 # Rechnung: schlimmster Fall = ab der Platine (robust)
HAT_TOP_H_WAHRSCH = HAT_MESS - HDR_H  # wahrscheinlich: die 38 mm ab Unterkante Buchsenleiste -> Platine bis Zellen 29,5
# --- Oberseite: Batteriehalter mit 2 × 18650 (Masszeichnung)
HOLDER_X0, HOLDER_X1 = 1.7, 84.4
HOLDER_Y0, HOLDER_Y1 = 7.6, 49.8
PINS_TOP = 10.0                      # NACHMESSEN: Stifte der Stapelleiste oben über der HAT-Platine (Foto: lange Stifte)
# --- Unterseite (zum Pi hin), an der Kante b = 0 (Masszeichnung: Lage a, Überstand; Höhen NACHMESSEN, höchstens wie die Leiste)
JACK_X, JACK_W, JACK_L, JACK_H = 47.3, 9.0, 14.0, 7.5     # 8,4-V-Hohlbuchse
JACK_AXIS = 4.0                      # NACHMESSEN: Achse unter der Platine
JACK_OUT = 2.8                       # Überstand über die Platinenkante – Masszeichnung
USBA_X, USBA_W, USBA_L, USBA_H = 31.5, 13.2, 14.0, 7.0    # USB-A (5 V OUT)
SW_X, SW_W, SW_L, SW_H = 16.2, 9.0, 4.5, 4.5              # Schiebeschalter ON/OFF
SW_OUT = 4.5                         # Schieber steht über die Kante vor – Masszeichnung
IND_X, IND_Y, IND_S, IND_H = 10.0, 18.0, 10.0, 6.0        # NACHMESSEN: hohe SMD-Spule
LED_X0, LED_X1, LED_Y = 69.5, 78.5, 4.8                   # WARNING-LEDs oben – Masszeichnung
# --- Stapel
HAT_GAP = 17.0                       # NACHMESSEN: Pi-Platine oben -> HAT-Platine unten mit GPIO-Verlängerung («Booster Header») und
                                     #   Abstandsbolzen M2,5 × 17 (Pimoroni für Pi 5 + Active Cooler). Bis 19 mm passt es noch.
COOL_H = v53.COOL_TOP - v5.PI_Z - 1.6    # Active Cooler über der Pi-Platine (Annahme v5.3: 14,4) – NACHMESSEN
PZ = ZF + 5.5                        # Unterseite Pi-Platine (z 8; v5.3: 39,5): Bolzen 5,5 mm über dem Boden
PX = 76.0                            # Pi-Platine x 76..161 (USB/Ethernet zur Stirnseite, ragen bis x 74 – Zaun innen 72,5)
PY = 9.0                             # Pi-Platine y 9..65, Buchsen-Kante bei y 65 (Halter ab y 15,2: frei vom Kabelkamm, y < 14)
ZH = PZ + 1.6 + HAT_GAP              # Unterseite HAT-Platine
TOP = ZH + HAT_TOP_H                 # Oberkante Zellen (schlimmster Fall)
TOP_WAHRSCH = ZH + HAT_TOP_H_WAHRSCH
# --- Laden von aussen: Einbaubuchse 5,5/2,1 in der Reserve-Öffnung (+x-Wand, Ø 12,3, statt Blindstopfen 17)
DCB_Y, DCB_Z = v52.RES_Y, v52.RES_ZC
DCB_L, DCB_D = 16.0, 12.0            # NACHMESSEN: Körper innen (Länge ab Wand innen, Ø inkl. Mutter)
PLUG90_L, PLUG90_D = 11.0, 10.0      # NACHMESSEN: Winkelstecker 5,5/2,1: Körper ab Buchsenfront, Ø
# --- Adapter 28 (flacher Rahmen wie Sockel 13, kurze Bolzen)
AD_T = 3.0                           # Stegbreite
AD_H = 2.5                           # Rahmenhöhe (z 2,5 .. 5,0)
AD_POST_D = 7.0
AD_PILOT_D = 2.2                     # M2,5: Aussengewinde der Abstandsbolzen schneidet sich ein (Loch durchgehend, 5,5 mm)

# ======================= ABGELEITET =====================================


def to_world(a, b):
    """Pi/HAT-lokal (a ab der Seite ohne USB, b ab der HDMI-/Buchsen-Kante) -> Gehäuse (Pi um 180° gedreht)"""
    return PX + HAT_L - a, PY + HAT_W - b


HOLES_W = [to_world(a, b) for a, b in HAT_HOLES]
EDGE_Y = PY + HAT_W                  # Buchsen-Kante (zeigt nach +y)


def wbox(a0, a1, b0, b1, z0, z1):
    x0, y0 = to_world(a1, b1); x1, y1 = to_world(a0, b0)
    return box(x0, x1, y0, y1, z0, z1)


# ======================= TEIL 28 ADAPTER ================================
def part_adapter():
    """28 Adapter altes UPS HAT: flacher Rahmen im Akku-Zaun (Klemmrippen wie Sockel 13), Stege unter den Lochreihen,
    4 Bolzen Ø 7 tragen den Pi 5 auf z = PZ. Druck: Rahmen unten, ohne Stützen."""
    x0, x1 = v5.BAT_X0 + 0.2, v5.BAT_X0 + v5.BAT_L - 0.2
    y0, y1 = 0.6, v5.BAT_W - 0.2
    zb, t, zt = ZF, AD_T, ZF + AD_H
    frame = D(box(x0, x1, y0, y1, zb, zt), box(x0 + t, x1 - t, y0 + t, y1 - t, zb - 1, zt + 1))
    xs = sorted(set(x for x, y in HOLES_W)); ys = sorted(set(y for x, y in HOLES_W))
    bars = [box(x0, x1, y - t / 2, y + t / 2, zb, zt) for y in ys] + [box(x - t / 2, x + t / 2, y0, y1, zb, zt) for x in xs]
    posts = [cyl_z(x, y, zb, PZ, AD_POST_D) for x, y in HOLES_W]
    clamps = []
    for xc, sgn in ((x0, -1), (x1, 1)):
        for yc in (20.0, 60.0):
            clamps.append(box(min(xc, xc + sgn * (0.7 + v52.SOCK_CLAMP)), max(xc, xc + sgn * (0.7 + v52.SOCK_CLAMP)), yc - 2.0, yc + 2.0, zb, zt))
    body = U(frame, *bars, *posts, *clamps)
    cut = [cyl_z(x, y, ZF - 1, PZ + 1, AD_PILOT_D) for x, y in HOLES_W]   # durchgehend (kein dünner Boden)
    return D(body, *cut)


# ======================= DUMMIES (nur Modell, nicht drucken) ============
def pi_dummy():
    """Pi 5 (gedreht): Platine, USB/Ethernet (an der Seite a = 66..87), GPIO-Stifte, Ports an der HDMI-Kante"""
    b = PZ + 1.6
    return U(box(PX, PX + 85, PY, PY + 56, PZ, b), wbox(66, 87, 1.5, 54.0, b, b + 16.0),
             wbox(7.1, 57.9, 50.0, 55.0, b, b + 8.5), wbox(5.0, 45.0, -0.5, 7.0, b, b + 3.5))


def cooler_dummy():
    return wbox(25, 56, 12, 44, PZ + 1.6, PZ + 1.6 + COOL_H)


def camconn_dummy():
    out = []
    for cx, cy in (v52.PI_CAM1_XY, v52.PI_CAM0_XY):
        a, b = cx - (v5.BAT_X0 + 1), cy - 3.0
        out.append(wbox(a - 1.25, a + 1.25, b - 6.5, b + 6.5, PZ + 1.6, PZ + 1.6 + 5.0))
    return U(*out)


def cam_world(which):
    cx, cy = v52.PI_CAM0_XY if which == 0 else v52.PI_CAM1_XY
    return to_world(cx - (v5.BAT_X0 + 1), cy - 3.0)


def hat_board():
    return D(box(PX, PX + HAT_L, PY, PY + HAT_W, ZH, ZH + HAT_T),
             *[cyl_z(x, y, ZH - 1, ZH + HAT_T + 1, HAT_HOLE_D) for x, y in HOLES_W])


def jack_world():
    x, _ = to_world(JACK_X, 0)
    return x, EDGE_Y + JACK_OUT, ZH - JACK_AXIS


def hat_under():
    """Unterseite: Hohlbuchse, USB-A, Schalter (mit Schieber), Spule, Buchsenleiste"""
    return U(wbox(JACK_X - JACK_W / 2, JACK_X + JACK_W / 2, -JACK_OUT, JACK_L - JACK_OUT, ZH - JACK_H, ZH),
             wbox(USBA_X - USBA_W / 2, USBA_X + USBA_W / 2, 0, USBA_L, ZH - USBA_H, ZH),
             wbox(SW_X - SW_W / 2, SW_X + SW_W / 2, 0, SW_L, ZH - SW_H, ZH),
             wbox(SW_X - 1.4, SW_X + 1.4, -SW_OUT, 0, ZH - SW_H + 1.0, ZH - 1.0),
             wbox(IND_X - IND_S / 2, IND_X + IND_S / 2, IND_Y - IND_S / 2, IND_Y + IND_S / 2, ZH - IND_H, ZH),
             wbox(7.1, 57.9, 50.0, 55.0, ZH - HDR_H, ZH))


def hat_top(top=None):
    """Oberseite: Halter mit 2 × 18650 bis TOP (Standard: schlimmster Fall), Stifte der Stapelleiste"""
    top = TOP if top is None else top
    zb = ZH + HAT_T
    zc = top - CELL_D / 2
    x0, y0 = to_world(HOLDER_X1, HOLDER_Y1); x1, y1 = to_world(HOLDER_X0, HOLDER_Y0)
    w = (y1 - y0) / 2
    base = box(x0, x1, y0, y1, zb, zc - 2.0)
    ends = [box(x0, x0 + 3.0, y0, y1, zb, zc + 3.0), box(x1 - 3.0, x1, y0, y1, zb, zc + 3.0)]
    cells = [cyl_x(y0 + w * (i + 0.5), zc, (x0 + x1) / 2 - CELL_L / 2, (x0 + x1) / 2 + CELL_L / 2, CELL_D) for i in range(2)]
    pins = wbox(7.1, 57.9, 50.0, 55.0, zb, zb + PINS_TOP)
    return U(base, *ends, *cells, pins)


def hat_leds():
    return wbox(LED_X0, LED_X1, LED_Y - 1.0, LED_Y + 1.0, ZH + HAT_T, ZH + HAT_T + 0.8)


def standoffs():
    return U(*[cyl_z(x, y, PZ + 1.6, ZH, 4.6, fn=6) for x, y in HOLES_W],
             wbox(7.1, 57.9, 50.0, 55.0, PZ + 1.6 + 8.5, ZH - HDR_H))


def plug90():
    """Winkelstecker in der 8,4-V-Buchse (Körper ab der Buchsenfront nach +y, Kabel nach unten)"""
    x, y, z = jack_world()
    return U(cyl_y(x, z, y, y + PLUG90_L, PLUG90_D), cyl_z(x, y + PLUG90_L - 3.0, z - 9.0, z, 4.0))


def dc_socket():
    """Einbaubuchse 5,5/2,1 in der Reserve-Öffnung (innen Körper + Mutter, aussen Kragen)"""
    return U(cyl_x(DCB_Y, DCB_Z, LX - DCB_L, LX, DCB_D), cyl_x(DCB_Y, DCB_Z, LX, LX + WALL + 2.0, 11.0))


def pigtail_pts():
    x, y, z = jack_world()
    return [(x, y + PLUG90_L - 3.0, z - 9.0), (x, 80.0, ZF + 6.0), (164.0, 80.0, ZF + 6.0), (164.0, DCB_Y, ZF + 30.0),
            (LX - DCB_L - 1.0, DCB_Y, DCB_Z)]


def placed(tilt=0.0, pan=180.0, top=None):
    """Gehäuse v5.3 unverändert (ohne UPS HAT (E), Zellen, Luftkanal 27, Blindstopfen 17) mit Adapter und Stapel"""
    P = v53.placed(tilt, pan)
    for k in ("ups", "duct", "sockel", "resplug", "resjack"):
        P.pop(k, None)
    P["adapter"] = part_adapter()
    P["pi"] = pi_dummy()
    P["cooler"] = cooler_dummy()
    P["camconn"] = camconn_dummy()
    P["standoff"] = standoffs()
    P["hat"] = hat_board()
    P["hatunder"] = hat_under()
    P["holder18650"] = hat_top(top)
    P["hatled"] = hat_leds()
    P["plug90"] = plug90()
    P["dcsocket"] = dc_socket()
    P["pigtail"] = v52.kabel(pigtail_pts(), 1.3)
    P["cam0"] = v52.kabel(cable_cam0_pts(top))
    P["cam1"] = v52.kabel(cable_cam1_pts())
    return P


# ======================= KABEL (Vorschlag) ==============================
def cable_cam0_pts(top=None):
    """CAM0 (Kopf): Kabelkamin -> über die Zellen nach +y -> neben dem HAT (Buchsen-Kante, links vom Winkelstecker) hinunter
    -> unter dem HAT flach zur Buchse CAM/DISP 0"""
    top = TOP if top is None else top
    cx, cy = cam_world(0)
    jx = jack_world()[0]
    zt = min((top + TOPZ) / 2, TOPZ - 1.6)
    xs = jx - JACK_W / 2 - 3.0
    return [(v5.CHIM_X, v5.AY, TOPZ + 1.0), (v5.CHIM_X, v5.AY + 2.0, zt), (v5.CHIM_X + 2.0, EDGE_Y - 4.0, zt),
            (xs, EDGE_Y + 9.0, TOPZ - 10.0), (xs, EDGE_Y + 9.0, PZ + 8.0), (cx, EDGE_Y + 2.0, PZ + 7.0), (cx, cy, PZ + 1.6 + 5.0)]


def cable_cam1_pts():
    """CAM1 (Weitwinkel vorne): wie v5.2 bis unter den Pan-Servo, dann über die Hub-Ablage nach +y -> hinter dem Winkelstecker
    hinunter -> unter Stecker und HAT flach zur Buchse CAM/DISP 1"""
    p = v52.cable_cam1_pts()
    cx, cy = cam_world(1)
    yb = EDGE_Y + JACK_OUT + PLUG90_L + 3.0
    return p[:3] + [(60.0, 66.0, 52.0), (cx - 6.0, yb, 48.0), (cx, yb, PZ + 6.0), (cx, EDGE_Y + 2.0, PZ + 6.5),
                    (cx, cy, PZ + 1.6 + 5.0)]


if __name__ == "__main__":
    print("Pi unten z %.2f, HAT unten z %.2f, Zellen oben z %.2f (schlimmster Fall) / %.2f (wahrscheinlich); Deckel unten %.1f"
          % (PZ, ZH, TOP, TOP_WAHRSCH, TOPZ))
    print("Luft Zellen -> Deckel: %.2f mm (schlimmster Fall) / %.2f mm (wahrscheinlich); Luft über dem Lüfter %.2f mm"
          % (TOPZ - TOP, TOPZ - TOP_WAHRSCH, ZH - PZ - 1.6 - COOL_H))
    print("Pi x %.1f..%.1f y %.1f..%.1f, Löcher %s" % (PX, PX + 85, PY, PY + 56, HOLES_W))
    print("8,4-V-Buchse", np.round(jack_world(), 2), " CAM0", cam_world(0), " CAM1", cam_world(1))
