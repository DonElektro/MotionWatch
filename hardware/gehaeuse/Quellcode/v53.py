"""MoveEye Gehäuse v5.3 – Variante auf Basis v5.2 (v52.py und v5.py bleiben unverändert; v5.1 und v5.2 bleiben erzeugbar).
Auftrag des Besitzers vom 02.11.2026 (Zweig real-gehaeuse-v53). Masse mit «NACHMESSEN» sind geschätzt.

Neu in v5.3:
  1. Gewindeeinsätze aus Messing (Heat-Set M3, z. B. ruthex M3 × 5,7, Bohrung Ø 4,0 nach Herstellerangabe) statt
     selbstschneidender Schrauben: Deckel ↔ Unterteil (6 Dome), Zwischenboden (2 Klötze, tiefer), Akkuklappe (4 Dome).
     Der Seitendeckel des Kopfs bleibt selbstschneidend: seine Säulen (Ø 6) sind zu dünn für einen Einsatz (Ø 4 + 2 × 1,6)
     und der Kopf ist voll (Kamera, Wärmebild) – er wird selten geöffnet.
  2. Halter für Wand und Baum (25_Halter_Wand_Baum): L-Winkel, Plattform unter dem Gerät (vordere Füsse rasten in Mulden
     mit Quetschrippen ein, eine Schraube 1/4"-20 von unten in die Stativmutter – das Stativgewinde bleibt frei nutzbar),
     Rückwand mit 2 Schlitzpaaren für einen Spanngurt 25 mm und 4 Löchern für Wandschrauben (4–5 mm), 2 Rippen als
     Auflage am Stamm. Rückwand an der +y-Seite (dort hat das Unterteil keine Öffnungen).
  3. Akkuklappe unten (26_Akkuklappe): Öffnung im Boden unter den 4 Zellen 21700 (die Zellen hängen unter der Platine des
     UPS HAT (E), angenommen wie in v5.py). Klappe mit 4 × M3 × 8 in Einsätzen von unten: Zellen tauschen ohne Deckel
     und ohne den Pi auszubauen. Die SD-Karte bleibt wie in v5.2 über die microSD-Verlängerung im Schlitz der
     Lüftungswand (Stopfen 16) erreichbar – sie steckt zwischen Pi und HAT und ist von unten nicht erreichbar.
     Die Füsse sitzen dafür weiter aussen in den Ecken (FEET53), sonst stünde ein Fuss auf der Klappe.
  4. Luftführung (27_Luftkanal): Einlass mit 3 Schlitzen und Regendach in der Lüftungswand über dem Service-Fenster,
     Kanal (Haube) vom Einlass über den Pi-Rand auf die Ansaugöffnung des Active Cooler. Die warme Luft tritt aus den
     Kühlrippen in den Innenraum und geht wie bisher durch die Lüftungsschlitze hinaus. Die Kamerakabel laufen über
     die Haube (CAM0 / CAM1 neu verlegt).
  5. Zugentlastung: Kabelbinder-Öse im Kabelkamin des Deckels (Servo- und Kamerakabel vom Drehteller), Ösen innen an der
     Rückwand über der GX16-Ladebuchse und neben der Relais-Buchse sowie an der +y-Wand neben dem Relais-Modul.
Koordinaten wie v5.py (Unterteil: x 0..LX innen, x = 0 Stirnwand innen, z = 0 Bodenunterseite).
"""
import math
import numpy as np
from csg import *
import csg
import pantilt as pt
import v5
import v52
from v5 import (LX, LY, WALL, ZF, TOPZ, LIDTOP, AX, AY, Plane, bracket)

