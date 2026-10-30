#@ MoveEye – Teil 163a: Status-LED (RGB auf PCA9685 Kanal 5/6/7) oben auf dem Kopf und zwei Tasten am Gerät («Schutz», «Alarm quittieren») – Farben pro Zustand, Alarm blinkt rot bis quittiert, Störung violett, Erkennung kurz, Blinki-Zwinkern als «alles ok», Nacht gedimmt; im Simulator LED und Tasten des Simulators. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Decisions Daniel 30.10.2026 21:55 (docs/Gehaeuse_Variante2_Weitwinkel.md, «Status-LED oben auf dem Kopf»):
#   * one RGB LED on the head, on the PCA9685 of the servos (channels 5 / 6 / 7 = red / green / blue; 0 / 1 servos,
#     2 / 3 white / IR, 4 wide IR), common cathode or common anode, brightness by PWM (gamma corrected)
#   * what it shows, the first that applies wins:
#       test (button «LED testen», 6 s) > alarm (red blinking until acknowledged) > fault (short violet pulses: battery
#       low, under-voltage, camera lost, servo fault) > detection flash (short white, for tests, default off) > the colour
#       of the state (Aus green, Wachsam orange, Voll red - editable; while arming the colour breathes) > the heartbeat
#       «Blinki-Zwinkern» (a short double blink every few minutes = all is well; not at night, not after a fault)
#   * night (dark - the simulator's night while connected): dimmed or off (setting); alarm stays bright
#   * the web page lets Blinki blink at the same moment (STATE["led"]["hb"] counts the heartbeats, 599c)
#   * two buttons (GPIO, internal pull-up, to ground; debounce; long press 1.5 s):
#       «Schutz»            short: Wachsam <-> Aus, long: Voll
#       «Alarm quittieren»  stops the siren and the escalation, ends the red blinking
#     every press is logged. A PIN for disarming (135) is respected: then the buttons can switch the protection ON, but
#     not off, and they do not silence the siren while protected (a thief at the device could otherwise) - setting
#     «btn_pin_rule». The operator mode (390) does not limit arming (the operator may), so it does not limit the buttons.
#   * simulator (sim_on and it answers): the LED is the one on the simulated head (sim_state «led», 599c) and the presses
#     come from the simulator's buttons (world_reply «buttons», 599c) - the real GPIO / PCA channels rest meanwhile.
# Settings, web page, window, simulator hooks, self-test: 599c. Texts: 639f.
# ----------------------------------------------------------------------------
LED_DEFAULTS = {
    "led_on": True, "led_ch_r": 5, "led_ch_g": 6, "led_ch_b": 7, "led_common": "cathode", "led_bright": 60,
    "led_col_off": "green", "led_col_watch": "orange", "led_col_full": "red",
    "led_night": "dim", "led_night_bright": 8, "led_alarm_blink": True, "led_fault_pulse": True, "led_det_flash": False,
    "led_heartbeat": True, "led_hb_min": 5,
    "btn_on": False, "btn_gpio_protect": "5", "btn_gpio_ack": "6", "btn_long_s": 1.5, "btn_debounce_ms": 50, "btn_pin_rule": "pin_arm_only",
}
for _k, _v in LED_DEFAULTS.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

# the colours: what the RGB LED gets (0..1 per channel) and how a page draws it (hex)
LED_RGB = {"green": (0.0, 1.0, 0.0), "orange": (1.0, 0.32, 0.0), "red": (1.0, 0.0, 0.0), "yellow": (1.0, 0.75, 0.0),
           "blue": (0.0, 0.2, 1.0), "turquoise": (0.0, 0.85, 0.65), "violet": (0.55, 0.0, 1.0), "white": (1.0, 1.0, 1.0), "off": (0.0, 0.0, 0.0)}
LED_HEX = {"green": "#2fd35a", "orange": "#ff8a1f", "red": "#ff2a2a", "yellow": "#ffd21f", "blue": "#3b7bff", "turquoise": "#1fd8bf",
           "violet": "#a64dff", "white": "#ffffff", "off": "#000000"}
