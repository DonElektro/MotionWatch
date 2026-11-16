#!/usr/bin/env python3
"""Synthetic distance test for the «Markier-Karte» (ArUco marker on A4/A5) with the MoveEye camera:
Camera Module 3, 1280x720, HFOV 66 deg (part 200 / 290). Renders the card in perspective (4x supersampled),
adds blur, noise, low contrast, JPEG, and counts detections. Works with OpenCV >= 4.7 (ArucoDetector) and
4.6 contrib (detectMarkers) - the same compat layer the part would use."""
import json, math, sys, time
import numpy as np
import cv2

W, H, HFOV = 1280, 720, 66.0
F = (W / 2) / math.tan(math.radians(HFOV / 2))          # focal length in px (~985)
SS = 4                                                  # supersampling


def aruco_api(dict_name):
    a = getattr(cv2, "aruco", None)
    if a is None:
        return None
    d = a.getPredefinedDictionary(getattr(a, dict_name))
    if hasattr(a, "ArucoDetector"):
        p = a.DetectorParameters()
        tune(p)
        det = a.ArucoDetector(d, p)
        return d, (lambda g: det.detectMarkers(g)), "ArucoDetector"
    p = a.DetectorParameters_create()
    tune(p)
    return d, (lambda g: a.detectMarkers(g, d, parameters=p)), "detectMarkers (4.6)"


TUNE = True


def tune(p):
    if not TUNE:
        return
    p.minMarkerPerimeterRate = 0.012          # allows ~4 px sides at 1280 (default 0.03 -> ~10 px)
    p.adaptiveThreshWinSizeMin = 3
    p.adaptiveThreshWinSizeMax = 33
    p.adaptiveThreshWinSizeStep = 6
    p.polygonalApproxAccuracyRate = 0.05
    p.perspectiveRemovePixelPerCell = 8
    p.perspectiveRemoveIgnoredMarginPerCell = 0.2
    p.errorCorrectionRate = 0.6
    try:
        p.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    except AttributeError:
        pass


def marker_img(d, mid, px):
    a = cv2.aruco
    if hasattr(a, "generateImageMarker"):
        return a.generateImageMarker(d, mid, px)
    return a.drawMarker(d, mid, px)


def card_texture(d, mid, fmt):
    """card as texture, 1 px = 0.5 mm: A4 210x297 (marker 180 mm), A5 148x210 (marker 128 mm); white quiet zone"""
    pw, ph, ms = (210, 297, 180) if fmt == "A4" else (148, 210, 128)
    k = 2
    tex = np.full((ph * k, pw * k), 255, np.uint8)
    m = marker_img(d, mid, ms * k)
    x0 = (pw - ms) // 2 * k
    tex[x0:x0 + ms * k, x0:x0 + ms * k] = m
    # small QR stand-in (dense pattern) below the marker
    rng = np.random.default_rng(1)
    q = (rng.random((25, 25)) > 0.5).astype(np.uint8) * 255
    qs = 30 * k
    qy = x0 + ms * k + 6 * k
    tex[qy:qy + qs, x0:x0 + qs] = cv2.resize(q, (qs, qs), interpolation=cv2.INTER_NEAREST)
    return tex, pw / 1000.0, ph / 1000.0, ms / 1000.0, (x0 / k / 1000.0)


def render(tex, cw, ch, dist, yaw, cx, cy, rng, blur, noise, contrast, jpeg):
    """card centre at pixel (cx,cy), distance dist (m), rotated by yaw around its vertical axis"""
    Ws, Hs, Fs = W * SS, H * SS, F * SS
    # background: soft random texture (grass / tent), mid grey
    bg = rng.normal(110, 35, (H // 8, W // 8)).astype(np.float32)
    bg = cv2.resize(bg, (Ws, Hs), interpolation=cv2.INTER_CUBIC)
    bg = np.clip(bg, 0, 255)
    # 3D corners of the card
    X = (cx - W / 2) / F * dist
    Y = (cy - H / 2) / F * dist
    cyw, syw = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    pts3 = []
    for u, v in ((-cw / 2, -ch / 2), (cw / 2, -ch / 2), (cw / 2, ch / 2), (-cw / 2, ch / 2)):
        pts3.append((X + u * cyw, Y + v, dist + u * syw))
    dst = np.float32([[Fs * p[0] / p[2] + Ws / 2, Fs * p[1] / p[2] + Hs / 2] for p in pts3])
    th, tw = tex.shape
    src = np.float32([[0, 0], [tw, 0], [tw, th], [0, th]])
    M = cv2.getPerspectiveTransform(src, dst)
    # paper is not pure white / black outdoors: contrast factor around mid grey
    t = (tex.astype(np.float32) - 128) * contrast + 140
    warped = cv2.warpPerspective(t, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderValue=0)
    mask = cv2.warpPerspective(np.ones_like(t), M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderValue=0)
    img = bg * (1 - mask) + warped * mask
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
    if blur > 0:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    if noise > 0:
        img = img + rng.normal(0, noise, img.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)
    if jpeg:
        ok, b = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, jpeg])
        img = cv2.imdecode(b, cv2.IMREAD_GRAYSCALE)
    return img


ROI = 0          # 0 = whole picture; k = crop 320x320 around the (known) position, enlarge k times (tracking mode)
QUICK = False


