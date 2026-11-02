#!/usr/bin/env python3
"""MoveEye Kiosk - HP-Wache (3.55.0): läuft in der Kiosk-Sitzung als Benutzer des Kiosks (kiosk_sitzung.sh wache) und
verbindet das Dauerrechnen des Test-Runners mit dem Spielen am HP.

  python3 -I hp_wache.py [--spiel-datei /run/moveeye-spiel/spielen] [--pause /run/moveeye-test/kiosk_pause]
                         [--status-port 8761] [--ruhe-s 900]

Drei Aufgaben, alles nur mit Daten-Dateien (nichts wird ausgeführt, was von aussen kommt):
1. «Spielen»-Wunsch erkennen und als Datei melden (SPIEL_DATEI, JSON {"grund", "seit"}; ihr Änderungsdatum = letzte
   Aktivität). Der Test-Runner (werkzeuge/test_runner/dauer.py) liest sie, hält das Rechnen an, sichert den Stand und gibt
   den Bildschirm frei; der Kiosk startet dann den Simulator.
   Entscheid Besitzer (03.11.2026): eine Verbindung MoveEye <-> Simulator allein ist KEIN Spielen (der Pi des Besitzers
   bleibt im Simulator-Betrieb dauernd verbunden). Spielen ist nur, wenn jemand wirklich zuschaut oder spielt:
   - Zuschauer in MoveEye: hat jemand bei MoveEye im Simulator-Betrieb den Reiter Live / die Sim-Ansicht offen und sichtbar
     (Web oder Fenster am Pi), schickt MoveEye alle ~20 s «POST /zuschauer» an den Status-Dienst (Teil 639zu). Das setzt nur
     eine Zeitmarke (Daten, höchstens 256 Bytes). Die Karte / Seite «HP rechnet» schickt das nie.
   - Handy-Seite des Spiels (8770): während gerechnet wird, lauscht die Wache dort; wer sie öffnet, will spielen (Antwort
     «Simulator startet», die Seite lädt neu). Verbindungen der Spieler zu 8770 / 8771 frischen das Spielen auf.
   - Am HP selbst: Knopf «Spielen» im Testbild (testbild.py schreibt dieselbe Datei); läuft der Simulator ohne Rechnen
     und jemand bedient ihn mit Maus / Tastatur, gilt das auch als Spielen.
   - Solange gespielt wird: jede Eingabe (Leerlauf-Zähler des X-Servers, libXss), jeder Zuschauer-Puls und jeder Spieler
     auf 8770 / 8771 frischt die Datei auf. 15 Min. ohne das -> die Datei ist abgelaufen (Änderungsdatum älter als --ruhe-s),
     das Rechnen geht dort weiter, wo es stand.
2. Kleiner Status-Dienst nur fürs eigene Netz (Port 8761, nur private Adressen): GET /status.json (was der HP gerade
   rechnet, Fortschritt, Spielen), GET /bild.png und POST /zuschauer (nur die Zeitmarke oben) (das kleine Live-Bild des Tests). MoveEye (Teil 639zu «HP rechnet») holt
   das für die Karte im Reiter Simulator. Keine Namen, Adressen, Zugangsdaten.
3. Protokoll nach stdout (kiosk_sitzung.sh leitet es nach ~/.moveeye_kiosk/wache.log).
"""
import argparse
import ipaddress
import json
import os
import select
import socket
import stat
import sys
import time

MAX_JSON, MAX_BILD = 65536, 2_500_000
SIM_PORTS = (8770,)                            # Handy-Seite des Spiels: beim Rechnen lauscht die Wache hier
AKTIV_PORTS = {8770, 8771}                     # Spieler am Handy (Seite, WebSocket) - nicht 8765: MoveEye allein zählt nicht
ARBEITEN = ("Erkennung messen", "KI-Trainingsbilder", "Langzeittest")


