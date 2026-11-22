#!/usr/bin/env python3
"""MoveEye: das Paket «Wildcamp» (Teil 639zzzzzw) - Schutzgebiete der Schweiz für die Offline-Karte, aus den offenen
Geodaten des Bundes (geo.admin.ch, Bundesamt für Umwelt BAFU / swisstopo).

Stufe 1  --holen ROH      lädt die Ebenen über die REST-Schnittstelle von geo.admin.ch (api3.geo.admin.ch «identify», Seiten
                          à 200 Objekte, LV95) - Wildruhezonen, Wildtierschutzgebiete (Teilgebiete der Jagdbanngebiete mit
                          Schutzzeit), eidgenössische Jagdbanngebiete, Schweizerischer Nationalpark, Wasser- und
                          Zugvogelreservate, Hoch- und Flachmoore, Moorlandschaften, Auengebiete, Kantonsgrenzen.
Stufe 2  --bauen ROH      vereinfacht (Douglas-Peucker in Metern), rechnet LV95 -> WGS84 (Näherung von swisstopo, ~1 m),
                          schreibt eine ZIP «wildcamp-ch-N.zip»:

  wildcamp.json     Kopf: Tag, Format, Datum, Zahlen je Ebene, Quellen mit Lizenz und Quellenangabe, eine Stichprobe
  zonen/<k>.json    GeoJSON je Kategorie (wrz, jb, snp, wzvv, moor, auen) - Eigenschaften kurz:
                      i Kennung · c Unterart (wrz, wsg, jb, snp, wzvv, hm, fm, ml, au) · n Name · z Schutzzeit wie in den
                      Daten · p [[MMTT von, MMTT bis] …] ([] = ganzjährig, fehlt = unbekannt) · s v verbindlich / e empfohlen ·
                      b Bestimmung (Kürzel) · r {de, fr, it} Bestimmung als Text · k Kanton · u Adresse (Objektblatt / Kanton)
                    plus «x»: [Westen, Süden, Osten, Norden] jedes Objekts (MoveEye sucht damit schnell)
  kantone.json      Kantonsgrenzen (vereinfacht, für «in welchem Kanton liegt der Punkt»)
  LIZENZEN.txt      Quellen und Lizenzen

  python3 -I werkzeuge/wildcamp/paket.py --holen ROH                         # Netz: nur api3.geo.admin.ch
  python3 -I werkzeuge/wildcamp/paket.py --bauen ROH --aus OUT --pins         # OUT/wildcamp-ch-N.zip + OUT/pins_wildcamp.txt
  python3 -I werkzeuge/wildcamp/paket.py --pruefen OUT                        # Zahlen, Grössen, Prüfsumme, bekannte Zone
  python3 -I werkzeuge/wildcamp/paket.py --eintragen OUT/pins_wildcamp.txt    # WC_FILE in quelle/639zzzzzw
Gleiche Rohdaten = gleiche Bytes (sortierte Namen, feste Zeitstempel). Die Daten des Bundes ändern sich laufend - ein neuer
Bau kann eine andere Prüfsumme haben; dann braucht es ein neues wildcamp-N (ein Release wird nie überschrieben).

Release (nur der Integrator; zwei Stufen wie die Bergtal-Karte 4.19.0, CLAUDE.md «Release in zwei Stufen»):
  Stufe 1  Quelle (Teil 639zzzzzw mit WC_FILE size 0 = «kommt mit einem Update») + gebaute Datei + Workflow auf main, OHNE
           Eintrag in versions.json, dazu vorstufe.json. Workflow «Wildcamp» von main mit release=echt, tag=wildcamp-1.
  Stufe 2  pins_wildcamp.txt -> `paket.py --eintragen pins_wildcamp.txt`, MoveEye bauen, signieren, vorstufe.json löschen.
"""
import argparse
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HIER))
TAG = "wildcamp-1"
NAME = "wildcamp-ch-%s.zip" % TAG.split("-")[1]
FORMAT = 1
QUELLE_TEIL = os.path.join(REPO, "quelle", "639zzzzzw_wildcamp.py")
FIX_TIME = (1980, 1, 1, 0, 0, 0)
API = "https://api3.geo.admin.ch/rest/services/api/MapServer/"
CH_BOX = "2480000,1070000,2840000,1300000"     # LV95: the whole of Switzerland (and Liechtenstein)
PAGE = 200                                      # identify returns at most ~200 objects per request
MAX_ZIP = 40 * 1000 * 1000                      # the host has 2 GB disk / 1.5 GB RAM: stay far below (MoveEye: WC_MAX)
OGD = "https://opendata.swiss/de/terms-of-use#terms_by"
GEO_TERMS = "https://www.geo.admin.ch/de/allgemeine-nutzungsbedingungen-bgdi"

