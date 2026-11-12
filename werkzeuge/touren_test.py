#!/usr/bin/env python3
"""MoveEye: Test «🥾 Touren» auf der Offline-Karte (Teil 639zzx, werkzeuge/karten/hoehe.py).

  python3 werkzeuge/touren_test.py [--web karte-web-1.zip] [--bilder ORDNER] [--ohne-browser] [--datei X.py]
  python3 werkzeuge/touren_test.py --hoehe-echt ORDNER     # das echte Höhenpaket (Ausgabe von hoehe.py): Kopf, bekannte Höhen, Abdeckung
  python3 werkzeuge/touren_test.py --tour DATEI.kml --bilder ORDNER   # eine eigene Tour im Browser (nur lokal; nichts davon kommt ins Repository)

A) im Prozess: Selbsttest, eine Tour im Aufbau des Exports der swisstopo-App (hier erzeugt – Ordner «Waypoints» und «Tracks»,
   2204 Punkte lon,lat,Höhe): Distanz / Auf- / Abstieg / Zeit gegen eine eigene Rechnung, GPX mit unruhigen Höhen wird
   geglättet (und so gemeldet), Härtung: böse und grosse Dateien (~2 MB) sind je unter ZEIT_MAX fertig (angenommen oder
   abgelehnt), keine Entity-Bombe, Namen nur als Text; Rechte (Admin, Familie, Kind, Gast), Import / Zeichnen / Umbenennen /
   «Nur ich» / Löschen, Export GPX + KML (wieder lesbar) + ZIP, keine Koordinate im Protokoll; Höhenpaket mit einer kleinen
   Ersatz-Datei: nur der Admin lädt, zu wenig Platz und veränderte Datei abgelehnt, gezeichnete Route bekommt Auf- / Abstieg,
   ausserhalb «keine Höhendaten» (nie 0).
B) im Browser bei 390 px (und PC): Kachel «🗺 Karte» unter «Mehr», /karte mit dem Kasten «Touren», Import über den
   Datei-Knopf, Linie + Wegpunkte + Zahlen + Profil, Route zeichnen (antippen, rückgängig, Punkt löschen, speichern),
   Löschen mit Rückfrage in der Seite, überall ein sichtbarer Weg zurück, nichts ragt seitlich hinaus, keine Anfrage
   nach aussen, Gast-Seite ohne Skript.
"""
import argparse
import base64
import gzip
import hashlib
import json
import math
import os
import random
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
sys.path.insert(0, os.path.join(HIER, "karten"))
ZEIT_MAX = 20.0          # s pro Datei; lokal gemessen < 0,5 s, langsame GitHub-Läufer brauchen ein Mehrfaches - mit viel Luft
FEHLER = []


def ok(c, what):
    print(("  ✓ " if c else "  ✗ ") + what, flush=True)
    if not c:
        FEHLER.append(what)
    return c


