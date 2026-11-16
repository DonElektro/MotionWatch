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
          "log_event": lambda k, t: None, "save_settings": lambda: None}
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
    ok("a.demo = a.headless = True" in st and 'a.bind = "127.0.0.1"' in st, "640: Host-Modus = Demo, ohne Fenster, nur 127.0.0.1")
    i_lock, i_thr = st.find("host_mode_start(a)"), st.find("threading.Thread(target=clock_guard_loop")
    ok(0 < i_lock < i_thr, "Sperren vor dem ersten Faden")
    d210 = open(os.path.join(ROOT, "quelle", "210_demo.py"), encoding="utf-8").read()
    ok('DEMO["on"] and not host_sim_source(spec)' in d210, "210: Simulator-Bild nur im Host-Modus mit verbundenem Web-Simulator")
    for k in ("/api/homepage", "/api/tunnel", "/api/helper", "/api/webpush", "/api/update", "/api/dev", "/api/relay", "/api/fehler/fix"):
        ok(k in src.split("HOST_BLOCK = ", 1)[1].split(")", 1)[0], f"HOST_BLOCK: {k}")
    d = open(os.path.join(ROOT, "quelle", "210_demo.py"), encoding="utf-8").read().split("DEMO_BLOCK = ", 1)[1].split(")", 1)[0]
    for k in ("/api/power", "/api/wifi", "/api/hotspot", "/api/password", "/api/autostart"):
        ok(k in d, f"DEMO_BLOCK (210): {k}")
    for k in ("RPi", "gpiozero", "smbus", "spidev", "picamera2", "dbus", "bluetooth", "serial"):
        ok(f'"{k}"' in src.split("HOST_NO_MODULES = ", 1)[1].split(")", 1)[0], f"keine Hardware: {k}")
    ok('HOST_PROGS = ("ffmpeg", "ffprobe")' in src, "Programme: nur ffmpeg / ffprobe")
    ok("# wraps: WebStream._serve" in src, "Wrapper markiert (bauen.py)")
    hn = src.split("def _host_note(", 1)[1].split("\ndef ", 1)[0]
    ok("log_event(" not in hn.replace("Never log_event", ""), "Sperren schreiben nicht selbst ins Protokoll (LOCK, sonst Verklemmung wie in /api/state)")
    print("2. Skript in den Seiten")
    ns = part_ns()
    js = ns["HOST_SHIM_JS"].replace("%PREFIX%", json.dumps("/demo"))
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
            "execv_other": "PermissionError", "read_out": "ok", "system": 127 << 8}
    for k, v in want.items():
        ok(res.get(k) == v, f"{k}: {res.get(k)} (soll {v})")


# ---------------------------------------------------------------------------------------------------------- live run
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
                        time.sleep(0.2)
                except OSError:
                    pass
            threading.Thread(target=stream, daemon=True).start(); return
        if path.startswith("/state"):
            body = json.dumps({"ok": True, "pid": 4242, "dark": False, "ambient_c": 14.0}).encode()
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
    tmp = tempfile.mkdtemp(prefix="hostdemo_")
    bilder = os.path.join(os.environ.get("TMPDIR") or tempfile.gettempdir(), "host_demo_bilder") if a.browser else ""
    port, pport = free_port(), free_port()
    data = os.path.join(tmp, "demo_daten")
    log = open(os.path.join(tmp, "mw.log"), "w")
    pr = subprocess.Popen([py, mw, "--demo", "--headless", "--bind", "127.0.0.1", "--port", str(port), "--host-modus", "--url-prefix", "/demo",
                           "--config", data], cwd=os.path.dirname(os.path.abspath(mw)), stdout=log, stderr=subprocess.STDOUT,
                          env=dict(os.environ, **child_env()))
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
        while time.time() - t1 < 60:
            time.sleep(2)
            c, b, h = get(base + "/snapshot.jpg")
            if c == 200:
                img = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    m = img.reshape(-1, 3).mean(0)
                    if m[0] > 120 and m[2] > 120 and m[1] < 90:
                        mag = True; break
        ok("/state" in sim.reqs, f"MoveEye fragt den Web-Simulator ({len(sim.reqs)} Anfragen: {sorted(set(sim.reqs))[:8]})")
        ok(mag, f"Kamerabild kommt durch die WebSocket-Leitung ({time.time() - t1:.0f} s)")
        if bilder and img is not None:
            os.makedirs(bilder, exist_ok=True); cv2.imwrite(os.path.join(bilder, "00_websim_kamerabild.jpg"), img)
        if a.browser:
            browser_check(base, bilder)
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
                if act == "demo" and im is not None and not mg:
                    back = True; break
            st = {"source_id": act}
            ok(back, f"Web-Simulator weg -> wieder die gezeichnete Szene ({time.time() - t2:.0f} s, Quelle {st.get('source_id')!r})")
            if not back:
                ml_ = open(os.path.join(data, "motionwatch.log"), errors="replace").read() if os.path.exists(os.path.join(data, "motionwatch.log")) else ""
                print("   " + "\n   ".join(l[:200] for l in ml_.splitlines() if re.search(r"(?i)simulat|web sim|host mode", l))[-3000:])
        if a.ram:
            ram_measure(pr.pid, base, a.ram, rss0)
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
    stop = threading.Event(); n = {"p": 0}

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
                        if not r.read(65536):
                            break
            except OSError:
                stop.wait(2)
    th = [threading.Thread(target=visitor, daemon=True) for _ in range(2)] + [threading.Thread(target=stream, daemon=True)]
    for t in th:
        t.start()
    out = []; c0 = cpu_s(pid); t0 = time.time(); peak = 0
    while time.time() - t0 < secs:
        r = rss_kb(pid); peak = max(peak, r); out.append((round(time.time() - t0), r))
        time.sleep(5)
    stop.set()
    cpu = (cpu_s(pid) - c0) / max(1.0, time.time() - t0) * 100
    avg = sum(x[1] for x in out) / max(1, len(out))
    rep = (f"RSS beim Start {rss0 / 1024:.0f} MB, Spitze {peak / 1024:.0f} MB, Mittel {avg / 1024:.0f} MB über {secs} s; "
           f"CPU im Mittel {cpu:.0f} % eines Kerns; {n['p']} Seitenaufrufe + Live-Bild")
    print("   " + rep)
    p_ = os.path.join(os.environ.get("TMPDIR") or tempfile.gettempdir(), "host_demo_ram.log")
    with open(p_, "w") as f:
        f.write(rep + "\n" + "\n".join(f"{t}\t{r}" for t, r in out) + "\n")
    ok(peak < 1024 * 1024, f"Spitze unter 1 GB, der Grenze des Hosts ({peak / 1024:.0f} MB)")
    if peak > 700 * 1024:
        WARN.append(f"Speicher-Spitze {peak / 1024:.0f} MB - über dem Ziel von etwa 700 MB (Reserve)")


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