LED_COLOURS = tuple(LED_RGB)
LED_STATE_NAMES = {"off": "Off", "watch": "Watchful", "full": "Full protection"}
LED_LAYER_NAMES = {"test": "LED test", "alarm": "Alarm", "fault": "Fault", "flash": "Detection", "state": "", "heartbeat": "Blinki blink",
                   "deny": "Refused", "dark": "off"}
LED_TEST_SEQ = ("red", "green", "blue", "white", "@off", "@watch", "@full")
LED_TEST_STEP = 0.8
LED_FAULT_RE = re.compile(r"UNDER-VOLTAGE|Battery almost empty|Battery empty|Camera stopped delivering|Servo error|Servo fault|"
                          r"Light error|PCA9685 .*(not|lost)|thermal camera lost|No picture from the camera")
LED_ALARM_KINDS = ("person", "warm", "noise", "sensor", "tamper", "refscan", "theft")
LED = {"alarm": False, "alarm_kind": "", "alarm_t": 0.0, "fault_t0": -1e9, "fault_until": 0.0, "fault_reason": "", "fault_seen": {},
       "flash_t0": 0.0, "flash_until": 0.0, "flash_col": "white", "flash_hz": 0.0, "hb_n": 0, "hb_t": -1e9, "hb_wall": 0.0, "hb_next": None,
       "test_t0": -1e9, "det_prev": 0, "srv_fault_prev": "", "armed_prev": None, "last": None, "hw": "none", "presses": deque(maxlen=12),
       "frame": None, "sim": False}
LED_LOCK = threading.Lock()


def led_now():
    return time.monotonic()


def _led_int(k, lo, hi):
    try:
        return max(lo, min(hi, int(float(CFG.get(k, LED_DEFAULTS.get(k, lo))))))
    except (TypeError, ValueError):
        return int(LED_DEFAULTS.get(k, lo))


def led_colour(k):
    c = str(CFG.get(k) or LED_DEFAULTS.get(k, "off"))
    return c if c in LED_RGB else str(LED_DEFAULTS.get(k, "off"))


def led_level():
    """off / watch / full and whether the countdown runs («arming»)"""
    try:
        lv = protect_level()
    except NameError:
        lv = "watch" if CFG.get("armed") else "off"
    if not CFG.get("armed"):
        lv = "off"
    return lv, STATE.get("arm_state") == "arming"


# ---- events -----------------------------------------------------------------------------------------------------------
def led_alarm(kind):
    """an alarm while protected: red blinking until acknowledged (button, web, window, or switching the protection off)"""
    with LED_LOCK:
        if not LED["alarm"]:
            LED.update(alarm=True, alarm_t=led_now(), alarm_kind=str(kind))
        else:
            LED["alarm_kind"] = str(kind)


def led_ack(src="web"):
    """«Alarm quittieren»: the red blinking ends, the siren stops, the escalation (siren after a while) is cancelled"""
    was = LED["alarm"]
    with LED_LOCK:
        LED["alarm"] = False
    playing = bool(SOUND.get("playing")) if "SOUND" in globals() else False
    try:
        sound_stop()
    except NameError:
        pass
    try:
        protect_cancel_escalation()
    except NameError:
        pass
    LIGHTS["strobe_until"] = 0.0
    log_event("sys", f"Alarm acknowledged ({src})" + (" - siren stopped" if playing else "") + ("" if was else " - no alarm was shown"))
    return True


def led_fault(reason):
    """a short violet pulse (about 2 s) - at most once a minute per reason"""
    now = led_now()
    k = str(reason)[:40]
    if now - float(LED["fault_seen"].get(k, -1e9)) < 60.0:
        return False
    LED["fault_seen"][k] = now
    LED.update(fault_t0=now, fault_until=now + 2.1, fault_reason=k)
    return True


