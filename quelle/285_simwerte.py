#@ MoveEye – Teil 285: Simulator-Werte (Akku, Uhrzeit, Ort, Wetter, Pi-Wärme, Netz-Ausfall) aus dem 3D-Simulator statt vom Pi. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026): while MoveEye is connected to the 3D simulator, the «hardware» readings come from the
# simulated world, not from the Pi. Before (kept): solar panel, GPS (+ theft), outside temperature / pressure / wind (storm),
# sound, thermal camera, head position, door / PIR / gas / bike sensors, darkness. New here (the simulator sends them in its
# answer to /state, simulator3d/scripts/power.gd -> SIM, taken in 350 SimLink.tick -> simvals_take):
#   battery   the simulated UPS HAT -> 100 BatteryMonitor (charge, time left, power cut / back, «almost empty», battery
#             saver 105, shutdown limit). «Empty» never shuts this computer down: MoveEye says what the device would do.
#   clock     the time of the scene -> sim_now(): schedules (030), night report (090), night time / «Heute Nacht bewachen»
#             and «Lagerfeuer bis» (130), night forecast + sunrise (280), battery forecast (066), the quiet night of the
#             sneeze answer (250), the timeline night (425), the solar day (280).
#             NOT for: log lines, file names, signatures, update checks, user time windows (041), backups - real time.
#             Sightings keep their real time stamps; sim_to_real() turns a simulated night into the real time span in which
#             the simulator ran through it (night report, timeline).
#   place     sun times (sun_times_here: schedules «dark» / «light», night forecast, diary day) use the place of the scene.
#   forecast  gusts and weather of the scene instead of Open-Meteo (060 weather_loop makes no internet call while connected,
#             280 storm_forecast_gust, the diary day 060 day_summary).
#   pi_temp   the CPU temperature of the simulated Pi -> STATE["cpu_temp"] (100 SysMonitor): heat warning, AI slower (180),
#             servo diagnosis (072), turbo (130), MQTT / devices. STATE["cpu_temp_real"] keeps the real value (run guard 390).
#   net       «WLAN weg» / «Internet weg» test of the simulator -> 110 online check (offline), 060 Notifier: alarms go to
#             the outbox and are sent later («nachgeschickt»), other messages fail like for real; nothing on the real network.
# After 10 s without an answer (simulator off / gone) everything is real again by itself (sim_live). STATE["simvals"] says
# which values come from the simulator - the web page and the window show «🧪 Simulator» there (part 598).
# ----------------------------------------------------------------------------
SIMVAL = {"live": False, "map": [], "net": "", "off": False, "off_t": 0.0, "temp_warned": False}


def simval_live():
    """the simulator is on and answered in the last 10 s"""
    return bool(CFG.get("sim_on")) and time.time() - float(SIM.get("t", 0.0)) <= 10      # a short hiccup (one failed request) does not count


def simvals_take(rep):
    """350 SimLink.tick: the new values of one answer of the simulator"""
    for k in ("battery", "clock", "place", "forecast", "net"):
        SIM[k] = rep.get(k) if isinstance(rep.get(k), dict) else None
    try:
        SIM["pi_temp"] = float(rep["pi_temp"]) if rep.get("pi_temp") is not None else None
    except (TypeError, ValueError):
        SIM["pi_temp"] = None
    try:
        st = sim_now().timestamp()
        M = SIMVAL["map"]; now = time.time()
        if not M or now - M[-1][0] >= 20 or abs((st - M[-1][1]) - (now - M[-1][0]) * float((SIM.get("clock") or {}).get("speed") or 1.0)) > 300:
            M.append((now, st))
            del M[:-3000]                                  # about 16 hours at one point per 20 s
    except Exception:
        pass


def sim_now():
    """The time of the simulated world while connected (the simulator sends date + hour; between two answers it runs on
    with the speed of the time-lapse) - otherwise the real local time. Only for decisions about day and night (see top)."""
    c = sim_sensor("clock")
    if c is None:
        return datetime.now()
    try:
        d = datetime.strptime(str(c["date"])[:10], "%Y-%m-%d")
        h = float(c["hour"]) % 24.0 + max(0.0, time.time() - float(SIM.get("t", 0.0))) * float(c.get("speed") or 1.0) / 3600.0
        return d + timedelta(hours=h)
    except (KeyError, TypeError, ValueError):
        return datetime.now()


