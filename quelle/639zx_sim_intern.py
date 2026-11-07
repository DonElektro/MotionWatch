#@ MoveEye – Teil 639zx: «Simulator intern» – MoveEye Sim abgespeckt direkt auf dem Raspberry Pi 5 (arm64): holen und prüfen wie ein Update, auspacken, starten, mit localhost verbinden, «Beenden» = zurück zur vorherigen Verbindung. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Besitzer (03.11.2026): unterwegs ohne HP / PC den 3D-Simulator auf dem Pi selbst laufen lassen («abgespeckt»),
# zum Vorführen und Ausprobieren. Im Reiter Simulator, Karte «Verbindung»: «🧪 Simulator intern (auf diesem Pi) ausprobieren».
#   Starten  1. nur auf Linux arm64 (Pi 5, Raspberry Pi OS Bookworm 64 Bit) und nur wenn SIM3D_PI (Teil 300) ein Paket kennt
#            2. Wächter: freier Arbeitsspeicher, Temperatur, Platz auf der Karte (zu knapp = nicht starten, knapp = Hinweis)
#            3. das Paket MoveEyeSim3D_Pi.zip einmal holen - derselbe Weg wie die Downloads (sim3d_fetch): es ist ein Release-Asset
#               (Tag sim-X.Y.Z, nicht im Repository); Grösse und SHA-256 NUR aus dem signierten Block «sim.pi» von versions.json
#               (Teil 300 sim_manifest_take, Ed25519 wie die Updates). Vor dem Auspacken noch einmal geprüft.
#            4. auspacken nach <Daten>/sim3d/pi_<version>/ (nur Namen unter MoveEyeSim3D/, keine Links, kein «..»); die SHA-256
#               der Programmdatei wird gemerkt und vor jedem Start verglichen (verändert = neu auspacken aus der geprüften ZIP)
#            5. starten als der Benutzer von MoveEye (läuft MoveEye als root-Dienst: als der Benutzer am Desktop, nie als
#               root), mit «nice» (die Erkennung von MoveEye hat Vorrang), Lite-Grafik, kleines Fenster, ohne Update;
#               eigener Daten-Ordner <Daten>/sim3d/intern_daten (stört keinen von Hand installierten Simulator)
#            6. Verbindung umstellen: Adresse http://127.0.0.1:<port>, «Simulator selbst finden» aus (sonst nähme MoveEye
#               wieder den HP), Simulation ein. Die vorherige Verbindung (Adresse, Simulation ein/aus, selbst finden) wird in
#               <Daten>/sim3d/intern.json gemerkt.
#   Beenden  Simulator beenden (TERM, nach 8 s KILL) und die vorherige Verbindung wiederherstellen - z. B. wieder der HP.
#            Ebenso, wenn das Fenster geschlossen wird / der Simulator abstürzt, oder der Wächter eingreift (zu heiss: ab 85 °C,
#            zu wenig Speicher: unter 250 MB frei, zweimal hintereinander).
# Ohne Desktop am Pi: mit Xvfb (falls installiert, «sudo apt install xvfb») - dann rechnet nur der Prozessor, sehr langsam.
# Web: /api/simintern (GET Zustand, POST start / stop; nur Rolle admin). Fenster (Tk): Abschnitt Simulator, ein Knopf.
# Texte: Englisch = Schlüssel, Deutsch / Französisch / Italienisch / Romanisch unten (_HX_SIMPI).
# Test: werkzeuge/sim_intern_test.py (gefälschtes Paket, ohne echten Simulator).
# ----------------------------------------------------------------------------
SIMPI = {"proc": None, "xvfb": None, "phase": "idle", "msg": "", "want": False, "confirm": False, "who": "", "t": 0.0,
          "port": 0, "mode": "", "warn": [], "watch": False, "bad": 0}
SIMPI_LOCK = threading.Lock()
SIMPI_PORTS = (8765, 8775, 8785)          # die Ports des 3D-Simulators (SIM_SCAN_PORTS, Teil 300): der erste freie
SIMPI_RAM_MIN = 700                       # MB frei: darunter nicht starten
SIMPI_RAM_WARN = 1500                     # MB frei: darunter ein Hinweis
SIMPI_RAM_STOP = 250                      # MB frei: darunter beendet der Wächter den Simulator (zweimal hintereinander)
SIMPI_TEMP_WARN = 70.0                    # °C: Hinweis
SIMPI_TEMP_MAX = 80.0                     # °C: nicht starten
SIMPI_TEMP_STOP = 85.0                    # °C: der Wächter beendet den Simulator
SIMPI_DISK_MIN = 400                      # MB frei auf der Karte für ZIP + ausgepackt
SIMPI_NICE = 15                           # tiefere Priorität: die Erkennung von MoveEye geht vor
SIMPI_EXE = "MoveEyeSim3D.arm64"


def simpi_dir():
    return os.path.join(DATA_DIR, "sim3d")


def simpi_inst_dir(pkg=None):
    return os.path.join(simpi_dir(), "pi_" + (pkg or SIM3D_PI)["version"])


def simpi_state_file():
    return os.path.join(simpi_dir(), "intern.json")


def simpi_arch_ok():
    """Linux auf arm64 (aarch64) - der Raspberry Pi 5 mit 64-Bit-System. MW_SIMPI_TEST=1 nur für werkzeuge/sim_intern_test.py"""
    import platform
    if os.environ.get("MW_SIMPI_TEST") == "1":
        return True
    return sys.platform.startswith("linux") and platform.machine().lower() in ("aarch64", "arm64")


def simpi_possible():
    """(ja/nein, warum nicht)"""
    if not simpi_arch_ok():
        return False, "only on a Raspberry Pi 5 with a 64-bit system (arm64)"
    return True, ""                                       # size / checksum: only from the signed «sim.pi» (fetched at the start)


def _simpi_read():
    try:
        with open(simpi_state_file(), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _simpi_write(d):
    try:
        os.makedirs(simpi_dir(), exist_ok=True)
        tmp = simpi_state_file() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, simpi_state_file())
    except OSError:
        pass


def _simpi_pid_alive(pid, exe=""):
    """lebt der Prozess noch, und ist es wirklich unser Simulator (nicht eine neue Nummer für etwas anderes)?"""
    try:
        pid = int(pid)
        if pid <= 1:
            return False
        os.kill(pid, 0)
    except (ValueError, TypeError, ProcessLookupError):
        return False
    except PermissionError:
        pass                                               # anderer Benutzer (MoveEye root, Simulator als Desktop-Benutzer)
    if not exe:
        return True
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return os.path.basename(exe).encode() in f.read()
    except OSError:
        return True


def simpi_running():
    """läuft «Simulator intern» (auch nach einem Neustart von MoveEye: der Simulator läuft in einer eigenen Sitzung weiter)"""
    p = SIMPI["proc"]
    if p is not None and p.poll() is None:
        return True
    d = _simpi_read()
    return bool(d.get("pid")) and _simpi_pid_alive(d.get("pid"), d.get("exe", ""))


