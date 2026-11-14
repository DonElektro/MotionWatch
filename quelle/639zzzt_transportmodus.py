#@ MoveEye – Teil 639zzzt: «🧳 Transportmodus» – für die gedruckte Transportkappe: Kopf langsam in die Grundstellung, dann Servos ohne Strom; nichts bewegt den Kopf mehr, Alarme ruhen, filmen geht weiter. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (14.11.2026, freigegeben): eine neue gedruckte Kappe hält den Kopf beim Transport in der Grundstellung
# (Kamera, Wärmebild und Lampen bleiben frei).
#  Ein         nur der Administrator (Einstellungen → Kameras & Kopf → Kopf (Servos) → «Servo-Bewegung & Sicherheit», Pi-Fenster im selben Abschnitt, Knopf
#              «Beenden» im Band), vorher die Frage «Kopf fährt in Grundstellung. Danach Kappe aufsetzen.». Der Kopf fährt mit
#              15 °/s in die Grundstellung (Planer 072, derselbe Weg wie «Not-Aus → parken»), danach bekommen die Servos keinen
#              Puls mehr (Hardware 080 _servos_off: PCA9685-Kanal ganz aus, gpiozero detach, pigpio 0) - kein Haltemoment,
#              kein Zittern. Grundstellung = der gespeicherte Punkt «Grundstellung» (076, kopf_home_point), sonst die Mitte;
#              sie wird beim Einschalten festgehalten (kopf_transport_pos), damit ein späteres Umlernen nichts ändert.
#  Gesperrt    servo_blocked() = «transport» (072): der Planer nimmt kein Ziel an - Joystick, Pfeile, Gamepad, Simulator-
#              Steuerung (/api/move, /api/stick), Positionen (teach_goto), Patrouille (160), Folgen (410), der Kopf-Koordinator
#              mit Runde / Alarm-Drehen / Übersicht lenkt den Kopf (162 _kopf_tick ruht), Lupe «Kopf folgt» (639zzzl). Jede
#              Anfrage bekommt die kurze Antwort «Transportmodus aktiv» (423 / 409), die Seite zeigt sie beim Antippen.
#  Alarm       is_armed() sagt «nein» (wie Gehtest / Morse): keine Sirene, kein Push, keine Eskalation, keine Sabotage-Meldung
#              (beim Tragen wäre «bewegt / abgedeckt / verdreht» immer falsch). War der Schutz an, wird trotzdem gefilmt wie
#              scharf (410 handle_recording «quiet»: Aufnahme und Foto ja, Push / Sirene / «Bist du's?» nein).
#              Entscheid hier: SOS-Lampe (639zzt) und Sirene von Hand bleiben - das sind Menschen, die Hilfe rufen; die
#              Einstellungen des Schutzes werden NICHT umgestellt (armed, Stufe, Sirene bleiben stehen).
#  Aus         Frage «Kappe abgenommen?» (mit Kappe könnten die Servos sich verspannen). Die Servos halten wieder an genau der
#              Grundstellung (kein Sprung), drei Sekunden Ruhe, dann läuft alles wie vorher; war der Schutz an, startet er mit
#              dem normalen Countdown neu (arm(): gleiche Stufe, gleiche Sirene - genau wie vorher).
#  Bleibt      CFG kopf_transport (sofort gespeichert, save_settings_flush): nach Neustart / Update gleich wieder gesperrt; der
#              Planer schaltet beim Start sofort stromlos, ohne einen Puls (die Kappe sitzt ja schon).
#  Anzeige     Band oben auf Live / Schutz / Einstellungen, im Kopf statt «Wachsam» «🧳 Transport» (Seite: prText, Fenster:
#              protect_label),
#              Push «Transportmodus ein / aus» nur an den Administrator (Kanal «tz_admin», 639zzc).
# Doppelung (Konzept-Check, dem Besitzer gemeldet): den Modus «Transport / Ruhe» (130 MODES) gibt es schon - er schaltet
# Erkennung, Aufnahmen und Alarme ab, kennt den Kopf aber nicht. Der Transportmodus hier sperrt den Kopf und filmt weiter.
# Texte: _HX_TRANSPORT (5 Sprachen). Test: werkzeuge/transportmodus_test.py.
# ----------------------------------------------------------------------------
TP_DEF = {"kopf_transport": False, "kopf_transport_pos": [], "kopf_transport_by": "", "kopf_transport_t": 0.0}
for _k, _v in TP_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
    FACTORY_CFG.setdefault(_k, json.loads(json.dumps(_v)))
USER_SETTINGS_DENY.update(TP_DEF)      # only the administrator over /api/transport (with the questions), never «settings» / an app key
APPKEY_DENY_KEYS.update(TP_DEF)
APPKEY_DENY_PATHS.add("/api/transport")
LOCK_DENY_PATHS.add("/api/transport")
_IMP["sys"] = re.compile(_IMP["sys"].pattern + r"|Transport mode")
SRV_FAULT_TEXT.setdefault("transport", "transport mode")
# head-moving requests that get the short notice right away (the planner refuses them anyway): path -> which bodies
TP_GUARD = {"/api/follow": lambda d: bool(d.get("on")), "/api/quick": lambda d: d.get("action") == "patrol",
            "/api/action": lambda d: d.get("action") in ("center", "patrol"), "/api/kopf": lambda d: True,
            "/api/refscan": lambda d: True}


