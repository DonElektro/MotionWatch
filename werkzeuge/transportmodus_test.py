#!/usr/bin/env python3
"""Test «🧳 Transportmodus» (Teil 639zzzt, Planer 072, Hardware 080, Aufnahme 410).

Zwei Teile:
  1. Im Prozess (eigener Unterprozess mit leerem HOME): die echte Klasse Hardware mit einem falschen PCA9685 (FakePCA zeichnet
     jeden Puls auf). Kopf steht schief -> Transport ein -> fährt langsam (≤ 15 °/s) in die Grundstellung, danach beide
     Servo-Kanäle ganz aus und kein Puls mehr, auch wenn Joystick, Pfeile, Positionen, Lupe, Ziel von Hand und der
     Kopf-Koordinator es versuchen. Kein Alarm (Sirene, Push, Sabotage), aber die Aufnahme einer Person startet; SOS-Lampe
     blinkt. Aus -> der erste Puls ist genau die Grundstellung, Schutz wieder wie vorher, der Kopf fährt wieder.
  2. Programm (Demo, ohne Fenster) über HTTP: Ein nur mit Bestätigung, Bewegen gesperrt mit «Transportmodus aktiv» (423 / 409),
     SOS geht, bleibt über einen Neustart (sofort stromlos), Aus stellt den Schutz wieder her. Mit Playwright am Handy
     (390 px, dunkel): Band, Chip, Knopf, die beiden Fragen; --bilder ORDNER = Bildschirmfotos.

  python3 werkzeuge/transportmodus_test.py [--datei X.py] [--bilder ORDNER] [--nur innen|web]
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
PASSWORT = "Transport-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


# =============================================================================================== 1. im Prozess (falscher PCA9685)
def innen(datei):
    import runpy
    import threading
    from collections import deque
    from types import SimpleNamespace
    import numpy as np
    g = runpy.run_path(datei, run_name="transportmodus_test")
    G = g["tp_set"].__globals__                          # die echten globalen Namen (run_path gibt eine Kopie zurück)
    CFG, SRV, STATE = G["CFG"], G["SRV"], G["STATE"]
    rec = os.path.join(os.environ["HOME"], "rec"); os.makedirs(rec, exist_ok=True)
    CFG.update(record_dir=rec, sim_on=False, armed=False, arm_delay=0, kopf_transport=False, light_white_out="pca:2", notify_on=True,
               servo_driver="pca9685", servo_vmax_pan=120.0, servo_acc_pan=360.0, invert_pan=False, invert_tilt=False)

    class FakePCA:                                       # der Ersatz für den PCA9685: zeichnet auf, was die Hardware-Schleife schickt
        addr = 0x41

        def __init__(self):
            self.log = []; self.lock = threading.Lock()

        def pulse_us(self, ch, us):
            with self.lock:
                self.log.append((time.time(), ch, "us", float(us)))

        def switch(self, ch, on):
            with self.lock:
                self.log.append((time.time(), ch, "on" if on else "off", 0.0))

        def healthy(self):
            return True

        def close(self):
            pass

        def servo(self, since=0.0):
            with self.lock:
                return [x for x in self.log if x[1] in (0, 1) and x[0] >= since]

    G["save_settings"] = lambda *a, **k: None
    pca = FakePCA()
    G["HW_REINIT"]["want"] = False
    hw = G["Hardware"].__new__(G["Hardware"])          # die echte Hardware-Schleife, nur der Treiber ist falsch
    hw.backend = "pca9685"; hw.io = "none"; hw._OutputDevice = None; hw.pan = hw.tilt = hw.pi = None; hw.pca = pca
    hw.outs = {}; hw.fail = {}; hw._last_servo = None; hw._pca_lights = {}
    STATE["servo_backend"] = "pca9685 (test)"
    threading.Thread(target=hw.loop, daemon=True).start()
    lo, hi = float(CFG["servo_min_us"]), float(CFG["servo_max_us"])
    half = G["servo_half"]("pan")

    def deg(us):
        return ((us - lo) / (hi - lo) * 100.0 - 50.0) / 50.0 * half

    def warte(cond, s=20.0):
        end = time.time() + s
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.05)
        return False

    # ---- Kopf schief, dann Transport ein -----------------------------------------------------------------------------------
    CFG["pan"], CFG["tilt"] = 80.0, 25.0
    pruef(warte(lambda: SRV.get("started") and SRV.get("pos") is not None and G["servo_arrived"]() and abs(G["servo_pos"]()[0] - 80) < 0.01), "Kopf steht zuerst schief (pan 80 %, tilt 25 %)")
    CFG.update(armed=True, protect_level="full", siren_on="person", escalate_on=False); G["ARM"]["at"] = 0.0
    vorher = {k: CFG.get(k) for k in ("armed", "protect_level", "siren_on", "escalate_on", "notify_on", "tamper_on")}
    pruef(G["is_armed"](), "Schutz an (Ausgangslage)")
    t0 = time.time()
    ok, _ = G["tp_set"](True, "test")
    pruef(ok and G["servo_blocked"]() == "transport", "Transportmodus ein -> Servos gesperrt (servo_blocked = transport)")
    pruef(warte(G["servo_detached"], 30), "Kopf in der Grundstellung, danach Servos freigegeben (%.1f s)" % (time.time() - t0))
    p = G["servo_pos"]()
    pruef(abs(p[0] - 50) < 1e-6 and abs(p[1] - 50) < 1e-6, "Grundstellung = Mitte (kein gespeicherter Punkt): %.2f / %.2f" % p)
    pulses = [x for x in pca.servo(t0) if x[2] == "us" and x[1] == 0]
    v = 0.0
    for a_, b_ in zip(pulses, pulses[5:]):               # Geschwindigkeit über 5 Pulse (~0.1 s)
        if b_[0] - a_[0] > 0.05:
            v = max(v, abs(deg(b_[3]) - deg(a_[3])) / (b_[0] - a_[0]))
    pruef(pulses and abs(deg(pulses[-1][3])) < 0.05 and 0 < v <= 17.0, "langsam in die Grundstellung: höchstens %.1f °/s (Grenze 15 °/s, Messung über die Pulse)" % v)
    # 3.94.0: first the home pulse (one tick), then the outputs off - the flag «detached» comes one tick before the hardware
    warte(lambda: {x[1] for x in pca.servo(t0) if x[2] == "off"} == {0, 1}, 2)
    pulses = [x for x in pca.servo(t0) if x[2] == "us" and x[1] == 0]
    t_off = max([x[0] for x in pca.servo(t0) if x[2] == "off"] or [0])
    offs = {x[1] for x in pca.servo(t0) if x[2] == "off"}
    pruef(offs == {0, 1}, "beide Servo-Kanäle ganz aus (kein Haltemoment, kein Zittern): %s" % sorted(offs))
    pruef(t_off >= pulses[-1][0], "zuerst angekommen, dann ausgeschaltet")
    # ---- alles, was den Kopf bewegt, versucht es ----------------------------------------------------------------------------
    G["WAYPOINTS"].append([20.0, 70.0, "Zelt"])
    tried = {
        "Pfeile (move_camera)": G["move_camera"]("left", 10, "test"),
        "Joystick / Gamepad / Simulator (stick_camera)": (G["stick_camera"](1.0, 0, 60, "test"), time.sleep(0.12), G["stick_camera"](1.0, 0, 60, "test"))[2],
        "Position anfahren (teach_goto)": G["teach_goto"](len(G["WAYPOINTS"]) - 1, "test")[0],
        "Planer direkt (servo_goto)": G["servo_goto"](10, 10, "test", wait=False),
        "Lupe «Kopf folgt»": G["lupe_aim"]([0.1, 0.1, 0.2, 0.2], ("k", "test"), "de")[0],
    }
    for k, r in tried.items():
        pruef(r is False, "gesperrt: " + k)
    pruef("Transport" in G["teach_goto"](len(G["WAYPOINTS"]) - 1, "test")[1], "Positionen nennen den Grund: «%s»" % G["teach_goto"](len(G["WAYPOINTS"]) - 1, "test")[1])
    pruef("Transportmodus aktiv" in G["servo_blocked_text"]("de"), "kurzer Hinweis «Transportmodus aktiv» (%s)" % G["servo_blocked_text"]("de"))
    G["KOPF"]["turn_req"] = (10.0, 80.0, "test"); G["_kopf_tick"]()
    pruef(G["KOPF"]["turn_req"] is None and G["KOPF"]["status"].startswith("transport"), "Kopf-Koordinator (Runde, Alarm-Drehen, Übersicht, Parken) ruht")
    n0 = len(pca.servo(t_off + 0.001))
    for _ in range(40):                                  # Ziel von Hand / Folgen / Patrouille schreiben CFG pan / tilt
        CFG["pan"], CFG["tilt"] = 5.0, 95.0
        time.sleep(0.05)
    pruef(len(pca.servo(t_off + 0.001)) == n0 == 0, "kein einziger Puls mehr seit dem Ausschalten (%d)" % len(pca.servo(t_off + 0.001)))
    pruef(G["servo_pos"]() == (50.0, 50.0), "Kopf bleibt in der Grundstellung %s" % (G["servo_pos"](),))
    # ---- Alarm aus, Aufnahme läuft, SOS geht -----------------------------------------------------------------------------------
    calls = {"sound": [], "push": [], "person": [], "tamper": []}
    G["sound_play"] = lambda *a, **k: (calls["sound"].append(k.get("reason")), (True, ""))[1]
    G["speaker_ok"] = lambda: True
    G["siren_quiet"] = lambda: False
    G["push_alert"] = lambda *a, **k: calls["push"].append(a)
    G["alarm_ctx_note"] = lambda *a, **k: None
    G["alarm_track_begin"] = lambda *a, **k: None
    G["kopf_tamper_wanted"] = lambda: False

    class FakeNotifier:
        def person(self, n, snap, frame):
            calls["person"].append(n)

        def tamper(self, text, frame=None):
            calls["tamper"].append(text)

    class FakeWriter:
        def __init__(self):
            self.n = 0

        def write(self, f):
            self.n += 1

        def release(self):
            pass
    G["open_writer"] = lambda name, fps, size: (FakeWriter(), "test")
    G["WATCH_REF"]["w"] = SimpleNamespace(notifier=FakeNotifier(), frame_out=None)

    def watch():
        return SimpleNamespace(last_person_time=0.0, notifier=FakeNotifier(), writer=None, rec_size=None, preroll=deque(), _rec_retry=0.0,
                               last_cleanup=time.time(), frame_gaps=[], last_warm=0.0, rec_info=None, rec_name="", ai=None,
                               cleanup_recordings=lambda: None, _finish_recording=lambda: None)
    CFG.update(record=True, snapshot_on_person=False, alarm_confirm2=False)
    G["SIM"]["off_t"] = 0.0
    frame = np.zeros((120, 160, 3), np.uint8)
    w = watch()
    G["MotionWatch"].handle_recording(w, frame, [(10, 10, 30, 60)])
    pruef(w.writer is not None and w.writer.n >= 1 and STATE.get("recording"), "filmen geht weiter: eine Person startet die Aufnahme")
    G["siren_alarm"]("person"); G["siren_alarm"]("tamper")
    STATE.setdefault("tamper", {"sensor": False, "last": "", "state": "watching"})
    G["TamperGuard"].alarm(SimpleNamespace(cool=0.0, ref=None), "moved")
    pruef(not calls["person"] and not calls["push"] and not calls["sound"] and not calls["tamper"],
          "kein Alarm: kein Push, keine Sirene, keine Sabotage-Meldung (%s)" % {k: len(v_) for k, v_ in calls.items()})
    ok, msg = G["alm_sos_set"](True, "test", False)
    flashed = []
    for _ in range(30):
        flashed.append(bool(G["lights_tick"]().get("white"))); time.sleep(0.05)
    pruef(ok and True in flashed and False in flashed, "SOS-Lampe blinkt trotzdem (%s)" % msg)
    G["alm_sos_set"](False, "test", False)
    # ---- Aus: wieder wie vorher ----------------------------------------------------------------------------------------------
    t1 = time.time()
    ok, _ = G["tp_set"](False, "test")
    pruef(ok and not G["servo_detached"]() and G["servo_blocked"]() == "", "Transportmodus aus -> Servos wieder frei zum Bewegen")
    pruef(warte(lambda: any(x[2] == "us" for x in pca.servo(t1)), 3), "die Servos bekommen wieder Pulse (Haltemoment)")
    first = [x for x in pca.servo(t1) if x[2] == "us"][:2]
    pruef(first and all(abs(deg(x[3])) < 0.05 for x in first), "der erste Puls ist genau die Grundstellung (kein Sprung)")
    nachher = {k: CFG.get(k) for k in vorher}
    pruef(G["is_armed"]() and nachher == vorher, "Schutz wieder an wie vorher %s" % nachher)
    w = watch()
    G["MotionWatch"].handle_recording(w, frame, [(10, 10, 30, 60)])
    pruef(calls["person"] == [1] and calls["push"], "Gegenprobe: ohne Transportmodus gibt dieselbe Person wieder Alarm")
    G["MANUAL"]["until"] = 0.0
    pruef(G["move_camera"]("right", 10, "test") and warte(lambda: G["servo_pos"]()[0] > 55, 5), "der Kopf fährt wieder (Pfeil rechts)")
    print("Innen-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)), flush=True)
    return 1 if FEHLER else 0


# =============================================================================================== 2. Programm über HTTP + Browser
def starte(datei, cfg, port, tmp, nr):
    logf = open(os.path.join(tmp, "log%d.txt" % nr), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp,
                         env=dict(os.environ, HOME=tmp))
    p.logf = logf
    return p


def stoppe(p):
    p.terminate()
    try:
        p.wait(15)
    except subprocess.TimeoutExpired:
        p.kill()
    p.logf.close()


def web(datei, bilder):
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_transport_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "arm_delay": 0, "light_white_out": "pca:2"}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    base = "http://127.0.0.1:%d" % port
    pw_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm(); pw_mgr.add_password(None, base, "admin", PASSWORT)
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPBasicAuthHandler(pw_mgr))
    hdr = {"Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode(), "Content-Type": "application/json"}

    def req(path, d=None):
        r = urllib.request.Request(base + path, data=None if d is None else json.dumps(d).encode(), headers=hdr, method="GET" if d is None else "POST")
        try:
            with op.open(r, timeout=15) as f:
                return f.status, json.loads(f.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode() or "{}")
            except ValueError:
                return e.code, {}

    def bereit(p):
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log1.txt"), errors="replace").read()[-3000:])
            try:
                if req("/api/transport")[0] == 200:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    p = starte(datei, cfg, port, tmp, 1)
    try:
        pruef(bereit(p), "MoveEye (Demo) läuft")
        req("/api/arm", {"action": "arm_now"})
        c, j = req("/api/transport")
        pruef(c == 200 and j.get("on") is False, "Zustand: aus")
        c, j = req("/api/transport", {"on": True})
        pruef(c == 400, "ohne Bestätigung wird nichts geschaltet (%d)" % c)
        c, j = req("/api/transport", {"on": True, "confirm": True, "lang": "de"})
        pruef(c == 200 and j.get("on"), "Transportmodus ein (Bestätigung)")
        end = time.time() + 20
        while time.time() < end and req("/api/transport")[1].get("phase") != "free":
            time.sleep(0.3)
        c, j = req("/api/transport")
        pruef(j.get("phase") == "free" and j.get("detached"), "Grundstellung erreicht, Servos frei (%s)" % j.get("phase"))
        for path, d, code in (("/api/move", {"dir": "left", "lang": "de"}, 423), ("/api/stick", {"x": 1, "y": 0, "lang": "de"}, 423),
                              ("/api/follow", {"on": True, "lang": "de"}, 423), ("/api/quick", {"action": "patrol", "lang": "de"}, 423),
                              ("/api/lupe", {"action": "aim", "box": [0.1, 0.1, 0.3, 0.3], "lang": "de"}, 409)):
            c, r = req(path, d)
            txt = str(r.get("error") or r.get("msg") or "")
            pruef(c == code and "Transportmodus aktiv" in txt, "%s gesperrt: %d «%s»" % (path, c, txt[:70]))
        req("/api/set", {"key": "pan", "value": 10})
        time.sleep(1.5)
        c, s = req("/api/servo")
        pos = (s.get("pos") or s.get("state", {}).get("pos") or [None])
        pruef(pos and abs(float(pos[0]) - 50) < 0.1, "Regler «Pan» bewegt den Kopf nicht (%s)" % pos)
        c, j = req("/almanach/sos", {"action": "start"})
        pruef(c == 200 and j.get("ok"), "SOS-Lampe startet (%d %s)" % (c, j.get("msg")))
        req("/almanach/sos", {"action": "stop"})
        c, j = req("/api/state?lang=de")
        sv = (j.get("state") or {}).get("servo") or {}
        pruef((sv.get("transport") or {}).get("on") and (j.get("state") or {}).get("arm_state") == "armed",
              "Zustand für die Seiten: transport.on, der Schutz bleibt in den Einstellungen an")
        stoppe(p)
        # ---- Neustart: bleibt -----------------------------------------------------------------------------------------------
        p = starte(datei, cfg, port, tmp, 2)
        pruef(bereit(p), "Neustart")
        c, j = req("/api/transport")
        pruef(j.get("on") and j.get("phase") == "free", "nach dem Neustart: Transportmodus an, sofort stromlos (%s)" % j.get("phase"))
        c, r = req("/api/move", {"dir": "up", "lang": "de"})
        pruef(c == 423, "nach dem Neustart weiter gesperrt (%d)" % c)
        if bilder or True:
            browser(base, bilder, req)
        c, j = req("/api/transport")
        pruef(not j.get("on"), "im Browser beendet")
        c, j = req("/api/state?lang=de")
        s_ = j.get("state") or {}
        pruef(s_.get("arm_state") in ("armed", "arming") and req("/api/transport")[1].get("armed") is True, "Schutz wieder wie vorher (%s)" % s_.get("arm_state"))
        c, r = req("/api/move", {"dir": "right", "lang": "de"})
        pruef(c == 200, "Kopf lässt sich wieder bewegen (%d)" % c)
    finally:
        stoppe(p)
        log = "".join(open(os.path.join(tmp, f), errors="replace").read() for f in os.listdir(tmp) if f.startswith("log"))
        if "Traceback (most recent call last)" in log:
            print(log[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)


def browser(base, bilder, req):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                             color_scheme="dark", http_credentials={"username": "admin", "password": PASSWORT})
        pg = ctx.new_page()
        jsf = []
        pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))

        def weg():
            pg.evaluate("""() => { ['g2-ov', 'g2-spot', 'g2-bub', 'gd-card'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); });
              document.querySelectorAll('.g2m, #fx-card, #news-ov').forEach(e => e.remove()); }""")

        def klick(sel):                                  # über JavaScript: die Karte kann gerade eingeklappt neu gezeichnet werden
            pg.wait_for_selector(sel, state="attached", timeout=10000)
            pg.evaluate("""s => { const b = document.querySelector(s); let e = b; while (e) { if (e.tagName === 'DETAILS') e.open = true; e = e.parentElement; }
              b.scrollIntoView({block: 'center'}); b.click(); }""", sel)

        def foto(name, full=False):
            if bilder:
                pg.screenshot(path=os.path.join(bilder, "transport_%s.png" % name), full_page=full)
        pg.goto(base + "/", wait_until="domcontentloaded")
        pg.wait_for_function("() => { const b = document.getElementById('tp-band'); return b && !b.hidden; }", timeout=30000)
        weg(); pg.wait_for_timeout(600)
        pg.wait_for_function("() => (document.getElementById('b-arm') || {}).textContent.includes('Transport')", timeout=10000)
        r = pg.evaluate("""() => { const b = document.getElementById('tp-band'), c = document.getElementById('b-arm'), m = document.getElementById('mwb-sum');
            return {band: b.textContent, chip: (c ? c.textContent : '') + ' | ' + (m ? m.textContent : ''), w: document.documentElement.scrollWidth}; }""")
        pruef("Transportmodus aktiv" in r["band"] and "filmen geht weiter" in r["band"], "Live: Band «%s»" % r["band"][:90])
        pruef(r["chip"].count("🧳 Transport") >= 1 and "Wachsam" not in r["chip"], "Kopf: «%s» statt «Wachsam»" % r["chip"][:80])
        pruef(r["w"] <= 392, "kein waagrechtes Scrollen am Handy (%d px)" % r["w"])
        foto("live_band")
        # Einstellungen → Kameras & Kopf → Kopf (Servos) → «Servo-Bewegung & Sicherheit» (die Demo hat keinen Kopf: «Experte»)
        req("/api/ui_simple", {"on": False, "page": "settings"})
        pg.goto(base + "/settings", wait_until="domcontentloaded")
        pg.wait_for_function("""() => { const b = document.querySelector('#tp-box .tp-btn');
            return b && b.closest('details[data-view="sec:Camera / Servos"]') && b.closest('.tp-box.on'); }""", timeout=30000)
        weg()
        zeige = """() => { ['g2-ov', 'g2-spot', 'g2-bub', 'gd-card'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); });
            const b = document.getElementById('tp-box'), g = b.closest('details.grp'), h = b.closest('details.sub');
            if (g && !g.open) g.querySelector(':scope > summary').click(); if (h && !h.open) h.querySelector(':scope > summary').click();
            window.scrollBy(0, b.getBoundingClientRect().top - 330); return b.textContent; }"""
        t_ = pg.evaluate(zeige)
        pruef("Transportmodus" in t_ and "beenden" in t_, "Einstellungen: Knopf «Transportmodus beenden» im Kopf-Abschnitt (%s)" % t_[-60:])
        pg.wait_for_timeout(600); pg.evaluate(zeige); pg.wait_for_timeout(400); foto("einstellungen_an")
        klick("#tp-box .tp-btn")
        pg.wait_for_selector("#tp-dlg", timeout=5000)
        q = pg.inner_text("#tp-dlg")
        pruef("Kappe abgenommen?" in q, "Frage vor dem Ausschalten: «Kappe abgenommen?»")
        foto("frage_aus")
        pg.click("#tp-no")
        pruef(req("/api/transport")[1].get("on"), "Abbrechen lässt den Transportmodus an")
        klick("#tp-box .tp-btn"); pg.wait_for_selector("#tp-dlg"); pg.click("#tp-yes")
        pg.wait_for_function("() => document.getElementById('tp-band').hidden", timeout=10000)
        pruef(not req("/api/transport")[1].get("on"), "Ausschalten über die Frage")
        pg.wait_for_timeout(400)
        klick("#tp-box .tp-btn")
        pg.wait_for_selector("#tp-dlg")
        q = pg.inner_text("#tp-dlg")
        pruef("Kopf fährt in Grundstellung. Danach Kappe aufsetzen." in q, "Frage vor dem Einschalten: «%s»" % q.replace("\n", " ")[:80])
        foto("frage_ein")
        pg.click("#tp-yes")
        pg.wait_for_function("() => !document.getElementById('tp-band').hidden", timeout=10000)
        pg.wait_for_timeout(1500)
        pg.evaluate(zeige); pg.wait_for_timeout(400); foto("einstellungen_band")
        pg.evaluate("() => window.scrollTo(0, 0)"); pg.wait_for_timeout(300)
        foto("einstellungen_oben")
        # fr / it / rm: die Texte sind übersetzt
        for L, w_ in (("fr", "Mode transport"), ("it", "Modalità trasporto"), ("rm", "Modus da transport"), ("en", "Transport mode")):
            js = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(urllib.request.Request(base + "/i18n/%s.js" % L, headers={
                "Authorization": "Basic " + base64.b64encode(("admin:" + PASSWORT).encode()).decode()}), timeout=10).read().decode() if L != "en" else w_
            pruef(w_ in js, "Text in %s: «%s»" % (L, w_))
        # zum Schluss über das Band beenden
        pg.goto(base + "/", wait_until="domcontentloaded")
        pg.wait_for_selector("#tp-end", timeout=20000); weg()
        pg.click("#tp-end"); pg.wait_for_selector("#tp-dlg"); pg.click("#tp-yes")
        pg.wait_for_function("() => document.getElementById('tp-band').hidden", timeout=10000)
        pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])
        ctx.close(); br.close()


def main():
    ap = argparse.ArgumentParser(description="Transportmodus")
    ap.add_argument("--datei", default="")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--nur", choices=("innen", "web"), default="")
    ap.add_argument("--innen", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else neueste()
    if a.innen:
        return innen(datei)
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    rc = 0
    if a.nur in ("", "innen"):
        print("== 1. im Prozess (falscher PCA9685)", flush=True)
        home = tempfile.mkdtemp(prefix="mw_transport_home_")
        try:
            rc = subprocess.run([sys.executable, os.path.abspath(__file__), "--innen", "--datei", datei], env=dict(os.environ, HOME=home),
                                cwd=home, timeout=600).returncode
        finally:
            shutil.rmtree(home, ignore_errors=True)
        if rc:
            FEHLER.append("Innen-Test")
    if a.nur in ("", "web"):
        print("== 2. Programm (Demo) über HTTP und im Browser", flush=True)
        web(datei, a.bilder)
    print("Transportmodus-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d): %s" % (len(FEHLER), FEHLER[:6])))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
