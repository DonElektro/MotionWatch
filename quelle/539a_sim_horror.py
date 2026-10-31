#@ MoveEye – Teil 539a: Bergtal · Horror-Modus des 3D-Simulators – seine «Aufnahmen» kommen in den Verlauf (Nachrichten, als Test). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (31.10.2026): der Horror-Modus «Das Hospiz» des 3D-Simulators (simulator3d/scripts/bergtal_horror.gd) wird
# über seltsame MoveEye-Aufnahmen erzählt, die man am Morgen in MoveEyes Verlauf findet. Der Simulator schickt die neuen
# Aufnahmen in world_reply «horror» (Liste: id, t, night, time, title, text - schon in der Sprache des Simulators), das Bild
# (links Kamerabild, rechts Wärmebild) holt MoveEye über /horror_pic/<id>.jpg. Jede Aufnahme wird ein Eintrag im Verlauf →
# Nachrichten (msglog_add, Status «test», Ort «Simulator · Horror») - NIE ein echter Push, kein Alarm-Licht, keine Sirene.
# Alte Aufnahmen von vor der Verbindung zählen nicht (wie shut_feed, 539).
# ----------------------------------------------------------------------------

HORROR = {"seen": 0, "n": 0}


def horror_feed(lst, first=False):
    """world_reply «horror» of the simulator: new recordings -> the message list (Verlauf), as test, never a real push"""
    if not isinstance(lst, list):
        return
    for it in lst[-6:]:
        if not isinstance(it, dict):
            continue
        try:
            id_ = int(it.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if id_ <= HORROR["seen"]:
            continue
        HORROR["seen"] = id_
        if not first:
            threading.Thread(target=horror_rec, args=(dict(it),), daemon=True, name="simhorror").start()


def horror_rec(it):
    jpg = None
    try:
        jpg, _h = _sim_get(f"/horror_pic/{int(it.get('id') or 0)}.jpg", 3.0)
        if not jpg or jpg[:2] != b"\xff\xd8":
            jpg = None
    except Exception:
        jpg = None
    title = ("[SIM] " if CFG.get("sim_on") else "") + "🎞 " + str(it.get("title") or "")[:120]
    text = (str(it.get("time") or "")[:5] + " · " + str(it.get("text") or "")).strip(" ·")[:500]
    try:
        msglog_add(title, text, "alarm", jpg, "test", "Simulator · Horror")
    except Exception as e:
        log_event("sim", f"Horror mode: message list failed: {e}"[:160])
        return
    HORROR["n"] += 1
    log_event("sim", f"Horror mode: recording {int(it.get('id') or 0)} (night {int(it.get('night') or 0)}) put into the message list")
