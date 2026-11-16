#!/usr/bin/env python3
"""Offline test of the «Markier-Karte»: a synthetic video (Camera Module 3, 1280x720, 66 deg) - the owner walks away with
an A4 card (2 m -> 15 m and back to the side), turns it away three times to mark a point, and somebody walks through the
picture twice (short and long). The head follows with the speed limits of the planner (072). Checks: the card stays near
the middle, 3 points saved where the card was (angle and distance), no point from the occlusions, «verloren» only when
the card is really gone. Usage: sequenz_probe.py [blur] [--video out.mp4]"""
import json, math, sys
import numpy as np
import cv2
from markier_logik import MkDetector, MkSession

W, H, HF = 1280, 720, 66.0
F = (W / 2) / math.tan(math.radians(HF / 2))
VF = math.degrees(2 * math.atan((H / 2) / F))
SS = 4
FPS = 10.0
CARD = (0.210, 0.297, 0.180)
CAM = np.array([0.0, 1.2, 0.0])


def card_tex(det, mid):
    a = cv2.aruco
    gen = a.generateImageMarker if hasattr(a, "generateImageMarker") else a.drawMarker
    k = 4                                           # 4 px per mm
    pw, ph, ms = 210, 297, 180
    tex = np.full((ph * k, pw * k), 245, np.uint8)
    x0 = (pw - ms) // 2 * k
    tex[x0:x0 + ms * k, x0:x0 + ms * k] = gen(det.dic, mid, ms * k)
    rng = np.random.default_rng(1)
    q = (rng.random((25, 25)) > 0.5).astype(np.uint8) * 255
    tex[x0 + ms * k + 24:x0 + ms * k + 24 + 140, x0:x0 + 140] = cv2.resize(q, (140, 140), interpolation=cv2.INTER_NEAREST)
    return tex


# the walk: (time, x, y of the card, z, hold-yaw deg) - the owner stops while marking
KEY = [(0, 0.3, 1.25, 2.0, 10), (3, 0.3, 1.25, 2.0, 10), (10, 2.5, 1.3, 7.0, 20), (14, 2.5, 1.3, 7.0, 20),          # mark 1 at ~7.4 m
       (22, 6.0, 1.6, 12.0, -15), (27, 6.0, 1.6, 12.0, -15),                                                       # mark 2 at ~13.4 m
       (35, -2.0, 0.9, 9.0, 25), (41, -2.0, 0.9, 9.0, 25), (48, -4.0, 1.0, 5.0, 0), (60, -4.0, 1.0, 5.0, 0)]        # mark 3 at ~9.2 m
HIDES = [(11.0, 1.2), (23.5, 2.0), (37.0, 0.8)]          # (start, seconds) the card is turned away
OCCL = [(31.0, 0.25), (50.0, 4.5)]                       # somebody walks through: short, long (no mark!)


def at(t):
    for (t0, *a), (t1, *b) in zip(KEY, KEY[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-6)
            return [x + (y - x) * u for x, y in zip(a, b)]
    return KEY[-1][1:]


def turned(t):
    """0 = card to the camera, 1 = edge-on / away (0.3 s to turn, like a hand)"""
    for s, d in HIDES:
        if s - 0.3 <= t <= s + d + 0.3:
            if t < s:
                return (t - (s - 0.3)) / 0.3
            if t > s + d:
                return 1 - (t - s - d) / 0.3
            return 1.0
    return 0.0


def occluded(t):
    return any(s <= t <= s + d for s, d in OCCL)


def project(P, pan, tilt):
    d = P - CAM
    p, q = math.radians(pan), math.radians(tilt)
    x1 = d[0] * math.cos(p) - d[2] * math.sin(p)
    z1 = d[0] * math.sin(p) + d[2] * math.cos(p)
    y2 = d[1] * math.cos(q) - z1 * math.sin(q)
    z2 = d[1] * math.sin(q) + z1 * math.cos(q)
    return F * x1 / z2 + W / 2, -F * y2 / z2 + H / 2, z2


def true_dir(P):
    d = P - CAM
    return math.degrees(math.atan2(d[0], d[2])), math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))


