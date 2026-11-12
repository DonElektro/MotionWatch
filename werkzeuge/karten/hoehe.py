#!/usr/bin/env python3
"""MoveEye: builds the package «Höhendaten Schweiz» (hoehe-ch-N.bin, part 639zzx) for ascent, descent, profile and hiking
time of hand-drawn routes. A release asset at the tag «hoehen-N» (never in the Git repository); size + sha256 are pinned in
quelle/639zzx (KH_FILE).

Source (decision of the owner, 12.11.2026): swisstopo, 25 m grid, 0.5 m height steps - DHM25 (one download, the model the
handbook «Signalisation Wanderwege» names for the official hiking times). Free geodata of swisstopo (OGD since 1.3.2021):
free use with the source «© swisstopo». The grid is a parameter: any ESRI ASCII grid (LV03 or LV95, any cell size) or XYZ
list can be packed, e.g. a 10 m grid made from swissALTI3D - the file says its own grid, MoveEye reads it from the head.

  python3 -I werkzeuge/karten/hoehe.py --holen ORDNER                     # find and download DHM25 (STAC of data.geo.admin.ch), say what was found
  python3 -I werkzeuge/karten/hoehe.py --quelle DATEI.asc|.xyz|.zip --gitter 25 --aus OUT [--stufe 0.5]
  python3 -I werkzeuge/karten/hoehe.py --pins --aus OUT                  # OUT/pins_hoehe.txt
  python3 -I werkzeuge/karten/hoehe.py --eintragen OUT/pins_hoehe.txt    # writes KH_FILE in quelle/639zzx_karten_touren.py

The file (read by KhFile in 639zzx): «MEHOEHE1», uint32 length, JSON head {grid, e0, n0 (LV95, centre of cell 0/0 in the
south-west), cols, rows, block, q, nodata, quelle, blocks [[offset, length] …]}, then per block of 256 × 256 cells zlib of
the int16 values as differences (to the left, first column upwards), zigzag, low bytes then high bytes. A block without
data has length 0. The same input gives the same bytes.
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import urllib.request
import zipfile
import zlib

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HIER))
TAG = "hoehen-1"
NAME = "hoehe-ch-%s.bin" % TAG.split("-")[1]
QUELLE_TEIL = os.path.join(REPO, "quelle", "639zzx_karten_touren.py")
MAGIC = b"MEHOEHE1"
BLOCK = 256
NODATA = -32768
STAC = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.digitales-hoehenmodell_25/items"
FALLBACK = "https://data.geo.admin.ch/ch.swisstopo.digitales-hoehenmodell_25/data.zip"


def log(*a):
    print(*a, flush=True)


def pack_block(v):
    """int16 block -> bytes (the reverse of KhFile._block)"""
    u = v.astype(np.int16).view(np.uint16).astype(np.uint32)
    d = u.copy()
    d[:, 1:] = (u[:, 1:] - u[:, :-1]) & 0xFFFF
    d[1:, 0] = (u[1:, 0] - u[:-1, 0]) & 0xFFFF
    s = d.astype(np.uint16).view(np.int16).astype(np.int32)
    zz = ((s << 1) ^ (s >> 15)) & 0xFFFF
    raw = (zz & 0xFF).astype(np.uint8).tobytes() + (zz >> 8).astype(np.uint8).tobytes()
    return zlib.compress(raw, 9)


def schreibe(path, h, grid, e0, n0, q=0.5, quelle="© swisstopo"):
    """h: float array, row 0 = south, NaN = no data; e0 / n0: LV95 of the centre of cell (0, 0)"""
    rows, cols = h.shape
    v = np.where(np.isfinite(h), np.clip(np.round(h / q), -32000, 32000), NODATA).astype(np.int16)
    by, bx = (rows + BLOCK - 1) // BLOCK, (cols + BLOCK - 1) // BLOCK
    blocks, data, off = [], [], 0
    for j in range(by):
        for i in range(bx):
            b = np.full((BLOCK, BLOCK), NODATA, np.int16)
            part = v[j * BLOCK:(j + 1) * BLOCK, i * BLOCK:(i + 1) * BLOCK]
            b[:part.shape[0], :part.shape[1]] = part
            if (b == NODATA).all():
                blocks.append([0, 0])
                continue
            z = pack_block(b)
            blocks.append([off, len(z)]); data.append(z); off += len(z)
    head = json.dumps({"grid": grid, "e0": e0, "n0": n0, "cols": cols, "rows": rows, "block": BLOCK, "q": q, "nodata": NODATA, "quelle": quelle,
                       "blocks": blocks}, separators=(",", ":"), sort_keys=True).encode()
    with open(path, "wb") as f:
        f.write(MAGIC + len(head).to_bytes(4, "little") + head)
        for z in data:
            f.write(z)
    return {"cols": cols, "rows": rows, "bloecke": sum(1 for b in blocks if b[1]), "leer": sum(1 for b in blocks if not b[1]), "bytes": os.path.getsize(path),
            "zellen": int(np.isfinite(h).sum())}


def _mittel(a, f):
    """block mean f × f (NaN = no data; a cell needs at least half of its values)"""
    if f == 1:
        return a
    r, c = a.shape[0] // f * f, a.shape[1] // f * f
    b = a[:r, :c].reshape(r // f, f, c // f, f)
    n = np.isfinite(b).sum(axis=(1, 3))
    s = np.nansum(b, axis=(1, 3))
    return np.where(n * 2 >= f * f, s / np.maximum(n, 1), np.nan).astype(np.float32)


def lies_asc(fh, gitter):
    """ESRI ASCII grid (rows from the north) -> (h with row 0 = south, grid, e0, n0); LV03 becomes LV95"""
    hd, first = {}, None
    while True:
        ln = fh.readline()
        if not ln:
            break
        p = ln.split()
        if len(p) == 2 and re.fullmatch(r"[A-Za-z_]+", p[0]):
            hd[p[0].lower()] = float(p[1].replace(",", "."))
        else:
            first = ln
            break
    cols, rows, cell = int(hd["ncols"]), int(hd["nrows"]), hd["cellsize"]
    nod = hd.get("nodata_value", -9999.0)
    xll = hd["xllcorner"] if "xllcorner" in hd else hd["xllcenter"] - cell / 2
    yll = hd["yllcorner"] if "yllcorner" in hd else hd["yllcenter"] - cell / 2
    f = gitter / cell
    if abs(f - round(f)) > 1e-6 or f < 1:
        sys.exit("Gitter %s m passt nicht zur Quelle (%s m): nur ganze Vielfache" % (gitter, cell))
    f = int(round(f))
    vals = []
    if first:
        vals.append(np.array(first.split(), np.float32))
    for ln in fh:
        vals.append(np.array(ln.split(), np.float32))
    flat = np.concatenate(vals) if vals else np.zeros(0, np.float32)
    if flat.size != rows * cols:
        sys.exit("ASCII-Gitter: %d Werte statt %d" % (flat.size, rows * cols))
    a = flat.reshape(rows, cols)[::-1]                      # row 0 = south
    a = np.where(a == nod, np.nan, a).astype(np.float32)
    a = _mittel(a, f)
    e0, n0 = xll + gitter / 2, yll + gitter / 2
    if e0 < 1500000:                                         # LV03 -> LV95 (the difference to the exact change is below 2 m)
        e0, n0 = e0 + 2000000, n0 + 1000000
    return a, float(gitter), float(e0), float(n0), {"zelle": cell, "cols": cols, "rows": rows, "xll": xll, "yll": yll, "lv03": xll < 1500000}


def lies_xyz(fh, gitter):
    """«x y z» per line on a regular grid"""
    d = np.loadtxt(fh, dtype=np.float64, comments=("#", "X", "x"))
    xs, ys = np.unique(d[:, 0]), np.unique(d[:, 1])
    cell = float(np.median(np.diff(xs)))
    f = int(round(gitter / cell))
    if f < 1 or abs(gitter / cell - f) > 1e-6:
        sys.exit("Gitter %s m passt nicht zur Quelle (%s m)" % (gitter, cell))
    cols, rows = int(round((xs[-1] - xs[0]) / cell)) + 1, int(round((ys[-1] - ys[0]) / cell)) + 1
    a = np.full((rows, cols), np.nan, np.float32)
    a[np.round((d[:, 1] - ys[0]) / cell).astype(int), np.round((d[:, 0] - xs[0]) / cell).astype(int)] = d[:, 2]
    a = _mittel(a, f)
    e0, n0 = xs[0] + (gitter - cell) / 2, ys[0] + (gitter - cell) / 2
    if e0 < 1500000:
        e0, n0 = e0 + 2000000, n0 + 1000000
    return a, float(gitter), float(e0), float(n0), {"zelle": cell, "cols": cols, "rows": rows, "lv03": xs[0] < 1500000}


def lies(quelle, gitter):
    if quelle.lower().endswith(".zip"):
        with zipfile.ZipFile(quelle) as z:
            names = z.namelist()
            log("im ZIP:", ", ".join("%s (%d)" % (i.filename, i.file_size) for i in z.infolist())[:1500])
            pick = next((n for n in names if n.lower().endswith(".asc")), None) or next((n for n in names if n.lower().endswith(".xyz")), None)
            if not pick:
                sys.exit("im ZIP ist kein .asc und kein .xyz")
            with z.open(pick) as raw:
                fh = io.TextIOWrapper(raw, encoding="latin-1")
                return (lies_asc if pick.lower().endswith(".asc") else lies_xyz)(fh, gitter) + (pick,)
    with open(quelle, encoding="latin-1") as fh:
        return (lies_asc if quelle.lower().endswith(".asc") else lies_xyz)(fh, gitter) + (os.path.basename(quelle),)


def holen(ordner):
    """DHM25 of swisstopo: ask the STAC list, say what is there, download the grid"""
    os.makedirs(ordner, exist_ok=True)
    hrefs = []
    try:
        with urllib.request.urlopen(urllib.request.Request(STAC, headers={"User-Agent": "MoveEye-Kartenbau"}), timeout=60) as r:
            d = json.load(r)
        for ft in d.get("features") or []:
            for k, a in (ft.get("assets") or {}).items():
                hrefs.append(a.get("href") or "")
                log("STAC:", ft.get("id"), k, a.get("type"), a.get("href"))
    except Exception as e:
        log("STAC nicht lesbar:", e)
    cand = [h for h in hrefs if h.lower().endswith(".zip") and ("asc" in h.lower() or "grid" in h.lower() or "raster" in h.lower())] \
        + [h for h in hrefs if h.lower().endswith(".zip")] + [h for h in hrefs if h.lower().endswith((".asc", ".xyz"))] + [FALLBACK]
    for url in cand:
        ziel = os.path.join(ordner, os.path.basename(url.split("?")[0]) or "dhm25.zip")
        try:
            log("lade", url)
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MoveEye-Kartenbau"}), timeout=600) as r, open(ziel, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            log("QUELLE url=%s bytes=%d sha256=%s" % (url, os.path.getsize(ziel), sha256(ziel)))
            return ziel, url
        except Exception as e:
            log("  ging nicht:", e)
    sys.exit("DHM25 nicht gefunden - Adresse von Hand prüfen (opendata.swiss «DHM25») und mit --quelle übergeben")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def eintragen(pins_txt, teil=QUELLE_TEIL):
    src = open(teil, encoding="utf-8").read()
    m = re.search(r"^PIN hoehe name=(\S+) size=(\d+) sha256=([0-9a-f]{64})", open(pins_txt, encoding="utf-8").read(), re.M)
    if not m:
        sys.exit("keine Zeile «PIN hoehe …» in " + pins_txt)
    neu = 'KH_FILE = {"name": "%s", "size": %s, "sha256": "%s"}' % m.groups()
    src, n = re.subn(r'^KH_FILE = \{"name": "[^"]*", "size": \d+, "sha256": "[0-9a-f]*"\}', neu, src, flags=re.M)
    if n != 1:
        sys.exit("KH_FILE nicht genau einmal gefunden")
    open(teil, "w", encoding="utf-8").write(src)
    log("eingetragen:", neu)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--holen")
    ap.add_argument("--quelle")
    ap.add_argument("--gitter", type=float, default=25.0)
    ap.add_argument("--stufe", type=float, default=0.5)
    ap.add_argument("--aus", default="hoehe_aus")
    ap.add_argument("--pins", action="store_true")
    ap.add_argument("--eintragen")
    ap.add_argument("--herkunft", default="")
    a = ap.parse_args()
    quelle, url = a.quelle, a.herkunft
    if a.holen:
        quelle, url = holen(a.holen)
    if quelle:
        os.makedirs(a.aus, exist_ok=True)
        h, grid, e0, n0, info, name = lies(quelle, a.gitter)
        ziel = os.path.join(a.aus, NAME)
        r = schreibe(ziel, h, grid, e0, n0, a.stufe, "© swisstopo (%s, Gitter %g m)" % (name, grid))
        ok = np.isfinite(h)
        mess = dict(r, gitter=grid, stufe=a.stufe, e0=e0, n0=n0, quelle=name, url=url, quelle_info=info,
                    hoehe_min=float(np.nanmin(h)), hoehe_max=float(np.nanmax(h)), flaeche_km2=float(ok.sum() * grid * grid / 1e6))
        with open(os.path.join(a.aus, "hoehe.json"), "w") as f:
            json.dump(mess, f, indent=1, sort_keys=True)
        log("Höhendaten: %d × %d Zellen à %g m, %.0f km² mit Daten, %.0f–%.0f m, %d Blöcke (+%d leer), %.1f MB"
            % (r["cols"], r["rows"], grid, mess["flaeche_km2"], mess["hoehe_min"], mess["hoehe_max"], r["bloecke"], r["leer"], r["bytes"] / 1e6))
    if a.pins:
        p = os.path.join(a.aus, NAME)
        t = "PIN hoehe name=%s size=%d sha256=%s\n" % (NAME, os.path.getsize(p), sha256(p))
        hj = os.path.join(a.aus, "hoehe.json")
        if os.path.isfile(hj):
            m = json.load(open(hj))
            t += "INFO gitter=%g stufe=%g flaeche_km2=%.0f quelle=%s url=%s\n" % (m["gitter"], m["stufe"], m["flaeche_km2"], m["quelle"], m.get("url") or "-")
        open(os.path.join(a.aus, "pins_hoehe.txt"), "w").write(t)
        log(t)
    if a.eintragen:
        eintragen(a.eintragen)


if __name__ == "__main__":
    main()