def log(*a):
    print(time.strftime("%F %T"), *a, flush=True)


# ------------------------------------------------------------------ Dateien (nur Daten)
def roh_lesen(p, max_bytes, max_alter=None):
    """normale Datei (keine Verknüpfung), nicht zu gross, optional nicht zu alt -> (bytes, mtime) oder (None, None)"""
    try:
        fd = os.open(p, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    except OSError:
        return None, None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > max_bytes:
            return None, None
        if max_alter is not None and time.time() - st.st_mtime > max_alter:
            return None, None
        return os.read(fd, max_bytes + 1)[:max_bytes], st.st_mtime
    except OSError:
        return None, None
    finally:
        os.close(fd)


def alter(p):
    """Alter einer normalen Datei in s (keine Verknüpfung), None = fehlt"""
    try:
        st = os.lstat(p)
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode):
        return None
    return max(0.0, time.time() - st.st_mtime)


def text(v, n):
    if not isinstance(v, str):
        return ""
    v = "".join(c for c in v if c.isprintable()).strip()
    return v[:n]


def zahl(v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return v if lo <= v <= hi else None


def spielen_schreiben(pfad, grund, ruhe_s=900):
    """Spielen-Wunsch melden (atomar, lesbar für den Test-Runner). Gilt die Datei noch, nur auffrischen."""
    try:
        al = alter(pfad)
        if al is not None and al < ruhe_s:
            os.utime(pfad, None)
            return True
        tmp = pfad + ".neu"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"grund": text(grund, 20), "seit": int(time.time())}, f)
        os.chmod(tmp, 0o644)
        os.replace(tmp, pfad)
        return True
    except OSError as e:
        log("Spielen-Datei nicht geschrieben:", e.strerror or e)
        return False


def spielen_lesen(pfad):
    roh, m = roh_lesen(pfad, 1024)
    if roh is None:
        return {}
    try:
        d = json.loads(roh.decode("utf-8", "replace"))
    except ValueError:
        d = {}
    if not isinstance(d, dict):
        d = {}
    return {"grund": text(d.get("grund"), 20), "seit": zahl(d.get("seit"), 0, 4e9), "mtime": m}


def fortschritt_sauber(roh):
    """fortschritt.json -> nur bekannte Felder, gekürzt (dieselben Regeln wie testbild.py)"""
    try:
        d = json.loads(roh.decode("utf-8", "replace"))
    except ValueError:
        return {}
    if not isinstance(d, dict):
        return {}
    jetzt = time.time()
    out = {"titel": text(d.get("titel"), 40), "arbeit": text(d.get("arbeit"), 30), "plan": text(d.get("plan"), 24),
           "plan_text": text(d.get("plan_text"), 90), "name": text(d.get("name"), 60),
           "fall": zahl(d.get("fall"), 0, 100000), "faelle": zahl(d.get("faelle"), 1, 100000),
           "start": zahl(d.get("start"), jetzt - 7 * 86400, jetzt + 120), "status": text(d.get("status"), 20),
           "soll": text(d.get("soll"), 20), "fall_name": text(d.get("fall_name"), 14)}
    ist = d.get("ist") if isinstance(d.get("ist"), dict) else {}
    out["ist"] = {"art": text(ist.get("art"), 12), "text": text(ist.get("text"), 30)} if ist else {}
    b = d.get("bilanz") if isinstance(d.get("bilanz"), dict) else {}
    bil = {}
    for k in ("personen", "ignoriert", "leer"):
        v = b.get(k)
        if isinstance(v, list) and len(v) == 2 and all(zahl(x, 0, 100000) is not None for x in v) and v[0] <= v[1]:
            bil[k] = [int(v[0]), int(v[1])]
    if zahl(b.get("pushes"), 0, 100000) is not None:
        bil["pushes"] = int(b["pushes"])
    out["bilanz"] = bil
    ka = []
    for k in (d.get("kacheln") if isinstance(d.get("kacheln"), list) else [])[:4]:
        if isinstance(k, list) and len(k) >= 2:
            ka.append([text(k[0], 30), text(k[1], 20), text(k[2], 8) if len(k) > 2 else ""])
    out["kacheln"] = ka
    le = d.get("letzter") if isinstance(d.get("letzter"), dict) else {}
    out["letzter"] = {"name": text(le.get("name"), 60), "text": text(le.get("text"), 60),
                      "ok": le.get("ok") if isinstance(le.get("ok"), bool) else None} if le else {}
    return {k: v for k, v in out.items() if v not in ("", None, {}, [])}


