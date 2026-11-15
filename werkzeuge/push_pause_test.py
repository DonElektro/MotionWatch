#!/usr/bin/env python3
"""Test «Mitteilungen pausieren» (MoveEye Teil 639zzzzp) – ohne echtes Netz, ohne Hardware, nur mit Temp-Ordnern.

  Teil A (im eigenen Prozess, gebaute Datei geladen, urlopen ersetzt):
    Halten      Pause an: Person / Voralarm / Wärme / Geräusch / Hinweis werden zurückgehalten und gezählt;
                Sabotage, SOS, «Akku fast leer», «Akku leer», Test kommen durch
    Ende        Zeit abgelaufen -> kurze Nachricht «Mitteilungen wieder an» mit «Während der Pause: 3 Alarme …»
    Knopf       ntfy: Live · Fehlalarm · «🔕 1 h pausieren» (statt Sirene), höchstens 3; Sabotage unverändert; Telegram: eigene
                Zeile, die anderen Knöpfe bleiben; Knopf -> Pause 1 h «Push-Knopf» + leise Bestätigung mit «Pause beenden»;
                «Pause beenden» -> Ende-Nachricht; jeder Knopf nur einmal
    Zeiten      bis morgen früh (Weckzeit / 07:00), eigene Zeit, höchstens 24 h, verlängern, «bis ich zurück bin» (Anwesenheit
                weg -> da = Ende; ohne Anwesenheit nicht wählbar)
    Rechte      Administrator = alle; Nutzer mit Alarm-Pushes = nur sein Thema; Kind ohne Alarm-Pushes darf nicht
    Neustart    der Zustand steht in der Einstellungsdatei und wird wieder geladen
    Sprachen    Knopf, Texte und «Abstand zwischen Alarmen» in 5 Sprachen; Protokoll mit Name und Weg
  Teil C (Pi-Fenster, Tkinter-Ersatz – nur Rauchtest): Block unter «Wann», Auswahl, Hinweis ohne Anwesenheit, laufende Pause mit
    «Pause beenden», Statuszeile.
  Teil B (echter Prozess, lokaler Schein-ntfy-Server): MoveEye startet mit einer laufenden Pause aus der Einstellungsdatei,
    /api/pushpause zeigt sie, die Seiten tragen das Glocken-Menü, nach Ablauf kommt «Mitteilungen wieder an» beim Schein-Server.

  python3 werkzeuge/push_pause_test.py [--datei X.py] [--nur a|b]
"""
import argparse
import base64
import glob
import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
PASSWORT = "Pausetest-" + base64.b16encode(os.urandom(5)).decode().lower()


def ok(cond, was):
    print(("  ok    " if cond else "  FEHLER ") + was)
    if not cond:
        FEHLER.append(was)


def dec(v):
    v = str(v or "")
    m = re.fullmatch(r"=\?UTF-8\?B\?([A-Za-z0-9+/=]+)\?=", v)
    return base64.b64decode(m.group(1)).decode() if m else v