def tp_on():
    return bool(CFG.get("kopf_transport"))


def tp_pick_home():
    """where the head goes: the taught point «Grundstellung» (076), else the middle"""
    try:
        hp = teach_point_by_name(CFG.get("kopf_home_point") or "")
    except NameError:
        hp = None
    return srv_clamp(*(hp[:2] if hp else (50.0, 50.0))) or (50.0, 50.0)


def tp_phase():
    """'' off · homing (drives to the home position) · wait (Not-Aus / fault / under-voltage first) · free (released)"""
    if not tp_on():
        return ""
    if servo_detached():
        return "free"
    return "homing" if servo_blocked() == "transport" else "wait"


def tp_state(lang=None):
    h = servo_tp_home()
    return {"on": tp_on(), "phase": tp_phase(), "home": [round(h[0], 2), round(h[1], 2)], "since": float(CFG.get("kopf_transport_t") or 0.0),
            "by": str(CFG.get("kopf_transport_by") or ""), "detached": servo_detached(), "off_n": int(SRV.get("tp_off_n", 0)),
            "armed": bool(CFG.get("armed")), "text": servo_blocked_text(lang) if tp_on() else ""}


def tp_push(on):
    """«Transportmodus ein / aus» to the administrator only (main channel + browsers without a user, 639zzc «tz_admin»)"""
    txt = tr("Transport mode on - the head is locked in the home position, alarms paused, recording goes on." if on
             else "Transport mode off - the head moves again, protection as before.")
    try:
        w = WATCH_REF.get("w")
        n = getattr(w, "notifier", None) if w is not None else None
        if n is None or not (n.configured() and CFG.get("notify_on")):
            return False
        p = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": txt,
             "info_title": "{name}: 🧳 " + tr("Transport mode on" if on else "Transport mode off"), "snapshot": None, "rain": False,
             "wind": "", "source": STATE.get("source_label", ""), "link": "/#settings", "tz_admin": True}
        threading.Thread(target=n._dispatch, args=(p, None, ""), daemon=True, name="tp-push").start()
        return True
    except Exception as e:
        log_event("sys", f"Transport mode push: {e}"[:160])
        return False


def tp_set(on, who="web"):
    """switch the transport mode -> (ok, error). The questions are asked by the page / the window before."""
    on = bool(on); who = str(who or "?")[:60]
    if on == tp_on():
        return True, ""
    if on:
        h = tp_pick_home()
        CFG.update(kopf_transport=True, kopf_transport_pos=[round(h[0], 3), round(h[1], 3)], kopf_transport_by=who, kopf_transport_t=time.time())
        SRV.update(tp="", cap=None)
        if SRV.get("parked") is True and not CFG.get("servo_estop"):
            SRV["parked"] = False                            # drive home even when it was parked by an emergency stop before
        try:
            protect_cancel_escalation()                      # a siren that waits for the escalation does not come any more
        except NameError:
            pass
        KOPF.update(back=None, alarm=None, turn_req=None, round_on=False)
        log_event("sys", f"Transport mode ON ({who}): the head drives slowly to the home position (pan {h[0]:.1f} % / tilt {h[1]:.1f} %), "
                         "then the servos are released - alarms paused, recording goes on")
    else:
        p = servo_pos()
        CFG.update(kopf_transport=False, kopf_transport_by="", kopf_transport_t=0.0)
        CFG["pan"], CFG["tilt"] = p[0], p[1]                 # nothing jumps: the servos hold exactly where the cap held the head
        SRV.update(vel=[0.0, 0.0], tgt=list(p), cap=None, tp="", parked=False)
        MANUAL["until"] = time.time() + 3.0                 # a short pause before the automatic moves start again
        log_event("sys", f"Transport mode OFF ({who}): the servos hold again in the home position - everything as before"
                         + (" (protection with the countdown)" if CFG.get("armed") else ""))
        if CFG.get("armed"):
            arm()                                            # the same level and siren as before, with the normal countdown
    save_settings_flush()
    tp_push(on)
    return True, ""


# ---- wrappers: no alarms, the state everywhere, the head coordinator rests, the magnifier says why, the PIN -------------------
_is_armed_tp = is_armed


# wraps: is_armed
def is_armed():                                              # + 639zzzt: no alarms in the transport mode (like the walk test)
    if CFG.get("kopf_transport"):
        return False
    return _is_armed_tp()


_protect_label_tp = protect_label


# wraps: protect_label
def protect_label(arm_state, left=0, lang=None):             # + 639zzzt: the state says «🧳 Transport», not «Wachsam» / «Aus»
    if CFG.get("kopf_transport"):
        return "🧳 " + tr("Transport", lang)
    return _protect_label_tp(arm_state, left, lang)


_kopf_tick_tp = _kopf_tick


