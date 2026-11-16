#@ MoveEye – Teil 639zzzzw: «Demo beim Host» (--host-modus): die Demo auf dem Webspace des Besitzers (moveeye.kevlaschef.com/demo/) – Sperren (kein Netz nach aussen, keine Programme, keine Hardware, Dateien nur im eigenen Ordner), Pfad-Vorsilbe «/demo» (Server + kleines Skript in jeder Seite), Simulator über eine WebSocket-Leitung (/simtun). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Besitzer (15.11.2026, approved): a public demo of MoveEye on the web host behind the Basic Auth of the homepage.
#   4.15.0 (Besitzer 16.11.2026): no longer a demo but a REAL MoveEye on the host - the web simulator of the homepage is its
#   camera; without it the normal «no camera» picture (with --demo still the drawn scene). Settings and recordings stay
#   (no nightly reset; the folder stays under ~1 GB through the normal clean-up, oldest recordings first: _host_fixed);
#   motion detection only, no AI model (person detector, BioCLIP, Blinki, voices: «not available on the host», RAM); no push.
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
              "/api/storage", "/api/usb", "/api/stick", "/api/soundev", "/api/talk", "/api/piper", "/api/homekit", "/api/smalltv",
              "/api/sim/upload", "/api/own_model", "/api/fehler/fix", "/api/turbo", "/api/radio", "/api/dev", "/api/simhub",
              "/api/simintern", "/api/webpush", "/api/update", "/api/fbx/flush", "/api/relay", "/api/disco", "/api/light",
              "/api/tausch/smb", "/api/storm_test", "/api/seclogin", "/api/push")
HOST_FPS = 4.0                            # pictures per second of the drawn scene (normally 15): the host gives half a core
HOST_SIM_DOOR = 18765                     # the same door as the tunnel of 180 (sim_url http://127.0.0.1:18765, _tun_reclaim)
HOST_WS_MAX = 8 * 1024 * 1024             # one WebSocket message of the simulator (a camera picture is ~100 KB)
HOST_WS_LINES = 4                         # simulator windows at the same time (the newest one is used)
_HOST_REAL = {}


def _host_fixed():
    """settings that never change in host mode (those that reach outside, the system or other folders)"""
    d = {"record_dir": os.path.join(HOST["data"] or DATA_DIR, "recordings"), "record_max_gb": 0.5, "ai_enabled": False,
         "tausch_total_gb": 0.2, "tausch_user_gb": 0.2, "tausch_file_mb": 50.0,    # 4.15.0: the folder stays under ~1 GB (oldest first)
         "update_mode": "off", "update_url": "", "update_token": "", "update_unsigned": False, "sim_url": f"http://127.0.0.1:{HOST_SIM_DOOR}",
         "sim_auto": False, "sim_autostart": False, "hotspot_on": False, "mqtt_on": False, "backup_type": "off", "backup_url": "",
         "fleet": [], "helper_serve": False, "helper_use": False, "helper_url": "", "tunnel_on": False, "notify_on": False,
         "email_on": False, "sms_on": False, "webpush_on": False, "hp_base": "", "hp_key": "", "hp_auto": False, "hp_public": "",
         "web_password": "", "web_pw_hash": "", "map_online": False, "ai_own_url": "", "lock_on": False, "source": None,
         "web_quality": 60, "web_width": 640, "proc_width": 320, "ai_every": 3, "sim_fps": 4, "sim_eco": True, "loop_on": False,
         "timelapse_on": False}                    # half a core: fewer / smaller pictures (measured with werkzeuge/host_demo_test.py --ram)
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
    _HOST_REAL.update(connect=_s.socket.connect, connect_ex=_s.socket.connect_ex, sendto=_s.socket.sendto, bind=_s.socket.bind)

    def connect(self, addr):
        if _host_inet(self) and not _host_ip_ok(addr[0] if isinstance(addr, tuple) else addr):
            _host_note(f"a connection to {str(addr)[:60]}")
            raise PermissionError(_er.EACCES, "host mode: no connections out of this computer")
        return _HOST_REAL["connect"](self, addr)

    def connect_ex(self, addr):
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
    return _open_source_host_base(spec, thermal)


HOST_NA = "not available on the host"
HOST_AI = ("/api/ki/", "/api/tausch/bio", "/api/ai_model", "/api/own_model", "/api/piper")   # 4.15.0: no AI model on the host (RAM)
for _k, _v in {HOST_NA: ("auf dem Host nicht verfügbar", "non disponible sur l'hébergeur", "non disponibile sull'host",
                         "betg disponibel sin il host")}.items():
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
            if m is None or m.closed:
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
                idle += 1
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
        self.close()

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

    @app.before_request
    def host_guard():                                    # 4.15.0: without --demo the demo guard of 550 is off - the same routes here
        p = request.path
        ai = p.startswith(HOST_AI) or "/untersuchen" in p or "/tausch/bio" in p
        sysp = not DEMO["on"] and request.method == "POST" and p.startswith(tuple(x for x in DEMO_BLOCK if x != "/api/tausch"))
        if not (ai or sysp):
            return None
        L = norm_lang(request.args.get("lang") or CFG.get("lang"))
        return Response(json.dumps({"ok": False, "error": tr(HOST_NA, L)}), 403, mimetype="application/json")

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
var P=%PREFIX%;if(!P||window.__mwBase!==undefined)return;window.__mwBase=P;
function has(p){return p===P||p.indexOf(P+"/")===0||p.indexOf(P+"?")===0||p.indexOf(P+"#")===0;}
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
    text = rx.sub(lambda m: m.group(1) + prefix + "/" + m.group(2) if m.group(2) in segs else m.group(0), text)
    text = root.sub(lambda m: m.group(1) + prefix + "/", text)
    if html:
        tag = "<script>" + HOST_SHIM_JS.replace("%PREFIX%", json.dumps(prefix)) + "</script>"
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
