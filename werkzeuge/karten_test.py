#!/usr/bin/env python3
"""MoveEye: Test der Offline-Karte Schweiz (Teil 639zzq, werkzeuge/karten/paket.py).

  python3 werkzeuge/karten_test.py [--web karte-web-1.zip] [--bilder ORDNER] [--ohne-browser] [--datei X.py]
  python3 werkzeuge/karten_test.py --echt ORDNER [--bilder ORDNER]     # die echten Release-Dateien (Ausgabe von paket.py)

Ohne --echt: eine kleine Test-Karte (PMTiles v3 um Seon AG, mit Blattverzeichnissen und 3 MB Füllkacheln, hier erzeugt) und
eine kleine Ortssuche (paket.index_bauen). Geprüft: Selbsttest, gleiche Suchschlüssel in paket.py und MoveEye, Kachel-Nummern
(gegen die Python-Referenz pmtiles, falls installiert), Kacheln lesen nur die nötigen Bytes, Laden mit Prüfsumme (falsche
Datei abgelehnt, zu wenig Platz abgelehnt, kein halber Ordner), nur der Admin lädt / entfernt, Kacheln / Schriften / Web-Dateien
/ Suche über den Server («Seon» -> Seon AG, «Zurich» -> Zürich, «Genf» -> Genève, «zuerich»), Rechte eines Benutzers.
Im Browser (MoveEye als eigener Prozess, Laden über HTTP wie auf dem Gerät): /karte in iPhone-Breite und am PC (Karte
erscheint, Quellenangabe sichtbar, Suche, Tipp setzt den Standort), Einstellungen → Standort (Kasten, Tipp speichert die
Koordinaten), Aufnahme mit Ort (kleine Karte), «Ort von der Karte» des Simulators (sendet «lat, lon, Name») - jede Seite
OHNE Anfrage nach aussen. Mit --echt: Kopf, Grösse, Kachel von Seon (MVT mit den Ebenen von Protomaps), gelesene Bytes,
Suche im echten Verzeichnis, /karte mit den echten Dateien im Browser.
"""
import argparse
import base64
import glob
import gzip
import hashlib
import io
import json
import math
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
ARGS = ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl"]
SEON = (47.3475, 8.1602)
FEHLER = []


def ok(c, what):
    print(("  ✓ " if c else "  ✗ ") + what, flush=True)
    if not c:
        FEHLER.append(what)
    return c


def neueste_datei():
    c = sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    return c[-1]


