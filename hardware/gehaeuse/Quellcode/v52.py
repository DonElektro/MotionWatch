"""MotionWatch Gehäuse v5.2 – Variante zu v5.1 (v5.py bleibt unverändert und wird importiert; v5.1 bleibt erzeugbar).
Paket v5.2 vom 30.10.2026, ins Repository übernommen und erweitert am 01.11.2026 (Zweig real-gehaeuse-v52):
  - breite IR-LED jetzt als Modul 850 nm mit 120°-Linse (IR_TYP = "modul"; die 5-mm-LED bleibt als IR_TYP = "5mm")
  - Trennsteg aussen zwischen IR-Modul und Kamera-Fenster
  - Führung (Kamm) für zwei Flachkabel CAM0 / CAM1 an der Lüftungswand neben den Kamera-Buchsen des Pi 5
  - Kabelwege CAM0 / CAM1 als Modell (Abstand zu Lüfter, Lüftungsschlitzen, Lautsprecher in check52.py)
  Masse mit «NACHMESSEN» sind geschätzt (Liste: LIESMICH.md und Dokumente/LIESMICH_Montage_v5-2.md).

Neu in v5.2:
  1. Weitwinkel-Kamera (Camera Module 3 Wide) an der Stirnwand (x = 0) über dem PIR, 12° nach unten geneigt,
     Fenster aus dem Sichtfeld berechnet (120° diagonal nicht beschnitten), Regendach (Blende) darüber.
  2. Loch + Hülse für eine 5-mm-IR-LED (850 nm) links vom PIR.
  3. Status-RGB-LED (5 mm) oben auf dem Kamerakopf mit Sockel (Vertiefung) für einen Diffusor.
  4. Zwei Tasten (12 mm, IP67) an der Rückwand mit Regendach und Seitenwangen.
  5. Neue Kleinteile: Blindstopfen Weitwinkel-Fenster, Stopfen IR-LED (beide mit Rastnasen), Diffusor + Pupillenring.
  MOSFET-Modul: neuer Platz an der -y-Wand unter dem PCA9685 (vorne war es der Kamera im Weg).
Koordinaten wie v5.py (Unterteil: x 0..LX innen, x = 0 Stirnwand innen; Kopf: Kipp-Koordinaten, Dach z = +29).
"""
import math
import numpy as np
from csg import *
import csg
import pantilt as pt
import v5
from v5 import (LX, LY, WALL, ZF, TOPZ, LIDTOP, AX, AY, PIR_Y, PIR_ZB, Plane, bracket)

# ======================= PARAMETER v5.2 =================================
# --- Weitwinkel-Kamera (Raspberry Pi Camera Module 3 Wide)
WC_TILT = 12.0                       # Neigung nach unten (Grad)
WC_LENS = (0.5, AY, 56.0)            # Mitte Linsen-Vorderseite (0,5 mm hinter der Wand-Innenseite)
WC_LENS_H = 11.4                     # NACHMESSEN: Platinen-Vorderseite -> Linsen-Vorderseite (geschätzt: 12,4 gesamt - 1,0 Platine)
WC_BOARD = (25.0, 24.0, 1.0)         # Breite (y), Höhe, Dicke
WC_LENS_FROM_TOP = 9.5               # NACHMESSEN: Linsenmitte unter Platinen-Oberkante (wie CM3, bei der Wide prüfen)
WC_HOLES = [(dy, dv) for dy in (-10.5, 10.5) for dv in (9.5 - 2.0, 9.5 - 14.5)]   # 21 x 12,5 mm, M2
WC_PAD = 1.6                         # Auflage-Polster (Platine liegt nur an den Löchern auf)
WC_RIB_W = 6.5                       # Rippenbreite (y); 01.11.2026: 5 -> 6,5, damit um das M2-Loch >= 1,5 mm bleiben
WC_PAD_D = 6.0                       # Polster-Ø (vorher 5)
WC_PILOT = 1.7                       # Kernloch M2 selbstschneidend
WC_FOV_H, WC_FOV_V = 58.5, 46.7      # halbe Fenster-Winkel (tan-Mass): Ecken 56,5° / 44,7° + 2° Reserve
WC_R0 = 3.0                          # NACHMESSEN: halbe Öffnung der Frontlinse (geschätzt, Ø6) – Fenster-Startquerschnitt
WC_BACK = 1.0                        # Fenster startet 1 mm hinter der Linse (falls die Linse kürzer ist)
WC_VIS_L = 5.0                       # Regendach-Tiefe vor der Wand (endet unter dem Deckelrand, z <= TOPZ)
# --- breite IR-LED: Modul 850 nm mit 120°-Linse (Standard ab 01.11.2026) oder 5-mm-LED (Paket vom 30.10.2026)
IR_TYP = "modul"                     # "modul" | "5mm"
IRW_Y, IRW_Z = 20.0, 49.0            # Mitte Modul an der Stirnwand (neben der Kamera, über dem Wandler D36V28F5)
IRW_MOD_D = 18.8                     # NACHMESSEN: Modul-Ø (geschätzt wie das Scheinwerfer-Modul LAMP_MOD_D)
IRW_MOD_L = 14.0                     # NACHMESSEN: Modul-Länge inkl. Linse und Sternplatine
IRW_LENS_D = 17.0                    # NACHMESSEN: Ø der Linse vorne = Loch in der Wand (Modul liegt innen am Lochrand an)
IRW_TOL = 0.4                        # Spiel Modul in der Hülse (Ø)
IRW_SLEEVE_T = 2.0                   # Hülsenwand
IRW_SLEEVE_L = 7.0                   # Hülsenlänge ab Wand innen (länger -> 45°-Stütze trifft den Wandler)
IRW_CHAMFER = 0.0                    # Fase 45° aussen am Loch (120°-Lichtkegel); 01.11.2026: 2 -> 1, sonst schneidet sie den Trennsteg-Fuss an
# --- Trennsteg aussen zwischen IR-Modul und Kamera-Fenster (gegen Streulicht, Regen von der Seite)
TRENN_Y, TRENN_T, TRENN_L = 28.6, 1.8, 1.5   # Lage (y), Dicke, Tiefe vor der Wand – ganz ausserhalb des Fenster-Keils (sonst
                                             # bleiben dünne Reste); 01.11.2026: 1,8 dick (>= 1,5) – NACHMESSEN: Abstand reicht?