def render(tex, bg, t, pan, tilt, rng, blur):
    x, y, z, yaw = at(t)
    P = np.array([x, y, z])
    to_cam = CAM - P; to_cam[1] = 0; to_cam /= np.linalg.norm(to_cam)
    ang = math.radians(yaw) + turned(t) * math.radians(95)
    right = np.array([-to_cam[2], 0, to_cam[0]])            # perpendicular to the view, horizontal
    nrm = to_cam
    r = right * math.cos(ang) + nrm * math.sin(ang)
    up = np.array([0, 1.0, 0])
    cw, ch = CARD[0], CARD[1]
    corners = [P - r * cw / 2 + up * ch / 2, P + r * cw / 2 + up * ch / 2, P + r * cw / 2 - up * ch / 2, P - r * cw / 2 - up * ch / 2]
    img = np.roll(bg, -int(pan * F / HF * 0.0175 * 57.3 / 1.0), axis=1)[:H, :W].astype(np.float32)
    back = turned(t) > 0.5
    if not occluded(t):
        uv = np.float32([project(c, pan, tilt)[:2] for c in corners])
        x0, y0 = np.floor(uv.min(0)).astype(int) - 2
        x1, y1 = np.ceil(uv.max(0)).astype(int) + 2
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
        if x1 > x0 + 1 and y1 > y0 + 1:
            th, tw = tex.shape
            src = np.float32([[0, 0], [tw, 0], [tw, th], [0, th]])
            M = cv2.getPerspectiveTransform(src, (uv - np.float32([x0, y0])) * SS)
            sz = ((x1 - x0) * SS, (y1 - y0) * SS)
            t_img = (np.full_like(tex, 235) if back else tex).astype(np.float32)
            t_img = (t_img - 128) * 0.8 + 140
            wp = cv2.warpPerspective(t_img, M, sz, flags=cv2.INTER_AREA if False else cv2.INTER_LINEAR)
            mk = cv2.warpPerspective(np.ones_like(t_img), M, sz, flags=cv2.INTER_LINEAR)
            wp = cv2.resize(wp, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
            mk = cv2.resize(mk, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
            roi = img[y0:y1, x0:x1]
            img[y0:y1, x0:x1] = roi * (1 - mk) + wp * mk
    else:                                                    # a person in front of the card: a dark blob
        u, v, _ = project(P, pan, tilt)
        cv2.ellipse(img, (int(u), int(v)), (60, 140), 0, 0, 360, 70, -1)
    if blur:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    img = np.clip(img + rng.normal(0, 5, img.shape), 0, 255).astype(np.uint8)
    ok, b = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return cv2.imdecode(b, cv2.IMREAD_GRAYSCALE)


def run(blur=0.8, video=None):
    det = MkDetector()
    if not det.ok:
        print("ArUco fehlt:", det.why); return 1
    tex = card_tex(det, 42)
    rng = np.random.default_rng(5)
    bg = np.clip(cv2.resize(rng.normal(110, 35, (H // 8, (W * 3) // 8)).astype(np.float32), (W * 3, H), interpolation=cv2.INTER_CUBIC), 0, 255)
    ses = MkSession(HF, VF, CARD[2])
    pan, tilt = 0.0, 0.0            # the head (deg)
    goal = [0.0, 0.0]
    vw = None
    if video:
        vw = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W // 2, H // 2))
    err, seen_n, n = [], 0, 0
    t = 0.0
    dt = 1.0 / FPS
    while t <= 60.0:
        img = render(tex, bg, t, pan, tilt, rng, blur)
        obs = det.detect(img)
        n += 1
        if obs is None:
            if det.last is not None and ses.seen_t is not None and t - ses.seen_t > 1.0:
                det.forget()                                    # gone a while: search the whole picture again
        else:
            seen_n += 1
            err.append(math.hypot((obs["cx"] - 0.5) * HF, (obs["cy"] - 0.5) * VF))
        tg = ses.step(t, obs, pan, tilt, W)
        if tg is not None:
            goal = [max(-90, min(90, tg[0])), max(-30, min(45, tg[1]))]
        # the planner: 120 deg/s pan, 90 deg/s tilt (072 defaults) - simple speed limit per frame
        pan += max(-120 * dt, min(120 * dt, goal[0] - pan))
        tilt += max(-90 * dt, min(90 * dt, goal[1] - tilt))
        if vw is not None:
            fr = cv2.cvtColor(cv2.resize(img, (W // 2, H // 2)), cv2.COLOR_GRAY2BGR)
            if obs is not None:
                cv2.polylines(fr, [(obs["pts"] / 2).astype(np.int32)], True, (80, 220, 90), 2)
            cv2.putText(fr, f"t={t:4.1f} {ses.state} pan {pan:5.1f} tilt {tilt:5.1f}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1)
            vw.write(fr)
        t = round(t + dt, 3)
    if vw is not None:
        vw.release()
    # truth for the 3 marks: where the card was while it was turned away
    truth = []
    for s, d in HIDES:
        x, y, z, _ = at(s)
        P = np.array([x, y, z])
        tp, tt = true_dir(P)
        truth.append({"pan": round(tp, 2), "tilt": round(tt, 2), "dist": round(float(np.linalg.norm(P - CAM)), 2)})
    marks = ses.marks
    ok = len(marks) == len(HIDES)
    rows = []
    for m, tr in zip(marks, truth):
        rows.append({"name": m["name"], "pan": m["pan"], "tilt": m["tilt"], "dist": m["dist"], "true": tr,
                     "dpan": round(m["pan"] - tr["pan"], 2), "dtilt": round(m["tilt"] - tr["tilt"], 2),
                     "ddist_pct": round(100 * (m["dist"] / tr["dist"] - 1), 1)})
        ok = ok and abs(m["pan"] - tr["pan"]) < 1.5 and abs(m["tilt"] - tr["tilt"]) < 1.5 and abs(m["dist"] / tr["dist"] - 1) < 0.15
    res = {"blur": blur, "api": det.api, "cv": cv2.__version__, "frames": n, "seen_pct": round(100 * seen_n / n, 1),
           "centre_err_deg_median": round(float(np.median(err)), 2) if err else None, "centre_err_deg_p95": round(float(np.percentile(err, 95)), 2) if err else None,
           "detect_ms_median": round(1000 * float(np.median(det.ms)), 1), "detect_ms_p95": round(1000 * float(np.percentile(det.ms, 95)), 1),
           "beeps": [e for e in ses.events], "marks": rows, "pass": bool(ok)}
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    b = float(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else 0.8
    v = sys.argv[sys.argv.index("--video") + 1] if "--video" in sys.argv else None
    sys.exit(run(b, v))
