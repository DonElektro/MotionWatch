"""5.5.0: Vorschaubilder Schutzschale 31 / 32 mit Stopfen 33 -> ../Bilder/Vorschau_v5-5-0_*.png   (python3 prev550.py [1 … 6])
1 geschlossen mit Massen   2 Hälften auseinander   3 / 4 Vorderseite mit / ohne Stopfen   5 Schnitt bei y = 40 (Luft über dem
Kopf, Sperr-Rippen)   6 Grösse mit und ohne Schale. Bilder nur zum Ansehen."""
import sys, os, itertools, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from csg import I, box
import kappe540 as k, schale550 as s

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.environ.get("GEH_BILDER") or os.path.join(HIER, "..", "Bilder")
os.makedirs(ZIEL, exist_ok=True)
vorne, hinten = s.part_vorne(), s.part_hinten()
P = s.placed()

if __name__ == "__main__":
    import concept_render as cr
    cr.COL.update({"schale_vorne": (0.25, 0.55, 0.75), "schale_hinten": (0.62, 0.64, 0.68), "stopfen": (0.95, 0.75, 0.1),
                   "lamp1": (0.95, 0.55, 0.15), "lamp2": (0.95, 0.55, 0.15), "diff": (0.95, 0.95, 0.95), "feet": (0.2, 0.2, 0.2),
                   "hatch": (0.6, 0.62, 0.66), "wcam": (0.1, 0.55, 0.2), "irled": (0.75, 0.1, 0.1), "btn": (0.1, 0.1, 0.1),
                   "sdplug": (0.15, 0.15, 0.15), "resplug": (0.15, 0.15, 0.15), "relayjack": (0.3, 0.3, 0.3)})
    W, H = 760, 600
    G = ("tub", "lid", "feet", "hatch", "turntable", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "head", "side", "cam3",
         "therm", "diff", "wcam", "irled", "pir", "jacks", "btn", "sdplug", "plug", "resplug", "relayjack")
    sel = sys.argv[1:]

    def kanten(lo, hi):
        ecken = [np.array([(lo, hi)[i][0], (lo, hi)[j][1], (lo, hi)[m][2]]) for i in (0, 1) for j in (0, 1) for m in (0, 1)]
        return [(a, b) for a, b in itertools.combinations(ecken, 2) if np.sum(np.abs(a - b) > 1e-6) == 1]

    def bild(name, img, proj, boxes, titel):
        fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
        ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(img); ax.set_axis_off()
        for blo, bhi, col, txt in boxes:
            blo, bhi = np.asarray(blo, float), np.asarray(bhi, float)
            for a, b in kanten(blo, bhi):
                (x0, y0), (x1, y1) = proj(a), proj(b)
                ax.plot([x0, x1], [y0, y1], color=col, lw=1.0, ls="--")
            for i_, b in enumerate(([bhi[0], blo[1], blo[2]], [blo[0], bhi[1], blo[2]], [blo[0], blo[1], bhi[2]])):
                b = np.asarray(b); m = proj((blo + b) / 2)
                ax.text(m[0], m[1], "%.0f" % (b - blo)[i_], color=col, fontsize=10, ha="center", va="center",
                        bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1))
            if txt:
                p = proj(bhi); ax.text(p[0], p[1] - 12, txt, color=col, fontsize=10, ha="center")
        ax.text(10, 22, titel, fontsize=12)
        fig.savefig(os.path.join(ZIEL, name)); plt.close(fig); print(name, flush=True)

    def huell(*nodes):
        los = np.array([n.bbox()[0] for n in nodes]); his = np.array([n.bbox()[1] for n in nodes])
        return np.maximum(los.min(0), [-30, -40, 60]), np.minimum(his.max(0), [s.X1, 135, 180])

    slo, shi = huell(vorne, hinten)
    slo[0], shi[0] = s.X0, s.X1
    if not sel or "1" in sel:
        img, proj = cr.render({n: P[n] for n in G + ("schale_vorne", "schale_hinten", "stopfen") if n in P}, [-0.85, -0.9, 0.55], W=W, H=H)
        bild("Vorschau_v5-5-0_1_geschlossen.png", img, proj, [(slo, shi, "tab:blue", "")],
             "Schutzschale 31 / 32 / 33 geschlossen: %.0f × %.0f × %.0f mm" % tuple(shi - slo))
    if not sel or "2" in sel:
        PE = s.placed(explo=45.0)
        img, proj = cr.render({n: PE[n] for n in G + ("schale_vorne", "schale_hinten", "stopfen") if n in PE}, [-0.55, -1.0, 0.45], W=W, H=H)
        bild("Vorschau_v5-5-0_2_auseinander.png", img, proj, [], "Hälften auseinander: 31 vorne (blau) von vorne, 32 hinten (grau) von hinten; Stopfen 33 (gelb)")
    if not sel or "3" in sel:
        img, proj = cr.render({n: P[n] for n in G + ("schale_vorne", "schale_hinten", "stopfen") if n in P}, [-1.0, -0.25, 0.2], W=W, H=H)
        bild("Vorschau_v5-5-0_3_vorne_Stopfen_drin.png", img, proj, [], "Vorderseite, Stopfen eingesetzt")
    if not sel or "4" in sel:
        P2 = s.placed(stopfen=False)
        img, proj = cr.render({n: P2[n] for n in G + ("schale_vorne", "schale_hinten") if n in P2}, [-1.0, -0.25, 0.2], W=W, H=H)
        r = s.fenster_rechtecke()
        wlo = [s.X0, min(x[1] for x in r), min(x[3] for x in r)]; whi = [s.X0, max(x[2] for x in r), max(x[4] for x in r)]
        bild("Vorschau_v5-5-0_4_vorne_Stopfen_draussen.png", img, proj, [],
             "Vorderseite, Stopfen draussen: Sichtfenster Kamera + Wärmebild %.0f × %.0f mm" % (whi[1] - wlo[1], whi[2] - wlo[2]))
    if not sel or "5" in sel:
        yc = 40.0
        bx = box(-40, 140, yc, 140, 50, 190)
        teile = {n: I(P[n], bx) for n in ("lid", "tub", "turntable", "yoke", "arm2", "lamp2", "head", "side", "diff", "cam3", "therm",
                                          "schale_vorne", "schale_hinten", "stopfen")}
        img, proj = cr.render(teile, [0.0, -1.0, 0.05], W=W, H=H)
        bild("Vorschau_v5-5-0_5_Schnitt.png", img, proj, [], "Schnitt bei y = %.0f: Luft über Kopf %.1f mm (Diffusor %.1f), Rippen hinten am Kopf %.1f mm"
             % (yc, s.DACH_Z0 - k.KOPF_OBEN, s.DACH_LUFT, s.PASS))
    if not sel or "6" in sel:
        dlo, dhi = huell(*[P[n] for n in ("tub", "lid", "turntable", "lamp1", "lamp2", "head", "diff", "feet")])
        dlo[2] = -6.0
        img, proj = cr.render({n: P[n] for n in G + ("schale_vorne", "schale_hinten", "stopfen") if n in P}, [-0.8, -1.0, 0.5], W=W, H=H, zoom=0.9)
        bild("Vorschau_v5-5-0_6_Groesse_mit_Geraet.png", img, proj, [(dlo, dhi, "tab:red", "Gerät"), (slo, shi, "tab:blue", "Schale")],
             "Gerät %.0f × %.0f × %.0f mm, mit Schale %.0f × %.0f × %.0f mm" % (*(dhi - dlo), *(np.maximum(dhi, shi) - np.minimum(dlo, slo))))
