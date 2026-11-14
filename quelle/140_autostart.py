#@ Motion Watch – Teil 140: Autostart. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Autostart: when switched on, the Pi starts MoveEye when it boots (no screen needed) and switches the own Wi-Fi on.
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
    """Only one MoveEye per web port (two would fight over camera, servos and port). True = we may run."""
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
    """Another MoveEye holds the port. Started by hand with a window while the autostart service runs: ask and take
    over (the service is stopped now and started again when this window closes). Returns True when we may run."""
    url = f"http://127.0.0.1:{int(port)}/"
    mode = _autostart_mode()
    code, out, _e = _systemctl(mode, "is-active", SERVICE_NAME, timeout=10) if shutil.which("systemctl") else (1, "", "")
    service = out.strip() == "active"
    msg = (tr("MoveEye is already running") + (" " + tr("in the background (autostart, without a window).") if service else ".")
           + "\n\n" + tr("Web page") + ": " + url)
    if not (gui and GUI_OK and service):
        print(msg.replace("\n\n", " - ")); return False
    try:
        r = tk.Tk(); r.withdraw()
        yes = messagebox.askyesno("MoveEye", msg + "\n\n" + tr("Open the window here instead? The background service is stopped for "
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


# Start watchdog (3.87.1, Besitzer 13.11.2026: «after the last two updates the page did not come back until I restarted the
# Pi» - ping worked, no port of MoveEye was open). Under systemd the web page must answer within START_WD_S after a start; if
# not, the threads are written to start_hang.txt (data folder) and the program ends with code 1: systemd starts it fresh
# (Restart=always: new process, its leftover child processes stopped - what the reboot did by hand). A known wait (the port is
# used by another program, 550 _serve) or no web page at all switches it off. «kill -USR1 <pid>» writes the threads into the
# journal at any time (also without systemd).
START_WD = {"on": False, "f": None, "last_hung": False}   # last_hung: the last start ended by this watchdog (390 run_guard)
START_WD_S = 90                 # before the systemd watchdog (WatchdogSec=120, counted from the last «alive» of the old program)


def start_watchdog_arm():
    import faulthandler
    try:
        faulthandler.register(signal.SIGUSR1, all_threads=True)
    except (AttributeError, ValueError, RuntimeError, OSError):
        pass
    p = os.path.join(DATA_DIR, "start_hang.txt")
    try:                                                   # the last start hung: tell it now (journal and log)
        if os.path.getsize(p) > 0:
            with open(p, encoding="utf-8", errors="replace") as f:
                kopf = f.readline()                        # «# start watchdog limit N s» (the dump follows)
                txt = f.read()[-4000:]
            os.replace(p, p + ".old")
            START_WD["last_hung"] = True                   # 3.87.1: no power loss - run_guard_start (390) must not count it
            m_ = re.search(r"^# start watchdog limit (\d+) s", kopf)
            lim_ = int(m_.group(1)) if m_ else START_WD_S
            print("The last start hung (web page not up after %d s) - where it was:\n%s" % (lim_, txt), flush=True)
            main = [ln.strip() for ln in txt.splitlines() if ln.strip().startswith("File ")][:3]
            log_event("sys", ("The last start hung (web page not up after %d s, started again by itself): %s"
                              % (lim_, " · ".join(main) or "?"))[:240])
    except OSError:
        pass
    if not (os.environ.get("NOTIFY_SOCKET") or os.environ.get("MW_START_WD")):
        return
    try:
        lim = float(os.environ.get("MW_START_WD") or START_WD_S)
    except ValueError:
        lim = START_WD_S
    try:
        START_WD["f"] = open(p, "w", encoding="utf-8")
        START_WD["f"].write("# start watchdog limit %d s\n" % round(max(5.0, lim))); START_WD["f"].flush()   # for the next start
        faulthandler.dump_traceback_later(max(5.0, lim), exit=True, file=START_WD["f"])
        START_WD["on"] = True
    except (OSError, ValueError, RuntimeError):
        pass


def start_watchdog_done(why=""):
    """the web page answers (or is not wanted / waits for a known reason): the start watchdog is not needed any more"""
    if not START_WD["on"]:
        return
    START_WD["on"] = False
    try:
        import faulthandler
        faulthandler.cancel_dump_traceback_later()
    except Exception:
        pass
    try:
        f = START_WD["f"]; START_WD["f"] = None
        if f is not None:
            f.close(); os.remove(f.name)
    except (OSError, AttributeError):
        pass


def start_watchdog_wait_web(port):
    """a thread: as soon as something answers on the web port, the start watchdog stops"""
    import socket

    def work():
        host = "127.0.0.1" if WEB_OPTS.get("bind") in ("", "0.0.0.0", "::") else WEB_OPTS.get("bind")
        while START_WD["on"]:
            try:
                with socket.create_connection((host, int(port)), timeout=2):
                    start_watchdog_done("web up")
                    return
            except OSError:
                time.sleep(0.5)
    threading.Thread(target=work, daemon=True, name="startwd").start()


def own_service(mode=None):
    """True when this process is the main process of the autostart service: then 550 never stops «the autostart copy» -
    after an update (os.execv, same PID) that copy is this program itself, and a stopped service is not started again
    (Besitzer 13.11.2026, user service: «Stopping motionwatch.service» in the same second as «MoveEye 3.87.0 started»)"""
    try:                                                   # the control group names the unit (system and user service)
        with open("/proc/self/cgroup") as f:
            if re.search(r"/" + re.escape(SERVICE_NAME) + r"(/|$)", f.read(), re.M):
                return True
    except OSError:
        pass
    if shutil.which("systemctl") is None:
        return False
    for m in ([mode] if mode else ["system", "user"]):
        rc, out, _e = _systemctl(m, "show", "-p", "MainPID", "--value", SERVICE_NAME, timeout=10)
        if rc == 0 and out.strip().isdigit() and int(out.strip()) == os.getpid():
            return True
    return False


def port_holders(port):
    """[(pid, parent pid, command line)] of the processes that hold a listening socket on this TCP port (Linux /proc;
    only the processes this user may look into). For the log when the web port is busy, and to stop a left-over child."""
    inodes = set()
    for fn in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(fn) as f:
                for ln in f.readlines()[1:]:
                    p = ln.split()
                    if len(p) > 9 and p[3] == "0A" and int(p[1].rsplit(":", 1)[1], 16) == int(port):
                        inodes.add("socket:[" + p[9] + "]")
        except (OSError, ValueError, IndexError):
            pass
    out = []
    if not inodes:
        return out
    try:
        pids = [x for x in os.listdir("/proc") if x.isdigit()]
    except OSError:
        return out
    for pid in pids:
        try:
            fds = os.listdir(f"/proc/{pid}/fd")
        except OSError:
            continue
        for fd in fds:
            try:
                if os.readlink(f"/proc/{pid}/fd/{fd}") in inodes:
                    with open(f"/proc/{pid}/stat") as f:
                        ppid = int(f.read().rsplit(")", 1)[1].split()[1])
                    with open(f"/proc/{pid}/cmdline", "rb") as f:
                        cmd = f.read().replace(b"\0", b" ").decode(errors="replace").strip()
                    out.append((int(pid), ppid, cmd[:200]))
                    break
            except (OSError, ValueError, IndexError):
                continue
    return out


def port_free_children(port):
    """the web port is busy: a child process of this program holds it (left over from before the update / pause -
    os.execv keeps the PID, so the children stay ours)? It is stopped. Returns what was found, for the log."""
    found = [h for h in port_holders(port) if h[0] != os.getpid()]
    for pid, ppid, cmd in found:
        if ppid == os.getpid():
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
            for _ in range(20):                              # 3.87.1: and collect it (no zombie left behind) - at most 2 s
                try:
                    if os.waitpid(pid, os.WNOHANG)[0] == pid:
                        break
                except ChildProcessError:
                    break
                time.sleep(0.1)
    return found


def port_foreign(held):
    """3.87.1 (Besitzer: «guarding without a web page is better than no guarding»): the holders of the web port that are a
    program other than MoveEye - not this process, not a child of it, not a MoveEye file (webcam_bewegung_X_Y_Z.py). Such a
    port does not get free by starting again: the start watchdog (above) must not end the guard for it."""
    def moveeye(cmd):                                        # the script it runs (first «….py»), not just any word of the line
        parts = str(cmd).split()
        script = next((x for x in parts[1:] if x.endswith(".py")), parts[0] if parts else "")
        return re.fullmatch(r"webcam_bewegung_\d{1,3}_\d{1,3}_\d{1,3}\.py", os.path.basename(script)) is not None
    if not any(h[0] for h in held):                          # 3.87.1: busy, but no holder we may look into (e.g. a program of root
        return [(0, 0, "")]                                  # while MoveEye runs as a user): a new start would not free it either
    return [(p, pp, c) for p, pp, c in held if p and p != os.getpid() and pp != os.getpid() and not moveeye(c)]



# One unit for both ways (Besitzer 14.11.2026, «system unit and user unit the same»): the user unit of the web page / window
# (~/.config/systemd/user, normal user + linger - the usual way) and the system unit of «sudo … --install-service»
# (/etc/systemd/system, einrichten.sh) come from autostart_unit() with the same options; they differ only in User=, After=
# and WantedBy=. ExecStart never names a version: it starts the small fixed starter START_FILE next to the program files,
# which starts the file named in START_PTR (written by the program that runs as the service, or by a version started by
# hand while autostart is on). An update therefore never has to touch the unit - the system unit (root) used to keep the
# old file and the old version came back at the next start of the Pi. An old unit (a file name in ExecStart, no watchdog)
# is rewritten once: by the service itself, as root or with «sudo -n» (Raspberry Pi OS: the first user may, as for 400
# power off), never with a stop of itself; without sudo a clear hint.
START_FILE = "moveeye_start.py"
START_PTR = "moveeye_start.json"
START_GOOD = "start_good.json"              # copy of the note in the data folder (MOTIONWATCH_HOME of the unit)
START_CODE = r"""#!/usr/bin/env python3
# MoveEye starter (written by MoveEye, the autostart service starts it - do not change). Starts ONLY a program file whose
# size and SHA-256 match what MoveEye recorded: first the file in moveeye_start.json (the version that runs as the service,
# or the one started by hand while autostart is on), then the last good versions of that note, also from the copy
# $MOTIONWATCH_HOME/start_good.json. A file that is not recorded or does not match (newer, changed, half written) is never
# started; if nothing matches, it ends with an error (systemd tries again; start MoveEye once by hand to record it again).
# Same process (exec): systemd sees MoveEye itself (watchdog, stop).
import hashlib, json, os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
name_re = re.compile(r"^webcam_bewegung_\d{1,3}_\d{1,3}_\d{1,3}\.py$")


def load(p):
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def checked(c):
    n = os.path.basename(str(c.get("file") or ""))
    p = os.path.join(here, n)
    try:
        if not (name_re.match(n) and os.path.getsize(p) == int(c.get("size", -1))):
            return ""
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
    except (OSError, ValueError, TypeError):
        return ""
    return p if h.hexdigest() == str(c.get("sha256") or "").lower() else ""


recs = [load(os.path.join(here, "moveeye_start.json"))]
if os.environ.get("MOTIONWATCH_HOME"):
    recs.append(load(os.path.join(os.environ["MOTIONWATCH_HOME"], "start_good.json")))
cands = [d for d in recs if d.get("file")] + [g for d in recs for g in (d.get("good") or []) if isinstance(g, dict)]
path, bad = "", []
for c in cands:
    path = checked(c)
    if path:
        break
    bad.append(os.path.basename(str(c.get("file") or "?")))
if not path:
    sys.exit("MoveEye starter: NO program file matches its recorded checksum in " + here + " (checked: " +
             (", ".join(dict.fromkeys(bad)) or "no note moveeye_start.json / start_good.json") +
             ") - nothing is started. Start MoveEye once by hand (or sudo ... --install-service) to record the file.")
note = ""
if not recs[0].get("file"):
    note = "moveeye_start.json missing or damaged - used the copy in the data folder"
if bad:
    note = (note + "; " if note else "") + "not started (checksum does not match the record): " + ", ".join(dict.fromkeys(bad))
if note:
    note = "MoveEye starter: " + note + " - started " + os.path.basename(path)
    print(note, file=sys.stderr, flush=True)
    os.environ["MW_STARTER_NOTE"] = note
os.execv(sys.executable, [sys.executable, path] + sys.argv[1:])
"""


def _owner_like_here(p):
    """written as root (sudo … --install-service): the file belongs to the owner of the program folder, like the program"""
    if _is_root():
        try:
            st = os.stat(HERE)
            os.chown(p, st.st_uid, st.st_gid)
        except OSError:
            pass


def start_launcher_ensure():
    """the fixed starter next to the program files (the unit starts it, never a file of one version) -> its path"""
    p = os.path.join(HERE, START_FILE)
    try:
        with open(p, encoding="utf-8") as f:
            if f.read() == START_CODE:
                return p
    except OSError:
        pass
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(START_CODE)
    os.chmod(tmp, 0o644)
    _owner_like_here(tmp)
    os.replace(tmp, p)
    return p


def _file_rec(path):
    """{file, sha256, size} of a program file (what the starter checks before it starts it)"""
    h, n = hashlib.sha256(), 0
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b); n += len(b)
    return {"file": os.path.basename(path), "sha256": h.hexdigest(), "size": n}


def start_pointer_set(path=None, good=True):
    """from now on the starter starts THIS program file (or `path`: the start guard of 390 going back to the old version).
    Records its size and SHA-256 - the starter starts nothing else; good=True also puts it at the top of the «last good»
    list (not while it is on trial after an update: 390 adds it after its 90 s). Only a file next to the starter.
    Written next to the starter and as a copy in the data folder. True when the note changed.
    Why hashes and no signature in the starter: the note is written only by MoveEye itself - for a version that it installed
    after checking the signature (390 update_install) or that the owner started by hand. Whoever can write the note can also
    replace the program files and the starter in the same folder, so a signature check in the starter would not stop that
    person; what the hash stops is what really happens: a file that is not the recorded one (an unsigned or half-written
    download, a copied-in or changed file, a damaged card) being started just because its name looks newer."""
    p = os.path.join(HERE, START_PTR)
    path = os.path.abspath(path or __file__)
    if os.path.dirname(path) != os.path.abspath(HERE):
        return False
    rec = _file_rec(path)
    try:
        with open(p, encoding="utf-8") as f:
            old = json.load(f)
        if not isinstance(old, dict):
            old = {}
    except (OSError, ValueError):
        old = {}
    if not old.get("good"):
        try:
            with open(os.path.join(DATA_DIR, START_GOOD), encoding="utf-8") as f:
                old = dict(json.load(f), file=old.get("file"))
        except (OSError, ValueError, TypeError):
            pass
    gl = [g for g in (old.get("good") or []) if isinstance(g, dict) and g.get("file")]
    if good:
        gl = [rec] + [g for g in gl if g.get("file") != rec["file"]]
    new = dict(rec, good=gl[:5])
    if all(old.get(k) == new[k] for k in new):
        return False
    new["set"] = datetime.now().isoformat(timespec="seconds")
    for dst in (p, os.path.join(DATA_DIR, START_GOOD)):
        try:
            with open(dst + ".tmp", "w", encoding="utf-8") as f:
                json.dump(new, f, indent=1)
            os.chmod(dst + ".tmp", 0o644)
            if dst == p:
                _owner_like_here(dst + ".tmp")
            os.replace(dst + ".tmp", dst)
        except OSError:
            if dst == p:
                raise
    return True


def start_on_trial():
    """this version was just installed by an update and has not yet run its 90 s (390 start_guard)"""
    try:
        with open(os.path.join(DATA_DIR, "update_guard.json")) as f:
            return json.load(f).get("new") == APP_VERSION
    except (OSError, ValueError, AttributeError):
        return False


def autostart_unit(mode):
    """the unit text for «user» (~/.config/systemd/user) or «system» (/etc/systemd/system) - one generator for both"""
    import shlex
    exe = " ".join(shlex.quote(x) for x in [sys.executable, os.path.join(HERE, START_FILE)] + autostart_args())
    user = _run_user() if mode == "system" else ""
    # StartLimitIntervalSec=0: never give up (e.g. after a power cut the camera / network may need a while)
    return ("[Unit]\nDescription=MoveEye (camera surveillance)\n"
            + ("After=network.target NetworkManager.service\nWants=NetworkManager.service\n" if mode == "system" else "")
            + "StartLimitIntervalSec=0\n\n[Service]\nType=simple\n"
            + (f"User={user}\n" if user and user != "root" else "")
            + f"WorkingDirectory={HERE}\nExecStart={exe}\n"
            + f"Environment=PYTHONUNBUFFERED=1\nEnvironment=MOTIONWATCH_HOME={DATA_DIR}\n"
            + "Restart=always\nRestartSec=5\nWatchdogSec=120\nNotifyAccess=main\n\n[Install]\n"
            + ("WantedBy=multi-user.target" if mode == "system" else "WantedBy=default.target") + "\n")


def _systemctl_log(mode, *args, timeout=30):
    """systemctl, and a line in the log when it fails (an unseen failed daemon-reload kept the old unit, Nov. 2026)"""
    code, out, err = _systemctl(mode, *args, timeout=timeout)
    if code != 0:
        log_event("sys", f"systemctl {'--user ' if mode == 'user' else ''}{' '.join(args)} failed ({code}): {(err or out).strip()[:160]}")
    return code, out, err


def _unit_write(mode, path, text):
    """write the unit and daemon-reload (never a stop / restart: this program may be the service itself). The system
    unit as a user: with «sudo -n» (no password question). -> "" or the reason it did not work"""
    if mode == "user" or _is_root():
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path + ".tmp", "w") as f:
                f.write(text)
            os.chmod(path + ".tmp", 0o600)                 # the web password may be in the command line
            os.replace(path + ".tmp", path)
        except OSError as e:
            return f"could not write {path}: {e}"
        code, _o, err = _systemctl_log(mode, "daemon-reload")
        return "" if code == 0 else f"systemctl daemon-reload failed: {err[:120]}"
    if shutil.which("sudo") is None:
        return "no sudo"
    fd, tmp = tempfile.mkstemp(prefix="motionwatch-unit-", suffix=".service")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        code, _o, err = _run(["sudo", "-n", "install", "-m", "600", "-o", "root", "-g", "root", tmp, path], 20)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    if code != 0:
        return f"sudo -n install: {err.strip()[:120] or code}"
    code, _o, err = _run(["sudo", "-n", "systemctl", "daemon-reload"], 30)
    return "" if code == 0 else f"sudo -n systemctl daemon-reload: {err.strip()[:120] or code}"


