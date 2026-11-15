#!/usr/bin/env python3
"""Test «★ Favoriten» (Teil 639zzzi).

Startet MoveEye ohne Fenster mit der Demo (eigener Ordner, freier Port) und prüft mit Playwright (iPhone 13):
  1. Reiter «★» (nur das Symbol, schmal) vor «Live»: sieben Reiter passen bei 390 px in allen fünf Sprachen
  2. /fav leer: Hinweis und «+ Hinzufügen»
  3. «+ Hinzufügen»: Schalter (Patrouille), Schutz (Wachsam, Aus), Seite (Almanach), Spiel (Vier gewinnt), Zeile (Updates)
     -> /api/fav hat sie (pro Benutzer auf dem Server)
  4. Kacheln: Patrouille zeigt den Zustand und schaltet direkt (die Einstellung ändert sich), Seite / Spiel / Zeile führen hin
  5. «Aus» mit PIN fragt die PIN (falsch = bleibt an, richtig = aus)
  6. Bearbeiten: ziehen ordnet (auch auf dem Server), ✕ entfernt
  7. ☆ am Ende einer Zeile (Einstellungen → Patrouille) fügt hinzu, ★ nimmt weg
  8. Live: langes Drücken auf «Foto» fügt hinzu – und macht KEIN Foto; kurzes Tippen macht weiter eins
  9. /party?game=c4 wählt «Vier gewinnt» in der Spielecke
 10. Rechte: ein Benutzer «Nur ansehen» hat eigene Favoriten, seine Kachel schaltet nichts, was er sonst nicht schalten darf
 11. Pi-Fenster (Ersatz-tkinter): Reiter «★», Knöpfe der Favoriten, ein Klick ruft dieselbe Funktion
 12. keine JavaScript-Fehler

  python3 werkzeuge/favoriten_test.py [--datei X.py] [--bilder ORDNER]
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
PASSWORT = "Fav-" + base64.b16encode(os.urandom(5)).decode().lower()
GAST_PW = "Gast-" + base64.b16encode(os.urandom(4)).decode().lower()
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


def warte(fn, t=15, schritt=0.3):
    t_ = time.time() + t
    while time.time() < t_:
        v = fn()
        if v:
            return v
        time.sleep(schritt)
    return fn()


def teil_fenster(datei):
    """11. the window with the fake tkinter of lupe_test"""
    print("Pi-Fenster (Ersatz-tkinter)", flush=True)
    src = open(os.path.join(HIER, "lupe_test.py"), encoding="utf-8").read()
    exec(re.search(r'FAKE_TK = r"""(.*?)"""', src, re.S).group(1), {})
    home = tempfile.mkdtemp(prefix="mw_fav_tk_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_fav_tk", "__file__": os.path.abspath(datei)}
    try:
        exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
        App, CFG, tkm = ns["App"], ns["CFG"], sys.modules["tkinter"]
        a = object.__new__(App)
        tabs = a._tabs()
        pruef(tabs[0] == ("fav", "★") and len(tabs) == 7, "Fenster: Reiter «★» zuerst (%s)" % tabs)
        CFG["ui_fav"] = {"admin": [{"k": "qs:patrol", "l": "Patrouille", "i": "🔄"}, {"k": "pr:watch", "l": "Wachsam", "i": "🟡"},
                                   {"k": "row:settings:sec:Updates", "l": "Updates", "i": "⬆"}]}
        calls = []
        a.root = tkm.Frame(); a.tab = "fav"
        a._qs_list = lambda: [{"id": "patrol", "on": lambda: CFG.get("patrol"), "go": lambda: calls.append("patrol")}]
        ns["protect_set"] = lambda lv, who, ans=None: (calls.append("protect:" + lv), (True, ""))[1]
        a._tab = lambda t: calls.append("tab:" + t)
        a._fav_tk(tkm.Frame())
        pruef(len(a._fav_tiles) == 3 and "Patrouille" in a._fav_tiles[0][1].cget("text"), "Fenster: drei Knöpfe der Favoriten")
        for f, _b in a._fav_tiles:
            a._fav_go(f)
        pruef(calls[:3] == ["patrol", "protect:watch", "tab:settings"] and a._ms_next == "Updates",
              "Fenster: ein Klick ruft dieselbe Funktion (Schnellschalter, Schutz, Thema «Updates» öffnen) (%s)" % calls)
        CFG["ui_fav"] = {}
        a._fav_tk(tkm.Frame())
        pruef(a._fav_tiles == [], "Fenster: leer = Hinweis, keine Knöpfe")
    except Exception as e:
        import traceback
        traceback.print_exc()
        pruef(False, "Fenster: %s" % e)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Favoriten")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5201)
    ap.add_argument("--bilder", default="")
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
    tmp = tempfile.mkdtemp(prefix="mw_fav_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "extra_cams": [], "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True,
          "https_extra": False, "ui_simple": False, "tours_auto": False, "patrol": False}
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": st}, f)
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(a.port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = "http://127.0.0.1:%d" % a.port
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def req(path, d=None, user="admin", pw=PASSWORT):
            H = {"Authorization": "Basic " + base64.b64encode((user + ":" + pw).encode()).decode(), "Content-Type": "application/json"}
            try:
                r = op.open(urllib.request.Request(base + path, data=json.dumps(d).encode() if d is not None else None, headers=H), timeout=15)
                return r.status, json.loads(r.read() or b"{}")
            except urllib.error.HTTPError as e:
                try:
                    return e.code, json.loads(e.read() or b"{}")
                except Exception:
                    return e.code, {}
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        favs = lambda user="admin", pw=PASSWORT: [x["k"] for x in req("/api/fav", None, user, pw)[1].get("items") or []]
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw_:
            br = pw_.chromium.launch(args=["--no-proxy-server"])
            dev = dict(pw_.devices["iPhone 13"]); dev.pop("default_browser_type", None)
            ctx = br.new_context(http_credentials={"username": "admin", "password": PASSWORT}, **dev)
            ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.removeItem('mw-fav')}catch(e){}")
            pg = ctx.new_page(); jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            weg = lambda: pg.evaluate("() => ['g2-ov','g2-spot','g2-bub','gd-card','mw-tip'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); })")
            # 1. the tab in five languages
            pg.goto(base + "/", wait_until="domcontentloaded"); pg.wait_for_timeout(3500)
            for L in ("de", "en", "fr", "it", "rm"):
                pg.evaluate("k => langSet(k)", L); pg.wait_for_timeout(1200)
                w = pg.evaluate("""() => { const n = document.querySelector('header>nav.nav'), f = n.querySelector('a.fav'); return {sw: n.scrollWidth, cw: n.clientWidth,
                    doc: document.documentElement.scrollWidth, fw: f ? Math.round(f.getBoundingClientRect().width) : 0, first: n.querySelector('a') === f,
                    svg: !!(f && f.querySelector('svg')), n: n.querySelectorAll('a').length,
                    cut: [...n.querySelectorAll('a .ns')].filter(s => s.getClientRects().length && s.scrollWidth > s.clientWidth + 1).map(s => s.textContent)}; }""")
                pruef(w["first"] and w["svg"] and 0 < w["fw"] <= 44 and w["n"] == 7 and w["sw"] <= w["cw"] + 1 and w["doc"] <= 391 and not w["cut"],
                      "Reiter %s: «★» zuerst, nur Symbol (%d px), sieben Reiter passen in 390 px (%s)" % (L, w["fw"], w))
            pg.evaluate("k => langSet(k)", "de"); pg.wait_for_timeout(1000)
            # 2. empty
            pg.goto(base + "/fav", wait_until="domcontentloaded"); pg.wait_for_selector("#fv-grid", state="attached", timeout=20000); pg.wait_for_timeout(1500); weg()
            e = pg.evaluate("() => { const x = document.getElementById('fv-empty'); return x && x.getClientRects().length ? x.textContent : ''; }")
            pruef("Noch keine Favoriten" in e and "Hinzufügen" in e, "/fav leer: Hinweis und «+ Hinzufügen» (%s)" % e[:80])
            if a.bilder:
                pg.screenshot(path=os.path.join(a.bilder, "fav_leer.png"))
            # 3. add through the picker
            pg.click("#fv-add"); pg.wait_for_timeout(600)
            for k in ("qs:patrol", "pr:watch", "pr:off", "page:/almanach", "game:c4", "row:settings:sec:Updates"):
                n = pg.locator("#fv-pick .pi[data-k='%s'] .fv-star" % k).count()
                if n:
                    pg.locator("#fv-pick .pi[data-k='%s'] .fv-star" % k).first.click(); pg.wait_for_timeout(350)
                pruef(n == 1, "«+ Hinzufügen» kennt %s" % k)
            pg.wait_for_timeout(800)
            got = favs()
            pruef(got == ["qs:patrol", "pr:watch", "pr:off", "page:/almanach", "game:c4", "row:settings:sec:Updates"], "auf dem Server gemerkt (%s)" % got)
            # 4. tiles
            pg.reload(wait_until="domcontentloaded"); pg.wait_for_selector("#fv-grid .fv-t", timeout=20000); pg.wait_for_timeout(2000); weg()
            t = pg.evaluate("() => [...document.querySelectorAll('#fv-grid .fv-t')].map(x => ({k: x.dataset.k, n: x.querySelector('.fn').textContent, s: x.querySelector('.fs').textContent, on: x.classList.contains('on'), h: x.getAttribute('href')}))")
            by = {x["k"]: x for x in t}
            pruef(len(t) == 6 and by["qs:patrol"]["n"] == "Patrouille" and by["qs:patrol"]["s"] == "aus" and by["page:/almanach"]["h"] == "/almanach"
                  and by["game:c4"]["h"] == "/party?game=c4" and (by["row:settings:sec:Updates"]["h"] or "").startswith("/settings#s=") and by["row:settings:sec:Updates"]["n"],
                  "Kacheln: Namen, Zustand, Ziele (%s)" % [(x["n"], x["s"], x["h"]) for x in t])
            if a.bilder:
                pg.screenshot(path=os.path.join(a.bilder, "fav_kacheln.png"), full_page=True)
            pg.locator("#fv-grid .fv-t[data-k='qs:patrol']").click()
            pruef(bool(warte(lambda: req("/api/state")[1].get("cfg", {}).get("patrol"))), "Kachel «Patrouille» schaltet direkt (Einstellung an)")
            pruef(bool(warte(lambda: pg.evaluate("() => document.querySelector(\"#fv-grid .fv-t[data-k='qs:patrol']\").classList.contains('on')"))),
                  "die Kachel zeigt den neuen Zustand")
            pg.locator("#fv-grid .fv-t[data-k='pr:watch']").click()
            pruef(bool(warte(lambda: (req("/api/protect?lang=de")[1] or {}).get("level") == "watch")), "Kachel «Wachsam» schaltet den Schutz")
            # 5. «Off» with a PIN asks for it
            pruef(req("/api/protect", {"action": "pin", "new": "4711", "lang": "de"})[0] == 200, "PIN gesetzt")
            pg.wait_for_timeout(1500)
            pg.locator("#fv-grid .fv-t[data-k='pr:off']").click(); pg.wait_for_timeout(600)
            pruef(pg.locator("#fv-pin input").count() == 1, "«Aus» mit PIN: die PIN wird gefragt")
            pg.fill("#fv-pin input", "0000"); pg.click("#fv-pin button:not(.sec)"); pg.wait_for_timeout(800)
            pruef((req("/api/protect?lang=de")[1] or {}).get("level") == "watch" and pg.locator("#fv-pin").count() == 1, "falsche PIN: Schutz bleibt an")
            pg.fill("#fv-pin input", "4711"); pg.click("#fv-pin button:not(.sec)")
            pruef(bool(warte(lambda: (req("/api/protect?lang=de")[1] or {}).get("level") == "off")), "richtige PIN: Schutz aus")
            # 6. edit: drag, remove
            pg.click("#fv-edit"); pg.wait_for_timeout(400)
            b1 = pg.locator("#fv-grid .fv-t").nth(0).bounding_box(); b3 = pg.locator("#fv-grid .fv-t").nth(2).bounding_box()
            pg.mouse.move(b1["x"] + b1["width"] / 2, b1["y"] + b1["height"] / 2); pg.mouse.down()
            for s in range(1, 9):
                pg.mouse.move(b1["x"] + b1["width"] / 2 + (b3["x"] - b1["x"]) * s / 8, b1["y"] + b1["height"] / 2 + (b3["y"] - b1["y"]) * s / 8); pg.wait_for_timeout(40)
            pg.mouse.up(); pg.wait_for_timeout(900)
            got = favs()
            pruef(got[:3] == ["pr:watch", "pr:off", "qs:patrol"], "ziehen ordnet, auch auf dem Server (%s)" % got)
            if a.bilder:
                pg.screenshot(path=os.path.join(a.bilder, "fav_bearbeiten.png"), full_page=True)
            pg.locator("#fv-grid .fv-t[data-k='page:/almanach'] .fx").click(); pg.wait_for_timeout(800)
            pruef("page:/almanach" not in favs(), "✕ entfernt")
            pg.click("#fv-edit")
            # 7. the ☆ on a row
            pg.goto(base + "/settings", wait_until="domcontentloaded"); pg.wait_for_selector("#ms-list .mi[data-ms='sec:Patrol'] .fv-star", timeout=20000); weg()
            pg.locator("#ms-list .mi[data-ms='sec:Patrol'] .fv-star").click(); pg.wait_for_timeout(800)
            f = req("/api/fav")[1].get("items") or []
            row = next((x for x in f if x["k"] == "row:settings:sec:Patrol"), None)
            pruef(bool(row) and row["l"] == "Patrouille" and not pg.evaluate("() => document.body.classList.contains('ms-sub')"),
                  "☆ in der Zeile fügt hinzu (Name «%s»), ohne die Unterseite zu öffnen" % (row or {}).get("l"))
            pg.locator("#ms-list .mi[data-ms='sec:Patrol'] .fv-star").click(); pg.wait_for_timeout(800)
            pruef("row:settings:sec:Patrol" not in favs(), "★ nimmt wieder weg")
            # 8. Live: a long press adds, takes no photo; a short tap still takes one
            pg.goto(base + "/", wait_until="domcontentloaded"); pg.wait_for_selector("#qs-photo", timeout=20000); pg.wait_for_timeout(2500); weg()
            n0 = (req("/api/recordings?offset=0&limit=1")[1].get("disk") or {}).get("files")
            pg.locator("#qs-photo").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
            b = pg.locator("#qs-photo").bounding_box()
            pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2); pg.mouse.down(); pg.wait_for_timeout(900); pg.mouse.up(); pg.wait_for_timeout(1500)
            n1 = (req("/api/recordings?offset=0&limit=1")[1].get("disk") or {}).get("files")
            pruef("qs:photo" in favs() and n1 == n0, "Live: langes Drücken auf «Foto» = Favorit, kein Foto (%s -> %s)" % (n0, n1))
            pg.locator("#qs-photo").click(); pg.wait_for_timeout(2500)
            n2 = (req("/api/recordings?offset=0&limit=1")[1].get("disk") or {}).get("files")
            pruef(n2 is not None and n0 is not None and n2 > n0, "Live: kurzes Tippen macht weiter ein Foto (%s -> %s)" % (n0, n2))
            # 9. the game corner: /party?game=c4
            pg.goto(base + "/party?game=c4", wait_until="domcontentloaded")
            pruef(bool(warte(lambda: req("/api/party")[1].get("game") == "c4")), "/party?game=c4: «Vier gewinnt» gewählt (%s)" % req("/api/party")[1].get("game"))
            pruef(bool(warte(lambda: "game=" not in pg.evaluate("() => location.search"), 12)), "die Adresse ist danach wieder /party")
            pruef(not jsf, "keine JavaScript-Fehler %s" % jsf[:3])
            ctx.close()
            # 10. a viewer: own favourites, the tile does not switch what he may not switch
            r = req("/api/users", {"action": "add", "name": "Zuschauer", "password": GAST_PW, "role": "view", "lang": "de"})
            pruef(r[0] == 200, "Benutzer «Zuschauer» (Nur ansehen) angelegt (%s)" % (r,))
            pruef(favs("Zuschauer", GAST_PW) == [], "Zuschauer: eigene, leere Favoriten")
            c2 = req("/api/fav", {"items": [{"k": "qs:patrol"}]}, "Zuschauer", GAST_PW)
            pruef(c2[0] == 200 and favs("Zuschauer", GAST_PW) == ["qs:patrol"] and "pr:watch" in favs(), "Zuschauer merkt seine Favoriten, die des Besitzers bleiben")
            ctx = br.new_context(http_credentials={"username": "Zuschauer", "password": GAST_PW}, **dev)
            pg = ctx.new_page(); pg.goto(base + "/fav", wait_until="domcontentloaded")
            p0 = req("/api/state")[1].get("cfg", {}).get("patrol")
            if pg.locator("#fv-grid .fv-t[data-k='qs:patrol']").count():
                pg.wait_for_timeout(1500); pg.locator("#fv-grid .fv-t[data-k='qs:patrol']").click(); pg.wait_for_timeout(1500)
            pruef(req("/api/state")[1].get("cfg", {}).get("patrol") == p0, "Zuschauer: die Kachel «Patrouille» schaltet nichts (Server lehnt ab)")
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
    teil_fenster(datei)
    print("Favoriten-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
