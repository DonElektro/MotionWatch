#!/usr/bin/env python3
"""Test «Rechte und Schutz» (Korrekturen der Prüfung vom 10.11.2026; Teile 040, 135, 130, 030, 550, 586, 639zzk).

Startet MoveEye ohne Fenster mit der Demo und einem Web-Passwort, legt die Benutzer «Kim» (Kind), «Anna» (Familie) und
«Cus» (eigene Rechte: keine) an und prüft über die echte Web-Schnittstelle:

  2   /api/factory und /api/factory/backup/<name> (alte Einstellungen mit Passwort-Hash): nur der Administrator.
      Die Rechte-Tabelle zählt genau: /api/fa bleibt offen, /api/audio/live braucht das Recht «live», /api/ui_simple bleibt.
  5   «Familie» (Recht «arm») bekommt /api/protect (Stand, Stufe wählen, «Schutz testen»); PIN / Eskalation nicht. Kind: 403.
  6   POST /api/tunnel (Fernzugriff ein, neuer Code) nur der Administrator; der Code ist für andere leer.
  4   Mit einer PIN: Modus «Transport», «Alle aus» (mehrere Geräte), Kurzbefehl /k/<key>/disarm und «Aus» verlangen die PIN
      (403 "need_pin", Schutz bleibt an), mit der richtigen PIN geht es (Kopfzeile X-MW-PIN, beim Kurzbefehl ?pin=).
      Ohne PIN alles wie bisher. Ein Zeitplan schaltet weiter ohne PIN aus. Der Administrator sperrt sich nicht aus.
      Mit --browser: die Seite fragt nach der PIN (Fenster wie bei «Aus») und schickt die Anfrage noch einmal.
  3   «Voll» schaltet Sirene + «Sirene nach 30 s» ein, «Wachsam» wieder aus – auch nach «Aus» und einfachem Einschalten.
      Eine selbst gewählte Sirene («Sirene bei Alarm» in den Lautsprecher-Einstellungen) bleibt.
  11  Ein / Aus steht sofort in der Einstellungsdatei. Von Hand aus während ein Zeitplan einschaltet: nach einem harten
      Neustart (kill -9) bleibt es aus.

  python3 werkzeuge/rechte_schutz_test.py [--datei X.py] [--browser]
"""
import argparse
import base64
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "Rechte-" + base64.b16encode(os.urandom(5)).decode().lower()
GEHEIM = "HashGeheim" + base64.b16encode(os.urandom(4)).decode().lower()      # steht in der «alten Einstellungsdatei»
PIN = "4711"
BENUTZER = {"Kim": "kid", "Anna": "family", "Cus": "custom"}
SICHERUNG = "motionwatch_settings.before_reset_20260101-000000.json"


