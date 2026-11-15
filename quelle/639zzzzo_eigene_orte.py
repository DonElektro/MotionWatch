#@ MoveEye – Teil 639zzzzo: «📌 Eigene Orte» auf der Offline-Karte (/karte) – Orte mit Symbolen setzen, ziehen, bearbeiten, löschen (nur Admin / files_admin), gespeichert als Datei im Digitalen Rucksack («🗺️ Karte/Meine Orte.geojson», Fotos daneben); jede GPX-, KML- und GeoJSON-Datei im Rucksack erscheint als eigene Ebene (ein / aus pro Gerät, Admin blendet für alle aus), Export GPX / KML, Höhe aus dem Höhenpaket. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (15.11.2026), Vorschau freigegeben (Koordinator, 15.11.2026):
#   * Auf /karte (639zzq) eine Symbolleiste «📌 Setzen» unten in der Karte: 🛖 Hütte, 🔥 Feuerstelle, 🚲 Velo, ⛺ Zelt, 🚗 Auto,
#     💧 Wasser, 🚻 WC, ⚠️ Gefahr, 📍 Punkt und «＋ Eigenes» (ein eigenes Emoji). Symbol wählen → auf die Karte tippen → der Ort
#     steht, die Karte zum Bearbeiten öffnet sich (Name, Symbol, Farbe, Notiz, Foto). Antippen = Karte des Orts (Foto, Name,
#     Farbe, Datum gesetzt, Notiz, Datei, Koordinaten, Höhe), «✥ Verschieben» (ziehen oder neuen Ort antippen), «🗑 Löschen» mit
#     Rückfrage in der Seite (kein confirm()). «🥾 Tour ab hier» startet eine Route der Touren (639zzx) an diesem Ort; während
#     eine Route gezeichnet wird, wird ein angetippter Ort ihr nächster Punkt.
#   * Rechte (Entscheid 15.11.2026): alle angemeldeten Benutzer sehen die Orte auf der Karte (auch ohne files_view), ändern
#     dürfen nur der Admin und files_admin. Fotos gibt es für Benutzer ohne Datei-Rechte nur über die Adresse der Karte
#     (/karte/orte/foto/<id>.jpg, nur Fotos, auf die ein sichtbarer Ort zeigt; die Vorschau des Rucksacks, nie die Original-Datei).
#   * WUNSCH DES BESITZERS: die Daten liegen IM DIGITALEN RUCKSACK. Eigene Orte = Datei «Meine Orte.geojson» im festen Ordner
#     «🗺️ Karte» (legt MoveEye selbst an), Fotos als normale Rucksack-Dateien im selben Ordner. Jede .gpx / .kml / .geojson in
#     «Für alle» (jeder Ordner, auch über die Netzwerk-Freigabe 639zzzn) ist eine Ebene für alle; private Dateien nur für ihren
#     Besitzer. Der Admin kann eine Ebene für alle ausblenden (Feld «eo_hide» in der Rucksack-Beschreibung der Datei).
#     Ein / aus pro Ebene und pro Symbol merkt sich jedes Gerät (localStorage). Linien der Dateien erscheinen gestrichelt.
#   * Lesen: GPX / KML mit kt_parse von 639zzx (need_route=False: Dateien nur mit Wegpunkten), GeoJSON mit eo_geojson (gleiche
#     Grenzen: KT_IMPORT_MAX, höchstens EO_MAX_FEAT Objekte, Text nur als Text). Jede Datei wird einmal gelesen und bis zur
#     nächsten Änderung behalten (Grösse, Zeit, Inode, Version).
#   * Schreiben (POST /api/karte/orte): hinzufügen / bearbeiten / verschieben / löschen / übernehmen (ein Ort einer anderen Ebene
#     in «Meine Orte») direkt in die Rucksack-Datei, unter der Sperre des Rucksacks; jeder Ort hat eine feste id und eine Nummer
#     «rev»: wer eine ältere Nummer schickt, bekommt «Inzwischen hat … diesen Ort geändert» (409) statt etwas zu überschreiben.
#     Die letzten 20 Fassungen bleiben (wie die Texte des Rucksacks: h/<id>/<Fassung>.txt, zählen im Platz) und lassen sich
#     zurückholen. Unbekannte Objekte und Felder der Datei bleiben stehen. Ist die Datei nicht lesbar (von Hand verändert),
#     wird nichts geschrieben.
#   * Höhe: aus dem Paket «Höhendaten Schweiz» (kh_height, 639zzx); ohne Paket steht keine Höhe.
#   * Rucksack-Seite: nur über die Haken window.tzCard / window.tzOpen (639zzc mit 639zzzzv), verkettet (Object.defineProperty:
#     wer später setzt, wird mitgerufen) – kein Eingriff in 639zzc. Abzeichen «🗺️ 3 Orte · 1 Linie» an jeder Datei mit Orten,
#     ein Blatt «Auf der Karte zeigen», ein Hinweis im Ordner «🗺️ Karte».
#   * Kein KMZ (Entscheid 15.11.2026).
# Selbsttest eo_selftest; Tests werkzeuge/orte_test.py.
# ----------------------------------------------------------------------------
EO_FOLDER = "🗺️ Karte"
EO_FILE = "Meine Orte.geojson"
EO_EXT = ("gpx", "kml", "geojson")
EO_MAX_PLACES = 500                                       # places in «Meine Orte»
EO_MAX_FEAT = 2000                                        # objects read from one GeoJSON file
EO_MAX_PTS = 500                                          # places shown of one file (markers on a phone)
EO_MAX_LAYERS = 40
EO_LINE_PTS = 1500                                        # points of one line on the map
EO_LINES_MAX = 50                                         # lines of one file
EO_NOTE_MAX = 1000
EO_SYMS = (("hut", "🛖", "Hut"), ("fire", "🔥", "Fireplace"), ("bike", "🚲", "Bike"), ("tent", "⛺", "Tent"), ("car", "🚗", "Car"),
           ("water", "💧", "Water"), ("wc", "🚻", "Toilet"), ("danger", "⚠️", "Danger"), ("pin", "📍", "Point"))
EO_COLS = ("#e03131", "#e8590c", "#f2c94c", "#2f9e44", "#15aabf", "#1c7ed6", "#7048e8", "#c2255c", "#8d5a2b", "#495057")
EO = {"cache": {}, "lock": threading.Lock()}
EO_PID = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
EO_COL = re.compile(r"^#[0-9a-fA-F]{6}$")


class EOError(Exception):
    pass


# ---- reading: GeoJSON here, GPX / KML with kt_parse (639zzx) -----------------------------------------------------------------------
def _eo_num(v, lo, hi):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and lo <= v <= hi else None


def _eo_pos(c):
    """[lon, lat(, height)] -> (lat, lon, height | None) or None"""
    if not isinstance(c, (list, tuple)) or len(c) < 2:
        return None
    lo, la = _eo_num(c[0], -180.0, 180.0), _eo_num(c[1], -90.0, 90.0)
    if lo is None or la is None:
        return None
    return (round(la, 6), round(lo, 6), _eo_num(c[2], -500.0, 9000.0) if len(c) > 2 else None)


def _eo_text(s, n):
    """a note: lines stay, no control or direction signs, at most n signs"""
    s = "".join(c for c in str(s or "") if (c >= " " or c == "\n") and c not in "\x7f‪‫‬‭‮⁦⁧⁨⁩")
    return "\n".join(" ".join(x.split()) for x in s.replace("\r", "").split("\n")).strip()[:n]


def _eo_emoji(s):
    s = "".join(c for c in str(s or "") if c >= " " and c not in "\x7f‪‫‬‭‮⁦⁧⁨⁩<>&\"'").strip()
    return s[:8]


def _eo_col(s):
    s = str(s or "")
    return s.lower() if EO_COL.match(s) else ""


def _eo_sym(sym, emoji):
    """(symbol key, emoji): a known symbol, or «custom» with its own emoji, or the point"""
    d = {k: e for k, e, _n in EO_SYMS}
    if sym in d:
        return sym, d[sym]
    em = _eo_emoji(emoji)
    if em:
        for k, e, _n in EO_SYMS:
            if e == em:
                return k, e
        return "custom", em
    return "pin", d["pin"]


def _eo_place(ft, pr, p, i):
    sym, em = _eo_sym(pr.get("symbol"), pr.get("emoji"))
    fid = ft.get("id")
    pid = str(fid) if isinstance(fid, (str, int)) and not isinstance(fid, bool) and EO_PID.match(str(fid)) else "n%d" % i
    ph = str(pr.get("photo") or "")
    rv = pr.get("rev")
    return {"id": pid, "la": p[0], "lo": p[1], "ele": p[2] if p[2] is not None else _eo_num(pr.get("ele"), -500.0, 9000.0),
            "name": _kt_name(pr.get("name") or pr.get("title"))[:80], "sym": sym, "em": em, "col": _eo_col(pr.get("color") or pr.get("marker-color")),
            "note": _eo_text(pr.get("note") or pr.get("description"), EO_NOTE_MAX), "photo": ph if TZ_ID.match(ph) else "",
            "date": str(pr.get("date") or "")[:40], "by": _kt_name(pr.get("by"))[:60], "v": rv if isinstance(rv, int) and not isinstance(rv, bool) else 0}


def _eo_thin(line):
    if len(line) > EO_LINE_PTS:
        step = (len(line) + EO_LINE_PTS - 1) // EO_LINE_PTS
        line = line[::step] + ([line[-1]] if (len(line) - 1) % step else [])
    return [[q[1], q[0]] for q in line]


def eo_geojson(data):
    """a GeoJSON file -> {"pts": [place], "lines": [[[lon, lat] …]]}; raises EOError with a text for the user"""
    if len(data) > KT_IMPORT_MAX:
        raise EOError("The file is too big.")
    if data[:3] == b"\xef\xbb\xbf":
        data = data[3:]
    try:
        d = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise EOError("This file could not be read.")
    if isinstance(d, dict) and d.get("type") == "FeatureCollection":
        feats = d.get("features")
    elif isinstance(d, dict) and d.get("type") == "Feature":
        feats = [d]
    else:
        feats = None
    if not isinstance(feats, list):
        raise EOError("This file is no GeoJSON file.")
    pts, lines = [], []
    for i, ft in enumerate(feats[:EO_MAX_FEAT]):
        if not isinstance(ft, dict) or not isinstance(ft.get("geometry"), dict):
            continue
        g, pr = ft["geometry"], ft.get("properties") if isinstance(ft.get("properties"), dict) else {}
        t, c = g.get("type"), g.get("coordinates")
        if t in ("Point", "MultiPoint") and len(pts) >= EO_MAX_PTS:
            continue
        if t == "Point":
            p = _eo_pos(c)
            if p:
                pts.append(_eo_place(ft, pr, p, i))
        elif t == "MultiPoint" and isinstance(c, list):
            for k, q in enumerate(c[:EO_MAX_PTS - len(pts)]):
                p = _eo_pos(q)
                if p:
                    pts.append(dict(_eo_place(ft, pr, p, i), id="n%d.%d" % (i, k)))
        elif t in ("LineString", "MultiLineString", "Polygon", "MultiPolygon") and isinstance(c, list):
            parts = [c] if t == "LineString" else c if t in ("MultiLineString", "Polygon") else [r for poly in c if isinstance(poly, list) for r in poly]
            for part in parts[:EO_LINES_MAX]:
                if isinstance(part, list) and len(lines) < EO_LINES_MAX:
                    ln = [p for p in (_eo_pos(q) for q in part[:KT_MAX_PTS]) if p]
                    if len(ln) >= 2:
                        lines.append(_eo_thin(ln))
    return {"pts": pts, "lines": lines}


def eo_read(root, m):
    """the places and lines of one backpack file (kept until the file changes): {"pts", "lines", "err"}"""
    p = os.path.join(root, "f", m["id"] + ".bin")
    try:
        st = os.stat(p)
    except OSError:
        return {"pts": [], "lines": [], "err": "This file could not be read."}
    sig = (st.st_size, st.st_mtime_ns, st.st_ino, m.get("ver"), m["name"])
    with EO["lock"]:
        c = EO["cache"].get(m["id"])
        if c is not None and c[0] == sig:
            return c[1]
    out = {"pts": [], "lines": [], "err": ""}
    try:
        if st.st_size > KT_IMPORT_MAX:
            raise EOError("The file is too big.")
        with open(p, "rb") as f:
            data = f.read(KT_IMPORT_MAX + 1)
        if tausch_ext(m["name"]) == "geojson":
            out.update(eo_geojson(data))
        else:
            r = kt_parse(data, m["name"], need_route=False)
            out["pts"] = [{"id": "w%d" % i, "la": round(w["lat"], 6), "lo": round(w["lon"], 6), "ele": w["ele"], "name": w["name"][:80], "sym": "pin", "em": "📍",
                           "col": "", "note": "", "photo": "", "date": "", "by": "", "v": 0} for i, w in enumerate(r["wps"])]
            out["lines"] = [_eo_thin(r["pts"])] if len(r["pts"]) >= 2 else []
    except (EOError, KTError) as e:
        out = {"pts": [], "lines": [], "err": str(e)}
    except Exception as e:                                    # a broken file is never more than a layer with a note
        log_event("sys", f"Own places: a file could not be read ({e.__class__.__name__})")
        out = {"pts": [], "lines": [], "err": "This file could not be read."}
    with EO["lock"]:
        EO["cache"][m["id"]] = (sig, out)
        if len(EO["cache"]) > 4 * EO_MAX_LAYERS:
            EO["cache"].pop(next(iter(EO["cache"])), None)
    return out