# --- Führung für die zwei Flachkabel (CAM0 vom Kopf, CAM1 von der Weitwinkel-Kamera)
FPC_X0 = 121.0                       # erste Rippe (nach dem HDMI-Fenster x 90..120, vor den Lüftungsschlitzen ab x 129)
FPC_FIN, FPC_SLOT = 1.5, 1.5         # Rippendicke, Schlitzbreite (Flachkabel 0,3 mm; Platz zum Einlegen)
FPC_DEPTH = 14.0                     # Rippen ragen so weit in den Innenraum (Kabelbreite 22-polig ca. 11,5 mm)
FPC_Z0 = 44.0                        # 45°-Unterseite beginnt an der Wand hier (über dem Pi, unter dem Deckel)
PI_CAM1_XY = (123.25, 11.0)          # NACHMESSEN: Lage der Buchse CAM/DISP 1 am Pi 5 im Modell (geschätzt)
PI_CAM0_XY = (126.25, 11.0)          # NACHMESSEN: Lage der Buchse CAM/DISP 0 am Pi 5 im Modell (geschätzt)
# --- Service-Fenster (01.11.2026, Entscheid Daniel): HDMI-Notfallfenster nach links bis über die USB-C-Buchse des Pi 5
#     verlängert (USB-C bei x = BAT_X0 + 1 + 11,2 = 85,2, z 42,7), ein Stopfen für beides (10_Stopfen_HDMI_USB_v52)
SVC_X0, SVC_X1 = 78.0, 120.0         # Fenster x (HDMI 0/1 bei x 100 / 113,5, USB-C bei 85,2 – NACHMESSEN: Lage am Pi 5)
# --- SD-Karte: die Karte steckt unter dem Pi mitten im Gehäuse (x 71–74, Akku darunter) – von aussen nicht erreichbar.
#     Darum: microSD-Verlängerung mit Einbau-Kartenhalter (kleine Platine mit 2 Löchern) innen an der Lüftungswand, Schlitz
#     in der Wand mit eigenem Stopfen (15_Stopfen_SD_v52). NACHMESSEN: Masse des Halters.
SD_X, SD_Z = 40.0, 57.0              # Schlitzmitte (über dem PCA9685, unter dem Deckelrand)
SD_W, SD_H = 14.0, 3.0               # Schlitz (microSD 11 × 0,8 + Griff)
SD_HOLES_DX, SD_HOLE_DZ = 18.0, 6.0  # NACHMESSEN: Lochabstand der Halter-Platine, Löcher 6 mm über der Schlitzmitte
SD_STAND = 3.0                       # Dome: Platine 3 mm vor der Wand (Kartenhalter ca. 2 mm hoch)
# --- Lampentreiber (unbekannt) und 2. Sicherung (B+ Akku) nahe beim Step-down (01.11.2026, Entscheid Daniel)
DRV_Y0, DRV_Y1, DRV_Z0, DRV_Z1 = 5.0, 35.0, 2.5, 22.5   # Feld 30 × 20 an der Stirnwand innen, unter dem Step-down
DRV_HOLES = [(8.5, 6.5), (31.5, 18.5)]   # PLATZHALTER: Löcher (y, z) M2,5 – nach dem Kauf des Treibers anpassen
DRV_STAND = 3.0
FUSE_X0, FUSE_Y = 28.0, 12.5             # Flachsicherungs-Halter (Inline, 5 A) liegt auf dem Boden, Achse entlang x
FUSE_L, FUSE_W, FUSE_H = 30.0, 13.0, 10.0   # NACHMESSEN: Körper des Halters (geschätzt)
# --- Reserve-Öffnung hinten (+x) in GX12-Grösse mit Nut, Regendach und Blindstopfen 17
RES_Y, RES_ZC, RES_D = 30.0, 50.0, 12.3   # zwischen den Tasten-Dächern, über dem Relais-Dach, unter dem Deckelrand
# --- Entwicklungs-Sockel 13 (statt UPS HAT (E) + Akkus im Akku-Zaun): Pi in gleicher Lage und Höhe
SOCK_T = 2.5                             # Wände / Rahmen
PI_HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]   # Pi 5: 58 × 49 mm, 3,5 mm vom Rand
SOCK_CLAMP = 0.6                         # Klemmrippe: so viel breiter als der Zaun innen (federt)
# --- 5-mm-LED (nur IR_TYP = "5mm")
IR_Y, IR_Z, IR_D = 26.0, 40.0, 5.2
IR_SLEEVE_END = 5.1                  # Hülse bis x = 5,1 -> LED-Spitze bündig mit der Aussenwand (LED 8,6 lang)
IR_SLEEVE_D = 9.0
# --- Status-LED auf dem Kopf (Kipp-Koordinaten)
SLED_X, SLED_Y = 3.0, 8.0
SLED_D = 5.2                         # Loch für 5-mm-LED, Kragen (Ø5,8) liegt innen am Dach
SLED_SOCK_D, SLED_SOCK_T = 14.4, 1.2 # Vertiefung für den Diffusor-Zapfen
DIFF_D, DIFF_H = 14.0, 7.5           # Diffusor Ø, Höhe über dem Dach (ohne Pupillenring)
# --- Tasten hinten (+x-Wand): (y, z), Lochdurchmesser, Dach
BTN = [(10.5, 33.0), (50.5, 33.0)]
BTN_D = 12.2
BTN_HOOD_L = 7.0                     # Dach/Wangen ragen 7 mm vor (Kappe ca. 3 mm -> 4 mm zurückversetzt)
BTN_ROOF_Z0 = 41.0                   # Dach-Unterseite an der Wand
BTN_DEPTH_MAX = 12.0                 # Einbautiefe innen (Vorgabe)
# --- Blindstopfen (PETG)
BLIND_TOL = 0.2                      # Spiel pro Seite Stopfen <-> Fenster
BLIND_NOSE = 0.5                     # Rastnasen-Höhe (Überdeckung hinter der Wand ca. 0,4 mm)
IR_PLUG_D = IR_D - 0.3               # Zapfen IR-Stopfen (Ø4,9 in Ø5,2)

