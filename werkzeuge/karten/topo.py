#!/usr/bin/env python3
"""MoveEye: the two topo files of the offline map (part 639zzq, «Topo-Karte»), called by paket.py - only on the GitHub
runners (workflow «Offline-Karten»), never on the Pi:

  relief-ch-N.pmtiles   the relief: heights as raster-dem tiles (terrarium in WebP, 256 px, z8..z13), MapLibre shades them
  topo-ch-N.pmtiles     vector tiles z11..z14 with two layers:
                          contour  contour lines every 10 m (ele, lvl 100 / 50 / 20 / 10, gl=1 on a glacier)
                          wege     hiking paths from OpenStreetMap (g 1 yellow / 2 red / 3 blue from sac_scale or the
                                   colour of the hiking route) - NOT the official network of the Swiss hiking trails

Heights: swissALTI3D of swisstopo (decision of the owner 15.11.2026: «10 m»): the 2 m tiles (1 km each, cloud-optimised
GeoTIFF) of the STAC service data.geo.admin.ch, read as averages over 10 m (GDAL reads the overview, not the whole tile) into
one grid in LV95. Free geodata of swisstopo (OGD): free use with the source «© swisstopo».

Steps (paket.py): --hoehe10 (STAC -> dem10.tif) · --wege (OSM -> wege.geojsonl + gletscher.geojsonl) · --hoehenlinien
(gdal_contour + glacier tags -> hk.geojsonl) · --relief (gdalwarp to Web-Mercator, tiles, MBTiles -> PMTiles) · --topo
(tippecanoe -> PMTiles). Needs: numpy, scipy, Pillow, rasterio, shapely, osmium (pyosmium), gdal-bin, tippecanoe, pmtiles.
"""
import concurrent.futures as cf
import io
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request

STAC = ("https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.swissalti3d/items",
        "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d/items")
CH_BBOX = (5.90, 45.80, 10.53, 47.84)              # lon / lat of Switzerland + Liechtenstein (+ a little)
ZELLE = 10.0                                       # m, the grid of dem10.tif
QSTUFE = 4                                         # terrarium: heights in 1/4 m (the lowest byte then has 4 values)
HK_STUFE = 10                                      # m between two contour lines
HK_MINZOOM = {100: 11, 50: 12, 20: 13, 10: 14}     # tippecanoe: from this zoom on (the style shows them the same way)
WEGE_MINZOOM = 12
SAC = {"hiking": 1, "mountain_hiking": 2, "demanding_mountain_hiking": 2, "alpine_hiking": 3, "demanding_alpine_hiking": 3,
       "difficult_alpine_hiking": 3}
R3857 = 2 * math.pi * 6378137.0                    # the width of the world in Web-Mercator metres


def log(*a):
    print(*a, flush=True)


# ---- LV95 <-> WGS84 (the approximate formulas of swisstopo, about 1 m; numpy arrays or numbers) ----------------------------------
def lv95_to_wgs(E, N):
    y, x = (E - 2600000) / 1e6, (N - 1200000) / 1e6
    lam = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y ** 3
    phi = 16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x - 0.0447 * y * y * x - 0.0140 * x ** 3
    return lam * 100 / 36, phi * 100 / 36


def wgs_to_lv95(lon, lat):
    p = (lat * 3600 - 169028.66) / 10000
    l_ = (lon * 3600 - 26782.5) / 10000
    e = 2600072.37 + 211455.93 * l_ - 10938.51 * l_ * p - 0.36 * l_ * p * p - 44.54 * l_ ** 3
    n = 1200147.07 + 308807.95 * p + 3745.25 * l_ * l_ + 76.63 * p * p - 194.56 * l_ * l_ * p + 119.79 * p ** 3
    return e, n


def tile_of(lon, lat, z):
    n = 1 << z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)


def tile_bounds(z, x, y):
    n = 1 << z
    lat = lambda t: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * t / n))))
    return x / n * 360 - 180, lat(y + 1), (x + 1) / n * 360 - 180, lat(y)


# ---- heights: swissALTI3D 2 m -> 10 m (STAC, cloud-optimised GeoTIFF) ---------------------------------------------------------------
def holen_json(url, tries=6):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MoveEye-Kartenbau", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except Exception as e:
            if t == tries - 1:
                raise
            log("  STAC: Versuch %d: %s" % (t + 1, e))
            time.sleep(5 * (t + 1))


