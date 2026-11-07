#!/usr/bin/env python3
"""Test «📁 Datentausch» (Teil 639zzc) – ohne Kamera, ohne echten USB-Stick:

  A) im eigenen Prozess mit dem Flask-Testclient der gebauten Datei (schnell):
     Rechte je Rolle + «Eigene Rechte» + Gast (auch abgelaufen), Grenzen (gesamt / Datei / Benutzer / 2 GB frei, auch beim
     Stück), Namen (Pfad-Tricks, versteckt, Richtungszeichen, reserviert), Programme (Endung, erste Bytes), aktive Inhalte
     (SVG/HTML nur als Download, nosniff, sandbox), Stücke (falsche Stelle, fortsetzen, zu gross, abbrechen, unfertig),
     Löschregeln, Ordner, CSRF (fremde Origin), Push gebündelt (nur Admin, nie andere Benutzer), Texte (Version, Konflikt,
     20 Versionen im Platz, Wiederherstellen), Chat (anhängen, Rechte, Ändern 5 Min., Admin löscht, Warten auf Neues,
     Push an die Mitschreibenden ohne Inhalt), XSS-Versuche als Daten.
  B) --browser: MoveEye ohne Fenster starten, Dateien hochladen (auch über die Seite mit Stücken), Bildschirmfotos iPhone
     (390 × 844) und PC: Liste, Editor (.md Vorschau), Konflikt, Chat, Gast-Seite; keine JavaScript-Fehler; Markdown sicher.

  python3 werkzeuge/tausch_test.py [--datei X.py] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}


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
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_tz_home_")
    ns = {"__name__": "mw_tausch_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    ns = laden(datei)
    CFG, TZ = ns["CFG"], ns["TZ"]
    GB, MB = ns["TZ_GB"], ns["TZ_MB"]
    root = tempfile.mkdtemp(prefix="mw_tz_root_")
    TZ["root_test"] = root
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de", tausch_on=True, tausch_guest=True, tausch_push=True, push_level="all", quiet_on=False)
    free = {"n": 100 * GB}
    ns["tausch_disk_free"] = lambda p: free["n"]
    sent = []
    TZ["push_manual"] = True
    ns["tausch_push_send"] = lambda txt, *a: sent.append(("admin", txt)) or True
    ns["tausch_push_user"] = lambda name, txt, *a: sent.append((name, txt)) or True
    ADMIN_PW = "Admin-Pass-123"
    assert ns["web_pw_set"](ADMIN_PW)[0]
    users = {"Anna": "family", "Bob": "friend", "Vera": "view", "Kim": "kid", "Cus": "custom", "Cuz": "custom", "Carl": "family"}
    for n, r in users.items():
        okk, err = ns["users_action"]({"action": "add", "name": n, "password": n.lower() + "-pass-1", "role": r})
        assert okk, err
    ns["users_action"]({"action": "update", "name": "Cus", "perms": ["live", "files_down"]})
    ns["users_action"]({"action": "update", "name": "Cuz", "perms": ["files_admin"]})
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    app = ws.app
    c = app.test_client(use_cookies=False)               # no «trusted device» cookie: every request logs in itself
    H = {n: basic(n, n.lower() + "-pass-1") for n in users}
    H["admin"] = basic("admin", ADMIN_PW)

    def api(who, d, code=None):
        r = c.post("/api/tausch", json=dict(d, lang="de"), headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def upload(who, name, data, area="all", folder="", finish=True, chunk=None):
        code, j = api(who, {"action": "start", "name": name, "size": len(data), "area": area, "folder": folder, "lastmod": 1})
        if code != 200:
            return code, j
        uid, off, cs = j["id"], j["have"], chunk or j["chunk"]
        while off < len(data):
            r = c.post(f"/api/tausch/chunk?id={uid}&off={off}", data=data[off:off + cs], headers=dict(H[who], **{"Content-Type": "application/octet-stream"}))
            k = r.get_json()
            if r.status_code != 200:
                return r.status_code, k
            off = k["have"]
        if not finish:
            return 200, {"id": uid}
        return api(who, {"action": "finish", "id": uid})

    import numpy as np
    import cv2
    img = np.zeros((300, 400, 3), np.uint8); cv2.rectangle(img, (50, 50), (350, 250), (0, 160, 255), -1)
    jpg = cv2.imencode(".jpg", img)[1].tobytes()
    print("A) Rechte je Rolle", flush=True)
    code, j = upload("Anna", "Ferien.jpg", jpg)
    ok(code == 200 and j.get("file", {}).get("name") == "Ferien.jpg", f"Familie lädt hoch: {code} {j}")
    fid = j.get("file", {}).get("id", "")
    for _i in range(60):
        if TZ["files"].get(fid, {}).get("thumb") is not None:
            break
        time.sleep(0.1)
    ok(TZ["files"][fid].get("thumb") is True, "Vorschaubild gerechnet")
    matrix = {  # who: (see list, download, upload)
        "admin": (True, True, True), "Anna": (True, True, True), "Carl": (True, True, True), "Bob": (True, True, False),
        "Vera": (True, True, False), "Kim": (False, False, False), "Cus": (True, True, False), "Cuz": (True, True, True)}
    for who, (see, down, up) in matrix.items():
        r = c.get("/api/tausch?area=all", headers=H[who])
        vis = r.status_code == 200 and any(f["id"] == fid for f in r.get_json().get("files", []))
        ok(vis == see, f"{who}: Liste sehen {vis} statt {see} ({r.status_code})")
        r = c.get("/tausch", headers=H[who])
        ok((r.status_code == 200) == see, f"{who}: Seite /tausch {r.status_code}")
        r = c.get(f"/tausch/dl/{fid}", headers=H[who])
        ok((r.status_code == 200) == down, f"{who}: Download {r.status_code} statt {down}")
        code, j = api(who, {"action": "start", "name": "x.jpg", "size": 3, "area": "all"})
        ok((code == 200) == up, f"{who}: Hochladen {code} statt {up}")
        if code == 200:
            api(who, {"action": "abort", "id": j["id"]})
    r = c.get(f"/tausch/dl/{fid}", headers=H["Anna"])
    ok(r.headers.get("Content-Disposition", "").startswith("attachment") and r.headers.get("X-Content-Type-Options") == "nosniff"
       and "sandbox" in r.headers.get("Content-Security-Policy", ""), f"Download-Kopfzeilen {dict(r.headers)}")
    ok(c.get(f"/tausch/dl/{fid}").status_code == 401, "Download ohne Anmeldung -> 401")
    r = c.get("/api/users", headers=H["admin"])
    uu = {u["name"]: u["perms"] for u in r.get_json()["users"]}
    ok({"files_view", "files_down", "files_up"} <= set(uu["Anna"]) and "files_admin" not in uu["Anna"], f"Benutzerliste Familie {uu['Anna']}")
    ok(not set(uu["Kim"]) & {"files_view", "files_down", "files_up", "files_admin"}, "Kind: keine Datei-Rechte")
    ok(set(uu["Cus"]) >= {"files_view", "files_down"} and "files_up" not in uu["Cus"], f"Eigene Rechte files_down -> ansehen dazu {uu['Cus']}")
    page = c.get("/settings", headers=H["admin"]).get_data(as_text=True)
    ok('"files_admin", "🗂"' in page, "Benutzer-Editor kennt die 4 Datei-Rechte")
    more = c.get("/more", headers=H["Kim"]).get_data(as_text=True)
    ok('a[href="/tausch"]' in more and "display:none" in more, "Kind: Mehr-Eintrag versteckt (CSS)")

    print("A) CSRF, private Dateien, Löschregeln, Ordner", flush=True)
    r = c.post("/api/tausch", json={"action": "mkdir", "name": "Böse"}, headers=dict(H["Anna"], Origin="https://evil.example"))
    ok(r.status_code == 403, f"fremde Origin abgewiesen {r.status_code}")
    code, j = upload("Anna", "Tagebuch.jpg", jpg, area="mine")
    pid = j.get("file", {}).get("id", "")
    ok(code == 200, "privat hochladen")
    ok(c.get(f"/tausch/dl/{pid}", headers=H["Bob"]).status_code == 404, "privat: Bob sieht es nicht")
    ok(c.get(f"/tausch/dl/{pid}", headers=H["Carl"]).status_code == 404, "privat: Carl (Familie) sieht es nicht")
    ok(any(f["id"] == pid for f in c.get("/api/tausch?area=mine", headers=H["admin"]).get_json()["files"]), "privat: Admin sieht es")
    ok(any(f["id"] == pid for f in c.get("/api/tausch?area=mine", headers=H["Cuz"]).get_json()["files"]), "privat: files_admin sieht es")
    ok(api("Bob", {"action": "delete", "id": fid})[0] == 400, "Freund löscht fremde Datei nicht")
    ok(api("Carl", {"action": "delete", "id": fid})[0] == 400, "Familie löscht fremde Datei nicht")
    ok(api("Anna", {"action": "mkdir", "name": "Ferien 2026"})[0] == 200, "Ordner anlegen")
    ok(api("Bob", {"action": "mkdir", "name": "X"})[0] == 400, "Freund: kein Ordner")
    ok(api("Anna", {"action": "mkdir", "name": "../../etc"})[0] == 200 and not os.path.exists(os.path.join(root, "..", "etc_x")), "Ordner-Name mit ../ nur ein Name")
    code, j = upload("Carl", "Strand.jpg", jpg, folder="Ferien 2026")
    ok(code == 200 and j["file"]["folder"] == "Ferien 2026", "in Ordner hochladen")
    ok(upload("Anna", "y.jpg", jpg, folder="gibt-es-nicht")[0] == 400, "unbekannter Ordner")
    ok(api("Anna", {"action": "rmdir", "name": "Ferien 2026"})[0] == 400, "voller Ordner: nur Admin")
    ok(api("admin", {"action": "rmdir", "name": "Ferien 2026", "force": True})[0] == 200, "Admin löscht vollen Ordner")
    ok(not any(m.get("folder") == "Ferien 2026" for m in TZ["files"].values()), "Dateien des Ordners weg")
    ok(api("Anna", {"action": "delete", "id": pid})[0] == 200, "eigene Datei löschen")
    ok(not os.path.exists(os.path.join(root, "f", pid + ".bin")), "Datei auf dem Speicher weg")

    print("A) Namen, Programme, aktive Inhalte", flush=True)
    names = {"../../../etc/passwd.jpg": "passwd.jpg", "..\\..\\win.jpg": "win.jpg", "C:\\Users\\x\\Bild.jpg": "Bild.jpg",
             "CON.jpg": "_CON.jpg", "a<b>c.jpg": "a_b_c.jpg", "Ca\u0301fe\u0301.jpg": "C\u00e1f\u00e9.jpg", "x\x00y.jpg": "xy.jpg"}
    for raw, want in names.items():
        code, j = upload("Anna", raw, jpg)
        ok(code == 200 and j["file"]["name"] == want, f"Name {raw!r} -> {j.get('file', {}).get('name')} statt {want}")
    for raw in (".htaccess", ".bashrc.jpg", "..", "   ", "virus.exe", "a.sh", "b.PY", "Rechnung\u202egpj.exe", "x.jpg.bat", "app.apk", "s.js"):
        code, j = api("Anna", {"action": "start", "name": raw, "size": 4, "area": "all"})
        ok(code == 400, f"abgelehnt {raw!r}: {code}")
    code, j = upload("Anna", "harmlos.jpg", b"MZ\x90\x00" + b"\0" * 100)
    ok(code == 400 and "Programm" in (j.get("error") or ""), f"MZ-Inhalt als .jpg abgelehnt: {j}")
    ok(not glob.glob(os.path.join(root, "up", "*.part")), "abgelehnter Upload ohne Rest")
    code, j = upload("Anna", "bild.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')
    sid = j.get("file", {}).get("id", "")
    ok(code == 200 and j["file"]["risky"] and not j["file"]["thumb"], "SVG gespeichert, ohne Vorschau")
    r = c.get(f"/tausch/dl/{sid}", headers=H["Anna"])
    ok(r.mimetype == "application/octet-stream" and r.headers["Content-Disposition"].startswith("attachment"), f"SVG nur als Download {r.mimetype}")
    ok(c.get(f"/tausch/view/{sid}", headers=H["Anna"]).status_code == 415, "SVG nie im Browser")
    for bad in ("..%2F..%2Fversions.json", "../../x", "0123456789abcdeg", "%00"):
        ok(c.get("/tausch/dl/" + bad, headers=H["Anna"]).status_code in (404, 308), f"Pfad-Trick {bad}")
    ok(not [n for n in os.listdir(os.path.join(root, "f")) if not re.match(r"^[0-9a-f]{16}\.(bin|json)$", n)], "nur Nummern-Dateien auf dem Speicher")

    print("A) Grenzen", flush=True)
    code, j = api("Anna", {"action": "start", "name": "gross.mp4", "size": 201 * MB, "area": "all"})
    ok(code == 400 and "200 MB" in j.get("error", ""), f"pro Datei 200 MB: {j}")
    CFG["tausch_file_mb"] = 2000.0
    code, j = api("Anna", {"action": "start", "name": "g1.mp4", "size": 900 * MB, "area": "all"})
    ok(code == 200, f"900 MB reserviert {j}")
    code2, j2 = api("Anna", {"action": "start", "name": "g2.mp4", "size": 200 * MB, "area": "all"})
    ok(code2 == 400 and "Dein Platz" in j2.get("error", ""), f"pro Benutzer 1 GB (mit Reservierung): {j2}")
    ok(api("Anna", {"action": "abort", "id": j["id"]})[0] == 200, "abbrechen gibt Platz frei")
    ok(api("Anna", {"action": "start", "name": "g2.mp4", "size": 200 * MB, "area": "all"})[0] == 200, "danach wieder Platz")
    TZ["ups"].clear()
    CFG["tausch_total_gb"] = 0.5
    code, j = api("admin", {"action": "start", "name": "a.mp4", "size": 600 * MB, "area": "all"})
    ok(code == 400 and "voll" in j.get("error", ""), f"gesamt (hier 0,5 GB): {j}")
    CFG["tausch_total_gb"] = 5.0
    CFG["tausch_file_mb"] = 200.0
    free["n"] = 2 * GB + 100
    code, j = api("Anna", {"action": "start", "name": "k.jpg", "size": 1000, "area": "all"})
    ok(code == 400 and "2 GB frei" in j.get("error", ""), f"2 GB frei lassen: {j}")
    free["n"] = 100 * GB
    code, j = upload("Anna", "lang.bin.txt", b"x" * (3 * MB), finish=False, chunk=MB)
    uid = j.get("id")
    free["n"] = 2 * GB - 20 * MB
    code, j = upload("Anna", "lang.bin.txt", b"x" * (5 * MB), finish=False)
    ok(code in (400, 507), f"freier Platz beim Stück geprüft: {code} {j}")
    free["n"] = 100 * GB
    TZ["ups"].clear()
    q = c.get("/api/tausch", headers=H["Anna"]).get_json()["quota"]
    ok(q["total"] == 5 * GB and q["user_max"] == GB and q["min_free"] == 2 * GB and q["file_max"] == 200 * MB, f"Quota-Werte {q}")

    print("A) Stücke: Stelle, fortsetzen, zu gross, abbrechen", flush=True)
    data = os.urandom(5 * MB)
    code, j = api("Bob" if False else "Anna", {"action": "start", "name": "film.mp4", "size": len(data), "area": "all", "lastmod": 77})
    uid = j["id"]
    r = c.post(f"/api/tausch/chunk?id={uid}&off=5", data=b"abc", headers=H["Anna"])
    ok(r.status_code == 409 and r.get_json()["have"] == 0, "falsche Stelle -> 409 mit have")
    r = c.post(f"/api/tausch/chunk?id={uid}&off=0", data=data[:2 * MB], headers=H["Anna"])
    ok(r.status_code == 200 and r.get_json()["have"] == 2 * MB, "erstes Stück")
    ok(api("Anna", {"action": "finish", "id": uid})[0] == 400, "unfertig: nicht abschliessen")
    code, j = api("Anna", {"action": "start", "name": "film.mp4", "size": len(data), "area": "all", "lastmod": 77})
    ok(j.get("id") == uid and j.get("have") == 2 * MB and j.get("resumed"), f"gleiche Datei: fortsetzen {j}")
    r = c.post(f"/api/tausch/chunk?id={uid}&off={2 * MB}", data=data[2 * MB:], headers=H["Bob"])
    ok(r.status_code in (403, 404), "fremder Upload: Bob darf nicht weiterschreiben")
    r = c.post(f"/api/tausch/chunk?id={uid}&off={2 * MB}", data=b"x" * (9 * MB), headers=H["Anna"])
    ok(r.status_code == 413, f"zu grosses Stück vor dem Lesen abgewiesen {r.status_code}")
    r = c.post(f"/api/tausch/chunk?id={uid}&off={2 * MB}", data=data[2 * MB:], headers=H["Anna"])
    ok(r.status_code == 200, "Rest")
    code, j = api("Anna", {"action": "finish", "id": uid})
    ok(code == 200 and open(os.path.join(root, "f", j["file"]["id"] + ".bin"), "rb").read() == data, "Datei vollständig und gleich")
    code, j = api("Anna", {"action": "start", "name": "weg.mp4", "size": 10, "area": "all"})
    api("Anna", {"action": "abort", "id": j["id"]})
    ok(not os.path.exists(os.path.join(root, "up", j["id"] + ".part")), "abbrechen löscht das Stück")
    TZ["files"] = None; TZ["root"] = None                 # restart: the open upload survives
    code, j = api("Anna", {"action": "start", "name": "neu.mp4", "size": 10, "area": "all", "lastmod": 5})
    c.post(f"/api/tausch/chunk?id={j['id']}&off=0", data=b"12345", headers=H["Anna"])
    TZ["files"] = None; TZ["root"] = None
    code, j2 = api("Anna", {"action": "start", "name": "neu.mp4", "size": 10, "area": "all", "lastmod": 5})
    ok(j2.get("have") == 5, f"nach Neustart fortsetzen {j2}")
    api("Anna", {"action": "abort", "id": j2["id"]})

    print("A) Push gebündelt, nur an den Admin", flush=True)
    sent.clear(); TZ["push"].clear()
    for i in range(3):
        upload("Anna", f"p{i}.jpg", jpg)
    upload("admin", "admin.jpg", jpg)
    ok(ns["tausch_push_tick"](time.time() + 30) == [], "noch nicht (90 s Ruhe)")
    ok(ns["tausch_push_tick"](time.time() + 200) == ["Anna hat 3 Dateien hochgeladen"] and sent == [("admin", "Anna hat 3 Dateien hochgeladen")], f"Bündel {sent}")
    tl = ns["_TZ_TL"]; tl.admin_only = True
    ok(ns["users_push_dispatch"]("t", "x", "info") == 0, "Admin-Meldung erreicht keine Benutzer")
    tl.admin_only = False
    CFG["push_level"] = "persons"; upload("Anna", "q.jpg", jpg); sent.clear()
    ok(ns["tausch_push_tick"](time.time() + 200) == [] and not sent, "«nur Personen»: kein Push")
    CFG["push_level"] = "all"

    print("A) Texte: Version, Konflikt, Verlauf, Wiederherstellen", flush=True)
    code, j = api("Anna", {"action": "newtext", "name": "Einkauf.md", "area": "all", "text": "# Liste\n- Brot"})
    tid = j["file"]["id"]
    ok(code == 200 and j["file"]["kind"] == "text" and j["file"]["edit"], "Text anlegen")
    r = c.get(f"/api/tausch/text?id={tid}", headers=H["Carl"]).get_json()
    ok(r["ver"] == 1 and r["edit"] and r["md"], "Carl lädt Version 1")
    ok(api("Anna", {"action": "save", "id": tid, "text": "# Liste\n- Brot\n- Milch", "ver": 1})[0] == 200, "Anna speichert")
    code, j = api("Carl", {"action": "save", "id": tid, "text": "# Liste\n- Käse", "ver": 1})
    ok(code == 409 and j.get("conflict") and j.get("by") == "Anna" and "Inzwischen hat Anna etwas geändert" in j.get("error", "")
       and "Milch" in j.get("text", ""), f"Konflikt: {code} {j}")
    ok(api("Carl", {"action": "save", "id": tid, "text": "# Liste\n- Käse", "ver": j["ver"]})[0] == 200, "überschreiben mit neuer Version")
    ok(api("Bob", {"action": "save", "id": tid, "text": "x", "ver": 3})[0] == 400, "Freund: nicht bearbeiten")
    ok(c.get(f"/api/tausch/text?id={tid}", headers=H["Bob"]).get_json().get("edit") is False, "Freund: nur lesen")
    for i in range(22):
        v = c.get(f"/api/tausch/text?id={tid}", headers=H["Anna"]).get_json()["ver"]
        api("Anna", {"action": "save", "id": tid, "text": f"Stand {i}\n" + "x" * 1000, "ver": v})
    t_ = c.get(f"/api/tausch/text?id={tid}", headers=H["Anna"]).get_json()
    m = TZ["files"][tid]
    ok(len(t_["hist"]) == 20 and len(os.listdir(os.path.join(root, "h", tid))) == 20, f"20 Versionen behalten ({len(t_['hist'])})")
    ok(m["hist_size"] > 19000 and ns["tausch_usage"]("anna")[0] >= m["size"] + m["hist_size"], "Versionen zählen im Platz des Besitzers")
    oldv = t_["hist"][-1]["v"]
    oldtxt = c.get(f"/api/tausch/text?id={tid}&v={oldv}", headers=H["Anna"]).get_json()["text"]
    code, j = api("Anna", {"action": "restore", "id": tid, "v": oldv, "ver": t_["ver"]})
    ok(code == 200 and c.get(f"/api/tausch/text?id={tid}", headers=H["Anna"]).get_json()["text"] == oldtxt, "Wiederherstellen")
    ok(api("Anna", {"action": "restore", "id": tid, "v": 1, "ver": j.get("ver")})[0] == 400, "zu alte Version: nicht mehr da")
    big = "x" * (1024 * 1024 + 5)
    ok(api("Anna", {"action": "save", "id": tid, "text": big, "ver": j["ver"]})[0] == 400, "über 1 MB abgelehnt")
    code, j = api("Anna", {"action": "newtext", "name": "geheim", "area": "mine", "text": "nur ich"})
    gid = j["file"]["id"]
    ok(j["file"]["name"] == "geheim.txt" and c.get(f"/api/tausch/text?id={gid}", headers=H["Carl"]).status_code == 404, "privater Text: andere nicht")

    print("A) Chat: anhängen, Rechte, ändern, warten, Push", flush=True)
    code, j = api("Anna", {"action": "newchat", "name": "Ferienplanung", "area": "all"})
    cid = j["file"]["id"]
    ok(code == 200 and j["file"]["name"] == "Ferienplanung.chat" and j["file"]["kind"] == "chat", "Chat anlegen")
    ok(api("Anna", {"action": "start", "name": "x.chat", "size": 3, "area": "all"})[0] == 400, ".chat nicht hochladen")
    xss = '<img src=x onerror="window.__xss=1"><script>window.__xss=1</script>'
    ok(api("Anna", {"action": "post", "id": cid, "text": xss})[0] == 200, "Anna schreibt")
    ok(api("Bob", {"action": "post", "id": cid, "text": "hi"})[0] == 400, "Freund: nur lesen")
    ok(api("Anna", {"action": "post", "id": cid, "text": "  \n "})[0] == 400, "leere Nachricht")
    ok(api("Anna", {"action": "post", "id": cid, "text": "x" * 4097})[0] == 400, "über 4 KB")
    j0 = c.get(f"/api/tausch/chat?id={cid}&rev=-1", headers=H["Carl"]).get_json()
    ok(j0["posts"][0]["x"] == xss and j0["posts"][0]["by"] == "Anna" and j0["write"], "Inhalt als Daten, Name vom Server")
    res = {}

    def warten():
        t0 = time.time()
        r = app.test_client(use_cookies=False).get(f"/api/tausch/chat?id={cid}&rev={j0['rev']}&after=1&wait=1", headers=H["Bob"])
        res.update(dt=time.time() - t0, j=r.get_json())
    th = threading.Thread(target=warten); th.start()
    time.sleep(1.0)
    sent.clear(); TZ["push"].clear()
    api("Carl", {"action": "post", "id": cid, "text": "Ich bringe das Zelt"})
    th.join(10)
    ok(res.get("j", {}).get("posts", [{}])[0].get("x") == "Ich bringe das Zelt" and 0.8 < res.get("dt", 99) < 4, f"wartende Anfrage bekommt den neuen Beitrag {res}")
    api("Carl", {"action": "post", "id": cid, "text": "und Kocher"})
    api("Anna", {"action": "post", "id": cid, "text": "super"})
    out = sorted(ns["tausch_push_tick"](time.time() + 200))
    ok(sorted(sent) == [("Anna", "Carl hat 2× geschrieben in «Ferienplanung»"), ("Carl", "Anna hat geschrieben in «Ferienplanung»")],
       f"Push an Mitschreibende ohne Autor, ohne Inhalt: {sent}")
    ok(not any("Zelt" in x[1] or "Kocher" in x[1] for x in sent), "kein Inhalt im Push")
    posts = c.get(f"/api/tausch/chat?id={cid}&rev=-1", headers=H["Carl"]).get_json()["posts"]
    n_carl = next(p["n"] for p in posts if p["x"] == "und Kocher")
    n_anna = posts[0]["n"]
    ok(api("Carl", {"action": "chat_edit", "id": cid, "n": n_carl, "text": "und der Kocher"})[0] == 200, "eigene Nachricht ändern")
    ok(api("Carl", {"action": "chat_edit", "id": cid, "n": n_anna, "text": "gefälscht"})[0] == 400, "fremde Nachricht nicht ändern")
    ok(api("Carl", {"action": "chat_del", "id": cid, "n": n_anna})[0] == 400, "fremde Nachricht nicht löschen")
    ok(api("admin", {"action": "chat_del", "id": cid, "n": n_anna})[0] == 200, "Admin löscht jede")
    for x_ in ns["_tz_chat"](TZ["files"][cid])["posts"]:
        if x_["n"] == n_carl:
            x_["t"] -= 400
    ok(api("Carl", {"action": "chat_edit", "id": cid, "n": n_carl, "text": "zu spät"})[0] == 400, "nach 5 Minuten nicht mehr")
    TZ["chats"].clear()
    j1 = c.get(f"/api/tausch/chat?id={cid}&rev=-1", headers=H["Carl"]).get_json()
    ok([p["del"] for p in j1["posts"]][0] and any(p["x"] == "und der Kocher" and p["ed"] for p in j1["posts"]), "nach Neuladen: gelöscht / geändert bleibt")
    rw = ns["TZ_WAIT_IP"]
    ths = []
    for _i in range(rw + 1):
        t_th = threading.Thread(target=lambda: app.test_client(use_cookies=False).get(f"/api/tausch/chat?id={cid}&rev={j1['rev']}&wait=1", headers=H["Bob"]))
        t_th.start(); ths.append(t_th)
    time.sleep(0.8)
    ok(TZ["waiting"] <= rw, f"höchstens {rw} wartende Anfragen pro Adresse ({TZ['waiting']})")
    api("Anna", {"action": "post", "id": cid, "text": "weckt alle"})
    for t_th in ths:
        t_th.join(10)
    ok(TZ["waiting"] == 0, "alle wartenden Anfragen beendet")
    code, j = api("Anna", {"action": "newchat", "name": "Privat", "area": "mine"})
    pcid = j["file"]["id"]
    api("Anna", {"action": "post", "id": pcid, "text": "nur für mich"})
    ok(c.get(f"/api/tausch/chat?id={pcid}&rev=-1", headers=H["Carl"]).status_code == 404, "privater Chat: andere nicht")

    print("A) Gast: nur «Für alle», nur Vorschau, Ablauf", flush=True)
    ns["guest_set"]("create", 1)
    tok = CFG["guest_token"]
    r = c.get(f"/g/{tok}/tausch/list")
    gl = r.get_json()
    ids = {f["id"] for f in gl["files"]}
    ok(r.status_code == 200 and fid in ids and sid not in ids and gid not in ids and pcid not in ids, "Gast: Für alle, ohne SVG / Privates")
    ok("by" not in json.dumps(gl["files"]) or all("by" not in f for f in gl["files"]), "Gast: keine Namen der Hochlader")
    ok(c.get(f"/g/{tok}/tausch/t/{fid}.jpg").status_code == 200 and c.get(f"/g/{tok}/tausch/p/{fid}.jpg").status_code == 200, "Gast: Vorschaubilder")
    ok(c.get(f"/g/{tok}/tausch/t/{sid}.jpg").status_code == 404, "Gast: kein SVG")
    ok(c.get(f"/g/{tok}/tausch/text/{tid}").status_code == 200 and c.get(f"/g/{tok}/tausch/text/{gid}").status_code == 404, "Gast: Texte nur Für alle")
    gc = c.get(f"/g/{tok}/tausch/chat/{cid}").get_json()
    ok(gc.get("ok") and not any("k" in p or "mine" in p for p in gc["posts"]), "Gast: Chat lesen ohne Schlüssel")
    ok(c.get(f"/g/{tok}/tausch/chat/{pcid}").status_code == 404, "Gast: kein privater Chat")
    ok(c.get(f"/tausch/dl/{fid}").status_code == 401 and c.post("/api/tausch", json={"action": "start", "name": "a.jpg", "size": 1}).status_code == 401,
       "Gast: kein Download, kein Hochladen")
    ok("gfiles" in c.get(f"/g/{tok}").get_data(as_text=True), "Gast-Seite: Link zu den Dateien")
    CFG["guest_until"] = time.time() - 5
    ok(c.get(f"/g/{tok}/tausch/list").status_code == 404 and c.get(f"/g/{tok}/tausch/t/{fid}.jpg").status_code == 404, "Gast abgelaufen: nichts mehr")
    CFG["guest_until"] = 0.0
    CFG["tausch_guest"] = False
    ok(c.get(f"/g/{tok}/tausch/list").status_code == 404, "Schalter tausch_guest aus")
    CFG["tausch_guest"] = True

    print("A) Aus, fehlender Stick", flush=True)
    CFG["tausch_on"] = False
    ok(api("Anna", {"action": "start", "name": "a.jpg", "size": 3})[0] == 400, "aus: kein Hochladen")
    ok(c.get("/api/tausch", headers=H["Anna"]).get_json()["on"] is False, "aus: Liste meldet es")
    CFG["tausch_on"] = True
    TZ["root_test"] = None
    CFG["storage_path"] = "/media/gibt-es-nicht-tz"
    j = c.get("/api/tausch", headers=H["Anna"]).get_json()
    ok(j["store"]["problem"] == "missing" and api("Anna", {"action": "start", "name": "a.jpg", "size": 3})[0] == 400, "Stick fehlt: nie still auf die Karte")
    CFG["storage_path"] = ""
    TZ["root_test"] = root
    shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(datei, bilder):
    from playwright.sync_api import sync_playwright
    import numpy as np
    import cv2
    tmp = tempfile.mkdtemp(prefix="mw_tz_b_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "theme": "dark",
          "tausch_free_gb": 0.5}                               # this test needs little room (the guard itself: part A)
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    PW = "Tausch-" + os.urandom(4).hex()
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg, "--web-password", PW],
                         stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user=("admin", PW), raw=None, ctype="application/json", method=None):
        r = urllib.request.Request(base + path, data=raw if raw is not None else (json.dumps(data).encode() if data is not None else None),
                                   headers=dict(basic(*user), **{"Content-Type": ctype}), method=method)
        try:
            with op.open(r, timeout=30) as x:
                return x.status, x.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt")).read()[-3000:])
            try:
                if req("/manifest.webmanifest")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        req("/api/users", {"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
        req("/api/users", {"action": "add", "name": "Carl", "password": "carl-pass-1", "role": "family"})
        A, Cu = ("Anna", "anna-pass-1"), ("Carl", "carl-pass-1")

        def up(name, data, user=A, area="all", folder=""):
            c, b = req("/api/tausch", {"action": "start", "name": name, "size": len(data), "area": area, "folder": folder}, user)
            j = json.loads(b); off = 0
            if "id" not in j:
                raise SystemExit(f"Hochladen {name} als {user[0]}: {c} {j}")
            while off < len(data):
                c, b = req(f"/api/tausch/chunk?id={j['id']}&off={off}", raw=data[off:off + j["chunk"]], user=user, ctype="application/octet-stream")
                off = json.loads(b)["have"]
            return json.loads(req("/api/tausch", {"action": "finish", "id": j["id"]}, user)[1])
        req("/api/tausch", {"action": "mkdir", "name": "Ferien 2026"}, A)
        cols = [(40, 120, 230), (60, 180, 90), (200, 120, 40), (150, 80, 200), (30, 160, 220)]
        for i, col in enumerate(cols):
            im = np.zeros((480, 640, 3), np.uint8); im[:] = col
            cv2.circle(im, (320, 240), 120 + i * 10, (255, 255, 255), -1); cv2.putText(im, f"Bild {i + 1}", (230, 260), cv2.FONT_HERSHEY_SIMPLEX, 2, (40, 40, 40), 4)
            up(f"Zeltplatz_{i + 1}.jpg", cv2.imencode(".jpg", im)[1].tobytes(), user=A if i % 2 else Cu)
        vp = os.path.join(tmp, "clip.mp4")
        vw = cv2.VideoWriter(vp, cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
        for k in range(30):
            fr = np.zeros((240, 320, 3), np.uint8); fr[:] = (30, 30, 30); cv2.circle(fr, (40 + k * 8, 120), 30, (0, 200, 255), -1); vw.write(fr)
        vw.release()
        up("Fuchs_in_der_Nacht.mp4", open(vp, "rb").read())
        pdf = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
               b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]/Contents 4 0 R/Resources<<>>>>endobj "
               b"4 0 obj<</Length 44>>stream\n0.2 0.5 0.9 rg 20 20 260 160 re f\nendstream endobj\ntrailer<</Root 1 0 R>>\n%%EOF")
        up("Platzordnung.pdf", pdf, user=Cu)
        up("Packliste.docx", b"PK\x03\x04" + b"0" * 2000)
        up("Notiz.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>")
        MDTXT = ("# Ferienplan\n\n**Abfahrt** Samstag 8 Uhr\n\n- Zelt\n- Kocher\n- *Schlafsäcke*\n\n> Wetter prüfen!\n\n"
                 "<script>window.__xss=1</script>\n[gefährlich](javascript:window.__xss=1) · [MeteoSchweiz](https://www.meteoschweiz.admin.ch)")
        md = json.loads(req("/api/tausch", {"action": "newtext", "name": "Ferienplan.md", "area": "all", "text": MDTXT}, A)[1])["file"]
        chat = json.loads(req("/api/tausch", {"action": "newchat", "name": "Ferienplanung", "area": "all"}, A)[1])["file"]
        for who, txt in ((A, "Wer bringt das Zelt mit?"), (Cu, "Ich! Und den Kocher 🔥"), (A, "Super 👍 Treffpunkt 8 Uhr beim Parkplatz"),
                         (Cu, '<img src=x onerror="window.__xss=1"> nur Text')):
            req("/api/tausch", {"action": "post", "id": chat["id"], "text": txt}, who)
        up("Tagebuch.jpg", cv2.imencode(".jpg", np.full((200, 200, 3), 90, np.uint8))[1].tobytes(), area="mine")
        time.sleep(3)
        req("/api/guest", {"action": "create", "hours": 2})
        gtok = json.loads(req("/api/guest")[1])["path"]
        os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            for name, vp_, mob in (("iphone", {"width": 390, "height": 844}, True), ("desktop", {"width": 1366, "height": 900}, False)):
                ctx = br.new_context(viewport=vp_, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                     http_credentials={"username": "Anna", "password": "anna-pass-1"}, locale="de-CH")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark')}catch(e){}")
                cur0 = json.loads(req(f"/api/tausch/text?id={md['id']}", user=A)[1])
                if cur0["text"] != MDTXT:
                    req("/api/tausch", {"action": "save", "id": md["id"], "text": MDTXT, "ver": cur0["ver"]}, A)
                pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                pg.goto(base + "/tausch"); pg.wait_for_selector(".tz-it img", timeout=15000); pg.wait_for_timeout(1500)
                pg.screenshot(path=os.path.join(bilder, f"tausch_{name}.png"), full_page=True)
                ok("belegt" in pg.inner_text("#tz-qt1"), f"{name}: Quota-Zeile «… von … belegt»")
                ok(pg.locator("#tz-mkt").is_visible() and pg.locator("#tz-mkc").is_visible(), f"{name}: Neuer Text / Neuer Chat")
                # upload through the page (pieces of 2 MB)
                big = os.path.join(tmp, f"gross_{name}.bin.zip"); open(big, "wb").write(os.urandom(5 * 1024 * 1024 + 123))
                pg.set_input_files("#tz-file", big)
                pg.wait_for_selector(".tz-job", timeout=5000)
                if not mob:
                    pg.wait_for_timeout(300); pg.screenshot(path=os.path.join(bilder, "tausch_upload_desktop.png"))
                pg.wait_for_function("() => [...document.querySelectorAll('.tz-it .nm')].some(e => e.textContent.startsWith('gross_'))", timeout=60000)
                ok(True, f"{name}: Upload über die Seite")
                if not mob:
                    pg.click("#tz-view"); pg.wait_for_timeout(500)
                    pg.screenshot(path=os.path.join(bilder, "tausch_desktop_liste.png"), full_page=True); pg.click("#tz-view")
                # editor with preview, then a conflict
                pg.locator(".tz-it", has_text="Ferienplan.md").locator(".th").click()
                pg.wait_for_selector("#tz-ta"); pg.click("#tz-pv"); pg.wait_for_timeout(300)
                html_ = pg.inner_html("#tz-mdv")
                ok("<script" not in html_ and 'href="javascript' not in html_ and "&lt;script&gt;" in html_ and "<b>Abfahrt</b>" in html_ and 'href="https://www.meteoschweiz.admin.ch"' in html_,
                   f"{name}: Markdown sicher ({html_[:200]})")
                pg.screenshot(path=os.path.join(bilder, f"tausch_editor_md_{name}.png"))
                pg.click("#tz-pv"); pg.fill("#tz-ta", "# Ferienplan\n\nAnna war hier.")
                cur = json.loads(req(f"/api/tausch/text?id={md['id']}", user=Cu)[1])
                req("/api/tausch", {"action": "save", "id": md["id"], "text": cur["text"] + "\nCarl auch.", "ver": cur["ver"]}, Cu)
                pg.click("#tz-save")
                try:
                    pg.wait_for_selector("#tz-conflict", timeout=5000)
                except Exception:
                    pg.screenshot(path=os.path.join(bilder, f"tausch_FEHLER_{name}.png"))
                    r_ = pg.evaluate("""async (id) => { const r = await fetch('/api/tausch', {method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({action: 'save', id: id, text: 'x', ver: 1})}); return r.status + ' ' + await r.text(); }""", md["id"])
                    raise SystemExit("kein Konflikt-Feld: " + pg.inner_text(".tz-edf") + " · " + str(errs) + " · " + r_[:300]
                                     + " · Carl: " + str(cur)[:200])
                ok("Inzwischen hat Carl etwas geändert" in pg.inner_text("#tz-conflict"), f"{name}: Konflikt-Meldung")
                pg.click("#tz-c-diff"); pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(bilder, f"tausch_konflikt_{name}.png"))
                pg.click("#tz-c-over"); pg.wait_for_timeout(800)
                now = json.loads(req(f"/api/tausch/text?id={md['id']}", user=A)[1])
                ok(now["text"] == "# Ferienplan\n\nAnna war hier." and len(now["hist"]) >= 2, f"{name}: überschrieben, Versionen da")
                pg.click("#tz-hist"); pg.wait_for_selector("#tz-versions"); pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(bilder, f"tausch_versionen_{name}.png"))
                pg.evaluate("document.getElementById('tz-editor').remove()")
                # chat: live delivery without reload
                pg.locator(".tz-it", has_text="Ferienplanung").locator(".th").click()
                pg.wait_for_selector("#tz-cl .tz-bub"); pg.wait_for_timeout(800)
                req("/api/tausch", {"action": "post", "id": chat["id"], "text": f"Live-Test {name} von Carl"}, Cu)
                t0 = time.time()
                pg.wait_for_function(f"() => document.getElementById('tz-cl').innerText.includes('Live-Test {name} von Carl')", timeout=15000)
                ok(time.time() - t0 < 8, f"{name}: neuer Beitrag erscheint ohne Neuladen ({time.time() - t0:.1f} s)")
                pg.fill("#tz-cin", f"Antwort aus dem Browser ({name})"); pg.click("#tz-csend")
                pg.wait_for_function(f"() => document.getElementById('tz-cl').innerText.includes('Antwort aus dem Browser ({name})')", timeout=8000)
                ok(pg.evaluate("() => !window.__xss && !document.querySelector('#tz-cl img')"), f"{name}: Chat ohne HTML-Einschleusung")
                pg.wait_for_timeout(400)
                pg.screenshot(path=os.path.join(bilder, f"tausch_chat_{name}.png"))
                ok(not errs, f"{name}: JavaScript-Fehler {errs}")
                ctx.close()
            ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, locale="de-CH")
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(base + gtok + "/tausch"); pg.wait_for_selector(".it img", timeout=15000); pg.wait_for_timeout(800)
            pg.screenshot(path=os.path.join(bilder, "tausch_gast_iphone.png"), full_page=True)
            txt = pg.inner_text("main")
            ok("Tagebuch" not in txt and "Notiz.svg" not in txt, "Gast: nichts Privates, kein SVG")
            pg.locator(".it", has_text="Ferienplanung").click(); pg.wait_for_selector(".bub"); pg.wait_for_timeout(300)
            ok(pg.evaluate("() => !window.__xss"), "Gast: Chat sicher")
            pg.screenshot(path=os.path.join(bilder, "tausch_gast_chat_iphone.png"))
            ok(not errs, f"Gast: JavaScript-Fehler {errs}")
            ctx.close()
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Test Datentausch (639zzc)")
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true", help="dazu MoveEye starten, Seite im Browser, Bildschirmfotos")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "tausch_bilder"))
    ap.add_argument("--nur-browser", action="store_true")
    a = ap.parse_args()
    datei = a.datei or neueste()
    t0 = time.time()
    if not a.nur_browser:
        teil_a(datei)
    if a.browser or a.nur_browser:
        print("B) Browser und Bildschirmfotos -> " + a.bilder, flush=True)
        teil_b(datei, a.bilder)
    print(f"{N['ok']} Prüfungen ok, {len(FEHLER)} Fehler ({time.time() - t0:.0f} s)")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
