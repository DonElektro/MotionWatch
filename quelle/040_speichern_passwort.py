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


# 2.98.42 (Daniel): roles = presets of rights; «custom» = own choice of rights. Old roles: «operate» → «family», «view» stays.
USER_ROLES = ("kid", "friend", "family", "view", "custom")
USER_PERMS = ("live", "rec", "arm", "light", "siren", "games", "talk", "head", "settings")
ROLE_PERMS = {"kid": ("live", "games"), "friend": ("live", "games", "talk", "light"),
              "family": ("live", "rec", "arm", "light", "siren", "games", "talk", "head"), "view": ("live", "rec")}
ROLE_OLD = {"operate": "family"}
USER_PUSH = ("alarm", "info", "games")                # what a user may get as push message
ROLE_PUSH = {"kid": ("games",), "friend": ("info", "games")}      # children get no alarms unless the administrator says so
_USER_RE = re.compile(r"^[A-Za-z0-9ÄÖÜäöüéèàç][A-Za-z0-9ÄÖÜäöüéèàç ._\-]{0,23}$")
_USER_HM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_USER_DAY = re.compile(r"^20\d\d-[01]\d-[0-3]\d$")
_USER_NTFY = re.compile(r"^(https://[A-Za-z0-9.\-]+(:\d+)?/)?[A-Za-z0-9_\-]{6,64}$")
ADMIN_GET = ("/api/settings/export", "/api/ext", "/api/wifi", "/api/qr", "/setup-card", "/api/update", "/api/guest", "/api/fleet",
             "/api/users", "/api/setup", "/api/log/file/", "/api/tools", "/tools/diag.zip", "/api/usb")


def user_perms(u):
    """the rights of a user (dict from CFG["users"]) as a set"""
    if not isinstance(u, dict):
        return set()
    if u.get("role") == "custom":
        return {p for p in (u.get("perms") or []) if p in USER_PERMS}
    return set(ROLE_PERMS.get(u.get("role"), ()))


def user_get(name):
    n = str(name or "").strip().lower()
    return next((u for u in CFG["users"] if u["name"].lower() == n), None) if n else None


def users_clean(lst):
    out, seen = [], set()
    for u in (lst if isinstance(lst, list) else [])[:20]:
        if not isinstance(u, dict):
            continue
        n = str(u.get("name", "")).strip()
        if not _USER_RE.match(n) or n.lower() in seen or not str(u.get("hash", "")).startswith("pbkdf2$"):
            continue
        seen.add(n.lower())
        r = ROLE_OLD.get(u.get("role"), u.get("role"))
        r = r if r in USER_ROLES else "view"
        e = {"name": n, "hash": u["hash"], "role": r}
        if r == "custom":
            e["perms"] = [p for p in USER_PERMS if p in (u.get("perms") or [])]
        w = u.get("win") if isinstance(u.get("win"), dict) else None
        if w and _USER_HM.match(str(w.get("from", ""))) and _USER_HM.match(str(w.get("to", ""))):
            days = sorted({int(x) for x in (w.get("days") or []) if isinstance(x, int) and 0 <= x <= 6}) or list(range(7))
            e["win"] = {"from": w["from"], "to": w["to"], "days": days}
        if _USER_DAY.match(str(u.get("until") or "")):
            e["until"] = u["until"]
        e["push"] = [p for p in USER_PUSH if p in u["push"]] if isinstance(u.get("push"), list) else list(ROLE_PUSH.get(r, USER_PUSH))
        if _USER_NTFY.match(str(u.get("ntfy") or "")):
            e["ntfy"] = u["ntfy"]
        if u.get("nopw"):
            e["nopw"] = True                              # no own password (only phones linked with a QR code)
        out.append(e)
    return out