def simpi_resources():
    """freier Arbeitsspeicher (MB), Gesamt (MB), Temperatur (°C), Last pro Kern, freier Platz (MB) - None = unbekannt"""
    out = {"ram_free": None, "ram_total": None, "temp": None, "load": None, "disk_free": None}
    try:
        mi = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, _s, v = line.partition(":")
                mi[k.strip()] = int(v.split()[0]) // 1024
        out["ram_free"] = mi.get("MemAvailable"); out["ram_total"] = mi.get("MemTotal")
    except (OSError, ValueError, IndexError):
        pass
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            out["temp"] = round(int(f.read().strip()) / 1000.0, 1)
    except (OSError, ValueError):
        pass
    try:
        out["load"] = round(os.getloadavg()[0] / max(1, os.cpu_count() or 1), 2)
    except (OSError, AttributeError):
        pass
    try:
        os.makedirs(simpi_dir(), exist_ok=True)
        st = os.statvfs(simpi_dir())
        out["disk_free"] = int(st.f_bavail * st.f_frsize / 1048576)
    except (OSError, AttributeError):
        pass
    return out


def simpi_check(res=None):
    """(Hindernis oder "", [Hinweise]) vor dem Start"""
    r = res or simpi_resources()
    warn = []
    if r["ram_free"] is not None:
        if r["ram_free"] < SIMPI_RAM_MIN:
            return "too little free memory (%d MB) - close other programs first" % r["ram_free"], warn
        if r["ram_free"] < SIMPI_RAM_WARN:
            warn.append("little free memory")
    if r["temp"] is not None:
        if r["temp"] >= SIMPI_TEMP_MAX:
            return "the Pi is too hot (%.0f °C) - let it cool down first" % r["temp"], warn
        if r["temp"] >= SIMPI_TEMP_WARN:
            warn.append("the Pi is warm")
    need = SIMPI_DISK_MIN if not os.path.isfile(os.path.join(simpi_inst_dir(), "MoveEyeSim3D", SIMPI_EXE)) else 50
    if r["disk_free"] is not None and r["disk_free"] < need:
        return "too little room on the memory card (%d MB free)" % r["disk_free"], warn
    if r["load"] is not None and r["load"] > 0.9:
        warn.append("the Pi is busy")
    return "", warn


def _simpi_sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def simpi_install(pkg=None):
    """die geholte ZIP prüfen und auspacken; (Pfad der Programmdatei, Fehler)"""
    pkg = pkg or SIM3D_PI
    z_ = sim3d_path(pkg)
    d_ = simpi_inst_dir(pkg)
    exe = os.path.join(d_, "MoveEyeSim3D", SIMPI_EXE)
    mark = os.path.join(d_, "geprueft.json")
    try:
        m = json.load(open(mark, encoding="utf-8"))
        if m.get("zip") == pkg["sha256"] and os.path.isfile(exe) and _simpi_sha(exe) == m.get("exe"):
            return exe, ""                                 # schon ausgepackt, unverändert
    except (OSError, ValueError, AttributeError):
        pass
    if not sim3d_ready(pkg) or _simpi_sha(z_) != pkg["sha256"]:
        try:
            os.remove(z_)                                   # verändert / unvollständig: beim nächsten Start neu holen
        except OSError:
            pass
        return "", "the package is damaged - it is fetched again at the next start"
    tmp = d_ + ".neu"
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        with zipfile.ZipFile(z_) as z:
            for info in z.infolist():
                n = info.filename
                if (n.startswith("/") or "\\" in n or ".." in n.split("/") or not n.startswith("MoveEyeSim3D/")
                        or ((info.external_attr >> 16) & 0o170000) == 0o120000):
                    raise ValueError("bad file name in the package")
            z.extractall(tmp)
        x_ = os.path.join(tmp, "MoveEyeSim3D", SIMPI_EXE)
        if not os.path.isfile(x_):
            raise ValueError(SIMPI_EXE + " missing in the package")
        for root_, ds, fs in os.walk(tmp):
            os.chmod(root_, 0o755)
            for f in fs:
                os.chmod(os.path.join(root_, f), 0o755 if f.endswith((".arm64", ".sh")) else 0o644)
        with open(os.path.join(tmp, "geprueft.json"), "w", encoding="utf-8") as f:
            json.dump({"zip": pkg["sha256"], "exe": _simpi_sha(x_), "version": pkg["version"]}, f)
        shutil.rmtree(d_, ignore_errors=True)
        os.replace(tmp, d_)
    except (OSError, ValueError, zipfile.BadZipFile) as e:
        shutil.rmtree(tmp, ignore_errors=True)
        return "", "unpacking: " + str(e)[:120]
    for old in glob.glob(os.path.join(simpi_dir(), "pi_*")):
        if old != d_ and os.path.isdir(old) and os.path.basename(old)[3:4].isdigit():
            shutil.rmtree(old, ignore_errors=True)          # nur die eigenen, älteren Fassungen von «Simulator intern»
    log_event("sys", f"{pkg['label']} {pkg['version']} checked and unpacked ({d_})")
    return exe, ""


def _simpi_user():
    """(uid, gid, home, name, runtime-Ordner) für den Simulator: MoveEye selbst - oder, wenn MoveEye als root läuft, der
    Benutzer am Desktop (nie root). None = kein passender Benutzer."""
    import pwd
    me = os.getuid() if hasattr(os, "getuid") else 1000
    if me != 0 or os.environ.get("MW_SIMPI_TEST") == "1":     # (Test: werkzeuge/sim_intern_test.py läuft im Container als root)
        p = pwd.getpwuid(me)
        return me, p.pw_gid, p.pw_dir, p.pw_name, os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{me}"
    for d in sorted(glob.glob("/run/user/*")):
        try:
            uid = int(os.path.basename(d))
        except ValueError:
            continue
        if uid >= 1000 and (glob.glob(os.path.join(d, "wayland-*")) or os.path.exists(os.path.join(d, "bus"))):
            try:
                p = pwd.getpwuid(uid)
                return uid, p.pw_gid, p.pw_dir, p.pw_name, d
            except KeyError:
                continue
    sudo_u = os.environ.get("SUDO_USER")
    if sudo_u:
        try:
            p = pwd.getpwnam(sudo_u)
            if p.pw_uid != 0:
                return p.pw_uid, p.pw_gid, p.pw_dir, p.pw_name, f"/run/user/{p.pw_uid}"
        except KeyError:
            pass
    return None


def _simpi_display(rt):
    """(Umgebung für den Bildschirm, Art) - Art «x11», «wayland» oder "" (kein Desktop)"""
    env = {}
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        for k in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
            if os.environ.get(k):
                env[k] = os.environ[k]
        return env, "x11" if env.get("DISPLAY") else "wayland"
    way = next((os.path.basename(x) for x in sorted(glob.glob(os.path.join(rt, "wayland-*"))) if not x.endswith(".lock")), "")
    if os.path.exists("/tmp/.X11-unix/X0"):
        env["DISPLAY"] = ":0"                               # Xwayland am Desktop (Godot öffnet sein Fenster darüber)
        if way:
            env["WAYLAND_DISPLAY"] = way
        return env, "x11"
    if way:
        env["WAYLAND_DISPLAY"] = way
        return env, "wayland"
    return env, ""


def _simpi_port_free(port):
    import socket
    s_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s_.settimeout(0.3)
        return s_.connect_ex(("127.0.0.1", port)) != 0
    finally:
        s_.close()