# category -> what the map shows as one switch; sources: [key, layer, kind, simplification tolerance in metres]
EBENEN = [
    # key    layer (geo.admin.ch)                                category  tol  title / owner
    ("wrz", "ch.bafu.wrz-wildruhezonen_portal", "wrz", 8.0, "Wildruhezonen (Kantone, zusammengestellt vom BAFU)", "Kantone / BAFU"),
    ("wsg", "ch.bafu.wrz-jagdbanngebiete_select", "jb", 8.0, "Wildtierschutzgebiete (Schutzzeiten in den Jagdbanngebieten)", "BAFU"),
    ("jb", "ch.bafu.bundesinventare-jagdbanngebiete", "jb", 15.0, "Bundesinventar der eidgenössischen Jagdbanngebiete", "BAFU"),
    ("snp", "ch.bafu.schutzgebiete-paerke_nationaler_bedeutung", "snp", 10.0, "Schweizerischer Nationalpark (Pärke von nationaler Bedeutung, Kategorie SNP)", "BAFU"),
    ("wzvv", "ch.bafu.bundesinventare-vogelreservate", "wzvv", 10.0, "Bundesinventar der Wasser- und Zugvogelreservate (WZVV)", "BAFU"),
    ("hm", "ch.bafu.bundesinventare-hochmoore", "moor", 6.0, "Bundesinventar der Hoch- und Übergangsmoore", "BAFU"),
    ("fm", "ch.bafu.bundesinventare-flachmoore", "moor", 6.0, "Bundesinventar der Flachmoore", "BAFU"),
    ("ml", "ch.bafu.bundesinventare-moorlandschaften", "moor", 20.0, "Bundesinventar der Moorlandschaften", "BAFU"),
    ("au", "ch.bafu.bundesinventare-auen", "auen", 10.0, "Bundesinventar der Auengebiete", "BAFU"),
    ("kt", "ch.swisstopo.swissboundaries3d-kanton-flaeche.fill", "kantone", 60.0, "swissBOUNDARIES3D Kantonsgrenzen", "swisstopo"),
]
KATS = ("wrz", "jb", "snp", "wzvv", "moor", "auen")
KANTONE = ("ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR", "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR", "AG", "TG",
           "TI", "VD", "VS", "NE", "GE", "JU")
KT_NUM = {1: "ZH", 2: "BE", 3: "LU", 4: "UR", 5: "SZ", 6: "OW", 7: "NW", 8: "GL", 9: "ZG", 10: "FR", 11: "SO", 12: "BS", 13: "BL", 14: "SH",
          15: "AR", 16: "AI", 17: "SG", 18: "GR", 19: "AG", 20: "TG", 21: "TI", 22: "VD", 23: "VS", 24: "NE", 25: "GE", 26: "JU"}
# known objects the check looks for (name part, sub-kind, protection period of the data) - one per important layer
BEKANNT = [("Alp Plaun", "wrz", "20.12. - 30.04."), ("Augstmatthorn", "jb", None), ("Schweizerischer Nationalpark", "snp", None)]
MIN_N = {"wrz": 500, "jb": 40, "snp": 1, "wzvv": 20, "moor": 1000, "auen": 200, "kantone": 26}


def log(*a):
    print(*a, flush=True)


# ---- stage 1: fetch (only api3.geo.admin.ch) ----------------------------------------------------------------------------------------
def _get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MoveEye-Wildcamp-Paket/1", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:                        # network / 5xx: wait and again
            last = e
            time.sleep(3 + 5 * i)
    raise RuntimeError("geo.admin.ch nicht erreichbar: %s (%s)" % (url[:160], last))


