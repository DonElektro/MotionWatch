"""v5.3: Kollisionen der neuen und geänderten Teile (Akkuklappe, Luftkanal, Halter, Ösen, Einsätze, Füsse) über die
verlangten Kopf-Stellungen, Mindestwände an den Einsätzen und Abstände der neu verlegten Kamerakabel.
python3 check53.py [statisch] [kopf] [einsatz] [abstand] [klappe]   (ohne Angabe: alles)"""
import sys, time, numpy as np
import v5, v52, v53, csg
from check52 import coll, TILTS, PANS
h = 0.4

STATIC = [("hatch", k) for k in ("tub", "ups", "feet", "probe", "speaker", "tripod_dummy", "sockel")] + \
         [("duct", k) for k in ("tub", "lid", "pi", "cooler", "cam0", "cam1", "sdext", "servo1", "shelf", "charger", "pam", "plug", "ups",
                                 "irled", "wcam", "pca", "mosfet", "soundcard", "hub", "relay")] + \
         [("holder", k) for k in ("tub", "feet", "hatch", "speaker", "probe", "lid", "jacks", "relayjack", "btn", "resjack", "tscrew_head")] + \
         [("tub", k) for k in ("ups", "pi", "cooler", "pca", "speaker", "charger", "pam", "soundcard", "mic", "pir", "jacks", "plug", "servo1",
                                "shelf", "feet", "lid", "hub", "relay", "mosfet", "buck", "relayjack", "probe", "ina", "wcam", "irled", "btn",
                                "sdext", "sdplug", "fuseh", "lampdrv", "resjack", "resplug", "sockel")] + \
         [("lid", k) for k in ("servo1", "pi", "cooler", "jacks", "soundcard", "charger", "wcam", "btn", "cam0", "cam1")]
KOPF = [(k, "lid") for k in ("lamp1", "lamp2", "yoke", "arm2", "head", "turntable", "diff", "side")]


def scene(halter=True):
    P = v53.placed(0, 180, halter=halter)
    P["tripod_dummy"] = csg.cyl_z(*v5.TRIPOD_XY, v5.ZF + 0.3, v5.ZF + 5.8, 11.0, fn=6)
    zb = v53.HOLD_Z_TOP - v53.HOLD_T
    P["tscrew_head"] = csg.cyl_z(*v5.TRIPOD_XY, zb - 4.0, zb, 11.0)
    return P


def statisch():
    t0 = time.time()
    P = scene()
    out = [f"{a}/{b} {v:.2f}" for a, b in STATIC if a in P and b in P and (v := coll(P, a, b)) > 0]
    print("statisch:", ", ".join(out) or "frei", f"({time.time() - t0:.0f}s)", flush=True)


def kopf():
    t0 = time.time()
    for pan in PANS:
        for tilt in TILTS:
            P = v53.placed(tilt, pan)
            out = [f"{a}/{b} {v:.1f}" for a, b in KOPF if (v := coll(P, a, b)) > 0]
            print(f"tilt {tilt:4} pan {pan:4}:", ", ".join(out) or "frei", f"({time.time() - t0:.0f}s)", flush=True)


def einsatz():
    """Material rund um jede Einsatzbohrung: kleinster Abstand Bohrungsrand -> Aussenfläche (soll >= 1,6 mm, ruthex)"""
    tub = v53.part_tub()
    holes = [(x, y, v5.TOPZ - v53.INS_HOLE_L, v5.TOPZ, "Deckel") for x, y in v5.LID_SCREWS] + \
            [(x, y, v53.SB - v53.INS_HOLE_L, v53.SB, "Zwischenboden") for x, y in v53.SHELF_SCREWS] + \
            [(x, y, 0.0, v53.INS_HOLE_L, "Akkuklappe") for x, y in v53.HATCH_SCREWS]
    r = v53.INS_D / 2
    worst = 99
    for x, y, z0, z1, wo in holes:
        best = 99.0
        for zz in np.linspace(z0 + 0.3, z1 - 0.3, 8):
            for wall in np.arange(0.2, 4.01, 0.1):
                a = np.linspace(0, 2 * np.pi, 48, endpoint=False)
                P = np.column_stack([x + (r + wall) * np.cos(a), y + (r + wall) * np.sin(a), np.full(48, zz)])
                if (tub.sdf(P) > 0).any():
                    best = min(best, wall - 0.1)
                    break
        worst = min(worst, best)
        print(f"  Einsatz {wo:13s} ({x:5.1f}, {y:5.1f}): Wand {'≥ 4' if best > 4 else '%.1f' % best} mm" + ("  <-- zu dünn" if best < v53.INS_WALL_MIN else ""), flush=True)
    print(f"Einsätze: kleinste Wand {worst:.1f} mm (Soll ≥ {v53.INS_WALL_MIN})", flush=True)