# ======================= Weitwinkel: Rahmen =============================
_t = math.radians(WC_TILT)
WA = np.array([-math.cos(_t), 0.0, -math.sin(_t)])     # Blickrichtung (nach aussen, unten)
WH = np.array([0.0, 1.0, 0.0])                          # Bild-waagrecht
WU = np.array([-math.sin(_t), 0.0, math.cos(_t)])       # Bild-oben
WL = np.array(WC_LENS, float)
WB = WL - WC_LENS_H * WA                                # Mitte Platinen-Vorderseite
WM = np.column_stack([-WA, WH, WU])                     # lokal (s nach innen, t, v) -> Welt


def wc_local(node):
    """Lokale Kamera-Koordinaten (s: von der Platinen-Vorderseite nach innen, t: y, v: Bild-oben) -> Welt."""
    return T(WB, RM(WM, node))


def wc_hole_world(dy, dv):
    return WB + dy * WH + dv * WU


def wc_window(off=0.0):
    """Sichtfeld-Pyramide (Fenster) im Wandbereich; off > 0 verkleinert (für den Stopfen)."""
    Lp = WL - WC_BACK * WA
    tH, tV = math.tan(math.radians(WC_FOV_H)), math.tan(math.radians(WC_FOV_V))
    pl = []
    for sh in (-1, 1):                                  # sh*(P-Lp).h - tH*(P-Lp).a <= r0
        n = sh * WH - tH * WA; pl.append(Plane(n, WC_R0 + n @ Lp - off * np.linalg.norm(n)))
    for sv in (-1, 1):
        n = sv * WU - tV * WA; pl.append(Plane(n, WC_R0 + n @ Lp - off * np.linalg.norm(n)))
    n = WA.copy(); pl.append(Plane(-n, -(n @ Lp)))     # nur vor dem Startquerschnitt
    return pl, tH, tV, Lp


def _win_corners(X):
    pl, tH, tV, Lp = wc_window()
    out = []
    for sh in (-1, 1):
        for sv in (-1, 1):
            Q = Lp + sh * WC_R0 * WH + sv * WC_R0 * WU
            c = WA + sh * tH * WH + sv * tV * WU
            out.append(Q + (X - Q[0]) / c[0] * c)
    return np.array(out)


_co, _ci = _win_corners(-WALL), _win_corners(0.0)
WIN_TOP = _co[:, 2].max()                       # Fensteroberkante aussen (flache Decke = Brücke)
WIN_TOP_Y = (_co[_co[:, 2] > WIN_TOP - 1e-6][:, 1].min(), _co[_co[:, 2] > WIN_TOP - 1e-6][:, 1].max())
WIN_BOT_IN = _ci[:, 2].min()                    # Unterkante innen (engste Stelle unten)
WIN_Y = (_co[:, 1].min(), _co[:, 1].max())
WIN_Z = (_co[:, 2].min(), WIN_TOP)
VIS_Z0 = WIN_TOP + 1.2                          # Regendach-Unterseite an der Wand


def wc_window_cut(off=0.0, x0=-WALL - 1.5, x1=0.3):   # x1 im Innenraum (nur Luft, schneidet keine Rippe)
    """Fenster = Sichtfeld-Pyramide + flache Decke (Brücke statt schräger Überhang)."""
    pl, *_ = wc_window(off)
    pyr = I(box(x0, x1, WIN_Y[0] - 5, WIN_Y[1] + 5, WIN_Z[0] - 5, WIN_TOP + 5), *pl)
    top = box(x0, x1, WIN_TOP_Y[0] + off, WIN_TOP_Y[1] - off, (WIN_TOP + WIN_BOT_IN) / 2, WIN_TOP - off)
    return U(pyr, top)


def wc_mount():
    """4 Halter (2 Rippen mit 45°-Unterseite) + Auflagepolster, stützenfrei druckbar."""
    add = []
    for dy in (-10.5, 10.5):
        top = wc_hole_world(dy, 7.5); bot = wc_hole_world(dy, -5.0)
        y0, y1 = AY + dy - WC_RIB_W / 2, AY + dy + WC_RIB_W / 2
        z0 = (bot[2] - 3.5) - bot[0]                    # 45°-Unterseite: z >= z0 + x (01.11.: 1 mm länger, Polster liegt ganz auf)
        z1 = top[2] + 3.5
        end = Plane(-WA, (-WA) @ WB - WC_PAD)          # endet WC_PAD vor der Platine
        add.append(I(bracket(-0.5, bot[0] + 3, y0, y1, z0, z1, "x", 0.0), end))
    for dy, dv in WC_HOLES:
        add.append(wc_local(cyl_x(dy, dv, -WC_PAD, 0.0, WC_PAD_D)))   # lokales x = s
    lim = box(-10, 40, 0, LY, -1, TOPZ - 0.2)                          # nicht über den Wannenrand (Deckel liegt auf)
    return [I(a, lim) for a in add]


def wc_mount_cuts():
    return [wc_local(cyl_x(dy, dv, -6.5, 0.5, WC_PILOT)) for dy, dv in WC_HOLES]


def wc_visor():
    w0 = -WALL
    return bracket(w0 - WC_VIS_L, w0 + 0.5, WIN_Y[0] - 2.0, WIN_Y[1] + 2.0, VIS_Z0, TOPZ, "-x", w0)


