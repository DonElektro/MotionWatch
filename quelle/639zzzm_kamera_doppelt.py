#@ MoveEye – Teil 639zzzm: ein Sensor = ein Eintrag – nach Simulator aus kommt genau die Kamera-Liste von vorher zurück, keine zweite «Pi camera 0», Selbstheilung beim Start (Texte und Selbsttest; die Logik steht in 440, 340, 410, 210, 318). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Fehler des Besitzers (MoveEye 3.92.0, echter Pi 5, 14.11.2026): Simulator verbunden, dann getrennt. Danach unter
# Einstellungen → Kameras: Karte 1 = die Hauptkamera «Pi camera 0» rot «fehlgeschlagen Camera __init__ sequence did not
# complete.», Karte 2 = ein neuer Eintrag «Pi camera 0» grün mit Bild. Beide wollten denselben Sensor (libcamera öffnet ihn
# nur einmal), der neue gewann, die Hauptkamera versuchte es ewig.
# Ursachen (werkzeuge/sim_kamera_zurueck_test.py mit einem falschen picamera2, das jede Nummer nur einmal öffnet):
#   1. 410: die Hauptkamera startete einen zweiten Öffnungs-Versuch, während das Ergebnis des ersten (Kamera offen) noch auf
#      die Schleife wartete; der zweite scheiterte am eigenen Sensor und ERSETZTE das Ergebnis - die offene Pi-Kamera ging
#      verloren, ohne geschlossen zu werden, und hielt den Sensor bis zum Neustart (rot, «sequence did not complete»).
#   2. 440: Zusatzkameras zählten nur den Namen der Quelle: im Simulator ist die Hauptkamera «sim:0», die Auswahl bot die echte
#      «Pi camera 0» als Zusatzkamera an (und nahm sie an); ebenso «usb:<interner Knoten>» (= die Pi-Kamera, 2.98.24) und
#      «auto». Nach dem Simulator wollten dann Haupt- und Zusatzkamera denselben Sensor.
#   3. 340: Simulator aus filterte nur «sim:» aus der Liste, statt die Liste von vorher zurückzulegen; die Zusatzkameras starteten
#      gleichzeitig mit der Hauptkamera (die Simulator-Kameras wurden im Hintergrund geschlossen).
# Korrektur:
#   * 340 sim_set: beim Einschalten die echten Zusatzkameras merken (sim_prev_cams), beim Ausschalten genau diese Liste in
#     derselben Reihenfolge zurück; erst die Simulator-Kameras schliessen (cams_apply(wait)), dann die Hauptkamera öffnen.
#     Eine echte Kamera, die im Simulator dazukommt oder entfernt wird, ändert die gemerkte Liste mit (440).
#   * 440: cam_sensor / cam_main_sensors - gezählt wird der Sensor; die Hauptkamera hat Vorrang (im Simulator gehört ihr der
#     Sensor der echten Hauptkamera, die zurückkommt). cams_add lehnt einen zweiten Eintrag auf einem Sensor ab, cams_apply
#     startet keinen. «auto» (210) nimmt zuerst eine Pi-Kamera, die keine Zusatzkamera hat.
#   * 410: kein zweiter Öffnungs-Versuch, solange ein Ergebnis wartet; ein späteres Ergebnis ersetzt nie eine offene Kamera.
#   * Selbstheilung (440 cams_dedupe, beim Start vor der Hauptkamera, nach Simulator aus, wenn die Hauptkamera den Sensor
#     braucht): zwei Einträge auf einem Sensor -> die Hauptkamera bzw. der ältere Eintrag bleibt. Der spätere wird nur ENTFERNT,
#     wenn er keine eigenen Einstellungen hat (Rolle «Übersicht» kopf_ov, «sitzt auf dem Kopf» cam_head, eigener Blickwinkel
#     cam_fov) = ein automatisch entstandenes Doppel; sonst nur AUSGESCHALTET (extra_cams_off, Karte «aus: derselbe Sensor wie
#     eine andere Kamera», ✕ entfernt sie, wird der Sensor frei, läuft sie von selbst wieder). Eine Zeile im Protokoll.
# ----------------------------------------------------------------------------
_HX_KAMDOPP = {   # English (key): Deutsch, Français, Italiano, Rumantsch
    CAMS_OFF_STATUS: ("aus: derselbe Sensor wie eine andere Kamera", "désactivée : même capteur qu’une autre caméra",
                      "spenta: stesso sensore di un’altra telecamera", "deactivada: il medem sensur sco ina autra camera"),
}
for _k, _v in _HX_KAMDOPP.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])



# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def kamdopp_selftest():
    keys = ("source", "extra_cams", "extra_cams_off", "sim_on", "sim_prev_source", "sim_prev_cams", "kopf_ov", "cam_head", "cam_fov")
    keep = ({k: CFG.get(k) for k in keys}, dict(STATE), dict(_PIC_C), globals()["save_settings"], globals()["log_event"],
            os.environ.get("MW_TEST_V4L"), dict(KW))
    logs = []
    try:
        globals()["save_settings"] = lambda *a, **k: None
        globals()["log_event"] = lambda kind, msg, *a, **k: logs.append(msg)
        os.environ["MW_TEST_V4L"] = ""; KW["usb"] = ([], 0.0)
        _PIC_C.update(t=time.time() + 3600, v=[0])           # one Pi camera (no picamera2 needed)
        STATE.update(source_id="", source_label="", source_status="connecting…")
        CFG.update(sim_on=False, source="auto", extra_cams=["pi:0", "url:x1"], extra_cams_off=[], kopf_ov="", cam_head={}, cam_fov={},
                   sim_prev_cams={})
        assert cam_sensor("pi:0") == "pi:0" and cam_sensor("url:x1") == "url:x1" and cam_sensor("auto") == ""
        assert cam_auto_sensor() == "pi:0" and cam_main_sensors() == {"pi:0"}, "auto = the only Pi camera (main camera first)"
        assert cams_dedupe("selftest") == 1 and CFG["extra_cams"] == ["url:x1"] and CFG["extra_cams_off"] == []
        assert len(logs) == 1 and logs[0].startswith("Duplicate camera") and "removed" in logs[0], logs
        assert cams_dedupe("selftest") == 0 and len(logs) == 1, "nothing twice"
        # with own settings (a role): only switched off, the card says so
        CFG.update(source="pi:0", extra_cams=["url:x1", "pi:0"], kopf_ov="pi:0")
        assert cams_dedupe("selftest") == 1 and CFG["extra_cams"] == ["url:x1", "pi:0"] and CFG["extra_cams_off"] == ["pi:0"]
        assert "switched off" in logs[-1] and cams_on() == ["url:x1"]
        st = cams_status()
        assert st[-1]["id"] == "pi:0" and st[-1]["status"] == CAMS_OFF_STATUS and st[-1]["n"] >= 100, st[-1]
        assert tr(CAMS_OFF_STATUS, "de").startswith("aus:") and CAMS_OFF_STATUS in CAMS_PAGE
        # the sensor is free again (the main camera is another one now): on again by itself
        CFG.update(source="url:x9")
        assert cams_dedupe("selftest") == 1 and CFG["extra_cams_off"] == [] and "on again" in logs[-1]
        # simulation: the real Pi camera belongs to the real main camera that comes back - never an extra camera
        CFG.update(source="sim:0", sim_on=True, sim_prev_source="pi:0", extra_cams=["url:x1", "sim:1"], kopf_ov="",
                   sim_prev_cams={"cams": ["url:x1"], "off": []})
        STATE.update(source_id="sim:0")
        assert "pi:0" in cam_main_sensors()
        ok, err = cams_add("pi:0")
        assert not ok and err == "this is the main camera already", (ok, err)
        assert CFG["extra_cams"] == ["url:x1", "sim:1"]
        for i, k in enumerate(_HX_KAMDOPP):
            assert len(_HX_KAMDOPP[k]) == 4 and all(_HX_KAMDOPP[k]) and "ß" not in "".join(_HX_KAMDOPP[k]), k
            assert k in TRX["fr"] and k in TRX["it"] and k in TRX["rm"], k
        return "sensor not name, main camera first, duplicate removed / switched off, sim keeps the real sensor, texts"
    finally:
        CFG.update(keep[0]); STATE.clear(); STATE.update(keep[1]); _PIC_C.clear(); _PIC_C.update(keep[2])
        globals()["save_settings"] = keep[3]; globals()["log_event"] = keep[4]
        if keep[5] is None:
            os.environ.pop("MW_TEST_V4L", None)
        else:
            os.environ["MW_TEST_V4L"] = keep[5]
        KW.clear(); KW.update(keep[6])


SELFTEST_EXTRA.append(("One sensor = one camera entry, the cameras after the simulation (639zzzm)", kamdopp_selftest))