def stac_kacheln(bbox):
    """{(E km, N km): (year, href of the 2 m GeoTIFF)} - the newest year of every 1 km tile in bbox (lon/lat)"""
    out, last = {}, None
    for base in STAC:
        url = base + "?limit=100&bbox=%s" % ",".join("%.5f" % v for v in bbox)
        try:
            n = 0
            while url:
                j = holen_json(url)
                for f in j.get("features") or []:
                    m = re.search(r"_(\d{4})_(\d{4})-(\d{4})$", f.get("id") or "")
                    if not m:
                        continue
                    yr, e, nn = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    href = None
                    for a in (f.get("assets") or {}).values():
                        h = a.get("href") or ""
                        if re.search(r"_2_2056_5728\.tif$", h):
                            href = h
                    if not href:
                        for a in (f.get("assets") or {}).values():
                            h = a.get("href") or ""
                            if h.endswith(".tif") and float(a.get("gsd") or a.get("eo:gsd") or 0) == 2.0:
                                href = h
                    if href and (e, nn) not in out or (href and out[(e, nn)][0] < yr):
                        out[(e, nn)] = (yr, href)
                n += 1
                url = next((l["href"] for l in j.get("links") or [] if l.get("rel") == "next"), None)
                if n % 50 == 0:
                    log("  STAC: %d Seiten, %d Kacheln" % (n, len(out)))
            log("STAC %s: %d Kacheln (1 km, 2 m) in %d Seiten" % (base.split("/api/")[1].split("/")[1], len(out), n))
            return out
        except Exception as e:
            last = e
            log("STAC %s geht nicht: %s" % (base, e))
            out = {}
    raise SystemExit("STAC von swisstopo nicht erreichbar: %s" % last)


def hoehe10(aus, bbox=None, threads=16):
    """dem10.tif: swissALTI3D as averages over 10 m (LV95, float32, NaN = no data) + hoehe10.json (tiles, missing, time)"""
    for k, v in {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif", "GDAL_HTTP_MAX_RETRY": "6",
                 "GDAL_HTTP_RETRY_DELAY": "3", "VSI_CACHE": "FALSE", "GDAL_HTTP_TIMEOUT": "90", "GDAL_HTTP_USERAGENT": "MoveEye-Kartenbau",
                 "GDAL_INGESTED_BYTES_AT_OPEN": "32768"}.items():
        os.environ.setdefault(k, v)
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    t0 = time.time()
    kach = stac_kacheln(bbox or CH_BBOX)
    if not kach:
        raise SystemExit("keine swissALTI3D-Kacheln")
    es = [k[0] for k in kach]
    ns = [k[1] for k in kach]
    E0, E1, N0, N1 = min(es) * 1000, (max(es) + 1) * 1000, min(ns) * 1000, (max(ns) + 1) * 1000
    W, H = int((E1 - E0) / ZELLE), int((N1 - N0) / ZELLE)
    log("Gitter 10 m: %d × %d (%.1f GB im Speicher), LV95 %d–%d / %d–%d" % (W, H, W * H * 4 / 1e9, E0, E1, N0, N1))
    a = np.full((H, W), np.nan, np.float32)
    fehl, fertig = [], [0]
    px = int(1000 / ZELLE)

    def eine(item):
        (e, n), (_yr, href) = item
        for t in range(4):
            try:
                with rasterio.open("/vsicurl/" + href) as ds:
                    l, b, r, tp = ds.bounds
                    w_, h_ = int(round((r - l) / ZELLE)), int(round((tp - b) / ZELLE))
                    v = ds.read(1, out_shape=(h_, w_), resampling=Resampling.average, masked=True).astype(np.float32).filled(np.nan)
                c0, r0 = int(round((l - E0) / ZELLE)), int(round((N1 - tp) / ZELLE))
                if not (0 <= c0 and c0 + w_ <= W and 0 <= r0 and r0 + h_ <= H):
                    raise ValueError("ausserhalb des Gitters: %s" % (ds.bounds,))
                v[(v < -500) | (v > 5000)] = np.nan
                a[r0:r0 + h_, c0:c0 + w_] = v
                fertig[0] += 1
                if fertig[0] % 2000 == 0:
                    log("  %d / %d Kacheln, %.0f s" % (fertig[0], len(kach), time.time() - t0))
                return
            except Exception as ex:
                if t == 3:
                    fehl.append((e, n, str(ex)[:120]))
                    return
                time.sleep(3 * (t + 1))
    with cf.ThreadPoolExecutor(threads) as ex:
        list(ex.map(eine, sorted(kach.items())))
    if fehl:
        log("fehlende Kacheln: %d, z. B. %s" % (len(fehl), fehl[:3]))
    if len(fehl) > max(3, 0.002 * len(kach)):
        raise SystemExit("zu viele swissALTI3D-Kacheln fehlen: %d von %d" % (len(fehl), len(kach)))
    ziel = os.path.join(aus, "dem10.tif")
    prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="float32", crs="EPSG:2056", transform=from_origin(E0, N1, ZELLE, ZELLE),
                nodata=float("nan"), tiled=True, blockxsize=512, blockysize=512, compress="deflate", predictor=3, BIGTIFF="IF_SAFER")
    with rasterio.open(ziel, "w", **prof) as ds:
        ds.write(a, 1)
    gut = int(np.count_nonzero(~np.isnan(a)))
    info = {"kacheln": len(kach), "fehlen": len(fehl), "zellen": gut, "km2": round(gut * ZELLE * ZELLE / 1e6), "min": float(np.nanmin(a)),
            "max": float(np.nanmax(a)), "sekunden": round(time.time() - t0), "jahre": sorted({v[0] for v in kach.values()}),
            "groesse": os.path.getsize(ziel), "gitter": [E0, N0, E1, N1, ZELLE]}
    json.dump(info, open(os.path.join(aus, "hoehe10.json"), "w"), indent=1)
    log("dem10.tif: %.0f MB, %d km² mit Höhen, %.0f–%.0f m, %d s" % (info["groesse"] / 1e6, info["km2"], info["min"], info["max"], info["sekunden"]))
    return ziel


