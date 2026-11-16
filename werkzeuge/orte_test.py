#!/usr/bin/env python3
"""MoveEye: Test «📌 Eigene Orte» auf der Offline-Karte (Teil 639zzzzo, mit 639zzx kt_parse und dem Digitalen Rucksack 639zzc).

  python3 werkzeuge/orte_test.py [--web karte-web-2.zip] [--bilder ORDNER] [--ohne-browser] [--datei X.py]

A) im Prozess (Test-Client): Selbsttest; Rechte (Admin, files_admin, Familie, Kind, «Nur ansehen»): alle sehen die Orte,
   nur Admin / files_admin ändern; «Meine Orte.geojson» im Ordner «🗺️ Karte» des Rucksacks (wird angelegt), hinzufügen /
   bearbeiten / verschieben / löschen, veraltete Nummer = 409 (nichts überschrieben), Namen nur als Text, 20 Fassungen +
   Zurückholen, gleichzeitiges Schreiben verliert nichts, eine von Hand zerstörte Datei wird nicht überschrieben; GPX / KML /
   GeoJSON aus dem Rucksack als Ebenen (Für alle = alle, privat = nur der Besitzer), «für alle ausblenden», übernehmen;
   Fotos nur über die Adresse der Karte (Benutzer ohne Datei-Rechte), Export GPX / KML (wieder lesbar), böse und grosse
   Dateien unter Zeitgrenze, keine Koordinate im Protokoll, Höhe ohne Paket = keine.
B) im Browser bei 390 px (und PC): Symbolleiste in der Karte, Symbol wählen + antippen = Ort + Bearbeiten, Karte des Orts,
   Löschen mit Rückfrage in der Seite (kein confirm()), Verschieben, Ebenen ein / aus (bleibt nach Neuladen), Symbole
   verstecken; Kind: sieht die Orte und das Foto, keine Leiste, keine Knöpfe zum Ändern; Rucksack: die Haken tzCard /
   tzOpen (verkettet), Abzeichen und Blatt «Auf der Karte zeigen»; keine Anfrage nach aussen, nichts ragt seitlich hinaus.
"""
import argparse
import base64
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import threading
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
sys.path.insert(0, HIER)
ZEIT_MAX = 20.0
FEHLER = []
SEON = (47.3475, 8.1602)


def ok(c, what):
    print(("  ✓ " if c else "  ✗ ") + what, flush=True)
    if not c:
        FEHLER.append(what)
    return c


def lade(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_orte_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    return ns


def gpx_datei(name="Rundweg", n=40):
    o = ['<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1"><metadata><name>%s</name></metadata>' % name,
         '<wpt lat="47.3500" lon="8.1650"><ele>480</ele><name>Brunnen &lt;img src=x onerror=alert(1)&gt;</name></wpt>',
         '<wpt lat="47.3520" lon="8.1700"><name>Aussicht</name></wpt>', "<trk><name>%s</name><trkseg>" % name]
    for i in range(n):
        o.append('<trkpt lat="%.6f" lon="%.6f"><ele>%.1f</ele></trkpt>' % (47.345 + i * 0.0003, 8.160 + i * 0.0004, 450 + i))
    o.append("</trkseg></trk></gpx>")
    return "\n".join(o).encode("utf-8")


def kml_datei():
    return ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>swisstopo Export</name><Folder><name>Waypoints</name>'
            '<Placemark><name>Parkplatz</name><Point><coordinates>8.1580,47.3460,455</coordinates></Point></Placemark>'
            '<Placemark><name>Grillstelle</name><Point><coordinates>8.1630,47.3490</coordinates></Point></Placemark></Folder></Document></kml>').encode("utf-8")


