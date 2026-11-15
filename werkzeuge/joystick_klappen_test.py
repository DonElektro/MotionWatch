#!/usr/bin/env python3
"""Test «Kopf steuern» einklappbar (Teil 536): der Joystick-Block in der Karte «Bedienung» klappt für sich.

Startet MoveEye ohne Fenster mit der Demo (eigener Datenordner, synthetisches Bild) und prüft mit Playwright
(Handy 390 px dunkel mit Touch, PC 1280 × 800 mit Maus):

  1. Joystick «Immer»: Zeile «🕹 Kopf steuern» da (44 px, aria-expanded), Standard offen, Joystick / «Mittel» / ⇆ / «◎ Mitte» /
     «📍＋ Wegpunkt» darin; Schnellschalter und «⚙ Einstellungen» ausserhalb.
  2. Zuklappen: nur die Zeile (mit Pan / Tilt klein), Schnellschalter und «Einstellungen» bleiben sichtbar.
  3. Neu laden: bleibt zu («mw-open:headctl»); Aufklappen: wieder da, nach dem Neuladen offen.
  4. ⇕ «Alle zuklappen» / «Alle aufklappen» (639o) nehmen die Zeile mit, ohne den eigenen Stand zu ändern; «Meine Ansicht»
     bringt ihn zurück und bleibt aktiv; der erste Besuch («Nur Gruppen» von 639r) klappt sie nicht zu.
  5. PC quer: der Stick im Bild (#lv-joy) bleibt, auch wenn die Zeile zu ist.
  6. Joystick «Nie»: keine Zeile, kein leerer Platz.
  7. Servos (PCA9685 im Zustand vorgetäuscht, Joystick «Automatisch»): die «⏹ Stopp»-Zeile (Teil 541) klappt nie mit ein -
     offen und zu sichtbar, direkt unter der Zeile «🕹 Kopf steuern», vor den Schnellschaltern.
  8. Keine JavaScript-Fehler.

  python3 werkzeuge/joystick_klappen_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos joyklapp_*.png
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
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "Klapp-" + base64.b16encode(os.urandom(5)).decode().lower()

ZUSTAND = """() => { const vis = s => { const e = typeof s === 'string' ? document.querySelector(s) : s; return !!(e && e.getClientRects().length && (e.checkVisibility ? e.checkVisibility({visibilityProperty: true, contentVisibilityAuto: true}) : true)); };
  const hc = document.getElementById('lv-hc'), su = hc && hc.querySelector('summary');
  const r = su && su.getBoundingClientRect();
  return {da: !!hc && !hc.hidden && vis(hc), offen: !!(hc && hc.open), aria: su ? su.getAttribute('aria-expanded') : null, h: r ? Math.round(r.height) : 0,
    text: su ? su.textContent.trim() : '', pos: vis('#lv-hc .lv-hc-pos') ? document.querySelector('#lv-hc .lv-hc-pos').textContent : '',
    stick: vis('#stick'), stickImBild: !!document.querySelector('#lv-joy #stick'), speed: vis('#stick-speed'), swap: vis('#swap-side'), mitte: vis('#stick-center'),
    innen: !!(hc && hc.contains(document.getElementById('ctl-side'))),
    qsw: vis('#qsw') && [...document.querySelectorAll('#qsw > button')].some(b => vis(b)), qswInnen: !!(hc && hc.contains(document.getElementById('qsw'))),
    einst: vis('#set-foot'), ovon: document.body.classList.contains('lv-ovon'), nohead: document.body.classList.contains('lv-nohead'),
    gespeichert: localStorage.getItem('mw-open:headctl')}; }"""


def main():
    ap = argparse.ArgumentParser(description="Kopf steuern einklappbar")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5143)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (joyklapp_*.png)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_joyklapp_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "kopf_ov": "", "thermal_source": "", "thermal_on": False, "ip_sources": [],
          "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False,
          "ui_simple": False, "tours_auto": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1",
                          "--config", cfg, "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            cred = {"username": "admin", "password": PASSWORT}
            ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                                 color_scheme="dark", http_credentials=cred)
            pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            handy(pg, base, a, pruef)
            pruef(not jsf, "Handy: keine JavaScript-Fehler %s" % jsf[:3])
            ctx.close()
            ctx = br.new_context(viewport={"width": 1280, "height": 800}, color_scheme="dark", http_credentials=cred)
            pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            pc(pg, base, a, pruef)
            pruef(not jsf, "PC: keine JavaScript-Fehler %s" % jsf[:3])
            ctx.close()
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
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)
    print("Joystick-Klappen-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def warte(pg, fn, ms=12000):
    t_ = time.time() + ms / 1000.0
    v = None
    while time.time() < t_:
        v = fn()
        if v:
            return v
        pg.wait_for_timeout(150)
    return v


def weg(pg):
    pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => b.offsetParent && ['OK', 'Überspringen', 'Verstanden', 'Später', 'Schliessen'].includes(b.textContent.trim().replace(/ ?›$/, ''))).forEach(b => b.click())""")
    pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); document.querySelectorAll('.nws').forEach(e => e.remove()); }")


