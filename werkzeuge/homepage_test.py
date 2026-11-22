#!/usr/bin/env python3
"""Test «🌐 Homepage» (Teil 639zzzh) gegen einen falschen Webspace auf localhost – nie gegen den echten.

Der falsche Webspace hat dieselbe Schnittstelle wie der des Besitzers: POST /api/moveeye/upload?path= (Bearer-Schlüssel und
«X-KV: 1», Inhalt = Bytes, höchstens 100 MB pro Datei, Platz begrenzt), GET /api/moveeye/files, DELETE /api/moveeye/files?path=,
öffentlich /moveeye/<Pfad>; er macht wie das Original aus jedem Punkt ausser dem letzten «_» und unterscheidet Gross / Klein.
Dazu Störungen auf Wunsch: 404, Umleitung auf eine andere Herkunft (zweiter Server), falscher Content-Type, nosniff,
Content-Security-Policy (connect-src 'none', script-src ohne 'wasm-unsafe-eval'), 500 beim ersten Versuch, Platz voll.

Geprüft: nur der Admin (Seite, API, /api/set, Eintrag unter «Mehr»); der Schlüssel steht nirgends ausser in der
Einstellungs-Datei (Zustand, Status, Protokoll, alle anderen Dateien, Export für Nicht-Admins, Fehlertexte des Servers); alles
hochgeladen (Funk/ = funk/ des Repositorys, Sim/ = sim-web.zip, test.html; drei Schalter Startseite (ab Werk aus) /
Funkgerät / Simulator / Besucherseite Info/ (ab Werk an; 22.11.2026: Produktseite ohne Senden und ohne Kontaktadresse, Kapitel-Knöpfe nur mit einem Sim, der «kapitel» kennt): ein Teil aus = weder hochgeladen noch gelöscht, die Prüfung überspringt ihn, alle aus = gesperrt); nur Geändertes; nur eigene Dateien
gelöscht; falscher Schlüssel, Platz voll, zu grosse Datei; Wiederholen nach 500; Umleitung beim Hochladen nie befolgt; die
Prüfung findet 404, Umleitung auf andere Herkunft, falschen Typ, nosniff und die CSP-Sperren; automatisch nur, wenn sich der
Inhalt geändert hat, nie während eines Alarms; das Paket sim-web.zip nur mit der signierten Prüfsumme (Teil 300 «anhang.web»),
werkzeuge/sim_web_paket.py; Texte in 5 Sprachen.

  python3 werkzeuge/homepage_test.py [--datei webcam_bewegung_X_Y_Z.py]
"""
import argparse
import base64
import glob
import hashlib
import http.server
import io
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import sim_web_paket  # noqa: E402

FEHLER = []
N = {"ok": 0}
HOMES = []
KEY = "Test-" + base64.b16encode(os.urandom(10)).decode().lower()          # erzeugte Ersatz-Werte, nie echte
KEY2 = "Neu-" + base64.b16encode(os.urandom(10)).decode().lower()
ADMIN_PW = "Admin-" + base64.b16encode(os.urandom(6)).decode().lower()
TYPES = {"html": "text/html; charset=utf-8", "js": "text/javascript", "wasm": "application/wasm", "png": "image/png", "pck": "application/octet-stream",
         "webmanifest": "application/manifest+json", "json": "application/json"}


def ok(cond, what):
    if cond:
        N["ok"] += 1
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


class Webspace:
    """der falsche Webspace (gleiche Schnittstelle, Umbenennung, Gross / Klein) + Störungen"""

    def __init__(self, key):
        self.key, self.files, self.log, self.quota, self.max_file = key, {}, [], 500 * 1024 * 1024, 100 * 1024 * 1024
        self.fail_once, self.csp, self.ctype, self.hide, self.redirect, self.nosniff, self.echo = set(), "", {}, set(), {}, False, False
        self.up_redirect = False
        ws = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, body=b"", hdr=None):
                self.send_response(code)
                for k, v in (hdr or {}).items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)

            def _auth(self, write):
                if self.headers.get("Authorization") != "Bearer " + ws.key:
                    msg = b'{"error":"unauthorized"' + ((b',"got":"' + (self.headers.get("Authorization") or "").encode() + b'"') if ws.echo else b"") + b"}"
                    self._send(401, msg, {"Content-Type": "application/json"})
                    return False
                if write and self.headers.get("X-KV") != "1":
                    self._send(403, b'{"error":"X-KV missing"}')
                    return False
                return True

            def _rec(self):
                u = urllib.parse.urlsplit(self.path)
                ws.log.append((self.command, u.path, urllib.parse.parse_qs(u.query).get("path", [""])[0], self.headers.get("Authorization") or ""))
                return u

            def do_GET(self):
                u = self._rec()
                if u.path == "/api/moveeye/files":
                    if self._auth(False):
                        self._send(200, json.dumps({"files": [{"path": p, "size": len(b)} for p, b in sorted(ws.files.items())]}).encode(),
                                   {"Content-Type": "application/json"})
                    return
                if u.path.startswith("/moveeye/"):
                    p = urllib.parse.unquote(u.path[9:])
                    if p in ws.redirect:
                        self._send(302, b"", {"Location": ws.redirect[p]})
                        return
                    if p == "" or p.endswith("/"):
                        p += "index.html"
                    if p not in ws.files or p in ws.hide:
                        self._send(404, b"not found", {"Content-Type": "text/plain"})
                        return
                    ext = p.rsplit(".", 1)[-1]
                    h = {"Content-Type": ws.ctype.get(p, TYPES.get(ext, "application/octet-stream"))}
                    if ws.csp and ext == "html":
                        h["Content-Security-Policy"] = ws.csp
                    if ws.nosniff:
                        h["X-Content-Type-Options"] = "nosniff"
                    self._send(200, ws.files[p], h)
                    return
                self._send(404, b"no")

            def do_POST(self):
                u = self._rec()
                n = int(self.headers.get("Content-Length") or 0)
                data = self.rfile.read(n)
                if u.path != "/api/moveeye/upload":
                    self._send(404, b"no")
                    return
                if not self._auth(True):
                    return
                if ws.up_redirect:
                    self._send(307, b"", {"Location": "http://127.0.0.1:%d/api/moveeye/upload?path=x" % OTHER["port"]})
                    return
                p = urllib.parse.parse_qs(u.query).get("path", [""])[0]
                if p in ws.fail_once:
                    ws.fail_once.discard(p)
                    self._send(500, b"oops")
                    return
                if n > ws.max_file:
                    self._send(413, b'{"error":"file too large"}')
                    return
                if sum(len(b) for q, b in ws.files.items() if q != p) + n > ws.quota:
                    self._send(507, b'{"error":"quota exceeded"}')
                    return
                d, _, name = p.rpartition("/")
                a, dot, e = name.rpartition(".")
                name = (a.replace(".", "_") + "." + e) if dot else name          # wie das Original: nur der letzte Punkt bleibt
                p2 = (d + "/" if d else "") + name
                ws.files[p2] = data
                self._send(200, json.dumps({"ok": True, "path": p2, "size": n}).encode(), {"Content-Type": "application/json"})

            def do_DELETE(self):
                u = self._rec()
                p = urllib.parse.parse_qs(u.query).get("path", [""])[0]
                if u.path != "/api/moveeye/files" or not self._auth(True):
                    return
                ws.files.pop(p, None)
                self._send(200, b'{"ok":true}')

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def uploads(self):
        return [x for x in self.log if x[0] == "POST"]