# ======================= IR-LED und Tasten ==============================
def ir_sleeve():
    z0 = 31.0                                            # Unterseite: z >= 31 + x (über dem Wandler, 45°)
    r = IR_SLEEVE_D / 2
    blk = U(cyl_x(IR_Y, IR_Z, -0.5, IR_SLEEVE_END, IR_SLEEVE_D), box(-0.5, IR_SLEEVE_END, IR_Y - r, IR_Y + r, z0, IR_Z))
    return I(blk, Plane([1, 0, -1], -z0))


def btn_hoods():
    xo = LX + WALL
    L = BTN_HOOD_L
    z1 = BTN_ROOF_Z0 + L + 1.0
    add = []
    # Taste 1 (y 10,5): Wange links neu, rechts Verlängerung der Relais-Wange (y 18..20)
    add.append(bracket(xo - 0.5, xo + L, 1.5, 3.0, 24.0, z1, "x", xo))
    add.append(bracket(xo - 0.5, xo + L, 18.0, 20.0, 25.0, z1, "x", xo))
    add.append(bracket(xo - 0.5, xo + L, 1.5, 20.0, BTN_ROOF_Z0, z1, "x", xo))
    # Taste 2 (y 50,5): links Verlängerung der Relais-Wange (y 40..42), rechts GX16-Wange (y 59..61, vorhanden)
    add.append(bracket(xo - 0.5, xo + L, 40.0, 42.0, 25.0, z1, "x", xo))
    add.append(bracket(xo - 0.5, xo + L, 40.0, 61.0, BTN_ROOF_Z0, z1, "x", xo))
    return add


# ======================= IR-MODUL 120°, TRENNSTEG, KABELFÜHRUNG (01.11.2026) ==========
def teardrop_x(y, z, x0, x1, d):
    """Waagrechter Zylinder entlang x mit 45°-Spitze oben (Loch ohne Stützen druckbar)."""
    r = d / 2
    tip = T([0, y, z], R([45, 0, 0], box(x0, x1, -r, r, -r, r)))
    return U(cyl_x(y, z, x0, x1, d), I(tip, box(x0, x1, y - r, y + r, z, z + r * 1.42)))


IRW_BORE = IRW_MOD_D + IRW_TOL
IRW_OD = IRW_BORE + 2 * IRW_SLEEVE_T


def irw_sleeve():
    """Hülse für das IR-Modul: innen an der Stirnwand, Bohrung mit 45°-Spitze, darunter 45°-Stütze zur Wand."""
    ro = IRW_OD / 2
    L = IRW_SLEEVE_L
    z0 = IRW_Z - ro - L                                   # Stütze: z >= z0 + x (endet unter der Hülse)
    blk = U(teardrop_x(IRW_Y, IRW_Z, -0.5, L, IRW_OD), box(-0.5, L, IRW_Y - ro, IRW_Y + ro, z0, IRW_Z))
    return I(blk, Plane([1, 0, -1], -z0))


def irw_cuts():
    w0 = -WALL
    c = IRW_CHAMFER
    return [teardrop_x(IRW_Y, IRW_Z, 0.0, IRW_SLEEVE_L + 1, IRW_BORE),            # Modul (von innen eingeschoben)
            cyl_x(IRW_Y, IRW_Z, w0 - 1, 0.5, IRW_LENS_D),                         # Linse (Modul liegt am Lochrand an)
            T([w0 - 0.01, IRW_Y, IRW_Z], R([0, 90, 0], Cyl(max(c, 0.01), r1=IRW_LENS_D / 2 + c, r2=IRW_LENS_D / 2))),   # Fase 45° (0 = keine)
            cyl_z(IRW_SLEEVE_L / 2, IRW_Y, IRW_Z, IRW_Z + IRW_OD, 2.6)]            # Madenschraube M3 oben


def trennsteg():
    """Steg aussen zwischen IR-Modul und Kamera-Fenster (45°-Unterseite, bis unter das Regendach)."""
    w0 = -WALL
    z0 = IRW_Z - IRW_LENS_D / 2 - 2.0
    fin = bracket(w0 - TRENN_L, w0 + 0.5, TRENN_Y, TRENN_Y + TRENN_T, z0, VIS_Z0, "-x", w0)
    fin = I(fin, box(w0 - TRENN_L - 1, w0 + 1, TRENN_Y - 1, TRENN_Y + TRENN_T + 1, z0 + 1.6, VIS_Z0 + 1))   # keine Messerkante unten
    return fin


def fpc_guide():
    """Kamm an der Lüftungswand (-y) für die Flachkabel CAM1 (Schlitz 1) und CAM0 (Schlitz 2): 3 Rippen, 45°-Unterseite,
    Kabel stehen senkrecht über den Buchsen und werden von oben eingelegt (der Deckel hält sie)."""
    out = []
    for i in range(3):
        x0 = FPC_X0 + i * (FPC_FIN + FPC_SLOT)
        out.append(bracket(x0, x0 + FPC_FIN, -0.5, FPC_DEPTH, FPC_Z0, TOPZ - 0.5, "y", 0.0))
    return out


def svc_cut():
    hz = v5.PI_Z + 4
    w = SVC_X1 - SVC_X0
    return T([(SVC_X0 + SVC_X1) / 2, -WALL / 2, hz - v5.HDMI_H / 2], RBox(w, WALL + 2, v5.HDMI_H, 2))


def part_service_plug():
    """Stopfen für das Service-Fenster (HDMI + USB-C), wie der HDMI-Stopfen v5.1, nur länger. Druck: Flansch unten."""
    W, H, tol = SVC_X1 - SVC_X0, v5.HDMI_H, 0.2                  # Spiel 0,2 (v5.1: 0,3 = kein Halt)
    core = RBox(W - 2 * tol, H - 2 * tol, 1.5 + WALL - 0.3, 2 - tol)
    flange = RBox(W + 6, H + 6, 1.5, 3)
    grip = box(-6, 6, -(H + 6) / 2 - 4, -(H + 6) / 2 + 0.5, 0, 1.5)
    return D(U(flange, core, grip), T([0, 0, 1.5], RBox(W - 2 * tol - 3, H - 2 * tol - 3, 5, 1)))


