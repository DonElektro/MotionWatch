"""Compares what is REALLY in front of the camera (the simulator knows) with what the program SAYS it sees.

Person episodes: a person is clearly visible (inside the picture, big enough, not hidden, enough light). Did the program
report a person during that episode, and how long did it take? False alarms: the program reports a person while no
person is in the picture at all. Tracking: while the program says it tracks, how far is the person from the centre?"""
import time
from collections import deque

from simulator import bridge
from simulator.config import SIM


def person_like(t):
    return t["kind"] == "person" or t["rider"]


class Scoreboard:
    def __init__(self):
        self.lock = __import__("threading").RLock()
        self.reset()

    def reset(self):
        with getattr(self, "lock", __import__("threading").RLock()):
            self.t0 = time.time(); self.last = None
            self.ep = None; self.ep_seen = 0.0
            self.episodes = 0; self.detected = 0; self.missed = 0; self.latencies = []
            self.fa_start = None; self.fa_counted = False; self.false_alarms = 0; self.fa_causes = {}
            self.fa_seconds = 0.0
            self.track_n = 0; self.track_err_sum = 0.0; self.track_good = 0; self.track_max = 0.0; self.track_secs = 0.0
            self.rec_prev = False; self.recordings = 0
            self.rev0 = None
            self.hist = deque(maxlen=600)          # 2 minutes at 5 Hz: (t, truth persons, program persons, tracking, rec)
            self.log = deque(maxlen=200)
            self.now = {}

    def note(self, text):
        self.log.appendleft(time.strftime("%H:%M:%S ") + text)

    def update(self, eng, now):
        if not bridge.ready():                       # no Motion Watch connected: just count what is really there
            self.now = {"truth_persons": sum(1 for t in eng.truth if person_like(t) and t["inside"] > 0.5 and t["px_h"] >= 18),
                        "truth_all": len(eng.truth), "prog_persons": 0, "reversals": 0}
            return
        with self.lock:
            dt = 0.0 if self.last is None else min(1.0, now - self.last)
            self.last = now
            truth = list(eng.truth)
            vis = [t for t in truth if person_like(t) and t["inside"] > 0.5 and t["px_h"] >= 18 and t["hidden"] < 0.7]
            clear = [t for t in vis if t["lit"] > 0.06]
            in_frame = [t for t in truth if person_like(t) and t["inside"] > 0.15]
            prog = int(bridge.state("persons", 0) or 0)
            cam_ok = SIM["cam_connected"] and not SIM["lens_cover"]

            # ---- person episodes ----
            if clear and cam_ok:
                if self.ep is None:
                    self.ep = {"start": now, "det": None, "ids": {t["id"] for t in clear}}
                self.ep_seen = now
                self.ep["ids"] |= {t["id"] for t in clear}
            if self.ep is not None:
                if prog > 0 and self.ep["det"] is None:
                    self.ep["det"] = now
                    self.note(f"person seen by the program after {now - self.ep['start']:.1f} s")
                if not clear and now - self.ep_seen > 2.0:
                    self.episodes += 1
                    if self.ep["det"] is not None:
                        self.detected += 1; self.latencies.append(self.ep["det"] - self.ep["start"])
                    else:
                        self.missed += 1
                        self.note(f"MISSED: person(s) {sorted(self.ep['ids'])} visible {self.ep_seen - self.ep['start']:.1f} s, never reported")
                    self.ep = None

            # ---- false alarms ----
            if prog > 0 and not in_frame:
                self.fa_seconds += dt
                if self.fa_start is None:
                    self.fa_start = now; self.fa_counted = False
                elif not self.fa_counted and now - self.fa_start >= 1.0:
                    self.fa_counted = True; self.false_alarms += 1
                    kinds = sorted({t["kind"] for t in truth if t["inside"] > 0.2}) or ["nothing"]
                    cause = "+".join(kinds)
                    if SIM["rain"] > 0.3:
                        cause += " (rain)"
                    if SIM["wind"] > 0.5:
                        cause += " (wind)"
                    self.fa_causes[cause] = self.fa_causes.get(cause, 0) + 1
                    self.note(f"FALSE ALARM: program reports {prog} person(s), in view: {cause}")
            else:
                self.fa_start = None

            # ---- tracking ----
            tracking = bool(bridge.state("tracking"))
            if tracking:
                self.track_secs += dt
                if vis:
                    err = min(t["center_err"] for t in vis)
                    self.track_n += 1; self.track_err_sum += err; self.track_max = max(self.track_max, err)
                    if err < 10.0:
                        self.track_good += 1

            # ---- recordings / alarms ----
            rec = bool(bridge.state("recording"))
            if rec and not self.rec_prev:
                self.recordings += 1; self.note("recording started")
            self.rec_prev = rec
            rev = eng.servos["pan"].reversals + eng.servos["tilt"].reversals
            if self.rev0 is None:
                self.rev0 = rev
            self.hist.append((now, len(clear), prog, tracking, rec))
            self.now = {"truth_persons": len(clear), "truth_all": len(truth), "prog_persons": prog,
                        "reversals": rev - self.rev0}

    def rows(self):
        """(label, value, colour) lines for the panel."""
        with self.lock:
            mins = max(1e-6, (time.time() - self.t0) / 60.0)
            lat = sorted(self.latencies)
            avg = sum(lat) / len(lat) if lat else None
            rate = 100.0 * self.detected / self.episodes if self.episodes else None
            terr = self.track_err_sum / self.track_n if self.track_n else None
            good = "#2e7d32"; bad = "#c62828"; mid = "#ef6c00"; neutral = ""
            out = [
                ("Persons in view (truth)", str(self.now.get("truth_persons", 0)), neutral),
                ("Persons reported (program)", str(self.now.get("prog_persons", 0)),
                 good if self.now.get("prog_persons", 0) == self.now.get("truth_persons", 0) else mid),
                ("Person episodes", f"{self.episodes}  (detected {self.detected}, missed {self.missed})", neutral),
                ("Detection rate", "–" if rate is None else f"{rate:.0f} %", neutral if rate is None else good if rate >= 90 else mid if rate >= 70 else bad),
                ("Time to detect (avg / worst)", "–" if avg is None else f"{avg:.1f} s / {lat[-1]:.1f} s", neutral if avg is None else good if avg < 2.5 else mid if avg < 5 else bad),
                ("False alarms", f"{self.false_alarms}  ({self.fa_seconds:.0f} s total)", good if self.false_alarms == 0 else bad),
                ("False alarm causes", ", ".join(f"{k} x{v}" for k, v in self.fa_causes.items()) or "–", neutral),
                ("Tracking time", f"{self.track_secs:.0f} s", neutral),
                ("Tracking error (avg / max)", "–" if terr is None else f"{terr:.1f}° / {self.track_max:.1f}°", neutral if terr is None else good if terr < 8 else mid if terr < 15 else bad),
                ("Person kept within 10°", "–" if not self.track_n else f"{100.0 * self.track_good / self.track_n:.0f} %", neutral),
                ("Servo direction changes / min", f"{self.now.get('reversals', 0) / mins:.0f}", neutral if self.now.get("reversals", 0) / mins < 40 else mid),
                ("Recordings started", str(self.recordings), neutral),
            ]
            return out