class Geraet:
    def __init__(self, datei, port):
        self.datei, self.port = datei, port
        self.tmp = tempfile.mkdtemp(prefix="mw_rechte_")
        self.cfg = os.path.join(self.tmp, "mw"); os.makedirs(self.cfg)
        self.base = "http://127.0.0.1:%d" % port
        self.p = None
        self.logf = None
        self.op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
              "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
              "setup_done": True, "https_extra": False, "arm_delay": 0.0, "armed": False, "tunnel_on": False}
        self.kurz = "me_" + base64.b16encode(os.urandom(12)).decode().lower()      # an app key only for the shortcut addresses /k/…
        st["app_keys"] = [{"id": "a1b2c3d4", "name": "Kurzbefehl-Test", "h": hashlib.sha256(("mw-appkey|" + self.kurz).encode()).hexdigest(),
                           "t0": int(time.time()), "seen": 0, "ip": "", "scope": "shortcut"}]
        with open(self.datei_einst(), "w") as f:
            json.dump({"cfg": st}, f)

    def datei_einst(self):
        return os.path.join(self.cfg, "motionwatch_settings.json")

    def einst(self):
        with open(self.datei_einst()) as f:
            return json.load(f)["cfg"]

    def einst_aendern(self, fn):
        """die Einstellungsdatei von Hand ändern (nur wenn MoveEye nicht läuft); der Rest der Datei (Zeitpläne …) bleibt"""
        with open(self.datei_einst()) as f:
            d = json.load(f)
        fn(d["cfg"])
        with open(self.datei_einst(), "w") as f:
            json.dump(d, f)

    def start(self, demo=True):
        self.logf = open(os.path.join(self.tmp, "log.txt"), "a")
        self.p = subprocess.Popen([sys.executable, self.datei, "--headless"] + (["--demo"] if demo else []) + ["--port", str(self.port), "--bind", "127.0.0.1",
                                   "--config", self.cfg, "--web-password", PASSWORT], stdout=self.logf, stderr=subprocess.STDOUT, cwd=self.tmp)
        for _i in range(240):
            if self.p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + self.log()[-3000:])
            try:
                self.op.open(self.base + "/manifest.webmanifest", timeout=2); return
            except Exception:
                time.sleep(1)
        sys.exit("MoveEye antwortet nicht")

    def stop(self, hart=False):
        if self.p is None:
            return
        if hart:
            self.p.send_signal(signal.SIGKILL)               # wie Strom weg: nichts wird mehr gespeichert
        else:
            self.p.terminate()
        try:
            self.p.wait(15)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self.p = None
        self.logf.close()

    def log(self):
        txt = open(os.path.join(self.tmp, "log.txt"), errors="replace").read()
        return txt + "".join(open(x, errors="replace").read() for x in glob.glob(os.path.join(self.cfg, "**", "*.log"), recursive=True))

    def req(self, pfad, daten=None, wer="admin", pin=None, roh=False):
        """(Status, JSON oder Text). wer: «admin», ein Benutzername oder None (ohne Anmeldung)"""
        h = {}
        if wer:
            pw = PASSWORT if wer == "admin" else wer.lower() + "-pass-1"
            h["Authorization"] = "Basic " + base64.b64encode(("%s:%s" % (wer, pw)).encode()).decode()
        if pin is not None:
            h["X-MW-PIN"] = pin
        body = None
        if daten is not None:
            body = json.dumps(daten).encode(); h["Content-Type"] = "application/json"
        r = urllib.request.Request(self.base + pfad, data=body, headers=h)
        try:
            with self.op.open(r, timeout=20) as a:
                code, raw = a.status, a.read(2_000_000)
        except urllib.error.HTTPError as e:
            code, raw = e.code, e.read(200_000)
        if roh:
            return code, raw
        try:
            return code, json.loads(raw.decode("utf-8", "replace"))
        except ValueError:
            return code, raw.decode("utf-8", "replace")

    def schutz(self):
        return self.req("/api/protect")[1]

    def warte(self, was, s=15.0):
        ende = time.time() + s
        while time.time() < ende:
            if was():
                return True
            time.sleep(0.3)
        return bool(was())


