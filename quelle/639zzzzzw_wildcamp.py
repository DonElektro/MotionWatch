#@ MoveEye – Teil 639zzzzzw: «🏕 Wildcamp» auf der Offline-Karte (/karte, Schweiz und Bergtal) – Schutzgebiete aus den offenen Geodaten des Bundes (Wildruhezonen mit Schutzzeit und verbindlich / empfohlen, eidg. Jagdbanngebiete, Nationalpark, Wasser- und Zugvogelreservate, Moore, Auen) als Ebene mit Schaltern je Kategorie und Legende, nach Datum blass / kräftig, Antippen = Schutzzone und Kanton, Hinweise bei «Eigene Orte» und Touren; Paket als Release-Asset (Grösse + sha256). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Auftrag des Besitzers (22.11.2026, freigegeben): ein Offline-Paket «Wildcamp» für die Schweizer Karte.
#   * Daten (werkzeuge/wildcamp/paket.py, Workflow «Wildcamp»): die Ebenen des Geoportals des Bundes über api3.geo.admin.ch –
#     Wildruhezonen (Kantone, zusammengestellt vom BAFU; mit Schutzzeit, Bestimmung, rechtsverbindlich / empfohlen, erlaubte
#     Routen), Wildtierschutzgebiete und eidgenössische Jagdbanngebiete, Schweizerischer Nationalpark, Wasser- und
#     Zugvogelreservate, Hoch- und Flachmoore, Moorlandschaften, Auengebiete, Kantonsgrenzen (swisstopo). Lizenz: Open
#     Government Data «Freie Nutzung. Quellenangabe ist Pflicht.» – die Quellenangabe steht unter der Karte und in
#     LIZENZEN.txt. Kantonale Naturschutzgebiete: kein Datensatz des Bundes – fehlen (so gesagt in der Legende).
#   * Paket wildcamp-ch-N.zip am Release WC_TAG (vereinfachtes GeoJSON, ~2.5 MB, entpackt ~11 MB – passt auch auf den Host
#     mit 1,5 GB RAM / 2 GB Platte: WC_HOST_MAX). Grösse + sha256 hier in WC_FILE (`paket.py --eintragen`), size 0 = noch nicht
#     freigegeben. Laden nur der Admin wie die Bergtal-Karte (639zzzzzt): Platz, Fortsetzen, Prüfsumme vor dem Auspacken, ein
#     neuer Ordner erst am Schluss umbenannt. Auf dem Host darf der Faden «wildcamp-dl» zu GitHub (639zzzzw).
#   * Karte (/karte): Feld «🏕 Wildcamp» unter der Karte – Ebene ein / aus, Schalter je Kategorie, Datum (Vorgabe heute),
#     Legende. Farben Okabe-Ito (farbenblind sicher) und je Kategorie eine eigene Linie. Ausserhalb der Schutzzeit blass und
#     gestrichelt, in der Schutzzeit kräftig. Antippen: Karte mit «Wildruhezone «X» – Betreten 20.12.–30.4. verboten
#     (verbindlich)» bzw. «keine Schutzzone bekannt», dazu der Kanton (kurze Notiz zum Wildcampen mit Quelle) und «Information,
#     keine Rechtsberatung». Im Bergtal dieselbe Ebene mit den ERFUNDENEN Wildruhezonen aus dem Bergtal-Paket (bergtal.gd
#     WILDRUHEZONEN -> export.gd -> werkzeuge/bergkarte/paket.py, vektor.json t = «wrz»).
#   * Hinweise: (a) beim Antippen; (b) «Eigene Orte» (639zzzzo): auf der Karte eines Orts und beim Setzen / Verschieben, beim
#     Zelt als «Nachtlager»; (c) Touren (639zzx): beim Zeichnen und in der Tour die Abschnitte, die eine Zone queren (km von –
#     bis, «Auf der Karte zeigen»). KEIN Push, kein GPS-Verfolgen.
#   * Ohne Schweizer Karte (Host): die Ebene Schweiz gibt es nicht – klarer Hinweis; das Bergtal geht wie bisher.
#   * Texte in 5 Sprachen; das Fenster (Tk) hat keine Offline-Karte – dort nichts. Der Live-Reiter bleibt unverändert.
# Selbsttest wildcamp_selftest; Test werkzeuge/wildcamp_test.py (Paket bauen / prüfen, Laden, Datum, Antippen, Hinweise Orte und
# Touren, Bergtal, Seite im Browser 390 px + PC).
# ----------------------------------------------------------------------------
# Die Pins bleiben in der (signierten) Hauptdatei; der Programmtext steht in EINEM Literal (Hauptdatei klein, wie 639zzzzzt):
# werkzeuge/bauen.py legt es in die Zusatz-ZIP (über ZD_SHA256 mit signiert). Ohne ZIP gibt es «Wildcamp» nicht - es gehört
# nicht zu Start, Schutz, Alarm, Update oder Reparatur.
WC_TAG = "wildcamp-1"
WC_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/"}   # + <tag>/<name>; Tests: lokaler Server
# Werte aus werkzeuge/wildcamp/paket.py (pins_wildcamp.txt des Workflows «Wildcamp»); size 0 = noch nicht freigegeben
WC_FILE = {"name": "wildcamp-ch-1.zip", "size": 2425742, "sha256": "3cf1b73ea72ebdefe342ff0a1b9bd54b97b555a0a084fc3bfe5522dd6f2ecd1e", "unpacked": 10886755, "datum": "2026-11-22"}
WC_PY = r'''WC_FORMAT = 1
WC_MAX = 40 * 1000 * 1000                                  # hard limit of the package (also unpacked)
WC_FREE_MIN = 200 * 1000 * 1000                            # so much stays free after the install
WC_HOST_MAX = 40 * 1000 * 1000                             # on the host (2 GB disk, 1.5 GB RAM): zip + unpacked + .gz copies
WC_KATS = ("wrz", "jb", "snp", "wzvv", "moor", "auen")
WC_FILES = tuple("zonen/%s.json" % k for k in WC_KATS) + ("kantone.json",)
WC_NEED = ("wildcamp.json", "LIZENZEN.txt") + WC_FILES
WC_STATIC = re.compile(r"zonen/(wrz|jb|snp|wzvv|moor|auen)\.json|LIZENZEN\.txt")
WC_CELL = 0.05                                             # degrees: the grid of the search index
WC_STEP = 20.0                                             # m: a route is tested every so many metres
WC_LINE_MAX = 5000                                         # points of a route that is tested
WC_SEGS = 30                                               # crossed sections reported per route
WC_DL = {"running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": False, "phase": ""}
WC_RT = {"lock": threading.Lock(), "ok_t": 0.0, "ok": False, "meta": None, "idx": {}, "kt": None, "berg": None, "berg_key": ""}


def wc_dir():
    return os.path.join(DATA_DIR, "wildcamp")


def wc_dl_dir():
    return os.path.join(DATA_DIR, "wildcamp_dl")


def wc_pinned():
    f = WC_FILE
    return bool(isinstance(f.get("size"), int) and 0 < f["size"] <= WC_MAX and re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or ""))
                and isinstance(f.get("unpacked"), int) and 0 < f["unpacked"] <= WC_MAX and re.fullmatch(r"wildcamp-ch-\d{1,3}\.zip", f.get("name") or "")
                and re.fullmatch(r"wildcamp-\d{1,3}", WC_TAG) and f["name"].split("-")[-1].split(".")[0] == WC_TAG.split("-")[1])


def wc_key():
    return (WC_FILE.get("sha256") or "0" * 12)[:12]


def wc_on_host():
    H = globals().get("HOST")
    return bool(isinstance(H, dict) and H.get("on"))


def wc_host_fit():
    """the package fits the host (or this is no host): zip + unpacked + the .gz copies (about a quarter)"""
    if not wc_on_host():
        return True
    return WC_FILE["size"] + WC_FILE["unpacked"] * 1.3 <= WC_HOST_MAX


def wc_reset():
    with WC_RT["lock"]:
        WC_RT.update(ok_t=0.0, ok=False, meta=None, idx={}, kt=None)


def wc_installed():
    """the package of WC_FILE is unpacked (marker wildcamp.ok with tag + sha256, every needed file there) - every 2 s"""
    now = time.time()
    if now - WC_RT["ok_t"] < 2.0:
        return WC_RT["ok"]
    ok = False
    if wc_pinned():
        try:
            with open(os.path.join(wc_dir(), "wildcamp.ok"), encoding="utf-8") as fh:
                m = json.load(fh)
            ok = (isinstance(m, dict) and m.get("tag") == WC_TAG and m.get("sha256") == WC_FILE["sha256"]
                  and all(os.path.isfile(os.path.join(wc_dir(), *p.split("/"))) for p in WC_NEED))
        except (OSError, ValueError):
            ok = False
    if ok != WC_RT["ok"]:
        with WC_RT["lock"]:
            WC_RT.update(meta=None, idx={}, kt=None)
    WC_RT["ok"], WC_RT["ok_t"] = ok, now
    return ok


def wc_meta():
    if not wc_installed():
        return None
    if WC_RT["meta"] is None:
        try:
            with open(os.path.join(wc_dir(), "wildcamp.json"), encoding="utf-8") as fh:
                m = json.load(fh)
            WC_RT["meta"] = {"tag": m["tag"], "datum": str(m.get("datum") or ""), "counts": m.get("counts", {}),
                             "quellen": [{k: q.get(k) for k in ("titel", "layer", "quelle", "objekte")} for q in m.get("quellen", [])][:20]}
        except (OSError, ValueError, KeyError, TypeError):
            return None
    return WC_RT["meta"]


# ---- the package: load, check, unpack, remove (only the administrator) ------------------------------------------------------------
def wc_space_ok():
    part = os.path.join(wc_dl_dir(), WC_FILE["name"] + ".part")
    have = os.path.getsize(part) if os.path.isfile(part) else 0
    return kq_free() - (WC_FILE["size"] - have + WC_FILE["unpacked"] * 1.3) >= WC_FREE_MIN


def wc_download(wait=False):
    if not wc_pinned():
        return False, "comes with an update"
    if not wc_host_fit():
        return False, "too large for the host"
    if WC_DL["running"] or wc_installed():
        return True, ""
    if not wc_space_ok():
        return False, "not enough free space on the memory card"
    WC_DL.update(running=True, got=0, total=WC_FILE["size"], msg="", stop=False, done=False, phase="load")

    def work():
        import gzip as _gz
        dd, d_ = wc_dl_dir(), wc_dir()
        zp = os.path.join(dd, WC_FILE["name"])
        new = d_ + ".neu"
        try:
            os.makedirs(dd, exist_ok=True)
            bio_fetch(WC_BASE["url"] + WC_TAG + "/" + WC_FILE["name"], zp, WC_FILE, WC_DL)   # 639zzd: resume, exact size + sha256
            WC_DL["phase"] = "unpack"
            shutil.rmtree(new, ignore_errors=True)
            os.makedirs(new)
            if _kq_unzip(zp, new, WC_FILE["unpacked"]) != WC_FILE["unpacked"]:
                raise ValueError("package has the wrong size")
            with open(os.path.join(new, "wildcamp.json"), encoding="utf-8") as fh:
                m = json.load(fh)
            if m.get("tag") != WC_TAG or int(m.get("format") or 0) != WC_FORMAT:
                raise ValueError("package does not fit this MoveEye")
            for p in WC_NEED:
                if not os.path.isfile(os.path.join(new, *p.split("/"))):
                    raise ValueError("package incomplete")
            for p in WC_FILES:                              # the browser gets the zones packed (moor.json is ~7 MB)
                src = os.path.join(new, *p.split("/"))
                with open(src, "rb") as fi, _gz.GzipFile(src + ".gz", "wb", 6, None, 0) as fo:
                    shutil.copyfileobj(fi, fo, 1 << 20)
            with open(os.path.join(new, "wildcamp.ok"), "w", encoding="utf-8") as fh:
                json.dump({"tag": WC_TAG, "sha256": WC_FILE["sha256"]}, fh)
            shutil.rmtree(d_, ignore_errors=True)
            os.replace(new, d_)
            os.remove(zp)
            WC_DL["done"] = True
            wc_reset()
            log_event("sys", f"Wildcamp package installed ({WC_TAG}, {round(WC_FILE['size'] / 1e6, 1)} MB)")
        except InterruptedError:
            WC_DL["msg"] = "cancelled"
        except Exception as e:
            WC_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Wildcamp package not installed: {WC_DL['msg']}")
            shutil.rmtree(new, ignore_errors=True)
            if "checksum" in WC_DL["msg"] or "large" in WC_DL["msg"]:
                for p in (zp, zp + ".part"):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        finally:
            WC_DL.update(running=False, phase="")
    if wait:
        work()
        return (not WC_DL["msg"]), WC_DL["msg"]
    threading.Thread(target=work, daemon=True, name="wildcamp-dl").start()
    return True, ""


def wc_delete():
    if WC_DL["running"]:
        return False, "busy right now - try again in a moment"
    shutil.rmtree(wc_dir(), ignore_errors=True)
    shutil.rmtree(wc_dl_dir(), ignore_errors=True)
    wc_reset()
    log_event("sys", "Wildcamp package deleted")
    return True, ""


if "HOST_DL_THREADS" in globals():                        # 639zzzzw: on the host this thread may reach GitHub (fixed checksum)
    HOST_DL_THREADS = tuple(HOST_DL_THREADS) + ("wildcamp-dl",)


# ---- protection periods -----------------------------------------------------------------------------------------------------------
def wc_mmdd(datum=None):
    """«YYYY-MM-DD» (or today) -> «MMDD»"""
    s = str(datum or "")
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m and 1 <= int(m.group(2)) <= 12 and 1 <= int(m.group(3)) <= 31:
        return m.group(2) + m.group(3)
    return time.strftime("%m%d", time.localtime())


def wc_aktiv(p, mmdd):
    """inside one of the periods [[MMDD, MMDD] …] (also over the new year)? [] = all year; None = unknown (cautious: yes)"""
    if not isinstance(p, list) or not p:
        return True
    for q in p:
        try:
            a, b = str(q[0]), str(q[1])
        except (TypeError, IndexError):
            return True
        if (a <= b and a <= mmdd <= b) or (a > b and (mmdd >= a or mmdd <= b)):
            return True
    return False


def _wc_dm(s):
    return "%d.%d." % (int(s[2:]), int(s[:2]))


def wc_zeit(pr, L):
    """the protection period as text: «20.12.–30.4.», «ganzjährig» or the words of the data"""
    p = pr.get("p")
    if isinstance(p, list) and p:
        return ", ".join(_wc_dm(a) + "–" + _wc_dm(b) for a, b in p[:4])
    if isinstance(p, list):
        return tr("all year", L)
    z = str(pr.get("z") or "").strip()
    return tr("at certain times", L) + (" (" + z[:80] + ")" if z else "")


# ---- the search index (float arrays per ring, a grid of 0.05°) ----------------------------------------------------------------------
def _wc_polys(g):
    t, c = (g or {}).get("type"), (g or {}).get("coordinates")
    P = [c] if t == "Polygon" else list(c or []) if t == "MultiPolygon" else []
    import array as _ar
    out = []
    for poly in P:
        rings = []
        for r in poly:
            a = _ar.array("d")
            for q in r:
                a.append(float(q[0])); a.append(float(q[1]))
            if len(a) >= 8:
                rings.append(a)
        if rings:
            out.append(rings)
    return out


def _wc_ring_in(x, y, a):
    c = False
    n = len(a) // 2
    j = n - 1
    for i in range(n):
        xi, yi, xj, yj = a[2 * i], a[2 * i + 1], a[2 * j], a[2 * j + 1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def wc_in_polys(x, y, polys):
    for rings in polys:
        if _wc_ring_in(x, y, rings[0]) and not any(_wc_ring_in(x, y, h) for h in rings[1:]):
            return True
    return False


def _wc_index(features):
    """[(bbox, props, polys)] + grid {(i, j): [n …]}"""
    items, grid = [], {}
    for f in features:
        pr = dict(f.get("properties") or {})
        bb = pr.pop("x", None)
        polys = _wc_polys(f.get("geometry"))
        if not polys:
            continue
        if not (isinstance(bb, list) and len(bb) == 4):
            xs = [r[0][k] for r in polys for k in range(0, len(r[0]), 2)]
            ys = [r[0][k] for r in polys for k in range(1, len(r[0]), 2)]
            bb = [min(xs), min(ys), max(xs), max(ys)]
        n = len(items)
        items.append((tuple(float(v) for v in bb), pr, polys))
        for i in range(int(math.floor(bb[0] / WC_CELL)), int(math.floor(bb[2] / WC_CELL)) + 1):
            for j in range(int(math.floor(bb[1] / WC_CELL)), int(math.floor(bb[3] / WC_CELL)) + 1):
                grid.setdefault((i, j), []).append(n)
    return {"items": items, "grid": grid}


def wc_idx(k):
    """the index of one category of the Swiss package (read once, kept; None without package)"""
    if not wc_installed():
        return None
    ix = WC_RT["idx"].get(k)
    if ix is None:
        with WC_RT["lock"]:
            ix = WC_RT["idx"].get(k)
            if ix is None:
                name = "kantone.json" if k == "kantone" else "zonen/%s.json" % k
                with open(os.path.join(wc_dir(), *name.split("/")), encoding="utf-8") as fh:
                    ix = _wc_index(json.load(fh).get("features", []))
                WC_RT["idx"][k] = ix
    return ix


def wc_berg():
    """the invented Wildruhezonen of the Bergtal package (vektor.json t = «wrz», 639zzzzzt) - None without that package"""
    try:
        if not bk_installed():
            return None
        key = bk_key()
    except NameError:
        return None
    if WC_RT["berg"] is None or WC_RT["berg_key"] != key:
        F = []
        try:
            for f in _bk_json("vektor.json").get("features", []):
                p = f.get("properties") or {}
                if p.get("t") == "wrz" and (f.get("geometry") or {}).get("type") in ("Polygon", "MultiPolygon"):
                    pr = {"c": "wrz", "n": str(p.get("name") or "")[:80], "z": str(p.get("z") or "")[:80], "s": p.get("s") if p.get("s") in ("v", "e") else "",
                          "b": str(p.get("b") or "")[:12], "i": "berg." + str(p.get("id") or len(F))[:40], "erf": 1}
                    if isinstance(p.get("p"), list):
                        pr["p"] = [[str(a)[:4], str(b)[:4]] for a, b in p["p"][:4]]
                    F.append({"type": "Feature", "properties": pr, "geometry": f["geometry"]})
        except (OSError, ValueError, KeyError, TypeError):
            F = []
        WC_RT["berg"] = {"fc": {"type": "FeatureCollection", "features": F}, "idx": _wc_index(F)}
        WC_RT["berg_key"] = key
    return WC_RT["berg"]


def _wc_find(ix, x, y):
    if not ix:
        return []
    out = []
    for n in ix["grid"].get((int(math.floor(x / WC_CELL)), int(math.floor(y / WC_CELL))), ()):
        bb, pr, polys = ix["items"][n]
        if bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3] and wc_in_polys(x, y, polys):
            out.append(pr)
    return out


def wc_hits(lat, lon, cats=None):
    """every protected area at this point: [(category, properties)] - the Bergtal frame: the invented zones of the valley"""
    try:
        if bk_in(lat, lon):
            b = wc_berg()
            return [("wrz", pr) for pr in _wc_find(b["idx"] if b else None, lon, lat)]
    except NameError:
        pass
    out = []
    for k in WC_KATS:
        if cats and k not in cats:
            continue
        try:
            for pr in _wc_find(wc_idx(k), lon, lat):
                out.append((k, pr))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return out


def wc_kanton(lat, lon):
    try:
        for pr in _wc_find(wc_idx("kantone"), lon, lat):
            return str(pr.get("k") or ""), str(pr.get("n") or "")
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return "", ""


# ---- texts of a zone ---------------------------------------------------------------------------------------------------------------
WC_REGEL = {"R10": "a", "R20": "a", "R30": "b", "R40": "b", "R130": "b", "R70": "c", "R80": "c", "R90": "c", "R100": "c", "R110": "c",
            "R120": "c", "R140": "d", "R150": "d", "R160": "d", "R170": "d", "E10": "e", "E20": "f", "E30": "f", "E40": "f", "E50": "f"}
WC_REGEL_EN = {"a": "Entering prohibited {zeit}", "b": "Entering prohibited {zeit} – crossing only on the marked path or route",
               "c": "{zeit} only on the marked paths and routes", "d": "Winter sports prohibited {zeit} off the marked pistes and routes",
               "e": "Please do not enter {zeit}", "f": "Please do not enter {zeit} – stay on the marked routes"}
WC_ART = {"wrz": "Wildlife rest area", "wsg": "Wildlife protection area", "jb": "Federal game reserve", "snp": "Swiss National Park",
          "wzvv": "Reserve for water and migratory birds", "hm": "Raised bog of national importance", "fm": "Fen of national importance",
          "ml": "Mire landscape of national importance", "au": "Floodplain of national importance"}
WC_SAGT = {"jb": "all year: hunting prohibited, do not disturb wild animals", "snp": "stay on the marked paths, visits by day only (no overnight stay outdoors)",
           "wzvv": "all year: do not disturb the birds, observe the rules on site", "hm": "protected habitat – observe the rules on site",
           "fm": "protected habitat – observe the rules on site", "ml": "protected landscape – observe the rules on site",
           "au": "protected habitat – observe the rules on site"}


def wc_text(k, pr, lang, mmdd):
    """one zone -> {kat, c, text, amtlich, aktiv, u, erf} (the line of the tap card, in the language of the page)"""
    L = norm_lang(lang)
    c = str(pr.get("c") or k)
    name = str(pr.get("n") or "")
    art = tr(WC_ART.get(c, "Protected area"), L)
    head = art + (" «" + name + "»" if name and c != "snp" else "")
    akt = wc_aktiv(pr.get("p"), mmdd)
    if c in ("wrz", "wsg"):
        g = WC_REGEL.get(str(pr.get("b") or ""))
        z = wc_zeit(pr, L)
        if g:
            rule = tr(WC_REGEL_EN[g], L).replace("{zeit}", z)
        else:
            r = pr.get("r") if isinstance(pr.get("r"), dict) else {}
            rule = (r.get(L) or r.get("de") or tr("special rules", L)) + " (" + z + ")"
        st = {"v": "binding", "e": "recommended"}.get(pr.get("s"), "")
        txt = head + " – " + rule + (" (" + tr(st, L) + ")" if st else "")
    else:
        txt = head + " – " + tr(WC_SAGT.get(c, "observe the rules on site"), L)
    if pr.get("erf"):
        txt += " · " + tr("invented (Bergtal)", L)
    r = pr.get("r") if isinstance(pr.get("r"), dict) else {}
    am = r.get(L) or r.get("de") or str(pr.get("t") or "")
    u = str(pr.get("u") or "")
    return {"kat": k, "c": c, "text": txt, "amtlich": am[:200], "aktiv": akt, "u": u if u.startswith("https://") else "", "erf": bool(pr.get("erf"))}


# ---- cantons: a short, cautious note about wild camping (source: TCS, revised 01.07.2026) -------------------------------------------
WC_TCS = "https://www.tcs.ch/de/camping-reisen/camping-insider/ratgeber/reisevorbereitung/wild-campen-in-der-schweiz.php"
WC_KT_WEB = {"ZH": "zh.ch", "BE": "be.ch", "LU": "lu.ch", "UR": "ur.ch", "SZ": "sz.ch", "OW": "ow.ch", "NW": "nw.ch", "GL": "gl.ch", "ZG": "zg.ch",
             "FR": "fr.ch", "SO": "so.ch", "BS": "bs.ch", "BL": "baselland.ch", "SH": "sh.ch", "AR": "ar.ch", "AI": "ai.ch", "SG": "sg.ch",
             "GR": "gr.ch", "AG": "ag.ch", "TG": "tg.ch", "TI": "ti.ch", "VD": "vd.ch", "VS": "vs.ch", "NE": "ne.ch", "GE": "ge.ch", "JU": "jura.ch"}
# status: n = generally not allowed · e = not banned in general, but restricted · u = unclear; extras: short phrases (below)
WC_KT = {"AG": ("u", ("park",)), "AR": ("n", ("schutz",)), "AI": ("n", ("biwak_eig",)), "BL": ("n", ()), "BS": ("n", ("eig",)),
         "BE": ("n", ()), "FR": ("n", ()), "GE": ("n", ("wald",)), "GL": ("n", ()), "GR": ("n", ("schutz",)), "JU": ("n", ("schutz",)),
         "LU": ("e", ("gemeinde", "eig")), "NE": ("n", ()), "NW": ("u", ()), "OW": ("e", ("nacht", "schutz")), "SH": ("n", ()),
         "SZ": ("n", ("eig",)), "SO": ("n", ("eig",)), "SG": ("n", ("schutz",)), "TI": ("n", ("baum",)), "TG": ("n", ("eig",)),
         "UR": ("e", ("schutz",)), "VD": ("n", ()), "VS": ("n", ("bew",)), "ZH": ("n", ("eig",)), "ZG": ("n", ("eig",))}
WC_KT_ST = {"n": "Wild camping generally not allowed.", "e": "Wild camping not banned in general, but restricted.",
            "u": "unclear – ask the canton"}
WC_KT_EX = {"park": "One night on a public car park is allowed (vehicles).", "schutz": "Banned in protected areas, mires and biotopes.",
            "biwak_eig": "A simple bivouac only with the consent of the landowner.", "eig": "Possible with the permission of the landowner.",
            "wald": "Camping in the forest is prohibited (except on approved sites).", "gemeinde": "On municipal land allowed unless the municipality forbids it.",
            "nacht": "One night outside campsites tolerated if no interests are harmed.", "baum": "A single bivouac above the tree line is tolerated.",
            "bew": "Camping outside a campsite needs a permit."}


def wc_kanton_info(lat, lon, lang):
    L = norm_lang(lang)
    k, name = wc_kanton(lat, lon)
    if k not in WC_KT:
        return None
    st, ex = WC_KT[k]
    parts = [tr(WC_KT_ST[st], L)] + [tr(WC_KT_EX[e], L) for e in ex] + [tr("Observe the rules of the municipality.", L)]
    return {"k": k, "name": name, "text": " ".join(parts), "st": st, "src": WC_TCS, "src_t": tr("TCS, as of 1.7.2026", L),
            "web": "https://www." + WC_KT_WEB[k] + "/"}


def wc_punkt(lat, lon, lang=None, datum=None):
    L = norm_lang(lang)
    md = wc_mmdd(datum)
    zs = [wc_text(k, pr, L, md) for k, pr in wc_hits(lat, lon)]
    zs.sort(key=lambda z: (not z["aktiv"], WC_KATS.index(z["kat"]) if z["kat"] in WC_KATS else 9))
    try:
        berg = bk_in(lat, lon)
    except NameError:
        berg = False
    out = {"ok": True, "zones": zs[:12], "berg": berg, "on": wc_installed(), "mmdd": md,
           "none": "" if zs else tr("no protected area known", L), "legal": tr("Information, not legal advice.", L)}
    if not berg:
        out["kanton"] = wc_kanton_info(lat, lon, L) if wc_installed() else None
        out["nur_bund"] = tr("Only federal data: cantonal and municipal nature reserves are missing.", L)
    return out


def wc_linie(pts, lang=None, datum=None):
    """a route [(lat, lon) …] -> the sections that cross a protected area: [{text, aktiv, km0, km1, line}]"""
    L = norm_lang(lang)
    md = wc_mmdd(datum)
    pts = [(float(p[0]), float(p[1])) for p in pts[:WC_LINE_MAX]]
    if len(pts) < 2:
        return []
    S, d = [], 0.0                                          # samples: (lat, lon, metres from the start)
    for i in range(len(pts)):
        if i:
            a, b = pts[i - 1], pts[i]
            m = kt_dist(a, b)
            k = int(m // WC_STEP)
            for j in range(1, k + 1):
                r = j / (k + 1.0)
                S.append((a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r, d + m * r))
            d += m
        S.append((pts[i][0], pts[i][1], d))
    if len(S) > 40000:                                      # very long route: every n-th sample
        S = S[::int(math.ceil(len(S) / 40000.0))]
    runs, cur = [], {}                                      # zone id -> open run
    for n, (la, lo, dm) in enumerate(S):
        here = {}
        for k, pr in wc_hits(la, lo):
            here[str(pr.get("i") or id(pr))] = (k, pr)
        for zid in list(cur):
            if zid not in here:
                runs.append(cur.pop(zid))
        for zid, (k, pr) in here.items():
            if zid in cur:
                cur[zid]["j"] = n
            else:
                cur[zid] = {"k": k, "pr": pr, "i": n, "j": n}
    runs += list(cur.values())
    runs.sort(key=lambda r: r["i"])
    out = []
    for r in runs[:WC_SEGS]:
        z = wc_text(r["k"], r["pr"], L, md)
        seg = S[max(0, r["i"] - 1):r["j"] + 2]
        step = max(1, len(seg) // 200)
        z.update(km0=round(S[r["i"]][2] / 1000.0, 2), km1=round(S[r["j"]][2] / 1000.0, 2),
                 line=[[round(q[1], 6), round(q[0], 6)] for q in seg[::step]] + [[round(seg[-1][1], 6), round(seg[-1][0], 6)]])
        out.append(z)
    return out


def wc_state():
    on = wc_installed()
    return {"on": on, "pinned": wc_pinned(), "tag": WC_TAG, "size": WC_FILE["size"], "unpacked": WC_FILE["unpacked"], "datum": WC_FILE.get("datum", ""),
            "space_ok": True if on else wc_space_ok(), "host": wc_on_host(), "fit": wc_host_fit(), "admin": kq_role() == "admin", "key": wc_key(),
            "meta": wc_meta() if on else None, "dl": {k: WC_DL[k] for k in ("running", "got", "total", "msg", "done", "phase")}}


# ---- web ------------------------------------------------------------------------------------------------------------------------------
VIEW_POST.add("/api/karte/wildcamp/linie")                 # every signed-in user: the check of a route (nothing is stored)
_smalltv_routes_639zzzzzw = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzzzzw: /karte/wildcamp/<key>/…, /api/karte/wildcamp…
    _smalltv_routes_639zzzzzw(app, reply, body)
    from flask import Response, request

    def nope(code=404):
        return Response(b"", status=code, mimetype="text/plain")

    def lang_():
        return norm_lang(request.args.get("lang") or CFG.get("lang"))

    @app.route("/karte/wildcamp/<key>/<path:fp>")
    def wc_file_(key, fp):
        if key != wc_key() or not wc_installed() or not WC_STATIC.fullmatch(fp):
            return nope()
        p_ = os.path.join(wc_dir(), *fp.split("/"))
        mt = "text/plain; charset=utf-8" if fp.endswith(".txt") else "application/json"
        h_ = {"Cache-Control": "public, max-age=2592000, immutable"}
        src = p_
        if os.path.isfile(p_ + ".gz") and "gzip" in (request.headers.get("Accept-Encoding") or "").lower():
            src = p_ + ".gz"; h_["Content-Encoding"] = "gzip"; h_["Vary"] = "Accept-Encoding"
        if not os.path.isfile(src):
            return nope()
        with open(src, "rb") as fh:
            return Response(fh.read(), mimetype=mt, headers=h_)

    @app.route("/api/karte/wildcamp", methods=["GET", "POST"])
    def wc_api_():
        if request.method == "GET":
            return reply(dict(wc_state(), ok=True))
        d = body()
        lang = norm_lang(d.get("lang") or request.args.get("lang") or CFG.get("lang"))
        if kq_role() != "admin":
            return reply({"ok": False, "error": tr("not allowed for your user", lang)}, 403)
        a = str(d.get("action") or "")
        if a == "install":
            ok, err = wc_download()
        elif a == "cancel":
            WC_DL["stop"] = bool(WC_DL["running"]); ok, err = True, ""
        elif a == "delete":
            ok, err = wc_delete()
        else:
            ok, err = False, "unknown action"
        return reply(dict(wc_state(), ok=ok, error=tr(err, lang) if err else ""), 200 if ok else 400)

    @app.route("/api/karte/wildcamp/punkt")
    def wc_punkt_():
        try:
            la, lo = float(str(request.args.get("lat"))[:30]), float(str(request.args.get("lon"))[:30])
            if not (math.isfinite(la) and math.isfinite(lo) and -90 <= la <= 90 and -180 <= lo <= 180):
                raise ValueError
        except (TypeError, ValueError):
            return reply({"ok": False, "error": "lat / lon"}, 400)
        return reply(wc_punkt(la, lo, lang_(), str(request.args.get("datum") or "")[:10]))

    @app.route("/api/karte/wildcamp/linie", methods=["POST"])
    def wc_linie_():
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        P = d.get("pts") if isinstance(d.get("pts"), list) else []
        pts = []
        for p in P[:WC_LINE_MAX]:
            try:
                la, lo = float(p[0]), float(p[1])
                if math.isfinite(la) and math.isfinite(lo) and -90 <= la <= 90 and -180 <= lo <= 180:
                    pts.append((la, lo))
            except (TypeError, ValueError, IndexError):
                continue
        try:
            segs = wc_linie(pts, L, str(d.get("datum") or "")[:10])
        except (OSError, ValueError, KeyError, TypeError) as e:
            return reply({"ok": False, "error": str(e)[:80], "segs": []}, 500)
        return reply({"ok": True, "segs": segs, "on": wc_installed(), "legal": tr("Information, not legal advice.", L)})

    @app.route("/api/karte/wildcamp/berg")
    def wc_berg_():
        b = wc_berg()
        return reply({"ok": True, "fc": b["fc"] if b else {"type": "FeatureCollection", "features": []}})


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_WC = {
    "Wildcamp": ("Wildcamp", "Camping sauvage", "Campeggio libero", "Campadi liber"),
    "Protected areas for wild camping": ("Schutzgebiete fürs Wildcampen", "Zones protégées pour le camping sauvage", "Zone protette per il campeggio libero",
                                         "Zonas protegidas per il campadi liber"),
    "Show": ("Zeigen", "Afficher", "Mostra", "Mussar"),
    "Date": ("Datum", "Date", "Data", "Data"),
    "today": ("heute", "aujourd’hui", "oggi", "oz"),
    "Wildlife rest areas": ("Wildruhezonen", "Zones de tranquillité", "Zone di tranquillità", "Zonas da ruaus per la selvaschina"),
    "Game reserves": ("Jagdbanngebiete", "Districts francs", "Bandite di caccia", "Districts da protecziun da la chatscha"),
    "National park": ("Nationalpark", "Parc national", "Parco nazionale", "Parc naziunal"),
    "Bird reserves": ("Vogelreservate", "Réserves d’oiseaux", "Riserve per uccelli", "Reservats d’utschels"),
    "Mires": ("Moore", "Marais", "Paludi", "Palids"),
    "Floodplains": ("Auen", "Zones alluviales", "Zone golenali", "Auas"),
    "strong = protection period now · pale and dashed = outside the period": (
        "kräftig = jetzt Schutzzeit · blass und gestrichelt = ausserhalb der Schutzzeit",
        "intense = période de protection en cours · pâle et en tirets = hors période",
        "intenso = periodo di protezione in corso · chiaro e tratteggiato = fuori periodo",
        "ferm = ussa temp da protecziun · pallid e cun strichs = ordaifer il temp"),
    "Dashed green: allowed routes in wildlife rest areas.": ("Grün gestrichelt: erlaubte Routen in Wildruhezonen.",
                                                             "Vert en tirets : itinéraires autorisés dans les zones de tranquillité.",
                                                             "Verde tratteggiato: itinerari autorizzati nelle zone di tranquillità.",
                                                             "Verd cun strichs: rutas permessas en zonas da ruaus."),
    "Only federal data: cantonal and municipal nature reserves are missing.": (
        "Nur Daten des Bundes: kantonale und kommunale Naturschutzgebiete fehlen.",
        "Seulement les données de la Confédération : les réserves naturelles cantonales et communales manquent.",
        "Solo dati della Confederazione: mancano le riserve naturali cantonali e comunali.",
        "Mo datas da la Confederaziun: las reservas da la natira chantunalas e communalas mancan."),   # rm: unsicher
    "Information, not legal advice.": ("Information, keine Rechtsberatung.", "Information, pas un conseil juridique.", "Informazione, non consulenza legale.",
                                       "Infurmaziun, betg cussegliaziun giuridica."),
    "Signs on site and the official data apply.": ("Massgebend sind die Signalisation vor Ort und die amtlichen Daten.",
                                                   "Font foi la signalisation sur place et les données officielles.",
                                                   "Fanno fede la segnaletica sul posto e i dati ufficiali.",
                                                   "Decisivs èn la signalisaziun al lieu e las datas uffizialas."),
    "© Data: BAFU, cantons, swisstopo (geo.admin.ch)": ("© Daten: BAFU, Kantone, swisstopo (geo.admin.ch)", "© Données : OFEV, cantons, swisstopo (geo.admin.ch)",
                                                        "© Dati: UFAM, Cantoni, swisstopo (geo.admin.ch)", "© Datas: UFAM, chantuns, swisstopo (geo.admin.ch)"),
    "Sources and licences": ("Quellen und Lizenzen", "Sources et licences", "Fonti e licenze", "Funtaunas e licenzas"),
    "The Wildcamp package is not installed.": ("Das Paket «Wildcamp» ist nicht installiert.", "Le paquet « Camping sauvage » n’est pas installé.",
                                               "Il pacchetto «Campeggio libero» non è installato.", "Il pachet «Campadi liber» n’è betg installà."),
    "Protected areas of Switzerland (federal open data), about %s MB, afterwards without internet.": (
        "Schutzgebiete der Schweiz (offene Daten des Bundes), etwa %s MB, danach ohne Internet.",
        "Zones protégées de Suisse (données ouvertes de la Confédération), environ %s Mo, ensuite sans Internet.",
        "Zone protette della Svizzera (dati aperti della Confederazione), circa %s MB, poi senza Internet.",
        "Zonas protegidas da la Svizra (datas avertas da la Confederaziun), var %s MB, lura senza internet."),
    "Download Wildcamp": ("Wildcamp herunterladen", "Télécharger Camping sauvage", "Scarica Campeggio libero", "Telechargiar Campadi liber"),
    "Load the Wildcamp package now? %s MB from GitHub (fixed checksum).": (
        "Paket «Wildcamp» jetzt laden? %s MB von GitHub (feste Prüfsumme).",
        "Charger maintenant le paquet « Camping sauvage » ? %s Mo depuis GitHub (somme de contrôle fixe).",
        "Caricare adesso il pacchetto «Campeggio libero»? %s MB da GitHub (somma di controllo fissa).",
        "Chargiar uss il pachet «Campadi liber»? %s MB da GitHub (summa da controlla fixa)."),
    "Remove the Wildcamp package?": ("Paket «Wildcamp» entfernen?", "Supprimer le paquet « Camping sauvage » ?", "Rimuovere il pacchetto «Campeggio libero»?",
                                     "Allontanar il pachet «Campadi liber»?"),
    "too large for the host": ("zu gross für den Host", "trop grand pour l’hôte", "troppo grande per l’host", "memia grond per il host"),
    "On the host the Wildcamp layer for Switzerland is not available: the offline map of Switzerland does not fit there.": (
        "Auf dem Host gibt es die Wildcamp-Ebene der Schweiz nicht: die Offline-Karte Schweiz hat dort keinen Platz.",
        "Sur l’hôte, la couche Camping sauvage de la Suisse n’est pas disponible : la carte hors ligne de la Suisse n’y a pas de place.",
        "Sull’host il livello Campeggio libero della Svizzera non è disponibile: la mappa offline della Svizzera non ci sta.",
        "Sin il host n’è la stresa Campadi liber da la Svizra betg disponibla: la charta offline da la Svizra n’ha betg plaz là."),
    "The Wildcamp layer needs the offline map of Switzerland.": ("Die Wildcamp-Ebene braucht die Offline-Karte Schweiz.",
                                                                 "La couche Camping sauvage nécessite la carte hors ligne de la Suisse.",
                                                                 "Il livello Campeggio libero richiede la mappa offline della Svizzera.",
                                                                 "La stresa Campadi liber dovra la charta offline da la Svizra."),
    "Invented wildlife rest areas of the Bergtal (for practice).": ("Erfundene Wildruhezonen des Bergtals (zum Üben).",
                                                                     "Zones de tranquillité inventées du Bergtal (pour s’exercer).",
                                                                     "Zone di tranquillità inventate del Bergtal (per esercitarsi).",
                                                                     "Zonas da ruaus inventadas dal Bergtal (per exercitar)."),
    "The Bergtal map has no wildlife rest areas yet – it needs a newer Bergtal package.": (
        "Die Bergtal-Karte hat noch keine Wildruhezonen – es braucht ein neueres Bergtal-Paket.",
        "La carte du Bergtal n’a pas encore de zones de tranquillité – il faut un paquet Bergtal plus récent.",
        "La mappa del Bergtal non ha ancora zone di tranquillità – serve un pacchetto Bergtal più recente.",
        "La charta dal Bergtal n’ha anc naginas zonas da ruaus – i dovra in pachet dal Bergtal pli nov."),
    "no protected area known": ("keine Schutzzone bekannt", "aucune zone protégée connue", "nessuna zona protetta nota", "nagina zona protegida enconuschenta"),
    "now in the protection period": ("jetzt in der Schutzzeit", "en période de protection", "ora nel periodo di protezione", "ussa en il temp da protecziun"),
    "outside the protection period": ("ausserhalb der Schutzzeit", "hors période de protection", "fuori dal periodo di protezione", "ordaifer il temp da protecziun"),
    "Official wording:": ("Amtlicher Wortlaut:", "Texte officiel :", "Testo ufficiale:", "Text uffizial:"),
    "Details": ("Details", "Détails", "Dettagli", "Detagls"),
    "Canton": ("Kanton", "Canton", "Cantone", "Chantun"),
    "Source:": ("Quelle:", "Source :", "Fonte:", "Funtauna:"),
    "Website of the canton": ("Webseite des Kantons", "Site du canton", "Sito del Cantone", "Pagina d’internet dal chantun"),
    "TCS, as of 1.7.2026": ("TCS, Stand 1.7.2026", "TCS, état au 1.7.2026", "TCS, stato 1.7.2026", "TCS, stadi 1.7.2026"),
    "Wild camping generally not allowed.": ("Wildcampen grundsätzlich nicht erlaubt.", "Camping sauvage en principe interdit.",
                                            "Campeggio libero in linea di principio non permesso.", "Campadi liber per princip betg permess."),
    "Wild camping not banned in general, but restricted.": ("Wildcampen nicht generell verboten, aber eingeschränkt.",
                                                            "Camping sauvage pas interdit en général, mais restreint.",
                                                            "Campeggio libero non vietato in generale, ma limitato.",
                                                            "Campadi liber betg scumandà en general, ma restrenschì."),
    "unclear – ask the canton": ("unklar – beim Kanton nachfragen", "pas clair – se renseigner auprès du canton", "non chiaro – chiedere al Cantone",
                                 "betg cler – dumandar il chantun"),
    "One night on a public car park is allowed (vehicles).": ("Eine Nacht auf einem öffentlichen Parkplatz ist erlaubt (Fahrzeuge).",
                                                             "Une nuit sur un parking public est autorisée (véhicules).",
                                                             "Una notte in un parcheggio pubblico è permessa (veicoli).",
                                                             "Ina notg sin in parcadi public è permessa (vehichels)."),
    "Banned in protected areas, mires and biotopes.": ("In Schutzgebieten, Mooren und Biotopen verboten.", "Interdit dans les zones protégées, marais et biotopes.",
                                                       "Vietato nelle zone protette, paludi e biotopi.", "Scumandà en zonas protegidas, palids e biotops."),
    "A simple bivouac only with the consent of the landowner.": ("Ein einfaches Biwak nur mit Zustimmung der Grundeigentümerin oder des Grundeigentümers.",
                                                                 "Un bivouac simple seulement avec l’accord du propriétaire foncier.",
                                                                 "Un bivacco semplice solo con il consenso del proprietario del fondo.",
                                                                 "In bivac simpel mo cun il consentiment da la proprietaria u dal proprietari dal terren."),
    "Possible with the permission of the landowner.": ("Mit Erlaubnis der Grundeigentümerin oder des Grundeigentümers möglich.",
                                                       "Possible avec l’autorisation du propriétaire foncier.", "Possibile con il permesso del proprietario del fondo.",
                                                       "Pussaivel cun il permiss da la proprietaria u dal proprietari dal terren."),
    "Camping in the forest is prohibited (except on approved sites).": ("Zelten im Wald ist verboten (ausser auf bewilligten Plätzen).",
                                                                        "Camper en forêt est interdit (sauf sur des sites autorisés).",
                                                                        "Campeggiare nel bosco è vietato (salvo su siti autorizzati).",
                                                                        "Campar en il guaud è scumandà (danor sin plazzas permessas)."),
    "On municipal land allowed unless the municipality forbids it.": ("Auf Gemeindeland erlaubt, wenn die Gemeinde es nicht verbietet.",
                                                                     "Autorisé sur le terrain communal si la commune ne l’interdit pas.",
                                                                     "Permesso su terreno comunale se il Comune non lo vieta.",
                                                                     "Permess sin terren communal, sche la vischnanca na scumonda betg."),
    "One night outside campsites tolerated if no interests are harmed.": ("Eine Nacht ausserhalb von Campingplätzen geduldet, wenn keine Interessen verletzt werden.",
                                                                          "Une nuit hors des campings tolérée si aucun intérêt n’est lésé.",
                                                                          "Una notte fuori dai campeggi tollerata se non si ledono interessi.",
                                                                          "Ina notg ordaifer plazzas da campar tolerada, sche nagins interess na vegnan violads."),
    "A single bivouac above the tree line is tolerated.": ("Ein einzelnes Biwak oberhalb der Baumgrenze ist geduldet.", "Un bivouac isolé au-dessus de la limite des arbres est toléré.",
                                                           "Un singolo bivacco sopra il limite degli alberi è tollerato.", "In singul bivac sur il cunfin dals pumers è tolerà."),
    "Camping outside a campsite needs a permit.": ("Zelten ausserhalb eines Campingplatzes braucht eine Bewilligung.",
                                                   "Camper hors d’un camping nécessite une autorisation.", "Campeggiare fuori da un campeggio richiede un permesso.",
                                                   "Campar ordaifer ina plazza da campar dovra in permiss."),
    "Observe the rules of the municipality.": ("Regeln der Gemeinde beachten.", "Respecter les règles de la commune.", "Rispettare le regole del Comune.",
                                               "Resguardar las reglas da la vischnanca."),
    "The route crosses protected areas:": ("Die Route quert Schutzgebiete:", "L’itinéraire traverse des zones protégées :", "Il percorso attraversa zone protette:",
                                           "La ruta traversa zonas protegidas:"),
    "No protected area known on this route.": ("Auf dieser Route ist keine Schutzzone bekannt.", "Aucune zone protégée connue sur cet itinéraire.",
                                               "Nessuna zona protetta nota su questo percorso.", "Nagina zona protegida enconuschenta sin questa ruta."),
    "This place is in a protected area:": ("Dieser Ort liegt in einem Schutzgebiet:", "Ce lieu est dans une zone protégée :", "Questo luogo è in una zona protetta:",
                                           "Quest lieu è en ina zona protegida:"),
    "Night camp in a protected area – check the rules before you sleep here.": (
        "Nachtlager in einem Schutzgebiet – vor dem Übernachten die Regeln prüfen.",
        "Bivouac dans une zone protégée – vérifier les règles avant d’y dormir.",
        "Accampamento notturno in una zona protetta – verificare le regole prima di dormire qui.",
        "Champ da notg en ina zona protegida – controllar las reglas avant che durmir qua."),
    "Show section": ("Abschnitt zeigen", "Afficher la section", "Mostra il tratto", "Mussar il tschancun"),
    "all year": ("ganzjährig", "toute l’année", "tutto l’anno", "tut onn"),
    "at certain times": ("zu bestimmten Zeiten", "à certaines périodes", "in determinati periodi", "a tscherts temps"),
    "special rules": ("besondere Bestimmungen", "dispositions particulières", "disposizioni particolari", "disposiziuns spezialas"),
    "binding": ("verbindlich", "contraignant", "vincolante", "liant"),
    "recommended": ("empfohlen", "recommandé", "raccomandato", "recumandà"),
    "invented (Bergtal)": ("erfunden (Bergtal)", "inventée (Bergtal)", "inventata (Bergtal)", "inventada (Bergtal)"),
    "Entering prohibited {zeit}": ("Betreten {zeit} verboten", "Accès interdit {zeit}", "Accesso vietato {zeit}", "Access scumandà {zeit}"),
    "Entering prohibited {zeit} – crossing only on the marked path or route": (
        "Betreten {zeit} verboten – durchqueren nur auf dem eingezeichneten Weg oder der Route",
        "Accès interdit {zeit} – traversée uniquement sur le chemin ou l’itinéraire indiqué",
        "Accesso vietato {zeit} – attraversare solo sul sentiero o l’itinerario indicato",
        "Access scumandà {zeit} – traversar mo sin la senda u la ruta marcada"),
    "{zeit} only on the marked paths and routes": ("{zeit} nur auf den eingezeichneten Wegen und Routen", "{zeit} uniquement sur les chemins et itinéraires indiqués",
                                                   "{zeit} solo sui sentieri e itinerari indicati", "{zeit} mo sin las sendas e rutas marcadas"),
    "Winter sports prohibited {zeit} off the marked pistes and routes": (
        "Wintersport {zeit} verboten abseits der markierten Pisten und Routen", "Sports d’hiver interdits {zeit} hors des pistes et itinéraires balisés",
        "Sport invernali vietati {zeit} fuori dalle piste e dagli itinerari segnalati", "Sport d’enviern scumandà {zeit} ordaifer las pistas e rutas marcadas"),
    "Please do not enter {zeit}": ("Bitte {zeit} nicht betreten", "Merci de ne pas entrer {zeit}", "Si prega di non entrare {zeit}", "Per plaschair betg entrar {zeit}"),
    "Please do not enter {zeit} – stay on the marked routes": ("Bitte {zeit} nicht betreten – auf den eingezeichneten Routen bleiben",
                                                               "Merci de ne pas entrer {zeit} – rester sur les itinéraires indiqués",
                                                               "Si prega di non entrare {zeit} – restare sugli itinerari indicati",
                                                               "Per plaschair betg entrar {zeit} – restar sin las rutas marcadas"),
    "Wildlife rest area": ("Wildruhezone", "Zone de tranquillité", "Zona di tranquillità", "Zona da ruaus per la selvaschina"),
    "Wildlife protection area": ("Wildtierschutzgebiet", "Zone de protection de la faune", "Zona di protezione della fauna", "Zona da protecziun da la selvaschina"),
    "Federal game reserve": ("Eidg. Jagdbanngebiet", "District franc fédéral", "Bandita federale di caccia", "District federal da protecziun da la chatscha"),
    "Swiss National Park": ("Schweizerischer Nationalpark", "Parc National Suisse", "Parco Nazionale Svizzero", "Parc Naziunal Svizzer"),
    "Reserve for water and migratory birds": ("Wasser- und Zugvogelreservat", "Réserve d’oiseaux d’eau et de migrateurs", "Riserva d’uccelli acquatici e migratori",
                                              "Reservat d’utschels d’aua e migrants"),
    "Raised bog of national importance": ("Hochmoor von nationaler Bedeutung", "Haut-marais d’importance nationale", "Torbiera alta d’importanza nazionale",
                                          "Palì aut d’impurtanza naziunala"),
    "Fen of national importance": ("Flachmoor von nationaler Bedeutung", "Bas-marais d’importance nationale", "Palude d’importanza nazionale",
                                   "Palì bass d’impurtanza naziunala"),
    "Mire landscape of national importance": ("Moorlandschaft von nationaler Bedeutung", "Site marécageux d’importance nationale",
                                              "Zona palustre d’importanza nazionale", "Cuntrada da palids d’impurtanza naziunala"),
    "Floodplain of national importance": ("Auengebiet von nationaler Bedeutung", "Zone alluviale d’importance nationale", "Zona golenale d’importanza nazionale",
                                          "Territori d’auas d’impurtanza naziunala"),
    "Protected area": ("Schutzgebiet", "Zone protégée", "Zona protetta", "Zona protegida"),
    "all year: hunting prohibited, do not disturb wild animals": ("ganzjährig: Jagd verboten, Wildtiere nicht stören",
                                                                   "toute l’année : chasse interdite, ne pas déranger la faune",
                                                                   "tutto l’anno: caccia vietata, non disturbare la fauna",
                                                                   "tut onn: chatscha scumandada, betg disturbar la selvaschina"),
    "stay on the marked paths, visits by day only (no overnight stay outdoors)": (
        "markierte Wege nicht verlassen, Besuch nur tagsüber (kein Übernachten im Freien)",
        "ne pas quitter les chemins balisés, visite seulement de jour (pas de nuit en plein air)",
        "non lasciare i sentieri segnalati, visita solo di giorno (nessun pernottamento all’aperto)",
        "betg bandunar las sendas marcadas, visita mo da di (betg pernottar a l’aviert)"),
    "all year: do not disturb the birds, observe the rules on site": ("ganzjährig: Vögel nicht stören, Regeln vor Ort beachten",
                                                                       "toute l’année : ne pas déranger les oiseaux, respecter les règles sur place",
                                                                       "tutto l’anno: non disturbare gli uccelli, rispettare le regole sul posto",
                                                                       "tut onn: betg disturbar ils utschels, resguardar las reglas al lieu"),
    "protected habitat – observe the rules on site": ("geschützter Lebensraum – Regeln vor Ort beachten", "habitat protégé – respecter les règles sur place",
                                                      "habitat protetto – rispettare le regole sul posto", "spazi da viver protegì – resguardar las reglas al lieu"),
    "protected landscape – observe the rules on site": ("geschützte Landschaft – Regeln vor Ort beachten", "paysage protégé – respecter les règles sur place",
                                                        "paesaggio protetto – rispettare le regole sul posto", "cuntrada protegida – resguardar las reglas al lieu"),
    "observe the rules on site": ("Regeln vor Ort beachten", "respecter les règles sur place", "rispettare le regole sul posto", "resguardar las reglas al lieu"),
    "Wildcamp package": ("Paket «Wildcamp»", "Paquet « Camping sauvage »", "Pacchetto «Campeggio libero»", "Pachet «Campadi liber»"),
    "data of": ("Daten vom", "données du", "dati del", "datas dals"),
}
_WC_EN = {k: k for k in _HX_WC}
for _k, _v in _HX_WC.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def wc_tx():
    out = {"en": dict(_WC_EN)}
    for i_, L_ in enumerate(("de", "fr", "it", "rm")):
        out[L_] = {k: v[i_] for k, v in _HX_WC.items()}
    return out


# ---- the browser part --------------------------------------------------------------------------------------------------------------
WC_CSS = """
#wc{margin:10px 0;padding:10px 12px;border:1px solid var(--line,#334);border-radius:12px;background:var(--panel,transparent)}
#wc h2{font-size:17px;margin:0;display:flex;gap:8px;align-items:center;flex-wrap:wrap}#wc h2 .sp{flex:1}
.wc-row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0}.wc-row label{font-size:14px}
.wc-row input[type=date]{min-height:40px;padding:4px 8px;border-radius:8px;border:1px solid var(--line);background:var(--field,var(--panel));color:var(--txt)}
.wc-chip{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:0 10px;border-radius:20px;border:1px solid var(--line,#445);font-size:14px;box-sizing:border-box}
.wc-chip[aria-pressed=false]{opacity:.55}.wc-chip[aria-pressed=false] i{background:transparent!important}.wc-chip:focus-visible{outline:2px solid #2f7cf6}
.wc-chip i{display:inline-block;width:16px;height:12px;border-radius:3px;border:2px solid var(--c);background:var(--f)}
.wc-main{all:unset;cursor:pointer;min-height:40px;padding:0 14px;border-radius:20px;font-weight:600;background:var(--panel,#222);border:1px solid var(--line,#445)}
.wc-main[aria-pressed=true]{background:#2f7cf6;color:#fff;border-color:#2f7cf6}
.wc-leg{font-size:12px;color:var(--mut,#8a93a0);display:flex;flex-direction:column;gap:3px;margin-top:4px}
.wc-leg .wc-sw{display:inline-flex;gap:4px;align-items:center;margin-right:10px}.wc-leg .wc-sw i{display:inline-block;width:18px;height:11px;border:2px solid #888;border-radius:2px}
.wc-warn{color:var(--warn,#e9a23b);font-weight:600}.wc-note{font-size:12px;color:var(--mut,#8a93a0)}
.wc-pop{font:13px/1.4 system-ui,sans-serif;max-width:280px;color:#10243f}.wc-pop b{display:block;margin-bottom:2px}.wc-pop .z{margin:4px 0;padding-left:8px;border-left:4px solid var(--c)}
.wc-pop .z.off{opacity:.7}.wc-pop small{display:block;color:#555}.wc-pop a{color:#1c5fd0}.wc-pop .kt{margin-top:6px;padding-top:6px;border-top:1px solid #ddd}
.wc-tap{margin:6px 0 8px;padding:8px 10px;border:1px solid var(--line,#334);border-radius:12px;background:var(--panel,transparent)}
.wc-tap .wc-pop{color:inherit;max-width:none}.wc-tap .wc-pop small{color:var(--mut,#8a93a0)}.wc-tap .wc-pop a{color:var(--acc2,#5aa0ff)}.wc-tap .wc-pop .kt{border-color:var(--line,#334)}
.wc-mini{max-width:230px}.wc-mini .z{font-size:12px}
.wc-hint{margin:8px 0;padding:8px 10px;border-radius:10px;border:2px solid #D55E00;background:rgba(213,94,0,.08);font-size:13px}
.wc-hint b{display:block;margin-bottom:4px}.wc-hint ul{margin:4px 0;padding-left:18px}.wc-hint li{margin:3px 0}.wc-hint button{min-height:36px;margin-top:4px}
.wc-inst{margin-top:8px}.wc-inst progress{flex:1 1 120px}
"""
WC_HTML = """
    <div id="wc-tap" class="wc-tap" hidden></div>
    <section id="wc" hidden><h2>🏕 <span id="wc-h"></span><span class="sp"></span></h2><div id="wc-body"></div></section>
"""
WC_JS = r"""
// 639zzzzzw: «🏕 Wildcamp» on /karte - protected areas (package of the Swiss map, or the invented zones of the Bergtal), tap card,
// hints for own places and tours. Everything from the data is set as text only.
(function () {
  const WC = window.WC = /*WCSTATE*/{}, TX = /*WCTX*/{};
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const T = WC.T = k => (TX[L()] || {})[k] || (TX.en || {})[k] || k;
  const $ = s => document.querySelector(s);
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const btn = (txt, cls, fn) => { const b = el("button", cls || "", txt); b.type = "button"; b.onclick = fn; return b; };
  const PRE = location.pathname.replace(/\/karte\/?$/, "");
  const EMPTY = {type: "FeatureCollection", features: []};
  const MB = n => Math.max(1, Math.round((n || 0) / 1e5) / 10);
  // Okabe-Ito colours (colour-blind safe) and a line of its own per category
  const KAT = [["wrz", "Wildlife rest areas", "#D55E00", null], ["jb", "Game reserves", "#0072B2", [3, 2]], ["snp", "National park", "#CC79A7", null],
    ["wzvv", "Bird reserves", "#56B4E9", [1, 1.5]], ["moor", "Mires", "#009E73", null], ["auen", "Floodplains", "#E69F00", [4, 1.5, 1, 1.5]]];
  const COL = {}; KAT.forEach(k => { COL[k[0]] = k[2]; });
  const world = () => (window.BK && BK.mode === "berg") ? "berg" : "ch";
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  let ON = get("mw-wc-on", "1") === "1", OFF = {}; try { OFF = JSON.parse(get("mw-wc-off", "{}")) || {}; } catch (e) { OFF = {}; }
  const today = () => { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
  WC.datum = new URLSearchParams(location.search).get("datum") || today();
  const mmdd = () => WC.datum.slice(5, 7) + WC.datum.slice(8, 10);
  const aktiv = (p, md) => { if (!Array.isArray(p) || !p.length) return true;
    return p.some(q => (q[0] <= q[1] && q[0] <= md && md <= q[1]) || (q[0] > q[1] && (md >= q[0] || md <= q[1]))); };
  WC.aktiv = aktiv;
  const DATA = {};                                   // category -> FeatureCollection (loaded once)
  let map = null, pop = null;
  const usable = () => world() === "berg" ? true : !!(window.KQ && KQ.on && WC.on);
  function mark(fc) { const md = mmdd(); (fc.features || []).forEach(f => { const p = f.properties || {}; p.a = p.c === "weg" ? 1 : (aktiv(p.p, md) ? 1 : 0); }); return fc; }
  function fetchKat(k) {
    if (DATA[k]) return Promise.resolve(DATA[k]);
    const u = world() === "berg" ? PRE + "/api/karte/wildcamp/berg" : PRE + "/karte/wildcamp/" + WC.key + "/zonen/" + k + ".json";
    return fetch(u).then(r => r.json()).then(j => { DATA[k] = mark(world() === "berg" ? (j.fc || EMPTY) : j); return DATA[k]; });
  }
  const kats = () => world() === "berg" ? [KAT[0]] : KAT;
  function before() { const ls = (map.getStyle() || {}).layers || []; const b = ls.find(l => /^(kt|bk-vor|bk-live|bk-orte|bk-geheim)/.test(l.id)); return b ? b.id : undefined; }
  function addLayers() {
    if (!map || map.getSource("wc-wrz") && map.getLayer("wc-wrz-f")) return;
    const bf = before();
    kats().forEach(([k, n, c, dash]) => {
      if (!map.getSource("wc-" + k)) map.addSource("wc-" + k, {type: "geojson", data: EMPTY, tolerance: 0.6});
      const notWeg = ["!=", ["get", "c"], "weg"];
      map.addLayer({id: "wc-" + k + "-f", type: "fill", source: "wc-" + k, filter: notWeg,
        paint: {"fill-color": c, "fill-opacity": ["case", ["==", ["get", "a"], 1], 0.34, 0.07]}}, bf);
      map.addLayer({id: "wc-" + k + "-l", type: "line", source: "wc-" + k, filter: ["all", notWeg, ["==", ["get", "a"], 1]],
        paint: Object.assign({"line-color": c, "line-width": k === "wrz" ? 2.4 : 1.8}, dash ? {"line-dasharray": dash} : {})}, bf);
      map.addLayer({id: "wc-" + k + "-lo", type: "line", source: "wc-" + k, filter: ["all", notWeg, ["==", ["get", "a"], 0]],
        paint: {"line-color": c, "line-width": 1.2, "line-opacity": 0.6, "line-dasharray": [2, 2]}}, bf);
      if (k === "wrz") map.addLayer({id: "wc-weg", type: "line", source: "wc-wrz", filter: ["==", ["get", "c"], "weg"], minzoom: 11,
        paint: {"line-color": "#009E73", "line-width": 2, "line-dasharray": [2, 1.5]}}, bf);
    });
    if (!map.getSource("wc-hl")) { map.addSource("wc-hl", {type: "geojson", data: EMPTY});
      map.addLayer({id: "wc-hl-c", type: "line", source: "wc-hl", layout: {"line-cap": "round", "line-join": "round"}, paint: {"line-color": "#fff", "line-width": 9, "line-opacity": 0.9}});
      map.addLayer({id: "wc-hl-l", type: "line", source: "wc-hl", layout: {"line-cap": "round", "line-join": "round"}, paint: {"line-color": "#D55E00", "line-width": 5}}); }
  }
  function vis() {
    if (!map) return;
    kats().forEach(([k]) => { const v = ON && !OFF[k] ? "visible" : "none";
      ["-f", "-l", "-lo"].forEach(s => { if (map.getLayer("wc-" + k + s)) map.setLayoutProperty("wc-" + k + s, "visibility", v); });
      if (k === "wrz" && map.getLayer("wc-weg")) map.setLayoutProperty("wc-weg", "visibility", v);
      if (v === "visible") fetchKat(k).then(fc => { const s = map.getSource("wc-" + k); if (s) s.setData(fc); }).catch(() => {}); });
  }
  WC.redate = d => { if (d) WC.datum = d; Object.keys(DATA).forEach(k => { mark(DATA[k]); const s = map && map.getSource("wc-" + k); if (s) s.setData(DATA[k]); }); };
  // ---- the tap card ----
  function zoneBox(z) {
    const d = el("div", "z" + (z.aktiv ? "" : " off")); d.style.setProperty("--c", COL[z.kat] || "#888");
    d.appendChild(el("div", "", (z.aktiv ? "⚠ " : "") + z.text));
    d.appendChild(el("small", "", z.aktiv ? T("now in the protection period") : T("outside the protection period")));
    if (z.amtlich) d.appendChild(el("small", "", T("Official wording:") + " " + z.amtlich));
    if (z.u) { const a = el("a", "", T("Details")); a.href = z.u; a.target = "_blank"; a.rel = "noopener"; d.appendChild(a); }
    return d;
  }
  WC.punkt = (lat, lon) => fetch(PRE + "/api/karte/wildcamp/punkt?lat=" + lat + "&lon=" + lon + "&datum=" + WC.datum + "&lang=" + L(), {cache: "no-store"}).then(r => r.json());
  WC.card = j => {
    const w = el("div", "wc-pop"); w.id = "wc-card";
    w.appendChild(el("b", "", "🏕 " + T("Wildcamp")));
    if (j.zones && j.zones.length) j.zones.forEach(z => w.appendChild(zoneBox(z)));
    else { const n = el("div", "z", "✓ " + (j.none || T("no protected area known"))); n.style.setProperty("--c", "#888"); w.appendChild(n); }
    if (j.nur_bund) w.appendChild(el("small", "", j.nur_bund));
    const k = j.kanton;
    if (k) { const d = el("div", "kt"); d.appendChild(el("b", "", T("Canton") + " " + k.k + (k.name ? " (" + k.name + ")" : "")));
      d.appendChild(el("div", "", k.text));
      const s = el("small", "", T("Source:") + " "); const a = el("a", "", k.src_t); a.href = k.src; a.target = "_blank"; a.rel = "noopener"; s.appendChild(a);
      s.append(" · "); const b = el("a", "", T("Website of the canton")); b.href = k.web; b.target = "_blank"; b.rel = "noopener"; s.appendChild(b); d.appendChild(s); w.appendChild(d); }
    w.appendChild(el("small", "", j.legal || T("Information, not legal advice.")));
    return w;
  };
  function tap(e) {
    if (!ON || !usable() || (window.KT && KT.busy) || (window.EO && EO.busy)) return;
    const ll = e.lngLat;
    WC.punkt(ll.lat.toFixed(6), ll.lng.toFixed(6)).then(j => { if (!j.ok) return;
      const box = $("#wc-tap"); if (box) { box.textContent = ""; box.appendChild(WC.card(j)); box.hidden = false; }    // the whole card under the map
      const mini = el("div", "wc-pop wc-mini"); mini.id = "wc-mini";                                                  // on the map: the zones only
      (j.zones || []).slice(0, 3).forEach(z => { const d = el("div", "z" + (z.aktiv ? "" : " off"), (z.aktiv ? "⚠ " : "") + z.text); d.style.setProperty("--c", COL[z.kat] || "#888"); mini.appendChild(d); });
      if (!(j.zones || []).length) mini.appendChild(el("div", "z", "✓ " + (j.none || T("no protected area known"))));
      if ((j.zones || []).length > 3) mini.appendChild(el("small", "", "+ " + (j.zones.length - 3)));
      if (pop) pop.remove(); pop = new maplibregl.Popup({maxWidth: "240px", closeButton: true, className: "wc-popup"}).setLngLat(ll).setDOMContent(mini).addTo(map); }).catch(() => {});
  }
  // ---- the box under the map ----
  function installBox(into) {
    const w = el("div", "wc-inst"); let tm = 0; into.appendChild(w);
    const st = () => fetch(PRE + "/api/karte/wildcamp", {cache: "no-store"}).then(r => r.json());
    const act = a => fetch(PRE + "/api/karte/wildcamp", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: a, lang: L()})})
      .then(r => r.json()).then(S => { paint(S); return S; });
    function paint(S) {
      clearTimeout(tm); w.textContent = ""; if (!S) return; const D = S.dl || {}; const row = el("div", "wc-row");
      if (D.running) { const p = el("progress"); p.max = D.total || 1; p.value = D.phase === "unpack" ? (D.total || 1) : (D.got || 0);
        row.append(el("span", "", "⏳ " + MB(D.got) + " / " + MB(D.total) + " MB"), p, btn("✕", "sec", () => act("cancel")));
        tm = setTimeout(() => st().then(S2 => { if (S2.on && !WC.on) location.reload(); else paint(S2); }).catch(() => {}), 1200); }
      else if (S.on) { row.appendChild(el("span", "", "✓ " + T("Wildcamp package") + " · " + MB(S.size) + " MB · " + T("data of") + " " + ((S.meta || {}).datum || S.datum || "?")));
        const rm = btn("🗑", "sec", () => { rm.replaceWith(el("b", "", T("Remove the Wildcamp package?")), btn("✓", "red", () => act("delete").then(() => location.reload())), btn("✕", "sec", () => paint(S))); }); rm.id = "wc-del"; row.appendChild(rm); }
      else if (!S.pinned) row.appendChild(el("span", "wc-note", "🏕 " + T("The Wildcamp package is not installed.") + " (" + (TX[L()] && TX[L()]["comes with an update"] || "…") + ")"));
      else if (!S.fit) row.appendChild(el("span", "wc-warn", "⚠ " + T("too large for the host")));
      else { const ib = btn("⬇ " + T("Download Wildcamp") + " (" + MB(S.size) + " MB)", "", () => { if (ib.dataset.sure) act("install"); else { ib.dataset.sure = "1"; ib.textContent = T("Load the Wildcamp package now? %s MB from GitHub (fixed checksum).").replace("%s", MB(S.size)); } });
        ib.id = "wc-install"; ib.disabled = !S.space_ok; row.appendChild(ib); }
      w.appendChild(row); const e_ = S.error || (!D.running && D.msg ? D.msg : ""); if (e_) w.appendChild(el("div", "wc-warn", "⚠ " + e_));
    }
    st().then(paint).catch(() => {});
  }
  function legend(box) {
    const d = el("div", "wc-leg"); d.id = "wc-leg";
    const r = el("div"); const s1 = el("span", "wc-sw"); const i1 = el("i"); i1.style.cssText = "background:rgba(213,94,0,.34);border-color:#D55E00"; s1.append(i1);
    const s2 = el("span", "wc-sw"); const i2 = el("i"); i2.style.cssText = "background:rgba(213,94,0,.07);border:2px dashed rgba(213,94,0,.6)"; s2.append(i2);
    r.append(s1, s2, T("strong = protection period now · pale and dashed = outside the period")); d.appendChild(r);
    if (world() === "berg") d.appendChild(el("div", "", T("Invented wildlife rest areas of the Bergtal (for practice).")));
    else { d.appendChild(el("div", "", T("Dashed green: allowed routes in wildlife rest areas."))); d.appendChild(el("div", "", T("Only federal data: cantonal and municipal nature reserves are missing."))); }
    d.appendChild(el("div", "", T("Information, not legal advice.") + " " + T("Signs on site and the official data apply.")));
    if (world() !== "berg" && WC.on) { const a = el("a", "", "ⓘ " + T("Sources and licences") + " · " + T("© Data: BAFU, cantons, swisstopo (geo.admin.ch)"));
      a.href = PRE + "/karte/wildcamp/" + WC.key + "/LIZENZEN.txt"; a.target = "_blank"; a.rel = "noopener"; a.id = "wc-lic"; d.appendChild(a); }
    box.appendChild(d);
  }
  function panel() {
    const S = $("#wc"), B = $("#wc-body"); if (!S || !B) return; S.hidden = false; B.textContent = ""; $("#wc-h").textContent = T("Wildcamp");
    const h = $("#wc h2"); let mb = $("#wc-on"); if (mb) mb.remove();
    if (world() !== "berg" && !(window.KQ && KQ.on)) { S.hidden = true; const nn = $("#kq-none"); if (!nn || $("#wc-nomap")) return;
      const x = el("div", "wc-note", "🏕 " + (WC.host ?T("On the host the Wildcamp layer for Switzerland is not available: the offline map of Switzerland does not fit there.") : T("The Wildcamp layer needs the offline map of Switzerland."))); x.id = "wc-nomap"; nn.appendChild(x); return; }
    if (world() !== "berg" && !WC.on) { B.appendChild(el("div", "wc-note", T("The Wildcamp package is not installed.") + " " + T("Protected areas of Switzerland (federal open data), about %s MB, afterwards without internet.").replace("%s", MB(WC.size))));
      if (WC.host && !WC.fit) B.appendChild(el("div", "wc-warn", "⚠ " + T("too large for the host")));
      if (WC.admin) installBox(B); return; }
    mb = btn(ON ? "✓ " + T("Show") : T("Show"), "wc-main", () => { ON = !ON; put("mw-wc-on", ON ? "1" : "0"); mb.setAttribute("aria-pressed", ON ? "true" : "false"); mb.textContent = (ON ? "✓ " : "") + T("Show"); vis(); if (!ON && pop) pop.remove(); });
    mb.id = "wc-on"; mb.setAttribute("aria-pressed", ON ? "true" : "false"); h.appendChild(mb);
    B.appendChild(el("div", "wc-note", T("Protected areas for wild camping")));
    const r = el("div", "wc-row"); const lb = el("label", "", T("Date") + " "); const inp = el("input"); inp.type = "date"; inp.id = "wc-datum"; inp.value = WC.datum;
    lb.htmlFor = "wc-datum"; inp.onchange = () => { if (/^\d{4}-\d{2}-\d{2}$/.test(inp.value)) WC.redate(inp.value); };
    const td = btn(T("today"), "sec", () => { inp.value = today(); WC.redate(inp.value); }); td.id = "wc-today"; r.append(lb, inp, td); B.appendChild(r);
    const cr = el("div", "wc-row"); cr.id = "wc-kats";
    kats().forEach(([k, n, c]) => { const b = btn("", "wc-chip", () => { OFF[k] = !OFF[k]; put("mw-wc-off", JSON.stringify(OFF)); b.setAttribute("aria-pressed", OFF[k] ? "false" : "true"); vis(); });
      const i = el("i"); i.style.setProperty("--c", c); i.style.setProperty("--f", c + "55"); b.append(i, T(n)); b.dataset.k = k; b.id = "wc-k-" + k; b.setAttribute("aria-pressed", OFF[k] ? "false" : "true"); cr.appendChild(b); });
    B.appendChild(cr); legend(B);
    if (WC.admin && world() !== "berg") installBox(B);
    if (world() === "berg") fetchKat("wrz").then(fc => { if (!fc.features.length) B.insertBefore(el("div", "wc-warn", "⚠ " + T("The Bergtal map has no wildlife rest areas yet – it needs a newer Bergtal package.")), cr); }).catch(() => {});
  }
  // ---- hints for own places (639zzzzo) and tours (639zzx) ----
  WC.hl = line => { if (!map) return; const s = map.getSource("wc-hl"); if (!s) return;
    s.setData(line && line.length > 1 ? {type: "FeatureCollection", features: [{type: "Feature", properties: {}, geometry: {type: "LineString", coordinates: line}}]} : EMPTY);
    if (line && line.length > 1) { let a = 90, b = -90, c = 180, d = -180; line.forEach(p => { c = Math.min(c, p[0]); d = Math.max(d, p[0]); a = Math.min(a, p[1]); b = Math.max(b, p[1]); });
      map.fitBounds([[c, a], [d, b]], {padding: 60, maxZoom: 16, duration: 0}); } };
  window.wcPlace = (la, lo, into, sym) => {
    if (!usable() || !into) return;
    WC.punkt(la, lo).then(j => { if (!j.ok || !into.isConnected || !(j.zones || []).length) return;
      const old = into.querySelector(".wc-hint"); if (old) old.remove();
      const h = el("div", "wc-hint"); h.id = "wc-place";
      h.appendChild(el("b", "", "⚠ " + T(sym === "tent" ? "Night camp in a protected area – check the rules before you sleep here." : "This place is in a protected area:")));
      const ul = el("ul"); j.zones.forEach(z => ul.appendChild(el("li", "", z.text + " · " + T(z.aktiv ? "now in the protection period" : "outside the protection period")))); h.appendChild(ul);
      h.appendChild(el("small", "wc-note", j.legal)); into.appendChild(h); }).catch(() => {});
  };
  let tseq = 0;
  window.wcTour = (pts, into) => {
    if (!usable() || !into || !pts || pts.length < 2) return; const my = ++tseq;
    fetch(PRE + "/api/karte/wildcamp/linie", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({pts: pts.map(p => [p[0], p[1]]), datum: WC.datum, lang: L()})})
      .then(r => r.json()).then(j => { if (my !== tseq || !j.ok || !into.isConnected) return; const old = into.querySelector(".wc-hint"); if (old) old.remove();
        if (!(j.segs || []).length) return;
        const h = el("div", "wc-hint"); h.id = "wc-tour"; h.appendChild(el("b", "", "⚠ " + T("The route crosses protected areas:")));
        const ul = el("ul");
        j.segs.forEach((s, i) => { const li = el("li", "", "km " + s.km0.toFixed(1) + "–" + s.km1.toFixed(1) + ": " + s.text + " · " + T(s.aktiv ? "now in the protection period" : "outside the protection period"));
          const b = btn("🗺 " + T("Show section"), "sec", () => { WC.hl(s.line); const mp = $("#kq-map"); if (mp) mp.scrollIntoView({behavior: "smooth", block: "center"}); }); b.className = "sec wc-seg"; b.dataset.i = i;
          li.appendChild(document.createElement("br")); li.appendChild(b); ul.appendChild(li); });
        h.append(ul, el("small", "wc-note", j.legal)); into.appendChild(h); }).catch(() => {});
  };
  // ---- start: wait for the map of the page (Swiss map of 639zzq or Bergtal of 639zzzzzt) ----
  function attach(m) {
    map = m; WC.map = m;
    const go = () => { try { addLayers(); vis(); } catch (e) {} };
    if (m.isStyleLoaded()) go(); else m.once("load", go);
    m.on("styledata", () => { if (!m.getLayer("wc-" + kats()[0][0] + "-f") && m.isStyleLoaded()) go(); });
    m.on("click", tap);
  }
  function start() {
    panel();
    if (!usable()) return; let n = 0;
    const iv = setInterval(() => { const m = window.KQMAP; if (m && m.on) { clearInterval(iv); attach(m); } else if (++n > 200) clearInterval(iv); }, 150);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => setTimeout(start, 0)); else setTimeout(start, 0);
})();
"""
_kq_page_639zzzzzw = kq_page
_WC_AT = '<div class="kq-info" id="kq-info"></div>'
_WC_NONE = '<div id="kq-none" class="kq-none" hidden></div>'


# wraps: kq_page
def kq_page():                                              # + 639zzzzzw: the box «Wildcamp» under the map (Switzerland and Bergtal)
    html = _kq_page_639zzzzzw()
    if "window.WC = " in html or html.count(_WC_AT) != 1 or html.count(_WC_NONE) != 1 or "</head>" not in html:
        return html
    st = {"on": wc_installed(), "admin": kq_role() == "admin", "key": wc_key(), "size": WC_FILE["size"], "pinned": wc_pinned(),
          "host": wc_on_host(), "fit": wc_host_fit()}
    tx = wc_tx()
    for L_ in tx:                                           # one key of 639zzzzzt the install box uses as well
        tx[L_]["comes with an update"] = tr("comes with an update", L_ if L_ != "en" else "en")
    js = (WC_JS.replace("/*WCSTATE*/{}", json.dumps(st, ensure_ascii=False).replace("</", "<\\/"), 1)
          .replace("/*WCTX*/{}", json.dumps(tx, ensure_ascii=False).replace("</", "<\\/"), 1))
    return (html.replace(_WC_AT, _WC_AT + WC_HTML, 1)
            .replace("</head>","<style>" + WC_CSS + "</style><script>" + js + "</script></head>", 1))


# own places (639zzzzo): the hint on the card of a place and while editing (after setting / moving)
WC_EO_HOOKS = [("    bd.appendChild(where);\n", "    bd.appendChild(where);\n    if (window.wcPlace) wcPlace(p.la, p.lo, bd, p.sym);\n"),
               ('    bd.appendChild(el("h3", "", "✏️ " + T("Edit place")));\n',
                '    bd.appendChild(el("h3", "", "✏️ " + T("Edit place")));\n    if (window.wcPlace) wcPlace(p.la, p.lo, bd, p.sym);\n')]
# tours (639zzx): the crossed sections while drawing and in the detail of a tour
WC_KT_HOOKS = [("  function notes(s, into) {\n", "  function notes(s, into) {\n    if (window.wcTour) wcTour(KT.busy ? S.pts : (s.line || []), into);\n")]
WC_HOOKED = {}
if "EO_JS" in globals():
    for _a, _b in WC_EO_HOOKS:
        WC_HOOKED["eo:" + _a.strip()[:40]] = EO_JS.count(_a) == 1
        if EO_JS.count(_a) == 1:
            EO_JS = EO_JS.replace(_a, _b, 1)
for _a, _b in WC_KT_HOOKS:
    WC_HOOKED["kt:" + _a.strip()[:40]] = KT_JS.count(_a) == 1
    if KT_JS.count(_a) == 1:
        KT_JS = KT_JS.replace(_a, _b, 1)


# ---- the manual: one point after the Bergtal map (5 languages) --------------------------------------------------------------------
_HELP_WC = {
    "de": ("🏕 Wildcamp", "(Mehr → 🗺 Karte, Feld «Wildcamp» unter der Karte): Schutzgebiete aus den offenen Daten des Bundes – Wildruhezonen (mit Schutzzeit, verbindlich oder empfohlen, erlaubte Routen grün gestrichelt), Jagdbanngebiete, Nationalpark, Vogelreservate, Moore und Auen; Schalter je Kategorie und ein Datum: in der Schutzzeit kräftig, sonst blass. Antippen zeigt die Schutzzone und eine kurze Notiz zum Wildcampen im Kanton (mit Quelle). Eigene Orte und Touren in einer Zone bekommen einen Hinweis. Paket einmal laden (Admin, etwa 2.5 MB). Im Bergtal: erfundene Wildruhezonen zum Üben. Nur Daten des Bundes – kantonale Naturschutzgebiete fehlen. Information, keine Rechtsberatung."),
    "en": ("🏕 Wildcamp", "(More → 🗺 Map, box “Wildcamp” under the map): protected areas from the federal open data – wildlife rest areas (with protection period, binding or recommended, allowed routes dashed green), game reserves, the National Park, bird reserves, mires and floodplains; a switch per category and a date: strong in the protection period, pale outside. A tap shows the protected area and a short note about wild camping in the canton (with source). Own places and tours inside a zone get a hint. Load the package once (administrator, about 2.5 MB). In the Bergtal: invented wildlife rest areas for practice. Federal data only – cantonal nature reserves are missing. Information, not legal advice."),
    "fr": ("🏕 Camping sauvage", "(Plus → 🗺 Carte, case « Camping sauvage » sous la carte) : zones protégées des données ouvertes de la Confédération – zones de tranquillité (avec période de protection, contraignantes ou recommandées, itinéraires autorisés en tirets verts), districts francs, Parc national, réserves d’oiseaux, marais et zones alluviales ; un bouton par catégorie et une date : intense pendant la période de protection, pâle sinon. Un toucher montre la zone protégée et une courte note sur le camping sauvage dans le canton (avec source). Les lieux et randonnées dans une zone reçoivent un avertissement. Charger le paquet une fois (administrateur, environ 2,5 Mo). Dans le Bergtal : zones inventées pour s’exercer. Seulement les données fédérales – les réserves cantonales manquent. Information, pas un conseil juridique."),
    "it": ("🏕 Campeggio libero", "(Altro → 🗺 Mappa, riquadro «Campeggio libero» sotto la mappa): zone protette dai dati aperti della Confederazione – zone di tranquillità (con periodo di protezione, vincolanti o raccomandate, itinerari autorizzati tratteggiati in verde), bandite di caccia, Parco nazionale, riserve per uccelli, paludi e zone golenali; un interruttore per categoria e una data: intenso nel periodo di protezione, chiaro fuori. Un tocco mostra la zona protetta e una breve nota sul campeggio libero nel Cantone (con fonte). Luoghi propri ed escursioni in una zona ricevono un avviso. Caricare il pacchetto una volta (amministratore, circa 2,5 MB). Nel Bergtal: zone inventate per esercitarsi. Solo dati federali – mancano le riserve cantonali. Informazione, non consulenza legale."),
    "rm": ("🏕 Campadi liber", "(Dapli → 🗺 Charta, champ «Campadi liber» sut la charta): zonas protegidas da las datas avertas da la Confederaziun – zonas da ruaus (cun temp da protecziun, liantas u recumandadas, rutas permessas verd cun strichs), districts da protecziun da la chatscha, Parc naziunal, reservats d’utschels, palids ed auas; in cumutatur per categoria ed ina data: ferm en il temp da protecziun, pallid ordaifer. Tutgar mussa la zona protegida ed ina curta notizia davart il campadi liber en il chantun (cun funtauna). Agens lieus e turas en ina zona survegnan in avis. Chargiar il pachet ina giada (administratur, var 2,5 MB). En il Bergtal: zonas inventadas per exercitar. Mo datas federalas – las reservas chantunalas mancan. Infurmaziun, betg cussegliaziun giuridica."),
}


def _help_wc(doc, lang):
    h_, x_ = _HELP_WC[lang]
    anchor = (_HELP_BK.get(lang) or _HELP_KT[lang])[0] if "_HELP_BK" in globals() else _HELP_KT[lang][0]
    if h_ in doc or anchor not in doc:
        return doc
    from html import escape as _e
    i = doc.find("</li>", doc.find(anchor))
    return doc if i < 0 else doc[:i + 5] + f"<li><b>{h_}</b> {_e(x_, quote=False)}</li>" + doc[i + 5:]


_hp_en_wc = HELP_PAGE.find('<div lang="en">')
if _hp_en_wc > 0:
    HELP_PAGE = _help_wc(HELP_PAGE[:_hp_en_wc], "de") + _help_wc(HELP_PAGE[_hp_en_wc:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_wc(HELP_X[_L], _L)


# ---- self-test (werkzeuge/wildcamp_test.py: package, install, dates, tap, hints, Bergtal, the page in the browser) ----------------
def wildcamp_selftest():
    assert all(WC_HOOKED.values()) and len(WC_HOOKED) == 3, WC_HOOKED
    assert wc_aktiv([["1220", "0430"]], "0101") and wc_aktiv([["1220", "0430"]], "1220") and not wc_aktiv([["1220", "0430"]], "1122")
    assert wc_aktiv([["0401", "0715"]], "0601") and not wc_aktiv([["0401", "0715"]], "1201") and wc_aktiv([], "0815") and wc_aktiv(None, "0815")
    assert wc_mmdd("2026-12-24") == "1224" and len(wc_mmdd("x")) == 4
    assert wc_zeit({"p": [["1220", "0430"]]}, "de") == "20.12.–30.4." and wc_zeit({"p": []}, "de") == "ganzjährig"
    sq = _wc_index([{"type": "Feature", "properties": {"c": "wrz", "n": "Test", "i": "t.1", "p": [["1220", "0430"]], "s": "v", "b": "R20"},
                     "geometry": {"type": "Polygon", "coordinates": [[[8.0, 46.0], [8.1, 46.0], [8.1, 46.1], [8.0, 46.1], [8.0, 46.0]],
                                                                     [[8.04, 46.04], [8.06, 46.04], [8.06, 46.06], [8.04, 46.06], [8.04, 46.04]]]}}])
    assert len(_wc_find(sq, 8.02, 46.02)) == 1 and not _wc_find(sq, 8.05, 46.05) and not _wc_find(sq, 8.2, 46.05), "inside / hole / outside"
    t = wc_text("wrz", _wc_find(sq, 8.02, 46.02)[0], "de", "0101")
    assert t["text"] == "Wildruhezone «Test» – Betreten 20.12.–30.4. verboten (verbindlich)" and t["aktiv"], t
    assert not wc_text("wrz", _wc_find(sq, 8.02, 46.02)[0], "de", "0815")["aktiv"]
    for L_ in ("de", "fr", "it", "rm", "en"):
        assert "{zeit}" not in wc_text("wrz", {"c": "wrz", "n": "X", "b": "E30", "p": []}, L_, "0101")["text"]
    assert set(WC_KT) == set(WC_KT_WEB) and len(WC_KT) == 26 and all(e in WC_KT_EX for s, ex in WC_KT.values() for e in ex)
    assert wc_punkt(46.8, 8.2, "de")["none"] in ("keine Schutzzone bekannt", "") and wc_punkt(46.8, 8.2, "de")["legal"] == "Information, keine Rechtsberatung."
    pg = kq_page()
    assert pg.count("window.WC = ") == 1 and "/*WCSTATE*/" not in pg and "/*WCTX*/" not in pg and pg.count('id="wc"') == 1
    assert "innerHTML" not in WC_JS and "confirm(" not in WC_JS and "https://" not in WC_JS and "prompt(" not in WC_JS
    assert all(len(v) == 4 and all(v) and "ß" not in v[0] for v in _HX_WC.values())
    assert WC_STATIC.fullmatch("zonen/moor.json") and WC_STATIC.fullmatch("LIZENZEN.txt")
    for bad in ("wildcamp.ok", "../x.json", "zonen/../wildcamp.ok", "kantone.json.gz", "zonen/x.json"):
        assert not WC_STATIC.fullmatch(bad), bad
    for p_ in ("/api/karte/wildcamp", "/api/karte/wildcamp/punkt", "/api/karte/wildcamp/berg", "/karte/wildcamp/0123456789ab/zonen/wrz.json"):
        assert role_allows("kid", p_, "GET", {}) and role_allows("view", p_, "GET", {}), p_
    assert role_allows("view", "/api/karte/wildcamp/linie", "POST", {}) and not role_allows("family", "/api/karte/wildcamp", "POST", {"action": "install"})
    assert _HELP_WC["de"][0] in HELP_PAGE and _HELP_WC["en"][0] in HELP_PAGE
    return "Wildcamp: periods, index, texts, hooks, rights, manual"


SELFTEST_EXTRA.append(("Wildcamp (639zzzzzw)", wildcamp_selftest))
'''
zd_exec(WC_PY, "639zzzzzw_wildcamp.py")