def user_login(name, pw):
    """(name, role) for a web login, or None. The web password = administrator (any user name)."""
    if CFG["web_password"]:
        if hmac.compare_digest(str(pw).encode(), str(CFG["web_password"]).encode()):
            return (name or "admin", "admin")
    elif CFG["web_pw_hash"] and pw_check(pw):
        return (name or "admin", "admin")
    for u in CFG["users"]:
        if u["name"].lower() == str(name or "").strip().lower() and not u.get("nopw") and pw_check(pw, u["hash"]):
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


def trust_add(user, role, ua, ip, via=""):
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
    lst = [e for e in (CFG.get("trusted") or [])][-59:]
    lst.append({"h": _trust_hash(tok), "user": user, "role": "admin" if role == "admin" else "user", "name": name, "t0": int(time.time()),
                "seen": int(time.time()), "ip": str(ip)[:45]})
    if via:
        lst[-1]["via"] = via                                # «link» = linked with the QR code of the administrator (041)
    CFG["trusted"] = lst
    save_settings()
    log_event("web", f"Trusted device added: {name} ({user}, {ip})")
    return tok


def _user_pw_ok(pw):
    return 6 <= len(pw) <= 64 and all(32 <= ord(c) < 127 for c in pw)


def users_action(d, who="admin"):
    """add / remove / role / password / update (rights, time window, expiry, push) - web (550/041) and window (573)"""
    import secrets
    a = d.get("action")
    if a == "add":
        if not web_pw_active():
            return False, "set the web password first (it is the administrator)"
        n = str(d.get("name", "")).strip(); pw = str(d.get("password", ""))
        if not _USER_RE.match(n):
            return False, "name: 1 to 24 letters / digits"
        if any(u["name"].lower() == n.lower() for u in CFG["users"]):
            return False, "this name exists already"
        if pw and not _user_pw_ok(pw):
            return False, "the password must have 6 to 64 characters (letters, digits, signs, no umlauts)"
        if len(CFG["users"]) >= 20:
            return False, "at most 20 users"
        r = ROLE_OLD.get(d.get("role"), d.get("role"))
        e = {"name": n, "hash": pw_hash(pw or secrets.token_urlsafe(24)), "role": r if r in USER_ROLES else "view", "perms": d.get("perms") or []}
        if not pw:
            e["nopw"] = True
        CFG["users"] = users_clean(CFG["users"] + [e])
        log_event("web", f"{who}: user «{n}» added ({CFG['users'][-1]['role']})")
    else:
        u = next((x for x in CFG["users"] if x["name"] == d.get("name")), None)
        if u is None:
            return False, "unknown user"
        logout = True
        if a == "remove":
            CFG["users"] = [x for x in CFG["users"] if x is not u]; log_event("web", f"{who}: user «{u['name']}» removed")
            users_push_forget(u["name"])                    # its browsers get no messages any more (041)
        elif a == "role" and ROLE_OLD.get(d.get("role"), d.get("role")) in USER_ROLES:
            u["role"] = ROLE_OLD.get(d["role"], d["role"]); logout = False; log_event("web", f"{who}: user «{u['name']}» now {u['role']}")
        elif a == "password":
            pw = str(d.get("password", ""))
            if not _user_pw_ok(pw):
                return False, "the password must have 6 to 64 characters (letters, digits, signs, no umlauts)"
            u["hash"] = pw_hash(pw); u.pop("nopw", None); log_event("web", f"{who}: new password for «{u['name']}»")
        elif a == "update":                                 # 2.98.42: rights, time window, expiry, push - the phones stay logged in
            logout = False; ch = []
            if "role" in d and ROLE_OLD.get(d.get("role"), d.get("role")) in USER_ROLES and d["role"] != u["role"]:
                u["role"] = ROLE_OLD.get(d["role"], d["role"]); ch.append("role " + u["role"])
                if "push" not in d:
                    u["push"] = list(ROLE_PUSH.get(u["role"], USER_PUSH))
            if "perms" in d and isinstance(d["perms"], list):
                u["perms"] = [p for p in USER_PERMS if p in d["perms"]]; ch.append("rights " + ",".join(u["perms"]))
            if "win" in d:
                w = d["win"] if isinstance(d["win"], dict) else None
                if w and not (_USER_HM.match(str(w.get("from", ""))) and _USER_HM.match(str(w.get("to", "")))):
                    return False, "time: hh:mm"
                u["win"] = w; ch.append("time " + (f"{w['from']}-{w['to']}" if w else "always"))
            if "until" in d:
                v = str(d.get("until") or "")
                if v and not _USER_DAY.match(v):
                    return False, "date: yyyy-mm-dd"
                u["until"] = v; ch.append("until " + (v or "-"))
            if "push" in d and isinstance(d["push"], list):
                u["push"] = [p for p in USER_PUSH if p in d["push"]]; ch.append("push " + (",".join(u["push"]) or "-"))
            if "ntfy" in d:
                v = str(d.get("ntfy") or "").strip()
                if v and not _USER_NTFY.match(v):
                    return False, "ntfy: a topic (6 to 64 letters, digits, - _) or https://server/topic"
                u["ntfy"] = v; ch.append("own ntfy topic" if v else "no own ntfy topic")
            log_event("web", f"{who}: user «{u['name']}»: " + ("; ".join(ch) or "no change"))
        else:
            return False, "unknown action"
        if logout:
            CFG["trusted"] = [e for e in (CFG.get("trusted") or []) if e.get("user") != u["name"]]   # 2.95.33: log in again
        CFG["users"] = users_clean(CFG["users"])
    _PW_OK.clear(); save_settings_now()
    return True, ""