def simpi_cmd(exe, port, wayland=False):
    """die Befehlszeile: nice (die Erkennung von MoveEye geht vor), Lite-Grafik, kleines Fenster, ohne Update / Rundgang / «Hoch» / Foto-Inhalte, sendet sofort"""
    pre = []
    if shutil.which("nice"):
        pre = ["nice", "-n", str(SIMPI_NICE)]
    eng = ["--resolution", "1024x600", "--max-fps", "20"] + (["--display-driver", "wayland"] if wayland else [])
    return pre + [exe] + eng + ["--", "--grafik", "lite", "--quality", "simple", "--no-update", "--no-tour", "--no-hoch",
                                "--no-inhalte", "--stream", "--port", str(port), "--moveeye-intern"]


def _simpi_url_set(url):
    CFG["sim_url"] = url
    SIM.update(t=0.0, ok=False, msg="connecting …")
    w = WATCH_REF.get("w")
    if CFG.get("sim_on") and w is not None and str(CFG.get("source", "")).startswith("sim:"):
        try:
            w._open_gen += 1; w._start_opener(CFG["source"])
        except Exception:
            pass


def _simpi_launch(exe, who):
    """den Simulator starten und die Verbindung umstellen; (ok, Fehler)"""
    u = _simpi_user()
    if u is None:
        return False, "no user at the desktop of the Pi found (the simulator never runs as root)"
    uid, gid, home, name, rt = u
    env_d, kind = _simpi_display(rt)
    data = os.path.join(simpi_dir(), "intern_daten")       # eigener Daten-Ordner des Simulators (Einstellungen, Protokoll)
    os.makedirs(data, exist_ok=True)
    kw = {}
    if hasattr(os, "getuid") and os.getuid() == 0:
        import pwd
        try:
            groups = os.getgrouplist(name, gid)              # video / render für die Grafik, ohne die Gruppen von root
        except OSError:
            groups = [gid]
        kw = {"user": uid, "group": gid, "extra_groups": [g_ for g_ in groups if g_ != 0]}
        for root_, ds, fs in os.walk(data):
            for x in [root_] + [os.path.join(root_, f) for f in fs]:
                try:
                    os.chown(x, uid, gid)
                except OSError:
                    pass
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home, "USER": name, "LANG": os.environ.get("LANG", "C.UTF-8"),
           "XDG_RUNTIME_DIR": rt, "XDG_DATA_HOME": data, "XDG_CONFIG_HOME": os.path.join(data, "config"),
           "XDG_CACHE_HOME": os.path.join(data, "cache")}
    if os.path.exists(os.path.join(rt, "bus")):
        env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={rt}/bus"
    env.update(env_d)
    xv = None
    if not kind:
        xvfb = shutil.which("Xvfb")
        if not xvfb:
            return False, "no desktop on the Pi - Raspberry Pi OS with desktop needed (or: sudo apt install xvfb, very slow)"
        n_ = 77
        while os.path.exists(f"/tmp/.X11-unix/X{n_}") and n_ < 90:
            n_ += 1
        try:
            xv = subprocess.Popen([xvfb, f":{n_}", "-screen", "0", "1024x600x24", "-nolisten", "tcp"], env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, **kw)
        except Exception as e:
            return False, "Xvfb: " + str(e)[:100]
        time.sleep(1.5)
        env["DISPLAY"] = f":{n_}"; kind = "xvfb"
    port = next((p for p in SIMPI_PORTS if _simpi_port_free(p)), 0)
    if not port:
        if xv is not None:
            xv.terminate()
        return False, "the simulator ports 8765 / 8775 / 8785 are all busy on the Pi"
    try:
        logf = open(os.path.join(data, "simulator.log"), "wb")
        p = subprocess.Popen(simpi_cmd(exe, port, kind == "wayland"), cwd=os.path.dirname(exe), env=env, stdin=subprocess.DEVNULL,
                             stdout=logf, stderr=subprocess.STDOUT, start_new_session=True, **kw)
        logf.close()
    except Exception as e:
        if xv is not None:
            xv.terminate()
        return False, "start: " + str(e)[:120]
    st_ = _simpi_read()
    prev = st_.get("prev") if st_.get("pid") and _simpi_pid_alive(st_.get("pid"), st_.get("exe", "")) else None
    if not isinstance(prev, dict):                               # die Verbindung von vorher (z. B. der HP) - einmal merken
        prev = {"url": CFG.get("sim_url") or "", "on": bool(CFG.get("sim_on")), "auto": bool(CFG.get("sim_auto")),
                "source": CFG.get("source", "")}
    SIMPI.update(proc=p, xvfb=xv, port=port, mode=kind, t=time.time())
    _simpi_write({"pid": p.pid, "exe": exe, "port": port, "mode": kind, "xvfb": xv.pid if xv is not None else 0,
                   "t": time.time(), "prev": prev, "version": SIM3D_PI["version"], "who": who})
    CFG["sim_auto"] = False                                       # sonst nimmt MoveEye wieder den Simulator am PC (sim_auto_adopt)
    _simpi_url_set(f"http://127.0.0.1:{port}")
    ok_, err_ = (True, "")
    if not CFG.get("sim_on"):
        ok_, err_ = sim_set(True, who, True)                      # bestätigt beim Start (die Seite fragt, wenn scharf)
    save_settings()
    log_event("sys", f"Simulator intern {SIM3D_PI['version']} started on this Pi ({kind}, port {port}, nice {SIMPI_NICE}, {who})"
                     + (f" - before: {prev.get('url')} ({'on' if prev.get('on') else 'off'})" if prev.get("url") else ""))
    _simpi_watch_start()
    return ok_, err_


def _simpi_work():
    """im Hintergrund: holen (einmal), prüfen, auspacken, starten"""
    try:
        if not sim3d_ready(SIM3D_PI):
            SIMPI["phase"] = "loading"
            sim3d_fetch(SIM3D_PI, SIM3D_PI_DL)
            time.sleep(0.3)
            while SIM3D_PI_DL["running"]:
                time.sleep(0.5)
            if not sim3d_ready(SIM3D_PI):
                SIMPI["msg"] = SIM3D_PI_DL["msg"] or "could not be fetched"
                return
        SIMPI["phase"] = "unpacking"
        exe, err = simpi_install()
        if err:
            SIMPI["msg"] = err
            return
        SIMPI["phase"] = "starting"
        ok_, err_ = _simpi_launch(exe, SIMPI["who"])
        if not ok_:
            SIMPI["msg"] = err_
    except Exception as e:
        SIMPI["msg"] = str(e)[:160]
    finally:
        SIMPI["phase"] = "idle"; SIMPI["want"] = False


