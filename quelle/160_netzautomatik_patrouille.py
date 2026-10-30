#@ Motion Watch – Teil 160: Netz-Automatik, Patrouille. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Network automatic: known networks first (e.g. the phone hotspot = internet + push messages), otherwise the own Wi-Fi.
#   start / connection lost: wait auto_wait seconds for a known network, then switch the own Wi-Fi on
#   own Wi-Fi on: every auto_retry minutes look for known networks again - only when no device is connected to the Pi
#   switching by hand (hotspot switch, camping profile) pauses the automatic until the network mode is chosen again
# Timers use time.monotonic(): the clock may jump when it is taken from the phone.
# ----------------------------------------------------------------------------
NETAUTO = {"paused": False, "status": "off"}
NETAUTO_SEARCH = 45.0                                   # seconds the own Wi-Fi stays off while known networks are tried


def netauto_pause():
    if CFG["net_mode"] == "auto" and not NETAUTO["paused"]:
        NETAUTO["paused"] = True
        log_event("sys", "Network automatic paused (switched by hand) - choose the network mode again to resume")


class NetAuto:
    def __init__(self):
        self.lost_since = None; self.next_retry = None
        threading.Thread(target=self.loop, daemon=True).start()

    def _set(self, status):
        if status != NETAUTO["status"]:
            NETAUTO["status"] = status
        STATE["netauto"] = status

    def wait_connected(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            time.sleep(1.0)
            w = STATE["wifi"] or {}
            if w.get("connected") and not STATE["hotspot"].get("on"):
                return w.get("ssid") or "?"
        return ""

    def step(self):
        if CFG["net_mode"] != "auto":
            self.lost_since = None; self.next_retry = None; self._set("off"); return
        if wifi_backend() != "nm":
            self._set("needs NetworkManager"); return
        if NETAUTO["paused"]:
            self._set("paused (switched by hand)"); return
        if WIFI["busy"] or WIFI.get("hs_busy"):
            return
        now = time.monotonic()
        hs, w = STATE["hotspot"] or {}, STATE["wifi"] or {}
        if DUAL["on"]:
            self.lost_since = None; self.next_retry = None
            if not hs.get("on"):
                ok, err = hotspot_set(True, persist=False); hotspot_refresh()
                self._set("own Wi-Fi on" if ok else "own Wi-Fi failed: " + err[:100]); return
            self._set(f"own Wi-Fi on + internet from «{w.get('ssid') or '?'}»" if w.get("connected")
                      else "own Wi-Fi on - the second adapter looks for known networks")
            return
        retry = max(0.0, float(CFG["auto_retry"])) * 60.0
        if hs.get("on"):
            self.lost_since = None
            if retry <= 0:
                self._set("own Wi-Fi on"); return
            if self.next_retry is None:
                self.next_retry = now + retry
            if now < self.next_retry:
                self._set(f"own Wi-Fi on - next search in {max(1, int((self.next_retry - now) / 60 + 0.99))} min"); return
            if hs.get("clients", 0) > 0:
                self.next_retry = now + min(60.0, retry)
                self._set("own Wi-Fi on - search postponed (a device is connected)"); return
            self._set("searching known networks …")
            log_event("sys", "Network automatic: own Wi-Fi off for a moment, looking for known networks")
            hotspot_set(False, persist=False); hotspot_refresh()
            ssid = self.wait_connected(NETAUTO_SEARCH)
            if ssid:
                self.next_retry = None
                log_event("sys", f"Network automatic: connected with «{ssid}»")
                self._set(f"connected with «{ssid}»")
            else:
                hotspot_set(True, persist=False); hotspot_refresh()
                self.next_retry = time.monotonic() + retry
                log_event("sys", "Network automatic: no known network - own Wi-Fi on again")
            return
        if w.get("connected"):
            self.lost_since = None; self.next_retry = None
            self._set(f"connected with «{w.get('ssid') or '?'}»"); return
        if self.lost_since is None:
            self.lost_since = now
        left = float(CFG["auto_wait"]) - (now - self.lost_since)
        if left > 0:
            self._set(f"no known network - own Wi-Fi in {int(left + 0.99)} s"); return
        log_event("sys", "Network automatic: no known network - switching the own Wi-Fi on")
        ok, err = hotspot_set(True, persist=False); hotspot_refresh()       # state at once, not 2 s later
        self.lost_since = None; self.next_retry = time.monotonic() + retry
        self._set("own Wi-Fi on" if ok else "own Wi-Fi failed: " + err[:100])

    def loop(self):
        while True:
            time.sleep(2.0)
            try:
                self.step()
            except Exception as e:
                self._set("error: " + str(e)[:100])


# ----------------------------------------------------------------------------
# Patrol: pendulum over waypoints  (1-2-3-2-1-2-3 ...)
# 2.98.30: «kluge Runde» - the stops come from kopf_patrol_plan() (part 162): the places of «Platz einrichten» with a
# longer stay at the tent and the access, hardly a stop at ignored directions; without places the waypoints. It runs only
# when «Patrouille» is on (aufr, decision Daniel - before also by itself in Wachsam / Voll), pauses while following and gives way to every
# mover with a higher rank (kopf_may). Battery low / deep night: it stays at the most important direction.
# ----------------------------------------------------------------------------
class Patrol:
    def __init__(self):
        self.paused_until = 0
        threading.Thread(target=self.loop, daemon=True).start()

    def _go_on(self):
        return not STATE["tracking"] and not servo_hold() and kopf_may("round") and bool(kopf_patrol_plan()[0])

    def move_to(self, pan, tilt):
        """drive pan and tilt together (straight line) at patrol_speed %/s; returns False if interrupted.
        2.98.35: through the motion planner (072, ramps) - no own ramp any more"""
        return servo_goto(pan, tilt, "round", speed=CFG["patrol_speed"], stop=lambda: not self._go_on())

    def loop(self):
        announced = ""
        while True:
            try:
                plan, why = kopf_patrol_plan()
            except Exception:
                plan, why = [], "off"
            if not plan:
                STATE["patrol_status"] = KOPF["status"] or why
                KOPF["round_on"] = False; announced = ""
                time.sleep(0.3); continue
            if servo_blocked():                           # 2.98.35: Not-Aus / fault / lock (072)
                STATE["patrol_status"] = "paused (servos stopped)"; KOPF["round_on"] = False
                time.sleep(0.3); continue
            if STATE["tracking"]:
                STATE["patrol_status"] = "paused (tracking person)"; KOPF["round_on"] = False
                time.sleep(0.2); continue
            if servo_hold():
                STATE["patrol_status"] = "paused (manual control)"; KOPF["round_on"] = False
                time.sleep(0.2); continue
            if not kopf_may("round"):
                STATE["patrol_status"] = "paused (the head is busy)"; KOPF["round_on"] = False
                time.sleep(0.3); continue
            KOPF["round_on"] = True
            sig = ";".join(f"{p[0]:.0f}/{p[1]:.0f}" for p in plan)
            if announced != sig:
                log_event("patrol", (f"Smart round over {len(plan)} directions: " if any(p[3] for p in plan) else f"Patrol started over {len(plan)} waypoints (pan/tilt): ")
                          + ", ".join((f"{p[3]} {p[2]:.0f}s" if p[3] else f"{p[0]:.0f}/{p[1]:.0f}") for p in plan))
                announced = sig
            # pendulum 1-2-3-2-1 (no doubled end points) or round trip 1-2-3-1-2-3
            path = plan if CFG["patrol_mode"] == "loop" or len(plan) < 3 else plan + plan[-2:0:-1]
            for i, wp in enumerate(path):
                STATE["patrol_status"] = f"moving to waypoint {i + 1}/{len(path)} ({wp[0]:.0f}/{wp[1]:.0f})"
                STATE["patrol_moving"] = True
                ok = self.move_to(wp[0], wp[1])
                STATE["patrol_moving"] = False
                if not ok:
                    break
                STATE["patrol_status"] = (why + " (" + wp[3] + ")") if why else f"dwelling at {(wp[3] + ' ') if wp[3] else ''}{wp[0]:.0f}/{wp[1]:.0f}"
                t_end = time.time() + wp[2]
                while time.time() < t_end:
                    if not self._go_on():
                        break
                    time.sleep(0.05)
                if not self._go_on() or len(plan) == 1:
                    break