# ---- which files are layers, for whom ----------------------------------------------------------------------------------------------
def eo_is_own(m):
    return (m["area"] == "all" and m.get("folder", "").lower() == EO_FOLDER.lower() and m["name"].lower() == EO_FILE.lower())


def eo_own():
    """the backpack file of «Meine Orte» (or None); call with TZ["lock"]"""
    return next((m for m in (TZ["files"] or {}).values() if eo_is_own(m)), None)


def eo_files(who):
    """the backpack files that are layers for this person: «Für alle» (not hidden; the administrator sees hidden ones too) and
    the own private files (with the right to see files)"""
    if _tz_load() is None:
        return []
    with TZ["lock"]:
        out = [dict(m) for m in TZ["files"].values() if tausch_ext(m["name"]) in EO_EXT
               and (m["area"] == "all" or ("files_view" in who["perms"] and m["owner"] == who["key"]))
               and (not m.get("eo_hide") or who["admin"])]
    out.sort(key=lambda m: (not eo_is_own(m), -int(m.get("t") or 0)))
    return out[:EO_MAX_LAYERS]


def eo_photo_ok(fid, owner):
    """a photo of a place: a picture of the backpack with a preview, «Für alle» (or of the same owner as the layer)"""
    m = (TZ["files"] or {}).get(fid)
    return bool(m and m.get("thumb") and tausch_type(m["name"])[1] == "image" and (m["area"] == "all" or m["owner"] == owner))


def eo_layer(root, m, who, lang=None):
    r = eo_read(root, m)
    own = eo_is_own(m)
    with TZ["lock"]:
        pts = [dict(p, photo=p["photo"] if p["photo"] and eo_photo_ok(p["photo"], m["owner"]) else "") for p in r["pts"]]
    out = {"id": m["id"], "name": m["name"], "folder": m.get("folder", "") if m["area"] == "all" else "", "area": m["area"], "own": own,
           "src": tausch_ext(m["name"]), "hidden": bool(m.get("eo_hide")), "mine": m["owner"] == who["key"], "t": int(m.get("t") or 0),
           "err": tr(r["err"], lang) if r["err"] else "", "pts": pts, "lines": r["lines"]}
    if own and who["admin"]:
        out["hist"] = [{"v": h["v"], "t": h["t"], "by": h.get("by", ""), "n": h.get("n")} for h in reversed(m.get("hist") or [])]
    return out


def eo_list(who, lang=None):
    root = _tz_load()
    r0, _k, prob = tausch_root()
    out = {"ok": True, "layers": [], "folder": EO_FOLDER,
           "me": {"admin": bool(who["admin"]), "down": "files_down" in who["perms"] or bool(who["admin"])}}
    if root is None:
        out["store"] = tr("The storage (USB stick / SSD) is not there - plug it in again.", lang) if prob == "missing" else ""
        return out
    out["layers"] = [eo_layer(root, m, who, lang) for m in eo_files(who)]
    return out


def eo_find_layer(who, fid):
    if not TZ_ID.match(str(fid or "")):
        return None, None
    root = _tz_load()
    if root is None:
        return None, None
    m = next((x for x in eo_files(who) if x["id"] == fid), None)
    return (root, m) if m else (None, None)


# ---- writing «Meine Orte.geojson» (in the backpack, under its lock) -----------------------------------------------------------------
def eo_folder(root):
    """the folder «🗺️ Karte» in «Für alle» (made when missing); its name. Call with TZ["lock"]."""
    x = next((f for f in TZ["folders"] if f["name"].lower() == EO_FOLDER.lower()), None)
    if x is not None:
        return x["name"]
    if len(TZ["folders"]) >= TZ_MAX_FOLDERS:
        raise EOError("The digital backpack has no room for the folder «🗺️ Karte» (too many folders).")
    TZ["folders"].append({"name": EO_FOLDER, "by": "admin", "by_name": "MoveEye", "t": int(time.time())})
    TZ["folders"].sort(key=lambda f: f["name"].lower())
    _tz_folders_save(root)
    log_event("web", "Digital backpack: folder «🗺️ Karte» created for the own places")
    return EO_FOLDER


def eo_empty():
    return {"type": "FeatureCollection", "moveeye": {"art": "orte", "v": 1}, "features": []}


def _eo_load_own(root, m):
    """the GeoJSON of «Meine Orte» as it is (dict) - EOError when it cannot be read (then nothing is written)"""
    if m is None:
        return eo_empty()
    try:
        with open(os.path.join(root, "f", m["id"] + ".bin"), "rb") as f:
            data = f.read(KT_IMPORT_MAX + 1)
        if len(data) > KT_IMPORT_MAX:
            raise ValueError("too big")
        d = json.loads(data[3:] if data[:3] == b"\xef\xbb\xbf" else data)
    except (OSError, ValueError, UnicodeDecodeError, RecursionError):
        d = None
    if not (isinstance(d, dict) and d.get("type") == "FeatureCollection" and isinstance(d.get("features"), list)):
        raise EOError("«Meine Orte.geojson» cannot be read - repair or delete it in the digital backpack.")
    return d


def _eo_save(root, m, data, who, lang=None):
    """write the bytes of «Meine Orte» as a new version of the backpack file (the last TZ_HIST stay) or as a new file; -> meta"""
    if not CFG.get("tausch_on", True):
        raise EOError("The file exchange is switched off.")
    if tausch_root()[2] == "ro":
        raise EOError("The memory card is write-protected (overlay) - files would be lost at the next restart. Use a USB stick.")
    err = _tz_extra_room(len(data), "admin", lang)
    if err:
        raise EOError(err)
    n_old = None
    if m is None:
        folder = eo_folder(root)
        fid = secrets.token_hex(8)
        while fid in TZ["files"]:
            fid = secrets.token_hex(8)
        m = {"id": fid, "name": EO_FILE, "area": "all", "folder": folder, "owner": "admin", "owner_name": "Admin", "size": len(data),
             "t": int(time.time()), "kind": "other", "thumb": False, "ver": 1, "ed_name": who["name"], "ed_t": int(time.time())}
        try:
            with open(os.path.join(root, "f", fid + ".bin.tmp"), "wb") as f:
                f.write(data)
            os.replace(os.path.join(root, "f", fid + ".bin.tmp"), os.path.join(root, "f", fid + ".bin"))
            _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
        except OSError as e:
            raise EOError(tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})")
        TZ["files"][fid] = m
        return m
    fid, cur = m["id"], int(m.get("ver") or 1)
    hd = os.path.join(root, "h", fid)
    try:
        n_old = len(eo_read(root, m)["pts"])
    except Exception:
        n_old = None
    try:
        os.makedirs(hd, exist_ok=True)
        shutil.copyfile(os.path.join(root, "f", fid + ".bin"), os.path.join(hd, f"{cur}.txt"))
        hist = list(m.get("hist") or []) + [{"v": cur, "t": m.get("ed_t") or m.get("t", 0), "by": m.get("ed_name") or m.get("owner_name") or "",
                                             "size": m["size"], "n": n_old}]
        for h in hist[:-TZ_HIST]:
            try:
                os.remove(os.path.join(hd, f"{h['v']}.txt"))
            except OSError:
                pass
        hist = hist[-TZ_HIST:]
        tmp = os.path.join(root, "f", fid + ".bin.tmp")
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, os.path.join(root, "f", fid + ".bin"))   # a new file: the network share (639zzzn) links it again
    except OSError as e:
        raise EOError(tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})")
    m.update(size=len(data), ver=cur + 1, ed_name=who["name"], ed_t=int(time.time()), hist=hist, hist_size=sum(h["size"] for h in hist))
    _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
    return m


def _eo_dump(fc):
    return json.dumps(fc, ensure_ascii=False, indent=1).encode("utf-8")


def _eo_feat_index(feats, pid):
    for i, ft in enumerate(feats):
        if not isinstance(ft, dict) or not isinstance(ft.get("geometry"), dict) or ft["geometry"].get("type") != "Point":
            continue
        fid = ft.get("id")
        own = str(fid) if isinstance(fid, (str, int)) and not isinstance(fid, bool) and EO_PID.match(str(fid)) else "n%d" % i
        if own == pid:
            return i
    return None


def _eo_now():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()) + (lambda z: z[:3] + ":" + z[3:] if len(z) == 5 else "")(time.strftime("%z"))


def _eo_props(d, old, who):
    """the properties of a place from the page (checked); old = the properties it had"""
    pr = dict(old or {})
    sym, em = _eo_sym(d.get("sym") if "sym" in d else pr.get("symbol"), d.get("emoji") if "emoji" in d else pr.get("emoji"))
    pr.update(symbol=sym, emoji=em)
    if "name" in d:
        pr["name"] = _kt_name(d.get("name"))[:80]
    if "note" in d:
        pr["note"] = _eo_text(d.get("note"), EO_NOTE_MAX)
    if "color" in d:
        c = _eo_col(d.get("color"))
        pr["color"] = c
        pr["marker-color"] = c                             # other map programs show the colour too (simplestyle)
        if not c:
            pr.pop("color", None); pr.pop("marker-color", None)
    if "photo" in d:
        ph = str(d.get("photo") or "")
        if ph and not (TZ_ID.match(ph) and eo_photo_ok(ph, "admin")):
            raise EOError("This photo is not in the digital backpack (any more).")
        if ph:
            pr["photo"], pr["photo_name"] = ph, TZ["files"][ph]["name"]
        else:
            pr.pop("photo", None); pr.pop("photo_name", None)
    pr.setdefault("name", "")
    if not old:
        pr["date"], pr["by"] = _eo_now(), who["name"]
    pr["changed"], pr["changed_by"] = _eo_now(), who["name"]
    pr["rev"] = int(pr.get("rev") or 0) + 1 if isinstance(pr.get("rev"), int) else 1
    return pr


