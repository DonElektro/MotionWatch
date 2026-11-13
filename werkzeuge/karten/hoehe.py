#!/usr/bin/env python3
"""MoveEye: builds the package «Höhendaten Schweiz» (hoehe-ch-N.bin, part 639zzx) for ascent, descent, profile and hiking
time of hand-drawn routes. A release asset at the tag «hoehen-N» (never in the Git repository); size + sha256 are pinned in
quelle/639zzx (KH_FILE).

Source (decision of the owner, 12.11.2026): swisstopo, 25 m grid, 0.5 m height steps - DHM25 (one download, the model the
handbook «Signalisation Wanderwege» names for the official hiking times). Free geodata of swisstopo (OGD since 1.3.2021):
free use with the source «© swisstopo». The grid is a parameter: any ESRI ASCII grid (LV03 or LV95, any cell size) or XYZ
list can be packed, e.g. a 10 m grid made from swissALTI3D - the file says its own grid, MoveEye reads it from the head.

  python3 -I werkzeuge/karten/hoehe.py --holen ORDNER                     # download DHM25 (address of the product page), say address + HTTP status
  python3 -I werkzeuge/karten/hoehe.py --erkunden DATEI --gitter 25       # only the heads: files, grid, extent, estimate; refuses a wrong grid (exit 2)
  python3 -I werkzeuge/karten/hoehe.py --pruefen OUT                      # the package is there and readable (else exit 1)
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
import urllib.error
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
# The matrix model of DHM25 as ESRI ASCII GRID - the link «Matrixmodell, ESRI ASCII GRID» on the product page of swisstopo
# (https://www.swisstopo.admin.ch/de/hoehenmodell-dhm25, read 13.11.2026). NOT https://data.geo.admin.ch/
# ch.swisstopo.digitales-hoehenmodell_25/data.zip: that archive is «DHM25 / 200 m» (DHM200.asc, a 200 m grid).
DHM25_URL = "https://cms.geo.admin.ch/ogd/topography/DHM25_MM_ASCII_GRID.zip"
B_PRO_ZELLE = 0.7                      # estimate: bytes per cell with data (measured 0.4-0.7 on 25 / 30 m samples at 0.5 m steps)
ECKEN = {"Bern": (2600000, 1200000), "Dufourspitze": (2633900, 1087300), "Chiasso": (2722800, 1077400), "Basel": (2611300, 1267500),
         "Genf": (2500100, 1117700), "Müstair": (2830700, 1168100), "Vaduz": (2758200, 1223100), "Malbun": (2764900, 1218900)}

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


class QuelleFalsch(Exception):
    """the source does not fit the wanted grid (exit 2 - never used silently at another resolution)"""


def asc_kopf(fh):
    """the head of an ESRI ASCII grid -> ({ncols, nrows, cellsize, xll, yll, nodata}, first data line or None)"""
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
    for k in ("ncols", "nrows", "cellsize"):
        if k not in hd:
            raise QuelleFalsch("kein ESRI-ASCII-Gitter (im Kopf fehlt «%s»)" % k)
    cell = hd["cellsize"]
    return {"ncols": int(hd["ncols"]), "nrows": int(hd["nrows"]), "cellsize": cell, "nodata": hd.get("nodata_value", -9999.0),
            "xll": hd["xllcorner"] if "xllcorner" in hd else hd.get("xllcenter", 0.0) - cell / 2,
            "yll": hd["yllcorner"] if "yllcorner" in hd else hd.get("yllcenter", 0.0) - cell / 2}, first


def faktor(gitter, zelle, was=""):
    """how many cells of the source make one cell of the package; raises QuelleFalsch when it does not fit"""
    f = gitter / zelle
    if f < 1 - 1e-6:
        raise QuelleFalsch("Die Quelle%s hat ein %g-m-Gitter, verlangt sind %g m: eine gröbere Quelle wird NICHT feiner gerechnet. "
                           "Für %g m braucht es eine Quelle mit höchstens %g m (DHM25: %s)." % (was, zelle, gitter, gitter, gitter, DHM25_URL))
    if abs(f - round(f)) > 1e-6:
        raise QuelleFalsch("Gitter %g m ist kein ganzes Vielfaches der Quelle%s (%g m)" % (gitter, was, zelle))
    return int(round(f))


def lies_asc(fh, gitter):
    """ESRI ASCII grid (rows from the north) -> (h with row 0 = south, source cell, xll, yll); nothing is averaged here"""
    hd, first = asc_kopf(fh)
    cols, rows = hd["ncols"], hd["nrows"]
    vals = []
    if first:
        vals.append(np.array(first.split(), np.float32))
    for ln in fh:
        vals.append(np.array(ln.split(), np.float32))
    flat = np.concatenate(vals) if vals else np.zeros(0, np.float32)
    if flat.size != rows * cols:
        raise QuelleFalsch("ASCII-Gitter: %d Werte statt %d" % (flat.size, rows * cols))
    a = flat.reshape(rows, cols)[::-1]                      # row 0 = south
    return np.where(a == hd["nodata"], np.nan, a).astype(np.float32), hd


def aus_teilen(teile, gitter):
    """[(h, head)] of one or many ASCII grids (sheets) -> one grid (h, grid, e0, n0, info) in LV95, averaged to «gitter»"""
    cell = teile[0][1]["cellsize"]
    if any(abs(hd["cellsize"] - cell) > 1e-6 for _h, hd in teile):
        raise QuelleFalsch("die Blätter der Quelle haben verschiedene Gitter")
    f = faktor(gitter, cell)
    x0, y0 = min(hd["xll"] for _h, hd in teile), min(hd["yll"] for _h, hd in teile)
    x1 = max(hd["xll"] + hd["ncols"] * cell for _h, hd in teile)
    y1 = max(hd["yll"] + hd["nrows"] * cell for _h, hd in teile)
    cols, rows = int(round((x1 - x0) / cell)), int(round((y1 - y0) / cell))
    if len(teile) == 1:
        a = teile[0][0]
    else:
        a = np.full((rows, cols), np.nan, np.float32)
        for h, hd in teile:
            i, j = int(round((hd["xll"] - x0) / cell)), int(round((hd["yll"] - y0) / cell))
            alt = a[j:j + h.shape[0], i:i + h.shape[1]]
            a[j:j + h.shape[0], i:i + h.shape[1]] = np.where(np.isfinite(h), h, alt)     # sheets share their border row
    a = _mittel(a, f)
    e0, n0 = x0 + gitter / 2, y0 + gitter / 2
    lv03 = e0 < 1500000
    if lv03:                                                 # LV03 -> LV95 (the difference to the exact change is below 2 m)
        e0, n0 = e0 + 2000000, n0 + 1000000
    return a, float(gitter), float(e0), float(n0), {"zelle": cell, "cols": cols, "rows": rows, "xll": x0, "yll": y0, "lv03": lv03, "blaetter": len(teile)}


def lies_xyz(fh, gitter):
    """«x y z» per line on a regular grid"""
    d = np.loadtxt(fh, dtype=np.float64, comments=("#", "X", "x"))
    xs, ys = np.unique(d[:, 0]), np.unique(d[:, 1])
    cell = float(np.median(np.diff(xs)))
    f = faktor(gitter, cell)
    cols, rows = int(round((xs[-1] - xs[0]) / cell)) + 1, int(round((ys[-1] - ys[0]) / cell)) + 1
    a = np.full((rows, cols), np.nan, np.float32)
    a[np.round((d[:, 1] - ys[0]) / cell).astype(int), np.round((d[:, 0] - xs[0]) / cell).astype(int)] = d[:, 2]
    a = _mittel(a, f)
    e0, n0 = xs[0] + (gitter - cell) / 2, ys[0] + (gitter - cell) / 2
    if e0 < 1500000:
        e0, n0 = e0 + 2000000, n0 + 1000000
    return a, float(gitter), float(e0), float(n0), {"zelle": cell, "cols": cols, "rows": rows, "lv03": xs[0] < 1500000}


def _asc_im_zip(z):
    return sorted(n for n in z.namelist() if n.lower().endswith((".asc", ".agr", ".grd")) and not n.endswith("/"))


def erkunden(quelle, gitter):
    """only the heads (cheap): what is in the source, its grid and extent, the estimate - before any heavy work.
    Raises QuelleFalsch when the grid does not fit."""
    koepfe, namen = [], []
    if quelle.lower().endswith(".zip"):
        with zipfile.ZipFile(quelle) as z:
            for i in z.infolist():
                log("ARCHIV %s %d Bytes" % (i.filename, i.file_size))
            namen = _asc_im_zip(z)
            if not namen:
                raise QuelleFalsch("im Archiv ist kein ESRI-ASCII-Gitter (.asc)")
            for n in namen:
                with z.open(n) as raw:
                    koepfe.append(asc_kopf(io.TextIOWrapper(raw, encoding="latin-1"))[0])
    elif quelle.lower().endswith(".xyz"):
        log("QUELLE-GITTER XYZ-Liste: das Gitter zeigt sich erst beim Lesen")
        return None
    else:
        namen = [os.path.basename(quelle)]
        with open(quelle, encoding="latin-1") as fh:
            koepfe.append(asc_kopf(fh)[0])
    cell = koepfe[0]["cellsize"]
    x0, y0 = min(h["xll"] for h in koepfe), min(h["yll"] for h in koepfe)
    x1, y1 = max(h["xll"] + h["ncols"] * cell for h in koepfe), max(h["yll"] + h["nrows"] * cell for h in koepfe)
    d = (2000000, 1000000) if x0 < 1500000 else (0, 0)
    zellen = sum(h["ncols"] * h["nrows"] for h in koepfe)
    log("QUELLE-GITTER zelle=%g m, %d Datei(en) (%s%s), %d Zellen, %s" % (cell, len(namen), ", ".join(namen[:3]), " …" if len(namen) > 3 else "", zellen,
                                                                      "LV03 -> LV95" if d[0] else "LV95"))
    log("QUELLE-AUSDEHNUNG LV95 E %.0f–%.0f, N %.0f–%.0f (%.0f × %.0f km)" % (x0 + d[0], x1 + d[0], y0 + d[1], y1 + d[1], (x1 - x0) / 1000, (y1 - y0) / 1000))
    f = faktor(gitter, cell, " «%s»" % namen[0])
    log("SCHAETZUNG höchstens %.0f MB bei %g m (%.2f Bytes pro Zelle mit Daten; Zellen ohne Daten kosten nichts)" % (zellen / f / f * B_PRO_ZELLE / 1e6, gitter, B_PRO_ZELLE))
    return {"zelle": cell, "dateien": namen, "zellen": zellen}


def lies(quelle, gitter):
    if quelle.lower().endswith(".zip"):
        with zipfile.ZipFile(quelle) as z:
            namen = _asc_im_zip(z)
            if not namen:
                xyz = next((n for n in z.namelist() if n.lower().endswith(".xyz")), None)
                if not xyz:
                    raise QuelleFalsch("im Archiv ist kein .asc und kein .xyz")
                with z.open(xyz) as raw:
                    return lies_xyz(io.TextIOWrapper(raw, encoding="latin-1"), gitter) + (xyz,)
            teile = []
            for n in namen:
                with z.open(n) as raw:
                    teile.append(lies_asc(io.TextIOWrapper(raw, encoding="latin-1"), gitter))
                faktor(gitter, teile[-1][1]["cellsize"], " «%s»" % n)          # refuse before the next big sheet is read
            return aus_teilen(teile, gitter) + (namen[0] if len(namen) == 1 else "%s + %d" % (namen[0], len(namen) - 1),)
    if quelle.lower().endswith(".xyz"):
        with open(quelle, encoding="latin-1") as fh:
            return lies_xyz(fh, gitter) + (os.path.basename(quelle),)
    with open(quelle, encoding="latin-1") as fh:
        return aus_teilen([lies_asc(fh, gitter)], gitter) + (os.path.basename(quelle),)


def pruefen(aus):
    """the package is there, has the magic, a head that can be read and at least one block; prints what the corners say"""
    p = os.path.join(aus, NAME)
    if not os.path.isfile(p) or os.path.getsize(p) < 64:
        sys.exit("FEHLT: %s - der Bau hat kein Paket geschrieben" % p)
    with open(p, "rb") as f:
        if f.read(8) != MAGIC:
            sys.exit("FALSCH: %s ist kein Höhenpaket" % p)
        H = json.loads(f.read(int.from_bytes(f.read(4), "little")).decode())
    n = sum(1 for b in H["blocks"] if b[1])
    if not n:
        sys.exit("LEER: %s hat keinen Block mit Daten" % p)
    e1, n1 = H["e0"] + (H["cols"] - 1) * H["grid"], H["n0"] + (H["rows"] - 1) * H["grid"]
    log("PAKET %s: %d Bytes, Gitter %g m, Stufe %g m, %d × %d Zellen, %d Blöcke, LV95 E %.0f–%.0f, N %.0f–%.0f, «%s»"
        % (NAME, os.path.getsize(p), H["grid"], H["q"], H["cols"], H["rows"], n, H["e0"], e1, H["n0"], n1, H.get("quelle", "")))
    for nm, (E, N) in ECKEN.items():
        log("LAGE %s (E %d, N %d): %s" % (nm, E, N, "im Rechteck der Daten" if H["e0"] <= E <= e1 and H["n0"] <= N <= n1 else "AUSSERHALB des Rechtecks"))
    return H


def holen(ordner, url=DHM25_URL):
    """download the source; says the address, the HTTP status and the size. No second guess: a wrong address is an error."""
    os.makedirs(ordner, exist_ok=True)
    ziel = os.path.join(ordner, os.path.basename(url.split("?")[0]) or "quelle.zip")
    log("QUELLE-ADRESSE", url)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MoveEye-Kartenbau"}), timeout=900) as r, open(ziel, "wb") as f:
            log("QUELLE-HTTP %s %s, Content-Length %s, endgültige Adresse %s" % (r.status, r.reason, r.headers.get("Content-Length"), r.geturl()))
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
    except urllib.error.HTTPError as e:
        sys.exit("QUELLE-HTTP %s %s - %s ist nicht abrufbar (Adresse auf https://www.swisstopo.admin.ch/de/hoehenmodell-dhm25 prüfen, "
                 "dann mit dem Eingang quelle_url übergeben)" % (e.code, e.reason, url))
    except Exception as e:
        sys.exit("QUELLE nicht abrufbar: %s (%s)" % (url, e))
    if os.path.getsize(ziel) < 1000:
        sys.exit("QUELLE leer: %s (%d Bytes)" % (url, os.path.getsize(ziel)))
    log("QUELLE-DATEI %s bytes=%d sha256=%s" % (ziel, os.path.getsize(ziel), sha256(ziel)))
    return ziel, url


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
    ap.add_argument("--url", default=DHM25_URL)
    ap.add_argument("--quelle")
    ap.add_argument("--erkunden")
    ap.add_argument("--pruefen")
    ap.add_argument("--gitter", type=float, default=25.0)
    ap.add_argument("--stufe", type=float, default=0.5)
    ap.add_argument("--aus", default="hoehe_aus")
    ap.add_argument("--pins", action="store_true")
    ap.add_argument("--eintragen")
    ap.add_argument("--herkunft", default="")
    a = ap.parse_args()
    try:
        if a.holen:
            holen(a.holen, a.url)
        if a.erkunden:
            erkunden(a.erkunden, a.gitter)
        if a.quelle:
            os.makedirs(a.aus, exist_ok=True)
            erkunden(a.quelle, a.gitter)                     # the grid is known and judged before the big file is read
            h, grid, e0, n0, info, name = lies(a.quelle, a.gitter)
            if abs(grid - a.gitter) > 1e-6:
                raise QuelleFalsch("gebaut würde %g m statt %g m" % (grid, a.gitter))
            ziel = os.path.join(a.aus, NAME)
            r = schreibe(ziel, h, grid, e0, n0, a.stufe, "© swisstopo (%s, Gitter %g m)" % (name, grid))
            ok = np.isfinite(h)
            if not ok.any():
                raise QuelleFalsch("die Quelle enthält keine Höhen")
            mess = dict(r, gitter=grid, stufe=a.stufe, e0=e0, n0=n0, quelle=name, url=a.herkunft, quelle_info=info,
                        hoehe_min=float(np.nanmin(h)), hoehe_max=float(np.nanmax(h)), flaeche_km2=float(ok.sum() * grid * grid / 1e6))
            with open(os.path.join(a.aus, "hoehe.json"), "w") as f:
                json.dump(mess, f, indent=1, sort_keys=True)
            log("Höhendaten: %d × %d Zellen à %g m, %.0f km² mit Daten, %.0f–%.0f m, %d Blöcke (+%d leer), %.1f MB"
                % (r["cols"], r["rows"], grid, mess["flaeche_km2"], mess["hoehe_min"], mess["hoehe_max"], r["bloecke"], r["leer"], r["bytes"] / 1e6))
    except QuelleFalsch as e:
        log("QUELLE-FALSCH: %s" % e)
        sys.exit(2)
    if a.pruefen:
        pruefen(a.pruefen)
    if a.pins:
        p = os.path.join(a.aus, NAME)
        if not os.path.isfile(p):
            sys.exit("FEHLT: %s - keine Pins ohne Paket" % p)
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
