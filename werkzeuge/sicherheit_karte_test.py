#!/usr/bin/env python3
"""Test «Karte Sicherheit» (Einstellungen → Sicherheit): Passwort, Benutzer, App-Schlüssel, Sicherheits-Check.

Hintergrund (3.72): /api/schema liess jeden Abschnitt ohne Schalter weg. Seit 3.23 hat «Security» keinen Schalter mehr,
darum fehlte die ganze Karte (kein #users-box), obwohl Hinweise und Werkzeuge dorthin zeigen. Der Abschnitt kommt jetzt
für den Administrator immer (Teil 540: SECTIONS_OWN_CONTENT).

Startet MoveEye ohne Fenster mit dem Demo-Bild als Videoquelle (ohne «--demo»: dort sind Passwort und App-Schlüssel
gesperrt), eigener Einstellungs-Ordner, zuerst OHNE Passwort (dieses Gerät), und prüft mit Playwright (iPhone):

  1. /api/schema nennt «Security» (Einfach und Experte); kein anderer Abschnitt mit eigener Karte fehlt.
  2. Die Karte ist da: Web-Passwort, Benutzer (#users-box), App-Schlüssel, Sicherheits-Check.
  3. Passwort über die Karte setzen; danach neu anmelden.
  4. Benutzer anlegen, dessen Passwort ändern (Anmeldung mit dem neuen geht, mit dem alten nicht).
  5. App-Schlüssel machen: wird einmal gezeigt, /api/state geht damit, /api/users nicht.
  6. Sicherheits-Check läuft und zeigt Zeilen.
  7. Ein Benutzer ohne Admin-Rechte (eigene Rechte: Einstellungen) bekommt den Abschnitt nicht und sieht die Karte nicht;
     /api/users und /api/appkeys bleiben für ihn zu.
  8. Keine JavaScript-Fehler; kein Passwort / Schlüssel im Protokoll.

  python3 werkzeuge/sicherheit_karte_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos sicherheit_*.png
"""
import argparse
import base64
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)


def zufall(vor):
    return vor + base64.b16encode(os.urandom(5)).decode().lower()


ADMIN_PW, USER_PW1, USER_PW2 = zufall("Admin-"), zufall("Erst-"), zufall("Neu-")


