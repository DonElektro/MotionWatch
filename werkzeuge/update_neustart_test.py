#!/usr/bin/env python3
"""Update und Neustart: kommt die Webseite nach dem Update wieder? (Besitzer 13.11.2026: «Seit den letzten zwei Updates ist
die Homepage nach dem Update nicht mehr erreichbar … bis ich den Raspberry neu starte» - Ping ging, kein Port von MoveEye offen.)

  python3 werkzeuge/update_neustart_test.py [--datei NEU.py] [--alt ALT.py] [--limit 90] [--nur A,B,C,D,E]

Jeder Fall in einem eigenen Daten-Ordner, auf einem freien Port, ohne Fenster (--headless --boot wie der Autostart-Dienst).
Ein kleiner «Aufpasser» startet MoveEye nach jedem Ende neu wie systemd (Restart=always, RestartSec=5 - hier 2 s).
  A  echtes Update über die Web-Schnittstelle (/api/update «install», wie die Taste «Update»): die ALTE Version (die Datei
     vor --datei im Repository) installiert --datei aus einem Ordner (USB-Weg, unsigniert erlaubt) und startet sich selbst
     neu (os.execv, gleiche PID). Die neue Version muss innerhalb von --limit Sekunden antworten. Dabei hält ein Browser
     das Live-Bild offen (wie das Handy, das «Update» getippt hat).
  B  nach dem Neustart hält ein übrig gebliebenes Kind-Programm den Web-Port (es hat die Steckdose geerbt; nach os.execv
     bleibt es ein Kind von MoveEye): MoveEye findet es, beendet es und die Seite kommt (vorher: Warten ohne Ende).
  C  MoveEye ist selbst der Autostart-Dienst (nachgebautes systemctl: «is-active» = active, MainPID = MoveEye) und der Port
     ist kurz belegt: MoveEye darf den Dienst NICHT stoppen (vorher: «systemctl stop motionwatch» - sich selbst, und ein
     gestoppter Dienst startet nicht mehr: Seite weg bis zum Neustart des Pi). Seite kommt, sobald der Port frei ist.
  D  Start-Wächter: die Seite kommt nicht (Port bleibt belegt) - MoveEye schreibt start_hang.txt und endet mit Code 1, der
     Aufpasser startet neu, der nächste Start meldet «The last start hung» im Protokoll; Port frei -> Seite kommt.
  E  vor os.execv hört eine geteilte Steckdose (auch in einem Kind-Programm) auf zu lauschen (_close_fds_on_exec, 390).
"""
import argparse
import base64
import glob
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
PW = "Neustart-Test-1234"
AUTH = "Basic " + base64.b64encode(("admin:" + PW).encode()).decode()
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def ok(bed, text):
    print(("  ok   " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


def vkey(p):
    return [int(x) for x in re.findall(r"\d+", os.path.basename(p))]


def zip_zu(py):
    z = os.path.join(os.path.dirname(py), "moveeye_daten_" + os.path.basename(py)[len("webcam_bewegung_"):-3] + ".zip")
    return z if os.path.isfile(z) else ""


def frei_port():
    """ein Port p, bei dem p, p+1 und p+2 frei sind (Web, https, Spiele)"""
    for _ in range(50):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]
        if p > 60000:
            continue
        try:
            for q in (p, p + 1, p + 2):
                with socket.socket() as s:
                    s.bind(("127.0.0.1", q))
            return p
        except OSError:
            continue
    raise SystemExit("kein freier Port")


def holen(port, pfad="/api/update", timeout=4):
    try:
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, pfad), headers={"Authorization": AUTH})
        with OP.open(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return -1, repr(e).encode()


def version_da(port):
    c, b = holen(port)
    if c != 200:
        return ""
    try:
        return json.loads(b).get("current") or ""
    except ValueError:
        return ""


def warten(port, limit, version=None):
    t0 = time.time()
    while time.time() - t0 < limit:
        v = version_da(port)
        if v and (version is None or v == version):
            return round(time.time() - t0, 1)
        time.sleep(0.5)
    return None


class Fall:
    """ein Daten-Ordner, ein Port, MoveEye unter einem Aufpasser (Restart=always)"""
    def __init__(self, name, prog, extra_files=(), env=None, wrapper=None, cfg_extra=None):
        self.tmp = tempfile.mkdtemp(prefix="mw_neustart_%s_" % name)
        self.app = os.path.join(self.tmp, "app"); self.cfg = os.path.join(self.tmp, "mw")
        os.makedirs(self.app); os.makedirs(self.cfg)
        for f in [prog, zip_zu(prog)] + list(extra_files):
            if f:
                shutil.copy(f, self.app)
        self.port = frei_port()
        st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
              "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
              "setup_done": True, "https_extra": False, "autostart": False}
        st.update(cfg_extra or {})
        with open(os.path.join(self.cfg, "motionwatch_settings.json"), "w") as f:
            json.dump({"cfg": st}, f)
        self.env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
        self.env.update(MOTIONWATCH_HOME=self.tmp, NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost",
                        PYTHONUNBUFFERED="1")
        self.env.update(env or {})
        self.cmd = [os.path.join(self.app, os.path.basename(prog)), "--headless", "--boot", "--port", str(self.port),
                    "--bind", "127.0.0.1", "--config", self.cfg, "--web-password", PW]
        self.wrapper = wrapper
        self.procs = []; self.ends = []; self.stop = False
        self.out = open(os.path.join(self.tmp, "ausgabe.txt"), "w")

    def start(self):
        threading.Thread(target=self._aufpasser, daemon=True).start()
        return self

    def _aufpasser(self):
        erst = True
        while not self.stop:
            pre = list(self.wrapper) if (self.wrapper and erst) else []
            p = subprocess.Popen([sys.executable] + pre + self.cmd, stdout=self.out, stderr=subprocess.STDOUT, cwd=self.app,
                                 env=self.env, start_new_session=True)
            self.procs.append(p); erst = False
            rc = p.wait()
            self.ends.append((time.time(), rc))
            if self.stop:
                break
            time.sleep(2)

    def log(self):
        p = os.path.join(self.cfg, "motionwatch.log")
        return open(p, errors="replace").read() if os.path.isfile(p) else ""

    def ausgabe(self):
        self.out.flush()
        return open(os.path.join(self.tmp, "ausgabe.txt"), errors="replace").read()

    def ende(self, zeigen=False):
        self.stop = True
        for p in self.procs:
            if p.poll() is None:
                try:
                    os.killpg(p.pid, signal.SIGTERM)         # with the children it started (own session)
                except OSError:
                    pass
                try:
                    p.wait(15)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
        if zeigen:
            print("---- motionwatch.log\n" + self.log()[-2500:] + "\n---- Ausgabe\n" + self.ausgabe()[-2500:])
        self.out.close()
        shutil.rmtree(self.tmp, ignore_errors=True)


