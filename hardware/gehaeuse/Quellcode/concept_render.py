import numpy as np, csg

COL = {"tub": (0.20, 0.45, 0.75), "lid": (0.35, 0.60, 0.90), "turntable": (0.95, 0.55, 0.15), "yoke": (0.95, 0.55, 0.15),
       "arm2": (0.95, 0.55, 0.15), "head": (0.22, 0.22, 0.25), "side": (0.35, 0.35, 0.38), "cam3": (0.6, 0.1, 0.1),
       "therm": (0.55, 0.15, 0.55), "lens_w": (1.0, 0.95, 0.6), "lens_ir": (0.75, 0.1, 0.1), "alu": (0.75, 0.75, 0.78),
       "balls": (0.8, 0.8, 0.82), "pi": (0.15, 0.55, 0.25), "cooler": (0.12, 0.12, 0.12), "pca": (0.1, 0.3, 0.7),
       "speaker": (0.9, 0.85, 0.2), "mosfet": (0.55, 0.35, 0.2), "pam": (0.85, 0.3, 0.6), "soundcard": (0.95, 0.95, 0.95),
       "mic": (0.1, 0.8, 0.8), "usbc": (0.3, 0.3, 0.3), "servo1": (0.15, 0.25, 0.6), "ups": (0.55, 0.75, 0.25), "mpu": (0.5, 0.2, 0.8), "lte": (0.95, 0.95, 0.95), "hub": (0.4, 0.4, 0.45), "gps": (0.95, 0.5, 0.1), "pir": (0.97, 0.97, 0.9), "jacks": (0.3, 0.3, 0.3), "bme": (0.6, 0.1, 0.6), "buck": (0.85, 0.2, 0.2), "reserve": (0.55, 0.55, 0.6), "plug": (0.15, 0.15, 0.15), "dps": (0.2, 0.2, 0.22), "dpsscreen": (0.2, 0.6, 0.95), "charger": (0.1, 0.55, 0.3)}


def render(parts, view, W=1000, H=760, hide=(), clip=None, zoom=1.0):
    names = [k for k in parts if k not in hide]
    scene = csg.U(*[parts[k] for k in names])
    lo, hi = scene.bbox(); ctr = (lo + hi) / 2
    v = np.array(view, float); v /= np.linalg.norm(v)
    up = np.array([0, 0, 1.0]); rgt = np.cross(up, v); rgt /= np.linalg.norm(rgt); up2 = np.cross(v, rgt)
    cs = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) - ctr
    su, sv = np.abs(cs @ rgt).max() * 1.06, np.abs(cs @ up2).max() * 1.06
    s = max(su / W, sv / H) * 2 / zoom
    uu, vv = np.meshgrid((np.arange(W) - W / 2) * s, (H / 2 - np.arange(H)) * s)
    dist = np.linalg.norm(hi - lo)
    O = ctr + v * dist + uu.reshape(-1, 1) * rgt + vv.reshape(-1, 1) * up2
    Dd = -v
    t = np.zeros(len(O)); hit = np.zeros(len(O), bool); act = np.arange(len(O))
    for it in range(300):
        if len(act) == 0: break
        P = O[act] + t[act, None] * Dd
        d = scene.sdf(P)
        h = d < 0.02
        hit[act[h]] = True
        t[act] += np.maximum(d, 0.02) * 0.9
        act = act[(~h) & (t[act] < dist * 2)]
    img = np.ones((len(O), 3))
    idx = np.where(hit)[0]
    P = O[idx] + t[idx, None] * Dd
    e = 0.05
    nrm = np.stack([scene.sdf(P + e * np.eye(3)[k]) - scene.sdf(P - e * np.eye(3)[k]) for k in range(3)], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    ds = np.stack([parts[k].sdf(P) for k in names], 1)
    col = np.array([COL[k] for k in names])[ds.argmin(1)]
    L = v * 0.6 - rgt * 0.4 + up2 * 0.7; L /= np.linalg.norm(L)
    img[idx] = col * (np.clip(nrm @ L, 0, 1) * 0.65 + 0.35)[:, None]

    def proj(p):
        q = np.asarray(p, float) - ctr
        return (q @ rgt) / s + W / 2, H / 2 - (q @ up2) / s
    return np.clip(img.reshape(H, W, 3), 0, 1), proj
