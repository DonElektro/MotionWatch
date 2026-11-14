#!/usr/bin/env python3
"""Test «Digitaler Rucksack im Netzwerk» (Teil 639zzzn) – ohne echte Installation, ohne echtes sudo:

  A) im eigenen Prozess mit dem Flask-Testclient der gebauten Datei und einer falschen Samba-/sudo-Schicht (smb_sys,
     smb_have, /etc/samba in einem Temp-Ordner): ab Werk aus, nur der Admin (Benutzer, «Eigene Rechte» mit Einstellungen,
     /api/set), Passwort nie in Protokoll / Einstellungen / Export / Status / Befehlszeilen (nur stdin von smbpasswd),
     Bestätigung «Samba wird einmal installiert», Inhalt der Datei (kein Gast, SMB2+, valid users, nur LAN-Adressen,
     versteckte Dateien, Programme, Platz), echtes testparm wenn vorhanden, aus = keine Freigabe mehr (Samba bleibt),
     sudo will ein Passwort → Befehle zum Kopieren, FAT-Speicher, root-Ordner, nur über https, Abgleich Netz ↔ Rucksack
     (neu, umbenannt, Ordner, gelöscht, Programm / Kennung / zu gross / versteckt, aus dem Browser, Text im Browser
     gespeichert), Texte in 5 Sprachen.
  B) --e2e (nur als root, wenn smbd und smbclient da sind): echtes smbd mit der erzeugten Datei auf 127.0.0.1:4455 in einem
     Temp-Ordner, smbclient schreibt / liest, Gast und falsches Passwort abgewiesen, SMB1 abgewiesen, versteckte Dateien und
     .exe abgewiesen, die Datei erscheint im Rucksack, eine Datei aus dem Browser erscheint im Netz.
  C) --bilder ORDNER: Bildschirmfoto der Karte in den Einstellungen (Handy 390 px, dunkel), Zustand «aktiv» (falsche Schicht).

  python3 werkzeuge/rucksack_smb_test.py [--datei X.py] [--e2e] [--bilder ORDNER]
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
import threading
import time

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
HOMES = []
N = {"ok": 0}
NUTZER = "nutzer"                                          # neutral test user (owner of the folder in the fake layer)
SMB_PW = "Netz-" + base64.b16encode(os.urandom(6)).decode().lower()     # generated dummy values, never real ones
ADMIN_PW = "Admin-" + base64.b16encode(os.urandom(6)).decode().lower()
DEFAULT_SMB_CONF = """[global]
   workgroup = WORKGROUP
   map to guest = bad user
   usershare allow guests = yes
[printers]
   path = /var/tmp
   printable = yes
[print$]
   path = /var/lib/samba/printers
   read only = yes
