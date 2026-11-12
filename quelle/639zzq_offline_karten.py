#@ MoveEye – Teil 639zzq: Offline-Karte Schweiz – Vektorkarte (PMTiles) + Ortssuche einmal laden (Admin, Release-Asset, Grösse + sha256, freier Platz), Kacheln lokal aus der Datei (Python liest nur die nötigen Bytes), MapLibre GL JS lokal; Karte beim Standort, bei den Aufnahmen, auf /karte und bei «Ort von der Karte» des Simulators. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Idee 12 des Besitzers «Offline-Karten Schweiz» (09.11.2026): Karten ohne Internet für MoveEye und den Simulator.
#   * Drei Dateien an einem Release «KQ_TAG» (nie «latest», nie im Git), gebaut vom Workflow «Offline-Karten»
#     (werkzeuge/karten/paket.py): karte-ch-N.pmtiles (Protomaps-Basiskarte, Schweiz + Liechtenstein, ein PMTiles-v3-File),
#     karte-web-N.zip (MapLibre GL JS, Stil, Schriften, Symbole, LIZENZEN.txt) und orte-ch-N.sqlite.gz (Ortssuche).
#     Grösse + sha256 jeder Datei stehen hier in der (signierten) Hauptdatei (KQ_FILES, `paket.py --eintragen pins.txt`);
#     size 0 = noch nicht freigegeben («kommt mit einem Update»).
#   * Laden nur durch den Admin (Einstellungen → Standort → «🗺 Offline-Karte Schweiz», auch auf /karte): Frage mit Grösse,
#     zuerst der freie Platz auf der Speicherkarte (alle Dateien + Entpacktes + tausch_free_gb, Standard 2 GB, bio_free_need),
#     Fortsetzen (.part + Range), Fortschritt, Prüfsumme jeder Datei VOR dem Einschalten (bio_fetch / piper_check_file), dann
#     ein fertiger Ordner DATA_DIR/karte (neuer Ordner, erst am Schluss umbenannt), Marke karte.ok. «🗑 Entfernen» löscht alles.
#     Bis dahin bleibt alles wie bisher (Karten aus dem Internet, wenn «map_online» an ist).
#   * Kacheln: GET /karte/t/<tag>/<z>/<x>/<y>.mvt – Python liest Kopf, Wurzel- und Blattverzeichnis (gzip) und genau die
#     Bytes der Kachel (os.pread, nie die ganze Datei; höchstens KQ_LEAF_CACHE Blätter im Speicher) und schickt sie so, wie
#     sie in der Datei stehen (gzip -> Content-Encoding: gzip). Warum nicht pmtiles.js im Browser über Byte-Bereiche: eine
#     Anfrage pro Kachel statt Verzeichnis + Kachel (iPhone über WLAN / Tailscale), Browser-Cache pro Kachel (Tag in der
#     Adresse), die grosse Datei ist nicht als Ganzes abrufbar, und MapLibre braucht kein Zusatzprogramm.
#   * Browser: MapLibre GL JS aus karte-web (lazy, erst wenn eine Karte erscheint), Stil Protomaps «light» mit lokalen
#     Namen, Schriften nur Latein (fehlende Bereiche = leere Glyphen-Antwort). Keine Anfrage ins Internet.
#   * Wo: (a) Einstellungen → Standort: die Karte zum Antippen bekommt die Offline-Karte als Hintergrund, die Suche sucht
#     offline (Vorschläge beim Tippen); (b) Aufnahmen: die Karte der Orte und eine kleine Karte im Bildbetrachter, wenn die
#     Aufnahme einen Ort hat; (c) /karte: grosse Karte mit Suche, «Als Standort setzen» (Admin) und «🎮 Im Simulator öffnen»;
#     die Links «📍 …» (Status, Tagebuch) öffnen /karte statt openstreetmap.org; (d) Simulator → «Ort von der Karte»
#     (Steuerung «map», SIMMAP_JS): Offline-Karte statt swisstopo, Suche offline, «Diesen Ort laden» schickt wie bisher
#     «lat, lon, Name» an den Simulator (Steuerung ort_map -> set_place_text); Gebäude / Gelände lädt der Simulator weiter
#     selbst (Internet oder sein Zwischenspeicher). Push-Links (Diebstahl) bleiben openstreetmap.org (das Handy ist dann
#     oft nicht im Netz von MoveEye).
#   * Geteilte Teile unverändert: die Haken kommen per .replace in WEB_PAGE / SIM_PAGE / REC_PAGE (genau einmal, sonst
#     nichts; der Selbsttest prüft jeden Haken), die Rechte über VIEW_GET (ansehen / suchen für alle Angemeldeten, laden
#     und entfernen nur der Admin).
#   * Quellenangabe «© OpenStreetMap-Mitwirkende» sichtbar auf jeder Karte (eigene Zeile, nicht die einklappbare von MapLibre).
# Selbsttest kq_selftest; Tests werkzeuge/karten_test.py (Laden gut / falsch, Platz, Byte-Bereiche, Seiten im Browser in
# iPhone-Breite ohne Anfrage nach aussen, Suche, Standort per Tipp, Quellenangabe, Rechte; --echt mit den Release-Dateien).
# ----------------------------------------------------------------------------
import struct as _kq_struct
from bisect import bisect_right as _kq_bisect
from collections import OrderedDict as _KqOD

KQ_TAG = "karten-1"
KQ_MAXZOOM = 15
KQ_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/" + KQ_TAG + "/"}   # Tests: lokaler Server
# Werte aus werkzeuge/karten/paket.py (pins.txt des Workflows «Offline-Karten»); size 0 = noch nicht freigegeben
KQ_FILES = {
    "tiles": {"name": "karte-ch-1.pmtiles", "size": 0, "sha256": "", "unpacked": 0},
    "web": {"name": "karte-web-1.zip", "size": 0, "sha256": "", "unpacked": 0},
    "orte": {"name": "orte-ch-1.sqlite.gz", "size": 0, "sha256": "", "unpacked": 0},
}
KQ_MAX = {"tiles": 2000 * 1000 * 1000, "web": 60 * 1000 * 1000, "orte": 300 * 1000 * 1000}   # harte Obergrenzen (auch entpackt)
KQ_NAME_RE = {"tiles": r"karte-ch-\d{1,3}\.pmtiles", "web": r"karte-web-\d{1,3}\.zip", "orte": r"orte-ch-\d{1,3}\.sqlite\.gz"}
KQ_LEAF_CACHE = 48
KQ_DL = {"running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": False, "phase": ""}
KQ_RT = {"pm": None, "db": None, "lock": threading.Lock(), "ok_t": 0.0, "ok": False}


def kq_dir():
    return os.path.join(DATA_DIR, "karte")


def kq_dl_dir():
    return os.path.join(DATA_DIR, "karte_dl")


def kq_pinned():
    """every file with exact size, sha256 and name - nothing else is ever downloaded"""
    for r_, f in KQ_FILES.items():
        if not (isinstance(f.get("size"), int) and 0 < f["size"] <= KQ_MAX[r_] and re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or ""))
                and isinstance(f.get("unpacked"), int) and 0 <= f["unpacked"] <= KQ_MAX[r_] and re.fullmatch(KQ_NAME_RE[r_], f.get("name") or "")):
            return False
    return KQ_FILES["web"]["unpacked"] > 0 and KQ_FILES["orte"]["unpacked"] > 0


def kq_total():
    return sum(f["size"] for f in KQ_FILES.values())


def kq_need_disk():
    """bytes on the card after the install: the map file, the unpacked web package and the unpacked place index"""
    return KQ_FILES["tiles"]["size"] + KQ_FILES["web"]["unpacked"] + KQ_FILES["orte"]["unpacked"]


def kq_installed():
    """checked once after the download (marker karte.ok: tag + every sha256), the files still there with their size"""
    now = time.time()
    if now - KQ_RT["ok_t"] < 2.0:
        return KQ_RT["ok"]
    ok = False
    if kq_pinned():
        d_ = kq_dir()
        try:
            with open(os.path.join(d_, "karte.ok"), encoding="utf-8") as fh:
                m = json.load(fh)
            ok = (isinstance(m, dict) and m.get("tag") == KQ_TAG and m.get("sha256") == {r_: f["sha256"] for r_, f in KQ_FILES.items()}
                  and os.path.getsize(os.path.join(d_, "ch.pmtiles")) == KQ_FILES["tiles"]["size"]
                  and os.path.getsize(os.path.join(d_, "orte.sqlite")) == KQ_FILES["orte"]["unpacked"]
                  and all(os.path.isfile(os.path.join(d_, "web", f)) for f in ("maplibre-gl.js", "maplibre-gl.css", "style.json")))
        except (OSError, ValueError):
            ok = False
    KQ_RT["ok"], KQ_RT["ok_t"] = ok, now
    return ok