def led_flash(col="white", seconds=0.35, hz=0.0):
    now = led_now()
    LED.update(flash_t0=now, flash_until=now + float(seconds), flash_col=col if col in LED_RGB else "white", flash_hz=float(hz))


def led_test():
    LED["test_t0"] = led_now()
    log_event("sys", "Status LED: test (all colours)")
    return True


# ---- the frame: which colour now (pure apart from CFG / LED, the clock is passed in - self-test with a fake clock) --------
def led_frame(now, level="off", arming=False, dark=False):
    """-> {"col": colour name or None, "rgb": (r, g, b) 0..1, "br": 0..1, "layer": ...} - starts the heartbeat when due"""
    on = bool(CFG.get("led_on", True))
    br_day = _led_int("led_bright", 1, 100) / 100.0
    night = bool(dark) and CFG.get("led_night", "dim") != "normal"
    br = (_led_int("led_night_bright", 1, 100) / 100.0) if night else br_day

    def out(col, b, layer, rgb=None):
        return {"col": col, "rgb": rgb if rgb is not None else LED_RGB.get(col, (0.0, 0.0, 0.0)), "br": max(0.0, min(1.0, b)) if col != "off" else 0.0,
                "layer": layer}
    if not on:
        return out("off", 0.0, "dark")
    t = now - LED["test_t0"]
    if 0.0 <= t < LED_TEST_STEP * len(LED_TEST_SEQ):
        c = LED_TEST_SEQ[int(t / LED_TEST_STEP)]
        c = led_colour("led_col_" + c[1:]) if c.startswith("@") else c
        return out(c, br_day, "test")
    if LED["alarm"] and CFG.get("led_alarm_blink", True):
        ph = (now - LED["alarm_t"]) * 2.0                 # 2 blinks a second, bright also at night
        return out("red" if (ph % 1.0) < 0.5 else "off", max(br_day, 0.6), "alarm")
    if now < LED["fault_until"] and CFG.get("led_fault_pulse", True):
        ph = (now - LED["fault_t0"]) % 0.7                 # three soft pulses
        k = math.sin(math.pi * ph / 0.45) if ph < 0.45 else 0.0
        return out("violet" if k > 0.02 else "off", br * k, "fault")
    if now < LED["flash_until"]:
        if LED["flash_hz"] > 0 and ((now - LED["flash_t0"]) * LED["flash_hz"]) % 1.0 >= 0.5:
            return out("off", 0.0, "flash")
        return out(LED["flash_col"], max(br, 0.25), "deny" if LED["flash_hz"] > 0 else "flash")
    col = led_colour("led_col_" + (level if level in LED_STATE_NAMES else "off"))
    if night and CFG.get("led_night") == "off":
        return out("off", 0.0, "dark")
    b = br
    if arming:                                            # the countdown: the colour of the coming state breathes
        b = br * (0.25 + 0.75 * (0.5 + 0.5 * math.sin(now * 2.0 * math.pi / 1.6)))
    # heartbeat «Blinki-Zwinkern»: a short double blink every few minutes - all is well (not at night, not after a fault)
    per = _led_int("led_hb_min", 1, 120) * 60.0
    if LED["hb_next"] is None or LED["hb_next"] - now > per:
        LED["hb_next"] = now + per                        # first frame, or a shorter period was just set
    if CFG.get("led_heartbeat", True) and not night and not arming:
        if now >= LED["hb_next"]:
            LED["hb_next"] = now + per
            if now - LED["fault_t0"] > per and not LED.get("srv_fault_prev"):     # not after / during a fault
                LED["hb_t"] = now; LED["hb_n"] += 1; LED["hb_wall"] = time.time()
        h = now - LED["hb_t"]
        if 0.0 <= h < 0.6:
            dark_ph = h < 0.15 or 0.3 <= h < 0.45            # «Zwinkern»: closed - open - closed - open
            if col == "off":
                return out("green" if dark_ph else "off", br, "heartbeat")
            return out("off" if dark_ph else col, b, "heartbeat")
    elif now >= (LED["hb_next"] or 0.0):
        LED["hb_next"] = now + per
    return out(col, b, "state")