# 2.95.35: ONE list of what users without admin rights may read. Everything else (also every new function) is only for
# the administrator. 2.98.42: by rights (USER_PERMS) instead of two roles; every user may read BASE, each right adds its part.
VIEW_GET_PAGES = {"/", "/help", "/quick", "/more"}
VIEW_GET = ("/api/tunnel", "/api/helper", "/api/info", "/api/nettest", "/api/state", "/api/alerts", "/api/appearance", "/api/version",
            "/api/health", "/api/gps", "/api/zones", "/api/webpush", "/api/ui", "/api/battery", "/api/sensors", "/api/qs", "/api/schedule",
            "/api/schema", "/api/triggers", "/api/fa", "/api/appicon", "/api/audio", "/i18n/", "/app-icon/", "/sim-icon/", "/api/simbar", "/api/news")
PERM_GET = {"live": ("/cams", "/preview", "/api/cams", "/api/frame.jpg", "/video_feed", "/cam_feed/", "/snapshot.jpg", "/api/audio/live",
                     "/sim/view.jpg", "/sim/view.mjpg"),
            "rec": ("/recordings", "/diary", "/kino", "/api/kino", "/api/dataset.zip", "/api/recordings", "/api/places", "/rec/file/", "/rec/play/",
                    "/rec/thumb/", "/rec/share/", "/rec/report/", "/api/day", "/api/diary", "/diary/img/", "/api/timelapse", "/timelapse/",
                    "/api/species", "/api/loop", "/api/report"),
            "arm": ("/protect", "/zones"),
            "games": ("/party", "/api/party"),
            "settings": ("/settings",)}
VIEW_POST = {"/api/webpush", "/api/time", "/api/gps"}
PERM_POST = {"rec": {"/api/rec/prepare", "/rec/zip", "/api/rec/fav", "/api/rec/false"},
             "arm": {"/api/arm", "/api/night", "/api/camping", "/api/quick", "/api/mode", "/api/tunnel", "/api/helper", "/api/info", "/api/nettest", "/api/tv"},
             "light": {"/api/light", "/api/disco"},
             "talk": {"/api/talk", "/api/talk/stop", "/api/tts"},
             "head": {"/api/follow", "/api/mover", "/api/move", "/api/stick"},
             "settings": {"/api/zones", "/api/schedule"}}
PERM_SET_KEYS = {"arm": {"thermal_on", "nightvision", "show_objects", "show_mask"}, "head": {"track_person", "track_motion"}}


