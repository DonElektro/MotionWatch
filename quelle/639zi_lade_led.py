#@ MoveEye – Teil 639zi: Lade-LED an GPIO 6 (Pin 31, 330 Ω, Lichtleiter hinten): leuchtet beim Laden, blinkt langsam = Akku voll und Strom da, schnell = Akku fast leer, sonst aus; nachts / beim Akku-Sparen gedimmt oder aus wie die Status-LED; Schalter «Lade-LED» unter Strom → Akku (Experte); im Simulator im Fenster «Gerät»; Selbsttest. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Auftrag Besitzer (01.11.2026), Bau-Infos hardware/gehaeuse/bau.json «ladeled»: GPIO 6 (pin 31) -> 330 Ω -> green 3 mm LED -> GND.
#   * what it shows (the first that applies wins), from STATE["battery"] (100: UPS HAT (E) / INA219, 285: the simulated HAT):
#       on    the battery charges (UPS HAT (E): state bit «charging», INA219: current into the battery)
#       fast  the battery is almost empty - the same limit as the warning «Battery almost empty» (100: BATT_LOW_PCT_UPS on the
#             battery, BATT_LOW_PCT_BANK for the powerbank estimate)
#       slow  full and power at the input (UPS HAT (E): «full»; INA219: on mains, no charge current, 98 % or more)
#       off   otherwise, without a battery value, or switched off («charge_led_on», Settings → Power supply → Battery, expert)
#   * brightness like the status LED (163a): led_bright by day; at night (is_dark) led_night «dim» = led_night_bright, «off» =
#     dark, «normal» = as by day; while the battery saver runs (105) always dimmed (never off: the fast blink is the warning)
#   * output: gpiozero PWMLED (lgpio on the Pi 5, like the buttons in 163a) in its own thread, 20 × a second. Only on a
#     Raspberry Pi; on a PC, without gpiozero or while a sensor uses GPIO 6 nothing is switched (STATE «charge_led» hw says why).
#     With the 3D simulator connected the real GPIO rests; the simulator shows it in the window «Gerät» (statusled.gd, sim_state
#     «charge_led»: mode on / slow / fast / off, br - the blinking runs in the simulator itself).
# ----------------------------------------------------------------------------
CHARGE_LED_GPIO = 6
CHARGE_LED_HZ = {"slow": 0.5, "fast": 4.0}               # slow: 1 s on / 1 s off; fast: 4 blinks a second
CHARGE_LED_FULL_PCT = 98
for _k, _v in {"charge_led_on": True}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)   # 636 took its copy before this part
CHARGE_LED = {"mode": "off", "why": "", "t0": 0.0, "hw": "none", "dev": None, "thread": None, "last": None, "pi": None, "err_t": 0.0}
CHARGE_LED_WHY = {"charging": "charging", "low": "battery almost empty", "full": "full, power at the input", "": "",
                  "switched off": "switched off", "no battery value": "no battery value"}
CHARGE_LED_MODE_NAMES = {"on": "on", "slow": "blinks slowly", "fast": "blinks fast", "off": "off"}


def charge_led_low_pct(b):
    """the limit of the warning «Battery almost empty» (100) for this kind of battery value"""
    return BATT_LOW_PCT_UPS if b.get("src") == "ups" else BATT_LOW_PCT_BANK


def charge_led_mode(b=None):
    """-> (mode, why): on / fast / slow / off from the battery value (pure apart from CFG - self-test with made-up values)"""
    b = (STATE.get("battery") or {}) if b is None else (b or {})
    if not CFG.get("charge_led_on", True):
        return "off", "switched off"
    if not b.get("on"):
        return "off", "no battery value"
    ups = b.get("src") == "ups"
    pct = b.get("pct")
    if b.get("charging"):
        return "on", "charging"
    on_batt = bool(b.get("on_battery")) if ups else True    # the powerbank estimate knows no mains: always «on the battery»
    if pct is not None and on_batt and int(pct) <= charge_led_low_pct(b):
        return "fast", "low"
    if ups and not on_batt and (b.get("full") or (pct is not None and int(pct) >= CHARGE_LED_FULL_PCT)):
        return "slow", "full"
    return "off", ""


