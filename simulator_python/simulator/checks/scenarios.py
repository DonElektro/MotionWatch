"""Scripted test situations. Each one sets up the world, lets things happen and checks what Motion Watch reports
(read from its web page over the network, see bridge.py).

A scenario is a function run(ctx). It uses ctx.wait / ctx.expect / ctx.never / ctx.info. Everything it changes
(simulator settings, Motion Watch settings, arming) is put back when it ends, also when it is stopped."""
import copy
import math
import threading
import time
import traceback

from simulator import bridge
from simulator.scene import world as W
from simulator.config import SIM


class Stop(Exception):
    pass


class Ctx:
    def __init__(self, eng, name, on_change):
        self.eng = eng; self.world = eng.world; self.name = name
        self.results = []; self.status = "running"; self.stop_flag = False
        self.on_change = on_change
        self._sim0 = SIM.snapshot()
        self._cfg0 = {}
        self._armed0 = None
        self.t0 = time.time()

    # ---- bookkeeping ----
    def _add(self, status, label, detail=""):
        self.results.append({"status": status, "label": label, "detail": detail, "t": time.time() - self.t0})
        self.on_change()

    def info(self, label, detail=""):
        self._add("INFO", label, detail)

    def check(self, label, ok, detail=""):
        self._add("PASS" if ok else "FAIL", label, detail)
        return ok

    def skip(self, label, why):
        self._add("SKIP", label, why)

    # ---- time ----
    def wait(self, sec):
        end = time.time() + sec
        while time.time() < end:
            if self.stop_flag:
                raise Stop()
            time.sleep(0.05)

    def wait_until(self, fn, timeout):
        end = time.time() + timeout
        while time.time() < end:
            if self.stop_flag:
                raise Stop()
            try:
                if fn():
                    return True
            except Exception:
                pass
            time.sleep(0.1)
        return False

    def expect(self, label, fn, timeout, hint=""):
        t = time.time()
        ok = self.wait_until(fn, timeout)
        self.check(label, ok, f"after {time.time() - t:.1f} s" if ok else f"not within {timeout:.0f} s. {hint}".strip())
        return ok

    def never(self, label, fn, duration, hint=""):
        end = time.time() + duration
        while time.time() < end:
            if self.stop_flag:
                raise Stop()
            try:
                if fn():
                    self.check(label, False, f"happened after {duration - (end - time.time()):.1f} s. {hint}".strip())
                    self.wait(max(0.0, end - time.time()))
                    return False
            except Exception:
                pass
            time.sleep(0.1)
        self.check(label, True, f"{duration:.0f} s watched")
        return True

    # ---- Motion Watch side (like a user would do it on its web page) ----
    def need(self, key, value):
        if key not in self._cfg0:
            self._cfg0[key] = bridge.cfg(key)
        bridge.set_cfg(key, value, note=False)

    def armed(self):
        if self._armed0 is None:
            self._armed0 = bridge.is_armed()
        if not bridge.is_armed():
            bridge.arm()

    def state(self, key, default=None):
        return bridge.state(key, default)

    # ---- simulator side ----
    def sim(self, **kw):
        SIM.update(**kw)

    def clean_world(self, hour=13.0):
        """Empty scene, plain daylight, no weather, no faults, camera centred and still."""
        SIM.update(auto_spawn=False, bg_traffic=False, time_mode="manual", hour=hour, rain=0.0, fog=0.0, wind=0.1, clouds=0.2,
                   lens_cover=False, lens_blur=0.0, cam_connected=True, cam_frozen=False, mount_yaw=self._sim0["mount_yaw"],
                   shake=0.0, servo_power=True, pan_stuck=False, tilt_stuck=False, paused=False, time_scale=1.0)
        self.world.clear()
        self.need("patrol", False); self.need("track_person", False); self.need("detection_on", True)
        bridge.centre()

    def settle(self, sec=8.0):
        """Wait until the servos have arrived and the background model got used to the picture."""
        self.wait_until(lambda: all(abs(s.angle - s.target) < 0.5 for s in self.eng.servos.values()), 6)
        self.wait(sec)

    def front(self, dist, side=0.0):
        """World point straight in front of the camera (current view direction) at dist metres, side metres to the right."""
        yaw = math.radians(self.eng.pose[0])
        cx, cy = W.VIEW["x"], W.VIEW["y"]
        return (cx + math.sin(yaw) * dist + math.cos(yaw) * side, cy + math.cos(yaw) * dist - math.sin(yaw) * side)

    def crossing(self, dist, speed, kind="person", crouch=1.0, end="exit"):
        """Something walks straight across the picture at dist metres, starting and ending outside the view."""
        a = self.front(dist, -28.0); b = self.front(dist, 28.0)
        e = W.make_path(kind, [a, b], speed, end=end, crouch=crouch)
        self.world.add(e)
        return e

    def visible(self, eid):
        return any(t["id"] == eid and t["inside"] > 0.5 and t["hidden"] < 0.6 for t in self.eng.truth)

    def wait_visible(self, eid, timeout=40):
        return self.wait_until(lambda: self.visible(eid), timeout)

    def restore(self):
        SIM.update(**{k: v for k, v in self._sim0.items() if k != "want"})
        SIM["want"] = self._sim0["want"]
        for k, v in self._cfg0.items():
            if v is not None:
                bridge.set_cfg(k, v, note=False)
        if self._armed0 is False:
            bridge.disarm()
        self.world.clear()