def teil_a(datei, tmp):
    print("Teil A (im Prozess)")
    home = os.path.join(tmp, "a")
    os.makedirs(home)
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_push_pause_test", "__file__": datei}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    C = ns["CFG"]
    import urllib.request as ur
    BASE = "http://moveeye.example:5000"
    C.update(lang="de", push_actions=True, msg_icons=True, msg_keyword_on=False, sim_on=False, push_home_pics=False, notify_on=True,
             main_push_on=True, notify_type="ntfy", notify_url="http://127.0.0.1:9/fake-thema", public_url=BASE, webpush_on=False,
             sms_on=False, email_on=False, pushover_on=False, wake_on=True, wake_time="06:30", presence_hosts=[], presence_macs=[],
             presence_bt=[], users=[], push_pause={}, push_pause_users={})
    logs = []
    log0 = ns["log_event"]
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
        sent.append((req.full_url, {k.lower(): dec(v) for k, v in req.header_items()}, req.data or b""))
        return R()
    ur.urlopen = fake_open
    n = ns["Notifier"]()

    class W:
        notifier = n
    ns["WATCH_REF"]["w"] = W()
    # the messages of the pause go out in a thread: run them at once
    class T:
        def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None):
            self.f, self.a, self.k = target, args, kwargs or {}
        def start(self):
            self.f(*self.a, **self.k)
    import types
    ns["threading"] = types.SimpleNamespace(**{k: getattr(threading, k) for k in dir(threading) if not k.startswith("__")})
    ns["threading"].Thread = T
    ns["PP"]["started"] = True                                # no clock thread here: pp_tick() is called by hand

    def P(ev, **kw):
        return dict({"event": ev, "persons": 1 if ev == "person" else 0, "time": "2026-11-15T22:10:00", "snapshot": None, "rain": False,
                     "wind": "", "source": "cam", "link": BASE + "/recordings", "text": "Kamera verdeckt" if ev == "tamper" else "",
                     "info_title": ("{name}: " + ns["tr"]("TAMPER ALARM")) if ev == "tamper" else ""}, **kw)

    def ntfy_sent():
        return [s for s in sent if "fake-thema" in s[0]]

    def go(p):
        del sent[:]
        n._dispatch(p, None, "")
        return ntfy_sent()

    tr, trf = ns["tr"], ns["trf"]
    print(" Halten")
    ok(go(P("person")), "ohne Pause: Personen-Alarm geht hinaus")
    okk, err, s = ns["pp_start"]("", "60", who="admin", via="bell")
    ok(okk and ns["pp_active"](""), "Pause 1 h läuft")
    for ev in ("person", "prealarm", "warm", "noise"):
        ok(not go(P(ev)), "%s: zurückgehalten" % ev)
    ok(not go(P("info", info_title="{name}: Update", text="Neue Version")), "Hinweis (Update): zurückgehalten")
    ok(bool(go(P("tamper"))), "Sabotage kommt durch")
    ok(bool(go(P("info", info_title="{name}: 🆘 SOS", text=trf("The SOS lamp was started by {who}", who="Gast")))), "SOS kommt durch")
    ok(bool(go(P("info", info_title="{name}: " + tr("battery"),
                 text=trf("Battery almost empty: about {pct} % ({hours:.1f} h) left – please charge or swap", pct=9, hours=0.4)))), "«Akku fast leer» kommt durch")
    ok(bool(go(P("info", info_title="{name}: " + tr("power"), text=tr("Battery empty – the Pi shuts down cleanly")))), "«Akku leer» kommt durch")
    ok(bool(go(P("test"))), "Test kommt durch")
    st = ns["pp_raw"]("")
    ok(st["held"] == 4 and st["held_info"] == 1, "gezählt: 4 Alarme, 1 Hinweis (%s / %s)" % (st["held"], st["held_info"]))
    ok(any("paused until" in x and "by admin (bell)" in x for x in logs), "Protokoll: wer, wie lange, über die Glocke")
    info = ns["push_info"]()
    ok("🔕 pausiert bis" in info["status_line"] and info["pause"]["on"], "Statuszeile: «%s»" % info["status_line"])
    ok(info["pause"]["held_line"] == "Bisher zurückgehalten: 4 Alarme · 1 Hinweis", "«%s»" % info["pause"]["held_line"])

    print(" Neustart")
    sf = ns["SETTINGS_FILE"]
    ns["save_settings_now"]()                               # (save_settings waits up to 15 s)
    try:
        disk = json.load(open(sf, encoding="utf-8"))["cfg"].get("push_pause") or {}
    except (OSError, ValueError, KeyError):
        disk = {}
    ok(abs(float(disk.get("until") or 0) - st["until"]) < 1, "in der Einstellungsdatei (%s)" % os.path.basename(sf))
    C["push_pause"] = {}
    ns["apply_settings"]({"cfg": {"push_pause": disk}})
    C["notify_type"] = "ntfy"                                 # (the migration of a file without notify_type: webhook)
    ok(bool(ns["pp_active"]("")), "nach dem Laden wieder aktiv")

    print(" Ende")
    s2 = ns["pp_raw"]("")
    s2["until"] = time.time() - 1
    C["push_pause"] = s2
    del sent[:]
    ns["pp_tick"]()
    m = ntfy_sent()
    ok(not ns["pp_active"]("") and not C["push_pause"], "abgelaufen: Pause weg")
    ok(len(m) == 1 and m[0][1].get("title", "") == "🔔 Mitteilungen wieder an" and "Während der Pause: 4 Alarme · 1 Hinweis (im Verlauf)" in m[0][2].decode(),
       "Ende-Nachricht: %s / %s" % (m and m[0][1].get("title"), m and m[0][2].decode()[:80]))
    ok(m and m[0][1].get("click", "") == BASE + "/recordings", "Ende-Nachricht öffnet den Verlauf")
    ok(any("on again (time is up)" in x for x in logs), "Protokoll: wieder an")

    print(" Knopf in der Push-Nachricht")
    def acts(p):
        return [x.strip() for x in ns["alx_ntfy_actions"](p).split(";") if x.strip()]
    pp = P("person")
    a = acts(pp)
    labs = [x.split(",")[1].strip() for x in a]
    ok(labs == ["📷 Live öffnen", "Fehlalarm", "🔕 1 h pausieren"], "ntfy Person: %s" % labs)
    ok(len(a) <= 3 and a[2].startswith("http,") and a[2].split(",")[2].strip().endswith("/pause") and "method=POST" in a[2], "Pause = http POST (%s)" % a[2:])
    for ev in ("prealarm", "warm", "noise"):
        ok([x.split(",")[1].strip() for x in acts(P(ev))][-1] == "🔕 1 h pausieren", "%s: Pause-Knopf" % ev)
    ok([x.split(",")[1].strip() for x in acts(P("tamper"))] == ["📷 Live öffnen", "Fehlalarm", "Aus"], "Sabotage: unverändert")
    ok(not acts(P("info", text="x")), "Hinweis: keine Knöpfe")
    mk = ns["alx_telegram_markup"](P("person"))
    rows = [[b["text"] for b in r] for r in mk["inline_keyboard"]]
    ok(rows == [["📷 Live öffnen"], ["Fehlalarm", "Sirene", "Aus"], ["🔕 1 h pausieren"]], "Telegram: %s" % rows)
    C["push_actions"] = False
    ok(not ns["alx_ntfy_actions"](P("person")), "Schalter «Knöpfe» aus: kein Pause-Knopf")
    C["push_actions"] = True
    tok = pp["alx_tok"]
    good, err, e = ns["alx_use"](tok, "pause")
    del sent[:]
    done, txt = ns["alx_do"]("pause", e, "push button")
    st = ns["pp_active"]("")
    ok(done and st and 3590 < st["until"] - time.time() <= 3600 and st["via"] == "push" and st["by"] == "push button", "Knopf: Pause 1 h (%s)" % txt)
    ok(any("by push button (push)" in x for x in logs), "Protokoll: «push button»")
    m = ntfy_sent()
    ok(len(m) == 1 and m[0][1].get("title", "") == "🔕 Mitteilungen pausiert" and m[0][1].get("priority") == "default"
       and m[0][2].decode().startswith("Bis " + time.strftime("%H:%M", time.localtime(st["until"]))), "leise Bestätigung: %s / %s" % (m and m[0][1].get("title"), m and m[0][2].decode()[:60]))
    ra = [x.strip() for x in (m[0][1].get("actions", "") if m else "").split(";") if x.strip()]
    ok(len(ra) == 1 and "Pause beenden" in ra[0] and ra[0].split(",")[2].strip().endswith("/resume"), "Bestätigung: Knopf «Pause beenden» (%s)" % ra)
    ok(ns["alx_use"](tok, "pause")[1] == "used", "der Pause-Knopf geht nur einmal")
    rt = ra[0].split(",")[2].strip().split("/")[-2] if ra else ""
    good, err, e = ns["alx_use"](rt, "resume")
    del sent[:]
    done, txt = ns["alx_do"]("resume", e, "push button") if good else (False, err)
    m = ntfy_sent()
    ok(done and not ns["pp_active"]("") and m and "Mitteilungen wieder an" in m[0][1].get("title", ""), "«Pause beenden» aus der Nachricht (%s)" % txt)

    print(" Zeiten")
    okk, err, s = ns["pp_start"]("", "morning", via="page")
    ok(okk and time.strftime("%H:%M", time.localtime(s["until"])) == "06:30" and s["until"] - time.time() <= 86400, "bis morgen früh = Weckzeit 06:30")
    C["wake_on"] = False
    okk, err, s = ns["pp_start"]("", "morning", via="page")
    ok(time.strftime("%H:%M", time.localtime(s["until"])) == "07:00", "ohne Wecker: 07:00")
    okk, err, s = ns["pp_start"]("", "own", via="page", value="90")
    ok(okk and abs(s["until"] - time.time() - 5400) < 3, "eigene Zeit 90 min")
    ok(not ns["pp_start"]("", "own", via="page", value="30 h")[0], "eigene Zeit über 24 h: nein")
    okk, err, s2 = ns["pp_extend"]("", add_min=15, via="page")
    ok(okk and abs(s2["until"] - s["until"] - 900) < 2, "verlängern +15 min")
    ns["pp_end"]("", "ended", via="page", push=False)
    okk, err, _s = ns["pp_start"]("", "home", via="bell")
    ok(not okk and err == "The presence detection is not set up.", "bis ich zurück bin: ohne Anwesenheit nicht wählbar")
    I = ns["pp_info"]("")
    ok(I["presence"]["ready"] is False and I["presence"]["text"] == "nicht eingerichtet", "Info: Anwesenheit fehlt")
    C["presence_hosts"] = ["handy.local"]
    home_now = {"v": True}
    ns["presence_home"] = lambda: home_now["v"]
    okk, err, s = ns["pp_start"]("", "home", via="bell")
    ok(okk and abs(s["until"] - time.time() - 86400) < 3 and not s["away"], "bis ich zurück bin: höchstens 24 h, Handy noch da")
    ns["pp_tick"]()
    ok(bool(ns["pp_active"]("")), "Handy noch da: Pause bleibt")
    home_now["v"] = False
    ns["pp_tick"]()
    ok(ns["pp_raw"]("")["away"], "Handy weg: gemerkt")
    home_now["v"] = True
    del sent[:]
    ns["pp_tick"]()
    ok(not ns["pp_active"]("") and ntfy_sent(), "Handy zurück: Pause zu Ende, Nachricht")
    ok(any("back home" in x for x in logs), "Protokoll: back home")

    print(" Rechte und Nutzer")
    C["users"] = [{"name": "Anna", "role": "family", "push": ["alarm", "info"], "ntfy": "anna-thema-123"},
                  {"name": "Ben", "role": "family", "push": ["alarm", "info"], "ntfy": "ben-thema-456"},
                  {"name": "Kid", "role": "kid", "push": ["games"], "ntfy": "kid-thema-789"}]
    out, code = ns["pp_api"]({"action": "pause", "mode": "15"}, "kid", "Kid")
    ok(code == 403, "Kind ohne Alarm-Pushes darf nicht (%s)" % code)
    g, c2 = ns["pp_api"]({}, "kid", "Kid", "GET")
    ok(c2 == 200 and g["can"] is False, "Kind: GET sagt «darf nicht»")
    out, code = ns["pp_api"]({"action": "pause", "mode": "30", "via": "bell"}, "family", "anna")
    ok(code == 200 and out["scope"] == "user" and ns["pp_active"]("Anna") and not ns["pp_active"](""), "Nutzerin pausiert nur ihr eigenes")
    del sent[:]
    n._dispatch(P("person"), None, "")
    urls = [s[0] for s in sent]
    ok(any("ben-thema" in u for u in urls) and not any("anna-thema" in u for u in urls) and any("fake-thema" in u for u in urls),
       "Alarm: Ben und der Administrator ja, Anna nein")
    del sent[:]
    n._dispatch(P("tamper"), None, "")
    ok(any("anna-thema" in s[0] for s in sent), "Sabotage kommt auch bei Anna")
    ok(ns["pp_raw"]("Anna")["held"] == 1, "Anna: 1 Alarm gezählt")
    out, code = ns["pp_api"]({"action": "end", "via": "bell"}, "family", "Anna")
    ok(code == 200 and not ns["pp_active"]("Anna"), "Anna beendet ihre Pause")
    ok(any("anna-thema" in s[0] and "wieder an" in s[1].get("title", "") for s in sent), "Anna bekommt die Ende-Nachricht")
    out, code = ns["pp_api"]({"action": "pause", "mode": "120", "via": "page"}, "admin", "")
    ok(code == 200 and out["scope"] == "all" and out["on"] and out.get("short") in ("2 h 00", "1 h 59"), "Administrator: alle (%s)" % out.get("short"))
    ns["pp_end"]("", "ended", push=False)
    ok(ns["role_allows"]("view", "/api/pushpause", "GET", {}) and ns["role_allows"]("kid", "/api/pushpause", "POST", {}), "Adresse für alle Angemeldeten (Recht prüft die Adresse)")

    print(" Sprachen")
    for L, pause, gap in (("de", "🔕 1 h pausieren", "Abstand zwischen Alarmen (s)"), ("en", "🔕 Pause 1 h", "Gap between alarms (s)"),
                          ("fr", "🔕 Pause 1 h", "Écart entre les alarmes (s)"), ("it", "🔕 Pausa 1 h", "Intervallo tra gli allarmi (s)"),
                          ("rm", "🔕 Pausa 1 h", "Distanza tranter alarms (s)")):
        C["lang"] = L
        lab = [x.split(",")[1].strip() for x in acts(P("person"))][-1]
        lbl = next(x[2] for x in ns["SLIDERS"] if x[1] == "notify_cooldown")
        ok(lab == pause and tr(lbl) == gap, "%s: %s · %s" % (L, lab, tr(lbl)))
        tx = ns["pp_tx"](L)
        ok(all(tx.values()) and (L in ("de", "en") or tx["Pause notifications"] != "Pause notifications"), "%s: Texte des Menüs" % L)
    C["lang"] = "de"
    ok("pp-pop" in ns["ALERT_JS"] and "#pp-push" not in ns["ALERT_JS"] and 'getElementById("pp-push")' in ns["ALERT_JS"], "Glocken-Menü im Skript jeder Seite")
    ok(ns["HELP_PAGE"].count('id="pp-help"') == 2, "Anleitung DE / EN")
    print(" Selbsttest")
    try:
        ok(bool(ns["push_pause_selftest"]()), "push_pause_selftest")
    except AssertionError as e:
        ok(False, "push_pause_selftest: %s" % e)
    ns["log_event"] = log0