# ======================= PARAMETER v5.3 =================================
# --- 1 Gewindeeinsätze (Heat-Set M3, ruthex M3 × 5,7 – Bohrung nach Herstellerangabe Ø 4,0, Mindestwand 1,6)
INS_D = 4.0                          # Herstellerangabe prüfen (ruthex M3 × 5,7: Ø 4,0 mm)
INS_L = 5.7
INS_HOLE_L = 6.7                     # Bohrtiefe = Einsatzlänge + 1 mm (Platz für Schmelze)
INS_WALL_MIN = 1.6
SB = v5.SHELF_Z - v5.SHELF_T         # Unterseite Zwischenboden (Auflage)
SHELF_SCREWS = [(150.0, LY - 4.0), (LX - 4.0, 76.0)]
SHELF_BLOCK_Z0 = SB - 17.0           # Klötze tiefer als v5.1 (sonst bricht die Einsatzbohrung durch die 45°-Unterseite)
# --- 3 Akkuklappe (Boden unter dem UPS HAT (E) mit 4 × 21700)
OPEN_X0, OPEN_X1, OPEN_Y0, OPEN_Y1 = 74.0, 162.0, 4.0, 76.0   # Öffnung im Boden (Zellen x 74,3..161,8, Länge 70 mm in y)
OPEN_R = 3.0
FEET53 = [(6.0, 6.0), (172.0, 6.0), (6.0, 86.0), (172.0, 86.0)]   # Füsse in die Ecken (v5.1/v5.2: (10, 8) …)
FEET_OLD = [(10.0, 8.0), (LX - 10.0, 8.0), (10.0, LY - 8.0), (LX - 10.0, LY - 8.0)]
HATCH_T = 2.0                        # Klappe unter dem Boden (Füsse 6 mm: 4 mm Luft zum Tisch)
HATCH_X0, HATCH_X1, HATCH_Y0, HATCH_Y1 = 64.5, 163.5, 0.0, 80.0
HATCH_EAR = (163.0, 172.5, 18.0, 66.0)   # Lasche für die hinteren Schrauben (zwischen den Füssen)
HATCH_SCREWS = [(69.0, 12.0), (69.0, 71.0), (168.5, 24.0), (168.5, 60.0)]
HATCH_BOSS_D = 8.0
HATCH_BOSS_Z1 = 8.5                  # Domoberkante (Einsatzbohrung von unten 6,7 + 45°-Spitze)
HATCH_TRIPOD_R = 9.0                 # Aussparung um Stativschraube (Kopf Ø 11) bei TRIPOD_XY
HATCH_RIM_W, HATCH_RIM_H, HATCH_TOL = 1.8, 2.3, 0.3
HATCH_RIB_Y = (22.0, 40.0, 58.0)     # Stützrippen unter den Zellen (quer zu den Zellen)
# --- 4 Luftführung: Einlass in der Lüftungswand (-y) und Haube auf dem Active Cooler
COOL_X0, COOL_X1, COOL_Y0, COOL_Y1 = 99.0, 130.0, 15.0, 47.0   # Active Cooler (v5.py internals: px+25..px+56, y 15..47)
COOL_TOP = v5.PI_Z + 16.0            # NACHMESSEN: Oberkante Active Cooler (Annahme v5.py)
FAN_IN = (103.0, 126.0, 19.0, 43.0)  # NACHMESSEN: Ansaugöffnung oben auf dem Active Cooler (Annahme check52.py)
INLET_X = (108.8, 112.8, 116.8)      # 3 Schlitze 2,5 × 6 mm über dem Service-Fenster (Stopfen-Flansch bis z 54,5, rechts vom
INLET_W, INLET_Z0, INLET_Z1 = 2.5, 55.5, 61.5     # Griff des Stopfens 10 bei x 93..105), Steg dazwischen 1,5 mm
INLET_ROOF_Z0 = 62.5                 # Regendach: Unterseite an der Wand, 6 mm tief, 45°
DUCT_T = 1.6                         # Wand der Haube
DUCT_TOP0 = 63.4                     # Unterseite Haubendach (oben 65,0 – darüber die Kamerakabel, Deckel bei 68,5)
DUCT_CH = (99.0, 119.5, 0.4, 15.0)     # Kanal vom Einlass zum Kühler (x, y), Wände bis z DUCT_CH_Z0
DUCT_CH_Z0 = 50.0
DUCT_CAP_Z0 = COOL_TOP + 0.3         # Haube liegt auf dem Kühler (Schaumstoff-Streifen)
# --- 5 Zugentlastung (Kabelbinder 2,5–3,6 mm)
TIE_W, TIE_T = 4.2, 2.0              # Tunnel für den Kabelbinder
# --- 2 Halter Wand / Baum
HOLD_X0, HOLD_X1 = -10.0, 188.0
HOLD_Y0 = -6.0
HOLD_PLATE_Y = LY + WALL + 6.0       # Vorderfläche der Rückwand (6 mm Luft zum Gerät: Gurt, Schraubenköpfe)
HOLD_PLATE_T = 5.0
HOLD_Z_TOP = -3.0                    # Oberseite Plattform (Füsse stehen 3 mm in den Mulden, Klappe frei)
HOLD_T = 5.0
HOLD_H = 56.0                        # Oberkante Rückwand (unter dem Deckel, Kopf und Lampen frei)
STRAP_W, STRAP_SLOT = 28.0, 4.0      # Schlitz für Gurt 25 mm
STRAP_X = [(8.0, 20.0), (158.0, 170.0)]   # Schlitzpaare (dazwischen der Steg, über den der Gurt läuft)
STRAP_Z = 8.0                        # Unterkante Schlitze
WALL_HOLES = [(40.0, 6.0), (138.0, 6.0), (40.0, 44.0), (138.0, 44.0)]   # (x, z) Ø 5 für Schrauben 4–5 mm
TRIPOD_SCREW = '1/4"-20 × 16 mm'