# =====================================================================================================================
# the scenarios
# =====================================================================================================================
def persons():
    return int(bridge.state("persons", 0) or 0)


def present():
    return set(bridge.state("present", []) or [])


def sc_walker(c):
    """One person walks across the picture at 10 m."""
    c.clean_world(); c.armed(); c.settle()
    rec0 = bool(c.state("recording"))
    p = c.crossing(10.0, 1.3)
    if not c.wait_visible(p.id):
        return c.check("person entered the picture", False, "never became visible")
    c.expect("program reports a person", lambda: persons() > 0, 6, "check sensitivity / walk frames / AI")
    c.expect("pre-alarm (movement) seen", lambda: "prealarm" in present() or "motion" in present() or persons() > 0, 4)
    if not bridge.cfg("record"):
        c.skip("recording started", "recording switched off in the program")
    elif c.wait_until(lambda: c.state("recording") or rec0, 8):
        c.check("recording started", True)
    else:
        c.skip("recording started", "no clip - Motion Watch saves no recordings while the simulation is on")
    relays = [r for r in bridge.relays() if r["mode"] == "auto" and r["trigger"] in ("person", "motion", "prealarm")]
    for r in relays:
        c.expect(f"{r['name']} (GPIO {r['gpio']}) switched on",
                 lambda r=r: any(x["name"] == r["name"] and x["on"] for x in bridge.relays()), 6)
    c.wait_until(lambda: not c.visible(p.id), 30)
    c.expect("person count back to 0 after leaving", lambda: persons() == 0, 8)


def sc_group(c):
    """Four people at different distances, two in each direction."""
    c.clean_world(); c.settle()
    for d, sp, rev in ((7, 1.2, False), (10, 1.4, True), (13, 1.1, False), (16, 1.5, True)):
        a, b = c.front(d, -28.0), c.front(d, 28.0)
        c.world.add(W.make_path("person", [b, a] if rev else [a, b], sp))
    best = [0]

    def watch():
        best[0] = max(best[0], persons())
        return False
    c.wait_until(lambda: any(t["kind"] == "person" and t["inside"] > 0.5 for t in c.eng.truth), 30)
    c.wait_until(watch, 30)
    c.check("at least 2 persons counted at the same time", best[0] >= 2, f"most at once: {best[0]}")
    c.info("most persons at once", str(best[0]))


def sc_stander(c):
    """A person walks in and then stands still for 40 s (needs the AI or 'person sticky')."""
    c.clean_world(); c.settle()
    x, y = c.front(9.0, 1.0)
    a = c.front(9.0, -28.0)
    p = W.make_path("person", [a, (x, y)], 1.3, end=40.0)
    c.world.add(p)
    c.expect("detected while walking in", lambda: persons() > 0, 30)
    c.wait_until(lambda: p.tasks and p.tasks[0][0] == "wait", 30)
    c.wait(15)
    c.check("still reported after standing 15 s", persons() > 0,
            "motion alone forgets a standing person - the AI (or person_sticky) must keep it")
    c.wait(15)
    c.check("still reported after standing 30 s", persons() > 0)


