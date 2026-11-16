#!/usr/bin/env python3
"""Prototype of the «📍 Markier-Karte» logic (what the MoveEye part would do), independent of MoveEye:
  * MkDetector: ArUco compat layer (OpenCV >= 4.7 ArucoDetector, 4.6 contrib detectMarkers, none -> unavailable),
    tracking ROI (crop around the last position, enlarged 3x) + full-picture search every few frames.
  * MkSession: the state machine  idle -> follow -> (gap) -> mark | lost -> end, with the beeps as events,
    the follow controller (angle error -> pan / tilt target, like 410 track()), the mark rule and the distance estimate.
Used by sequenz_probe.py (synthetic video) and sim_probe.py (MoveEye Sim); preview only, not part of MoveEye yet."""
import math
import time
import numpy as np
import cv2

MK_DICT = "DICT_4X4_50"
MK_IDS = range(40, 48)            # the id range of this device (one fixed range, the QR / HMAC says it is ours)
MK_ROI = 320                      # px: tracking crop (picture of the head camera), enlarged MK_ROI_K times
MK_ROI_K = 3.0
MK_FULL_EVERY = 4                 # full-picture search every n-th frame while tracking (finds it after a jump)


class MkDetector:
    def __init__(self, dict_name=MK_DICT):
        a = getattr(cv2, "aruco", None)
        self.api = ""
        self.ok = False
        if a is None or not hasattr(a, "getPredefinedDictionary"):
            self.why = "OpenCV without ArUco (opencv-python-headless < 4.7) - install python3-opencv / opencv-contrib"
            return
        self.dic = a.getPredefinedDictionary(getattr(a, dict_name))
        if hasattr(a, "ArucoDetector"):
            p = a.DetectorParameters()
            self._tune(p, a)
            det = a.ArucoDetector(self.dic, p)
            self._det = det.detectMarkers
            self.api = "ArucoDetector"
        else:
            p = a.DetectorParameters_create()
            self._tune(p, a)
            self._det = lambda g: a.detectMarkers(g, self.dic, parameters=p)
            self.api = "detectMarkers (OpenCV 4.6)"
        self.ok = True
        self.why = ""
        self.n = 0
        self.last = None              # (cx, cy, side) in px of the full picture
        self.ms = []

    @staticmethod
    def _tune(p, a):
        p.minMarkerPerimeterRate = 0.012
        p.adaptiveThreshWinSizeMin = 3
        p.adaptiveThreshWinSizeMax = 23
        p.adaptiveThreshWinSizeStep = 10
        p.polygonalApproxAccuracyRate = 0.05
        p.perspectiveRemovePixelPerCell = 8
        p.errorCorrectionRate = 0.6
        if not hasattr(a, "ArucoDetector"):   # OpenCV 4.6: else the white paper edge (narrower than a cell) wins and nothing is read;
            p.minMarkerDistanceRate = 0.01   # 4.7+: not needed, and with it the corners shrink and jitter
        try:
            p.cornerRefinementMethod = a.CORNER_REFINE_SUBPIX
        except AttributeError:
            pass

    def _find(self, gray, x0=0, y0=0, k=1.0):
        corners, ids, _r = self._det(gray)
        out = []
        if ids is None:
            return out
        for c, i in zip(corners, ids.flatten()):
            if int(i) not in MK_IDS:
                continue
            q = c.reshape(4, 2) / k + np.float32([x0, y0])
            out.append((int(i), q))
        return out

    def detect(self, img):
        """-> dict(id, pts (4x2 px), cx, cy (0..1), side px, aspect) or None"""
        t0 = time.perf_counter()
        g = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        H, W = g.shape
        self.n += 1
        found = []
        if self.last is not None:
            cx, cy, side = self.last
            r = int(max(MK_ROI / 2, side * 2.5))
            x0, y0 = int(max(0, min(W - 2 * r, cx - r))), int(max(0, min(H - 2 * r, cy - r)))
            crop = g[y0:y0 + 2 * r, x0:x0 + 2 * r]
            k = max(1.0, min(MK_ROI_K, 60.0 / max(side, 1.0), 640.0 / (2 * r)))   # small marker: enlarge (crop at most 640 px)
            big = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC) if k > 1.0 else crop
            found = self._find(big, x0, y0, k)
        if not found and (self.last is None or self.n % MK_FULL_EVERY == 0):
            found = self._find(g)
            if not found and W >= 1280:                                   # far away: once more on the enlarged middle
                pass
        self.ms.append(time.perf_counter() - t0)
        if not found:
            return None
        i, q = max(found, key=lambda f: cv2.contourArea(f[1]))
        side_v = max(np.linalg.norm(q[0] - q[3]), np.linalg.norm(q[1] - q[2]))     # vertical sides: not shortened by a turn
        side_h = max(np.linalg.norm(q[0] - q[1]), np.linalg.norm(q[3] - q[2]))
        c = q.mean(axis=0)
        self.last = (float(c[0]), float(c[1]), float(side_v))
        return {"id": i, "pts": q, "cx": float(c[0]) / W, "cy": float(c[1]) / H, "side": float(side_v),
                "aspect": float(side_h / max(side_v, 1e-3))}

    def forget(self):
        self.last = None


