#@ MoveEye – Teil 635a: Spieltest-Meldungen (Paket «Spieltest-Assistent», Daniel 31.10.2026) – der Spieltest-Assistent des 3D-Simulators meldet jede fertige Runde kurz, MoveEye schickt sie über seinen Push (nur mit dem Schalter «Spieltest-Meldungen», Gruppe Entwickler). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Simulator: simulator3d/scripts/spieltest.gd (Mehr → Entwickler → Spieltest) beobachtet die Spielmodi und schreibt nach
# jeder Runde eine kurze Meldung in world_reply «spieltest» (Liste: id, t, text - schon in der Sprache des Simulators), z. B.
# «Spieltest: Abenteuer Kap. 2 fertig, 12 Min., 3 Tipps, 😀». MoveEye (350 SimLink.tick -> spieltest_feed):
#   * eine neue Meldung (id grösser als die letzte, nicht älter als 10 Min., nicht von vor der Verbindung) geht NUR mit dem
#     Schalter «spieltest_push» (Einstellungen → Entwickler, nur mit Entwickler-Bereich sichtbar, Standard aus) hinaus;
#   * über den Hauptkanal der bestehenden Push-Einstellung (ntfy / Telegram / Webhook, Notifier._send_main) - nicht an die
#     eigenen Kanäle der Benutzer (041), nicht als Alarm; bewusst AUCH während eines Spiels (sonst Test-Postfach 141): die
#     Meldung ist für den Besitzer, darum hat sie ihren eigenen Schalter. Ohne eingerichteten Push: nur in die Nachrichten.
#   * Zustand «spieltest» an den Simulator (sim_state): on, seen (letzte id), st (sent / none / error / off / net), t - der
#     Simulator zeigt damit im Entwickler-Fenster, ob es einen Push gibt; sein Schalter fragt über mw_cmd «spieltest_push».
#   * Code-Prüfung (M1, Daniel 31.10.2026): der Simulator darf den Schalter nur AUSschalten - einschalten nur in MoveEye
#     (ein fremdes Gerät, das sich als Simulator meldet, könnte sonst Texte aufs Handy schicken). Gegen eine Flut: höchstens
#     eine Push-Nachricht pro SPIELTEST_GAP_S Sekunden und SPIELTEST_MAX_H pro Stunde; was dazwischen kommt, wird gesammelt und
#     mit der nächsten erlaubten Nachricht geschickt («+2 weitere»), über der Stundengrenze nur noch in die Nachrichten.
# Kein ntfy-Thema, keine Zugangsdaten hier - es gilt nur, was in den Push-Einstellungen steht.
# Hier (nach 570 TOGGLES, 560 DE / TRX, 290 sim_state, vor 636 Werkseinstellungen) damit der Schalter in FACTORY_CFG ist.
# ----------------------------------------------------------------------------
CFG.setdefault("spieltest_push", False)
DEFAULTS.setdefault("spieltest_push", False)
TOGGLES.append(("Developer", "spieltest_push", "Play test messages to the phone"))   # (short label, menu 2: the text below is the «?» help)
SIMPLE_KEYS.add("spieltest_push")
SPIELTEST_HELP = ("After every round of the play test assistant in the 3D simulator (More → Developer → Play test) a short push "
                  "through your push channel, e.g. «Play test: Adventure ch. 2 done, 12 min, 3 tips». Only for you, not as an alarm.")
SPIELTEST_REC = "Off unless you are testing the games; switch it off again afterwards."
SPIELTEST = {"seen": 0, "n": 0, "st": "", "t": 0.0, "last": None, "q": [], "sent_t": [], "busy": False}
SPIELTEST_GAP_S = 60.0       # at most one push per minute (a round of a game takes minutes; a broken simulator not 60 a second)
SPIELTEST_MAX_H = 20         # and at most 20 an hour - beyond that only into the messages (the phone stays quiet)
_SPIELTEST_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def spieltest_clean(text):
    """the text of the simulator: one line, at most 200 characters (no control characters)"""
    return _SPIELTEST_CTRL.sub(" ", str(text or "")).strip()[:200]


def spieltest_due(now=None):
    """the collected messages (oldest first) when the next push is allowed now, else [] (the pause / the limit per hour)"""
    now = time.time() if now is None else now
    q = SPIELTEST["q"]
    if not q or SPIELTEST["busy"]:
        return []
    sent = SPIELTEST["sent_t"] = [t_ for t_ in SPIELTEST["sent_t"] if now - t_ < 3600.0]
    if sent and now - sent[-1] < SPIELTEST_GAP_S:
        return []
    out = list(q); q.clear()
    return out


def spieltest_join(texts):
    """several collected messages -> one text: the newest + «(+n more)»"""
    if len(texts) <= 1:
        return texts[0] if texts else ""
    return spieltest_clean(texts[-1] + " " + trf("(+{n} more)", n=len(texts) - 1))