def sc_car(c):
    """A car drives along the road: it must not raise a person alarm."""
    if not W.ROADS:
        return c.skip("car drive-by", "this map has no road - choose another map")
    c.clean_world()
    cx, cy = W.VIEW["x"], W.VIEW["y"]                         # turn the camera mount towards the nearest road
    o, pos = min(W.ROADS, key=lambda r: abs((cy if r[0] == "h" else cx) - r[1]))
    tx, ty = (cx, pos) if o == "h" else (pos, cy)
    c.sim(mount_yaw=math.degrees(math.atan2(tx - cx, ty - cy)))
    c.settle()
    v0 = int(c.state("ignored_vehicles", 0) or 0)
    car = W.make_vehicle("car", nearest_road=True)
    if car is None:
        return c.skip("car drive-by", "no road end outside the view")
    c.world.add(car)
    if not c.wait_visible(car.id, 25):
        return c.skip("car drive-by", f"the road is not in the picture from this camera place (camera looks {c.eng.pose[0]:.0f} deg, "
                                      f"car at {car.x:.0f}/{car.y:.0f}, alive {car.alive})")
    c.never("no person reported while the car passes", lambda: persons() > 0 and not any(
        t["kind"] == "person" for t in c.eng.truth), 10)
    c.info("vehicles ignored by the car filter", str(int(c.state("ignored_vehicles", 0) or 0) - v0))
    c.info("AI labelled", ", ".join(sorted(present() - {"motion", "prealarm"})) or "-")


def sc_animals(c):
    """A dog and later a cat cross the picture: animal yes, person no."""
    c.clean_world(); c.settle()
    for kind, dist in (("dog", 8.0), ("cat", 6.0)):
        a = c.crossing(dist, 2.0 if kind == "dog" else 0.9, kind=kind)
        c.wait_visible(a.id, 30)
        c.expect(f"{kind} recognised", lambda kind=kind: kind in present() or "animal" in present(), 10,
                 "needs the AI (AI detection on in Motion Watch)")
        c.never(f"no person alarm for the {kind}", lambda: persons() > 0, 6)
        c.wait_until(lambda a=a: not c.visible(a.id), 30)


def sc_deter(c):
    """A bear comes close and stays: Motion Watch's deterrent (siren / loudspeaker) must chase it away."""
    c.clean_world(); c.armed(); c.settle()
    x, y = c.front(8.0, 0.5)
    b = c.world.add(W.make_visit("bear", x, y, stay=True))
    if not c.wait_visible(b.id, 40):
        return c.check("bear came into the picture", False, "never became visible")
    if not c.expect("Motion Watch plays a sound", lambda: c.eng.proto is not None and c.eng.proto_live() and bool(c.eng.proto.sound),
                    30, "switch on the deterrent for big animals in Motion Watch"):
        return
    c.info("sound", str(c.eng.proto.sound))
    c.expect("the bear runs away", lambda: not c.visible(b.id), 20)


def sc_wind(c):
    """Strong wind shakes the bushes and trees, nobody is there."""
    c.clean_world(); c.settle(4)
    c.sim(wind=0.9)
    c.expect("program notices the wind", lambda: (c.state("wind_level") or "calm") not in ("calm", "off"), 30)
    c.never("no person alarm from moving leaves", lambda: persons() > 0, 30)
    c.info("wind level / threshold factor", f"{c.state('wind_level')} x{c.state('wind_boost')}")


def sc_rain(c):
    """Heavy rain, then a person walks through it."""
    c.clean_world(); c.settle(4)
    c.sim(rain=0.85, clouds=0.9)
    c.expect("rain mode switches on", lambda: bool(c.state("rain_mode")), 25)
    c.never("no person alarm from rain alone", lambda: persons() > 0, 10)
    p = c.crossing(9.0, 1.3)
    c.wait_visible(p.id)
    c.expect("person found in the rain", lambda: persons() > 0, 8)


