#!/usr/bin/env python3
"""Test «Schach zu zweit mit je einem Handy» (MoveEye Teil 639zzr + games/schach/fern.js).

  1. Regeln auf dem Pi (eigener Zug-Prüfer in 639zzr): Perft-Zahlen bekannter Stellungen, dazu zufällige Partien in Node mit
     chess.js + partie.js (wie im Spiel) – bei jedem Halbzug müssen erlaubte Züge, Stellung und Spielende (Matt, Patt,
     Wiederholung, 50 Züge, zu wenig Material) auf dem Pi genau gleich sein.
  2. Vermittlung (gebaute Datei geladen, Flask-Testclient und der echte Spiele-Port): erstellen (Code aus 4 gut lesbaren
     Zeichen), beitreten (freier Platz, dann Zuschauer), Züge abwechselnd, unerlaubter Zug / Zug ausser der Reihe / falscher
     Schlüssel / Zuschauer abgelehnt, Zug doppelt geschickt (Antwort verloren) ist harmlos, Long Polling (wartet und kommt
     sofort bei einem Zug), Wiederaufnahme nach dem Neuladen auf beiden Seiten (Code + Schlüssel), Remis / Zug zurück /
     Revanche mit Annehmen, Aufgeben, Abbrechen, «Tipps sind an» für beide, Aufräumen nach 24 h und 30 min nach dem Ende,
     höchstens 10 Spiele (das älteste ruhende geht), Bremse pro Platz und pro Adresse (Codes raten), Rechte (ohne Anmeldung
     401, Kind mit «Spiele» ja, eigene Rechte ohne «Spiele» 403), Gäste über den Spieler-Link nur solange «Spiele freigeben»
     an ist, /spiele nur im eigenen WLAN, Spiele-Port: nur /schachfern/, fremde Seite (Origin) abgelehnt, keine anderen
     MoveEye-Adressen, kein Tunnel; QR-Code: echt gelesen (OpenCV) = Adresse der Seite + Code, kein Schlüssel; Datei auf dem
     Pi ohne Schlüssel im Klartext, nach einem Neustart ist das Spiel wieder da.
  3. Browser (Playwright, zwei iPhone 13 hochkant) gegen ein echtes MoveEye (--headless --demo): Handy A über den Spiele-Port
     (eigenes WLAN), Handy B über die Hauptadresse mit Anmeldung (wie Fernzugriff). Erstellen, Beitreten mit dem Code,
     Narrenmatt durch Antippen, Verbindung weg und wieder da, beide Seiten schliessen und öffnen (Handy schläft), Revanche mit
     getauschten Farben, Remis abgelehnt, Zuschauer, Hinweis «Tipps sind an». Bildschirmfotos mit --bilder ORDNER.

  python3 werkzeuge/schach_fern_test.py [--datei webcam_bewegung_X.py] [--ohne-browser] [--bilder ORDNER] [--partien 60]
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
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
SCHACH = os.path.join(REPO, "games", "schach")
FEHLER = []


def ok(c, was):
    print(("  ✓ " if c else "  ✗ ") + was, flush=True)
    if not c:
        FEHLER.append(was)
    return c


def neueste():
    fs = sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    return fs[-1]


def lan_ip():
    """eine private, nicht-lokale Adresse dieses Rechners (zählt für MoveEye als «eigenes WLAN»), sonst ''"""
    import ipaddress
    cand = []
    try:
        cand += subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5).stdout.split()
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9)); cand.append(s.getsockname()[0])
    except OSError:
        pass
    for c in cand:
        try:
            a = ipaddress.ip_address(c)
        except ValueError:
            continue
        if a.version == 4 and a.is_private and not a.is_loopback and not a in ipaddress.ip_network("100.64.0.0/10"):
            return c
    return ""


def frei_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


# ---- 1. rules: Python (Pi) against chess.js + partie.js (the game) ---------------------------------------------------------------
NODE_SKRIPT = r"""
const fs = require("fs"), vm = require("vm"), path = require("path");
vm.runInThisContext(fs.readFileSync(path.join(process.argv[2], "lib", "chess.js"), "utf8"));
const Partie = require(path.join(process.argv[2], "partie.js"));
const starts = JSON.parse(process.argv[3]), n = +process.argv[4];
let seed = 12345; const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
const out = [];
function lauf(start, vorgabe, max) {
  const p = new Partie(start), r = {start: start, zuege: [], schritte: []};
  for (let i = 0; i <= max; i++) {
    const z = p.zustand(), leg = z.ende ? [] : p.alleZuege().sort();
    r.schritte.push({fen: z.fen, leg: leg, ende: z.ende});
    if (z.ende) break;
    let u = vorgabe ? vorgabe[i] : null;
    if (!u) { if (vorgabe) break; const cap = leg.filter(m => p.figur(m.slice(2, 4)) || m.length === 5);
      u = cap.length && rnd() < 0.35 ? cap[Math.floor(rnd() * cap.length)] : leg[Math.floor(rnd() * leg.length)]; }
    if (!p.zug(u)) { r.fehler = "node: " + u; break; }
    r.zuege.push(u);
  }
  out.push(r);
}
lauf(Partie.START, ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"], 20);
lauf(Partie.START, ["e2e4", "d7d5", "e4e5", "f7f5", "e5f6", "e7f6", "d1h5", "g7g6"], 20);
for (let k = 0; k < n; k++) lauf(starts[k % starts.length], null, 260);
process.stdout.write(JSON.stringify(out));
"""
STARTS = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
          "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
          "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
          "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
          "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
          "4k3/8/8/8/8/8/8/4K2R w K - 90 80", "8/8/4k3/8/8/2B5/4K3/8 w - - 0 1", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
          "8/8/8/3k4/8/8/2KBB3/8 w - - 0 1", "4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1"]


def regeln_pruefen(ns, partien):
    print("1. Regeln auf dem Pi (639zzr) gegen chess.js + partie.js", flush=True)
    t0 = time.time()
    perft = [(STARTS[0], 3, 8902), (STARTS[1], 2, 2039), (STARTS[2], 3, 2812), (STARTS[3], 2, 264), (STARTS[4], 2, 1486)]
    for fen, d, soll in perft:
        n = ns["sf_perft"](ns["sf_fen_lesen"](fen), d)
        ok(n == soll, f"Perft {fen.split()[0][:20]}… Tiefe {d}: {n} (soll {soll})")
    node = shutil.which("node")
    if not node:
        ok(False, "Node fehlt (für den Vergleich mit chess.js)"); return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(NODE_SKRIPT)
    r = subprocess.run([node, f.name, SCHACH, json.dumps(STARTS), str(partien)], capture_output=True, text=True, timeout=300)
    os.unlink(f.name)
    if not ok(r.returncode == 0, "Node: zufällige Partien mit chess.js" + ("" if r.returncode == 0 else ": " + r.stderr[-400:])):
        return
    games = json.loads(r.stdout)
    halb, enden, falsch = 0, {}, []
    for gi, g in enumerate(games):
        p = ns["sf_fen_lesen"](g["start"]); keys = {ns["sf_schluessel"](p): 1}
        for i, st in enumerate(g["schritte"]):
            leg = ns["sf_legal"](p)
            e = ns["sf_ende_regeln"](p, keys, leg)
            mine = sorted(ns["sf_uci"](m) for m in leg) if not e else []
            fa, fb = ns["sf_fen"](p).split(), st["fen"].split()
            if mine != st["leg"] or e != st["ende"] or fa[:3] != fb[:3] or fa[4:] != fb[4:]:
                falsch.append(f"Partie {gi} Halbzug {i}: {ns['sf_fen'](p)} / {st['fen']} – Pi {len(mine)} Züge {e}, chess.js {len(st['leg'])} {st['ende']}")
                break
            if e:
                enden[e["art"]] = enden.get(e["art"], 0) + 1; break
            if i < len(g["zuege"]):
                m = next(m for m in leg if ns["sf_uci"](m) == g["zuege"][i])
                p = ns["sf_ziehe"](p, m); k = ns["sf_schluessel"](p); keys[k] = keys.get(k, 0) + 1; halb += 1
    ok(not falsch, f"{len(games)} Partien, {halb} Halbzüge: erlaubte Züge, Stellung und Ende gleich wie chess.js (Enden {enden})"
       + ("" if not falsch else ": " + "; ".join(falsch[:3])))
    ok(all(enden.get(k) for k in ("matt", "wiederholung", "material", "patt", "50zuege")), f"alle Arten Spielende kamen vor ({sorted(enden)})")
    print(f"   ({time.time() - t0:.1f} s)", flush=True)


# ---- 2. relay ----------------------------------------------------------------------------------------------------------------------
def svg_text(svg):
    """den QR-Code der SVG (Pfad aus Einheits-Quadraten) wirklich lesen"""
    import cv2
    import numpy as np
    n = int(re.search(r'viewBox="0 0 (\d+) ', svg).group(1))
    a = np.full((n, n), 255, np.uint8)
    for x, y in re.findall(r"M(\d+),(\d+)h1v1h-1z", svg):
        a[int(y), int(x)] = 0
    a = cv2.resize(a, (n * 8, n * 8), interpolation=cv2.INTER_NEAREST)
    t, _pts, _q = cv2.QRCodeDetector().detectAndDecode(a)
    return t


def vermittlung_pruefen(ns, home):
    print("2. Vermittlung (Flask-Testclient und echter Spiele-Port)", flush=True)
    CFG, SF, G_ = ns["CFG"], ns["SF"], ns["SF_GRENZEN"]
    CFG.update(https_extra=False, lang="de")
    PW = "Fern-Admin-" + base64.b16encode(os.urandom(4)).decode().lower()
    assert ns["web_pw_set"](PW)[0]
    for name, role, perms in (("Kim", "kid", None), ("Cus", "custom", [])):
        d = {"action": "add", "name": name, "password": name.lower() + "-pass-1", "role": role}
        if perms is not None:
            d["perms"] = perms
        okk, err = ns["users_action"](d)
        assert okk, err
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    c = ws.app.test_client(use_cookies=False)
    auth = lambda u, p: {"Authorization": "Basic " + base64.b64encode(f"{u}:{p}".encode()).decode()}
    H, HK, HC = auth("admin", PW), auth("Kim", "kim-pass-1"), auth("Cus", "cus-pass-1")
    LAN, TS = "192.168.1.20", "100.101.102.103"
    G_["posts"] = (200, 10.0)                        # the brake per seat is tested on its own below

    def api(op, d=None, args=None, pre="/schachfern", h=None, ip=LAN):
        h = H if h is None else h
        if d is not None:
            r = c.post(pre + "/" + op, json=d, headers=h, environ_base={"REMOTE_ADDR": ip})
        else:
            r = c.get(pre + "/" + op, query_string=args or {}, headers=h, environ_base={"REMOTE_ADDR": ip})
        return r.status_code, (r.get_json(silent=True) or {}), r

    # create, join, spectator
    st, A, _r = api("neu", {"farbe": "w"})
    ok(st == 200 and A.get("sitz") == "w" and re.fullmatch("[%s]{4}" % ns["SF_ABC"], A.get("code", "")) and len(A.get("token", "")) >= 20,
       f"erstellen: Code {A.get('code')} (4 gut lesbare Zeichen), Sitz Weiss, Schlüssel")
    code, ta = A["code"], A["token"]
    ok(A["status"] == "warte" and not A["sitze"]["b"]["da"], "vor dem Beitreten: «warte auf Gegner»")
    st, j, _r = api("zug", {"code": code, "token": ta, "uci": "e2e4", "n": 0})
    ok(st == 409 and j.get("fehler") == "warte", f"ziehen ohne Gegner abgelehnt ({st} {j.get('fehler')})")
    st, B, _r = api("beitreten", {"code": code.lower()}, h=HK)
    ok(st == 200 and B.get("sitz") == "b" and B.get("token") and B["status"] == "laeuft", "beitreten (Code klein geschrieben): Schwarz, Spiel läuft")
    tb = B["token"]
    st, Z, _r = api("beitreten", {"code": code})
    ok(st == 200 and Z.get("sitz") == "zuschauer" and not Z.get("token"), "dritter mit dem Code: Zuschauer ohne Schlüssel")
    st, j, _r = api("zug", {"code": code, "token": "", "uci": "e2e4", "n": 0})
    ok(st == 403, f"Zuschauer darf nicht ziehen ({st})")
    st, j, _r = api("beitreten", {"code": code, "token": ta})
    ok(st == 200 and j.get("sitz") == "w" and j.get("token") == ta, "beitreten mit eigenem Schlüssel: wieder der eigene Platz")
    # moves
    st, j, _r = api("zug", {"code": code, "token": tb, "uci": "e7e5", "n": 0})
    ok(st == 409 and j.get("fehler") == "nicht_dran" and j["v"]["zuege"] == [], f"Zug ausser der Reihe abgelehnt ({j.get('fehler')})")
    st, j, _r = api("zug", {"code": code, "token": ta, "uci": "e2e5", "n": 0})
    ok(st == 409 and j.get("fehler") == "illegal", f"unerlaubter Zug e2e5 abgelehnt ({j.get('fehler')})")
    st, j, _r = api("zug", {"code": code, "token": ta + "x", "uci": "e2e4", "n": 0})
    ok(st == 403 and j.get("fehler") == "token", f"falscher Schlüssel abgelehnt ({st})")
    for bad in ({"uci": "e2e4' or 1", "n": 0}, {"uci": "e2e4", "n": "x"}, {"uci": ["e2e4"], "n": 0}, {"uci": "e2e4", "n": 3}):
        st, j, _r = api("zug", dict(bad, code=code, token=ta))
        ok(st in (400, 409) and j["v"]["zuege"] == [], f"kaputte Daten {bad} abgelehnt ({st} {j.get('fehler')})")
    st, j, _r = api("zug", {"code": code, "token": ta, "uci": "f2f3", "n": 0})
    ok(st == 200 and j["zuege"] == ["f2f3"] and j["amZug"] == "b", "Weiss zieht f2-f3")
    st, j, _r = api("zug", {"code": code, "token": ta, "uci": "f2f3", "n": 0})
    ok(st == 200 and j["zuege"] == ["f2f3"], "derselbe Zug nochmals (Antwort unterwegs verloren): harmlos, nicht doppelt")
    st, j, _r = api("zug", {"code": code, "token": ta, "uci": "g2g4", "n": 1})
    ok(st == 409 and j.get("fehler") == "nicht_dran", "zweimal hintereinander Weiss: abgelehnt")
    # long polling
    G_["warten"] = 2.0
    st, j, _r = api("zustand", args={"code": code, "token": tb})
    seq, res = j["seq"], {}

    def warte():
        t0 = time.time(); res["r"] = api("zustand", args={"code": code, "token": tb, "seq": seq, "warte": 1}); res["t"] = time.time() - t0
    th = threading.Thread(target=warte); th.start(); time.sleep(0.5)
    api("zug", {"code": code, "token": tb, "uci": "e7e5", "n": 1}, h=HK)
    th.join(5)
    ok(res.get("r") and res["r"][1].get("zuege") == ["f2f3", "e7e5"] and res["t"] < 1.6, f"Long Polling: der Zug kommt sofort beim Wartenden an ({res.get('t', 0):.2f} s)")
    t0 = time.time(); st, j, _r = api("zustand", args={"code": code, "token": tb, "seq": res["r"][1]["seq"], "warte": 1})
    ok(st == 200 and 1.6 < time.time() - t0 < 4, f"ohne Änderung wartet die Abfrage ({time.time() - t0:.1f} s, auf dem Pi 15 s)")
    # reconnect after a reload (both sides): only code + token
    for wer, tok, sitz in (("Weiss", ta, "w"), ("Schwarz", tb, "b")):
        st, j, _r = api("zustand", args={"code": code, "token": tok})
        ok(st == 200 and j["sitz"] == sitz and j["zuege"] == ["f2f3", "e7e5"] and j["sitze"]["w"]["online"] and "token" not in json.dumps(j).replace('"token"', ""),
           f"Wiederaufnahme {wer} nach dem Neuladen: Platz und Züge, kein Schlüssel in der Antwort")
    # hints note, requests
    api("aktion", {"code": code, "token": ta, "art": "hilfe", "lern": True, "balken": False})
    api("aktion", {"code": code, "token": ta, "art": "hilfe", "tipp": True})
    st, j, _r = api("zustand", args={"code": code, "token": tb})
    ok(j["hilfe"]["w"] == {"lern": True, "balken": False, "tipps": 1}, f"«Tipps sind an»: der Gegner sieht Lern-Modus und 1 Tipp ({j['hilfe']['w']})")
    st, j, _r = api("aktion", {"code": code, "token": tb, "art": "zurueck"})
    ok(st == 200 and j["anfrage"] == {"art": "zurueck", "von": "b", "nr": 2}, "Schwarz fragt «Zug zurück»")
    st, j, _r = api("aktion", {"code": code, "token": tb, "art": "annehmen"})
    ok(st == 409, "die eigene Frage selbst annehmen geht nicht")
    st, j, _r = api("aktion", {"code": code, "token": ta, "art": "annehmen"})
    ok(st == 200 and j["zuege"] == ["f2f3"] and j["amZug"] == "b" and not j["anfrage"], "Weiss nimmt an: e7-e5 ist zurück, Schwarz wieder am Zug")
    api("zug", {"code": code, "token": tb, "uci": "e7e5", "n": 1})
    st, j, _r = api("aktion", {"code": code, "token": ta, "art": "remis"})
    st, j, _r = api("aktion", {"code": code, "token": tb, "art": "ablehnen"})
    ok(st == 200 and not j["anfrage"] and not j["ende"], "Remis angeboten und abgelehnt")
    st, j, _r = api("zug", {"code": code, "token": ta, "uci": "g2g4", "n": 2})
    st, j, _r = api("zug", {"code": code, "token": tb, "uci": "d8h4", "n": 3})
    ok(st == 200 and j["ende"] == {"art": "matt", "sieger": "b"} and j["status"] == "ende", "Narrenmatt: der Pi erkennt Matt, Schwarz gewinnt")
    st, j, _r = api("zug", {"code": code, "token": ta, "uci": "e1f2", "n": 4})
    ok(st == 409 and j.get("fehler") == "ende", "nach dem Matt kein Zug mehr")
    st, j, _r = api("aktion", {"code": code, "token": ta, "art": "revanche"})
    st, j, _r = api("aktion", {"code": code, "token": tb, "art": "revanche"})
    ok(st == 200 and j["nr"] == 2 and j["sitz"] == "w" and j["zuege"] == [] and not j["ende"] and j["hilfe"]["b"].get("lern") and not j["hilfe"]["b"].get("tipps"),
       f"Revanche (beide wollen): Partie 2, Farben getauscht (der Schwarze von vorher ist jetzt Weiss) ({st} {j.get('nr')} {j.get('sitz')} {j.get('hilfe')} {j.get('fehler')})")
    st, j, _r = api("zustand", args={"code": code, "token": ta})
    ok(j["sitz"] == "b", "der Weisse von vorher spielt jetzt Schwarz (gleicher Schlüssel)")
    st, j, _r = api("aktion", {"code": code, "token": tb, "art": "remis"})
    st, j, _r = api("aktion", {"code": code, "token": ta, "art": "annehmen"})
    ok(j["ende"] == {"art": "einigung", "sieger": None}, "Remis angeboten und angenommen: unentschieden")
    st, j, _r = api("aktion", {"code": code, "token": ta, "art": "revanche"})
    st, j, _r = api("aktion", {"code": code, "token": tb, "art": "annehmen"})
    st, j, _r = api("aktion", {"code": code, "token": tb, "art": "aufgeben"})
    ok(j["ende"] == {"art": "aufgabe", "sieger": "w"} and j["nr"] == 3, "Revanche angenommen, dann aufgegeben")
    # persistence: no token in the file, the game survives a restart
    raw = open(os.path.join(home, "schach_fern.json"), encoding="utf-8").read()
    ok(ta not in raw and tb not in raw and code in raw, "Datei auf dem Pi: Spiel ja, Schlüssel nur als Prüfsumme")
    with SF["cond"]:
        SF["spiele"].clear(); SF["geladen"] = False
    st, j, _r = api("zustand", args={"code": code, "token": ta})
    ok(st == 200 and j["nr"] == 3 and j["sitz"] == "w", "nach einem Neustart von MoveEye: Spiel und Plätze sind wieder da")
    # QR: address + code only
    for u in ("http://192.168.1.56:5003/g/schach/", "https://pi.tail1234.ts.net/games/schach/", "http://pi:5001/p/AbC_123-x/g/schach/index.html"):
        st, _j, r = api("qr", args={"code": code, "u": u})
        t = svg_text(r.get_data(as_text=True)) if st == 200 else ""
        ok(st == 200 and r.mimetype == "image/svg+xml" and t == u + "?fern=" + code and ta not in t and tb not in t and PW not in t,
           f"QR-Code gelesen: «{t}» = Adresse + Code, kein Schlüssel")
    for u in ("http://pi/g/schach/?token=" + ta, "http://evil.example/settings", "javascript:alert(1)", "http://user:pw@pi/g/schach/", "http://pi/g/schach/#x"):
        st, _j, _r = api("qr", args={"code": code, "u": u})
        ok(st == 400, f"QR mit fremder Adresse abgelehnt: {u[:40]} ({st})")
    # waiting game: cancel
    st, W, _r = api("neu", {"farbe": "zufall"})
    ok(W.get("sitz") in ("w", "b"), f"Farbe Zufall: {W.get('sitz')}")
    st, j, _r = api("aktion", {"code": W["code"], "token": W["token"], "art": "abbrechen"})
    st2, _j, _r = api("zustand", args={"code": W["code"]})
    ok(st == 200 and j.get("weg") and st2 == 404, "Spiel ohne Gegner löschen")
    # cleanup after 24 h / 30 min after the end
    st, X, _r = api("neu", {"farbe": "w"})
    with SF["cond"]:
        SF["spiele"][X["code"]]["t"] -= 24 * 3600 + 5
    st, j, _r = api("zustand", args={"code": X["code"], "token": X["token"]})
    ok(st == 404 and j.get("fehler") == "weg", "24 h ohne Aktivität: das Spiel ist weg")
    with SF["cond"]:
        SF["spiele"][code]["t_ende"] -= 1801
    st, j, _r = api("zustand", args={"code": code, "token": ta})
    ok(st == 404, "30 Minuten nach dem Ende: das Spiel ist weg")
    # at most 10 games; the oldest idle one goes
    with SF["cond"]:
        SF["spiele"].clear(); SF["ip"].clear()
    codes = []
    for i in range(10):
        st, j, _r = api("neu", {"farbe": "w"}, ip=f"192.168.2.{i + 1}")
        codes.append(j.get("code"))
    st, j, _r = api("neu", {"farbe": "w"}, ip="192.168.3.1")
    ok(st == 429 and j.get("fehler") == "voll", f"11. Spiel, alle 10 aktiv: abgelehnt ({st} {j.get('fehler')})")
    with SF["cond"]:
        SF["spiele"][codes[3]]["t"] -= 700
    st, j, _r = api("neu", {"farbe": "w"}, ip="192.168.3.1")
    ok(st == 200 and codes[3] not in SF["spiele"] and len(SF["spiele"]) == 10, "11. Spiel: das am längsten ruhende (über 10 min) macht Platz")
    # rate limits
    with SF["cond"]:
        SF["spiele"].clear(); SF["ip"].clear()
    G_["posts"] = (12, 10.0)
    st, R1, _r = api("neu", {"farbe": "w"})
    st, R2, _r = api("beitreten", {"code": R1["code"]})
    sts = [api("aktion", {"code": R1["code"], "token": R1["token"], "art": "hilfe", "lern": bool(i % 2)})[0] for i in range(14)]
    ok(sts[:12] == [200] * 12 and sts[12] == 429, f"Bremse pro Platz: 12 Anfragen in 10 s, dann 429 ({sts[10:]})")
    st, j, _r = api("aktion", {"code": R1["code"], "token": R2["token"], "art": "hilfe", "lern": True})
    ok(st == 200, "der andere Platz ist nicht gebremst")
    sts = [api("zustand", args={"code": "QQQQ"}, ip="192.168.4.4")[0] for _ in range(16)]
    ok(sts[:15] == [404] * 15 and sts[15] == 429, f"Codes raten: nach 15 falschen in 5 min 429 ({sts[13:]})")
    ok(api("zustand", args={"code": R1["code"]}, ip="192.168.4.4")[0] == 429, "… auch der richtige Code ist dann für diese Adresse gebremst")
    sts = [api("neu", {"farbe": "w"}, ip="192.168.5.5")[0] for _ in range(9)]
    ok(sts[:8] == [200] * 8 and sts[8] == 429, f"neue Spiele: 8 pro Adresse in 10 min ({sts[6:]})")
    # rights and access
    with SF["cond"]:
        SF["spiele"].clear(); SF["ip"].clear()
    ok(api("info", h={})[0] == 401, "ohne Anmeldung: 401 (Hauptadresse)")
    ok(api("info", h=HK)[0] == 200 and api("neu", {"farbe": "w"}, h=HK)[0] == 200, "Kind (Recht «Spiele»): erstellen ja")
    ok(api("info", h=HC)[0] == 403 and api("neu", {"farbe": "w"}, h=HC)[0] == 403, "eigene Rechte ohne «Spiele»: 403")
    ok(api("info", pre="/spiele/schachfern", h={}, ip=LAN)[0] == 200, "/spiele/schachfern aus dem eigenen WLAN ohne Anmeldung (wie /spiele)")
    ok(api("info", pre="/spiele/schachfern", h={}, ip=TS)[0] == 404, "/spiele/schachfern über Tailscale: zu")
    ns["party_open"](1.0)
    key = ns["PARTY"]["key"]
    st, j, _r = api("neu", {"farbe": "b"}, pre=f"/p/{key}/schachfern", h={}, ip=TS)
    ok(st == 200 and j.get("sitz") == "b", "Gast über den Spieler-Link (Tailscale), «Spiele freigeben» an: erstellen ja")
    gcode, gtok = j.get("code"), j.get("token")
    st, j, _r = api("beitreten", {"code": gcode}, pre="/schachfern", h=HK)
    ok(st == 200 and j.get("sitz") == "w", "ein angemeldeter Benutzer tritt dem Spiel des Gastes bei (gleiche Spiele für alle Wege)")
    ok(api("info", pre="/p/falsch/schachfern", h={}, ip=TS)[0] == 404, "falscher Raum-Schlüssel: zu")
    ns["party_close"]()
    st, j, _r = api("zustand", args={"code": gcode, "token": gtok}, pre=f"/p/{key}/schachfern", h={}, ip=TS)
    ok(st == 404 and j.get("fehler") == "zu", "«Spiele freigeben» aus: der Gast kommt nicht mehr hinein")
    ok(api("neu", {"farbe": "w"}, pre=f"/p/{key}/schachfern", h={}, ip=TS)[0] == 404, "… und kann kein Spiel erstellen")
    r = c.post("/schachfern/neu", json={"farbe": "w"}, headers=dict(H, Origin="http://evil.example"), environ_base={"REMOTE_ADDR": LAN})
    ok(r.status_code == 403, f"Hauptadresse: fremde Seite (Origin) abgelehnt ({r.status_code})")
    ok(api("neu", None, h=H)[0] == 404 and api("zustand", {"code": "AAAA"})[0] == 404, "GET/POST vertauscht: 404")
    # games port (own origin): only /schachfern/, nothing else of MoveEye
    lan = lan_ip()
    if not lan:
        ns["lan_guest_ip"] = lambda ip, fwd="": not fwd
        lan = "127.0.0.1"
    wp = frei_port()
    CFG["web_port"] = wp - 2
    ns["GAMESRV"]["port"] = 0
    ns["games_server_start"]()
    gp = ns["GAMESRV"]["port"]
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def port(pfad, d=None, hdr=None):
        rq = urllib.request.Request(f"http://{lan}:{gp}{pfad}", data=json.dumps(d).encode() if d is not None else None,
                                    headers=dict({"Content-Type": "application/json"} if d is not None else {}, **(hdr or {})))
        try:
            with op.open(rq, timeout=30) as x:
                return x.status, x.read(), dict(x.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)
    st, b, hh = port("/schachfern/info")
    ok(st == 200 and json.loads(b).get("ok") and hh.get("Cache-Control") == "no-store", f"Spiele-Port {gp}: /schachfern/info")
    st, b, _h = port("/schachfern/neu", {"farbe": "w"}, {"Origin": f"http://{lan}:{gp}"})
    ok(st == 200 and json.loads(b).get("code"), "Spiele-Port: erstellen von der eigenen Seite")
    pc = json.loads(b)
    st, b, _h = port("/schachfern/zug", {"code": pc["code"], "token": pc["token"], "uci": "e2e4", "n": 0}, {"Origin": "http://evil.example"})
    ok(st == 403, f"Spiele-Port: POST einer fremden Seite abgelehnt ({st})")
    st, b, _h = port("/schachfern/neu", {"farbe": "w"}, {"X-Forwarded-For": "1.2.3.4"})
    ok(st == 403, f"Spiele-Port über einen Tunnel/Proxy: abgelehnt ({st})")
    st, b, _h = port("/schachfern/neu", None)
    ok(st == 404, "Spiele-Port: GET auf eine POST-Adresse 404")
    rq = urllib.request.Request(f"http://{lan}:{gp}/schachfern/neu", data=b"x" * 5000, headers={"Content-Type": "application/json"})
    try:
        st = op.open(rq, timeout=10).status
    except urllib.error.HTTPError as e:
        st = e.code
    ok(st == 413, f"Spiele-Port: grosser Inhalt abgelehnt ({st})")
    for pfad in ("/api/state", "/api/settings", "/api/party", "/schachfern/../api/state", "/p/x/schachfern/info", "/"):
        st, b, _h = port(pfad)
        ok(st == 404, f"Spiele-Port: {pfad} -> {st} (keine anderen MoveEye-Adressen)")
    rq = urllib.request.Request(f"http://{lan}:{gp}/api/party", data=b"{}", headers={"Content-Type": "application/json"})
    try:
        st = op.open(rq, timeout=10).status
    except urllib.error.HTTPError as e:
        st = e.code
    ok(st == 405, f"Spiele-Port: POST auf andere Adressen 405 ({st})")
    return PW


# ---- 3. browser: two iPhones against a real MoveEye ---------------------------------------------------------------------------------
def browser_pruefen(datei, bilder):
    print("3. Browser: zwei iPhone 13 gegen ein echtes MoveEye (--headless --demo)", flush=True)
    sys.path.insert(0, HIER)
    from rechte_schutz_test import Geraet, PASSWORT
    from playwright.sync_api import sync_playwright
    port = frei_port()
    g = Geraet(datei, port)
    gd = os.path.join(g.cfg, "games")
    shutil.copytree(SCHACH, os.path.join(gd, "schach"), ignore=shutil.ignore_patterns("kachel.json"))
    k = json.load(open(os.path.join(SCHACH, "kachel.json"), encoding="utf-8"))
    k.pop("lizenz", None)
    json.dump({"version": "test", "games": [k]}, open(os.path.join(gd, "games.json"), "w"))
    lan = lan_ip()
    g.start(demo=True)
    try:
        if bilder:
            os.makedirs(bilder, exist_ok=True)
        gp = port + 2
        url_a = f"http://{lan}:{gp}/g/schach/?test=1" if lan else f"http://127.0.0.1:{port}/games/schach/?test=1"
        url_b = f"http://127.0.0.1:{port}/games/schach/?test=1"
        print(f"   Handy A: {url_a}\n   Handy B: {url_b}", flush=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            dev = dict(pw.devices["iPhone 13"])
            fehl = []

            def kontext(anm):
                ctx = br.new_context(**dev, **({"http_credentials": {"username": "admin", "password": PASSWORT}} if anm else {}))
                return ctx

            def seite(ctx, url, name):
                pg = ctx.new_page()
                pg.on("pageerror", lambda e: fehl.append(f"{name}: JavaScript {str(e)[:200]}"))
                pg.on("console", lambda m: fehl.append(f"{name}: console.error {m.text[:160]}") if m.type == "error" and "ERR_FAILED" not in m.text and "Failed to load resource" not in m.text else None)
                pg.goto(url, wait_until="load", timeout=30000)
                pg.wait_for_function("() => window.__schach && document.querySelectorAll('#brett piece').length >= 32", timeout=15000)
                return pg

            def z(pg):
                return pg.evaluate("() => __schach.zustand()")

            def warte(pg, js, ms=20000):
                pg.wait_for_function(js, timeout=ms, polling=100)

            def tippe(pg, feld):
                p = pg.evaluate("f => __schach.feld(f)", feld)
                pg.touchscreen.tap(p["x"], p["y"]); pg.wait_for_timeout(150)

            def zug(pg, a, b):
                tippe(pg, a); tippe(pg, b)

            def bild(pa, pb, name):
                if not bilder:
                    return
                from PIL import Image
                (pa or pb).wait_for_timeout(450)                       # the windows slide in (0.22 s)
                fa, fb = os.path.join(bilder, f"_{name}_a.png"), os.path.join(bilder, f"_{name}_b.png")
                (pa.screenshot(path=fa) if pa else None); (pb.screenshot(path=fb) if pb else None)
                ims = [Image.open(f) for f in (fa, fb) if os.path.isfile(f) and ((f == fa and pa) or (f == fb and pb))]
                w = sum(i.width for i in ims) + 24 * (len(ims) - 1)
                out = Image.new("RGB", (w, max(i.height for i in ims)), (40, 44, 52)); x = 0
                for i in ims:
                    out.paste(i, (x, 0)); x += i.width + 24
                out.save(os.path.join(bilder, f"{name}.png"))
                for f in (fa, fb):
                    if os.path.isfile(f):
                        os.remove(f)

            ca, cb = kontext(False), kontext(True)
            pa = seite(ca, url_a, "A")
            ok(pa.locator("#dNeu").is_visible(), "A: «Neues Spiel» beim ersten Start")
            pa.locator("#segGegner button[data-w=fern]").tap()
            ok(pa.locator("#nurFern").is_visible() and pa.locator("#bFernNeu").is_visible() and pa.locator("#fernCodeEin").is_visible() and not pa.locator("#bSpielen").is_visible(),
               "A: «Zwei Handys»: «Neues Spiel erstellen» und Code-Feld, kein «Spielen»")
            klein = pa.evaluate("""() => [...document.querySelectorAll('#dNeu button, #dNeu input')].filter(e => { const r = e.getBoundingClientRect();
                return r.width > 0 && (r.width < 43.9 || r.height < 43.9); }).map(e => e.id || e.textContent.trim().slice(0, 14))""")
            ok(not klein, f"A: alle Knöpfe und das Feld mindestens 44 px ({klein})")
            pa.locator("#segFarbe button[data-w=w]").tap()
            pb = seite(cb, url_b, "B")
            pb.locator("#segGegner button[data-w=fern]").tap()
            bild(pa, pb, "01_start_zwei_handys")
            pa.locator("#bFernNeu").tap()
            warte(pa, "() => !document.getElementById('dFernWarte').hidden && document.getElementById('fernQr').complete && document.getElementById('fernQr').naturalWidth > 0")
            code = pa.inner_text("#fernCode").strip()
            ok(re.fullmatch("[ACDEFHJKMNPQRTUVWXY3479]{4}", code) is not None, f"A: Code gross angezeigt: {code}, QR-Code geladen")
            lk = pa.inner_text("#fernLink")
            ok(lk.endswith("/g/schach/?fern=" + code) or lk.endswith("/games/schach/?fern=" + code), f"A: Link = Seite + Code ({lk})")
            ok("token" not in pa.get_attribute("#fernQr", "src").split("?")[1].replace("code=", "") , "A: die QR-Adresse nennt keinen Schlüssel")
            pb.locator("#fernCodeEin").fill(code.lower())
            bild(pa, pb, "02_erstellt_und_beitreten")
            pb.locator("#bFernBei").tap()
            warte(pb, "() => { const f = __schach.zustand().fern; return f && f.sitz === 'b' && f.status === 'laeuft'; }")
            warte(pa, "() => { const f = __schach.zustand().fern; return f && f.status === 'laeuft' && document.getElementById('dFernWarte').hidden; }")
            ok(True, "B tritt mit dem Code bei (Schwarz), bei A schliesst sich das Warte-Fenster von selbst")
            ok("Du bist Weiss" in pa.inner_text("#fern") and "verbunden" in pa.inner_text("#fern") and "Du bist Schwarz" in pb.inner_text("#fern"),
               f"Status: «{pa.inner_text('#fern')}» / «{pb.inner_text('#fern')}»")
            ok(z(pb)["drehung"] == "b" and z(pa)["drehung"] == "w", "jeder sieht seine Farbe unten")
            ok("Du bist am Zug" in pa.inner_text("#status") or "beginnt" in pa.inner_text("#status") or "am Zug" in pa.inner_text("#status"), f"A Status: {pa.inner_text('#status')}")
            tippe(pb, "e7")
            ok(pb.locator("#brett square.move-dest").count() == 0, "B (nicht dran) kann keine Figur ziehen")
            zug(pa, "f2", "f3")
            warte(pb, "() => __schach.zustand().zugNr === 1")
            ok(z(pb)["toene"].get("zug", 0) >= 1, "B hört den Zug des Gegners (Ton)")
            bild(pa, pb, "03_im_spiel")
            zug(pb, "e7", "e5")
            warte(pa, "() => __schach.zustand().zugNr === 2")
            # connection lost and back (A)
            ca.route("**/schachfern/**", lambda r: r.abort())
            pa.evaluate("() => window.dispatchEvent(new Event('focus'))")
            warte(pa, "() => __schach.zustand().fern.verb === 'weg'", 10000)
            ok("Verbindung weg – versuche neu" in pa.inner_text("#fern"), f"A ohne Netz: «{pa.inner_text('#fern')}»")
            zug(pa, "g2", "g4")
            ok(z(pa)["fern"]["ausstehend"] is not None, "A zieht ohne Netz: der Zug wartet")
            bild(pa, pb, "04_verbindung_weg")
            ca.unroute("**/schachfern/**")
            warte(pa, "() => __schach.zustand().fern.verb === 'ok' && !__schach.zustand().fern.ausstehend", 15000)
            warte(pb, "() => __schach.zustand().zugNr === 3", 20000)
            ok(True, "Netz wieder da: der wartende Zug kommt an, Status «verbunden»")
            # both phones sleep: pages closed and opened again
            pb.close(); pa.close()
            time.sleep(1.0)
            pa = seite(ca, url_a.replace("?test=1", "?test=1&x=1"), "A")
            warte(pa, "() => { const f = __schach.zustand().fern; return f && f.status === 'laeuft' && __schach.zustand().zugNr === 3; }")
            ok(z(pa)["fern"]["sitz"] == "w" and pa.locator("#dNeu").is_hidden(), "A wieder offen (Handy aufgewacht): gleiches Spiel, Weiss, 3 Züge")
            pb = seite(cb, url_b, "B")
            warte(pb, "() => { const f = __schach.zustand().fern; return f && f.sitz === 'b' && __schach.zustand().zugNr === 3; }")
            ok(True, "B wieder offen: gleiches Spiel, Schwarz, am Zug")
            bild(pa, pb, "05_wieder_offen")
            zug(pb, "d8", "h4")
            warte(pa, "() => !!__schach.zustand().ende")
            warte(pb, "() => !!__schach.zustand().ende")
            pa.wait_for_timeout(900)
            ok(z(pa)["ende"] == {"art": "matt", "sieger": "b"} and "dein Gegner gewinnt" in pa.inner_text("#endeTitel") and "du hast gewonnen" in pb.inner_text("#endeTitel"),
               f"Narrenmatt: A «{pa.inner_text('#endeTitel')}», B «{pb.inner_text('#endeTitel')}»")
            ok(pb.inner_text("#bEndeNeu").strip() == "Revanche", "Ende-Fenster mit «Revanche»")
            bild(pa, pb, "06_matt")
            # rematch with swapped colours
            pb.locator("#bEndeNeu").tap()
            warte(pa, "() => !document.getElementById('dAnfrage').hidden")
            ok("Revanche" in pa.inner_text("#anfrageTitel") and "Schwarz" in pa.inner_text("#anfrageText"), f"A wird gefragt: {pa.inner_text('#anfrageText')}")
            bild(pa, pb, "07_revanche_frage")
            pa.locator("#bAnfrageJa").tap()
            warte(pa, "() => __schach.zustand().fern.nr === 2 && __schach.zustand().fern.sitz === 'b'")
            warte(pb, "() => __schach.zustand().fern.nr === 2 && __schach.zustand().fern.sitz === 'w'")
            ok(z(pa)["drehung"] == "b" and z(pb)["drehung"] == "w" and z(pa)["zugNr"] == 0, "Revanche: Farben getauscht, Brett gedreht, neue Partie")
            # hints note for both
            pa.locator("#bLern").tap()
            warte(pb, "() => /Tipps sind an: Gegner \\(Lern-Modus\\)/.test(__schach.zustand().fern.hilfeZeile)")
            ok("Tipps sind an: du (Lern-Modus)" in z(pa)["fern"]["hilfeZeile"], f"«Tipps sind an» bei beiden: B «{z(pb)['fern']['hilfeZeile']}»")
            # spectator
            cc = br.new_context(**dev)
            pc = seite(cc, url_a.replace("?test=1", "?test=1&z=1"), "Zuschauer")
            pc.locator("#segGegner button[data-w=fern]").tap()
            pc.locator("#fernCodeEin").fill(code); pc.locator("#bFernBei").tap()
            warte(pc, "() => { const f = __schach.zustand().fern; return f && f.sitz === 'zuschauer'; }")
            zug(pb, "e2", "e4")
            warte(pc, "() => __schach.zustand().zugNr === 1")
            ok("Du schaust zu" in pc.inner_text("#fern") and pc.locator("#bAufgeben").is_disabled(), "dritter mit dem Code: schaut zu (Züge kommen an, keine Knöpfe)")
            # draw offer declined
            warte(pa, "() => __schach.zustand().zugNr === 1 && __schach.zustand().menschDran")
            pa.locator("#bDrehen").tap()
            warte(pb, "() => !document.getElementById('dAnfrage').hidden")
            ok("Remis" in pb.inner_text("#anfrageTitel") and "Remis angeboten" in z(pa)["fern"]["hilfeZeile"], "Remis anbieten: der Gegner wird gefragt, beim Anbieter «warte auf Antwort»")
            bild(pa, pb, "08_remis_frage")
            pb.locator("#bAnfrageNein").tap()
            warte(pa, "() => !__schach.zustand().fern.anfrage")
            ok(not z(pa)["ende"], "Remis abgelehnt: es geht weiter")
            cc.close()
            ok(not fehl, "keine JavaScript-Fehler" + ("" if not fehl else ": " + "; ".join(fehl[:4])))
            ca.close(); cb.close(); br.close()
    finally:
        g.stop()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datei", default="")
    ap.add_argument("--ohne-browser", action="store_true")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--partien", type=int, default=60)
    a = ap.parse_args()
    datei = a.datei or neueste()
    print("Datei:", os.path.basename(datei), flush=True)
    home = tempfile.mkdtemp(prefix="mw_schachfern_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_schachfern_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *x, **k: None
    ok(ns["sf_selftest"]().startswith("chess"), "Selbsttest 639zzr")
    regeln_pruefen(ns, a.partien)
    vermittlung_pruefen(ns, home)
    if not a.ohne_browser:
        browser_pruefen(datei, a.bilder)
    shutil.rmtree(home, ignore_errors=True)
    for f in FEHLER:
        print("FEHLER:", f)
    print("Schach-zwei-Handys-Test:", "OK" if not FEHLER else f"{len(FEHLER)} Fehler")
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