def hav(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 12742017.6 * math.asin(math.sqrt(h))


def beispiel_punkte(n=2204):
    """a made-up tour near Seon AG (not a real export): a winding line of ~15 km with smooth heights 450–1100 m"""
    pts = []
    for i in range(n):
        f = i / (n - 1)
        lat = 47.3475 + 0.06 * f + 0.004 * math.sin(f * 40)
        lon = 8.1602 + 0.09 * f + 0.006 * math.cos(f * 31)
        ele = 450 + 650 * math.sin(f * math.pi) ** 2 + 30 * math.sin(f * 25)
        pts.append((round(lat, 6), round(lon, 6), round(ele, 1)))
    return pts


def beispiel_kml(pts, name="Seon – Probetour"):
    """the structure of the KML export of the swisstopo app: Document name, folder «Waypoints» (points with ExtendedData),
    folder «Tracks» with ONE LineString «lon,lat,height»"""
    wp = [("Startpunkt", pts[0])] + [("Wegpunkt", pts[len(pts) * k // 7]) for k in range(1, 7)] + [("Ziel", pts[-1])]
    o = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">',
         "<Document>", '<Style id="track"><LineStyle><color>ff0000ff</color><width>4</width></LineStyle></Style>',
         "<Folder>", "<name>Waypoints</name>"]
    for nm, p in wp:
        o.append('<Placemark><name>%s</name><ExtendedData><Data name="type"><value>swisstopo</value></Data></ExtendedData>'
                 "<Point><coordinates>%.6f,%.6f,%.1f</coordinates></Point></Placemark>" % (nm, p[1], p[0], p[2]))
    o += ["</Folder>", "<Folder>", "<name>Tracks</name>", "<Placemark><name>Swisstopo Route</name><styleUrl>#track</styleUrl><LineString><tessellate>1</tessellate><coordinates>",
          " ".join("%.6f,%.6f,%.1f" % (p[1], p[0], p[2]) for p in pts), "</coordinates></LineString></Placemark>", "</Folder>"] + (["<name>%s</name>" % name] if name else []) + ["</Document>", "</kml>"]   # the name of the document stands AFTER the folders
    return "\n".join(o).encode("utf-8")


def beispiel_gpx(pts, rausch=0.0, name="GPS-Spur"):
    rnd = random.Random(7)
    o = ['<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1"><metadata><name>%s</name></metadata>' % name,
         '<wpt lat="%.6f" lon="%.6f"><ele>%.1f</ele><name>Hütte &lt;b&gt;</name></wpt>' % pts[0], "<trk><name>%s</name><trkseg>" % name]
    for p in pts:
        o.append('<trkpt lat="%.6f" lon="%.6f"><ele>%.1f</ele><time>2026-07-01T10:00:00Z</time></trkpt>' % (p[0], p[1], p[2] + rnd.uniform(-rausch, rausch)))
    o.append("</trkseg></trk></gpx>")
    return "\n".join(o).encode("utf-8")


def boese_dateien():
    """(name, bytes, what must happen: "ok" | "nein" | "egal")"""
    M = 2 * 1024 * 1024
    k = lambda body: b'<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><LineString><coordinates>' + body + b"</coordinates></LineString></Placemark></Document></kml>"
    out = [("Entity-Bombe", b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY a "aaaaaaaaaa">' + b"".join(b'<!ENTITY %c "%s">' % (98 + i, (b"&%c;" % (97 + i)) * 10) for i in range(9))
            + b"]><kml><Document><name>&j;</name></Document></kml>", "nein"),
           ("externe Entity", b'<?xml version="1.0"?><!DOCTYPE k [<!ENTITY x SYSTEM "file:///etc/passwd">]><kml><Document><name>&x;</name></Document></kml>', "nein"),
           ("95 000 Punkte", k(b" ".join(b"8.%06d,47.%06d,500" % (i % 999999, i % 999999) for i in range(95000))), "ok"),
           ("ein 2-MB-Wort", k(b"1," * (M // 2)), "nein"),
           ("2 MB Kommas und Leerzeichen", k(b" , ,, " * (M // 6)), "nein"),
           ("2 MB Leerraum", k(b" \n\t" * (M // 3) + b"8.1,47.0,500 8.2,47.0,510"), "ok"),
           ("2 MB Ziffern", k(b"9" * M), "nein"),
           ("inf / nan / 1e999", k(b"inf,nan,1e999 1e999,1e999 nan,nan " * 50000 + b"8.1,47.0 8.2,47.0"), "ok"),
           ("40 000 Ebenen tief", b"<kml>" + b"<a>" * 40000 + b"</a>" * 40000 + b"</kml>", "nein"),
           ("600 000 leere Elemente", b"<kml><Document>" + b"<a/>" * 600000 + b"</Document></kml>", "nein"),
           ("22 000 Placemarks ohne Linie", b"<kml><Document>" + b"<Placemark><name>x</name><Point><coordinates>8,47</coordinates></Point></Placemark>" * 22000 + b"</Document></kml>", "nein"),
           ("2-MB-Name", b"<kml><Document><name>" + b"A" * M + b"</name><Placemark><LineString><coordinates>8,47 8.1,47</coordinates></LineString></Placemark></Document></kml>", "ok"),
           ("2-MB-Attribut", b'<kml><Document id="' + b"B" * M + b'"></Document></kml>', "nein"),
           ("2 MB «<»", b"<" * M, "nein"),
           ("2 MB «&amp;»", b"<kml><Document><name>" + b"&amp;" * (M // 5) + b"</name></Document></kml>", "nein"),
           ("GPX 40 000 Punkte", b'<gpx><trk><trkseg>' + b"".join(b'<trkpt lat="47.%05d" lon="8.%05d"><ele>500</ele></trkpt>' % (i, i) for i in range(40000)) + b"</trkseg></trk></gpx>", "ok"),
           ("GPX: 2 MB in lat", b'<gpx><trk><trkseg><trkpt lat="' + b"4" * M + b'" lon="8"/></trkseg></trk></gpx>', "nein"),
           ("kein XML (ZIP)", b"PK\x03\x04" + os.urandom(100000), "nein"),
           ("HTML", b"<html><body><script>alert(1)</script></body></html>", "nein"),
           ("UTF-16", "<kml><Document/></kml>".encode("utf-16"), "nein"),
           ("abgeschnitten", beispiel_kml(beispiel_punkte(500))[:-400], "nein")]
    return out


def lade(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_touren_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    return ns


def test_hoehe_datei(path):
    """a small height file: a tilted plane with a hill around Seon, 25 m grid, 12 × 10 km; the function it was made of"""
    import numpy as np
    import hoehe
    e0, n0, cols, rows, grid = 2650000.0, 1240000.0, 480, 400, 25.0
    f = lambda E, N: 400.0 + (E - e0) * 0.02 + (N - n0) * 0.03 + 300.0 * np.exp(-(((E - 2655000) / 1500.0) ** 2 + ((N - 1245000) / 1500.0) ** 2))
    E, N = np.meshgrid(e0 + np.arange(cols) * grid, n0 + np.arange(rows) * grid)
    h = f(E, N).astype("float32")
    h[:40, :60] = float("nan")                              # a corner without data (like outside the border)
    r = hoehe.schreibe(path, h, grid, e0, n0, 0.5, "Test")
    return f, r


# ---- A ---------------------------------------------------------------------------------------------------------------------------------
def teil_a(datei):
    from piper_test import Srv
    import hoehe
    home = tempfile.mkdtemp(prefix="mw_touren_home_")
    ns = lade(datei, home)
    logs = []
    ns["log_event"] = lambda *x, **k: logs.append(" ".join(str(v) for v in x))
    CFG = ns["CFG"]
    print("A) Touren im Prozess", flush=True)
    ok(bool(ns["kt_selftest"]()), "Selbsttest 639zzx")
    pts = beispiel_punkte()
    kml = beispiel_kml(pts)
    t0 = time.time(); p = ns["kt_parse"](kml, "Seon.kml"); dt = time.time() - t0
    ok(p["src"] == "kml" and len(p["pts"]) == 2204 and len(p["wps"]) == 8 and p["name"] == "Seon – Probetour" and not p["thinned"]
       and [w["name"] for w in p["wps"]][:2] == ["Startpunkt", "Wegpunkt"] and p["wps"][-1]["name"] == "Ziel",
       f"KML im Aufbau der swisstopo-App: 2204 Punkte, 8 Wegpunkte, Name, in {dt * 1000:.0f} ms")
    kurz = beispiel_punkte(20)
    n1 = ns["kt_parse"](beispiel_kml(kurz, ""), "Meine Wanderung.kml")["name"]
    n2 = ns["kt_parse"](beispiel_kml(kurz, ""), "")["name"]
    n3 = ns["kt_parse"](beispiel_kml(kurz, "").replace(b"Swisstopo Route", b"Rundweg Hallwilersee"), "x.kml")["name"]
    ok(p["name"] != "Swisstopo Route" and n1 == "Meine Wanderung" and re.fullmatch(r"Tour \d\d\.\d\d\.\d{4}", n2) and n3 == "Rundweg Hallwilersee",
       f"Name: Dokument (steht nach den Ordnern) vor «Swisstopo Route»; ohne: Dateiname «{n1}», sonst «{n2}»; eigener Spurname «{n3}»")
    gn = lambda meta, trk, f="": ns["kt_parse"](('<gpx>%s<trk>%s<trkseg><trkpt lat="47" lon="8"/><trkpt lat="47.01" lon="8"/></trkseg></trk></gpx>'
                                                 % ("<metadata><name>%s</name></metadata>" % meta if meta else "", "<name>%s</name>" % trk if trk else "")).encode(), f)["name"]
    ok(gn("Meta", "Spur") == "Meta" and gn("", "Spur") == "Spur" and gn("", "", "abc.gpx") == "abc" and ns["kt_parse"](
        b'<gpx><trk><name>Spur</name><trkseg><trkpt lat="47" lon="8"/><trkpt lat="47.01" lon="8"/></trkseg></trk><metadata><name>Meta</name></metadata></gpx>')["name"] == "Meta",
       "GPX-Name: metadata vor trk (auch wenn es danach steht), sonst Dateiname")
    s = ns["kt_stats"](p["pts"])
    dist = sum(hav(pts[i - 1], pts[i]) for i in range(1, len(pts)))
    up = sum(max(0.0, pts[i][2] - pts[i - 1][2]) for i in range(1, len(pts)))
    dn = sum(max(0.0, pts[i - 1][2] - pts[i][2]) for i in range(1, len(pts)))
    zeit = sum(ns["kt_hike_minutes"](hav(pts[i - 1], pts[i]), pts[i][2] - pts[i - 1][2]) for i in range(1, len(pts)))
    ok(abs(s["m"] - dist) < 1 and s["up"] == round(up) and s["down"] == round(dn) and not s["smooth"] and s["lo"] == round(min(x[2] for x in pts))
       and s["hi"] == round(max(x[2] for x in pts)), f"Zahlen wie eigene Rechnung: {s['m'] / 1000:.2f} km, +{s['up']} / −{s['down']} m, {s['lo']}–{s['hi']} m, roh (glatte Höhen)")
    ok(abs(s["min"] - zeit) <= 5 and s["min"] % 5 == 0 and len(s["profile"]) <= 260, f"Wanderzeit {s['min']} min (eigene Rechnung {zeit:.0f}), auf 5 min; Profil {len(s['profile'])} Punkte")
    g = ns["kt_parse"](beispiel_gpx(pts, 3.0), "spur.gpx")
    sg = ns["kt_stats"](g["pts"])
    roh = sum(max(0.0, g["pts"][i][2] - g["pts"][i - 1][2]) for i in range(1, len(g["pts"])))
    ok(g["src"] == "gpx" and len(g["pts"]) == 2204 and g["wps"][0]["name"] == "Hütte <b>" and sg["smooth"] and abs(sg["up"] - up) < 0.12 * up and roh > 2 * up,
       f"GPX mit ±3 m Rauschen: geglättet +{sg['up']} m (wahr +{up:.0f}, roh wären +{roh:.0f})")
    ruhig = ns["kt_stats"](ns["kt_parse"](beispiel_gpx(pts, 0.0))["pts"])
    ok(not ruhig["smooth"] and ruhig["up"] == round(up), "GPX mit glatten Höhen: nicht geglättet")
    ohne = ns["kt_parse"](b'<gpx><rte><name>R</name><rtept lat="47" lon="8"/><rtept lat="47.01" lon="8"/></rte></gpx>')
    so = ns["kt_stats"](ohne["pts"])
    ok(ohne["name"] == "R" and not so["ele"] and "up" not in so and so["min"] == 15, "GPX-Route ohne Höhen: keine Höhenzahlen (nicht 0), Zeit der Ebene")
    gx = ns["kt_parse"](b'<kml xmlns:gx="http://www.google.com/kml/ext/2.2"><Document><Placemark><name>T</name><gx:Track><gx:coord>8.1 47 500</gx:coord><gx:coord>8.2 47 600</gx:coord></gx:Track></Placemark></Document></kml>')
    ok(len(gx["pts"]) == 2 and gx["pts"][1] == (47.0, 8.2, 600.0), "KML mit gx:Track")
    print("   Härtung: böse und grosse Dateien", flush=True)
    langsam = 0.0
    for name, data, soll in boese_dateien():
        t0 = time.time()
        try:
            r = ns["kt_parse"](data, "x.kml"); res = "ok"
            st = ns["kt_stats"](r["pts"]); ns["kt_clean"]({"name": r["name"], "pts": r["pts"], "wps": r["wps"]}, "0" * 12)
        except ns["KTError"] as e:
            res, r = "nein", str(e)
        dt = time.time() - t0
        langsam = max(langsam, dt)
        extra = ""
        if res == "ok":
            extra = f", {len(r['pts'])} Punkte" + (", ausgedünnt" if r["thinned"] else "") + f", Name {len(r['name'])} Zeichen"
            ok(len(r["pts"]) <= ns["KT_MAX_PTS"] + 1 and len(r["name"]) <= 120, f"{name}: Grenzen eingehalten")
        ok(dt < ZEIT_MAX and (soll == "egal" or res == soll), f"{name} ({len(data) / 1e6:.1f} MB): {'angenommen' if res == 'ok' else 'abgelehnt'} in {dt * 1000:.0f} ms{extra}")
    ok(langsam < ZEIT_MAX, f"langsamste Datei {langsam:.2f} s (Grenze {ZEIT_MAX:.0f} s)")
    try:
        ns["kt_parse"](b"x" * (ns["KT_IMPORT_MAX"] + 1)); ok(False, "zu grosse Datei abgelehnt")
    except ns["KTError"]:
        ok(True, "zu grosse Datei abgelehnt (vor dem Lesen)")

    # ---- web: rights, import, drawing, export, guests
    CFG.update(https_extra=False, lang="de", tausch_free_gb=0.02, tausch_on=True, tausch_guest=True)
    PW = "Admin-Tour-123"
    assert ns["web_pw_set"](PW)[0]
    for nm, pw, role in (("Anna", "anna-pass-1", "family"), ("Ben", "ben-pass-12", "family"), ("Kim", "kim-pass-12", "kid")):
        okk, err = ns["users_action"]({"action": "add", "name": nm, "password": pw, "role": role}); assert okk, err
    ws = ns["WebStream"](None); ws._serve = lambda app, ctx: None; ws.start()
    c = ws.app.test_client(use_cookies=False)
    hd = lambda u, p: {"Authorization": "Basic " + base64.b64encode(f"{u}:{p}".encode()).decode()}
    H, HA, HB, HK = hd("admin", PW), hd("Anna", "anna-pass-1"), hd("Ben", "ben-pass-12"), hd("Kim", "kim-pass-12")
    api = lambda d, h: (lambda r: (r.status_code, r.get_json(silent=True) or {}))(c.post("/api/touren", json=d, headers=h))
    lst = lambda h: (lambda r: (r.status_code, r.get_json(silent=True) or {}))(c.get("/api/touren", headers=h))
    imp = lambda data, h, name="t.kml": (lambda r: (r.status_code, r.get_json(silent=True) or {}))(
        c.post("/api/touren/import?name=" + urllib.request.quote(name), data=data, headers=dict(h, **{"Content-Type": "application/octet-stream"})))
    ok(lst(HK)[0] == 403 and imp(kml, HK)[0] == 403 and api({"action": "save", "name": "x", "pts": [[47, 8], [47.1, 8]]}, HK)[0] == 403, "Kind (ohne Datei-Rechte): sieht und ändert nichts")
    code, j = lst(HA)
    ok(code == 200 and j["tours"] == [] and j["me"]["edit"] and not j["me"]["admin"] and not j["hoehe"]["pinned"], "Familie: leere Liste, darf bearbeiten; Höhenpaket «kommt mit einem Update»")
    code, j = imp(kml, HA, "Seon – Probe.kml")
    T1 = (j.get("tour") or {}).get("id", "")
    ok(code == 200 and j["tour"]["name"] == "Seon – Probetour" and j["tour"]["kind"] == "import" and j["tour"]["up"] == round(up) and len(j["tour"]["line"]) <= 1500
       and len(j["tour"]["points"]) == 8 and len(j["tour"]["profile"]) > 100 and j["tour"]["pts"] is None,
       f"Import über die Schnittstelle: Zahlen, Linie {len(j.get('tour', {}).get('line', []))} Punkte für die Karte, 8 Wegpunkte, Profil")
    code, j = imp(b'<kml><Document><name>&lt;script&gt;alert(1)&lt;/script&gt; "x" \'y\'</name><Placemark><name>&lt;img src=x onerror=alert(2)&gt;</name><Point><coordinates>8,47,1</coordinates></Point></Placemark>'
                  b"<Placemark><LineString><coordinates>8,47,400 8.01,47,420</coordinates></LineString></Placemark></Document></kml>", HA)
    T2 = j["tour"]["id"]
    ok(code == 200 and j["tour"]["name"] == "<script>alert(1)</script> \"x\" 'y'", "Name mit Spitzklammern bleibt Text (wird nirgends HTML)")
    ok(imp(b"<html>x</html>", HA)[0] == 400 and imp(b"x" * (ns["KT_IMPORT_MAX"] + 5), HA)[0] == 413, "kein KML / GPX: 400 mit Meldung; zu gross: 413")
    code, j = api({"action": "save", "name": "Runde am See", "pts": [[47.29, 8.20], [47.30, 8.21], [47.31, 8.20]]}, HB)
    T3 = j["tour"]["id"]
    ok(code == 200 and j["tour"]["kind"] == "drawn" and j["tour"]["pts"] and not j["tour"]["ele"] and j["tour"]["need"] and j["tour"].get("up") is None and 2300 < j["tour"]["m"] < 2900,
       f"gezeichnete Route gespeichert: {j['tour']['m']:.0f} m, ohne Höhenpaket keine Höhenzahlen (Hinweis statt 0)")
    code, j = api({"action": "save", "id": T3, "name": "Runde am See 2", "pts": [[47.29, 8.20], [47.30, 8.21], [47.31, 8.20], [47.32, 8.21]]}, HA)
    ok(code == 200 and j["tour"]["name"] == "Runde am See 2" and len(j["tour"]["pts"]) == 4, "ein anderer Benutzer mit «hochladen» ändert die gemeinsame Route")
    ok(api({"action": "save", "id": T1, "name": "x", "pts": [[47, 8], [47.1, 8]]}, HA)[0] == 404, "eine importierte Tour wird nicht überzeichnet")
    ok(api({"action": "save", "name": "x", "pts": [[47, 8]]}, HA)[0] == 400 and api({"action": "save", "name": "x", "pts": [[47, 8]] * 501}, HA)[0] == 400, "ein Punkt / 501 Punkte: abgelehnt")
    ok(api({"action": "rename", "id": T1, "name": "  Seon   neu\x00 "}, HB)[1].get("tour", {}).get("name") == "Seon neu" and api({"action": "rename", "id": T1, "name": ""}, HB)[0] == 400, "Umbenennen (bereinigt), leer abgelehnt")
    ok(api({"action": "delete", "id": T1}, HB)[0] == 403 and api({"action": "area", "id": T1, "area": "mine"}, HB)[0] == 403, "löschen / «Nur ich» darf nur, wer die Tour angelegt hat (oder der Admin)")
    ok(api({"action": "area", "id": T2, "area": "mine"}, HA)[0] == 200 and T2 not in [x["id"] for x in lst(HB)[1]["tours"]] and T2 in [x["id"] for x in lst(H)[1]["tours"]]
       and c.get("/api/touren?id=" + T2, headers=HB).status_code == 404, "«Nur ich»: andere sehen sie nicht mehr, der Admin schon")
    r = c.get(f"/touren/x/{T1}.kml", headers=HA); r2 = c.get(f"/touren/x/{T1}.gpx", headers=HA)
    back, back2 = ns["kt_parse"](r.data), ns["kt_parse"](r2.data)
    ok(r.status_code == 200 and "attachment" in r.headers.get("Content-Disposition", "") and len(back["pts"]) == 2204 and len(back["wps"]) == 8 and back["name"] == "Seon neu"
       and len(back2["pts"]) == 2204 and back2["pts"][100] == back["pts"][100] and b"<Folder><name>Tracks</name>" in r.data, "Export KML (Ordner Waypoints / Tracks) und GPX: wieder lesbar, alle Punkte und Höhen")
    r = c.get(f"/touren/x/{T2}.gpx", headers=HA)
    ok(b"&lt;script&gt;" in r.data and b"<script>" not in r.data and b"&lt;img src=x" in r.data, "Export: Namen als XML-Text")
    ok(c.get(f"/touren/x/{T2}.gpx", headers=HB).status_code == 404 and c.get(f"/touren/x/{T1}.gpx", headers=HK).status_code == 403 and c.get("/touren/x/../settings.json", headers=HA).status_code == 404,
       "Export: fremde «Nur ich»-Tour 404, Kind 403, kein Pfad nach aussen")
    r = c.get("/touren/x/alle.zip", headers=HB)
    zn = zipfile.ZipFile(__import__("io").BytesIO(r.data)).namelist()
    ok(r.status_code == 200 and len(zn) == 2 and all(n.endswith(".gpx") for n in zn), f"Alle Touren als ZIP: {zn}")
    # 3.85.0: ein ZIP hat eine Grenze (sonst stünden 300 lange Aufzeichnungen zugleich im Speicher), die neuesten sind sicher drin
    gr = ns["KT_ZIP_RAW"]; ns["KT_ZIP_RAW"] = 10
    try:
        zn = zipfile.ZipFile(__import__("io").BytesIO(c.get("/touren/x/alle.zip", headers=HB).data)).namelist()
    finally:
        ns["KT_ZIP_RAW"] = gr
    ok(len(zn) == 2 and sum(n.endswith(".gpx") for n in zn) == 1 and "NICHT_ALLE.txt" in zn, f"ZIP über der Grenze: die neueste Tour und ein Hinweis {zn}")
    # 3.85.0: mitnehmen (GPX / KML / ZIP) braucht das Recht «herunterladen» – ausser bei der eigenen Tour (wie im Datentausch)
    wer0 = ns["tausch_who"]
    ns["tausch_who"] = lambda g_: (lambda w: dict(w, perms=w["perms"] - {"files_down"}) if not w["is_admin"] else w)(wer0(g_))
    try:
        ok(c.get(f"/touren/x/{T1}.gpx", headers=HB).status_code == 403 and c.get("/touren/x/alle.zip", headers=HB).status_code == 403
           and c.get(f"/touren/x/{T3}.gpx", headers=HB).status_code == 200 and c.get("/api/touren?id=" + T1, headers=HB).status_code == 200,
           "ohne «herunterladen»: fremde Tour und ZIP 403, die eigene Tour geht, ansehen geht")
    finally:
        ns["tausch_who"] = wer0
    c.post("/api/guest", json={"action": "create", "hours": 2}, headers=H); tok = (c.get("/api/guest", headers=H).get_json() or {}).get("path", "")
    tok = tok.strip("/").split("/")[-1]
    r = c.get(f"/g/{tok}/touren"); tx = r.get_data(as_text=True)
    ok(r.status_code == 200 and "Seon neu" in tx and "Runde am See 2" in tx and "alert(1)" not in tx and "<script" not in tx and "Anna" not in tx and "Ben" not in tx,
       "Gast: Liste der gemeinsamen Touren, ohne «Nur ich», ohne Benutzernamen, ohne Skript")
    r = c.get(f"/g/{tok}/touren?t={T1}"); tx = r.get_data(as_text=True)
    ok(r.status_code == 200 and tx.count("<svg") == 2 and "Startpunkt" in tx and "km" in tx and "default-src 'none'" in r.headers.get("Content-Security-Policy", "") and "‹" in tx,
       "Gast: eine Tour mit Skizze, Profil, Wegpunkten, Weg zurück; CSP ohne Skript")
    ok(c.get(f"/g/{tok}/touren?t={T2}").status_code == 404 and c.get("/g/falsch/touren").status_code == 404 and c.post("/api/touren", json={"action": "delete", "id": T1}).status_code in (401, 403),
       "Gast: «Nur ich» 404, falscher Link 404, ändern geht nicht")
    api({"action": "area", "id": T2, "area": "all"}, HA)
    tx = c.get(f"/g/{tok}/touren?t={T2}").get_data(as_text=True)
    ok("&lt;script&gt;alert(1)&lt;/script&gt;" in tx and "&lt;img src=x" in tx and "<img" not in tx, "Gast-Seite: Namen aus der Datei als Text")
    ok("🥾" in c.get(f"/g/{tok}/tausch").get_data(as_text=True), "Gast-Seite des Datentausches: Link «🥾 Touren»")
    CFG["tausch_guest"] = False
    ok(c.get(f"/g/{tok}/touren").status_code == 404, "Schalter tausch_guest aus: keine Gast-Seite")
    CFG["tausch_guest"] = True
    r = c.get("/more", headers=HA).get_data(as_text=True)
    ok('href="/karte" id="m-karte"' in r and "🗺" in r, "«Mehr»: Kachel «🗺 Karte»")
    r = c.get("/karte", headers=HA).get_data(as_text=True)
    ok(r.count('id="kt"') == 1 and "window.KT = " in r and '"Route zeichnen"' in r and '"Dessiner un itinéraire"' in r and '"Dissegnar ina ruta"' in r, "/karte: Kasten «Touren» mit Texten in den Sprachen")
    koord = re.compile(r"\b4[5-7]\.\d{3,}|\b[5-9]\.\d{4,}|\b10\.\d{4,}")
    ok(logs and not any(koord.search(x) for x in logs), f"Protokoll ({len(logs)} Zeilen): keine Koordinate")
    ok(api({"action": "delete", "id": T2}, HA)[0] == 200 and not os.path.exists(os.path.join(home, "touren", T2 + ".json")) and api({"action": "delete", "id": T1}, H)[0] == 200, "löschen: der Besitzer und der Admin")
    ok(sorted(os.listdir(os.path.join(home, "touren"))) == [T3 + ".json"] and json.load(open(os.path.join(home, "touren", T3 + ".json")))["name"] == "Runde am See 2", "Speicher: DATA_DIR/touren/<Nummer>.json, lesbar")

    # ---- the height package (a small stand-in file)
    print("   Höhenpaket (Ersatz-Datei)", flush=True)
    rel = tempfile.mkdtemp(prefix="mw_touren_rel_")
    hp = os.path.join(rel, "hoehe-ch-1.bin")
    f, info = test_hoehe_datei(hp)
    data = open(hp, "rb").read()
    srv = Srv(); srv.files["/hoehen-1/hoehe-ch-1.bin"] = data
    ns["KH_BASE"]["url"] = srv.url + "hoehen-1/"
    ns["KH_FILE"].update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    ns["KH_RT"]["ok_t"] = 0
    DL = ns["KH_DL"]

    def warten():
        t0 = time.time()
        while DL["running"] and time.time() - t0 < 120:
            time.sleep(0.05)
        ns["KH_RT"]["ok_t"] = 0
    code, j = lst(HA)
    ok(j["hoehe"]["pinned"] and not j["hoehe"]["on"] and j["hoehe"]["size"] == len(data), f"Zustand: gepinnt ({len(data) / 1e3:.0f} KB), nicht installiert")
    ok(api({"action": "hoehe_install"}, HA)[0] == 403 and api({"action": "hoehe_delete"}, HA)[0] == 403 and not DL["running"], "Familie darf das Höhenpaket nicht laden / entfernen")
    CFG["tausch_free_gb"] = 1e6
    code, j = api({"action": "hoehe_install"}, H)
    ok(code == 400 and "Platz" in str(j.get("error")) and not srv.hits, f"zu wenig Platz: abgelehnt, nichts geladen ({j.get('error')})")
    CFG["tausch_free_gb"] = 0.02
    srv.tamper.add("/hoehen-1/hoehe-ch-1.bin")
    api({"action": "hoehe_install"}, H); warten()
    ok(not ns["kh_installed"]() and "checksum" in DL["msg"] and not os.path.exists(ns["kh_path"]()), f"veränderte Datei abgelehnt ({DL['msg']})")
    srv.tamper.discard("/hoehen-1/hoehe-ch-1.bin")
    api({"action": "hoehe_install"}, H); warten()
    ok(ns["kh_installed"]() and DL["done"] and not DL["msg"], "geladen, geprüft, eingeschaltet")
    K = ns["kh_file"]()
    import numpy as np
    rnd = random.Random(3); worst = 0.0
    for _ in range(300):
        E, N = 2651600 + rnd.random() * 9000, 1241100 + rnd.random() * 8000
        la, lo = 47.30 + (N - 1241100) / 111200.0, 8.10 + (E - 2651600) / 75500.0
        e2, n2 = ns["kh_lv95"](la, lo)
        v = K.height(la, lo)
        if v is not None:
            worst = max(worst, abs(v - float(f(e2, n2))))
    ok(worst < 1.0 and K.reads < len(data), f"300 Höhen gegen die Vorlage: grösste Abweichung {worst:.2f} m (0,5-m-Stufen, 25 m Gitter)")
    ok(ns["kh_height"](46.0, 7.0) is None and ns["kh_height"](47.5, 9.9) is None, "ausserhalb der Datei: keine Höhe (None, nie 0)")
    ecke = [(la / 2000.0, lo / 2000.0) for la in range(94500, 94700, 4) for lo in range(16100, 16300, 4)]
    ecke = [q for q in ecke if 2650200 < ns["kh_lv95"](*q)[0] < 2651200 and 1240200 < ns["kh_lv95"](*q)[1] < 1240800]
    ok(len(ecke) > 3 and all(K.height(*q) is None for q in ecke), f"in der Ecke ohne Daten ({len(ecke)} Stellen): keine Höhe")
    code, j = c.get("/api/touren?id=" + T3, headers=HA).status_code, c.get("/api/touren?id=" + T3, headers=HA).get_json()
    ok(code == 200 and (j["tour"]["nodata"] or j["tour"]["ele"]), "gespeicherte Route rechnet neu, sobald das Paket da ist")
    A, B = (47.345, 8.175), (47.375, 8.215)
    code, j = api({"action": "save", "name": "Über den Hügel", "pts": [list(A), list(B)]}, HA)
    t = j["tour"]
    ea, eb = float(f(*ns["kh_lv95"](*A))), float(f(*ns["kh_lv95"](*B)))
    prof = [float(f(*ns["kh_lv95"](A[0] + (B[0] - A[0]) * k / 400.0, A[1] + (B[1] - A[1]) * k / 400.0))) for k in range(401)]
    wahr_up = sum(max(0.0, prof[i] - prof[i - 1]) for i in range(1, 401)); wahr_dn = sum(max(0.0, prof[i - 1] - prof[i]) for i in range(1, 401))
    ok(code == 200 and t["ele"] and t["smooth"] and abs(t["up"] - wahr_up) <= 6 and abs(t["down"] - wahr_dn) <= 6 and len(t["profile"]) > 50 and t["min"] > 0,
       f"gezeichnete Route mit Höhen aus dem Paket: +{t['up']} / −{t['down']} m (Vorlage +{wahr_up:.0f} / −{wahr_dn:.0f}), als «geglättet» gemeldet, Profil, {t['min']} min")
    r = ns["kt_parse"](c.get(f"/touren/x/{t['id']}.gpx", headers=HA).data)
    ok(r["pts"][0][2] is not None and abs(r["pts"][0][2] - ea) < 1.5 and abs(r["pts"][1][2] - eb) < 1.5, "Export einer gezeichneten Route: mit den Höhen aus dem Paket")
    code, j = api({"action": "save", "name": "Hinaus", "pts": [list(A), [47.345, 8.60]]}, HA)
    ok(code == 200 and not j["tour"]["ele"] and j["tour"]["nodata"] and j["tour"].get("up") is None and j["tour"]["m"] > 30000, "Route über den Rand der Daten: «keine Höhendaten», keine 0")
    r = c.post("/api/touren/profil", json={"pts": [list(A), list(B)]}, headers=HA).get_json()
    ok(r["ok"] and r["ele"] and r["up"] == t["up"] and c.post("/api/touren/profil", json={"pts": [list(A), list(B)]}, headers=HK).status_code == 403, "Zahlen beim Zeichnen (/api/touren/profil); Kind 403")
    tx = c.get(f"/g/{tok}/touren?t={j['tour']['id']}").get_data(as_text=True)
    ok("Keine Höhendaten" in tx and "↑" not in tx, "Gast-Seite: «Keine Höhendaten» statt Zahlen")
    ok(api({"action": "hoehe_delete"}, H)[0] == 200 and not ns["kh_installed"]() and not os.path.exists(os.path.dirname(ns["kh_path"]())), "Entfernen löscht das Paket")
    ok(c.get("/api/touren?id=" + t["id"], headers=HA).get_json()["tour"]["need"], "danach: wieder der Hinweis auf das Paket")
    shutil.rmtree(home, ignore_errors=True); shutil.rmtree(rel, ignore_errors=True)


# ---- B: the page in the browser ----------------------------------------------------------------------------------------------------------
def teil_b(datei, web, bilder, tour=""):
    from playwright.sync_api import sync_playwright
    from piper_test import Srv
    import karten_test as KA
    print("B) im Browser (390 px und PC)", flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_touren_b_")
    P, rel, pins, tiles = KA.dateien_bauen(tmp, web)
    hp = os.path.join(rel, "hoehe-ch-1.bin")
    test_hoehe_datei(hp)
    hdata = open(hp, "rb").read()
    srv = Srv()
    for r_, f in pins.items():
        srv.files["/karten-1/" + f["name"]] = open(os.path.join(rel, f["name"]), "rb").read()
    srv.files["/hoehen-1/hoehe-ch-1.bin"] = hdata
    d2 = KA.gepatcht(datei, tmp, pins, srv.url + "karten-1/")
    src = open(d2, encoding="utf-8").read()
    alt = '"https://github.com/DonElektro/MotionWatch/releases/download/" + KH_TAG + "/"'
    src, n1 = re.subn(r'^KH_FILE = \{"name": "[^"]*", "size": \d+, "sha256": "[0-9a-f]*"\}', 'KH_FILE = {"name": "hoehe-ch-1.bin", "size": %d, "sha256": "%s"}' % (len(hdata), hashlib.sha256(hdata).hexdigest()), src, flags=re.M)
    assert n1 == 1 and src.count(alt) == 1
    open(d2, "w", encoding="utf-8").write(src.replace(alt, json.dumps(srv.url + "hoehen-1/"), 1))
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    PW = "Tour-" + os.urandom(4).hex()
    p, cfg = KA.starte(d2, tmp, port, PW)
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user=("admin", PW), raw=None):
        hd = {"Authorization": "Basic " + base64.b64encode(f"{user[0]}:{user[1]}".encode()).decode(), "Content-Type": "application/json" if raw is None else "application/octet-stream", "Origin": base}
        r = urllib.request.Request(base + path, data=raw if raw is not None else (json.dumps(data).encode() if data is not None else None), headers=hd)
        try:
            with op.open(r, timeout=120) as x:
                return x.status, json.loads(x.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, {}
    kmlf = os.path.join(tmp, "Seon_Probetour.kml")
    open(kmlf, "wb").write(open(tour, "rb").read() if tour else beispiel_kml(beispiel_punkte()))
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt")).read()[-3000:])
            try:
                if req("/api/karte")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        req("/api/users", {"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
        req("/api/karte", {"action": "install"})
        for _i in range(240):
            if req("/api/karte")[1].get("on"):
                break
            time.sleep(0.5)
        ok(req("/api/karte")[1].get("on"), "Testkarte installiert")
        os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=KA.ARGS)
            aussen = []

            def kontext(mob, user=("Anna", "anna-pass-1")):
                vp = {"width": 390, "height": 844} if mob else {"width": 1366, "height": 900}
                ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, http_credentials={"username": user[0], "password": user[1]}, locale="de-CH")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');localStorage.setItem('mw-lv-knoepfe','1');"
                                    "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\",\"settings\",\"rec\",\"history\",\"sim\",\"protect\",\"zones\",\"cams\",\"place\",\"tools\"]')}catch(e){}")
                ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:")) else (aussen.append(r.request.url[:120]), r.abort()))
                return ctx
            breit = "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
            for name, mob in (("390", True), ("pc", False)):
                ctx = kontext(mob); pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                tap = (lambda sel: pg.tap(sel)) if mob else (lambda sel: pg.click(sel))
                pg.goto(base + "/more"); pg.wait_for_selector("#m-karte", timeout=20000)
                ok(pg.locator("#m-karte").is_visible() and "Karte" in pg.inner_text("#m-karte"), f"{name}: «Mehr» zeigt die Kachel «🗺 Karte»")
                if mob and not tour:
                    pg.locator("#m-karte").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(bilder, "mehr_kachel_390.png"))
                tap("#m-karte"); pg.wait_for_url("**/karte", timeout=15000)
                pg.wait_for_function("() => window.KQMAP && KQMAP.loaded()", timeout=60000)
                pg.wait_for_selector("#kt:not([hidden]) #kt-new", timeout=15000)
                ok(pg.inner_text("#kt-h") == "Touren" and pg.locator("#kt-imp").is_visible() and pg.evaluate(breit), f"{name}: /karte mit dem Kasten «Touren», nichts ragt hinaus")
                ok(pg.evaluate("() => { const f = document.getElementById('kt-file'); return f.type === 'file' && !f.accept; }"), f"{name}: Datei-Knopf ohne «accept» (iPhone «Dateien» zeigt jede Endung)")
                if name == "390" or not tour:
                    for old in req("/api/touren", user=("Anna", "anna-pass-1"))[1].get("tours", []):
                        req("/api/touren", {"action": "delete", "id": old["id"]})
                pg.locator("#kt-imp").scroll_into_view_if_needed()
                with pg.expect_file_chooser() as fc:
                    tap("#kt-imp")
                fc.value.set_files(kmlf)
                pg.wait_for_selector("#kt-detail:not([hidden]) #kt-name", timeout=30000)
                pg.wait_for_function("() => KQMAP.getSource('kt') && KQMAP.querySourceFeatures('kt').length >= 0 && document.querySelectorAll('.kt-wp').length >= 2", timeout=30000)
                pg.wait_for_function("() => KQMAP.loaded()", timeout=30000); pg.wait_for_timeout(700)
                txt = pg.inner_text("#kt-detail")
                ok(all(w in txt for w in ("Distanz", "Aufstieg", "Abstieg", "Wanderzeit", "km", "↑", "↓")) and pg.locator("#kt-detail svg.kt-prof").is_visible(), f"{name}: Tour importiert: Zahlen und Höhenprofil")
                ok(pg.locator("#kt-back").is_visible() and pg.evaluate(breit), f"{name}: sichtbarer Weg zurück («‹ Touren»), nichts ragt hinaus")
                frei = pg.evaluate("() => { const h = document.querySelector('header').getBoundingClientRect(), b = document.getElementById('kt-back').getBoundingClientRect(), n = document.getElementById('kt-name').getBoundingClientRect(); return [Math.round(h.bottom), Math.round(b.top), Math.round(n.top), Math.round(n.bottom), innerHeight]; }")
                ok(frei[1] >= frei[0] and frei[2] >= frei[0] and frei[3] <= frei[4], f"{name}: beim Öffnen stehen «‹ Touren» und der Titel frei unter dem festen Kopf (Kopf bis {frei[0]}, Titel ab {frei[2]})")
                pg.screenshot(path=os.path.join(bilder, f"tour_offen_{name}.png"))
                if not tour:
                    ok("Seon – Probetour" in pg.inner_text("#kt-name") and "+535" not in txt and pg.locator(".kt-wp").count() == 8, f"{name}: Name aus der Datei, 8 Wegpunkte auf der Karte")
                    ok("geglättet" not in txt, f"{name}: glatte Höhen aus der Datei: nicht «geglättet»")
                ln = pg.evaluate("() => { const d = KQMAP.getSource('kt').serialize().data; return d.features.length ? d.features[0].geometry.coordinates.length : 0; }")
                ok(2 <= ln <= 1501, f"{name}: Linie auf der Karte ({ln} Punkte)")
                pg.locator("#kq-map").scroll_into_view_if_needed(); pg.wait_for_timeout(400)
                pg.screenshot(path=os.path.join(bilder, f"tour_karte_{name}.png"))
                pg.locator("#kt-detail").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(bilder, f"tour_zahlen_{name}.png"))
                pg.locator("#kt-detail svg.kt-prof").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(bilder, f"tour_profil_{name}.png"))
                ok(pg.get_attribute("#kt-x-gpx", "href").endswith(".gpx") and pg.get_attribute("#kt-x-kml", "href").endswith(".kml"), f"{name}: Export GPX und KML")
                if not tour:
                    tap("#kt-ren"); pg.fill("#kt-rn", "Seon <b>fett</b> & Co"); tap("#kt-detail .kt-row button:not(.sec)")
                    pg.wait_for_function("() => { const n = document.getElementById('kt-name'); return n && n.textContent === 'Seon <b>fett</b> & Co'; }", timeout=10000)
                    ok(pg.evaluate("() => !document.querySelector('#kt-name b')"), f"{name}: umbenannt; der Name ist Text, kein HTML")
                    # delete with the question inside the page
                    dial = []
                    pg.on("dialog", lambda d: (dial.append(d.message), d.dismiss()))
                    tap("#kt-del"); pg.wait_for_selector("#kt-delq", timeout=5000)
                    ok("Wirklich löschen?" in pg.inner_text("#kt-delq") and not dial, f"{name}: Löschen fragt in der Seite nach (kein confirm())")
                    pg.screenshot(path=os.path.join(bilder, f"tour_loeschen_{name}.png"))
                    tap("#kt-delq button.sec"); pg.wait_for_selector("#kt-del", timeout=5000)
                    ok(len(req("/api/touren", user=("Anna", "anna-pass-1"))[1]["tours"]) >= 1, f"{name}: «Nein» löscht nicht")
                    tap("#kt-del"); pg.wait_for_selector("#kt-delq"); tap("#kt-delq button.red")
                    pg.wait_for_selector("#kt-list:not([hidden])", timeout=10000)
                    pg.wait_for_function("() => !document.querySelector('.kt-li')", timeout=10000)
                    ok(req("/api/touren", user=("Anna", "anna-pass-1"))[1]["tours"] == [], f"{name}: «Ja, löschen» löscht; zurück in der Liste")
                    # drawing
                    tap("#kt-new"); pg.wait_for_selector("#kt-bar #kt-dname", timeout=10000)
                    ok(pg.locator("#kt-dback").is_visible() and pg.locator("#kt-undo").is_disabled(), f"{name}: Zeichnen: Weg zurück sichtbar, «Rückgängig» noch aus")
                    pg.evaluate("() => KQMAP.jumpTo({center: [8.1602, 47.3475], zoom: 13})"); pg.wait_for_function("() => KQMAP.loaded()", timeout=30000)
                    pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'end'})"); pg.wait_for_timeout(300)
                    bx = pg.locator("#kq-c").bounding_box()
                    ok(pg.evaluate("() => { const b = document.getElementById('kt-save').getBoundingClientRect(), m = document.getElementById('kq-map').getBoundingClientRect(); return b.bottom <= m.top + 1 && m.top - b.bottom < 160; }"),
                       f"{name}: Knöpfe (Rückgängig, Speichern) stehen direkt über der Karte")
                    P4 = [(0.25, 0.55), (0.5, 0.65), (0.7, 0.55), (0.75, 0.85)]
                    for fx, fy in P4:
                        (pg.touchscreen.tap if mob else pg.mouse.click)(bx["x"] + bx["width"] * fx, bx["y"] + bx["height"] * fy); pg.wait_for_timeout(250)
                    ok(pg.locator(".kt-pt").count() == 4 and pg.evaluate("() => !document.querySelector('#kq-btns') || document.querySelector('#kq-btns').hidden"), f"{name}: 4 Punkte gesetzt (der Tipp wählt dabei keinen Standort)")
                    pg.wait_for_function("() => document.querySelector('#kt-dinfo .kt-nums') && /km/.test(document.getElementById('kt-dinfo').innerText)", timeout=10000)
                    tap("#kt-undo"); pg.wait_for_function("() => document.querySelectorAll('.kt-pt').length === 3", timeout=5000)
                    pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'end'})"); pg.wait_for_timeout(300)
                    bx = pg.locator("#kq-c").bounding_box()
                    (pg.touchscreen.tap if mob else pg.mouse.click)(bx["x"] + bx["width"] * 0.75, bx["y"] + bx["height"] * 0.85); pg.wait_for_function("() => document.querySelectorAll('.kt-pt').length === 4", timeout=5000)
                    pg.locator(".kt-pt").nth(1).dispatch_event("click"); pg.wait_for_selector(".kt-pt.sel", timeout=5000)
                    tap("#kt-delpt"); pg.wait_for_function("() => document.querySelectorAll('.kt-pt').length === 3", timeout=5000)
                    ok(True, f"{name}: «Rückgängig», Punkt antippen + «Punkt löschen»")
                    if not mob:                             # drag a point
                        b0 = pg.locator(".kt-pt").nth(2).bounding_box(); d0 = pg.inner_text("#kt-dinfo")
                        pg.mouse.move(b0["x"] + 9, b0["y"] + 9); pg.mouse.down(); pg.mouse.move(b0["x"] + 60, b0["y"] + 90, steps=8); pg.mouse.up(); pg.wait_for_timeout(500)
                        b1 = pg.locator(".kt-pt").nth(2).bounding_box()
                        ok(abs(b1["x"] - b0["x"]) > 30 and pg.locator(".kt-pt").count() == 3, "pc: Punkt ziehen verschiebt ihn (kein neuer Punkt)")
                    tap("#kt-save"); pg.wait_for_timeout(300)
                    ok("Namen" in pg.inner_text("#kt-bar"), f"{name}: ohne Namen wird nicht gespeichert (Meldung in der Seite)")
                    pg.fill("#kt-dname", f"Gezeichnet {name}")
                    pg.wait_for_function("() => /Höhendaten/.test(document.getElementById('kt-dinfo').innerText)", timeout=10000)
                    pg.screenshot(path=os.path.join(bilder, f"zeichnen_{name}.png"))
                    tap("#kt-save"); pg.wait_for_selector("#kt-detail:not([hidden]) #kt-name", timeout=15000)
                    txt = pg.inner_text("#kt-detail")
                    ok(f"Gezeichnet {name}" in txt and "brauchen die Höhendaten Schweiz" in txt and "↑" not in txt, f"{name}: Route gespeichert; ohne Höhenpaket der Hinweis statt Zahlen")
                    ok(not errs, f"{name}: keine JS-Fehler" + (": " + " | ".join(errs[:3]) if errs else ""))
                ctx.close()
            if not tour:
                # the administrator loads the height data through the page; the drawn routes get their numbers
                ctx = kontext(True, ("admin", PW)); pg = ctx.new_page()
                pg.goto(base + "/karte"); pg.wait_for_selector("#kt-hget", timeout=30000)
                ok("Höhendaten Schweiz herunterladen" in pg.inner_text("#kt-hget") and "© swisstopo" in pg.inner_text("#kt-hbox"), "Admin: Knopf «Höhendaten Schweiz herunterladen (… MB)», Quelle © swisstopo")
                pg.locator("#kt-hbox").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(bilder, "hoehendaten_laden_390.png"))
                pg.tap("#kt-hget"); pg.wait_for_timeout(200)
                ok("Wirklich laden" in pg.inner_text("#kt-hget"), "Admin: zweiter Tipp bestätigt (kein confirm())")
                pg.tap("#kt-hget")
                for _i in range(120):
                    if req("/api/touren")[1].get("hoehe", {}).get("on"):
                        break
                    time.sleep(0.5)
                ok(req("/api/touren")[1]["hoehe"]["on"], "Höhenpaket über die Seite geladen")
                pg.wait_for_selector("#kt-hdel", timeout=15000)
                pg.tap(".kt-li"); pg.wait_for_selector("#kt-detail:not([hidden]) svg.kt-prof", timeout=15000)
                txt = pg.inner_text("#kt-detail")
                ok("↑" in txt and "geglättet" in txt and "Wanderzeit" in txt, "gezeichnete Route jetzt mit Auf- / Abstieg, Profil, Zeit – als «geglättet» beschriftet")
                pg.locator("#kt-detail").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(bilder, "gezeichnet_mit_hoehen_390.png"))
                ctx.close()
                # the guest page
                req("/api/guest", {"action": "create", "hours": 2}); tok = req("/api/guest")[1].get("path", "").strip("/").split("/")[-1]
                ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2, locale="de-CH")
                ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) else (aussen.append(r.request.url[:120]), r.abort()))
                pg = ctx.new_page(); pg.goto(f"{base}/g/{tok}/touren"); pg.wait_for_selector("a.li", timeout=15000)
                ok(pg.evaluate(breit) and pg.locator("a.back").is_visible(), "Gast 390 px: Liste, Weg zurück, nichts ragt hinaus")
                pg.tap("a.li"); pg.wait_for_selector("svg", timeout=10000)
                ok(pg.evaluate(breit) and pg.locator("a.back").is_visible() and pg.evaluate("() => document.scripts.length === 0"), "Gast 390 px: Tour mit Skizze und Profil, ohne Skript")
                pg.screenshot(path=os.path.join(bilder, "gast_tour_390.png"), full_page=True)
                ctx.close()
            ok(not aussen, "keine Anfrage nach aussen" + (": " + ", ".join(sorted(set(aussen))[:5]) if aussen else ""))
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(20)
        except Exception:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)


# ---- the real height package -----------------------------------------------------------------------------------------------------------
def teil_hoehe_echt(datei, aus):
    home = tempfile.mkdtemp(prefix="mw_touren_echt_")
    ns = lade(datei, home)
    p = os.path.join(aus, "hoehe-ch-1.bin")
    print(f"H) echtes Höhenpaket: {os.path.getsize(p) / 1e6:.1f} MB", flush=True)
    K = ns["KhFile"](p)
    ok(K.grid >= 2 and K.q <= 1 and K.cols * K.grid > 300000 and K.rows * K.grid > 200000, f"Kopf: Gitter {K.grid:g} m, Stufe {K.q:g} m, {K.cols} × {K.rows} Zellen, «{K.info}»")
    # known heights (swisstopo, rounded): place, lat, lon, metres, tolerance
    for nm, la, lo, h, tol in (("Bern, Bundesplatz", 46.9470, 7.4440, 540, 12), ("Zürich, Bürkliplatz", 47.3663, 8.5410, 408, 10), ("Seon AG", 47.3475, 8.1602, 445, 20),
                               ("Rigi Kulm", 47.0567, 8.4853, 1790, 40), ("Jungfraujoch", 46.5474, 7.9853, 3460, 120), ("Lugano, Piazza", 46.0037, 8.9511, 273, 15),
                               ("Dufourspitze", 45.9369, 7.8668, 4634, 150)):
        v = K.height(la, lo)
        ok(v is not None and abs(v - h) <= tol, f"{nm}: {v} m (erwartet {h} ± {tol})")
    for nm, la, lo in (("Vaduz (Liechtenstein)", 47.1410, 9.5215), ("Malbun (Liechtenstein)", 47.1010, 9.6100), ("Konstanz (D)", 47.6600, 9.1750), ("Chamonix (F)", 45.9237, 6.8694),
                       ("Mailand (I)", 45.4642, 9.1900)):
        v = K.height(la, lo)
        print(f"    ABDECKUNG {nm}: {'keine Höhendaten' if v is None else str(v) + ' m'}", flush=True)
    ok(K.height(45.4642, 9.19) is None and K.height(48.5, 8.0) is None, "weit ausserhalb: keine Höhe")
    ok(K.reads < 0.05 * os.path.getsize(p), f"gelesen {K.reads / 1e3:.0f} KB von {os.path.getsize(p) / 1e6:.1f} MB")
    t0 = time.time()
    ns["kh_installed"] = lambda: True; ns["kh_file"] = lambda: K
    line, cov = ns["kh_line"]([(47.0567, 8.4853), (47.0445, 8.4660), (47.0330, 8.4330)])
    s = ns["kt_stats"](line, drawn=True)
    ok(cov is True and s["ele"] and s["down"] > 500, f"Route an der Rigi: {s['m'] / 1000:.2f} km, +{s['up']} / −{s['down']} m, {s['min']} min in {1000 * (time.time() - t0):.0f} ms")
    K.close(); shutil.rmtree(home, ignore_errors=True)


def main():
    import glob
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--web", default="")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--ohne-browser", action="store_true")
    ap.add_argument("--hoehe-echt", default="")
    ap.add_argument("--tour", default="", help="eine eigene KML- / GPX-Datei im Browser zeigen (nur lokal)")
    a = ap.parse_args()
    c = sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    datei = os.path.abspath(a.datei or c[-1])
    bilder = a.bilder or tempfile.mkdtemp(prefix="touren_bilder_")
    print(f"Touren · {os.path.basename(datei)}", flush=True)
    if a.hoehe_echt:
        teil_hoehe_echt(datei, a.hoehe_echt)
    elif a.tour:
        teil_b(datei, a.web, bilder, a.tour)
    else:
        teil_a(datei)
        if not a.ohne_browser:
            teil_b(datei, a.web, bilder)
    print("Bilder:", bilder)
    for f in FEHLER:
        print("FEHLER:", f)
    print("Touren-Test:", "OK" if not FEHLER else f"{len(FEHLER)} Fehler")
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
