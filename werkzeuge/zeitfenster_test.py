#!/usr/bin/env python3
"""Test «⏪ Zeitfenster» (Teil 639zzzz): Damals / Jetzt pro Blickrichtung, Änderungen, «wann geändert?», Ausdünnen.

A) im eigenen Prozess (falsche Kamera / falscher Kopf, eigener Ordner):
   1. Sammeln ohne Kopfbewegung: Halt der Runde, stündlich bei stillem Kopf, Zeitraffer-Foto mit Richtung; nichts bei Alarm,
      fahrendem Kopf oder zu kurzem Abstand; nie ein Befehl an die Servos, Schwenk / Neigung bleiben.
   2. Suchen nach Richtung (±3°, über ±180°) und Zeit (1 h · gestern · 1 Woche · 1 Monat · 1 Jahr).
   3. Änderungen: ein hingestellter Gegenstand wird gefunden, eine Helligkeitsänderung des ganzen Bilds nicht, das Band oben zählt nicht;
      Bezug von derselben Tageszeit.
   4. Binäre Suche findet den Moment der Änderung (wenige Vergleiche).
   5. Ausdünnen (24 h alles, bis 7 Tage 1 pro Stunde, dann 1 pro Tag, je Richtung) und Obergrenze (klein simuliert, älteste zuerst);
      Zeitraffer-Fotos und Aufnahmen bleiben.
B) MoveEye mit der Demo (eigener Ordner, freier Port, Demo-Uhr fest): nur Administrator (403 für «nur ansehen», 401 ohne Anmeldung),
   Browser Handy 390 px (dunkel) und PC: Knopf ⏪, Leiste unter dem Bild, Bild von «gestern» mit Datum, Trennbalken ziehen, Markierung des
   hingestellten Gegenstands, Antippen = «Geändert zwischen …» + Zeitleiste, nichts überdeckt Knöpfe / CPU-Chip / Kompass / Lupe /
   kleines Bild / Joystick, Richtung ohne Bild = klare Meldung, keine JavaScript-Fehler.

  python3 werkzeuge/zeitfenster_test.py [--datei X.py] [--nur a|b] [--bilder ORDNER]
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
PW = "Zf-" + base64.b16encode(os.urandom(5)).decode().lower()
FEHLER = []


def ok(c, text):
    print(("  ok    " if c else "  FEHLER ") + text, flush=True)
    if not c:
        FEHLER.append(text)


def warte(fn, s=10.0):
    t = time.time() + s
    while time.time() < t:
        r = fn()
        if r:
            return r
        time.sleep(0.05)
    return fn()


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    import cv2
    import numpy as np
    print("A) im eigenen Prozess", flush=True)
    home = tempfile.mkdtemp(prefix="mw_zf_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_zf_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["log_event"] = lambda *a, **k: None
    CFG, STATE, KOPF, SRV, ZF = ns["CFG"], ns["STATE"], ns["KOPF"], ns["SRV"], ns["ZF"]
    rec = os.path.join(home, "rec"); CFG["record_dir"] = rec; ZF["items"] = None
    ok(ns["zf_selftest"]().startswith("compare"), "Selbsttest zf_selftest")
    moves = []
    for n in ("servo_goto", "kopf_move", "move_camera"):
        ns[n] = (lambda n_: lambda *a, **k: moves.append(n_) or True)(n)
    rng = np.random.default_rng(1)
    szene = cv2.GaussianBlur(rng.integers(30, 220, (540, 960, 3), dtype=np.uint8), (0, 0), 4)
    CFG.update(pan=50.0, tilt=50.0, zf_on=True, zf_still_min="60", servo_range=180.0, pan_servo_range=180.0)
    STATE["tracking"] = False

    def kopf(pan_pct, tilt_pct, still_s, runde):
        CFG["pan"], CFG["tilt"] = pan_pct, tilt_pct
        SRV["pos"] = [pan_pct, tilt_pct]; SRV["vel"] = [0.0, 0.0]; SRV["arrive_t"] = time.time() - still_s
        KOPF["round_on"] = runde; STATE["patrol_moving"] = False
        ZF["chk"] = 0.0

    def zahl():
        warte(lambda: not ZF["saving"], 5)
        return len(ns["zf_items"]())
    # 1. collecting
    kopf(50.0, 50.0, 3.0, True)
    SRV["vel"] = [2.0, 0.0]
    ns["zf_feed"](szene, False)
    ok(zahl() == 0, "Kopf fährt: kein Bild")
    kopf(50.0, 50.0, 3.0, True)
    ns["zf_feed"](szene, True)                                         # (the next call would wait a second: chk reset below)
    ok(zahl() == 0, "Alarm / Person: kein Bild")
    ZF["chk"] = 0.0; ns["zf_feed"](szene, False)
    ok(zahl() == 1 and ns["zf_items"]()[-1][4] == "stop", "Halt der Runde: ein Bild (Quelle «stop»)")
    kopf(50.0, 50.0, 3.0, True); ns["zf_feed"](szene, False)
    ok(zahl() == 1, "gleicher Halt gleich wieder: kein zweites Bild (Abstand pro Richtung)")
    kopf(72.0, 50.0, 3.0, True); ns["zf_feed"](szene, False)          # +39.6°
    ok(zahl() == 2, "anderer Halt der Runde: eigenes Bild")
    kopf(30.0, 40.0, 10.0, False); ns["zf_feed"](szene, False)
    ok(zahl() == 2, "ohne Runde, Kopf erst 10 s still: noch kein Stundenbild")
    kopf(30.0, 40.0, 61.0, False); ns["zf_feed"](szene, False)
    ok(zahl() == 3 and ns["zf_items"]()[-1][4] == "hour", "Kopf steht still: ein Stundenbild")
    CFG["zf_still_min"] = "off"; kopf(10.0, 40.0, 120.0, False); ns["zf_feed"](szene, False)
    ok(zahl() == 3, "«Bild, wenn der Kopf still steht: aus»: kein Bild")
    # the interval (Besitzer 15.11.2026): 1 / 5 / 10 / 15 / 30 / 60 min - the clock moved back by shifting the last still
    def frueher(s_):
        ns["zf_items"]()[-1][0] -= s_
        for k_ in ZF["last"]:
            ZF["last"][k_] -= s_
    for m, (zu_frueh, genug) in (("5", (200, 150)), ("1", (40, 25)), ("30", (1500, 400))):
        CFG["zf_still_min"] = m
        kopf(10.0 + float(m), 40.0, 120.0, False); n0 = zahl(); ns["zf_feed"](szene, False)
        ok(zahl() == n0 + 1, f"alle {m} Min.: erstes Bild in der neuen Richtung")
        frueher(zu_frueh); kopf(10.0 + float(m), 40.0, 120.0, False); ns["zf_feed"](szene, False)
        ok(zahl() == n0 + 1, f"alle {m} Min.: nach {zu_frueh} s noch kein zweites Bild")
        frueher(genug); kopf(10.0 + float(m), 40.0, 120.0, False); ns["zf_feed"](szene, False)
        ok(zahl() == n0 + 2, f"alle {m} Min.: nach {zu_frueh + genug} s das nächste Bild")
    CFG["zf_still_min"] = "1"
    kopf(30.0, 40.0, 120.0, False); n0 = zahl(); ns["zf_feed"](szene, True)
    ok(zahl() == n0, "jede Minute, aber Alarm / Aufnahme: kein Bild")
    STATE["tracking"] = True; ZF["chk"] = 0.0; ns["zf_feed"](szene, False); STATE["tracking"] = False
    ok(zahl() == n0, "jede Minute, aber Folgen: kein Bild")
    ok([c for c, _l in ns["text_choice_pairs"]("zf_still_min")] == ["off", "1", "5", "10", "15", "30", "60"]
       and ns["text_choice_pairs"]("zf_still_min")[2][1] == ns["tr"]("every %s min") % "5", "Auswahl: aus / 1 / 5 / 10 / 15 / 30 / 60 Min.")
    ok(all(ns["tr"](k, L) != k or L == "en" for k in ("Picture while the head stands still", "every minute", "every %s min",
                                                         "about %s MB per day and direction (thinned out later)") for L in ("de", "fr", "it", "rm")),
       "Texte in fünf Sprachen")
    avg = sum(x[5] for x in ns["zf_items"]()[-200:]) / len(ns["zf_items"]()[-200:])
    CFG["zf_still_min"] = "1"; e1 = ns["zf_estimate_mb"](); CFG["zf_still_min"] = "60"; e60 = ns["zf_estimate_mb"]()
    CFG["zf_still_min"] = "off"; eo = ns["zf_estimate_mb"]()
    ok(abs(e1 - avg * 1440 / 1048576) < 0.1 and abs(e60 - avg * 24 / 1048576) < 0.1 and eo is None,
       f"Schätzung aus der echten Bildgrösse: 1 Min. {e1} MB, 60 Min. {e60} MB pro Tag und Richtung, aus = keine")
    # migration of the old switch «every hour»
    for old, want in (({"zf_hourly": True}, "60"), ({"zf_hourly": False}, "off"), ({"zf_hourly": False, "zf_still_min": "5"}, "5"), ({}, "5")):
        CFG["zf_still_min"] = "5"; ns["_settings_migrations"](old)
        ok(CFG["zf_still_min"] == want, f"Übernahme {old} -> «{CFG['zf_still_min']}»")
    CFG["zf_still_min"] = "60"; ns["apply_settings"]({"cfg": {"zf_hourly": False}})
    ok(CFG["zf_still_min"] == "off" and "zf_hourly" not in CFG and "zf_hourly" not in ns["settings_data"]()["cfg"],
       "alte Datei mit «jede Stunde: aus» -> «aus», der alte Schlüssel wird nicht mehr gespeichert")
    CFG["zf_still_min"] = "60"
    CFG.update(timelapse_pan=60.0, timelapse_tilt=55.0, timelapse_on=True)
    kopf(60.0, 55.0, 0.0, False)
    tl = ns["Timelapse"](); tl._shoot(szene, time.time())
    it = warte(lambda: ns["zf_items"]()[-1] if ns["zf_items"]()[-1][4] == "tl" else None, 5)
    tlname = STATE.get("timelapse_last")
    ok(bool(it) and abs(it[1] - 18.0) < 0.01 and abs(it[2] - 9.0) < 0.01 and tlname and os.path.isfile(os.path.join(rec, "timelapse", tlname)),
       f"Zeitraffer-Foto: auch als Zeitfenster-Bild mit seiner Richtung 18° / 9° ({it and it[1:3]}), Original bleibt")
    rows = []
    for f in glob.glob(os.path.join(rec, "zeitfenster", "idx_*.jsonl")):
        rows += [json.loads(x) for x in open(f, encoding="utf-8")]
    ok(len(rows) == len(ns["zf_items"]()) >= 4 and all(set(r) >= {"t", "p", "q", "f", "s", "c"} for r in rows) and any(r.get("tl") == tlname for r in rows),
       "Index pro Tag (JSONL): Zeit, Schwenk, Neigung, Kamera, Quelle; Zeitraffer mit Namen")
    im = cv2.imread(os.path.join(rec, "zeitfenster", rows[0]["f"]))
    ok(im is not None and im.shape[1] == 960 and os.path.getsize(os.path.join(rec, "zeitfenster", rows[0]["f"])) < 400000,
       f"klein gespeichert ({None if im is None else im.shape[1]} px)")
    ok(not moves and CFG["pan"] == 60.0, f"nie ein Befehl an den Kopf ({moves})")
    # 2. lookup by direction and time
    shutil.rmtree(os.path.join(rec, "zeitfenster")); ZF["items"] = None
    now = time.time()
    ages = (3600, 86400, 604800, 2592000, 31536000)
    for i, a in enumerate(ages):
        ns["zf_save"](szene, (178.5, 1.0), "hour", t=now - a)
        ns["zf_save"](szene, (30.0, 1.0), "hour", t=now - a - 600)
    its = ns["zf_dir_items"](-179.0, 2.5)
    ok(len(its) == 5 and all(abs(x[1] - 178.5) < 0.01 for x in its), "Richtung ±3° auch über ±180° (178.5° = -179°), andere Richtung nicht dabei")
    ok(all(abs(ns["zf_nearest"](its, now - a)[0] - (now - a)) < 2 for a in ages), "1 h · gestern · 1 Woche · 1 Monat · 1 Jahr: das passende Bild")
    ok(ns["zf_dir_items"](-170.0, 1.0) == [], "Richtung ohne Bild: leer")
    # 3. changes
    shutil.rmtree(os.path.join(rec, "zeitfenster")); ZF["items"] = None; ZF["cache"].clear()
    obj = szene.copy(); cv2.rectangle(obj, (600, 300), (700, 400), (30, 30, 240), -1)
    dunkel = np.clip(szene.astype(np.float32) * 0.6 + 5, 0, 255).astype(np.uint8)
    a = ns["zf_save"](szene, (0, 0), "hour", t=now - 86400)
    b = ns["zf_save"](obj, (0.5, 0), "hour", t=now - 60)
    c = ns["zf_save"](dunkel, (0, 0.5), "hour", t=now - 30)
    r = ns["zf_diff"](a["f"], b["f"])
    bx = r.get("boxes") or [[0, 0, 0, 0]]
    ok(r.get("ok") and len(r["boxes"]) == 1 and abs(bx[0][0] - 600 / 960) < 0.05 and abs(bx[0][1] - 300 / 540) < 0.06 and abs(bx[0][2] - 100 / 960) < 0.05,
       f"hingestellter Gegenstand gefunden ({bx})")
    r = ns["zf_diff"](a["f"], c["f"])
    ok(r.get("ok") and r["boxes"] == [], f"ganzes Bild 40 % dunkler: keine Markierung ({r.get('boxes')})")
    ok(ns["zf_diff"](a["f"], b["f"], top=75)["boxes"] == [], "Band oben 75 %: der Gegenstand liegt darin, keine Markierung")
    d = ns["zf_save"](obj, (0, 0), "hour", t=now - 86400 * 3 + 300)
    e = ns["zf_save"](szene, (0, 0), "hour", t=now - 86400 * 3 + 9000)
    ref, same = ns["zf_reference"](ns["zf_item"](e["f"]), now)
    ok(same and ref[3] == d["f"], "Bezug: ein Bild derselben Tageszeit (±1 h) nahe am gewählten")
    # 4. binary search
    shutil.rmtree(os.path.join(rec, "zeitfenster")); ZF["items"] = None; ZF["cache"].clear()
    st = [ns["zf_save"](obj if i >= 23 else szene, (0, 0), "hour", t=now - (40 - i) * 3600) for i in range(40)]
    w = ns["zf_when"](st[0]["f"], [0.6, 0.53, 0.13, 0.2], st[-1]["f"])
    ok(w.get("found") and w["before"]["f"] == st[22]["f"] and w["after"]["f"] == st[23]["f"] and w["steps"] <= 8,
       f"binäre Suche: Änderung zwischen Bild 22 und 23 ({w.get('steps')} Vergleiche, {w.get('timeline')})")
    ok(w.get("timeline", "").startswith("/timeline?day=") and "&mode=day" in w["timeline"], "Sprung in die Zeitleiste des Tages")
    w = ns["zf_when"](st[0]["f"], [0.05, 0.05, 0.1, 0.1], st[-1]["f"])
    ok(w.get("ok") and not w.get("found"), "Bereich ohne Änderung: «keine Änderung»")
    # 5. thinning and the cap
    shutil.rmtree(os.path.join(rec, "zeitfenster")); ZF["items"] = None
    small = cv2.resize(szene, (160, 90))
    os.makedirs(os.path.join(rec, "timelapse"), exist_ok=True)
    keepf = [os.path.join(rec, "timelapse", "tl_20250101_120000.jpg"), os.path.join(rec, "aufnahme_20250101_120000.mp4")]
    for p in keepf:
        open(p, "wb").write(b"x" * 10)
    T = now
    plan = []
    for dirp in (0.0, 40.0):
        plan += [(T - k * 1800, dirp) for k in range(1, 47)]                       # last 24 h: every 30 min
        plan += [(T - 86400 - 600 - k * 1200, dirp) for k in range(0, 6 * 72)]     # 1 - 7 days: every 20 min
        plan += [(T - 8 * 86400 - k * 3 * 3600, dirp) for k in range(0, 8 * 30)]   # older: every 3 h for 30 days
    for t_, dp in plan:
        ns["zf_save"](small, (dp, 0.0), "hour", t=t_)
    n0 = len(ns["zf_items"]())
    gone, left = ns["zf_thin"](now=T, cap_gb=100)
    its = ns["zf_items"]()
    day = [x for x in its if T - x[0] <= 86400]
    week = [x for x in its if 86400 < T - x[0] <= 7 * 86400]
    old = [x for x in its if T - x[0] > 7 * 86400]
    hours = {(round(x[1]), time.strftime("%Y%m%d%H", time.localtime(x[0]))) for x in week}
    days = {(round(x[1]), time.strftime("%Y%m%d", time.localtime(x[0]))) for x in old}
    ok(len(day) == 92, f"letzte 24 h: alle Bilder ({len(day)} von 92)")
    ok(len(week) == len(hours), f"1 - 7 Tage: genau 1 pro Stunde und Richtung ({len(week)} Bilder, {len(hours)} Stunden)")
    ok(len(old) == len(days) and len(old) <= 2 * 32, f"älter: 1 pro Tag und Richtung ({len(old)})")
    files = glob.glob(os.path.join(rec, "zeitfenster", "*", "zf_*.jpg"))
    rows = sum(len(open(f, encoding="utf-8").read().splitlines()) for f in glob.glob(os.path.join(rec, "zeitfenster", "idx_*.jsonl")))
    ok(len(files) == len(its) == rows and gone == n0 - len(its), f"Dateien = Index = Liste ({len(files)} / {rows} / {len(its)}, {gone} gelöscht)")
    ZF["items"] = None
    ok(len(ns["zf_items"]()) == len(its), "Index nach dem Ausdünnen neu gelesen: gleich")
    total = sum(x[5] for x in its)
    cap = total * 0.4 / 1024 ** 3
    gone, left = ns["zf_thin"](now=T, cap_gb=cap)
    its2 = ns["zf_items"]()
    ok(left <= cap * 1024 ** 3 and its2 and min(x[0] for x in its2) > max(x[0] for x in its if x not in its2),
       f"Obergrenze (klein simuliert {cap * 1024:.2f} MB): die ältesten zuerst gelöscht, {left / 1024 ** 2:.2f} MB übrig")
    ok(all(os.path.isfile(p) for p in keepf), "Zeitraffer-Fotos und Aufnahmen bleiben unberührt")
    ok(not moves, "auch dabei nie ein Befehl an den Kopf")
    shutil.rmtree(home, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- B
WRAP = r'''
import os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = """
_zt_dr = DemoSource.read
def _zt_read(self):                      # the demo clock stands still (40 s = quiet meadow): «now» stays the same picture
    self.t0 = time.time() - 40.0
    return _zt_dr(self)
