#!/usr/bin/env python3
"""Test «🔥 Glut-Wächter» (MoveEye Teil 639zzzw) – mit erfundenen Wärmebildern (80 × 62, °C pro Pixel), ohne Hardware.

  A) im eigenen Prozess (gebaute Datei geladen, Kopf ohne Servo-Schleife, Wärmebild-Modul ersetzt):
     Feuerstelle merken (ohne Feuer: nichts gemerkt; mit Feuer: Kopfstellung + Bereich), «aus» unter der Schwelle,
     «Glut» darüber, 400+ am Ende des Messbereichs, der Kopf fährt hin und zurück, Wache: wieder heiss = Alarm (Ton + Push),
     neuer heisser Punkt daneben = Alarm, Flackern unter der Marge = kein Alarm, Abkühlzeit, Transportmodus (beide Arten):
     kein Kopf-Fahren, Alarm auf Personen geht vor (Wache wartet 30 s), Sensor fehlt / liefert nichts / nur Farben: klare
     Meldung, Umriss im Live-Wärmebild, Texte in 5 Sprachen.
  B) --browser: MoveEye (Demo, eigener Daten-Ordner) mit erfundenem Thermal-90, Seite 390 px dunkel: merken, «aus»,
     «Glut», Bilder nach --bilder (glut_aus.png, glut_glut.png, glut_waermebild.png, glut_live.png).

  python3 werkzeuge/glut_test.py [--datei X.py] [--browser] [--bilder ORDNER]
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
FEHLER = []

TEIL_A = r'''
import json, os, sys, threading, time
import numpy as np
ns = {"__name__": "mw_glut_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
C, S, G = ns["CFG"], ns["STATE"], ns["GLUT"]
out = {}
SC = {"fire": 15.0, "spot": None, "kind": "c"}          # the scene: fire temperature, a new hot spot, kind c = °C / u8 = colours
def scene():
    f = np.full((62, 80), 14.0, np.float32) + np.random.default_rng(int(time.time() * 1000) % 99999).normal(0, 0.15, (62, 80)).astype(np.float32)
    if abs(float(ns["servo_pos"]()[0]) - 60.0) <= 2.0:   # the fire is in view only when the head looks at pan 60 %
        f[30:34, 40:45] = SC["fire"]; f[29, 42] = SC["fire"] * 0.7
        if SC["spot"]:
            f[SC["spot"][1], SC["spot"][0]] = SC["spot"][2]; f[SC["spot"][1], SC["spot"][0] + 1] = SC["spot"][2] - 5
    return (np.clip(f, 0, 255).astype(np.uint8)[:, :, None].repeat(3, 2)) if SC["kind"] == "u8" else f
class FT:
    frame = None; t = 0.0
TH = FT()
def feed():
    while True:
        if SC["kind"] != "none":
            TH.frame = scene(); TH.t = time.time()
        time.sleep(0.07)
threading.Thread(target=feed, daemon=True).start()
ns["THERMAL"] = TH
sounds, pushes = [], []
ns["sound_play"] = lambda kind=None, seconds=None, volume=None, reason="": (sounds.append((kind, round(volume or 0), reason)), (True, ""))[1]
class N:
    def alert(self, title, text, frame=None):
        pushes.append((title, text, None if frame is None else list(frame.shape)))
class W:
    notifier = N()
ns["WATCH_REF"]["w"] = W()
ns["save_settings"] = lambda *a, **k: None
ns["SRV"]["pos"] = None; ns["SRV"]["started"] = False
C.update(thermal_source="senxor", lang="de", pan=20.0, tilt=50.0, glut_spot={}, glut_watch=False, mode="fire", kopf_transport=False,
         servo_estop=False, siren_volume=80)
S.update(persons=0, tracking=False)
moves = []
_goto = ns["servo_goto"]
def goto(p, t, who="", **k):
    moves.append((round(p, 1), round(t, 1), who)); return _goto(p, t, who, **k)
ns["servo_goto"] = goto
res = lambda r: ns["glut_result_text"](r, "de")
# 1 teach
SC["fire"] = 300.0
ok, msg, kw = ns["glut_teach"]("test")
out["teach_nofire"] = [ok, ns["trf"](msg, "de", **kw)]
C["pan"] = 60.0
ok, msg, kw = ns["glut_teach"]("test")
out["teach"] = [ok, ns["trf"](msg, "de", **kw), C["glut_spot"]]
# 2 out / embers, the head goes there and back
C["pan"] = 20.0; moves.clear(); SC["fire"] = 35.0
r = ns["glut_check"]("test"); out["aus"] = [r["kind"], r["max"], res(r), list(moves), C["pan"]]
moves.clear(); SC["fire"] = 180.0
r = ns["glut_check"]("test"); out["glut"] = [r["kind"], r["max"], res(r), list(moves)]
C["glut_off_c"] = 30.0; SC["fire"] = 35.0
r = ns["glut_check"]("test"); out["schwelle"] = [r["kind"], res(r)]; C["glut_off_c"] = 40.0
SC["fire"] = 520.0
r = ns["glut_check"]("test"); out["over"] = [r["kind"], r["max"], r["over"], res(r)]
import cv2
im = cv2.imdecode(np.frombuffer(G["jpg"], np.uint8), cv2.IMREAD_COLOR); out["jpg"] = list(im.shape)
# 3 night watch
ns["glut_set_watch"](True, "test")
SC["fire"] = 35.0; ns["glut_check"]("watch", True); out["w1"] = [len(sounds), len(pushes), G["low"]]
SC["fire"] = 45.0; ns["glut_check"]("watch", True); out["w_flicker"] = [len(sounds), len(pushes)]
SC["fire"] = 90.0; ns["glut_check"]("watch", True); time.sleep(0.3); out["w_reflare"] = [len(pushes), pushes[-1] if pushes else None, sounds[:3]]
SC["fire"] = 140.0; ns["glut_check"]("watch", True); out["w_cool"] = len(pushes)
SC["fire"] = 35.0; SC["spot"] = (10, 8, 95.0); ns["glut_check"]("watch", True); time.sleep(0.3)
out["w_spot"] = [len(pushes), pushes[-1] if pushes else None, (G["last"] or {}).get("new")]
SC["spot"] = None
# 4 glut_tick: due -> a check in the background; persons -> it waits 30 s
G["next"] = 0.0; S["persons"] = 1; C["pan"] = 20.0; moves.clear()
ns["glut_tick"](); out["tick_alarm"] = [G["note"], round(G["next"] - time.time()), list(moves), G["busy"]]
r = ns["glut_check"]("test"); out["btn_alarm"] = [r["kind"], res(r), C["pan"]]
S["persons"] = 0; G["next"] = 0.0
ns["glut_tick"](); time.sleep(0.2)
t0 = time.time()
while G["busy"] and time.time() - t0 < 15: time.sleep(0.1)
out["tick"] = [len(moves) >= 1, (G["last"] or {}).get("auto"), round((G["next"] - time.time()) / 60.0)]
# 5 transport mode: never move the head
for how in ("kopf", "mode"):
    C["pan"] = 20.0; moves.clear()
    if how == "kopf": C["kopf_transport"] = True
    else: C["kopf_transport"] = False; C["mode"] = "transport"
    r = ns["glut_check"]("test"); out["tp_" + how] = [r["kind"], res(r), list(moves), C["pan"]]
C["pan"] = 60.0; SC["fire"] = 35.0
r = ns["glut_check"]("test"); out["tp_at"] = [r["kind"], res(r), list(moves)]
C.update(mode="fire", kopf_transport=False)
# 6 sensor missing / no picture / colours only
C["thermal_source"] = ""; r = ns["glut_check"]("test"); out["s_none"] = [r["kind"], res(r)]
C["thermal_source"] = "senxor"; SC["kind"] = "none"; TH.frame = None; S["thermal"] = "not found: [Errno 2] No such file or directory: '/dev/spidev0.0'"
r = ns["glut_check"]("test"); out["s_nopic"] = [r["kind"], res(r)]
ok, msg, kw = ns["glut_teach"]("test"); out["s_teach"] = [ok, ns["glut_err_tr"](msg, "de", **kw)]
SC["kind"] = "u8"; r = ns["glut_check"]("test"); out["s_u8"] = [r["kind"], res(r)]
SC["kind"] = "c"
# 7 live thermal picture: outline while the head is at the spot
tc = ns["ThermalCam"].__new__(ns["ThermalCam"]); tc.frame = scene(); tc.t = time.time()
C.update(thermal_zoom=100, thermal_dx=0, thermal_dy=0, thermal_hot=False, thermal_alpha=0.6, sim_on=False)
base = ns["_glut_overlay_base"](tc, np.zeros((360, 640, 3), np.uint8))
mine = ns["ThermalCam"].overlay(tc, np.zeros((360, 640, 3), np.uint8))
out["overlay"] = int((np.abs(mine.astype(int) - base.astype(int)).sum(axis=2) > 60).sum())
C["pan"] = 20.0; tc.frame = scene()
out["overlay_away"] = int((np.abs(ns["ThermalCam"].overlay(tc, np.zeros((360, 640, 3), np.uint8)).astype(int)
                           - ns["_glut_overlay_base"](tc, np.zeros((360, 640, 3), np.uint8)).astype(int)).sum(axis=2) > 60).sum())
# 8 texts
r = {"kind": "glow", "max": 180.0, "over": False}
out["txt"] = {L: [ns["glut_result_text"](r, L), ns["glut_result_text"]({"kind": "out", "max": 38.0}, L), ns["tr"]("Only the surface: embers under ash or soil can be missed. Not a substitute for putting the fire out properly.", L)] for L in ("de", "en", "fr", "it", "rm")}
out["state"] = sorted(ns["mode_state"]()["glut"].keys())
out["alm"] = ns["glut_alm_link"]()
out["selftest"] = ns["glut_selftest"]()
print("ERG " + json.dumps(out, ensure_ascii=False, default=str))
os._exit(0)
'''


def ok(bed, text):
    print(("  ok     " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


def teil_a(datei, tmp):
    print("A) Glut-Wächter im eigenen Prozess (erfundene Wärmebilder)", flush=True)
    home = os.path.join(tmp, "a"); os.makedirs(home)
    r = subprocess.run([sys.executable, "-c", TEIL_A, datei], capture_output=True, text=True, timeout=600,
                       env=dict(os.environ, MOTIONWATCH_HOME=home), cwd=tmp)
    erg = next((json.loads(ln[4:]) for ln in r.stdout.splitlines() if ln.startswith("ERG ")), None)
    if erg is None:
        print((r.stdout + r.stderr)[-3000:])
        ok(False, "Teil A lief nicht durch")
        return
    e = erg
    ok(e["teach_nofire"][0] is False and "Kein Feuer" in e["teach_nofire"][1], "merken ohne Feuer im Bild: nichts gemerkt (%s)" % e["teach_nofire"][1])
    sp = e["teach"][2]
    ok(e["teach"][0] and sp.get("pan") == 60.0 and sp["box"][0] < 40 / 80 and sp["box"][0] + sp["box"][2] > 45 / 80 and "300 °C" in e["teach"][1],
       "merken: Kopf 60 %% + Bereich um das Feuer (%s, %s)" % (sp.get("box"), e["teach"][1]))
    a = e["aus"]
    ok(a[0] == "out" and 34 <= a[1] <= 36 and a[2] == "✅ aus – höchstens 35 °C", "unter 40 °C: «%s»" % a[2])
    ok(a[3] and a[3][0][0] == 60.0 and a[3][-1][0] == 20.0 and a[4] == 20.0, "Kopf fährt zur Feuerstelle und zurück (%s)" % a[3])
    g = e["glut"]
    ok(g[0] == "glow" and g[2] == "⚠️ Glut noch 180 °C – mehr Wasser, umrühren", "über der Schwelle: «%s»" % g[2])
    ok(e["schwelle"][0] == "glow", "eigene Schwelle 30 °C: 35 °C ist Glut (%s)" % e["schwelle"][1])
    ok(e["over"][0] == "glow" and e["over"][1] == 400.0 and e["over"][2] and "400+" in e["over"][3], "über dem Messbereich: «%s»" % e["over"][3])
    ok(e["jpg"] == [496, 640, 3], "Wärmebild mit Umriss (%s)" % e["jpg"])
    ok(e["w1"][:2] == [0, 0] and 34 <= e["w1"][2] <= 36, "Wache: kalt, kein Alarm (tiefster Wert %s)" % e["w1"][2])
    ok(e["w_flicker"] == [0, 0], "Wache: 45 °C (unter 35 + 15) = kein Alarm")
    p = e["w_reflare"]
    ok(p[0] == 1 and "wieder heiss" in p[1][1] and "90 °C" in p[1][1] and p[1][2] == [496, 640, 3], "wieder heiss: Push mit Wärmebild (%s)" % (p[1][1] if p[1] else ""))
    ok(len(p[2]) >= 1 and p[2][0][0] == "beep4" and p[2][0][2] == "fire" and (len(p[2]) < 2 or p[2][1][1] > p[2][0][1]), "leiser steigender Ton (%s)" % p[2])
    ok(e["w_cool"] == 1, "zweites Aufflammen innerhalb von 10 min: kein zweiter Push")
    s = e["w_spot"]
    ok(s[0] == 2 and "Neuer heisser Punkt" in s[1][1] and "95 °C" in s[1][1] and s[2] and abs(s[2][0][0] - 10.5 / 80) < 0.02, "neuer heisser Punkt daneben: Push (%s, %s)" % (s[1][1] if s[1] else "", s[2]))
    t = e["tick_alarm"]
    ok(t[0] == "alarm" and 28 <= t[1] <= 30 and t[2] == [] and not t[3], "Wache bei Personen-Alarm: wartet 30 s, Kopf bleibt (%s)" % t)
    ok(e["btn_alarm"][0] == "err" and "Alarm geht vor" in e["btn_alarm"][1] and e["btn_alarm"][2] == 20.0, "Knopf bei Alarm: «%s»" % e["btn_alarm"][1])
    ok(e["tick"][0] and e["tick"][1] is True and e["tick"][2] == 2, "Wache fällig: Prüfung im Hintergrund, nächste in 2 min (%s)" % e["tick"])
    for k in ("tp_kopf", "tp_mode"):
        ok(e[k][0] == "err" and "Transportmodus" in e[k][1] and e[k][2] == [] and e[k][3] == 20.0, "%s: kein Kopf-Fahren («%s»)" % (k, e[k][1]))
    ok(e["tp_at"][0] == "out" and e["tp_at"][2] == [], "Transportmodus, Kopf schon an der Feuerstelle: gemessen ohne Fahren (%s)" % e["tp_at"][1])
    ok(e["s_none"][1] == "⚠ Kein Wärmebild gewählt (Einstellungen → Wärmebild).", "kein Wärmebild gewählt: «%s»" % e["s_none"][1])
    ok(e["s_nopic"][0] == "err" and e["s_nopic"][1].startswith("⚠ Das Wärmebild liefert kein Bild: not found"), "Modul fehlt: «%s»" % e["s_nopic"][1])
    ok(e["s_teach"][0] is False and "kein Bild" in e["s_teach"][1], "merken ohne Modul: «%s»" % e["s_teach"][1])
    ok(e["s_u8"][0] == "err" and "keine Temperaturen" in e["s_u8"][1], "Quelle nur mit Farben: «%s»" % e["s_u8"][1])
    ok(e["overlay"] > 200 and e["overlay_away"] == 0, "Live-Wärmebild: Umriss an der Feuerstelle (%d Pixel), weg davon keiner" % e["overlay"])
    for L, (gl, au, note) in e["txt"].items():
        ok("180 °C" in gl and "38 °C" in au and len(note) > 40 and (L == "en" or note != e["txt"]["en"][2]), "%s: «%s» · «%s»" % (L, gl, au))
    ok({"taught", "watch", "last", "alm", "transport"} <= set(e["state"]) and e["alm"].startswith("/almanach/#a"), "Zustand mit dem Modus, Almanach-Link %s" % e["alm"])
    ok(bool(e["selftest"]), "Selbsttest-Funktion: " + str(e["selftest"]))


WRAP = r'''
import json, os, sys, time
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = """
import numpy as _np
class _GlutFake:                                      # the test: a Thermal-90 that delivers made-up °C pictures from a file
    size = (80, 62)
    def read(self):
        time.sleep(0.07)
        try:
            sc = json.load(open(os.environ["MW_GLUT_SCENE"]))
        except Exception:
            sc = {"fire": 15}
        f = _np.full((62, 80), 13.0, _np.float32) + _np.random.normal(0, 0.15, (62, 80)).astype(_np.float32)
        f[44:62, :] += 4.0
        f[30:35, 38:45] = sc["fire"]; f[29, 40:43] = sc["fire"] * 0.6
        if sc.get("spot"):
            f[12:14, 14:16] = sc["spot"]
        return True, f
    def release(self):
        pass
