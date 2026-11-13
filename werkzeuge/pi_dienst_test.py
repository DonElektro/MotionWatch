#!/usr/bin/env python3
"""MoveEye als echter systemd-Dienst wie auf dem Pi des Besitzers (Benutzer-Dienst ~/.config/systemd/user/motionwatch.service,
eingeschaltet, Restart=always, WatchdogSec=120, «linger») - mit dem echten systemd, nicht mit einem nachgebauten systemctl.

  sudo python3 werkzeuge/pi_dienst_test.py --ci                 # im CI (GitHub, Ubuntu-VM): legt den Test-Benutzer an
  sudo python3 werkzeuge/pi_dienst_test.py [--datei NEU.py] [--alt ALT.py] [--nur a,b,c,d,e,f,g] [--limit 60]

Anlass (Besitzer 13.11.2026): nach dem Update startete das NEUE Programm (gleiche PID nach os.execv = Hauptprozess des Dienstes),
fand den Web-Port kurz belegt und rief «systemctl --user stop motionwatch.service» - es stoppte sich selbst; Seite weg bis zum
Neustart des Pi. Alle 45 CI-Jobs liefen ohne systemd und sahen es nicht.

Läuft als root (legt mit --ci den Test-Benutzer «mwtest» an, schaltet «linger» ein = eigener systemd --user wie auf dem Pi,
und braucht root für die System-Variante g). MoveEye selbst läuft immer als der Test-Benutzer, Daten im Pi-Ordner
~/.config/motionwatch, Programm in ~/MoveEye (wie werkzeuge/einrichten.sh), Kamera «sim:0» (Simulator, nicht erreichbar).
Eingerichtet wird wie auf dem Pi: MoveEye von Hand starten, auf der Webseite «Autostart» einschalten (/api/autostart -> Teil 140
autostart_set: derselbe Erzeuger der Unit-Datei), Hand-Programm beenden, Dienst starten (= Pi einschalten).
Update-Quelle: lokaler HTTPS-Server mit eigenem Zertifikat und Wegwerf-Schlüssel (wie update_uebergang_test.py), signiert.

  a  kalter Start: Seite antwortet, Dienst «active», Hauptprozess = MoveEye, systemd bekommt «WATCHDOG=1»
  d  kill -9 des Hauptprozesses: systemd startet neu (neue PID, Seite kommt) - «systemctl stop» (SIGTERM): bleibt aus
  e  Stromausfall: alles hart beendet (SIGKILL), alte Sperr-Datei, halb geschriebene Einstellungen / Update-Datei liegen
     herum -> sauberer Start, Einstellungen aus der Sicherung, kein Neustart-Kreis
  f  Start-Wächter (140): Start hängt (Port von einer hängenden alten MoveEye desselben Benutzers belegt) -> Ende mit Code 1, systemd startet neu,
     start_hang.txt mit den Threads; Port frei -> Seite kommt
  f2 ein Programm eines anderen Benutzers hält den Port (3.87.1): kein Ende, der Dienst bewacht weiter, die Seite kommt danach
  b  Update in der App (ALT -> NEU, /api/update «install» wie die Taste «Update»), dabei hält ein Hilfsprogramm, das das alte
     Programm gestartet hat, eine Kopie der Web-Steckdose (werkzeug macht sie vererbbar - ein Hilfsprogramm, das ohne
     close_fds gestartet wird, behält sie): beim Start des neuen Programms ist der Port kurz belegt, wie am 13.11. auf dem Pi.
     Seite mit NEU innerhalb --limit s, derselbe Dienst (InvocationID, MainPID), «active», kein «Stopping motionwatch.service»,
     die Unit zeigt auf die neue Datei (autostart_follow_version)
  c  gleich danach das zweite Update (NEU -> NEU+1, aus quelle/ gebaut) bei offenem Live-Bild: Live-Bild endet, Seite kommt,
     Live-Bild geht wieder
  g  System-Dienst /etc/systemd/system/motionwatch.service (sudo … --install-service wie einrichten.sh): a + b + Neustart
     des Pi (systemctl restart): welche Version kommt? (nur mit dem System-systemd: auf GitHub, nicht im lokalen Namensraum)

Reihenfolge: a, d, e, f mit NEU; dann ALT von Hand gestartet (der Dienst folgt der Hand-Version), b, c; zuletzt g.
"""
import argparse
import base64
import glob
import json
import os
import pwd
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
sys.path.insert(0, HIER)
import update_uebergang_test as UU          # noqa: E402 (certificate, HTTPS server, throwaway key - the same as there)

FEHLER, HINWEISE, ZEITEN = [], [], []
PW = "Pi-Dienst-Test-4711"
AUTH = "Basic " + base64.b64encode(("admin:" + PW).encode()).decode()
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
UNIT = "motionwatch.service"
GH = bool(os.environ.get("GITHUB_ACTIONS"))


def ok(bed, text):
    print(("  ok      " if bed else "  FEHLER  ") + text, flush=True)
    if not bed:
        FEHLER.append(text)
        if GH:
            print("::error title=Pi-Dienst::" + text[:240], flush=True)
    return bed


def hinweis(text):
    print("  HINWEIS " + text, flush=True)
    HINWEISE.append(text)
    if GH:
        print("::warning title=Pi-Dienst::" + text[:240], flush=True)


def warte(bed, limit, schritt=0.5):
    """bis bed() wahr ist -> Sekunden (eine Stelle), sonst None"""
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            if bed():
                return round(time.time() - t0, 1)
        except Exception:
            pass
        time.sleep(schritt)
    return None


def vkey(p):
    return tuple(int(x) for x in re.findall(r"\d+", os.path.basename(p))[-3:])


def zip_zu(py):
    z = os.path.join(os.path.dirname(py), "moveeye_daten_" + os.path.basename(py)[len("webcam_bewegung_"):-3] + ".zip")
    return z if os.path.isfile(z) else ""


def frei_port():
    """ein Port p mit p, p+1 (https) und p+2 (Spiele) frei, auf 0.0.0.0 wie auf dem Pi"""
    for _ in range(80):
        with socket.socket() as s:
            s.bind(("0.0.0.0", 0)); p = s.getsockname()[1]
        if p > 60000:
            continue
        try:
            for q in (p, p + 1, p + 2):
                with socket.socket() as s:
                    s.bind(("0.0.0.0", q))
            return p
        except OSError:
            continue
    raise SystemExit("kein freier Port")


