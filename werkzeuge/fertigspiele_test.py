#!/usr/bin/env python3
"""MoveEye: Test der fertigen freien Spiele zum Nachladen (Teil 639zzn, werkzeuge/fertigspiele/).

  python3 werkzeuge/fertigspiele_test.py                       # MoveEye-Teil mit kleinen Ersatz-Paketen (schnell, ohne Browser)
  python3 werkzeuge/fertigspiele_test.py --pakete ORDNER       # + die echten Pakete (Ausgabe von paket.py): Pins im Programm,
        [--bilder ORDNER] [--nur fs-angst,…] [--datei X.py]    #   Laden über den echten Weg, jedes Spiel im Browser

Ohne --pakete: Selbsttest, Rechte (nur der Admin lädt), zu wenig Platz, veränderte / zu grosse Datei, Laden + Entpacken,
Kachel (/spiele, Gästeseite, Reiter Spielecke), Kachelbild vom gleichen Ursprung, Spiele-Port (Knopf «✕ Zurück», keine
Pfade nach aussen, Marker nicht lesbar), Entfernen, FOTAQ-Aktionen unverändert.
Mit --pakete: die ZIP passen zu FS_GAMES (Grösse, sha256, entpackt) und jedes Spiel läuft vom Spiele-Port von MoveEye:
Handy (iPhone 13) und PC (1280 × 800), Start per Tipp bzw. Klick, kein Fehler in der Konsole, KEINE Anfrage nach aussen,
«✕ Zurück» da und über keinem Bedienelement; geladene Menge wird gemessen.
"""
import argparse
import base64
import glob
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
PC = {"width": 1280, "height": 800}


def neueste_datei():
    c = sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    return c[-1]


def _fake(gid, tag, start):
    """a tiny package with the layout of the real one"""
    files = {start: ("<!doctype html><html><head><title>%s</title></head><body><h1>%s</h1></body></html>" % (gid, gid)).encode(),
             "thumb.png": base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="),
             "LIZENZEN.txt": b"Test", "fspiel.json": json.dumps({"id": gid, "tag": tag}).encode(), "sub/a.txt": b"abc"}
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_STORED) as z:
        for n, d in sorted(files.items()):
            z.writestr(n, d)
    return b.getvalue(), sum(len(d) for d in files.values())


def hell(png):
    """share of pixels that are not (nearly) black and the number of different colours (coarse)"""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB").resize((96, 96))
    px = list(im.getdata())
    return sum(1 for p in px if max(p) > 40) / len(px), len({(p[0] >> 4, p[1] >> 4, p[2] >> 4) for p in px})


# what «✕ Zurück» of MoveEye covers: a button / link of the game below it (the same rule as in GAME_BACK)
UEBERDECKT = """() => { const b = document.getElementById("mw-back"); if (!b || getComputedStyle(b).display === "none") return [];
  const r = b.firstElementChild.getBoundingClientRect(), out = [];
  for (let i = 0; i <= 4; i++) for (let j = 0; j <= 2; j++) {
    const x = Math.min(innerWidth - 1, Math.max(0, r.left + 2 + (r.width - 4) * i / 4)), y = Math.min(innerHeight - 1, Math.max(0, r.top + 2 + (r.height - 4) * j / 2));
    for (const q of document.elementsFromPoint(x, y)) { if (b.contains(q) || q === document.body || q === document.documentElement) continue;
      const c = q.closest && q.closest("a,button,input,select,textarea,label,[role=button],[onclick]"); if (c) out.push(c.id || c.tagName); } }
  return [...new Set(out)]; }"""
ZURUECK = """() => { const b = document.getElementById("mw-back"); if (!b) return "fehlt";
  if (getComputedStyle(b).display !== "none") { const r = b.firstElementChild.getBoundingClientRect(); return r.width >= 40 && r.height >= 36 && r.top >= 0 && r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight ? "ok" : "ausserhalb"; }
  const a = [...document.querySelectorAll('a[href="../"],a[href="index.html"]')].filter(x => !b.contains(x) && x.getBoundingClientRect().width >= 40 && x.getBoundingClientRect().height >= 30);
  return a.length ? "ok" : "versteckt ohne eigenen Knopf"; }"""


