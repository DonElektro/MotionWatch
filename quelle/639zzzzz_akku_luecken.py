#@ MoveEye – Teil 639zzzzz: Akku-Lücken Geekworm X1206 (Besitzer 21.11.2026) – Kälteschutz beim Laden (GPIO 16), «Trotzdem laden», Notladen unter 10 %, «Akku schonen» (80 %), gelernte Laufzeit, «Voll in …», Zyklen und Kapazität, Licht dimmen (Texte). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entscheide Besitzer 21.11.2026 (Geekworm X1206 V2.0, 1S4P 21700, MAX17043 0x36, PLD GPIO 6, Laden GPIO 16):
#   * MoveEye darf GPIO 16 SCHALTEN (nur dieser Teil): Laden aus = der Pegel «chg_off_level» (Geekworm, Seite «X1200 Hardware»:
#     «GPIO16: High – charging disabled, Low – charging enabled»; für das X1206 selbst steht es dort nicht: darum eine Einstellung).
#     Laden wieder frei = GPIO 16 zurück auf Eingang mit Pull-down (so steht er nach dem Start des Pi: tief = lädt).
#     Das X1206 hat KEINEN Temperaturschutz beim Laden.
#   1. Kälteschutz: Quelle der BME280 / BMP280 im Gehäuse (060 EnvSensor, STATE["env"], im Simulator dessen Wert). Unter
#      chg_cold_c (0 °C) Laden aus, wieder frei ab chg_cold_c + chg_cold_hyst (3 K, kein Flattern). Fällt der Sensor kurz aus,
#      gilt der letzte Wert 10 min weiter. Ohne BME280 nur eine Warnung (Karte; Push, wenn ein anderer Fühler unter 0 °C misst
#      und geladen wird), nie eine Sperre.
#      Notfall: (a) «Trotzdem laden» (Web + Fenster, nur Admin, mit Warnung) gilt chg_override_h (1 h), dann wieder gesperrt;
#      Push + Protokoll. (b) unter chg_emerg_pct (10 %) lädt es trotzdem (wieder gesperrt ab 13 %), mit Warn-Push.
#   2. Gelernte Laufzeit: Abfall des Ladestands im Akkubetrieb (%/h, Gerade über die letzte Stunde, geglättet) -> Restzeit
#      = % / Abfall und Verbrauch (W) = Abfall x Kapazität; geht in «hours», «use_w» und damit in die Nachtprognose (280).
#   3. «Voll in …» beim Laden aus dem Anstieg (%/h, letzte 30 min) -> full_min (die Anzeige gibt es schon, 530 / 570).
#   4. Gesundheit: äquivalente Vollzyklen = Summe der entladenen % / 100 (nur im Akkubetrieb, gegen Rauschen). Kapazität aus
#      langen Entladungen (mind. 30 % und 2 h am Stück, Energie aus dem Strom-Chip des Pi 5 «pmic»): Wh / (Abfall / 100).
#      Hinweis «Zellen altern» unter 80 % der Nennkapazität (ab 2 Messungen) oder ab 500 Zyklen.
#   5. «Akku schonen» (ab Werk aus): am Netz nur bis chg_care_max (80 %), wieder laden unter chg_care_resume (75 %).
#      Reihenfolge: Kälte sperrt (ausser Notfall / «Trotzdem laden»), «schonen» sperrt (ausser «Trotzdem laden»), sonst frei.
# Gelerntes in <Daten>/akku_lernen.json. In der Hauptdatei (die Grösse ist knapp) stehen nur die Standardwerte und ein kleiner
# Haken nach BatteryMonitor.ups_x12 (100, dessen Ereignisse / Schutz-Alarm bleiben unberührt): er ruft akl_tick aus dem Literal
# AKKU_LUECKEN_PY; fehlt die Zusatz-ZIP, gibt er GPIO 16 einmal frei, falls MoveEye das Laden gesperrt hinterliess. Alles andere
# (Entscheid, GPIO 16, Lernen, Anzeige, Knöpfe, Einstellungen, Texte) im Literal.
# Licht dimmen (Punkt 7): 070 light_pct / PCA9685.dim, 080 Hardware._lights; hier nur Regler und Texte.
# Test: werkzeuge/x1206_test.py Teil 7 / 8 (erfundener I2C-Bus, erfundenes pinctrl, erfundene Zeit).
# ----------------------------------------------------------------------------
AKL_DEF = {"chg_cold_on": True, "chg_cold_c": 0.0, "chg_cold_hyst": 3.0, "chg_emerg_pct": 10, "chg_override_h": 1.0,
           "chg_care": False, "chg_care_max": 80, "chg_care_resume": 75, "chg_off_level": "high"}
for _k, _v in AKL_DEF.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update(AKL_DEF)                         # charging: only the administrator
LOCK_DENY_KEYS.update(AKL_DEF)
AKL_FILE = "akku_lernen.json"
_AKL0 = {"done": False}


def akl_release_nozip():
    """without the zip (no charging control): GPIO 16 back to the board once, if MoveEye left charging blocked"""
    _AKL0["done"] = True
    try:
        with open(os.path.join(DATA_DIR, AKL_FILE), encoding="utf-8") as f:
            if not json.load(f).get("we_blocked"):
                return
    except (OSError, ValueError, AttributeError):
        return
    for c in (["pinctrl", "set", "16", "ip", "pd"], ["sudo", "-n", "pinctrl", "set", "16", "ip", "pd"]):
        if _run(c, timeout=5)[0] == 0:
            log_event("sys", "Charging allowed again (GPIO 16): no charging control without the data zip")
            return


_akl_ups_x12_base = BatteryMonitor.ups_x12


def _akl_ups_x12(self, r):                                  # + 639zzzzz: after the reading (the events of 100 stay untouched)
    res = _akl_ups_x12_base(self, r)
    try:
        if "akl_tick" in globals():
            akl_tick(self, r)                               # the charging control and the learning (zip)
        elif not _AKL0["done"]:
            akl_release_nozip()
    except Exception as e:
        if not _AKL0.get("err"):
            _AKL0["err"] = True
            log_event("sys", f"Battery learning / charging control: {e}"[:160])
    return res


# wraps: BatteryMonitor.ups_x12 (100)
BatteryMonitor.ups_x12 = _akl_ups_x12