# wraps: _kopf_tick
def _kopf_tick():                                            # + 639zzzt: no round, no alarm turn, no overview, no parking
    if CFG.get("kopf_transport"):
        KOPF.update(back=None, alarm=None, turn_req=None, round_on=False, glance="")
        KOPF["status"] = "transport mode - the head stays in the home position"
        return None
    return _kopf_tick_tp()


_lupe_head_block_tp = lupe_head_block


# wraps: lupe_head_block
def lupe_head_block():                                       # + 639zzzt: «Kopf folgt» of the magnifier names the reason
    if CFG.get("kopf_transport"):
        return "Transport mode active"
    return _lupe_head_block_tp()


_web_disarms_tp = web_disarms


# wraps: web_disarms
def web_disarms(path, d):                                    # + 639zzzt: switching it on pauses the alarms -> the PIN (if set)
    if path == "/api/transport" and isinstance(d, dict) and CFG.get("armed"):
        return bool(d.get("on"))
    return _web_disarms_tp(path, d)


_servo_client_state_tp = servo_client_state


# wraps: servo_client_state
def servo_client_state(request, lang=None):                  # + 639zzzt: the state poll of every page carries the transport mode
    d = _servo_client_state_tp(request, lang)
    d["transport"] = tp_state(lang)
    return d


# ---- web: /api/transport (GET state, POST on / off - only the administrator, 550 role_guard) ------------------------------------
_smalltv_routes_tp = smalltv_routes