def sim_to_real(dt):
    """A moment of the simulated clock -> the real time at which the simulator showed it (from the points of this
    connection). Not connected / unknown: unchanged. Before the first point: the first point."""
    if not simval_live() or not SIMVAL["map"]:
        return dt
    M = SIMVAL["map"]; s = dt.timestamp()
    if float((SIM.get("clock") or {}).get("speed") or 1.0) <= 1.0 and abs(sim_now().timestamp() - time.time()) < 120:
        return dt                                           # the simulator runs on the real clock: nothing to turn
    if s >= M[-1][1]:
        return datetime.fromtimestamp(min(time.time(), M[-1][0] + (s - M[-1][1]) / max(1.0, float((SIM.get("clock") or {}).get("speed") or 1.0))))
    for i in range(len(M) - 1, 0, -1):
        (r0, s0), (r1, s1) = M[i - 1], M[i]
        if s0 <= s <= s1 and s1 > s0:
            return datetime.fromtimestamp(r0 + (r1 - r0) * (s - s0) / (s1 - s0))
        if s1 < s0:                                         # the clock was set back here: older points are another night
            return datetime.fromtimestamp(r1)
    return datetime.fromtimestamp(M[0][0])


def sim_place():
    """(lat, lon, name) of the scene while connected, else None"""
    p = sim_sensor("place")
    try:
        return (float(p["lat"]), float(p["lon"]), str(p.get("name") or "")) if p else None
    except (KeyError, TypeError, ValueError):
        return None


def here_latlon():
    p = sim_place()
    return (p[0], p[1]) if p else (float(CFG["latitude"]), float(CFG["longitude"]))


def sun_times_here(d):
    """sun_times (030) for the place of MoveEye - or of the simulated scene, in the time zone of the scene"""
    lat, lon = here_latlon()
    st = sun_times(d, lat, lon)
    c = sim_sensor("clock") if sim_place() else None
    if c is not None and isinstance(st, tuple):
        try:
            loc = datetime(d.year, d.month, d.day, 12).astimezone().utcoffset().total_seconds() / 60.0
            off = float(c.get("tz_h", 1.0)) * 60.0 - loc
            st = (st[0] + off, st[1] + off)
        except (OverflowError, OSError, ValueError, TypeError):
            pass
    return st


def sim_forecast():
    return sim_sensor("forecast")


SIM_WX = {"clear": ("☀️", "clear"), "cloudy": ("☁️", "cloudy"), "fog": ("🌫", "fog"), "rain": ("🌧", "rain"), "snow": ("🌨", "snow")}


def sim_weather_day(lang=None):
    """the weather of the scene for the diary day (instead of Open-Meteo)"""
    f = sim_forecast()
    if not f:
        return None
    icon, key = SIM_WX.get(str(f.get("weather")), ("🌤", "partly cloudy"))
    return {"icon": icon, "text": tr(key, lang), "tmax": f.get("tmax"), "tmin": f.get("tmin"), "rain": None,
            "wind": round(float(SIM.get("wind") or 0.0)), "gust": f.get("gust_kmh"), "hourly": {}, "sim": True}


def sim_pi_temp():
    if not simval_live():
        return None
    return SIM.get("pi_temp")


def sim_net_down():
    """'wifi' / 'internet' while the simulator plays «WLAN weg» / «Internet weg», else ''"""
    n = sim_sensor("net")
    if not n:
        return ""
    return "wifi" if n.get("wifi") is False else ("internet" if n.get("internet") is False else "")


def simnet_hold(nf, p, jpg, fname):
    """060 Notifier._dispatch while the simulator plays a network outage: like a failed send - an alarm waits in the
    outbox (sent later, also into the test inbox), other messages are lost (as for real). Nothing goes out."""
    ev = nf._event(p)
    alarm = ev in ("person", "tamper", "warm", "noise")
    why = sim_net_down()
    STATE["notify_status"] = "error: " + ("no Wi-Fi" if why == "wifi" else "no internet") + " (simulator)"
    log_event("web", f"Notification not sent - {'Wi-Fi' if why == 'wifi' else 'internet'} gone (simulator test)")
    msglog_add(nf._title(p), push_with_map(nf._text(p), p, " · "), ev, jpg, "failed", "🧪 " + ("no Wi-Fi" if why == "wifi" else "no internet"))
    if alarm and not p.get("late"):
        outbox_add(dict(p, sandbox=bool(sandbox_active() or p.get("_test"))), jpg, fname)


