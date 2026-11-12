#@ MoveEye – Teil 639zzc: «📁 Datentausch» – Dateien teilen unter Mehr und /tausch: «📂 Für alle» (mit Ordnern) und «👤 Meine Dateien», Vorschaubilder, Hochladen in Stücken (fortsetzbar, iPhone), Rechte pro Benutzer, Gäste nur ansehen, Grenzen und freier Speicher, Push gebündelt, Protokoll. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket des Besitzers «📁 Datentausch» (freigegeben 07.11.2026).
#   * Ort: Mehr → «📁 Datentausch» (kein Hauptreiter) und direkt /tausch; im Fenster ein Knopf unter «Mehr» (öffnet den Browser).
#   * Speicher: liegt die Aufnahmen auf einem USB-Stick / einer SSD (Einstellung «storage_path», Teil 420), dann
#     <Laufwerk>/MotionWatch/tausch - neben den Aufnahmen, nie darin (Werkseinstellungen löschen nur die Aufnahmen). Sonst im
#     Datenordner von MoveEye auf der Karte (~/.config/motionwatch/tausch). Ist das gewählte Laufwerk nicht eingesteckt, nimmt
#     der Datentausch nichts an (nie still auf die Karte). Updates lassen beide Ordner stehen. Die «Sicherung» (060) kopiert nur
#     Aufnahmen, das Diagnose-Paket und der Einstellungs-Export enthalten keine Dateien: der Datentausch ist in keiner Sicherung.
#   * Auf dem Laufwerk heissen die Dateien nur nach einer zufälligen Nummer (f/<id>.bin + f/<id>.json mit Name, Besitzer, Ordner):
#     ein Dateiname aus dem Browser wird nie ein Pfad. Ordner gibt es nur als Eintrag (ordner.json), eine Ebene unter «Für alle».
#   * Rechte (040 USER_PERMS / ROLE_PERMS): files_view (ansehen), files_down (herunterladen), files_up (hochladen, Ordner anlegen),
#     files_admin (alles verwalten, auch private Dateien anderer sehen und löschen). Ab Werk: Admin alles, Familie ansehen +
#     herunterladen + hochladen, Freund und «Nur ansehen» ansehen + herunterladen, Kind nichts; «Eigene Rechte» einzeln. Jedes
#     Datei-Recht schliesst «ansehen» ein, files_admin alle. Bestehende Benutzer bekommen die Rechte ihrer Rolle von selbst (die
#     Rollen sind Vorlagen); «Eigene Rechte» bleiben, wie sie sind (keine Datei-Rechte, bis der Admin sie ankreuzt).
#   * Eigene Dateien darf der Besitzer immer herunterladen und löschen; fremde löscht nur files_admin / der Admin.
#   * Gäste (Gast-Link /g/<token>, Ablauf wie das Live-Bild): nur «Für alle», nur Vorschaubilder (neu gerechnet), kein Download,
#     kein Hochladen, keine Namen der Hochlader. Schalter tausch_guest.
#   * Grenzen (Einstellungen → System → Datentausch, nur der Admin): gesamt 5 GB, pro Datei 200 MB, pro Benutzer 1 GB, auf dem
#     Speicher bleiben immer mindestens 2 GB frei. Platz wird beim Start eines Uploads reserviert (zwei gleichzeitige Uploads
#     können die Grenze nicht überlisten), bei jedem Stück wird der freie Speicher nochmals geprüft.
#   * Sicherheit: Namen bereinigt (nur der letzte Teil eines Pfads, NFC, keine Steuer- / Richtungszeichen, keine versteckten
#     Dateien, keine reservierten Windows-Namen), Programme und Skripte abgelehnt (Endung und erste Bytes: MZ, ELF, #!, Mach-O),
#     HTML / SVG / XML nur als Download ohne Vorschau. Download immer «attachment» mit nosniff und CSP sandbox; abspielen im
#     Browser nur Video / Ton (sandbox). Vorschaubilder neu gerechnet (keine Original-Bytes), Bildgrösse vorher geprüft (keine
#     Pixel-Bomben). CSRF wie überall (Origin-Prüfung in 550), Ratenbremse pro Benutzer bzw. Gast-Adresse, Protokoll aller
#     Uploads / Downloads / Löschungen (log_event «web»). Zu grosse Stücke werden vor dem Lesen abgewiesen.
#   * Push an den Admin (Notifier.info, 060 / 635b): gebündelt pro Benutzer «📁 Anna hat 3 Dateien hochgeladen» (90 s Ruhe
#     oder höchstens 10 Min.), nur Name + Anzahl, keine Dateinamen. Eigene Uploads des Admins ohne Push.
#   * Hochladen, das nicht hängen bleibt (Besitzer 08.11.2026: 5-MB-Foto vom iPhone blieb beim ersten 2-MB-Stück bei 0 %):
#     vorher ging jedes Stück als fetch(Datei-Ausschnitt) ohne Zeitgrenze – kam keine Antwort, begann der neue Versuch nie.
#     Jetzt (Seite): jedes Stück zuerst in den Speicher lesen (eigene Meldung, wenn die Datei nicht lesbar ist – iCloud-Foto),
#     senden mit Wächter (45 s ohne Fortschritt und ohne Antwort → abbrechen → neuer Versuch, 6 Versuche), erstes Stück 256 KB,
#     nach 2 Fehlern 512-KB-Stücke, nach 4 Fehlern 128 KB, Fortschritt auch innerhalb eines Stücks, «Stück 2 von 4», am Schluss
#     eine ehrliche Meldung mit «Nochmal versuchen» (macht weiter) und einer Diagnose-Zeile für ein Bildschirmfoto.
#     Gerät: ein Stück, dessen Daten 30 s nicht mehr kommen, wird mit 408 beantwortet (TZ_BODY_IDLE) statt für immer zu warten;
#     ein Stück wird erst geschrieben, wenn es ganz da ist; dasselbe Stück zweimal → 409 mit dem Stand (Sperre pro Upload).
#     HEIC (iPhone über «Dateien»; aus der Fotomediathek liefert Safari meist JPEG): wird gespeichert und als Bild geführt,
#     aber ohne Vorschau (OpenCV liest kein HEIC) – Symbol, «Keine Vorschau», Herunterladen geht.
#     Nicht beweisbar ohne echtes iPhone: ob Safari wirklich am Datei-Ausschnitt als Anfrage-Körper hängen blieb.
# Tests: werkzeuge/tausch_test.py (Rechte, Grenzen, Namen, Programme, Stücke, Löschen, Push, Bilder im Browser), Selbsttest
# tausch_selftest unten.
# ----------------------------------------------------------------------------
for _k, _v in {"tausch_on": True, "tausch_guest": True, "tausch_push": True, "tausch_block_exec": True, "tausch_total_gb": 5.0,
               "tausch_file_mb": 200.0, "tausch_user_gb": 1.0, "tausch_free_gb": 2.0}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)   # 636 took its copy before this part

TZ_PERMS = ("files_view", "files_down", "files_up", "files_admin")
# wraps: USER_PERMS
USER_PERMS = tuple(p for p in USER_PERMS if p not in TZ_PERMS) + TZ_PERMS
for _r, _p in {"family": ("files_view", "files_down", "files_up"), "friend": ("files_view", "files_down"),
               "view": ("files_view", "files_down")}.items():
    ROLE_PERMS[_r] = tuple(ROLE_PERMS.get(_r, ())) + tuple(p for p in _p if p not in ROLE_PERMS.get(_r, ()))
for _p in TZ_PERMS:                                       # role_guard (550) lets these through, the routes check the exact right
    PERM_GET[_p] = ("/tausch", "/tausch/", "/api/tausch")
    PERM_POST[_p] = {"/api/tausch", "/api/tausch/chunk"}
USER_UI_HIDE["files_view"] = 'a[href="/tausch"],#m-tausch'
USER_SETTINGS_DENY.update({"tausch_on", "tausch_guest", "tausch_push", "tausch_block_exec", "tausch_total_gb", "tausch_file_mb",
                           "tausch_user_gb", "tausch_free_gb"})
DEMO_BLOCK = tuple(DEMO_BLOCK) + ("/api/tausch",)         # wraps: DEMO_BLOCK (the demo fills no drive)

_user_perms_tz_base = user_perms


def user_perms(u):                                         # + 639zzc: every file right includes «see», files_admin all of them
    return tausch_imply(_user_perms_tz_base(u))


def tausch_imply(perms):
    P = set(perms or ())
    if "files_admin" in P:
        P.update(TZ_PERMS)
    if P & set(TZ_PERMS):
        P.add("files_view")
    return P


TZ_ID = re.compile(r"^[0-9a-f]{16}$")
TZ_CHUNK = 2 * 1024 * 1024                                 # one piece of an upload (iPhone, tunnel: small enough, few requests)
TZ_CHUNK_MAX = 8 * 1024 * 1024                             # bigger pieces are refused before they are read
TZ_BODY_IDLE = 30.0                                        # s: a piece whose data stops coming is given up (answer 408) - the browser
                                                           # (it waits 45 s) tries again with a smaller piece instead of hanging for ever
TZ_MAX_FILES = 5000
TZ_MAX_FOLDERS = 60
TZ_MAX_OPEN_UPS = 6                                        # open uploads per person
TZ_STALE = 24 * 3600                                       # an upload without a piece for a day is thrown away
TZ_PUSH_QUIET, TZ_PUSH_MAX = 90.0, 600.0                   # push: after 90 s without a new file, at the latest after 10 min
TZ_GB = 1024 ** 3
TZ_MB = 1024 ** 2
TZ = {"lock": threading.RLock(), "root": None, "files": None, "folders": None, "ups": {}, "rate": {}, "push": {},
      "thumbq": deque(), "thumb_run": False, "chats": {}, "waiters": {}, "waiting": 0, "push_run": False, "root_test": None, "pdftoppm": None}

# what a file is: extension -> (type for the browser, kind for the symbol / preview)
TZ_TYPES = {
    "jpg": ("image/jpeg", "image"), "jpeg": ("image/jpeg", "image"), "png": ("image/png", "image"), "gif": ("image/gif", "image"),
    "webp": ("image/webp", "image"), "bmp": ("image/bmp", "image"), "tif": ("image/tiff", "image"), "tiff": ("image/tiff", "image"),
    "heic": ("image/heic", "image"), "heif": ("image/heif", "image"),
    "mp4": ("video/mp4", "video"), "m4v": ("video/mp4", "video"), "mov": ("video/quicktime", "video"), "webm": ("video/webm", "video"),
    "mkv": ("video/x-matroska", "video"), "avi": ("video/x-msvideo", "video"), "3gp": ("video/3gpp", "video"),
    "mp3": ("audio/mpeg", "audio"), "m4a": ("audio/mp4", "audio"), "aac": ("audio/aac", "audio"), "ogg": ("audio/ogg", "audio"),
    "opus": ("audio/ogg", "audio"), "wav": ("audio/wav", "audio"), "flac": ("audio/flac", "audio"),
    "pdf": ("application/pdf", "pdf"),
    "txt": ("text/plain", "text"), "md": ("text/plain", "text"), "chat": ("application/octet-stream", "chat"),
    "csv": ("text/csv", "doc"), "rtf": ("application/rtf", "doc"),
    "doc": ("application/msword", "doc"), "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "doc"),
    "xls": ("application/vnd.ms-excel", "doc"), "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "doc"),
    "ppt": ("application/vnd.ms-powerpoint", "doc"), "pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", "doc"),
    "odt": ("application/vnd.oasis.opendocument.text", "doc"), "ods": ("application/vnd.oasis.opendocument.spreadsheet", "doc"),
    "odp": ("application/vnd.oasis.opendocument.presentation", "doc"), "pages": ("application/octet-stream", "doc"),
    "numbers": ("application/octet-stream", "doc"), "key": ("application/octet-stream", "doc"),
    "zip": ("application/zip", "archive"), "7z": ("application/x-7z-compressed", "archive"), "rar": ("application/vnd.rar", "archive"),
    "tar": ("application/x-tar", "archive"), "gz": ("application/gzip", "archive"), "tgz": ("application/gzip", "archive"),
    "bz2": ("application/x-bzip2", "archive"), "xz": ("application/x-xz", "archive"),
}
TZ_INLINE = {"video", "audio"}                             # played in the browser (sandbox); everything else only as download
# programs and scripts: refused (switch tausch_block_exec)
TZ_BLOCK_EXT = {"exe", "msi", "msp", "com", "scr", "pif", "bat", "cmd", "ps1", "psm1", "psd1", "vbs", "vbe", "js", "jse", "mjs", "cjs",
                "wsf", "wsh", "hta", "cpl", "dll", "sys", "drv", "lnk", "reg", "inf", "scf", "msc", "gadget", "jar", "class", "sh", "bash",
                "zsh", "ksh", "csh", "fish", "command", "tool", "py", "pyc", "pyo", "pyw", "pyz", "pl", "pm", "rb", "php", "php3",
                "php4", "php5", "phtml", "phar", "cgi", "asp", "aspx", "jsp", "lua", "tcl", "awk", "run", "bin", "elf", "out", "so",
                "ko", "deb", "rpm", "appimage", "snap", "flatpak", "apk", "xapk", "ipa", "app", "pkg", "mpkg", "dmg", "desktop",
                "service", "url", "webloc", "applescript", "scpt", "workflow", "action", "vb", "ws", "xbap", "application", "appref-ms"}
# active content: kept, but only as download (attachment, sandbox), never a preview
TZ_RISKY_EXT = {"html", "htm", "xhtml", "shtml", "svg", "svgz", "xml", "xsl", "xslt", "mht", "mhtml", "swf", "pdfxml", "xht"}
TZ_MAGIC_EXEC = (b"MZ", b"\x7fELF", b"#!", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe",
                 b"\xca\xfe\xba\xbe", b"dex\n")
_TZ_BAD_CH = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_TZ_WIN_RES = {"con", "prn", "aux", "nul"} | {f"com{i}" for i in range(10)} | {f"lpt{i}" for i in range(10)}


# ---- names ------------------------------------------------------------------------------------------------------------------
def tausch_clean_name(raw, folder=False):
    """(clean name, "") or (None, why). Only the last part of a path, NFC, no control / direction / invisible signs, no
    signs Windows / a USB stick cannot store, no hidden name («.x»), no reserved Windows name, at most 120 signs."""
    import unicodedata
    s = str(raw or "")
    s = s.replace("\\", "/").rsplit("/", 1)[-1]
    s = unicodedata.normalize("NFC", s)
    s = "".join(c for c in s if unicodedata.category(c)[0] != "C")      # Cc, Cf (bidi, zero width), Cs, Co, Cn
    s = _TZ_BAD_CH.sub("_", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.rstrip(". ")
    if not s:
        return None, "the file needs a name" if not folder else "the folder needs a name"
    if s.startswith("."):
        return None, "hidden files (name starts with «.») are not accepted"
    lim = 40 if folder else 120
    stem, ext = os.path.splitext(s)
    if folder:
        stem, ext = s, ""
    if stem.split(".")[0].strip().lower() in _TZ_WIN_RES:
        stem = "_" + stem
        s = stem + ext
    if len(s) > lim:
        ext = ext[:16]
        s = stem[:lim - len(ext)].rstrip(". ") + ext
    while len(s.encode("utf-8")) > 240:                        # file systems: 255 bytes
        s = s[:-1]
    return s, ""


def tausch_ext(name):
    return os.path.splitext(str(name or ""))[1].lower().lstrip(".")


def tausch_blocked(name):
    """is this name a program / script? (only with tausch_block_exec, the default) - every extension counts («x.exe.txt» not)"""
    if not CFG.get("tausch_block_exec", True):
        return False
    return tausch_ext(name) in TZ_BLOCK_EXT


def tausch_magic_exec(head):
    return bool(CFG.get("tausch_block_exec", True)) and any(bytes(head[:8]).startswith(m) for m in TZ_MAGIC_EXEC)


def tausch_type(name):
    """(mime, kind, risky) - by the extension only (what the browser says is never trusted)"""
    e = tausch_ext(name)
    if e in TZ_RISKY_EXT:
        return "application/octet-stream", "risky", True
    mime, kind = TZ_TYPES.get(e, ("application/octet-stream", "other"))
    return mime, kind, False


# ---- where the files are ----------------------------------------------------------------------------------------------------
def _tz_drive_ok(want):
    """the chosen drive (storage_path) is really there - not the empty folder of an unplugged stick on the card"""
    want = os.path.abspath(want)
    if not os.path.isdir(want):
        return False
    if want.startswith(("/media/", "/mnt/")):
        q = want
        while q not in ("/", "/media", "/mnt") and not os.path.ismount(q):
            q = os.path.dirname(q)
        return q not in ("/", "/media", "/mnt")
    return True


def tausch_root():
    """(folder, kind, problem): kind usb / ssd / sd / disk; problem "missing" (chosen drive not there) / "ro" (card protected)"""
    if TZ.get("root_test"):
        return TZ["root_test"], "sd", ""
    want = str(CFG.get("storage_path") or "").strip()
    if want:
        if not _tz_drive_ok(want):
            return "", "usb", "missing"
        k = _dev_kind(_mount_of(want)[0])
        return os.path.join(want, "MotionWatch", "tausch"), ("ssd" if k == "ssd" else "usb" if k in ("usb", "other") else k), ""
    root = os.path.join(DATA_DIR, "tausch")
    k = _dev_kind(_mount_of(DATA_DIR)[0])
    try:
        if k == "sd" and SDCARD.get("overlay"):
            return root, "sd", "ro"                      # 067: write protection - the files would be gone after a restart
    except NameError:
        pass
    return root, {"sd": "sd", "ssd": "ssd", "usb": "usb"}.get(k, "disk"), ""


def tausch_disk_free(path):
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return 0


def _tz_write_json(path, obj):
    tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        f.flush()
    os.replace(tmp, path)


def _tz_meta_ok(m):
    return (isinstance(m, dict) and TZ_ID.match(str(m.get("id", ""))) and isinstance(m.get("name"), str) and m.get("area") in ("all", "mine")
            and isinstance(m.get("owner"), str) and isinstance(m.get("size"), int) and isinstance(m.get("folder", ""), str))


def _tz_load():
    """the list of files of the present storage (cached; a new storage = read again). None = no storage now."""
    root, _kind, prob = tausch_root()
    if not root or prob == "missing":
        return None
    with TZ["lock"]:
        if TZ["root"] == root and TZ["files"] is not None:
            return root
        files, folders, ups = {}, [], {}
        try:
            for sub in ("f", "t", "up"):
                os.makedirs(os.path.join(root, sub), exist_ok=True)
        except OSError as e:
            log_event("sys", f"Digital backpack: folder {root} cannot be made: {e}"[:180])
            return None
        for nm in os.listdir(os.path.join(root, "f")):
            if not nm.endswith(".json") or not TZ_ID.match(nm[:-5]):
                continue
            try:
                with open(os.path.join(root, "f", nm), encoding="utf-8") as f:
                    m = json.load(f)
            except (OSError, ValueError):
                continue
            if _tz_meta_ok(m) and m["id"] == nm[:-5] and os.path.isfile(os.path.join(root, "f", m["id"] + ".bin")):
                files[m["id"]] = m
        try:
            with open(os.path.join(root, "ordner.json"), encoding="utf-8") as f:
                folders = [x for x in json.load(f) if isinstance(x, dict) and isinstance(x.get("name"), str)][:TZ_MAX_FOLDERS]
        except (OSError, ValueError, TypeError):
            folders = []
        now = time.time()
        upd = os.path.join(root, "up")
        names = os.listdir(upd)
        for nm in names:                                     # 1: open uploads that had a piece within a day (survive a restart)
            if not (nm.endswith(".json") and TZ_ID.match(nm[:-5])):
                continue
            part = os.path.join(upd, nm[:-5] + ".part")
            try:
                with open(os.path.join(upd, nm), encoding="utf-8") as f:
                    u = json.load(f)
                if isinstance(u, dict) and isinstance(u.get("size"), int) and isinstance(u.get("owner"), str) and now - os.path.getmtime(part) < TZ_STALE:
                    u["have"] = os.path.getsize(part)
                    u["lock"] = threading.Lock()
                    ups[nm[:-5]] = u
            except (OSError, ValueError, AttributeError):
                pass
        for nm in names:                                     # 2: everything else in up/ goes away
            if nm.endswith((".json", ".part")) and nm[:-5] in ups:
                continue
            try:
                os.remove(os.path.join(upd, nm))
            except OSError:
                pass
        TZ.update(root=root, files=files, folders=folders, ups=ups, chats={})
        missing = [fid for fid, m in files.items() if m.get("thumb") is None and m.get("kind") in ("image", "video", "pdf")]
    for fid in missing:
        tausch_thumb_queue(fid)
    return root


def _tz_folders_save(root):
    _tz_write_json(os.path.join(root, "ordner.json"), TZ["folders"])


# ---- who is asking, what may they do ----------------------------------------------------------------------------------------
def tausch_who(g_):
    """{"key", "name", "admin", "perms"} of the request (administrator / app key = everything)"""
    role = getattr(g_, "role", "admin")
    if role == "admin":
        return {"key": "admin", "name": "Admin", "admin": True, "perms": set(TZ_PERMS), "is_admin": True}
    u = user_get(getattr(g_, "user", ""))
    P = user_perms(u) if u else tausch_imply(ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))
    P = {p for p in P if p in TZ_PERMS}
    name = u["name"] if u else str(getattr(g_, "user", "") or "?")
    return {"key": name.lower(), "name": name, "admin": "files_admin" in P, "perms": P, "is_admin": False}


def tausch_can_see(m, who):
    if "files_view" not in who["perms"]:
        return False
    return m["area"] == "all" or m["owner"] == who["key"] or who["admin"]


def tausch_can_down(m, who):
    return tausch_can_see(m, who) and ("files_down" in who["perms"] or m["owner"] == who["key"])


def tausch_can_del(m, who):
    return tausch_can_see(m, who) and (m["owner"] == who["key"] or who["admin"])


def tausch_rate(key, kind, limit, per=600.0, now=None):
    """True = allowed (and counted); a simple sliding window per person (or guest address) and kind"""
    now = time.time() if now is None else now
    with TZ["lock"]:
        R = TZ["rate"]
        lst = [x for x in R.get((key, kind), []) if now - x < per]
        if len(lst) >= limit:
            R[(key, kind)] = lst
            return False
        lst.append(now)
        R[(key, kind)] = lst
        if len(R) > 3000:
            for k in [k for k, v in R.items() if not v or now - v[-1] > per]:
                R.pop(k, None)
    return True


# ---- room ---------------------------------------------------------------------------------------------------------------------
def tausch_usage(owner=None):
    """(bytes of the files, bytes reserved by open uploads) - all, or of one owner"""
    with TZ["lock"]:
        f = sum(m["size"] + int(m.get("hist_size") or 0) for m in (TZ["files"] or {}).values() if owner is None or m["owner"] == owner)
        r = sum(u["size"] for u in TZ["ups"].values() if owner is None or u["owner"] == owner)
    return f, r


def tausch_limits():
    return {"total": int(float(CFG.get("tausch_total_gb", 5.0)) * TZ_GB), "file": int(float(CFG.get("tausch_file_mb", 200.0)) * TZ_MB),
            "user": int(float(CFG.get("tausch_user_gb", 1.0)) * TZ_GB), "min_free": int(float(CFG.get("tausch_free_gb", 2.0)) * TZ_GB)}


def tausch_fmt(n, lang=None):
    """«2,1 GB» / «350 MB» (comma in de / fr / it / rm)"""
    L = cur_lang(lang)
    n = float(n or 0)
    if n >= TZ_GB:
        s, u = f"{n / TZ_GB:.1f}", "GB"
    elif n >= TZ_MB:
        s, u = f"{n / TZ_MB:.0f}", "MB"
    else:
        s, u = f"{max(1.0, n / 1024) if n else 0:.0f}", "KB"
    if s.endswith(".0"):
        s = s[:-2]
    return (s if L == "en" else s.replace(".", ",")) + " " + u


def tausch_room_error(size, who, lang=None):
    """"" = this file fits; else a clear text (file / total / person / free space on the storage)"""
    lim = tausch_limits()
    root = TZ["root"] or ""
    if size > lim["file"]:
        return trf("Too big: at most {n} per file.", lang, n=tausch_fmt(lim["file"], lang))
    with TZ["lock"]:
        if len(TZ["files"] or {}) + len(TZ["ups"]) >= TZ_MAX_FILES:
            return trf("Too many files (at most {n}) - delete old ones first.", lang, n=TZ_MAX_FILES)
    used, res = tausch_usage()
    if used + res + size > lim["total"]:
        return trf("The file exchange is full: {a} of {b} used. Delete old files first.", lang, a=tausch_fmt(used + res, lang),
                   b=tausch_fmt(lim["total"], lang))
    if not who.get("is_admin"):
        u, ur = tausch_usage(who["key"])
        if u + ur + size > lim["user"]:
            return trf("Your space is full: {a} of {b} used. Delete some of your files first.", lang, a=tausch_fmt(u + ur, lang),
                       b=tausch_fmt(lim["user"], lang))
    with TZ["lock"]:
        rest = sum(max(0, u["size"] - u.get("have", 0)) for u in TZ["ups"].values())
    if tausch_disk_free(root) - rest - size < lim["min_free"]:
        return trf("Not enough free space on the storage: MoveEye always keeps {n} free (for recordings and the system).", lang,
                   n=tausch_fmt(lim["min_free"], lang))
    return ""