class MkSession:
    """beeps: «found» (session starts), «mark» (point saved), «lost», «end». Times in s, angles in degrees."""
    GAP_MIN, GAP_MAX = 0.6, 3.0       # card turned away this long = mark
    TURN_REQUIRED = False
    TURN_K = 0.85                     # ... and it was seen turning (narrower than before) just before or after the gap
    LOST_S = 6.0                      # longer away = lost (head stays, beep «verloren»)
    END_S = 90.0                      # no card for this long = the session ends
    DEAD = 0.04                       # dead zone (part of the picture) - like track_deadzone
    GAIN = 0.6

    def __init__(self, hfov, vfov, marker_m, events=None):
        self.hf, self.vf = hfov, vfov
        self.mm = marker_m
        self.state = "idle"
        self.seen_t = None            # last time the card was seen
        self.hist = []                # (t, seen, pan, tilt, ex, ey)
        self.gap_from = None
        self.marks = []
        self.events = events if events is not None else []
        self.settle_t = 0.0
        self.pending = None           # a mark waiting for the head to be centred again
        self.last_mark_t = -99.0

    def beep(self, at, kind, **kw):
        self.events.append(dict(kw, at=round(at, 2), beep=kind))

    def step(self, t, obs, pan, tilt, img_w):
        """one picture: obs = detection or None, pan / tilt = where the head looks now (deg) -> new head target (deg) or None"""
        tgt = None
        seen = obs is not None
        ex = ey = 0.0
        if seen:
            ex, ey = obs["cx"] - 0.5, obs["cy"] - 0.5
        self.hist.append((t, seen, pan, tilt, ex, ey, obs["aspect"] if seen else None))
        self.hist = [h for h in self.hist if t - h[0] < 4.0]
        if self.state == "idle":
            if seen:
                self.state = "follow"
                self.beep(t, "found", id=obs["id"])
            else:
                return None
        if seen:
            if self.gap_from is not None:
                gap = t - self.gap_from
                if self.GAP_MIN <= gap <= self.GAP_MAX and self._stable_before(self.gap_from):
                    # a person walking through hides the card < 0.6 s (GAP_MIN); the narrowing of a turn is only noted
                    # (at 10+ m the turn is often not visible in the pictures - measured in the simulator)
                    self.pending = {"t": t, "gap": round(gap, 2), "before": self._pos_before(self.gap_from),
                                    "turn_seen": bool(self.TURN_REQUIRED is False and self._turned(self.gap_from, obs))}
                    if self.TURN_REQUIRED and not self._turned(self.gap_from, obs):
                        self.pending = None
                        self.beep(t, "no_turn", gap=round(gap, 2))
                elif self.GAP_MIN <= gap <= self.GAP_MAX:
                    self.beep(t, "not_still", gap=round(gap, 2))       # gap like a mark, but the card moved or flickered before: no point
                elif gap > self.LOST_S:
                    self.beep(t, "found_again")
                self.gap_from = None
                self.state = "follow"
            self.seen_t = t
            # follow: turn by the angle the card has from the middle, a part of the way, then let the picture settle
            if t >= self.settle_t and (abs(ex) > self.DEAD or abs(ey) > self.DEAD):
                tgt = (pan + ex * self.hf * self.GAIN, tilt - ey * self.vf * self.GAIN)
                self.settle_t = t + 0.15
            if self.pending is not None and self._stable_after(self.pending["t"], t):
                self._mark(t, obs, pan, tilt, img_w)
        else:
            if self.state == "follow" and self.gap_from is None and self.seen_t is not None:
                self.gap_from = self.seen_t
            if self.gap_from is not None and t - self.gap_from > self.LOST_S and self.state == "follow":
                self.state = "lost"
                self.beep(t, "lost")
            if self.seen_t is not None and t - self.seen_t > self.END_S and self.state != "end":
                self.state = "end"
                self.beep(t, "end")
        return tgt

    def _stable_before(self, tg):
        """the card was seen steadily in the second before it went away (no flicker at the range limit)"""
        h = [x for x in self.hist if tg - 1.0 <= x[0] <= tg]
        if not (len(h) >= 4 and sum(1 for x in h if x[1]) / len(h) >= 0.8):
            return False
        return self._still(tg)

    STILL_DEG = 0.8                   # the owner stands still while marking: the card moved less than this in the last 0.8 s

    def _dirs(self, a, b):
        return [(x[2] + x[4] * self.hf, x[3] - x[5] * self.vf) for x in self.hist if x[1] and a <= x[0] <= b]

    def _still(self, tg):
        d = self._dirs(tg - 0.8, tg)
        if len(d) < 3:
            return False
        p = np.array(d)
        return float(np.max(np.ptp(p, axis=0))) <= 2 * self.STILL_DEG

    def _turned(self, tg, obs):
        """the card got narrower right before it went away, or comes back narrow (it was turned, not covered)"""
        a = [x[6] for x in self.hist if x[1] and tg - 1.5 <= x[0] <= tg - 0.5]
        if len(a) < 2:
            return True                                     # too few pictures to tell: allow
        ref = float(np.median(a))
        near = [x[6] for x in self.hist if x[1] and tg - 0.45 <= x[0] <= tg] + [obs["aspect"]]
        return min(near) < self.TURN_K * ref

    def _stable_after(self, t0, t):
        h = [x for x in self.hist if x[0] >= t0]
        return len(h) >= 3 and all(x[1] for x in h)

    def _same_place(self, before, t0):
        """the card came back where it went away (turned in place, not a walk past something)"""
        d = self._dirs(t0, t0 + 2.0)
        if before is None or not d:
            return False
        p = np.mean(np.array(d), axis=0)
        return abs(p[0] - before[0]) <= 1.5 and abs(p[1] - before[1]) <= 1.5

    def _pos_before(self, tg):
        """where the head looked at the card just before it went away (centre of the picture = the card)"""
        h = [x for x in self.hist if tg - 0.4 <= x[0] <= tg and x[1]]
        if not h:
            return None
        return (float(np.mean([x[2] + x[4] * self.hf for x in h])), float(np.mean([x[3] - x[5] * self.vf for x in h])))

    def _mark(self, t, obs, pan, tilt, img_w):
        p = self.pending
        self.pending = None
        if t - self.last_mark_t < 3.0:
            return
        if not self._same_place(p["before"], p["t"]):
            self.beep(t, "moved", gap=p["gap"])                # it came back somewhere else: no point
            return
        f = (img_w / 2) / math.tan(math.radians(self.hf / 2))
        dist = f * self.mm / max(obs["side"], 1.0)
        ap, at = pan + (obs["cx"] - 0.5) * self.hf, tilt - (obs["cy"] - 0.5) * self.vf     # the card itself, not only the head
        if p["before"] is not None:
            ap, at = 0.5 * (ap + p["before"][0]), 0.5 * (at + p["before"][1])
        if self.marks and abs(self.marks[-1]["pan"] - ap) < 1.0 and abs(self.marks[-1]["tilt"] - at) < 1.0:
            self.beep(t, "same_point")
            return
        n = len(self.marks) + 1
        m = {"name": f"Punkt {n}", "pan": round(ap, 2), "tilt": round(at, 2), "dist": round(dist, 1), "t": round(t, 2), "gap": p["gap"], "turn_seen": p.get("turn_seen")}
        self.marks.append(m)
        self.last_mark_t = t
        self.beep(t, "mark", **m)
