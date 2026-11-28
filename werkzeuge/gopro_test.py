#!/usr/bin/env python3
"""Test «GoPro als Zusatzkamera» (Teil 639zzzzzze_gopro_kern) am echten Programm – ohne echte GoPro.

Eine GoPro mit Labs-Firmware schickt nach dem Start-Code einen RTMP-Strom (H.264). Hier spielt ffmpeg die GoPro:
testsrc2 (bewegtes Testbild) -> rtmp://127.0.0.1:<port>/gopro/<id>-<schlüssel>. Prüft:
  A  im Prozess (Ersatz-tkinter): die drei Labs-Codes (WLAN / Adresse / Start 480/720/1080 + Kopie, HERO12/13 ohne Vorsatz),
     falsche Zeichen abgelehnt, Weg-Schnittstelle (gopro_register_weg, gopro_quelle), nur Administrator (role_allows),
     Pi-Fenster «GoPro hinzufügen …» (Knopf unter der Videoquelle, Dialog mit Schritten), Selbsttest des Teils
  B  MoveEye (eigener Ordner, freier Port) mit dem einfachen Empfänger (ffmpeg): wartet -> Strom -> Zusatzkamera «connected» mit
     640x360 und Bewegung, Bild über /cam_snap; Strom weg -> «lost», Protokoll, stille Meldung (Webhook, event info), Start-Code
     wieder; Strom wieder -> «streaming»; QR-Codes über /api/gopro/qr = genau die Labs-Texte (SVG verglichen), das WLAN-Passwort
     steht danach in KEINER Datei des Ordners und nicht im Protokoll; ohne Anmeldung 401; Neustart: GoPro bleibt
  C  dasselbe mit mediamtx (feste Fassung, Prüfsumme der Release-Liste und – wenn fest im Programm – MTX["pins"]): Strom über
     RTSP an MoveEye, Abbruch erkannt. Ohne mediamtx übersprungen; --mtx-pflicht (CI) = rot statt übersprungen.
  D  Seite /gopro (Playwright, Handy 390 px und PC, keine JavaScript-Fehler), Knopf auf /cams; Bildschirmfotos nach --bilder

  python3 werkzeuge/gopro_test.py [--datei X.py] [--bilder ORDNER] [--mtx PFAD] [--mtx-pflicht] [--ohne-browser]
  python3 werkzeuge/gopro_test.py --mtx-pruefsummen     # Prüfsummen der mediamtx-Pakete (für MTX["pins"])
"""
import argparse
import base64
import glob
import hashlib
import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "GoPro-" + base64.b16encode(os.urandom(5)).decode().lower()
WLAN_PW = "WlanGeheim-" + base64.b16encode(os.urandom(6)).decode().lower()
GID, KEY = "0a1b2c3d", "00112233445566ff"
MTX_VERSION = "v1.21.4"
MTX_URL = "https://github.com/bluenviron/mediamtx/releases/download/"
FEHLER = []


def pruef(ok, text):
    print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
    if not ok:
        FEHLER.append(text)


def freie_ports(n=1, start=21000):
    """n freie Ports hintereinander (der Empfänger braucht RTMP, RTSP, API, UDP = Port .. Port+3)"""
    for p in range(start, start + 4000, 7):
        ok = True
        for q in range(p, p + n):
            with socket.socket() as sk:
                try:
                    sk.bind(("127.0.0.1", q))
                except OSError:
                    ok = False; break
        if ok:
            return p
    raise SystemExit("keine freien Ports")


def neueste_datei():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


