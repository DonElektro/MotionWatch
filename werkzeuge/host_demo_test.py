#!/usr/bin/env python3
"""Test «Demo beim Host» (Teil 639zzzzw, --host-modus): Sperren, Pfad-Vorsilbe «/demo», WebSocket des Web-Simulators.

  python3 werkzeuge/host_demo_test.py                     # ohne MoveEye-Lauf: Quelltext, Skript (node --check), Umschreiben,
                                                          #   WSGI-Schicht, Sperren in einem eigenen Prozess
  python3 werkzeuge/host_demo_test.py --lauf [--datei MW] [--browser] [--ram 600] [--python BIN]
        startet MoveEye im Host-Modus hinter einem kleinen Proxy, der «/demo» abschneidet (wie der Host): Seiten über /demo/,
        nichts geht an der Vorsilbe vorbei (der Proxy zählt jede Anfrage ohne /demo), Sperren (403, hört nur auf 127.0.0.1),
        ein nachgemachter Web-Simulator über ws://…/demo/simtun (das Kamerabild kommt durch die WebSocket-Leitung);
        --browser: die Hauptseiten bei 390 px (Bildschirmfotos nach $TMPDIR/host_demo_bilder, keine JS-Fehler);
        --ram SEK: Speicher (RSS) und CPU des Prozesses so lange messen, mit Besuchern (Seiten, Live-Bild).
Ohne Netz nach aussen; alles in einem Wegwerf-Ordner, der danach gelöscht wird.
"""
import argparse, glob, hashlib, json, os, re, shutil, socket, subprocess, sys, tempfile, threading, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PART = os.path.join(ROOT, "quelle", "639zzzzw_host_demo.py")
FAIL, WARN = [], []


def ok(cond, what):
    print(("  ok  " if cond else "  FEHLER  ") + what, flush=True)
    if not cond:
        FAIL.append(what)
    return cond


def part_ns():
    """the part alone, with the few names it needs from the rest of MoveEye as stand-ins"""
    import collections, ipaddress, math, secrets, shutil as sh, subprocess as sp, tempfile as tf
    ns = {"__name__": "host_part", "__file__": PART, "re": re, "json": json, "os": os, "sys": sys, "time": time, "threading": threading,
          "hashlib": hashlib, "ipaddress": ipaddress, "subprocess": sp, "shutil": sh, "tempfile": tf, "deque": collections.deque,
          "math": math, "secrets": secrets, "CFG": {"source": "demo", "sim_on": False, "notify_on": True, "sim_url": "http://x:1",
                                                    "hp_key": "k", "record_dir": "/x", "update_mode": "dev"},
          "DATA_DIR": "/nonexistent-data", "DEMO_BLOCK": ("/api/power",), "WebStream": type("WebStream", (), {"_serve": lambda *a: None}),
          "DemoSource": type("DemoSource", (), {"__init__": lambda self: setattr(self, "fps", 15.0),
                                                "set_fps": lambda self, f: setattr(self, "fps", float(f) if f else 15.0)}),
          "log_event": lambda k, t: None, "save_settings": lambda: None, "DEMO": {"on": False},
          "open_source": lambda spec, thermal=False: ("base", spec, spec, ""), "source_label": lambda s: str(s),
          "DE": {}, "TRX": {"fr": {}, "it": {}, "rm": {}}, "simwait_texts": lambda r, lang=None: {"hint": "PC", "hint2": "bat"},
          "sim_cam_fps": lambda c: 4, "tr": lambda k, L=None: k, "norm_lang": lambda L: L or "de", "cur_lang": lambda: "de",
          "bio_free_need": lambda: 2 << 30, "games_install": lambda: None,
          # 4.16.0: AI model, continuous recording, watchdog, simulator link, health list, tools page
          "ai_model_download": lambda: (False, "base"), "LoopRecorder": type("LoopRecorder", (), {"_clean": lambda self: None}),
          "_servo_inhibit": lambda code, on, now: None, "SimLink": type("SimLink", (), {"tick": lambda self: None}),
          "simwait_reason": lambda now=None: None, "health_check": lambda lang=None: {"items": [], "count": {}},
          "security_check": lambda: True, "ai_model_dirs": lambda: ["/prog"]}
    src = open(PART, encoding="utf-8").read()
    exec(compile(src, PART, "exec"), ns)
    return ns


class FakeRule:
    def __init__(self, r):
        self.rule = r


class FakeApp:
    def __init__(self, rules):
        self.url_map = type("M", (), {"iter_rules": lambda s: [FakeRule(r) for r in rules]})()


