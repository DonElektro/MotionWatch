#@ Motion Watch – Teil 390: Protokoll, Bedienermodus, Pause, Update-Wächter. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Event log on the SD card: motionwatch.log is written at once (every line). Each day gets its own file in the archive
# logs/motionwatch_YYYY-MM-DD.log.gz (packed), kept for log_keep_days. A status line every log_status_min minutes.
# ----------------------------------------------------------------------------
LOG_NAME_RE = re.compile(r"^motionwatch_\d{4}-\d{2}-\d{2}(_\d+)?\.log(\.gz)?$")
LOG_LINE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})  \[([a-z]+)\]  (.*)$")
LOG_MAX_MB = 20


def log_dir():
    return os.path.join(DATA_DIR, "logs")


def log_rotate(force=False):
    """Move yesterday's (or a too big) motionwatch.log into the archive and pack it."""
    import gzip
    try:
        st = os.stat(LOG_FILE)
    except OSError:
        return False
    day = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")
    big = st.st_size > LOG_MAX_MB * 1024 * 1024
    if not (force or big or day != datetime.now().strftime("%Y-%m-%d")):
        return False
    os.makedirs(log_dir(), exist_ok=True)
    base = os.path.join(log_dir(), f"motionwatch_{day}")
    name, i = base + ".log.gz", 1
    while os.path.exists(name):
        i += 1; name = f"{base}_{i}.log.gz"
    tmp = LOG_FILE + ".rotating"
    try:
        os.replace(LOG_FILE, tmp)                         # new lines go into a fresh motionwatch.log from now on
        with open(tmp, "rb") as src, gzip.open(name + ".part", "wb", compresslevel=6) as dst:
            shutil.copyfileobj(src, dst)
        os.replace(name + ".part", name)
        os.remove(tmp)
    except OSError as e:
        print(f"Log rotation failed: {e}")
        return False
    return True


def log_purge():
    keep = max(1, int(CFG["log_keep_days"]))
    limit = (datetime.now() - timedelta(days=keep)).strftime("%Y-%m-%d")
    n = 0
    try:
        for f in os.listdir(log_dir()):
            if LOG_NAME_RE.match(f) and f[12:22] < limit:
                os.remove(os.path.join(log_dir(), f)); n += 1
    except OSError:
        pass
    return n


def log_archive():
    out = []
    try:
        for f in sorted(os.listdir(log_dir()), reverse=True):
            if LOG_NAME_RE.match(f):
                out.append({"name": f, "day": f[12:22], "size": os.path.getsize(os.path.join(log_dir(), f))})
    except OSError:
        pass
    cur = os.path.getsize(LOG_FILE) if os.path.isfile(LOG_FILE) else 0
    return {"current": {"name": "motionwatch.log", "size": cur}, "files": out, "keep_days": int(CFG["log_keep_days"])}


def log_lines(name="", limit=300, kind="", q=""):
    """The newest lines of today's log (or of an archive day), newest first, filtered by kind / words."""
    import gzip
    path = LOG_FILE if not name or name == "motionwatch.log" else (os.path.join(log_dir(), name) if LOG_NAME_RE.match(name) else "")
    if not path or not os.path.isfile(path):
        return []
    try:
        if path.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        else:
            with open(path, "rb") as f:                   # only the end of a big file
                f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 4 * 1024 * 1024))
                lines = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return []
    words = [w for w in (q or "").lower().split() if w]
    out = []
    for ln in reversed(lines):
        m = LOG_LINE_RE.match(ln)
        if not m:
            continue
        if kind == "important":
            if not log_important(m.group(3), m.group(4)):
                continue
        elif kind and m.group(3) != kind:
            continue
        if words and not all(w in ln.lower() for w in words):
            continue
        out.append({"d": m.group(1), "t": m.group(2), "kind": m.group(3), "text": m.group(4)})
        if len(out) >= limit:
            break
    return out


def status_line():
    st = STATE; parts = []
    parts.append({"armed": "armed", "arming": "arming"}.get(st.get("arm_state"), "disarmed"))
    if st.get("cpu") is not None:
        parts.append(f"CPU {st['cpu']:.0f}%" + (f" {st['cpu_temp']:.0f}°C" if st.get("cpu_temp") is not None else ""))
    parts.append(f"{st.get('fps', 0):.0f} FPS · camera {st.get('source_status', '?')}")
    wf = st.get("wifi") or {}
    if wf.get("connected"):
        parts.append(f"Wi-Fi {wf.get('dbm')} dBm")
    net = st.get("net") or {}
    if net.get("online") is not None:
        parts.append("internet ok" if net["online"] else "no internet")
    dk = st.get("disk") or {}
    if dk.get("free_mb") is not None:
        parts.append(f"{dk['free_mb']} MB free")
    sup = st.get("supply") or {}
    if sup.get("volt"):
        parts.append(f"{sup['volt']:.2f} V" + (" UNDER-VOLTAGE" if sup.get("uv_now") else ""))
    bt = st.get("battery") or {}
    if bt.get("pct") is not None:
        parts.append(f"battery {bt['pct']} %")
    if st.get("remote"):
        parts.append("remote: " + ", ".join(st["remote"]))
    parts.append(f"persons today {st.get('detections_total', 0)}")
    return "Status: " + " · ".join(parts)


def preload_events():
    """After a (re)start the overview would be empty: take the last entries of today's log (and of the newest archive day)."""
    lines = log_lines("", 300)                           # today's file already holds the lines of this start too
    if sum(1 for x in lines if log_important(x["kind"], x["text"])) < 10:
        arch = log_archive()["files"]
        if arch:
            lines += log_lines(arch[0]["name"], 300)
    old = [{"t": x["t"], "d": x["d"], "kind": x["kind"], "text": x["text"], "imp": log_important(x["kind"], x["text"])} for x in lines]
    if old:
        with LOCK:
            STATE["events"][:] = old[:300]


class LogKeeper:
    """Every minute: new day -> archive yesterday's log; delete old archive files; status line every N minutes."""
    def __init__(self):
        self._st = time.time(); self._purge_t = 0.0
        try:
            log_rotate()                                  # a log from an earlier day (e.g. after the Pi was off)
            preload_events()
        except Exception:
            pass
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            time.sleep(60)
            try:
                if log_rotate():
                    log_event("sys", "New day: yesterday's event log was moved into the archive")
                if time.time() - self._purge_t > 3600:
                    self._purge_t = time.time()
                    n = log_purge()
                    if n:
                        log_event("sys", f"Event log archive: {n} old day(s) deleted")
                every = int(CFG["log_status_min"])
                if every > 0 and time.time() - self._st >= every * 60:
                    self._st = time.time()
                    log_event("status", status_line())
            except Exception as e:
                print(f"Log keeper: {e}")


