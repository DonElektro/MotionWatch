#!/usr/bin/env python3
"""Test «Aufnahmeordner 8 GB» (4.18.1, Teil 639zzzzs, Wunsch des Besitzers, Karte 32 GB):
  - ab Werk record_max_gb = 8.0 (vorher 2.0)
  - höchstens die Hälfte des Laufwerks (rec_limit_gb, Aufräumen 410, Chip im Verlauf, Hinweis in Einstellungen → Aufnahme)
  - einmal beim Update: genau 2.0 und Laufwerk ab 16 GB -> 8.0 + «Neu in dieser Version» (5 Sprachen); ein anderer Wert, ein
    kleines Laufwerk, eine zweite Runde und der Host-Modus (fest 0.5) bleiben unberührt
  - die drei Grenzen (record_max_gb, timelapse_max_gb, rec_keep_days) auch in «Einfach»; Fehler bis 4.18.0: die Seite
    Einstellungen hatte keine Zeile «Aufnahme» (nur Schutz), die 🔍 fand «Aufnahmeordner» nicht
Mit --browser (Playwright, 390 px): 🔍 «Aufnahmeordner» und «Zeitraffer-Ordner» finden die Zeile, Tippen zeigt den Regler;
/settings?setting=record_max_gb zeigt den Regler; Chip «… MB / … GB» im Verlauf führt dorthin.

  python3 werkzeuge/aufnahme_8gb_test.py [--datei X.py] [--browser]
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

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)

LAUF = r'''
import json, os, sys, collections
ns = {"__name__": "mw_rec8_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
rec = sys.argv[2]
C = ns["CFG"]; C.update(record_dir=rec)
ns["log_event"] = lambda *a, **k: None
erg = []
def ok(b, t):
    erg.append([bool(b), t])
GiB = 1024 ** 3
DU = collections.namedtuple("DU", "total used free")
real_du = ns["shutil"].disk_usage
def drive(gb):
    ns["shutil"].disk_usage = lambda p: DU(int(gb * GiB), 0, int(gb * GiB))
ok(ns["DEFAULTS"]["record_max_gb"] == 8.0 and C["record_max_gb"] == 8.0, "ab Werk 8.0 GB (%s)" % ns["DEFAULTS"]["record_max_gb"])
drive(29.7)
ok(ns["rec_limit_gb"]() == 8.0, "Karte 32 GB: Grenze 8 GB (%s)" % ns["rec_limit_gb"]())
drive(7.4)
ok(ns["rec_limit_gb"]() == 3.7, "kleines Laufwerk 8 GB: höchstens die Hälfte = 3.7 GB (%s)" % ns["rec_limit_gb"]())
si = ns["storage_info"]()
ok(si.get("limit_gb") == 8.0 and si.get("limit_eff_gb") == 3.7, "storage_info: limit_gb 8, limit_eff_gb 3.7 (%s / %s)" % (si.get("limit_gb"), si.get("limit_eff_gb")))
r = ns["list_recordings"]({"limit": "5"})
ok(r["disk"].get("limit_gb") == 3.7, "Chip im Verlauf zeigt die echte Grenze 3.7 GB (%s)" % r["disk"].get("limit_gb"))
C["record_max_gb"] = 2.0
ok(ns["rec_limit_gb"]() == 2.0, "kleiner Wert des Benutzers bleibt (2.0 auf 8 GB: %s)" % ns["rec_limit_gb"]())
cr = [v.cleanup_recordings for v in list(ns.values()) if isinstance(v, type) and "cleanup_recordings" in vars(v)]
ok(cr and "rec_limit_gb" in cr[0].__code__.co_names, "Aufräumen (410) nimmt rec_limit_gb")
sf = ns["SETTINGS_FILE"]
def load(cfg, host=False):
    os.makedirs(os.path.dirname(sf), exist_ok=True)
    json.dump({"cfg": dict(cfg, setup_done=True)}, open(sf, "w"))
    C.update(record_max_gb=8.0, rec8_mig=False, rec8_note="", rec8_seen=[])
    ns["HOST"]["on"] = host
    try:
        ns["load_settings"]()
    finally:
        ns["HOST"]["on"] = False
    return C["record_max_gb"], C["rec8_note"]
drive(29.7)
v, n = load({"record_max_gb": 2.0})
ok(v == 8.0 and n == "pending" and C["rec8_mig"], "Update mit 2.0 auf 32 GB: 8.0 + Hinweis (%s, %r)" % (v, n))
st = ns["news_state"]("web", "de")
it = [x for x in st.get("items") or [] if "8 GB" in x.get("t", "")]
ok(it and it[0].get("href") == "/settings?setting=record_max_gb" and it[0]["t"].startswith("🗄 Neu: Aufnahmen dürfen jetzt bis 8 GB") and st.get("show"),
   "«Neu in dieser Version» (de) mit Link zur Einstellung (%s)" % (it[:1],))
ok(all(ns["TRX"][L].get(ns["REC8_NOTE"]) for L in ("fr", "it", "rm")), "Hinweis in fr / it / rm")
ns["news_seen"]("web")
ok(not [x for x in ns["news_state"]("web", "de").get("items") or [] if "8 GB" in x.get("t", "")], "gesehen (web): nicht nochmals")
ok([x for x in ns["news_state"]("window", "de").get("items") or [] if "8 GB" in x.get("t", "")], "Fenster sieht ihn noch")
C["rec8_mig"] = True; C["record_max_gb"] = 2.0
ok(ns["rec8_migrate"]({"record_max_gb": 2.0, "rec8_mig": True}) == [] and C["record_max_gb"] == 2.0, "nur einmal: rec8_mig gesetzt -> 2.0 bleibt")
for cfg, t in (({"record_max_gb": 3.0}, "Wert des Benutzers 3.0"), ({"record_max_gb": 1.5}, "Wert des Benutzers 1.5"),
               ({"record_max_gb": 16.0}, "Wert des Benutzers 16")):
    v, n = load(cfg)
    ok(v == cfg["record_max_gb"] and n == "", "%s bleibt (%s)" % (t, v))
v, n = load({"record_max_gb": 2.0, "rec8_mig": True})
ok(v == 2.0 and n == "", "schon migriert (Benutzer stellte danach 2.0 ein) bleibt 2.0 (%s)" % v)
drive(7.4)
v, n = load({"record_max_gb": 2.0})
ok(v == 2.0 and n == "", "Laufwerk 8 GB: 2.0 bleibt (%s)" % v)
drive(14.8)
v, n = load({"record_max_gb": 2.0})
ok(v == 8.0, "Karte «16 GB» (14.8 GiB): 8.0 (%s)" % v)
drive(29.7)
v, n = load({"record_max_gb": 2.0}, host=True)
ok(v == 2.0 and n == "", "Host-Modus: nie angefasst (%s, %r)" % (v, n))
ok(ns["_host_fixed"]().get("record_max_gb") == 0.5, "Host-Modus: fest 0.5 (%s)" % ns["_host_fixed"]().get("record_max_gb"))
v, n = load({"setup_done": True})
ok(v == 8.0 and n == "", "neues Gerät ohne Wert: 8.0 ohne Hinweis (%s, %r)" % (v, n))
ns["shutil"].disk_usage = real_du
hint = "The drive is small: at most {n} GB for recordings (half of the drive)"
ok(all(ns["TRX"][L].get(hint) for L in ("fr", "it", "rm")) and ns["DE"].get(hint, "").startswith("Das Laufwerk ist klein"), "Hinweis «Laufwerk klein» in 5 Sprachen")
ns["CFG"]["ui_simple"] = True
for k in ("record_max_gb", "rec_keep_days", "timelapse_max_gb"):
    sec = "Timelapse" if k == "timelapse_max_gb" else "Recording"
    ok(k in ns["SIMPLE_KEYS"] and sec in ns["SIMPLE_SECTIONS"], "%s auch in «Einfach»" % k)
ok('"sec:Recording"' in json.dumps(ns["MS_PAGES"]["settings"]) and '"sec:Recording"' in json.dumps(ns["MS_PAGES"]["protect"]),
   "Einstellungen haben die Zeile «Aufnahme» (Ursache des Suchfehlers)")
page = ns.get("REC_PAGE", "")
ok('id="b-disk" href="/settings?setting=record_max_gb"' in page, "Chip «… MB / … GB» führt zur Einstellung")
print("ERG " + json.dumps(erg))
'''


def frei_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def browser(datei, tmp):
    data = os.path.join(tmp, "web"); os.makedirs(data)
    json.dump({"cfg": {"setup_done": True, "dev_phase_done": True, "lang": "de"}}, open(os.path.join(data, "motionwatch_settings.json"), "w"))
    port = frei_port(); erg = []
    p = subprocess.Popen([sys.executable, datei, "--headless", "--bind", "127.0.0.1", "--port", str(port), "--config", data],
                         stdout=open(os.path.join(tmp, "web.log"), "w"), stderr=subprocess.STDOUT, cwd=tmp,
                         env=dict(os.environ, MOTIONWATCH_HOME=data))
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(180):
            try:
                op.open("http://127.0.0.1:%d/" % port, timeout=2); break
            except Exception:
                time.sleep(1)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch(); errs = []
            pg = b.new_page(viewport={"width": 390, "height": 844}, locale="de-CH")
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            u = "http://127.0.0.1:%d" % port
            for q, key in (("Aufnahmeordner", "record_max_gb"), ("Zeitraffer-Ordner", "timelapse_max_gb"), ("Tagen löschen", "rec_keep_days")):
                pg.goto(u + "/settings"); pg.wait_for_timeout(3500)
                pg.evaluate("() => document.querySelector('#ms-find') && document.querySelector('#ms-find').click()"); pg.wait_for_timeout(400)
                pg.evaluate("(q) => { const i = document.querySelector('#ms-qi'); i.value = q; i.dispatchEvent(new Event('input')); }", q)
                pg.wait_for_timeout(1200)
                rows = pg.evaluate("() => [...document.querySelectorAll('button.mi')].filter(m => !m.hidden && m.offsetParent)"
                                   ".map(m => m.dataset.ms)")
                erg.append([bool(rows), "🔍 «%s» findet %s" % (q, rows)])
                if rows:
                    pg.evaluate("(r) => document.querySelector('button.mi[data-ms=\"' + r + '\"]').click()", rows[0]); pg.wait_for_timeout(1200)
                    vis = pg.evaluate("(k) => { const w = document.querySelector('[data-key=' + k + ']'); return !!(w && w.offsetParent); }", key)
                    erg.append([vis, "Tippen auf die Zeile zeigt den Regler %s" % key])
            pg.goto(u + "/settings?setting=record_max_gb"); pg.wait_for_timeout(4500)
            vis = pg.evaluate("() => { const w = document.querySelector('[data-key=record_max_gb]'); return !!(w && w.offsetParent); }")
            erg.append([vis, "/settings?setting=record_max_gb zeigt den Regler"])
            pg.goto(u + "/recordings"); pg.wait_for_timeout(3500)
            h = pg.evaluate("() => { const e = document.querySelector('#b-disk'); return e ? [e.getAttribute('href'), e.textContent, e.getBoundingClientRect().right] : null; }")
            erg.append([bool(h) and h[0] == "/settings?setting=record_max_gb" and h[2] <= 390, "Verlauf 390 px: Chip %s führt zur Einstellung" % (h,)])
            wide = pg.evaluate("() => document.documentElement.scrollWidth")
            erg.append([wide <= 390, "Verlauf ohne waagrechtes Scrollen (%s px)" % wide])
            erg.append([not errs, "keine JS-Fehler %s" % errs[:2]])
            b.close()
    finally:
        p.terminate()
        try:
            p.wait(30)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(10)
    return erg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("Aufnahme-8-GB-Test · " + os.path.basename(datei))
    tmp = tempfile.mkdtemp(prefix="mw_rec8_")
    try:
        rec = os.path.join(tmp, "aufnahmen"); os.makedirs(rec)
        env = dict(os.environ, MOTIONWATCH_HOME=os.path.join(tmp, "daten"))
        r = subprocess.run([sys.executable, "-c", LAUF, datei, rec], capture_output=True, text=True, timeout=600, env=env,
                           cwd=os.path.dirname(datei))
        erg = None
        for ln in (r.stdout + r.stderr).splitlines():
            if ln.startswith("ERG "):
                erg = json.loads(ln[4:])
        if erg is None:
            print((r.stdout + r.stderr)[-3000:])
            print("FEHLER: der Lauf brach ab")
            return 1
        if a.browser:
            erg += browser(datei, tmp)
        for b, t in erg:
            print(("  ok   " if b else "  FEHLER  ") + t)
        bad = [t for b, t in erg if not b]
        print("Aufnahme-8-GB-Test OK" if not bad else "FEHLER: " + "; ".join(bad))
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