def static():
    print("1. Quelltext")
    src = open(PART, encoding="utf-8").read()
    st = open(os.path.join(ROOT, "quelle", "640_start.py"), encoding="utf-8").read()
    ok('"--host-modus"' in st and "host_mode_start(a)" in st and "host_after_settings()" in st, "640: --host-modus, Sperren vor jedem Faden")
    ok("a.demo = a.headless = True" not in st and 'a.headless = True; a.helper = False; a.bind = "127.0.0.1"' in st
       and "nosys = a.demo or a.host_modus" in st, "640: Host-Modus = echte MoveEye (4.15.0, keine Demo), ohne Fenster, nur 127.0.0.1")
    i_lock, i_thr = st.find("host_mode_start(a)"), st.find("threading.Thread(target=clock_guard_loop")
    ok(0 < i_lock < i_thr, "Sperren vor dem ersten Faden")
    d210 = open(os.path.join(ROOT, "quelle", "210_demo.py"), encoding="utf-8").read()
    ok('DEMO["on"] and not (HOST["on"] and host_sim_source(spec))' in d210, "210: Simulator-Bild nur im Host-Modus mit verbundenem Web-Simulator")
    for k in ("/api/homepage", "/api/tunnel", "/api/helper", "/api/webpush", "/api/update", "/api/dev", "/api/relay", "/api/fehler/fix"):
        ok(k in src.split("HOST_BLOCK = ", 1)[1].split(")", 1)[0], f"HOST_BLOCK: {k}")
    d = open(os.path.join(ROOT, "quelle", "210_demo.py"), encoding="utf-8").read().split("DEMO_BLOCK = ", 1)[1].split(")", 1)[0]
    for k in ("/api/power", "/api/wifi", "/api/hotspot", "/api/password", "/api/autostart"):
        ok(k in d, f"DEMO_BLOCK (210): {k}")
    for k in ("RPi", "gpiozero", "smbus", "spidev", "picamera2", "dbus", "bluetooth", "serial"):
        ok(f'"{k}"' in src.split("HOST_NO_MODULES = ", 1)[1].split(")", 1)[0], f"keine Hardware: {k}")
    ok('HOST_PROGS = ("ffmpeg", "ffprobe")' in src, "Programme: nur ffmpeg / ffprobe")
    ok("# wraps: WebStream._serve" in src, "Wrapper markiert (bauen.py)")
    ok("host needs the data zip" in st or "host mode needs the data zip" in st, "640: ohne Zusatzdatei kein Host-Modus (sicher zu)")
    ok(src.count("HOST_PY = r\'\'\'") == 1 and "exec(compile(HOST_PY" in src, "Programmtext als ein Literal (Hauptdatei klein)")
    hn = src.split("def _host_note(", 1)[1].split("\ndef ", 1)[0]
    ok("log_event(" not in hn.replace("Never log_event", ""), "Sperren schreiben nicht selbst ins Protokoll (LOCK, sonst Verklemmung wie in /api/state)")
    # 4.16.1 (coordinator): OpenCV 5.x cannot read the SSD model - every pip install of OpenCV stays below 5
    req = open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8").read()
    ok("opencv-python-headless>=4.8,<5" in req, "requirements.txt: opencv-python-headless>=4.8,<5 (der Host installiert sie)")
    loose = []
    for f in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))) + [os.path.join(ROOT, "werkzeuge", "ci_pakete.txt"),
                                                                                    os.path.join(ROOT, "werkzeuge", "test_runner", "runner_einrichten.sh")]:
        for i, l in enumerate(open(f, encoding="utf-8"), 1):
            if l.lstrip().startswith("#"):
                continue
            for m in re.finditer(r"opencv-python(?:-headless)?([^\s\"']*)", l):
                if not (m.group(1).startswith("==4") or "<5" in m.group(1)):
                    loose.append(f"{os.path.basename(f)}:{i}")
    ok(not loose, f"OpenCV überall unter 5 gepinnt (CI, Prüfsatz, HP-venv, Runner) {loose[:6]}")
    print("2. Skript in den Seiten")
    ns = part_ns()
    js = ns["HOST_SHIM_JS"].replace("%OUTSIDE%", json.dumps(list(ns["HOST_OUTSIDE"]))).replace("%PREFIX%", json.dumps("/demo"))
    node = shutil.which("node")
    if node:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        os.remove(f.name)
        ok(r.returncode == 0, "node --check HOST_SHIM_JS" + (": " + r.stderr[:300] if r.returncode else ""))
        test_js = js + r"""
;(function(){var P="/demo",f=window.__mwFix,c=[];function t(a,b){if(f(a)!==b)c.push(a+" -> "+f(a)+" (soll "+b+")");}
t("/api/state","/demo/api/state");t("/demo/api/state","/demo/api/state");t("/demo","/demo");t("/","/demo/");t("api/x","api/x");
t("//cdn.example/x","//cdn.example/x");t("https://other.example/api","https://other.example/api");
t("http://h.example:8090/api/x","http://h.example:8090/demo/api/x");t("ws://h.example:8090/simtun","ws://h.example:8090/demo/simtun");
t("wss://h.example:8090/demo/simtun","wss://h.example:8090/demo/simtun");t("/demox","/demo/demox");t("#top","#top");t("?a=1","?a=1");
t("/Sim/","/Sim/");t("/Sim","/Sim");t("/Sim/index.html?x=1","/Sim/index.html?x=1");t("http://h.example:8090/Sim/","http://h.example:8090/Sim/");
t("/Simx","/demo/Simx");t("/sim","/demo/sim");
console.log(c.length?"FEHLER "+c.join("; "):"FIX OK");})();"""
        stub = r"""var window=globalThis;var location={host:"h.example:8090",origin:"http://h.example:8090",pathname:"/demo/"};
function Noop(){};var XMLHttpRequest=function(){};XMLHttpRequest.prototype.open=function(){};var history={pushState:function(){},replaceState:function(){}};
var navigator={};var Element=function(){};Element.prototype.setAttribute=function(){};Element.prototype.insertAdjacentHTML=function(){};
var document={documentElement:{},addEventListener:function(){}};var MutationObserver=function(){this.observe=function(){}};
window.fetch=function(){};window.open=function(){};window.WebSocket=function(){};window.EventSource=function(){};var URL=globalThis.URL;
"""
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(stub + test_js)
        r = subprocess.run([node, f.name], capture_output=True, text=True)
        os.remove(f.name)
        ok("FIX OK" in r.stdout, "Adressen im Browser (fix): " + (r.stdout + r.stderr).strip()[:400])
    else:
        print("  (node fehlt - Skript nicht geprüft)")
    d_ = ns["DemoSource"](); ns["HOST"]["on"] = True; d2 = ns["DemoSource"](); d2.set_fps(None); ns["HOST"]["on"] = False; d3 = ns["DemoSource"]()
    ok(d2.fps == ns["HOST_FPS"] and d3.fps == 15.0, f"Demo-Szene im Host-Modus {d2.fps} statt 15 Bilder/s, sonst unverändert ({d3.fps})")
    fx = ns["_host_fixed"]()
    ns["CFG"].update(web_quality=75, web_width=1280, proc_width=480, ai_every=3, sim_fps=6, sim_eco=True, loop_on=False, timelapse_on=False)
    fx = ns["_host_fixed"]()
    ok(fx.get("web_quality") == 60 and fx.get("web_width") == 640 and fx.get("proc_width") == 320, "Live-Bild kleiner im Host-Modus (CPU)")
    print("2b. 4.16.0: Sperren nach ganzen Adressteilen, Passwort, Simulator-Tab, Watchdog, KI, 300 MB")
    hp = ns["host_path_in"]
    ok(hp("/api/time", ("/api/time",)) and hp("/api/ki/ask", ("/api/ki/",)) and hp("/api/talk/stop", ("/api/talk",))
       and not hp("/api/timelapse", ("/api/time",)) and not hp("/api/stick", ("/api/stick2",)) and not hp("/api/pushpause", ("/api/push",)),
       "Sperren nach ganzen Adressteilen (/api/time sperrt nicht /api/timelapse)")
    ok("/api/stick" not in ns["HOST_BLOCK"], "Joystick des Kopfs (/api/stick) nicht mehr gesperrt")
    ok("/api/ai_model" not in ns["HOST_AI"] and "/api/ai_model" in ns["HOST_AI_OK"] and "/api/ki/" in ns["HOST_AI"] and "/api/piper" in ns["HOST_AI"]
       and "/api/tausch/bio" in ns["HOST_AI"] and "/api/own_model" in ns["HOST_AI"], "KI-Erkennung frei, Blinki / BioCLIP / eigenes Modell / Stimmen gesperrt")
    ns["CFG"].update(ai_enabled=True, loop_on=True, timelapse_on=True, timelapse_max_gb=2.0)
    fx = ns["_host_fixed"]()
    ok("ai_enabled" not in fx and "loop_on" not in fx and "timelapse_on" not in fx and abs(fx["timelapse_max_gb"] * 1024 - 300) < 1e-6,
       f"KI, Daueraufnahme, Zeitraffer frei; Zeitraffer höchstens 300 MB ({fx.get('timelapse_max_gb')})")
    ok(ns["HOST_DL_HOSTS"]["ai_ips"] == ("storage.googleapis.com", "raw.githubusercontent.com") and ns["HOST_AI_THREAD"] == "ai-model"
       and ns["HOST_AI_TGZ"].startswith("https://storage.googleapis.com/") and len(ns["HOST_AI_PBTXT_SHA256"]) == 64
       and len(ns["HOST_AI_PB_SHA1"]) == 40 and len(ns["HOST_AI_TGZ_SHA1"]) == 40, "KI-Modell: eine feste Quelle mit festen Prüfsummen")
    ns["HOST"]["on"] = True
    ns.update(web_pw_active=lambda: False, HEALTH_ORDER=("bad", "warn", "ok", "off"))
    ns["_health_check_host_base"] = lambda lang=None: {"items": [{"id": "pw", "level": "bad", "text": "no password", "tip": "x"},
                                                                {"id": "cpu", "level": "ok", "text": "", "tip": ""}],
                                                      "count": {"bad": 1, "warn": 0, "ok": 1, "off": 0}}
    h = ns["health_check"]("de")
    pw = [x for x in h["items"] if x["id"] == "pw"][0]
    ok(pw["level"] == "ok" and "Basic Auth" in pw["text"] and h["count"]["bad"] == 0 and h["count"]["ok"] == 2,
       f"Host: «Passwort kommt vom Host (Basic Auth)» statt «kein Passwort» ({pw}, {h['count']})")
    ns["HOST"]["on"] = False
    h = ns["health_check"]("de")
    ok([x for x in h["items"] if x["id"] == "pw"][0]["level"] == "bad", "normales Gerät: «kein Passwort» bleibt")
    ns["HOST"]["on"] = True
    tx = ns["simwait_texts"]({"why": "connect", "s": 3}, "de")
    ok(tx.get("url") == "/Sim/", f"Link «Simulator öffnen» absolut /Sim/ ({tx.get('url')!r})")
    ns["_mmss"] = lambda s: f"0:{int(s):02d}"
    tx = ns["simwait_texts"]({"why": "hidden", "s": 25}, "de")
    ok(tx["title"] == ns["HOST_HIDDEN"] and tx["hint"] == ns["HOST_HIDDEN_TIP"] and tx["url"] == "/Sim/" and "0:25" in tx["sub"],
       f"Simulator-Tab im Hintergrund: eigener Text, kein «Verbinde …» ({tx['title']!r})")
    rw_ = ns["host_rewrite"]('<a href="/Sim/">x</a> fetch("/api/state")', "/demo", FakeApp(["/api/state", "/Sim/<p>"]))
    ok('href="/Sim/"' in rw_ and '"/demo/api/state"' in rw_, f"Server: /Sim/ bleibt ohne Vorsilbe ({rw_!r})")
    ns["_HOST_RW"]["segs"] = None                         # (the segments of the next fake server)
    # the line of the web simulator: «VIS hidden» keeps it, the last picture stays, the watchdog waits
    import numpy as np
    class FakeSock:
        def __init__(self): self.out = []
        def sendall(self, b): self.out.append(b)
        def shutdown(self, n): pass
    ns.update(log_event=lambda k, t: None, WATCH_REF={"w": type("W", (), {"cap": object()})()}, STATE={}, SIM={}, SIMWAIT={"why": None},
              cv2=type("cv2", (), {"imdecode": staticmethod(lambda b, f: np.zeros((4, 4, 3), np.uint8)), "IMREAD_COLOR": 1}), np=np)
    m = ns["_HostWsMux"](FakeSock(), "peer", "x"); ns["HOST"]["mux"] = m
    ok(not ns["host_sim_hidden"](), "sichtbar: kein Hintergrund")
    sn = ns["HostSimSnap"](0); sn.gap = 0.0
    sn._get = lambda: b"jpg"
    ok(sn.read()[0], "Bild vom sichtbaren Simulator")
    m.set_hidden(True)
    ok(ns["host_sim_hidden"]() and m.hidden_t > 0, "«VIS hidden»: Tab im Hintergrund")
    sn._get = lambda: (_ for _ in ()).throw(OSError("no answer"))
    r1, f1 = sn.read()
    ok(r1 and f1 is not None and f1.shape == (4, 4, 3), "im Hintergrund: das letzte Bild, keine Anfrage, kein Neuverbinden")
    ns["CFG"].update(sim_on=True, source="sim:0")
    ok(ns["simwait_reason"]()["why"] == "hidden", "Ruhebild-Grund «hidden»")
    seen = {}
    ns["_servo_inhibit_host_base"] = lambda code, on, now: seen.update(on=on)
    ns["_servo_inhibit"]("wd_cam", True, 0.0)
    ok(seen.get("on") is False, "Watchdog-Banner nicht, solange der Simulator-Tab im Hintergrund ist")
    m.set_hidden(False)
    ns["_servo_inhibit"]("wd_cam", True, 0.0)
    ok(seen.get("on") is True, "echtes Hängen (Simulator sichtbar, kein Bild unterwegs): Watchdog bleibt")
    ns["HOST"]["snap_busy"] = time.time()
    ns["_servo_inhibit"]("wd_cam", True, 0.0)
    ok(seen.get("on") is False, "ein Bild ist zum Web-Simulator unterwegs: kein Watchdog-Banner")
    ns["HOST"]["snap_busy"] = 0.0
    ns["_servo_inhibit"]("uv", True, 0.0)
    ok(seen.get("on") is True, "andere Gründe (Unterspannung) unverändert")
    ns["HOST"]["mux"] = None; ns["HOST"]["on"] = False; ns["CFG"].update(sim_on=False, source="demo")
    # 300 MB: continuous recording + time-lapse together, oldest first
    md = tempfile.mkdtemp(prefix="hostmedia_")
    try:
        rec = os.path.join(md, "rec"); os.makedirs(os.path.join(rec, "loop", "2026-11-18")); os.makedirs(os.path.join(rec, "timelapse"))
        ns.update(rec_dir=lambda: rec, loop_dir=lambda: os.path.join(rec, "loop"), tl_dir=lambda: os.path.join(rec, "timelapse"),
                  glob=__import__("glob"), LIVE_RECS=set(), _read_sidecar=lambda n: {"fav": n.endswith("_000300.jpg")},
                  TL_PHOTO_RE=re.compile(r"^tl_(\d{8})_(\d{6})\.jpg$"), TL_VIDEO_RE=re.compile(r"^tlv_[0-9A-Za-z_\-]{1,40}\.mp4$"),
                  LOOPREC=type("L", (), {"cur": "loop/2026-11-18/10-50.mp4"})())
        made = []
        for i, (rel, sz) in enumerate([("loop/2026-11-18/10-00.mp4", 6), ("timelapse/tl_20261118_000100.jpg", 2), ("loop/2026-11-18/10-10.mp4", 6),
                                       ("timelapse/tl_20261118_000300.jpg", 2), ("timelapse/tlv_2026-11-18.mp4", 4), ("loop/2026-11-18/10-50.mp4", 6),
                                       ("timelapse/notes.txt", 9)]):
            fp = os.path.join(rec, rel)
            with open(fp, "wb") as f:
                f.write(b"x" * sz * 1024 * 1024)
            os.utime(fp, (1000 + i, 1000 + i)); made.append(fp)
        left = ns["host_media_trim"](12 * 1024 * 1024)
        have = sorted(os.path.relpath(x, rec) for x in made if os.path.exists(x))
        ok(have == ["loop/2026-11-18/10-50.mp4", "timelapse/notes.txt", "timelapse/tl_20261118_000300.jpg", "timelapse/tlv_2026-11-18.mp4"]
           and left == 12 * 1024 * 1024, f"300 MB gemeinsam: das Älteste zuerst, laufendes Stück und Stern bleiben ({have}, {left >> 20} MB)")
        ok(ns["HOST_MEDIA_BYTES"] == 300 * 1024 * 1024, "Grenze 300 MB")
    finally:
        shutil.rmtree(md, ignore_errors=True)
    print("3. Umschreiben auf dem Server")
    app = FakeApp(["/", "/api/state", "/api/x/<y>", "/sim", "/protect", "/i18n/<l>.js", "/sw.js", "/g/<tok>", "/simtun", "/static/<path:f>"])
    rw = lambda t, html=False: ns["host_rewrite"](t, "/demo", app, html)
    cases = [('<a href="/protect">', '<a href="/demo/protect">'), ('fetch("/api/state")', 'fetch("/demo/api/state")'),
             ("x='/api/x/'+id", "x='/demo/api/x/'+id"), ('<a href="/">Live</a>', '<a href="/demo/">Live</a>'),
             ('location.href = "/"', 'location.href = "/demo/"'), ('background:url(/api/state)', 'background:url(/demo/api/state)'),
             ('"/demo/api/state"', '"/demo/api/state"'), ('"/apix"', '"/apix"'), ("s.split('/')", "s.split('/')"),
             ("/sim/.test(p)", "/sim/.test(p)"), ('"start_url": "/"', '"start_url": "/demo/"'), ('<script src="/i18n/fr.js">', '<script src="/demo/i18n/fr.js">'),
             ('"//cdn/x"', '"//cdn/x"'), ("'<img src=\\\"/api/state\\\">'", "'<img src=\\\"/demo/api/state\\\">'"), ("`/sim?x=1`", "`/demo/sim?x=1`")]
    for a, b in cases:
        ok(rw(a) == b, f"{a!r} -> {rw(a)!r}")
    page = rw("<!doctype html><html><head><title>x</title></head><body></body></html>", True)
    ok(page.index("__mwBase") < page.index("<title>") and page.count("<script>") == 1, "Skript gleich nach <head> (vor allem anderen)")
    print("4. WSGI-Schicht")
    seen = {}

    def inner(env, sr):
        seen["path"] = env["PATH_INFO"]; seen["ae"] = env.get("HTTP_ACCEPT_ENCODING")
        if env["PATH_INFO"] == "/go":
            sr("302 FOUND", [("Location", "/protect"), ("Set-Cookie", "a=1; Path=/; HttpOnly")]); return [b""]
        if env["PATH_INFO"] == "/abs":
            sr("302 FOUND", [("Location", "http://h.example:8090/sim")]); return [b""]
        if env["PATH_INFO"] == "/img":
            sr("200 OK", [("Content-Type", "image/jpeg")]); return [b'"/api/state"']
        sr("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", "5")]); return [b'<html><head></head><a href="/sim">x</a></html>']
    ns["HOST"]["prefix"] = "/demo"
    mw = ns["_HostPrefix"](inner, app)

    def call(path, extra=None):
        out = {}
        env = dict({"PATH_INFO": path, "REQUEST_METHOD": "GET", "HTTP_HOST": "h.example:8090", "HTTP_ACCEPT_ENCODING": "br"}, **(extra or {}))
        body = b"".join(mw(env, lambda s, h, e=None: out.update(s=s, h=dict(h))))
        return out, body
    o, b = call("/go")
    ok(o["h"]["Location"] == "/demo/protect", "Umleitung: Location /protect -> /demo/protect")
    ok("Path=/demo/" in o["h"]["Set-Cookie"], "Cookie-Pfad /demo/")
    o, b = call("/abs")
    ok(o["h"]["Location"] == "http://h.example:8090/demo/sim", "Umleitung mit ganzer Adresse (gleicher Rechner) mit Vorsilbe")
    o, b = call("/x")
    ok(b'href="/demo/sim"' in b and b"__mwBase" in b and o["h"]["Content-Length"] == str(len(b)), "HTML umgeschrieben, Länge stimmt")
    ok(seen["ae"] is None, "Kompression für umzuschreibende Seiten aus (nachher selbst gzip)")
    o, b = call("/demo/x")
    ok(seen["path"] == "/x", "kommt «/demo» trotzdem an, wird es abgeschnitten")
    o, b = call("/img")
    ok(b == b'"/api/state"', "Bilder / Ströme bleiben unverändert")
    o, b = call("/x", {"HTTP_ACCEPT_ENCODING": "gzip"})
    import gzip
    ok(o["h"].get("Content-Encoding") != "gzip" or b'href="/demo/sim"' in gzip.decompress(b), "gzip nach dem Umschreiben")
    o, b = call("/x", {"HTTP_X_FORWARDED_PREFIX": "/andere"})
    ok(b'href="/andere/sim"' in b, "X-Forwarded-Prefix gilt vor --url-prefix")
    ns["HOST"]["prefix"] = ""
    o, b = call("/x")
    ok(b == b'<html><head></head><a href="/sim">x</a></html>', "ohne Vorsilbe: Seite Byte für Byte wie bisher")
    print("5. Sperren (eigener Prozess)")
    code = r"""
import os, sys, json, socket, subprocess, tempfile, shutil
sys.path.insert(0, %r)
import host_demo_test as t
ns = t.part_ns()
data = tempfile.mkdtemp(prefix="hostlock_")
ns["DATA_DIR"] = data
class A: url_prefix = None
ns["host_mode_start"](A())
r = {}
def tr(name, f):
    try:
        f(); r[name] = "ok"
    except Exception as e:
        r[name] = type(e).__name__
s = socket.socket(); s.settimeout(1)
tr("connect_out", lambda: s.connect(("1.1.1.1", 80)))
s2 = socket.socket()
tr("bind_all", lambda: s2.bind(("0.0.0.0", 0)))
s3 = socket.socket(); tr("bind_lo", lambda: s3.bind(("127.0.0.1", 0)))
u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tr("udp_bcast", lambda: u.sendto(b"x", ("255.255.255.255", 8764)))
tr("udp_lo", lambda: u.sendto(b"x", ("127.0.0.1", 9)))
tr("nmcli", lambda: subprocess.run(["nmcli", "radio"]))
tr("sudo", lambda: subprocess.run(["sudo", "reboot"]))
tr("nice_ffmpeg", lambda: subprocess.run(["nice", "-n", "5", "ffmpeg", "-hide_banner", "-version"], capture_output=True))
tr("nice_sh", lambda: subprocess.run(["nice", "-n", "5", "sh", "-c", "true"]))
tr("nice_bare", lambda: subprocess.run(["nice"]))
tr("shell", lambda: subprocess.run("echo hi", shell=True))
tr("check_output", lambda: subprocess.check_output(["/usr/bin/systemctl", "reboot"]))
r["system"] = os.system("echo hi")
tr("import_gpio", lambda: __import__("RPi.GPIO"))
tr("import_smbus", lambda: __import__("smbus2"))
tr("write_out", lambda: open("/tmp/../etc/host_demo_test_x", "w"))
tr("write_home", lambda: open(os.path.expanduser("~/.config/autostart/x.desktop"), "w"))
tr("write_data", lambda: open(os.path.join(data, "a.txt"), "w").close())
tr("remove_out", lambda: os.remove("/etc/hostname"))
tr("rmtree_out", lambda: shutil.rmtree("/usr/share/doc"))
tr("execv_other", lambda: os.execv("/bin/sh", ["/bin/sh", "-c", "true"]))
tr("read_out", lambda: open("/etc/hostname").read())
ns["HOST"].setdefault("gh_ips", set()).add("203.0.113.5")       # 4.15.1: as if getaddrinfo had resolved a GitHub name
import threading
def in_thread(name, f):
    out = {}
    def run():
        try:
            f(); out["r"] = "ok"
        except Exception as e:
            out["r"] = type(e).__name__
    th = threading.Thread(target=run, name=name); th.start(); th.join(10)
    return out.get("r")
def gh(ip, port):
    s = socket.socket(); s.settimeout(0.5)
    try:
        s.connect((ip, port))
    finally:
        s.close()
r["gh_dl"] = in_thread("fspiele-dl", lambda: gh("203.0.113.5", 443))
r["gh_other_thread"] = in_thread("x-thread", lambda: gh("203.0.113.5", 443))
r["gh_dl_port80"] = in_thread("fspiele-dl", lambda: gh("203.0.113.5", 80))
r["dl_other_ip"] = in_thread("fspiele-dl", lambda: gh("198.51.100.7", 443))
ns["HOST"].setdefault("ai_ips", set()).add("203.0.113.9")       # 4.16.0: as if the thread «ai-model» had resolved the model source
r["ai_dl"] = in_thread("ai-model", lambda: gh("203.0.113.9", 443))
r["ai_to_github_ip"] = in_thread("ai-model", lambda: gh("203.0.113.5", 443))
r["games_to_ai_ip"] = in_thread("fspiele-dl", lambda: gh("203.0.113.9", 443))
r["ai_ip_other_thread"] = in_thread("hostmode", lambda: gh("203.0.113.9", 443))
print(json.dumps(r))
shutil.rmtree(data)
""" % os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    try:
        res = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {}
        print(r.stdout[-800:], r.stderr[-1500:])
    want = {"connect_out": "PermissionError", "bind_all": "PermissionError", "bind_lo": "ok", "udp_bcast": "PermissionError", "udp_lo": "ok",
            "nmcli": "FileNotFoundError", "sudo": "FileNotFoundError", "shell": "FileNotFoundError", "check_output": "FileNotFoundError",
            "import_gpio": "ModuleNotFoundError", "import_smbus": "ModuleNotFoundError", "write_out": "PermissionError",
            "write_home": "PermissionError", "write_data": "ok", "remove_out": "PermissionError", "rmtree_out": "PermissionError",
            "execv_other": "PermissionError", "read_out": "ok", "system": 127 << 8,
            "nice_ffmpeg": "ok" if shutil.which("nice") else "FileNotFoundError",   # 4.15.0: let through (without ffmpeg nice just ends with 127)
            "nice_sh": "FileNotFoundError", "nice_bare": "FileNotFoundError",
            "gh_other_thread": "PermissionError", "gh_dl_port80": "PermissionError", "dl_other_ip": "PermissionError",
            "ai_to_github_ip": "PermissionError", "games_to_ai_ip": "PermissionError", "ai_ip_other_thread": "PermissionError"}
    ok(res.get("ai_dl") not in (None, "PermissionError"), f"KI-Modell (443, Faden «ai-model», Adresse der festen Quelle) durchgelassen: {res.get('ai_dl')}")
    ok(res.get("gh_dl") not in (None, "PermissionError"), f"Spiele-Download zu GitHub (443, eigener Faden) durchgelassen: {res.get('gh_dl')}")
    for k, v in want.items():
        ok(res.get(k) == v, f"{k}: {res.get(k)} (soll {v})")


