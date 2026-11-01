"""v5.2: Kollisionen (wie check5.py, plus neue Teile) über alle verlangten Kopf-Stellungen
und Sichtfeld-Test der Weitwinkel-Kamera (Strahlen gegen alle festen und bewegten Teile).
python3 check52.py [koll] [fov] [wand] [abstand] [stopfen]   (ohne Angabe: alles; «statisch» = nur die festen Teile, schnell)
01.11.2026: IR-Modul 120°, Trennsteg, Kabelkamm; «wand» = Stegbreiten in der Stirnwand zwischen den Öffnungen,
«abstand» = Abstände der Kabelwege CAM0 / CAM1 und des IR-Moduls zu Lüfter, Lüftungsschlitzen und Lautsprecher.
01.11.2026 (Pakete): «stopfen» = die Stopfen 18–21, 23, 24 eingesetzt gegen Unterteil / Kopf / Nachbarn (Kopf über alle Stellungen)
und wie dicht sie die Öffnung schliessen (offene Fläche = Spalt rundum)."""
import sys, math, time, numpy as np
import v52, csg
h = 0.4
TILTS = [0, 40, -40, 70, -70]
PANS = [0, 90, 135, 180, 225, 270]
pairs = [("head", "yoke"), ("head", "arm2"), ("head", "horn2"), ("side", "arm2"), ("side", "yoke"), ("servo2", "yoke"), ("servo2", "arm2"),
         ("lamp1", "yoke"), ("lamp1", "arm2"), ("lamp2", "arm2"), ("lamp1", "head"), ("lamp2", "head"), ("lamp2", "side"), ("lamp1", "lid"), ("lamp2", "lid"),
         ("yoke", "lid"), ("arm2", "lid"), ("head", "lid"), ("turntable", "lid"), ("turntable", "balls"), ("yoke", "turntable"), ("arm2", "turntable"),
         ("lamp1", "turntable"), ("lamp2", "turntable"), ("lens_w", "lamp1"), ("lens_ir", "lamp2"), ("alu", "lamp1"), ("alu", "lamp2"),
         # v5.2: Status-LED + Diffusor
         ("diff", "yoke"), ("diff", "arm2"), ("diff", "lid"), ("diff", "turntable"), ("diff", "lamp1"), ("diff", "lamp2"), ("diff", "horn2"),
         ("diff", "side"), ("diff", "head"), ("sled", "head"), ("sled", "servo2"), ("sled", "cam3"), ("sled", "therm"), ("sled", "side"),
         ("diff", "tub")]
static = [("tub", k) for k in ("ups", "pi", "cooler", "pca", "speaker", "charger", "pam", "soundcard", "mic", "pir", "jacks", "plug", "servo1", "shelf", "feet", "lid",
                               "hub", "relay", "mosfet", "buck", "relayjack", "probe", "ina", "wcam", "irled", "btn")] + \
         [("hub", k) for k in ("ups", "pi", "speaker", "relay", "pca", "servo1")] + [("soundcard", k) for k in ("speaker", "pca", "servo1", "pir")] + \
         [("lid", k) for k in ("servo1", "pi", "cooler", "jacks", "soundcard", "charger", "wcam", "btn")] + \
         [("servo1", "speaker"), ("shelf", "ups"), ("shelf", "pi"), ("shelf", "jacks"), ("ups", "pi"), ("pca", "speaker")] + \
         [("wcam", k) for k in ("pir", "mic", "servo1", "mosfet", "buck", "pca", "speaker", "irled", "hub", "soundcard", "relay")] + \
         [("irled", k) for k in ("buck", "mosfet", "pir", "speaker", "pca", "lid", "hub", "soundcard", "servo1")] + \
         [("btn", k) for k in ("pi", "cooler", "ups", "shelf", "jacks", "relayjack", "charger", "pam", "ina")] + \
         [("mosfet", k) for k in ("pca", "speaker", "probe", "buck", "hub", "soundcard")] + \
         [("sdext", k) for k in ("pca", "servo1", "lid", "pi", "hub", "mosfet", "irled", "wcam")] + [("tub", "sdext"), ("tub", "sdplug"), ("plug", "pi")] + \
         [("sockel", k) for k in ("pi", "shelf", "pca", "hub", "charger", "pam", "ina", "jacks", "relayjack", "speaker", "soundcard", "cam1", "cam0", "mosfet", "probe")] + \
         [("lampdrv", k) for k in ("tub", "buck", "pca", "speaker", "mosfet", "pir", "irled", "probe", "fuseh")] + \
         [("fuseh", k) for k in ("tub", "speaker", "probe", "mosfet", "pca", "ups", "sockel")] + \
         [("resjack", k) for k in ("pi", "ups", "sockel", "shelf", "jacks", "relayjack", "btn", "charger", "lid")] + [("tub", "resplug"), ("tub", "resjack")] + \
         [("blind_w", "tub"), ("blind_ir", "tub"), ("blind_w", "blind_ir")]