def eo_action(who, d, lang=None):
    """(ok, error, result, code) - every change: administrator or files_admin"""
    a = str(d.get("action") or "")
    if not who["admin"]:
        return False, tr("not allowed for your user", lang), {}, 403
    root = _tz_load()
    if root is None:
        return False, tr("The storage (USB stick / SSD) is not there - plug it in again.", lang), {}, 409
    if not tausch_rate(who["key"], "eo", 400):
        return False, tr("Too many changes in a short time - wait a few minutes.", lang), {}, 429
    try:
        if a == "hide":
            fid = str(d.get("file") or "")
            with TZ["lock"]:
                m = TZ["files"].get(fid) if TZ_ID.match(fid) else None
                if m is None or m["area"] != "all" or tausch_ext(m["name"]) not in EO_EXT or eo_is_own(m):
                    return False, tr("unknown file", lang), {}, 404
                if d.get("hide"):
                    m["eo_hide"] = True
                else:
                    m.pop("eo_hide", None)
                _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
            log_event("web", f"{who['name']}: map layer «{m['name']}» " + ("hidden for everyone" if d.get("hide") else "shown for everyone again"))
            return True, "", {}, 200
        if a == "prep":                                     # before a photo is uploaded: the folder «🗺️ Karte»
            if not CFG.get("tausch_on", True):
                raise EOError("The file exchange is switched off.")
            with TZ["lock"]:
                return True, "", {"folder": eo_folder(root)}, 200
        with TZ["lock"]:
            m = eo_own()
            if a == "restore":
                h = next((x for x in (m.get("hist") or []) if x.get("v") == d.get("v")), None) if m else None
                if h is None:
                    return False, tr("This version is not kept any more.", lang), {}, 404
                try:
                    with open(os.path.join(root, "h", m["id"], f"{int(h['v'])}.txt"), "rb") as f:
                        data = f.read(KT_IMPORT_MAX + 1)
                    eo_geojson(data)
                except (OSError, EOError):
                    return False, tr("This version is not kept any more.", lang), {}, 404
                m = _eo_save(root, m, data, who, lang)
                log_event("web", f"{who['name']}: own places - version {h['v']} taken back")
                return True, "", {"layer": eo_layer(root, m, who, lang)}, 200
            fc = _eo_load_own(root, m)
            feats = fc["features"]
            res = {}
            if a in ("add", "copy"):
                if sum(1 for ft in feats if isinstance(ft, dict) and isinstance(ft.get("geometry"), dict) and ft["geometry"].get("type") == "Point") >= EO_MAX_PLACES:
                    return False, trf("At most {n} places - delete some first.", lang, n=EO_MAX_PLACES), {}, 400
                if a == "copy":
                    r2, src = eo_find_layer(who, d.get("file"))
                    p = next((x for x in eo_read(r2, src)["pts"] if x["id"] == str(d.get("id") or "")), None) if src else None
                    if p is None:
                        return False, tr("This place does not exist (any more).", lang), {}, 404
                    la, lo = p["la"], p["lo"]
                    src_d = {"name": p["name"] or src["name"].rsplit(".", 1)[0], "note": p["note"], "sym": p["sym"], "emoji": p["em"], "color": p["col"]}
                    if p.get("ele") is not None:
                        src_d["ele"] = p["ele"]
                    if p["photo"] and eo_photo_ok(p["photo"], "admin"):
                        src_d["photo"] = p["photo"]
                    d2 = src_d
                else:
                    la, lo = _eo_num(d.get("lat"), -90.0, 90.0), _eo_num(d.get("lon"), -180.0, 180.0)
                    if la is None or lo is None:
                        return False, tr("unknown place", lang), {}, 400
                    d2 = {k: d[k] for k in ("name", "note", "sym", "emoji", "color", "photo") if k in d}
                pid = "o" + secrets.token_hex(4)
                pr = _eo_props(d2, None, who)
                if d2.get("ele") is not None:
                    pr["ele"] = round(float(d2["ele"]), 1)
                feats.append({"type": "Feature", "id": pid, "geometry": {"type": "Point", "coordinates": [round(lo, 6), round(la, 6)]}, "properties": pr})
                res["id"] = pid
            elif a in ("edit", "move", "delete"):
                pid = str(d.get("id") or "")
                i = _eo_feat_index(feats, pid)
                if i is None:
                    return False, tr("This place does not exist (any more).", lang), {"layer": eo_layer(root, m, who, lang) if m else None}, 404
                ft = feats[i]
                old = ft.get("properties") if isinstance(ft.get("properties"), dict) else {}
                rv = old.get("rev") if isinstance(old.get("rev"), int) and not isinstance(old.get("rev"), bool) else 0
                if d.get("v") != rv:
                    return False, trf("Meanwhile {who} has changed this place.", lang, who=old.get("changed_by") or old.get("by") or "?"), \
                        {"layer": eo_layer(root, m, who, lang), "conflict": True}, 409
                if a == "delete":
                    feats.pop(i)
                elif a == "move":
                    la, lo = _eo_num(d.get("lat"), -90.0, 90.0), _eo_num(d.get("lon"), -180.0, 180.0)
                    if la is None or lo is None:
                        return False, tr("unknown place", lang), {}, 400
                    ft["geometry"] = {"type": "Point", "coordinates": [round(lo, 6), round(la, 6)]}
                    pr = _eo_props({}, old, who)
                    pr.pop("ele", None)                              # a height from a file is not true any more
                    ft["properties"] = pr
                else:
                    ft["properties"] = _eo_props({k: d[k] for k in ("name", "note", "sym", "emoji", "color", "photo") if k in d}, old, who)
            else:
                return False, tr("unknown action", lang), {}, 400
            for k, ft in enumerate(feats):                         # every place gets its fixed id
                if isinstance(ft, dict) and isinstance(ft.get("geometry"), dict) and ft["geometry"].get("type") == "Point" and \
                        not (isinstance(ft.get("id"), (str, int)) and not isinstance(ft.get("id"), bool) and EO_PID.match(str(ft["id"]))):
                    ft["id"] = "o" + secrets.token_hex(4)
            data = _eo_dump(fc)
            if len(data) > KT_IMPORT_MAX:
                return False, tr("The file is too big.", lang), {}, 400
            m = _eo_save(root, m, data, who, lang)
            res["layer"] = eo_layer(root, m, who, lang)
        log_event("web", f"{who['name']}: own place " + {"add": "added", "copy": "taken over", "edit": "changed", "move": "moved", "delete": "deleted"}[a])
        return True, "", res, 200
    except EOError as e:
        return False, tr(str(e), lang), {}, 400


# ---- export of a layer: GPX / KML (escaped like 639zzx: _kt_x; notes keep their lines) --------------------------------------------
def _eo_x(s):
    return "&#10;".join(_kt_x(x) for x in str(s).split("\n"))


def eo_gpx(name, r):
    o = ['<?xml version="1.0" encoding="UTF-8"?>', '<gpx version="1.1" creator="MoveEye" xmlns="http://www.topografix.com/GPX/1/1">',
         "<metadata><name>%s</name></metadata>" % _kt_x(name)]
    for p in r["pts"]:
        o.append('<wpt lat="%.6f" lon="%.6f">%s<name>%s</name>%s%s</wpt>' % (p["la"], p["lo"], "" if p.get("ele") is None else "<ele>%.1f</ele>" % p["ele"],
                 _kt_x(p["name"] or p["em"]), "<desc>%s</desc>" % _eo_x(p["note"]) if p["note"] else "", "<sym>%s</sym>" % _kt_x(p["em"]) if p["em"] else ""))
    for ln in r["lines"]:
        o.append("<trk><name>%s</name><trkseg>" % _kt_x(name) + "".join('<trkpt lat="%.6f" lon="%.6f"/>' % (q[1], q[0]) for q in ln) + "</trkseg></trk>")
    o.append("</gpx>")
    return "\n".join(o).encode("utf-8")


def eo_kml(name, r):
    o = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>', "<name>%s</name>" % _kt_x(name), "<Folder><name>Waypoints</name>"]
    for p in r["pts"]:
        o.append("<Placemark><name>%s</name>%s<Point><coordinates>%.6f,%.6f%s</coordinates></Point></Placemark>"
                 % (_kt_x(p["name"] or p["em"]), "<description>%s</description>" % _eo_x(p["note"]) if p["note"] else "", p["lo"], p["la"],
                    "" if p.get("ele") is None else ",%.1f" % p["ele"]))
    o.append("</Folder><Folder><name>Tracks</name>")
    for ln in r["lines"]:
        o.append("<Placemark><name>%s</name><LineString><tessellate>1</tessellate><coordinates>%s</coordinates></LineString></Placemark>"
                 % (_kt_x(name), " ".join("%.6f,%.6f" % (q[0], q[1]) for q in ln)))
    o.append("</Folder></Document></kml>")
    return "\n".join(o).encode("utf-8")


# ---- rights and routes --------------------------------------------------------------------------------------------------------------
# /karte/… and /api/karte/… are for every logged-in user (VIEW_GET of 639zzq): the places on the map are for all; changing: the
# administrator, and files_admin through this path
PERM_POST["files_admin"] = set(PERM_POST.get("files_admin", ())) | {"/api/karte/orte"}

_smalltv_routes_639zzzzo = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzzzo: /api/karte/orte, photos, export, height
    _smalltv_routes_639zzzzo(app, reply, body)
    from flask import Response, request, g

    def lang_():
        return norm_lang(request.args.get("lang") or CFG.get("lang"))

    @app.route("/api/karte/orte", methods=["GET", "POST"])
    def api_eo():
        who = tausch_who(g)
        if request.method == "GET":
            return reply(eo_list(who, lang_()))
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        ok, err, res, code = eo_action(who, d, L)
        return reply(dict(res, ok=ok, error=err or None), code)

    @app.route("/api/karte/orte/hoehe")
    def api_eo_hoehe():
        who = tausch_who(g)
        la, lo = _eo_num(_eo_flt(request.args.get("lat")), -90.0, 90.0), _eo_num(_eo_flt(request.args.get("lon")), -180.0, 180.0)
        if la is None or lo is None or not tausch_rate(who["key"], "eoh", 600):
            return reply({"ok": True, "ele": None})
        return reply({"ok": True, "ele": kh_height(la, lo)})

    @app.route("/karte/orte/foto/<fid>.jpg")
    def eo_foto(fid):                                      # only a photo a visible place points to; the preview, never the file
        who = tausch_who(g)
        root = _tz_load()
        if root is None or not TZ_ID.match(fid or ""):
            return Response(b"", 404)
        ok_ = False
        for m in eo_files(who):
            if any(p["photo"] == fid for p in eo_read(root, m)["pts"]):
                with TZ["lock"]:
                    ok_ = eo_photo_ok(fid, m["owner"])
                if ok_:
                    break
        p = os.path.join(root, "t", fid + "_p.jpg")
        if not ok_ or not os.path.isfile(p):
            return Response(b"", 404)
        return _tz_send(p, "image/jpeg", False, cache="private, max-age=86400")

    @app.route("/karte/orte/x/<fid>.<ext>")
    def eo_export(fid, ext):
        who = tausch_who(g)
        root, m = eo_find_layer(who, fid)
        if m is None or ext not in ("gpx", "kml"):
            return reply({"ok": False, "error": tr("unknown file", lang_())}, 404)
        if not (who["admin"] or "files_down" in who["perms"] or m["owner"] == who["key"]):
            return reply({"ok": False, "error": tr("not allowed for your user", lang_())}, 403)
        r = eo_read(root, m)
        if r["err"]:
            return reply({"ok": False, "error": tr(r["err"], lang_())}, 400)
        stem = os.path.splitext(m["name"])[0]
        from urllib.parse import quote
        fn = ("".join(c if c.isalnum() or c in " -_." else "_" for c in stem).strip(" .")[:60] or "Orte") + "." + ext
        data = eo_gpx(stem, r) if ext == "gpx" else eo_kml(stem, r)
        return Response(data, mimetype="application/gpx+xml" if ext == "gpx" else "application/vnd.google-earth.kml+xml",
                        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store", "Content-Security-Policy": "sandbox; default-src 'none'",
                                 "Content-Disposition": "attachment; filename*=UTF-8''" + quote(fn)})


