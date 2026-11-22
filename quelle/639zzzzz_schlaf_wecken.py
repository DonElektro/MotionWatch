#@ MoveEye – Teil 639zzzzz: Schlafen und Wecken mit der Uhr des Pi 5 (RTC-Weckalarm, Besitzer 21.11.2026) – feste Zeiten, nach der Sonne, nur bei leerem Akku, einmal «Schlafen bis …»; nur Admin. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entscheide Besitzer 21.11.2026:
#   * Schlafen = Weckzeit in /sys/class/rtc/rtc0/wakealarm (Sekunden seit 1970, UTC; als root direkt, sonst «sudo -n»), dann
#     sauber aus (400 power_action «poweroff», Quelle «sleep»). Die Uhr des Pi 5 weckt ihn.
#   * Arten (sleep_mode): «times» feste Zeiten (sleep_off .. sleep_on, auch über Mitternacht); «sun» nach der Sonne: schläft am
#     Tag, aus bei Sonnenaufgang + sleep_sun_min, an bei Sonnenuntergang − sleep_sun_min (030 sun_times, Ort aus Setup);
#     «low» nur bei leerem Akku (im Akkubetrieb unter sleep_low_pct, nicht beim Laden; weckt nach sleep_low_h Stunden);
#     dazu einmal «Schlafen bis …» (Knopf, Web + Fenster).
#     «times» / «sun» schlafen nur beim Übergang in die Schlafzeit: wer MoveEye in der Schlafzeit von Hand startet, wird nicht
#     gleich wieder schlafen gelegt. «low» frühestens 10 min nach dem Start.
#   * Nie während eines Alarms (639zzzh hp_quiet, Personen, Aufnahme, Verfolgen), eines Updates / Neustarts, mit dem Simulator;
#     nie solange der Schutz scharf ist, ausser der Admin wählt «Auch schlafen, wenn der Schutz scharf ist». Vorher ein Push.
#   * Geekworm X1206: schaltet den Strom ab, wenn der Pi aus ist. Ob der Weckalarm dann noch weckt, hängt am EEPROM des Pi 5
#     (POWER_OFF_ON_HALT, WAKE_ON_GPIO) und an der Platine – NICHT mit echter Hardware geprüft. MoveEye liest das EEPROM nur
#     (rpi-eeprom-config) und ändert es nie. Nach jedem Schlaf prüft MoveEye beim Start, ob es zur geplanten Zeit aufwachte
#     (Protokoll; Push, wenn es viel später kam). Die Anleitung erklärt die Einstellungen und den Test mit 10 min.
# Alles ausser den Standardwerten steht im Literal SCHLAF_PY (Zusatz-ZIP): Schlafen ist keine Start-, Schutz-, Alarm- oder
# Update-Funktion; ohne ZIP schläft MoveEye einfach nie. Test: werkzeuge/x1206_test.py Teil 9.
# ----------------------------------------------------------------------------
SLP_DEF = {"sleep_mode": "off", "sleep_off": "09:00", "sleep_on": "18:00", "sleep_sun_min": 30, "sleep_low_pct": 30,
           "sleep_low_h": 4, "sleep_armed_ok": False}
for _k, _v in SLP_DEF.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update(SLP_DEF)                         # sleeping: only the administrator
LOCK_DENY_KEYS.update(SLP_DEF)