def simpi_start(who="web", confirm=False, force=False):
    """«Simulator intern» starten (holt das Paket beim ersten Mal); (ok, Fehler, braucht Bestätigung)"""
    ok, why = simpi_possible()
    if not ok:
        return False, why, ""
    if simpi_running():
        return True, "", ""
    with SIMPI_LOCK:
        if SIMPI["want"]:
            return True, "", ""
        block, warn = simpi_check()
        SIMPI["warn"] = warn
        if block and not force:
            return False, block, ""
        if CFG.get("armed") and not CFG.get("sim_on") and not confirm:
            return False, "MoveEye is armed. The simulation replaces the real camera - nothing real is watched then. Disarm and switch the simulation on?", "armed"
        SIMPI.update(want=True, msg="", who=who, phase="loading" if not sim3d_ready(SIM3D_PI) else "unpacking")
    threading.Thread(target=_simpi_work, daemon=True, name="simintern").start()
    return True, "", ""


def _simpi_kill(pid, grace=8.0):
    import signal
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return
    if pid <= 1:
        return
    for sig, wait in ((signal.SIGTERM, grace), (signal.SIGKILL, 2.0)):
        try:
            os.killpg(pid, sig)                             # eigene Sitzung: der ganze Simulator (nice davor)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                os.kill(pid, sig)
            except (ProcessLookupError, PermissionError, OSError):
                return
        t0 = time.time()
        while time.time() - t0 < wait:
            p = SIMPI["proc"]
            if p is not None and p.pid == pid:
                if p.poll() is not None:
                    return
            elif not _simpi_pid_alive(pid):
                return
            time.sleep(0.2)


def _simpi_restore(who, why=""):
    """die Verbindung von vorher wieder herstellen (Adresse, selbst finden, Simulation ein / aus)"""
    st_ = _simpi_read()
    prev = st_.get("prev") if isinstance(st_.get("prev"), dict) else None
    port = int(st_.get("port") or SIMPI["port"] or 0)
    mine = port and sim_base().rstrip("/") == f"http://127.0.0.1:{port}"
    if prev is not None and (mine or not CFG.get("sim_url")):
        u = str(prev.get("url") or "")
        if u == f"http://127.0.0.1:{port}":
            u = "http://127.0.0.1:8765"
        _simpi_url_set(u or "http://127.0.0.1:8765")
        CFG["sim_auto"] = bool(prev.get("auto", True))
        if not prev.get("on") and CFG.get("sim_on"):
            sim_set(False, who)
        save_settings()
    try:
        os.remove(simpi_state_file())
    except OSError:
        pass
    SIMPI.update(proc=None, xvfb=None, port=0, mode="")
    log_event("sys", "Simulator intern stopped (" + who + ")" + (": " + why if why else "")
              + (f" - back to {CFG.get('sim_url')} ({'on' if CFG.get('sim_on') else 'off'})" if prev else ""))


def simpi_stop(who="web", why=""):
    """beenden und zurück zur vorherigen Verbindung"""
    st_ = _simpi_read()
    p = SIMPI["proc"]
    pid = p.pid if p is not None else st_.get("pid")
    if pid:
        SIMPI["phase"] = "stopping"
        _simpi_kill(pid)
    for x in (SIMPI["xvfb"].pid if SIMPI["xvfb"] is not None else 0, st_.get("xvfb") or 0):
        if x:
            _simpi_kill(x, 2.0)
    if p is not None:
        try:
            p.wait(timeout=1)
        except Exception:
            pass
    _simpi_restore(who, why)
    SIMPI["phase"] = "idle"; SIMPI["want"] = False
    if why:
        SIMPI["msg"] = why
    return True, ""


def _simpi_watch():
    """Wächter alle 10 s: Simulator weg (Fenster zu / abgestürzt) -> Verbindung zurück; zu heiss / zu wenig Speicher -> beenden"""
    while True:
        time.sleep(10)
        try:
            st_ = _simpi_read()
            if not st_.get("pid"):
                if SIMPI["proc"] is None:
                    SIMPI["watch"] = False
                    return
                continue
            if not simpi_running():
                SIMPI["msg"] = "the simulator was closed - back to the connection before"
                for x in (st_.get("xvfb") or 0,):
                    if x:
                        _simpi_kill(x, 2.0)
                _simpi_restore("closed", "window closed or crashed")
                continue
            r = simpi_resources()
            hot = r["temp"] is not None and r["temp"] >= SIMPI_TEMP_STOP
            low = r["ram_free"] is not None and r["ram_free"] < SIMPI_RAM_STOP
            SIMPI["bad"] = SIMPI["bad"] + 1 if (hot or low) else 0
            if SIMPI["bad"] >= 2:
                SIMPI["bad"] = 0
                why = "too hot (%.0f °C)" % r["temp"] if hot else "too little free memory (%d MB)" % r["ram_free"]
                simpi_stop("guard", why)
                log_event("sys", "Simulator intern: stopped by the guard - " + why + " (MoveEye's detection goes first)")
        except Exception:
            pass


def _simpi_watch_start():
    if not SIMPI["watch"]:
        SIMPI["watch"] = True
        threading.Thread(target=_simpi_watch, daemon=True, name="simpi-watch").start()


def simpi_state():
    """für die Seite / das Fenster"""
    ok, why = simpi_possible()
    on = simpi_running()
    st_ = _simpi_read() if on else {}
    if on:
        _simpi_watch_start()                                # z. B. nach einem Neustart von MoveEye
    prev = st_.get("prev") if isinstance(st_.get("prev"), dict) else None
    port = int(st_.get("port") or SIMPI["port"] or 0)
    size = SIM3D_PI.get("size") or 0
    res = simpi_resources()
    phase = "running" if on and SIMPI["phase"] in ("idle", "starting") else SIMPI["phase"]
    return {"possible": ok, "why": why, "on": on, "phase": phase, "version": SIM3D_PI["version"], "size_mb": round(size / 1e6),
            "ready": bool(size) and sim3d_ready(SIM3D_PI), "pct": int(100 * SIM3D_PI_DL["got"] / size) if size else 0,
            "msg": SIMPI["msg"], "warn": SIMPI["warn"] if not on else simpi_check(res)[1], "port": port,
            "mode": st_.get("mode") or SIMPI["mode"], "since": int(time.time() - float(st_.get("t") or time.time())) if on else None,
            "connected": bool(on and port and sim_base().rstrip("/") == f"http://127.0.0.1:{port}" and SIM.get("ok")),
            "prev": {"url": prev.get("url", ""), "on": bool(prev.get("on"))} if prev else None, "res": res,
            "armed": bool(CFG.get("armed")) and not CFG.get("sim_on")}


def simpi_routes(app, reply, body):
    """/api/simintern - GET Zustand, POST {action: start | stop}; nur der Besitzer (Rolle admin)"""
    from flask import g, request

    @app.route("/api/simintern", methods=["GET", "POST"])
    def api_simintern():
        if getattr(g, "role", "admin") != "admin":
            return reply({"ok": False, "error": "not allowed"}, 403)
        if request.method == "GET":
            s_ = simpi_state(); L_ = norm_lang(request.args.get("lang"))
            s_["msg"] = tr_err(s_["msg"], L_) if s_["msg"] else ""
            return reply(dict(s_, ok=True))
        d = body(); lang = norm_lang(d.get("lang"))
        a_ = str(d.get("action") or "")
        who_ = "web " + (request.remote_addr or "?")
        if a_ == "start":
            ok_, err_, need = simpi_start(who_, bool(d.get("confirm")), bool(d.get("force")))
            if need:
                return reply({"ok": False, "need_confirm": need, "error": tr_err(err_, lang), "state": simpi_state()})
            return reply({"ok": ok_, "error": tr_err(err_, lang) if err_ else None, "state": simpi_state()}, 200 if ok_ else 400)
        if a_ == "stop":
            ok_, err_ = simpi_stop(who_)
            return reply({"ok": ok_, "error": tr_err(err_, lang) if err_ else None, "state": simpi_state()})
        return reply({"ok": False, "error": "unknown action"}, 400)