def smalltv_routes(app, reply, body):                         # + 639zzzt
    _smalltv_routes_tp(app, reply, body)
    from flask import request, g

    @app.before_request
    def tp_guard():                                          # the short notice for head-moving buttons
        if not CFG.get("kopf_transport") or request.method != "POST" or request.path not in TP_GUARD:
            return None
        d = request.get_json(force=True, silent=True) or {}
        if not isinstance(d, dict) or not TP_GUARD[request.path](d):
            return None
        L = norm_lang(d.get("lang") or request.args.get("lang") or CFG.get("lang"))
        return reply({"ok": False, "error": servo_blocked_text(L), "blocked": "transport"}, 423)

    @app.route("/api/transport", methods=["GET", "POST"])
    def api_transport():
        if request.method == "GET":
            return reply(dict(tp_state(norm_lang(request.args.get("lang") or CFG.get("lang"))), ok=True))
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        if getattr(g, "role", "admin") != "admin" or getattr(g, "appkey", None):
            return reply({"ok": False, "error": tr("Only for the administrator", L)}, 403)
        if not d.get("confirm"):
            return reply({"ok": False, "error": "confirm"}, 400)
        user = str(getattr(g, "user", "") or "")
        who = servo_client(request, d)[1]
        ok, err = tp_set(bool(d.get("on")), (user + " · " if user and user not in who else "") + who)
        return reply(dict(tp_state(L), ok=ok, error=tr(err, L) if err else None), 200 if ok else 409)


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_TRANSPORT = {
    "Transport mode": ("Transportmodus", "Mode transport", "Modalità trasporto", "Modus da transport"),
    "Transport": ("Transport", "Transport", "Trasporto", "Transport"),
    "Transport mode active": ("Transportmodus aktiv", "Mode transport actif", "Modalità trasporto attiva", "Modus da transport activ"),
    "the head stays in the home position": ("der Kopf bleibt in der Grundstellung", "la tête reste en position de base",
                                            "la testa resta nella posizione base", "il chau resta en la posiziun da basa"),
    "Transport mode on": ("Transportmodus ein", "Mode transport activé", "Modalità trasporto attivata", "Modus da transport activà"),
    "Transport mode off": ("Transportmodus aus", "Mode transport désactivé", "Modalità trasporto disattivata", "Modus da transport deactivà"),
    "The head drives to the home position. Then put on the cap.": (
        "Kopf fährt in Grundstellung. Danach Kappe aufsetzen.", "La tête va en position de base. Ensuite, mets le capuchon.",
        "La testa va nella posizione base. Poi metti il cappuccio.", "Il chau va en la posiziun da basa. Lura metta si il chapitsch."),
    "transport mode - the head stays in the home position": ("Transportmodus – der Kopf bleibt in der Grundstellung",
                                                             "mode transport – la tête reste en position de base",
                                                             "modalità trasporto – la testa resta nella posizione base",
                                                             "modus da transport – il chau resta en la posiziun da basa"),
    "Cap removed?": ("Kappe abgenommen?", "Capuchon retiré ?", "Cappuccio tolto?", "Chapitsch prendì giu?"),
    "Moving with the cap on could strain the servos. Take the cap off first.": (
        "Mit aufgesetzter Kappe könnten sich die Servos verspannen. Zuerst die Kappe abnehmen.",
        "Avec le capuchon, les servos pourraient forcer. Retire d’abord le capuchon.",
        "Con il cappuccio i servo potrebbero sforzarsi. Togli prima il cappuccio.",
        "Cun il chapitsch pudessan ils servos sa stirar. L’emprim prender giu il chapitsch."),
    "Start transport mode": ("Transportmodus einschalten", "Activer le mode transport", "Attivare la modalità trasporto", "Activar il modus da transport"),
    "End transport mode": ("Transportmodus beenden", "Terminer le mode transport", "Terminare la modalità trasporto", "Terminar il modus da transport"),
    "Cap is off - end": ("Kappe ist ab – beenden", "Capuchon retiré – terminer", "Cappuccio tolto – terminare", "Chapitsch è giu – terminar"),
    "End": ("Beenden", "Terminer", "Terminare", "Terminar"),
    "The head drives slowly to the home position …": ("Kopf fährt langsam in die Grundstellung …", "La tête va lentement en position de base …",
                                                      "La testa va lentamente nella posizione base …", "Il chau va plaun en la posiziun da basa …"),
    "Head in the home position, servos free - put on the cap": ("Kopf in Grundstellung, Servos frei – Kappe aufsetzen",
                                                                "Tête en position de base, servos libres – mets le capuchon",
                                                                "Testa nella posizione base, servo liberi – metti il cappuccio",
                                                                "Chau en la posiziun da basa, servos libers – metta si il chapitsch"),
    "waiting: the servos are stopped": ("wartet: die Servos sind gestoppt", "en attente : les servos sont arrêtés",
                                        "in attesa: i servo sono fermi", "spetga: ils servos èn fermads"),
    "Alarms paused, recording goes on": ("Alarm aus, filmen geht weiter", "Alarmes en pause, l’enregistrement continue",
                                         "Allarmi in pausa, la registrazione continua", "Alarms en pausa, la registraziun cuntinuescha"),
    "For travelling with the transport cap: the head drives to the home position and is released, nothing moves it any more. Alarms are paused - camera, thermal camera, lamps and recording keep working. SOS and the siren by hand still work.": (
        "Für unterwegs mit der Transportkappe: der Kopf fährt in die Grundstellung und wird freigegeben, nichts bewegt ihn mehr. Alarme ruhen – Kamera, Wärmebild, Lampen und Aufnahme laufen weiter. SOS und Sirene von Hand gehen weiter.",
        "Pour voyager avec le capuchon de transport : la tête va en position de base et est libérée, plus rien ne la bouge. Les alarmes sont en pause – caméra, caméra thermique, lampes et enregistrement continuent. Le SOS et la sirène à la main fonctionnent toujours.",
        "Per viaggiare con il cappuccio di trasporto: la testa va nella posizione base e viene liberata, niente la muove più. Gli allarmi sono in pausa – telecamera, termocamera, lampade e registrazione continuano. SOS e sirena a mano funzionano ancora.",
        "Per viagiar cun il chapitsch da transport: il chau va en la posiziun da basa e vegn deliberà, nagut na al mova pli. Ils alarms èn en pausa – camera, camera termica, lampas e registraziun cuntinueschan. SOS e la sirena a maun funcziunan anc."),
    "Transport mode on - the head is locked in the home position, alarms paused, recording goes on.": (
        "Transportmodus ein – der Kopf ist in der Grundstellung gesperrt, Alarme ruhen, filmen geht weiter.",
        "Mode transport activé – la tête est bloquée en position de base, alarmes en pause, l’enregistrement continue.",
        "Modalità trasporto attivata – la testa è bloccata nella posizione base, allarmi in pausa, la registrazione continua.",
        "Modus da transport activà – il chau è bloccà en la posiziun da basa, alarms en pausa, la registraziun cuntinuescha."),
    "Transport mode off - the head moves again, protection as before.": (
        "Transportmodus aus – der Kopf bewegt sich wieder, Schutz wie vorher.",
        "Mode transport désactivé – la tête bouge de nouveau, protection comme avant.",
        "Modalità trasporto disattivata – la testa si muove di nuovo, protezione come prima.",
        "Modus da transport deactivà – il chau sa mova puspè, protecziun sco avant."),
}
for _k, _v in _HX_TRANSPORT.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