def laden(pg, base, joy=None, neu=False):
    """joy: "on" / "off" / None = keep; neu = forget the fold (first visit)."""
    pg.goto(base + "/", wait_until="domcontentloaded")
    pg.evaluate("""([j, n]) => { try { if (j) { const v = JSON.parse(localStorage.getItem('mw-live-view') || '{}'); v.joy = j; localStorage.setItem('mw-live-view', JSON.stringify(v)); }
      if (n) localStorage.removeItem('mw-open:headctl'); } catch (e) {} }""", [joy, neu])
    pg.evaluate("() => fetch('/api/news', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({seen: true})})")
    pg.reload(wait_until="domcontentloaded")
    warte(pg, lambda: pg.evaluate("() => { const v = document.getElementById('video'); return !!(v && v.naturalWidth > 0 && document.getElementById('qsw') && document.querySelector('#qsw > button')); }"), 30000)
    pg.wait_for_timeout(2500)                            # apply() runs again after 0.6 s and 2 s; «Meine Ansicht» loads
    weg(pg); pg.wait_for_timeout(300); weg(pg)


def zeige(pg):
    pg.evaluate("() => { const c = document.querySelector('details[data-view=controls]'); if (c) { c.open = true; c.scrollIntoView({block: 'start'}); } }")
    pg.wait_for_timeout(300)


def foto(pg, a, name):
    if a.bilder:
        loc = pg.locator("details[data-view=controls]")
        loc.screenshot(path=os.path.join(a.bilder, "joyklapp_%s.png" % name))


def falten(pg, k):
    """⇕ menu of 639o: close / mine / open."""
    pg.evaluate("() => { const b = document.getElementById('mwb-fold'); if (b) b.click(); }")
    pg.wait_for_timeout(200)
    ok = pg.evaluate("k => { const b = document.getElementById('all-' + k); if (!b) return false; b.click(); return true; }", k)
    pg.wait_for_timeout(500)
    return ok