_smalltv_routes_simpi_base = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zx: /api/simintern («Simulator intern» auf dem Pi)
    _smalltv_routes_simpi_base(app, reply, body)
    simpi_routes(app, reply, body)


# ---- Fenster (Tk), Abschnitt Simulator: ein Knopf Starten / Beenden + eine Zeile Zustand ----
def simpi_tk_build(app, parent):
    ok, _why = simpi_possible()
    if not ok and not simpi_running():
        return
    ttk.Label(parent, text="🧪 " + tr("Simulator intern (on this Pi)"), style="Mut.TLabel").pack(anchor="w", pady=(8, 0))
    ttk.Label(parent, text=tr("si-note"), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w")
    lbl = ttk.Label(parent, text="", style="Mut.TLabel", wraplength=330, justify="left")
    btn = ttk.Button(parent, text="")

    def paint():
        try:
            s_ = simpi_state()
            btn.config(text=("⏹ " + tr("Stop the simulator intern")) if s_["on"] else ("🧪 " + tr("Try the simulator intern")),
                       state="disabled" if s_["phase"] in ("loading", "unpacking", "starting", "stopping") else "normal")
            lbl.config(text=simpi_line(s_))
            app.root.after(3000, paint)
        except Exception:
            pass

    def go():
        s_ = simpi_state()
        if s_["on"]:
            threading.Thread(target=lambda: simpi_stop("window"), daemon=True).start()
        else:
            ok_, err_, need = simpi_start("window")
            if need and messagebox.askyesno("MoveEye", tr(err_), parent=app.root):
                ok_, err_, need = simpi_start("window", True)
            if not ok_ and err_ and not need:
                lbl.config(text="⚠ " + tr_err(err_))
    btn.config(command=go)
    btn.pack(fill="x", pady=(4, 0))
    lbl.pack(anchor="w", pady=(2, 0))
    paint()


def simpi_line(s_, lang=None):
    """eine Zeile Zustand (Fenster; die Seite baut ihre eigene)"""
    T = lambda k: tr(k, lang)
    if s_["phase"] == "loading":
        return T("fetching the package") + f" … {s_['pct']} %"
    if s_["phase"] == "unpacking":
        return T("checking and unpacking …")
    if s_["phase"] == "starting":
        return T("starting …")
    if s_["phase"] == "stopping":
        return T("stopping …")
    if s_["on"]:
        p_ = s_.get("prev") or {}
        return (T("running on this Pi") + f" · Port {s_['port']}" + (" · " + T("connected") if s_["connected"] else "")
                + ("\n" + T("Stop: back to") + " " + p_["url"] + (" (" + T("simulation on") + ")" if p_.get("on") else "") if p_.get("url") else ""))
    return ("⚠ " + tr_err(s_["msg"], lang) + "\n" if s_["msg"] else "") + (
        T("package ready") if s_["ready"] else T("fetched at the first start") + (f" ({s_['size_mb']} MB)" if s_["size_mb"] else ""))


# ---- Web: Reiter Simulator, Karte «Verbindung»: ein Unterabschnitt; Karte «Status»: Zeile + «Beenden», solange er läuft ----
SIMPI_HTML = ('<details class="sub" id="c-intern" hidden><summary><svg viewBox="0 0 24 24"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/>'
               '<path d="M7.5 15h9"/></svg><span data-i18n="si-title">si-title</span><span class="mut" id="si-chip" style="font-weight:400;flex:none"></span></summary>'
               '<div id="si-box"></div></details>')
SIMPI_JS = r"""<script>
Object.assign(I18N.de, /*SIDE*/{});
(function () {
  const C = document.getElementById("c-intern"), B = document.getElementById("si-box"); if (!C || !B) return;
  let J = null, busy = false, SIG = "";
  const mb = v => v == null ? "–" : v >= 1000 ? (v / 1024).toFixed(1) + " GB" : v + " MB";
  async function get() {
    try { const r = await fetch("/api/simintern?lang=" + encodeURIComponent(LANG || ""), {cache: "no-store"}); J = r.ok ? await r.json() : null; } catch (e) { J = null; }
    paint(); clearTimeout(get.t);
    get.t = setTimeout(get, J && (J.phase !== "idle" || J.on) ? 2000 : 6000);
  }
  async function act(a, extra) {
    busy = true; SIG = ""; paint();
    try {
      let r = await post("/api/simintern", Object.assign({action: a, lang: LANG}, extra || {}));
      if (r && r.need_confirm) { r = confirm(r.error) ? await post("/api/simintern", Object.assign({action: a, lang: LANG, confirm: true}, extra || {})) : null; }
      if (r && r.ok === false && r.error) toast("⚠ " + r.error);
    } catch (e) {} finally { busy = false; SIG = ""; get(); if (typeof load === "function") setTimeout(load, 400); }
  }
  function line(cls, txt) { const d = el("div", cls, txt); B.appendChild(d); return d; }
  function paint() {
    const sig = JSON.stringify([J, busy, LANG]); if (sig === SIG) return; SIG = sig;
    C.hidden = !J || !(J.possible || J.on); if (C.hidden) { runPaint(); return; }
    C.classList.toggle("act", !!(J.on && J.connected));
    const ph = J.phase, work = busy || ["loading", "unpacking", "starting", "stopping"].indexOf(ph) >= 0;
    document.getElementById("si-chip").textContent = J.on ? "· " + t("runs") : work ? "· …" : "";
    B.textContent = "";
    line("mut", "🐢 " + t("si-note"));
    const R = J.res || {}, w = (J.warn || []).map(x => t(x));
    const rs = line("mut", t("free memory") + " " + mb(R.ram_free) + (R.ram_total ? " / " + mb(R.ram_total) : "") + " · " + (R.temp == null ? "–" : Math.round(R.temp) + " °C")
      + (R.load == null ? "" : " · " + t("load") + " " + Math.round(R.load * 100) + " %"));
    if (w.length) { rs.textContent += " · ⚠ " + w.join(", "); rs.style.color = "#d29922"; }
    let st = "";
    if (ph === "loading") st = t("fetching the package") + " … " + (J.pct || 0) + " %";
    else if (ph === "unpacking") st = t("checking and unpacking …");
    else if (ph === "starting") st = t("starting …");
    else if (ph === "stopping") st = t("stopping …");
    else if (J.on) st = "🟢 " + t("running on this Pi") + " · Port " + J.port + (J.mode === "xvfb" ? " · " + t("without screen (Xvfb, very slow)") : "")
      + " · " + (J.connected ? t("connected") : t("connecting …"));
    else st = J.ready ? "✓ " + t("package ready") + " (" + J.version + ", " + t("checked like an update") + ")" : t("fetched at the first start") + " (" + (J.size_mb ? J.size_mb + " MB, " : "") + t("checked like an update") + ")";
    const sl = line("", st); sl.style.cssText = "font-size:14px;margin-top:6px";
    if (ph === "loading") { const p = el("div", "tr-prog"); const i = document.createElement("i"); i.style.width = (J.pct || 0) + "%"; p.appendChild(i); B.appendChild(p); }
    if (J.msg && !J.on && !work) { const m = line("mut", "⚠ " + t(J.msg)); m.style.color = "var(--red,#ff5b4b)"; }
    if (J.on) {
      const P = J.prev;
      line("mut", t("Stop: back to") + " " + (P && P.url ? P.url + (P.on ? " (" + t("simulation on") + ")" : " (" + t("simulation off") + ")") : t("the connection before")));
    } else if (J.armed) line("mut", "🛡 " + t("MoveEye is armed - the simulation replaces the real camera while it runs."));
    if (!J.possible && !J.on) { line("mut", "⚠ " + t(J.why)); }
    const b = el("button", J.on ? "sec" : "", J.on ? "⏹ " + t("Stop the simulator intern") : "🧪 " + t("Try the simulator intern"));
    b.type = "button"; b.id = "si-btn"; b.style.cssText = "width:100%;margin-top:8px"; b.disabled = work || (!J.possible && !J.on);
    b.onclick = () => act(J.on ? "stop" : "start"); B.appendChild(b);
    runPaint();
  }
  // Karte «Status» (nur mit eingeschalteter Simulation sichtbar): solange er läuft eine Zeile und «Beenden»
  function runPaint() {
    const body = document.getElementById("s-stbody"); if (!body) return;
    let r = document.getElementById("si-run");
    if (!J || !J.on) { if (r) r.remove(); return; }
    if (!r) { r = el("div", "supd"); r.id = "si-run"; r.style.cssText = "display:flex;gap:10px;align-items:center;flex-wrap:wrap"; body.prepend(r); }
    r.textContent = "";
    const tx = el("div", "", "🧪 " + t("Simulator intern runs on this Pi") + " – " + t("slower, only for showing and trying out")); tx.style.cssText = "flex:1 1 220px;font-size:14px";
    const b = el("button", "sec", "⏹ " + t("Stop")); b.type = "button"; b.disabled = busy || J.phase === "stopping"; b.onclick = () => act("stop");
    r.append(tx, b);
  }
  get();
  // Programme und Downloads: auf dem Pi ist die Linux-ZIP (x86_64) die falsche - Hinweis
  const dl = document.getElementById("d-3dln");
  const hint = () => { if (dl && J && J.possible && !dl.dataset.si) { dl.dataset.si = "1"; dl.textContent = (dl.textContent ? dl.textContent + " · " : "") + t("not for this Pi - use «Simulator intern»"); } };
  setTimeout(hint, 2500);
})();
</script>"""

_HX_SIMPI = {
    'si-title': ('Simulator intern (auf diesem Pi) ausprobieren', 'Essayer le simulateur interne (sur ce Pi)',
                 'Provare il simulatore interno (su questo Pi)', 'Empruvar il simulatur intern (sin quest Pi)'),
    'si-note': ('Langsamer, nur zum Vorführen / Ausprobieren: MoveEye Sim läuft abgespeckt (Lite-Grafik, kleines Fenster) direkt auf '
                'diesem Pi – unterwegs ohne HP oder PC. Beim ersten Mal wird das Paket geholt und wie ein Update geprüft. «Beenden» '
                'stellt die Verbindung von vorher wieder her (z. B. den HP). Die Erkennung von MoveEye hat Vorrang.',
                'Plus lent, seulement pour montrer / essayer : MoveEye Sim tourne en version allégée (graphisme Lite, petite fenêtre) '
                'directement sur ce Pi – en déplacement sans HP ni PC. La première fois, le paquet est téléchargé et vérifié comme une '
                'mise à jour. « Arrêter » rétablit la connexion d’avant (p. ex. le HP). La détection de MoveEye a la priorité.',
                'Più lento, solo per mostrare / provare: MoveEye Sim gira in versione ridotta (grafica Lite, finestra piccola) '
                'direttamente su questo Pi – in viaggio senza HP né PC. La prima volta il pacchetto viene scaricato e verificato come un '
                'aggiornamento. «Termina» ripristina il collegamento di prima (p. es. l’HP). Il rilevamento di MoveEye ha la precedenza.',
                'Pli plaun, mo per preschentar / empruvar: MoveEye Sim gira en versiun reducida (grafica Lite, fanestra pitschna) '
                'directamain sin quest Pi – en viadi senza HP u PC. L’emprima giada vegn il pachet chargià giu e verifitgà sco in '
                'update. «Terminar» restabilescha la colliaziun da pli baud (p.ex. il HP). La identificaziun da MoveEye ha la prioritad.'),
    'Simulator intern (on this Pi)': ('Simulator intern (auf diesem Pi)', 'Simulateur interne (sur ce Pi)', 'Simulatore interno (su questo Pi)',
                                      'Simulatur intern (sin quest Pi)'),
    'Try the simulator intern': ('Simulator intern starten', 'Démarrer le simulateur interne', 'Avviare il simulatore interno', 'Aviar il simulatur intern'),
    'Stop the simulator intern': ('Simulator intern beenden', 'Arrêter le simulateur interne', 'Terminare il simulatore interno', 'Terminar il simulatur intern'),
    'Simulator intern runs on this Pi': ('Simulator intern läuft auf diesem Pi', 'Le simulateur interne tourne sur ce Pi',
                                         'Il simulatore interno gira su questo Pi', 'Il simulatur intern gira sin quest Pi'),
    'slower, only for showing and trying out': ('langsamer, nur zum Vorführen / Ausprobieren', 'plus lent, seulement pour montrer / essayer',
                                                'più lento, solo per mostrare / provare', 'pli plaun, mo per preschentar / empruvar'),
    'Stop': ('Beenden', 'Arrêter', 'Termina', 'Terminar'),
    'runs': ('läuft', 'tourne', 'gira', 'gira'),
    'free memory': ('Speicher frei', 'mémoire libre', 'memoria libera', 'memoria libra'),
    'load': ('Last', 'charge', 'carico', 'chargia'),
    'fetching the package': ('Paket wird geholt', 'téléchargement du paquet', 'scaricamento del pacchetto', 'il pachet vegn chargià giu'),
    'checking and unpacking …': ('prüfen und auspacken …', 'vérification et décompression …', 'verifica e decompressione …', 'verifitgar e decumprimer …'),
    'starting …': ('startet …', 'démarrage …', 'avvio …', 'avia …'),
    'stopping …': ('wird beendet …', 'arrêt …', 'chiusura …', 'vegn terminà …'),
    'running on this Pi': ('läuft auf diesem Pi', 'tourne sur ce Pi', 'gira su questo Pi', 'gira sin quest Pi'),
    'connected': ('verbunden', 'connecté', 'collegato', 'collià'),
    'connecting …': ('verbindet …', 'connexion …', 'collegamento …', 'collia …'),
    'without screen (Xvfb, very slow)': ('ohne Bildschirm (Xvfb, sehr langsam)', 'sans écran (Xvfb, très lent)', 'senza schermo (Xvfb, molto lento)',
                                         'senza visur (Xvfb, fitg plaun)'),
    'package ready': ('Paket bereit', 'paquet prêt', 'pacchetto pronto', 'pachet pront'),
    'checked like an update': ('geprüft wie ein Update', 'vérifié comme une mise à jour', 'verificato come un aggiornamento', 'verifitgà sco in update'),
    'fetched at the first start': ('wird beim ersten Start geholt', 'téléchargé au premier démarrage', 'scaricato al primo avvio',
                                   'vegn chargià giu a l’emprim start'),
    'Stop: back to': ('Beenden: zurück zu', 'Arrêter : retour à', 'Termina: ritorno a', 'Terminar: enavos tar'),
    'simulation on': ('Simulation ein', 'simulation active', 'simulazione attiva', 'simulaziun activa'),
    'simulation off': ('Simulation aus', 'simulation désactivée', 'simulazione spenta', 'simulaziun deactivada'),
    'the connection before': ('der Verbindung von vorher', 'la connexion d’avant', 'il collegamento di prima', 'la colliaziun da pli baud'),
    'MoveEye is armed - the simulation replaces the real camera while it runs.': (
        'MoveEye ist scharf – die Simulation ersetzt die echte Kamera, solange sie läuft.',
        'MoveEye est armé – la simulation remplace la vraie caméra tant qu’elle tourne.',
        'MoveEye è armato – la simulazione sostituisce la vera telecamera finché gira.',
        'MoveEye è armà – la simulaziun remplazza la vaira camera uschè ditg ch’ella gira.'),
    'not for this Pi - use «Simulator intern»': ('nicht für diesen Pi – «Simulator intern» nehmen', 'pas pour ce Pi – utiliser « Simulateur interne »',
                                                 'non per questo Pi – usare «Simulatore interno»', 'betg per quest Pi – utilisar «Simulatur intern»'),
    'little free memory': ('wenig Speicher frei', 'peu de mémoire libre', 'poca memoria libera', 'pauca memoria libra'),
    'the Pi is warm': ('der Pi ist warm', 'le Pi est chaud', 'il Pi è caldo', 'il Pi è chaud'),
    'the Pi is busy': ('der Pi ist ausgelastet', 'le Pi est très occupé', 'il Pi è molto occupato', 'il Pi è fitg occupà'),
    'only on a Raspberry Pi 5 with a 64-bit system (arm64)': ('nur auf einem Raspberry Pi 5 mit 64-Bit-System (arm64)',
                                                              'seulement sur un Raspberry Pi 5 avec un système 64 bits (arm64)',
                                                              'solo su un Raspberry Pi 5 con sistema a 64 bit (arm64)',
                                                              'mo sin in Raspberry Pi 5 cun sistem da 64 bits (arm64)'),
    'no signed package known yet': (
        'noch kein signiertes Simulator-Paket für den Pi – es kommt mit einem der nächsten Simulator-Releases',
        'pas encore de paquet simulateur signé pour le Pi – il viendra avec une prochaine version du simulateur',
        'ancora nessun pacchetto del simulatore firmato per il Pi – arriverà con una delle prossime versioni del simulatore',
        'anc nagin pachet dal simulatur suttascrit per il Pi – el vegn cun ina da las proximas versiuns dal simulatur'),
    'the simulator was closed - back to the connection before': ('der Simulator wurde geschlossen – zurück zur Verbindung von vorher',
                                                                 'le simulateur a été fermé – retour à la connexion d’avant',
                                                                 'il simulatore è stato chiuso – ritorno al collegamento di prima',
                                                                 'il simulatur è vegnì serrà – enavos tar la colliaziun da pli baud'),
    'the package is damaged - it is fetched again at the next start': ('das Paket ist beschädigt – es wird beim nächsten Start neu geholt',
                                                                       'le paquet est endommagé – il sera retéléchargé au prochain démarrage',
                                                                       'il pacchetto è danneggiato – sarà riscaricato al prossimo avvio',
                                                                       'il pachet è donnegià – el vegn chargià giu da nov al proxim start'),
    'no user at the desktop of the Pi found (the simulator never runs as root)': (
        'kein Benutzer am Desktop des Pi gefunden (der Simulator läuft nie als root)',
        'aucun utilisateur trouvé sur le bureau du Pi (le simulateur ne tourne jamais en root)',
        'nessun utente trovato sul desktop del Pi (il simulatore non gira mai come root)',
        'nagin utilisader chattà sin il desktop dal Pi (il simulatur na gira mai sco root)'),
    'no desktop on the Pi - Raspberry Pi OS with desktop needed (or: sudo apt install xvfb, very slow)': (
        'kein Desktop auf dem Pi – Raspberry Pi OS mit Desktop nötig (oder: sudo apt install xvfb, sehr langsam)',
        'pas de bureau sur le Pi – Raspberry Pi OS avec bureau nécessaire (ou : sudo apt install xvfb, très lent)',
        'nessun desktop sul Pi – serve Raspberry Pi OS con desktop (oppure: sudo apt install xvfb, molto lento)',
        'nagin desktop sin il Pi – Raspberry Pi OS cun desktop necessari (u: sudo apt install xvfb, fitg plaun)'),
    'the simulator ports 8765 / 8775 / 8785 are all busy on the Pi': ('die Simulator-Ports 8765 / 8775 / 8785 sind auf dem Pi alle belegt',
                                                                      'les ports du simulateur 8765 / 8775 / 8785 sont tous occupés sur le Pi',
                                                                      'le porte del simulatore 8765 / 8775 / 8785 sono tutte occupate sul Pi',
                                                                      'ils ports dal simulatur 8765 / 8775 / 8785 èn tuts occupads sin il Pi'),
    'window closed or crashed': ('Fenster geschlossen oder abgestürzt', 'fenêtre fermée ou plantage', 'finestra chiusa o arresto anomalo',
                                 'fanestra serrada u collaps'),
    'could not be fetched': ('konnte nicht geholt werden', 'n’a pas pu être téléchargé', 'non è stato possibile scaricarlo', 'na pudeva betg vegnir chargià giu'),
}
# Hindernisse mit Zahl (simpi_check): Übersetzung des Anfangs, die Zahl bleibt
_SIMPI_PATTERNS = {
    "too little free memory (%d MB) - close other programs first": ('zu wenig Speicher frei (%d MB) – zuerst andere Programme schliessen',
                                                                    'trop peu de mémoire libre (%d Mo) – fermer d’abord d’autres programmes',
                                                                    'troppo poca memoria libera (%d MB) – chiudere prima altri programmi',
                                                                    'memia pauca memoria libra (%d MB) – serrar l’emprim auters programs'),
    "the Pi is too hot (%.0f °C) - let it cool down first": ('der Pi ist zu heiss (%.0f °C) – zuerst abkühlen lassen',
                                                            'le Pi est trop chaud (%.0f °C) – le laisser refroidir d’abord',
                                                            'il Pi è troppo caldo (%.0f °C) – lasciarlo prima raffreddare',
                                                            'il Pi è memia chaud (%.0f °C) – l’emprim laschar sfradentar'),
    "too hot (%.0f °C)": ('zu heiss (%.0f °C)', 'trop chaud (%.0f °C)', 'troppo caldo (%.0f °C)', 'memia chaud (%.0f °C)'),
    "too little free memory (%d MB)": ('zu wenig Speicher frei (%d MB)', 'trop peu de mémoire libre (%d Mo)', 'troppo poca memoria libera (%d MB)',
                                       'memia pauca memoria libra (%d MB)'),
    "too little room on the memory card (%d MB free)": ('zu wenig Platz auf der Speicherkarte (%d MB frei)',
                                                        'trop peu de place sur la carte mémoire (%d Mo libres)',
                                                        'troppo poco spazio sulla scheda di memoria (%d MB liberi)',
                                                        'memia pauc plaz sin la carta da memoria (%d MB libers)'),
}
for _k, _v in _HX_SIMPI.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])