# ---------------------------------------------------------------------------------------------------------- live run
def throttle(pid, share):
    """«half a core» like the quota of the host: one core (affinity above) and only share of each 100 ms (SIGSTOP / SIGCONT)"""
    import signal

    def run():
        while True:
            try:
                os.kill(pid, signal.SIGCONT); time.sleep(0.1 * share)
                os.kill(pid, signal.SIGSTOP); time.sleep(0.1 * (1 - share))
            except OSError:
                return
        # (the process ended: nothing more to do)
    threading.Thread(target=run, daemon=True, name="throttle").start()
    print(f"   CPU: ein Kern, davon {share:.0%} (SIGSTOP/SIGCONT alle 100 ms)")


def child_env():
    """the same environment demo_start.py gives MoveEye (CHILD_ENV: memory)"""
    import importlib.util
    sp = importlib.util.spec_from_file_location("demo_start_env", os.path.join(ROOT, "demo_start.py"))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return dict(m.CHILD_ENV)


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close()
    return p


class Proxy:
    """like the web host: only /demo/… goes to MoveEye (without «/demo»); everything else is «the homepage» (404, counted)"""
    def __init__(self, port, up):
        self.port, self.up = port, up; self.escaped = []; self.n = 0
        self.srv = socket.socket(); self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("127.0.0.1", port)); self.srv.listen(64)
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            try:
                c, _a = self.srv.accept()
            except OSError:
                return
            threading.Thread(target=self.one, args=(c,), daemon=True).start()

    def one(self, c):
        try:
            head = b""
            while b"\r\n\r\n" not in head and len(head) < 65536:
                ch = c.recv(65536)
                if not ch:
                    c.close(); return
                head += ch
            h, _s, rest = head.partition(b"\r\n\r\n")
            lines = h.decode("latin-1").split("\r\n")
            meth, path, ver = lines[0].split(" ", 2)
            self.n += 1
            if path == "/demo":
                c.sendall(b"HTTP/1.1 301 Moved\r\nLocation: /demo/\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"); c.close(); return
            if not path.startswith("/demo/"):
                self.escaped.append(path)
                c.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 8\r\nConnection: close\r\n\r\nhomepage"); c.close(); return
            ws = any(x.lower().startswith("upgrade:") for x in lines[1:])
            keep = [x for x in lines[1:] if not x.lower().startswith(("connection:", "x-forwarded-", "keep-alive:"))]
            keep += ["Connection: Upgrade" if ws else "Connection: close", "X-Forwarded-For: 203.0.113.7", "X-Forwarded-Proto: http",
                     "X-Forwarded-Host: " + next((x.split(":", 1)[1].strip() for x in lines[1:] if x.lower().startswith("host:")), "")]
            u = socket.create_connection(("127.0.0.1", self.up), timeout=10); u.settimeout(None)
            u.sendall((f"{meth} {path[5:]} {ver}\r\n" + "\r\n".join(keep) + "\r\n\r\n").encode("latin-1") + rest)

            def pipe(a, b):
                try:
                    while True:
                        d = a.recv(65536)
                        if not d:
                            break
                        b.sendall(d)
                except OSError:
                    pass
                for z in (a, b):
                    try:
                        z.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
            t = threading.Thread(target=pipe, args=(u, c), daemon=True); t.start()
            pipe(c, u); t.join(30)
        except (OSError, ValueError):
            pass
        finally:
            for z in (c,):
                try:
                    z.close()
                except OSError:
                    pass

    def close(self):
        self.srv.close()