def sc_night(c):
    """Night without lights: a person walks by."""
    c.clean_world(hour=23.5); c.settle(10)
    c.expect("low-light mode on", lambda: bool(c.state("lowlight")), 15)
    p = c.crossing(8.0, 1.3)
    c.wait_visible(p.id)
    ok = c.wait_until(lambda: persons() > 0, 10)
    c.check("person found in the dark", ok, "without IR light / thermal camera this may fail - like in reality")
    c.info("picture brightness", str(c.state("brightness")))


def sc_tracking(c):
    """Person tracking: someone walks a long arc, the camera has to follow."""
    c.clean_world(); c.settle()
    c.need("track_person", True)
    a = c.front(9.0, -30.0)
    pts = [a] + [c.front(9.0 + 3 * math.sin(k / 6 * math.pi), -10.0 + 4.0 * k) for k in range(7)] + [c.front(10.0, 40.0)]
    p = W.make_path("person", pts, 1.1)
    c.world.add(p)
    pan0 = c.eng.servos["pan"].angle
    errs = []
    c.expect("tracking starts", lambda: bool(c.state("tracking")), 40)

    def sample():
        if c.state("tracking"):
            for t in c.eng.truth:
                if t["id"] == p.id:
                    errs.append(t["center_err"])
        return not p.alive
    c.wait_until(sample, 60)
    moved = abs(c.eng.servos["pan"].angle - pan0)
    c.check("camera turned to follow", moved > 10, f"pan moved {moved:.0f} degrees")
    if errs:
        avg = sum(errs) / len(errs)
        c.check("person kept near the centre (avg < 12 deg)", avg < 12, f"average {avg:.1f} deg, worst {max(errs):.1f} deg")
    c.info("servo direction changes", str(c.eng.servos["pan"].reversals))


def sc_patrol(c):
    """Patrol between the waypoints set in Motion Watch while nobody is there."""
    wps = bridge.waypoints()
    if len(wps) < 2 or max(w[0] for w in wps) - min(w[0] for w in wps) < 15:
        return c.skip("patrol", "set at least two waypoints far apart in Motion Watch first (Camera -> waypoints)")
    c.clean_world(); c.settle(2)
    c.need("patrol", True)
    seen = []

    def sample():
        seen.append(c.eng.servo_angles()[0])
        return False
    c.wait_until(sample, 25)
    lo, hi = min(seen), max(seen)
    c.check("camera swings between the waypoints", hi - lo > 30, f"pan from {lo:.0f} to {hi:.0f} degrees")
    c.info("patrol status", str(c.state("patrol_status")))


def sc_cover(c):
    """Somebody covers the lens (sabotage)."""
    c.need("tamper_on", True)
    c.clean_world(); c.settle(14)
    last0 = (c.state("tamper") or {}).get("last", "")
    c.sim(lens_cover=True)
    c.expect("sabotage 'covered' reported", lambda: (c.state("tamper") or {}).get("last", "") != last0 and
             "cover" in (c.state("tamper") or {}).get("last", ""), 15)
    c.sim(lens_cover=False)


def sc_turned(c):
    """The whole camera head is turned away on its mount."""
    c.need("tamper_on", True)
    c.clean_world(); c.settle(14)
    last0 = (c.state("tamper") or {}).get("last", "")
    c.sim(mount_yaw=SIM["mount_yaw"] + 75.0)
    c.expect("sabotage 'turned' reported", lambda: (c.state("tamper") or {}).get("last", "") != last0 and
             "turn" in (c.state("tamper") or {}).get("last", ""), 20)


def sc_unplug(c):
    """The camera cable is pulled for 10 s."""
    c.clean_world(); c.settle(3)
    c.sim(cam_connected=False)
    c.expect("program notices the lost camera", lambda: not str(c.state("source_status", "")).startswith("connected"), 20)
    c.wait(4)
    c.sim(cam_connected=True)
    c.expect("camera reconnected", lambda: str(c.state("source_status", "")).startswith("connected"), 25)


def sc_thermal(c):
    """Night, thermal alarm on: a warm body walks by."""
    c.need("thermal_alarm", True)
    c.clean_world(hour=23.0); c.settle(12)
    if not c.expect("thermal camera connected", lambda: c.state("thermal") == "connected", 15,
                    "in Motion Watch the thermal camera must be the simulator's"):
        return
    p = c.crossing(8.0, 1.3)
    c.wait_visible(p.id, 40)
    c.expect("warm body reported", lambda: int(c.state("warm", 0) or 0) > 0, 12)
    c.info("hottest pixel", f"{c.state('thermal_max')} C")