def simpi_tr_num(msg, lang=None):
    """«zu wenig Speicher frei (612 MB) …» in der gewählten Sprache"""
    L = norm_lang(lang or CFG.get("lang"))
    for en, tx in _SIMPI_PATTERNS.items():
        rx = "^" + re.escape(en).replace(re.escape("%d"), r"(\d+)").replace(re.escape("%.0f"), r"(\d+)") + "$"
        m = re.match(rx, str(msg))
        if m:
            if L == "en":
                return msg
            i = {"de": 0, "fr": 1, "it": 2, "rm": 3}.get(L, 0)
            return tx[i].replace("%d", m.group(1)).replace("%.0f", m.group(1))
    return None


_tr_err_simpi_base = tr_err


def tr_err(msg, lang=None):                                # + 639zx: Hindernisse von «Simulator intern» mit Zahl
    x = simpi_tr_num(msg, lang) if isinstance(msg, str) and ("MB" in msg or "°C" in msg) else None
    return x if x is not None else _tr_err_simpi_base(msg, lang)


# Seite Simulator: Unterabschnitt in «Verbindung» (vor «Simulator hinter einer Firewall»), Skript am Ende
_SIMPI_ANKER = '<details class="sub" id="c-tunnel">'
if _SIMPI_ANKER in SIM_PAGE:
    SIM_PAGE = SIM_PAGE.replace(_SIMPI_ANKER, SIMPI_HTML + _SIMPI_ANKER, 1)
    SIM_PAGE = SIM_PAGE.replace("</body>", SIMPI_JS.replace("/*SIDE*/{}", json.dumps({k: v[0] for k, v in _HX_SIMPI.items()},
                                                                                      ensure_ascii=False).replace("</", "<\\/")) + "</body>", 1)

