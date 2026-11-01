"""Pan-Tilt-Kamera v3 (Aufbau ähnlich Waveshare-PTZ):
geschlossenes Unterteil (Raspberry Pi 5 + PCA9685), Deckel mit Kugel-Laufring (6-mm-BBs),
Drehteller auf dem Pan-Servo, seitlicher Arm mit Tilt-Servo, Kameragehäuse mit Blende.
Servos: 2x MG90S/SG90. Kameras: Pi Camera Module 3 + Waveshare Thermal-90 (WS-31941).
Alle Maße in mm. Parameter anpassen, dann:  python3 export.py
"""
import math
from csg import *

# ======================= PARAMETER ======================================
TOL = 0.3

# --- Unterteil
WALL, FLOOR, LID_T = 2.5, 2.5, 3.0
LX, LY, HIN = 117.0, 66.0, 42.0
R_OUT = 3.0
LID_SCREW_HOLE = 2.6                 # 2.6 = M3 selbstschneidend, 4.0 = Einschmelzmutter
TRIPOD = True
CABLE_GLAND_D = 7.0

# --- Raspberry Pi 5
PI_L, PI_W, PI_T = 85.0, 56.0, 1.6
PI_HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]
STANDOFF_H, STANDOFF_HOLE = 6.5, 2.2
PX, PY = 31.0, 1.75

# --- PCA9685 (Adafruit-Format)
PCA_L, PCA_W = 62.5, 25.4
PCA_HOLE_DL, PCA_HOLE_DW = 55.9, 19.0
PCA_X0 = 2.5
PCA_Y0 = (LY - PCA_L) / 2
PCA_STANDOFF = 4.0

# --- MG90S / SG90
SV_L, SV_W = 22.8, 12.4
SV_TAB_Z, SV_TAB_T = 15.9, 2.5
SV_BODY_H = 26.7
SV_SHAFT_OFF = 6.0
SV_HOLE_DL, SV_HOLE_D = 27.8, 2.4    # Laschen-Lochabstand, Durchgangsloch (Pan, im Deckel)
SV_PILOT = 1.6                       # Kernloch für Servoschraube (Tilt, im Arm)
HORN_TOP = 13.5                      # Laschen-Oberseite -> Außenfläche aufgestecktes Horn (!)
HORN_ARM_L, HORN_ARM_W, HORN_HUB_D = 35.0, 6.4, 7.8
HORN_POCKET = 2.2                    # Hornstärke + Luft (Pan-Horn im Drehteller)
HORN_RECESS = 1.5                    # Einlass Tilt-Horn im Kameragehäuse

# --- Kugellager (Pan)
BB_D = 6.0                           # Softair-Kugeln 6 mm
BB_RING_R = 28.0                     # Laufkreis-Radius
GROOVE_R = 3.15                      # Rillenradius
GROOVE_OFF = 0.8                     # Rillenmitte über Laufring-Oberfläche
BB_PLAY = 0.2                        # axiales Spiel
RING_RI, RING_RO = 23.0, 33.0        # Laufring innen/außen
TT_R, TT_T = 34.0, 6.0               # Drehteller Radius/Dicke

# --- Gabel + Kamerakopf (Pan-Koordinaten: Ursprung Pan-Achse, z=0 Oberseite Drehteller, Blick +x)
AXZ = 40.0                           # Kippachse über Drehteller
BASE_T = 4.0                         # Gabelboden
ARM_T, ARM_W = 5.0, 24.0             # Armdicke / -breite
GAP = 1.5                            # Luft Kopf-Seitenwand <-> Arm
ARM_HORN_RECESS = 1.5                # Tilt-Horn in Arm 1 eingelassen
HW, HH = 58.0, 58.0                  # Kamerakopf Breite (y) / Höhe (z)
HX0, HX1 = -10.0, 19.5               # Kopf hinten / vorne (Kipp-Koordinaten)
SHELL_T, FRONT_T, BACK_T = 2.5, 2.5, 2.5
H_R = 7.0
VIS_L = 12.0                         # Blende

