#@ MoveEye – Teil 635b: Kurze Push-Nachrichten (Paket «Handy-Mitteilungen kurz», Daniel 31.10.2026): ein Aufbau für alle Meldungen (Titel kurz mit Symbol, höchstens eine Zeile Text, Bild wo sinnvoll, nie JSON), im Simulator-Betrieb nur Alarme aufs Handy (Schalter «Im Simulator: Info-Meldungen aufs Handy», ab Werk aus), ntfy-Adresse in der Webhook-Karte geht als ntfy. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Fehler (Screenshot Daniel, Simulator-Betrieb): Info-Meldungen («Tasten am Gerät», «Netzwerk») kamen mit dem rohen JSON als
# Text aufs Handy ({"event": "info", … "info_title": "{name}: Tasten am Gerät" …}, ä sichtbar). Ursache: der Hauptkanal
# stand auf «Webhook» mit einer ntfy-Adresse - der Webhook schickt den JSON-Körper (json.dumps, ASCII-Escapes, info_title roh)
# und nur den Titel als Kopfzeile; ntfy zeigt den Körper als Nachricht. Jetzt:
#   * 060 _send_main: eine ntfy-Adresse (Host mit «ntfy») in der Webhook-Karte geht als ntfy (push_url_is_ntfy); ein echter
#     Webhook bekommt lesbares JSON (UTF-8, info_title ersetzt).
#   * 060 _title / _text -> push_short(p): ein Aufbau für ALLE Meldungen: «[SIM] » + Symbol + kurzer Titel (ohne Gerätename),
#     Text höchstens eine Zeile (PK_MAX Zeichen), nie {Platzhalter}. Alarme: Schnappschuss wie bisher; «Schutz aus» mit dem
#     aktuellen Kamerabild (060 info -> push_frame_jpg); «Online» ohne Bild, Antippen öffnet die Seite (Click-Link wie bisher).
#     Eigene Nachrichtentexte (msg_<art>_title / _text) gelten weiter. ntfy: keine Emoji-Tags mehr (das Symbol steht im Titel).
#   * 060 _dispatch -> push_sim_hold(p): im Simulator-Betrieb gehen Info-Meldungen (Tasten, Netzwerk, Start, Akku, Updates …)
#     nicht aufs Handy, nur in die Nachrichten (Status «none», «🧪 Simulator»); Alarme (auch Zonen-Meldungen, «Bist du's?»)
#     und Berichte der Simulator-Tests (Nacht-Testlauf, Trainings-Nacht, Wochen-Check) weiter. Schalter sim_info_push
#     (Push → Erweitert im Web 531a und Fenster 571a, Seite Simulator → «Einstellungen der Simulation»), ab Werk aus (636).
#     Der Spieltest-Push (635a) schickt selbst über _send_main und hat seinen eigenen Schalter - davon unberührt.
# Kein ntfy-Thema, keine Adresse, keine Zugangsdaten hier. Hier (nach 470 SIM_PAGE, 560–600 DE / TRX, 586 SET_HELP, vor 636
# Werkseinstellungen), damit der Schalter in FACTORY_CFG ist; 060 ruft push_short / push_kind / push_sim_hold erst beim Senden.
# ----------------------------------------------------------------------------
CFG.setdefault("sim_info_push", False)
DEFAULTS.setdefault("sim_info_push", False)
TOGGLES.append(("Notifications", "sim_info_push", "In the simulator: info messages to the phone"))
PK_HELP = ("While the simulation is on, only alarms (marked [SIM]) go to the phone. Info messages (buttons, network, start, battery, "
           "updates …) stay in MoveEye under Messages. Switch on to get them on the phone too. The play test messages have their own switch.")
PK_REC = "Off: during tests with the simulator the phone stays quiet except for alarms."
SET_HELP["sim_info_push"] = (PK_HELP, PK_REC)
PK_MAX = 80                                               # one line on the phone (ntfy, iPhone lock screen)

