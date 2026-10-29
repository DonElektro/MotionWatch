#@ Motion Watch – Teil 040: Einstellungen speichern, Web-Passwort. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Settings persistence (autosaved 2 s after any change)
# ----------------------------------------------------------------------------
VOLATILE = {"web_stream", "web_password", "rain_mode", "fullscreen"}   # never restored from disk
_save_timer = None


WEB_UI_KEY = re.compile(r"^mw-[A-Za-z0-9_:\-./ ]{1,90}$")
WEB_UI_LOCAL = {"mw-sound", "mw-hdr", "mw-listen-vol"}                      # per device on purpose (sound on the phone, not on the PC)


# ---- web password set on the page / in the window: stored as a salted PBKDF2 hash; checked passwords are remembered
#      (as a keyed digest, only in memory) so the Pi does not have to compute the slow hash for every picture of the stream
_PW_KEY = os.urandom(32)
_PW_OK = set()


def pw_hash(pw):
    import hashlib
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200000)
    return f"pbkdf2${200000}${salt.hex()}${h.hex()}"


def pw_check(pw, stored=None):
    import hashlib
    stored = (CFG.get("web_pw_hash") or "") if stored is None else stored
    key = hmac.new(_PW_KEY, (stored + "|" + str(pw)).encode(), "sha256").digest()
    if key in _PW_OK:
        return True
    try:
        _alg, it, salt, h = stored.split("$")
        ok = hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", str(pw).encode(), bytes.fromhex(salt), int(it)).hex(), h)
    except (ValueError, TypeError):
        return False
    if ok:
        if len(_PW_OK) > 50:
            _PW_OK.clear()
        _PW_OK.add(key)
    return ok


USER_ROLES = ("operate", "view")
_USER_RE = re.compile(r"^[A-Za-z0-9ÄÖÜäöüéèàç][A-Za-z0-9ÄÖÜäöüéèàç ._\-]{0,23}$")
# what an "operate" user may change (everything else is read-only); "view" may only look
OPERATE_POST = {"/api/follow", "/api/tunnel", "/api/disco", "/api/helper", "/api/info", "/api/nettest", "/api/tv", "/api/mode", "/api/mover", "/api/arm", "/api/night", "/api/camping", "/api/quick", "/api/light", "/api/move", "/api/stick", "/api/talk",
                "/api/talk/stop", "/api/tts", "/api/rec/fav", "/api/rec/false", "/api/action"}
VIEW_POST = {"/api/webpush", "/api/time", "/api/gps", "/api/rec/prepare", "/rec/zip"}
OPERATE_SET_KEYS = {"thermal_on", "nightvision", "show_objects", "show_mask", "track_person", "track_motion"}
ADMIN_GET = ("/api/settings/export", "/api/ext", "/api/wifi", "/api/qr", "/setup-card", "/api/update", "/api/guest", "/api/fleet",
             "/api/users", "/api/setup", "/api/log/file/", "/api/tools", "/tools/diag.zip", "/api/usb")


def users_clean(lst):
    out, seen = [], set()
    for u in (lst if isinstance(lst, list) else [])[:20]:
        if not isinstance(u, dict):
            continue
        n = str(u.get("name", "")).strip()
        if not _USER_RE.match(n) or n.lower() in seen or not str(u.get("hash", "")).startswith("pbkdf2$"):
            continue
        seen.add(n.lower())
        out.append({"name": n, "hash": u["hash"], "role": u.get("role") if u.get("role") in USER_ROLES else "view"})
    return out


def user_login(name, pw):
    """(name, role) for a web login, or None. The web password = administrator (any user name)."""
    if CFG["web_password"]:
        if hmac.compare_digest(str(pw).encode(), str(CFG["web_password"]).encode()):
            return (name or "admin", "admin")
    elif CFG["web_pw_hash"] and pw_check(pw):
        return (name or "admin", "admin")
    for u in CFG["users"]:
        if u["name"].lower() == str(name or "").strip().lower() and pw_check(pw, u["hash"]):
            return (u["name"], u["role"])
    return None


