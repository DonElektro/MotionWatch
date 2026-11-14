#!/usr/bin/env python3
"""Test «Kopien der alten Einstellungen» (Teil 586): nach «Auf Werkseinstellungen zurücksetzen» steht die Kopie in der Liste.

Hintergrund (3.72): factory_backups() las das Datum mit festen Positionen (n[33:48], ein Zeichen daneben) - kein Datum
liess sich lesen, jede Kopie wurde übersprungen, die Liste blieb in Web und Fenster leer, obwohl die Datei da war.
Jetzt kommt das Datum aus dem Muster des Dateinamens (factory_backup_when).

  1. Ohne Programmstart: factory_backup_when / factory_backups aus quelle/586 mit echten Dateinamen (auch falsche).
  2. MoveEye ohne Fenster (Demo, eigener Ordner, Aufnahme-Ordner im Test-Ordner): eine ältere Kopie liegt schon da ->
     /api/factory nennt sie mit Datum; ein echtes Zurücksetzen -> die neue Kopie steht zuoberst, lässt sich laden;
     Einstellungen → System → «Einrichtung & Werkseinstellungen» (bis 3.88: Mehr → System) zeigt «Kopien der alten
     Einstellungen» mit beiden.

  python3 werkzeuge/werkskopie_test.py [--datei X.py] [--ohne-browser]
"""
import argparse
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
from datetime import datetime

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
ALT = "motionwatch_settings.before_reset_20261109-213045.json"          # ein echter Name, wie factory_reset() ihn schreibt
FALSCH = ["motionwatch_settings.before_reset_20269999-999999.json",       # Ziffern, aber kein Datum
          "motionwatch_settings.before_reset_2026110-213045.json", "motionwatch_settings.json",
          "xmotionwatch_settings.before_reset_20261109-213045.json", "motionwatch_settings.before_reset_20261109-213045.json.bak"]