# ---- the short forms -------------------------------------------------------------------------------------------------------
# texts (the English key of the call site; a tuple = key + literal rest): (templates, symbol, title, text, class, picture)
# class: info = not to the phone in the simulation (without the switch) · alarm / sim = always
PK_TEXTS = [
    (("Protection switched off at the device",), "🛡", "Protection off", "Switched off at the device", "info", True),
    (("Protection on - alarms are active",), "🛡", "Protection on", "Alarms are active", "info", True),
    (("Siren stopped at the device",), "🔕", "Siren off", "Stopped at the device", "info", False),
    (("Disarmed via MQTT / Home Assistant",), "🛡", "Protection off", "Via MQTT / Home Assistant", "info", True),
    (("MoveEye is online in Wi-Fi {ssid}: {addr}",), "📶", "Online", "Wi-Fi {ssid} · open page", "info", False),
    ((("Simulation switched on automatically (a simulator is online)", ": {who}"),), "🧪", "Simulation on", "{who}", "info", False),
    ((("Fixed again", ": {k}"),), "✅", "Fixed again", "{k}", "info", False),
    (("Power cut – running on the battery ({pct} %)",), "🔌", "Power cut", "Battery {pct} %", "info", False),
    (("Power back – battery {pct} %",), "🔌", "Power back", "Battery {pct} %", "info", False),
    (("Battery almost empty: about {pct} % ({hours:.1f} h) left – please charge or swap", "Battery almost empty: about {pct} % ({hours:.1f} h)"),
     "🪫", "Battery {pct} %", "About {hours} h left · please charge", "info", False),
    (("Battery empty – the Pi shuts down cleanly",), "🪫", "Battery empty", "The Pi shuts down", "info", False),
    (("Under-voltage: power bank almost empty or cable too weak",), "⚡", "Under-voltage", "Power bank almost empty or cable too weak", "info", False),
    (("Battery {pct} %: the battery saver is on - fewer pictures per second, the AI less often. Back to normal when charging.",),
     "🔋", "Battery saver on", "Battery {pct} % · fewer pictures, AI less often", "info", False),
    (("The battery will probably not last until sunrise ({sr}): about {have} h left, {need} h needed. Charge it or switch on power saving.",),
     "🪫", "Battery until sunrise?", "{have} h left, {need} h needed", "info", False),
    (("Memory card almost full: {free} MB free - the oldest recordings are deleted",), "💾", "Memory card almost full", "{free} MB free", "info", False),
    (("Pi too hot: {temp:.0f} °C (limit {lim:.0f} °C) - check the cooling / ventilation",), "🌡", "Pi too hot", "{temp} °C (limit {lim} °C)", "info", False),
    (("Temperature fine again: {t:.1f} °C",), "🌡", "Temperature OK", "{t} °C", "info", False),
    (("Remote access: {who} is watching",), "👁", "Remote access", "{who} is watching", "info", False),
    (("Automatic update to version {v} – the program restarts (about 20 s)",), "⬆", "Update {v}", "Restarts (about 20 s)", "info", False),
    (("New version {v} available - tap «Update now» on the page",), "⬆", "New version {v}", "Tap to update", "info", False),
    (("Person crossed the line «{zone}»",), "🚶", "Person at «{zone}»", "Line crossed", "alarm", False),
    (("Person stays in «{zone}» for more than {secs} s",), "🚶", "Person at «{zone}»", "Stays longer than {secs} s", "alarm", False),
    ((("Person on the public path (only reported, no alarm)", " · {where}"),), "🚶", "Person on the path", "{where} · only reported", "alarm", False),
    (("The picture has been blurred for 15 minutes (sharpness {p} % of normal). Wipe the lens and look for dew or a spider web.",),
     "📷", "Lens dirty?", "Wipe the lens · sharpness {p} %", "info", False),
    (("Weekly check: score {a} instead of {b} – the recognition got worse. Details: tab Simulator.",), "📉", "Weekly check", "Score {a} instead of {b}", "sim", False),
    (("Night test run: score {a} instead of {b} - the recognition got worse. Details: tab Simulator.",), "📉", "Night test run", "Score {a} instead of {b}", "sim", False),
    (("Reference scan: {m} missing, {n} new, {c} changed - see the report",), "🔍", "Reference scan", "{m} missing, {n} new, {c} changed", "info", False),
]
# titles (the English key after «{name}: »): (symbol, short title, class, picture); the text is shortened to one line
PK_TITLES = {
    "Buttons on the device": ("🛡", "Buttons on the device", "info", False), "network": ("ℹ️", "Note", "info", False),
    "power": ("🔌", "Power", "info", False), "battery": ("🔋", "Battery", "info", False), "Battery": ("🔋", "Battery", "info", False),
    "battery saver": ("🔋", "Battery saver on", "info", False), "memory": ("💾", "Memory card", "info", False),
    "temperature": ("🌡", "Temperature", "info", False), "Temperature": ("🌡", "Temperature", "info", False),
    "TEMPERATURE ALARM": ("🌡", "Temperature alarm", "alarm", False), "Update": ("⬆", "Update", "info", False),
    "night report": ("🌙", "Night report", "info", False), "remote access": ("👁", "Remote access", "info", False),
    "Mode": ("⚙", "Mode", "info", False), "Servos": ("↔", "Servos", "info", False), "Self-healing": ("🩹", "Self-healing", "info", False),
    "safe start": ("🩹", "Safe start", "info", False), "Back on": ("🔌", "Back on", "info", False),
    "Training night": ("🧪", "Training night", "sim", False), "Night test run (simulation)": ("🌙", "Night test run", "sim", False),
    "Weekly check": ("📉", "Weekly check", "sim", False), "Test run": ("📉", "Night test run", "sim", False),
    "Weekly detection report": ("📊", "Weekly report", "info", False), "STORM WARNING": ("🌪", "Storm warning", "alarm", False),
    "Missing things": ("🔍", "Missing things", "info", False), "Reference scan": ("🔍", "Reference scan", "info", False),
    "Lens fogged or dirty": ("📷", "Lens dirty?", "info", False), "line": ("🚶", "Person detected", "alarm", False),
    "dwell area": ("🚶", "Person detected", "alarm", False), "Only report": ("🚶", "Person on the path", "alarm", False),
    "question from the product page": ("💬", "Question", "info", False), "Play test": ("🎮", "Play test", "sim", False),
    "Is it you?": ("❓", "Is it you?", "alarm", False), "TAMPER ALARM": ("🛑", "Sabotage", "alarm", False),
    "THEFT ALARM": ("🚨", "Theft alarm", "alarm", False), "Camera lost": ("📷", "Camera lost", "alarm", False),
    "Wi-Fi jamming attack": ("📶", "Wi-Fi jamming", "alarm", False), "Wake-up alarm": ("⏰", "Wake-up alarm", "alarm", False),
    "Quick look at the valuables": ("👀", "Valuables", "alarm", False), "new device in the network": ("📡", "New device", "alarm", False),
    "unknown tracker nearby": ("📍", "Unknown tracker", "alarm", False), "Problem": ("⚠", "Problem", "alarm", False),
}
PK_EVENT = {"person": "Person detected", "prealarm": "Movement", "warm": "Warm body", "noise": "Noise"}
_PK_PH = re.compile(r"\{(\w+)(?::[^}]*)?\}")
_PK_SIM = re.compile(r"\s*\(🧪[^)]*\)|\s*🧪\s*")


