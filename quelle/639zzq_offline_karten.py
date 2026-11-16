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
# «🗺️ Topo-Karte» (Entscheid des Besitzers 15.11.2026, Option c der Vorschau): die Karte von heute + eigene Höhenlinien und
# Relief aus swissALTI3D (10 m, © swisstopo) + Wanderwege gelb / rot / blau aus OpenStreetMap (nicht das offizielle Netz).
#   * Release «karten-2»: karte-web-2.zip (vier Stile: Standard / Topo, je hell / dunkel – werkzeuge/karten/stil.py),
#     topo-ch-2.pmtiles (Vektor: Ebenen «contour» mit ele / lvl / gl=1 auf Gletschern und «wege» mit g 1 / 2 / 3) und
#     relief-ch-2.pmtiles (Raster: Höhen als terrarium-WebP z8–13, MapLibre schattiert selbst). Karte und Ortssuche bleiben am
#     Release «karten-1» (KQ_FILE_TAG): ein Gerät, das sie hat, lädt nur das Neue (rund 0.8 GB), die alten Dateien werden in den
#     neuen Ordner verlinkt (gleiche Prüfsumme, nichts doppelt auf der Karte). Bis dahin bleibt die alte Karte an (kq_on).
#   * Kacheln: /karte/t/<sha12>/<schicht>/<z>/<x>/<y>.<mvt|webp> (Schichten ch / topo / relief, der Anfang der Prüfsumme statt
#     des Tags: der Browser-Cache gilt pro Datei); die alte Adresse /karte/t/<tag>/<z>/<x>/<y>.mvt bleibt für die Basiskarte.
#   * Stil: Schalter «Standard / Topo» oben links auf /karte (pro Browser gemerkt, mw-kq-style), Vorgabe für alle in den
#     Einstellungen → Standort «Topo-Karte» (map_topo, Web und Fenster, Standard an). Hell / dunkel folgt dem Aussehen der Seite
#     (Klasse «light» am body); ein Wechsel stellt jede Karte der Seite um und behält eigene Ebenen (Touren 639zzx).
#   * Quellenangabe der Topo-Karte «© OpenStreetMap-Mitwirkende · © swisstopo»; unter der grossen Karte die Farben der Wege und
#     «aus OpenStreetMap – nicht das offizielle Netz».
# Selbsttest kq_selftest; Tests werkzeuge/karten_test.py (Laden gut / falsch, Platz, Byte-Bereiche, Seiten im Browser in
# iPhone-Breite ohne Anfrage nach aussen, Suche, Standort per Tipp, Quellenangabe, Rechte, Stile, Ergänzen von karten-1;
# --echt mit den Release-Dateien).
# ----------------------------------------------------------------------------
import struct as _kq_struct
from bisect import bisect_right as _kq_bisect
from collections import OrderedDict as _KqOD

KQ_TAG = "karten-2"
KQ_MAXZOOM = 15
KQ_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/"}   # + <tag>/<name>; Tests: lokaler Server
KQ_FILE_TAG = {"orte": "karten-1", "tiles": "karten-1"}   # Dateien, die an einem früheren Release bleiben (paket.py BASIS)
# Werte aus werkzeuge/karten/paket.py (pins.txt des Workflows «Offline-Karten»); size 0 = noch nicht freigegeben
KQ_FILES = {
    "tiles": {"name": "karte-ch-1.pmtiles", "size": 655187450, "sha256": "ea71c54bcf1c91585106a6d3dcb7d5757f219761f3c0ebbbf54c5df487fde185", "unpacked": 0},
    "web": {"name": "karte-web-2.zip", "size": 1495338, "sha256": "c72953b5c74c5c9dc839aaa48da67eafd8fb04922ad9584ae187d5519a42b227", "unpacked": 2604659},
    "orte": {"name": "orte-ch-1.sqlite.gz", "size": 11211798, "sha256": "1e9f1e574a92a324b789768fb18c1deff2bf3716942d725d0dc1d3999330eb00", "unpacked": 28307456},
    "topo": {"name": "topo-ch-2.pmtiles", "size": 381431763, "sha256": "9e8a74a87ab1a7d486ac933ccbc4e22a20b7cf97e63893afd6856dd45e937a7c", "unpacked": 0},
    "relief": {"name": "relief-ch-2.pmtiles", "size": 226169173, "sha256": "31a369ba638b330d943e9f7797402ae596d72b55eb904ba292c206c74994a579", "unpacked": 0},
}
KQ_MAX = {"tiles": 2000 * 1000 * 1000, "web": 60 * 1000 * 1000, "orte": 300 * 1000 * 1000, "topo": 2000 * 1000 * 1000,
          "relief": 2000 * 1000 * 1000}                     # harte Obergrenzen (auch entpackt; GitHub: unter 2 GiB pro Datei)
KQ_NAME_RE = {"tiles": r"karte-ch-\d{1,3}\.pmtiles", "web": r"karte-web-\d{1,3}\.zip", "orte": r"orte-ch-\d{1,3}\.sqlite\.gz",
              "topo": r"topo-ch-\d{1,3}\.pmtiles", "relief": r"relief-ch-\d{1,3}\.pmtiles"}