# Pi Camera Module 3 (25 x 24 mm)
CAM3_LENS_Y, CAM3_LENS_Z = -13.5, 13.5
CAM3_LENS_FROM_TOP = 9.5
CAM3_WIN_D = 12.5                    # rundes Fenster, Linsenblock 8,5 x 8,5 passt durch
CAM3_STAND = 2.0

# Waveshare Thermal-90 (45 x 22 mm) – Maße aus Produktfoto (Bauteile vorne)
THERM_W, THERM_H, THERM_T = 45.0, 22.0, 1.6
THERM_LENS = (7.4, 10.5)             # Linsenmitte ab linker / oberer Platinenkante
THERM_MOD = (8.45, 10.7, 13.4)       # Linsenblock Mitte (links, oben) + Kantenlänge
THERM_HOLES = [(1.75, 1.75), (1.75, 20.25)]  # nur links, M2
THERM_STAND = 5.0                    # Abstand Platine <-> Frontwand (Stecker 4,5 mm hoch)
THERM_TOP_Z = -2.0                   # Oberkante Platine
THERM_LEFT_Y = -26.0                 # linke Kante (von vorne gesehen)

# ======================= ABGELEITET =====================================
TOPZ = FLOOR + HIN                   # Deckel-Unterseite
LIDTOP = TOPZ + LID_T
PCB_Z = FLOOR + STANDOFF_H
PCB_TOP = PCB_Z + PI_T
TAB_TOP_TO_BOTTOM = SV_TAB_Z + SV_TAB_T
SV_ABOVE_TAB = SV_BODY_H - TAB_TOP_TO_BOTTOM       # Körper oberhalb Laschen (8,3)
SVX, SVY = 33.0, LY / 2                              # Pan-Achse
HORN_Z = TOPZ + HORN_TOP
BB_CONTACT = 2 * (GROOVE_OFF - (GROOVE_R - BB_D / 2))  # Abstand Ringe bei Kugelkontakt
TT_BOT = HORN_Z - HORN_POCKET
RING_TOP = TT_BOT - BB_CONTACT - BB_PLAY
RACE_H = RING_TOP - LIDTOP
PAN_Z0 = TT_BOT + TT_T               # Pan-Koordinaten z=0 (absolut)
CORNERS = [(3, 3), (LX - 3, 3), (3, LY - 3), (LX - 3, LY - 3)]
PCA_HOLES = [(PCA_X0 + (PCA_W - PCA_HOLE_DW) / 2 + dx, PCA_Y0 + (PCA_L - PCA_HOLE_DL) / 2 + dy)
             for dx in (0, PCA_HOLE_DW) for dy in (0, PCA_HOLE_DL)]
# Gabel / Tilt-Servo
A1 = HW / 2 + GAP                                   # Innenseite Arm 1 (Servo-Seite, +y)
TAB_TOP = A1 + ARM_HORN_RECESS - HORN_TOP           # Laschen-Oberseite (Kopf-y)
TAB_Y0 = TAB_TOP - SV_TAB_T
SV_TOP_END, SV_BOT_END = SV_SHAFT_OFF, -(SV_L - SV_SHAFT_OFF)   # Körper-z im Kopf (Welle oben)
TBC = -(SV_L / 2 - SV_SHAFT_OFF)                    # Körpermitte z


def horn_recess_z(x, y, z0, z1, along="y"):
    arm = RBox(HORN_ARM_W, HORN_ARM_L, z1 - z0, HORN_ARM_W / 2 - 0.01) if along == "y" else \
        RBox(HORN_ARM_L, HORN_ARM_W, z1 - z0, HORN_ARM_W / 2 - 0.01)
    return U(cyl_z(x, y, z0, z1, HORN_HUB_D), T([x, y, z0], arm))


