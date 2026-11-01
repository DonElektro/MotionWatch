"""MotionWatch Gehäuse v5.1 (druckbar) – aus Konzept v5f.
Unterteil 183 x 97 mm mit UPS HAT (E) + 4 x 21700, Pi 5, PCA9685, Lautsprecher nach unten, PIR + Mikrofon vorne (-x),
GX12-Ladebuchse hinten (+x), HDMI-Notfallöffnung, Lüftung -y. Kopf, Seitendeckel, Drehteller aus v4.1 (pantilt.py).
Koordinaten Unterteil: x 0..LX innen, y 0..LY innen, z = 0 Unterseite Boden. Kopf schaut in Grundstellung nach -x.
Alle Masse in mm.  Ändern -> python3 export5.py
"""
import math
import numpy as np
from csg import *
import csg
import pantilt as pt

pt.VIS_L = 18.0                          # v5.1: längere Blende (Tau/Regen), Sichtfelder geprüft

# ======================= PARAMETER ======================================
TOL = 0.3
LX, LY, HIN = 178.0, 92.0, 66.0          # Innenmasse
WALL, FLOOR, LID_T, R_OUT = 2.5, 2.5, 3.0, 4.0
LID_SCREW_HOLE = 2.6                     # M3 selbstschneidend
AX, AY = 40.0, 46.0                      # Pan-Achse

# Akkublock UPS HAT (E) + 4 x 21700 (GESCHÄTZT – bitte nachmessen!)
BAT_X0 = 73.0
BAT_L, BAT_W, BAT_H = 90.0, 80.0, 26.0   # Länge (x), Breite (y), Höhe
FENCE_H, FENCE_T = 8.0, 1.6
PI_Z_ABOVE_FLOOR = 37.0                  # Unterseite Pi-Platine über Innenboden (geschätzt)

SPK_X, SPK_D = 30.0, 41.0                # Visaton SC 4.7 ND: Ø41, 27 tief
TRIPOD_XY = (62.0, 36.0)                 # 1/4"-Stativmutter

# PCA9685 (Adafruit-Format), stehend an der -y-Wand
PCA_X0, PCA_ZB = 4.0, 22.0               # linke Kante, Unterkante über Innenboden
PCA_L, PCA_W, PCA_DL, PCA_DW = 62.5, 25.4, 55.9, 19.0
PCA_STAND = 3.5

PIR_Y, PIR_ZB, PIR_D = 46.0, 33.0, 12.4  # Micro-PIR AS312 (Bastelgarage 420448): Linse Ø 12,2
MIC_Y, MIC_ZB = 76.0, 59.0               # Mikrofon vorne oben
GX12_Y, GX12_D = 73.0, 16.2              # v5.1: Ladebuchse GX16-4P (Bastelgarage 420241), Loch 16 mm
LED_Y, LED_D = 56.0, 3.3                 # Lichtleiter Lade-LED
HDMI_X, HDMI_W, HDMI_H = 105.0, 30.0, 16.0   # Notfallfenster HDMI (Pi 5 HDMI 0 / 1 liegen darin)
LOUV_X0, LOUV_X1, LOUV_N = 129.0, 173.0, 7

SHELF_X0, SHELF_Y0 = 124.0, 60.0         # Zwischenboden (separates Teil)
SHELF_T = 2.5

# v5.1
HUB_X0, HUB_X1, HUB_Y0 = 13.0, 71.0, 68.0   # Ablage USB-Hub (vorne rechts, über dem Lautsprecher-Niveau)
HUB_TRAY_Z = 26.0                        # Oberseite Ablage über Innenboden
TEMP_XY, TEMP_D = (22.0, 12.0), 6.5      # Durchführung Temperaturfühler DS18B20 (Ø6) im Boden
RELAY_Y, RELAY_ZC, RELAY_D = 30.0, 16.0, 12.3   # 2. Buchse hinten: GX12 3-polig für Relais (Warnlampe/Sirene)
LAMP_MOD_D, LAMP_MOD_L = 18.8, 14.0      # Scheinwerfer-Modul (gemessen)