class Lauf:
    """one game on one device: page, console errors, requests to the outside, bytes loaded"""

    def __init__(self, br, pw, base, gid, start, geraet, quer=False):
        self.gid, self.geraet, self.touch = gid, geraet, geraet != "PC"
        if self.touch:
            dev = dict(pw.devices["iPhone 13 landscape" if quer else "iPhone 13"])
            dev.pop("default_browser_type", None)
            self.ctx = br.new_context(**dev)
        else:
            self.ctx = br.new_context(viewport=PC)
        self.aussen, self.fe, self.bytes, self.n404 = [], [], 0, []
        self.base = base
        self.ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:"))
                       else (self.aussen.append(r.request.url[:120]), r.abort()))
        self.pg = self.ctx.new_page()
        self.pg.on("pageerror", lambda e: self.fe.append("pageerror: " + str(e)[:300]))
        self.pg.on("console", lambda m: self.fe.append("console.error: " + m.text[:300]) if m.type == "error" else None)
        self.pg.on("response", self._resp)
        self.pg.on("websocket", lambda w: self.aussen.append("websocket " + w.url[:100]))
        self.pg.goto(f"{base}/g/{gid}/{start}", wait_until="load", timeout=90000)

    def _resp(self, r):
        if r.status == 404:
            self.n404.append(r.url[len(self.base):][:100])
        try:
            n = r.header_value("content-length")
            self.bytes += int(n) if n and r.status == 200 else 0
        except Exception:
            pass

    def tipp(self, x, y):
        self.pg.touchscreen.tap(x, y) if self.touch else self.pg.mouse.click(x, y)

    def druck(self, x, y, ms=160):
        """a tap that lasts as long as a finger (games that poll «is pressed» once per frame miss a 0 ms tap)"""
        if self.touch:
            cdp = self.ctx.new_cdp_session(self.pg)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
            self.pg.wait_for_timeout(ms)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            cdp.detach()
        else:
            self.pg.mouse.move(x, y); self.pg.mouse.down(); self.pg.wait_for_timeout(ms); self.pg.mouse.up()

    def tipp_el(self, sel, timeout=15000):
        loc = self.pg.locator(sel).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.tap() if self.touch else loc.click()

    def bild(self, bilder, name):
        if bilder:
            os.makedirs(bilder, exist_ok=True)
            self.pg.screenshot(path=os.path.join(bilder, f"{self.gid}_{self.geraet}_{name}.png"))

    def warte(self, ms):
        self.pg.wait_for_timeout(ms)

    def ende(self):
        self.ctx.close()


# ---- the games: start by touch / click until the game really runs; returns a short text for the table --------------------------
def spiel_angst(L, bilder, ok):
    pg = L.pg
    pg.wait_for_function("() => document.getElementById('loading').getAttribute('loaded') === 'yes'", timeout=180000)
    L.warte(800)
    L.bild(bilder, "1_start")
    L.tipp_el("#loading")                                      # «LOS!»
    pg.wait_for_function("() => getComputedStyle(document.getElementById('loading')).display === 'none'", timeout=10000)
    L.warte(2500)
    ok(pg.title() == "Abenteuer mit Angst!", "deutsche Fassung (Titel «%s»)" % pg.title())
    ok("psychische" in pg.content() or "Angst" in pg.content(), "deutscher Text auf der Seite")
    vw, vh = pg.viewport_size["width"], pg.viewport_size["height"]
    box = pg.locator("#game_container").bounding_box()
    ok(box and box["width"] <= vw + 1 and box["x"] >= -1, f"Spielfläche passt in die Breite ({box and round(box['width'])} von {vw})")
    t0 = pg.evaluate("() => document.getElementById('game_words').innerText + '|' + document.getElementById('game_choices').innerText")
    h0 = hell(pg.locator("#game_container").screenshot())
    # tap on: the content note / start button, then the story advances with every tap on the game
    texte = set()
    for i in range(14):
        ch = pg.locator("#game_choices > div:visible, #content_notes button:visible, #about button:visible")
        if ch.count():
            (ch.first.tap if L.touch else ch.first.click)(timeout=5000)
        else:
            L.tipp(box["x"] + box["width"] / 2, box["y"] + box["height"] * 0.45)
        L.warte(1800)
        texte.add(pg.evaluate("() => document.getElementById('game_words').innerText.trim().slice(0, 200)"))
        if i == 5:
            L.bild(bilder, "2_spiel")
    L.bild(bilder, "3_spiel")
    texte.discard("")
    ok(len(texte) >= 2, f"die Geschichte läuft per {'Tipp' if L.touch else 'Klick'} weiter ({len(texte)} verschiedene Texte)")
    h1 = hell(pg.locator("#game_container").screenshot())
    ok(h1[0] > 0.05 and h1[1] >= 4, f"Bild ist da (hell {h1[0]:.2f}, {h1[1]} Farben)")
    stille = pg.evaluate("""async () => { const o = {}; for (const f of ["sounds/music/pokemon.mp3", "sounds/sfx/hadouken.mp3"]) { const r = await fetch(f); o[f] = (await r.arrayBuffer()).byteLength; } return o; }""")
    ok(stille["sounds/music/pokemon.mp3"] < 40000 and stille["sounds/sfx/hadouken.mp3"] < 4000, f"die zwei nicht freien Klänge sind Stille ({stille})")
    return "Geschichte läuft"