def push_url_is_ntfy(url):
    """an ntfy server (ntfy.sh, ntfy-me.com, own «ntfy.…») - its messages must not get a JSON body"""
    try:
        from urllib.parse import urlsplit
        host = urlsplit(str(url or "").strip()).hostname or ""
    except ValueError:
        return False
    return "ntfy" in host.lower()


def pk_line(s, n=None):
    """one line: no line breaks, no control characters, at most n characters (cut at a word, «…»)"""
    n = n or PK_MAX
    s = " · ".join(x.strip() for x in str(s or "").splitlines() if x.strip())
    s = " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", s).split())
    if len(s) <= n:
        return s
    cut = s[:n - 1]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > n * 0.6 else cut).rstrip(" ,;:-–·") + "…"


def _pk_tpl(t):
    """the template in the current language: a key, or (key, literal rest)"""
    return (tr(t[0]) + t[1], t[0] + t[1]) if isinstance(t, tuple) else (tr(t), t)


def _pk_match(tpl, text):
    """the values of the placeholders when text was made from tpl (trailing words of a longer text allowed), else None"""
    parts = _PK_PH.split(tpl)
    rx = "^"
    for i, s_ in enumerate(parts):
        if i % 2 == 0:
            rx += re.escape(s_)
        else:
            rx += "(?P<%s>.+)" % s_ if (i == len(parts) - 2 and parts[-1] == "") else "(?P<%s>.+?)" % s_
    m = re.match(rx + ("" if parts[-1] == "" else ".*") + "$", text, re.S)
    return m.groupdict() if m else None


def _pk_fill(tpl, vals):
    return re.sub(r"\{(\w+)\}", lambda m: str(vals.get(m.group(1), "")).strip(), tpl)


def _pk_cut(text):
    """text without a known form: the first line, the part before « - » / « – » / the first sentence (the advice behind it is on the page)"""
    s = (str(text or "").strip().splitlines() or [""])[0]
    for sep in (" - ", " – ", ". "):
        i = s.find(sep)
        if i >= 12:
            s = s[:i]
    return s


def push_kind(p):
    """the short form of an info / sabotage message: {ic, title, text, cls, pic}"""
    ev = Notifier._event(p)
    text = _PK_SIM.sub(" ", str(p.get("text") or "")).strip()
    raw = re.sub(r"^\{name\}\s*:\s*", "", str(p.get("info_title") or "")).strip()
    test = raw.startswith("[Test] ")
    raw = re.sub(r"^\[Test\]\s*", "", raw)
    raw = _PK_SIM.sub(" ", raw).strip()
    out = None
    for tpls, ic, ti, tx, cls, pic in PK_TEXTS:
        for t_ in tpls:
            for cand in dict.fromkeys(_pk_tpl(t_)):
                v = _pk_match(cand, text)
                if v is not None:
                    out = {"ic": ic, "title": _pk_fill(tr(ti), v), "text": _pk_fill(tr(tx), v), "cls": cls, "pic": pic}
                    break
            if out:
                break
        if out:
            break
    if out is None:
        for key, (ic, ti, cls, pic) in PK_TITLES.items():
            for k_ in dict.fromkeys((tr(key), key)):
                if raw == k_ or raw.startswith(k_ + " – "):
                    out = {"ic": ic, "title": tr(ti) + raw[len(k_):], "text": _pk_cut(text), "cls": cls, "pic": pic}
                    break
            if out:
                break
    if out is None:                                       # unknown: own title, or «Title: rest» of the text, or «Note»
        ti = render_msg(raw, p).strip()
        tx = _pk_cut(text)
        if not ti:
            m = re.match(r"^([^:·\n]{3,30}):\s+(.+)$", tx)
            ti, tx = (m.group(1), m.group(2)) if m else (tr("Note"), tx)
        out = {"ic": ev_icon(ev), "title": ti, "text": tx, "cls": "alarm" if ev == "tamper" else "info", "pic": False}
    m = re.match(r"^" + re.escape(out["title"]) + r"\s*:\s*", out["text"], re.I) if out["title"] else None
    if m and out["text"][m.end():]:                       # «Safe start: …» under the title «Safe start»
        rest = out["text"][m.end():]
        out["text"] = (rest[:1].upper() + rest[1:]) if " " in rest else rest
    if ev == "tamper":
        out["cls"] = "alarm"
    out["test"] = test
    return out