# ======================= ABGELEITET =====================================
ZF = FLOOR
TOPZ = ZF + HIN
LIDTOP = TOPZ + LID_T
RING_TOP = LIDTOP + pt.RACE_H
PAN_Z0 = TOPZ + (pt.PAN_Z0 - pt.TOPZ)
PI_Z = ZF + PI_Z_ABOVE_FLOOR
SHELF_Z = ZF + BAT_H + 3.0 + SHELF_T     # Oberseite Zwischenboden
GX12_Z = SHELF_Z + 10.0
LED_Z = SHELF_Z + 28.0
LID_SCREWS = [(3.0, 3.0), (LX - 3.0, 3.0), (3.0, LY - 3.0), (LX - 3.0, LY - 3.0), (70.0, 3.0), (89.0, LY - 3.0)]
LAMP_Z = pt.AXZ - 16.0                   # Lampenachse (Pan-Koordinaten)
LAMP_Y = pt.A1 + pt.ARM_T + 16.0
ARM_OUT = pt.A1 + pt.ARM_T               # Aussenfläche Arm
LAMP_HOLE_X = -5.5                       # 01.11.2026 (Druck-Check): hinter dem Becher (vorher x 2 = unter dem Becher, kein Werkzeug)
LAMP_HOLES = [(LAMP_HOLE_X, LAMP_Z - 10.75), (LAMP_HOLE_X, LAMP_Z + 10.75)]   # (x, z) M3 × 8 + Scheibe durch Lampenlasche in den Arm
LAMP_TAB_X0 = -8.7                       # Lasche nach hinten verlängert (trägt die Löcher; ab -9 stehen die Rippen am Armfuss)
LAMP_AXIS_RECESS = 7.0                   # Aussparung um den Kopf der Kippachsen-Schraube (Arm 2, Ø 5,5)


class Plane(csg.N):
    """Halbraum a.P <= b (nur innerhalb von I() verwenden)."""
    def __init__(s, a, b):
        s.a = np.array(a, float); s.n = np.linalg.norm(s.a); s.b = b
    def bbox(s): return np.array([-1e4] * 3), np.array([1e4] * 3)
    def sdf(s, P): return (P @ s.a - s.b) / s.n


def bracket(x0, x1, y0, y1, z0, z1, n, w0):
    """Klotz an einer senkrechten Wand mit 45°-Unterseite (stützenfrei druckbar).
    n = Achse ('x','-x','y','-y') zeigt von der Wandfläche w0 weg; Unterseite beginnt an der Wand bei z0."""
    ax = {"x": (0, 1), "-x": (0, -1), "y": (1, 1), "-y": (1, -1)}[n]
    a = np.zeros(3); a[ax[0]] = ax[1]; a[2] = -1.0         # (s - w0) - (z - z0) <= 0
    b = ax[1] * w0 - z0
    return I(box(x0, x1, y0, y1, z0, z1), Plane(a, b))


def teardrop_y(x, z, y0, y1, d):
    """Waagrechter Zylinder entlang y mit 45°-Spitze unten (Stütze für Dome an der Wand)."""
    r = d / 2
    tip = T([x, 0, z], R([0, 45, 0], box(-r, r, y0, y1, -r, r)))
    return U(cyl_y(x, z, y0, y1, d), I(tip, box(x - r, x + r, y0, y1, z - r * 1.42, z)))