def gemeinsam(pg, base, a, pruef, wo, tippen):
    laden(pg, base, joy="on", neu=True); zeige(pg)
    z = pg.evaluate(ZUSTAND)
    pruef(z["da"] and z["offen"] and z["aria"] == "true" and z["gespeichert"] != "0", "%s Immer: Zeile da, Standard offen, aria-expanded (%s)" % (wo, z))
    pruef("Kopf steuern" in z["text"] and "🕹" in z["text"], "%s: Text «🕹 Kopf steuern» (%s)" % (wo, z["text"]))
    pruef(z["h"] >= 44, "%s: Zeile mindestens 44 px hoch (%d)" % (wo, z["h"]))
    pruef(z["innen"] and not z["qswInnen"] and z["speed"] and z["swap"] and z["mitte"], "%s: «Mittel», ⇆, «◎ Mitte» in der Zeile, Schnellschalter nicht (%s)" % (wo, z))
    pruef(z["qsw"] and z["einst"], "%s: Schnellschalter und «Einstellungen» sichtbar" % wo)
    foto(pg, a, wo + "_offen")
    # collapse with a tap / click on the row
    tippen("#lv-hc > summary"); pg.wait_for_timeout(400)
    z = pg.evaluate(ZUSTAND)
    pruef(z["da"] and not z["offen"] and z["aria"] == "false" and not z["speed"] and not z["mitte"] and (z["ovon"] or not z["stick"]),
          "%s: zugeklappt nur die Zeile (%s)" % (wo, z))
    pruef(z["qsw"] and z["einst"], "%s zu: Schnellschalter und «Einstellungen» bleiben (%s)" % (wo, z))
    pruef(z["gespeichert"] == "0", "%s: gemerkt in «mw-open:headctl» (%s)" % (wo, z["gespeichert"]))
    foto(pg, a, wo + "_zu")
    pg.wait_for_timeout(1300)                            # «Meine Ansicht» stores after 1 s
    laden(pg, base); zeige(pg)
    z = pg.evaluate(ZUSTAND)
    pruef(z["da"] and not z["offen"] and z["aria"] == "false", "%s: nach dem Neuladen zu (%s)" % (wo, z))
    tippen("#lv-hc > summary"); pg.wait_for_timeout(400)
    z = pg.evaluate(ZUSTAND)
    pruef(z["offen"] and z["speed"] and z["aria"] == "true", "%s: wieder aufgeklappt (%s)" % (wo, z))
    pg.wait_for_timeout(1300)
    laden(pg, base); zeige(pg)
    z = pg.evaluate(ZUSTAND)
    pruef(z["offen"] and z["gespeichert"] == "1", "%s: nach dem Neuladen offen (%s)" % (wo, z))
    # 639o: «Alle zuklappen» / «Alle aufklappen» / «Meine Ansicht»
    if falten(pg, "close"):
        pg.evaluate("() => { const c = document.querySelector('details[data-view=controls]'); if (c) c.open = true; }"); pg.wait_for_timeout(200)
        z = pg.evaluate(ZUSTAND)
        pruef(not z["offen"] and z["aria"] == "false" and z["gespeichert"] == "1", "%s: «Alle zuklappen» klappt auch «Kopf steuern» zu, eigener Stand bleibt (%s)" % (wo, z))
        falten(pg, "mine")
        z = pg.evaluate(ZUSTAND)
        pruef(z["offen"], "%s: «Meine Ansicht» bringt den eigenen Stand (offen) zurück (%s)" % (wo, z))
        falten(pg, "close")
        falten(pg, "open")
        z = pg.evaluate(ZUSTAND)
        pruef(z["offen"] and z["speed"], "%s: «Alle aufklappen» klappt es wieder auf (%s)" % (wo, z))
        falten(pg, "mine")
        z = pg.evaluate(ZUSTAND)
        mine = pg.evaluate("() => { const b = document.getElementById('all-mine'); return !!(b && b.classList.contains('cur')); }")
        pruef(mine and z["da"] and z["offen"], "%s: «Meine Ansicht» geht weiter (%s, aktiv %s)" % (wo, z, mine))
        tippen("#lv-hc > summary"); pg.wait_for_timeout(400)
        z = pg.evaluate(ZUSTAND)
        pruef(not z["offen"] and z["gespeichert"] == "0", "%s: nach dem ⇕-Menü merkt ein Tipp wieder (%s)" % (wo, z))
        tippen("#lv-hc > summary"); pg.wait_for_timeout(400)
    else:
        pruef(False, "%s: ⇕-Menü «Alle zuklappen» nicht gefunden" % wo)
    return z


STOPP = """() => { const b = document.getElementById('srv-stop'), hc = document.getElementById('lv-hc'), su = hc && hc.querySelector('summary'), w = document.getElementById('lv-hc-stop');
  if (!b) return {da: false};
  const vis = b.getClientRects().length > 0 && (b.checkVisibility ? b.checkVisibility({visibilityProperty: true}) : true);
  const rb = b.getBoundingClientRect(), rs = su.getBoundingClientRect(), q = document.getElementById('qsw').getBoundingClientRect();
  return {da: true, sicht: vis, offen: hc.open, innen: !!(w && hc.contains(w)), direkt: !!(w && (hc.open ? w.previousElementSibling === su : hc.nextElementSibling === w)),
    unter: rb.top >= rs.bottom - 1 && rb.top - rs.bottom < 40, vorQsw: rb.bottom <= q.top + 1, text: b.textContent}; }"""


def servos_vortaeuschen(route):
    """/api/state as with a real pan / tilt head (PCA9685 found, «⏹ Stopp» on) - no hardware needed"""
    try:
        r = route.fetch()
    except Exception:                                    # page reloaded / closed meanwhile
        return
    try:
        j = r.json()
        s = j.setdefault("state", {})
        s["servo_backend"] = "pca9685 (test)"
        sv = s.get("servo") if isinstance(s.get("servo"), dict) else {}
        sv.update(stop_btn=True, sim=False); sv.setdefault("blocked", ""); sv.setdefault("driver", {})
        s["servo"] = sv
        route.fulfill(response=r, body=json.dumps(j), headers=dict(r.headers, **{"content-type": "application/json"}))
    except Exception:
        try:
            route.fulfill(response=r)
        except Exception:                                # already handled / page gone: nothing to do
            pass