def holen_ebene(key, layer):
    """every object of one layer: [{id, attributes, geometry (GeoJSON, LV95)}]"""
    out, seen, off = [], set(), 0
    if key == "snp":                                  # the Swiss National Park: the parks layer, category «SNP»
        q = urllib.parse.urlencode({"layer": layer, "searchText": "SNP", "searchField": "kategorie", "contains": "false", "returnGeometry": "true",
                                    "geometryFormat": "geojson", "sr": "2056", "lang": "de"})
        for f in _get(API + "find?" + q).get("results", []):
            a = f.get("attributes") or f.get("properties") or {}
            if a.get("kategorie") == "SNP":
                out.append({"id": f.get("id"), "attributes": a, "geometry": f.get("geometry")})
        return out
    while True:
        q = urllib.parse.urlencode({"geometryType": "esriGeometryEnvelope", "geometry": CH_BOX, "sr": "2056", "tolerance": "0", "lang": "de",
                                    "layers": "all:" + layer, "returnGeometry": "true", "geometryFormat": "geojson", "limit": str(PAGE), "offset": str(off)})
        r = _get(API + "identify?" + q).get("results", [])
        if not r:
            break
        for f in r:
            k = (f.get("layerBodId"), f.get("id"))
            if k in seen:
                continue
            seen.add(k)
            out.append({"id": f.get("id"), "attributes": f.get("properties") or f.get("attributes") or {}, "geometry": f.get("geometry")})
        off += len(r)
        time.sleep(0.3)                               # fair use of the free service
        if off > 200000:
            raise RuntimeError("zu viele Objekte in " + layer)
    return out


def holen(roh):
    os.makedirs(roh, exist_ok=True)
    meta = {"datum": time.strftime("%Y-%m-%d", time.gmtime()), "ebenen": {}}
    for key, layer, _k, _t, _ti, _o in EBENEN:
        t0 = time.time()
        F = holen_ebene(key, layer)
        with open(os.path.join(roh, key + ".json"), "w", encoding="utf-8") as fh:
            json.dump(F, fh, ensure_ascii=False, separators=(",", ":"))
        meta["ebenen"][key] = len(F)
        log("HOLEN %-5s %-55s %5d Objekte (%.0f s)" % (key, layer, len(F), time.time() - t0))
    with open(os.path.join(roh, "holen.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1, sort_keys=True)
    return meta


# ---- geometry -----------------------------------------------------------------------------------------------------------------------
def lv95_wgs84(e, n):
    """swisstopo «Näherungsformeln» LV95 -> WGS84 (accuracy about 1 m) -> (lon, lat)"""
    y, x = (e - 2600000.0) / 1e6, (n - 1200000.0) / 1e6
    lam = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y ** 3
    phi = 16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x - 0.0447 * y * y * x - 0.0140 * x ** 3
    return lam * 100.0 / 36.0, phi * 100.0 / 36.0


def dp(pts, tol):
    """Douglas-Peucker (iterative) on [(x, y)] in metres; the first and last point stay"""
    n = len(pts)
    if n < 3:
        return list(pts)
    keep = [False] * n
    keep[0] = keep[-1] = True
    st = [(0, n - 1)]
    t2 = tol * tol
    while st:
        a, b = st.pop()
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            if L == 0:
                d = (px - ax) ** 2 + (py - ay) ** 2
            else:
                t = ((px - ax) * dx + (py - ay) * dy) / L
                t = 0.0 if t < 0 else 1.0 if t > 1 else t
                d = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2
            if d > best:
                best, bi = d, i
        if best > t2:
            keep[bi] = True
            st.append((a, bi))
            st.append((bi, b))
    return [p for p, k in zip(pts, keep) if k]


def ring_area(r):
    return 0.5 * sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))