"""


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
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_smb_home_")
    HOMES.append(os.environ["MOTIONWATCH_HOME"])
    ns = {"__name__": "mw_smb_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


class Falsch:
    """the fake system: apt, useradd, install, smbpasswd, systemctl, ip, testparm (real testparm when installed)"""

    def __init__(self, etc):
        self.etc, self.have, self.active, self.deny, self.calls, self.stdin, self.users, self.passdb = etc, False, False, False, [], [], set(), {}
        self.ip = ("1: lo    inet 127.0.0.1/8 scope host lo\n2: eth0    inet 192.168.1.20/24 brd 192.168.1.255 scope global eth0\n"
                   "3: wlan0    inet 10.0.0.5/24 scope global wlan0\n4: tailscale0    inet 100.101.1.2/32 scope global tailscale0\n"
                   "5: docker0    inet 172.17.0.1/16 scope global docker0\n6: eth1    inet 203.0.113.5/24 scope global eth1\n")

    def run(self, cmd, inp=None, timeout=60, root=True):
        self.calls.append((list(cmd), root))
        if inp is not None:
            self.stdin.append(inp)
        c0 = os.path.basename(cmd[0])
        if root and self.deny:
            return 1, "sudo: a password is required"
        if c0 == "ip":
            return 0, self.ip
        if c0 == "testparm":
            if shutil.which("testparm"):
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return r.returncode, r.stdout + r.stderr
            return 0, ""
        if c0 == "apt-get":
            if "install" in cmd:
                self.have = True
            return 0, "ok"
        if c0 == "useradd":
            self.users.add(cmd[-1])
            return 0, ""
        if c0 in ("install", "cp"):
            src, dst = cmd[-2], cmd[-1]
            if not dst.startswith(self.etc):
                return 1, "outside the fake /etc"
            if c0 == "cp" and os.path.exists(dst):
                return 0, ""
            shutil.copyfile(src, dst)
            return 0, ""
        if c0 == "smbpasswd":
            flag, user = cmd[-2], cmd[-1]
            if flag == "-a":
                a, b = (inp or "").split("\n")[:2]
                if a != b:
                    return 1, "mismatch"
                self.passdb[user] = {"pw": a, "on": True}
            elif flag == "-x":
                if user not in self.passdb:
                    return 1, "Failed to find entry for user"
                self.passdb.pop(user)
            elif flag in ("-e", "-d"):
                if user not in self.passdb:
                    return 1, "Failed to find entry for user"
                self.passdb[user]["on"] = flag == "-e"
            return 0, ""
        if c0 == "systemctl":
            if cmd[1] == "is-active":
                return (0, "active") if self.active else (3, "inactive")
            if cmd[1] == "enable":
                self.active = True
            if cmd[1] == "disable":
                self.active = False
            return 0, ""
        return 127, "unknown " + c0

    def argv(self):
        return " ".join(" ".join(c) for c, _r in self.calls)


def _gibt_es(user):
    import pwd
    try:
        return bool(pwd.getpwnam(user))
    except KeyError:
        return False


def warte(SMB, s=20.0):
    t0 = time.time()
    while SMB["busy"] and time.time() - t0 < s:
        time.sleep(0.05)


# ---------------------------------------------------------------------------------------------------------------------- A
def aufbau(datei):
    ns = laden(datei)
    CFG, TZ, SMB = ns["CFG"], ns["TZ"], ns["SMB"]
    tmp = tempfile.mkdtemp(prefix="mw_smb_")
    root = os.path.join(tmp, "tausch")
    os.makedirs(root)
    etc = os.path.join(tmp, "etc")
    os.makedirs(etc)
    with open(os.path.join(etc, "smb.conf"), "w") as f:
        f.write(DEFAULT_SMB_CONF)
    TZ["root_test"] = root
    SMB["etc"] = etc
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de", tausch_on=True, tausch_push=False, push_level="all", quiet_on=False, setup_done=True)
    ns["tausch_disk_free"] = lambda p: 100 * ns["TZ_GB"]
    fk = Falsch(etc)
    ns["smb_sys"] = fk.run
    ns["smb_have"] = lambda: fk.have
    ns["smb_unix_user"] = lambda: NUTZER
    assert ns["web_pw_set"](ADMIN_PW)[0]
    for n, r in (("Anna", "family"), ("Cus", "custom")):
        okk, err = ns["users_action"]({"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
        assert okk, err
    ns["users_action"]({"action": "update", "name": "Cus", "perms": ["live", "settings", "files_admin"]})
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    return ns, ws.app, fk, tmp, root


def teil_a(datei):
    ns, app, fk, tmp, root = aufbau(datei)
    CFG, SMB, TZ = ns["CFG"], ns["SMB"], ns["TZ"]
    c = app.test_client(use_cookies=False)
    H = {"admin": basic("admin", ADMIN_PW), "Anna": basic("Anna", "anna-pass-1"), "Cus": basic("Cus", "cus-pass-1")}

    def api(who="admin", d=None, lang="de"):
        if d is None:
            r = c.get("/api/tausch/smb?lang=" + lang, headers=H[who])
        else:
            r = c.post("/api/tausch/smb", json=dict(d, lang=lang), headers=H[who])
            j = r.get_json(silent=True) or {}
            if r.status_code == 200 and SMB["busy"]:
                warte(SMB)
                j = c.get("/api/tausch/smb?lang=" + lang, headers=H[who]).get_json(silent=True) or j
            return r.status_code, j
        warte(SMB)
        return r.status_code, (r.get_json(silent=True) or {})

    print("A1) ab Werk aus, nur der Admin", flush=True)
    ok(CFG["tausch_smb"] is False and ns["DEFAULTS"]["tausch_smb"] is False, "ab Werk aus")
    code, j = api()
    ok(code == 200 and j.get("state") == "off" and j.get("user") == "rucksack" and j.get("pw") is False, f"Admin sieht «aus»: {code} {j}")
    for who in ("Anna", "Cus"):
        code, j = api(who)
        ok(code == 403, f"{who}: GET verboten ({code})")
        code, j = api(who, {"action": "on", "password": SMB_PW})
        ok(code == 403 and not CFG["tausch_smb"], f"{who}: einschalten verboten ({code})")
        r = c.post("/api/set", json={"key": "tausch_smb", "value": True}, headers=H[who])
        ok(not CFG["tausch_smb"], f"{who}: /api/set tausch_smb geht nicht ({r.status_code})")
    ok("tausch_smb" in ns["USER_SETTINGS_DENY"], "tausch_smb in USER_SETTINGS_DENY")
    ok(not any(t[1] == "tausch_smb" for t in ns["TOGGLES"]), "kein Schema-Schalter (kein Einschalten ohne Bestätigung / Passwort)")

    print("A2) einschalten: Passwort zuerst, Bestätigung, Installation", flush=True)
    code, j = api("admin", {"action": "on"})
    ok(code == 400 and "Passwort" in (j.get("error") or ""), f"ohne Passwort: {code} {j.get('error')}")
    code, j = api("admin", {"action": "on", "password": "kurz"})
    ok(code == 400 and not CFG["tausch_smb"], f"zu kurzes Passwort abgewiesen: {code}")
    code, j = api("admin", {"action": "on", "password": SMB_PW})
    ok(code == 200 and j.get("need_install") is True and not fk.have and not CFG["tausch_smb"], f"Samba fehlt → Bestätigung: {j}")
    ok(not any("apt-get" in cc[0][0] for cc in fk.calls), "vor der Bestätigung nichts installiert")
    ok(SMB_PW not in json.dumps(j), "Passwort nicht im Status")
    code, j = api("admin", {"action": "install"})
    code, j = api()
    ok(fk.have and CFG["tausch_smb"] and j.get("state") == "on", f"installiert und aktiv: {j.get('state')} {j.get('why')}")
    ok(("rucksack" in fk.users or _gibt_es("rucksack")) and fk.passdb.get("rucksack", {}).get("pw") == SMB_PW and fk.passdb["rucksack"]["on"], "Benutzer + Passwort in Samba")
    ok(SMB["pw"] is None, "Passwort nicht mehr im Speicher")
    ok(j.get("pw") is True and j.get("win", "").endswith("\\rucksack") and j.get("mac") == "smb://192.168.1.20/rucksack",
       f"Anzeige Windows / Mac: {j.get('win')} {j.get('mac')}")
    with open(os.path.join(fk.etc, "smb.conf")) as f:
        main = f.read()
    ok(main.count("include = " + os.path.join(fk.etc, "moveeye.conf")) == 1 and main.startswith(DEFAULT_SMB_CONF.rstrip("\n")),
       "smb.conf: eine include-Zeile am Ende, sonst unverändert")
    ok(os.path.exists(os.path.join(fk.etc, "smb.conf.vor-moveeye")), "Kopie smb.conf.vor-moveeye")
    with open(os.path.join(fk.etc, "moveeye.conf")) as f:
        conf = f.read()
    for want in ("server min protocol = SMB2", "smb ports = 445", "map to guest = never", "restrict anonymous = 2", "guest ok = no", "valid users = rucksack",
                 f"force user = {NUTZER}", "bind interfaces only = yes", "interfaces = 127.0.0.1/8 192.168.1.20/24 10.0.0.5/24", "hide dot files = yes",
                 "follow symlinks = no", "wide links = no", "max disk size = 5120", "usershare allow guests = no", "path = " + os.path.join(root, "netz")):
        ok(want in conf, f"conf: «{want}»")
    vet = re.search(r"veto files = (\S+)", conf)
    ok(vet and vet.group(1).startswith("/.*/") and "/*.exe/" in vet.group(1) and "/*.sh/" in vet.group(1), "conf: veto versteckt + Programme")
    for bad in ("guest ok = yes", "NT1", "SMB1", "100.101.1.2", "172.17.0.1", "203.0.113.5", SMB_PW):
        ok(bad not in conf, f"conf ohne «{bad}»")
    ok(len(re.findall(r"^\[(?!global|printers|print\$)", conf, re.M)) == 1, "conf: genau eine Freigabe")
    if shutil.which("testparm"):
        w = os.path.join(tmp, "testparm.conf")
        with open(w, "w") as f:
            f.write(DEFAULT_SMB_CONF + "include = " + os.path.join(fk.etc, "moveeye.conf") + "\n")
        r = subprocess.run(["testparm", "-s", "--suppress-prompt", w], capture_output=True, text=True, timeout=60)
        out = r.stdout
        ok(r.returncode == 0 and "[rucksack]" in out and "map to guest" not in out and "usershare allow guests" not in out and "guest ok" not in out and "server min protocol = SMB2" in out
           and re.search(r"\[printers\][^\[]*available = No", out) and re.search(r"\[print\$\][^\[]*available = No", out),
           f"testparm (echt) mit der Debian-Vorlage (Gast = Standard «nie»): rc {r.returncode} {r.stderr[-300:]}")
        print("    testparm: echt geprüft", flush=True)
    else:
        print("    testparm fehlt: nur der Text geprüft", flush=True)
    for cc, _r in fk.calls:
        ok(SMB_PW not in " ".join(cc), "Passwort nie in einer Befehlszeile")
    ok(any(SMB_PW in s for s in fk.stdin), "Passwort nur über stdin")

    print("A3) Abgleich Netzwerk ↔ Rucksack", flush=True)
    nd = os.path.join(root, "netz")
    sync = ns["smb_sync"]

    def zwei(t=None):
        t = time.time() + 30 if t is None else t
        return sync(t) + sync(t + 1)

    def alt(p):
        os.utime(p, (time.time() - 30, time.time() - 30))

    import numpy as np
    import cv2
    img = np.zeros((120, 160, 3), np.uint8); cv2.rectangle(img, (20, 20), (140, 100), (0, 160, 255), -1)
    jpg = cv2.imencode(".jpg", img)[1].tobytes()
    p = os.path.join(nd, "Ferien.jpg")
    with open(p, "wb") as f:
        f.write(jpg)
    sync(time.time())
    ok(not any(m["name"] == "Ferien.jpg" for m in TZ["files"].values()), "eine Datei, die gerade geschrieben wird, wartet")
    alt(p)
    zwei()
    fm = [m for m in TZ["files"].values() if m["name"] == "Ferien.jpg"]
    ok(len(fm) == 1 and fm[0]["area"] == "all" and fm[0]["owner_name"] == "Netzwerk", f"aus dem Netz übernommen: {fm}")
    fid = fm[0]["id"] if fm else ""
    ok(fm and os.stat(p).st_ino == os.stat(os.path.join(root, "f", fid + ".bin")).st_ino, "dieselben Daten (feste Verknüpfung, kein doppelter Platz)")
    r = c.get("/api/tausch?area=all", headers=H["Anna"])
    ok(any(x["id"] == fid for x in r.get_json().get("files", [])), "erscheint auf der Rucksack-Seite (auch für Benutzer)")
    os.rename(p, os.path.join(nd, "Sommer.jpg"))
    zwei()
    ok(TZ["files"].get(fid, {}).get("name") == "Sommer.jpg", "im Netz umbenannt = im Rucksack umbenannt (gleiche Nummer)")
    os.makedirs(os.path.join(nd, "Fotos"))
    os.rename(os.path.join(nd, "Sommer.jpg"), os.path.join(nd, "Fotos", "Sommer.jpg"))
    zwei()
    ok(any(x["name"] == "Fotos" for x in TZ["folders"]) and TZ["files"].get(fid, {}).get("folder") == "Fotos", "Ordner im Netz = Rucksack-Ordner, verschoben")
    bad = {"Spiel.exe": b"hello", "bild.jpg": b"MZ\x90\x00" + b"\x00" * 40, "Gross.pdf": b"%PDF" + b"x" * (6 * 1024 * 1024),
           "Fotos/Tief/x.jpg": jpg}
    CFG["tausch_file_mb"] = 5.0
    for nm, data in bad.items():
        q = os.path.join(nd, nm)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        with open(q, "wb") as f:
            f.write(data)
        alt(q)
    alt(os.path.join(nd, "Fotos", "Tief"))
    with open(os.path.join(nd, ".versteckt"), "w") as f:
        f.write("x")
    zwei()
    for nm in bad:
        ok(not os.path.exists(os.path.join(nd, nm)) and not any(m["name"] == os.path.basename(nm) for m in TZ["files"].values()),
           f"abgewiesen und gelöscht: {nm}")
    ok(not os.path.isdir(os.path.join(nd, "Fotos", "Tief")), "tiefere Ordner weg")
    ok(os.path.exists(os.path.join(nd, ".versteckt")) and not any(m["name"] == ".versteckt" for m in TZ["files"].values()), "versteckte Datei: nicht übernommen")
    code, j = api()
    why = " | ".join(x["name"] + ": " + x["why"] for x in j.get("rej", []))
    ok(len(j.get("rej", [])) >= 4 and "Programm" in why and "gross" in why, f"Gründe auf der Seite (Deutsch): {why[:300]}")
    CFG["tausch_file_mb"] = 200.0
    # from the browser into the network
    code, j0 = c.post("/api/tausch", json={"action": "newtext", "name": "Liste.txt", "folder": "", "lang": "de"}, headers=H["admin"]).status_code, None
    tm = [m for m in TZ["files"].values() if m["name"] == "Liste.txt"]
    if not tm:                                             # older API: upload a small text
        ok(False, f"Text im Browser anlegen ({code})")
    else:
        tid = tm[0]["id"]
        zwei()
        ok(os.path.exists(os.path.join(nd, "Liste.txt")), "im Browser angelegt → im Netz")
        ok_, err, res = ns["tausch_text_save"](ns["SMB_WHO"], tid, "neu aus dem Browser", tm[0].get("ver", 1), "de")
        zwei()
        with open(os.path.join(nd, "Liste.txt"), encoding="utf-8") as f:
            ok(f.read() == "neu aus dem Browser", f"im Browser gespeichert → im Netz neu ({ok_} {err})")
        with open(os.path.join(nd, "Liste.txt"), "w", encoding="utf-8") as f:
            f.write("im Netz geändert, länger")
        zwei()
        ok(TZ["files"][tid]["size"] == len("im Netz geändert, länger".encode()), "im Netz geändert → Grösse im Rucksack")
        ok(ns["tausch_delete"](ns["tausch_who"](type("G", (), {"role": "admin"})()), tid, "de")[0], "im Browser löschen")
        zwei()
        ok(not os.path.exists(os.path.join(nd, "Liste.txt")), "im Browser gelöscht → im Netz weg")
    os.remove(os.path.join(nd, "Fotos", "Sommer.jpg"))
    zwei()
    ok(fid not in TZ["files"], "im Netz gelöscht → im Rucksack gelöscht")
    os.rmdir(os.path.join(nd, "Fotos"))
    zwei()
    ok(not any(x["name"] == "Fotos" for x in TZ["folders"]), "leerer Ordner im Netz gelöscht → Rucksack-Ordner weg")
    shutil.rmtree(nd)
    n_vor = len(TZ["files"])
    zwei()
    ok(os.path.isdir(nd) and len(TZ["files"]) == n_vor, "fehlt der ganze Ordner, wird nichts gelöscht")

    print("A4) Passwort ändern / löschen, nur über https", flush=True)
    neu = "Neu-" + base64.b16encode(os.urandom(5)).decode()
    code, j = api("admin", {"action": "pw", "password": neu})
    ok(code == 200 and fk.passdb["rucksack"]["pw"] == neu, "Passwort geändert")
    keep = ns["seclogin_plain"]
    ns["seclogin_plain"] = lambda req: True
    code, j = api("admin", {"action": "pw", "password": "Plain-" + SMB_PW})
    ok(code == 403 and fk.passdb["rucksack"]["pw"] == neu, f"über http abgewiesen ({code})")
    ns["seclogin_plain"] = keep

    print("A5) Passwort nirgends gespeichert", flush=True)
    ns["save_settings_now"]()
    r = c.get("/api/settings/export", headers=H["admin"])
    st = c.get("/api/state", headers=H["admin"]).get_data(as_text=True) + c.get("/api/state", headers=H["Cus"]).get_data(as_text=True)
    home = os.environ["MOTIONWATCH_HOME"]
    gefunden = []
    for base in (home, tmp):
        for dp, _dn, fn in os.walk(base):
            for x in fn:
                q = os.path.join(dp, x)
                if q.startswith(os.path.join(tmp, "etc")):
                    continue                                   # the fake «Samba» keeps nothing on disk anyway
                try:
                    with open(q, "rb") as f:
                        b = f.read()
                except OSError:
                    continue
                if SMB_PW.encode() in b or neu.encode() in b:
                    gefunden.append(q)
    ok(not gefunden, f"Passwort in keiner Datei (Protokoll, Einstellungen, Rucksack): {gefunden}")
    ok(r.status_code == 200 and SMB_PW not in r.get_data(as_text=True) and neu not in r.get_data(as_text=True), "nicht im Export")
    ok(SMB_PW not in st and neu not in st, "nicht im Zustand /api/state")
    ev = json.dumps(ns["STATE"]["events"], ensure_ascii=False)
    ok(SMB_PW not in ev and neu not in ev and "network share" in ev, "nicht in den Protokoll-Zeilen")
    code, j = api("admin", {"action": "pw_del"})
    ok("rucksack" not in fk.passdb and j.get("pw") is False and j.get("state") == "err", f"Passwort gelöscht → Fehler «kein Passwort»: {j.get('why')}")
    api("admin", {"action": "pw", "password": SMB_PW})

    print("A6) ausschalten: Freigabe weg, Samba bleibt", flush=True)
    calls0 = len(fk.calls)
    code, j = api("admin", {"action": "off"})
    with open(os.path.join(fk.etc, "moveeye.conf")) as f:
        conf = f.read()
    ok(j.get("state") == "off" and "[rucksack]" not in conf and "path" not in conf, f"aus: Datei ohne Freigabe ({j.get('state')})")
    ok(fk.passdb.get("rucksack", {}).get("on") is False, "Konto gesperrt")
    ok(not fk.active, "von MoveEye gestartetes smbd wieder gestoppt")
    ok(fk.have and not any("remove" in cc[0] or "purge" in cc[0] for cc, _r in fk.calls[calls0:]), "Samba bleibt installiert")
    n0 = len(TZ["files"])
    with open(os.path.join(root, "netz", "Neu.txt"), "w") as f:
        f.write("x")
    alt(os.path.join(root, "netz", "Neu.txt"))
    zwei()
    ok(len(TZ["files"]) == n0, "aus: kein Abgleich mehr")

    print("A7) Fehler mit Grund: sudo will ein Passwort, FAT, root", flush=True)
    fk.deny = True
    code, j = api("admin", {"action": "on"})
    code, j = api()
    cm = "\n".join(j.get("cmds", []))
    ok(j.get("state") == "err" and "sudo" in j.get("why", "") and "smbpasswd -a rucksack" in cm and "apt install" in cm and SMB_PW not in cm,
       f"sudo will ein Passwort → Befehle zum Kopieren: {j.get('why')} | {cm[:200]}")
    ok(not any("NOPASSWD" in (cc[0][-1] if cc[0] else "") for cc, _r in fk.calls) and "sudoers" not in fk.argv(), "keine neue sudo-Regel")
    fk.deny = False
    ns["_smb_links_ok"] = lambda r: False
    api("admin", {"action": "on"})
    code, j = api()
    ok(j.get("state") == "err" and "exFAT" in j.get("why", ""), f"FAT-Speicher: {j.get('why')}")
    ns["_smb_links_ok"] = lambda r: True
    ns["smb_unix_user"] = lambda: ""
    api("admin", {"action": "on"})
    code, j = api()
    ok(j.get("state") == "err" and "root" in j.get("why", ""), f"Ordner gehört root: {j.get('why')}")
    ns["smb_unix_user"] = lambda: NUTZER
    fk.ip = "1: lo    inet 127.0.0.1/8 scope host lo\n6: eth1    inet 203.0.113.5/24 scope global eth1\n"
    SMB["lan"] = None
    api("admin", {"action": "on"})
    code, j = api()
    ok(j.get("state") == "err" and "Heimnetz" in j.get("why", ""), f"nur öffentliche Adresse → keine Freigabe: {j.get('why')}")
    api("admin", {"action": "off"})

    print("A8) Texte in 5 Sprachen", flush=True)
    HX = ns["_HX_SMB"]
    tr = ns["tr"]
    for k in HX:
        for L in ("de", "fr", "it", "rm"):
            ok(bool((ns["DE"] if L == "de" else ns["TRX"][L]).get(k)) and tr(k, L) == (ns["DE"] if L == "de" else ns["TRX"][L])[k], f"{L}: «{k[:50]}»")
    for L, want in (("de", "Im Netzwerk freigeben (Windows/Mac/iPhone)"), ("en", "Share in the network (Windows/Mac/iPhone)"),
                    ("fr", "Partager sur le réseau (Windows/Mac/iPhone)"), ("it", "Condividi in rete (Windows/Mac/iPhone)"),
                    ("rm", "Parter en la rait (Windows/Mac/iPhone)")):
        ok(tr("Share in the network (Windows/Mac/iPhone)", L) == want, f"Schalter {L}")
        code, j = api("admin", None, L)
        ok(code == 200, f"Status {L}")
    ok("smbPanel(d)" in ns["WEB_PAGE"] and "Im Netzwerk freigeben (Windows/Mac/iPhone)" in ns["WEB_PAGE"], "Karte auf der Einstellungsseite (mit Deutsch)")
    for L in ("fr", "it", "rm"):
        ok("🖧" in ns["HELP_X"].get(L, ""), f"Anleitung {L}")
    ok(ns["HELP_PAGE"].count("🖧") >= 2, "Anleitung de + en")
    return ns, app, fk, tmp


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(ns, tmp):
    """real smbd + smbclient on 127.0.0.1:4455 with the generated file (only as root, only when installed)"""
    if os.geteuid() != 0 or not (shutil.which("smbd") or os.path.exists("/usr/sbin/smbd")) or not shutil.which("smbclient"):
        print("B) übersprungen: smbd / smbclient fehlen oder nicht root", flush=True)
        return
    import pwd
    print("B) echtes smbd + smbclient", flush=True)
    smbd = shutil.which("smbd") or "/usr/sbin/smbd"
    CFG, TZ, SMB = ns["CFG"], ns["TZ"], ns["SMB"]
    base = tempfile.mkdtemp(prefix="mw_smb_e2e_", dir="/tmp")
    os.chmod(base, 0o755)
    root = os.path.join(base, "tausch")
    for d in ("tausch", "tausch/netz", "run", "lock", "state", "cache", "private", "log"):
        os.makedirs(os.path.join(base, d), exist_ok=True)
    TZ["root_test"] = root
    TZ["root"] = None
    SMB.update(root=None, S=None, pend={}, err="")
    ns["_tz_load"]()
    nob = pwd.getpwnam("nobody")
    for dp, dn, fn in os.walk(root):
        os.chown(dp, nob.pw_uid, nob.pw_gid)
    made_user = False
    try:
        pwd.getpwnam("rucksack")
    except KeyError:
        subprocess.run(["useradd", "--system", "--no-create-home", "--home-dir", "/nonexistent", "--shell", "/usr/sbin/nologin", "--user-group", "rucksack"], check=True)
        made_user = True
    gen = ns["smb_conf"](os.path.join(root, "netz"), "nobody", [], 5120, sorted(ns["TZ_BLOCK_EXT"]))
    gp = os.path.join(base, "moveeye.conf")
    with open(gp, "w") as f:
        f.write(gen)
    wp = os.path.join(base, "smb.conf")
    with open(wp, "w") as f:
        f.write(DEFAULT_SMB_CONF + f"include = {gp}\n[global]\n   smb ports = 4455\n   pid directory = {base}/run\n   lock directory = {base}/lock\n"
                f"   state directory = {base}/state\n   cache directory = {base}/cache\n   private dir = {base}/private\n"
                f"   ncalrpc dir = {base}/run/ncalrpc\n   passdb backend = tdbsam:{base}/private/passdb.tdb\n   log file = {base}/log/smbd.log\n"
                "   disable netbios = yes\n   server role = standalone server\n")
    pw = "E2e-" + base64.b16encode(os.urandom(5)).decode()
    r = subprocess.run(["smbpasswd", "-c", wp, "-s", "-a", "rucksack"], input=f"{pw}\n{pw}\n", capture_output=True, text=True, timeout=60)
    ok(r.returncode == 0, f"smbpasswd -a (Temp-Datenbank): {r.stdout} {r.stderr}")
    pr = subprocess.Popen([smbd, "--foreground", "--no-process-group", f"--configfile={wp}"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, start_new_session=True)     # own session: smbd may signal its process group
    try:
        for _i in range(50):                               # smbd writes its pid file when it listens
            if glob.glob(os.path.join(base, "run", "*.pid")) and pr.poll() is None:
                break
            time.sleep(0.2)
        time.sleep(1.0)

        def cl(cmd, user=f"rucksack%{pw}", proto="SMB3", extra=()):
            a = ["smbclient", "//127.0.0.1/rucksack", "-p", "4455", "-m", proto, "-c", cmd, "--configfile=" + wp] + list(extra)
            a += ["-N"] if user is None else ["-U", user]
            q = subprocess.run(a, capture_output=True, text=True, timeout=30, cwd=base)
            return q.returncode, q.stdout + q.stderr
        src = os.path.join(base, "Hallo.txt")
        with open(src, "w") as f:
            f.write("Hallo aus dem Netz")
        rc, out = cl("put Hallo.txt; ls")
        ok(rc == 0 and "Hallo.txt" in out, f"smbclient schreibt und liest: {out[-300:]}")
        rc, out = cl("ls", user=None)
        ok(rc != 0 and re.search(r"ACCESS_DENIED|LOGON_FAILURE", out), f"Gast abgewiesen: {out[-160:]}")
        rc, out = cl("ls", user="rucksack%falsch-falsch")
        ok(rc != 0 and "LOGON_FAILURE" in out, f"falsches Passwort abgewiesen: {out[-160:]}")
        rc, out = cl("ls", proto="NT1", extra=["--option=client min protocol=NT1"])
        ok(rc != 0, f"SMB1 abgewiesen: {out[-160:]}")
        for nm in (".geheim", "Spiel.exe"):
            with open(os.path.join(base, nm), "w") as f:
                f.write("x")
            rc, out = cl(f"put {nm}")
            ok(not os.path.exists(os.path.join(root, "netz", nm)), f"Samba weist {nm} ab ({out.strip()[-120:]})")
        CFG.update(tausch_smb=True, tausch_on=True)
        SMB["err"] = ""
        p = os.path.join(root, "netz", "Hallo.txt")
        if not os.path.exists(p):
            return
        os.utime(p, (time.time() - 30, time.time() - 30))
        t = time.time() + 30
        ns["smb_sync"](t); ns["smb_sync"](t + 1)
        ok(any(m["name"] == "Hallo.txt" for m in TZ["files"].values()), "über SMB geschrieben → im Rucksack")
        who = ns["tausch_who"](type("G", (), {"role": "admin"})())
        okk, err, res = ns["tausch_create"](who, {"name": "Vom Browser.txt", "folder": ""}, "text", "de")
        ns["smb_sync"](t + 2)
        rc, out = cl("ls")
        ok(okk and "Vom Browser.txt" in out, f"im Browser angelegt → über SMB sichtbar: {err} {out[-200:]}")
        rc, out = cl("get \"Vom Browser.txt\" /dev/null")
        ok(rc == 0, f"über SMB lesbar: {out[-160:]}")
    finally:
        if FEHLER:
            for lg in glob.glob(os.path.join(base, "log", "*.log")):
                print("    " + lg + ":\n" + open(lg, errors="replace").read()[-1500:], flush=True)
        import signal
        try:
            os.killpg(pr.pid, signal.SIGTERM)              # smbd and its children (own session)
            pr.wait(10)
        except (OSError, subprocess.TimeoutExpired):
            try:
                os.killpg(pr.pid, signal.SIGKILL)
            except OSError:
                pass
        if made_user:
            for _i in range(20):
                if subprocess.run(["userdel", "rucksack"], capture_output=True).returncode in (0, 6):
                    break
                time.sleep(0.5)
        shutil.rmtree(base, ignore_errors=True)
        CFG["tausch_smb"] = False


# ---------------------------------------------------------------------------------------------------------------------- C
def knips(pg, el, pfad):
    """the card with a little of the section above it (page coordinates)"""
    pg.evaluate("""() => { document.querySelectorAll('[id^="g2"], #gd-card').forEach(e => e.remove());
      for (const e of document.querySelectorAll('body *')) { const p = getComputedStyle(e).position;
        if ((p === 'fixed' || p === 'sticky') && !e.contains(document.getElementById('smb-card'))) e.style.visibility = 'hidden'; } }""")
    pg.wait_for_timeout(800)
    bb = el.bounding_box()
    sy = pg.evaluate("() => window.scrollY")
    pg.screenshot(path=pfad, full_page=True, clip={"x": 0, "y": max(0, bb["y"] + sy - 70), "width": 390, "height": min(2000, bb["height"] + 100)})


def teil_c(datei, bilder):
    """screenshot of the card: in-process server (fake layer, state «on»), phone 390 px, dark"""
    print("C) Bildschirmfoto", flush=True)
    os.makedirs(bilder, exist_ok=True)
    ns, app, fk, tmp, root = aufbau(datei)
    CFG, SMB = ns["CFG"], ns["SMB"]
    fk.have = True
    c = app.test_client(use_cookies=False)
    c.post("/api/tausch/smb", json={"action": "on", "password": SMB_PW, "lang": "de"}, headers=basic("admin", ADMIN_PW))
    warte(SMB)
    from werkzeug.serving import make_server
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    srv = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    from playwright.sync_api import sync_playwright
    jsf = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-proxy-server"])
        for L in ("de", "en"):
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, color_scheme="dark",
                                 http_credentials={"username": "admin", "password": ADMIN_PW})
            ctx.add_init_script(f"try {{ localStorage.setItem('mw-lang', '{L}'); localStorage.setItem('mw-theme', 'dark'); }} catch (e) {{}}")
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: jsf.append(str(e)[:300]))
            pg.goto(f"http://127.0.0.1:{port}/settings", wait_until="domcontentloaded")
            pg.wait_for_timeout(2000)
            with pg.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                pg.evaluate("k => { langSet(k); }", L)
            pg.wait_for_timeout(3500)
            pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub', 'g2w'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
            pg.evaluate("() => { const c = document.getElementById('smb-card'); if (!c) return; let d = c.closest('details'); while (d) { d.open = true; d = d.parentElement && d.parentElement.closest('details'); } }")
            pg.wait_for_timeout(1500)
            card = pg.query_selector("#smb-card")
            ok(card is not None and card.is_visible(), f"{L}: Karte sichtbar")
            if card:
                card.scroll_into_view_if_needed()
                pg.wait_for_timeout(300)
                txt = card.inner_text()
                ok(("aktiv" if L == "de" else "active") in txt and "\\\\" in txt and "smb://" in txt and "rucksack" in txt, f"{L}: Zustand und Adressen: {txt[:200]}")
                ok(SMB_PW not in pg.content(), f"{L}: Passwort nicht auf der Seite")
                w = pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                ok(w <= 4, f"{L}: nicht breiter als das Handy (+{w} px)")
                knips(pg, card, os.path.join(bilder, f"rucksack_smb_{L}.png"))
            # the confirmation step (Samba missing)
            if L == "de":
                fk.have = False
                c.post("/api/tausch/smb", json={"action": "off", "lang": "de"}, headers=basic("admin", ADMIN_PW)); warte(SMB)
                c.post("/api/tausch/smb", json={"action": "on", "password": SMB_PW, "lang": "de"}, headers=basic("admin", ADMIN_PW))
                pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(3500)
                pg.evaluate("() => { const c = document.getElementById('smb-card'); if (!c) return; let d = c.closest('details'); while (d) { d.open = true; d = d.parentElement && d.parentElement.closest('details'); } }")
                pg.wait_for_timeout(1200)
                cf = pg.query_selector("#smb-confirm")
                ok(cf is not None and "Samba wird einmal installiert (ca. 10 MB). Weiter?" in cf.inner_text(), "Bestätigung auf der Seite")
                if cf:
                    cf.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                    knips(pg, pg.query_selector("#smb-card"), os.path.join(bilder, "rucksack_smb_de_bestaetigen.png"))
                    pg.evaluate("() => document.getElementById('smb-go').click()"); pg.wait_for_timeout(2500)
                    ok(fk.have and CFG["tausch_smb"], "«Weiter» installiert und schaltet ein")
                fk.have = True
            ctx.close()
        br.close()
    srv.shutdown()
    ok(not jsf, "keine JavaScript-Fehler: " + " | ".join(jsf[:3]))
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Digitaler Rucksack im Netzwerk (SMB) mit falscher Samba-/sudo-Schicht")
    ap.add_argument("--datei", default="")
    ap.add_argument("--e2e", action="store_true", help="echtes smbd / smbclient (nur root, wenn installiert)")
    ap.add_argument("--bilder", default="")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else neueste()
    ns, app, fk, tmp = teil_a(datei)
    if a.e2e:
        teil_b(ns, tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    if a.bilder:
        teil_c(datei, a.bilder)
    for h in HOMES:
        shutil.rmtree(h, ignore_errors=True)
    print(f"Rucksack-Netzwerk-Test: {N['ok']} ok, {len(FEHLER)} Fehler")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