class FakeWebSim:
    """the web simulator of the homepage, as MoveEye sees it: one WebSocket (MWTUN2), answers /state, /info, camera pictures"""
    def __init__(self, port, path="/demo/simtun"):
        import base64, cv2, numpy as np
        img = np.zeros((360, 640, 3), np.uint8); img[:] = (200, 0, 200)          # magenta (BGR)
        self.jpg = cv2.imencode(".jpg", img)[1].tobytes()
        self.s = socket.create_connection(("127.0.0.1", port), timeout=15)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: http://127.0.0.1:{port}\r\n\r\n").encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            ch = self.s.recv(4096)
            if not ch:
                break
            resp += ch
        self.status = resp.split(b"\r\n", 1)[0].decode("latin-1")
        self.rest = resp.partition(b"\r\n\r\n")[2]
        self.lock = threading.Lock(); self.ch = {}; self.reqs = []; self.closed = False; self.texts = []
        self.last_state = {}; self.pause = False          # 4.16.0: what MoveEye sent last (/state); a tab in the background answers nothing

    def _exact(self, n):
        out = self.rest[:n]; self.rest = self.rest[n:]
        while len(out) < n:
            ch = self.s.recv(n - len(out))
            if not ch:
                raise OSError("closed")
            out += ch
        return out

    def recv_msg(self):
        b0, b1 = self._exact(2)
        ln = b1 & 0x7F
        if ln == 126:
            ln = int.from_bytes(self._exact(2), "big")
        elif ln == 127:
            ln = int.from_bytes(self._exact(8), "big")
        return b0 & 0x0F, self._exact(ln)

    def send(self, op, data):
        m = os.urandom(4); n = len(data)
        head = bytes([0x80 | op]) + (bytes([0x80 | n]) if n < 126 else (bytes([0x80 | 126]) + n.to_bytes(2, "big") if n < 65536 else bytes([0x80 | 127]) + n.to_bytes(8, "big")))
        k = (m * (n // 4 + 1))[:n]
        body = (int.from_bytes(data, "big") ^ int.from_bytes(k, "big")).to_bytes(n, "big") if n else b""
        with self.lock:
            self.s.sendall(head + m + body)

    def hello(self):
        self.send(1, b"MWTUN2 demo %d-1" % int(time.time()))
        op, d = self.recv_msg()
        return d.decode().strip()

    def run(self):
        self.s.settimeout(None)
        try:
            while True:
                op, d = self.recv_msg()
                if op == 1:
                    t = d.decode().split(); self.texts.append(" ".join(t)[:40])
                    if t[0] == "OPEN":
                        self.ch[int(t[1])] = b""
                    elif t[0] == "CLOSE":
                        self.ch.pop(int(t[1]), None)
                    elif t[0] == "TAKEN":
                        break
                elif op == 2:
                    cid = int.from_bytes(d[:4], "big")
                    self.ch[cid] = self.ch.get(cid, b"") + d[4:]
                    self.serve(cid)
                elif op == 9:
                    self.send(10, d)
                elif op == 8:
                    break
        except OSError:
            pass
        self.closed = True

    def out(self, cid, b):
        for i in range(0, len(b), 60000):
            self.send(2, cid.to_bytes(4, "big") + b[i:i + 60000])

    def serve(self, cid):
        if self.pause:
            return
        buf = self.ch.get(cid, b"")
        if b"\r\n\r\n" not in buf:
            return
        head, _s, rest = buf.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        ln = int(next((x.split(":", 1)[1] for x in lines if x.lower().startswith("content-length:")), "0"))
        if len(rest) < ln:
            return
        self.ch[cid] = rest[ln:]
        path = lines[0].split(" ")[1]
        self.reqs.append(path.split("?")[0])
        if "/video.mjpg" in path or path.startswith("/view.mjpg"):
            def stream():
                self.out(cid, b"HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=mwsimframe\r\nCache-Control: no-store\r\n\r\n")
                try:
                    while cid in self.ch and not self.closed:
                        self.out(cid, b"--mwsimframe\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(self.jpg) + self.jpg + b"\r\n")
                        time.sleep(8.0)            # 4.15.1: like the real web simulator behind a slow line - the stream piles up
                except OSError:
                    pass
            threading.Thread(target=stream, daemon=True).start(); return
        if path.startswith("/state"):
            try:
                self.last_state = json.loads(rest[:ln] or b"{}")
            except ValueError:
                pass
            sv = self.last_state.get("servo") or {}                      # the head of the simulator follows (like net.gd)
            body = json.dumps({"ok": True, "pid": 4242, "dark": False, "ambient_c": 14.0,
                               "head_deg": [sv.get("pan_deg", 0.0), sv.get("tilt_deg", 0.0)]}).encode()
        elif path.startswith("/info"):
            body = json.dumps({"name": "Web-Sim (Test)", "version": "3.99.0", "ver": "3.99.0", "cams": 2}).encode()
        elif "/snapshot.jpg" in path:
            body = self.jpg
        else:
            body = json.dumps({"ok": False, "error": "unknown path"}).encode()
        ctype = "image/jpeg" if body is self.jpg else "application/json"
        code = "404 Not Found" if b"unknown path" in body else "200 OK"
        self.out(cid, (f"HTTP/1.1 {code}\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\nConnection: keep-alive\r\n\r\n").encode() + body)

    def close(self):
        try:
            self.send(8, b"\x03\xe8")
        except OSError:
            pass
        try:
            self.s.close()
        except OSError:
            pass


def get(url, data=None, timeout=20, headers=None):
    req = urllib.request.Request(url, data=data, headers=dict({"Content-Type": "application/json"} if data else {}, **(headers or {})))
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except OSError as e:                                  # time-out / refused: a red line, not a crash of the test
        return 0, str(e).encode(), {}


def listen_addrs(pid):
    """(proto, address) of every listening TCP / bound UDP socket of the process"""
    inodes = set()
    for fd in glob.glob(f"/proc/{pid}/fd/*"):
        try:
            l = os.readlink(fd)
        except OSError:
            continue
        m = re.match(r"socket:\[(\d+)\]", l)
        if m:
            inodes.add(m.group(1))
    out = []
    for proto in ("tcp", "tcp6", "udp", "udp6"):
        try:
            rows = open(f"/proc/net/{proto}").read().splitlines()[1:]
        except OSError:
            continue
        for r in rows:
            f = r.split()
            if len(f) < 10 or f[9] not in inodes:
                continue
            if proto.startswith("tcp") and f[3] != "0A":
                continue                                  # only LISTEN
            ip_hex, port_hex = f[1].split(":")
            if len(ip_hex) == 8:
                ip = ".".join(str(int(ip_hex[i:i + 2], 16)) for i in (6, 4, 2, 0))
            else:
                ip = "::1" if ip_hex == "00000000000000000000000001000000" else ("::" if set(ip_hex) == {"0"} else ip_hex)
            out.append((proto, ip, int(port_hex, 16)))
    return out


def threads_n(pid):
    """threads of the MoveEye process (4.15.0: the host had a limit of 64)"""
    try:
        for l in open(f"/proc/{pid}/status"):
            if l.startswith("Threads:"):
                return int(l.split()[1])
    except OSError:
        pass
    return 0


def rss_kb(pid):
    tot = 0
    for p in [pid] + [int(x) for x in subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True).stdout.split()]:
        try:
            for l in open(f"/proc/{p}/status"):
                if l.startswith("VmRSS:"):
                    tot += int(l.split()[1])
        except OSError:
            pass
    return tot


def cpu_s(pid):
    try:
        f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
        return (int(f[11]) + int(f[12])) / os.sysconf("SC_CLK_TCK")
    except (OSError, IndexError, ValueError):
        return 0.0


def run(a):
    mw = a.datei or sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*_*_*.py")),
                           key=lambda p: tuple(int(x) for x in re.findall(r"(\d+)_(\d+)_(\d+)\.py$", p)[0]))[-1]
    txt = open(mw, encoding="utf-8", errors="replace").read(8 * 1024 * 1024)
    if '"--host-modus"' not in txt:
        print(f"{os.path.basename(mw)} kennt --host-modus noch nicht (zuerst bauen)"); return 1
    py = a.python or sys.executable
    if not shutil.which(py):
        print(f"  Hinweis: {py} ist auf diesem Rechner nicht vorhanden - Lauf damit nicht möglich"); WARN.append(f"{py} fehlt")
        return 0
    print(f"Lauf: {os.path.basename(mw)} mit {py} ({subprocess.run([py, '-V'], capture_output=True, text=True).stdout.strip()})")
    cvv = subprocess.run([py, "-c", "import cv2; print(cv2.__version__, 'TF-Import' if hasattr(cv2.dnn, 'readNetFromTensorflow') else 'OHNE TF-Import')"],
                         capture_output=True, text=True)
    print(f"   OpenCV: {(cvv.stdout or cvv.stderr).strip()[-120:]}")
    tmp = tempfile.mkdtemp(prefix="hostdemo_")
    bilder = os.path.join(os.environ.get("TMPDIR") or tempfile.gettempdir(), "host_demo_bilder") if a.browser else ""
    port, pport = free_port(), free_port()
    data = os.path.join(tmp, "demo_daten")
    log = open(os.path.join(tmp, "mw.log"), "w")
    cpu1 = sorted(os.sched_getaffinity(0))[:1]
    pr = subprocess.Popen([py, mw, "--headless", "--bind", "127.0.0.1", "--port", str(port), "--host-modus", "--url-prefix", "/demo",
                           "--config", data], cwd=os.path.dirname(os.path.abspath(mw)), stdout=log, stderr=subprocess.STDOUT,
                          env=dict(os.environ, **child_env(), MW_HOST_KI_AUTO="1" if a.ki else "0"),
                          preexec_fn=(lambda: os.sched_setaffinity(0, set(cpu1))) if a.kern else None)
    if a.kern:
        throttle(pr.pid, a.kern)
    px = Proxy(pport, port)
    base = f"http://127.0.0.1:{pport}/demo"
    sim = None
    try:
        t0 = time.time(); code = 0
        while time.time() - t0 < 180 and pr.poll() is None:
            try:
                code = get(base + "/", timeout=5)[0]
                if code == 200:
                    break
            except OSError:
                pass
            time.sleep(1)
        ok(code == 200, f"Seite über den Proxy da ({time.time() - t0:.0f} s)")
        if code != 200:
            return 1
        rss0 = rss_kb(pr.pid)
        print("A. Vorsilbe")
        c, b, h = get(base + "/")
        t = b.decode("utf-8", "replace")
        ok("__mwBase" in t and '"/demo"' in t, "Live-Seite: Skript mit Vorsilbe")
        left = re.findall(r"""["'`]/(?:api|sim|protect|settings|more|diary|timeline|cams|zones|i18n|cam_feed|video_feed|snapshot\.jpg)\b""", t)
        ok(not left, f"keine absoluten Adressen ohne /demo in der Seite ({len(left)}: {left[:5]})")
        c2, b2, h2 = get(f"http://127.0.0.1:{port}/", headers={"Accept-Encoding": "identity"})
        ok(c2 == 200 and b"__mwBase" in b2, "direkt (ohne Proxy) auch mit Vorsilbe (Host-Modus)")
        t_ = time.time(); c, b, h = get(base + "/api/state", timeout=40)
        try:
            js_ = json.loads(b)
        except ValueError:
            js_ = {}
        ok(c == 200 and isinstance(js_, dict) and "armed" in json.dumps(js_)[:200000],
           f"API über /demo/api/state ({c}, {len(b)} Bytes, {time.time() - t_:.1f} s{'' if c == 200 else ': ' + b[:120].decode('utf-8', 'replace')})")
        c, b, h = get(base + "/i18n/fr.js")
        ok(c == 200, "Übersetzung /demo/i18n/fr.js")
        print("B. Sperren")
        for path, d in (("/api/homepage", {"action": "upload"}), ("/api/wifi", {"action": "scan"}), ("/api/power", {"action": "reboot"}),
                        ("/api/tunnel", {"on": True}), ("/api/update", {"action": "install", "version": "9.9.9"}), ("/api/webpush", {"action": "test"}),
                        ("/api/autostart", {"on": True}), ("/api/helper", {"on": True})):
            c, b, h = get(base + path, json.dumps(d).encode(), headers={"Origin": f"http://127.0.0.1:{pport}"})
            ok(c == 403, f"POST {path}: {c}")
        for path, d in (("/api/ki/state", None), ("/api/ki/model", {"action": "load"}), ("/api/tausch/bio", {"action": "load"}),
                        ("/api/untersuchen", {"cam": "head"}), ("/api/piper", {"action": "load"})):
            c, b, h = get(base + path, json.dumps(d).encode() if d else None, headers={"Origin": f"http://127.0.0.1:{pport}"})
            try:
                er = json.loads(b).get("error")
            except ValueError:
                er = b[:80]
            ok(c == 403 and er in ("not available on the host", "auf dem Host nicht verfügbar"), f"KI auf dem Host nicht verfügbar: {path} {c} {er!r}")
        c, b, h = get(base + "/api/tausch?lang=de")
        ok(c == 200, f"Digitaler Rucksack geht (4.15.0, echte MoveEye): {c}")
        c, b, h = get(base + "/api/party?lang=de")
        try:
            pj = json.loads(b)
        except ValueError:
            pj = {}
        ok(c == 200 and pj.get("lan_url") == "" and pj.get("no_rest") is True,
           f"Spiele auf dem Host: kein «Ohne Login im eigenen WLAN», kein Ruhemodus ({c}, {pj.get('lan_url')!r}, {pj.get('no_rest')})")
        fq = pj.get("fotaq") or {}
        if "free" in fq and "free_need" in fq:
            left = fq["free"] - fq["free_need"]
            ok(0 <= left <= 400 * 1024 * 1024, f"Platz für Spiele = Rest der 400 MB, nicht die ganze Platte ({left / 1048576:.0f} MB)")
        else:
            ok(False, f"Spiele-Zustand ohne free / free_need ({sorted(fq)[:12]})")
        try:
            act0 = json.loads(get(base + "/api/sources")[1]).get("active")
        except ValueError:
            act0 = None
        ok(act0 != "demo", f"ohne Web-Simulator keine gezeichnete Szene (Quelle {act0!r})")
        c, b, h = get(base + "/api/set", json.dumps({"key": "notify_url", "value": "https://ntfy.sh/x"}).encode(), headers={"Origin": f"http://127.0.0.1:{pport}"})
        time.sleep(3)
        la = listen_addrs(pr.pid)
        ok(la and all(ip in ("127.0.0.1", "::1") for _p, ip, _po in la), f"hört nur auf 127.0.0.1: {sorted(set(la))}")
        if a.ohne_sim:
            if a.ram:
                ram_measure(pr.pid, base, a.ram, rss0)
            return 0
        print("C. Web-Simulator über WebSocket")
        sim = FakeWebSim(pport)
        ok(sim.status.startswith("HTTP/1.1 101"), f"WebSocket durch den Proxy: {sim.status}")
        hi = sim.hello()
        ok(hi == "OK", f"Anmeldung MWTUN2: {hi}")
        threading.Thread(target=sim.run, daemon=True).start()
        t1 = time.time(); mag = False; img = None
        import cv2, numpy as np
        while time.time() - t1 < 90:
            time.sleep(2)
            c, b, h = get(base + "/snapshot.jpg")
            if c == 200:
                img = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    m = img.reshape(-1, 3).mean(0)
                    if m[0] > 120 and m[2] > 120 and m[1] < 90:
                        mag = True
            if mag and "/state" in sim.reqs:              # (on half a core the first /state can come after the picture)
                break
        ok("/state" in sim.reqs, f"MoveEye fragt den Web-Simulator ({len(sim.reqs)} Anfragen: {sorted(set(sim.reqs))[:8]})")
        ok(mag, f"Kamerabild kommt durch die WebSocket-Leitung ({time.time() - t1:.0f} s)")
        time.sleep(25)                                 # 4.15.1: the stream of the fake piles up (8 s per picture) - no matter
        lg_ = os.path.join(data, "motionwatch.log")
        lgt = open(lg_, errors="replace").read() if os.path.exists(lg_) else ""
        ok(sim.reqs.count("/cam/0/snapshot.jpg") >= 10 and "/cam/0/video.mjpg" not in sim.reqs,
           f"Host-Modus: Einzelbilder statt Strom ({sim.reqs.count('/cam/0/snapshot.jpg')} × snapshot, Strom {'/cam/0/video.mjpg' in sim.reqs})")
        ok("Camera stopped delivering frames" not in lgt, "Kamera reisst nicht ab, auch wenn die Leitung langsam ist (kein Neuverbinden)")
        head_checks(base, pport, sim)
        hidden_checks(base, sim, data)
        if a.ki:
            print("C4. KI-Modell von der festen Quelle (4.16.0)")
            t4 = time.time(); am = {}
            while time.time() - t4 < 900:
                try:
                    am = json.loads(get(base + "/api/ai_model")[1])
                except ValueError:
                    am = {}
                if am.get("present") and not am.get("busy"):
                    break
                if str(am.get("msg") or "").startswith("failed") and not am.get("busy"):
                    break
                time.sleep(5)
            ok(am.get("present") is True and am.get("msg") == "ready", f"KI-Modell geladen und an ({time.time() - t4:.0f} s, {am})")
            time.sleep(20)
            try:
                ai_ = json.loads(get(base + "/api/health?lang=de", timeout=40)[1])
            except ValueError:
                ai_ = {}
            ail = [x for x in (ai_.get("items") or []) if x.get("id") == "ai"][:1]
            print("   KI-Zeile:", ail)
            lg = open(os.path.join(data, "motionwatch.log"), errors="replace").read() if os.path.exists(os.path.join(data, "motionwatch.log")) else ""
            print("   " + "\n   ".join([l[:220] for l in lg.splitlines() if "[ai]" in l][-8:]))
            ok(bool(ail) and ail[0].get("level") == "ok", f"KI läuft ({ail[0].get('text') if ail else '-'})")
            ok(os.path.isfile(os.path.join(data, "models", "frozen_inference_graph.pb")), "Modell im Datenordner (geprüfter Download)")
        if bilder and img is not None:
            os.makedirs(bilder, exist_ok=True); cv2.imwrite(os.path.join(bilder, "00_websim_kamerabild.jpg"), img)
        if a.browser:
            browser_check(base, bilder)
        if a.ram:
            ram_measure(pr.pid, base, a.ram, rss0)          # 4.15.0: with the web simulator connected (its camera is the picture)
        sim.close()
        if a.sim_aus:
            t2 = time.time(); back = False; act = None
            while time.time() - t2 < 150:
                time.sleep(3)
                try:
                    act = json.loads(get(base + "/api/sources")[1]).get("active")
                except ValueError:
                    act = None
                c, b, h = get(base + "/snapshot.jpg")
                im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR) if c == 200 else None
                mg = im is not None and (lambda m: m[0] > 120 and m[2] > 120 and m[1] < 90)(im.reshape(-1, 3).mean(0))
                lg = os.path.join(data, "motionwatch.log")
                nocam = os.path.exists(lg) and "Video source 'Automatic' not available" in open(lg, errors="replace").read()
                if act != "demo" and im is not None and not mg and nocam:      # 4.15.0: «no camera» (the last source id may stay)
                    back = True; break
            st = {"source_id": act}
            ok(back, f"Web-Simulator weg -> wieder «keine Kamera» ({time.time() - t2:.0f} s, Quelle {st.get('source_id')!r})")
            if not back:
                ml_ = open(os.path.join(data, "motionwatch.log"), errors="replace").read() if os.path.exists(os.path.join(data, "motionwatch.log")) else ""
                print("   " + "\n   ".join(l[:200] for l in ml_.splitlines() if re.search(r"(?i)simulat|web sim|host mode", l))[-3000:])
        esc = [p for p in px.escaped if p not in ("/favicon.ico",)]
        ok(not esc, f"keine Anfrage an der Vorsilbe vorbei ({px.n} Anfragen; daneben: {sorted(set(esc))[:10]})")
        if "/favicon.ico" in px.escaped:
            WARN.append("der Browser fragte /favicon.ico ohne /demo (das holt jeder Browser von selbst)")
        ml = open(os.path.join(data, "motionwatch.log")).read() if os.path.exists(os.path.join(data, "motionwatch.log")) else ""
        print("   Host-Sperren im Protokoll:", sorted(set(re.findall(r"Host mode: refused ([^\n]{0,60})", ml)))[:12])
        ok("Traceback" not in open(log.name).read(), "keine Python-Fehler in der Ausgabe")
    finally:
        if sim:
            sim.close()
        px.close()
        pr.terminate()
        try:
            pr.wait(30)
        except subprocess.TimeoutExpired:
            pr.kill()
        log.close()
        tail = open(log.name).read()[-3000:]
        if FAIL:
            print("---- Ausgabe von MoveEye (Ende) ----\n" + tail)
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