# ======================= UNTERTEIL ======================================
def part_tub():
    outer = T([LX / 2, LY / 2, 0], RBox(LX + 2 * WALL, LY + 2 * WALL, TOPZ, R_OUT))
    cavity = box(0, LX, 0, LY, FLOOR, TOPZ + 1)
    add = []
    for hx, hy_ in PI_HOLES:
        add.append(cyl_z(PX + hx, PY + hy_, FLOOR - 0.5, PCB_Z, 6.5))
    for x, y in PCA_HOLES:
        add.append(cyl_z(x, y, FLOOR - 0.5, FLOOR + PCA_STANDOFF, 5.5))
    for cx, cy in CORNERS:
        add.append(cyl_z(cx, cy, TOPZ - 10, TOPZ, 8))
        add.append(T([cx, cy, TOPZ - 14], Cyl(4.01, r1=0.01, r2=4.0)))
    tpx, tpy = PX + 32.5, PY + 28.0
    if TRIPOD:
        add.append(cyl_z(tpx, tpy, FLOOR - 0.5, FLOOR + 5.8, 18))
    body = U(D(outer, cavity), *add)
    cut = []
    for hx, hy_ in PI_HOLES:
        cut.append(cyl_z(PX + hx, PY + hy_, 1.0, PCB_Z + 1, STANDOFF_HOLE))
    for x, y in PCA_HOLES:
        cut.append(cyl_z(x, y, 1.0, FLOOR + PCA_STANDOFF + 1, 2.2))
    for cx, cy in CORNERS:
        cut.append(cyl_z(cx, cy, TOPZ - 9, TOPZ + 1, LID_SCREW_HOLE))
    zc = PCB_TOP + 1.6
    cut.append(box(PX + 11.2 - 6.5, PX + 11.2 + 6.5, -WALL - 1, 1, zc - 4, zc + 4))
    cut.append(box(PX + 25.8 - 6.5, PX + 39.2 + 6.5, -WALL - 1, 1, zc - 4, zc + 4))
    cut.append(box(LX - 1, LX + WALL + 1, PY + 2, PY + 54, PCB_TOP - 0.5, PCB_TOP + 17))
    for i in range(10):
        x = 46 + i * 6
        cut.append(box(x, x + 2.5, LY - 1, LY + WALL + 1, 14, 32))
    for i in range(5):
        x = 86 + i * 5.5
        cut.append(box(x, x + 2.5, -WALL - 1, 1, 17, 30))
    if CABLE_GLAND_D > 0:
        cut.append(cyl_x(LY / 2, 28, -WALL - 1, 1, CABLE_GLAND_D))
    if TRIPOD:
        cut.append(cyl_z(tpx, tpy, -1, FLOOR + 7, 6.8))
        cut.append(cyl_z(tpx, tpy, FLOOR + 0.2, FLOOR + 7, 11.3 / math.cos(math.pi / 6), fn=6))
    return D(body, *cut)


def part_lid():
    plate = T([LX / 2, LY / 2, TOPZ], RBox(LX + 2 * WALL, LY + 2 * WALL, LID_T, R_OUT))
    ring = D(cyl_z(SVX, SVY, LIDTOP - 0.1, RING_TOP, 2 * RING_RO),
             cyl_z(SVX, SVY, LIDTOP - 1, RING_TOP + 1, 2 * RING_RI))
    body = U(plate, ring)
    cut = [T([SVX, SVY, RING_TOP + GROOVE_OFF], Torus(BB_RING_R, GROOVE_R))]
    for cx, cy in CORNERS:
        cut.append(cyl_z(cx, cy, TOPZ - 3, LIDTOP + 1, 3.4))
        cut.append(cyl_z(cx, cy, LIDTOP - 1.8, LIDTOP + 1, 6.5))
    # Pan-Servo: Körper entlang x, Welle bei SVX, Körper nach -x
    cut.append(box(SVX - (SV_L - SV_SHAFT_OFF) - 0.4, SVX + SV_SHAFT_OFF + 0.4,
                   SVY - SV_W / 2 - 0.4, SVY + SV_W / 2 + 0.4, TOPZ - 3, LIDTOP + 1))
    bc = SVX - (SV_L / 2 - SV_SHAFT_OFF)
    for dx in (-SV_HOLE_DL / 2, SV_HOLE_DL / 2):
        cut.append(cyl_z(bc + dx, SVY, TOPZ - 3, LIDTOP + 1, SV_HOLE_D))
        cut.append(cyl_z(bc + dx, SVY, LIDTOP - 1.2, LIDTOP + 1, 4.6))
    cut.append(T([75, LY / 2, TOPZ - 3], RBox(10, 26, LID_T + 4, 3)))          # Kabeldurchlass
    for i in range(5):
        x = 87 + i * 5.5
        cut.append(T([x + 1.25, LY / 2, TOPZ - 3], RBox(2.5, 40, LID_T + 4, 1.2)))
    return D(body, *cut)


