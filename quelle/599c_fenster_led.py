#@ MoveEye – Teil 599c: Status-LED und Tasten (163a) – Einstellungen (Web und Fenster lesen dieselben Listen, Gruppe «Licht & Ton»), Statuszeile «LED: Wachsam (orange)», «LED testen», «Alarm quittieren», Blinki in der Kopfzeile zwinkert mit der LED, Simulator (state «led», world_reply «buttons»), Anleitung, Selbsttest. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Here (after 570 / 591 / 598) because TOGGLES / SLIDERS / App / the last sim_state and simvals_take wrappers live before.
# The window group «Licht & Ton» gets the section in 639f (after the menu structure 639c builds TK_GROUPS).
# ----------------------------------------------------------------------------
_LEDS = "Status LED"
TOGGLES.extend([
    (_LEDS, "led_on", "Status LED on the head (RGB LED on PCA9685 channels 5 / 6 / 7)"),
    (_LEDS, "led_alarm_blink", "Alarm: blink red until acknowledged"),
    (_LEDS, "led_fault_pulse", "Fault: short violet pulse (battery low, under-voltage, camera lost, servo fault)"),
    (_LEDS, "led_det_flash", "Short flash at every detection (for testing)"),
    (_LEDS, "led_heartbeat", "Blinki blink: a short double blink every few minutes = all is well (not at night)"),
    (_LEDS, "btn_on", "Buttons on the device (GPIO): «Protection» and «Acknowledge alarm»"),
    (_LEDS, "btn_allow_arm", "Button may switch the protection on"),           # 2.98.50: the buttons may do everything,
    (_LEDS, "btn_allow_disarm", "Button may switch the protection off"),       # each action can be switched off (Daniel)
    (_LEDS, "btn_allow_siren", "Button may stop the siren"),
    (_LEDS, "btn_allow_ack", "Button may acknowledge the alarm"),
    (_LEDS, "btn_notify_off", "Message when switched off at the device"),
])
SLIDERS.extend([
    (_LEDS, "led_bright", "Brightness (%)", 5, 100, 5),
    (_LEDS, "led_night_bright", "Brightness at night (%)", 1, 50, 1),
    (_LEDS, "led_hb_min", "Blinki blink every (minutes)", 1, 30, 1),
    (_LEDS, "led_ch_r", "PCA9685 channel red", 0, 15, 1),
    (_LEDS, "led_ch_g", "PCA9685 channel green", 0, 15, 1),
    (_LEDS, "led_ch_b", "PCA9685 channel blue", 0, 15, 1),
    (_LEDS, "btn_long_s", "Long press (s)", 0.8, 4.0, 0.1),
    (_LEDS, "btn_debounce_ms", "Button debounce (ms)", 10, 200, 10),
])
TEXTS.extend([
    (_LEDS, "led_col_off", "Colour at «Off»", "enum", "led_colours"),
    (_LEDS, "led_col_watch", "Colour at «Watchful»", "enum", "led_colours"),
    (_LEDS, "led_col_full", "Colour at «Full»", "enum", "led_colours"),
    (_LEDS, "led_night", "At night", "enum", "led_night"),
    (_LEDS, "led_common", "LED type", "enum", "led_common"),
    (_LEDS, "btn_gpio_protect", "Button «Protection»: GPIO", "enum", "btn_gpio"),
    (_LEDS, "btn_gpio_ack", "Button «Acknowledge alarm»: GPIO", "enum", "btn_gpio"),
])
TEXT_SPECS.update({k: (kind, extra) for s, k, l, kind, extra in TEXTS if s == _LEDS})
SECTIONS.append(_LEDS)
TK_SUB_ICONS[_LEDS] = "◉"
SIMPLE_SECTIONS.add(_LEDS)
SIMPLE_KEYS.update({"led_on", "led_col_off", "led_col_watch", "led_col_full", "led_night", "led_heartbeat", "btn_on"})
SET_HELP.update({
    "led_on": ("A colour LED on top of the head shows the protection from afar: Off, Watchful, Full - and alarms, faults and the "
               "«all is well» blink. Wired to the PCA9685 of the servos, channels 5 / 6 / 7 (red / green / blue).", "On."),
    "led_alarm_blink": ("After an alarm the LED blinks red until somebody acknowledges it: button «Acknowledge alarm» on the device, "
                        "«Acknowledge alarm» on this page or in the window - or switching the protection off.", "On."),
    "led_heartbeat": ("Every few minutes the LED blinks twice shortly, like Blinki: MoveEye runs and all is well. Blinki in the header of "
                      "the page blinks at the same moment. Not at night and not after a fault.", "On."),
    "btn_on": ("Two buttons on the device, each from a GPIO to ground (internal pull-up): «Protection» short = Watchful ↔ Off, long "
               "(1.5 s) = Full; «Acknowledge alarm» stops the siren and the red blinking. Every press is in the log.",
               "On once the buttons are wired. With the simulator its buttons work without this switch."),
    **{k: ("By default the buttons may do everything - also with a PIN for disarming. Switch off here what a button must not do (e.g. "
            "switching off, so a thief at the device cannot disarm). Every switching off and every siren stop at the device is in the log "
            "and sent as a push message.", "On (all four).") for k in ("btn_allow_arm", "btn_allow_disarm", "btn_allow_siren", "btn_allow_ack")},
    "btn_notify_off": ("A push message «Protection switched off at the device» / «Siren stopped at the device» whenever a button "
                       "switches off or stops the siren. In the log it is always.", "On."),
    "led_night": ("At night (dark - in the simulator its night) the LED is dimmed or off, so it does not disturb and does not show "
                  "the device. An alarm is always bright.", "Dimmed."),
})