def charge_led_bright(dark=False, saving=False):
    """0..1 like the status LED (163a): by day led_bright, at night dimmed / off / as by day; battery saver: dimmed"""
    day = _led_int("led_bright", 1, 100) / 100.0
    low = min(day, _led_int("led_night_bright", 1, 100) / 100.0)
    rule = CFG.get("led_night", "dim")
    if dark and rule == "off":
        return 0.0
    if saving or (dark and rule == "dim"):
        return low
    return day


def charge_led_level(now, mode, br):
    """0..1 for the LED at the moment «now» (the blinking starts with the mode: CHARGE_LED["t0"])"""
    if mode == "on":
        return br
    hz = CHARGE_LED_HZ.get(mode)
    if hz and ((now - CHARGE_LED["t0"]) * hz) % 1.0 < 0.5:
        return br
    return 0.0


def charge_led_tick(now=None):
    """the mode, the brightness and the level now -> STATE["charge_led"]; returns the level 0..1"""
    now = led_now() if now is None else now
    mode, why = charge_led_mode()
    if mode != CHARGE_LED["mode"]:
        CHARGE_LED.update(mode=mode, t0=now)
    CHARGE_LED["why"] = why
    try:
        dark = bool(is_dark())
    except Exception:
        dark = False
    try:
        saving = bool(batt_save_active())
    except NameError:
        saving = False
    br = charge_led_bright(dark, saving) if mode != "off" else 0.0
    lvl = charge_led_level(now, mode, br)
    STATE["charge_led"] = {"on": bool(CFG.get("charge_led_on", True)), "mode": mode, "why": why, "br": round(br, 3), "lvl": round(lvl, 3),
                           "night": dark and CFG.get("led_night", "dim") != "normal", "saving": saving, "hw": CHARGE_LED["hw"], "gpio": CHARGE_LED_GPIO}
    return lvl


def charge_led_label(lang=None):
    """«Lade-LED: blinkt langsam (voll, Strom da)» - for the simulator window and the log"""
    s = STATE.get("charge_led") or {}
    if not s.get("on", CFG.get("charge_led_on", True)):
        return tr("Charge LED: off", lang)
    m = s.get("mode") or "off"
    txt = tr("Charge LED", lang) + ": " + tr(CHARGE_LED_MODE_NAMES.get(m, "off"), lang)
    w = CHARGE_LED_WHY.get(s.get("why") or "", "")
    if w and m != "off":
        txt += f" ({tr(w, lang)})"
    if m != "off" and (s.get("night") or s.get("saving")):
        txt += " · " + tr("dimmed" if s.get("br", 0) > 0 else "LED off at night", lang)
    return txt


def charge_led_is_pi():
    if CHARGE_LED["pi"] is None:
        try:
            with open("/proc/device-tree/model", "rb") as f:
                CHARGE_LED["pi"] = b"Raspberry Pi" in f.read()
        except OSError:
            CHARGE_LED["pi"] = False
    return CHARGE_LED["pi"]


def charge_led_gpio_taken():
    """GPIO 6 used by a sensor, a light, a relay or the buttons -> True (then the charge LED stays off)"""
    try:
        u = set(_sens_used_gpios_cl_base(None))
    except Exception:
        u = set()
    return CHARGE_LED_GPIO in u


def _charge_led_close():
    d = CHARGE_LED.get("dev")
    CHARGE_LED.update(dev=None, last=None)
    if d is not None:
        try:
            d.value = 0
            d.close()
        except Exception:
            pass


def charge_led_start():
    if CHARGE_LED["thread"] is None:
        CHARGE_LED["thread"] = threading.Thread(target=_charge_led_loop, daemon=True, name="charge-led")
        CHARGE_LED["thread"].start()