# ======================= 1 EINSÄTZE =====================================
def insert_hole_down(x, y, z_top, depth=INS_HOLE_L):
    """Einsatzbohrung von oben (Öffnung oben bei z_top)"""
    return cyl_z(x, y, z_top - depth, z_top + 1, INS_D)


def insert_hole_up(x, y, z_bot, depth=INS_HOLE_L):
    """Einsatzbohrung von unten (Öffnung unten) mit 45°-Spitze oben (ohne Brücke druckbar)"""
    r = INS_D / 2
    return U(cyl_z(x, y, z_bot - 1, z_bot + depth, INS_D), T([x, y, z_bot + depth - 0.01], Cyl(r + 0.01, r1=r, r2=0.01)))


def lid_inserts():
    return [insert_hole_down(x, y, TOPZ) for x, y in v5.LID_SCREWS]


def shelf_blocks():
    """tiefere Klötze für die Einsätze des Zwischenbodens (45°-Unterseite an der Wand)"""
    return [bracket(146.0, 154.0, LY - 8.0, LY + 0.5, SHELF_BLOCK_Z0, SB, "-y", LY),
            bracket(LX - 8.0, LX + 0.5, 72.0, 80.0, SHELF_BLOCK_Z0, SB, "-x", LX)]


def shelf_inserts():
    return [insert_hole_down(x, y, SB) for x, y in SHELF_SCREWS]


# ======================= 3 AKKUKLAPPE ===================================
def floor_opening():
    w, d = OPEN_X1 - OPEN_X0, OPEN_Y1 - OPEN_Y0
    return T([(OPEN_X0 + OPEN_X1) / 2, (OPEN_Y0 + OPEN_Y1) / 2, -1.0], RBox(w, d, ZF + 2.0, OPEN_R))


def hatch_bosses():
    return [cyl_z(x, y, ZF - 0.5, HATCH_BOSS_Z1, HATCH_BOSS_D) for x, y in HATCH_SCREWS]


def hatch_insert_holes():
    return [insert_hole_up(x, y, 0.0) for x, y in HATCH_SCREWS]


def feet_fill():
    """alte Fusslöcher (v5.1 / v5.2) schliessen"""
    return [cyl_z(x, y, -0.01, ZF - 0.3, 5.6) for x, y in FEET_OLD]


def feet_holes():
    return [cyl_z(x, y, -1, ZF - 0.6, 5.3) for x, y in FEET53]


def hatch_outline(off=0.0, z0=0.0, z1=1.0):
    """Umriss der Klappe als Prisma z0..z1; off > 0 vergrössert (Aussparung im Halter)"""
    main = box(HATCH_X0 - off, HATCH_X1 + off, HATCH_Y0 - off, HATCH_Y1 + off, z0, z1)
    ear = box(HATCH_EAR[0], HATCH_EAR[1] + off, HATCH_EAR[2] - off, HATCH_EAR[3] + off, z0, z1)
    tx, ty = v5.TRIPOD_XY
    return D(U(main, ear), cyl_z(tx, ty, z0 - 1, z1 + 1, 2 * (HATCH_TRIPOD_R - off)))


