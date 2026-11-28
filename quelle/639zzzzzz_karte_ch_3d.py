#@ MoveEye – Teil 639zzzzzz: «2D / 3D» auf der Schweizer Karte (/karte, «🗺 Schweiz») – Gelände in 3D wie auf der Bergtal-Karte (neigen, drehen, Relief); Höhen-Kacheln (terrarium) rechnet MoveEye selbst aus dem Paket «Höhendaten Schweiz» (/karte/dem/…, Zwischenspeicher mit Grenze), oder nimmt das Relief der Topo-Karte. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Idee 42 des Besitzers «Schweizer Karte in 3D» (28.11.2026):
#   * Schalter «2D | 3D» oben links in der Karte, gleich wie im Bergtal (639zzzzzt, Klasse kq-sw); auf der Schweizer Karte
#     steht dort schon «Standard | Topo» – «2D | 3D» kommt direkt darunter. Pro Browser gemerkt (mw-kq-3d). 3D: Gelände
#     (setTerrain, Überhöhung K3_EX), neigen und drehen (zwei Finger, rechte Maustaste, Kompass), Himmel; 2D wie bisher.
#     Auch im Vollbild «⛶» (der Schalter liegt im Kartenkasten).
#   * Höhen, in dieser Reihenfolge: (a) das Relief der Topo-Karte (relief-ch-N.pmtiles, swissALTI3D 10 m, terrarium-WebP
#     z8–13, ist schon da und kostet den Pi nichts); (b) sonst Kacheln aus dem Paket «Höhendaten Schweiz» (639zzx, DHM25
#     25 m): GET /karte/dem/<key>/<z>/<x>/<y>.png, 256 px terrarium-PNG, z KD_Z (8–13; darüber vergrössert MapLibre),
#     bilinear zwischen den Zellen, ausserhalb der Daten 0 m. Gerechnet mit numpy beim ersten Abruf (höchstens KD_PAR
#     gleichzeitig), dann im Zwischenspeicher DATA_DIR/karte_hoehe/kacheln/<key>/ (höchstens KD_CACHE_MAX, die am längsten
#     nicht gebrauchten zuerst weg; nicht, wenn die Karte zu voll ist; «Entfernen» der Höhendaten löscht ihn mit). Nichts wird
#     im Voraus gerechnet. (c) ohne beides: der Knopf «3D» zeigt «3D braucht die Höhendaten Schweiz» mit dem Link zum Laden
#     (Admin; sonst «Der Admin kann sie laden»).
#   * Host (639zzzzw): keine Höhendaten, keine Schweizer Karte – dort kein Schalter und keine Kacheln.
#   * Texte in 5 Sprachen; das Fenster (Tk) hat keine Offline-Karte – dort nichts. Der Live-Reiter bleibt unverändert.
# Selbsttest karte3d_selftest; Test werkzeuge/karte_3d_test.py (Kodierung hin und zurück, Kacheln aus einer kleinen
# Höhendatei, Zwischenspeicher mit Grenze, Rechte, Seite im Browser 390 × 844 DPR 2 und 1366 × 768).
# ----------------------------------------------------------------------------
# Der Programmtext steht in EINEM Literal (Hauptdatei klein, wie 639zzzzzt): werkzeuge/bauen.py legt es in die Zusatz-ZIP
# (über ZD_SHA256 mit signiert). Ohne ZIP gibt es kein 3D – es gehört nicht zu Start, Schutz, Alarm, Update oder Reparatur.
K3_PY = r'''K3_FORMAT = 1
KD_Z = (8, 13)                                            # zoom levels of the generated tiles (25 m grid: z12 = 26 m per pixel)
KD_N = 256                                                # pixels per side
KD_VER = 1                                                # in the address: a new way of computing = new tiles in the browser
KD_CACHE_MAX = 256 * 1024 * 1024                          # bytes of generated tiles on the memory card
KD_STEP = 8                                               # heights in 1/8 m (decoded within 0.07 m; PNG ~30 % smaller than 1/256 m)
KD_PAR = 2                                                # tiles computed at the same time (the Pi stays responsive)
K3_EX = 1.3                                               # exaggeration of the terrain in 3D
KD_RT = {"lock": threading.Lock(), "sem": threading.BoundedSemaphore(KD_PAR), "bytes": None, "dir": None, "bounds": {}, "flat": None,
         "made": 0, "hits": 0, "ms": 0.0}


def kd_encode(h):
    """heights (m, float array) -> uint8 RGB (terrarium: h = R·256 + G + B/256 − 32768, steps of 1/256 m)"""
    u = np.clip(np.rint((np.asarray(h, np.float64) + 32768.0) * 256.0), 0, (1 << 24) - 1).astype(np.uint32)
    return np.stack([(u >> 16) & 255, (u >> 8) & 255, u & 255], axis=-1).astype(np.uint8)


def kd_decode(rgb):
    a = np.asarray(rgb, np.float64)
    return a[..., 0] * 256.0 + a[..., 1] + a[..., 2] / 256.0 - 32768.0


def kd_png(rgb):
    """RGB -> PNG bytes (OpenCV if there, else zlib by hand)"""
    try:
        ok_, b_ = cv2.imencode(".png", np.ascontiguousarray(rgb[..., ::-1]), [cv2.IMWRITE_PNG_COMPRESSION, 6])
        if ok_:
            return b_.tobytes()
    except Exception:
        pass
    import zlib
    h_, w_ = rgb.shape[:2]
    raw = b"".join(b"\x00" + rgb[j].tobytes() for j in range(h_))

    def chunk(t, d):
        c = zlib.crc32(t + d) & 0xFFFFFFFF
        return len(d).to_bytes(4, "big") + t + d + c.to_bytes(4, "big")
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", w_.to_bytes(4, "big") + h_.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00")
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def kd_wgs84(E, N):
    """LV95 -> (lat, lon), the approximate formulas of swisstopo (about 1 m; the reverse of kh_lv95)"""
    y, x = (E - 2600000.0) / 1e6, (N - 1200000.0) / 1e6
    lo = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y ** 3
    la = 16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x - 0.0447 * y * y * x - 0.0140 * x ** 3
    return la * 100.0 / 36.0, lo * 100.0 / 36.0


def kd_bounds(f):
    """[west, south, east, north] of the height file (a little margin) - MapLibre asks for no tile outside"""
    b = KD_RT["bounds"].get(id(f))
    if b is None:
        E = [f.e0 - f.grid, f.e0 + (f.cols / 2.0) * f.grid, f.e0 + f.cols * f.grid]
        N = [f.n0 - f.grid, f.n0 + (f.rows / 2.0) * f.grid, f.n0 + f.rows * f.grid]
        pts = [kd_wgs84(e, n) for e in E for n in N]
        b = [round(min(p[1] for p in pts) - 0.01, 4), round(min(p[0] for p in pts) - 0.01, 4),
             round(max(p[1] for p in pts) + 0.01, 4), round(max(p[0] for p in pts) + 0.01, 4)]
        KD_RT["bounds"] = {id(f): b}
    return b


def _kd_gather(f, cx, cy):
    """cell values (m) at integer cells cx / cy (flat int arrays), NaN = no data; every block is unpacked once"""
    out = np.full(cx.shape, np.nan, np.float32)
    idx = np.nonzero((cx >= 0) & (cx < f.cols) & (cy >= 0) & (cy < f.rows))[0]
    if not len(idx):
        return out
    B = f.block
    bi = (cy[idx] // B) * f.bx + cx[idx] // B
    order = np.argsort(bi, kind="stable")
    bs = bi[order]
    starts = np.flatnonzero(np.r_[True, bs[1:] != bs[:-1]])
    ends = np.r_[starts[1:], len(bs)]
    for s, e in zip(starts, ends):
        blk = f._block(int(bs[s]))
        if blk is False:
            continue
        sel = idx[order[s:e]]
        v = blk[cy[sel] % B, cx[sel] % B]
        good = v != f.nodata
        out[sel[good]] = v[good].astype(np.float32) * f.q
    return out


def kd_heights(f, z, x, y, n=KD_N):
    """the heights (m) of the n × n pixel centres of tile z/x/y (Web Mercator, row 0 = north): bilinear between the four cells
    around each pixel, cells without data left out; nowhere data = 0 m. None = the tile lies outside the file."""
    s = float(1 << z)
    p = (np.arange(n, dtype=np.float64) + 0.5) / n
    lon = (x + p) / s * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1.0 - 2.0 * (y + p) / s))))
    LO, LA = np.meshgrid(lon, lat)
    E, N = kh_lv95(LA, LO)
    fx, fy = (E - f.e0) / f.grid, (N - f.n0) / f.grid
    if fx.max() < -1 or fy.max() < -1 or fx.min() > f.cols or fy.min() > f.rows:
        return None
    x0, y0 = np.floor(fx).astype(np.int64).ravel(), np.floor(fy).astype(np.int64).ravel()
    tx, ty = (fx.ravel() - x0).astype(np.float32), (fy.ravel() - y0).astype(np.float32)
    m = len(x0)
    v = _kd_gather(f, np.concatenate([x0, x0 + 1, x0, x0 + 1]), np.concatenate([y0, y0, y0 + 1, y0 + 1])).reshape(4, m)
    w = np.stack([(1 - tx) * (1 - ty), tx * (1 - ty), (1 - tx) * ty, tx * ty])
    ok_ = np.isfinite(v)
    ws = np.where(ok_, w, 0).sum(axis=0)
    h = np.where(ok_, v * w, 0).sum(axis=0)
    h = np.where(ws > 1e-6, h / np.maximum(ws, 1e-6), 0.0)
    return h.reshape(n, n)


def kd_key():
    """part of the tile address: the height file (its checksum) and the way of computing - a new one = new browser cache"""
    return (KH_FILE.get("sha256") or "0" * 12)[:12] + "v%d" % KD_VER


def kd_host():
    return bool((globals().get("HOST") or {}).get("on"))


def kd_on():
    return bool(not kd_host() and "KhFile" in globals() and kh_installed())


def kd_flat():
    if KD_RT["flat"] is None:
        KD_RT["flat"] = kd_png(kd_encode(np.zeros((KD_N, KD_N))))
    return KD_RT["flat"]


def kd_cache_dir():
    return os.path.join(os.path.dirname(kh_path()), "kacheln", kd_key())


def _kd_scan():
    """the bytes in the cache (once); folders of an older key are removed"""
    d_ = kd_cache_dir()
    if KD_RT["dir"] == d_ and KD_RT["bytes"] is not None:
        return
    top = os.path.dirname(d_)
    try:
        for x_ in os.listdir(top):
            if x_ != os.path.basename(d_) and re.fullmatch(r"[0-9a-f]{12}v\d{1,3}", x_):
                shutil.rmtree(os.path.join(top, x_), ignore_errors=True)
    except OSError:
        pass
    tot = 0
    try:
        for e in os.scandir(d_):
            if e.name.endswith(".png"):
                tot += e.stat().st_size
    except OSError:
        pass
    KD_RT["dir"], KD_RT["bytes"] = d_, tot


def kd_trim(limit=None):
    """keep the cache under its limit: the tiles not used for the longest time go first (down to 80 %)"""
    limit = KD_CACHE_MAX if limit is None else limit
    with KD_RT["lock"]:
        _kd_scan()
        if KD_RT["bytes"] <= limit:
            return 0
        fs = []
        try:
            for e in os.scandir(KD_RT["dir"]):
                if e.name.endswith(".png"):
                    st = e.stat()
                    fs.append((st.st_mtime, st.st_size, e.path))
        except OSError:
            pass
        fs.sort()
        tot, gone = sum(x[1] for x in fs), 0
        for _t, sz, p_ in fs:
            if tot <= limit * 0.8:
                break
            try:
                os.remove(p_)
                tot -= sz
                gone += 1
            except OSError:
                pass
        KD_RT["bytes"] = tot
        return gone


def _kd_room():
    try:
        return kq_free() >= bio_free_need()
    except Exception:
        return True


def kd_tile(z, x, y):
    """PNG bytes of tile z/x/y (from the cache or computed), or None = not in the range of the tiles"""
    if not (KD_Z[0] <= z <= KD_Z[1] and 0 <= x < (1 << z) and 0 <= y < (1 << z)):
        return None
    p_ = os.path.join(kd_cache_dir(), "%d-%d-%d.png" % (z, x, y))
    try:
        with open(p_, "rb") as fh:
            b_ = fh.read()
        try:
            os.utime(p_)                                   # used = young again (the cache throws out the oldest)
        except OSError:
            pass
        KD_RT["hits"] += 1
        return b_
    except OSError:
        pass
    with KD_RT["sem"]:
        t0 = time.time()
        h = kd_heights(kh_file(), z, x, y)
        if h is None:
            return kd_flat()
        b_ = kd_png(kd_encode(np.rint(h * KD_STEP) / KD_STEP))
        KD_RT["made"] += 1
        KD_RT["ms"] += (time.time() - t0) * 1000.0
    if _kd_room():
        try:
            os.makedirs(os.path.dirname(p_), exist_ok=True)
            tmp_ = p_ + ".%d.part" % threading.get_ident()
            with open(tmp_, "wb") as fh:
                fh.write(b_)
            os.replace(tmp_, p_)
            with KD_RT["lock"]:
                _kd_scan()
                KD_RT["bytes"] += len(b_)
                over = KD_RT["bytes"] > KD_CACHE_MAX
            if over:
                kd_trim()
        except OSError:
            pass
    return b_


def kd_state():
    """what the page needs for 3D"""
    if kd_host():
        return {"on": False, "host": True}
    on = kd_on()
    out = {"on": on, "host": False, "key": kd_key(), "z": list(KD_Z)}
    if on:
        try:
            out["bounds"] = kd_bounds(kh_file())
        except (OSError, ValueError, KeyError):
            out["on"] = False
    return out


# ---- web: the tiles ---------------------------------------------------------------------------------------------------------------
_smalltv_routes_639zzzzzz = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzzzzz: /karte/dem/<key>/<z>/<x>/<y>.png
    _smalltv_routes_639zzzzzz(app, reply, body)
    from flask import Response

    @app.route("/karte/dem/<key>/<int:z>/<int:x>/<int:y>.png")
    def kd_tile_(key, z, x, y):
        if key != kd_key() or not kd_on():
            return Response(b"", status=404, mimetype="text/plain")
        try:
            b_ = kd_tile(z, x, y)
        except (OSError, ValueError, KeyError) as e:
            log_event("sys", f"3D map: height tile {z}/{x}/{y} not made ({e.__class__.__name__})")
            return Response(b"", status=500, mimetype="text/plain")
        if b_ is None:
            return Response(b"", status=404, mimetype="text/plain")
        return Response(b_, mimetype="image/png", headers={"Cache-Control": "public, max-age=2592000, immutable"})


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_K3 = {
    "3D needs the height data of Switzerland.": ("3D braucht die Höhendaten Schweiz.", "La 3D nécessite les données d’altitude de la Suisse.",
                                                  "Il 3D richiede i dati di quota della Svizzera.", "3D dovra las datas d’autezza da la Svizra."),
    "Load height data of Switzerland": ("Höhendaten Schweiz laden", "Charger les données d’altitude de la Suisse", "Carica i dati di quota della Svizzera",
                                        "Chargiar las datas d’autezza da la Svizra"),
    "The administrator can load them.": ("Der Admin kann sie laden.", "L’administrateur peut les charger.", "L’amministratore può caricarli.",
                                         "L’administratur las po chargiar."),
    "3D – two fingers turn and tilt the map": ("3D – mit zwei Fingern drehen und neigen", "3D – deux doigts pour tourner et incliner la carte",
                                              "3D – due dita per ruotare e inclinare la mappa", "3D – dus dets per volver ed inclinar la charta"),
    "2D – map from above": ("2D – Karte von oben", "2D – carte vue d’en haut", "2D – mappa vista dall’alto", "2D – charta da sura"),
    "Map view": ("Kartenansicht", "Vue de la carte", "Vista della mappa", "Vista da la charta"),
}
for _k, _v in _HX_K3.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def k3_tx():
    out = {"en": {k: k for k in _HX_K3}}
    for i_, L_ in enumerate(("de", "fr", "it", "rm")):
        out[L_] = {k: v[i_] for k, v in _HX_K3.items()}
    return out


# ---- the browser part (only on the map of Switzerland; the Bergtal has its own switch) ----------------------------------------------
K3_CSS = """
#kq-map .kq-3d.kq-3d-2{top:52px}
#kq-map.kq-fs .kq-3d.kq-3d-2{top:calc(52px + env(safe-area-inset-top,0px))}
.kq-3dhint{position:absolute;left:8px;top:52px;z-index:5;max-width:min(300px,calc(100% - 70px));background:rgba(255,255,255,.96);color:#123;border-radius:10px;padding:8px 10px;font:13px/1.4 system-ui,sans-serif;box-shadow:0 1px 4px rgba(0,0,0,.35)}
.kq-3d-2~.kq-3dhint{top:96px}
#kq-map.kq-fs .kq-3dhint{top:calc(52px + env(safe-area-inset-top,0px));left:calc(8px + env(safe-area-inset-left,0px))}
#kq-map.kq-fs .kq-3d-2~.kq-3dhint{top:calc(96px + env(safe-area-inset-top,0px))}
.kq-3dhint a{color:#1a5fd0;font-weight:600;display:inline-block;margin-top:4px;min-height:28px;line-height:28px}
body:not(.light) .kq-3dhint{background:rgba(22,25,28,.94);color:#e6eaef}body:not(.light) .kq-3dhint a{color:#8ab8ff}
"""
K3_JS = r"""
// 639zzzzzz: «2D | 3D» on the map of Switzerland - the terrain from the relief of the topo map, else from /karte/dem (height data)
(function () {
  const K3 = window.K3 = /*K3STATE*/{}, TX = /*K3TX*/{};
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const T = k => (TX[L()] || {})[k] || (TX.en || {})[k] || k;
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const dark = () => !(document.body && document.body.classList.contains("light"));
  const EX = /*K3EX*/1.3;
  let map = null, ready = false, comp = null, nudgeT = 0, hintT = 0;
  K3.d3 = false;
  // where the heights come from: the relief of the topo map (10 m), else the tiles MoveEye makes from the height data (25 m)
  K3.src = () => {
    const LY = (window.KQ && KQ.layers) || {}, R = LY.relief, D = K3.dem || {};
    if (R && R.key) return {type: "raster-dem", tiles: [location.origin + "/karte/t/" + R.key + "/relief/{z}/{x}/{y}." + (R.ext || "webp")], tileSize: 256,
      encoding: "terrarium", minzoom: R.z[0], maxzoom: R.z[1], bounds: R.bounds};
    if (D.on && D.key) return {type: "raster-dem", tiles: [location.origin + "/karte/dem/" + D.key + "/{z}/{x}/{y}.png"], tileSize: 256,
      encoding: "terrarium", minzoom: D.z[0], maxzoom: D.z[1], bounds: D.bounds};
    return null;
  };
  K3.from = () => { const s = K3.src(); return !s ? "" : (/\/relief\//.test(s.tiles[0]) ? "relief" : "dem"); };
  const hill = () => dark() ? {"hillshade-exaggeration": 0.45, "hillshade-shadow-color": "#000000", "hillshade-highlight-color": "rgba(160,176,198,0.30)", "hillshade-accent-color": "rgba(0,0,0,0.25)"}
    : {"hillshade-exaggeration": 0.42, "hillshade-shadow-color": "#465472", "hillshade-highlight-color": "#fffdf6", "hillshade-accent-color": "#7a6c58"};
  const below = () => { const ls = (map.getStyle() || {}).layers || []; const r = ls.find(l => /^roads?_|^road/.test(l.id)) || ls.find(l => l.type === "symbol"); return r ? r.id : undefined; };
  // terrain + relief for the style that is there now (also after «Standard / Topo» or light / dark: a new style)
  function apply() {
    if (!map || !ready) return;
    const S = (map.getStyle() || {}).sources || {}, rel = !!(S.relief && S.relief.tiles && S.relief.tiles.length);
    try {
      if (K3.d3) {
        let sid = "relief";
        if (!rel) { sid = "kq-dem"; if (!map.getSource(sid)) map.addSource(sid, K3.src());
          if (!map.getLayer("kq-hill")) map.addLayer({id: "kq-hill", type: "hillshade", source: sid, paint: hill()}, below()); }
        else if (map.getLayer("kq-hill")) map.removeLayer("kq-hill");
        const t = map.getTerrain && map.getTerrain(); if (!t || t.source !== sid) map.setTerrain({source: sid, exaggeration: EX});
        try { map.setSky({"sky-color": dark() ? "#1b2a40" : "#9cc7ef", "horizon-color": dark() ? "#3a4a60" : "#eef4fa", "fog-color": dark() ? "#2a3340" : "#eef2f5", "sky-horizon-blend": 0.5, "horizon-fog-blend": 0.8, "fog-ground-blend": 0.25}); } catch (e) {}
      } else {
        if (map.getTerrain && map.getTerrain()) map.setTerrain(null);
        if (map.getLayer("kq-hill")) map.removeLayer("kq-hill");
      }
    } catch (e) { if (window.console) console.warn("3D", e); }
    credit();
  }
  // the heights are © swisstopo (DHM25 / swissALTI3D): in 3D the credit says so also on the standard map
  function credit() {
    document.querySelectorAll("#kq-map .kq-attr").forEach(a => { if (!window.KQ || !KQ.at) return; KQ.at(a);
      if (K3.d3 && !/swisstopo/.test(a.textContent)) { const x = el("a", "", "swisstopo"); x.href = "https://www.swisstopo.admin.ch"; x.target = "_blank"; x.rel = "noopener"; a.append(" · © ", x); } });
  }
  function paint() { document.querySelectorAll(".kq-3d button").forEach(b => { const on = (b.dataset.v === "3d") === K3.d3; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on ? "true" : "false"); }); }
  function hint() {
    const box = document.getElementById("kq-map"); if (!box) return; let h = document.getElementById("kq-3dhint");
    if (!h) { h = el("div", "kq-3dhint"); h.id = "kq-3dhint"; h.setAttribute("role", "status"); box.appendChild(h); h.onclick = e => e.stopPropagation(); }
    h.textContent = ""; h.appendChild(el("div", "", "⛰ " + T("3D needs the height data of Switzerland.")));
    if (window.KQ && KQ.admin) { const a = el("a", "", T("Load height data of Switzerland") + " ›"); a.href = "#kt-hoehe"; a.id = "kq-3dload";
      a.onclick = e => { e.preventDefault(); h.hidden = true; const fs = document.getElementById("kq-full");
        if (box.classList.contains("kq-fs") && fs) fs.click();
        setTimeout(() => { const t = document.getElementById("kt-hbox") || document.getElementById("kt-hoehe") || document.getElementById("kt"); if (t) t.scrollIntoView({behavior: "smooth", block: "center"}); }, 200); };
      h.appendChild(a); }
    else h.appendChild(el("div", "", T("The administrator can load them.")));
    h.hidden = false; clearTimeout(hintT); hintT = setTimeout(() => { h.hidden = true; }, 9000);
  }
  K3.set = (v, quick) => {
    if (v && !K3.src()) { hint(); v = false; }
    else { const h = document.getElementById("kq-3dhint"); if (h) h.hidden = true; }
    K3.d3 = v; try { localStorage.setItem("mw-kq-3d", v ? "1" : "0"); } catch (e) {}
    paint();
    if (!map || !ready) return;                                         // before «load»: the load handler does it
    clearInterval(nudgeT);
    if (v) {
      map.setMaxPitch(80); map.dragRotate.enable(); map.touchZoomRotate.enableRotation(); map.touchPitch.enable(); map.keyboard.enableRotation();
      if (!comp) { comp = new maplibregl.NavigationControl({showZoom: false, showCompass: true, visualizePitch: true}); map.addControl(comp, "top-right"); }
      apply();
      // first the terrain, then the tilt: before the height under the centre is known MapLibre would put the camera at 0 m
      // (inside the mountain - learnt on the Bergtal map). Wait for it (at most ~6 s), nudge a little, then tilt.
      let n = 0;
      const elev = () => { try { return map.queryTerrainElevation(map.getCenter()) || 0; } catch (e) { return 0; } };
      const tilt = () => map.easeTo({pitch: 60, bearing: map.getBearing() || -20, zoom: Math.max(map.getZoom(), 9), duration: quick ? 0 : 700});
      nudgeT = setInterval(() => { if (!K3.d3) { clearInterval(nudgeT); return; }
        n++; if (!map.getTerrain()) { if (n > 60) clearInterval(nudgeT); else apply(); return; }   // the style was still loading: again
        if (elev() > 0 || n > 12) { clearInterval(nudgeT); tilt();
          map.once("moveend", () => { if (K3.d3) { const c = map.getCenter(); map.jumpTo({center: [c.lng + 2e-5, c.lat]}); } }); return; }
        if (n % 3 === 0) { const c = map.getCenter(); map.jumpTo({center: [c.lng + (n % 2 ? 2e-5 : -2e-5), c.lat]}); } }, 500);
    } else {
      apply();
      map.dragRotate.disable(); map.touchZoomRotate.disableRotation(); map.touchPitch.disable(); map.keyboard.disableRotation();
      if (comp) { try { map.removeControl(comp); } catch (e) {} comp = null; }
      map.easeTo({pitch: 0, bearing: 0, duration: quick ? 0 : 500});
      map.once("moveend", () => { if (!K3.d3) map.setMaxPitch(0); });
    }
  };
  // called by the page of the map of Switzerland (639zzq) right after the map is made
  window.kq3d = m => {
    if (K3.host || !m || map) return;
    map = m; const box = document.getElementById("kq-map"); if (!box) return;
    const sw = el("div", "kq-sw kq-3d"); sw.setAttribute("role", "group"); sw.setAttribute("aria-label", T("Map view"));
    if (box.querySelector(".kq-sw")) sw.classList.add("kq-3d-2");      // under «Standard | Topo»
    [["2d", "2D", "2D – map from above"], ["3d", "3D", "3D – two fingers turn and tilt the map"]].forEach(([v, n, tt]) => {
      const b = el("button", "", n); b.type = "button"; b.dataset.v = v; b.id = "kq-" + v; b.title = T(tt);
      b.onclick = e => { e.stopPropagation(); K3.set(v === "3d"); }; sw.appendChild(b); });
    box.appendChild(sw);
    let want = false; try { want = localStorage.getItem("mw-kq-3d") === "1"; } catch (e) {}
    K3.d3 = want && !!K3.src(); paint();
    m.on("style.load", () => { if (ready) apply(); });                  // «Standard / Topo», light / dark: a new style
    const go = () => { ready = true; if (K3.d3) K3.set(true, true); };
    if (m.loaded()) go(); else m.once("load", go);
  };
})();
"""
_K3_HOOK_A = "  kqFull(m);\n"
_K3_HOOK_B = "  kqFull(m); if (window.kq3d) kq3d(m);\n"
_kq_page_639zzzzzz = kq_page


# wraps: kq_page
def kq_page():                                              # + 639zzzzzz: the switch «2D | 3D» on the map of Switzerland
    html = _kq_page_639zzzzzz()
    if "window.K3 = " in html or html.count(_K3_HOOK_A) != 1 or "</head>" not in html:
        return html
    st = {"dem": kd_state(), "host": kd_host()}
    js = (K3_JS.replace("/*K3STATE*/{}", json.dumps(st), 1).replace("/*K3EX*/1.3", repr(float(K3_EX)), 1)
          .replace("/*K3TX*/{}", json.dumps(k3_tx(), ensure_ascii=False).replace("</", "<\\/"), 1))
    return (html.replace(_K3_HOOK_A, _K3_HOOK_B, 1)
            .replace("</head>", "<style>" + K3_CSS + "</style><script>" + js + "</script></head>", 1))


# ---- the manual: one point after the offline map (5 languages) ---------------------------------------------------------------------
_HELP_K3 = {
    "de": ("🏔 Schweizer Karte in 3D", "(Mehr → 🗺 Karte, Schalter «2D | 3D» oben links): das Gelände in 3D – mit zwei Fingern (am PC rechte Maustaste) drehen und neigen, der Kompass stellt zurück; geht auch im Vollbild «⛶». Die Höhen kommen aus dem Relief der Topo-Karte (swissALTI3D, © swisstopo) oder, ohne Topo-Karte, aus den «⛰ Höhendaten Schweiz» (DHM25, © swisstopo): MoveEye rechnet die Höhen-Kacheln selbst und merkt sie sich (höchstens 256 MB). Ohne beides zeigt «3D» den Weg zum Laden der Höhendaten. Die Wahl merkt sich der Browser."),
    "en": ("🏔 Map of Switzerland in 3D", "(More → 🗺 Map, switch “2D | 3D” top left): the terrain in 3D – turn and tilt with two fingers (on a PC the right mouse button), the compass turns it back; also in full screen “⛶”. The heights come from the relief of the topo map (swissALTI3D, © swisstopo) or, without the topo map, from the “⛰ Height data of Switzerland” (DHM25, © swisstopo): MoveEye computes the height tiles itself and keeps them (at most 256 MB). Without either, “3D” shows how to load the height data. The browser remembers the choice."),
    "fr": ("🏔 Carte de la Suisse en 3D", "(Plus → 🗺 Carte, bouton « 2D | 3D » en haut à gauche) : le terrain en 3D – tourner et incliner avec deux doigts (sur PC le bouton droit de la souris), la boussole remet en place ; aussi en plein écran « ⛶ ». Les altitudes viennent du relief de la carte topo (swissALTI3D, © swisstopo) ou, sans carte topo, des « ⛰ Données d’altitude de la Suisse » (DHM25, © swisstopo) : MoveEye calcule lui-même les tuiles d’altitude et les garde (256 Mo au plus). Sans l’un ni l’autre, « 3D » montre comment charger les données d’altitude. Le navigateur retient le choix."),
    "it": ("🏔 Mappa della Svizzera in 3D", "(Altro → 🗺 Mappa, interruttore «2D | 3D» in alto a sinistra): il terreno in 3D – ruotare e inclinare con due dita (sul PC il tasto destro del mouse), la bussola rimette a posto; anche a schermo intero «⛶». Le quote vengono dal rilievo della mappa topo (swissALTI3D, © swisstopo) o, senza mappa topo, dai «⛰ Dati di quota della Svizzera» (DHM25, © swisstopo): MoveEye calcola da solo le tessere di quota e le conserva (al massimo 256 MB). Senza nessuno dei due, «3D» mostra come caricare i dati di quota. Il browser ricorda la scelta."),
    "rm": ("🏔 Charta da la Svizra en 3D", "(Dapli → 🗺 Charta, cumutatur «2D | 3D» sura a sanestra): il terren en 3D – volver ed inclinar cun dus dets (sin il PC il buttun dretg da la mieur), la busla metta enavos; er en il maletg entir «⛶». Las autezzas vegnan dal relief da la charta topo (swissALTI3D, © swisstopo) u, senza charta topo, da las «⛰ Datas d’autezza da la Svizra» (DHM25, © swisstopo): MoveEye quinta sez ils quadrels d’autezza e als tegna (al pli 256 MB). Senza in u l’auter mussa «3D» co chargiar las datas d’autezza. Il navigatur sa regorda da la tscherna."),
}


def _help_k3(doc, lang):
    h_, x_ = _HELP_K3[lang]
    anchor = _HELP_KQ[lang][0]
    if h_ in doc or anchor not in doc:
        return doc
    from html import escape as _e
    i = doc.find("</li>", doc.find(anchor))
    return doc if i < 0 else doc[:i + 5] + f"<li><b>{h_}</b> {_e(x_, quote=False)}</li>" + doc[i + 5:]


_hp_en_k3 = HELP_PAGE.find('<div lang="en">')
if _hp_en_k3 > 0:
    HELP_PAGE = _help_k3(HELP_PAGE[:_hp_en_k3], "de") + _help_k3(HELP_PAGE[_hp_en_k3:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_k3(HELP_X[_L], _L)


# ---- self-test (werkzeuge/karte_3d_test.py: tiles from a height file, cache, the page in the browser) ----------------------------------
def karte3d_selftest():
    h = np.array([[-430.25, 0.0, 372.1], [4478.0, 1234.5678, 8848.86], [-12000.0, 0.004, 32767.0]])
    assert np.abs(kd_decode(kd_encode(h)) - h).max() < 0.1 / 25, "terrarium there and back"
    assert kd_encode(np.zeros((1, 1)))[0, 0].tolist() == [128, 0, 0], "0 m = terrarium 128 / 0 / 0"
    png = kd_png(kd_encode(np.full((4, 4), 500.0)))
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    la, lo = kd_wgs84(*kh_lv95(46.9480, 7.4474))
    assert abs(la - 46.9480) < 2e-5 and abs(lo - 7.4474) < 2e-5, "LV95 there and back (Bern)"
    assert kd_key().endswith("v%d" % KD_VER) and re.fullmatch(r"[0-9a-f]{12}v\d+", kd_key())
    assert role_allows("view", "/karte/dem/" + kd_key() + "/12/2138/1447.png", "GET", {}, []), "every logged-in user sees the 3D map"
    assert all(len(v) == 4 and all(v) and "ß" not in v[0] for v in _HX_K3.values()) and all(k in DE for k in _HX_K3)
    assert all(k in TRX[L_] for L_ in ("fr", "it", "rm") for k in _HX_K3)
    assert "innerHTML" not in K3_JS and K3_JS.count("https://") == 1 and "https://www.swisstopo.admin.ch" in K3_JS and "confirm(" not in K3_JS
    pg = kq_page()
    assert pg.count("window.K3 = ") == 1 and "/*K3STATE*/" not in pg and "/*K3TX*/" not in pg and "kq3d(m)" in pg
    assert _HELP_K3["de"][0] in HELP_PAGE and _HELP_K3["en"][0] in HELP_PAGE
    return "3D map: terrarium, LV95, rights, texts, hook"


SELFTEST_EXTRA.append(("Map of Switzerland in 3D (639zzzzzz)", karte3d_selftest))
'''
zd_exec(K3_PY, "639zzzzzz_karte_ch_3d.py")