# ------------------------------------------------------------------ mediamtx (feste Fassung)
def mtx_holen(ziel):
    """das amd64-Paket von GitHub (wie MoveEye: Prüfsumme der Liste des Releases), nur die Datei «mediamtx»"""
    os.makedirs(ziel, exist_ok=True)
    exe = os.path.join(ziel, "mediamtx")
    if os.path.isfile(exe):
        return exe
    name = "mediamtx_%s_linux_amd64.tar.gz" % MTX_VERSION
    lst = urllib.request.urlopen(MTX_URL + MTX_VERSION + "/checksums.sha256", timeout=60).read().decode()
    m = re.search(r"^([0-9a-f]{64})\s+\*?" + re.escape(name) + r"\s*$", lst, re.M)
    if not m:
        raise RuntimeError("keine Prüfsumme für " + name)
    b = urllib.request.urlopen(MTX_URL + MTX_VERSION + "/" + name, timeout=180).read()
    if hashlib.sha256(b).hexdigest() != m.group(1):
        raise RuntimeError("Prüfsumme stimmt nicht")
    tgz = os.path.join(ziel, name)
    with open(tgz, "wb") as f:
        f.write(b)
    with tarfile.open(tgz) as tf:
        mem = tf.getmember("mediamtx")
        with tf.extractfile(mem) as s, open(exe, "wb") as f:
            shutil.copyfileobj(s, f)
    os.chmod(exe, 0o755); os.remove(tgz)
    for z in lst.splitlines():
        if "_linux_" in z:
            print("    MTX-PRUEFSUMME " + z.replace("*", " "), flush=True)
    return exe


def github_da():
    try:
        urllib.request.urlopen(MTX_URL + MTX_VERSION + "/checksums.sha256", timeout=20).read(64); return True
    except Exception:                                                # noqa: BLE001
        return False


def pruefsummen():
    lst = urllib.request.urlopen(MTX_URL + MTX_VERSION + "/checksums.sha256", timeout=60).read().decode()
    for arch in ("arm64", "armv7", "amd64"):
        n = "mediamtx_%s_linux_%s.tar.gz" % (MTX_VERSION, arch)
        b = urllib.request.urlopen(MTX_URL + MTX_VERSION + "/" + n, timeout=180).read()
        h = hashlib.sha256(b).hexdigest()
        print('    "%s": {"size": %d, "sha256": "%s"},   # %s, Liste: %s' % (arch, len(b), h, n, "ok" if h in lst else "FEHLT"))
    return 0


# ------------------------------------------------------------------ die nachgestellte GoPro
def gopro_senden(port, sek=0):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-re", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=15"]
    if sek:
        cmd += ["-t", str(sek)]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-g", "15", "-pix_fmt", "yuv420p",
            "-f", "flv", "rtmp://127.0.0.1:%d/gopro/%s-%s" % (port, GID, KEY)]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stopp(p):
    if p is not None and p.poll() is None:
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()


class Haken(http.server.BaseHTTPRequestHandler):
    """Webhook-Empfänger: die stille Meldung kommt als JSON (event info)"""
    got = []

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            Haken.got.append(json.loads(self.rfile.read(n).decode() or "{}"))
        except ValueError:
            Haken.got.append({})
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