def sd_mount():
    out = []
    for dx in (-SD_HOLES_DX / 2, SD_HOLES_DX / 2):
        out.append(v5.teardrop_y(SD_X + dx, SD_Z + SD_HOLE_DZ, -0.5, SD_STAND, 5.5))
    return out


def sd_cuts():
    out = [T([SD_X, -WALL / 2, SD_Z - SD_H / 2], RBox(SD_W, WALL + 2, SD_H, 0.8))]
    for dx in (-SD_HOLES_DX / 2, SD_HOLES_DX / 2):
        out.append(cyl_y(SD_X + dx, SD_Z + SD_HOLE_DZ, -0.2, SD_STAND + 1, 2.2))       # M2,5 selbstschneidend
    return out


def part_sd_plug():
    """Stopfen für den SD-Schlitz: Flansch 1,2 + Kern im Schlitz (Spiel 0,15) + Griffnase. Druck: Flansch unten."""
    tol = 0.15
    core = RBox(SD_W - 2 * tol, SD_H - 2 * tol, 1.6 + WALL - 0.3, 0.6)
    flange = RBox(SD_W + 6, SD_H + 6, 1.6, 2)
    grip = box(-3, 3, -(SD_H + 6) / 2 - 3, -(SD_H + 6) / 2 + 0.5, 0, 1.6)
    return U(flange, core, grip)


def teardrop_x_down(y, z, x0, x1, d):
    """Dom entlang x an einer senkrechten Wand mit 45°-Spitze unten (ohne Stützen)"""
    r = d / 2
    tip = T([0, y, z], R([45, 0, 0], box(x0, x1, -r, r, -r, r)))
    return U(cyl_x(y, z, x0, x1, d), I(tip, box(x0, x1, y - r, y + r, z - r * 1.42, z)))


def drv_mount():
    return [teardrop_x_down(y, z, -0.5, DRV_STAND, 5.5) for y, z in DRV_HOLES]


def drv_cuts():
    return [cyl_x(y, z, -0.2, DRV_STAND + 1, 2.2) for y, z in DRV_HOLES]


def fuse_clip():
    """2 Klammern auf dem Boden für den Sicherungshalter: je 2 Stege mit Rastnase oben (eindrücken, ohne Werkzeug lösbar)"""
    out = []
    w = FUSE_W + 0.4
    for x in (FUSE_X0 + 5.0, FUSE_X0 + FUSE_L - 9.0):
        for sgn in (-1, 1):
            y0 = FUSE_Y + sgn * w / 2
            out.append(box(x, x + 4.0, min(y0, y0 + sgn * 1.6), max(y0, y0 + sgn * 1.6), ZF - 0.5, ZF + FUSE_H * 0.7 + 1.0))
            nose = I(box(x, x + 4.0, min(y0, y0 - sgn * 0.8), max(y0, y0 - sgn * 0.8), ZF + FUSE_H * 0.7, ZF + FUSE_H * 0.7 + 1.0),
                     Plane([0, -sgn, -1], -sgn * y0 - (ZF + FUSE_H * 0.7)))   # 45° Rastschräge unten
            out.append(nose)
    return out


def res_add():
    xo = LX + WALL
    add = [bracket(xo - 0.5, xo + 8, RES_Y - 12, RES_Y + 12, RES_ZC + 9, RES_ZC + 17, "x", xo)]
    for yy in (RES_Y - 12, RES_Y + 10):
        add.append(bracket(xo - 0.5, xo + 8, yy, yy + 2, RES_ZC - 14, RES_ZC + 17, "x", xo))
    return add


def res_cuts():
    return [cyl_x(RES_Y, RES_ZC, LX - 1, LX + WALL + 1, RES_D),
            box(LX - 1, LX + WALL + 1, RES_Y - 1, RES_Y + 1, RES_ZC + 5.5, RES_ZC + 7.2)]    # Nut gegen Verdrehen


def part_res_plug():
    """17 Blindstopfen Reserve: Zapfen Ø RES_D - 0,3 mit Nase in der Nut, Flansch Ø 18. Druck: Flansch unten."""
    rp = (RES_D - 0.3) / 2
    L = WALL + 1.0
    F = 1.6                                                                       # Flansch und Wand >= 1,5 mm
    body = U(cyl_z(0, 0, 0, F, 18.0), cyl_z(0, 0, F, F + L, 2 * rp),
             box(rp - 0.2, rp + 1.0, -0.85, 0.85, F, F + L))                       # Nase in die Nut (eingebaut oben)
    return D(body, cyl_z(0, 0, F + 0.6, F + L + 1, 2 * rp - 3.2))                 # hohl (spart Material)