# ======================= UNTERTEIL ======================================
def part_tub():
    outer = T([LX / 2, LY / 2, 0], RBox(LX + 2 * WALL, LY + 2 * WALL, TOPZ, R_OUT))
    cav = box(0, LX, 0, LY, ZF, TOPZ + 1)
    add = []
    # Deckelschraub-Dome mit 45°-Kegel darunter
    for cx, cy in LID_SCREWS:
        add.append(cyl_z(cx, cy, TOPZ - 10, TOPZ, 8))
        add.append(T([cx, cy, TOPZ - 14], Cyl(4.01, r1=0.01, r2=4.0)))
    # Lautsprecher-Ring + Stativdom
    add.append(D(cyl_z(SPK_X, AY, ZF - 0.5, ZF + 4, SPK_D + 0.6 + 3.2), cyl_z(SPK_X, AY, ZF, ZF + 5, SPK_D + 0.6)))
    tx, ty = TRIPOD_XY
    add.append(cyl_z(tx, ty, ZF - 0.5, ZF + 6, 18))
    # Akku-Zaun (2 Seiten, die anderen sind Gehäusewand -y bzw. offen zum Lautsprecher hin)
    fx0, fx1, fy1 = BAT_X0 - 0.5, BAT_X0 + BAT_L + 0.5, BAT_W + 0.5
    add.append(box(fx0 - FENCE_T, fx0, 0, fy1 + FENCE_T, ZF - 0.5, ZF + FENCE_H))
    add.append(box(fx1, fx1 + FENCE_T, 0, fy1 + FENCE_T, ZF - 0.5, ZF + FENCE_H))
    add.append(box(fx0 - FENCE_T, fx1 + FENCE_T, fy1, fy1 + FENCE_T, ZF - 0.5, ZF + FENCE_H))
    # PCA9685-Dome an der -y-Wand
    pca_holes = [(PCA_X0 + (PCA_L - PCA_DL) / 2 + dx, ZF + PCA_ZB + (PCA_W - PCA_DW) / 2 + dz) for dx in (0, PCA_DL) for dz in (0, PCA_DW)]
    for x, z in pca_holes:
        add.append(teardrop_y(x, z, -0.5, PCA_STAND, 5.5))
    # PIR-Hülse (vorne, -x-Wand)
    pz = ZF + PIR_ZB
    add.append(bracket(-0.5, 8.0, PIR_Y - 8.5, PIR_Y + 8.5, pz - 8.5 - 8.5, pz + 8.5, "x", 0.0))
    # Mikrofon: zwei Führungsrippen + Auflage für Schaumstoff/Mikrofon
    mz = ZF + MIC_ZB
    for y0 in (MIC_Y - 9.5, MIC_Y + 8.0):
        add.append(bracket(-0.5, 12.0, y0, y0 + 1.5, mz - 6 - 12.5, mz + 6, "x", 0.0))
    add.append(bracket(-0.5, 4.0, MIC_Y - 9.5, MIC_Y + 9.5, mz - 6 - 4.5, mz - 6, "x", 0.0))
    # Auflagen Zwischenboden (+y- und +x-Wand), Schraubklötze
    sb = SHELF_Z - SHELF_T
    add.append(bracket(SHELF_X0 + 2, LX + 0.5, LY - 3.0, LY + 0.5, sb - 3.5, sb, "-y", LY))
    add.append(bracket(LX - 3.0, LX + 0.5, SHELF_Y0 + 2, LY + 0.5, sb - 3.5, sb, "-x", LX))
    for (x0, x1, y0, y1, n, w) in ((146, 154, LY - 8, LY + 0.5, "-y", LY), (LX - 8, LX + 0.5, 72, 80, "-x", LX)):
        add.append(bracket(x0, x1, y0, y1, sb - 9, sb, n, w))
    # Lüftungs-Regendach (-y aussen): Dach mit 45°-Unterseite + Wangen
    lz0, lz1 = ZF + 40, ZF + 56
    yo = -WALL
    add.append(bracket(LOUV_X0 - 4, LOUV_X1 + 4, yo - 6, yo + 0.5, lz1, lz1 + 6, "-y", yo))
    for xx in (LOUV_X0 - 4, LOUV_X1 + 2):
        add.append(bracket(xx, xx + 2, yo - 6, yo + 0.5, lz0 - 6, lz1 + 6, "-y", yo))
    # GX12-Regendach hinten (+x aussen)
    xo = LX + WALL
    add.append(bracket(xo - 0.5, xo + 9, GX12_Y - 14, GX12_Y + 14, GX12_Z + 11.5, GX12_Z + 20.5, "x", xo))
    for yy in (GX12_Y - 14, GX12_Y + 12):
        add.append(bracket(xo - 0.5, xo + 9, yy, yy + 2, GX12_Z - 16, GX12_Z + 20.5, "x", xo))
    # v5.1: Ablage für USB-Hub auf vier Stegen, Kabelbinder-Schlitze
    tz = ZF + HUB_TRAY_Z
    for x in np.linspace(HUB_X0, HUB_X1 - 2, 4):                          # 4 Stege, Brücken ~17 mm
        add.append(box(x, x + 2, HUB_Y0, LY + 0.5, ZF - 0.5, tz))
    add.append(box(HUB_X0, HUB_X1, HUB_Y0, LY + 0.5, tz - 2, tz))
    add.append(box(HUB_X0, HUB_X1, HUB_Y0, HUB_Y0 + 1.6, tz - 0.1, tz + 1.5))           # Anschlag vorne (niedrig, Stecker frei)
    # v5.1: Kragen um die Fühler-Durchführung (Kondenswasser bleibt aussen)
    add.append(cyl_z(*TEMP_XY, ZF - 0.5, ZF + 4, TEMP_D + 3.2))
    # v5.1: Relais-Buchse GX12-3P hinten unten mit Regendach
    add.append(bracket(xo - 0.5, xo + 8, RELAY_Y - 12, RELAY_Y + 12, RELAY_ZC + 9, RELAY_ZC + 17, "x", xo))
    for yy in (RELAY_Y - 12, RELAY_Y + 10):
        add.append(bracket(xo - 0.5, xo + 8, yy, yy + 2, RELAY_ZC - 14, RELAY_ZC + 17, "x", xo))
    hz = PI_Z + 4
    body = U(D(outer, cav), *add)

    cut = []
    for cx, cy in LID_SCREWS:
        cut.append(cyl_z(cx, cy, TOPZ - 9, TOPZ + 1, LID_SCREW_HOLE))
    for dx in np.arange(-15, 16, 5):                     # Lautsprechergitter
        for dy in np.arange(-15, 16, 5):
            if dx * dx + dy * dy < 17 ** 2:
                cut.append(cyl_z(SPK_X + dx, AY + dy, -1, ZF + 1, 3))
    cut.append(cyl_z(tx, ty, -1, ZF + 7, 6.8))
    cut.append(cyl_z(tx, ty, ZF + 0.2, ZF + 7, 11.3 / math.cos(math.pi / 6), fn=6))
    for fx, fy in ((10, 8), (LX - 10, 8), (10, LY - 8), (LX - 10, LY - 8)):   # Füsse (Zapfen Ø5)
        cut.append(cyl_z(fx, fy, -1, ZF - 0.6, 5.3))
    for x, z in pca_holes:
        cut.append(cyl_y(x, z, -0.2, PCA_STAND + 1, 2.2))
    cut.append(cyl_x(PIR_Y, pz, -WALL - 1, 9, PIR_D))                                       # PIR
    for dy, dz in ((0, 0), (-3, 0), (3, 0), (0, 3), (0, -3)):                               # Mikrofon
        cut.append(cyl_x(MIC_Y + dy, mz + dz, -WALL - 1, 1, 1.8))
    cut.append(cyl_x(GX12_Y, GX12_Z, LX - 1, LX + WALL + 1, GX12_D))                        # Ladebuchse
    cut.append(cyl_x(LED_Y, LED_Z, LX - 1, LX + WALL + 1, LED_D))                           # Lichtleiter
    cut.append(T([HDMI_X, -WALL / 2, hz - HDMI_H / 2], RBox(HDMI_W, WALL + 2, HDMI_H, 2)))   # HDMI-Fenster
    step = (LOUV_X1 - LOUV_X0) / LOUV_N
    for i in range(LOUV_N):
        x = LOUV_X0 + i * step + step * 0.25
        cut.append(T([x + 1.4, -WALL / 2, lz0], RBox(2.8, WALL + 2, lz1 - lz0, 1.2)))
    for (x, y) in ((146 + 4, LY - 4), (LX - 4, 76)):                                        # Zwischenboden-Schrauben
        cut.append(cyl_z(x, y, sb - 8, sb + 1, 2.6))
    for x in (22.0, 40.5, 59.0):                                                          # Kabelbinder-Schlitze Hub (zwischen den Stegen)
        cut.append(box(x, x + 3, HUB_Y0 + 4, HUB_Y0 + 8, ZF + HUB_TRAY_Z - 3, ZF + HUB_TRAY_Z + 1))
        cut.append(box(x, x + 3, LY - 6, LY - 2, ZF + HUB_TRAY_Z - 3, ZF + HUB_TRAY_Z + 1))
    cut.append(cyl_z(*TEMP_XY, -1, ZF + 5, TEMP_D))                                          # Fühler
    cut.append(cyl_x(RELAY_Y, RELAY_ZC, LX - 1, LX + WALL + 1, RELAY_D))                    # Relaisbuchse
    cut.append(box(LX - 1, LX + WALL + 1, RELAY_Y - 1, RELAY_Y + 1, RELAY_ZC + 5.5, RELAY_ZC + 7.2))   # Nut gegen Verdrehen
    return D(body, *cut)