# ----------------------------------------------------------------------------
# Operator mode ("lock"): the person using the device can switch the main functions on and off, but cannot change
# any settings. Unlocking needs the PIN (4-8 digits, stored as PBKDF2 hash). Enforced by the web server and the window.
# ----------------------------------------------------------------------------
OPER_KEYS = {"detection_on", "record", "notify_on", "browser_alarm", "timelapse_on", "eco_on", "patrol", "track_person",
             "relays_on", "noise_alarm", "thermal_on", "thermal_alarm", "report_on", "show_objects", "nightvision"}
LOCK_FAILS = []


def _pin_hash(pin, salt=None):
    import hashlib
    salt = salt or secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 120000).hex()


def lock_pin_ok(pin):
    h = CFG["lock_pin"]
    if not h or "$" not in h or not isinstance(pin, str):
        return False
    return hmac.compare_digest(_pin_hash(pin, h.split("$", 1)[0]), h)


# not put back when unlocking: what the operator does (arm, move the camera), what the Pi measures itself, how a
# device shows the page
LOCK_KEEP = {"armed", "pan", "tilt", "hotspot_on", "lock_on", "lock_pin", "lock_snap", "web_ui", "ui_open", "ui_tab", "theme", "lang",
             "fullscreen", "latitude", "longitude", "batt_full_t", "batt_warned", "setup_done", "autostart", "ui_simple"}
LOCK_LAST = {"restored": []}


def lock_snapshot():
    d = json.loads(json.dumps(settings_data()))
    d["cfg"] = {k: v for k, v in d["cfg"].items() if k not in LOCK_KEEP}
    d["v"] = 2
    return d


def lock_restore():
    """Unlocking: everything changed since the lock goes back to the copy (settings, zones, schedules, waypoints, relays)."""
    snap = CFG.get("lock_snap") if isinstance(CFG.get("lock_snap"), dict) else {}
    CFG["lock_snap"] = {}
    if not snap:
        return []
    if snap.get("v") != 2:                                           # copy made by 2.44.0: settings only
        snap = {"cfg": {k: v for k, v in snap.items() if not k.startswith("_")}}
    now = json.loads(json.dumps(settings_data()))
    back = [k for k, v in snap.get("cfg", {}).items() if k in CFG and k not in LOCK_KEEP and k not in VOLATILE and now["cfg"].get(k) != v]
    for part in ("waypoints", "relays", "schedules", "zones"):
        if part in snap and snap[part] != now.get(part):
            back.append(part)
    if not back:
        return []
    data = {"cfg": {k: v for k, v in snap.get("cfg", {}).items() if k not in LOCK_KEEP and k not in VOLATILE}}
    for part in ("waypoints", "relays", "schedules", "zones"):
        data[part] = snap.get(part, now.get(part))
    keep = {k: CFG[k] for k in LOCK_KEEP if k in CFG}
    apply_settings(data)
    CFG.update(keep)
    for k in back:
        if k in CFG:
            try:
                sched_user_changed(k)
            except Exception:
                pass
    HW_REINIT["want"] = True; SETTINGS_GEN["n"] += 1                 # servos / lights / window follow the old values
    return back


def lock_info():
    snap = CFG.get("lock_snap") if isinstance(CFG.get("lock_snap"), dict) else {}
    since = str(snap.get("saved") or "")[11:16] if CFG["lock_on"] else ""
    return {"on": bool(CFG["lock_on"]), "pin_set": bool(CFG["lock_pin"]), "restored": len(LOCK_LAST["restored"]), "since": since}


def lock_set(action, pin="", new_pin="", source="web"):
    """lock (optionally with a new PIN) / unlock (PIN) / pin (change the PIN while unlocked)."""
    pin, new_pin = str(pin or "").strip(), str(new_pin or "").strip()
    if new_pin and not re.fullmatch(r"\d{4,8}", new_pin):
        return False, "the PIN must have 4 to 8 digits"
    if action in ("lock", "pin"):
        if CFG["lock_on"]:
            return False, "locked - settings can only be changed after unlocking (PIN)"
        if new_pin:
            CFG["lock_pin"] = _pin_hash(new_pin)
        if action == "pin":
            save_settings(); log_event("sys", f"Operator mode: PIN changed ({source})")
            return True, ""
        if not CFG["lock_pin"]:
            return False, "set a PIN first"
        CFG["lock_snap"] = lock_snapshot(); CFG["lock_on"] = True; save_settings()
        log_event("sys", f"Operator mode ON - settings locked, a copy of all {len(CFG['lock_snap'])} settings kept ({source})")
        return True, ""
    if action == "unlock":
        now = time.time()
        LOCK_FAILS[:] = [t for t in LOCK_FAILS if now - t < 300]
        if len(LOCK_FAILS) >= 5:
            return False, "too many wrong PINs - try again in 5 minutes"
        if not lock_pin_ok(pin):
            LOCK_FAILS.append(now)
            log_event("sys", f"Operator mode: wrong PIN ({source})")
            return False, "wrong PIN"
        LOCK_FAILS.clear()
        back = lock_restore(); LOCK_LAST["restored"] = back
        CFG["lock_on"] = False; save_settings()
        log_event("sys", f"Operator mode OFF - settings unlocked ({source})"
                         + (f", {len(back)} change(s) put back: " + ", ".join(back[:12]) + (" …" if len(back) > 12 else "") if back else ", nothing was changed"))
        return True, ""
    return False, "unknown action"


# operator mode: everything may be changed and is put back at unlocking - except what could lock the owner out
LOCK_DENY_PATHS = {"/api/wifi", "/api/hotspot", "/api/password", "/api/settings/import", "/api/autostart", "/api/setup", "/api/ext",
                   "/api/users", "/api/trusted", "/api/shortcut"}     # 2.95.34: users, trusted devices, shortcut keys too
LOCK_DENY_KEYS = {"net_mode", "hotspot_ssid", "hotspot_password", "hotspot_on", "update_url", "update_token", "update_unsigned",
                  "lock_on", "lock_pin", "autostart", "web_port"}


