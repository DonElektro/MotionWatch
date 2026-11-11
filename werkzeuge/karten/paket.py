#!/usr/bin/env python3
"""MoveEye: builds the three files of the offline map of Switzerland («Offline-Karte Schweiz», part 639zzq).

They are release assets at the tag «karten-N» (never in the Git repository, together several hundred MB):

  karte-ch-N.pmtiles    vector map of Switzerland + Liechtenstein (Protomaps basemap, one PMTiles v3 file), cut from a
                        Protomaps daily build with `pmtiles extract --region schweiz.geojson --maxzoom Z` (range reads, the
                        planet is never downloaded); schweiz.geojson = Natural Earth 10 m (public domain) + ~4 km margin
  karte-web-N.zip       everything the browser needs, nothing from a CDN: MapLibre GL JS (BSD-3), the Protomaps style
                        «light» (code BSD-3, design CC0, icons MIT) as style.json, glyphs Noto Sans (OFL, only the Latin
                        ranges for de / fr / it / rm / en), sprites, LIZENZEN.txt
  orte-ch-N.sqlite.gz   the offline place search: places, peaks, passes, lakes, glaciers and streets of Switzerland and
                        Liechtenstein from OpenStreetMap (Geofabrik extracts, ODbL) with canton and municipality

  python3 -I werkzeuge/karten/paket.py --web --aus OUT                      # karte-web-N.zip (needs node + internet)
  python3 -I werkzeuge/karten/paket.py --kacheln --aus OUT [--datum JJJJMMTT] [--zoom auto|14|15] [--pmtiles BIN]
  python3 -I werkzeuge/karten/paket.py --orte --aus OUT --pbf a.osm.pbf [--pbf b.osm.pbf]   # needs osmium (pyosmium) + shapely
  python3 -I werkzeuge/karten/paket.py --pins --aus OUT                     # OUT/pins.txt: «PIN <rolle> name=… size=… sha256=… unpacked=…»
  python3 -I werkzeuge/karten/paket.py --eintragen OUT/pins.txt             # writes the pins into quelle/639zzq_offline_karten.py

The web ZIP is reproducible (pinned npm packages with their sha512, the assets at a fixed commit, sorted names, fixed time
stamps). The map and the places follow OpenStreetMap of the day of the build: the release is made once, its pins are then
written into the program (the workflow «Offline-Karten» never overwrites a release).
"""
import argparse
import base64
import datetime
import gzip
import hashlib
import io
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unicodedata
import urllib.request
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HIER))
TAG = "karten-1"
N = TAG.split("-")[1]
NAMEN = {"tiles": "karte-ch-%s.pmtiles" % N, "web": "karte-web-%s.zip" % N, "orte": "orte-ch-%s.sqlite.gz" % N}
QUELLE_TEIL = os.path.join(REPO, "quelle", "639zzq_offline_karten.py")

NPM = {   # name -> (version, tarball, integrity from the npm registry)
    "maplibre-gl": ("5.24.0", "https://registry.npmjs.org/maplibre-gl/-/maplibre-gl-5.24.0.tgz",
                    "sha512-ALyFxgtd5R+65UqZ/++lOqwWcC0SNho9c27fYSyLmG7AfnAul2o46F05aDJGPbFU57wos9dgcIySHs0Xe6ia3A=="),
    "@protomaps/basemaps": ("5.7.2", "https://registry.npmjs.org/@protomaps/basemaps/-/basemaps-5.7.2.tgz",
                            "sha512-K1Yk6bWdULulYg+R2QRVXx4NzJZan5YQhpejEG0c1/sXruJrfPIPZuakpf3jwAgVmjIRVQwAv+yRafDeN0aaUQ=="),
}
ASSETS = "https://raw.githubusercontent.com/protomaps/basemaps-assets/028c18f713baecad011301ff7a69acc39bcc2ae7/"
FONTS = ("Noto Sans Regular", "Noto Sans Medium", "Noto Sans Italic")
RANGES = ("0-255", "256-511", "8192-8447")      # Basic Latin + Latin-1, Latin Extended-A (œ, ŝ …), punctuation (– ’ …)
SPRITES = ("light.json", "light.png", "light@2x.json", "light@2x.png")
PMTILES_TOOL = "github.com/protomaps/go-pmtiles@v1.31.2"
BUILD_URL = "https://build.protomaps.com/%s.pmtiles"
ZOOM_AUTO_MAX = 800 * 1000 * 1000          # «auto»: z15 if the file stays below this, else z14
FIX_TIME = (1980, 1, 1, 0, 0, 0)