SCHLAF_PY = r'''SLP_RTC = "/sys/class/rtc/rtc0/wakealarm"
SLP_FILE = "schlaf.json"
SLP = {"was_in": None, "pending": False, "status": "", "n": "", "eeprom": None, "eeprom_t": -1e9, "started": False, "last": None,
       "now": None, "rtc": None}
SLP_MODES = ("off", "times", "sun", "low")


def slp_now():
    return SLP["now"]() if callable(SLP["now"]) else datetime.now()


def _slp_hm(s, d):
    m = _HM_RE.match(str(s or "").strip())
    return d if not m else int(m.group(1)) * 60 + int(m.group(2))


def slp_window(now, b=None):
    """(in the sleep time now, wake datetime or None, why) for the chosen sleep_mode"""
    mode = CFG.get("sleep_mode"); b = b or {}
    day0 = datetime(now.year, now.month, now.day)
    mins = now.hour * 60 + now.minute + now.second / 60.0
    if mode == "times":
        a, e = _slp_hm(CFG.get("sleep_off"), 540), _slp_hm(CFG.get("sleep_on"), 1080)
        if a == e:
            return False, None, ""
        inw = a <= mins < e if a < e else (mins >= a or mins < e)
        wake = day0 + timedelta(minutes=e)
        if wake <= now:
            wake += timedelta(days=1)
        return inw, wake, "fixed times"
    if mode == "sun":
        try:
            st = sun_times(now.date(), float(CFG["latitude"]), float(CFG["longitude"]))
        except (TypeError, ValueError):
            return False, None, ""
        if isinstance(st, str):
            return False, None, ""                               # polar day / night: no sunrise
        x = float(CFG.get("sleep_sun_min") or 0)
        a, e = st[0] + x, st[1] - x
        if a >= e:
            return False, None, ""
        return a <= mins < e, day0 + timedelta(minutes=e), "by the sun"
    if mode == "low":
        pct = b.get("pct")
        low = b.get("on_battery") and not b.get("charging") and pct is not None and pct < int(CFG.get("sleep_low_pct") or 30)
        return bool(low), now + timedelta(hours=float(CFG.get("sleep_low_h") or 4)), "battery low"
    return False, None, ""


def slp_next(now):
    """(next sleep start, its wake) for the display - fixed times / sun only"""
    if CFG.get("sleep_mode") not in ("times", "sun"):
        return None, None
    for d in range(0, 3):
        base = datetime(now.year, now.month, now.day) + timedelta(days=d)
        if CFG["sleep_mode"] == "times":
            a = base + timedelta(minutes=_slp_hm(CFG.get("sleep_off"), 540))
        else:
            try:
                st = sun_times(base.date(), float(CFG["latitude"]), float(CFG["longitude"]))
            except (TypeError, ValueError):
                return None, None
            if isinstance(st, str):
                continue
            a = base + timedelta(minutes=st[0] + float(CFG.get("sleep_sun_min") or 0))
        if a > now:
            inw, wake, _w = slp_window(a + timedelta(seconds=30))
            if inw:
                return a, wake
    return None, None


def slp_rtc_ok():
    if SLP["rtc"] is None:
        SLP["rtc"] = os.path.exists(SLP_RTC)
    return SLP["rtc"]


def slp_block():
    """why not to sleep now ("" = it may)"""
    try:
        if not hp_quiet() or STATE.get("tracking") or STATE.get("persons") or STATE.get("recording"):
            return "an alarm is going on"
    except Exception:
        pass
    if is_armed() and not CFG.get("sleep_armed_ok"):
        return "the protection is armed"
    if UPD_PROG.get("phase") or RESTART.get("pending") or POWER.get("pending"):
        return "an update or restart is running"
    if CFG.get("sim_on"):
        return "the simulator is connected"
    if not slp_rtc_ok():
        return "no RTC wake alarm on this device"
    return ""


def slp_write_alarm(ts):
    """the wake time into the RTC of the Pi 5 -> "" or the error"""
    ts = int(ts)
    try:
        with open(SLP_RTC, "w") as f:
            f.write("0")
        with open(SLP_RTC, "w") as f:
            f.write(str(ts))
        return ""
    except OSError as e:
        err = str(e)
    if not _is_root() and shutil.which("sudo"):
        rc, _o, e = _run(["sudo", "-n", "sh", "-c", f"echo 0 > {SLP_RTC} && echo {ts} > {SLP_RTC}"], timeout=10)
        if rc == 0:
            return ""
        err = e or f"exit {rc}"
    return "no permission to set the wake alarm (" + err[:80] + ")"


def slp_eeprom():
    """{POWER_OFF_ON_HALT, WAKE_ON_GPIO} of the Pi 5 bootloader (read only, never changed), cached 1 h; values the
    config does not name are the defaults of the Pi 5 (0 / 1)"""
    if time.monotonic() - SLP["eeprom_t"] < 3600:
        return SLP["eeprom"]
    SLP["eeprom_t"] = time.monotonic(); out = None
    if shutil.which("rpi-eeprom-config"):
        rc, txt, _e = _run(["rpi-eeprom-config"], timeout=15)
        if rc == 0:
            out = {"POWER_OFF_ON_HALT": "0", "WAKE_ON_GPIO": "1"}
            for ln in (txt or "").splitlines():
                k, _s, v = ln.strip().partition("=")
                if k in out and v.strip():
                    out[k] = v.strip()
    SLP["eeprom"] = out
    return out


def slp_save_plan(d):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = os.path.join(DATA_DIR, SLP_FILE + ".part")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, os.path.join(DATA_DIR, SLP_FILE))
    except OSError:
        pass


def slp_sleep(wake, why, who="auto", check=True):
    """write the wake alarm, push, clean poweroff. -> (ok, error)"""
    now = slp_now()
    if not isinstance(wake, datetime):
        return False, "invalid time"
    if not timedelta(minutes=5) <= wake - now <= timedelta(days=7):
        return False, "the wake-up time must be 5 min to 7 days ahead"
    blk = slp_block() if check else ""
    if blk:
        return False, blk
    ts = int(wake.timestamp())
    err = slp_write_alarm(ts)
    if err:
        log_event("sys", f"Sleep: {err}")
        return False, err
    slp_save_plan({"wake": ts, "t": time.time(), "why": why, "who": who})
    w_ = wake.strftime("%a %H:%M")
    log_event("sys", f"Sleep until {w_} ({why}, {who}) - RTC wake alarm set, shutting down")
    w = WATCH_REF.get("w")
    if w is not None:
        try:
            w.notifier.info(trf("MoveEye sleeps until {time} ({why}) – nothing is watched until then.", time=w_, why=tr(why)),
                            title="{name}: " + tr("Sleep"))
        except Exception:
            pass
    SLP["last"] = ts
    power_action("poweroff", delay=15.0, source="sleep")
    return True, ""


def slp_wake_check():
    """after a sleep: did the Pi wake up at the planned time? (log; push when much later - the X1206 may have cut the power)"""
    p = os.path.join(DATA_DIR, SLP_FILE)
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        os.remove(p)
    except (OSError, ValueError):
        return None
    try:
        with open("/proc/uptime") as f:
            boot = time.time() - float(f.read().split()[0])
    except (OSError, ValueError, IndexError):
        boot = RUNGUARD["t0"]
    wake = float(d.get("wake") or 0)
    if not wake:
        return None
    pl, st = datetime.fromtimestamp(wake).strftime("%a %H:%M"), datetime.fromtimestamp(boot).strftime("%a %H:%M")
    if boot > wake + 900:
        log_event("sys", f"Wake-up came late: planned {pl}, started {st} - the RTC alarm did not start the Pi (X1206 power cut? EEPROM?)")
        w = WATCH_REF.get("w")
        if w is not None:
            try:
                w.notifier.info(trf("The wake-up did not come as planned ({plan}, started {start}). The X1206 may cut the power at shutdown – see the guide (EEPROM).",
                                    plan=pl, start=st), title="{name}: " + tr("Sleep"))
            except Exception:
                pass
        return "late"
    if boot < wake - 300:
        log_event("sys", f"Started before the planned wake-up ({pl}, started {st}) - by the button or the power")
        return "early"
    log_event("sys", f"Woke up as planned ({pl}, started {st})")
    return "ok"


def slp_tick():
    now = slp_now(); b = STATE.get("battery") or {}
    mode = CFG.get("sleep_mode")
    inw, wake, why = slp_window(now, b)
    if mode in ("times", "sun"):
        if SLP["was_in"] is False and inw:
            SLP["pending"] = True
        if not inw:
            SLP["pending"] = False
        SLP["was_in"] = inw
    elif mode == "low":
        SLP["pending"] = inw and time.time() - RUNGUARD["t0"] > 600
        SLP["was_in"] = inw
    else:
        SLP.update(pending=False, was_in=None)
    nx, nw = slp_next(now)
    st = {"mode": mode, "next": nx.timestamp() if nx else None, "next_wake": nw.timestamp() if nw else None,
          "rtc": slp_rtc_ok(), "eeprom": slp_eeprom(), "status": "", "why": ""}
    if SLP["pending"] and wake is not None:
        blk = slp_block()
        if blk:
            st.update(status="waiting", why=blk)
        else:
            ok, err = slp_sleep(wake, why, "auto")
            SLP["pending"] = False
            st.update(status="sleeping" if ok else "failed", why=err)
    STATE["sleep"] = st
    return st


def slp_loop():
    time.sleep(20)
    try:
        slp_wake_check()
    except Exception as e:
        log_event("sys", f"Sleep: wake-up check: {e}"[:160])
    while True:
        try:
            slp_tick()
        except Exception as e:
            log_event("sys", f"Sleep: {e}"[:160])
        time.sleep(30)


def slp_thread():
    if not SLP["started"]:
        SLP["started"] = True
        threading.Thread(target=slp_loop, daemon=True, name="sleep").start()


def slp_parse_until(v):
    """«YYYY-MM-DDTHH:MM» / «YYYY-MM-DD HH:MM» / «HH:MM» (the next time it comes) / epoch seconds -> datetime or None"""
    s = str(v or "").strip(); now = slp_now()
    try:
        if re.fullmatch(r"\d{9,11}(\.\d+)?", s):
            return datetime.fromtimestamp(float(s))
        m = _HM_RE.match(s)
        if m:
            d = datetime(now.year, now.month, now.day, int(m.group(1)), int(m.group(2)))
            return d if d > now else d + timedelta(days=1)
        return datetime.strptime(s.replace("T", " ")[:16], "%Y-%m-%d %H:%M")
    except (ValueError, OverflowError, OSError):
        return None


def slp_api(d):
    if str(d.get("action") or "") != "until":
        return False, "unknown action"
    w = slp_parse_until(d.get("until"))
    if w is None:
        return False, "invalid time"
    return slp_sleep(w, "Sleep until …", "web")


_slp_sx_routes_before = sx_routes


def sx_routes(app, watch, reply, body):                    # + /api/schlaf (called once by 550; administrator only)
    _slp_sx_routes_before(app, watch, reply, body)
    slp_thread()

    @app.route("/api/schlaf", methods=["POST"])
    def api_schlaf():
        ok, err = slp_api(body())
        return reply({"ok": ok, "error": tr(err) if err else ""}, 200 if ok else 400)


TOGGLES.append(("Power saving", "sleep_armed_ok", "Sleep also while the protection is armed"))
SLIDERS.extend([
    ("Power saving", "sleep_sun_min", "By the sun: sleep from sunrise + / wake up at sunset − (min)", 0, 180, 5),
    ("Power saving", "sleep_low_pct", "Low battery: sleep below (%)", 5, 60, 1),
    ("Power saving", "sleep_low_h", "Low battery: wake up after (hours)", 1, 24, 1),
])
TEXTS.extend([("Power saving", "sleep_mode", "Sleep and wake up (clock of the Pi 5)", "enum", "sleep_modes"),
              ("Power saving", "sleep_off", "Sleep from (HH:MM)", "str", None),
              ("Power saving", "sleep_on", "Wake up at (HH:MM)", "str", None)])
for _k_ in ("sleep_mode", "sleep_off", "sleep_on"):
    TEXT_SPECS[_k_] = next((kind, extra) for s, k, l, kind, extra in TEXTS if k == _k_)
SET_HELP["sleep_mode"] = ("MoveEye switches the Pi off and the clock of the Pi 5 wakes it up again: fixed times, by the sun (sleeps by day, "
                          "guards at night) or only when the battery is low. Never during an alarm. With the Geekworm X1206 test it "
                          "once with «Sleep until …» and 10 min (guide: EEPROM).", "Off.")
_text_choice_pairs_slp_base = text_choice_pairs


def text_choice_pairs(key):                               # + 639zzzzz: the sleep modes
    if (TEXT_SPECS.get(key) or (None, None))[1] == "sleep_modes":
        return [("off", tr("off")), ("times", tr("at fixed times")), ("sun", tr("by the sun (sleeps by day)")),
                ("low", tr("only when the battery is low"))]
    return _text_choice_pairs_slp_base(key)


_set_text_slp_base = set_text


def set_text(key, value):                                 # + 639zzzzz: HH:MM
    if key in ("sleep_off", "sleep_on") and not _HM_RE.match(str(value or "").strip()):
        return False, "a time like 07:30"
    return _set_text_slp_base(key, value)


def slp_text(L=None):
    """«😴 Sleep: by the sun · next Sat 08:10 → 16:20» (window; the page builds the same with t())"""
    st = STATE.get("sleep") or {}
    m = CFG.get("sleep_mode")
    lab = dict(text_choice_pairs("sleep_mode")).get(m, m) if L is None else tr({"off": "off", "times": "at fixed times", "sun": "by the sun (sleeps by day)", "low": "only when the battery is low"}.get(m, "off"), L)
    s = "😴 " + tr("Sleep", L) + ": " + lab
    if st.get("next"):
        s += " · " + tr("next", L) + " " + datetime.fromtimestamp(st["next"]).strftime("%a %H:%M") + (
            " → " + datetime.fromtimestamp(st["next_wake"]).strftime("%H:%M") if st.get("next_wake") else "")
    if st.get("status") == "waiting":
        s += "\n⏸ " + tr("not now", L) + ": " + tr(st.get("why") or "", L)
    if st and not st.get("rtc"):
        s += "\n⚠ " + tr("no RTC wake alarm on this device", L)
    e = st.get("eeprom")
    if e:
        s += f"\nEEPROM: POWER_OFF_ON_HALT={e.get('POWER_OFF_ON_HALT')} · WAKE_ON_GPIO={e.get('WAKE_ON_GPIO')}"
    return s


SLP_HTML = r"""
<style id="slp-css">
#slp-box{margin-top:8px;padding-top:6px;border-top:1px solid var(--line);font-size:14px;white-space:pre-line}
#slp-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px;align-items:center}
#slp-row input{flex:1;min-width:0}
</style>
<script>
// 639zzzzz: sleep and wake up (clock of the Pi 5) in the battery card - only for the administrator
(function () {
  const tt = (k, o) => { let s = t(k); for (const n in (o || {})) s = s.split("{" + n + "}").join(o[n]); return s; };
  const dt = ts => new Date(ts * 1000).toLocaleString(LOCALE(LANG), {weekday: "short", hour: "2-digit", minute: "2-digit"});
  const MODES = {off: "off", times: "at fixed times", sun: "by the sun (sleeps by day)", low: "only when the battery is low"};
  window.slpPaint = function (s) {
    const bl = $("#batt-line"), st = s && s.sleep; if (!bl || !st || (s.me && s.me.role !== "admin")) return;
    let box = $("#slp-box");
    if (!box) {
      box = el("div", ""); box.id = "slp-box";
      const tx = el("div", "mut"); tx.id = "slp-tx";
      const row = el("div", ""); row.id = "slp-row";
      const inp = document.createElement("input"); inp.type = "datetime-local"; inp.id = "slp-until";
      const d = new Date(Date.now() + 3600e3); d.setMinutes(0, 0, 0); d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
      inp.value = d.toISOString().slice(0, 16);
      const b = el("button", "sec", "😴 " + t("Sleep until …")); b.type = "button";
      b.onclick = async () => {
        const v = inp.value; if (!v) return;
        const w = new Date(v).getTime() / 1000;
        if (!confirm(tt("MoveEye shuts down now and wakes up at {time} by the clock of the Pi 5. Nothing is watched until then. Test it once with a short time: the X1206 may cut the power at shutdown, then only the button or the power wakes it.", {time: dt(w)}))) return;
        const r = await post("/api/schlaf", {action: "until", until: String(Math.round(w)), lang: LANG});
        toast(r && r.ok ? "😴 " + t("Sleep") + " · " + dt(w) : "⚠ " + ((r && r.error) || t("Only the administrator can do this.")));
      };
      row.append(inp, b); box.append(tx, row);
      const ak = $("#akl-box"); (ak || bl).after(box);
      if (ak && ak.nextSibling !== box) ak.after(box);
    }
    let txt = "😴 " + t("Sleep") + ": " + t(MODES[st.mode] || "off");
    if (st.next) txt += " · " + t("next") + " " + dt(st.next) + (st.next_wake ? " → " + new Date(st.next_wake * 1000).toLocaleTimeString(LOCALE(LANG), {hour: "2-digit", minute: "2-digit"}) : "");
    if (st.status === "waiting") txt += "\n⏸ " + t("not now") + ": " + t(st.why || "");
    if (!st.rtc) txt += "\n⚠ " + t("no RTC wake alarm on this device");
    if (st.eeprom) txt += "\nEEPROM: POWER_OFF_ON_HALT=" + st.eeprom.POWER_OFF_ON_HALT + " · WAKE_ON_GPIO=" + st.eeprom.WAKE_ON_GPIO;
    $("#slp-tx").textContent = txt;
  };
  const base = paintExtras;
  paintExtras = function (s) { base(s); try { slpPaint(s); } catch (e) {} };
})();
</script>
"""


# ---- Pi window: «Power saving» gets the state and «Sleep until …» -----------------------------------------------------------------
_slp_tk_build_section_base = App._build_section


def _slp_tk_build_section(self, sec, sbody, settings_parent=None):
    _slp_tk_build_section_base(self, sec, sbody, settings_parent)
    if sec != "Power saving" or CFG["lock_on"]:
        return
    try:
        lab = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=380, justify="left"); lab.pack(anchor="w", pady=(10, 0))
        row = ttk.Frame(sbody); row.pack(fill="x", pady=(4, 0))
        var = tk.StringVar(value=(datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:00"))
        ttk.Entry(row, textvariable=var, width=18).pack(side="left", padx=(0, 4))

        def go():
            w = slp_parse_until(var.get())
            if w is None:
                messagebox.showwarning("MoveEye", tr("invalid time"), parent=self.root); return
            if not messagebox.askyesno("MoveEye", trf("MoveEye shuts down now and wakes up at {time} by the clock of the Pi 5. Nothing is watched until then. Test it once with a short time: the X1206 may cut the power at shutdown, then only the button or the power wakes it.",
                                                      time=w.strftime("%a %H:%M")), parent=self.root):
                return
            ok, err = slp_sleep(w, "Sleep until …", "window")
            if not ok:
                messagebox.showwarning("MoveEye", tr(err), parent=self.root)
        ttk.Button(row, text="😴 " + tr("Sleep until …"), command=go).pack(side="left", expand=True, fill="x")

        def paint():
            if not lab.winfo_exists():
                return
            lab.config(text=slp_text())
            lab.after(5000, paint)
        paint()
    except Exception as e:
        log_event("sys", f"Window: sleep: {e}"[:160])


# wraps: App._build_section (570)
App._build_section = _slp_tk_build_section


_HX_SLP = {
    "Sleep": ("Schlafen", "Veille", "Sospensione", "Durmir"),
    "Sleep until …": ("Schlafen bis …", "Veille jusqu'à …", "Sospendi fino a …", "Durmir fin …"),
    "Sleep and wake up (clock of the Pi 5)": ("Schlafen und Wecken (Uhr des Pi 5)", "Veille et réveil (horloge du Pi 5)", "Sospensione e risveglio (orologio del Pi 5)",
                                              "Durmir e dasdar (ura dal Pi 5)"),
    "Sleep from (HH:MM)": ("Schlafen ab (HH:MM)", "Veille dès (HH:MM)", "Sospendi dalle (HH:MM)", "Durmir a partir da (HH:MM)"),
    "Wake up at (HH:MM)": ("Aufwachen um (HH:MM)", "Réveil à (HH:MM)", "Risveglio alle (HH:MM)", "Dasdar a las (HH:MM)"),
    "By the sun: sleep from sunrise + / wake up at sunset − (min)": ("Nach der Sonne: schlafen ab Sonnenaufgang + / aufwachen bei Sonnenuntergang − (min)",
                                                                    "Selon le soleil : veille dès le lever + / réveil au coucher − (min)",
                                                                    "Secondo il sole: sospendi dall'alba + / risveglio al tramonto − (min)",
                                                                    "Tenor il sulegl: durmir a partir da la levada + / dasdar a la rendida − (min)"),
    "Low battery: sleep below (%)": ("Akku leer: schlafen unter (%)", "Batterie faible : veille sous (%)", "Batteria scarica: sospendi sotto (%)", "Accu vid: durmir sut (%)"),
    "Low battery: wake up after (hours)": ("Akku leer: aufwachen nach (Stunden)", "Batterie faible : réveil après (heures)", "Batteria scarica: risveglio dopo (ore)",
                                           "Accu vid: dasdar suenter (uras)"),
    "Sleep also while the protection is armed": ("Auch schlafen, wenn der Schutz scharf ist", "Mettre en veille même quand la protection est armée",
                                                 "Sospendere anche quando la protezione è attiva", "Er durmir, cura che la protecziun è activa"),
    "at fixed times": ("zu festen Zeiten", "à heures fixes", "a orari fissi", "a uras fixas"),
    "by the sun (sleeps by day)": ("nach der Sonne (schläft am Tag)", "selon le soleil (dort le jour)", "secondo il sole (dorme di giorno)", "tenor il sulegl (dorma il di)"),
    "only when the battery is low": ("nur bei leerem Akku", "seulement quand la batterie est faible", "solo con batteria scarica", "mo cun accu vid"),
    "fixed times": ("feste Zeiten", "heures fixes", "orari fissi", "uras fixas"),
    "by the sun": ("nach der Sonne", "selon le soleil", "secondo il sole", "tenor il sulegl"),
    "battery low": ("Akku fast leer", "batterie faible", "batteria scarica", "accu prest vid"),
    "next": ("nächstes Mal", "prochaine fois", "prossima volta", "proxima giada"),
    "not now": ("jetzt nicht", "pas maintenant", "non ora", "betg ussa"),
    "an alarm is going on": ("ein Alarm läuft", "une alarme est en cours", "è in corso un allarme", "in alarm è en curs"),
    "the protection is armed": ("der Schutz ist scharf", "la protection est armée", "la protezione è attiva", "la protecziun è activa"),
    "an update or restart is running": ("ein Update oder Neustart läuft", "une mise à jour ou un redémarrage est en cours", "è in corso un aggiornamento o un riavvio",
                                        "ina actualisaziun u in reavviament è en curs"),
    "the simulator is connected": ("der Simulator ist verbunden", "le simulateur est connecté", "il simulatore è collegato", "il simulatur è collià"),
    "no RTC wake alarm on this device": ("kein RTC-Weckalarm auf diesem Gerät", "pas de réveil RTC sur cet appareil", "nessuna sveglia RTC su questo dispositivo",
                                         "nagin svegliarin RTC sin quest apparat"),
    "the wake-up time must be 5 min to 7 days ahead": ("die Weckzeit muss 5 min bis 7 Tage voraus sein", "l'heure du réveil doit être dans 5 min à 7 jours",
                                                       "l'ora del risveglio deve essere tra 5 min e 7 giorni", "l'ura da dasdar sto esser 5 min fin 7 dis ordavant"),
    "invalid time": ("ungültige Zeit", "heure non valable", "ora non valida", "ura nunvalaivla"),
    "a time like 07:30": ("eine Zeit wie 07:30", "une heure comme 07:30", "un'ora come 07:30", "in'ura sco 07:30"),
    "MoveEye sleeps until {time} ({why}) – nothing is watched until then.": (
        "MoveEye schläft bis {time} ({why}) – bis dahin wird nichts überwacht.", "MoveEye est en veille jusqu'à {time} ({why}) – rien n'est surveillé d'ici là.",
        "MoveEye dorme fino alle {time} ({why}) – fino ad allora nulla è sorvegliato.", "MoveEye dorma fin {time} ({why}) – fin lura na vegn nagut surveglià."),
    "The wake-up did not come as planned ({plan}, started {start}). The X1206 may cut the power at shutdown – see the guide (EEPROM).": (
        "Das Aufwachen kam nicht wie geplant ({plan}, gestartet {start}). Das X1206 schaltet beim Ausschalten vielleicht den Strom ab – siehe Anleitung (EEPROM).",
        "Le réveil n'est pas venu comme prévu ({plan}, démarré {start}). Le X1206 coupe peut-être le courant à l'arrêt – voir le guide (EEPROM).",
        "Il risveglio non è arrivato come previsto ({plan}, avviato {start}). L'X1206 forse toglie la corrente allo spegnimento – vedi la guida (EEPROM).",
        "Il dasdar n'è betg vegnì sco planisà ({plan}, avià {start}). Il X1206 stizza forsa il current cun stizzar – guarda l'instrucziun (EEPROM)."),
    "MoveEye shuts down now and wakes up at {time} by the clock of the Pi 5. Nothing is watched until then. Test it once with a short time: the X1206 may cut the power at shutdown, then only the button or the power wakes it.": (
        "MoveEye schaltet jetzt aus und wacht um {time} durch die Uhr des Pi 5 auf. Bis dahin wird nichts überwacht. Einmal mit kurzer Zeit testen: das X1206 schaltet beim Ausschalten vielleicht den Strom ab, dann weckt ihn nur die Taste oder der Strom.",
        "MoveEye s'éteint maintenant et se réveille à {time} grâce à l'horloge du Pi 5. Rien n'est surveillé d'ici là. À tester une fois avec un temps court : le X1206 coupe peut-être le courant à l'arrêt, alors seul le bouton ou le courant le réveille.",
        "MoveEye si spegne ora e si risveglia alle {time} con l'orologio del Pi 5. Fino ad allora nulla è sorvegliato. Provare una volta con un tempo breve: l'X1206 forse toglie la corrente allo spegnimento, allora lo sveglia solo il tasto o la corrente.",
        "MoveEye stizza ussa e sa dasda a las {time} tras l'ura dal Pi 5. Fin lura na vegn nagut surveglià. Empruvar ina giada cun in curt temp: il X1206 stizza forsa il current cun stizzar, lura al dasda mo il buttun u il current."),
    SET_HELP["sleep_mode"][0]: (
        "MoveEye schaltet den Pi aus und die Uhr des Pi 5 weckt ihn wieder: zu festen Zeiten, nach der Sonne (schläft am Tag, wacht in der Nacht) "
        "oder nur bei leerem Akku. Nie während eines Alarms. Mit dem Geekworm X1206 einmal mit «Schlafen bis …» und 10 min testen (Anleitung: EEPROM).",
        "MoveEye éteint le Pi et l'horloge du Pi 5 le réveille : à heures fixes, selon le soleil (dort le jour, veille la nuit) ou seulement quand la "
        "batterie est faible. Jamais pendant une alarme. Avec le Geekworm X1206, tester une fois avec « Veille jusqu'à … » et 10 min (guide : EEPROM).",
        "MoveEye spegne il Pi e l'orologio del Pi 5 lo risveglia: a orari fissi, secondo il sole (dorme di giorno, sorveglia di notte) o solo con "
        "batteria scarica. Mai durante un allarme. Con il Geekworm X1206 provare una volta con «Sospendi fino a …» e 10 min (guida: EEPROM).",
        "MoveEye stizza il Pi e l'ura dal Pi 5 al dasda puspè: a uras fixas, tenor il sulegl (dorma il di, surveglia la notg) u mo cun accu vid. "
        "Mai durant in alarm. Cun il Geekworm X1206 empruvar ina giada cun «Durmir fin …» e 10 min (instrucziun: EEPROM)."),
    "Off.": ("Aus.", "Désactivé.", "Spento.", "Ora."),
}
for _k, _v in _HX_SLP.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
if 'id="slp-css"' not in WEB_PAGE:                          # after the battery box of 639zzzzz_akku_luecken (530 paintExtras)
    WEB_PAGE = WEB_PAGE.replace("</body>", "<script>try { Object.assign(I18N.de, " + json.dumps({k: v[0] for k, v in _HX_SLP.items()}, ensure_ascii=False)
                                + "); } catch (e) {}</script>" + SLP_HTML + "</body>", 1)


# ---- the manual: one paragraph in «Alarm & Camping» after the battery (5 languages) -----------------------------------------------
HELP_AKL = {
    "de": '<p id="akl-help"><b>🔋 Geekworm X1206: Laden, Lernen, Schlafen:</b> Das X1206 hat <b>keinen Temperaturschutz</b> beim Laden. '
          'Mit einem BME280 im Gehäuse schaltet MoveEye das Laden unter 0 °C über GPIO 16 aus und erst ab 3 °C wieder ein (Einstellungen → Akku). '
          'Im Notfall: Knopf «Trotzdem laden» in der Akku-Karte (gilt 1 h, Push), und unter 10 % lädt es von selbst trotzdem. Ohne BME280 gibt es nur eine Warnung. '
          '«Akku schonen» lädt am Netz nur bis 80 % (wieder unter 75 %). Welcher Pegel an GPIO 16 das Laden ausschaltet, ist einstellbar (Geekworm: hoch). '
          'MoveEye lernt aus dem Abfall des Ladestands den echten Verbrauch (für die Restzeit und die Nachtprognose), zeigt beim Laden «voll in …», zählt die '
          'Vollzyklen und lernt die Kapazität aus langen Entladungen (Hinweis, wenn die Zellen altern). '
          '<b>Schlafen und Wecken</b> (Einstellungen → Strom sparen, nur Admin): feste Zeiten, nach der Sonne, nur bei leerem Akku oder einmal «Schlafen bis …». '
          'Die Uhr des Pi 5 weckt ihn (/sys/class/rtc/rtc0/wakealarm). Nie während eines Alarms und nicht, solange der Schutz scharf ist (ausser so gewählt); vorher kommt ein Push. '
          '<b>Wichtig:</b> Das X1206 schaltet den Strom ab, wenn der Pi aus ist – dann kann ihn auch die Uhr nicht wecken. MoveEye ändert das EEPROM nie; '
          'es zeigt nur die Werte. Laut Raspberry Pi weckt der Alarm mit <code>POWER_OFF_ON_HALT=1</code> und <code>WAKE_ON_GPIO=0</code> '
          '(<code>sudo -E rpi-eeprom-config --edit</code>); mit dem X1206 ist das nicht geprüft. Darum zuerst einmal «Schlafen bis …» mit 10 min testen: '
          'kam MoveEye zu spät, meldet es das beim nächsten Start. <b>Eigene Ein-/Aus-Taste:</b> Das X1206 hat einen Anschluss XH2.54-2P für eine '
          'externe Taste (macht dasselbe wie die Taste des Pi 5: kurz = ein bzw. sauber aus); sie weckt auch einen schlafenden MoveEye. '
          'Weisses Licht und Infrarot (PCA9685 Kanal 2 / 3) lassen sich unter Licht in Prozent dimmen (100 % = wie bisher).</p>',
    "en": '<p id="akl-help"><b>🔋 Geekworm X1206: charging, learning, sleeping:</b> The X1206 has <b>no temperature protection</b> when charging. '
          'With a BME280 in the case MoveEye switches the charging off below 0 °C via GPIO 16 and on again only from 3 °C (Settings → Battery). '
          'In an emergency: the button «Charge anyway» in the battery card (valid 1 h, push), and below 10 % it charges anyway by itself. Without a BME280 there is only a warning. '
          '«Protect the battery» charges on mains only up to 80 % (again below 75 %). Which level of GPIO 16 switches the charging off is a setting (Geekworm: high). '
          'MoveEye learns the real consumption from the drop of the charge level (for the time left and the night forecast), shows «full in …» while charging, counts '
          'the full cycles and learns the capacity from long discharges (a hint when the cells are aging). '
          '<b>Sleep and wake up</b> (Settings → Power saving, administrator only): fixed times, by the sun, only when the battery is low, or once «Sleep until …». '
          'The clock of the Pi 5 wakes it (/sys/class/rtc/rtc0/wakealarm). Never during an alarm and not while the protection is armed (unless chosen); a push comes first. '
          '<b>Important:</b> the X1206 cuts the power when the Pi is off – then the clock cannot wake it either. MoveEye never changes the EEPROM; '
          'it only shows the values. According to Raspberry Pi the alarm wakes with <code>POWER_OFF_ON_HALT=1</code> and <code>WAKE_ON_GPIO=0</code> '
          '(<code>sudo -E rpi-eeprom-config --edit</code>); with the X1206 this is not tested. So first test «Sleep until …» once with 10 min: '
          'if MoveEye came too late, it reports it at the next start. <b>Own power button:</b> the X1206 has an XH2.54-2P connector for an '
          'external button (does the same as the button of the Pi 5: short = on or clean off); it also wakes a sleeping MoveEye. '
          'White and infrared light (PCA9685 channels 2 / 3) can be dimmed in percent under Lights (100 % = as before).</p>',
    "fr": '<p id="akl-help"><b>🔋 Geekworm X1206 : charge, apprentissage, veille :</b> le X1206 n’a <b>aucune protection thermique</b> pendant la charge. '
          'Avec un BME280 dans le boîtier, MoveEye coupe la charge sous 0 °C par le GPIO 16 et ne la remet qu’à partir de 3 °C (Réglages → Batterie). '
          'En cas d’urgence : le bouton « Charger quand même » dans la carte batterie (valable 1 h, push), et sous 10 % elle charge quand même toute seule. Sans BME280, seulement un avertissement. '
          '« Ménager la batterie » charge sur secteur seulement jusqu’à 80 % (de nouveau sous 75 %). Le niveau du GPIO 16 qui coupe la charge est réglable (Geekworm : haut). '
          'MoveEye apprend la vraie consommation à partir de la baisse du niveau de charge (pour l’autonomie et la prévision de nuit), affiche « plein dans … » pendant la charge, compte '
          'les cycles complets et apprend la capacité à partir de longues décharges (indication quand les cellules vieillissent). '
          '<b>Veille et réveil</b> (Réglages → Économie d’énergie, administrateur seulement) : heures fixes, selon le soleil, seulement batterie faible ou une fois « Veille jusqu’à … ». '
          'L’horloge du Pi 5 le réveille (/sys/class/rtc/rtc0/wakealarm). Jamais pendant une alarme ni tant que la protection est armée (sauf si choisi) ; un push arrive avant. '
          '<b>Important :</b> le X1206 coupe le courant quand le Pi est éteint – alors l’horloge ne peut pas non plus le réveiller. MoveEye ne modifie jamais l’EEPROM ; '
          'il affiche seulement les valeurs. Selon Raspberry Pi, l’alarme réveille avec <code>POWER_OFF_ON_HALT=1</code> et <code>WAKE_ON_GPIO=0</code> '
          '(<code>sudo -E rpi-eeprom-config --edit</code>) ; avec le X1206 ce n’est pas vérifié. Donc tester d’abord une fois « Veille jusqu’à … » avec 10 min : '
          'si MoveEye est venu trop tard, il le signale au prochain démarrage. <b>Bouton marche/arrêt externe :</b> le X1206 a un connecteur XH2.54-2P pour un '
          'bouton externe (fait la même chose que le bouton du Pi 5 : bref = marche ou arrêt propre) ; il réveille aussi un MoveEye en veille. '
          'La lumière blanche et l’infrarouge (PCA9685 canaux 2 / 3) se règlent en pour cent sous Lumières (100 % = comme avant).</p>',
    "it": '<p id="akl-help"><b>🔋 Geekworm X1206: carica, apprendimento, sospensione:</b> l’X1206 non ha <b>nessuna protezione termica</b> durante la carica. '
          'Con un BME280 nella custodia MoveEye spegne la carica sotto 0 °C con il GPIO 16 e la riaccende solo da 3 °C (Impostazioni → Batteria). '
          'In emergenza: il pulsante «Carica comunque» nella scheda batteria (vale 1 h, push), e sotto il 10 % carica comunque da sola. Senza BME280 c’è solo un avviso. '
          '«Proteggere la batteria» con la rete carica solo fino all’80 % (di nuovo sotto il 75 %). Il livello del GPIO 16 che spegne la carica è regolabile (Geekworm: alto). '
          'MoveEye impara il consumo reale dal calo del livello di carica (per l’autonomia e la previsione notturna), mostra «piena tra …» durante la carica, conta '
          'i cicli completi e impara la capacità da lunghe scariche (avviso quando le celle invecchiano). '
          '<b>Sospensione e risveglio</b> (Impostazioni → Risparmio energetico, solo amministratore): orari fissi, secondo il sole, solo con batteria scarica o una volta «Sospendi fino a …». '
          'L’orologio del Pi 5 lo risveglia (/sys/class/rtc/rtc0/wakealarm). Mai durante un allarme e non finché la protezione è attiva (salvo se scelto); prima arriva un push. '
          '<b>Importante:</b> l’X1206 toglie la corrente quando il Pi è spento – allora nemmeno l’orologio può risvegliarlo. MoveEye non modifica mai l’EEPROM; '
          'mostra solo i valori. Secondo Raspberry Pi l’allarme risveglia con <code>POWER_OFF_ON_HALT=1</code> e <code>WAKE_ON_GPIO=0</code> '
          '(<code>sudo -E rpi-eeprom-config --edit</code>); con l’X1206 non è verificato. Quindi provare prima una volta «Sospendi fino a …» con 10 min: '
          'se MoveEye è arrivato troppo tardi, lo segnala al prossimo avvio. <b>Tasto di accensione esterno:</b> l’X1206 ha un connettore XH2.54-2P per un '
          'tasto esterno (fa lo stesso del tasto del Pi 5: breve = acceso o spegnimento pulito); risveglia anche un MoveEye sospeso. '
          'La luce bianca e l’infrarosso (PCA9685 canali 2 / 3) si regolano in percento sotto Luci (100 % = come prima).</p>',
    "rm": '<p id="akl-help"><b>🔋 Geekworm X1206: chargiar, emprender, durmir:</b> il X1206 n’ha <b>nagina protecziun da temperatura</b> cun chargiar. '
          'Cun in BME280 en la chascha stizza MoveEye il chargiar sut 0 °C cun GPIO 16 ed envida el pir puspè a partir da 3 °C (Parameters → Accu). '
          'En cas d’urgenza: il buttun «Tuttina chargiar» en la carta da l’accu (vala 1 h, push), e sut 10 % chargia el tuttina sez. Senza BME280 dat i mo in avertiment. '
          '«Schanegiar l’accu» chargia a la rait mo fin 80 % (puspè sut 75 %). Tge nivel dal GPIO 16 che stizza il chargiar è reglabel (Geekworm: aut). '
          'MoveEye empren il consum vair or da la sbassada dal stadi da chargia (per il temp restant e la prognosa da notg), mussa «plain en …» cun chargiar, dumbra '
          'ils ciclus cumplets ed empren la capacitad or da lungas stgargiadas (indicaziun, cura che las cellas vegnan veglias). '
          '<b>Durmir e dasdar</b> (Parameters → Spargnar energia, mo administratur): uras fixas, tenor il sulegl, mo cun accu vid u ina giada «Durmir fin …». '
          'L’ura dal Pi 5 al dasda (/sys/class/rtc/rtc0/wakealarm). Mai durant in alarm e betg uschè ditg che la protecziun è activa (danor sche tschernì); avant vegn in push. '
          '<b>Impurtant:</b> il X1206 stizza il current, cura ch’il Pi è stizzà – lura na po er l’ura betg al dasdar. MoveEye na mida mai l’EEPROM; '
          'el mussa mo las valurs. Tenor Raspberry Pi dasda l’alarm cun <code>POWER_OFF_ON_HALT=1</code> e <code>WAKE_ON_GPIO=0</code> '
          '(<code>sudo -E rpi-eeprom-config --edit</code>); cun il X1206 n’è quai betg verifitgà. Perquai empruvar l’emprim ina giada «Durmir fin …» cun 10 min: '
          'sche MoveEye è vegnì memia tard, annunzia el quai a la proxima partenza. <b>Agen buttun d’envidar:</b> il X1206 ha in colliament XH2.54-2P per in '
          'buttun extern (fa il medem sco il buttun dal Pi 5: curt = envidar u stizzar nett); el dasda er in MoveEye che dorma. '
          'La glisch alva e l’infracotschen (PCA9685 chanals 2 / 3) sa laschan reglar en pertschient sut Glischs (100 % = sco fin ussa).</p>',
}


def _help_akl(doc, lang):
    i = doc.find('<section id="alarm"')
    if i < 0 or 'id="akl-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_AKL[lang] + doc[j:] if j >= 0 else doc


_hp_en_akl = HELP_PAGE.find('<div lang="en">')
if _hp_en_akl > 0:
    HELP_PAGE = _help_akl(HELP_PAGE[:_hp_en_akl], "de") + _help_akl(HELP_PAGE[_hp_en_akl:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_akl(HELP_X[_L], _L)


def slp_selftest():
    """sleep windows (fixed times over midnight, sun, low battery), only at the change into the window, blocks, wake-up check"""
    keep = {k: CFG.get(k) for k in list(SLP_DEF) + ["latitude", "longitude", "sim_on"]}; keep_s = dict(SLP); keep_b = STATE.get("battery")
    g_ = globals(); old = {k: g_[k] for k in ("slp_write_alarm", "power_action", "is_armed", "hp_quiet", "slp_save_plan")}
    calls = []
    try:
        g_["slp_write_alarm"] = lambda ts: calls.append(("rtc", ts)) or ""
        g_["power_action"] = lambda a, delay=3.0, source="": calls.append((a, source)) or (True, "")
        g_["is_armed"] = lambda: False; g_["hp_quiet"] = lambda: True; g_["slp_save_plan"] = lambda d: calls.append(("plan", d["wake"]))
        SLP.update(rtc=True, was_in=None, pending=False, eeprom={"POWER_OFF_ON_HALT": "0", "WAKE_ON_GPIO": "1"}, eeprom_t=time.monotonic())
        CFG.update(sleep_mode="times", sleep_off="23:00", sleep_on="06:00", sim_on=False)
        inw, wake, _w = slp_window(datetime(2026, 11, 21, 23, 30))
        assert inw and wake == datetime(2026, 11, 22, 6, 0), wake
        assert slp_window(datetime(2026, 11, 22, 5, 59))[0] and not slp_window(datetime(2026, 11, 22, 6, 0))[0]
        clk = [datetime(2026, 11, 21, 23, 10)]; SLP["now"] = lambda: clk[0]
        slp_tick()
        assert not calls, "started inside the sleep time by hand: no sleep"
        clk[0] = datetime(2026, 11, 22, 7, 0); slp_tick(); clk[0] = datetime(2026, 11, 22, 23, 0, 30)
        g_["is_armed"] = lambda: True
        assert slp_tick()["why"] == "the protection is armed" and not calls
        g_["is_armed"] = lambda: False
        slp_tick()
        ts_ = int(datetime(2026, 11, 23, 6, 0).timestamp())
        assert calls == [("rtc", ts_), ("plan", ts_), ("poweroff", "sleep")], calls
        CFG.update(sleep_mode="sun", latitude=46.8, longitude=9.5, sleep_sun_min=30)
        inw, wake, _w = slp_window(datetime(2026, 6, 21, 12, 0))
        st_ = sun_times(datetime(2026, 6, 21).date(), 46.8, 9.5)
        assert inw and wake == datetime(2026, 6, 21) + timedelta(minutes=st_[1] - 30), wake
        assert not slp_window(datetime(2026, 6, 21, 3, 0))[0]
        CFG.update(sleep_mode="low", sleep_low_pct=30)
        assert slp_window(datetime(2026, 6, 21, 3, 0), {"pct": 25, "on_battery": True})[0]
        assert not slp_window(datetime(2026, 6, 21, 3, 0), {"pct": 25, "on_battery": True, "charging": True})[0]
        assert slp_sleep(clk[0] + timedelta(minutes=2), "x")[1] == "the wake-up time must be 5 min to 7 days ahead"
        assert slp_parse_until("07:30") == datetime(2026, 11, 23, 7, 30) and slp_parse_until("2026-11-24T08:15") == datetime(2026, 11, 24, 8, 15)
        assert set_text("sleep_off", "25:00")[0] is False
        for L_ in ("fr", "it", "rm"):
            for k in _HX_SLP:
                assert tr(k, L_) != k, (L_, k)
        assert HELP_PAGE.count('id="akl-help"') == 2 and all('id="akl-help"' in HELP_X.get(L_, 'id="akl-help"') for L_ in ("fr", "it", "rm"))
        assert "XH2.54-2P" in HELP_PAGE and 'id="slp-css"' in WEB_PAGE
        return "fixed times over midnight, only at the change into the window, armed blocks, RTC + clean poweroff, sun, low battery, 5 languages, guide"
    finally:
        g_.update(old); CFG.update(keep); SLP.clear(); SLP.update(keep_s); SLP["now"] = None; STATE["battery"] = keep_b


SELFTEST_EXTRA.append(("Sleep and wake up with the RTC of the Pi 5 (639zzzzz)", slp_selftest))
'''
zd_exec(SCHLAF_PY, '639zzzzz_schlaf_wecken.py')