def lock_allows(path, method, data):
    """Web requests in operator mode: all but the ones that could lock the owner out."""
    if not CFG["lock_on"]:
        return True
    if method != "POST":
        return path != "/api/settings/export"            # the settings file contains passwords
    if path in LOCK_DENY_PATHS:
        return False
    d = data or {}
    if path in ("/api/set", "/api/text") and d.get("key") in LOCK_DENY_KEYS:
        return False
    return True


_GH_HOSTS = ("raw.githubusercontent.com", "api.github.com", "github.com", "objects.githubusercontent.com")


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    """urllib copies the Authorization header to the new address of a redirect - only keep it on the same host
    (or GitHub to GitHub). 2.95.33"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            try:
                from urllib.parse import urlparse
                h0, h1 = (urlparse(req.full_url).hostname or "").lower(), (urlparse(new.full_url).hostname or "").lower()
            except ValueError:
                h0, h1 = "", "?"
            if h0 != h1 and not (h0 in _GH_HOSTS and h1 in _GH_HOSTS):
                for k in list(new.headers):
                    if k.lower() == "authorization":
                        del new.headers[k]
                new.unredirected_hdrs.pop("Authorization", None)
        return new


try:
    urllib.request.install_opener(urllib.request.build_opener(_SafeRedirect))
except Exception:
    pass


def _upd_request(url, extra=None):
    """Request for the update source. The GitHub key is added only for GitHub addresses (never sent anywhere else)."""
    h = {"User-Agent": "MotionWatch/" + APP_VERSION}
    h.update(extra or {})
    try:
        from urllib.parse import urlparse
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        host = ""
    tok = CFG["update_token"].strip()
    if tok and host in _GH_HOSTS:
        h["Authorization"] = "token " + tok
    return urllib.request.Request(url, headers=h)


def _upd_error(e):
    """Readable reason why the update source did not answer (the key never appears in it)."""
    import urllib.error
    code = getattr(e, "code", None)
    if code in (401, 403, 404) and "github" in CFG["update_url"]:
        if not CFG["update_token"].strip():
            return "not found - is the repository private? Then enter the GitHub key (token)"
        return "GitHub refused the key - check that it is valid and may read this repository"
    msg = str(e)
    tok = CFG["update_token"].strip()
    return msg.replace(tok, "***") if tok else msg


def update_check():
    """List what can be chosen: versions next to this program (installed) + versions at the update source."""
    src = CFG["update_url"].strip()
    items = {}
    for it in local_versions(HERE):
        items[it["version"]] = dict(it, installed=True, available=False, url="")
    msg = ""
    if src.startswith("https://"):
        try:
            # GitHub's file server keeps a copy for up to 5 minutes - a changing ?t= asks for the newest list
            src_ = src
            fs_ = UPD.get("fast_sha") or ""                 # 2.95.71 test mode: the list of exactly this commit (never an old copy)
            mg_ = re.match(r"(https://raw\.githubusercontent\.com/[^/]+/[^/]+/)[^/]+(/.+)$", src)
            if fs_ and mg_ and CFG.get("update_fast"):
                src_ = mg_.group(1) + fs_ + mg_.group(2)
            req = _upd_request(src_ + ("&" if "?" in src_ else "?") + "t=" + str(int(time.time())), {"Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read(1024 * 1024 + 1)[:1024 * 1024].decode("utf-8"))
            UPD["list_time"] = str(data.get("generated") or "")[:16]
            base = src.rsplit("/", 1)[0] + "/"
            for e in (data.get("versions") or [])[:200]:
                v, fn = str(e.get("version", "")), str(e.get("file", ""))
                url = str(e.get("url") or (base + fn))
                if not (VER_RE.match(v) and VFILE_RE.match(fn) and url.startswith("https://")):
                    continue
                it = items.setdefault(v, {"version": v, "file": fn, "installed": False, "path": ""})
                sha = str(e.get("sha256", ""))[:64].lower()
                it.update(available=True, url=url, sha256=sha, signed=sig_ok(v, fn, sha, e.get("sig")),
                          date=str(e.get("date", it.get("date", "")))[:16], notes=str(e.get("notes", it.get("notes", "")))[:600])
        except Exception as e:
            msg = f"update source not reachable: {_upd_error(e)}"[:240]
    elif src.startswith("/"):
        found = local_versions(src)
        if not found and not os.path.isdir(src):
            msg = "folder not found"
        sigs = {}
        try:                                             # signatures of a folder (USB stick) come from its versions.json
            with open(os.path.join(src, "versions.json"), encoding="utf-8") as f:
                sigs = {str(e.get("file")): str(e.get("sig") or "") for e in (json.load(f).get("versions") or [])[:500]}
        except (OSError, ValueError, AttributeError):
            pass
        for it in found:
            cur = items.setdefault(it["version"], dict(it, installed=False, path=""))
            sha = ""
            if sigs.get(it["file"]):
                try:
                    with open(it["path"], "rb") as f:
                        sha = hashlib.sha256(f.read(8 * 1024 * 1024 + 1)).hexdigest()
                except OSError:
                    pass
            cur.update(available=True, src_path=it["path"], url="", sha256=sha, signed=sig_ok(it["version"], it["file"], sha, sigs.get(it["file"])))
            cur.setdefault("notes", it["notes"])
    for v, it in items.items():
        it["current"] = v == APP_VERSION
        it.setdefault("signed", False)
    UPD["items"] = sorted(items.values(), key=lambda x: _vkey(x["version"]), reverse=True)
    newer = [x for x in UPD["items"] if x.get("available") and _installable(x) and _vkey(x["version"]) > _vkey(APP_VERSION)]
    STATE["update_new"] = ({"version": newer[0]["version"], "notes": newer[0].get("notes", "")[:300], "date": newer[0].get("date", "")}
                           if newer else {})
    UPD["msg"] = msg; UPD["time"] = time.time()
    return UPD["items"], msg


def _verify_program(data, want_version, sha=""):
    import hashlib
    if len(data) > 8 * 1024 * 1024 or len(data) < 10000:
        return "the file does not look like MoveEye"
    if sha and hashlib.sha256(data).hexdigest() != sha:
        return "the file is damaged (checksum does not match) - try again"
    try:
        text = data.decode("utf-8")
        compile(text, "update.py", "exec")
    except Exception:
        return "the file is not a working Python program"
    if "class MotionWatch" not in text or file_version(text) != want_version:
        return "the file does not look like MoveEye"
    return ""


def update_install(version):
    """Fetch (if needed), check and start the chosen version. The program restarts itself (settings stay)."""
    if UPD["busy"]:
        return False, "an update is already running"
    if not UPD["items"] or time.time() - UPD["time"] > 600:
        update_check()
    it = next((x for x in UPD["items"] if x["version"] == version), None)
    if it is None:
        return False, "unknown version"
    if it.get("current"):
        return False, "this version is already running"
    if not _installable(it):
        return False, "this version is not signed by the developer - not installed (only with the setting «Also accept unsigned versions»)"
    UPD["busy"] = True
    UPD_PROG.update(phase="download", got=0, size=int(it.get("size") or 0), t0=time.time(), tp=time.time())
    try:
        dst = os.path.join(HERE, it["file"])
        if not it.get("installed"):
            if it.get("url"):
                req = _upd_request(it["url"])
                with urllib.request.urlopen(req, timeout=60) as r:
                    try:
                        UPD_PROG["size"] = int(r.headers.get("Content-Length") or 0) or UPD_PROG["size"]
                    except ValueError:
                        pass
                    parts, n = [], 0
                    while n <= 8 * 1024 * 1024:
                        b = r.read(min(65536, 8 * 1024 * 1024 + 1 - n))
                        if not b:
                            break
                        parts.append(b); n += len(b); UPD_PROG["got"] = n
                    data = b"".join(parts)
            elif it.get("src_path"):
                with open(it["src_path"], "rb") as f:
                    data = f.read(8 * 1024 * 1024 + 1)
            else:
                return False, "unknown version"
            UPD_PROG.update(phase="check", tp=time.time())
            err = _verify_program(data, version, it.get("sha256", ""))
            if err:
                return False, err
            tmp = dst + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, dst)
            log_event("sys", f"Version {version} downloaded: {it['file']}")
        else:
            UPD_PROG.update(phase="check", tp=time.time())
            with open(dst, "rb") as f:
                err = _verify_program(f.read(8 * 1024 * 1024 + 1), version)
            if err:
                return False, err
        UPD_PROG.update(phase="restart", tp=time.time())
        update_restart(dst, version)
        return True, ""
    except Exception as e:
        return False, f"update failed: {_upd_error(e)}"[:240]
    finally:
        UPD["busy"] = False
        if UPD_PROG["phase"] != "restart":
            UPD_PROG["phase"] = ""


RESTART = {"pending": ""}
PAUSING = {"on": False}


def _close_fds_on_exec():
    """The web server sockets are inheritable: they must not survive os.execv (the new program needs the port)."""
    try:
        if RUNGUARD.get("clean"):
            RUNGUARD["clean"]()                         # a planned restart (update, pause) is a clean end
    except Exception:
        pass
    try:
        for fd in os.listdir("/proc/self/fd"):
            if int(fd) > 2:
                try:
                    os.set_inheritable(int(fd), False)
                except OSError:
                    pass
    except OSError:
        pass


def _base_args():
    """Command line of this run without one-shot options and without --paused-until."""
    out, skip = [], False
    for x in sys.argv[1:]:
        if skip:
            skip = False; continue
        if x == "--paused-until":
            skip = True; continue
        if x.startswith("--paused-until=") or x in ("--print-service", "--install-service", "--allow-wifi"):
            continue
        out.append(x)
    return out


PAUSE_CHOICES = (5, 15, 30, 60, 120, 240, 480, 720)
TOOLMODE = {"until": 0.0, "by": "", "since": 0.0}         # tool mode: camera, detection and AI rest - the tools get the computer


def toolmode_on():
    return time.time() < TOOLMODE["until"]


def toolmode_set(minutes, source="web"):
    """minutes > 0: MoveEye rests (no camera, no detection, no alarms) and comes back by itself after the time.
    0: back now. The web page and the tools keep running."""
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return False, "not a number"
    if minutes <= 0:
        if toolmode_on():
            TOOLMODE["until"] = 0.0
            log_event("sys", f"Tool mode ended by {source} - monitoring runs again")
        return True, ""
    if minutes > 720:
        return False, "not a number"
    was = toolmode_on()
    TOOLMODE.update(until=time.time() + minutes * 60, by=source, since=TOOLMODE["since"] if was else time.time())
    log_event("sys", f"Tool mode for {minutes} min by {source}: monitoring paused until {datetime.fromtimestamp(TOOLMODE['until']).strftime('%H:%M')}")
    return True, ""


def toolmode_state():
    on = toolmode_on()
    return {"on": on, "until": TOOLMODE["until"] if on else 0, "since": TOOLMODE["since"] if on else 0, "cpu": STATE.get("cpu"),
            "temp": STATE.get("cpu_temp"), "armed": bool(CFG["armed"])}


def pause_program(minutes, source="web"):
    """Switch the program off now (recording finished, settings saved) and start it again after <minutes>.
    The same process becomes a tiny waiting page (same PID: autostart and watchdog stay happy)."""
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return False, "not a number"
    if not 1 <= minutes <= 1440:
        return False, "not a number"
    if RESTART.get("pending"):
        return False, "a restart is already running"
    until = int(time.time() + minutes * 60)
    RESTART["pending"] = "pause"
    log_event("sys", f"Program paused for {minutes} min by {source} - starts again at {datetime.fromtimestamp(until).strftime('%H:%M')}")

    def work():
        time.sleep(1.5)                                   # the page gets its answer first
        try:
            w = WATCH_REF["w"]
            end = time.time() + 10.0
            while w is not None and w.writer is not None and time.time() < end:
                time.sleep(0.2)
            if AUDIO is not None:
                AUDIO.wait_mux(20.0)
            sound_stop(); talk_stop()
            PAUSING["on"] = True                          # relays and lights off before the program goes away
            time.sleep(0.6)
            if getattr(w, "sights", None) is not None:
                w.sights.tick(time.time(), force=True)    # the open visits go into the diary
            save_settings_now()
            _close_fds_on_exec()
            os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)] + _base_args() + ["--paused-until", str(until)])
        except Exception as e:
            RESTART["pending"] = ""
            log_event("sys", f"Pause failed: {e}"[:200])
    threading.Thread(target=work, daemon=True, name="pause").start()
    return True, ""


PAUSE_PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye – __T_TITLE__</title><style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0b0f14;color:#e6edf3;
font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;text-align:center;padding:20px;box-sizing:border-box}
.c{max-width:420px}.big{font-size:56px}.t{font-size:22px;font-weight:700;margin:6px 0}.m{color:#8b9bb0}
#cd{font-size:40px;font-weight:700;margin:14px 0;font-variant-numeric:tabular-nums}
button{font:inherit;font-weight:700;padding:12px 22px;border-radius:12px;border:0;background:#2f81f7;color:#fff;cursor:pointer;margin-top:10px}
</style></head><body><div class="c"><div class="big">⏸</div><div class="t">__T_TITLE__</div>
<div class="m">__T_BACK__ <b>__UNTIL__</b></div><div id="cd">–</div>
<div class="m">__T_NOTE__</div>
<form method="post" action="/resume"><button>▶ __T_NOW__</button></form></div>
<script>const U=__UNTIL_TS__*1000;function f(){const s=Math.max(0,Math.round((U-Date.now())/1000));
document.getElementById("cd").textContent=Math.floor(s/3600)+":"+String(Math.floor(s%3600/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0");
if(s<=0){document.getElementById("cd").textContent="…";setTimeout(()=>location.replace("/"),4000);return;}setTimeout(f,1000);}f();</script>
</body></html>"""


