#!/usr/bin/env python3
"""MoveEye: Test «🏕 Wildcamp» (Teil 639zzzzzw, werkzeuge/wildcamp/paket.py).

  python3 werkzeuge/wildcamp_test.py [--roh ROH] [--web karte-web-2.zip] [--bilder ORDNER] [--ohne-browser] [--datei X.py]

Ohne --roh: kleine erfundene Rohdaten in LV95 (wie sie api3.geo.admin.ch liefert) - der Test braucht so kein Netz zu
geo.admin.ch. Mit --roh: die echte Ausgabe von `paket.py --holen` (dann die strenge Prüfung: Mindestzahlen, «Alp Plaun» mit
20.12. - 30.04., «Augstmatthorn», Nationalpark, alle 26 Kantone).

A) im Prozess
   * Paket: bauen, --pruefen (Dateien, Lage, bekannte Zone mit Schutzzeit, Lizenztext, Pins = Grösse + sha256), gleiche
     Eingabe = gleiche Bytes, Grösse unter der Grenze des Hosts.
   * Laden: nur der Admin, veränderte Datei abgelehnt (kein halber Ordner), dann installiert; Dateien nur über die Liste.
   * DATUM: dieselbe Zone im November blass (ausserhalb), im Januar kräftig (Schutzzeit über Neujahr).
   * ANTIPPEN: «Wildruhezone «Alp Plaun (Nr. 2.0)» – Betreten 20.12.–30.4. verboten (verbindlich)», Kanton mit Notiz und
     Quelle, «keine Schutzzone bekannt» daneben, alle 5 Sprachen.
   * TOUR: eine Route durch die Zone -> ein Abschnitt (km von - bis), daneben keiner; auch für Benutzer ohne Admin.
   * BERGTAL: die erfundenen Wildruhezonen aus bergtal.gd im Bergtal-Paket (paket.py), Antippen am Schlafplatz «Riedmoos»,
     Tour durch die Zone, Host-Grenze.
B) im Browser (MoveEye als eigener Prozess, 390 px DPR 2 und PC): Offline-Karte Schweiz (Testdateien) + Wildcamp über den
   Knopf laden, Ebene mit Legende und Schaltern, Datum blass / kräftig, Antippen = Karte, Eigener Ort «Zelt» in der Zone =
   Hinweis «Nachtlager», gespeicherte Tour = Abschnitt mit «Abschnitt zeigen», Bergtal mit erfundenen Zonen; keine Anfrage
   nach aussen, keine JS-Fehler, nichts ragt seitlich hinaus. Bildschirmfotos in --bilder.
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
sys.path.insert(0, os.path.join(HIER, "wildcamp"))
import paket as WP                                      # noqa: E402  (werkzeuge/wildcamp/paket.py)
sys.path.remove(os.path.join(HIER, "wildcamp"))
del sys.modules["paket"]
FEHLER = []
PLAUN = (47.36, 8.20)                                   # the made-up «Alp Plaun» lies here (inside the test tiles of karten_test)
TEXT_PLAUN = "Wildruhezone «Alp Plaun (Nr. 2.0)» – Betreten 20.12.–30.4. verboten (verbindlich)"


def ok(c, what):
    print(("  ✓ " if c else "  ✗ ") + what, flush=True)
    if not c:
        FEHLER.append(what)
    return c


def neueste_datei():
    c = sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    return c[-1]


# ---- made-up raw data in LV95 ----------------------------------------------------------------------------------------------------
def lv95(lat, lon):
    """swisstopo «Näherungsformeln» WGS84 -> LV95 (the inverse of paket.lv95_wgs84)"""
    p, l = (lat * 3600 - 169028.66) / 10000, (lon * 3600 - 26782.5) / 10000
    e = 2600072.37 + 211455.93 * l - 10938.51 * l * p - 0.36 * l * p * p - 44.54 * l ** 3
    n = 1200147.07 + 308807.95 * p + 3745.25 * l * l + 76.63 * p * p - 194.56 * l * l * p + 119.79 * p ** 3
    return [round(e, 1), round(n, 1)]


def quadrat(lat, lon, d, n=24):
    """a ring of n+1 points (dense, so the simplification has work) around (lat, lon), d degrees"""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        pts.append(lv95(lat + d * 0.75 * math.sin(a), lon + d * math.cos(a)))
    return pts + [pts[0]]


def mp(*rings):
    return {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}


def erfundene_roh(roh):
    os.makedirs(roh, exist_ok=True)
    wrz_a = {"wrz_name": "Alp Plaun (Nr. 2.0)", "schutzs_de": "rechtsverbindlich", "bestimmung": "R20", "best_de": "Zutrittsverbot (zu Fuss und Wintersportarten)",
             "best_fr": "Interdiction d’accès (à pied ou pour les sports d’hiver)", "best_it": "Divieto di accesso (a piedi o per la pratica di sport invernali)",
             "schutzzeit": "20.12. - 30.04.", "grundlage": "Regierungsbeschluss", "kanton": "GR", "url_kanton": None}
    wrz_b = {"wrz_name": "Sommerruhe Test (Nr. 9.0)", "schutzs_de": "empfohlen", "bestimmung": "E30", "best_de": "Bitte nicht betreten, durchqueren nur auf eingezeichneter Route",
             "schutzzeit": "01.04. - 31.07.", "kanton": "AG"}
    D = {
        "wrz": [{"id": 1, "attributes": wrz_a, "geometry": mp(quadrat(PLAUN[0], PLAUN[1], 0.012))},
                {"id": 2, "attributes": wrz_b, "geometry": mp(quadrat(47.33, 8.10, 0.01))},
                {"id": 3, "attributes": {"weg_id": 7, "wegtyp_de": "Erlaubter Weg / Route", "wegtyp_fr": "Chemin autorisé", "wegtyp_it": "Sentiero autorizzato"},
                 "geometry": {"type": "LineString", "coordinates": [lv95(PLAUN[0] - 0.012, PLAUN[1] - 0.004), lv95(PLAUN[0] + 0.012, PLAUN[1] + 0.004)]}}],
        "wsg": [{"id": 4, "attributes": {"jb_name": "Augstmatthorn (Nr. 1.00)", "schutzs_de": "rechtsverbindlich", "bestimmung": "R170", "schutzzeit": "01.01.-31.12.",
                                         "best_de": "Schneesportarten verboten ausserhalb markierter Pisten, Routen und Loipen", "kanton": "BE"},
                 "geometry": mp(quadrat(47.42, 8.32, 0.006))},
                {"id": 5, "attributes": {"jb_name": "Augstmatthorn"}, "geometry": {"type": "LineString", "coordinates": [lv95(47.41, 8.31), lv95(47.43, 8.33)]}}],
        "jb": [{"id": 6, "attributes": {"gebietsname": "Augstmatthorn", "objektnummer": "1", "typ_de": "Jagdbanngebiet",
                                        "refobjblatt": "https://api3.geo.admin.ch/featureattachments/x/nr1.pdf"}, "geometry": mp(quadrat(47.42, 8.32, 0.02))}],
        "snp": [{"id": 7, "attributes": {"name": "Schweizerischer Nationalpark", "kategorie": "SNP"}, "geometry": mp(quadrat(47.25, 8.35, 0.02))}],
        "wzvv": [{"id": 8, "attributes": {"name": "Testsee (AG)", "objnummer": "3", "schutzkategorie_de": "Jagd verboten"}, "geometry": mp(quadrat(47.30, 7.98, 0.01))}],
        "hm": [{"id": 9, "attributes": {"name": "Hochmoor Test", "objnummer": "136"}, "geometry": mp(quadrat(47.38, 8.05, 0.004))}],
        "fm": [{"id": 10, "attributes": {"name": "Flachmoor Test", "objnummer": "12"}, "geometry": mp(quadrat(47.45, 8.12, 0.005), quadrat(47.455, 8.14, 0.002))}],
        "ml": [{"id": 11, "attributes": {"name": "Moorlandschaft Test", "objnummer": "2"}, "geometry": mp(quadrat(47.45, 8.12, 0.015))}],
        "au": [{"id": 12, "attributes": {"name": "Aue Test", "objnummer": "2", "auen_type_de": "Fliessgewässer"}, "geometry": mp(quadrat(47.28, 8.22, 0.008))}],
        "kt": [{"id": 13, "attributes": {"ak": "GR", "name": "Graubünden"}, "geometry": mp([lv95(47.30, 8.15), lv95(47.30, 8.30), lv95(47.42, 8.30), lv95(47.42, 8.15), lv95(47.30, 8.15)])},
               {"id": 14, "attributes": {"ak": "AG", "name": "Aargau"}, "geometry": mp([lv95(47.20, 7.90), lv95(47.20, 8.15), lv95(47.50, 8.15), lv95(47.50, 7.90), lv95(47.20, 7.90)])}],
    }
    for k, F in D.items():
        json.dump(F, open(os.path.join(roh, k + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"datum": "2026-11-22", "ebenen": {k: len(v) for k, v in D.items()}}, open(os.path.join(roh, "holen.json"), "w", encoding="utf-8"))
    return roh


def paket_bauen(roh, aus, echt):
    zp = WP.bauen(roh, aus)
    WP.pins(aus)
    err = WP.pruefen(aus, strikt=echt)
    ok(not err, "paket.py --pruefen%s: %s" % (" (streng, echte Daten)" if echt else "", "OK" if not err else "; ".join(err[:4])))
    data = open(zp, "rb").read()
    zp2 = WP.bauen(roh, aus + "_2")
    ok(open(zp2, "rb").read() == data, "Paket: gleiche Eingabe = gleiche Bytes")
    with zipfile.ZipFile(zp) as z:
        unp = sum(i.file_size for i in z.infolist())
        wrz = json.loads(z.read("zonen/wrz.json"))
        lic = z.read("LIZENZEN.txt").decode()
    pl = [f for f in wrz["features"] if f["properties"].get("n", "").startswith("Alp Plaun")]
    ok(len(pl) == 1 and pl[0]["properties"]["p"] == [["1220", "0430"]] and pl[0]["properties"]["s"] == "v" and pl[0]["properties"]["z"] == "20.12. - 30.04.",
       "bekannte Zone «Alp Plaun» mit Schutzzeit 20.12. - 30.04. (verbindlich) im Paket")
    pin = open(os.path.join(aus, "pins_wildcamp.txt")).read()
    ok("size=%d " % len(data) in pin and "sha256=%s " % hashlib.sha256(data).hexdigest() in pin and "unpacked=%d " % unp in pin,
       "Pins: Grösse %d, sha256 %s…, entpackt %d" % (len(data), hashlib.sha256(data).hexdigest()[:12], unp))
    ok(len(data) + unp * 1.3 < 40e6 and len(data) < WP.MAX_ZIP, "passt auf den Host (ZIP %.1f MB + entpackt %.1f MB)" % (len(data) / 1e6, unp / 1e6))
    ok("Quellenangabe ist Pflicht" in lic and "keine Rechtsberatung" in lic and "Kantonale Naturschutzgebiete" in lic,
       "LIZENZEN.txt: Lizenz, Quellenangabe, fehlende kantonale Gebiete, keine Rechtsberatung")
    return zp, data, unp


# ---- the Bergtal: invented Wildruhezonen from bergtal.gd through werkzeuge/bergkarte/paket.py ----------------------------------------
def berg_zonen():
    """WILDRUHEZONEN of simulator3d/scripts/bergtal.gd, read as text (the Godot test bergkarte_test.gd checks the real export)"""
    src = open(os.path.join(ROOT, "simulator3d", "scripts", "bergtal.gd"), encoding="utf-8").read()
    blk = src[src.index("const WILDRUHEZONEN := ["):]
    blk = blk[:blk.index("}]\n") + 2]
    out = []
    for m in re.finditer(r'\{"id": "([^"]+)", "name": "([^"]+)", "z": "([^"]+)", "s": "([ve])", "b": "([A-Z0-9]+)",\s*"ring": \[([^\]]+)\]\}', blk):
        ring = [[float(a), float(b)] for a, b in re.findall(r"Vector2\((-?[\d.]+), (-?[\d.]+)\)", m.group(6))]
        out.append({"id": m.group(1), "name": m.group(2), "z": m.group(3), "s": m.group(4), "b": m.group(5), "ring": ring})
    return out


def berg_paket(tmp, web):
    import bergkarte_test as BT
    exp = BT.erfundenes_tal(os.path.join(tmp, "bexp"))
    d = json.load(open(os.path.join(exp, "bergtal.json"), encoding="utf-8"))
    d["wildruhezonen"] = berg_zonen()
    json.dump(d, open(os.path.join(exp, "bergtal.json"), "w", encoding="utf-8"), ensure_ascii=False)
    BP = BT.BP
    zp = BP.bauen(exp, web, os.path.join(tmp, "baus"))
    rep = BP.pruefen(os.path.join(tmp, "baus"), exp)
    ok("PRUEFUNG OK" in rep and len(d["wildruhezonen"]) >= 3, "Bergtal-Paket mit %d erfundenen Wildruhezonen (paket.py --pruefen)" % len(d["wildruhezonen"]))
    data = open(zp, "rb").read()
    with zipfile.ZipFile(zp) as z:
        unp = sum(i.file_size for i in z.infolist())
        vk = json.loads(z.read("vektor.json"))
    wz = [f for f in vk["features"] if f["properties"]["t"] == "wrz"]
    ok(sorted(f["properties"]["id"] for f in wz) == sorted(w["id"] for w in d["wildruhezonen"]) and all(f["properties"]["p"] for f in wz),
       "vektor.json: Wildruhezonen mit Schutzzeit (t = «wrz»)")
    return BP, data, unp


def lade(datei, home):
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_wildcamp_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    return ns


# ---- A) in the process ------------------------------------------------------------------------------------------------------------
def teil_a(datei, data, unp, bpaket, echt):
    from piper_test import Srv
    print("A) im Prozess", flush=True)
    home = tempfile.mkdtemp(prefix="mw_wc_a_")
    ns = lade(datei, home)
    ns["log_event"] = lambda *x, **k: None
    CFG = ns["CFG"]
    ok("wildcamp_selftest" in ns and bool(ns["wildcamp_selftest"]()), "Selbsttest 639zzzzzw")
    ok(ns["wc_installed"]() is False and ns["wc_pinned"]() == (ns["WC_FILE"]["size"] > 0), "ohne Paket: nicht installiert; gepinnt wie im Programm")
    srv = Srv()
    srv.files["/" + ns["WC_TAG"] + "/" + ns["WC_FILE"]["name"]] = data
    ns["WC_BASE"]["url"] = srv.url
    ns["WC_FILE"].update(size=len(data), sha256=hashlib.sha256(data).hexdigest(), unpacked=unp, datum="2026-11-22")
    ns["WC_RT"]["ok_t"] = 0
    CFG.update(https_extra=False, lang="de", tausch_free_gb=0.02, tausch_on=True, sim_on=False)
    PW = "Admin-Wild-123"
    assert ns["web_pw_set"](PW)[0]
    for nm, pw, role in (("Anna", "anna-pass-1", "family"), ("Kim", "kim-pass-12", "kid")):
        okk, err = ns["users_action"]({"action": "add", "name": nm, "password": pw, "role": role}); assert okk, err
    ws = ns["WebStream"](None); ws._serve = lambda app, ctx: None; ws.start()
    c = ws.app.test_client(use_cookies=False)
    hd = lambda u, p: {"Authorization": "Basic " + base64.b64encode(f"{u}:{p}".encode()).decode()}
    H, HA, HK = hd("admin", PW), hd("Anna", "anna-pass-1"), hd("Kim", "kim-pass-12")
    jget = lambda u, h=H: (lambda r: (r.status_code, r.get_json(silent=True) or {}))(c.get(u, headers=h))
    jpost = lambda u, d, h=H: (lambda r: (r.status_code, r.get_json(silent=True) or {}))(c.post(u, json=d, headers=h))
    ok(jpost("/api/karte/wildcamp", {"action": "install"}, HA)[0] == 403 and jpost("/api/karte/wildcamp", {"action": "install"}, HK)[0] == 403,
       "laden: nur der Admin (Familie / Kind 403)")
    # host limits
    ns["HOST"]["on"] = True
    fit = ns["wc_host_fit"]()
    big = dict(ns["WC_FILE"]); ns["WC_FILE"].update(size=30 * 1000 * 1000, unpacked=20 * 1000 * 1000)
    ok(fit and not ns["wc_host_fit"]() and ns["wc_download"]()[1] == "too large for the host", "Host: dieses Paket passt; ein zu grosses wird abgelehnt («zu gross für den Host»)")
    ns["WC_FILE"].update(big); ns["HOST"]["on"] = False
    srv.tamper.add("/" + ns["WC_TAG"] + "/" + ns["WC_FILE"]["name"])
    okk, err = ns["wc_download"](wait=True)
    ok(not okk and "checksum" in err.lower() and not os.path.isdir(ns["wc_dir"]()) and not ns["wc_installed"](), f"veränderte Datei abgelehnt, kein halber Ordner ({err[:60]})")
    srv.tamper.clear()
    code, st = jpost("/api/karte/wildcamp", {"action": "install"})
    for _i in range(100):
        if not ns["WC_DL"]["running"]:
            break
        time.sleep(0.1)
    ns["WC_RT"]["ok_t"] = 0
    ok(code == 200 and ns["wc_installed"]() and not os.path.exists(os.path.join(ns["wc_dl_dir"](), ns["WC_FILE"]["name"])),
       "über /api/karte/wildcamp geladen, geprüft, ausgepackt, die ZIP wieder weg (%s %s %s)" % (code, st.get("error", ""), ns["WC_DL"]["msg"]))
    key = ns["wc_key"]()
    code, st = jget("/api/karte/wildcamp", HK)
    ok(code == 200 and st["on"] and not st["admin"] and st["meta"]["counts"]["wrz"] >= 2, "Zustand für alle Angemeldeten (Kind sieht, ist nicht Admin)")
    f = lambda p, h=HK, gz=False: c.get("/karte/wildcamp/" + key + "/" + p, headers=dict(h, **({"Accept-Encoding": "gzip"} if gz else {})))
    r = f("zonen/wrz.json", gz=True)
    ok(r.status_code == 200 and r.headers.get("Content-Encoding") == "gzip" and f("zonen/moor.json").status_code == 200 and f("LIZENZEN.txt").status_code == 200,
       "Zonen-Dateien über die Liste (gepackt)")
    ok(all(f(p).status_code == 404 for p in ("wildcamp.ok", "wildcamp.json", "kantone.json", "../wildcamp.ok", "zonen/../wildcamp.ok", "zonen/x.json"))
       and c.get("/karte/wildcamp/000000000000/zonen/wrz.json", headers=HK).status_code == 404, "Marke, Kopf, ../ und falscher Schlüssel: 404")
    # ---- DATE: pale outside, strong inside the period (over the new year)
    la, lo = (PLAUN if not echt else (46.6236, 9.5713))
    if echt:                                                # the real Alp Plaun: the middle of its polygon
        z_ = json.loads(open(os.path.join(ns["wc_dir"](), "zonen", "wrz.json"), encoding="utf-8").read())
        pf = next(x for x in z_["features"] if x["properties"].get("n", "").startswith("Alp Plaun"))
        ring = pf["geometry"]["coordinates"][0] if pf["geometry"]["type"] == "Polygon" else pf["geometry"]["coordinates"][0][0]
        bb = pf["properties"]["x"]
        la, lo = None, None
        for gx in range(1, 20):                             # a point inside (the shape need not be convex)
            for gy in range(1, 20):
                x_, y_ = bb[0] + (bb[2] - bb[0]) * gx / 20, bb[1] + (bb[3] - bb[1]) * gy / 20
                if WP._inside((x_, y_), ring) and la is None:
                    la, lo = y_, x_
    P = lambda datum, lang="de", h=HK: jget("/api/karte/wildcamp/punkt?lat=%s&lon=%s&datum=%s&lang=%s" % (la, lo, datum, lang), h)[1]
    pl = lambda j: [z for z in j.get("zones", []) if z["text"].startswith("Wildruhezone «Alp Plaun")]
    nov, jan = P("2026-11-22"), P("2027-01-15")
    zn, zj = pl(nov), pl(jan)
    ok(len(zn) == 1 and len(zj) == 1 and zn[0]["aktiv"] is False and zj[0]["aktiv"] is True, "Datum: 22.11. ausserhalb der Schutzzeit (blass), 15.1. darin (kräftig)")
    ok(pl(P("2026-12-20"))[0]["aktiv"] and pl(P("2027-04-30"))[0]["aktiv"] and not pl(P("2027-05-01"))[0]["aktiv"] and not pl(P("2026-12-19"))[0]["aktiv"],
       "Datum: Grenzen 20.12. und 30.4. gehören dazu, 19.12. und 1.5. nicht")
    # ---- TAP
    ok(zj and zj[0]["text"] == TEXT_PLAUN, "Antippen: «%s»" % (zj[0]["text"] if zj else "?"))
    kt = jan.get("kanton") or {}
    ok(kt.get("k") == "GR" and "Regeln der Gemeinde beachten" in kt.get("text", "") and kt.get("src", "").startswith("https://www.tcs.ch/") and kt.get("web") == "https://www.gr.ch/",
       "Antippen: Kanton GR mit Notiz «… Regeln der Gemeinde beachten», Quelle TCS, Webseite des Kantons")
    ok(jan.get("legal") == "Information, keine Rechtsberatung." and "kantonale" in jan.get("nur_bund", ""), "Antippen: «Information, keine Rechtsberatung», «nur Daten des Bundes»")
    leer = jget("/api/karte/wildcamp/punkt?lat=46.95&lon=7.45&lang=de", HK)[1]
    ok(leer.get("zones") == [] and leer.get("none") == "keine Schutzzone bekannt", "Antippen daneben: «keine Schutzzone bekannt»")
    langs = {L_: next((z["text"] for z in P("2027-01-15", L_)["zones"] if "Alp Plaun" in z["text"]), "") for L_ in ("fr", "it", "rm", "en")}
    ok(all(t and "{zeit}" not in t and "20.12.–30.4." in t for t in langs.values()) and langs["fr"].startswith("Zone de tranquillité") and langs["en"].startswith("Wildlife rest area")
       and "contraignant" in langs["fr"], "Antippen in fr / it / rm / en: " + langs["it"][:70])
    if not echt:
        sz = jget("/api/karte/wildcamp/punkt?lat=47.33&lon=8.10&datum=2026-06-01&lang=de", HK)[1]
        ok(sz["zones"] and sz["zones"][0]["text"] == "Wildruhezone «Sommerruhe Test (Nr. 9.0)» – Bitte 1.4.–31.7. nicht betreten – auf den eingezeichneten Routen bleiben (empfohlen)"
           and sz["zones"][0]["aktiv"], "empfohlene Zone: " + (sz["zones"][0]["text"] if sz.get("zones") else "?"))
        jb = jget("/api/karte/wildcamp/punkt?lat=47.42&lon=8.32&lang=de", HK)[1]
        cs = sorted(z["c"] for z in jb["zones"])
        ok(cs == ["jb", "wsg"] and any("Eidg. Jagdbanngebiet «Augstmatthorn» – ganzjährig: Jagd verboten" in z["text"] for z in jb["zones"]),
           "Jagdbanngebiet + Wildtierschutzgebiet übereinander: " + ", ".join(cs))
        ho = jget("/api/karte/wildcamp/punkt?lat=47.451&lon=8.12&lang=de", HK)[1]
        ok(sorted(z["c"] for z in ho["zones"]) == ["fm", "ml"], "Flachmoor in der Moorlandschaft: beide")
    # ---- TOUR
    tour = [[la - 0.03, lo], [la + 0.03, lo]]
    code, r = jpost("/api/karte/wildcamp/linie", {"pts": tour, "datum": "2027-01-15", "lang": "de"}, HA)
    s = [x for x in r.get("segs", []) if x["text"] == TEXT_PLAUN]
    ok(code == 200 and len(s) == 1 and 0 < s[0]["km0"] < s[0]["km1"] < 6.7 and s[0]["aktiv"] and len(s[0]["line"]) >= 2,
       "Tour durch die Zone: Abschnitt km %s–%s (Familie darf prüfen)" % (s[0]["km0"] if s else "?", s[0]["km1"] if s else "?"))
    code, r = jpost("/api/karte/wildcamp/linie", {"pts": [[46.95, 7.40], [46.96, 7.45]], "lang": "de"}, HK)
    ok(code == 200 and r.get("segs") == [], "Tour daneben: kein Abschnitt (Kind darf prüfen)")
    ok(jpost("/api/karte/wildcamp/linie", {"pts": "x"}, HK)[0] == 200 and jget("/api/karte/wildcamp/punkt?lat=x&lon=1", HK)[0] == 400, "falsche Eingaben: kein Fehler 500")
    # ---- the page: hooks for own places and tours
    pg = c.get("/karte", headers=HA).get_data(as_text=True)
    ok(pg.count("window.WC = ") == 1 and pg.count('id="wc"') == 1 and "wcPlace(p.la, p.lo, bd, p.sym)" in pg and "wcTour(KT.busy ? S.pts" in pg,
       "/karte: Wildcamp-Skript, Feld, Haken bei Eigenen Orten und Touren")
    # ---- BERGTAL
    BP, bdata, bunp = bpaket
    with zipfile.ZipFile(__import__("io").BytesIO(bdata)) as z_:
        if "web/maplibre-gl.js" not in z_.namelist():          # built without MapLibre (--ohne-browser): only the server side here
            ns["BK_NEED"] = tuple(x for x in ns["BK_NEED"] if not x.startswith("web/"))
    srv.files["/" + ns["BK_TAG"] + "/" + ns["BK_FILE"]["name"]] = bdata
    ns["BK_BASE"]["url"] = srv.url
    ns["BK_FILE"].update(size=len(bdata), sha256=hashlib.sha256(bdata).hexdigest(), unpacked=bunp, sim="test")
    ns["BK_RT"]["ok_t"] = 0
    okk, err = ns["bk_download"](wait=True)
    ns["BK_RT"]["ok_t"] = 0
    ok(okk and ns["bk_installed"](), "Bergtal-Paket geladen " + err)
    bb = jget("/api/karte/wildcamp/berg", HK)[1]
    ok(len(bb.get("fc", {}).get("features", [])) >= 3, "Bergtal: %d erfundene Zonen für die Karte" % len(bb.get("fc", {}).get("features", [])))
    M = ns["BK_M"]
    blat, blon = 230.0 / M, -420.0 / M                    # the sleeping spot «Am Rand des Riedmoos» (x -420, z -230)
    pb = jget("/api/karte/wildcamp/punkt?lat=%.7f&lon=%.7f&datum=2026-11-22&lang=de" % (blat, blon), HK)[1]
    ok(pb.get("berg") and pb["zones"] and pb["zones"][0]["text"] == "Wildruhezone «Riedmoos-Schwarzseeli» – Betreten 1.11.–30.4. verboten (verbindlich) · erfunden (Bergtal)"
       and pb["zones"][0]["aktiv"] and pb["zones"][0]["erf"] and "kanton" not in pb, "Bergtal: Schlafplatz Riedmoos -> " + (pb["zones"][0]["text"] if pb.get("zones") else "?"))
    pg2 = jget("/api/karte/wildcamp/punkt?lat=%.7f&lon=%.7f&datum=2026-11-22&lang=de" % (0.0, 60.0 / M), HK)[1]
    ok(pg2.get("berg") and pg2["zones"] == [], "Bergtal: Alp Tschuggen in keiner Zone")
    code, r = jpost("/api/karte/wildcamp/linie", {"pts": [[300 / M, -500 / M], [150 / M, -350 / M]], "datum": "2026-11-22", "lang": "de"}, HA)
    ok(code == 200 and len(r["segs"]) == 1 and "Riedmoos" in r["segs"][0]["text"], "Bergtal: Tour durch die erfundene Zone -> Abschnitt")
    gr = jget("/api/karte/wildcamp/punkt?lat=%.7f&lon=%.7f&datum=2026-11-22&lang=de" % (-150 / M, -560 / M), HK)[1]
    ok(gr["zones"] and not gr["zones"][0]["aktiv"] and "Gratspitz" in gr["zones"][0]["text"] and "durchqueren nur" in gr["zones"][0]["text"],
       "Bergtal: Gratspitz am 22.11. ausserhalb der Schutzzeit (blass)")
    srv.httpd.shutdown()
    shutil.rmtree(home, ignore_errors=True)


# ---- B) in the browser --------------------------------------------------------------------------------------------------------------
def gepatcht(datei, tmp, wc, bk, kqpins, url):
    import karten_test as KA
    d1 = KA.gepatcht(datei, tmp, kqpins, url)              # the test files of the Swiss map (karten_test)
    src = open(d1, encoding="utf-8").read()
    neu = 'WC_FILE = {"name": "%s", "size": %d, "sha256": "%s", "unpacked": %d, "datum": "2026-11-22"}' % (WP.NAME, len(wc[0]), hashlib.sha256(wc[0]).hexdigest(), wc[1])
    src, n = re.subn(r'^WC_FILE = \{[^\n]*\}$', neu, src, count=1, flags=re.M)
    alt = 'WC_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/"}'
    assert n == 1 and src.count(alt) == 1
    src = src.replace(alt, "WC_BASE = {\"url\": %s}" % json.dumps(url), 1)
    neu = 'BK_FILE = {"name": "%s", "size": %d, "sha256": "%s", "unpacked": %d, "sim": "test"}' % (bk[2], len(bk[0]), hashlib.sha256(bk[0]).hexdigest(), bk[1])
    src, n = re.subn(r'^BK_FILE = \{[^\n]*\}$', neu, src, count=1, flags=re.M)
    alt = 'BK_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/"}'
    assert n == 1 and src.count(alt) == 1
    src = src.replace(alt, "BK_BASE = {\"url\": %s}" % json.dumps(url), 1)
    open(d1, "w", encoding="utf-8").write(src)
    return d1


def teil_b(datei, wc, bk, web, bilder):
    from playwright.sync_api import sync_playwright
    from piper_test import Srv
    import karten_test as KA
    print("B) im Browser (390 px DPR 2 und PC)", flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_wc_b_")
    P, rel, pins, _tiles = KA.dateien_bauen(tmp, web)
    srv = Srv()
    for r_, f in pins.items():
        srv.files["/" + f["tag"] + "/" + f["name"]] = open(os.path.join(rel, f["name"]), "rb").read()
    srv.files["/wildcamp-1/" + WP.NAME] = wc[0]
    srv.files["/" + bk[3] + "/" + bk[2]] = bk[0]
    d2 = gepatcht(datei, tmp, wc, bk, pins, srv.url)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    PW = "Wild-" + os.urandom(4).hex()
    p, cfg = KA.starte(d2, tmp, port, PW, {"latitude": PLAUN[0] - 0.01, "longitude": PLAUN[1] - 0.02, "tausch_on": True})
    base = f"http://127.0.0.1:{port}"
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, data=None, user=("admin", PW)):
        hd = {"Authorization": "Basic " + base64.b64encode(f"{user[0]}:{user[1]}".encode()).decode(), "Content-Type": "application/json", "Origin": base}
        r = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers=hd)
        try:
            with op.open(r, timeout=60) as x:
                return x.status, json.loads(x.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, {}
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
        for what in ("/api/karte", "/api/karte/berg"):         # the Swiss test map and the Bergtal package: loaded like by the administrator
            req(what, {"action": "install"})
        for _i in range(240):
            if req("/api/karte")[1].get("on") and req("/api/karte/berg")[1].get("on"):
                break
            time.sleep(0.5)
        ok(req("/api/karte")[1].get("on") and req("/api/karte/berg")[1].get("on"), "Offline-Karte (Testdateien) und Bergtal-Paket installiert")
        code, tr_ = req("/api/touren", {"action": "save", "name": "Durch Alp Plaun", "pts": [[PLAUN[0] - 0.03, PLAUN[1]], [PLAUN[0] + 0.03, PLAUN[1] + 0.002]], "lang": "de"})
        tid = (tr_.get("tour") or {}).get("id", "")
        ok(code == 200 and tid, "Testtour gespeichert")
        os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=KA.ARGS)
            aussen = []

            def kontext(mob, user=("admin", PW)):
                vp = {"width": 390, "height": 844} if mob else {"width": 1366, "height": 900}
                ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                     http_credentials={"username": user[0], "password": user[1]}, locale="de-CH")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','light');localStorage.setItem('mw-kq-welt','ch');"
                                    "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\",\"settings\",\"rec\",\"history\",\"sim\",\"protect\",\"zones\",\"cams\",\"place\",\"tools\"]')}catch(e){}")
                ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:"))
                          else (aussen.append(r.request.url[:120]), r.abort()))
                return ctx
            breit = "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
            # the install button (administrator, phone)
            ctx = kontext(True); pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.goto(base + "/karte?welt=ch")
            pg.wait_for_selector("#wc-install", timeout=60000)
            t = pg.inner_text("#wc")
            ok("Wildcamp herunterladen" in t and "MB" in t, "/karte: Knopf «Wildcamp herunterladen (… MB)»")
            pg.locator("#wc").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(bilder, "wildcamp_laden_390.png"))
            pg.tap("#wc-install"); pg.wait_for_timeout(300)
            ok("jetzt laden" in pg.inner_text("#wc-install") and "feste Prüfsumme" in pg.inner_text("#wc-install"), "erster Tipp: Rückfrage mit Grösse und «feste Prüfsumme»")
            pg.tap("#wc-install"); t0 = time.time(); st_ = {}
            for _i in range(120):
                st_ = req("/api/karte/wildcamp")[1]
                if st_.get("on"):
                    break
                time.sleep(0.5)
            ok(st_.get("on"), "über den Knopf geladen (Grösse + sha256 geprüft) in %.1f s %s" % (time.time() - t0, "" if st_.get("on") else json.dumps(st_.get("dl"))[:200]))
            pg.wait_for_timeout(1500)
            ctx.close()
            for mob, name in ((True, "390"), (False, "pc")):
                ctx = kontext(mob); pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                tap = (lambda sel: pg.tap(sel)) if mob else (lambda sel: pg.click(sel))
                pg.goto(base + "/karte?welt=ch&lat=%s&lon=%s&z=13&datum=2027-01-15" % (PLAUN[0], PLAUN[1]))
                pg.wait_for_function("() => window.KQMAP && KQMAP.loaded() && window.WC && WC.map && KQMAP.getLayer('wc-wrz-f')", timeout=90000)
                pg.wait_for_function("() => KQMAP.querySourceFeatures('wc-wrz').length > 0", timeout=30000)
                ok(pg.locator("#wc-kats .wc-chip").count() == 6 and pg.locator("#wc-leg").is_visible() and "kräftig" in pg.inner_text("#wc-leg") and pg.locator("#wc-lic").count() == 1,
                   f"[{name}] Ebene mit 6 Schaltern, Legende (kräftig / blass) und «Quellen und Lizenzen»")
                st = lambda: pg.evaluate("() => KQMAP.querySourceFeatures('wc-wrz').filter(f => String(f.properties.n).startsWith('Alp Plaun')).map(f => f.properties.a)")
                ok(st() and all(a == 1 for a in st()), f"[{name}] Datum 15.1.2027: Alp Plaun kräftig (a = 1)")
                pg.fill("#wc-datum", "2026-11-22"); pg.dispatch_event("#wc-datum", "change"); pg.wait_for_timeout(700)
                ok(st() and all(a == 0 for a in st()), f"[{name}] Datum 22.11.2026: Alp Plaun blass (a = 0)")
                pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'start'})"); pg.wait_for_timeout(500)
                pg.screenshot(path=os.path.join(bilder, f"wildcamp_blass_{name}.png"))
                pg.fill("#wc-datum", "2027-01-15"); pg.dispatch_event("#wc-datum", "change"); pg.wait_for_timeout(700)
                ok(st() and all(a == 1 for a in st()), f"[{name}] wieder 15.1.: kräftig")
                pg.screenshot(path=os.path.join(bilder, f"wildcamp_karte_{name}.png"))
                pg.locator("#wc").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(bilder, f"wildcamp_legende_{name}.png"))
                # tap -> card
                pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'start'})"); pg.wait_for_timeout(300)
                xy = pg.evaluate("([lo, la]) => { const p = KQMAP.project([lo, la]), r = document.getElementById('kq-c').getBoundingClientRect(); return [r.left + p.x, r.top + p.y]; }", [PLAUN[1] + 0.004, PLAUN[0] - 0.003])
                (pg.touchscreen.tap if mob else pg.mouse.click)(xy[0], xy[1])
                pg.wait_for_selector("#wc-mini", timeout=15000); pg.wait_for_selector("#wc-tap #wc-card", timeout=15000); pg.wait_for_timeout(400)
                ok(TEXT_PLAUN in pg.inner_text("#wc-mini"), f"[{name}] Antippen: kleine Karte auf der Karte mit der Zone")
                t = pg.inner_text("#wc-card")
                ok(TEXT_PLAUN in t and "jetzt in der Schutzzeit" in t and "Kanton GR" in t and "Regeln der Gemeinde beachten" in t and "keine Rechtsberatung" in t,
                   f"[{name}] Antippen: Karte mit Zone, Schutzzeit, Kanton und «keine Rechtsberatung»")
                pg.screenshot(path=os.path.join(bilder, f"wildcamp_antippen_{name}.png"))
                pg.locator("#wc-tap").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(bilder, f"wildcamp_antippen_details_{name}.png"))
                pg.evaluate("() => document.querySelectorAll('.maplibregl-popup').forEach(p => p.remove())")
                # a category switched off
                pg.locator("#wc-k-moor").scroll_into_view_if_needed(); tap("#wc-k-moor"); pg.wait_for_timeout(300)
                ok(pg.evaluate("() => KQMAP.getLayoutProperty('wc-moor-f', 'visibility') === 'none' && KQMAP.getLayoutProperty('wc-wrz-f', 'visibility') === 'visible'"),
                   f"[{name}] Schalter «Moore» aus: nur diese Ebene weg")
                tap("#wc-k-moor")
                # own place «tent» inside the zone -> hint «Nachtlager»
                if mob:
                    pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'start'})")
                    pg.wait_for_selector("#eo-bar button[data-sym=tent]", timeout=20000)
                    tap("#eo-bar button[data-sym=tent]"); pg.wait_for_timeout(300)
                    xy = pg.evaluate("([lo, la]) => { const p = KQMAP.project([lo, la]), r = document.getElementById('kq-c').getBoundingClientRect(); return [r.left + p.x, r.top + p.y]; }", [PLAUN[1] - 0.003, PLAUN[0] + 0.002])
                    pg.touchscreen.tap(xy[0], xy[1])
                    pg.wait_for_selector("#wc-place", timeout=20000); pg.wait_for_timeout(300)
                    t = pg.inner_text("#wc-place")
                    ok("Nachtlager in einem Schutzgebiet" in t and "Alp Plaun" in t, f"[{name}] Eigener Ort «Zelt» in der Zone: Hinweis «Nachtlager …»")
                    pg.locator("#wc-place").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                    pg.screenshot(path=os.path.join(bilder, f"wildcamp_nachtlager_{name}.png"))
                    if pg.locator("#eo-cx").count():
                        pg.locator("#eo-cx").click()
                # the saved tour -> crossed section
                pg.goto(base + "/karte?welt=ch&tour=%s&datum=2027-01-15" % tid)
                pg.wait_for_function("() => window.KQMAP && KQMAP.loaded() && window.WC && WC.map", timeout=90000)
                pg.wait_for_selector("#wc-tour", timeout=30000)
                t = pg.inner_text("#wc-tour")
                ok("Die Route quert Schutzgebiete" in t and re.search(r"km \d\.\d–\d\.\d: Wildruhezone «Alp Plaun", t) is not None, f"[{name}] Tour: Abschnitt «km … – …: Wildruhezone «Alp Plaun …»»")
                pg.locator("#wc-tour .wc-seg").first.scroll_into_view_if_needed(); pg.locator("#wc-tour .wc-seg").first.click(); pg.wait_for_timeout(800)
                ok(pg.evaluate("() => KQMAP.querySourceFeatures('wc-hl').length > 0"), f"[{name}] «Abschnitt zeigen» hebt den Abschnitt hervor")
                pg.locator("#wc-tour").scroll_into_view_if_needed(); pg.screenshot(path=os.path.join(bilder, f"wildcamp_tour_{name}.png"))
                pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'start'})"); pg.wait_for_timeout(400)
                pg.screenshot(path=os.path.join(bilder, f"wildcamp_tour_karte_{name}.png"))
                ok(pg.evaluate(breit), f"[{name}] nichts ragt seitlich hinaus")
                # Bergtal
                pg.goto(base + "/karte?welt=berg&datum=2026-11-22")
                pg.wait_for_function("() => window.KQMAP && KQMAP.loaded() && window.BK && BK.map && window.WC && WC.map && KQMAP.getLayer('wc-wrz-f')", timeout=90000)
                pg.wait_for_function("() => KQMAP.querySourceFeatures('wc-wrz').length >= 3", timeout=30000)
                ok(pg.locator("#wc-kats .wc-chip").count() == 1 and "Erfundene Wildruhezonen" in pg.inner_text("#wc-leg"), f"[{name}] Bergtal: Ebene mit den erfundenen Zonen")
                pg.evaluate("() => KQMAP.jumpTo({center: [-420 / 111195.0802, 230 / 111195.0802], zoom: 15.2})"); pg.wait_for_timeout(800)
                pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'start'})"); pg.wait_for_timeout(300)
                xy = pg.evaluate("() => { const p = KQMAP.project([-420 / 111195.0802, 230 / 111195.0802]), r = document.getElementById('kq-c').getBoundingClientRect(); return [r.left + p.x, r.top + p.y]; }")
                (pg.touchscreen.tap if mob else pg.mouse.click)(xy[0], xy[1])
                pg.wait_for_selector("#wc-mini", timeout=15000); pg.wait_for_selector("#wc-tap #wc-card", timeout=15000); pg.wait_for_timeout(400)
                t = pg.inner_text("#wc-card")
                ok("Riedmoos-Schwarzseeli" in t and "erfunden (Bergtal)" in t, f"[{name}] Bergtal: Antippen am Schlafplatz Riedmoos")
                pg.screenshot(path=os.path.join(bilder, f"wildcamp_bergtal_{name}.png"))
                ok(not errs, f"[{name}] keine JS-Fehler" + (": " + " | ".join(errs[:3]) if errs else ""))
                ctx.close()
            # a family member: sees the layer, no install / remove
            ctx = kontext(True, ("Anna", "anna-pass-1")); pg = ctx.new_page()
            pg.goto(base + "/karte?welt=ch")
            pg.wait_for_function("() => window.WC && WC.map && KQMAP.getLayer('wc-wrz-f')", timeout=90000)
            ok(pg.locator("#wc-del").count() == 0 and pg.locator("#wc-install").count() == 0 and pg.locator("#wc-kats .wc-chip").count() == 6,
               "Familie: Ebene ja, Laden / Entfernen nein")
            ctx.close()
            ok(not aussen, "keine Anfrage nach aussen" + (": " + ", ".join(aussen[:3]) if aussen else ""))
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(20)
        except Exception:
            p.kill()
        srv.httpd.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--roh", default="", help="echte Rohdaten (paket.py --holen)")
    ap.add_argument("--web", default="", help="karte-web-2.zip (sonst vom Release karten-2, Prüfsumme aus Teil 639zzq)")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--ohne-browser", action="store_true")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or neueste_datei())
    bilder = a.bilder or tempfile.mkdtemp(prefix="wildcamp_bilder_")
    print(f"Wildcamp · {os.path.basename(datei)}", flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_wc_")
    try:
        import bergkarte_test as BT
        roh = a.roh or erfundene_roh(os.path.join(tmp, "roh"))
        zp, data, unp = paket_bauen(roh, os.path.join(tmp, "aus"), bool(a.roh))
        web = None
        if not a.ohne_browser:
            web = BT.web_zip(a.web, tmp)
        BP, bdata, bunp = berg_paket(tmp, web)
        teil_a(datei, data, unp, (BP, bdata, bunp), bool(a.roh))
        if not a.ohne_browser and not a.roh:
            teil_b(datei, (data, unp), (bdata, bunp, BP.NAME, BP.TAG), web, bilder)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Bilder:", bilder)
    for f in FEHLER:
        print("FEHLER:", f)
    print("Wildcamp-Test:", "OK" if not FEHLER else f"{len(FEHLER)} Fehler")
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