KQ_DISK = {"tiles": "ch.pmtiles", "topo": "topo.pmtiles", "relief": "relief.pmtiles", "orte": "orte.sqlite", "web": "web"}   # in DATA_DIR/karte
KQ_LAYER = {"ch": "tiles", "topo": "topo", "relief": "relief"}       # /karte/t/<key>/<schicht>/… -> Datei
KQ_TTYPE = {"tiles": (1,), "topo": (1,), "relief": (2, 4)}          # PMTiles-Kacheltyp: 1 MVT, 2 PNG, 4 WebP
KQ_MIME = {1: "application/x-protobuf", 2: "image/png", 3: "image/jpeg", 4: "image/webp"}
KQ_EXT = {1: "mvt", 2: "png", 3: "jpg", 4: "webp"}
KQ_ORDER = ("web", "orte", "topo", "relief", "tiles")          # laden: klein zuerst (eine kaputte Verbindung fällt früh auf)
KQ_STYLES = ("style.json", "style_dark.json", "style_topo.json", "style_topo_dark.json")
KQ_LEAF_CACHE = 48
KQ_DL = {"running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": False, "phase": ""}
KQ_RT = {"pm": {}, "db": None, "lock": threading.Lock(), "ok_t": 0.0, "have": {}}
for _k, _v in {"map_topo": True}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)   # 636 took its copy before this part


def kq_dir():
    return os.path.join(DATA_DIR, "karte")


def kq_dl_dir():
    return os.path.join(DATA_DIR, "karte_dl")


def kq_tag(r_):
    return KQ_FILE_TAG.get(r_, KQ_TAG)


def kq_url(r_):
    return KQ_BASE["url"] + kq_tag(r_) + "/" + KQ_FILES[r_]["name"]


def kq_key(r_):
    """the part of the tile address that changes with the file (browser cache per file)"""
    return (KQ_FILES[r_].get("sha256") or "0" * 12)[:12]


def kq_pinned():
    """every file with exact size, sha256 and name - nothing else is ever downloaded"""
    for r_, f in KQ_FILES.items():
        if not (isinstance(f.get("size"), int) and 0 < f["size"] <= KQ_MAX[r_] and re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or ""))
                and isinstance(f.get("unpacked"), int) and 0 <= f["unpacked"] <= KQ_MAX[r_] and re.fullmatch(KQ_NAME_RE[r_], f.get("name") or "")
                and re.fullmatch(r"karten-\d{1,3}", kq_tag(r_)) and f["name"].split("-")[-1].split(".")[0] == kq_tag(r_).split("-")[1]):
            return False
    return KQ_FILES["web"]["unpacked"] > 0 and KQ_FILES["orte"]["unpacked"] > 0


def kq_total():
    """bytes still to download (a device with the files of karten-1 loads only what is new)"""
    have = kq_have()
    return sum(f["size"] for r_, f in KQ_FILES.items() if not have.get(r_))


def kq_need_disk():
    """bytes on the card after the install: the map files, the unpacked web package and the unpacked place index"""
    return sum(f["size"] for r_, f in KQ_FILES.items() if r_ not in ("web", "orte")) + KQ_FILES["web"]["unpacked"] + KQ_FILES["orte"]["unpacked"]


def kq_have():
    """{role: True} for every file that is installed with exactly the pinned checksum (marker karte.ok of the download: tag +
    every sha256, the file still there with its size) - checked at most every 2 s"""
    now = time.time()
    if now - KQ_RT["ok_t"] < 2.0:
        return KQ_RT["have"]
    have = {}
    d_ = kq_dir()
    try:
        with open(os.path.join(d_, "karte.ok"), encoding="utf-8") as fh:
            m = json.load(fh)
        sh = m.get("sha256") if isinstance(m, dict) else None
        sh = sh if isinstance(sh, dict) else {}
        for r_, f in KQ_FILES.items():
            if not f.get("sha256") or sh.get(r_) != f["sha256"]:
                continue
            p_ = os.path.join(d_, KQ_DISK[r_])
            if r_ == "web":
                ok = all(os.path.isfile(os.path.join(p_, x)) for x in ("maplibre-gl.js", "maplibre-gl.css", "style.json"))
            elif r_ == "orte":
                ok = os.path.isfile(p_) and os.path.getsize(p_) == f["unpacked"]
            else:
                ok = os.path.isfile(p_) and os.path.getsize(p_) == f["size"]
            if ok:
                have[r_] = True
    except (OSError, ValueError):
        have = {}
    KQ_RT["have"], KQ_RT["ok_t"] = have, now
    return have


def kq_installed():
    """everything of KQ_TAG is there (also the topo map)"""
    return kq_pinned() and all(kq_have().get(r_) for r_ in KQ_FILES)


def kq_on():
    """the map can be shown: the base map and the place search with their pinned checksum, a web package (also the older one
    of karten-1 until the topo map is added)"""
    h_ = kq_have()
    return bool(h_.get("tiles") and h_.get("orte") and os.path.isfile(os.path.join(kq_dir(), "web", "style.json"))
                and os.path.isfile(os.path.join(kq_dir(), "web", "maplibre-gl.js")))


def kq_styles():
    """the styles of the installed web package (karte-web-1 had only style.json)"""
    if not kq_on():
        return []
    return [s_ for s_ in KQ_STYLES if os.path.isfile(os.path.join(kq_dir(), "web", s_))]


def kq_topo_on():
    h_ = kq_have()
    return bool(kq_on() and h_.get("topo") and h_.get("relief") and "style_topo.json" in kq_styles())


def kq_close():
    with KQ_RT["lock"]:
        pms, KQ_RT["pm"] = KQ_RT["pm"], {}
        db_, KQ_RT["db"] = KQ_RT["db"], None
        for o in list(pms.values()) + [db_]:
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
            if self.icomp not in (1, 2) or self.ttype not in KQ_MIME or self.root_len > 1 << 20:
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
        """the bytes of the tile as stored (gzip for the vector tiles, WebP / PNG as they are) or None"""
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