# the window group «Licht & Ton» lists the section (639f, after 639c builds TK_GROUPS); the web group here:
_LED_GROUP_OLD = '{sec: "Lights", ic: "💡"}, '
_LED_GROUP_NEW = _LED_GROUP_OLD + '{sec: "Status LED", title: "Status LED & buttons", ic: "🔴"}, '
WEB_PAGE = WEB_PAGE.replace(_LED_GROUP_OLD, _LED_GROUP_NEW, 1)
_LED_SEC_OLD = 'if (sec.id === "Extra display" && window.stvPanel) stvPanel(d);'
WEB_PAGE = WEB_PAGE.replace(_LED_SEC_OLD, _LED_SEC_OLD + '\n    if (sec.id === "Status LED" && window.ledPanel) ledPanel(d);   // 599c: status LED and buttons', 1)


# ---- choices -------------------------------------------------------------------------------------------------------------
def led_btn_gpio_pairs(key):
    other = str(CFG.get("btn_gpio_ack" if key == "btn_gpio_protect" else "btn_gpio_protect") or "")
    try:
        free = list(_sens_used_gpios_led_free())
    except Exception:
        free = list(FREE_GPIOS)
    cur = str(CFG.get(key) or "")
    gs = [g for g in free if str(g) != other] + ([int(cur)] if cur.isdigit() else [])
    return [("", "– " + tr("none") + " –")] + [(str(g), f"GPIO {g}") for g in sorted(set(gs))]


def _sens_used_gpios_led_free():
    """free GPIOs for the buttons: not taken by servos, I2C, relays, lights, thermal camera, sensors (the buttons themselves left out)"""
    used = _sens_used_gpios_led_base(None)
    order = [g for g in FREE_GPIOS if g != 4] + [g for g in range(5, 28) if g not in FREE_GPIOS]
    return [g for g in order if g not in used]


_text_choice_pairs_led_base = text_choice_pairs


def text_choice_pairs(key):                               # + 599c: the choices of the status LED and the buttons
    extra = (TEXT_SPECS.get(key) or (None, None))[1]
    if extra == "led_colours":
        return [(c, tr(c)) for c in LED_COLOURS]
    if extra == "led_night":
        return [("dim", tr("dimmed")), ("off", tr("LED off at night")), ("normal", tr("as by day"))]
    if extra == "led_common":
        return [("cathode", tr("common cathode (–): the outputs give the colour")), ("anode", tr("common anode (+): the outputs pull to ground"))]
    if extra == "btn_gpio":
        return led_btn_gpio_pairs(key)
    return _text_choice_pairs_led_base(key)


_settings_migrations_before_led = _settings_migrations


def _settings_migrations(cfg_in):                         # + 599c (2.98.50): «btn_pin_rule» -> the four switches of the buttons
    _settings_migrations_before_led(cfg_in)
    try:
        if led_pin_rule_migrate(cfg_in):
            log_event("sys", "Settings of an older version taken over: buttons with a PIN only switch on")
    except Exception as e:
        log_event("sys", f"Settings migration (599c): {e}"[:150])


def led_pin_rule_migrate(cfg_in):
    """the test build of the buttons had «btn_pin_rule» (with a PIN: buttons only switch on). Saved as «pin_arm_only» together
    with a PIN and without the new switches: disarm and siren stop by button off - everybody else gets all four on."""
    CFG.pop("btn_pin_rule", None)
    if not isinstance(cfg_in, dict) or cfg_in.get("btn_pin_rule") != "pin_arm_only" or not cfg_in.get("protect_pin"):
        return False
    if any(k in cfg_in for k in ("btn_allow_arm", "btn_allow_disarm", "btn_allow_siren", "btn_allow_ack")):
        return False
    CFG.update(btn_allow_disarm=False, btn_allow_siren=False)
    return True


_sens_used_gpios_led_base = sens_used_gpios


def sens_used_gpios(skip=None):                           # + 599c: the two buttons take their GPIOs (when switched on)
    u = _sens_used_gpios_led_base(skip)
    if CFG.get("btn_on"):
        u = set(u) | set(led_gpio_pins().values())
    return u


_siren_alarm_led_base = siren_alarm


def siren_alarm(kind):                                    # + 599c: sabotage / sensor alarms blink red too (163a)
    try:
        if kind in ("tamper", "sensor") and is_armed():
            led_alarm(kind)
    except Exception:
        pass
    return _siren_alarm_led_base(kind)


# ---- simulator: the LED on the simulated head, its buttons instead of the GPIO --------------------------------------------
_sim_state_591_led = sim_state


def sim_state():                                          # + 599c: «led» - the colour of the status LED on the simulated head
    d = _sim_state_591_led()
    s = STATE.get("led") or {}
    d["led"] = {"on": bool(s.get("on", True)), "rgb": str(s.get("rgb") or "#000000"), "br": float(s.get("br") or 0.0),
                "layer": str(s.get("layer") or "state"), "hb": int(s.get("hb") or 0), "alarm": bool(s.get("alarm")),
                "state": str(s.get("state") or "off"), "text": led_label("de", False)}
    return d


_simvals_take_557_led = simvals_take


def simvals_take(rep):                                    # + 599c: the buttons of the simulator («Gerät»: Schutz, Alarm quittieren)
    _simvals_take_557_led(rep)
    try:
        led_sim_buttons(rep.get("buttons"))
    except Exception as e:
        log_event("sys", f"Simulator buttons: {type(e).__name__}: {e}"[:160])