def boese():
    """(name, bytes, ext) - every one must end as a layer with or without places, never as an error of the server"""
    M = 2 * 1024 * 1024
    return [("GeoJSON 100 000 Ebenen tief", b"[" * 100000 + b"]" * 100000, "geojson"),
            ("GeoJSON 2 MB Ziffern", b"9" * M, "geojson"),
            ("GeoJSON 30 000 Punkte", json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [8.1 + i * 1e-6, 47.3]}, "properties": {"name": "x" * 50}} for i in range(30000)]}).encode(), "geojson"),
            ("GeoJSON 2-MB-Name", json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [8.1, 47.3]}, "properties": {"name": "A" * M, "note": "B" * M}}).encode(), "geojson"),
            ("GeoJSON Linie 120 000 Punkte", json.dumps({"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[8.1 + i * 1e-7, 47.3] for i in range(120000)]}}).encode(), "geojson"),
            ("GeoJSON NaN / Infinity", b'{"type":"Feature","geometry":{"type":"Point","coordinates":[NaN,Infinity]}}', "geojson"),
            ("KML Entity-Bombe", b'<?xml version="1.0"?><!DOCTYPE l [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]><kml><Document><name>&b;</name></Document></kml>', "kml"),
            ("GPX 22 000 Wegpunkte", b"<gpx>" + b'<wpt lat="47.3" lon="8.1"><name>x</name></wpt>' * 22000 + b"</gpx>", "gpx"),
            ("UTF-16", '{"type":"FeatureCollection","features":[]}'.encode("utf-16"), "geojson")]


def teil_a(datei):
    home = tempfile.mkdtemp(prefix="mw_orte_home_")
    ns = lade(datei, home)
    logs = []
    ns["log_event"] = lambda *x, **k: logs.append(" ".join(str(v) for v in x))
    CFG, TZ = ns["CFG"], ns["TZ"]
    root = tempfile.mkdtemp(prefix="mw_orte_root_")
    TZ["root_test"] = root
    ns["tausch_disk_free"] = lambda p: 100 * 1024 ** 3
    print("A) Eigene Orte im Prozess", flush=True)
    ok(bool(ns["eo_selftest"]()) and bool(ns["kt_selftest"]()), "Selbsttest 639zzzzo und 639zzx")
    CFG.update(https_extra=False, lang="de", tausch_on=True, tausch_guest=True, tausch_push=False)
    PW = "Admin-Orte-123"
    assert ns["web_pw_set"](PW)[0]
    users = {"Anna": "family", "Kim": "kid", "Ida": "custom", "Vera": "view"}
    for nm, role in users.items():
        okk, err = ns["users_action"]({"action": "add", "name": nm, "password": nm.lower() + "-pass-12", "role": role}); assert okk, err
    ns["users_action"]({"action": "update", "name": "Ida", "perms": ["files_admin"]})
    ws = ns["WebStream"](None); ws._serve = lambda app, ctx: None; ws.start()
    c = ws.app.test_client(use_cookies=False)
    hd = lambda u, p: {"Authorization": "Basic " + base64.b64encode(f"{u}:{p}".encode()).decode()}
    H = {n: hd(n, n.lower() + "-pass-12") for n in users}
    H["admin"] = hd("admin", PW)

    def get(who, path="/api/karte/orte"):
        r = c.get(path, headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def api(who, d):
        r = c.post("/api/karte/orte", json=dict(d, lang="de"), headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def tz(who, d):
        r = c.post("/api/tausch", json=dict(d, lang="de"), headers=H[who])
        return r.status_code, (r.get_json(silent=True) or {})

    def hoch(who, name, data, area="all", folder=""):
        code, j = tz(who, {"action": "start", "name": name, "size": len(data), "area": area, "folder": folder, "lastmod": 1})
        assert code == 200, (code, j)
        r = c.post(f"/api/tausch/chunk?id={j['id']}&off=0", data=data, headers=dict(H[who], **{"Content-Type": "application/octet-stream"}))
        assert r.status_code == 200, r.get_json()
        code, j = tz(who, {"action": "finish", "id": j["id"]})
        assert code == 200, (code, j)
        return j["file"]["id"]

    own = lambda j: next((l for l in j.get("layers", []) if l["own"]), None)
    # ---- rights
    for who in ("Kim", "Vera", "Anna", "Ida", "admin"):
        code, j = get(who)
        ok(code == 200 and j["layers"] == [] and j["me"]["admin"] == (who in ("Ida", "admin")), f"{who}: /api/karte/orte lesbar, leer, ändern {'ja' if j.get('me', {}).get('admin') else 'nein'}")
    ok(api("Kim", {"action": "add", "lat": 47.35, "lon": 8.16, "sym": "hut"})[0] == 403 and api("Anna", {"action": "add", "lat": 47.35, "lon": 8.16, "sym": "hut"})[0] == 403
       and api("Vera", {"action": "add", "lat": 47.35, "lon": 8.16, "sym": "hut"})[0] == 403, "Kind / Familie / «Nur ansehen»: kein Ort setzen (403)")
    code, j = api("admin", {"action": "add", "lat": 47.3475, "lon": 8.1602, "sym": "fire", "name": "Feuerstelle <script>alert(1)</script>"})
    L1 = j.get("layer") or {}
    p1 = next((p for p in L1.get("pts", []) if p["id"] == j.get("id")), {})
    ok(code == 200 and L1.get("own") and L1.get("name") == "Meine Orte.geojson" and L1.get("folder") == "🗺️ Karte" and p1.get("em") == "🔥" and p1.get("name") == "Feuerstelle <script>alert(1)</script>"
       and p1.get("v") == 1 and p1.get("by") == "Admin" and p1.get("date"), f"Admin setzt einen Ort: in «🗺️ Karte/Meine Orte.geojson», Name bleibt Text, Nummer 1 ({code})")
    lst = c.get("/api/tausch?area=all", headers=H["admin"]).get_json()
    ok(any(f["name"] == "🗺️ Karte" for f in lst["folders"]), "Rucksack: Ordner «🗺️ Karte» angelegt")
    lst = c.get("/api/tausch?area=all&folder=" + urllib.request.quote("🗺️ Karte"), headers=H["admin"]).get_json()
    fown = next((f for f in lst["files"] if f["name"] == "Meine Orte.geojson"), None)
    ok(fown is not None, "Rucksack: «Meine Orte.geojson» liegt im Ordner")
    raw = json.loads(open(os.path.join(root, "f", fown["id"] + ".bin"), encoding="utf-8").read())
    ft = raw["features"][0]
    ok(raw["type"] == "FeatureCollection" and ft["geometry"]["coordinates"] == [8.1602, 47.3475] and ft["properties"]["symbol"] == "fire" and ft["properties"]["emoji"] == "🔥"
       and ft["id"] == j["id"], "Datei: GeoJSON FeatureCollection, Punkt lon/lat, symbol / emoji / id")
    code, j = api("Ida", {"action": "add", "lat": 47.35, "lon": 8.17, "sym": "custom", "emoji": "🦌", "name": "Gämsen", "color": "#2F9E44", "note": "Morgens\nam Waldrand\x00‮"})
    p2 = next((p for p in (j.get("layer") or {}).get("pts", []) if p["id"] == j.get("id")), {})
    ok(code == 200 and p2.get("sym") == "custom" and p2.get("em") == "🦌" and p2.get("col") == "#2f9e44" and p2.get("note") == "Morgens\nam Waldrand" and p2.get("by") == "Ida",
       "files_admin (Ida) setzt einen Ort mit eigenem Emoji, Farbe, Notiz (Zeilen bleiben, Steuerzeichen weg)")
    for who in ("Kim", "Vera"):
        code, j = get(who)
        ok(code == 200 and len((own(j) or {}).get("pts", [])) == 2 and not j["me"]["admin"] and "hist" not in (own(j) or {}), f"{who}: sieht beide Orte (ohne Datei-Rechte), keine Fassungen")
    # ---- edit / move / delete with the number
    code, j = api("admin", {"action": "edit", "id": p1["id"], "v": 0, "name": "x"})
    ok(code == 409 and "geändert" in (j.get("error") or "") and j.get("layer") and j.get("conflict"), f"veraltete Nummer: 409 «{j.get('error')}», nichts überschrieben")
    code, j = api("admin", {"action": "edit", "id": p1["id"], "v": 1, "name": "Feuerstelle", "sym": "fire", "emoji": "", "color": "red", "note": "Holz", "photo": "../../etc"})
    ok(code == 400 and "Foto" in (j.get("error") or ""), "Foto, das nicht im Rucksack ist: abgelehnt")
    code, j = api("admin", {"action": "edit", "id": p1["id"], "v": 1, "name": "Feuerstelle", "sym": "fire", "emoji": "", "color": "red", "note": "Holz"})
    q = next((p for p in (j.get("layer") or {}).get("pts", []) if p["id"] == p1["id"]), {})
    ok(code == 200 and q.get("name") == "Feuerstelle" and q.get("col") == "" and q.get("note") == "Holz" and q.get("v") == 2, "bearbeiten: Name, Notiz, ungültige Farbe weg, Nummer 2")
    code, j = api("admin", {"action": "move", "id": p1["id"], "v": 2, "lat": 47.3480, "lon": 8.1610})
    q = next((p for p in (j.get("layer") or {}).get("pts", []) if p["id"] == p1["id"]), {})
    ok(code == 200 and abs(q.get("la", 0) - 47.348) < 1e-9 and abs(q.get("lo", 0) - 8.161) < 1e-9 and q.get("v") == 3, "verschieben: neue Koordinaten, Nummer 3")
    ok(api("admin", {"action": "move", "id": p1["id"], "v": 3, "lat": 99, "lon": 8})[0] == 400 and api("admin", {"action": "delete", "id": "zzz", "v": 0})[0] == 404,
       "ungültige Koordinate / unbekannter Ort abgelehnt")
    ok(api("Anna", {"action": "delete", "id": p1["id"], "v": 3})[0] == 403, "Familie darf nicht löschen")
    # ---- uploaded files as layers
    g1 = hoch("Anna", "Rundweg Seon.gpx", gpx_datei())
    k1 = hoch("Anna", "swisstopo Export.kml", kml_datei())
    gpriv = hoch("Anna", "Geheim.gpx", gpx_datei("Geheim"), area="mine")
    bad = hoch("Anna", "kaputt.geojson", b'{"type":"FeatureCollection","features":')
    code, j = get("Kim")
    names = [l["name"] for l in j["layers"]]
    lg = next((l for l in j["layers"] if l["id"] == g1), {})
    ok(names[0] == "Meine Orte.geojson" and "Rundweg Seon.gpx" in names and "swisstopo Export.kml" in names and "Geheim.gpx" not in names,
       f"Kind sieht die Ebenen aus «Für alle» (eigene Orte zuerst), nicht die private Datei: {names}")
    ok(len(lg.get("pts", [])) == 2 and lg["pts"][0]["name"] == "Brunnen <img src=x onerror=alert(1)>" and len(lg.get("lines", [])) == 1 and len(lg["lines"][0]) == 40 and lg["pts"][0]["ele"] == 480,
       "GPX: 2 Wegpunkte (Name als Text, Höhe aus der Datei), 1 Linie")
    lk = next((l for l in j["layers"] if l["id"] == k1), {})
    ok(len(lk.get("pts", [])) == 2 and not lk.get("lines"), "KML nur mit Wegpunkten: als Ebene (kt_parse need_route=False)")
    lb = next((l for l in j["layers"] if l["id"] == bad), {})
    ok(lb.get("err") and not lb.get("pts"), f"kaputte GeoJSON: Ebene mit Hinweis «{lb.get('err')}»")
    ok(any(l["id"] == gpriv for l in get("Anna")[1]["layers"]) and not any(l["id"] == gpriv for l in get("admin")[1]["layers"]), "private Datei: nur ihr Besitzer sieht die Ebene")
    # hide for everyone
    ok(api("Anna", {"action": "hide", "file": g1, "hide": True})[0] == 403, "Familie kann nicht ausblenden")
    ok(api("admin", {"action": "hide", "file": g1, "hide": True})[0] == 200, "Admin blendet eine Ebene für alle aus")
    ok(not any(l["id"] == g1 for l in get("Kim")[1]["layers"]) and next(l for l in get("admin")[1]["layers"] if l["id"] == g1)["hidden"], "ausgeblendet: Kind sieht sie nicht, Admin sieht sie als «ausgeblendet»")
    ok(api("admin", {"action": "hide", "file": fown["id"], "hide": True})[0] == 404, "«Meine Orte» selbst lässt sich nicht ausblenden")
    api("admin", {"action": "hide", "file": g1, "hide": False})
    ok(any(l["id"] == g1 for l in get("Kim")[1]["layers"]), "wieder für alle gezeigt")
    # copy into own
    code, j = api("Ida", {"action": "copy", "file": k1, "id": "w0"})
    q = next((p for p in (j.get("layer") or {}).get("pts", []) if p["id"] == j.get("id")), {})
    ok(code == 200 and q.get("name") == "Parkplatz" and abs(q.get("la", 0) - 47.346) < 1e-9 and q.get("ele") == 455, "«In Meine Orte übernehmen»: Name, Ort, Höhe aus der Datei")
    # ---- photo: only through the map address
    import numpy as np
    import cv2
    img = np.zeros((300, 400, 3), np.uint8); cv2.circle(img, (200, 150), 90, (40, 160, 230), -1)
    jpg = cv2.imencode(".jpg", img)[1].tobytes()
    code, j = api("admin", {"action": "prep"})
    ok(code == 200 and j.get("folder") == "🗺️ Karte", "vor dem Foto: Ordner bereit")
    ph = hoch("admin", "Ort Feuerstelle.jpg", jpg, folder="🗺️ Karte")
    for _i in range(100):
        if TZ["files"].get(ph, {}).get("thumb") is not None:
            break
        time.sleep(0.1)
    cur = next(p for p in own(get("admin")[1])["pts"] if p["id"] == p1["id"])
    code, j = api("admin", {"action": "edit", "id": p1["id"], "v": cur["v"], "name": "Feuerstelle", "photo": ph})
    q = next((p for p in (j.get("layer") or {}).get("pts", []) if p["id"] == p1["id"]), {})
    ok(code == 200 and q.get("photo") == ph, "Foto am Ort")
    r = c.get(f"/karte/orte/foto/{ph}.jpg", headers=H["Kim"])
    ok(r.status_code == 200 and r.mimetype == "image/jpeg" and r.data[:2] == b"\xff\xd8" and r.data != jpg and "sandbox" in r.headers.get("Content-Security-Policy", ""),
       "Kind (ohne Datei-Rechte) sieht das Foto über die Karte (neu gerechnete Vorschau, nicht die Datei)")
    ok(c.get(f"/tausch/prev/{ph}.jpg", headers=H["Kim"]).status_code in (403, 404) and c.get(f"/tausch/dl/{ph}", headers=H["Kim"]).status_code in (403, 404),
       "Kind: dasselbe Foto im Rucksack gesperrt")
    other = hoch("Anna", "Privat.jpg", jpg)
    ok(c.get(f"/karte/orte/foto/{other}.jpg", headers=H["Kim"]).status_code == 404 and c.get("/karte/orte/foto/..%2Fx.jpg", headers=H["Kim"]).status_code == 404,
       "ein Foto, auf das kein Ort zeigt: 404")
    # ---- export
    r = c.get(f"/karte/orte/x/{g1}.gpx", headers=H["Anna"])
    back = ns["kt_parse"](r.data, "x.gpx", need_route=False) if r.status_code == 200 else {}
    ok(r.status_code == 200 and "attachment" in r.headers.get("Content-Disposition", "") and len(back.get("wps", [])) == 2 and len(back.get("pts", [])) == 40, "Export GPX einer Ebene: wieder lesbar (2 Orte, Linie)")
    r = c.get(f"/karte/orte/x/{fown['id']}.kml", headers=H["Anna"])
    back = ns["kt_parse"](r.data, "x.kml", need_route=False) if r.status_code == 200 else {}
    ok(r.status_code == 200 and len(back.get("wps", [])) == 3, "Export KML von «Meine Orte»: wieder lesbar")
    ok(c.get(f"/karte/orte/x/{g1}.gpx", headers=H["Kim"]).status_code == 403 and c.get(f"/karte/orte/x/{gpriv}.gpx", headers=H["admin"]).status_code == 404
       and c.get(f"/karte/orte/x/{g1}.exe", headers=H["admin"]).status_code == 404, "Export: Kind ohne «herunterladen» 403, fremde private Datei / falsche Endung 404")
    # ---- height without the package
    code, j = get("Kim", "/api/karte/orte/hoehe?lat=47.35&lon=8.16")
    ok(code == 200 and j.get("ele") is None, "Höhe ohne Höhenpaket: keine (nie 0)")
    # ---- versions
    for i in range(24):
        cur = next(p for p in own(get("admin")[1])["pts"] if p["id"] == p2["id"])
        api("admin", {"action": "edit", "id": p2["id"], "v": cur["v"], "name": "Gämsen %d" % i})
    lay = own(get("admin")[1])
    ok(len(lay.get("hist", [])) == 20 and len(os.listdir(os.path.join(root, "h", fown["id"]))) == 20, f"20 Fassungen bleiben ({len(lay.get('hist', []))}), ältere gelöscht")
    oldest = lay["hist"][-1]
    code, j = api("admin", {"action": "restore", "v": oldest["v"]})
    nm_back = next((p["name"] for p in (j.get("layer") or {}).get("pts", []) if p["id"] == p2["id"]), "")
    ok(code == 200 and nm_back.startswith("Gämsen") and nm_back != "Gämsen 23" and len(j["layer"].get("hist", [])) == 20,
       f"Fassung {oldest['v']} zurückgeholt («{nm_back}» statt «Gämsen 23»), als neueste Fassung gespeichert")
    ok(api("admin", {"action": "restore", "v": 1})[0] == 404, "eine nicht mehr gehaltene Fassung: 404")
    # ---- delete in the page = with the number
    cur = next(p for p in own(get("admin")[1])["pts"] if p["id"] == p1["id"])
    code, j = api("admin", {"action": "delete", "id": p1["id"], "v": cur["v"]})
    ok(code == 200 and not any(p["id"] == p1["id"] for p in j["layer"]["pts"]), "löschen mit der richtigen Nummer")
    # ---- two people at the same time: nothing lost
    n0 = len(own(get("admin")[1])["pts"])
    errs = []

    def viele(who, k):
        cc = ws.app.test_client(use_cookies=False)
        for i in range(12):
            r = cc.post("/api/karte/orte", json={"action": "add", "lat": 47.3 + k * 0.01 + i * 0.0001, "lon": 8.1, "sym": "pin", "name": f"{who}{i}"}, headers=H[who])
            if r.status_code != 200:
                errs.append(r.status_code)
    th = [threading.Thread(target=viele, args=(w, k)) for k, w in enumerate(("admin", "Ida"))]
    [t.start() for t in th]; [t.join() for t in th]
    n1 = len(own(get("admin")[1])["pts"])
    ok(not errs and n1 == n0 + 24, f"zwei gleichzeitig: {n1 - n0} von 24 Orten da, keiner verloren")
    # ---- a file destroyed by hand is not overwritten
    p_ = os.path.join(root, "f", fown["id"] + ".bin")
    open(p_, "wb").write(b"kaputt von Hand")
    code, j = api("admin", {"action": "add", "lat": 47.35, "lon": 8.16, "sym": "hut"})
    ok(code == 400 and "nicht lesbar" in (j.get("error") or "") and open(p_, "rb").read() == b"kaputt von Hand", f"zerstörte «Meine Orte.geojson»: «{j.get('error')}», nichts überschrieben")
    ok(get("Kim")[0] == 200, "zerstörte Datei: die Karte antwortet weiter")
    # ---- bad and big files
    print("   Härtung: böse und grosse Dateien", flush=True)
    for name, data, ext in boese():
        fid = hoch("admin", "boese." + ext, data) if len(data) <= 5 * 1024 * 1024 else None
        if not fid:
            continue
        t0 = time.time(); code, j = get("Kim"); dt = time.time() - t0
        l_ = next((l for l in j.get("layers", []) if l["id"] == fid), {})
        info = l_.get("err") or f"{len(l_.get('pts', []))} Orte, {len(l_.get('lines', []))} Linien, {sum(len(x) for x in l_.get('lines', []))} Linienpunkte"
        ok(code == 200 and dt < ZEIT_MAX and len(l_.get("pts", [])) <= 500 and all(len(x) <= 1501 for x in l_.get("lines", []))
           and all(len(p["name"]) <= 80 and len(p["note"]) <= 1000 for p in l_.get("pts", [])), f"{name} ({len(data) / 1e6:.1f} MB): {info}, {dt * 1000:.0f} ms")
        tz("admin", {"action": "delete", "id": fid})
    ok(not any(re.search(r"47\.3\d|8\.1\d{2}", x) for x in logs), "keine Koordinate im Protokoll")
    ok(any("own place added" in x for x in logs), "Änderungen stehen im Protokoll (ohne Ort)")
    TZ["root_test"] = None
    shutil.rmtree(root, ignore_errors=True); shutil.rmtree(home, ignore_errors=True)


# ---- B: the browser ------------------------------------------------------------------------------------------------------------------
def teil_b(datei, web, bilder):
    from playwright.sync_api import sync_playwright
    from piper_test import Srv
    import karten_test as KA
    import numpy as np
    import cv2
    print("B) im Browser (390 px und PC)", flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_orte_b_")
    P, rel, pins, tiles = KA.dateien_bauen(tmp, web)
    srv = Srv()
    for r_, f in pins.items():
        srv.files["/" + f["tag"] + "/" + f["name"]] = open(os.path.join(rel, f["name"]), "rb").read()   # 639zzq Topo: each file at its release
    d2 = KA.gepatcht(datei, tmp, pins, srv.url)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    PW = "Orte-" + os.urandom(4).hex()
    p, cfg = KA.starte(d2, tmp, port, PW, {"latitude": SEON[0], "longitude": SEON[1]})
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user=("admin", PW), raw=None):
        hd = {"Authorization": "Basic " + base64.b64encode(f"{user[0]}:{user[1]}".encode()).decode(), "Origin": base,
              "Content-Type": "application/json" if raw is None else "application/octet-stream"}
        r = urllib.request.Request(base + path, data=raw if raw is not None else (json.dumps(data).encode() if data is not None else None), headers=hd)
        try:
            with op.open(r, timeout=120) as x:
                return x.status, json.loads(x.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, {}

    def hoch(name, data, folder="", user=("admin", PW)):
        c_, j = req("/api/tausch", {"action": "start", "name": name, "size": len(data), "folder": folder, "area": "all"}, user)
        req(f"/api/tausch/chunk?id={j['id']}&off=0", raw=data, user=user)
        return req("/api/tausch", {"action": "finish", "id": j["id"]}, user)[1]["file"]["id"]
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
        req("/api/users", {"action": "add", "name": "Kim", "password": "kim-pass-123", "role": "kid"})
        req("/api/karte", {"action": "install"})
        for _i in range(240):
            if req("/api/karte")[1].get("on"):
                break
            time.sleep(0.5)
        ok(req("/api/karte")[1].get("on"), "Testkarte installiert")
        # data: a GPX of a user, a photo and two places
        g1 = hoch("Rundweg Seon.gpx", gpx_datei())
        img = np.zeros((360, 640, 3), np.uint8); img[:] = (200, 160, 90); cv2.rectangle(img, (220, 150), (420, 330), (40, 70, 140), -1)
        req("/api/karte/orte", {"action": "prep"})
        ph = hoch("Ort Hütte.jpg", cv2.imencode(".jpg", img)[1].tobytes(), "🗺️ Karte")
        time.sleep(2)
        j = req("/api/karte/orte", {"action": "add", "lat": SEON[0] + 0.002, "lon": SEON[1] - 0.004, "sym": "hut", "name": "Waldhütte", "note": "Schlüssel beim Förster", "photo": ph})[1]
        hut = j.get("id")
        req("/api/karte/orte", {"action": "add", "lat": SEON[0] - 0.002, "lon": SEON[1] + 0.003, "sym": "danger", "name": "Steinschlag"})
        os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=KA.ARGS)
            aussen = []

            def kontext(mob, user=("admin", PW)):
                vp = {"width": 390, "height": 844} if mob else {"width": 1366, "height": 900}
                ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, http_credentials={"username": user[0], "password": user[1]}, locale="de-CH")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');localStorage.setItem('mw-sheet','full');"
                                    "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\",\"settings\",\"rec\",\"history\",\"sim\",\"protect\",\"zones\",\"cams\",\"place\",\"tools\"]')}catch(e){}")
                ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:")) else (aussen.append(r.request.url[:120]), r.abort()))
                return ctx
            breit = "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
            for name, mob in (("390", True), ("pc", False)):
                ctx = kontext(mob); pg = ctx.new_page(); errs = []; dial = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                pg.on("dialog", lambda d: (dial.append(d.message), d.dismiss()))
                tap = (lambda sel: pg.tap(sel)) if mob else (lambda sel: pg.click(sel))
                pg.goto(base + "/karte?z=15")
                pg.wait_for_function("() => window.KQMAP && KQMAP.loaded()", timeout=60000)
                pg.wait_for_selector("#eo:not([hidden]) .eo-ly", timeout=20000)
                pg.wait_for_function("() => document.querySelectorAll('.eo-m').length >= 4", timeout=15000)
                ok(pg.locator("#eo-bar").is_visible() and pg.locator("#eo-bar button").count() == 10 and pg.evaluate(breit), f"{name}: Symbolleiste in der Karte (9 Symbole + Eigenes), nichts ragt hinaus")
                ok(pg.inner_text("#eo-h") == "Eigene Orte" and pg.locator(".eo-ly").count() == 2 and pg.evaluate("() => document.getElementById('eo').compareDocumentPosition(document.getElementById('kt')) & 4"),
                   f"{name}: Abschnitt «Eigene Orte» mit 2 Ebenen, über den Touren")
                n0 = pg.locator(".eo-m").count()
                # set a place: symbol, then tap the map
                pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'end'})"); pg.wait_for_timeout(300)
                tap('#eo-bar button[data-sym="fire"]'); pg.wait_for_selector("#eo-hint", timeout=5000)
                ok("Feuerstelle setzen" in pg.inner_text("#eo-hint"), f"{name}: Hinweis «Tippe auf die Karte: 🔥 Feuerstelle setzen»")
                if mob:
                    pg.screenshot(path=os.path.join(bilder, "orte_setzen_390.png"))
                bx = pg.locator("#kq-c").bounding_box()
                (pg.touchscreen.tap if mob else pg.mouse.click)(bx["x"] + bx["width"] * 0.35, bx["y"] + bx["height"] * 0.4)
                pg.wait_for_selector("#eo-card #eo-ename", timeout=10000)
                ok(pg.locator(".eo-m").count() == n0 + 1 and pg.evaluate("() => !document.querySelector('#kq-btns') || document.querySelector('#kq-btns').hidden") and not dial,
                   f"{name}: der Tipp setzt den Ort (wählt keinen Standort), Bearbeiten offen")
                pg.fill("#eo-ename", f"Feuer <b>{name}</b>"); pg.fill("#eo-enote", "Holz liegt bereit"); pg.locator("#eo-card .cols button").nth(3).click()
                tap("#eo-esave"); pg.wait_for_selector("#eo-card #eo-name", timeout=10000)
                ok(pg.inner_text("#eo-name").strip().endswith(f"Feuer <b>{name}</b>") and not pg.query_selector("#eo-name b") and "Holz liegt bereit" in pg.inner_text("#eo-card"),
                   f"{name}: gespeichert, Name als Text")
                if mob:
                    pg.screenshot(path=os.path.join(bilder, "orte_ort_offen_390.png"))
                # delete: the question inside the page
                tap("#eo-del"); pg.wait_for_selector("#eo-ask", timeout=5000)
                ok("löschen?" in pg.inner_text("#eo-ask") and not dial, f"{name}: Löschen fragt in der Seite (kein confirm())")
                if mob:
                    pg.screenshot(path=os.path.join(bilder, "orte_loeschen_390.png"))
                tap("#eo-no"); pg.wait_for_timeout(200)
                ok(pg.locator("#eo-ask").count() == 0 and pg.locator(".eo-m").count() == n0 + 1, f"{name}: «Nein» löscht nicht")
                tap("#eo-del"); pg.wait_for_selector("#eo-ask"); tap("#eo-yes")
                pg.wait_for_function("(n) => !document.getElementById('eo-card') && document.querySelectorAll('.eo-m').length === n", arg=n0, timeout=10000)
                ok(True, f"{name}: «Ja, löschen» löscht, die Karte schliesst sich")
                # open the hut: photo, move it
                pg.evaluate("(id) => document.querySelector('.eo-m[data-p=\"' + id + '\"]').click()", hut); pg.wait_for_selector("#eo-card img", timeout=10000)
                pg.wait_for_function("() => { const i = document.querySelector('#eo-card img'); return i && i.complete && i.naturalWidth > 0; }", timeout=10000)
                ok("Schlüssel beim Förster" in pg.inner_text("#eo-card") and pg.locator("#eo-tour").count() == 1, f"{name}: Karte des Orts mit Foto, Notiz, «Tour ab hier»")
                tap("#eo-move"); pg.wait_for_selector("#eo-hint", timeout=5000)
                (pg.touchscreen.tap if mob else pg.mouse.click)(bx["x"] + bx["width"] * 0.6, bx["y"] + bx["height"] * 0.3)
                pg.wait_for_selector("#eo-card #eo-name", timeout=10000)
                pt = next(q for q in next(l for l in req("/api/karte/orte")[1]["layers"] if l["own"])["pts"] if q["id"] == hut)
                ok(abs(pt["la"] - (SEON[0] + 0.002)) > 1e-5, f"{name}: «Verschieben» + Tipp auf die Karte: neuer Ort gespeichert")
                tap("#eo-cx")
                # «Tour ab hier»: the tours start drawing at the place
                pg.evaluate("(id) => document.querySelector('.eo-m[data-p=\"' + id + '\"]').click()", hut); pg.wait_for_selector("#eo-tour", timeout=5000)
                tap("#eo-tour")
                try:
                    pg.wait_for_function("() => window.KT && KT.busy && document.querySelectorAll('.kt-pt').length === 1", timeout=10000); tz_ok = True
                except Exception:
                    tz_ok = False
                ok(tz_ok and not pg.locator("#eo-card").count(), f"{name}: «Tour ab hier» startet das Zeichnen mit dem Ort als erstem Punkt "
                   + str(pg.evaluate("() => [!!(window.KT && KT.busy), document.querySelectorAll('.kt-pt').length, !!document.getElementById('kt-bar'), !!document.getElementById('eo-card')]")))
                pg.evaluate("() => document.querySelector('.eo-m[title=\"Steinschlag\"]').click()")
                try:
                    pg.wait_for_function("() => document.querySelectorAll('.kt-pt').length === 2", timeout=5000); t2 = True
                except Exception:
                    t2 = False
                ok(t2 and not pg.locator("#eo-card").count(), f"{name}: beim Zeichnen wird ein angetippter Ort der nächste Punkt der Route")
                tap("#kt-dback"); pg.wait_for_function("() => !KT.busy", timeout=5000)
                # layers on / off, remembered
                sw = pg.locator(f'.eo-ly[data-id="{g1}"] .eo-sw')
                sw.scroll_into_view_if_needed(); n1 = pg.locator(".eo-m").count(); sw.click()
                pg.wait_for_function("(n) => document.querySelectorAll('.eo-m').length === n - 2", arg=n1, timeout=5000)
                pg.reload(); pg.wait_for_function("() => window.KQMAP && KQMAP.loaded()", timeout=60000); pg.wait_for_selector(".eo-ly", timeout=15000); pg.wait_for_timeout(800)
                ok(pg.locator(".eo-m").count() == n1 - 2 and "on" not in (pg.get_attribute(f'.eo-ly[data-id="{g1}"] .eo-sw', "class") or ""), f"{name}: Ebene aus (bleibt nach Neuladen, dieses Gerät)")
                pg.locator(f'.eo-ly[data-id="{g1}"] .eo-sw').click(); pg.wait_for_function("(n) => document.querySelectorAll('.eo-m').length === n", arg=n1, timeout=5000)
                chip = pg.locator("#eo-chips button", has_text="⚠️"); chip.click(); pg.wait_for_timeout(200)
                ok(pg.locator(".eo-m").count() == n1 - 1 and "off" in (chip.get_attribute("class") or ""), f"{name}: Symbol ⚠️ versteckt")
                chip.click()
                if mob:
                    pg.locator("#eo").scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0, -120)"); pg.wait_for_timeout(300)
                    pg.screenshot(path=os.path.join(bilder, "orte_ebenen_390.png"))
                else:
                    pg.screenshot(path=os.path.join(bilder, "orte_pc.png"), full_page=True)
                ok(pg.evaluate(breit), f"{name}: nichts ragt hinaus")
                ok(not errs, f"{name}: keine JS-Fehler" + (": " + " | ".join(errs[:3]) if errs else ""))
                ctx.close()
            # the kid: sees, does not change
            ctx = kontext(True, ("Kim", "kim-pass-123")); pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(base + "/karte?z=15"); pg.wait_for_function("() => window.KQMAP && KQMAP.loaded()", timeout=60000)
            pg.wait_for_selector(".eo-ly", timeout=15000); pg.wait_for_function("() => document.querySelectorAll('.eo-m').length >= 4", timeout=15000)
            ok(pg.locator("#eo-bar").count() == 0, "Kind: sieht die Orte, keine Symbolleiste")
            pg.evaluate("(id) => document.querySelector('.eo-m[data-p=\"' + id + '\"]').click()", hut); pg.wait_for_selector("#eo-card", timeout=5000)
            pg.wait_for_function("() => { const i = document.querySelector('#eo-card img'); return i && i.complete && i.naturalWidth > 0; }", timeout=10000)
            ok(pg.locator("#eo-edit, #eo-del, #eo-move, #eo-copy").count() == 0 and pg.locator('a[href*="/karte/orte/x/"]').count() == 0, "Kind: Foto sichtbar, keine Knöpfe zum Ändern, kein Export")
            pg.screenshot(path=os.path.join(bilder, "orte_kind_390.png"))
            ok(not errs, "Kind: keine JS-Fehler")
            ctx.close()
            # the backpack: the hooks tzCard / tzOpen
            ctx = kontext(True); pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(base + "/tausch"); pg.wait_for_selector(".tz-it", state="attached", timeout=20000)
            r = pg.evaluate("""(id) => { const it = document.createElement('div'), tx = document.createElement('div'), th = document.createElement('div');
              let other = 0; window.tzCard = function () { other++; };
              window.tzCard({id: id, name: 'Rundweg Seon.gpx', folder: ''}, it, tx, th);
              const a = tx.querySelector('a.eo-bdg');
              const opened = window.tzOpen({id: id, name: 'Rundweg Seon.gpx', dl: true}, {});
              const notGeo = window.tzOpen({id: id, name: 'x.jpg', kind: 'image', ext: 'jpg', dl: true}, {});   // like 639zzc (kind set): 639zzzzv keeps pictures for the preview
              return {other, href: a && a.getAttribute('href'), th: th.textContent, opened, notGeo, sheet: !!document.getElementById('eo-sheet')}; }""", g1)
            ok(r["other"] == 1 and r["href"] == "/karte?orte=" + g1 and r["th"] == "🗺️" and r["opened"] is True and r["notGeo"] is False and r["sheet"],
               f"Rucksack: tzCard verkettet (der andere Haken läuft mit), Abzeichen → /karte?orte=…, tzOpen zeigt das Blatt nur für Dateien mit Orten {r}")
            pg.wait_for_function("() => /Orte/.test(document.getElementById('eo-sheet').innerText)", timeout=10000)
            ok("2 Orte · 1 Linie" in pg.inner_text("#eo-sheet") and pg.get_attribute("#eo-go", "href") == "/karte?orte=" + g1, "Blatt: «2 Orte · 1 Linie», «Auf der Karte zeigen»")
            ok(not errs, "Rucksack: keine JS-Fehler")
            ctx.close()
            # /karte?orte=<file>: the layer comes on and the map shows it
            ctx = kontext(False); pg = ctx.new_page()
            pg.add_init_script("try{localStorage.setItem('eo-off', JSON.stringify(['%s']))}catch(e){}" % g1)
            pg.goto(base + "/karte?orte=" + g1); pg.wait_for_function("() => window.KQMAP && KQMAP.loaded()", timeout=60000); pg.wait_for_selector(".eo-ly", timeout=15000)
            pg.wait_for_timeout(800)
            ok("on" in (pg.get_attribute(f'.eo-ly[data-id="{g1}"] .eo-sw', "class") or "") and pg.evaluate("() => KQMAP.getZoom()") > 12, "/karte?orte=…: die Ebene ist an, die Karte zeigt sie")
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


def main():
    import glob
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--web", default="")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--ohne-browser", action="store_true")
    a = ap.parse_args()
    c = sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    datei = os.path.abspath(a.datei or c[-1])
    bilder = a.bilder or tempfile.mkdtemp(prefix="orte_bilder_")
    print(f"Eigene Orte · {os.path.basename(datei)}", flush=True)
    teil_a(datei)
    if not a.ohne_browser:
        teil_b(datei, a.web, bilder)
    print("Bilder:", bilder)
    for f in FEHLER:
        print("FEHLER:", f)
    print("Orte-Test:", "OK" if not FEHLER else f"{len(FEHLER)} Fehler")
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