def led_tick(now=None):
    """called 50 × a second by the hardware loop (080 via the wrapper below): the events of the device, then the frame"""
    now = led_now() if now is None else now
    lv, arming = led_level()
    armed = bool(CFG.get("armed"))
    if LED["armed_prev"] is not None and LED["armed_prev"] and not armed and LED["alarm"]:
        LED["alarm"] = False                              # switching the protection off acknowledges the alarm too
    LED["armed_prev"] = armed
    det = int(STATE.get("persons") or 0) + int(STATE.get("objects") or 0)
    if det > LED["det_prev"] and CFG.get("led_det_flash"):
        led_flash("white", 0.3)
    LED["det_prev"] = det
    try:
        f_ = str(SRV.get("fault") or "")
    except NameError:
        f_ = ""
    if f_ and f_ != LED["srv_fault_prev"]:
        led_fault("servo:" + f_)
    LED["srv_fault_prev"] = f_
    try:
        dark = is_dark()
    except Exception:
        dark = False
    fr = led_frame(now, lv, arming, dark)
    LED["frame"] = fr
    sim = led_sim_live()
    LED["sim"] = sim
    st = {"on": bool(CFG.get("led_on", True)), "layer": fr["layer"], "col": fr["col"], "rgb": LED_HEX.get(fr["col"], "#000000") if fr["br"] > 0 else "#000000",
          "br": round(fr["br"], 3), "state": lv, "arming": arming, "state_col": led_colour("led_col_" + lv), "state_hex": LED_HEX.get(led_colour("led_col_" + lv), "#000000"), "alarm": bool(LED["alarm"]),
          "night": bool(dark) and CFG.get("led_night", "dim") != "normal", "hb": LED["hb_n"], "hb_t": round(LED["hb_wall"], 2), "sim": sim,
          "hw": "sim" if sim else LED["hw"], "presses": list(LED["presses"])[-5:], "btn_on": bool(CFG.get("btn_on")),
          "fault": LED["fault_reason"] if now < LED["fault_until"] else ""}
    STATE["led"] = st
    return fr


def led_sim_live():
    try:
        return bool(CFG.get("sim_on")) and simval_live()
    except NameError:
        return False


def led_label(lang=None, sim_mark=True):
    """«LED: Wachsam (orange)» - the line for the web page and the window (sim_mark=False: for the simulator itself)"""
    s = STATE.get("led") or {}
    if not s.get("on", True):
        return tr("LED: off", lang)
    lay = s.get("layer") or "state"
    st = tr(LED_STATE_NAMES.get(s.get("state") or "off", "Off"), lang)
    col = tr(s.get("state_col") or "off", lang)
    txt = f"{tr('LED', lang)}: {st} ({col})"
    if lay in ("alarm", "fault", "test", "flash", "deny"):
        txt += " · " + tr(LED_LAYER_NAMES[lay], lang)
    if s.get("alarm") and lay != "alarm":
        txt += " · " + tr("Alarm", lang)
    if s.get("night"):
        txt += " · " + tr("night: dimmed" if CFG.get("led_night") == "dim" else "night: off", lang)
    if s.get("sim") and sim_mark:
        txt += " · 🧪 " + tr("on the simulated head", lang)
    return txt


# ---- the output: PCA9685 channels (gamma, common anode / cathode) -----------------------------------------------------
def led_channels():
    return [_led_int(k, 0, 15) for k in ("led_ch_r", "led_ch_g", "led_ch_b")]


