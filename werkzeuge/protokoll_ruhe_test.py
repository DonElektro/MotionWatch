#!/usr/bin/env python3
"""Test «ruhiges Protokoll» (Teil 190 / 410): keine Hin-und-her-Zeilen «Auto-tune: walk_frames 9 -> 8 -> 9» und «Wind: …».

Hintergrund (3.72): walk_frames wurde bei jedem Bild neu gerundet (Bilder/s x walk_seconds) und die Wind-Stufe ohne
Totband bestimmt - 104 von 163 Protokoll-Zeilen in fünf Minuten. Jetzt: Totband + Haltezeit (walk_frames_step),
Wind-Stufe fällt erst 0.03 unter der Grenze (wind_level_of), eine Stufe muss 20 s dauern, höchstens eine Zeile pro 2 min
(LogHold). Die Erkennung soll sich dabei nicht merklich ändern - das prüft der Test mit:

  1. Quelle (ohne Programmstart): walk_frames mit zitternder Bildrate -> früher viele Wechsel, jetzt keiner; der Wert bleibt
     höchstens 0.75 Bilder vom genauen Produkt weg; ein echter Sprung (Stromsparen) kommt nach 2 s, ein Schritt nach 10 s.
     Wind: zitternder Wert an der Grenze -> kaum Stufenwechsel; steigen wie früher sofort; Verstärkung unberührt.
  2. Lauf (Demo, --lauf Sekunden, 0 = aus): im Protokoll höchstens wenige Zeilen pro Thema.

  python3 werkzeuge/protokoll_ruhe_test.py [--datei X.py] [--lauf 60]
"""
import argparse
import glob
import json
import math
import os
import random
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


def quelle():
    """Konstanten und Funktionen aus quelle/190, ohne das ganze Programm zu laden"""
    src = open(os.path.join(REPO, "quelle", "190_relais_wetter_tracker.py"), encoding="utf-8").read()
    teile = re.findall(r"^(?:WALK|WIND)_[A-Z_]+ = .*$", src, re.M)
    for kopf in (r"def walk_frames_step\(", r"def wind_level_of\(", r"class LogHold:"):
        teile.append(re.search(r"^%s.*?(?=^\S)" % kopf, src, re.M | re.S).group(0))
    ns = {}
    exec("\n".join(teile), ns)
    return ns


def alt_stufe(ws, thr):                                   # die Regel bis 3.71 (zum Vergleich)
    return "calm" if ws < thr else ("breezy" if ws < 0.55 else ("strong" if ws < 0.8 else "storm"))