def simple_ring(r, tol):
    """a closed ring in LV95 -> simplified, closed, at least 4 points; None if it falls apart"""
    r = [(float(p[0]), float(p[1])) for p in r if isinstance(p, (list, tuple)) and len(p) >= 2]
    if len(r) < 4:
        return None
    if r[0] != r[-1]:
        r.append(r[0])
    # split the closed ring at its farthest point so Douglas-Peucker keeps the shape
    far = max(range(len(r)), key=lambda i: (r[i][0] - r[0][0]) ** 2 + (r[i][1] - r[0][1]) ** 2)
    s = dp(r[:far + 1], tol)[:-1] + dp(r[far:], tol)
    if len(s) < 4 or abs(ring_area(s)) < 1.0:
        return None
    return s


def to_ll(r):
    return [[round(c, 5) for c in lv95_wgs84(p[0], p[1])] for p in r]


def polys_of(g):
    """GeoJSON geometry -> list of polygons (list of rings), lines ignored"""
    if not isinstance(g, dict):
        return []
    t, c = g.get("type"), g.get("coordinates")
    if t == "Polygon":
        return [c]
    if t == "MultiPolygon":
        return list(c)
    if t == "GeometryCollection":
        return [p for gg in g.get("geometries", []) for p in polys_of(gg)]
    return []


def lines_of(g):
    if not isinstance(g, dict):
        return []
    t, c = g.get("type"), g.get("coordinates")
    if t == "LineString":
        return [c]
    if t == "MultiLineString":
        return list(c)
    return []


def geom(g, tol, linien=False):
    """-> (GeoJSON geometry in WGS84 or None, bbox [w, s, e, n])"""
    if linien:
        L = []
        for ln in lines_of(g):
            s = dp([(float(p[0]), float(p[1])) for p in ln], tol)
            if len(s) >= 2:
                L.append(to_ll(s))
        if not L:
            return None, None
        gg = {"type": "LineString", "coordinates": L[0]} if len(L) == 1 else {"type": "MultiLineString", "coordinates": L}
        allp = [p for ln in L for p in ln]
    else:
        P = []
        for poly in polys_of(g):
            if not poly:
                continue
            outer = simple_ring(poly[0], tol)
            if outer is None:
                continue
            holes = [h for h in (simple_ring(h, tol) for h in poly[1:]) if h is not None]
            P.append([to_ll(outer)] + [to_ll(h) for h in holes])
        if not P:
            return None, None
        gg = {"type": "Polygon", "coordinates": P[0]} if len(P) == 1 else {"type": "MultiPolygon", "coordinates": P}
        allp = [p for poly in P for p in poly[0]]
    xs, ys = [p[0] for p in allp], [p[1] for p in allp]
    return gg, [round(min(xs), 5), round(min(ys), 5), round(max(xs), 5), round(max(ys), 5)]