def part_hatch():
    """26 Akkuklappe (Unterteil-Koordinaten: Platte z -2..0 unter dem Boden, Rand und Rippen in der Öffnung).
    Druck: Platte unten, ohne Stützen."""
    plate = hatch_outline(0.0, -HATCH_T, 0.0)
    w, d = OPEN_X1 - OPEN_X0 - 2 * HATCH_TOL, OPEN_Y1 - OPEN_Y0 - 2 * HATCH_TOL
    cx, cy = (OPEN_X0 + OPEN_X1) / 2, (OPEN_Y0 + OPEN_Y1) / 2
    rim = D(T([cx, cy, -0.01], RBox(w, d, HATCH_RIM_H, OPEN_R - HATCH_TOL)),
            T([cx, cy, -1.0], RBox(w - 2 * HATCH_RIM_W, d - 2 * HATCH_RIM_W, HATCH_RIM_H + 2, max(OPEN_R - HATCH_TOL - HATCH_RIM_W, 0.5))))
    ribs = [box(OPEN_X0 + 1.0, OPEN_X1 - 1.0, y - 0.8, y + 0.8, -0.01, HATCH_RIM_H) for y in HATCH_RIB_Y]
    body = U(plate, rim, *ribs)
    cut = []
    for x, y in HATCH_SCREWS:
        cut.append(cyl_z(x, y, -HATCH_T - 1, 1, 3.4))
    cut.append(box(cx - 6, cx + 6, HATCH_Y0 - 1, HATCH_Y0 + 2.0, -HATCH_T - 1, 0.01))   # Kerbe am Rand: Schraubenzieher zum Abheben
    return D(body, *cut)


def hatch_placed():
    return part_hatch()


# ======================= 4 LUFTFÜHRUNG ==================================
def inlet_cuts():
    out = []
    for x in INLET_X:
        out.append(T([x, -WALL / 2, INLET_Z0], RBox(INLET_W, WALL + 2, INLET_Z1 - INLET_Z0, 1.0)))
    return out


def inlet_roof():
    yo = -WALL
    x0, x1 = INLET_X[0] - INLET_W / 2 - 1.9, INLET_X[-1] + INLET_W / 2 + 2.0   # Wangen neben dem Griff des Stopfens 10
    add = [bracket(x0, x1, yo - 6, yo + 0.5, INLET_ROOF_Z0, TOPZ, "-y", yo)]
    for xx in (x0, x1 - 2.0):
        add.append(bracket(xx, xx + 2.0, yo - 6, yo + 0.5, INLET_Z0, TOPZ, "-y", yo))
    return add


def part_duct():
    """27 Luftkanal (Unterteil-Koordinaten, eingebaut): Haube auf dem Active Cooler + Kanal zum Einlass. Unten offen
    (der Kühler ist der Boden), die Haube liegt mit einem Schaumstoff-Streifen auf dem Kühler, der Deckel hält sie über
    ein Schaumstoff-Pad. 4 Finger an den Seiten zentrieren sie. Druck: Dach unten (gedreht), ohne Stützen."""
    t = DUCT_T
    top = DUCT_TOP0 + t
    cap = box(COOL_X0, COOL_X1, COOL_Y0, COOL_Y1, DUCT_CAP_Z0, top)
    ch = box(DUCT_CH[0], DUCT_CH[1], DUCT_CH[2], DUCT_CH[3], DUCT_CH_Z0, top)
    cap_in = box(COOL_X0 + t, COOL_X1 - t, COOL_Y0 + t, COOL_Y1 - t, DUCT_CAP_Z0 - 1, DUCT_TOP0)
    ch_in = box(DUCT_CH[0] + t, DUCT_CH[1] - t, DUCT_CH[2] - 1, COOL_Y0 + t + 0.01, DUCT_CH_Z0 - 1, DUCT_TOP0)
    fz0 = COOL_TOP - 2.5
    fingers = [box(COOL_X1 + 0.3, COOL_X1 + 0.3 + t, 29.0, 33.0, fz0, top),        # +x
               box(110.0, 114.0, COOL_Y1 + 0.3, COOL_Y1 + 0.3 + t, fz0, top),      # +y
               box(COOL_X0 - 0.3 - t, COOL_X0 - 0.3, 36.0, 40.0, fz0, top)]        # -x (neben dem Kamin-Kabel)
    roof = [box(COOL_X0 - 0.3 - t, COOL_X0 + 0.01, 36.0, 40.0, DUCT_TOP0, top),
            box(COOL_X1 - 0.01, COOL_X1 + 0.3 + t, 29.0, 33.0, DUCT_TOP0, top),
            box(110.0, 114.0, COOL_Y1 - 0.01, COOL_Y1 + 0.3 + t, DUCT_TOP0, top)]
    return D(U(cap, ch, *fingers, *roof), cap_in, ch_in)