_glut_os = open_source
def open_source(spec, thermal=False):
    if thermal and spec == "senxor":
        return _GlutFake(), spec, "Thermal-90 (Test)", ""
    return _glut_os(spec, thermal)
"""
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
exec(compile(src, D, "exec"), {"__name__": "__main__", "__file__": D})
'''
PW = "glut-test-pw-1"


def teil_b(datei, tmp, bilder):
    print("B) Seite 390 px dunkel (MoveEye Demo, erfundener Thermal-90)", flush=True)
    from playwright.sync_api import sync_playwright
    os.makedirs(bilder, exist_ok=True)
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    scene = os.path.join(tmp, "scene.json")
    json.dump({"fire": 260}, open(scene, "w"))
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "thermal_source": "senxor", "thermal_on": False, "mode": "fire", "theme": "dark",
          "detection_on": False, "track_person": False, "track_motion": False, "patrol": False}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=dict(os.environ, MW_GLUT_SCENE=scene))
    base = "http://127.0.0.1:%d" % port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    auth = {"Authorization": "Basic " + base64.b64encode(("admin:" + PW).encode()).decode()}

    def api(data=None):
        r = urllib.request.Request(base + "/api/glut", data=json.dumps(data).encode() if data is not None else None,
                                   headers=dict(auth, **{"Content-Type": "application/json"}))
        try:
            with op.open(r, timeout=90) as x:
                return json.loads(x.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(3)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                                 color_scheme="dark", http_credentials={"username": "admin", "password": PW}, locale="de-CH")
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base + "/protect", wait_until="domcontentloaded")
            pg.wait_for_selector("#glut-box:not([hidden])", state="attached", timeout=60000)
            pg.wait_for_timeout(2500)

            def weg():                                    # the coach-mark tour of the page (516, #g2-ov over everything): end it
                pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")

            def klick(text):
                weg(); pg.locator("#glut-box button", has_text=text).click()
            weg()
            if not pg.evaluate("() => document.getElementById('pr-card').open"):
                pg.locator("#pr-card > summary").click()
            pg.wait_for_timeout(500)

            def show(name):
                weg(); b = pg.locator("#glut-box")
                b.scroll_into_view_if_needed()
                pg.wait_for_timeout(600)
                b.screenshot(path=os.path.join(bilder, name))
            klick("Feuerstelle merken")
            pg.wait_for_function("() => (document.querySelector('#glut-box .mut') || {}).textContent.includes('Feuerstelle')", timeout=60000)
            json.dump({"fire": 34}, open(scene, "w"))
            klick("Ist das Feuer aus?")
            pg.wait_for_selector("#glut-box .gl-res.out", timeout=60000)
            txt = pg.locator("#glut-box .gl-res").inner_text()
            ok(txt.startswith("✅ aus – höchstens 34 °C"), "Karte «aus»: %s" % txt.splitlines()[0])
            show("glut_aus.png")
            json.dump({"fire": 180, "spot": 85}, open(scene, "w"))
            klick("Ist das Feuer aus?")
            try:
                pg.wait_for_selector("#glut-box .gl-res.glow", timeout=60000)
            except Exception:
                print("  Karte: " + pg.locator("#glut-box").inner_text().replace("\n", " / ")[:400]); raise
            txt = pg.locator("#glut-box .gl-res").inner_text()
            ok(txt.startswith("⚠️ Glut noch 180 °C – mehr Wasser, umrühren"), "Karte «Glut»: %s" % txt.splitlines()[0])
            pg.wait_for_function("() => { const i = document.querySelector('#glut-box img'); return i && i.complete && i.naturalWidth > 0; }", timeout=20000)
            show("glut_glut.png")
            pg.locator("#glut-box img").screenshot(path=os.path.join(bilder, "glut_waermebild.png"))
            note = pg.locator("#glut-box .gl-note").inner_text()
            href = pg.locator("#glut-box .gl-note a").get_attribute("href")
            ok("Nur die Oberfläche" in note and href.startswith("/almanach/#a"), "ehrlicher Hinweis + Almanach-Link (%s)" % href)
            w = pg.evaluate("() => document.documentElement.scrollWidth")
            ok(w <= 390, "keine waagrechte Bildlaufleiste bei 390 px (%d)" % w)
            # the live thermal picture with the outline (the head stands at the fire spot)
            api({"action": "set", "off_c": 40})
            r = urllib.request.Request(base + "/api/set", data=json.dumps({"key": "thermal_on", "value": True}).encode(),
                                       headers=dict(auth, **{"Content-Type": "application/json"}))
            op.open(r, timeout=20).read()
            pg.goto(base + "/", wait_until="domcontentloaded")
            pg.wait_for_timeout(7000)
            weg()
            pg.locator("#video").first.screenshot(path=os.path.join(bilder, "glut_live.png"))
            # other languages: the card renders
            for L, word in (("fr", "Gardien des braises"), ("it", "Guardiano delle braci"), ("rm", "Guardian da la brasa"), ("en", "Fire watch")):
                pg.evaluate("async l => { try { localStorage.setItem('mw-lang', l); } catch (e) {} await fetch('/api/ui', {method: 'POST', "
                            "headers: {'Content-Type': 'application/json'}, body: JSON.stringify({set: {'mw-lang': l}})}); }", L)
                pg.goto(base + "/protect", wait_until="domcontentloaded")
                try:
                    pg.wait_for_function("w => (document.getElementById('glut-box') || {}).textContent.includes(w)", arg=word, timeout=30000)
                    ok(True, "%s: Karte «%s»" % (L, word))
                except Exception:
                    ok(False, "%s: Karte «%s» fehlt (%s)" % (L, word, pg.evaluate("() => (document.getElementById('glut-box')||{}).textContent")[:120]))
            ok(not errs, "keine JS-Fehler %s" % errs[:3])
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(10)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "glut_bilder"))
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("Glut-Wächter-Test · " + os.path.basename(datei), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_glut_")
    try:
        teil_a(datei, tmp)
        if a.browser:
            teil_b(datei, tmp, a.bilder)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Glut-Wächter-Test: " + ("OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