AKKU_LUECKEN_PY = r'''# ---- charging control (cold, emergency, «Charge anyway», protect the battery), GPIO 16 ----------------------------------------
AKL_KEEP = ("cyc_pct", "cap_wh", "cap_n", "rate_dis", "we_blocked", "override_until", "cold", "care")
AKL = {"loaded": False, "save_t": 0.0, "blocked": None, "why": "", "cold": False, "care": False, "emerg": False,
       "override_until": 0.0, "we_blocked": False, "temp": None, "temp_src": "", "temp_t": 0.0, "err_t": 0.0,
       "dis": [], "chg": [], "rate_dis": None, "rate_t": 0.0, "rate_chg": None, "cyc_pct": 0.0, "last_pct": None,
       "cap_wh": None, "cap_n": 0, "span": None, "pushed": set(), "warn_t": 0.0, "now": None}
AKL_HOLD_S = 600.0                  # the last temperature counts this long when the sensor does not answer
AKL_BME = ("BME280", "BMP280", "Simulator")


def akl_now():
    return AKL["now"]() if callable(AKL["now"]) else time.time()       # tests set a made-up clock


def akl_load():
    if AKL["loaded"]:
        return
    AKL["loaded"] = True
    try:
        with open(os.path.join(DATA_DIR, AKL_FILE), encoding="utf-8") as f:
            d = json.load(f)
        for k in AKL_KEEP:
            if k in d:
                AKL[k] = d[k]
    except (OSError, ValueError, TypeError, AttributeError):
        pass


def akl_save(force=False):
    now = akl_now()
    if not force and now - AKL["save_t"] < 300:
        return
    AKL["save_t"] = now
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = os.path.join(DATA_DIR, AKL_FILE + ".part")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({k: AKL[k] for k in AKL_KEEP}, f)
        os.replace(tmp, os.path.join(DATA_DIR, AKL_FILE))
    except OSError:
        pass


def akl_gpio16(block):
    """block: drive GPIO 16 to the level that stops charging; else back to input with pull-down (as after the start of the
    Pi: low = the board charges). -> "" or the error"""
    lv = "dl" if CFG.get("chg_off_level") == "low" else "dh"
    args = ["pinctrl", "set", "16"] + (["op", lv] if block else ["ip", "pd"])
    cmds = [args] + ([["sudo", "-n"] + args] if not _is_root() and shutil.which("sudo") else [])
    err = ""
    for c in cmds:
        rc, _o, e = _run(c, timeout=5)
        if rc == 0:
            return ""
        err = e or f"exit {rc}"
    return err[:120]


def akl_temp(now):
    """(°C, source) of the BME280 / BMP280 in the case; the last good value for AKL_HOLD_S; (None, "") = none"""
    env = STATE.get("env") or {}
    if env.get("t") is not None and env.get("src") in AKL_BME:
        AKL.update(temp=float(env["t"]), temp_src=env["src"], temp_t=now)
    elif now - AKL["temp_t"] > AKL_HOLD_S:
        AKL.update(temp=None, temp_src="")
    return AKL["temp"], AKL["temp_src"]


def akl_decide(now, pct, on_batt):
    """-> (block, why). why: cold | care | emergency (cold, but charging anyway) | override | "" """
    C_ = CFG; A = AKL
    try:
        ep = int(C_["chg_emerg_pct"])
    except (TypeError, ValueError):
        ep = 10
    if pct is not None:
        if pct < ep:
            A["emerg"] = True
        elif pct >= ep + 3:
            A["emerg"] = False
    t, _src = akl_temp(now)
    if C_.get("chg_cold_on") and t is not None:
        lim = float(C_["chg_cold_c"])
        if t < lim:
            A["cold"] = True
        elif t >= lim + max(0.5, float(C_["chg_cold_hyst"])):
            A["cold"] = False
    elif not C_.get("chg_cold_on") or t is None:
        A["cold"] = False                                   # no sensor: never a block (only the warning)
    if C_.get("chg_care") and pct is not None and not on_batt:
        if pct >= int(C_["chg_care_max"]):
            A["care"] = True
        elif pct <= int(C_["chg_care_resume"]):
            A["care"] = False
    elif not C_.get("chg_care"):
        A["care"] = False
    ov = now < float(A["override_until"] or 0)
    if not ov and A["override_until"]:
        A["override_until"] = 0.0
        log_event("sys", "Charge anyway: the time is over - the cold protection holds charging again")
    if A["cold"] and not ov and not A["emerg"]:
        return True, "cold"
    if A["care"] and not ov:
        return True, "care"
    return False, "emergency" if A["cold"] and A["emerg"] and not ov else "override" if ov else ""


def akl_push(key, text_en, **kw):
    """one push per episode (key), only with push messages for the battery switched on"""
    if key in AKL["pushed"]:
        return
    AKL["pushed"].add(key)
    w = WATCH_REF.get("w")
    if w is not None and CFG.get("ups_push", True):
        try:
            w.notifier.info(trf(text_en, **kw), title="{name}: " + tr("Battery"))
        except Exception:
            pass


def akl_apply(block, why, pct):
    """switch GPIO 16 only when the wish changes; at the first reading only if MoveEye itself left it blocked"""
    A = AKL; now = akl_now()
    if block == A["blocked"]:
        return
    if A["blocked"] is None and not block and not A["we_blocked"]:
        A["blocked"] = False                                # never touched: the board stays as it is
        return
    if now - A["err_t"] < 60:
        return
    err = akl_gpio16(block)
    if err:
        A["err_t"] = now
        log_event("sys", f"Charging control GPIO 16: {err}")
        return
    A["blocked"] = block; A["we_blocked"] = block
    akl_save(True)
    if block:
        log_event("sys", f"Charging switched off (GPIO 16): {'cold' if why == 'cold' else 'protect the battery'} - battery {pct} %"
                  + (f", {AKL['temp']:.1f} °C" if why == "cold" and AKL["temp"] is not None else ""))
        if why == "cold":
            akl_push("cold", "Too cold to charge ({t} °C): charging is off until it is warmer. «Charge anyway» on the page.",
                     t=f"{AKL['temp']:.1f}" if AKL["temp"] is not None else "?")
    else:
        log_event("sys", f"Charging allowed again (GPIO 16) - battery {pct} %" + (f" ({why})" if why else ""))
        AKL["pushed"].discard("cold")


def akl_tick(bm, r):
    """after every X1206 reading (100 ups_x12): decide, switch GPIO 16; learning and the display come from the zip (akl_more)"""
    akl_load()
    b = STATE.get("battery") or {}
    if b.get("model") != "x12":
        return
    now = akl_now(); pct = b.get("pct"); on_batt = bool(b.get("on_battery"))
    block, why = akl_decide(now, pct, on_batt)
    if r.get("pld") is not None:                              # only with a readable board (pinctrl there)
        akl_apply(block, why, pct)
    if "akl_more" in globals():
        akl_more(bm, b, now, pct, on_batt, why)
    akl_save()


_akl_own_block_base = ups_x12_own_block                   # 100: always False


# wraps: ups_x12_own_block (100)
def ups_x12_own_block():                                    # + 639zzzzz: no «GPIO 16 is high» warning when MoveEye set it
    return bool(AKL["blocked"])


# ---- learning (2-4) and «Charge anyway» -----------------------------------------------------------------------------------------
def akl_rate(samples, span_min, dmin):
    """slope in %/h of [(t, pct)] over the last span_min minutes, None with too little change / time"""
    if len(samples) < 3:
        return None
    t1 = samples[-1][0]
    pts = [s for s in samples if t1 - s[0] <= span_min * 60.0]
    if len(pts) < 3 or pts[-1][0] - pts[0][0] < span_min * 60.0 * 0.5 or abs(pts[-1][1] - pts[0][1]) < dmin:
        return None
    n = len(pts); mt = sum(p[0] for p in pts) / n; mp = sum(p[1] for p in pts) / n
    den = sum((p[0] - mt) ** 2 for p in pts)
    return None if den <= 0 else sum((p[0] - mt) * (p[1] - mp) for p in pts) / den * 3600.0


def akl_nominal_wh():
    try:
        return float(CFG["ups_mah"]) * 4 * 3.6 * 0.9 / 1000.0
    except (TypeError, ValueError):
        return 0.0


def akl_cap_wh():
    """the capacity used for the forecast: learned (from 2 long discharges on) or the nominal one"""
    c = AKL["cap_wh"]
    return float(c) if c and int(AKL["cap_n"] or 0) >= 2 else akl_nominal_wh()


def akl_learn(now, pct, on_batt, charging, watts, wsrc):
    A = AKL
    if pct is None:
        return
    if on_batt:
        if A["last_pct"] is not None and pct < A["last_pct"]:
            A["cyc_pct"] = float(A["cyc_pct"] or 0) + (A["last_pct"] - pct)       # equivalent full cycles = sum / 100
        if not A["dis"] or now - A["dis"][-1][0] >= 60:
            A["dis"].append((now, pct)); A["dis"] = [s for s in A["dis"] if now - s[0] <= 3 * 3600]
        if now - A["rate_t"] >= 600:
            r = akl_rate(A["dis"], 60, 2)
            if r is not None and r < 0:
                A["rate_t"] = now
                old = A["rate_dis"]
                A["rate_dis"] = round(-r if not old else 0.7 * float(old) + 0.3 * -r, 3)
        sp = A["span"]
        if sp is None:
            A["span"] = sp = {"t0": now, "p0": pct, "e": 0.0, "ok": True, "t": now, "done": False}
        dt = min(60.0, now - sp["t"]); sp["t"] = now
        sp["e"] += watts * dt / 3600.0
        sp["ok"] = sp["ok"] and wsrc == "pmic"
        if not sp["done"] and sp["p0"] - pct >= 60:
            akl_span_end(now, pct)
    else:
        if A["span"] is not None:
            akl_span_end(now, pct)
        A["span"] = None; A["dis"] = []
    if charging:
        if not A["chg"] or now - A["chg"][-1][0] >= 60:
            A["chg"].append((now, pct)); A["chg"] = [s for s in A["chg"] if now - s[0] <= 3600]
        r = akl_rate(A["chg"], 30, 1)
        A["rate_chg"] = round(r, 3) if r and r > 0 else None
    else:
        A["chg"] = []; A["rate_chg"] = None
    A["last_pct"] = pct


def akl_span_end(now, pct):
    sp = AKL["span"]
    if not sp or sp["done"]:
        return
    sp["done"] = True
    d = sp["p0"] - pct
    if not (sp["ok"] and d >= 30 and now - sp["t0"] >= 7200):
        return
    cap = sp["e"] / (d / 100.0); nom = akl_nominal_wh()
    if nom and not 0.3 * nom <= cap <= 1.3 * nom:
        log_event("sys", f"Battery capacity: {cap:.1f} Wh from a long discharge is not plausible - ignored")
        return
    old = AKL["cap_wh"]
    AKL["cap_wh"] = round(cap if not old else 0.7 * float(old) + 0.3 * cap, 2); AKL["cap_n"] = int(AKL["cap_n"] or 0) + 1
    log_event("sys", f"Battery capacity learned: {cap:.1f} Wh ({d:.0f} % in {(now - sp['t0']) / 3600:.1f} h) -> {AKL['cap_wh']:.1f} Wh")
    akl_save(True)


def akl_health():
    """{cycles, health %, cap_wh, aging} for the battery card"""
    cyc = round(float(AKL["cyc_pct"] or 0) / 100.0, 1)
    nom = akl_nominal_wh(); cap = AKL["cap_wh"]; n = int(AKL["cap_n"] or 0)
    h = int(round(100.0 * float(cap) / nom)) if cap and nom and n >= 1 else None
    return {"cycles": cyc, "health": h, "cap_wh": cap, "cap_n": n, "aging": bool((h is not None and h < 80 and n >= 2) or cyc >= 500)}


def akl_more(bm, b, now, pct, on_batt, why):
    """learning and the display of the battery card (after akl_tick of the main file)"""
    try:
        w, wsrc = bm.watts()
    except Exception:
        w, wsrc = float(b.get("use_w") or 3.0), "estimate"
    akl_learn(now, pct, on_batt, bool(b.get("charging")), w, wsrc)
    if AKL["blocked"]:
        b["charging"] = False                                 # switched off in this reading already
    if why == "emergency" and pct is not None:
        akl_push("emerg", "Battery only {pct} %: it charges although it is cold ({t} °C) - charging in the cold harms the cells.",
                 pct=pct, t=f"{AKL['temp']:.1f}" if AKL["temp"] is not None else "?")
        if "emerg_log" not in AKL["pushed"]:
            AKL["pushed"].add("emerg_log"); log_event("sys", f"Emergency charging: battery {pct} % - charging despite the cold")
    elif not AKL["emerg"]:
        AKL["pushed"].discard("emerg"); AKL["pushed"].discard("emerg_log")
    t, src = AKL["temp"], AKL["temp_src"]
    no_bme = not src
    if CFG.get("chg_cold_on") and no_bme and b.get("charging"):
        env = STATE.get("env") or {}
        ot = env.get("t") if env.get("src") and env.get("src") not in AKL_BME else None
        if ot is not None and float(ot) < float(CFG["chg_cold_c"]) and now - AKL["warn_t"] > 12 * 3600:
            AKL["warn_t"] = now
            log_event("sys", f"Charging at {float(ot):.1f} °C ({env.get('src')}): without a BME280 MoveEye cannot stop it")
            w_ = WATCH_REF.get("w")
            if w_ is not None and CFG.get("ups_push", True):
                w_.notifier.info(trf("It is {t} °C and the battery charges. Without a BME280 in the case MoveEye cannot stop the charging.",
                                     t=f"{float(ot):.1f}"), title="{name}: " + tr("Battery"))
    cap = akl_cap_wh(); rd = AKL["rate_dis"]
    if on_batt and rd and float(rd) > 0.05 and pct is not None:
        b["hours"] = round(pct / float(rd), 1)
        b["use_w"] = round(float(rd) / 100.0 * cap, 1); b["use_src"] = "learned"; b["cap_wh"] = round(cap, 1)
    elif rd and float(rd) > 0.05:
        b["learned_w"] = round(float(rd) / 100.0 * cap, 1)
    if b.get("charging") and AKL["rate_chg"] and pct is not None:
        tgt = int(CFG["chg_care_max"]) if CFG.get("chg_care") else 100
        b["full_min"] = int(round(max(0, tgt - pct) / float(AKL["rate_chg"]) * 60.0)) if pct < tgt else None
    b["health"] = akl_health()
    b["chg_ctl"] = {"blocked": bool(AKL["blocked"]), "why": why, "cold": bool(AKL["cold"]), "emerg": bool(AKL["emerg"]),
                    "until": float(AKL["override_until"] or 0), "temp": t, "temp_src": src, "no_bme": no_bme,
                    "cold_on": bool(CFG.get("chg_cold_on")), "care": bool(CFG.get("chg_care")), "care_max": int(CFG["chg_care_max"]),
                    "resume": round(float(CFG["chg_cold_c"]) + float(CFG["chg_cold_hyst"]), 1), "emerg_pct": int(CFG["chg_emerg_pct"]),
                    "hours": float(CFG["chg_override_h"])}
    STATE["battery"] = b


def akl_override(on=True, who="web"):
    """«Charge anyway»: for chg_override_h hours, then the cold protection holds again. Push + log."""
    akl_load()
    if on:
        h = max(0.25, min(6.0, float(CFG.get("chg_override_h") or 1.0)))
        AKL["override_until"] = akl_now() + h * 3600.0
        log_event("sys", f"Charge anyway ({who}): for {h:g} h, the cold protection is off until then")
        w = WATCH_REF.get("w")
        if w is not None:
            try:
                w.notifier.info(trf("Charge anyway for {h} h (cold protection off) – charging below 0 °C harms the cells.", h=f"{h:g}"),
                                title="{name}: " + tr("Battery"))
            except Exception:
                pass
    else:
        AKL["override_until"] = 0.0
        log_event("sys", f"Charge anyway ended ({who})")
    akl_save(True)
    return True, ""


# ---- settings (schema: 570 / 030), help, texts -----------------------------------------------------------------------------------
TOGGLES.extend([
    ("Battery", "chg_cold_on", "Cold protection: no charging below the limit (BME280 in the case)"),
    ("Battery", "chg_care", "Protect the battery: on mains charge only up to the limit"),
])
SLIDERS.extend([
    ("Battery", "chg_cold_c", "Cold protection: no charging below (°C)", -10.0, 10.0, 0.5),
    ("Battery", "chg_cold_hyst", "Cold protection: charge again from the limit + (K)", 1.0, 10.0, 0.5),
    ("Battery", "chg_emerg_pct", "Emergency: below this charge level it charges anyway (%)", 0, 30, 1),
    ("Battery", "chg_override_h", "«Charge anyway»: valid for (hours)", 0.5, 6.0, 0.5),
    ("Battery", "chg_care_max", "Protect the battery: charge up to (%)", 60, 95, 1),
    ("Battery", "chg_care_resume", "Protect the battery: charge again below (%)", 50, 90, 1),
    ("Lights", "light_white_pct", "White light: brightness (%)", 5, 100, 5),
    ("Lights", "light_ir_pct", "Infrared light: brightness (%)", 5, 100, 5),
])
_AKL_LEVEL = "Charging off = GPIO 16 level"
TEXTS.append(("Battery", "chg_off_level", _AKL_LEVEL, "enum", "chg_level"))
TEXT_SPECS["chg_off_level"] = ("enum", "chg_level")
SET_HELP.update({
    "chg_cold_on": ("Lithium cells must not be charged below 0 °C (they lose capacity for good). The Geekworm X1206 has no temperature "
                    "protection of its own: MoveEye switches the charging off with GPIO 16 while the BME280 in the case is too cold. "
                    "Without a BME280 there is only a warning.", "On."),
    "chg_care": ("Lithium cells live longer when they are not kept at 100 %. On mains MoveEye charges only up to the limit and again "
                 "below the lower value. Off when you need the whole battery (a night without mains).", "Off, on for a long stay on mains."),
    "chg_emerg_pct": ("Below this charge level the battery charges even in the cold (with a push): an empty battery would switch "
                      "MoveEye off.", "10 %."),
    "chg_off_level": ("Which level of GPIO 16 switches the charging of the X1206 off. Geekworm (X120x): high = off. Change it only if "
                      "the board charges while MoveEye shows «Charging off».", "high (Geekworm)."),
    "light_white_pct": ("Brightness of the white light on the PCA9685 (PWM). 100 % = fully on as before. A light on a GPIO stays on / off.", "100 %."),
    "light_ir_pct": ("Brightness of the infrared light on the PCA9685 (PWM). Less = less current, but the night picture gets darker.", "100 %."),
})
SET_HELP.setdefault("pan_servo_range", ("With a 270° servo the head turns ±135°: raise «Pan limit» to 135° to use the whole range "
                                        "(less = protects the cables). Patrol, taught points, zones and the simulator follow.", "As the servo: 180, 270 or 360."))
_text_choice_pairs_akl_base = text_choice_pairs


def text_choice_pairs(key):                               # + 639zzzzz: the level of GPIO 16
    if (TEXT_SPECS.get(key) or (None, None))[1] == "chg_level":
        return [("high", tr("high (Geekworm)")), ("low", tr("low"))]
    return _text_choice_pairs_akl_base(key)


def akl_lines(b, L=None):
    """the extra lines of the battery card (window; the page builds the same with t())"""
    out = []
    c = b.get("chg_ctl") or {}
    if c.get("why") == "cold":
        out.append("🧊 " + trf("Charging off: too cold ({t} °C) – again from {lim} °C", L, t=f"{c.get('temp') or 0:.1f}",
                              lim=f"{float(CFG['chg_cold_c']) + float(CFG['chg_cold_hyst']):g}"))
    elif c.get("why") == "care":
        out.append("🌿 " + trf("Charging paused: protect the battery (up to {max} %)", L, max=c.get("care_max")))
    elif c.get("why") == "emergency":
        out.append("⚠ " + trf("Emergency charging: below {pct} % it charges despite the cold", L, pct=CFG["chg_emerg_pct"]))
    if c.get("until") and c.get("until") > time.time():
        out.append("⏱ " + trf("Charge anyway until {time}", L, time=datetime.fromtimestamp(c["until"]).strftime("%H:%M")))
    if c.get("cold_on") and c.get("no_bme"):
        out.append("ℹ " + tr("No BME280 in the case: no cold protection, only a warning", L))
    h = b.get("health") or {}
    if h:
        s = trf("{n} full cycles", L, n=f"{h.get('cycles', 0):g}") + " · " + (
            trf("capacity {h} % ({wh} Wh)", L, h=h["health"], wh=f"{h['cap_wh']:.1f}") if h.get("health") is not None
            else tr("capacity: still learning (needs a long discharge)", L))
        out.append("♻ " + s)
        if h.get("aging"):
            out.append("⚠ " + tr("The cells are aging – plan new ones", L))
    w = b.get("use_w") if b.get("use_src") == "learned" else b.get("learned_w")
    if w:
        out.append("📈 " + trf("consumption learned: {w} W", L, w=w))
    return out


def akl_api(d):
    a = str(d.get("action") or "")
    if a == "override":
        return akl_override(True, "web")
    if a == "override_end":
        return akl_override(False, "web")
    return False, "unknown action"


_akl_sx_routes_before = sx_routes


def sx_routes(app, watch, reply, body):                    # + /api/akku2 (called once by 550; not in VIEW_POST = administrator only)
    _akl_sx_routes_before(app, watch, reply, body)

    @app.route("/api/akku2", methods=["POST"])
    def api_akku2():
        ok, err = akl_api(body())
        return reply({"ok": ok, "error": tr(err) if err else ""}, 200 if ok else 400)


AKL_HTML = r"""
<style id="akl-css">
#akl-box{margin-top:6px;font-size:14px;line-height:1.45;white-space:pre-line}
#akl-box .akl-warn{color:var(--yel);font-weight:600}
#akl-btns{margin-top:6px;display:flex;gap:6px;flex-wrap:wrap}
</style>
<script>
// 639zzzzz: battery card - charging control (cold, protect, emergency), cycles / capacity, learned consumption, «Charge anyway»
(function () {
  const tt = (k, o) => { let s = t(k); for (const n in (o || {})) s = s.split("{" + n + "}").join(o[n]); return s; };
  const hm = ts => new Date(ts * 1000).toLocaleTimeString(LOCALE(LANG), {hour: "2-digit", minute: "2-digit"});
  window.aklLines = function (b) {
    const out = [], c = b.chg_ctl || {};
    if (c.why === "cold") out.push("🧊 " + tt("Charging off: too cold ({t} °C) – again from {lim} °C", {t: (c.temp || 0).toFixed(1), lim: c.resume}));
    else if (c.why === "care") out.push("🌿 " + tt("Charging paused: protect the battery (up to {max} %)", {max: c.care_max}));
    else if (c.why === "emergency") out.push("⚠ " + tt("Emergency charging: below {pct} % it charges despite the cold", {pct: c.emerg_pct}));
    if (c.until && c.until * 1000 > Date.now()) out.push("⏱ " + tt("Charge anyway until {time}", {time: hm(c.until)}));
    if (c.cold_on && c.no_bme) out.push("ℹ " + t("No BME280 in the case: no cold protection, only a warning"));
    const h = b.health;
    if (h) {
      out.push("♻ " + tt("{n} full cycles", {n: h.cycles}) + " · " + (h.health != null ? tt("capacity {h} % ({wh} Wh)", {h: h.health, wh: Number(h.cap_wh).toFixed(1)})
        : t("capacity: still learning (needs a long discharge)")));
      if (h.aging) out.push("⚠ " + t("The cells are aging – plan new ones"));
    }
    const w = b.use_src === "learned" ? b.use_w : b.learned_w;
    if (w) out.push("📈 " + tt("consumption learned: {w} W", {w: w}));
    return out;
  };
  async function act(a) {
    const r = await post("/api/akku2", {action: a, lang: LANG});
    if (!r || !r.ok) { toast("⚠ " + ((r && r.error) || t("Only the administrator can do this."))); return; }
    refresh();
  }
  window.aklPaint = function (s) {
    const bl = $("#batt-line"), b = (s && s.battery) || {}; if (!bl) return;
    let box = $("#akl-box");
    if (b.model !== "x12") { if (box) box.hidden = true; return; }
    if (!box) { box = el("div", "mut"); box.id = "akl-box"; bl.after(box); }
    box.hidden = false; box.textContent = "";
    for (const ln of aklLines(b)) box.appendChild(el("div", ln.startsWith("⚠") || ln.startsWith("🧊") ? "akl-warn" : "", ln));
    const c = b.chg_ctl || {}, admin = !s.me || s.me.role === "admin";
    if (!admin) return;
    const bt = el("div", ""); bt.id = "akl-btns";
    if (c.why === "cold" || c.why === "care") {
      const go = el("button", "sec", "⚡ " + t("Charge anyway")); go.type = "button";
      go.onclick = () => { if (confirm(tt("Charge although it is cold? Charging lithium cells below 0 °C can damage them for good. Only in an emergency. Valid for {h} h, then charging is blocked again.", {h: c.hours || 1}))) act("override"); };
      bt.appendChild(go);
    }
    if (c.until && c.until * 1000 > Date.now()) { const e = el("button", "sec", t("End «Charge anyway»")); e.type = "button"; e.onclick = () => act("override_end"); bt.appendChild(e); }
    if (bt.firstChild) box.appendChild(bt);
  };
  const base = paintExtras;
  paintExtras = function (s) { base(s); try { aklPaint(s); } catch (e) {} };
})();
</script>
"""


# ---- Pi window: lines and buttons in «Battery» ------------------------------------------------------------------------------------
_akl_tk_extras_base = App._tk_extras


def _akl_tk_extras(self, st):
    _akl_tk_extras_base(self, st)
    try:
        b = st.get("battery") or {}
        lbl = self.status_labels.get("Battery")
        if b.get("model") == "x12" and lbl is not None:
            extra = akl_lines(b)
            if extra:
                lbl.config(text=lbl.cget("text") + "\n" + "\n".join(extra))
        bb = getattr(self, "_akl_btn", None)
        if bb is not None and bb.winfo_exists():
            c = b.get("chg_ctl") or {}
            bb.config(state="normal" if c.get("why") in ("cold", "care") else "disabled")
            eb = self._akl_end
            eb.config(state="normal" if c.get("until") and c["until"] > time.time() else "disabled")
    except Exception as e:
        if not getattr(self, "_akl_err", False):
            self._akl_err = True; log_event("sys", f"Window: battery lines: {e}"[:160])


# wraps: App._tk_extras (570)
App._tk_extras = _akl_tk_extras
_akl_tk_build_section_base = App._build_section


def _akl_tk_build_section(self, sec, sbody, settings_parent=None):
    _akl_tk_build_section_base(self, sec, sbody, settings_parent)
    if sec != "Battery" or CFG["lock_on"]:
        return
    try:
        bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(4, 0))

        def go():
            h = f"{float(CFG['chg_override_h']):g}"
            if messagebox.askyesno("MoveEye", trf("Charge although it is cold? Charging lithium cells below 0 °C can damage them for good. Only in an emergency. Valid for {h} h, then charging is blocked again.", h=h), parent=self.root):
                akl_override(True, "window")
        self._akl_btn = ttk.Button(bf, text="⚡ " + tr("Charge anyway"), command=go, state="disabled")
        self._akl_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._akl_end = ttk.Button(bf, text=tr("End «Charge anyway»"), command=lambda: akl_override(False, "window"), state="disabled")
        self._akl_end.pack(side="left", expand=True, fill="x")
    except Exception as e:
        log_event("sys", f"Window: charge anyway: {e}"[:160])


# wraps: App._build_section (570)
App._build_section = _akl_tk_build_section


_HX_AKL = {
    "Cold protection: no charging below the limit (BME280 in the case)": (
        "Kälteschutz: unter der Grenze nicht laden (BME280 im Gehäuse)", "Protection contre le froid : ne pas charger sous la limite (BME280 dans le boîtier)",
        "Protezione dal freddo: non caricare sotto il limite (BME280 nella custodia)", "Protecziun cunter la fradaglia: betg chargiar sut il cunfin (BME280 en la chascha)"),
    "Protect the battery: on mains charge only up to the limit": (
        "Akku schonen: am Netz nur bis zur Grenze laden", "Ménager la batterie : sur secteur, charger seulement jusqu'à la limite",
        "Proteggere la batteria: con la rete caricare solo fino al limite", "Schanegiar l'accu: a la rait chargiar mo fin al cunfin"),
    "Cold protection: no charging below (°C)": ("Kälteschutz: nicht laden unter (°C)", "Protection contre le froid : ne pas charger sous (°C)",
                                                "Protezione dal freddo: non caricare sotto (°C)", "Protecziun cunter la fradaglia: betg chargiar sut (°C)"),
    "Cold protection: charge again from the limit + (K)": ("Kälteschutz: wieder laden ab Grenze + (K)", "Protection contre le froid : recharger dès la limite + (K)",
                                                           "Protezione dal freddo: ricaricare dal limite + (K)", "Protecziun cunter la fradaglia: puspè chargiar a partir dal cunfin + (K)"),
    "Emergency: below this charge level it charges anyway (%)": ("Notfall: unter diesem Ladestand lädt es trotzdem (%)", "Urgence : sous ce niveau, la charge se fait quand même (%)",
                                                                 "Emergenza: sotto questo livello carica comunque (%)", "Urgenza: sut quest stadi da chargia chargia el tuttina (%)"),
    "«Charge anyway»: valid for (hours)": ("«Trotzdem laden»: gilt für (Stunden)", "« Charger quand même » : valable pendant (heures)",
                                           "«Carica comunque»: vale per (ore)", "«Tuttina chargiar»: vala per (uras)"),
    "Protect the battery: charge up to (%)": ("Akku schonen: laden bis (%)", "Ménager la batterie : charger jusqu'à (%)", "Proteggere la batteria: caricare fino a (%)",
                                              "Schanegiar l'accu: chargiar fin (%)"),
    "Protect the battery: charge again below (%)": ("Akku schonen: wieder laden unter (%)", "Ménager la batterie : recharger sous (%)",
                                                    "Proteggere la batteria: ricaricare sotto (%)", "Schanegiar l'accu: puspè chargiar sut (%)"),
    "White light: brightness (%)": ("Weisses Licht: Helligkeit (%)", "Lumière blanche : luminosité (%)", "Luce bianca: luminosità (%)", "Glisch alva: clerezza (%)"),
    "Infrared light: brightness (%)": ("Infrarot-Licht: Helligkeit (%)", "Lumière infrarouge : luminosité (%)", "Luce infrarossa: luminosità (%)", "Glisch infracotschna: clerezza (%)"),
    _AKL_LEVEL: ("Laden aus = Pegel an GPIO 16", "Charge coupée = niveau du GPIO 16", "Carica spenta = livello del GPIO 16", "Chargiar ora = nivel dal GPIO 16"),
    "high (Geekworm)": ("hoch (Geekworm)", "haut (Geekworm)", "alto (Geekworm)", "aut (Geekworm)"),
    "low": ("tief", "bas", "basso", "bass"),
    "Charging off: too cold ({t} °C) – again from {lim} °C": ("Laden aus: zu kalt ({t} °C) – wieder ab {lim} °C", "Charge coupée : trop froid ({t} °C) – de nouveau dès {lim} °C",
                                                              "Carica spenta: troppo freddo ({t} °C) – di nuovo da {lim} °C", "Chargiar ora: memia fraid ({t} °C) – puspè a partir da {lim} °C"),
    "Charging paused: protect the battery (up to {max} %)": ("Laden pausiert: Akku schonen (bis {max} %)", "Charge en pause : ménager la batterie (jusqu'à {max} %)",
                                                             "Carica in pausa: proteggere la batteria (fino a {max} %)", "Chargiar pausà: schanegiar l'accu (fin {max} %)"),
    "Emergency charging: below {pct} % it charges despite the cold": ("Notladen: unter {pct} % lädt es trotz Kälte", "Charge d'urgence : sous {pct} %, charge malgré le froid",
                                                                      "Carica d'emergenza: sotto {pct} % carica nonostante il freddo", "Chargiar d'urgenza: sut {pct} % chargia el malgrà la fradaglia"),
    "Charge anyway until {time}": ("Trotzdem laden bis {time}", "Charger quand même jusqu'à {time}", "Carica comunque fino alle {time}", "Tuttina chargiar fin las {time}"),
    "No BME280 in the case: no cold protection, only a warning": ("Kein BME280 im Gehäuse: kein Kälteschutz, nur eine Warnung",
                                                                   "Pas de BME280 dans le boîtier : pas de protection contre le froid, seulement un avertissement",
                                                                   "Nessun BME280 nella custodia: nessuna protezione dal freddo, solo un avviso",
                                                                   "Nagin BME280 en la chascha: nagina protecziun cunter la fradaglia, mo in avertiment"),
    "{n} full cycles": ("{n} Vollzyklen", "{n} cycles complets", "{n} cicli completi", "{n} ciclus cumplets"),
    "capacity {h} % ({wh} Wh)": ("Kapazität {h} % ({wh} Wh)", "capacité {h} % ({wh} Wh)", "capacità {h} % ({wh} Wh)", "capacitad {h} % ({wh} Wh)"),
    "capacity: still learning (needs a long discharge)": ("Kapazität: wird noch gelernt (braucht eine lange Entladung)", "capacité : encore en apprentissage (il faut une longue décharge)",
                                                          "capacità: ancora in apprendimento (serve una lunga scarica)", "capacitad: vegn anc emprendida (basegna ina lunga stgargiada)"),
    "The cells are aging – plan new ones": ("Die Zellen altern – neue einplanen", "Les cellules vieillissent – prévoir des neuves", "Le celle invecchiano – prevedere celle nuove",
                                             "Las cellas vegnan veglias – planisar novas"),
    "consumption learned: {w} W": ("Verbrauch gelernt: {w} W", "consommation apprise : {w} W", "consumo appreso: {w} W", "consum emprendì: {w} W"),
    "Charge anyway": ("Trotzdem laden", "Charger quand même", "Carica comunque", "Tuttina chargiar"),
    "End «Charge anyway»": ("«Trotzdem laden» beenden", "Arrêter « Charger quand même »", "Terminare «Carica comunque»", "Terminar «Tuttina chargiar»"),
    "Only the administrator can do this.": ("Das darf nur der Administrator.", "Seul l'administrateur peut le faire.", "Solo l'amministratore può farlo.",
                                            "Quai po far mo l'administratur."),
    "Charge although it is cold? Charging lithium cells below 0 °C can damage them for good. Only in an emergency. Valid for {h} h, then charging is blocked again.": (
        "Trotz Kälte laden? Lithium-Zellen unter 0 °C zu laden kann sie dauerhaft schädigen. Nur im Notfall. Gilt {h} h, danach ist das Laden wieder gesperrt.",
        "Charger malgré le froid ? Charger des cellules lithium sous 0 °C peut les abîmer pour de bon. Seulement en cas d'urgence. Valable {h} h, ensuite la charge est de nouveau bloquée.",
        "Caricare nonostante il freddo? Caricare celle al litio sotto 0 °C può danneggiarle per sempre. Solo in emergenza. Vale {h} h, poi la carica è di nuovo bloccata.",
        "Chargiar malgrà la fradaglia? Chargiar cellas da litium sut 0 °C las po donnegiar per adina. Mo en cas d'urgenza. Vala {h} h, lura è il chargiar puspè bloccà."),
    "Too cold to charge ({t} °C): charging is off until it is warmer. «Charge anyway» on the page.": (
        "Zu kalt zum Laden ({t} °C): das Laden ist aus, bis es wärmer ist. «Trotzdem laden» auf der Seite.",
        "Trop froid pour charger ({t} °C) : la charge est coupée jusqu'à ce qu'il fasse plus chaud. « Charger quand même » sur la page.",
        "Troppo freddo per caricare ({t} °C): la carica è spenta finché fa più caldo. «Carica comunque» sulla pagina.",
        "Memia fraid per chargiar ({t} °C): il chargiar è ora fin ch'i è pli chaud. «Tuttina chargiar» sin la pagina."),
    "Battery only {pct} %: it charges although it is cold ({t} °C) - charging in the cold harms the cells.": (
        "Akku nur noch {pct} %: es lädt trotz Kälte ({t} °C) – Laden in der Kälte schadet den Zellen.",
        "Batterie à {pct} % seulement : elle charge malgré le froid ({t} °C) – charger dans le froid abîme les cellules.",
        "Batteria solo al {pct} %: carica nonostante il freddo ({t} °C) – caricare al freddo danneggia le celle.",
        "Accu mo pli {pct} %: el chargia malgrà la fradaglia ({t} °C) – chargiar en la fradaglia donnegia las cellas."),
    "It is {t} °C and the battery charges. Without a BME280 in the case MoveEye cannot stop the charging.": (
        "Es ist {t} °C und der Akku lädt. Ohne BME280 im Gehäuse kann MoveEye das Laden nicht stoppen.",
        "Il fait {t} °C et la batterie charge. Sans BME280 dans le boîtier, MoveEye ne peut pas arrêter la charge.",
        "Ci sono {t} °C e la batteria carica. Senza BME280 nella custodia MoveEye non può fermare la carica.",
        "I fa {t} °C e l'accu chargia. Senza BME280 en la chascha na po MoveEye betg fermar il chargiar."),
    "Charge anyway for {h} h (cold protection off) – charging below 0 °C harms the cells.": (
        "Trotzdem laden für {h} h (Kälteschutz aus) – Laden unter 0 °C schadet den Zellen.",
        "Charger quand même pendant {h} h (protection contre le froid coupée) – charger sous 0 °C abîme les cellules.",
        "Carica comunque per {h} h (protezione dal freddo spenta) – caricare sotto 0 °C danneggia le celle.",
        "Tuttina chargiar per {h} h (protecziun cunter la fradaglia ora) – chargiar sut 0 °C donnegia las cellas."),
    SET_HELP["chg_cold_on"][0]: (
        "Lithium-Zellen dürfen unter 0 °C nicht geladen werden (sie verlieren dauerhaft Kapazität). Das Geekworm X1206 hat selbst keinen "
        "Temperaturschutz: MoveEye schaltet das Laden über GPIO 16 aus, solange der BME280 im Gehäuse zu kalt ist. Ohne BME280 gibt es nur eine Warnung.",
        "Les cellules lithium ne doivent pas être chargées sous 0 °C (elles perdent de la capacité pour de bon). Le Geekworm X1206 n'a pas de "
        "protection thermique : MoveEye coupe la charge par le GPIO 16 tant que le BME280 du boîtier est trop froid. Sans BME280, seulement un avertissement.",
        "Le celle al litio non vanno caricate sotto 0 °C (perdono capacità per sempre). Il Geekworm X1206 non ha una protezione termica: "
        "MoveEye spegne la carica con il GPIO 16 finché il BME280 nella custodia è troppo freddo. Senza BME280 c'è solo un avviso.",
        "Cellas da litium na dastgan betg vegnir chargiadas sut 0 °C (ellas perdan capacitad per adina). Il Geekworm X1206 n'ha nagina "
        "protecziun da temperatura: MoveEye stizza il chargiar cun GPIO 16 uschè ditg ch'il BME280 en la chascha è memia fraid. Senza BME280 dat i mo in avertiment."),
    SET_HELP["chg_care"][0]: (
        "Lithium-Zellen leben länger, wenn sie nicht dauernd auf 100 % stehen. Am Netz lädt MoveEye nur bis zur Grenze und erst unter dem unteren "
        "Wert wieder. Aus, wenn du den ganzen Akku brauchst (eine Nacht ohne Netz).",
        "Les cellules lithium vivent plus longtemps si elles ne restent pas à 100 %. Sur secteur, MoveEye charge seulement jusqu'à la limite et "
        "recharge sous la valeur basse. Désactivé si tu as besoin de toute la batterie (une nuit sans secteur).",
        "Le celle al litio durano di più se non restano sempre al 100 %. Con la rete MoveEye carica solo fino al limite e ricarica sotto il valore "
        "basso. Spento se ti serve tutta la batteria (una notte senza rete).",
        "Cellas da litium vivan pli ditg, sch'ellas na stattan betg adina sin 100 %. A la rait chargia MoveEye mo fin al cunfin e pir puspè sut la "
        "valur bassa. Ora, sche ti dovras l'entir accu (ina notg senza rait)."),
    SET_HELP["chg_emerg_pct"][0]: (
        "Unter diesem Ladestand lädt der Akku auch in der Kälte (mit Push): ein leerer Akku würde MoveEye ausschalten.",
        "Sous ce niveau, la batterie charge même dans le froid (avec push) : une batterie vide éteindrait MoveEye.",
        "Sotto questo livello la batteria carica anche al freddo (con push): una batteria vuota spegnerebbe MoveEye.",
        "Sut quest stadi chargia l'accu er en la fradaglia (cun push): in accu vid stizzass MoveEye."),
    SET_HELP["chg_off_level"][0]: (
        "Welcher Pegel an GPIO 16 das Laden des X1206 ausschaltet. Geekworm (X120x): hoch = aus. Nur ändern, wenn die Platine lädt, obwohl "
        "MoveEye «Laden aus» zeigt.",
        "Quel niveau du GPIO 16 coupe la charge du X1206. Geekworm (X120x) : haut = coupé. À changer seulement si la carte charge alors que "
        "MoveEye affiche « Charge coupée ».",
        "Quale livello del GPIO 16 spegne la carica dell'X1206. Geekworm (X120x): alto = spento. Cambiare solo se la scheda carica mentre "
        "MoveEye mostra «Carica spenta».",
        "Tge nivel dal GPIO 16 stizza il chargiar dal X1206. Geekworm (X120x): aut = ora. Midar mo, sche la platina chargia, schebain che "
        "MoveEye mussa «Chargiar ora»."),
    SET_HELP["light_white_pct"][0]: (
        "Helligkeit des weissen Lichts am PCA9685 (PWM). 100 % = ganz an wie bisher. Ein Licht an einem GPIO bleibt ein / aus.",
        "Luminosité de la lumière blanche sur le PCA9685 (PWM). 100 % = entièrement allumée comme avant. Une lumière sur un GPIO reste marche / arrêt.",
        "Luminosità della luce bianca sul PCA9685 (PWM). 100 % = tutta accesa come prima. Una luce su un GPIO resta acceso / spento.",
        "Clerezza da la glisch alva al PCA9685 (PWM). 100 % = dal tut envidada sco fin ussa. Ina glisch vi d'in GPIO resta envidada / stizzada."),
    SET_HELP["light_ir_pct"][0]: (
        "Helligkeit des Infrarot-Lichts am PCA9685 (PWM). Weniger = weniger Strom, aber das Nachtbild wird dunkler.",
        "Luminosité de la lumière infrarouge sur le PCA9685 (PWM). Moins = moins de courant, mais l'image de nuit devient plus sombre.",
        "Luminosità della luce infrarossa sul PCA9685 (PWM). Meno = meno corrente, ma l'immagine notturna diventa più scura.",
        "Clerezza da la glisch infracotschna al PCA9685 (PWM). Pli pauc = pli pauc current, ma il maletg da notg vegn pli stgir."),
    SET_HELP["pan_servo_range"][0]: (
        "Mit einem 270°-Servo dreht der Kopf ±135°: «Schwenk-Grenze» auf 135° stellen, um den ganzen Bereich zu nutzen (weniger = schont die "
        "Kabel). Patrouille, gespeicherte Punkte, Zonen und Simulator gehen mit.",
        "Avec un servo de 270°, la tête tourne de ±135° : mettre la « limite de panoramique » à 135° pour utiliser toute la plage (moins = "
        "ménage les câbles). Patrouille, points enregistrés, zones et simulateur suivent.",
        "Con un servo da 270° la testa ruota di ±135°: portare il «limite di rotazione» a 135° per usare tutto il campo (meno = protegge i "
        "cavi). Pattuglia, punti salvati, zone e simulatore seguono.",
        "Cun in servo da 270° sa volva il chau ±135°: metter il «cunfin da girar» sin 135° per duvrar l'entir sectur (pli pauc = schanegia "
        "ils cabels). Patrulgia, puncts memorisads, zonas e simulatur van cun."),
    "As the servo: 180, 270 or 360.": ("Wie der Servo: 180, 270 oder 360.", "Comme le servo : 180, 270 ou 360.", "Come il servo: 180, 270 o 360.",
                                       "Sco il servo: 180, 270 u 360."),
    "On.": ("An.", "Activé.", "Acceso.", "Activà."),
    "Off, on for a long stay on mains.": ("Aus, an für einen langen Aufenthalt am Netz.", "Désactivé, activé pour un long séjour sur secteur.",
                                          "Spento, acceso per una lunga permanenza con la rete.", "Ora, en per ina lunga dimora a la rait."),
    "10 %.": ("10 %.", "10 %.", "10 %.", "10 %."),
    "high (Geekworm).": ("hoch (Geekworm).", "haut (Geekworm).", "alto (Geekworm).", "aut (Geekworm)."),
    "100 %.": ("100 %.", "100 %.", "100 %.", "100 %."),
}
for _k, _v in _HX_AKL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
if 'id="akl-css"' not in WEB_PAGE:                          # the box and its script at the end of the main page (530)
    WEB_PAGE = WEB_PAGE.replace("</body>", "<script>try { Object.assign(I18N.de, " + json.dumps({k: v[0] for k, v in _HX_AKL.items()}, ensure_ascii=False)
                                + "); } catch (e) {}</script>" + AKL_HTML + "</body>", 1)


def akl_selftest():
    """charging control (cold with hysteresis, emergency, «Charge anyway», protect the battery), learning, texts - made-up clock and GPIO"""
    g_ = globals(); keep = {k: CFG.get(k) for k in AKL_DEF}; keep_a = {k: (set(v) if isinstance(v, set) else list(v) if isinstance(v, list) else v) for k, v in AKL.items()}
    keep_env = STATE.get("env"); sw = []; clk = [1.0e9]
    old_gpio, old_save = g_["akl_gpio16"], g_["akl_save"]
    try:
        g_["akl_gpio16"] = lambda blk: sw.append(blk) or ""
        g_["akl_save"] = lambda force=False: None
        CFG.update(AKL_DEF); AKL.update(now=lambda: clk[0], blocked=None, we_blocked=False, cold=False, care=False, emerg=False,
                                         override_until=0.0, temp=None, temp_src="", temp_t=0.0, err_t=0.0, pushed=set())
        def step(t, pct=60, batt=False):
            STATE["env"] = {"t": t, "src": "BME280"} if t is not None else None
            clk[0] += 30.0
            blk, why = akl_decide(clk[0], pct, batt); akl_apply(blk, why, pct)
            return why
        assert step(5.0) == "" and sw == [], "warm: GPIO 16 untouched"
        assert step(-1.0) == "cold" and sw == [True]
        assert step(1.5) == "cold" and step(2.9) == "cold" and sw == [True], "hysteresis: still blocked below 3 °C"
        assert step(3.0) == "" and sw == [True, False]
        step(-2.0); akl_override(True, "test")
        assert step(-2.0) == "override" and sw[-1] is False
        clk[0] += 3700.0
        assert step(-2.0) == "cold" and sw[-1] is True, "override over after 1 h"
        assert step(-2.0, pct=9) == "emergency" and sw[-1] is False and step(-2.0, pct=11) == "emergency" and step(-2.0, pct=13) == "cold"
        STATE["env"] = {"t": -5.0, "src": "DS18B20"}; clk[0] += 700.0
        assert akl_decide(clk[0], 60, False) == (False, ""), "without a BME280: never a block"
        CFG["chg_care"] = True
        assert step(20.0, pct=80) == "care" and step(20.0, pct=77) == "care" and step(20.0, pct=75) == "", "protect: 80 % / 75 %"
        assert step(20.0, pct=81, batt=True) == "", "on the battery: nothing to protect"
        assert akl_rate([(i * 60.0, 80 - i * 0.1) for i in range(61)], 60, 2) is not None
        r = akl_rate([(i * 60.0, 80 - i * 0.1) for i in range(61)], 60, 2)
        assert abs(r + 6.0) < 0.01, r
        for L_ in ("fr", "it", "rm"):
            for k in _HX_AKL:
                assert tr(k, L_) != k or k in ("10 %.", "100 %."), (L_, k)
        assert 'id="akl-css"' in WEB_PAGE and "aklPaint(s)" in WEB_PAGE
        return "cold block with hysteresis, override 1 h, emergency below 10 %, protect 80 / 75 %, no block without a BME280, SOC rate, 5 languages"
    finally:
        g_["akl_gpio16"], g_["akl_save"] = old_gpio, old_save
        CFG.update(keep); AKL.clear(); AKL.update(keep_a); AKL["now"] = None; STATE["env"] = keep_env


SELFTEST_EXTRA.append(("Battery gaps X1206: charging control, learning (639zzzzz)", akl_selftest))
'''
zd_exec(AKKU_LUECKEN_PY, '639zzzzz_akku_luecken.py')
