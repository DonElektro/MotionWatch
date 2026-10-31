#@ Motion Watch – Teil 350: Verbindung zum Simulator (Schleife). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
def follow_set(on, who="web"):
    """2.98.1: one «Folgen»: the camera keeps what it detects in the middle of the picture - a person first, otherwise an
    animal the AI knows or something that really goes somewhere. (Before, «Folgen» only followed persons; «Bewegung folgen»
    was a separate switch.)"""
    on = bool(on)
    CFG["track_person"] = on; CFG["track_motion"] = on
    sched_user_changed("track_person"); sched_user_changed("track_motion")
    save_settings()
    log_event("servo", f"Following {'ON' if on else 'OFF'} ({who}): persons, animals and moving things are kept in the middle")


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
                        msg_ = "announces itself but does not answer - its firewall or security software blocks MoveEye: use the tunnel"
                except Exception:
                    pass
                SIM.update(ok=False, msg=msg_, errs=SIM["errs"] + 1, since=0.0)
                if SIM["errs"] in (2, 6) and CFG["sim_url"].startswith("http://127.0.0.1:18765"):
                    tunnel_flush()                           # 2.98.11: lines of a simulator that was just updated - only fresh ones
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
                AUDIO.feed_sim(float(rep_["sound_db"]), rep_.get("mic"))   # the sound of the simulated world for the noise alarm (+ «mic»: listening, 558p)
            except Exception:
                pass
        if rep_.get("sound_ev") is not None and AUDIO is not None:   # 2.98.11: claps, sneezes, voices of the simulated world
            try:
                sim_sound_events(rep_["sound_ev"], int(rep_.get("sound_ev_last") or 0), first or int(rep_.get("pid") or 0) != SIM.get("pid_seen"))
            except Exception:
                pass
        if first or int(rep_.get("pid") or 0) != SIM.get("pid_seen"):
            SIM["pid"] = SIM["pid_seen"] = int(rep_.get("pid") or 0)  # its process number: CPU share if it runs on this computer
        SIM.update(t=time.time(), ok=True, dark=bool(rep_.get("dark")), ambient=float(rep_.get("ambient_c", 15.0)),
                   pressure=float(rep_.get("pressure_hpa", 1013.0)), wind=float(rep_.get("wind_kmh", 0.0)), sent=SIM["sent"] + 1,
                   mover=bool(rep_.get("mover")),                # the simulator has a mover (3D-3.11): second stick
                   mover_pose=_mover_pose(rep_.get("mover_pose")) if rep_.get("mover") else None,   # where it is (2.95.43, optional)
                   pc_cpu=rep_.get("pc_cpu"), cores=rep_.get("cores"),   # CPU of the PC the simulator runs on (3D-3.24)
                   sim_cpu=rep_.get("sim_cpu_own"),              # Aufräumen 2: its own share there (tile «CPU of the PC», 470)
                   humidity=rep_.get("humidity"),                # Aufräumen 2: humidity of the scene -> climate sensor (060, field h)
                   solar=rep_.get("solar") if isinstance(rep_.get("solar"), dict) else None,   # 2.98.11: solar panel and
                   gps=rep_.get("gps") if isinstance(rep_.get("gps"), dict) else None)         # GPS module of the simulator   # CPU of the PC the simulator runs on (3D-3.24)
        simvals_take(rep_)                                 # Simulator-Werte: battery, clock, place, forecast, Pi heat, network test (285)
        # 2.98.29: another MoveEye (e.g. the AI helper on the PC, or the Pi) steers the simulator - this one only watches
        SIM["follower"] = bool(rep_.get("follower"))
        SIM["head"] = rep_.get("head_deg") if isinstance(rep_.get("head_deg"), list) else None    # 2.98.35: the simulated head (539 /api/servo)
        weit_from_sim(rep_.get("wide"))                 # 163: the mount of the wide camera (3D-4.17) - «Übersicht lenkt den Kopf» by itself
        SIM["leader"] = str(rep_.get("leader") or "")[:40] if SIM["follower"] else ""   # Aufräumen 2: who steers (shown in the message)
        SIM["msg"] = "connected - only watching (another MoveEye steers the simulator)" if SIM["follower"] else "connected"
        if time.time() - SIMDIARY["t"] >= 30:                # 2.96.1: the diary of the simulator (visits)
            threading.Thread(target=simdiary_poll, daemon=True, name="simdiary").start()
            SIMDIARY["t"] = time.time() - 25                # (the thread sets it again)
        if CFG.get("sim_autoupd", True) and time.time() - SIM.get("upd_check", 0.0) > 60:
            SIM["upd_check"] = time.time()
            threading.Thread(target=sim_auto_update_check, daemon=True, name="simautoupd").start()
        if first:
            SIM["since"] = time.time()
            self.hello()
        g_ = SIMGAME.get("g") or {}
        if g_.get("round") == "play" and WATCH_REF.get("w") is not None:   # 2.98.2: keep the clean picture during a game round
            WATCH_REF["w"].raw_until = max(WATCH_REF["w"].raw_until, time.time() + 3.0)      # (false alarms -> fa_learn)
        mc_ = rep_.get("mw_cmd")                            # 2.95.97: the simulator asks MoveEye for something (button there)
        if isinstance(mc_, dict) and int(mc_.get("id") or 0) > int(SIM.get("cmd_seen") or 0):
            SIM["cmd_seen"] = int(mc_.get("id") or 0)
            if not first:                                   # an old request of before the connection does not count
                op_ = str(mc_.get("op") or "")
                if op_ in ("refscan", "refcompare", "refcompare_day"):
                    refscan_start("scan" if op_ == "refscan" else "compare", "simulator" if op_ != "refcompare_day" else "night test",
                                  "day" if op_ == "refcompare_day" else None)
                elif op_ == "refstop":
                    refscan_stop()
                elif op_ == "look":                         # 2.95.103: «Kopf steuern» in the simulator window
                    move_camera(str(mc_.get("dir") or ""), mc_.get("step", 3), "Simulator")
                elif op_ == "fa_box":                       # 2.98.2: a box of a game without a player: a false alarm to learn from
                    fa_game_box(mc_.get("box"), mc_.get("info"))      # 2.98.18: with the situation («Fehlalarm-Jäger»)
                elif op_ == "track":                        # 2.98.1: «Verfolgen» in the simulator = «Folgen» of MoveEye
                    follow_set(bool(mc_.get("on")), "simulator")
                elif op_ == "light":                        # 2.95.103: the white light from the simulator (on / off)
                    light_set("white", "on" if mc_.get("on") else "auto")
                elif op_ == "ir":                           # 2.98.41: B of the controller in the simulator (one mapping, 542)
                    light_set("ir", "on" if mc_.get("on") else "auto")
                elif op_ == "spieltest_push":               # Spieltest-Assistent: the switch «Spieltest-Meldungen» from the simulator (635a)
                    spieltest_set(bool(mc_.get("on")))
                elif op_ == "feedback":                     # 2.98.33: «Rückmeldung an den Entwickler» in the simulator (584)
                    threading.Thread(target=lambda m=dict(mc_): feedback_send(m.get("kind"), m.get("text"), str(m.get("contact") or "")[:120], True, m.get("stars"),
                                     "3D-Simulator " + str(m.get("sim") or "")[:12], feedback_shot("sim") if m.get("shot") else None, "simulator"),
                                     daemon=True, name="simfeedback").start()
        shut_feed(rep_.get("shut"), first)               # 2.98.35: «Auslöser» hits -> alarm into the test inbox (539)
        horror_feed(rep_.get("horror"), first)           # Bergtal · Horror-Modus: its «recordings» -> Verlauf / Nachrichten (539a)
        spieltest_feed(rep_.get("spieltest"), first)     # Spieltest-Assistent: a short message after every round -> push (635a)
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
#   it is signed together with MoveEye and can be installed without internet.