# Anleitung: ein Punkt im Kapitel «Sim-Ansicht und Spielen» (639zt), alle Sprachen
_HELP_SIMPI = {
    "de": '<li><b>🧪 Simulator intern (ab MoveEye 3.59.0):</b> unterwegs ohne HP oder PC läuft MoveEye Sim abgespeckt direkt auf dem Pi 5 '
          '(Reiter Simulator → Verbindung → «Simulator intern (auf diesem Pi) ausprobieren»). Langsamer, nur zum Vorführen und '
          'Ausprobieren. Das Paket wird beim ersten Mal geholt und wie ein Update geprüft; «Beenden» stellt die Verbindung von vorher '
          'wieder her. Braucht Raspberry Pi OS mit Desktop; ist der Pi zu heiss oder der Speicher knapp, beendet MoveEye den Simulator selbst.</li>',
    "en": '<li><b>🧪 Simulator intern (from MoveEye 3.59.0):</b> on the go without the HP or a PC, MoveEye Sim runs slimmed down right on the Pi 5 '
          '(tab Simulator → Connection → «Try the simulator intern (on this Pi)»). Slower, only for showing and trying out. The package '
          'is fetched the first time and checked like an update; «Stop» brings back the connection before. Needs Raspberry Pi OS with '
          'desktop; when the Pi gets too hot or the memory runs short, MoveEye stops the simulator itself.</li>',
    "fr": '<li><b>🧪 Simulateur interne (dès MoveEye 3.59.0) :</b> en déplacement sans HP ni PC, MoveEye Sim tourne en version allégée directement '
          'sur le Pi 5 (onglet Simulateur → Connexion). Plus lent, seulement pour montrer et essayer. Le paquet est téléchargé la première '
          'fois et vérifié comme une mise à jour ; « Arrêter » rétablit la connexion d’avant.</li>',
    "it": '<li><b>🧪 Simulatore interno (da MoveEye 3.59.0):</b> in viaggio senza HP né PC, MoveEye Sim gira in versione ridotta direttamente sul '
          'Pi 5 (scheda Simulatore → Collegamento). Più lento, solo per mostrare e provare. Il pacchetto viene scaricato la prima volta e '
          'verificato come un aggiornamento; «Termina» ripristina il collegamento di prima.</li>',
    "rm": '<li><b>🧪 Simulatur intern (a partir da MoveEye 3.59.0):</b> en viadi senza HP u PC gira MoveEye Sim en versiun reducida directamain sin '
          'il Pi 5 (register Simulatur → Colliaziun). Pli plaun, mo per preschentar ed empruvar. Il pachet vegn chargià giu l’emprima giada '
          'e verifitgà sco in update; «Terminar» restabilescha la colliaziun da pli baud.</li>',
}