def log(*a):
    print(*a, flush=True)


def holen(url, ziel=None):
    req = urllib.request.Request(url, headers={"User-Agent": "MoveEye-Kartenbau"})
    with urllib.request.urlopen(req, timeout=120) as r:
        b = r.read()
    if ziel:
        with open(ziel, "wb") as f:
            f.write(b)
    return b


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---- the normalised search key (the SAME rules as kq_norm in quelle/639zzq; karten_test.py compares both) ----------------
_KQ_FOLD = {"ß": "ss", "ẞ": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe", "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "ð": "d", "þ": "th"}


def kq_norm(s, umlaut=False):
    """lower case, without accents (Zürich -> zurich; umlaut=True: zuerich), only a-z 0-9 and single spaces"""
    s = str(s or "")
    if umlaut:
        s = re.sub("[äÄ]", "ae", s); s = re.sub("[öÖ]", "oe", s); s = re.sub("[üÜ]", "ue", s)
    s = "".join(_KQ_FOLD.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"['’`´]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def kq_keys(name):
    """{key: w} of one name: the whole name (w=0) and every later word (w=1), also with ä -> ae"""
    out = {}
    for um in (False, True):
        k = kq_norm(name, um)
        if not k:
            continue
        out[k] = 0
        ws = k.split(" ")
        for i in range(1, len(ws)):
            sub = " ".join(ws[i:])
            if len(sub) >= 2 and sub not in out:
                out[sub] = 1
    return out


# ---- the place index (SQLite) ------------------------------------------------------------------------------------------
KIND_RANG = {"city": 900, "town": 700, "village": 500, "suburb": 420, "quarter": 360, "neighbourhood": 320, "hamlet": 300,
             "locality": 230, "isolated_dwelling": 150, "farm": 130, "island": 300, "islet": 160, "peak": 380, "volcano": 380,
             "saddle": 330, "pass": 420, "lake": 300, "reservoir": 280, "glacier": 360, "street": 60}
SCHEMA = """
CREATE TABLE info (k TEXT PRIMARY KEY, v TEXT) WITHOUT ROWID;
CREATE TABLE ort (id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
                  rank INTEGER NOT NULL, gem TEXT, kt TEXT, ele INTEGER, alt TEXT);
CREATE TABLE such (k TEXT NOT NULL, id INTEGER NOT NULL, w INTEGER NOT NULL, r INTEGER NOT NULL, PRIMARY KEY (k, id)) WITHOUT ROWID;
"""


def rang(e):
    r = KIND_RANG.get(e["kind"], 100)
    pop = e.get("pop") or 0
    if pop > 0:
        r += min(260, int(45 * math.log10(1 + pop)))
    if e.get("ele") and e["kind"] in ("peak", "volcano", "saddle", "pass"):
        r += min(480, int(e["ele"]) // 10)
    if e.get("km2"):
        r += min(320, int(80 * math.log10(1 + 10 * e["km2"])))
    return r


def index_bauen(eintraege, ziel, info):
    """eintraege: dicts {name, alts, kind, lat, lon, gem, kt, ele, pop, km2}; writes ziel (SQLite, VACUUMed)"""
    if os.path.exists(ziel):
        os.remove(ziel)
    db = sqlite3.connect(ziel)
    db.executescript(SCHEMA)
    for k, v in sorted(info.items()):
        db.execute("INSERT INTO info VALUES (?, ?)", (k, str(v)))
    eintraege = sorted(eintraege, key=lambda e: (-rang(e), e["name"], e["lat"], e["lon"]))   # same order -> same file
    n = 0
    for i, e in enumerate(eintraege, 1):
        r = rang(e)
        alts = sorted({a for a in (e.get("alts") or []) if a and a != e["name"]})
        db.execute("INSERT INTO ort VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (i, e["name"], e["kind"], round(e["lat"], 5), round(e["lon"], 5), r, e.get("gem") or None, e.get("kt") or None,
                    int(e["ele"]) if e.get("ele") else None, "|".join(alts) or None))
        keys = {}
        for nm in [e["name"]] + alts:
            for k, w in kq_keys(nm).items():
                keys[k] = min(w, keys.get(k, 9))
        if e["kind"] == "street" and e.get("gem"):
            for k, w in kq_keys(e["name"] + " " + e["gem"]).items():
                if w == 0:
                    keys.setdefault(k, 0)
        for k, w in keys.items():
            db.execute("INSERT OR IGNORE INTO such VALUES (?,?,?,?)", (k, i, w, r))
        n += 1
    db.execute("INSERT OR REPLACE INTO info VALUES ('anzahl', ?)", (str(n),))
    db.commit()
    db.execute("VACUUM")
    db.close()
    return n


def gz_fest(src, dst):
    """gzip without name and time (the same input gives the same bytes)"""
    with open(src, "rb") as f, open(dst, "wb") as out:
        with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=9) as z:
            shutil.copyfileobj(f, z, 1 << 20)