def led_channel_conflict():
    """a LED channel that a servo or a light uses -> its number, else None"""
    used = {int(CFG.get("pca_pan_ch", 0)), int(CFG.get("pca_tilt_ch", 1))}
    for k in ("light_white_out", "light_ir_out"):
        v = str(CFG.get(k) or "")
        if v.startswith("pca:") and v[4:].isdigit():
            used.add(int(v[4:]))
    if CFG.get("light_ir_wide"):
        used.add(4)
    chs = led_channels()
    for c in chs:
        if c in used or chs.count(c) > 1:
            return c
    return None


def led_duty(v, anode=False):
    """0..1 light -> (on, off) register values of the PCA9685 (bit 12 = fully on / off), gamma 2.2"""
    d = int(round(4095 * max(0.0, min(1.0, v)) ** 2.2))
    if anode:
        d = 4095 - d                                      # common anode: the output sinks the current - low = light
    if d <= 0:
        return 0, 0x1000
    if d >= 4095:
        return 0x1000, 0
    return 0, d


def led_pca_write(pca, fr, force=False):
    """the three channels of the frame (only when they change: I2C is shared with the servos)"""
    chs = led_channels()
    anode = CFG.get("led_common") == "anode"
    vals = [c * fr["br"] for c in fr["rgb"]] if fr else [0.0, 0.0, 0.0]
    key = (tuple(chs), anode, tuple(round(v, 3) for v in vals))
    if not force and key == LED.get("last"):
        return False
    for ch, v in zip(chs, vals):
        on, off = led_duty(v, anode)
        pca._set(ch, on, off)
    LED["last"] = key
    return True


_led_hw_lights_163 = Hardware._lights


def _led_hw_lights(self, wanted):
    _led_hw_lights_163(self, wanted)
    fr = led_tick()
    led_buttons_start()
    if self.pca is None:
        LED["hw"] = "none"; LED["last"] = None
        return
    try:
        if LED["sim"] or not CFG.get("led_on", True):
            LED["hw"] = "sim" if LED["sim"] else "off"
            if LED.get("last") is not None:                # was lit by us: dark once (the channels may serve others then)
                led_pca_write(self.pca, {"rgb": (0.0, 0.0, 0.0), "br": 0.0}); LED["last"] = None
            return
        if led_channel_conflict() is not None:
            LED["hw"] = "conflict"; LED["last"] = None
            return
        LED["hw"] = "pca"
        led_pca_write(self.pca, fr)
    except Exception as e:
        LED["last"] = None
        if not LED.get("err_t") or time.time() - LED["err_t"] > 60:
            LED["err_t"] = time.time()
            log_event("servo", f"Status LED error: {e}"[:160])


# wraps: Hardware._lights (after 163: white / IR / wide IR, then the status LED)
Hardware._lights = _led_hw_lights
_light_out_pairs_163 = light_out_pairs


def light_out_pairs(name):                                # + 163a: channels 5 / 6 / 7 belong to the status LED when it is on
    p = _light_out_pairs_163(name)
    if CFG.get("led_on", True):
        own = {f"pca:{c}" for c in led_channels()}
        p = [x for x in p if x[0] not in own or x[0] == CFG.get(f"light_{name}_out")]
    return p


# ---- faults and alarms from the rest of MoveEye --------------------------------------------------------------------
_log_event_led_base = log_event


def log_event(kind, text):                                # + 163a: a fault line -> a short violet pulse of the LED
    r = _log_event_led_base(kind, text)
    try:
        if LED_FAULT_RE.search(str(text)) and CFG.get("led_fault_pulse", True):
            led_fault(LED_FAULT_RE.search(str(text)).group(0))
    except Exception:
        pass
    return r


_push_alert_led_base = push_alert


def push_alert(kind, text="", **extra):                   # + 163a: an alarm while protected -> red blinking until acknowledged
    try:
        if kind in LED_ALARM_KINDS and is_armed():
            led_alarm(kind)
    except Exception:
        pass
    return _push_alert_led_base(kind, text, **extra)


