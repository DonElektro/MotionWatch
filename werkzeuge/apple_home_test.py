#!/usr/bin/env python3
"""Test «🏠 Apple Home» (Teil 639zzzo) – ohne echte Installation, ohne echtes sudo, ohne echtes systemd:

  A) im eigenen Prozess mit dem Flask-Testclient der gebauten Datei und einer falschen Installations- / systemd-Schicht
     (hk_sys; /opt, /var/lib, /etc/systemd in einem Temp-Ordner, daneben fremde Dateien, die bleiben müssen):
     ab Werk aus, nur der Admin (QR / Code nie für Benutzer, nie in Einstellungen / Export / /api/state), Frage vor der
     Installation, Inhalt der config.json (RTSP-Adresse, Bewegungs-Auslöser nur 127.0.0.1, Plugin-Adresse, LAN-Bindung,
     keine PIN, kein Passwort, Datei 600 über stdin, Schlüssel nie in einer Befehlszeile / Datei von MoveEye / im Protokoll),
     Scope des Schlüssels (nur /k/hk/, nur von 127.0.0.1), Alarm → Bewegungsmelder, Schalter «Schutz» (PIN → abgelehnt,
     ausdrückliche Erlaubnis), Kopf-Positionen / -Taster (Transportmodus, Not-Aus, Alarm hat Vorrang, zu schnell), Patrouille /
     Folgen, Licht (an / aus / automatisch), «Kamera-Qualität», «Neu koppeln», ohne Rechte → Befehle, Deinstallieren entfernt
     nur die eigenen Dateien.
  B) das Plugin «homebridge-moveeye» in Node mit einer falschen Homebridge-API gegen den echten Server (Zufallsport):
     Geräte angelegt / entfernt, wenn sich die Positionen ändern, Taster gehen nach ~1 s von selbst aus, «Schutz» aus mit PIN
     springt zurück, Licht-Zustand kommt nach, «gekoppelt» aus persist, Schlüssel nie im Homebridge-Protokoll.
     (Echtes Homebridge ist hier nicht installierbar, wenn npm keine Verbindung hat – dann nur B.)
  C) --bilder ORDNER: Bildschirmfotos der Karte (Handy 390 px, dunkel): aus, Einrichten mit QR, läuft (gekoppelt).

  python3 werkzeuge/apple_home_test.py [--datei X.py] [--bilder ORDNER]
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
import tempfile
import threading
import time

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
HOMES = []
N = {"ok": 0}
ADMIN_PW = "Admin-" + base64.b16encode(os.urandom(6)).decode().lower()     # generated dummy values, never real ones
PIN = str(1000 + int.from_bytes(os.urandom(2), "big") % 9000)


def ok(cond, what):
    if cond:
        N["ok"] += 1
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def laden(datei):
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_hk_home_")
    HOMES.append(os.environ["MOTIONWATCH_HOME"])
    ns = {"__name__": "mw_hk_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


def frei():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Falsch:
    """the fake system: dpkg-query, node, apt-get, useradd / userdel, install, npm, rm, find, systemctl - only inside root"""

    def __init__(self, root):
        self.root, self.calls, self.stdin, self.deny, self.active, self.enabled = root, [], [], False, False, False
        self.pkgs = {"ffmpeg"}                               # ffmpeg was there before, nodejs / npm not
        self.users, self.owner, self.removed_pkgs = set(), {}, []

    def _in(self, p):
        p = os.path.abspath(p)
        assert p.startswith(self.root + os.sep) or p.startswith(tempfile.gettempdir()), "outside the fake root: " + p
        return p

    def run(self, cmd, inp=None, timeout=60, root=True):
        cmd = list(cmd)
        self.calls.append((cmd, root))
        if inp is not None:
            self.stdin.append(inp)
        c0 = os.path.basename(cmd[0])
        if root and self.deny:
            return 1, "sudo: a password is required"
        if c0 == "dpkg-query":
            p = cmd[-1]
            return (0, "install ok installed") if p in self.pkgs else (1, f"dpkg-query: no packages found matching {p}")
        if c0 == "node":
            return (0, "v18.19.0") if "nodejs" in self.pkgs else (127, "node: not found")
        if c0 == "apt-get":
            if "install" in cmd:
                self.pkgs |= {x for x in cmd if x in ("nodejs", "npm", "ffmpeg")}
            if "remove" in cmd:
                gone = [x for x in cmd[3:]]
                self.removed_pkgs += gone
                self.pkgs -= set(gone)
            return 0, "ok"
        if c0 == "useradd":
            self.users.add(cmd[-1])
            return 0, ""
        if c0 == "userdel":
            if cmd[-1] not in self.users:
                return 6, f"userdel: user '{cmd[-1]}' does not exist"
            self.users.discard(cmd[-1])
            return 0, ""
        if c0 == "install":
            a = cmd[1:]
            mode, own, d = 0o755, None, False
            rest = []
            i = 0
            while i < len(a):
                if a[i] == "-d":
                    d = True
                elif a[i] == "-m":
                    mode = int(a[i + 1], 8); i += 1
                elif a[i] == "-o":
                    own = a[i + 1]; i += 1
                elif a[i] == "-g":
                    i += 1
                else:
                    rest.append(a[i])
                i += 1
            if d:
                for p in rest:
                    os.makedirs(self._in(p), exist_ok=True); os.chmod(p, mode); self.owner[os.path.abspath(p)] = own
                return 0, ""
            *srcs, dst = rest
            dst = self._in(dst)
            for s in srcs:
                t = os.path.join(dst, os.path.basename(s)) if dst.endswith(os.sep) or os.path.isdir(dst) else dst
                if s == "/dev/stdin":
                    with open(t, "w", encoding="utf-8") as f:
                        f.write(inp or "")
                else:
                    shutil.copyfile(s, t)
                os.chmod(t, mode); self.owner[os.path.abspath(t)] = own
            return 0, ""
        if c0 == "npm":
            pre = cmd[cmd.index("--prefix") + 1]
            for n in ("homebridge", "homebridge-camera-ffmpeg"):
                os.makedirs(os.path.join(self._in(pre), "node_modules", n), exist_ok=True)
            os.makedirs(os.path.join(pre, ".npm-tmp", "x"), exist_ok=True)
            return 0, "added 120 packages"
        if c0 == "rm":
            p = self._in(cmd[-1])
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.exists(p):
                os.remove(p)
            return 0, ""
        if c0 == "find":
            base, pat = self._in(cmd[1]), cmd[cmd.index("-name") + 1]
            for f in glob.glob(os.path.join(base, pat)):
                os.remove(f)
            return 0, ""
        if c0 == "systemctl":
            v = cmd[1]
            if v == "is-active":
                return (0, "active") if self.active else (3, "inactive")
            if v in ("restart", "start") or v == "enable" and "--now" in cmd:
                self.active = True
            if v == "enable":
                self.enabled = True
            if v in ("stop",) or v == "disable" and "--now" in cmd:
                self.active = False
            if v == "disable":
                self.enabled = False
            return 0, ""
        if c0 == "ip":
            return 0, "2: eth0    inet 192.168.1.20/24 scope global eth0\n"
        return 127, "unknown " + c0

    def argv(self):
        return "\n".join(" ".join(c) for c, _r in self.calls)


def warte(HK, s=20.0):
    t0 = time.time()
    while HK["busy"] and time.time() - t0 < s:
        time.sleep(0.05)


def aufbau(datei):
    ns = laden(datei)
    CFG, HK = ns["CFG"], ns["HK"]
    tmp = tempfile.mkdtemp(prefix="mw_hk_")
    root = os.path.join(tmp, "root")
    for d in ("opt/other", "var/lib/homebridge", "etc/systemd/system"):
        os.makedirs(os.path.join(root, d))
    for f in ("opt/other/keep.txt", "var/lib/homebridge/config.json", "etc/systemd/system/homebridge.service"):   # someone else's
        with open(os.path.join(root, f), "w") as fh:
            fh.write("fremd")
    HK.update(opt=os.path.join(root, "opt/moveeye-homebridge"), var=os.path.join(root, "var/lib/moveeye-homebridge"),
              unit=os.path.join(root, "etc/systemd/system/moveeye-homebridge.service"))
    fk = Falsch(root)
    ns["hk_sys"] = fk.run
    ns["smb_lan"] = lambda now=None: [("wlan0", "192.168.1.20/24"), ("eth0", "10.0.0.5/24")]
    ns["_mediamtx_bin"] = lambda: "/usr/local/bin/mediamtx"
    RS = {"n": 0}
    ns["rtsp_restart"] = lambda: RS.__setitem__("n", RS["n"] + 1)
    ns["live_has_head"] = lambda: True
    MOVES = []
    ns["servo_goto"] = lambda pan, tilt, who="", speed=None, wait=True, stop=None, timeout=60.0: MOVES.append((round(pan, 1), round(tilt, 1), who)) or True
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de", setup_done=True, device_name="Garten Cam", light_white_out="pca:5", light_ir_out="",
               light_white="auto", rtsp_port=8554, quiet_on=False, notify_on=False)
    assert ns["web_pw_set"](ADMIN_PW)[0]
    for n, r in (("Anna", "family"), ("Cus", "custom")):
        okk, err = ns["users_action"]({"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
        assert okk, err
    ns["users_action"]({"action": "update", "name": "Cus", "perms": ["live", "settings"]})
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    return ns, ws.app, fk, tmp, root, RS, MOVES


def lies(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    ns, app, fk, tmp, root, RS, MOVES = aufbau(datei)
    CFG, HK = ns["CFG"], ns["HK"]
    c = app.test_client(use_cookies=False)
    H = {"admin": basic("admin", ADMIN_PW), "Anna": basic("Anna", "anna-pass-1"), "Cus": basic("Cus", "cus-pass-1")}

    def api(who="admin", d=None, lang="de"):
        if d is None:
            r = c.get("/api/homekit?lang=" + lang, headers=H[who])
        else:
            r = c.post("/api/homekit", json=dict(d, lang=lang), headers=H[who])
        code = r.status_code
        warte(HK)
        if d is not None and code == 200:
            r = c.get("/api/homekit?lang=" + lang, headers=H[who])
        return code, (r.get_json(silent=True) or {})

    print("A1) ab Werk aus, nur der Admin", flush=True)
    ok(CFG["hk_on"] is False and ns["DEFAULTS"]["hk_on"] is False and CFG["hk_quality"] == "copy", "ab Werk aus, Kopie")
    code, j = api()
    ok(code == 200 and j.get("state") == "off" and not j.get("code") and not j.get("qr"), f"Admin: aus, kein Code: {code} {j.get('state')}")
    for who in ("Anna", "Cus"):
        code, _ = api(who)
        ok(code == 403, f"{who}: GET verboten ({code})")
        code, _ = api(who, {"action": "setup"})
        ok(code == 403 and not HK["want"], f"{who}: einrichten verboten ({code})")
        r = c.post("/api/set", json={"key": "hk_on", "value": True}, headers=H[who])
        ok(not CFG["hk_on"], f"{who}: /api/set hk_on geht nicht ({r.status_code})")
    ok("hk_on" in ns["USER_SETTINGS_DENY"] and "hk_disarm_nopin" in ns["APPKEY_DENY_KEYS"], "Einstellungen nur über die Karte")
    ok(not any(t[1].startswith("hk_") for t in ns["TOGGLES"]), "kein Schema-Schalter (kein Einschalten ohne Frage)")

    print("A2) Einrichten: Frage, Installation, Dienst", flush=True)
    code, j = api("admin", {"action": "install"})
    ok(code == 400 and not CFG["hk_on"], f"ohne «Einrichten» keine Installation: {code}")
    code, j = api("admin", {"action": "setup"})
    ok(j.get("need_confirm") is True and not fk.calls, f"Frage zuerst, nichts installiert: {j.get('need_confirm')} {len(fk.calls)}")
    code, j = api("admin", {"action": "cancel"})
    ok(not j.get("need_confirm") and not CFG["hk_on"], "Abbrechen")
    api("admin", {"action": "setup"})
    code, j = api("admin", {"action": "install"})
    ok(CFG["hk_on"] and fk.active and fk.enabled and j.get("state") == "run", f"installiert, Dienst läuft: {j.get('state')} {j.get('why')} {HK['err']}")
    st = CFG["hk_st"]
    ok(st.get("mine", {}).get("pkgs") == ["nodejs", "npm"], f"nur fehlende Pakete gemerkt: {st.get('mine')}")
    ok("ffmpeg" not in " ".join(" ".join(cc) for cc, _ in fk.calls if cc[0].endswith("apt-get")), "ffmpeg war da: nicht installiert")
    npm = next((cc for cc, _ in fk.calls if os.path.basename(cc[0]) == "npm"), [])
    ok("--ignore-scripts" in npm and "homebridge@1.8.5" in npm and "homebridge-camera-ffmpeg@3.1.4" in npm and "--omit=dev" in npm, f"npm: {npm}")
    ok(not os.path.exists(os.path.join(HK["opt"], ".npm-tmp")), "npm-Zwischenspeicher wieder weg")
    ok("moveeye-hb" in fk.users, "eigener Systembenutzer")
    unit = lies(HK["unit"])
    for w in ("User=moveeye-hb", "ProtectSystem=strict", "NoNewPrivileges=yes", f"ReadWritePaths={HK['var']}", "--strict-plugin-resolution",
              f"-P {HK['opt']}/plugins"):
        ok(w in unit, f"Unit: «{w}»")
    pl = os.path.join(HK["opt"], "plugins/homebridge-moveeye/index.js")
    ok(os.path.exists(pl) and "registerPlatform" in lies(pl), "Plugin installiert")
    ok(oct(os.stat(HK["var"]).st_mode & 0o777) == "0o700" and fk.owner.get(HK["var"]) == "moveeye-hb", "Speicher 700, Besitzer moveeye-hb")

    print("A3) config.json", flush=True)
    cp = os.path.join(HK["var"], "config.json")
    cf = json.loads(lies(cp))
    ok(oct(os.stat(cp).st_mode & 0o777) == "0o600" and fk.owner.get(cp) == "moveeye-hb", f"config.json 600 moveeye-hb: {oct(os.stat(cp).st_mode)}")
    br = cf["bridge"]
    setup = json.loads(lies(os.path.join(os.environ["MOTIONWATCH_HOME"], *[]) if False else os.path.join(ns["DATA_DIR"], "homekit", "setup.json")))
    ok(br["bind"] == ["eth0", "wlan0"] and br["port"] == ns["HK_PORT"] and br["pin"] == setup["code"] and br["setupID"] == setup["sid"],
       f"bridge: {br}")
    ok(re.fullmatch(r"[0-9A-F]{2}(:[0-9A-F]{2}){5}", br["username"]) and int(br["username"][:2], 16) & 2, "Kennung (lokale MAC)")
    cam = cf["platforms"][0]
    vc = cam["cameras"][0]["videoConfig"]
    m = re.match(r"-rtsp_transport tcp -i rtsp://homekit:([A-Za-z0-9_-]{20,})@127\.0\.0\.1:8554/motionwatch$", vc["source"])
    ok(bool(m) and vc["vcodec"] == "copy" and vc["audio"] is False, f"Kamera: RTSP kopieren: {vc['source'][:40]}… {vc['vcodec']}")
    vpw = m.group(1) if m else ""
    ok(vc["stillImageSource"].endswith(f"/k/hk/photo.jpg?t={vpw}") and "127.0.0.1" in vc["stillImageSource"], "Foto von photo.jpg (nur 127.0.0.1)")
    ok(cam["platform"] == "Camera-ffmpeg" and cam["localhttp"] is True and cam["porthttp"] == ns["HK_MOTION_PORT"] and cam["cameras"][0]["motion"] is True
       and cam["cameras"][0]["unbridge"] is False and cam["cameras"][0]["name"] == "Garten Cam", "Bewegungs-Auslöser nur lokal, Kamera an der Bridge")
    me = cf["platforms"][1]
    key = me.get("key", "")
    ok(me["platform"] == "MoveEye" and re.match(r"^https?://127\.0\.0\.1:\d+$", me["base"]) and key.startswith("me_"), f"Plugin-Adresse: {me['base']}")
    ok(cf["plugins"] == ["homebridge-camera-ffmpeg", "homebridge-moveeye"], "nur die zwei Plugins")
    ke = ns["appkey_find"](key, want="homekit")
    ok(ke is not None and ke.get("scope") == "homekit" and ns["appkey_find"](key) is None and ns["appkey_find"](key, api=True) is None, "eigener Scope «homekit»")
    rl = ns["RTSP_LOCAL"].get("homekit", "")
    ok("sha256:" + base64.b64encode(hashlib.sha256(vpw.encode()).digest()).decode() in rl and "127.0.0.1/32" in rl and vpw not in rl, "RTSP-Leser: nur Hash, nur lokal")
    ok(RS["n"] >= 1, "RTSP neu gestartet")
    # secrets nowhere else
    sett = lies(ns["SETTINGS_FILE"]) if os.path.exists(ns.get("SETTINGS_FILE", "")) else json.dumps(CFG)
    exp = c.get("/api/settings/export", headers=H["admin"]).get_data(as_text=True)
    stt = c.get("/api/state", headers=H["admin"]).get_data(as_text=True)
    logs = json.dumps(list(ns["STATE"].get("events") or []), default=str)
    for what, txt in (("Einstellungen", json.dumps(CFG) + sett), ("Export", exp), ("/api/state", stt), ("Protokoll", logs), ("Befehlszeilen", fk.argv()),
                      ("Status", json.dumps(j))):
        ok(key not in txt, f"Schlüssel nicht in {what}")
        ok(setup["code"] not in txt or what == "Status", f"Einrichtungscode nicht in {what}")
    dfiles = "".join(lies(p) for p in glob.glob(os.path.join(ns["DATA_DIR"], "homekit", "**"), recursive=True) if os.path.isfile(p))
    ok(key not in dfiles and vpw not in dfiles, "Schlüssel / Bildgeheimnis nicht in den Dateien von MoveEye")
    ok(oct(os.stat(os.path.join(ns["DATA_DIR"], "homekit", "setup.json")).st_mode & 0o777) == "0o600", "setup.json 600")
    ok(any(key in x for x in fk.stdin), "Schlüssel nur über stdin")
    ns["protect_pin_set"](PIN)
    code, _ = api("admin", {"action": "repair"})
    cf2 = lies(cp)
    for bad in (PIN, CFG["protect_pin"], ADMIN_PW, CFG.get("web_pw_hash") or "§", CFG.get("ext_token") or "§", "anna-pass-1"):
        ok(bad not in cf2, f"config ohne PIN / Passwort ({bad[:3]}…)")
    cf = json.loads(cf2)
    key2 = cf["platforms"][1]["key"]
    vpw = re.search(r"homekit:([^@]+)@", cf["platforms"][0]["cameras"][0]["videoConfig"]["source"]).group(1)
    ok(key2 != key and ns["appkey_find"](key, want="homekit") is None, "Neu koppeln: neuer Schlüssel, alter gesperrt")
    setup2 = json.loads(lies(os.path.join(ns["DATA_DIR"], "homekit", "setup.json")))
    ok(setup2["code"] != setup["code"] and cf["bridge"]["username"] != br["username"], "Neu koppeln: neuer Code, neue Kennung")
    key = key2
    code, j = api()
    ok(j.get("code") == setup2["code"] and j.get("uri", "").startswith("X-HM://") and j["uri"].endswith(setup2["sid"]) and "<svg" in (j.get("qr") or ""),
       f"Admin sieht Code + QR: {j.get('code')} {j.get('uri')}")
    v = int(j["uri"][7:16], 36)
    ok(v & 0x7FFFFFF == int(setup2["code"].replace("-", "")) and v >> 28 & 1 and v >> 32 == 1, "X-HM: Code, IP, Kategorie Bridge")
    for who in ("Anna", "Cus"):
        ok(setup2["code"] not in c.get("/api/state", headers=H[who]).get_data(as_text=True) and c.get("/api/homekit", headers=H[who]).status_code == 403,
           f"{who}: kein Code")

    print("A4) lokale Adressen /k/hk/: Schlüssel, Scope, nur dieser Pi", flush=True)
    K = {"X-MoveEye-Key": key}
    r = c.get("/k/hk/state", headers=K)
    j = r.get_json() or {}
    ok(r.status_code == 200 and any(x["id"] == "protect" for x in j.get("items", [])), f"state mit Schlüssel: {r.status_code}")
    ok(c.get("/k/hk/state", headers=dict(K, **{"X-Forwarded-For": "1.2.3.4"})).status_code == 404, "weitergeleitet (Tunnel) → 404")
    ok(c.get("/k/hk/state", headers=K, environ_base={"REMOTE_ADDR": "192.168.1.50"}).status_code == 404, "aus dem LAN → 404")
    ok(c.get("/k/hk/state", headers={"X-MoveEye-Key": "me_falsch_falsch_falsch"}).status_code == 403, "falscher Schlüssel → 403")
    okk, err, other = ns["appkey_create"]("Home Assistant", "test")
    ok(c.get("/k/hk/state", headers={"X-MoveEye-Key": other}).status_code == 403, "normaler App-Schlüssel öffnet /k/hk nicht")
    ok(c.get("/api/state", headers=K).status_code == 401, "HomeKit-Schlüssel öffnet /api nicht")
    ok(c.get(f"/k/{key}/status").status_code == 403 and c.get(f"/k/{key}/disarm").status_code == 403, "HomeKit-Schlüssel öffnet /k/<key>/ nicht")
    ok(c.get("/k/hk/photo.jpg?t=falsch_falsch_falsch_falsch").status_code == 404, "Foto ohne Geheimnis → 404")
    rp = c.get("/k/hk/photo.jpg?t=" + vpw)
    ok(rp.status_code in (200, 503), f"Foto mit Geheimnis ({rp.status_code})")
    ok(c.get("/k/hk/photo.jpg?t=" + vpw, environ_base={"REMOTE_ADDR": "192.168.1.50"}).status_code == 404, "Foto aus dem LAN → 404")

    def do(i, on):
        r = c.post("/k/hk/do", json={"id": i, "on": on}, headers=K)
        return r.get_json() or {}

    print("A5) Schalter «Schutz» und PIN", flush=True)
    ns["protect_pin_set"]("", PIN)
    ok(not CFG["protect_pin"], "PIN gelöscht")
    ok(do("protect", True).get("ok") and CFG["armed"], "ein = scharf")
    ok(do("protect", False).get("ok") and not CFG["armed"], "aus ohne PIN = aus")
    ns["protect_pin_set"](PIN)
    ns["arm"](0)
    r = do("protect", False)
    ok(not r.get("ok") and r.get("on") is True and CFG["armed"] and "PIN" in r.get("error", ""), f"aus mit PIN abgelehnt: {r}")
    code, j = api()
    ok(j.get("pin") is True and j.get("nopin") is False and any("PIN" in x["why"] for x in j.get("log", [])), "Karte zeigt die Ablehnung")
    api("admin", {"action": "nopin", "value": True})
    ok(do("protect", False).get("ok") and not CFG["armed"], "mit ausdrücklicher Erlaubnis: aus")
    api("admin", {"action": "nopin", "value": False})
    ok(PIN not in lies(cp), "PIN nie in Homebridge")

    print("A6) Alarm → Bewegungsmelder", flush=True)
    got = []

    class Hd(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            got.append(self.path); self.send_response(200); self.end_headers(); self.wfile.write(b"ok")

        def log_message(self, *a):
            pass
    port = frei()
    srv = http.server.HTTPServer(("127.0.0.1", port), Hd)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    ns["HK_MOTION_PORT"] = port

    def alarm(kind="person"):
        HK["motion_t"] = 0.0
        n0 = len(got)
        ns["push_alert"](kind, kind, count=1)
        t0 = time.time()
        while len(got) == n0 and time.time() - t0 < 3:
            time.sleep(0.05)
        return got[n0:]
    ns["arm"](0)
    g1 = alarm()
    ok(g1 == ["/motion?Garten%20Cam"], f"Alarm (scharf) → /motion?Garten%20Cam: {g1}")
    ok(alarm("warm") == ["/motion?Garten%20Cam"], "Wärme-Alarm auch")
    ok(alarm("prealarm") == [], "Voralarm nicht")
    CFG["sim_on"] = True
    ok(alarm() == [], "Simulation: kein Melder")
    CFG["sim_on"] = False
    CFG["kopf_transport"] = True
    ok(alarm() == [], "Transportmodus: kein Melder")
    CFG["kopf_transport"] = False
    ns["disarm"]()
    ok(alarm() == [], "nicht scharf: kein Melder")
    srv.shutdown()

    print("A7) Kopf, Patrouille, Folgen, Licht", flush=True)
    W = ns["WAYPOINTS"]
    W[:] = [[30.0, 50.0, "Eingang"], [70.0, 40.0, "Zelt"], [50.0, 50.0]]
    names = [x["name"] for x in hk_items_get(c, K)]
    for nm in ("Schutz", "Patrouille", "Folgen", "Licht weiss", "Kopf Grundstellung", "Kopf Eingang", "Kopf Zelt", "Kopf links", "Kopf runter"):
        ok(nm in names, f"Gerät «{nm}»")
    ok("Infrarot" not in names, "Infrarot nicht angeschlossen → kein Gerät")
    MOVES.clear()
    r = do("pt:Eingang", True)
    ok(r.get("ok") and MOVES and MOVES[-1][:2] == (30.0, 50.0), f"Kopf Eingang fährt: {r} {MOVES}")
    r = do("pt:Zelt", True)
    ok(not r.get("ok") and "fast" in r.get("error", ""), f"zu schnell abgelehnt: {r}")
    time.sleep(0.85)
    p0 = CFG["pan"]
    r = do("head_right", True)
    exp_pct = 15 * ns["kopf_pct_per_deg"]("pan")
    ok(r.get("ok") and abs(CFG["pan"] - min(100.0, p0 + min(25.0, exp_pct))) < 0.01, f"Kopf rechts 15°: {p0} → {CFG['pan']}")
    time.sleep(0.85)
    CFG["kopf_transport"] = True
    MOVES.clear()
    r = do("pt:Zelt", True)
    ok(not r.get("ok") and not MOVES and "Transport" in r.get("error", ""), f"Transportmodus: Kopf gesperrt: {r}")
    ok(not do("head_left", True).get("ok") and not do("head_home", True).get("ok"), "Transportmodus: Taster / Grundstellung gesperrt")
    r = do("patrol", True)
    ok(not r.get("ok") and not CFG["patrol"] and r.get("on") is False, f"Transportmodus: Patrouille springt zurück: {r}")
    CFG["track_person"] = CFG["track_motion"] = False
    r = do("follow", True)
    ok(not r.get("ok") and not CFG["track_person"] and r.get("on") is False, f"Transportmodus: Folgen gesperrt: {r}")
    code, j = api()
    ok(any("Transport" in x["why"] for x in j.get("log", [])), "Karte: warum gesperrt")
    CFG["kopf_transport"] = False
    CFG["servo_estop"] = True
    time.sleep(0.85)
    ok(not do("head_up", True).get("ok"), "Not-Aus: gesperrt")
    CFG["servo_estop"] = False
    ns["KOPF"]["alarm"] = True
    ns["arm"](0)
    time.sleep(0.85)
    r = do("head_left", True)
    ok(not r.get("ok") and "alarm" in r.get("error", ""), f"Alarm hat Vorrang: {r}")
    ns["KOPF"]["alarm"] = False
    ns["disarm"]()
    ok(do("patrol", True).get("ok") and CFG["patrol"] and do("patrol", False).get("ok") and not CFG["patrol"], "Patrouille ein / aus")
    ok(do("follow", True).get("ok") and CFG["track_person"] and do("follow", False).get("ok") and not CFG["track_person"], "Folgen ein / aus")
    ok(do("head_left", False).get("ok") is True, "Taster «aus» tut nichts")
    # lights: auto stays auto
    CFG["light_white"] = "auto"
    ns["STATE"]["lights"] = {"white": True, "ir": False}
    ok(item(c, K, "light_white")["on"] is True, "Licht: automatisch und leuchtet = an")
    ns["STATE"]["lights"] = {"white": False, "ir": False}
    ok(item(c, K, "light_white")["on"] is False, "Licht: automatisch und dunkel = aus")
    ok(do("light_white", True).get("ok") and CFG["light_white"] == "on", "Licht an = «an»")
    ok(do("light_white", False).get("ok") and CFG["light_white"] == "auto", "Licht aus = zurück auf automatisch")
    CFG["light_white"] = "off"
    do("light_white", True); do("light_white", False)
    ok(CFG["light_white"] == "off", "war aus → wieder aus")
    CFG["light_white"] = "on"
    ok(item(c, K, "light_white")["on"] is True, "in MoveEye eingeschaltet → Home zeigt an")
    W.append([10.0, 60.0, "Garage"])
    ok(any(x["name"] == "Kopf Garage" for x in hk_items_get(c, K)), "neue Position → neues Gerät")
    W[:] = [w for w in W if len(w) < 3 or w[2] != "Zelt"]
    ok(not any(x["name"] == "Kopf Zelt" for x in hk_items_get(c, K)), "gelöschte Position → Gerät weg")
    ok(do("pt:Zelt", True).get("ok") is False, "gelöschte Position: abgelehnt")
    n429 = 0
    for _ in range(35):
        n429 += c.get("/k/hk/state", headers=K).status_code == 429
    ok(n429 > 0, "zu viele Befehle → 429")
    HK["rl"].clear()

    print("A8) Kamera-Qualität, Texte", flush=True)
    api("admin", {"action": "quality", "value": "720p"})
    vc = json.loads(lies(cp))["platforms"][0]["cameras"][0]["videoConfig"]
    ok(vc["vcodec"] == "libx264" and "/k/hk/video.mjpg?t=" in vc["source"] and vc["maxHeight"] == 720 and "homekit" not in ns["RTSP_LOCAL"],
       f"720p: das Plugin kodiert aus dem MJPEG, kein RTSP: {vc['source'][:50]}")
    api("admin", {"action": "quality", "value": "copy"})
    ns["_mediamtx_bin"] = lambda: None
    code, j = api()
    ok(j.get("quality") == "copy" and j.get("quality_eff") == "720p", "ohne mediamtx: automatisch neu kodiert")
    ns["_mediamtx_bin"] = lambda: "/usr/local/bin/mediamtx"
    for L, w in (("de", "erstes Einrichten"), ("en", "Beta"), ("fr", "Bêta"), ("it", "Beta"), ("rm", "Beta")):
        ok(ns["tr"]("hk-beta", L).startswith(("Beta", "Bêta")) and (L != "de" or w in ns["tr"]("hk-beta", L)), f"{L}: Zeile «Beta»")
        ok(all(ns["tr"](k, L) != k for k in ("hk-beta", "hk-intro", "hk-howto", "hk-note")), f"{L}: keine rohen Schlüssel")
    for L, w in (("de", "Ausschalten"), ("en", "Pair"), ("fr", "Coupler"), ("it", "Abbina"), ("rm", "Colliar")):
        code, j = api("admin", None, L)
        ok(j.get("state") in ("run", "paired"), f"{L}: Status")
        ok(w in ns["tr"]("Switch off / uninstall" if L == "de" else "Pair again", L), f"{L}: Text «{w}»")
    code, j = api("admin", {"action": "step", "value": 30})
    ok(CFG["hk_step"] == 30 and api("admin", {"action": "step", "value": 99})[0] == 400, "Kopf-Schritt nur feste Werte")
    CFG["hk_step"] = 15

    print("A9) ohne Rechte → Befehle; Deinstallieren nur das Eigene", flush=True)
    fk.deny = True
    code, j = api("admin", {"action": "retry"})
    ok(j.get("state") == "err" and len(j.get("cmds") or []) >= 6, f"sudo will ein Passwort → Befehle: {j.get('state')} {len(j.get('cmds') or [])}")
    pend = os.path.join(ns["DATA_DIR"], "homekit", "config.pending.json")
    cmds = "\n".join(j.get("cmds") or [])
    pk = json.loads(lies(pend))["platforms"][1]["key"] if os.path.exists(pend) else ""
    ok(os.path.exists(pend) and oct(os.stat(pend).st_mode & 0o777) == "0o600" and pk and pk not in cmds and "rm -f" in cmds,
       "wartende Datei 600, Befehle ohne Schlüssel, löschen sie")
    fk.deny = False
    api("admin", {"action": "retry"})
    persist = os.path.join(HK["var"], "persist")
    os.makedirs(persist, exist_ok=True)
    code, j = api("admin", {"action": "uninstall"})
    left = sorted(os.path.relpath(p, root) for p in glob.glob(os.path.join(root, "**"), recursive=True) if os.path.isfile(p))
    ok(left == ["etc/systemd/system/homebridge.service", "opt/other/keep.txt", "var/lib/homebridge/config.json"], f"nur fremde Dateien bleiben: {left}")
    ok(not os.path.exists(HK["opt"]) and not os.path.exists(HK["var"]) and not os.path.exists(HK["unit"]), "eigene Ordner und Unit weg")
    ok(fk.removed_pkgs == ["nodejs", "npm"] and "ffmpeg" in fk.pkgs, f"apt remove nur das Eigene: {fk.removed_pkgs}")
    ok("moveeye-hb" not in fk.users and not fk.active and not fk.enabled, "Benutzer weg, Dienst aus")
    ok(not CFG["hk_on"] and not CFG["hk_st"] and ns["appkey_find"](key, want="homekit") is None, "aus, Schlüssel gesperrt")
    ok(not os.path.exists(os.path.join(ns["DATA_DIR"], "homekit", "setup.json")) and not os.path.exists(pend), "Code und wartende Datei weg")
    ok(j.get("state") == "off" and "homekit" not in ns["RTSP_LOCAL"], "Karte: aus, kein RTSP-Leser")
    ok(not any("autoremove" in cc for cc, _ in fk.calls) and not any("purge" in cc for cc, _ in fk.calls), "kein autoremove / purge")
    return ns, app, fk, tmp


def hk_items_get(c, K):
    return (c.get("/k/hk/state", headers=K).get_json() or {}).get("items", [])


def item(c, K, i):
    return next((x for x in hk_items_get(c, K) if x["id"] == i), {})


# ---------------------------------------------------------------------------------------------------------------------- B
NODE_HARNESS = r"""
'use strict';
// a fake Homebridge API: just enough of hap-nodejs for homebridge-moveeye
const path = require('path');
const [plugin, cfgPath, persist, script] = process.argv.slice(2);
const cfg = JSON.parse(require('fs').readFileSync(cfgPath, 'utf8'));
const out = []; const say = (...a) => out.push(a.join(' '));
class Char { constructor(n) { this.n = n; this.v = false; this.get = null; this.set = null; this.hist = []; }
  onGet(f) { this.get = f; return this; } onSet(f) { this.set = f; return this; } updateValue(v) { this.v = v; this.hist.push([Date.now(), v]); return this; } }