TRUST_COOKIE = "mw_trust"


def _trust_hash(tok):
    import hashlib
    return hashlib.sha256(("mw-trust|" + str(tok)).encode()).hexdigest()


def trust_find(tok):
    """the trusted device of this cookie: (user, role) or None. The user must still exist (the administrator always does)."""
    if not tok or len(tok) < 20 or len(tok) > 100:
        return None
    h = _trust_hash(tok)
    for e in CFG.get("trusted") or []:
        if hmac.compare_digest(e.get("h", ""), h):
            u = e.get("user", "admin")
            if e.get("role", "admin") == "admin":
                return (u, "admin"), e
            for x in CFG["users"]:
                if x["name"].lower() == u.lower():
                    return (x["name"], x["role"]), e
            return None
    return None


def trust_add(user, role, ua, ip):
    """a new trusted device: returns the cookie value (only its hash is kept here)"""
    import secrets
    tok = secrets.token_urlsafe(32)
    name = "Gerät"
    for k, n in (("iPad", "iPad"), ("iPhone", "iPhone"), ("Android", "Android"), ("Macintosh", "Mac"), ("Windows", "Windows-PC"), ("Linux", "Linux")):
        if k in ua:
            name = n
            break
    for k, n in (("Edg/", "Edge"), ("Firefox", "Firefox"), ("Chrome", "Chrome"), ("Safari", "Safari")):
        if k in ua:
            name += " · " + n
            break
    lst = [e for e in (CFG.get("trusted") or [])][-29:]
    lst.append({"h": _trust_hash(tok), "user": user, "role": "admin" if role == "admin" else "user", "name": name, "t0": int(time.time()),
                "seen": int(time.time()), "ip": str(ip)[:45]})
    CFG["trusted"] = lst
    save_settings()
    log_event("web", f"Trusted device added: {name} ({user}, {ip})")
    return tok


def users_action(d, who="admin"):
    a = d.get("action")
    if a == "add":
        if not web_pw_active():
            return False, "set the web password first (it is the administrator)"
        n = str(d.get("name", "")).strip(); pw = str(d.get("password", ""))
        if not _USER_RE.match(n):
            return False, "name: 1 to 24 letters / digits"
        if any(u["name"].lower() == n.lower() for u in CFG["users"]):
            return False, "this name exists already"
        if not (6 <= len(pw) <= 64 and all(32 <= ord(c) < 127 for c in pw)):
            return False, "the password must have 6 to 64 characters (letters, digits, signs, no umlauts)"
        if len(CFG["users"]) >= 20:
            return False, "at most 20 users"
        CFG["users"] = users_clean(CFG["users"] + [{"name": n, "hash": pw_hash(pw), "role": d.get("role") if d.get("role") in USER_ROLES else "view"}])
        log_event("web", f"{who}: user «{n}» added ({CFG['users'][-1]['role']})")
    else:
        u = next((x for x in CFG["users"] if x["name"] == d.get("name")), None)
        if u is None:
            return False, "unknown user"
        if a == "remove":
            CFG["users"] = [x for x in CFG["users"] if x is not u]; log_event("web", f"{who}: user «{u['name']}» removed")
        elif a == "role" and d.get("role") in USER_ROLES:
            u["role"] = d["role"]; log_event("web", f"{who}: user «{u['name']}» now {u['role']}")
        elif a == "password":
            pw = str(d.get("password", ""))
            if not (6 <= len(pw) <= 64 and all(32 <= ord(c) < 127 for c in pw)):
                return False, "the password must have 6 to 64 characters (letters, digits, signs, no umlauts)"
            u["hash"] = pw_hash(pw); log_event("web", f"{who}: new password for «{u['name']}»")
        else:
            return False, "unknown action"
        CFG["trusted"] = [e for e in (CFG.get("trusted") or []) if e.get("user") != u["name"]]   # 2.95.33: log in again
    _PW_OK.clear(); save_settings_now()
    return True, ""