# ======================= DREHTELLER (Pan-Koordinaten) ===================
TT_SCREWS = [(-8.0, -19.0), (8.0, -19.0), (-8.0, 19.0), (8.0, 19.0)]   # 01.11.2026 (Druck-Check): vorher ±11/±20,5 = 0,4 mm zur Kugelrille; M3 × 8


def part_turntable():
    disc = cyl_z(0, 0, -TT_T, 0, 2 * TT_R)
    cut = [T([0, 0, -TT_T - GROOVE_OFF], Torus(BB_RING_R, GROOVE_R)),
           horn_recess_z(0, 0, -TT_T - 0.1, -TT_T + HORN_POCKET, along="y"),
           cyl_z(0, 0, -TT_T - 1, 1, 5.5)]
    for y in (-14.0, -10.0, 10.0, 14.0):                      # Hornschrauben (von unten)
        cut.append(cyl_z(0, y, -TT_T - 1, -1.0, 1.5))
    for x, y in TT_SCREWS:
        cut.append(cyl_z(x, y, -TT_T - 1, 1, 2.6))
    for a in (0, 45, 135, 180, 225, 315):                     # Gewichtsersparnis
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        cut.append(cyl_z(17 * c, 17 * s, -TT_T + 1.2, 1, 7))
    return D(disc, *cut)


# ======================= GABEL (Pan-Koordinaten) ========================
ARM2_FOOT_D = 9.0
ARM2_SCREWS = [(-7.0, -(A1 + ARM_T + ARM2_FOOT_D / 2)), (7.0, -(A1 + ARM_T + ARM2_FOOT_D / 2))]
BASE_Y0, BASE_Y1 = -(A1 + ARM_T + ARM2_FOOT_D), A1 + ARM_T


def _arm_plate(y0, y1, z0):
    return U(box(-ARM_W / 2, ARM_W / 2, y0, y1, z0, AXZ), cyl_y(0, AXZ, y0, y1, ARM_W))


def part_yoke():
    """Gabelboden + Arm 1 (Servo-Seite, +y) in einem Teil."""
    base = T([0, (BASE_Y0 + BASE_Y1) / 2, 0], RBox(2 * 15.0, BASE_Y1 - BASE_Y0, BASE_T, 5))
    arm1 = _arm_plate(A1, A1 + ARM_T, 0)
    ribs = [rib_yz(x0, 3.0, A1 + ARM_T, +1, 0.0, 8.0, BASE_T + 16.0) for x0 in (ARM_W / 2 - 3, -ARM_W / 2)]  # bis aufs Druckbett
    body = U(base, arm1, *ribs)
    cut = [cyl_z(0, 0, -1, BASE_T + 1, 8.0)]                                   # Zugang Pan-Mittelschraube
    for x, y in TT_SCREWS:
        cut.append(cyl_z(x, y, -1, BASE_T + 1, 3.4))
        cut.append(cyl_z(x, y, BASE_T - 2.0, BASE_T + 1, 6.4))
    for x, y in ARM2_SCREWS:
        cut.append(cyl_z(x, y, 0.8, BASE_T + 1, 2.6))
    cut.append(box(-ARM_W / 2 - 0.2, ARM_W / 2 + 0.2, -A1 - ARM_T - 0.2, -A1 + 0.2, BASE_T - 1.5, BASE_T + 1))  # Nut Arm 2
    # Tilt-Horn: Einlass in Innenseite Arm 1, Arme senkrecht
    cut.append(T([0, A1 - 0.1, AXZ], R([-90, 0, 0], horn_recess_z(0, 0, 0, ARM_HORN_RECESS + 0.1, along="x"))))
    cut.append(cyl_y(0, AXZ, A1 - 1, A1 + ARM_T + 1, 5.5))
    for dz in (-14.0, -10.0, 10.0, 14.0):
        cut.append(cyl_y(0, AXZ + dz, A1, A1 + ARM_T - 0.8, 1.5))
    return D(body, *cut)


