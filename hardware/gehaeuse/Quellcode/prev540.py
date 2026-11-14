"""5.4.0: Vorschaubilder 29 Transportsicherung (Haube) und 30 Drehsperre-Klammer -> ../Bilder/Vorschau_v5-4-0_*.png
(python3 prev540.py 1 3)
1 Haube allein mit Massen   2 Klammer allein mit Massen   3 Vergleich: erste Kappe (Rahmen, Runde 1) und Haube + Klammer im
gleichen Massstab   4 / 5 / 6 aufgesetzt (Gerät v5.3, Kopf in Grundstellung): vorne links, hinten links, hinten rechts von oben.
Bilder nur zum Ansehen."""
import os, sys, itertools, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import kappe540 as k, klammer540 as kl, concept_render as cr

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.environ.get("GEH_BILDER") or os.path.join(HIER, "..", "Bilder")
cr.COL.update({"kappe": (0.62, 0.64, 0.68), "klammer": (0.15, 0.6, 0.35), "lamp1": (0.95, 0.55, 0.15), "lamp2": (0.95, 0.55, 0.15),
               "diff": (0.95, 0.95, 0.95), "feet": (0.2, 0.2, 0.2), "hatch": (0.6, 0.62, 0.66), "wcam": (0.1, 0.55, 0.2),
               "irled": (0.75, 0.1, 0.1), "btn": (0.1, 0.1, 0.1), "sdplug": (0.15, 0.15, 0.15), "resplug": (0.15, 0.15, 0.15),
               "relayjack": (0.3, 0.3, 0.3), "probe": (0.75, 0.75, 0.78)})
os.makedirs(ZIEL, exist_ok=True)
sel = sys.argv[1:]
W, H = 760, 600
GERAET = ("tub", "lid", "feet", "hatch", "turntable", "yoke", "arm2", "lamp1", "lamp2", "lens_w", "lens_ir", "head", "side", "cam3",
          "therm", "diff", "wcam", "irled", "pir", "jacks", "btn", "sdplug", "plug", "resplug", "relayjack")
ANSICHT = [-0.85, -0.9, 0.55]


def kanten(lo, hi):
    """die 12 Kanten eines Quaders"""
    ecken = [np.array([(lo, hi)[i][0], (lo, hi)[j][1], (lo, hi)[m][2]]) for i in (0, 1) for j in (0, 1) for m in (0, 1)]
    return [(a, b) for a, b in itertools.combinations(ecken, 2) if np.sum(np.abs(a - b) > 1e-6) == 1]


def mit_massen(name, img, proj, boxes, titel):
    """Bild + Quader-Rahmen mit Kantenlängen (boxes: [(lo, hi, Farbe, Text)])"""
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(img); ax.set_axis_off()
    for lo, hi, col, txt in boxes:
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        for a, b in kanten(lo, hi):
            (x0, y0), (x1, y1) = proj(a), proj(b)
            ax.plot([x0, x1], [y0, y1], color=col, lw=1.0, ls="--")
        for ax_i, b in enumerate(([hi[0], lo[1], lo[2]], [lo[0], hi[1], lo[2]], [lo[0], lo[1], hi[2]])):
            b = np.asarray(b)
            m = proj((lo + b) / 2)
            ax.text(m[0], m[1], "%.0f" % (b - lo)[ax_i], color=col, fontsize=10, ha="center", va="center",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1))
        if txt:
            p = proj(hi)
            ax.text(p[0], p[1] - 12, txt, color=col, fontsize=10, ha="center")
    ax.text(10, 22, titel, fontsize=12, color="black")
    fig.savefig(os.path.join(ZIEL, f"Vorschau_v5-4-0_{name}.png")); plt.close(fig); print(name, flush=True)


def save(name, img, titel):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(img); ax.set_axis_off()
    ax.text(10, 22, titel, fontsize=12, color="black")
    fig.savefig(os.path.join(ZIEL, f"Vorschau_v5-4-0_{name}.png")); plt.close(fig); print(name, flush=True)


kap, kla = k.part_kappe(), kl.part_klammer()
lo, hi = kap.bbox()
klo, khi = kla.bbox()
P = kl.placed(0, 180)
if not sel or "1" in sel:
    img, proj = cr.render({"kappe": kap}, [-0.8, -1.0, 0.75], W=W, H=H, zoom=0.85)
    mit_massen("1_Haube", img, proj, [(lo, hi, "tab:blue", "")], "29 Transportsicherung (Haube): %.0f × %.0f × %.0f mm" % tuple(hi - lo))
if not sel or "2" in sel:
    img, proj = cr.render({"klammer": kla}, [0.8, -0.9, 0.9], W=W, H=H, zoom=0.85)
    mit_massen("2_Klammer", img, proj, [(klo, khi, "tab:green", "")], "30 Drehsperre-Klammer: %.0f × %.0f × %.0f mm" % tuple(khi - klo))
if not sel or "3" in sel:
    alt_lo, alt_hi = np.array(k.ALT_BOX[0]), np.array(k.ALT_BOX[1])
    teile = {n: P[n] for n in ("lid", "turntable", "yoke", "arm2", "lamp1", "lamp2", "head", "side", "diff", "kappe", "klammer")}
    img, proj = cr.render(teile, ANSICHT, W=W, H=H, zoom=0.8)
    mit_massen("3_Vergleich_alt_neu", img, proj,
               [(alt_lo, alt_hi, "tab:red", "erste Kappe"), (lo, hi, "tab:blue", "Haube"), (klo, khi, "tab:green", "Klammer")],
               "alt %.0f×%.0f×%.0f  ->  Haube %.0f×%.0f×%.0f + Klammer %.0f×%.0f×%.0f mm"
               % (*(alt_hi - alt_lo), *(hi - lo), *(khi - klo)))
for nr, (vw, nm) in ((4, ([-0.85, -0.9, 0.55], "vorne links")), (5, ([0.9, -0.7, 0.6], "hinten links")),
                     (6, ([0.75, 0.8, 0.9], "hinten rechts, von oben"))):
    if not sel or str(nr) in sel:
        img, _ = cr.render({n: P[n] for n in GERAET + ("kappe", "klammer") if n in P}, vw, W=W, H=H)
        save("%d_aufgesetzt_%s" % (nr, nm.split(",")[0].replace(" ", "_")), img, "Haube 29 + Klammer 30 aufgesetzt, %s" % nm)