# 2.95.35: ONE list of what users without admin rights may read. Everything else (also every new function) is only for
# the administrator. Changing things (POST): VIEW_POST for everybody, OPERATE_POST (+ the keys below) for «operate».
VIEW_GET_PAGES = {"/", "/cams", "/recordings", "/diary", "/help", "/quick", "/preview", "/zones", "/kino"}
VIEW_GET = ("/api/tunnel", "/api/dataset.zip", "/api/helper", "/api/info", "/api/nettest", "/api/state", "/api/alerts", "/api/appearance", "/api/version", "/api/health", "/api/cams", "/api/frame.jpg",
            "/video_feed", "/cam_feed/", "/snapshot.jpg", "/api/audio/live", "/api/recordings", "/api/places", "/rec/file/",
            "/rec/play/", "/rec/thumb/", "/rec/share/", "/rec/report/", "/api/day", "/api/diary", "/diary/img/", "/api/timelapse",
            "/timelapse/", "/api/species", "/api/loop", "/api/gps", "/api/zones", "/api/webpush", "/api/ui", "/api/report",
            "/api/battery", "/api/sensors", "/api/qs", "/api/schedule", "/api/schema", "/api/triggers", "/api/fa", "/api/appicon",
            "/api/audio", "/i18n/", "/app-icon/", "/sim-icon/", "/sim/view.jpg", "/sim/view.mjpg", "/api/kino", "/api/simbar", "/api/news")


def role_allows(role, path, method, d):
    if role == "admin":
        return True
    if method in ("GET", "HEAD"):
        return (path in VIEW_GET_PAGES or path.startswith(VIEW_GET)) and not path.startswith(ADMIN_GET)
    if path == "/api/webpush":
        return d.get("action") in ("subscribe", "unsubscribe", "key", None)
    if path in VIEW_POST:
        return True
    if role != "operate":
        return False
    if path == "/api/set":
        return d.get("key") in OPERATE_SET_KEYS
    if path == "/api/audio":
        return d.get("action") in ("test", "siren", "stop")
    if path == "/api/action":
        return d.get("action") in ("center", "patrol")
    return path in OPERATE_POST


def web_pw_active():
    return bool(CFG["web_password"] or CFG["web_pw_hash"])


def web_pw_set(pw):
    """pw = "" removes the password. A password given on the command line (--web-password) always wins."""
    if CFG["web_password"]:
        return False, "the password was given on the command line (--web-password) - change it there"
    pw = str(pw or "")
    if pw and not (6 <= len(pw) <= 64 and all(32 <= ord(c) < 127 for c in pw)):
        return False, "the password must have 6 to 64 characters (letters, digits, signs, no umlauts)"
    CFG["web_pw_hash"] = pw_hash(pw) if pw else ""
    _PW_OK.clear()
    CFG["trusted"] = []                                    # a new password: every device logs in again
    save_settings_now()
    log_event("web", "Web password set" if pw else "Web password removed")
    return True, ""


def clean_web_ui(d):
    out = {}
    if isinstance(d, dict):
        for k, v in list(d.items())[:400]:
            if isinstance(k, str) and WEB_UI_KEY.match(k) and k not in WEB_UI_LOCAL and isinstance(v, str) and len(v) <= 4000:
                out[k] = v
    return out


def web_ui_update(changes, removes=()):
    if not isinstance(changes, dict):
        return False
    cur = dict(CFG["web_ui"])
    cur.update(clean_web_ui(changes))
    for k in (removes if isinstance(removes, list) else []):
        cur.pop(k, None)
    CFG["web_ui"] = clean_web_ui(cur)                # re-assign: DEFAULTS share the old dict
    save_settings()
    return True


