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
# ----------------------------------------------------------------------------
class Patrol:
    def __init__(self):
        self.paused_until = 0
        threading.Thread(target=self.loop, daemon=True).start()

    def move_to(self, pan, tilt):
        """Smoothly move pan and tilt together (straight line) at patrol_speed %/s; returns False if interrupted."""
        while True:
            dp, dt = pan - CFG["pan"], tilt - CFG["tilt"]
            dist = math.hypot(dp, dt)
            if dist <= 0.5:
                break
            if not CFG["patrol"] or STATE["tracking"] or servo_hold():
                return False
            f = min(1.0, CFG["patrol_speed"] * 0.02 / dist)
            CFG["pan"] = CFG["pan"] + dp * f
            CFG["tilt"] = CFG["tilt"] + dt * f
            time.sleep(0.02)
        CFG["pan"], CFG["tilt"] = float(pan), float(tilt)
        return True

    def loop(self):
        announced = False
        while True:
            if not CFG["patrol"] or len(WAYPOINTS) < 2:
                STATE["patrol_status"] = "off" if not CFG["patrol"] else "need 2+ waypoints"
                announced = False
                time.sleep(0.3); continue
            if STATE["tracking"]:
                STATE["patrol_status"] = "paused (tracking person)"
                time.sleep(0.2); continue
            if servo_hold():
                STATE["patrol_status"] = "paused (manual control)"
                time.sleep(0.2); continue
            if not announced:
                log_event("patrol", f"Patrol started over {len(WAYPOINTS)} waypoints (pan/tilt): {wp_text()}")
                announced = True
            wps = list(WAYPOINTS)
            # pendulum 1-2-3-2-1 (no doubled end points) or round trip 1-2-3-1-2-3
            path = wps if CFG["patrol_mode"] == "loop" else wps + wps[-2:0:-1]
            for i, wp in enumerate(path):
                STATE["patrol_status"] = f"moving to waypoint {i + 1}/{len(path)} ({wp[0]:.0f}/{wp[1]:.0f})"
                if not self.move_to(wp[0], wp[1]):
                    break
                STATE["patrol_status"] = f"dwelling at {wp[0]:.0f}/{wp[1]:.0f}"
                t_end = time.time() + CFG["patrol_dwell"]
                while time.time() < t_end:
                    if not CFG["patrol"] or STATE["tracking"] or servo_hold():
                        break
                    time.sleep(0.05)
                if not CFG["patrol"] or STATE["tracking"] or servo_hold():
                    break