def part_arm2():
    """Arm 2 (Lager-Seite, -y), wird auf den Gabelboden geschraubt."""
    y0, y1 = -A1 - ARM_T, -A1
    plate = _arm_plate(y0, y1, BASE_T - 1.4)
    foot = box(-ARM_W / 2, ARM_W / 2, y0 - ARM2_FOOT_D, y0, BASE_T, BASE_T + 5)
    ribs = [rib_yz(x0, 3.0, y0, -1, BASE_T + 5, ARM2_FOOT_D - 1, 14.0) for x0 in (ARM_W / 2 - 3, -ARM_W / 2)]
    body = U(plate, foot, *ribs)
    cut = [cyl_y(0, AXZ, y0 - 1, y1 + 1, 3.4),
           T([0, y1 + 0.1, AXZ], R([90, 0, 0], Cyl(2.6, d=5.7 / math.cos(math.pi / 6) + 0.3, fn=6)))]   # Mutter M3
    for x, y in ARM2_SCREWS:
        cut.append(cyl_z(x, y, BASE_T - 1, BASE_T + 6, 3.4))
        cut.append(cyl_z(x, y, BASE_T + 5 - 2.0, BASE_T + 30, 6.4))
    return D(body, *cut)


# ======================= KAMERAKOPF (Kipp-Koordinaten) =================
FB = HX1 - FRONT_T                                     # Innenseite Frontwand


def _profile(x0, x1, inset=0.0):
    return rx_box(x0, x1, HW - 2 * inset, HH - 2 * inset, max(H_R - inset, 0.5))


BOSS_YZ = [(sy * (HW / 2 - 6.5), sz * (HH / 2 - 6.5)) for sy in (-1, 1) for sz in (-1, 1)]


def therm_pos(u, v):
    """Platinen-Koordinate (ab linker / oberer Kante, von vorne gesehen) -> Kopf (y, z)."""
    return THERM_LEFT_Y + u, THERM_TOP_Z - v


def cam3_holes():
    top = CAM3_LENS_Z + CAM3_LENS_FROM_TOP
    return [(CAM3_LENS_Y + dy, top - dz) for dy in (-10.5, 10.5) for dz in (2.0, 14.5)]


# Kopf v4.1: zur -y-Seite offen (Seitendeckel), damit nichts in der Luft beginnt.
OPEN_Y = -HW / 2 + SHELL_T                             # Öffnungsebene (= Innenseite des Seitendeckels)
# Schraubsäulen für den Seitendeckel (x, z, volle Länge?)
SIDE_SCREWS = [(-4.0, HH / 2 - 5.5, True), (10.5, HH / 2 - 5.5, True), (-4.0, -(HH / 2 - 5.5), False)]
SIDE_COL_D = 6.0


def _visor():
    th = math.atan(20.0 / VIS_L)
    below = T([HX1, 0, HH / 2 - 22], R([0, -math.degrees(th), 0], box(-300, 300, -300, 300, -600, 0)))
    return D(_profile(HX1 - 0.5, HX1 + VIS_L), _profile(HX1 - 1, HX1 + VIS_L + 1, SHELL_T), below)


def _side_columns():
    cols = []
    for x, z, full in SIDE_SCREWS:
        if full:
            cols.append(cyl_y(x, z, OPEN_Y, HW / 2 - SHELL_T + 0.5, SIDE_COL_D))
        else:
            # kurze Säule an der Bodenwand, Anfang mit 45°-Fase (druckbar ohne Stütze)
            c = cyl_y(x, z, OPEN_Y, 14.0, SIDE_COL_D)
            wall = -HH / 2 + SHELL_T
            fill = box(x - SIDE_COL_D / 2, x + SIDE_COL_D / 2, OPEN_Y, 14.0, wall - 0.5, z)
            cham = T([0, 14.0, wall], R([45, 0, 0], box(-300, 300, -300, 0, -300, 300)))   # y + (z-wall) <= 14
            cols.append(I(U(c, fill), cham))
    return cols


