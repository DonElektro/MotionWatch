#@ MoveEye – Teil 074: Servo-Selbstdiagnose wie bei einer Robotersteuerung: Fehlerspeicher, Betriebsstunden, gefahrene Grad und Bewegungen pro Achse, Wartungshinweise, Export. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.35 (Wunsch Daniel): the planner (072) counts per axis: degrees travelled, seconds moving, number of moves; the servo
#   loop counts the operating time. Real servos («hw») and the simulation («sim») are counted apart - the maintenance
#   hints only use the real ones. Fault memory (Fehlerspeicher): I2C errors, the PCA9685 lost its settings (brown-out),
#   no driver, limit hits, under-voltage, temperature, throttling, watchdog, Not-Aus / release - the same code within
#   10 minutes is one entry with a counter (no flood), at most 300 entries.
# Memory card (067): <data>/servo_diag.json is written at most every 15 minutes (and at once for a fault, at most once a
#   minute) and at the end of the program.
# Pages: Mehr → Werkzeuge → «Servo diagnosis» (/servo#diag, part 539) and the window (588), export as JSON or CSV.
# ----------------------------------------------------------------------------
for _k, _v in {"servo_service_h": 100.0}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
SVD = {"d": None, "dirty": False, "saved_t": 0.0, "fault_save_t": 0.0, "lock": threading.Lock(), "atexit": False}
SVD_SAVE_S = 900
SVD_MAX_FAULTS = 300
SVD_LEVELS = ("info", "warn", "error")


def _svd_file():
    return os.path.join(DATA_DIR, "servo_diag.json")


def _svd_axis():
    return {"deg": 0.0, "move_s": 0.0, "moves": 0}


def _svd_bucket():
    return {"on_s": 0.0, "uv_min": 0, "pan": _svd_axis(), "tilt": _svd_axis()}


def _svd_blank():
    return {"v": 1, "since": time.time(), "hw": _svd_bucket(), "sim": _svd_bucket(),
            "service": {"pan": 0.0, "tilt": 0.0, "t": 0.0}, "faults": []}


def servo_diag_data():
    if SVD["d"] is None:
        d = None
        try:
            with open(_svd_file()) as f:
                d = json.load(f)
        except (OSError, ValueError):
            d = None
        b = _svd_blank()
        if isinstance(d, dict):
            for k in ("hw", "sim"):
                if isinstance(d.get(k), dict):
                    for kk in ("on_s", "uv_min"):
                        if isinstance(d[k].get(kk), (int, float)):
                            b[k][kk] = d[k][kk]
                    for ax in SERVO_AXES:
                        if isinstance(d[k].get(ax), dict):
                            for kk in ("deg", "move_s", "moves"):
                                if isinstance(d[k][ax].get(kk), (int, float)):
                                    b[k][ax][kk] = d[k][ax][kk]
            if isinstance(d.get("service"), dict):
                b["service"].update({k: float(v) for k, v in d["service"].items() if k in ("pan", "tilt", "t") and isinstance(v, (int, float))})
            if isinstance(d.get("since"), (int, float)):
                b["since"] = d["since"]
            b["faults"] = [x for x in (d.get("faults") or []) if isinstance(x, dict) and x.get("code")][-SVD_MAX_FAULTS:]
        SVD["d"] = b
        if not SVD["atexit"]:
            SVD["atexit"] = True
            atexit.register(lambda: servo_diag_save(True))
    return SVD["d"]


def servo_diag_save(force=False):
    d = SVD["d"]
    if d is None or not (SVD["dirty"] or force):
        return
    try:
        with SVD["lock"]:
            tmp = _svd_file() + ".tmp"
            with open(tmp, "w") as f:
                json.dump(d, f)
            os.replace(tmp, _svd_file())
        SVD["dirty"] = False; SVD["saved_t"] = time.time()
    except OSError:
        pass


def _svd_cur():
    sim = bool(CFG.get("sim_on")) or str(STATE.get("servo_backend") or "simulation").startswith("simulation")
    return servo_diag_data()["sim" if sim else "hw"]


def servo_diag_count(dt, vel):
    """the planner (072), every step: operating time, degrees and seconds moving per axis"""
    b = _svd_cur()
    if not servo_outputs_off():
        b["on_s"] += dt
    for i, ax in enumerate(SERVO_AXES):
        v = abs(vel[i])
        if v > 0.01:
            b[ax]["deg"] += v * dt / _srv_k(ax)
            b[ax]["move_s"] += dt
    SVD["dirty"] = True
    if time.time() - SVD["saved_t"] > SVD_SAVE_S:
        SVD["saved_t"] = time.time()
        threading.Thread(target=servo_diag_save, daemon=True, name="servodiag-save").start()


