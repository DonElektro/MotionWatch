#@ MoveEye – Teil 137: «Neu in dieser Version» – kurze Info nach jedem Update (Webseite und Fenster). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.3 (Wunsch Daniel, während dem grossen Makeover): nach jedem Update erscheint am PC einmal eine kurze Info - was neu ist
# (aus der Änderungsliste am Dateianfang, alle Versionen seit der zuletzt gesehenen) und was als Nächstes kommt
# (MAKEOVER_NEXT, wird bei jeder Makeover-Version nachgeführt). Web und Fenster merken sich getrennt, was gesehen wurde
# (news_seen_web / news_seen_tk). Abschaltbar mit «news_popup».
# ----------------------------------------------------------------------------
# the makeover list (Daniel, 28.10.2026): number, title - what is still to come (done ones are taken out)
MAKEOVER_ALL = [
    (1, "Ein gemeinsames Erscheinungsbild (Web, Fenster, Simulator)"), (2, "Simulations-Modus sichtbar (oranger Streifen «SIMULATION»)"),
    (3, "Startseite mit Simulator-Kachel"), (4, "Kachel-Steuerung des Simulators auf dem Handy"), (5, "Kino-Modus (Vollbild für TV / Beamer)"),
    (6, "Einheitliche Ereignis-Symbole"), (7, "Simulator-Zentrale in MoveEye"), (8, "«Was wäre wenn …?» bei echten Alarmen"),
    (9, "Zwilling deines Platzes (Ort, Winkel, Zonen, Patrouille)"), (10, "Zonen im Simulator sehen"), (11, "Erkennung live in der 3D-Ansicht"),
    (12, "Automatische Trainings-Nacht"), (13, "Einstellungs-Vergleich A/B"), (14, "Benachrichtigungen testen (Test-Kanal)"),
    (15, "Akku-, Wetter- und WLAN-Ausfall üben"), (16, "Mehrere MoveEye-Geräte im Simulator"), (17, "Rover voll integriert"),
    (18, "Tagebuch-Statistik aus dem Simulator"), (19, "Versionen vergleichen (Kurve)"), (20, "Ein-Klick-Demo"),
    (21, "Fehlalarm-Lernen"), (22, "Karte der blinden Flecken"), (23, "Nacht-Generalprobe vor dem Scharfschalten"),
    (24, "Schwellen automatisch einstellen"), (25, "Erkennungs-Check jede Woche"),
]
MAKEOVER_DONE = set()                                  # numbers already delivered (nachführen)


def _news_vt(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


def news_entries():
    """{version: text} from the list of changes at the top of the file"""
    out, cur = {}, None
    for ln in (globals().get("__doc__") or "").splitlines():
        m = re.match(r"^  \* (\d+\.\d+\.\d+): (.*)$", ln)
        if m:
            cur = m.group(1)
            out[cur] = m.group(2).strip()
        elif cur and ln.startswith("    ") and ln.strip():
            out[cur] += " " + ln.strip()
        elif not ln.strip():
            cur = None
    return out


def news_next(n=5):
    return [{"n": k, "t": t} for k, t in MAKEOVER_ALL if k not in MAKEOVER_DONE][:n]


def news_state(who="web"):
    seen = str(CFG.get("news_seen_" + who) or "")
    ent = news_entries()
    cur = APP_VERSION
    if seen == cur:
        items = []
    elif not seen:
        items = [{"v": cur, "t": ent.get(cur, "")}] if ent.get(cur) else []
    else:
        vs = sorted((v for v in ent if _news_vt(seen) < _news_vt(v) <= _news_vt(cur)), key=_news_vt, reverse=True)[:6]
        items = [{"v": v, "t": ent[v]} for v in vs]
    return {"version": cur, "show": bool(items) and bool(CFG.get("news_popup", True)), "items": items, "next": news_next(),
            "done": len(MAKEOVER_DONE), "total": len(MAKEOVER_ALL)}


def news_seen(who="web"):
    CFG["news_seen_" + who] = APP_VERSION
    save_settings()
