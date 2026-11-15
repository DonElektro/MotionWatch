#!/usr/bin/env python3
"""Test Push-Knopf «📷 Live öffnen» (MoveEye Teil 639zzzzb) – ohne Netz (urlopen / webpush_send ersetzt), ohne Hardware.

  Im eigenen Prozess (gebaute Datei geladen): für jede Art Push die gebaute Nachricht prüfen
    ntfy        Header «Actions»: erster Knopf «view, 📷 Live öffnen, <Basis>/», höchstens 3 Knöpfe (bei Alarmen fällt «Aus» weg),
                Infos (Update, Online, Fehlalarm-Stelle) unverändert, Schalter «Knöpfe in der Push-Nachricht» aus = kein Knopf
    Telegram    erste Zeile der Link-Knöpfe;  Pushover  url / url_title (Karte und «Bilder bleiben zu Hause» gehen vor)
    Web-Push    Aktion «live» auf «/»;  Service Worker kennt die Aktion
    Basis       = «Adresse dieser Seite für Links», ohne Benutzer / Passwort / ?… / #…;  ohne Adresse kein Knopf
    Geheimnisse Web-Passwort, PINs, Tokens, App-Schlüssel, Pushover-Schlüssel und das ntfy-Thema stehen in keinem Header / Körper,
                das ntfy-Thema in keiner Protokoll-Zeile;  5 Sprachen;  Selbsttest push_live_selftest

  python3 werkzeuge/push_live_test.py [--datei X.py]
"""
import argparse
import base64
import glob
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []


def ok(cond, was):
    print(("  ok    " if cond else "  FEHLER ") + was)
    if not cond:
        FEHLER.append(was)