def part_head():
    keep = box(HX0 - 1, HX1 + VIS_L + 1, OPEN_Y, HW / 2 + 1, -HH, HH)
    cav = rx_box(HX0 + SHELL_T, FB, HW, HH - 2 * SHELL_T, H_R - SHELL_T, y=-SHELL_T)   # nach -y offen
    shell = D(_profile(HX0, HX1), cav)
    add = [_visor()]
    add += _side_columns()
    add += [cyl_x(y, z, FB - CAM3_STAND, FB + 0.5, 4.5) for y, z in cam3_holes()]
    ts = FB - THERM_STAND
    add += [cyl_x(*therm_pos(u, v), ts, FB + 0.5, 4.0) for u, v in THERM_HOLES]
    add += [cyl_x(*therm_pos(38.5, v), ts, FB + 0.5, 3.0) for v in (-0.6, THERM_H + 0.6)]
    # Servohalter: massive Blöcke zwischen Laschen und +y-Wand, mit Führungsrahmen für die Laschen
    yb1 = HW / 2 - SHELL_T + 0.2
    zt0, zt1 = SV_TOP_END + 0.3, SV_TOP_END + 4.85 + 2.3
    zb0, zb1 = SV_BOT_END - 4.85 - 2.3, SV_BOT_END - 0.3
    for z0, z1 in ((zt0, zt1), (zb0, zb1)):
        add.append(box(-SV_W / 2 - 2, SV_W / 2 + 2.3, TAB_TOP, yb1, z0, z1))
    rim_y0 = TAB_TOP - 1.5
    for s in (-1, 1):                                   # seitliche Führungen an beiden Laschen
        for z0, z1 in ((SV_TOP_END - 0.5, zt1), (zb0, SV_BOT_END + 0.5)):
            x0, x1 = sorted([s * (SV_W / 2 + 0.3), s * (SV_W / 2 + 1.5)])
            add.append(box(x0, x1, rim_y0, TAB_TOP + 0.1, z0, z1))
    add.append(box(-SV_W / 2 - 1.5, SV_W / 2 + 1.5, rim_y0, TAB_TOP + 0.1, SV_TOP_END + 4.85 + 0.3, zt1))   # Stirnanschlag oben
    add.append(box(-SV_W / 2 - 1.5, SV_W / 2 + 1.5, rim_y0, TAB_TOP + 0.1, zb0, SV_BOT_END - 4.85 - 0.3))   # Stirnanschlag unten
    body = I(U(shell, *add), keep)

    cut = [cyl_x(CAM3_LENS_Y, CAM3_LENS_Z, FB - 1, HX1 + 1, CAM3_WIN_D)]
    my, mz = therm_pos(THERM_MOD[0], THERM_MOD[1])
    m = THERM_MOD[2] + 1.0
    cut.append(T([FB - 1, my, mz], R([0, 90, 0], RBox(m, m, FRONT_T + 2, 1.2))))
    cut += [cyl_x(y, z, FB - CAM3_STAND - 1, HX1 - 1.0, 1.8) for y, z in cam3_holes()]
    cut += [cyl_x(*therm_pos(u, v), ts - 1, HX1 - 1.0, 1.7) for u, v in THERM_HOLES]
    for x, z, full in SIDE_SCREWS:
        cut.append(cyl_y(x, z, OPEN_Y - 1, OPEN_Y + 10, 2.6))
    cut.append(cyl_y(0, 0, HW / 2 - SHELL_T - 1, HW / 2 + 1, 13.0))           # Servowelle
    # Rückwand: Kabelschlitz unten + Lüftung
    cut.append(T([HX0 - 1, -3, -HH / 2 + 8.5], R([0, 90, 0], RBox(6, 24, SHELL_T + 2, 2.9))))
    for i in range(4):
        cut.append(T([HX0 - 1, -12, 4 + i * 5], R([0, 90, 0], RBox(2.2, 20, SHELL_T + 2, 1.05))))
    return D(body, *cut)