def kq_pm(r_="tiles"):
    with KQ_RT["lock"]:
        pm = KQ_RT["pm"].get(r_)
        if pm is None:
            pm = KQ_RT["pm"][r_] = KqPMTiles(os.path.join(kq_dir(), KQ_DISK[r_]))
        return pm


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
    if len(k) < 2 or not kq_on():
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
    """enough free space on the memory card for what is still to load + the unpacked files + the reserve (files that stay
    from an earlier install are linked, they need no room)"""
    dd = kq_dl_dir()
    have, h_ = 0, kq_have()
    for r_, f in KQ_FILES.items():
        if h_.get(r_):
            continue
        for p in (os.path.join(dd, f["name"]), os.path.join(dd, f["name"]) + ".part"):
            if os.path.isfile(p):
                have += os.path.getsize(p)
    unp = sum(KQ_FILES[r_]["unpacked"] for r_ in ("web", "orte") if not h_.get(r_))
    return kq_free() - (kq_total() - have + unp) >= bio_free_need()


def _kq_keep(src, dst, moved):
    """a file of the old install into the new folder: a hard link (no room needed, the old map stays until the switch),
    else moved (remembered: back on an error)"""
    try:
        os.link(src, dst)
    except OSError:
        os.replace(src, dst)
        moved.append((dst, src))


def kq_download(wait=False):
    """load what is missing, check it, switch the map on (background); (ok, error)"""
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
        dd, tmp, old = kq_dl_dir(), kq_dir() + ".new", kq_dir()
        have = dict(kq_have())
        moved = []
        try:
            os.makedirs(dd, exist_ok=True)
            for r_ in KQ_ORDER:                                   # small first: a broken connection is found early
                if have.get(r_):
                    continue
                f = KQ_FILES[r_]
                dest = os.path.join(dd, f["name"])
                if os.path.isfile(dest) and piper_check_file(dest, f)[0]:
                    KQ_DL["got"] += f["size"]
                else:
                    bio_fetch(kq_url(r_), dest, f, KQ_DL)          # 639zzd: resume, exact size + sha256 before use
            KQ_DL["phase"] = "unpack"
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp)
            if have.get("web"):
                shutil.copytree(os.path.join(old, "web"), os.path.join(tmp, "web"))
            else:
                os.makedirs(os.path.join(tmp, "web"))
                _kq_unzip(os.path.join(dd, KQ_FILES["web"]["name"]), os.path.join(tmp, "web"), KQ_FILES["web"]["unpacked"])
            with open(os.path.join(tmp, "web", "karte.json"), encoding="utf-8") as fh:
                man = json.load(fh)
            if man.get("tag") != kq_tag("web"):
                raise ValueError("the package is not " + kq_tag("web"))
            if have.get("orte"):
                _kq_keep(os.path.join(old, "orte.sqlite"), os.path.join(tmp, "orte.sqlite"), moved)
            else:
                _kq_gunzip(os.path.join(dd, KQ_FILES["orte"]["name"]), os.path.join(tmp, "orte.sqlite"), KQ_FILES["orte"]["unpacked"])
            import sqlite3
            c_ = sqlite3.connect("file:" + os.path.join(tmp, "orte.sqlite") + "?mode=ro", uri=True)
            try:
                c_.execute("SELECT id, name, kind, lat, lon FROM ort LIMIT 1").fetchall()
                c_.execute("SELECT k, id, w, r FROM such LIMIT 1").fetchall()
            finally:
                c_.close()
            for r_ in ("tiles", "topo", "relief"):
                dst = os.path.join(tmp, KQ_DISK[r_])
                if have.get(r_):
                    _kq_keep(os.path.join(old, KQ_DISK[r_]), dst, moved)
                else:
                    os.replace(os.path.join(dd, KQ_FILES[r_]["name"]), dst)
                pm = KqPMTiles(dst)                              # a real PMTiles v3 file of the right kind
                try:
                    if pm.ttype not in KQ_TTYPE[r_]:
                        raise ValueError("%s: wrong tile type %d" % (KQ_FILES[r_]["name"], pm.ttype))
                finally:
                    pm.close()
            with open(os.path.join(tmp, "karte.ok"), "w", encoding="utf-8") as fh:
                json.dump({"tag": KQ_TAG, "sha256": {r_: f["sha256"] for r_, f in KQ_FILES.items()},
                           "tags": {r_: kq_tag(r_) for r_ in KQ_FILES}}, fh)
            kq_close()
            moved.clear()
            shutil.rmtree(old, ignore_errors=True)
            os.replace(tmp, old)
            shutil.rmtree(dd, ignore_errors=True)
            KQ_DL["done"] = True
            KQ_RT["ok_t"] = 0.0
            log_event("sys", f"Offline map of Switzerland installed ({KQ_TAG}, {round(kq_need_disk() / 1e6)} MB)")
        except InterruptedError:
            KQ_DL["msg"] = "cancelled"
        except Exception as e:
            KQ_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Offline map not installed: {KQ_DL['msg']}")
        finally:
            for dst, src in moved:                               # an error after moving: the old map gets its files back
                try:
                    os.replace(dst, src)
                except OSError:
                    pass
            shutil.rmtree(tmp, ignore_errors=True)
            KQ_RT["ok_t"] = 0.0
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
        return int(kq_pm().maxz) if kq_on() else KQ_MAXZOOM
    except (OSError, ValueError):
        return KQ_MAXZOOM


def kq_layers():
    """{schicht: {key, z: [min, max], bounds, ext}} of the files that are there (for the styles in the browser)"""
    out = {}
    h_ = kq_have()
    for sch, r_ in KQ_LAYER.items():
        if not h_.get(r_) or (r_ != "tiles" and not kq_topo_on()):
            continue
        try:
            pm = kq_pm(r_)
            out[sch] = {"key": kq_key(r_), "z": [int(pm.minz), int(pm.maxz)], "bounds": [round(v, 5) for v in pm.bounds],
                        "ext": KQ_EXT.get(pm.ttype, "mvt")}
        except (OSError, ValueError):
            pass
    return out