# ---- protection periods ---------------------------------------------------------------------------------------------------------------
_PER = re.compile(r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.?\s*(?:\d{2,4})?\s*(?:-|–|—|bis|au|al|a)\s*(\d{1,2})\s*\.\s*(\d{1,2})\s*\.?")


def perioden(s):
    """«20.12. - 30.04.» -> [["1220", "0430"]]; «ganzjährig» -> []; unknown -> None"""
    s = str(s or "").strip()
    if not s:
        return None
    low = s.lower()
    if any(w in low for w in ("ganzjährig", "ganzjaehrig", "toute l", "tutto l", "ganzes jahr", "1.1. - 31.12", "01.01. - 31.12")):
        return []
    out = []
    for m in _PER.finditer(s):
        d0, m0, d1, m1 = (int(x) for x in m.groups())
        if 1 <= m0 <= 12 and 1 <= m1 <= 12 and 1 <= d0 <= 31 and 1 <= d1 <= 31:
            out.append(["%02d%02d" % (m0, d0), "%02d%02d" % (m1, d1)])
    if out and all(p == ["0101", "1231"] for p in out):
        return []
    return out or None


def aktiv(p, mmdd):
    """is the date «MMDD» inside one of the periods (over the new year too)? [] = all year; None = unknown (cautious: yes)"""
    if p is None or p == []:
        return True
    for a, b in p:
        if (a <= b and a <= mmdd <= b) or (a > b and (mmdd >= a or mmdd <= b)):
            return True
    return False


# ---- stage 2: build -----------------------------------------------------------------------------------------------------------------
def _txt(v, n=200):
    s = " ".join(str(v or "").split())
    return s[:n]


def _url(v):
    s = str(v or "").strip()
    return s if re.match(r"^https://[A-Za-z0-9.-]+(/[^\s\"'<>]*)?$", s) and len(s) < 300 else ""


def _sv(s):
    s = str(s or "").lower()
    return "v" if "verbindlich" in s else "e" if "empfohl" in s else ""


def props(key, a):
    """the short properties of one object (see the head of this file)"""
    if key == "wrz":
        return {"c": "wrz", "n": _txt(a.get("wrz_name") or a.get("label")), "z": _txt(a.get("schutzzeit"), 80), "s": _sv(a.get("schutzs_de")),
                "b": _txt(a.get("bestimmung"), 12), "r": {"de": _txt(a.get("best_de")), "fr": _txt(a.get("best_fr")), "it": _txt(a.get("best_it"))},
                "k": _txt(a.get("kanton"), 4), "u": _url(a.get("url_kanton")), "g": _txt(a.get("grundlage"), 80)}
    if key == "wsg":
        return {"c": "wsg", "n": _txt(a.get("jb_name") or a.get("label")), "z": _txt(a.get("schutzzeit"), 80), "s": _sv(a.get("schutzs_de")),
                "b": _txt(a.get("bestimmung"), 12), "r": {"de": _txt(a.get("best_de")), "fr": _txt(a.get("best_fr")), "it": _txt(a.get("best_it"))},
                "k": _txt(a.get("kanton"), 4), "u": _url(a.get("url_kanton"))}
    if key == "jb":
        return {"c": "jb", "n": _txt(a.get("gebietsname") or a.get("label")), "t": _txt(a.get("typ_de"), 60), "o": _txt(a.get("objektnummer"), 12),
                "u": _url(a.get("refobjblatt")), "s": "v"}
    if key == "snp":
        return {"c": "snp", "n": _txt(a.get("name") or "Schweizerischer Nationalpark"), "s": "v", "u": "https://www.nationalpark.ch/de/schutzbestimmungen/"}
    if key == "wzvv":
        return {"c": "wzvv", "n": _txt(a.get("name") or a.get("label")), "t": _txt(a.get("schutzkategorie_de") or a.get("schutzebene_de"), 60),
                "o": _txt(a.get("objnummer"), 12), "u": _url(a.get("refobjblatt")), "s": "v"}
    if key in ("hm", "fm", "ml"):
        return {"c": key, "n": _txt(a.get("name") or a.get("label")), "o": _txt(a.get("objnummer"), 12), "u": _url(a.get("refobjblat")), "s": "v"}
    if key == "au":
        return {"c": "au", "n": _txt(a.get("name") or a.get("label")), "t": _txt(a.get("auen_type_de"), 60), "o": _txt(a.get("objnummer"), 12),
                "u": _url(a.get("refobjblat")), "s": "v"}
    raise KeyError(key)


def bauen(roh, aus):
    os.makedirs(aus, exist_ok=True)
    with open(os.path.join(roh, "holen.json"), encoding="utf-8") as fh:
        hm = json.load(fh)
    kat = {k: [] for k in KATS}
    kant = []
    zahlen = {}
    quellen = []
    for key, layer, k, tol, title, owner in EBENEN:
        with open(os.path.join(roh, key + ".json"), encoding="utf-8") as fh:
            F = json.load(fh)
        n = 0
        for o in sorted(F, key=lambda o: str(o.get("id"))):
            a = o.get("attributes") or {}
            if key == "kt":
                g, bb = geom(o.get("geometry"), tol)
                if g is None:
                    continue
                ak = str(a.get("ak") or "").upper() or KT_NUM.get(a.get("kantonsnum"), "")
                if ak not in KANTONE:
                    continue
                kant.append({"type": "Feature", "properties": {"k": ak, "n": _txt(a.get("name") or a.get("label"), 60), "x": bb}, "geometry": g})
                n += 1
                continue
            linie = key == "wrz" and (a.get("weg_id") is not None or a.get("wegtyp_de"))
            if linie:                                   # allowed routes inside the Wildruhezonen (shown dashed)
                g, bb = geom(o.get("geometry"), 5.0, linien=True)
                if g is None:
                    continue
                pr = {"c": "weg", "n": _txt(a.get("wegtyp_de"), 60), "r": {"de": _txt(a.get("wegtyp_de"), 60), "fr": _txt(a.get("wegtyp_fr"), 60),
                                                                           "it": _txt(a.get("wegtyp_it"), 60)}, "x": bb}
            else:
                g, bb = geom(o.get("geometry"), tol)
                if g is None:
                    continue
                pr = props(key, a)
                if "z" in pr:
                    pe = perioden(pr["z"])
                    if pe is not None:
                        pr["p"] = pe
                elif key in ("jb", "snp", "wzvv", "hm", "fm", "ml", "au"):
                    pr["p"] = []                        # all year (the inventories have no season)
                pr["x"] = bb
            pr = {kk: vv for kk, vv in pr.items() if vv not in ("", None) and vv != {"de": "", "fr": "", "it": ""}}
            pr["i"] = "%s.%s" % (key, o.get("id"))
            kat[k].append({"type": "Feature", "properties": pr, "geometry": g})
            n += 1
        zahlen[key] = n
        quellen.append({"key": key, "kat": k, "layer": layer, "titel": title, "von": owner, "objekte": n,
                        "quelle": "© " + ("BAFU" if owner == "BAFU" else "swisstopo" if owner == "swisstopo" else "Kantone / BAFU"),
                        "lizenz": "Open Government Data: freie Nutzung, Quellenangabe ist Pflicht (opendata.swiss «terms_by»)",
                        "lizenz_url": OGD, "daten": "https://map.geo.admin.ch/?layers=" + layer})
        log("BAUEN %-5s %5d Objekte" % (key, n))
    files = {}
    for k in KATS:
        fc = {"type": "FeatureCollection", "features": kat[k]}
        files["zonen/%s.json" % k] = json.dumps(fc, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    files["kantone.json"] = json.dumps({"type": "FeatureCollection", "features": sorted(kant, key=lambda f: f["properties"]["k"])},
                                       ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    probe = []
    for name, c, z in BEKANNT:
        hit = next((f for k in KATS for f in kat[k] if f["properties"].get("c") == c and name in f["properties"].get("n", "")), None)
        if hit:
            probe.append({"n": hit["properties"]["n"], "c": c, "z": hit["properties"].get("z"), "p": hit["properties"].get("p"), "x": hit["properties"]["x"]})
    counts = {k: len(kat[k]) for k in KATS}
    counts["kantone"] = len(kant)
    head = {"tag": TAG, "format": FORMAT, "datum": hm.get("datum"), "counts": counts, "zahlen": zahlen, "quellen": quellen, "probe": probe,
            "lv95": "LV95 -> WGS84 mit den Näherungsformeln von swisstopo (etwa 1 m), vereinfacht (Douglas-Peucker 6 - 20 m)"}
    files["wildcamp.json"] = json.dumps(head, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
    files["LIZENZEN.txt"] = lizenzen(head).encode("utf-8")
    zp = os.path.join(aus, NAME)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(files):
            zi = zipfile.ZipInfo(name, FIX_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, files[name])
    unp = sum(len(v) for v in files.values())
    log("PAKET %s %d Bytes (entpackt %d) %s" % (NAME, os.path.getsize(zp), unp, " ".join("%s=%d" % kv for kv in sorted(counts.items()))))
    return zp


def lizenzen(head):
    L = ["Wildcamp – Schutzgebiete der Schweiz für MoveEye (Paket %s, Daten vom %s)" % (head["tag"], head["datum"]), "",
         "Quellen und Lizenzen", "====================", "",
         "Alle Ebenen stammen aus den offenen Geodaten des Bundes (Geoportal des Bundes, geo.admin.ch), geholt über die",
         "REST-Schnittstelle api3.geo.admin.ch. Nutzungsbedingungen: " + GEO_TERMS,
         "Lizenz: Open Government Data «Freie Nutzung. Quellenangabe ist Pflicht.» (opendata.swiss terms_by): " + OGD, ""]
    for q in head["quellen"]:
        L += ["* %s" % q["titel"], "  Ebene: %s · %d Objekte" % (q["layer"], q["objekte"]), "  Quelle: %s · %s" % (q["quelle"], q["daten"]),
              "  Lizenz: %s" % q["lizenz"], ""]
    L += ["Die Wildruhezonen legen die Kantone fest (Quellenangabe «Kt. [BAFU]» wie im Geoportal); die Fassung des BAFU fasst sie zusammen.",
          "Kantonale Naturschutzgebiete: es gibt keinen gesamtschweizerischen Datensatz des Bundes - sie fehlen in diesem Paket.",
          "(Die Pro-Natura-Gebiete im Geoportal sind Daten eines Vereins mit eigenen Bedingungen und darum nicht dabei.)", "",
          "Bearbeitung: vereinfacht (Douglas-Peucker), umgerechnet LV95 -> WGS84 mit den Näherungsformeln von swisstopo (etwa 1 m).",
          "Die Linien können darum einige Meter von den amtlichen Grenzen abweichen. Massgebend sind die amtlichen Daten und die",
          "Signalisation vor Ort. Information, keine Rechtsberatung.", ""]
    return "\n".join(L)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pins(aus):
    zp = os.path.join(aus, NAME)
    with zipfile.ZipFile(zp) as z:
        unp = sum(i.file_size for i in z.infolist())
        head = json.loads(z.read("wildcamp.json"))
    line = "PIN wildcamp tag=%s name=%s size=%d sha256=%s unpacked=%d datum=%s" % (TAG, NAME, os.path.getsize(zp), sha256(zp), unp, head.get("datum"))
    with open(os.path.join(aus, "pins_wildcamp.txt"), "w", encoding="utf-8") as fh:
        fh.write(line + "\n")
    log(line)
    return line


def eintragen(pins_txt, teil=QUELLE_TEIL):
    with open(pins_txt, encoding="utf-8") as fh:
        m = re.search(r"^PIN wildcamp tag=(\S+) name=(\S+) size=(\d+) sha256=([0-9a-f]{64}) unpacked=(\d+) datum=(\S+)", fh.read(), re.M)
    if not m or m.group(1) != TAG:
        raise SystemExit("pins: keine Zeile «PIN wildcamp tag=%s …»" % TAG)
    with open(teil, encoding="utf-8") as fh:
        src = fh.read()
    neu = 'WC_FILE = {"name": "%s", "size": %s, "sha256": "%s", "unpacked": %s, "datum": "%s"}' % (m.group(2), m.group(3), m.group(4), m.group(5), m.group(6))
    src, n = re.subn(r'^WC_FILE = \{[^\n]*\}$', neu, src, count=1, flags=re.M)
    if n != 1:
        raise SystemExit("WC_FILE nicht gefunden in " + teil)
    with open(teil, "w", encoding="utf-8") as fh:
        fh.write(src)
    log("EINGETRAGEN " + neu)


def _inside(pt, ring):
    x, y, c = pt[0], pt[1], False
    for i in range(len(ring) - 1):
        (x1, y1), (x2, y2) = ring[i][:2], ring[i + 1][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def pruefen(aus, strikt=True):
    """the package: zip readable, sizes, every category with enough objects, the known zones with their periods, coordinates
    in Switzerland, no foreign files - prints PRUEFUNG lines; returns the list of errors"""
    err = []
    zp = os.path.join(aus, NAME)
    size = os.path.getsize(zp)
    if size > MAX_ZIP:
        err.append("Paket zu gross: %d > %d" % (size, MAX_ZIP))
    with zipfile.ZipFile(zp) as z:
        names = sorted(z.namelist())
        want = sorted(["wildcamp.json", "kantone.json", "LIZENZEN.txt"] + ["zonen/%s.json" % k for k in KATS])
        if names != want:
            err.append("Dateien: %s" % names)
        head = json.loads(z.read("wildcamp.json"))
        unp = sum(i.file_size for i in z.infolist())
        if head.get("tag") != TAG or head.get("format") != FORMAT:
            err.append("Kopf: tag/format")
        Z = {k: json.loads(z.read("zonen/%s.json" % k)) for k in KATS}
        K = json.loads(z.read("kantone.json"))
        lic = z.read("LIZENZEN.txt").decode("utf-8")
    for k in KATS:
        n = len(Z[k]["features"])
        if strikt and n < MIN_N[k]:
            err.append("%s: nur %d Objekte (mindestens %d)" % (k, n, MIN_N[k]))
        for f in Z[k]["features"]:
            p = f["properties"]
            x = p.get("x")
            if not (isinstance(x, list) and len(x) == 4 and 5.7 < x[0] <= x[2] < 10.7 and 45.7 < x[1] <= x[3] < 47.9):
                err.append("%s %s: Lage ausserhalb der Schweiz %s" % (k, p.get("i"), x))
                break
    ks = sorted(f["properties"]["k"] for f in K["features"])
    if strikt and sorted(set(ks)) != sorted(KANTONE):
        err.append("Kantone: %s" % ks)
    for name, c, z_ in BEKANNT if strikt else []:
        hit = [f for k in KATS for f in Z[k]["features"] if f["properties"].get("c") == c and name in f["properties"].get("n", "")]
        if not hit:
            err.append("bekannte Zone fehlt: %s (%s)" % (name, c))
            continue
        p = hit[0]["properties"]
        if z_ is not None and (p.get("z") != z_ or p.get("p") != perioden(z_)):
            err.append("%s: Schutzzeit %r / %r statt %r" % (name, p.get("z"), p.get("p"), z_))
        log("PRUEFUNG bekannt: %s · %s · Schutzzeit %s · %s" % (p.get("n"), c, p.get("z") or "ganzjährig", p.get("p")))
    if strikt:                                         # a point inside Alp Plaun is in Graubünden
        plaun = next((f for f in Z["wrz"]["features"] if "Alp Plaun" in f["properties"].get("n", "")), None)
        if plaun:
            g = plaun["geometry"]
            ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
            cx = sum(p[0] for p in ring[:-1]) / (len(ring) - 1)
            cy = sum(p[1] for p in ring[:-1]) / (len(ring) - 1)
            gr = [f for f in K["features"] if f["properties"]["k"] == "GR"]
            if gr and not any(_inside((cx, cy), poly[0]) for f in gr for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"])):
                log("PRUEFUNG Hinweis: Mitte von Alp Plaun nicht in GR (Form nicht konvex?)")
    for w in ("Quellenangabe ist Pflicht", "opendata.swiss", "geo.admin.ch", "BAFU", "swisstopo", "keine Rechtsberatung"):
        if w not in lic:
            err.append("LIZENZEN.txt ohne «%s»" % w)
    pin = os.path.join(aus, "pins_wildcamp.txt")
    if os.path.isfile(pin):
        with open(pin, encoding="utf-8") as fh:
            t = fh.read()
        if "size=%d " % size not in t or "sha256=%s " % sha256(zp) not in t or "unpacked=%d " % unp not in t:
            err.append("pins_wildcamp.txt passt nicht zum Paket")
    log("PRUEFUNG %s %d Bytes, entpackt %d, %s · %s" % (NAME, size, unp, " ".join("%s=%d" % (k, len(Z[k]["features"])) for k in KATS),
                                                     "OK" if not err else "FEHLER: " + "; ".join(err)))
    return err


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--holen", metavar="ROH")
    ap.add_argument("--bauen", metavar="ROH")
    ap.add_argument("--aus", default="wildcamp_aus")
    ap.add_argument("--pins", action="store_true")
    ap.add_argument("--pruefen", metavar="AUS")
    ap.add_argument("--locker", action="store_true", help="--pruefen ohne Mindestzahlen / bekannte Zonen (Test mit kleinen Daten)")
    ap.add_argument("--eintragen", metavar="PINS")
    a = ap.parse_args()
    if a.holen:
        holen(a.holen)
    if a.bauen:
        bauen(a.bauen, a.aus)
    if a.pins:
        pins(a.aus)
    if a.pruefen:
        if pruefen(a.pruefen, strikt=not a.locker):
            sys.exit(1)
    if a.eintragen:
        eintragen(a.eintragen)


if __name__ == "__main__":
    main()