OTHER = {"port": 0, "log": []}


def andere_herkunft():
    """ein zweiter Server (andere Herkunft) als Ziel einer Umleitung: merkt sich, ob je ein Schlüssel ankommt"""
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _do(self):
            OTHER["log"].append((self.command, self.path, self.headers.get("Authorization") or ""))
            body = b"\0asm" + b"x" * 100
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        do_GET = do_POST = _do
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    OTHER["port"] = s.server_address[1]
    threading.Thread(target=s.serve_forever, daemon=True).start()


def fake_sim_zip(ordner, wasm_extra=b""):
    """ein kleiner falscher Godot-Web-Export (8 Dateien, Namen wie Godot) -> sim-web.zip mit werkzeuge/sim_web_paket.py"""
    ex = os.path.join(ordner, "export")
    shutil.rmtree(ex, ignore_errors=True)
    os.makedirs(ex)
    import sim_web_sandbox as sb                          # die Stellen der Godot-4.3-Fassung, die das Paket patcht
    files = {"index.html": '<html><head><link rel="icon" href="index.icon.png"><link rel="apple-touch-icon" href="index.apple-touch-icon.png"></head>'
                           '<body><script src="index.js"></script><script>\n' + sb.HTML_ALT + "\t}\n\tif (x) {\n\t} else {\n"
                           "\t\tsetStatusMode('progress');\n\t\tengine.startGame({\n\t\t\t'onProgress': function () {},\n"
                           "\t\t}).then(() => {\n\t\t\tsetStatusMode('hidden');\n\t\t}, displayFailureNotice);\n\t}\n</script></body></html>",
             "index.js": "function locate(path){ if (path.endsWith('.audio.worklet.js')) {\n return `${loadPath}.audio.worklet.js`;\n} }\n"
                         + "".join(a for a, _ in sb.JS_ERSATZ),
             "index.audio.worklet.js": "class W extends AudioWorkletProcessor{}", "index.wasm": b"\0asm\x01\0\0\0" + os.urandom(3000) + wasm_extra,
             "index.pck": os.urandom(12000000 + 5000), "index.png": b"\x89PNG-boot", "index.icon.png": b"\x89PNG-icon", "index.apple-touch-icon.png": b"\x89PNG-apple"}
    for n, d in files.items():
        with open(os.path.join(ex, n), "wb") as f:
            f.write(d.encode() if isinstance(d, str) else d)
    z = os.path.join(ordner, "sim-web.zip")
    sim_web_paket.packen(ex, z)
    return z


def laden(datei):
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_hp_home_")
    HOMES.append(os.environ["MOTIONWATCH_HOME"])
    ns = {"__name__": "mw_hp_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


def fmt(ns, j, L="de"):
    """the state as the page shows it: HP_FMT_JS of the program in node, with the texts of the language L"""
    import subprocess
    D = {k: ns["tr"](k, L) for k in ns["HP_TEXTS"]}
    js = ns["HP_FMT_JS"] + "\nconst D = " + json.dumps(D) + ", t = k => D[k] || k, j = " + json.dumps(j) + ";\n" + \
        "const rows = ((j.check || {}).rows || []).map(r => hpRow(r, t));\n" + \
        "console.log(JSON.stringify({err: hpErr(j.err, t), prog: hpProg(j.prog), note: j.last ? hpNote(j.last.note, t) : '', " + \
        "last: j.last ? hpLast(j.last, t) : '', rows: rows, sum: hpSum(rows, t), ren: (j.last || {}).ren || []}));"
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-500:]
    return json.loads(r.stdout)


def warte(HP, s=60):
    t0 = time.time()
    time.sleep(0.05)
    while HP["busy"] and time.time() - t0 < s:
        time.sleep(0.05)


