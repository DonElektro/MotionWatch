#!/usr/bin/env python3
"""Test «📻 Radio» (MoveEye Teil 639zzzzd) – ohne das echte Internet, ohne Lautsprecher.

Ein falsches Verzeichnis (radio-browser.info nachgebaut: /json/servers, /json/stations/search, /json/stations/byuuid, /json/url)
und lokale Testströme (mit ffmpeg erzeugt: MP3 mit ICY-Titeln, Ogg über «ICY 200 OK» wie alte Shoutcast-Server, .pls / .m3u /
verschachtelt / .m3u8, Weiterleitung, ein Sender, der nie Ton schickt) laufen in diesem Prozess. MoveEye kommt nur an
127.0.0.1 (socket.create_connection / getaddrinfo ersetzt: alles andere = «kein Internet»). Der Lautsprecher ist ein kleines
Python-Programm (nimmt den Ton im Takt an wie aplay und schreibt Menge und Spitze in eine Datei).

  A) im eigenen Prozess (gebaute Datei geladen): Ab-Werk-Liste (Radio Pilatus ohne Adresse), Server-Liste mit User-Agent,
     suchen / hinzufügen / doppelt / falsche Adressen / ordnen / entfernen, Adresse beim Abspielen (uuid → /json/url, Ersatz
     byuuid, Pilatus über den Namen, uuid gemerkt), Wiedergabelisten, HLS, Weiterleitung; Abspielen mit Titel und
     Titelwechsel, Lautstärke (Spitze), Sirene / Ansage / Gegensprechen / Morse-Empfang mit Mikrofon pausieren das Radio
     und es spielt im selben Strom weiter; Einschlaf-Timer (leiser, dann aus); Stopp = keine Prozesse mehr; Wecker mit
     Radio, Ersatz-Ton ohne Internet und nach 10 s ohne Ton; ohne Internet: 5 Versuche mit wachsender Pause, dann Schluss;
     Rechte (ansehen / abspielen / Liste), Texte in 5 Sprachen, Favoriten-Einträge, Selbsttest-Funktion.
  C) Prozess-Lebenslauf: MoveEye wird mit kill -9 beendet – ffmpeg und der Lautsprecher gehen mit (PR_SET_PDEATHSIG).
  D) Pi-Fenster mit nachgebautem tkinter: Liste, ▶ / ⏹, Lautstärke, Schliessen.
  B) --browser: MoveEye (Demo) im Browser 390 px dunkel: Karte «spielt» mit Titel, Suche, hinzufügen, «Bearbeiten», Mehr
     (Zeile in «Unterwegs» mit dem Sender), 5 Sprachen, keine waagrechte Bildlaufleiste, keine JS-Fehler; Rechte über HTTP
     (Nur ansehen: 403, Familie: abspielen ja / Liste nein). --bilder ORDNER: radio_spielt.png, radio_suche.png, radio_mehr.png.

  python3 werkzeuge/radio_test.py [--datei X.py] [--browser] [--bilder ORDNER]
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
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
U_PIL = "11111111-2222-4333-8444-555555555551"
U_T1 = "11111111-2222-4333-8444-555555555552"
U_T2 = "11111111-2222-4333-8444-555555555553"
U_SIL = "11111111-2222-4333-8444-555555555554"
U_PX = "11111111-2222-4333-8444-555555555555"            # refuses browsers (only MoveEye gets the stream): the page needs the proxy


def ok(bed, text):
    print(("  ok     " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


# ---- test sounds and the fake directory / stations -------------------------------------------------------------------------------
def make_sounds(d):
    mp3, ogg = os.path.join(d, "ton.mp3"), os.path.join(d, "ton.ogg")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=6:sample_rate=44100", "-af", "volume=0.5",
                    "-ac", "1", "-c:a", "libmp3lame", "-b:a", "64k", mp3], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=660:duration=6:sample_rate=44100", "-af", "volume=0.5",
                    "-ac", "1", "-c:a", "libvorbis", "-q:a", "2", ogg], check=True)
    return open(mp3, "rb").read(), open(ogg, "rb").read()


class Srv:
    def __init__(self, mp3, ogg):
        self.mp3, self.ogg, self.hits, self.url500, self.conns = mp3, ogg, [], False, {}
        me = self
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0)); self.dead = s.getsockname()[1]          # a port where nobody listens
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.base = "http://127.0.0.1:%d" % self.port
        B = self.base
        self.db = [{"stationuuid": U_PIL, "name": "Radio Pilatus", "countrycode": "CH", "country": "Switzerland", "codec": "MP3", "bitrate": 64,
                    "tags": "pop", "url": B + "/pilatus.pls", "url_resolved": B + "/pilatus.pls", "lastcheckok": 1},
                   {"stationuuid": "11111111-2222-4333-8444-555555555559", "name": "Radio Pilatus Classic", "countrycode": "CH", "country": "Switzerland",
                    "codec": "MP3", "bitrate": 128, "tags": "", "url": B + "/x", "url_resolved": B + "/x", "lastcheckok": 1},
                   {"stationuuid": U_T1, "name": "Test FM", "countrycode": "CH", "country": "Switzerland", "codec": "MP3", "bitrate": 64, "tags": "test,<b>x</b>",
                    "url": B + "/stream.mp3", "url_resolved": B + "/stream.mp3", "lastcheckok": 1},
                   {"stationuuid": U_T2, "name": "Test Ogg <script>", "countrycode": "DE", "country": "Germany", "codec": "OGG", "bitrate": 0, "tags": "",
                    "url": B + "/list.m3u", "url_resolved": B + "/list.m3u", "lastcheckok": 1},
                   {"stationuuid": U_SIL, "name": "Silent Test", "countrycode": "CH", "country": "Switzerland", "codec": "MP3", "bitrate": 64, "tags": "",
                    "url": B + "/hang", "url_resolved": B + "/hang", "lastcheckok": 1},
                   {"stationuuid": U_PX, "name": "Proxy FM", "countrycode": "CH", "country": "Switzerland", "codec": "MP3", "bitrate": 64, "tags": "",
                    "url": B + "/stream_ua.mp3", "url_resolved": B + "/stream_ua.mp3", "lastcheckok": 1}]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def _handler(self):
        me = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def log_message(self, *a):
                pass

            def j(self, obj, code=200):
                b = json.dumps(obj).encode()
                self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers()
                self.wfile.write(b)

            def txt(self, body, ct):
                b = body.encode()
                self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

            def do_GET(self):
                from urllib.parse import urlsplit, parse_qs
                u = urlsplit(self.path); p = u.path; q = parse_qs(u.query)
                me.hits.append((p, self.headers.get("User-Agent") or "", self.headers.get("Icy-MetaData") or "", u.query))
                B = me.base
                if p == "/json/servers":
                    return self.j([{"name": "127.0.0.1:%d" % me.port, "ip": "127.0.0.1"}])
                if p == "/json/stations/search":
                    name = (q.get("name") or [""])[0].lower(); cc = (q.get("countrycode") or [""])[0]
                    return self.j([s for s in me.db if name in s["name"].lower() and (not cc or s["countrycode"] == cc)])
                m = re.match(r"^/json/stations/byuuid/([0-9a-f-]+)$", p)
                if m:
                    return self.j([s for s in me.db if s["stationuuid"] == m.group(1)])
                m = re.match(r"^/json/url/([0-9a-f-]+)$", p)
                if m:
                    if me.url500:
                        self.send_response(500); self.end_headers(); return
                    s = next((s for s in me.db if s["stationuuid"] == m.group(1)), None)
                    return self.j({"ok": bool(s), "url": s["url_resolved"] if s else ""})
                if p == "/pilatus.pls":
                    return self.txt("[playlist]\nNumberOfEntries=1\nFile1=%s/stream.mp3\nTitle1=Pilatus\nLength1=-1\nVersion=2\n" % B, "audio/x-scpls")
                if p == "/list.m3u":
                    return self.txt("#EXTM3U\n#EXTINF:-1,inner\ninner.pls\n", "audio/x-mpegurl")
                if p == "/inner.pls":
                    return self.txt("[playlist]\nFile1=%s/dead\nFile2=/stream.ogg\n" % ("http://127.0.0.1:%d" % me.dead), "audio/x-scpls")
                if p == "/live.m3u8":
                    return self.txt("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg1.aac\n", "application/vnd.apple.mpegurl")
                if p == "/redir":
                    self.send_response(302); self.send_header("Location", "/stream.mp3"); self.end_headers(); return
                if p == "/hang":
                    self.wfile.write(b"HTTP/1.0 200 OK\r\nContent-Type: audio/mpeg\r\n\r\n"); self.wfile.flush()
                    time.sleep(25); return
                if p == "/stream_ua.mp3" and "MoveEye" not in (self.headers.get("User-Agent") or ""):
                    me.conns["refused"] = me.conns.get("refused", 0) + 1
                    self.send_response(403); self.send_header("Content-Length", "0"); self.end_headers(); return
                if p in ("/stream.mp3", "/stream.ogg", "/stream_ua.mp3"):
                    me.conns[p] = me.conns.get(p, 0) + 1
                    return self.stream(p)
                self.send_response(404); self.end_headers()

            def stream(self, p):
                icy = self.headers.get("Icy-MetaData") == "1" and p != "/stream.ogg"
                data = me.ogg if p == "/stream.ogg" else me.mp3
                mi = 4000
                if p != "/stream.ogg":
                    p = "/stream.mp3"
                if p == "/stream.ogg":                     # an old Shoutcast server: «ICY 200 OK»
                    head = "ICY 200 OK\r\nicy-name:Test Ogg\r\nContent-Type: application/ogg\r\n\r\n"
                else:
                    head = "HTTP/1.0 200 OK\r\nContent-Type: audio/mpeg\r\nicy-name:Test FM\r\n" + ("icy-metaint:%d\r\n" % mi if icy else "") + "\r\n"
                try:
                    self.wfile.write(head.encode()); self.wfile.flush()
                    rate = 8000 if p == "/stream.mp3" else 6000      # bytes per second (64 kbit/s; the Ogg about 48)
                    t0, sent, pos, n_meta = time.time(), 0, 0, 0
                    buf = b""
                    while True:
                        want = int((time.time() - t0 + 1.0) * rate) - sent    # one second ahead, then in time
                        if want <= 0:
                            time.sleep(0.05); continue
                        chunk = b""
                        while len(chunk) < want:
                            take = data[pos:pos + want - len(chunk)]
                            chunk += take; pos = (pos + len(take)) % len(data)
                        sent += len(chunk)
                        if not icy:
                            self.wfile.write(chunk); self.wfile.flush(); continue
                        buf += chunk
                        while len(buf) >= mi:
                            self.wfile.write(buf[:mi]); buf = buf[mi:]
                            song = 1 + int((time.time() - t0) / 3.0) % 2
                            meta = ("StreamTitle='Test Artist - Song %d';StreamUrl='';" % song).encode() if n_meta % 2 == 0 else b""
                            n_meta += 1
                            if meta:
                                meta += b"\x00" * ((16 - len(meta) % 16) % 16)
                            self.wfile.write(bytes([len(meta) // 16]) + meta)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
        return H


SINK = r'''
import array, os, sys, time
d, rate = sys.argv[1], int(sys.argv[2])
f = os.path.join(d, "sink_%d_%d.txt" % (rate, os.getpid()))
tot, t0 = 0, time.time()
while True:
    b = sys.stdin.buffer.read(rate // 5 * 2)
    if not b:
        break
    a = array.array("h"); a.frombytes(b[:len(b) // 2 * 2])
    tot += len(b)
    with open(f + ".tmp", "w") as w:
        w.write("%d %d %.2f" % (tot, max((abs(x) for x in a), default=0), time.time()))
    os.replace(f + ".tmp", f)
    ahead = tot / (2.0 * rate) - (time.time() - t0)
    if ahead > 0.3:
        time.sleep(ahead - 0.3)
'''

# the common patches for MoveEye in a test process: only 127.0.0.1, «aplay» = the sink above
PATCH = r'''
import socket as _s_, shutil as _sh_, sys as _sy_, os as _o_
_RT_ALLOW = ("127.0.0.1", "localhost", "::1", "0.0.0.0", None, "")
_RT_BLOCKED = []
_rt_cc, _rt_ga = _s_.create_connection, _s_.getaddrinfo
def _rt_guard_cc(addr, *a, **k):
    if addr[0] not in _RT_ALLOW:
        _RT_BLOCKED.append(str(addr[0])); raise _s_.gaierror(-2, "radio_test: no internet for " + str(addr[0]))
    return _rt_cc(addr, *a, **k)
def _rt_guard_ga(host, *a, **k):
    if host not in _RT_ALLOW:
        _RT_BLOCKED.append(str(host)); raise _s_.gaierror(-2, "radio_test: no internet for " + str(host))
    return _rt_ga(host, *a, **k)
_s_.create_connection, _s_.getaddrinfo = _rt_guard_cc, _rt_guard_ga
_rt_which = _sh_.which
_sh_.which = lambda c, *a, **k: "/usr/bin/true" if c == "aplay" else _rt_which(c, *a, **k)
def out_cmd(rate, connect=True):
    return [_sy_.executable, _o_.environ["MW_RT_SINK"], _o_.environ["MW_RT_DIR"], str(rate), "mwradiosink"], ""
'''


def children(pid):
    out = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            st = open("/proc/%s/stat" % d).read()
            ppid = int(st.rsplit(")", 1)[1].split()[1])
            cmd = open("/proc/%s/cmdline" % d, "rb").read().replace(b"\0", b" ").decode(errors="replace")
        except (OSError, ValueError, IndexError):
            continue
        if ppid == pid and ("ffmpeg" in cmd or "mwradiosink" in cmd):
            out.append((int(d), "ffmpeg" if "ffmpeg" in cmd else "sink:" + cmd.split("mwradiosink")[0].split()[-1]))
    return out


TEIL_A = r'''
import json, os, sys, threading, time, wave
import numpy as np
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
src = src[:i] + "\n" + os.environ["MW_RT_PATCH"] + src[i:]
ns = {"__name__": "mw_radio_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src, sys.argv[1], "exec"), ns)
B = os.environ["MW_RT_BASE"]; D = os.environ["MW_RT_DIR"]; DEAD = int(os.environ["MW_RT_DEAD"])
C, R = ns["CFG"], ns["RADIO"]
C.update(lang="de", audio_out="default", audio_in="", radio_volume=40, wake_volume=50, morse_rx_sound=False)
out, logs = {}, []
_lg = ns["log_event"]
def lg(kind, text):
    logs.append(str(text)); return _lg(kind, text)
ns["log_event"] = lg
sounds = []
_sp = ns["sound_play"]
def sp(kind=None, seconds=None, volume=None, reason="test"):
    sounds.append((kind, reason)); return _sp(kind, seconds, volume, reason)
ns["sound_play"] = sp
do = lambda d, **k: ns["radio_do"](d, "test", **k)
me = os.getpid()
def kids():
    res = []
    for d in os.listdir("/proc"):
        if not d.isdigit(): continue
        try:
            st = open("/proc/%s/stat" % d).read(); ppid = int(st.rsplit(")", 1)[1].split()[1])
            cmd = open("/proc/%s/cmdline" % d, "rb").read().replace(b"\0", b" ").decode(errors="replace")
        except Exception: continue
        if ppid == me and ("ffmpeg" in cmd or "mwradiosink" in cmd):
            res.append("ffmpeg" if "ffmpeg" in cmd else "sink" + cmd.split("mwradiosink")[0].split()[-1])
    return sorted(res)
def wait(f, s):
    t0 = time.time()
    while time.time() - t0 < s:
        if f(): return round(time.time() - t0, 1)
        time.sleep(0.1)
    return None
def sinkpk(rate=44100):
    best = None
    for f in os.listdir(D):
        if f.startswith("sink_%d_" % rate) and f.endswith(".txt"):
            try:
                tot, pk, t = open(os.path.join(D, f)).read().split()
            except ValueError: continue
            if best is None or float(t) > best[2]: best = (int(tot), int(pk), float(t))
    return best
# 1 the list of the factory, the directory
out["default"] = ns["radio_list"]()
out["servers"] = ns["radio_servers"](True)
c, a = do({"action": "search", "q": "test"}); out["search"] = [c, [h["name"] for h in a.get("hits") or []], [h["tags"] for h in a.get("hits") or []]]
c, a = do({"action": "search", "q": "x"}); out["search_short"] = [c, a.get("error")]
r = []
for d_ in ({"action": "add", "uuid": U_T1}, {"action": "add", "uuid": U_T1}, {"action": "add", "uuid": U_T2},
           {"action": "add", "url": B + "/list.m3u", "name": "Meine Liste"}, {"action": "add", "url": "file:///etc/passwd"},
           {"action": "add", "url": "javascript:alert(1)"}, {"action": "add", "url": "http://user:pw@127.0.0.1/x"}, {"action": "add", "uuid": "nope"},
           {"action": "add", "uuid": "11111111-2222-4333-8444-000000000000"}):
    c, a = do(d_); r.append([c, a.get("error")])
out["add"] = r
ids = [e["id"] for e in ns["radio_list"]()]
out["ids"] = ids; out["names"] = [e["name"] for e in ns["radio_list"]()]
do({"action": "move", "id": ids[2], "by": -1}); out["moved"] = [e["id"] for e in ns["radio_list"]()]
do({"action": "move", "id": ids[2], "by": 1})
uid = ids[3]
do({"action": "remove", "id": uid}); out["removed"] = [e["id"] for e in ns["radio_list"]()]
c, a = do({"action": "remove", "id": "zzz"}); out["remove_bad"] = c
T1 = next(e["id"] for e in ns["radio_list"]() if e.get("uuid") == U_T1)
# 2 the address at play time
pil = ns["radio_station"]("pilatus")
u = ns["radio_resolve"](pil); out["pil"] = [u, pil.get("uuid"), C["radio_stations"][0].get("uuid")]
src = ns["radio_open"](u); out["pil_open"] = [src["kind"], src["url"], src["metaint"]]; src["sock"].close()
src = ns["radio_open"](B + "/list.m3u"); out["nested"] = [src["kind"], src["url"], src["ct"]]; src["sock"].close()
out["hls"] = ns["radio_open"](B + "/live.m3u8")["kind"]
src = ns["radio_open"](B + "/redir"); out["redir"] = src["url"]; src["sock"].close()
open(os.path.join(D, "url500"), "w").write("1")
time.sleep(0.2)
out["byuuid"] = ns["radio_resolve"]({"uuid": U_T1})
os.remove(os.path.join(D, "url500")); time.sleep(0.2)
try:
    ns["radio_open"](B + "/nothing"); out["e404"] = "no error"
except Exception as e:
    out["e404"] = str(e)
# 3 play: title, title change, sound at the sink, volume
c, a = do({"action": "play", "id": T1}); out["play"] = c
out["t_play"] = wait(lambda: R["state"] == "playing" and sinkpk() is not None, 15)
out["t_title"] = wait(lambda: "Song" in R["title"], 10); t1 = R["title"]
out["t_change"] = wait(lambda: R["title"] and R["title"] != t1, 10); out["titles"] = [t1, R["title"]]
out["kids_play"] = kids()
time.sleep(1.5); pk40 = sinkpk()[1]
do({"action": "volume", "v": 10}); time.sleep(2.0); pk10 = sinkpk()[1]
do({"action": "volume", "v": 40}); out["vol"] = [pk40, pk10, C["radio_volume"]]
# 4 priority: siren, announcement, talking, Morse with the microphone
def held_cycle(start, label, stop=None):
    n0 = len([f for f in os.listdir(D) if f.startswith("sink_44100_")])
    start()
    t_h = wait(lambda: R["held"] == label and R["out"] is None, 3)
    txt = ns["radio_state"]("de")["held"]
    if stop: stop()
    t_r = wait(lambda: not R["held"] and R["out"] is not None and R["out"].poll() is None, 12)
    grew = wait(lambda: len([f for f in os.listdir(D) if f.startswith("sink_44100_")]) > n0, 3) is not None   # the new sink writes after 0.2 s
    return [t_h, txt, t_r, grew, R["state"]]
out["siren"] = held_cycle(lambda: ns["sound_play"]("siren", 1.5, 50, reason="person alarm"), "siren")
w = wave.open(ns["TTS"]["file"], "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
w.writeframes((np.sin(np.arange(16000) / 16000 * 2 * np.pi * 300) * 8000).astype("<i2").tobytes()); w.close()
out["voice"] = held_cycle(lambda: ns["sound_play"]("tts", 1.0, None, reason="test"), "voice")
out["talk"] = held_cycle(lambda: ns["talk_chunk"](bytes(6400), "test"), "talk")
def mic_on():
    ns["MORSE"]["until"] = time.time() + 60; C["morse_rx_sound"] = True
def mic_off():
    time.sleep(1.0); ns["MORSE"]["until"] = 0.0; C["morse_rx_sound"] = False
out["mic"] = held_cycle(mic_on, "mic", mic_off)
out["held_en"] = ns["tr"](ns["_RADIO_HELD_TXT"]["mic"], "en")
# 5 sleep timer
c, a = do({"action": "sleep", "min": 15}); out["sleep15"] = [c, a["state"]["sleep"]["min"], a["state"]["sleep"]["left"]]
c, a = do({"action": "sleep", "min": 7}); out["sleep7"] = c
R["sleep_until"] = time.time() + 3.0
out["fade"] = wait(lambda: 0.0 < R["fade"] < 0.5, 4)
out["sleep_end"] = [wait(lambda: not R["want"] and R["state"] == "off", 8), R["msg"], any("sleep timer" in x for x in logs)]
out["kids_sleep"] = wait(lambda: not kids(), 4); out["kids_sleep_l"] = kids()
# 6 play / stop: no processes, no threads left
do({"action": "play", "id": "pilatus"})
out["pil_play"] = [wait(lambda: R["state"] == "playing", 15), R["name"]]
out["kids2"] = kids()
c, a = do({"action": "stop"}); out["stop"] = [c, wait(lambda: not kids(), 4), kids(), [t.name for t in threading.enumerate() if t.name.startswith("radio")]]
c, a = do({"action": "toggle"}); out["toggle_on"] = [c, R["want"]]
wait(lambda: R["state"] == "playing", 15)
c, a = do({"action": "toggle"}); out["toggle_off"] = [c, R["want"], wait(lambda: not kids(), 4)]
# 7 the wake-up alarm with the radio
out["pairs"] = [p for p in ns["text_choice_pairs"]("wake_sound") if p[0].startswith("radio:")]
def ring(kind, secs, until):
    sounds.clear(); C["wake_sound"] = kind
    ns["wake_ring"](True, "test"); t0 = time.time(); got = None
    while time.time() - t0 < secs:
        ns["wake_tick"]()
        if got is None and until():
            got = round(time.time() - t0, 1)
        time.sleep(0.25)
    res = [got, [s for s in sounds], R["wake"], R["want"], round(R["wvol"])]
    ns["wake_stop"]("test")
    res.append(wait(lambda: not kids() and not R["want"], 4))
    return res
out["wake_radio"] = ring("radio:" + T1, 6, lambda: R["wake"] and R["state"] == "playing")
c, a = do({"action": "add", "url": "http://nohost.invalid/live", "name": "Kein Netz"}); NO = [e["id"] for e in ns["radio_list"]() if e["name"] == "Kein Netz"][0]
out["wake_nonet"] = ring("radio:" + NO, 4, lambda: any(s[0] == "chime" for s in sounds))
c, a = do({"action": "add", "uuid": U_SIL}); SIL = [e["id"] for e in ns["radio_list"]() if e.get("uuid") == U_SIL][0]
out["wake_silent"] = ring("radio:" + SIL, 15, lambda: any(s[0] == "chime" for s in sounds))
C["wake_sound"] = "chime"
# 8 without internet: a few tries with longer pauses, then the end
ns["RADIO_BACKOFF"] = (0.4, 0.8, 1.6)
R["tries"].clear()
do({"action": "play", "id": NO})
st_retry = None
t0 = time.time()
while time.time() - t0 < 10 and R["want"]:
    s = ns["radio_state"]("de")
    if s["state"] == "retry" and st_retry is None: st_retry = s
    time.sleep(0.05)
tries = [t for t, _e in R["tries"]]
s = ns["radio_state"]("de")
out["nonet"] = [len(tries), [round(b - a_, 1) for a_, b in zip(tries, tries[1:])], s["state"], s["offline"], s["msg"], st_retry and st_retry["retry"], st_retry and st_retry["offline"]]
time.sleep(2.5); out["nonet_after"] = len(R["tries"])
c, a = do({"action": "add", "url": "http://127.0.0.1:%d/live" % DEAD, "name": "Tot"}); TOT = [e["id"] for e in ns["radio_list"]() if e["name"] == "Tot"][0]
R["tries"].clear(); do({"action": "play", "id": TOT}); wait(lambda: not R["want"], 10)
s = ns["radio_state"]("de"); out["dead"] = [len(R["tries"]), s["state"], s["offline"], s["msg"]]
ns["RADIO_BACKOFF"] = (5.0, 10.0, 20.0, 40.0, 80.0)
# 9 rights
ra = ns["role_allows"]
out["rights"] = {"view_get": ra("view", "/api/radio", "GET", {}), "view_page": ra("view", "/radio", "GET", {}), "view_play": ra("view", "/api/radio", "POST", {"action": "play"}),
                 "family_play": ra("family", "/api/radio", "POST", {"action": "play"}), "family_stop": ra("family", "/api/radio", "POST", {"action": "stop"}),
                 "family_add": ra("family", "/api/radio", "POST", {"action": "add"}), "family_search": ra("family", "/api/radio", "POST", {"action": "search"}),
                 "friend_play": ra("friend", "/api/radio", "POST", {"action": "play"}), "custom_siren": ra("custom", "/api/radio", "POST", {"action": "volume"}, {"siren"}),
                 "custom_none": ra("custom", "/api/radio", "POST", {"action": "volume"}, {"live"})}
out["rights_do"] = [do({"action": "add", "uuid": U_T2}, role="family")[0], do({"action": "volume", "v": 33}, role="family")[0], do({"action": "play"}, role="view")[0],
                    ns["radio_state"]("de", "view")["may"], ns["radio_state"]("de", "family")["may"]]
C["lock_on"] = True; out["rights_lock"] = [do({"action": "remove", "id": T1})[0], do({"action": "volume", "v": 40})[0]]; C["lock_on"] = False
# 10 texts, favourites, the self-test
out["txt"] = {L: [ns["tr"]("Radio as wake-up alarm", L), ns["tr"]("No internet - the radio needs a connection.", L), ns["radio_tr"]("the station does not answer: HTTP 500", L)]
              for L in ("de", "en", "fr", "it", "rm")}
out["fav"] = [x["k"] for x in ns["radio_fav_items"]("de")]
# «📱 dieser Browser»: the address for the page, the proxy (only stations of the list, at most 2 listeners)
c, a = do({"action": "bplay", "id": "pilatus"}); out["bplay"] = [c, a.get("src")]
c, a = do({"action": "bplay", "id": "pilatus"}, role="view"); out["bplay_view"] = c
px = [ns["radio_br_proxy"]("pilatus") for _i in range(3)]
it0 = iter(px[0][2]) if px[0][2] is not None else iter([b""])      # keep the iterator (werkzeug keeps it while it sends)
first = next(it0)
out["proxy"] = [[x[0], x[1]] for x in px] + [len(first) > 1000, ns["BR"]["n"]]
for x in px:
    if x[2] is not None: x[2].close()
out["proxy_after"] = ns["BR"]["n"]
out["proxy_bad"] = [ns["radio_br_proxy"](x)[0] for x in ("nichtda", "../etc", "http://example.com/x", "")]
C["radio_stations"].append({"id": "hlsx", "name": "HLS", "url": B + "/live.m3u8"})
out["proxy_hls"] = ns["radio_br_proxy"]("hlsx")[0]; C["radio_stations"].pop()
time.sleep(0.5); out["proxy_end"] = ns["BR"]["n"]
do({"action": "bstop"})
q0 = ns["radio_state"]("de")["quiet"]; C["clap_on"] = True; q1 = ns["radio_state"]("de")["quiet"]; C["clap_on"] = False; C["noise_alarm"] = True
out["quiet"] = [q0, q1, ns["radio_state"]("de")["quiet"]]; C["noise_alarm"] = False
out["icons"] = ['📡 Phone radio' in ns["MORSE_PAGE"], '📻 Phone radio' in ns["MORSE_PAGE"], "📡 Eigenes Protokoll" in ns["_HELP_MORSE"]["de"]]
out["help"] = ['id="radio"' in ns["HELP_PAGE"], 'href="/radio"' in ns["MORE_PAGE"]]
out["selftest"] = ns["radio_selftest"]()
out["blocked"] = sorted(set(ns["_RT_BLOCKED"]))
out["kids_end"] = kids()
print("ERG " + json.dumps(out, ensure_ascii=False, default=str), flush=True)
os._exit(0)
'''


def env_for(tmp, srv, home):
    sink = os.path.join(tmp, "sink.py")
    if not os.path.isfile(sink):
        open(sink, "w").write(SINK)
    e = dict(os.environ, MOTIONWATCH_HOME=home, MW_RT_SINK=sink, MW_RT_DIR=os.path.join(tmp, "snd"), MW_RT_PATCH=PATCH, MW_RT_BASE=srv.base,
             MW_RT_DEAD=str(srv.dead), MW_RADIO_DISCOVER=srv.base, NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):   # no way out (MoveEye only reaches 127.0.0.1 anyway)
        e[k] = "http://127.0.0.1:9"
    os.makedirs(e["MW_RT_DIR"], exist_ok=True)
    return e


def teil_a(datei, tmp, srv):
    print("A) Radio im eigenen Prozess (falsches Verzeichnis, lokale Testströme)", flush=True)
    home = os.path.join(tmp, "a"); os.makedirs(home)
    env = env_for(tmp, srv, home)
    code = TEIL_A.replace("U_T1", repr(U_T1)).replace("U_T2", repr(U_T2)).replace("U_SIL", repr(U_SIL))
    stop = threading.Event()

    def url500():                                         # the child switches /json/url to «500» with a file
        while not stop.is_set():
            srv.url500 = os.path.isfile(os.path.join(env["MW_RT_DIR"], "url500"))
            time.sleep(0.05)
    threading.Thread(target=url500, daemon=True).start()
    t0 = time.time()
    r = subprocess.run([sys.executable, "-c", code, datei], capture_output=True, text=True, timeout=900, env=env, cwd=tmp)
    stop.set()
    erg = next((json.loads(ln[4:]) for ln in r.stdout.splitlines() if ln.startswith("ERG ")), None)
    if erg is None:
        print((r.stdout + r.stderr)[-4000:])
        ok(False, "Teil A lief nicht durch")
        return
    print("  (Teil A: %.0f s)" % (time.time() - t0))
    e = erg
    d0 = e["default"]
    ok(len(d0) == 1 and d0[0]["name"] == "Radio Pilatus" and "url" not in d0[0] and d0[0].get("find", {}).get("cc") == "CH",
       "ab Werk: Radio Pilatus, ohne eingebaute Adresse (über den Namen im Verzeichnis) %s" % d0)
    ok(e["servers"] == [srv.base], "Server-Liste über /json/servers: %s" % e["servers"])
    uas = {h[1] for h in srv.hits if h[0].startswith("/json/")}
    ok(uas and all(re.match(r"^MoveEye/\d+\.\d+\.\d+ \(internet radio", u) for u in uas), "User-Agent: %s" % sorted(uas))
    ok(e["search"][0] == 200 and {"Test FM", "Test Ogg <script>"} <= set(e["search"][1]), "suchen «test»: %s" % e["search"][1])
    ok(e["search_short"][0] == 400 and "2 Buchstaben" in (e["search_short"][1] or ""), "zu kurz: %s" % e["search_short"][1])
    a = e["add"]
    ok(a[0][0] == 200 and a[1] == [400, "der Sender ist schon in der Liste"] and a[2][0] == 200 and a[3][0] == 200, "hinzufügen / doppelt: %s" % a[:4])
    ok(all(x[0] == 400 for x in a[4:8]) and "keine gültige Adresse" in (a[4][1] or "") and a[8] == [400, "der Sender ist nicht im Verzeichnis"],
       "falsche Adressen (file:, javascript:, Passwort in der Adresse, keine uuid, unbekannte uuid): %s" % a[4:])
    ok(e["names"][:3] == ["Radio Pilatus", "Test FM", "Test Ogg <script>"] and e["names"][3] == "Meine Liste", "Liste: %s" % e["names"])
    ok(e["moved"][:3] == [e["ids"][0], e["ids"][2], e["ids"][1]], "ordnen: %s" % e["moved"])
    ok(e["ids"][3] not in e["removed"] and len(e["removed"]) == 3 and e["remove_bad"] == 400, "entfernen: %s" % e["removed"])
    ok(e["pil"][0] == srv.base + "/pilatus.pls" and e["pil"][1] == U_PIL and e["pil"][2] == U_PIL, "Pilatus über den Namen gefunden, uuid gemerkt: %s" % e["pil"])
    ok(any(h[0] == "/json/stations/search" and "countrycode=CH" in h[3] for h in srv.hits) and any(h[0] == "/json/url/" + U_PIL for h in srv.hits),
       "Suche mit Land CH, danach /json/url/<uuid> (zählt den Klick)")
    ok(e["pil_open"] == ["icy", srv.base + "/stream.mp3", 4000], ".pls → MP3-Strom mit ICY: %s" % e["pil_open"])
    ok(e["nested"] == ["icy", srv.base + "/stream.ogg", "application/ogg"], ".m3u → .pls → toter Eintrag übersprungen → Ogg «ICY 200 OK»: %s" % e["nested"])
    ok(e["hls"] == "hls" and e["redir"] == srv.base + "/stream.mp3" and "404" in e["e404"], "HLS erkannt, Weiterleitung, 404: %s %s %s" % (e["hls"], e["redir"], e["e404"]))
    ok(e["byuuid"] == srv.base + "/stream.mp3", "/json/url antwortet 500 → byuuid url_resolved: %s" % e["byuuid"])
    ok(e["play"] == 200 and e["t_play"] is not None and e["t_play"] < 10, "Abspielen: Ton nach %s s" % e["t_play"])
    ok(e["t_title"] is not None and e["titles"][0].startswith("Test Artist - Song") and e["t_change"] is not None, "ICY-Titel %s, Wechsel nach %s s" % (e["titles"], e["t_change"]))
    ok(e["kids_play"] == ["ffmpeg", "sink44100"], "Prozesse beim Abspielen: %s" % e["kids_play"])
    v = e["vol"]
    ok(v[0] > 150 and v[1] < v[0] / 8 and v[2] == 40, "Lautstärke 40 %% → 10 %%: Spitze %d → %d" % (v[0], v[1]))
    for k, lab in (("siren", "Sirene"), ("voice", "Ansage"), ("talk", "Gegensprechen"), ("mic", "Mikrofon")):
        h = e[k]
        ok(h[0] is not None and h[0] < 1.0 and h[2] is not None and h[3] and h[4] == "playing",
           "%s: Radio pausiert nach %s s («%s»), spielt nach %s s weiter (%s)" % (lab, h[0], h[1], h[2], h[3:]))
    ok("Sirene" in e["siren"][1] and "Ansage" in e["voice"][1] and "spricht" in e["talk"][1] and "Mikrofon" in e["mic"][1] and "Rückkopplung" in e["mic"][1],
       "Hinweise auf der Karte: %s" % [e[k][1] for k in ("siren", "voice", "talk", "mic")])
    ok(srv.conns.get("/stream.mp3", 0) >= 1, "Strom verbunden (%s Verbindungen)" % srv.conns)
    ok(e["sleep15"][0] == 200 and e["sleep15"][1] == 15 and 890 <= e["sleep15"][2] <= 900 and e["sleep7"] == 400, "Einschlaf-Timer 15 min (%s), 7 min abgelehnt" % e["sleep15"])
    ok(e["fade"] is not None and e["sleep_end"][0] is not None and e["sleep_end"][2] and e["kids_sleep"] is not None,
       "Timer: leiser nach %s s, aus nach %s s, keine Prozesse (%s)" % (e["fade"], e["sleep_end"][0], e["kids_sleep_l"]))
    ok(e["pil_play"][0] is not None and e["pil_play"][1] == "Radio Pilatus" and e["kids2"] == ["ffmpeg", "sink44100"], "Radio Pilatus spielt (%s)" % e["pil_play"])
    ok(e["stop"][0] == 200 and e["stop"][1] is not None and not e["stop"][2] and not e["stop"][3], "Stopp: keine Prozesse, keine Threads (%s)" % e["stop"])
    ok(e["toggle_on"] == [200, True] and e["toggle_off"][:2] == [200, False] and e["toggle_off"][2] is not None, "Schalter «Radio ein / aus» (toggle)")
    ok(len(e["pairs"]) >= 3 and e["pairs"][0][1] == "📻 Radio Pilatus", "Weckton-Auswahl: %s" % e["pairs"][:3])
    w = e["wake_radio"]
    ok(w[0] is not None and w[0] < 8 and not any(s[0] == "chime" for s in w[1]) and w[2] and 18 <= w[4] <= 30 and w[5] is not None,
       "Wecker mit Radio: spielt nach %s s, kein Ersatz-Ton, leise anfangen (%s %%), aus = keine Prozesse" % (w[0], w[4]))
    w = e["wake_nonet"]
    ok(w[0] is not None and w[0] < 2.5 and [s[0] for s in w[1]].count("chime") == 1, "Wecker ohne Internet: Ersatz-Ton nach %s s (%s)" % (w[0], w[1]))
    w = e["wake_silent"]
    ok(w[0] is not None and 9.0 <= w[0] <= 13.5 and [s[0] for s in w[1]].count("chime") >= 1, "Wecker, Sender ohne Ton: Ersatz-Ton nach %s s" % w[0])
    n = e["nonet"]
    ok(n[0] == 4 and len(n[1]) == 3 and n[1][0] < n[1][1] < n[1][2] and n[2] == "offline" and n[3] and "kein internet" in ns_txt(n[4]).lower(),
       "ohne Internet: %d Versuche, Pausen %s s, dann «%s» (%s)" % (n[0], n[1], n[2], n[4]))
    ok(n[5] and n[5]["max"] == 4 and n[6], "Karte während der Pause: nächster Versuch / Zähler %s, Hinweis «Kein Internet»" % n[5])
    ok(e["nonet_after"] == 4, "danach keine weiteren Versuche (%d)" % e["nonet_after"])
    ok(e["dead"][1] == "error" and not e["dead"][2] and "antwortet nicht" in e["dead"][3], "Sender aus (Port zu): kein «kein Internet», sondern «%s»" % e["dead"][3])
    r_ = e["rights"]
    ok(r_ == {"view_get": True, "view_page": True, "view_play": False, "family_play": True, "family_stop": True, "family_add": False, "family_search": False,
              "friend_play": False, "custom_siren": True, "custom_none": False}, "Rechte: %s" % r_)
    rd = e["rights_do"]
    ok(rd[0] == 403 and rd[1] == 200 and rd[2] == 403 and rd[3] == {"play": False, "edit": False} and rd[4] == {"play": True, "edit": False}, "radio_do mit Rollen: %s" % rd)
    ok(e["rights_lock"] == [403, 200], "Bedienermodus: Liste gesperrt, Lautstärke geht (%s)" % e["rights_lock"])
    for L, (w_, n_, s_) in e["txt"].items():
        ok(w_ and n_ and s_.endswith(": HTTP 500") and (L == "en" or (w_ != "Radio as wake-up alarm" and not s_.startswith("the station"))), "%s: «%s» · «%s» · «%s»" % (L, w_, n_, s_))
    ok(e["fav"][:2] == ["page:/radio", "radio:on"] and all(k.startswith("radio:play:") for k in e["fav"][2:]) and len(e["fav"]) >= 4, "Favoriten: %s" % e["fav"][:4])
    ok(e["help"] == [True, True], "Anleitung + Zeile unter Mehr")
    ok(e["quiet"] == [False, True, True], "Hinweis «Geräusch-Alarm / Klatschschalter pausiert» nur, wenn einer davon an ist: %s" % e["quiet"])
    b_ = e["bplay"]
    ok(b_[0] == 200 and b_[1]["url"] == srv.base + "/stream.mp3" and b_[1]["kind"] == "icy" and b_[1]["proxy"] == "/radio/stream/pilatus" and e["bplay_view"] == 403,
       "Browser: Adresse vom Pi (Wiedergabeliste aufgelöst) %s, Nur ansehen %s" % (b_[1], e["bplay_view"]))
    ok(e["proxy"][:3] == [[200, "audio/mpeg"], [200, "audio/mpeg"], [429, "too many listeners through MoveEye (at most 2)"]] and e["proxy"][3] and e["proxy"][4] == 2,
       "Proxy: 2 Zuhörer, der dritte 429, Ton kommt durch: %s" % e["proxy"])
    ok(e["proxy_after"] == 0 and e["proxy_end"] == 0, "Proxy: Plätze nach close() wieder frei (auch ohne gesendete Daten)")
    ok(e["proxy_bad"] == [404, 404, 404, 404] and e["proxy_hls"] == 415, "Proxy: nur Sender der Liste (%s), HLS nicht (%s)" % (e["proxy_bad"], e["proxy_hls"]))
    ok(e["icons"] == [True, False, True], "Handy-Funkgerät jetzt mit 📡 (Morse-Seite, Anleitung): %s" % e["icons"])
    ok(bool(e["selftest"]), "Selbsttest-Funktion: %s" % e["selftest"])
    ok(e["blocked"] == ["nohost.invalid"], "nie das echte Internet (nur nohost.invalid absichtlich abgewiesen): %s" % e["blocked"])
    ok(not e["kids_end"], "am Ende keine Prozesse: %s" % e["kids_end"])


def ns_txt(s):
    return s or ""


# ---- C) kill -9: ffmpeg and the loudspeaker die with MoveEye -----------------------------------------------------------------------
TEIL_C = r'''
import os, sys, time
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
src = src[:i] + "\n" + os.environ["MW_RT_PATCH"] + src[i:]
ns = {"__name__": "mw_radio_c", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src, sys.argv[1], "exec"), ns)
ns["CFG"].update(audio_out="default", lang="de")
ns["CFG"]["radio_stations"].append({"id": "t1", "name": "Test FM", "url": os.environ["MW_RT_BASE"] + "/stream.mp3"})
ns["radio_play"]("t1", "test")
t0 = time.time()
while time.time() - t0 < 15 and not (ns["RADIO"]["state"] == "playing" and ns["RADIO"]["out"] is not None):
    time.sleep(0.1)
print("PLAYING", ns["RADIO"]["state"], flush=True)
time.sleep(600)
'''


def teil_c(datei, tmp, srv):
    print("C) kill -9: ffmpeg und Lautsprecher gehen mit", flush=True)
    home = os.path.join(tmp, "c"); os.makedirs(home)
    p = subprocess.Popen([sys.executable, "-c", TEIL_C, datei], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env_for(tmp, srv, home), cwd=tmp)
    line, t0 = "", time.time()
    while time.time() - t0 < 120:
        line = p.stdout.readline()
        if not line or line.startswith("PLAYING"):
            break
    time.sleep(1.0)
    kids = children(p.pid)
    os.kill(p.pid, signal.SIGKILL); p.wait(10)
    def alive(pid):                                       # a zombie (dead, not yet collected by init) counts as gone
        try:
            return open("/proc/%d/stat" % pid).read().rsplit(")", 1)[1].split()[0] != "Z"
        except OSError:
            return False
    gone = None
    for i in range(40):
        if not any(alive(pid) for pid, _k in kids):
            gone = round(i * 0.1, 1); break
        time.sleep(0.1)
    left = [k for k in kids if alive(k[0])]
    for pid, _k in left:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    ok(line.startswith("PLAYING playing") and sorted(k for _p, k in kids) == ["ffmpeg", "sink:44100"], "spielt: %s %s" % (line.strip(), kids))
    ok(gone is not None, "nach kill -9 sind ffmpeg und Lautsprecher nach %s s weg (übrig: %s)" % (gone, left))


# ---- D) the Pi window with a made-up tkinter --------------------------------------------------------------------------------------
TEIL_D = r'''
import os, sys, types, time
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
src = src[:i] + "\n" + os.environ["MW_RT_PATCH"] + src[i:]
ns = {"__name__": "mw_radio_d", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src, sys.argv[1], "exec"), ns)
W, AFTER = [], []
class Wd:
    def __init__(self, parent=None, **kw):
        self.kw = dict(kw); self.binds = {}; self.packed = False; self.items = []; self.sel = (); self.val = 0; self.cls = type(self).__name__; W.append(self)
    def config(self, **kw): self.kw.update(kw)
    configure = config
    def pack(self, **kw): self.packed = True; return self
    grid = pack
    def bind(self, ev, f): self.binds[ev] = f
    def after(self, ms, f): AFTER.append(f)
    def winfo_exists(self): return not self.kw.get("destroyed")
    def title(self, t): self.kw["title"] = t
    def geometry(self, g): pass
    def lift(self): pass
    def destroy(self): self.kw["destroyed"] = True
    def delete(self, *a): self.items = []
    def insert(self, i, s): self.items.append(s)
    def size(self): return len(self.items)
    def curselection(self): return self.sel
    def set(self, v): self.val = v
    def get(self): return self.val
tk = types.SimpleNamespace(**{n: type(n, (Wd,), {}) for n in ("Toplevel", "Label", "Frame", "Listbox", "Scale", "Button")})
ns["tk"] = tk; ns["GUI_OK"] = True
part = open(os.environ["MW_RT_PART"], encoding="utf-8").read()
a0 = part.index("if GUI_OK:\n    def _radio_tk_win"); a1 = part.index("App._radio_win = _radio_tk_win", a0) + len("App._radio_win = _radio_tk_win")
exec(compile(part[a0:a1], "639zzzzd(fenster)", "exec"), ns)
App = ns["App"]
class Btn(Wd): pass
def fbtn(self, parent, text, cmd, tip=None, primary=False, **k):
    b = Btn(parent, text=text); b.cmd = cmd; return b
App._fbtn = fbtn
C, R = ns["CFG"], ns["RADIO"]
C.update(audio_out="default", lang=sys.argv[2])
C["radio_stations"].append({"id": "t1", "name": "Test FM", "url": os.environ["MW_RT_BASE"] + "/stream.mp3"})
app = App.__new__(App); app.root = Wd(); pages = []; app._open_page = lambda p: pages.append(p)
app._radio_win()
FAIL = []
def chk(c, m):
    print(("  ✓ " if c else "  ✗ ") + m, flush=True); c or FAIL.append(m)
tr = ns["tr"]
lb = [w for w in W if w.cls == "Listbox"][0]
chk(lb.items == ["Radio Pilatus", "Test FM"], "Liste im Fenster: %s" % lb.items)
btn = lambda sub: [w for w in W if isinstance(w, Btn) and sub in w.kw.get("text", "")][0]
lab = lambda: [w.kw.get("text", "") for w in W if w.cls == "Label"]
chk(any(x == tr("The radio is off.") for x in lab()), "Zustand «%s»" % tr("The radio is off."))
lb.sel = (1,); btn(tr("Play")).cmd()
t0 = time.time()
while time.time() - t0 < 15 and R["state"] != "playing": time.sleep(0.1)
AFTER.pop(0)()
chk(R["sid"] == "t1" and any(x == "▶ Test FM" for x in lab()), "▶ spielt den gewählten Sender: %s" % [x for x in lab() if x][:3])
sc = [w for w in W if w.cls == "Scale"][0]
sc.val = 15; sc.binds["<ButtonRelease-1>"](None)
chk(C["radio_volume"] == 15, "Lautstärke 15")
btn(tr("Stop")).cmd()
chk(not R["want"] and R["out"] is None, "⏹ stoppt")
btn("🌐").cmd(); chk(pages == ["/radio"], "Knopf zur Seite /radio")
btn(tr("Close")).cmd(); chk(app._radio_top.kw.get("destroyed"), "Schliessen")
print("FENSTER " + ("ok" if not FAIL else "%d FEHLER" % len(FAIL)), flush=True)
os._exit(1 if FAIL else 0)
'''


def teil_d(datei, tmp, srv):
    print("D) Pi-Fenster (nachgebautes tkinter), 5 Sprachen", flush=True)
    part = os.path.join(REPO, "quelle", "639zzzzd_radio.py")
    for L in ("de", "en", "fr", "it", "rm"):
        home = os.path.join(tmp, "d_" + L); os.makedirs(home)
        env = dict(env_for(tmp, srv, home), MW_RT_PART=part)
        r = subprocess.run([sys.executable, "-c", TEIL_D, datei, L], capture_output=True, text=True, timeout=300, env=env, cwd=tmp)
        good = r.returncode == 0 and "FENSTER ok" in r.stdout
        if not good:
            print((r.stdout + r.stderr)[-2500:])
        ok(good, "Fenster %s" % L)


# ---- B) the browser ---------------------------------------------------------------------------------------------------------------
WRAP = r'''
import os, sys
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
src = src[:i] + "\n" + os.environ["MW_RT_PATCH"] + src[i:]
sys.argv = [D] + sys.argv[2:]
exec(compile(src, D, "exec"), {"__name__": "__main__", "__file__": D})
'''
PW = "radio-test-pw-1"


def pwhash(pw):
    salt = os.urandom(16)
    return "pbkdf2$200000$%s$%s" % (salt.hex(), hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200000).hex())


def teil_b(datei, tmp, srv, bilder):
    print("B) Browser 390 px dunkel (MoveEye Demo)", flush=True)
    from playwright.sync_api import sync_playwright
    os.makedirs(bilder, exist_ok=True)
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "theme": "dark", "clap_on": True, "detection_on": False, "track_person": False, "track_motion": False, "patrol": False, "audio_out": "default",
          "users": [{"name": "gast", "hash": pwhash("gast-pw-123"), "role": "view"}, {"name": "familie", "hash": pwhash("familie-pw-1"), "role": "family"}]}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tmp, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tmp, "log.txt"), "w")
    env = env_for(tmp, srv, os.path.join(tmp, "bhome"))
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = "http://127.0.0.1:%d" % port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def api(data=None, user="admin", pw=PW):
        h = {"Authorization": "Basic " + base64.b64encode((user + ":" + pw).encode()).decode(), "Content-Type": "application/json"}
        r = urllib.request.Request(base + "/api/radio", data=json.dumps(data).encode() if data is not None else None, headers=h)
        try:
            with op.open(r, timeout=60) as x:
                return x.status, json.loads(x.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(2)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                                 color_scheme="dark", http_credentials={"username": "admin", "password": PW}, locale="de-CH")
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))

            def weg():                                    # the coach-mark tour of the page (516): out of the way
                pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
            pg.goto(base + "/radio", wait_until="domcontentloaded")
            pg.wait_for_function("() => (document.getElementById('ra-name') || {}).textContent === 'Radio Pilatus'", timeout=60000)
            weg()
            ok(pg.locator("#ra-go").inner_text().startswith("▶ Abspielen"), "Knopf «▶ Abspielen»")
            pg.locator("#ra-go").click()
            pg.wait_for_function("() => (document.getElementById('ra-tit') || {}).textContent.includes('Test Artist')", timeout=40000)
            pg.wait_for_timeout(600); weg()
            ok("läuft" in pg.locator("#ra-st").inner_text().lower() and pg.locator("#ra-go").inner_text().startswith("⏹"), "Karte: «%s» · «%s»" % (pg.locator("#ra-st").inner_text(), pg.locator("#ra-tit").inner_text()))
            qn = pg.locator("#ra-qn").inner_text()
            ok(qn == "🔇 Während Radio: Geräusch-Alarm und Klatschschalter pausiert – Kamera-Alarm läuft normal", "Karte: %s" % qn)
            pg.locator("#ra-sleep button", has_text="30 min").click()
            pg.wait_for_function("() => (document.getElementById('ra-hint') || {}).textContent.includes('aus in')", timeout=10000)
            pg.wait_for_timeout(500); weg()
            pg.screenshot(path=os.path.join(bilder, "radio_spielt.png"))
            w = pg.evaluate("() => document.documentElement.scrollWidth")
            ok(w <= 390, "keine waagrechte Bildlaufleiste (%d)" % w)
            pg.locator("#ra-q").fill("test")
            pg.locator("#ra-sgo").click()
            pg.wait_for_function("() => document.querySelectorAll('#ra-res li').length >= 2", timeout=30000)
            txt = pg.locator("#ra-res").inner_text()
            ok("Test FM" in txt and "Test Ogg <script>" in txt and pg.evaluate("() => !document.querySelector('#ra-res script')"), "Suchergebnis (Text, kein HTML): %s" % txt.replace("\n", " / ")[:120])
            pg.locator("#ra-res li", has_text="Test FM").locator("button").click()
            pg.wait_for_function("() => [...document.querySelectorAll('#ra-list li')].some(x => x.textContent.includes('Test FM'))", timeout=20000)
            pg.locator("#ra-ac").scroll_into_view_if_needed(); pg.wait_for_timeout(400); weg()
            pg.screenshot(path=os.path.join(bilder, "radio_suche.png"))
            pg.locator("#ra-edit").click()
            ok(pg.locator("#ra-list li button[aria-label='Entfernen']").count() == 2, "«Bearbeiten»: ✕ pro Sender")
            # rights over HTTP
            c1, _a = api(None, "gast", "gast-pw-123"); c2, _a = api({"action": "stop"}, "gast", "gast-pw-123")
            c3, _a = api({"action": "add", "uuid": U_T2}, "familie", "familie-pw-1"); c4, a4 = api({"action": "volume", "v": 35}, "familie", "familie-pw-1")
            ok([c1, c2, c3, c4] == [200, 403, 403, 200], "Rechte über HTTP: Nur ansehen GET %d / stoppen %d · Familie Liste %d / Lautstärke %d" % (c1, c2, c3, c4))
            # «📱 dieser Browser»: the page plays itself, the loudspeaker of MoveEye stays silent
            pg.goto(base + "/radio", wait_until="domcontentloaded")
            pg.wait_for_function("() => (document.getElementById('ra-name') || {}).textContent.length > 2", timeout=30000); weg()
            ok(pg.locator("#ra-l-where").inner_text() == "Wo spielen:" and pg.locator("#ra-w-br").inner_text() == "📱 dieser Browser", "Auswahl «Wo spielen: 🔊 / 📱»")
            pg.locator("#ra-w-br").click()
            pg.wait_for_timeout(1500)
            ok(not api()[1]["state"]["on"] and pg.evaluate("() => localStorage.getItem('mw-radio-where')") == "br", "auf «📱» gestellt: MoveEye-Lautsprecher aus, im Browser gemerkt")
            pg.locator("#ra-list li", has_text="Radio Pilatus").locator(".ra-r").click()
            pg.wait_for_function("() => window.mwRadioVia === 'direct' && !mwRadioAudio.paused && mwRadioAudio.currentTime > 1.5", timeout=40000)
            pg.wait_for_function("() => (document.getElementById('ra-tit') || {}).textContent.includes('Test Artist')", timeout=40000)
            ok(True, "Browser spielt direkt (%.1f s), Titel vom Pi: %s" % (pg.evaluate("() => mwRadioAudio.currentTime"), pg.locator("#ra-tit").inner_text()))
            ok(pg.locator("#ra-qn").is_hidden(), "kein Hinweis «Geräusch-Alarm pausiert» im Browser-Modus")
            ok(not children(p.pid), "MoveEye-Lautsprecher still: kein ffmpeg / aplay (%s)" % children(p.pid))
            mt = pg.evaluate("() => navigator.mediaSession && navigator.mediaSession.metadata ? navigator.mediaSession.metadata.title + ' / ' + navigator.mediaSession.metadata.artist : ''")
            ok("Test Artist" in mt or "Radio Pilatus" in mt, "Media Session (Sperrbildschirm): %s" % mt)
            pg.locator("#ra-vol").fill("30"); pg.wait_for_timeout(300)
            ok(abs(pg.evaluate("() => mwRadioAudio.volume") - 0.3) < 0.01 and pg.evaluate("() => localStorage.getItem('mw-radio-bvol')") == "30", "Lautstärke im Browser")
            pg.locator("#ra-sleep button", has_text="15 min").click(); pg.wait_for_timeout(1200)
            ok("aus in 14:5" in pg.locator("#ra-hint").inner_text(), "Einschlaf-Timer im Browser: %s" % pg.locator("#ra-hint").inner_text())
            pg.locator("#ra-now").scroll_into_view_if_needed(); weg(); pg.evaluate("() => window.scrollTo(0, 0)"); pg.wait_for_timeout(400)
            pg.screenshot(path=os.path.join(bilder, "radio_browser.png"))
            c0, _a = api({"action": "add", "uuid": U_PX})
            pg.wait_for_function("() => [...document.querySelectorAll('#ra-list li')].some(x => x.textContent.includes('Proxy FM'))", timeout=20000)
            pg.locator("#ra-list li", has_text="Proxy FM").locator(".ra-r").click()
            pg.wait_for_function("() => window.mwRadioVia === 'proxy' && !mwRadioAudio.paused && mwRadioAudio.currentTime > 1.5", timeout=40000)
            ok(srv.conns.get("refused", 0) >= 1 and "über moveeye" in pg.locator("#ra-st").inner_text().lower(),
               "Sender sperrt Browser → über MoveEye (/radio/stream): %s" % pg.locator("#ra-st").inner_text())
            pid = [s_["id"] for s_ in api()[1]["state"]["stations"] if s_["name"] == "Proxy FM"][0]

            def stream(q="", user="admin", pw_=PW):
                h = {"Authorization": "Basic " + base64.b64encode((user + ":" + pw_).encode()).decode()}
                try:
                    x = op.open(urllib.request.Request(base + "/radio/stream/" + q, headers=h), timeout=20)
                    return x.status, x
                except urllib.error.HTTPError as e_:
                    return e_.code, None
            s1 = stream(pid)                               # the browser is the first listener, this the second
            head = s1[1].read(2000) if s1[1] else b""
            s2 = stream(pid)
            ok(s1[0] == 200 and len(head) == 2000 and s2[0] == 429, "Zuhörer-Grenze: 2. Zuhörer %d, 3. Zuhörer %d" % (s1[0], s2[0]))
            s1[1].close(); time.sleep(2.5)
            s3 = stream(pid, "familie", "familie-pw-1")
            ok(s3[0] == 200, "Platz wieder frei, Familie darf (%d)" % s3[0])
            if s3[1]:
                s3[1].close()
            bad = [stream(pid + "?url=http%3A%2F%2Fexample.com%2F")[0], stream("nichtda")[0], stream("http%3A%2F%2Fexample.com%2Fx")[0],
                   stream(pid, "gast", "gast-pw-123")[0]]
            ok(bad == [400, 404, 404, 403], "kein offener Proxy (fremde Adresse 400, unbekannt 404), Nur ansehen 403: %s" % bad)
            pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
            ok(pg.locator("#ra-w-br").get_attribute("class").find("sel") >= 0, "Auswahl nach dem Neuladen gemerkt")
            pg.locator("#ra-w-pi").click(); pg.wait_for_timeout(500)
            ok(pg.evaluate("() => mwRadioAudio.paused") and pg.evaluate("() => localStorage.getItem('mw-radio-where')") == "pi", "zurück auf 🔊: der Browser hört auf")
            api({"action": "play", "id": "pilatus"}); time.sleep(3)
            # «Mehr»: the row with the station
            pg.goto(base + "/more", wait_until="domcontentloaded")
            pg.wait_for_function("() => (document.getElementById('m-radio-s') || {}).textContent.includes('Radio Pilatus')", timeout=20000)
            grp = pg.evaluate("() => { const r = document.getElementById('m-radio'); const s = r && r.closest('section'); return s ? s.querySelector('h2').textContent : ''; }")
            mq = pg.evaluate("() => { const q = document.querySelector('#m-radio small + small'); return q ? q.textContent : ''; }")
            ok(mq.startswith("🔇 Während Radio: Geräusch-Alarm"), "Mehr-Zeile: %s" % mq)
            ok(grp == "Unterwegs", "Mehr: Zeile «📻 Radio» in «%s» mit «%s»" % (grp, pg.locator("#m-radio-s").inner_text()))
            weg(); pg.locator("#m-radio").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(bilder, "radio_mehr.png"))
            for L, word in (("fr", "Mes stations"), ("it", "Le mie stazioni"), ("rm", "Mes emetturs"), ("en", "My stations")):
                pg.evaluate("async l => { try { localStorage.setItem('mw-lang', l); } catch (e) {} await fetch('/api/ui', {method: 'POST', "
                            "headers: {'Content-Type': 'application/json'}, body: JSON.stringify({set: {'mw-lang': l}})}); }", L)
                pg.goto(base + "/radio", wait_until="domcontentloaded")
                try:
                    pg.wait_for_function("w => (document.getElementById('ra-lt') || {}).textContent === w", arg=word, timeout=30000)
                    ok(True, "%s: «%s» · «%s»" % (L, word, pg.locator("#ra-l-where").inner_text() + " " + pg.locator("#ra-w-br").inner_text()))
                except Exception:
                    ok(False, "%s: «%s» fehlt (%s)" % (L, word, pg.locator("#ra-lt").inner_text()))
            pg.evaluate("async () => { try { localStorage.setItem('mw-lang', 'de'); } catch (e) {} await fetch('/api/ui', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({set: {'mw-lang': 'de'}})}); }")
            c5, a5 = api({"action": "stop"})
            ok(c5 == 200 and not a5["state"]["on"], "stoppen")
            ok(not errs, "keine JS-Fehler %s" % errs[:3])
            br.close()
        time.sleep(1.5)
        left = children(p.pid)
        ok(not left, "nach dem Stoppen keine Prozesse (%s)" % left)
        ok(any(h[0] == "/stream.mp3" for h in srv.hits), "der Browser fragt nie das Verzeichnis selbst (alles über MoveEye)")
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
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "radio_bilder"))
    ap.add_argument("--nur", default="", help="nur diese Teile, z. B. «a,c»")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg fehlt (sudo apt install ffmpeg)")
    print("Radio-Test · " + os.path.basename(datei), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_radio_")
    nur = set(a.nur.split(",")) if a.nur else set("acdb")
    try:
        srv = Srv(*make_sounds(tmp))
        if "a" in nur:
            teil_a(datei, tmp, srv)
        if "c" in nur:
            teil_c(datei, tmp, srv)
        if "d" in nur:
            teil_d(datei, tmp, srv)
        if a.browser and "b" in nur:
            teil_b(datei, tmp, srv, a.bilder)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Radio-Test: " + ("OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