def run_paused(until, argv_rest):
    """Waiting mode: no camera, no detection - only a small page on the web port. At <until> (or 'Start now')
    the full program comes back (same process, same options)."""
    import http.server
    de = CFG["lang"] == "de"
    T = {"title": tr("Program paused"), "back": tr("Starts again at"), "note": tr("While paused there is no monitoring and there are no alarms."),
         "now": tr("Start now")}
    state = {"go": False}

    def restart():
        print("Pause over - starting MoveEye again")
        log_event("sys", "Pause over - starting again")
        _close_fds_on_exec()
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)] + argv_rest)

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="text/html; charset=utf-8", extra=None):
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers(); self.wfile.write(data)

        def do_GET(self):
            if self.path.startswith("/api/") or self.path.startswith("/video") or self.path.startswith("/g/"):
                self._send(503, json.dumps({"paused": True, "until": until}), "application/json")
                return
            page = (PAUSE_PAGE.replace("__T_TITLE__", T["title"]).replace("__T_BACK__", T["back"]).replace("__T_NOTE__", T["note"])
                    .replace("__T_NOW__", T["now"]).replace("__UNTIL_TS__", str(int(until)))
                    .replace("__UNTIL__", datetime.fromtimestamp(until).strftime("%H:%M")))
            self._send(200, page)

        def do_POST(self):
            if self.path != "/resume":
                self._send(404, "not found", "text/plain"); return
            if web_pw_active() and self.client_address[0] not in ("127.0.0.1", "::1"):
                import base64
                ok = False
                h = self.headers.get("Authorization", "")
                if h.startswith("Basic "):
                    try:
                        pw = base64.b64decode(h[6:]).decode("utf-8", "replace").split(":", 1)[1]
                        ok = (hmac.compare_digest(pw.encode(), CFG["web_password"].encode()) if CFG["web_password"] else pw_check(pw))
                    except (ValueError, IndexError):
                        ok = False
                if not ok:
                    self._send(401, tr("Login required"), "text/plain", {"WWW-Authenticate": 'Basic realm="MoveEye", charset="UTF-8"'}); return
            state["go"] = True
            self._send(200, "<meta http-equiv='refresh' content='15;url=/'>" + tr("Starting …"))

    srv = None
    for _i in range(30):                                   # the old program has just released the port
        try:
            http.server.ThreadingHTTPServer.allow_reuse_address = True
            srv = http.server.ThreadingHTTPServer((WEB_OPTS.get("bind") or "0.0.0.0", int(CFG["web_port"])), H)
            break
        except OSError:
            time.sleep(1.0)
    if srv is not None:
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"MoveEye paused until {datetime.fromtimestamp(until).strftime('%H:%M')} - page on port {CFG['web_port']}")
    sd_notify("READY=1\nSTATUS=paused")
    last_ping = 0.0
    try:
        while time.time() < until and not state["go"]:
            if time.time() - last_ping > 20:
                last_ping = time.time(); sd_notify("WATCHDOG=1")
            time.sleep(0.5)
        if state["go"]:
            log_event("sys", "Pause ended early ('Start now')")
            time.sleep(0.8)                                # the answer reaches the browser first
    except KeyboardInterrupt:
        sys.exit(0)
    restart()


