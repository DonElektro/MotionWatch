#!/usr/bin/env python3
"""Test «GoPro Hero 8 über Bluetooth (inoffiziell)» (MoveEye Teil 639zzzzzzg) – ohne echte GoPro, ohne echtes Netz.

  A) im eigenen Prozess (gebaute Datei geladen):
     * erfundenes nmcli / ip vorne im PATH (schreiben jeden Aufruf und stdin mit), zwei erfundene WLAN-Adapter,
     * Fake-BLE (H8["ble_factory"]): liefert WLAN-Name + Passwort, zeichnet die Befehle auf,
     * nachgestellte GoPro auf 127.0.0.1: HTTP (gpStream restart, Status mit Akku 70) und Keep-alive-Empfänger;
       der Strom ist ffmpeg testsrc als MPEG-TS über UDP und läuft nur, solange Keep-alive kommt (wie die echte Kamera).
     Geprüft: ohne 2. Stick = klare Meldung (5 Sprachen), Stick im Repeater = klare Meldung, Start → Quelle liefert ein Bild
     (OpenCV), Keep-alive läuft (richtiges Paket), Akku, NetworkManager nur auf wlan1 (never-default, psk-flags 2, Passwort nur
     über stdin), Abbruch → Neustart (zweimal: nur Strom weg; Strom + HTTP weg = WLAN neu), Stopp (WLAN aus, GoPro schlafen),
     von Hand getipptes Passwort wenn BLE nicht geht, API nur Admin, kein Passwort in Protokoll / argv / API / Ausgabe.
  B) --browser: MoveEye (Demo, eigener Daten-Ordner): Feld window.goproH8 auf der Einstellungsseite, 390 px (dunkel) und PC,
     keine JS-Fehler, ohne 2. Stick die klare Meldung; Bilder nach --bilder.

  python3 werkzeuge/gopro_hero8_test.py [--datei X.py] [--browser] [--bilder ORDNER]
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
FEHLER = []
PW = "Hero8-Geheim-42x"          # the made-up GoPro Wi-Fi password (must never show up anywhere)

FAKE = r'''#!/usr/bin/env python3
import json, os, sys
P = os.environ["MW_FAKE_NET"]
st = json.load(open(P))
me = os.path.basename(sys.argv[0]); a = sys.argv[1:]
inp = ""
if "/dev/stdin" in a:
    inp = sys.stdin.read()
st["calls"].append({"argv": [me] + a, "stdin": inp})
out, code = "", 0
if me == "nmcli":
    if "--wait" in a:
        i = a.index("--wait"); a = a[:i] + a[i + 2:]
    if a[:5] == ["-t", "-f", "NAME", "connection", "show"]:
        out = "".join(n + "\n" for n in st["conns"])
    elif a[:2] == ["connection", "add"]:
        st["conns"].append(a[a.index("con-name") + 1])
    elif a[:2] == ["connection", "modify"]:
        pass
    elif a[:2] == ["connection", "up"]:
        st["ups"] += 1
        if st.get("up_fail", 0) > 0:
            st["up_fail"] -= 1; code = 4; sys.stderr.write("Error: Connection activation failed\n")
        elif inp.strip() != "802-11-wireless-security.psk:" + st["pw"]:
            code = 4; sys.stderr.write("Error: secrets were required\n")
    elif a[:2] == ["connection", "down"]:
        st["downs"] += 1
elif me == "ip":
    if a[:3] == ["-4", "route", "get"]:
        out = a[3] + " dev " + st["route_dev"] + " src 10.5.5.100 uid 1000\n    cache\n"
    elif a[:4] == ["-4", "route", "show", "default"]:
        out = "default via 192.168.1.1 dev " + st["default_dev"] + " proto dhcp metric 600\n"
    elif a[:4] == ["-4", "-o", "addr", "show"]:
        out = "3: wlan0    inet " + st["home_ip"] + "/24 brd 192.168.1.255 scope global wlan0\n"
json.dump(st, open(P, "w"))
sys.stdout.write(out)
sys.exit(code)
'''


def fake_bin(tmp, state):
    b = os.path.join(tmp, "bin"); os.makedirs(b, exist_ok=True)
    for n in ("nmcli", "ip"):
        p = os.path.join(b, n)
        open(p, "w").write(FAKE); os.chmod(p, 0o755)
    json.dump(state, open(os.path.join(tmp, "net.json"), "w"))
    return b


TEIL_A = r'''
import json, os, socket, subprocess, sys, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import cv2
ns = {"__name__": "mw_h8_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
P = os.environ["MW_FAKE_NET"]; PW = os.environ["H8_PW"]
out = {}
logs = []
ns["log_event"] = lambda kind, text, *a, **k: logs.append(str(text))
H8, NET = ns["H8"], ns["H8_NET"]

def free(kind=socket.SOCK_DGRAM):
    s = socket.socket(socket.AF_INET, kind); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

CAM = {"ka": 0, "ka_bad": 0, "ka_t": 0.0, "ff": None, "restarts": 0, "http_fail": 0, "streaming": True}
NET.update(ip="127.0.0.1", cam_port=free(), rx_port=free(), http=free(socket.SOCK_STREAM))
ns["H8_STATUS_S"] = 2.0; H8["up_pause"] = 0.2

def ff_start():
    ff_stop()
    CAM["ff"] = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-re", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10",
                                  "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-g", "10", "-f", "mpegts",
                                  "udp://127.0.0.1:%d?pkt_size=1316" % NET["rx_port"]], stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ff_stop():
    p = CAM.get("ff")
    if p is not None and p.poll() is None:
        p.terminate()
        try: p.wait(5)
        except Exception: p.kill()
    CAM["ff"] = None

class Cam(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if CAM["http_fail"] > 0 and u.path == "/gp/gpControl/execute":
            CAM["http_fail"] -= 1; self.send_response(503); self.end_headers(); return
        if u.path == "/gp/gpControl/execute" and q.get("p1") == ["gpStream"] and q.get("c1") == ["restart"]:
            CAM["restarts"] += 1
            if CAM["streaming"]:
                ff_start()
            body = b"{}"
        elif u.path == "/gp/gpControl/status":
            body = json.dumps({"status": {"70": 77, "8": 0}}).encode()
        else:
            self.send_response(404); self.end_headers(); return
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)

srv = ThreadingHTTPServer(("127.0.0.1", NET["http"]), Cam)
threading.Thread(target=srv.serve_forever, daemon=True).start()

def ka_rx():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", NET["cam_port"]))
    while True:
        d, src = s.recvfrom(2048)
        if d == b"_GPHD_:1:0:2:0.000000\n" and src[1] == NET["rx_port"]:
            CAM["ka"] += 1; CAM["ka_t"] = time.monotonic()
        else:
            CAM["ka_bad"] += 1
threading.Thread(target=ka_rx, daemon=True).start()

def ka_watch():                  # like the real GoPro: no keep-alive for 8 s -> the stream stops
    while True:
        time.sleep(0.5)
        if CAM["ff"] is not None and CAM["ka_t"] and time.monotonic() - CAM["ka_t"] > 8:
            ff_stop()
threading.Thread(target=ka_watch, daemon=True).start()

class FakeBle:
    log = []
    fail = False
    def __init__(self, addr): self.addr = addr
    def connect(self, timeout=20.0):
        if FakeBle.fail: raise OSError("no device")
        FakeBle.log.append("connect " + self.addr)
    def write(self, short, data, wait=3.0):
        FakeBle.log.append("w %s %s" % (short, data.hex())); return bytes([2, data[1], 0])
    def read(self, short):
        FakeBle.log.append("r " + short)
        return {"0002": b"GP25123456", "0003": PW.encode()}[short]
    def close(self): FakeBle.log.append("close")
H8["ble_factory"] = FakeBle

AD = [{"iface": "wlan0", "usb": False, "chip": "Broadcom (built in)"}, {"iface": "wlan1", "usb": True, "chip": "MediaTek MT7612U"}]
ns["wifi_adapters"] = lambda: [dict(a) for a in AD]
ns["wifi_backend"] = lambda: "nm"
ns["WIFI"]["iface"] = "wlan0"
ns["CFG"]["gopro_h8"] = {"g1": {"addr": "AA:BB:CC:DD:EE:01", "name": "GoPro 1234"}}
tr = ns["tr"]

def net(): return json.load(open(P))

# 1) no second stick
ns["wifi_adapters"] = lambda: [dict(AD[0])]
try:
    ns["h8_start"]({"id": "g1"}); out["nostick"] = ["started?!"]
except RuntimeError as e:
    out["nostick"] = [str(e), {L: tr(str(e), L) for L in ("de", "fr", "it", "rm", "en")}, ns["h8_bereit"]()["ok"], ns["h8_status"]("g1")["fehler"]]
out["nostick_calls"] = [c["argv"][:3] for c in net()["calls"]]
# 2) the stick belongs to the repeater
ns["wifi_adapters"] = lambda: [dict(a) for a in AD]
ns["DUAL"].update(on=True, ap="wlan0", up="wlan1")
out["repeater"] = ns["h8_stick"]()
ns["DUAL"].update(on=False, ap="", up="")
# 3) start: Bluetooth, Wi-Fi only on wlan1, preview
t0 = time.time()
src = ns["h8_start"]({"id": "g1"})
out["src"] = src
cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 15000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 15000])
ok, fr = cap.read()
out["frame"] = [bool(ok), list(fr.shape) if ok else None, round(time.time() - t0, 1)]
for _i in range(40):
    if ns["h8_status"]("g1")["akku"] is not None and CAM["ka"] >= 3: break
    time.sleep(0.5)
for _i in range(20):
    ok2, _f = cap.read()
cap.release()
st = ns["h8_status"]("g1")
out["run"] = [st["streamt"], st["verbunden"], st["akku"], st["keepalive"], CAM["ka"], CAM["ka_bad"], st["zustand"], st["stick"], bool(ok2)]
out["ble1"] = list(FakeBle.log)
c = net()["calls"]
out["nm_add"] = next((x["argv"] for x in c if x["argv"][1:3] == ["connection", "add"]), [])
ups_ = [x for x in c if "up" in x["argv"] and "connection" in x["argv"]]
out["nm_up"] = [len(ups_), all("passwd-file" in u["argv"] and "/dev/stdin" in u["argv"] and "wlan1" in u["argv"] for u in ups_),
                bool(ups_) and ups_[0]["stdin"] == "802-11-wireless-security.psk:" + PW + "\n"]
# 4) the picture breaks off (only the stream) -> restart over HTTP
n0 = st["neustarts"]; r0 = CAM["restarts"]
ff_stop()
for _i in range(60):
    s_ = ns["h8_status"]("g1")
    if s_["neustarts"] > n0 and s_["streamt"]: break
    time.sleep(0.5)
s_ = ns["h8_status"]("g1")
out["break1"] = [s_["neustarts"] - n0, s_["streamt"], CAM["restarts"] - r0, any("picture interrupted" in x for x in logs)]
# 5) stream AND camera HTTP gone once -> the Wi-Fi again, then the preview
ups0 = net()["ups"]; n0 = s_["neustarts"]
CAM["http_fail"] = 1; ff_stop()
for _i in range(80):
    s_ = ns["h8_status"]("g1")
    if s_["neustarts"] > n0 and s_["streamt"]: break
    time.sleep(0.5)
out["break2"] = [s_["neustarts"] - n0, s_["streamt"], net()["ups"] - ups0]
cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 15000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 15000])
ok3, _f = cap.read(); cap.release()
out["frame_after"] = bool(ok3)
# 6) API: only the administrator, never the password
out["api_user"] = ns["h8_api"]({}, "GET", "user")[1]
ns["CFG"]["lock_on"] = True
out["api_locked"] = ns["h8_api"]({}, "GET", "admin")[1]
ns["CFG"]["lock_on"] = False
g, code = ns["h8_api"]({"lang": "de"}, "GET", "admin")
out["api_get"] = [code, g["devs"]["g1"]["pw_im_speicher"], g["devs"]["g1"]["zustand_text"]]
out["api_json"] = json.dumps(g, ensure_ascii=False)
out["api_cmd"] = ns["h8_api"]({"do": "cmd", "id": "g1", "cmd": "rec_on"}, "POST", "admin")[0]["ok"]
out["api_badcmd"] = ns["h8_api"]({"do": "cmd", "id": "g1", "cmd": "format_sd"}, "POST", "admin")[0]["ok"]
out["api_badaddr"] = ns["h8_api"]({"do": "addr", "id": "g1", "addr": "zz"}, "POST", "admin")[1]
# 7) stop: Wi-Fi down, the GoPro Wi-Fi off and asleep
FakeBle.log.clear(); d0 = net()["downs"]
ns["h8_stop"]({"id": "g1"})
out["stop"] = [net()["downs"] - d0, list(FakeBle.log), ns["h8_status"]("g1")["zustand"], ns["h8_status"]("g1")["streamt"]]
time.sleep(1.0)
# 8) Bluetooth does not work, the password was typed -> it still starts
FakeBle.fail = True
ns["H8_SECRET"].clear()
r = ns["h8_api"]({"do": "pw", "id": "g1", "pw": PW, "ssid": "GP25123456"}, "POST", "admin")
out["typed_pw"] = r[0]["ok"]
try:
    src2 = ns["h8_start"]({"id": "g1"})
    cap = cv2.VideoCapture(src2, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 15000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 15000])
    out["typed_frame"] = bool(cap.read()[0]); cap.release()
except RuntimeError as e:
    out["typed_frame"] = "error " + str(e)
FakeBle.fail = False
ns["h8_stop"]({"id": "g1"}, sleep=False)
ns["H8_SECRET"].clear()
FakeBle.fail = True
try:
    ns["h8_start"]({"id": "g1"}); out["no_ble_no_pw"] = "started?!"
except RuntimeError as e:
    out["no_ble_no_pw"] = str(e)
FakeBle.fail = False
# 9) the default route never moves to the stick
st_ = net(); st_["default_dev"] = "wlan1"; json.dump(st_, open(P, "w"))
out["route_guard"] = ns["h8_route_ok"]("wlan1")
# 10) through the core (639zzzzzze): way only for HERO8, gopro_add -> gopro_quelle -> start, gopro_open -> picture
st_ = net(); st_["default_dev"] = "wlan0"; json.dump(st_, open(P, "w"))
ns["H8_SECRET"].clear(); FakeBle.log.clear()
ns["_rx_manage"] = lambda *a, **k: None          # the RTMP receiver of the core is not part of this test
out["weg_ok"] = [ns["_gp_weg_ok"]("hero8_ble", "hero8"), ns["_gp_weg_ok"]("hero8_ble", "hero9"),
                 ns["_gp_weg_info"]("hero8_ble")["titel"], tr(ns["_gp_weg_info"]("hero8_ble")["titel"], "de")]
try:
    okk, err, gid = ns["gopro_add"]("Hero 8 Zelt", "hero8", "hero8_ble", addr="AA:BB:CC:DD:EE:02")
    out["core_add"] = [okk, err]
    if okk:
        q = ns["gopro_quelle"](gid)
        for _i in range(40):
            if ns["gopro_status"](gid)["streamt"]: break
            time.sleep(0.5)
        so = ns["gopro_open"]("gopro:" + gid)
        fr_ = so[0].read() if so[0] is not None else None
        out["core"] = [q.startswith("udp://127.0.0.1:"), ns["gopro_status"](gid), so[3], None if fr_ is None else (list(fr_[1].shape) if isinstance(fr_, tuple) else list(fr_.shape)),
                       "connect AA:BB:CC:DD:EE:02" in FakeBle.log]
        ns["gopro_stop"](gid)
        out["core_stop"] = ns["h8_status"](gid)["zustand"]
except Exception as e:
    out["core_add"] = [False, "%s: %s" % (type(e).__name__, e)]
# password nowhere
calls = net()["calls"]
out["pw_argv"] = any(PW in " ".join(x["argv"]) for x in calls)
out["pw_stdin_only_up"] = all(("connection" in x["argv"] and "up" in x["argv"]) for x in calls if PW in x["stdin"])
out["pw_log"] = any(PW in x for x in logs)
out["pw_api"] = PW in out.pop("api_json")
out["logs"] = logs[-12:]
ns["h8_selftest"]()
out["selftest"] = True
ff_stop(); time.sleep(0.5); ff_stop()
print("ERG " + json.dumps(out, ensure_ascii=False, default=str))
sys.stdout.flush()
os._exit(0)
'''


def ok(bed, text):
    print(("  ok     " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


def teil_a(datei, tmp):
    print("A) Logik im eigenen Prozess (Fake-BLE, erfundenes nmcli / ip, UDP-Strom mit ffmpeg testsrc)", flush=True)
    home = os.path.join(tmp, "a"); os.makedirs(home)
    b = fake_bin(tmp, {"calls": [], "conns": [], "ups": 0, "downs": 0, "pw": PW, "route_dev": "wlan1", "default_dev": "wlan0",
                       "home_ip": "192.168.1.20"})
    env = dict(os.environ, MOTIONWATCH_HOME=home, MW_FAKE_NET=os.path.join(tmp, "net.json"), H8_PW=PW,
               PATH=b + os.pathsep + os.environ.get("PATH", ""))
    r = subprocess.run([sys.executable, "-c", TEIL_A, datei], capture_output=True, text=True, timeout=600, env=env, cwd=tmp)
    e = next((json.loads(ln[4:]) for ln in r.stdout.splitlines() if ln.startswith("ERG ")), None)
    if e is None:
        print((r.stdout + r.stderr)[-4000:])
        ok(False, "Teil A lief nicht durch")
        return
    ok(PW not in r.stdout and PW not in r.stderr, "kein Passwort in der Ausgabe des Programms")
    n = e["nostick"]
    ok(n[0].startswith("A second Wi-Fi stick is needed") and n[2] is False and n[3] == n[0], "ohne 2. Stick: «%s»" % n[0])
    ok(n[1]["de"].startswith("Ein 2. WLAN-Stick ist nötig") and len({v for v in n[1].values()}) == 5, "Meldung in 5 Sprachen (%s)" % n[1]["de"])
    ok(e["nostick_calls"] == [], "ohne 2. Stick: kein nmcli / ip (%s)" % e["nostick_calls"][:3])
    ok(e["repeater"][0] == "" and "in use" in e["repeater"][1], "Stick im Repeater: «%s»" % e["repeater"][1])
    ok(e["src"].startswith("udp://127.0.0.1:") and "overrun_nonfatal=1" in e["src"], "Videoquelle %s" % e["src"])
    ok(e["frame"][0] and e["frame"][1] == [240, 320, 3], "Quelle liefert Bild %s (nach %s s)" % (e["frame"][1], e["frame"][2]))
    s = e["run"]
    ok(s[0] and s[1] and s[6] == "picture running" and s[7] == "wlan1" and s[8], "Zustand: %s" % s)
    ok(s[3] >= 3 and s[4] >= 3 and s[5] == 0, "Keep-alive läuft: %d gesendet, %d angekommen (vom Empfangs-Port), %d falsch" % (s[3], s[4], s[5]))
    ok(s[2] == 77, "Akku aus /gp/gpControl/status: %s" % s[2])
    ok("w 0072 03170101" in e["ble1"] and "r 0002" in e["ble1"] and "r 0003" in e["ble1"] and e["ble1"][0].startswith("connect"),
       "BLE: verbinden (wecken), WLAN ein, Name + Passwort lesen (%s)" % e["ble1"][:5])
    a = " ".join(e["nm_add"])
    ok("ifname wlan1" in a and "ipv4.never-default yes" in a and "802-11-wireless-security.psk-flags 2" in a
       and "ipv4.ignore-auto-dns yes" in a and "connection.autoconnect no" in a and "connection.interface-name wlan1" in a,
       "NetworkManager-Verbindung nur auf wlan1, ohne Standard-Route, Passwort nie gespeichert")
    up = e["nm_up"]
    ok(up[0] >= 1 and up[1] and up[2], "Verbinden: Passwort nur über stdin (passwd-file) %s" % up)
    b1 = e["break1"]
    ok(b1[0] >= 1 and b1[1] and b1[2] >= 1 and b1[3], "Abbruch → Neustart über die Vorschau (%s)" % b1)
    b2 = e["break2"]
    ok(b2[0] >= 1 and b2[1] and b2[2] >= 1, "Abbruch + GoPro antwortet nicht → WLAN neu, dann Bild (%s)" % b2)
    ok(e["frame_after"], "nach dem Neustart wieder ein Bild")
    ok(e["api_user"] == 403 and e["api_locked"] == 403, "API: nur Administrator, nicht im Bedienermodus")
    ok(e["api_get"][0] == 200 and e["api_get"][1] is True and e["api_get"][2] == "Bild läuft", "API GET: %s" % e["api_get"])
    ok(e["api_cmd"] is True and e["api_badcmd"] is False and e["api_badaddr"] == 400, "API: Aufnahme-Befehl ja, unbekannter Befehl / Adresse nein")
    st = e["stop"]
    ok(st[0] >= 1 and "w 0072 03170100" in st[1] and "w 0072 0105" in st[1] and st[2] == "Bluetooth link: off" and not st[3],
       "Stopp: WLAN getrennt, GoPro-WLAN aus, GoPro schläft (%s)" % st[1])
    ok(e["typed_pw"] is True and e["typed_frame"] is True, "BLE geht nicht, Passwort getippt → Bild (%s)" % e["typed_frame"])
    ok(e["no_ble_no_pw"] == "Bluetooth: no connection to the GoPro.", "BLE geht nicht, kein Passwort: «%s»" % e["no_ble_no_pw"])
    ok(e["route_guard"] != "", "Standard-Route auf dem Stick = Fehler (wlan0 bleibt)")
    ok(not e["pw_argv"] and e["pw_stdin_only_up"], "Passwort nie in argv, nur in stdin von «connection up»")
    ok(not e["pw_log"], "kein Passwort im Protokoll (%d Zeilen)" % len(e["logs"]))
    ok(not e["pw_api"], "kein Passwort in der API-Antwort")
    w = e["weg_ok"]
    ok(w[0] is True and w[1] is False and w[3] == "HERO8: Bluetooth + 2. WLAN-Stick (inoffiziell)", "Kern: Weg nur für HERO8, Titel «%s»" % w[3])
    ok(e["core_add"][0] is True, "Kern: gopro_add mit Weg hero8_ble (%s)" % e["core_add"])
    if e.get("core"):
        c = e["core"]
        ok(c[0] and c[1]["streamt"] and c[1]["akku"] == 77 and c[2] == "" and c[3] and c[4],
           "Kern: gopro_quelle → Start über BLE, gopro_open liefert Bild %s (%s)" % (c[3], c[1]))
        ok(e["core_stop"] == "Bluetooth link: off", "Kern: gopro_stop stoppt den Weg")
    ok(e["selftest"] is True, "Selbsttest-Funktion h8_selftest")


WRAP = r'''
import sys
D = sys.argv[1]
sys.argv = [D] + sys.argv[2:]
exec(compile(open(D, encoding="utf-8").read(), D, "exec"), {"__name__": "__main__", "__file__": D})
'''
WEB_PW = "h8-test-web-1"


def teil_b(datei, tmp, bilder):
    print("B) Schritt-Karte «HERO8 über Bluetooth» auf /gopro, 390 px dunkel + PC (MoveEye Demo)", flush=True)
    from playwright.sync_api import sync_playwright
    os.makedirs(bilder, exist_ok=True)
    tb = os.path.join(tmp, "b"); os.makedirs(tb)
    cfg = os.path.join(tb, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "theme": "dark", "detection_on": False, "track_person": False, "track_motion": False, "patrol": False, "net_mode": "client"}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tb, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tb, "log.txt"), "w")
    env = dict(os.environ, MOTIONWATCH_HOME=cfg)
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", WEB_PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tb, env=env)
    base = "http://127.0.0.1:%d" % port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tb, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        r = urllib.request.Request(base + "/api/gopro/hero8?lang=de",
                                   headers={"Authorization": "Basic " + base64.b64encode(("admin:" + WEB_PW).encode()).decode()})
        with op.open(r, timeout=30) as x:
            g = json.loads(x.read())
        ok(g.get("ok") and g.get("faehig") is False and "WLAN-Stick" in g.get("grund", ""), "API im Demo-Betrieb: «%s»" % g.get("grund"))
        r = urllib.request.Request(base + "/api/gopro", data=json.dumps({"action": "add", "name": "Hero 8 Zelt", "modell": "hero8", "weg": "hero8_ble", "lang": "de"}).encode(),
                                   headers={"Content-Type": "application/json", "Authorization": "Basic " + base64.b64encode(("admin:" + WEB_PW).encode()).decode()})
        with op.open(r, timeout=30) as x:
            q = json.loads(x.read())
        gid = q.get("id") or next((d["id"] for d in q.get("devs", []) if d.get("weg") == "hero8_ble"), "")
        ok(q.get("ok") and gid, "GoPro mit Weg hero8_ble angelegt (%s)" % {k: q.get(k) for k in ("ok", "error")})
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            for name, vp, mob in (("handy", {"width": 390, "height": 844}, True), ("pc", {"width": 1280, "height": 900}, False)):
                ctx = br.new_context(viewport=vp, device_scale_factor=2, is_mobile=mob, has_touch=mob, color_scheme="dark",
                                     http_credentials={"username": "admin", "password": WEB_PW}, locale="de-CH")
                pg = ctx.new_page()
                errs = []
                pg.on("pageerror", lambda e_: errs.append(str(e_)))
                pg.goto(base + "/gopro", wait_until="domcontentloaded")
                pg.wait_for_selector(".h8-slot .h8-box .h8-state", state="attached", timeout=30000)
                txt = pg.locator(".h8-slot").first.inner_text()
                ok("Hero 8 über Bluetooth (inoffiziell)" in txt and "Firmware-Update" in txt and "Ein 2. WLAN-Stick ist nötig" in txt
                   and "nie gespeichert" in txt, "%s: Feld mit Hinweisen (inoffiziell, Firmware, 2. Stick, Passwort)" % name)
                ok(pg.locator(".h8-pw").first.get_attribute("type") == "password", "%s: Passwort-Feld verdeckt" % name)
                w = pg.evaluate("() => document.documentElement.scrollWidth")
                ok(w <= vp["width"], "%s: keine waagrechte Bildlaufleiste (%d)" % (name, w))
                info = pg.locator('.gp-card[data-id="%s"] .gp-sec' % gid).first.inner_text()
                ok("HERO8: Bluetooth + 2. WLAN-Stick (inoffiziell)" in info, "%s: Karte nennt den Weg («%s»)" % (name, info))
                pg.wait_for_timeout(300)
                card = pg.locator('.gp-card[data-id="%s"]' % gid)
                card.scroll_into_view_if_needed()
                card.screenshot(path=os.path.join(bilder, "gopro_hero8_%s.png" % name))
                if name == "handy":
                    pg.screenshot(path=os.path.join(bilder, "gopro_hero8_%s_seite.png" % name), full_page=True)
                ok(not errs, "%s: keine JS-Fehler %s" % (name, errs[:3]))
                ctx.close()
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(10)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "gopro_hero8_bilder"))
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        print("ffmpeg fehlt"); return 1
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("GoPro-Hero-8-Test · " + os.path.basename(datei), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_h8_")
    try:
        teil_a(datei, tmp)
        if a.browser:
            teil_b(datei, tmp, a.bilder)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("GoPro-Hero-8-Test: " + ("OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