def kq_close():
    with KQ_RT["lock"]:
        for k in ("pm", "db"):
            o = KQ_RT[k]
            KQ_RT[k] = None
            try:
                if o is not None:
                    o.close()
            except Exception:
                pass
    KQ_RT["ok_t"] = 0.0


# ---- PMTiles v3: read only the header, the directories and the one tile ----------------------------------------------------------
def kq_tileid(z, x, y):
    """the tile id of PMTiles v3 (Hilbert curve per zoom level, like the reference implementation)"""
    if z > 31 or x < 0 or y < 0 or x >= 1 << z or y >= 1 << z:
        raise ValueError("tile outside the zoom level")
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


class KqPMTiles:
    """a PMTiles v3 file: os.pread of the header (127 bytes), the root directory and the leaf directories (an LRU of
    KQ_LEAF_CACHE, as compact arrays) - a tile is one more pread of its bytes; never the whole file"""

    def __init__(self, path):
        from array import array
        self._array = array
        self.fd = os.open(path, os.O_RDONLY)
        try:
            h = os.pread(self.fd, 127, 0)
            if len(h) < 127 or h[:7] != b"PMTiles" or h[7] != 3:
                raise ValueError("not a PMTiles v3 file")
            (self.root_off, self.root_len, self.meta_off, self.meta_len, self.leaf_off, self.leaf_len, self.data_off,
             self.data_len, self.n_addr, self.n_entries, self.n_contents) = _kq_struct.unpack_from("<11Q", h, 8)
            self.clustered, self.icomp, self.tcomp, self.ttype, self.minz, self.maxz = _kq_struct.unpack_from("<6B", h, 96)
            self.bounds = [v / 1e7 for v in _kq_struct.unpack_from("<4i", h, 102)]
            if self.icomp not in (1, 2) or self.ttype != 1 or self.root_len > 1 << 20:
                raise ValueError("unsupported PMTiles (compression %d, tile type %d)" % (self.icomp, self.ttype))
            self.size = os.fstat(self.fd).st_size
            self.leaves = _KqOD()
            self.lock = threading.Lock()
            self.reads = 0                                  # bytes read (tests: never the whole file)
            self.root = self._dir(self.root_off, self.root_len)
        except Exception:
            os.close(self.fd)
            raise

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass

    def _read(self, off, n):
        if off < 0 or n < 0 or off + n > self.size or n > 64 << 20:
            raise ValueError("outside the file")
        self.reads += n
        b = os.pread(self.fd, n, off)
        if len(b) != n:
            raise ValueError("short read")
        return b

    def _dir(self, off, n):
        import gzip as _gz
        b = self._read(off, n)
        if self.icomp == 2:
            b = _gz.decompress(b)
        p = 0

        def rv():
            nonlocal p
            v = sh = 0
            while True:
                c = b[p]; p += 1
                v |= (c & 0x7F) << sh
                if c < 0x80:
                    return v
                sh += 7
                if sh > 63:
                    raise ValueError("bad varint")
        cnt = rv()
        if cnt > 1 << 22:
            raise ValueError("directory too big")
        A = self._array
        ids, runs, lens, offs = A("Q"), A("L"), A("L"), A("Q")
        last = 0
        for _ in range(cnt):
            last += rv(); ids.append(last)
        for _ in range(cnt):
            runs.append(rv())
        for _ in range(cnt):
            lens.append(rv())
        for i in range(cnt):
            v = rv()
            offs.append(offs[i - 1] + lens[i - 1] if v == 0 and i > 0 else v - 1)
        return ids, runs, lens, offs

    def _leaf(self, off, n):
        k = (off, n)
        with self.lock:
            d = self.leaves.get(k)
            if d is not None:
                self.leaves.move_to_end(k)
                return d
        d = self._dir(self.leaf_off + off, n)
        with self.lock:
            self.leaves[k] = d
            while len(self.leaves) > KQ_LEAF_CACHE:
                self.leaves.popitem(last=False)
        return d

    def tile(self, z, x, y):
        """the bytes of the tile as stored (gzip for the Protomaps builds) or None"""
        if z < self.minz or z > self.maxz:
            return None
        tid = kq_tileid(z, x, y)
        ids, runs, lens, offs = self.root
        for _ in range(4):
            i = _kq_bisect(ids, tid) - 1
            if i < 0:
                return None
            if runs[i] == 0:
                ids, runs, lens, offs = self._leaf(offs[i], lens[i])
                continue
            if tid - ids[i] < runs[i]:
                return self._read(self.data_off + offs[i], lens[i])
            return None
        return None


def kq_pm():
    with KQ_RT["lock"]:
        if KQ_RT["pm"] is None:
            KQ_RT["pm"] = KqPMTiles(os.path.join(kq_dir(), "ch.pmtiles"))
        return KQ_RT["pm"]


# ---- the place search (SQLite, read-only) ---------------------------------------------------------------------------------------
_KQ_FOLD = {"ß": "ss", "ẞ": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe", "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "ð": "d", "þ": "th"}