# ------------------------------------------------------------------ A: im Prozess
def teil_a(datei):
    print("A · im Prozess (Ersatz-tkinter)", flush=True)
    src = open(os.path.join(HIER, "lupe_test.py"), encoding="utf-8").read()
    exec(re.search(r'FAKE_TK = r"""(.*?)"""', src, re.S).group(1), {})
    home = tempfile.mkdtemp(prefix="mw_gopro_a_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_gopro_a", "__file__": os.path.abspath(datei)}
    try:
        exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
        CFG = ns["CFG"]
        ns["save_settings"] = lambda *a, **k: None
        ns["cams_apply"] = lambda *a, **k: None
        pruef(bool(ns["gopro_selftest"]()), "Selbsttest des Teils")
        CFG.update(gopro_devs=[{"id": GID, "name": "Zelt", "modell": "hero8", "weg": "rtmp", "key": KEY, "res": "720", "copy": False,
                                "aktiv": True, "ip": "", "x": {}}], extra_cams=[], gopro_rtmp_port=19350, lang="de")
        dev = ns["gopro_dev"](GID)
        q = ns["gopro_qr_text"]
        pruef(q("join", None, "Camping", "pw:1 x") == '!MJOIN="Camping:pw:1 x"', "WLAN-Code !MJOIN=\"ssid:passwort\"")
        pruef(q("rtmp", dev, ip="192.168.4.20") == '!MRTMP="rtmp://192.168.4.20:19350/gopro/%s-%s"' % (GID, KEY), "Adress-Code !MRTMP")
        want = {("480", False): "oW1mVr1080!W!GS", ("720", False): "oW1mVr1080!W!GM", ("1080", False): "oW1mVr1080!W!GL", ("1080", True): "oW1mVr1080!W!GLC"}
        got = {}
        for (r, c), w in want.items():
            dev.update(res=r, copy=c); got[(r, c)] = q("start", dev)
        pruef(got == want, "Start-Code 480 / 720 / 1080 / 1080 + Kopie (%s)" % sorted(got.values()))
        dev.update(modell="hero12", res="720", copy=False)
        pruef(q("start", dev) == "!GM", "HERO12: ohne «oW1mVr1080!W» (wie der Labs-Generator)")
        dev.update(modell="hero8")
        bad = 0
        for s_, p_ in (("a:b", "x"), ("x", 'a"b'), ("", "x"), ("x", "a\nb"), ("x" * 33, "y")):
            try:
                q("join", None, s_, p_)
            except ValueError:
                bad += 1
        pruef(bad == 5, "WLAN-Code: « : » im Namen, \", Zeilenumbruch, leerer / zu langer Name abgelehnt (%d/5)" % bad)
        ra = ns["role_allows"]
        pruef(not ra("view", "/api/gopro", "GET", {}) and not ra("view", "/gopro", "GET", {}) and not ra("view", "/api/gopro", "POST", {"action": "add"})
              and not ra("view", "/api/gopro/qr", "POST", {}) and ra("admin", "/api/gopro", "POST", {}), "nur der Administrator (role_allows)")
        # the window
        tkm = sys.modules["tkinter"]
        made = tkm.Button.__mro__[1].made
        n0 = len(made)
        app = type("A", (), {})()
        app.root = tkm.Tk()
        ns["_gp_source_box_570"] = lambda self, parent: None
        ns["_gp_app_source_box"](app, tkm.Frame())
        btn = [w for w in made[n0:] if "GoPro hinzufügen" in str(w.k.get("text", ""))]
        pruef(len(btn) == 1, "Pi-Fenster: Knopf «GoPro hinzufügen …» unter der Videoquelle")
        pruef(ns["App"]._build_source_box is ns["_gp_app_source_box"], "Pi-Fenster: Hülle um App._build_source_box")
        n1 = len(made)
        ns["_GP_W"]["thread"] = type("T", (), {"is_alive": lambda self: True})()      # no watch thread in the window test
        top = ns["gopro_tk_dialog"](app)
        txt = " ".join(str(w.k.get("text", "")) for w in made[n1:])
        pruef(top is not None and all(s in txt for s in ("WLAN für die GoPro", "Wohin die GoPro das Bild schickt", "Live-Strom starten",
                                                         "Empfänger für den Live-Strom", "Neue GoPro")),
              "Pi-Fenster: Dialog mit Empfänger, WLAN / Adresse / Start, «Neue GoPro»")
        pw_e = [w for w in made[n1:] if type(w).__name__ == "Entry" and w.k.get("show") == "•"]
        pruef(len(pw_e) == 1, "Pi-Fenster: Passwort-Feld verdeckt (•)")
        # the Wi-Fi code in the window: no text, closes by itself
        n2 = len(made)
        ns["qr_png"] = lambda t, s=6: b"\x89PNG"
        ns["_gp_tk_qr"](top, '!MJOIN="a:' + WLAN_PW + '"', secret=True)
        pruef(not any(WLAN_PW in str(w.k.get("text", "")) for w in made[n2:]), "Pi-Fenster: der WLAN-Code zeigt das Passwort nicht als Text")
        return ns
    finally:
        shutil.rmtree(home, ignore_errors=True)