# ---- web: API, header Blinki, settings panel -------------------------------------------------------------------------------
def led_api(lang=None):
    L = norm_lang(lang) if lang else cur_lang()
    s = STATE.get("led") or {}
    pins = led_gpio_pins()
    if s.get("sim"):
        bt = "🧪 " + tr("Buttons of the simulator (window «Gerät»)", L)
    elif CFG.get("btn_on"):
        bt = tr("Buttons", L) + ": " + " · ".join(f"{tr(LED_BTN_NAMES[n], L)} GPIO {pins[n]}" for n in LED_BTN_NAMES if n in pins) + f" ({LEDBTN.get('msg')})"
    else:
        bt = tr("Buttons on the device: off", L)
    hw = {"pca": tr("PCA9685 channels", L) + " " + "/".join(str(c) for c in led_channels()), "sim": "🧪 " + tr("on the simulated head", L),
          "none": tr("no PCA9685 found", L), "off": tr("off", L),
          "conflict": tr("channel {n} is used by a servo or a light", L).replace("{n}", str(led_channel_conflict()))}.get(s.get("hw") or "none", "")
    pr = [dict(p, what=tr(p.get("what") or "", L), btn=tr(LED_BTN_NAMES.get(p.get("btn"), ""), L), ev=tr(p.get("ev") or "", L)) for p in reversed(s.get("presses") or [])]
    return {"ok": True, "label": led_label(L), "led": s, "hw": hw, "buttons": bt, "presses": pr, "state_hex": LED_HEX.get(s.get("state_col") or "off")}


def led_routes(app, reply, body):
    from flask import request

    @app.route("/api/led", methods=["GET", "POST"])
    def api_led():
        if request.method == "GET":
            return reply(led_api(request.args.get("lang")))
        d = body(); a = d.get("action")
        if a == "test":
            led_test()
        elif a == "ack":
            led_ack("web")
        else:
            return reply({"ok": False, "error": "unknown action"}, 400)
        return reply(led_api(d.get("lang")))


_smalltv_routes_led_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 599c: /api/led (550 calls smalltv_routes once)
    _smalltv_routes_led_base(app, reply, body)
    led_routes(app, reply, body)


LED_CSS = r"""
.ledchip{display:inline-flex;align-items:center;gap:4px;padding:1px 7px 1px 5px}
.ledbk{display:inline-block;width:15px;line-height:0;flex:none}
.ledbk.big{width:46px}
.ledbk svg{width:100%;height:auto;display:block;overflow:visible}
.ledbk .bk-s0{stop-color:#ff9f43;stop-opacity:1}.ledbk .bk-s1{stop-color:#ff9f43;stop-opacity:.4}
.ledbk .bk-ft{fill:#e8590c}.ledbk .bk-br{fill:none;stroke:currentColor;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
.ledbk .bk-i,.ledbk .bk-hap{display:none}
.ledbk .bk-scl{fill:#fff}.ledbk .bk-rim{fill:none;stroke:#e8590c;stroke-width:2.6}
.ledbk .bk-iris{fill:var(--led,#39424e);transition:fill .3s}.ledbk .bk-pupil{fill:#0a0e14}.ledbk .bk-hl{fill:#fff}
.ledbk .bk-eye{filter:drop-shadow(0 0 4px var(--ledglow,transparent))}
.ledbk .bk-lid{fill:#e8590c;transform-box:fill-box;transform-origin:50% 0;transform:scaleY(0)}
.ledbk.hb .bk-lid{animation:ledhb .6s linear}
@keyframes ledhb{0%{transform:scaleY(0)}12%,25%{transform:scaleY(1)}37%,50%{transform:scaleY(0)}62%,75%{transform:scaleY(1)}87%,100%{transform:scaleY(0)}}
.ledon.alarm .bk-iris{animation:ledal .5s steps(1) infinite}
@keyframes ledal{0%{fill:#ff2a2a}50%{fill:#39424e}}
html.sxnight .ledbk .bk-scl{fill:#2a0606}html.sxnight .ledbk .bk-hl{fill:#3a0a08}
#ledpanel .ledrow{display:flex;gap:12px;align-items:center}
#ledpanel .ledtxt{flex:1;min-width:0;white-space:pre-wrap}
#ledpanel .btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}#ledpanel .btns button{flex:1 1 140px}
#ledpanel .ledpr{margin-top:8px;font-size:13px;white-space:pre-wrap}
@media (prefers-reduced-motion:reduce){.ledbk .bk-lid,.ledon.alarm .bk-iris{animation:none!important}}
"""