PAGES = [("live", "/"), ("schutz", "/protect"), ("verlauf", "/timeline"), ("einstellungen", "/settings"), ("simulator", "/sim"), ("mehr", "/more"),
         ("tagebuch", "/diary"), ("hilfe", "/help")]


def head_checks(base, pport, sim):
    """4.16.0: the head of the web simulator follows MoveEye (arrows, joystick, teach-in, follow, patrol) and reports back"""
    print("C2. Kopf über die WebSocket-Leitung (4.16.0)")
    H = {"Origin": f"http://127.0.0.1:{pport}"}

    def post(path, d):
        c, b, h = get(base + path, json.dumps(d).encode(), headers=H)
        try:
            return c, json.loads(b)
        except ValueError:
            return c, {"raw": b[:120]}
    g0 = float((sim.last_state.get("servo") or {}).get("pan_goal") or 0.0)
    c, j = post("/api/move", {"dir": "right", "step": 20})
    ok(c == 200 and j.get("ok"), f"Kopf: Pfeil nach rechts ({c} {j})")
    c, j = post("/api/stick", {"x": 0.0, "y": 0.8, "speed": 60})
    ok(c == 200 and j.get("ok"), f"Kopf: Joystick (/api/stick) geht ({c} {j})")
    time.sleep(1.5)
    post("/api/stick", {"x": 0.0, "y": 0.0, "speed": 60})
    t3 = time.time(); sv = {}
    while time.time() - t3 < 20:
        sv = sim.last_state.get("servo") or {}
        if float(sv.get("pan_goal") or 0) > g0 + 5 and float(sv.get("pan_deg") or 0) > g0 + 5:
            break
        time.sleep(0.5)
    ok(float(sv.get("pan_goal") or 0) > g0 + 5 and float(sv.get("pan_deg") or 0) > g0 + 5 and not sv.get("estop"),
       f"die Ziele kommen beim Web-Simulator an (pan_goal {g0:.1f} -> {sv.get('pan_goal')}, pan_deg {sv.get('pan_deg')}, "
       f"tilt_goal {sv.get('tilt_goal')}, estop {sv.get('estop')})")
    time.sleep(1.0)
    c, b, h = get(base + "/api/servo?lang=de")
    try:
        js = json.loads(b)
    except ValueError:
        js = {}
    hd = js.get("sim_head")
    ok(isinstance(hd, list) and len(hd) == 2 and abs(float(hd[0]) - float(sv.get("pan_deg") or 0)) < 15,
       f"der Web-Simulator meldet den Kopf zurück, MoveEye zeigt ihn (sim_head {hd})")
    ok(not js.get("blocked") and not js.get("inhibit"), f"Servos nicht gestoppt (blocked {js.get('blocked')!r}, inhibit {js.get('inhibit')!r})")
    c, j = post("/api/follow", {"on": True})
    ok(c == 200 and j.get("on"), f"Folgen an ({c} {j})")
    time.sleep(1.5)
    ok((sim.last_state.get("servo") or {}).get("track") is True, "Folgen kommt beim Web-Simulator an")
    post("/api/follow", {"on": False})
    c, j = post("/api/servo", {"op": "add", "name": "Tor"})
    ok(c == 200 and j.get("ok"), f"Teach-in-Punkt gespeichert ({c} {j})")
    post("/api/move", {"dir": "left", "step": 40})
    time.sleep(0.5)
    c2, j2 = post("/api/servo", {"op": "goto", "i": j.get("i", 0)})
    ok(c2 == 200 and j2.get("ok"), f"Teach-in-Punkt anfahren ({c2} {j2})")
    c, j = post("/api/quick", {"action": "patrol"})
    ok(c == 200 and j.get("ok") and j.get("patrol"), f"Patrouille an ({c} {j})")
    for _ in range(3):
        if not j.get("patrol"):
            break
        c, j = post("/api/quick", {"action": "patrol"})
    ok(not j.get("patrol"), f"Patrouille wieder aus ({j})")