def dec(v):
    v = str(v or "")
    m = re.fullmatch(r"=\?UTF-8\?B\?([A-Za-z0-9+/=]+)\?=", v)
    return base64.b64decode(m.group(1)).decode() if m else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                              key=lambda f: [int(x) for x in re.findall(r"\d+", os.path.basename(f))])[-1])
    print("Datei:", os.path.basename(datei))
    ns = {"__name__": "mw_push_live_test", "__file__": datei}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    C = ns["CFG"]
    import urllib.request as ur

    TOPIC = "mw-geheimes-thema-7f3a9c"
    SECRETS = {"web_password": "PW-geheim-81x", "protect_pin": "947213", "lock_pin": "582036", "telegram_token": "123456:TG-geheim-Q",
               "pushover_token": "POtokenGeheim77", "pushover_user": "POuserGeheim55", "shortcut_token": "SC-geheim-tok",
               "guest_token": "GUEST-geheim-tok", "ext_token": "EXT-geheim-tok", "email_password": "MAIL-geheim-pw"}
    APPKEY = "APPKEY-geheim-0815"
    for k, v in SECRETS.items():
        if k in C and not isinstance(C[k], str):
            continue
        C[k] = v
    C.update(lang="de", push_actions=True, msg_icons=True, msg_keyword_on=False, sim_on=False, push_home_pics=False,
             notify_type="ntfy", notify_url="https://ntfy.example.invalid/" + TOPIC, telegram_chat="42",
             public_url="https://besitzer:%s@moveeye.example:8443/?key=%s#pin=%s" % (SECRETS["web_password"], APPKEY, SECRETS["protect_pin"]))
    BASE = "https://moveeye.example:8443/"
    LIVE = "📷 Live öffnen"
    logs = []
    ns["log_event"] = lambda kind, msg, *x, **k: logs.append(str(msg))
    sent = []

    class R:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *x):
            return False
        def read(self, *x):
            return b"{}"

    def fake_open(req, timeout=None):
        sent.append((req.full_url, {k.lower(): v for k, v in req.header_items()}, req.data or b""))
        return R()
    ur.urlopen = fake_open
    n = ns["Notifier"].__new__(ns["Notifier"])

    def P(ev, **kw):
        return dict({"event": ev, "persons": 1 if ev == "person" else 0, "time": "2026-11-14T22:10:00", "snapshot": None, "rain": False,
                     "wind": "", "source": "cam", "link": BASE + "recordings", "text": "Kamera verdeckt" if ev == "tamper" else "",
                     "info_title": "{name}: " + ns["tr"]("TAMPER ALARM") if ev == "tamper" else ""}, **kw)

    def ntfy(p):
        del sent[:]
        code, where = n._send_main(p, None, "")
        h = sent[-1][1]
        acts = [x.strip() for x in dec(h.get("actions", "")).split(";") if x.strip()]
        return acts, h, sent[-1][2], where

    allsent = []
    print("ntfy")
    for ev in ("person", "prealarm", "warm", "noise", "tamper", "test"):
        acts, h, body, where = ntfy(P(ev))
        allsent.append((h, body))
        ok(bool(acts) and acts[0] == "view, %s, %s" % (LIVE, BASE), "%s: erster Knopf «%s» auf %s (%s)" % (ev, LIVE, BASE, acts[:1]))
        ok(len(acts) <= 3, "%s: höchstens 3 Knöpfe (%d)" % (ev, len(acts)))
        ok(TOPIC not in where, "%s: Ziel im Protokoll ohne Thema (%s)" % (ev, where))
        if ev in ("person", "prealarm", "warm", "noise"):
            labs = [x.split(",")[1].strip() for x in acts]
            ok(labs == [LIVE, "Fehlalarm", "🔕 1 h pausieren"], "%s: Live · Fehlalarm · Pause (639zzzzp: statt Sirene) (%s)" % (ev, labs))
        if ev == "tamper":
            labs = [x.split(",")[1].strip() for x in acts]
            ok(labs == [LIVE, "Fehlalarm", "Aus"], "tamper: Live · Fehlalarm · Aus (%s)" % labs)
    for name, p in (("Info «Update»", dict(P("info"), info_title="{name}: Update", text="Neue Version 3.95.1")),
                    ("Info «Online»", dict(P("info"), info_title="", text="MoveEye is online (known Wi-Fi): http://192.168.1.20:5000")),
                    ("Fehlalarm-Stelle", dict(P("info"), fs_tok="x" * 24))):
        acts, h, body, _w = ntfy(p)
        ok(not any(LIVE in x for x in acts), "%s: kein Live-Knopf" % name)
    C["push_actions"] = False
    acts, _h, _b, _w = ntfy(P("person"))
    ok(not acts, "Schalter «Knöpfe in der Push-Nachricht» aus: keine Knöpfe")
    C["push_actions"] = True
    keep_pub = C["public_url"]
    C["public_url"] = ""
    acts, _h, _b, _w = ntfy(P("person"))
    ok(not any(LIVE in x for x in acts), "ohne Adresse der Seite: kein Live-Knopf")
    C["public_url"] = keep_pub

    print("Telegram")
    mk = ns["alx_telegram_markup"](P("person"))
    ok(mk and mk["inline_keyboard"][0] == [{"text": LIVE, "url": BASE}], "erste Zeile = %s (%s)" % (LIVE, mk and mk["inline_keyboard"][0]))
    ok(len(mk["inline_keyboard"]) == 3 and len(mk["inline_keyboard"][1]) == 3, "die drei anderen Knöpfe bleiben (+ Zeile «Pause», 639zzzzp)")
    ok(ns["alx_telegram_markup"](P("info")) is None, "Info: keine Knöpfe")
    allsent.append(({}, json.dumps(mk, ensure_ascii=False).encode()))

    print("Pushover")
    def po(p):
        del sent[:]
        n._pushover(p, None, "")
        raw = sent[-1][2].decode("utf-8", "replace")
        f = dict(re.findall(r'name="(\w+)"\r\n\r\n(.*?)\r\n', raw, re.S))
        return f, raw
    f, raw = po(P("person"))
    ok(f.get("url") == BASE and f.get("url_title") == LIVE, "Personen-Alarm: url / url_title (%s, %s)" % (f.get("url"), f.get("url_title")))
    f2, _r = po(P("info", link=BASE + "x"))
    ok(f2.get("url_title") == "MoveEye", "Info: Link wie bisher (%s)" % f2.get("url_title"))
    f3, _r = po(P("tamper", map="https://www.openstreetmap.org/?mlat=46.9&mlon=7.4"))
    ok("openstreetmap" in f3.get("url", ""), "Diebstahl mit Karte: die Karte bleibt der Link")
    f4, _r = po(P("person", home_id="0123456789abcdef", link=BASE + "pb/0123456789abcdef"))
    ok(f4.get("url", "").endswith("/pb/0123456789abcdef"), "«Bilder bleiben zu Hause»: der Bild-Link bleibt")
    # the Pushover form carries its own token / user (that is the API, not the link) - only the url fields count here
    allsent.append(({}, (f.get("url", "") + f.get("url_title", "")).encode()))

    print("Web-Push")
    wp = []
    ns.update(webpush_subs=lambda: [{"endpoint": "https://push.example.invalid/e", "p256dh": "x", "auth": "y"}],
              webpush_supported=lambda: True, push_sub_wants=lambda sb, cat: True,
              webpush_send=lambda sb, msg, ttl=86400, urgent=True: (wp.append(msg), 201)[1], _webpush_save=lambda s: None)
    for ev in ("person", "prealarm", "test"):
        del wp[:]
        n._webpush(P(ev))
        m = wp[-1] if wp else {}
        ok(m.get("actions") == [{"action": "live", "title": LIVE}] and m.get("live") == "/", "%s: Aktion «live» auf «/» (%s)" % (ev, m.get("actions")))
        allsent.append(({}, json.dumps(m, ensure_ascii=False).encode()))
    del wp[:]
    n._webpush(P("info"))
    ok(wp and "actions" not in wp[-1], "Info: keine Aktion")
    sw = ns["SW_JS"]
    ok('e.action === "live"' in sw and "actions:" in sw, "Service Worker: Aktion «live» öffnet dt.live")

    print("Geheimnisse")
    leak = []
    for h, body in allsent:
        blob = json.dumps(h, ensure_ascii=False) + body.decode("utf-8", "replace")
        blob = blob + dec(h.get("actions", "")) + dec(h.get("title", "")) + dec(h.get("message", ""))
        for s in list(SECRETS.values()) + [APPKEY, TOPIC, "besitzer"]:
            if s in blob:
                leak.append(s)
    ok(not leak, "kein Passwort / PIN / Token / App-Schlüssel / Thema in den Nachrichten (%s)" % sorted(set(leak)))
    ok(not any(TOPIC in x for x in logs), "das ntfy-Thema in keiner Protokoll-Zeile (%d Zeilen)" % len(logs))

    print("Sprachen")
    for L, want in (("de", "📷 Live öffnen"), ("en", "📷 Open Live"), ("fr", "📷 Ouvrir Live"), ("it", "📷 Apri Live"), ("rm", "📷 Avrir Live")):
        C["lang"] = L
        acts, _h, _b, _w = ntfy(P("test"))
        ok(acts and acts[0].split(",")[1].strip() == want, "%s: %s" % (L, acts[:1]))
    C["lang"] = "de"

    print("Selbsttest")
    try:
        ok(bool(ns["push_live_selftest"]()), "push_live_selftest")
    except AssertionError as e:
        ok(False, "push_live_selftest: %s" % e)

    print("\n%s" % ("ALLES OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