def quelle_pruefen(pruef):
    """die drei Funktionen aus dem Quelltext, ohne das ganze Programm zu laden"""
    src = open(os.path.join(REPO, "quelle", "586_guide2.py"), encoding="utf-8").read()
    teile = [re.search(r"^_BACKUP_RE = .*$", src, re.M).group(0)]
    for name in ("factory_backup_when", "factory_backups"):
        teile.append(re.search(r"^def %s\(.*?(?=^\S)" % name, src, re.M | re.S).group(0))
    tmp = tempfile.mkdtemp(prefix="mw_werkskopie_q_")
    try:
        ns = {"re": re, "os": os, "datetime": datetime, "DATA_DIR": tmp}
        exec("\n".join(teile), ns)
        pruef(ns["factory_backup_when"](ALT) == "09.11.2026 21:30", "Datum aus dem echten Namen: %s" % ns["factory_backup_when"](ALT))
        jetzt = datetime.now()
        neu = "motionwatch_settings.before_reset_%s.json" % jetzt.strftime("%Y%m%d-%H%M%S")
        pruef(ns["factory_backup_when"](neu) == jetzt.strftime("%d.%m.%Y %H:%M"), "Datum aus einem Namen von jetzt")
        pruef(all(ns["factory_backup_when"](n) is None for n in FALSCH + ["", None]), "falsche Namen: kein Datum, kein Absturz")
        for n in [ALT, neu] + FALSCH:
            with open(os.path.join(tmp, n), "w") as f:
                f.write("{}" * 700)
        bk = ns["factory_backups"]()
        erw = sorted([ALT, neu], reverse=True)
        pruef([x["name"] for x in bk] == erw and all(x["when"] and x["kb"] >= 1 for x in bk), "Liste: genau die zwei echten Kopien, neueste zuerst (%s)" % [(x["name"][34:49], x["when"]) for x in bk])
        for i in range(12):                                        # höchstens 10 in der Liste
            open(os.path.join(tmp, "motionwatch_settings.before_reset_202501%02d-120000.json" % (i + 1)), "w").close()
        pruef(len(ns["factory_backups"]()) == 10, "höchstens 10 Kopien in der Liste")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Kopien der alten Einstellungen nach dem Zurücksetzen")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5143)
    ap.add_argument("--ohne-browser", action="store_true", help="nur Quelle und Server, ohne Playwright")
    a = ap.parse_args()
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    print("== Quelle (586)", flush=True)
    quelle_pruefen(pruef)
    print("== Server", flush=True)
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="mw_werkskopie_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    rec = os.path.join(tmp, "aufnahmen"); os.makedirs(rec)           # das Zurücksetzen löscht Aufnahmen: nur im Test-Ordner (unten geprüft)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
          "setup_done": True, "https_extra": False, "record_dir": rec, "record": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    with open(os.path.join(cfg, ALT), "w") as f:
        json.dump({"cfg": st, "fueller": "x" * 3000}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1",
                          "--config", cfg], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def api(pfad, daten=None):
        rq = urllib.request.Request(base + pfad, data=None if daten is None else json.dumps(daten).encode(),
                                    headers={"Content-Type": "application/json", "Origin": base})
        with op.open(rq, timeout=30) as r:
            return json.loads(r.read())

    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        F = api("/api/factory?lang=de")
        pruef([x["name"] for x in F["backups"]] == [ALT] and F["backups"][0]["when"] == "09.11.2026 21:30" and F["backups"][0]["kb"] >= 2,
              "ältere Kopie steht in der Liste, mit Datum und Grösse (%s)" % F["backups"])
        if not os.path.abspath(F.get("rec_dir") or "/").startswith(os.path.abspath(tmp) + os.sep):
            pruef(False, "Aufnahme-Ordner liegt nicht im Test-Ordner (%s) - kein Zurücksetzen" % F.get("rec_dir"))
        else:
            r = api("/api/factory", {"word": F["word"], "lang": "de"})
            neu = r.get("backup") or ""
            pruef(bool(r.get("ok")) and os.path.isfile(os.path.join(cfg, neu)), "Zurücksetzen: Kopie geschrieben (%s)" % neu)
            F = api("/api/factory?lang=de")
            namen = [x["name"] for x in F["backups"]]
            pruef(namen == [neu, ALT], "nach dem Zurücksetzen: neue Kopie zuoberst, die ältere darunter (%s)" % namen)
            heute = datetime.now().strftime("%d.%m.%Y")
            pruef(bool(F["backups"]) and F["backups"][0]["when"].startswith(heute), "Datum der neuen Kopie ist heute (%s)" % (F["backups"] and F["backups"][0]["when"]))
            with op.open(base + "/api/factory/backup/" + neu, timeout=10) as rr:
                inhalt = json.loads(rr.read())
            pruef(isinstance(inhalt, dict) and bool(inhalt), "die Kopie lässt sich herunterladen (Administrator)")
            if not a.ohne_browser:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as pw:
                    br = pw.chromium.launch(args=["--no-proxy-server"])
                    ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
                    pg = ctx.new_page()
                    jsf = []
                    pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
                    pg.goto(base + "/settings?open=g2:setup", wait_until="domcontentloaded")   # Design «Klar» Etappe 1: Einstellungen → System
                    t_ = time.time() + 25
                    links = []
                    while time.time() < t_ and len(links) < 2:
                        links = pg.evaluate("() => [...document.querySelectorAll('a[href^=\"/api/factory/backup/\"]')].map(x => x.textContent)")
                        pg.wait_for_timeout(400)
                    txt = pg.evaluate("() => document.body.textContent")
                    pruef("Kopien der alten Einstellungen" in txt and len(links) == 2 and "09.11.2026 21:30" in links[1] and heute in links[0],
                          "Einstellungen → System: «Kopien der alten Einstellungen» mit beiden (%s)" % links)
                    vis = pg.evaluate("() => { const s = document.getElementById('g2-setup'); if (!s) return null; s.open = true; s.scrollIntoView(); "
                                      "const a = s.querySelector('a[href^=\"/api/factory/backup/\"]'); return !!a && a.getClientRects().length > 0; }")
                    pruef(vis is True, "die Kopien stehen sichtbar unter Einstellungen → System → «Einrichtung & Werkseinstellungen» (%s)" % vis)
                    pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])
                    ctx.close(); br.close()
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
    print("Werkskopie-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