# ---- the page (Live / Schutz / Einstellungen): band, state in the header, panel in «Kopf (Servos)», the two questions -------------------------
TP_CSS = r"""
/* 639zzzt transport mode: the band (all tabs of the main page), the panel, the question */
#tp-band{position:sticky;top:0;z-index:61;display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:9px 14px;background:#1f4fa8;color:#fff;font-weight:600;font-size:14px;line-height:1.35}
#tp-band[hidden]{display:none}
#tp-band .tp-t{flex:1 1 220px;min-width:0}#tp-band small{display:block;font-weight:400;opacity:.92;font-size:12.5px}
#tp-band button{background:#fff;color:#1f4fa8;border:0;font-weight:700;padding:7px 12px;border-radius:10px}
.tp-box{margin:8px 0 6px;padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:var(--field,transparent)}
.tp-box .tp-st{margin:6px 0 8px;font-size:13.5px}
.tp-box button{width:100%;font-weight:700}
.tp-box.on{border-color:#3b72d9}
#tp-dlg{position:fixed;inset:0;z-index:9000;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;padding:16px}
#tp-dlg .tp-c{background:var(--panel,#1b2230);color:var(--txt,#e8edf5);border:1px solid var(--line,#334);border-radius:16px;max-width:420px;width:100%;padding:18px 18px 14px;box-shadow:0 12px 40px rgba(0,0,0,.45)}
#tp-dlg h3{margin:0 0 8px;font-size:18px}#tp-dlg p{margin:0 0 14px;line-height:1.45}
#tp-dlg .tp-b{display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap}#tp-dlg .tp-b button{min-width:120px;font-weight:700}
"""
TP_JS = r"""
(() => {
  const TPC = window.TP_CFG || {};
  let S = null, band = null, boxes = [], noteT = 0;
  const T = s => (typeof t === "function" ? t(s) : s);
  const E = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const isAdmin = () => { const m = window.__lastState && window.__lastState.me; return !m || m.role === "admin"; };
  const say = m => { if (typeof toast === "function") toast(m); };
  function ask(on) {
    return new Promise(res => {
      const old = document.getElementById("tp-dlg"); if (old) old.remove();
      const ov = E("div"); ov.id = "tp-dlg"; ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true");
      const c = E("div", "tp-c");
      c.append(E("h3", "", "🧳 " + T(on ? "Transport mode" : "Cap removed?")),
               E("p", "", T(on ? "The head drives to the home position. Then put on the cap." : "Moving with the cap on could strain the servos. Take the cap off first.")));
      const b = E("div", "tp-b"), no = E("button", "sec", T("Cancel")), yes = E("button", "", on ? "🧳 " + T("Start transport mode") : "✅ " + T("Cap is off - end"));
      no.type = yes.type = "button"; yes.id = "tp-yes"; no.id = "tp-no";
      const done = v => { ov.remove(); res(v); };
      no.onclick = () => done(false); yes.onclick = () => done(true); ov.onclick = e => { if (e.target === ov) done(false); };
      b.append(no, yes); c.appendChild(b); ov.appendChild(c); document.body.appendChild(ov); yes.focus();
    });
  }
  async function toggle(on) {
    if (!(await ask(on))) return;
    let r = null;
    try { r = await (await fetch("/api/transport", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({on: on, confirm: true, lang: (typeof LANG !== "undefined" ? LANG : "")})})).json(); } catch (e) {}
    if (!r || !r.ok) { say("⚠ " + ((r && r.error) || T("No connection to MoveEye."))); return; }
    S = r; paint(); say("🧳 " + T(on ? "Transport mode on" : "Transport mode off"));
    if (typeof refresh === "function") setTimeout(refresh, 300);
  }
  window.tpToggle = toggle;
  function phaseText(s) {
    return s.phase === "free" ? T("Head in the home position, servos free - put on the cap") : s.phase === "wait" ? T("waiting: the servos are stopped")
      : T("The head drives slowly to the home position …");
  }
  function build() {
    if (!band) {
      band = E("div"); band.id = "tp-band"; band.hidden = true;
      document.body.insertBefore(band, document.body.firstChild ? document.body.firstChild.nextSibling : null);
    }
  }
  function paint() {
    build(); const s = S || {};
    if (s.on) {
      band.textContent = ""; band.hidden = false;
      const tx = E("div", "tp-t", "🧳 " + T("Transport mode active"));
      tx.appendChild(E("small", "", phaseText(s) + " · " + T("Alarms paused, recording goes on")));
      band.appendChild(tx);
      if (isAdmin()) { const b = E("button", "", T("End")); b.type = "button"; b.id = "tp-end"; b.onclick = () => toggle(false); band.appendChild(b); }
    } else band.hidden = true;
    boxes = boxes.filter(x => x.isConnected);
    // first thing in «Kopf (Servos)», not inside its «Feineinstellungen» (530 regroup puts «Servo motion & safety» there)
    const hd = document.querySelector('#settings details.sub[data-view="sec:Camera / Servos"]'), sm = hd && hd.querySelector(":scope > summary");
    boxes.forEach(bx => { if (sm && bx.parentNode !== hd) hd.insertBefore(bx, sm.nextSibling); paintBox(bx); });
  }
  function paintBox(bx) {
    const s = S || {}, k = [!!s.on, s.phase, isAdmin(), typeof LANG !== "undefined" ? LANG : ""].join("|");
    if (bx._k === k) return;
    bx._k = k; bx.textContent = ""; bx.classList.toggle("on", !!s.on);
    bx.appendChild(E("b", "", "🧳 " + T("Transport mode")));
    bx.appendChild(E("div", "mut", T("For travelling with the transport cap: the head drives to the home position and is released, nothing moves it any more. Alarms are paused - camera, thermal camera, lamps and recording keep working. SOS and the siren by hand still work.")));
    bx.appendChild(E("div", "tp-st", s.on ? "● " + phaseText(s) : "○ " + T("off")));
    const b = E("button", s.on ? "sec" : "", s.on ? "✅ " + T("End transport mode") : "🧳 " + T("Start transport mode"));
    b.type = "button"; b.className += " tp-btn"; b.disabled = !isAdmin(); if (!isAdmin()) b.title = T("Only for the administrator");
    b.onclick = () => toggle(!s.on); bx.appendChild(b);
  }
  window.tpPanel = d => { const bx = E("div", "tp-box auxbox"); bx.id = "tp-box"; d.appendChild(bx); boxes.push(bx); paintBox(bx); };
  window.tpPaint = j => {
    const s = j && j.state && j.state.servo && j.state.servo.transport; if (!s) return;
    S = s; paint();
  };
  // the state in the header (and on the page «Schutz»): «🧳 Transport» instead of «Wachsam» / «Voll» / «Aus» - the alarms rest
  try { if (typeof prText === "function" && !prText._tp) { const base = prText;
    prText = function (s) { const x = s && s.servo && s.servo.transport; return x && x.on ? ["🧳 " + T("Transport"), "blu"] : base.apply(this, arguments); };
    prText._tp = true; } } catch (e) {}
  // the short notice when a head control is touched (the server refuses the move anyway)
  document.addEventListener("pointerdown", e => {
    if (!S || !S.on || !e.target || !e.target.closest) return;
    if (!e.target.closest("#stick, #mstick, #lv-joy, .dp, #stick-center, #vo-ctl, #vo-mctl, [data-head]")) return;
    const now = Date.now(); if (now - noteT < 2500) return; noteT = now;
    say("🧳 " + T("Transport mode active") + " – " + T("the head stays in the home position"));
  }, true);
})();
"""
TP_JS_KEYS = ("Cancel", "No connection to MoveEye.", "Only for the administrator", "off")


