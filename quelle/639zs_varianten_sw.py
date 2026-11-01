#@ MoveEye – Teil 639zs: Ausbauvarianten ohne alle Teile (Basis, Komplett, Autark): ehrliche Selbstdiagnose ohne Servo-Treiber (GPIO-Ausweich ohne Rückmeldung) und ohne Wärmebild-Modul («nicht gefunden» statt «USB-Kabel prüfen»), «Relay 1» ab Werk aus, Mover-Fahrt ist «eigene Fahrt» für Bewegungssensor und Bild-Sabotage; Texte in 5 Sprachen, Selbsttest. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «real-varianten-sw» (01.11.2026, aus dem Bericht «Ausbauvarianten im Check»). Die Logik steht dort, wo sie hingehört:
#   * 080 servo_gpio_fallback / SERVO_GPIO_FALLBACK_TEXT, 120 health_check «servo»: «automatisch» ohne PCA9685 = Hinweis (warn,
#     kind «gpio_fallback»), kein grüner Haken; von Hand «GPIO» gewählt bleibt ok. Auch Servo-Seite (072 servo_state
#     «backend_note», 541) und Fenster-Status «Servo driver» (570).
#   * 230 thermal_absent / THERMAL_NOT_FOUND / THERMAL_TIPS, 120 health_check «thermal»: nichts antwortet (I2C Errno 121, kein
#     /dev/video<N> …) = «nicht gefunden – vielleicht nicht eingebaut» (kind «not_found»); gefunden, aber Fehler = Tipp je Quelle
#     (Thermal-90: Flachkabel SPI / I2C, Treiber fehlt, USB: Kabel, Simulator). Dieselbe Meldung nur einmal im Log statt alle 5 s.
#   * 020 default_relays: «Relay 1» (GPIO 22) ab Werk «aus»; 040 relay1_migrate: ältere Einstellungen (ohne «relay1_off_done»)
#     nur dann, wenn das Relais nie verändert wurde (genau das alte Werks-Relais), einmal auf «aus». Begründung: ohne Relais
#     schaltet GPIO 22 ins Leere oder in etwas anderes, das dort hängt; bisher gibt es kein ausgeliefertes Gerät mit Relais.
#   * 070 mover_own_motion, 060 TamperGuard: während eigener Fahrbefehle des Movers und MOVER_QUIET_S (3 s) danach zählt der
#     Bewegungssensor nicht «Gerät bewegt» (nur Umfallen > 60° gegenüber vorher), danach lernt er die neue Ruhelage; das Bild
#     lernt ebenfalls neu. Bewegen von Hand (keine Fahrt) meldet wie bisher.
# Hier nur: Übersetzungen, Hilfe-Satz, Selbsttest.
# ----------------------------------------------------------------------------
_HX_VARSW = {
    SERVO_GPIO_FALLBACK_TEXT: (
        "kein Servo-Treiber gefunden – GPIO-Ausweich (17 / 27) ohne Rückmeldung",
        "aucun pilote de servo trouvé – repli GPIO (17 / 27) sans retour",
        "nessun driver servo trovato – ripiego GPIO (17 / 27) senza riscontro",
        "nagin driver da servos chattà – remplazzament GPIO (17 / 27) senza resposta"),
    SERVO_GPIO_FALLBACK_TIP: (
        "Gehäuse v5.x: der PCA9685 (0x41) antwortet nicht – Strom und I2C prüfen, dann neu starten. Kein Kopf eingebaut: nichts zu "
        "tun. Servos wirklich an GPIO 17 / 27: Servo-Treiber «GPIO» wählen.",
        "Boîtier v5.x : le PCA9685 (0x41) ne répond pas – vérifiez son alimentation et l’I2C, puis redémarrez. Pas de tête montée : "
        "rien à faire. Servos vraiment sur GPIO 17 / 27 : choisissez le pilote de servo «GPIO».",
        "Custodia v5.x: il PCA9685 (0x41) non risponde – controlla alimentazione e I2C, poi riavvia. Nessuna testa montata: niente "
        "da fare. Servo davvero su GPIO 17 / 27: scegli il driver servo «GPIO».",
        "Chascha v5.x: il PCA9685 (0x41) na respunda betg – controllar current ed I2C, lura reaviar. Nagin chau montà: nagut da "
        "far. Servos propi vi da GPIO 17 / 27: tscherner il driver da servos «GPIO»."),
    "not found - maybe not built in": (
        "nicht gefunden – vielleicht nicht eingebaut", "introuvable – peut-être pas montée", "non trovata – forse non montata",
        "betg chattà – forsa betg montà"),
    THERMAL_TIPS["missing"]: (
        "Nicht eingebaut: Wärmebild ausschalten (Einstellungen → Wärmebild). Eingebaut: Flachkabel (SPI / I2C) prüfen und SPI und "
        "I2C einschalten (raspi-config), dann MoveEye neu starten.",
        "Pas montée : désactivez la caméra thermique (Réglages → Caméra thermique). Montée : vérifiez le câble plat (SPI / I2C) et "
        "activez SPI et I2C (raspi-config), puis redémarrez MoveEye.",
        "Non montata: spegni la termocamera (Impostazioni → Termocamera). Montata: controlla il cavo piatto (SPI / I2C) e attiva "
        "SPI e I2C (raspi-config), poi riavvia MoveEye.",
        "Betg montada: stizzar la camera termica (Parameters → Camera termica). Montada: controllar il cabel plat (SPI / I2C) ed "
        "activar SPI ed I2C (raspi-config), lura reaviar MoveEye."),
    THERMAL_TIPS["senxor"]: (
        "Gefunden, meldet aber einen Fehler: Flachkabel der Thermal-90 (SPI / I2C) prüfen und MoveEye neu starten.",
        "Trouvée, mais elle signale une erreur : vérifiez le câble plat de la Thermal-90 (SPI / I2C) et redémarrez MoveEye.",
        "Trovata, ma segnala un errore: controlla il cavo piatto della Thermal-90 (SPI / I2C) e riavvia MoveEye.",
        "Chattada, ma ella annunzia ina errur: controllar il cabel plat da la Thermal-90 (SPI / I2C) e reaviar MoveEye."),
    THERMAL_TIPS["driver"]: (
        "Der Waveshare-Treiber (pysenxor) fehlt – siehe Mehr → Bauen → Software.",
        "Le pilote Waveshare (pysenxor) manque – voir Plus → Construire → Logiciel.",
        "Manca il driver Waveshare (pysenxor) – vedi Altro → Costruire → Software.",
        "Il driver da Waveshare (pysenxor) manca – guarda Dapli → Construir → Software."),
    THERMAL_TIPS["sim"]: (
        "Simulator starten (oder eine andere Wärmebild-Quelle wählen).",
        "Démarrez le simulateur (ou choisissez une autre source thermique).",
        "Avvia il simulatore (o scegli un’altra sorgente termica).",
        "Aviar il simulatur (u tscherner in’autra funtauna termica)."),
}
for _k, _v in _HX_VARSW.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX.setdefault(_L, {}).setdefault(_k, _v[_i + 1])