def push_show_name():
    """the device name in the title only when there is more than one MoveEye. There is no pairing yet (CLAUDE.md: «Zwei
    MoveEye koppeln», later); the condition is: other devices in the device list of Teil 260 (CFG «fleet», Cameras page →
    several devices) - or, in the simulation, the «second device in the simulator» (dev2 of the simulator, the cached summary
    of 139 sim_hub, no extra request). Simulators in the network alone do not count (they are no second MoveEye)."""
    if CFG.get("fleet"):
        return True
    try:
        return bool(CFG.get("sim_on") and (_SIMHUB.get("d") or {}).get("dev2"))
    except NameError:
        return False


def push_long(p):
    """the full text for the e-mail (Daniel 31.10.2026: e-mail complete, the phone channels short): the text of the call
    site / the message text with time and camera, the distance, «+n», «late»"""
    ev = Notifier._event(p)
    if ev in ("info", "tamper"):
        t_ = str(p.get("text") or "")
    else:
        kind = "person" if ev == "test" else ev
        t_ = render_msg(msg_template(kind, 1), dict(p, persons=max(1, int(p.get("persons") or 0))) if ev == "test" else p)
        if p.get("dist"):
            t_ += " · " + str(p["dist"])
    if p.get("more"):
        t_ += " " + trf("(+{n} more detections since the last message)", n=p["more"])
    if p.get("late"):
        t_ += " · " + trf("late - from {t} (the message could not be sent then)", t=str(p.get("time", ""))[11:16])
    return t_


def push_protect_on():
    """«🛡 Protection on» with the current camera picture (info; in the simulation only with sim_info_push) - 130 arm_tick
    calls it when the protection becomes active (after the countdown; not at the start of the program)"""
    w = WATCH_REF.get("w")
    n = getattr(w, "notifier", None) if w is not None else None
    if n is None:
        return False
    try:
        return bool(n.info(tr("Protection on - alarms are active"), title="{name}: " + tr("Protection")))
    except Exception as e:
        log_event("sys", f"Protection on message: {type(e).__name__}"[:120])
        return False


def push_short(p):
    """the one form of every push message: {title, text} - title «symbol short title» (the Notifier adds [SIM] and the keyword),
    text at most one line. Own message texts (msg_<kind>_title / _text) stay."""
    ev = Notifier._event(p)
    icons = CFG.get("msg_icons", True)
    t_ = str(p.get("time") or "")
    hm = t_[11:16]
    if ev in ("info", "tamper"):
        k = push_kind(p)
        ic, title, parts = k["ic"], k["title"], [k["text"]]
        if push_show_name():
            title = ((CFG.get("device_name") or "").strip()[:20] or "MoveEye") + ": " + title
        title = ("[Test] " if k["test"] else "") + ((ic + " ") if icons and ic else "") + title
    else:
        kind = "person" if ev == "test" else ev
        pp = dict(p, persons=max(1, int(p.get("persons") or 0))) if ev == "test" else p
        own_t = str(CFG.get(f"msg_{kind}_title", "") or "").strip()
        own_x = str(CFG.get(f"msg_{kind}_text", "") or "").strip()
        n = int(pp.get("persons") or 0)
        title = render_msg(own_t, pp) if own_t else (trf("{n} persons", n=n) if kind == "person" and n > 1 else tr(PK_EVENT.get(kind, "Note")))
        if push_show_name() and not own_t:
            title = ((CFG.get("device_name") or "").strip()[:20] or "MoveEye") + ": " + title
        ic = ev_icon(kind)
        if icons and ic and not title.startswith(ic):
            title = ic + " " + title
        title = ("[Test] " + title) if ev == "test" else title
        if own_x:
            parts = [render_msg(own_x, pp)]
        else:
            parts = [hm]
            if ev == "test":
                parts.append(tr("Test message"))
            elif kind == "person" and p.get("dist"):
                d = str(p["dist"])
                for h_ in (tr("Person") + ", ",):
                    d = d[len(h_):] if d.startswith(h_) else d
                parts.append(d)
            elif kind == "prealarm":
                parts.append(tr("pre-alarm"))
            elif kind == "warm":
                parts.append(tr("thermal camera"))
            elif kind == "noise" and p.get("db") not in (None, ""):
                parts.append(f"{p['db']} dB")
        if own_x and p.get("dist"):
            parts.append(str(p["dist"]))
    if p.get("more"):
        parts.append(trf("+{n} more", n=p["more"]))
    if p.get("late"):
        parts.append(trf("late, from {t}", t=hm))
    title = pk_line(_PK_PH.sub("", render_msg(title, p)) if "{" in title else title, 60)
    text = pk_line(" · ".join(x for x in parts if x))
    return {"title": title, "text": text}


def push_frame_jpg():
    """the current camera picture for «Protection off» (small, about 640 px) - None without a picture"""
    try:
        w = WATCH_REF.get("w")
        fr = getattr(w, "frame_out", None) if w is not None else None
        if fr is None:
            return None
        h, w_ = fr.shape[:2]
        if w_ > 640:
            fr = cv2.resize(fr, (640, int(h * 640 / w_)), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 75])
        return buf.tobytes() if ok else None
    except Exception:
        return None


_PK_HELD = {"t": 0.0}


def push_sim_hold(p):
    """True = not to the phone: in the simulation only alarms (and the reports of simulator tests), unless sim_info_push"""
    if not CFG.get("sim_on") or CFG.get("sim_info_push") or Notifier._event(p) != "info":
        return False
    if push_kind(p)["cls"] in ("alarm", "sim"):
        return False
    STATE["notify_status"] = "simulation: only alarms"
    if time.time() - _PK_HELD["t"] > 60:
        _PK_HELD["t"] = time.time()
        log_event("web", "Info message not sent to the phone (simulation: only alarms, switch «In the simulator: info messages to the phone»)")
    return True