def tp_live_html():
    de = {k: v[0] for k, v in _HX_TRANSPORT.items()}
    de.update({k: DE.get(k, k) for k in TP_JS_KEYS if DE.get(k)})
    return ("<style id=\"tp-css\">" + TP_CSS + "</style><script>\ntry { Object.assign(I18N.de, " + json.dumps(de, ensure_ascii=False)
            + "); } catch (e) {}\n" + TP_JS + "</script>")


def tp_page_hooks(page):
    """the hooks in the main page (530): the state poll, the panel in the section «Servo motion & safety» (card «Kopf (Servos)»)"""
    for a, b in (('try { if (window.servoPaint) window.servoPaint(j); } catch (e) {}',
                  'try { if (window.servoPaint) window.servoPaint(j); } catch (e) {}\n  try { if (window.tpPaint) window.tpPaint(j); } catch (e) {}'),
                 ('if (sec.id === "Developer") devExtras(d);',
                  'if (sec.id === "Developer") devExtras(d);\n    if (sec.id === "Servo motion & safety" && window.tpPanel) tpPanel(d);')):
        if a in page and b not in page:
            page = page.replace(a, b, 1)
    if 'id="tp-css"' not in page:
        page = page.replace("</body>", tp_live_html() + "</body>", 1)
    return page


WEB_PAGE = tp_page_hooks(WEB_PAGE)


# ---- the Pi window: the same button in the section «Kopf (Servos)», the questions as message boxes -----------------------------
def tp_tk_toggle(app):
    on = not tp_on()
    q = tr("The head drives to the home position. Then put on the cap.") if on else tr("Moving with the cap on could strain the servos. Take the cap off first.")
    if not messagebox.askyesno("MoveEye – 🧳 " + tr("Transport mode" if on else "Cap removed?"), q, parent=app.root):
        return
    tp_set(on, tr("Window") + " (" + tr("this computer") + ")")


_tp_tk_build_section_base = App._build_section


def _tp_tk_build_section(self, sec, sbody, settings_parent=None):
    _tp_tk_build_section_base(self, sec, sbody, settings_parent)
    if sec != _SVS:                                          # «Servo motion & safety» in the card «Kopf (Servos)», like the web
        return
    try:
        fr = ttk.Frame(sbody); fr.pack(fill="x", pady=(8, 0))
        lab = ttk.Label(fr, text="", style="Mut.TLabel", wraplength=330, justify="left"); lab.pack(anchor="w")
        btn = ttk.Button(fr, text="", command=lambda: (tp_tk_toggle(self), paint()))
        btn.pack(fill="x", pady=(4, 0))

        def paint():
            try:
                if not btn.winfo_exists():
                    return
                on = tp_on()
                btn.config(text=("✅ " + tr("End transport mode")) if on else ("🧳 " + tr("Start transport mode")))
                ph = tp_phase()
                lab.config(text="🧳 " + tr("Transport mode") + ": " + (tr("Head in the home position, servos free - put on the cap") if ph == "free"
                           else tr("The head drives slowly to the home position …") if ph == "homing" else tr("waiting: the servos are stopped") if ph
                           else tr("off")))
                btn.after(1500, paint)
            except Exception:
                pass
        paint()
    except Exception as e:
        log_event("sys", f"Window: transport mode button: {e}"[:160])


# wraps: App._build_section
App._build_section = _tp_tk_build_section