def _guard_file():
    return os.path.join(DATA_DIR, "update_guard.json")


RUNGUARD = {"t0": time.time(), "m0": time.monotonic(), "safe": False, "last": None, "streak": 0, "changed": []}
SAFE_SET = {"ai_enabled": False, "thermal_on": False, "thermal_alarm": False, "nightvision": False, "nightvision_auto": False,
            "patrol": False, "track_person": False, "timelapse_on": False, "light_white": "off", "light_ir": "off"}


def _run_file():
    return os.path.join(DATA_DIR, "run_state.json")


def _run_write(d):
    try:
        tmp = _run_file() + ".tmp"
        with open(tmp, "w") as f:
            json.dump(d, f)
        os.replace(tmp, _run_file())
    except OSError:
        pass


def run_guard_start():
    """At every start: did the last run end without a clean stop (the whole Pi went off)? Two short runs in a row ->
    safe start with the heavy parts off. Then a heartbeat every 10 s keeps the conditions for next time."""
    if DEMO["on"]:
        return
    try:
        with open(_run_file()) as f:
            prev = json.load(f)
    except (OSError, ValueError):
        prev = None
    streak = 0
    if isinstance(prev, dict) and not prev.get("clean"):
        ran = int(prev.get("up", 0))
        RUNGUARD["last"] = {"ran_s": ran, "cpu_temp": prev.get("cpu_temp"), "uv": prev.get("uv"), "throttled": prev.get("throttled"),
                            "cpu": prev.get("cpu"), "ai": prev.get("ai"), "ver": prev.get("ver"), "when": prev.get("beat_txt", "")}
        streak = int(prev.get("streak", 0)) + 1 if ran < 600 else 0
        ct = prev.get("cpu_temp")
        log_event("sys", f"The last run ended unexpectedly after {ran // 60} min {ran % 60} s"
                         + (f" (CPU {ct:.0f} °C" if isinstance(ct, (int, float)) else " (") + (", under-voltage" if prev.get("uv") else "")
                         + (", AI on" if prev.get("ai") else "") + ") - power supply, heat or a crash")
    RUNGUARD["streak"] = streak
    if streak >= 2:
        RUNGUARD["safe"] = True
        RUNGUARD["changed"] = [k for k, v in SAFE_SET.items() if k in CFG and CFG[k] != v]
        for k in RUNGUARD["changed"]:
            CFG[k] = SAFE_SET[k]
        save_settings()
        log_event("sys", "Safe start: the Pi went off twice shortly after starting - AI, thermal camera, night vision, IR light "
                         "and patrol are off. Check power supply (5 V / 5 A) and cooling, then switch them on again one by one.")

        def tell():
            time.sleep(40)
            w = WATCH_REF["w"]
            if w is not None:
                w.notifier.info(tr("Safe start: the Pi went off twice shortly after starting. AI, thermal camera, night vision, "
                                   "IR light and patrol are off - check power supply and cooling."), title="{name}: " + tr("safe start"))
        threading.Thread(target=tell, daemon=True).start()
    state = {"start": time.time(), "up": 0, "clean": False, "streak": streak, "ver": APP_VERSION}
    _run_write(state)

    def clean():
        state["clean"] = True; state["up"] = int(time.monotonic() - RUNGUARD["m0"]); _run_write(state)
    atexit.register(clean); RUNGUARD["clean"] = clean

    def beat():
        while True:
            time.sleep(10)
            sup = STATE.get("supply") or {}
            up = int(time.monotonic() - RUNGUARD["m0"])
            state.update(up=up, cpu_temp=STATE.get("cpu_temp"), uv=bool(sup.get("uv_now") or sup.get("uv_boot")),
                         throttled=bool(sup.get("throttled")), cpu=STATE.get("cpu"), ai=bool(CFG["ai_enabled"] and str(STATE.get("ai_status", "")).startswith("running")),
                         beat_txt=datetime.now().strftime("%Y-%m-%d %H:%M"))
            if up > 1800 and state.get("streak"):
                state["streak"] = 0                              # ran long enough: the next short run starts counting again
            # 2.98.13 (memory card): every 10 s only in the first 15 minutes (a crash right after the start counts for the
            # safe start), then once a minute - and at once when the power or the heat gets critical
            crit = (state["uv"], state["throttled"], (state.get("cpu_temp") or 0) >= 75)
            if not state["clean"] and (up < 900 or time.monotonic() - wrote[0] >= 60 or crit != wrote[1]):
                wrote[0] = time.monotonic(); wrote[1] = crit
                _run_write(state)
    wrote = [0.0, None]
    threading.Thread(target=beat, daemon=True, name="runguard").start()