# ------------------------------------------------------------------ Eingaben und Verbindungen
class Leerlauf:
    """Leerlauf des X-Servers (ms seit der letzten Maus / Taste) über libXss; None = nicht messbar"""

    def __init__(self):
        self.ok = False
        try:
            import ctypes
            import ctypes.util

            class Info(ctypes.Structure):
                _fields_ = [("window", ctypes.c_ulong), ("state", ctypes.c_int), ("kind", ctypes.c_int),
                            ("til_or_since", ctypes.c_ulong), ("idle", ctypes.c_ulong), ("eventMask", ctypes.c_ulong)]
            x11 = ctypes.CDLL(ctypes.util.find_library("X11") or "libX11.so.6")
            xss = ctypes.CDLL(ctypes.util.find_library("Xss") or "libXss.so.1")
            x11.XOpenDisplay.restype = ctypes.c_void_p
            x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
            x11.XDefaultRootWindow.restype = ctypes.c_ulong
            x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
            xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(Info)
            xss.XScreenSaverQueryInfo.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(Info)]
            self.dpy = x11.XOpenDisplay(None)
            if not self.dpy:
                raise OSError("kein Bildschirm")
            self.root = x11.XDefaultRootWindow(self.dpy)
            self.info = xss.XScreenSaverAllocInfo()
            self.xss = xss
            self.ok = True
        except (OSError, AttributeError) as e:
            log("Leerlauf der Eingaben nicht messbar (libXss?):", e)

    def sekunden(self):
        if not self.ok:
            return None
        try:
            if self.xss.XScreenSaverQueryInfo(self.dpy, self.root, self.info):
                return self.info.contents.idle / 1000.0
        except OSError:
            pass
        return None


def verbindungen(ports):
    """Zahl der TCP-Verbindungen (offen oder gerade beendet) auf diesen lokalen Ports, aus /proc/net/tcp(6)"""
    n = 0
    for fn in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(fn) as f:
                next(f, None)
                for ln in f:
                    p = ln.split()
                    if len(p) < 4 or p[3] not in ("01", "06", "08"):        # ESTABLISHED, TIME_WAIT, CLOSE_WAIT
                        continue
                    try:
                        if int(p[1].rsplit(":", 1)[1], 16) in ports:
                            n += 1
                    except (ValueError, IndexError):
                        pass
        except OSError:
            pass
    return n


def privat(ip):
    """nur das eigene Netz: privat, Loopback, Link-Local, CGNAT (Tailscale)"""
    try:
        a = ipaddress.ip_address(ip.split("%", 1)[0])
    except ValueError:
        return False
    if getattr(a, "ipv4_mapped", None):
        a = a.ipv4_mapped
    if a.is_loopback or a.is_link_local or a.is_private:
        return True
    return a.version == 4 and a in ipaddress.ip_network("100.64.0.0/10")