# ---- the buttons --------------------------------------------------------------------------------------------------------
class LedButton:
    """debounce + short / long press from a level (True = pressed) and a time; feed() returns "short", "long" or None.
    Long fires while held (after btn_long_s), short at the release of a shorter press."""
    def __init__(self, name, debounce=0.05, long_s=1.5):
        self.name, self.debounce, self.long_s = name, float(debounce), float(long_s)
        self.raw = False; self.raw_t = None; self.stable = False; self.down_t = None; self.long_done = False

    def feed(self, level, t):
        level = bool(level)
        if level != self.raw:
            self.raw = level; self.raw_t = t
        ev = None
        if self.raw != self.stable and self.raw_t is not None and t - self.raw_t >= self.debounce:
            self.stable = self.raw
            if self.stable:
                self.down_t = self.raw_t; self.long_done = False
            else:
                if self.down_t is not None and not self.long_done:
                    ev = "short"
                self.down_t = None
        if self.stable and self.down_t is not None and not self.long_done and t - self.down_t >= self.long_s:
            self.long_done = True; ev = "long"
        return ev


LED_BTN_NAMES = {"protect": "Protection", "ack": "Acknowledge alarm"}
LEDBTN = {"thread": None, "dets": {}, "pins": None, "devs": {}, "msg": "off", "sim": {}}


def led_btn_params():
    return max(0.005, _led_int("btn_debounce_ms", 5, 500) / 1000.0), max(0.5, min(5.0, float(CFG.get("btn_long_s") or 1.5)))


def led_button_event(name, ev, src="GPIO"):
    """a press of a button of the device (real GPIO or the simulator) -> the action; every press is logged"""
    if ev not in ("short", "long") or name not in LED_BTN_NAMES:
        return None
    pin_set = bool(CFG.get("protect_pin"))
    guard = pin_set and CFG.get("btn_pin_rule", "pin_arm_only") == "pin_arm_only"
    lv, _arming = led_level()
    what = ""
    if name == "protect":
        if ev == "long":
            if lv == "full" and CFG.get("armed"):
                what = "already Full"
            else:
                protect_set("full", "button")
                what = "-> Full"
        elif CFG.get("armed"):
            if guard:
                what = "switching off refused: a PIN for disarming is set (use the app)"
                led_flash("red", 1.0, 3.0)
            else:
                protect_cancel_escalation()
                protect_set("off", "button")
                what = "-> Off"
        else:
            protect_set("watch", "button")
            what = "-> Watchful"
    else:
        if guard and CFG.get("armed"):
            with LED_LOCK:
                was = LED["alarm"]; LED["alarm"] = False
            what = "LED acknowledged; siren / escalation stay (a PIN for disarming is set - use the app)" if was else "nothing to acknowledge (PIN set: siren only from the app)"
        else:
            led_ack("button" + (" 🧪" if src == "simulator" else ""))
            what = "alarm acknowledged"
    LED["presses"].append({"t": datetime.now().strftime("%H:%M:%S"), "btn": name, "ev": ev, "src": src, "what": what})
    log_event("sys", f"Button «{LED_BTN_NAMES[name]}» {ev} press ({src}{' 🧪' if src == 'simulator' else ''}): {what}")
    return what