# ---- the list -----------------------------------------------------------------------------------------------------------------
def tausch_public(m, who=None):
    mime, kind, risky = tausch_type(m["name"])
    d = {"id": m["id"], "name": m["name"], "area": m["area"], "folder": m.get("folder", ""), "size": m["size"], "t": m.get("t", 0),
         "kind": kind, "ext": tausch_ext(m["name"])[:8], "thumb": m.get("thumb"), "risky": risky,
         "inline": kind in TZ_INLINE}
    if who is not None:
        d.update(by=m.get("owner_name") or m["owner"], mine=m["owner"] == who["key"], dl=tausch_can_down(m, who), rm=tausch_can_del(m, who),
                 edit=kind in ("text", "chat") and tausch_can_edit(m, who))
    return d


def tausch_list(who, area="all", folder="", lang=None):
    root = _tz_load()
    r0, kind, prob = tausch_root()
    lim = tausch_limits()
    out = {"ok": True, "on": bool(CFG.get("tausch_on", True)), "area": area, "folder": folder, "files": [], "folders": [],
           "perms": sorted(who["perms"]), "me": {"name": who["name"], "admin": who["admin"], "is_admin": who["is_admin"]},
           "store": {"kind": kind, "problem": prob}, "chunk": TZ_CHUNK, "ups": []}
    if root is None:
        out["store"]["problem"] = prob or "missing"
        out["quota"] = {"used": 0, "total": lim["total"], "file_max": lim["file"], "free": 0, "min_free": lim["min_free"]}
        return out
    used, res = tausch_usage()
    mu, mr = tausch_usage(who["key"])
    out["quota"] = {"used": used + res, "total": lim["total"], "file_max": lim["file"], "free": tausch_disk_free(root),
                    "min_free": lim["min_free"], "user_used": mu + mr, "user_max": None if who["is_admin"] else lim["user"]}
    if "files_view" not in who["perms"]:
        return out
    with TZ["lock"]:
        files = list(TZ["files"].values())
        folders = list(TZ["folders"])
        ups = [{"id": k, "name": u["name"], "size": u["size"], "have": u.get("have", 0), "area": u["area"], "folder": u.get("folder", "")}
               for k, u in TZ["ups"].items() if u["owner"] == who["key"]]
    out["ups"] = ups
    if area == "all":
        if folder and not any(x["name"] == folder for x in folders):
            out["ok"] = False
            out["error"] = tr("This folder does not exist (any more).", lang)
            return out
        if not folder:
            for x in folders:
                inside = [m for m in files if m["area"] == "all" and m.get("folder") == x["name"]]
                out["folders"].append({"name": x["name"], "n": len(inside), "size": sum(m["size"] for m in inside), "t": x.get("t", 0),
                                       "by": x.get("by_name", ""), "rm": who["admin"] or (x.get("by") == who["key"] and not inside)})
        out["files"] = [tausch_public(m, who) for m in files if m["area"] == "all" and m.get("folder", "") == folder]
    else:
        out["files"] = [tausch_public(m, who) for m in files if m["area"] == "mine" and (m["owner"] == who["key"] or who["admin"])]
    out["files"].sort(key=lambda x: -x["t"])
    return out


# ---- upload: start, pieces, finish, abort --------------------------------------------------------------------------------------
def tausch_up_start(who, d, lang=None):
    if not CFG.get("tausch_on", True):
        return False, tr("The file exchange is switched off.", lang), {}
    if "files_up" not in who["perms"]:
        return False, tr("You may not upload files.", lang), {}
    root = _tz_load()
    r0, kind, prob = tausch_root()
    if root is None:
        return False, tr("The storage (USB stick / SSD) is not there - plug it in again.", lang), {}
    if prob == "ro":
        return False, tr("The memory card is write-protected (overlay) - files would be lost at the next restart. Use a USB stick.", lang), {}
    name, why = tausch_clean_name(d.get("name"))
    if name is None:
        return False, tr(why, lang), {}
    if tausch_ext(name) == "chat":
        return False, tr("Chats are made with «New chat».", lang), {}
    if tausch_blocked(name):
        return False, trf("Programs and scripts are not accepted (.{e}). Pack them into a ZIP if you really need to share them.", lang,
                          e=tausch_ext(name)), {}
    try:
        size = int(d.get("size"))
    except (TypeError, ValueError):
        return False, tr("unknown size", lang), {}
    if size < 0:
        return False, tr("unknown size", lang), {}
    area = "mine" if d.get("area") == "mine" else "all"
    folder = str(d.get("folder") or "") if area == "all" else ""
    try:
        lastmod = int(float(d.get("lastmod") or 0))
    except (TypeError, ValueError):
        lastmod = 0
    with TZ["lock"]:
        if folder and not any(x["name"] == folder for x in TZ["folders"]):
            return False, tr("This folder does not exist (any more).", lang), {}
        for uid, u in TZ["ups"].items():                     # the same file again: continue where it stopped
            if (u["owner"] == who["key"] and u["name"] == name and u["size"] == size and u["area"] == area
                    and u.get("folder", "") == folder and u.get("lastmod", 0) == lastmod):
                u["t"] = time.time()
                return True, "", {"id": uid, "have": u.get("have", 0), "chunk": TZ_CHUNK, "name": name, "resumed": u.get("have", 0) > 0}
        if sum(1 for u in TZ["ups"].values() if u["owner"] == who["key"]) >= TZ_MAX_OPEN_UPS:
            return False, tr("Too many uploads at the same time - wait until the others are done.", lang), {}
    if not tausch_rate(who["key"], "up", 150):
        return False, tr("Too many uploads in a short time - wait a few minutes.", lang), {}
    err = tausch_room_error(size, who, lang)
    if err:
        return False, err, {}
    uid = secrets.token_hex(8)
    u = {"owner": who["key"], "owner_name": who["name"], "name": name, "size": size, "area": area, "folder": folder, "lastmod": lastmod,
         "t0": time.time(), "t": time.time()}
    try:
        open(os.path.join(root, "up", uid + ".part"), "wb").close()
        _tz_write_json(os.path.join(root, "up", uid + ".json"), u)
    except OSError as e:
        return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", {}
    with TZ["lock"]:
        TZ["ups"][uid] = dict(u, have=0, lock=threading.Lock())
    return True, "", {"id": uid, "have": 0, "chunk": TZ_CHUNK, "name": name, "resumed": False}


def _tz_up_get(who, uid, lang=None):
    if not TZ_ID.match(str(uid or "")):
        return None, tr("unknown upload", lang)
    with TZ["lock"]:
        u = TZ["ups"].get(uid)
    if u is None or u["owner"] != who["key"]:
        return None, tr("unknown upload", lang)
    return u, ""


def tausch_up_chunk(who, uid, off, data, lang=None):
    """(ok, error, have, http code) - a piece must come exactly at the end of what is there (else 409 with «have»)"""
    if "files_up" not in who["perms"] or not CFG.get("tausch_on", True):
        return False, tr("You may not upload files.", lang), 0, 403
    root = _tz_load()
    if root is None:
        return False, tr("The storage (USB stick / SSD) is not there - plug it in again.", lang), 0, 409
    u, err = _tz_up_get(who, uid, lang)
    if u is None:
        return False, err, 0, 404
    if len(data) > TZ_CHUNK_MAX:
        return False, tr("piece too big", lang), u.get("have", 0), 413
    if not u["lock"].acquire(timeout=30):
        return False, tr("busy - try again", lang), u.get("have", 0), 409
    try:
        have = u.get("have", 0)
        if off != have:
            return False, "offset", have, 409
        if have + len(data) > u["size"]:
            return False, tr("more data than announced", lang), have, 400
        lim = tausch_limits()
        rest = u["size"] - have - len(data)
        if tausch_disk_free(root) - len(data) - rest < lim["min_free"] - TZ_CHUNK_MAX:
            return False, trf("Not enough free space on the storage: MoveEye always keeps {n} free (for recordings and the system).", lang,
                              n=tausch_fmt(lim["min_free"], lang)), have, 507
        p = os.path.join(root, "up", uid + ".part")
        try:
            with open(p, "r+b") as f:
                f.seek(have)
                f.write(data)
                f.truncate()
        except OSError as e:
            return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", have, 507
        u["have"] = have + len(data)
        u["t"] = time.time()
        return True, "", u["have"], 200
    finally:
        u["lock"].release()


def tausch_up_finish(who, uid, lang=None):
    root = _tz_load()
    if root is None:
        return False, tr("The storage (USB stick / SSD) is not there - plug it in again.", lang), {}
    u, err = _tz_up_get(who, uid, lang)
    if u is None:
        return False, err, {}
    with u["lock"]:
        if u.get("have", 0) != u["size"]:
            return False, tr("The upload is not complete yet.", lang), {"have": u.get("have", 0)}
        part = os.path.join(root, "up", uid + ".part")
        try:
            with open(part, "rb") as f:
                head = f.read(16)
        except OSError:
            head = b""
        if tausch_magic_exec(head):
            tausch_up_abort(who, uid, lang, _locked=True)
            log_event("web", f"Digital backpack: {who['name']} tried to upload a program («{u['name']}») - refused")
            return False, tr("This file is a program or script - not accepted.", lang), {}
        with TZ["lock"]:
            folder = u.get("folder", "")
            if folder and not any(x["name"] == folder for x in TZ["folders"]):
                folder = ""                                  # the folder was deleted meanwhile: into «Für alle»
            name = _tz_unique(u["name"], u["area"], folder, u["owner"])
            fid = secrets.token_hex(8)
            while fid in TZ["files"]:
                fid = secrets.token_hex(8)
            mime, kind, risky = tausch_type(name)
            m = {"id": fid, "name": name, "area": u["area"], "folder": folder, "owner": u["owner"], "owner_name": u.get("owner_name") or u["owner"],
                 "size": u["size"], "t": int(time.time()), "kind": kind, "thumb": None if kind in ("image", "video", "pdf") and not risky else False}
            try:
                os.replace(part, os.path.join(root, "f", fid + ".bin"))
                _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
            except OSError as e:
                return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", {}
            TZ["files"][fid] = m
            TZ["ups"].pop(uid, None)
        try:
            os.remove(os.path.join(root, "up", uid + ".json"))
        except OSError:
            pass
    where = "Für alle" + (" / " + folder if folder else "") if m["area"] == "all" else "privat"
    log_event("web", f"Digital backpack: {who['name']} uploaded «{name}» ({tausch_fmt(m['size'], 'de')}, {where})")
    if m["thumb"] is None:
        tausch_thumb_queue(fid)
    tausch_push_note(who)
    return True, "", {"file": tausch_public(m, who)}


def tausch_up_abort(who, uid, lang=None, _locked=False):
    root = TZ["root"] or _tz_load()
    u, err = _tz_up_get(who, uid, lang)
    if u is None:
        return False, err
    with TZ["lock"]:
        TZ["ups"].pop(uid, None)
    for ext in (".part", ".json"):
        try:
            os.remove(os.path.join(root, "up", uid + ext))
        except OSError:
            pass
    return True, ""


def _tz_unique(name, area, folder, owner):
    """«Bild.jpg» -> «Bild (2).jpg» when the same name is already there (same place; private: same owner)"""
    taken = {m["name"].lower() for m in TZ["files"].values() if m["area"] == area and m.get("folder", "") == folder
             and (area == "all" or m["owner"] == owner)}
    if name.lower() not in taken:
        return name
    stem, ext = os.path.splitext(name)
    for i in range(2, 1000):
        n = f"{stem} ({i}){ext}"
        if n.lower() not in taken:
            return n
    return f"{stem} ({secrets.token_hex(2)}){ext}"


# ---- delete, folders -----------------------------------------------------------------------------------------------------------
def tausch_delete(who, fid, lang=None):
    root = _tz_load()
    if root is None or not TZ_ID.match(str(fid or "")):
        return False, tr("unknown file", lang)
    with TZ["lock"]:
        m = TZ["files"].get(fid)
        if m is None or not tausch_can_see(m, who):
            return False, tr("unknown file", lang)
        if not tausch_can_del(m, who):
            return False, tr("Only the person who uploaded it (or the administrator) may delete this file.", lang)
        if not tausch_rate(who["key"], "rm", 300):
            return False, tr("Too many changes in a short time - wait a few minutes.", lang)
        TZ["files"].pop(fid, None)
    for p in (os.path.join(root, "f", fid + ".bin"), os.path.join(root, "f", fid + ".json"), os.path.join(root, "t", fid + ".jpg"),
              os.path.join(root, "t", fid + "_p.jpg")):
        try:
            os.remove(p)
        except OSError:
            pass
    shutil.rmtree(os.path.join(root, "h", fid), ignore_errors=True)
    with TZ["lock"]:
        TZ["chats"].pop(fid, None)
    log_event("web", f"Digital backpack: {who['name']} deleted «{m['name']}» (from {m.get('owner_name') or m['owner']})")
    return True, ""


def tausch_mkdir(who, name, lang=None):
    if "files_up" not in who["perms"] or not CFG.get("tausch_on", True):
        return False, tr("You may not create folders.", lang)
    root = _tz_load()
    if root is None:
        return False, tr("The storage (USB stick / SSD) is not there - plug it in again.", lang)
    n, why = tausch_clean_name(name, folder=True)
    if n is None:
        return False, tr(why, lang)
    with TZ["lock"]:
        if any(x["name"].lower() == n.lower() for x in TZ["folders"]):
            return False, tr("This folder exists already.", lang)
        if len(TZ["folders"]) >= TZ_MAX_FOLDERS:
            return False, trf("At most {n} folders.", lang, n=TZ_MAX_FOLDERS)
        if not tausch_rate(who["key"], "rm", 300):
            return False, tr("Too many changes in a short time - wait a few minutes.", lang)
        TZ["folders"].append({"name": n, "by": who["key"], "by_name": who["name"], "t": int(time.time())})
        TZ["folders"].sort(key=lambda x: x["name"].lower())
        _tz_folders_save(root)
    log_event("web", f"Digital backpack: {who['name']} created the folder «{n}»")
    return True, ""


def tausch_rmdir(who, name, force=False, lang=None):
    """an empty folder: its creator or files_admin; with files inside only files_admin and «force» (the files are deleted)"""
    root = _tz_load()
    if root is None:
        return False, tr("unknown folder", lang)
    with TZ["lock"]:
        x = next((f for f in TZ["folders"] if f["name"] == name), None)
        if x is None:
            return False, tr("unknown folder", lang)
        inside = [m["id"] for m in TZ["files"].values() if m["area"] == "all" and m.get("folder") == name]
        if inside and not (who["admin"] and force):
            return False, tr("The folder is not empty - only the administrator can delete it with all files.", lang)
        if not inside and not (who["admin"] or x.get("by") == who["key"]):
            return False, tr("Only the person who created it (or the administrator) may delete this folder.", lang)
        TZ["folders"] = [f for f in TZ["folders"] if f is not x]
        _tz_folders_save(root)
    for fid in inside:
        tausch_delete(who, fid, lang)
    log_event("web", f"Digital backpack: {who['name']} deleted the folder «{name}»" + (f" with {len(inside)} files" if inside else ""))
    return True, ""


# ---- 📝 text files in the browser (.txt / .md): versions, «somebody changed it meanwhile» ------------------------------------
# A save sends the version it loaded («ver»); is the file newer, nothing is written and the answer says who changed it (the
# page offers: differences / overwrite / save mine as a copy). The last TZ_HIST versions stay (h/<id>/<ver>.txt) and count
# in the space of the file's owner. Editing = the right «upload» (files_up); private texts only their owner / files_admin.
TZ_TEXT_EXT = {"txt", "md"}
TZ_TEXT_MAX = 1024 * 1024
TZ_HIST = 20
TZ_POST_MAX = 4096                                        # one chat post (bytes)
TZ_CHAT_MAX = 2 * 1024 * 1024                             # one chat file
TZ_EDIT_WIN = 300                                         # own posts: change / delete within 5 minutes
TZ_WAIT_MAX, TZ_WAIT_IP, TZ_WAIT_S = 24, 4, 20.0          # long poll of open chats: at most 24 (4 per address), 20 s each
TZ_CHAT_COND = threading.Condition()
_TZ_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f​-‏‪-‮⁦-⁩]")


def tausch_file(fid):
    if not TZ_ID.match(str(fid or "")) or _tz_load() is None:
        return None
    with TZ["lock"]:
        return TZ["files"].get(fid)


def tausch_is_text(m):
    return tausch_ext(m["name"]) in TZ_TEXT_EXT


def tausch_can_edit(m, who):
    """write a text / in a chat: the right «upload»; private ones only the owner (or files_admin)"""
    return (bool(CFG.get("tausch_on", True)) and tausch_can_see(m, who) and "files_up" in who["perms"]
            and (m["area"] == "all" or m["owner"] == who["key"] or who["admin"]))


def _tz_extra_room(extra, owner, lang=None):
    """"" = «extra» more bytes fit (total, the owner's space, free storage)"""
    lim = tausch_limits()
    used, res = tausch_usage()
    if used + res + extra > lim["total"]:
        return trf("The file exchange is full: {a} of {b} used. Delete old files first.", lang, a=tausch_fmt(used + res, lang), b=tausch_fmt(lim["total"], lang))
    if owner != "admin":
        u, ur = tausch_usage(owner)
        if u + ur + extra > lim["user"]:
            return trf("Your space is full: {a} of {b} used. Delete some of your files first.", lang, a=tausch_fmt(u + ur, lang), b=tausch_fmt(lim["user"], lang))
    if tausch_disk_free(TZ["root"] or "") - extra < lim["min_free"]:
        return trf("Not enough free space on the storage: MoveEye always keeps {n} free (for recordings and the system).", lang, n=tausch_fmt(lim["min_free"], lang))
    return ""


def _tz_read(root, fid, v=None):
    p = os.path.join(root, "h", fid, f"{int(v)}.txt") if v else os.path.join(root, "f", fid + ".bin")
    with open(p, "rb") as f:
        return f.read(TZ_TEXT_MAX + 1).decode("utf-8", errors="replace")


def tausch_text_get(who, fid, v=None, lang=None):
    m = tausch_file(fid)
    if m is None or (who is not None and not tausch_can_see(m, who)) or (who is None and m["area"] != "all"):
        return False, tr("unknown file", lang), {}
    if not tausch_is_text(m):
        return False, tr("This is not a text file.", lang), {}
    if m["size"] > TZ_TEXT_MAX:
        return False, trf("Too big for the editor (at most {n}) - download it instead.", lang, n=tausch_fmt(TZ_TEXT_MAX, lang)), {}
    try:
        if v and not any(h["v"] == int(v) for h in m.get("hist") or []):
            return False, tr("This version is not kept any more.", lang), {}
        txt = _tz_read(TZ["root"], fid, v)
    except (OSError, ValueError):
        return False, tr("unknown file", lang), {}
    out = {"id": fid, "name": m["name"], "text": txt, "ver": int(m.get("ver") or 1), "md": tausch_ext(m["name"]) == "md",
           "t": m.get("ed_t") or m.get("t", 0), "v": int(v) if v else None}
    if who is not None:
        out.update(by=m.get("ed_name") or m.get("owner_name") or m["owner"], edit=tausch_can_edit(m, who),
                   hist=[{"v": h["v"], "t": h["t"], "by": h.get("by", ""), "size": h["size"]} for h in reversed(m.get("hist") or [])])
    return True, "", out


def tausch_text_save(who, fid, text, ver, lang=None, restore=None):
    """(ok, error, extra) - extra {"conflict": True, "by", "ver", "text"} when somebody saved meanwhile"""
    m = tausch_file(fid)
    if m is None or not tausch_can_see(m, who):
        return False, tr("unknown file", lang), {}
    if not tausch_is_text(m):
        return False, tr("This is not a text file.", lang), {}
    if not tausch_can_edit(m, who):
        return False, tr("You may not change this text.", lang), {}
    root = TZ["root"]
    if restore is not None:
        ok, err, old = tausch_text_get(who, fid, restore, lang)
        if not ok:
            return False, err, {}
        text = old["text"]
    if not isinstance(text, str):
        return False, tr("no text", lang), {}
    enc = text.encode("utf-8")
    if len(enc) > TZ_TEXT_MAX:
        return False, trf("Too big for the editor (at most {n}) - download it instead.", lang, n=tausch_fmt(TZ_TEXT_MAX, lang)), {}
    if not tausch_rate(who["key"], "save", 240):
        return False, tr("Too many changes in a short time - wait a few minutes.", lang), {}
    with TZ["lock"]:
        cur = int(m.get("ver") or 1)
        try:
            ver = int(ver)
        except (TypeError, ValueError):
            ver = -1
        if ver != cur:
            try:
                now_txt = _tz_read(root, fid)
            except OSError:
                now_txt = ""
            return False, trf("Meanwhile {who} has changed something.", lang, who=m.get("ed_name") or m.get("owner_name") or "?"), {
                "conflict": True, "by": m.get("ed_name") or m.get("owner_name") or "", "ver": cur, "text": now_txt, "t": m.get("ed_t") or m.get("t", 0)}
        err = _tz_extra_room(len(enc), m["owner"], lang)
        if err:
            return False, err, {}
        hd = os.path.join(root, "h", fid)
        try:
            os.makedirs(hd, exist_ok=True)
            shutil.copyfile(os.path.join(root, "f", fid + ".bin"), os.path.join(hd, f"{cur}.txt"))
            hist = list(m.get("hist") or []) + [{"v": cur, "t": m.get("ed_t") or m.get("t", 0), "by": m.get("ed_name") or m.get("owner_name") or "",
                                                 "size": m["size"]}]
            for h in hist[:-TZ_HIST]:
                try:
                    os.remove(os.path.join(hd, f"{h['v']}.txt"))
                except OSError:
                    pass
            hist = hist[-TZ_HIST:]
            tmp = os.path.join(root, "f", fid + ".bin.tmp")
            with open(tmp, "wb") as f:
                f.write(enc)
            os.replace(tmp, os.path.join(root, "f", fid + ".bin"))
        except OSError as e:
            return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", {}
        m.update(size=len(enc), ver=cur + 1, ed_name=who["name"], ed_t=int(time.time()), hist=hist, hist_size=sum(h["size"] for h in hist))
        _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
    log_event("web", f"Digital backpack: {who['name']} " + (f"restored version {restore} of" if restore is not None else "changed") + f" «{m['name']}» (version {cur + 1})")
    return True, "", {"ver": cur + 1}


def tausch_create(who, d, kind, lang=None):
    """«📝 New text» / «💬 New chat»: an empty file (a text may bring its first content: «save mine as a copy»)"""
    if "files_up" not in who["perms"] or not CFG.get("tausch_on", True):
        return False, tr("You may not upload files.", lang), {}
    root = _tz_load()
    if root is None:
        return False, tr("The storage (USB stick / SSD) is not there - plug it in again.", lang), {}
    name, why = tausch_clean_name(d.get("name"))
    if name is None:
        return False, tr(why, lang), {}
    if kind == "chat":
        name = (name[:-5] if name.lower().endswith(".chat") else name)[:110] + ".chat"
    elif tausch_ext(name) not in TZ_TEXT_EXT:
        name = name[:115] + ".txt"
    text = str(d.get("text") or "") if kind == "text" else ""
    enc = text.encode("utf-8")
    if len(enc) > TZ_TEXT_MAX:
        return False, trf("Too big for the editor (at most {n}) - download it instead.", lang, n=tausch_fmt(TZ_TEXT_MAX, lang)), {}
    area = "mine" if d.get("area") == "mine" else "all"
    folder = str(d.get("folder") or "") if area == "all" else ""
    if not tausch_rate(who["key"], "up", 150):
        return False, tr("Too many uploads in a short time - wait a few minutes.", lang), {}
    err = tausch_room_error(len(enc), who, lang)
    if err:
        return False, err, {}
    with TZ["lock"]:
        if folder and not any(x["name"] == folder for x in TZ["folders"]):
            return False, tr("This folder does not exist (any more).", lang), {}
        name = _tz_unique(name, area, folder, who["key"])
        fid = secrets.token_hex(8)
        m = {"id": fid, "name": name, "area": area, "folder": folder, "owner": who["key"], "owner_name": who["name"], "size": len(enc),
             "t": int(time.time()), "kind": kind, "thumb": False, "ver": 1}
        try:
            with open(os.path.join(root, "f", fid + ".bin"), "wb") as f:
                f.write(enc)
            _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
        except OSError as e:
            return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", {}
        TZ["files"][fid] = m
    log_event("web", f"Digital backpack: {who['name']} created «{name}»")
    return True, "", {"file": tausch_public(m, who)}