def cable_cam1_pts():
    """CAM1 v5.3: wie v5.2 bis vor den Pi, dann über das Dach der Luftführung zum Kabelkamm (Schlitz 1)"""
    p = v52.cable_cam1_pts()
    sx = v52.fpc_slots()[0]
    cx, cy = v52.PI_CAM1_XY
    zt = DUCT_TOP0 + DUCT_T + 1.6
    return p[:4] + [(90.0, 20.0, 60.0), (95.5, 9.0, zt), (120.6, 7.5, zt), (sx, 7.5, 62.0), (sx, 7.5, 58.0), (sx, 7.5, 50.0),
                    (cx, cy, 46.0), (cx, cy, v5.PI_Z + 3.0)]


def cable_cam0_pts():
    """CAM0 v5.3: Kabelkamin -> über das Dach der Luftführung -> Kabelkamm (Schlitz 2) -> Buchse CAM/DISP 0"""
    sx = v52.fpc_slots()[1]
    cx, cy = v52.PI_CAM0_XY
    zt = DUCT_TOP0 + DUCT_T + 1.6
    return [(v5.CHIM_X, AY, TOPZ + 1.0), (v5.CHIM_X, AY, zt), (101.0, 30.0, zt), (120.6, 9.5, zt), (sx, 9.5, 62.0),
            (sx, 9.5, 58.0), (sx, 9.5, 50.0), (cx, cy, 46.0), (cx, cy, v5.PI_Z + 3.0)]


# ======================= 5 ZUGENTLASTUNG ================================
def tie_block_wall(n, w0, a0, a1, z0, z1, depth=5.0):
    """Kabelbinder-Öse an einer Innenwand: Klotz mit 45°-Unterseite, senkrechter Tunnel (Kabelbinder von oben durch)
    n = '-x' (Wand +x innen, w0 = LX) oder '-y' (Wand +y innen, w0 = LY); a0..a1 = Lage entlang der Wand"""
    if n == "-x":
        blk = bracket(w0 - depth, w0 + 0.5, a0, a1, z0, z1, "-x", w0)
        am = (a0 + a1) / 2
        tun = box(w0 - depth + 1.5, w0 - depth + 1.5 + TIE_T, am - TIE_W / 2, am + TIE_W / 2, z0 - 20, z1 + 1)
    else:
        blk = bracket(a0, a1, w0 - depth, w0 + 0.5, z0, z1, "-y", w0)
        am = (a0 + a1) / 2
        tun = box(am - TIE_W / 2, am + TIE_W / 2, w0 - depth + 1.5, w0 - depth + 1.5 + TIE_T, z0 - 20, z1 + 1)
    return blk, tun


TIE_TUB = [("-x", LX, 70.0, 77.5, 53.0, 64.0),     # über der GX16-Ladebuchse (Kabel zum Lader)
           ("-x", LX, 37.0, 45.0, 14.0, 26.0),     # neben der Relais-Buchse (GX12-3P bzw. Kabelverschraubung)
           ("-y", LY, 63.5, 71.5, 46.0, 58.0)]     # +y-Wand neben dem Relais-Modul
TIE_LID = (82.4, 90.0, AY - 4.0, AY + 4.0)         # Öse im Kabelkamin (vor dem Loch im Deckel)


def tie_tub():
    add, cut = [], []
    for n, w0, a0, a1, z0, z1 in TIE_TUB:
        b, t = tie_block_wall(n, w0, a0, a1, z0, z1)
        add.append(b); cut.append(t)
    return add, cut