# ------------------------------------------------------------------ Netz
def lauscher(port):
    for fam, adr in ((socket.AF_INET6, "::"), (socket.AF_INET, "0.0.0.0")):
        s = None
        try:
            s = socket.socket(fam, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if fam == socket.AF_INET6:
                s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            s.bind((adr, port))
            s.listen(16)
            s.setblocking(False)
            return s
        except OSError:
            if s is not None:
                s.close()
    return None


def anfrage(c, mit_inhalt=False):
    """erste Zeile einer HTTP-Anfrage lesen (höchstens 2 KB, 2 s) -> (Methode, Pfad) oder ("", ""); mit_inhalt: dazu
    höchstens 256 Bytes Inhalt -> (Methode, Pfad, Inhalt)"""
    c.settimeout(2.0)
    roh = b""
    try:
        while b"\r\n\r\n" not in roh and b"\n\n" not in roh and len(roh) < 2048:
            t = c.recv(2048 - len(roh))
            if not t:
                break
            roh += t
    except OSError:
        pass
    zeile = roh.split(b"\n", 1)[0].decode("latin-1", "replace").strip().split()
    if len(zeile) < 2:
        return ("", "", b"") if mit_inhalt else ("", "")
    meth, pfad = zeile[0][:8], zeile[1].split("?", 1)[0][:200]
    if not mit_inhalt:
        return meth, pfad
    kopf, _, inhalt = roh.partition(b"\r\n\r\n")
    n = 0
    for ln in kopf.split(b"\r\n")[1:]:
        k, _, v = ln.partition(b":")
        if k.strip().lower() == b"content-length":
            try:
                n = int(v.strip())
            except ValueError:
                n = -1
    if n < 0 or n > 256:
        return meth, pfad, None
    try:
        while len(inhalt) < n:
            t = c.recv(n - len(inhalt))
            if not t:
                break
            inhalt += t
    except OSError:
        pass
    return meth, pfad, inhalt[:n]


def antwort(c, code, typ, daten, extra=""):
    kopf = {200: "OK", 404: "Not Found", 405: "Method Not Allowed", 503: "Service Unavailable"}.get(code, "OK")
    try:
        c.sendall(("HTTP/1.0 %d %s\r\nContent-Type: %s\r\nContent-Length: %d\r\nCache-Control: no-store\r\n"
                   "X-Content-Type-Options: nosniff\r\nConnection: close\r\n%s\r\n" % (code, kopf, typ, len(daten), extra)).encode()
                  + daten)
    except OSError:
        pass


class Wache:
    def __init__(self, a):
        self.a = a
        self.spiel = a.spiel_datei
        self.ordner = os.path.dirname(a.pause)
        self.yield_s = {}                       # Port -> Socket (nur während gerechnet wird)
        self.status_s = lauscher(a.status_port) if a.status_port else None
        if a.status_port and self.status_s is None:
            log("Status-Port", a.status_port, "besetzt - ohne Status-Dienst")
        self.leer = Leerlauf()
        self.zuschauer_t = 0.0                  # letzter Zuschauer-Puls von MoveEye (POST /zuschauer)
        self.n_sek = []
        self.letzte_aktiv = 0.0
        self.t_zustand = 0.0
        self.zustand = "frei"
        self.dir_warnung = False

    # ---------------------------------------------- Zustand
    def rechnet(self):
        al = alter(self.a.pause)
        return al is not None and al < self.a.pause_max_s

    def spielt(self):
        al = alter(self.spiel)
        return al is not None and al < self.a.ruhe_s

    def neu_zustand(self):
        z = "spielen" if self.spielt() else ("rechnet" if self.rechnet() else "frei")
        if z != self.zustand:
            log("Zustand:", self.zustand, "->", z)
            self.zustand = z
        return z

    def wunsch(self, grund):
        if not os.path.isdir(os.path.dirname(self.spiel)):
            if not self.dir_warnung:
                log("Ordner", os.path.dirname(self.spiel), "fehlt (moveeye-hp-update richtet ihn ein) - Spielen nicht möglich")
                self.dir_warnung = True
            return
        if spielen_schreiben(self.spiel, grund, self.a.ruhe_s):
            log("Spielen:", grund, "- Rechnen wird angehalten")
        self.letzte_aktiv = time.time()
        self.lauscher_zu()
        self.neu_zustand()

    # ---------------------------------------------- Lauscher auf den Simulator-Ports
    def lauscher_auf(self):
        for p in self.a.sim_ports:
            if p not in self.yield_s:
                s = lauscher(p)
                if s is not None:
                    self.yield_s[p] = s
                    log("lausche auf Port", p, "(Simulator aus)")

    def lauscher_zu(self):
        for p, s in list(self.yield_s.items()):
            try:
                s.close()
            except OSError:
                pass
            del self.yield_s[p]
            log("Port", p, "frei (für den Simulator)")

    def gast(self, port, c, adr):
        """Handy-Seite des Spiels (8770), während gerechnet wird: wer sie öffnet, will spielen"""
        meth, pfad = anfrage(c)
        html = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
                "<meta http-equiv=refresh content=12><body style='font:18px sans-serif;background:#0f1624;color:#e6ebf4;"
                "text-align:center;padding-top:30vh'>MoveEye Sim startet …<br><small>Die Seite lädt gleich neu.</small>")
        antwort(c, 503, "text/html; charset=utf-8", html.encode(), "Retry-After: 10\r\n")
        if meth:
            self.wunsch("handy")

    # ---------------------------------------------- Status-Dienst
    def status(self):
        z = self.neu_zustand()
        d = {"v": 1, "t": int(time.time()), "zustand": z}
        if z == "rechnet":
            roh, _ = roh_lesen(os.path.join(self.ordner, "fortschritt.json"), MAX_JSON, 3 * 86400)
            f = fortschritt_sauber(roh) if roh else {}
            d["fortschritt"] = f
            if f.get("arbeit") in ARBEITEN:
                d["arbeit"] = f["arbeit"]
            al = alter(os.path.join(self.ordner, "bild_klein.png"))
            d["bild"] = al is not None and al < 120
        elif z == "spielen":
            s = spielen_lesen(self.spiel)
            d["spielen"] = {"grund": s.get("grund", ""), "seit": int(s["seit"]) if s.get("seit") else None,
                            "ruhe_noch_s": max(0, int(self.a.ruhe_s - (alter(self.spiel) or 0)))}
        return json.dumps(d, ensure_ascii=False).encode()

    def status_gast(self, c):
        meth, pfad, inhalt = anfrage(c, mit_inhalt=True)
        if meth == "POST" and pfad == "/zuschauer":
            was = ""
            try:
                d = json.loads((inhalt or b"").decode("utf-8", "replace")) if inhalt else {}
                was = d.get("was") if isinstance(d, dict) else ""
            except ValueError:
                pass
            if was not in ("live", "fenster", "spiel"):
                antwort(c, 404, "text/plain", b"nicht da\n")
                return
            neu = time.time() - self.zuschauer_t > self.a.zuschauer_s
            self.zuschauer_t = time.time()
            if neu:
                log("Zuschauer in MoveEye (%s)" % was)
            if self.neu_zustand() != "spielen":
                self.wunsch("zuschauer" if was != "spiel" else "spiel")
            else:
                self.aktivitaet("spielen")
            antwort(c, 200, "application/json; charset=utf-8", self.status())
        elif meth not in ("GET", "HEAD"):
            antwort(c, 405, "text/plain", b"nur GET\n")
        elif pfad in ("/status.json", "/"):
            antwort(c, 200, "application/json; charset=utf-8", self.status())
        elif pfad == "/bild.png" and self.zustand == "rechnet":
            roh, _ = roh_lesen(os.path.join(self.ordner, "bild_klein.png"), MAX_BILD, 120)
            if roh and roh.startswith(b"\x89PNG\r\n\x1a\n"):
                antwort(c, 200, "image/png", roh if meth == "GET" else b"")
            else:
                antwort(c, 404, "text/plain", b"kein Bild\n")
        else:
            antwort(c, 404, "text/plain", b"nicht da\n")

    # ---------------------------------------------- Takt
    def aktivitaet(self, z):
        """Eingaben / Verbindungen prüfen: Spielen auffrischen, beginnen (ohne Rechnen) oder nach 15 Min. Ruhe beenden"""
        jetzt = time.time()
        idle = self.leer.sekunden()
        eingabe = idle is not None and idle < 20
        zusch = jetzt - self.zuschauer_t < self.a.zuschauer_s
        verb = (verbindungen(AKTIV_PORTS) > 0 if z != "rechnet" else False) or zusch   # beim Rechnen ist 8770 die Wache
        if z == "frei" and (eingabe or verb):
            self.wunsch("eingabe" if eingabe else "zuschauer" if zusch else "handy")
            return
        if z != "spielen":
            return
        if eingabe or verb:
            self.letzte_aktiv = jetzt
            al = alter(self.spiel)
            if al is not None and al > 30:
                try:
                    os.utime(self.spiel, None)
                except OSError:
                    pass

    def lauf(self):
        log("HP-Wache startet (Spielen:", self.spiel, "· Status-Port", self.a.status_port or "aus", ")")
        t_akt = 0.0
        while True:
            jetzt = time.time()
            if jetzt - self.t_zustand >= 0.5:
                self.t_zustand = jetzt
                z = self.neu_zustand()
                if z == "rechnet":
                    self.lauscher_auf()
                else:
                    self.lauscher_zu()
                if jetzt - t_akt >= 3:
                    t_akt = jetzt
                    self.aktivitaet(z)
            socks = list(self.yield_s.values()) + ([self.status_s] if self.status_s else [])
            try:
                bereit, _, _ = select.select(socks, [], [], 0.5)
            except (OSError, ValueError):
                time.sleep(0.5)
                continue
            for s in bereit:
                try:
                    c, adr = s.accept()
                except OSError:
                    continue
                self.n_sek = [t for t in self.n_sek if jetzt - t < 1.0] + [jetzt]
                ip = adr[0] if adr else ""
                if len(self.n_sek) > 20 or not privat(ip):       # zu viele oder nicht aus dem eigenen Netz: zu
                    c.close()
                    continue
                try:
                    if s is self.status_s:
                        self.status_gast(c)
                    else:
                        port = next((p for p, x in self.yield_s.items() if x is s), 0)
                        self.gast(port, c, ip)
                finally:
                    c.close()


