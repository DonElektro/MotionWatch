#!/usr/bin/env python3
"""Test «Bild drehen für jede Kamera» (Teil 639zzzzzzd) am echten Programm.

Startet MoveEye ohne Fenster mit der Demo (eigener Ordner, freier Port), Hauptkamera = Demo, eine Zusatzkamera usb:4
(MW_TEST_V4L; in der Demo liefert jede Quelle das Demo-Bild). Prüft:
  1. ab Werk: die Zusatzkamera ist nicht gedreht (/api/camturn rot 0, Auflösung quer)
  2. /api/camturn {spec usb:4, rot 90, mirror}: die Zusatzkamera liefert das Bild hochkant (Breite ↔ Höhe getauscht, /api/cams)
  3. Wärmebild: thermal_rotate / thermal_mirror über /api/text und /api/set (Schema), ungültige Werte abgelehnt
  4. Web (Playwright, Handy 390 px und PC): Einstellungen → Kamera / Servos zeigt den Kasten «Bild drehen: weitere Kameras»
     mit der Kamera, Auswahl 90° und Haken «spiegeln»; Wärmebild → «Kamera und Ausrichtung» hat «Wärmebild drehen»;
     eine Änderung auf der Seite kommt an; keine JavaScript-Fehler
  5. Neustart (Prozess beendet, neu gestartet, gleicher Ordner): die Einstellungen sind noch da, das Bild bleibt hochkant
  6. Pi-Fenster (Ersatz-tkinter aus lupe_test.py): Kamera / Servos → unter dem Blickwinkel der Kasten mit einer Auswahl pro
     weiterer Kamera und «spiegeln»; eine Wahl setzt cam_turn

  python3 werkzeuge/kamera_drehen_test.py [--datei X.py] [--bilder ORDNER]   # Bildschirmfotos kamera_drehen_*.png
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
PASSWORT = "Drehen-" + base64.b16encode(os.urandom(5)).decode().lower()
SPEC = "usb:4"


def freier_port(p):
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", p))
        except OSError:
            sk.bind(("127.0.0.1", 0)); p = sk.getsockname()[1]
    return p


def main():
    ap = argparse.ArgumentParser(description="Bild drehen für jede Kamera")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5143)
    ap.add_argument("--bilder", default="", help="Ordner für Bildschirmfotos (kamera_drehen_*.png)")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    a.port = freier_port(a.port)
    tmp = tempfile.mkdtemp(prefix="mw_kamera_drehen_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [SPEC], "kopf_ov": "", "thermal_source": "", "thermal_on": False,
          "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False,
          "ui_simple": False, "tours_auto": False}      # Expert: «Kamera / Servos» shows everything (also the field of view)
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    base = "http://127.0.0.1:%d" % a.port
    fehler = []
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                     urllib.request.HTTPBasicAuthHandler(_pw(base)))

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    def api(path, data=None):
        req = urllib.request.Request(base + path, data=None if data is None else json.dumps(data).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with op.open(req, timeout=15) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                return dict(json.loads(e.read().decode() or "{}"), _code=e.code)
            except ValueError:
                return {"_code": e.code}

    def res_usb():
        cams = api("/api/cams")
        cams = cams.get("cams", cams) if isinstance(cams, dict) else cams
        c = next((x for x in cams or [] if str(x.get("id")) == SPEC), None)
        return (c or {}).get("res") or ""

    def warte_res(pred, sek=40):
        t_ = time.time() + sek
        r = ""
        while time.time() < t_:
            r = res_usb()
            m = re.fullmatch(r"(\d+)x(\d+)", r)
            if m and pred(int(m.group(1)), int(m.group(2))):
                return r
            time.sleep(0.5)
        return r

    procs = []
    try:
        p = start(datei, a.port, cfg, tmp, procs)
        warte_start(p, op, base, tmp)
        # 1. factory
        q = api("/api/camturn?lang=de")
        c = next((x for x in q.get("cams") or [] if x["spec"] == SPEC), None)
        pruef(c is not None and c["rot"] == "0" and not c["mirror"], "ab Werk: %s nicht gedreht (%s)" % (SPEC, c))
        r0 = warte_res(lambda w, h: w > h)
        pruef(bool(r0), "Zusatzkamera liefert quer (%s)" % r0)
        # 2. turn by 90° + mirror
        q = api("/api/camturn", {"spec": SPEC, "rot": "90", "mirror": True, "lang": "de"})
        pruef(q.get("ok") and q["cams"][0]["rot"] == "90" and q["cams"][0]["mirror"], "90° + spiegeln gesetzt")
        r1 = warte_res(lambda w, h: h > w)
        pruef(bool(r1) and r0 and r1.split("x") == r0.split("x")[::-1], "gedreht: Breite ↔ Höhe getauscht (%s → %s)" % (r0, r1))
        q = api("/api/camturn", {"spec": SPEC, "rot": "45", "mirror": False})
        pruef(q.get("_code") == 400, "45° abgelehnt (%s)" % q.get("_code"))
        # 3. thermal camera (schema)
        q1 = api("/api/text", {"key": "thermal_rotate", "value": "180"})
        q2 = api("/api/set", {"key": "thermal_mirror", "value": True})
        cf = gespeichert(cfg)
        pruef(cf.get("thermal_rotate") == "180" and cf.get("thermal_mirror") is True,
              "Wärmebild: drehen 180° + spiegeln über die Einstellungen (%s %s → %s %s)" % (q1.get("ok"), q2.get("ok"), cf.get("thermal_rotate"), cf.get("thermal_mirror")))
        # 4. web
        web(base, a, pruef)
        # 5. restart
        p.terminate()
        try:
            p.wait(20)
        except subprocess.TimeoutExpired:
            p.kill()
        p = start(datei, a.port, cfg, tmp, procs)
        warte_start(p, op, base, tmp)
        q = api("/api/camturn?lang=de")
        c = next((x for x in q.get("cams") or [] if x["spec"] == SPEC), None)
        pruef(c is not None and c["rot"] == "270" and c["mirror"], "nach Neustart: Einstellung der Zusatzkamera erhalten (%s)" % c)
        r2 = warte_res(lambda w, h: h > w)
        pruef(bool(re.fullmatch(r"\d+x\d+", r2 or "")) and r2 == r1, "nach Neustart: Bild weiter hochkant (%s)" % r2)
        cf = gespeichert(cfg)
        pruef(cf.get("thermal_rotate") == "180" and cf.get("thermal_mirror") is True, "nach Neustart: Wärmebild-Einstellung erhalten")
        if p.poll() is not None:
            fehler.append("MoveEye ist während des Tests abgestürzt")
    finally:
        for p_ in procs:
            if p_.poll() is None:
                p_.terminate()
                try:
                    p_.wait(15)
                except subprocess.TimeoutExpired:
                    p_.kill()
        log = open(os.path.join(tmp, "log.txt"), errors="replace").read() if os.path.exists(os.path.join(tmp, "log.txt")) else ""
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
            fehler.append("Traceback im Protokoll")
        shutil.rmtree(tmp, ignore_errors=True)
    try:
        fenster(datei, pruef)
    except Exception as e:                                     # noqa: BLE001
        pruef(False, "Pi-Fenster: %s: %s" % (type(e).__name__, e))
    print("Kamera-drehen-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


def gespeichert(cfg, sek=20.0):
    """die gespeicherten Einstellungen (motionwatch_settings.json im Ordner des Tests) - wartet, bis das Wärmebild drin ist
    (MoveEye schreibt die Datei kurz nach der Änderung)"""
    t_, d = time.time() + sek, {}
    while time.time() < t_:
        try:
            with open(os.path.join(cfg, "motionwatch_settings.json")) as f:
                d = json.load(f)
            d = d.get("cfg", d) if isinstance(d, dict) else {}
            if d.get("thermal_rotate") == "180" and d.get("thermal_mirror") is True:
                return d
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    return d


def fenster(datei, pruef):
    """6. the window box with the fake tkinter of lupe_test (no display needed)"""
    print("Pi-Fenster (Ersatz-tkinter)", flush=True)
    src = open(os.path.join(HIER, "lupe_test.py"), encoding="utf-8").read()
    exec(re.search(r'FAKE_TK = r"""(.*?)"""', src, re.S).group(1), {})
    home = tempfile.mkdtemp(prefix="mw_drehen_tk_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_drehen_tk", "__file__": os.path.abspath(datei)}
    try:
        exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
        CFG, tkm = ns["CFG"], sys.modules["tkinter"]
        CFG.update(source="demo", extra_cams=[SPEC, "pi:1"], cam_turn={"pi:1": {"rot": "270", "mirror": False}}, lang="de")
        ns["save_settings"] = lambda *a, **k: None
        made = tkm.Button.__mro__[1].made
        n0 = len(made)
        ns["_ct_tk_box"](tkm.Frame())
        new = made[n0:]
        cbs = [w for w in new if type(w).__name__ == "Combobox"]
        chk = [w for w in new if type(w).__name__ == "Checkbutton"]
        txt = [w.k.get("text", "") for w in new if type(w).__name__ == "Label"]
        pruef(len(cbs) == 2 and len(chk) == 2 and any("Bild drehen: weitere Kameras" in t for t in txt),
              "Pi-Fenster: Kasten mit 2 Kameras (Auswahl + spiegeln) (%d / %d)" % (len(cbs), len(chk)))
        cb = cbs[0]
        cb.current = lambda *a: 2                              # «auf den Kopf (180°)»
        cb.binds["<<ComboboxSelected>>"][0]()
        pruef((CFG.get("cam_turn") or {}).get(SPEC) == {"rot": "180", "mirror": False}, "Pi-Fenster: Wahl setzt cam_turn (%s)" % CFG.get("cam_turn"))
        pruef(ns["App"]._fov_box is ns["_ct_app_fov_box"], "Pi-Fenster: der Kasten hängt am Blickwinkel (App._fov_box)")
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _pw(base):
    m = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    m.add_password(None, base, "admin", PASSWORT)
    return m


def start(datei, port, cfg, tmp, procs):
    logf = open(os.path.join(tmp, "log.txt"), "a")
    env = dict(os.environ, MW_TEST_V4L="4:Fake USB Cam")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1",
                          "--config", cfg, "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    procs.append(p)
    return p


def warte_start(p, op, base, tmp):
    for _i in range(240):
        if p.poll() is not None:
            sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
        try:
            op.open(base + "/manifest.webmanifest", timeout=2); return
        except Exception:
            time.sleep(1)
    sys.exit("MoveEye startet nicht")


def oeffne(pg, base, ms):
    """Einstellungen → ein Thema (Tipp auf seine Zeile; öffnet als Fenster)"""
    pg.goto(base + "/settings", wait_until="domcontentloaded")
    sel = '#ms-list .mi[data-ms="%s"]' % ms
    pg.wait_for_selector(sel, state="visible", timeout=60000)
    pg.wait_for_timeout(1200)
    for _ in range(3):                                         # a first-start dialog may be in the way
        pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => b.offsetParent && ['OK', 'Überspringen', 'Verstanden', 'Später', 'Schliessen'].includes(b.textContent.trim().replace(/ ?›$/, ''))).forEach(b => b.click())""")
        pg.wait_for_timeout(200)
    pg.locator(sel).click()
    pg.wait_for_timeout(1500)