def paket_modul():
    import importlib.util
    sp = importlib.util.spec_from_file_location("karten_paket", os.path.join(HIER, "karten", "paket.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# ---- a tiny vector tile (Mapbox Vector Tile 2.1) and a PMTiles v3 writer - only for the test ---------------------------------------
def _vi(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b); return bytes(out)


def _fld(num, wt, payload):
    return _vi((num << 3) | wt) + (_vi(len(payload)) + payload if wt == 2 else payload)


def _zz(n):
    return (n << 1) ^ (n >> 31)


def mvt(layers):
    """layers: {name: [(type 1|2|3, [[(x, y), …], …], {key: value})]} in tile units (extent 4096)"""
    out = b""
    for name, feats in layers.items():
        keys, vals, body = [], [], b""
        for typ, rings, props in feats:
            tags = []
            for k, v in props.items():
                if k not in keys:
                    keys.append(k)
                vk = ("s", v) if isinstance(v, str) else ("i", int(v))
                if vk not in vals:
                    vals.append(vk)
                tags += [keys.index(k), vals.index(vk)]
            geom, cx, cy = [], 0, 0
            for ring in rings:
                pts = ring[:-1] if typ == 3 and ring[0] == ring[-1] else ring
                x, y = pts[0]
                geom += [(1 | (1 << 3)), _zz(x - cx), _zz(y - cy)]; cx, cy = x, y
                if len(pts) > 1:
                    geom.append(2 | ((len(pts) - 1) << 3))
                    for x, y in pts[1:]:
                        geom += [_zz(x - cx), _zz(y - cy)]; cx, cy = x, y
                if typ == 3:
                    geom.append(7 | (1 << 3))
            f = _fld(2, 2, b"".join(_vi(t) for t in tags)) + _fld(3, 0, _vi(typ)) + _fld(4, 2, b"".join(_vi(g) for g in geom))
            body += _fld(2, 2, f)
        ly = _fld(15, 0, _vi(2)) + _fld(1, 2, name.encode()) + body
        for k in keys:
            ly += _fld(3, 2, k.encode())
        for t, v in vals:
            ly += _fld(4, 2, _fld(1, 2, v.encode()) if t == "s" else _fld(4, 0, _vi(v & ((1 << 64) - 1))))
        ly += _fld(5, 0, _vi(4096))
        out += _fld(3, 2, ly)
    return out


def mvt_layers(b):
    """the layer names of a vector tile (to check the real tiles)"""
    names, p = [], 0
    while p < len(b):
        key, p = _rv(b, p)
        num, wt = key >> 3, key & 7
        if wt == 2:
            n, p = _rv(b, p)
            if num == 3:
                q, sub = 0, b[p:p + n]
                while q < len(sub):
                    k2, q = _rv(sub, q)
                    if k2 & 7 == 2:
                        n2, q = _rv(sub, q)
                        if k2 >> 3 == 1:
                            names.append(sub[q:q + n2].decode()); break
                        q += n2
                    elif k2 & 7 == 0:
                        _, q = _rv(sub, q)
                    else:
                        break
            p += n
        elif wt == 0:
            _, p = _rv(b, p)
        else:
            break
    return names


def _rv(b, p):
    v = sh = 0
    while True:
        c = b[p]; p += 1
        v |= (c & 0x7F) << sh
        if c < 0x80:
            return v, p
        sh += 7


def tileid(z, x, y):                                       # the reference algorithm (pmtiles/tile.py), written out again
    acc = ((1 << (z * 2)) - 1) // 3
    a = z - 1
    while a >= 0:
        s = 1 << a
        rx, ry = s & x, s & y
        acc += ((3 * rx) ^ ry) << a
        if ry == 0:
            if rx != 0:
                x, y = s - 1 - x, s - 1 - y
            x, y = y, x
        a -= 1
    return acc


def _dir_bytes(entries):
    out = _vi(len(entries))
    last = 0
    for e in entries:
        out += _vi(e[0] - last); last = e[0]
    for e in entries:
        out += _vi(e[3])
    for e in entries:
        out += _vi(e[2])
    for i, e in enumerate(entries):
        out += _vi(0 if i > 0 and e[1] == entries[i - 1][1] + entries[i - 1][2] else e[1] + 1)
    return gzip.compress(out, mtime=0)


def pmtiles_schreiben(path, tiles, leaf_size=6, bounds=(7.9, 47.2, 8.4, 47.5), center=(SEON[1], SEON[0], 12)):
    """tiles: {(z, x, y): raw MVT} -> PMTiles v3 (gzip tiles, gzip directories, leaf directories of «leaf_size» entries)"""
    items = sorted(((tileid(z, x, y), gzip.compress(b, mtime=0)) for (z, x, y), b in tiles.items()), key=lambda t: t[0])
    data, entries = b"", []
    for tid, b in items:
        entries.append((tid, len(data), len(b), 1)); data += b
    leaves, root = b"", []
    for i in range(0, len(entries), leaf_size):
        lb = _dir_bytes(entries[i:i + leaf_size])
        root.append((entries[i][0], len(leaves), len(lb), 0)); leaves += lb
    rootb = _dir_bytes(root)
    meta = gzip.compress(json.dumps({"name": "Test Seon", "attribution": "© OpenStreetMap"}).encode(), mtime=0)
    zs = [k[0] for k in tiles]
    off_root = 127; off_meta = off_root + len(rootb); off_leaf = off_meta + len(meta); off_data = off_leaf + len(leaves)
    h = b"PMTiles" + bytes([3]) + struct.pack("<11Q", off_root, len(rootb), off_meta, len(meta), off_leaf, len(leaves), off_data, len(data),
                                              len(entries), len(entries), len(entries))
    h += struct.pack("<6B", 1, 2, 2, 1, min(zs), max(zs)) + struct.pack("<4i", *[int(v * 1e7) for v in bounds])
    h += struct.pack("<B2i", center[2], int(center[0] * 1e7), int(center[1] * 1e7))
    assert len(h) == 127
    with open(path, "wb") as f:
        f.write(h + rootb + meta + leaves + data)
    return {k: gzip.compress(v, mtime=0) for k, v in tiles.items()}


def _px(lat, lon, z, tx, ty):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    r = math.radians(lat)
    y = (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n
    return int(round((x - tx) * 4096)), int(round((y - ty) * 4096))


def _tile_of(lat, lon, z):
    n = 2 ** z
    r = math.radians(lat)
    return z, int((lon + 180) / 360 * n), int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)


def test_karte(path):
    """a small map of Seon AG with the layers of Protomaps; + 3 MB filler tiles far away (Genève) - never read for Seon"""
    tiles = {}
    for z in range(0, 15):
        want = {_tile_of(SEON[0], SEON[1], z)}
        if z >= 11:
            _, x0, y0 = _tile_of(SEON[0], SEON[1], z)
            want |= {(z, x0 + dx, y0 + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        for (z_, tx, ty) in want:
            P = lambda la, lo: _px(la, lo, z_, tx, ty)
            L = {"earth": [(3, [[(-64, -64), (4160, -64), (4160, 4160), (-64, 4160), (-64, -64)]], {"kind": "earth"})]}
            lake = [P(47.305, 8.195), P(47.305, 8.225), P(47.275, 8.225), P(47.275, 8.195), P(47.305, 8.195)]
            L["water"] = [(3, [lake], {"kind": "lake", "name": "Hallwilersee"})]
            L["landuse"] = [(3, [[P(47.36, 8.13), P(47.36, 8.15), P(47.35, 8.15), P(47.35, 8.13), P(47.36, 8.13)]], {"kind": "forest"})]
            L["roads"] = [(2, [[P(47.3475, 8.12), P(47.3475, 8.20)]], {"kind": "minor_road", "name": "Bahnhofstrasse", "min_zoom": 12}),
                          (2, [[P(47.40, 8.10), P(47.30, 8.22)]], {"kind": "major_road", "name": "Seetalstrasse", "ref": "26", "min_zoom": 8})]
            if z_ >= 13:
                L["buildings"] = [(3, [[P(47.3480 + i * 0.0004, 8.1590 + j * 0.0006), P(47.3480 + i * 0.0004, 8.1594 + j * 0.0006),
                                        P(47.3477 + i * 0.0004, 8.1594 + j * 0.0006), P(47.3477 + i * 0.0004, 8.1590 + j * 0.0006),
                                        P(47.3480 + i * 0.0004, 8.1590 + j * 0.0006)]], {"kind": "building", "height": 8}) for i in range(3) for j in range(3)]
            L["places"] = [(1, [[P(SEON[0], SEON[1])]], {"kind": "locality", "kind_detail": "village", "name": "Seon", "min_zoom": 9, "population_rank": 9}),
                           (1, [[P(47.3165, 8.1912)]], {"kind": "locality", "kind_detail": "village", "name": "Seengen", "min_zoom": 10, "population_rank": 8})]
            tiles[(z_, tx, ty)] = mvt(L)
    for i in range(20):                                     # filler near Genève (not compressible, ~250 KB each)
        z_, tx, ty = _tile_of(46.2, 6.14 + i * 0.03, 14)
        tiles[(z_, tx, ty)] = mvt({"earth": [(3, [[(0, 0), (4096, 0), (4096, 4096), (0, 0)]], {"kind": os.urandom(120000).hex()})]})
    return pmtiles_schreiben(path, tiles)


TEST_ORTE = [
    {"name": "Seon", "alts": [], "kind": "village", "lat": 47.3475, "lon": 8.1602, "kt": "AG", "gem": None, "pop": 5300},
    {"name": "Seengen", "alts": [], "kind": "village", "lat": 47.3165, "lon": 8.1912, "kt": "AG", "gem": None, "pop": 3900},
    {"name": "Seon Dorf", "alts": [], "kind": "locality", "lat": 47.349, "lon": 8.161, "kt": "AG", "gem": "Seon"},
    {"name": "Zürich", "alts": ["Zurich", "Zurigo", "Turitg"], "kind": "city", "lat": 47.3769, "lon": 8.5417, "kt": "ZH", "pop": 421000},
    {"name": "Zürichsee", "alts": ["Lac de Zurich", "Lago di Zurigo"], "kind": "lake", "lat": 47.25, "lon": 8.66, "kt": "ZH", "km2": 88.6},
    {"name": "Zurzach", "alts": [], "kind": "town", "lat": 47.586, "lon": 8.293, "kt": "AG", "pop": 4300},
    {"name": "Genève", "alts": ["Genf", "Ginevra", "Geneva"], "kind": "city", "lat": 46.2044, "lon": 6.1432, "kt": "GE", "pop": 203000},
    {"name": "Matterhorn", "alts": ["Monte Cervino", "Mont Cervin"], "kind": "peak", "lat": 45.9763, "lon": 7.6586, "kt": "VS", "ele": 4478},
    {"name": "Hallwilersee", "alts": ["Lac de Hallwil"], "kind": "lake", "lat": 47.29, "lon": 8.21, "kt": "AG", "km2": 10.3},
    {"name": "Bahnhofstrasse", "alts": [], "kind": "street", "lat": 47.3476, "lon": 8.1605, "kt": "AG", "gem": "Seon"},
    {"name": "Bahnhofstrasse", "alts": [], "kind": "street", "lat": 47.3705, "lon": 8.5393, "kt": "ZH", "gem": "Zürich"},
    {"name": "Sumvitg", "alts": ["Somvix"], "kind": "village", "lat": 46.729, "lon": 9.022, "kt": "GR", "pop": 1200},
]
NORM_PROBEN = ["Zürich", "Genève", "La Chaux-de-Fonds", "Sant’Antonio", "Großmünster", "Sumvitg/Somvix", "Œuvre", "Ålesund", "Biel/Bienne",
               "  Mont-Soleil ", "Bürglen (UR)", "Lac de Neuchâtel", "Zuoz", "Tschlin – Strada", "Æbeltoft", "São Paulo", "ß"]


def dateien_bauen(tmp, web_zip):
    """the three test files + their pins"""
    P = paket_modul()
    out = os.path.join(tmp, "rel"); os.makedirs(out, exist_ok=True)
    tiles = test_karte(os.path.join(out, "karte-ch-1.pmtiles"))
    sq = os.path.join(tmp, "orte.sqlite")
    P.index_bauen(TEST_ORTE, sq, {"tag": P.TAG, "quelle": "Test"})
    P.gz_fest(sq, os.path.join(out, "orte-ch-1.sqlite.gz"))
    if web_zip:
        shutil.copyfile(web_zip, os.path.join(out, "karte-web-1.zip"))
    else:
        print("  (karte-web-1.zip wird gebaut: paket.py --web, braucht node und Internet)", flush=True)
        P.baue_web(out, 14)
    pins = {}
    for r_, n in P.NAMEN.items():
        p = os.path.join(out, n)
        unp = 0
        if r_ == "web":
            with zipfile.ZipFile(p) as z:
                unp = sum(i.file_size for i in z.infolist())
        elif r_ == "orte":
            unp = os.path.getsize(sq)
        pins[r_] = {"name": n, "size": os.path.getsize(p), "sha256": P.sha256(p), "unpacked": unp}
    return P, out, pins, tiles


# ---- part A: MoveEye in this process (test client) ------------------------------------------------------------------------------------
def teil_a(datei, P, rel, pins, tiles):
    sys.path.insert(0, HIER)
    from piper_test import Srv
    home = tempfile.mkdtemp(prefix="mw_karten_home_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_karten_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    ns["DATA_DIR"] = home
    ns["log_event"] = lambda *x, **k: None
    CFG, KF, DL = ns["CFG"], ns["KQ_FILES"], ns["KQ_DL"]
    print("A) MoveEye-Teil 639zzq (Testkarte Seon)", flush=True)
    ok(ns["kq_selftest"](), "Selbsttest 639zzq")
    ok(all(ns["kq_norm"](s) == P.kq_norm(s) and ns["kq_norm"](s, True) == P.kq_norm(s, True) for s in NORM_PROBEN),
       "Suchschlüssel: gleiche Regeln in paket.py und MoveEye (%s …)" % ", ".join(P.kq_norm(s) for s in NORM_PROBEN[:4]))
    kt = ns["kq_tileid"]
    sample = [(0, 0, 0), (1, 1, 0), (5, 16, 11), (12, 2140, 1435), (14, 8578, 5744), (15, 17157, 11489)]
    ok(all(kt(*s) == tileid(*s) for s in sample), "Kachel-Nummern wie die Referenz (Testschreiber)")
    try:
        from pmtiles.tile import zxy_to_tileid
        ok(all(kt(*s) == zxy_to_tileid(*s) for s in sample), "Kachel-Nummern wie pmtiles (Python-Referenz)")
    except ImportError:
        print("  (pmtiles nicht installiert: Vergleich mit der Python-Referenz übersprungen)")
    # reader: every tile, only the needed bytes
    pm = ns["KqPMTiles"](os.path.join(rel, "karte-ch-1.pmtiles"))
    ok(pm.maxz == 14 and pm.minz == 0 and pm.tcomp == 2 and len(pm.root[0]) > 2, f"Kopf gelesen: z{pm.minz}–{pm.maxz}, gzip, Wurzel mit {len(pm.root[0])} Blättern")
    alle = all(pm.tile(*k) == v for k, v in tiles.items())
    ok(alle, f"alle {len(tiles)} Kacheln byte-genau (über Blattverzeichnisse)")
    pm2 = ns["KqPMTiles"](os.path.join(rel, "karte-ch-1.pmtiles"))
    r0 = pm2.reads
    b = pm2.tile(*_tile_of(SEON[0], SEON[1], 14))
    ok(b is not None and pm2.reads - r0 < 40000 and pm2.size > 2_000_000,
       f"eine Kachel liest nur {pm2.reads - r0} Bytes (Datei {pm2.size / 1e6:.1f} MB, nie die ganze Datei)")
    ok(pm2.tile(14, 0, 0) is None and pm2.tile(3, 7, 7) is None and pm2.tile(16, 1, 1) is None, "fehlende Kacheln: None")
    ns["KQ_LEAF_CACHE"] = 3
    for k in tiles:
        pm2.tile(*k)
    ok(len(pm2.leaves) <= 3, f"Blatt-Speicher begrenzt ({len(pm2.leaves)} Blätter bei Grenze 3)")
    ns["KQ_LEAF_CACHE"] = 48
    pm.close(); pm2.close()
    try:
        ns["KqPMTiles"](os.path.join(rel, "orte-ch-1.sqlite.gz"))
        ok(False, "keine PMTiles-Datei wird abgelehnt")
    except ValueError:
        ok(True, "keine PMTiles-Datei wird abgelehnt")

    srv = Srv()
    for r_, f in pins.items():
        srv.files["/" + ns["KQ_TAG"] + "/" + f["name"]] = open(os.path.join(rel, f["name"]), "rb").read()
    ns["KQ_BASE"]["url"] = srv.url + ns["KQ_TAG"] + "/"
    echt = {r_: dict(f) for r_, f in KF.items()}                 # ab 3.81.0 stehen die echten Pins (Release karten-1) in der Datei
    ok(ns["kq_pinned"]() or not any(f["size"] for f in echt.values()),
       "Pins in der gebauten Datei: %s" % ("echt, %.1f MB" % (sum(f["size"] for f in echt.values()) / 1e6) if ns["kq_pinned"]() else "noch keine"))
    for f in KF.values():
        f.update(size=0, sha256="", unpacked=0)
    ns["KQ_RT"]["ok_t"] = 0
    st0 = ns["kq_state"]()
    ok(not st0["pinned"] and not st0["on"] and ns["kq_download"]()[0] is False, "ohne Pins: «kommt mit einem Update», nichts installiert, kein Laden")
    for r_, f in pins.items():
        KF[r_].update(f)
    ns["KQ_RT"]["ok_t"] = 0
    CFG.update(https_extra=False, lang="de", tausch_free_gb=0.02)
    PW = "Admin-Karte-123"
    assert ns["web_pw_set"](PW)[0]
    okk, err = ns["users_action"]({"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
    assert okk, err
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    c = ws.app.test_client(use_cookies=False)
    H = {"Authorization": "Basic " + base64.b64encode(f"admin:{PW}".encode()).decode()}
    HA = {"Authorization": "Basic " + base64.b64encode(b"Anna:anna-pass-1").decode()}

    def api(d=None, h=H):
        r = c.post("/api/karte", json=d, headers=h) if d else c.get("/api/karte", headers=h)
        return r.status_code, (r.get_json(silent=True) or {})

    def warten(limit=300):
        t0 = time.time()
        while DL["running"] and time.time() - t0 < limit:
            time.sleep(0.05)
        ns["KQ_RT"]["ok_t"] = 0
    code, j = api()
    ok(code == 200 and j["pinned"] and not j["on"] and j["admin"] and j["size"] == sum(f["size"] for f in pins.values()),
       f"/api/karte: gepinnt, nicht installiert, Grösse {j.get('size')} Bytes")
    code, j = api(None, HA)
    ok(code == 200 and not j["admin"], "Benutzer sieht den Zustand (ohne Admin)")
    code, j = api({"action": "install"}, HA)
    ok(code == 403 and not DL["running"], f"Benutzer (Familie) darf nicht laden ({code})")
    code, j = api({"action": "delete"}, HA)
    ok(code == 403, f"Benutzer darf nicht entfernen ({code})")
    CFG["tausch_free_gb"] = 1e6
    code, j = api({"action": "install"})
    ok(code == 400 and "Platz" in str(j.get("error")) and not DL["running"] and not srv.hits, f"zu wenig Platz: abgelehnt, nichts geladen ({code} {j.get('error')})")
    ok(not j["space_ok"], "Zustand meldet zu wenig Platz (Knopf gesperrt)")
    CFG["tausch_free_gb"] = 0.02
    pfad = "/" + ns["KQ_TAG"] + "/" + pins["tiles"]["name"]
    srv.tamper.add(pfad)
    api({"action": "install"}); warten()
    ok(not ns["kq_installed"]() and "checksum" in DL["msg"], f"veränderte Karte abgelehnt ({DL['msg']})")
    ok(not os.path.exists(ns["kq_dir"]()) and not os.path.exists(ns["kq_dir"]() + ".new"), "kein halber Ordner danach")
    r = c.get("/karte/t/%s/14/%d/%d.mvt" % ((ns["KQ_TAG"],) + _tile_of(SEON[0], SEON[1], 14)[1:]), headers=H)
    ok(r.status_code == 404, "ohne Installation: keine Kachel")
    srv.tamper.discard(pfad)
    srv.extra = b"x" * 7
    api({"action": "install"}); warten()
    ok(not ns["kq_installed"](), f"zu grosse Datei abgelehnt ({DL['msg']})")
    srv.extra = b""
    t0 = time.time()
    code, j = api({"action": "install"}); warten()
    ok(code == 200 and ns["kq_installed"]() and DL["done"] and not DL["msg"], f"geladen, geprüft, eingeschaltet in {time.time() - t0:.1f} s ({DL['msg'] or 'ok'})")
    ok(not os.path.exists(ns["kq_dl_dir"]()), "Download-Ordner danach gelöscht")
    z_, x_, y_ = _tile_of(SEON[0], SEON[1], 14)
    T = ns["KQ_TAG"]
    r = c.get(f"/karte/t/{T}/14/{x_}/{y_}.mvt", headers=HA)
    ok(r.status_code == 200 and r.headers.get("Content-Encoding") == "gzip" and gzip.decompress(r.data) == gzip.decompress(tiles[(14, x_, y_)])
       and "max-age" in r.headers.get("Cache-Control", ""), "Kachel über den Server: gzip wie in der Datei, Cache, auch für den Benutzer")
    r = c.get(f"/karte/t/{T}/14/1/1.mvt", headers=H)
    ok(r.status_code == 204, f"fehlende Kachel: 204 ({r.status_code})")
    ok(c.get(f"/karte/t/karten-99/14/{x_}/{y_}.mvt", headers=H).status_code == 404, "falscher Tag: 404")
    seite = c.get("/karte", headers=H).get_data(as_text=True)
    ok(re.search(r'<main>\s*<a class="kq-back" href="/more">‹ <span data-i18n="More">', seite) and ".kq-back{" in seite and "min-height:44px" in seite.split(".kq-back{")[1].split("}")[0],
       "/karte: ganz oben ein Weg zurück zu «Mehr» (44 px hoch, wie bei den Packlisten)")
    r = c.get("/karte/fonts/Noto Sans Regular/0-255.pbf", headers=H)
    ok(r.status_code == 200 and len(r.data) > 1000, f"Schrift Noto Sans Regular 0-255 ({len(r.data)} Bytes)")
    r = c.get("/karte/fonts/Noto Sans Devanagari Regular v1/2304-2559.pbf", headers=H)
    ok(r.status_code == 200 and r.data == b"", "fehlende Schrift: leere Antwort")
    ok(c.get("/karte/fonts/../../settings.json", headers=H).status_code in (200, 404) and c.get("/karte/fonts/../../settings.json", headers=H).data in (b"",),
       "Schriften: kein Pfad nach aussen")
    r = c.get("/karte/web/maplibre-gl.js", headers=dict(H, **{"Accept-Encoding": "gzip"}))
    ok(r.status_code == 200 and r.headers.get("Content-Encoding") == "gzip" and b"maplibre" in gzip.decompress(r.data)[:5000].lower(),
       f"maplibre-gl.js vorkomprimiert ({len(r.data) / 1e3:.0f} KB)")
    for bad in ("/karte/web/../karte.ok", "/karte/web/karte.json", "/karte/web/maplibre-gl.js.gz", "/karte/web/%2e%2e/karte.ok"):
        ok(c.get(bad, headers=H).status_code == 404, f"{bad} -> 404")
    st = c.get("/karte/web/style.json", headers=H).get_json()
    ok(st and st["sources"]["protomaps"]["tiles"] == ["{TILES}"] and all(l["id"] != "landcover" for l in st["layers"]) and '"name:de"' not in json.dumps(st),
       f"Stil: {len(st['layers'])} Ebenen, ohne «landcover», lokale Namen")
    lic = c.get("/karte/web/LIZENZEN.txt", headers=H).get_data(as_text=True)
    ok("OpenStreetMap-Mitwirkende" in lic and "ODbL" in lic and "BSD-3" in lic and "Open Font License" in lic and "CC0" in lic, "LIZENZEN.txt: ODbL, BSD-3, OFL, CC0")

    def such(q, h=H):
        r = c.get("/api/karte/suche?q=" + urllib.request.quote(q), headers=h)
        return (r.get_json() or {}).get("results") or []
    s = such("Seon")
    ok(s and s[0]["name"] == "Seon" and s[0]["kt"] == "AG" and s[0]["kind"] == "village", "«Seon» -> zuerst Seon (Dorf, AG)" + f" [{', '.join(x['name'] for x in s)}]")
    s = such("Zurich")
    ok(s and s[0]["name"] == "Zürich" and s[0]["kt"] == "ZH", "«Zurich» -> Zürich" + f" [{', '.join(x['name'] for x in s)}]")
    s = such("zuerich")
    ok(s and s[0]["name"] == "Zürich", "«zuerich» -> Zürich")
    s = such("Genf")
    ok(s and s[0]["name"] == "Genève" and s[0]["also"] == "Genf", "«Genf» -> Genève (Genf)")
    s = such("zur")
    ok([x["name"] for x in s][:2] == ["Zürich", "Zürichsee"] or [x["name"] for x in s][0] == "Zürich", "«zur»: die Stadt vor See und Zurzach " + str([x["name"] for x in s]))
    s = such("Matter")
    ok(s and s[0]["name"] == "Matterhorn" and s[0]["ele"] == 4478, "«Matter» -> Matterhorn 4478 m")
    s = such("bahnhofstrasse seon")
    ok(s and s[0]["gem"] == "Seon" and s[0]["kind"] == "street", "«bahnhofstrasse seon» -> die Strasse in Seon")
    s = such("Somvix")
    ok(s and s[0]["name"] == "Sumvitg" and s[0]["also"] == "Somvix", "«Somvix» -> Sumvitg (romanischer Name zuerst)")
    ok(such("s") == [] and such("") == [], "ein Buchstabe: keine Suche")
    ok(such("Seon", HA) and such("Seon", HA)[0]["name"] == "Seon", "Benutzer darf suchen")
    t0 = time.time()
    for q in ("Se", "Zu", "Ba", "Ma", "Ge"):
        such(q)
    ok(time.time() - t0 < 2, f"5 Suchen in {1000 * (time.time() - t0):.0f} ms")
    r = c.get("/karte", headers=HA)
    ok(r.status_code == 200 and "window.KQ =" in r.get_data(as_text=True) and '"admin": false' in r.get_data(as_text=True), "/karte für den Benutzer (ohne Admin-Knöpfe)")
    h = c.get("/recordings", headers=H).get_data(as_text=True)
    ok(h.count("window.KQ =") == 1 and '"on": true' in h, "Aufnahmen: Kartenskript im Kopf, Karte an")
    code, j = api({"action": "delete"})
    ok(code == 200 and not ns["kq_installed"]() and not os.path.exists(ns["kq_dir"]()), "Entfernen löscht alles")
    ok(such("Seon") == [] and c.get(f"/karte/t/{T}/14/{x_}/{y_}.mvt", headers=H).status_code == 404, "danach: keine Suche, keine Kachel")
    shutil.rmtree(home, ignore_errors=True)
    return srv


# ---- part B: MoveEye as its own process, the pages in the browser ---------------------------------------------------------------------
def gepatcht(datei, tmp, pins, url):
    """a copy of the program with the test pins and the test server (the zip next to it stays the same)"""
    src = open(datei, encoding="utf-8").read()
    for r_, f in pins.items():
        neu = '"%s": {"name": "%s", "size": %d, "sha256": "%s", "unpacked": %d}' % (r_, f["name"], f["size"], f["sha256"], f["unpacked"])
        src, n = re.subn(r'"%s": \{"name": "[^"]*", "size": \d+, "sha256": "[0-9a-f]*", "unpacked": \d+\}' % r_, neu, src)
        assert n == 1, r_
    alt = '"https://github.com/DonElektro/MotionWatch/releases/download/" + KQ_TAG + "/"'
    assert src.count(alt + "}") >= 1
    src = src.replace(alt + "}", json.dumps(url) + "}; bio_free_need = lambda: 20 << 20   # test: little room on the test machine (the guard: part A)", 1)
    ziel = os.path.join(tmp, os.path.basename(datei))
    open(ziel, "w", encoding="utf-8").write(src)
    for z in glob.glob(os.path.join(os.path.dirname(datei), "moveeye_daten_*.zip")):
        shutil.copyfile(z, os.path.join(tmp, os.path.basename(z)))
    return ziel


def starte(datei, tmp, port, pw, extra=None):
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg, exist_ok=True)
    st = {"source": "sim:0", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "theme": "dark",
          "tausch_free_gb": 0.02, "gps_phone": False, "latitude": 47.0, "longitude": 8.0, "map_online": False, "record_dir": os.path.join(tmp, "recordings"), "news_popup": False}
    st.update(extra or {})
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg, "--web-password", pw],
                         stdout=logf, stderr=subprocess.STDOUT, cwd=tmp)
    return p, cfg


def teil_b(datei, P, rel, pins, bilder, echt=False):
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, HIER)
    from piper_test import Srv
    import numpy as np
    import cv2
    print("B) im Browser" + (" (echte Dateien)" if echt else ""), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_karten_b_")
    srv = Srv()
    if not echt:
        for r_, f in pins.items():
            srv.files["/karten-1/" + f["name"]] = open(os.path.join(rel, f["name"]), "rb").read()
    d2 = gepatcht(datei, tmp, pins, srv.url + "karten-1/")
    rd = os.path.join(tmp, "recordings"); os.makedirs(rd)
    im = np.full((480, 640, 3), (60, 110, 60), np.uint8); cv2.circle(im, (320, 240), 90, (230, 230, 230), -1)
    cv2.imwrite(os.path.join(rd, "snapshot_20261110_120000.jpg"), im)
    json.dump({"gps": {"lat": SEON[0], "lon": SEON[1]}}, open(os.path.join(rd, "snapshot_20261110_120000.json"), "w"))
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    PW = "Karte-" + os.urandom(4).hex()
    p, cfg = starte(d2, tmp, port, PW)
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
        os.makedirs(bilder, exist_ok=True)
        if echt:                                            # the real files: put in place like after a download (the download path: part A)
            kd = os.path.join(cfg, "karte"); os.makedirs(os.path.join(kd, "web"))
            with zipfile.ZipFile(os.path.join(rel, pins["web"]["name"])) as z:
                z.extractall(os.path.join(kd, "web"))
            with gzip.open(os.path.join(rel, pins["orte"]["name"])) as g_, open(os.path.join(kd, "orte.sqlite"), "wb") as o_:
                shutil.copyfileobj(g_, o_)
            os.symlink(os.path.abspath(os.path.join(rel, pins["tiles"]["name"])), os.path.join(kd, "ch.pmtiles"))
            json.dump({"tag": "karten-1", "sha256": {r_: f["sha256"] for r_, f in pins.items()}}, open(os.path.join(kd, "karte.ok"), "w"))
            time.sleep(2.5)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=ARGS)
            aussen = []

            def kontext(mob, user=("admin", PW)):
                vp = {"width": 390, "height": 844} if mob else {"width": 1366, "height": 900}
                ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                     http_credentials={"username": user[0], "password": user[1]}, locale="de-CH")
                ctx.add_init_script("try{localStorage.setItem('mw-lang','de');localStorage.setItem('mw-theme','dark');localStorage.setItem('mw-lv-knoepfe','1');"
                                    "localStorage.setItem('mw-tours-seen','[\"live\",\"more\",\"guest\",\"settings\",\"rec\",\"history\",\"sim\",\"protect\",\"zones\",\"cams\",\"place\",\"tools\"]')}catch(e){}")
                ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(("data:", "blob:"))
                          else (aussen.append(r.request.url[:120]), r.abort()))
                return ctx
            if not echt:
                # the install box as the administrator sees it, then loading through the page
                ctx = kontext(True); pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                pg.goto(base + "/karte"); pg.wait_for_selector(".kq-install", timeout=20000)
                ok("Offline-Karte Schweiz herunterladen" in pg.inner_text(".kq-install") and "MB" in pg.inner_text(".kq-install"), "/karte ohne Karte: Knopf «Offline-Karte Schweiz herunterladen (… MB)»")
                pg.screenshot(path=os.path.join(bilder, "karte_installieren_iphone.png"), full_page=True)
                pg.once("dialog", lambda d: d.accept())
                pg.tap(".kq-install")
                for _i in range(120):
                    if req("/api/karte")[1].get("on"):
                        break
                    time.sleep(0.5)
                ok(req("/api/karte")[1].get("on"), "über die Seite geladen und eingeschaltet")
                pg.wait_for_timeout(2500)
                ok(not errs, "keine JS-Fehler (Installieren)" + (": " + " | ".join(errs[:3]) if errs else ""))
                ctx.close()
            n0 = len(aussen)
            for name, mob in (("iphone", True), ("desktop", False)):
                ctx = kontext(mob); pg = ctx.new_page(); errs = []; kach = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                pg.on("response", lambda r: kach.append(r.status) if "/karte/t/" in r.url else None)
                pg.goto(base + f"/karte?lat={SEON[0]}&lon={SEON[1]}&z=14")
                pg.wait_for_function("() => window.KQMAP && KQMAP.loaded() && KQMAP.areTilesLoaded()", timeout=60000)
                pg.wait_for_timeout(800)
                ok(pg.evaluate("() => !!document.querySelector('#kq-c canvas.maplibregl-canvas')"), f"{name}: /karte zeigt die Karte (MapLibre, WebGL)")
                ok(kach and all(s in (200, 204) for s in kach), f"{name}: {len(kach)} Kacheln geladen ({sorted(set(kach))})")
                at = pg.locator("#kq-at")
                ok(at.is_visible() and "© OpenStreetMap-Mitwirkende" in at.inner_text(), f"{name}: Quellenangabe sichtbar «{at.inner_text()}»")
                pg.screenshot(path=os.path.join(bilder, f"karte_ort_{name}.png"))
                pg.fill("#kq-q", "Seon")
                pg.wait_for_selector(".kq-hit", timeout=10000)
                hits = pg.locator(".kq-hit").all_inner_texts()
                ok(hits and hits[0].startswith("Seon") and ("AG" in hits[0]), f"{name}: Suche «Seon» -> «{hits[0] if hits else ''}»")
                pg.screenshot(path=os.path.join(bilder, f"karte_suche_{name}.png"))
                pg.fill("#kq-q", "Zurich")
                pg.wait_for_function("() => { const b = document.querySelector('.kq-hit'); return b && b.innerText.startsWith('Zürich'); }", timeout=10000)
                ok(pg.locator(".kq-hit").first.inner_text().startswith("Zürich"), f"{name}: Suche «Zurich» -> Zürich")
                pg.fill("#kq-q", "Seon"); pg.wait_for_function("() => { const b = document.querySelector('.kq-hit'); return b && b.innerText.startsWith('Seon'); }", timeout=10000)
                (pg.locator(".kq-hit").first.tap if mob else pg.locator(".kq-hit").first.click)()
                pg.wait_for_timeout(600)
                ok("Seon" in pg.inner_text("#kq-info"), f"{name}: Treffer gewählt: «{pg.inner_text('#kq-info')}»")
                box = pg.locator("#kq-c").bounding_box()
                x, y = box["x"] + box["width"] * 0.35, box["y"] + box["height"] * 0.6
                (pg.touchscreen.tap if mob else pg.mouse.click)(x, y)
                pg.wait_for_timeout(500)
                want = pg.evaluate(f"() => {{ const r = document.getElementById('kq-c').getBoundingClientRect(); const l = KQMAP.unproject([{x} - r.left, {y} - r.top]); return [l.lat, l.lng]; }}")
                info = pg.inner_text("#kq-info")
                got = [float(v) for v in re.findall(r"-?\d+\.\d{5}", info)[-2:]]
                ok(len(got) == 2 and abs(got[0] - want[0]) < 1.5e-4 and abs(got[1] - want[1]) < 1.5e-4, f"{name}: Tipp auf die Karte wählt den Punkt ({info}; erwartet {want[0]:.5f}, {want[1]:.5f})")
                (pg.tap if mob else pg.click)("#kq-set")
                pg.wait_for_function("() => document.getElementById('kq-msg').innerText.includes('Gespeichert')", timeout=10000)
                g = req("/api/gps")[1]
                ok(abs(g["lat"] - want[0]) < 0.0002 and abs(g["lon"] - want[1]) < 0.0002 and not g["on"],
                   f"{name}: Standort gespeichert ({g['lat']}, {g['lon']}), «automatisch» aus")
                pg.screenshot(path=os.path.join(bilder, f"karte_tipp_{name}.png"))
                if mob:                                     # two fingers / pinch: MapLibre zooms (touch)
                    pg.evaluate("() => document.getElementById('kq-map').scrollIntoView({block: 'end'})"); pg.wait_for_timeout(300)   # 639zzx: the page is longer now
                    box = pg.locator("#kq-c").bounding_box()
                    z0 = pg.evaluate("() => KQMAP.getZoom()")
                    cdp = ctx.new_cdp_session(pg)
                    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": cx - 20, "y": cy, "id": 1}, {"x": cx + 20, "y": cy, "id": 2}]})
                    for s in range(1, 11):
                        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": cx - 20 - s * 12, "y": cy, "id": 1}, {"x": cx + 20 + s * 12, "y": cy, "id": 2}]})
                        pg.wait_for_timeout(30)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                    pg.wait_for_timeout(700)
                    z1 = pg.evaluate("() => KQMAP.getZoom()")
                    ok(z1 > z0 + 0.5, f"iphone: zwei Finger zoomen ({z0:.1f} -> {z1:.1f})")
                    c0 = pg.evaluate("() => KQMAP.getCenter().lng")
                    pg.mouse.move(cx, cy)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": cx, "y": cy, "id": 1}]})
                    for s in range(1, 9):
                        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": cx - s * 15, "y": cy, "id": 1}]})
                        pg.wait_for_timeout(30)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                    pg.wait_for_timeout(500)
                    ok(pg.evaluate("() => KQMAP.getCenter().lng") > c0, "iphone: ein Finger verschiebt die Karte")
                    cdp.detach()
                ok(not errs, f"{name}: keine JS-Fehler auf /karte" + (": " + " | ".join(errs[:3]) if errs else ""))
                if not echt:
                    # Settings -> location: background, attribution, tap saves the coordinates, the install box
                    pg = ctx.new_page(); errs2 = []
                    pg.on("pageerror", lambda e: errs2.append(str(e)[:200]))
                    pg.goto(base + "/settings")
                    pg.wait_for_selector(".locbox", state="attached", timeout=30000)
                    pg.wait_for_timeout(2500)               # the settings are grouped after loading (the boxes move into new parts)
                    for _k in range(12):                    # outer first, then inner, until the box is really visible
                        if pg.locator(".locbox .lmap").is_visible():
                            break
                        pg.evaluate("() => { const b = document.querySelector('.locbox'); const ds = []; let d = b.closest('details'); while (d) { ds.unshift(d); d = d.parentElement.closest('details'); } const c = ds.find(x => !x.open); if (c) { const sm = c.querySelector(':scope > summary'); if (sm) sm.click(); else c.open = true; } }")
                        pg.wait_for_timeout(400)
                    pg.evaluate("() => document.querySelector('.locbox').scrollIntoView()")
                    pg.wait_for_timeout(1500)
                    pg.wait_for_function("() => { const m = document.querySelector('.locbox .lmap'); return m && m.__kq && m.__kq.m && m.__kq.m.loaded() && m.__kq.m.areTilesLoaded(); }", timeout=60000)
                    pg.wait_for_timeout(800)
                    ok(pg.locator(".locbox .kq-attr").first.is_visible() and "OpenStreetMap-Mitwirkende" in pg.locator(".locbox .kq-attr").first.inner_text(),
                       f"{name}: Einstellungen → Standort: Offline-Karte mit Quellenangabe")
                    pg.evaluate("() => document.querySelector('.locbox .kq-loc').scrollIntoView({block: 'end'})")
                    pg.wait_for_selector(".locbox .kq-inst", timeout=10000)
                    ok(pg.locator(".locbox .kq-inst").is_visible() and "installiert" in pg.inner_text(".locbox .kq-inst"), f"{name}: Kasten «Offline-Karte Schweiz · installiert»")
                    pg.locator(".locbox").screenshot(path=os.path.join(bilder, f"einstellungen_standort_{name}.png"))
                    pg.evaluate("() => document.querySelector('.locbox .lmap').scrollIntoView({block: 'center'})")
                    pg.wait_for_timeout(400)
                    mb = pg.locator(".locbox .lmap").bounding_box()
                    (pg.touchscreen.tap if mob else pg.mouse.click)(mb["x"] + mb["width"] * 0.3, mb["y"] + mb["height"] * 0.4)
                    pg.wait_for_timeout(1200)
                    g2 = req("/api/gps")[1]
                    ok(abs(g2["lat"] - g["lat"]) > 1e-4 or abs(g2["lon"] - g["lon"]) > 1e-4, f"{name}: Tipp in den Einstellungen speichert den Ort ({g2['lat']}, {g2['lon']})")
                    pg.fill(".locbox .lq", "Seon")
                    pg.wait_for_selector(".locbox + .kq-res .kq-hit, .locbox .kq-res .kq-hit", timeout=10000)
                    ok(pg.locator(".locbox .kq-res .kq-hit").first.inner_text().startswith("Seon"), f"{name}: Suche im Standort-Kasten offline")
                    pg.locator(".locbox").screenshot(path=os.path.join(bilder, f"einstellungen_suche_{name}.png"))
                    ok(not errs2, f"{name}: keine JS-Fehler (Einstellungen)" + (": " + " | ".join(errs2[:3]) if errs2 else ""))
                    # recordings: the map of the places and the small map in the viewer
                    pg = ctx.new_page(); errs3 = []
                    pg.on("pageerror", lambda e: errs3.append(str(e)[:200]))
                    pg.goto(base + "/recordings")
                    pg.wait_for_selector("#grid img, #grid .item, #grid > *", timeout=30000)
                    pg.wait_for_timeout(1000)
                    pg.evaluate("() => { const it = (window.ML && ML.length) ? 0 : null; }")
                    pg.locator("#grid img").first.click()
                    pg.wait_for_function("() => { const b = document.getElementById('kq-small'); return b && !b.hidden && b.__m && b.__m.loaded() && b.__m.areTilesLoaded(); }", timeout=60000)
                    pg.wait_for_timeout(600)
                    ok(pg.locator("#kq-small .kq-attr").is_visible(), f"{name}: Aufnahme mit Ort: kleine Karte mit Quellenangabe")
                    ok("/karte?lat=" in (pg.get_attribute("#kq-small .kq-big", "href") or ""), f"{name}: Link «Grosse Karte»")
                    for tip in ("text=Verstanden", "text=Überspringen"):
                        if pg.locator(tip).count() and pg.locator(tip).first.is_visible():
                            pg.locator(tip).first.click(); pg.wait_for_timeout(300)
                    pg.screenshot(path=os.path.join(bilder, f"aufnahme_ort_{name}.png"))
                    ok(not errs3, f"{name}: keine JS-Fehler (Aufnahmen)" + (": " + " | ".join(errs3[:3]) if errs3 else ""))
                    # the simulator: «Ort von der Karte» (control type «map») with the offline map
                    pg = ctx.new_page(); errs4 = []
                    pg.on("pageerror", lambda e: errs4.append(str(e)[:200]))
                    pg.goto(base + "/sim")
                    pg.wait_for_function("() => typeof simMap === 'function'", timeout=30000)
                    pg.evaluate("""() => { const host = document.createElement('div'); host.id = 'kq-simtest'; host.style.cssText = 'padding:10px;max-width:640px';
                        host.appendChild(simMap({label: 'Ort auf der Karte wählen (Schweiz)', value: ''}, v => { window.__simSent = v; }));
                        const m = document.querySelector('main') || document.body; m.prepend(host); host.scrollIntoView(); }""")
                    pg.wait_for_timeout(500)
                    pg.fill("#kq-simtest input[type=search]", "Seon"); pg.press("#kq-simtest input[type=search]", "Enter")
                    pg.wait_for_selector("#kq-simtest button.sec >> text=/^Seon ·/", timeout=10000)
                    pg.locator("#kq-simtest button.sec >> text=/^Seon ·/").first.click()
                    pg.wait_for_function("() => { const m = document.querySelector('#kq-simtest .kq-bg'); return m && m.parentNode.__kq.m && m.parentNode.__kq.m.loaded() && m.parentNode.__kq.m.areTilesLoaded(); }", timeout=60000)
                    pg.wait_for_timeout(600)
                    ok("OpenStreetMap-Mitwirkende" in pg.inner_text("#kq-simtest .kq-attr"), f"{name}: Simulator «Ort von der Karte»: Offline-Karte, Quellenangabe statt swisstopo")
                    pg.locator("#kq-simtest").screenshot(path=os.path.join(bilder, f"simulator_ort_{name}.png"))
                    pg.locator("#kq-simtest button:not(.sec)").last.click()
                    v = pg.evaluate("() => window.__simSent || ''")
                    ok(re.match(r"^47\.347\d+, 8\.160\d+, Seon$", v) is not None, f"{name}: «Diesen Ort laden» schickt «{v}» an den Simulator")
                    ok(not errs4, f"{name}: keine JS-Fehler (Simulator)" + (": " + " | ".join(errs4[:3]) if errs4 else ""))
                ctx.close()
            ok(len(aussen) == n0 == 0, "keine Anfrage nach aussen" + (": " + ", ".join(sorted(set(aussen))[:5]) if aussen else ""))
            # a user without admin rights: map and search yes, no install / remove, no «Als Standort setzen»
            ctx = kontext(True, ("Anna", "anna-pass-1")); pg = ctx.new_page()
            pg.goto(base + "/karte"); pg.wait_for_function("() => window.KQMAP && KQMAP.loaded()", timeout=60000)
            ok(not pg.locator("#kq-set").is_visible() and not pg.locator(".kq-inst").count(), "Benutzer: Karte ja, kein «Als Standort setzen», kein Laden / Entfernen")
            ctx.close()
            br.close()
        if not echt:
            code, j = req("/api/karte", {"action": "delete"}, ("Anna", "anna-pass-1"))
            ok(code == 403, f"Benutzer darf nicht entfernen ({code})")
    finally:
        p.terminate()
        try:
            p.wait(20)
        except Exception:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)