def halter(port):
    """eine fremde Steckdose, die den Port belegt (lauscht)"""
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port)); s.listen(5)
    return s


def fake_systemctl(ordner):
    """systemctl zum Nachbauen: der Dienst läuft («active») und sein Hauptprogramm ist der Aufrufer (= MoveEye); jeder Aufruf
    landet in systemctl.log, nichts wird wirklich gestartet oder gestoppt"""
    b = os.path.join(ordner, "bin"); os.makedirs(b, exist_ok=True)
    log = os.path.join(ordner, "systemctl.log")
    with open(os.path.join(b, "systemctl"), "w") as f:
        f.write('#!/bin/sh\necho "systemctl $*" >> "%s"\ncase "$*" in\n  *is-active*) echo active;;\n  *is-enabled*) echo enabled;;\n'
                '  *MainPID*) echo "$PPID";;\nesac\nexit 0\n' % log)
    os.chmod(os.path.join(b, "systemctl"), 0o755)
    return b, log


WRAPPER = r'''
import os, socket, subprocess, sys
port = int(sys.argv[1])
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", port)); s.listen(5)
c = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(900)"], pass_fds=[s.fileno()])
open(sys.argv[2], "w").write(str(c.pid))
s.close()
os.execv(sys.executable, [sys.executable] + sys.argv[3:])      # like the update: same PID, the child stays ours
'''