class Fake(http.server.BaseHTTPRequestHandler):
    got = []

    def _any(self):
        n = int(self.headers.get("Content-Length") or 0)
        Fake.got.append((self.path, {k.lower(): dec(v) for k, v in self.headers.items()}, self.rfile.read(n)))
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b'{"id":"x"}')
    do_POST = do_PUT = _any

    def log_message(self, *a):
        pass


def teil_b(datei, tmp):
    print("Teil B (echter Prozess, Schein-ntfy)")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    fport = srv.server_address[1]
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    home = os.path.join(tmp, "b")
    cfg = os.path.join(home, "mw")
    os.makedirs(cfg)
    ende = time.time() + 45
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True,
          "https_extra": False, "notify_on": True, "notify_type": "ntfy", "main_push_on": True, "notify_url": "http://127.0.0.1:%d/fake-thema" % fport,
          "notify_network": False, "notify_remote": False,
          "push_pause": {"until": ende, "t0": time.time() - 600, "mode": "min", "via": "bell", "by": "admin", "held": 3, "held_info": 0, "away": False}}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(home, "mw.log"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg, "--web-password", PASSWORT],
                         stdout=logf, stderr=subprocess.STDOUT, cwd=home, env=dict(os.environ, MOTIONWATCH_HOME=home))
    base = "http://127.0.0.1:%d" % port
    auth = "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode()

    def get(path):
        r = urllib.request.Request(base + path, headers={"Authorization": auth})
        with urllib.request.urlopen(r, timeout=10) as x:
            return x.read().decode("utf-8", "replace")
    try:
        for _i in range(240):
            if p.poll() is not None:
                ok(False, "MoveEye beendet:\n" + open(os.path.join(home, "mw.log")).read()[-2000:]); return
            try:
                get("/manifest.webmanifest"); break
            except Exception:
                time.sleep(1)
        if time.time() > ende - 3:
            ok(False, "Start dauerte zu lange (Pause schon vorbei) – Rechner sehr langsam?")
        else:
            d = json.loads(get("/api/pushpause?lang=de&tx=1"))
            ok(d.get("on") and d.get("can") and d.get("held") == 3 and d["tx"].get("Pause notifications") == "Mitteilungen pausieren",
               "nach dem Start: Pause aus der Einstellungsdatei läuft (%s)" % d.get("line"))
        html = get("/")
        ok('getElementById("pp-push")' in html and "pp-pop" in html, "Live-Seite: Glocken-Menü im Kopf-Skript")
        ok('pp.id = "pp-push"' in get("/protect"), "Schutz-Seite: Platz unter «Wann» (531a)")
        for _i in range(90):
            if any("wieder an" in g[1].get("title", "") for g in Fake.got):
                break
            time.sleep(1)
        m = [g for g in Fake.got if "wieder an" in g[1].get("title", "")]
        ok(bool(m) and m[0][0] == "/fake-thema" and "3 Alarme" in m[0][2].decode("utf-8", "replace"),
           "nach Ablauf beim Schein-ntfy: %s" % str(m and (m[0][1].get("title"), m[0][2].decode()[:60])))
        d = json.loads(get("/api/pushpause?lang=de"))
        ok(not d.get("on"), "danach: keine Pause")
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        srv.shutdown()