LED_JS = r"""
<script>
(function () {
  try { const D = /*LEDDE*/{}; if (typeof I18N !== "undefined" && I18N.de) for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  const SVG = /*LEDSVG*/"";
  const st = document.createElement("style"); st.textContent = /*LEDCSS*/""; (document.head || document.documentElement).appendChild(st);
  let HB = null, chip = null, n = 0;
  const fig = big => { const s = document.createElement("span"); s.className = "ledbk" + (big ? " big" : ""); s.setAttribute("aria-hidden", "true");
    s.innerHTML = SVG.split("__I__").join("led" + (++n)); return s; };
  function colour(el, v) {                                // the iris = the colour of the state (stable), the alarm blinks by CSS
    if (!el || !v) return;
    const c = v.on ? (v.state_hex || "#39424e") : "#39424e", dim = v.night ? .45 : 1;
    el.style.setProperty("--led", c); el.style.setProperty("--ledglow", v.on && v.br > 0 ? v.rgb : "transparent");
    el.style.opacity = v.on ? dim : .6; el.classList.toggle("alarm", !!v.alarm); el.classList.add("ledon");
  }
  function blink() { document.querySelectorAll(".ledbk").forEach(b => { b.classList.remove("hb"); void b.offsetWidth; b.classList.add("hb"); setTimeout(() => b.classList.remove("hb"), 800); }); }
  function mkChip() {
    const a = document.getElementById("b-arm"); if (!a) return null;
    chip = document.createElement("span"); chip.id = "b-led"; chip.className = "badge ledchip"; chip.hidden = true; chip.style.cursor = "pointer";
    chip.appendChild(fig(false));
    chip.onclick = () => { try { if (typeof tabOpen === "function" && document.querySelector('#settings [data-view="sec:Status LED"]')) tabOpen("sec:Status LED"); else location.href = "/settings?open=" + encodeURIComponent("sec:Status LED"); } catch (e) {} };
    a.parentNode.insertBefore(chip, a.nextSibling); return chip;
  }
  function paint(s) {
    const v = s && s.led; if (!chip) mkChip(); if (!chip || !v) return;
    chip.hidden = !v.on; colour(chip, v);
    chip.title = T("Status LED") + (v.alarm ? " · " + T("Alarm") + " – " + T("Acknowledge alarm") : "") + (v.sim ? " · 🧪" : "") + "\n" + T("Blinki blinks with the LED: all is well");
    if (HB !== null && v.hb !== HB) blink();
    HB = v.hb;
  }
  window.ledPaint = paint;
  if (typeof window.tidyHeader === "function") {           // main page: after every refresh (like 598)
    const th = window.tidyHeader;
    window.tidyHeader = function (s, c) { const r = th.apply(this, arguments); setTimeout(() => { try { paint(s); } catch (e) {} }, 0); return r; };
  }
  // ---- Settings → Light & sound → Status LED & buttons ----
  let BOX = null, TM = null;
  const P = d => (typeof post === "function" ? post("/api/led", Object.assign({lang: L()}, d)) : fetch("/api/led", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))}).then(r => r.json()));
  function show(j) {
    if (!BOX || !j || !j.ok) return;
    const v = Object.assign({}, j.led || {}, {state_hex: j.state_hex});
    colour(BOX.querySelector(".ledbk"), v);
    BOX.querySelector(".ledtxt").textContent = j.label + "\n" + j.hw + "\n" + j.buttons;
    BOX.querySelector(".ledack").disabled = !v.alarm;
    const pr = j.presses || [];
    BOX.querySelector(".ledpr").textContent = pr.length ? T("Last presses") + ":\n" + pr.map(p => p.t + "  " + p.btn + " (" + p.ev + ", " + p.src + ") – " + p.what).join("\n") : "";
    if (HB !== null && v.hb !== HB) blink();
    HB = v.hb;
  }
  const load = () => fetch("/api/led?lang=" + L(), {cache: "no-store"}).then(r => r.json()).then(show).catch(() => {});
  window.ledPanel = function (d) {
    if (d.querySelector("#ledpanel")) return;
    BOX = document.createElement("div"); BOX.className = "auxbox"; BOX.id = "ledpanel";
    const row = document.createElement("div"); row.className = "ledrow"; const tx = document.createElement("div"); tx.className = "ledtxt";
    row.append(fig(true), tx); BOX.appendChild(row);
    const bb = document.createElement("div"); bb.className = "btns";
    const b1 = document.createElement("button"); b1.type = "button"; b1.className = "ledtest"; b1.textContent = "💡 " + T("Test LED");
    b1.onclick = async () => { b1.disabled = true; show(await P({action: "test"})); setTimeout(() => { b1.disabled = false; }, 5600); };
    const b2 = document.createElement("button"); b2.type = "button"; b2.className = "ledack"; b2.textContent = "✓ " + T("Acknowledge alarm"); b2.disabled = true;
    b2.onclick = async () => show(await P({action: "ack"}));
    bb.append(b1, b2); BOX.appendChild(bb);
    const pr = document.createElement("div"); pr.className = "ledpr mut"; BOX.appendChild(pr);
    d.appendChild(BOX); load();
    if (!TM) TM = setInterval(() => { if (BOX && BOX.offsetParent !== null && !document.hidden) load(); }, 1500);
  };
})();
</script>
"""
LED_JS_KEYS = ["Status LED", "Alarm", "Acknowledge alarm", "Blinki blinks with the LED: all is well", "Test LED", "Last presses"]
WEB_PAGE = WEB_PAGE.replace("</body>", LED_JS.replace("/*LEDDE*/{}", "/*LEDDE*/" + json.dumps({_k: DE.get(_k, _k) for _k in LED_JS_KEYS}, ensure_ascii=False), 1)
                            .replace('/*LEDSVG*/""', json.dumps(BLINKI_SVG), 1).replace('/*LEDCSS*/""', json.dumps(LED_CSS), 1) + "</body>", 1)


# 2.98.50 (Daniel): «Alarm quittieren» also in the alarm card of the tab «Schutz» («Was passiert bei einem Alarm?», 530) - the
# same function as the button of the card «Status-LED & Tasten» (led_ack: red blinking, siren, escalation)
_LED_CHAIN_KEY_OLD = 'c.escalate_on, c.escalate_siren_s, LANG].join("|");'
_LED_CHAIN_KEY_NEW = 'c.escalate_on, c.escalate_siren_s, LANG, !!(s.led && s.led.alarm)].join("|");'
_LED_CHAIN_OLD = '  box.appendChild(ch);\n  box.appendChild(el("div", "mut", armed ?'
_LED_CHAIN_NEW = ('  box.appendChild(ch);\n'
                  '  { const ak = el("button", "sec", "✓ " + t("Acknowledge alarm")); ak.type = "button"; ak.id = "chain-ack"; ak.style.marginTop = "6px";   // 599c\n'
                  '    ak.disabled = !(s.led && s.led.alarm); ak.title = t("Stops the siren and the red blinking of the status LED");\n'
                  '    ak.onclick = () => { ak.disabled = true; fetch("/api/led", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: "ack", lang: LANG})}).catch(() => {}); };\n'
                  '    box.appendChild(ak); }\n'
                  '  box.appendChild(el("div", "mut", armed ?')
WEB_PAGE = WEB_PAGE.replace(_LED_CHAIN_KEY_OLD, _LED_CHAIN_KEY_NEW, 1).replace(_LED_CHAIN_OLD, _LED_CHAIN_NEW, 1)
LED_JS_KEYS.append("Stops the siren and the red blinking of the status LED")