def settings_status_text(lang=None):
    """The settings line (saved / loaded / defaults) in the language of the page / window."""
    st = str(STATE.get("settings_status", ""))
    m = re.match(r"^saved (\S+)$", st)
    if m:
        return trf("saved {t}", lang, t=m.group(1))
    m = re.match(r"^loaded (\d+) settings, (\d+) waypoints, (\d+) relays, (\d+) schedules$", st)
    if m:
        return trf("loaded: {a} settings, {b} waypoints, {c} relays, {d} schedules", lang, a=m.group(1), b=m.group(2), c=m.group(3), d=m.group(4))
    if st.startswith("save failed: "):
        return tr("save failed", lang) + ": " + st[13:]
    return tr(st, lang)


def _read_settings_file(p):
    with open(p) as f:
        d = json.load(f)
    if not isinstance(d, dict) or not isinstance(d.get("cfg", {}), dict):
        raise ValueError("not a settings object")
    return d


def load_settings():
    """2.95.33: a broken file (power cut while saving) is kept as .bad and the backup copy of the last good settings is
    used instead - otherwise password, users and messages would silently fall back to the defaults."""
    try:
        data = _read_settings_file(SETTINGS_FILE)
    except OSError:
        STATE["settings_status"] = "defaults (no file yet)"
        return
    except ValueError:
        bad = SETTINGS_FILE + ".bad-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        try:
            shutil.copy2(SETTINGS_FILE, bad)
        except OSError:
            pass
        try:
            data = _read_settings_file(os.path.join(DATA_DIR, "motionwatch_settings.backup.json"))
            STATE["settings_restored"] = bad; STATE["settings_from_backup"] = True
        except (OSError, ValueError):
            STATE["settings_status"] = "defaults (settings file damaged, no usable backup)"
            STATE["settings_restored"] = bad; STATE["settings_from_backup"] = False
            return
    apply_settings(data)
    if STATE.get("settings_from_backup"):
        STATE["settings_status"] = "restored from the backup copy (the settings file was damaged)"
    if isinstance(data, dict) and isinstance(data.get("cfg"), dict) and "setup_done" not in data["cfg"]:
        CFG["setup_done"] = True                     # settings from an earlier version: already set up


def settings_data():
    """Everything that is saved (also used for "export settings")."""
    return {"cfg": {k: SCHED["base"].get(k, v) for k, v in CFG.items() if k not in VOLATILE}, "waypoints": list(WAYPOINTS),
            "relays": [dict(r) for r in RELAYS], "schedules": [dict(x) for x in SCHEDULES], "zones": [dict(z) for z in ZONES],
            "saved": datetime.now().isoformat(timespec="seconds")}


SETTINGS_GEN = {"n": 0}                  # +1 after an import: the window rebuilds itself


def import_settings(data):
    """Settings from an exported file. The current file is kept as motionwatch_settings.before_import.json."""
    if not isinstance(data, dict) or not isinstance(data.get("cfg"), dict):
        return False, "not a MoveEye settings file"
    try:
        shutil.copy2(SETTINGS_FILE, os.path.join(DATA_DIR, "motionwatch_settings.before_import.json"))
    except OSError:
        pass
    data = dict(data); data["cfg"] = {k: v for k, v in data["cfg"].items() if k not in ("record_dir",)}   # 2.95.34
    apply_settings(data)
    save_settings_now()
    HW_REINIT["want"] = True; _PW_OK.clear(); SETTINGS_GEN["n"] += 1
    log_event("sys", "Settings imported (the previous ones are in motionwatch_settings.before_import.json)")
    return True, ""