def web(base, a, pruef):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        for gname, vp, mob in [("handy", {"width": 390, "height": 844}, True), ("pc", {"width": 1280, "height": 900}, False)]:
            ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2,
                                 http_credentials={"username": "admin", "password": PASSWORT})
            pg = ctx.new_page()
            jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            oeffne(pg, base, "sec:Camera / Servos")
            ok = False
            for _w in range(40):
                ok = pg.evaluate("() => !!document.querySelector('#ct-box [data-spec]')")
                if ok:
                    break
                pg.wait_for_timeout(400)
            pruef(ok, "%s: Kasten «Bild drehen: weitere Kameras» da" % gname)
            s = pg.evaluate("""() => { const r = document.querySelector('#ct-box [data-spec]'); if (!r) return null;
                const b = document.getElementById('ct-box'), f = document.getElementById('fov-box');
                return {spec: r.dataset.spec, rot: r.querySelector('select').value, mir: r.querySelector('input[type=checkbox]').checked,
                        title: b.querySelector('b').textContent, after: !!f && f.nextElementSibling === b,
                        wide: b.getBoundingClientRect().width <= window.innerWidth}; }""")
            pruef(bool(s) and s["spec"] == SPEC and s["rot"] == "90" and s["mir"] and "Bild drehen" in s["title"] and s["wide"],
                  "%s: Kamera %s mit 90° und «spiegeln», deutscher Titel, passt in die Breite (%s)" % (gname, SPEC, s))
            pruef(bool(s) and s["after"], "%s: Kasten steht unter «Blickwinkel der Kamera»" % gname)
            pg.evaluate("() => document.getElementById('ct-box').scrollIntoView({block: 'start'})")
            pg.wait_for_timeout(500)
            if a.bilder:
                os.makedirs(a.bilder, exist_ok=True)
                pg.locator("#ct-box").screenshot(path=os.path.join(a.bilder, "kamera_drehen_%s_kasten.png" % gname))
                pg.screenshot(path=os.path.join(a.bilder, "kamera_drehen_%s.png" % gname))
            if gname == "pc":                                  # a change on the page arrives (270° stays for the restart)
                pg.select_option("#ct-box [data-spec] select", "270")
                pg.wait_for_timeout(1500)
            # thermal camera: «Kamera und Ausrichtung»
            oeffne(pg, base, "sec:Thermal camera")
            th = None
            for _w in range(40):
                th = pg.evaluate("""() => { const d = document.querySelector('details[data-view="th:cam"]'); if (!d) return null;
                    const r = d.querySelector('[data-key="thermal_rotate"]'), m = d.querySelector('[data-key="thermal_mirror"]');
                    return {r: !!r, m: !!m, txt: r ? r.textContent : ""}; }""")
                if th and th["r"]:
                    break
                pg.wait_for_timeout(400)
            pruef(bool(th) and th["r"] and th["m"] and "Wärmebild drehen" in th["txt"],
                  "%s: Wärmebild → Kamera und Ausrichtung: «Wärmebild drehen» + «spiegeln» (%s)" % (gname, th))
            if a.bilder and th and th["r"]:
                pg.evaluate("() => { const d = document.querySelector('details[data-view=\"th:cam\"]'); d.open = true; d.querySelector('[data-key=\"thermal_rotate\"]').scrollIntoView({block: 'center'}); }")
                pg.wait_for_timeout(500)
                pg.screenshot(path=os.path.join(a.bilder, "kamera_drehen_%s_waermebild.png" % gname))
            pruef(not jsf, "%s: keine JavaScript-Fehler %s" % (gname, jsf[:3]))
            ctx.close()
        br.close()


if __name__ == "__main__":
    sys.exit(main())