def main():
    ap = argparse.ArgumentParser(description="Rechte und Schutz")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5141)
    ap.add_argument("--browser", action="store_true", help="dazu die PIN-Frage im Browser (Playwright)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    G = Geraet(datei, a.port)
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    try:
        with open(os.path.join(G.cfg, SICHERUNG), "w") as f:
            json.dump({"cfg": {"web_pw_hash": GEHEIM}}, f)
        G.start()
        for n, r in BENUTZER.items():
            c, j = G.req("/api/users", {"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
            pruef(c == 200 and j.get("ok"), "Benutzer %s (%s) angelegt" % (n, r))
        G.req("/api/users", {"action": "update", "name": "Cus", "perms": []})
        rechte(G, pruef)
        pin_ueberall(G, pruef)
        if a.browser:
            pin_im_browser(G, pruef)
        stufe_sirene(G, pruef)
        speichern_zeitplan(G, pruef)
        if G.p is not None and G.p.poll() is not None:
            fehler.append("MoveEye ist während des Tests abgestürzt")
    finally:
        G.stop()
        log = G.log()
        pruef(GEHEIM not in log and PASSWORT not in log, "Protokoll: kein Passwort, kein Inhalt der alten Einstellungen")
        if "Traceback (most recent call last)" in log:
            print(log[-3000:]); fehler.append("Traceback im Protokoll")
        shutil.rmtree(G.tmp, ignore_errors=True)
    print("Rechte-und-Schutz-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def rechte(G, pruef):
    print("== 2 / 5 / 6: Rechte", flush=True)
    c, raw = G.req("/api/factory/backup/" + SICHERUNG, roh=True)
    pruef(c == 200 and GEHEIM.encode() in raw, "Administrator: alte Einstellungen herunterladen (%d)" % c)
    c, j = G.req("/api/factory")
    pruef(c == 200 and "backups" in j, "Administrator: /api/factory mit der Liste der Kopien (%d)" % c)
    bk = [b for b in (j.get("backups") or []) if b.get("name") == SICHERUNG]      # 3.72: with the date fix of 586 the copy is really listed
    pruef(len(bk) == 1 and bk[0].get("when") == "01.01.2026 00:00" and bk[0].get("kb", 0) >= 1,
          "Administrator: die Kopie steht in der Liste, mit Datum (%s)" % (j.get("backups"),))
    c, raw = G.req("/api/factory/backup/" + SICHERUNG, wer=None, roh=True)
    pruef(c == 401 and GEHEIM.encode() not in raw, "ohne Anmeldung: 401 (%d)" % c)
    for n in BENUTZER:
        c, raw = G.req("/api/factory/backup/" + SICHERUNG, wer=n, roh=True)
        pruef(c == 403 and GEHEIM.encode() not in raw, "%s: /api/factory/backup/… = 403 (%d)" % (n, c))
        c, j = G.req("/api/factory", wer=n)
        pruef(c == 403 and "backups" not in j, "%s: /api/factory (Liste der Kopien) = 403 (%d)" % (n, c))
        c, _j = G.req("/api/factory", {"word": "x"}, wer=n)
        pruef(c == 403, "%s: Werkseinstellungen (POST) = 403 (%d)" % (n, c))
        for p in ("/api/fa", "/api/ui", "/api/ui_simple", "/api/ui_sync", "/api/state", "/api/audio", "/api/tunnel", "/sx/ui.js", "/i18n/fr.js"):
            c, _j = G.req(p, wer=n, roh=True)
            pruef(c == 200, "%s: %s bleibt offen (%d)" % (n, p, c))
        for p in ("/api/factoryx", "/api/statex", "/api/fax", "/api/settings/export", "/api/users"):
            c, _j = G.req(p, wer=n, roh=True)
            pruef(c in (403, 404) and c != 200, "%s: %s nicht offen (%d)" % (n, p, c))
        c, j = G.req("/api/tunnel", {"on": True}, wer=n)
        pruef(c == 403, "%s: Fernzugriff einschalten = 403 (%d)" % (n, c))
        c, j = G.req("/api/tunnel", {"new_code": True}, wer=n)
        pruef(c == 403, "%s: neuer Code für den Fernzugriff = 403 (%d)" % (n, c))
    pruef(G.req("/api/tunnel")[1]["tunnel"]["on"] is False and not G.einst().get("tunnel_on"), "Fernzugriff ist aus geblieben")
    c, _r = G.req("/api/audio/live", wer="Cus", roh=True)
    pruef(c == 403, "ohne Rechte: Live-Ton /api/audio/live = 403 (%d)" % c)
    c, _r = G.req("/api/audio/live", wer="Kim", roh=True)
    pruef(c != 403, "Kind (Recht «live»): Live-Ton erlaubt (%d, 404 = kein Mikrofon)" % c)
    c, j = G.req("/api/tunnel", {"on": True})
    pruef(c == 200 and j["tunnel"]["on"] and re.fullmatch(r"\d{6}", j["tunnel"]["code"] or ""), "Administrator: Fernzugriff ein, Code sichtbar")
    c, j = G.req("/api/tunnel", wer="Anna")
    pruef(c == 200 and j["tunnel"]["on"] and j["tunnel"]["code"] == "", "Familie: sieht «ein», aber nicht den Code")
    c, j = G.req("/api/state", wer="Anna")
    pruef(c == 200 and j["state"]["tunnel"]["code"] == "", "Familie: auch /api/state ohne Code")
    G.req("/api/tunnel", {"on": False})
    # 5: Familie und die Seite «Schutz»
    c, _r = G.req("/protect", wer="Anna", roh=True)
    c2, j = G.req("/api/protect", wer="Anna")
    pruef(c == 200 and c2 == 200 and j.get("level") in ("off", "watch", "full"), "Familie: Seite «Schutz» und ihr Stand (%d / %d)" % (c, c2))
    c, j = G.req("/api/protect", {"action": "level", "level": "watch", "lang": "de"}, wer="Anna")
    pruef(c == 200 and j.get("ok") and j.get("chosen") == "watch", "Familie: Stufe «Wachsam» wählen (%d)" % c)
    c, j = G.req("/api/protect", {"action": "level", "level": "off"}, wer="Anna")
    pruef(c == 200 and j.get("level") == "off", "Familie: «Aus» (ohne PIN) (%d)" % c)
    for akt in ({"action": "pin", "new": "1234"}, {"action": "escalate", "on": True}, {"action": "presence", "on": True}):
        c, j = G.req("/api/protect", akt, wer="Anna")
        pruef(c == 403, "Familie: %s = 403 (%d)" % (akt["action"], c))
    pruef(not G.schutz()["pin"] and not G.schutz()["escalate"]["on"], "PIN und Eskalation unverändert")
    for n in ("Kim", "Cus"):
        c, _j = G.req("/api/protect", wer=n)
        c2, _j = G.req("/api/protect", {"action": "level", "level": "off"}, wer=n)
        pruef(c == 403 and c2 == 403, "%s: /api/protect = 403 (%d / %d)" % (n, c, c2))


def an(G, wer="admin"):
    return G.req("/api/arm", {"action": "arm_now"}, wer=wer)


def pin_ueberall(G, pruef):
    print("== 4: PIN für alles, was der Browser ausschaltet", flush=True)
    an(G)
    c, j = G.req("/api/mode", {"mode": "transport"})
    pruef(c == 200 and G.schutz()["level"] == "off", "ohne PIN: Modus «Transport» schaltet aus wie bisher (%d)" % c)
    G.req("/api/mode", {"mode": ""})
    key = G.kurz                                             # the key of the shortcut (in the settings file from the start:
    an(G)                                                    # the demo makes no new app keys)
    c, t = G.req("/k/%s/disarm" % key, wer=None)
    pruef(c == 200 and G.schutz()["level"] == "off", "ohne PIN: Kurzbefehl «disarm» wie bisher (%d)" % c)
    c, j = G.req("/api/protect", {"action": "pin", "new": PIN})
    pruef(c == 200 and j.get("pin"), "PIN gesetzt")
    an(G)

    def bleibt_an(text, c, j):
        pruef(c == 403 and isinstance(j, dict) and j.get("need_pin") and G.schutz()["level"] != "off", "%s: 403 «PIN nötig», Schutz bleibt an (%d)" % (text, c))

    bleibt_an("Modus «Transport» ohne PIN", *G.req("/api/mode", {"mode": "transport", "lang": "de"}))
    pruef(G.req("/api/state")[1]["state"]["mode"]["id"] == "", "der Modus ist nicht umgestellt")
    bleibt_an("Modus «Transport» als Familie", *G.req("/api/mode", {"mode": "transport"}, wer="Anna"))
    bleibt_an("«Alle aus» (mehrere Geräte)", *G.req("/api/fleet", {"action": "disarm", "id": "all"}))
    bleibt_an("«Aus» (/api/arm)", *G.req("/api/arm", {"action": "disarm"}))
    bleibt_an("«Aus» (/api/protect)", *G.req("/api/protect", {"action": "level", "level": "off"}))
    bleibt_an("«Simulation an» (schaltet den Schutz aus)", *G.req("/api/sim", {"on": True, "confirm": True}))
    c, t = G.req("/k/%s/disarm" % key, wer=None)
    pruef(c == 403 and "pin" in str(t).lower() and G.schutz()["level"] != "off", "Kurzbefehl «disarm» ohne PIN: 403 mit Hinweis (%d)" % c)
    c, j = G.req("/api/mode", {"mode": "transport"}, pin="0000")
    pruef(c == 403 and j.get("need_pin") and G.schutz()["level"] != "off", "falsche PIN: 403, Schutz bleibt an")
    c, j = G.req("/api/mode", {"mode": "home"})
    pruef(c == 200, "ein Modus, der nicht ausschaltet («Zuhause»), braucht keine PIN (%d)" % c)
    c, j = G.req("/api/mode", {"mode": ""})
    pruef(c == 200 and G.schutz()["level"] != "off", "zurück zu den eigenen Einstellungen (waren «an»): keine PIN (%d)" % c)
    c, j = G.req("/api/arm", {"action": "arm_now"})
    pruef(c == 200, "Einschalten braucht keine PIN")
    c, j = G.req("/api/light", {"which": "white", "mode": "off"}, wer="Anna")
    pruef(c != 403 or not (isinstance(j, dict) and j.get("need_pin")), "anderes (Licht) braucht keine PIN")
    c, j = G.req("/api/mode", {"mode": "transport"}, pin=PIN)
    pruef(c == 200 and G.schutz()["level"] == "off" and G.req("/api/state")[1]["state"]["mode"]["id"] == "transport", "richtige PIN (Kopfzeile X-MW-PIN): «Transport», Schutz aus (%d)" % c)
    G.req("/api/mode", {"mode": ""}); an(G)
    c, j = G.req("/api/fleet", {"action": "disarm", "id": "me"}, pin=PIN)      # (the demo itself refuses /api/fleet afterwards)
    pruef(not j.get("need_pin") and (c == 200) == (G.schutz()["level"] == "off"), "richtige PIN: «Dieses Gerät aus» kommt durch die PIN-Prüfung (%d)" % c)
    an(G)
    c, t = G.req("/k/%s/disarm?pin=%s" % (key, PIN), wer=None)
    pruef(c == 200 and G.schutz()["level"] == "off", "Kurzbefehl mit ?pin=: aus (%d)" % c)
    an(G)
    c, j = G.req("/api/arm", {"action": "disarm", "pin": PIN}, wer="Anna")
    pruef(c == 200 and G.schutz()["level"] == "off", "Familie mit der PIN: «Aus» (%d)" % c)
    an(G)
    c, j = G.req("/api/arm", {"action": "disarm"}, pin=PIN)
    pruef(c == 200 and G.schutz()["level"] == "off", "«Aus» mit der PIN in der Kopfzeile (%d)" % c)
    # automatic: a schedule switches off without the PIN
    an(G)
    jetzt = datetime.now()
    plan = {"name": "Aus-Plan", "enabled": True, "days": list(range(7)), "start": (jetzt - timedelta(minutes=2)).strftime("%H:%M"),
            "end": (jetzt + timedelta(minutes=20)).strftime("%H:%M"), "actions": {"armed": False}}
    if (jetzt - timedelta(minutes=2)).date() == (jetzt + timedelta(minutes=20)).date():
        G.req("/api/schedule", {"action": "add"})
        n = len(G.req("/api/schedule")[1]["schedules"]) - 1
        c, j = G.req("/api/schedule", {"action": "save", "index": n, "schedule": plan})
        pruef(c == 200 and G.warte(lambda: G.schutz()["level"] == "off"), "ein Zeitplan schaltet weiter ohne PIN aus")
        G.req("/api/schedule", {"action": "remove", "index": n})
        pruef(G.warte(lambda: G.schutz()["level"] != "off"), "nach dem Zeitplan wieder an (eigene Einstellung)")
    else:
        print("  (Zeitplan-Teil übersprungen: Mitternacht)")
    # the administrator is not locked out: PIN away with the old PIN, then everything as before
    c, j = G.req("/api/protect", {"action": "pin", "new": "", "old": "0000"})
    pruef(c == 400 and G.schutz()["pin"], "PIN entfernen mit falscher alter PIN: nein")
    c, j = G.req("/api/protect", {"action": "pin", "new": "", "old": PIN})
    pruef(c == 200 and not G.schutz()["pin"], "PIN entfernen mit der alten PIN")
    an(G)
    c, j = G.req("/api/arm", {"action": "disarm"})
    pruef(c == 200 and G.schutz()["level"] == "off", "danach «Aus» wieder ohne PIN")


def pin_im_browser(G, pruef):
    print("== 4: die PIN-Frage im Browser", flush=True)
    from playwright.sync_api import sync_playwright
    G.req("/api/protect", {"action": "pin", "new": PIN})
    an(G)
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        ctx = br.new_context(viewport={"width": 390, "height": 844}, http_credentials={"username": "admin", "password": PASSWORT})
        pg = ctx.new_page()
        jsf = []
        pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
        for seite in ("/", "/protect", "/more", "/cams"):
            pg.goto(G.base + seite, wait_until="domcontentloaded")
            pruef(pg.evaluate("() => typeof window.mwPinAsk === 'function'"), "Seite %s kann nach der PIN fragen" % seite)
        pg.goto(G.base + "/", wait_until="domcontentloaded")
        POST = """(b) => { window.__r = null; fetch("/api/mode", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b)})
                   .then(async r => { window.__r = {s: r.status, j: await r.json()}; }); }"""
        pg.evaluate(POST, {"mode": "transport", "lang": "de"})
        pg.wait_for_selector("#mw-pin-dlg #mw-pin-in", timeout=8000)
        pruef(pg.locator("#mw-pin-ok").inner_text() == "Ausschalten" and "Schutz" in pg.locator("#mw-pin-msg").inner_text(), "Fenster: Feld «PIN», Knopf «Ausschalten»")
        pruef(pg.locator("#mw-pin-in").get_attribute("type") == "password" and pg.locator("#mw-pin-in").get_attribute("inputmode") == "numeric", "PIN-Feld: verdeckt, Zahlentastatur")
        pg.locator("#mw-pin-no").click()
        pg.wait_for_function("() => window.__r !== null", timeout=8000)
        pruef(pg.evaluate("() => window.__r.s") == 403 and pg.locator("#mw-pin-dlg").count() == 0 and G.schutz()["level"] != "off", "✕: nichts geschieht, Schutz bleibt an")
        pg.evaluate(POST, {"mode": "transport", "lang": "de"})
        pg.wait_for_selector("#mw-pin-in", timeout=8000)
        pg.locator("#mw-pin-in").fill("0000"); pg.locator("#mw-pin-ok").click()
        pg.wait_for_function("() => { const m = document.getElementById('mw-pin-msg'); return m && /falsche PIN/.test(m.textContent); }", timeout=8000)
        pruef(G.schutz()["level"] != "off", "falsche PIN: das Fenster fragt noch einmal («falsche PIN»), Schutz bleibt an")
        pg.locator("#mw-pin-in").fill(PIN); pg.locator("#mw-pin-in").press("Enter")
        pg.wait_for_function("() => window.__r !== null", timeout=8000)
        pruef(pg.evaluate("() => window.__r.s") == 200 and pg.evaluate("() => window.__r.j.mode.id") == "transport" and G.schutz()["level"] == "off",
              "richtige PIN: die Anfrage geht noch einmal, Modus «Transport», Schutz aus")
        pruef(pg.locator("#mw-pin-dlg").count() == 0, "Fenster ist zu")
        pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])
        ctx.close(); br.close()
    G.req("/api/mode", {"mode": ""})
    G.req("/api/protect", {"action": "pin", "new": "", "old": PIN})


def stufe_sirene(G, pruef):
    print("== 3: die Stufe bestimmt die Sirene", flush=True)

    def stand():
        P = G.schutz(); c = G.req("/api/state")[1]["cfg"]
        return P["level"], bool(P["escalate"]["on"]), c.get("siren_on")

    G.req("/api/protect", {"action": "level", "level": "off"})
    G.req("/api/text", {"key": "siren_on", "value": "off"})
    G.req("/api/protect", {"action": "level", "level": "full"})
    pruef(stand() == ("full", True, "person"), "«Voll»: Sirene nach der Wartezeit an, «Sirene bei Alarm» = Person %s" % (stand(),))
    G.req("/api/protect", {"action": "level", "level": "watch"})
    pruef(stand() == ("watch", False, "off"), "«Voll» → «Wachsam»: beides wieder aus %s" % (stand(),))
    G.req("/api/protect", {"action": "level", "level": "full"})
    G.req("/api/protect", {"action": "level", "level": "off"})
    for name, wie in (("Knopf «Ein»", lambda: G.req("/api/arm", {"action": "arm_now"})),
                      ("Familie schaltet ein", lambda: G.req("/api/arm", {"action": "arm"}, wer="Anna")),
                      ("Modus «Zuhause»", lambda: G.req("/api/mode", {"mode": "home"}))):
        G.req("/api/mode", {"mode": ""})
        G.req("/api/protect", {"action": "level", "level": "full"})
        G.req("/api/protect", {"action": "level", "level": "off"})
        wie()
        pruef(stand() == ("watch", False, "off"), "«Voll» → «Aus» → %s: «Wachsam» ohne Sirene %s" % (name, stand()))
    G.req("/api/mode", {"mode": ""})
    jetzt = datetime.now()
    if (jetzt - timedelta(minutes=2)).date() == (jetzt + timedelta(minutes=20)).date():
        G.req("/api/protect", {"action": "level", "level": "full"})
        G.req("/api/protect", {"action": "level", "level": "off"})
        G.req("/api/schedule", {"action": "add"})
        n = len(G.req("/api/schedule")[1]["schedules"]) - 1
        G.req("/api/schedule", {"action": "save", "index": n, "schedule": {
            "name": "Ein-Plan", "enabled": True, "days": list(range(7)), "start": (jetzt - timedelta(minutes=2)).strftime("%H:%M"),
            "end": (jetzt + timedelta(minutes=20)).strftime("%H:%M"), "actions": {"armed": True}}})
        G.warte(lambda: G.schutz()["level"] != "off")
        pruef(stand() == ("watch", False, "off"), "«Voll» → «Aus» → Zeitplan schaltet ein: «Wachsam» ohne Sirene %s" % (stand(),))
        G.req("/api/schedule", {"action": "remove", "index": n})
        G.warte(lambda: G.schutz()["level"] == "off")
    G.req("/api/protect", {"action": "level", "level": "full"})
    G.req("/api/arm", {"action": "disarm"}); G.req("/api/protect", {"action": "level", "level": "full"})
    pruef(stand() == ("full", True, "person"), "«Voll» bleibt «Voll» mit Sirene %s" % (stand(),))
    # the user's own choice stays
    G.req("/api/protect", {"action": "level", "level": "off"})
    c, j = G.req("/api/text", {"key": "siren_on", "value": "alarm"})
    G.req("/api/protect", {"action": "level", "level": "full"})
    G.req("/api/protect", {"action": "level", "level": "watch"})
    pruef(c == 200 and stand() == ("watch", False, "alarm"), "selbst gewählte «Sirene bei Alarm» bleibt in «Wachsam» %s" % (stand(),))
    G.req("/api/protect", {"action": "level", "level": "full"})
    G.req("/api/text", {"key": "siren_on", "value": "person"})                  # by hand, the same value the level would set
    G.req("/api/protect", {"action": "level", "level": "off"}); G.req("/api/arm", {"action": "arm_now"})
    pruef(stand() == ("watch", False, "person"), "von Hand auf «Person» gestellt: bleibt nach «Aus» → «Ein» %s" % (stand(),))
    G.req("/api/protect", {"action": "escalate", "on": True, "s": 30})
    G.req("/api/arm", {"action": "disarm"}); G.req("/api/arm", {"action": "arm_now"})
    pruef(stand() == ("watch", True, "person"), "Schalter «Sirene nach 30 s» von Hand: bleibt nach «Aus» → «Ein» %s" % (stand(),))
    G.req("/api/protect", {"action": "escalate", "on": False}); G.req("/api/text", {"key": "siren_on", "value": "off"})
    G.req("/api/protect", {"action": "level", "level": "off"})


def speichern_zeitplan(G, pruef):
    print("== 11: sofort gespeichert, «von Hand» übersteht den Neustart", flush=True)
    # ohne die Demo (wie werkzeuge/web_rauchtest.py, Quelle «sim:0»): die Demo schaltet 3 s nach jedem Start von selbst ein
    G.stop()
    G.einst_aendern(lambda c: c.update(source="sim:0"))
    G.start(demo=False)
    G.req("/api/arm", {"action": "arm_now"})
    t0 = time.time()
    pruef(G.einst().get("armed") is True and time.time() - t0 < 1.5, "«Ein» steht sofort in der Einstellungsdatei")
    G.req("/api/arm", {"action": "disarm"})
    pruef(G.einst().get("armed") is False and time.time() - t0 < 3.0, "«Aus» steht sofort in der Einstellungsdatei")
    jetzt = datetime.now()
    if (jetzt - timedelta(minutes=5)).date() != (jetzt + timedelta(minutes=30)).date():
        print("  (Zeitplan-Teil übersprungen: Mitternacht)"); return
    G.req("/api/schedule", {"action": "add"})
    n = len(G.req("/api/schedule")[1]["schedules"]) - 1
    plan = {"name": "Nacht", "enabled": True, "days": list(range(7)), "start": (jetzt - timedelta(minutes=5)).strftime("%H:%M"),
            "end": (jetzt + timedelta(minutes=30)).strftime("%H:%M"), "actions": {"armed": True}}
    G.req("/api/schedule", {"action": "save", "index": n, "schedule": plan})
    pruef(G.warte(lambda: G.schutz()["level"] != "off"), "der Zeitplan schaltet ein")
    G.req("/api/arm", {"action": "disarm"})
    e = G.einst()
    pruef(e.get("armed") is False and (e.get("sched_manual") or {}).get("armed", {}).get("v") is True, "von Hand aus: mit dem Vermerk sofort gespeichert %s" % (e.get("sched_manual"),))
    time.sleep(2.5)
    pruef(G.schutz()["level"] == "off", "der Zeitplan lässt es aus (wie bisher)")
    G.stop(hart=True)                                           # Strom weg
    G.start(demo=False)
    time.sleep(4)
    st = G.req("/api/state")[1]["state"]
    pruef(G.schutz()["level"] == "off" and "armed" in (st.get("sched_manual") or []) and "Nacht" in (st.get("sched_active") or []),
          "nach dem harten Neustart: bleibt aus, obwohl der Zeitplan läuft %s %s %s" % (G.schutz()["level"], st.get("sched_manual"), st.get("sched_active")))
    plan2 = dict(plan, actions={"armed": False})                 # the schedule changes: it takes over again, the note goes
    G.req("/api/schedule", {"action": "save", "index": n, "schedule": plan2})
    G.req("/api/schedule", {"action": "save", "index": n, "schedule": plan})
    pruef(G.warte(lambda: G.schutz()["level"] != "off"), "ändert der Zeitplan, übernimmt er wieder (schaltet ein)")
    pruef(G.warte(lambda: not (G.einst().get("sched_manual") or {}), 25), "der Vermerk ist dann auch aus der Datei weg")
    G.req("/api/arm", {"action": "disarm"})
    G.stop(hart=True)
    G.einst_aendern(lambda c: c["sched_manual"]["armed"].update(t=time.time() - 3 * 3600))   # the note is from an earlier window (3 h ago)
    G.start(demo=False)
    pruef(G.warte(lambda: G.schutz()["level"] != "off"), "ein Vermerk aus einem früheren Zeitfenster gilt nicht mehr: der Zeitplan schaltet ein")
    G.req("/api/schedule", {"action": "remove", "index": n})


if __name__ == "__main__":
    sys.exit(main())