def coll(P, a, b):
    la, ha = P[a].bbox(); lb, hb = P[b].bbox()
    lo = np.maximum(la, lb); hi = np.minimum(ha, hb)
    if np.any(hi <= lo): return 0
    g = [np.arange(lo[i], hi[i], h) for i in range(3)]
    X = np.stack(np.meshgrid(*g, indexing="ij"), -1).reshape(-1, 3)
    return sum(int(np.sum((P[a].sdf(X[c:c + 300000]) < -0.05) & (P[b].sdf(X[c:c + 300000]) < -0.05))) for c in range(0, len(X), 300000)) * h ** 3


def fov_rays(k=1.0):
    """Strahlen der CM3 Wide (Modell äquidistant: 102° x 67°, Ecke ~120°) von 5 Punkten der Frontlinse (r 2,5).
    k > 1 vergrössert das Sichtfeld (Winkel-Reserve)."""
    us = np.linspace(-51, 51, 35) * k; vs = np.linspace(-33.5, 33.5, 23) * k
    U_, V_ = np.meshgrid(us, vs, indexing="ij")
    edge = (np.abs(U_) == 51 * k) | (np.abs(V_) == 33.5 * k)
    grid = np.column_stack([U_[edge | ((np.arange(35)[:, None] % 4 == 0) & (np.arange(23)[None, :] % 4 == 0))].ravel(),
                            V_[edge | ((np.arange(35)[:, None] % 4 == 0) & (np.arange(23)[None, :] % 4 == 0))].ravel()])
    th = np.radians(np.hypot(grid[:, 0], grid[:, 1])); ph = np.arctan2(grid[:, 1], grid[:, 0])
    D = (np.cos(th)[:, None] * v52.WA + (np.sin(th) * np.cos(ph))[:, None] * v52.WH + (np.sin(th) * np.sin(ph))[:, None] * v52.WU)
    orig = [v52.WL + 0.05 * v52.WA + r * e for r, e in ((0, v52.WH), (2.5, v52.WH), (-2.5, v52.WH), (2.5, v52.WU), (-2.5, v52.WU))]
    O = np.concatenate([np.repeat(o[None], len(D), 0) for o in orig]); DD = np.concatenate([D] * len(orig))
    return O, DD


def trace(scene, O, D, tmax=400.0):
    t = np.zeros(len(O)); mind = np.full(len(O), 1e9); hit = np.zeros(len(O), bool); act = np.arange(len(O))
    for it in range(600):
        if len(act) == 0: break
        d = scene.sdf(O[act] + t[act, None] * D[act])
        far = t[act] > 0.3                              # Abstand ab 0,3 mm vor der Linse werten
        mind[act[far]] = np.minimum(mind[act[far]], d[far])
        hh = d < 0.0                                    # echt im Material (Schritt >= 0,03 mm)
        hit[act[hh]] = True
        t[act] += np.maximum(d, 0.03)
        act = act[(~hh) & (t[act] < tmax)]
    return hit, mind