def main():
    ap = argparse.ArgumentParser(description="Homepage (Teil 639zzzh) gegen einen falschen Webspace")
    ap.add_argument("--datei", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else neueste()
    tmp = tempfile.mkdtemp(prefix="mw_hp_")
    try:
        lauf(datei, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        for h in HOMES:
            shutil.rmtree(h, ignore_errors=True)
    print(f"Homepage-Test: {N['ok']} ok, {len(FEHLER)} Fehler")
    return 1 if FEHLER else 0


def lauf(datei, tmp):
    print("0) sim_web_paket.py (Paket für Sim/)", flush=True)
    zp = fake_sim_zip(tmp)
    with zipfile.ZipFile(zp) as z:
        names = sorted(z.namelist())
        js = z.read("index.js").decode()
        html = z.read("index.html").decode()
    ok(names == sorted(["index.html", "index.js", "index.wasm", "index.pck", "index_audio_worklet.js", "index.png", "index_icon.png",
                        "index_apple-touch-icon.png", "index_pck1.wasm", "index_pck2.wasm"]), f"8 Dateien + 2 Teile, je ein Punkt: {names}")
    ok("/*mw-sandbox*/" in js and "/*mw-sandbox*/" in html, "Sandbox-Patch in index.js und index.html")
    ok("const PARTS = ['index_pck1.wasm', 'index_pck2.wasm'];" in html and "engine.startGame" not in html
       and re.search(r'<script src="index\.js\?v=[0-9a-f]{12}"></script>', html), "index.html: lädt die Teile selbst, index.js?v=…")
    ok("`${loadPath}_audio_worklet.js`" in js and ".audio.worklet.js`" not in js, "index.js lädt index_audio_worklet.js")
    ok('"index_icon.png"' in html and '"index_apple-touch-icon.png"' in html and "index.icon.png" not in html, "index.html: Symbole mit einem Punkt")
    bad = os.path.join(tmp, "bad.zip")
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("index.audio.worklet.js", "x")
        z.writestr("../x.js", "x")
    ok(sim_web_paket.pruefen(zp) == [] and len(sim_web_paket.pruefen(bad)) >= 2, "pruefen: gut / schlecht")

    ns = laden(datei)
    CFG, HP = ns["CFG"], ns["HP"]
    ns["HP_TEST_HTTP"] = True
    ns["HP_RETRY"][:] = [0.05, 0.1]
    ns["GAMESRV"]["port"] = 1
    ns["sim_manifest_refresh"] = lambda *a, **k: None                    # kein Netz: versions.json kommt im Test von Hand
    CFG.update(https_extra=False, lang="de", setup_done=True, update_url="")
    assert ns["web_pw_set"](ADMIN_PW)[0]
    okk, err = ns["users_action"]({"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
    assert okk, err
    okk, err = ns["users_action"]({"action": "add", "name": "Cus", "password": "cus-pass-1", "role": "custom"})
    assert okk, err
    ns["users_action"]({"action": "update", "name": "Cus", "perms": ["live", "settings"]})
    wst = ns["WebStream"](None)
    wst._serve = lambda app, ctx: None
    wst.start()
    c = wst.app.test_client(use_cookies=False)
    H = {"admin": basic("admin", ADMIN_PW), "Anna": basic("Anna", "anna-pass-1"), "Cus": basic("Cus", "cus-pass-1")}
    W = Webspace(KEY)
    andere_herkunft()
    base = "http://127.0.0.1:%d" % W.port

    def api(who="admin", d=None, lang="de", wait=True):
        if d is None:
            r = c.get("/api/homepage?lang=" + lang, headers=H[who])
        else:
            r = c.post("/api/homepage?lang=" + lang, json=dict(d, lang=lang), headers=H[who])
            if wait:
                warte(HP)
                if r.status_code == 200:
                    r2 = c.get("/api/homepage?lang=" + lang, headers=H[who])
                    return r2.status_code, r2.get_json(silent=True) or {}
        return r.status_code, r.get_json(silent=True) or {}

    print("1) ab Werk, nur der Admin", flush=True)
    ok(CFG["hp_base"] == "https://kevlaschef.com" and CFG["hp_auto"] is True and CFG["hp_key"] == "", "ab Werk: kevlaschef.com, automatisch an, kein Schlüssel")
    ok(CFG["hp_start_on"] is False and ns["DEFAULTS"]["hp_start_on"] is False, "ab Werk: «Startseite mit hochladen» aus")
    code, j = api()
    ok(code == 200 and j.get("key_set") is False and j.get("base") == "https://kevlaschef.com", f"Admin sieht den Status: {code}")
    for who in ("Anna", "Cus"):
        ok(api(who)[0] == 403 and api(who, {"action": "key", "key": KEY}, wait=False)[0] == 403 and not CFG["hp_key"], f"{who}: API verboten")
        ok(c.get("/homepage", headers=H[who]).status_code == 403, f"{who}: Seite verboten")
        c.post("/api/set", json={"key": "hp_base", "value": "https://boese.example"}, headers=H[who])
        c.post("/api/text", json={"key": "hp_key", "value": "boese-1234"}, headers=H[who])
        c.post("/api/set", json={"key": "hp_start_on", "value": True}, headers=H[who])
        ok(CFG["hp_base"] == "https://kevlaschef.com" and not CFG["hp_key"] and CFG["hp_start_on"] is False, f"{who}: /api/set / /api/text gehen nicht")
        ok('href="/homepage"' not in c.get("/more", headers=H[who]).get_data(as_text=True), f"{who}: kein Eintrag unter «Mehr»")
    ok('href="/homepage"' in c.get("/more", headers=H["admin"]).get_data(as_text=True), "Admin: Eintrag «🌐 Homepage» unter «Mehr»")
    pg = c.get("/homepage", headers=H["admin"])
    ok(pg.status_code == 200 and "hp-go" in pg.get_data(as_text=True) and "Auf Homepage veröffentlichen" in pg.get_data(as_text=True), "Seite /homepage (Deutsch)")

    print("2) Adresse und Schlüssel", flush=True)
    ns["HP_TEST_HTTP"] = False
    code, j = api("admin", {"action": "base", "base": base})
    ok(code == 400 and CFG["hp_base"] == "https://kevlaschef.com", "http-Adresse abgewiesen (nur https)")
    ns["HP_TEST_HTTP"] = True
    for b in ("https://kevlaschef.com/x", "https://user:pw@kevlaschef.com", "javascript:alert(1)"):
        ok(api("admin", {"action": "base", "base": b})[0] == 400, f"Adresse abgewiesen: {b}")
    ok(api("admin", {"action": "key", "key": "kurz"})[0] == 400 and not CFG["hp_key"], "zu kurzer Schlüssel abgewiesen")
    code, j = api("admin", {"action": "key", "key": KEY})
    ok(code == 200 and j.get("key_set") is True and CFG["hp_key"] == KEY, "Schlüssel gesetzt")
    code, j = api("admin", {"action": "base", "base": base})
    ok(code == 200 and CFG["hp_base"] == base and not CFG["hp_key"] and j.get("key_set") is False, "neue Adresse löscht den Schlüssel")
    api("admin", {"action": "key", "key": KEY})
    ok(CFG["hp_key"] == KEY, "Schlüssel wieder gesetzt")

    print("3) veröffentlichen (Simulator für den Browser noch nicht veröffentlicht), Startseite ab Werk aus", flush=True)
    owner_start = b"<html>Startseite des Besitzers, von Hand hochgeladen</html>"
    CFG["info_mail"] = "kontakt-test@example.invalid"                # 22.11.2026: die Kontaktadresse von /info/ kommt nie auf den Webspace
    ok(CFG["hp_info_on"] is True and ns["DEFAULTS"]["hp_info_on"] is True, "ab Werk: Besucherseite (Info/) an")
    W.files["index.html"] = owner_start                              # schon auf dem Webspace (nicht von MoveEye)
    code, j = api("admin", {"action": "publish"})
    funk = {n: open(os.path.join(REPO, "funk", n), "rb").read() for n in os.listdir(os.path.join(REPO, "funk"))}
    ok(code == 200 and not j.get("err") and fmt(ns, j)["note"].startswith("Der Simulator für den Browser ist noch nicht"), f"ohne Sim-Paket: {fmt(ns, j)['err']} {fmt(ns, j)}")
    ok(fmt(ns, j)["last"].startswith("Fertig: 9 hochgeladen, 0 unverändert, 0 gelöscht. · "), "Meldung (Startseite aus): " + fmt(ns, j)["last"])
    info = W.files.get("Info/index.html", b"").decode("utf-8")
    ok(info.encode() == ns["hp_info_page"]() and len(info) > 1000000 and "Interesse? Frag unverbindlich an." in info,
       "Info/index.html = die Produktseite von /info/ (%d KB)" % (len(info) // 1024))
    ok("[data-mw-exit]{display:none!important}" in info and "Text kopieren" in info and "/info/ask" not in info
       and "kontakt-test@example.invalid" not in info and "__MAIL__" not in info and "/info/bild/" not in info,
       "Info/: «✕» versteckt, «Text kopieren» statt Senden, keine Kontaktadresse, keine eigenen Kamerabilder")
    ok(all(W.files.get("Funk/" + n) == b for n, b in funk.items()) and len(funk) == 7, "Funk/ = die 7 Dateien von funk/ (Byte für Byte)")
    ok("Sim/test.html" in W.files, "Sim/test.html bleibt dabei")
    ok("index.html" not in [x[2] for x in W.uploads()] and W.files.get("index.html") == owner_start, "Startseite aus: index.html nicht hochgeladen, vorhandene bleibt")
    ok(not any(x[0] == "DELETE" for x in W.log), "Startseite aus: nichts gelöscht")
    ok(len(W.uploads()) == 9, f"9 Dateien hochgeladen ({len(W.uploads())})")
    ok(j.get("start_on") is False, "Status: start_on aus")
    F = fmt(ns, j)
    rows3 = [r["line"] for r in F["rows"]]
    ok(rows3 and rows3[0] == "Startseite: nicht hochgeladen (aus)" and not any(r.startswith(("/:", "index.html:")) for r in rows3)
       and not any(x[0] == "GET" and x[1] in ("/moveeye/", "/moveeye/index.html") for x in W.log), f"Prüfung überspringt die Startseite: {rows3[:3]}")
    pg = c.get("/homepage", headers=H["admin"]).get_data(as_text=True)
    ok('id="hp-start"' in pg and "Öffentlich auf der Homepage" in pg, "Schalter «Startseite» unter «Öffentlich auf der Homepage» auf der Seite")
    cid_off = ns["hp_content_id"]()
    code, j = api("admin", {"action": "start_on", "on": True})
    ok(code == 200 and CFG["hp_start_on"] is True and j.get("start_on") is True and ns["hp_content_id"]() != cid_off, "Schalter an: anderer Inhalt (hp_content_id)")
    n0 = len(W.uploads())
    ok(ns["hp_auto_tick"]() is True, "Schalter an: automatisch ein Lauf")
    warte(HP)
    j = api("admin")[1]
    ok([x[2] for x in W.uploads()[n0:]] == ["index.html"] and b"Funk/" in W.files["index.html"] and "index.html" in ns["hp_state"]()["up"],
       f"Startseite an: index.html hochgeladen ({[x[2] for x in W.uploads()[n0:]]})")
    ok(any(r["line"].startswith("/: 200") for r in fmt(ns, j)["rows"]), "Startseite an: Prüfung mit /")
    ix = W.files["index.html"].decode("utf-8")              # 4.17.0 (Besitzer): MoveEye beim Host und das Spiel direkt
    ok('href="demo/"' in ix and 'href="Sim/?grossvater=1"' in ix and "📷 MoveEye" in ix and "Die Karte des Grossvaters" in ix,
       "Startseite: «📷 MoveEye» → demo/, «🗺️ Die Karte des Grossvaters» → Sim/?grossvater=1")
    tj = re.search(r"var T=(\{.*?\}),l=", ix, re.S)
    nt = len(ns["hp_tiles_tx"]())
    ok(tj and sorted(json.loads(tj.group(1))) == ["en", "fr", "it", "rm"] and all(len(v) == nt for v in json.loads(tj.group(1)).values())
       and ix.count('class="tile t-') == 5 and 'href="Info/"' in ix and "ℹ️ Besucherseite" in ix,
       "Startseite: 5 Kacheln (mit ℹ️ Besucherseite → Info/), je %d Texte in en / fr / it / rm (Deutsch im HTML)" % nt)
    ok('href="Sim/?grossvater=1" data-t="gv.all"' in ix and "kapitel=" not in ix and "roboter=1" not in ix and "🤖" not in ix.split("<script>")[0],
       "Simulator für den Browser noch nicht veröffentlicht: nur «▶ Ganzes Spiel», keine Kapitel, keine Kachel «🤖 Roboter-Labor»")
    code, j = api("admin", {"action": "start_on", "on": False})
    up_before = ns["hp_state"]()["up"].get("index.html")
    n0, nl = len(W.uploads()), len(W.log)
    api("admin", {"action": "publish"})
    ok(len(W.uploads()) == n0 and not any(x[0] == "DELETE" for x in W.log[nl:]) and W.files.get("index.html")
       and ns["hp_state"]()["up"].get("index.html") == up_before, "wieder aus: eigene index.html nicht gelöscht, Eintrag in der eigenen Liste bleibt")
    api("admin", {"action": "start_on", "on": True})                  # ab hier wie bisher mit Startseite
    ok(CFG["hp_start_on"] is True, "Schalter wieder an")

    print("4) Paket sim-web.zip nur mit der signierten Prüfsumme (Teil 300 «anhang.web»)", flush=True)
    sha = hashlib.sha256(open(zp, "rb").read()).hexdigest()
    size = os.path.getsize(zp)
    ns["sig_ok"] = lambda v, f, s, sig: sig == "gut-" + s[:8]
    url = ns["sim_anhang_url"]("web", "3.95.0")
    good = {"ver": "3.95.0", "file": "simulator3d/anhang/sim-web.zip", "size": size, "sha256": sha, "url": url, "sig": "gut-" + sha[:8]}
    for what, e in (("andere Adresse", dict(good, url="https://example.org/sim-web.zip")), ("falsche Signatur", dict(good, sig="x")),
                    ("anderer Dateiname", dict(good, file="simulator3d/anhang/MoveEyeSim3D_Linux.zip"))):
        ok("web" not in (ns["sim_manifest_verify"]({"anhang": {"ver": "3.95.0", "web": e}}).get("anhang") or {}), f"«anhang.web» abgewiesen: {what}")
    ok(ns["sim_manifest_take"]({"anhang": {"ver": "3.95.0", "web": good}}, save=False) == ["web"] and ns["SIM3D_WEB"]["sha256"] == sha, "«anhang.web» übernommen")
    # holen: wie die anderen Sim-Pakete (sim3d_fetch, Prüfsumme) - hier von einem lokalen Server statt von github.com
    srv_dir = os.path.join(tmp, "rel")
    os.makedirs(srv_dir)
    shutil.copy(zp, os.path.join(srv_dir, "sim-web.zip"))
    import functools
    rel = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=srv_dir))
    rel.RequestHandlerClass.log_message = lambda *a: None
    threading.Thread(target=rel.serve_forever, daemon=True).start()
    ns["SIM3D_WEB"]["url"] = "http://127.0.0.1:%d/sim-web.zip" % rel.server_address[1]
    with open(os.path.join(srv_dir, "sim-web.zip"), "r+b") as f:
        f.seek(size - 30)
        f.write(b"X")                                           # verändert: wird nie benutzt
    code, j = api("admin", {"action": "publish"})
    ok("Laden fehlgeschlagen" in fmt(ns, j)["note"] and not os.path.exists(ns["sim3d_path"](ns["SIM3D_WEB"]))
       and not any(p.startswith("Sim/index") for p in W.files), f"verändertes Paket nicht benutzt: {fmt(ns, j)['note']}")
    shutil.copy(zp, os.path.join(srv_dir, "sim-web.zip"))
    n0 = len(W.uploads())
    code, j = api("admin", {"action": "publish"})
    with zipfile.ZipFile(zp) as z:
        ok(all(W.files.get("Sim/" + n) == z.read(n) for n in z.namelist()), "Sim/ = die 8 Dateien aus sim-web.zip")
    ok(len(W.uploads()) - n0 == 10 and not j["last"].get("ren"), f"nur die 10 neuen Dateien (8 + 2 Pack-Teile) hochgeladen ({len(W.uploads()) - n0}), keine Umbenennung")
    ok("index.html" in ns["hp_state"]()["up"] and b"kapitel=1" in W.files["index.html"],
       "index.html mit den Kapiteln schon beim Lauf davor hochgeladen (Sim 3.95.0 übernommen)")
    ix = W.files["index.html"].decode("utf-8")
    want = ns["hp_gv_kapitel"]("3.95.0")
    ok(want == [n for n, _v in ns["HP_GV_KAPITEL"]] and want[:3] == [1, 2, 3] and all('href="Sim/?grossvater=1&amp;kapitel=%d"' % n in ix for n in want)
       and "kapitel=%d" % (len(want) + 1) not in ix, f"Sim 3.95.0: Kapitel-Knöpfe {want} (Parameter «kapitel»)")
    ok(ns["hp_gv_kapitel"]("3.76.0") == [] and ns["hp_gv_kapitel"]("") == [], "Sim 3.76.0 (ohne «kapitel»): keine Kapitel-Knöpfe")
    ok('<a class="tile t-r" href="Sim/?roboter=1">' in ix and ix.count('class="tile t-') == 6 and "🤖 Roboter-Labor" in ix
       and "Segment-Roboter mit Physik ausprobieren (am PC)" in ix and '"btn.rs": "Try out the segment robot with physics (on a PC)"' in ix
       and ix.index('href="Sim/"') < ix.index('href="Sim/?roboter=1"') < ix.index('href="Info/"'),
       "Sim 3.95.0: Kachel «🤖 Roboter-Labor» → Sim/?roboter=1 (6 Kacheln, nach dem Simulator, 5 Sprachen)")
    rs = ns["HP_ROBOTER_SIM"]
    ok(not ns["hp_roboter"]("3.79.0") and ns["hp_roboter"](rs) and not ns["hp_roboter"]("") and "roboter=1" not in ns["hp_index_html"]([], ns["hp_roboter"]("3.79.0")),
       f"Kachel «Roboter-Labor» erst ab Sim {rs} (3.79.0 kennt ?roboter=1 nicht)")
    ok(all(re.fullmatch(r"[^.]+\.[a-z0-9]+", p.rsplit("/", 1)[-1]) for p in W.files), "jede Datei auf dem Webspace hat genau einen Punkt")

    print("5) nur Geändertes", flush=True)
    n0 = len(W.uploads())
    api("admin", {"action": "publish"})
    ok(len(W.uploads()) == n0, f"nichts geändert: nichts hochgeladen ({len(W.uploads()) - n0})")
    W.files["Funk/sw.js"] = b"alt"                                   # auf dem Webspace verändert (andere Grösse)
    del W.files["Sim/index.png"]                                     # auf dem Webspace gelöscht
    api("admin", {"action": "publish"})
    ok(sorted(x[2] for x in W.uploads()[n0:]) == ["Funk/sw.js", "Sim/index.png"], f"nur die zwei: {[x[2] for x in W.uploads()[n0:]]}")
    n0 = len(W.uploads())
    old_test = ns["HP_TEST_HTML"]
    ns["HP_TEST_HTML"] = old_test.replace("Sim-Test", "Sim-Test 2")
    api("admin", {"action": "publish"})
    ok([x[2] for x in W.uploads()[n0:]] == ["Sim/test.html"], "neue Test-Seite: nur sie")
    ns["HP_TEST_HTML"] = old_test
    W.files["sim/index.html"] = b"klein geschrieben, vom Besitzer"   # Gross / Klein: ein anderer Ordner
    W.files["Sim/eigene.txt"] = b"vom Besitzer"
    st = ns["hp_state"]()
    st["up"]["Sim/alt_index.js"] = [3, "0" * 64]
    W.files["Sim/alt_index.js"] = b"alt"
    ns["hp_save"](st)
    n0 = len(W.uploads())
    api("admin", {"action": "publish"})
    ok("Sim/alt_index.js" not in W.files and W.files.get("sim/index.html") and W.files.get("Sim/eigene.txt"), "nur eigene alte Datei gelöscht (sim/ und fremde bleiben)")

    print("5b) vier Schalter: Funkgerät / Simulator / Besucherseite einzeln aus, alle aus", flush=True)
    ok(CFG["hp_funk_on"] is True and CFG["hp_sim_on"] is True and ns["DEFAULTS"]["hp_funk_on"] is True and ns["DEFAULTS"]["hp_sim_on"] is True,
       "ab Werk: Funkgerät und Simulator an")
    api("admin", {"action": "publish"})
    for part, pre, wort in (("funk", "Funk/", "Funkgerät (Funk/)"), ("sim", "Sim/", "Simulator (Sim/ + Test-Seite)"), ("info", "Info/", "Besucherseite (Info/)")):
        mine = {p: b for p, b in W.files.items() if p.startswith(pre)}
        up0 = {p: v for p, v in ns["hp_state"]()["up"].items() if p.startswith(pre)}
        cid_on = ns["hp_content_id"]()
        code, j = api("admin", {"action": part + "_on", "on": False})
        ok(code == 200 and CFG["hp_" + part + "_on"] is False and j.get(part + "_on") is False and ns["hp_content_id"]() != cid_on,
           f"{part} aus: Status und anderer Inhalt (hp_content_id)")
        weg = sorted(p for p in up0 if p in mine)[0]                  # eine eigene Datei (nicht die fremde Sim/eigene.txt)
        W.files.pop(weg)                                              # auf dem Webspace weg: aus = trotzdem nicht hochgeladen
        n0, nl = len(W.uploads()), len(W.log)
        code, j = api("admin", {"action": "publish"})
        ok(not j.get("err") and not any(x[2].startswith(pre) for x in W.uploads()[n0:]), f"{part} aus: nichts von {pre} hochgeladen")
        ok(not any(x[0] == "DELETE" for x in W.log[nl:]) and all(W.files.get(p) == b for p, b in mine.items() if p != weg),
           f"{part} aus: nichts gelöscht")
        ok({p: v for p, v in ns["hp_state"]()["up"].items() if p.startswith(pre)} == up0, f"{part} aus: eigene Liste unverändert")
        rows = [r["line"] for r in fmt(ns, j)["rows"]]
        ok(wort + ": nicht hochgeladen (aus)" in rows and not any(r.startswith(pre) for r in rows)
           and not any(x[0] == "GET" and x[1].startswith("/moveeye/" + pre) for x in W.log[nl:]), f"{part} aus: Prüfung überspringt {pre}: {rows[:4]}")
        api("admin", {"action": part + "_on", "on": True})
        n0 = len(W.uploads())
        ok(ns["hp_auto_tick"]() is True, f"{part} wieder an: automatisch ein Lauf")
        warte(HP)
        ok([x[2] for x in W.uploads()[n0:]] == [weg] and W.files.get(weg) == mine[weg], f"{part} wieder an: {weg} hochgeladen ({[x[2] for x in W.uploads()[n0:]]})")
    for part in ("start", "funk", "sim", "info"):
        api("admin", {"action": part + "_on", "on": False})
    n0, nl = len(W.uploads()), len(W.log)
    code, j = api("admin", {"action": "publish"})
    ok(code == 400 and "Nichts gewählt" in j.get("error", "") and len(W.uploads()) == n0, f"alle aus: nicht veröffentlichen ({code} {j.get('error')})")
    ok(ns["hp_auto_tick"]() is False and not any(x[0] == "DELETE" for x in W.log[nl:]), "alle aus: kein automatischer Lauf, nichts gelöscht")
    import subprocess
    D = {k: ns["tr"](k, "de") for k in ns["HP_TEXTS"]}
    js = ns["HP_FMT_JS"] + "\nconst D = " + json.dumps(D) + ", t = k => D[k] || k;\nconsole.log(JSON.stringify([hpIntro({}, t), " + \
        "hpIntro({funk_on: true, sim_on: true}, t), hpIntro({start_on: true, funk_on: true, sim_on: true}, t)]));"
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    I = json.loads(r.stdout) if r.returncode == 0 else ["", "", ""]
    ok(I[0].startswith("Nichts gewählt") and I[1] == "MoveEye lädt auf deinen Webspace: Handy-Funkgerät (Funk/) und Simulator im Browser mit Test-Seite (Sim/)."
       and I[2].startswith("MoveEye lädt auf deinen Webspace: Startseite, Handy-Funkgerät"), f"Text oben nennt die Auswahl: {I}")
    pg = c.get("/homepage", headers=H["admin"]).get_data(as_text=True)
    ok(all(f'id="{x}"' in pg for x in ("hp-start", "hp-funk", "hp-sim-on", "hp-info-on", "hp-none")), "vier Schalter + Hinweis auf der Seite")
    for part in ("start", "funk", "sim", "info"):
        api("admin", {"action": part + "_on", "on": True})
    api("admin", {"action": "publish"})

    print("6) Retry, Umleitung, falscher Schlüssel, Platz, zu gross", flush=True)
    W.files.pop("Funk/index.html")
    W.fail_once.add("Funk/index.html")
    code, j = api("admin", {"action": "publish"})
    ok(not j.get("err") and W.files.get("Funk/index.html") == funk["index.html"]
       and [x[2] for x in W.uploads()].count("Funk/index.html") >= 2, "500 beim ersten Versuch: nochmals, dann gut")
    W.files.pop("Funk/index.html")
    W.up_redirect = True
    n_other = len(OTHER["log"])
    code, j = api("admin", {"action": "publish"})
    ok("umgeleitet" in fmt(ns, j)["err"] and len(OTHER["log"]) == n_other, f"Umleitung beim Hochladen nie befolgt: {fmt(ns, j)['err']}")
    W.up_redirect = False
    W.key, W.echo = KEY2, True                                        # der Server kennt einen anderen Schlüssel und zeigt den falschen
    n0 = len(W.uploads())
    code, j = api("admin", {"action": "publish"})
    ok("Upload-Schlüssel falsch" in fmt(ns, j)["err"] and "401" in fmt(ns, j)["err"] and len(W.uploads()) == n0, f"falscher Schlüssel: {fmt(ns, j)['err']}")
    ok(KEY not in json.dumps(j) and KEY not in str(HP), "Antwort des Servers mit dem Schlüssel: nicht im Status")
    W.key, W.echo = KEY, False
    oldt = ns["HP_MAX_TOTAL"]
    ns["HP_MAX_TOTAL"] = sum(len(b) for b in W.files.values()) + 10
    n0 = len(W.uploads())
    code, j = api("admin", {"action": "publish"})
    ok("voll" in fmt(ns, j)["err"] and len(W.uploads()) == n0, f"Platz voll (vor dem Hochladen erkannt): {fmt(ns, j)['err']}")
    ns["HP_MAX_TOTAL"] = oldt
    old = ns["HP_MAX_FILE"]
    ns["HP_MAX_FILE"] = 1000
    code, j = api("admin", {"action": "publish"})
    ok("zu gross" in fmt(ns, j)["err"] and "Funk/index.html" in fmt(ns, j)["err"], f"zu grosse Datei: {fmt(ns, j)['err']}")
    ns["HP_MAX_FILE"] = old
    W.max_file = 1000
    code, j = api("admin", {"action": "publish"})
    ok("zu gross" in fmt(ns, j)["err"], f"413 vom Server: {fmt(ns, j)['err']}")
    W.max_file = 100 * 1024 * 1024
    W.quota = sum(len(b) for b in W.files.values()) + 10
    code, j = api("admin", {"action": "publish"})
    ok("voll" in fmt(ns, j)["err"], f"507 vom Server: {fmt(ns, j)['err']}")
    W.quota = 500 * 1024 * 1024
    code, j = api("admin", {"action": "publish"})
    ok(not j.get("err") and W.files.get("Funk/index.html"), "danach wieder gut")
    ren_item = ns["_hp_item"]("Sim/a.b.txt", b"zwei Punkte")
    fixed = ns["hp_fixed_items"]
    ns["hp_fixed_items"] = lambda: fixed() + [ren_item]
    code, j = api("admin", {"action": "publish"})
    ok(any("Sim/a.b.txt → Sim/a_b.txt" in x for x in j["last"].get("ren") or []), f"Umbenennung des Servers gemeldet: {j['last'].get('ren')}")
    ns["hp_fixed_items"] = fixed
    W.files.pop("Sim/a_b.txt", None)

    print("7) Prüfung der öffentlichen Adressen", flush=True)
    code, j = api("admin", {"action": "check"})
    F = fmt(ns, j)
    rows = {r["line"].split(":")[0]: r for r in F["rows"]}
    ok(F["sum"] == "alle Adressen in Ordnung" and "Sim/index.wasm" in rows, f"alles gut: {F['sum']} {[r['probs'] for r in F['rows'] if r['probs']]}")
    ok(re.match(r"Sim/index\.wasm: 200 · 0\.0 MB · application/wasm$", rows["Sim/index.wasm"]["line"]), rows["Sim/index.wasm"]["line"])
    W.hide.add("Sim/index.js")
    W.redirect["Sim/index.pck"] = "http://127.0.0.1:%d/cdn/index.pck" % OTHER["port"]
    W.ctype["Sim/index.wasm"] = "text/plain"
    W.ctype["Sim/index_audio_worklet.js"] = "text/plain"
    W.nosniff = True
    W.csp = "default-src 'self'; connect-src 'none'; script-src 'self'"
    n_other = len(OTHER["log"])
    code, j = api("admin", {"action": "check"})
    F = fmt(ns, j)
    rows = {r["line"].split(":")[0]: r for r in F["rows"]}
    P = lambda p: " | ".join(rows[p]["probs"])                         # noqa: E731
    ok("Antwort 404 statt 200" in P("Sim/index.js"), "404 gefunden: " + P("Sim/index.js"))
    ok("andere Adresse" in P("Sim/index.pck") and rows["Sim/index.pck"]["chain"], "Umleitung auf andere Herkunft gefunden: " + P("Sim/index.pck"))
    ok(all(not x[2] for x in OTHER["log"][n_other:]) and len(OTHER["log"]) > n_other, "die Prüfung schickt nie den Schlüssel (auch nicht an die Umleitung)")
    ok("Typ text/plain – erwartet application/wasm" in P("Sim/index.wasm"), "falscher Typ gefunden: " + P("Sim/index.wasm"))
    ok("nosniff" in P("Sim/index_audio_worklet.js"), "falscher Typ + nosniff gefunden: " + P("Sim/index_audio_worklet.js"))
    ok("connect-src sperrt fetch()" in P("Sim/test.html") and "wasm-unsafe-eval" in P("Sim/test.html") and "unsafe-inline" in P("Sim/test.html"),
       "CSP gefunden (connect-src, wasm-unsafe-eval, unsafe-inline): " + P("Sim/test.html"))
    ok("Content-Security-Policy" in rows["Sim/test.html"]["headers"] and rows["Sim/index.wasm"]["headers"].get("X-Content-Type-Options") == "nosniff",
       "Kopfzeilen CSP / X-Content-Type-Options werden gezeigt")
    ok("connect-src" in P("/") and F["sum"].endswith("Adressen mit Problemen"), "auch die Startseite / und die Zusammenfassung: " + F["sum"])
    W.csp = "default-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'"
    W.hide.clear(); W.redirect.clear(); W.ctype.clear(); W.nosniff = False
    code, j = api("admin", {"action": "check"})
    F = fmt(ns, j)
    ok(F["sum"] == "alle Adressen in Ordnung", "erlaubende CSP: in Ordnung " + str([r["probs"] for r in F["rows"] if r["probs"]]))
    W.csp = ""
    W.files["Funk/manifest.webmanifest"] = W.files["Funk/manifest.webmanifest"][:-1] + b" "
    code, j = api("admin", {"action": "check"})
    ok(any("Inhalt anders" in p for r in fmt(ns, j)["rows"] for p in r["probs"]), "anderer Inhalt bei gleicher Grösse gefunden")
    api("admin", {"action": "publish"})
    code, j = api("admin", {"action": "check", "lang": "fr"}, lang="fr")
    ok(fmt(ns, j, "fr")["sum"] == "toutes les adresses sont en ordre", "Französisch: " + fmt(ns, j, "fr")["sum"])

    print("7b) öffentliche Adresse hp_public, vom Host mit Passwort geschützt (401)", flush=True)
    PUB = {"log": []}

    class PubH(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _do(self):
            PUB["log"].append((self.command, self.path, self.headers.get("Authorization") or ""))
            body = b"Authentication required"
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="MoveEye"')
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        do_GET = do_POST = _do
    ps = http.server.ThreadingHTTPServer(("127.0.0.1", 0), PubH)
    threading.Thread(target=ps.serve_forever, daemon=True).start()
    pub = "http://127.0.0.1:%d/seiten/" % ps.server_address[1]
    ok(CFG["hp_public"] == "" and ns["DEFAULTS"]["hp_public"] == "" and api()[1].get("public") == base + "/moveeye/", "ab Werk: öffentliche Adresse = <hp_base>/moveeye/")
    ns["HP_TEST_HTTP"] = False
    for b in (pub, "http://moveeye.kevlaschef.com/", "https://user:pw@moveeye.kevlaschef.com/", "https://moveeye.kevlaschef.com/?pw=1", "javascript:alert(1)"):
        code, j = api("admin", {"action": "public", "public": b})
        ok(code == 400 and CFG["hp_public"] == "" and "nur https" in j.get("error", "").lower(), f"öffentliche Adresse abgewiesen (nur https): {b} {code}")
    code, j = api("admin", {"action": "public", "public": "https://moveeye.kevlaschef.com"})
    ok(code == 200 and CFG["hp_public"] == "https://moveeye.kevlaschef.com/" and j.get("public") == "https://moveeye.kevlaschef.com/"
       and CFG["hp_key"] == KEY and j.get("key_set") is True, "https-Adresse übernommen, Schlüssel bleibt")
    ns["HP_TEST_HTTP"] = True
    for who in ("Anna", "Cus"):
        api(who, {"action": "public", "public": pub}, wait=False)
        c.post("/api/set", json={"key": "hp_public", "value": pub}, headers=H[who])
        ok(CFG["hp_public"] == "https://moveeye.kevlaschef.com/", f"{who}: öffentliche Adresse nicht änderbar")
    code, j = api("admin", {"action": "public", "public": pub})
    ok(code == 200 and CFG["hp_public"] == pub and CFG["hp_key"] == KEY and j.get("key_set") is True and CFG["hp_base"] == base,
       "öffentliche Adresse geändert: Schlüssel und Webspace-Adresse bleiben")
    ok(j.get("public") == pub and j.get("public_set") == pub, f"«Homepage öffnen» zeigt auf hp_public: {j.get('public')}")
    pg = c.get("/homepage", headers=H["admin"]).get_data(as_text=True)
    ok('id="hp-pub"' in pg and "MoveEye kennt es nicht und speichert es nie" in pg and 'type="password" id="hp-pub' not in pg,
       "Feld «Öffentliche Adresse» + Hinweis zum Passwort, kein Passwort-Feld dafür")
    ns["HP_TEST_HTML"] = old_test.replace("Sim-Test", "Sim-Test P")
    n0, np0 = len(W.uploads()), len(PUB["log"])
    code, j = api("admin", {"action": "publish"})
    ok(not j.get("err") and [x[2] for x in W.uploads()[n0:]] == ["Sim/test.html"] and not any(x[0] == "POST" for x in PUB["log"][np0:]),
       "Hochladen weiter über hp_base (nichts an die öffentliche Adresse)")
    ns["HP_TEST_HTML"] = old_test
    api("admin", {"action": "publish"})
    np0, nw0 = len(PUB["log"]), len(W.log)
    code, j = api("admin", {"action": "check"})
    F = fmt(ns, j)
    lock = [r for r in F["rows"] if not r["line"].endswith("(aus)")]
    ok(lock and all("🔒 geschützt (Passwort) ✓" in r["line"] and not r["probs"] for r in lock), "Prüfung: 401 = geschützt ✓, kein Fehler " + str([r["line"] for r in lock[:3]]))
    ok(F["sum"] == "Alles hinter Passwort – Inhalt nicht prüfbar", "Zusammenfassung: " + F["sum"])
    ok(len(PUB["log"]) - np0 == len(lock) and all(x[1].startswith("/seiten/") and not x[2] for x in PUB["log"][np0:])
       and not any(x[0] == "GET" and x[1].startswith("/moveeye/") for x in W.log[nw0:]), "Prüfung über hp_public, ohne Passwort / Schlüssel")
    ok(ns["hp_state"]()["up"].get("Sim/test.html"), "geschützt: eigene Liste bleibt (nichts als «geändert» vermerkt)")
    code, j = api("admin", {"action": "check", "lang": "fr"}, lang="fr")
    ok(fmt(ns, j, "fr")["sum"].startswith("Tout est derrière un mot de passe"), "Französisch: " + fmt(ns, j, "fr")["sum"])
    code, j = api("admin", {"action": "public", "public": ""})
    ok(code == 200 and CFG["hp_public"] == "" and j.get("public") == base + "/moveeye/" and CFG["hp_key"] == KEY, "leer: wieder <hp_base>/moveeye/, Schlüssel bleibt")
    code, j = api("admin", {"action": "check"})
    ok(fmt(ns, j)["sum"] == "alle Adressen in Ordnung", "alte Adresse: Prüfung wie bisher " + fmt(ns, j)["sum"])

    print("8) automatisch nach einem Update - nur wenn sich der Inhalt geändert hat, nie während eines Alarms", flush=True)
    n0 = len(W.uploads())
    ok(ns["hp_auto_tick"]() is False and len(W.uploads()) == n0, "gleicher Inhalt: kein Lauf")
    with zipfile.ZipFile(zp) as z:
        z0 = {n: z.read(n) for n in z.namelist()}
    zp2 = fake_sim_zip(os.path.join(tmp, "neu"), wasm_extra=b"neu")
    shutil.copy(zp2, os.path.join(srv_dir, "sim-web.zip"))
    sha2 = hashlib.sha256(open(zp2, "rb").read()).hexdigest()
    ns["sim_manifest_take"]({"anhang": {"ver": "3.95.1", "web": dict(good, ver="3.95.1", url=ns["sim_anhang_url"]("web", "3.95.1"), size=os.path.getsize(zp2),
                                                                     sha256=sha2, sig="gut-" + sha2[:8])}}, save=False)
    ns["SIM3D_WEB"]["url"] = "http://127.0.0.1:%d/sim-web.zip" % rel.server_address[1]
    CFG["hp_auto"] = False
    ok(ns["hp_auto_tick"]() is False, "automatisch aus: kein Lauf")
    CFG["hp_auto"] = True
    ns["LED"]["alarm"] = True
    ok(ns["hp_auto_tick"]() is False, "während eines Alarms: kein Start")
    ns["LED"]["alarm"] = False
    ok(ns["hp_auto_tick"]() is True, "neuer Simulator (neue signierte Prüfsumme): automatisch")
    warte(HP)
    with zipfile.ZipFile(zp2) as z:
        changed = sorted("Sim/" + n for n in z.namelist() if z.read(n) != z0.get(n))
    ok(sorted(set(x[2] for x in W.uploads()[n0:])) == changed and W.files["Sim/index.wasm"].endswith(b"neu"),
       f"nur die geänderten Sim-Dateien: {sorted(set(x[2] for x in W.uploads()[n0:]))} = {changed}")
    ok((ns["hp_state"]().get("last") or {}).get("auto") is True, "als «automatisch» vermerkt")
    n0 = len(W.uploads())
    ok(ns["hp_auto_tick"]() is False and len(W.uploads()) == n0, "danach gleich: kein Lauf")
    ns["HP_TEST_HTML"] = old_test.replace("Sim-Test", "Sim-Test A")
    ns["LED"]["alarm"] = True                                         # Alarm: der Lauf wartet, nichts wird hochgeladen
    ns["hp_start"]("publish", True)
    t0 = time.time()
    while not HP["wait"] and time.time() - t0 < 20:
        time.sleep(0.02)
    time.sleep(0.3)
    ok(HP["wait"] is True and HP["busy"] and len(W.uploads()) == n0, "Alarm: der Lauf wartet, nichts hochgeladen")
    code, j = api("admin")
    ok(j.get("wait") is True and ns["tr"]("waiting – alarm", "de") == "wartet – Alarm" and re.search(r"^1/1 · 0\.0 MB · Sim/test\.html$", fmt(ns, j)["prog"]),
       f"Fortschritt «1/1 · MB» und «wartet – Alarm»: {fmt(ns, j)['prog']} {j.get('wait')}")
    ns["LED"]["alarm"] = False
    warte(HP)
    ok([x[2] for x in W.uploads()[n0:]] == ["Sim/test.html"] and b"Sim-Test A" in W.files["Sim/test.html"], "nach dem Alarm hochgeladen")
    W.key = KEY2
    ns["HP_TEST_HTML"] = old_test.replace("Sim-Test", "Sim-Test 3")
    ok(ns["hp_auto_tick"]() is True, "neue MoveEye (andere Test-Seite): automatisch")
    warte(HP)
    ok(HP["err"] == "key" and ns["hp_auto_tick"]() is False, "falscher Schlüssel: nicht gleich nochmals (erst nach 6 h oder neuem Schlüssel)")
    W.key = KEY
    api("admin", {"action": "key", "key": KEY})
    ok(ns["hp_auto_tick"]() is True, "neuer Schlüssel: wieder")
    warte(HP)
    ns["HP_TEST_HTML"] = old_test

    print("9) der Schlüssel steht nirgends sonst", flush=True)
    ns["save_settings_now"]()
    home = os.environ["MOTIONWATCH_HOME"]
    wo = []
    for d, _, fs in os.walk(home):
        for f in fs:
            p = os.path.join(d, f)
            try:
                if KEY.encode() in open(p, "rb").read():
                    wo.append(os.path.relpath(p, home))
            except OSError:
                pass
    ok(wo and all("settings" in os.path.basename(x) for x in wo), f"nur in der Einstellungs-Datei: {wo}")
    for who in ("admin", "Anna", "Cus"):
        for u in ("/api/state", "/api/homepage", "/api/schema", "/api/state?lang=fr"):
            r = c.get(u, headers=H[who])
            ok(KEY not in r.get_data(as_text=True), f"{who} {u}: kein Schlüssel")
    ok(KEY not in json.dumps(list(ns["STATE"].get("events") or []), default=str), "nicht im Verlauf")
    for who in ("Anna", "Cus"):
        r = c.get("/api/settings/export", headers=H[who])
        ok(r.status_code == 403 and KEY not in r.get_data(as_text=True), f"{who}: Export verboten ({r.status_code})")
    ok(ns["_SECRET_RE"].search("hp_key"), "Diagnose-Bericht (Teil 300) blendet hp_key aus")
    code, j = api("admin", {"action": "key_del"})
    ok(j.get("key_set") is False and not CFG["hp_key"], "Schlüssel gelöscht")
    ok(api("admin", {"action": "publish"})[0] == 400, "ohne Schlüssel: nicht veröffentlichen")

    print("10) Texte in 5 Sprachen, Selbsttest des Teils", flush=True)
    for L, w in (("de", "Kein Upload-Schlüssel gesetzt."), ("fr", "Aucune clé d’envoi définie."), ("it", "Nessuna chiave di caricamento impostata."),
                 ("rm", "Nagina clav da chargiar definida.")):
        ok(ns["tr"]("No upload key set.", L) == w, f"Text {L}")
    for k, v in ns["HP_TEXTS"].items():
        ok(len(v) == 4 and all(v), f"Text vollständig: {k}")
    ok(ns["homepage_selftest"]() is True, "homepage_selftest")


if __name__ == "__main__":
    sys.exit(main())