def part_sockel():
    """13 Entwicklungs-Sockel: steht im Akku-Zaun statt UPS HAT + Akkus; der Pi sitzt in gleicher Lage und Höhe auf 4 Bolzen
    M2,5. Rahmen + 2 Wände mit Fenstern (Kabel), Klemmrippen gegen den Zaun. Koordinaten wie das Unterteil."""
    x0, x1 = v5.BAT_X0 + 0.2, v5.BAT_X0 + v5.BAT_L - 0.2           # 0,2 + 0,5 Zaun-Spiel = ca. 0,7 mm pro Seite
    y0, y1 = 0.6, v5.BAT_W - 0.2
    zb, zt = ZF, v5.PI_Z                                              # Unterseite / Pi-Unterseite
    t = SOCK_T
    px = v5.BAT_X0 + 1
    hx = [px + a for a, b in PI_HOLES]; hy = [3.0 + b for a, b in PI_HOLES]
    frame = D(box(x0, x1, y0, y1, zb, zb + 4.0), box(x0 + t, x1 - t, y0 + t, y1 - t, zb - 1, zb + 5))
    walls = []
    for x in sorted(set(hx)):                                         # 2 Wände quer (y) unter den Bolzen-Reihen
        walls.append(box(x - t / 2, x + t / 2, y0, hy[-1] + 3.5, zb, zt - 3.0))
    beams = [box(x0, x1, y, y + t, zb, zb + 4.0) for y in (hy[0] - t / 2, hy[-1] - t / 2)]
    posts = [cyl_z(x, y, zb, zt, 7.0) for x, y in zip(hx, hy)]
    clamps = []                                                       # Klemmrippen aussen an den Stirnseiten
    for xc, sgn in ((x0, -1), (x1, 1)):
        for yc in (20.0, 60.0):
            clamps.append(box(min(xc, xc + sgn * (0.7 + SOCK_CLAMP)), max(xc, xc + sgn * (0.7 + SOCK_CLAMP)), yc - 2.0, yc + 2.0, zb, zb + 3.5))
    body = U(frame, *walls, *beams, *posts, *clamps)
    cut = [cyl_z(x, y, zt - 8.0, zt + 1, 2.2) for x, y in zip(hx, hy)]  # M2,5 selbstschneidend, 8 tief
    for x in sorted(set(hx)):                                         # Fenster in den Wänden: Kabel, Material (Brücke 8 mm)
        for yc in np.arange(hy[0] + 12.0, hy[-1] - 11.0, 11.0):      # nicht in die Bolzen schneiden
            cut.append(box(x - 2, x + 2, yc - 4.0, yc + 4.0, zb + 6.0, zt - 8.0))
    return D(body, *cut)


def fpc_slots():
    return [FPC_X0 + FPC_FIN + FPC_SLOT / 2 + i * (FPC_FIN + FPC_SLOT) for i in range(2)]   # x Mitte Schlitz 1 / 2


# ======================= UNTERTEIL v5.2 =================================
def part_tub():
    add = [*wc_mount(), wc_visor(), *btn_hoods()]
    cut = [wc_window_cut()] + wc_mount_cuts()
    if IR_TYP == "5mm":
        add.append(ir_sleeve())
        cut.append(cyl_x(IR_Y, IR_Z, -WALL - 1, IR_SLEEVE_END + 1, IR_D))
    else:
        add += [irw_sleeve(), trennsteg()]
        cut += irw_cuts()
    add += fpc_guide() + sd_mount() + drv_mount() + fuse_clip() + res_add()
    cut += [svc_cut()] + sd_cuts() + drv_cuts() + res_cuts()
    body = U(v5.part_tub(), *add)
    for y, z in BTN:
        cut.append(cyl_x(y, z, LX - 1, LX + WALL + 1, BTN_D))
    return D(body, *cut)


# ======================= KOPF v5.2 (Status-LED) =========================
def part_head():
    top = pt.HH / 2
    cut = [cyl_z(SLED_X, SLED_Y, top - SLED_SOCK_T, top + 1, SLED_SOCK_D),
           cyl_z(SLED_X, SLED_Y, top - pt.SHELL_T - 1, top + 1, SLED_D)]
    return D(pt.part_head(), *cut)


# ======================= NEUE KLEINTEILE ================================
def part_diffuser():
    """Diffusor «Blinki-Auge»: runde Kuppel Ø14, Zapfen 1,2 mm in die Dach-Vertiefung (Presssitz mit 6 Rippen).
    z = 0 = Dachoberfläche. Druck: Zapfen unten, ohne Stützen. Transparent/weiss (PETG natur)."""
    R = DIFF_D / 2; f = 3.5                              # Rundung oben
    zb = -SLED_SOCK_T + 0.1
    body = U(cyl_z(0, 0, zb, DIFF_H - f, DIFF_D), cyl_z(0, 0, DIFF_H - f, DIFF_H, 2 * (R - f)),
             T([0, 0, DIFF_H - f], Torus(R - f, f)))
    body = I(body, box(-R - 1, R + 1, -R - 1, R + 1, zb, DIFF_H))
    ribs = [T([0, 0, zb], R_([0, 0, a], box(R - 0.3, (SLED_SOCK_D / 2) + 0.1, -0.3, 0.3, 0, -zb - 0.1))) for a in range(0, 360, 60)]
    body = U(body, *ribs)
    cut = [cyl_z(0, 0, zb - 1, 3.6, 5.6), T([0, 0, 3.6], Cyl(2.8, r1=2.8, r2=0.01)),     # LED-Raum, Kegel 45°
           cyl_z(0, 0, DIFF_H - 0.6, DIFF_H + 1, 6.4)]                                   # Vertiefung Pupillenring
    return D(body, *cut)


def part_pupil():
    """Pupillenring (dunkles PETG): Ø6,0 / Ø2,6, 0,9 dick; wird in die Kuppel gedrückt/geklebt, steht 0,3 mm vor."""
    return D(cyl_z(0, 0, 0, 0.9, 6.0), cyl_z(0, 0, -1, 2, 2.6))


R_ = R