# ---- the manual: one paragraph at the end of «Kamera & Servos» -----------------------------------------------------------------
HELP_TP = {
    "de": '<p id="tp-help"><b>🧳 Transportmodus (Einstellungen → Kameras &amp; Kopf → Kopf, nur Administrator; auch im Pi-Fenster):</b> für die Transportkappe. Nach der Frage «Kopf fährt in Grundstellung. Danach Kappe aufsetzen.» fährt der Kopf langsam in die Grundstellung (der gespeicherte Punkt «Grundstellung», sonst die Mitte), danach bekommen die Servos keinen Strom mehr – nichts bewegt den Kopf (Joystick, Patrouille, Folgen, Übersicht, Positionen, Gamepad, Simulator, Lupe sagen «Transportmodus aktiv»). Alarme ruhen, Kamera, Wärmebild, Lampen und Aufnahme laufen weiter; SOS-Lampe und Sirene von Hand gehen. Oben ein blaues Band, im Kopf «🧳 Transport», ein Push an den Administrator. Bleibt nach Neustart und Update. Ausschalten fragt «Kappe abgenommen?»; danach halten die Servos wieder an der Grundstellung und alles läuft wie vorher (der Schutz mit dem Countdown).</p>',
    "en": '<p id="tp-help"><b>🧳 Transport mode (Settings → Cameras &amp; head → Head, administrator only; also in the Pi window):</b> for the transport cap. After the question «The head drives to the home position. Then put on the cap.» the head drives slowly to the home position (the taught point «Home position», else the middle), then the servos get no current any more – nothing moves the head (joystick, patrol, follow, overview, positions, gamepad, simulator, magnifier say «Transport mode active»). Alarms are paused, camera, thermal camera, lamps and recording keep working; the SOS lamp and the siren by hand work. A blue band at the top, «🧳 Transport» in the header, a push to the administrator. Stays after a restart and an update. Switching off asks «Cap removed?»; then the servos hold at the home position again and everything runs as before (the protection with the countdown).</p>',
    "fr": '<p id="tp-help"><b>🧳 Mode transport (Réglages → Caméras &amp; tête → Tête, administrateur seulement ; aussi dans la fenêtre du Pi) :</b> pour le capuchon de transport. Après la question « La tête va en position de base. Ensuite, mets le capuchon. », la tête va lentement en position de base (le point enregistré « Position de base », sinon le milieu), puis les servos ne reçoivent plus de courant – plus rien ne bouge la tête (joystick, patrouille, suivre, vue d’ensemble, positions, manette, simulateur, loupe disent « Mode transport actif »). Les alarmes sont en pause ; caméra, caméra thermique, lampes et enregistrement continuent ; la lampe SOS et la sirène à la main fonctionnent. Une bande bleue en haut, « 🧳 Transport » dans l’en-tête, un push à l’administrateur. Reste après un redémarrage et une mise à jour. L’arrêt demande « Capuchon retiré ? » ; ensuite les servos tiennent de nouveau la position de base et tout fonctionne comme avant (la protection avec le compte à rebours).</p>',
    "it": '<p id="tp-help"><b>🧳 Modalità trasporto (Impostazioni → Telecamere &amp; testa → Testa, solo amministratore; anche nella finestra del Pi):</b> per il cappuccio di trasporto. Dopo la domanda «La testa va nella posizione base. Poi metti il cappuccio.» la testa va lentamente nella posizione base (il punto salvato «Posizione base», altrimenti il centro), poi i servo non ricevono più corrente – niente muove la testa (joystick, pattuglia, segui, panoramica, posizioni, gamepad, simulatore, lente dicono «Modalità trasporto attiva»). Gli allarmi sono in pausa; telecamera, termocamera, lampade e registrazione continuano; la lampada SOS e la sirena a mano funzionano. Una banda blu in alto, «🧳 Trasporto» nell’intestazione, un push all’amministratore. Resta dopo un riavvio e un aggiornamento. Lo spegnimento chiede «Cappuccio tolto?»; poi i servo tengono di nuovo la posizione base e tutto funziona come prima (la protezione con il conto alla rovescia).</p>',
    "rm": '<p id="tp-help"><b>🧳 Modus da transport (Parameters → Cameras &amp; chau → Chau, mo administratur; er en la fanestra dal Pi):</b> per il chapitsch da transport. Suenter la dumonda «Il chau va en la posiziun da basa. Lura metta si il chapitsch.» va il chau plaun en la posiziun da basa (il punct memorisà «Posiziun da basa», uschiglio il center), lura na survegnan ils servos nagin current pli – nagut na mova il chau (joystick, patruglia, suandar, survista, posiziuns, gamepad, simulatur, lupa din «Modus da transport activ»). Ils alarms èn en pausa; camera, camera termica, lampas e registraziun cuntinueschan; la lampa SOS e la sirena a maun funcziunan. Ina strivla blaua sisum, «🧳 Transport» en il chau da la pagina, in push a l’administratur. Resta suenter in reavviament ed ina actualisaziun. Il deactivar dumonda «Chapitsch prendì giu?»; lura tegnan ils servos puspè la posiziun da basa e tut funcziuna sco avant (la protecziun cun il countdown).</p>',
}


def _help_tp(doc, lang):
    i = doc.find('<section id="camera"')
    if i < 0 or 'id="tp-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_TP[lang] + doc[j:] if j >= 0 else doc