def fall_a(neu, alt, limit):
    print("A  Update über die Web-Schnittstelle: %s -> %s" % (os.path.basename(alt), os.path.basename(neu)))
    quelle = tempfile.mkdtemp(prefix="mw_neustart_quelle_")
    for f in (neu, zip_zu(neu)):
        shutil.copy(f, quelle)
    f_ = Fall("a", alt, cfg_extra={"update_url": quelle, "update_unsigned": True, "update_unsigned_t": time.time()}).start()
    try:
        t = warten(f_.port, 240)
        ok(t is not None, "alte Version antwortet (%s s)" % t)
        if t is None:
            return
        v_neu = None
        c, b = holen(f_.port)
        j = json.loads(b) if c == 200 else {}
        v_neu = (j.get("newer") or [None])[-1]
        ok(bool(v_neu), "die neue Version steht in der Liste (%s)" % v_neu)
        if not v_neu:
            return
        k = socket.create_connection(("127.0.0.1", f_.port), timeout=5)      # the phone keeps the live picture open
        k.sendall(("GET /video_feed HTTP/1.1\r\nHost: x\r\nAuthorization: %s\r\n\r\n" % AUTH).encode())
        req = urllib.request.Request("http://127.0.0.1:%d/api/update" % f_.port, method="POST",
                                     data=json.dumps({"action": "install", "version": v_neu}).encode(),
                                     headers={"Authorization": AUTH, "Content-Type": "application/json"})
        try:
            with OP.open(req, timeout=180) as r:
                ans = json.loads(r.read())
        except urllib.error.HTTPError as e:
            ans = {"ok": False, "error": "HTTP %d %s" % (e.code, e.read()[:200])}
        ok(ans.get("ok"), "«Update» angenommen (%s)" % (ans.get("error") or "ok"))
        t = warten(f_.port, limit, v_neu)
        ok(t is not None, "neue Version %s antwortet nach dem Update in %s s (Grenze %d s)" % (v_neu, t, limit))
        ok(len(f_.procs) == 1 and f_.procs[0].poll() is None, "derselbe Prozess (os.execv), kein Absturz (Neustarts: %d)" % (len(f_.procs) - 1))
        k.close()
        if t is None:
            f_.ende(zeigen=True); return
    finally:
        if not f_.stop:
            f_.ende()
        shutil.rmtree(quelle, ignore_errors=True)


def fall_b(neu, limit):
    print("B  ein übrig gebliebenes Kind hält den Web-Port (wie nach os.execv)")
    tmpw = tempfile.mkdtemp(prefix="mw_neustart_w_")
    w = os.path.join(tmpw, "wrapper.py"); open(w, "w").write(WRAPPER)
    kidf = os.path.join(tmpw, "kind.pid")
    f_ = Fall("b", neu)
    f_.wrapper = [w, str(f_.port), kidf]      # the wrapper takes the port, leaves a child with it and execs MoveEye
    f_.start()
    kid = 0
    try:
        t = warten(f_.port, limit)
        kid = int(open(kidf).read()) if os.path.isfile(kidf) else 0
        ok(t is not None, "Seite antwortet trotz belegtem Port in %s s (Grenze %d s)" % (t, limit))
        ok(kid and not _lebt(kid), "das Kind-Programm (PID %s), das den Port hielt, ist beendet" % kid)
        ok("own child, stopped" in f_.log(), "Protokoll nennt den Halter des Ports («own child, stopped»)")
        if t is None:
            f_.ende(zeigen=True)
    finally:
        if kid and _lebt(kid):
            try:
                os.kill(kid, signal.SIGKILL)
            except OSError:
                pass
        if not f_.stop:
            f_.ende()
        shutil.rmtree(tmpw, ignore_errors=True)


def _lebt(pid):
    if not pid:
        return False
    try:
        with open("/proc/%d/stat" % pid) as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


def fall_c(neu, limit):
    print("C  MoveEye ist der Autostart-Dienst, der Port ist 10 s belegt: kein «systemctl stop» von sich selbst")
    tmpb = tempfile.mkdtemp(prefix="mw_neustart_c_")
    b, slog = fake_systemctl(tmpb)
    f_ = Fall("c", neu, env={"PATH": b + os.pathsep + os.environ.get("PATH", "")})
    h = halter(f_.port)                                       # the port is busy BEFORE MoveEye starts
    f_.start()
    try:
        time.sleep(10)
        h.close()
        t = warten(f_.port, limit)
        calls = open(slog).read() if os.path.isfile(slog) else ""
        ok(t is not None, "Seite antwortet, nachdem der Port frei ist (%s s, Grenze %d s)" % (t, limit))
        ok(" stop " not in calls + " ", "kein «systemctl stop» (Aufrufe: %s)" % " / ".join(calls.strip().splitlines())[:300])
        ok("this program is the autostart service" in f_.log(), "Protokoll: «Port … busy at the start (this program is the autostart service)»")
        ok(len(f_.procs) == 1, "kein Neustart nötig (%d Starts)" % len(f_.procs))
        if t is None:
            f_.ende(zeigen=True)
    finally:
        if not f_.stop:
            f_.ende()
        shutil.rmtree(tmpb, ignore_errors=True)