def wand(step=0.1):
    """Stirnwand (x = -WALL..0) als Bild y/z: Öffnungen finden, schmalster Steg zwischen je zwei Öffnungen"""
    from scipy import ndimage
    tub = v52.part_tub()
    ys = np.arange(-v52.WALL, v52.LY + v52.WALL, step); zs = np.arange(0.0, v52.TOPZ, step)
    Y, Z = np.meshgrid(ys, zs, indexing="ij")
    solid = np.ones(Y.shape, bool)
    for x in np.linspace(-v52.WALL + 0.05, -0.05, 6):     # durchgehend Material über die ganze Wanddicke
        solid &= (tub.sdf(np.column_stack([np.full(Y.size, x), Y.ravel(), Z.ravel()])) < 0).reshape(Y.shape)
    inside = (Y > 0) & (Y < v52.LY) & (Z > v52.ZF + 1) & (Z < v52.TOPZ - 1)
    lab, n = ndimage.label(~solid & inside)
    holes = []
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() * step * step < 2.0:
            continue
        c = np.argwhere(m).mean(0) * step
        holes.append((m, (round(c[0] - v52.WALL, 1), round(c[1], 1)), round(m.sum() * step * step)))
    res = []
    for a in range(len(holes)):
        da = ndimage.distance_transform_edt(~holes[a][0]) * step
        for b in range(a + 1, len(holes)):
            w = float(da[holes[b][0]].min())
            if w < 8.0:
                res.append((round(w, 2), holes[a][1], holes[b][1]))
    res.sort()
    print(f"Stirnwand: {len(holes)} Öffnungen (y, z Mitte / mm²):", [(h[1], h[2]) for h in holes], flush=True)
    for w, a, b in res:
        print(f"  Steg {w:.2f} mm zwischen Öffnung {a} und {b}" + ("  <-- schmal (< 2 mm)" if w < 2.0 else ""), flush=True)


def abstand():
    """kleinster Abstand der Kabelwege (Mittellinie, Flachkabel ca. 16 mm breit -> ± 8) und des IR-Moduls zu Lüfter,
    Lüftungsschlitzen (Wand -y, x 129..173) und Lautsprecher"""
    import v5
    P = v52.placed(0, 180)
    def pts(seq, n=40):
        out = []
        for a, b in zip(seq[:-1], seq[1:]):
            for t in np.linspace(0, 1, n):
                out.append(np.array(a) * (1 - t) + np.array(b) * t)
        return np.array(out)
    louv = csg.box(v5.LOUV_X0, v5.LOUV_X1, -0.5, 1.0, v5.ZF + 40, v5.ZF + 56)
    fan_in = csg.box(103.0, 126.0, 19.0, 43.0, 55.5, 57.0)            # Ansaugfläche oben auf dem Active Cooler (Annahme)
    for nm, X in (("CAM1", pts(v52.cable_cam1_pts())), ("CAM0", pts(v52.cable_cam0_pts()))):
        for on, node in (("Lüfter (Gehäuse)", P["cooler"]), ("Lüfter-Ansaugung oben", fan_in), ("Lüftungsschlitze", louv),
                         ("Lautsprecher", P["speaker"])):
            print(f"  {nm} -> {on}: {node.sdf(X).min():.1f} mm (Mittellinie)", flush=True)
    ir = P["irled"]
    g = np.stack(np.meshgrid(*[np.arange(l, h, 0.5) for l, h in zip(*ir.bbox())], indexing="ij"), -1).reshape(-1, 3)
    g = g[ir.sdf(g) < 0]
    for on in ("speaker", "buck", "pca", "wcam", "pir"):
        print(f"  IR-Modul -> {on}: {P[on].sdf(g).min():.1f} mm", flush=True)
    print(f"  IR-Modul -> Lüftungsschlitze: {louv.sdf(g).min():.1f} mm", flush=True)


STOPFEN_PAARE = {"st_therm": ("head", "side", "yoke", "arm2", "lid", "turntable", "lamp1", "lamp2", "servo2", "cam3", "horn2"),
                 "st_irmod": ("tub", "buck", "mosfet", "pir", "wcam", "speaker", "pca", "lampdrv", "lid"),
                 "st_ds18": ("tub", "feet", "fuseh", "speaker", "pca", "mosfet", "lampdrv", "tripod"),
                 "st_relay": ("tub", "btn", "resplug", "resjack", "ups", "sockel", "shelf", "jacks", "fuseh"),
                 "st_mic": ("tub", "mic", "lid", "wcam", "pir", "hub"),
                 "st_ll": ("tub", "btn", "jacks", "lid", "shelf", "charger", "resjack")}