def kq_norm(s, umlaut=False):
    """the search key - the SAME rules as kq_norm in werkzeuge/karten/paket.py (karten_test.py compares both)"""
    import unicodedata
    s = str(s or "")
    if umlaut:
        s = re.sub("[äÄ]", "ae", s); s = re.sub("[öÖ]", "oe", s); s = re.sub("[üÜ]", "ue", s)
    s = "".join(_KQ_FOLD.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"['’`´]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


KQ_ZOOM = {"city": 12, "town": 13, "village": 14, "suburb": 15, "quarter": 15, "neighbourhood": 16, "hamlet": 15, "locality": 15,
           "isolated_dwelling": 16, "farm": 16, "island": 14, "islet": 15, "peak": 14, "volcano": 14, "saddle": 14, "pass": 14,
           "lake": 12, "reservoir": 13, "glacier": 13, "street": 17}


def kq_db():
    import sqlite3
    with KQ_RT["lock"]:
        if KQ_RT["db"] is None:
            KQ_RT["db"] = sqlite3.connect("file:" + os.path.join(kq_dir(), "orte.sqlite") + "?mode=ro", uri=True, check_same_thread=False)
        return KQ_RT["db"]


def kq_search(q, n=8):
    """[{name, also, kind, lat, lon, gem, kt, ele, z}] best first: exact name, then the beginning of the name, then a later
    word; within that the importance (city > town > village …, population, height, area)"""
    k = kq_norm(q)[:60]
    if len(k) < 2 or not kq_installed():
        return []
    try:
        n = max(1, min(20, int(n or 8)))
    except (TypeError, ValueError):
        n = 8
    db = kq_db()
    with KQ_RT["lock"]:
        rows = db.execute("SELECT k, id, w, r FROM such WHERE k = ?", (k,)).fetchall()
        rows += db.execute("SELECT k, id, w, r FROM such WHERE k >= ? AND k < ? ORDER BY r DESC LIMIT 400", (k, k + "{")).fetchall()
    best = {}
    for kk, i, w, r in rows:
        s = r + (10000 if kk == k else 0) + (0 if w else 2000)
        if s > best.get(i, -1):
            best[i] = s
    top = sorted(best, key=lambda i: -best[i])[:n]
    if not top:
        return []
    with KQ_RT["lock"]:
        got = {r[0]: r for r in db.execute("SELECT id, name, kind, lat, lon, gem, kt, ele, alt FROM ort WHERE id IN (%s)" % ",".join("?" * len(top)), top)}
    out = []
    for i in top:
        r = got.get(i)
        if not r:
            continue
        _, name, kind, lat, lon, gem, kt, ele, alt = r
        also = ""
        nk = kq_norm(name)
        if not (nk.startswith(k) or (" " + k) in (" " + nk) or kq_norm(name, True).startswith(k)):
            for a in (alt or "").split("|"):
                ak = kq_norm(a)
                if a and (ak.startswith(k) or (" " + k) in (" " + ak) or kq_norm(a, True).startswith(k)):
                    also = a
                    break
        out.append({"name": name, "also": also, "kind": kind, "lat": lat, "lon": lon, "gem": gem or "", "kt": kt or "",
                    "ele": ele, "z": KQ_ZOOM.get(kind, 14)})
    return out


# ---- download, check, switch on, remove (only the administrator) ------------------------------------------------------------------
def _kq_unzip(zp, dest, limit):
    """the web package into dest: only plain names below the folder, no links, at most «limit» bytes"""
    tot = 0
    with zipfile.ZipFile(zp) as z:
        infos = z.infolist()
        for i in infos:
            nm = i.filename
            if nm.startswith("/") or "\\" in nm or ".." in nm.split("/") or not re.fullmatch(r"[A-Za-z0-9._ /@+-]{1,200}", nm):
                raise ValueError("bad file name in the package")
            if (i.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("link in the package")
            tot += i.file_size
        if tot > limit:
            raise ValueError("package larger than announced")
        for i in infos:
            if i.is_dir():
                continue
            p = os.path.join(dest, *i.filename.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with z.open(i) as src, open(p, "wb") as out:
                shutil.copyfileobj(src, out, 1 << 20)
    return tot


def _kq_gunzip(src, dst, want):
    import gzip as _gz
    n = 0
    with _gz.open(src, "rb") as g_, open(dst, "wb") as out:
        while True:
            if KQ_DL.get("stop"):
                raise InterruptedError("cancelled")
            b = g_.read(1 << 20)
            if not b:
                break
            n += len(b)
            if n > want:
                raise ValueError("place index larger than announced")
            out.write(b)
    if n != want:
        raise ValueError("place index has the wrong size")


def kq_free():
    try:
        return shutil.disk_usage(DATA_DIR).free
    except OSError:
        return 1 << 40


def kq_space_ok():
    """enough free space on the memory card for what is still to load + the unpacked files + the reserve"""
    dd = kq_dl_dir()
    have = 0
    for f in KQ_FILES.values():
        for p in (os.path.join(dd, f["name"]), os.path.join(dd, f["name"]) + ".part"):
            if os.path.isfile(p):
                have += os.path.getsize(p)
    return kq_free() - (kq_total() - have + KQ_FILES["web"]["unpacked"] + KQ_FILES["orte"]["unpacked"]) >= bio_free_need()


def kq_download(wait=False):
    """load the three files, check them, switch the map on (background); (ok, error)"""
    if not kq_pinned():
        return False, "comes with an update"
    if KQ_DL["running"]:
        return True, ""
    if kq_installed():
        return True, ""
    if not kq_space_ok():
        return False, "not enough free space on the memory card"
    KQ_DL.update(running=True, got=0, total=kq_total(), msg="", stop=False, done=False, phase="load")

    def work():
        dd, tmp = kq_dl_dir(), kq_dir() + ".new"
        try:
            os.makedirs(dd, exist_ok=True)
            for r_ in ("web", "orte", "tiles"):                  # small first: a broken connection is found early
                f = KQ_FILES[r_]
                dest = os.path.join(dd, f["name"])
                if os.path.isfile(dest) and piper_check_file(dest, f)[0]:
                    KQ_DL["got"] += f["size"]
                else:
                    bio_fetch(KQ_BASE["url"] + f["name"], dest, f, KQ_DL)    # 639zzd: resume, exact size + sha256 before use
            KQ_DL["phase"] = "unpack"
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(os.path.join(tmp, "web"))
            _kq_unzip(os.path.join(dd, KQ_FILES["web"]["name"]), os.path.join(tmp, "web"), KQ_FILES["web"]["unpacked"])
            with open(os.path.join(tmp, "web", "karte.json"), encoding="utf-8") as fh:
                man = json.load(fh)
            if man.get("tag") != KQ_TAG:
                raise ValueError("the package is not " + KQ_TAG)
            _kq_gunzip(os.path.join(dd, KQ_FILES["orte"]["name"]), os.path.join(tmp, "orte.sqlite"), KQ_FILES["orte"]["unpacked"])
            import sqlite3
            c_ = sqlite3.connect("file:" + os.path.join(tmp, "orte.sqlite") + "?mode=ro", uri=True)
            try:
                c_.execute("SELECT id, name, kind, lat, lon FROM ort LIMIT 1").fetchall()
                c_.execute("SELECT k, id, w, r FROM such LIMIT 1").fetchall()
            finally:
                c_.close()
            os.replace(os.path.join(dd, KQ_FILES["tiles"]["name"]), os.path.join(tmp, "ch.pmtiles"))
            KqPMTiles(os.path.join(tmp, "ch.pmtiles")).close()                # a real PMTiles v3 vector file
            with open(os.path.join(tmp, "karte.ok"), "w", encoding="utf-8") as fh:
                json.dump({"tag": KQ_TAG, "sha256": {r_: f["sha256"] for r_, f in KQ_FILES.items()}}, fh)
            kq_close()
            shutil.rmtree(kq_dir(), ignore_errors=True)
            os.replace(tmp, kq_dir())
            shutil.rmtree(dd, ignore_errors=True)
            KQ_DL["done"] = True
            KQ_RT["ok_t"] = 0.0
            log_event("sys", f"Offline map of Switzerland installed ({KQ_TAG}, {round(kq_total() / 1e6)} MB)")
        except InterruptedError:
            KQ_DL["msg"] = "cancelled"
        except Exception as e:
            KQ_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Offline map not installed: {KQ_DL['msg']}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            KQ_DL.update(running=False, phase="")
    if wait:
        work()
        return (not KQ_DL["msg"]), KQ_DL["msg"]
    threading.Thread(target=work, daemon=True, name="karte-dl").start()
    return True, ""


def kq_cancel():
    if KQ_DL["running"]:
        KQ_DL["stop"] = True
    return True, ""


def kq_delete():
    if KQ_DL["running"]:
        return False, "busy right now - try again in a moment"
    kq_close()
    for p in (kq_dir(), kq_dir() + ".new", kq_dl_dir()):
        shutil.rmtree(p, ignore_errors=True)
    KQ_RT["ok_t"] = 0.0
    log_event("sys", "Offline map of Switzerland deleted")
    return True, ""


def kq_role():
    try:
        from flask import g as _g, has_request_context
        return getattr(_g, "role", "admin") if has_request_context() else "admin"
    except Exception:
        return "admin"


def kq_sim_ok():
    try:
        return bool(sim_live())
    except Exception:
        return False


def kq_maxzoom():
    """the highest zoom level in the file itself (MapLibre zooms the tiles of that level further in)"""
    try:
        return int(kq_pm().maxz) if kq_installed() else KQ_MAXZOOM
    except (OSError, ValueError):
        return KQ_MAXZOOM


def kq_state():
    on = kq_installed()
    return {"on": on, "tag": KQ_TAG, "maxzoom": kq_maxzoom(), "pinned": kq_pinned(), "admin": kq_role() == "admin", "sim": kq_sim_ok(),
            "size": kq_total(), "disk": kq_need_disk(), "free": kq_free(), "free_need": bio_free_need(), "space_ok": True if on else kq_space_ok(),
            "dl": {k: KQ_DL[k] for k in ("running", "got", "total", "msg", "done", "phase")}}


# ---- web: tiles, fonts, the package, search, state, the page /karte --------------------------------------------------------------
_smalltv_routes_639zzq = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzq: /karte, /karte/…, /api/karte (550 calls smalltv_routes once)
    _smalltv_routes_639zzq(app, reply, body)
    from flask import request, Response

    def nope(code=404):
        return Response(b"", status=code, mimetype="text/plain")

    @app.route("/karte")
    def kq_page_():
        return Response(kq_page(), mimetype="text/html")

    @app.route("/karte/t/<tag>/<int:z>/<int:x>/<int:y>.mvt")
    def kq_tile_(tag, z, x, y):
        if tag != KQ_TAG or not kq_installed():
            return nope()
        try:
            pm = kq_pm()
            b_ = pm.tile(z, x, y)
        except (ValueError, OSError):
            return nope()
        if b_ is None:
            return Response(b"", status=204, headers={"Cache-Control": "public, max-age=2592000"})
        h_ = {"Cache-Control": "public, max-age=2592000, immutable"}
        if pm.tcomp == 2:
            h_["Content-Encoding"] = "gzip"
        return Response(b_, mimetype="application/x-protobuf", headers=h_)

    @app.route("/karte/fonts/<path:fp>")
    def kq_font_(fp):
        """glyphs: a missing font or range = an empty answer (MapLibre then leaves those letters out, nothing breaks)"""
        h_ = {"Cache-Control": "public, max-age=2592000"}
        if not kq_installed():
            return nope()
        m_ = re.fullmatch(r"([A-Za-z0-9 ,]{1,120})/(\d{1,5}-\d{1,5})\.pbf", fp)
        if m_:
            base = os.path.realpath(os.path.join(kq_dir(), "web", "fonts"))
            for fo in m_.group(1).split(","):
                p_ = os.path.realpath(os.path.join(base, fo.strip(), m_.group(2) + ".pbf"))
                if p_.startswith(base + os.sep) and os.path.isfile(p_):
                    with open(p_, "rb") as fh:
                        return Response(fh.read(), mimetype="application/x-protobuf", headers=h_)
        return Response(b"", mimetype="application/x-protobuf", headers=h_)

    @app.route("/karte/web/<path:fp>")
    def kq_web_(fp):
        if not kq_installed() or not re.fullmatch(r"[A-Za-z0-9._@/-]{1,120}", fp) or fp.endswith(".gz") or fp == "karte.json":
            return nope()
        base = os.path.realpath(os.path.join(kq_dir(), "web"))
        p_ = os.path.realpath(os.path.join(base, fp))
        if not p_.startswith(base + os.sep) or not os.path.isfile(p_):
            return nope()
        mt = {".js": "application/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png", ".txt": "text/plain; charset=utf-8"}
        ext = os.path.splitext(p_)[1]
        if ext not in mt:
            return nope()
        h_ = {"Cache-Control": "public, max-age=86400"}
        src = p_
        if ext in (".js", ".css") and os.path.isfile(p_ + ".gz") and "gzip" in (request.headers.get("Accept-Encoding") or "").lower():
            src = p_ + ".gz"; h_["Content-Encoding"] = "gzip"; h_["Vary"] = "Accept-Encoding"     # already compressed: no work for the Pi
        with open(src, "rb") as fh:
            return Response(fh.read(), mimetype=mt[ext], headers=h_)

    @app.route("/api/karte/suche")
    def kq_suche_():
        try:
            r_ = kq_search(request.args.get("q", ""), request.args.get("n", 8))
        except Exception as e:
            return reply({"ok": False, "error": str(e)[:80], "results": []}, 500)
        return reply({"ok": True, "results": r_})

    @app.route("/api/karte", methods=["GET", "POST"])
    def kq_api_():
        if request.method == "GET":
            return reply(dict(kq_state(), ok=True))
        d = body()
        lang = norm_lang(d.get("lang") or request.args.get("lang") or CFG.get("lang"))
        if kq_role() != "admin":
            return reply({"ok": False, "error": tr("not allowed for your user", lang)}, 403)
        a = str(d.get("action") or "")
        if a == "install":
            ok, err = kq_download()
        elif a == "cancel":
            ok, err = kq_cancel()
        elif a == "delete":
            ok, err = kq_delete()
        else:
            ok, err = False, "unknown action"
        return reply(dict(kq_state(), ok=ok, error=tr(err, lang) if err else ""), 200 if ok else 400)


# the map and the search are for every logged-in user (nothing secret: a map of Switzerland); loading / removing: administrator
VIEW_GET = tuple(VIEW_GET) + tuple(p for p in ("/karte", "/karte/", "/api/karte", "/api/karte/") if p not in VIEW_GET)


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_KQ = {
    "OpenStreetMap contributors": ("OpenStreetMap-Mitwirkende", "contributeurs d’OpenStreetMap", "contributori di OpenStreetMap", "contribuents d’OpenStreetMap"),
    "Offline map of Switzerland": ("Offline-Karte Schweiz", "Carte hors ligne de la Suisse", "Mappa offline della Svizzera", "Charta offline da la Svizra"),
    "Map and place search without internet: loaded once from GitHub (fixed checksum), then everything stays on MoveEye.": (
        "Karte und Ortssuche ohne Internet: einmal von GitHub laden (feste Prüfsumme), danach bleibt alles auf MoveEye.",
        "Carte et recherche de lieux sans Internet : chargées une fois depuis GitHub (somme de contrôle fixe), ensuite tout reste sur MoveEye.",
        "Mappa e ricerca di luoghi senza Internet: caricate una volta da GitHub (somma di controllo fissa), poi tutto resta su MoveEye.",
        "Charta e tschertga da lieus senza internet: chargiar ina giada da GitHub (summa da controlla fixa), lura resta tut sin MoveEye."),
    "Download offline map of Switzerland": ("Offline-Karte Schweiz herunterladen", "Télécharger la carte hors ligne de la Suisse",
                                            "Scarica la mappa offline della Svizzera", "Telechargiar la charta offline da la Svizra"),
    "kq-ask": ("Offline-Karte Schweiz jetzt laden? %s MB von GitHub (danach %s MB auf der Speicherkarte, %s GB bleiben frei).",
               "Charger maintenant la carte hors ligne de la Suisse ? %s Mo depuis GitHub (ensuite %s Mo sur la carte, %s Go restent libres).",
               "Caricare adesso la mappa offline della Svizzera? %s MB da GitHub (poi %s MB sulla scheda, %s GB restano liberi).",
               "Chargiar uss la charta offline da la Svizra? %s MB da GitHub (lura %s MB sin la carta, %s GB restan libers)."),
    "kq-del": ("Offline-Karte entfernen? Danach kommen die Karten wieder aus dem Internet (wenn eingeschaltet).",
               "Supprimer la carte hors ligne ? Les cartes viendront de nouveau d’Internet (si activé).",
               "Rimuovere la mappa offline? Poi le mappe arrivano di nuovo da Internet (se attivato).",
               "Allontanar la charta offline? Lura vegnan las chartas puspè da l’internet (sch’activà)."),
    "installed": ("installiert", "installée", "installata", "installada"),
    "Remove": ("Entfernen", "Supprimer", "Rimuovi", "Allontanar"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "checking and unpacking …": ("prüfen und entpacken …", "vérification et décompression …", "verifica e decompressione …", "controllar e spachetar …"),
    "not enough free space on the memory card": ("zu wenig freier Platz auf der Speicherkarte", "pas assez d’espace libre sur la carte mémoire",
                                                 "spazio libero insufficiente sulla scheda di memoria", "memia pauc spazi liber sin la carta da memoria"),
    "comes with an update": ("kommt mit einem Update", "arrive avec une mise à jour", "arriva con un aggiornamento", "vegn cun in update"),
    "cancelled": ("abgebrochen", "annulé", "annullato", "interrut"),
    "Search a place …": ("Ort suchen …", "Chercher un lieu …", "Cerca un luogo …", "Tschertgar in lieu …"),
    "Nothing found": ("Nichts gefunden", "Rien trouvé", "Nessun risultato", "Chattà nagut"),
    "Open in the simulator": ("Im Simulator öffnen", "Ouvrir dans le simulateur", "Apri nel simulatore", "Avrir en il simulatur"),
    "Set as location of MoveEye": ("Als Standort von MoveEye setzen", "Définir comme emplacement de MoveEye", "Imposta come posizione di MoveEye",
                                   "Definir sco lieu da MoveEye"),
    "Big map": ("Grosse Karte", "Grande carte", "Mappa grande", "Charta gronda"),
    "Map": ("Karte", "Carte", "Mappa", "Charta"),
    "Location of MoveEye": ("Standort von MoveEye", "Emplacement de MoveEye", "Posizione di MoveEye", "Lieu da MoveEye"),
    "Tap on the map to choose a point. Two fingers or the wheel zoom.": (
        "Auf die Karte tippen, um einen Punkt zu wählen. Mit zwei Fingern oder dem Rad zoomen.",
        "Toucher la carte pour choisir un point. Zoomer avec deux doigts ou la molette.",
        "Tocca la mappa per scegliere un punto. Zoom con due dita o la rotella.",
        "Tutgar la charta per tscherner in punct. Zoomar cun dus dets u la rodella."),
    "The offline map is not installed.": ("Die Offline-Karte ist nicht installiert.", "La carte hors ligne n’est pas installée.",
                                          "La mappa offline non è installata.", "La charta offline n’è betg installada."),
    "Install it under Settings → Location.": ("Installieren unter Einstellungen → Standort.", "L’installer sous Réglages → Emplacement.",
                                              "Installarla in Impostazioni → Posizione.", "L’installar sut Parameters → Lieu."),
    "Offline map not readable": ("Offline-Karte nicht lesbar", "Carte hors ligne illisible", "Mappa offline non leggibile", "Charta offline betg legibla"),
    "Sent to the simulator – it loads the place.": ("An den Simulator geschickt – er lädt den Ort.", "Envoyé au simulateur – il charge le lieu.",
                                                    "Inviato al simulatore – carica il luogo.", "Tramess al simulatur – el chargia il lieu."),
    "Saved": ("Gespeichert", "Enregistré", "Salvato", "Memorisà"),
    "Only in Switzerland": ("Nur in der Schweiz", "Seulement en Suisse", "Solo in Svizzera", "Mo en Svizra"),
    "Sources and licences": ("Quellen und Lizenzen", "Sources et licences", "Fonti e licenze", "Funtaunas e licenzas"),
    "kind-city": ("Stadt", "ville", "città", "citad"), "kind-town": ("Stadt", "ville", "città", "citad"),
    "kind-village": ("Dorf", "village", "villaggio", "vischnanca"), "kind-suburb": ("Quartier", "quartier", "quartiere", "quartier"),
    "kind-quarter": ("Quartier", "quartier", "quartiere", "quartier"), "kind-neighbourhood": ("Quartier", "quartier", "quartiere", "quartier"),
    "kind-hamlet": ("Weiler", "hameau", "frazione", "fracziun"), "kind-locality": ("Flurname", "lieu-dit", "località", "num local"),
    "kind-isolated_dwelling": ("Einzelhof", "ferme isolée", "casa isolata", "chasa isolada"), "kind-farm": ("Hof", "ferme", "fattoria", "bain puril"),
    "kind-island": ("Insel", "île", "isola", "insla"), "kind-islet": ("Insel", "îlot", "isolotto", "insletta"),
    "kind-peak": ("Gipfel", "sommet", "vetta", "piz"), "kind-volcano": ("Gipfel", "sommet", "vetta", "piz"),
    "kind-saddle": ("Sattel", "col", "sella", "sella"), "kind-pass": ("Pass", "col", "passo", "pass"),
    "kind-lake": ("See", "lac", "lago", "lai"), "kind-reservoir": ("Stausee", "lac de barrage", "bacino", "lai artifizial"),
    "kind-glacier": ("Gletscher", "glacier", "ghiacciaio", "glatscher"), "kind-street": ("Strasse", "rue", "via", "via"),
}
_KQ_EN = {"kq-ask": "Load the offline map of Switzerland now? %s MB from GitHub (then %s MB on the memory card, %s GB stay free).",
          "kq-del": "Remove the offline map? Then the maps come from the internet again (if switched on).",
          "kind-city": "city", "kind-town": "town", "kind-village": "village", "kind-suburb": "quarter", "kind-quarter": "quarter",
          "kind-neighbourhood": "quarter", "kind-hamlet": "hamlet", "kind-locality": "locality", "kind-isolated_dwelling": "farmstead",
          "kind-farm": "farm", "kind-island": "island", "kind-islet": "islet", "kind-peak": "peak", "kind-volcano": "peak",
          "kind-saddle": "saddle", "kind-pass": "pass", "kind-lake": "lake", "kind-reservoir": "reservoir", "kind-glacier": "glacier",
          "kind-street": "street"}
for _k, _v in _HX_KQ.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def kq_tx():
    """the texts of the map scripts in all five languages (the scripts run before the page has its dictionaries)"""
    out = {"en": dict(_KQ_EN)}
    for i_, L_ in enumerate(("de", "fr", "it", "rm")):
        out[L_] = {k: v[i_] for k, v in _HX_KQ.items()}
    return out


# ---- the browser part: one script in <head> of the pages with a map ----------------------------------------------------------------
KQ_HEAD_JS = r"""<script>
// 639zzq: Offline-Karte Schweiz - MapLibre GL JS from MoveEye itself (lazy), the vector tiles from /karte/t/…, the search /api/karte/suche
(function () {
  const K = window.KQ = /*KQSTATE*/{}, TX = /*KQTX*/{};
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const T = window.kqT = k => (TX[L()] || {})[k] || (TX.en || {})[k] || k;
  K.attr = () => '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">' + T("OpenStreetMap contributors") + "</a>";
  let libP = null, styleP = null;
  K.lib = () => libP || (libP = new Promise((ok, no) => {
    const c = document.createElement("link"); c.rel = "stylesheet"; c.href = "/karte/web/maplibre-gl.css"; document.head.appendChild(c);
    const s = document.createElement("script"); s.src = "/karte/web/maplibre-gl.js"; s.onload = () => ok(window.maplibregl); s.onerror = () => { libP = null; no(new Error("maplibre")); };
    document.head.appendChild(s); }));
  K.style = () => styleP || (styleP = fetch("/karte/web/style.json").then(r => r.json()).then(s => {
    const o = location.origin, src = s.sources.protomaps;
    src.tiles = [o + "/karte/t/" + K.tag + "/{z}/{x}/{y}.mvt"]; src.maxzoom = K.maxzoom || 15; delete src.attribution;
    s.glyphs = o + "/karte/fonts/{fontstack}/{range}.pbf"; s.sprite = o + "/karte/web/sprites/light"; return s; }));
  K.make = (box, opt) => Promise.all([K.lib(), K.style()]).then(([ml, st]) => {
    const m = new ml.Map(Object.assign({container: box, style: JSON.parse(JSON.stringify(st)), attributionControl: false, fadeDuration: 0,
      dragRotate: false, pitchWithRotate: false, touchPitch: false, maxPitch: 0, renderWorldCopies: false}, opt || {}));
    try { m.touchZoomRotate.disableRotation(); m.keyboard.disableRotation(); } catch (e) {}
    return m; });
  K.at = el => { el.classList.add("kq-attr"); el.innerHTML = K.attr(); el.hidden = false; return el; };
  // background of the maps that MoveEye draws itself (pins, gestures stay theirs): same centre and scale (256 px tiles -> zoom - 1)
  window.kqBg = function (host, cx, cy, z) {
    if (!K.on || !host) return false;
    let b = host.__kq;
    if (!b) {
      b = host.__kq = {w: document.createElement("div")};
      b.w.className = "kq-bg"; b.w.style.cssText = "position:absolute;inset:0;pointer-events:none;z-index:0;background:#e2dfd6";
      const c = document.createElement("div"); c.style.cssText = "position:absolute;inset:0"; b.w.appendChild(c); host.insertBefore(b.w, host.firstChild);
      K.make(c, {interactive: false}).then(m => { b.m = m; if (b.v) m.jumpTo(b.v);
        if (window.ResizeObserver) new ResizeObserver(() => { m.resize(); if (b.v) m.jumpTo(b.v); }).observe(b.w); })
        .catch(() => { b.w.textContent = T("Offline map not readable"); });
    }
    const s = 256 * Math.pow(2, z);
    b.v = {center: [cx / s * 360 - 180, Math.atan(Math.sinh(Math.PI * (1 - 2 * cy / s))) * 180 / Math.PI], zoom: Math.max(0, z - 1)};
    if (b.m) b.m.jumpTo(b.v);
    host.querySelectorAll(".mattr,.kq-at").forEach(a => { if (!a.classList.contains("kq-attr")) K.at(a); a.hidden = false; });
    return true;
  };
  // a small map with one point (recordings)
  window.kqSmall = function (anchor, gps) {
    let box = document.getElementById("kq-small");
    if (!K.on || !gps || !anchor) { if (box) box.hidden = true; return; }
    const ll = [+gps[1], +gps[0]];
    if (!box) {
      box = document.createElement("div"); box.id = "kq-small"; box.style.cssText = "position:relative;height:170px;margin-top:8px;border-radius:10px;overflow:hidden;border:1px solid var(--line,#334);background:#e2dfd6";
      const c = document.createElement("div"); c.style.cssText = "position:absolute;inset:0"; box.appendChild(c);
      box.appendChild(K.at(document.createElement("div")));
      const big = document.createElement("a"); big.className = "kq-big"; big.textContent = "🗺 " + T("Big map"); box.appendChild(big); box.__big = big;
      anchor.after(box);
      K.make(c, {zoom: 14, center: ll}).then(m => { box.__m = m; box.__mk = new maplibregl.Marker({color: "#f0571a"}).setLngLat(box.__ll || ll).addTo(m); m.jumpTo({center: box.__ll || ll, zoom: 14}); });
    }
    box.hidden = false; box.__ll = ll;
    box.__big.href = "/karte?lat=" + gps[0] + "&lon=" + gps[1] + "&z=15";
    if (box.__m) { box.__mk.setLngLat(ll); box.__m.resize(); box.__m.jumpTo({center: ll, zoom: 14}); }
  };
  K.find = q => fetch("/api/karte/suche?n=8&q=" + encodeURIComponent(q), {cache: "no-store"}).then(r => r.json()).then(j => j.results || []).catch(() => []);
  K.sub = x => [T("kind-" + x.kind), x.ele ? x.ele + " m" : "", x.gem, x.kt].filter(Boolean).join(" · ");
  K.label = x => x.name + (x.also ? " (" + x.also + ")" : "");
  // results under a search field; pick(lat, lon, result)
  window.kqSearchUI = function (inp, pick) {
    let box = inp.__kqres;
    if (!box) {
      box = inp.__kqres = document.createElement("div"); box.className = "kq-res";
      (inp.parentNode.tagName === "DIV" ? inp.parentNode : inp).after(box);
      let tm = 0; inp.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(() => kqSearchUI(inp, pick), 220); });
    }
    const q = inp.value.trim(); box.textContent = "";
    if (q.length < 2) return Promise.resolve([]);
    return K.find(q).then(R => {
      if (inp.value.trim() !== q) return R;
      box.textContent = "";
      if (!R.length) { const n = document.createElement("div"); n.className = "mut"; n.textContent = T("Nothing found"); box.appendChild(n); return R; }
      R.forEach(x => { const b = document.createElement("button"); b.type = "button"; b.className = "sec kq-hit";
        const nb = document.createElement("b"); nb.textContent = K.label(x); const sb = document.createElement("span"); sb.className = "mut"; sb.textContent = K.sub(x);
        b.append(nb, " ", sb); b.onclick = () => { box.textContent = ""; pick(x.lat, x.lon, x); }; box.appendChild(b); });
      return R; });
  };
  K.toSim = (lat, lon, name) => fetch("/api/sim", {method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({action: "ctl", ctl: "set", id: "ort_map", value: lat.toFixed(6) + ", " + lon.toFixed(6) + (name ? ", " + String(name).replace(/,/g, " ") : ""), lang: L()})})
    .then(r => r.json()).catch(() => ({ok: false}));
  // the administrator: load / remove the offline map
  window.kqInstallBox = function () {
    const w = document.createElement("div"); w.className = "kq-inst"; let tm = 0;
    const MB = n => Math.max(1, Math.round((n || 0) / 1e6));
    const get = () => fetch("/api/karte", {cache: "no-store"}).then(r => r.json());
    const act = a => fetch("/api/karte", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: a, lang: L()})})
      .then(r => r.json()).then(S => { paint(S); return S; }).catch(() => {});
    function paint(S) {
      clearTimeout(tm); w.textContent = ""; if (!S) return;
      const h = document.createElement("b"); h.textContent = "🗺 " + T("Offline map of Switzerland"); w.appendChild(h);
      const tx = document.createElement("div"); tx.className = "mut"; tx.textContent = T("Map and place search without internet: loaded once from GitHub (fixed checksum), then everything stays on MoveEye."); w.appendChild(tx);
      const row = document.createElement("div"); row.className = "kq-row"; const D = S.dl || {};
      if (D.running) {
        const p = document.createElement("progress"); p.max = D.total || 1; p.value = D.phase === "unpack" ? (D.total || 1) : (D.got || 0);
        const sp = document.createElement("span"); sp.textContent = D.phase === "unpack" ? "⏳ " + T("checking and unpacking …") : "⏳ " + MB(D.got) + " / " + MB(D.total) + " MB";
        const cb = document.createElement("button"); cb.type = "button"; cb.className = "sec"; cb.textContent = T("Cancel"); cb.onclick = () => act("cancel");
        row.append(sp, p, cb);
        tm = setTimeout(() => get().then(S2 => { if (S2.on && !K.on) location.reload(); else paint(S2); }).catch(() => {}), 1500);
      } else if (S.on) {
        const ok = document.createElement("span"); ok.textContent = "✓ " + T("installed") + " · " + MB(S.disk) + " MB";
        const a = document.createElement("a"); a.className = "btn sec"; a.href = "/karte"; a.textContent = "🗺 " + T("Big map");
        const db = document.createElement("button"); db.type = "button"; db.className = "sec kq-del"; db.textContent = "🗑 " + T("Remove");
        db.onclick = () => { if (confirm(T("kq-del"))) act("delete").then(() => location.reload()); };
        row.append(ok, a, db);
        if (!K.on) setTimeout(() => location.reload(), 300);
      } else if (!S.pinned) {
        const m = document.createElement("span"); m.className = "mut"; m.textContent = T("comes with an update"); row.appendChild(m);
      } else {
        const ib = document.createElement("button"); ib.type = "button"; ib.className = "kq-install"; ib.textContent = "⬇ " + T("Download offline map of Switzerland") + " (" + MB(S.size) + " MB)";
        ib.disabled = !S.space_ok;
        ib.onclick = () => { if (confirm(T("kq-ask").replace("%s", MB(S.size)).replace("%s", MB(S.disk)).replace("%s", Math.round(S.free_need / 1e9)))) act("install"); };
        row.appendChild(ib);
        if (!S.space_ok) { const n = document.createElement("span"); n.className = "kq-warn"; n.textContent = "⚠ " + T("not enough free space on the memory card"); row.appendChild(n); }
      }
      w.appendChild(row);
      const e = S.error || (!D.running && D.msg ? T(D.msg) : ""); if (e) { const n = document.createElement("div"); n.className = "kq-warn kq-err"; n.textContent = "⚠ " + e; w.appendChild(n); }
    }
    get().then(paint).catch(() => {});
    return w;
  };
  // Settings -> location: the big map, «Im Simulator öffnen», the install box (administrator)
  window.kqLocExtra = function (box, getG) {
    const w = document.createElement("div"); w.className = "kq-loc";
    const here = () => { const G = getG() || {}, g = G.gps; return g ? [g.lat, g.lon] : (G.lat != null ? [G.lat, G.lon] : null); };
    if (K.on) {
      const row = document.createElement("div"); row.className = "kq-row";
      const a = document.createElement("a"); a.className = "btn sec kq-bigl"; a.textContent = "🗺 " + T("Big map"); a.href = "/karte";
      a.onclick = () => { const p = here(); a.href = "/karte" + (p ? "?lat=" + p[0] + "&lon=" + p[1] + "&z=14" : ""); };
      row.appendChild(a);
      if (K.sim) { const s = document.createElement("button"); s.type = "button"; s.className = "sec kq-sim"; s.textContent = "🎮 " + T("Open in the simulator");
        s.onclick = () => { const p = here(); if (!p) return;
          K.toSim(+p[0], +p[1], "").then(r => { const m = r.ok ? T("Sent to the simulator – it loads the place.") : "⚠ " + (r.error || "?"); if (window.toast) toast(m); else s.title = m; }); };
        row.appendChild(s); }
      w.appendChild(row);
    }
    if (K.admin) {                                           // only when it is seen (no request while the settings stay closed)
      const slot = document.createElement("div"); slot.style.minHeight = "1px"; w.appendChild(slot);
      const go = () => { if (!slot.firstChild) slot.appendChild(kqInstallBox()); };
      if (window.IntersectionObserver) { const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); go(); } }); io.observe(slot); } else go();
    }
    box.appendChild(w);
  };
  // links «📍 …» to openstreetmap.org (status, diary) open the own map when it is there
  document.addEventListener("click", e => {
    const a = K.on && e.target && e.target.closest ? e.target.closest('a[href^="https://www.openstreetmap.org/?mlat="]') : null; if (!a) return;
    const u = new URL(a.href), la = +u.searchParams.get("mlat"), lo = +u.searchParams.get("mlon"); if (!isFinite(la) || !isFinite(lo)) return;
    e.preventDefault(); const z = ((u.hash.match(/map=(\d+)/) || [])[1]) || 14;
    window.open("/karte?lat=" + la + "&lon=" + lo + "&z=" + z, a.target || "_self");
  }, true);
  const st = document.createElement("style");
  st.textContent = ".kq-attr{position:absolute;right:0;bottom:0;z-index:4;font:11px/1.4 system-ui,sans-serif;color:#222;background:rgba(255,255,255,.8);padding:1px 6px;border-top-left-radius:6px}"
    + ".kq-attr a{color:#222}.kq-res{display:flex;flex-direction:column;gap:4px;margin:4px 0}.kq-hit{text-align:left;display:block;width:100%}"
    + ".kq-hit .mut{font-size:12px}.kq-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:8px}.kq-row progress{flex:1 1 120px}"
    + ".kq-inst{margin-top:10px;padding:10px 12px;border:1px solid var(--line,#334);border-radius:12px}.kq-warn{color:var(--warn,#e9a23b);font-weight:600}"
    + ".kq-big{position:absolute;left:6px;top:6px;z-index:4;background:rgba(255,255,255,.9);color:#123;border-radius:8px;padding:3px 8px;font-size:13px;text-decoration:none}";
  document.head.appendChild(st);
})();
</script>
"""


def kq_head():
    s_ = kq_state()
    st = {k: s_[k] for k in ("on", "tag", "maxzoom", "pinned", "admin", "sim")}
    return (KQ_HEAD_JS.replace("/*KQSTATE*/{}", json.dumps(st), 1)
            .replace("/*KQTX*/{}", json.dumps(kq_tx(), ensure_ascii=False).replace("</", "<\\/"), 1))


_KQ_MARKS = ("kqBg(", "kqSmall(", "kqLocExtra(", "kqSearchUI(", "openstreetmap.org/?mlat=", "/*KQPAGE*/")
_render_page_639zzq = render_page


# wraps: render_page
def render_page(page, active):                              # + 639zzq: the map script in <head> of the pages with a map
    html = _render_page_639zzq(page, active)
    if "</head>" in html and any(m in page for m in _KQ_MARKS) and "window.KQ =" not in html:
        try:
            html = html.replace("</head>", kq_head() + "</head>", 1)
        except Exception as e:
            log_event("sys", f"Offline map: script not added ({e.__class__.__name__})")
    return html


# ---- the hooks in the pages (exactly once each; the self-test checks them) ----------------------------------------------------------
KQ_HOOKS = {
    "WEB_PAGE": [
        ("    if (M.online) for (let ty = Math.floor(y0 / 256); ty <= Math.floor((y0 + h) / 256); ty++) {",
         "    if (window.kqBg && kqBg(m, M.cx, M.cy, z)) {} else if (M.online) for (let ty = Math.floor(y0 / 256); ty <= Math.floor((y0 + h) / 256); ty++) {"),
        ("    mp.M.online = G.map_online;", "    mp.M.online = G.map_online || !!(window.KQ && KQ.on);"),
        ('  const search = async () => { const s = q.value.trim(); if (!s) return; err.textContent = "";',
         '  const search = async () => { const s = q.value.trim(); if (!s) return; err.textContent = "";'
         ' if (window.KQ && KQ.on) { kqSearchUI(q, (la, lo) => { mp.show(la, lo, 14); save(la, lo); }); return; }'),
        ("  box.append(seg, info, tools, mp.el, hint, err);",
         "  box.append(seg, info, tools, mp.el, hint, err); if (window.kqLocExtra) kqLocExtra(box, () => G);"
         " if (window.KQ && KQ.on) setTimeout(() => kqSearchUI(q, (la, lo) => { mp.show(la, lo, 14); save(la, lo); }), 0);"),
    ],
    "REC_PAGE": [
        ("  if (MAP.online) {\n    for (let ty = Math.floor(y0 / 256); ty <= Math.floor((y0 + h) / 256); ty++) {",
         "  if (window.kqBg && kqBg(m, MAP.cx, MAP.cy, z)) {} else if (MAP.online) {\n    for (let ty = Math.floor(y0 / 256); ty <= Math.floor((y0 + h) / 256); ty++) {"),
        ("MAP.pts = j.points || []; MAP.online = j.map_online !== false;",
         "MAP.pts = j.points || []; MAP.online = j.map_online !== false || !!(window.KQ && KQ.on);"),
        ('  if (it.kind === "image") { const im = el("img"); im.src = "/rec/file/" + encodeURIComponent(it.name); body.appendChild(im); }\n  else showVideo(it, token);',
         '  if (window.kqSmall) kqSmall(note, it.gps);\n'
         '  if (it.kind === "image") { const im = el("img"); im.src = "/rec/file/" + encodeURIComponent(it.name); body.appendChild(im); }\n  else showVideo(it, token);'),
    ],
}
KQ_SIM_HOOKS = [                                           # SIMMAP_JS (470) - it stands in SIM_PAGE and WEB_PAGE
    ("    for (let ty = Math.floor(tly / 256); ty <= Math.floor((tly + h) / 256); ty++) for (let tx = Math.floor(tlx / 256); tx <= Math.floor((tlx + w) / 256); tx++) {",
     "    if (!(window.kqBg && kqBg(map, cx, cy, z))) for (let ty = Math.floor(tly / 256); ty <= Math.floor((tly + h) / 256); ty++) for (let tx = Math.floor(tlx / 256); tx <= Math.floor((tlx + w) / 256); tx++) {"),
    ('  sr.append(q, sb, kb); box.appendChild(sr);', '  sr.append(q, sb, kb); box.appendChild(sr); if (window.KQ && KQ.on) kb.hidden = true;'),
    ('const at = el("div", "", "© swisstopo");', 'const at = el("div", "kq-at", "© swisstopo");'),
    ('    const s = q.value.trim(); if (!s) return; res.textContent = "";\n    try {\n      const r = await fetch("https://api3.geo.admin.ch',
     '    const s = q.value.trim(); if (!s) return; res.textContent = "";\n'
     '    if (window.KQ && KQ.on) { const L = await KQ.find(s); if (!L.length) { info.textContent = t("Nothing found"); return; }\n'
     '      L.forEach(x => { const name = KQ.label(x), b = el("button", "sec", name + " · " + KQ.sub(x)); b.type = "button"; b.style.textAlign = "left";\n'
     '        b.onclick = () => { if (!inCH(x.lat, x.lon)) { info.textContent = kqT("Only in Switzerland"); return; } sel = {la: x.lat, lo: x.lon, name: x.name}; z = 16; cx = lx(sel.lo, z); cy = ly(sel.la, z); res.textContent = ""; go.disabled = false; info.textContent = name; draw(); };\n'
     '        res.appendChild(b); }); return; }\n'
     '    try {\n      const r = await fetch("https://api3.geo.admin.ch'),
]
KQ_HOOKED = {}
for _nm, _hooks in list(KQ_HOOKS.items()) + [("SIM_PAGE", KQ_SIM_HOOKS), ("WEB_PAGE", KQ_SIM_HOOKS)]:
    _pg = globals().get(_nm) or ""
    for _a, _b in _hooks:
        if _pg.count(_a) == 1:
            _pg = _pg.replace(_a, _b, 1)
            KQ_HOOKED[(_nm, _a)] = True
        else:
            KQ_HOOKED[(_nm, _a)] = False                    # the page was changed: this hook stays out (self-test says which)
    globals()[_nm] = _pg

# ---- the page /karte -------------------------------------------------------------------------------------------------------------------
KQ_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MoveEye - Karte</title>
<style>
/*BASECSS*/
main{padding:12px;max-width:980px;margin:0 auto}
.kq-top{display:flex;gap:6px;align-items:center}.kq-top input{flex:1;min-width:0;padding:9px 11px;border-radius:10px;border:1px solid var(--line);background:var(--field,var(--panel));color:var(--txt)}
#kq-map{position:relative;height:min(64vh,620px);min-height:300px;border-radius:12px;overflow:hidden;border:1px solid var(--line);background:#e2dfd6;margin-top:6px;touch-action:none}
#kq-c{position:absolute;inset:0}
.kq-info{margin:8px 2px;font-size:14px}.kq-btns{display:flex;gap:8px;flex-wrap:wrap}
.kq-none{border:1px solid var(--line);border-radius:12px;padding:14px;background:var(--panel)}
.kq-lic{display:inline-block;margin-top:10px;font-size:12px}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <div id="kq-none" class="kq-none" hidden></div>
  <div id="kq-wrap" hidden>
    <div class="kq-top"><input id="kq-q" type="search" enterkeyhint="search" autocomplete="off"><button class="sec" type="button" id="kq-go">🔍</button></div>
    <div id="kq-map"><div id="kq-c"></div><div id="kq-at"></div></div>
    <div class="kq-info" id="kq-info"></div>
    <div class="kq-btns" id="kq-btns" hidden>
      <button type="button" id="kq-set">📍 <span></span></button>
      <button type="button" class="sec" id="kq-sim">🎮 <span></span></button>
    </div>
    <div class="mut" id="kq-msg"></div>
    <a class="mut kq-lic" id="kq-lic" href="/karte/web/LIZENZEN.txt" target="_blank" rel="noopener"></a>
  </div>
</main>
<script>
/*COMMON*/
/*KQPAGE*/
(async () => {
  await initAppearance();
  const K = window.KQ, T = kqT, P = new URLSearchParams(location.search), $ = s => document.querySelector(s);
  document.title = "MoveEye – " + T("Map");
  if (!K.on) { const n = $("#kq-none"); n.hidden = false; const b = document.createElement("b"); b.textContent = "🗺 " + T("The offline map is not installed.");
    n.appendChild(b); if (K.admin) { n.appendChild(document.createElement("br")); n.append(T("Install it under Settings → Location.")); n.appendChild(kqInstallBox()); } return; }
  $("#kq-wrap").hidden = false; $("#kq-q").placeholder = T("Search a place …"); $("#kq-lic").textContent = "ⓘ " + T("Sources and licences");
  $("#kq-set span").textContent = T("Set as location of MoveEye"); $("#kq-sim span").textContent = T("Open in the simulator");
  $("#kq-set").hidden = !K.admin; $("#kq-sim").hidden = !K.sim;
  K.at($("#kq-at"));
  let G = {}; try { G = await (await fetch("/api/gps", {cache: "no-store"})).json(); } catch (e) {}
  const me = G.gps ? [G.gps.lon, G.gps.lat] : (G.lat != null && !G.factory ? [G.lon, G.lat] : null);
  const la = parseFloat(P.get("lat")), lo = parseFloat(P.get("lon")), zz = parseFloat(P.get("z"));
  const start = isFinite(la) && isFinite(lo) ? [lo, la] : (me || [8.23, 46.8]);
  const m = await K.make($("#kq-c"), {center: start, zoom: isFinite(zz) ? zz : (isFinite(la) || me ? 14 : 7), minZoom: 5, maxZoom: 19, maxBounds: [[4.5, 45.0], [11.5, 48.6]]});
  window.KQMAP = m;
  m.addControl(new maplibregl.NavigationControl({showCompass: false}), "top-right");
  if (me) { const d = document.createElement("div"); d.title = T("Location of MoveEye"); d.style.cssText = "width:16px;height:16px;border-radius:50%;background:#2f7cf6;border:3px solid #fff;box-shadow:0 0 0 2px rgba(47,124,246,.4)";
    new maplibregl.Marker({element: d}).setLngLat(me).addTo(m); }
  let sel = null, selName = "";
  const mk = new maplibregl.Marker({color: "#f0571a"});
  const info = $("#kq-info"), msg = $("#kq-msg");
  function choose(lat, lon, name) {
    sel = [lat, lon]; selName = name || ""; mk.setLngLat([lon, lat]).addTo(m); $("#kq-btns").hidden = false; msg.textContent = "";
    info.textContent = (name ? name + " · " : "") + lat.toFixed(5) + ", " + lon.toFixed(5);
  }
  if (isFinite(la) && isFinite(lo)) choose(la, lo, P.get("name") || "");
  else info.textContent = T("Tap on the map to choose a point. Two fingers or the wheel zoom.");
  m.on("click", e => choose(e.lngLat.lat, e.lngLat.lng, ""));
  const pick = (lat, lon, x) => { m.jumpTo({center: [lon, lat], zoom: x && x.z ? x.z : 14}); choose(lat, lon, x ? x.name : ""); };
  $("#kq-go").onclick = () => kqSearchUI($("#kq-q"), pick);
  $("#kq-q").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); kqSearchUI($("#kq-q"), pick); } });
  kqSearchUI($("#kq-q"), pick);
  $("#kq-set").onclick = async () => { if (!sel) return;
    await post("/api/set", {key: "gps_phone", value: false});
    const a = await post("/api/text", {key: "latitude", value: sel[0].toFixed(4), lang: LANG}), b = await post("/api/text", {key: "longitude", value: sel[1].toFixed(4), lang: LANG});
    msg.textContent = a.ok && b.ok ? "📍 " + T("Saved") : "⚠ " + (a.error || b.error || "error"); };
  $("#kq-sim").onclick = async () => { if (!sel) return; const r = await K.toSim(sel[0], sel[1], selName);
    msg.textContent = r.ok ? "🎮 " + T("Sent to the simulator – it loads the place.") : "⚠ " + (r.error || "?"); };
})();
</script>
</body></html>
"""


def kq_page():
    return render_page(KQ_PAGE, "more").replace("/*KQPAGE*/", "", 1)


# ---- the manual: one point in the section about the settings / location (5 languages) ---------------------------------------------
_HELP_KQ = {
    "de": ("🗺 Offline-Karte Schweiz", "(Einstellungen → Standort, nur der Admin): Karte und Ortssuche der ganzen Schweiz einmal von GitHub laden (feste Prüfsumme; vorher wird der freie Platz auf der Speicherkarte geprüft), danach ohne Internet: Standort auf der Karte antippen oder suchen («Zurich» findet Zürich), Orte der Aufnahmen, grosse Karte /karte, «🎮 Im Simulator öffnen» und «Ort von der Karte» im Simulator. «🗑 Entfernen» löscht sie wieder. Daten © OpenStreetMap-Mitwirkende (ODbL)."),
    "en": ("🗺 Offline map of Switzerland", "(Settings → Location, administrator only): load the map and the place search of all of Switzerland once from GitHub (fixed checksum; the free space on the memory card is checked first), then without internet: tap or search the location (“Zurich” finds Zürich), the places of the recordings, the big map /karte, “🎮 Open in the simulator” and “Place from the map” in the simulator. “🗑 Remove” deletes it again. Data © OpenStreetMap contributors (ODbL)."),
    "fr": ("🗺 Carte hors ligne de la Suisse", "(Réglages → Emplacement, administrateur seulement) : charger une fois depuis GitHub la carte et la recherche de lieux de toute la Suisse (somme de contrôle fixe ; l’espace libre sur la carte mémoire est vérifié d’abord), ensuite sans Internet : toucher ou chercher l’emplacement (« Zurich » trouve Zürich), les lieux des enregistrements, la grande carte /karte, « 🎮 Ouvrir dans le simulateur » et « Lieu sur la carte » dans le simulateur. « 🗑 Supprimer » l’efface. Données © contributeurs d’OpenStreetMap (ODbL)."),
    "it": ("🗺 Mappa offline della Svizzera", "(Impostazioni → Posizione, solo l’amministratore): caricare una volta da GitHub la mappa e la ricerca di luoghi di tutta la Svizzera (somma di controllo fissa; prima viene controllato lo spazio libero sulla scheda di memoria), poi senza Internet: toccare o cercare la posizione («Zurich» trova Zürich), i luoghi delle registrazioni, la mappa grande /karte, «🎮 Apri nel simulatore» e «Luogo dalla mappa» nel simulatore. «🗑 Rimuovi» la cancella. Dati © contributori di OpenStreetMap (ODbL)."),
    "rm": ("🗺 Charta offline da la Svizra", "(Parameters → Lieu, mo l’administratur): chargiar ina giada da GitHub la charta e la tschertga da lieus da tut la Svizra (summa da controlla fixa; avant vegn controllà il spazi liber sin la carta da memoria), lura senza internet: tutgar u tschertgar il lieu («Zurich» chatta Zürich), ils lieus da las registraziuns, la charta gronda /karte, «🎮 Avrir en il simulatur» e «Lieu da la charta» en il simulatur. «🗑 Allontanar» la stizza. Datas © contribuents d’OpenStreetMap (ODbL)."),
}


def _help_kq(doc, lang):
    """one more point at the end of the first list of the section about the settings (or the first section with a list)"""
    h_, x_ = _HELP_KQ[lang]
    if h_ in doc:
        return doc
    from html import escape as _e
    item = f"<li><b>{h_}</b> {_e(x_, quote=False)}</li>"
    for sid in ("settings", "location", "setup", "start"):
        i = doc.find(f'<section id="{sid}"')
        if i >= 0:
            j, k = doc.find("</ul>", i), doc.find("</section>", i)
            if 0 < j < k:
                return doc[:j] + item + doc[j:]
    return doc


_hp_en_kq = HELP_PAGE.find('<div lang="en">')
if _hp_en_kq > 0:
    HELP_PAGE = _help_kq(HELP_PAGE[:_hp_en_kq], "de") + _help_kq(HELP_PAGE[_hp_en_kq:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_kq(HELP_X[_L], _L)


# ---- self-test (without the files; werkzeuge/karten_test.py tests loading, tiles, search and the pages in the browser) ----------------
def kq_selftest():
    assert KQ_BASE["url"] == "https://github.com/DonElektro/MotionWatch/releases/download/" + KQ_TAG + "/"
    assert re.fullmatch(r"karten-\d{1,3}", KQ_TAG) and KQ_MAXZOOM in (14, 15)
    n_ = KQ_TAG.split("-")[1]
    assert KQ_FILES["tiles"]["name"] == "karte-ch-%s.pmtiles" % n_ and KQ_FILES["web"]["name"] == "karte-web-%s.zip" % n_
    assert KQ_FILES["orte"]["name"] == "orte-ch-%s.sqlite.gz" % n_
    pins = [bool(f["size"]) for f in KQ_FILES.values()]
    assert all(pins) == kq_pinned() and (all(pins) or not any(pins)), "either all pins or none"
    bad = [k for k, v in KQ_HOOKED.items() if not v]
    assert not bad, "hooks not found: " + "; ".join(n + ": " + a[:50] for n, a in bad)
    for nm in ("WEB_PAGE", "REC_PAGE", "SIM_PAGE"):
        assert "kqBg(" in globals()[nm], nm
    assert "kqSmall(note, it.gps)" in REC_PAGE and "kqLocExtra(box" in WEB_PAGE and "KQ.find(s)" in SIM_PAGE and "KQ.find(s)" in WEB_PAGE
    assert kq_tileid(0, 0, 0) == 0 and kq_tileid(1, 0, 0) == 1 and kq_tileid(1, 0, 1) == 2 and kq_tileid(1, 1, 1) == 3 and kq_tileid(1, 1, 0) == 4
    assert kq_tileid(2, 0, 0) == 5 and kq_tileid(14, 8580, 5745) > kq_tileid(13, 8191, 8191)
    assert kq_norm("Zürich") == "zurich" and kq_norm("Zürich", True) == "zuerich" and kq_norm("La Chaux-de-Fonds") == "la chaux de fonds"
    assert kq_norm("Grossmünster") == kq_norm("Großmünster") and kq_norm("Sant’Antonio") == "santantonio"
    for p in ("/karte", "/karte/t/x/1/1/1.mvt", "/api/karte", "/api/karte/suche"):
        assert role_allows("view", p, "GET", {}, []), p
    assert not role_allows("view", "/api/karte", "POST", {"action": "install"}, list(USER_PERMS)), "only the administrator loads the map"
    html = render_page(REC_PAGE, "rec")
    assert html.count("window.KQ =") == 1 and html.find("window.KQ =") < html.find("<body"), "the map script stands in <head>"
    assert "window.KQ =" not in render_page("<html><head></head><body><main>x</main></body></html>", "live")
    if not kq_installed():
        assert kq_search("Seon") == [] and '"on": false' in kq_head()
    tx = kq_tx()
    assert all(tx[L_]["OpenStreetMap contributors"] for L_ in ("de", "fr", "it", "rm")) and tx["de"]["OpenStreetMap contributors"] == "OpenStreetMap-Mitwirkende"
    assert all("ß" not in v[0] for v in _HX_KQ.values()) and all(k in DE for k in _HX_KQ)
    assert _HELP_KQ["de"][0] in HELP_PAGE and _HELP_KQ["en"][0] in HELP_PAGE
    return True


SELFTEST_EXTRA.append(("Offline map of Switzerland (639zzq)", kq_selftest))