def start_guard():
    """Called early at every start. After an update the new version must run 90 s; if it crashes 3 times in a row
    (the autostart restarts it), the previous version is started again."""
    p = _guard_file()
    try:
        with open(p) as f:
            g = json.load(f)
    except (OSError, ValueError):
        return
    if g.get("new") != APP_VERSION:
        if g.get("old") == APP_VERSION and g.get("new"):   # the old program runs again: the new one did not get far
            log_event("sys", f"Version {g['new']} did not start - back to {APP_VERSION}; it will not be installed automatically again")
            try:
                with open(os.path.join(DATA_DIR, "update_bad.json"), "w") as f:
                    json.dump({"version": g["new"]}, f)
            except OSError:
                pass
        try:
            os.remove(p)
        except OSError:
            pass
        return
    g["tries"] = int(g.get("tries", 0)) + 1
    old = g.get("old_path", "")
    if g["tries"] > 3 and old and os.path.isfile(old) and os.path.abspath(old) != os.path.abspath(__file__):
        log_event("sys", f"Version {APP_VERSION} did not start 3 times - going back to {g.get('old', '?')}")
        try:
            with open(os.path.join(DATA_DIR, "update_bad.json"), "w") as f:
                json.dump({"version": APP_VERSION}, f)    # the automatic update will not try this version again
        except OSError:
            pass
        try:
            os.remove(p)
        except OSError:
            pass
        _close_fds_on_exec()
        os.execv(sys.executable, [sys.executable, old] + _base_args())
    try:
        with open(p, "w") as f:
            json.dump(g, f)
    except OSError:
        pass

    def ok_later():
        time.sleep(90)
        try:
            os.remove(p)
            log_event("sys", f"Version {APP_VERSION} runs fine (update finished)")
        except OSError:
            pass
    threading.Thread(target=ok_later, daemon=True).start()


def update_restart(path, version):
    """Finish the recording, save the settings, then replace this program by the chosen file (same options, same PID:
    the autostart keeps working and points to the new file from now on)."""
    RESTART["pending"] = version
    log_event("sys", f"Switching to version {version} - restarting")
    _restart_mark()

    def work():
        time.sleep(2.0)                                   # the page gets its answer first
        try:
            w = WATCH_REF["w"]
            end = time.time() + 10.0
            while w is not None and w.writer is not None and time.time() < end:
                time.sleep(0.2)
            if AUDIO is not None:
                AUDIO.wait_mux(30.0)
            sound_stop(); talk_stop()
            save_settings_now()
            try:                                          # start guard: the new version must prove it starts
                with open(_guard_file(), "w") as f:
                    json.dump({"old": APP_VERSION, "old_path": os.path.abspath(__file__), "new": version, "tries": 0}, f)
            except OSError:
                pass
            _close_fds_on_exec()
            os.execv(sys.executable, [sys.executable, path] + _base_args())
        except Exception as e:
            RESTART["pending"] = ""; UPD["msg"] = f"restart failed: {e}"[:200]; UPD_PROG["phase"] = ""
            log_event("sys", UPD["msg"])
    threading.Thread(target=work, daemon=True, name="update").start()