def part_sidecover():
    """Seitendeckel (-y) mit Lagerdom für die Kippachse und Stempel, der den Servo hält."""
    slab = box(HX0 - 1, HX1 + VIS_L + 1, -HW / 2, OPEN_Y, -HH, HH)
    plate = I(U(_profile(HX0, HX1), _visor()), slab)
    lip_outer = rx_box(HX0 + SHELL_T + TOL, FB - TOL, HW, HH - 2 * SHELL_T - 2 * TOL, H_R - SHELL_T - TOL)
    lip_inner = rx_box(HX0 + SHELL_T + TOL + 1.6, FB - TOL - 1.6, HW + 2, HH - 2 * SHELL_T - 2 * TOL - 3.2, max(H_R - SHELL_T - TOL - 1.6, 0.5))
    lip = I(D(lip_outer, lip_inner), box(-100, 100, OPEN_Y - 0.1, OPEN_Y + 2.5, -100, 100))
    lip = D(lip, *[cyl_y(x, z, OPEN_Y - 1, OPEN_Y + 3, SIDE_COL_D + 4) for x, z, _ in SIDE_SCREWS])
    lip = D(lip, box(FB - 8, FB, OPEN_Y - 1, OPEN_Y + 3, -HH, HH))           # Platz für Kamera-Dome vorne
    boss = cyl_y(0, 0, OPEN_Y - 0.1, OPEN_Y + 5.0, 10)
    post = cyl_y(0, TBC, OPEN_Y - 0.1, TAB_TOP - TAB_TOP_TO_BOTTOM - 0.3, 7)
    body = U(plate, lip, boss, post)
    cut = [cyl_y(0, 0, -HW / 2 - 1, OPEN_Y + 6, 3.3)]
    for x, z, _ in SIDE_SCREWS:
        cut.append(cyl_y(x, z, -HW / 2 - 1, OPEN_Y + 1, 3.4))
        cut.append(cyl_y(x, z, -HW / 2 - 1, -HW / 2 + 1.4, 6.2))
    return D(body, *cut)


# ======================= DUMMIES ========================================
def dummies_abs():
    pi = U(box(PX, PX + PI_L, PY, PY + PI_W, PCB_Z, PCB_TOP),
           box(PX + 66, PX + 87, PY + 2, PY + 54, PCB_TOP, PCB_TOP + 16),
           box(PX + 25, PX + 55, PY + 15, PY + 45, PCB_TOP, PCB_TOP + 14))
    pz = FLOOR + PCA_STANDOFF
    pca = U(box(PCA_X0, PCA_X0 + PCA_W, PCA_Y0, PCA_Y0 + PCA_L, pz, pz + 1.6),
            box(PCA_X0 + PCA_W - 8, PCA_X0 + PCA_W - 0.5, PCA_Y0 + 10, PCA_Y0 + 52, pz + 1.6, pz + 1.6 + 12),
            box(PCA_X0 + 2, PCA_X0 + 10, PCA_Y0 + 26, PCA_Y0 + 36, pz + 1.6, pz + 1.6 + 10))
    sb = TOPZ - TAB_TOP_TO_BOTTOM
    bc = SVX - (SV_L / 2 - SV_SHAFT_OFF)
    pan_servo = U(box(SVX - (SV_L - SV_SHAFT_OFF), SVX + SV_SHAFT_OFF, SVY - SV_W / 2, SVY + SV_W / 2, sb, sb + SV_BODY_H),
                  box(bc - 16.25, bc + 16.25, SVY - SV_W / 2, SVY + SV_W / 2, TOPZ - SV_TAB_T, TOPZ),
                  cyl_z(SVX, SVY, sb + SV_BODY_H, HORN_Z - 2.0, 4.6))
    balls = T([SVX, SVY, RING_TOP + GROOVE_OFF - (GROOVE_R - BB_D / 2)], Torus(BB_RING_R, BB_D / 2))
    return pi, pan_servo, pca, balls