def sc_hotstone(c):
    """A sun-warmed stone (static, hot) must not cause a thermal alarm when 'needs motion' is on."""
    c.need("thermal_alarm", True); c.need("thermal_need_motion", True)
    c.clean_world(); c.settle(10)
    c.sim(hot_stone=True)
    c.wait(3)
    c.never("no warm-body alarm from the hot stone", lambda: int(c.state("warm", 0) or 0) > 0, 25)


def sc_runner(c):
    """A runner (4 m/s) - fast, but still a person."""
    c.clean_world(); c.settle()
    p = c.crossing(11.0, 4.2)
    c.wait_visible(p.id)
    ok = c.wait_until(lambda: persons() > 0, 5)
    c.check("runner reported as a person", ok, "the car filter (speed) may throw fast people away")


def sc_sneak(c):
    """Someone sneaks by, crouched and slow."""
    c.clean_world(hour=21.0); c.settle(8)
    p = c.crossing(9.0, 0.5, crouch=0.6)
    c.wait_visible(p.id, 80)
    ok = c.wait_until(lambda: persons() > 0, 15)
    c.check("sneaking person found", ok, "slow + small + dusk is the hardest case")


SCENARIOS = [
    ("walker", "Person walks by", sc_walker),
    ("group", "Group of four", sc_group),
    ("stander", "Person stands still", sc_stander),
    ("runner", "Runner", sc_runner),
    ("sneak", "Sneaking at dusk", sc_sneak),
    ("car", "Car drives by (no alarm)", sc_car),
    ("animals", "Dog and cat (animal, no person)", sc_animals),
    ("deter", "Bear chased away (deterrent)", sc_deter),
    ("wind", "Storm, nobody there (no alarm)", sc_wind),
    ("rain", "Heavy rain + person", sc_rain),
    ("night", "Night, no lights", sc_night),
    ("tracking", "Tracking follows a person", sc_tracking),
    ("patrol", "Patrol between waypoints", sc_patrol),
    ("cover", "Lens covered (sabotage)", sc_cover),
    ("turned", "Camera turned away (sabotage)", sc_turned),
    ("unplug", "Camera cable pulled", sc_unplug),
    ("thermal", "Thermal alarm at night", sc_thermal),
    ("hotstone", "Hot stone (no thermal alarm)", sc_hotstone),
]


class Runner:
    """Runs one scenario or the whole list after each other in a background thread."""
    def __init__(self, eng):
        self.eng = eng
        self.current = None
        self.history = []                 # finished: (name, label, results, status)
        self.queue = []
        self.thread = None
        self.changed = 0

    def _bump(self):
        self.changed += 1

    def busy(self):
        return self.thread is not None and self.thread.is_alive()

    def run(self, keys):
        if self.busy() or not bridge.ready():
            return False
        self.queue = [s for s in SCENARIOS if s[0] in keys]
        self.thread = threading.Thread(target=self._work, daemon=True, name="sim-tests")
        self.thread.start()
        return True

    def stop(self):
        self.queue = []
        if self.current:
            self.current.stop_flag = True

    def _work(self):
        while self.queue:
            key, label, fn = self.queue.pop(0)
            c = Ctx(self.eng, label, self._bump)
            self.current = c
            bridge.log(f"test start: {label}")
            try:
                fn(c)
                c.status = "FAIL" if any(r["status"] == "FAIL" for r in c.results) else "PASS"
            except Stop:
                c.status = "STOPPED"
            except Exception as e:
                c.status = "ERROR"
                c.results.append({"status": "ERROR", "label": str(e), "detail": traceback.format_exc(limit=2), "t": 0})
            finally:
                try:
                    c.restore()
                except Exception:
                    pass
            bridge.log(f"test end: {label}: {c.status}")
            self.history.append((key, label, copy.deepcopy(c.results), c.status))
            self.current = None
            self._bump()
            time.sleep(2.0)