def abstand():
    P = v53.placed(0, 180)
    def pts(seq, n=40):
        out = []
        for a, b in zip(seq[:-1], seq[1:]):
            for t in np.linspace(0, 1, n):
                out.append(np.array(a) * (1 - t) + np.array(b) * t)
        return np.array(out)
    louv = csg.box(v5.LOUV_X0, v5.LOUV_X1, -0.5, 1.0, v5.ZF + 40, v5.ZF + 56)
    for nm, X in (("CAM1", pts(v53.cable_cam1_pts())), ("CAM0", pts(v53.cable_cam0_pts()))):
        for on, node in (("Luftkanal", P["duct"]), ("Lüfter", P["cooler"]), ("Lüftungsschlitze", louv), ("Deckel", P["lid"])):
            print(f"  {nm} -> {on}: {node.sdf(X).min():.1f} mm (Mittellinie, Kabelmodell Ø 3)", flush=True)
    fx0, fx1, fy0, fy1 = v53.FAN_IN
    q = np.array([[x, y, v53.COOL_TOP + 0.5] for x in np.linspace(fx0, fx1, 12) for y in np.linspace(fy0, fy1, 12)])
    print(f"  Ansaugfläche unter der Haube: {'ja' if (P['duct'].sdf(q) > 0).all() else 'NEIN'}", flush=True)


def klappe():
    """Zellen von unten: jede Zelle passt ganz durch die Öffnung (Grundriss), Klappe deckt die Öffnung ≥ 1,5 mm"""
    for i in range(4):
        cx = v5.BAT_X0 + 12 + i * 22
        x0, x1 = cx - 10.75, cx + 10.75
        ok = x0 >= v53.OPEN_X0 and x1 <= v53.OPEN_X1
        print(f"  Zelle {i + 1}: x {x0:.1f}..{x1:.1f}, Länge 70 in y {v53.OPEN_Y0:.0f}..{v53.OPEN_Y1:.0f}: {'passt' if ok and v53.OPEN_Y1 - v53.OPEN_Y0 >= 70 else 'NEIN'}")
    o = min(v53.OPEN_X0 - v53.HATCH_X0, v53.HATCH_X1 - v53.OPEN_X1, v53.OPEN_Y0 - v53.HATCH_Y0, v53.HATCH_Y1 - v53.OPEN_Y1)
    print(f"  Klappe überdeckt die Öffnung um mindestens {o:.1f} mm")
    ho = v53.hatch_outline(0.0, -1, 0)
    for fx, fy in v53.FEET53:
        for gap in np.arange(0.0, 6.01, 0.25):               # kleinster Ring um den Fuss (Ø 14), der die Klappe berührt
            a = np.linspace(0, 2 * np.pi, 180, endpoint=False)
            Q = np.column_stack([fx + (7.0 + gap) * np.cos(a), fy + (7.0 + gap) * np.sin(a), np.full(180, -0.5)])
            if (ho.sdf(Q) < 0).any():
                break
        print(f"  Fuss ({fx:.0f}, {fy:.0f}) -> Klappe: {'> 6' if gap >= 6 else '%.2f' % gap} mm")


if __name__ == "__main__":
    what = sys.argv[1:] or ["klappe", "einsatz", "abstand", "statisch", "kopf"]
    for w in what:
        globals()[w]()