_hp_en_tp = HELP_PAGE.find('<div lang="en">')
if _hp_en_tp > 0:
    HELP_PAGE = _help_tp(HELP_PAGE[:_hp_en_tp], "de") + _help_tp(HELP_PAGE[_hp_en_tp:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_tp(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def transport_selftest():
    """planner: home slowly, then released; nothing takes a target; no alarms; the page hooks; texts"""
    keep = {k: CFG.get(k) for k in ("kopf_transport", "kopf_transport_pos", "kopf_transport_by", "kopf_transport_t", "pan", "tilt", "armed",
                                    "servo_estop", "kopf_home_point")}
    keep_srv = {k: (list(SRV[k]) if isinstance(SRV.get(k), list) else SRV.get(k)) for k in ("pos", "vel", "tgt", "cap", "tp", "parked", "started",
                                                                                           "fault", "inhibit", "moving", "scale")}
    G = globals()
    keep_fn = {k: G[k] for k in ("save_settings_flush", "tp_push", "log_event", "arm", "servo_diag_move_start", "servo_diag_count", "servo_safety_tick")}
    keep_man = dict(MANUAL)
    armed_n = []
    try:
        G.update(save_settings_flush=lambda *a, **k: None, tp_push=lambda *a, **k: None, log_event=lambda *a, **k: None,
                 arm=lambda *a, **k: armed_n.append(1), servo_diag_move_start=lambda *a, **k: None, servo_diag_count=lambda *a, **k: None,
                 servo_safety_tick=lambda *a, **k: None)
        CFG.update(kopf_transport=False, servo_estop=False, armed=True, kopf_home_point="", pan=90.0, tilt=20.0)
        SRV.update(pos=[90.0, 20.0], vel=[0.0, 0.0], tgt=[90.0, 20.0], cap=None, tp="", parked=False, fault="", inhibit="")
        assert is_armed() == _is_armed_tp() and servo_blocked() == ""
        ok, _ = tp_set(True, "selftest")
        assert ok and tp_on() and servo_blocked() == "transport" and not is_armed() and CFG["kopf_transport_pos"] == [50.0, 50.0]
        assert "Transport" in protect_label("armed") and lupe_head_block() == "Transport mode active"
        assert not move_camera("left", 5, "selftest") and not servo_goto(10, 10, "selftest", wait=False)
        k_ = srv_axis_limits("pan")[0] / max(1e-6, float(CFG["servo_vmax_pan"]))       # % per degree
        mx, n = 0.0, 0
        while not servo_detached() and n < 3000:
            p0 = list(SRV["pos"])
            CFG["pan"], CFG["tilt"] = 0.0, 100.0             # somebody tries to steer: the planner does not take it
            servo_plan_tick(0.02); n += 1
            mx = max(mx, abs(SRV["pos"][0] - p0[0]) / 0.02 / k_)
        assert servo_detached() and abs(SRV["pos"][0] - 50.0) < 1e-6 and abs(SRV["pos"][1] - 50.0) < 1e-6, (SRV["pos"], n)
        assert mx <= 15.5, mx                                 # slowly: at most 15 °/s
        assert servo_outputs_off() and tp_phase() == "free"
        for _ in range(20):
            CFG["pan"] = 5.0; servo_plan_tick(0.02)
        assert SRV["pos"] == [50.0, 50.0] and CFG["pan"] == 50.0
        KOPF["turn_req"] = (10.0, 10.0, "selftest"); _kopf_tick()
        assert KOPF["turn_req"] is None and KOPF["status"].startswith("transport")
        assert web_disarms("/api/transport", {"on": True}) and not web_disarms("/api/transport", {"on": False})
        ok, _ = tp_set(False, "selftest")
        assert ok and not tp_on() and not servo_detached() and servo_blocked() == "" and armed_n == [1] and CFG["pan"] == 50.0
        assert is_armed() == _is_armed_tp()
        assert 'id="tp-css"' in WEB_PAGE and "window.tpPaint(j)" in WEB_PAGE and "tpPanel(d)" in WEB_PAGE
        assert HELP_PAGE.count('id="tp-help"') == 2 and all('id="tp-help"' in HELP_X.get(L_, 'id="tp-help"') for L_ in ("fr", "it", "rm"))
        # the window button: our wrapper is the outermost one - or the saved predecessor of a later one (later parts, and 557
        # thermal align which wraps only at the start, _TALIGN_TK) - 3.94.0 / 3.95.0: GitHub with tkinter was red here
        assert not GUI_OK or _tp_tk_build_section in (App._build_section, (globals().get("_TALIGN_TK") or {}).get("before"),
                                *[v for k, v in globals().items() if k.startswith("_") and k.endswith(("_build_section_before", "_build_section_base"))]), "window button"
        for k, v in _HX_TRANSPORT.items():
            assert len(v) == 4 and all(v) and "ß" not in "".join(v), k
        assert tr("Transport mode", "de") == "Transportmodus" and tr("Cap removed?", "it") == "Cappuccio tolto?"
    finally:
        G.update(keep_fn)
        CFG.update(keep); SRV.update(keep_srv); MANUAL.update(keep_man)
    return "home at 15 °/s, released, targets refused, no alarms, back as before, page hooks, texts"


SELFTEST_EXTRA.append(("Transport mode «🧳» (639zzzt)", transport_selftest))