def _charge_led_loop():
    """20 × a second: the level to GPIO 6 (gpiozero PWMLED). Nothing on a PC, without gpiozero, while the simulator is connected."""
    while True:
        try:
            lvl = charge_led_tick()
            if not CFG.get("charge_led_on", True) or led_sim_live():
                _charge_led_close()
                CHARGE_LED["hw"] = "sim" if CFG.get("charge_led_on", True) else "off"
                time.sleep(0.5); continue
            if CHARGE_LED["dev"] is None:
                if not charge_led_is_pi():
                    CHARGE_LED["hw"] = "none"; time.sleep(30); continue
                if charge_led_gpio_taken():
                    CHARGE_LED["hw"] = "conflict"; time.sleep(10); continue
                try:
                    from gpiozero import PWMLED
                    CHARGE_LED["dev"] = PWMLED(CHARGE_LED_GPIO, frequency=200)
                    CHARGE_LED["hw"] = "gpio"
                    log_event("sys", f"Charge LED on GPIO {CHARGE_LED_GPIO} (pin 31)")
                except Exception as e:
                    CHARGE_LED["hw"] = f"no GPIO ({type(e).__name__})"
                    time.sleep(60); continue
            v = round(lvl, 3)
            if v != CHARGE_LED["last"]:
                CHARGE_LED["dev"].value = v
                CHARGE_LED["last"] = v
            time.sleep(0.05)
        except Exception as e:
            _charge_led_close()
            if time.time() - CHARGE_LED["err_t"] > 60:
                CHARGE_LED["err_t"] = time.time()
                log_event("sys", f"Charge LED error: {e}"[:160])
            time.sleep(2)


_charge_led_hw_lights_base = Hardware._lights


def _charge_led_hw_lights(self, wanted):                  # + 639zi: the hardware loop starts the thread of the charge LED once
    _charge_led_hw_lights_base(self, wanted)
    charge_led_start()


# wraps: Hardware._lights (after 163 / 163a)
Hardware._lights = _charge_led_hw_lights
_sens_used_gpios_cl_base = sens_used_gpios


# wraps: sens_used_gpios
def sens_used_gpios(skip=None):                           # + 639zi: GPIO 6 belongs to the charge LED while it is switched on
    u = _sens_used_gpios_cl_base(skip)
    if CFG.get("charge_led_on", True):
        u = set(u) | {CHARGE_LED_GPIO}
    return u


_sim_state_639zi = sim_state


# wraps: sim_state
def sim_state():                                          # + 639zi: «charge_led» - the simulator shows it in the window «Gerät»
    d = _sim_state_639zi()
    try:
        charge_led_tick()
    except Exception:
        pass
    s = STATE.get("charge_led") or {}
    d["charge_led"] = {"on": bool(s.get("on", True)), "mode": str(s.get("mode") or "off"), "br": float(s.get("br") or 0.0),
                       "text": charge_led_label("de")}
    return d


# ---- the switch: Settings → Power supply → Battery (expert: not in SIMPLE_KEYS) ------------------------------------------------
_CL_LABEL = "Charge LED (GPIO 6, pin 31): on while charging, blinks slowly when full, fast when the battery is almost empty"
_bi = max([i for i, x in enumerate(TOGGLES) if x[0] == "Battery"] or [len(TOGGLES) - 1])
TOGGLES.insert(_bi + 1, ("Battery", "charge_led_on", _CL_LABEL))
SET_HELP["charge_led_on"] = ("The small green LED at the back of the device (GPIO 6, pin 31): on while the battery charges, blinks slowly "
                             "when it is full and power is at the input, blinks fast when the battery is almost empty (the same limit as "
                             "the warning), otherwise off. At night and while the battery saver runs it is dimmed (or off at night, like "
                             "the status LED). On a PC nothing is switched; with the simulator it shows in the window «Gerät».", "On.")

