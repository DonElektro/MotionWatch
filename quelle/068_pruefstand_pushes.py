#@ MoveEye – Teil 068: Prüfstand – die letzten Push-Nachrichten für den 3D-Simulator (er zählt echte Pushes statt Flackern). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# nach 2.98.17 (Wunsch Daniel, Prüfstand 2): der Prüfstand zählt nicht mehr jedes Aufflackern der Personen-Erkennung als Fehlalarm,
# sondern die Push-Nachrichten, die MoveEye wirklich verschickt (im Test-Postfach der Simulation). Der Simulator bekommt dafür
# mit jedem Zustand (290, «det») die letzten paar Nachrichten der Liste «Nachrichten» (065): Kennung, Zeit, Art – ohne Text,
# ohne Bild, ohne Adresse. Er ordnet jede neue Nachricht dem Besucher zu, der in dem Moment sichtbar war (testrun.gd).
# ----------------------------------------------------------------------------


def msglog_recent(n=4):
    """the newest n messages as [id, time, kind, status] (for the simulator / test bench) - cheap, from the cached list"""
    try:
        with MSGLOG["lock"]:
            items = list(_msglog_load()[-n:])
        return [[str(x.get("id", "")), round(float(x.get("t", 0.0)), 2), str(x.get("ev", "")), str(x.get("status", ""))] for x in items]
    except Exception:
        return []