def led_sim_buttons(d, now=None):
    """the buttons of the simulator (world_reply «buttons»): {"protect"|"ack": {"down", "held_ms", "seq", "last_ms"}} - turned
    into the same levels as a real GPIO (the presses of before the connection do not count)"""
    if not isinstance(d, dict):
        return []
    now = led_now() if now is None else now
    deb, lng = led_btn_params()
    evs = []
    pid = SIM.get("pid") if "SIM" in globals() else None
    for name in LED_BTN_NAMES:
        b = d.get(name)
        if not isinstance(b, dict):
            continue
        st = LEDBTN["sim"].setdefault(name, {"seq": None, "track": False, "t_down": 0.0, "pid": pid, "det": LedButton(name, deb, lng)})
        det = st["det"]; det.debounce, det.long_s = deb, lng
        try:
            seq = int(b.get("seq") or 0); held = max(0.0, float(b.get("held_ms") or 0) / 1000.0); last = max(0.0, float(b.get("last_ms") or 0) / 1000.0)
        except (TypeError, ValueError):
            continue
        if st["seq"] is None or st["pid"] != pid or seq < st["seq"]:
            st.update(seq=seq, pid=pid, track=bool(b.get("down")), t_down=now - held)
            if st["track"]:
                det.feed(True, now - held); det.feed(True, now)
            continue
        if seq > st["seq"]:                               # a press ended: played with its length (the simulator has no bounce:
            t0 = st["t_down"] if st["track"] else now - last - deb * 3   # a short click counts, stretched to the debounce time)
            ln = max(deb * 1.5, last)
            for lvl, t_ in ((True, t0), (True, t0 + deb * 1.5), (True, t0 + ln), (False, t0 + ln), (False, t0 + ln + deb * 1.5)):
                e = det.feed(lvl, t_)
                if e:
                    evs.append((name, e))
            st.update(seq=seq, track=False)
        if b.get("down"):
            if not st["track"]:
                det.feed(True, now - held); st.update(track=True, t_down=now - held)
            e = det.feed(True, now)
            if e:
                evs.append((name, e))
    for name, e in evs:
        try:
            led_button_event(name, e, "simulator")
        except Exception as ex:
            log_event("sys", f"Button {name}: {type(ex).__name__}: {ex}"[:160])
    return evs


def led_gpio_pins():
    out = {}
    for name, k in (("protect", "btn_gpio_protect"), ("ack", "btn_gpio_ack")):
        v = str(CFG.get(k) or "")
        if v.isdigit():
            out[name] = int(v)
    return out


def led_buttons_start():
    if LEDBTN["thread"] is None:
        LEDBTN["thread"] = threading.Thread(target=_led_buttons_loop, daemon=True, name="buttons")
        LEDBTN["thread"].start()


def _led_buttons_close():
    for d in LEDBTN["devs"].values():
        try:
            d.close()
        except Exception:
            pass
    LEDBTN["devs"] = {}; LEDBTN["pins"] = None


def _led_buttons_loop():
    """100 × a second: the two GPIO buttons (internal pull-up, the button pulls to ground). Not while the simulator has them."""
    while True:
        try:
            if not CFG.get("btn_on") or LED.get("sim"):
                if LEDBTN["devs"]:
                    _led_buttons_close()
                LEDBTN["msg"] = "simulator" if LED.get("sim") else "off"
                time.sleep(0.5); continue
            pins = led_gpio_pins()
            if pins != LEDBTN["pins"]:
                _led_buttons_close()
                try:
                    from gpiozero import DigitalInputDevice
                    for name, g in pins.items():
                        LEDBTN["devs"][name] = DigitalInputDevice(g, pull_up=True)
                    LEDBTN["msg"] = "GPIO " + " / ".join(str(pins[n]) for n in LED_BTN_NAMES if n in pins)
                    log_event("sys", "Buttons on the device: " + ", ".join(f"{LED_BTN_NAMES[n]} GPIO {g}" for n, g in pins.items()))
                except Exception as e:
                    LEDBTN["msg"] = f"no GPIO ({type(e).__name__})"
                    _led_buttons_close(); LEDBTN["pins"] = pins
                    time.sleep(10); continue
                LEDBTN["pins"] = pins
            deb, lng = led_btn_params()
            now = led_now()
            for name, dev in list(LEDBTN["devs"].items()):
                det = LEDBTN["dets"].setdefault(name, LedButton(name, deb, lng))
                det.debounce, det.long_s = deb, lng
                ev = det.feed(bool(dev.value), now)            # pull_up=True: value 1 = pulled to ground = pressed
                if ev:
                    led_button_event(name, ev, f"GPIO {LEDBTN['pins'].get(name)}")
            time.sleep(0.01)
        except Exception as e:
            LEDBTN["msg"] = f"error: {e}"[:60]
            time.sleep(2)