def spieltest_flush(now=None):
    """send what was collected, if the pause is over (called with every SimLink tick through spieltest_feed)"""
    now = time.time() if now is None else now
    texts = spieltest_due(now)
    if not texts:
        return None
    text = spieltest_join(texts)
    if len(SPIELTEST["sent_t"]) >= SPIELTEST_MAX_H:       # the limit per hour: only into the messages
        SPIELTEST.update(last={"t": now, "text": text}, t=now, st="limit")
        msglog_add(Notifier._title(spieltest_payload(text)), text, "info", None, "none", "")
        if now - SPIELTEST.get("limit_log", 0.0) > 600:
            SPIELTEST["limit_log"] = now
            log_event("sim", f"Play test messages: more than {SPIELTEST_MAX_H} an hour - only in the messages, not to the phone")
        return "limit"
    if CFG.get("spieltest_push") and not sim_net_down():
        SPIELTEST["sent_t"].append(now)
    SPIELTEST["busy"] = True

    def _run():
        try:
            spieltest_send(text)
        finally:
            SPIELTEST["busy"] = False
    threading.Thread(target=_run, daemon=True, name="spieltest").start()
    return "go"


def spieltest_feed(lst, first=False):
    """world_reply «spieltest» of the simulator: new round messages -> collected -> push (only with the switch, pause +
    limit per hour: spieltest_flush)"""
    try:
        if not isinstance(lst, list):
            return
        _spieltest_take(lst, first)
    finally:
        spieltest_flush()


def _spieltest_take(lst, first):
    for it in lst[-6:]:
        if not isinstance(it, dict):
            continue
        try:
            id_ = int(it.get("id") or 0)
            t_ = float(it.get("t") or 0)
        except (TypeError, ValueError):
            continue
        if id_ <= SPIELTEST["seen"]:
            continue
        SPIELTEST["seen"] = id_
        if first or (t_ and abs(time.time() - t_) > 600):   # from before the connection / old: not again
            continue
        text = spieltest_clean(it.get("text"))
        if text:
            SPIELTEST["q"] = (SPIELTEST["q"] + [text])[-10:]      # collected; spieltest_flush sends when the pause is over


def spieltest_payload(text):
    """the message as the Notifier builds it (event «info»: title «{name}: Play test», the text of the simulator)"""
    return {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": text,
            "info_title": "{name}: " + tr("Play test"), "snapshot": None, "rain": False, "wind": "",
            "source": STATE.get("source_label", ""), "link": ""}


def spieltest_send(text):
    """one message: through the main push channel if the switch is on; returns the state (sent / none / error / off / net)"""
    p = spieltest_payload(text)
    SPIELTEST.update(last={"t": time.time(), "text": text}, t=time.time())
    st = "off"
    if not CFG.get("spieltest_push"):
        st = "off"
    elif sim_net_down():                                  # the «WLAN weg» test of the simulator: nothing goes out (285)
        st = "net"
    else:
        w = WATCH_REF.get("w")
        n = getattr(w, "notifier", None) if w is not None else None
        title = Notifier._title(p)
        if n is None or not Notifier.main_configured() or not CFG.get("notify_on", True):
            st = "none"
            msglog_add(title, text, "info", None, "none", "")
        else:
            try:
                code, where = n._send_main(p, None, "")
                st = "sent"
                msglog_add(title, text, "info", None, "sent", str(where).split(" ")[0])
                log_event("sim", f"Play test message sent ({where}, HTTP {code})"[:160])
            except Exception as e:
                st = "error"
                msglog_add(title, text, "info", None, "failed", CFG.get("notify_type", ""))
                log_event("sim", f"Play test message failed: {type(e).__name__}"[:160])
    SPIELTEST["st"] = st
    SPIELTEST["n"] += 1 if st == "sent" else 0
    return st


def spieltest_set(on):
    """the switch from the simulator (mw_cmd «spieltest_push», only the developer window / group Entwickler there): the
    simulator may only switch it OFF - on only in MoveEye (Einstellungen → Entwickler), Code-Prüfung M1"""
    if on:
        if not CFG.get("spieltest_push"):
            log_event("sim", "Play test messages: the simulator asked to switch them on - refused, only in MoveEye "
                             "(Settings → Developer)")
        return False
    if CFG.get("spieltest_push"):
        CFG["spieltest_push"] = False
        save_settings()
        log_event("sim", "Play test messages off (from the simulator)")
    return True


_sim_state_635a = sim_state


def sim_state():                                          # + 635a: «spieltest» - the switch and how the last message went out
    d = _sim_state_635a()
    d["spieltest"] = {"on": bool(CFG.get("spieltest_push")), "seen": int(SPIELTEST["seen"]), "st": str(SPIELTEST["st"]),
                      "t": int(SPIELTEST["t"])}
    return d


