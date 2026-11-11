#!/usr/bin/env python3
"""Test «Überlebens-Almanach» (Teile 630, 639zzt, 639zzu) – ohne Kamera, ohne Lampe, ohne Sensor:

  A) im eigenen Prozess mit dem Flask-Testclient der gebauten Datei:
     Bilder: jedes Bild eines Artikels gibt es, ist gültiges SVG ohne fremde Adressen, nur mit Klassen der Seite.
     Knoten: die Kreuzungen im gezeichneten Bild passen zur gespeicherten Folge (der untere Strang ist dort unterbrochen,
     der obere läuft durch), jede Kreuzung hat ein «o» und ein «u», Schritt-Bilder zeigen nur Kreuzungen der Folge;
     der Achterknoten hat die Knoten-Determinante 5 (= echte Acht), der Kreuzknoten ist spiegelgleich (kein Altweiberknoten).
     Koordinaten: swisstopo-Beispiel und Nullpunkt Bern. Sonne / Mond: bekannte Werte (Sonnenwende, Finsternisse 2026).
     SOS: ohne Lampe Meldung; Start, Blinkmuster, Alarm-Licht geht vor, hört von selbst auf (verkürzte Zeit), Stopp,
     höchstens 3 Starts pro Stunde für Gäste, Push an den Besitzer; ein Gast darf genau diese eine Aktion und sonst nichts.
     Wetter: ohne Sensor / mit Sensor (stabil, fällt schnell).
  B) --browser: die Seite im Browser (iPhone-Breite 390): jeder Artikel in Hell, Dunkel und Rotlicht ohne Überbreite,
     Bilder geladen, keine JavaScript-Fehler, keine Anfrage nach aussen; mit --bilder ORDNER Bildschirmfotos.

  python3 werkzeuge/almanach_test.py [--datei X.py] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import os
import re
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from fractions import Fraction

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
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_alm_home_")
    os.environ["TZ"] = "Europe/Zurich"; time.tzset()
    ns = {"__name__": "mw_almanach_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


def determinante(G):
    """Knoten-Determinante aus den Kreuzungen eines Strangs (Enden aussen verbunden gedacht): Acht = 5, Kleeblatt = 3."""
    vis = sorted([(x["a"][1], i, 0) for i, x in enumerate(G["X"])] + [(x["b"][1], i, 1) for i, x in enumerate(G["X"])])
    n = len(G["X"])
    arc, cur, into, out, over = {}, 0, {}, {}, {}
    for _pos, xi, side in vis:
        if G["X"][xi]["over"] == side:
            over[xi] = cur
        else:
            into[xi] = cur; cur = (cur + 1) % n; out[xi] = cur
    for xi in over:
        over[xi] %= n
    M = [[Fraction(0)] * n for _ in range(n)]
    for xi in range(n):
        M[xi][over[xi]] += 2; M[xi][into[xi]] -= 1; M[xi][out[xi]] -= 1
    M = [r[:-1] for r in M[:-1]]
    det = Fraction(1)
    for c in range(len(M)):
        p = next((r for r in range(c, len(M)) if M[r][c] != 0), None)
        if p is None:
            return 0
        if p != c:
            M[c], M[p] = M[p], M[c]; det = -det
        det *= M[c][c]
        for r in range(c + 1, len(M)):
            f = M[r][c] / M[c][c]
            M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    return abs(int(det))


def svg_punkte(svg):
    """{Strang: [(x, y)]} aus den gezeichneten Wegen eines Knotenbildes"""
    out = {}
    for m in re.finditer(r'<path class="k[01]" data-s="(\d+)" d="([^"]+)"', svg):
        pts = [tuple(float(v) for v in p.split()) for p in m.group(2).replace("M", "").split(" L")]
        out.setdefault(int(m.group(1)), []).extend(pts)
    return out


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    ns = laden(datei)
    CFG, STATE, SOS = ns["CFG"], ns["STATE"], ns["ALM_SOS"]
    ALMANAC, FIG, PICS, KNOTS = ns["ALMANAC"], ns["ALM_FIG"], ns["ALM_PICS"], ns["ALM_KNOTS"]
    page = ns["ALM_PAGE"]

    # ---- Inhalt
    keys = [c[0] for c in ALMANAC]
    ok(keys == ["notfall", "wetter", "gesundheit", "essbar", "wasser", "feuer", "orientierung", "lager", "spuren", "knoten", "nacht", "abend"], f"Kapitel {keys}")
    titles = [a[0] for c in ALMANAC for a in c[3]]
    ok(len(titles) == len(set(titles)) == 59, f"59 Artikel, keiner doppelt ({len(titles)})")
    kn = [a[0] for c in ALMANAC if c[0] == "knoten" for a in c[3]]
    ok(kn[-1] == "Was ins Taschenmesser gehört" and len(kn) == 9, f"Knoten-Kapitel {kn}")
    text = "\n".join(a[1] for c in ALMANAC for a in c[3])
    ok("ß" not in text, "Schweizer Schreibweise (kein ß)")
    for nr in ("112", "144", "1414", "117", "118", "145"):
        ok(nr in dict(ALMANAC[0][3])["Notrufnummern Schweiz"] and ">%s<" % nr in PICS["nummern"][1], f"Notrufnummer {nr} in Text und Bild")
    ok("Nie nur nach diesem Almanach oder einer App essen" in text and "145" in dict(ALMANAC[keys.index("essbar")][3])["Zuerst lesen: die Regeln"], "Warnung im Kapitel «Essbar oder giftig?»")
    ok("kein sicherer Knoten, um zwei Seile zu verbinden" in dict(ALMANAC[keys.index("knoten")][3])["Kreuzknoten"], "Warnung beim Kreuzknoten")
    ok("Abstand halten" in dict(ALMANAC[keys.index("gesundheit")][3])["Schlangen in der Schweiz"] and "Abstand halten" in PICS["schlangen"][1], "Schlangen: im Zweifel Abstand halten")

    # ---- Bilder: vorhanden, gültiges SVG, nichts von aussen, nur Klassen der Seite
    css = set(re.findall(r"svg \.([a-z0-9]+)", page)) | {"c", "kn"}
    for t, figs in FIG.items():
        ok(t in titles, f"Bild für einen Artikel, den es nicht gibt: {t}")
        b = ns["alm_bilder"](t)
        ok(len(b) >= len(figs), f"{t}: Bilder fehlen")
        for f in b:
            try:
                root = ET.fromstring(f["svg"])
                ok(root.tag.endswith("svg") and root.get("viewBox"), f"{t}: kein SVG mit viewBox")
            except ET.ParseError as e:
                ok(False, f"{t}: SVG ungültig ({e})"); continue
            ok(not re.search(r"https?://(?!www\.w3\.org/2000/svg)|href|<image|url\(|<script|<foreignObject|@import", f["svg"]), f"{t}: fremde Adresse / aktiver Inhalt im Bild")
            used = {c for el in root.iter() for c in (el.get("class") or "").split()}
            ok(used <= css, f"{t}: Klasse ohne Stil {sorted(used - css)}")
            ok(not re.search(r'(fill|stroke)="#|fill:#|stroke:#', f["svg"]), f"{t}: feste Farbe (passt nicht zu Hell / Dunkel / Rotlicht)")
    ok(all(any(a[0] in FIG for a in c[3]) for c in ALMANAC), "jedes Kapitel hat Bilder")
    ok(sum(len(v[1]) for v in PICS.values()) < 60000, "Zeichnungen bleiben klein (< 60 KB Quelltext)")

    # ---- Knoten: Bild = Folge
    ok(set(KNOTS) == {"achter", "kreuz", "palstek", "mastwurf", "spann", "zimmermann", "trucker", "prusik"}, f"Knoten {sorted(KNOTS)}")
    for key, K in KNOTS.items():
        G = ns["alm_knot_geo"](K)
        ok(not G["err"], f"{key}: {G['err']}")
        ok(G["seq"] == ["".join(c for c in s["seq"] if c in "ouvh") for s in K["s"]], f"{key}: Folge im Bild {G['seq']}")
        ok(all(sorted(x["tok"]) == ["o", "u"] for x in G["X"]), f"{key}: jede Kreuzung einmal oben, einmal unten")
        steps = ns["alm_knot_steps"](key)
        ok(3 <= len(steps) <= 5, f"{key}: {len(steps)} Bilder")
        fin = steps[-1][0]
        marks = [tuple(int(v) for v in mk.split(",")) for mk in re.search(r'data-x="([^"]*)"', fin).group(1).split()]
        if key != "prusik":
            ok(len(marks) == len(G["X"]), f"{key}: fertiges Bild zeigt alle {len(G['X'])} Kreuzungen ({len(marks)})")
        prev = -1
        for si, (svg, cap) in enumerate(steps):
            pts = svg_punkte(svg)
            mk = [tuple(int(v) for v in m_.split(",")) for m_ in re.search(r'data-x="([^"]*)"', svg).group(1).split()]
            ok(len(mk) >= prev, f"{key} Schritt {si + 1}: weniger Kreuzungen als im Schritt davor"); prev = len(mk)
            for x, y, o, u in mk:
                du = min((abs(px - x) + abs(py - y) for px, py in pts.get(u, [])), default=99)
                do = min((abs(px - x) + abs(py - y) for px, py in pts.get(o, [(-99, -99)]) if True), default=99)
                if o == u:                                 # same strand: the over pass is near, the under pass has a hole -
                    near = sorted(abs(px - x) + abs(py - y) for px, py in pts.get(o, []))[:1]
                    ok(near and near[0] < 5, f"{key} Schritt {si + 1}: bei {x},{y} läuft kein Strang durch")
                    idx = [k for k, (px, py) in enumerate(pts.get(o, [])) if (px - x) ** 2 + (py - y) ** 2 < 2.4 ** 2]
                    ok(not idx or max(idx) - min(idx) <= 4, f"{key} Schritt {si + 1}: bei {x},{y} ist der untere Strang nicht unterbrochen")
                else:
                    ok(do < 5 and du > 3, f"{key} Schritt {si + 1}: Kreuzung {x},{y} oben {do:.1f} / unten {du:.1f}")
            ok(len(cap) > 15 and svg.count("<path") < 120, f"{key} Schritt {si + 1}: Beschriftung / Grösse")
    ok(determinante(ns["alm_knot_geo"](KNOTS["achter"])) == 5, "Achterknoten: Determinante 5")
    falsch = dict(KNOTS["achter"], s=[dict(KNOTS["achter"]["s"][0], seq="ouuoouou")])
    gf = ns["alm_knot_geo"](falsch)
    ok(gf["err"] or determinante(gf) != 5, "eine falsche Folge fällt auf")
    a_, b_ = KNOTS["kreuz"]["s"][0]["seq"], KNOTS["kreuz"]["s"][1]["seq"]
    ok(a_ == a_[::-1] and b_ == b_[::-1] and a_[:3] in ("uou", "ouo") and a_ != "uououo" and b_ == a_.translate(str.maketrans("ou", "uo")), f"Kreuzknoten spiegelgleich, nicht durchgehend abwechselnd: {a_} / {b_}")
    try:
        ns["alm_knot_svg"](falsch); ok(gf["err"] == [], "ein Bild mit widersprüchlicher Folge wird nicht gezeichnet")
    except ValueError:
        ok(True, "")

    # ---- Koordinaten (swisstopo: Beispiel der Näherungsformeln, Nullpunkt alte Sternwarte Bern, Säntis)
    e, n = ns["alm_lv95"](46 + 2 / 60 + 38.87 / 3600, 8 + 43 / 60 + 49.79 / 3600)
    ok(abs(e - 2699999.76) < 0.05 and abs(n - 1099999.97) < 0.05, f"swisstopo-Beispiel {e:.2f} / {n:.2f}")
    e, n = ns["alm_lv95"](46.951083, 7.438637)
    ok(abs(e - 2600000) < 1.5 and abs(n - 1200000) < 1.5, f"Bern {e:.1f} / {n:.1f}")
    CFG["latitude"], CFG["longitude"], CFG["gpsmod_on"] = 47.37, 8.54, False
    ns["GPS"].update(lat=None)
    ok(ns["alm_ort"]() == {"ok": False}, "Werkseinstellung ist kein Standort")
    CFG["latitude"], CFG["longitude"] = 46.95108, 7.43864
    o = ns["alm_ort"]()
    ok(o["ok"] and o["lv95"] == "2'600'001 / 1'200'000" and o["wgs"] == "46.95108, 7.43864" and o["dms"] == "46°57'03.9\" N 7°26'19.1\" O", f"Standort {o}")
    CFG["latitude"], CFG["longitude"] = 52.52, 13.40
    ok("lv95" not in ns["alm_ort"]() and ns["alm_ort"]()["ok"], "ausserhalb der Schweiz: nur WGS84")
    CFG["latitude"], CFG["longitude"] = 46.95108, 7.43864

    # ---- Sonne und Mond
    def minuten(s):
        return int(s[:2]) * 60 + int(s[3:])
    nt = ns["alm_nacht"](datetime(2026, 6, 21, 12), 46.948, 7.447)
    ok(abs(minuten(nt["sonne_auf"]) - (5 * 60 + 36)) <= 4 and abs(minuten(nt["sonne_unter"]) - (21 * 60 + 28)) <= 4, f"Bern 21.6.: {nt['sonne_auf']} / {nt['sonne_unter']}")
    ok(nt["nacht_ab"] and nt["nacht_bis"] and 0 < minuten(nt["nacht_bis"]) - minuten(nt["nacht_ab"]) < 180, f"Bern 21.6.: nur kurz ganz dunkel ({nt['nacht_ab']}–{nt['nacht_bis']})")
    nt = ns["alm_nacht"](datetime(2026, 12, 21, 12), 47.377, 8.541)
    ok(abs(minuten(nt["sonne_auf"]) - (8 * 60 + 10)) <= 4 and abs(minuten(nt["sonne_unter"]) - (16 * 60 + 37)) <= 4, f"Zürich 21.12.: {nt['sonne_auf']} / {nt['sonne_unter']}")
    ok(abs(minuten(nt["nacht_ab"]) - (18 * 60 + 30)) <= 6 and abs(minuten(nt["nacht_bis"]) - (6 * 60 + 18)) <= 6, f"Zürich 21.12. Dämmerung {nt['nacht_ab']} / {nt['nacht_bis']}")
    ok({"Orion (Wintersternbild)", "Kassiopeia"} <= {s["name"] for s in nt["sterne"]} and not any("Wega" in s["name"] for s in nt["sterne"]), "Winter: Orion ja, Wega nein")
    for d in (datetime(2026, 6, 21), datetime(2026, 12, 21), datetime(2026, 3, 20)):      # the own scan against sun_times (030)
        st = ns["sun_times"](d.date(), 46.948, 7.447)
        up, down = ns["alm_events"](d.date(), 46.948, 7.447, "sun", -0.833)
        ok(abs(up[0] - st[0]) < 2.5 and abs(down[0] - st[1]) < 2.5, f"Sonnenauf-/untergang zweimal gerechnet {d:%d.%m.}: {up[0]:.1f}/{st[0]:.1f}")
    jd = ns["_alm_jd"](datetime(2026, 8, 12, 17, 37))       # new moon = total solar eclipse of 12.8.2026 (17:37 UT)
    mo, so = ns["alm_moon_pos"](jd), ns["alm_sun_pos"](jd)
    el = (mo[2] - so[2] + 180) % 360 - 180
    ok(abs(el) < 0.6 and ns["alm_moon_lit"](jd)[0] < 0.01, f"Neumond / Sonnenfinsternis 12.8.2026: Abstand {el:.2f}°")
    jd = ns["_alm_jd"](datetime(2026, 3, 3, 11, 38))        # full moon = total lunar eclipse of 3.3.2026 (11:38 UT)
    mo, so = ns["alm_moon_pos"](jd), ns["alm_sun_pos"](jd)
    el = (mo[2] - so[2]) % 360 - 180
    ok(abs(el) < 0.6 and ns["alm_moon_lit"](jd)[0] > 0.99 and abs(ns["_alm_altaz"](mo[0], mo[1], jd, 0, 0)[0]) <= 90, f"Vollmond / Mondfinsternis 3.3.2026: Abstand {el:.2f}°")
    nt = ns["alm_nacht"](datetime(2026, 3, 3, 12), 46.004, 8.951)
    ok(nt["mond"]["hell"] >= 99 and abs(minuten(nt["mond_auf"]) - minuten(nt["sonne_unter"])) < 30, f"Vollmond geht bei Sonnenuntergang auf ({nt['mond_auf']} / {nt['sonne_unter']})")
    nt = ns["alm_nacht"](datetime(2026, 8, 12, 12), 46.02, 7.75)
    ok(nt["mond"]["hell"] <= 1 and abs(minuten(nt["mond_unter"]) - minuten(nt["sonne_unter"])) < 15 and nt["mond_auf"] == "05:43", f"Neumond geht mit der Sonne unter ({nt['mond_unter']} / {nt['sonne_unter']}, auf {nt['mond_auf']})")
    nt = ns["alm_nacht"](datetime(2026, 6, 21, 12), 46.948, 7.447)
    ok((nt["mond_auf"], nt["mond_unter"]) == ("13:09", "01:02"), f"Mond Bern 21.6.2026 (eigener Vergleichswert) {nt['mond_auf']} / {nt['mond_unter']}")

    # ---- Web: Rechte, SOS, Wetter
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de", light_white_out="", sim_on=False, notify_on=True, light_white="off", light_hold=30.0)
    ADMIN_PW = "Admin-Pass-123"
    assert ns["web_pw_set"](ADMIN_PW)[0]
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    app = ws.app
    c = app.test_client(use_cookies=False)
    A_ = basic("admin", ADMIN_PW)

    def sos(action, **kw):
        r = c.post("/almanach/sos", json={"action": action}, **kw)
        return r.status_code, (r.get_json(silent=True) or {})
    for path in ("/almanach/", "/almanach/plus", "/almanach/live", "/almanach/bilder?t=Palstek"):
        ok(c.get(path).status_code == 200, f"Gast: {path} offen")
    j = c.get("/almanach/plus").get_json()
    ok("Palstek" in j["bilder"] and j["quellen"]["essbar"].startswith("Quellen:") and j["karte"] in (True, False), "/almanach/plus")
    ok(len(c.get("/almanach/bilder?t=Palstek").get_json()["f"]) == 4 and c.get("/almanach/bilder?t=gibt es nicht").get_json()["f"] == [], "/almanach/bilder")
    for path, meth in (("/api/state", "get"), ("/api/light", "post"), ("/api/disco", "post"), ("/api/settings", "post"), ("/recordings", "get"), ("/tausch", "get"), ("/api/ui", "post")):
        r = getattr(c, meth)(path, **({"json": {}} if meth == "post" else {}))
        ok(r.status_code in (401, 403), f"Gast: {meth.upper()} {path} bleibt zu ({r.status_code})")
    posts = sorted(r.rule for r in app.url_map.iter_rules() if r.rule.startswith("/almanach") and (r.methods & {"POST", "PUT", "DELETE", "PATCH"}))
    ok(posts == ["/almanach/sos"], f"unter /almanach/ gibt es genau eine Aktion: {posts}")
    code, j = sos("start")
    ok(code == 409 and j["msg"] == "keine Lampe angeschlossen" and not SOS["on"] and not SOS["pushes"], f"ohne Lampe: {code} {j.get('msg')}")
    ok(c.get("/almanach/live?w=ort").get_json()["sos"]["lampe"] is False, "Zustand: keine Lampe")
    CFG["light_white_out"] = "gpio:17"
    r = c.post("/almanach/sos", json={"action": "start"}, headers={"Origin": "http://boese.example"})
    ok(r.status_code == 403 and not SOS["on"], "fremde Webseite kann die Lampe nicht starten")
    code, j = sos("start")
    ok(code == 200 and j["ok"] and j["sos"]["on"] and 295 <= j["sos"]["rest"] <= 300 and j["sos"]["frei"] == 2, f"Gast startet SOS: {j}")
    ok(len(SOS["pushes"]) == 1 and SOS["pushes"][0].startswith("SOS-Lampe wurde ausgelöst von einem Gast (") and "WLAN" not in SOS["pushes"][0], f"Push {SOS['pushes']}")
    t0 = SOS["t0"]; muster = ""
    real = time.time
    try:
        for k in range(34):
            ns["time"].time = lambda k=k: t0 + k * 0.25 + 0.01
            muster += "1" if ns["lights_tick"]()["white"] else "0"
        ok(muster == "1010100011101110111000101010000000", f"Blinkmuster · · · — — — · · · ({muster})")
        ns["time"].time = lambda: t0 + 0.01
        ok(ns["lights_tick"]().get("ir") is False, "das Infrarot-Licht bleibt, wie es ist")
        ns["LIGHTS"]["alarm_t"] = t0                        # an alarm: its light rules go first (white light is off here)
        ok(ns["lights_tick"]()["white"] is False and c.get("/almanach/live?w=ort").get_json()["sos"]["alarm"], "bei Alarm blinkt SOS nicht dazwischen")
        ns["LIGHTS"]["alarm_t"] = 0.0
        ns["LIGHTS"]["strobe_until"] = t0 + 5
        ok(ns["lights_tick"]()["white"] == (int((t0 + 0.01) * 5) % 2 == 0), "die Abschreckung (Blitzlicht) geht vor")
        ns["LIGHTS"]["strobe_until"] = 0.0
    finally:
        ns["time"].time = real
    code, j = sos("start")
    ok(code == 200 and len(SOS["pushes"]) == 1 and j["sos"]["frei"] == 2, "läuft schon: kein zweiter Push, kein Zähler")
    code, j = sos("stop")
    ok(code == 200 and not j["sos"]["on"] and ns["lights_tick"]()["white"] is False, "Stopp")
    SOS["dauer"] = 0.4
    code, j = sos("start")
    ok(code == 200 and j["sos"]["on"], "zweiter Start")
    time.sleep(0.6)
    ok(ns["lights_tick"]()["white"] is False and not SOS["on"] and not c.get("/almanach/live?w=ort").get_json()["sos"]["on"], "hört von selbst auf")
    code, j = sos("start"); sos("stop")
    ok(code == 200 and j["sos"]["frei"] == 0, "dritter Start")
    code, j = sos("start")
    ok(code == 429 and not j["ok"] and "112" in j["msg"] and not SOS["on"], f"vierter Start in einer Stunde: {code} {j.get('msg')}")
    code, j = sos("start", headers=A_)
    ok(code == 200 and j["sos"]["on"] and SOS["pushes"][-1] == "SOS-Lampe wurde ausgelöst von admin" or SOS["pushes"][-1].startswith("SOS-Lampe wurde ausgelöst von A"), f"Administrator ohne Grenze: {code} {SOS['pushes'][-1:]}")
    sos("stop")
    SOS["starts"][:] = [time.time() - 3700] * 3
    ok(sos("start")[0] == 200, "nach einer Stunde geht es wieder"); sos("stop")
    CFG["light_white"] = "off"
    ok(CFG["light_white"] == "off" and CFG["light_white_out"] == "gpio:17", "SOS ändert keine Einstellung")

    STATE["env"] = None; ns["STORM"]["p"].clear()
    ok(c.get("/almanach/live?w=wetter").get_json()["wetter"] == {"ok": False}, "Wetter ohne Sensor")
    now = time.time()
    STATE["env"] = {"t": 14.5, "h": 60, "p": 950.0, "src": "BME280", "ds": [], "time": now}
    for k in range(240, -1, -1):
        ns["STORM"]["p"].append((now - k * 60, 950.0 + 0.002 * k))
    w = c.get("/almanach/live?w=wetter").get_json()["wetter"]
    ok(w["ok"] and w["p"] == 950.0 and w["stufe"] == 0 and "stabil" in w["text"] and len(w["kurve"]) > 20 and w["stunden"] == 4.0, f"Wetter stabil {w}")
    ns["STORM"]["p"].clear()
    for k in range(240, -1, -1):
        ns["STORM"]["p"].append((now - k * 60, 950.0 + 1.5 * k / 60.0))
    w = c.get("/almanach/live?w=wetter").get_json()["wetter"]
    ok(w["stufe"] == 1 and w["h1"] == -1.5 and w["h3"] == -4.5 and "kann auf" in w["text"], f"Luftdruck fällt schnell {w}")
    ns["STORM"]["p"].clear()
    for k in range(240, -1, -1):
        ns["STORM"]["p"].append((now - k * 60, 950.0 + 2.6 * k / 60.0))
    w = c.get("/almanach/live?w=wetter").get_json()["wetter"]
    ok(w["stufe"] == 2 and "Gewitter" in w["text"] and "hindeuten" in w["text"], f"Luftdruck fällt sehr schnell {w}")
    nt = c.get("/almanach/live?w=nacht").get_json()["nacht"]
    ok(nt.get("ort_ok") is True and re.fullmatch(r"\d\d:\d\d", nt["sonne_auf"]) and nt["mond"]["name"], f"Heute Nacht {nt}")
    ok("alm_selftest" in ns and ns["alm_selftest"]().startswith("8 knots"), "Selbsttest")
    return ns, app


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(ns, app, bilder):
    from playwright.sync_api import sync_playwright
    from werkzeug.serving import make_server
    srv = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.server_port
    ALMANAC, FIG, SOS = ns["ALMANAC"], ns["ALM_FIG"], ns["ALM_SOS"]
    SOS.update(on=False, dauer=300.0); SOS["starts"].clear()
    arts = [(c[0], a[0]) for c in ALMANAC for a in c[3]]
    if bilder:
        os.makedirs(bilder, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        errs, fremd = [], []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("request", lambda r: fremd.append(r.url) if not r.url.startswith(base) and not r.url.startswith("data:") else None)
        pg.goto(base + "/almanach/")
        pg.wait_for_selector(".chp")
        ok(pg.locator(".chp").count() == 12, "12 Kapitel auf der Startseite")

        def thema(t):
            pg.evaluate("([th, n]) => { localStorage.setItem('mw-theme', th); localStorage.setItem('mw-night', n); apply(); }",
                        ["light" if t == "hell" else "dark", "1" if t == "rot" else "0"])

        def breit(was):
            w = pg.evaluate("[document.documentElement.scrollWidth, innerWidth, Math.max(0, ...[...document.querySelectorAll('main *')].map(e => e.getBoundingClientRect().right))]")
            ok(w[0] <= w[1] and w[2] <= w[1] + 0.5, f"{was}: zu breit {w}")

        def foto(name):
            if bilder:
                pg.wait_for_timeout(120)
                pg.screenshot(path=os.path.join(bilder, name + ".png"), full_page=True)
        for t in ("hell", "dunkel", "rot"):
            thema(t)
            pg.evaluate("home('')"); pg.wait_for_selector(".chp"); breit(f"Inhalt {t}")
            if t != "rot":
                foto(f"01_inhalt_{t}")
            for i, (ch, title) in enumerate(arts):
                pg.evaluate("i => show(i)", i)
                want = len(ns["alm_bilder"](title)) if title in FIG else 0
                if want:
                    pg.wait_for_function("n => document.querySelectorAll('#figs figure svg').length === n", arg=want, timeout=8000)
                ok(pg.locator("article h2").inner_text() == title, f"Artikel {title}")
                breit(f"{title} ({t})")
                if t != "rot" and (ch in ("knoten", "spuren", "essbar") and want or title in ("Die stabile Seitenlage", "Notsignale", "Schlangen in der Schweiz", "Wolken als Wettervorhersage")):
                    foto("%s_%s_%s" % ({"knoten": "02_knoten", "spuren": "06_spuren", "essbar": "07_essbar"}.get(ch, "08_bild"), re.sub(r"\W+", "_", title)[:24], t))
            for nr, key, sel in ((3, "notfall", "#sos"), (4, "wetter", "#wetter"), (5, "nacht", "#nacht")):
                ci = [c[0] for c in ALMANAC].index(key)
                pg.evaluate("i => chap(i)", ci); pg.wait_for_selector(sel); breit(f"Kapitel {key} ({t})")
                if key == "notfall":
                    ok("2'600'001 / 1'200'000" in pg.locator("#ort .big").inner_text() and pg.locator("#b-copy").count() == 1, "Standort gross, mit Kopieren")
                if t != "rot":
                    foto(f"0{nr}_{key}_{t}")
        thema("hell")
        pg.evaluate("i => chap(i)", 0); pg.wait_for_selector("#b-sos")
        pg.click("#b-sos"); pg.wait_for_selector("#b-sosx")
        ok(SOS["on"] and "hört in" in pg.locator("#sos").inner_text(), "SOS-Knopf startet, Stopp-Knopf erscheint")
        foto("03_notfall_sos_laeuft_hell")
        pg.click("#b-sosx"); pg.wait_for_selector("#b-sos")
        ok(not SOS["on"], "Stopp-Knopf")
        ns["CFG"]["light_white_out"] = ""
        pg.evaluate("i => chap(i)", 0); pg.wait_for_selector("#sos")
        ok("keine Lampe angeschlossen" in pg.locator("#sos").inner_text() and pg.locator("#b-sos").count() == 0, "ohne Lampe: Hinweis statt Knopf")
        ns["STATE"]["env"] = None
        pg.evaluate("i => chap(i)", 1); pg.wait_for_selector("#wetter")
        ok("Kein Luftdruck-Sensor" in pg.locator("#wetter").inner_text(), "Wetter ohne Sensor: kleiner Hinweis")
        foto("04_wetter_ohne_sensor_hell")
        pg.evaluate("i => show(i)", [a[1] for a in arts].index("Palstek")); pg.wait_for_selector("#figs figure")
        pg.click("#figs figure >> nth=0")
        ok(pg.locator("figure.zoom").count() == 1, "Bild antippen = gross")
        pg.click("figure.zoom"); ok(pg.locator("figure.zoom").count() == 0, "noch einmal = wieder klein")
        pg.fill("#q", "prusik"); pg.wait_for_selector(".it")
        ok(pg.locator(".it").count() >= 1, "Suche findet neue Artikel")
        ok(not errs, f"JavaScript-Fehler: {errs[:3]}")
        ok(not fremd, f"Anfragen nach aussen: {fremd[:3]}")
        b.close()
    srv.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei"); ap.add_argument("--browser", action="store_true"); ap.add_argument("--bilder")
    a = ap.parse_args()
    datei = a.datei or neueste()
    print("Almanach-Test mit", os.path.basename(datei), flush=True)
    ns, app = teil_a(datei)
    print(f"A fertig: {N['ok']} Prüfungen, {len(FEHLER)} Fehler", flush=True)
    if a.browser or a.bilder:
        ns["CFG"]["light_white_out"] = "gpio:17"
        teil_b(ns, app, a.bilder)
    print(f"{N['ok']} Prüfungen, {len(FEHLER)} Fehler")
    for f in FEHLER:
        print("  ✗ " + f)
    sys.stdout.flush()
    os._exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
