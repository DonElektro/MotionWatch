#@ Motion Watch – Teil 350: Verbindung zum Simulator (Schleife). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
class SimLink:
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True, name="simulator").start()

    def loop(self):
        eco = None
        while True:
            if not CFG["sim_on"]:
                eco = None; time.sleep(0.5); continue
            now_eco = (bool(sim_eco_now()), sim_cam_fps(0))
            if eco is not None and now_eco != eco:                 # CPU saving changed: fetch the head camera again with the new rate
                w = WATCH_REF.get("w")
                if w is not None and str(CFG["source"]).startswith("sim:"):
                    w._open_gen += 1; w._start_opener(CFG["source"])
                    log_event("sys", f"Simulation: {now_eco[1]} pictures per second" if now_eco[0] else "Simulation: CPU saving off")
            eco = now_eco
            t0 = time.time()
            try:
                self.tick()
            except Exception as e:
                msg_ = ("not reachable: " + _short_net_err(e)) if "_short_net_err" in globals() else str(e)[:100]
                try:                                         # 2.95.66: it announces itself (broadcast) but does not answer
                    u_ = urllib.parse.urlsplit(sim_base())
                    f_ = SIMFOUND.get(f"{u_.hostname}:{u_.port or 8765}") or {}
                    if f_ and time.time() - float(f_.get("t") or 0) < 15 and not str(u_.hostname).startswith("127."):
                        msg_ = "announces itself but does not answer - its firewall or security software blocks Motion Watch: use the tunnel"
                except Exception:
                    pass
                SIM.update(ok=False, msg=msg_, errs=SIM["errs"] + 1, since=0.0)
                time.sleep(2.0); continue
            time.sleep(max(0.02, (0.2 if sim_eco_now() else 0.1) - (time.time() - t0)))

    def tick(self):
        body = json.dumps(sim_state()).encode()
        req = urllib.request.Request(sim_base() + "/state", data=body, headers={"Content-Type": "application/json", "User-Agent": "MotionWatch"})
        t_ = time.time()
        with _SIM_OPENER.open(req, timeout=2.0) as r:
            rep_ = json.loads(r.read())
        ms_ = (time.time() - t_) * 1000.0
        SIM["rtt"] = ms_ if not SIM["rtt"] else SIM["rtt"] * 0.9 + ms_ * 0.1
        if not CFG["sim_on"]:
            return                                          # switched off while this request was running
        first = not SIM["ok"]
        if rep_.get("sound_db") is not None and AUDIO is not None:
            try:
                AUDIO.feed_sim(float(rep_["sound_db"]))      # the sound of the simulated world for the noise alarm
            except Exception:
                pass
        if first or int(rep_.get("pid") or 0) != SIM.get("pid_seen"):
            SIM["pid"] = SIM["pid_seen"] = int(rep_.get("pid") or 0)  # its process number: CPU share if it runs on this computer
        SIM.update(t=time.time(), ok=True, msg="connected", dark=bool(rep_.get("dark")), ambient=float(rep_.get("ambient_c", 15.0)),
                   pressure=float(rep_.get("pressure_hpa", 1013.0)), wind=float(rep_.get("wind_kmh", 0.0)), sent=SIM["sent"] + 1,
                   mover=bool(rep_.get("mover")),                # the simulator has a mover (3D-3.11): second stick
                   mover_pose=_mover_pose(rep_.get("mover_pose")) if rep_.get("mover") else None,   # where it is (2.95.43, optional)
                   pc_cpu=rep_.get("pc_cpu"), cores=rep_.get("cores"))   # CPU of the PC the simulator runs on (3D-3.24)
        if CFG.get("sim_autoupd", True) and time.time() - SIM.get("upd_check", 0.0) > 60:
            SIM["upd_check"] = time.time()
            threading.Thread(target=sim_auto_update_check, daemon=True, name="simautoupd").start()
        if first:
            SIM["since"] = time.time()
            self.hello()
        mc_ = rep_.get("mw_cmd")                            # 2.95.97: the simulator asks Motion Watch for something (button there)
        if isinstance(mc_, dict) and int(mc_.get("id") or 0) > int(SIM.get("cmd_seen") or 0):
            SIM["cmd_seen"] = int(mc_.get("id") or 0)
            if not first:                                   # an old request of before the connection does not count
                op_ = str(mc_.get("op") or "")
                if op_ in ("refscan", "refcompare", "refcompare_day"):
                    refscan_start("scan" if op_ == "refscan" else "compare", "simulator" if op_ != "refcompare_day" else "night test",
                                  "day" if op_ == "refcompare_day" else None)
                elif op_ == "refstop":
                    refscan_stop()
        le = int(rep_.get("last_event") or 0)
        if le > SIM["seen_event"]:
            data, _ = _sim_get(f"/events?since={SIM['seen_event']}")
            for e in json.loads(data).get("events", []):
                SIM["seen_event"] = max(SIM["seen_event"], int(e.get("id", 0)))
                src = "sim:" + re.sub(r"[^\w .:+\-]", "_", str(e.get("sensor", "")))[:60]
                sens_seen(src, "Sim: " + str(e.get("sensor", "")), {"kind": e.get("kind")})
                sens_event(src, e.get("active")); SIM["events_n"] += 1

    def hello(self):
        """First contact: the sensors of the simulation become extra sensors (removed again when the simulation is off)."""
        try:
            info = json.loads(_sim_get("/info")[0]); SIM["info"] = info
        except Exception:
            return
        if not CFG["sim_on"]:
            return
        log_event("sys", f"Simulator connected: {info.get('name', '?')} ({len(info.get('cameras') or [])} cameras"
                         + (", thermal camera" if info.get("thermal") else "") + ")")
        new = []
        for x in info.get("sensors") or []:
            src = "sim:" + re.sub(r"[^\w .:+\-]", "_", str(x.get("name", "")))[:60]
            if not any(y["src"] == src for y in CFG["sensors"]):
                new.append({"name": ("Sim " + str(x.get("name", "")))[:24], "kind": x.get("kind") if x.get("kind") in SENS_KINDS else "other", "src": src})
        if new:
            CFG["sensors"] = sens_clean(CFG["sensors"] + new); CFG["sens_on"] = True; save_settings()


SIMLINK = None

# The simulation program itself (motionwatch_simulator.py + motionwatch_sim_interface.py + guide), packed (ZIP, base64):
#   it is signed together with Motion Watch and can be installed without internet.