# ---- OpenStreetMap -> entries (pyosmium + shapely; only in the workflow) -----------------------------------------------------
def osm_eintraege(pbfs, tmp):
    import osmium
    from shapely import wkb as swkb
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    wkbf = osmium.geom.WKBFactory()
    roh, strassen, kantone, gemeinden = [], {}, [], []
    STRASSE = {"residential", "living_street", "pedestrian", "unclassified", "tertiary", "secondary", "primary", "trunk", "road"}
    LANG = ("name:de", "name:fr", "name:it", "name:rm", "name:gsw", "name:en", "alt_name", "official_name", "short_name", "loc_name", "old_name")

    def namen(tags):
        al = []
        for k in LANG:
            v = tags.get(k)
            if v:
                al += [x.strip() for x in v.split(";") if x.strip()]
        return al

    def ele(tags):
        m = re.match(r"\s*(\d{2,4})(?:[.,]\d+)?\s*(m)?\s*$", tags.get("ele") or "")
        return int(m.group(1)) if m else None

    def pop(tags):
        m = re.match(r"\s*(\d[\d' ]*)", tags.get("population") or "")
        return int(re.sub(r"\D", "", m.group(1))) if m else 0

    class H(osmium.SimpleHandler):
        def node(self, n):
            t = n.tags
            nm = t.get("name")
            if not nm or not n.location.valid():
                return
            kind = None
            if t.get("place") in KIND_RANG:
                kind = t["place"]
            elif t.get("natural") in ("peak", "volcano", "saddle"):
                kind = t["natural"]
            elif t.get("mountain_pass") == "yes":
                kind = "pass"
            if kind:
                roh.append({"name": nm, "alts": namen(t), "kind": kind, "lat": n.location.lat, "lon": n.location.lon,
                            "ele": ele(t), "pop": pop(t)})

        def way(self, w):
            t = w.tags
            nm = t.get("name")
            if not nm or t.get("highway") not in STRASSE:
                return
            try:
                locs = [x.location for x in w.nodes if x.location.valid()]
            except osmium.InvalidLocationError:
                return
            if not locs:
                return
            m = locs[len(locs) // 2]
            k = nm
            strassen.setdefault(k, []).append((m.lat, m.lon, len(locs), namen(t)))

        def area(self, a):
            t = a.tags
            try:
                if t.get("boundary") == "administrative":
                    lv = t.get("admin_level")
                    iso = t.get("ISO3166-2") or ""
                    if lv == "4" and iso.startswith("CH-"):
                        kantone.append((swkb.loads(wkbf.create_multipolygon(a), hex=True), iso[3:]))
                    elif lv == "2" and t.get("ISO3166-1") == "LI":
                        kantone.append((swkb.loads(wkbf.create_multipolygon(a), hex=True), "FL"))
                    elif lv == "8" and t.get("name"):
                        gemeinden.append((swkb.loads(wkbf.create_multipolygon(a), hex=True), t["name"]))
                    return
                nm = t.get("name")
                if not nm:
                    return
                kind = None
                if t.get("natural") == "water" and t.get("water") in ("lake", "reservoir", "pond", "basin", None):
                    kind = "reservoir" if t.get("water") == "reservoir" else "lake"
                elif t.get("natural") == "glacier":
                    kind = "glacier"
                elif t.get("place") in ("island", "islet"):
                    kind = t["place"]
                if not kind:
                    return
                g = swkb.loads(wkbf.create_multipolygon(a), hex=True)
                p = g.representative_point()
                km2 = g.area * 111.32 * 111.32 * math.cos(math.radians(p.y))
                roh.append({"name": nm, "alts": namen(t), "kind": kind, "lat": p.y, "lon": p.x, "km2": round(km2, 3)})
            except Exception as e:                       # a broken polygon: skip it
                log("  Fläche übersprungen:", t.get("name"), e.__class__.__name__)

    for p in pbfs:
        log("lese", p)
        H().apply_file(p, locations=True, idx="flex_mem")
    log("roh: %d Orte, %d Strassennamen, %d Kantone, %d Gemeinden" % (len(roh), len(strassen), len(kantone), len(gemeinden)))
    for name, teile in strassen.items():               # one entry per street name and municipality (below), the longest piece
        for lat, lon, n, al in teile:
            roh.append({"name": name, "alts": al, "kind": "street", "lat": lat, "lon": lon, "_n": n})

    def zuordnen(polys):
        if not polys:
            return [None] * len(roh)
        tree = STRtree([p for p, _ in polys])
        pts = [Point(e["lon"], e["lat"]) for e in roh]
        out = [None] * len(roh)
        a, b = tree.query(pts, predicate="within")
        for i, j in zip(a, b):
            out[i] = polys[j][1]
        return out

    for e, kt, gem in zip(roh, zuordnen(kantone), zuordnen(gemeinden)):
        e["kt"] = kt
        e["gem"] = gem
    aus, seen = [], {}
    for e in roh:
        if not e["kt"]:                                 # outside Switzerland / Liechtenstein (the Geofabrik extract has a margin)
            continue
        if e["kind"] == "street":
            k = (e["name"], e["gem"] or "", e["kt"])
            alt = seen.get(k)
            if alt is None:
                seen[k] = e; aus.append(e)
            elif e["_n"] > alt["_n"]:
                alt.update(lat=e["lat"], lon=e["lon"], _n=e["_n"])
            continue
        if (e["kind"] in ("city", "town", "village") and e.get("gem") == e["name"]) or e["kind"] in ("lake", "reservoir", "glacier"):
            e["gem"] = None                             # «Seon» in «Seon»: say it once; a lake lies in several municipalities
        aus.append(e)
    for e in aus:
        e.pop("_n", None)
    return aus


# ---- the web package ------------------------------------------------------------------------------------------------------------
def npm_holen(name, tmp):
    ver, url, integ = NPM[name]
    b = holen(url)
    algo, want = integ.split("-", 1)
    got = base64.b64encode(hashlib.new(algo, b).digest()).decode()
    if got != want:
        sys.exit("%s %s: Prüfsumme falsch (%s statt %s)" % (name, ver, got, want))
    d = os.path.join(tmp, name.replace("/", "_"))
    with tarfile.open(fileobj=io.BytesIO(b)) as t:
        t.extractall(d, filter="data")
    return os.path.join(d, "package")


STYLE_JS = r"""
import {layers, namedFlavor} from %s;
// the local names (Switzerland: Genève, Zürich, Lugano, Sumvitg - like the Swiss maps) for every language of MoveEye
const L = layers("protomaps", namedFlavor("light"), {lang: "de"}).filter(l => l.id !== "landcover");
const s = JSON.stringify({version: 8, name: "MoveEye Offline-Karte Schweiz (Protomaps light)",
  sources: {protomaps: {type: "vector", tiles: ["{TILES}"], minzoom: 0, maxzoom: %d, attribution: "{ATTR}"}},
  glyphs: "{GLYPHS}", sprite: "{SPRITE}", layers: L}).replaceAll('"name:de"', '"name"');
process.stdout.write(s);
"""


def baue_web(aus, maxzoom=15):
    tmp = tempfile.mkdtemp(prefix="karte-web-")
    try:
        ml = npm_holen("maplibre-gl", tmp)
        bm = npm_holen("@protomaps/basemaps", tmp)
        node = shutil.which("node")
        if not node:
            sys.exit("node fehlt (für den Stil von Protomaps)")
        js = STYLE_JS % (json.dumps("file://" + os.path.join(bm, "dist", "esm", "index.js")), maxzoom)
        style = subprocess.run([node, "--input-type=module", "-e", js], check=True, capture_output=True).stdout.decode()
        st = json.loads(style)
        fonts_used = set()
        for ly in st["layers"]:
            f = (ly.get("layout") or {}).get("text-font")
            for x in re.findall(r'"(Noto Sans [^"]+)"', json.dumps(f)) if f else []:
                fonts_used.add(x)
        dateien = {}                                    # name in the ZIP -> bytes
        dateien["style.json"] = json.dumps(st, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        for f in ("maplibre-gl.js", "maplibre-gl.css"):
            with open(os.path.join(ml, "dist", f), "rb") as fh:
                b = fh.read()
            dateien[f] = b
            bio = io.BytesIO()
            with gzip.GzipFile(filename="", mode="wb", fileobj=bio, mtime=0, compresslevel=9) as z:
                z.write(b)
            dateien[f + ".gz"] = bio.getvalue()
        for fo in FONTS:
            for r in RANGES:
                dateien["fonts/%s/%s.pbf" % (fo, r)] = holen(ASSETS + "fonts/" + urllib.request.quote(fo) + "/" + r + ".pbf")
        for s in SPRITES:
            dateien["sprites/" + s] = holen(ASSETS + "sprites/v4/" + s)
        lic = {"maplibre": open(os.path.join(ml, "LICENSE.txt"), encoding="utf-8").read(),
               "ofl": holen(ASSETS + "fonts/OFL.txt").decode("utf-8")}
        dateien["LIZENZEN.txt"] = lizenzen(lic, sorted(fonts_used)).encode()
        dateien["karte.json"] = json.dumps({"tag": TAG, "maplibre": NPM["maplibre-gl"][0], "basemaps": NPM["@protomaps/basemaps"][0],
                                            "assets": ASSETS.rstrip("/").rsplit("/", 1)[1], "fonts": list(FONTS), "ranges": list(RANGES),
                                            "maxzoom": maxzoom}, sort_keys=True).encode()
        os.makedirs(aus, exist_ok=True)
        z = os.path.join(aus, NAMEN["web"])
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for n in sorted(dateien):
                i = zipfile.ZipInfo(n, FIX_TIME)
                i.external_attr = 0o644 << 16
                i.compress_type = zipfile.ZIP_STORED if n.endswith((".gz", ".png", ".pbf")) else zipfile.ZIP_DEFLATED
                zf.writestr(i, dateien[n])
        log("web:", z, os.path.getsize(z), "Bytes,", len(dateien), "Dateien, Schriften", sorted(fonts_used))
        return z
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def lizenzen(lic, fonts):
    return """MoveEye – Offline-Karte Schweiz (%s): Quellen und Lizenzen
=====================================================================

KARTENDATEN (karte-ch-%s.pmtiles) und ORTSSUCHE (orte-ch-%s.sqlite.gz)
  © OpenStreetMap-Mitwirkende – Open Database License (ODbL) 1.0, https://www.openstreetmap.org/copyright
  Die Karte ist ein «Produced Work» der Protomaps-Basiskarte (https://github.com/protomaps/basemaps, täglicher Build von
  https://build.protomaps.com), ausgeschnitten für die Schweiz und Liechtenstein (werkzeuge/karten/schweiz.geojson).
  Darin auch: Natural Earth (gemeinfrei), Wasser- und Landflächen von osmdata.openstreetmap.de (ODbL),
  Landbedeckung «landcover» aus ESA WorldCover (CC BY 4.0, © ESA WorldCover project / Daylight / Overture) – im Stil
  von MoveEye nicht angezeigt.
  Die Ortssuche stammt aus den OpenStreetMap-Auszügen von Geofabrik (https://download.geofabrik.de, ODbL).
  Anzeige: «© OpenStreetMap-Mitwirkende» steht auf jeder Karte von MoveEye.

KARTENSTIL (style.json): Protomaps basemaps %s – Code BSD-3-Clause (© 2019-2023 Protomaps LLC, Kelso Cartography),
  Gestaltung CC0 1.0 (Geraldine Sarmiento für Protomaps LLC), Ebenen-Schema nach Tilezen (MIT, © Mapzen / Linux Foundation).
  Geändert für MoveEye: lokale Ortsnamen («name» statt «name:de»), ohne die Ebene «landcover».

SYMBOLE (sprites/): protomaps/basemaps-assets, abgeleitet von tangrams/icons – MIT License, © 2017 Mapzen, Linux Foundation.

SCHRIFTEN (fonts/): %s – SIL Open Font License 1.1 (Text unten), als Glyphen-PBF aus protomaps/basemaps-assets
  (nur die Bereiche %s).

PROGRAMM (maplibre-gl.js, maplibre-gl.css): MapLibre GL JS %s – BSD-3-Clause (Text unten).

---------------------------------------------------------------------
MapLibre GL JS – LICENSE.txt
---------------------------------------------------------------------
%s
---------------------------------------------------------------------
Protomaps basemaps – BSD-3-Clause
---------------------------------------------------------------------
Copyright 2019-2023 Protomaps LLC, Kelso Cartography

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

---------------------------------------------------------------------
tangrams/icons – MIT License
---------------------------------------------------------------------
Copyright (c) 2017 Mapzen, Linux Foundation

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---------------------------------------------------------------------
Noto Sans – SIL Open Font License 1.1 (OFL.txt)
---------------------------------------------------------------------
%s
""" % (TAG, N, N, NPM["@protomaps/basemaps"][0], ", ".join(fonts), ", ".join(RANGES), NPM["maplibre-gl"][0],
       lic["maplibre"].strip(), lic["ofl"].strip())


# ---- the map tiles -------------------------------------------------------------------------------------------------------------
def neuester_build(datum=None):
    if datum:
        return datum
    heute = datetime.date.today()
    for i in range(0, 15):
        d = (heute - datetime.timedelta(days=i)).strftime("%Y%m%d")
        try:
            req = urllib.request.Request(BUILD_URL % d, method="HEAD", headers={"User-Agent": "MoveEye-Kartenbau"})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200 and int(r.headers.get("Content-Length") or 0) > 10 ** 10:
                    return d
        except Exception:
            pass
    sys.exit("kein Protomaps-Build der letzten 15 Tage gefunden")


def header_json(tool, p):
    out = subprocess.run([tool, "show", "--header-json", p], check=True, capture_output=True).stdout.decode()
    return json.loads(out)


def baue_kacheln(aus, tool, datum=None, zoom="auto"):
    os.makedirs(aus, exist_ok=True)
    d = neuester_build(datum)
    url = BUILD_URL % d
    region = os.path.join(HIER, "schweiz.geojson")
    z15 = os.path.join(aus, "ch-z15.pmtiles")
    z14 = os.path.join(aus, "ch-z14.pmtiles")
    log("Quelle:", url)
    subprocess.run([tool, "extract", url, z15, "--region=" + region, "--maxzoom=15", "--download-threads=8"], check=True)
    subprocess.run([tool, "extract", z15, z14, "--maxzoom=14"], check=True)
    for p in (z15, z14):
        subprocess.run([tool, "verify", p], check=True)
    s15, s14 = os.path.getsize(z15), os.path.getsize(z14)
    wahl = 15 if (zoom == "15" or (zoom == "auto" and s15 <= ZOOM_AUTO_MAX)) else 14
    ziel = os.path.join(aus, NAMEN["tiles"])
    shutil.copyfile(z15 if wahl == 15 else z14, ziel)
    h = header_json(tool, ziel)
    mess = {"datum": d, "quelle": url, "z15": s15, "z14": s14, "wahl": wahl, "header": h}
    with open(os.path.join(aus, "kacheln.json"), "w") as f:
        json.dump(mess, f, indent=1, sort_keys=True)
    log("Grössen: z15 = %.1f MB, z14 = %.1f MB -> gewählt z%d" % (s15 / 1e6, s14 / 1e6, wahl))
    return mess


# ---- pins --------------------------------------------------------------------------------------------------------------------------
def pins(aus):
    zeilen = []
    for rolle in ("tiles", "web", "orte"):
        p = os.path.join(aus, NAMEN[rolle])
        if not os.path.isfile(p):
            sys.exit("fehlt: " + p)
        unpacked = 0
        if rolle == "web":
            with zipfile.ZipFile(p) as z:
                unpacked = sum(i.file_size for i in z.infolist())
        elif rolle == "orte":
            with gzip.open(p, "rb") as g:
                for b in iter(lambda: g.read(1 << 20), b""):
                    unpacked += len(b)
        zeilen.append("PIN %s name=%s size=%d sha256=%s unpacked=%d" % (rolle, NAMEN[rolle], os.path.getsize(p), sha256(p), unpacked))
    extra = {}
    for f in ("kacheln.json", "orte.json"):
        q = os.path.join(aus, f)
        if os.path.isfile(q):
            extra.update(json.load(open(q)))
    if extra.get("wahl"):
        zeilen.append("INFO maxzoom=%s datum=%s z15=%s z14=%s" % (extra["wahl"], extra.get("datum"), extra.get("z15"), extra.get("z14")))
    if extra.get("anzahl"):
        zeilen.append("INFO orte=%s osm=%s" % (extra["anzahl"], extra.get("osm", "")))
    t = "\n".join(zeilen) + "\n"
    with open(os.path.join(aus, "pins.txt"), "w") as f:
        f.write(t)
    log(t)
    return t


def eintragen(pins_txt, teil=QUELLE_TEIL):
    """writes «"name": …, "size": …, "sha256": …, "unpacked": …» of every role into KQ_FILES of quelle/639zzq"""
    src = open(teil, encoding="utf-8").read()
    t = open(pins_txt, encoding="utf-8").read()
    for m in re.finditer(r"^PIN (\w+) name=(\S+) size=(\d+) sha256=([0-9a-f]{64}) unpacked=(\d+)", t, re.M):
        rolle, name, size, sha, unp = m.groups()
        neu = '"%s": {"name": "%s", "size": %s, "sha256": "%s", "unpacked": %s}' % (rolle, name, size, sha, unp)
        src, n = re.subn(r'"%s": \{"name": "[^"]*", "size": \d+, "sha256": "[0-9a-f]*", "unpacked": \d+\}' % rolle, neu, src)
        if n != 1:
            sys.exit("KQ_FILES[%s] nicht genau einmal gefunden" % rolle)
    m = re.search(r"^INFO maxzoom=(\d+)", t, re.M)
    if m:
        src, n = re.subn(r"^KQ_MAXZOOM = \d+", "KQ_MAXZOOM = " + m.group(1), src, flags=re.M)
    open(teil, "w", encoding="utf-8").write(src)
    log("eingetragen:", teil)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--aus", default="karten_aus")
    ap.add_argument("--web", action="store_true")
    ap.add_argument("--kacheln", action="store_true")
    ap.add_argument("--orte", action="store_true")
    ap.add_argument("--pins", action="store_true")
    ap.add_argument("--eintragen")
    ap.add_argument("--pbf", action="append", default=[])
    ap.add_argument("--datum")
    ap.add_argument("--zoom", default="auto", choices=("auto", "14", "15"))
    ap.add_argument("--pmtiles", default="pmtiles")
    a = ap.parse_args()
    if a.kacheln:
        m = baue_kacheln(a.aus, a.pmtiles, a.datum, a.zoom)
        mz = m["wahl"]
    else:
        mz = 15
        kj = os.path.join(a.aus, "kacheln.json")
        if os.path.isfile(kj):
            mz = json.load(open(kj))["wahl"]
    if a.web:
        baue_web(a.aus, mz)
    if a.orte:
        if not a.pbf:
            sys.exit("--orte braucht --pbf")
        tmp = tempfile.mkdtemp(prefix="orte-")
        try:
            ee = osm_eintraege(a.pbf, tmp)
            osm = []
            for p in a.pbf:
                try:
                    osm.append(os.path.basename(p) + ":" + subprocess.run(["osmium", "fileinfo", "-g", "header.option.osmosis_replication_timestamp", p],
                                                                         capture_output=True, check=True).stdout.decode().strip())
                except Exception:
                    osm.append(os.path.basename(p))
            sq = os.path.join(tmp, "orte.sqlite")
            n = index_bauen(ee, sq, {"tag": TAG, "quelle": "© OpenStreetMap-Mitwirkende (ODbL), Geofabrik", "osm": " ".join(osm)})
            gz_fest(sq, os.path.join(a.aus, NAMEN["orte"]))
            arten = {}
            for e in ee:
                arten[e["kind"]] = arten.get(e["kind"], 0) + 1
            with open(os.path.join(a.aus, "orte.json"), "w") as f:
                json.dump({"anzahl": n, "osm": " ".join(osm), "arten": arten, "sqlite": os.path.getsize(sq)}, f, indent=1, sort_keys=True)
            log("orte: %d Einträge, SQLite %.1f MB, gz %.1f MB" % (n, os.path.getsize(sq) / 1e6, os.path.getsize(os.path.join(a.aus, NAMEN["orte"])) / 1e6))
            log(json.dumps(arten, sort_keys=True))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if a.pins:
        pins(a.aus)
    if a.eintragen:
        eintragen(a.eintragen)


if __name__ == "__main__":
    main()