def part_feet():
    """Ein Fuss (4x drucken): Ø14 x 6 mit Zapfen."""
    return U(cyl_z(0, 0, 0, 6.0, 14), cyl_z(0, 0, 6.0, 6.0 + ZF - 0.8, 4.9))


def part_shelf():
    x1, y1 = LX - TOL, LY - TOL
    plate = box(SHELF_X0, x1, SHELF_Y0, y1, 0, SHELF_T)
    cut = [cyl_z(146 + 4, LY - 4, -1, SHELF_T + 1, 3.4), cyl_z(LX - 4, 76, -1, SHELF_T + 1, 3.4),
           box(SHELF_X0 - 1, SHELF_X0 + 14, SHELF_Y0 - 1, SHELF_Y0 + 8, -1, SHELF_T + 1)]     # Kabelecke
    for i in range(3):                                                                     # Kabelbinder-Schlitze
        cut.append(box(SHELF_X0 + 18 + i * 10, SHELF_X0 + 21 + i * 10, SHELF_Y0 + 4, SHELF_Y0 + 8, -1, SHELF_T + 1))
    cut += shelf_grid(plate, cut)
    return D(plate, *cut)


SHELF_GRID = 5.0                         # 01.11.2026 (Besitzer): Lochraster ca. 5 mm für M2,5 / M3 selbstschneidend
SHELF_GRID_D = 2.4                       # Kernloch: M2,5 fest, M3 schneidet sich ein (PETG)
SHELF_GRID_KEEP = 2.0                    # Rand zu Plattenkante, Schlitzen, Löchern und Kabelecke (Stabilität)