# ------------------------------------------------------------------ B / C: MoveEye
def einstellungen(cfg, port, hook, mtx=""):
    st = {"source": "demo", "extra_cams": ["gopro:" + GID], "kopf_ov": "", "thermal_source": "", "thermal_on": False,
          "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False,
          "ui_simple": False, "tours_auto": False, "detection_on": True, "record": False,
          "notify_on": True, "notify_type": "webhook", "notify_url": hook,
          "gopro_rtmp_port": port, "gopro_mtx": mtx,
          "gopro_devs": [{"id": GID, "name": "Zelt", "modell": "hero8", "weg": "rtmp", "key": KEY, "res": "720", "copy": False,
                          "aktiv": True, "ip": "", "x": {}}]}
    os.makedirs(cfg, exist_ok=True)
    p = os.path.join(cfg, "motionwatch_settings.json")
    if os.path.exists(p):
        d = json.load(open(p)); d.setdefault("cfg", {}).update(gopro_mtx=mtx, gopro_rtmp_port=port)
    else:
        d = {"cfg": st}
    with open(p, "w") as f:
        json.dump(d, f)


class MW:
    def __init__(self, datei, tmp, port_web):
        self.datei, self.tmp, self.port = datei, tmp, port_web
        self.base = "http://127.0.0.1:%d" % port_web
        m = urllib.request.HTTPPasswordMgrWithDefaultRealm(); m.add_password(None, self.base, "admin", PASSWORT)
        self.op = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPBasicAuthHandler(m))
        self.p = None

    def start(self):
        logf = open(os.path.join(self.tmp, "log.txt"), "a")
        env = dict(os.environ, PATH=os.environ.get("PATH", ""))
        self.p = subprocess.Popen([sys.executable, self.datei, "--headless", "--port", str(self.port), "--bind", "127.0.0.1",
                                   "--config", os.path.join(self.tmp, "mw"), "--web-password", PASSWORT],
                                  stdout=logf, stderr=subprocess.STDOUT, cwd=self.tmp, env=env)
        for _i in range(240):
            if self.p.poll() is not None:
                sys.exit("MoveEye hat sich beendet:\n" + self.log()[-3000:])
            try:
                self.op.open(self.base + "/manifest.webmanifest", timeout=2); return
            except Exception:
                time.sleep(1)
        sys.exit("MoveEye startet nicht")

    def stop(self):
        if self.p is not None and self.p.poll() is None:
            self.p.terminate()
            try:
                self.p.wait(20)
            except subprocess.TimeoutExpired:
                self.p.kill()

    def log(self):
        """stdout (log.txt) + the event log of MoveEye (mw/motionwatch.log)"""
        out = ""
        for n in ("log.txt", os.path.join("mw", "motionwatch.log")):
            try:
                out += open(os.path.join(self.tmp, n), errors="replace").read()
            except OSError:
                pass
        return out

    def api(self, path, data=None, raw=False):
        req = urllib.request.Request(self.base + path, data=None if data is None else json.dumps(data).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with self.op.open(req, timeout=20) as r:
                b = r.read()
                return b if raw else json.loads(b.decode() or "{}")
        except urllib.error.HTTPError as e:
            b = e.read()
            if raw:
                return b
            try:
                return dict(json.loads(b.decode() or "{}"), _code=e.code)
            except ValueError:
                return {"_code": e.code}

    def dev(self):
        s = self.api("/api/gopro?lang=de")
        return s, next((d for d in s.get("devs") or [] if d["id"] == GID), {})

    def warte(self, pred, sek=60):
        t_ = time.time() + sek; s = d = {}
        while time.time() < t_:
            s, d = self.dev()
            if pred(s, d):
                return s, d
            time.sleep(0.5)
        return s, d

    def cam(self):
        j = self.api("/api/cams")
        cams = j.get("cams", j) if isinstance(j, dict) else j
        return next((c for c in cams or [] if str(c.get("id")) == "gopro:" + GID), {})


def lauf(datei, art, mtx, ns, hook_url, bilder, browser):
    """B (art ffmpeg) or C (art mediamtx)"""
    print(("B · einfacher Empfänger (ffmpeg)" if art == "ffmpeg" else "C · mediamtx " + MTX_VERSION), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_gopro_%s_" % art)
    port_rx = freie_ports(4, 21000 if art == "ffmpeg" else 23000)
    port_web = freie_ports(1, 5180 if art == "ffmpeg" else 5190)
    inst = art == "mediamtx" and mtx == "INSTALL"
    einstellungen(os.path.join(tmp, "mw"), port_rx, hook_url, mtx if art == "mediamtx" and not inst else "/nicht/da/mediamtx")
    mw = MW(datei, tmp, port_web)
    tx = None
    n_hook = len(Haken.got)
    try:
        mw.start()
        if inst:                                                     # «Install mediamtx» (the page asks first; here the API)
            s, d = mw.dev()
            pruef(s.get("rx", {}).get("art") == "ffmpeg", "vor dem Installieren: einfacher Empfänger (%s)" % s.get("rx", {}).get("art"))
            r = mw.api("/api/gopro", {"action": "install", "lang": "de"})
            pruef(bool(r.get("ok")), "Installieren gestartet (%s)" % r.get("error"))
            s, d = mw.warte(lambda s, d: not s.get("rx", {}).get("install", {}).get("running"), 240)
            msg = s.get("rx", {}).get("install", {}).get("msg", "")
            pruef("mediamtx installiert" in msg and "Liste des Releases" not in msg, "mediamtx installiert, Prüfsumme fest im Programm (%s)" % msg)
            exe = os.path.join(tmp, "mw", "gopro", "bin", "mediamtx")
            pruef(os.path.isfile(exe) and os.access(exe, os.X_OK), "Programm unter <Ordner>/gopro/bin/mediamtx")
            s, d = mw.warte(lambda s, d: s.get("rx", {}).get("art") == "mediamtx" and s["rx"].get("laeuft"), 30)
        s, d = mw.warte(lambda s, d: s.get("rx", {}).get("laeuft") and d.get("zustand") == "waiting", 40)
        pruef(s.get("rx", {}).get("art") == art and s["rx"].get("laeuft"), "%s: Empfänger läuft (%s, Port %s) %s" % (art, s.get("rx", {}).get("art"), port_rx, s.get("rx", {}).get("fehler") or ""))
        if s.get("rx", {}).get("art") != art:
            try:
                print(open(os.path.join(tmp, "mw", "gopro", "rx.log"), errors="replace").read()[-1500:])
            except OSError:
                pass
        pruef(d.get("zustand") == "waiting" and d.get("aktiv"), "%s: GoPro wartet (%s)" % (art, d.get("zustand")))
        pruef(d.get("start_qr") == "oW1mVr1080!W!GM", "%s: Start-Code auf der Seite (%s)" % (art, d.get("start_qr")))
        # unauthenticated
        try:
            urllib.request.build_opener(urllib.request.ProxyHandler({})).open(mw.base + "/api/gopro", timeout=10); code = 200
        except urllib.error.HTTPError as e:
            code = e.code
        pruef(code == 401, "%s: /api/gopro ohne Anmeldung abgelehnt (%s)" % (art, code))
        # the GoPro starts
        tx = gopro_senden(port_rx)
        s, d = mw.warte(lambda s, d: d.get("zustand") == "streaming", 60)
        pruef(d.get("zustand") == "streaming", "%s: Strom kommt an (%s)" % (art, d.get("zustand")))
        t_ = time.time() + 60; c = {}; mot = False
        while time.time() < t_:
            c = mw.cam()
            mot = mot or bool(c.get("motion"))
            if c.get("status") == "connected" and c.get("res") == "640x360" and mot:
                break
            time.sleep(0.5)
        pruef(c.get("status") == "connected" and c.get("res") == "640x360", "%s: Zusatzkamera «%s» verbunden, %s, %s fps" % (art, c.get("label"), c.get("res"), c.get("fps")))
        pruef(mot, "%s: Erkennung läuft (Bewegung im Testbild erkannt)" % art)
        jpg = b""
        if c.get("n") is not None:
            for _i in range(20):
                jpg = mw.api("/cam_snap/%s" % c["n"], raw=True)
                if jpg[:2] == b"\xff\xd8":
                    break
                time.sleep(0.5)
        pruef(jpg[:2] == b"\xff\xd8", "%s: Bild der GoPro über /cam_snap (%d Bytes)" % (art, len(jpg)))
        if bilder and jpg[:2] == b"\xff\xd8":
            open(os.path.join(bilder, "gopro_%s_bild.jpg" % art), "wb").write(jpg)
        # QR codes over the web = the Labs texts exactly
        svg = mw.api("/api/gopro/qr", {"id": GID, "art": "join", "ssid": "Camping", "pw": WLAN_PW, "lang": "de"}, raw=True)
        pruef(svg.decode(errors="replace") == ns["qr_svg"]('!MJOIN="Camping:' + WLAN_PW + '"'), "%s: WLAN-Code = !MJOIN=\"Camping:…\" (SVG gleich)" % art)
        svg = mw.api("/api/gopro/qr", {"id": GID, "art": "rtmp", "ip": "192.168.4.20", "lang": "de"}, raw=True)
        pruef(svg.decode(errors="replace") == ns["qr_svg"]('!MRTMP="rtmp://192.168.4.20:%d/gopro/%s-%s"' % (port_rx, GID, KEY)), "%s: Adress-Code = !MRTMP (SVG gleich)" % art)
        svg = mw.api("/api/gopro/qr", {"id": GID, "art": "start", "lang": "de"}, raw=True)
        pruef(svg.decode(errors="replace") == ns["qr_svg"]("oW1mVr1080!W!GM"), "%s: Start-Code = oW1mVr1080!W!GM (SVG gleich)" % art)
        r = mw.api("/api/gopro/qr", {"id": GID, "art": "join", "ssid": "a:b", "pw": WLAN_PW + "x", "lang": "de"})
        pruef(r.get("_code") == 400 and WLAN_PW not in json.dumps(r), "%s: falscher WLAN-Name abgelehnt, das Passwort nicht in der Antwort" % art)
        r = mw.api("/api/gopro", {"action": "set", "id": GID, "res": "1080", "copy": True, "lang": "de"})
        d = next((x for x in r.get("devs") or [] if x["id"] == GID), {})
        pruef(d.get("start_qr") == "oW1mVr1080!W!GLC", "%s: 1080p + Kopie -> Start-Code %s" % (art, d.get("start_qr")))
        mw.api("/api/gopro", {"action": "set", "id": GID, "res": "720", "copy": False, "lang": "de"})
        if browser and art == "ffmpeg":
            seite(mw, bilder, "streaming")
        # drop-out
        stopp(tx); tx = None
        s, d = mw.warte(lambda s, d: d.get("zustand") == "lost", 60)
        pruef(d.get("zustand") == "lost", "%s: Abbruch erkannt (%s)" % (art, d.get("zustand")))
        pruef("the live stream dropped out" in mw.log(), "%s: Abbruch im Protokoll" % art)
        t_ = time.time() + 20
        while time.time() < t_ and not [h for h in Haken.got[n_hook:] if h.get("event") == "info"]:
            time.sleep(0.5)
        inf = [h for h in Haken.got[n_hook:] if h.get("event") == "info"]
        pruef(bool(inf) and "GoPro" in json.dumps(inf, ensure_ascii=False) and not [h for h in Haken.got[n_hook:] if h.get("event") in ("person", "tamper")],
              "%s: stille Meldung (Webhook event info, kein Alarm): %s" % (art, (inf[0].get("text") if inf else "")[:90]))
        pruef(d.get("start_qr") == "oW1mVr1080!W!GM" and d.get("aktiv"), "%s: Start-Code wird wieder gezeigt (Seite: aktiv, nicht «streaming»)" % art)
        if browser and art == "ffmpeg":
            seite(mw, bilder, "abbruch")
        # again
        tx = gopro_senden(port_rx)
        s, d = mw.warte(lambda s, d: d.get("zustand") == "streaming", 60)
        pruef(d.get("zustand") == "streaming", "%s: Strom wieder da (%s)" % (art, d.get("zustand")))
        stopp(tx); tx = None
        if art == "ffmpeg":
            # restart: the GoPro stays, stopped / started
            mw.stop(); mw.start()
            s, d = mw.warte(lambda s, d: d.get("zustand") in ("waiting", "lost"), 40)
            pruef(d.get("name") == "Zelt" and d.get("aktiv"), "Neustart: GoPro noch da (%s)" % d.get("zustand"))
            r = mw.api("/api/gopro", {"action": "stop", "id": GID, "lang": "de"})
            d = next((x for x in r.get("devs") or [] if x["id"] == GID), {})
            pruef(d.get("zustand") == "stopped" and not d.get("aktiv") and not mw.cam(), "Stopp: aus den Kameras (%s)" % d.get("zustand"))
            r = mw.api("/api/gopro", {"action": "start", "id": GID, "lang": "de"})
            pruef(r.get("ok") and bool(mw.cam()), "Start: wieder Zusatzkamera")
            r = mw.api("/api/gopro", {"action": "add", "name": "Zwei", "modell": "hero8", "weg": "rtmp", "lang": "de"})
            pruef(r.get("ok") and len(r.get("devs") or []) == 2, "zweite GoPro hinzugefügt")
            s, d2 = mw.warte(lambda s, d: any("nur eine GoPro" in (x.get("fehler") or "") for x in s.get("devs") or []), 20)
            pruef(any("nur eine GoPro" in (x.get("fehler") or "") for x in s.get("devs") or []), "einfacher Empfänger: Hinweis «nur eine GoPro»")
    finally:
        stopp(tx)
        mw.stop()
        log = mw.log()
        if "Traceback (most recent call last)" in log:
            print(log[-3000:]); pruef(False, "%s: Traceback im Protokoll" % art)
        hits = []
        for wurzel, _d, files in os.walk(tmp):
            for fn in files:
                try:
                    if WLAN_PW.encode() in open(os.path.join(wurzel, fn), "rb").read():
                        hits.append(os.path.relpath(os.path.join(wurzel, fn), tmp))
                except OSError:
                    pass
        pruef(not hits, "%s: das WLAN-Passwort steht in keiner Datei des Ordners und nicht im Protokoll %s" % (art, hits))
        pruef(bool(log) and KEY not in log, "%s: der Strom-Schlüssel steht nicht im Protokoll" % art)
        shutil.rmtree(tmp, ignore_errors=True)


def seite(mw, bilder, was):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        for gname, vp, mob in [("handy", {"width": 390, "height": 844}, True), ("pc", {"width": 1280, "height": 900}, False)]:
            ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2,
                                 http_credentials={"username": "admin", "password": PASSWORT})
            pg = ctx.new_page()
            jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            pg.goto(mw.base + "/gopro", wait_until="domcontentloaded")
            ok = False
            for _w in range(40):
                ok = pg.evaluate("() => !!document.querySelector('.gp-card[data-id] .gp-chip')")
                if ok:
                    break
                pg.wait_for_timeout(400)
            pg.wait_for_timeout(1500)
            s = pg.evaluate("""() => { const c = document.querySelector('.gp-card[data-id]'); if (!c) return null;
                return {chip: c.querySelector('.gp-chip').textContent, qr: !!c.querySelector('.gp-qr svg'), code: (c.querySelector('.gp-code:last-of-type') || {}).textContent || '',
                        title: document.querySelector('h2').textContent, wide: document.documentElement.scrollWidth <= window.innerWidth + 1,
                        rx: document.getElementById('gp-rx').textContent, pw: !!c.querySelector('input[type=password]')}; }""")
            pruef(bool(s) and "GoPro hinzufügen" in s["title"] and s["pw"] and s["wide"], "%s %s: Seite /gopro deutsch, Passwort-Feld, passt in die Breite (%s)" % (gname, was, s and {k: s[k] for k in ("chip", "wide")}))
            if was == "streaming":
                pruef(bool(s) and "Bild kommt" in s["chip"] and not s["qr"], "%s: «Bild kommt», kein Start-Code (%s)" % (gname, s and s["chip"]))
            else:
                pruef(bool(s) and "abgebrochen" in s["chip"] and s["qr"], "%s: «Strom abgebrochen» + Start-Code als QR (%s)" % (gname, s and s["chip"]))
            if was == "streaming" and gname == "handy":                   # the Wi-Fi code only after the tap, password field emptied
                pg.fill('.gp-card[data-id] .gp-step input[type=text]', "Camping")
                pg.fill('.gp-card[data-id] input[type=password]', WLAN_PW)
                pg.click('.gp-card[data-id] .gp-step button')
                pg.wait_for_timeout(1500)
                w = pg.evaluate("""() => { const c = document.querySelector('.gp-card[data-id] .gp-step'); return {qr: !!c.querySelector('.gp-qr svg'),
                    pw: c.querySelector('input[type=password]').value, txt: c.textContent}; }""")
                pruef(w["qr"] and w["pw"] == "" and WLAN_PW not in w["txt"], "Handy: WLAN-Code erst nach Antippen, Passwort-Feld danach leer, Passwort nicht als Text (%s)" % {k: w[k] for k in ("qr",)})
                if bilder:
                    pg.locator('.gp-card[data-id] .gp-step').first.screenshot(path=os.path.join(bilder, "gopro_handy_wlan_code.png"))
            if bilder:
                pg.screenshot(path=os.path.join(bilder, "gopro_%s_%s.png" % (gname, was)), full_page=True)
            if was == "streaming":
                pg.goto(mw.base + "/cams", wait_until="domcontentloaded")
                pg.wait_for_timeout(2500)
                b = pg.evaluate("() => { const b = document.getElementById('gp-link'); return b ? b.textContent : null; }")
                pruef(b is not None and "GoPro hinzufügen" in b, "%s: Kameras-Seite hat «📹 GoPro hinzufügen» (%s)" % (gname, b))
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, "gopro_%s_kameras.png" % gname), full_page=True)
            pruef(not jsf, "%s %s: keine JavaScript-Fehler %s" % (gname, was, jsf[:3]))
            ctx.close()
        br.close()