DemoSource.read = _zt_read
live_has_head = lambda: True             # the test: the demo has a pan / tilt head
"""
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
g = {"__name__": "__main__", "__file__": D}
exec(compile(src, D, "exec"), g)
'''

LAGE = """() => { const seen = e => { for (let n = e; n && n !== document.body; n = n.parentElement) { const c = getComputedStyle(n); if (n.hidden || c.display === 'none' || c.visibility === 'hidden' || +c.opacity === 0) return false; } return true; };
  const R = e => { if (!e || !e.getClientRects().length || !seen(e)) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  const hit = (a, b) => a && b && !(b[2] <= a[0] + 0.5 || b[0] >= a[2] - 0.5 || b[3] <= a[1] + 0.5 || b[1] >= a[3] - 0.5);
  const ctl = [...document.querySelectorAll('#lv-tools button, #lv-cpu, #lv-comp, #v3-mini, #lv-joy, .vtag, #vo-lupe')].map(e => [e.id || e.className, R(e), e]).filter(x => x[1]);
  const grip = R(document.getElementById('zf-grip')), panel = R(document.getElementById('zf-panel')), vw = R(document.querySelector('#vcard .vwrap'));
  const zi = e => { for (let n = e; n && n !== document.body; n = n.parentElement) { const z = getComputedStyle(n).zIndex; if (z !== 'auto') return +z; } return 0; };
  const under = ctl.filter(c => { if (getComputedStyle(c[2]).pointerEvents === 'none') return zi(c[2]) <= 3;      // a label: above the layer?
    const x = (c[1][0] + c[1][2]) / 2, y = (c[1][1] + c[1][3]) / 2; const e = document.elementFromPoint(x, y); return e && e.closest('#zf-ov'); }).map(c => c[0]);
  return {grip, panel, vw, ov: R(document.getElementById('zf-ov')), gripHits: ctl.filter(c => hit(grip, c[1])).map(c => c[0]), panelHits: ctl.filter(c => hit(panel, c[1])).map(c => c[0]),
          covered: under, ctl: ctl.map(c => c[0]), text: (document.querySelector('#zf-panel .zf-t') || {}).textContent || '', msg: (document.querySelector('#zf-panel .zf-msg') || {}).textContent || '',
          marks: [...document.querySelectorAll('#zf-ov .zf-m')].map(R), split: window.mwZf ? window.mwZf.state().split : null,
          oldOk: !!(document.querySelector('#zf-ov > img') || {}).naturalWidth, find: (document.querySelector('#zf-panel .zf-find') || {}).textContent || '',
          scrollW: document.documentElement.scrollWidth, winW: innerWidth}; }"""


def teil_b(datei, a):
    import cv2
    import numpy as np
    print("B) MoveEye mit der Demo, Browser", flush=True)
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_zf_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    rec = os.path.join(cfg, "recordings")                                # the demo keeps its recordings there (640)
    # the stills of «back then», planted before the start: the demo picture (clock 40 s) - a red box stood on the meadow until 13 h ago
    home = tempfile.mkdtemp(prefix="mw_zf_h2_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_zf_test_b", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["log_event"] = lambda *a_, **k: None
    ns["CFG"]["record_dir"] = rec; ns["ZF"]["items"] = None
    src = ns["DemoSource"](); src.fps = 1000.0; src.t0 = time.time() - 40.0
    bild = src.read()
    bild = bild[1] if isinstance(bild, tuple) else bild
    H, W = bild.shape[:2]
    box = (int(W * 0.30), int(H * 0.70), int(W * 0.40), int(H * 0.86))
    obj = bild.copy(); cv2.rectangle(obj, box[:2], box[2:], (40, 40, 220), -1)
    now = time.time()
    for k in range(26, 1, -2):                                        # 26 h … 2 h ago: with the box until 14 h ago
        ns["zf_save"](obj if k >= 14 else bild, (0.4, -0.3), "hour", t=now - k * 3600)
    ns["zf_save"](np.clip(bild * 0.5, 0, 255).astype(np.uint8), (30.0, 0.0), "hour", t=now - 86400)   # another direction
    shutil.rmtree(home, ignore_errors=True)
    os.environ.pop("MOTIONWATCH_HOME", None)
    st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True,
          "https_extra": False, "ui_simple": False, "tours_auto": False, "pan": 50.0, "tilt": 50.0, "patrol": False, "track_person": False,
          "track_motion": False, "record_dir": rec, "zf_mask_top": 0, "theme": "dark", "zf_hourly": False}     # an install of 3.95.0 with the switch off
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    wrap = os.path.join(tmp, "zf_wrap.py")
    open(wrap, "w").write(WRAP)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, d=None, user=("admin", PW)):
        hd = {"Content-Type": "application/json"}
        if user:
            hd["Authorization"] = "Basic " + base64.b64encode((user[0] + ":" + user[1]).encode()).decode()
        r = urllib.request.Request(base + path, data=json.dumps(d).encode() if d is not None else None, headers=hd)
        try:
            with op.open(r, timeout=60) as x:
                b = x.read()
                return x.status, (json.loads(b) if x.headers.get_content_type() == "application/json" else b)
        except urllib.error.HTTPError as e:
            b = e.read()
            try:
                return e.code, json.loads(b)
            except ValueError:
                return e.code, b
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        req("/api/users", {"action": "add", "name": "Vera", "password": "vera-pass-1", "role": "view"})
        req("/api/users", {"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
        print("B) Rechte", flush=True)
        c, j = req("/api/zeitfenster?lang=de")
        ok(c == 200 and j.get("ok") and j.get("on") and len(j.get("items") or []) >= 13, f"Admin: Zustand mit den Bildern dieser Richtung ({c}, {len((j or {}).get('items') or [])})")
        f0 = (j.get("items") or [[0, ""]])[0][1]
        for who in (("Vera", "vera-pass-1"), ("Anna", "anna-pass-1")):
            ok(all(req(u, user=who)[0] == 403 for u in ("/api/zeitfenster", "/api/zeitfenster/bild?f=" + f0, "/api/zeitfenster/diff?f=" + f0,
                                                         "/api/zeitfenster/wann?f=" + f0 + "&box=0.1,0.1,0.2,0.2")),
               f"{who[0]} (kein Administrator): 403 überall")
        ok(req("/api/zeitfenster", user=None)[0] == 401, "ohne Anmeldung: 401")
        ok(j.get("est_mb") is None, "alte Einstellung «jede Stunde: aus» übernommen: aus, keine Schätzung")
        c, r_ = req("/api/text", {"key": "zf_still_min", "value": "7", "lang": "de"})
        ok(c != 200 or not r_.get("ok"), "Intervall 7 Min.: abgelehnt (nur die Auswahl)")
        c, r_ = req("/api/text", {"key": "zf_still_min", "value": "1", "lang": "de"})
        e = req("/api/zeitfenster")[1].get("est_mb")
        ok(c == 200 and e and 20 < e < 400, f"jede Minute gewählt: Schätzung {e} MB pro Tag und Richtung")
        ok(req("/api/text", {"key": "zf_still_min", "value": "1"}, user=("Anna", "anna-pass-1"))[0] == 403, "Familie darf das Intervall nicht ändern (403)")
        req("/api/text", {"key": "zf_still_min", "value": "10", "lang": "de"})      # 10 min: no new still in the direction «without a picture» below
        c, b = req("/api/zeitfenster/bild?f=" + f0)
        ok(c == 200 and bytes(b[:2]) == b"\xff\xd8", "Admin: Bild von damals (JPEG)")
        ok(req("/api/zeitfenster/bild?f=../../mw/motionwatch_settings.json")[0] == 404, "Pfad-Trick: 404")
        ok(req("/api/zeitfenster/wann?f=" + f0 + "&box=a,b")[0] == 400, "falscher Bereich: 400")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            init = "try{localStorage.setItem('mw-live-view','{\"joy\":\"on\"}');localStorage.setItem('mw-lang','de')}catch(e){}"
            for name, kw in (("handy", {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True,
                                        "color_scheme": "dark"}), ("pc", {"viewport": {"width": 1280, "height": 860}, "color_scheme": "dark"})):
                ctx = br.new_context(http_credentials={"username": "admin", "password": PW}, **kw); ctx.add_init_script(init)
                pg = ctx.new_page(); jsf = []
                pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
                pg.goto(base + "/", wait_until="domcontentloaded")
                ok(bool(warte(lambda: pg.evaluate("() => !!document.getElementById('lv-b-zf')"), 25)), f"{name}: Knopf ⏪ auf dem Live-Bild (Administrator)")
                pg.evaluate("() => document.body.classList.add('lvc-show')")              # the buttons on the picture shown (639zzj)
                pg.evaluate("() => document.getElementById('lv-b-zf').click()")
                pg.wait_for_timeout(600)
                pg.evaluate("() => { for (const b of document.querySelectorAll('#zf-panel .zf-s button')) if (b.dataset.a === '86400') b.click(); }")
                l = warte(lambda: (lambda x: x if x["oldOk"] and x["ov"] else None)(pg.evaluate(LAGE)), 10) or pg.evaluate(LAGE)
                ok(bool(l["ov"]) and l["oldOk"] and bool(re.search(r"\d{1,2}\.\d{1,2}\.\d{4}", l["text"])) and "vor" in l["text"],
                   f"{name}: «gestern» – Bild von damals mit Datum und Zeit («{l['text']}»)")
                # drag the split bar
                o = l["ov"]; y = o[1] + (o[3] - o[1]) * 0.55
                pg.mouse.move(o[0] + (o[2] - o[0]) * 0.5, y); pg.mouse.down(); pg.mouse.move(o[0] + (o[2] - o[0]) * 0.75, y, steps=5); pg.mouse.up()
                s = pg.evaluate("() => window.mwZf.state().split")
                ok(abs(s - 0.75) < 0.04, f"{name}: Trennbalken gezogen ({s:.2f})")
                pg.evaluate("() => document.getElementById('zf-marks').click()")
                l = warte(lambda: (lambda x: x if x["marks"] else None)(pg.evaluate(LAGE)), 15) or pg.evaluate(LAGE)
                bw = [(box[0] / W, box[1] / H, box[2] / W, box[3] / H)]
                fr = [((m[0] - o[0]) / (o[2] - o[0]), (m[1] - o[1]) / (o[3] - o[1]), (m[2] - o[0]) / (o[2] - o[0]), (m[3] - o[1]) / (o[3] - o[1])) for m in l["marks"]]
                hitb = [m for m in fr if not (m[2] < bw[0][0] or m[0] > bw[0][2] or m[3] < bw[0][1] or m[1] > bw[0][3])]
                ok(len(hitb) >= 1 and len(fr) <= 3, f"{name}: der verschwundene Gegenstand ist markiert ({len(fr)} Markierungen, «{l['msg']}»)")
                ok(not l["gripHits"] and not l["panelHits"] and not l["covered"], f"{name}: nichts überdeckt Knöpfe / Chip / Kompass / Lupe / kleines Bild ({l['gripHits']} {l['panelHits']} {l['covered']})")
                ok(l["panel"] and l["vw"] and l["panel"][1] >= l["vw"][3] - 1 and l["scrollW"] <= l["winW"], f"{name}: Leiste unter dem Bild, keine Seite quer ({l['panel']}, {l['vw']})")
                if a.bilder:
                    pg.locator("#vcard").screenshot(path=os.path.join(a.bilder, "zeitfenster_%s_bild.png" % name))
                    if name == "pc":
                        pg.screenshot(path=os.path.join(a.bilder, "zeitfenster_pc.png"))
                pg.evaluate("() => document.querySelector('#zf-ov .zf-m').click()")
                t_ = warte(lambda: (lambda x: x if "zwischen" in x else None)(pg.evaluate(LAGE)["find"]), 20) or pg.evaluate(LAGE)["find"]
                lnk = pg.evaluate("() => [...document.querySelectorAll('#zf-panel .zf-find button')].map(b => b.textContent)")
                ok("Geändert zwischen" in t_ and any("Zeitleiste" in x for x in lnk), f"{name}: Antippen – «{t_[:90]}», Knöpfe {lnk}")
                if a.bilder and name == "handy":
                    pg.screenshot(path=os.path.join(a.bilder, "zeitfenster_handy.png"), full_page=True)
                ok(not jsf, f"{name}: keine JavaScript-Fehler {jsf[:3]}")
                ctx.close()
            # a direction without pictures: a clear message
            req("/api/move", {"dir": "right", "step": 30})
            warte(lambda: not req("/api/zeitfenster")[1].get("items"), 20)
            ctx = br.new_context(http_credentials={"username": "admin", "password": PW}, viewport={"width": 390, "height": 844}, is_mobile=True,
                                 has_touch=True, color_scheme="dark"); ctx.add_init_script(init)
            pg = ctx.new_page(); pg.goto(base + "/", wait_until="domcontentloaded")
            warte(lambda: pg.evaluate("() => !!document.getElementById('lv-b-zf')"), 25)
            pg.evaluate("() => document.getElementById('lv-b-zf').click()")
            m = warte(lambda: (lambda x: x if "noch kein Bild" in x["msg"] else None)(pg.evaluate(LAGE)), 10) or pg.evaluate(LAGE)
            ok("noch kein Bild" in m["msg"] and not m["ov"], f"Richtung ohne Bild: klare Meldung («{m['msg'][:60]}…»)")
            ctx.close()
            # the settings: the estimate under the choice
            ctx = br.new_context(http_credentials={"username": "admin", "password": PW}, viewport={"width": 390, "height": 844}, is_mobile=True,
                                 has_touch=True, color_scheme="dark"); ctx.add_init_script(init)
            pg = ctx.new_page(); pg.goto(base + "/settings", wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
            info = pg.evaluate("""() => { const s = document.querySelector('select[data-key="zf_still_min"]');
                if (!s) return [...document.querySelectorAll('details > summary')].map(x => x.textContent.trim()).filter(x => /Zeit|Kopf/.test(x));
                for (let d = s.closest('details'); d; d = d.parentElement && d.parentElement.closest('details')) { d.open = true; d.dispatchEvent(new Event('toggle')); }
                s.scrollIntoView(); return 'ok'; }""")
            ok(info == "ok", f"Einstellungen: Auswahl «Bild, wenn der Kopf still steht» da ({info})")
            est = warte(lambda: pg.evaluate("() => { const s = document.querySelector('select[data-key=\"zf_still_min\"]'), e = document.querySelector('.zf-est');"
                                            " return s && e && e.textContent ? [s.value, [...s.options].map(o => o.textContent).join(' / '), e.textContent] : null; }"), 10)
            ok(bool(est) and est[0] == "10" and "jede Minute" in est[1] and "alle 5 Min." in est[1] and "aus" in est[1]
               and re.search(r"ca\. [\d.]+ MB pro Tag und Blickrichtung", est[2] or ""), f"Einstellungen: Auswahl und Schätzung darunter ({est})")
            if a.bilder:
                srch = pg.locator("input[type=search], input[placeholder*='suchen']").first
                if srch.count():
                    srch.fill("Kopf still steht"); pg.wait_for_timeout(800)
                pg.evaluate("() => document.querySelector('.zf-est').scrollIntoView({block: 'center'})"); pg.wait_for_timeout(400)
                pg.screenshot(path=os.path.join(a.bilder, "zeitfenster_intervall_handy.png"))
            ctx.close()
            # «nur ansehen»: no button
            ctx = br.new_context(http_credentials={"username": "Vera", "password": "vera-pass-1"}, viewport={"width": 390, "height": 844}); ctx.add_init_script(init)
            pg = ctx.new_page(); pg.goto(base + "/", wait_until="domcontentloaded"); pg.wait_for_timeout(5000)
            ok(not pg.evaluate("() => !!document.getElementById('lv-b-zf')"), "«nur ansehen»: kein Knopf ⏪")
            ctx.close()
            br.close()
        if p.poll() is not None:
            FEHLER.append("MoveEye ist während des Tests abgestürzt")
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


def main():
    ap = argparse.ArgumentParser(description="Zeitfenster (Damals / Jetzt)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5173)
    ap.add_argument("--nur", choices=("a", "b"), default="")
    ap.add_argument("--bilder", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    if a.nur != "b":
        teil_a(datei)
    if a.nur != "a":
        teil_b(datei, a)
    print("Zeitfenster-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