_CL_HELP = (
    ("Einstellungen → Licht &amp; Ton → Status-LED &amp; Tasten.</p>",
     "<p><b>🔋 Lade-LED:</b> Die kleine grüne LED hinten am Gerät (GPIO 6 = Pin 31, 330 Ω) leuchtet, solange der Akku lädt, "
     "blinkt langsam, wenn er voll ist und Strom anliegt, und blinkt schnell, wenn der Akku fast leer ist (dieselbe Schwelle wie die "
     "Warnung «Akku fast leer»); sonst ist sie aus. Nachts und beim Akku-Sparen gedimmt (nachts aus, wenn die Status-LED nachts aus "
     "ist). Mit dem 3D-Simulator zeigt sie das Fenster «Gerät» (🧪). Einstellungen → Strom → Akku → «Lade-LED» (Experte).</p>"),
    ("sound → Status LED &amp; buttons.</p>",
     "<p><b>🔋 Charge LED:</b> the small green LED at the back of the device (GPIO 6 = pin 31, 330 Ω) is on while the battery "
     "charges, blinks slowly when it is full and power is at the input, and blinks fast when the battery is almost empty (the same "
     "limit as the warning «Battery almost empty»); otherwise it is off. Dimmed at night and while the battery saver runs (off at "
     "night when the status LED is off at night). With the 3D simulator it shows in the window «Gerät» (🧪). Settings → Power "
     "supply → Battery → «Charge LED» (expert).</p>"),
)
for _a, _b in _CL_HELP:
    if _a in HELP_PAGE and _b not in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)

_HX_CHARGELED = {
    _CL_LABEL: ("Lade-LED (GPIO 6, Pin 31): leuchtet beim Laden, blinkt langsam bei vollem Akku, schnell bei fast leerem Akku",
                "LED de charge (GPIO 6, broche 31) : allumée pendant la charge, clignote lentement quand la batterie est pleine, vite quand elle est presque vide",
                "LED di carica (GPIO 6, pin 31): accesa durante la carica, lampeggia lentamente a batteria piena, velocemente a batteria quasi scarica",
                "LED da chargiar (GPIO 6, pin 31): glischa durant chargiar, cliegna plaunsieu cun accu plain, svelt cun accu bunamain vid"),
    SET_HELP["charge_led_on"][0]:
        ("Die kleine grüne LED hinten am Gerät (GPIO 6, Pin 31): leuchtet, solange der Akku lädt, blinkt langsam, wenn er voll ist und "
         "Strom anliegt, blinkt schnell, wenn der Akku fast leer ist (dieselbe Schwelle wie die Warnung), sonst aus. Nachts und beim "
         "Akku-Sparen gedimmt (nachts aus wie die Status-LED, falls so eingestellt). Auf einem PC wird nichts geschaltet; mit dem "
         "Simulator zeigt sie das Fenster «Gerät».",
         "La petite LED verte à l’arrière de l’appareil (GPIO 6, broche 31) : allumée pendant la charge de la batterie, clignote "
         "lentement quand elle est pleine et que le courant est branché, clignote vite quand la batterie est presque vide (même seuil "
         "que l’avertissement), sinon éteinte. Atténuée la nuit et pendant l’économie de batterie (éteinte la nuit comme la LED d’état, "
         "si réglé ainsi). Sur un PC rien n’est commuté ; avec le simulateur elle apparaît dans la fenêtre «Gerät».",
         "Il piccolo LED verde sul retro del dispositivo (GPIO 6, pin 31): acceso mentre la batteria si carica, lampeggia lentamente "
         "quando è piena e c’è corrente, lampeggia velocemente quando la batteria è quasi scarica (stessa soglia dell’avviso), "
         "altrimenti spento. Attenuato di notte e durante il risparmio batteria (spento di notte come il LED di stato, se impostato "
         "così). Su un PC non viene commutato nulla; con il simulatore appare nella finestra «Gerät».",
         "La pitschna LED verda davos sin l’apparat (GPIO 6, pin 31): glischa durant che l’accu chargia, cliegna plaunsieu cur ch’el "
         "è plain e la current è avant maun, cliegna svelt cur che l’accu è bunamain vid (il medem limit sco l’avertiment), "
         "uschiglio stizzada. La notg e durant spargnar accu sfiarada (la notg stizzada sco la LED da status, sche uschia "
         "definì). Sin in PC na vegn nagut stizzà; cun il simulatur sa mussa ella en la fanestra «Gerät»."),
    "On.": ("An.", "Activé.", "Attivo.", "Activà."),
    "Charge LED": ("Lade-LED", "LED de charge", "LED di carica", "LED da chargiar"),
    "Charge LED: off": ("Lade-LED: aus", "LED de charge : éteinte", "LED di carica: spento", "LED da chargiar: stizzada"),
    "blinks slowly": ("blinkt langsam", "clignote lentement", "lampeggia lentamente", "cliegna plaunsieu"),
    "blinks fast": ("blinkt schnell", "clignote vite", "lampeggia velocemente", "cliegna svelt"),
    "charging": ("lädt", "en charge", "in carica", "chargia"),
    "battery almost empty": ("Akku fast leer", "batterie presque vide", "batteria quasi scarica", "accu bunamain vid"),
    "full, power at the input": ("voll, Strom liegt an", "pleine, courant branché", "piena, corrente presente", "plain, current avant maun"),
    "no battery value": ("kein Akku-Wert", "pas de valeur de batterie", "nessun valore della batteria", "nagina valur da l’accu"),
    "switched off": ("ausgeschaltet", "désactivée", "disattivato", "stizzà"),
}
for _k, _v in _HX_CHARGELED.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