def apply_settings(data):
    """the loaded / imported settings into CFG (values checked), then the migrations of older files (131, 577)"""
    n = 0
    if not isinstance(data, dict):
        _settings_migrations(None)
        return
    try:
        specs = web_specs()
    except Exception:
        specs = {}
    cfg_in = data.get("cfg", {}) if isinstance(data.get("cfg", {}), dict) else {}
    for k, v in cfg_in.items():
        if k not in CFG or k in VOLATILE:
            continue
        if isinstance(v, type(CFG[k])) or (isinstance(CFG[k], float) and isinstance(v, int) and not isinstance(v, bool)):
            v = type(CFG[k])(v)
            sp = specs.get(k) or {}
            if isinstance(v, (int, float)) and not isinstance(v, bool) and sp.get("type") != "bool":
                if isinstance(v, float) and not math.isfinite(v):
                    continue
                if "min" in sp:
                    v = type(CFG[k])(max(sp["min"], v))
                if "max" in sp:
                    v = type(CFG[k])(min(sp["max"], v))
            CFG[k] = v; n += 1
    wps = []
    for w in data.get("waypoints", []):
        if isinstance(w, (int, float)) and not isinstance(w, bool):        # old files: pan only
            wps.append([float(w), float(CFG["patrol_tilt"])])
        elif isinstance(w, (list, tuple)) and len(w) == 2 and all(isinstance(x, (int, float)) for x in w):
            wps.append([max(0.0, min(100.0, float(w[0]))), max(0.0, min(100.0, float(w[1])))])
    WAYPOINTS[:] = wps[:50]
    CFG["ui_hidden"] = [k for k in CFG["ui_hidden"] if isinstance(k, str)][:200]
    CFG["ui_open"] = [k for k in CFG["ui_open"] if isinstance(k, str)][:100]
    _ql = CFG["qs_layout"] if isinstance(CFG["qs_layout"], dict) else {}
    CFG["qs_layout"] = {"order": [k for k in (_ql.get("order") or []) if isinstance(k, str)][:60], "hidden": [k for k in (_ql.get("hidden") or []) if isinstance(k, str)][:60]}
    CFG["web_ui"] = clean_web_ui(CFG["web_ui"])
    if not CFG.get("dev_phase_done"):                  # 2.96.2: Daniel is in the development phase - fast updates on (once)
        CFG["dev_phase_done"] = True
        CFG["update_fast"] = True
    if not CFG.get("app_icon_moveeye_done"):          # 2.96.0: the new name MoveEye and its symbol for everybody (once)
        CFG["app_icon_moveeye_done"] = True
        CFG["app_icon_orange_done"] = True
        CFG["app_icon"] = "moveeye"
    if not CFG.get("app_icon_orange_done"):            # 2.95.100: Daniel wants the orange MoveEye symbol everywhere (once)
        CFG["app_icon_orange_done"] = True
        if CFG.get("app_icon") in ("radar", "", None):
            CFG["app_icon"] = "classic"
    rl = data.get("relays")
    if isinstance(rl, list):
        used, out = set(), []
        for r in rl[:MAX_RELAYS]:
            if isinstance(r, dict):
                c = _clean_relay(r, len(out), used)
                if c:
                    out.append(c); used.add(c["gpio"])
        RELAYS[:] = out
    else:                                    # settings file from 1.2.2 -> migrate the single relay
        old = data.get("cfg", {}); r0 = default_relays()[0]
        if old.get("relay_on_person") is False:
            r0["mode"] = "off"
        if isinstance(old.get("relay_hold"), (int, float)) and not isinstance(old.get("relay_hold"), bool):
            r0["hold"] = max(0.5, min(600.0, float(old["relay_hold"])))
        RELAYS[:] = [r0]
    sc = data.get("schedules")
    if isinstance(sc, list):
        out = []
        for x in sc[:MAX_SCHEDULES]:
            c = _clean_schedule(x, len(out))
            if c:
                out.append(c)
        SCHEDULES[:] = out
    zl = data.get("zones")
    if isinstance(zl, list):
        ZONES[:] = [z for z in (_clean_zone(x, i) for i, x in enumerate(zl[:MAX_ZONES])) if z]
    CFG["presence_hosts"] = [h for h in CFG["presence_hosts"] if isinstance(h, str) and _HOST_RE.match(h)][:8]
    CFG["extra_cams"] = [x for x in CFG["extra_cams"] if isinstance(x, str) and SRC_RE.match(x) and x != "auto"][:MAX_EXTRA]
    CFG["fleet"] = [d for d in CFG["fleet"] if isinstance(d, dict) and isinstance(d.get("url"), str) and _FLEET_URL.match(d["url"])
                    and isinstance(d.get("id"), str)][:12]
    if CFG["notify_type"] not in NOTIFY_TYPES:
        CFG["notify_type"] = "webhook"
    CFG["ip_sources"] = _clean_ip_sources(CFG["ip_sources"])
    CFG["sensors"] = sens_clean(CFG["sensors"])
    CFG["users"] = users_clean(CFG["users"])
    if not SRC_RE.match(str(CFG["source"])):
        CFG["source"] = "auto"
    STATE["settings_status"] = f"loaded {n} settings, {len(WAYPOINTS)} waypoints, {len(RELAYS)} relays, {len(SCHEDULES)} schedules"
    log_event("sys", f"Settings loaded from {SETTINGS_FILE} ({n} values, {len(WAYPOINTS)} waypoints, {len(RELAYS)} relays, {len(SCHEDULES)} schedules)")
    _settings_migrations(data.get("cfg"))


