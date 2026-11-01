import sys, numpy as np, v5
h = 0.4
moving = ["head","side","yoke","arm2","lamp1","lamp2","lens_w","lens_ir","alu","turntable","servo2","cam3","therm"]
pairs = [("head","yoke"),("head","arm2"),("head","horn2"),("side","arm2"),("side","yoke"),("servo2","yoke"),("servo2","arm2"),
         ("lamp1","yoke"),("lamp1","arm2"),("head","yoke"),("lamp2","arm2"),("lamp1","head"),("lamp2","head"),("lamp2","side"),("lamp1","lid"),("lamp2","lid"),
         ("yoke","lid"),("arm2","lid"),("head","lid"),("turntable","lid"),("turntable","balls"),("yoke","turntable"),("arm2","turntable"),
         ("lamp1","turntable"),("lamp2","turntable"),("lens_w","lamp1"),("lens_ir","lamp2"),("alu","lamp1"),("alu","lamp2")]
static = [("tub", k) for k in ("ups","pi","cooler","pca","speaker","charger","pam","soundcard","mic","pir","jacks","plug","servo1","shelf","feet","lid","hub","relay","mosfet","buck","relayjack","probe","ina")] + [("hub", k) for k in ("ups","pi","speaker","relay","pca","servo1")] + [("soundcard", k) for k in ("speaker","pca","servo1","pir")] + \
         [("lid", k) for k in ("servo1","pi","cooler","jacks","soundcard","charger")] + [("servo1","speaker"),("shelf","ups"),("shelf","pi"),("shelf","jacks"),("ups","pi"),("pca","speaker")]
def coll(P, a, b):
    la, ha = P[a].bbox(); lb, hb = P[b].bbox()
    lo = np.maximum(la, lb); hi = np.minimum(ha, hb)
    if np.any(hi <= lo): return 0
    g = [np.arange(lo[i], hi[i], h) for i in range(3)]
    X = np.stack(np.meshgrid(*g, indexing="ij"), -1).reshape(-1, 3)
    return sum(int(np.sum((P[a].sdf(X[c:c+300000]) < -0.05) & (P[b].sdf(X[c:c+300000]) < -0.05))) for c in range(0, len(X), 300000)) * h**3
P = v5.placed(0, 180)
out = [f"{a}/{b} {v:.1f}" for a, b in static if (v := coll(P, a, b)) > 0]
print("statisch:", ", ".join(out) or "frei", flush=True)
for tilt, pan in [(0,180),(40,180),(-40,180),(70,180),(-70,180),(0,90),(30,270),(-60,0),(0,135),(0,225)]:
    P = v5.placed(tilt, pan)
    out = [f"{a}/{b} {v:.1f}" for a, b in pairs if (v := coll(P, a, b)) > 0]
    print(f"tilt {tilt:4} pan {pan:4}:", ", ".join(out) or "frei", flush=True)