_VARSW_HELP = (
    ("<li><b>Relais:</b> Aus / Ein / Auto.",
     "<li><b>Relay 1 (GPIO 22) ab Werk aus</b> (ab 3.44.3): ohne Relais schaltet MoveEye nichts ins Leere. Mit Warnlampe am Relais "
     "einmal auf Auto stellen. Ältere Einstellungen bleiben, wie sie sind – nur ein nie verändertes Werks-Relais wurde einmal "
     "ausgeschaltet.</li>"),
    ("<li><b>Relays:</b> Off / On / Auto.",
     "<li><b>Relay 1 (GPIO 22) is off from the factory</b> (from 3.44.3): without a relay MoveEye switches nothing into the void. "
     "With a warning lamp on the relay set it to Auto once. Older settings stay as they are – only a never changed factory relay "
     "was switched off once.</li>"),
)
for _a, _b in _VARSW_HELP:
    if _a in HELP_PAGE and _b not in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _b + _a, 1)


# ---- self-test ----------------------------------------------------------------------------------------------------------------
def _varsw_item(key, lang="en"):
    return next((x for x in health_check(lang)["items"] if x["id"] == key), None)


def varianten_sw_selftest():
    keep_state = {k: STATE.get(k) for k in ("servo_backend", "thermal")}
    keep_cfg = {k: CFG.get(k) for k in ("servo_driver", "thermal_source", "relay1_off_done", "tamper_tilt")}
    keep_relays = [dict(r) for r in RELAYS]
    keep_mover = dict(MOVER)
    keep_armed = globals()["is_armed"]
    notes = []
    try:
        # 1. servos: «automatic» without a PCA9685 -> a hint, not ok; GPIO chosen by hand / PCA9685 -> ok
        assert servo_gpio_fallback("gpiozero", "auto") and servo_gpio_fallback("pigpio", "auto"), "auto + GPIO = fallback"
        assert not servo_gpio_fallback("gpiozero", "gpio") and not servo_gpio_fallback("pca9685", "auto"), "chosen / PCA9685"
        assert not servo_gpio_fallback("simulation", "auto"), "simulation is «not found», not a fallback"
        if not servo_blocked():
            CFG["servo_driver"] = "auto"; STATE["servo_backend"] = "gpiozero"
            it = _varsw_item("servo")
            assert it and it["level"] == "warn" and it.get("kind") == "gpio_fallback" and "GPIO" in it["text"], it
            de = _varsw_item("servo", "de")
            assert "kein Servo-Treiber gefunden" in de["text"] and "PCA9685" in de["tip"], de
            CFG["servo_driver"] = "gpio"
            assert _varsw_item("servo")["level"] == "ok", "GPIO by hand: ok"
            CFG["servo_driver"] = "auto"; STATE["servo_backend"] = "pca9685"
            assert _varsw_item("servo")["level"] == "ok", "PCA9685: ok"
            STATE["servo_backend"] = "gpiozero"
            assert servo_state("de")["backend_note"].startswith("kein Servo-Treiber"), "servo page note"
            notes.append("servos")
        # 2. thermal camera: not found (maybe not built in) / found, but an error - never «USB cable» for the Thermal-90
        assert thermal_absent("senxor:0", "[Errno 121] Remote I/O error"), "nothing on I2C 0x40"
        assert thermal_absent("senxor:0", "[Errno 2] No such file or directory: '/dev/spidev0.0'"), "SPI off / nothing there"
        assert not thermal_absent("senxor:0", "Waveshare driver missing: Thermal_Camera_Hat.zip ..."), "driver = software"
        assert not thermal_absent("senxor:0", "MI48 reports a CRC error"), "found, but an error"
        assert not thermal_absent("sim:thermal", "simulator not reachable")
        if sys.platform.startswith("linux") and os.path.isdir("/dev"):
            assert thermal_absent("usb:63", "no picture from /dev/video63") == (not os.path.exists("/dev/video63"))
        CFG["thermal_source"] = "senxor:0"
        STATE["thermal"] = THERMAL_NOT_FOUND + "[Errno 121] Remote I/O error"
        it = _varsw_item("thermal")
        assert it["level"] == "warn" and it.get("kind") == "not_found" and "USB" not in it["tip"] and "maybe not built in" in it["text"], it
        assert "nicht eingebaut" in _varsw_item("thermal", "de")["text"]
        STATE["thermal"] = "no picture: MI48 reports a CRC error"
        it = _varsw_item("thermal")
        assert it["level"] == "warn" and not it.get("kind") and "USB" not in it["tip"] and "Found" in it["tip"], it
        STATE["thermal"] = "no picture: Waveshare driver missing: Thermal_Camera_Hat.zip"
        assert "pysenxor" in _varsw_item("thermal")["tip"]
        CFG["thermal_source"] = "usb:1"; STATE["thermal"] = "connection lost - reconnecting"
        assert "USB" in _varsw_item("thermal")["tip"], "a USB thermal camera keeps the USB tip"
        # 3. «Relay 1»: off from the factory; old settings only when never changed, once
        assert default_relays()[0]["mode"] == "off" and default_relays()[0]["gpio"] == GPIO_RELAY
        assert DEFAULTS.get("relay1_off_done") is True
        RELAYS[:] = [dict(RELAY1_OLD_DEFAULT)]
        assert relay1_migrate({"lang": "de"}) and RELAYS[0]["mode"] == "off", "never changed -> off"
        RELAYS[:] = [dict(RELAY1_OLD_DEFAULT, hold=10.0)]
        assert not relay1_migrate({}) and RELAYS[0]["mode"] == "auto", "changed by hand -> stays"
        RELAYS[:] = [dict(RELAY1_OLD_DEFAULT), dict(RELAY1_OLD_DEFAULT, name="Relay 2", gpio=23)]
        assert not relay1_migrate({}) and RELAYS[0]["mode"] == "auto", "two relays -> stays"
        RELAYS[:] = [dict(RELAY1_OLD_DEFAULT)]
        assert not relay1_migrate({"relay1_off_done": True}) and RELAYS[0]["mode"] == "auto", "already migrated (or new) -> stays"
        # 4. mover: own drive is not «device moved», moving it by hand is
        hits = []
        g = TamperGuard.__new__(TamperGuard)
        g.base = [0.0, 0.0, 1.0]; g.armed_was = True; g.n_tilt = 0; g.own_drive = False; g.cool = 0.0
        g.alarm = lambda what, looked=None: hits.append(what)
        globals()["is_armed"] = lambda: True
        CFG["tamper_tilt"] = 12.0
        tilt = lambda deg: [math.sin(math.radians(deg)), 0.0, math.cos(math.radians(deg))]
        MOVER.update(l=0.5, r=0.5, move_t=time.time())
        for _ in range(5):
            g.check_motion(tilt(30)); g.check_motion([0.0, 0.3, 1.4])      # slope and bumps while driving
        assert hits == [] and g.own_drive, f"own drive counted: {hits}"
        MOVER.update(l=0.0, r=0.0, move_t=time.time() - 1.0)
        assert mover_own_motion(), "quiet time after the stop"
        g.check_motion(tilt(30)); g.check_motion(tilt(30))
        assert hits == [], "within 3 s after the stop"
        MOVER.update(move_t=time.time() - MOVER_QUIET_S - 1.0)
        assert not mover_own_motion()
        g.check_motion(tilt(30))                                        # quiet time over: learns the new resting position
        assert hits == [] and not g.own_drive and abs(g.base[0] - math.sin(math.radians(30))) < 1e-6, "new resting position"
        g.check_motion(tilt(60)); g.check_motion(tilt(60))              # somebody lifts it (no drive command)
        assert hits == ["moved"], f"moved by hand must be reported: {hits}"
        hits.clear(); g.base = [0.0, 0.0, 1.0]
        MOVER.update(l=0.4, r=-0.4, move_t=time.time())
        for _ in range(4):
            g.check_motion(tilt(95))                                    # falls over while driving
        assert hits == ["knocked"], f"falling over while driving: {hits}"
        notes += ["thermal", "relay 1", "mover"]
    finally:
        globals()["is_armed"] = keep_armed
        STATE.update(keep_state); CFG.update(keep_cfg); RELAYS[:] = keep_relays
        MOVER.clear(); MOVER.update(keep_mover)
    for k in _HX_VARSW:
        for L in ("fr", "it", "rm"):
            assert TRX[L].get(k), f"{L}: {k[:40]}"
        assert DE.get(k), k[:40]
    return ", ".join(notes) + ", 5 languages"


SELFTEST_EXTRA.append(("Variants without all parts: servo fallback, thermal not found, relay 1 off, mover own drive (639zs)",
                       varianten_sw_selftest))