class UpdateWatcher:
    """Looks for a new version 2 minutes after the start and then every 3 hours. A new one is shown on the page / in the
    window (button to update) and announced once by push message."""
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True, name="updwatch").start()

    def loop(self):
        time.sleep(120)
        last = 0.0
        while True:
            try:
                if time.time() - last > 3 * 3600 or UPD.get("recheck") or self.fast_changed():
                    UPD["recheck"] = False; last = time.time()
                    self.tick()
                self.auto_install()
            except Exception as e:
                print(f"Update watcher: {e}")
            time.sleep(60)

    def fast_changed(self):
        """2.95.71 test mode: every minute ask GitHub whether versions.json has a new commit. The answer «unchanged» (304 with
        the ETag) does not count against GitHub's limit of 60 questions per hour; a new commit -> look for versions now."""
        if not CFG.get("update_fast") or not CFG["update_url"].strip():
            return False
        m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$", CFG["update_url"].strip())
        if not m:
            return False
        owner, repo, branch, path = m.groups()
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&path={path}&per_page=1"
        h = {"Accept": "application/vnd.github+json", "User-Agent": "MotionWatch"}
        if getattr(self, "_etag", ""):
            h["If-None-Match"] = self._etag
        tok = CFG["update_token"].strip()
        if tok:
            h["Authorization"] = "token " + tok
        import urllib.error
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=10) as r:
                self._etag = r.headers.get("ETag", "") or ""
                sha = str((json.loads(r.read(200000) or b"[]") or [{}])[0].get("sha", ""))
        except urllib.error.HTTPError as e:
            return False                                     # 304 = unchanged (or limit reached: try again in a minute)
        except Exception:
            return False
        old = getattr(self, "_fast_sha", None)
        self._fast_sha = sha
        if sha:
            UPD["fast_sha"] = sha
        if old is None or not sha or sha == old:
            return old is None                               # first answer: look once
        log_event("sys", "Test mode: new versions.json on GitHub - looking for versions now")
        UPD["fast_t"] = time.time()
        return True

    def auto_install(self):
        """Automatic update: in the chosen hour, when nothing is going on (disarmed unless allowed, no recording, no person),
        install the newest version. If the new version does not start, the start guard goes back to the old one.
        2.95.71 test mode (update_fast): at once, at any hour, also while armed - but never during a recording or a person."""
        fast = bool(CFG.get("update_fast"))
        if not (CFG["update_install"] or fast) or RESTART["pending"] or UPD["busy"] or POWER.get("pending"):
            return
        u = STATE.get("update_new") or {}
        v = u.get("version")
        if not v or (not fast and datetime.now().hour != int(CFG["update_hour"]) % 24):
            return
        if (is_armed() and not CFG["update_install_armed"] and not fast) or STATE.get("recording") or STATE.get("persons") or STATE.get("arm_state") == "arming":
            return
        try:
            if simtask_busy():                            # 2.97.0: not in the middle of a test run, a training night or a game
                return
        except NameError:
            pass
        try:
            with open(os.path.join(DATA_DIR, "update_bad.json")) as f:
                if json.load(f).get("version") == v:
                    return                                   # this version was rolled back once: only by hand
        except (OSError, ValueError, AttributeError):
            pass
        if getattr(self, "_tried", {}).get(v, 0) >= 2:
            return                                           # failed twice already: leave it to a person
        self._tried = getattr(self, "_tried", {}); self._tried[v] = self._tried.get(v, 0) + 1
        log_event("sys", f"Automatic update to version {v}")
        w = WATCH_REF["w"]
        if w is not None and CFG["update_push"]:
            de = CFG["lang"] == "de"
            w.notifier.info(trf("Automatic update to version {v} – the program restarts (about 20 s)", v=v), title="{name}: Update")
        ok, err = update_install(v)
        if not ok:
            log_event("sys", f"Automatic update failed: {err}")

    def tick(self):
        if not (CFG["update_auto"] or CFG.get("update_fast")) or not CFG["update_url"].strip() or RESTART["pending"]:
            return
        items, err = update_check()
        new = sorted((x for x in items if x.get("available") and _installable(x) and _vkey(x["version"]) > _vkey(APP_VERSION)), key=lambda x: _vkey(x["version"]))
        if not new:
            STATE["update_new"] = {}; return
        top = new[-1]
        STATE["update_new"] = {"version": top["version"], "notes": top.get("notes", "")[:300], "date": top.get("date", "")}
        if CFG["update_notified"] != top["version"]:
            CFG["update_notified"] = top["version"]; save_settings()
            log_event("sys", f"New version {top['version']} available")
            w = WATCH_REF["w"]
            if CFG["update_push"] and w is not None:
                de = CFG["lang"] == "de"
                pub = CFG["public_url"].strip().rstrip("/")
                w.notifier.info(trf("New version {v} available - tap «Update now» on the page", v=top["version"]),
                                pub + "/" if pub else "", title="{name}: Update")