TK_TEXTE = []


def tk_ersatz():
    """a stand-in for tkinter / PIL (this computer has no Tkinter): every widget takes everything, the texts are recorded"""
    import types

    class W:
        def __init__(self, *a, **k):
            if "text" in k:
                TK_TEXTE.append(str(k["text"]))
            self._d = {}

        def __getattr__(self, n):
            if n.startswith("__"):
                raise AttributeError(n)
            w = W()
            self.__dict__[n] = w                       # the same object again (app.vars, app.status_labels …)
            return w

        def __getitem__(self, k):
            return self._d.get(k, W())

        def __setitem__(self, k, v):
            self._d[k] = v

        def __call__(self, *a, **k):
            if "text" in k:                            # .config(text=…)
                TK_TEXTE.append(str(k["text"]))
            return W()

        def __iter__(self):
            return iter(())

        def __bool__(self):
            return True

    def mod(name):
        m = types.ModuleType(name)
        m.__getattr__ = lambda n: W
        return m
    for n in ("tkinter", "tkinter.ttk", "tkinter.messagebox", "tkinter.simpledialog", "tkinter.font", "tkinter.filedialog", "PIL", "PIL.Image", "PIL.ImageTk"):
        sys.modules[n] = mod(n)
    sys.modules["tkinter"].ttk = sys.modules["tkinter.ttk"]
    sys.modules["tkinter"].messagebox = sys.modules["tkinter.messagebox"]
    sys.modules["tkinter"].simpledialog = sys.modules["tkinter.simpledialog"]
    sys.modules["PIL"].Image = sys.modules["PIL.Image"]
    sys.modules["PIL"].ImageTk = sys.modules["PIL.ImageTk"]
    return W