def tie_lid():
    """Öse auf dem Deckel im Kabelkamin: Kabel liegt oben auf, Kabelbinder durch den Tunnel (entlang y, 45°-Dach)"""
    x0, x1, y0, y1 = TIE_LID
    blk = box(x0, x1, y0, y1, LIDTOP - 1.05, LIDTOP + 5.0)    # ab der Kamin-Mulde (Deckel dort 1 mm tiefer)
    xc = (x0 + x1) / 2
    z0 = LIDTOP + 0.6
    tun = U(box(xc - TIE_W / 2, xc + TIE_W / 2, y0 - 1, y1 + 1, z0, z0 + TIE_T),
            I(T([xc, 0, z0 + TIE_T], R([0, 45, 0], box(-TIE_W / 2 / 1.4142, TIE_W / 2 / 1.4142, y0 - 1, y1 + 1, -TIE_W / 2 / 1.4142, TIE_W / 2 / 1.4142))),
              box(xc - TIE_W / 2, xc + TIE_W / 2, y0 - 1, y1 + 1, z0 + TIE_T, z0 + TIE_T + TIE_W)))
    return blk, tun


# ======================= UNTERTEIL v5.3 =================================
def part_tub():
    tadd, tcut = tie_tub()
    add = [*shelf_blocks(), *hatch_bosses(), *feet_fill(), *inlet_roof(), *tadd]
    cut = [floor_opening(), *hatch_insert_holes(), *feet_holes(), *lid_inserts(), *shelf_inserts(), *inlet_cuts(), *tcut]
    return D(U(v52.part_tub(), *add), *cut)


# ======================= DECKEL v5.3 ====================================
def part_lid():
    blk, tun = tie_lid()
    return D(U(v5.part_lid(), blk), tun)


# ======================= 25 HALTER WAND / BAUM ==========================
def _gable_slot_y(x0, x1, z0, z1, y0, y1):
    """Schlitz durch eine Wand entlang y mit 45°-Giebel oben (ohne Brücke)"""
    w = x1 - x0
    r = w / 2 / 1.4142
    xc = (x0 + x1) / 2
    gable = I(T([xc, 0, z1], R([0, 45, 0], box(-r, r, y0, y1, -r, r))), box(x0, x1, y0, y1, z1, z1 + w))
    return U(box(x0, x1, y0, y1, z0, z1), gable)


def _teardrop_y(x, z, y0, y1, d):
    r = d / 2
    tip = I(T([x, 0, z], R([0, 45, 0], box(-r, r, y0, y1, -r, r))), box(x - r, x + r, y0, y1, z, z + r * 1.42))
    return U(cyl_y(x, z, y0, y1, d), tip)