def blind_wide():
    """Blindstopfen für das Weitwinkel-Fenster (Welt-Koordinaten, eingesetzt). Flansch aussen, Kern im Fenster,
    zwei Rastzungen (oben/unten) greifen hinter die Wand-Innenseite (45°-Rastfläche: ohne Werkzeug abziehbar)."""
    tol = BLIND_TOL
    w0 = -WALL
    core = I(wc_window_cut(off=tol, x0=w0, x1=0.0), box(w0, 0.0, -100, 200, -100, 200))
    fy0, fy1 = WIN_Y[0] - 2.0, WIN_Y[1] + 2.0
    fz0, fz1 = WIN_Z[0] - 2.0, WIN_TOP + 1.8
    fl_out = (rx_box(w0 - 1.2, w0 - 0.6, fy1 - fy0, fz1 - fz0, 2.5, y=(fy0 + fy1) / 2, z=(fz0 + fz1) / 2))
    fl_in = rx_box(w0 - 0.6, w0 + 0.01, fy1 - fy0 - 1.6, fz1 - fz0 - 1.6, 1.8, y=(fy0 + fy1) / 2, z=(fz0 + fz1) / 2)
    tw, tt, tl = 8.0, 0.8, 1.8                          # Zungenbreite, -dicke, Länge hinter der Wand
    yc = AY
    # Zunge oben (an der flachen Decke) und unten (über der schrägen Fensterunterkante)
    zt1 = WIN_TOP - tol / 2; zt0 = zt1 - tt
    zb0 = WIN_BOT_IN + tol / 2; zb1 = zb0 + tt
    slot = 0.8
    core = D(core, box(w0 - 1, 0.5, yc - tw / 2 - slot, yc + tw / 2 + slot, zt0 - slot, 200),
             box(w0 - 1, 0.5, yc - tw / 2 - slot, yc + tw / 2 + slot, -100, zb1 + slot))
    tong = [box(w0 - 0.6, tl, yc - tw / 2, yc + tw / 2, zt0, zt1), box(w0 - 0.6, tl, yc - tw / 2, yc + tw / 2, zb0, zb1)]
    bh = BLIND_NOSE; xc = 0.1                                    # Nasenhöhe, Rastkante 0,1 hinter der Wand
    def bump(sgn, zf):                                    # sgn +1: nach +z (oben), -1: nach -z (unten)
        b = box(xc - 0.3, tl, yc - tw / 2 + 0.5, yc + tw / 2 - 0.5, zf - sgn * 0.15, zf + sgn * bh)   # 0,15 in die Zunge
        # Rastfläche 45°: sgn*(z - zf) <= x - xc ; Einführschräge: sgn*(z - zf) <= (tl - x) * bh / (tl - xc - 0.7)
        k = bh / (tl - xc - 0.7)
        return I(b, Plane([-1, 0, sgn], sgn * zf - xc), Plane([k, 0, sgn], sgn * zf + k * tl))
    return U(fl_out, fl_in, core, *tong, bump(+1, zt1), bump(-1, zb0))


def blind_ir():
    """Stopfen für das IR-LED-Loch (lokal, Druckrichtung z): Flansch Ø9, geschlitzter Zapfen mit Rastnasen,
    die hinter dem Hülsenende (x = 5,1) einrasten."""
    L = WALL + IR_SLEEVE_END                              # 7,6 Bohrungslänge
    rp = IR_PLUG_D / 2                                    # Zapfen Ø4,9
    fl = U(cyl_z(0, 0, 0, 0.6, 9.0), cyl_z(0, 0, 0.6, 1.0, 8.0))
    z0 = 1.0; zc = z0 + L + 0.15
    pin = cyl_z(0, 0, z0 - 0.1, zc, 2 * rp)
    nose = U(T([0, 0, zc], Cyl(0.4, r1=rp, r2=rp + 0.4)), cyl_z(0, 0, zc + 0.4, zc + 0.6, 2 * (rp + 0.4)),
             T([0, 0, zc + 0.6], Cyl(1.0, r1=rp + 0.4, r2=rp - 0.3)))
    return D(U(fl, pin, nose), box(-0.6, 0.6, -5, 5, 2.2, 20))



# ======================= DUMMIES / ZUSAMMENBAU ==========================
def wc_dummy():
    bw, bh, bt = WC_BOARD
    vt = WC_LENS_FROM_TOP
    board = box(0, bt, -bw / 2, bw / 2, vt - bh, vt)
    block = box(-5.0, 0, -4.25, 4.25, -4.25, 4.25)
    barrel = cyl_x(0, 0, -WC_LENS_H, -5.0, 8.0)
    conn = box(bt, bt + 2.5, -11, 11, vt - bh, vt - bh + 6)
    return wc_local(U(board, block, barrel, conn))


def ir_module_dummy():
    """IR-Modul 120°: Linse vorne im Wandloch, Körper in der Hülse, Kabel hinten"""
    x1 = IRW_MOD_L
    return U(cyl_x(IRW_Y, IRW_Z, -1.5, 0.0, IRW_LENS_D - 0.4), cyl_x(IRW_Y, IRW_Z, 0.0, x1, IRW_MOD_D),
             box(x1, x1 + 6, IRW_Y - 1.5, IRW_Y + 1.5, IRW_Z - 0.6, IRW_Z + 0.6))


def kabel(pts, w=1.0):
    """Flachkabel als Kette dünner Quader-Stäbe (nur Modell / Simulator; Kabel sind biegsam)"""
    from csg import RM as _RM
    segs = []
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = np.array(a, float), np.array(b, float)
        d = b - a; L = float(np.linalg.norm(d)); e3 = d / L
        e1 = np.cross(e3, [0, 0, 1.0] if abs(e3[2]) < 0.9 else [1.0, 0, 0]); e1 /= np.linalg.norm(e1)
        e2 = np.cross(e3, e1)
        segs.append(T(a, _RM(np.column_stack([e1, e2, e3]), Cyl(L, d=w * 3.0, fn=6))))
    return U(*segs)


def cable_cam1_pts():
    """CAM1: Stecker unten hinten an der Weitwinkel-Kamera -> über den PIR -> unter dem Pan-Servo -> über den Pi zur
    Lüftungswand -> Kamm (Schlitz 1) -> Buchse CAM/DISP 1. Lüfter (Active Cooler) und Lüftungsschlitze bleiben frei."""
    bot = WB - 14.5 * WU - 2.5 * WA                       # Rückseite der Platine unten (Stecker)
    sx = fpc_slots()[0]
    cx, cy = PI_CAM1_XY
    return [tuple(bot), (bot[0] + 2.0, AY, bot[2] - 2.0), (30.0, 42.0, 44.0), (72.0, 42.0, 45.5), (92.0, 10.0, 56.0),
            (sx - 3.0, 7.5, 60.0), (sx, 7.5, 58.0), (sx, 7.5, 50.0), (cx, cy, 46.0), (cx, cy, v5.PI_Z + 3.0)]


