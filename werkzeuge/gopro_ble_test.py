#!/usr/bin/env python3
"""Test «GoPro über Bluetooth (Hero 9 und neuer, Open GoPro)» (Teil 639zzzzzzf) – ohne echtes Bluetooth, ohne Netz.

Eine nachgestellte GoPro (Ersatz für das Paket «bleak») antwortet wie die Open-GoPro-Spezifikation: Werbung 0xFEA6, Pakete
mit 5-/13-bit-Kopf und Fortsetzung, TLV-Befehle und -Abfragen, Protobuf (Netz 0x02, Befehl 0xF1, Abfrage 0xF5), Meldungen
(Provisioning 0x02 0x0C, Livestream 0xF5 0xF5, COHN 0xF5 0xEF).

  A) im eigenen Prozess (gebaute Datei geladen): ohne bleak klare Meldung, Suche (nur GoPro), Koppeln ohne / mit
     Kopplungsmodus, Hero 8 abgelehnt, Kopplungsdatei (Rechte 600), Akku, Strom über das MoveEye-WLAN -> Quelle der
     Zusatzkamera (G1-Schnittstelle), wach halten (0x5B 0x42), Abbruch des Stroms -> Neustart ohne Passwort, Bluetooth weg ->
     neu verbinden + Strom wieder da, Heim-WLAN (unbekannt ohne Passwort, falsches Passwort: kein endloses Neuversuchen),
     Stopp, COHN (Hero 12), Kamera-WLAN nur mit zweitem WLAN-Stick, Aus = Schlaf, G3-Schnittstelle (gopro_ble_client /
     gopro_ble_scan), kein Geheimnis in Protokoll / Zustand / Datei, Texte in 5 Sprachen, Selbsttest-Funktion.
  B) MoveEye als Prozess (Demo, eigener Ordner, Ersatz-«bleak» im Suchpfad): /api/gopro/ble nur für den Administrator,
     Installation nur mit Bestätigung, Suche + Koppeln über HTTP; --browser: Seite Kameras zeigt den Kasten (Handy 390 px +
     PC 1280, keine JS-Fehler), --bilder ORDNER für Bildschirmfotos.

  python3 werkzeuge/gopro_ble_test.py [--datei X.py] [--browser] [--bilder ORDNER] [--nur a,b]
"""
import argparse
import asyncio
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PASSWORT = "GoproTest-4711"
HOTSPOT_PW = "hotspotGEHEIM42"
HOME_PW = "heimGEHEIM-99"
AP_PW = "apGEHEIM-7788"
COHN_PW = "cohnGEHEIM-5566"
FEHLER = []


