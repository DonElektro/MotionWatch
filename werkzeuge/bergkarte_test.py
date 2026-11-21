#!/usr/bin/env python3
"""MoveEye: Test der Bergtal-Karte (Teil 639zzzzzt, werkzeuge/bergkarte/paket.py).

  python3 werkzeuge/bergkarte_test.py [--web karte-web-2.zip] [--export EXP] [--bilder ORDNER] [--ohne-browser] [--datei X.py]

Ohne --export: ein kleines erfundenes Tal (Gitter wie das Bergtal, 513 × 513 à 4 m, ein paar Orte, Wege, Seen und geheime
Orte) - der Test braucht so kein Godot. Mit --export: die echte Ausgabe von werkzeuge/bergkarte/export.gd (Bildschirmfotos).
Das Web-Paket (MapLibre + Schriften) ist karte-web-2.zip des Releases karten-2, geprüft gegen die Prüfsumme in Teil 639zzq.

A) im Prozess
   * Paket: paket.py baut, --pruefen sagt «Paket = Eingabe» (Orte, Höhen der Kacheln an den Stichproben, nichts Geheimes in
     vektor.json), gleiche Eingabe = gleiche Bytes.
   * Laden: nur der Admin, veränderte Datei abgelehnt (kein halber Ordner), dann installiert; Dateien des Pakets nur über die
     Liste (geheim.json / hoehen.f32 / ../ -> 404), Schlüssel in der Adresse.
   * Schalter: /karte hat den Schalter «Schweiz / Bergtal» und den Haken in der Seite genau einmal.
   * GEHEIME ORTE: ohne Simulator keiner; mit gemeldeten Kennungen genau die passenden (Ort, Pfad, See, Kapitel-Ziel); alt
     (> 15 s) oder Simulation aus = wieder keiner; nie in der Ortssuche.
   * TOUREN-PROFIL: /api/touren/profil im Bergtal rechnet mit den Höhen des Pakets (gegen eine eigene Rechnung im Gitter),
     gespeicherte Tour = «welt» berg mit Auf- / Abstieg, Vorschläge (Hospiz → Pass → Biwak) mit Zahlen und Profil, eine
     Schweizer Tour bleibt unberührt; «Tour im Sim nachlaufen» schickt Tal-Meter an den Simulator (ersetzte sim_control),
     ein alter Simulator gibt «braucht eine neuere Version».
   * Live: Lage, Blick, Figur, Erkanntes werden zu Punkten der Karte.
B) im Browser (MoveEye als eigener Prozess, 390 px DPR 2 und PC): /karte ohne Schweizer Karte geht ins Bergtal, Schalter
   wechselt hin und zurück (gemerkt), Karte mit WebGL, 2D / 3D, Vorschläge mit Profil, Route zeichnen mit Profil, keine
   geheimen Orte ohne Simulator, keine Anfrage nach aussen, keine Fehler, nichts ragt seitlich hinaus.
"""
import argparse
import base64
import glob
import hashlib
import json
import math
import os
import re
import shutil
import socket
import sys
import tempfile
import time
import urllib.request
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "bergkarte"))
import paket as BP                                      # noqa: E402  (werkzeuge/bergkarte/paket.py)
FEHLER = []
WEB_URL = "https://github.com/DonElektro/MotionWatch/releases/download/karten-2/karte-web-2.zip"
GEHEIM_NAMEN = ("Kristallhöhle hinter dem Wasserfall", "Geheimer Bergsee hinter dem Grat", "Kapitel 1 - Der Brief", "Pfad zum geheimen See")


def ok(c, what):
    print(("  ✓ " if c else "  ✗ ") + what, flush=True)
    if not c:
        FEHLER.append(what)
    return c


def neueste_datei():
    c = sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    return c[-1]


def web_zip(path, tmp):
    """karte-web-N.zip (MapLibre + fonts): the given file or the release asset, checked against KQ_FILES of part 639zzq"""
    src = open(os.path.join(ROOT, "quelle", "639zzq_offline_karten.py"), encoding="utf-8").read()
    m = re.search(r'"web": \{"name": "([^"]+)", "size": (\d+), "sha256": "([0-9a-f]{64})"', src)
    if not path:
        path = os.path.join(tmp, m.group(1))
        req = urllib.request.Request(WEB_URL, headers={"User-Agent": "MoveEye-Test"})
        with urllib.request.urlopen(req, timeout=120) as r:
            open(path, "wb").write(r.read())
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if h != m.group(3):
        sys.exit("karte-web: Prüfsumme %s statt %s" % (h, m.group(3)))
    return path