def cable_cam0_pts():
    """CAM0 (Kopfkamera) in v5.2: Kabelkamin -> vor dem Lüfter entlang -> Kamm (Schlitz 2) -> Buchse CAM/DISP 0"""
    sx = fpc_slots()[1]
    cx, cy = PI_CAM0_XY
    return [(v5.CHIM_X, AY, v5.TOPZ + 1.0), (v5.CHIM_X, AY, TOPZ - 6.0), (97.0, 12.0, TOPZ - 6.0), (sx - 3.0, 9.5, 61.0),
            (sx, 9.5, 58.0), (sx, 9.5, 50.0), (cx, cy, 46.0), (cx, cy, v5.PI_Z + 3.0)]


def ir_led_dummy():
    if IR_TYP != "5mm":
        return ir_module_dummy()
    return U(cyl_x(IR_Y, IR_Z, -WALL, IR_SLEEVE_END, 5.0), cyl_x(IR_Y, IR_Z, IR_SLEEVE_END, IR_SLEEVE_END + 1.0, 5.8),
             box(IR_SLEEVE_END + 1, IR_SLEEVE_END + 12, IR_Y - 1.5, IR_Y + 1.5, IR_Z - 0.3, IR_Z + 0.3))


def btn_dummy():
    xo = LX + WALL
    out = []
    for y, z in BTN:
        out += [cyl_x(y, z, LX - BTN_DEPTH_MAX, LX, 12.0), cyl_x(y, z, LX - 3.0, LX, 16.0),
                cyl_x(y, z, LX - 1, xo + 0.5, 11.9), cyl_x(y, z, xo, xo + 2.0, 14.0), cyl_x(y, z, xo + 2.0, xo + 3.0, 10.0)]
    return U(*out)


def sled_dummy():
    top = pt.HH / 2
    led = U(cyl_z(SLED_X, SLED_Y, top - pt.SHELL_T - 1.0, top - pt.SHELL_T, 5.8),
            cyl_z(SLED_X, SLED_Y, top - pt.SHELL_T, top - pt.SHELL_T + 5.1, 5.0))
    return led


def diffuser_placed():
    return T([SLED_X, SLED_Y, pt.HH / 2], U(part_diffuser(), T([0, 0, DIFF_H - 0.6], part_pupil())))


def placed(tilt=0.0, pan=180.0, blinds=False):
    P = v5.placed(tilt, pan)

    def pan_frame(n):
        return T([AX, AY, v5.PAN_Z0], R([0, 0, pan], n))

    def tilt_frame(n):
        return pan_frame(T([0, 0, pt.AXZ], R([0, tilt, 0], n)))
    P["tub"] = part_tub()
    P["head"] = tilt_frame(part_head())
    P["sled"] = tilt_frame(sled_dummy())
    P["diff"] = tilt_frame(diffuser_placed())
    P["wcam"] = wc_dummy()
    P["irled"] = ir_led_dummy()
    P["btn"] = btn_dummy()
    P["mosfet"] = box(10.0, 38.0, 0.5, 2.1, ZF + 0.5, ZF + 20.5)      # neu: -y-Wand unter dem PCA9685
    P["plug"] = T([(SVC_X0 + SVC_X1) / 2, -WALL - 1.5, v5.PI_Z + 4], R([-90, 0, 0], part_service_plug()))
    P["sdplug"] = T([SD_X, -WALL - 1.6, SD_Z], R([-90, 0, 0], part_sd_plug()))
    P["sdext"] = box(SD_X - 11, SD_X + 11, SD_STAND, SD_STAND + 1.6, SD_Z - 5, SD_Z + 10)    # Halter-Platine (Annahme 22 × 15)
    P["lampdrv"] = box(DRV_STAND, DRV_STAND + 1.6, DRV_Y0, DRV_Y1, DRV_Z0, DRV_Z1)        # PLATZHALTER Lampentreiber
    P["fuseh"] = box(FUSE_X0, FUSE_X0 + FUSE_L, FUSE_Y - FUSE_W / 2, FUSE_Y + FUSE_W / 2, ZF, ZF + FUSE_H)
    P["resplug"] = T([LX + WALL + 1.6, RES_Y, RES_ZC], R([0, -90, 0], part_res_plug()))
    P["sockel"] = part_sockel()
    P["resjack"] = cyl_x(RES_Y, RES_ZC, LX - 13, LX + WALL + 6, 12)                          # GX12-Buchse (falls belegt)
    P["cam1"] = kabel(cable_cam1_pts())
    P["cam0"] = kabel(cable_cam0_pts())
    if blinds:
        P["blind_w"] = blind_wide()
        P["blind_ir"] = T([-WALL - 1.0, IR_Y, IR_Z], R([0, 90, 0], blind_ir()))
    return P


if __name__ == "__main__":
    np.set_printoptions(precision=2, suppress=True)
    print("Platinen-Mitte vorne:", WB, " Linse:", WL)
    for dy, dv in WC_HOLES:
        print("  Loch", dy, dv, "->", wc_hole_world(dy, dv))
    print("  Platine oben:", WB + 9.5 * WU, " unten:", WB - 14.5 * WU, " Rückseite oben:", WB + 9.5 * WU - 1.0 * WA)
    print("Fenster aussen y %.1f..%.1f  z %.1f..%.1f  (Decke flach bei %.1f, Breite oben %.1f..%.1f)" % (*WIN_Y, *WIN_Z, WIN_TOP, *WIN_TOP_Y))
    print("Fenster innen:", _ci[:, 1].min().round(1), _ci[:, 1].max().round(1), _ci[:, 2].min().round(1), _ci[:, 2].max().round(1))
    print("IR:", IR_TYP, " Modul y/z", IRW_Y, IRW_Z, " Hülse Ø", IRW_OD, " Loch Ø", IRW_LENS_D, " Kamm-Schlitze x", fpc_slots())
    print("Regendach z0:", round(VIS_Z0, 2), " bis", TOPZ, " Tiefe", WC_VIS_L, " Spitze", round(TOPZ - VIS_Z0 - WC_VIS_L, 2))
