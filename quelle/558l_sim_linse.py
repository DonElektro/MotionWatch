#@ MoveEye – Teil 558l: «Linse verschmutzt» im Simulator-Betrieb – der 3D-Simulator meldet Tropfen und Beschlag auf seinen Linsen (world_reply «lens»), die Seite zeigt einen Hinweis mit Knopf «Linse putzen». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (09.11.2026, Sim 3.67.0): im Kamerabild des Simulators lagen viele Tropfen auf der Linse (wetter.gd /
# linse.gd), und MoveEye sagte nichts. Jetzt:
#   Simulator  world_reply «lens» = {head: {cover 0..1, fog 0..1, drops}, wide: {…}, dirty} (null: Tropfen-Physik aus) –
#              optional: ältere Simulatoren senden nichts, ältere MoveEye lesen es nicht (kein SIM_MIN / MW_MIN nötig).
#   MoveEye    350 SimLink.tick -> sim_lens_take() -> STATE["sim_lens"]; die Hauptseite zeigt bei «dirty» (und nur solange der
#              Simulator verbunden ist) einen gelben Chip «💧 Linse verschmutzt» in der Kopfzeile und unter der Simulator-Kachel
#              der Live-Seite «💧 Linse verschmutzt – im Simulator «Linse putzen»» mit dem Knopf «🧽 Linse putzen»
#              (/api/sim action lens_wipe -> /control {"action": "wetter", "do": "wipe"}, Simulator 3.67.1).
#   Die Prüfung der echten Linse (Teil 060/410 LENS: Schärfe 15 Minuten unter 35 %) bleibt, wie sie ist.
# Texte und die Zeilen der Seite (LENS_JS): Teil 639zl (nach den Übersetzungs-Tabellen; Deutsch / Französisch / Italienisch / Rätoromanisch).
# ----------------------------------------------------------------------------
STATE.setdefault("sim_lens", None)


def sim_lens_take(v):
    """world_reply «lens» des 3D-Simulators -> STATE["sim_lens"] (None: nichts gemeldet / Tropfen-Physik aus)"""
    if not isinstance(v, dict):
        STATE["sim_lens"] = None
        return None

    def one(x):
        x = x if isinstance(x, dict) else {}
        try:
            return {"cover": round(min(1.0, max(0.0, float(x.get("cover") or 0.0))), 3), "fog": round(min(1.0, max(0.0, float(x.get("fog") or 0.0))), 2),
                    "drops": max(0, int(x.get("drops") or 0))}
        except (TypeError, ValueError):
            return {"cover": 0.0, "fog": 0.0, "drops": 0}
    r = {"head": one(v.get("head")), "wide": one(v.get("wide")) if isinstance(v.get("wide"), dict) else None, "dirty": bool(v.get("dirty"))}
    was = bool((STATE.get("sim_lens") or {}).get("dirty"))
    STATE["sim_lens"] = r
    if r["dirty"] and not was:
        log_event("sys", f"Simulator: lens dirty (drops / fog, {int(round(r['head']['cover'] * 100))} % covered) - «Clean lens» in the simulator")
    return r


def sim_lens_wipe():
    """«Linse putzen» im Simulator (Knopf des Hinweises): (ok, Fehler)"""
    try:
        r = sim_control({"action": "wetter", "do": "wipe"})
    except Exception:
        return False, "simulator not reachable"
    if not isinstance(r, dict) or not r.get("ok"):
        return False, str((r or {}).get("error") or "not supported - update the simulator") if isinstance(r, dict) else "simulator not reachable"
    if isinstance(STATE.get("sim_lens"), dict):
        STATE["sim_lens"] = dict(STATE["sim_lens"], dirty=False)
    log_event("sys", "Simulator: lens cleaned")
    return True, ""


def sim_lens_selftest():
    saved = STATE.get("sim_lens")
    try:
        assert sim_lens_take(None) is None and STATE["sim_lens"] is None, "nothing reported must clear the hint"
        r = sim_lens_take({"head": {"cover": 0.12, "fog": 0.0, "drops": 40}, "wide": {"cover": 0.05, "fog": 0.1, "drops": 9}, "dirty": True})
        assert r["dirty"] and STATE["sim_lens"]["head"]["drops"] == 40 and abs(STATE["sim_lens"]["wide"]["fog"] - 0.1) < 1e-9
        r = sim_lens_take({"head": {"cover": "x", "drops": None}, "dirty": 0})
        assert r == {"head": {"cover": 0.0, "fog": 0.0, "drops": 0}, "wide": None, "dirty": False}, r
        r = sim_lens_take({"head": {"cover": 7, "fog": -1}, "dirty": "yes"})
        assert r["head"]["cover"] == 1.0 and r["head"]["fog"] == 0.0 and r["dirty"]
        import inspect
        assert 'rep_.get("lens")' in inspect.getsource(SimLink.tick), "350 SimLink.tick does not pass «lens» on"
        assert 'id = "b-lens"' in WEB_PAGE and "lens_wipe" in WEB_PAGE, "hint not in the main page"
        for k in _HX_LINSE:
            assert DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")), f"text not translated: {k}"
    finally:
        STATE["sim_lens"] = saved
    return "lens of the simulator: hint and «Clean lens» (558l)"


SELFTEST_EXTRA.append(("Simulator lens dirty -> hint «Clean lens» (558l)", sim_lens_selftest))