def dienst_selftest():
    """one unit generator for the user and the system service (same options, never a file of one version in ExecStart) and
    the starter picks the noted program file, else the newest (only for --self-test)"""
    u, sy = autostart_unit("user"), autostart_unit("system")
    for k in ("Restart=always", "RestartSec=5", "WatchdogSec=120", "NotifyAccess=main", "StartLimitIntervalSec=0", "Type=simple",
              "Environment=PYTHONUNBUFFERED=1", "Environment=MOTIONWATCH_HOME=", "--boot", "--headless", START_FILE):
        assert k in u and k in sy, "unit option missing: " + k
    assert "WantedBy=default.target" in u and "WantedBy=multi-user.target" in sy and "User=" not in u
    import shlex
    for t in (u, sy):
        ex = shlex.split(next(x for x in t.splitlines() if x.startswith("ExecStart="))[len("ExecStart="):])
        assert ex[1] == os.path.join(HERE, START_FILE), "the unit starts the starter, never the file of one version"
    d, h2 = tempfile.mkdtemp(prefix="mw_starter_"), tempfile.mkdtemp(prefix="mw_starter_home_")
    try:
        with open(os.path.join(d, START_FILE), "w") as f:
            f.write(START_CODE)
        for v in ("3_9_0", "3_10_0"):
            with open(os.path.join(d, f"webcam_bewegung_{v}.py"), "w") as f:
                f.write("import sys; print('RUN', __file__.rsplit('_', 3)[1:], sys.argv[1:])\n")
        r9, r10 = (_file_rec(os.path.join(d, f"webcam_bewegung_{v}.py")) for v in ("3_9_0", "3_10_0"))

        def note(rec, good, where=d):
            with open(os.path.join(where, START_PTR if where == d else START_GOOD), "w") as f:
                json.dump(dict(rec, good=good), f)

        def run():
            r = subprocess.run([sys.executable, os.path.join(d, START_FILE), "--boot"], capture_output=True, text=True, timeout=30,
                               env=dict(os.environ, MOTIONWATCH_HOME=h2))
            return r.returncode, r.stdout.strip(), r.stderr
        rc, out, err = run()
        assert rc != 0 and "RUN" not in out and "NO program file" in err, "without a note nothing is started (not «the newest»)"
        note(r9, [r9, r10])
        assert run()[1] == "RUN ['3', '9', '0.py'] ['--boot']", "the noted file, options passed on"
        with open(os.path.join(d, "webcam_bewegung_3_9_0.py"), "a") as f:
            f.write("# changed\n")
        rc, out, err = run()
        assert out.startswith("RUN ['3', '10', '0.py']") and "checksum does not match" in err, "a changed file: the last good one, said loudly"
        os.remove(os.path.join(d, START_PTR))
        note(r10, [r10], h2)
        with open(os.path.join(d, "webcam_bewegung_3_11_0.py"), "w") as f:
            f.write("print('RUN', 'NEWER')\n")
        rc, out, err = run()
        assert out.startswith("RUN ['3', '10', '0.py']") and "NEWER" not in out, "no note + a newer unrecorded file: the copy decides"
    finally:
        shutil.rmtree(d, ignore_errors=True); shutil.rmtree(h2, ignore_errors=True)
    return "user + system unit alike, starter ok"


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
            cmd = ["notify-send", "-a", "MoveEye", "-i", icon, "-t", "12000", title, text]
        elif shutil.which("gdbus"):
            cmd = ["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications", "--object-path", "/org/freedesktop/Notifications",
                   "--method", "org.freedesktop.Notifications.Notify", gq("MoveEye"), "0", gq(icon), gq(title), gq(text), "[]", "{}", "12000"]
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
            start_launcher_ensure(); start_pointer_set()  # the unit starts the starter, the starter this file
        except OSError as e:
            return False, f"could not write {START_FILE} next to the program: {e}"
        err = _unit_write(mode, path, autostart_unit(mode))
        if err.startswith("could not write"):
            return False, err
        code, out, err = _systemctl_log(mode, "enable", SERVICE_NAME)
        ok, msg = code == 0, "" if code == 0 else (err or "systemctl enable failed")[:200]
        if ok and mode == "user":                         # start at boot even when nobody logs in
            c2, o2, e2 = _run(["loginctl", "enable-linger", _run_user()], 15)
            if c2 != 0:
                msg = ("autostart is on, but it only starts after a login until you run once: "
                       f"sudo loginctl enable-linger {_run_user()}   (or: sudo python3 {os.path.basename(__file__)} --allow-wifi)")
    else:
        code, out, err = _systemctl_log(mode, "disable", SERVICE_NAME)
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
    """At every start: the service starts THIS file from now on, when this program is the service itself (e.g. after an
    update: os.execv, same PID) or was started by hand while autostart is on. Only the note START_PTR changes; the unit is
    rewritten only when its text is not the one of this version (an older unit: a file name in ExecStart, no watchdog) -
    a system unit as the user with «sudo -n», without it a hint (the next start of the Pi would bring the old version)."""
    mode = _autostart_mode()
    path = _unit_path(mode)
    if not os.path.isfile(path):
        return
    if not (CFG["autostart"] or own_service(mode)):
        return
    note = os.environ.pop("MW_STARTER_NOTE", "")
    if note:                                             # the starter did not take the noted file: say it loudly
        log_event("sys", note[:300]); print(note)
        STATE["starter_note"] = note
    try:
        start_launcher_ensure()
        if start_pointer_set(good=not start_on_trial()):
            log_event("sys", f"Autostart now starts this version: {os.path.basename(__file__)}")
    except OSError as e:
        log_event("sys", f"Autostart: {START_FILE} / {START_PTR} not written: {e}"[:200]); return
    try:
        with open(path) as f:
            old = f.read()
    except OSError:
        old = None                                       # a system unit the user may not read (sudo … chmod 600)
    new = autostart_unit(mode)
    if old == new:
        return
    if old is None and mode == "system" and not _is_root():
        code, out, _e = _systemctl(mode, "show", "-p", "ExecStart", "--value", SERVICE_NAME, timeout=10)
        if code == 0 and START_FILE in out and "--boot" in out:
            return                                       # already the starter (the text itself is root's)
    err = _unit_write(mode, path, new)
    if err:
        AUTOSTART["msg"] = (f"the autostart service still has an older unit file ({err}) - the next start of the Pi may bring an "
                            f"older version. Run once: sudo {sys.executable} {os.path.abspath(__file__)} --install-service")
        log_event("sys", "Autostart: " + AUTOSTART["msg"][:300])
    else:
        log_event("sys", f"Autostart: unit {path} updated (starter {START_FILE}, watchdog) - the service keeps running")


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