def simvals_tick():
    """once a second (100 SysMonitor): what comes from the simulator (STATE["simvals"]) and the change back to real"""
    live = simval_live()
    if live != SIMVAL["live"]:
        SIMVAL["live"] = live
        if live:
            log_event("sys", "Simulator values: battery, clock, place, weather and Pi temperature come from the simulator")
        else:
            log_event("sys", "Simulator values ended - the real sensors and the real clock apply again")
            SIMVAL["map"] = []
            if SIMVAL["off"]:
                SIMVAL["off"] = False
    nd = sim_net_down() if live else ""
    if nd != SIMVAL["net"]:
        SIMVAL["net"] = nd
        log_event("sys", ("Simulator test: Wi-Fi gone" if nd == "wifi" else "Simulator test: internet gone") if nd else "Simulator test: network back")
        w = WATCH_REF.get("w")
        try:
            w.netmon.recheck = True                          # the online check (110) at once
        except Exception:
            pass
        if not nd:
            OUTBOX["kick"] = True                            # waiting alarms out at once
            if "(simulator)" in str(STATE.get("notify_status") or ""):
                STATE["notify_status"] = ""                  # no «push problem» afterwards: the outage was only the test
    if not live:
        STATE["simvals"] = {"on": False}
        return
    now = sim_now(); pl = sim_place(); b = sim_sensor("battery")
    keys = [k for k, ok in (("battery", b is not None), ("clock", sim_sensor("clock") is not None), ("place", pl is not None),
                            ("weather", sim_forecast() is not None), ("pi_temp", SIM.get("pi_temp") is not None),
                            ("solar", bool(CFG.get("solar_on")) and sim_sensor("solar") is not None),
                            ("gps", bool(CFG.get("gpsmod_on")) and sim_sensor("gps") is not None), ("net", sim_sensor("net") is not None)) if ok]
    STATE["simvals"] = {"on": True, "keys": keys, "time": now.strftime("%H:%M"), "date": now.strftime("%Y-%m-%d"),
                        "speed": float((SIM.get("clock") or {}).get("speed") or 1.0), "dark": bool(SIM.get("dark")),
                        "place": pl[2] if pl else "", "lat": pl[0] if pl else None, "lon": pl[1] if pl else None,
                        "weather": (sim_forecast() or {}).get("weather"), "net": nd, "pi_temp": SIM.get("pi_temp"),
                        "off": bool(SIMVAL["off"]), "sched": [s["name"] for s in SCHEDULES if schedule_active(s, now)] if SCHEDULES else []}


def sim_battery_tick(bm, sb):
    """100 BatteryMonitor.tick with the simulated UPS HAT: the same display and the same reactions as the real HAT (E)"""
    try:
        v, a, pct = float(sb["v"]), float(sb["a"]), int(sb["pct"])
    except (KeyError, TypeError, ValueError):
        return False
    on_batt = bool(sb.get("on_battery", True)) and not bool(sb.get("charging") and sb.get("mains"))
    charging = bool(sb.get("charging"))
    cap_wh = float(sb.get("cap_wh") or 0.0)
    use_w = float(sb.get("load_w") or 0.0)
    ml = sb.get("min_left")
    hours = round(float(ml) / 60.0, 1) if on_batt and ml else (round(pct / 100.0 * cap_wh / max(0.8, use_w), 1) if on_batt and cap_wh else None)
    STATE["battery"] = {"on": True, "src": "ups", "model": "sim", "sim": True, "pct": pct, "hours": hours, "cap_wh": round(cap_wh, 1),
                        "use_w": round(use_w, 1), "watts": round(use_w, 1), "volt": round(v, 2), "amps": round(a, 2), "on_battery": on_batt,
                        "charging": charging, "full": bool(sb.get("full")), "temp": sb.get("temp"), "solar_w": sb.get("solar_w"),
                        "full_min": None}
    if not getattr(bm, "_sim_seen", False):
        bm._sim_seen = True
        log_event("sys", f"Simulated UPS HAT (simulator): battery {v:.2f} V, {pct} %")
    bm.ups_events(v, pct, hours, on_batt, False)          # volt_ok False: never the real shutdown of this computer
    lim = int(CFG["ups_shutdown_pct"])
    drill_ = drill_active("battery") if "drill_active" in globals() else False   # 565: the drill «battery empty» never «shuts down»
    if not SIMVAL["off"] and on_batt and lim > 0 and (pct <= lim or sb.get("empty")) and not drill_:
        SIMVAL["off"] = True; SIMVAL["off_t"] = time.time()
        log_event("sys", f"Battery empty ({pct} %, {v:.2f} V) - the Pi would shut down now (simulator: this computer stays on)")
        w = WATCH_REF.get("w")
        if w is not None and CFG["ups_push"]:
            w.notifier.info(tr("Battery empty – the Pi shuts down cleanly") + " (🧪 " + tr("simulator") + ")", title="{name}: " + tr("power"))
    elif SIMVAL["off"] and (pct >= lim + 10 or not on_batt):
        SIMVAL["off"] = False
        log_event("sys", f"Battery charged again ({pct} %) - the Pi would start again (simulator)")
    STATE["battery"]["sim_off"] = bool(SIMVAL["off"])
    return True
