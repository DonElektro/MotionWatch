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
SPIELTEST = {"seen": 0, "n": 0, "st": "", "t": 0.0, "last": None}
_SPIELTEST_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def spieltest_clean(text):
    """the text of the simulator: one line, at most 200 characters (no control characters)"""
    return _SPIELTEST_CTRL.sub(" ", str(text or "")).strip()[:200]


def spieltest_feed(lst, first=False):
    """world_reply «spieltest» of the simulator: new round messages -> push (only with the switch)"""
    if not isinstance(lst, list):
        return
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
            threading.Thread(target=spieltest_send, args=(text,), daemon=True, name="spieltest").start()


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
    """the switch from the simulator (mw_cmd «spieltest_push», only the developer window / group Entwickler there)"""
    CFG["spieltest_push"] = bool(on)
    save_settings()
    log_event("sim", "Play test messages " + ("on" if on else "off") + " (from the simulator)")


_sim_state_635a = sim_state


def sim_state():                                          # + 635a: «spieltest» - the switch and how the last message went out
    d = _sim_state_635a()
    d["spieltest"] = {"on": bool(CFG.get("spieltest_push")), "seen": int(SPIELTEST["seen"]), "st": str(SPIELTEST["st"]),
                      "t": int(SPIELTEST["t"])}
    return d


_HX_SPIELTEST = {
    "Play test": ("Spieltest", "Test de jeu", "Test di gioco", "Test da gieu"),
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
    finally:
        CFG["spieltest_push"] = old[0]
        SPIELTEST.clear()
        SPIELTEST.update(old[1])
    return "play test messages: only with the switch, main channel, state to the simulator"


SELFTEST_EXTRA.append(("Play test messages of the 3D simulator (635a)", spieltest_selftest))
