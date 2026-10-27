#@ Motion Watch – Teil 140: Autostart. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Autostart: when switched on, the Pi starts Motion Watch when it boots (no screen needed) and switches the own Wi-Fi on.
# When switched off, nothing starts at boot and the Pi joins its known networks as usual (the own Wi-Fi never starts by itself).
#   normal user: systemd USER service  ~/.config/systemd/user/motionwatch.service  (+ "linger" so it starts without login)
#   root (sudo): systemd system service /etc/systemd/system/motionwatch.service
# ----------------------------------------------------------------------------
SERVICE_NAME = "motionwatch.service"
AUTOSTART = {"on": False, "mode": "", "msg": "", "path": ""}


def _is_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _run_user():
    import getpass
    return os.environ.get("SUDO_USER") or os.environ.get("USER") or getpass.getuser()


def _unit_path(mode):
    if mode == "system":
        return "/etc/systemd/system/" + SERVICE_NAME
    return os.path.join(os.path.expanduser("~"), ".config", "systemd", "user", SERVICE_NAME)


def _autostart_mode():
    return "system" if (_is_root() or os.path.isfile(_unit_path("system"))) else "user"


def _systemctl(mode, *args, timeout=30):
    return _run(["systemctl"] + (["--user"] if mode == "user" else []) + list(args), timeout)


INSTANCE = {"fd": None, "stopped": None}


def instance_lock(port):
    """Only one Motion Watch per web port (two would fight over camera, servos and port). True = we may run."""
    try:
        import fcntl
    except ImportError:
        return True
    p = os.path.join(tempfile.gettempdir(), f"motionwatch-{int(port)}.lock")
    try:
        fd = os.open(p, os.O_RDWR | os.O_CREAT, 0o666)
    except OSError:
        try:
            fd = os.open(p, os.O_RDONLY)
        except OSError:
            return True
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd); return False
    INSTANCE["fd"] = fd
    try:
        os.chmod(p, 0o666)
    except OSError:
        pass
    return True


def instance_takeover(port, gui):
    """Another Motion Watch holds the port. Started by hand with a window while the autostart service runs: ask and take
    over (the service is stopped now and started again when this window closes). Returns True when we may run."""
    url = f"http://127.0.0.1:{int(port)}/"
    mode = _autostart_mode()
    code, out, _e = _systemctl(mode, "is-active", SERVICE_NAME, timeout=10) if shutil.which("systemctl") else (1, "", "")
    service = out.strip() == "active"
    msg = (tr("Motion Watch is already running") + (" " + tr("in the background (autostart, without a window).") if service else ".")
           + "\n\n" + tr("Web page") + ": " + url)
    if not (gui and GUI_OK and service):
        print(msg.replace("\n\n", " - ")); return False
    try:
        r = tk.Tk(); r.withdraw()
        yes = messagebox.askyesno("Motion Watch", msg + "\n\n" + tr("Open the window here instead? The background service is stopped for "
                                  "that and starts again when you close the window."), parent=r)
        r.destroy()
    except Exception:
        yes = False
    if not yes:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
        return False
    c2, _o, e2 = _systemctl(mode, "stop", SERVICE_NAME, timeout=40)
    if c2 != 0:
        print(tr("The background service could not be stopped") + ": " + (e2 or "")[:160]); return False
    for _ in range(60):
        if instance_lock(port):
            INSTANCE["stopped"] = mode
            atexit.register(instance_restart_service)
            return True
        time.sleep(0.5)
    return False


