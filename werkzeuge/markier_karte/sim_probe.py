#!/usr/bin/env python3
"""«Markier-Karte» against a running MoveEye Sim (prop markierkarte.gd): this script plays MoveEye - it reads the head
camera (/cam/0/snapshot.jpg), finds the marker, steers the head over POST /state (servo pan_deg / tilt_deg, like part 290)
and marks points when the card is turned away. A person carries the A4 card from 3 m to ~14 m and turns it there (beyond the
promised range: expected NO point and no false point), walks to ~7 m and ~5.4 m and marks there (promised: up to ~6 m, both must
give a point within 2.5°). Usage: sim_probe.py http://127.0.0.1:PORT [--shots DIR]"""
import json, math, os, sys, time, urllib.request
import numpy as np
import cv2
from markier_logik import MkDetector, MkSession

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:9471"
SHOTS = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else ""
MID = 42


def ctl(d, timeout=30):
    r = urllib.request.Request(BASE + "/control", json.dumps(d).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read())


def get(path, timeout=10):
    return urllib.request.urlopen(BASE + path, timeout=timeout).read()


PAN = [0.0, 0.0]          # the planner of this «MoveEye»: where the head should be (deg) and the speed limit


def send_state(pan, tilt, goal_p, goal_t, dps=(0.0, 0.0)):
    st = {"v": 1, "t": time.time(), "device": "MarkierTest", "uid": "markier-test:1", "armed": False,
          "servo": {"pan_deg": round(pan, 2), "tilt_deg": round(tilt, 2), "pan_goal": round(goal_p, 2), "tilt_goal": round(goal_t, 2),
                    "pan_dps": dps[0], "tilt_dps": dps[1], "pan_limit": 170, "tilt_limit": 60, "moving": abs(dps[0]) + abs(dps[1]) > 0.1,
                    "track": False, "tracking": False, "estop": False},
          "lights": {"white": False, "ir": False}, "sound": ""}
    r = urllib.request.Request(BASE + "/state", json.dumps(st).encode(), {"Content-Type": "application/json"})
    urllib.request.urlopen(r, timeout=10).read()