# ---- a small made-up valley (same grid as the Bergtal) ----------------------------------------------------------------------------
def tal_hoehe(x, z):
    """valley from north (low) to the pass (south), ridges west and east"""
    return 120 + 0.45 * (z + 1024) + 0.0009 * x * x + 60 * math.sin(x / 140.0) * math.cos(z / 170.0)


def erfundenes_tal(aus):
    import array
    os.makedirs(aus, exist_ok=True)
    n, lo, st = 513, -1024.0, 4.0
    h = array.array("f", (tal_hoehe(lo + i * st, lo + j * st) for j in range(n) for i in range(n)))
    open(os.path.join(aus, "hoehen.f32"), "wb").write(h.tobytes())
    land = bytearray(n * n)
    for j in range(n):
        for i in range(n):
            x, z = lo + i * st, lo + j * st
            land[j * n + i] = 4 if x > 600 and z > 300 else 1 if -400 < z < -200 and abs(x) < 300 else 2 if abs(x) > 850 else 6 if math.hypot(x + 470, z + 265) < 80 else 0
    open(os.path.join(aus, "land.u8"), "wb").write(bytes(land))
    places = [{"name": "Alp Tschuggen", "x": 60.0, "z": 0.0, "kind": "huette"}, {"name": "Gumpisee", "x": -60.0, "z": -390.0, "kind": "see"},
              {"name": "Furggapass mit Hospiz", "x": 40.0, "z": 800.0, "kind": "hospiz"}, {"name": "Passchanzle Furgga", "x": -30.0, "z": 850.0, "kind": "aussicht", "vp": True},
              {"name": "Biwak Chüebodehorn", "x": -520.0, "z": 560.0, "kind": "biwak"}, {"name": "Tschingelspitz (Gipfel West)", "x": -790.0, "z": 520.0, "kind": "gipfel"},
              {"name": "Kapelle St. Jodern", "x": 210.0, "z": -700.0, "kind": "kapelle"}, {"name": "Bei der Alp Tschuggen", "x": 30.0, "z": 22.0, "kind": "schlafplatz", "spot": "huette"}]
    secrets = [{"id": "v.kristallhoehle", "name": GEHEIM_NAMEN[0], "x": 40.0, "z": -98.0, "kind": "geheim", "found": ["berg.kristallhoehle"]},
               {"id": "v.geheimer_see", "name": GEHEIM_NAMEN[1], "x": -880.0, "z": 420.0, "kind": "geheim", "found": ["berg.geheimer_see"]},
               {"id": "ab.1", "name": GEHEIM_NAMEN[2], "x": 38.0, "z": 18.0, "kind": "schatz", "found": ["abenteuer.kapitel.1"]}]
    trails = [{"name": "Passweg", "level": 1, "pts": [[60, 0], [110, 120], [90, 420], [60, 560], [30, 780], [40, 800]], "secret": []},
              {"name": "Höhenweg West", "level": 1, "pts": [[60, 0], [-90, 170], [-300, 300], [-450, 470], [-520, 548]], "secret": []},
              {"name": "Passchanzle", "level": 0, "pts": [[40, 800], [-30, 850]], "secret": []},
              {"name": "Seeweg", "level": 0, "pts": [[60, 0], [-60, -100], [-150, -230], [-60, -390], [210, -700]], "secret": []},
              {"name": GEHEIM_NAMEN[3], "level": 2, "pts": [[-620, 128], [-720, 290], [-860, 405]], "secret": ["berg.geheimer_see"]}]
    lakes = [{"c": [-60, -390], "a": 130.0, "b": 80.0, "rot": 0.25, "level": tal_hoehe(-60, -390) - 1, "secret": []},
             {"c": [-880, 420], "a": 30.0, "b": 20.0, "rot": 0.2, "level": tal_hoehe(-880, 420) - 1, "secret": ["berg.geheimer_see"]}]
    d = {"format": 1, "sim": "0.0.1-test", "grid": {"lo": lo, "step": st, "n": n, "alt0": 1500.0}, "places": places, "secrets": secrets,
         "trails": trails, "streams": [{"w": 2.0, "pts": [[600, 430], [200, 220], [48, -60], [-30, -310]]}], "lakes": lakes,
         "road": [[240, -1060], [205, -600], [172, -40], [175, 300], [60, 830]], "samples": [], "land_classes": []}
    json.dump(d, open(os.path.join(aus, "bergtal.json"), "w", encoding="utf-8"), ensure_ascii=False)
    g = BP.Gitter(aus)                                     # samples in the grid (like export.gd: Bt.H)
    d["samples"] = [[x, z, round(g.H(x, z), 3)] for x in range(-900, 901, 300) for z in range(-900, 901, 300)] + [[p["x"], p["z"], round(g.H(p["x"], p["z"]), 3)] for p in places]
    json.dump(d, open(os.path.join(aus, "bergtal.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return aus


def paket_bauen(exp, web, aus):
    zp = BP.bauen(exp, web, aus)
    BP.pins(aus)
    rep = BP.pruefen(aus, exp)
    data = open(zp, "rb").read()
    zp2 = BP.bauen(exp, web, aus + "_2")
    ok(open(zp2, "rb").read() == data, "Paket: gleiche Eingabe = gleiche Bytes")
    ok("PRUEFUNG OK" in rep, "Paket = Eingabe (paket.py --pruefen: Orte, Höhen der Kacheln an den Stichproben, nichts Geheimes offen)")
    with zipfile.ZipFile(zp) as z:
        unp = sum(i.file_size for i in z.infolist())
    return zp, data, unp


def lade(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_bergkarte_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    return ns


# ---- A) in the process ------------------------------------------------------------------------------------------------------------
def teil_a(datei, zp, data, unp, exp):
    from piper_test import Srv
    print("A) im Prozess", flush=True)
    home = tempfile.mkdtemp(prefix="mw_bk_a_")
    ns = lade(datei, home)
    logs = []
    ns["log_event"] = lambda *x, **k: logs.append(" ".join(str(v) for v in x))
    CFG, SIM = ns["CFG"], ns["SIM"]
    ok("bk_selftest" in ns and bool(ns["bk_selftest"]()), "Selbsttest 639zzzzzt")
    ok(ns["bk_installed"]() is False and ns["bk_pinned"]() == (ns["BK_FILE"]["size"] > 0), "ohne Paket: nicht installiert; gepinnt wie im Programm")
    srv = Srv()
    srv.files["/" + ns["BK_TAG"] + "/" + ns["BK_FILE"]["name"]] = data
    ns["BK_BASE"]["url"] = srv.url
    ns["BK_FILE"].update(size=len(data), sha256=hashlib.sha256(data).hexdigest(), unpacked=unp, sim="test")
    ns["BK_RT"]["ok_t"] = 0
    # web
    CFG.update(https_extra=False, lang="de", tausch_free_gb=0.02, tausch_on=True, sim_on=False)
    PW = "Admin-Berg-123"
    assert ns["web_pw_set"](PW)[0]
    for nm, pw, role in (("Anna", "anna-pass-1", "family"), ("Kim", "kim-pass-12", "kid")):
        okk, err = ns["users_action"]({"action": "add", "name": nm, "password": pw, "role": role}); assert okk, err
    ws = ns["WebStream"](None); ws._serve = lambda app, ctx: None; ws.start()
    c = ws.app.test_client(use_cookies=False)
    hd = lambda u, p: {"Authorization": "Basic " + base64.b64encode(f"{u}:{p}".encode()).decode()}
    H, HA, HK = hd("admin", PW), hd("Anna", "anna-pass-1"), hd("Kim", "kim-pass-12")
    jget = lambda u, h=H: (lambda r: (r.status_code, r.get_json(silent=True) or {}))(c.get(u, headers=h))
    jpost = lambda u, d, h=H: (lambda r: (r.status_code, r.get_json(silent=True) or {}))(c.post(u, json=d, headers=h))
    ok(jpost("/api/karte/berg", {"action": "install"}, HA)[0] == 403 and jpost("/api/karte/berg", {"action": "install"}, HK)[0] == 403, "laden: nur der Admin (Familie / Kind 403)")
    srv.tamper.add("/" + ns["BK_TAG"] + "/" + ns["BK_FILE"]["name"])
    okk, err = ns["bk_download"](wait=True)
    ok(not okk and "checksum" in err.lower() and not os.path.isdir(ns["bk_dir"]()) and not ns["bk_installed"](), f"veränderte Datei abgelehnt, kein halber Ordner ({err[:60]})")
    srv.tamper.clear()
    okk, err = ns["bk_download"](wait=True)
    ns["BK_RT"]["ok_t"] = 0
    ok(okk and ns["bk_installed"]() and not os.path.exists(os.path.join(ns["bk_dl_dir"](), ns["BK_FILE"]["name"])), "geladen, geprüft, ausgepackt, die ZIP wieder weg")
    key = ns["bk_key"]()
    code, st = jget("/api/karte/berg", HK)
    ok(code == 200 and st["on"] and not st["admin"] and st["meta"]["counts"]["orte"] >= 6, "Zustand für alle Angemeldeten (Kind sieht, ist nicht Admin)")
    f = lambda p, h=HK: c.get("/karte/berg/" + key + "/" + p, headers=h)
    ok(f("stil.json").status_code == 200 and f("vektor.json").status_code == 200 and f("dem/15/16383/16383.png").status_code in (200, 404), "Paket-Dateien über die Liste (Stil, Vektor)")
    ok(all(f(p).status_code == 404 for p in ("geheim.json", "hoehen.f32", "bergkarte.ok", "touren.json", "../bergkarte.ok", "web/../geheim.json")) and c.get("/karte/berg/000000000000/stil.json", headers=HK).status_code == 404,
       "geheim.json, Höhen, Marke, ../ und falscher Schlüssel: 404")
    pbf = f("web/fonts/Noto Sans Bold/0-255.pbf")
    ok(pbf.status_code == 200 and pbf.data == b"", "fehlende Schrift: leere Antwort (MapLibre lässt sie aus)")
    # ---- the switch on /karte
    pg = c.get("/karte", headers=HA).get_data(as_text=True)
    ok(pg.count("window.BK = ") == 1 and pg.count("BK.take()") == 1 and 'id="bk-vor"' in pg and '"on": true' in pg.split("window.BK = ", 1)[1][:400],
       "Schalter: /karte mit dem Bergtal-Skript, Haken genau einmal, Paket an")
    # ---- SECRETS
    vk = f("vektor.json").get_data(as_text=True)
    ok(not any(n in vk for n in GEHEIM_NAMEN), "geheime Namen nicht in vektor.json")
    ok(not any(n in pg for n in GEHEIM_NAMEN), "geheime Namen nicht in der Seite (Ortssuche)")
    live = lambda h=HK: jget("/api/karte/berg?live=1", h)[1]
    names = lambda j: sorted(x["properties"].get("name") or x["properties"]["t"] for x in (j.get("geheim") or {}).get("features", []))
    D = json.load(open(os.path.join(exp, "bergtal.json"), encoding="utf-8"))

    def erwartet(F):
        """the names the map may show for these found-ids: from the export itself (secret places, trails, lakes)"""
        out = [x["name"] for x in D["secrets"] if set(x["found"]) & F] + [t["name"] for t in D["trails"] if set(t["secret"]) & F]
        return sorted(out + ["geheim_see"] * sum(1 for l in D["lakes"] if set(l["secret"]) & F))
    j = live()
    ok(j["geheim"]["features"] == [] and not j["sim"] and j["secrets"] == len(D["secrets"]) and j["found"] == 0, "ohne Simulator: kein geheimer Ort (%d geheime im Paket)" % len(D["secrets"]))
    ns["simvals_take"]({"bkarte": {"v": 1, "found": ["berg.kristallhoehle"]}})
    ok(live()["geheim"]["features"] == [], "Meldung da, aber Simulation aus: kein geheimer Ort")
    CFG["sim_on"], SIM["ok"] = True, True
    F1 = {"berg.kristallhoehle"}
    ok(names(live()) == erwartet(F1) and len(erwartet(F1)) >= 1 and live()["found"] == len([x for x in D["secrets"] if set(x["found"]) & F1]),
       "Simulator meldet «berg.kristallhoehle»: genau die Kristallhöhle " + str(erwartet(F1)))
    F2 = {"berg.geheimer_see", "abenteuer.kapitel.1", "berg.unbekannt"}
    ns["simvals_take"]({"bkarte": {"v": 1, "found": sorted(F2)}})
    ok(names(live()) == erwartet(F2),
       "geheimer See: Ort + Pfad + See; Kapitel 1 erledigt: sein Ziel; unbekannte Kennung: nichts " + str(erwartet(F2)))
    ok("geheim_see" in erwartet(F2) and any(t["secret"] for t in D["trails"]), "der geheime See hat seinen See und seinen Pfad im Paket")
    SIM["bkarte"]["t"] = time.time() - 20
    ok(live()["geheim"]["features"] == [], "Meldung älter als 15 s: wieder alles verborgen")
    ns["simvals_take"]({"x": 1})
    ok(live()["geheim"]["features"] == [], "Simulator ohne «bkarte» (anderer Ort): verborgen")
    # ---- live
    ns["simvals_take"]({"bkarte": {"v": 1, "found": [], "me": [100.0, -200.0, 90.0, 66.0], "fig": [120, -210, 45], "seen": [["a", 130, -190], ["p", 140, -195], ["x", 1, 1]]}})
    lv = live()["live"]
    ok(lv["me"]["ll"] == ns["bk_ll"](100.0, -200.0) and lv["me"]["az"] == 90.0 and lv["fig"]["x"] == 120 and [s["w"] for s in lv["seen"]] == ["a", "p"],
       "live: MoveEye mit Blick, Figur, Tier und Person als Punkte (Tal-Meter -> Karte)")
    # ---- TOUR PROFILE
    g = BP.Gitter(exp)
    pts_xz = [(60.0, 0.0), (90.0, 420.0), (30.0, 780.0)]
    pts = [(ns["bk_ll"](x, z)[1], ns["bk_ll"](x, z)[0]) for x, z in pts_xz]
    code, pr = jpost("/api/touren/profil", {"pts": [list(p) for p in pts], "lang": "de"}, HA)
    eigen = []
    for (x0, z0), (x1, z1) in zip(pts_xz, pts_xz[1:]):
        L_ = math.hypot(x1 - x0, z1 - z0); k = int(L_ // 10.0)
        eigen += [g.alt0 + g.H(x0 + (x1 - x0) * i / (k + 1.0), z0 + (z1 - z0) * i / (k + 1.0)) for i in range(k + 1)]
    eigen.append(g.alt0 + g.H(*pts_xz[-1]))
    dm = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts_xz, pts_xz[1:]))
    ok(code == 200 and pr.get("ele") and not pr.get("need") and abs(pr["m"] - dm) < 1.0 and abs(pr["profile"][0][1] - round(eigen[0], 1)) < 5 and abs(pr["hi"] - max(eigen)) < 6 and abs(pr["lo"] - min(eigen)) < 6,   # drawn routes: mean over 30 m (KT_SMOOTH_DRAWN)
       f"Profil im Bergtal mit den Höhen des Pakets: {pr.get('m')} m ({dm:.0f}), {pr.get('lo')}–{pr.get('hi')} m (eigene Rechnung {min(eigen):.0f}–{max(eigen):.0f})")
    ok(pr.get("up", 0) > 100 and pr.get("min", 0) > 0, f"Auf- / Abstieg und Wanderzeit: ↑ {pr.get('up')} m ↓ {pr.get('down')} m, {pr.get('min')} min")
    code, sv = jpost("/api/touren", {"action": "save", "name": "Bergtal Probe", "pts": [list(p) for p in pts], "lang": "de"}, HA)
    code2, lst = jget("/api/touren", HA)
    row = [t for t in lst.get("tours", []) if t["id"] == sv.get("tour", {}).get("id")]
    ok(code == 200 and row and row[0].get("welt") == "berg" and row[0]["ele"] and row[0]["up"] == pr["up"], "gespeicherte Tour: «welt» berg, gleiche Zahlen wie beim Zeichnen")
    code, sw = jpost("/api/touren", {"action": "save", "name": "Seon", "pts": [[47.35, 8.16], [47.36, 8.17]], "lang": "de"}, HA)
    srow = [t for t in jget("/api/touren", HA)[1]["tours"] if t["id"] == sw.get("tour", {}).get("id")]
    ok(srow and "welt" not in srow[0] and not srow[0]["ele"], "Schweizer Tour: nicht im Bergtal, ohne Höhenpaket der Schweiz keine Höhen (unverändert)")
    code, vs = jget("/api/karte/berg/vorschlaege", HA)
    hz = [v for v in vs.get("tours", []) if v["name"].startswith("Hospiz")]
    ok(code == 200 and hz and hz[0]["ele"] and hz[0]["m"] > 500 and hz[0]["min"] > 10 and len(hz[0]["profile"]) > 10 and hz[0]["stops"][0] == "Furggapass mit Hospiz",
       "Vorschlag Hospiz → Pass → Biwak: Distanz, Auf- / Abstieg, Wanderzeit, Profil" + (f" ({hz[0]['m']:.0f} m, ↑ {hz[0]['up']} ↓ {hz[0]['down']}, {hz[0]['min']} min)" if hz else ""))
    # «Tour im Sim nachlaufen»
    sent = []
    ns["kq_sim_ok"] = lambda: True
    ns["sim_control"] = lambda d=None: (sent.append(d), {"ok": True, "tour": {"who": "person", "n": len(d.get("pts", []))}})[1]
    tid = sv["tour"]["id"]
    ok(jpost("/api/karte/berg", {"action": "tour_sim", "id": tid}, HA)[0] == 403, "Tour im Sim: nur der Admin")
    code, r = jpost("/api/karte/berg", {"action": "tour_sim", "id": tid}, H)
    p0 = sent[-1]["pts"][0] if sent else [0, 0]
    ok(code == 200 and r["ok"] and sent and sent[-1]["action"] == "bkarte" and sent[-1]["do"] == "tour" and abs(p0[0] - 60) < 0.2 and abs(p0[1] - 0) < 0.2 and sent[-1]["name"] == "Bergtal Probe",
       "Tour im Sim: {action bkarte, do tour, pts in Tal-Metern} an den Simulator")
    code, r = jpost("/api/karte/berg", {"action": "tour_sim", "vorschlag": hz[0]["i"] if hz else 0}, H)
    ok(code == 200 and len(sent[-1]["pts"]) == len(hz[0]["pts"] if hz else []) and len(sent[-1]["pts"]) <= 600, "Vorschlag im Sim nachlaufen")
    ok(jpost("/api/karte/berg", {"action": "tour_sim", "id": sw["tour"]["id"]}, H)[1].get("error", "").startswith("Diese Tour liegt nicht im Bergtal"), "Schweizer Tour: «liegt nicht im Bergtal»")
    ns["sim_control"] = lambda d=None: {"ok": False, "error": "unknown action"}
    ok("neuere Version" in jpost("/api/karte/berg", {"action": "tour_sim", "id": tid}, H)[1].get("error", ""), "alter Simulator: «braucht eine neuere Version»")
    ok(not any("47.3" in l or "0.000" in l for l in logs), "keine Koordinate im Protokoll")
    okk, _ = ns["bk_delete"]()
    ns["BK_RT"]["ok_t"] = 0
    ok(okk and not ns["bk_installed"]() and not os.path.isdir(ns["bk_dir"]()), "entfernen: Ordner weg")
    shutil.rmtree(home, ignore_errors=True)


# ---- B) in the browser --------------------------------------------------------------------------------------------------------------
def gepatcht(datei, tmp, data, unp, url):
    src = open(datei, encoding="utf-8").read()
    neu = 'BK_FILE = {"name": "bergtal-karte-1.zip", "size": %d, "sha256": "%s", "unpacked": %d, "sim": "test"}' % (len(data), hashlib.sha256(data).hexdigest(), unp)
    src, n = re.subn(r'^BK_FILE = \{"name": "[^"]*", "size": \d+, "sha256": "[0-9a-f]*", "unpacked": \d+, "sim": "[^"]*"\}', neu, src, flags=re.M)
    alt = 'BK_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/"}'
    assert n == 1 and src.count(alt) == 1
    src = src.replace(alt, "BK_BASE = {\"url\": %s}" % json.dumps(url), 1)
    ziel = os.path.join(tmp, os.path.basename(datei))
    open(ziel, "w", encoding="utf-8").write(src)
    for z in glob.glob(os.path.join(os.path.dirname(datei), "moveeye_daten_*.zip")):
        shutil.copyfile(z, os.path.join(tmp, os.path.basename(z)))
    return ziel


def teil_b(datei, data, unp, bilder):
    from playwright.sync_api import sync_playwright
    from piper_test import Srv
    import karten_test as KA
    print("B) im Browser (390 px DPR 2 und PC)", flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_bk_b_")
    srv = Srv()
    srv.files["/bergkarte-1/bergtal-karte-1.zip"] = data
    d2 = gepatcht(datei, tmp, data, unp, srv.url)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    PW = "Berg-" + os.urandom(4).hex()
    p, cfg = KA.starte(d2, tmp, port, PW)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, d=None, user=("admin", PW)):
        hd = {"Authorization": "Basic " + base64.b64encode(f"{user[0]}:{user[1]}".encode()).decode(), "Content-Type": "application/json", "Origin": base}
        r = urllib.request.Request(base + path, data=json.dumps(d).encode() if d is not None else None, headers=hd)
        try:
            with op.open(r, timeout=120) as x:
                return x.status, json.loads(x.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, {}
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt")).read()[-3000:])
            try:
                if req("/api/karte/berg")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        req("/api/users", {"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
        req("/api/karte/berg", {"action": "install"})
        for _i in range(120):
            if req("/api/karte/berg")[1].get("on"):
                break
            time.sleep(0.5)
        ok(req("/api/karte/berg")[1].get("on"), "Bergtal-Paket über HTTP geladen und installiert")
        if bilder:
            os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=KA.ARGS)
            aussen = []
            breit = "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
            for name, mob in (("390", True), ("pc", False)):
                vp = {"width": 390, "height": 844} if mob else {"width": 1366, "height": 900}
                ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2, http_credentials={"username": "admin", "password": PW}, locale="de-CH")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','light');localStorage.setItem('mw-sheet','page');"
                                    "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\",\"settings\",\"rec\",\"history\",\"sim\",\"protect\",\"zones\",\"cams\",\"place\",\"tools\"]')}catch(e){}")
                ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:")) else (aussen.append(r.request.url[:120]), r.abort()))
                pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                tap = (lambda sel: pg.tap(sel)) if mob else (lambda sel: pg.click(sel))
                pg.goto(base + "/karte")
                pg.wait_for_function("() => window.KQMAP && KQMAP.loaded() && window.BK && BK.map", timeout=90000)
                ok(pg.evaluate("() => BK.mode") == "berg" and pg.locator("#bk-welt").is_visible() and pg.locator("#bk-welt button.on").inner_text().strip().endswith("Bergtal"),
                   f"{name}: ohne Schweizer Karte direkt im Bergtal, Schalter «Schweiz | Bergtal» sichtbar")
                ok(pg.evaluate("() => !!document.querySelector('#kq-c canvas.maplibregl-canvas') && KQMAP.getStyle().layers.some(l => l.id === 'bk-hk')") and pg.evaluate(breit),
                   f"{name}: Karte mit Höhenlinien (MapLibre, WebGL), nichts ragt hinaus")
                pg.wait_for_function("() => KQMAP.querySourceFeatures('bk', {filter: ['==', ['get', 't'], 'ort']}).length > 0", timeout=30000)
                pg.wait_for_selector("#bk-live:not([hidden])", timeout=20000)
                ok(pg.evaluate("() => KQMAP.querySourceFeatures('geheim').length === 0") and "verborgen" in pg.inner_text("#bk-live"),
                   f"{name}: ohne Simulator keine geheimen Orte, Hinweis unter der Karte")
                pg.wait_for_selector("#bk-vor:not([hidden]) .kt-li", timeout=20000)
                pg.wait_for_timeout(600)
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, f"bergtal_2d_{name}.png"))
                pg.evaluate("() => document.getElementById('bk-3d').click()")
                pg.wait_for_function("() => KQMAP.getPitch() > 40 && !!KQMAP.getTerrain()", timeout=30000)
                try:                                                   # software WebGL: 3D takes a while (loaded() rarely settles)
                    pg.wait_for_function("() => KQMAP.queryTerrainElevation(KQMAP.getCenter()) > 1000", timeout=120000)
                except Exception:
                    pass
                pg.wait_for_timeout(4000)
                ok(pg.evaluate("() => KQMAP.queryTerrainElevation(KQMAP.getCenter()) > 1000"), f"{name}: 3D an (Neigung, Gelände mit Höhen des Pakets)")
                if bilder:
                    pg.screenshot(path=os.path.join(bilder, f"bergtal_3d_{name}.png"))
                pg.evaluate("() => document.getElementById('bk-2d').click()")
                pg.wait_for_function("() => KQMAP.getPitch() < 1 && !KQMAP.getTerrain()", timeout=60000)
                pg.locator("#bk-vor .kt-li").first.scroll_into_view_if_needed()
                pg.locator("#bk-vor .kt-li").first.click()
                pg.wait_for_selector("#bk-vor-d:not([hidden]) svg.kt-prof", timeout=20000)
                txt = pg.inner_text("#bk-vor-d")
                ok(all(w in txt for w in ("Distanz", "Aufstieg", "Abstieg", "Wanderzeit", "Hospiz")) and pg.locator("#bk-vor-back").is_visible(),
                   f"{name}: Vorschlag Hospiz → Pass → Biwak mit Zahlen und Höhenprofil, Weg zurück")
                pg.wait_for_function("() => KQMAP.getSource('bk-vor') && KQMAP.loaded()", timeout=20000); pg.wait_for_timeout(700)
                if bilder:
                    pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'start'})")
                    pg.screenshot(path=os.path.join(bilder, f"bergtal_tour_{name}.png"), full_page=False)
                    pg.locator("#bk-vor-d svg.kt-prof").scroll_into_view_if_needed()
                    pg.screenshot(path=os.path.join(bilder, f"bergtal_profil_{name}.png"), full_page=False)
                    pg.evaluate("() => document.getElementById('bk-3d').click()")
                    pg.wait_for_function("() => KQMAP.getPitch() > 40 && KQMAP.queryTerrainElevation(KQMAP.getCenter()) > 1000", timeout=120000); pg.wait_for_timeout(4000)
                    pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'start'})")
                    pg.screenshot(path=os.path.join(bilder, f"bergtal_tour_3d_{name}.png"))
                    pg.evaluate("() => document.getElementById('bk-2d').click()"); pg.wait_for_function("() => KQMAP.getPitch() < 1", timeout=60000)
                # draw a route (tours of 639zzx on the Bergtal map)
                pg.wait_for_selector("#kt:not([hidden]) #kt-new", timeout=20000)
                pg.locator("#kt-new").scroll_into_view_if_needed(); tap("#kt-new")
                pg.wait_for_selector("#kt-bar", timeout=10000)
                pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'center'})")
                pg.wait_for_timeout(300)
                bb = pg.locator("#kq-c").bounding_box()
                for fx, fy in ((0.35, 0.3), (0.5, 0.55), (0.62, 0.75)):
                    (pg.touchscreen.tap if mob else pg.mouse.click)(bb["x"] + bb["width"] * fx, bb["y"] + bb["height"] * fy)
                    pg.wait_for_timeout(250)
                pg.wait_for_function("() => document.querySelector('#kt-dinfo svg.kt-prof')", timeout=20000)
                dt = pg.inner_text("#kt-dinfo")
                ok("Aufstieg" in dt and "Wanderzeit" in dt and "Höhendaten" not in dt, f"{name}: gezeichnete Route im Bergtal mit Auf- / Abstieg und Profil aus dem Paket")
                pg.fill("#kt-dname", "Bergtal Test " + name); tap("#kt-save")
                pg.wait_for_selector("#kt-detail:not([hidden]) #kt-name", timeout=20000)
                ok(pg.locator("#kt-detail .bk-simtour").count() == 1, f"{name}: Tour-Detail hat «🎮 Tour im Sim nachlaufen» (Admin)")
                # the switch: to Switzerland and back (remembered)
                pg.locator("#bk-welt").scroll_into_view_if_needed()
                pg.locator("#bk-welt button[data-v=ch]").click()
                pg.wait_for_function("() => window.BK && BK.mode === 'ch' && !document.getElementById('kq-none').hidden", timeout=30000)
                nt = pg.inner_text("#kq-none")
                ok(pg.locator("#bk-welt").is_visible() and "nicht installiert" in nt, f"{name}: Schalter → Schweiz (hier nicht installiert: «{nt[:50]}»)")
                pg.wait_for_selector("#kt:not([hidden])", timeout=20000); pg.wait_for_timeout(500)
                ok(pg.locator("#kt .kt-li").filter(has_text="Bergtal Test").count() == 0 and pg.evaluate("() => !!document.querySelector('#kt-items')"),
                   f"{name}: in der Schweiz keine Bergtal-Touren in der Liste ({pg.locator('#kt .kt-li').count()} Touren sichtbar)")
                pg.goto(base + "/karte")
                pg.wait_for_function("() => window.BK && BK.mode === 'ch'", timeout=30000)
                ok(True, f"{name}: Wahl gemerkt (/karte ohne Angabe bleibt bei «Schweiz»)")
                pg.locator("#bk-welt button[data-v=berg]").click()
                pg.wait_for_function("() => window.BK && BK.mode === 'berg' && window.KQMAP && KQMAP.loaded()", timeout=60000)
                ok(True, f"{name}: zurück ins Bergtal")
                ok(not errs, f"{name}: keine JS-Fehler" + (f" ({errs[:2]})" if errs else ""))
                ctx.close()
            ok(not aussen, "keine Anfrage nach aussen" + (f" ({aussen[:3]})" if aussen else ""))
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(20)
        except Exception:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datei")
    ap.add_argument("--web")
    ap.add_argument("--export")
    ap.add_argument("--bilder")
    ap.add_argument("--ohne-browser", action="store_true")
    a = ap.parse_args()
    datei = a.datei or neueste_datei()
    tmp = tempfile.mkdtemp(prefix="mw_bk_")
    try:
        web = web_zip(a.web, tmp)
        exp = a.export or erfundenes_tal(os.path.join(tmp, "exp"))
        zp, data, unp = paket_bauen(exp, web, os.path.join(tmp, "out"))
        print("  Paket: %d Bytes (%d entpackt)" % (len(data), unp), flush=True)
        teil_a(datei, zp, data, unp, exp)
        if not a.ohne_browser:
            teil_b(datei, data, unp, a.bilder)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s: %d Fehler" % ("OK" if not FEHLER else "FEHLER", len(FEHLER)), flush=True)
    for f in FEHLER:
        print("  ✗", f)
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