# ---- page Simulator: the same switch in «Settings of the simulation» (470 #simset-box, after the own switches) -----------------
_PK_SIMJS = ('  try { const nx = await (await fetch("/api/schema?sec=Notifications&simple=0&lang=" + LANG)).json(); '
             'const it = ((nx[0] || {}).toggles || []).find(x => x.key === "sim_info_push"); '
             'if (it && !box.querySelector("[data-k=sim_info_push]")) { const l = el("label", "opt"), cb = document.createElement("input"); l.dataset.k = "sim_info_push"; '
             'cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!it.value; '
             'cb.onchange = () => post("/api/set", {key: "sim_info_push", value: cb.checked}).then(r => { if (!r.ok) toast(r.error || t("not possible")); }); '
             'l.append(el("span", "", it.label), cb); box.appendChild(l); } } catch (e) {}\n')
_PK_ANCHOR = '  if (!box.children.length) box.appendChild(el("div", "mut", "–"));\n'
if _PK_ANCHOR in SIM_PAGE:
    SIM_PAGE = SIM_PAGE.replace(_PK_ANCHOR, _PK_SIMJS + _PK_ANCHOR, 1)

# ---- texts (de, fr, it, rm) ------------------------------------------------------------------------------------------------
_HX_PK = {
    "In the simulator: info messages to the phone": ("Im Simulator: Info-Meldungen aufs Handy", "Dans le simulateur : infos sur le téléphone",
                                                     "Nel simulatore: messaggi informativi sul telefono", "En il simulatur: infos sin il telefonin"),
    PK_HELP: ("Während die Simulation läuft, kommen nur Alarme (mit [SIM]) aufs Handy. Info-Meldungen (Tasten, Netzwerk, Start, Akku, Updates …) bleiben in MoveEye unter Nachrichten. Einschalten, wenn du sie trotzdem auf dem Handy willst. Die Spieltest-Meldungen haben ihren eigenen Schalter.",
              "Pendant la simulation, seules les alarmes (marquées [SIM]) arrivent sur le téléphone. Les messages d’info (boutons, réseau, démarrage, batterie, mises à jour …) restent dans MoveEye sous Messages. Active-le pour les recevoir quand même. Les messages du test de jeu ont leur propre interrupteur.",
              "Durante la simulazione arrivano sul telefono solo gli allarmi (con [SIM]). I messaggi informativi (tasti, rete, avvio, batteria, aggiornamenti …) restano in MoveEye sotto Messaggi. Attivalo per riceverli comunque. I messaggi del test di gioco hanno il loro interruttore.",
              "Durant la simulaziun vegnan mo ils alarms (cun [SIM]) sin il telefonin. Ils messadis d’info (buttuns, rait, start, accu, actualisaziuns …) restan en MoveEye sut Messadis. Activar, sche ti als vuls tuttina sin il telefonin. Ils messadis dal test da gieu han lur agen interruptur."),
    PK_REC: ("Aus: bei Tests mit dem Simulator bleibt das Handy ruhig, ausser bei Alarmen.",
             "Arrêt : pendant les tests avec le simulateur, le téléphone reste calme sauf pour les alarmes.",
             "Spento: durante i test con il simulatore il telefono resta tranquillo, tranne per gli allarmi.",
             "Stizzà: durant ils tests cun il simulatur resta il telefonin quiet, auter che per alarms."),
    "Person detected": ("Person erkannt", "Personne détectée", "Persona rilevata", "Persuna identifitgada"),
    "{n} persons": ("{n} Personen", "{n} personnes", "{n} persone", "{n} persunas"),
    "Movement": ("Bewegung", "Mouvement", "Movimento", "Moviment"),
    "Warm body": ("Wärme erkannt", "Corps chaud", "Corpo caldo", "Corp chaud"),
    "Noise": ("Geräusch", "Bruit", "Rumore", "Canera"),
    "Note": ("Hinweis", "Info", "Avviso", "Infurmaziun"),
    "Test message": ("Testnachricht", "Message de test", "Messaggio di prova", "Messadi da test"),
    "pre-alarm": ("Voralarm", "pré-alarme", "preallarme", "pre-alarm"),
    "thermal camera": ("Wärmebild", "caméra thermique", "termocamera", "camera termica"),
    "+{n} more": ("+{n} weitere", "+{n} autres", "+{n} altri", "+{n} ulteriurs"),
    "late, from {t}": ("verspätet, von {t}", "en retard, de {t}", "in ritardo, delle {t}", "tard, da las {t}"),
    "Protection on": ("Schutz ein", "Protection activée", "Protezione attiva", "Protecziun activada"),
    "Protection on - alarms are active": ("Schutz ein – Alarme aktiv", "Protection activée – alarmes actives",
                                          "Protezione attiva – allarmi attivi", "Protecziun activada – alarms activs"),
    "Alarms are active": ("Alarme aktiv", "Alarmes actives", "Allarmi attivi", "Alarms activs"),
    "Protection": ("Schutz", "Protection", "Protezione", "Protecziun"),
    "Protection off": ("Schutz aus", "Protection désactivée", "Protezione spenta", "Protecziun stizzada"),
    "Switched off at the device": ("Am Gerät ausgeschaltet", "Désactivée sur l’appareil", "Spenta sul dispositivo", "Stizzada a l’apparat"),
    "Siren off": ("Sirene aus", "Sirène arrêtée", "Sirena spenta", "Sirena stizzada"),
    "Stopped at the device": ("Am Gerät gestoppt", "Arrêtée sur l’appareil", "Fermata sul dispositivo", "Fermada a l’apparat"),
    "Via MQTT / Home Assistant": ("Über MQTT / Home Assistant", "Via MQTT / Home Assistant", "Tramite MQTT / Home Assistant", "Via MQTT / Home Assistant"),
    "Online": ("Online", "En ligne", "Online", "Online"),
    "Wi-Fi {ssid} · open page": ("WLAN {ssid} · Seite öffnen", "Wi-Fi {ssid} · ouvrir la page", "Wi-Fi {ssid} · apri la pagina", "WLAN {ssid} · avrir la pagina"),
    "Simulation on": ("Simulation ein", "Simulation activée", "Simulazione attiva", "Simulaziun activada"),
    "Fixed again": ("Wieder in Ordnung", "De nouveau en ordre", "Di nuovo a posto", "Puspè en urden"),
    "Power cut": ("Stromausfall", "Coupure de courant", "Interruzione di corrente", "Interrupziun da current"),
    "Power back": ("Strom wieder da", "Courant rétabli", "Corrente tornata", "Current puspè qua"),
    "Battery {pct} %": ("Akku {pct} %", "Batterie {pct} %", "Batteria {pct} %", "Accu {pct} %"),
    "About {hours} h left · please charge": ("Noch etwa {hours} h · bitte laden", "Encore environ {hours} h · à recharger",
                                             "Ancora circa {hours} h · da ricaricare", "Anc var {hours} h · per plaschair chargiar"),
    "Battery empty": ("Akku leer", "Batterie vide", "Batteria scarica", "Accu vid"),
    "The Pi shuts down": ("Der Pi fährt herunter", "Le Pi s’éteint", "Il Pi si spegne", "Il Pi sa stizza"),
    "Under-voltage": ("Unterspannung", "Sous-tension", "Sottotensione", "Tensiun memia bassa"),
    "Power bank almost empty or cable too weak": ("Powerbank fast leer oder Kabel zu schwach", "Batterie externe presque vide ou câble trop faible",
                                                  "Power bank quasi scarico o cavo troppo debole", "Powerbank bunamain vid u cabel memia flaivel"),
    "Battery saver on": ("Akku-Sparen ein", "Économie de batterie activée", "Risparmio batteria attivo", "Spargnar accu activà"),
    "Battery {pct} % · fewer pictures, AI less often": ("Akku {pct} % · weniger Bilder, KI seltener", "Batterie {pct} % · moins d’images, IA moins souvent",
                                                        "Batteria {pct} % · meno immagini, IA meno spesso", "Accu {pct} % · main maletgs, IA pli darar"),
    "Battery until sunrise?": ("Akku bis Sonnenaufgang?", "Batterie jusqu’au lever du soleil ?", "Batteria fino all’alba?", "Accu fin la levada dal sulegl?"),
    "{have} h left, {need} h needed": ("Noch {have} h, nötig {need} h", "Reste {have} h, besoin {need} h", "Restano {have} h, servono {need} h", "Anc {have} h, basegn {need} h"),
    "Memory card almost full": ("Speicherkarte fast voll", "Carte mémoire presque pleine", "Scheda di memoria quasi piena", "Carta da memoria bunamain plaina"),
    "{free} MB free": ("{free} MB frei", "{free} Mo libres", "{free} MB liberi", "{free} MB liber"),
    "Pi too hot": ("Pi zu heiss", "Pi trop chaud", "Pi troppo caldo", "Pi memia chaud"),
    "{temp} °C (limit {lim} °C)": ("{temp} °C (Grenze {lim} °C)", "{temp} °C (limite {lim} °C)", "{temp} °C (limite {lim} °C)", "{temp} °C (limita {lim} °C)"),
    "Temperature OK": ("Temperatur wieder gut", "Température OK", "Temperatura OK", "Temperatura OK"),
    "Temperature alarm": ("Temperatur-Alarm", "Alarme de température", "Allarme temperatura", "Alarm da temperatura"),
    "Remote access": ("Fernzugriff", "Accès à distance", "Accesso remoto", "Access a distanza"),
    "{who} is watching": ("{who} schaut zu", "{who} regarde", "{who} sta guardando", "{who} guarda"),
    "Update {v}": ("Update {v}", "Mise à jour {v}", "Aggiornamento {v}", "Actualisaziun {v}"),
    "Restarts (about 20 s)": ("Startet neu (etwa 20 s)", "Redémarre (environ 20 s)", "Si riavvia (circa 20 s)", "Reaviescha (var 20 s)"),
    "New version {v}": ("Neue Version {v}", "Nouvelle version {v}", "Nuova versione {v}", "Nova versiun {v}"),
    "Tap to update": ("Antippen zum Aktualisieren", "Toucher pour mettre à jour", "Tocca per aggiornare", "Tutgar per actualisar"),
    "Person at «{zone}»": ("Person bei «{zone}»", "Personne à «{zone}»", "Persona a «{zone}»", "Persuna tar «{zone}»"),
    "Line crossed": ("Linie überquert", "Ligne franchie", "Linea attraversata", "Lingia traversada"),
    "Stays longer than {secs} s": ("Bleibt länger als {secs} s", "Reste plus de {secs} s", "Resta più di {secs} s", "Resta pli ditg che {secs} s"),
    "Person on the path": ("Person auf dem Weg", "Personne sur le chemin", "Persona sul sentiero", "Persuna sin la via"),
    "{where} · only reported": ("{where} · nur gemeldet", "{where} · seulement signalé", "{where} · solo segnalato", "{where} · mo annunzià"),
    "Lens dirty?": ("Linse schmutzig?", "Objectif sale ?", "Obiettivo sporco?", "Lentilla malnetta?"),
    "Wipe the lens · sharpness {p} %": ("Linse abwischen · Schärfe {p} %", "Essuyer l’objectif · netteté {p} %", "Pulire l’obiettivo · nitidezza {p} %", "Nettegiar la lentilla · nitidezza {p} %"),
    "Weekly check": ("Wochen-Check", "Contrôle hebdo", "Controllo settimanale", "Controlla d’emna"),
    "Night test run": ("Nacht-Testlauf", "Test de nuit", "Test notturno", "Test da notg"),
    "Score {a} instead of {b}": ("Note {a} statt {b}", "Note {a} au lieu de {b}", "Punteggio {a} invece di {b}", "Nota {a} empè da {b}"),
    "Reference scan": ("Referenz-Scan", "Scan de référence", "Scansione di riferimento", "Scan da referenza"),
    "{m} missing, {n} new, {c} changed": ("{m} fehlen, {n} neu, {c} geändert", "{m} manquants, {n} nouveaux, {c} modifiés",
                                          "{m} mancanti, {n} nuovi, {c} cambiati", "{m} mancan, {n} novs, {c} midads"),
    "Buttons on the device": ("Tasten am Gerät", "Boutons sur l’appareil", "Tasti sul dispositivo", "Buttuns sin l’apparat"),
    "Power": ("Strom", "Courant", "Corrente", "Current"),
    "Battery": ("Akku", "Batterie", "Batteria", "Accu"),
    "Memory card": ("Speicherkarte", "Carte mémoire", "Scheda di memoria", "Carta da memoria"),
    "Temperature": ("Temperatur", "Température", "Temperatura", "Temperatura"),
    "Update": ("Update", "Mise à jour", "Aggiornamento", "Actualisaziun"),
    "Night report": ("Nachtbericht", "Rapport de nuit", "Rapporto notturno", "Rapport da la notg"),
    "Safe start": ("Sicherer Start", "Démarrage sûr", "Avvio sicuro", "Start segir"),
    "Weekly report": ("Wochenbericht", "Rapport hebdomadaire", "Rapporto settimanale", "Rapport d’emna"),
    "Storm warning": ("Sturmwarnung", "Alerte tempête", "Allerta tempesta", "Avertiment da stemprà"),
    "Question": ("Frage", "Question", "Domanda", "Dumonda"),
    "Sabotage": ("Sabotage", "Sabotage", "Sabotaggio", "Sabotascha"),
    "Theft alarm": ("Diebstahl-Alarm", "Alarme de vol", "Allarme furto", "Alarm da ladrun"),
    "Wi-Fi jamming": ("WLAN-Störung", "Brouillage Wi-Fi", "Disturbo Wi-Fi", "Disturbi WLAN"),
    "Valuables": ("Wertsachen", "Objets de valeur", "Oggetti di valore", "Objects da valur"),
    "New device": ("Neues Gerät", "Nouvel appareil", "Nuovo dispositivo", "Nov apparat"),
    "Unknown tracker": ("Unbekannter Tracker", "Traceur inconnu", "Tracker sconosciuto", "Tracker nunenconuschent"),
}
for _k, _v in _HX_PK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