def main():
    ap = argparse.ArgumentParser(description="Karte Sicherheit in den Einstellungen")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5139)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (sicherheit_*.png)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_sicherheit_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(a.port), "--bind", "127.0.0.1",
                          "--config", cfg], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    geheim = [ADMIN_PW, USER_PW1, USER_PW2]
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open("http://127.0.0.1:%d/manifest.webmanifest" % a.port, timeout=2); break
            except Exception:
                time.sleep(1)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            lauf(br, a, pruef, geheim)
            br.close()
        if p.poll() is not None:
            fehler.append("MoveEye ist während des Tests abgestürzt")
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        log = open(os.path.join(tmp, "log.txt"), errors="replace").read()
        log += "".join(open(x, errors="replace").read() for x in glob.glob(os.path.join(cfg, "**", "*.log"), recursive=True))
        pruef(not any(g and g in log for g in geheim), "Protokoll: kein Passwort und kein App-Schlüssel")
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)
    print("Sicherheit-Karte-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def holen(port, pfad, user=None, pw=None, kopf=None):
    """(Status, JSON oder None) - direkt, ohne Browser"""
    rq = urllib.request.Request("http://127.0.0.1:%d%s" % (port, pfad), headers=dict(kopf or {}))
    if user is not None:
        rq.add_header("Authorization", "Basic " + base64.b64encode(("%s:%s" % (user, pw)).encode()).decode())
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(rq, timeout=10) as r:
            roh = r.read()
            try:
                return r.status, json.loads(roh)
            except ValueError:
                return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, None


def lauf(br, a, pruef, geheim):
    base = "http://127.0.0.1:%d" % a.port
    KARTE = "#settings details[data-view='grp:security']"      # eine Gruppe mit nur einem Abschnitt ist selbst die Karte
    jsf = []

    def seite(**kw):
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3, **kw)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
        return ctx, pg

    def weg(pg):
        for _ in range(3):
            pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => b.offsetParent && ['OK', 'Überspringen', 'Verstanden', 'Später', 'Schliessen'].includes(b.textContent.trim().replace(/ ?›$/, ''))).forEach(b => b.click())""")
            pg.wait_for_timeout(300)
        pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")

    def warte(pg, fn, ms=15000):
        t_ = time.time() + ms / 1000.0
        v = None
        while time.time() < t_:
            v = fn()
            if v:
                return v
            pg.wait_for_timeout(250)
        return v

    def oeffnen(pg):
        """Einstellungen laden, die Karte Sicherheit aufklappen; True = die Karte ist da"""
        pg.goto(base + "/settings?open=grp:security", wait_until="domcontentloaded")
        warte(pg, lambda: pg.evaluate("() => document.querySelectorAll('#settings details[data-view^=\"sec:\"]').length > 5"))
        weg(pg)
        da = pg.evaluate("s => !!document.querySelector(s)", KARTE)
        if da:
            pg.evaluate("""s => { let d = document.querySelector(s); while (d) { if (d.tagName === 'DETAILS') d.open = true; d = d.parentElement; } }""", KARTE)
            pg.wait_for_timeout(600)
        return da

    def foto(pg, name, sel=KARTE):
        if a.bilder:
            weg(pg)
            pg.evaluate("s => { const e = document.querySelector(s); if (e) e.scrollIntoView({block: 'start'}); }", sel)
            pg.wait_for_timeout(700)
            pg.screenshot(path=os.path.join(a.bilder, "sicherheit_%s.png" % name))

    # ---- 1. /api/schema: der Abschnitt kommt, Einfach und Experte -----------------------------------------------------------
    for sv in ("0", "1"):
        c_, j = holen(a.port, "/api/schema?lang=de&simple=" + sv)
        sec = [s for s in (j or []) if s.get("id") == "Security"]
        pruef(c_ == 200 and len(sec) == 1 and sec[0].get("name") == "Sicherheit",
              "/api/schema?simple=%s nennt «Sicherheit» (%s)" % (sv, [s.get("name") for s in sec]))
        pruef(all(isinstance(s.get(k), list) for s in (j or []) for k in ("toggles", "sliders", "texts")), "jeder Abschnitt hat toggles / sliders / texts (simple=%s)" % sv)

    # ---- 2. ohne Passwort: die Karte ist da -----------------------------------------------------------------------------------
    ctx, pg = seite()
    pruef(oeffnen(pg), "ohne Passwort: Karte «Sicherheit» ist in den Einstellungen")
    v = warte(pg, lambda: pg.evaluate("""s => { const d = document.querySelector(s); if (!d) return null; const x = d.querySelector('#secpanel');
        return x && d.querySelector('#users-box') && d.querySelector('#ak-add') && d.querySelector('.sc-btn') ? {titel: d.querySelector('summary').textContent,
        text: d.innerText} : null; }""", KARTE))
    pruef(bool(v) and "Sicherheit" in v["titel"], "Titel «Sicherheit» (%s)" % (v and v["titel"]))
    for wort in ("Web-Passwort", "Benutzer", "App-Schlüssel", "Sicherheits-Check"):
        pruef(bool(v) and wort in v["text"], "Karte zeigt «%s»" % wort)
    foto(pg, "1_ohne_passwort")
    # ---- 3. Passwort über die Karte setzen ------------------------------------------------------------------------------------
    weg(pg)
    pg.locator(KARTE + " #secpanel button", has_text="Web-Passwort").first.click()
    pg.wait_for_selector("#pwd-ov input[type=password]", timeout=5000)
    ein = pg.locator("#pwd-ov input[type=password]")
    ein.nth(0).fill(ADMIN_PW); ein.nth(1).fill(ADMIN_PW)
    weg(pg)
    pg.locator("#pwd-ov button", has_text="Speichern").first.click()
    ok = warte(pg, lambda: holen(a.port, "/api/state")[0] == 401, 8000)
    pruef(bool(ok), "Passwort gesetzt: ohne Anmeldung kommt 401")
    ctx.close()
    pruef(holen(a.port, "/api/state", "admin", ADMIN_PW)[0] == 200, "Anmeldung mit dem neuen Passwort geht")

    # ---- 4. Benutzer anlegen, Passwort ändern ---------------------------------------------------------------------------------
    ctx, pg = seite(http_credentials={"username": "admin", "password": ADMIN_PW})
    pruef(oeffnen(pg), "mit Passwort (Administrator): Karte «Sicherheit» ist da")
    pruef(bool(warte(pg, lambda: pg.evaluate("() => !!document.querySelector('#users-box #us-add')"))), "Benutzer: Formular «Neuer Benutzer» ist da")
    weg(pg)
    pg.fill("#us-name", "Testkind"); pg.fill("#us-pw", USER_PW1); pg.select_option("#us-role", "custom")
    pg.click("#us-add")
    pruef(bool(warte(pg, lambda: pg.evaluate("() => !!document.querySelector('#users-box .us-card[data-u=\"Testkind\"]')"))), "Benutzer «Testkind» angelegt und in der Liste")
    pg.evaluate("""() => fetch('/api/users', {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: 'update', name: 'Testkind', perms: ['settings'], lang: 'de'})}).then(r => r.json())""")
    pruef(holen(a.port, "/api/state", "Testkind", USER_PW1)[0] == 200, "Benutzer meldet sich mit seinem Passwort an")
    pg.once("dialog", lambda d: d.accept(USER_PW2))
    weg(pg)
    pg.locator("#users-box .us-card[data-u='Testkind'] button[title='Neues Passwort']").click()
    ok = warte(pg, lambda: holen(a.port, "/api/state", "Testkind", USER_PW2)[0] == 200, 8000)
    pruef(bool(ok), "Passwort des Benutzers geändert: das neue geht")
    pruef(holen(a.port, "/api/state", "Testkind", USER_PW1)[0] == 401, "… und das alte nicht mehr")
    foto(pg, "2_benutzer", "#users-box")
    # ---- 5. App-Schlüssel ------------------------------------------------------------------------------------------------------
    weg(pg)
    pg.fill("#ak-name", "Testprogramm"); pg.click("#ak-add")
    key = warte(pg, lambda: pg.evaluate("() => { const k = document.getElementById('ak-key'); return k ? k.textContent : ''; }"), 8000) or ""
    geheim.append(key)
    pruef(key.startswith("me_") and len(key) > 20, "App-Schlüssel gemacht und einmal gezeigt")
    weg(pg)
    pg.locator(".sx-ak button.sec").last.click()
    pruef(bool(warte(pg, lambda: pg.evaluate("s => document.querySelector(s).innerText.includes('Testprogramm')", KARTE))), "App-Schlüssel steht in der Liste (nur der Name)")
    pruef(key not in pg.content(), "der Schlüssel steht danach nicht mehr in der Seite")
    pruef(holen(a.port, "/api/state", kopf={"X-MoveEye-Key": key})[0] == 200, "/api/state geht mit dem App-Schlüssel")
    pruef(holen(a.port, "/api/users", kopf={"X-MoveEye-Key": key})[0] in (401, 403), "/api/users geht mit dem App-Schlüssel nicht")
    # ---- 6. Sicherheits-Check --------------------------------------------------------------------------------------------------
    weg(pg)
    pg.locator(KARTE + " .sc-btn").click()
    n = warte(pg, lambda: pg.evaluate("s => { const d = document.querySelector(s), b = d.querySelector('.sc-btn'); return b.disabled ? 0 : d.querySelectorAll('.sc-list > div').length; }", KARTE), 60000)
    pruef(bool(n) and n >= 2, "Sicherheits-Check läuft und zeigt Zeilen (%s)" % n)
    foto(pg, "4_karte")
    ctx.close()

    # ---- 7. Benutzer ohne Admin-Rechte ----------------------------------------------------------------------------------------
    c_, j = holen(a.port, "/api/schema?lang=de&simple=0", "Testkind", USER_PW2)
    pruef(c_ == 200 and bool(j) and not any(s.get("id") == "Security" for s in j), "Benutzer (eigene Rechte: Einstellungen): /api/schema ohne «Sicherheit»")
    pruef(holen(a.port, "/api/users", "Testkind", USER_PW2)[0] == 403, "Benutzer: /api/users bleibt zu")
    pruef(holen(a.port, "/api/appkeys", "Testkind", USER_PW2)[0] == 403, "Benutzer: /api/appkeys bleibt zu")
    ctx, pg = seite(http_credentials={"username": "Testkind", "password": USER_PW2})
    da = oeffnen(pg)
    pruef(not da and not pg.evaluate("() => !!(document.querySelector('#users-box') || document.querySelector('#secpanel'))"),
          "Benutzer: keine Karte «Sicherheit», kein #users-box")
    foto(pg, "5_benutzer_ohne_karte", "#settings")
    ctx.close()
    pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])


if __name__ == "__main__":
    sys.exit(main())
