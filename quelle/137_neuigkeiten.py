#@ MoveEye – Teil 137: «Neu in dieser Version» – kurze Info nach jedem Update (Webseite und Fenster). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.3 (Wunsch Besitzer, während dem grossen Makeover): nach jedem Update erscheint am PC einmal eine kurze Info - was neu ist
# (aus der Änderungsliste am Dateianfang, alle Versionen seit der zuletzt gesehenen) und was als Nächstes kommt
# (MAKEOVER_NEXT, wird bei jeder Makeover-Version nachgeführt). Web und Fenster merken sich getrennt, was gesehen wurde
# (news_seen_web / news_seen_tk). Abschaltbar mit «news_popup».
# ----------------------------------------------------------------------------
# the makeover list (Besitzer, 28.10.2026): number, title - what is still to come (done ones are taken out)
MAKEOVER_ALL = [
    (1, "Ein gemeinsames Erscheinungsbild (Web, Fenster, Simulator)"), (2, "Simulations-Modus sichtbar (oranger Streifen «SIMULATION»)"),
    (3, "Startseite mit Simulator-Kachel"), (4, "Kachel-Steuerung des Simulators auf dem Handy"), (5, "Kino-Modus (Vollbild für TV / Beamer)"),
    (6, "Einheitliche Ereignis-Symbole"), (7, "Simulator-Zentrale in MoveEye"), (8, "«Was wäre wenn …?» bei echten Alarmen"),
    (9, "Dein Platz (Ort, Winkel, Zonen, Patrouille)"), (10, "Zonen im Simulator sehen"), (11, "Erkennung live in der 3D-Ansicht"),
    (12, "Automatische Trainings-Nacht"), (13, "Einstellungs-Vergleich A/B"), (14, "Benachrichtigungen testen (Test-Kanal)"),
    (15, "Akku-, Wetter- und WLAN-Ausfall üben"), (16, "Mehrere MoveEye-Geräte im Simulator"), (17, "Mover voll integriert"),
    (18, "Tagebuch-Statistik aus dem Simulator"), (19, "Versionen vergleichen (Kurve)"), (20, "Ein-Klick-Demo"),
    (21, "Fehlalarm-Lernen"), (22, "Karte der blinden Flecken"), (23, "Nacht-Generalprobe vor dem Einschalten des Schutzes"),
    (24, "Schwellen automatisch einstellen"), (25, "Erkennungs-Check jede Woche"),
]
MAKEOVER_DONE = set(range(1, 26))                                # numbers already delivered (nachführen)


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


# ---- Links zu Neuerungen (Wunsch Besitzer, 01.11.2026) ------------------------------------------------------------------------
# Bei jeder Neuerung ein kleiner Link, der direkt zur Funktion springt. Die Ziele stehen für beide Programme in
# simulator3d/ui_gemeinsam.json «neu_ziele» (Version -> {seite, anker, einstellung, sim_einstellung, sim_menue, sim_aktion}).
# Schalter «Links zu Neuerungen» (news_links auto | on | off, Entwickler-Bereich, Teil 639zc, mit dem Simulator geteilt);
# «auto» folgt dem Projektschalter «projekt_veroeffentlicht» (ui_gemeinsam.json): false = an, true = aus.
def news_links_on():
    v = str(CFG.get("news_links") or "auto")
    if v in ("on", "off"):
        return v == "on"
    return not bool((globals().get("UI_GEMEINSAM") or {}).get("projekt_veroeffentlicht"))


def news_target(v):
    z = ((globals().get("UI_GEMEINSAM") or {}).get("neu_ziele") or {}).get(str(v))
    return z if isinstance(z, dict) else None


def news_href(z):
    """the page of MoveEye for a target ('' = none): /settings?setting=K (open and mark a setting), ?open=grp:x / sec:x, #anchor"""
    if not isinstance(z, dict):
        return ""
    page, a, k = str(z.get("seite") or ""), str(z.get("anker") or ""), str(z.get("einstellung") or "")
    if not (page or a or k):
        return ""
    if not page.startswith("/"):
        page = "/settings" if (a or k) else "/"
    from urllib.parse import quote
    if k:
        return page + "?setting=" + quote(k)
    if a.startswith(("grp:", "sec:")):
        return page + "?open=" + quote(a)
    return page + ("#" + quote(a) if a else "")


def news_hint(k, lang=None):
    h = ((globals().get("UI_GEMEINSAM") or {}).get("hint") or {}).get(k) or {}
    L = lang or cur_lang()
    return str(h.get(L) or h.get("en") or h.get("de") or k)


def news_link_item(it, lang=None):
    """an item {v, t} + «href» (a link in MoveEye) or «where»: «sim» (only in the simulator)"""
    z = news_target(it.get("v")) if news_links_on() else None
    if z:
        h = news_href(z)
        if h:
            it["href"] = h
        elif any(z.get(x) for x in ("sim_einstellung", "sim_menue", "sim_aktion")):
            it["where"] = "sim"
    return it


def news_state(who="web", lang=None):
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
    items = [news_link_item(x, lang) for x in items]
    return {"version": cur, "show": bool(items) and bool(CFG.get("news_popup", True)), "items": items, "next": news_next(),
            "fresh": not seen,                               # 639zzs: never seen any = a new device - the browser shows no news then
            "done": len(MAKEOVER_DONE), "total": len(MAKEOVER_ALL), "links": news_links_on(),
            "lt": {"go": news_hint("neu_link", lang), "sim": news_hint("neu_in_sim", lang)}}


def news_seen(who="web"):
    CFG["news_seen_" + who] = APP_VERSION
    save_settings()