class Svc { constructor(t, name) { this.t = t; this.name = name; this.c = {}; }
  getCharacteristic(k) { return this.c[k] || (this.c[k] = new Char(k)); } setCharacteristic(k, v) { this.getCharacteristic(k).v = v; return this; } }
const Service = {Switch: 'Switch', Lightbulb: 'Lightbulb', AccessoryInformation: 'Info'};
const Characteristic = {On: 'On', Manufacturer: 'Manufacturer', Model: 'Model'};
class PA { constructor(name, uuid) { this.displayName = name; this.UUID = uuid; this.context = {}; this.s = [new Svc('Info', name)]; }
  addService(t, n) { const s = new Svc(t, n); this.s.push(s); return s; } getService(t) { return this.s.find(x => x.t === t); } }
const acc = new Map(); let P = null; const ev = {};
const api = {hap: {Service, Characteristic, uuid: {generate: s => require('crypto').createHash('sha1').update(s).digest('hex')}},
  platformAccessory: PA, user: {persistPath: () => persist},
  registerPlatform: (pl, name, C) => { P = new C(log, cfg, api); },
  registerPlatformAccessories: (pl, name, list) => list.forEach(a => acc.set(a.UUID, a)),
  unregisterPlatformAccessories: (pl, name, list) => list.forEach(a => acc.delete(a.UUID)),
  on: (e, f) => { ev[e] = f; }};