SPIELE = {"fs-angst": {"lauf": spiel_angst, "quer": False}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--pakete", default="", help="Ausgabe von werkzeuge/fertigspiele/paket.py (ZIP + pins.txt)")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--nur", default="")
    ap.add_argument("--ohne-pins", action="store_true", help="die Pins im Programm nicht mit pins.txt vergleichen (Entwicklung)")
    a = ap.parse_args()
    datei = a.datei or neueste_datei()
    import urllib.request
    sys.path.insert(0, HIER)
    from piper_test import Srv
    fehler = []
    home = tempfile.mkdtemp(prefix="mw_fspiele_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_fspiele_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *x, **k: None
    ns["lan_guest_ip"] = lambda ip, fwd="": not fwd          # test: 127.0.0.1 counts as own Wi-Fi (on the device: tunnel = outside)
    CFG, G, DL, TAG = ns["CFG"], ns["FS_GAMES"], ns["FS_DL"], ns["FS_TAG"]

    def ok(c, what, vor="MoveEye"):
        print(("  ✓ " if c else "  ✗ ") + what, flush=True)
        if not c:
            fehler.append(f"{vor}: {what}")
        return c
    print(f"Fertige Spiele · {os.path.basename(datei)} · {TAG} · {', '.join(G)}", flush=True)
    ok(ns["fs_selftest"](), "Selbsttest 639zzn")
    ok(ns["fotaq_selftest"](), "Selbsttest 639zzg (FOTAQ unverändert)")
    srv = Srv()
    echt = {}
    if a.pakete:
        tx = open(os.path.join(a.pakete, "pins.txt"), encoding="utf-8").read()
        for m in re.finditer(r"^PIN (fspiele-([a-z0-9]+)-\d+\.zip) size=(\d+) sha256=([0-9a-f]{64}) unpacked=(\d+)", tx, re.M):
            echt["fs-" + m.group(2)] = {"name": m.group(1), "size": int(m.group(3)), "sha256": m.group(4), "unpacked": int(m.group(5))}
        for gid in G:
            if gid not in echt:
                ok(False, f"{gid}: fehlt in pins.txt"); continue
            if not a.ohne_pins:
                ok(G[gid]["file"] == echt[gid], f"{gid}: Pins im Programm = pins.txt ({echt[gid]['size']} Bytes)")
            b = open(os.path.join(a.pakete, echt[gid]["name"]), "rb").read()
            ok(len(b) == echt[gid]["size"] and hashlib.sha256(b).hexdigest() == echt[gid]["sha256"], f"{gid}: ZIP passt zu pins.txt")
            G[gid]["file"] = dict(echt[gid])
            srv.files["/" + TAG + "/" + echt[gid]["name"]] = b
    else:
        for gid, g in G.items():
            b, unz = _fake(gid, TAG, g["tile"]["start"])
            g["file"] = {"name": g["file"]["name"], "size": len(b), "sha256": hashlib.sha256(b).hexdigest(), "unpacked": unz}
            srv.files["/" + TAG + "/" + g["file"]["name"]] = b
    ns["FS_BASE"]["url"] = srv.url + TAG + "/"
    CFG.update(https_extra=False, lang="de", tausch_free_gb=0.1)
    PW = "Admin-Pass-123"
    assert ns["web_pw_set"](PW)[0]
    okk, err = ns["users_action"]({"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
    assert okk, err
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    c = ws.app.test_client(use_cookies=False)
    H = {"Authorization": "Basic " + base64.b64encode(f"admin:{PW}".encode()).decode()}
    HA = {"Authorization": "Basic " + base64.b64encode(b"Anna:anna-pass-1").decode()}

    def party(d=None, h=H):
        r = c.post("/api/party", json=d, headers=h) if d else c.get("/api/party", headers=h)
        return r.status_code, (r.get_json(silent=True) or {})

    def warten(limit=900):
        t0 = time.time()
        while DL["running"] and time.time() - t0 < limit:
            time.sleep(0.1)
    ids = list(G)
    g0 = ids[0]
    code, j = party()
    S = (j.get("fotaq") or {}).get("fs") or {}
    ok(code == 200 and [x["id"] for x in S.get("games", [])] == ids and all(x["pinned"] and not x["installed"] for x in S["games"]),
       f"/api/party: {len(ids)} Spiele gepinnt, keines installiert")
    ok("pinned" in (j.get("fotaq") or {}) and "langs" in j["fotaq"], "/api/party: Zustand von FOTAQ unverändert daneben")
    ok(all(x.get("dir") not in G for x in j.get("games", [])), "nicht installiert: keine Kachel")
    code, j = party({"action": "fotaq_install", "fs": g0}, HA)
    ok(code == 403, f"Familie darf nicht laden ({code})")
    code, j = party({"action": "fotaq_install", "fs": "fs-gibtsnicht"})
    ok(code == 400, f"unbekanntes Spiel abgelehnt ({code})")
    CFG["tausch_free_gb"] = 1e6
    code, j = party({"action": "fotaq_install", "fs": g0})
    ok(code == 400 and "Platz" in str(j.get("error")) and not DL["running"], f"zu wenig Platz: nicht geladen ({code} {j.get('error')})")
    CFG["tausch_free_gb"] = 0.1
    pfad = "/" + TAG + "/" + G[g0]["file"]["name"]
    srv.tamper.add(pfad)
    party({"action": "fotaq_install", "fs": g0}); warten()
    ok(not ns["fs_installed"](g0) and "checksum" in DL["msg"], f"veränderte Datei abgelehnt ({DL['msg']})")
    srv.tamper.discard(pfad)
    srv.extra = b"x" * 10
    party({"action": "fotaq_install", "fs": g0}); warten()
    ok(not ns["fs_installed"](g0) and ("large" in DL["msg"] or "size" in DL["msg"] or "checksum" in DL["msg"]), f"zu grosse Datei abgelehnt ({DL['msg']})")
    srv.extra = b""
    ok(not os.path.isdir(ns["fs_dir"](g0)), "nach einem Fehler bleibt kein halber Ordner")
    for gid in ids:
        t0 = time.time()
        code, j = party({"action": "fotaq_install", "fs": gid}); warten()
        ok(code == 200 and ns["fs_installed"](gid) and DL["done"] and not DL["msg"], f"{gid}: geladen und entpackt in {time.time() - t0:.1f} s ({DL['msg'] or 'ok'})")
    ok(not os.path.exists(ns["fs_dl_dir"]()), "ZIP danach gelöscht")
    code, j = party()
    ok(all(x["installed"] for x in j["fotaq"]["fs"]["games"]), "/api/party: alle installiert")
    gl = ns["games_list"]()
    ok([x["dir"] for x in gl if x["dir"] in G] == ids and all(x["icon"] == "thumb.png" for x in gl), "Kacheln in games_list()")
    ok(ns["games_list"](extra=False) == [], "games_list(extra=False): die Sammlung allein (leer)")
    r = c.get("/spiele", environ_base={"REMOTE_ADDR": "192.168.1.20"})
    t = r.get_data(as_text=True)
    ok(r.status_code == 200 and all(G[g]["tile"]["name"] in t and f'src="/spiele/thumb/{g}"' in t and G[g]["tile"]["desc"].replace("’", "&#x27;") in t.replace("&#x27;", "&#x27;") for g in ids),
       "/spiele zeigt die Kacheln mit Bild, Name und Beschreibung")
    ok(all("⚠️ " + G[g]["tile"]["note"] in t for g in ids if G[g]["tile"].get("note")) and "⚠️ Ab ca. 12 Jahren, mit Kraftausdrücken" in t, "/spiele: Hinweis auf der Kachel (Angst: ab ca. 12 Jahren)")
    ok(all("Englisch, wenig Text" in G[g]["tile"]["desc"] for g in ids if g != "fs-angst"), "englische Spiele: «Englisch, wenig Text» in der Beschreibung")
    ok("👆 Für Handy und Tablet (Touch)" in t, "/spiele: Gruppe «Für Handy und Tablet»")
    pv = ns["party_view"]("") if "party_view" in ns else {}
    ok(all(any(x.get("dir") == g for x in (pv.get("games") or [])) for g in ids), "Gästeseite /p/<key>/: Kacheln da")
    for g in ids:
        r = c.get("/spiele/thumb/" + g, environ_base={"REMOTE_ADDR": "192.168.1.20"})
        r2 = c.get("/party/thumb/" + g, headers=H)
        ok(r.status_code == 200 and r.mimetype == "image/png" and r2.status_code == 200, f"{g}: Kachelbild vom gleichen Ursprung ({r.status_code} {r.mimetype})")
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); wp = sk.getsockname()[1]
    if not ns["GAMESRV"]["port"]:
        CFG["web_port"] = wp - 2
        ns["games_server_start"]()
    gp = ns["GAMESRV"]["port"]
    ok(gp > 0, f"Spiele-Port läuft ({gp})")
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(path, hdr=None):
        try:
            with op.open(urllib.request.Request(f"http://127.0.0.1:{gp}{path}", headers=hdr or {}), timeout=60) as x:
                return x.status, dict(x.headers), x.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), b""
    for g in ids:
        s_, h_, b_ = get(f"/g/{g}/")
        ok(s_ == 200 and b'id="mw-back"' in b_, f"Port: /g/{g}/ = Startseite mit «✕ Zurück» von MoveEye")
        s_, h_, b_ = get(f"/g/{g}/LIZENZEN.txt")
        ok(s_ == 200 and len(b_) > 3, f"Port: /g/{g}/LIZENZEN.txt")
        for bad in (f"/g/{g}/fspiel.ok", f"/g/{g}/../settings.json", f"/g/{g}/%2e%2e/settings.json", f"/g/{g}/../{ids[-1]}.new/x", f"/g/{g}/../../users.json"):
            s_, _h, _b = get(bad)
            ok(s_ == 404, f"Port: {bad} -> 404 ({s_})")
    if echt:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            sys.exit("Playwright fehlt (pip install playwright && python3 -m playwright install chromium)")
        nur = [x for x in a.nur.split(",") if x] or ids
        base = f"http://127.0.0.1:{gp}"
        zeilen = []
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=ARGS)
            for gid in nur:
                for geraet in ("Handy", "PC"):
                    print(f"{gid} · {geraet}", flush=True)
                    vor = f"{gid} {geraet}"
                    L = None
                    try:
                        L = Lauf(br, pw, base, gid, G[gid]["tile"]["start"], geraet, quer=SPIELE[gid]["quer"])
                        was = SPIELE[gid]["lauf"](L, a.bilder, lambda cnd, what, vor=vor: ok(cnd, what, vor))
                        z = L.pg.evaluate(ZURUECK)
                        ok(z == "ok", f"«✕ Zurück» zu den Spielen: {z}", vor)
                        ue = L.pg.evaluate(UEBERDECKT)
                        ok(not ue, "«✕ Zurück» liegt über keinem Bedienelement" + (f" ({', '.join(ue)})" if ue else ""), vor)
                        ok(not L.fe, "keine Fehler in der Konsole" + (": " + " | ".join(L.fe[:4]) if L.fe else ""), vor)
                        ok(not L.aussen, "keine Anfrage nach aussen" + (": " + ", ".join(L.aussen[:4]) if L.aussen else ""), vor)
                        ok(not L.n404, "keine fehlende Datei" + (": " + ", ".join(L.n404[:6]) if L.n404 else ""), vor)
                        zeilen.append(f"{gid:<12} {geraet:<6} {L.bytes / 1e6:6.1f} MB geladen · {was}")
                    except Exception as e:
                        ok(False, f"Abbruch: {str(e)[:300]}", vor)
                        if L:
                            L.bild(a.bilder, "abbruch")
                    finally:
                        if L:
                            L.ende()
            br.close()
        print("\n".join(zeilen), flush=True)
    for gid in ids:
        code, j = party({"action": "fotaq_delete", "fs": gid})
        ok(code == 200 and not ns["fs_installed"](gid) and not os.path.exists(ns["fs_dir"](gid)), f"{gid}: Entfernen")
    ok(all(x.get("dir") not in G for x in ns["games_list"]()), "nach dem Entfernen: keine Kachel")
    code, j = party({"action": "fotaq_delete"})
    ok(code == 200, "FOTAQ-Aktion ohne «fs» geht weiter an FOTAQ")
    shutil.rmtree(home, ignore_errors=True)
    for f in fehler:
        print("FEHLER:", f)
    print("Fertige-Spiele-Test:", "OK" if not fehler else f"{len(fehler)} Fehler")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main()