def role_allows(role, path, method, d, perms=None):
    """may a user with this role (and these rights - for «custom») do this? The administrator may do everything."""
    if role == "admin":
        return True
    P = set(perms) if perms is not None else set(ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))
    if method in ("GET", "HEAD"):
        if path in ("/servo", "/api/servo"):                  # 2.98.35: everybody sees the servo state (who steers, Not-Aus)
            return True
        if path.startswith(ADMIN_GET):
            return False
        if path in VIEW_GET_PAGES or path.startswith(VIEW_GET):
            return True
        return any(path == x or (x.endswith("/") and path.startswith(x)) or (x.startswith("/api/") and path.startswith(x))
                   for p in P for x in PERM_GET.get(p, ()))
    if path == "/api/servo":                                  # 2.98.35: Not-Aus is for everybody, the rest for the administrator
        return d.get("op") == "estop"
    if path == "/api/webpush":
        return d.get("action") in ("subscribe", "unsubscribe", "key", None)
    if path in VIEW_POST:
        return True
    if path == "/api/set":
        k = d.get("key")
        if any(k in PERM_SET_KEYS.get(p, ()) for p in P):
            return True
        return "settings" in P and isinstance(k, str) and k not in USER_SETTINGS_DENY and k in CFG
    if path == "/api/text":
        return "settings" in P and isinstance(d.get("key"), str) and d.get("key") not in USER_SETTINGS_DENY
    if path == "/api/audio":
        return ("siren" in P and d.get("action") in ("test", "siren", "stop")) or ("talk" in P and d.get("action") == "stop")
    if path == "/api/action":
        return "head" in P and d.get("action") in ("center", "patrol")
    return any(path in PERM_POST.get(p, ()) for p in P)


# «settings» (own rights) never reaches the security: password, users, keys, access, updates, secret addresses and channels
USER_SETTINGS_DENY = {"login_https_only", "https_extra", "web_port", "web_bind", "lock_on", "lock_pin", "update_unsigned", "update_url",
                      "update_token", "protect_pin", "users", "trusted", "app_keys", "shortcut_token", "web_pw_hash", "guest_token",
                      "ext_token", "web_password", "notify_url", "notify_type", "telegram_token", "telegram_chat", "pushover_token",
                      "pushover_user", "email_password", "email_user", "sms_numbers", "public_url", "tunnel_on", "guest_on", "ext_on",
                      "mqtt_password", "mqtt_user", "hotspot_password", "autostart", "sim_url"}


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
        elif isinstance(w, (list, tuple)) and wp_clean(w) is not None:      # 2.98.35: also [pan, tilt, name(, 0)] (076)
            wps.append(wp_clean(w))
    WAYPOINTS[:] = wps[:50]
    CFG["ui_hidden"] = [k for k in CFG["ui_hidden"] if isinstance(k, str)][:200]
    CFG["ui_open"] = [k for k in CFG["ui_open"] if isinstance(k, str)][:100]
    CFG["qs_layout"] = qs_layout_clean(CFG["qs_layout"])   # 2.98.29: also favourites and cards (290)
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
    try:
        did = thermal_migrate(cfg_in)                        # 2.98.22: thermal camera runs along (232)
        if did:
            log_event("sys", "Settings of an older version taken over: " + "; ".join(did))
    except Exception as e:
        log_event("sys", f"Settings migration (232): {e}"[:150])
    for _f, _n in ((lambda: shortcut_migrate(cfg_in), "573"), (place_report_migrate, "317")):   # aufr: shortcut key -> app key, public path -> zone
        try:
            did = _f()
            if did:
                log_event("sys", "Settings of an older version taken over: " + "; ".join(did))
        except Exception as e:
            log_event("sys", f"Settings migration ({_n}): {e}"[:150])


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


# «Reset settings» (before: a plain confirm, also removed the password) is now «Reset to factory settings» with password /
# PIN, a typed word and a backup copy: factory_reset() in 586.