def shelf_grid(plate, cut):
    """Rasterlöcher nur dort, wo um das Loch noch SHELF_GRID_KEEP Material bis zu jeder Kante / Öffnung bleibt"""
    if not SHELF_GRID:
        return []
    solid = D(plate, *cut) if cut else plate
    r = SHELF_GRID_D / 2 + SHELF_GRID_KEEP
    out = []
    for x in np.arange(SHELF_X0 + 5.0, LX - TOL - 2.0, SHELF_GRID):
        for y in np.arange(SHELF_Y0 + 5.0, LY - TOL - 2.0, SHELF_GRID):
            ring = [(x + r * math.cos(a), y + r * math.sin(a), SHELF_T / 2) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
            if np.all(solid.sdf(np.array(ring + [(x, y, SHELF_T / 2)])) < 0):
                out.append(cyl_z(x, y, -1, SHELF_T + 1, SHELF_GRID_D))
    return out


def part_hdmi_plug():
    core = T([0, 0, 0], RBox(HDMI_W - 2 * TOL, HDMI_H - 2 * TOL, 1.5 + WALL - 0.3, 2 - TOL))
    flange = RBox(HDMI_W + 6, HDMI_H + 6, 1.5, 3)
    grip = T([0, 0, 0], box(-6, 6, -(HDMI_H + 6) / 2 - 4, -(HDMI_H + 6) / 2 + 0.5, 0, 1.5))
    return D(U(flange, core, grip), T([0, 0, 1.5], RBox(HDMI_W - 2 * TOL - 3, HDMI_H - 2 * TOL - 3, 5, 1)))


# ======================= DECKEL =========================================
CHIM_X = 96.0


def part_lid():
    plate = T([LX / 2, LY / 2, TOPZ], RBox(LX + 2 * WALL, LY + 2 * WALL, LID_T, R_OUT))
    ring = D(cyl_z(AX, AY, LIDTOP - 0.1, RING_TOP, 2 * pt.RING_RO), cyl_z(AX, AY, LIDTOP - 1, RING_TOP + 1, 2 * pt.RING_RI))
    cx = CHIM_X
    chim = D(T([cx, AY, LIDTOP], RBox(16, 30, 9, 3)), T([cx, AY, LIDTOP - 1], RBox(10, 24, 7.5, 2)),
             box(cx - 12, cx, AY - 12, AY + 12, LIDTOP - 1, LIDTOP + 7))
    # Zentrierleisten unten (greifen innen in die Wanne) – an den Seiten, wo nichts stört
    body = U(plate, ring, chim)
    cut = [T([AX, AY, RING_TOP + pt.GROOVE_OFF], Torus(pt.BB_RING_R, pt.GROOVE_R)),
           box(cx - 6, cx + 6, AY - 12, AY + 12, TOPZ - 1, LIDTOP + 1)]
    for x, y in LID_SCREWS:
        cut.append(cyl_z(x, y, TOPZ - 3, LIDTOP + 1, 3.4))
        cut.append(cyl_z(x, y, LIDTOP - 1.8, LIDTOP + 1, 6.5))
    # Pan-Servo: Körper entlang x, Welle bei AX, Körper nach -x (wie v4.1)
    cut.append(box(AX - (pt.SV_L - pt.SV_SHAFT_OFF) - 0.4, AX + pt.SV_SHAFT_OFF + 0.4,
                   AY - pt.SV_W / 2 - 0.4, AY + pt.SV_W / 2 + 0.4, TOPZ - 3, LIDTOP + 1))
    bc = AX - (pt.SV_L / 2 - pt.SV_SHAFT_OFF)
    for dx in (-pt.SV_HOLE_DL / 2, pt.SV_HOLE_DL / 2):
        cut.append(cyl_z(bc + dx, AY, TOPZ - 3, LIDTOP + 1, pt.SV_HOLE_D))
        cut.append(cyl_z(bc + dx, AY, LIDTOP - 1.2, LIDTOP + 1, 4.6))
    return D(body, *cut)


# ======================= GABEL / ARM 2 mit Lampenbohrungen ==============
def cable_clip_arm1():
    """Kabelbügel an Arm 1 (v5.1) – gleiche Lage wie an Arm 2, darunter 45°-Stütze zum Arm."""
    y0, y1 = pt.A1, pt.A1 + pt.ARM_T
    blk = bracket(-24, -11.5, y0, y1, 6.0, 34, "-x", -12.0)
    return D(blk, box(-21, -12.5, y0 - 1, y1 + 1, 21, 31))


def part_yoke():
    cut = [cyl_y(x, z, ARM_OUT - 4.0, ARM_OUT + 1, 2.6) for x, z in LAMP_HOLES]
    return D(U(pt.part_yoke(), cable_clip_arm1()), *cut)


def cable_clip():
    y0 = -(pt.A1 + pt.ARM_T)
    return D(box(-24, -12 + 0.5, y0, y0 + 5, 18, 34), box(-21, -12.5, y0 - 1, y0 + 6, 21, 31))


def part_arm2():
    cut = [cyl_y(x, z, -ARM_OUT - 1, -ARM_OUT + 4.0, 2.6) for x, z in LAMP_HOLES]
    return D(U(pt.part_arm2(), cable_clip()), *cut)


# ======================= LAMPENHALTER ===================================
# lokale Koordinaten: Lampenachse = x (Licht nach +x), Mitte y = z = 0, Armfläche bei y = -(LAMP_Y - ARM_OUT)
CUP_BACK, CUP_X0 = 2.5, -2.0
CUP_ID = LAMP_MOD_D + 0.4                # 19,2 – Modul mit Heisskleber/Silikon oder Madenschraube fixieren
CUP_OD = CUP_ID + 2 * 2.2
CUP_X1 = CUP_X0 + CUP_BACK + 2.5 + LAMP_MOD_L + 1.0   # 2,5 mm Kabelraum hinten, Modul 1 mm zurückversetzt (Regen)


def part_lamp():
    gy = -(LAMP_Y - ARM_OUT)                                 # -16
    cup = D(cyl_x(0, 0, CUP_X0, CUP_X1, CUP_OD), cyl_x(0, 0, CUP_X0 + CUP_BACK, CUP_X1 + 1, CUP_ID))
    tab = box(LAMP_TAB_X0, 6.0, gy, gy + 4.0, -14, 14)
    web = box(CUP_X0, 6.0, gy + 3.0, -CUP_OD / 2 + 2.0, -6, 6)
    # 01.11.2026: Schürze hinter dem Becher bis ans Laschenende – gedruckt liegt der Halter auf der Rückseite, so steht der
    # Becherboden nicht in der Luft (wird eine 19-mm-Brücke); Schlitz oben für die Kabel
    skirt = D(cyl_x(0, 0, LAMP_TAB_X0, CUP_X0 + 0.01, CUP_OD), cyl_x(0, 0, LAMP_TAB_X0 - 1, CUP_X0 + 0.02, CUP_OD - 3.2))
    body = U(cup, tab, web, skirt)
    cut = [box(LAMP_TAB_X0 - 1, CUP_X0 + 0.005, -3.0, 3.0, 0.0, CUP_OD / 2 + 1),   # Kabelschlitz in der Schürze (oben)
           cyl_x(0, 0, CUP_X0 - 1, CUP_X0 + CUP_BACK + 1, 4.0),            # Kabel
           cyl_y(0.0, pt.AXZ - LAMP_Z, gy - 1, gy + 5, LAMP_AXIS_RECESS),    # Kopf der Kippachse (lokal z +16) ...
           cyl_y(0.0, LAMP_Z - pt.AXZ, gy - 1, gy + 5, LAMP_AXIS_RECESS)]    # ... und z -16: Halter an Arm 2 steht kopfüber
    for x, z in LAMP_HOLES:
        cut.append(cyl_y(x, z - LAMP_Z, gy - 1, gy + 5, 3.4))
    for a in (60, 120, 240, 300):                                           # Kühl-/Lüftungslöcher hinten
        cut.append(cyl_x(6 * math.cos(math.radians(a)), 6 * math.sin(math.radians(a)), CUP_X0 - 1, CUP_X0 + CUP_BACK + 1, 2.2))
    xm = CUP_X0 + CUP_BACK + 2.5 + LAMP_MOD_L / 2
    cut.append(cyl_z(xm, 0, CUP_ID / 2 - 1, CUP_OD / 2 + 1, 2.6))           # Madenschraube M3 (oben)
    return D(body, *cut)


def lamp_placed(side):
    """Lampe in Pan-Koordinaten. side=+1: Arm 1 (+y), -1: Arm 2 (-y, um x gedreht)."""
    n = part_lamp()
    if side < 0:
        n = R([180, 0, 0], n)
    return T([0, side * LAMP_Y, LAMP_Z], n)


def lamp_dummies(side):
    s = 1 if side > 0 else -1
    x0 = CUP_X0 + CUP_BACK + 2.5
    star = cyl_x(s * LAMP_Y, LAMP_Z, x0, x0 + 4, LAMP_MOD_D)
    lens = cyl_x(s * LAMP_Y, LAMP_Z, x0 + 4, x0 + LAMP_MOD_L, LAMP_MOD_D)
    return star, lens


# ======================= DUMMIES / ZUSAMMENBAU ==========================
def internals():
    d = {}
    cells = [cyl_y(BAT_X0 + 12 + i * 22, ZF + 11, 2, 2 + BAT_W - 4, 21.5) for i in range(4)]
    d["ups"] = U(*cells, box(BAT_X0, BAT_X0 + BAT_L, 0.2, BAT_W, ZF, ZF + 2),
                 box(BAT_X0 + 1, BAT_X0 + 89, 3, 59, ZF + BAT_H - 1.6, ZF + BAT_H))
    px = BAT_X0 + 1
    d["pi"] = U(box(px, px + 85, 3, 59, PI_Z, PI_Z + 1.6), box(px + 66, px + 87, 5, 57, PI_Z + 1.6, PI_Z + 17.6))
    d["cooler"] = box(px + 25, px + 56, 15, 47, PI_Z + 1.6, PI_Z + 16)
    d["pca"] = box(PCA_X0, PCA_X0 + PCA_L, PCA_STAND, PCA_STAND + 1.6, ZF + PCA_ZB, ZF + PCA_ZB + PCA_W)
    d["speaker"] = U(cyl_z(SPK_X, AY, ZF, ZF + 3, SPK_D), cyl_z(SPK_X, AY, ZF + 3, ZF + 27, 30))
    d["mosfet"] = box(0.5, 2.1, 8, 36, ZF + 44, ZF + 64)                 # an der Stirnwand (Schaumklebeband)
    d["buck"] = box(0.5, 2.1, 10, 30, ZF + 20, ZF + 28)
    d["relay"] = box(12, 62, LY - 2.6, LY - 1, ZF + 42, ZF + 65)           # 1-Kanal-Relais an der +y-Wand
    d["hub"] = box(HUB_X0 + 1, HUB_X1 - 1, HUB_Y0 + 2, HUB_Y0 + 22, ZF + HUB_TRAY_Z, ZF + HUB_TRAY_Z + 12)
    d["soundcard"] = box(HUB_X0 + 20, HUB_X0 + 32, HUB_Y0 - 42, HUB_Y0 + 2, ZF + HUB_TRAY_Z + 2, ZF + HUB_TRAY_Z + 9)   # Stick im Hub
    d["charger"] = box(126, 135.5, 62, 80, SHELF_Z, SHELF_Z + 25.4)
    d["pam"] = box(137, 155, 62, 80, SHELF_Z, SHELF_Z + 6)
    d["ina"] = box(137, 157, 82, 91, SHELF_Z, SHELF_Z + 4)                # INA219 (Solar) auf dem Zwischenboden
    d["relayjack"] = cyl_x(RELAY_Y, RELAY_ZC, LX - 13, LX + WALL + 6, 12)
    d["probe"] = cyl_z(*TEMP_XY, -40, ZF + 6, 6)
    d["mic"] = box(1, 11, MIC_Y - 7.5, MIC_Y + 7.5, ZF + MIC_ZB - 6, ZF + MIC_ZB + 6)
    d["pir"] = U(box(8, 26, PIR_Y - 5, PIR_Y + 5, ZF + PIR_ZB - 5, ZF + PIR_ZB + 5), cyl_x(PIR_Y, ZF + PIR_ZB, -1, 8, 9.8))
    d["jacks"] = cyl_x(GX12_Y, GX12_Z, LX - 20, LX + WALL + 6, 16)
    d["plug"] = T([HDMI_X, -WALL - 1.5, PI_Z + 4], R([-90, 0, 0], part_hdmi_plug()))
    sb = TOPZ - pt.TAB_TOP_TO_BOTTOM
    bc = AX - (pt.SV_L / 2 - pt.SV_SHAFT_OFF)
    d["servo1"] = U(box(AX - (pt.SV_L - pt.SV_SHAFT_OFF), AX + pt.SV_SHAFT_OFF, AY - 6.2, AY + 6.2, sb, sb + pt.SV_BODY_H),
                    box(bc - 16.25, bc + 16.25, AY - 6.2, AY + 6.2, TOPZ - 2.5, TOPZ))
    d["shelf"] = T([0, 0, SHELF_Z - SHELF_T], part_shelf())
    d["feet"] = U(*[T([fx, fy, -6.0], part_feet()) for fx, fy in ((10, 8), (LX - 10, 8), (10, LY - 8), (LX - 10, LY - 8))])
    return d


def placed(tilt=0.0, pan=180.0):
    def pan_frame(n):
        return T([AX, AY, PAN_Z0], R([0, 0, pan], n))

    def tilt_frame(n):
        return pan_frame(T([0, 0, pt.AXZ], R([0, tilt, 0], n)))
    cam3, th = pt.dummies_head()
    sw, lw = lamp_dummies(+1)
    si, li = lamp_dummies(-1)
    P = {"tub": part_tub(), "lid": part_lid(),
         "turntable": pan_frame(pt.part_turntable()), "yoke": pan_frame(part_yoke()), "arm2": pan_frame(part_arm2()),
         "lamp1": pan_frame(lamp_placed(+1)), "lamp2": pan_frame(lamp_placed(-1)),
         "lens_w": pan_frame(lw), "lens_ir": pan_frame(li), "alu": pan_frame(U(sw, si)),
         "head": tilt_frame(pt.part_head()), "side": tilt_frame(pt.part_sidecover()),
         "servo2": tilt_frame(pt.dummy_tilt_servo()), "horn2": pan_frame(pt.dummy_tilt_horn()), "horn1": pan_frame(pt.dummy_pan_horn()),
         "cam3": tilt_frame(cam3), "therm": tilt_frame(th),
         "balls": T([AX, AY, RING_TOP + pt.GROOVE_OFF - (pt.GROOVE_R - pt.BB_D / 2)], Torus(pt.BB_RING_R, pt.BB_D / 2))}
    P.update(internals())
    return P


if __name__ == "__main__":
    print("Unterteil aussen:", LX + 2 * WALL, LY + 2 * WALL, "Höhe bis Deckel oben:", LIDTOP,
          " Kippachse:", round(PAN_Z0 + pt.AXZ, 1), " Gesamthöhe ~", round(PAN_Z0 + pt.AXZ + pt.HH / 2, 1),
          " Zwischenboden oben:", SHELF_Z, " GX12 z:", GX12_Z)
