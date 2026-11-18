#@ MoveEye – Teil 639zzzzw: «Demo beim Host» (--host-modus): die Demo auf dem Webspace des Besitzers (moveeye.kevlaschef.com/demo/) – Sperren (kein Netz nach aussen, keine Programme, keine Hardware, Dateien nur im eigenen Ordner), Pfad-Vorsilbe «/demo» (Server + kleines Skript in jeder Seite), Simulator über eine WebSocket-Leitung (/simtun). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Besitzer (15.11.2026, approved): a public demo of MoveEye on the web host behind the Basic Auth of the homepage.
#   4.15.0 (Besitzer 16.11.2026): no longer a demo but a REAL MoveEye on the host - the web simulator of the homepage is its
#   camera; without it the normal «no camera» picture (with --demo still the drawn scene). Settings and recordings stay
#   (no nightly reset; the folder stays under ~1 GB through the normal clean-up, oldest recordings first: _host_fixed);
#   motion detection only, no AI model (person detector, BioCLIP, Blinki, voices: «not available on the host», RAM); no push.
#   4.16.0 (Besitzer 18.11.2026, the host has 1.5 GB RAM / 2 GB disk): the AI detection (person / animal / vehicle) is back -
#   its model only from its fixed source with fixed checksums, from its own thread (host_ai_download); Blinki, BioCLIP and
#   the voices stay off. Continuous recording + time-lapse together at most 300 MB (host_media_trim). The tab of the web
#   simulator in the background («VIS hidden»): the last picture stays, nothing is asked, the line holds, no watchdog banner.
#   Started by demo_start.py (repository root) with  --headless --bind 127.0.0.1 --port $PORT --host-modus
#   --url-prefix /demo --config <folder>/demo_daten. demo_start.py picks the newest signed version and updates it every
#   6 h (only signed files) - this part is what MoveEye itself does in host mode:
#   * Locks (central, so no single function can forget them; they hold for every visitor, also the administrator):
#       - network: no connection out of this computer (socket connect / sendto) and no listening on the network (bind only
#         127.0.0.1 / ::1). That switches off push (ntfy, Telegram, e-mail, web push, webhooks, MQTT), the homepage upload,
#         the tunnel listener, the AI helper server, the game servers on 0.0.0.0, the simulator beacon / UDP search and
#         every download.
#       - programs: subprocess only ffmpeg / ffprobe, also behind «nice -n N» (no shell, nmcli, sudo, systemctl, ...); os.system
#         is off; os.exec* only restarts this same program file.
#       - hardware: the modules for GPIO / I2C / SPI / Pi camera / Bluetooth / D-Bus / serial / audio are not importable.
#       - files: writing, deleting and renaming only inside the demo folder (--config) and the temporary folder.
#       - the web page refuses (403 «not available on the host», host_guard) the routes in HOST_BLOCK and DEMO_BLOCK (210)
#         except the backpack (/api/tausch, with small limits), and every AI route (HOST_AI, /untersuchen, /tausch/bio).
#       - settings that reach outside or the system are put back after every request and every 2 s (_host_fixed).
#   * Path prefix: the host passes the requests WITHOUT «/demo». With a prefix (--url-prefix, or the header
#     X-Forwarded-Prefix) a small WSGI layer (_HostPrefix) puts it in front of every absolute address the page uses:
#     Location headers of redirects, cookie paths, the addresses in HTML / JavaScript / CSS / manifest («"/api/…"»,
#     «href="/"», «url(/…)», for every first path segment the server knows), and a small script at the top of each page
#     (HOST_SHIM_JS) catches what is built at run time: fetch, XMLHttpRequest, EventSource, WebSocket, window.open,
#     sendBeacon, history, src / href / action of elements, setAttribute, innerHTML, clicks on links, form posts and (where
#     the browser has the Navigation API) location.href = "/…". The service worker stays off (it could otherwise take over
#     the whole homepage). Without a prefix none of this is installed: normal MoveEye is exactly as before.
#   * Simulator: the web simulator of the homepage connects to wss://<homepage>/demo/simtun (relative to the page). It speaks
#     one WebSocket that carries many HTTP connections («MWTUN2», protocol in _HostWsMux; unlike the TCP tunnel of 180 it
#     needs no new connection per request - MoveEye posts /state 10 times a second). The code is not checked in host mode
#     (every visitor is administrator); the newest simulator window wins, the older one gets «TAKEN». MoveEye reaches it
#     through the local door 127.0.0.1:18765 (sim_url, as with the tunnel); connected, the simulation switches on by itself
#     (sim_set, armed again), gone for 60 s it switches off («no camera» again; with --demo the drawn scene).
#   * RAM / CPU: nothing new runs in the background except one small thread (every 2 s). The rewritten pages are cached.
# Tests: werkzeuge/host_demo_test.py (static + a short run behind a proxy that strips «/demo»), werkzeuge/demo_start_test.py.
# ----------------------------------------------------------------------------
HOST = {"on": False, "prefix": "", "data": "", "roots": (), "door": "", "sim_auto": False, "ws": 0, "blocked": {}, "fixed_t": 0.0}
# Main file small (coordinator 16.11.2026): the code of this part is ONE literal - werkzeuge/bauen.py moves it into the data
# zip, it runs here at its place. The zip is vouched for by ZD_SHA256 of this signed file. Without the zip there is no host
# mode at all: 640 refuses --host-modus (fail closed) - nothing of start, protection, alarm, update or repair is in here.
HOST_PY = r'''HOST_PROGS = ("ffmpeg", "ffprobe")
HOST_NO_MODULES = ("RPi", "gpiozero", "lgpio", "pigpio", "smbus", "smbus2", "spidev", "picamera2", "libcamera", "senxor", "pysenxor",
                   "board", "busio", "digitalio", "adafruit_pca9685", "adafruit_servokit", "adafruit_blinka", "bluetooth", "dbus",
                   "pydbus", "gi", "serial", "usb", "evdev", "pyaudio", "sounddevice", "alsaaudio", "paramiko", "pysftp")
HOST_BLOCK = ("/api/homepage", "/api/tunnel", "/api/helper", "/api/nettest", "/api/notify_test", "/api/report/send", "/api/sms",
              "/api/storage", "/api/usb", "/api/soundev", "/api/talk", "/api/piper", "/api/homekit", "/api/smalltv",
              "/api/sim/upload", "/api/own_model", "/api/fehler/fix", "/api/turbo", "/api/radio", "/api/dev", "/api/simhub",
              "/api/simintern", "/api/webpush", "/api/update", "/api/fbx/flush", "/api/relay", "/api/disco", "/api/light",
              "/api/tausch/smb", "/api/storm_test", "/api/seclogin", "/api/push")
HOST_FPS = 4.0                            # pictures per second of the drawn scene (normally 15): the host gives half a core
HOST_SIM_DOOR = 18765                     # the same door as the tunnel of 180 (sim_url http://127.0.0.1:18765, _tun_reclaim)
HOST_WS_MAX = 8 * 1024 * 1024             # one WebSocket message of the simulator (a camera picture is ~100 KB)
HOST_WS_LINES = 4                         # simulator windows at the same time (the newest one is used)
HOST_AI_EVERY = 3                         # the AI looks at every 3rd picture (4.16.0: measured with --kern 0.5, the live picture keeps its rate)
HOST_MEDIA_BYTES = 300 * 1024 * 1024      # 4.16.0: continuous recording + time-lapse together (oldest first), apart from the 0.5 GB of
                                          # the alarm recordings, the 400 MB of the games and the 0.2 GB of the backpack
_HOST_REAL = {}


def _host_fixed():
    """settings that never change in host mode (those that reach outside, the system or other folders)"""
    d = {"record_dir": os.path.join(HOST["data"] or DATA_DIR, "recordings"), "record_max_gb": 0.5,
         "tausch_total_gb": 0.2, "tausch_user_gb": 0.2, "tausch_file_mb": 50.0,    # 4.15.0: the folder stays under ~1 GB (oldest first)
         "update_mode": "off", "update_url": "", "update_token": "", "update_unsigned": False, "sim_url": f"http://127.0.0.1:{HOST_SIM_DOOR}",
         "sim_auto": False, "sim_autostart": False, "hotspot_on": False, "mqtt_on": False, "backup_type": "off", "backup_url": "",
         "fleet": [], "helper_serve": False, "helper_use": False, "helper_url": "", "tunnel_on": False, "notify_on": False,
         "email_on": False, "sms_on": False, "webpush_on": False, "hp_base": "", "hp_key": "", "hp_auto": False, "hp_public": "",
         "web_password": "", "web_pw_hash": "", "map_online": False, "ai_own_url": "", "lock_on": False, "source": None,
         "web_quality": 60, "web_width": 640, "proc_width": 320, "ai_every": HOST_AI_EVERY, "sim_fps": 4, "sim_eco": True,
         "timelapse_max_gb": HOST_MEDIA_BYTES / 1024 ** 3}   # half a core: fewer / smaller pictures (measured with werkzeuge/host_demo_test.py --ram)
    # 4.16.0 (Besitzer 18.11.2026, the host has 1.5 GB RAM / 2 GB disk): AI detection (person / animal / vehicle), continuous
    # recording and time-lapse are free again (ai_enabled, loop_on, timelapse_on no longer fixed); loop + time-lapse share 300 MB
    return {k: v for k, v in d.items() if k in CFG}


def host_enforce(save=False):
    """put the fixed settings back (after every request and every 2 s); «source» stays the web simulator or «no camera»"""
    if not HOST["on"]:
        return 0
    n = 0
    for k, v in _host_fixed().items():
        if k == "source":
            if not (CFG["source"] == host_idle_source() or (CFG.get("sim_on") and str(CFG["source"]).startswith("sim:"))):
                CFG["source"] = host_idle_source(); n += 1
            continue
        if CFG.get(k) != v:
            CFG[k] = v; n += 1
    if n and save:
        try:
            save_settings()
        except Exception:
            pass
    HOST["fixed_t"] = time.time()
    return n


def _host_note(what):
    """remember a refused action (logged once per minute by _host_loop). Never log_event here: the guards are hit inside
    code that holds LOCK (e.g. /api/state -> health_check -> dmesg), and log_event takes LOCK too - that was a deadlock."""
    now = time.time()
    if now - HOST["blocked"].get(what, 0.0) > 60:
        HOST["blocked"][what] = now
        HOST.setdefault("notes", deque(maxlen=50)).append(what)


def _host_notes_flush():
    q = HOST.get("notes")
    while q:
        try:
            log_event("sys", f"Host mode: refused {q.popleft()}"[:200])
        except Exception:
            break


def _host_ip_ok(host):
    h = str(host or "").strip().strip("[]").lower().split("%")[0]
    if h == "localhost":
        return True
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        return False
    if getattr(ip, "ipv4_mapped", None) is not None:
        ip = ip.ipv4_mapped
    return ip.is_loopback


def _host_inet(sk):
    import socket as _s
    return getattr(sk, "family", None) in (_s.AF_INET, _s.AF_INET6)


def _host_guard_sockets():
    import socket as _s, errno as _er
    if "connect" in _HOST_REAL:
        return
    _HOST_REAL.update(connect=_s.socket.connect, connect_ex=_s.socket.connect_ex, sendto=_s.socket.sendto, bind=_s.socket.bind,
                      getaddrinfo=_s.getaddrinfo)

    def getaddrinfo(host, port, *a, **k):              # 4.15.1: remember the addresses of GitHub for the game downloads
        r = _HOST_REAL["getaddrinfo"](host, port, *a, **k)
        kind = _host_dl_kind()                           # 4.16.0: and of the fixed source of the AI model for its own thread
        if kind and str(host or "").lower().rstrip(".") in HOST_DL_HOSTS[kind]:
            HOST.setdefault(kind, set()).update(str(x[4][0]) for x in r)
        return r

    def connect(self, addr):
        if _host_inet(self) and _host_net_ok(addr):
            return _HOST_REAL["connect"](self, addr)
        if _host_inet(self) and not _host_ip_ok(addr[0] if isinstance(addr, tuple) else addr):
            _host_note(f"a connection to {str(addr)[:60]}")
            raise PermissionError(_er.EACCES, "host mode: no connections out of this computer")
        return _HOST_REAL["connect"](self, addr)

    def connect_ex(self, addr):
        if _host_inet(self) and _host_net_ok(addr):
            return _HOST_REAL["connect_ex"](self, addr)
        if _host_inet(self) and not _host_ip_ok(addr[0] if isinstance(addr, tuple) else addr):
            _host_note(f"a connection to {str(addr)[:60]}")
            return _er.EACCES
        return _HOST_REAL["connect_ex"](self, addr)

    def sendto(self, data, *args):
        addr = args[-1] if args else None
        if _host_inet(self) and isinstance(addr, tuple) and not _host_ip_ok(addr[0]):
            _host_note(f"a message to {str(addr)[:60]}")
            raise PermissionError(_er.EACCES, "host mode: no messages out of this computer")
        return _HOST_REAL["sendto"](self, data, *args)

    def bind(self, addr):
        if _host_inet(self) and isinstance(addr, tuple) and not _host_ip_ok(addr[0]):
            _host_note(f"listening on {str(addr)[:60]}")
            raise PermissionError(_er.EACCES, "host mode: listening only on 127.0.0.1")
        return _HOST_REAL["bind"](self, addr)
    _s.socket.connect, _s.socket.connect_ex, _s.socket.sendto, _s.socket.bind = connect, connect_ex, sendto, bind
    _s.getaddrinfo = getaddrinfo


# 4.15.1 (Besitzer 17.11.2026): games on the host - the game downloads (collection, Amazon Queen, the other ready games) may
# reach GitHub: only these host names, only https (443), only from their own download threads; the files keep their fixed
# checksums (320 / 639zzg / 639zzn). Everything else stays blocked.
HOST_GH = ("github.com", "raw.githubusercontent.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com",
           "codeload.github.com")
HOST_DL_THREADS = ("games-dl", "fspiele-dl", "fotaq-dl")
# 4.16.0 (Besitzer 18.11.2026): the AI model (SSD MobileNet V2) from its one fixed source, only from its own thread «ai-model»,
# with fixed checksums (host_ai_download) - the same gate as the games: host names, https, thread, then the addresses it resolved
HOST_AI_THREAD = "ai-model"
HOST_DL_HOSTS = {"gh_ips": HOST_GH, "ai_ips": ("storage.googleapis.com", "raw.githubusercontent.com")}
_HOST_TL = threading.local()


def _host_dl_kind():
    """which download may go out of this thread: "gh_ips" (games), "ai_ips" (AI model) or "" (none)"""
    n = threading.current_thread().name
    if getattr(_HOST_TL, "dl", False) or n in HOST_DL_THREADS:
        return "gh_ips"
    return "ai_ips" if n == HOST_AI_THREAD else ""


def _host_dl_thread():
    return bool(_host_dl_kind())


def _host_net_ok(addr):
    kind = _host_dl_kind()
    if not (isinstance(addr, tuple) and len(addr) >= 2 and addr[1] == 443 and kind):
        return False
    return str(addr[0]).split("%")[0] in HOST.get(kind, ())


def _host_guard_programs():
    import errno as _er
    if "Popen" in _HOST_REAL:
        return
    real = _HOST_REAL["Popen"] = subprocess.Popen

    class HostPopen(real):
        def __init__(self, args, *a, **k):
            al = [args] if isinstance(args, (str, bytes, os.PathLike)) else list(args)
            name = os.path.basename(os.fsdecode((al[:1] or [""])[0])).lower()
            if name == "nice" and not k.get("shell"):          # 4.14.1: «nice -n N ffmpeg …» (recording, conversion, time-lapse)
                i = 1
                while i < len(al) and str(al[i]).startswith("-"):
                    i += 2 if str(al[i]) == "-n" else 1
                name = os.path.basename(os.fsdecode(al[i])).lower() if i < len(al) else "nice"
            if k.get("shell") or name not in HOST_PROGS:
                _host_note(f"the program {name[:40] or '?'}")
                raise FileNotFoundError(_er.ENOENT, "host mode: this program is not allowed", name)
            super().__init__(args, *a, **k)
    subprocess.Popen = HostPopen

    def no_system(cmd):
        _host_note(f"the command {str(cmd)[:40]}")
        return 127 << 8
    os.system = no_system
    me = os.path.realpath(os.path.abspath(sys.argv[0] if sys.argv and sys.argv[0] else __file__))
    for fn in ("execv", "execve", "execvp", "execvpe", "execl", "execlp", "execle", "execlpe"):
        if hasattr(os, fn):
            _HOST_REAL[fn] = getattr(os, fn)

    def make(fn):
        def ex(path, *args):
            argv = args[0] if args and isinstance(args[0], (list, tuple)) else args
            script = os.path.realpath(os.path.abspath(str(argv[1]))) if len(argv) > 1 else ""
            if script != me or not me.endswith(".py") or not os.path.isfile(me):
                _host_note(f"starting {str(path)[:40]}")
                raise PermissionError(_er.EACCES, "host mode: only this program may restart itself")
            return _HOST_REAL[fn](path, *args)
        return ex
    for fn in list(_HOST_REAL):
        if fn.startswith("exec"):
            setattr(os, fn, make(fn))


class _HostNoHardware:
    """import hook: the hardware modules are «not installed» in host mode (every part already handles a missing module)"""
    def find_spec(self, name, path=None, target=None):
        top = name.split(".")[0]
        if top in HOST_NO_MODULES or top.startswith("adafruit_"):
            raise ModuleNotFoundError(f"No module named '{name}' (host mode)", name=name)
        return None


def _host_path_ok(p):
    try:
        ap = os.path.realpath(os.path.abspath(os.fsdecode(p)))
    except (TypeError, ValueError):
        return True                                       # a file descriptor (int) - opened before
    if ap in ("/dev/null",):
        return True
    return any(ap == r or ap.startswith(r + os.sep) for r in HOST["roots"])


def _host_guard_files():
    import builtins as _b, errno as _er
    if "open" in _HOST_REAL:
        return
    _HOST_REAL["open"] = _b.open

    def hopen(file, mode="r", *a, **k):
        if isinstance(file, (str, bytes, os.PathLike)) and any(c in str(mode) for c in "wax+") and not _host_path_ok(file):
            _host_note(f"writing {os.fsdecode(file)[:80]}")
            raise PermissionError(_er.EACCES, "host mode: files only in the demo folder", os.fsdecode(file))
        return _HOST_REAL["open"](file, mode, *a, **k)
    _b.open = hopen
    for fn in ("remove", "unlink", "rmdir", "rename", "replace"):
        _HOST_REAL[fn] = getattr(os, fn)

    def make(fn):
        def f(*paths, **k):
            for p in paths[:2]:
                if isinstance(p, (str, bytes, os.PathLike)) and not _host_path_ok(p):
                    _host_note(f"{fn} {os.fsdecode(p)[:80]}")
                    raise PermissionError(_er.EACCES, "host mode: files only in the demo folder", os.fsdecode(p))
            return _HOST_REAL[fn](*paths, **k)
        return f
    for fn in ("remove", "unlink", "rmdir", "rename", "replace"):
        setattr(os, fn, make(fn))
    _HOST_REAL["rmtree"] = shutil.rmtree

    def rmtree(path, *a, **k):
        if not _host_path_ok(path):
            _host_note(f"deleting {os.fsdecode(path)[:80]}")
            raise PermissionError(_er.EACCES, "host mode: files only in the demo folder", os.fsdecode(path))
        return _HOST_REAL["rmtree"](path, *a, **k)
    shutil.rmtree = rmtree


def host_prefix_clean(p):
    p = str(p or "").strip().rstrip("/")
    return p if re.match(r"^(/[A-Za-z0-9._~-]{1,40}){1,4}$", p) else ""


def host_mode_start(a):
    """called by 640 right after the demo folder is set: switch on every lock (before any thread starts)"""
    global DEMO_BLOCK
    HOST["on"] = True
    HOST["data"] = DATA_DIR
    HOST["prefix"] = host_prefix_clean("/demo" if getattr(a, "url_prefix", None) is None else a.url_prefix)
    HOST["roots"] = tuple(sorted({os.path.realpath(os.path.abspath(DATA_DIR)), os.path.realpath(tempfile.gettempdir())}))
    DEMO_BLOCK = tuple(DEMO_BLOCK) + HOST_BLOCK
    _host_guard_sockets()
    _host_guard_programs()
    if not any(isinstance(x, _HostNoHardware) for x in sys.meta_path):
        sys.meta_path.insert(0, _HostNoHardware())
    _host_guard_files()
    print(f"HOST MODE - locks on, prefix {HOST['prefix'] or '(none)'}, files only in {DATA_DIR}")


def host_after_settings():
    """640, after the demo settings: the fixed values, then the small watcher (every 2 s) and the door for the web simulator"""
    if not HOST["on"]:
        return
    CFG["source"] = host_idle_source()
    host_enforce(True)
    host_door_start()
    threading.Thread(target=_host_loop, daemon=True, name="hostmode").start()


def _host_trim():
    """give freed memory back to the system (glibc malloc_trim; measured: 0.77 -> ~0.7 GB without the CPU cost of fixed
    mmap thresholds). Every 30 s, a few ms."""
    try:
        import ctypes
        if "trim" not in HOST:
            HOST["trim"] = ctypes.CDLL("libc.so.6").malloc_trim
        HOST["trim"](0)
    except (OSError, AttributeError):
        HOST["trim"] = lambda _n: 0


def _host_loop():
    n = 0
    while True:
        time.sleep(2.0)
        n += 1
        if n % 15 == 0:
            _host_trim()
        try:
            if n % 15 == 7:
                host_media_trim()                        # 4.16.0: continuous recording + time-lapse at most 300 MB
            if n == 15:
                _host_ai_auto()                          # 4.16.0: the AI model once, 30 s after the start (if it is missing)
            _host_notes_flush()
            host_enforce(True)
            _host_sim_tick()
        except Exception as e:
            _host_note(f"(watcher error {type(e).__name__})")


def host_ws_active():
    """a web simulator is connected right now (its WebSocket answered in the last 45 s)"""
    m = HOST.get("mux")
    return m is not None and not m.closed and time.time() - m.seen < 45


def _host_sim_tick():
    """the web simulator connected: switch the simulation on (and keep the demo armed); gone for 60 s: the drawn scene again"""
    act = host_ws_active()
    if act and not CFG.get("sim_on"):
        armed = bool(CFG.get("armed"))
        ok, _w = sim_set(True, who="automatic: web simulator (host)", confirm=True)
        HOST["sim_auto"] = bool(ok); HOST["gone_t"] = 0.0
        if ok and armed:
            arm(0)
    elif act:
        HOST["gone_t"] = 0.0
    elif HOST["sim_auto"]:
        HOST["gone_t"] = HOST.get("gone_t") or time.time()
        if time.time() - HOST["gone_t"] > 60:
            armed = bool(CFG.get("armed"))
            HOST["sim_auto"] = False; HOST["gone_t"] = 0.0
            try:
                sim_set(False, who="automatic: web simulator gone (host)", confirm=True)
            except Exception as e:                       # whatever fails there: the drawn scene comes back anyway
                _host_note(f"(simulation off: {type(e).__name__}: {str(e)[:60]})")
                CFG["sim_on"] = False
            _host_back_to_demo(armed)
    elif not CFG.get("sim_on") and str(STATE.get("source_id") or "").startswith("sim:") and time.time() - HOST.get("back_t", 0.0) > 15:
        HOST["back_t"] = time.time()                     # the simulation is off, but the picture still comes from it
        _host_back_to_demo(bool(CFG.get("armed")))


def host_idle_source():
    """the source while no web simulator is connected: the drawn scene only with --demo, else «auto» = «no camera» (4.15.0)"""
    return "demo" if DEMO["on"] else "auto"


def _host_back_to_demo(armed):
    CFG["source"] = host_idle_source()
    w = WATCH_REF.get("w")
    if w is not None:
        w.request_source(CFG["source"])
    if armed:
        try:
            arm(0)
        except Exception:
            pass


def host_sim_source(spec):
    """210 open_source: in host mode the simulator cameras are allowed while the web simulator is connected"""
    return bool(HOST["on"]) and str(spec).startswith("sim:") and bool(CFG.get("sim_on")) and host_ws_active()


_open_source_host_base = open_source


def open_source(spec, thermal=False):                    # wraps: open_source (host mode without --demo: only the web simulator)
    if HOST["on"] and not DEMO["on"] and spec != "demo" and not host_sim_source(spec):
        return None, spec, source_label(spec), "no camera - open the simulator on the homepage"
    arg = str(spec).partition(":")[2]
    if HOST["on"] and str(spec).startswith("sim:") and arg.isdigit() and not thermal:
        src = HostSimSnap(int(arg))                     # 4.15.1: single pictures through /simtun instead of the MJPEG stream
        ok, _f = src.read()
        if ok:
            return src, spec, source_label(spec), ""
        src.release()
        return None, spec, source_label(spec), "simulator not reachable - is it running?"
    return _open_source_host_base(spec, thermal)


class HostSimSnap:
    """host mode (4.15.1): the camera of the web simulator as single pictures (/cam/<n>/snapshot.jpg) through the door. An MJPEG
    stream piles up in the WebSocket of the browser when its upload or its drawing is slower than the stream - then the pictures
    came seconds late, MoveEye reconnected every 6 s and /state waited behind them («simulator not reachable»). One request
    at a time can never pile up: the rate follows the line by itself (at most sim_fps)."""

    def __init__(self, cam):
        self.cam = cam; self.c = None; self.t = 0.0; self.size = None
        self.gap = 1.0 / max(1.0, float(sim_cam_fps(cam)))

    def _get(self):
        import http.client
        if self.c is None:
            self.c = http.client.HTTPConnection("127.0.0.1", HOST_SIM_DOOR, timeout=20)
        self.c.request("GET", f"/cam/{self.cam}/snapshot.jpg", headers={"Connection": "keep-alive"})
        r = self.c.getresponse(); b = r.read()
        if r.status != 200 or not b:
            raise OSError(f"snapshot {r.status}")
        return b

    def read(self):
        w = self.gap - (time.time() - self.t)
        if w > 0:
            time.sleep(w)
        self.t = time.time()
        if host_sim_hidden():                           # 4.16.0: the tab of the simulator is in the background (the browser
            f = HOST.get("snap", {}).get(self.cam)      # draws nothing there): its last picture, no request, no reconnecting
            return (True, f.copy()) if f is not None else (False, None)
        HOST["snap_busy"] = time.time()
        try:
            b = self._get()
        except Exception:
            self.release()
            return False, None
        finally:
            HOST["snap_busy"] = 0.0
        f = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
        if f is None:
            return False, None
        self.size = (f.shape[1], f.shape[0])
        HOST.setdefault("snap", {})[self.cam] = f.copy()
        return True, f

    def set_fps(self, fps):
        self.gap = 1.0 / max(1.0, float(fps or sim_cam_fps(self.cam)))

    def release(self):
        c, self.c = self.c, None
        if c is not None:
            try:
                c.close()
            except Exception:
                pass


HOST_GAMES_BYTES = 400 * 1024 * 1024                   # 4.15.1 (Besitzer): games up to 400 MB on the host
_HOST_GU = {"t": 0.0, "n": 0}


def _host_games_used():
    """bytes of the games in the data folder (collection, ready games, Amazon Queen, their downloads) - at most every 10 s"""
    if time.time() - _HOST_GU["t"] < 10:
        return _HOST_GU["n"]
    n = 0
    for d in (games_dir(), fs_root(), fs_dl_dir(), fotaq_dir(), fotaq_dl_dir()):
        for root, _ds, fs in os.walk(d):
            for f in fs:
                try:
                    n += os.lstat(os.path.join(root, f)).st_size
                except OSError:
                    pass
    _HOST_GU.update(t=time.time(), n=n)
    return n


_bio_free_need_host_base = bio_free_need


def bio_free_need():                                     # wraps: bio_free_need (639zzd) - on the host the games budget counts
    """«free - need < bio_free_need()» = «need > what is left of the 400 MB» (never more than the disk really has)"""
    if not HOST["on"]:
        return _bio_free_need_host_base()
    try:
        free = shutil.disk_usage(DATA_DIR).free
    except OSError:
        free = 0
    left = max(0, min(HOST_GAMES_BYTES - _host_games_used(), free - 64 * 1024 * 1024))
    return free - left


_games_install_host_base = games_install


def games_install():                                     # wraps: games_install (340) - the collection may reach GitHub
    _HOST_TL.dl = True
    try:
        return _games_install_host_base()
    finally:
        _HOST_TL.dl = False
        _HOST_GU["t"] = 0.0


# ---- 4.16.0: the AI model (SSD MobileNet V2: person, animal, vehicle) from its one fixed source ----------------------------
HOST_AI_TGZ = "https://storage.googleapis.com/download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz"
HOST_AI_TGZ_SHA1 = "69c93d29e292bc9682396a5c78355b1dfe481b61"      # the checksums OpenCV pins for this archive and its model
HOST_AI_PB_SHA1 = "35d571ac314f1d32ae678a857f87cc0ef6b220e8"       # (opencv_extra testdata/dnn/download_models.py)
HOST_AI_PBTXT = "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"
HOST_AI_PBTXT_SHA256 = "cfbecf9447c384403ef5cf695f4cd0bb4840c1312938280350639a9a8e82d303"
HOST_AI_TGZ_MAX = 260 * 1024 * 1024                                # (the archive has 187 MB, the model 67 MB)
HOST_AI_PB_MAX = 120 * 1024 * 1024


class _HostHashReader:
    """the archive while it arrives: checksum and size on the way (it is never written to the disk)"""
    def __init__(self, r, limit):
        self.r = r; self.h = hashlib.sha1(); self.n = 0; self.limit = limit
        self.total = int(r.headers.get("Content-Length") or 0)

    def read(self, n=-1):
        b = self.r.read(n if n and n > 0 else 1 << 16)
        self.n += len(b)
        if self.n > self.limit:
            raise RuntimeError("the file is bigger than expected")
        self.h.update(b)
        AI_MODEL["pct"] = min(89, int(self.n * 90 / self.total)) if self.total else min(89, self.n // (2 * 1024 * 1024))
        return b


def host_ai_download():
    """the AI model on the host: only HOST_AI_TGZ and HOST_AI_PBTXT, the archive streamed (no 190 MB on the disk), used only
    with the right checksums; its own thread «ai-model» is the only one that may reach these two addresses (_host_net_ok)"""
    if AI_MODEL["busy"]:
        return False, "already running"
    AI_MODEL.update(busy=True, msg="downloading", pct=0)

    def run():
        import tarfile, urllib.request as _u
        dst = os.path.join(DATA_DIR, "models")
        pb_tmp, tx_tmp = os.path.join(dst, AIDetector.PB + ".part"), os.path.join(dst, AIDetector.PBTXT + ".part")
        op = _u.build_opener(_u.ProxyHandler({}))
        hd = {"User-Agent": "MotionWatch/" + APP_VERSION}
        try:
            os.makedirs(dst, exist_ok=True)
            got = None
            with op.open(_u.Request(HOST_AI_TGZ, headers=hd), timeout=60) as r:
                rd = _HostHashReader(r, HOST_AI_TGZ_MAX)
                with tarfile.open(fileobj=rd, mode="r|gz") as tf_:
                    for m in tf_:
                        if got is None and m.isfile() and m.name.endswith("/" + AIDetector.PB):
                            if m.size > HOST_AI_PB_MAX:
                                raise RuntimeError("the model file is bigger than expected")
                            src, ph = tf_.extractfile(m), hashlib.sha1()
                            with open(pb_tmp, "wb") as f:
                                while True:
                                    b = src.read(1 << 16)
                                    if not b:
                                        break
                                    f.write(b); ph.update(b)
                            got = ph.hexdigest()
                while rd.read(1 << 16):                  # the rest of the archive: its checksum counts too
                    pass
            if got is None:
                raise RuntimeError("model file missing in the archive")
            if rd.h.hexdigest() != HOST_AI_TGZ_SHA1 or got != HOST_AI_PB_SHA1:
                raise RuntimeError("the checksum of the model is wrong")
            with op.open(_u.Request(HOST_AI_PBTXT, headers=hd), timeout=60) as r:
                txt = r.read(2 * 1024 * 1024)
            if hashlib.sha256(txt).hexdigest() != HOST_AI_PBTXT_SHA256:
                raise RuntimeError("the checksum of the description file is wrong")
            with open(tx_tmp, "wb") as f:
                f.write(txt)
            AI_MODEL["pct"] = 95
            os.replace(pb_tmp, os.path.join(dst, AIDetector.PB)); os.replace(tx_tmp, os.path.join(dst, AIDetector.PBTXT))
            CFG["ai_enabled"] = True; save_settings()
            w = WATCH_REF.get("w")
            if w is not None:
                w.ai = AIDetector()
            AI_MODEL.update(msg="ready", pct=100)
            log_event("ai", "AI model downloaded (fixed source, checksums right) and switched on - host mode")
        except Exception as e:
            AI_MODEL.update(msg=f"failed: {tr(str(e))}"[:120], pct=0)
            log_event("ai", f"AI model download failed: {e}"[:200])
        finally:
            AI_MODEL["busy"] = False
            for p_ in (pb_tmp, tx_tmp):
                try:
                    os.remove(p_)
                except OSError:
                    pass
    threading.Thread(target=run, daemon=True, name=HOST_AI_THREAD).start()
    return True, ""


_ai_model_dirs_host_base = ai_model_dirs


def ai_model_dirs():                                     # wraps: ai_model_dirs (170) - on the host only the checked download
    """host mode: only the models folder of the data folder (host_ai_download puts only checked files there) - never a
    file that happens to lie next to the program"""
    if HOST["on"]:
        return [os.path.join(DATA_DIR, "models")]
    return _ai_model_dirs_host_base()


_ai_model_download_host_base = ai_model_download


def ai_model_download():                                 # wraps: ai_model_download (170) - on the host only the fixed source
    if HOST["on"]:
        return host_ai_download()
    return _ai_model_download_host_base()


def _host_ai_auto():
    """once, 30 s after the start: the AI model if it is missing (Besitzer: AI detection on the host). MW_HOST_KI_AUTO=0: not
    (werkzeuge/host_demo_test.py without --ki: no 190 MB download in every test run)"""
    if HOST.get("ai_auto") or os.environ.get("MW_HOST_KI_AUTO", "1") == "0":
        return
    HOST["ai_auto"] = True
    if not ai_model_paths()[0] and not AI_MODEL["busy"]:
        ai_model_download()


# ---- 4.16.0: continuous recording + time-lapse together at most 300 MB ------------------------------------------------
def host_media_trim(limit=None):
    """the pieces of the continuous recording and the photos / videos of the time-lapse together at most HOST_MEDIA_BYTES:
    the oldest go first (the piece being written and starred photos stay) -> bytes afterwards"""
    limit = HOST_MEDIA_BYTES if limit is None else limit
    lr = globals().get("LOOPREC")
    cur = str(getattr(lr, "cur", "") or "")
    files = []
    for p in glob.glob(os.path.join(loop_dir(), "*", "*.mp4")):
        files.append((p, "loop"))
    try:
        files += [(os.path.join(tl_dir(), n), "tl") for n in os.listdir(tl_dir()) if TL_PHOTO_RE.match(n) or TL_VIDEO_RE.match(n)]
    except OSError:
        pass
    items = []
    for p, k in files:
        try:
            st = os.stat(p)
        except OSError:
            continue
        items.append((st.st_mtime, st.st_size, p, k))
    items.sort()
    total = sum(x[1] for x in items); removed = 0
    for _mt, sz, p, k in items:
        if total <= limit:
            break
        rel = os.path.relpath(p, rec_dir()).replace(os.sep, "/")
        if rel == cur or rel in LIVE_RECS or os.path.basename(p) in LIVE_RECS:
            continue
        if k == "tl" and _read_sidecar("timelapse/" + os.path.basename(p)).get("fav"):
            continue
        try:
            os.remove(p); total -= sz; removed += 1
        except OSError:
            pass
    HOST["media_mb"] = total // (1024 * 1024)
    if removed:
        log_event("rec", f"Host mode: {removed} old file(s) of the continuous recording / time-lapse deleted, "
                         f"now {total // 1048576} of {limit // 1048576} MB")
    return total


_LoopRecorder_clean_host_base = LoopRecorder._clean


def _host_loop_clean(self):                              # wraps: LoopRecorder._clean (420) - host: the 300 MB, not «1 GB free»
    """on the host (2 GB disk) «keep 1 GB free» would delete every piece at once: the hours, then the common 300 MB"""
    if not HOST["on"]:
        return _LoopRecorder_clean_host_base(self)
    now = time.time()
    if now - self.last_clean < 60:
        return
    self.last_clean = now
    keep = float(CFG["loop_hours"]) * 3600
    for p in glob.glob(os.path.join(loop_dir(), "*", "*.mp4")):
        try:
            if os.path.relpath(p, rec_dir()).replace(os.sep, "/") != self.cur and now - os.path.getmtime(p) > keep:
                os.remove(p)
        except OSError:
            pass
    for dp in glob.glob(os.path.join(loop_dir(), "*")):
        try:
            if os.path.isdir(dp) and not os.listdir(dp) and not self.cur.startswith("loop/" + os.path.basename(dp) + "/"):
                os.rmdir(dp)
        except OSError:
            pass
    try:
        low = shutil.disk_usage(rec_dir()).free < 150 * 1024 * 1024
    except OSError:
        low = False
    host_media_trim(0 if low else None)                  # the disk almost full: only the piece being written stays


# wraps: LoopRecorder._clean
LoopRecorder._clean = _host_loop_clean


# ---- 4.16.0: the simulator tab in the background, the watchdog, the password note ----------------------------------------
HOST_HIDDEN = "The simulator tab is in the background – picture paused"
HOST_HIDDEN_TIP = "Tip: open the simulator in its own window next to this one"
HOST_PW = "Password comes from the host (Basic Auth)"


def host_sim_hidden():
    """the web simulator is connected, but its tab is in the background (it says so: «VIS hidden», Sim 3.72.0)"""
    m = HOST.get("mux")
    return bool(m is not None and getattr(m, "hidden", False) and host_ws_active())


def host_cam_waits():
    """the camera loop waits for the web simulator (tab in the background, a picture on its way, not connected) - no hang"""
    if not (CFG.get("sim_on") or str(CFG.get("source") or "").startswith("sim:")):
        return False
    w = WATCH_REF.get("w")
    return (host_sim_hidden() or not host_ws_active() or float(HOST.get("snap_busy") or 0.0) > 0.0
            or w is None or getattr(w, "cap", None) is None)


_servo_inhibit_host_base = _servo_inhibit


def _servo_inhibit(code, on, now):                       # wraps: _servo_inhibit (072) - host: waiting for the web simulator is no hang
    if on and code == "wd_cam" and HOST["on"] and host_cam_waits():
        on = False
    return _servo_inhibit_host_base(code, on, now)


_SimLink_tick_host_base = SimLink.tick


def _host_simlink_tick(self):                            # wraps: SimLink.tick (350) - host: the tab in the background stays connected
    if HOST["on"] and host_sim_hidden():
        SIM.update(t=time.time(), ok=True, msg="connected - the simulator tab is in the background (picture paused)")
        time.sleep(0.5)
        return
    return _SimLink_tick_host_base(self)


_host_simlink_tick.__wrapped__ = _SimLink_tick_host_base   # (the self-tests 558 / 558l read the source of SimLink.tick)
# wraps: SimLink.tick
SimLink.tick = _host_simlink_tick
_simwait_reason_host_base = simwait_reason


def simwait_reason(now=None):                            # wraps: simwait_reason (639y) - the tab in the background is no lost line
    if HOST["on"] and CFG.get("sim_on") and str(CFG.get("source") or "").startswith("sim:") and host_sim_hidden():
        now = time.time() if now is None else now
        SIMWAIT["why"] = "hidden"
        return {"why": "hidden", "ver": "", "pct": None, "s": int(max(0.0, now - float(getattr(HOST.get("mux"), "hidden_t", now))))}
    if SIMWAIT.get("why") == "hidden":
        SIMWAIT["why"] = None
    return _simwait_reason_host_base(now)


_health_check_host_base = health_check


def health_check(lang=None):                             # wraps: health_check - on the host the Basic Auth of the homepage protects
    out = _health_check_host_base(lang)
    if not HOST["on"] or web_pw_active():
        return out
    items = out.get("items") if isinstance(out, dict) else out
    if not isinstance(items, list):
        return out
    L = norm_lang(lang) if lang else cur_lang()
    for x in items:
        if isinstance(x, dict) and x.get("id") == "pw":
            x.update(level="ok", text=tr(HOST_PW, L), tip="")
    if isinstance(out, dict) and isinstance(out.get("count"), dict):
        out["count"] = {k: sum(1 for x in items if isinstance(x, dict) and x.get("level") == k) for k in HEALTH_ORDER}
    return out


_security_check_host_base = security_check


def security_check():                                    # wraps: security_check (300) - the same on the tools page
    r = _security_check_host_base()
    if HOST["on"] and not web_pw_active():
        for x in TOOLS["sec"].get("items") or []:
            if str(x.get("text") or "").startswith("Web password"):
                x.update(level="ok", text=HOST_PW, tip="")
    return r


def host_public_base():
    """the address of MoveEye as the visitor sees it (https://<homepage>/demo) - for links and QR codes"""
    from flask import request
    proto = (request.headers.get("X-Forwarded-Proto") or "https").split(",")[0].strip()
    host = (request.headers.get("X-Forwarded-Host") or request.host or "").split(",")[0].strip()
    return f"{proto}://{host}{HOST['prefix']}"


HOST_SIM_HINT = "Open the simulator on moveeye.kevlaschef.com/Sim/ (same browser or phone)"
HOST_SIM_LINK = "Open the simulator"
HOST_SIM_URL = "/Sim/"              # 4.16.0: the simulator of the homepage - absolute, and never given the prefix (HOST_OUTSIDE)
HOST_OUTSIDE = ("/Sim/",)           # addresses of the homepage itself: the prefix layer and the page script leave them alone
_simwait_texts_host_base = simwait_texts


def simwait_texts(r, lang=None):                        # wraps: simwait_texts (639y) - on the host no «simulator on the PC»
    L = norm_lang(lang) if lang else cur_lang()
    if HOST["on"] and r.get("why") == "hidden":          # 4.16.0: the tab of the simulator is in the background
        return {"title": tr(HOST_HIDDEN, L), "sub": tr("for {t}", L).replace("{t}", _mmss(r.get("s") or 0)),
                "hint": tr(HOST_HIDDEN_TIP, L), "hint2": "", "link": tr(HOST_SIM_LINK, L), "help": tr("Help", L), "url": HOST_SIM_URL}
    d = _simwait_texts_host_base(r, lang)
    if HOST["on"]:
        d.update(hint=tr(HOST_SIM_HINT, L), hint2="", link=tr(HOST_SIM_LINK, L), url=HOST_SIM_URL)
    return d


HOST_NA = "not available on the host"
HOST_AI = ("/api/ki/", "/api/tausch/bio", "/api/own_model", "/api/piper")   # 4.15.0: no Blinki, BioCLIP, own model, voices (RAM)
HOST_AI_OK = ("/api/ai_model", "/api/tausch")   # 4.16.0: the AI detection (fixed source) and the backpack go (in DEMO_BLOCK)


def host_path_in(p, prefixes):
    """p is one of the addresses or below it («/api/time» is not «/api/timelapse»; «/api/ki/» ends with / - all below)"""
    for x in prefixes:
        if p == x.rstrip("/") or p.startswith(x if x.endswith("/") else x + "/"):
            return True
    return False
for _k, _v in {HOST_NA: ("auf dem Host nicht verfügbar", "non disponible sur l'hébergeur", "non disponibile sull'host",
                         "betg disponibel sin il host"),
               HOST_SIM_HINT: ("Öffne den Simulator auf moveeye.kevlaschef.com/Sim/ (gleicher Browser oder Handy)",
                               "Ouvre le simulateur sur moveeye.kevlaschef.com/Sim/ (même navigateur ou téléphone)",
                               "Apri il simulatore su moveeye.kevlaschef.com/Sim/ (stesso browser o telefono)",
                               "Avra il simulatur sin moveeye.kevlaschef.com/Sim/ (il medem navigatur u il telefonin)"),
               HOST_SIM_LINK: ("Simulator öffnen", "Ouvrir le simulateur", "Apri il simulatore", "Avrir il simulatur"),
               HOST_HIDDEN: ("Simulator-Tab ist im Hintergrund – Bild pausiert", "L'onglet du simulateur est en arrière-plan – image en pause",
                             "La scheda del simulatore è in secondo piano – immagine in pausa",
                             "Il tab dal simulatur è en il fund – maletg en pausa"),
               HOST_HIDDEN_TIP: ("Tipp: Simulator in einem eigenen Fenster daneben öffnen",
                                 "Astuce : ouvre le simulateur dans sa propre fenêtre à côté",
                                 "Consiglio: apri il simulatore in una finestra propria accanto",
                                 "Tip: avra il simulatur en ina atgna fanestra sper questa"),
               HOST_PW: ("Passwort kommt vom Host (Basic Auth)", "Le mot de passe vient de l'hébergeur (Basic Auth)",
                         "La password viene dall'host (Basic Auth)", "Il pled-clav vegn dal host (Basic Auth)")}.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def host_door_start():
    """the door 127.0.0.1:18765 (the address of the tunnel in 180, which stays off in the demo): every connection MoveEye
    opens there becomes one channel of the WebSocket of the web simulator"""
    import socket as _s
    if HOST["door"]:
        return
    srv = _s.socket(_s.AF_INET, _s.SOCK_STREAM); srv.setsockopt(_s.SOL_SOCKET, _s.SO_REUSEADDR, 1)
    try:
        srv.bind(("127.0.0.1", HOST_SIM_DOOR)); srv.listen(32)
    except OSError as e:
        HOST["door"] = "busy: " + str(e)[:60]
        log_event("sys", f"Host mode: the door for the web simulator (127.0.0.1:{HOST_SIM_DOOR}) could not open: {e}"[:200])
        srv.close(); return
    HOST["door"] = "ok"

    def loop():
        while True:
            cl, _a = srv.accept()
            m = HOST.get("mux")
            if m is None or m.closed or m.hidden:         # 4.16.0: a tab in the background answers nothing - at once, not after 20 s
                cl.close(); continue
            threading.Thread(target=m.channel, args=(cl,), daemon=True, name="hostch").start()
    threading.Thread(target=loop, daemon=True, name="hostdoor").start()


class _HostWsMux:
    """the WebSocket of one web simulator (RFC 6455; the browser masks its messages). Protocol «MWTUN2»:
       simulator -> «MWTUN2 <code> <instance>» (text), MoveEye -> «OK\n» or «NO\n»;
       MoveEye -> «OPEN <id> 8765» (text): a new HTTP connection to the simulator (like a TCP connection to its port 8765);
       both ways: binary message = 4 bytes channel id (big endian) + bytes of that connection; «CLOSE <id>» (text) ends one;
       «PING» -> «PONG» (text) either way; «TAKEN\n» (text): a newer simulator window took over - do not reconnect by itself."""

    def __init__(self, sock, peer, inst):
        self.s = sock; self.peer = peer; self.inst = inst; self.closed = False; self.seen = time.time()
        self.lock = threading.Lock(); self.ch = {}; self.next = 1; self.bytes = 0
        self.hidden = False; self.hidden_t = 0.0                # 4.16.0: «VIS hidden|visible» of the simulator (its tab)

    def _exact(self, n):
        out = b""
        while len(out) < n:
            ch = self.s.recv(min(65536, n - len(out)))
            if not ch:
                raise OSError("closed")
            out += ch
        return out

    def frame(self):
        """(fin, opcode, payload) of the next frame"""
        b0, b1 = self._exact(2)
        op, ln = b0 & 0x0F, b1 & 0x7F
        if ln == 126:
            ln = int.from_bytes(self._exact(2), "big")
        elif ln == 127:
            ln = int.from_bytes(self._exact(8), "big")
        if ln > HOST_WS_MAX:
            raise OSError("message too big")
        mask = self._exact(4) if b1 & 0x80 else b""
        data = self._exact(ln) if ln else b""
        if mask and data:
            k = (mask * (ln // 4 + 1))[:ln]
            data = (int.from_bytes(data, "big") ^ int.from_bytes(k, "big")).to_bytes(ln, "big")
        return bool(b0 & 0x80), op, data

    def message(self):
        """(opcode, payload) of the next whole message; answers pings"""
        buf, first = b"", None
        while True:
            fin, op, data = self.frame()
            if op >= 8:
                if op == 8:
                    raise OSError("closed by the simulator")
                if op == 9:
                    self.send(10, data)
                self.seen = time.time()                         # 4.16.0: a pong of the browser (also from a tab in the background)
                continue
            if op:
                first = op
            buf += data
            if len(buf) > HOST_WS_MAX:
                raise OSError("message too big")
            if fin:
                return first or 2, buf

    def send(self, op, data):
        n = len(data)
        head = bytes([0x80 | op, n]) if n < 126 else (bytes([0x80 | op, 126]) + n.to_bytes(2, "big") if n < 65536 else bytes([0x80 | op, 127]) + n.to_bytes(8, "big"))
        with self.lock:
            if self.closed and op != 8:
                raise OSError("closed")
            self.s.sendall(head + data)

    def text(self, t):
        self.send(1, t.encode())

    def channel(self, cl):
        """one HTTP connection of MoveEye to the simulator: bytes from MoveEye into the WebSocket"""
        with self.lock:
            cid = self.next; self.next += 1; self.ch[cid] = cl
        try:
            self.text(f"OPEN {cid} 8765")
            while True:
                d_ = cl.recv(65536)
                if not d_:
                    break
                for i in range(0, len(d_), 60000):
                    self.send(2, cid.to_bytes(4, "big") + d_[i:i + 60000])
                self.bytes += len(d_)
        except OSError:
            pass
        finally:
            self.drop(cid, tell=True)

    def drop(self, cid, tell):
        with self.lock:
            cl = self.ch.pop(cid, None)
        if cl is not None:
            for f_ in (lambda: cl.shutdown(2), cl.close):
                try:
                    f_()
                except OSError:
                    pass
            if tell:
                try:
                    self.text(f"CLOSE {cid}")
                except OSError:
                    pass

    def run(self):
        """bytes / control messages from the simulator (the request thread of the web server stays here)"""
        self.s.settimeout(20.0)
        idle = 0
        while not self.closed:
            try:
                op, data = self.message()
            except TimeoutError:
                idle = 0 if time.time() - self.seen < 25 else idle + 1    # the browser answered the last ping: still there
                if idle >= 4:
                    break                                       # 80 s without anything: gone (closed tab, lost network)
                try:
                    self.send(9, b"mw")
                except OSError:
                    break
                continue
            except (OSError, ValueError):
                break
            idle = 0; self.seen = time.time()
            if op == 2 and len(data) >= 4:
                cl = self.ch.get(int.from_bytes(data[:4], "big"))
                if cl is not None:
                    try:
                        cl.sendall(data[4:]); self.bytes += len(data) - 4
                    except OSError:
                        self.drop(int.from_bytes(data[:4], "big"), tell=True)
            elif op == 1:
                t = data.decode("utf-8", "replace").strip().split()
                if t[:1] == ["CLOSE"] and len(t) == 2 and t[1].isdigit():
                    self.drop(int(t[1]), tell=False)
                elif t[:1] == ["PING"]:
                    try:
                        self.text("PONG")
                    except OSError:
                        break
                elif t[:1] == ["VIS"] and len(t) == 2:
                    self.set_hidden(t[1] == "hidden")
        self.close()

    def set_hidden(self, h):
        """the tab of the simulator went to the background (the browser draws nothing there, so no picture and no answer
        comes) or back: keep the line, the last picture stays (HostSimSnap), no reconnecting; running requests end at once"""
        if h == self.hidden:
            return
        self.hidden = h; self.hidden_t = time.time()
        if h:
            for cid in list(self.ch):
                self.drop(cid, tell=True)
        log_event("sys", "Web simulator: its tab is in the background - picture paused" if h else "Web simulator: its tab is visible again")

    def close(self, why=""):
        if why:
            try:
                self.text(why)
            except OSError:
                pass
        self.closed = True
        for cid in list(self.ch):
            self.drop(cid, tell=False)
        try:
            self.send(8, b"\x03\xe8")
        except OSError:
            pass
        try:
            self.s.shutdown(2)
        except OSError:
            pass


def host_routes(app):
    """the WebSocket of the web simulator (only in host mode; the TCP tunnel of 180 stays off)"""
    from flask import request, Response
    import base64 as _b64

    @app.after_request
    def host_party(resp):                                # 4.15.1: the game page on the host - right links, no rest mode
        if request.path != "/api/party" or resp.mimetype != "application/json":
            return resp
        try:
            d = json.loads(resp.get_data())
            d["lan_url"] = ""                            # «without login in your own Wi-Fi» does not exist on the host
            d["no_rest"] = True                          # the game server of the rest mode has its own port - not reachable here
            if d.get("url") and "/p/" in d["url"]:
                d["url"] = host_public_base() + "/p/" + d["url"].split("/p/", 1)[1]
                d["qr"] = qr_svg(d["url"])
            resp.set_data(json.dumps(d))
        except Exception:
            pass
        return resp

    @app.before_request
    def host_guard():                                    # 4.15.0: without --demo the demo guard of 550 is off - the same routes here
        p = request.path                                 # 4.16.0: whole address parts (before, «/api/stick» = the joystick of
        ai = host_path_in(p, HOST_AI) or "/untersuchen" in p or "/tausch/bio" in p      # the head was refused as a USB stick,
        sysp = not DEMO["on"] and request.method == "POST" and host_path_in(p, tuple(x for x in DEMO_BLOCK if x not in HOST_AI_OK))   # «/api/time» the time-lapse)
        if not (ai or sysp):
            return None
        L = norm_lang(request.args.get("lang") or CFG.get("lang"))
        return Response(json.dumps({"ok": False, "error": tr(HOST_NA, L)}), 403, mimetype="application/json")

    @app.before_request
    def host_simview():                                  # 4.16.0: the simulator tab in the background - the calm picture at once
        if request.path != "/sim/view.jpg" or not CFG.get("sim_on") or not host_sim_hidden():
            return None
        cj = simwait_jpeg(request.args.get("w") or 960)
        if not cj:
            return Response("simulator tab in the background", 503, {"Retry-After": "2"})
        return Response(cj, mimetype="image/jpeg", headers={"Cache-Control": "no-store", "X-MW-Wait": "1"})

    @app.after_request
    def host_simview_live(resp):                         # 4.16.0: no view of the web simulator - the picture of the Live page
        if request.path != "/sim/view.jpg" or host_sim_hidden() or not (resp.status_code >= 500 or resp.headers.get("X-MW-Wait")):
            return resp
        w = WATCH_REF.get("w")
        f = getattr(w, "frame_out", None) if w is not None else None
        if f is None or not sim_picture_ok():
            return resp
        ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ok:
            return resp
        return Response(buf.tobytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store", "X-MW-Live": "1"})

    @app.route("/simtun", websocket=True)
    def host_simtun():
        key = request.headers.get("Sec-WebSocket-Key", "")
        sock = request.environ.get("werkzeug.socket")
        if request.headers.get("Upgrade", "").lower() != "websocket" or not re.match(r"^[A-Za-z0-9+/]{22}==$", key):
            return Response("WebSocket only", 400)
        if sock is None:
            return Response("not supported", 501)
        if HOST["ws"] >= HOST_WS_LINES:
            return Response("too many simulators", 503)
        peer = (request.headers.get("X-Forwarded-For") or request.remote_addr or "?").split(",")[0].strip()[:45]
        acc = _b64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        HOST["ws"] += 1
        mux = _HostWsMux(sock, peer, "")
        try:
            sock.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                          f"Sec-WebSocket-Accept: {acc}\r\n\r\n").encode())
            sock.settimeout(10.0)
            op, data = mux.message()
            parts = data.decode("ascii", "replace").split() if op == 1 else []
            if not (len(parts) in (2, 3) and parts[0] == "MWTUN2"):
                mux.text("NO\n"); mux.close(); return Response("", 200)
            mux.inst = parts[2][:40] if len(parts) == 3 else ""
            mux.text("OK\n")
            old = HOST.get("mux")
            HOST["mux"] = mux                                   # the newest window wins (a tab left open never blocks others)
            if old is not None and not old.closed:
                old.close("TAKEN\n")
                log_event("sys", f"Web simulator: a newer window ({peer}) took over from {old.peer}")
            else:
                log_event("sys", f"Web simulator connected (host mode, WebSocket) from {peer}")
            mux.run()
        except OSError:
            pass
        finally:
            HOST["ws"] -= 1
            mux.closed = True
            if HOST.get("mux") is mux:
                log_event("sys", f"Web simulator gone ({peer}, {mux.bytes // 1024} KB)")
        return Response("", 200)                 # never reaches the browser: the connection was taken over


# ---- path prefix («/demo») --------------------------------------------------------------------------------------------
_HOST_RW = {"segs": None, "rx": None, "cache": {}, "order": deque()}
HOST_RW_TYPES = ("text/html", "text/javascript", "application/javascript", "application/x-javascript", "text/css", "application/manifest+json")

HOST_SHIM_JS = r"""(function(){
var P=%PREFIX%,OUT=%OUTSIDE%;if(!P||window.__mwBase!==undefined)return;window.__mwBase=P;
function out(p){for(var i=0;i<OUT.length;i++){var o=OUT[i];if(p===o.slice(0,-1)||p.indexOf(o)===0)return true;}return false;}
function has(p){return p===P||p.indexOf(P+"/")===0||p.indexOf(P+"?")===0||p.indexOf(P+"#")===0||out(p);}
function fix(u){
 if(u instanceof URL)u=u.href;
 if(typeof u!=="string")return u;
 if(u.charAt(0)==="/"&&u.charAt(1)!=="/"&&u.charAt(1)!=="\\")return has(u)?u:P+u;
 var m=/^(https?|wss?):\/\/([^\/?#]+)(\/[^?#]*)?([\s\S]*)$/i.exec(u);
 if(m&&m[2].toLowerCase()===location.host.toLowerCase()){var p=m[3]||"/";if(!has(p))return m[1]+"://"+m[2]+P+p+m[4];}
 return u;}
window.__mwFix=fix;
var F=window.fetch;if(F)window.fetch=function(i,o){
 if(typeof i==="string"||i instanceof URL)i=fix(String(i));
 else if(i&&i.url){var n=fix(i.url);if(n!==i.url)i=new Request(n,i);}
 return F.call(this,i,o);};
var XO=XMLHttpRequest.prototype.open;XMLHttpRequest.prototype.open=function(m,u){var a=[].slice.call(arguments);a[1]=fix(u);return XO.apply(this,a);};
function wrapC(name){var C=window[name];if(!C)return;var W=function(u,x){return x===undefined?new C(fix(String(u))):new C(fix(String(u)),x);};
 W.prototype=C.prototype;["CONNECTING","OPEN","CLOSING","CLOSED"].forEach(function(k){if(k in C)try{Object.defineProperty(W,k,{value:C[k]});}catch(e){}});
 window[name]=W;}
wrapC("EventSource");wrapC("WebSocket");
var WO=window.open;window.open=function(u){var a=[].slice.call(arguments);if(a.length)a[0]=fix(u);return WO.apply(this,a);};
if(navigator.sendBeacon){var SB=navigator.sendBeacon.bind(navigator);navigator.sendBeacon=function(u,d){return SB(fix(u),d);};}
["pushState","replaceState"].forEach(function(k){var h=history[k];history[k]=function(s,t,u){return u===undefined?h.call(history,s,t):h.call(history,s,t,fix(u));};});
var PROPS=[["HTMLAnchorElement","href"],["HTMLAreaElement","href"],["HTMLLinkElement","href"],["HTMLImageElement","src"],["HTMLScriptElement","src"],
 ["HTMLIFrameElement","src"],["HTMLMediaElement","src"],["HTMLSourceElement","src"],["HTMLVideoElement","poster"],["HTMLFormElement","action"],
 ["HTMLEmbedElement","src"],["HTMLObjectElement","data"],["HTMLInputElement","src"],["HTMLTrackElement","src"]];
PROPS.forEach(function(x){var C=window[x[0]];if(!C)return;var d=Object.getOwnPropertyDescriptor(C.prototype,x[1]);if(!d||!d.set)return;
 Object.defineProperty(C.prototype,x[1],{configurable:true,enumerable:d.enumerable,get:d.get,set:function(v){d.set.call(this,typeof v==="string"?fix(v):v);}});});
var ATTR={href:1,src:1,action:1,poster:1,data:1,formaction:1};
var SA=Element.prototype.setAttribute;Element.prototype.setAttribute=function(n,v){if(ATTR[String(n).toLowerCase()]&&typeof v==="string")v=fix(v);return SA.call(this,n,v);};
var RX=/(\s(?:href|src|action|poster|formaction)\s*=\s*["']?)\/(?![\/\\])/gi;
function fixHtml(h){return typeof h!=="string"||h.indexOf("/")<0?h:h.replace(RX,function(a,b,o,s){return has(s.substr(o+b.length))?a:b+P+"/";});}
[["innerHTML",Element.prototype],["outerHTML",Element.prototype]].forEach(function(x){var d=Object.getOwnPropertyDescriptor(x[1],x[0]);if(!d||!d.set)return;
 Object.defineProperty(x[1],x[0],{configurable:true,enumerable:d.enumerable,get:d.get,set:function(v){d.set.call(this,fixHtml(v));}});});
var IA=Element.prototype.insertAdjacentHTML;Element.prototype.insertAdjacentHTML=function(p,h){return IA.call(this,p,fixHtml(h));};
function fixEl(el){if(!el||el.nodeType!==1)return;for(var k in ATTR){var v=el.getAttribute&&el.getAttribute(k);if(v){var n=fix(v);if(n!==v)SA.call(el,k,n);}}}
function fixTree(n){if(!n||n.nodeType!==1)return;fixEl(n);if(n.querySelectorAll){var l=n.querySelectorAll("[href],[src],[action],[poster],[data],[formaction]");for(var i=0;i<l.length;i++)fixEl(l[i]);}}
new MutationObserver(function(ms){ms.forEach(function(m){if(m.type==="attributes")fixEl(m.target);else for(var i=0;i<m.addedNodes.length;i++)fixTree(m.addedNodes[i]);});})
 .observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:["href","src","action","poster","data","formaction"]});
document.addEventListener("click",function(e){var a=e.target&&e.target.closest&&e.target.closest("a[href]");if(a)fixEl(a);},true);
document.addEventListener("submit",function(e){fixEl(e.target);},true);
if(window.navigation&&navigation.addEventListener)navigation.addEventListener("navigate",function(e){try{var u=new URL(e.destination.url);
 if(u.origin===location.origin&&!has(u.pathname)&&e.cancelable&&!e.hashChange&&!e.downloadRequest&&!e.formData){e.preventDefault();location.href=P+u.pathname+u.search+u.hash;}}catch(x){}});
try{if(navigator.serviceWorker){navigator.serviceWorker.register=function(){return Promise.reject(new Error("no service worker in the demo"));};
 navigator.serviceWorker.getRegistrations&&navigator.serviceWorker.getRegistrations().then(function(rs){rs.forEach(function(r){try{if(!has(new URL(r.scope).pathname))return;r.unregister();}catch(x){}});});}}catch(x){}
})();"""


def _host_segs(flask_app):
    if _HOST_RW["segs"] is None:
        segs = set()
        for r in flask_app.url_map.iter_rules():
            s = str(r.rule).split("/")[1] if str(r.rule).startswith("/") else ""
            if s and "<" not in s:
                segs.add(s)
        _HOST_RW["segs"] = frozenset(segs)
        _HOST_RW["rx"] = re.compile(r"""(["'`]|url\()/([A-Za-z0-9_.~-]+)(?=[/?#"'`)\\]|$)""")   # segment checked in a set: 3x faster than one alternation
        _HOST_RW["root"] = re.compile(r"""(\b(?:href|src|action)\s*=\s*\\?["']|location(?:\.href)?\s*=\s*["']|location\.(?:assign|replace)\(\s*["']|"(?:start_url|scope)"\s*:\s*")/(?=\\?["'?#])""")
    return _HOST_RW["rx"], _HOST_RW["root"]


def host_rewrite(text, prefix, flask_app, html=False):
    """the absolute addresses of a page / script / style with the prefix in front (twice is never done: «/demo/…» is no
    segment of the server)"""
    rx, root = _host_segs(flask_app)
    segs = _HOST_RW["segs"]
    text = rx.sub(lambda m: m.group(1) + prefix + "/" + m.group(2) if m.group(2) in segs and "/" + m.group(2) + "/" not in HOST_OUTSIDE
                  else m.group(0), text)
    text = root.sub(lambda m: m.group(1) + prefix + "/", text)
    if html:
        tag = "<script>" + HOST_SHIM_JS.replace("%OUTSIDE%", json.dumps(list(HOST_OUTSIDE))).replace("%PREFIX%", json.dumps(prefix)) + "</script>"
        m = re.search(r"<head\b[^>]*>", text[:4000], re.I) or re.search(r"<html\b[^>]*>", text[:4000], re.I) or re.search(r"<!doctype[^>]*>", text[:400], re.I)
        text = text[:m.end()] + tag + text[m.end():] if m else tag + text
    return text


class _HostPrefix:
    """WSGI layer in host mode: path prefix for the browser, the server keeps its paths («/demo» is taken off if it
    arrives), compression off for the pages it rewrites"""
    def __init__(self, wsgi, flask_app):
        self.wsgi = wsgi; self.flask_app = flask_app

    def __call__(self, environ, start_response):
        P = host_prefix_clean(environ.get("HTTP_X_FORWARDED_PREFIX", "")) or HOST["prefix"]
        if not P:
            return self.wsgi(environ, start_response)
        pi = environ.get("PATH_INFO", "") or "/"
        if pi == P or pi.startswith(P + "/"):
            environ["PATH_INFO"] = pi[len(P):] or "/"
        gz = "gzip" in (environ.pop("HTTP_ACCEPT_ENCODING", None) or "").lower()
        host = (environ.get("HTTP_X_FORWARDED_HOST") or environ.get("HTTP_HOST") or "").split(",")[0].strip().lower()
        st = {}

        def fix_loc(v):
            if v.startswith("/") and not v.startswith("//"):
                return v if (v == P or v.startswith(P + "/") or v.startswith(P + "?")) else P + v
            m = re.match(r"^(https?://)([^/?#]+)(/[^?#]*)?(.*)$", v, re.I | re.S)
            if m and m.group(2).lower() == host:
                p = m.group(3) or "/"
                if not (p == P or p.startswith(P + "/")):
                    return m.group(1) + m.group(2) + P + p + m.group(4)
            return v

        def sr(status, headers, exc_info=None):
            out = []
            for k, v in headers:
                kl = k.lower()
                if kl == "location":
                    v = fix_loc(v)
                elif kl == "set-cookie":
                    v = re.sub(r"(?i)(;\s*path=)/(?=;|$)", lambda m: m.group(1) + P + "/", v)
                out.append((k, v))
            ctype = next((v for k, v in out if k.lower() == "content-type"), "").split(";")[0].strip().lower()
            st.update(status=status, headers=out, ctype=ctype)
            if ctype in HOST_RW_TYPES:
                st["hold"] = True
                return lambda data: st.setdefault("written", []).append(data)
            return start_response(status, out, exc_info)
        it = self.wsgi(environ, sr)
        try:
            host_enforce()                                # a visitor changed a fixed setting: back at once
        except Exception:
            pass
        if not st.get("hold"):
            return it
        try:
            body = b"".join(st.get("written", [])) + b"".join(it)
        finally:
            if hasattr(it, "close"):
                it.close()
        heads = st["headers"]
        enc = next((v for k, v in heads if k.lower() == "content-encoding"), "").lower()
        if enc == "gzip":
            import gzip as _gz
            try:
                body = _gz.decompress(body)
            except OSError:
                pass
        key = (hashlib.blake2b(body, digest_size=16).digest(), P, st["ctype"], gz)
        new = _HOST_RW["cache"].get(key)
        if new is None:
            new = host_rewrite(body.decode("utf-8", "surrogateescape"), P, self.flask_app, st["ctype"] == "text/html").encode("utf-8", "surrogateescape")
            if gz and len(new) > 2048:
                import gzip as _gz
                new = _gz.compress(new, 1)                   # level 1: a fraction of the CPU (half a core)
            if len(body) > 16384:
                _HOST_RW["cache"][key] = new; _HOST_RW["order"].append(key)
                while len(_HOST_RW["order"]) > 6:
                    _HOST_RW["cache"].pop(_HOST_RW["order"].popleft(), None)
        heads = [(k, v) for k, v in heads if k.lower() not in ("content-length", "content-encoding")]
        if gz and new[:2] == b"\x1f\x8b":
            heads.append(("Content-Encoding", "gzip"))
            if not any(k.lower() == "vary" for k, v in heads):
                heads.append(("Vary", "Accept-Encoding"))
        heads.append(("Content-Length", str(len(new))))
        start_response(st["status"], heads)
        return [new] if environ.get("REQUEST_METHOD") != "HEAD" else [b""]


_WebStream_serve_base = WebStream._serve


def _host_serve(self, app, ctx):                        # wraps: WebStream._serve (only in host mode: prefix layer + /simtun)
    if HOST["on"]:
        try:
            host_routes(app)
        except Exception as e:
            log_event("sys", f"Host mode: /simtun not available: {e}"[:200])
        app.wsgi_app = _HostPrefix(app.wsgi_app, app)
    return _WebStream_serve_base(self, app, ctx)


# wraps: WebStream._serve
WebStream._serve = _host_serve
_DemoSource_set_fps_base = DemoSource.set_fps


def _host_demo_fps(self, fps):                         # wraps: DemoSource.set_fps (host mode: at most HOST_FPS)
    _DemoSource_set_fps_base(self, fps)
    if HOST["on"]:
        self.fps = min(self.fps, HOST_FPS)


DemoSource.set_fps = _host_demo_fps
_DemoSource_init_base = DemoSource.__init__


def _host_demo_init(self):                             # wraps: DemoSource.__init__
    _DemoSource_init_base(self)
    if HOST["on"]:
        self.fps = min(self.fps, HOST_FPS)


DemoSource.__init__ = _host_demo_init
'''
if HOST_PY:
    import linecache as _hlc
    _hlc.cache["639zzzzw_host_demo.py"] = (len(HOST_PY), None, HOST_PY.splitlines(True), "639zzzzw_host_demo.py")
    exec(compile(HOST_PY, "639zzzzw_host_demo.py", "exec"), globals())