def servo_diag_move_start():
    b = _svd_cur()
    for i, ax in enumerate(SERVO_AXES):
        if abs(SRV["vel"][i]) > 0.01:
            b[ax]["moves"] += 1


def servo_diag_count_uv():
    _svd_cur()["uv_min"] += 1


def servo_diag_fault(code, level="warn", text=""):
    """one entry in the fault memory - the same code and text within 10 min only counts up"""
    d = servo_diag_data()
    now = time.time()
    level = level if level in SVD_LEVELS else "warn"
    text = str(text or "")[:160]
    with SVD["lock"]:
        for f in reversed(d["faults"][-20:]):
            if f.get("code") == code and f.get("text") == text and now - float(f.get("last", 0)) < 600:
                f["n"] = int(f.get("n", 1)) + 1; f["last"] = round(now, 1)
                break
        else:
            d["faults"].append({"t": round(now, 1), "last": round(now, 1), "code": code, "level": level, "text": text, "n": 1,
                                "sim": bool(CFG.get("sim_on"))})
            del d["faults"][:-SVD_MAX_FAULTS]
    SVD["dirty"] = True
    if level == "error" and now - SVD["fault_save_t"] > 60:
        SVD["fault_save_t"] = now
        threading.Thread(target=servo_diag_save, daemon=True, name="servodiag-save").start()


def servo_diag_clear_faults(by="web"):
    d = servo_diag_data()
    with SVD["lock"]:
        d["faults"] = []
    SVD["dirty"] = True; servo_diag_save(True)
    log_event("servo", f"Servo fault memory cleared ({by})")


def servo_diag_service_done(axis="", by="web"):
    """«Wartung erledigt»: the maintenance counter of one axis (or both) starts again"""
    d = servo_diag_data()
    for ax in SERVO_AXES:
        if axis in ("", ax):
            d["service"][ax] = d["hw"][ax]["move_s"]
    d["service"]["t"] = time.time()
    SVD["dirty"] = True; servo_diag_save(True)
    log_event("servo", f"Servo maintenance done ({axis or 'both axes'}, {by})")
    servo_diag_fault("service", "info", f"maintenance done: {axis or 'pan + tilt'}")


def _h(s):
    return round(float(s) / 3600.0, 2)


def servo_diag_hints(lang=None):
    """maintenance hints from the counters and the fault memory (already translated)"""
    d = servo_diag_data()
    out = []
    T = lambda x: tr(x, lang)
    lim = max(5.0, float(CFG.get("servo_service_h") or 100.0))
    for ax, name in (("pan", "Pan servo"), ("tilt", "Tilt servo")):
        h = _h(d["hw"][ax]["move_s"] - float(d["service"].get(ax) or 0.0))
        if h >= lim:
            out.append(("warn", trf("{axis} (MG90S): {h} h moved since the last check - check it now: play in the gears, noise, does it hold the position?", lang, axis=T(name), h=f"{h:.1f}")))
        elif h >= lim * 0.8:
            out.append(("info", trf("{axis} (MG90S): {h} h moved - check after about {lim} h (play, noise).", lang, axis=T(name), h=f"{h:.1f}", lim=f"{lim:.0f}")))
    cnt = {}
    week = time.time() - 7 * 86400
    for f in d["faults"]:
        if float(f.get("last", 0)) >= week and not f.get("sim"):
            cnt[f["code"]] = cnt.get(f["code"], 0) + int(f.get("n", 1))
    if cnt.get("uv") or cnt.get("pca_reset") or d["hw"]["uv_min"] > 0 and cnt.get("uv"):
        out.append(("warn", T("Under-voltage / brown-out: give the servos their own 5 V supply (BEC, at least 2 A), put a 470–1000 µF capacitor at V+ of the PCA9685 and use a short, thick cable.")))
    if cnt.get("i2c"):
        out.append(("warn", T("I2C errors: check the 4 wires to the PCA9685 (short, firmly plugged), the address 0x41 and that I2C is on (raspi-config).")))
    if cnt.get("limit", 0) >= 20:
        out.append(("info", T("The head often runs into the software limit: widen the limit (Camera / Servos) or move the taught points a little inwards.")))
    if cnt.get("temp") or cnt.get("throttle"):
        out.append(("info", T("The Pi gets hot or slows down: shade, air holes in the housing, a heat sink.")))
    if cnt.get("wd_cam") or cnt.get("wd_loop"):
        out.append(("info", T("The watchdog stopped the servos: the computer was too busy - see the log; fewer AI pictures or the AI helper on the PC help.")))
    if d["hw"]["on_s"] < 60 and (d["sim"]["on_s"] > 0):
        out.append(("info", T("Only the simulation so far - the counters of the real servos start with the hardware.")))
    return out