# ---- self-test: the logic with made-up battery values and a fake clock --------------------------------------------------------
def charge_led_selftest():
    keys = ("charge_led_on", "led_bright", "led_night", "led_night_bright")
    keep_cfg = {k: CFG.get(k) for k in keys}
    keep_cl = dict(CHARGE_LED)
    keep_bat = STATE.get("battery")
    try:
        CFG.update(charge_led_on=True, led_bright=60, led_night="dim", led_night_bright=8)
        ups = lambda **kw: dict({"on": True, "src": "ups", "model": "e", "pct": 60, "on_battery": False, "charging": False, "full": False}, **kw)
        M = lambda b: charge_led_mode(b)[0]
        # the four states (UPS HAT (E))
        assert M(ups(charging=True, pct=40)) == "on", "charging -> on"
        assert M(ups(full=True, pct=100)) == "slow", "full + power -> slow"
        assert M(ups(on_battery=True, pct=BATT_LOW_PCT_UPS)) == "fast", "almost empty -> fast"
        assert M(ups(on_battery=True, pct=BATT_LOW_PCT_UPS + 1)) == "off", "above the warning limit -> off"
        assert M(ups(on_battery=True, pct=100, full=True)) == "off", "full but on the battery (no power at the input) -> off"
        assert M(ups(pct=60)) == "off", "on mains, neither charging nor full -> off"
        assert M(ups(charging=True, pct=5)) == "on", "charging wins over almost empty"
        # INA219 (no «full» bit): full = on mains, no charge current, 98 % or more
        assert M(ups(model="ina", full=None, pct=CHARGE_LED_FULL_PCT)) == "slow" and M(ups(model="ina", pct=CHARGE_LED_FULL_PCT - 1)) == "off"
        # powerbank estimate: no mains known, the limit of its warning
        bank = {"on": True, "src": "pmic", "pct": BATT_LOW_PCT_BANK}
        assert M(bank) == "fast" and M(dict(bank, pct=BATT_LOW_PCT_BANK + 1)) == "off" and M(dict(bank, pct=None)) == "off"
        assert M({"on": False}) == "off" and charge_led_mode({"on": False})[1] == "no battery value"
        assert (BATT_LOW_PCT_UPS, BATT_LOW_PCT_BANK) == (20, 15), "the limits of «Battery almost empty» (100)"
        CFG["charge_led_on"] = False
        assert charge_led_mode(ups(charging=True)) == ("off", "switched off"), "switch «Charge LED» off"
        CFG["charge_led_on"] = True
        # brightness: day, night dimmed / off / as by day, battery saver always dimmed
        assert abs(charge_led_bright() - 0.6) < 1e-9 and abs(charge_led_bright(dark=True) - 0.08) < 1e-9
        assert abs(charge_led_bright(saving=True) - 0.08) < 1e-9
        CFG["led_night"] = "off"
        assert charge_led_bright(dark=True) == 0.0 and abs(charge_led_bright(saving=True) - 0.08) < 1e-9, "saver: dimmed, never off"
        CFG["led_night"] = "normal"
        assert abs(charge_led_bright(dark=True) - 0.6) < 1e-9
        CFG["led_night"] = "dim"
        # blinking with a fake clock: slow 1 s on / 1 s off, fast 4 × a second, «on» steady
        CHARGE_LED["t0"] = 100.0
        assert [charge_led_level(t, "slow", 1.0) for t in (100.0, 100.9, 101.1, 101.9, 102.0)] == [1.0, 1.0, 0.0, 0.0, 1.0]
        assert [charge_led_level(t, "fast", 1.0) for t in (100.0, 100.1, 100.13, 100.24, 100.25)] == [1.0, 1.0, 0.0, 0.0, 1.0]
        assert charge_led_level(123.4, "on", 0.6) == 0.6 and charge_led_level(123.4, "off", 0.6) == 0.0
        # the tick: STATE, phase starts with a new mode, label in German
        CHARGE_LED.update(mode="off", t0=0.0)
        STATE["battery"] = ups(on_battery=True, pct=10)
        charge_led_tick(500.0)
        s = STATE["charge_led"]
        assert s["mode"] == "fast" and CHARGE_LED["t0"] == 500.0 and s["gpio"] == 6, s
        charge_led_tick(500.2)
        assert CHARGE_LED["t0"] == 500.0, "same mode: the phase keeps running"
        assert charge_led_label("de").startswith("Lade-LED: blinkt schnell (Akku fast leer)"), charge_led_label("de")
        STATE["battery"] = ups(charging=True)
        charge_led_tick(501.0)
        assert charge_led_label("de").startswith("Lade-LED: an (lädt)"), charge_led_label("de")
        for L_ in ("fr", "it", "rm"):
            assert tr(_CL_LABEL, L_) != _CL_LABEL and tr("blinks slowly", L_) != "blinks slowly", L_
        # GPIO 6 is taken while the switch is on; the switch in Settings → Battery, expert; simulator field
        assert 6 in sens_used_gpios() and 6 not in sens_free_gpios()
        assert any(x[1] == "charge_led_on" and x[0] == "Battery" for x in TOGGLES) and "charge_led_on" not in SIMPLE_KEYS
        assert "Lade-LED" in HELP_PAGE and "Charge LED" in HELP_PAGE
        sd = sim_state()
        assert sd["charge_led"]["mode"] == "on" and sd["charge_led"]["text"].startswith("Lade-LED"), sd["charge_led"]
        L = iface_list()
        if L is not None:
            assert "charge_led" in L["state"], "schnittstelle.json «charge_led»"
        return "on / slow / fast / off from made-up UPS HAT (E), INA219 and powerbank values, limits 20 / 15 %, night and saver, blinking, GPIO 6, simulator"
    finally:
        CFG.update(keep_cfg)
        CHARGE_LED.clear(); CHARGE_LED.update(keep_cl)
        if keep_bat is None:
            STATE.pop("battery", None)
        else:
            STATE["battery"] = keep_bat
        STATE.pop("charge_led", None)


SELFTEST_EXTRA.append(("Charge LED on GPIO 6: charging / full / almost empty, night, simulator (639zi)", charge_led_selftest))