def teil_c_intern(datei, tmp):
    W = tk_ersatz()
    os.environ["MOTIONWATCH_HOME"] = tmp
    ns = {"__name__": "mw_push_pause_tk", "__file__": datei}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["PP"]["started"] = True
    C = ns["CFG"]
    C.update(lang="de", push_pause={}, presence_hosts=[], presence_macs=[], presence_bt=[], wake_on=False)
    ns["save_settings"] = lambda: None
    app = W()
    ns["_px_tk_panel"](app, W())
    ok(isinstance(getattr(app, "_d", None), dict) and "box" in (getattr(app, "_pp", None) or {}), "Fenster: Block «Mitteilungen pausieren» unter «Wann» gebaut")
    ok("🔕 Mitteilungen pausieren" in TK_TEXTE and "🌅 Bis morgen früh  (07:00)" in TK_TEXTE and "⏱ Eigene Zeit …" in TK_TEXTE, "Fenster: Auswahl da")
    ok(any(t.startswith("🏠 Bis ich zurück bin") for t in TK_TEXTE) and "Dafür zuerst dein Handy unter Zeit & Anwesenheit eintragen" in TK_TEXTE,
       "Fenster: ohne Anwesenheit mit Hinweis")
    del TK_TEXTE[:]
    ns["pp_start"]("", "30", via="window")
    ns["_px_tk_paint"](app)
    ok("🔔 Pause beenden" in TK_TEXTE and any(t.startswith("bis ") and "noch 30 min" in t for t in TK_TEXTE), "Fenster: laufende Pause mit «Pause beenden» (%s)"
       % [t for t in TK_TEXTE if t.startswith("bis ")][:1])
    ok(any("🔕 pausiert bis" in t for t in TK_TEXTE), "Fenster: Statuszeile zeigt die Pause")
    ok(ns["pp_raw"]("")["via"] == "window", "Fenster: Weg «window» gemerkt")