def kq_state():
    on, full = kq_on(), kq_installed()
    return {"on": on, "full": full, "topo": kq_topo_on(), "add": bool(on and not full and kq_pinned()), "tag": KQ_TAG,
            "maxzoom": kq_maxzoom(), "pinned": kq_pinned(), "admin": kq_role() == "admin", "sim": kq_sim_ok(),
            "styles": kq_styles(), "layers": kq_layers(), "def": "topo" if CFG.get("map_topo", True) else "std",
            "size": kq_total(), "disk": kq_need_disk(), "free": kq_free(), "free_need": bio_free_need(), "space_ok": True if full else kq_space_ok(),
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

    def tile_reply(r_, z, x, y):
        try:
            pm = kq_pm(r_)
            b_ = pm.tile(z, x, y)
        except (ValueError, OSError):
            return nope()
        if b_ is None:
            return Response(b"", status=204, headers={"Cache-Control": "public, max-age=2592000"})
        h_ = {"Cache-Control": "public, max-age=2592000, immutable"}
        if pm.tcomp == 2:
            h_["Content-Encoding"] = "gzip"
        return Response(b_, mimetype=KQ_MIME.get(pm.ttype, "application/octet-stream"), headers=h_)

    @app.route("/karte/t/<tag>/<int:z>/<int:x>/<int:y>.mvt")
    def kq_tile_(tag, z, x, y):                             # the address up to karten-1 (base map only)
        if tag not in (KQ_TAG, kq_tag("tiles")) or not kq_on():
            return nope()
        return tile_reply("tiles", z, x, y)

    @app.route("/karte/t/<key>/<sch>/<int:z>/<int:x>/<int:y>.<ext>")
    def kq_tile2_(key, sch, z, x, y, ext):
        r_ = KQ_LAYER.get(sch)
        if not r_ or not kq_on() or key != kq_key(r_) or not kq_have().get(r_) or (r_ != "tiles" and not kq_topo_on()):
            return nope()
        return tile_reply(r_, z, x, y)

    @app.route("/karte/fonts/<path:fp>")
    def kq_font_(fp):
        """glyphs: a missing font or range = an empty answer (MapLibre then leaves those letters out, nothing breaks)"""
        h_ = {"Cache-Control": "public, max-age=2592000"}
        if not kq_on():
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
        if not kq_on() or not re.fullmatch(r"[A-Za-z0-9._@/-]{1,120}", fp) or fp.endswith(".gz") or fp == "karte.json":
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
_KQ_TOPO_LABEL = "Offline map: topo map (contour lines, relief, hiking paths) instead of the standard map"
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
    # 639zzq Topo (karten-2)
    "Map style": ("Kartenstil", "Style de carte", "Stile della mappa", "Stil da la charta"),
    "Standard": ("Standard", "Standard", "Standard", "Standard"),
    "Topo": ("Topo", "Topo", "Topo", "Topo"),
    "hiking trail": ("Wanderweg", "chemin de randonnée", "sentiero escursionistico", "senda da viandar"),
    "mountain trail": ("Bergwanderweg", "chemin de randonnée de montagne", "sentiero di montagna", "senda da viandar da muntogna"),
    "alpine trail": ("Alpinwanderweg", "chemin de randonnée alpine", "sentiero alpino", "senda da viandar alpina"),
    "Hiking paths from OpenStreetMap – not the official network.": (
        "Wanderwege aus OpenStreetMap – nicht das offizielle Netz.", "Sentiers d’OpenStreetMap – pas le réseau officiel.",
        "Sentieri da OpenStreetMap – non la rete ufficiale.", "Sendas da OpenStreetMap – betg la rait uffiziala."),
    "Add the topo map": ("Topo-Karte ergänzen", "Ajouter la carte topo", "Aggiungi la mappa topo", "Agiuntar la charta topo"),
    "Contour lines, relief and hiking paths for the map.": ("Höhenlinien, Relief und Wanderwege für die Karte.",
                                                            "Courbes de niveau, relief et sentiers pour la carte.",
                                                            "Curve di livello, rilievo e sentieri per la mappa.",
                                                            "Lingias d’autezza, relief e sendas per la charta."),
    "kq-ask-topo": ("Topo-Karte jetzt ergänzen? %s MB von GitHub (danach %s MB auf der Speicherkarte, %s GB bleiben frei). Die Karte bleibt solange an.",
                    "Ajouter maintenant la carte topo ? %s Mo depuis GitHub (ensuite %s Mo sur la carte, %s Go restent libres). La carte reste disponible pendant ce temps.",
                    "Aggiungere adesso la mappa topo? %s MB da GitHub (poi %s MB sulla scheda, %s GB restano liberi). La mappa resta disponibile nel frattempo.",
                    "Agiuntar uss la charta topo? %s MB da GitHub (lura %s MB sin la carta, %s GB restan libers). La charta resta dentant disponibla."),
    _KQ_TOPO_LABEL: ("Offline-Karte: Topo-Karte (Höhenlinien, Relief, Wanderwege) statt Standard",
                     "Carte hors ligne : carte topo (courbes de niveau, relief, sentiers) au lieu de la carte standard",
                     "Mappa offline: mappa topo (curve di livello, rilievo, sentieri) invece di quella standard",
                     "Charta offline: charta topo (lingias d’autezza, relief, sendas) empè da la charta standard"),
}
_KQ_EN = {"kq-ask": "Load the offline map of Switzerland now? %s MB from GitHub (then %s MB on the memory card, %s GB stay free).",
          "kq-ask-topo": "Add the topo map now? %s MB from GitHub (then %s MB on the memory card, %s GB stay free). The map stays on meanwhile.",
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

# the setting «Topo-Karte» (Settings → Location, web and window): the style of every map unless the browser chose one on /karte
_kq_i = max([i for i, x in enumerate(TOGGLES) if x[1] == "map_online"] or [len(TOGGLES) - 1])
TOGGLES.insert(_kq_i + 1, ("Setup", "map_topo", _KQ_TOPO_LABEL))


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
  const OSM = () => '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">' + T("OpenStreetMap contributors") + "</a>";
  // 639zzq Topo: «Standard» or «Topo» (this browser: mw-kq-style, else the setting map_topo), light / dark like the page
  K.pref = () => { try { const v = localStorage.getItem("mw-kq-style"); if (v === "topo" || v === "std") return v; } catch (e) {} return K.def || "topo"; };
  K.isTopo = () => !!K.topo && K.pref() === "topo";
  K.dark = () => !(document.body && document.body.classList.contains("light"));
  K.file = () => { const st = K.styles || ["style.json"], f = (K.isTopo() ? "style_topo" : "style") + (K.dark() ? "_dark" : "") + ".json";
    return st.indexOf(f) >= 0 ? f : (K.isTopo() && st.indexOf("style_topo.json") >= 0 ? "style_topo.json" : "style.json"); };
  K.attr = () => OSM() + (K.isTopo() ? ' · © <a href="https://www.swisstopo.admin.ch" target="_blank" rel="noopener">swisstopo</a>' : "");
  let libP = null; const SP = {};
  K.maps = [];
  K.lib = () => libP || (libP = new Promise((ok, no) => {
    const c = document.createElement("link"); c.rel = "stylesheet"; c.href = "/karte/web/maplibre-gl.css"; document.head.appendChild(c);
    const s = document.createElement("script"); s.src = "/karte/web/maplibre-gl.js"; s.onload = () => ok(window.maplibregl); s.onerror = () => { libP = null; no(new Error("maplibre")); };
    document.head.appendChild(s); }));
  const LY = K.layers || {}, tilesOf = (sch, ext) => location.origin + "/karte/t/" + LY[sch].key + "/" + sch + "/{z}/{x}/{y}." + ext;
  K.styleOf = f => SP[f] || (SP[f] = fetch("/karte/web/" + f).then(r => r.json()).then(s => {
    const o = location.origin, src = s.sources.protomaps;
    src.tiles = LY.ch ? [tilesOf("ch", "mvt")] : [o + "/karte/t/" + K.tag + "/{z}/{x}/{y}.mvt"]; src.maxzoom = K.maxzoom || 15; delete src.attribution;
    [["topo", "mvt"], ["relief", ""]].forEach(([n, ext]) => { const q = s.sources[n]; if (!q) return; const L_ = LY[n]; delete q.attribution;
      if (!L_) { q.tiles = []; return; }
      q.tiles = [tilesOf(n, ext || L_.ext)]; q.minzoom = L_.z[0]; q.maxzoom = L_.z[1]; q.bounds = L_.bounds; });
    s.glyphs = o + "/karte/fonts/{fontstack}/{range}.pbf"; s.sprite = o + "/karte/web/sprites/" + (/dark$/.test(s.sprite || "") ? "dark" : "light"); return s; })
    .catch(e => { delete SP[f]; throw e; }));
  K.style = () => K.styleOf(K.file());
  K.make = (box, opt) => { const f = K.file(); return Promise.all([K.lib(), K.styleOf(f)]).then(([ml, st]) => {
    const m = new ml.Map(Object.assign({container: box, style: JSON.parse(JSON.stringify(st)), attributionControl: false, fadeDuration: 0,
      dragRotate: false, pitchWithRotate: false, touchPitch: false, maxPitch: 0, renderWorldCopies: false}, opt || {}));
    try { m.touchZoomRotate.disableRotation(); m.keyboard.disableRotation(); } catch (e) {}
    m.__kqF = f; m.__kqL = new Set(st.layers.map(l => l.id)); m.__kqS = new Set(Object.keys(st.sources)); K.maps.push(m);
    return m; }); };
  // another style for every map of the page: own layers and sources (e.g. the tours of 639zzx) stay on top
  K.restyle = () => {
    const f = K.file();
    K.maps.forEach(m => { if (m.__kqF === f) return; m.__kqF = f;
      K.styleOf(f).then(st => { if (m.__kqF !== f) return; const oL = m.__kqL, oS = m.__kqS;
        m.__kqL = new Set(st.layers.map(l => l.id)); m.__kqS = new Set(Object.keys(st.sources));
        m.setStyle(JSON.parse(JSON.stringify(st)), {diff: false, transformStyle: (prev, next) => { if (!prev) return next;
          Object.keys(prev.sources || {}).forEach(k => { if (!oS.has(k) && !(k in next.sources)) next.sources[k] = prev.sources[k]; });
          (prev.layers || []).forEach(l => { if (!oL.has(l.id) && !next.layers.some(x => x.id === l.id)) next.layers.push(l); });
          return next; }}); }).catch(() => {}); });
    document.querySelectorAll(".kq-attr").forEach(a => { a.innerHTML = K.attr(); });
    document.querySelectorAll(".kq-sw").forEach(w => K.paintSwitch(w));
    document.querySelectorAll(".kq-leg").forEach(l => { l.hidden = !K.isTopo(); });
  };
  K.setPref = v => { try { localStorage.setItem("mw-kq-style", v); } catch (e) {} K.restyle(); };
  // the switch «Standard | Topo» (on the big map)
  K.paintSwitch = w => { w.querySelectorAll("button").forEach(b => { const on = (b.dataset.v === "topo") === K.isTopo(); b.classList.toggle("on", on); b.setAttribute("aria-pressed", on ? "true" : "false"); }); };
  K.switchUI = host => { if (!K.topo) return null; const w = document.createElement("div"); w.className = "kq-sw"; w.setAttribute("role", "group"); w.setAttribute("aria-label", T("Map style"));
    [["std", "Standard"], ["topo", "Topo"]].forEach(([v, n]) => { const b = document.createElement("button"); b.type = "button"; b.dataset.v = v; b.textContent = T(n);
      b.onclick = e => { e.stopPropagation(); K.setPref(v); }; w.appendChild(b); });
    K.paintSwitch(w); host.appendChild(w); return w; };
  // the colours of the hiking paths and where they come from (under the big map, only with Topo)
  K.legend = () => { const d = document.createElement("div"); d.className = "kq-leg"; d.hidden = !K.isTopo();
    [["#e3a800", "hiking trail", ""], ["#d83a22", "mountain trail", "d"], ["#2b63d0", "alpine trail", "d"]].forEach(([c, k, dash]) => {
      const i = document.createElement("span"); i.className = "kq-li"; const sw = document.createElement("i"); sw.className = "kq-swatch" + (dash ? " kq-dash" : ""); sw.style.setProperty("--c", c);
      i.append(sw, T(k)); d.appendChild(i); });
    const n = document.createElement("span"); n.className = "kq-lnote"; n.textContent = T("Hiking paths from OpenStreetMap – not the official network."); d.appendChild(n);
    return d; };
  const watch = () => { let last = K.dark(); const mo = new MutationObserver(() => { const d = K.dark(); if (d !== last) { last = d; K.restyle(); } });
    mo.observe(document.body, {attributes: true, attributeFilter: ["class"]}); };
  if (document.body) watch(); else document.addEventListener("DOMContentLoaded", watch);
  window.addEventListener("storage", e => { if (e.key === "mw-kq-style") K.restyle(); });
  K.at = el => { el.classList.add("kq-attr"); el.innerHTML = K.attr(); el.hidden = false; return el; };
  // background of the maps that MoveEye draws itself (pins, gestures stay theirs): same centre and scale (256 px tiles -> zoom - 1)
  window.kqBg = function (host, cx, cy, z) {
    if (!K.on || !host) return false;
    let b = host.__kq;
    if (!b) {
      b = host.__kq = {w: document.createElement("div")};
      b.w.className = "kq-bg"; b.w.style.cssText = "position:absolute;inset:0;pointer-events:none;z-index:0;background:" + (K.dark() ? "#1d2125" : "#e2dfd6");
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
      box = document.createElement("div"); box.id = "kq-small"; box.style.cssText = "position:relative;height:170px;margin-top:8px;border-radius:10px;overflow:hidden;border:1px solid var(--line,#334);background:" + (K.dark() ? "#1d2125" : "#e2dfd6");
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
        tm = setTimeout(() => get().then(S2 => { if ((S2.on && !K.on) || (S2.full && !S2.dl.running && K.on && !K.full)) location.reload(); else paint(S2); }).catch(() => {}), 1500);
      } else if (S.on && S.add) {                              // karten-1 is there: only the topo map (and the new web package) is missing
        const ok = document.createElement("span"); ok.textContent = "✓ " + T("installed");
        const ib = document.createElement("button"); ib.type = "button"; ib.className = "kq-install kq-add"; ib.textContent = "⬇ " + T("Add the topo map") + " (" + MB(S.size) + " MB)";
        ib.disabled = !S.space_ok;
        ib.onclick = () => { if (confirm(T("kq-ask-topo").replace("%s", MB(S.size)).replace("%s", MB(S.disk)).replace("%s", Math.round(S.free_need / 1e9)))) act("install"); };
        const tx2 = document.createElement("div"); tx2.className = "mut"; tx2.textContent = T("Contour lines, relief and hiking paths for the map.");
        row.append(ok, ib); w.appendChild(tx2);
        if (!S.space_ok) { const n = document.createElement("span"); n.className = "kq-warn"; n.textContent = "⚠ " + T("not enough free space on the memory card"); row.appendChild(n); }
      } else if (S.on) {
        const ok = document.createElement("span"); ok.textContent = "✓ " + T("installed") + " · " + MB(S.disk) + " MB";
        const a = document.createElement("a"); a.className = "btn sec"; a.href = "/karte"; a.textContent = "🗺 " + T("Big map");
        const db = document.createElement("button"); db.type = "button"; db.className = "sec kq-del"; db.textContent = "🗑 " + T("Remove");
        db.onclick = () => { if (confirm(T("kq-del"))) act("delete").then(() => location.reload()); };
        row.append(ok, a, db);
        if (!K.on || (S.full && !K.full)) setTimeout(() => location.reload(), 300);
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
    + ".kq-big{position:absolute;left:6px;top:6px;z-index:4;background:rgba(255,255,255,.9);color:#123;border-radius:8px;padding:3px 8px;font-size:13px;text-decoration:none}"
    + ".kq-sw{position:absolute;left:8px;top:8px;z-index:4;display:flex;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.35)}"
    + ".kq-sw button{all:unset;cursor:pointer;min-height:36px;min-width:44px;padding:0 12px;font:600 13px/36px system-ui,sans-serif;text-align:center;background:rgba(255,255,255,.92);color:#123}"
    + ".kq-sw button+button{border-left:1px solid rgba(0,0,0,.15)}.kq-sw button.on{background:#2f7cf6;color:#fff}.kq-sw button:focus-visible{outline:2px solid #2f7cf6;outline-offset:-2px}"
    + ".kq-leg{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center;margin:6px 2px 0;font-size:12px;color:var(--mut,#8a93a0)}.kq-leg[hidden]{display:none}"
    + ".kq-li{display:inline-flex;align-items:center;gap:5px;white-space:nowrap}.kq-swatch{display:inline-block;width:22px;height:4px;border-radius:2px;background:var(--c)}"
    + ".kq-dash{background:repeating-linear-gradient(90deg,var(--c) 0 7px,transparent 7px 10px)}.kq-lnote{flex-basis:100%}"
    + "body:not(.light) .kq-attr{color:#dfe3e8;background:rgba(22,25,28,.78)}body:not(.light) .kq-attr a{color:#dfe3e8}";
  document.head.appendChild(st);
})();
</script>
"""


def kq_head():
    s_ = kq_state()
    st = {k: s_[k] for k in ("on", "full", "topo", "tag", "maxzoom", "pinned", "admin", "sim", "styles", "layers", "def")}
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
body:not(.light) #kq-map{background:#1d2125}
.kq-info{margin:8px 2px;font-size:14px}.kq-btns{display:flex;gap:8px;flex-wrap:wrap}
.kq-none{border:1px solid var(--line);border-radius:12px;padding:14px;background:var(--panel)}
.kq-back{color:var(--acc2);text-decoration:none;font-weight:600;min-height:44px;min-width:44px;display:inline-flex;align-items:center;white-space:nowrap}
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
<a class="kq-back" href="/more">‹ <span data-i18n="More">More</span></a>
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
  K.at($("#kq-at")); K.switchUI($("#kq-map"));
  if (K.topo) $("#kq-map").after(K.legend());
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
  m.on("click", e => { if (window.KT && KT.busy) return; choose(e.lngLat.lat, e.lngLat.lng, ""); });   // 639zzx: while a route is drawn the tap sets its point
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
    "de": ("🗺 Offline-Karte Schweiz", "(Einstellungen → Standort, nur der Admin): Karte und Ortssuche der ganzen Schweiz einmal von GitHub laden (feste Prüfsumme; vorher wird der freie Platz auf der Speicherkarte geprüft), danach ohne Internet: Standort auf der Karte antippen oder suchen («Zurich» findet Zürich), Orte der Aufnahmen, grosse Karte /karte, «🎮 Im Simulator öffnen» und «Ort von der Karte» im Simulator. «🗑 Entfernen» löscht sie wieder. Daten © OpenStreetMap-Mitwirkende (ODbL). Topo-Karte (Vorgabe, Schalter «Standard / Topo» auf /karte): Höhenlinien und Relief aus swissALTI3D (© swisstopo), Wanderwege gelb / rot / blau aus OpenStreetMap (nicht das offizielle Netz); hell oder dunkel wie die Seite."),
    "en": ("🗺 Offline map of Switzerland", "(Settings → Location, administrator only): load the map and the place search of all of Switzerland once from GitHub (fixed checksum; the free space on the memory card is checked first), then without internet: tap or search the location (“Zurich” finds Zürich), the places of the recordings, the big map /karte, “🎮 Open in the simulator” and “Place from the map” in the simulator. “🗑 Remove” deletes it again. Data © OpenStreetMap contributors (ODbL). Topo map (default, switch “Standard / Topo” on /karte): contour lines and relief from swissALTI3D (© swisstopo), hiking paths yellow / red / blue from OpenStreetMap (not the official network); light or dark like the page."),
    "fr": ("🗺 Carte hors ligne de la Suisse", "(Réglages → Emplacement, administrateur seulement) : charger une fois depuis GitHub la carte et la recherche de lieux de toute la Suisse (somme de contrôle fixe ; l’espace libre sur la carte mémoire est vérifié d’abord), ensuite sans Internet : toucher ou chercher l’emplacement (« Zurich » trouve Zürich), les lieux des enregistrements, la grande carte /karte, « 🎮 Ouvrir dans le simulateur » et « Lieu sur la carte » dans le simulateur. « 🗑 Supprimer » l’efface. Données © contributeurs d’OpenStreetMap (ODbL). Carte topo (par défaut, bouton « Standard / Topo » sur /karte) : courbes de niveau et relief de swissALTI3D (© swisstopo), sentiers jaunes / rouges / bleus d’OpenStreetMap (pas le réseau officiel) ; claire ou sombre comme la page."),
    "it": ("🗺 Mappa offline della Svizzera", "(Impostazioni → Posizione, solo l’amministratore): caricare una volta da GitHub la mappa e la ricerca di luoghi di tutta la Svizzera (somma di controllo fissa; prima viene controllato lo spazio libero sulla scheda di memoria), poi senza Internet: toccare o cercare la posizione («Zurich» trova Zürich), i luoghi delle registrazioni, la mappa grande /karte, «🎮 Apri nel simulatore» e «Luogo dalla mappa» nel simulatore. «🗑 Rimuovi» la cancella. Dati © contributori di OpenStreetMap (ODbL). Mappa topo (predefinita, interruttore «Standard / Topo» su /karte): curve di livello e rilievo da swissALTI3D (© swisstopo), sentieri gialli / rossi / blu da OpenStreetMap (non la rete ufficiale); chiara o scura come la pagina."),
    "rm": ("🗺 Charta offline da la Svizra", "(Parameters → Lieu, mo l’administratur): chargiar ina giada da GitHub la charta e la tschertga da lieus da tut la Svizra (summa da controlla fixa; avant vegn controllà il spazi liber sin la carta da memoria), lura senza internet: tutgar u tschertgar il lieu («Zurich» chatta Zürich), ils lieus da las registraziuns, la charta gronda /karte, «🎮 Avrir en il simulatur» e «Lieu da la charta» en il simulatur. «🗑 Allontanar» la stizza. Datas © contribuents d’OpenStreetMap (ODbL). Charta topo (predefinida, cumutatur «Standard / Topo» sin /karte): lingias d’autezza e relief da swissALTI3D (© swisstopo), sendas melnas / cotschnas / blauas da OpenStreetMap (betg la rait uffiziala); clera u stgira sco la pagina."),
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
    assert KQ_BASE["url"] == "https://github.com/DonElektro/MotionWatch/releases/download/"
    assert re.fullmatch(r"karten-\d{1,3}", KQ_TAG) and KQ_MAXZOOM in (14, 15) and set(KQ_FILES) == set(KQ_DISK) == set(KQ_MAX) == set(KQ_NAME_RE)
    for r_, f in KQ_FILES.items():
        n_ = kq_tag(r_).split("-")[1]
        assert re.fullmatch(KQ_NAME_RE[r_], f["name"]) and f["name"].split("-")[-1].split(".")[0] == n_, (r_, f["name"])
        assert kq_url(r_) == KQ_BASE["url"] + kq_tag(r_) + "/" + f["name"]
        assert int(kq_tag(r_).split("-")[1]) <= int(KQ_TAG.split("-")[1])
    # the files of an earlier release are pinned; those of KQ_TAG: all or none (none = «comes with an update», stage 1)
    assert all(KQ_FILES[r_]["size"] for r_ in KQ_FILE_TAG), "files of an earlier release without pins"
    pins = [bool(f["size"]) for r_, f in KQ_FILES.items() if r_ not in KQ_FILE_TAG]
    assert all(pins) == kq_pinned() and (all(pins) or not any(pins)), "either all pins of " + KQ_TAG + " or none"
    bad = [k for k, v in KQ_HOOKED.items() if not v]
    assert not bad, "hooks not found: " + "; ".join(n + ": " + a[:50] for n, a in bad)
    for nm in ("WEB_PAGE", "REC_PAGE", "SIM_PAGE"):
        assert "kqBg(" in globals()[nm], nm
    assert "kqSmall(note, it.gps)" in REC_PAGE and "kqLocExtra(box" in WEB_PAGE and "KQ.find(s)" in SIM_PAGE and "KQ.find(s)" in WEB_PAGE
    assert kq_tileid(0, 0, 0) == 0 and kq_tileid(1, 0, 0) == 1 and kq_tileid(1, 0, 1) == 2 and kq_tileid(1, 1, 1) == 3 and kq_tileid(1, 1, 0) == 4
    assert kq_tileid(2, 0, 0) == 5 and kq_tileid(14, 8580, 5745) > kq_tileid(13, 8191, 8191)
    assert kq_norm("Zürich") == "zurich" and kq_norm("Zürich", True) == "zuerich" and kq_norm("La Chaux-de-Fonds") == "la chaux de fonds"
    assert kq_norm("Grossmünster") == kq_norm("Großmünster") and kq_norm("Sant’Antonio") == "santantonio"
    for p in ("/karte", "/karte/t/x/1/1/1.mvt", "/karte/t/0123456789ab/relief/8/133/90.webp", "/api/karte", "/api/karte/suche"):
        assert role_allows("view", p, "GET", {}, []), p
    assert not role_allows("view", "/api/karte", "POST", {"action": "install"}, list(USER_PERMS)), "only the administrator loads the map"
    html = render_page(REC_PAGE, "rec")
    assert html.count("window.KQ =") == 1 and html.find("window.KQ =") < html.find("<body"), "the map script stands in <head>"
    assert "window.KQ =" not in render_page("<html><head></head><body><main>x</main></body></html>", "live")
    if not kq_on():
        assert kq_search("Seon") == [] and '"on": false' in kq_head() and not kq_topo_on() and kq_layers() == {}
    tx = kq_tx()
    assert all(tx[L_]["OpenStreetMap contributors"] for L_ in ("de", "fr", "it", "rm")) and tx["de"]["OpenStreetMap contributors"] == "OpenStreetMap-Mitwirkende"
    assert all(tx[L_][k] for L_ in ("de", "fr", "it", "rm") for k in ("kq-ask", "kq-ask-topo", "Map style", "Hiking paths from OpenStreetMap – not the official network."))
    assert tx["en"]["kq-ask"] and tx["en"]["kq-ask-topo"]
    assert all("ß" not in v[0] for v in _HX_KQ.values()) and all(k in DE for k in _HX_KQ)
    assert _HELP_KQ["de"][0] in HELP_PAGE and _HELP_KQ["en"][0] in HELP_PAGE and "Topo" in _HELP_KQ["de"][1]
    # Topo: the setting (web + window), the styles, the credit, the switch
    assert ("Setup", "map_topo", _KQ_TOPO_LABEL) in TOGGLES and CFG.get("map_topo") in (True, False) and _KQ_TOPO_LABEL in DE
    assert all(_KQ_TOPO_LABEL in TRX[L_] for L_ in ("fr", "it", "rm"))
    assert KQ_STYLES[0] == "style.json" and set(KQ_LAYER.values()) == {"tiles", "topo", "relief"} and KQ_TTYPE["relief"] == (2, 4)
    for frag in ("swisstopo.admin.ch", "K.switchUI", "K.legend", "K.restyle", "mw-kq-style", "transformStyle", "MutationObserver"):
        assert frag in KQ_HEAD_JS, frag
    assert "K.switchUI($(\"#kq-map\"))" in KQ_PAGE and "K.legend()" in KQ_PAGE
    return True


SELFTEST_EXTRA.append(("Offline map of Switzerland (639zzq)", kq_selftest))