def ok(bed, text):
    print(("  ok     " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


# ---- the fake GoPro (speaks Open GoPro over a stand-in for bleak) ----------------------------------------------------------------
def _v(n):
    out = bytearray()
    while True:
        b, n = n & 0x7F, n >> 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def pb(*fields):
    out = b""
    for num, val in fields:
        if isinstance(val, (bytes, str)):
            b = val.encode() if isinstance(val, str) else val
            out += _v((num << 3) | 2) + _v(len(b)) + b
        else:
            out += _v(num << 3) + _v(int(val))
    return out


def pbd(data):
    i, out = 0, {}
    while i < len(data):
        n = s = 0
        while True:
            b = data[i]; i += 1; n |= (b & 0x7F) << s; s += 7
            if not b & 0x80:
                break
        num, wt = n >> 3, n & 7
        if wt == 0:
            n = s = 0
            while True:
                b = data[i]; i += 1; n |= (b & 0x7F) << s; s += 7
                if not b & 0x80:
                    break
            v = n
        else:
            ln = s = 0
            while True:
                b = data[i]; i += 1; ln |= (b & 0x7F) << s; s += 7
                if not b & 0x80:
                    break
            v = data[i:i + ln]; i += ln
        out.setdefault(num, []).append(v)
    return out


def lv(b):
    b = b.encode() if isinstance(b, str) else b
    return bytes([len(b)]) + b


class Cam:
    """the camera's state (one fake GoPro)"""

    def __init__(self, model="HERO12 Black", addr="AA:BB:CC:DD:EE:01", name="GoPro 1234"):
        self.model, self.addr, self.name = model, addr, name
        self.on, self.pairing, self.bonded = True, False, set()
        self.batt, self.known, self.pw = 87, set(), {}
        self.ls, self.url, self.keep, self.log, self.client = 0, "", 0, [], None
        self.sleeping = False
        self.cohn = False

    def hw(self):
        return (b"\x3c\x00" + lv(b"\x00\x00\x00\x3e") + lv(self.model) + lv(b"\x00") + lv("H23.01.01.10.00") + lv("C3501325000000")
                + lv("GP12345678") + lv("aabbccddeeff"))


def frames_out(payload):
    """the camera answers short messages with a 5-bit header, long ones with 13 bits + continuation"""
    if len(payload) <= 19:
        return [bytes([len(payload)]) + payload]
    out = [bytes([0x20 | (len(payload) >> 8), len(payload) & 0xFF]) + payload[:18]]
    rest, c = payload[18:], 0
    while rest:
        out.append(bytes([0x80 | c]) + rest[:19]); rest, c = rest[19:], (c + 1) & 0xF
    return out


def make_bleak(cams):
    """a module that looks like bleak (BleakScanner.discover, BleakClient) for the fake cameras"""
    m = types.ModuleType("bleak")
    m.FAKE_ADAPTER = True
    m.CAMS = cams

    class Dev:
        def __init__(self, addr, name):
            self.address, self.name = addr, name

    class Adv:
        def __init__(self, name, uu, rssi):
            self.local_name, self.service_uuids, self.rssi = name, uu, rssi

    class BleakScanner:
        @staticmethod
        async def discover(timeout=5.0, return_adv=False, **_k):
            await asyncio.sleep(0.05)
            r = {c.addr: (Dev(c.addr, c.name), Adv(c.name, ["0000fea6-0000-1000-8000-00805f9b34fb"], -50 - n))
                 for n, c in enumerate(m.CAMS) if c.on}
            r["11:22:33:44:55:66"] = (Dev("11:22:33:44:55:66", "Kopfhörer"), Adv("Kopfhörer", ["0000110b-0000-1000-8000-00805f9b34fb"], -40))
            return r

    class BleakClient:
        def __init__(self, addr, disconnected_callback=None, timeout=10.0, **_k):
            self.addr, self.gone, self.is_connected, self.cbs, self.buf = addr, disconnected_callback, False, {}, {}
            self.cam = next((c for c in m.CAMS if c.addr == addr), None)

        async def connect(self, **_k):
            await asyncio.sleep(0.02)
            if self.cam is None or not self.cam.on:
                raise Exception("Device with address %s was not found" % self.addr)
            self.is_connected = True; self.cam.client = self; self.cam.sleeping = False
            return True

        async def pair(self, **_k):
            if self.addr in self.cam.bonded:
                return True
            if not self.cam.pairing:
                raise Exception("org.bluez.Error.AuthenticationFailed")
            self.cam.bonded.add(self.addr)
            return True

        async def disconnect(self):
            self.is_connected = False
            return True

        def drop(self):                                   # the link breaks (out of range)
            self.is_connected = False
            if self.gone:
                self.gone(self)

        async def start_notify(self, uuid, cb):
            self.cbs[uuid[4:8]] = cb

        async def read_gatt_char(self, uuid):
            if self.addr not in self.cam.bonded:
                raise Exception("Not paired")
            return {"0002": b"GP12345678", "0003": AP_PW.encode()}[uuid[4:8]]

        def send(self, u, payload, delay=0.01):
            loop = asyncio.get_running_loop()
            for n, f in enumerate(frames_out(payload)):
                loop.call_later(delay + n * 0.002, lambda f=f: self.cbs[u](None, bytearray(f)) if self.is_connected else None)

        async def write_gatt_char(self, uuid, data, response=True):
            if not self.is_connected:
                raise Exception("Not connected")
            if self.addr not in self.cam.bonded:
                raise Exception("Insufficient authentication")
            u, data = uuid[4:8], bytes(data)
            if u in ("0002", "0003", "0004"):
                return
            if data[0] & 0x80:
                self.buf[u] += data[1:]
            else:
                kind = (data[0] >> 5) & 3
                self.need = (data[0] & 0x1F) if kind == 0 else (((data[0] & 0x1F) << 8) | data[1])
                self.buf[u] = data[1:] if kind == 0 else data[2:]
            if len(self.buf[u]) < self.need:
                return
            msg = self.buf[u][:self.need]
            self.cam.log.append((u, msg))
            self.handle(u, msg)

        def handle(self, u, msg):
            c = self.cam
            R = {"0072": "0073", "0074": "0075", "0076": "0077", "0091": "0092"}[u]
            if u == "0074" and msg == b"\x5b\x01\x42":
                c.keep += 1; self.send(R, b"\x5b\x00"); return
            if u == "0072":
                if msg == b"\x50":
                    self.send(R, b"\x50\x00")
                elif msg == b"\x3c":
                    self.send(R, c.hw())
                elif msg == b"\x01\x01\x01":
                    self.send(R, b"\x01\x00")
                    if c.ls == 2:
                        c.ls = 3; self.send("0077", b"\xf5\xf5" + pb((1, 3), (2, 0)), 0.1)
                elif msg == b"\x01\x01\x00":
                    self.send(R, b"\x01\x00"); c.ls = 0
                elif msg == b"\x05":
                    self.send(R, b"\x05\x00"); c.sleeping = True
                elif msg[:2] == b"\x17\x01":
                    self.send(R, b"\x17\x00")
                elif msg[:2] == b"\xf1\x79":
                    p = pbd(msg[2:]); c.url = p[1][0].decode()
                    self.send(R, b"\xf1\xf9" + pb((1, 1)))
                    c.ls = 1
                    asyncio.get_running_loop().call_later(0.3, self.ready)
                elif msg[:2] == b"\xf1\x67":
                    self.send(R, b"\xf1\xe7" + pb((1, 1)))
                elif msg[:2] == b"\xf1\x65":
                    c.cohn = True; self.send(R, b"\xf1\xe5" + pb((1, 1)))
                else:
                    self.send(R, bytes([msg[0], 2]))
                return
            if u == "0076":
                if msg[:1] == b"\x13":
                    vals = {70: c.batt, 2: 3, 8: 0, 10: 0, 6: 0, 82: 1}
                    self.send(R, b"\x13\x00" + b"".join(bytes([k, 1, vals[k]]) for k in msg[1:] if k in vals))
                elif msg[:2] == b"\xf5\x74":
                    self.send(R, b"\xf5\xf4" + pb((1, c.ls), (2, 0)))
                elif msg[:2] == b"\xf5\x6e":
                    self.send(R, b"\xf5\xee" + pb((1, 1), (2, "-----BEGIN CERTIFICATE-----\nMIIBfake\n-----END CERTIFICATE-----\n")))
                elif msg[:2] == b"\xf5\x6f":
                    st = pb((1, 1), (2, 27), (3, "gopro"), (4, COHN_PW), (5, "192.168.1.77"), (6, 1), (7, "Heimnetz")) if c.cohn else pb((1, 0), (2, 5))
                    self.send(R, b"\xf5\xef" + st)
                return
            if u == "0091":
                p = pbd(msg[2:])
                if msg[1] == 0x04:
                    ssid = p[1][0].decode()
                    if ssid in c.known:
                        self.send(R, b"\x02\x84" + pb((1, 1), (2, 2), (3, 10)))
                        self.send(R, b"\x02\x0c" + pb((1, 6)), 0.15)
                    else:
                        self.send(R, b"\x02\x84" + pb((1, 5), (2, 1), (3, 0)))
                elif msg[1] == 0x05:
                    ssid, pw = p[1][0].decode(), p[2][0].decode()
                    self.send(R, b"\x02\x85" + pb((1, 1), (2, 2), (3, 10)))
                    good = c.pw.get(ssid) == pw
                    if good:
                        c.known.add(ssid)
                    self.send(R, b"\x02\x0c" + pb((1, 5 if good else 8)), 0.15)
                elif msg[1] == 0x78:
                    self.send(R, b"\x02\xf8" + pb((1, 1)))
                return

        def ready(self):
            if self.cam.ls == 1:
                self.cam.ls = 2; self.send("0077", b"\xf5\xf5" + pb((1, 2), (2, 0)))

        def fail_stream(self):
            self.cam.ls = 5; self.send("0077", b"\xf5\xf5" + pb((1, 5), (2, 1)))

    m.BleakScanner, m.BleakClient = BleakScanner, BleakClient
    return m


# ---- A: in our own process ---------------------------------------------------------------------------------------------------------
TEIL_A = r'''
import json, os, sys, time, asyncio
sys.path.insert(0, os.environ["GPB_HIER"])
import gopro_ble_test as K
src = open(sys.argv[1], encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
ns = {"__name__": "mw_gopro_ble_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(src[:i], sys.argv[1], "exec"), ns)
ok = K.ok
G, CFG, S = ns["GPB"], ns["CFG"], ns["STATE"]
CFG.update(lang="de", hotspot_ssid="MoveEye", hotspot_password=K.HOTSPOT_PW)
ns["save_settings"] = lambda *a, **k: None
ns["GPB_BACKOFF"] = (0.5, 1.0, 1.5, 2.0, 3.0)
ns["GPB_KEEPALIVE_S"] = 0.5
G["tick"] = 0.2
D = ns["DATA_DIR"]
RX_ON = {"on": True}
ns["_rx_manage"] = lambda: None                      # G1's receiver: not started in this test
ns["_rtmp_status"] = lambda dev: {"verbunden": RX_ON["on"], "akku": None, "streamt": RX_ON["on"], "fehler": ""}
def wait(f, s):
    t = time.time()
    while time.time() - t < s:
        if f(): return True
        time.sleep(0.05)
    return False
# --- without bleak
G["bleak"] = None
real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
import builtins
def no_bleak(name, *a, **k):
    if name == "bleak": raise ImportError("no bleak")
    return real_import(name, *a, **k)
builtins.__import__ = no_bleak
f = ns["gpb_faehig_ok"]()
st = ns["gpb_state"]("de")
ok(not f[0] and "bleak" in f[1] and not st["bleak"] and st["why"].startswith("«bleak» fehlt"), "ohne bleak: klare Meldung (%s)" % st["why"])
ok(ns["gpb_action"]("install", {})[0] is False and ns["gpb_action"]("install", {"confirm": "yes"})[0] is False, "Installation nur mit Bestätigung (confirm: true)")
builtins.__import__ = real_import
W = ns["GOPRO_WEGE"].get("ble")
ok(W is not None and W["start"] is ns["gpb_start"] and W["stop"] is ns["gpb_stop"] and W["status"] is ns["gpb_status"], "Weg «ble» bei G1 angemeldet (start / stop / status)")
ok(W is not None and W["faehig"]["modelle"] == ["hero9", "hero10", "hero11", "hero12", "hero13"] and W["faehig"]["akku"] and W["faehig"]["steuern"]
   and ns["DE"].get(W["faehig"]["titel"]), "faehig: HERO9 … HERO13, Akku, Steuern, Titel übersetzt (%s)" % ns["DE"].get((W or {}).get("faehig", {}).get("titel")))
ok(not ns["_gp_weg_ok"]("ble", "hero8") and ns["_gp_weg_ok"]("ble", "hero9"), "G1: Weg «ble» nicht für die Hero 8")
# --- the fake cameras
cam = K.Cam("HERO12 Black"); old = K.Cam("HERO8 Black", "AA:BB:CC:DD:EE:08", "GoPro 0808")
B = K.make_bleak([cam, old]); G["bleak"] = B
ok(ns["gpb_faehig_ok"]()[0], "mit bleak + Adapter: Bluetooth bereit")
found = ns["gopro_ble_scan"](1.0)
ok([x["addr"] for x in found] == [cam.addr, old.addr] and all(set(x) == {"addr", "name", "rssi"} for x in found), "G3-Schnittstelle gopro_ble_scan: nur GoPro (0xFEA6), stärkste zuerst (%s)" % found)
ok(ns["gpb_action"]("scan", {})[0] and wait(lambda: not G["scan"]["running"] and G["scan"]["found"], 10), "Bluetooth-Suche über die Seite")
# --- pairing
try:
    ns["gpb_pair"](cam.addr, "GoPro 1234"); r = "ok"
except ns["GpbError"] as e:
    r = str(e)
ok(r.startswith("pairing failed"), "Koppeln ohne Kopplungsmodus: klare Meldung (%s)" % ns["tr_err"](r, "de"))
cam.pairing = old.pairing = True
try:
    ns["gpb_pair"](old.addr, "GoPro 0808"); r = "ok"
except ns["GpbError"] as e:
    r = str(e)
ok(r.startswith("not a Hero 9"), "Hero 8 abgelehnt (%s)" % ns["tr_err"](r, "de"))
did = ns["gpb_pair"](cam.addr, "GoPro 1234")
d = G["dev"][did]
ok(len(did) == 8 and d["rec"]["modell"] == "HERO12 Black" and d["rec"]["fw"] == "H23.01.01.10.00", "gekoppelt: %s %s %s" % (did, d["rec"]["modell"], d["rec"]["fw"]))
p = os.path.join(D, "gopro_ble.json")
ok(os.path.isfile(p) and (os.stat(p).st_mode & 0o777) == 0o600, "Kopplungsdatei in DATA_DIR mit Rechten 600 (%o)" % (os.stat(p).st_mode & 0o777))
ok(any(m[1][:1] == b"\x50" for m in cam.log), "Hallo an die Kamera (Set Analytics 0x50)")
ok(wait(lambda: d["akku"] == 87, 5), "Akku 87 %% (Status 70) – %s" % d["akku"])
g = ns["GOPRO"][did]
ok(g["weg"] == "ble" and g["modell"] == "hero12" and g["spec"] in ns["CFG"]["extra_cams"], "bei G1 als GoPro (Zusatzkamera) angelegt: %s" % {k: g[k] for k in ("name", "modell", "weg", "spec")})
ok(ns["gopro_status"](did)["akku"] == 87, "G1 gopro_status: Akku 87")
# a GoPro added on /gopro first, paired later
ok2, err2, g2 = ns["gopro_add"]("Zweite", "hero10", "ble")
st = ns["gpb_state"]("de")
x2 = next((x for x in st["devices"] if x["id"] == g2), None)
ok(ok2 and x2 is not None and not x2["paired"] and ns["gpb_status"](ns["GOPRO"][g2])["fehler"].startswith("not paired"), "neue GoPro (Weg ble) ohne Kopplung: «noch nicht gekoppelt»")
ok(ns["gpb_action"]("power", {"id": g2, "on": True}) == (False, "not paired yet - search and pair first"), "ohne Kopplung: Ein abgelehnt")
ns["gopro_remove"](g2)
# --- stream over MoveEye's own WLAN
S["hotspot"] = {"on": False}
src = ns["gpb_start_now"](did, "hotspot")
ok(src == "" and d["fehler"].startswith("MoveEye's own WLAN is off") and not d["want"], "MoveEye-WLAN aus: Meldung, kein Neuversuch (%s)" % ns["tr_err"](d["fehler"], "de"))
S["hotspot"] = {"on": True, "ip": "10.42.0.1"}
cam.pw["MoveEye"] = K.HOTSPOT_PW
n0 = len(cam.log)
d["net"] = "hotspot"; d["next"] = 0
t0 = time.time()
r0 = ns["gpb_start"](g)
ok(r0 == "" and time.time() - t0 < 0.5, "start(dev) für G1 blockiert nicht (%.2f s)" % (time.time() - t0))
ok(wait(lambda: d["zustand"] == "streaming", 20) and cam.ls == 3, "Strom läuft (%s)" % d["zustand"])
src = ns["gpb_start"](g)
path = ns["gopro_rtmp_path"](g)
ok(src == ns["_rx_local_url"](g) and src.endswith(path), "Quelle = Empfänger von G1: %s" % src)
g["quelle"] = ""
ok(ns["gopro_quelle"](did) == src, "G1 gopro_quelle liefert die Quelle")
ok(cam.url == ns["gopro_rtmp_url"](g, "10.42.0.1") and ":19350/" in cam.url, "RTMP-Adresse an die Kamera (Empfänger G1, Schlüsselpfad): %s" % cam.url.split("/gopro/")[0])
ok(path in ns["_rx_paths"](), "Empfänger nimmt den Pfad der Bluetooth-GoPro an (_rx_paths)")
RX_ON["on"] = False
ok(not ns["gpb_status"](g)["streamt"], "streamt erst, wenn der Empfänger das Bild hat")
RX_ON["on"] = True
sent = [m for m in cam.log[n0:]]
ok(any(u == "0091" and m[:2] == b"\x02\x05" for u, m in sent) and any(u == "0072" and m == b"\x01\x01\x01" for u, m in sent), "ConnectNew (MoveEye-WLAN), SetLiveStreamMode, Auslöser an")
ok(any(u == "0072" and m[:2] == b"\xf1\x79" and K.pbd(m[2:])[3] == [7] for u, m in sent), "Auflösung 720 (EnumWindowSize 7)")
k0 = cam.keep
ok(wait(lambda: cam.keep >= k0 + 2, 5), "wach halten: Keep Alive 0x5B 0x42 (%d)" % (cam.keep - k0))
# --- the stream breaks off -> restart (camera knows the WLAN: no password any more)
n0 = len(cam.log)
asyncio.run_coroutine_threadsafe(asyncio.sleep(0), G["loop"]).result(2)
G["loop"].call_soon_threadsafe(cam.client.fail_stream)
ok(wait(lambda: d["zustand"] in ("reconnecting",) or d["fehler"] == "stream lost - restarting", 5), "Abbruch erkannt: %s / %s" % (d["zustand"], ns["tr_err"](d["fehler"], "de")))
ok(wait(lambda: d["zustand"] == "streaming" and cam.ls == 3, 20), "Strom von selbst neu gestartet (%s)" % d["zustand"])
ok(any(u == "0091" and m[:2] == b"\x02\x04" for u, m in cam.log[n0:]) and not any(u == "0091" and m[:2] == b"\x02\x05" for u, m in cam.log[n0:]),
   "Neustart mit RequestConnect (bekanntes WLAN, kein Passwort)")
# --- Bluetooth gone -> reconnect, stream again
G["loop"].call_soon_threadsafe(cam.client.drop)
ok(wait(lambda: d["zustand"] == "reconnecting", 5), "Bluetooth weg: «verbindet neu»")
ok(wait(lambda: d["zustand"] == "streaming" and d["client"] is not None and d["client"].connected, 20), "Bluetooth wieder da, Strom läuft (%s)" % d["zustand"])
ok(ns["gpb_status"](g) == {"verbunden": True, "akku": 87, "streamt": True, "fehler": ""}, "status() für G1: %s" % ns["gpb_status"](g))
# --- stop
n0 = len(cam.log)
ns["gpb_stop"](did)
ok(d["zustand"] == "connected" and not d["want"] and any(m == b"\x01\x01\x00" for u, m in cam.log[n0:]) and any(m[:2] == b"\x02\x78" for u, m in cam.log[n0:]),
   "Stopp: Auslöser aus, Kamera verlässt das WLAN")
# --- home WLAN
ns["wifi_ip"] = lambda iface=None: ""
r = ns["gpb_start_now"](did, "home", "Heimnetz", "")
ok(r == "" and d["fehler"] == "MoveEye has no address in this WLAN", "Heim-WLAN ohne eigene Adresse: %s" % ns["tr_err"](d["fehler"], "de"))
d["want"] = False
ns["wifi_ip"] = lambda iface=None: "192.168.1.20"
r = ns["gpb_start_now"](did, "home", "Heimnetz", "")
ok(r == "" and d["fehler"].startswith("the GoPro does not know this WLAN") and not d["want"], "Heim-WLAN unbekannt ohne Passwort: Meldung, kein Neuversuch")
cam.pw["Heimnetz"] = K.HOME_PW
r = ns["gpb_start_now"](did, "home", "Heimnetz", "falsch-123")
ok(r == "" and d["fehler"] == "wrong WLAN password" and not d["want"], "falsches WLAN-Passwort: %s" % ns["tr_err"](d["fehler"], "de"))
ok(ns["gpb_action"]("wlan", {"id": did, "net": "home", "ssid": "Heimnetz", "password": K.HOME_PW})[0], "Seite: «GoPro ins WLAN bringen» (Heim-WLAN, Passwort einmal)")
ok(wait(lambda: not d["job"], 20) and "Heimnetz" in d["rec"]["known"] and not d["fehler"], "die GoPro kennt das Heim-WLAN (%s)" % d["fehler"])
ok(ns["gpb_action"]("stream", {"id": did, "on": True, "net": "home", "ssid": "Heimnetz"})[0], "Fenster: Strom starten (Heim-WLAN, ohne Passwort)")
ok(wait(lambda: d["zustand"] == "streaming" and not d["job"], 20) and cam.url.startswith("rtmp://192.168.1.20:19350/") and g["aktiv"], "Heim-WLAN: Strom läuft, GoPro bei G1 aktiv")
ns["gopro_stop"](did)
ok(d["zustand"] == "connected" and not d["want"] and not ns["GOPRO"][did]["aktiv"], "G1 Stopp -> stop(dev): Strom aus")
# --- COHN (Hero 12)
ns["gpb_cohn_setup"](did, "Heimnetz", "")
co = d["rec"].get("cohn") or {}
ok(co.get("ip") == "192.168.1.77" and co.get("user") == "gopro" and "BEGIN CERTIFICATE" in co.get("cert", ""), "COHN eingerichtet (IP %s)" % co.get("ip"))
calls = []
G["cohn_http"] = lambda c, path: (calls.append(path) or (200, json.dumps({"status": {"70": 55}}).encode()))
d["client"].close(); d["client"] = None; d["t_stat"] = 0; d["want"] = False; d["awake"] = True; d["next"] = time.time() + 60
ok(wait(lambda: d["akku"] == 55, 5) and "/gopro/camera/state" in calls, "ausser Bluetooth-Reichweite: Akku über COHN (HTTPS + Zertifikat) %s" % d["akku"])
d["next"] = 0
ok(wait(lambda: d["client"] is not None and d["client"].connected, 10), "Bluetooth von selbst wieder verbunden")
# --- camera WLAN: only with a second adapter
ns["WIFI"]["iface"] = "wlan0"; CFG["gopro_ble_ap_iface"] = "wlan0"
r = ns["gpb_start_now"](did, "ap")
ok(r == "" and d["fehler"].startswith("the camera WLAN needs a second"), "Kamera-WLAN ohne zweiten Stick abgelehnt")
CFG["gopro_ble_ap_iface"] = "wlan1"
joined, http = [], []
G["nm_join"] = lambda s, p, i: (joined.append((s, i, p == K.AP_PW)) or True)
G["http"] = lambda u: (http.append(u) or True)
r = ns["gpb_start_now"](did, "ap")
ok(r == "udp://@:8554" and joined == [("GP12345678", "wlan1", True)] and http[-1].endswith("/gopro/camera/stream/start"), "Kamera-WLAN (wlan1): Vorschau-Strom %s" % r)
ns["gpb_stop"](did)
ok(http[-1].endswith("/stream/stop"), "Kamera-WLAN: Vorschau gestoppt")
# --- off = sleep
ns["gpb_power"](did, False)
ok(d["zustand"] == "asleep" and cam.sleeping and d["client"] is None, "Aus: Kamera schläft, Bluetooth getrennt")
ns["gpb_power"](did, True)
ok(d["zustand"] == "connected" and not cam.sleeping, "Ein: Kamera wach")
# --- G3 interface
c3 = ns["gopro_ble_client"](cam.addr)
ok(c3.connect(5) and c3.write("0072", b"\x3c")[:2] == b"\x3c\x00" and c3.read("0002") == b"GP12345678" and c3.write("0002", b"x") == b"", "G3-Schnittstelle gopro_ble_client: connect / write / read")
c3.close()
ok(not c3.connected, "G3: close")
# --- restart of MoveEye: the pairing is still there
rec = json.load(open(p))["devices"][did]
ok(rec["addr"] == cam.addr and rec["known"] == ["MoveEye", "Heimnetz"] and rec["net"] in ("hotspot", "home", "ap"), "Kopplungsdatei: Adresse, bekannte WLAN-Namen (%s)" % rec["known"])
# --- no secret anywhere
logt = open(ns["LOG_FILE"], encoding="utf-8", errors="replace").read()
filet = open(p, encoding="utf-8").read()
stt = json.dumps(ns["gpb_state"]("de"), ensure_ascii=False)
for pw in (K.HOTSPOT_PW, K.HOME_PW, K.AP_PW, "falsch-123"):
    ok(pw not in logt and pw not in filet and pw not in stt, "Passwort %s… nicht in Protokoll / Datei / Zustand" % pw[:4])
ok(K.COHN_PW not in logt and K.COHN_PW not in stt and K.COHN_PW in filet, "COHN-Zugang nur in der Kopplungsdatei (600), nie im Protokoll / Zustand")
ok("GoPro" in logt and "paired" in logt and "stream lost" in logt, "Protokoll: koppeln, Abbruch (stille Meldung)")
# --- texts, selftest
miss = [(k, L) for k in ns["_HX_GPB"] for L in ("fr", "it", "rm") if not ns["TRX"][L].get(k)] + [k for k in ns["_HX_GPB"] if not ns["DE"].get(k)]
ok(not miss, "Texte in 5 Sprachen (%d Schlüssel) %s" % (len(ns["_HX_GPB"]), miss[:3]))
ok(all(ns["tr_err"](e, "de") != e for e in ns["GPB_FATAL"]), "jede Fehlermeldung auf Deutsch")
hp = ns["HELP_PAGE"]
ok(hp.count('id="gpb-help"') == 2 and all('id="gpb-help"' in ns["HELP_X"][L] for L in ("fr", "it", "rm")), "Anleitung DE / EN (+ fr / it / rm)")
ok(ns["gopro_ble_selftest"]() is True, "Selbsttest-Funktion")
ok("gpb-box" in ns["GOPRO_PAGE"] and ns["GOPRO_PAGE"].count("/*ALERTS*/") == 1, "Kasten auf G1s Seite /gopro")
ns["gpb_forget"](did)
ok(did not in G["dev"] and did in ns["GOPRO"] and did not in json.load(open(p))["devices"], "Kopplung vergessen (GoPro bleibt bei G1)")
ns["gopro_remove"](did)
ok(did not in ns["GOPRO"], "bei G1 entfernt")
print("ERGEBNIS", json.dumps(K.FEHLER))
'''


def teil_a(datei):
    print("A) im eigenen Prozess (nachgestellte GoPro)", flush=True)
    home = tempfile.mkdtemp(prefix="mw_gopro_ble_a_")
    try:
        f = os.path.join(home, "teil_a.py")
        with open(f, "w") as fh:
            fh.write(TEIL_A)
        env = dict(os.environ, MOTIONWATCH_HOME=os.path.join(home, "mw"), GPB_HIER=HIER, PYTHONPATH=HIER)
        os.makedirs(env["MOTIONWATCH_HOME"])
        p = subprocess.run([sys.executable, f, datei], env=env, capture_output=True, text=True, timeout=400, cwd=home)
        out = p.stdout
        print("\n".join(l for l in out.splitlines() if not l.startswith("ERGEBNIS")), flush=True)
        m = re.search(r"^ERGEBNIS (.*)$", out, re.M)
        if not m:
            ok(False, "Teil A lief nicht durch (rc %s): %s" % (p.returncode, (p.stderr or "")[-2500:]))
        else:
            FEHLER.extend(json.loads(m.group(1)))
    finally:
        shutil.rmtree(home, ignore_errors=True)


# ---- B: MoveEye as a process (demo), stand-in «bleak» on the path ----------------------------------------------------------------
FAKE_PKG = '''import sys, os
sys.path.insert(0, os.environ["GPB_HIER"])
import gopro_ble_test as _K
_cam = _K.Cam("HERO11 Black", "AA:BB:CC:DD:EE:11", "GoPro 1111")
_cam.pairing = True
_m = _K.make_bleak([_cam])
BleakScanner, BleakClient, FAKE_ADAPTER, CAMS = _m.BleakScanner, _m.BleakClient, True, _m.CAMS
'''


def freier_port(p):
    for q in range(p, p + 50):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", q)); return q
        except OSError:
            continue
        finally:
            s.close()
    return p


def teil_b(datei, browser, bilder):
    print("B) MoveEye als Prozess (Ersatz-bleak, HTTP%s)" % (" + Browser" if browser else ""), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_gopro_ble_b_")
    port = freier_port(5171)
    base = "http://127.0.0.1:%d" % port
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    os.makedirs(os.path.join(tmp, "fake", "bleak"))
    with open(os.path.join(tmp, "fake", "bleak", "__init__.py"), "w") as f:
        f.write(FAKE_PKG)
    with open(os.path.join(cfg, "motionwatch_settings.json"), "w") as f:
        json.dump({"cfg": {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False,
                           "sim_autostart_v2": False, "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False,
                           "setup_done": True, "https_extra": False, "tours_auto": False, "gopro_rtmp_port": freier_port(port + 200)}}, f)
    pm = urllib.request.HTTPPasswordMgrWithDefaultRealm(); pm.add_password(None, base, "admin", PASSWORT)
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPBasicAuthHandler(pm))
    anon = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def api(path, data=None, o=op):
        req = urllib.request.Request(base + path, data=None if data is None else json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        try:
            with o.open(req, timeout=20) as r:
                return dict(json.loads(r.read().decode() or "{}"), _code=r.status)
        except urllib.error.HTTPError as e:
            try:
                return dict(json.loads(e.read().decode() or "{}"), _code=e.code)
            except ValueError:
                return {"_code": e.code}

    logf = open(os.path.join(tmp, "log.txt"), "a")
    env = dict(os.environ, GPB_HIER=HIER, PYTHONPATH=os.path.join(tmp, "fake") + os.pathsep + HIER, NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PASSWORT], stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    try:
        for _i in range(240):
            if p.poll() is not None:
                ok(False, "MoveEye beendet: " + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-2000:]); return
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        q = api("/api/gopro/ble?lang=de")
        ok(q.get("ok") and q["state"]["bleak"] and q["state"]["adapter"] and q["state"]["devices"] == [], "Administrator: Zustand (bleak da, Adapter da, keine GoPro)")
        q = api("/api/gopro/ble?lang=de", o=anon)
        ok(q.get("_code") in (401, 403) and "devices" not in json.dumps(q), "ohne Anmeldung: kein Zugriff (%s)" % q.get("_code"))
        q = api("/api/gopro/ble", {"action": "install", "lang": "de"})
        ok(q.get("_code") == 400 and "bestätigen" in (q.get("error") or ""), "Installation ohne Bestätigung abgelehnt (%s)" % q.get("error"))
        q = api("/api/gopro", {"action": "add", "name": "Velo", "modell": "hero11", "weg": "ble", "lang": "de"})
        gid = next((x["id"] for x in q.get("devs") or [] if x["weg"] == "ble"), "")
        ok(q.get("ok") and bool(gid), "G1: neue GoPro mit dem Weg «HERO9 und neuer: Bluetooth» (%s)" % (q.get("error") or gid))
        q = api("/api/gopro", {"action": "add", "name": "Zweite", "modell": "hero13", "weg": "ble", "lang": "de"})
        q = api("/api/gopro/ble?lang=de")
        ok(len(q["state"]["devices"]) == 2 and not any(x["paired"] for x in q["state"]["devices"]), "beide noch nicht gekoppelt")
        q = api("/api/gopro/ble", {"action": "scan", "lang": "de"})
        st = {}
        for _i in range(60):
            st = api("/api/gopro/ble?lang=de").get("state") or {}
            if st.get("scan", {}).get("found"):
                break
            time.sleep(0.25)
        found = st.get("scan", {}).get("found") or []
        ok(len(found) == 1 and found[0]["name"] == "GoPro 1111", "Suche über HTTP: %s" % [f["name"] for f in found])
        if found:
            api("/api/gopro/ble", {"action": "pair", "id": gid, "addr": found[0]["addr"], "name": found[0]["name"], "lang": "de"})
            dv = {}
            for _i in range(80):
                st = api("/api/gopro/ble?lang=de").get("state") or {}
                dv = next((x for x in st.get("devices") or [] if x["id"] == gid), {})
                if dv.get("paired") and not st.get("pairing"):
                    break
                time.sleep(0.25)
            ok(dv.get("modell") == "HERO11 Black" and dv.get("akku") == 87 and not dv.get("cohn_ok"), "Koppeln über HTTP: %s · Akku %s" % (dv.get("modell"), dv.get("akku")))
            q = api("/api/gopro", {"action": "start", "id": gid, "lang": "de"})
            for _i in range(40):
                dv = next((x for x in (api("/api/gopro/ble?lang=de").get("state") or {}).get("devices", []) if x["id"] == gid), {})
                if dv.get("fehler"):
                    break
                time.sleep(0.25)
            ok("WLAN" in dv.get("fehler", "") and dv.get("zustand") == "connected", "G1 Start, MoveEye-WLAN aus: deutsche Meldung (%s)" % dv.get("fehler"))
            api("/api/gopro", {"action": "stop", "id": gid, "lang": "de"})
        if browser:
            web(base, bilder)
        lt = open(os.path.join(tmp, "log.txt"), errors="replace").read()
        ok("Traceback" not in lt or "gopro" not in lt.lower().split("traceback", 1)[1][:3000], "kein Traceback zur GoPro im Protokoll")
    finally:
        p.terminate()
        try:
            p.wait(20)
        except subprocess.TimeoutExpired:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def web(base, bilder):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        for gname, vp, mob in [("handy", {"width": 390, "height": 844}, True), ("pc", {"width": 1280, "height": 900}, False)]:
            ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2, color_scheme="dark",
                                 http_credentials={"username": "admin", "password": PASSWORT})
            pg = ctx.new_page()
            jsf = []
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            pg.goto(base + "/gopro", wait_until="domcontentloaded")
            box = None
            for _w in range(40):
                box = pg.evaluate("""() => { const b = [...document.querySelectorAll('.gp-card .gpb-box')]; if (b.length < 2) return null;
                    const p = b.find(x => x.querySelector('.gpb-st')), u = b.find(x => !x.querySelector('.gpb-st'));
                    if (!p || !u) return null;
                    return {st: p.querySelector('.gpb-st').textContent, btns: [...p.querySelectorAll('button')].map(x => x.textContent),
                            ubtns: [...u.querySelectorAll('button')].map(x => x.textContent), title: p.querySelector('b').textContent,
                            inCard: !!p.closest('.gp-card') && !!p.closest('.gp-card').querySelector('button'),
                            wide: Math.max(...b.map(x => x.getBoundingClientRect().right)) <= window.innerWidth + 1,
                            weg: [...document.querySelectorAll('#gp-weg option')].map(o => o.textContent)}; }""")
                if box:
                    break
                pg.wait_for_timeout(400)
            ok(bool(box) and "Bluetooth" in box["title"] and "HERO11" in box["st"] and "Akku 87" in box["st"] and box["wide"] and box["inCard"],
               "%s: Kasten «Bluetooth» in der Karte der gekoppelten GoPro, passt in die Breite (%s)" % (gname, box and box["st"]))
            ok(bool(box) and any("ins WLAN" in b for b in box["btns"]) and any("Kopplung vergessen" in b for b in box["btns"]) and any("Bluetooth-Suche" in b for b in box["ubtns"]),
               "%s: Knöpfe auf Deutsch, ungekoppelte GoPro mit «Bluetooth-Suche» (%s / %s)" % (gname, box and box["btns"], box and box["ubtns"]))
            if bilder:
                os.makedirs(bilder, exist_ok=True)
                pg.screenshot(path=os.path.join(bilder, "gopro_ble_%s.png" % gname), full_page=True)
            ok(not jsf, "%s: keine JavaScript-Fehler %s" % (gname, jsf[:2]))
            ctx.close()
        br.close()


def main():
    ap = argparse.ArgumentParser(description="GoPro über Bluetooth (Open GoPro)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--nur", default="a,b")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                                            key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    nur = set(a.nur.split(","))
    if "a" in nur:
        teil_a(datei)
    if "b" in nur:
        teil_b(datei, a.browser, a.bilder)
    print("\n%s: %d Fehler" % ("GRÜN" if not FEHLER else "ROT", len(FEHLER)))
    for f in FEHLER:
        print("  - " + f)
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