def main():
    det = MkDetector()
    if not det.ok:
        print("ArUco fehlt:", det.why); return 2
    info = json.loads(get("/info"))
    cam = next(c for c in info.get("cameras", []) if int(c.get("id", -1)) == 0)
    W, H, HF = int(cam["w"]), int(cam["h"]), float(cam["fov_h"])
    VF = math.degrees(2 * math.atan(math.tan(math.radians(HF) / 2) * H / W))
    a = cv2.aruco
    gen = a.generateImageMarker if hasattr(a, "generateImageMarker") else a.drawMarker
    bits = (gen(det.dic, MID, 6) > 127).astype(int).tolist()
    send_state(0, 0, 0, 0)
    print("hour:", ctl({"action": "set", "id": "hour", "value": 13.0}))
    time.sleep(1.5)
    k0 = ctl({"action": "markierkarte", "do": "on", "bits": bits, "qr": "M1ABCDEXK2345678923", "size": "A4", "pos": [0, -50, 0]})
    hp = np.array(k0["head"]); ry = math.radians(k0["rig_yaw"])
    fwd = np.array([-math.sin(ry), 0, -math.cos(ry)]); right = np.array([math.cos(ry), 0, -math.sin(ry)])
    P = lambda f, r: [float((hp + fwd * f + right * r)[0]), float((hp + fwd * f + right * r)[2])]
    ctl({"action": "markierkarte", "do": "off"})
    # the card walks by itself (moveto, chest height over the ground): the visitors of the scene stop or go round
    # obstacles on their own, the card path stays the same in every run
    st = P(3.0, 0.3)
    k = ctl({"action": "markierkarte", "do": "on", "bits": bits, "qr": "M1ABCDEXK2345678923", "size": "A4", "yaw": 15,
             "pos": [st[0], float(hp[1]), st[1]]})
    ctl({"action": "markierkarte", "do": "moveto", "to": P(14.0, 3.0), "speed": 1.0})
    print("card:", {x: k.get(x) for x in ("dist", "az", "el", "carried")}, "cam", W, H, HF)
    ses = MkSession(HF, VF, 0.180)
    goal = [0.0, 0.0]
    # lockstep: measure how long one round (picture + step) takes in real time, then slow the simulator down so that
    # MoveEye gets about SIM_FPS pictures per simulated second (a slow PC without a graphics card: llvmpipe)
    SIM_FPS = 8.0
    r0 = time.time()
    for _ in range(3):
        get("/cam/0/snapshot.jpg"); ctl({"action": "markierkarte", "do": "step", "pan": 0, "tilt": 0})
    L = (time.time() - r0) / 3
    tempo = max(0.02, min(1.0, 1.0 / (SIM_FPS * L)))
    ctl({"action": "markierkarte", "do": "tempo", "value": tempo})
    print(f"round {L:.2f} s real -> tempo {tempo:.3f}", flush=True)
    c0 = ctl({"action": "markierkarte", "do": "info"})["clock"]
    # event driven: the owner walks, stops (carrier stands 2.5 s), turns the card, walks on
    plan = [("hide", 1.5), ("walk", P(6.8, -2.2)), ("hide", 1.0), ("walk", P(5.0, 2.0)), ("hide", 2.0), ("end", 0)]
    END = 110.0
    still_since, last_pos, ev_t = None, None, 0.0
    rt = []
    log, err, truth_at_hide, nseen, n = [], [], [], 0, 0
    pi = 0
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
    ki = ctl({"action": "markierkarte", "do": "step", "pan": 0, "tilt": 0})
    t = 0.0
    while t < END:
        r_t0 = time.time()
        pos = np.array(ki["pos"])
        if last_pos is not None and np.linalg.norm(pos - last_pos) < 0.03:
            still_since = t if still_since is None else still_since
        else:
            still_since = None
        last_pos = pos
        what, arg = plan[pi]
        stood = still_since is not None and t - still_since >= 2.5
        if what == "hide" and (stood or t - ev_t > 35.0) and t - ev_t > 4.0:
            truth_at_hide.append(ctl({"action": "markierkarte", "do": "hide", "secs": arg}))
            pi += 1; ev_t = t
        elif what == "walk" and t - ev_t > 4.0:
            ctl({"action": "markierkarte", "do": "moveto", "to": arg, "speed": 1.0})
            pi += 1; ev_t = t; still_since = None
        elif what == "end" and t - ev_t > 6.0:
            break
        real_pan = -ki["head_yaw"]; real_tilt = ki["head_pitch"] + 6.0       # main.gd: yaw = -pan, pitch = tilt - 6
        jpg = get("/cam/0/snapshot.jpg", 60)
        img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_GRAYSCALE)
        obs = det.detect(img) if img is not None else None
        n += 1
        if obs is None and det.last is not None and ses.seen_t is not None and t - ses.seen_t > 1.0:
            det.forget()
        if obs is not None:
            nseen += 1
            err.append(math.hypot((obs["cx"] - 0.5) * HF, (obs["cy"] - 0.5) * VF))
        tg = ses.step(t, obs, real_pan, real_tilt, W)
        if tg is not None:
            goal = [max(-90, min(90, tg[0])), max(-30, min(45, tg[1]))]
        log.append({"t": round(t, 2), "seen": obs is not None, "side": round(obs["side"], 1) if obs else None,
                    "dist_true": round(ki["dist"], 2), "pan": round(real_pan, 1), "tilt": round(real_tilt, 1), "state": ses.state})
        if SHOTS and (n % 12 == 0 or obs is None and n % 3 == 0):
            fr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            if obs is not None:
                cv2.polylines(fr, [obs["pts"].astype(np.int32)], True, (80, 220, 90), 2)
            cv2.imwrite(os.path.join(SHOTS, f"sim_{t:05.1f}.jpg"), fr)
        ki = ctl({"action": "markierkarte", "do": "step", "pan": goal[0], "tilt": goal[1]})
        t = ki["clock"] - c0
        rt.append(time.time() - r_t0)
        if n % 20 == 0:
            L = float(np.mean(rt[-20:]))
            tempo = max(0.02, min(1.0, 1.0 / (SIM_FPS * L)))           # keep about SIM_FPS pictures per simulated second
            ctl({"action": "markierkarte", "do": "tempo", "value": tempo})
            print(f"t={t:.1f} n={n} seen={nseen} state={ses.state} marks={len(ses.marks)} dist={ki['dist']:.1f}", flush=True)
    # the truth: direction of the card (relative to the rig) at the moment it was turned away
    tr = []
    for ki in truth_at_hide:
        p = np.array(ki["pos"]); h = np.array(ki["head"]); d = p - h
        az = math.degrees(math.atan2(float(d @ right), float(d @ fwd)))
        el = math.degrees(math.atan2(float(d[1]), math.hypot(float(d @ right), float(d @ fwd))))
        tr.append({"pan": round(az, 2), "tilt": round(el + 6.0, 2), "dist": round(ki["dist"], 2)})   # MoveEye tilt = elevation + 6 (main.gd)
    rows = []
    for m in ses.marks:
        k_ = min(range(len(tr)), key=lambda i: abs(tr[i]["pan"] - m["pan"]) + abs(tr[i]["dist"] - m["dist"]))
        t_ = tr[k_]
        rows.append(dict(m, stop=k_, true=t_, dpan=round(m["pan"] - t_["pan"], 2), dtilt=round(m["tilt"] - t_["tilt"], 2),
                         ddist_pct=round(100 * (m["dist"] / t_["dist"] - 1), 1)))
    good = lambda r: abs(r["dpan"]) < 2.5 and abs(r["dtilt"]) < 2.5
    # stop 0 = ~14 m (beyond range): no point; stops 1 and 2 (~7 m, ~5.4 m, promised): exactly one good point each; no other point
    checks = {"far_no_point": len(tr) == 3 and not [r for r in rows if r["stop"] == 0],
              "mid_7m_point": len([r for r in rows if r["stop"] == 1 and good(r)]) == 1,
              "near_5m_point": len([r for r in rows if r["stop"] == 2 and good(r)]) == 1,
              "no_false_point": len(rows) == len([r for r in rows if r["stop"] in (1, 2) and good(r)])}
    ctl({"action": "markierkarte", "do": "off"})
    res = {"cam": [W, H, HF], "frames": n, "fps_sim": round(n / max(t, 1), 1), "tempo": tempo, "seen_pct": round(100 * nseen / max(n, 1), 1),
           "centre_err_deg_median": round(float(np.median(err)), 2) if err else None,
           "max_dist_seen": max([x["dist_true"] for x in log if x["seen"]] or [0]),
           "detect_ms_median": round(1000 * float(np.median(det.ms)), 1), "beeps": ses.events, "marks": rows, "truth": tr,
           "checks": checks, "pass": all(checks.values())}
    json.dump(log, open(os.path.join(SHOTS or ".", "sim_log.json"), "w"))
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
