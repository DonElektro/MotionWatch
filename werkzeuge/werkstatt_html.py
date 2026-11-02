#!/usr/bin/env python3
"""Die Werkstatt «Bauen» als eigenständige HTML-Datei (Wunsch Daniel, 02.11.2026, Paket real-werkstatt-standalone).

Eine einzige Datei MoveEye_Werkstatt_X.Y.Z.html (dazu derselbe Inhalt als MoveEye_Werkstatt.html): Doppelklick, und sie läuft
offline im Browser, ohne Pi und ohne Internet – alle 10 Reiter, das 3D-Modell mit Explosion, Einzelteil-Vorschau, Druckplatten,
Paket- und Varianten-Wahl, «Stand MoveEye X.Y.Z», 5 Sprachen. «Mein Bau» bleibt im Browser (localStorage).
Nur die Druckdateien (raw.githubusercontent.com) und «Alles» (MoveEye_Bausatz.zip des neuesten Release) brauchen Internet.

Gleiche Quelle wie /build: das Werkzeug lädt die gebaute Programmdatei (webcam_bewegung_X_Y_Z.py + Zusatz-ZIP, ohne sie zu
starten) und ruft geh_offline_html() aus Teil 639w – dieselbe Seite, dieselben Daten (bau.json -> 639v, three.js + gehaeuse.glb
-> 639vb, Druck-Lage -> 639wb), dieselben Übersetzungen. Keine Doppelpflege.

  python3 werkzeuge/werkstatt_html.py                          # -> ausgabe_werkstatt/MoveEye_Werkstatt_X.Y.Z.html + MoveEye_Werkstatt.html
  python3 werkzeuge/werkstatt_html.py --aus DIR --datei webcam_bewegung_3_49_0.py
  python3 werkzeuge/werkstatt_html.py --test [--bilder DIR]    # dazu: offen in Chromium (file://, Netz gesperrt) prüfen, Bilder PC + Handy

Läuft bei jedem Release im Workflow «Bausatz» (Release-Asset, beide Namen) und als Test im «CI».
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
MAX_MB = 15.0                                              # Ziel: unter ca. 15 MB


def app_version():
    with open(os.path.join(REPO, "quelle", "010_grundlagen.py"), encoding="utf-8") as f:
        m = re.search(r'^APP_VERSION = "([0-9.]+)"', f.read(), re.M)
    return m.group(1) if m else ""


def programm(datei=None):
    if datei:
        return os.path.abspath(datei)
    v = app_version()
    p = os.path.join(REPO, "webcam_bewegung_%s.py" % v.replace(".", "_"))
    if os.path.isfile(p):
        return p
    alle = sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda x: tuple(int(n) for n in re.findall(r"\d+", os.path.basename(x))))
    if not alle:
        sys.exit("keine webcam_bewegung_*.py gefunden (zuerst python3 werkzeuge/bauen.py)")
    return alle[-1]


def bauen(datei):
    """-> (Version, HTML): die gebaute Datei laden (nicht starten) und geh_offline_html() aufrufen"""
    home = tempfile.mkdtemp(prefix="mw_werkstatt_")
    out = os.path.join(home, "werkstatt.html")
    code = r'''
import os, sys
ns = {"__name__": "mw_werkstatt", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
h = ns["geh_offline_html"]()
open(sys.argv[2], "w", encoding="utf-8").write(h)
print("VERSION " + ns["APP_VERSION"])
'''
    try:
        r = subprocess.run([sys.executable, "-c", code, datei, out], capture_output=True, text=True, timeout=300,
                           env=dict(os.environ, MOTIONWATCH_HOME=home), cwd=home)
        ver = next((l[8:].strip() for l in r.stdout.splitlines() if l.startswith("VERSION ")), "")
        if r.returncode or not ver or not os.path.isfile(out):
            sys.exit("Werkstatt nicht gebaut:\n" + (r.stdout + r.stderr)[-3000:])
        with open(out, encoding="utf-8") as f:
            return ver, f.read()
    finally:
        shutil.rmtree(home, ignore_errors=True)


def pruefen_text(html, ver):
    """ohne Browser: keine Adresse des Pi, die geladen würde, alles drin"""
    fehler = []
    for x in ('<script type="importmap">{"imports":{"three":"data:text/javascript;base64,', "data:model/gltf-binary;base64,",
              "window.MW_OFFLINE=", "raw.githubusercontent.com/DonElektro/MotionWatch/main/hardware/gehaeuse/Druckdateien/",
              "releases/latest/download/MoveEye_Bausatz.zip", "window.I18NXA=", '"Bauen"', ver):
        if x not in html:
            fehler.append("fehlt: " + x[:70])
    for x in ('src="/', "href=\"/", "/bau3d/", "/build/qr.svg", "/i18n/", "/sx/ui.js", "/*GEH", "<!--NAV-->", "/*ALERTS*/", "/*COMMON*/"):
        if x in html:
            fehler.append("noch drin: " + x)
    return fehler


def browser_test(pfad, bilder=None):
    """Chromium öffnet die Datei über file://, jede Anfrage ins Netz wird gesperrt (und zählt als Fehler beim Laden)"""
    from playwright.sync_api import sync_playwright
    fehler, netz = [], []
    url = "file://" + os.path.abspath(pfad)

    def sperren(route):
        u = route.request.url
        if u.startswith(("file:", "data:", "blob:")):
            route.continue_()
        else:
            netz.append(u)
            route.abort()

    def lauf(br, name, vp, mobile, lang):
        ctx = br.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile, device_scale_factor=2 if mobile else 1, locale=lang)
        ctx.set_offline(True)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append("JS: " + str(e)))
        pg.on("console", lambda m: errs.append("Konsole: " + m.text) if m.type == "error" else None)
        pg.route("**/*", sperren)
        pg.goto(url, wait_until="load", timeout=90000)
        try:
            pg.wait_for_function("window.BV_READY > 0", timeout=60000)
        except Exception:
            fehler.append(name + ": 3D-Modell nicht geladen (" + (pg.inner_text("#v3d-msg") or "?") + ")")
        n = pg.evaluate("window.BV_READY || 0")
        tabs = pg.locator("#g-tabs button")
        k = tabs.count()
        if k != 10:
            fehler.append("%s: %d Reiter statt 10" % (name, k))
        ids = pg.evaluate("[...document.querySelectorAll('.pane')].map(p => p.id)")
        for i in range(k):
            pg.locator("#g-tabs button").nth(i).click()
            on = pg.evaluate("[...document.querySelectorAll('.pane.on')].map(p => p.id)")
            if len(on) != 1 or on[0] != ids[i] or not pg.locator("#" + on[0]).is_visible():
                fehler.append("%s: Reiter %d zeigt %s" % (name, i + 1, on))
        # Einzelteil, Druckplatten, Explosion, Montage-Schritt, Mein Bau (localStorage), Variante
        pg.locator("#g-tabs button").nth(0).click()
        info = pg.evaluate("""() => { const id = Object.keys(TEIL).find(i => TEIL[i].datei); gSolo(id); const a = document.querySelector('#v3d-info a');
            const r = {solo: BV.mode, link: a ? a.href : ''}; gPlates(0); r.plate = BV.mode; r.plateLinks = [...document.querySelectorAll('#v3d-info a')].map(x => x.href);
            gWhole(); BV.explode = 1; bv('paint'); gStep(3); gStep(0);
            const c = document.querySelector('#g-buy input.chk'); c.click(); return r; }""")
        if info.get("solo") != "teil" or "raw.githubusercontent.com" not in info.get("link", ""):
            fehler.append(name + ": Einzelteil " + str(info)[:200])
        if info.get("plate") != "platten" or not any("MoveEye_Bausatz.zip" in x for x in info.get("plateLinks", [])):
            fehler.append(name + ": Druckplatten " + str(info)[:200])
        try:                                                 # the 3D view in software (swiftshader) may hold up the timer
            pg.wait_for_function("(() => { try { return (localStorage.getItem('mwbau') || '').includes('\"done\":[\"e:'); } catch (e) { return false; } })()", timeout=20000)
        except Exception:
            pass
        saved = pg.evaluate("(() => { try { return localStorage.getItem('mwbau') || ''; } catch (e) { return 'X'; } })()")
        if '"done":["e:' not in saved:
            fehler.append(name + ": Mein Bau nicht im Browser gespeichert: " + saved[:80])
        pg.evaluate("window.scrollTo(0, 0)")
        tab_txt = pg.locator("#g-tabs button").nth(1).inner_text()
        if bilder:
            os.makedirs(bilder, exist_ok=True)
            pg.screenshot(path=os.path.join(bilder, "werkstatt_%s.png" % name), full_page=False)
        if errs:
            fehler.extend(name + ": " + e for e in errs[:8])
        ctx.close()
        return n, tab_txt

    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        n, t1 = lauf(br, "pc", {"width": 1280, "height": 900}, False, "de-CH")
        n2, t2 = lauf(br, "handy", {"width": 390, "height": 844}, True, "fr-CH")
        br.close()
    if t1 != "Teile":
        fehler.append("Sprache Deutsch: Reiter heisst %r" % t1)
    if t2 != "Parties":
        fehler.append("Sprache Französisch: Reiter heisst %r" % t2)
    if netz:
        fehler.append("Anfragen ins Netz beim Laden: " + ", ".join(sorted(set(netz))[:5]))
    return fehler, n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datei", help="gebaute Programmdatei (Standard: webcam_bewegung_<APP_VERSION>.py)")
    ap.add_argument("--aus", default=os.path.join(REPO, "ausgabe_werkstatt"), help="Zielordner")
    ap.add_argument("--test", action="store_true", help="in Chromium offline öffnen und prüfen (Playwright)")
    ap.add_argument("--bilder", help="Bildschirmfotos PC + Handy in diesen Ordner (mit --test)")
    a = ap.parse_args()
    ver, html = bauen(programm(a.datei))
    fehler = pruefen_text(html, ver)
    os.makedirs(a.aus, exist_ok=True)
    ziel = os.path.join(a.aus, "MoveEye_Werkstatt_%s.html" % ver)
    for p in (ziel, os.path.join(a.aus, "MoveEye_Werkstatt.html")):
        with open(p, "w", encoding="utf-8") as f:
            f.write(html)
    mb = os.path.getsize(ziel) / 1e6
    print("Werkstatt %s: %s (%.1f MB)" % (ver, ziel, mb))
    if mb > MAX_MB:
        fehler.append("zu gross: %.1f MB (Ziel unter %.0f MB)" % (mb, MAX_MB))
    if a.test and not fehler:
        f2, n = browser_test(ziel, a.bilder)
        fehler += f2
        if not f2:
            print("Offline-Test: OK (file://, Netz gesperrt, %d 3D-Teile, 10 Reiter, Einzelteil, Druckplatten, Mein Bau, DE + FR)" % n)
    if fehler:
        print("FEHLER:\n  " + "\n  ".join(fehler))
        sys.exit(1)


if __name__ == "__main__":
    main()