_HX_SPIELTEST = {
    "Play test": ("Spieltest", "Test de jeu", "Test di gioco", "Test da gieu"),
    "(+{n} more)": ("(+{n} weitere)", "(+{n} autres)", "(+{n} altri)", "(+{n} ulteriurs)"),
    "Play test messages to the phone": ("Spieltest-Meldungen aufs Handy", "Messages du test de jeu sur le téléphone",
                                        "Messaggi del test di gioco sul telefono", "Messadis dal test da gieu sin il telefonin"),
    SPIELTEST_HELP: ("Nach jeder Runde des Spieltest-Assistenten im 3D-Simulator (Mehr → Entwickler → Spieltest) eine kurze Push-Nachricht über deinen Push-Kanal, z. B. «Spieltest: Abenteuer Kap. 2 fertig, 12 Min., 3 Tipps». Nur für dich, nicht als Alarm.",
                     "Après chaque partie de l’assistant de test du simulateur 3D (Plus → Développeur → Test de jeu), un court push sur ton canal, p. ex. « Test de jeu : Aventure chap. 2 terminé, 12 min, 3 indices ». Seulement pour toi, pas comme alarme.",
                     "Dopo ogni partita dell’assistente di test nel simulatore 3D (Altro → Sviluppatore → Test di gioco) un breve push sul tuo canale, p. es. «Test di gioco: Avventura cap. 2 finita, 12 min, 3 suggerimenti». Solo per te, non come allarme.",
                     "Suenter mintga runda da l’assistent da test en il simulatur 3D (Dapli → Sviluppader → Test da gieu) in curt push sin tes chanal, p. ex. «Test da gieu: Aventura cap. 2 finì, 12 min., 3 tips». Mo per tai, betg sco alarm."),
}
SET_HELP["spieltest_push"] = (SPIELTEST_HELP, SPIELTEST_REC)  # the «?» of the switch (586 g2_help)
_HX_SPIELTEST[SPIELTEST_REC] = ("Aus, ausser du testest gerade die Spiele; danach wieder ausschalten.",
                                "Arrêt, sauf si tu testes les jeux ; ensuite le remettre sur arrêt.",
                                "Spento, a meno che tu stia testando i giochi; poi spegnerlo di nuovo.",
                                "Stizzà, auter che ti testeschas gist ils gieus; suenter puspè stizzar.")
for _k, _v in _HX_SPIELTEST.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def spieltest_selftest():
    old = (CFG.get("spieltest_push"), dict(SPIELTEST))
    try:
        assert spieltest_clean("a\nb\x07c" + "x" * 300) == "a b c" + "x" * 195, "text not cleaned"
        CFG["spieltest_push"] = False
        SPIELTEST.update(seen=0, st="", last=None)
        spieltest_feed([{"id": 5, "t": time.time(), "text": "old"}], first=True)      # from before the connection: only noted
        assert SPIELTEST["seen"] == 5 and SPIELTEST["last"] is None, "a message from before the connection was sent"
        assert spieltest_send("Spieltest: Abenteuer Kap. 2 fertig, 12 Min., 3 Tipps, 😀") == "off", "sent without the switch"
        p = spieltest_payload("Spieltest: x")
        assert p["event"] == "info" and p["info_title"].endswith(tr("Play test")) and "x" in Notifier._text(p), "payload"
        assert "spieltest" in sim_state() and sim_state()["spieltest"]["on"] is False, "state field"
        assert any(t_[1] == "spieltest_push" and t_[0] == "Developer" for t_ in TOGGLES), "switch not in Developer"
        # M1: the simulator can not switch it on (only off)
        _ss = globals()["save_settings"]
        globals()["save_settings"] = lambda *a, **k: None
        try:
            assert spieltest_set(True) is False and CFG["spieltest_push"] is False, "the simulator switched the push on"
            CFG["spieltest_push"] = True
            assert spieltest_set(False) is True and CFG["spieltest_push"] is False, "the simulator can not switch it off"
        finally:
            globals()["save_settings"] = _ss
        # M1: a flood (a new id with every tick) -> at most one push a minute, the rest collected, limit per hour
        CFG["spieltest_push"] = True
        SPIELTEST.update(seen=0, q=[], sent_t=[], busy=False)
        t0 = 1_000_000.0
        sent = []
        for i in range(600):                                # 60 s of ticks every 0.1 s, a new message each
            _spieltest_take([{"id": i + 1, "t": 0, "text": f"Runde {i + 1}"}], False)
            got = spieltest_due(t0 + 0.1 * i)
            if got:
                sent.append(spieltest_join(got)); SPIELTEST["sent_t"].append(t0 + 0.1 * i)
        assert len(sent) == 1 and sent[0] == "Runde 1", sent
        got = spieltest_due(t0 + 60.5)
        assert got and len(got) == 10 and "(+9 " in spieltest_join(got), (len(got), spieltest_join(got))   # collected (last 10)
        SPIELTEST["sent_t"] = [t0 + 60.0 * k for k in range(SPIELTEST_MAX_H)]
        SPIELTEST["q"] = ["x"]
        _ml = globals()["msglog_add"]; globals()["msglog_add"] = lambda *a, **k: None
        try:
            assert spieltest_flush(t0 + 60.0 * SPIELTEST_MAX_H) == "limit", "no limit per hour"
        finally:
            globals()["msglog_add"] = _ml
    finally:
        CFG["spieltest_push"] = old[0]
        SPIELTEST.clear()
        SPIELTEST.update(old[1])
    return "play test messages: only with the switch (the simulator only switches off), pause 60 s + 20 an hour, state to the simulator"


SELFTEST_EXTRA.append(("Play test messages of the 3D simulator (635a)", spieltest_selftest))