def teil_c(datei, tmp):
    print("Teil C (Pi-Fenster mit Tkinter-Ersatz, nur Rauchtest)")
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--datei", datei, "--intern-c", os.path.join(tmp, "c")],
                       capture_output=True, text=True, timeout=600)
    out = r.stdout + r.stderr
    for line in out.splitlines():
        if line.startswith(("  ok", "  FEHLER")):
            print(line)
    ok(r.returncode == 0 and "  ok" in out, "Teil C lief durch" + ("" if r.returncode == 0 else ":\n" + out[-1500:]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--nur", choices=("a", "b", "c"), default="")
    ap.add_argument("--intern-c", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                              key=lambda f: [int(x) for x in re.findall(r"\d+", os.path.basename(f))])[-1])
    if a.intern_c:
        os.makedirs(a.intern_c, exist_ok=True)
        teil_c_intern(datei, a.intern_c)
        return 1 if FEHLER else 0
    print("Datei:", os.path.basename(datei))
    tmp = tempfile.mkdtemp(prefix="mw_pause_")
    try:
        if a.nur in ("", "b"):
            teil_b(datei, tmp)                         # first: part A changes the environment of this process
        if a.nur in ("", "c"):
            teil_c(datei, tmp)
        if a.nur in ("", "a"):
            teil_a(datei, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("ALLES OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