# ---- self-test: the form of every kind, never JSON / escapes / {name}, the simulation filter, the webhook with an ntfy address --
def push_kurz_selftest():
    keys = ("sim_on", "sim_info_push", "msg_icons", "msg_keyword_on", "lang", "device_name", "msg_person_title", "msg_person_text", "fleet")
    keep = {k: CFG.get(k) for k in keys}
    try:
        CFG.update(sim_on=False, sim_info_push=False, msg_icons=True, msg_keyword_on=False, lang="de", device_name="Zelt",
                   msg_person_title="", msg_person_text="", fleet=[])
        now = datetime(2026, 10, 31, 21, 7, 5).isoformat(timespec="seconds")
        def P(**kw):
            return dict({"event": "info", "persons": 0, "time": now, "snapshot": None, "rain": False, "wind": "", "source": "cam", "link": ""}, **kw)
        def T(p):
            return Notifier._title(p), Notifier._text(p)
        bad = re.compile(r"[{}]|\\u|\"event\"|info_title")
        cases = {
            "off": P(text=tr("Protection switched off at the device") + " 🧪", info_title="{name}: " + tr("Buttons on the device")),
            "online": P(text=trf("MoveEye is online in Wi-Fi {ssid}: {addr}", ssid="Camping", addr="http://192.0.2.5:5000/"), info_title="", link="http://192.0.2.5:5000/"),
            "batt": P(text=trf("Battery almost empty: about {pct} % ({hours:.1f} h) left – please charge or swap", pct=12, hours=1.5), info_title="{name}: " + tr("battery")),
            "person": P(event="person", persons=1, dist=tr("Person") + ", " + trf("about {m} m", m=12) + ", " + tr("coming closer")),
            "night": P(text="Zeile 1\nZeile 2", info_title="{name}: " + tr("night report")),
            "unknown": P(text="Etwas ganz Neues: " + "x " * 80, info_title=""),
        }
        out = {k: T(p) for k, p in cases.items()}
        for k, (ti, tx) in out.items():
            assert not bad.search(ti + tx), f"{k}: placeholder / JSON in «{ti}» «{tx}»"
            assert "\n" not in tx and len(tx) <= PK_MAX and len(ti) <= 60, f"{k}: more than one line: «{tx}»"
        assert out["off"] == ("🛡 Schutz aus", "Am Gerät ausgeschaltet"), out["off"]
        assert out["online"] == ("📶 Online", "WLAN Camping · Seite öffnen"), out["online"]
        assert out["batt"] == ("🪫 Akku 12 %", "Noch etwa 1.5 h · bitte laden"), out["batt"]
        assert out["person"] == ("🚶 Person erkannt", "21:07 · ca. 12 m, kommt näher") or out["person"][0] == "🚶 Person erkannt", out["person"]
        assert out["night"] == ("🌙 Nachtbericht", "Zeile 1"), out["night"]
        assert push_kind(cases["off"])["pic"] and not push_kind(cases["online"])["pic"], "picture only for «Protection off»"
        on = P(text=tr("Protection on - alarms are active"), info_title="{name}: " + tr("Protection"))
        assert T(on) == ("🛡 Schutz ein", "Alarme aktiv") and push_kind(on)["pic"], T(on)
        # the device name only with several MoveEye (device list of 260)
        CFG["fleet"] = [{"url": "http://192.0.2.9:5000", "id": "x"}]
        assert Notifier._title(cases["off"]) == "🛡 Zelt: Schutz aus" and Notifier._title(cases["person"]) == "🚶 Zelt: Person erkannt", Notifier._title(cases["off"])
        CFG["fleet"] = []
        # e-mail: the complete text
        assert push_long(cases["batt"]).endswith(tr("Battery almost empty: about {pct} % ({hours:.1f} h) left – please charge or swap").format(pct=12, hours=1.5))
        assert "Person" in push_long(cases["person"]) and "cam" in push_long(cases["person"]), push_long(cases["person"])
        CFG["msg_person_title"] = "{name}: Achtung"
        assert Notifier._title(cases["person"]) == "🚶 Zelt: Achtung", "own title with {name} replaced"
        CFG["msg_person_title"] = ""
        # the simulation: [SIM] in front, info messages held back (switch off), alarms and sim reports go out
        CFG["sim_on"] = True
        assert Notifier._title(cases["off"]).startswith("[SIM] 🛡 "), "[SIM] in front"
        assert push_sim_hold(cases["off"]) and push_sim_hold(cases["online"]) and push_sim_hold(cases["batt"]), "info in the simulation"
        assert not push_sim_hold(cases["person"]) and not push_sim_hold(P(event="tamper", text="x", info_title="{name}: " + tr("TAMPER ALARM")))
        assert not push_sim_hold(P(text="x", info_title="{name}: 🧪 " + tr("Night test run (simulation)"))), "the report of a sim test goes out"
        assert not push_sim_hold(P(text=trf("Person crossed the line «{zone}»", zone="Eingang"), info_title="{name}: " + tr("line"))), "zone = alarm"
        assert Notifier._title(P(text=trf("Person crossed the line «{zone}»", zone="Eingang"), info_title="{name}: " + tr("line"))) == "[SIM] 🚶 Person bei «Eingang»"
        CFG["sim_info_push"] = True
        assert not push_sim_hold(cases["off"]), "the switch lets info messages through"
        CFG["sim_on"] = False; CFG["sim_info_push"] = False
        assert not push_sim_hold(cases["off"]), "outside the simulation everything as before"
        assert globals().get("FACTORY_CFG", {}).get("sim_info_push") is False, "not in the factory settings (off)"
        assert any(x[1] == "sim_info_push" and x[0] == "Notifications" for x in TOGGLES), "switch not in the push group"
        assert "sim_info_push" in SIM_PAGE, "switch not on the page Simulator"
        # an ntfy address in the webhook card goes as ntfy, a real webhook gets readable JSON
        assert push_url_is_ntfy("https://ntfy.sh/x") and push_url_is_ntfy("https://ntfy-me.com/x") and not push_url_is_ntfy("https://ha.local/api/webhook/x")
        for L in ("fr", "it", "rm", "en"):
            CFG["lang"] = L
            ti, tx = T(P(text=tr("Protection switched off at the device"), info_title="{name}: " + tr("Buttons on the device")))
            assert ti.startswith("🛡 ") and tx and not bad.search(ti + tx), f"{L}: {ti} / {tx}"
    finally:
        CFG.update(keep)
    return "one short form (title with symbol, one line), [SIM], only alarms in the simulation, webhook with an ntfy address"


SELFTEST_EXTRA.append(("Short push messages, only alarms in the simulation (635b)", push_kurz_selftest))