def stopfen(step=0.1):
    """18–21: Kollisionen (eingesetzt) und offene Fläche der Öffnung (Spalt) – der Kopf-Stopfen in allen Stellungen"""
    t0 = time.time()
    P = v52.placed(0, 180); S = v52.stopfen_placed(0, 180)
    for k, node in S.items():
        out = [f"{b} {v:.2f}" for b in STOPFEN_PAARE[k] if b in P and (v := coll({k: node, b: P[b]}, k, b)) > 0]
        print(f"{k:9s} eingesetzt: {', '.join(out) or 'frei'}", flush=True)
    for k, hole in v52.stopfen_loecher().items():          # Durchblick: Strahlen entlang der Lochachse ohne Stopfen-Material
        lo, hi = hole.bbox()
        ax = int(np.argmin(hi - lo)); o = [i for i in range(3) if i != ax]
        A, B = np.meshgrid(np.arange(lo[o[0]] + step / 2, hi[o[0]], step), np.arange(lo[o[1]] + step / 2, hi[o[1]], step), indexing="ij")
        Q = np.zeros((A.size, 3)); Q[:, o[0]] = A.ravel(); Q[:, o[1]] = B.ravel(); Q[:, ax] = (lo[ax] + hi[ax]) / 2
        Q = Q[hole.sdf(Q) < 0]
        zu = np.zeros(len(Q), bool)
        for a in np.arange(lo[ax] - 3.0, hi[ax] + 3.0, step):
            Q[:, ax] = a; zu |= S[k].sdf(Q) < 0
        print(f"{k:9s} Öffnung {len(Q) * step ** 2:6.1f} mm², Durchblick {(~zu).sum() * step ** 2:5.2f} mm² ({(~zu).mean() * 100:.1f} %)", flush=True)
    for pan in PANS:
        for tilt in TILTS:
            P = v52.placed(tilt, pan); P["st_therm"] = v52.stopfen_placed(tilt, pan)["st_therm"]
            out = [f"{b} {v:.1f}" for b in STOPFEN_PAARE["st_therm"] if b != "head" and (v := coll(P, "st_therm", b)) > 0]
            print(f"st_therm tilt {tilt:4} pan {pan:4}: {', '.join(out) or 'frei'} ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    what = sys.argv[1:] or ["koll", "fov", "wand", "abstand", "stopfen"]
    t0 = time.time()
    if "wand" in what:
        wand()
    if "abstand" in what:
        abstand()
    if "stopfen" in what:
        stopfen()
    if "koll" in what or "statisch" in what:
        P = v52.placed(0, 180, blinds=v52.IR_TYP == "5mm")
        st = [(a, b) for a, b in static if a in P and b in P]
        out = [f"{a}/{b} {v:.1f}" for a, b in st if (v := coll(P, a, b)) > 0]
        print("statisch:", ", ".join(out) or "frei", f"({time.time() - t0:.0f}s)", flush=True)
    if "koll" in what:
        for pan in PANS:
            for tilt in TILTS:
                P = v52.placed(tilt, pan)
                out = [f"{a}/{b} {v:.1f}" for a, b in pairs if (v := coll(P, a, b)) > 0]
                print(f"tilt {tilt:4} pan {pan:4}:", ", ".join(out) or "frei", f"({time.time() - t0:.0f}s)", flush=True)
    if "fov" in what:
        O, D = fov_rays()
        print(f"Sichtfeld-Test: {len(O)} Strahlen", flush=True)
        solid = ["tub", "lid", "turntable", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "alu", "head", "side", "diff", "feet", "balls"]
        for pan in PANS:
            for tilt in TILTS:
                P = v52.placed(tilt, pan)
                hit, mind = trace(csg.U(*[P[k] for k in solid]), O, D)
                msg = "frei" if not hit.any() else f"{hit.sum()} Strahlen blockiert"
                print(f"tilt {tilt:4} pan {pan:4}: {msg} ({time.time() - t0:.0f}s)", flush=True)
        # Winkel-Reserve gegenüber dem Unterteil (Fensterrand, Regendach): Sichtfeld vergrössern bis ein Strahl anstösst
        tub = v52.placed(0, 180)["tub"]
        for k in (1.0, 1.02, 1.04, 1.06, 1.08, 1.10, 1.12, 1.15, 1.2):
            O, D = fov_rays(k)
            hit, _ = trace(tub, O, D, tmax=60)
            print(f"Sichtfeld x {k:.2f} ({102 * k:.0f}° x {67 * k:.0f}°, Ecke ~{120 * k:.0f}°): {'frei' if not hit.any() else str(hit.sum()) + ' Strahlen am Unterteil'}", flush=True)
            if hit.any(): break