def dummy_tilt_servo():  # Kipp-Koordinaten, Welle entlang +y, Körper nach unten
    return U(box(-SV_W / 2, SV_W / 2, TAB_TOP - TAB_TOP_TO_BOTTOM, TAB_TOP + SV_ABOVE_TAB - 0.4, SV_BOT_END, SV_TOP_END),
             box(-SV_W / 2, SV_W / 2, TAB_Y0, TAB_TOP, TBC - 16.25, TBC + 16.25),
             cyl_y(0, 0, TAB_TOP, A1 + ARM_HORN_RECESS - 2.0, 4.6))


def dummy_pan_horn():
    return T([0, 0, -TT_T], RBox(5.8, 32, 2.0, 2.8))


def dummy_tilt_horn():  # Pan-Koordinaten, sitzt fest in Arm 1
    return T([0, A1 + ARM_HORN_RECESS, AXZ], R([90, 0, 0], RBox(32, 5.8, 2.0, 2.8)))


def dummies_head():
    top = CAM3_LENS_Z + CAM3_LENS_FROM_TOP
    cam3 = U(box(FB - CAM3_STAND - 1.0, FB - CAM3_STAND, CAM3_LENS_Y - 12.5, CAM3_LENS_Y + 12.5, top - 24, top),
             cyl_x(CAM3_LENS_Y, CAM3_LENS_Z, FB - CAM3_STAND, FB + 1.0, 8.5))
    ts = FB - THERM_STAND
    y0, z0 = therm_pos(0, 0)
    my, mz = therm_pos(THERM_MOD[0], THERM_MOD[1])
    ly, lz = therm_pos(*THERM_LENS)
    th = U(box(ts - THERM_T, ts, y0, y0 + THERM_W, z0 - THERM_H, z0),
           box(ts, ts + 6.5, my - THERM_MOD[2] / 2, my + THERM_MOD[2] / 2, mz - THERM_MOD[2] / 2, mz + THERM_MOD[2] / 2),
           cyl_x(ly, lz, ts + 6.5, ts + 7.0, 5),
           box(ts, ts + 4.5, y0 + 40.5, y0 + THERM_W, z0 - 20.5, z0 - 1.5))   # MX1.25-Stecker
    return cam3, th


def placed(tilt=0.0, pan=0.0):
    def pan_frame(n):
        return T([SVX, SVY, PAN_Z0], R([0, 0, pan], n))

    def tilt_frame(n):
        return pan_frame(T([0, 0, AXZ], R([0, tilt, 0], n)))
    pi, ps, pca, balls = dummies_abs()
    cam3, th = dummies_head()
    return {
        "tub": part_tub(), "lid": part_lid(), "balls": balls,
        "turntable": pan_frame(part_turntable()), "yoke": pan_frame(part_yoke()), "arm2": pan_frame(part_arm2()),
        "head": tilt_frame(part_head()), "side": tilt_frame(part_sidecover()),
        "pi": pi, "pca": pca, "servo1": ps, "servo2": tilt_frame(dummy_tilt_servo()),
        "horn1": pan_frame(dummy_pan_horn()), "horn2": pan_frame(dummy_tilt_horn()),
        "cam3": tilt_frame(cam3), "therm": tilt_frame(th),
    }


if __name__ == "__main__":
    print("Laufring-Höhe:", round(RACE_H, 2), " Pan z0:", round(PAN_Z0, 2), " Kippachse abs z:", round(PAN_Z0 + AXZ, 1))
    print("Arm1 innen y:", A1, " Laschen-Oberseite y:", TAB_TOP, " Servo y:", round(TAB_TOP - 18.4, 1), "..", round(TAB_TOP + SV_ABOVE_TAB, 1))
    print("Thermal-Linse (y,z):", therm_pos(*THERM_LENS), " Cam3-Linse:", (CAM3_LENS_Y, CAM3_LENS_Z))
    print("Gesamthöhe:", round(PAN_Z0 + AXZ + HH / 2, 1))