def led_web_de_refresh():
    """639f adds the German texts after this part: the page dictionary is filled again then"""
    global WEB_PAGE
    m = re.search(r"/\*LEDDE\*/(\{.*?\});", WEB_PAGE)
    if m:
        WEB_PAGE = WEB_PAGE[:m.start(1)] + json.dumps({_k: DE.get(_k, _k) for _k in LED_JS_KEYS}, ensure_ascii=False) + WEB_PAGE[m.end(1):]


# ---- window (Tkinter): the same in Settings → Light & sound → Status LED & buttons -------------------------------------
def _led_tk_build_section(self, sec, sbody, settings_parent=None):
    _led_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec == "Camping / protection":                      # 2.98.50: «Alarm quittieren» also in the group «Schutz» (like the web card)
        try:
            _led_tk_ack_row(self, sbody)
        except Exception as e:
            log_event("sys", f"Window: acknowledge button: {e}"[:160])
        return
    if sec != _LEDS:
        return
    try:
        _led_tk_panel(self, sbody)
    except Exception as e:
        log_event("sys", f"Window: status LED section: {e}"[:160])


def _led_tk_panel(app, sbody):
    row = tk.Frame(sbody, bg=C["panel"]); row.pack(fill="x", pady=(4, 0))
    cv = tk.Canvas(row, width=26, height=26, bg=C["panel"], highlightthickness=0, bd=0); cv.pack(side="left", padx=(0, 8))
    dot = cv.create_oval(4, 4, 22, 22, fill="#000000", outline=C["line"], width=2)
    lbl = ttk.Label(row, text="", style="Mut.TLabel", wraplength=300, justify="left"); lbl.pack(side="left", fill="x", expand=True)
    app.status_labels[_LEDS] = lbl
    bf = ttk.Frame(sbody); bf.pack(fill="x", pady=(6, 0))
    ttk.Button(bf, text="💡 " + tr("Test LED"), command=led_test).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ack = ttk.Button(bf, text="✓ " + tr("Acknowledge alarm"), command=lambda: led_ack("window")); ack.pack(side="left", expand=True, fill="x")
    pr = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=330, justify="left"); pr.pack(anchor="w", pady=(4, 0))

    def tick():
        try:
            if not lbl.winfo_exists():
                return
            j = led_api()
            s = j["led"]
            cv.itemconfig(dot, fill=s.get("rgb") if s.get("br", 0) > 0 else "#000000",
                          outline=LED_HEX.get(s.get("state_col") or "off", C["line"]) if s.get("on") else C["line"])
            lbl.config(text=j["label"] + "\n" + j["hw"] + "\n" + j["buttons"])
            ack.state(["!disabled"] if s.get("alarm") else ["disabled"])
            p = j["presses"][:4]
            pr.config(text=(tr("Last presses") + ":\n" + "\n".join(f"{x['t']}  {x['btn']} ({x['ev']}, {x['src']}) – {x['what']}" for x in p)) if p else "")
            app.root.after(200, tick)
        except Exception:
            pass
    tick()


def _led_tk_ack_row(app, sbody):
    ack = ttk.Button(sbody, text="✓ " + tr("Acknowledge alarm"), command=lambda: led_ack("window"))
    ack.pack(fill="x", pady=(8, 0))
    ttk.Label(sbody, text=tr("Stops the siren and the red blinking of the status LED"), style="Mut.TLabel", wraplength=380).pack(anchor="w", pady=(2, 0))

    def tick():
        try:
            if not ack.winfo_exists():
                return
            ack.state(["!disabled"] if (STATE.get("led") or {}).get("alarm") else ["disabled"])
            app.root.after(1000, tick)
        except Exception:
            pass
    tick()


_led_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _led_tk_build_section

# ---- the manual (HELP_PAGE): Light & sound, German and English -------------------------------------------------------------
_LED_HELP = (
    ('<section id="lightsound" data-icon="💡"><h2>Licht &amp; Ton</h2>',
     "<p><b>🔴 Status-LED und Tasten:</b> Eine Farb-LED oben auf dem Kopf (RGB an PCA9685 Kanal 5 / 6 / 7, gemeinsame Kathode oder Anode, "
     "Helligkeit einstellbar) zeigt den Schutz von weitem: <i>Aus</i> grün, <i>Wachsam</i> orange, <i>Voll</i> rot (Farben einstellbar; "
     "während des Countdowns «atmet» die Farbe). Nach einem Alarm blinkt sie rot, bis jemand quittiert – Taste «Alarm quittieren», Knopf "
     "auf dieser Seite oder im Fenster, oder Schutz aus. Störungen (Akku schwach, Unterspannung, Kamera weg, Servo-Störung) zeigt ein "
     "kurzes violettes Pulsieren. Alle paar Minuten zwinkert sie zweimal kurz – «alles ok»; Blinki in der Kopfzeile zwinkert im selben "
     "Moment. Nachts gedimmt oder aus. Zwei Tasten am Gerät (GPIO gegen Masse, interner Pull-up, entprellt; Standard GPIO 16 = Pin 36 "
     "«Schutz», GPIO 26 = Pin 37 «Alarm quittieren»): «Schutz» kurz = Wachsam ↔ Aus, lang (1,5 s) = Voll; «Alarm quittieren» stoppt "
     "Sirene und Eskalation – dasselbe wie der Knopf «Alarm quittieren» im Alarmfenster. Jeder Druck steht im Protokoll. Die Tasten "
     "dürfen alles, auch mit einer PIN zum Ausschalten; jede Aufgabe (Einschalten, Ausschalten, Sirene stoppen, Quittieren) lässt sich "
     "einzeln ausschalten. Jedes Ausschalten und jedes Sirene-Stoppen am Gerät steht im Protokoll und kommt als Push-Nachricht "
     "(«Schutz am Gerät ausgeschaltet» / «Sirene am Gerät gestoppt», abschaltbar). Mit dem "
     "3D-Simulator leuchtet die LED auf dem simulierten Kopf, und die Tasten sind im Simulator-Fenster «Gerät» (🧪). "
     "Einstellungen → Licht &amp; Ton → Status-LED &amp; Tasten.</p>"),
    ('<section id="lightsound" data-icon="💡"><h2>Light &amp; sound</h2>',
     "<p><b>🔴 Status LED and buttons:</b> a colour LED on top of the head (RGB on PCA9685 channels 5 / 6 / 7, common cathode or anode, "
     "brightness adjustable) shows the protection from afar: <i>Off</i> green, <i>Watchful</i> orange, <i>Full</i> red (colours "
     "adjustable; during the countdown the colour «breathes»). After an alarm it blinks red until somebody acknowledges – button "
     "«Acknowledge alarm», the button on this page or in the window, or protection off. Faults (battery low, under-voltage, camera lost, "
     "servo fault) show as a short violet pulse. Every few minutes it blinks twice shortly – «all is well»; Blinki in the header blinks "
     "at the same moment. Dimmed or off at night. Two buttons on the device (GPIO to ground, internal pull-up, debounced; default GPIO 16 = "
     "pin 36 «Protection», GPIO 26 = pin 37 «Acknowledge alarm»): «Protection» short = Watchful ↔ Off, long (1.5 s) = Full; «Acknowledge "
     "alarm» stops siren and escalation – the same as the button «Acknowledge alarm» in the alarm window. Every press is in the log. The "
     "buttons may do everything, also with a PIN for disarming; each job (switching on, switching off, stopping the siren, acknowledging) "
     "can be switched off on its own. Every switching off and every siren stop at the device is in the log and sent as a push message "
     "(«Protection switched off at the device» / «Siren stopped at the device», can be switched off). With the 3D "
     "simulator the LED shines on the simulated head and the buttons are in the simulator window «Gerät» (🧪). Settings → Light &amp; "
     "sound → Status LED &amp; buttons.</p>"),
)
for _a, _b in _LED_HELP:
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)