# ---------------------------------------------------------------------------------------------------------- Test-Benutzer
class Benutzer:
    def __init__(self, name, python):
        pw_ = pwd.getpwnam(name)
        self.name, self.uid, self.gid, self.home = name, pw_.pw_uid, pw_.pw_gid, pw_.pw_dir
        self.py = python
        self.run = "/run/user/%d" % self.uid
        self.app = os.path.join(self.home, "MoveEye")
        self.daten = os.path.join(self.home, ".config", "motionwatch")
        self.ci = os.path.join(self.home, "mw_ci")

    def env(self, extra=None):
        e = {"HOME": self.home, "USER": self.name, "LOGNAME": self.name, "XDG_RUNTIME_DIR": self.run, "LANG": "C.UTF-8",
             "PATH": os.path.dirname(self.py) + ":/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
             "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"}
        if os.path.exists(os.path.join(self.run, "bus")):
            e["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=%s/bus" % self.run
        e.update(extra or {})
        return e

    def cmd(self, args, extra=None):
        e = self.env(extra)
        return ["runuser", "-u", self.name, "--", "env", "-i"] + ["%s=%s" % kv for kv in e.items()] + list(args)

    def als(self, args, extra=None, timeout=60):
        try:
            r = subprocess.run(self.cmd(args, extra), capture_output=True, text=True, timeout=timeout, cwd=self.home)
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        except subprocess.TimeoutExpired:
            return -9, "", "Zeitlimit %d s: %s" % (timeout, " ".join(args))

    def gehoert(self, *pfade):
        for p in pfade:
            os.chown(p, self.uid, self.gid)


class Dienst:
    """systemctl für den Benutzer-Dienst (--user, als Test-Benutzer) oder den System-Dienst (root)"""
    def __init__(self, b, modus="user"):
        self.b, self.modus = b, modus

    def sctl(self, *args, timeout=60):
        if self.modus == "user":
            return self.b.als(["systemctl", "--user"] + list(args), timeout=timeout)
        r = subprocess.run(["systemctl"] + list(args), capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()

    def zeig(self):
        _rc, out, _e = self.sctl("show", UNIT, "-p", "ActiveState,SubState,MainPID,NRestarts,InvocationID,ExecMainStatus,"
                                 "WatchdogTimestampMonotonic,NeedDaemonReload,Result,FragmentPath,UnitFileState")
        d = dict(x.split("=", 1) for x in out.splitlines() if "=" in x)
        d["MainPID"] = int(d.get("MainPID") or 0)
        d["NRestarts"] = int(d.get("NRestarts") or 0)
        return d

    def journal(self, seit):
        """Zeilen des Dienst-Verwalters und von MoveEye seit `seit` (root liest das Journal; lokal ohne journald: "")"""
        if self.modus == "user":
            a = ["journalctl", "--no-pager", "-o", "short-precise", "_UID=%d" % self.b.uid, "--since", "@%d" % int(seit)]
        else:
            a = ["journalctl", "--no-pager", "-o", "short-precise", "-u", UNIT, "--since", "@%d" % int(seit)]
        try:
            r = subprocess.run(a, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if r.returncode != 0 or "No journal files" in r.stdout + r.stderr:
            return None
        return r.stdout


# ---------------------------------------------------------------------------------------------------------- Web
def holen(port, pfad="/api/update", timeout=4, daten=None):
    try:
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, pfad), headers={"Authorization": AUTH, "Content-Type": "application/json"},
                                     data=json.dumps(daten).encode() if daten is not None else None,
                                     method="POST" if daten is not None else "GET")
        with OP.open(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400]
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


def web_aus(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return False
    except OSError:
        return True


def lauscher(port):
    """wer auf dem Port lauscht: [(pid, kommando)] (für die Fehlermeldung)"""
    try:
        r = subprocess.run(["ss", "-ltnpH", "sport = :%d" % port], capture_output=True, text=True, timeout=10)
        return r.stdout.strip()[:400]
    except (OSError, subprocess.TimeoutExpired):
        return "?"


class LiveBild:
    """hält /video_feed offen wie das Handy; liest im Hintergrund, merkt sich Bytes und das Ende"""
    def __init__(self, port):
        self.n, self.ende = 0, None
        self.s = socket.create_connection(("127.0.0.1", port), timeout=10)
        self.s.sendall(("GET /video_feed HTTP/1.1\r\nHost: x\r\nAuthorization: %s\r\n\r\n" % AUTH).encode())
        threading.Thread(target=self._lesen, daemon=True).start()

    def _lesen(self):
        self.s.settimeout(300)
        try:
            while True:
                d = self.s.recv(65536)
                if not d:
                    break
                self.n += len(d)
        except OSError:
            pass
        self.ende = time.time()

    def zu(self):
        try:
            self.s.close()
        except OSError:
            pass


# ---------------------------------------------------------------------------------------------------------- Einrichten
LECK = r'''# sitecustomize nur für den CI-Test werkzeuge/pi_dienst_test.py (Fall b): einmal nach dem Start des Webservers startet
# MoveEye «ein Hilfsprogramm» ohne close_fds (wie es eine Bibliothek tun kann) - es erbt die vererbbare Web-Steckdose
# von werkzeug und hält den Port, auch nachdem das Programm sich beim Update durch os.execv ersetzt hat.
import os, sys, threading, time, socket, subprocess
_m = os.environ.get("MW_CI_LECK", "")
if _m and any("webcam_bewegung_" in a for a in sys.argv) and not os.path.exists(_m):
    def _leck():
        port = int(sys.argv[sys.argv.index("--port") + 1])
        for _ in range(600):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=1).close()
                break
            except OSError:
                time.sleep(0.5)
        time.sleep(2.0)
        if os.path.exists(_m):
            return
        p = subprocess.Popen(["sleep", "900"], close_fds=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        open(_m, "w").write(str(p.pid))
    threading.Thread(target=_leck, daemon=True, name="ci-leck").start()
'''


def einstellungen(b, url, extra=None):
    """Einstellungen wie ein eingerichteter Pi (Kamera = Simulator, nicht erreichbar); Update-Quelle = der Test-Server"""
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
          "sim_autostart_v2": True, "sim_autoupd": False, "update_url": url, "update_mode": "off", "lang": "de",
          "setup_done": True, "dev_phase_done": True}
    st.update(extra or {})
    os.makedirs(b.daten, exist_ok=True)
    p = os.path.join(b.daten, "motionwatch_settings.json")
    with open(p, "w") as f:
        json.dump({"cfg": st}, f)
    for x in (os.path.join(b.home, ".config"), b.daten, p):
        b.gehoert(x)


def bauen_plus1(neu, ziel_dir):
    """NEU+1 aus quelle/ bauen (bauen.py in einer Kopie, wie update_uebergang_test.py) -> (py, zip) oder ("", "")"""
    x, y, z = vkey(neu)
    v = "%d.%d.%d" % (x, y, z + 1)
    bau = os.path.join(ziel_dir, "bau")
    shutil.copytree(os.path.join(REPO, "quelle"), os.path.join(bau, "quelle"))
    os.makedirs(os.path.join(bau, "werkzeuge")); os.makedirs(os.path.join(bau, "simulator3d"))
    shutil.copy(os.path.join(HIER, "bauen.py"), os.path.join(bau, "werkzeuge"))
    for fn in ("ui_gemeinsam.json", "fehler_katalog.json", "version.json"):
        shutil.copy(os.path.join(REPO, "simulator3d", fn), os.path.join(bau, "simulator3d"))
    r = subprocess.run([sys.executable, os.path.join(bau, "werkzeuge", "bauen.py"), "--neue-version", "CI Pi-Dienst", "--version", v],
                       capture_output=True, text=True, cwd=bau, timeout=600)
    u = v.replace(".", "_")
    py, zp = os.path.join(bau, "webcam_bewegung_%s.py" % u), os.path.join(bau, "moveeye_daten_%s.zip" % u)
    if r.returncode != 0 or not (os.path.isfile(py) and os.path.isfile(zp)):
        print((r.stdout + r.stderr)[-2000:])
        return "", ""
    shutil.rmtree(os.path.join(bau, "quelle"), ignore_errors=True)
    return py, zp


class Lauf:
    """alles, was ein Lauf braucht: Benutzer, Dienst, Port, Update-Server, die drei Versionen"""
    def __init__(self, a, b, tmp):
        self.a, self.b, self.tmp = a, b, tmp
        self.d = Dienst(b, "user")
        self.port = frei_port()
        self.hand = None
        self.t0 = time.time()

    # -- program files in ~/MoveEye (with the throwaway public key), update server with versions.json
    def dateien(self, alt, neu, plus1):
        b = self.b
        for d in (b.app, b.ci):
            os.makedirs(d, exist_ok=True); b.gehoert(d)
        self.key = os.path.join(self.tmp, "test_schluessel.txt")
        open(self.key, "w").write(os.urandom(32).hex())
        res = UU.py(neu, 'ns["_ED"].extend(ns["_ed25519_impl"]())\n'
                    'print("RES " + json.dumps(ns["_ED"][0](bytes.fromhex(open(sys.argv[2]).read().strip())).hex()))',
                    os.path.join(self.tmp, "h0"), {}, self.key)
        self.pub = res if isinstance(res, str) else ""
        if not ok(len(self.pub) == 64 and self.pub != UU.ECHT_PUB, "Wegwerf-Schlüssel erzeugt (nicht der echte)"):
            return False
        self.srv_dir = os.path.join(self.tmp, "server"); os.makedirs(self.srv_dir)
        self.prog = {}
        for name, p in (("alt", alt), ("neu", neu), ("plus1", plus1)):
            for f in (p, zip_zu(p)):
                shutil.copy(f, self.srv_dir)
            UU.pub_setzen(os.path.join(self.srv_dir, os.path.basename(p)), self.pub)
            self.prog[name] = os.path.basename(p)
        self.ver = {k: UU.version_von(os.path.join(self.srv_dir, v)) for k, v in self.prog.items()}
        cp, kp = UU.zertifikat(self.tmp)
        self.cert = os.path.join(b.ci, "update_ca.pem"); shutil.copy(cp, self.cert); b.gehoert(self.cert)
        self.srv, base = UU.server(self.srv_dir, cp, kp)
        man_home = os.path.join(self.tmp, "hm")
        # the manifest lists NEU and NEU+1 only (ALT is installed already) - signed with the throwaway key
        lst = os.path.join(self.tmp, "liste"); os.makedirs(lst)
        for k in ("neu", "plus1"):
            for f in (self.prog[k], os.path.basename(zip_zu(os.path.join(self.srv_dir, self.prog[k])) or "")):
                if f:
                    os.link(os.path.join(self.srv_dir, f), os.path.join(lst, f))
        r = subprocess.run([sys.executable, os.path.join(lst, self.prog["plus1"]), "--make-manifest", lst, "--sign-key", self.key,
                            "--base-url", base], capture_output=True, text=True, cwd=lst, env=dict(os.environ, MOTIONWATCH_HOME=man_home))
        try:
            shutil.copy(os.path.join(lst, "versions.json"), self.srv_dir)
            man = json.load(open(os.path.join(self.srv_dir, "versions.json")))
            vs = sorted(e["version"] for e in man["versions"])
        except (OSError, ValueError, KeyError):
            print(r.stdout[-1500:] + r.stderr[-1500:])
            vs = []
        self.url = base + "/versions.json"
        return ok(vs == sorted([self.ver["neu"], self.ver["plus1"]]), "Update-Quelle (HTTPS, signiert): %s" % ", ".join(vs))

    def kopieren(self, name):
        """eine Version nach ~/MoveEye (Programm + Zusatzdatei), dem Test-Benutzer gehörend -> Pfad"""
        src = os.path.join(self.srv_dir, self.prog[name])
        for f in (src, zip_zu(src)):
            dst = os.path.join(self.b.app, os.path.basename(f))
            shutil.copy(f, dst); self.b.gehoert(dst)
        return os.path.join(self.b.app, self.prog[name])

    def hand_start(self, prog, warten_web=True):
        """MoveEye von Hand starten (wie der Besitzer im Terminal) - ohne Fenster, Web auf allen Adressen wie auf dem Pi"""
        out = open(os.path.join(self.tmp, "hand_%d.txt" % int(time.time())), "w")
        self.hand = subprocess.Popen(self.b.cmd([self.b.py, prog, "--headless", "--port", str(self.port), "--web-password", PW],
                                                {"SSL_CERT_FILE": self.cert}), stdout=out, stderr=subprocess.STDOUT, cwd=self.b.app)
        return warte(lambda: version_da(self.port), self.a.limit) if warten_web else None

    def hand_ende(self):
        if self.hand and self.hand.poll() is None:
            self.hand.terminate()
            try:
                self.hand.wait(30)
            except subprocess.TimeoutExpired:
                self.hand.kill(); self.hand.wait(10)
        self.hand = None

    def log(self):
        p = os.path.join(self.b.daten, "motionwatch.log")
        try:
            return open(p, errors="replace").read()
        except OSError:
            return ""

    def zeigen(self, warum):
        """bei einem Fehler: Zustand, Journal und Protokoll-Ende"""
        print("---- %s: Zustand %s" % (warum, self.d.zeig()))
        print("---- Port %d: %s" % (self.port, lauscher(self.port)))
        j = self.d.journal(self.t0)
        print("---- Journal (Ende)\n" + (j[-3000:] if j else "(kein Journal)"))
        print("---- motionwatch.log (Ende)\n" + self.log()[-2500:])

    def schritt(self, name, t0):
        ZEITEN.append((name, time.time() - t0))


# ---------------------------------------------------------------------------------------------------------- Fälle
def einrichten(L, prog, titel):
    """von Hand starten, «Autostart» auf der Webseite einschalten, Hand-Programm beenden, Dienst starten (= Pi einschalten)"""
    print("%s: von Hand starten, Autostart über die Webseite, Dienst starten" % titel)
    t = L.hand_start(prog)
    if not ok(t is not None, "von Hand gestartet, Seite antwortet (%s s)" % t):
        return False
    c, body = holen(L.port, "/api/autostart", timeout=60, daten={"on": True, "lang": "de"})
    try:
        j = json.loads(body)
    except ValueError:
        j = {}
    ok(c == 200 and j.get("ok"), "Autostart eingeschaltet (HTTP %s, %s)" % (c, j.get("error") or "ok"))
    if (j.get("autostart") or {}).get("msg"):
        hinweis("Autostart-Meldung: %s" % j["autostart"]["msg"][:200])
    unit = os.path.join(L.b.home, ".config", "systemd", "user", UNIT)
    txt = open(unit).read() if os.path.isfile(unit) else ""
    ok(all(x in txt for x in ("Restart=always", "WatchdogSec=120", "NotifyAccess=main", "--headless --boot", os.path.basename(prog))),
       "Unit-Datei aus Teil 140 (autostart_unit): Restart=always, WatchdogSec=120, NotifyAccess=main, --headless --boot")
    rc, out, err = L.b.als(["systemd-analyze", "--user", "verify", unit], timeout=60)
    ok(rc == 0 or not (out + err).strip(), "systemd-analyze --user verify: %s" % ((out + err).strip()[:200] or "ok"))
    rc, out, _e = L.d.sctl("is-enabled", UNIT)
    ok(out == "enabled", "systemctl --user is-enabled: %s" % out)
    L.hand_ende()
    L.d.sctl("set-environment", "SSL_CERT_FILE=" + L.cert)        # the test server's certificate (not in the unit file)
    rc, out, err = L.d.sctl("start", UNIT, timeout=90)
    ok(rc == 0, "systemctl --user start (Pi eingeschaltet)%s" % ("" if rc == 0 else ": " + err[:200]))
    return True


def fall_a(L, v):
    print("a  kalter Start als Dienst")
    t0 = time.time()
    t = warte(lambda: version_da(L.port) == v, L.a.limit)
    ok(t is not None, "Seite antwortet mit %s (%s s, Grenze %d s)" % (v, t, L.a.limit))
    z = L.d.zeig()
    ok(z.get("ActiveState") == "active" and z.get("SubState") == "running", "Dienst active / running (%s / %s)" % (z.get("ActiveState"), z.get("SubState")))
    pid = z["MainPID"]
    try:
        cmd = open("/proc/%d/cmdline" % pid, "rb").read().replace(b"\0", b" ").decode(errors="replace")
        env = open("/proc/%d/environ" % pid, "rb").read().split(b"\0")
    except OSError:
        cmd, env = "", []
    ok("webcam_bewegung_" in cmd and "--boot" in cmd, "Hauptprozess des Dienstes ist MoveEye (PID %d: %s)" % (pid, cmd[-90:]))
    ok(any(e.startswith(b"NOTIFY_SOCKET=") for e in env), "NOTIFY_SOCKET gesetzt (Watchdog / Start-Wächter aktiv)")
    keys = [e.decode(errors="replace") for e in env if e.split(b"=")[0] in (b"XDG_RUNTIME_DIR", b"DBUS_SESSION_BUS_ADDRESS", b"PATH", b"USER", b"HOME")]
    print("  (Umgebung des Dienstes: %s)" % " · ".join(keys))
    if L.d.modus == "user":                                      # what MoveEye sees when it asks systemctl from inside a unit
        rc, out, err = L.b.als(["systemd-run", "--user", "--wait", "--pipe", "--quiet", "systemctl", "--user", "is-active", UNIT], timeout=60)
        ok(out.strip() == "active", "systemctl --user aus einem Dienst heraus (wie MoveEye): «%s» %s" % (out.strip(), err[:160]))
    tw = warte(lambda: int(L.d.zeig().get("WatchdogTimestampMonotonic") or 0) > 0, 45, 1.0)
    ok(tw is not None, "systemd bekommt «WATCHDOG=1» von MoveEye (nach %s s; WatchdogSec=120)" % tw)
    # a second MoveEye started by hand (without a window) while the service runs: ends by itself, the service stays (140)
    L.hand_start(os.path.join(L.b.app, L.prog["neu"]), warten_web=False)
    te = warte(lambda: L.hand.poll() is not None, 40)
    rc2 = L.hand.poll()
    L.hand_ende()
    z2 = L.d.zeig()
    ok(te is not None and rc2 == 0 and z2["MainPID"] == pid and z2.get("ActiveState") == "active",
       "zweites MoveEye von Hand: endet von selbst (Code %s, %s s), der Dienst bleibt (PID %d -> %d, %s)" % (rc2, te, pid, z2["MainPID"], z2.get("ActiveState")))
    if t is None:
        L.zeigen("a")
    L.schritt("a kalter Start", t0)
    return t is not None


def fall_d(L, v):
    print("d  kill -9 -> systemd startet neu; systemctl stop -> bleibt aus")
    t0 = time.time()
    z = L.d.zeig()
    os.kill(z["MainPID"], 9)
    t = warte(lambda: L.d.zeig()["MainPID"] not in (0, z["MainPID"]) and version_da(L.port) == v, L.a.limit + 10)
    z2 = L.d.zeig()
    ok(t is not None, "nach kill -9: neuer Prozess, Seite antwortet wieder (%s s; RestartSec=5)" % t)
    ok(z2["NRestarts"] == z["NRestarts"] + 1, "NRestarts %d -> %d" % (z["NRestarts"], z2["NRestarts"]))
    ts = time.time()
    rc, _o, err = L.d.sctl("stop", UNIT, timeout=120)
    dt = time.time() - ts
    ok(rc == 0 and dt < 30, "systemctl --user stop in %.1f s (SIGTERM: Aufnahme beenden, speichern; Grenze 30 s)%s" % (dt, "" if rc == 0 else " " + err[:120]))
    time.sleep(12)                                              # Restart=always must not start it again after a stop
    z3 = L.d.zeig()
    ok(z3.get("ActiveState") == "inactive" and web_aus(L.port), "bleibt aus nach «stop» (12 s gewartet: %s, Port %s)" % (
        z3.get("ActiveState"), "zu" if web_aus(L.port) else "offen"))
    rc, _o, _e = L.d.sctl("start", UNIT)
    t = warte(lambda: version_da(L.port) == v, L.a.limit)
    ok(t is not None, "wieder gestartet (%s s)" % t)
    if t is None:
        L.zeigen("d")
    L.schritt("d kill -9 / stop", t0)


def fall_e(L, v):
    print("e  Stromausfall: hart beendet, Reste liegen herum -> sauberer Start")
    t0 = time.time()
    time.sleep(3)                                               # the backup copy of the settings is written at the start
    L.d.sctl("kill", "-s", "SIGKILL", "--kill-whom=all", UNIT)
    L.d.sctl("stop", UNIT)                                      # before RestartSec=5: the Pi is off
    p = os.path.join(L.b.daten, "motionwatch_settings.json")
    txt = open(p).read()
    with open(p, "w") as f:
        f.write(txt[: max(10, len(txt) // 2)])                  # half written (no fsync before the power went)
    reste = [p + ".%d.1.tmp" % 4242, os.path.join(L.b.app, "webcam_bewegung_9_9_9.py.part"), os.path.join(L.b.daten, "run_state.json.tmp")]
    for r in reste:
        with open(r, "w") as f:
            f.write('{"cfg": {"web_po')
        L.b.gehoert(r)
    lock = os.path.join(tempfile.gettempdir(), "motionwatch-%d.lock" % L.port)
    ok(os.path.exists(lock), "alte Sperr-Datei liegt noch da (%s)" % os.path.basename(lock))
    rs = {}
    try:
        rs = json.load(open(os.path.join(L.b.daten, "run_state.json")))
    except (OSError, ValueError):
        pass
    ok(rs.get("clean") is False, "run_state.json: letzter Lauf nicht sauber beendet")
    n0 = L.d.zeig()["NRestarts"]
    L.d.sctl("start", UNIT)
    t = warte(lambda: version_da(L.port) == v, L.a.limit)
    ok(t is not None, "Seite antwortet nach dem Stromausfall (%s s)" % t)
    time.sleep(8)
    z = L.d.zeig()
    ok(z.get("ActiveState") == "active" and z["NRestarts"] == n0, "kein Neustart-Kreis (NRestarts %d -> %d, %s)" % (n0, z["NRestarts"], z.get("ActiveState")))
    lg = L.log()
    ok("the backup copy was used" in lg, "Protokoll: Einstellungen beschädigt -> Sicherung benutzt")
    ok(bool(glob.glob(p + ".bad-*")), "beschädigte Datei aufbewahrt (motionwatch_settings.json.bad-…)")
    if "unexpectedly" in lg:
        print("  (Protokoll: «The last run ended unexpectedly» - wie nach einem Stromausfall erwartet)")
    if t is None:
        L.zeigen("e")
    L.schritt("e Stromausfall", t0)


def fall_f(L, v):
    print("f  Start-Wächter: der Start hängt -> Code 1, systemd startet neu, start_hang.txt")
    t0 = time.time()
    hang, alt_ = os.path.join(L.b.daten, "start_hang.txt"), os.path.join(L.b.daten, "start_hang.txt.old")
    for x in (hang, alt_):
        if os.path.exists(x):
            os.remove(x)
    L.d.sctl("stop", UNIT)
    L.d.sctl("set-environment", "MW_START_WD=12")              # 12 s instead of 90 s (the same code path)
    # 3.87.1: a genuinely hung start = a stuck OLD MoveEye of the same user holds the web port (a foreign program would not
    # end the guard - case f2). Its command line names a MoveEye file, so the service knows: a fresh start helps here.
    os.makedirs(L.b.ci, exist_ok=True); L.b.gehoert(L.b.ci)
    alt_py, marke = os.path.join(L.b.ci, "webcam_bewegung_9_9_8.py"), os.path.join(L.b.ci, "alt_bereit")
    open(alt_py, "w").write("import socket, sys, time\ns = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
                            "s.bind(('0.0.0.0', int(sys.argv[1]))); s.listen(5); open(sys.argv[2], 'w').write('ok'); time.sleep(900)\n")
    L.b.gehoert(alt_py)
    if os.path.exists(marke):
        os.remove(marke)
    hp = subprocess.Popen(L.b.cmd([L.b.py, alt_py, str(L.port), marke]), cwd=L.b.home, start_new_session=True)
    warte(lambda: os.path.exists(marke), 20, 0.2)
    h = None
    n0 = L.d.zeig()["NRestarts"]
    try:
        L.d.sctl("start", UNIT)
        t = warte(lambda: L.d.zeig()["NRestarts"] > n0, 75, 1.0)
        ok(t is not None, "der hängende Start endet, systemd startet neu (nach %s s; Wächter 12 s + RestartSec 5 s)" % t)
        j = L.d.journal(t0)
        if j is None:
            hinweis("f: kein Journal (lokal) - Exit-Code 1 nicht geprüft, nur der Neustart durch systemd")
        else:
            ok(re.search(r"motionwatch\.service: Main process exited, code=exited, status=1", j) is not None,
               "Journal: «Main process exited, code=exited, status=1/FAILURE» (Start-Wächter, Teil 140)")
        tw = warte(lambda: os.path.exists(hang) or os.path.exists(alt_), 20)
        txt = ""
        for x in (hang, alt_):
            if os.path.exists(x):
                txt += open(x, errors="replace").read()
        ok(tw is not None and ("File" in txt or "Thread" in txt), "start_hang.txt mit den Threads (%d Zeichen)" % len(txt))
    finally:
        try:
            os.killpg(hp.pid, signal.SIGKILL)
        except OSError:
            pass
        hp.wait(10)
    t = warte(lambda: version_da(L.port) == v, L.a.limit + 30)
    ok(t is not None, "Port frei -> Seite antwortet (%s s)" % t)
    ok("The last start hung" in L.log(), "Protokoll: «The last start hung …»")
    z = L.d.zeig()
    ok(z.get("ActiveState") == "active", "Dienst active (%s)" % z.get("ActiveState"))
    if t is None:
        L.zeigen("f")
    L.d.sctl("unset-environment", "MW_START_WD")
    L.schritt("f Start-Wächter", t0)


def fall_f2(L, v):
    print("f2 ein Programm eines anderen Benutzers (root) hält den Web-Port: der Dienst bewacht weiter, kein Neustart (3.87.1)")
    t0 = time.time()
    L.d.sctl("stop", UNIT)
    L.d.sctl("set-environment", "MW_START_WD=12")
    h = socket.socket(); h.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    h.bind(("0.0.0.0", L.port)); h.listen(5)                    # this test runs as root: the service's user cannot see the holder
    try:
        L.d.sctl("start", UNIT)                                 # («start» after «stop» sets NRestarts to 0 - measured from here)
        time.sleep(2)
        z0 = L.d.zeig()
        time.sleep(40)                                          # more than three times the start watchdog (12 s)
        z = L.d.zeig()
        ok(z["NRestarts"] == z0["NRestarts"] and z.get("MainPID") == z0.get("MainPID") and z.get("ActiveState") == "active",
           "nach 40 s (Wächter 12 s): kein Neustart, derselbe Prozess, Dienst active (Neustarts %s -> %s, PID %s -> %s, %s)"
           % (z0["NRestarts"], z["NRestarts"], z0.get("MainPID"), z.get("MainPID"), z.get("ActiveState")))
        lg = L.log()
        ok("used by another program" in lg and "keeps guarding" in lg, "Protokoll: «… used by another program (not visible to this user) … keeps guarding»")
    finally:
        h.close()
    t = warte(lambda: version_da(L.port) == v, L.a.limit + 30)
    ok(t is not None, "Port frei -> Seite antwortet ohne Neustart (%s s)" % t)
    L.d.sctl("unset-environment", "MW_START_WD")
    L.schritt("f2 fremder Halter", t0)


def update(L, von, nach, titel, live=False):
    """Update in der App über /api/update (wie die Taste «Update»): derselbe Dienst, Seite kommt, kein Selbst-Stopp"""
    t0 = time.time()
    z = L.d.zeig()
    lb = LiveBild(L.port) if live else None
    if lb:
        time.sleep(2)
    c, body = holen(L.port, "/api/update", timeout=60)
    try:
        newer = json.loads(body).get("newer") or []
    except ValueError:
        newer = []
    ok(nach in newer, "%s steht in der Liste der Update-Quelle (%s)" % (nach, ", ".join(newer) or body[:120]))
    c, body = holen(L.port, "/api/update", timeout=180, daten={"action": "install", "version": nach})
    try:
        ans = json.loads(body)
    except ValueError:
        ans = {"error": body[:200]}
    ok(c == 200 and ans.get("ok"), "«Update» %s -> %s angenommen (%s)" % (von, nach, ans.get("error") or "ok"))
    t = warte(lambda: version_da(L.port) == nach, L.a.limit)
    z2 = L.d.zeig()
    ok(t is not None, "%s: neue Version %s antwortet nach %s s (Grenze %d s)" % (titel, nach, t, L.a.limit))
    ok(z2.get("ActiveState") == "active", "Dienst nach dem Update active (%s / %s)" % (z2.get("ActiveState"), z2.get("SubState")))
    ok(z2.get("InvocationID") == z.get("InvocationID") and z2["MainPID"] == z["MainPID"] and z2["NRestarts"] == z["NRestarts"],
       "derselbe Dienst-Lauf: InvocationID gleich, MainPID %d -> %d (os.execv), NRestarts %d -> %d" % (z["MainPID"], z2["MainPID"], z["NRestarts"], z2["NRestarts"]))
    lg = L.log()
    ok("it is stopped, this program takes over" not in lg[L.loglen:], "MoveEye hat den eigenen Dienst nicht gestoppt (Protokoll)")
    j = L.d.journal(t0)
    if j is None:
        hinweis("%s: kein Journal (lokal ohne journald) - «Stopping motionwatch.service» nicht geprüft, nur der Zustand" % titel)
    else:
        stops = [x for x in j.splitlines() if re.search(r"Stopp(ing|ed) .*motionwatch|motionwatch\.service: (Deactivated|Main process exited)", x)]
        ok(not stops, "Journal: kein «Stopping motionwatch.service» (%s)" % (" / ".join(stops)[:200] or "keins"))
    busy = [x for x in lg[L.loglen:].splitlines() if "busy at the start" in x]
    if busy:
        print("  (Protokoll: %s)" % busy[-1][-200:])
    rc, out, _e = L.d.sctl("show", UNIT, "-p", "ExecStart", "-p", "NeedDaemonReload")
    nd = os.path.basename(L.prog["plus1" if nach == L.ver["plus1"] else "neu"])
    folgt = nd in out and "NeedDaemonReload=no" in out
    if L.d.modus == "system" and not folgt:
        hinweis("BEKANNT (Vorschlag im Bericht): der System-Dienst von --install-service folgt dem Update nicht - die Unit "
                "startet weiter die alte Datei (Teil 140 autostart_follow_version: nur als root bzw. mit CFG autostart)")
    elif not ok(folgt, "die Unit startet jetzt %s (autostart_follow_version, daemon-reload)" % nd):
        print("  (systemctl show: %s)" % out.replace("\n", " · ")[:400])
        print("  (Protokoll Autostart: %s)" % " / ".join(x[-160:] for x in lg.splitlines() if "utostart" in x)[-600:])
    if lb:
        te = warte(lambda: lb.ende is not None, 30)
        ok(te is not None, "das offene Live-Bild endet beim Update (das Handy verbindet neu; %s Bytes vorher)" % lb.n)
        lb.zu()
        lb2 = LiveBild(L.port)
        tb = warte(lambda: lb2.n > 0, 30)
        ok(tb is not None, "Live-Bild der neuen Version kommt (%s s)" % tb)
        lb2.zu()
    if t is None or z2.get("ActiveState") != "active":
        L.zeigen(titel)
    L.loglen = len(L.log())
    L.schritt(titel, t0)
    return t is not None


def fall_g(L):
    print("g  System-Dienst /etc/systemd/system/motionwatch.service (sudo … --install-service, wie einrichten.sh)")
    t0 = time.time()
    rc, out, _e = (lambda r: (r.returncode, r.stdout.strip(), ""))(subprocess.run(["systemctl", "is-system-running"], capture_output=True, text=True))
    if out not in ("running", "degraded"):
        if L.a.ci:
            ok(False, "g: System-systemd läuft nicht (%s)" % out)
        else:
            hinweis("g übersprungen: kein System-systemd hier (%s) - läuft im CI" % (out or "?"))
        return
    L.d.sctl("disable", "--now", UNIT)
    sysunit = "/etc/systemd/system/" + UNIT
    S = Dienst(L.b, "system")
    try:
        L.d.sctl("stop", UNIT)
        alt = L.kopieren("alt")
        einstellungen(L.b, L.url, {"autostart": False})
        L.loglen = len(L.log())
        env = dict(os.environ, SUDO_USER=L.b.name, HOME="/root")
        r = subprocess.run([L.b.py, alt, "--install-service", "--port", str(L.port), "--web-password", PW], capture_output=True, text=True,
                           env=env, cwd=L.b.app, timeout=120)
        txt = open(sysunit).read() if os.path.isfile(sysunit) else ""
        ok(r.returncode == 0 and ("User=%s" % L.b.name) in txt, "System-Unit geschrieben (User=%s): %s" % (L.b.name, (r.stdout + r.stderr).strip()[-160:]))
        os.makedirs(sysunit + ".d", exist_ok=True)
        with open(sysunit + ".d/ci.conf", "w") as f:            # the test server's certificate (a drop-in: the unit stays as written)
            f.write("[Service]\nEnvironment=SSL_CERT_FILE=%s\n" % L.cert)
        subprocess.run(["systemctl", "daemon-reload"])
        S.sctl("restart", UNIT)
        if "WatchdogSec" not in txt:
            hinweis("g: die System-Unit von --install-service (Teil 420 service_text) hat kein WatchdogSec / NotifyAccess, kein "
                    "--boot und kein StartLimitIntervalSec=0 - anders als die Benutzer-Unit (Teil 140 autostart_unit)")
        t = warte(lambda: version_da(L.port) == L.ver["alt"], L.a.limit)
        ok(t is not None, "g/a: System-Dienst, Seite antwortet mit %s (%s s)" % (L.ver["alt"], t))
        z = S.zeig()
        ok(z.get("ActiveState") == "active", "g/a: active (%s)" % z.get("ActiveState"))
        if t is None:
            print(S.journal(t0) or "")
            return
        L.d = S
        update(L, L.ver["alt"], L.ver["neu"], "g/b Update (System-Dienst)")
        # the Pi is switched off and on again: which version comes?
        S.sctl("restart", UNIT, timeout=120)
        tv = warte(lambda: version_da(L.port), L.a.limit)
        v = version_da(L.port)
        ok(tv is not None, "g: nach dem Neustart des Pi antwortet die Seite (%s)" % (v or "nichts"))
        if v != L.ver["neu"]:
            hinweis("BEKANNT (Vorschlag im Bericht): System-Dienst - nach dem Neustart des Pi läuft wieder %s statt %s "
                    "(das Update gilt nur bis zum nächsten Neustart)" % (v or "nichts", L.ver["neu"]))
    finally:
        subprocess.run(["systemctl", "disable", "--now", UNIT], capture_output=True)
        for x in (sysunit + ".d/ci.conf",):
            if os.path.exists(x):
                os.remove(x)
        if os.path.isdir(sysunit + ".d"):
            os.rmdir(sysunit + ".d")
        if os.path.exists(sysunit):
            os.remove(sysunit)
        subprocess.run(["systemctl", "daemon-reload"])
        L.schritt("g System-Dienst", t0)


# ---------------------------------------------------------------------------------------------------------- main
def benutzer_anlegen(name):
    """CI: ein gewöhnlicher Benutzer mit eigenem systemd --user («linger»), wie der Benutzer auf dem Pi"""
    try:
        pwd.getpwnam(name)
    except KeyError:
        subprocess.run(["useradd", "-m", "-s", "/bin/bash", name], check=True)
    subprocess.run(["loginctl", "enable-linger", name], check=True)
    uid = pwd.getpwnam(name).pw_uid
    t = warte(lambda: os.path.exists("/run/user/%d/systemd/private" % uid), 30)
    ok(t is not None, "systemd --user für %s läuft (linger, /run/user/%d; %s s)" % (name, uid, t))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datei", default="", help="neue Version (Standard: neueste webcam_bewegung_*.py im Repository)")
    ap.add_argument("--alt", default="", help="alte Version für b (Standard: die Datei davor im Repository)")
    ap.add_argument("--plus1", default="", help="fertige Version NEU+1 für c (Standard: aus quelle/ bauen)")
    ap.add_argument("--benutzer", default="mwtest")
    ap.add_argument("--python", default=sys.executable, help="Python für MoveEye (wie auf dem Pi: 3.11)")
    ap.add_argument("--limit", type=int, default=60, help="Sekunden, bis die Seite antworten muss")
    ap.add_argument("--nur", default="a,d,e,f,b,c,g")
    ap.add_argument("--ci", action="store_true", help="Test-Benutzer anlegen, linger einschalten; g ist Pflicht")
    ap.add_argument("--ohne-leck", action="store_true", help="b ohne das Hilfsprogramm, das den Port hält (zum Vergleich)")
    a = ap.parse_args()
    if os.geteuid() != 0:
        print("braucht root (sudo): Test-Benutzer, linger, System-Dienst"); return 2
    nur = set(a.nur.lower().split(","))
    progs = sorted((p for p in glob.glob(os.path.join(REPO, "webcam_bewegung_*_*_*.py")) if zip_zu(p)), key=vkey)
    neu = os.path.abspath(a.datei or progs[-1])
    alt = os.path.abspath(a.alt) if a.alt else next((p for p in reversed(progs) if vkey(p) < vkey(neu)), "")
    if not (zip_zu(neu) and alt):
        print("NEU mit Zusatzdatei und eine ältere Version nötig (%s / %s)" % (neu, alt)); return 1
    tmp = tempfile.mkdtemp(prefix="mw_pidienst_")
    os.chmod(tmp, 0o755)
    plus1, bt = ([os.path.abspath(a.plus1), zip_zu(os.path.abspath(a.plus1))] if a.plus1 else []), None
    if not a.plus1:                                             # built while the setup runs (about 40 s)
        bt = threading.Thread(target=lambda: plus1.extend(bauen_plus1(neu, tmp)), daemon=True); bt.start()
    if a.ci:
        benutzer_anlegen(a.benutzer)
    b = Benutzer(a.benutzer, a.python)
    rc, out, err = b.als([b.py, "-c", "import sys, cv2, flask, numpy, cryptography; print(sys.version.split()[0])"])
    ok(rc == 0, "Python für %s: %s %s" % (b.name, b.py, out or err[-200:]))
    rc, out, err = b.als(["systemctl", "--user", "is-system-running"])
    ok(out in ("running", "degraded"), "systemctl --user als %s: %s %s" % (b.name, out, err[:120]))
    # GitHub's runner image writes its own variables (XDG_RUNTIME_DIR of the user «runner», its PATH) into the global
    # environment - every user manager takes them over and a service of the test user then reaches the wrong bus
    # («Failed to connect to bus: Permission denied»). On the Pi the manager has the user's own: set it like there.
    rc, out, err = b.als(["systemctl", "--user", "show-environment"])
    env_ = dict(x.split("=", 1) for x in out.splitlines() if "=" in x)
    if env_.get("XDG_RUNTIME_DIR") != b.run:
        hinweis("systemd --user von %s hatte XDG_RUNTIME_DIR=%s (Vorgabe des Runners) - auf %s gesetzt wie auf dem Pi"
                % (b.name, env_.get("XDG_RUNTIME_DIR"), b.run))
        b.als(["systemctl", "--user", "set-environment", "XDG_RUNTIME_DIR=" + b.run])
    if FEHLER:
        return 1
    L = Lauf(a, b, tmp)
    L.loglen = 0
    print("Neu: %s · alt: %s · Port %d · Benutzer %s (%s)" % (os.path.basename(neu), os.path.basename(alt), L.port, b.name, b.home))
    try:
        if bt is not None:
            bt.join(600)
        if not ok(len(plus1) == 2 and all(plus1), "NEU+1 aus quelle/ gebaut (%s)" % (os.path.basename(plus1[0]) if plus1 else "-")):
            return 1
        if not L.dateien(alt, neu, plus1[0]):
            return 1
        print("Versionen: alt %(alt)s · neu %(neu)s · neu+1 %(plus1)s" % L.ver)
        # ---- a, d, e, f with NEU
        prog = L.kopieren("neu")
        einstellungen(b, L.url)
        if einrichten(L, prog, "Einrichten (NEU)"):
            if "a" in nur:
                fall_a(L, L.ver["neu"])
            else:
                warte(lambda: version_da(L.port) == L.ver["neu"], L.a.limit)
            if "d" in nur:
                fall_d(L, L.ver["neu"])
            if "e" in nur:
                fall_e(L, L.ver["neu"])
            if "f" in nur:
                fall_f(L, L.ver["neu"])
                fall_f2(L, L.ver["neu"])
        # ---- b, c: ALT started by hand (the service follows the version started by hand), then two updates
        if nur & {"b", "c"}:
            t0 = time.time()
            print("ALT von Hand starten: der Dienst folgt der Hand-Version (autostart_follow_version)")
            L.d.sctl("stop", UNIT)
            einstellungen(b, L.url, {"autostart": True})
            for x in ("run_state.json", "update_guard.json"):
                if os.path.exists(os.path.join(b.daten, x)):
                    os.remove(os.path.join(b.daten, x))
            for f in os.listdir(b.app):                          # only ALT is installed: the updates download over HTTPS
                if re.match(r"(webcam_bewegung_|moveeye_daten_)\d+_\d+_\d+\.(py|zip)$", f):
                    os.remove(os.path.join(b.app, f))
            altp = L.kopieren("alt")
            th = L.hand_start(altp)
            ok(th is not None, "ALT von Hand gestartet (%s s)" % th)
            L.hand_ende()
            rc, out, _e = L.d.sctl("show", UNIT, "-p", "ExecStart")
            ok(os.path.basename(altp) in out, "die Unit startet jetzt ALT (%s)" % os.path.basename(altp))
            leck = os.path.join(b.ci, "leck")
            os.makedirs(leck, exist_ok=True); b.gehoert(leck)
            open(os.path.join(leck, "sitecustomize.py"), "w").write(LECK)
            marke = os.path.join(leck, "kind.pid")
            if not a.ohne_leck:
                L.d.sctl("set-environment", "PYTHONPATH=" + leck, "MW_CI_LECK=" + marke)
            L.d.sctl("start", UNIT)
            tv = warte(lambda: version_da(L.port) == L.ver["alt"], L.a.limit)
            ok(tv is not None, "Dienst mit ALT %s antwortet (%s s)" % (L.ver["alt"], tv))
            kind = 0
            if not a.ohne_leck:
                tk = warte(lambda: os.path.exists(marke), 30)
                kind = int(open(marke).read() or 0) if tk is not None else 0
                ok(kind > 0, "ein Hilfsprogramm des alten Programms hält eine Kopie der Web-Steckdose (PID %s)" % kind)
            L.d.sctl("unset-environment", "PYTHONPATH", "MW_CI_LECK")
            L.loglen = len(L.log())
            L.schritt("ALT von Hand, Dienst folgt", t0)
            if "b" in nur and tv is not None:
                gut = update(L, L.ver["alt"], L.ver["neu"], "b Update ALT -> NEU" + ("" if a.ohne_leck else " (Port beim Start belegt)"))
                if kind:
                    try:
                        st = open("/proc/%d/stat" % kind).read().rsplit(")", 1)[1].split()[0]
                    except OSError:
                        st = "weg"
                    print("  (Hilfsprogramm PID %d nach dem Update: %s)" % (kind, st))
                if "c" in nur and gut:
                    update(L, L.ver["neu"], L.ver["plus1"], "c zweites Update NEU -> NEU+1 bei offenem Live-Bild", live=True)
        if "g" in nur:
            fall_g(L)
    finally:
        L.hand_ende()
        try:
            L.d = Dienst(b, "user")
            L.d.sctl("disable", "--now", UNIT, timeout=60)
            L.d.sctl("unset-environment", "SSL_CERT_FILE", "PYTHONPATH", "MW_CI_LECK", "MW_START_WD")
        except Exception:
            pass
        try:
            L.srv.shutdown()
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nZeiten: " + " · ".join("%s %.0f s" % z for z in ZEITEN))
    if HINWEISE:
        print("Hinweise: %d" % len(HINWEISE))
    print("FEHLER: %d" % len(FEHLER) if FEHLER else "Alles gut.")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("### Pi-Dienst (echtes systemd): %s\n\n" % ("❌ %d Fehler" % len(FEHLER) if FEHLER else "✅ alles gut"))
            for x in FEHLER:
                f.write("- ❌ %s\n" % x)
            for x in HINWEISE:
                f.write("- ⚠️ %s\n" % x)
            f.write("\n" + " · ".join("%s %.0f s" % z for z in ZEITEN) + "\n\n")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