def servo_diag_state(lang=None):
    d = servo_diag_data()
    lim = max(5.0, float(CFG.get("servo_service_h") or 100.0))

    def bucket(b, service=None):
        ax = {}
        for a in SERVO_AXES:
            x = b[a]
            ax[a] = {"deg": int(round(x["deg"])), "move_h": _h(x["move_s"]), "moves": int(x["moves"]),
                     "turns": round(x["deg"] / 360.0, 1)}
            if service is not None:
                ax[a]["service_h"] = _h(x["move_s"] - float(service.get(a) or 0.0))
                ax[a]["service_pct"] = int(min(100, round(ax[a]["service_h"] / lim * 100)))
        return {"on_h": _h(b["on_s"]), "uv_min": int(b["uv_min"]), "axes": ax}
    faults = []
    for f in reversed(d["faults"][-100:]):
        faults.append({"t": f["t"], "last": f.get("last", f["t"]), "code": f["code"], "level": f.get("level", "warn"), "n": int(f.get("n", 1)),
                       "what": tr(SRV_FAULT_TEXT.get(f["code"], f["code"]), lang), "text": f.get("text", ""), "sim": bool(f.get("sim"))})
    return {"since": d["since"], "hw": bucket(d["hw"], d["service"]), "sim": bucket(d["sim"]), "service_t": d["service"].get("t") or 0,
            "service_h": lim, "faults": faults, "n_faults": len(d["faults"]),
            "hints": [{"level": l, "text": t} for l, t in servo_diag_hints(lang)]}


def servo_diag_export(fmt="json", lang=None):
    """(bytes, mimetype, file name) - everything for the developer / a service note"""
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    st = {"app": "MoveEye", "version": APP_VERSION, "device": CFG.get("device_name") or "MoveEye", "t": datetime.now().isoformat(timespec="seconds"),
          "servo": servo_state(lang), "diag": servo_diag_state(lang), "points": teach_list(lang),
          "settings": {k: CFG.get(k) for k in ("servo_driver", "pca_address", "pca_pan_ch", "pca_tilt_ch", "servo_min_us", "servo_max_us",
                                               "servo_range", "pan_servo_range", "servo_kind", "pan_limit", "tilt_limit", "invert_pan", "invert_tilt",
                                               "servo_vmax_pan", "servo_vmax_tilt", "servo_acc_pan", "servo_acc_tilt", "servo_estop_park",
                                               "servo_uv_stop", "servo_wd_s", "servo_service_h")}}
    if fmt == "csv":
        lines = ["time;last;code;level;count;sim;what;text"]
        for f in st["diag"]["faults"]:
            ts = lambda x: datetime.fromtimestamp(float(x)).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(";".join([ts(f["t"]), ts(f["last"]), f["code"], f["level"], str(f["n"]), "1" if f["sim"] else "0",
                                   f["what"].replace(";", ","), str(f["text"]).replace(";", ",")]))
        lines.append("")
        for k in ("hw", "sim"):
            b = st["diag"][k]
            lines.append(f"{k};on_h;{b['on_h']};uv_min;{b['uv_min']}")
            for a in SERVO_AXES:
                x = b["axes"][a]
                lines.append(f"{k};{a};deg;{x['deg']};move_h;{x['move_h']};moves;{x['moves']}")
        return ("\n".join(lines) + "\n").encode("utf-8-sig"), "text/csv", f"moveeye_servo_{stamp}.csv"
    return json.dumps(st, ensure_ascii=False, indent=1).encode("utf-8"), "application/json", f"moveeye_servo_{stamp}.json"


def servo_diag_selftest():
    keep = SVD["d"]
    try:
        SVD["d"] = _svd_blank()
        servo_diag_fault("i2c", "warn", "x"); servo_diag_fault("i2c", "warn", "x"); servo_diag_fault("uv", "warn", "")
        f = SVD["d"]["faults"]
        assert len(f) == 2 and f[0]["n"] == 2, f
        SVD["d"]["hw"]["pan"]["move_s"] = 3600.0 * float(CFG.get("servo_service_h") or 100)
        for x in f:
            x["sim"] = False
        hs = servo_diag_hints("de")
        assert any("MG90S" in t for _l, t in hs) and any("BEC" in t or "Unterspannung" in t for _l, t in hs), hs
        b, mt, fn = servo_diag_export("csv")
        assert mt == "text/csv" and b"i2c" in b and fn.endswith(".csv")
        servo_diag_service_done("pan", "test") if False else None
    finally:
        SVD["d"] = keep; SVD["dirty"] = False
    return "fault memory (counted up), maintenance hints, CSV export"
