#@ MoveEye – Teil 639zzzzb: Knopf «📷 Live öffnen» in den Alarm-, Personen- und Bewegungs-Pushes (ntfy, Telegram, Pushover, Web-Push) – damit er auch auf der Apple Watch steht (gespiegelte iOS-Mitteilungen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (14.11.2026): auf Alarm- / Personen- / Bewegungs-Pushes ein Knopf «📷 Live öffnen», der den Reiter Live
# von MoveEye öffnet (Adresse «/» = main_tab_page("live"), Teil 550).
#   * Adresse: dieselbe Basis wie der Tipp-Link und die Knöpfe «Fehlalarm / Sirene / Aus» (alx_base, Teil 066 = «Adresse dieser
#     Seite für Links», lokal / Tailscale – wie der Besitzer sie eingetragen hat). Ohne diese Adresse: kein Knopf (wie bisher die
#     anderen Knöpfe). Nur Schema, Host, Port und Pfad – Benutzer / Passwort, «?…» und «#…» der eingetragenen Adresse fallen weg
#     (Hülle um alx_base, gilt so auch für die anderen Knöpfe): nie ein Passwort, App-Schlüssel, Token oder PIN in der Adresse.
#     Der Live-Reiter verlangt wie immer das Anmelden.
#   * Welche Pushes: person, prealarm (Bewegung), warm, noise, tamper (Sabotage / Diebstahl / Sensor-Alarm) und test (damit der
#     Besitzer es ohne Alarm ausprobieren kann). Infos (Update, Online, Bericht, Fehlalarm-Stelle …) bleiben, wie sie sind.
#   * Schalter: «push_actions» (Knöpfe in der Push-Nachricht, Teil 066) gilt auch für diesen Knopf.
#   * ntfy (Header «Actions»): «view»-Knopf als ERSTER (die Uhr zeigt die Knöpfe in dieser Reihenfolge). ntfy erlaubt höchstens 3
#     Knöpfe: bei «Fehlalarm · Sirene · Aus» fällt dort «Aus» weg (öffnete ohnehin nur die Seite mit dem PIN-Feld; Ausschalten geht
#     im Live-Reiter). Telegram: eigene erste Zeile, die anderen Knöpfe bleiben alle. Pushover: der eine Link der Nachricht
#     (url / url_title) wird «📷 Live öffnen» – ausser bei einer Karte (Diebstahl) oder «Bilder bleiben zu Hause» (Bild-Link).
#     Web-Push: Aktion «live» (Service Worker, Teil 510) auf «/» der eigenen Seite. Eigene ntfy-Themen der Benutzer: unverändert.
#   * Nichts davon schreibt etwas ins Protokoll (das ntfy-Thema nie).
# Test: werkzeuge/push_live_test.py, Selbsttest push_live_selftest.
# ----------------------------------------------------------------------------
PUSH_LIVE_EV = ("person", "prealarm", "warm", "noise", "tamper", "test")

_HX_PLIVE = {
    "📷 Open Live": ("📷 Live öffnen", "📷 Ouvrir Live", "📷 Apri Live", "📷 Avrir Live"),
}
for _k, _v in _HX_PLIVE.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def push_live_kind(ev):
    return str(ev or "") in PUSH_LIVE_EV and bool(CFG.get("push_actions", True))


def push_live_label(lang=None):
    return tr("📷 Open Live", lang)


_plive_base_before = alx_base


# wraps: alx_base
def alx_base():
    """+ 639zzzzb: only scheme, host, port and path of the address - never user / password, «?…» or «#…» in a push link"""
    base = _plive_base_before()
    if not base:
        return ""
    try:
        from urllib.parse import urlsplit, urlunsplit
        u = urlsplit(base)
        host, port = u.hostname or "", u.port
    except ValueError:
        return ""
    if not host or u.scheme not in ("http", "https"):
        return ""
    return urlunsplit((u.scheme, ("[" + host + "]" if ":" in host else host) + (":%d" % port if port else ""), u.path.rstrip("/"), "", ""))


def push_live_url(p):
    """the Live tab for an alarm / motion push ('' for infos or without the address of the page)"""
    if not isinstance(p, dict) or p.get("fs_tok") or not push_live_kind(p.get("event")):
        return ""
    base = alx_base()
    return base + "/" if base else ""


_plive_ntfy_before = alx_ntfy_actions


# wraps: alx_ntfy_actions (after 639zy)
def alx_ntfy_actions(p):
    acts = _plive_ntfy_before(p)
    url = push_live_url(p)
    if not url:
        return acts
    rest = [a.strip() for a in str(acts or "").split(";") if a.strip()]
    if len(rest) > 2:                                    # ntfy: at most 3 buttons - «Off» goes first (the Live tab can switch off)
        rest = [a for a in rest if not a.split(",")[2].strip().endswith("/off")] if all(a.count(",") >= 2 for a in rest) else rest
        rest = rest[:2]
    lab = " ".join(push_live_label().replace(",", " ").replace(";", " ").split())
    return "; ".join(["view, " + lab + ", " + url] + rest)


_plive_tg_before = alx_telegram_markup


# wraps: alx_telegram_markup (after 639zy)
def alx_telegram_markup(p):
    mk = _plive_tg_before(p)
    url = push_live_url(p)
    if not url:
        return mk
    return {"inline_keyboard": [[{"text": push_live_label(), "url": url}]] + list((mk or {}).get("inline_keyboard") or [])}


def push_live_selftest():
    keep = {k: CFG.get(k) for k in ("public_url", "push_actions", "lang")}
    try:
        CFG.update(public_url="https://besitzer:geheim@moveeye.example:8443/x/?key=APPKEY#pin=4711", push_actions=True, lang="de")
        for ev in PUSH_LIVE_EV:
            assert push_live_url({"event": ev}) == "https://moveeye.example:8443/x/", ev
        assert alx_base() == "https://moveeye.example:8443/x" and "@" not in alx_ntfy_actions({"event": "tamper"})
        assert push_live_url({"event": "info"}) == "" and push_live_url({"event": "person", "fs_tok": "t"}) == ""
        CFG["public_url"] = "http://192.168.1.20:5000"
        assert push_live_url({"event": "person"}) == "http://192.168.1.20:5000/"
        a = alx_ntfy_actions({"event": "test"})
        assert a == "view, 📷 Live öffnen, http://192.168.1.20:5000/", a
        assert alx_ntfy_actions({"event": "info", "time": "2026-11-14T22:00:00"}) == "", "info unchanged"
        tg = alx_telegram_markup({"event": "test"})
        assert tg["inline_keyboard"][0] == [{"text": "📷 Live öffnen", "url": "http://192.168.1.20:5000/"}], tg
        CFG["push_actions"] = False
        assert push_live_url({"event": "person"}) == "" and not push_live_kind("person")
        CFG.update(push_actions=True, public_url="")
        assert push_live_url({"event": "person"}) == "" and push_live_kind("noise") and not push_live_kind("info")
        for L, want in (("de", "Live öffnen"), ("en", "Open Live"), ("fr", "Ouvrir Live"), ("it", "Apri Live"), ("rm", "Avrir Live")):
            assert push_live_label(L) == "📷 " + want, (L, push_live_label(L))
        assert 'e.action === "live"' in SW_JS
    finally:
        CFG.update(keep)
    return "Live link only for alarms / motion / test, without user / query, ntfy first button, Telegram row, 5 languages"


SELFTEST_EXTRA.append(("Push button «📷 Live öffnen» (639zzzzb)", push_live_selftest))