def main():
    ap = argparse.ArgumentParser(description="MoveEye Kiosk: Spielen-Wunsch erkennen, Status fürs eigene Netz")
    ap.add_argument("--spiel-datei", default="/run/moveeye-spiel/spielen")
    ap.add_argument("--pause", default="/run/moveeye-test/kiosk_pause")
    ap.add_argument("--pause-max-s", type=int, default=25200)
    ap.add_argument("--ruhe-s", type=int, default=900, help="so lange ohne Eingabe und ohne Verbindung, dann wird weitergerechnet")
    ap.add_argument("--status-port", type=int, default=8761, help="0 = aus")
    ap.add_argument("--zuschauer-s", type=int, default=60, help="so lange gilt ein Zuschauer-Puls von MoveEye (s)")
    ap.add_argument("--sim-ports", default=",".join(str(p) for p in SIM_PORTS),
                    help="Port der Handy-Seite des Spiels, auf dem beim Rechnen gelauscht wird")
    a = ap.parse_args()
    try:
        a.sim_ports = [int(x) for x in a.sim_ports.split(",") if x.strip()][:1]
    except ValueError:
        ap.error("--sim-ports: Zahlen mit Komma")
    if not a.sim_ports or not all(1024 < p < 65536 for p in a.sim_ports):
        ap.error("--sim-ports: Ports 1025 bis 65535")
    a.ruhe_s = max(30, min(7200, a.ruhe_s))
    try:
        Wache(a).lauf()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