def _help_simpi(doc, lang):
    i = doc.find('<section id="simview"')
    if i < 0 or "Simulator intern" in doc[i:i + 6000] or "interne (dès" in doc[i:i + 6000]:
        return doc
    j = doc.find("</ul></section>", i)
    return doc[:j] + _HELP_SIMPI[lang] + doc[j:] if j > 0 else doc


_hp_en_simpi = HELP_PAGE.find('<div lang="en">')
if _hp_en_simpi > 0:
    HELP_PAGE = _help_simpi(HELP_PAGE[:_hp_en_simpi], "de") + _help_simpi(HELP_PAGE[_hp_en_simpi:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_simpi(HELP_X[_L], _L)


def simpi_selftest():
    assert 'id="c-intern"' in SIM_PAGE and "/api/simintern" in SIM_PAGE, "page Simulator: «Simulator intern»"
    assert SIM3D_PI["file"] == "simulator3d/MoveEyeSim3D_Pi.zip" and SIM3D_PI["stem"] == "MoveEyeSim3D_Pi", "SIM3D_PI (300)"
    assert not SIM3D_PI["sha256"] or re.fullmatch(r"[0-9a-f]{64}", SIM3D_PI["sha256"]), "SIM3D_PI sha256"
    c = simpi_cmd("/x/MoveEyeSim3D.arm64", 8775)
    assert "--no-update" in c and c[c.index("--port") + 1] == "8775" and "--grafik" in c and c.index("--") > c.index("/x/MoveEyeSim3D.arm64"), "command"
    for k in _HX_SIMPI:
        assert all(_HX_SIMPI[k]), "translation " + k
    assert tr_err("too little free memory (612 MB) - close other programs first", "de").startswith("zu wenig Speicher frei (612 MB)"), "tr_err"
    return "Simulator intern: page, package, command, translations"


SELFTEST_EXTRA.append(("Simulator intern on the Pi (639zx)", simpi_selftest))