def _eo_flt(v):
    try:
        return float(str(v)[:30])
    except (TypeError, ValueError):
        return None


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_EO = {
    "Own places": ("Eigene Orte", "Lieux personnels", "Luoghi propri", "Agens lieus"),
    "Layers from the digital backpack – every file with places (GeoJSON, GPX, KML) appears here by itself.": (
        "Ebenen aus dem Digitalen Rucksack – jede Datei mit Orten (GeoJSON, GPX, KML) erscheint hier von selbst.",
        "Calques du sac à dos numérique – chaque fichier avec des lieux (GeoJSON, GPX, KML) apparaît ici tout seul.",
        "Livelli dello zaino digitale – ogni file con luoghi (GeoJSON, GPX, KML) appare qui da solo.",
        "Nivels dal satgados digital – mintga datoteca cun lieus (GeoJSON, GPX, KML) cumpara qua da sasez."),
    "Set": ("Setzen", "Placer", "Posa", "Metter"),
    "Own": ("Eigenes", "Perso", "Proprio", "Agen"),
    "Own symbol": ("Eigenes Symbol", "Symbole personnel", "Simbolo proprio", "Agen simbol"),
    "Hut": ("Hütte", "Cabane", "Capanna", "Tegia"),
    "Fireplace": ("Feuerstelle", "Foyer", "Focolare", "Fuaina"),
    "Bike": ("Velo", "Vélo", "Bici", "Velo"),
    "Tent": ("Zelt", "Tente", "Tenda", "Tenda"),
    "Car": ("Auto", "Voiture", "Auto", "Auto"),
    "Water": ("Wasser", "Eau", "Acqua", "Aua"),
    "Toilet": ("WC", "WC", "WC", "WC"),
    "Danger": ("Gefahr", "Danger", "Pericolo", "Privel"),
    "Point": ("Punkt", "Point", "Punto", "Punct"),
    "Tap on the map:": ("Tippe auf die Karte:", "Touchez la carte :", "Tocca la mappa:", "Tutga la charta:"),
    "set {name}": ("{name} setzen", "placer {name}", "posa {name}", "metter {name}"),
    "Finish drawing the route first.": ("Zuerst die Route fertig zeichnen.", "Terminez d’abord de dessiner l’itinéraire.", "Prima finisci di disegnare il percorso.",
                                        "L’emprim finir da dissegnar la ruta."),
    "Drag the symbol or tap the new place.": ("Symbol ziehen oder den neuen Ort antippen.", "Faites glisser le symbole ou touchez le nouvel endroit.",
                                              "Trascina il simbolo o tocca il nuovo luogo.", "Trair il simbol u tutgar il nov lieu."),
    "Close": ("Schliessen", "Fermer", "Chiudi", "Serrar"),
    "set": ("gesetzt", "placé le", "posato il", "mess"),
    "by": ("von", "par", "da", "da"),
    "m a.s.l.": ("m ü. M.", "m d’alt.", "m s.l.m.", "m s. m."),
    "Edit": ("Bearbeiten", "Modifier", "Modifica", "Modifitgar"),
    "Move": ("Verschieben", "Déplacer", "Sposta", "Spustar"),
    "Delete": ("Löschen", "Supprimer", "Elimina", "Stizzar"),
    "Copy into «My places»": ("In «Meine Orte» übernehmen", "Reprendre dans « Mes lieux »", "Copia in «I miei luoghi»", "Prender en «Mes lieus»"),
    "Start a tour here": ("Tour ab hier", "Randonnée depuis ici", "Escursione da qui", "Tura da qua"),
    "Delete «{name}»? It cannot be undone here.": ("«{name}» löschen? Das geht hier nicht rückgängig.", "Supprimer « {name} » ? Impossible d’annuler ici.",
                                                   "Eliminare «{name}»? Qui non si può annullare.", "Stizzar «{name}»? Quai na po betg vegnir revocà qua."),
    "Yes, delete": ("Ja, löschen", "Oui, supprimer", "Sì, elimina", "Gea, stizzar"),
    "No": ("Nein", "Non", "No", "Na"),
    "Edit place": ("Ort bearbeiten", "Modifier le lieu", "Modifica il luogo", "Modifitgar il lieu"),
    "Name": ("Name", "Nom", "Nome", "Num"),
    "Symbol": ("Symbol", "Symbole", "Simbolo", "Simbol"),
    "Colour": ("Farbe", "Couleur", "Colore", "Colur"),
    "Note": ("Notiz", "Note", "Nota", "Notizia"),
    "Photo": ("Foto", "Photo", "Foto", "Foto"),
    "Choose photo": ("Foto wählen", "Choisir une photo", "Scegli foto", "Tscherner ina foto"),
    "Remove": ("Entfernen", "Supprimer", "Rimuovi", "Allontanar"),
    "Uploading": ("Lade hoch", "Envoi", "Caricamento", "Chargiar si"),
    "saved in": ("gespeichert in", "enregistré dans", "salvato in", "memorisà en"),
    "Please choose a symbol.": ("Bitte ein Symbol wählen.", "Veuillez choisir un symbole.", "Scegli un simbolo.", "Tscherna per plaschair in simbol."),
    "Save": ("Speichern", "Enregistrer", "Salva", "Memorisar"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "This picture cannot be read here.": ("Dieses Bild kann hier nicht gelesen werden.", "Cette image ne peut pas être lue ici.", "Questa immagine non può essere letta qui.",
                                          "Quest maletg na po betg vegnir legì qua."),
    "Place": ("Ort", "Lieu", "Luogo", "Lieu"),
    "No places yet.": ("Noch keine Orte.", "Pas encore de lieux.", "Ancora nessun luogo.", "Anc nagins lieus."),
    "Choose a symbol in the bar on the map, then tap the place.": ("Ein Symbol in der Leiste auf der Karte wählen, dann den Ort antippen.",
                                                                  "Choisissez un symbole dans la barre sur la carte, puis touchez l’endroit.",
                                                                  "Scegli un simbolo nella barra sulla mappa, poi tocca il luogo.",
                                                                  "Tscherna in simbol en la trav sin la charta, lura tutga il lieu."),
    "place": ("Ort", "lieu", "luogo", "lieu"),
    "places": ("Orte", "lieux", "luoghi", "lieus"),
    "line": ("Linie", "ligne", "linea", "lingia"),
    "lines": ("Linien", "lignes", "linee", "lingias"),
    "Only me": ("Nur ich", "Moi seulement", "Solo io", "Mo jau"),
    "For everyone": ("Für alle", "Pour tous", "Per tutti", "Per tuts"),
    "edit here": ("hier bearbeiten", "modifier ici", "modifica qui", "modifitgar qua"),
    "only to look at": ("nur ansehen", "consultation seule", "solo da guardare", "mo per guardar"),
    "hidden for everyone": ("für alle ausgeblendet", "masqué pour tous", "nascosto per tutti", "zuppà per tuts"),
    "Show for everyone": ("Für alle zeigen", "Afficher pour tous", "Mostra a tutti", "Mussar a tuts"),
    "Hide for everyone": ("Für alle ausblenden", "Masquer pour tous", "Nascondi a tutti", "Zuppentar per tuts"),
    "Versions": ("Versionen", "Versions", "Versioni", "Versiuns"),
    "Earlier versions of «My places» (the last 20). Taking one back saves it as the newest version.": (
        "Frühere Versionen von «Meine Orte» (die letzten 20). Zurückholen speichert sie als neueste Version.",
        "Versions précédentes de « Mes lieux » (les 20 dernières). La reprendre l’enregistre comme version la plus récente.",
        "Versioni precedenti di «I miei luoghi» (le ultime 20). Ripristinarne una la salva come versione più recente.",
        "Versiuns pli veglias da «Mes lieus» (las ultimas 20). Turnar a prender la memorisescha sco versiun la pli nova."),
    "Take back": ("Zurückholen", "Reprendre", "Ripristina", "Turnar a prender"),
    "Show / hide symbols": ("Symbole zeigen / verstecken", "Afficher / masquer les symboles", "Mostra / nascondi simboli", "Mussar / zuppentar simbols"),
    "New places from on the way: load a GPX or KML file (e.g. an export of the swisstopo app) into the 🎒 digital backpack – it appears here as its own layer.": (
        "Neue Orte von unterwegs: GPX- oder KML-Datei (z. B. Export der swisstopo-App) in den 🎒 Digitalen Rucksack laden – sie erscheint hier als eigene Ebene.",
        "Nouveaux lieux en route : chargez un fichier GPX ou KML (p. ex. un export de l’app swisstopo) dans le 🎒 sac à dos numérique – il apparaît ici comme calque.",
        "Nuovi luoghi in viaggio: carica un file GPX o KML (ad es. esportato dall’app swisstopo) nello 🎒 zaino digitale – appare qui come livello proprio.",
        "Novs lieus sin via: chargiar ina datoteca GPX u KML (p.ex. export da l’app swisstopo) en il 🎒 satgados digital – ella cumpara qua sco agen nivel."),
    "No connection to MoveEye.": ("Keine Verbindung zu MoveEye.", "Pas de connexion à MoveEye.", "Nessuna connessione a MoveEye.", "Nagina connexiun cun MoveEye."),
    "on the map": ("auf Karte", "sur la carte", "sulla mappa", "sin la charta"),
    "Show on the map": ("Auf der Karte zeigen", "Afficher sur la carte", "Mostra sulla mappa", "Mussar sin la charta"),
    "Download": ("Herunterladen", "Télécharger", "Scarica", "Telechargiar"),
    "This file shows its places on the offline map, as its own layer.": ("Diese Datei zeigt ihre Orte auf der Offline-Karte, als eigene Ebene.",
                                                                        "Ce fichier affiche ses lieux sur la carte hors ligne, comme calque.",
                                                                        "Questo file mostra i suoi luoghi sulla mappa offline, come livello proprio.",
                                                                        "Questa datoteca mussa ses lieus sin la charta offline, sco agen nivel."),
    "Not on the map (hidden or not readable).": ("Nicht auf der Karte (ausgeblendet oder nicht lesbar).", "Pas sur la carte (masqué ou illisible).",
                                                 "Non sulla mappa (nascosto o non leggibile).", "Betg sin la charta (zuppà u betg legibel)."),
    "The map fills this folder: «My places» and the photos of the places. Other files with places (GPX, KML, GeoJSON) may lie anywhere in the backpack.": (
        "Diesen Ordner füllt die Karte: «Meine Orte» und die Fotos der Orte. Andere Dateien mit Orten (GPX, KML, GeoJSON) dürfen überall im Rucksack liegen.",
        "La carte remplit ce dossier : « Mes lieux » et les photos des lieux. D’autres fichiers avec des lieux (GPX, KML, GeoJSON) peuvent être n’importe où dans le sac.",
        "La mappa riempie questa cartella: «I miei luoghi» e le foto dei luoghi. Altri file con luoghi (GPX, KML, GeoJSON) possono stare ovunque nello zaino.",
        "La charta emplenescha quest ordinatur: «Mes lieus» e las fotos dals lieus. Autras datotecas cun lieus (GPX, KML, GeoJSON) dastgan esser dapertut en il satgados."),
    "This file is no GeoJSON file.": ("Diese Datei ist keine GeoJSON-Datei.", "Ce fichier n’est pas un fichier GeoJSON.", "Questo file non è un file GeoJSON.",
                                      "Questa datoteca n’è nagina datoteca GeoJSON."),
    "No places were found in this file.": ("In dieser Datei wurden keine Orte gefunden.", "Aucun lieu trouvé dans ce fichier.", "Nessun luogo trovato in questo file.",
                                           "En questa datoteca n’èn vegnids chattads nagins lieus."),
    "«Meine Orte.geojson» cannot be read - repair or delete it in the digital backpack.": (
        "«Meine Orte.geojson» ist nicht lesbar – im Digitalen Rucksack reparieren oder löschen.",
        "« Meine Orte.geojson » est illisible – le réparer ou le supprimer dans le sac à dos numérique.",
        "«Meine Orte.geojson» non è leggibile – ripararlo o eliminarlo nello zaino digitale.",
        "«Meine Orte.geojson» n’è betg legibel – reparar u stizzar en il satgados digital."),
    "The digital backpack has no room for the folder «🗺️ Karte» (too many folders).": (
        "Im Digitalen Rucksack hat der Ordner «🗺️ Karte» keinen Platz (zu viele Ordner).",
        "Le sac à dos numérique n’a pas de place pour le dossier « 🗺️ Karte » (trop de dossiers).",
        "Nello zaino digitale non c’è posto per la cartella «🗺️ Karte» (troppe cartelle).",
        "En il satgados digital n’ha l’ordinatur «🗺️ Karte» betg plaz (memia blers ordinaturs)."),
    "This photo is not in the digital backpack (any more).": ("Dieses Foto ist (nicht mehr) im Digitalen Rucksack.", "Cette photo n’est pas (plus) dans le sac à dos numérique.",
                                                              "Questa foto non è (più) nello zaino digitale.", "Questa foto n’è (betg pli) en il satgados digital."),
    "At most {n} places - delete some first.": ("Höchstens {n} Orte – zuerst einige löschen.", "Au plus {n} lieux – en supprimer d’abord.", "Al massimo {n} luoghi – eliminarne prima alcuni.",
                                                "Maximalmain {n} lieus – l’emprim stizzar intgins."),
    "This place does not exist (any more).": ("Diesen Ort gibt es (nicht mehr).", "Ce lieu n’existe pas (plus).", "Questo luogo non esiste (più).", "Quest lieu n’exista (betg pli)."),
    "Meanwhile {who} has changed this place.": ("Inzwischen hat {who} diesen Ort geändert.", "Entre-temps, {who} a modifié ce lieu.", "Nel frattempo {who} ha modificato questo luogo.",
                                                "Entant ha {who} midà quest lieu."),
    "unknown place": ("unbekannter Ort", "lieu inconnu", "luogo sconosciuto", "lieu nunenconuschent"),
}
for _k, _v in _HX_EO.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def eo_tx(keys=None):
    out = {"en": {}}
    for i_, L_ in enumerate(("de", "fr", "it", "rm")):
        out[L_] = {k: v[i_] for k, v in _HX_EO.items() if keys is None or k in keys}
    return out


# ---- on /karte: the section, the bar in the map, the card (CSS, HTML and script are put into the finished page of 639zzq) -----
EO_CSS = """
#eo-bar{position:absolute;left:8px;right:8px;bottom:22px;z-index:3;display:flex;gap:6px;overflow-x:auto;padding:6px;border-radius:14px;background:rgba(20,26,36,.86);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);scrollbar-width:none}
#eo-bar::-webkit-scrollbar{display:none}
#eo-bar button{flex:none;min-width:48px;min-height:48px;border-radius:11px;border:1px solid #ffffff30;background:#ffffff14;color:#fff;font-size:22px;line-height:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;padding:4px 6px}
#eo-bar button small{font-size:10px;color:#d6dbe4}
#eo-bar button.on{background:#2f7cf6;border-color:#8fb8ff}
#eo-bar .eo-lb{flex:none;color:#fff;font-weight:700;font-size:13px;display:flex;align-items:center;padding:0 4px 0 2px;white-space:nowrap}
#eo-hint{position:absolute;left:8px;right:52px;top:8px;z-index:3;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 10px;border-radius:12px;background:#2f7cf6;color:#fff;font-weight:600;font-size:14px;box-shadow:0 2px 10px #0005}
#eo-hint span{flex:1 1 140px;min-width:0}#eo-hint button{min-height:40px;background:#ffffff26;color:#fff;border:0;border-radius:9px;padding:0 10px}
#eo-hint input{width:64px;min-height:40px;font-size:22px;text-align:center;border-radius:9px;border:2px solid #fff;background:#fff;color:#123}
#eo-hint input.bad{border-color:#ffd43b;box-shadow:0 0 0 3px #ffd43b}
.eo-m{display:flex;flex-direction:column;align-items:center;cursor:pointer;touch-action:none}
.eo-m i{font-style:normal;width:34px;height:34px;border-radius:50% 50% 50% 4px;transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 1px 5px #0007}
.eo-m i b{transform:rotate(45deg);font-size:18px;font-weight:400;line-height:1}
.eo-m.sel i{box-shadow:0 0 0 4px #2f7cf6aa,0 1px 5px #0007}
.eo-m span{margin-top:3px;font:600 11px/1.2 system-ui,sans-serif;color:#1b2330;background:#ffffffe0;border-radius:6px;padding:1px 5px;max-width:120px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.eo-m.f i{border-radius:50%;transform:none;width:28px;height:28px}.eo-m.f i b{transform:none;font-size:15px}
.eo-m.f span{display:none}#kq-map.eo-z .eo-m.f span{display:block}
#eo-card{position:absolute;left:8px;right:8px;bottom:8px;z-index:4;max-width:380px;border-radius:16px;background:var(--panel);color:var(--txt);border:1px solid var(--line);box-shadow:0 6px 24px #0008;overflow:hidden;max-height:calc(100% - 16px);overflow-y:auto;overscroll-behavior:contain;touch-action:pan-y}
#eo-card>img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}
#eo-card .bd{padding:10px 12px 12px}
#eo-card h3{margin:0 44px 0 0;font-size:18px;display:flex;gap:8px;align-items:center;overflow-wrap:anywhere}#eo-card h3 .dot{width:14px;height:14px;border-radius:50%;flex:none;border:2px solid #fff}
#eo-card .meta{color:var(--mut);font-size:12.5px;margin:3px 0 6px;overflow-wrap:anywhere}
#eo-card .note{font-size:14.5px;margin:6px 0 10px;white-space:pre-wrap;overflow-wrap:anywhere}
#eo-card .row{display:flex;gap:8px;flex-wrap:wrap}#eo-card .row button{min-height:44px;flex:1 1 auto}
#eo-card .x{position:absolute;right:8px;top:8px;width:40px;height:40px;min-height:0;border-radius:50%;background:#000a;color:#fff;border:0;font-size:18px;z-index:1;padding:0}
#eo-card .ask{margin-top:10px;padding:10px;border-radius:12px;border:1px solid #e0313180;background:#e031311a}
#eo-card .ask b{display:block;margin-bottom:8px;overflow-wrap:anywhere}
.eo{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.eo h2{font-size:18px;margin:0 0 4px}
.eo .sub{color:var(--mut);font-size:13px;margin:0 0 8px}
.eo-ly{display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center;padding:10px 12px;margin:6px 0;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
.eo-ly .ic{font-size:22px;flex:none}.eo-ly>span:not(.ic){flex:1 1 150px;min-width:0;cursor:pointer}.eo-ly b{display:block;overflow-wrap:anywhere}.eo-ly small{display:block;color:var(--mut);overflow-wrap:anywhere}
.eo-ly .ex{display:flex;flex-wrap:wrap;gap:6px;margin-left:auto;justify-content:flex-end}.eo-ly .ex a,.eo-ly .ex button{min-height:40px;padding:0 10px;font-size:13px;display:inline-flex;align-items:center}
.eo-sw{flex:none;width:50px;height:30px;min-height:0;border-radius:15px;background:#5c6577;position:relative;border:0;padding:0}
.eo-sw::after{content:"";position:absolute;top:3px;left:3px;width:24px;height:24px;border-radius:50%;background:#fff;transition:left .15s}
.eo-sw.on{background:#2f7cf6}.eo-sw.on::after{left:23px}.eo-sw:disabled{opacity:.5}
.eo-hist{margin:-2px 0 8px;padding:8px 12px;border:1px dashed var(--line);border-radius:12px}
.eo-hv{display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:4px 0;font-size:13.5px}.eo-hv button{min-height:38px}
.eo-chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.eo-chips button{min-height:40px;border-radius:20px;padding:0 11px;font-size:14px}
.eo-chips button.off{opacity:.45;text-decoration:line-through}
.eo-tip{color:var(--mut);font-size:13px;margin:8px 0;padding:9px 11px;border:1px dashed var(--line);border-radius:12px}
.eo-ed label{display:block;font-size:12.5px;color:var(--mut);margin:8px 0 3px}
.eo-ed input[type=text],.eo-ed textarea{width:100%;box-sizing:border-box;min-height:42px;padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:var(--field,var(--panel));color:var(--txt);font:inherit}
.eo-ed textarea{min-height:64px}
.eo-ed .syms{display:flex;flex-wrap:wrap;gap:5px}.eo-ed .syms button{min-width:42px;min-height:42px;font-size:20px;padding:0;border-radius:10px}
.eo-ed .syms button.on{outline:3px solid #2f7cf6}.eo-ed .syms input.emo{width:56px!important;min-height:42px;text-align:center;font-size:20px;padding:0}
.eo-ed .cols{display:flex;flex-wrap:wrap;gap:7px}.eo-ed .cols button{width:34px;height:34px;border-radius:50%;border:2px solid #fff4;padding:0;min-height:0}
.eo-ed .cols button.on{outline:3px solid #2f7cf6;outline-offset:2px}
.eo-ed .ph{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.eo-ed .ph img{width:72px;height:54px;object-fit:cover;border-radius:8px}
"""
EO_HTML = """
  <section class="eo" id="eo" hidden>
    <h2>📌 <span id="eo-h"></span></h2>
    <p class="sub" id="eo-sub"></p>
    <div class="kt-err" id="eo-msg" hidden></div>
    <div id="eo-items"></div>
    <div class="sub" id="eo-chh" hidden></div>
    <div class="eo-chips" id="eo-chips"></div>
    <div class="eo-tip" id="eo-tip"></div>
  </section>
"""
EO_JS = r"""
// 639zzzzo: «📌 Eigene Orte» on /karte - layers from the digital backpack, the symbol bar, a place card, edit / move / delete.
// Everything from files is set as text only (textContent), never as HTML.
(function () {
  const TX = /*EOTX*/{}, CF = /*EOCF*/{};
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const T = k => (TX[L()] || {})[k] || k;
  const $ = s => document.querySelector(s);
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const btn = (txt, cls, fn) => { const b = el("button", cls || "", txt); b.type = "button"; if (fn) b.onclick = fn; return b; };
  const lsGet = k => { try { return JSON.parse(localStorage.getItem(k) || "[]") || []; } catch (e) { return []; } };
  const lsSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify([...v])); } catch (e) {} };
  const SYM = CF.syms || [], COLS = CF.cols || [];
  const EO = window.EO = {busy: false};
  const S = {layers: [], me: {}, off: new Set(lsGet("eo-off")), symOff: new Set(lsGet("eo-symoff")), marks: [], pick: null, move: null, cur: null, hist: false};
  const api = d => fetch("/api/karte/orte", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))})
    .then(r => r.json()).catch(() => ({ok: false, error: T("No connection to MoveEye.")}));
  const symName = p => { const s = SYM.find(x => x[0] === p.sym); return s ? T(s[2]) : T("Own symbol"); };
  const fmtD = s => { const d = new Date(s); if (isNaN(d)) return ""; const loc = {de: "de-CH", fr: "fr-CH", it: "it-CH", rm: "de-CH"}[L()] || "en-GB";
    return d.toLocaleDateString(loc) + " " + d.toLocaleTimeString(loc, {hour: "2-digit", minute: "2-digit"}); };
  const hasMap = () => !!(window.KQ && KQ.on);
  const ktBusy = () => !!(window.KT && KT.busy && !EO.busy);
  // a point for the tours (639zzx): a real click on the map at the place - its own tap handler takes it like a finger
  const tapAt = (m, la, lo) => { const c = m.getCanvas(), r = c.getBoundingClientRect(), q = m.project([lo, la]);
    const o = {bubbles: true, cancelable: true, view: window, button: 0, clientX: r.left + q.x, clientY: r.top + q.y};   // mousedown first: MapLibre
    ["mousedown", "mouseup", "click"].forEach(t => c.dispatchEvent(new MouseEvent(t, Object.assign({buttons: t === "mousedown" ? 1 : 0}, o)))); };   // compares the click with it
  // ---- the map ----
  let mapP = null;
  const map = () => mapP || (mapP = new Promise(ok => { const t = setInterval(() => { const m = window.KQMAP; if (!m) return;
    const go = () => { clearInterval(t);
      if (!m.getSource("eo")) { m.addSource("eo", {type: "geojson", data: {type: "FeatureCollection", features: []}});
        m.addLayer({id: "eo-c", type: "line", source: "eo", layout: {"line-join": "round", "line-cap": "round"}, paint: {"line-color": "#ffffff", "line-width": 6, "line-opacity": 0.85}});
        m.addLayer({id: "eo-l", type: "line", source: "eo", layout: {"line-join": "round", "line-cap": "round"}, paint: {"line-color": ["get", "c"], "line-width": 3.5, "line-dasharray": [2, 1]}}); }
      m.on("click", tap); m.on("zoom", zl); zl(); ok(m); };
    if (m.isStyleLoaded()) go(); else { clearInterval(t); m.once("load", go); } }, 200); }));
  const zl = () => { const m = window.KQMAP, b = $("#kq-map"); if (m && b) b.classList.toggle("eo-z", m.getZoom() >= 13); };
  const LCOL = ["#f08c00", "#7048e8", "#0ca678", "#d6336c", "#1971c2", "#5c940d"];
  const lcol = L_ => L_.own ? "#e03131" : LCOL[Math.max(0, S.layers.indexOf(L_)) % LCOL.length];
  const shown = L_ => !L_.err && !S.off.has(L_.id) && !L_.hidden;
  function draw() {
    if (!hasMap()) return;
    map().then(m => {
      S.marks.forEach(x => x.remove()); S.marks = [];
      const fc = {type: "FeatureCollection", features: []};
      S.layers.forEach(L_ => { if (!shown(L_)) return;
        (L_.lines || []).forEach(c => fc.features.push({type: "Feature", properties: {c: lcol(L_)}, geometry: {type: "LineString", coordinates: c}}));
        (L_.pts || []).forEach(p => { if (!S.symOff.has(p.em)) marker(m, L_, p); }); });
      m.getSource("eo").setData(fc);
      if (S.cur) { const mk = S.marks.find(x => x._eo.L.id === S.cur.L.id && x._eo.p.id === S.cur.p.id); if (mk) mk.getElement().classList.add("sel"); }
    });
  }
  function marker(m, L_, p) {
    const d = el("div", "eo-m" + (L_.own ? "" : " f")), i = el("i"), b = el("b", "", p.em || "📍");
    i.style.background = p.col || lcol(L_); i.appendChild(b); d.appendChild(i);
    if (p.name) d.appendChild(el("span", "", p.name));
    d.dataset.l = L_.id; d.dataset.p = p.id; d.title = p.name || symName(p);
    d.addEventListener("click", e => { e.stopPropagation();
      if (ktBusy()) { tapAt(m, p.la, p.lo); return; }       // drawing a route: the place becomes a point of it
      if (S.pick || S.move) return; card(L_, p); });
    const mk = new maplibregl.Marker({element: d, anchor: L_.own ? "bottom" : "center"}).setLngLat([p.lo, p.la]).addTo(m);
    mk._eo = {L: L_, p}; S.marks.push(mk); return mk;
  }
  function tap(e) {
    if (S.pick) { place(e.lngLat); return; }
    if (S.move) { moveTo(e.lngLat.lat, e.lngLat.lng); return; }
    if ($("#eo-card")) closeCard();
  }
  const fit = L_ => { if (!hasMap()) return; let a = 90, b = -90, c = 180, d = -180, n = 0;
    const add = (la, lo) => { a = Math.min(a, la); b = Math.max(b, la); c = Math.min(c, lo); d = Math.max(d, lo); n++; };
    (L_.pts || []).forEach(p => add(p.la, p.lo)); (L_.lines || []).forEach(l => l.forEach(q => add(q[1], q[0])));
    if (n) map().then(m => m.fitBounds([[c, a], [d, b]], {padding: 50, maxZoom: 15, duration: 0})); };
  // ---- data ----
  function load() {
    return fetch("/api/karte/orte?lang=" + L(), {cache: "no-store"}).then(r => r.json()).then(j => {
      if (!j.ok) return; S.layers = j.layers || []; S.me = j.me || {}; S.store = j.store || ""; $("#eo").hidden = false;
      if (S.cur) { const L_ = S.layers.find(x => x.id === S.cur.L.id), p = L_ && L_.pts.find(x => x.id === S.cur.p.id); if (p) S.cur = {L: L_, p}; else closeCard(); }
      bar(); draw(); panel(); }).catch(() => {});
  }
  const own = () => S.layers.find(x => x.own);
  function took(r, er) {                                   // the answer of a change: the new own layer
    if (!r.ok) { if (r.layer) setOwn(r.layer); say(r.error || "?", er); return false; }
    if (r.layer) setOwn(r.layer);
    return true;
  }
  function setOwn(ly) { const i = S.layers.findIndex(x => x.own || x.id === ly.id); if (i >= 0) S.layers[i] = ly; else S.layers.unshift(ly); draw(); panel(); }
  const say = (t, where) => { const m = where || $("#eo-msg"); if (!m) return; m.hidden = !t; m.textContent = t ? "⚠ " + t : ""; };
  // ---- setting a place: the symbol bar ----
  function bar() {
    const box = $("#kq-map"); if (!box || !hasMap()) return;
    let b = $("#eo-bar"); if (b) b.remove();
    if (!S.me.admin) return;
    b = el("div"); b.id = "eo-bar"; b.appendChild(el("span", "eo-lb", "📌 " + T("Set")));
    SYM.forEach(s => { const k = btn("", "", () => pick({sym: s[0], em: s[1], name: T(s[2])}, k)); k.append(el("span", "", s[1]), el("small", "", T(s[2]))); k.dataset.sym = s[0]; b.appendChild(k); });
    const o = btn("", "", () => pick({sym: "custom", em: "", name: T("Own symbol")}, o)); o.append(el("span", "", "＋"), el("small", "", T("Own"))); o.dataset.sym = "custom"; b.appendChild(o);
    box.appendChild(b); b.hidden = !!$("#eo-card");
  }
  function pick(s, k) {
    if (ktBusy()) { hint(T("Finish drawing the route first."), null); return; }
    closeCard(); S.move = null; S.pick = s;
    document.querySelectorAll("#eo-bar button").forEach(x => x.classList.toggle("on", x === k));
    if (window.KT && !KT.busy) { KT.busy = true; EO.busy = true; }
    let inp = null;
    if (s.sym === "custom") { inp = el("input"); inp.type = "text"; inp.maxLength = 8; inp.placeholder = "🦌"; inp.id = "eo-emo"; inp.setAttribute("aria-label", T("Own symbol"));
      inp.oninput = () => { s.em = inp.value.trim(); }; }
    hint(T("Tap on the map:") + " " + (s.em || "") + " " + T("set {name}").replace("{name}", s.name), inp);
    if (inp) setTimeout(() => inp.focus(), 50);
  }
  function hint(txt, extra) {
    let h = $("#eo-hint"); if (!h) { h = el("div"); h.id = "eo-hint"; $("#kq-map").appendChild(h); }
    h.textContent = ""; const sp = el("span", "", txt); h.appendChild(sp); if (extra) h.appendChild(extra);
    const x = btn("✕ " + T("Cancel"), "", stopPick); x.id = "eo-hx"; h.appendChild(x);
    if (!S.pick && !S.move) setTimeout(() => { if (!S.pick && !S.move) stopPick(); }, 2500);
  }
  function stopPick() {
    S.pick = null; S.move = null; const h = $("#eo-hint"); if (h) h.remove();
    document.querySelectorAll("#eo-bar button.on").forEach(x => x.classList.remove("on"));
    if (EO.busy) { EO.busy = false; if (window.KT) KT.busy = false; }
    S.marks.forEach(mk => mk.setDraggable(false));
  }
  function place(ll) {
    const s = S.pick; if (!s) return;
    if (s.sym === "custom" && !s.em) { const i = $("#eo-emo"); if (i) { i.focus(); i.classList.add("bad"); } return; }
    stopPick();
    api({action: "add", lat: +ll.lat.toFixed(6), lon: +ll.lng.toFixed(6), sym: s.sym, emoji: s.em, name: s.sym === "custom" ? "" : s.name}).then(r => {
      if (!took(r)) return; const L_ = own(), p = L_ && L_.pts.find(x => x.id === r.id); if (p) { card(L_, p); edit(L_, p, true); } });
  }
  // ---- the card of one place ----
  function closeCard() {
    const c = $("#eo-card"); if (c) c.remove(); S.cur = null; if (S.move) stopPick();
    const b = $("#eo-bar"); if (b) b.hidden = false;
    document.querySelectorAll(".eo-m.sel").forEach(x => x.classList.remove("sel"));
  }
  function shell() {
    let c = $("#eo-card"); if (c) c.remove(); c = el("div"); c.id = "eo-card";
    const x = btn("✕", "x", closeCard); x.id = "eo-cx"; x.setAttribute("aria-label", T("Close")); c.appendChild(x);
    $("#kq-map").appendChild(c); const b = $("#eo-bar"); if (b) b.hidden = true; return c;
  }
  function card(L_, p) {
    if (!hasMap()) return;
    S.cur = {L: L_, p}; const c = shell();
    document.querySelectorAll(".eo-m.sel").forEach(x => x.classList.remove("sel"));
    const mk = S.marks.find(x => x._eo.L.id === L_.id && x._eo.p.id === p.id); if (mk) mk.getElement().classList.add("sel");
    if (p.photo) { const im = el("img"); im.alt = ""; im.src = "/karte/orte/foto/" + p.photo + ".jpg"; im.onerror = () => im.remove(); c.insertBefore(im, c.firstChild); }
    const bd = el("div", "bd"), h = el("h3"), dot = el("span", "dot"); dot.style.background = p.col || lcol(L_);
    h.append(el("span", "", p.em || "📍"), el("span", "nmx", p.name || symName(p)), dot); h.id = "eo-name"; bd.appendChild(h);
    bd.appendChild(el("div", "meta", [symName(p), [p.date ? T("set") + " " + fmtD(p.date) : "", p.by ? T("by") + " " + p.by : ""].filter(Boolean).join(" ")].filter(Boolean).join(" · ")));
    if (p.note) bd.appendChild(el("div", "note", p.note));
    const where = el("div", "meta"); where.id = "eo-where";
    const wt = () => "🎒 " + (L_.folder ? L_.folder + " › " : "") + L_.name + " · " + p.la.toFixed(5) + ", " + p.lo.toFixed(5);
    where.textContent = wt() + (p.ele != null ? " · " + Math.round(p.ele) + " " + T("m a.s.l.") : "");
    if (p.ele == null) fetch("/api/karte/orte/hoehe?lat=" + p.la + "&lon=" + p.lo, {cache: "no-store"}).then(r => r.json()).then(j => {
      if (j && j.ok && j.ele != null && S.cur && S.cur.p === p) where.textContent = wt() + " · " + Math.round(j.ele) + " " + T("m a.s.l."); }).catch(() => {});
    bd.appendChild(where);
    const er = el("div", "kt-err"); er.hidden = true; er.id = "eo-cerr";
    const row = el("div", "row");
    if (L_.own && S.me.admin) {
      const e = btn("✏️ " + T("Edit"), "", () => edit(L_, p)); e.id = "eo-edit";
      const mv = btn("✥ " + T("Move"), "sec", () => moveStart(L_, p)); mv.id = "eo-move";
      const del = btn("🗑 " + T("Delete"), "sec", () => ask(bd, L_, p)); del.id = "eo-del";
      row.append(e, mv, del);
    } else if (!L_.own && S.me.admin) {
      const cp = btn("📌 " + T("Copy into «My places»"), "sec", () => { cp.disabled = true; api({action: "copy", file: L_.id, id: p.id}).then(r => { cp.disabled = false;
        if (!took(r, er)) return; const O = own(), q = O && O.pts.find(x => x.id === r.id); if (q) card(O, q); }); }); cp.id = "eo-copy"; row.appendChild(cp);
    }
    const kn = $("#kt-new");
    if (kn && !kn.disabled && !ktBusy()) { const go = btn("🥾 " + T("Start a tour here"), "sec", () => { closeCard(); kn.click();
      map().then(m => { m.jumpTo({center: [p.lo, p.la]}); let k = 0;           // the tours take their map a moment later: until the point is there
        const go = () => { if (!(window.KT && KT.busy) || document.querySelector(".kt-pt") || k++ > 20) return; tapAt(m, p.la, p.lo); setTimeout(go, 300); };
        setTimeout(go, 100); }); }); go.id = "eo-tour"; row.appendChild(go); }
    if (row.children.length) bd.appendChild(row);
    bd.appendChild(er); c.appendChild(bd);
    return c;
  }
  function ask(bd, L_, p) {
    if (bd.querySelector(".ask")) return;
    const a = el("div", "ask"); a.id = "eo-ask"; a.appendChild(el("b", "", T("Delete «{name}»? It cannot be undone here.").replace("{name}", p.name || symName(p))));
    const er = el("div", "kt-err"); er.hidden = true;
    const y = btn("🗑 " + T("Yes, delete"), "red", () => { y.disabled = true; api({action: "delete", id: p.id, v: p.v}).then(r => { y.disabled = false; if (took(r, er)) closeCard(); }); }); y.id = "eo-yes";
    const n = btn(T("No"), "sec", () => a.remove()); n.id = "eo-no";
    const r = el("div", "row"); r.append(y, n); a.append(r, er); bd.appendChild(a); a.scrollIntoView({block: "nearest"});
  }
  function moveStart(L_, p) {
    const mk = S.marks.find(x => x._eo.L.id === L_.id && x._eo.p.id === p.id); if (!mk) return;
    const c = $("#eo-card"); if (c) c.remove(); S.cur = {L: L_, p}; S.move = {L: L_, p, mk};
    if (window.KT && !KT.busy) { KT.busy = true; EO.busy = true; }
    mk.setDraggable(true); mk.getElement().classList.add("sel");
    mk.on("dragend", () => { if (S.move && S.move.mk === mk) { const ll = mk.getLngLat(); moveTo(ll.lat, ll.lng); } });
    hint(T("Drag the symbol or tap the new place."), null);
  }
  function moveTo(la, lo) {
    const M = S.move; if (!M) return; stopPick();
    api({action: "move", id: M.p.id, v: M.p.v, lat: +la.toFixed(6), lon: +lo.toFixed(6)}).then(r => { const ok_ = took(r);
      const O = own(), q = O && O.pts.find(x => x.id === M.p.id); if (q) card(O, q); if (!ok_ && q) say(r.error, $("#eo-cerr")); });
  }
  // ---- edit ----
  function edit(L_, p, fresh) {
    const c = shell(); S.cur = {L: L_, p}; const bd = el("div", "bd eo-ed"); c.appendChild(bd);
    bd.appendChild(el("h3", "", "✏️ " + T("Edit place")));
    const lab = (t, f) => { const l = el("label", "", t); if (f) { f.id = f.id || "eo-f-" + Math.random().toString(36).slice(2, 7); l.htmlFor = f.id; } bd.appendChild(l); };
    const n = el("input"); n.type = "text"; n.maxLength = 80; n.value = p.name || ""; n.id = "eo-ename"; lab(T("Name"), n); bd.appendChild(n);
    const st = {sym: p.sym, em: p.em, col: p.col || "", photo: p.photo || "", pname: ""};
    lab(T("Symbol")); const sy = el("div", "syms");
    const own_ = el("input"); own_.type = "text"; own_.maxLength = 8; own_.className = "emo"; own_.placeholder = "＋"; own_.setAttribute("aria-label", T("Own symbol"));
    const mark = () => sy.querySelectorAll("button").forEach(x => x.classList.toggle("on", x.dataset.sym === st.sym));
    SYM.forEach(s => { const b = btn(s[1], "sec", () => { st.sym = s[0]; st.em = s[1]; own_.value = ""; mark(); }); b.title = T(s[2]); b.dataset.sym = s[0]; sy.appendChild(b); });
    if (st.sym === "custom") own_.value = st.em || "";
    own_.oninput = () => { const v = own_.value.trim(); if (v) { st.sym = "custom"; st.em = v; mark(); } };
    sy.appendChild(own_); bd.appendChild(sy); mark();
    lab(T("Colour")); const co = el("div", "cols");
    COLS.forEach(k => { const b = btn("", k === st.col ? "on" : "", () => { st.col = k; co.querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b)); }); b.style.background = k; b.title = k; co.appendChild(b); });
    bd.appendChild(co);
    const t = el("textarea"); t.maxLength = 1000; t.value = p.note || ""; t.id = "eo-enote"; lab(T("Note"), t); bd.appendChild(t);
    lab(T("Photo")); const ph = el("div", "ph"), pim = el("img"); pim.alt = ""; pim.hidden = true;
    const showPh = () => { pim.hidden = !st.photo; if (st.photo) { pim.src = "/karte/orte/foto/" + st.photo + ".jpg"; pim.onerror = () => { pim.hidden = true; }; } rm.hidden = !st.photo; };
    const fi = el("input"); fi.type = "file"; fi.accept = "image/*"; fi.hidden = true; fi.id = "eo-efile";
    const pb = btn("📷 " + T("Choose photo"), "sec", () => fi.click()); pb.id = "eo-ephoto";
    const rm = btn("✕", "sec", () => { st.photo = ""; showPh(); }); rm.title = T("Remove");
    const er = el("div", "kt-err"); er.hidden = true;
    fi.onchange = () => { const f = fi.files && fi.files[0]; fi.value = ""; if (!f) return; pb.disabled = true; pb.textContent = "… " + T("Uploading");
      upload(f, n.value || p.name || "Ort").then(id => { st.photo = id; showPh(); }).catch(e => say(String(e && e.message || e), er))
        .finally(() => { pb.disabled = false; pb.textContent = "📷 " + T("Choose photo"); }); };
    ph.append(pim, pb, rm, fi); bd.appendChild(ph); showPh();
    bd.appendChild(el("div", "meta", (p.date ? T("set") + " " + fmtD(p.date) + " · " : "") + T("saved in") + " 🎒 " + (L_.folder ? L_.folder + " › " : "") + L_.name));
    const sv = btn("💾 " + T("Save"), "", () => {
      if (st.sym === "custom" && !st.em) { say(T("Please choose a symbol."), er); return; }
      sv.disabled = true;
      api({action: "edit", id: p.id, v: p.v, name: n.value, sym: st.sym, emoji: st.em, color: st.col, note: t.value, photo: st.photo}).then(r => { sv.disabled = false;
        if (!took(r, er)) return; const O = own(), q = O && O.pts.find(x => x.id === p.id); if (q) card(O, q); else closeCard(); }); }); sv.id = "eo-esave";
    const ca = btn(T("Cancel"), "sec", () => { const O = own(), q = O && O.pts.find(x => x.id === p.id); if (q) card(O, q); else closeCard(); }); ca.id = "eo-ecancel";
    const r = el("div", "row"); r.style.marginTop = "10px"; r.append(sv, ca); bd.append(r, er);
    if (fresh) setTimeout(() => { try { n.focus(); n.select(); } catch (e) {} }, 60);
  }
  // a photo: made smaller in the browser (at most 1600 px, JPEG), then into the backpack folder like any upload
  function shrink(f) {
    return new Promise((ok, no) => { const u = URL.createObjectURL(f), im = new Image();
      im.onload = () => { const s = Math.min(1, 1600 / Math.max(im.naturalWidth, im.naturalHeight, 1)), cv = document.createElement("canvas");
        cv.width = Math.max(1, Math.round(im.naturalWidth * s)); cv.height = Math.max(1, Math.round(im.naturalHeight * s));
        cv.getContext("2d").drawImage(im, 0, 0, cv.width, cv.height); URL.revokeObjectURL(u);
        cv.toBlob(b => b ? ok(b) : no(new Error(T("This picture cannot be read here."))), "image/jpeg", 0.85); };
      im.onerror = () => { URL.revokeObjectURL(u); no(new Error(T("This picture cannot be read here."))); }; im.src = u; });
  }
  async function upload(f, name) {
    const b = await shrink(f);
    const pr = await api({action: "prep"}); if (!pr.ok) throw new Error(pr.error || "?");
    const P = (u, d) => fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))}).then(r => r.json());
    const nm = (T("Place") + " " + String(name).replace(/[\\/:*?"<>|]+/g, " ").trim()).slice(0, 80) + ".jpg";
    const s = await P("/api/tausch", {action: "start", name: nm, size: b.size, area: "all", folder: pr.folder, lastmod: Date.now()});
    if (!s.ok) throw new Error(s.error || "?");
    const c = await fetch("/api/tausch/chunk?id=" + s.id + "&off=0&lang=" + L(), {method: "POST", headers: {"Content-Type": "application/octet-stream"}, body: b}).then(r => r.json());
    if (!c.ok) throw new Error(c.error || "?");
    const e = await P("/api/tausch", {action: "finish", id: s.id});
    if (!e.ok || !e.file) throw new Error(e.error || "?");
    return e.file.id;
  }
  // ---- the list of layers under the map ----
  function panel() {
    const P = $("#eo-items"); if (!P) return; P.textContent = "";
    $("#eo-h").textContent = T("Own places");
    $("#eo-sub").textContent = T("Layers from the digital backpack – every file with places (GeoJSON, GPX, KML) appears here by itself.");
    if (S.store) P.appendChild(el("div", "kt-err", "⚠ " + S.store));
    if (!S.layers.length) P.appendChild(el("p", "kt-note", T("No places yet.") + (S.me.admin && hasMap() ? " " + T("Choose a symbol in the bar on the map, then tap the place.") : "")));
    S.layers.forEach(L_ => {
      const r = el("div", "eo-ly"); r.dataset.id = L_.id;
      const on = shown(L_), sw = btn("", "eo-sw" + (on ? " on" : ""), () => { if (S.off.has(L_.id)) S.off.delete(L_.id); else S.off.add(L_.id); lsSet("eo-off", S.off); draw(); panel(); });
      sw.setAttribute("role", "switch"); sw.setAttribute("aria-checked", on ? "true" : "false"); sw.setAttribute("aria-label", L_.name); sw.disabled = !!L_.err || !!L_.hidden;
      const n = (L_.pts || []).length, nl = (L_.lines || []).length;
      const tx = el("span"); tx.append(el("b", "", L_.name));
      const info = L_.err ? ["⚠ " + L_.err] : [n + " " + T(n === 1 ? "place" : "places"), nl ? nl + " " + T(nl === 1 ? "line" : "lines") : "",
        "🎒 " + (L_.area === "mine" ? T("Only me") : (L_.folder || T("For everyone"))), L_.own ? (S.me.admin ? "✏️ " + T("edit here") : "") : T("only to look at"),
        L_.hidden ? "🚫 " + T("hidden for everyone") : ""];
      tx.appendChild(el("small", "", info.filter(Boolean).join(" · ")));
      tx.onclick = () => { if (shown(L_)) { fit(L_); $("#kq-map").scrollIntoView({behavior: "smooth", block: "center"}); } };
      const ex = el("div", "ex");
      if (S.me.down && !L_.err && (n || nl)) ["gpx", "kml"].forEach(x => { const a = el("a", "btn sec", "⬇ " + x.toUpperCase()); a.href = "/karte/orte/x/" + L_.id + "." + x; a.setAttribute("download", ""); ex.appendChild(a); });
      if (S.me.admin && !L_.own) { const hb = btn(L_.hidden ? "👁 " + T("Show for everyone") : "🚫 " + T("Hide for everyone"), "sec", () => { hb.disabled = true;
        api({action: "hide", file: L_.id, hide: !L_.hidden}).then(x => { if (!x.ok) say(x.error); load(); }); }); hb.className = "sec eo-hide"; ex.appendChild(hb); }
      if (S.me.admin && L_.own && (L_.hist || []).length) { const vb = btn("🕘 " + T("Versions") + " (" + L_.hist.length + ")", "sec", () => { S.hist = !S.hist; panel(); }); vb.id = "eo-vers"; ex.appendChild(vb); }
      r.append(sw, el("span", "ic", L_.own ? "📌" : nl ? "🥾" : "📍"), tx, ex); P.appendChild(r);
      if (L_.own && S.hist && S.me.admin) { const hv = el("div", "eo-hist"); hv.id = "eo-hist";
        hv.appendChild(el("div", "kt-note", T("Earlier versions of «My places» (the last 20). Taking one back saves it as the newest version.")));
        (L_.hist || []).forEach(h => { const q = el("div", "eo-hv"); q.append(el("span", "", fmtD(h.t * 1000) + (h.by ? " · " + h.by : "") + (h.n != null ? " · " + h.n + " " + T(h.n === 1 ? "place" : "places") : "")),
          btn("↶ " + T("Take back"), "sec", () => api({action: "restore", v: h.v}).then(x => { if (took(x)) { S.hist = false; panel(); } }))); hv.appendChild(q); });
        P.appendChild(hv); }
    });
    const C = $("#eo-chips"); C.textContent = ""; const cnt = {};
    S.layers.forEach(L_ => { if (shown(L_)) (L_.pts || []).forEach(p => { cnt[p.em] = (cnt[p.em] || 0) + 1; }); });
    const ks = Object.keys(cnt); $("#eo-chh").hidden = !ks.length;
    ks.forEach(e => { const b = btn(e + " " + cnt[e], "sec" + (S.symOff.has(e) ? " off" : ""), () => { if (S.symOff.has(e)) S.symOff.delete(e); else S.symOff.add(e); lsSet("eo-symoff", S.symOff); draw(); panel(); });
      b.setAttribute("aria-pressed", S.symOff.has(e) ? "false" : "true"); C.appendChild(b); });
    $("#eo-chh").textContent = T("Show / hide symbols");
    $("#eo-tip").textContent = T("New places from on the way: load a GPX or KML file (e.g. an export of the swisstopo app) into the 🎒 digital backpack – it appears here as its own layer.");
  }
  const start = () => { if (!$("#eo")) return;
    load().then(() => { const id = new URLSearchParams(location.search).get("orte");
      if (id && /^[0-9a-f]{16}$/.test(id)) { const L_ = S.layers.find(x => x.id === id);
        if (L_) { if (S.off.delete(id)) { lsSet("eo-off", S.off); draw(); panel(); } fit(L_); setTimeout(() => { const b = $("#kq-map"); if (b) b.scrollIntoView({block: "center"}); }, 300); } } }); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
  window.addEventListener("pageshow", e => { if (e.persisted) load(); });
})();
"""
EO_TZ_JS = r"""<script>
// 639zzzzo: files with places in the digital backpack - «🗺️ auf Karte», the folder «🗺️ Karte», a small sheet with «Auf der Karte zeigen».
// Only through the hooks tzCard / tzOpen (639zzc / 639zzzzv); chained, so no part replaces the other.
(function () {
  if (window.EOTZ) return; window.EOTZ = 1;
  const TX = /*EOTZTX*/{}, FOLDER = /*EOFOLDER*/"";
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const T = k => (TX[L()] || {})[k] || k;
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const GEO = /\.(gpx|kml|geojson)$/i;
  const st = document.createElement("style");
  st.textContent = ".eo-bdg{display:inline-block;margin:2px 9px 6px;padding:2px 8px;border-radius:9px;background:#2f7cf6;color:#fff!important;font-size:11.5px;font-weight:700;text-decoration:none;white-space:nowrap}"
    + ".tz-list .eo-bdg{margin:0 10px 4px}.eo-fhint{margin:0 0 10px;padding:9px 11px;border-radius:12px;border:1px solid #2f7cf680;background:#2f7cf61a;font-size:13.5px}"
    + ".eo-sh{text-align:center;padding:10px}.eo-sh .ic{font-size:54px}.eo-sh p{margin:8px auto;max-width:420px}.eo-sh a.btn{display:inline-flex;min-height:44px;align-items:center;margin-top:6px}";
  document.head.appendChild(st);
  let info = null;                                          // the layers of the map: «3 Orte · 1 Linie»
  const getInfo = () => info || (info = fetch("/api/karte/orte?lang=" + L(), {cache: "no-store"}).then(r => r.json()).then(j => {
    const o = {}; (j && j.layers || []).forEach(l => { o[l.id] = l; }); return o; }).catch(() => ({})));
  const cnt = l => !l ? "" : l.err ? "⚠ " + l.err : [(l.pts || []).length + " " + T((l.pts || []).length === 1 ? "place" : "places"),
    (l.lines || []).length ? (l.lines || []).length + " " + T((l.lines || []).length === 1 ? "line" : "lines") : ""].filter(Boolean).join(" · ");
  let htm = 0;
  function folderHint() {                                   // inside «🗺️ Karte»: what this folder is
    clearTimeout(htm); htm = setTimeout(() => {
      const cr = document.getElementById("tz-crumb"), inF = !!(cr && !cr.hidden && FOLDER && cr.textContent.indexOf(FOLDER) >= 0);
      let h = document.getElementById("eo-fhint");
      if (!inF) { if (h) h.remove(); return; }
      if (!h) { h = E("div", "eo-fhint", "🗺️ " + T("The map fills this folder: «My places» and the photos of the places. Other files with places (GPX, KML, GeoJSON) may lie anywhere in the backpack."));
        h.id = "eo-fhint"; cr.after(h); } }, 30);
  }
  const mine = {
    card(f, it, tx, th) {
      folderHint();
      if (!f || !GEO.test(f.name || "")) return;
      if (th && !th.querySelector("img")) th.textContent = /\.geojson$/i.test(f.name) ? "📌" : "🗺️";
      const a = E("a", "eo-bdg", "🗺️ " + T("on the map")); a.href = "/karte?orte=" + f.id; a.title = T("Show on the map"); a.dataset.eo = f.id;
      a.addEventListener("click", e => e.stopPropagation()); tx.appendChild(a);
      getInfo().then(o => { const l = o[f.id]; if (l && !l.err) a.textContent = "🗺️ " + cnt(l); else if (l && l.err) a.textContent = "🗺️ ⚠"; });
    },
    open(f) {
      if (!f || !GEO.test(f.name || "")) return false;
      const ov = E("div", "tz-lb"), bar = E("div", "bar"), bd = E("div", "bd"), x = E("button", "sec", "✕");
      x.type = "button"; x.onclick = () => ov.remove(); bar.appendChild(E("b", "", f.name));
      if (f.dl) { const d = E("a", "btn", "⬇ " + T("Download")); d.href = "/tausch/dl/" + f.id; d.setAttribute("download", ""); bar.appendChild(d); }
      bar.appendChild(x);
      const sh = E("div", "eo-sh"); sh.id = "eo-sheet"; sh.append(E("div", "ic", /\.geojson$/i.test(f.name) ? "📌" : "🗺️"), E("p", "", T("This file shows its places on the offline map, as its own layer.")));
      const c = E("p", "mut", "…"); sh.appendChild(c);
      const go = E("a", "btn", "🗺️ " + T("Show on the map")); go.href = "/karte?orte=" + f.id; go.id = "eo-go"; sh.appendChild(go);
      getInfo().then(o => { c.textContent = cnt(o[f.id]) || T("Not on the map (hidden or not readable)."); });
      bd.appendChild(sh); ov.append(bar, bd); ov.addEventListener("click", e => { if (e.target === ov || e.target === bd) ov.remove(); });
      document.body.appendChild(ov); return true;
    },
  };
  let oc = typeof window.tzCard === "function" ? window.tzCard : null, oo = typeof window.tzOpen === "function" ? window.tzOpen : null;
  const card = function (f, it, tx, th) { if (oc) { try { oc(f, it, tx, th); } catch (e) {} } try { mine.card(f, it, tx, th); } catch (e) {} };
  const open = function (f, H) { try { if (mine.open(f, H)) return true; } catch (e) {} return oo ? oo(f, H) : false; };
  try {
    Object.defineProperty(window, "tzCard", {configurable: true, get: () => card, set: v => { if (v !== card) oc = typeof v === "function" ? v : null; }});
    Object.defineProperty(window, "tzOpen", {configurable: true, get: () => open, set: v => { if (v !== open) oo = typeof v === "function" ? v : null; }});
  } catch (e) {}
  window.addEventListener("pageshow", () => { info = null; });
})();
</script>
"""
_EO_TZ_KEYS = ("place", "places", "line", "lines", "on the map", "Show on the map", "Download", "This file shows its places on the offline map, as its own layer.",
               "Not on the map (hidden or not readable).",
               "The map fills this folder: «My places» and the photos of the places. Other files with places (GPX, KML, GeoJSON) may lie anywhere in the backpack.")
_EO_KT_AT = '<section class="kt" id="kt" hidden>'
_kq_page_639zzzzo = kq_page


# wraps: kq_page
def kq_page():                                              # + 639zzzzo: «📌 Eigene Orte» above the tours
    html = _kq_page_639zzzzo()
    if 'id="eo"' in html or "</head>" not in html or "</body>" not in html:
        return html
    if html.count(_EO_KT_AT) == 1:
        html = html.replace(_EO_KT_AT, EO_HTML + _EO_KT_AT, 1)
    elif html.count("</main>") == 1:
        html = html.replace("</main>", EO_HTML + "</main>", 1)
    else:
        return html
    cf = {"syms": [list(s) for s in EO_SYMS], "cols": list(EO_COLS)}
    js = (EO_JS.replace("/*EOTX*/{}", json.dumps(eo_tx(), ensure_ascii=False).replace("</", "<\\/"), 1)
          .replace("/*EOCF*/{}", json.dumps(cf, ensure_ascii=False), 1))
    return html.replace("</head>", "<style>" + EO_CSS + "</style></head>", 1).replace("</body>", "<script>" + js + "</script></body>", 1)


_tausch_page_html_639zzzzo = tausch_page_html


# wraps: tausch_page_html
def tausch_page_html():                                     # + 639zzzzo: «🗺️ auf Karte» on files with places (hooks tzCard / tzOpen)
    out = _tausch_page_html_639zzzzo()
    i = out.rfind("</body>")
    if i < 0 or "window.EOTZ" in out:
        return out
    js = (EO_TZ_JS.replace("/*EOTZTX*/{}", json.dumps(eo_tx(_EO_TZ_KEYS), ensure_ascii=False).replace("</", "<\\/"), 1)
          .replace('/*EOFOLDER*/""', json.dumps(EO_FOLDER, ensure_ascii=False), 1))
    return out[:i] + js + out[i:]


# ---- the manual: one point after the tours (5 languages) ------------------------------------------------------------------------
_HELP_EO = {
    "de": ("📌 Eigene Orte", "(Mehr → 🗺 Karte): Hütte, Feuerstelle, Velo, Zelt, Auto, Wasser, WC, Gefahr, Punkt oder ein eigenes Emoji in der Leiste «📌 Setzen» wählen und auf die Karte tippen (nur der Admin und «Dateien: alles verwalten»); antippen zeigt Foto, Notiz, Datum und Höhe (mit den Höhendaten Schweiz), «✥ Verschieben», «🗑 Löschen» fragt in der Seite nach. Die Orte liegen im Digitalen Rucksack in «🗺️ Karte/Meine Orte.geojson» (die letzten 20 Versionen bleiben, «🕘 Versionen»). Jede GPX-, KML- oder GeoJSON-Datei im Rucksack (z. B. Export der swisstopo-App) erscheint als eigene Ebene; ein / aus pro Gerät, der Admin kann eine Ebene für alle ausblenden; Export als GPX oder KML. Alle Benutzer sehen die Orte auf der Karte."),
    "en": ("📌 Own places", "(More → 🗺 Map): choose hut, fireplace, bike, tent, car, water, toilet, danger, point or an own emoji in the bar “📌 Set” and tap the map (only the administrator and “Files: manage all”); a tap shows photo, note, date and height (with the height data of Switzerland), “✥ Move”, “🗑 Delete” asks inside the page. The places are kept in the digital backpack in “🗺️ Karte/Meine Orte.geojson” (the last 20 versions stay, “🕘 Versions”). Every GPX, KML or GeoJSON file in the backpack (e.g. an export of the swisstopo app) appears as its own layer; on / off per device, the administrator can hide a layer for everyone; export as GPX or KML. All users see the places on the map."),
    "fr": ("📌 Lieux personnels", "(Plus → 🗺 Carte) : choisir cabane, foyer, vélo, tente, voiture, eau, WC, danger, point ou un emoji perso dans la barre « 📌 Placer » et toucher la carte (seulement l’administrateur et « Fichiers : tout gérer ») ; un toucher montre photo, note, date et altitude (avec les données d’altitude de la Suisse), « ✥ Déplacer », « 🗑 Supprimer » demande dans la page. Les lieux sont gardés dans le sac à dos numérique dans « 🗺️ Karte/Meine Orte.geojson » (les 20 dernières versions restent). Chaque fichier GPX, KML ou GeoJSON du sac (p. ex. export de l’app swisstopo) apparaît comme calque ; activé / désactivé par appareil, l’administrateur peut masquer un calque pour tous ; export en GPX ou KML. Tous les utilisateurs voient les lieux sur la carte."),
    "it": ("📌 Luoghi propri", "(Altro → 🗺 Mappa): scegliere capanna, focolare, bici, tenda, auto, acqua, WC, pericolo, punto o un emoji proprio nella barra «📌 Posa» e toccare la mappa (solo l’amministratore e «File: gestire tutto»); un tocco mostra foto, nota, data e quota (con i dati di quota della Svizzera), «✥ Sposta», «🗑 Elimina» chiede nella pagina. I luoghi stanno nello zaino digitale in «🗺️ Karte/Meine Orte.geojson» (restano le ultime 20 versioni). Ogni file GPX, KML o GeoJSON nello zaino (ad es. esportato dall’app swisstopo) appare come livello proprio; acceso / spento per dispositivo, l’amministratore può nascondere un livello a tutti; esportazione GPX o KML. Tutti gli utenti vedono i luoghi sulla mappa."),
    "rm": ("📌 Agens lieus", "(Dapli → 🗺 Charta): tscherner tegia, fuaina, velo, tenda, auto, aua, WC, privel, punct u in agen emoji en la trav «📌 Metter» e tutgar la charta (mo l’administratur e «Datotecas: administrar tut»); tutgar mussa foto, notizia, data ed autezza (cun las datas d’autezza da la Svizra), «✥ Spustar», «🗑 Stizzar» dumonda en la pagina. Ils lieus èn en il satgados digital en «🗺️ Karte/Meine Orte.geojson» (las ultimas 20 versiuns restan). Mintga datoteca GPX, KML u GeoJSON en il satgados (p.ex. export da l’app swisstopo) cumpara sco agen nivel; en / ora per apparat, l’administratur po zuppentar in nivel per tuts; export sco GPX u KML. Tut ils utilisaders vesan ils lieus sin la charta."),
}


def _help_eo(doc, lang):
    h_, x_ = _HELP_EO[lang]
    anchor = _HELP_KT[lang][0]
    if h_ in doc or anchor not in doc:
        return doc
    from html import escape as _e
    i = doc.find("</li>", doc.find(anchor))
    return doc if i < 0 else doc[:i + 5] + f"<li><b>{h_}</b> {_e(x_, quote=False)}</li>" + doc[i + 5:]


_hp_en_eo = HELP_PAGE.find('<div lang="en">')
if _hp_en_eo > 0:
    HELP_PAGE = _help_eo(HELP_PAGE[:_hp_en_eo], "de") + _help_eo(HELP_PAGE[_hp_en_eo:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_eo(HELP_X[_L], _L)


# ---- self-test (werkzeuge/orte_test.py tests the writing, the rights, the conflicts and the pages in the browser) -----------------
def eo_selftest():
    gj = json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": "a1", "geometry": {"type": "Point", "coordinates": [7.72, 46.5, 1590]}, "properties": {"name": "Hütte <b>", "symbol": "hut", "color": "#8D5A2B", "note": "a\nb\x00"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [7.7, 46.49]}, "properties": {"emoji": "🦌", "photo": "../x"}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [999, 46.49]}, "properties": {}},
        {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[7.7, 46.49], [7.71, 46.5], ["x", 1]]}, "properties": {}},
        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[7.7, 46.49], [7.71, 46.5], [7.7, 46.5], [7.7, 46.49]]]}}]}).encode()
    r = eo_geojson(gj)
    assert len(r["pts"]) == 2 and len(r["lines"]) == 2 and r["lines"][0] == [[7.7, 46.49], [7.71, 46.5]], r
    a, b = r["pts"]
    assert a["id"] == "a1" and a["name"] == "Hütte <b>" and a["sym"] == "hut" and a["em"] == "🛖" and a["col"] == "#8d5a2b" and a["note"] == "a\nb" and a["ele"] == 1590
    assert b["id"] == "n1" and b["sym"] == "custom" and b["em"] == "🦌" and b["photo"] == ""
    for bad, why in ((b"[1,2]", "GeoJSON"), (b"{", "could not be read"), (b"[" * 100000 + b"]" * 100000, "could not be read"), (b"\xff\xfe", "could not be read")):
        try:
            eo_geojson(bad)
            raise AssertionError("accepted: %r" % bad[:20])
        except EOError as e:
            assert why in str(e), (bad[:20], str(e))
    wp = kt_parse(b'<gpx><wpt lat="46.5" lon="7.7"><name>W</name></wpt></gpx>', "w.gpx", need_route=False)
    assert wp["pts"] == [] and wp["wps"][0]["name"] == "W"
    for args, why in (((b'<gpx></gpx>', "x.gpx", False), "No places"), ((b'<gpx><wpt lat="46.5" lon="7.7"/></gpx>',), "No route")):
        try:
            kt_parse(*args)
            raise AssertionError("accepted")
        except KTError as e:
            assert why in str(e), str(e)
    assert _eo_sym("x", "⛺") == ("tent", "⛺") and _eo_sym("", "") == ("pin", "📍") and _eo_sym("custom", "<b>") == ("custom", "b") and _eo_col("red") == ""
    g = eo_gpx("A & B", r)
    k = eo_kml("A & B", r)
    back = kt_parse(g, "x.gpx", need_route=False)
    assert b"A &amp; B" in g and "Hütte &lt;b&gt;".encode() in k and [w["name"] for w in back["wps"]] == ["Hütte <b>", "🦌"] and len(back["pts"]) == 6 and b"<desc>a&#10;b</desc>" in g
    assert len(kt_parse(k, "x.kml", need_route=False)["wps"]) == 2
    assert tausch_clean_name(EO_FOLDER, folder=True)[0] == EO_FOLDER and tausch_clean_name(EO_FILE)[0] == EO_FILE
    pg = kq_page()
    assert pg.count('id="eo"') == 1 and pg.find('id="eo"') < pg.find('id="kt"') and "window.EO = " in pg and "/*EOTX*/" not in pg and '"Eigene Orte"' in pg
    assert "confirm(" not in EO_JS and "prompt(" not in EO_JS and "innerHTML" not in EO_JS and "innerHTML" not in EO_TZ_JS and "https://" not in EO_JS + EO_TZ_JS
    assert "tzCard = function" not in EO_TZ_JS and "defineProperty(window, \"tzCard\"" in EO_TZ_JS and "/*EOCSS*/" not in EO_CSS
    tp = tausch_page_html()
    assert tp.count("window.EOTZ = 1") == 1 and "/*EOTZTX*/" not in tp and json.dumps(EO_FOLDER, ensure_ascii=False) in tp
    for p_ in ("/api/karte/orte", "/karte/orte/foto/0123456789abcdef.jpg", "/karte/orte/x/0123456789abcdef.gpx", "/api/karte/orte/hoehe"):
        assert role_allows("kid", p_, "GET", {}) and role_allows("view", p_, "GET", {}), p_
    assert not role_allows("family", "/api/karte/orte", "POST", {"action": "add"}) and role_allows("custom", "/api/karte/orte", "POST", {}, {"files_admin"})
    assert all("ß" not in v[0] and all(v) for v in _HX_EO.values()) and all(s[2] in _HX_EO for s in EO_SYMS)
    assert _HELP_EO["de"][0] in HELP_PAGE and _HELP_EO["en"][0] in HELP_PAGE
    return "own places: GeoJSON / GPX / KML reader, export, pages, rights"


SELFTEST_EXTRA.append(("Own places on the map (639zzzzo)", eo_selftest))