# ---- the real files --------------------------------------------------------------------------------------------------------------------
def teil_echt(datei, aus, bilder, browser):
    P = paket_modul()
    tx = open(os.path.join(aus, "pins.txt"), encoding="utf-8").read()
    pins = {}
    for m in re.finditer(r"^PIN (\w+) name=(\S+) size=(\d+) sha256=([0-9a-f]{64}) unpacked=(\d+)", tx, re.M):
        pins[m.group(1)] = {"name": m.group(2), "size": int(m.group(3)), "sha256": m.group(4), "unpacked": int(m.group(5))}
    ok(set(pins) == {"tiles", "web", "orte"}, "pins.txt: drei Dateien")
    print("E) echte Dateien: " + ", ".join(f"{f['name']} {f['size'] / 1e6:.1f} MB" for f in pins.values()), flush=True)
    for r_, f in pins.items():
        p = os.path.join(aus, f["name"])
        ok(os.path.getsize(p) == f["size"] and P.sha256(p) == f["sha256"], f"{f['name']}: Grösse + sha256 = pins.txt")
    home = tempfile.mkdtemp(prefix="mw_karten_echt_")
    os.environ["MOTIONWATCH_HOME"] = home
    ns = {"__name__": "mw_karten_echt", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    pm = ns["KqPMTiles"](os.path.join(aus, pins["tiles"]["name"]))
    ok(pm.maxz in (14, 15) and pm.tcomp == 2 and pm.ttype == 1, f"Kopf: z{pm.minz}–{pm.maxz}, gzip-MVT, Grenzen {[round(b, 2) for b in pm.bounds]}")
    ok(5.0 < pm.bounds[0] < 6.5 and 10.0 < pm.bounds[2] < 11.0 and 45.0 < pm.bounds[1] < 46.2 and 47.5 < pm.bounds[3] < 48.5, "Grenzen: die Schweiz")
    r0 = pm.reads
    t0 = time.time()
    b = pm.tile(*_tile_of(SEON[0], SEON[1], 14))
    ok(b is not None, "Kachel z14 von Seon da")
    names = mvt_layers(gzip.decompress(b)) if b else []
    ok({"earth", "roads", "places"} <= set(names), f"Seon z14: Ebenen {', '.join(names)}")
    z15 = pm.tile(*_tile_of(SEON[0], SEON[1], pm.maxz))
    ok(z15 is not None and "buildings" in mvt_layers(gzip.decompress(z15)), f"Seon z{pm.maxz}: mit Gebäuden")
    ok(pm.reads - r0 < 2_000_000, f"zwei Kacheln lesen {(pm.reads - r0) / 1e3:.0f} KB von {pm.size / 1e6:.0f} MB in {1000 * (time.time() - t0):.0f} ms")
    for (la, lo, nm) in ((46.2044, 6.1432, "Genève"), (46.0207, 7.7491, "Zermatt"), (46.0037, 8.9511, "Lugano"), (47.1415, 9.5215, "Vaduz")):
        tt = pm.tile(*_tile_of(la, lo, 13))
        ok(tt is not None, f"Kachel z13 bei {nm}")
    pm.close()
    import sqlite3
    sq = os.path.join(home, "orte.sqlite")
    with gzip.open(os.path.join(aus, pins["orte"]["name"])) as g_, open(sq, "wb") as o_:
        shutil.copyfileobj(g_, o_)
    ok(os.path.getsize(sq) == pins["orte"]["unpacked"], f"Ortssuche entpackt: {os.path.getsize(sq) / 1e6:.1f} MB")
    os.makedirs(os.path.join(home, "karte", "web"))
    shutil.move(sq, os.path.join(home, "karte", "orte.sqlite"))
    ns["DATA_DIR"] = home
    ns["kq_installed"] = lambda: True
    S = ns["kq_search"]
    t0 = time.time()
    s = S("Seon")
    ok(s and s[0]["name"] == "Seon" and s[0]["kt"] == "AG", f"«Seon» -> {s[0]['name'] if s else '-'} {s[0]['kt'] if s else ''} [{', '.join(x['name'] + ' ' + x['kt'] for x in s[:4])}]")
    s = S("Zurich")
    ok(s and s[0]["name"] == "Zürich", f"«Zurich» -> {s[0]['name'] if s else '-'} [{', '.join(x['name'] for x in s[:4])}]")
    s = S("Genf")
    ok(s and s[0]["name"] in ("Genève", "Genf"), f"«Genf» -> {s[0]['name'] if s else '-'} ({s[0]['also'] if s else ''})")
    s = S("Matterhorn")
    ok(s and s[0]["name"] == "Matterhorn" and (s[0]["ele"] or 0) > 4000, f"«Matterhorn» -> {s[0]['name'] if s else '-'} {s[0]['ele'] if s else ''} m")
    s = S("Bahnhofstrasse Zürich")
    ok(s and s[0]["kind"] == "street" and s[0]["gem"] == "Zürich", f"«Bahnhofstrasse Zürich» -> {s[0]['name'] + ' ' + s[0]['gem'] if s else '-'}")
    s = S("Seon")
    print("    Seon:", "; ".join(f"{x['name']} ({x['kind']}, {x['gem']}, {x['kt']})" for x in s[:8]))
    s = S("Hallwil")
    ok(s and any(x["kind"] == "lake" for x in s), f"«Hallwil» -> {', '.join(x['name'] for x in s[:3])}")
    for q in ("Se", "Ba", "St", "Zu", "Lu"):
        S(q)
    dt = time.time() - t0
    ok(dt < 3, f"11 Suchen im echten Verzeichnis: {1000 * dt:.0f} ms (auf dem Pi etwa 3–5 × länger)")
    ns["kq_close"]()
    shutil.rmtree(home, ignore_errors=True)
    if browser:
        teil_b(datei, P, aus, pins, bilder, echt=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--web", default="", help="karte-web-1.zip (sonst wird es mit paket.py --web gebaut)")
    ap.add_argument("--echt", default="", help="Ausgabe von paket.py (die drei Dateien + pins.txt)")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--ohne-browser", action="store_true")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or neueste_datei())
    bilder = a.bilder or tempfile.mkdtemp(prefix="karten_bilder_")
    print(f"Offline-Karte · {os.path.basename(datei)}", flush=True)
    if a.echt:
        teil_echt(datei, a.echt, bilder, not a.ohne_browser)
    else:
        tmp = tempfile.mkdtemp(prefix="mw_karten_")
        try:
            P, rel, pins, tiles = dateien_bauen(tmp, a.web)
            print("  Testdateien: " + ", ".join(f"{f['name']} {f['size'] / 1e3:.0f} KB" for f in pins.values()), flush=True)
            teil_a(datei, P, rel, pins, tiles)
            if not a.ohne_browser:
                teil_b(datei, P, rel, pins, bilder)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("Bilder:", bilder)
    for f in FEHLER:
        print("FEHLER:", f)
    print("Karten-Test:", "OK" if not FEHLER else f"{len(FEHLER)} Fehler")
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