def part_holder():
    """25 Halter für Wand und Baum (Unterteil-Koordinaten, Gerät eingesetzt). Druck: Plattform unten, Rückwand steht."""
    zt, zb = HOLD_Z_TOP, HOLD_Z_TOP - HOLD_T
    yp = HOLD_PLATE_Y
    plat = box(HOLD_X0, HOLD_X1, HOLD_Y0, yp + 0.01, zb, zt)
    plate = box(HOLD_X0, HOLD_X1, yp, yp + HOLD_PLATE_T, zb, HOLD_H)
    fillet = I(box(HOLD_X0, HOLD_X1, yp - 5.0, yp + 0.01, zt - 0.01, zt + 5.0), Plane([0, -1, -1], -(yp - 5.0) - zt))
    gus = []
    for x in (HOLD_X0, HOLD_X1 - 3.0):                      # Seitenrippen (ausserhalb des Geräts)
        g = I(box(x, x + 3.0, yp - 40.0, yp + 0.01, zt - 0.01, zt + 40.0), Plane([0, -1, 1], -(yp - 40.0) + zt))
        gus.append(g)
    ribs = [box(x, x + 3.0, yp + HOLD_PLATE_T - 0.01, yp + HOLD_PLATE_T + 2.5, zb, HOLD_H) for x in (60.0, 115.0)]   # Auflage am Stamm
    body = U(plat, plate, fillet, *gus, *ribs)
    cut = []
    for fx, fy in FEET53[::2]:                               # vordere Füsse (x 6): Mulden mit Quetschrippen
        cut.append(cyl_z(fx, fy, zt - 3.0, zt + 1, 14.8))
    for fx, fy in FEET53[1::2]:                              # hintere Füsse (x 172): Mulde, zur Klappen-Aussparung hin offen
        cut.append(U(cyl_z(fx, fy, zt - 3.0, zt + 1, 14.8), box(HATCH_X1, fx, fy - 7.4, fy + 7.4, zt - 3.0, zt + 1)))
    cut.append(cyl_z(30.0, AY, zb - 1, zt + 1, 42.0))        # Lautsprecher frei
    cut.append(hatch_outline(1.0, zb - 1, zt + 1))                           # Akkuklappe von unten erreichbar
    tx, ty = v5.TRIPOD_XY
    cut.append(cyl_z(tx, ty, zb - 1, zt + 1, 6.8))           # Schraube 1/4"-20 in die Stativmutter
    cut.append(cyl_z(*v5.TEMP_XY, zb - 1, zt + 1, 12.0))     # Temperaturfühler DS18B20 hängt durch den Boden (Stopfen 20: Flansch Ø 9)
    for x0, x1 in STRAP_X:                                   # Gurt-Schlitzpaare
        for xs in (x0, x1):
            cut.append(_gable_slot_y(xs - STRAP_SLOT / 2, xs + STRAP_SLOT / 2, STRAP_Z, STRAP_Z + STRAP_W, yp - 1, yp + HOLD_PLATE_T + 3))
    for x, z in WALL_HOLES:
        cut.append(_teardrop_y(x, z, yp - 1, yp + HOLD_PLATE_T + 3, 5.0))
    body = D(body, *cut)
    crush = []
    for fx, fy in FEET53[::2]:                               # 3 Quetschrippen je Mulde (Fuss Ø 14: 0,15 mm Übermass)
        for a in (90, 210, 330):
            crush.append(T([fx, fy, zt - 3.0], R([0, 0, a], box(6.85, 7.5, -0.8, 0.8, 0, 3.0))))
    return U(body, *crush)


# ======================= DUMMIES / ZUSAMMENBAU ==========================
def cells_dummy():
    """die 4 Zellen 21700 (wie v5.internals), zum Zeigen bei offener Klappe"""
    return U(*[cyl_y(v5.BAT_X0 + 12 + i * 22, ZF + 11, 2, 2 + v5.BAT_W - 4, 21.5) for i in range(4)])


def feet_placed():
    return {f"feet{'' if i == 0 else i + 1}": T([fx, fy, -6.0], v5.part_feet()) for i, (fx, fy) in enumerate(FEET53)}


def tripod_screw():
    """Schraube 1/4"-20 × 16 mm mit Rändelkopf von unten durch den Halter in die Stativmutter"""
    tx, ty = v5.TRIPOD_XY
    zb = HOLD_Z_TOP - HOLD_T
    return U(cyl_z(tx, ty, zb - 4.0, zb, 11.0), cyl_z(tx, ty, zb - 0.01, zb + 15.9, 6.2))


def placed(tilt=0.0, pan=180.0, blinds=False, halter=False, klappe_offen=False):
    P = v52.placed(tilt, pan, blinds)
    P["tub"] = part_tub()
    P["lid"] = part_lid()
    P["feet"] = U(*feet_placed().values())
    P["hatch"] = T([0, 0, -40.0], part_hatch()) if klappe_offen else part_hatch()
    P["duct"] = part_duct()
    P["cam1"] = v52.kabel(cable_cam1_pts())
    P["cam0"] = v52.kabel(cable_cam0_pts())
    if halter:
        P["holder"] = part_holder()
        P["tscrew"] = tripod_screw()
    return P


if __name__ == "__main__":
    print("Öffnung Boden x %.1f..%.1f y %.1f..%.1f; Zellen x %.1f..%.1f" % (OPEN_X0, OPEN_X1, OPEN_Y0, OPEN_Y1,
          v5.BAT_X0 + 12 - 10.75, v5.BAT_X0 + 12 + 66 + 10.75))
    print("Füsse v5.3:", FEET53, " Klappen-Schrauben:", HATCH_SCREWS)
    print("Halter: x %.0f..%.0f, Rückwand y %.1f, Höhe bis z %.0f" % (HOLD_X0, HOLD_X1, HOLD_PLATE_Y, HOLD_H))