def roi_detect(detect, img, cx, cy, k):
    x0 = int(max(0, min(W - 320, cx - 160))); y0 = int(max(0, min(H - 320, cy - 160)))
    crop = img[y0:y0 + 320, x0:x0 + 320]
    big = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    corners, ids, rej = detect(big)
    if ids is not None:
        corners = [c / k + np.float32([x0, y0]) for c in corners]
    return corners, ids, rej


def run(dict_name="DICT_4X4_50", fmt="A4", trials=12, out=None):
    d, detect, api = aruco_api(dict_name)
    tex, cw, ch, ms, _ = card_texture(d, 7, fmt)
    conds = {
        "sharp": dict(blur=0.0, noise=3, contrast=0.85, jpeg=85),
        "blur1": dict(blur=1.0, noise=6, contrast=0.75, jpeg=80),
        "blur1.6+noise": dict(blur=1.6, noise=10, contrast=0.6, jpeg=75),
        "dusk": dict(blur=1.2, noise=16, contrast=0.35, jpeg=70),
    }
    dists = [2, 5, 8, 10, 12, 15, 18]
    yaws = [0, 30, 50, 65]
    if QUICK:
        conds = {"sharp": conds["sharp"], "blur0.7": dict(blur=0.7, noise=5, contrast=0.8, jpeg=85), "blur1": conds["blur1"],
                 "blur1.6+noise": conds["blur1.6+noise"], "dusk": conds["dusk"]}
        dists = [5, 8, 10, 12, 15, 18, 22]
        yaws = [0, 45]
        trials = 8
    res = {"api": api, "cv": cv2.__version__, "dict": dict_name, "fmt": fmt, "marker_m": ms, "f_px": round(F, 1), "rows": []}
    t_det = []
    for cname, c in conds.items():
        for yaw in yaws:
            for dist in dists:
                rng = np.random.default_rng(int(dist * 100 + yaw + len(cname)))
                hit = 0
                derr = []
                for i in range(trials):
                    cx = rng.uniform(200, W - 200)
                    cy = rng.uniform(150, H - 150)
                    img = render(tex, cw, ch, dist, yaw + rng.uniform(-5, 5), cx, cy, rng, **c)
                    t0 = time.perf_counter()
                    corners, ids, _rej = roi_detect(detect, img, cx, cy, ROI) if ROI else detect(img)
                    t_det.append(time.perf_counter() - t0)
                    if ids is not None and 7 in ids.flatten():
                        hit += 1
                        k = list(ids.flatten()).index(7)
                        q = corners[k].reshape(4, 2)
                        # distance from the longest side (vertical sides are not shortened by yaw)
                        side = max(np.linalg.norm(q[0] - q[3]), np.linalg.norm(q[1] - q[2]))
                        derr.append(F * ms / side / dist - 1)
                res["rows"].append({"cond": cname, "yaw": yaw, "dist": dist, "rate": hit / trials,
                                    "dist_err_pct": round(100 * float(np.mean(np.abs(derr))), 1) if derr else None,
                                    "side_px": round(F * ms / dist, 1)})
    res["det_ms_median"] = round(1000 * float(np.median(t_det)), 2)
    if out:
        json.dump(res, open(out, "w"), indent=1)
    return res


def table(res):
    print(f"# {res['api']} cv {res['cv']} {res['dict']} {res['fmt']} marker {res['marker_m']*1000:.0f} mm, f={res['f_px']} px, "
          f"detect median {res['det_ms_median']} ms/frame (1280x720, this PC)")
    dists = sorted({r["dist"] for r in res["rows"]})
    print("cond            yaw  " + " ".join(f"{d:>5}m" for d in dists))
    key = {}
    for r in res["rows"]:
        key.setdefault((r["cond"], r["yaw"]), {})[r["dist"]] = r
    for (c, y), m in key.items():
        print(f"{c:15s} {y:3d}  " + " ".join(f"{int(100*m[d]['rate']):5d}%" for d in dists))
    print("side px:             " + " ".join(f"{F*res['marker_m']/d:6.1f}" for d in dists))
    errs = [r["dist_err_pct"] for r in res["rows"] if r["dist_err_pct"] is not None and r["yaw"] == 0]
    print(f"distance error (yaw 0, all conds, mean |err|): {np.mean(errs):.1f} %   max {np.max(errs):.1f} %")


if __name__ == "__main__":
    dn = sys.argv[1] if len(sys.argv) > 1 else "DICT_4X4_50"
    fmt = sys.argv[2] if len(sys.argv) > 2 else "A4"
    if len(sys.argv) > 4 and sys.argv[4] == "default":
        TUNE = False
    for a in sys.argv:
        if a.startswith("--roi="):
            ROI = float(a[6:])
        if a == "--quick":
            QUICK = True
    r = run(dn, fmt, out=sys.argv[3] if len(sys.argv) > 3 else None)
    if not TUNE:
        r["api"] += " (default params)"
    if ROI:
        r["api"] += f" ROI x{ROI}"
    table(r)
    if "--sample" in sys.argv:
        d, _, _ = aruco_api(dn)
        tex, cw, ch, ms, _ = card_texture(d, 7, fmt)
        rng = np.random.default_rng(3)
        for dist in (5, 10, 15):
            cv2.imwrite(f"sample_{fmt}_{dist}m.png", render(tex, cw, ch, dist, 30, 640, 360, rng, blur=1.0, noise=6, contrast=0.75, jpeg=80))