# ---- 💬 chat files: one post per line (JSON), appended on the server with name and time ----------------------------------------
def _tz_chat(m):
    """the posts of a chat (cached): {"posts", "rev" (every change), "erev" (last change / deletion)}"""
    with TZ["lock"]:
        ch = TZ["chats"].get(m["id"])
        if ch is not None:
            return ch
        posts = []
        try:
            with open(os.path.join(TZ["root"], "f", m["id"] + ".bin"), encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        x = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(x, dict) and isinstance(x.get("n"), int) and isinstance(x.get("x"), str):
                        posts.append(x)
        except OSError:
            pass
        ch = TZ["chats"][m["id"]] = {"posts": posts, "rev": len(posts), "erev": 0}
        return ch


def tausch_chat_clean(text):
    s = _TZ_CTRL.sub("", str(text or "").replace("\r\n", "\n").replace("\r", "\n"))
    s = re.sub(r"\n{4,}", "\n\n\n", s).strip()
    return s


def tausch_chat_get(who, fid, after=0, rev=-1, lang=None):
    m = tausch_file(fid)
    if m is None or (who is not None and not tausch_can_see(m, who)) or (who is None and m["area"] != "all"):
        return False, tr("unknown file", lang), {}
    if tausch_ext(m["name"]) != "chat":
        return False, tr("This is not a chat.", lang), {}
    ch = _tz_chat(m)
    now = time.time()
    with TZ["lock"]:
        full = rev < ch["erev"] or rev < 0 or rev > ch["rev"]
        sel = ch["posts"] if full else [x for x in ch["posts"] if x["n"] > after]
        pub = []
        for x in sel[-800:]:
            d = {"n": x["n"], "t": x["t"], "by": x.get("by", ""), "x": "" if x.get("d") else x["x"], "ed": x.get("e", 0), "del": bool(x.get("d"))}
            if who is not None:
                mine = x.get("k") == who["key"]
                d.update(mine=mine, ce=mine and not x.get("d") and now - x["t"] < TZ_EDIT_WIN and tausch_can_edit(m, who),
                         cd=not x.get("d") and ((mine and now - x["t"] < TZ_EDIT_WIN) or who["admin"]))
            pub.append(d)
        out = {"id": fid, "name": os.path.splitext(m["name"])[0], "rev": ch["rev"], "full": full, "posts": pub,
               "n": len(ch["posts"]), "size": m["size"], "max": TZ_CHAT_MAX, "post_max": TZ_POST_MAX}
    if who is not None:
        out["write"] = tausch_can_edit(m, who)
    return True, "", out


def tausch_chat_wait(fid, rev, ip, timeout=TZ_WAIT_S):
    """the long poll of an open chat: waits until something changes (at most «timeout» s); False = no place (poll later)"""
    with TZ["lock"]:
        if TZ["waiting"] >= TZ_WAIT_MAX or TZ["waiters"].get(ip, 0) >= TZ_WAIT_IP:
            return False
        TZ["waiting"] += 1
        TZ["waiters"][ip] = TZ["waiters"].get(ip, 0) + 1
    try:
        end = time.time() + timeout
        with TZ_CHAT_COND:
            while True:
                ch = TZ["chats"].get(fid)
                if ch is None or ch["rev"] != rev:
                    return True
                left = end - time.time()
                if left <= 0:
                    return True
                TZ_CHAT_COND.wait(min(left, 5.0))
    finally:
        with TZ["lock"]:
            TZ["waiting"] = max(0, TZ["waiting"] - 1)
            TZ["waiters"][ip] = max(0, TZ["waiters"].get(ip, 1) - 1)
            if not TZ["waiters"][ip]:
                TZ["waiters"].pop(ip, None)


def _tz_chat_changed():
    with TZ_CHAT_COND:
        TZ_CHAT_COND.notify_all()


def _tz_chat_rewrite(m, ch):
    tmp = os.path.join(TZ["root"], "f", m["id"] + ".bin.tmp")
    data = "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in ch["posts"]).encode("utf-8")
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, os.path.join(TZ["root"], "f", m["id"] + ".bin"))
    m["size"] = len(data)


def tausch_chat_post(who, fid, text, lang=None):
    m = tausch_file(fid)
    if m is None or not tausch_can_see(m, who) or tausch_ext(m["name"]) != "chat":
        return False, tr("unknown file", lang), {}
    if not tausch_can_edit(m, who):
        return False, tr("You may not write in this chat.", lang), {}
    s = tausch_chat_clean(text)
    if not s:
        return False, tr("The message is empty.", lang), {}
    if len(s.encode("utf-8")) > TZ_POST_MAX:
        return False, trf("Too long: at most {n} per message.", lang, n=tausch_fmt(TZ_POST_MAX, lang)), {}
    if not tausch_rate(who["key"], "post", 30, per=60.0):
        return False, tr("Too many messages in a short time - wait a moment.", lang), {}
    ch = _tz_chat(m)
    with TZ["lock"]:
        n = (ch["posts"][-1]["n"] + 1) if ch["posts"] else 1
        x = {"n": n, "t": int(time.time()), "k": who["key"], "by": who["name"], "x": s}
        line = (json.dumps(x, ensure_ascii=False) + "\n").encode("utf-8")
        if m["size"] + len(line) > TZ_CHAT_MAX:
            return False, tr("This chat is full - start a new one.", lang), {}
        err = _tz_extra_room(len(line), m["owner"], lang)
        if err:
            return False, err, {}
        try:
            with open(os.path.join(TZ["root"], "f", fid + ".bin"), "ab") as f:
                f.write(line)
        except OSError as e:
            return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", {}
        ch["posts"].append(x)
        ch["rev"] += 1
        m["size"] += len(line)
        m["ed_t"] = x["t"]
        try:
            _tz_write_json(os.path.join(TZ["root"], "f", fid + ".json"), m)
        except OSError:
            pass
    _tz_chat_changed()
    tausch_chat_note(m, who)
    return True, "", {"n": n, "rev": ch["rev"]}


def tausch_chat_change(who, fid, n, text=None, lang=None):
    """text None = delete. Own posts within 5 minutes; files_admin may delete every post (not change it)."""
    m = tausch_file(fid)
    if m is None or not tausch_can_see(m, who) or tausch_ext(m["name"]) != "chat":
        return False, tr("unknown file", lang)
    ch = _tz_chat(m)
    with TZ["lock"]:
        x = next((p for p in ch["posts"] if p["n"] == n), None)
        if x is None or x.get("d"):
            return False, tr("unknown message", lang)
        mine = x.get("k") == who["key"] and time.time() - x["t"] < TZ_EDIT_WIN
        if text is None:
            if not (mine or who["admin"]):
                return False, tr("Only your own messages, and only within 5 minutes.", lang)
            x.update(d=True, x="", e=int(time.time()))
        else:
            if not mine or not tausch_can_edit(m, who):
                return False, tr("Only your own messages, and only within 5 minutes.", lang)
            s = tausch_chat_clean(text)
            if not s or len(s.encode("utf-8")) > TZ_POST_MAX:
                return False, trf("Too long: at most {n} per message.", lang, n=tausch_fmt(TZ_POST_MAX, lang)) if s else tr("The message is empty.", lang)
            x.update(x=s, e=int(time.time()))
        ch["rev"] += 1
        ch["erev"] = ch["rev"]
        try:
            _tz_chat_rewrite(m, ch)
            _tz_write_json(os.path.join(TZ["root"], "f", fid + ".json"), m)
        except OSError as e:
            return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})"
    _tz_chat_changed()
    if text is None:
        log_event("web", f"Digital backpack: {who['name']} deleted a message in «{m['name']}»")
    return True, ""


# ---- previews (thumbnails 320 px, preview 1280 px - always computed anew, never the original bytes) ------------------------------
def tausch_img_dims(path):
    """(width, height) from the head of a PNG / JPEG / GIF / BMP / WebP / TIFF, or None - checked before decoding (pixel bombs).
    3.68.1: the reading itself is img_head() in part 639zzf (shared with the upload of «Untersuchen» and the AI helper)."""
    try:
        with open(path, "rb") as f:
            r = img_head(f)
    except OSError:
        return None
    return (r[1], r[2]) if r else None