def self_test(folder=""):
    """--self-test [FOLDER]: quick checks without camera / hardware (also run on GitHub for every version). Returns 0 = all ok."""
    res = []

    def chk(name, fn):
        try:
            r = fn()
            res.append((name, r is not False, "" if r in (None, True) else str(r)))
        except Exception as e:
            res.append((name, False, f"{e.__class__.__name__}: {e}"[:200]))
    pub, sign, verify = _ed25519_impl()

    def ed():
        sk = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
        assert pub(sk).hex() == "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
        sig = sign(sk, b"")
        assert sig.hex().startswith("e5564300c360ac729086e2cc806e828a") and verify(pub(sk), b"", sig) and not verify(pub(sk), b"x", sig)
        assert len(UPDATE_PUBKEY) == 64
    chk("Ed25519 (RFC 8032 test vector)", ed)

    def qr():
        det = cv2.QRCodeDetector()
        for t in ("http://10.42.0.1:5000/", wifi_qr_text("Motion;Watch", "pa:ss"), "x" * 200):
            img = cv2.imdecode(np.frombuffer(qr_png(t, 6), np.uint8), cv2.IMREAD_GRAYSCALE)
            got = det.detectAndDecode(img)[0]
            assert got == t, f"QR decoded {got!r}"
    chk("QR codes (encode + decode)", qr)

    def tun():
        """2.98.13: the tunnel to the simulator without network - a closed line is skipped, an open one carries a request
        both ways (GO line + pipe), tunnel_flush empties the pool (the live picture after a simulator update)"""
        saved = list(TUN["pool"]); TUN["pool"].clear()
        try:
            dead_a, dead_b = _socket.socketpair(); dead_b.close()                # the simulator closed this line
            mw_side, sim_side = _socket.socketpair()
            TUN["pool"].append((dead_a, time.time() - 5)); TUN["pool"].append((mw_side, time.time()))
            c = _tun_take()
            assert c is mw_side, "the open line must be taken"
            cl, cl_far = _socket.socketpair()                                 # a local program asks (like the door 18765)
            c.sendall(b"GO 8765\n"); _tun_pipe(cl, c)
            sim_side.settimeout(3); cl_far.settimeout(3)
            assert sim_side.recv(100).startswith(b"GO 8765"), "GO line"
            cl_far.sendall(b"ping"); assert sim_side.recv(100) == b"ping", "request through the tunnel"
            sim_side.sendall(b"pong"); assert cl_far.recv(100) == b"pong", "answer through the tunnel"
            sim_side.close(); cl_far.close()
            x_a, x_b = _socket.socketpair()
            TUN["pool"].append((x_a, time.time())); tunnel_flush()
            assert not TUN["pool"], "flush must empty the pool"
            x_b.settimeout(2); assert x_b.recv(10) == b"", "a flushed line is closed"
        finally:
            TUN["pool"].clear(); TUN["pool"].extend(saved)
    chk("Tunnel to the simulator (lines, GO, pipe, flush)", tun)
    chk("Own AI model: YOLO decoder + NMS (fake output)", own_ai_selftest)

    def wp():
        if not webpush_supported():
            return "skipped (python3-cryptography missing)"
        from cryptography.hazmat.primitives import hashes, hmac as chmac, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        ua = ec.generate_private_key(ec.SECP256R1()); auth = os.urandom(16)
        ua_pub = ua.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        body_ = _webpush_encrypt(b'{"t":1}', _b64u(ua_pub), _b64u(auth))

        def hm(k, d):
            h = chmac.HMAC(k, hashes.SHA256()); h.update(d); return h.finalize()
        salt, as_pub, ct = body_[:16], body_[21:86], body_[86:]
        sh = ua.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_pub))
        prk = hm(salt, hm(hm(auth, sh), b"WebPush: info\x00" + ua_pub + as_pub + b"\x01"))
        pt = AESGCM(hm(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]).decrypt(hm(prk, b"Content-Encoding: nonce\x00\x01")[:12], ct, None)
        assert pt == b'{"t":1}\x02'
    chk("Web push encryption (RFC 8291)", wp)

    def schema():
        miss = [k for _s, k, *_r in TOGGLES + SLIDERS if k not in CFG] + [k for _s, k, *_r in TEXTS if k not in CFG]
        secs = {x[0] for x in TOGGLES + SLIDERS + TEXTS} - set(SECTIONS)
        nde = [lab for _s, _k, lab, *_r in TOGGLES + SLIDERS + TEXTS if lab not in DE]
        assert not miss, f"settings without default: {miss}"
        assert not secs, f"sections missing in SECTIONS: {secs}"
        return f"{len(nde)} labels without German text" if nde else None
    chk("Settings schema", schema)

    def pages():
        node = shutil.which("node")
        names = ["WEB_PAGE", "CAMS_PAGE", "ZONES_PAGE", "REC_PAGE", "DIARY_PAGE", "HELP_PAGE", "LOG_PAGE", "GUEST_PAGE", "MSG_PAGE", "TL_PAGE"]
        n = 0
        for nm in names:
            html = render_page(globals()[nm], "live")
            for i, js in enumerate(re.findall(r"<script>(.*?)</script>", html, re.S)):
                if not node:
                    continue
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                    f.write(js); fn = f.name
                r = subprocess.run([node, "--check", fn], capture_output=True, text=True)
                os.remove(fn)
                assert r.returncode == 0, f"{nm} script {i}: {r.stderr.strip().splitlines()[-1] if r.stderr else 'error'}"
                n += 1
        return None if node else "JavaScript not checked (node missing)"
    chk("Web pages (render + JavaScript)", pages)
    chk("Timeline, weekly report, blur faces when sharing", verlauf_selftest)     # 2.98.14 (425, 426, 375)
    chk("One weekly report, return of the phone, auto-tuner ±20 % (migrations)", nachlauf_selftest)     # 2.98.15 (577)
    chk("Off in the push only with the PIN, push after a power cut, recordings by age, push without picture", sicher_selftest)   # (578)
    for _name, _fn in SELFTEST_EXTRA:                       # 2.98.18: further checks of other parts (395 …)
        chk(_name, _fn)

    if folder:
        def manifest():
            with open(os.path.join(folder, "versions.json"), encoding="utf-8") as f:
                m = json.load(f)
            bad = []
            for e in m.get("versions", []):
                p_ = os.path.join(folder, e["file"])
                if not os.path.isfile(p_):
                    continue
                with open(p_, "rb") as f:
                    sha = hashlib.sha256(f.read()).hexdigest()
                if sha != e.get("sha256") or not sig_ok(e["version"], e["file"], sha, e.get("sig")):
                    bad.append(e["version"])
            assert not bad, f"bad checksum / signature: {bad}"
            return f"{len(m.get('versions', []))} versions signed and checked"
        chk("versions.json signatures", manifest)
    ok = all(r[1] for r in res)
    for name, good, note in res:
        print(("✓ " if good else "✗ ") + name + (f" – {note}" if note else ""))
    print("Self-test " + ("OK" if ok else "FAILED") + f" (MoveEye {APP_VERSION})")
    return 0 if ok else 1


def make_manifest(folder, base_url, sign_key=""):
    """--make-manifest: write versions.json for all webcam_bewegung_X_Y_Z.py in a folder (to put on GitHub / a web server).
    --sign-key FILE: sign every version with the secret key in FILE (64 hex characters; never put this file on GitHub)."""
    base = (base_url or "").rstrip("/") + "/"
    seed = b""
    if sign_key:
        with open(os.path.expanduser(sign_key)) as f:
            seed = bytes.fromhex(f.read().strip())
        if not _ED:
            _ED.extend(_ed25519_impl())
        if _ED[0](seed).hex() != UPDATE_PUBKEY:
            print("Note: this key does not belong to the public key built into this program - devices will not accept the signatures.")
    out = []
    for it in sorted(local_versions(folder), key=lambda x: _vkey(x["version"]), reverse=True):
        with open(it["path"], "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        e = {"version": it["version"], "file": it["file"], "url": base + it["file"] if base_url else "", "sha256": sha,
             "date": it["date"], "notes": it["notes"]}
        if seed:
            e["sig"] = _ED[1](seed, _sig_msg(it["version"], it["file"], sha)).hex()
        out.append(e)
    p = os.path.join(folder, "versions.json")
    with open(p, "w") as f:
        json.dump({"app": "Motion Watch", "generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "versions": out}, f, indent=1, ensure_ascii=False)
    print(f"{p}: {len(out)} version(s)" + (", signed" if seed else ", NOT signed"))
    return 0