def instance_restart_service():
    """The window closes: the autostart service takes over again (not when the Pi is shutting down)."""
    if INSTANCE.get("stopped") and not POWER.get("pending"):
        try:
            subprocess.Popen(["systemctl"] + (["--user"] if INSTANCE["stopped"] == "user" else []) + ["start", "--no-block", SERVICE_NAME],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError:
            pass


def autostart_args():
    """The options this program was started with, for the service (without one-time actions), plus --headless --boot."""
    drop = {"--print-service", "--install-service", "--allow-wifi", "--boot", "--headless", "--no-web", "--web"}
    return [x for x in sys.argv[1:] if x not in drop] + ["--headless", "--boot"]


HEART = {"t": time.time()}           # the camera loop is alive (systemd watchdog)
BEATS = {}                            # 2.95.35: name -> [last beat (monotonic), max. age s, label] of background tasks
REC_HEALTH = {"fail_t": 0.0, "fail_n": 0, "msg": ""}   # encoder trouble lately (for the health list)


def beat(name, max_age=120.0, label=""):
    """a background task says «I am alive» - the health list and the guard watch report it when it stops"""
    b = BEATS.get(name)
    if b is None:
        BEATS[name] = [time.monotonic(), float(max_age), label or name]
    else:
        b[0] = time.monotonic(); b[1] = float(max_age)


def _shift_times(obj, d, ref, depth=0):
    """after a jump of the system clock: move time stamps that mean «x seconds ago / in x seconds» along with it,
    so that cool-downs, holds and timers keep their length (2.95.35)"""
    near = lambda v: isinstance(v, float) and abs(v - ref) < 40 * 86400
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if near(v):
                obj[k] = v + d
        return
    try:
        items = list(vars(obj).items())
    except TypeError:
        return
    for k, v in items:
        if isinstance(v, bool):
            continue
        if near(v):
            setattr(obj, k, v + d)
        elif isinstance(v, deque) and v and isinstance(v[0], tuple) and v[0] and near(v[0][0]):
            setattr(obj, k, deque(((t[0] + d,) + tuple(t[1:]) for t in list(v)), maxlen=v.maxlen))
        elif depth == 0 and isinstance(v, list) and v and hasattr(v[0], "__dict__"):
            for o in list(v):
                _shift_times(o, d, ref, 1)
        elif depth == 0 and isinstance(v, dict) and v and all(isinstance(x, (int, float, str, type(None))) for x in v.values()):
            _shift_times(v, d, ref, 1)


def clock_guard_loop():
    """The Pi has no clock battery: the time is set later from the internet or the phone and jumps (hours, days).
    Timers measured with the wall clock would then fire at once or never - they are moved by the jump."""
    w0, m0 = time.time(), time.monotonic()
    while True:
        time.sleep(1.0)
        try:
            w, m = time.time(), time.monotonic()
            d = (w - w0) - (m - m0)
            if abs(d) > 5.0:
                ref = w0 + (m - m0)
                wa = WATCH_REF.get("w")
                objs = [ARM, LIGHTS, TEMPA, TOOLMODE, HEART]
                if wa is not None:
                    objs += [wa] + [getattr(wa, a_, None) for a_ in ("notifier", "ai", "patrol", "relays", "zwatch", "tracker", "tuner", "weather")]
                if "DETER" in globals():
                    objs.append(DETER)
                if PARTY.get("until"):
                    PARTY["until"] += d
                for o in objs:
                    if o is not None:
                        try:
                            _shift_times(o, d, ref)
                        except Exception:
                            pass
                log_event("sys", f"System clock jumped {d:+.0f} s - running timers adjusted")
            w0, m0 = w, m
        except Exception:
            w0, m0 = time.time(), time.monotonic()


GUARD_WATCH = {"bad": {}, "last_push": {}}
_GUARD_IDS = ("loop", "cam", "rec", "looprec", "bg", "disk", "push", "temp", "power", "batt", "store")


def guard_watch_loop():
    """every 30 s: something important failed while armed -> one push message (again after 6 h at the earliest);
    fixed again -> a short note"""
    time.sleep(90)
    while True:
        try:
            h = health_check()
            now = time.time(); w = WATCH_REF.get("w")
            bad = {x["id"]: x for x in h["items"] if x["level"] == "bad" and x["id"] in _GUARD_IDS}
            for k, x in bad.items():
                if k not in GUARD_WATCH["bad"]:
                    GUARD_WATCH["bad"][k] = now
                    log_event("sys", f"Health: {x['title']} - {x['text']}"[:200])
                if is_armed() and now - GUARD_WATCH["bad"][k] > 60 and now - GUARD_WATCH["last_push"].get(k, 0) > 6 * 3600 and w is not None:
                    GUARD_WATCH["last_push"][k] = now
                    w.notifier.alert("{name}: " + tr("Problem") + " – " + x["title"], (x["text"] + (" · " + x["tip"] if x.get("tip") else ""))[:300], None)
            for k in [k for k in GUARD_WATCH["bad"] if k not in bad]:
                GUARD_WATCH["bad"].pop(k, None)
                if GUARD_WATCH["last_push"].pop(k, None) and w is not None:
                    w.notifier.info(tr("Fixed again") + ": " + k)
        except Exception as e:
            print(f"guard watch: {e}")
        time.sleep(30)


def sd_notify(msg):
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return False
    import socket
    if addr[0] == "@":
        addr = "\0" + addr[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sk:
            sk.connect(addr); sk.sendall(msg.encode())
        return True
    except OSError:
        return False


def watchdog_loop():
    """Started by the autostart (systemd, WatchdogSec): "still alive" every 20 s while the camera loop runs. If the program
    hangs (e.g. a camera that blocks forever), systemd restarts it after 2 minutes."""
    if not os.environ.get("NOTIFY_SOCKET"):
        return
    while True:
        if time.time() - HEART["t"] < 60:
            sd_notify("WATCHDOG=1")
        time.sleep(20)


def autostart_unit(mode):
    import shlex
    exe = " ".join(shlex.quote(x) for x in [sys.executable, os.path.abspath(__file__)] + autostart_args())
    # StartLimitIntervalSec=0: never give up (e.g. after a power cut the camera / network may need a while)
    if mode == "system":
        head = ("[Unit]\nDescription=Motion Watch (camera surveillance)\nAfter=network.target NetworkManager.service\n"
                "Wants=NetworkManager.service\nStartLimitIntervalSec=0\n\n")
        install = "WantedBy=multi-user.target"
    else:
        head = "[Unit]\nDescription=Motion Watch (camera surveillance)\nStartLimitIntervalSec=0\n\n"
        install = "WantedBy=default.target"
    return (head + "[Service]\nType=simple\n" + f"WorkingDirectory={HERE}\nExecStart={exe}\n"
            + f"Environment=PYTHONUNBUFFERED=1\nEnvironment=MOTIONWATCH_HOME={DATA_DIR}\n"
            + "Restart=always\nRestartSec=5\nWatchdogSec=120\nNotifyAccess=main\n\n[Install]\n" + install + "\n")


def desktop_notice(title, text, wait=300):
    """A small message on the desktop of the Pi (notification bubble), also from the background service (often root, before
    anybody is logged in): waits up to `wait` seconds for the desktop session, then sends it as that user. Background thread."""
    def users():
        out = []
        for d in sorted(glob.glob("/run/user/*")):
            try:
                uid = int(os.path.basename(d))
            except ValueError:
                continue
            if (uid >= 1000 or uid == os.getuid()) and os.path.exists(os.path.join(d, "bus")):
                out.append(uid)
        if os.getuid() != 0:
            out = [u for u in out if u == os.getuid()]
        return out

    def send(uid):
        import pwd
        env = dict(os.environ, DBUS_SESSION_BUS_ADDRESS=f"unix:path=/run/user/{uid}/bus", XDG_RUNTIME_DIR=f"/run/user/{uid}")
        kw = {}
        if os.getuid() == 0 and uid != 0:
            try:
                pw_ = pwd.getpwuid(uid); kw = {"user": uid, "group": pw_.pw_gid}; env["HOME"] = pw_.pw_dir; env["USER"] = pw_.pw_name
            except KeyError:
                return False
        gq = lambda x: "'" + str(x).replace("\\", "\\\\").replace("'", "\\'") + "'"     # GVariant text for gdbus
        icon = os.path.join(tempfile.gettempdir(), "motionwatch_icon.png")
        try:
            if not os.path.exists(icon):
                with open(icon, "wb") as f:
                    f.write(app_icon_png(96))
                os.chmod(icon, 0o644)
        except Exception:
            icon = "camera-web"
        if shutil.which("notify-send"):
            cmd = ["notify-send", "-a", "Motion Watch", "-i", icon, "-t", "12000", title, text]
        elif shutil.which("gdbus"):
            cmd = ["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications", "--object-path", "/org/freedesktop/Notifications",
                   "--method", "org.freedesktop.Notifications.Notify", gq("Motion Watch"), "0", gq(icon), gq(title), gq(text), "[]", "{}", "12000"]
        else:
            return None                                      # nothing on this system can show a message
        try:
            return subprocess.run(cmd, env=env, capture_output=True, timeout=15, **kw).returncode == 0
        except (OSError, subprocess.SubprocessError, ValueError):
            return False

    def run():
        end = time.time() + wait
        while time.time() < end:
            for uid in users():
                r = send(uid)
                if r:
                    log_event("sys", "Desktop message shown: " + text[:80]); return
                if r is None:
                    return
            time.sleep(10)
    threading.Thread(target=run, daemon=True, name="desktop-notice").start()


def autostart_refresh():
    mode = _autostart_mode()
    path = _unit_path(mode)
    code, out, _e = _systemctl(mode, "is-enabled", SERVICE_NAME, timeout=10)
    AUTOSTART.update(on=out.strip() == "enabled", mode=mode, path=path if os.path.isfile(path) else "")
    STATE["autostart"] = dict(AUTOSTART)
    return STATE["autostart"]


def autostart_set(on):
    if shutil.which("systemctl") is None:
        return False, "autostart needs systemd (Raspberry Pi OS)"
    mode = _autostart_mode()
    path = _unit_path(mode)
    if mode == "system" and not _is_root():
        if on:
            return False, "a system service exists - change it with sudo, or remove it: sudo systemctl disable --now motionwatch"
        code, out, err = _systemctl(mode, "disable", SERVICE_NAME)
        ok = code == 0
        msg = "" if ok else "the system service can only be switched off with sudo: sudo systemctl disable motionwatch"
    elif on:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(autostart_unit(mode))
            os.chmod(path, 0o600)                         # the web password may be in the command line
        except OSError as e:
            return False, f"could not write {path}: {e}"
        _systemctl(mode, "daemon-reload")
        code, out, err = _systemctl(mode, "enable", SERVICE_NAME)
        ok, msg = code == 0, "" if code == 0 else (err or "systemctl enable failed")[:200]
        if ok and mode == "user":                         # start at boot even when nobody logs in
            c2, o2, e2 = _run(["loginctl", "enable-linger", _run_user()], 15)
            if c2 != 0:
                msg = ("autostart is on, but it only starts after a login until you run once: "
                       f"sudo loginctl enable-linger {_run_user()}   (or: sudo python3 {os.path.basename(__file__)} --allow-wifi)")
    else:
        code, out, err = _systemctl(mode, "disable", SERVICE_NAME)
        ok, msg = code == 0, "" if code == 0 else (err or "systemctl disable failed")[:200]
    if ok:
        CFG["autostart"] = on; save_settings()
        log_event("sys", "Autostart ON: starts at boot and switches the own Wi-Fi on" if on else
                         "Autostart OFF: nothing starts at boot, the Pi joins its known networks")
    AUTOSTART["msg"] = msg
    autostart_refresh()
    return ok, msg


def autostart_check_boot():
    """Autostart as a user service needs 'linger', otherwise it only starts after somebody logs in (e.g. not after a power
    cut without a desktop login). Checked at every start: switched on when allowed, otherwise a clear hint."""
    if not CFG["autostart"] or _autostart_mode() != "user" or shutil.which("loginctl") is None:
        return
    user = _run_user()
    code, out, _e = _run(["loginctl", "show-user", user, "-p", "Linger"], 10)
    if code == 0 and "Linger=yes" in out:
        return
    c2, _o, _e2 = _run(["loginctl", "enable-linger", user], 15)
    if c2 == 0:
        log_event("sys", "Autostart: start at boot without login switched on (linger)")
        return
    AUTOSTART["msg"] = ("autostart is on, but it only starts after a login until you run once: "
                        f"sudo loginctl enable-linger {user}   (or: sudo python3 {os.path.basename(__file__)} --allow-wifi)")
    log_event("sys", "Autostart: " + AUTOSTART["msg"])


def autostart_follow_version():
    """A new version was started by hand while autostart is on: let the service start this file from now on."""
    if not CFG["autostart"]:
        return
    mode = _autostart_mode()
    path = _unit_path(mode)
    if mode == "system" and not _is_root():
        return
    try:
        with open(path) as f:
            old = f.read()
    except OSError:
        return
    if old != autostart_unit(mode):                 # new file or new unit content (e.g. the watchdog of 1.8.2)
        try:
            with open(path, "w") as f:
                f.write(autostart_unit(mode))
            os.chmod(path, 0o600)
            _systemctl(mode, "daemon-reload")
            log_event("sys", f"Autostart now starts this version: {os.path.basename(__file__)}")
        except OSError:
            pass


def boot_hotspot():
    """Started at boot (--boot): switch the own Wi-Fi on. NetworkManager may still be starting, so try a few times."""
    def work():
        time.sleep(3.0)
        for attempt in range(8):
            ok, err = hotspot_set(True, persist=False)
            if ok:
                return
            WIFI["hs_msg"] = err
            time.sleep(10.0)
        log_event("sys", "Own Wi-Fi could not be switched on at boot")
    threading.Thread(target=work, daemon=True).start()