def _tz_jpg_write(img, path, side, q):
    hh, ww = img.shape[:2]
    s = min(1.0, float(side) / max(hh, ww, 1))
    if s < 1.0:
        img = cv2.resize(img, (max(1, int(ww * s)), max(1, int(hh * s))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    if not ok:
        return False
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(buf.tobytes())
    os.replace(tmp, path)
    return True


def tausch_thumb_make(root, m):
    """True = preview made, False = none possible (symbol instead)"""
    src = os.path.join(root, "f", m["id"] + ".bin")
    kind = tausch_type(m["name"])[1]
    img = None
    if kind == "image":
        dims = tausch_img_dims(src)
        if dims is None or not (0 < dims[0] <= IMG_SIDE_MAX and 0 < dims[1] <= IMG_SIDE_MAX and dims[0] * dims[1] <= IMG_MP_MAX):
            return False                                     # 3.68.1: head unreadable / pixel bomb / absurd picture: only the symbol, nothing decoded
        flag = cv2.IMREAD_COLOR
        if dims and dims[0] * dims[1] > 16_000_000 and tausch_ext(m["name"]) in ("jpg", "jpeg"):
            flag = cv2.IMREAD_REDUCED_COLOR_4
        try:
            img = cv2.imdecode(np.fromfile(src, dtype=np.uint8), flag)
        except (cv2.error, ValueError, MemoryError):
            img = None
        if img is None and tausch_ext(m["name"]) == "gif":
            kind = "video"                                   # an animated GIF: the first picture
    if kind == "video" and img is None:
        cap = cv2.VideoCapture(src)
        try:
            if cap.isOpened():
                n = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
                fps = cap.get(cv2.CAP_PROP_FPS) or 25
                if n > 2:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(fps), int(n // 2)))
                ok, img = cap.read()
                if not ok:
                    img = None
        finally:
            cap.release()
    if kind == "pdf" and img is None:
        exe = TZ["pdftoppm"] if TZ["pdftoppm"] is not None else (shutil.which("pdftoppm") or "")
        TZ["pdftoppm"] = exe
        if not exe or m["size"] > 50 * TZ_MB:
            return False
        tmpd = tempfile.mkdtemp(prefix="mw_tz_")
        try:
            r = subprocess.run([exe, "-f", "1", "-l", "1", "-scale-to", "1280", "-jpeg", "-singlefile", src, os.path.join(tmpd, "s")],
                               capture_output=True, timeout=25)
            pj = os.path.join(tmpd, "s.jpg")
            if r.returncode == 0 and os.path.isfile(pj):
                img = cv2.imread(pj, cv2.IMREAD_COLOR)
        except (OSError, subprocess.SubprocessError):
            img = None
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
    if img is None or img.size == 0:
        return False
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    ok1 = _tz_jpg_write(img, os.path.join(root, "t", m["id"] + ".jpg"), 320, 78)
    ok2 = _tz_jpg_write(img, os.path.join(root, "t", m["id"] + "_p.jpg"), 1280, 84)
    return bool(ok1 and ok2)


def tausch_thumb_queue(fid):
    with TZ["lock"]:
        if fid not in TZ["thumbq"]:
            TZ["thumbq"].append(fid)
        if TZ["thumb_run"]:
            return
        TZ["thumb_run"] = True
    threading.Thread(target=_tz_thumb_worker, daemon=True, name="tausch-thumbs").start()


def _tz_thumb_worker():
    try:
        while True:
            with TZ["lock"]:
                if not TZ["thumbq"]:
                    TZ["thumb_run"] = False
                    return
                fid = TZ["thumbq"].popleft()
                root = TZ["root"]
                m = (TZ["files"] or {}).get(fid)
            if m is None or not root:
                continue
            try:
                ok = tausch_thumb_make(root, m)
            except Exception as e:                              # a broken file must never stop the worker
                ok = False
                log_event("sys", f"Digital backpack: no preview for «{m['name']}»: {e.__class__.__name__}")
            with TZ["lock"]:
                if fid in (TZ["files"] or {}):
                    m["thumb"] = bool(ok)
                    try:
                        _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
                    except OSError:
                        pass
    except Exception:
        with TZ["lock"]:
            TZ["thumb_run"] = False


# ---- push: uploads to the administrator, chat posts to the people who wrote in that chat (bundled) -------------------------
# Uploads: only the administrator (the main channel and the browsers without a user), never the other users (Notifier.info
# would also reach every user with «Infos»). Chat posts: every participant who wrote in that chat, never the author; a user
# by his own browsers (web push) and his own ntfy topic, only inside his time window and only with «Infos» (041); the
# administrator by the main channel. «What is reported» = only persons / animals: no such push; quiet hours: held back.
# Content never goes out - only the name and the number («📁 Anna hat 3 Dateien hochgeladen», «💬 Anna hat 2× geschrieben in
# «Ferienplanung»»).
_TZ_TL = threading.local()


def tausch_push_note(who, n=1, now=None):
    """an upload of «who»: one more in the bundle for the administrator"""
    if who.get("is_admin") or not CFG.get("tausch_push", True):
        return
    _tz_bundle(("up", who["key"]), {"kind": "up", "name": who["name"], "target": "admin"}, n, now)


def tausch_chat_note(m, who, now=None):
    """a chat post of «who»: one more in the bundle of every other participant"""
    if not CFG.get("tausch_push", True):
        return
    ch = TZ["chats"].get(m["id"]) or {}
    names = {}
    for x in ch.get("posts") or []:
        if x.get("k") and x["k"] != who["key"]:
            names[x["k"]] = x.get("by") or x["k"]
    for k, nm in names.items():
        if m["area"] == "mine" and k != m["owner"] and k != "admin":
            continue                                        # a private chat: only its owner (and the administrator)
        _tz_bundle(("chat", k, m["id"]), {"kind": "chat", "target": k, "target_name": nm, "chat": os.path.splitext(m["name"])[0],
                                          "authors": {}}, 1, now, author=who["name"])


def _tz_bundle(key, base, n, now, author=None):
    now = time.time() if now is None else now
    with TZ["lock"]:
        e = TZ["push"].get(key)
        if e is None:
            e = TZ["push"][key] = dict(base, n=0, first=now)
        e["n"] += n
        e["last"] = now
        if author:
            e["authors"][author] = e["authors"].get(author, 0) + n
        if TZ["push_run"] or TZ.get("push_manual"):
            return
        TZ["push_run"] = True
    threading.Thread(target=_tz_push_worker, daemon=True, name="tausch-push").start()


def tausch_push_text(name, n, lang=None):
    return trf("{who} uploaded a file", lang, who=name) if n == 1 else trf("{who} uploaded {n} files", lang, who=name, n=n)


def tausch_chat_text(e, lang=None):
    au = list(e.get("authors") or {})
    who, n, chat = ", ".join(au[:3]) + (" …" if len(au) > 3 else ""), e["n"], e["chat"]
    if len(au) > 1:
        return trf("{who} have written {n}× in «{chat}»", lang, who=who, n=n, chat=chat)
    if n == 1:
        return trf("{who} wrote in «{chat}»", lang, who=who, chat=chat)
    return trf("{who} wrote {n}× in «{chat}»", lang, who=who, n=n, chat=chat)


def tausch_push_ok():
    """(may go out now, hold back): level «only persons / animals» = never, quiet hours = later"""
    try:
        if CFG.get("push_level") in ("persons", "animals"):
            return False, False
        if quiet_now():
            return False, True
    except NameError:
        pass
    return True, False


def tausch_push_tick(now=None, force=False):
    """sends the bundles that are due; returns the texts (for the tests)"""
    now = time.time() if now is None else now
    ok, hold = tausch_push_ok()
    due = []
    with TZ["lock"]:
        for k, e in list(TZ["push"].items()):
            if not ok and hold and now - e["first"] < 12 * 3600 and not force:
                continue                                    # quiet hours: keep collecting
            if force or now - e["last"] >= TZ_PUSH_QUIET or now - e["first"] >= TZ_PUSH_MAX or not ok:
                due.append(TZ["push"].pop(k))
    out = []
    for e in due:
        if not ok and not force:
            continue                                        # level: not reported
        txt = tausch_push_text(e["name"], e["n"]) if e["kind"] == "up" else tausch_chat_text(e)
        out.append(txt)
        tausch_push_deliver(e, txt)
    return out


def tausch_push_deliver(e, txt):
    title_key = "File exchange" if e["kind"] == "up" else "Chat"
    pub = (CFG.get("public_url") or "").strip().rstrip("/")
    try:
        link = (pub or page_address().rstrip("/")) + "/tausch"
    except Exception:
        link = ""
    if e["target"] == "admin":
        return tausch_push_send(txt, title_key, link)
    return tausch_push_user(e.get("target_name") or e["target"], txt, title_key, link)


def tausch_push_send(txt, title_key="File exchange", link=""):
    """the administrator only: main channel + the browsers without a user (payload «tz_admin», see the wrappers below)"""
    w = WATCH_REF.get("w")
    n = getattr(w, "notifier", None) if w is not None else None
    if n is None or not (n.configured() and CFG.get("notify_on")):
        return False
    p = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": txt, "info_title": "{name}: " + tr(title_key),
         "snapshot": None, "rain": False, "wind": "", "source": STATE.get("source_label", ""), "link": link, "tz_admin": True}
    threading.Thread(target=n._dispatch, args=(p, None, ""), daemon=True, name="tausch-push-admin").start()
    return True


def tausch_push_user(name, txt, title_key, link):
    """one user: his browsers (web push) and his own ntfy topic - only inside his time window and with «Infos» (041)"""
    u = user_get(name)
    if u is None or not users_push_wants(u["name"], "info"):
        return False
    title = ("💬 " if title_key == "Chat" else "📁 ") + ((CFG.get("device_name") or "").strip()[:20] or "MoveEye") + ": " + tr(title_key)
    subs = [x for x in webpush_subs() if str(x.get("user", "")).lower() == u["name"].lower()]
    if subs and webpush_supported() and CFG.get("webpush_on"):
        threading.Thread(target=_tz_webpush_to, args=(subs, title, txt, "/tausch"), daemon=True, name="tausch-push-wp").start()
    if u.get("ntfy"):
        threading.Thread(target=_users_ntfy_send, args=(u["name"], _users_ntfy_url(u["ntfy"]), title, txt, "info", link),
                         daemon=True, name="tausch-push-ntfy").start()
    return True


def _tz_webpush_to(subs, title, text, url):
    n = 0
    for sb in subs:
        try:
            code = webpush_send(sb, {"title": title[:120], "body": text[:400], "url": url, "tag": "mw-info", "urgent": False}, urgent=False)
            n += 200 <= code < 300
        except Exception:
            pass
    return n


def _tz_push_worker():
    try:
        while True:
            time.sleep(10)
            tausch_push_tick()
            with TZ["lock"]:
                if not TZ["push"]:
                    TZ["push_run"] = False
                    return
    except Exception:
        with TZ["lock"]:
            TZ["push_run"] = False


_tz_dispatch_base = Notifier._dispatch


def _tz_dispatch(self, p, jpg, fname):                   # + 639zzc: «tz_admin» = not to the other users
    if not (isinstance(p, dict) and p.get("tz_admin")):
        return _tz_dispatch_base(self, p, jpg, fname)
    _TZ_TL.admin_only = True
    try:
        return _tz_dispatch_base(self, p, jpg, fname)
    finally:
        _TZ_TL.admin_only = False


# wraps: Notifier._dispatch (after 639zy)
Notifier._dispatch = _tz_dispatch
_tz_webpush_base = Notifier._webpush


def _tz_webpush(self, p):                                 # + 639zzc: «tz_admin» = only the browsers without a user
    if not (isinstance(p, dict) and p.get("tz_admin")):
        return _tz_webpush_base(self, p)
    subs = [x for x in webpush_subs() if not x.get("user")]
    if subs and webpush_supported():
        _tz_webpush_to(subs, self._title(p), self._text(p), p.get("link") or "/tausch")


# wraps: Notifier._webpush
Notifier._webpush = _tz_webpush
_users_push_dispatch_tz_base = users_push_dispatch


def users_push_dispatch(title, text, cat, click=""):      # + 639zzc: nothing to the users for an administrator-only message
    if getattr(_TZ_TL, "admin_only", False):
        return 0
    return _users_push_dispatch_tz_base(title, text, cat, click)


PK_TITLES.setdefault("File exchange", ("📁", "File exchange", "info", False))
PK_TITLES.setdefault("Chat", ("💬", "Chat", "info", False))


# ---- web: the page, the list, uploads, downloads, previews, guests ------------------------------------------------------------
def _tz_send(path, mime, attach, name=None, cache="private, no-cache"):
    from flask import send_file
    r = send_file(path, mimetype=mime, as_attachment=attach, download_name=name, conditional=True, max_age=0)
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["Content-Security-Policy"] = "sandbox; default-src 'none'; img-src 'self'; media-src 'self'"
    r.headers["Cache-Control"] = cache
    r.headers["Referrer-Policy"] = "no-referrer"
    r.headers["X-Frame-Options"] = "SAMEORIGIN"
    return r


def _tz_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def tausch_guest_ok(token):
    return bool(CFG.get("tausch_on", True) and CFG.get("tausch_guest", True) and guest_ok(token))


def tausch_guest_list(folder=""):
    root = _tz_load()
    if root is None:
        return {"ok": True, "files": [], "folders": []}
    with TZ["lock"]:
        files = [m for m in TZ["files"].values() if m["area"] == "all" and not tausch_type(m["name"])[2]]
        folders = list(TZ["folders"])
    if folder and not any(x["name"] == folder for x in folders):
        return {"ok": False, "files": [], "folders": []}
    out = {"ok": True, "folder": folder, "files": [], "folders": []}
    if not folder:
        out["folders"] = [{"name": x["name"], "n": sum(1 for m in files if m.get("folder") == x["name"])} for x in folders]
    out["files"] = sorted(({"id": m["id"], "name": m["name"], "size": m["size"], "t": m.get("t", 0), "kind": tausch_type(m["name"])[1],
                            "ext": tausch_ext(m["name"])[:8], "thumb": m.get("thumb")} for m in files if m.get("folder", "") == folder),
                          key=lambda x: -x["t"])
    return out


_smalltv_routes_639zzc = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzc: /tausch, /api/tausch, downloads, previews, guests
    _smalltv_routes_639zzc(app, reply, body)
    from flask import Response, request, g

    def size_guard():                                    # before everything else: a too big piece is not even read
        if request.path == "/api/tausch/chunk" and request.method == "POST":
            n = request.content_length
            if n is None or n > TZ_CHUNK_MAX:
                return Response(json.dumps({"ok": False, "error": "piece too big"}), 413, mimetype="application/json",
                                headers={"Connection": "close"})
            sock = request.environ.get("werkzeug.socket")    # the data of a piece must keep coming: without a limit a stalled
            if sock is not None:                             # phone holds this request (and the bar at 0 %) for ever
                try:
                    sock.settimeout(TZ_BODY_IDLE)
                except (OSError, AttributeError, ValueError):
                    pass
        return None
    app.before_request_funcs.setdefault(None, []).insert(0, size_guard)

    from werkzeug.exceptions import ClientDisconnected

    def piece_lost():
        return Response(json.dumps({"ok": False, "error": tr("The piece did not arrive completely.", lang_())}), 408, mimetype="application/json",
                        headers={"Connection": "close", "Cache-Control": "no-store"})

    @app.errorhandler(ClientDisconnected)
    def tausch_body_lost(e):                             # the body stopped (also while an earlier check read it): a clear 408 for the page
        return piece_lost() if request.path == "/api/tausch/chunk" else e

    def lang_():
        return norm_lang(request.args.get("lang") or CFG.get("lang"))

    def nope(code=404, msg="not found"):
        return reply({"ok": False, "error": tr(msg, lang_())}, code)

    @app.route("/tausch")
    @app.route("/tausch/")
    def tausch_page():
        who = tausch_who(g)
        if "files_view" not in who["perms"]:
            return sx_err(403, "error")
        return Response(tausch_page_html(), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/tausch", methods=["GET", "POST"])
    def api_tausch():
        who = tausch_who(g)
        if request.method == "GET":
            L = lang_()
            if not who["perms"]:
                return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
            area = "mine" if request.args.get("area") == "mine" else "all"
            j = tausch_list(who, area, str(request.args.get("folder") or "")[:80], L)
            return reply(j)
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        a = d.get("action")
        if not who["perms"]:
            return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
        if a == "start":
            ok, err, res = tausch_up_start(who, d, L)
        elif a == "finish":
            ok, err, res = tausch_up_finish(who, str(d.get("id") or ""), L)
        elif a == "abort":
            ok, err = tausch_up_abort(who, str(d.get("id") or ""), L); res = {}
        elif a == "delete":
            ok, err = tausch_delete(who, str(d.get("id") or ""), L); res = {}
        elif a == "mkdir":
            ok, err = tausch_mkdir(who, d.get("name"), L); res = {}
        elif a == "rmdir":
            ok, err = tausch_rmdir(who, str(d.get("name") or ""), bool(d.get("force")), L); res = {}
        elif a in ("newtext", "newchat"):
            ok, err, res = tausch_create(who, d, "text" if a == "newtext" else "chat", L)
        elif a in ("save", "restore"):
            ok, err, res = tausch_text_save(who, str(d.get("id") or ""), d.get("text"), d.get("ver"), L,
                                            restore=_tz_int(d.get("v")) if a == "restore" else None)
            if res.get("conflict"):
                return reply(dict(res, ok=False, error=err), 409)
        elif a == "post":
            ok, err, res = tausch_chat_post(who, str(d.get("id") or ""), d.get("text"), L)
        elif a in ("chat_edit", "chat_del"):
            ok, err = tausch_chat_change(who, str(d.get("id") or ""), _tz_int(d.get("n")), d.get("text") if a == "chat_edit" else None, L); res = {}
        else:
            ok, err, res = False, tr("unknown action", L), {}
        return reply(dict(res, ok=ok, error=err or None), 200 if ok else 400)

    @app.route("/api/tausch/chunk", methods=["POST"])
    def api_tausch_chunk():
        who = tausch_who(g)
        L = lang_()
        try:
            off = int(request.args.get("off", "-1"))
        except ValueError:
            off = -1
        try:
            data = request.get_data(cache=False)
        except (ClientDisconnected, OSError):                # the data stopped coming (TZ_BODY_IDLE) or the phone hung up
            return piece_lost()
        if request.content_length is not None and len(data) != request.content_length:
            return piece_lost()
        ok, err, have, code = tausch_up_chunk(who, str(request.args.get("id") or ""), off, data, L)
        return reply({"ok": ok, "error": err or None, "have": have}, code)

    @app.route("/api/tausch/text")
    def api_tausch_text():
        who = tausch_who(g)
        ok, err, res = tausch_text_get(who, str(request.args.get("id") or ""), _tz_int(request.args.get("v")) or None, lang_())
        return reply(dict(res, ok=ok, error=err or None), 200 if ok else 404)

    def chat_reply(who, fid):
        rev, after = _tz_int(request.args.get("rev"), -1), _tz_int(request.args.get("after"))
        if request.args.get("wait") == "1" and rev >= 0 and tausch_file(fid) is not None:
            m = tausch_file(fid)
            if who is None or tausch_can_see(m, who):
                _tz_chat(m)
                if not tausch_chat_wait(fid, rev, request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr or "?"):
                    pass                                     # no place for waiting: answer at once, the page polls slower
        ok, err, res = tausch_chat_get(who, fid, after, rev, lang_())
        return reply(dict(res, ok=ok, error=err or None), 200 if ok else 404)

    @app.route("/api/tausch/chat")
    def api_tausch_chat():
        return chat_reply(tausch_who(g), str(request.args.get("id") or ""))

    def file_of(fid, who):
        if not TZ_ID.match(fid or "") or _tz_load() is None:
            return None
        with TZ["lock"]:
            m = TZ["files"].get(fid)
        return m if m is not None and tausch_can_see(m, who) else None

    @app.route("/tausch/dl/<fid>")
    def tausch_dl(fid):
        who = tausch_who(g)
        m = file_of(fid, who)
        if m is None:
            return nope()
        if not tausch_can_down(m, who):
            return nope(403, "You may not download files.")
        rg = request.headers.get("Range", "")
        if not rg or rg.startswith("bytes=0-"):
            if not tausch_rate(who["key"], "dl", 400):
                return nope(429, "Too many downloads in a short time - wait a few minutes.")
            log_event("web", f"Digital backpack: {who['name']} downloaded «{m['name']}»")
        mime, kind, risky = tausch_type(m["name"])
        return _tz_send(os.path.join(TZ["root"], "f", fid + ".bin"), "application/octet-stream" if risky else mime, True, m["name"])

    @app.route("/tausch/view/<fid>")
    def tausch_view(fid):                                    # only video / sound, in the browser (sandbox)
        who = tausch_who(g)
        m = file_of(fid, who)
        if m is None:
            return nope()
        mime, kind, risky = tausch_type(m["name"])
        if kind not in TZ_INLINE or risky:
            return nope(415, "no preview for this file")
        if not tausch_can_down(m, who):
            return nope(403, "You may not download files.")
        return _tz_send(os.path.join(TZ["root"], "f", fid + ".bin"), mime, False)

    def thumb(fid, big, who):
        m = file_of(fid, who) if who is not None else None
        if who is None:                                      # a guest: only «Für alle», never active content
            if TZ_ID.match(fid or "") and _tz_load() is not None:
                with TZ["lock"]:
                    m = TZ["files"].get(fid)
                if m is not None and (m["area"] != "all" or tausch_type(m["name"])[2]):
                    m = None
        if m is None or not m.get("thumb"):
            return nope()
        p = os.path.join(TZ["root"], "t", fid + ("_p.jpg" if big else ".jpg"))
        if not os.path.isfile(p):
            return nope()
        return _tz_send(p, "image/jpeg", False, cache="private, max-age=86400")

    @app.route("/tausch/thumb/<fid>.jpg")
    def tausch_thumb(fid):
        return thumb(fid, False, tausch_who(g))

    @app.route("/tausch/prev/<fid>.jpg")
    def tausch_prev(fid):
        return thumb(fid, True, tausch_who(g))

    # ---- guests: «Für alle», only previews, no names of the uploaders, no download, no upload ----
    def guest_gate(token):
        if not tausch_guest_ok(token):
            return False
        return tausch_rate("guest|" + (request.remote_addr or "?"), "g", 2000)

    @app.route("/g/<token>/tausch")
    def tausch_guest_page(token):
        if not tausch_guest_ok(token):
            return sx_err(404, "guest")
        return Response(tausch_guest_html(token), mimetype="text/html", headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})

    @app.route("/g/<token>/tausch/list")
    def tausch_guest_listing(token):
        if not guest_gate(token):
            return reply({"ok": False}, 404)
        return reply(tausch_guest_list(str(request.args.get("folder") or "")[:80]))

    @app.route("/g/<token>/tausch/text/<fid>")
    def tausch_guest_text(token, fid):
        if not guest_gate(token):
            return reply({"ok": False}, 404)
        ok, err, res = tausch_text_get(None, fid, None, lang_())
        return reply(dict(res, ok=ok), 200 if ok else 404)

    @app.route("/g/<token>/tausch/chat/<fid>")
    def tausch_guest_chat(token, fid):
        if not guest_gate(token):
            return reply({"ok": False}, 404)
        ok, err, res = tausch_chat_get(None, fid, 0, -1, lang_())
        return reply(dict(res, ok=ok), 200 if ok else 404)

    @app.route("/g/<token>/tausch/t/<fid>.jpg")
    def tausch_guest_thumb(token, fid):
        if not guest_gate(token):
            return Response("not found", 404)
        return thumb(fid, False, None)

    @app.route("/g/<token>/tausch/p/<fid>.jpg")
    def tausch_guest_prev(token, fid):
        if not guest_gate(token):
            return Response("not found", 404)
        return thumb(fid, True, None)


# ---- settings (web: Einstellungen → System → Datentausch, window: the same group) ---------------------------------------------------
_TZS = "File exchange"
TOGGLES.extend([
    (_TZS, "tausch_on", "File exchange on (Mehr → File exchange)"),
    (_TZS, "tausch_guest", "Guests see «For everyone» (pictures only, no download)"),
    (_TZS, "tausch_push", "Push to me when someone uploads files (bundled)"),
    (_TZS, "tausch_block_exec", "Refuse programs and scripts (.exe, .sh, .py, .js …)"),
])
SLIDERS.extend([
    (_TZS, "tausch_total_gb", "Space for the file exchange in total (GB)", 0.5, 500.0, 0.5),
    (_TZS, "tausch_file_mb", "At most per file (MB)", 5.0, 2000.0, 5.0),
    (_TZS, "tausch_user_gb", "At most per user (GB)", 0.1, 100.0, 0.1),
    (_TZS, "tausch_free_gb", "Always keep free on the storage (GB)", 0.5, 50.0, 0.5),
])
SECTIONS.append(_TZS)
SIMPLE_SECTIONS.add(_TZS)
SIMPLE_KEYS.add("tausch_on")
MENU_TITLES.setdefault(_TZS, "File exchange")
TK_SUB_ICONS[_TZS] = "▤"
for _g in TK_GROUPS:
    if _g[0] == "sys" and _TZS not in _g[2]:
        _g[2].insert(_g[2].index("Updates") if "Updates" in _g[2] else len(_g[2]), _TZS)
_tz_grp = '{sec: "Updates", ic: "⬆️"}'
if _tz_grp in WEB_PAGE and '{sec: "File exchange"' not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_tz_grp, '{sec: "File exchange", title: "File exchange", ic: "📁"}, ' + _tz_grp, 1)
_tz_perm_ui = '["settings", "⚙", "Settings"]];'
if _tz_perm_ui in WEB_PAGE:                                # 547: the four rights in the user editor («Own rights»: one by one)
    WEB_PAGE = WEB_PAGE.replace(_tz_perm_ui, '["settings", "⚙", "Settings"], ["files_view", "📁", "Files: see"], ["files_down", "⬇", "Files: download"],'
                                ' ["files_up", "⬆", "Files: upload"], ["files_admin", "🗂", "Files: manage all"]];', 1)
SET_HELP.update({
    "tausch_total_gb": ("All files of the file exchange together. Uploads stop with a clear message when it is full.", ""),
    "tausch_free_gb": ("MoveEye never fills the storage: below this free space no upload is accepted (recordings and the system need room).", ""),
})

# ---- «Mehr» (525) and the window (572): one entry ------------------------------------------------------------------------------
TZ_MORE_ROW = ('  <a class="mi" href="/tausch" id="m-tausch"><i>📁</i><span><b data-i18n="File exchange">Digital backpack</b><small data-i18n="Share photos, videos and documents - for everyone or only for you">'
               'Share photos, videos and documents - for everyone or only for you</small></span><span class="ar">›</span></a>\n')
_tz_anchor = '  <a class="mi" href="/tools">'
if 'href="/tausch"' not in MORE_PAGE and _tz_anchor in MORE_PAGE:
    MORE_PAGE = MORE_PAGE.replace(_tz_anchor, TZ_MORE_ROW + _tz_anchor, 1)
    MORE_PAGE = MORE_PAGE.replace("/*ALERTS*/", 'fetch("/api/tausch", {cache: "no-store"}).then(r => r.json()).then(j => { if (!j.ok || (!j.on && !(j.me || {}).is_admin)) '
                                  '{ const e = document.getElementById("m-tausch"); if (e) e.hidden = true; } }).catch(() => {});\n/*ALERTS*/', 1)
MORE_DE.update({"File exchange": "Digitaler Rucksack", "Share photos, videos and documents - for everyone or only for you":
                "Fotos, Videos und Dokumente teilen – für alle oder nur für dich"})

if GUI_OK:                                                # the window: «📁 Digitaler Rucksack» under «Mehr» (opens the browser)
    _tz_tk_more_base = App._tk_more_bar

    def _tz_tk_more_bar(self, parent):
        f = _tz_tk_more_base(self, parent)
        skip = getattr(self, "_fk_more_row", None)       # 639zj: the full-width hint stays below the buttons
        i = len([w for w in f.grid_slaves() if w is not skip])
        self._fbtn(f, "📁 " + tr("File exchange"), lambda: self._open_page("/tausch")).grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (572, after 639w / 639zj)
    App._tk_more_bar = _tz_tk_more_bar

# ---- guest page (520): a link to the shared files --------------------------------------------------------------------------------
# wraps: GUEST_KEYS
GUEST_KEYS = tuple(GUEST_KEYS) + ("Shared files",)
_tz_gfoot = '<div class="foot" id="ft"></div>'
if _tz_gfoot in GUEST_PAGE and "gfiles" not in GUEST_PAGE:
    GUEST_PAGE = GUEST_PAGE.replace(_tz_gfoot, _tz_gfoot + '<div class="foot"><a id="gfiles" href="__BASE__/tausch" hidden style="color:#8ab4f8;font-size:14px">📂 </a></div>', 1)
    GUEST_PAGE = GUEST_PAGE.replace("\nst();\n</script>", '\nst();\nfetch("__BASE__/tausch/list", {cache: "no-store"}).then(r => { if (r.ok) { const a = $("#gfiles"); '
                                    'a.textContent += g_("Shared files", "Geteilte Dateien", "Shared files"); a.hidden = false; } }).catch(() => {});\n</script>', 1)


# ---- the page /tausch ----------------------------------------------------------------------------------------------------------------
TAUSCH_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MoveEye - Digital backpack</title>
<style>
/*BASECSS*/
main{padding:14px 16px 60px;max-width:1100px;margin:0 auto}
.tz-h{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:2px 0 10px}.tz-h h2{margin:0;font-size:20px}
.tz-card{border:1px solid var(--line);border-radius:var(--r);background:var(--panel);padding:12px 14px;margin:0 0 12px;box-shadow:var(--shadow)}
.tz-q{display:flex;flex-direction:column;gap:6px}.tz-qt{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-size:13px}
.tz-bar{height:10px;border-radius:6px;background:var(--field);border:1px solid var(--line);overflow:hidden}.tz-bar i{display:block;height:100%;background:var(--acc);width:0;transition:width .4s}
.tz-bar.hi i{background:var(--yel)}.tz-bar.full i{background:var(--red)}
.tz-tabs{display:flex;gap:4px;background:var(--field);border:1px solid var(--line);border-radius:12px;padding:4px;margin:0 0 10px}
.tz-tabs button{flex:1;border:0;background:transparent;color:var(--mut);font:inherit;font-weight:600;padding:9px 10px;border-radius:9px;cursor:pointer;min-height:40px}
.tz-tabs button.on{background:var(--acc);color:#fff}
.tz-tool{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 10px}
.tz-tool input[type=search]{flex:1 1 180px;min-width:0;min-height:38px}
.tz-tool input[type=search],.tz-cf textarea{background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:8px 10px;font:inherit}.tz-tool select{flex:0 1 auto}
.tz-crumb{display:flex;align-items:center;gap:8px;margin:0 0 10px;font-size:14px;flex-wrap:wrap}.tz-crumb a{color:var(--acc2);text-decoration:none;cursor:pointer}
.tz-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.tz-it{position:relative;border:1px solid var(--line);border-radius:12px;background:var(--panel);overflow:hidden;display:flex;flex-direction:column;min-width:0}
.tz-it .th{aspect-ratio:4/3;background:var(--field);display:flex;align-items:center;justify-content:center;font-size:44px;cursor:pointer;overflow:hidden;position:relative}
.tz-it .th img{width:100%;height:100%;object-fit:cover;display:block}
.tz-it .th .play{position:absolute;inset:auto auto 6px 6px;font-size:13px;background:#000a;color:#fff;border-radius:8px;padding:1px 7px}
.tz-it .nm{padding:7px 9px 0;font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tz-it .mt{padding:0 9px 6px;color:var(--mut);font-size:11.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tz-it .ac{display:flex;gap:6px;padding:0 9px 9px;margin-top:auto}.tz-it .ac a,.tz-it .ac button{flex:1;min-height:34px;padding:4px 6px;font-size:13px;text-align:center;text-decoration:none}
.tz-dir .th{font-size:50px}.tz-dir{cursor:pointer}
.tz-list .tz-grid{grid-template-columns:1fr;gap:6px}
.tz-list .tz-it{flex-direction:row;align-items:center}.tz-list .tz-it .th{width:64px;height:52px;aspect-ratio:auto;font-size:26px;flex:none}
.tz-list .tz-it .tx{flex:1;min-width:0}.tz-list .tz-it .nm{padding:4px 10px 0}.tz-list .tz-it .mt{padding:0 10px 4px}
.tz-list .tz-it .ac{margin:0;padding:0 8px;flex:none}.tz-list .tz-it .ac a,.tz-list .tz-it .ac button{flex:none;min-width:40px}
.tz-up{display:flex;flex-direction:column;gap:6px;margin:0 0 10px}.tz-up:empty{display:none}
.tz-job{border:1px solid var(--line);border-radius:10px;background:var(--panel2);padding:8px 10px;font-size:13px}
.tz-job .r{display:flex;gap:8px;align-items:center}.tz-job .r b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tz-job .tz-bar{margin-top:6px;height:8px}.tz-job.err{border-color:var(--red)}.tz-job.ok{border-color:var(--grn)}
.tz-job .msg{color:var(--mut);font-size:12px;margin-top:4px}.tz-job.err .msg{color:var(--red)}
.tz-job .dg{font:11px/1.35 ui-monospace,Menlo,Consolas,monospace;color:var(--mut);margin-top:4px;overflow-wrap:anywhere;-webkit-user-select:all;user-select:all}.tz-job .again{margin-top:6px;min-height:36px;padding:4px 12px}
.tz-drop{position:fixed;inset:0;z-index:80;background:rgba(10,14,20,.78);display:none;align-items:center;justify-content:center;pointer-events:none}
.tz-drop.on{display:flex}.tz-drop div{border:3px dashed var(--acc);border-radius:20px;padding:40px 30px;font-size:20px;font-weight:700;color:#fff;text-align:center}
.tz-empty{color:var(--mut);text-align:center;padding:30px 10px}
.tz-msg{border:1px solid var(--yel);color:var(--yel);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:13px}.tz-msg.bad{border-color:var(--red);color:var(--red)}
.tz-lb{position:fixed;inset:0;z-index:120;background:rgba(0,0,0,.9);display:flex;flex-direction:column}
.tz-lb .bar{display:flex;gap:8px;align-items:center;padding:10px 12px;padding-top:max(10px,env(safe-area-inset-top));color:#fff}
.tz-lb .bar b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tz-lb .bd{flex:1;display:flex;align-items:center;justify-content:center;min-height:0;padding:8px}
.tz-lb img,.tz-lb video{max-width:100%;max-height:100%;object-fit:contain;border-radius:8px}.tz-lb audio{width:min(520px,94vw)}
.tz-lb .ic{font-size:90px}
.mut{color:var(--mut)}
.tz-ed{background:var(--bg)}.tz-ed .bar,.tz-chat .bar{color:var(--txt);border-bottom:1px solid var(--line);flex-wrap:wrap}
.tz-ed .bar button,.tz-ed .bar a{min-height:36px;padding:4px 10px}
.tz-edb{align-items:stretch;justify-content:stretch;padding:0;flex-direction:column}
.tz-ta{flex:1;width:100%;min-height:0;resize:none;border:0;border-radius:0;background:var(--field);color:var(--txt);padding:12px 14px;font:15px/1.5 system-ui,-apple-system,sans-serif;outline:none}
.tz-ta.mono{font:14px/1.5 ui-monospace,Menlo,Consolas,monospace}
.tz-md{flex:1;overflow:auto;padding:12px 16px;line-height:1.55;overflow-wrap:anywhere}.tz-md pre{background:var(--field);padding:10px;border-radius:8px;overflow:auto}
.tz-md code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.92em}.tz-md blockquote{border-left:3px solid var(--line);margin:6px 0;padding:2px 10px;color:var(--mut)}
.tz-md a{color:var(--acc2)}.tz-md h2,.tz-md h3,.tz-md h4,.tz-md h5{margin:12px 0 6px}
.tz-edf{display:flex;gap:8px;align-items:center;padding:8px 12px;padding-bottom:max(8px,env(safe-area-inset-bottom));border-top:1px solid var(--line);flex-wrap:wrap}
.tz-edf .st{flex:1;min-width:0;font-size:12.5px;color:var(--mut)}
.tz-pan{position:absolute;left:0;right:0;bottom:0;max-height:70%;overflow:auto;background:var(--panel);border-top:1px solid var(--line);padding:12px 14px;z-index:3;box-shadow:0 -8px 24px #0006}
.tz-pan h3{margin:0 0 8px;font-size:15px}.tz-pan .row{display:flex;gap:8px;align-items:center;padding:6px 0;border-bottom:1px solid var(--line);flex-wrap:wrap}
.tz-pan .row span{flex:1;min-width:0;font-size:13px}.tz-pan .btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.tz-diff{font:12.5px/1.45 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;max-height:40vh;overflow:auto;border:1px solid var(--line);border-radius:8px;padding:6px}
.tz-diff .a{background:rgba(255,77,77,.15)}.tz-diff .b{background:rgba(63,207,107,.15)}
.tz-chat{background:var(--bg)}.tz-cl{flex:1;overflow:auto;padding:10px 12px;display:flex;flex-direction:column;gap:8px;-webkit-overflow-scrolling:touch}
.tz-bub{max-width:82%;align-self:flex-start;background:var(--panel);border:1px solid var(--line);border-radius:14px 14px 14px 4px;padding:6px 10px}
.tz-bub.me{align-self:flex-end;background:var(--acc);color:#fff;border-color:var(--acc);border-radius:14px 14px 4px 14px}
.tz-bub .hd{font-size:11.5px;opacity:.75;display:flex;gap:6px;align-items:center}.tz-bub .hd button{background:none;border:0;color:inherit;padding:0 2px;min-height:0;font-size:13px;cursor:pointer}
.tz-bub .tx{white-space:pre-wrap;overflow-wrap:anywhere;font-size:15px}.tz-bub.del .tx{font-style:italic;opacity:.6}
.tz-cf{display:flex;gap:8px;align-items:flex-end;padding:8px 10px;padding-bottom:max(8px,env(safe-area-inset-bottom));border-top:1px solid var(--line);background:var(--panel)}
.tz-cf textarea{flex:1;min-height:42px;max-height:30vh;resize:none;border-radius:12px;padding:9px 12px}.tz-cf button{min-height:42px;min-width:48px}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main id="tz">
  <div class="tz-h"><h2>📁 <span data-i18n="File exchange">Digital backpack</span></h2><span class="mut" id="tz-store"></span></div>
  <div class="tz-card tz-q" id="tz-quota"><div class="tz-qt"><span id="tz-qt1">…</span><span class="mut" id="tz-qt2"></span></div><div class="tz-bar" id="tz-qbar"><i></i></div>
    <div class="tz-qt mut" id="tz-qt3" hidden></div></div>
  <div class="tz-msg" id="tz-msg" hidden></div>
  <div class="tz-tabs" role="tablist"><button type="button" id="tz-t-all" class="on" data-a="all">📂 <span data-i18n="For everyone">For everyone</span></button>
    <button type="button" id="tz-t-mine" data-a="mine">👤 <span data-i18n="My files">My files</span></button></div>
  <div class="tz-crumb" id="tz-crumb" hidden></div>
  <div class="tz-tool">
    <button type="button" id="tz-upb">⬆ <span data-i18n="Upload">Upload</span></button>
    <button type="button" class="sec" id="tz-mkd">📁+ <span data-i18n="New folder">New folder</span></button>
    <button type="button" class="sec" id="tz-mkt">📝 <span data-i18n="New text">New text</span></button>
    <button type="button" class="sec" id="tz-mkc">💬 <span data-i18n="New chat">New chat</span></button>
    <input type="file" id="tz-file" multiple hidden>
    <input type="search" id="tz-q" data-i18n-ph="Search" placeholder="Search" autocomplete="off">
    <select id="tz-kind"><option value="" data-i18n="All types">All types</option><option value="image" data-i18n="Pictures">Pictures</option>
      <option value="video" data-i18n="Videos">Videos</option><option value="audio" data-i18n="Sound">Sound</option><option value="doc" data-i18n="Documents">Documents</option><option value="chat" data-i18n="Chats">Chats</option>
      <option value="other" data-i18n="Other">Other</option></select>
    <select id="tz-sort"><option value="new" data-i18n="Newest first">Newest first</option><option value="old" data-i18n="Oldest first">Oldest first</option>
      <option value="name" data-i18n="Name">Name</option><option value="size" data-i18n="Size">Size</option><option value="by" data-i18n="Uploaded by">Uploaded by</option></select>
    <button type="button" class="sec" id="tz-view" title="">▦</button>
  </div>
  <div class="mut" id="tz-hint" style="font-size:12px;margin:-4px 0 10px"></div>
  <div class="tz-up" id="tz-up"></div>
  <div id="tz-body"><div class="tz-grid" id="tz-grid"></div><div class="tz-empty" id="tz-empty" hidden></div></div>
</main>
<div class="tz-drop" id="tz-drop"><div>⬆<br><span data-i18n="Drop the files here">Drop the files here</span></div></div>
<script>
/*COMMON*/
Object.assign(I18N.de, /*TZDE*/{});
/*TZMD*/
(function () {
  const S = {area: "all", folder: "", j: null, view: "grid", jobs: [], busy: false, poll: 0};
  try { S.view = localStorage.getItem("tausch-view") || "grid"; } catch (e) {}
  const KIC = {image: "🖼", video: "🎬", audio: "🎵", pdf: "📕", doc: "📄", text: "📝", chat: "💬", archive: "🗜", risky: "⚠️", other: "📦"};
  const num = (x, d) => { let s = x.toFixed(d); if (s.endsWith(".0")) s = s.slice(0, -2); return LANG === "en" ? s : s.replace(".", ","); };
  const fmt = n => n >= 1073741824 ? num(n / 1073741824, 1) + " GB" : n >= 1048576 ? num(n / 1048576, 0) + " MB" : n > 0 ? num(Math.max(1, n / 1024), 0) + " KB" : "0 KB";
  const when = s => { const d = new Date(s * 1000); return d.toLocaleDateString() + " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2); };
  const has = p => S.j && (S.j.perms || []).includes(p);
  const msg = (txt, bad) => { const m = $("#tz-msg"); m.hidden = !txt; m.textContent = txt || ""; m.classList.toggle("bad", !!bad); };
  async function load() {
    clearTimeout(S.poll);
    let j = null;
    try { j = await (await fetch("/api/tausch?area=" + S.area + "&folder=" + encodeURIComponent(S.folder) + "&lang=" + LANG, {cache: "no-store"})).json(); } catch (e) {}
    if (!j) { msg("⚠ " + t("No connection to MoveEye."), true); S.poll = setTimeout(load, 8000); return; }
    if (!j.ok && S.folder) { S.folder = ""; return load(); }
    S.j = j; paint();
    if ((j.files || []).some(f => f.thumb === null)) S.poll = setTimeout(load, 3000);
  }
  function paint() {
    const j = S.j, q = j.quota || {};
    const st = j.store || {};
    $("#tz-store").textContent = st.problem === "missing" ? "" : "💾 " + t({usb: "USB stick", ssd: "SSD", sd: "Memory card", disk: "Drive"}[st.kind] || "Drive");
    const pct = q.total ? Math.min(100, 100 * q.used / q.total) : 0;
    $("#tz-qbar i").style.width = pct.toFixed(1) + "%"; $("#tz-qbar").classList.toggle("hi", pct > 80); $("#tz-qbar").classList.toggle("full", pct > 97);
    $("#tz-qt1").textContent = t("{a} of {b} used").replace("{a}", fmt(q.used || 0)).replace("{b}", fmt(q.total || 0));
    $("#tz-qt2").textContent = t("at most {n} per file").replace("{n}", fmt(q.file_max || 0)) + (q.free !== undefined ? " · " + t("{n} free on the storage").replace("{n}", fmt(q.free || 0)) : "");
    const q3 = $("#tz-qt3"); q3.hidden = !q.user_max; if (q.user_max) q3.textContent = t("Your files: {a} of {b}").replace("{a}", fmt(q.user_used || 0)).replace("{b}", fmt(q.user_max));
    if (!j.on) msg("⏸ " + t("The file exchange is switched off.") + (j.me && j.me.is_admin ? " " + t("Switch it on under Settings → System → File exchange.") : ""), false);
    else if (st.problem === "missing") msg("⚠ " + t("The storage (USB stick / SSD) is not there - plug it in again."), true);
    else if (st.problem === "ro") msg("⚠ " + t("The memory card is write-protected (overlay) - files would be lost at the next restart. Use a USB stick."), true);
    else if (q.free !== undefined && q.free < q.min_free) msg("⚠ " + t("Not enough free space on the storage: MoveEye always keeps {n} free (for recordings and the system).").replace("{n}", fmt(q.min_free)), true);
    else if (!S.jobs.some(x => x.err)) msg("");
    $("#tz-t-all").classList.toggle("on", S.area === "all"); $("#tz-t-mine").classList.toggle("on", S.area === "mine");
    const canUp = has("files_up") && j.on && !st.problem;
    $("#tz-upb").hidden = !canUp; $("#tz-mkd").hidden = !(canUp && S.area === "all" && !S.folder); $("#tz-mkt").hidden = $("#tz-mkc").hidden = !canUp;
    $("#tz-hint").textContent = S.area === "mine" ? (j.me && j.me.admin ? "🔒 " + t("Only you see these files. As administrator you also see the private files of the others.") : "🔒 " + t("Only you (and the administrator) see these files."))
      : (canUp ? t("Everybody with access to MoveEye sees these files. Upload with the button or drag files onto the page.") : t("Everybody with access to MoveEye sees these files."));
    const cr = $("#tz-crumb"); cr.hidden = !S.folder; cr.textContent = "";
    if (S.folder) { const a = el("a", "", "📂 " + t("For everyone")); a.onclick = () => { S.folder = ""; load(); }; cr.append(a, el("span", "mut", "›"), el("b", "", S.folder)); }
    $("#tz-body").classList.toggle("tz-list", S.view === "list"); $("#tz-view").textContent = S.view === "list" ? "▦" : "☰";
    $("#tz-view").title = S.view === "list" ? t("Grid") : t("List");
    const g = $("#tz-grid"); g.textContent = "";
    const qq = ($("#tz-q").value || "").trim().toLowerCase(), kd = $("#tz-kind").value, so = $("#tz-sort").value;
    let fs = (j.files || []).filter(f => (!qq || f.name.toLowerCase().includes(qq) || (f.by || "").toLowerCase().includes(qq))
      && (!kd || (kd === "doc" ? ["doc", "pdf", "text"].includes(f.kind) : kd === "other" ? ["other", "archive", "risky"].includes(f.kind) : f.kind === kd)));
    const cmp = {new: (a, b) => b.t - a.t, old: (a, b) => a.t - b.t, name: (a, b) => a.name.localeCompare(b.name), size: (a, b) => b.size - a.size,
      by: (a, b) => (a.by || "").localeCompare(b.by || "") || b.t - a.t}[so] || ((a, b) => b.t - a.t);
    fs.sort(cmp);
    (qq || kd ? [] : (j.folders || [])).forEach(d => {
      const it = el("div", "tz-it tz-dir"), th = el("div", "th", "📁"), tx = el("div", "tx");
      tx.append(el("div", "nm", d.name), el("div", "mt", d.n + " " + t(d.n === 1 ? "file" : "files") + (d.n ? " · " + fmt(d.size) : "") + (d.by ? " · " + d.by : "")));
      it.append(th, tx); it.onclick = () => { S.folder = d.name; load(); };
      if (d.rm) { const ac = el("div", "ac"), b = el("button", "sec", "🗑"); b.type = "button"; b.title = t("Delete");
        b.onclick = async ev => { ev.stopPropagation(); if (!confirm((d.n ? t("Delete the folder with all its files?") : t("Delete the folder?")) + "\n" + d.name)) return;
          const r = await post("/api/tausch", {action: "rmdir", name: d.name, force: !!d.n, lang: LANG}); if (!r.ok) msg("⚠ " + (r.error || "error"), true); load(); };
        ac.appendChild(b); it.appendChild(ac); }
      g.appendChild(it);
    });
    fs.forEach(f => g.appendChild(card(f)));
    const em = $("#tz-empty"); em.hidden = g.children.length > 0;
    em.textContent = (qq || kd) ? t("Nothing found.") : S.area === "mine" ? t("No private files yet.") : t("No files yet.") + (canUp ? " " + t("Upload the first one with «Upload».") : "");
    applyI18n();
  }
  function card(f) {
    const it = el("div", "tz-it"), th = el("div", "th"), tx = el("div", "tx");
    if (f.thumb) { const im = el("img"); im.loading = "lazy"; im.alt = ""; im.src = "/tausch/thumb/" + f.id + ".jpg"; im.onerror = () => { im.remove(); th.textContent = KIC[f.kind] || "📦"; }; th.appendChild(im); }
    else th.textContent = f.thumb === null ? "⏳" : (KIC[f.kind] || "📦");
    if (f.kind === "video" && f.thumb) th.appendChild(el("span", "play", "▶"));
    th.onclick = () => f.kind === "text" ? openText(f) : f.kind === "chat" ? openChat(f) : preview(f);
    tx.append(el("div", "nm", f.name), el("div", "mt", (f.by ? (f.mine ? t("you") : f.by) + " · " : "") + when(f.t) + " · " + fmt(f.size)));
    tx.firstChild.title = f.name;
    const ac = el("div", "ac");
    if (f.dl) { const a = el("a", "btn sec", "⬇"); a.href = "/tausch/dl/" + f.id; a.title = t("Download"); a.setAttribute("download", ""); ac.appendChild(a); }
    if (f.rm) { const b = el("button", "sec", "🗑"); b.type = "button"; b.title = t("Delete");
      b.onclick = async () => { if (!confirm(t("Delete this file? It cannot be undone.") + "\n" + f.name)) return;
        const r = await post("/api/tausch", {action: "delete", id: f.id, lang: LANG}); if (!r.ok) msg("⚠ " + (r.error || "error"), true); else toast("🗑 " + f.name); load(); };
      ac.appendChild(b); }
    it.append(th, tx); if (ac.children.length) it.appendChild(ac);
    return it;
  }
  function preview(f) {
    const ov = el("div", "tz-lb"), bar = el("div", "bar"), bd = el("div", "bd"), x = el("button", "sec", "✕");
    x.type = "button"; x.onclick = () => ov.remove(); bar.appendChild(el("b", "", f.name));
    if (f.dl) { const a = el("a", "btn", "⬇ " + t("Download")); a.href = "/tausch/dl/" + f.id; a.setAttribute("download", ""); bar.appendChild(a); }
    bar.appendChild(x);
    if (f.inline && f.dl) { const v = el(f.kind === "audio" ? "audio" : "video"); v.controls = true; v.playsInline = true; v.preload = "metadata"; v.src = "/tausch/view/" + f.id;
      if (f.thumb && f.kind === "video") v.poster = "/tausch/prev/" + f.id + ".jpg"; bd.appendChild(v); }
    else if (f.thumb) { const im = el("img"); im.alt = f.name; im.src = "/tausch/prev/" + f.id + ".jpg"; bd.appendChild(im); }
    else { const c = el("div", "", ""); c.style.textAlign = "center"; c.append(el("div", "ic", KIC[f.kind] || "📦"), el("div", "mut", f.risky ? t("No preview for this kind of file (for safety only as download).") : t("No preview for this file."))); bd.appendChild(c); }
    ov.append(bar, bd); ov.addEventListener("click", e => { if (e.target === ov || e.target === bd) ov.remove(); });
    document.body.appendChild(ov);
  }
  // ---- upload: one file after the other, in pieces; the same file again continues where it stopped ----
  // 639zzc (iPhone, Besitzer 08.11.2026: a 5 MB photo stayed at 0 % for ever): every piece is first read into memory (a
  // photo from the library can be an iCloud / converted item that stalls as a streamed Blob body), sent with a watchdog
  // (no progress and no answer for UP.idle -> abort -> retry), the first piece is small (the bar moves at once, a problem
  // shows early), after repeated failures the pieces get smaller, and after the last try there is an honest message with
  // «Nochmal versuchen» (continues where it stopped) and one line of diagnostics for a screenshot.
  const UP = Object.assign({first: 262144, small: 524288, tiny: 131072, idle: 45000, read: 30000, tries: 6, wait: 1500, post: 30000}, window.TZ_UP_TEST || {});
  function addFiles(list) {
    if (!has("files_up")) return;
    [...list].forEach(file => S.jobs.push({file, area: S.area, folder: S.area === "all" ? S.folder : "", have: 0, part: 0, done: false, err: "", cancel: false, node: null}));
    paintJobs(); run();
  }
  function paintJobs() {
    const box = $("#tz-up");
    S.jobs.forEach(jb => {
      if (!jb.node) { jb.node = el("div", "tz-job"); const r = el("div", "r"), x = el("button", "sec", "✕"); x.type = "button"; x.title = t("Cancel");
        x.onclick = () => { if (jb.done || jb.err) { jb.node.remove(); S.jobs = S.jobs.filter(z => z !== jb); } else { jb.cancel = true; if (jb.xhr) try { jb.xhr.abort(); } catch (e) {} } };
        r.append(el("b", "", "⬆ " + jb.file.name), el("span", "mut pc", ""), x); jb.node.append(r, el("div", "tz-bar"), el("div", "msg", ""));
        const again = el("button", "sec again", "↻ " + t("Try once more")); again.type = "button"; again.hidden = true;
        again.onclick = () => { if (!jb.err) return; jb.err = ""; jb.retry = false; jb.cancel = false; jb.state = ""; paintJobs(); run(); };
        jb.node.append(el("div", "dg", ""), again);
        jb.node.querySelector(".tz-bar").appendChild(el("i")); box.appendChild(jb.node); }
      const got = Math.min(jb.file.size, jb.have + (jb.part || 0));
      const p = jb.file.size ? Math.floor(100 * got / jb.file.size) : (jb.done ? 100 : 0);
      jb.node.querySelector(".tz-bar i").style.width = p + "%"; jb.node.querySelector(".pc").textContent = jb.done ? "✓" : jb.err ? "⚠" : p + " %";
      jb.node.classList.toggle("ok", jb.done); jb.node.classList.toggle("err", !!jb.err);
      jb.node.querySelector(".msg").textContent = jb.err || (jb.done ? t("Done") : (jb.state ? jb.state + " · " : "") + fmt(got) + " / " + fmt(jb.file.size));
      const dg = jb.node.querySelector(".dg"); dg.hidden = !(jb.err && jb.diag); dg.textContent = jb.err && jb.diag ? jb.diag : "";
      jb.node.querySelector(".again").hidden = !(jb.err && jb.retry);
    });
  }
  async function run() {
    if (S.busy) return; S.busy = true;
    try {
      for (;;) {
        const jb = S.jobs.find(x => !x.done && !x.err && !x.cancel); if (!jb) break;
        try { await upOne(jb); } catch (e) { jb.err = t("error") + ": " + String((e && e.message) || e).slice(0, 80); jb.retry = true; }
        jb.xhr = null; paintJobs();
        if (jb.done) setTimeout(() => { if (jb.node && jb.done) { jb.node.remove(); S.jobs = S.jobs.filter(z => z !== jb); } }, 6000);
      }
    } finally { S.busy = false; load(); }
  }
  // a JSON request that cannot wait for ever (start / finish / abort)
  async function postT(body, ms) {
    const ac = window.AbortController ? new AbortController() : null, tm = setTimeout(() => { if (ac) ac.abort(); }, ms || UP.post);
    try { const r = await fetch("/api/tausch", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body), signal: ac ? ac.signal : undefined});
      return await r.json(); }
    catch (e) { return {ok: false, error: "", lost: true}; }
    finally { clearTimeout(tm); }
  }
  // one piece of the file into memory (with a limit: a photo that is not on the phone can take for ever)
  function readPiece(f, a, b) {
    return new Promise((ok, bad) => {
      let fin = false; const end = (fn, v) => { if (fin) return; fin = true; clearTimeout(tm); fn(v); };
      const tm = setTimeout(() => end(bad, new Error("read timeout " + Math.round(UP.read / 1000) + " s")), UP.read);
      try {
        const bl = f.slice(a, b);
        if (bl.arrayBuffer) bl.arrayBuffer().then(v => end(ok, v), e => end(bad, e || new Error("read")));
        else { const fr = new FileReader(); fr.onload = () => end(ok, fr.result); fr.onerror = () => end(bad, fr.error || new Error("read")); fr.readAsArrayBuffer(bl); }
      } catch (e) { end(bad, e); }
    });
  }
  // send one piece; rejects with {kind: "timeout" | "net" | "abort", sent} - «timeout» = no progress and no answer for UP.idle
  function sendPiece(jb, off, buf) {
    return new Promise((ok, bad) => {
      const x = new XMLHttpRequest(); let last = Date.now(), sent = 0, fin = false;
      const end = (fn, v) => { if (fin) return; fin = true; clearInterval(iv); if (jb.xhr === x) jb.xhr = null; fn(v); };
      const iv = setInterval(() => { if (Date.now() - last > UP.idle) { end(bad, {kind: "timeout", sent}); try { x.abort(); } catch (e) {} } }, 250);
      x.open("POST", "/api/tausch/chunk?id=" + jb.id + "&off=" + off + "&lang=" + LANG);
      x.setRequestHeader("Content-Type", "application/octet-stream");
      if (x.upload) x.upload.onprogress = e => { last = Date.now(); sent = e.loaded; jb.part = Math.min(e.loaded, buf.byteLength); paintJobs(); };
      x.onload = () => { let k; try { k = JSON.parse(x.responseText); } catch (e) { k = {ok: false}; } end(ok, {status: x.status, k: k || {ok: false}}); };
      x.onerror = () => end(bad, {kind: "net", sent}); x.onabort = () => end(bad, {kind: "abort", sent});
      jb.xhr = x; x.send(buf);
    });
  }
  async function upOne(jb) {
    const f = jb.file, D = {n: 0, of: 0, off: 0, len: 0, sent: 0, ms: 0, tries: 0, http: "-", last: ""};
    jb.err = ""; jb.retry = false; jb.diag = ""; jb.part = 0;
    const fail = (msg, retry) => { jb.err = msg; jb.retry = !!retry; jb.part = 0;                 // one line for a screenshot - only after a failure
      jb.diag = "Diagnose: Stück " + D.n + "/" + D.of + " · ab " + D.off + " · " + D.len + " B · gesendet " + D.sent + " B · " + (D.ms / 1000).toFixed(1) + " s · Versuch " + D.tries
        + " · HTTP " + D.http + " · " + (D.last || "-") + " · Datei " + f.size + " B " + (f.type || "?") + " · " + location.protocol.replace(":", "") + (navigator.onLine === false ? " offline" : ""); };
    const startBody = {action: "start", name: f.name, size: f.size, lastmod: f.lastModified || 0, area: jb.area, folder: jb.folder, lang: LANG};
    const r = await postT(startBody);
    if (!r.ok) { D.last = r.lost ? "start: no answer" : "start: refused"; fail(r.lost ? t("No connection to MoveEye.") : (r.error || t("error")), r.lost); return; }
    jb.id = r.id; jb.have = r.have || 0; const big = r.chunk || 2097152; let cs = Math.min(big, jb.cs || big), n = 0, stuck = 0;
    if (r.resumed) jb.state = t("continues where it stopped …");
    const abort = async () => { await postT({action: "abort", id: jb.id, lang: LANG}); jb.err = t("Cancelled"); jb.retry = false; jb.diag = ""; jb.part = 0; };
    while (jb.have < f.size) {
      if (jb.cancel) { await abort(); return; }
      let res = null, fails = 0;
      while (fails < UP.tries && !res && !jb.cancel) {
        const len = Math.min(n === 0 ? Math.min(UP.first, cs) : cs, f.size - jb.have), t0 = Date.now();    // the first piece is small: the bar moves at once
        D.n = n + 1; D.of = n + 1 + Math.ceil((f.size - jb.have - len) / cs); D.off = jb.have; D.len = len; D.tries = fails + 1; D.sent = 0; D.http = "-";
        let buf = null;
        try { buf = await readPiece(f, jb.have, jb.have + len); if (!buf || buf.byteLength !== len) throw new Error("short read " + (buf ? buf.byteLength : 0) + "/" + len); }
        catch (e) { D.ms = Date.now() - t0; D.last = "read: " + String((e && (e.name ? e.name + " " : "") + (e.message || "")) || e).slice(0, 90);
          fail(t("The file could not be read. A photo from iCloud: open it in the Photos app first (so it is loaded), then choose it again."), true); return; }
        if (!fails) jb.state = t("Piece {n} of {m}").replace("{n}", D.n).replace("{m}", D.of);
        jb.part = 0; paintJobs();
        try { res = await sendPiece(jb, jb.have, buf); D.ms = Date.now() - t0; D.sent = len; }
        catch (e) {
          D.ms = Date.now() - t0; D.sent = e.sent || 0; jb.part = 0;
          if (jb.cancel) break;
          fails++; D.last = e.kind === "timeout" ? "timeout: no progress / answer for " + Math.round(UP.idle / 1000) + " s" : "network error (connection dropped)";
          if (fails >= 2 && cs > UP.small) cs = UP.small;                    // smaller pieces get through where big ones do not
          if (fails >= 4 && cs > UP.tiny) cs = UP.tiny;
          jb.cs = cs;
          if (fails >= UP.tries) break;
          jb.state = t(e.kind === "timeout" ? "No answer - trying again …" : "Connection lost - trying again …") + " (" + (fails + 1) + "/" + UP.tries + ")"; paintJobs();
          await sleep(Math.min(UP.wait * fails, 4 * UP.wait));
          const s = await postT(startBody);                                // the piece may have arrived after all: ask where the upload stands
          if (s.ok && s.id === jb.id && typeof s.have === "number") jb.have = s.have;
          if (jb.have >= f.size) break;
        }
        buf = null;
      }
      if (jb.cancel) { await abort(); return; }
      if (jb.have >= f.size) break;
      if (!res) { fail(t("MoveEye did not answer - the upload stopped. «Try again» continues where it stopped."), true); return; }
      const k = res.k; D.http = res.status;
      if (res.status === 409 && typeof k.have === "number" && k.have !== jb.have) { jb.have = k.have; jb.part = 0; stuck = 0; continue; }
      if (res.status === 409 || res.status === 408 || res.status >= 500 && res.status !== 507) {          // busy / the body did not arrive / a hiccup: a few more times
        D.last = "HTTP " + res.status + (k.error ? " " + String(k.error).slice(0, 60) : "");
        if (res.status === 408 && cs > UP.small) jb.cs = cs = UP.small;
        if (++stuck >= UP.tries) { fail(k.error || t("MoveEye did not answer - the upload stopped. «Try again» continues where it stopped."), true); return; }
        jb.state = t("No answer - trying again …") + " (" + (stuck + 1) + "/" + UP.tries + ")"; jb.part = 0; paintJobs(); await sleep(UP.wait); continue; }
      if (!k.ok) { D.last = "HTTP " + res.status; fail(k.error || ("error " + res.status), false); return; }
      jb.have = k.have; jb.part = 0; n++; stuck = 0; jb.state = ""; paintJobs();
    }
    jb.state = ""; jb.part = 0; paintJobs();
    const z = await postT({action: "finish", id: jb.id, lang: LANG}, 4 * UP.post);
    if (!z.ok) { D.n = D.n || 1; D.of = D.of || 1; D.last = z.lost ? "finish: no answer" : "finish: refused"; fail(z.lost ? t("No connection to MoveEye.") : (z.error || t("error")), z.lost); return; }
    jb.done = true; jb.have = f.size;
  }
  $("#tz-upb").onclick = () => $("#tz-file").click();
  $("#tz-file").onchange = e => { addFiles(e.target.files); e.target.value = ""; };
  const mkFile = async (action, q, ph) => { const n = prompt(t(q), ph ? t(ph) : ""); if (!n) return null;
    const r = await post("/api/tausch", {action, name: n, area: S.area, folder: S.area === "all" ? S.folder : "", lang: LANG});
    if (!r.ok) { msg("⚠ " + (r.error || "error"), true); return null; } msg(""); await load(); return r.file; };
  $("#tz-mkt").onclick = async () => { const f = await mkFile("newtext", "Name of the new text (.txt or .md)", "Notes.txt"); if (f) openText(f); };
  $("#tz-mkc").onclick = async () => { const f = await mkFile("newchat", "Name of the new chat", ""); if (f) openChat(f); };
  /*TZEDIT*/
  $("#tz-mkd").onclick = async () => { const n = prompt(t("Name of the new folder")); if (!n) return;
    const r = await post("/api/tausch", {action: "mkdir", name: n, lang: LANG}); if (!r.ok) msg("⚠ " + (r.error || "error"), true); else { msg(""); load(); } };
  ["all", "mine"].forEach(a => { $("#tz-t-" + a).onclick = () => { S.area = a; S.folder = ""; load(); }; });
  ["#tz-q", "#tz-kind", "#tz-sort"].forEach(s => $(s).addEventListener("input", () => S.j && paint()));
  $("#tz-view").onclick = () => { S.view = S.view === "list" ? "grid" : "list"; try { localStorage.setItem("tausch-view", S.view); } catch (e) {} paint(); };
  let dragN = 0;
  const dz = $("#tz-drop"), canDrop = e => has("files_up") && S.j && S.j.on && e.dataTransfer && [...(e.dataTransfer.types || [])].includes("Files");
  addEventListener("dragenter", e => { if (!canDrop(e)) return; e.preventDefault(); dragN++; dz.classList.add("on"); });
  addEventListener("dragover", e => { if (canDrop(e)) e.preventDefault(); });
  addEventListener("dragleave", () => { dragN = Math.max(0, dragN - 1); if (!dragN) dz.classList.remove("on"); });
  addEventListener("drop", e => { dragN = 0; dz.classList.remove("on"); if (!canDrop(e)) return; e.preventDefault(); addFiles(e.dataTransfer.files); });
  addEventListener("beforeunload", e => { if (S.busy) { e.preventDefault(); e.returnValue = ""; } });
  (async () => { await initAppearance(); document.querySelectorAll("[data-i18n-ph]").forEach(x => x.placeholder = t(x.dataset.i18nPh)); load(); })();
})();
/*ALERTS*/
</script>
</body></html>
"""

TAUSCH_GUEST_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex">
<title>MoveEye – Files</title>
<style>
html,body{margin:0;background:#0a0e14;color:#e6edf3;font:15px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.top{display:flex;align-items:center;gap:10px;padding:10px 14px;padding-top:max(10px,env(safe-area-inset-top))}
.top b{font-size:17px}.top a{color:#8ab4f8;text-decoration:none;margin-left:auto;font-size:14px}
main{padding:0 14px 30px;max-width:1000px;margin:0 auto}.mut{color:#8b9bb0;font-size:13px}
.crumb{margin:4px 0 10px;font-size:14px}.crumb a{color:#8ab4f8;cursor:pointer}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.it{border:1px solid #1f2b3a;border-radius:12px;background:#111822;overflow:hidden;cursor:pointer;min-width:0}
.it .th{aspect-ratio:4/3;background:#0c121a;display:flex;align-items:center;justify-content:center;font-size:42px;overflow:hidden}
.it img{width:100%;height:100%;object-fit:cover;display:block}
.it .nm{padding:6px 8px;font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:flex;flex-direction:column;z-index:9}
.lb .bar{display:flex;gap:8px;align-items:center;padding:10px 12px;padding-top:max(10px,env(safe-area-inset-top))}
.lb .bar b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lb button{background:#1a2433;color:#fff;border:1px solid #1f2b3a;border-radius:10px;padding:8px 14px;font:inherit}
.lb .bd{flex:1;display:flex;align-items:center;justify-content:center;min-height:0;padding:8px;flex-direction:column;gap:8px}
.lb img{max-width:100%;max-height:100%;object-fit:contain;border-radius:8px}
.lb .doc{align-self:stretch;flex:1;overflow:auto;background:#111822;border-radius:10px;padding:12px 14px;line-height:1.55;overflow-wrap:anywhere}
.lb .doc pre{white-space:pre-wrap}.lb .doc a{color:#8ab4f8}
.bub{background:#1a2433;border-radius:12px;padding:6px 10px;margin:0 0 8px}.bub .hd{font-size:11.5px;color:#8b9bb0}.bub .tx{white-space:pre-wrap;overflow-wrap:anywhere}
</style></head><body>
<div class="top"><b>📂 MoveEye</b><a href="__BASE__">← __LIVE__</a></div>
<main><div class="mut" id="nt"></div><div class="crumb" id="cr"></div><div class="grid" id="g"></div><p class="mut" id="em" hidden></p></main>
<script>
const TX = /*TX*/{}, $ = s => document.querySelector(s);
/*TZMD*/
const KIC = {image: "🖼", video: "🎬", audio: "🎵", pdf: "📕", doc: "📄", text: "📝", chat: "💬", archive: "🗜", other: "📦"};
let F = "";
$("#nt").textContent = TX.note;
function el(t, c, x) { const e = document.createElement(t); if (c) e.className = c; if (x !== undefined) e.textContent = x; return e; }
async function load() {
  let j = null;
  try { const r = await fetch("__BASE__/tausch/list?folder=" + encodeURIComponent(F), {cache: "no-store"}); if (r.status === 404) { $("#g").textContent = ""; $("#em").hidden = false; $("#em").textContent = TX.expired; return; } j = await r.json(); } catch (e) { return; }
  if (!j.ok && F) { F = ""; return load(); }
  const g = $("#g"), cr = $("#cr"); g.textContent = ""; cr.textContent = "";
  if (F) { const a = el("a", "", "📂 " + TX.all); a.onclick = () => { F = ""; load(); }; cr.append(a, document.createTextNode(" › " + F)); }
  (j.folders || []).forEach(d => { const it = el("div", "it"), th = el("div", "th", "📁"); it.append(th, el("div", "nm", d.name + " (" + d.n + ")")); it.onclick = () => { F = d.name; load(); }; g.appendChild(it); });
  (j.files || []).forEach(f => { const it = el("div", "it"), th = el("div", "th");
    if (f.thumb) { const im = el("img"); im.loading = "lazy"; im.alt = ""; im.src = "__BASE__/tausch/t/" + f.id + ".jpg"; th.appendChild(im); } else th.textContent = KIC[f.kind] || "📦";
    it.append(th, el("div", "nm", f.name)); it.onclick = () => show(f); g.appendChild(it); });
  $("#em").hidden = g.children.length > 0; $("#em").textContent = TX.empty;
}
function show(f) {
  const ov = el("div", "lb"), bar = el("div", "bar"), bd = el("div", "bd"), x = el("button", "", "✕");
  x.onclick = () => ov.remove(); bar.append(el("b", "", f.name), x);
  let iv = 0;
  if (f.kind === "text" || f.kind === "chat") {
    const doc = el("div", "doc"); bd.appendChild(doc);
    const get = async () => { let j = null; try { j = await (await fetch("__BASE__/tausch/" + f.kind + "/" + f.id, {cache: "no-store"})).json(); } catch (e) { return; }
      if (!j || !j.ok) { doc.textContent = TX.expired; clearInterval(iv); return; }
      if (f.kind === "text") { if (j.md) doc.innerHTML = tzMd(j.text); else { doc.textContent = ""; const pr = el("pre"); pr.textContent = j.text; doc.appendChild(pr); } return; }
      const near = doc.scrollHeight - doc.scrollTop - doc.clientHeight < 80; doc.textContent = "";
      (j.posts || []).forEach(p => { const b = el("div", "bub"); b.append(el("div", "hd", p.by + " · " + new Date(p.t * 1000).toLocaleString()), el("div", "tx", p.del ? "–" : p.x)); doc.appendChild(b); });
      if (near) doc.scrollTop = doc.scrollHeight; };
    get(); if (f.kind === "chat") iv = setInterval(() => { if (!document.hidden && document.body.contains(ov)) get(); else if (!document.body.contains(ov)) clearInterval(iv); }, 8000);
    bd.appendChild(el("div", "mut", TX.read));
  } else {
    if (f.thumb) { const im = el("img"); im.alt = ""; im.src = "__BASE__/tausch/p/" + f.id + ".jpg"; bd.appendChild(im); } else bd.appendChild(el("div", "", KIC[f.kind] || "📦"));
    bd.appendChild(el("div", "mut", TX.only));
  }
  ov.append(bar, bd); ov.onclick = e => { if (e.target === ov || e.target === bd) ov.remove(); }; document.body.appendChild(ov);
}
load(); setInterval(() => { if (!document.hidden) fetch("__BASE__/tausch/list", {method: "HEAD"}).then(r => { if (r.status === 404) load(); }).catch(() => {}); }, 30000);
</script></body></html>
"""


# a small, safe Markdown: everything is escaped FIRST, only then our own tags are added (links only http / https)
TZ_MD_JS = r"""
function tzEsc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"); }
function tzMd(src) {
  const inl = s => tzEsc(s).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(/(^|[^*\w])\*([^*\s][^*]*)\*/g, "$1<i>$2</i>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s()<>]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer nofollow">$1</a>');
  const out = []; let code = false, list = null;
  const close = () => { if (list) { out.push("</" + list + ">"); list = null; } };
  String(src || "").split("\n").forEach(ln => {
    let m;
    if (/^```/.test(ln)) { close(); out.push(code ? "</code></pre>" : "<pre><code>"); code = !code; return; }
    if (code) { out.push(tzEsc(ln) + "\n"); return; }
    if ((m = ln.match(/^(#{1,4})\s+(.*)$/))) { close(); const n = m[1].length + 1; out.push("<h" + n + ">" + inl(m[2]) + "</h" + n + ">"); }
    else if ((m = ln.match(/^\s*[-*+]\s+(.*)$/))) { if (list !== "ul") { close(); out.push("<ul>"); list = "ul"; } out.push("<li>" + inl(m[1]) + "</li>"); }
    else if ((m = ln.match(/^\s*\d+[.)]\s+(.*)$/))) { if (list !== "ol") { close(); out.push("<ol>"); list = "ol"; } out.push("<li>" + inl(m[1]) + "</li>"); }
    else if ((m = ln.match(/^>\s?(.*)$/))) { close(); out.push("<blockquote>" + inl(m[1]) + "</blockquote>"); }
    else if (/^\s*(---|\*\*\*)\s*$/.test(ln)) { close(); out.push("<hr>"); }
    else if (ln.trim()) { close(); out.push("<p>" + inl(ln) + "</p>"); }
    else close();
  });
  close(); if (code) out.push("</code></pre>");
  return out.join("");
}
function tzDiff(a, b) {
  const A = String(a).split("\n"), B = String(b).split("\n"), n = A.length, m = B.length;
  if (n * m > 4000000) return null;
  const dp = []; for (let i = 0; i <= n; i++) dp.push(new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) dp[i][j] = A[i] === B[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out = []; let i = 0, j = 0;
  while (i < n && j < m) { if (A[i] === B[j]) { out.push([" ", A[i]]); i++; j++; } else if (dp[i + 1][j] >= dp[i][j + 1]) out.push(["-", A[i++]]); else out.push(["+", B[j++]]); }
  while (i < n) out.push(["-", A[i++]]); while (j < m) out.push(["+", B[j++]]);
  return out;
}
"""

TZ_EDIT_JS = r"""
  // ---- 📝 text editor: versions, «somebody changed it meanwhile» ----
  async function getJ(u) { try { const r = await fetch(u, {cache: "no-store"}); return await r.json(); } catch (e) { return null; } }
  async function openText(f, keep) {
    const j = await getJ("/api/tausch/text?id=" + f.id + "&lang=" + LANG);
    if (!j || !j.ok) { msg("⚠ " + ((j && j.error) || t("No connection to MoveEye.")), true); return; }
    if (keep) keep.remove();
    const ov = el("div", "tz-lb tz-ed"), bar = el("div", "bar"), bd = el("div", "bd tz-edb"), ft = el("div", "tz-edf"), st = el("span", "st");
    ov.id = "tz-editor";
    let ver = j.ver, base = j.text, by = j.by, tt = j.t, pan = null, mono = false;
    try { mono = localStorage.getItem("tausch-mono") === "1"; } catch (e) {}
    const ta = el("textarea", "tz-ta" + (mono ? " mono" : "")); ta.value = j.text; ta.readOnly = !j.edit; ta.spellcheck = true; ta.id = "tz-ta";
    const pv = el("div", "tz-md"); pv.id = "tz-mdv";
    let view = j.md && !j.edit;
    const dirty = () => ta.value !== base;
    const status = () => { st.textContent = (dirty() ? "● " + t("not saved") + " · " : "") + t("Version {v}").replace("{v}", ver) + " · " + by + " · " + when(tt) + (j.edit ? "" : " · " + t("read only")); };
    const show = () => { ta.hidden = view; pv.hidden = !view; if (view) pv.innerHTML = tzMd(ta.value); if (pvb) pvb.textContent = view ? "✎ " + t("Edit") : "👁 " + t("Preview"); };
    const close = () => { if (dirty() && !confirm(t("Close without saving?"))) return; ov.remove(); load(); };
    bar.appendChild(el("b", "", "📝 " + f.name));
    let pvb = null;
    if (j.md) { pvb = el("button", "sec"); pvb.type = "button"; pvb.id = "tz-pv"; pvb.onclick = () => { view = !view; show(); }; bar.appendChild(pvb); }
    const mb = el("button", "sec", "Aa"); mb.type = "button"; mb.title = t("Monospace"); mb.onclick = () => { mono = !mono; ta.classList.toggle("mono", mono); try { localStorage.setItem("tausch-mono", mono ? "1" : "0"); } catch (e) {} };
    const hb = el("button", "sec", "🕘"); hb.type = "button"; hb.title = t("Versions"); hb.id = "tz-hist"; hb.onclick = () => history();
    const x = el("button", "sec", "✕"); x.type = "button"; x.onclick = close;
    bar.append(mb, hb);
    if (f.dl !== false) { const a = el("a", "btn sec", "⬇"); a.href = "/tausch/dl/" + f.id; a.setAttribute("download", ""); a.title = t("Download"); bar.appendChild(a); }
    bar.appendChild(x);
    bd.append(ta, pv);
    const sv = el("button", "", "💾 " + t("Save")); sv.type = "button"; sv.id = "tz-save"; sv.hidden = !j.edit;
    sv.onclick = () => save();
    ft.append(st, sv);
    ov.append(bar, bd, ft); document.body.appendChild(ov);
    ta.addEventListener("input", status);
    ta.addEventListener("keydown", e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); save(); } });
    const panel = (title) => { if (pan) pan.remove(); pan = el("div", "tz-pan"); const h = el("h3", "", title), c = el("button", "sec", "✕"); c.type = "button";
      c.style.cssText = "float:right"; c.onclick = () => { pan.remove(); pan = null; }; pan.append(c, h); bd.style.position = "relative"; bd.appendChild(pan); return pan; };
    async function save(force) {
      sv.disabled = true;
      const r = await post("/api/tausch", {action: "save", id: f.id, text: ta.value, ver: force ? force : ver, lang: LANG});
      sv.disabled = false;
      if (r.conflict) return conflict(r);
      if (!r.ok) { st.textContent = "⚠ " + (r.error || t("error")); return; }
      ver = r.ver; base = ta.value; by = t("you"); tt = Date.now() / 1000; status(); toast("💾 " + t("Saved"));
    }
    function conflict(r) {
      const p = panel("⚠ " + t("Meanwhile {who} has changed something.").replace("{who}", r.by || "?")); p.id = "tz-conflict";
      p.appendChild(el("div", "mut", t("Your text is not saved yet. What now?")));
      const dv = el("div"), bs = el("div", "btns");
      const b1 = el("button", "sec", "🔍 " + t("Show the differences")), b2 = el("button", "", "⤴ " + t("Overwrite anyway")),
        b3 = el("button", "sec", "📄 " + t("Save mine as a copy")), b4 = el("button", "sec", t("Cancel"));
      [b1, b2, b3, b4].forEach(b => b.type = "button"); b1.id = "tz-c-diff"; b2.id = "tz-c-over"; b3.id = "tz-c-copy";
      b1.onclick = () => { dv.textContent = ""; const d = tzDiff(r.text, ta.value);
        if (!d) { dv.appendChild(el("div", "mut", t("Too long for a comparison."))); return; }
        dv.appendChild(el("div", "mut", "− " + t("now on MoveEye") + " (" + (r.by || "?") + ") · + " + t("yours")));
        const box = el("div", "tz-diff"); d.forEach(([k, l]) => { if (k === " " && d.length > 60) return; box.appendChild(el("div", k === "-" ? "a" : k === "+" ? "b" : "", k + " " + l)); });
        dv.appendChild(box); };
      b2.onclick = () => { p.remove(); pan = null; save(r.ver); };
      b3.onclick = async () => { const dot = f.name.lastIndexOf("."), nm = (dot > 0 ? f.name.slice(0, dot) : f.name) + " (" + t("my version") + ")" + (dot > 0 ? f.name.slice(dot) : ".txt");
        const z = await post("/api/tausch", {action: "newtext", name: nm, area: f.area, folder: f.folder || "", text: ta.value, lang: LANG});
        if (!z.ok) { toast("⚠ " + (z.error || t("error"))); return; } base = ta.value; toast("📄 " + z.file.name); ov.remove(); await load(); openText(z.file); };
      b4.onclick = () => { p.remove(); pan = null; };
      bs.append(b1, b2, b3, b4); p.append(bs, dv);
    }
    async function history() {
      const k = await getJ("/api/tausch/text?id=" + f.id + "&lang=" + LANG); const p = panel("🕘 " + t("Versions")); p.id = "tz-versions";
      const h = (k && k.hist) || [];
      if (!h.length) { p.appendChild(el("div", "mut", t("No older versions yet."))); return; }
      p.appendChild(el("div", "mut", t("The last 20 versions are kept (they count in the space of the owner).")));
      h.forEach(v => { const r = el("div", "row"), a = el("button", "sec", "👁"), b = el("button", "sec", "↩ " + t("Restore")); a.type = b.type = "button";
        a.title = t("Show"); r.append(el("span", "", t("Version {v}").replace("{v}", v.v) + " · " + v.by + " · " + when(v.t) + " · " + fmt(v.size)), a);
        a.onclick = async () => { const o = await getJ("/api/tausch/text?id=" + f.id + "&v=" + v.v + "&lang=" + LANG); if (!o || !o.ok) return;
          const box = el("div", "tz-diff"); box.textContent = o.text; const old = p.querySelector(".tz-diff"); if (old) old.remove(); p.appendChild(box); };
        if (j.edit) { b.onclick = async () => { if (dirty() && !confirm(t("Close without saving?"))) return;
            const z = await post("/api/tausch", {action: "restore", id: f.id, v: v.v, ver: ver, lang: LANG});
            if (z.conflict) { p.remove(); pan = null; return conflict(z); }
            if (!z.ok) { toast("⚠ " + (z.error || t("error"))); return; } toast("↩ " + t("Version {v}").replace("{v}", v.v)); openText(f, ov); };
          r.appendChild(b); }
        p.appendChild(r); });
    }
    status(); show(); if (j.edit && !view) ta.focus();
  }
  // ---- 💬 chat: posts with name and time from the server; while open: one waiting request (no extra stream) ----
  async function openChat(f) {
    const ov = el("div", "tz-lb tz-chat"), bar = el("div", "bar"), list = el("div", "tz-cl"), form = el("div", "tz-cf"), ta = el("textarea"), send = el("button", "", "➤");
    ov.id = "tz-chatv"; list.id = "tz-cl"; ta.id = "tz-cin"; send.id = "tz-csend"; send.type = "button"; send.title = t("Send");
    let rev = -1, after = 0, open = true, first = true, wr = false;
    const posts = new Map(), x = el("button", "sec", "✕"); x.type = "button"; x.onclick = () => { open = false; ov.remove(); load(); };
    const nm = el("b", "", "💬 " + f.name.replace(/\.chat$/i, "")); bar.append(nm, x);
    ta.rows = 1; ta.maxLength = 4000; ta.placeholder = t("Message"); ta.enterKeyHint = "send";
    form.append(ta, send); ov.append(bar, list, form); document.body.appendChild(ov);
    const vv = window.visualViewport;                   // iPhone: the keyboard makes the visible part smaller
    const fit = () => { if (!vv || !open) return; ov.style.top = vv.offsetTop + "px"; ov.style.height = vv.height + "px"; ov.style.bottom = "auto"; };
    if (vv) { vv.addEventListener("resize", fit); vv.addEventListener("scroll", fit); fit(); }
    const grow = () => { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, innerHeight * 0.3) + "px"; };
    function paintC() {
      const near = list.scrollHeight - list.scrollTop - list.clientHeight < 90;
      list.textContent = "";
      const ps = [...posts.values()].sort((a, b) => a.n - b.n);
      if (!ps.length) list.appendChild(el("div", "tz-empty", t("No messages yet.") + (wr ? " " + t("Write the first one below.") : "")));
      ps.forEach(p => { const b = el("div", "tz-bub" + (p.mine ? " me" : "") + (p.del ? " del" : "")), hd = el("div", "hd");
        hd.append(el("span", "", (p.mine ? t("you") : p.by) + " · " + when(p.t) + (p.ed && !p.del ? " · " + t("changed") : "")));
        if (p.ce) { const e = el("button", "", "✎"); e.title = t("Change"); e.onclick = async () => { const v = prompt(t("Change the message"), p.x); if (v === null) return;
          const r = await post("/api/tausch", {action: "chat_edit", id: f.id, n: p.n, text: v, lang: LANG}); if (!r.ok) toast("⚠ " + (r.error || t("error"))); pull(false); }; hd.appendChild(e); }
        if (p.cd) { const d = el("button", "", "🗑"); d.title = t("Delete"); d.onclick = async () => { if (!confirm(t("Delete this message?"))) return;
          const r = await post("/api/tausch", {action: "chat_del", id: f.id, n: p.n, lang: LANG}); if (!r.ok) toast("⚠ " + (r.error || t("error"))); pull(false); }; hd.appendChild(d); }
        b.append(hd, el("div", "tx", p.del ? t("Message deleted") : p.x)); list.appendChild(b); });
      if (near || first) list.scrollTop = list.scrollHeight;
      first = false;
    }
    async function pull(wait) {
      const j = await getJ("/api/tausch/chat?id=" + f.id + "&rev=" + rev + "&after=" + after + (wait ? "&wait=1" : "") + "&lang=" + LANG);
      if (!j) throw new Error("net");
      if (!j.ok) { open = false; toast("⚠ " + (j.error || t("error"))); ov.remove(); load(); return; }
      if (j.full) posts.clear();
      (j.posts || []).forEach(p => { posts.set(p.n, p); after = Math.max(after, p.n); });
      const ch = j.rev !== rev; rev = j.rev; wr = !!j.write; form.hidden = !wr;
      if (!wr && !ov.querySelector(".ro")) ov.insertBefore(el("div", "mut ro", "👁 " + t("read only")), list);
      if (ch || j.full) paintC();
      return ch;
    }
    async function loop() {
      while (open) {
        if (document.hidden) { await sleep(1500); continue; }
        const t0 = Date.now();
        let ch = false;
        try { ch = await pull(rev >= 0); } catch (e) { await sleep(3000); continue; }
        if (!ch && Date.now() - t0 < 1500) await sleep(3000);       // no place for a waiting request: ask every few seconds
      }
    }
    async function sendIt() {
      const v = ta.value.trim(); if (!v) return;
      send.disabled = true; const r = await post("/api/tausch", {action: "post", id: f.id, text: v, lang: LANG}); send.disabled = false;
      if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; }
      ta.value = ""; grow(); first = true; pull(false);
    }
    send.onclick = sendIt;
    ta.addEventListener("input", grow);
    ta.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey && !matchMedia("(pointer:coarse)").matches) { e.preventDefault(); sendIt(); } });
    loop();
  }
"""


def tausch_page_html():
    return (render_page(TAUSCH_PAGE, "more").replace("/*TZDE*/{}", json.dumps(_TZ_DE, ensure_ascii=False), 1)
            .replace("/*TZMD*/", TZ_MD_JS, 1).replace("/*TZEDIT*/", TZ_EDIT_JS, 1))


def tausch_guest_html(token):
    import html as _h
    L = sx_req_lang()
    tx = {"note": tr("Shared files · only to look at (no download)", L), "all": tr("For everyone", L), "empty": tr("No files yet.", L),
          "expired": tr("access expired", L), "only": tr("Preview only - downloading needs a login.", L), "read": tr("read only", L)}
    return (TAUSCH_GUEST_HTML.replace("/*TX*/{}", json.dumps(tx, ensure_ascii=False).replace("</", "<\\/"), 1).replace("/*TZMD*/", TZ_MD_JS, 1)
            .replace("__LIVE__", _h.escape(tr("Live", L))).replace("__BASE__", "/g/" + token))


# ---- texts (English key: Deutsch, français, italiano, rumantsch) --------------------------------------------------------------------
_HX_TAUSCH = {
    "File exchange": ("Digitaler Rucksack", "Sac à dos numérique", "Zaino digitale", "Satgados digital"),
    "Share photos, videos and documents - for everyone or only for you": (
        "Fotos, Videos und Dokumente teilen – für alle oder nur für dich", "Partager photos, vidéos et documents – pour tous ou seulement pour toi",
        "Condividere foto, video e documenti – per tutti o solo per te", "Parter fotos, videos e documents – per tuts u mo per tai"),
    "For everyone": ("Für alle", "Pour tous", "Per tutti", "Per tuts"),
    "My files": ("Meine Dateien", "Mes fichiers", "I miei file", "Mias datotecas"),
    "Upload": ("Hochladen", "Envoyer", "Carica", "Chargiar si"),
    "New folder": ("Neuer Ordner", "Nouveau dossier", "Nuova cartella", "Nov ordinatur"),
    "Name of the new folder": ("Name des neuen Ordners", "Nom du nouveau dossier", "Nome della nuova cartella", "Num dal nov ordinatur"),
    "Search": ("Suchen", "Rechercher", "Cerca", "Tschertgar"),
    "All types": ("Alle Arten", "Tous les types", "Tutti i tipi", "Tut las sorts"),
    "Pictures": ("Bilder", "Images", "Immagini", "Maletgs"),
    "Videos": ("Videos", "Vidéos", "Video", "Videos"),
    "Sound": ("Ton", "Son", "Audio", "Tun"),
    "Documents": ("Dokumente", "Documents", "Documenti", "Documents"),
    "Other": ("Andere", "Autres", "Altro", "Auter"),
    "Newest first": ("Neueste zuerst", "Plus récents d’abord", "Più recenti prima", "Ils pli novs l’emprim"),
    "Oldest first": ("Älteste zuerst", "Plus anciens d’abord", "Più vecchi prima", "Ils pli vegls l’emprim"),
    "Name": ("Name", "Nom", "Nome", "Num"),
    "Size": ("Grösse", "Taille", "Dimensione", "Grondezza"),
    "Uploaded by": ("Hochgeladen von", "Envoyé par", "Caricato da", "Chargià si da"),
    "Grid": ("Kacheln", "Grille", "Griglia", "Quadrels"),
    "List": ("Liste", "Liste", "Elenco", "Glista"),
    "Drop the files here": ("Dateien hier loslassen", "Dépose les fichiers ici", "Rilascia qui i file", "Laschar las datotecas qua"),
    "USB stick": ("USB-Stick", "Clé USB", "Chiavetta USB", "Stick USB"),
    "SSD": ("SSD", "SSD", "SSD", "SSD"),
    "Memory card": ("Speicherkarte", "Carte mémoire", "Scheda di memoria", "Carta da memoria"),
    "Drive": ("Laufwerk", "Lecteur", "Unità", "Unitad"),
    "{a} of {b} used": ("{a} von {b} belegt", "{a} sur {b} utilisés", "{a} di {b} occupati", "{a} da {b} occupà"),
    "at most {n} per file": ("höchstens {n} pro Datei", "au plus {n} par fichier", "al massimo {n} per file", "al pli {n} per datoteca"),
    "{n} free on the storage": ("{n} frei auf dem Speicher", "{n} libres sur le support", "{n} liberi sul supporto", "{n} liber sin la memoria"),
    "Your files: {a} of {b}": ("Deine Dateien: {a} von {b}", "Tes fichiers : {a} sur {b}", "I tuoi file: {a} di {b}", "Tias datotecas: {a} da {b}"),
    "The file exchange is switched off.": ("Der Digitale Rucksack ist ausgeschaltet.", "Le sac à dos numérique est désactivé.", "Lo zaino digitale è disattivato.",
                                           "Il satgados digital è deactivà."),
    "Switch it on under Settings → System → File exchange.": (
        "Einschalten unter Einstellungen → System → Digitaler Rucksack.", "L’activer sous Réglages → Système → Sac à dos numérique.",
        "Attivarlo in Impostazioni → Sistema → Zaino digitale.", "L’activar sut Configuraziuns → Sistem → Satgados digital."),
    "The storage (USB stick / SSD) is not there - plug it in again.": (
        "Der Speicher (USB-Stick / SSD) fehlt – bitte wieder einstecken.", "Le support (clé USB / SSD) manque – rebranche-le.",
        "Il supporto (chiavetta USB / SSD) manca – ricollegalo.", "La memoria (stick USB / SSD) manca – la tacar puspè."),
    "The memory card is write-protected (overlay) - files would be lost at the next restart. Use a USB stick.": (
        "Die Speicherkarte ist schreibgeschützt (Overlay) – Dateien wären beim nächsten Neustart weg. Bitte einen USB-Stick verwenden.",
        "La carte mémoire est protégée en écriture (overlay) – les fichiers seraient perdus au prochain redémarrage. Utilise une clé USB.",
        "La scheda di memoria è protetta da scrittura (overlay) – i file andrebbero persi al prossimo riavvio. Usa una chiavetta USB.",
        "La carta da memoria è protegida (overlay) – las datotecas fissan davent tar la proxima reaviada. Duvra in stick USB."),
    "Not enough free space on the storage: MoveEye always keeps {n} free (for recordings and the system).": (
        "Zu wenig Platz auf dem Speicher: MoveEye lässt immer {n} frei (für Aufnahmen und das System).",
        "Pas assez de place sur le support : MoveEye laisse toujours {n} libres (pour les enregistrements et le système).",
        "Spazio insufficiente sul supporto: MoveEye lascia sempre {n} liberi (per le registrazioni e il sistema).",
        "Memia pauc spazi sin la memoria: MoveEye lascha adina {n} liber (per registraziuns ed il sistem)."),
    "Only you see these files. As administrator you also see the private files of the others.": (
        "Nur du siehst diese Dateien. Als Administrator siehst du auch die privaten Dateien der anderen.",
        "Toi seul vois ces fichiers. En tant qu’administrateur, tu vois aussi les fichiers privés des autres.",
        "Solo tu vedi questi file. Come amministratore vedi anche i file privati degli altri.",
        "Mo ti vesas questas datotecas. Sco administratur vesas ti er las datotecas privatas dals auters."),
    "Only you (and the administrator) see these files.": (
        "Nur du (und der Administrator) siehst diese Dateien.", "Seuls toi (et l’administrateur) voyez ces fichiers.",
        "Solo tu (e l’amministratore) vedete questi file.", "Mo ti (e l’administratur) vesais questas datotecas."),
    "Everybody with access to MoveEye sees these files. Upload with the button or drag files onto the page.": (
        "Alle mit Zugang zu MoveEye sehen diese Dateien. Hochladen mit dem Knopf oder Dateien auf die Seite ziehen.",
        "Toutes les personnes ayant accès à MoveEye voient ces fichiers. Envoie avec le bouton ou glisse des fichiers sur la page.",
        "Tutti quelli con accesso a MoveEye vedono questi file. Carica con il pulsante o trascina i file sulla pagina.",
        "Tuts cun access a MoveEye vesan questas datotecas. Chargiar si cun il buttun u trair datotecas sin la pagina."),
    "Everybody with access to MoveEye sees these files.": (
        "Alle mit Zugang zu MoveEye sehen diese Dateien.", "Toutes les personnes ayant accès à MoveEye voient ces fichiers.",
        "Tutti quelli con accesso a MoveEye vedono questi file.", "Tuts cun access a MoveEye vesan questas datotecas."),
    "file": ("Datei", "fichier", "file", "datoteca"),
    "files": ("Dateien", "fichiers", "file", "datotecas"),
    "you": ("du", "toi", "tu", "ti"),
    "Delete the folder with all its files?": ("Ordner mit allen Dateien löschen?", "Supprimer le dossier avec tous ses fichiers ?",
                                              "Eliminare la cartella con tutti i file?", "Stizzar l’ordinatur cun tut las datotecas?"),
    "Delete the folder?": ("Ordner löschen?", "Supprimer le dossier ?", "Eliminare la cartella?", "Stizzar l’ordinatur?"),
    "Delete this file? It cannot be undone.": ("Diese Datei löschen? Das lässt sich nicht rückgängig machen.", "Supprimer ce fichier ? C’est définitif.",
                                               "Eliminare questo file? Non si può annullare.", "Stizzar questa datoteca? Quai na po betg vegnir revocà."),
    "Nothing found.": ("Nichts gefunden.", "Rien trouvé.", "Nessun risultato.", "Chattà nagut."),
    "No private files yet.": ("Noch keine privaten Dateien.", "Pas encore de fichiers privés.", "Ancora nessun file privato.", "Anc naginas datotecas privatas."),
    "No files yet.": ("Noch keine Dateien.", "Pas encore de fichiers.", "Ancora nessun file.", "Anc naginas datotecas."),
    "Upload the first one with «Upload».": ("Lade die erste mit «Hochladen» hoch.", "Envoie le premier avec «Envoyer».", "Carica il primo con «Carica».",
                                            "Chargia si l’emprima cun «Chargiar si»."),
    "No preview for this kind of file (for safety only as download).": (
        "Keine Vorschau für diese Art Datei (aus Sicherheitsgründen nur als Download).", "Pas d’aperçu pour ce type de fichier (par sécurité seulement en téléchargement).",
        "Nessuna anteprima per questo tipo di file (per sicurezza solo come download).", "Nagina prevista per questa sort da datoteca (per segirezza mo sco download)."),
    "No preview for this file.": ("Keine Vorschau für diese Datei.", "Pas d’aperçu pour ce fichier.", "Nessuna anteprima per questo file.", "Nagina prevista per questa datoteca."),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "Cancelled": ("Abgebrochen", "Annulé", "Annullato", "Interrut"),
    "Done": ("Fertig", "Terminé", "Fatto", "Finì"),
    "continues where it stopped …": ("macht dort weiter, wo es aufgehört hat …", "reprend là où il s’est arrêté …", "riprende da dove si era fermato …",
                                     "cuntinuescha là nua ch’el ha chalà …"),
    "Connection lost - trying again …": ("Verbindung weg – neuer Versuch …", "Connexion perdue – nouvel essai …", "Connessione persa – nuovo tentativo …",
                                         "Colliaziun interrutta – nov emprov …"),
    "Connection lost. Choose the same file again later: the upload continues where it stopped.": (
        "Verbindung weg. Wähle später dieselbe Datei nochmals: das Hochladen macht dort weiter, wo es aufgehört hat.",
        "Connexion perdue. Choisis plus tard le même fichier : l’envoi reprend là où il s’est arrêté.",
        "Connessione persa. Scegli più tardi lo stesso file: il caricamento riprende da dove si era fermato.",
        "Colliaziun interrutta. Tscherna pli tard la medema datoteca: il chargiar si cuntinuescha là nua ch’el ha chalà."),
    "No answer - trying again …": ("Keine Antwort – neuer Versuch …", "Pas de réponse – nouvel essai …", "Nessuna risposta – nuovo tentativo …",
                                   "Nagina resposta – nov emprov …"),
    "Piece {n} of {m}": ("Stück {n} von {m}", "Morceau {n} sur {m}", "Pezzo {n} di {m}", "Toc {n} da {m}"),
    "Try once more": ("Nochmal versuchen", "Réessayer", "Riprova", "Empruvar anc ina giada"),
    "MoveEye did not answer - the upload stopped. «Try again» continues where it stopped.": (
        "MoveEye hat nicht geantwortet – das Hochladen ist stehen geblieben. «Nochmal versuchen» macht dort weiter, wo es aufgehört hat.",
        "MoveEye n’a pas répondu – l’envoi s’est arrêté. «Réessayer» reprend là où il s’est arrêté.",
        "MoveEye non ha risposto – il caricamento si è fermato. «Riprova» riprende da dove si era fermato.",
        "MoveEye n’ha betg respundì – il chargiar si è sa fermà. «Empruvar anc ina giada» cuntinuescha là nua ch’el ha chalà."),
    "The file could not be read. A photo from iCloud: open it in the Photos app first (so it is loaded), then choose it again.": (
        "Die Datei konnte nicht gelesen werden. Ein Foto aus iCloud: bitte zuerst in der Fotos-App öffnen (damit es geladen ist), dann nochmals wählen.",
        "Le fichier n’a pas pu être lu. Une photo d’iCloud : ouvre-la d’abord dans l’app Photos (pour qu’elle soit chargée), puis choisis-la à nouveau.",
        "Impossibile leggere il file. Una foto di iCloud: aprila prima nell’app Foto (così viene caricata), poi sceglila di nuovo.",
        "La datoteca n’ha betg pudì vegnir legida. Ina foto dad iCloud: l’avra l’emprim en l’app Fotos (per ch’ella saja chargiada), lura la tscherna anc ina giada."),
    "No connection to MoveEye.": ("Keine Verbindung zu MoveEye.", "Pas de connexion à MoveEye.", "Nessuna connessione a MoveEye.", "Nagina colliaziun cun MoveEye."),
    "error": ("Fehler", "erreur", "errore", "errur"),
    "Shared files": ("Geteilte Dateien", "Fichiers partagés", "File condivisi", "Datotecas partidas"),
    "Shared files · only to look at (no download)": (
        "Geteilte Dateien · nur ansehen (kein Download)", "Fichiers partagés · seulement à regarder (pas de téléchargement)",
        "File condivisi · solo da guardare (nessun download)", "Datotecas partidas · mo guardar (nagin download)"),
    "Preview only - downloading needs a login.": (
        "Nur Vorschau – herunterladen geht nur mit Anmeldung.", "Aperçu seulement – le téléchargement demande une connexion.",
        "Solo anteprima – per scaricare serve l’accesso.", "Mo prevista – telechargiar mo cun annunzia."),
    "Files: see": ("Dateien: ansehen", "Fichiers : voir", "File: vedere", "Datotecas: guardar"),
    "Files: download": ("Dateien: herunterladen", "Fichiers : télécharger", "File: scaricare", "Datotecas: telechargiar"),
    "Files: upload": ("Dateien: hochladen", "Fichiers : envoyer", "File: caricare", "Datotecas: chargiar si"),
    "Files: manage all": ("Dateien: alles verwalten", "Fichiers : tout gérer", "File: gestire tutto", "Datotecas: administrar tut"),
    "File exchange on (Mehr → File exchange)": ("Digitaler Rucksack an (Mehr → Digitaler Rucksack)", "Sac à dos numérique activé (Plus → Sac à dos numérique)",
                                                "Zaino digitale attivo (Altro → Zaino digitale)", "Satgados digital activ (Dapli → Satgados digital)"),
    "Guests see «For everyone» (pictures only, no download)": (
        "Gäste sehen «Für alle» (nur Bilder, kein Download)", "Les invités voient «Pour tous» (images seulement, pas de téléchargement)",
        "Gli ospiti vedono «Per tutti» (solo immagini, nessun download)", "Ils giasts vesan «Per tuts» (mo maletgs, nagin download)"),
    "Push to me when someone uploads files (bundled)": (
        "Push an mich, wenn jemand Dateien hochlädt (gebündelt)", "Notification pour moi quand quelqu’un envoie des fichiers (regroupée)",
        "Notifica a me quando qualcuno carica file (raggruppata)", "Messadi a mai, sch’insatgi chargia si datotecas (unì)"),
    "Refuse programs and scripts (.exe, .sh, .py, .js …)": (
        "Programme und Skripte ablehnen (.exe, .sh, .py, .js …)", "Refuser les programmes et scripts (.exe, .sh, .py, .js …)",
        "Rifiutare programmi e script (.exe, .sh, .py, .js …)", "Refusar programs e scripts (.exe, .sh, .py, .js …)"),
    "Space for the file exchange in total (GB)": ("Platz für den Digitalen Rucksack gesamt (GB)", "Place pour le sac à dos numérique au total (Go)",
                                                  "Spazio per lo zaino digitale in totale (GB)", "Spazi per il satgados digital en total (GB)"),
    "At most per file (MB)": ("Höchstens pro Datei (MB)", "Au plus par fichier (Mo)", "Al massimo per file (MB)", "Al pli per datoteca (MB)"),
    "At most per user (GB)": ("Höchstens pro Benutzer (GB)", "Au plus par utilisateur (Go)", "Al massimo per utente (GB)", "Al pli per utilisader (GB)"),
    "Always keep free on the storage (GB)": ("Immer frei lassen auf dem Speicher (GB)", "Toujours laisser libre sur le support (Go)",
                                             "Lasciare sempre libero sul supporto (GB)", "Laschar adina liber sin la memoria (GB)"),
    "All files of the file exchange together. Uploads stop with a clear message when it is full.": (
        "Alle Dateien des Digitalen Rucksacks zusammen. Ist es voll, stoppt das Hochladen mit einer klaren Meldung.",
        "Tous les fichiers de l’échange ensemble. Quand c’est plein, l’envoi s’arrête avec un message clair.",
        "Tutti i file dello scambio insieme. Quando è pieno, il caricamento si ferma con un messaggio chiaro.",
        "Tut las datotecas dal barat ensemen. Sch’i è plain, chala il chargiar si cun in messadi cler."),
    "MoveEye never fills the storage: below this free space no upload is accepted (recordings and the system need room).": (
        "MoveEye füllt den Speicher nie ganz: unter diesem freien Platz wird nichts mehr angenommen (Aufnahmen und System brauchen Platz).",
        "MoveEye ne remplit jamais le support : en dessous de cet espace libre, aucun envoi n’est accepté (enregistrements et système ont besoin de place).",
        "MoveEye non riempie mai il supporto: sotto questo spazio libero non si accettano caricamenti (registrazioni e sistema hanno bisogno di spazio).",
        "MoveEye na emplenescha mai la memoria: sut quest spazi liber na vegn nagut acceptà (registraziuns e sistem dovran spazi)."),
    "Too big: at most {n} per file.": ("Zu gross: höchstens {n} pro Datei.", "Trop gros : au plus {n} par fichier.", "Troppo grande: al massimo {n} per file.",
                                       "Memia grond: al pli {n} per datoteca."),
    "Too many files (at most {n}) - delete old ones first.": (
        "Zu viele Dateien (höchstens {n}) – zuerst alte löschen.", "Trop de fichiers (au plus {n}) – supprime d’abord les anciens.",
        "Troppi file (al massimo {n}) – elimina prima quelli vecchi.", "Memia bleras datotecas (al pli {n}) – l’emprim stizzar las veglias."),
    "The file exchange is full: {a} of {b} used. Delete old files first.": (
        "Der Digitale Rucksack ist voll: {a} von {b} belegt. Zuerst alte Dateien löschen.", "Le sac à dos numérique est plein : {a} sur {b} utilisés. Supprime d’abord d’anciens fichiers.",
        "Lo zaino digitale è pieno: {a} di {b} occupati. Elimina prima file vecchi.", "Il satgados digital è plain: {a} da {b} occupà. L’emprim stizzar datotecas veglias."),
    "Your space is full: {a} of {b} used. Delete some of your files first.": (
        "Dein Platz ist voll: {a} von {b} belegt. Zuerst eigene Dateien löschen.", "Ta place est pleine : {a} sur {b} utilisés. Supprime d’abord certains de tes fichiers.",
        "Il tuo spazio è pieno: {a} di {b} occupati. Elimina prima alcuni tuoi file.", "Tes spazi è plain: {a} da {b} occupà. L’emprim stizzar atgnas datotecas."),
    "You may not upload files.": ("Du darfst keine Dateien hochladen.", "Tu ne peux pas envoyer de fichiers.", "Non puoi caricare file.", "Ti na dastas betg chargiar si datotecas."),
    "You may not download files.": ("Du darfst keine Dateien herunterladen.", "Tu ne peux pas télécharger de fichiers.", "Non puoi scaricare file.",
                                    "Ti na dastas betg telechargiar datotecas."),
    "You may not create folders.": ("Du darfst keine Ordner anlegen.", "Tu ne peux pas créer de dossiers.", "Non puoi creare cartelle.", "Ti na dastas betg crear ordinaturs."),
    "the file needs a name": ("die Datei braucht einen Namen", "le fichier a besoin d’un nom", "il file ha bisogno di un nome", "la datoteca dovra in num"),
    "the folder needs a name": ("der Ordner braucht einen Namen", "le dossier a besoin d’un nom", "la cartella ha bisogno di un nome", "l’ordinatur dovra in num"),
    "hidden files (name starts with «.») are not accepted": (
        "versteckte Dateien (Name beginnt mit «.») werden nicht angenommen", "les fichiers cachés (nom commençant par «.») ne sont pas acceptés",
        "i file nascosti (nome che inizia con «.») non sono accettati", "datotecas zuppadas (num cumenza cun «.») na vegnan betg acceptadas"),
    "Programs and scripts are not accepted (.{e}). Pack them into a ZIP if you really need to share them.": (
        "Programme und Skripte werden nicht angenommen (.{e}). Wenn es wirklich sein muss: in eine ZIP-Datei packen.",
        "Les programmes et scripts ne sont pas acceptés (.{e}). Si tu dois vraiment les partager : mets-les dans un ZIP.",
        "Programmi e script non sono accettati (.{e}). Se devi proprio condividerli: mettili in uno ZIP.",
        "Programs e scripts na vegnan betg acceptads (.{e}). Sch’i sto propi esser: als metter en in ZIP."),
    "This file is a program or script - not accepted.": ("Diese Datei ist ein Programm oder Skript – nicht angenommen.",
                                                         "Ce fichier est un programme ou un script – refusé.", "Questo file è un programma o uno script – non accettato.",
                                                         "Questa datoteca è in program u script – betg acceptada."),
    "unknown size": ("unbekannte Grösse", "taille inconnue", "dimensione sconosciuta", "grondezza nunenconuschenta"),
    "This folder does not exist (any more).": ("Diesen Ordner gibt es nicht (mehr).", "Ce dossier n’existe pas (plus).", "Questa cartella non esiste (più).",
                                               "Quest ordinatur n’exista betg (pli)."),
    "Too many uploads at the same time - wait until the others are done.": (
        "Zu viele Uploads gleichzeitig – warte, bis die anderen fertig sind.", "Trop d’envois en même temps – attends que les autres soient terminés.",
        "Troppi caricamenti contemporanei – aspetta che gli altri siano finiti.", "Memia blers chargiaments a medem temp – spetga fin ch’ils auters èn finids."),
    "Too many uploads in a short time - wait a few minutes.": (
        "Zu viele Uploads in kurzer Zeit – warte ein paar Minuten.", "Trop d’envois en peu de temps – attends quelques minutes.",
        "Troppi caricamenti in poco tempo – aspetta qualche minuto.", "Memia blers chargiaments en curt temp – spetga in pèr minutas."),
    "Too many downloads in a short time - wait a few minutes.": (
        "Zu viele Downloads in kurzer Zeit – warte ein paar Minuten.", "Trop de téléchargements en peu de temps – attends quelques minutes.",
        "Troppi download in poco tempo – aspetta qualche minuto.", "Memia blers downloads en curt temp – spetga in pèr minutas."),
    "Too many changes in a short time - wait a few minutes.": (
        "Zu viele Änderungen in kurzer Zeit – warte ein paar Minuten.", "Trop de modifications en peu de temps – attends quelques minutes.",
        "Troppe modifiche in poco tempo – aspetta qualche minuto.", "Memia bleras midadas en curt temp – spetga in pèr minutas."),
    "The storage cannot be written to.": ("Auf den Speicher kann nicht geschrieben werden.", "Impossible d’écrire sur le support.",
                                          "Impossibile scrivere sul supporto.", "I na po betg vegnir scrit sin la memoria."),
    "unknown upload": ("unbekannter Upload", "envoi inconnu", "caricamento sconosciuto", "chargiament nunenconuschent"),
    "The piece did not arrive completely.": ("Das Stück ist nicht ganz angekommen.", "Le morceau n’est pas arrivé en entier.", "Il pezzo non è arrivato per intero.",
                                             "Il toc n’è betg arrivà cumplettamain."),
    "piece too big": ("Stück zu gross", "morceau trop gros", "pezzo troppo grande", "toc memia grond"),
    "busy - try again": ("beschäftigt – nochmals versuchen", "occupé – réessaie", "occupato – riprova", "occupà – empruvar anc ina giada"),
    "more data than announced": ("mehr Daten als angekündigt", "plus de données qu’annoncé", "più dati di quelli annunciati", "dapli datas che annunzià"),
    "The upload is not complete yet.": ("Das Hochladen ist noch nicht fertig.", "L’envoi n’est pas encore terminé.", "Il caricamento non è ancora completo.",
                                        "Il chargiar si n’è anc betg finì."),
    "unknown file": ("unbekannte Datei", "fichier inconnu", "file sconosciuto", "datoteca nunenconuschenta"),
    "Only the person who uploaded it (or the administrator) may delete this file.": (
        "Nur wer die Datei hochgeladen hat (oder der Administrator), darf sie löschen.", "Seule la personne qui l’a envoyé (ou l’administrateur) peut supprimer ce fichier.",
        "Solo chi l’ha caricato (o l’amministratore) può eliminare questo file.", "Mo tgi che ha chargià si la datoteca (u l’administratur) dastga la stizzar."),
    "This folder exists already.": ("Diesen Ordner gibt es schon.", "Ce dossier existe déjà.", "Questa cartella esiste già.", "Quest ordinatur exista gia."),
    "At most {n} folders.": ("Höchstens {n} Ordner.", "Au plus {n} dossiers.", "Al massimo {n} cartelle.", "Al pli {n} ordinaturs."),
    "unknown folder": ("unbekannter Ordner", "dossier inconnu", "cartella sconosciuta", "ordinatur nunenconuschent"),
    "The folder is not empty - only the administrator can delete it with all files.": (
        "Der Ordner ist nicht leer – nur der Administrator kann ihn mit allen Dateien löschen.", "Le dossier n’est pas vide – seul l’administrateur peut le supprimer avec tous les fichiers.",
        "La cartella non è vuota – solo l’amministratore può eliminarla con tutti i file.", "L’ordinatur n’è betg vid – mo l’administratur al po stizzar cun tut las datotecas."),
    "Only the person who created it (or the administrator) may delete this folder.": (
        "Nur wer den Ordner angelegt hat (oder der Administrator), darf ihn löschen.", "Seule la personne qui l’a créé (ou l’administrateur) peut supprimer ce dossier.",
        "Solo chi l’ha creata (o l’amministratore) può eliminare questa cartella.", "Mo tgi che ha creà l’ordinatur (u l’administratur) dastga al stizzar."),
    "no preview for this file": ("keine Vorschau für diese Datei", "pas d’aperçu pour ce fichier", "nessuna anteprima per questo file", "nagina prevista per questa datoteca"),
    "{who} uploaded a file": ("{who} hat eine Datei hochgeladen", "{who} a envoyé un fichier", "{who} ha caricato un file", "{who} ha chargià si ina datoteca"),
    "New text": ("Neuer Text", "Nouveau texte", "Nuovo testo", "Nov text"),
    "New chat": ("Neuer Chat", "Nouveau chat", "Nuova chat", "Nov chat"),
    "Chats": ("Chats", "Chats", "Chat", "Chats"),
    "Chat": ("Chat", "Chat", "Chat", "Chat"),
    "Name of the new text (.txt or .md)": ("Name des neuen Texts (.txt oder .md)", "Nom du nouveau texte (.txt ou .md)", "Nome del nuovo testo (.txt o .md)",
                                           "Num dal nov text (.txt u .md)"),
    "Notes.txt": ("Notizen.txt", "Notes.txt", "Note.txt", "Notizias.txt"),
    "Name of the new chat": ("Name des neuen Chats", "Nom du nouveau chat", "Nome della nuova chat", "Num dal nov chat"),
    "not saved": ("nicht gespeichert", "pas enregistré", "non salvato", "betg memorisà"),
    "Version {v}": ("Version {v}", "Version {v}", "Versione {v}", "Versiun {v}"),
    "read only": ("nur lesen", "lecture seule", "solo lettura", "mo leger"),
    "Edit": ("Bearbeiten", "Modifier", "Modifica", "Modifitgar"),
    "Preview": ("Vorschau", "Aperçu", "Anteprima", "Prevista"),
    "Close without saving?": ("Ohne Speichern schliessen?", "Fermer sans enregistrer ?", "Chiudere senza salvare?", "Serrar senza memorisar?"),
    "Monospace": ("Feste Zeichenbreite", "Chasse fixe", "Spaziatura fissa", "Ladezza fixa"),
    "Versions": ("Versionen", "Versions", "Versioni", "Versiuns"),
    "Save": ("Speichern", "Enregistrer", "Salva", "Memorisar"),
    "Saved": ("Gespeichert", "Enregistré", "Salvato", "Memorisà"),
    "Meanwhile {who} has changed something.": ("Inzwischen hat {who} etwas geändert.", "Entre-temps, {who} a modifié quelque chose.",
                                               "Nel frattempo {who} ha modificato qualcosa.", "Entant ha {who} midà insatge."),
    "Your text is not saved yet. What now?": ("Dein Text ist noch nicht gespeichert. Was nun?", "Ton texte n’est pas encore enregistré. Que faire ?",
                                              "Il tuo testo non è ancora salvato. E adesso?", "Tes text n’è anc betg memorisà. E ussa?"),
    "Show the differences": ("Unterschiede ansehen", "Voir les différences", "Mostra le differenze", "Mussar las differenzas"),
    "Overwrite anyway": ("Trotzdem überschreiben", "Écraser quand même", "Sovrascrivi comunque", "Tuttina surscriver"),
    "Save mine as a copy": ("Meine als Kopie speichern", "Enregistrer la mienne comme copie", "Salva la mia come copia", "Memorisar mia sco copia"),
    "Too long for a comparison.": ("Zu lang für einen Vergleich.", "Trop long pour une comparaison.", "Troppo lungo per un confronto.", "Memia lung per ina cumparegliaziun."),
    "now on MoveEye": ("jetzt auf MoveEye", "maintenant sur MoveEye", "ora su MoveEye", "ussa sin MoveEye"),
    "yours": ("deine", "la tienne", "la tua", "tia"),
    "my version": ("meine Fassung", "ma version", "mia versione", "mia versiun"),
    "No older versions yet.": ("Noch keine älteren Versionen.", "Pas encore de versions plus anciennes.", "Ancora nessuna versione precedente.", "Anc naginas versiuns pli veglias."),
    "The last 20 versions are kept (they count in the space of the owner).": (
        "Die letzten 20 Versionen bleiben (sie zählen zum Platz des Besitzers).", "Les 20 dernières versions sont gardées (elles comptent dans la place du propriétaire).",
        "Le ultime 20 versioni restano (contano nello spazio del proprietario).", "Las ultimas 20 versiuns restan (ellas quintan tar il spazi dal possessur)."),
    "Restore": ("Wiederherstellen", "Restaurer", "Ripristina", "Restituir"),
    "Show": ("Ansehen", "Voir", "Mostra", "Mussar"),
    "Send": ("Senden", "Envoyer", "Invia", "Trametter"),
    "Message": ("Nachricht", "Message", "Messaggio", "Messadi"),
    "No messages yet.": ("Noch keine Nachrichten.", "Pas encore de messages.", "Ancora nessun messaggio.", "Anc nagins messadis."),
    "Write the first one below.": ("Schreib unten die erste.", "Écris le premier en bas.", "Scrivi il primo qui sotto.", "Scriva sutvart l’emprim."),
    "changed": ("geändert", "modifié", "modificato", "midà"),
    "Change": ("Ändern", "Modifier", "Modifica", "Midar"),
    "Change the message": ("Nachricht ändern", "Modifier le message", "Modifica il messaggio", "Midar il messadi"),
    "Delete": ("Löschen", "Supprimer", "Elimina", "Stizzar"),
    "Download": ("Herunterladen", "Télécharger", "Scarica", "Telechargiar"),
    "Delete this message?": ("Diese Nachricht löschen?", "Supprimer ce message ?", "Eliminare questo messaggio?", "Stizzar quest messadi?"),
    "Message deleted": ("Nachricht gelöscht", "Message supprimé", "Messaggio eliminato", "Messadi stizzà"),
    "Chats are made with «New chat».": ("Chats entstehen mit «Neuer Chat».", "Les chats se créent avec «Nouveau chat».", "Le chat si creano con «Nuova chat».",
                                       "Chats vegnan creads cun «Nov chat»."),
    "This is not a text file.": ("Das ist keine Textdatei.", "Ce n’est pas un fichier texte.", "Questo non è un file di testo.", "Quai n’è nagina datoteca da text."),
    "Too big for the editor (at most {n}) - download it instead.": (
        "Zu gross für den Editor (höchstens {n}) – bitte herunterladen.", "Trop gros pour l’éditeur (au plus {n}) – télécharge-le.",
        "Troppo grande per l’editor (al massimo {n}) – scaricalo.", "Memia grond per l’editur (al pli {n}) – al telechargiar."),
    "This version is not kept any more.": ("Diese Version gibt es nicht mehr.", "Cette version n’est plus conservée.", "Questa versione non è più conservata.",
                                           "Questa versiun n’exista betg pli."),
    "You may not change this text.": ("Du darfst diesen Text nicht ändern.", "Tu ne peux pas modifier ce texte.", "Non puoi modificare questo testo.",
                                      "Ti na dastas betg midar quest text."),
    "no text": ("kein Text", "pas de texte", "nessun testo", "nagin text"),
    "This is not a chat.": ("Das ist kein Chat.", "Ce n’est pas un chat.", "Questa non è una chat.", "Quai n’è nagin chat."),
    "You may not write in this chat.": ("Du darfst in diesem Chat nicht schreiben.", "Tu ne peux pas écrire dans ce chat.", "Non puoi scrivere in questa chat.",
                                        "Ti na dastas betg scriver en quest chat."),
    "The message is empty.": ("Die Nachricht ist leer.", "Le message est vide.", "Il messaggio è vuoto.", "Il messadi è vid."),
    "Too long: at most {n} per message.": ("Zu lang: höchstens {n} pro Nachricht.", "Trop long : au plus {n} par message.", "Troppo lungo: al massimo {n} per messaggio.",
                                           "Memia lung: al pli {n} per messadi."),
    "Too many messages in a short time - wait a moment.": ("Zu viele Nachrichten in kurzer Zeit – kurz warten.", "Trop de messages en peu de temps – attends un instant.",
                                                           "Troppi messaggi in poco tempo – aspetta un attimo.", "Memia blers messadis en curt temp – spetgar in mument."),
    "This chat is full - start a new one.": ("Dieser Chat ist voll – bitte einen neuen beginnen.", "Ce chat est plein – commence-en un nouveau.",
                                             "Questa chat è piena – iniziane una nuova.", "Quest chat è plain – cumenzar in nov."),
    "unknown message": ("unbekannte Nachricht", "message inconnu", "messaggio sconosciuto", "messadi nunenconuschent"),
    "Only your own messages, and only within 5 minutes.": ("Nur eigene Nachrichten und nur innert 5 Minuten.", "Seulement tes propres messages, et seulement dans les 5 minutes.",
                                                           "Solo i propri messaggi e solo entro 5 minuti.", "Mo atgns messadis e mo entaifer 5 minutas."),
    "{who} wrote in «{chat}»": ("{who} hat geschrieben in «{chat}»", "{who} a écrit dans «{chat}»", "{who} ha scritto in «{chat}»", "{who} ha scrit en «{chat}»"),
    "{who} wrote {n}× in «{chat}»": ("{who} hat {n}× geschrieben in «{chat}»", "{who} a écrit {n}× dans «{chat}»", "{who} ha scritto {n}× in «{chat}»",
                                     "{who} ha scrit {n}× en «{chat}»"),
    "{who} have written {n}× in «{chat}»": ("{who} haben {n}× geschrieben in «{chat}»", "{who} ont écrit {n}× dans «{chat}»", "{who} hanno scritto {n}× in «{chat}»",
                                            "{who} han scrit {n}× en «{chat}»"),
    "{who} uploaded {n} files": ("{who} hat {n} Dateien hochgeladen", "{who} a envoyé {n} fichiers", "{who} ha caricato {n} file", "{who} ha chargià si {n} datotecas"),
}
for _k, _v in _HX_TAUSCH.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_TZ_DE = {_k: _v[0] for _k, _v in _HX_TAUSCH.items()}

# ---- the manual (5 languages) ------------------------------------------------------------------------------------------------------
_HELP_TZ = {
    "de": ('<section id="tausch" data-icon="📁"><h2>Digitaler Rucksack</h2><p>Unter <i>Mehr → 📁 Digitaler Rucksack</i> (oder direkt <code>/tausch</code>) '
           'teilst du Fotos, Videos und Dokumente mit allen, die Zugang zu MoveEye haben.</p><ul>'
           '<li><b>📂 Für alle</b> sehen alle mit dem Recht «Dateien: ansehen»; wer hochladen darf, kann Ordner anlegen. <b>👤 Meine Dateien</b> sieht nur, wer sie hochgeladen hat (und der Administrator).</li>'
           '<li><b>Hochladen</b> mit dem Knopf oder Dateien auf die Seite ziehen. Grosse Dateien gehen in Stücken; bricht die Verbindung ab, wähle dieselbe Datei nochmals – es geht dort weiter.</li>'
           '<li><b>Rechte</b> (Einstellungen → Sicherheit → Benutzer): Familie darf ansehen, herunterladen und hochladen; Freund und «Nur ansehen» ansehen und herunterladen; Kind nichts. Bei «Eigene Rechte» einzeln ankreuzen.</li>'
           '<li><b>Gäste</b> mit dem Gast-Link sehen «Für alle» nur als Vorschaubilder – kein Download, kein Hochladen; endet mit dem Gast-Link.</li>'
           '<li><b>Grenzen</b> (Einstellungen → System → Digitaler Rucksack): gesamt 5 GB, 200 MB pro Datei, 1 GB pro Benutzer; auf dem Speicher bleiben immer 2 GB frei. Programme und Skripte werden abgelehnt.</li>'
           '<li><b>Speicher:</b> liegen die Aufnahmen auf einem USB-Stick / einer SSD, dann dort im Ordner <code>MotionWatch/tausch</code>, sonst auf der Speicherkarte. Die Dateien bleiben bei Updates und Werkseinstellungen; sie sind in <i>keiner</i> Sicherung.</li>'
           '<li>Lädt jemand Dateien hoch, bekommst du eine Push-Nachricht (gebündelt, nur Name und Anzahl).</li>'
           '<li><b>📝 Texte</b> (.txt, .md bis 1 MB) direkt im Browser bearbeiten (.md mit Vorschau). Hat inzwischen jemand anderes gespeichert, zeigt MoveEye «Inzwischen hat … etwas geändert» mit Unterschieden, Überschreiben oder «Meine als Kopie speichern». Die letzten 20 Versionen bleiben (🕘, Wiederherstellen).</li><li><b>💬 Chats</b> («Neuer Chat»): Nachrichten mit Name und Zeit, neue erscheinen bei allen von selbst. Eigene Nachrichten 5 Minuten lang ändern oder löschen. Wer im Chat geschrieben hat, bekommt eine Push-Nachricht («Anna hat 2× geschrieben in «Ferienplanung»») – ohne Inhalt.</li></ul></section>\n'),
    "en": ('<section id="tausch" data-icon="📁"><h2>Digital backpack</h2><p>Under <i>More → 📁 Digital backpack</i> (or directly <code>/tausch</code>) '
           'you share photos, videos and documents with everybody who has access to MoveEye.</p><ul>'
           '<li><b>📂 For everyone</b> is seen by all with the right «Files: see»; who may upload can create folders. <b>👤 My files</b> are only seen by the person who uploaded them (and the administrator).</li>'
           '<li><b>Upload</b> with the button or drag files onto the page. Big files go in pieces; if the connection breaks, choose the same file again – it continues.</li>'
           '<li><b>Rights</b> (Settings → Security → Users): family may see, download and upload; friend and «View only» see and download; child nothing. With «Own rights» tick them one by one.</li>'
           '<li><b>Guests</b> with the guest link see «For everyone» as previews only – no download, no upload; it ends with the guest link.</li>'
           '<li><b>Limits</b> (Settings → System → Digital backpack): 5 GB in total, 200 MB per file, 1 GB per user; 2 GB always stay free on the storage. Programs and scripts are refused.</li>'
           '<li><b>Storage:</b> when the recordings are on a USB stick / SSD, there in the folder <code>MotionWatch/tausch</code>, else on the memory card. The files stay through updates and factory settings; they are in <i>no</i> backup.</li>'
           '<li>When somebody uploads files you get a push message (bundled, only name and number).</li>'
           '<li><b>📝 Texts</b> (.txt, .md up to 1 MB) are edited right in the browser (.md with preview). If somebody else saved meanwhile, MoveEye says «Meanwhile … has changed something» with the differences, overwrite or «Save mine as a copy». The last 20 versions stay (🕘, restore).</li><li><b>💬 Chats</b> («New chat»): messages with name and time, new ones appear for everybody by themselves. Change or delete your own messages for 5 minutes. Who wrote in a chat gets a push message («Anna wrote 2× in «Holiday plan»») – without the content.</li></ul></section>\n'),
    "fr": ('<section id="tausch" data-icon="📁"><h2>Sac à dos numérique</h2><p>Sous <i>Plus → 📁 Sac à dos numérique</i> (ou <code>/tausch</code>) '
           'tu partages photos, vidéos et documents avec toutes les personnes ayant accès à MoveEye.</p><ul>'
           '<li><b>📂 Pour tous</b> : visible avec le droit «Fichiers : voir» ; qui peut envoyer peut créer des dossiers. <b>👤 Mes fichiers</b> : seulement pour la personne qui les a envoyés (et l’administrateur).</li>'
           '<li><b>Envoyer</b> avec le bouton ou en glissant des fichiers. Les gros fichiers partent en morceaux ; si la connexion coupe, choisis le même fichier – l’envoi reprend.</li>'
           '<li><b>Droits</b> (Réglages → Sécurité → Utilisateurs) : famille voir, télécharger et envoyer ; ami et «Seulement regarder» voir et télécharger ; enfant rien.</li>'
           '<li><b>Invités</b> avec le lien invité : «Pour tous» en aperçu seulement – ni téléchargement ni envoi.</li>'
           '<li><b>Limites</b> : 5 Go au total, 200 Mo par fichier, 1 Go par utilisateur ; 2 Go restent toujours libres. Programmes et scripts refusés.</li>'
           '<li><b>Stockage :</b> sur la clé USB / SSD des enregistrements (<code>MotionWatch/tausch</code>), sinon sur la carte mémoire ; dans aucune sauvegarde.</li>'
           '<li><b>📝 Textes</b> (.txt, .md) modifiables dans le navigateur, 20 versions gardées ; <b>💬 Chats</b> avec nom et heure, mis à jour tout seuls ; notification sans contenu.</li></ul></section>\n'),
    "it": ('<section id="tausch" data-icon="📁"><h2>Zaino digitale</h2><p>In <i>Altro → 📁 Zaino digitale</i> (o <code>/tausch</code>) '
           'condividi foto, video e documenti con tutti quelli che hanno accesso a MoveEye.</p><ul>'
           '<li><b>📂 Per tutti</b>: visibile con il diritto «File: vedere»; chi può caricare può creare cartelle. <b>👤 I miei file</b>: solo per chi li ha caricati (e l’amministratore).</li>'
           '<li><b>Caricare</b> con il pulsante o trascinando i file. I file grandi vanno a pezzi; se la connessione cade, scegli lo stesso file – riprende.</li>'
           '<li><b>Diritti</b> (Impostazioni → Sicurezza → Utenti): famiglia vedere, scaricare e caricare; amico e «Solo guardare» vedere e scaricare; bambino niente.</li>'
           '<li><b>Ospiti</b> con il link ospite: «Per tutti» solo come anteprima – né download né caricamento.</li>'
           '<li><b>Limiti</b>: 5 GB in totale, 200 MB per file, 1 GB per utente; 2 GB restano sempre liberi. Programmi e script rifiutati.</li>'
           '<li><b>Memoria:</b> sulla chiavetta USB / SSD delle registrazioni (<code>MotionWatch/tausch</code>), altrimenti sulla scheda; in nessun backup.</li>'
           '<li><b>📝 Testi</b> (.txt, .md) modificabili nel browser, 20 versioni conservate; <b>💬 Chat</b> con nome e ora, aggiornate da sole; notifica senza contenuto.</li></ul></section>\n'),
    "rm": ('<section id="tausch" data-icon="📁"><h2>Satgados digital</h2><p>Sut <i>Dapli → 📁 Satgados digital</i> (u <code>/tausch</code>) '
           'partas ti fotos, videos e documents cun tuts che han access a MoveEye.</p><ul>'
           '<li><b>📂 Per tuts</b>: visibel cun il dretg «Datotecas: guardar»; tgi che dastga chargiar si po crear ordinaturs. <b>👤 Mias datotecas</b>: mo per tgi che las ha chargià si (e l’administratur).</li>'
           '<li><b>Chargiar si</b> cun il buttun u trair datotecas sin la pagina. Datotecas grondas van en tocs; sche la colliaziun interrumpa, tscherna la medema datoteca – i cuntinuescha.</li>'
           '<li><b>Dretgs</b> (Configuraziuns → Segirezza → Utilisaders): famiglia guardar, telechargiar e chargiar si; ami e «Mo guardar» guardar e telechargiar; uffant nagut.</li>'
           '<li><b>Giasts</b> cun la colliaziun da giast: «Per tuts» mo sco prevista – nagin download, nagin chargiar si.</li>'
           '<li><b>Limitas</b>: 5 GB en total, 200 MB per datoteca, 1 GB per utilisader; 2 GB restan adina libers. Programs e scripts vegnan refusads.</li>'
           '<li><b>Memoria:</b> sin il stick USB / SSD da las registraziuns (<code>MotionWatch/tausch</code>), uschiglio sin la carta; en nagina copia da segirezza.</li>'
           '<li><b>📝 Texts</b> (.txt, .md) modifitgabels en il navigatur, 20 versiuns restan; <b>💬 Chats</b> cun num ed ura, actualisads da sasez; messadi senza cuntegn.</li></ul></section>\n'),
}


def _help_tz(doc, lang):
    if 'id="tausch"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_TZ[lang] + doc[i:] if i >= 0 else doc


_hp_en_tz = HELP_PAGE.find('<div lang="en">')
if _hp_en_tz > 0:
    HELP_PAGE = _help_tz(HELP_PAGE[:_hp_en_tz], "de") + _help_tz(HELP_PAGE[_hp_en_tz:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_tz(HELP_X[_L], _L)


# ---- self-test (without a server; werkzeuge/tausch_test.py tests the web side) ----------------------------------------------------
def tausch_selftest():
    keep = {k: CFG.get(k) for k in ("tausch_on", "tausch_push", "tausch_block_exec", "tausch_total_gb", "tausch_file_mb", "tausch_user_gb",
                                    "tausch_free_gb", "lang")}
    keepTZ = {k: TZ.get(k) for k in ("root", "files", "folders", "ups", "rate", "push", "root_test", "chats", "push_manual")}
    g = globals()
    sv = {k: g[k] for k in ("tausch_disk_free", "log_event", "tausch_thumb_queue", "tausch_push_send", "tausch_push_user", "tausch_push_ok")}
    tmp = tempfile.mkdtemp(prefix="mw_tz_")
    try:
        g["log_event"] = lambda *a, **k: None
        g["tausch_thumb_queue"] = lambda fid: None
        sent = []
        g["tausch_push_send"] = lambda txt, *a: sent.append(txt) or True
        g["tausch_push_user"] = lambda name, txt, *a: sent.append((name, txt)) or True
        g["tausch_push_ok"] = lambda: (True, False)
        TZ["push_manual"] = True
        free = {"n": 50 * TZ_GB}
        g["tausch_disk_free"] = lambda p: free["n"]
        CFG.update(tausch_on=True, tausch_push=True, tausch_block_exec=True, tausch_total_gb=5.0, tausch_file_mb=200.0, tausch_user_gb=1.0,
                   tausch_free_gb=2.0, lang="de")
        TZ.update(root=None, files=None, folders=None, ups={}, rate={}, push={}, root_test=tmp, chats={})
        # names
        assert tausch_clean_name("../../etc/passwd")[0] == "passwd" and tausch_clean_name("..\\..\\boot.ini")[0] == "boot.ini"
        assert tausch_clean_name(".bashrc")[0] is None and tausch_clean_name("..")[0] is None and tausch_clean_name("  ")[0] is None
        assert tausch_clean_name("Rechnung‮gpj.exe")[0] == "Rechnunggpj.exe" and tausch_blocked("Rechnunggpj.exe")
        assert tausch_clean_name("Café.jpg")[0] == "Café.jpg" and tausch_clean_name("CON.txt")[0] == "_CON.txt"
        assert tausch_clean_name('a<b>:c"d|e?f*.png')[0] == "a_b__c_d_e_f_.png" and len(tausch_clean_name("x" * 400 + ".jpg")[0]) == 120
        assert tausch_blocked("x.SH") and tausch_blocked("bild.jpg.exe") and not tausch_blocked("x.exe.txt") and tausch_type("a.svg")[2]
        assert tausch_magic_exec(b"MZ\x90\x00") and tausch_magic_exec(b"\x7fELF") and not tausch_magic_exec(b"\xff\xd8\xff")
        # rights per role
        P = lambda r: tausch_imply(ROLE_PERMS.get(r, ()))
        assert P("family") >= {"files_view", "files_down", "files_up"} and "files_admin" not in P("family")
        assert P("friend") & set(TZ_PERMS) == {"files_view", "files_down"} == P("view") & set(TZ_PERMS)
        assert not P("kid") & set(TZ_PERMS) and tausch_imply({"files_admin"}) == set(TZ_PERMS) and "files_view" in tausch_imply({"files_up"})
        assert role_allows("family", "/api/tausch", "POST", {}) and not role_allows("kid", "/tausch", "GET", {})
        assert role_allows("custom", "/tausch/dl/x", "GET", {}, user_perms({"role": "custom", "perms": ["files_down"]}))
        assert not role_allows("custom", "/tausch", "GET", {}, user_perms({"role": "custom", "perms": ["live"]}))
        # upload in pieces, quota, push bundle
        anna = {"key": "anna", "name": "Anna", "admin": False, "perms": P("family"), "is_admin": False}
        ok, err, r = tausch_up_start(anna, {"name": "Ferien.jpg", "size": 5, "area": "all"})
        assert ok, err
        assert tausch_up_chunk(anna, r["id"], 2, b"xx")[3] == 409, "a piece at the wrong place"
        assert tausch_up_chunk(anna, r["id"], 0, b"\xff\xd8\xff\xe0x")[0]
        ok, err, res = tausch_up_finish(anna, r["id"])
        assert ok and res["file"]["name"] == "Ferien.jpg" and sent == [], (err, sent)
        assert not tausch_up_start(anna, {"name": "gross.mp4", "size": 201 * TZ_MB, "area": "all"})[0]
        assert not tausch_up_start(anna, {"name": "x.mp4", "size": 1025 * TZ_MB, "area": "mine"})[0] or CFG["tausch_file_mb"] < 1025
        free["n"] = 2 * TZ_GB + 3
        assert "frei" in tausch_up_start(anna, {"name": "b.jpg", "size": 10, "area": "all"})[1], "keep 2 GB free"
        free["n"] = 50 * TZ_GB
        assert tausch_push_tick(time.time() + 200) == ["Anna hat eine Datei hochgeladen"], TZ["push"]
        tausch_push_note(anna, 2); tausch_push_note(anna)
        assert tausch_push_tick(time.time() + 200) == ["Anna hat 3 Dateien hochgeladen"]
        fid = res["file"]["id"]
        bob = {"key": "bob", "name": "Bob", "admin": False, "perms": P("friend"), "is_admin": False}
        assert not tausch_delete(bob, fid)[0] and tausch_delete(anna, fid)[0]
        # text: version check, history, restore
        ok, err, r = tausch_create(anna, {"name": "Plan.md", "area": "all", "text": "eins"}, "text")
        tid = r["file"]["id"]
        assert ok and r["file"]["kind"] == "text" and tausch_text_save(anna, tid, "zwei", 1)[0]
        ok, err, c = tausch_text_save(anna, tid, "drei", 1)
        assert not ok and c.get("conflict") and c["text"] == "zwei" and c["ver"] == 2, (err, c)
        assert not tausch_text_save(bob, tid, "x", 2)[0], "friend: no editing"
        assert tausch_text_save(anna, tid, None, 2, restore=1)[0] and tausch_text_get(anna, tid)[2]["text"] == "eins"
        # chat: append with name, rights, push to the others only
        ok, err, r = tausch_create(anna, {"name": "Ferienplanung", "area": "all"}, "chat")
        cid = r["file"]["id"]
        assert r["file"]["name"] == "Ferienplanung.chat" and tausch_chat_post(anna, cid, "Hallo <b>")[0]
        assert not tausch_chat_post(bob, cid, "hi")[0], "friend reads only"
        carl = dict(anna, key="carl", name="Carl")
        TZ["push"].clear()
        assert tausch_chat_post(carl, cid, "Ja")[0] and tausch_chat_post(carl, cid, "Gut")[0]
        assert tausch_push_tick(time.time() + 200) == ["Carl hat 2× geschrieben in «Ferienplanung»"], TZ["push"]
        j = tausch_chat_get(None, cid)[2]
        assert [p["x"] for p in j["posts"]] == ["Hallo <b>", "Ja", "Gut"] and "k" not in j["posts"][0]
    finally:
        CFG.update(keep); TZ.update(keepTZ); g.update(sv)
        shutil.rmtree(tmp, ignore_errors=True)
    return "names, programs, rights per role, pieces, limits, 2 GB free, push «Anna hat 3 Dateien hochgeladen», delete rules, text versions, chat"


SELFTEST_EXTRA.append(("Digital backpack (files): names, rights, limits, pieces, push (639zzc)", tausch_selftest))