def main():
    ap = argparse.ArgumentParser(description="GoPro als Zusatzkamera")
    ap.add_argument("--datei", default="")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--mtx", default="", help="Pfad zu mediamtx (sonst PATH, Zwischenspeicher, oder von GitHub)")
    ap.add_argument("--mtx-pflicht", action="store_true", help="ohne mediamtx rot statt übersprungen (CI)")
    ap.add_argument("--mtx-pruefsummen", action="store_true")
    ap.add_argument("--ohne-browser", action="store_true")
    a = ap.parse_args()
    if a.mtx_pruefsummen:
        return pruefsummen()
    if not shutil.which("ffmpeg"):
        print("ffmpeg fehlt"); return 1
    datei = os.path.abspath(a.datei) if a.datei else neueste_datei()
    if a.bilder:
        os.makedirs(a.bilder, exist_ok=True)
    ns = teil_a(datei)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Haken)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    hook = "http://127.0.0.1:%d/hook" % srv.server_address[1]
    try:
        lauf(datei, "ffmpeg", "", ns, hook, a.bilder, not a.ohne_browser)
        mtx = a.mtx or os.environ.get("MW_MEDIAMTX") or ""
        if not mtx and github_da():
            mtx = "INSTALL"                                          # MoveEye installs it itself (button, fixed checksum)
        if not mtx:
            try:
                mtx = mtx_holen(os.path.join(os.path.expanduser("~"), ".cache", "moveeye", "mediamtx-" + MTX_VERSION))
            except Exception as e:                                   # noqa: BLE001
                print("  mediamtx nicht geholt: %s: %s" % (type(e).__name__, e))
        if mtx:
            lauf(datei, "mediamtx", mtx, ns, hook, a.bilder, False)
        elif a.mtx_pflicht:
            pruef(False, "mediamtx fehlt (--mtx-pflicht)")
        else:
            print("  übersprungen: Teil C (mediamtx nicht da)")
    finally:
        srv.shutdown()
    print("GoPro-Test " + ("OK" if not FEHLER else "FEHLGESCHLAGEN (%d)" % len(FEHLER)))
    for f in FEHLER:
        print("   - " + f)
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