# ---- relief: raster-dem tiles (terrarium, WebP lossless) ------------------------------------------------------------------------------
def terrarium(h):
    """heights (float, NaN allowed - then 0) -> RGB uint8, heights in 1/QSTUFE m"""
    import numpy as np
    q = np.round((np.nan_to_num(h, nan=0.0).astype(np.float64) + 32768.0) * QSTUFE).astype(np.int64)
    ip, fr = q // QSTUFE, q % QSTUFE
    return np.stack([(ip >> 8) & 255, ip & 255, fr * (256 // QSTUFE)], -1).astype(np.uint8)


def terrarium_zurueck(rgb):
    import numpy as np
    r, g, b = (rgb[..., i].astype(np.float64) for i in range(3))
    return r * 256 + g + b / 256 - 32768


def webp(rgb):
    from PIL import Image
    bio = io.BytesIO()
    Image.fromarray(rgb).save(bio, "WEBP", lossless=True, quality=60, method=4, exact=True)
    return bio.getvalue()


def fuellen(a, valid, rand=48):
    """NaN outside the data: the nearest height, smoothed further out (no cliff at the border, no stripes)"""
    import numpy as np
    from scipy import ndimage
    if valid.all():
        return a
    if not valid.any():
        return np.zeros_like(a)
    d, (ii, jj) = ndimage.distance_transform_edt(~valid, return_indices=True)
    near = a[ii, jj]
    del ii, jj
    glatt = ndimage.gaussian_filter(near, 24, mode="nearest")
    w = np.clip(d / rand, 0, 1).astype(np.float32)
    return np.where(valid, a, near * (1 - w) + glatt * w).astype(np.float32)


def pyramide(a, z_hi, x0, y0, z_lo, valid13):
    """a: heights of a block of tiles at z_hi (x0, y0 = its first tile) -> [(z, x, y, rgb)], downwards by 2 × 2 means;
    valid13: per z_hi tile «has data (or a neighbour has)»"""
    import numpy as np
    out = []
    n = a.shape[0] // 256
    keep = valid13
    z = z_hi
    while True:
        for ty in range(n):
            for tx in range(n):
                if keep[ty, tx]:
                    out.append((z, x0 + tx, y0 + ty, terrarium(a[ty * 256:(ty + 1) * 256, tx * 256:(tx + 1) * 256])))
        if z == z_lo or n == 1:
            break
        a = a.reshape(a.shape[0] // 2, 2, a.shape[1] // 2, 2).mean(axis=(1, 3))
        keep = keep.reshape(n // 2, 2, n // 2, 2).any(axis=(1, 3))
        n //= 2; z -= 1; x0 //= 2; y0 //= 2
    return out


def _relief_block(args):
    """one block of 2^(zmax-zsup) × … tiles (a z «zsup» tile) from dem3857.tif -> [(z, x, y, webp)]"""
    import numpy as np
    import rasterio
    from rasterio.windows import Window
    from scipy import ndimage
    path, zsup, sx, sy, zmax, zmin, gx0, gy0, rand = args
    k = 1 << (zmax - zsup)
    n = k * 256
    c0, r0 = (sx * k - gx0) * 256, (sy * k - gy0) * 256
    with rasterio.open(path) as ds:
        win = Window(c0 - rand, r0 - rand, n + 2 * rand, n + 2 * rand)
        a = ds.read(1, window=win, boundless=True, fill_value=np.nan).astype(np.float32)
    valid = ~np.isnan(a)
    if not valid.any():
        return []
    core = valid[rand:rand + n, rand:rand + n]
    has = core.reshape(k, 256, k, 256).any(axis=(1, 3))
    has = ndimage.binary_dilation(has, iterations=1)            # the margin of the map (~4 km) gets relief too
    if not has.any():
        return []
    a = fuellen(a, valid)[rand:rand + n, rand:rand + n]
    return [(z, x, y, webp(rgb)) for z, x, y, rgb in pyramide(a, zmax, sx * k, sy * k, max(zmin, zsup), has)]


def relief(aus, dem, name, zmax=13, zmin=8, zsup=8, pmtiles="pmtiles", gdalwarp="gdalwarp", procs=3):
    """dem10.tif -> name (PMTiles, raster-dem terrarium WebP z zmin..zmax); returns the measurement"""
    import numpy as np
    import rasterio
    t0 = time.time()
    with rasterio.open(dem) as ds:
        l, b, r, tp = ds.bounds
    corners = [lv95_to_wgs(e, n) for e in (l, r) for n in (b, tp)]
    lon0, lon1 = min(c[0] for c in corners), max(c[0] for c in corners)
    lat0, lat1 = min(c[1] for c in corners), max(c[1] for c in corners)
    k = 1 << (zmax - zsup)
    sx0, sy0 = tile_of(lon0, lat1, zsup)
    sx1, sy1 = tile_of(lon1, lat0, zsup)
    gx0, gy0 = sx0 * k, sy0 * k                              # the first z_max tile of the grid
    gx1, gy1 = (sx1 + 1) * k, (sy1 + 1) * k
    res = R3857 / (256 << zmax)
    x_min, y_max = -R3857 / 2 + gx0 * 256 * res, R3857 / 2 - gy0 * 256 * res
    x_max, y_min = -R3857 / 2 + gx1 * 256 * res, R3857 / 2 - gy1 * 256 * res
    d3857 = os.path.join(aus, "dem3857.tif")
    log("Relief: gdalwarp nach Web-Mercator z%d (%.3f m), %d × %d Pixel" % (zmax, res, (gx1 - gx0) * 256, (gy1 - gy0) * 256))
    subprocess.run([gdalwarp, "-q", "-overwrite", "-s_srs", "EPSG:2056", "-t_srs", "EPSG:3857", "-te", repr(x_min), repr(y_min), repr(x_max), repr(y_max),
                    "-tr", repr(res), repr(res), "-r", "average", "-srcnodata", "nan", "-dstnodata", "nan", "-ot", "Float32", "-multi",
                    "-wo", "NUM_THREADS=ALL_CPUS", "-wm", "2048", "-co", "TILED=YES", "-co", "COMPRESS=DEFLATE", "-co", "PREDICTOR=3",
                    "-co", "BIGTIFF=YES", dem, d3857], check=True)
    log("  gdalwarp fertig nach %.0f s" % (time.time() - t0))
    mb = os.path.join(aus, "relief.mbtiles")
    if os.path.exists(mb):
        os.remove(mb)
    db = sqlite3.connect(mb)
    db.executescript("CREATE TABLE metadata (name TEXT, value TEXT); CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, "
                     "tile_row INTEGER, tile_data BLOB); CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);")
    meta = {"name": "MoveEye Relief Schweiz", "format": "webp", "type": "baselayer", "minzoom": str(zmin), "maxzoom": str(zmax),
            "bounds": "%.5f,%.5f,%.5f,%.5f" % (lon0, lat0, lon1, lat1), "center": "%.5f,%.5f,%d" % ((lon0 + lon1) / 2, (lat0 + lat1) / 2, zmin),
            "attribution": "© swisstopo", "description": "swissALTI3D 10 m, terrarium (1/%d m), WebP lossless" % QSTUFE, "encoding": "terrarium"}
    db.executemany("INSERT INTO metadata VALUES (?, ?)", sorted(meta.items()))
    jobs = [(d3857, zsup, sx, sy, zmax, zmin, gx0, gy0, 48) for sy in range(sy0, sy1 + 1) for sx in range(sx0, sx1 + 1)]
    pro_z, groesse = {}, {}
    seen = set()
    with cf.ProcessPoolExecutor(procs) as ex:
        for i, res_ in enumerate(ex.map(_relief_block, jobs)):
            for z, x, y, b in res_:
                if (z, x, y) in seen:                          # zsup < zmin: the low tiles of several blocks - keep the first
                    continue
                seen.add((z, x, y))
                db.execute("INSERT INTO tiles VALUES (?, ?, ?, ?)", (z, x, (1 << z) - 1 - y, b))
                pro_z[z] = pro_z.get(z, 0) + 1
                groesse[z] = groesse.get(z, 0) + len(b)
            db.commit()
            log("  Block %d / %d fertig (%d Kacheln, %.0f s)" % (i + 1, len(jobs), sum(pro_z.values()), time.time() - t0))
    db.commit(); db.close()
    os.remove(d3857)
    ziel = os.path.join(aus, name)
    if os.path.exists(ziel):
        os.remove(ziel)
    subprocess.run([pmtiles, "convert", mb, ziel], check=True)
    subprocess.run([pmtiles, "verify", ziel], check=True)
    os.remove(mb)
    m = {"datei": name, "groesse": os.path.getsize(ziel), "kacheln": pro_z, "bytes": groesse, "zmin": zmin, "zmax": zmax,
         "sekunden": round(time.time() - t0)}
    log("Relief: %s %.1f MB, Kacheln %s" % (name, m["groesse"] / 1e6, json.dumps(pro_z, sort_keys=True)))
    return m


# ---- hiking paths and glaciers from OpenStreetMap ---------------------------------------------------------------------------------
def osmc_grad(sym):
    c = (sym or "").split(":")[0].strip().lower()
    return {"yellow": 1, "red": 2, "blue": 3}.get(c, 1)


def wege(aus, pbfs, bbox=None):
    """wege.geojsonl (layer «wege», g 1/2/3) + gletscher.geojsonl (natural=glacier) from OSM extracts (osmium tags-filter)"""
    import osmium
    from shapely import wkb as swkb
    from shapely.geometry import mapping
    t0 = time.time()
    rel = {}

    class R(osmium.SimpleHandler):
        def relation(self, r):
            if r.tags.get("route") in ("hiking", "foot"):
                g = osmc_grad(r.tags.get("osmc:symbol"))
                for m in r.members:
                    if m.type == "w":
                        rel[m.ref] = max(rel.get(m.ref, 0), g)
    for p in pbfs:
        R().apply_file(p)
    log("Wanderrouten: %d Wege in Routen" % len(rel))
    wkbf = osmium.geom.WKBFactory()
    gj = osmium.geom.GeoJSONFactory()
    n = {"wege": 0, "g1": 0, "g2": 0, "g3": 0, "gletscher": 0}
    fw = open(os.path.join(aus, "wege.geojsonl"), "w", encoding="utf-8")
    fg = open(os.path.join(aus, "gletscher.geojsonl"), "w", encoding="utf-8")

    def drin(lon, lat):
        return not bbox or (bbox[0] - 0.05 <= lon <= bbox[2] + 0.05 and bbox[1] - 0.05 <= lat <= bbox[3] + 0.05)

    class W(osmium.SimpleHandler):
        def way(self, w):
            if not w.tags.get("highway"):
                return
            g = SAC.get(w.tags.get("sac_scale") or "", 0) or rel.get(w.id, 0)
            if not g:
                return
            try:
                geo = gj.create_linestring(w)
            except Exception:
                return
            c = json.loads(geo)["coordinates"]
            if not drin(*c[len(c) // 2]):
                return
            fw.write(json.dumps({"type": "Feature", "tippecanoe": {"layer": "wege", "minzoom": WEGE_MINZOOM}, "properties": {"g": g},
                                 "geometry": {"type": "LineString", "coordinates": [[round(x, 6), round(y, 6)] for x, y in c]}},
                                separators=(",", ":")) + "\n")
            n["wege"] += 1; n["g%d" % g] += 1

        def area(self, a):
            if a.tags.get("natural") != "glacier":
                return
            try:
                geo = swkb.loads(wkbf.create_multipolygon(a), hex=True)
            except Exception:
                return
            if geo.is_empty:
                return
            p = geo.representative_point()
            if not drin(p.x, p.y):
                return
            fg.write(json.dumps({"type": "Feature", "properties": {}, "geometry": mapping(geo)}, separators=(",", ":")) + "\n")
            n["gletscher"] += 1
    for p in pbfs:
        W().apply_file(p, locations=True, idx="flex_mem")
    fw.close(); fg.close()
    n["sekunden"] = round(time.time() - t0)
    log("Wege: %s" % json.dumps(n, sort_keys=True))
    return n


# ---- contour lines --------------------------------------------------------------------------------------------------------------------
def stufe(e):
    return 100 if e % 100 == 0 else 50 if e % 50 == 0 else 20 if e % 20 == 0 else 10


def hoehenlinien(aus, dem, gdal_contour="gdal_contour", ogr2ogr="ogr2ogr", simplify=1.0):
    """dem10.tif -> hk.geojsonl (layer «contour»: ele, lvl, gl=1 on a glacier; WGS84)"""
    import numpy as np
    import shapely
    from shapely.geometry import shape, LineString
    from shapely.strtree import STRtree
    t0 = time.time()
    polys = []
    gp = os.path.join(aus, "gletscher.geojsonl")
    if os.path.isfile(gp):
        for line in open(gp, encoding="utf-8"):
            g = shape(json.loads(line)["geometry"])
            polys.append(shapely.transform(g, lambda c: np.stack(wgs_to_lv95(c[:, 0], c[:, 1]), 1)))
    tree = STRtree(polys) if polys else None
    log("Höhenlinien: %d Gletscher-Flächen" % len(polys))
    gpkg = os.path.join(aus, "hk.gpkg")
    if os.path.exists(gpkg):
        os.remove(gpkg)
    subprocess.run([gdal_contour, "-q", "-a", "ele", "-i", str(HK_STUFE), "-f", "GPKG", "-nln", "hk", dem, gpkg], check=True)
    log("  gdal_contour fertig nach %.0f s, %.0f MB" % (time.time() - t0, os.path.getsize(gpkg) / 1e6))
    # GeoJSONSeq may write WGS84 by itself (RFC 7946): the coordinates are looked at below, LV95 or lon / lat both work
    pr = subprocess.Popen([ogr2ogr, "-f", "GeoJSONSeq", "/vsistdout/", gpkg, "hk", "-simplify", str(simplify)],
                          stdout=subprocess.PIPE, bufsize=1 << 20)
    out = open(os.path.join(aus, "hk.geojsonl"), "w", encoding="utf-8")
    n = {"linien": 0, "punkte": 0, "gletscher": 0}

    def schreibe(ls, ele, gl):
        c = np.asarray(ls.coords)
        if len(c) < 2:
            return
        lon, lat = lv95_to_wgs(c[:, 0], c[:, 1])
        lv = stufe(ele)
        pr_ = {"ele": ele, "lvl": lv}
        if gl:
            pr_["gl"] = 1
        out.write('{"type":"Feature","tippecanoe":{"layer":"contour","minzoom":%d},"properties":%s,"geometry":{"type":"LineString","coordinates":%s}}\n'
                  % (HK_MINZOOM[lv], json.dumps(pr_, separators=(",", ":")),
                     json.dumps(np.round(np.stack([lon, lat], 1), 6).tolist(), separators=(",", ":"))))
        n["linien"] += 1; n["punkte"] += len(c); n["gletscher"] += 1 if gl else 0

    def teile(g):
        if g.is_empty:
            return []
        if g.geom_type == "LineString":
            return [g]
        return [x for x in getattr(g, "geoms", []) if x.geom_type == "LineString"] + \
               [y for x in getattr(g, "geoms", []) if x.geom_type == "MultiLineString" for y in x.geoms]
    for line in pr.stdout:
        f = json.loads(line)
        ele = int(round(float(f["properties"]["ele"])))
        geo = f.get("geometry") or {}
        cs = [geo["coordinates"]] if geo.get("type") == "LineString" else geo.get("coordinates") or []
        for c in cs:
            if len(c) < 2:
                continue
            c = np.asarray(c, dtype=np.float64)[:, :2]
            if abs(c[0, 0]) < 400:                             # lon / lat (the driver reprojected): back to LV95 for the glaciers
                c = np.stack(wgs_to_lv95(c[:, 0], c[:, 1]), 1)
            ls = LineString(c)
            hit = tree.query(ls, predicate="intersects") if tree is not None else []
            if len(hit):
                gg = shapely.union_all([polys[i] for i in hit])
                for p in teile(ls.intersection(gg)):
                    schreibe(p, ele, True)
                for p in teile(ls.difference(gg)):
                    schreibe(p, ele, False)
            else:
                schreibe(ls, ele, False)
        if n["linien"] and n["linien"] % 200000 == 0:
            log("  %d Linien, %d Punkte, %.0f s" % (n["linien"], n["punkte"], time.time() - t0))
    out.close()
    if pr.wait() != 0:
        raise SystemExit("ogr2ogr fehlgeschlagen")
    os.remove(gpkg)
    n["sekunden"] = round(time.time() - t0)
    n["groesse"] = os.path.getsize(os.path.join(aus, "hk.geojsonl"))
    log("Höhenlinien: %s" % json.dumps(n, sort_keys=True))
    return n


# ---- the vector file (tippecanoe) -------------------------------------------------------------------------------------------------------
def topo_pmtiles(aus, name, tippecanoe="tippecanoe", pmtiles="pmtiles"):
    t0 = time.time()
    ins = [os.path.join(aus, f) for f in ("hk.geojsonl", "wege.geojsonl") if os.path.isfile(os.path.join(aus, f))]
    if len(ins) != 2:
        raise SystemExit("--topo braucht hk.geojsonl und wege.geojsonl")
    mb = os.path.join(aus, "topo.mbtiles")
    subprocess.run([tippecanoe, "-q", "--force", "-o", mb, "-Z", "11", "-z", "14", "-P", "--no-feature-limit", "--no-tile-size-limit",
                    "--buffer", "8", "-n", "MoveEye Topo Schweiz", "-A", "© swisstopo · © OpenStreetMap-Mitwirkende",
                    "--attribute-type=ele:int", "--attribute-type=lvl:int", "--attribute-type=gl:int", "--attribute-type=g:int"] + ins, check=True)
    ziel = os.path.join(aus, name)
    if os.path.exists(ziel):
        os.remove(ziel)
    subprocess.run([pmtiles, "convert", mb, ziel], check=True)
    subprocess.run([pmtiles, "verify", ziel], check=True)
    db = sqlite3.connect(mb)
    pro_z = {z: [c, s] for z, c, s in db.execute("SELECT zoom_level, COUNT(*), SUM(LENGTH(tile_data)) FROM tiles GROUP BY zoom_level")}
    big = db.execute("SELECT MAX(LENGTH(tile_data)) FROM tiles").fetchone()[0]
    db.close()
    os.remove(mb)
    m = {"datei": name, "groesse": os.path.getsize(ziel), "kacheln": pro_z, "groesste_kachel": big, "sekunden": round(time.time() - t0)}
    log("Topo: %s %.1f MB, pro Zoom %s, grösste Kachel %d B" % (name, m["groesse"] / 1e6, json.dumps(pro_z, sort_keys=True), big))
    return m
