#@ MoveEye – Teil 639zzzzzt: «⛰ Bergtal» auf der Offline-Karte (/karte, Schalter «Schweiz / Bergtal») – die Karte des Tals im Simulator wie die Landeskarte (Relief, Höhenlinien, 3D, alle Orte mit Symbolen, Wanderwege gelb / rot / blau, Bäche, Seen), geheime Orte erst nach dem Finden im Simulator, live MoveEye, Figur, Mover und Erkanntes, Touren mit Bergtal-Höhen, «Tour im Sim nachlaufen», Vorschläge; Paket als Release-Asset (Grösse + sha256). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entscheide des Besitzers (21.11.2026, freigegeben):
#   * Wo: /karte bekommt oben den Schalter «🗺 Schweiz | ⛰ Bergtal» (pro Browser gemerkt, mw-kq-welt; ?welt=berg|ch). Ohne
#     Schweizer Karte (Homepage / Host: 1,5 GB RAM, 2 GB Platte) geht die Seite gleich ins Bergtal. Das Paket braucht die
#     Schweizer Karte NICHT: MapLibre GL JS und die Schriften liegen darin (unverändert aus karte-web-2.zip, Teil 639zzq).
#   * Inhalt: Relief (hillshade) und 3D-Gelände aus Höhen-Kacheln (terrarium), Höhenlinien 10 m (Zählkurven 100 m, blau auf
#     dem Gletscher), Wald / Fels / Geröll / Gletscher / Moor in den Farben der Topo-Karte (werkzeuge/karten/stil.py), alle
#     Orte mit Symbol und Namen (Gipfel und Pässe mit Höhe), Wanderwege gelb / rot / blau, Bäche, Seen, Strasse.
#   * GEHEIME Orte (versteckte Dinge, Spoiler, Ziele der Kapitel «Die Karte des Grossvaters», der geheime See mit Pfad):
#     sie stehen im Paket in geheim.json, das NIE als Datei herausgeht. /api/karte/berg gibt nur die heraus, die der
#     verbundene Simulator in seiner Antwort (world_reply «bkarte».found) als gefunden meldet; ohne Simulator (oder älter
#     als 15 s) keine. Das Ei des Bergtals (639z) steht nie auf der Karte.
#   * Koordinaten: eigenes Gitter in Metern ab der Mitte des Tals (x = Osten, z = Süden). MapLibre braucht Grad: das Tal liegt
#     um 0° / 0° (lon = x / BK_M, lat = -z / BK_M, BK_M = Meter pro Grad beim Erdradius von kt_dist) - so rechnen Touren und
#     Höhen genau in Metern, und nichts ist mit der Schweiz zu verwechseln (lat 45–48). Angezeigt werden nur «O 120 m · N
#     340 m». Eine Tour gehört zum Bergtal, wenn ihr erster Punkt im Rahmen des Tals liegt (bk_in) - kein neues Feld.
#   * Live (Simulator verbunden, im Bergtal): MoveEye mit Blickkegel, die Figur (Erkunden als Person), der Mover, was MoveEye
#     gerade erkennt (Tiere grün, Personen orange) - alle 1,5 s.
#   * Touren (639zzx): Auf- / Abstieg, Profil und Wanderzeit mit den Höhen des Pakets (kh_line umhüllt: Punkte im Bergtal ->
#     bk_line), die Liste zeigt im Bergtal nur Bergtal-Touren (und umgekehrt). «🎮 Tour im Sim nachlaufen» (Admin, Simulator
#     verbunden): sim_control {"action": "bkarte", "do": "tour", "pts": [[x, z] …]} - die Figur geht sie ab (sonst der Mover).
#     Vorschläge aus dem Paket (touren.json, auf den Wanderwegen gesucht), z. B. Hospiz → Pass → Biwak, als Tour speicherbar.
#   * Paket: bergtal-karte-N.zip am Release BK_TAG (werkzeuge/bergkarte/paket.py aus werkzeuge/bergkarte/export.gd, Workflow
#     «Bergtal-Karte»), Grösse + sha256 hier in BK_FILE (paket.py --eintragen); size 0 = noch nicht freigegeben. Laden nur
#     der Admin (wie 639zzq): Platz (BK_FREE_MIN bleibt frei - nicht 2 GB: das Paket hat ~3 MB), Fortsetzen, Prüfsumme vor dem
#     Auspacken, ein neuer Ordner erst am Schluss umbenannt. Auf dem Host darf der Faden «bergkarte-dl» zu GitHub (639zzzzw).
#   * Texte in 5 Sprachen; das Fenster (Tk) hat keine Offline-Karte - dort nichts. Der Live-Reiter bleibt unverändert.
# Selbsttest bk_selftest; Tests werkzeuge/bergkarte_test.py (Schalter, geheime Orte, Touren-Profil, Laden, Seite im Browser)
# und werkzeuge/bergkarte_test.gd (Paket = Simulator: Zahl der Orte, Höhen an Stichproben).
# ----------------------------------------------------------------------------
# Die Pins bleiben in der (signierten) Hauptdatei; der Programmtext steht in EINEM Literal (Hauptdatei klein, wie 639zzzzo):
# werkzeuge/bauen.py legt es in die Zusatz-ZIP (über ZD_SHA256 mit signiert). Ohne ZIP gibt es die Bergtal-Karte nicht - sie
# gehört nicht zu Start, Schutz, Alarm, Update oder Reparatur.
BK_TAG = "bergkarte-1"
BK_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/"}   # + <tag>/<name>; Tests: lokaler Server
# Werte aus werkzeuge/bergkarte/paket.py (pins_bergkarte.txt des Workflows «Bergtal-Karte»); size 0 = noch nicht freigegeben
BK_FILE = {"name": "bergtal-karte-1.zip", "size": 0, "sha256": "", "unpacked": 0, "sim": ""}
BK_PY = r'''BK_FORMAT = 1
BK_MAX = 80 * 1000 * 1000                                  # hard limit of the package (also unpacked)
BK_FREE_MIN = 200 * 1000 * 1000                            # so much stays free after the install
BK_M = 6371008.8 * math.pi / 180.0                         # metres per degree at 0° / 0° (kt_dist uses the same radius)
BK_FRAME = 0.012                                           # degrees: a point within ± this is in the Bergtal (± 1334 m)
BK_FRESH = 15.0                                            # s: so old may the answer of the simulator be (secrets)
BK_LIVE_FRESH = 4.0                                        # s: live positions
BK_SIM_PTS = 600                                           # points of a tour sent to the simulator (bergkarte.gd MAX_PTS)
BK_STATIC = re.compile(r"(stil|stil_dunkel|vektor)\.json|land(_dunkel)?\.png|dem/\d{1,2}/\d{1,6}/\d{1,6}\.png|LIZENZEN\.txt|"
                       r"web/(maplibre-gl\.(js|css)|LIZENZEN_karte_web\.txt|fonts/[A-Za-z0-9 ,]{1,120}/\d{1,5}-\d{1,5}\.pbf)")
BK_NEED = ("bergkarte.json", "stil.json", "stil_dunkel.json", "vektor.json", "geheim.json", "touren.json", "hoehen.f32", "web/maplibre-gl.js")
BK_DL = {"running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": False, "phase": ""}
BK_RT = {"lock": threading.Lock(), "ok_t": 0.0, "ok": False, "h": None, "meta": None, "geheim": None, "orte": None, "tours": None, "vor": None}


def bk_dir():
    return os.path.join(DATA_DIR, "bergkarte")


def bk_dl_dir():
    return os.path.join(DATA_DIR, "bergkarte_dl")


def bk_pinned():
    f = BK_FILE
    return bool(isinstance(f.get("size"), int) and 0 < f["size"] <= BK_MAX and re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or ""))
                and isinstance(f.get("unpacked"), int) and 0 < f["unpacked"] <= BK_MAX and re.fullmatch(r"bergtal-karte-\d{1,3}\.zip", f.get("name") or "")
                and re.fullmatch(r"bergkarte-\d{1,3}", BK_TAG) and f["name"].split("-")[-1].split(".")[0] == BK_TAG.split("-")[1])


def bk_key():
    return (BK_FILE.get("sha256") or "0" * 12)[:12]


def bk_reset():
    with BK_RT["lock"]:
        BK_RT.update(ok_t=0.0, ok=False, h=None, meta=None, geheim=None, orte=None, tours=None, vor=None)
    with KT["lock"]:
        KT["stats"].clear()                                   # tours of the Bergtal: their numbers change with the package


def bk_installed():
    """the package of BK_FILE is unpacked (marker bergkarte.ok with tag + sha256, every needed file there) - every 2 s"""
    now = time.time()
    if now - BK_RT["ok_t"] < 2.0:
        return BK_RT["ok"]
    ok = False
    if bk_pinned():
        try:
            with open(os.path.join(bk_dir(), "bergkarte.ok"), encoding="utf-8") as fh:
                m = json.load(fh)
            ok = (isinstance(m, dict) and m.get("tag") == BK_TAG and m.get("sha256") == BK_FILE["sha256"]
                  and all(os.path.isfile(os.path.join(bk_dir(), *p.split("/"))) for p in BK_NEED))
        except (OSError, ValueError):
            ok = False
    if ok != BK_RT["ok"]:
        BK_RT.update(h=None, meta=None, geheim=None, orte=None, tours=None, vor=None)
    BK_RT["ok"], BK_RT["ok_t"] = ok, now
    return ok


def _bk_json(name):
    with open(os.path.join(bk_dir(), name), encoding="utf-8") as fh:
        return json.load(fh)


def bk_meta():
    if not bk_installed():
        return None
    if BK_RT["meta"] is None:
        try:
            m = _bk_json("bergkarte.json")
            g = m["grid"]
            BK_RT["meta"] = {"tag": m["tag"], "sim": str(m.get("sim") or ""), "center": m["center"], "bounds": m["bounds"], "landc": m["landc"],
                             "counts": m.get("counts", {}), "grid": {k: float(g[k]) for k in ("lo", "step", "n", "alt0")}, "mpd": float(m["m_per_deg"])}
        except (OSError, ValueError, KeyError, TypeError):
            return None
    return BK_RT["meta"]


def bk_heights():
    """the height grid of the package (Float32, about 1 MB) - kept once read"""
    if BK_RT["h"] is None:
        import array as _ar
        a = _ar.array("f")
        with open(os.path.join(bk_dir(), "hoehen.f32"), "rb") as fh:
            a.frombytes(fh.read())
        if sys.byteorder != "little":
            a.byteswap()
        n = int(bk_meta()["grid"]["n"])
        if len(a) != n * n:
            raise ValueError("height grid has the wrong size")
        BK_RT["h"] = a
    return BK_RT["h"]


def bk_xz(lat, lon):
    return lon * BK_M, -lat * BK_M


def bk_ll(x, z):
    return [round(x / BK_M, 7), round(-z / BK_M, 7)]


def bk_in(lat, lon):
    try:
        return abs(float(lat)) <= BK_FRAME and abs(float(lon)) <= BK_FRAME
    except (TypeError, ValueError):
        return False


def bk_H(x, z):
    """height above sea level of the valley like bergtal.gd H() (bilinear; outside the grid the edge rises) - None without package"""
    m = bk_meta()
    if m is None:
        return None
    g = m["grid"]
    lo, st, n = g["lo"], g["step"], int(g["n"])
    h = bk_heights()
    fx, fz = (x - lo) / st, (z - lo) / st
    out = 0.0
    if fx < 0 or fz < 0 or fx > n - 1 or fz > n - 1:
        out = max(max(-fx, fx - (n - 1)), max(-fz, fz - (n - 1))) * st * 0.35
        fx, fz = min(max(fx, 0.0), n - 1.001), min(max(fz, 0.0), n - 1.001)
    i, j = min(int(fx), n - 2), min(int(fz), n - 2)
    u, v = fx - i, fz - j
    k = j * n + i
    a = h[k] + (h[k + 1] - h[k]) * u
    b = h[k + n] + (h[k + n + 1] - h[k + n]) * u
    return g["alt0"] + a + (b - a) * v + out


def bk_height(lat, lon):
    if not bk_in(lat, lon) or not bk_installed():
        return None
    try:
        v = bk_H(*bk_xz(lat, lon))
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return None if v is None else round(v, 1)


def bk_line(pts):
    """a drawn route in the Bergtal -> like kh_line: ([(lat, lon, height)] every ~10 m, True) · (flat, None) without package"""
    flat = [(p[0], p[1], None) for p in pts]
    if not bk_installed():
        return flat, None
    tot = sum(kt_dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))
    step = max(10.0, tot / (KT_MAX_PTS - len(pts) - 1)) if tot > 0 else 10.0
    out = []
    try:
        for i in range(len(pts)):
            a = pts[i]
            if i:
                b0 = pts[i - 1]
                k = int(kt_dist(b0, a) // step)
                for j in range(1, k + 1):
                    r = j / (k + 1.0)
                    la, lo = b0[0] + (a[0] - b0[0]) * r, b0[1] + (a[1] - b0[1]) * r
                    out.append((la, lo, round(bk_H(*bk_xz(la, lo)), 1)))
            out.append((a[0], a[1], round(bk_H(*bk_xz(a[0], a[1])), 1)))
    except (OSError, ValueError, KeyError, TypeError):
        return flat, False
    return out, True


_kh_line_639zzzzzt = kh_line


# wraps: kh_line
def kh_line(pts):                                           # + 639zzzzzt: a route in the Bergtal takes the heights of its package
    if pts and all(bk_in(p[0], p[1]) for p in pts):
        return bk_line(pts)
    return _kh_line_639zzzzzt(pts)


_kt_row_639zzzzzt = kt_row


# wraps: kt_row
def kt_row(t, who):                                         # + 639zzzzzt: «welt» berg for tours in the Bergtal (the list shows its world)
    r = _kt_row_639zzzzzt(t, who)
    if t.get("pts") and bk_in(t["pts"][0][0], t["pts"][0][1]):
        r["welt"] = "berg"
    return r


# ---- the simulator: found secrets and live positions (world_reply «bkarte», bergkarte.gd) ------------------------------------------
_simvals_take_639zzzzzt = simvals_take


# wraps: simvals_take
def simvals_take(rep):                                    # + 639zzzzzt: the answer «bkarte» of the simulator (only in the Bergtal)
    _simvals_take_639zzzzzt(rep)
    try:
        b = rep.get("bkarte") if isinstance(rep, dict) else None
        SIM["bkarte"] = dict(b, t=time.time()) if isinstance(b, dict) else None
    except Exception:
        SIM["bkarte"] = None


def _bk_sim(fresh):
    b = SIM.get("bkarte") if CFG.get("sim_on") and SIM.get("ok") else None
    if not isinstance(b, dict) or time.time() - float(b.get("t") or 0) > fresh:
        return None
    return b


def bk_found():
    """the found-ids the connected simulator reports - an empty set without a simulator (then every secret stays hidden)"""
    b = _bk_sim(BK_FRESH)
    f = b.get("found") if b else None
    return {str(x)[:80] for x in f[:400]} if isinstance(f, list) else set()


def bk_geheim(found):
    """GeoJSON of the secret places / trails / lakes with a found-id in «found» (never more)"""
    if not bk_installed():
        return {"type": "FeatureCollection", "features": []}
    if BK_RT["geheim"] is None:
        BK_RT["geheim"] = _bk_json("geheim.json")
    G = BK_RT["geheim"]
    F = []
    hit = lambda ids: any(str(i) in found for i in (ids or []))
    for o in G.get("orte", []):
        if hit(o.get("found")):
            F.append({"type": "Feature", "properties": {"t": "geheim", "name": o["name"], "kind": o.get("kind", "geheim"), "ele": o.get("ele")},
                      "geometry": {"type": "Point", "coordinates": o["lonlat"]}})
    for w in G.get("wege", []):
        if hit(w.get("found")):
            F.append({"type": "Feature", "properties": {"t": "geheim_weg", "name": w["name"], "g": w.get("g", 3)},
                      "geometry": {"type": "LineString", "coordinates": w["coords"]}})
    for s in G.get("seen", []):
        if hit(s.get("found")):
            F.append({"type": "Feature", "properties": {"t": "geheim_see", "ele": s.get("ele")}, "geometry": {"type": "Polygon", "coordinates": [s["ring"]]}})
    return {"type": "FeatureCollection", "features": F}


def bk_secret_total():
    if not bk_installed():
        return 0
    if BK_RT["geheim"] is None:
        BK_RT["geheim"] = _bk_json("geheim.json")
    return len(BK_RT["geheim"].get("orte", []))


def _bk_pt(v, n=3):
    """[x, z, az, …] of the simulator -> {x, z, ll, az, fov} (checked numbers only)"""
    if not isinstance(v, list) or len(v) < 2:
        return None
    try:
        x, z = float(v[0]), float(v[1])
        if not (math.isfinite(x) and math.isfinite(z)) or abs(x) > 5000 or abs(z) > 5000:
            return None
        o = {"x": round(x, 1), "z": round(z, 1), "ll": bk_ll(x, z)}
        if len(v) > 2:
            o["az"] = round(float(v[2]) % 360.0, 1)
        if len(v) > 3 and n > 3:
            o["fov"] = round(min(max(float(v[3]), 5.0), 180.0), 1)
        return o
    except (TypeError, ValueError):
        return None


def _bk_f(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.0
    return round(v, 1) if math.isfinite(v) and 0 <= v <= 1e6 else 0.0


def bk_live():
    """where MoveEye, the figure and the mover are and what MoveEye detects right now - None without a simulator in the Bergtal"""
    b = _bk_sim(BK_LIVE_FRESH)
    if not b:
        return None
    out = {"me": _bk_pt(b.get("me"), 4), "fig": _bk_pt(b.get("fig")), "mover": _bk_pt(b.get("mover")), "seen": []}
    for s in (b.get("seen") or [])[:24] if isinstance(b.get("seen"), list) else []:
        if isinstance(s, list) and len(s) >= 3 and s[0] in ("p", "a"):
            p = _bk_pt(s[1:3])
            if p:
                out["seen"].append({"w": s[0], "ll": p["ll"]})
    t = b.get("tour")
    if isinstance(t, dict):
        out["tour"] = {"name": _kt_name(t.get("name"))[:80], "who": "person" if t.get("who") == "person" else "mover", "done": bool(t.get("done")),
                       "why": str(t.get("why") or "")[:20], "left": _bk_f(t.get("left")), "len": _bk_f(t.get("len"))}
    return out


# ---- the package: load, check, unpack, remove (only the administrator) ------------------------------------------------------------
def bk_space_ok():
    part = os.path.join(bk_dl_dir(), BK_FILE["name"] + ".part")
    have = os.path.getsize(part) if os.path.isfile(part) else 0
    return kq_free() - (BK_FILE["size"] - have + BK_FILE["unpacked"]) >= BK_FREE_MIN


def bk_download(wait=False):
    if not bk_pinned():
        return False, "comes with an update"
    if BK_DL["running"] or bk_installed():
        return True, ""
    if not bk_space_ok():
        return False, "not enough free space on the memory card"
    BK_DL.update(running=True, got=0, total=BK_FILE["size"], msg="", stop=False, done=False, phase="load")

    def work():
        dd, d_ = bk_dl_dir(), bk_dir()
        zp = os.path.join(dd, BK_FILE["name"])
        new = d_ + ".neu"
        try:
            os.makedirs(dd, exist_ok=True)
            bio_fetch(BK_BASE["url"] + BK_TAG + "/" + BK_FILE["name"], zp, BK_FILE, BK_DL)   # 639zzd: resume, exact size + sha256
            BK_DL["phase"] = "unpack"
            shutil.rmtree(new, ignore_errors=True)
            os.makedirs(new)
            if _kq_unzip(zp, new, BK_FILE["unpacked"]) != BK_FILE["unpacked"]:
                raise ValueError("package has the wrong size")
            with open(os.path.join(new, "bergkarte.json"), encoding="utf-8") as fh:
                m = json.load(fh)
            if m.get("tag") != BK_TAG or int(m.get("format") or 0) != BK_FORMAT:
                raise ValueError("package does not fit this MoveEye")
            for p in BK_NEED:
                if not os.path.isfile(os.path.join(new, *p.split("/"))):
                    raise ValueError("package incomplete")
            with open(os.path.join(new, "bergkarte.ok"), "w", encoding="utf-8") as fh:
                json.dump({"tag": BK_TAG, "sha256": BK_FILE["sha256"]}, fh)
            shutil.rmtree(d_, ignore_errors=True)
            os.replace(new, d_)
            os.remove(zp)                                   # only the unpacked files stay (about 4 MB)
            BK_DL["done"] = True
            bk_reset()
            log_event("sys", f"Bergtal map installed ({BK_TAG}, {round(BK_FILE['size'] / 1e6, 1)} MB)")
        except InterruptedError:
            BK_DL["msg"] = "cancelled"
        except Exception as e:
            BK_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Bergtal map not installed: {BK_DL['msg']}")
            shutil.rmtree(new, ignore_errors=True)
            if "checksum" in BK_DL["msg"] or "large" in BK_DL["msg"]:
                for p in (zp, zp + ".part"):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        finally:
            BK_DL.update(running=False, phase="")
    if wait:
        work()
        return (not BK_DL["msg"]), BK_DL["msg"]
    threading.Thread(target=work, daemon=True, name="bergkarte-dl").start()
    return True, ""


def bk_delete():
    if BK_DL["running"]:
        return False, "busy right now - try again in a moment"
    shutil.rmtree(bk_dir(), ignore_errors=True)
    shutil.rmtree(bk_dl_dir(), ignore_errors=True)
    bk_reset()
    log_event("sys", "Bergtal map deleted")
    return True, ""


if "HOST_DL_THREADS" in globals():                        # 639zzzzw: on the host this thread may reach GitHub (fixed checksum)
    HOST_DL_THREADS = tuple(HOST_DL_THREADS) + ("bergkarte-dl",)


def bk_orte():
    """the places for the search: [[name, lon, lat, kind, ele]] (public ones only)"""
    if BK_RT["orte"] is None:
        out = []
        for f in _bk_json("vektor.json").get("features", []):
            p = f.get("properties") or {}
            if p.get("t") == "ort":
                out.append([p.get("name"), f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1], p.get("kind"), p.get("ele")])
        BK_RT["orte"] = out
    return BK_RT["orte"]


def bk_vorschlaege():
    """the suggested tours of the package with their numbers (heights of the package) - kept"""
    if BK_RT["vor"] is None:
        out = []
        for i, t in enumerate(_bk_json("touren.json")[:20]):
            pts = [(float(p[0]), float(p[1])) for p in t.get("pts", [])[:KT_MAX_DRAW] if bk_in(p[0], p[1])]
            if len(pts) < 2:
                continue
            line, cov = kh_line(pts)
            s = kt_stats(line, drawn=True)
            s["m"] = kt_stats([(p[0], p[1], None) for p in pts])["m"]
            out.append(dict({k: s.get(k) for k in ("m", "ele", "up", "down", "lo", "hi", "min", "profile", "smooth", "model")},
                            i=i, name=_kt_name(t.get("name")), stops=[_kt_name(x) for x in t.get("stops", [])][:8], pts=[[p[0], p[1]] for p in pts]))
        BK_RT["vor"] = out
    return BK_RT["vor"]


def bk_state():
    on = bk_installed()
    m = bk_meta() if on else None
    return {"on": on, "pinned": bk_pinned(), "tag": BK_TAG, "size": BK_FILE["size"], "unpacked": BK_FILE["unpacked"], "sim_ver": BK_FILE.get("sim", ""),
            "space_ok": True if on else bk_space_ok(), "free_min": BK_FREE_MIN, "admin": kq_role() == "admin", "sim": kq_sim_ok(), "key": bk_key(),
            "meta": m, "dl": {k: BK_DL[k] for k in ("running", "got", "total", "msg", "done", "phase")}}


def bk_tour_sim(d, who):
    """send a tour (id of 639zzx, or a suggestion) to the simulator: the figure / the mover walks it"""
    if not kq_sim_ok():
        return False, "The simulator is not connected.", {}
    pts, name = None, ""
    if d.get("action") == "tour_stop":
        r = sim_control({"action": "bkarte", "do": "stop", "src": "mw"}) or {}
        return bool(r.get("ok")), "" if r.get("ok") else "The simulator does not know this yet - it needs a newer version.", {}
    if "vorschlag" in d:
        try:
            v = bk_vorschlaege()[int(d.get("vorschlag"))]
            pts, name = v["pts"], v["name"]
        except (ValueError, TypeError, IndexError, OSError, KeyError):
            return False, "unknown tour", {}
    else:
        tid = str(d.get("id") or "")
        T_ = kt_load()
        t = T_.get(tid) if KT_ID.match(tid) else None
        if t is None or not kt_can_see(t, who):
            return False, "unknown tour", {}
        pts, name = [(p[0], p[1]) for p in t["pts"]], t["name"]
    if not pts or not all(bk_in(p[0], p[1]) for p in pts):
        return False, "This tour is not in the Bergtal.", {}
    step = max(1, (len(pts) + BK_SIM_PTS - 1) // BK_SIM_PTS)
    sel = pts[::step]
    if sel[-1] != pts[-1]:
        sel.append(pts[-1])
    xz = [[round(bk_xz(p[0], p[1])[0], 1), round(bk_xz(p[0], p[1])[1], 1)] for p in sel[:BK_SIM_PTS]]
    who_ = d.get("who") if d.get("who") in ("person", "mover") else "auto"
    try:
        r = sim_control({"action": "bkarte", "do": "tour", "pts": xz, "name": name[:120], "who": who_, "src": "mw"}) or {}
    except Exception as e:
        return False, str(e)[:80], {}
    if not r.get("ok"):
        err = str(r.get("error") or "")
        if not err or "unknown" in err.lower():
            err = "The simulator does not know this yet - it needs a newer version."
        elif "Bergtal" in err:
            err = "The simulator is not in the Bergtal."
        return False, err[:160], {}
    return True, "", {"tour": r.get("tour")}


# ---- web: package files, state, live, height, suggestions -----------------------------------------------------------------------
_smalltv_routes_639zzzzzt = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzzzzt: /karte/berg/<key>/…, /api/karte/berg (550 calls it once)
    _smalltv_routes_639zzzzzt(app, reply, body)
    from flask import Response, request, g

    def nope(code=404):
        return Response(b"", status=code, mimetype="text/plain")

    @app.route("/karte/berg/<key>/<path:fp>")
    def bk_file_(key, fp):
        if key != bk_key() or not bk_installed() or not BK_STATIC.fullmatch(fp):
            return nope()
        base = os.path.realpath(bk_dir())
        p_ = os.path.realpath(os.path.join(base, *fp.split("/")))
        h_ = {"Cache-Control": "public, max-age=2592000, immutable"}
        ext = os.path.splitext(p_)[1]
        mt = {".json": "application/json", ".png": "image/png", ".pbf": "application/x-protobuf", ".js": "application/javascript",
              ".css": "text/css", ".txt": "text/plain; charset=utf-8"}.get(ext)
        if not p_.startswith(base + os.sep) or not mt:
            return nope()
        if not os.path.isfile(p_):
            if ext == ".pbf":                               # a font range that is not there: an empty answer (MapLibre leaves it out)
                return Response(b"", mimetype=mt, headers=h_)
            return nope()
        src = p_
        if ext in (".js", ".css", ".json") and os.path.isfile(p_ + ".gz") and "gzip" in (request.headers.get("Accept-Encoding") or "").lower():
            src = p_ + ".gz"; h_["Content-Encoding"] = "gzip"; h_["Vary"] = "Accept-Encoding"
        with open(src, "rb") as fh:
            return Response(fh.read(), mimetype=mt, headers=h_)

    @app.route("/api/karte/berg", methods=["GET", "POST"])
    def bk_api_():
        if request.method == "GET":
            on = bk_installed()
            if request.args.get("live"):
                gh = bk_geheim(bk_found()) if on else None
                return reply({"ok": True, "on": on, "sim": kq_sim_ok(), "live": bk_live() if on else None, "geheim": gh,
                              "found": sum(1 for f in (gh["features"] if gh else []) if f["properties"]["t"] == "geheim"),
                              "secrets": bk_secret_total()})
            return reply(dict(bk_state(), ok=True))
        d = body()
        lang = norm_lang(d.get("lang") or request.args.get("lang") or CFG.get("lang"))
        if kq_role() != "admin":
            return reply({"ok": False, "error": tr("not allowed for your user", lang)}, 403)
        a = str(d.get("action") or "")
        res = {}
        if a == "install":
            ok, err = bk_download()
        elif a == "cancel":
            BK_DL["stop"] = bool(BK_DL["running"]); ok, err = True, ""
        elif a == "delete":
            ok, err = bk_delete()
        elif a in ("tour_sim", "tour_stop"):
            ok, err, res = bk_tour_sim(d, tausch_who(g))
        else:
            ok, err = False, "unknown action"
        return reply(dict(bk_state(), ok=ok, error=tr(err, lang) if err else "", **res), 200 if ok else 400)

    @app.route("/api/karte/berg/hoehe")
    def bk_hoehe_():
        try:
            la, lo = float(str(request.args.get("lat"))[:30]), float(str(request.args.get("lon"))[:30])
        except (TypeError, ValueError):
            return reply({"ok": True, "ele": None})
        if not bk_in(la, lo):
            return reply({"ok": True, "ele": None})
        x, z = bk_xz(la, lo)
        return reply({"ok": True, "ele": bk_height(la, lo), "x": round(x), "z": round(z)})

    @app.route("/api/karte/berg/vorschlaege")
    def bk_vor_():
        if not bk_installed():
            return reply({"ok": True, "tours": []})
        try:
            return reply({"ok": True, "tours": bk_vorschlaege()})
        except (OSError, ValueError, KeyError, TypeError) as e:
            return reply({"ok": False, "error": str(e)[:80], "tours": []}, 500)


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_BK = {
    "Switzerland": ("Schweiz", "Suisse", "Svizzera", "Svizra"),
    "Bergtal": ("Bergtal", "Bergtal", "Bergtal", "Bergtal"),
    "Which map": ("Welche Karte", "Quelle carte", "Quale mappa", "Tge charta"),
    "Bergtal map": ("Bergtal-Karte", "Carte du Bergtal", "Mappa del Bergtal", "Charta dal Bergtal"),
    "The Bergtal map is not installed.": ("Die Bergtal-Karte ist nicht installiert.", "La carte du Bergtal n’est pas installée.",
                                          "La mappa del Bergtal non è installata.", "La charta dal Bergtal n’è betg installada."),
    "The map of the valley in the simulator: relief, contour lines, 3D, all places, trails and tours. Small (about %s MB), afterwards without internet.": (
        "Die Karte des Tals im Simulator: Relief, Höhenlinien, 3D, alle Orte, Wanderwege und Touren. Klein (etwa %s MB), danach ohne Internet.",
        "La carte de la vallée du simulateur : relief, courbes de niveau, 3D, tous les lieux, sentiers et randonnées. Petite (environ %s Mo), ensuite sans Internet.",
        "La mappa della valle del simulatore: rilievo, curve di livello, 3D, tutti i luoghi, sentieri ed escursioni. Piccola (circa %s MB), poi senza Internet.",
        "La charta da la val dal simulatur: relief, lingias d’autezza, 3D, tut ils lieus, sendas e turas. Pitschna (var %s MB), lura senza internet."),
    "The administrator can install it.": ("Der Admin kann sie installieren.", "L’administrateur peut l’installer.", "L’amministratore può installarla.",
                                          "L’administratur la po installar."),
    "Download the Bergtal map": ("Bergtal-Karte herunterladen", "Télécharger la carte du Bergtal", "Scarica la mappa del Bergtal", "Telechargiar la charta dal Bergtal"),
    "Load the Bergtal map now? %s MB from GitHub (fixed checksum).": ("Bergtal-Karte jetzt laden? %s MB von GitHub (feste Prüfsumme).",
                                                                     "Charger maintenant la carte du Bergtal ? %s Mo depuis GitHub (somme de contrôle fixe).",
                                                                     "Caricare adesso la mappa del Bergtal? %s MB da GitHub (somma di controllo fissa).",
                                                                     "Chargiar uss la charta dal Bergtal? %s MB da GitHub (summa da controlla fixa)."),
    "Remove the Bergtal map?": ("Bergtal-Karte entfernen?", "Supprimer la carte du Bergtal ?", "Rimuovere la mappa del Bergtal?", "Allontanar la charta dal Bergtal?"),
    "Search a place in the Bergtal …": ("Ort im Bergtal suchen …", "Chercher un lieu dans le Bergtal …", "Cerca un luogo nel Bergtal …", "Tschertgar in lieu en il Bergtal …"),
    "Bergtal – invented valley of MoveEye Sim": ("Bergtal – erfundenes Tal von MoveEye Sim", "Bergtal – vallée inventée de MoveEye Sim",
                                                "Bergtal – valle inventata di MoveEye Sim", "Bergtal – val inventada da MoveEye Sim"),
    "Own grid in metres from the centre of the valley – no real coordinates.": (
        "Eigenes Gitter in Metern ab der Mitte des Tals – keine echten Koordinaten.",
        "Grille propre en mètres depuis le centre de la vallée – pas de vraies coordonnées.",
        "Griglia propria in metri dal centro della valle – nessuna coordinata reale.",
        "Agen raster en meters dal center da la val – naginas coordinatas veras."),
    "E": ("O", "E", "E", "O"),
    "N": ("N", "N", "N", "N"),
    "Simulator not connected – secret places stay hidden.": ("Simulator nicht verbunden – geheime Orte bleiben verborgen.",
                                                            "Simulateur non connecté – les lieux secrets restent cachés.",
                                                            "Simulatore non collegato – i luoghi segreti restano nascosti.",
                                                            "Simulatur betg collià – ils lieus secrets restan zuppads."),
    "Simulator connected – not in the Bergtal right now.": ("Simulator verbunden – gerade nicht im Bergtal.", "Simulateur connecté – pas dans le Bergtal en ce moment.",
                                                           "Simulatore collegato – al momento non nel Bergtal.", "Simulatur collià – gist betg en il Bergtal."),
    "Live from the simulator": ("Live aus dem Simulator", "En direct du simulateur", "In diretta dal simulatore", "Live dal simulatur"),
    "detected": ("erkannt", "détectés", "rilevati", "renconuschids"),
    "secret places found": ("geheime Orte gefunden", "lieux secrets trouvés", "luoghi segreti trovati", "lieus secrets chattads"),
    "Figure": ("Figur", "Personnage", "Personaggio", "Figura"),
    "Mover": ("Mover", "Mover", "Mover", "Mover"),
    "Animal": ("Tier", "Animal", "Animale", "Animal"),
    "Person": ("Person", "Personne", "Persona", "Persuna"),
    "Tour in the simulator:": ("Tour im Simulator:", "Randonnée dans le simulateur :", "Escursione nel simulatore:", "Tura en il simulatur:"),
    "to go": ("noch", "restants", "mancanti", "anc"),
    "at the finish": ("am Ziel", "à l’arrivée", "all’arrivo", "a la finamira"),
    "stopped": ("angehalten", "arrêtée", "fermata", "fermada"),
    "Stop": ("Anhalten", "Arrêter", "Ferma", "Fermar"),
    "Walk the tour in the simulator": ("Tour im Sim nachlaufen", "Parcourir la randonnée dans le simulateur", "Percorri l’escursione nel simulatore",
                                       "Ir la tura en il simulatur"),
    "Sent to the simulator – the figure walks the tour.": ("An den Simulator geschickt – die Figur läuft die Tour ab.",
                                                           "Envoyé au simulateur – le personnage parcourt la randonnée.",
                                                           "Inviato al simulatore – il personaggio percorre l’escursione.",
                                                           "Tramess al simulatur – la figura va la tura."),
    "Sent to the simulator – the mover drives the tour.": ("An den Simulator geschickt – der Mover fährt die Tour ab.",
                                                           "Envoyé au simulateur – le mover parcourt la randonnée.",
                                                           "Inviato al simulatore – il mover percorre l’escursione.",
                                                           "Tramess al simulatur – il mover fa la tura."),
    "Connect the simulator and open the Bergtal first.": ("Zuerst den Simulator verbinden und das Bergtal öffnen.",
                                                          "Connecter d’abord le simulateur et ouvrir le Bergtal.",
                                                          "Prima collegare il simulatore e aprire il Bergtal.",
                                                          "L’emprim colliar il simulatur ed avrir il Bergtal."),
    "The simulator is not connected.": ("Der Simulator ist nicht verbunden.", "Le simulateur n’est pas connecté.", "Il simulatore non è collegato.",
                                        "Il simulatur n’è betg collià."),
    "The simulator is not in the Bergtal.": ("Der Simulator ist nicht im Bergtal.", "Le simulateur n’est pas dans le Bergtal.", "Il simulatore non è nel Bergtal.",
                                             "Il simulatur n’è betg en il Bergtal."),
    "The simulator does not know this yet - it needs a newer version.": (
        "Der Simulator kennt das noch nicht – er braucht eine neuere Version.", "Le simulateur ne connaît pas encore cela – il lui faut une version plus récente.",
        "Il simulatore non lo conosce ancora – serve una versione più recente.", "Il simulatur na enconuscha quai anc betg – el dovra ina versiun pli nova."),
    "This tour is not in the Bergtal.": ("Diese Tour liegt nicht im Bergtal.", "Cette randonnée n’est pas dans le Bergtal.", "Questa escursione non è nel Bergtal.",
                                         "Questa tura n’è betg en il Bergtal."),
    "package does not fit this MoveEye": ("Das Paket passt nicht zu diesem MoveEye", "Le paquet ne convient pas à ce MoveEye", "Il pacchetto non è adatto a questo MoveEye",
                                          "Il pachet na va betg cun quest MoveEye"),
    "package incomplete": ("Paket unvollständig", "Paquet incomplet", "Pacchetto incompleto", "Pachet incomplet"),
    "package has the wrong size": ("Paket hat die falsche Grösse", "Le paquet n’a pas la bonne taille", "Il pacchetto ha la dimensione sbagliata",
                                   "Il pachet ha la faussa grondezza"),
    "Suggestions": ("Vorschläge", "Suggestions", "Proposte", "Propostas"),
    "Tours on the trails of the valley – tap one.": ("Touren auf den Wanderwegen des Tals – eine antippen.", "Randonnées sur les sentiers de la vallée – en toucher une.",
                                                     "Escursioni sui sentieri della valle – toccarne una.", "Turas sin las sendas da la val – tutgar ina."),
    "Save as tour": ("Als Tour speichern", "Enregistrer comme randonnée", "Salva come escursione", "Memorisar sco tura"),
    "Show on the map": ("Auf der Karte zeigen", "Afficher sur la carte", "Mostra sulla mappa", "Mussar sin la charta"),
    "Back": ("Zurück", "Retour", "Indietro", "Enavos"),
    "Distance": ("Distanz", "Distance", "Distanza", "Distanza"),
    "Ascent": ("Aufstieg", "Montée", "Salita", "Ascensiun"),
    "Descent": ("Abstieg", "Descente", "Discesa", "Descensiun"),
    "Hiking time": ("Wanderzeit", "Temps de marche", "Tempo di percorrenza", "Temp da viandar"),
    "Lowest / highest": ("Tiefster / höchster Punkt", "Point le plus bas / haut", "Punto più basso / alto", "Punct il pli bass / aut"),
    "hiking trail": ("Wanderweg", "chemin de randonnée", "sentiero escursionistico", "senda da viandar"),
    "mountain trail": ("Bergweg", "chemin de montagne", "sentiero di montagna", "senda da muntogna"),
    "alpine trail": ("Alpinwanderweg", "chemin de randonnée alpine", "sentiero alpino", "senda alpina"),
    "secret place (found)": ("geheimer Ort (gefunden)", "lieu secret (trouvé)", "luogo segreto (trovato)", "lieu secret (chattà)"),
    "Trails, places and heights come from the simulator.": ("Wege, Orte und Höhen stammen aus dem Simulator.", "Les sentiers, lieux et altitudes viennent du simulateur.",
                                                            "Sentieri, luoghi e altitudini vengono dal simulatore.", "Sendas, lieus ed autezzas vegnan dal simulatur."),
    "installed": ("installiert", "installée", "installata", "installada"),
    "Remove": ("Entfernen", "Supprimer", "Rimuovi", "Allontanar"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "checking and unpacking …": ("prüfen und auspacken …", "vérification et décompression …", "verifica e decompressione …", "controllar e spachetar …"),
    "comes with an update": ("kommt mit einem Update", "arrive avec une mise à jour", "arriva con un aggiornamento", "vegn cun in update"),
    "not enough free space on the memory card": ("zu wenig freier Platz auf der Speicherkarte", "pas assez d’espace libre sur la carte mémoire",
                                                 "spazio libero insufficiente sulla scheda di memoria", "memia pauc spazi liber sin la carta da memoria"),
    "Sources and licences": ("Quellen und Lizenzen", "Sources et licences", "Fonti e licenze", "Funtaunas e licenzas"),
    "Nothing found": ("Nichts gefunden", "Rien trouvé", "Nessun risultato", "Chattà nagut"),
    "Tap on the map: name, grid and height of the point.": ("Auf die Karte tippen: Name, Gitter und Höhe des Punkts.",
                                                           "Toucher la carte : nom, grille et altitude du point.",
                                                           "Toccare la mappa: nome, griglia e altitudine del punto.",
                                                           "Tutgar la charta: num, raster ed autezza dal punct."),
    "No connection to MoveEye.": ("Keine Verbindung zu MoveEye.", "Pas de connexion à MoveEye.", "Nessuna connessione con MoveEye.", "Nagina colliaziun cun MoveEye."),
}
_BK_EN = {k: k for k in _HX_BK}
_BK_EN.update({"E": "E", "N": "N"})
for _k, _v in _HX_BK.items():
    if len(_k) > 2:                                       # «E» / «N» stay in the page only (no key for tr())
        DE.setdefault(_k, _v[0])
        for _i, _L in enumerate(("fr", "it", "rm")):
            TRX[_L].setdefault(_k, _v[_i + 1])


def bk_tx():
    out = {"en": dict(_BK_EN)}
    for i_, L_ in enumerate(("de", "fr", "it", "rm")):
        out[L_] = {k: v[i_] for k, v in _HX_BK.items()}
    return out


# ---- the browser part --------------------------------------------------------------------------------------------------------------
BK_CSS = """
.bk-welt{display:flex;margin:4px 0 8px;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.3);max-width:420px}
.bk-welt button{all:unset;flex:1;cursor:pointer;min-height:44px;padding:0 12px;font:600 15px/44px system-ui,sans-serif;text-align:center;background:var(--panel,#222);color:var(--txt,#eee)}
.bk-welt button+button{border-left:1px solid var(--line,#444)}.bk-welt button.on{background:#2f7cf6;color:#fff}
.bk-welt button:focus-visible{outline:2px solid #2f7cf6;outline-offset:-2px}
body.bk-berg #eo{display:none!important}
#bk-res{display:flex;flex-direction:column;gap:4px;margin:4px 0}#bk-res .kq-hit{text-align:left;display:block;width:100%;min-height:40px}
.bk-live{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;margin:8px 2px;font-size:14px}.bk-live .mut{font-size:13px}
.bk-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}.bk-row button,.bk-row a.btn{min-height:44px}
.bk-leg i.bk-dot{display:inline-block;width:11px;height:11px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.35);background:var(--c)}
.bk-grid{font-size:12px;color:var(--mut,#8a93a0);margin:2px}
.bk-vor{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}.bk-vor h2{font-size:18px;margin:0 0 6px}
.bk-inst{margin-top:10px;padding:10px 12px;border:1px solid var(--line,#334);border-radius:12px}.bk-inst progress{flex:1 1 120px}
.bk-warn{color:var(--warn,#e9a23b);font-weight:600}
"""
BK_HTML = """
    <div id="bk-res"></div>
    <div class="bk-live" id="bk-live" hidden></div>
    <div class="bk-row" id="bk-btns" hidden></div>
    <section class="bk-vor" id="bk-vor" hidden><h2>💡 <span id="bk-vor-h"></span></h2><div class="kt-note" id="bk-vor-n"></div><div id="bk-vor-l"></div><div id="bk-vor-d" hidden></div></section>
    <div id="bk-adm"></div>
"""
BK_JS = r"""
// 639zzzzzt: «⛰ Bergtal» on /karte - its own MapLibre map from the package (/karte/berg/<key>/…), the secrets only from /api/karte/berg
(function () {
  const BK = window.BK = /*BKSTATE*/{}, TX = /*BKTX*/{};
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const T = BK.T = k => (TX[L()] || {})[k] || (TX.en || {})[k] || k;
  const $ = s => document.querySelector(s);
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const btn = (txt, cls, fn) => { const b = el("button", cls || "", txt); b.type = "button"; b.onclick = fn; return b; };
  const PRE = location.pathname.replace(/\/karte\/?$/, "");            // «/demo» on the host, else ""
  const ORG = location.origin + PRE, BASE = ORG + "/karte/berg/" + (BK.key || "0");
  const M = (BK.meta && BK.meta.mpd) || 111195.0802;
  const EMPTY = {type: "FeatureCollection", features: []};
  const MB = n => Math.max(1, Math.round((n || 0) / 1e5) / 10);
  const km = m => (m / 1000).toFixed(m < 10000 ? 2 : 1).replace(".", L() === "en" ? "." : ",") + " km";
  const dur = m => m >= 60 ? Math.floor(m / 60) + " h " + String(m % 60).padStart(2, "0") + " min" : m + " min";
  const grid = (lon, lat) => T("E") + " " + Math.round(lon * M) + " m · " + T("N") + " " + Math.round(lat * M) + " m";
  const dark = () => !(document.body && document.body.classList.contains("light"));
  const post = d => fetch(PRE + "/api/karte/berg", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))})
    .then(r => r.json()).catch(() => ({ok: false, error: T("No connection to MoveEye.")}));
  const P = new URLSearchParams(location.search);
  let mode = P.get("welt");
  if (mode !== "berg" && mode !== "ch") { try { mode = localStorage.getItem("mw-kq-welt"); } catch (e) {} }
  if (mode !== "berg" && mode !== "ch") mode = (window.KQ && KQ.on) || !BK.on ? "ch" : "berg";
  if (mode === "berg" && !BK.on && !BK.admin) mode = "ch";
  BK.mode = mode;
  // ---- the switch «Schweiz | Bergtal» (above the map, both worlds) ----
  BK.switchUI = () => {
    if (!(BK.on || BK.admin) || $("#bk-welt")) return;
    const w = el("div", "bk-welt"); w.id = "bk-welt"; w.setAttribute("role", "group"); w.setAttribute("aria-label", T("Which map"));
    [["ch", "🗺 ", "Switzerland"], ["berg", "⛰ ", "Bergtal"]].forEach(([v, ic, n]) => {
      const b = btn(ic + T(n), "", () => { if (v === BK.mode) return; try { localStorage.setItem("mw-kq-welt", v); } catch (e) {} location.href = ORG + "/karte?welt=" + v; });
      b.dataset.v = v; b.classList.toggle("on", v === BK.mode); b.setAttribute("aria-pressed", v === BK.mode ? "true" : "false"); w.appendChild(b); });
    const back = $(".kq-back"); if (back) back.after(w); else $("main").prepend(w);
  };
  BK.take = () => { BK.switchUI(); if (BK.mode !== "berg") return false; page(); return true; };
  // ---- tours (639zzx): the list shows the tours of its world, a Bergtal tour can be walked in the simulator ----
  window.bkTourShow = t => BK.mode === "berg" ? t.welt === "berg" : t.welt !== "berg";
  window.bkTourRow = (row, t) => { if (BK.mode !== "berg" || t.welt !== "berg" || !BK.admin) return; row.appendChild(simBtn({action: "tour_sim", id: t.id})); };
  function simBtn(d) {
    const b = btn("🎮 " + T("Walk the tour in the simulator"), "sec bk-simtour", () => {
      if (!BK.sim) { note(T("Connect the simulator and open the Bergtal first.")); return; }
      b.disabled = true; post(d).then(r => { b.disabled = false;
        note(r.ok ? "🎮 " + T(r.tour && r.tour.who === "mover" ? "Sent to the simulator – the mover drives the tour." : "Sent to the simulator – the figure walks the tour.") : "⚠ " + (r.error || "?")); }); });
    return b;
  }
  const note = t => { const m = $("#kq-msg"); if (m) { m.textContent = t; m.scrollIntoView({block: "nearest"}); } if (window.toast) try { toast(t); } catch (e) {} };
  // ---- the administrator: load / remove ----
  function installBox(into) {
    const w = el("div", "bk-inst"); let tm = 0; into.appendChild(w);
    const get = () => fetch(PRE + "/api/karte/berg", {cache: "no-store"}).then(r => r.json());
    const act = a => post({action: a}).then(S => { paint(S); return S; });
    function paint(S) {
      clearTimeout(tm); w.textContent = ""; if (!S) return; const D = S.dl || {};
      w.appendChild(el("b", "", "⛰ " + T("Bergtal map")));
      const row = el("div", "bk-row");
      if (D.running) {
        const p = el("progress"); p.max = D.total || 1; p.value = D.phase === "unpack" ? (D.total || 1) : (D.got || 0);
        row.append(el("span", "", D.phase === "unpack" ? "⏳ " + T("checking and unpacking …") : "⏳ " + MB(D.got) + " / " + MB(D.total) + " MB"), p, btn(T("Cancel"), "sec", () => act("cancel")));
        tm = setTimeout(() => get().then(S2 => { if (S2.on && !BK.on) location.reload(); else paint(S2); }).catch(() => {}), 1200);
      } else if (S.on) {
        row.appendChild(el("span", "", "✓ " + T("installed") + " · " + MB(S.size) + " MB · Sim " + ((S.meta || {}).sim || S.sim_ver || "?")));
        const rm = btn("🗑 " + T("Remove"), "sec", () => { rm.replaceWith(el("b", "", T("Remove the Bergtal map?")), btn("✓", "red", () => act("delete").then(() => location.reload())), btn("✕", "sec", () => paint(S))); }); rm.id = "bk-del";
        row.appendChild(rm);
      } else if (!S.pinned) row.appendChild(el("span", "mut", T("comes with an update")));
      else {
        const ib = btn("⬇ " + T("Download the Bergtal map") + " (" + MB(S.size) + " MB)", "", () => { if (ib.dataset.sure) act("install"); else { ib.dataset.sure = "1"; ib.textContent = T("Load the Bergtal map now? %s MB from GitHub (fixed checksum).").replace("%s", MB(S.size)); } });
        ib.id = "bk-install"; ib.disabled = !S.space_ok; row.appendChild(ib);
        if (!S.space_ok) row.appendChild(el("span", "bk-warn", "⚠ " + T("not enough free space on the memory card")));
      }
      w.appendChild(row);
      const e = S.error || (!D.running && D.msg ? T(D.msg) : ""); if (e) w.appendChild(el("div", "bk-warn", "⚠ " + e));
    }
    get().then(paint).catch(() => {});
  }
  // ---- symbols like the Swiss map (drawn, no sprite file) ----
  function icon(kind) {
    const S = 40, c = document.createElement("canvas"); c.width = c.height = S; const g = c.getContext("2d"), mid = S / 2;
    const ink = dark() ? "#e6dccb" : "#2d2a26", blue = dark() ? "#6ea8ff" : "#2b63d0", red = "#d83a22", halo = dark() ? "rgba(22,25,28,.85)" : "rgba(255,255,255,.9)";
    g.lineJoin = "round"; g.lineCap = "round";
    const ring = (r) => { g.beginPath(); g.arc(mid, mid, r, 0, 7); g.fillStyle = halo; g.fill(); };
    const tri = (col) => { g.beginPath(); g.moveTo(mid, 9); g.lineTo(31, 29); g.lineTo(9, 29); g.closePath(); g.fillStyle = col; g.fill(); g.lineWidth = 2; g.strokeStyle = halo; g.stroke(); };
    const house = (col, cross) => { ring(15); g.beginPath(); g.moveTo(mid, 8); g.lineTo(31, 18); g.lineTo(28, 18); g.lineTo(28, 31); g.lineTo(12, 31); g.lineTo(12, 18); g.lineTo(9, 18); g.closePath();
      g.fillStyle = col; g.fill(); if (cross) { g.strokeStyle = "#fff"; g.lineWidth = 2.4; g.beginPath(); g.moveTo(mid, 19); g.lineTo(mid, 29); g.moveTo(15.5, 23); g.lineTo(24.5, 23); g.stroke(); } };
    switch (kind) {
      case "gipfel": tri(ink); break;
      case "aussicht": ring(13); g.strokeStyle = ink; g.lineWidth = 2.2; g.beginPath(); g.arc(mid, mid, 6, 0, 7); g.stroke();
        for (let a = 0; a < 8; a++) { const r = a * Math.PI / 4; g.beginPath(); g.moveTo(mid + Math.cos(r) * 8.5, mid + Math.sin(r) * 8.5); g.lineTo(mid + Math.cos(r) * 12, mid + Math.sin(r) * 12); g.stroke(); } break;
      case "pass": ring(12); g.strokeStyle = ink; g.lineWidth = 3; g.beginPath(); g.arc(8, mid, 9, -0.9, 0.9); g.stroke(); g.beginPath(); g.arc(32, mid, 9, Math.PI - 0.9, Math.PI + 0.9); g.stroke(); break;
      case "huette": house(red); break;
      case "hospiz": house(ink, true); break;
      case "biwak": ring(13); g.beginPath(); g.moveTo(mid, 9); g.lineTo(30, 29); g.lineTo(10, 29); g.closePath(); g.fillStyle = red; g.fill(); g.fillStyle = "#fff"; g.fillRect(17, 22, 6, 7); break;
      case "kapelle": ring(13); g.fillStyle = ink; g.beginPath(); g.arc(mid, 25, 6, 0, 7); g.fill(); g.strokeStyle = ink; g.lineWidth = 2.6; g.beginPath(); g.moveTo(mid, 7); g.lineTo(mid, 20); g.moveTo(15, 12); g.lineTo(25, 12); g.stroke(); break;
      case "bunker": ring(12); g.fillStyle = ink; g.fillRect(12, 12, 16, 16); g.fillStyle = halo; g.fillRect(17, 17, 6, 6); break;
      case "ruine": ring(12); g.strokeStyle = ink; g.lineWidth = 2.4; g.setLineDash([4, 3]); g.strokeRect(12, 12, 16, 16); g.setLineDash([]); break;
      case "seilbahn": ring(13); g.strokeStyle = ink; g.lineWidth = 2; g.beginPath(); g.moveTo(7, 28); g.lineTo(33, 12); g.stroke(); g.fillStyle = ink; [[12, 25], [20, 20], [28, 15]].forEach(([x, y]) => { g.beginPath(); g.arc(x, y, 2.6, 0, 7); g.fill(); }); break;
      case "parkplatz": g.fillStyle = "#2b63d0"; g.fillRect(9, 9, 22, 22); g.fillStyle = "#fff"; g.font = "bold 18px system-ui,sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("P", mid, mid + 1); break;
      case "bruecke": ring(12); g.strokeStyle = ink; g.lineWidth = 2.6; g.beginPath(); g.moveTo(9, 15); g.lineTo(31, 15); g.moveTo(9, 25); g.lineTo(31, 25); g.stroke(); break;
      case "wasserfall": ring(12); g.strokeStyle = blue; g.lineWidth = 2.6; g.beginPath(); g.moveTo(12, 10); g.lineTo(20, 16); g.lineTo(12, 22); g.lineTo(20, 28); g.moveTo(22, 10); g.lineTo(30, 16); g.lineTo(22, 22); g.lineTo(30, 28); g.stroke(); break;
      case "gletscher": ring(12); g.strokeStyle = blue; g.lineWidth = 2.4; for (let a = 0; a < 3; a++) { const r = a * Math.PI / 3; g.beginPath(); g.moveTo(mid + Math.cos(r) * 10, mid + Math.sin(r) * 10); g.lineTo(mid - Math.cos(r) * 10, mid - Math.sin(r) * 10); g.stroke(); } break;
      case "see": case "moor": ring(11); g.strokeStyle = blue; g.lineWidth = 2.4; [15, 22].forEach(y => { g.beginPath(); g.moveTo(11, y); g.quadraticCurveTo(15.5, y - 4, mid, y); g.quadraticCurveTo(24.5, y + 4, 29, y); g.stroke(); }); break;
      case "wald": ring(11); g.fillStyle = dark() ? "#5f9b6a" : "#3f7d3a"; g.beginPath(); g.arc(mid, 16, 8, 0, 7); g.fill(); g.fillRect(18.5, 20, 3, 10); break;
      case "schlafplatz": ring(12); g.beginPath(); g.moveTo(mid, 10); g.lineTo(30, 29); g.lineTo(10, 29); g.closePath(); g.fillStyle = "#2f9e44"; g.fill(); g.fillStyle = "#fff"; g.beginPath(); g.moveTo(mid, 18); g.lineTo(24, 29); g.lineTo(16, 29); g.closePath(); g.fill(); break;
      case "grat": case "klettersteig": ring(11); g.strokeStyle = ink; g.lineWidth = 2.4; g.beginPath(); g.moveTo(8, 26); g.lineTo(16, 14); g.lineTo(22, 22); g.lineTo(32, 10); g.stroke(); break;
      case "hoehle": ring(11); g.fillStyle = ink; g.beginPath(); g.arc(mid, 26, 9, Math.PI, 0); g.fill(); break;
      case "geheim": case "schatz": g.fillStyle = dark() ? "#e08ad0" : "#b0479a"; g.beginPath(); for (let i = 0; i < 10; i++) { const r = i % 2 ? 6 : 14, a = -Math.PI / 2 + i * Math.PI / 5; g.lineTo(mid + Math.cos(a) * r, mid + Math.sin(a) * r); } g.closePath(); g.fill(); g.lineWidth = 2; g.strokeStyle = halo; g.stroke(); break;
      default: ring(8); g.fillStyle = ink; g.beginPath(); g.arc(mid, mid, 4.5, 0, 7); g.fill();
    }
    return g.getImageData(0, 0, S, S);
  }
  // ---- the map ----
  let map = null;
  const lib = () => window.maplibregl ? Promise.resolve(window.maplibregl) : new Promise((ok, no) => {
    const c = document.createElement("link"); c.rel = "stylesheet"; c.href = BASE + "/web/maplibre-gl.css"; document.head.appendChild(c);
    const s = document.createElement("script"); s.src = BASE + "/web/maplibre-gl.js"; s.onload = () => ok(window.maplibregl); s.onerror = () => no(new Error("maplibre")); document.head.appendChild(s); });
  const style = () => fetch(BASE + (dark() ? "/stil_dunkel.json" : "/stil.json")).then(r => r.text()).then(t => {
    const s = JSON.parse(t.split("{B}").join(BASE)); s.sources.land.coordinates = BK.meta.landc;
    return s; });
  const D3 = {source: "dem", exaggeration: 1.2};                       // the same source as the relief (a copy stayed empty in WebGL tests)
  function set3d(v, quick) {
    BK.d3 = v; try { localStorage.setItem("mw-bk-3d", v ? "1" : "0"); } catch (e) {}
    document.querySelectorAll(".bk-3d button").forEach(b => { const on = (b.dataset.v === "3d") === v; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on ? "true" : "false"); });
    if (!map || !BK.ready) return;                                      // before «load»: the load handler does it (isStyleLoaded()
                                                                        // is false while 3D tiles stream in - then 2D did nothing)
    if (v) { map.setTerrain(D3); map.dragRotate.enable(); map.touchZoomRotate.enableRotation(); map.touchPitch.enable(); map.keyboard.enableRotation();
      try { map.setSky({"sky-color": dark() ? "#1b2a40" : "#9cc7ef", "horizon-color": dark() ? "#3a4a60" : "#eef4fa", "fog-color": dark() ? "#2a3340" : "#eef2f5", "sky-horizon-blend": 0.5, "horizon-fog-blend": 0.8, "fog-ground-blend": 0.25}); } catch (e) {}
      map.easeTo({pitch: 58, bearing: map.getBearing() || -25, zoom: Math.min(Math.max(map.getZoom(), 15.2), 15.2), duration: quick ? 0 : 700});
      // MapLibre takes the height under the centre when the terrain is switched on - before its tiles are there (0 m: the
      // camera would stand inside the mountain, empty picture, measured). Once everything is loaded: a tiny move = new height.
      // (a timer, not «idle»: a big canvas with software WebGL never gets idle - measured)
      clearInterval(BK.nudgeT); let n = 0;
      const nudge = () => { clearInterval(BK.nudgeT);                 // after the tilt (a jumpTo would stop it)
        BK.nudgeT = setInterval(() => { if (!BK.d3 || !map.getTerrain() || ++n > 120) { clearInterval(BK.nudgeT); return; }
          let el = 0; try { el = map.queryTerrainElevation(map.getCenter()) || 0; } catch (e) {}     // throws while the terrain starts
          if (el > 0 && n > 2) { clearInterval(BK.nudgeT); return; }
          const c = map.getCenter(); map.jumpTo({center: [c.lng + (n % 2 ? 2e-5 : -2e-5), c.lat]}); }, 1000); };   // ±2 m
      if (quick) nudge(); else map.once("moveend", nudge); }
    else { map.setTerrain(null); map.dragRotate.disable(); map.touchZoomRotate.disableRotation(); map.touchPitch.disable(); map.keyboard.disableRotation(); map.easeTo({pitch: 0, bearing: 0, duration: quick ? 0 : 500}); }
  }
  function addLive() {
    if (!map || map.getSource("bk-live")) return;
    map.addSource("bk-live", {type: "geojson", data: EMPTY});
    map.addLayer({id: "bk-live-cone", type: "fill", source: "bk-live", filter: ["==", ["get", "k"], "cone"], paint: {"fill-color": "#2f7cf6", "fill-opacity": 0.2}});
    map.addLayer({id: "bk-live-seen", type: "circle", source: "bk-live", filter: ["==", ["get", "k"], "seen"],
      paint: {"circle-radius": 6, "circle-color": ["case", ["==", ["get", "w"], "p"], "#e8590c", "#2f9e44"], "circle-stroke-color": "#fff", "circle-stroke-width": 2}});
    map.addLayer({id: "bk-live-pt", type: "circle", source: "bk-live", filter: ["==", ["get", "k"], "pt"],
      paint: {"circle-radius": 7.5, "circle-color": ["get", "c"], "circle-stroke-color": "#fff", "circle-stroke-width": 3}});
    map.addLayer({id: "bk-live-txt", type: "symbol", source: "bk-live", filter: ["==", ["get", "k"], "pt"],
      layout: {"text-field": ["get", "n"], "text-font": ["Noto Sans Medium"], "text-size": 12, "text-offset": [0, 1.1], "text-anchor": "top"},
      paint: {"text-color": "#10243f", "text-halo-color": "#fff", "text-halo-width": 1.6}});
  }
  function applyGeheim() { const s = map && map.getSource("geheim"); if (s) s.setData(BK.geheim || EMPTY); }
  let liveTm = 0;
  function paintLive(j) {
    const box = $("#bk-live"), row = $("#bk-btns"); box.hidden = false; box.textContent = ""; row.textContent = ""; const F = [], lv = j.live;
    const pt = (o, n, c) => { if (o) F.push({type: "Feature", properties: {k: "pt", n: n, c: c}, geometry: {type: "Point", coordinates: o.ll}}); };
    if (lv && lv.me) { const o = lv.me, R = 70, a = (o.az || 0) * Math.PI / 180, h = ((o.fov || 66) / 2) * Math.PI / 180, ring = [o.ll];
      for (let i = 0; i <= 10; i++) { const b = a - h + 2 * h * i / 10; ring.push([(o.x + Math.sin(b) * R) / M, -(o.z - Math.cos(b) * R) / M]); }
      ring.push(o.ll); F.push({type: "Feature", properties: {k: "cone"}, geometry: {type: "Polygon", coordinates: [ring]}}); }
    if (lv) (lv.seen || []).forEach(s => F.push({type: "Feature", properties: {k: "seen", w: s.w}, geometry: {type: "Point", coordinates: s.ll}}));
    if (lv) { pt(lv.mover, T("Mover"), "#f2a33a"); pt(lv.fig, T("Figure"), "#e03131"); pt(lv.me, "MoveEye", "#2f7cf6"); }
    const s = map && map.getSource("bk-live"); if (s) s.setData({type: "FeatureCollection", features: F});
    const sec = j.secrets ? " · 🔒 " + (j.found || 0) + " / " + j.secrets + " " + T("secret places found") : "";
    if (!j.sim) box.appendChild(el("span", "mut", "🎮 " + T("Simulator not connected – secret places stay hidden.")));
    else if (!lv) box.appendChild(el("span", "mut", "🎮 " + T("Simulator connected – not in the Bergtal right now.") + sec));
    else { const n = (lv.seen || []).length; box.appendChild(el("span", "", "🟢 " + T("Live from the simulator") + (n ? " · " + n + " " + T("detected") : "") + sec)); }
    const fly = (o, n) => { if (o) row.appendChild(btn("📍 " + n, "sec", () => map.flyTo({center: o.ll, zoom: Math.max(map.getZoom(), 16)}))); };
    if (lv) { fly(lv.me, "MoveEye"); fly(lv.fig, T("Figure")); fly(lv.mover, T("Mover")); }
    const t = lv && lv.tour;
    if (t && t.name !== undefined) {
      const tx = "🥾 " + T("Tour in the simulator:") + " " + (t.name || "") + " – " + (t.done ? T(t.why === "finish" ? "at the finish" : "stopped") : km(t.left || 0) + " " + T("to go"));
      box.appendChild(el("span", "", tx));
      if (!t.done && BK.admin) row.appendChild(btn("■ " + T("Stop"), "sec", () => post({action: "tour_stop"})));
    }
    row.hidden = !row.childNodes.length;
  }
  function poll() {
    clearTimeout(liveTm); liveTm = setTimeout(poll, 1500); if (document.hidden) return;
    fetch(PRE + "/api/karte/berg?live=1", {cache: "no-store"}).then(r => r.json()).then(j => {
      BK.sim = !!j.sim; const g = JSON.stringify(j.geheim || EMPTY); if (g !== BK.gs) { BK.gs = g; BK.geheim = j.geheim; applyGeheim(); }
      paintLive(j); }).catch(() => {});
  }
  function legend() {
    const d = el("div", "kq-leg bk-leg");
    const sw = (c, k, dash) => { const i = el("span", "kq-li"), s = el("i", "kq-swatch" + (dash ? " kq-dash" : "")); s.style.setProperty("--c", c); i.append(s, T(k)); d.appendChild(i); };
    sw("#e3a800", "hiking trail"); sw("#d83a22", "mountain trail", 1); sw("#2b63d0", "alpine trail", 1);
    const dot = (c, k) => { const i = el("span", "kq-li"), s = el("i", "bk-dot"); s.style.setProperty("--c", c); i.append(s, k); d.appendChild(i); };
    dot("#2f7cf6", "MoveEye"); dot("#e03131", T("Figure")); dot("#2f9e44", T("Animal")); dot("#e8590c", T("Person")); dot(dark() ? "#e08ad0" : "#b0479a", T("secret place (found)"));
    d.appendChild(el("span", "kq-lnote", T("Trails, places and heights come from the simulator.") + " " + T("Own grid in metres from the centre of the valley – no real coordinates.")));
    return d;
  }
  async function info(ll, name) {
    const inf = $("#kq-info"); inf.textContent = (name ? name + " · " : "") + grid(ll[0], ll[1]);
    try { const j = await (await fetch(PRE + "/api/karte/berg/hoehe?lat=" + ll[1] + "&lon=" + ll[0], {cache: "no-store"})).json();
      if (j.ele != null) inf.textContent = (name ? name + " · " : "") + grid(ll[0], ll[1]) + " · " + Math.round(j.ele) + " m"; } catch (e) {}
  }
  function search(q, pick) {
    const box = $("#bk-res"); box.textContent = ""; const s = q.trim().toLowerCase(); if (s.length < 2) return;
    const hits = (BK.orte || []).filter(o => String(o[0]).toLowerCase().indexOf(s) >= 0).slice(0, 8);
    (((BK.geheim || EMPTY).features) || []).forEach(f => { if (f.properties.t === "geheim" && String(f.properties.name).toLowerCase().indexOf(s) >= 0) hits.push([f.properties.name, f.geometry.coordinates[0], f.geometry.coordinates[1], "geheim", f.properties.ele]); });
    if (!hits.length) { box.appendChild(el("div", "mut", T("Nothing found"))); return; }
    hits.forEach(o => { const b = el("button", "sec kq-hit"); b.type = "button"; b.append(el("b", "", o[0]), " ", el("span", "mut", (o[4] != null ? o[4] + " m · " : "") + grid(o[1], o[2])));
      b.onclick = () => { box.textContent = ""; pick(o); }; box.appendChild(b); });
  }
  // ---- suggestions (touren.json of the package, numbers from the heights of the package) ----
  let vorLine = null;
  function profile(P, s) {
    if (!P || P.length < 2) return null;
    const NS = "http://www.w3.org/2000/svg", sv = document.createElementNS(NS, "svg"); sv.setAttribute("viewBox", "0 0 600 180"); sv.setAttribute("class", "kt-prof"); sv.setAttribute("role", "img");
    let lo = Infinity, hi = -Infinity; P.forEach(p => { lo = Math.min(lo, p[1]); hi = Math.max(hi, p[1]); });
    const sp = Math.max(hi - lo, 20), dm = P[P.length - 1][0] || 1, X = d => 46 + d / dm * 544, Y = h => 150 - (h - lo) / sp * 130;
    const d = P.map(p => X(p[0]).toFixed(1) + "," + Y(p[1]).toFixed(1)).join(" ");
    const mk = (n, a) => { const e = document.createElementNS(NS, n); Object.keys(a).forEach(k => e.setAttribute(k, a[k])); sv.appendChild(e); return e; };
    mk("polygon", {points: "46,150 " + d + " 590,150", fill: "rgba(224,40,30,.22)"}); mk("polyline", {points: d, fill: "none", stroke: "#e0281e", "stroke-width": 2});
    const tx = (x, y, t, anc) => { const e = mk("text", {x: x, y: y, "font-size": 12, fill: "currentColor", "text-anchor": anc || "start"}); e.textContent = t; };
    tx(2, 24, Math.round(hi) + " m"); tx(2, 150, Math.round(lo) + " m"); tx(46, 172, "0"); tx(590, 172, km(dm), "end");
    return sv;
  }
  function nums(v) {
    const box = el("div", "kt-nums"), add = (k, x) => { const d = el("div"); d.append(el("small", "", T(k)), el("b", "", x)); box.appendChild(d); };
    add("Distance", km(v.m || 0)); if (v.ele) { add("Ascent", "↑ " + v.up + " m"); add("Descent", "↓ " + v.down + " m"); add("Lowest / highest", v.lo + " – " + v.hi + " m"); }
    if (v.min != null) add("Hiking time", "≈ " + dur(v.min)); return box;
  }
  function showLine(pts) {
    if (!map) return; const s = map.getSource("bk-vor"), data = {type: "FeatureCollection", features: pts && pts.length > 1 ? [{type: "Feature", properties: {}, geometry: {type: "LineString", coordinates: pts.map(p => [p[1], p[0]])}}] : []};
    if (s) s.setData(data); else { map.addSource("bk-vor", {type: "geojson", data: data});
      map.addLayer({id: "bk-vor-c", type: "line", source: "bk-vor", layout: {"line-join": "round", "line-cap": "round"}, paint: {"line-color": "#ffffff", "line-width": 7, "line-opacity": 0.85}}, map.getLayer("bk-orte") ? "bk-orte" : undefined);
      map.addLayer({id: "bk-vor-l", type: "line", source: "bk-vor", layout: {"line-join": "round", "line-cap": "round"}, paint: {"line-color": "#7048e8", "line-width": 4}}, map.getLayer("bk-orte") ? "bk-orte" : undefined); }
    if (pts && pts.length > 1) { let a = 90, b = -90, c = 180, d = -180; pts.forEach(p => { a = Math.min(a, p[0]); b = Math.max(b, p[0]); c = Math.min(c, p[1]); d = Math.max(d, p[1]); });
      map.fitBounds([[c, a], [d, b]], {padding: 40, maxZoom: 16.5, duration: 0}); }
  }
  async function vorschlaege() {
    const V = $("#bk-vor"); let j; try { j = await (await fetch(PRE + "/api/karte/berg/vorschlaege", {cache: "no-store"})).json(); } catch (e) { return; }
    if (!j.tours || !j.tours.length) return;
    V.hidden = false; $("#bk-vor-h").textContent = T("Suggestions"); $("#bk-vor-n").textContent = T("Tours on the trails of the valley – tap one.");
    const Ls = $("#bk-vor-l"), Dt = $("#bk-vor-d");
    const list = () => { Ls.hidden = false; Dt.hidden = true; Ls.textContent = ""; showLine(null);
      j.tours.forEach(v => { const b = el("button", "kt-li"); b.type = "button"; b.dataset.i = v.i; const sp = el("span");
        sp.append(el("b", "", v.name), el("small", "", [km(v.m || 0), v.ele ? "↑ " + v.up + " m  ↓ " + v.down + " m" : "", v.min != null ? "≈ " + dur(v.min) : ""].filter(Boolean).join(" · ")));
        b.append(el("span", "", "🥾"), sp, el("span", "", "›")); b.onclick = () => detail(v); Ls.appendChild(b); }); };
    const detail = v => { Ls.hidden = true; Dt.hidden = false; Dt.textContent = "";
      const back = btn("‹ " + T("Suggestions"), "sec", list); back.id = "bk-vor-back";
      Dt.append(back, el("div", "kt-title", v.name), el("div", "kt-note", v.stops.join(" → ")), nums(v));
      const pr = profile(v.profile, v); if (pr) Dt.appendChild(pr);
      const row = el("div", "bk-row");
      row.appendChild(btn("🗺 " + T("Show on the map"), "sec", () => { showLine(v.pts); $("#kq-map").scrollIntoView({behavior: "smooth", block: "center"}); }));
      const sv = btn("💾 " + T("Save as tour"), "sec", () => { sv.disabled = true;
        fetch(PRE + "/api/touren", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: "save", name: v.name, pts: v.pts, lang: L()})})
          .then(r => r.json()).then(r => { sv.disabled = false; if (!r.ok) { note("⚠ " + (r.error || "?")); return; } location.href = ORG + "/karte?welt=berg&tour=" + r.tour.id; }).catch(() => { sv.disabled = false; }); });
      sv.id = "bk-vor-save"; row.appendChild(sv);
      if (BK.admin) row.appendChild(simBtn({action: "tour_sim", vorschlag: v.i}));
      Dt.appendChild(row); showLine(v.pts); };
    list();
  }
  async function page() {
    document.body.classList.add("bk-berg"); document.title = "MoveEye – " + T("Bergtal map");
    if (BK.admin) installBox($("#bk-adm") || $("main"));
    if (!BK.on) { const n = $("#kq-none"); n.hidden = false; n.textContent = "";
      n.append(el("b", "", "⛰ " + T("The Bergtal map is not installed.")), el("div", "mut", T("The map of the valley in the simulator: relief, contour lines, 3D, all places, trails and tours. Small (about %s MB), afterwards without internet.").replace("%s", MB(BK.size))));
      if (!BK.admin) n.appendChild(el("div", "mut", T("The administrator can install it.")));
      else { const a = $("#bk-adm"); if (a) n.appendChild(a); }
      return; }
    $("#kq-wrap").hidden = false; $("#kq-btns").hidden = true;
    const q = $("#kq-q"); q.placeholder = T("Search a place in the Bergtal …");
    const lic = $("#kq-lic"); lic.href = BASE + "/LIZENZEN.txt"; lic.textContent = "ⓘ " + T("Sources and licences");
    const at = $("#kq-at"); at.className = "kq-attr"; at.textContent = T("Bergtal – invented valley of MoveEye Sim") + " " + (BK.meta.sim || ""); at.hidden = false;
    $("#kq-info").textContent = T("Tap on the map: name, grid and height of the point.");
    const lg = legend(); $("#kq-map").after(lg);
    let want3d = false; try { want3d = localStorage.getItem("mw-bk-3d") === "1"; } catch (e) {}
    const ml = await lib(), st = await style(), b = BK.meta.bounds, pd = 0.004;
    // never exactly on 0° / 0°: that is the corner of a tile at every zoom - MapLibre then finds no terrain under the centre
    // and puts the 3D camera inside the mountain (measured: elevation 0, empty picture; 4 m off was not enough, 11 m was)
    const c0 = [BK.meta.center[0] + 0.0006, BK.meta.center[1] - 0.0004];   // ~65 m east, ~45 m south of the centre of the valley
    map = BK.map = new ml.Map({container: "kq-c", style: st, center: c0, zoom: 14.2, minZoom: 12.5, maxZoom: 18.6, maxPitch: 78,
      maxBounds: [[b[0] - pd, b[1] - pd], [b[2] + pd, b[3] + pd]], attributionControl: false, fadeDuration: 0, dragRotate: false, pitchWithRotate: false,
      touchPitch: false, renderWorldCopies: false});
    try { map.touchZoomRotate.disableRotation(); map.keyboard.disableRotation(); } catch (e) {}
    window.KQMAP = map;
    map.addControl(new ml.NavigationControl({showCompass: true, visualizePitch: true}), "top-right");
    map.on("styleimagemissing", e => { if (String(e.id).startsWith("bk-") && !map.hasImage(e.id)) map.addImage(e.id, icon(e.id.slice(3)), {pixelRatio: 2}); });
    const sw = el("div", "kq-sw bk-3d"); sw.setAttribute("role", "group"); sw.setAttribute("aria-label", "2D / 3D");
    [["2d", "2D"], ["3d", "3D"]].forEach(([v, n]) => { const x = btn(n, "", e => { e.stopPropagation(); set3d(v === "3d"); }); x.dataset.v = v; x.id = "bk-" + v; sw.appendChild(x); });
    $("#kq-map").appendChild(sw); set3d(want3d, true);
    const mk = new ml.Marker({color: "#f0571a"});
    map.on("click", e => { if (window.KT && KT.busy) return;
      const f = map.queryRenderedFeatures(e.point, {layers: ["bk-orte", "bk-geheim"].filter(l => map.getLayer(l))})[0];
      const ll = f ? f.geometry.coordinates : [e.lngLat.lng, e.lngLat.lat]; mk.setLngLat(ll).addTo(map); info(ll, f ? f.properties.name : ""); });
    const pick = o => { map.flyTo({center: [o[1], o[2]], zoom: 16}); mk.setLngLat([o[1], o[2]]).addTo(map); info([o[1], o[2]], o[0]); };
    let tm = 0; q.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(() => search(q.value, pick), 150); });
    q.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); search(q.value, pick); } });
    $("#kq-go").onclick = () => search(q.value, pick);
    map.on("load", () => { BK.ready = true; addLive(); applyGeheim(); if (BK.d3) set3d(true, true); });
    // light / dark like the page: a new style, the own sources and layers (tours, live, suggestions) stay
    let lastDark = dark();
    new MutationObserver(() => { const d = dark(); if (d === lastDark) return; lastDark = d;
      style().then(ns => { map.setStyle(ns, {diff: false, transformStyle: (prev, next) => { if (!prev) return next;
        Object.keys(prev.sources || {}).forEach(k => { if (!(k in next.sources) || k === "geheim") next.sources[k] = prev.sources[k]; });
        const ids = new Set(next.layers.map(l => l.id)); (prev.layers || []).forEach(l => { if (!ids.has(l.id)) next.layers.push(l); });
        if (BK.d3) next.terrain = D3; return next; }}); }).catch(() => {}); }).observe(document.body, {attributes: true, attributeFilter: ["class"]});
    poll(); vorschlaege();
  }
})();
"""
_kq_page_639zzzzzt = kq_page
_BK_HOOK_A = '  document.title = "MoveEye – " + T("Map");\n  if (!K.on) {'
_BK_HOOK_B = '  document.title = "MoveEye – " + T("Map");\n  if (window.BK && BK.take()) return;\n  if (!K.on) {'
_BK_AT = '<div class="mut" id="kq-msg"></div>'


# wraps: kq_page
def kq_page():                                              # + 639zzzzzt: the switch «Schweiz / Bergtal» and the Bergtal map
    html = _kq_page_639zzzzzt()
    if "window.BK = " in html or html.count(_BK_HOOK_A) != 1 or html.count(_BK_AT) != 1 or "</head>" not in html:
        return html
    on = bk_installed()
    st = {"on": on, "admin": kq_role() == "admin", "sim": kq_sim_ok(), "key": bk_key(), "size": BK_FILE["size"], "pinned": bk_pinned(),
          "meta": bk_meta() if on else None, "orte": []}
    if on:
        try:
            st["orte"] = bk_orte()
        except (OSError, ValueError, KeyError, TypeError):
            pass
    js = (BK_JS.replace("/*BKSTATE*/{}", json.dumps(st, ensure_ascii=False).replace("</", "<\\/"), 1)
          .replace("/*BKTX*/{}", json.dumps(bk_tx(), ensure_ascii=False).replace("</", "<\\/"), 1))
    return (html.replace(_BK_HOOK_A, _BK_HOOK_B, 1).replace(_BK_AT, _BK_AT + BK_HTML, 1)
            .replace("</head>", "<style>" + BK_CSS + "</style><script>" + js + "</script></head>", 1))


# the tours (639zzx): drawing on the Bergtal map, the list per world, «Tour im Sim nachlaufen» in the detail of a tour
BK_KT_HOOKS = [("const hasMap = () => !!(window.KQ && KQ.on);",
                'const hasMap = () => !!(window.BK && BK.mode === "berg" ? BK.on : (window.KQ && KQ.on));'),
               ("S.tours = j.tours; S.me = j.me;", "S.tours = window.bkTourShow ? j.tours.filter(bkTourShow) : j.tours; S.me = j.me;"),
               ("    D.append(row, er);", "    if (window.bkTourRow) bkTourRow(row, t);\n    D.append(row, er);")]
BK_KT_HOOKED = {}
for _a, _b in BK_KT_HOOKS:
    BK_KT_HOOKED[_a] = KT_JS.count(_a) == 1
    if BK_KT_HOOKED[_a]:
        KT_JS = KT_JS.replace(_a, _b, 1)


# ---- the manual: one point after the tours (5 languages) --------------------------------------------------------------------------
_HELP_BK = {
    "de": ("⛰ Bergtal-Karte", "(Mehr → 🗺 Karte, Schalter «Schweiz / Bergtal»): die Karte des Tals im Simulator wie die Landeskarte – Relief, Höhenlinien, 3D (Knopf «3D», zwei Finger drehen und neigen), alle Orte mit Symbolen, Wanderwege gelb / rot / blau, Bäche und Seen. Eigenes Gitter in Metern ab der Mitte des Tals, keine echten Koordinaten. Geheime Orte erscheinen erst, wenn der verbundene Simulator sie als gefunden meldet. Ist der Simulator im Bergtal, zeigt die Karte live MoveEye mit Blickrichtung, die Figur, den Mover und was MoveEye erkennt. Touren bekommen die Höhen des Tals; «🎮 Tour im Sim nachlaufen» (Admin) lässt die Figur die Tour gehen. Vorschläge wie Hospiz → Pass → Biwak lassen sich als Tour speichern. Der Admin lädt das kleine Paket einmal von GitHub (feste Prüfsumme)."),
    "en": ("⛰ Bergtal map", "(More → 🗺 Map, switch “Switzerland / Bergtal”): the map of the valley in the simulator like the Swiss national map – relief, contour lines, 3D (button “3D”, two fingers turn and tilt), every place with its symbol, hiking trails yellow / red / blue, streams and lakes. Own grid in metres from the centre of the valley, no real coordinates. Secret places appear only when the connected simulator reports them as found. With the simulator in the Bergtal the map shows MoveEye with its view, the figure, the mover and what MoveEye detects, live. Tours get the heights of the valley; “🎮 Walk the tour in the simulator” (administrator) lets the figure walk it. Suggestions like Hospiz → Pass → Biwak can be saved as tours. The administrator loads the small package once from GitHub (fixed checksum)."),
    "fr": ("⛰ Carte du Bergtal", "(Plus → 🗺 Carte, bouton « Suisse / Bergtal ») : la carte de la vallée du simulateur comme la carte nationale – relief, courbes de niveau, 3D (bouton « 3D », deux doigts pour tourner et incliner), tous les lieux avec leur symbole, sentiers jaunes / rouges / bleus, ruisseaux et lacs. Grille propre en mètres depuis le centre de la vallée, pas de vraies coordonnées. Les lieux secrets n’apparaissent que lorsque le simulateur connecté les signale comme trouvés. Avec le simulateur dans le Bergtal, la carte montre en direct MoveEye avec sa direction de vue, le personnage, le mover et ce que MoveEye détecte. Les randonnées reçoivent les altitudes de la vallée ; « 🎮 Parcourir la randonnée dans le simulateur » (administrateur) la fait parcourir au personnage. Des suggestions comme Hospiz → Pass → Biwak peuvent être enregistrées. L’administrateur charge une fois le petit paquet depuis GitHub (somme de contrôle fixe)."),
    "it": ("⛰ Mappa del Bergtal", "(Altro → 🗺 Mappa, interruttore «Svizzera / Bergtal»): la mappa della valle del simulatore come la carta nazionale – rilievo, curve di livello, 3D (pulsante «3D», due dita per ruotare e inclinare), tutti i luoghi con il loro simbolo, sentieri gialli / rossi / blu, ruscelli e laghi. Griglia propria in metri dal centro della valle, nessuna coordinata reale. I luoghi segreti appaiono solo quando il simulatore collegato li segnala come trovati. Con il simulatore nel Bergtal la mappa mostra in diretta MoveEye con la direzione dello sguardo, il personaggio, il mover e ciò che MoveEye rileva. Le escursioni ricevono le altitudini della valle; «🎮 Percorri l’escursione nel simulatore» (amministratore) la fa percorrere al personaggio. Proposte come Hospiz → Pass → Biwak si possono salvare. L’amministratore carica una volta il piccolo pacchetto da GitHub (somma di controllo fissa)."),
    "rm": ("⛰ Charta dal Bergtal", "(Dapli → 🗺 Charta, cumutatur «Svizra / Bergtal»): la charta da la val dal simulatur sco la charta naziunala – relief, lingias d’autezza, 3D (buttun «3D», dus dets per volver e inclinar), tut ils lieus cun lur simbol, sendas melnas / cotschnas / blauas, auals e lais. Agen raster en meters dal center da la val, naginas coordinatas veras. Ils lieus secrets cumparan pir cura ch’il simulatur collià als annunzia sco chattads. Cun il simulatur en il Bergtal mussa la charta live MoveEye cun la direcziun da vista, la figura, il mover e quai che MoveEye renconuscha. Las turas survegnan las autezzas da la val; «🎮 Ir la tura en il simulatur» (administratur) lascha ir la figura. Propostas sco Hospiz → Pass → Biwak sa laschan memorisar. L’administratur chargia ina giada il pitschen pachet da GitHub (summa da controlla fixa)."),
}


def _help_bk(doc, lang):
    h_, x_ = _HELP_BK[lang]
    anchor = _HELP_KT[lang][0]
    if h_ in doc or anchor not in doc:
        return doc
    from html import escape as _e
    i = doc.find("</li>", doc.find(anchor))
    return doc if i < 0 else doc[:i + 5] + f"<li><b>{h_}</b> {_e(x_, quote=False)}</li>" + doc[i + 5:]


_hp_en_bk = HELP_PAGE.find('<div lang="en">')
if _hp_en_bk > 0:
    HELP_PAGE = _help_bk(HELP_PAGE[:_hp_en_bk], "de") + _help_bk(HELP_PAGE[_hp_en_bk:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_bk(HELP_X[_L], _L)


# ---- self-test (werkzeuge/bergkarte_test.py: install, secrets, tours, the page in the browser) ------------------------------------------
def bk_selftest():
    assert all(BK_KT_HOOKED.values()), [a for a, v in BK_KT_HOOKED.items() if not v]
    assert bk_in(0.005, -0.008) and not bk_in(46.8, 8.2) and not bk_in("x", 0) and not bk_in(0.0, 0.013)
    x, z = bk_xz(-0.003, 0.004)
    assert abs(x - 0.004 * BK_M) < 1e-6 and abs(z - 0.003 * BK_M) < 1e-6 and bk_ll(x, z) == [0.004, -0.003]
    assert abs(kt_dist((0.0, 0.0), (0.0, 1000.0 / BK_M)) - 1000.0) < 0.01, "kt_dist = metres in the frame of the valley"
    assert BK_STATIC.fullmatch("dem/15/16383/16384.png") and BK_STATIC.fullmatch("web/fonts/Noto Sans Medium/0-255.pbf")
    for bad in ("geheim.json", "hoehen.f32", "bergkarte.ok", "../x.json", "web/../geheim.json", "dem/1/2/3.json", "touren.json"):
        assert not BK_STATIC.fullmatch(bad), bad
    assert bk_geheim({"x"})["features"] == [] or bk_installed()
    old = SIM.get("bkarte"), CFG.get("sim_on"), SIM.get("ok")
    try:
        simvals_take({"bkarte": {"v": 1, "found": ["berg.a"], "me": [1, 2, 3, 66]}})
        CFG["sim_on"], SIM["ok"] = False, True
        assert bk_found() == set() and bk_live() is None, "no simulator: nothing found, nothing live"
        CFG["sim_on"] = True
        assert bk_found() == {"berg.a"} and bk_live()["me"]["fov"] == 66.0
        simvals_take({"x": 1})
        assert bk_found() == set()
    finally:
        SIM["bkarte"], CFG["sim_on"], SIM["ok"] = old
    pg = kq_page()
    assert pg.count("window.BK = ") == 1 and "/*BKSTATE*/" not in pg and "/*BKTX*/" not in pg and "BK.take()" in pg and 'id="bk-vor"' in pg
    assert "innerHTML" not in BK_JS and "confirm(" not in BK_JS and "https://" not in BK_JS and "prompt(" not in BK_JS
    assert all(len(v) == 4 and all(v) and "ß" not in v[0] for v in _HX_BK.values())
    for p_ in ("/api/karte/berg", "/api/karte/berg/hoehe", "/api/karte/berg/vorschlaege", "/karte/berg/0123456789ab/stil.json"):
        assert role_allows("kid", p_, "GET", {}) and role_allows("view", p_, "GET", {}), p_
    assert not role_allows("family", "/api/karte/berg", "POST", {"action": "install"}) and not role_allows("family", "/api/karte/berg", "POST", {"action": "tour_sim"})
    assert _HELP_BK["de"][0] in HELP_PAGE and _HELP_BK["en"][0] in HELP_PAGE
    return "Bergtal map: frame, files, secrets only from the simulator, hooks, rights, texts"


SELFTEST_EXTRA.append(("Bergtal map (639zzzzzt)", bk_selftest))
'''
zd_exec(BK_PY, "639zzzzzt_bergtal_karte.py")