def _st(b):
    """the state of /api/state (it sits under «state»)"""
    try:
        j = json.loads(b)
    except ValueError:
        return {}
    return j.get("state", j) if isinstance(j, dict) else {}


def hidden_checks(base, sim, data):
    """4.16.0: the tab of the web simulator in the background - no «connecting …», no reconnecting, no watchdog banner"""
    print("C3. Simulator-Tab im Hintergrund (4.16.0)")
    sim.send(1, b"VIS hidden"); sim.pause = True
    time.sleep(4)
    n0 = len(sim.reqs)
    time.sleep(6)
    t_ = time.time(); c, b, h = get(base + "/api/state?lang=de", timeout=40)
    ok(c == 200 and time.time() - t_ < 10, f"/api/state antwortet, auch wenn der Tab im Hintergrund ist ({c}, {time.time() - t_:.1f} s)")
    st = _st(b)
    sw = st.get("simwait") or {}
    if not ok(sw.get("why") == "hidden" and "Hintergrund" in str(sw.get("title")) and sw.get("url") == "/Sim/",
              f"Hinweis «Simulator-Tab ist im Hintergrund – Bild pausiert» ({sw.get('why')!r}: {sw.get('title')!r}, {sw.get('hint')!r})"):
        lg = open(os.path.join(data, "motionwatch.log"), errors="replace").read() if os.path.exists(os.path.join(data, "motionwatch.log")) else ""
        print("   sim:", json.dumps(st.get("sim"))[:300], "| source", st.get("source_id"), st.get("source"), "|", b[:200])
        print("   " + "\n   ".join([l[:160] for l in lg.splitlines() if re.search(r"(?i)simulat|host mode", l)][-8:]))
    c, b, h = get(base + "/snapshot.jpg")
    ok(c == 200 and len(b) > 1000, "Live-Bild bleibt (das letzte Bild des Simulators)")
    c, b, h = get(base + "/sim/view.jpg?w=320")
    ok(c == 200 and h.get("X-MW-Wait") == "1", f"Simulator-Ansicht: Ruhebild «im Hintergrund» ({c}, {h.get('X-MW-Wait')})")
    time.sleep(35)
    ok(len(sim.reqs) - n0 <= 1, f"im Hintergrund fragt MoveEye nichts ({len(sim.reqs) - n0} Anfragen in 41 s)")
    try:
        st = _st(get(base + "/api/state?lang=de", timeout=40)[1])
    except ValueError:
        st = {}
    lg = open(os.path.join(data, "motionwatch.log"), errors="replace").read() if os.path.exists(os.path.join(data, "motionwatch.log")) else ""
    ok("Web simulator gone" not in lg and (st.get("simwait") or {}).get("why") == "hidden",
       f"die Leitung hält 45 s im Hintergrund (Protokoll ohne «gone», Grund {(st.get('simwait') or {}).get('why')!r})")
    ok("camera loop hangs" not in lg, "kein Watchdog-Banner «die Kamera-Schleife hängt»")
    c, b, h = get(base + "/api/servo?lang=de")
    try:
        inh = json.loads(b).get("inhibit")
    except ValueError:
        inh = "?"
    ok(not inh, f"Servos nicht gestoppt ({inh!r})")
    sim.pause = False; sim.send(1, b"VIS visible")
    t5 = time.time(); n1 = sim.reqs.count("/cam/0/snapshot.jpg"); sw = {"why": "?"}
    while time.time() - t5 < 30:
        time.sleep(2)
        try:
            sw = _st(get(base + "/api/state?lang=de", timeout=40)[1]).get("simwait") or {}
        except ValueError:
            sw = {"why": "?"}
        if sim.reqs.count("/cam/0/snapshot.jpg") > n1 + 3 and not sw:
            break
    ok(sim.reqs.count("/cam/0/snapshot.jpg") > n1 + 3 and not sw, f"wieder sichtbar: Bilder kommen, kein Hinweis ({time.time() - t5:.0f} s, {sw})")
    c, b, h = get(base + "/sim/view.jpg?w=320")
    ok(c == 200 and h.get("X-MW-Live") == "1", f"Simulator-Ansicht ohne Bild des Simulator-Fensters: das Bild der Live-Seite ({c}, {sorted(h)[:6]})")