def fall_d(neu, limit):
    print("D  Start-Wächter: die Seite kommt nicht -> start_hang.txt, Ende mit Code 1, neuer Start")
    tmpb = tempfile.mkdtemp(prefix="mw_neustart_d_")
    b, slog = fake_systemctl(tmpb)
    f_ = Fall("d", neu, env={"PATH": b + os.pathsep + os.environ.get("PATH", ""), "MW_START_WD": "8"})
    h = halter(f_.port)
    f_.start()
    try:
        t0 = time.time()
        while time.time() - t0 < limit and not f_.ends:
            time.sleep(0.5)
        rc = f_.ends[0][1] if f_.ends else None
        ok(rc == 1, "MoveEye endet von selbst mit Code 1 (nach %.0f s, Wächter 8 s; Code %s)" % (time.time() - t0, rc))
        hang = os.path.join(f_.cfg, "start_hang.txt")
        txt = open(hang, errors="replace").read() if os.path.isfile(hang) else ""
        ok("Thread" in txt or "File" in txt, "start_hang.txt mit den Threads geschrieben (%d Zeichen)" % len(txt))
        h.close()
        t = warten(f_.port, limit)
        ok(t is not None, "nach dem neuen Start antwortet die Seite (%s s)" % t)
        ok("The last start hung" in f_.log(), "Protokoll: «The last start hung …»")
        if t is None:
            f_.ende(zeigen=True)
    finally:
        try:
            h.close()
        except OSError:
            pass
        if not f_.stop:
            f_.ende()
        shutil.rmtree(tmpb, ignore_errors=True)


PRUEF_E = r'''
import json, os, socket, sys, time
ns = {"__name__": "mw_neustart", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", 0)); s.listen(5)
port = s.getsockname()[1]
pid = os.fork()
if pid == 0:                                    # a child with a copy of the listening socket
    time.sleep(30); os._exit(0)
ns["_close_fds_on_exec"]()
t = socket.socket(); t.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    t.bind(("127.0.0.1", port)); t.listen(1); free = True
except OSError:
    free = False
os.kill(pid, 9); os.waitpid(pid, 0)
print("RES " + json.dumps({"free": free}))
'''


def fall_e(neu):
    print("E  vor os.execv: eine geteilte Steckdose hört überall auf zu lauschen")
    home = tempfile.mkdtemp(prefix="mw_neustart_e_")
    env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
    env["MOTIONWATCH_HOME"] = home
    r = subprocess.run([sys.executable, "-c", PRUEF_E, neu], capture_output=True, text=True, env=env, timeout=180,
                       cwd=os.path.dirname(neu))
    res = next((json.loads(x[4:]) for x in r.stdout.splitlines() if x.startswith("RES ")), None)
    if res is None:
        print((r.stdout + r.stderr)[-2000:])
    ok(bool(res and res["free"]), "Port frei, obwohl ein Kind die Steckdose noch hat (_close_fds_on_exec)")
    shutil.rmtree(home, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datei", default="", help="neue Version (Standard: neueste webcam_bewegung_*.py im Repository)")
    ap.add_argument("--alt", default="", help="alte Version für A (Standard: die Datei davor im Repository)")
    ap.add_argument("--limit", type=int, default=90, help="Sekunden, bis die Seite antworten muss (Spielraum für langsame Rechner)")
    ap.add_argument("--nur", default="A,B,C,D,E")
    a = ap.parse_args()
    if not sys.platform.startswith("linux"):
        print("nur unter Linux (/proc, wie der Pi)"); return 0
    progs = sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*_*_*.py")), key=vkey)
    neu = os.path.abspath(a.datei or progs[-1])
    alt = os.path.abspath(a.alt) if a.alt else next((p for p in reversed(progs) if vkey(p) < vkey(neu) and zip_zu(p)), "")
    if not zip_zu(neu):
        print("Zusatzdatei zu %s fehlt" % neu); return 1
    nur = set(a.nur.upper().split(","))
    print("Neu: %s · alt: %s · Grenze %d s" % (os.path.basename(neu), os.path.basename(alt) or "-", a.limit))
    if "E" in nur:
        fall_e(neu)
    if "A" in nur:
        if alt:
            fall_a(neu, alt, a.limit)
        else:
            ok(False, "A: keine ältere Version mit Zusatzdatei im Repository")
    if "B" in nur:
        fall_b(neu, a.limit)
    if "C" in nur:
        fall_c(neu, a.limit)
    if "D" in nur:
        fall_d(neu, a.limit)
    print("FEHLER: %d" % len(FEHLER) if FEHLER else "Alles gut.")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
