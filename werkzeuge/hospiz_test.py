#!/usr/bin/env python3
"""Live-Test «Das Hospiz» gegen einen laufenden 3D-Simulator (Code-Prüfung H1 + Knopf «Ohne Passwort starten», 31.10.2026).

Stellt den alten Umgehungsweg nach (/control «spielbereich story weiter horror» + «gs next»: startete das Hospiz ohne
Passwort) und prüft, dass er jetzt abgelehnt wird; dazu /control «horror start», den Kapitel-Sprung, «ohne_passwort» von
einem fremden Gerät (eigene Netz-Adresse dieses Rechners statt 127.0.0.1) und von diesem PC, und dass Passwort-Hash und
Datei unverändert bleiben.

  python3 werkzeuge/hospiz_test.py --sim http://127.0.0.1:9283 --datei <TEST-HOME>/…/bergtal_horror.json

NUR gegen einen Simulator mit eigenem Test-HOME: der Test legt (falls noch keines da ist) ein Test-Passwort fest und sperrt
das Hospiz wieder («horror sperren»). Ende: «Hospiz-Live-Test OK» (Exit 0) oder die Liste der Fehler (Exit 1).
"""
import argparse
import json
import socket
import sys
import time
import urllib.parse
import urllib.request

PW = "test-hospiz-1234"          # nur im Test-HOME


def ctl(base, d):
    req = urllib.request.Request(base + "/control", json.dumps(d).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def own_ip():
    """an address of this computer that is not 127.x - the simulator then sees a «foreign device»"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return "" if ip.startswith("127.") else ip
    except OSError:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", default="http://127.0.0.1:8765")
    ap.add_argument("--datei", default="", help="user://bergtal_horror.json des Test-HOME (Hash bleibt gleich?)")
    a = ap.parse_args()
    errs = []

    def ok(what, cond, info=None):
        print(("  ok   " if cond else "  FEHLER ") + what + ("" if cond or info is None else "  -> " + json.dumps(info, ensure_ascii=False)[:300]))
        if not cond:
            errs.append(what)

    H = lambda d: ctl(a.sim, dict(d, action="horror"))
    info = H({"do": "info"})
    if not info.get("has_password"):
        ok("Test-Passwort festlegen", H({"do": "set_password", "pw": PW}).get("ok"))
    H({"do": "sperren"})
    info = H({"do": "info"})
    ok("gesperrt wie nach einem Neustart", not info.get("unlocked") and not info.get("may_play"), info)
    hash_before = open(a.datei, encoding="utf-8").read() if a.datei else ""

    print("1. alter Umgehungsweg (H1): story weiter horror + gs next")
    r = ctl(a.sim, {"action": "spielbereich", "do": "story", "what": "weiter", "id": "horror"})
    ok("«Weiterspielen» geht zur Passwort-Abfrage", r.get("locked") is True, r)
    for _ in range(4):
        ctl(a.sim, {"action": "spielbereich", "do": "gs", "k": "next"})
    time.sleep(1.0)
    info = H({"do": "info"})
    ok("keine Warnung, kein Startbild, keine Nacht", info.get("phase") == "lock" and not info.get("running") and not info.get("unlocked"), info)
    r = ctl(a.sim, {"action": "spielbereich", "do": "story", "what": "neu", "id": "horror"})
    for _ in range(4):
        ctl(a.sim, {"action": "spielbereich", "do": "gs", "k": "next"})
    info = H({"do": "info"})
    ok("«Neu beginnen» ebenso", info.get("phase") == "lock" and not info.get("running"), info)

    print("2. weitere Wege ohne Passwort")
    r = H({"do": "start", "chapter": 1})
    ok("/control horror start -> locked", r.get("error") == "locked", r)
    r = ctl(a.sim, {"action": "dev", "do": "chapter", "area": "horror", "n": 1})
    ok("Kapitel-Sprung -> locked", r.get("ok") is False, r)
    r = ctl(a.sim, {"action": "spielbereich", "do": "start", "id": "horror"})      # what MoveEye's /api/play sends
    ok("MoveEye /api/play start horror startet nichts", not H({"do": "info"}).get("running"), r)

    print("3. «ohne Passwort» über /control")
    ip = own_ip()
    if ip:
        port = urllib.parse.urlparse(a.sim).port or 8765
        far = "http://%s:%d" % (ip, port)
        r = ctl(far, {"action": "horror", "do": "ohne_passwort"})
        ok("von einem fremden Gerät (%s) -> nur_lokal" % ip, r.get("error") == "nur_lokal" and not H({"do": "info"}).get("unlocked"), r)
        r = ctl(far, {"action": "horror", "do": "ohne_passwort", "_von_lokal": True})
        ok("gefälschtes _von_lokal -> nur_lokal", r.get("error") == "nur_lokal" and not H({"do": "info"}).get("unlocked"), r)
        r = ctl(far, {"action": "spielbereich", "do": "story", "what": "weiter", "id": "horror"})
        ok("fremdes Gerät: «Weiterspielen» -> Passwort", r.get("locked") is True, r)
    else:
        print("  (keine eigene Netz-Adresse – fremdes Gerät nicht geprüft)")
    r = H({"do": "ohne_passwort"})
    info = H({"do": "info"})
    ok("von diesem PC -> entsperrt (via knopf)", r.get("ok") and info.get("unlocked") and info.get("via") == "knopf", [r, info])
    ok("Passwort bleibt festgelegt", info.get("has_password"), info)
    if a.datei:
        ok("Datei mit dem Hash unverändert", open(a.datei, encoding="utf-8").read() == hash_before)

    print("4. danach der normale Weg: Warnung kommt trotzdem")
    H({"do": "stop"})
    r = ctl(a.sim, {"action": "spielbereich", "do": "story", "what": "weiter", "id": "horror"})
    for _ in range(4):
        g = ctl(a.sim, {"action": "spielbereich", "do": "gs", "k": "next"})
        if "step" not in g:                       # the last step: into the story (or no start open)
            break
    time.sleep(1.0)
    info = H({"do": "info"})
    ok("Warnung vor dem Start", info.get("phase") == "warn", info)

    H({"do": "sperren"})
    if errs:
        print("Hospiz-Live-Test: %d Fehler" % len(errs))
        sys.exit(1)
    print("Hospiz-Live-Test OK")


if __name__ == "__main__":
    main()