def _settings_migrations(cfg_in):
    """settings of older versions: modes / profiles (2.98.14, concept_migrate in 131), weekly report and return of the phone
    (2.98.15, nachlauf_migrate in 577). A failing migration never stops the loading."""
    try:
        concept_migrate()
    except Exception as e:
        log_event("sys", f"Settings migration: {e}"[:150])
    try:
        did = nachlauf_migrate(cfg_in)
        if did:
            log_event("sys", "Settings of an older version taken over: " + "; ".join(did))
    except Exception as e:
        log_event("sys", f"Settings migration (577): {e}"[:150])


_SAVE_LOCK = threading.Lock()


def save_settings_now():
    """Atomic: own temp file, flushed to the card (fsync) before it replaces the old one; one save at a time."""
    with _SAVE_LOCK:
        tmp = f"{SETTINGS_FILE}.{os.getpid()}.{threading.get_ident()}.tmp"
        try:
            txt = json.dumps(settings_data(), indent=1)
            with open(tmp, "w") as f:
                f.write(txt); f.flush(); os.fsync(f.fileno())
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
            os.replace(tmp, SETTINGS_FILE)
            try:
                dfd = os.open(os.path.dirname(os.path.abspath(SETTINGS_FILE)), os.O_RDONLY)
                try:
                    os.fsync(dfd)
                finally:
                    os.close(dfd)
            except OSError:
                pass
            STATE["settings_status"] = "saved " + datetime.now().strftime("%H:%M:%S")
        except Exception as e:                          # also TypeError / RuntimeError: must not vanish in a thread
            STATE["settings_status"] = f"save failed: {e}"[:200]
            try:
                os.remove(tmp)
            except OSError:
                pass


_SAVE_T = {"last": 0.0}


def save_settings():
    """Debounced: many slider moves -> one write. 2.98.13 (memory card): at most one write every 15 s - something that
    saves again and again (a counter, a slider held down) no longer writes the card every 2 s."""
    global _save_timer
    if _save_timer:
        _save_timer.cancel()
    wait = max(2.0, 15.0 - (time.monotonic() - _SAVE_T["last"]))

    def go():
        _SAVE_T["last"] = time.monotonic()
        save_settings_now()
    _save_timer = threading.Timer(wait, go); _save_timer.daemon = True; _save_timer.start()


def reset_settings():
    for k, v in DEFAULTS.items():
        if k not in VOLATILE and k not in ("pan", "tilt", "source", "ip_sources", "extra_cams", "latitude", "longitude",
                                           "presence_hosts", "telegram_token", "telegram_chat", "public_url", "notify_url", "notify_type",
                                           "pushover_user", "pushover_token", "email_to", "email_host", "email_port", "email_user",
                                           "email_password", "email_from", "shortcut_token",
                                           "web_ui", "ui_open", "ui_hidden", "theme", "lang"):
            CFG[k] = v
    WAYPOINTS.clear()
    RELAYS[:] = default_relays()
    ZONES.clear(); SCHEDULES.clear(); SCHED["base"].clear(); SCHED["manual"].clear(); SCHED["last"] = {}; SCHED["active"] = []
    save_settings_now()
    log_event("sys", "Settings reset to defaults")