def quelle_pruefen(pruef):
    Q = quelle()
    step, stufe, LogHold = Q["walk_frames_step"], Q["wind_level_of"], Q["LogHold"]
    rnd = random.Random(7)
    # ---- walk_frames: die Bildrate zittert um 14.2 / s, walk_seconds 0.6 -> genau 8.5 Bilder ---------------------------------
    cur_alt = cur = 9
    since, w_alt, w_neu, weg = None, 0, 0, 0.0
    for i in range(15 * 300):                             # 5 Minuten, 15 Bilder / s
        now = i / 15.0
        ideal = (14.17 + rnd.uniform(-0.4, 0.4)) * 0.6
        a_ = max(4, min(24, round(ideal)))
        w_alt += a_ != cur_alt; cur_alt = a_
        v, since = step(cur, ideal, since, now)
        if v is not None:
            w_neu += v != cur; cur = v
        weg = max(weg, abs(cur - ideal))
    pruef(w_alt > 100, "Vergleich: die alte Regel wechselt bei zitternder Bildrate dauernd (%d Wechsel in 5 min)" % w_alt)
    pruef(w_neu == 0, "neu: kein Wechsel bei zitternder Bildrate (%d)" % w_neu)
    pruef(weg <= Q["WALK_DEADBAND"] + 1e-9, "der Wert bleibt höchstens %.2f Bilder vom genauen Produkt weg (%.2f)" % (Q["WALK_DEADBAND"], weg))
    # ein echter Sprung kommt sofort (Stromsparen: 15 -> 3 Bilder / s und zurück)
    J = Q["WALK_JUMP_HOLD_S"]
    pruef(step(9, 3 * 0.6, None, 50.0) == (None, 50.0) and step(9, 3 * 0.6, 50.0, 50.0 + J - 0.1)[0] is None and step(9, 3 * 0.6, 50.0, 50.0 + J) == (4, None)
          and step(4, 15 * 0.6, 7.0, 7.0 + J) == (9, None), "Sprung um 2 Bilder oder mehr: nach %.0f s" % J)
    cur, since, n = 6, None, 0                            # wilde Messwerte in der ersten Sekunde nach dem Start: kein Hin und Her
    for i, fps_ in enumerate([18, 23, 27, 8, 12, 11, 12, 12] + [12] * 220):     # 15 s
        v, since = step(cur, fps_ * 0.6, since, i / 15.0)
        if v is not None:
            n += 1; cur = v
    pruef(n == 1 and cur == 7, "wilde Messwerte beim Start: ein einziger Schritt auf den richtigen Wert (%d Schritte, Wert %d)" % (n, cur))
    # ein Schritt (8 -> genau 9.0) kommt nach der Haltezeit, nicht vorher; kurz zurück = die Wartezeit beginnt neu
    v, s = step(8, 9.0, None, 100.0)
    pruef(v is None and s == 100.0, "Schritt um 1: wartet zuerst")
    pruef(step(8, 9.0, s, 100.0 + Q["WALK_HOLD_S"] - 0.1)[0] is None and step(8, 9.0, s, 100.0 + Q["WALK_HOLD_S"])[0] == 9, "… und kommt nach %d s" % Q["WALK_HOLD_S"])
    pruef(step(8, 8.6, s, 105.0) == (None, None), "zurück im Totband: die Wartezeit ist weg")
    pruef(step(4, 2.0, None, 0.0) == (None, None) and step(24, 40.0, None, 0.0) == (None, None), "Grenzen 4 und 24 bleiben")
    # langsame, echte Änderung der Bildrate (10 -> 20 / s in 2 min): der Wert folgt, nie mehr als 1 Bild daneben, wenige Schritte
    cur, since, n, weg = 6, None, 0, 0.0
    for i in range(15 * 120):
        now = i / 15.0
        ideal = (10 + 10 * now / 120.0) * 0.6
        v, since = step(cur, ideal, since, now)
        if v is not None:
            n += 1; cur = v
        weg = max(weg, abs(cur - ideal))
    pruef(cur in (11, 12) and n <= 7 and weg < 1.5, "langsame echte Änderung: der Wert folgt (6 -> %d in %d Schritten, höchstens %.2f Bilder daneben)" % (cur, n, weg))

    # ---- Wind: der Wert zittert an der Grenze 0.55 (böig / stark) ------------------------------------------------------------------
    thr = 0.3
    lv_alt = lv = "breezy"
    w_alt = w_neu = zeilen = 0
    H = LogHold(Q["WIND_LOG_HOLD_S"], Q["WIND_LOG_GAP_S"], "calm")
    gleich = True
    for i in range(15 * 300):
        now = 1000.0 + i / 15.0
        ws = 0.55 + 0.012 * math.sin(i / 23.0) + rnd.uniform(-0.008, 0.008)
        a_ = alt_stufe(ws, thr)
        w_alt += a_ != lv_alt; lv_alt = a_
        n_ = stufe(ws, thr, lv)
        w_neu += n_ != lv; lv = n_
        gleich = gleich and Q["WIND_LEVELS"].index(n_) >= Q["WIND_LEVELS"].index(a_)      # nie tiefer als die alte Regel
        zeilen += bool(H.feed(n_, now))
    pruef(w_alt > 40, "Vergleich: die alte Regel wechselt an der Grenze dauernd (%d Stufenwechsel in 5 min)" % w_alt)
    pruef(w_neu <= 1, "neu: höchstens ein Stufenwechsel (%d)" % w_neu)
    pruef(zeilen <= 1, "neu: höchstens eine Protokoll-Zeile (%d)" % zeilen)
    pruef(gleich, "die Stufe ist nie tiefer als nach der alten Regel (steigen wie bisher sofort)")
    for ws, prev in ((0.56, "breezy"), (0.81, "strong"), (0.31, "calm"), (0.9, "calm"), (0.2, "off"), (0.6, None)):
        pruef(stufe(ws, thr, prev) == alt_stufe(ws, thr), "steigen / Neustart: %.2f nach «%s» = «%s» wie bisher" % (ws, prev, alt_stufe(ws, thr)))
    pruef(stufe(0.53, thr, "strong") == "strong" and stufe(0.519, thr, "strong") == "breezy", "fallen: «stark» bleibt bis %.2f unter der Grenze" % Q["WIND_DEADBAND"])
    pruef(stufe(0.28, thr, "breezy") == "breezy" and stufe(0.26, thr, "breezy") == "calm" and stufe(0.1, thr, "storm") == "calm", "fallen: «böig» -> «ruhig» ebenso, ein grosser Fall sofort")
    # ---- LogHold: eine Böe von 5 s gibt keine Zeile, ein Wechsel der bleibt eine; höchstens eine pro 2 min ------------------------
    H = LogHold(20, 120, "calm")
    z = [t for t in range(0, 600) if H.feed("strong" if 100 <= t < 105 else "calm", float(t))]
    pruef(z == [], "kurze Böe (5 s): keine Zeile (%s)" % z)
    H = LogHold(20, 120, "calm")
    z = [(t, v) for t in range(0, 600) for v in ["breezy" if 100 <= t < 300 else ("strong" if 300 <= t < 315 else "calm")] if H.feed(v, float(t))]
    pruef(z == [(120, "breezy"), (335, "calm")], "bleibender Wechsel: eine Zeile nach 20 s; 15 s «stark» dazwischen: keine eigene Zeile (%s)" % z)
    H = LogHold(20, 120, "calm")
    z = [t for t in range(0, 900) if H.feed(("breezy", "strong")[(t // 30) % 2], float(t))]
    pruef(len(z) <= 8 and all(y - x >= 120 for x, y in zip(z, z[1:])), "Wechsel alle 30 s: höchstens eine Zeile pro 2 min (%s)" % z)


def lauf(a, pruef):
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_protokoll_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "auto_tune": True, "wind_auto": True, "calib_seconds": 5}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1",
                          "--config", cfg], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open("http://127.0.0.1:%d/manifest.webmanifest" % port, timeout=2); break
            except Exception:
                time.sleep(1)
        ende = time.time() + a.lauf
        while time.time() < ende:                         # ein Zuschauer holt Bilder: die Bildrate schwankt wie im Betrieb
            try:
                op.open("http://127.0.0.1:%d/snapshot.jpg" % port, timeout=5).read()
            except Exception:
                pass
            time.sleep(0.7)
        pruef(p.poll() is None, "MoveEye läuft noch")
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        logf.close()
        log = "".join(open(x, errors="replace").read() for x in glob.glob(os.path.join(cfg, "**", "motionwatch.log"), recursive=True))
        shutil.rmtree(tmp, ignore_errors=True)
    zeilen = log.splitlines()
    wf = [z for z in zeilen if "walk_frames" in z]
    wi = [z for z in zeilen if "[wind]" in z]
    erl_wf = 2 + int(a.lauf / 10)                         # theoretisch höchstens ein Schritt pro Haltezeit (echte Sprünge der Bildrate dazu)
    erl_wi = 1 + int(a.lauf / 120)
    print("  Protokoll: %d Zeilen in %d s, davon walk_frames %d, Wind %d" % (len(zeilen), a.lauf, len(wf), len(wi)), flush=True)
    pruef(len(zeilen) > 3, "das Protokoll wird geschrieben")
    pruef(len(wf) <= erl_wf, "walk_frames: höchstens %d Zeilen (%d)" % (erl_wf, len(wf)))
    pruef(len(wi) <= erl_wi, "Wind: höchstens %d Zeilen (%d)" % (erl_wi, len(wi)))
    hin_her = sum(1 for x, y in zip(wf, wf[1:]) if x[:19] == y[:19])
    pruef(hin_her == 0, "keine zwei walk_frames-Zeilen in derselben Sekunde (%d)" % hin_her)


def main():
    ap = argparse.ArgumentParser(description="ruhiges Protokoll: Auto-tune walk_frames und Wind-Stufe")
    ap.add_argument("--datei", default="")
    ap.add_argument("--lauf", type=int, default=60, help="Sekunden mit der Demo (0 = nur die Quelle prüfen)")
    a = ap.parse_args()
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    print("== Quelle (190)", flush=True)
    quelle_pruefen(pruef)
    if a.lauf > 0:
        print("== Lauf (%d s)" % a.lauf, flush=True)
        lauf(a, pruef)
    print("Protokoll-Ruhe-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