def browser_check(base, bilder):
    print("D. Browser (390 px)")
    from playwright.sync_api import sync_playwright
    os.makedirs(bilder, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        for name, path in PAGES:
            pg = ctx.new_page(); errs = []; bad = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.on("console", lambda m: errs.append("console: " + m.text[:200]) if m.type == "error" else None)
            fails = []
            pg.on("response", lambda r: (bad.append(f"{r.status} {r.url}") if "/demo/" not in r.url else fails.append(f"{r.status} {r.url.split('/demo', 1)[1][:60]}")) if r.status >= 400 else None)
            pg.goto(base + path, wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(4000)
            pg.screenshot(path=os.path.join(bilder, f"{PAGES.index((name, path)) + 1:02d}_{name}.png"))
            href_ok = pg.evaluate("""() => [...document.querySelectorAll('a[href],img[src],script[src],link[href]')]
                .map(e => e.getAttribute('href') || e.getAttribute('src')).filter(u => u && u[0] === '/' && u[1] !== '/' && !u.startsWith('/demo'))""")
            real_errs = [e for e in errs if "favicon" not in e and "Failed to load resource" not in e]
            if fails:
                print(f"   {name}: Antworten >= 400 (gesperrt / ohne Hardware): {sorted(set(fails))[:8]}")
            ok(not real_errs, f"{name}: keine JS-Fehler" + (f" ({real_errs[:3]})" if real_errs else ""))
            ok(not href_ok, f"{name}: alle Verweise mit /demo" + (f" ({href_ok[:5]})" if href_ok else ""))
            ok(not bad, f"{name}: keine Anfrage ausserhalb /demo" + (f" ({bad[:3]})" if bad else ""))
            if name == "live":
                pg.evaluate("document.querySelector(\"a[href='/demo/protect']\").click()")    # (the first-start guide covers the page)
                pg.wait_for_timeout(2500)
                ok(pg.url.endswith("/demo/protect"), f"Klick auf «Schutz» bleibt unter /demo ({pg.url})")
            pg.close()
        br.close()


def ram_measure(pid, base, secs, rss0):
    print(f"E. Speicher und CPU über {secs} s (mit Besuchern)")
    stop = threading.Event(); n = {"p": 0, "f": 0}

    def visitor():
        pages = ["/", "/protect", "/timeline", "/settings", "/sim", "/more", "/api/state", "/api/state", "/snapshot.jpg"]
        i = 0
        while not stop.is_set():
            try:
                get(base + pages[i % len(pages)], timeout=30); n["p"] += 1
            except OSError:
                pass
            i += 1; stop.wait(1.0)

    def stream():
        while not stop.is_set():
            try:
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(base + "/video_feed", timeout=30) as r:
                    t0 = time.time()
                    while not stop.is_set() and time.time() - t0 < 60:
                        b = r.read1(65536) if hasattr(r, "read1") else r.read(65536)
                        if not b:
                            break
                        n["f"] += b.count(b"Content-Type: image/jpeg")       # 4.16.0: pictures of the live view
            except Exception:                                 # (OSError, http.client.IncompleteRead at the end of a stream)
                stop.wait(2)
    th = [threading.Thread(target=visitor, daemon=True) for _ in range(2)] + [threading.Thread(target=stream, daemon=True)]
    for t in th:
        t.start()
    out = []; c0 = cpu_s(pid); t0 = time.time(); peak = 0; th0 = threads_n(pid); thp = th0
    while time.time() - t0 < secs:
        r = rss_kb(pid); peak = max(peak, r); out.append((round(time.time() - t0), r)); thp = max(thp, threads_n(pid))
        time.sleep(5)
    stop.set()
    cpu = (cpu_s(pid) - c0) / max(1.0, time.time() - t0) * 100
    avg = sum(x[1] for x in out) / max(1, len(out))
    fps = n["f"] / max(1.0, time.time() - t0)
    rep = (f"RSS beim Start {rss0 / 1024:.0f} MB, Spitze {peak / 1024:.0f} MB, Mittel {avg / 1024:.0f} MB über {secs} s; "
           f"CPU im Mittel {cpu:.0f} % eines Kerns; {n['p']} Seitenaufrufe + Live-Bild {fps:.1f} Bilder/s; Threads {th0} am Anfang, höchstens {thp}")
    print("   " + rep)
    p_ = os.path.join(os.environ.get("TMPDIR") or tempfile.gettempdir(), "host_demo_ram.log")
    with open(p_, "w") as f:
        f.write(rep + "\n" + "\n".join(f"{t}\t{r}" for t, r in out) + "\n")
    ok(peak < 1200 * 1024, f"Spitze unter 1.2 GB (4.16.0: der Host hat 1.5 GB) ({peak / 1024:.0f} MB)")
    if peak > 1000 * 1024:
        WARN.append(f"Speicher-Spitze {peak / 1024:.0f} MB - über 1 GB (Reserve bis 1.5 GB)")
    ok(fps >= 1.0, f"Live-Bild läuft weiter ({fps:.1f} Bilder/s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lauf", action="store_true")
    ap.add_argument("--datei", default="")
    ap.add_argument("--python", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--ram", type=int, default=0)
    ap.add_argument("--sim-aus", action="store_true", help="also wait until the simulation switches off after the web simulator left (about 70 s)")
    ap.add_argument("--ohne-statisch", action="store_true")
    ap.add_argument("--ohne-sim", action="store_true", help="no web simulator (for the RAM baseline)")
    ap.add_argument("--ki", action="store_true", help="4.16.0: MoveEye fetches the AI model from its fixed source (internet) and measures with AI")
    ap.add_argument("--kern", type=float, default=0.0, help="4.16.0: only this share of one core (0.5 = like the host)")
    a = ap.parse_args()
    if not a.ohne_statisch:
        static()
    if a.lauf:
        run(a)
    for w in WARN:
        print("  Hinweis: " + w)
    print("FEHLER: " + "; ".join(FAIL) if FAIL else "host_demo: alles gut")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
