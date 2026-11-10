#!/usr/bin/env python3
"""MoveEye: Test «Spiele unter Mehr aufgeräumt» (Teil 639zzo) – im Browser (Playwright, Handy-Breite und PC).

  python3 werkzeuge/spiele_ordnen_test.py [--datei X.py] [--bilder ORDNER] [--name nachher]

Prüft: die Seite «Mehr» hat genau EINEN Einstieg zu den Spielen (Unterreiter «Spielen»); dort öffnet die Kachel «Spielecke»
die Seite /party; «Spiele freigeben» geht von der Spielecke aus (öffnen, QR-Code, schliessen) und nur für den Administrator;
ein Benutzer ohne Administrator-Rolle (Recht «Spiele») findet die Spielecke weiter über die Übersicht; alle Adressen gehen
weiter (/party, /spiele, /p/<key>/). Mit --bilder: Bilder der Seiten in Handy-Breite (<name>_mehr.png …).
"""
import argparse
import base64
import glob
import os
import re
import shutil
import sys
import tempfile
import threading

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--name", default="nachher")
    ap.add_argument("--nur-bilder", action="store_true", help="nur die Bilder (für den Stand vorher), keine Prüfung")
    a = ap.parse_args()
    datei = a.datei or sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    home = tempfile.mkdtemp(prefix="mw_ordnen_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_ordnen_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *x, **k: None
    ns["GAMESRV"]["port"] = 1                                # no games port in this test
    CFG = ns["CFG"]
    CFG.update(https_extra=False, lang="de", setup_done=True)
    PW = "Admin-Pass-123"
    assert ns["web_pw_set"](PW)[0]
    okk, err = ns["users_action"]({"action": "add", "name": "Kim", "password": "kim-pass-12", "role": "kid"})
    assert okk, err
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    from werkzeug.serving import make_server
    srv = make_server("127.0.0.1", 0, ws.app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    fehler = []

    def ok(c, what):
        print(("  ✓ " if c else "  ✗ ") + what, flush=True)
        if not c:
            fehler.append(what)
        return c
    from playwright.sync_api import sync_playwright
    SICHT = """(sel) => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
        return r.width > 4 && r.height > 4 && s.display !== "none" && s.visibility !== "hidden" && !e.closest("[hidden]"); }).map(e => e.getAttribute("href") + "|" + (e.closest("nav") ? "nav" : "main"))"""
    # the guided tour of a fresh installation (516) lies over the page: not part of this test
    OHNE_TOUR = """document.addEventListener("DOMContentLoaded", () => { const s = document.createElement("style");
        s.textContent = "#g2-ov,#g2-spot,#g2-bub,.g2m,#gd-card{display:none!important}"; document.head.appendChild(s); });"""
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for geraet, vp, mobil in (("handy", {"width": 390, "height": 844}, True), ("pc", {"width": 1280, "height": 800}, False)):
            ctx = br.new_context(viewport=vp, is_mobile=mobil, has_touch=mobil, device_scale_factor=2 if mobil else 1, locale="de-CH",
                                 http_credentials={"username": "admin", "password": PW})
            ctx.add_init_script(OHNE_TOUR)
            pg = ctx.new_page()
            fe = []
            pg.on("pageerror", lambda e: fe.append(str(e)[:200]))

            def bild(n):
                if a.bilder and mobil:
                    os.makedirs(a.bilder, exist_ok=True)
                    pg.screenshot(path=os.path.join(a.bilder, f"mehr_{a.name}_{n}.png"), full_page=True)
            pg.goto(base + "/more", wait_until="load"); pg.wait_for_timeout(1500)
            bild("1_uebersicht")
            if a.nur_bilder:
                pg.goto(base + "/play", wait_until="load"); pg.wait_for_timeout(1500); bild("2_spielen")
                pg.goto(base + "/party", wait_until="load"); pg.wait_for_timeout(2500); bild("3_spielecke")
                ctx.close(); continue
            print(f"Administrator · {geraet}", flush=True)
            ein = pg.evaluate(SICHT, 'a[href="/play"],a[href="/party"]')
            ok(ein == ["/play|nav"], f"Seite «Mehr»: genau ein Einstieg zu den Spielen, der Unterreiter «Spielen» ({ein})")
            ok(pg.locator("#games").count() == 0 and "Spiele freigeben" not in pg.locator("main").inner_text(), "Seite «Mehr»: keine Karte «Spiele freigeben» mehr")
            sub = pg.evaluate("() => [...document.querySelectorAll('nav.subnav a')].map(a => a.getAttribute('href'))")
            ok("/party" not in sub and sub.count("/play") == 1, f"Unterreiter ohne «Spielecke», mit «Spielen»: {sub}")
            pg.locator('nav.subnav a[href="/play"]').click(); pg.wait_for_url("**/play"); pg.wait_for_timeout(1200)
            bild("2_spielen")
            t = pg.locator("#pl-party")
            ok(t.is_visible() and "Spielecke" in t.inner_text() and "🎲" in t.inner_text() and pg.evaluate("() => document.querySelector('main').firstElementChild.id") == "pl-party",
               "«Spielen»: Kachel «🎲 Spielecke» zuoberst")
            ok("Spiele freigeben" in t.inner_text() and "Vier gewinnt" in t.inner_text(), "Kachel deutsch beschriftet")
            b = t.bounding_box()
            ok(b["height"] >= 56 and b["width"] >= min(vp["width"], 720) - 40, f"Kachel gut sichtbar ({round(b['width'])} × {round(b['height'])})")
            (t.tap if mobil else t.click)(); pg.wait_for_url("**/party"); pg.wait_for_timeout(2500)
            ok(pg.url.endswith("/party"), "Kachel öffnet /party")
            ok(pg.evaluate("() => [...document.querySelectorAll('nav.subnav a.on')].map(a => a.getAttribute('href'))") == ["/play"], "auf /party leuchtet der Unterreiter «Spielen»")
            fb = pg.locator("#party-box button", has_text="Spiele freigeben")
            ok(fb.is_visible() and pg.evaluate("() => { const b = [...document.querySelectorAll('#party-box button')][0]; return b && b.textContent; }").strip().endswith("Spiele freigeben"),
               "Spielecke: «Spiele freigeben» ist der oberste Knopf")
            bild("3_spielecke")
            fb.click(); pg.wait_for_timeout(2500)
            ok(ns["party_on"]() and pg.locator("#party-box svg").count() >= 1 and pg.locator("#party-box button", has_text="Schliessen").is_visible(),
               "«Spiele freigeben» von der Spielecke aus: offen, QR-Code und «Schliessen» da")
            bild("4_spielecke_offen")
            key = ns["PARTY"]["key"]
            r = ctx.request.get(base + f"/p/{key}/")
            ok(r.status == 200 and "Spielecke" in r.text(), f"Gästeseite /p/<key>/ geht ({r.status})")
            pg.locator("#party-box button", has_text="Schliessen").click(); pg.wait_for_timeout(2000)
            ok(not ns["party_on"](), "«Schliessen» von der Spielecke aus")
            for adr in ("/party", "/more", "/play", "/tools", "/help"):
                ok(ctx.request.get(base + adr).status == 200, f"{adr} geht weiter")
            ok(not fe, "keine JavaScript-Fehler" + (": " + " | ".join(fe[:3]) if fe else ""))
            ctx.close()
        if not a.nur_bilder:
            print("Benutzerin «Kim» (Rolle Kind: Live-Bild + Spiele)", flush=True)
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="de-CH",
                                 http_credentials={"username": "Kim", "password": "kim-pass-12"})
            ctx.add_init_script(OHNE_TOUR)
            pg = ctx.new_page()
            pg.goto(base + "/more", wait_until="load"); pg.wait_for_timeout(2000)
            ein = [x for x in pg.evaluate(SICHT, 'a[href="/party"]') if x.endswith("|main")]
            ok(len(ein) == 1, f"ohne Administrator-Rolle: der Eintrag «Spielecke» bleibt in der Übersicht ({ein})")
            ok(ctx.request.get(base + "/party").status == 200, "Kind darf /party öffnen (wie bisher)")
            ok(ctx.request.get(base + "/play").status in (401, 403), "Kind darf /play nicht öffnen (wie bisher)")
            r = ctx.request.post(base + "/api/party", data={"action": "all", "hours": 2}, headers={"X-Requested-With": "XMLHttpRequest"})
            ok(r.status in (401, 403) and not ns["party_on"](), f"Kind darf nicht freigeben (wie bisher, {r.status})")
            if a.bilder:
                pg.screenshot(path=os.path.join(a.bilder, f"mehr_{a.name}_5_kind_uebersicht.png"), full_page=True)
            ctx.close()
        br.close()
    srv.shutdown()
    shutil.rmtree(home, ignore_errors=True)
    if a.nur_bilder:
        print("Bilder:", a.bilder); return
    c = ws.app.test_client(use_cookies=False)
    r = c.get("/spiele", environ_base={"REMOTE_ADDR": "192.168.1.20"})
    ok(r.status_code == 200, f"/spiele im eigenen WLAN geht ({r.status_code})")
    for f in fehler:
        print("FEHLER:", f)
    print("Spiele-ordnen-Test:", "OK" if not fehler else f"{len(fehler)} Fehler")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main()