const log = {info: (...a) => say('LOG', ...a), warn: (...a) => say('WARN', ...a), error: (...a) => say('ERR', ...a), debug: () => {}};
require(path.resolve(plugin))(api);
const byName = n => [...acc.values()].find(a => a.displayName === n);
const on = a => (a.getService('Lightbulb') || a.getService('Switch')).getCharacteristic('On');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  ev.didFinishLaunching(); await sleep(1500);
  const names = () => [...acc.values()].map(a => a.displayName).sort();
  const res = {first: names()};
  for (const step of JSON.parse(script)) {
    if (step.wait) { await sleep(step.wait); continue; }
    if (step.names) { res[step.names] = names(); continue; }
    const a = byName(step.press); if (!a) { res[step.key] = 'missing'; continue; }
    const c = on(a); const t0 = Date.now(); c.set(step.on); await sleep(step.ms || 1600);
    res[step.key] = {now: c.v, hist: c.hist.filter(h => h[0] >= t0).map(h => [h[0] - t0, h[1]]), get: c.get()};
  }
  res.log = out; console.log(JSON.stringify(res)); process.exit(0);
})();
"""


def teil_b(datei):
    print("B) Plugin homebridge-moveeye in Node (falsche Homebridge-API)", flush=True)
    node = shutil.which("node")
    if not node:
        print("  (kein node – übersprungen)")
        return
    ns, app, fk, tmp, root, RS, MOVES = aufbau(datei)
    CFG, HK = ns["CFG"], ns["HK"]
    c = app.test_client(use_cookies=False)
    A = basic("admin", ADMIN_PW)
    c.post("/api/homekit", json={"action": "setup"}, headers=A)
    c.post("/api/homekit", json={"action": "install"}, headers=A)
    warte(HK)
    ns["WAYPOINTS"][:] = [[30.0, 50.0, "Eingang"]]
    cf = json.loads(lies(os.path.join(HK["var"], "config.json")))
    pc = cf["platforms"][1]
    key = pc["key"]
    from werkzeug.serving import make_server
    port = frei()
    srv = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    d = tempfile.mkdtemp(prefix="mw_hk_node_", dir=tmp)
    pc = dict(pc, base=f"http://127.0.0.1:{port}", poll=1)
    persist = os.path.join(d, "persist")
    os.makedirs(persist)
    with open(os.path.join(d, "cfg.json"), "w") as f:
        json.dump(pc, f)
    with open(os.path.join(d, "harness.js"), "w") as f:
        f.write(NODE_HARNESS)
    plug = os.path.join(HK["opt"], "plugins/homebridge-moveeye/index.js")
    ns["protect_pin_set"](PIN)
    ns["arm"](0)
    CFG["light_white"] = "off"
    # while the harness runs: a new taught point after 2 s, the light switched on in MoveEye, the Home app paired
    def later():
        time.sleep(2.2)
        ns["WAYPOINTS"].append([60.0, 40.0, "Zelt"])
        CFG["light_white"] = "on"
        with open(os.path.join(persist, "AccessoryInfo." + pc["username"].replace(":", "") + ".json"), "w") as f:
            json.dump({"pairedClients": {"AAAA": "x"}}, f)
    threading.Thread(target=later, daemon=True).start()
    script = [{"press": "Kopf Eingang", "on": True, "key": "btn", "ms": 1700},
              {"press": "Schutz", "on": False, "key": "prot", "ms": 1200},
              {"wait": 1500}, {"names": "later"},
              {"press": "Licht weiss", "on": False, "key": "light", "ms": 1500}]
    r = subprocess.run([node, os.path.join(d, "harness.js"), plug, os.path.join(d, "cfg.json"), persist, json.dumps(script)],
                       capture_output=True, text=True, timeout=60)
    srv.shutdown()
    try:
        res = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        ok(False, "Node-Ausgabe: " + (r.stdout + r.stderr)[-400:])
        return
    ok("Schutz" in res["first"] and "Kopf Eingang" in res["first"] and "Licht weiss" in res["first"] and "Kopf Zelt" not in res["first"],
       f"Geräte angelegt: {res['first']}")
    ok("Kopf Zelt" in res.get("later", []), f"neue Position erscheint ohne Neustart: {res.get('later')}")
    b = res.get("btn") or {}
    ok(b.get("now") is False and any(v is False and 900 <= t <= 1500 for t, v in b.get("hist", [])), f"Taster nach ~1 s wieder aus: {b}")
    ok(MOVES and MOVES[0][:2] == (30.0, 50.0), f"Taster hat den Kopf gefahren: {MOVES}")
    p = res.get("prot") or {}
    ok(p.get("now") is True and CFG["armed"], f"«Schutz» aus mit PIN springt zurück: {p}")
    ok(any("PIN" in x for x in res["log"]), "Homebridge-Protokoll nennt den Grund")
    lt = res.get("light") or {}
    ok(lt.get("now") is False and CFG["light_white"] == "off", f"Licht: kam als «an» nach, aus in Home = aus: {lt} {CFG['light_white']}")
    ok(HK["paired"] is True, "gekoppelt (persist) kommt bei MoveEye an")
    ok(key not in r.stdout + r.stderr, "Schlüssel nie im Homebridge-Protokoll")
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- C
def knips(pg, el, pfad):
    pg.evaluate("() => window.scrollTo(0, 0)")             # the sticky header stays at the top of the page, not over the card
    pg.wait_for_timeout(500)
    bb = el.bounding_box()
    sy = pg.evaluate("() => window.scrollY")
    pg.screenshot(path=pfad, full_page=True, clip={"x": 0, "y": max(0, bb["y"] + sy - 50), "width": 390, "height": min(2400, bb["height"] + 70)})


def teil_c(datei, bilder):
    print("C) Bildschirmfotos", flush=True)
    os.makedirs(bilder, exist_ok=True)
    ns, app, fk, tmp, root, RS, MOVES = aufbau(datei)
    CFG, HK = ns["CFG"], ns["HK"]
    ns["protect_pin_set"](PIN)
    ns["WAYPOINTS"][:] = [[30.0, 50.0, "Eingang"], [70.0, 40.0, "Zelt"]]
    from werkzeug.serving import make_server
    port = frei()
    srv = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    from playwright.sync_api import sync_playwright
    jsf = []
    c = app.test_client(use_cookies=False)
    A = basic("admin", ADMIN_PW)
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, color_scheme="dark",
                             http_credentials={"username": "admin", "password": ADMIN_PW})
        ctx.add_init_script("try { localStorage.setItem('mw-lang', 'de'); localStorage.setItem('mw-theme', 'dark'); } catch (e) {}")
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))

        def open_card():
            pg.goto(f"http://127.0.0.1:{port}/settings", wait_until="domcontentloaded")
            pg.wait_for_timeout(3500)
            pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub', 'g2w'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
            pg.evaluate("() => { const c = document.getElementById('hk-card'); if (!c) return; let d = c.closest('details'); while (d) { d.open = true; d = d.parentElement && d.parentElement.closest('details'); } }")
            pg.wait_for_timeout(1500)
            el = pg.query_selector("#hk-card")
            if el:
                el.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
            return el
        el = open_card()
        ok(el is not None and el.is_visible(), "Karte sichtbar (Netz & Zugang)")
        if el:
            grp = pg.evaluate("() => { const g = document.getElementById('hk-card').closest('details.grp'); return g ? g.dataset.view : ''; }")
            ok(grp == "grp:net", f"in der Gruppe Netz & Zugang: {grp}")
            ok("Einrichten" in el.inner_text() and "○" in el.inner_text(), "aus: Knopf «Einrichten»")
            ok("erstes Einrichten ist der Test; bei Problemen ein Bildschirmfoto schicken" in el.inner_text(), "Karte: Zeile «Beta»")
            rb = pg.evaluate("() => { const s = document.getElementById('hk-card').closest('details.sub'); const b = s && s.querySelector(':scope > summary .hk-beta'); return b ? b.textContent : ''; }")
            ok(rb == "Beta", f"Zeile: Abzeichen «Beta» ({rb!r})")
            w = pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            ok(w <= 4, f"nicht breiter als das Handy (+{w} px)")
            knips(pg, el, os.path.join(bilder, "apple_home_1_aus.png"))
            pg.evaluate("() => document.getElementById('hk-setup').click()"); pg.wait_for_timeout(1200)
            cf = pg.query_selector("#hk-confirm")
            ok(cf is not None and "Homebridge wird installiert (ca. 150 MB) und läuft als eigener Dienst. Weiter?" in cf.inner_text(), "Frage auf der Seite")
            ok(not fk.calls, "vor «Weiter» nichts installiert")
            knips(pg, el, os.path.join(bilder, "apple_home_2_frage.png"))
            pg.evaluate("() => document.getElementById('hk-confirm-go').click()")
            pg.wait_for_timeout(500); warte(HK); pg.wait_for_timeout(2500)
            qr = pg.query_selector("#hk-qr")
            ok(qr is not None and qr.query_selector("svg") is not None and re.search(r"\d{3}-\d{2}-\d{3}", qr.inner_text()), "Code und QR auf der Karte")
            knips(pg, el, os.path.join(bilder, "apple_home_3_einrichten_qr.png"))
            # paired: the plugin asks once with «paired»
            key = json.loads(lies(os.path.join(HK["var"], "config.json")))["platforms"][1]["key"]
            c.get("/k/hk/state", headers={"X-MoveEye-Key": key, "X-HK-Paired": "1"})
            CFG["kopf_transport"] = True
            c.post("/k/hk/do", json={"id": "pt:Zelt", "on": True}, headers={"X-MoveEye-Key": key, "X-HK-Paired": "1"})
            CFG["kopf_transport"] = False
            el = open_card()
            txt = el.inner_text() if el else ""
            ok("gekoppelt" in txt and "Kopf Eingang" in txt and not pg.query_selector("#hk-qr"), "gekoppelt: Geräte, kein QR mehr")
            ok(key not in pg.content(), "Schlüssel nicht auf der Seite")
            knips(pg, el, os.path.join(bilder, "apple_home_4_gekoppelt.png"))
        ctx.close()
        br.close()
    srv.shutdown()
    ok(not jsf, "keine JavaScript-Fehler: " + " | ".join(jsf[:3]))
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Apple Home (Homebridge) mit falscher Installations- / systemd-Schicht")
    ap.add_argument("--datei", default="")
    ap.add_argument("--bilder", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else neueste()
    ns, app, fk, tmp = teil_a(datei)
    shutil.rmtree(tmp, ignore_errors=True)
    teil_b(datei)
    if a.bilder:
        teil_c(datei, a.bilder)
    for h in HOMES:
        shutil.rmtree(h, ignore_errors=True)
    print(f"Apple-Home-Test: {N['ok']} ok, {len(FEHLER)} Fehler")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