def stopp(pg, base, a, pruef, wo, tippen):
    pg.route("**/api/state*", servos_vortaeuschen)
    laden(pg, base, joy="auto"); zeige(pg)
    if not pg.evaluate("() => document.getElementById('lv-hc').open"):
        tippen("#lv-hc > summary"); pg.wait_for_timeout(400)
    warte(pg, lambda: pg.evaluate(STOPP).get("sicht"), 8000)
    z, k = pg.evaluate(STOPP), pg.evaluate(ZUSTAND)
    pruef(k["da"] and not k["nohead"], "%s Servos (Automatisch): Zeile «Kopf steuern» da (%s)" % (wo, k))
    pruef(z.get("sicht") and z.get("offen") and z.get("direkt") and z.get("unter"), "%s offen: «⏹ Stopp» direkt unter der Zeile (%s)" % (wo, z))
    tippen("#lv-hc > summary"); pg.wait_for_timeout(500)
    z, k = pg.evaluate(STOPP), pg.evaluate(ZUSTAND)
    pruef(not k["offen"] and not k["speed"], "%s: zugeklappt (%s)" % (wo, k))
    pruef(z.get("sicht") and not z.get("innen") and z.get("direkt") and z.get("unter") and z.get("vorQsw"),
          "%s zu: «⏹ Stopp» bleibt sichtbar, direkt unter der Zeile, vor den Schnellschaltern (%s)" % (wo, z))
    foto(pg, a, wo + "_stopp_zu")
    pg.wait_for_timeout(2500)                            # several state polls later still there
    z = pg.evaluate(STOPP)
    pruef(z.get("sicht") and z.get("direkt"), "%s zu: «⏹ Stopp» nach weiteren Abfragen noch da (%s)" % (wo, z))
    tippen("#lv-hc > summary"); pg.wait_for_timeout(500)
    z = pg.evaluate(STOPP)
    pruef(z.get("sicht") and z.get("offen") and z.get("direkt"), "%s wieder offen: «⏹ Stopp» direkt unter der Zeile (%s)" % (wo, z))
    foto(pg, a, wo + "_stopp_offen")
    pg.unroute("**/api/state*", servos_vortaeuschen)


def handy(pg, base, a, pruef):
    tippen = lambda s: (lambda r: pg.touchscreen.tap(r[0], r[1]))(pg.evaluate("s => { const b = document.querySelector(s).getBoundingClientRect(); return [b.x + b.width / 2, b.y + b.height / 2]; }", s))
    gemeinsam(pg, base, a, pruef, "handy", tippen)
    z = pg.evaluate(ZUSTAND)
    pruef(not z["ovon"] and z["stick"] and not z["stickImBild"], "Handy hoch: Joystick in der Karte (%s)" % z)
    stopp(pg, base, a, pruef, "handy", tippen)
    laden(pg, base, joy="off"); zeige(pg)
    z = pg.evaluate(ZUSTAND)
    pruef(z["nohead"] and not z["da"] and not z["stick"], "Handy Nie: keine Zeile «Kopf steuern», kein Joystick (%s)" % z)
    pruef(z["qsw"] and z["einst"], "Handy Nie: Schnellschalter und «Einstellungen» da (%s)" % z)
    foto(pg, a, "handy_nie")


def pc(pg, base, a, pruef):
    tippen = lambda s: pg.click(s)
    gemeinsam(pg, base, a, pruef, "pc", tippen)
    tippen("#lv-hc > summary"); pg.wait_for_timeout(400)
    z = pg.evaluate(ZUSTAND)
    pruef(not z["offen"] and z["ovon"] and z["stickImBild"] and z["stick"], "PC quer zu: Stick im Bild bleibt (%s)" % z)
    print("  info  PC: Pan / Tilt in der Zeile «%s»" % z["pos"])
    tippen("#lv-hc > summary"); pg.wait_for_timeout(300)
    stopp(pg, base, a, pruef, "pc", tippen)
    laden(pg, base, joy="off")
    z = pg.evaluate(ZUSTAND)
    pruef(z["nohead"] and not z["da"], "PC Nie: keine Zeile (%s)" % z)


if __name__ == "__main__":
    sys.exit(main())
