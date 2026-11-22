#@ MoveEye – Teil 639zzzzq: Simulator verbunden / getrennt ist kein Ereignis – keine Push «Stromausfall» / «Strom wieder da», 60 s Ruhe für Gerätemeldungen, Schalter «Während der Simulator verbunden ist: keine Push». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer 21.11.2026 (4.17.1): verbindet sich der Simulator, liefert er Akku- und Stromwerte (285 sim_sensor «battery»). Der
# Wechsel von den echten zu den simulierten Werten (und zurück) sah aus wie ein Stromausfall: Push «Stromausfall – Akku x %»,
# beim Trennen «Strom wieder da», mit Schutz an sogar TAMPER.alarm("power").
#   1. Wechsel der Quelle (echt <-> Simulator) ist nie ein Ereignis: 100 BatteryMonitor.tick merkt die Quelle; wechselt sie,
#      beginnt ups_events neu (kein «vorher») - nur eine Zeile im Protokoll, keine Push, kein Sabotage-Alarm.
#   2. 60 s nach dem Verbinden UND nach dem Trennen: Gerätemeldungen (Push «info»: Strom, Akku, WLAN, Sensoren, Wärmebild …)
#      nur ins Protokoll / die Nachrichten-Liste. Erkennungs-Alarme (Person, Tier, Vor-Alarm, Wärme, Geräusch) wie immer.
#   3. Schalter «Während der Simulator verbunden ist: keine Push» (sim_push_off, ab Werk aus, nur Administrator): an = keine
#      Push, solange der Simulator verbunden ist.
#   4. Nie zurückgehalten: Sabotage / Diebstahl / Sensor-Alarme (event «tamper») von echter Hardware und die SOS-Lampe. Nur
#      «Kamera abgedeckt / verdreht» aus dem Bild des Simulators zählt beim Schalter (3) als Simulator.
# Test: werkzeuge/sim_push_ruhe_test.py, Selbsttest sim_push_ruhe_selftest.
# ----------------------------------------------------------------------------
CFG.setdefault("sim_push_off", False); DEFAULTS.setdefault("sim_push_off", False)
USER_SETTINGS_DENY.update({"sim_push_off"})
SIMQ_S = 60.0                        # quiet time after the simulator connected or left
_sx_put_after(TOGGLES, "sim_autoupd", ("Simulator", "sim_push_off", "While the simulator is connected: no push"))
_HX_SIMQ = {"While the simulator is connected: no push": ("Während der Simulator verbunden ist: keine Push",
                                                          "Pendant que le simulateur est connecté : pas de push",
                                                          "Mentre il simulatore è collegato: nessun push",
                                                          "Durant che il simulatur è collià: nagins push")}
for _k, _v in _HX_SIMQ.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def simq_connected(now=None):
    now = time.time() if now is None else now
    return bool(CFG.get("sim_on") and SIM.get("ok") and now - float(SIM.get("t") or 0.0) < 5.0)


def simq_quiet(now=None):
    """the 60 s after the simulator connected or left (lost or switched off): '' or the reason"""
    now = time.time() if now is None else now
    if simq_connected(now):
        return "simulator just connected" if now - float(SIM.get("since") or 0.0) < SIMQ_S else ""
    return "simulator just left" if now - max(float(SIM.get("t") or 0.0), float(SIM.get("off_t") or 0.0)) < SIMQ_S + 5.0 else ""


def simq_hold(p, now=None):
    """'' = send, else why this push is held (only logged). Never held: sabotage / theft / sensor alarms of real hardware
    (only «camera covered / turned» from the picture of the simulator counts as simulator), the SOS lamp, tests"""
    if not isinstance(p, dict) or p.get("event") == "test" or p.get("_test") or "SOS" in str(p.get("info_title") or ""):
        return ""
    if p.get("event") == "tamper" and not (str(STATE.get("source_id") or "").startswith("sim:") and any(
            str(p.get("text") or "").startswith(tr(k)) for k in ("camera covered", "camera turned / picture changed"))):
        return ""
    if CFG.get("sim_push_off") and simq_connected(now):
        return "simulator connected, setting «no push»"
    q = simq_quiet(now) if p.get("event") == "info" else ""
    return q and q + ", device message"


_simq_dispatch_before = Notifier._dispatch


def _simq_dispatch(self, p, jpg, fname):
    """+ 639zzzzq: the simulator connected / left - device messages and (switch) all pushes only into the log"""
    why = simq_hold(p)
    if not why:
        return _simq_dispatch_before(self, p, jpg, fname)
    try:
        msglog_add(self._title(p), push_with_map(self._text(p), p, " · "), self._event(p), jpg, "none", "🎮 Simulator")
    except Exception:
        pass
    log_event("sys", f"No push ({why}): {self._title(p)}"[:200])


# wraps: Notifier._dispatch
Notifier._dispatch = _simq_dispatch


def sim_push_ruhe_selftest():
    keep_cfg = {k: CFG.get(k) for k in ("sim_on", "sim_push_off")}
    keep_sim = {k: SIM.get(k) for k in ("ok", "t", "since", "off_t")}
    keep_src = STATE.get("source_id")
    try:
        now = time.time()
        info = {"event": "info", "text": "Power cut", "info_title": "{name}: power"}
        CFG.update(sim_on=True, sim_push_off=False); SIM.update(ok=True, t=now, since=now - 10, off_t=0.0)
        assert simq_hold(info, now), "just connected: device message held"
        assert not simq_hold({"event": "person", "persons": 1}, now), "a person alarm still goes out"
        assert not simq_hold({"event": "tamper", "text": "device moved"}, now), "real sabotage never held"
        SIM.update(since=now - 300)
        assert not simq_hold(info, now), "after 60 s: device messages again"
        CFG["sim_push_off"] = True
        assert simq_hold({"event": "person", "persons": 1}, now), "switch on: nothing while connected"
        assert not simq_hold({"event": "info", "info_title": "{name}: 🆘 SOS"}, now), "SOS never held"
        STATE["source_id"] = "sim:0"
        assert simq_hold({"event": "tamper", "text": tr("camera covered")}, now), "switch on: camera alarm from the simulator picture held"
        CFG.update(sim_on=False, sim_push_off=False); SIM.update(ok=False, t=now - 20)
        assert simq_hold(info, now), "just left: device message held"
        SIM.update(t=now - 200)
        assert not simq_hold(info, now), "long gone: normal"
    finally:
        CFG.update(keep_cfg); SIM.update(keep_sim); STATE["source_id"] = keep_src
    return "simulator connected / left: device messages 60 s only in the log, alarms as always, switch «no push»"


SELFTEST_EXTRA.append(("Simulator connect is no power event (639zzzzq)", sim_push_ruhe_selftest))