# ---- self-test ------------------------------------------------------------------------------------------------------------
class _LedFakePCA:
    """records the register writes of the LED channels (like PCA9685._set)"""
    def __init__(self):
        self.regs = {}

    def _set(self, ch, on, off):
        self.regs[ch] = (on, off)


def led_selftest():
    keep_cfg = {k: CFG.get(k) for k in list(LED_DEFAULTS) + ["armed", "protect_pin", "protect_level", "sim_on"]}
    keep_led = {k: (v.copy() if isinstance(v, (dict, deque)) else v) for k, v in LED.items()}
    G = globals()
    keep_g = {k: G[k] for k in ("led_button_event", "protect_set", "led_ack", "log_event", "protect_cancel_escalation")}
    try:
        CFG.update(LED_DEFAULTS); CFG["led_heartbeat"] = False
        LED.update(alarm=False, fault_until=0.0, fault_t0=-1e9, flash_until=0.0, test_t0=-1e9, hb_next=None, hb_t=-1e9, hb_n=0)
        f = led_frame(100.0, "watch")
        assert f["col"] == "orange" and f["layer"] == "state" and abs(f["br"] - 0.6) < 1e-6, f
        assert led_frame(100.0, "off")["col"] == "green" and led_frame(100.0, "full")["col"] == "red"
        # priority: alarm > fault > flash > state
        LED.update(flash_t0=100.0, flash_until=100.3, flash_col="white", flash_hz=0.0)
        assert led_frame(100.1, "watch")["layer"] == "flash"
        LED.update(fault_t0=100.0, fault_until=102.1)
        assert led_frame(100.2, "watch")["layer"] == "fault" and led_frame(100.2, "watch")["col"] == "violet"
        LED.update(alarm=True, alarm_t=100.0)
        a1, a2 = led_frame(100.1, "watch"), led_frame(100.35, "watch")
        assert a1["layer"] == a2["layer"] == "alarm" and a1["col"] == "red" and a2["col"] == "off", (a1, a2)
        assert led_frame(100.1, "watch", dark=True)["br"] >= 0.6, "alarm stays bright at night"
        LED["test_t0"] = 100.0
        assert led_frame(100.1, "watch")["layer"] == "test" and led_frame(100.9, "watch")["col"] == "green"
        LED.update(test_t0=-1e9, alarm=False)
        assert led_frame(101.0, "watch")["layer"] == "fault"
        assert led_frame(103.0, "watch")["layer"] == "state"
        # night: dimmed / off / as by day
        CFG.update(led_night="dim", led_night_bright=8)
        n = led_frame(200.0, "watch", dark=True)
        assert n["col"] == "orange" and abs(n["br"] - 0.08) < 1e-6, n
        CFG["led_night"] = "off"
        assert led_frame(200.0, "watch", dark=True)["layer"] == "dark"
        CFG["led_night"] = "normal"
        assert abs(led_frame(200.0, "watch", dark=True)["br"] - 0.6) < 1e-6
        CFG["led_night"] = "dim"
        # heartbeat with a fake clock: every led_hb_min minutes a double blink, not at night, not after a fault
        CFG.update(led_heartbeat=True, led_hb_min=5)
        LED.update(hb_next=None, hb_n=0, hb_t=-1e9, fault_t0=-1e9, fault_until=0.0)
        assert led_frame(1000.0, "watch")["layer"] == "state" and LED["hb_next"] == 1300.0
        assert led_frame(1299.9, "watch")["layer"] == "state" and LED["hb_n"] == 0
        h0 = led_frame(1300.0, "watch")
        assert h0["layer"] == "heartbeat" and h0["col"] == "off" and LED["hb_n"] == 1, h0
        assert led_frame(1300.2, "watch")["col"] == "orange" and led_frame(1300.35, "watch")["col"] == "off"
        assert led_frame(1300.7, "watch")["layer"] == "state" and LED["hb_next"] == 1600.0
        led_frame(1600.0, "watch", dark=True)
        assert LED["hb_n"] == 1 and LED["hb_next"] == 1900.0, "no heartbeat at night"
        LED["fault_t0"] = 1850.0
        led_frame(1900.0, "watch")
        assert LED["hb_n"] == 1, "no heartbeat after a fault"
        led_frame(2200.0, "watch")
        assert LED["hb_n"] == 2
        CFG["led_col_off"] = "off"
        LED["hb_next"] = 2300.0
        assert led_frame(2300.05, "off")["col"] == "green", "LED dark at «Off»: the blink shows green"
        CFG["led_col_off"] = "green"
        # buttons: debounce, short, long (fake clock)
        b = LedButton("t", 0.05, 1.5)
        evs = [b.feed(lv, t) for lv, t in ((True, 0.0), (False, 0.01), (True, 0.02), (True, 0.08), (True, 0.3), (False, 0.31), (True, 0.315), (False, 0.33), (False, 0.4))]
        assert [e for e in evs if e] == ["short"], evs
        b = LedButton("t", 0.05, 1.5)
        evs = [b.feed(lv, t) for lv, t in ((True, 0.0), (True, 0.06), (True, 1.0), (True, 1.56), (True, 2.5), (False, 2.6), (False, 2.7))]
        assert [e for e in evs if e] == ["long"], evs
        b = LedButton("t", 0.05, 1.5)
        assert [e for e in (b.feed(True, 0.0), b.feed(False, 0.02), b.feed(False, 0.2)) if e] == [], "a 20 ms glitch is no press"
        # PCA9685 fake: channels 5 / 6 / 7, gamma, common anode, fully on / off bits
        p = _LedFakePCA()
        CFG.update(led_common="cathode"); LED["last"] = None
        assert led_pca_write(p, {"rgb": (1.0, 0.32, 0.0), "br": 1.0})
        assert set(p.regs) == {5, 6, 7} and p.regs[5] == (0x1000, 0) and p.regs[7] == (0, 0x1000) and 0 < p.regs[6][1] < 4095, p.regs
        assert not led_pca_write(p, {"rgb": (1.0, 0.32, 0.0), "br": 1.0}), "same colour: no I2C traffic"
        CFG["led_common"] = "anode"
        led_pca_write(p, {"rgb": (1.0, 0.0, 0.0), "br": 1.0})
        assert p.regs[5] == (0, 0x1000) and p.regs[6] == (0x1000, 0), p.regs
        CFG.update(led_common="cathode", led_ch_r=0)
        assert led_channel_conflict() == 0
        CFG["led_ch_r"] = 5
        assert led_channel_conflict() is None
        assert not [x for x in light_out_pairs("white") if x[0] in ("pca:5", "pca:6", "pca:7")]
        # the simulator buttons -> the same events as a GPIO (presses of before the connection do not count)
        got = []
        G["led_button_event"] = lambda name, ev, src="GPIO": got.append((name, ev, src))
        LEDBTN["sim"] = {}
        led_sim_buttons({"protect": {"down": False, "seq": 4, "last_ms": 200}, "ack": {"down": False, "seq": 1, "last_ms": 100}}, 10.0)
        assert got == [], got
        led_sim_buttons({"protect": {"down": False, "seq": 5, "last_ms": 300}}, 11.0)
        assert got == [("protect", "short", "simulator")], got
        led_sim_buttons({"protect": {"down": True, "held_ms": 400, "seq": 5}}, 12.0)
        led_sim_buttons({"protect": {"down": True, "held_ms": 1600, "seq": 5}}, 13.2)
        assert got[-1] == ("protect", "long", "simulator"), got
        led_sim_buttons({"protect": {"down": False, "seq": 6, "last_ms": 1900}}, 13.5)
        assert len(got) == 2, "a long press gives no short one at the release"
        led_sim_buttons({"ack": {"down": False, "seq": 2, "last_ms": 2000}}, 14.0)
        assert got[-1] == ("ack", "long", "simulator"), got
        G["led_button_event"] = keep_g["led_button_event"]
        # the actions (no real arming in the self-test). 2.98.50: the buttons may do everything, also with a PIN; each action
        # can be switched off; disarm / siren stop at the device -> log + push message
        calls = []
        G["protect_set"] = lambda lv, who="web", answers=None: (calls.append(("set", lv)), CFG.update(armed=lv != "off"))
        G["led_ack"] = lambda src="web": calls.append(("ack", src))
        G["protect_cancel_escalation"] = lambda: None
        G["log_event"] = lambda kind, text: calls.append(("log", text))

        class _N:
            def info(self, text, link="", title="", jpg=None, fname=""):
                calls.append(("push", text)); return True

        class _W:
            notifier = _N()
        keep_w = WATCH_REF.get("w"); WATCH_REF["w"] = _W()
        keep_snd = SOUND.get("playing")
        try:
            assert CFG["btn_gpio_protect"] == "16" and CFG["btn_gpio_ack"] == "26", "default GPIO 16 / 26 (GPIO 5 = PIR)"
            assert all(CFG[k] for k in ("btn_allow_arm", "btn_allow_disarm", "btn_allow_siren", "btn_allow_ack", "btn_notify_off"))
            CFG.update(armed=False, protect_pin="x$y")
            led_button_event("protect", "short", "GPIO 16")
            assert ("set", "watch") in calls and any("Button «Protection» short" in str(c[1]) for c in calls if c[0] == "log"), calls
            calls.clear()
            led_button_event("protect", "short", "GPIO 16")
            assert ("set", "off") in calls, "PIN set: the button still switches off (Daniel 30.10.2026)"
            assert ("push", tr("Protection switched off at the device")) in calls, calls
            assert any("Protection switched off at the device" in str(c[1]) for c in calls if c[0] == "log"), "disarm at the device in the log"
            calls.clear(); CFG["armed"] = True; SOUND["playing"] = True
            led_button_event("ack", "short", "GPIO 26")
            assert ("ack", "button") in calls and ("push", tr("Siren stopped at the device")) in calls, calls
            calls.clear(); SOUND["playing"] = False
            led_button_event("ack", "short", "simulator")
            assert ("ack", "button 🧪") in calls and not [c for c in calls if c[0] == "push"], "no siren - no push"
            # each action can be switched off
            calls.clear(); CFG.update(btn_allow_disarm=False, armed=True)
            led_button_event("protect", "short", "GPIO 16")
            assert not [c for c in calls if c[0] in ("set", "push")] and LED["flash_hz"] > 0, "disarm by button switched off"
            led_button_event("protect", "long", "GPIO 16")
            assert ("set", "full") in calls
            calls.clear(); CFG.update(btn_allow_arm=False, armed=False)
            led_button_event("protect", "short", "GPIO 16"); led_button_event("protect", "long", "GPIO 16")
            assert not [c for c in calls if c[0] == "set"], "arming by button switched off"
            calls.clear(); CFG.update(btn_allow_siren=False, armed=True); LED["alarm"] = True; SOUND["playing"] = True
            led_button_event("ack", "short", "GPIO 26")
            assert not [c for c in calls if c[0] in ("ack", "push")] and not LED["alarm"], "siren stop switched off: only the LED"
            calls.clear(); CFG["btn_allow_ack"] = False; LED["alarm"] = True
            led_button_event("ack", "short", "GPIO 26")
            assert LED["alarm"] and not [c for c in calls if c[0] == "ack"], "acknowledging switched off"
            # no push message when switched off, the log line stays
            CFG.update(btn_allow_ack=True, btn_allow_siren=True, btn_allow_disarm=True, btn_allow_arm=True, btn_notify_off=False, armed=True)
            calls.clear(); led_button_event("protect", "short", "GPIO 16")
            assert ("set", "off") in calls and not [c for c in calls if c[0] == "push"] and any("at the device" in str(c[1]) for c in calls if c[0] == "log")
            # the old setting of the test build: «pin_arm_only» with a PIN -> disarm / siren off; without a PIN or new keys: all on
            CFG.update(btn_allow_disarm=True, btn_allow_siren=True)
            assert not led_pin_rule_migrate({"btn_pin_rule": "pin_arm_only"}) and CFG["btn_allow_disarm"]
            assert not led_pin_rule_migrate({"btn_pin_rule": "pin_arm_only", "protect_pin": "a$b", "btn_allow_disarm": True})
            assert led_pin_rule_migrate({"btn_pin_rule": "pin_arm_only", "protect_pin": "a$b"}) and not CFG["btn_allow_disarm"] and not CFG["btn_allow_siren"]
            assert CFG["btn_allow_arm"] and CFG["btn_allow_ack"] and "btn_pin_rule" not in CFG
        finally:
            WATCH_REF["w"] = keep_w; SOUND["playing"] = keep_snd
        # the same switches in the web page and the window (schema), the acknowledge button in the alarm card / group «Schutz»
        keys = {x[1] for x in TOGGLES if x[0] == _LEDS}
        assert {"btn_allow_arm", "btn_allow_disarm", "btn_allow_siren", "btn_allow_ack", "btn_notify_off"} <= keys, keys
        assert 'id = "chain-ack"' in WEB_PAGE and "!!(s.led && s.led.alarm)].join" in WEB_PAGE, "Alarm quittieren in the alarm card"
        assert tr("Protection switched off at the device", "de") == "Schutz am Gerät ausgeschaltet" and tr("Siren stopped at the device", "de") == "Sirene am Gerät gestoppt"
        for L_ in ("fr", "it", "rm"):
            assert tr("Siren stopped at the device", L_) != "Siren stopped at the device", L_
        for k, v in keep_g.items():
            G[k] = v
        # alarm hook, labels, pages, field list
        CFG.update(armed=False); LED["alarm"] = False
        led_alarm("person"); assert LED["alarm"]
        LED["alarm"] = False
        STATE["led"] = {"on": True, "state": "watch", "state_col": "orange", "layer": "state"}
        assert tr("LED", "de") + ": Wachsam (orange)" == led_label("de"), led_label("de")
        assert "Status LED" in SECTIONS and _LED_GROUP_NEW in WEB_PAGE and "ledPanel(d)" in WEB_PAGE and "window.ledPanel" in WEB_PAGE
        assert any(_LEDS in g[2] for g in TK_GROUPS if g[0] == "lightsound"), "window group Licht & Ton"
        assert '"Test LED": "LED testen"' in WEB_PAGE, "German texts of the web panel"
        assert "Status-LED und Tasten" in HELP_PAGE and "Status LED and buttons" in HELP_PAGE
        assert text_choice_pairs("led_col_watch")[1][0] == "orange" and dict(text_choice_pairs("btn_gpio_protect")).get("16") == "GPIO 16"
        L = iface_list()
        if L is not None:
            assert "led" in L["state"] and "buttons" in L["world_reply"]
        sd = sim_state()
        assert sd["led"]["rgb"].startswith("#") and "hb" in sd["led"]
        return "priority, night, heartbeat, buttons (GPIO 16 / 26, may do everything, each switchable, push at disarm / siren stop), PCA9685 channels 5-7, simulator buttons, acknowledge in the alarm card"
    finally:
        for k, v in keep_g.items():
            G[k] = v
        CFG.update(keep_cfg)
        LED.clear(); LED.update(keep_led)
        LEDBTN["sim"] = {}


SELFTEST_EXTRA.append(("Status LED and buttons: priority, night, heartbeat, debounce, PCA9685 5-7, simulator (163a / 599c)", led_selftest))
