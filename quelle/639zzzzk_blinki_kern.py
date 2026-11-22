#@ MoveEye – Teil 639zzzzk: «Blinki fragen» – Kern: Sprachmodell auf dem Gerät (llama.cpp «llama-server» als eigener Prozess), Modell laden mit fester Prüfsumme, Motor einrichten, Pause bei Alarm / Bewegung / Hitze, Fragen der Reihe nach. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (15.11.2026, Stufe 1 freigegeben): «Blinki fragen» – Blinki beantwortet Fragen zur Bedienung (aus der
# Anleitung, Teil 639zzzzk_blinki_wissen) und erklärt Fehler (Protokoll + Selbstdiagnose). Alles offline auf dem Pi; Cloud folgt in Stufe 2.
#  Modell     BLINKI_MODELS: Qwen2.5-1.5B-Instruct, GGUF Q4_0 (Apache-2.0, Modellseite geprüft 15.11.2026), von Hugging Face mit
#             fester Revision, fester Grösse und fester SHA-256 (aus dem LFS-Zeiger der Datei) - wie die Piper-Stimmen (639zzb):
#             die Signatur der Hauptdatei bürgt für das Modell. Laden nur auf Knopfdruck, mit Fortsetzen (piper_fetch), nie im
#             Repository. Stimmt Grösse oder Prüfsumme nicht, wird die Datei verworfen.
#  Motor      llama.cpp «llama-server» (MIT): zuerst ein vorhandenes (PATH), sonst eines in DATA_DIR/blinki/bin. «Motor einrichten»
#             baut es einmal aus dem Quelltext einer FESTEN Fassung (Tag + Commit geprüft, BLINKI_LLAMA): apt git / cmake /
#             build-essential (wie 639zzb mit sudo -n), git clone --depth 1, cmake (statisch, ohne Web-Oberfläche, ohne Netz-
#             Funktionen; die Optionen wurden im Quelltext von b12000 nachgesehen und hier probehalber gebaut), nice 19, 2 Kerne. Fertige Pakete von GitHub sind für Ubuntu 24.04 gebaut (glibc 2.39) und laufen auf
#             Raspberry Pi OS Bookworm nicht - darum der Bau. Dauer auf dem Pi 5 geschätzt 15-30 min (nicht gemessen).
#  Prozess    eigener Prozess (wie Piper): nur 127.0.0.1, freier Port, -t 2 (Antworten schreiben ist durch die Speicher-Bandbreite
#             begrenzt, 2 Kerne sind am schnellsten), nice 15, auf die letzten 2 Kerne gelegt (die Erkennung behält die ersten),
#             PR_SET_PDEATHSIG (stirbt MoveEye, geht er mit) - darum startet ihn immer derselbe Faden «blinki-mgr».
#             Nach BLINKI_IDLE_S ohne Frage beendet er sich (RAM frei).
#  Vorrang    Der Schutz geht immer vor: bei Alarm (LED 163a / Sirene), verfolgter Bewegung (Kopf folgt, Person, Wärme) oder CPU über
#             80 °C hält «blinki-mgr» den Prozess an (SIGSTOP) und lässt ihn erst weiterlaufen (SIGCONT), wenn 3 s lang alles ruhig
#             ist (Hitze: unter 75 °C). Die Antwort wartet so lange (die Seite sagt warum).
#  Fragen     eine nach der anderen (BLINKI_JOBS), Text kommt Stück für Stück (OpenAI-kompatibles /v1/chat/completions mit
#             «stream»), die Seite holt ihn alle 0.4 s ab. Höchstens BLINKI_MAX_TOKENS Wörter-Stücke, Zeitlimit.
# Test: werkzeuge/ki_test.py (Ersatz-llama-server, lokaler Ersatz für Hugging Face, nie das echte Internet).
# ----------------------------------------------------------------------------
# Der Programmtext dieses Teils steht in EINEM Literal (Besitzer / Koordinator 15.11.2026: Hauptdatei klein): werkzeuge/bauen.py
# legt es in die Zusatz-ZIP, beim Start läuft es hier an seinem Platz (zd_exec, Teil 639zzzzk_blinki_kern). Ohne ZIP gibt es
# «Blinki fragen» nicht - es gehört nicht zu Start, Schutz oder Alarm. Die ZIP ist über ZD_SHA256 (Teil 012) mit signiert.

# wraps: zd_exec
def zd_exec(src, name):
    """run the program text of a part that bauen.py moved into the data zip (639zzzzk «Blinki fragen»): src comes from _zd
    (Teil 012), i.e. only from a zip whose SHA-256 matched ZD_SHA256 of this signed program - no own loader. Real file name
    for compile + linecache: tracebacks and the log show the lines of the part. Only for functions that do not belong to
    start, protection, alarm, update or repair (without the zip they are simply missing)."""
    if not src:
        return False
    import linecache
    linecache.cache[name] = (len(src), None, src.splitlines(True), name)
    exec(compile(src, name, "exec"), globals())
    return True


BLINKI_KERN_PY = r'''import signal as _bsig
import http.client as _bhttp

BLINKI_HF = {"url": "https://huggingface.co/"}           # tests put a local server here
BLINKI_MODELS = {
    "qwen2.5-1.5b-q4_0": {
        "name": "Qwen 2.5 · 1.5B · Q4_0", "repo": "Qwen/Qwen2.5-1.5B-Instruct-GGUF", "rev": "dd26da440ef0330c47919d1ecae0966d24022222",
        "file": "qwen2.5-1.5b-instruct-q4_0.gguf", "size": 1066227232,
        "sha256": "dcd819ff094852c38faba6873d8ff0c9d51eadb2844539e52042ae5d647bbfdb",
        "licence": "Apache-2.0 (Qwen, huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF)", "ram_mb": 1500, "ctx": 4096},
}
BLINKI_MODEL_DEFAULT = "qwen2.5-1.5b-q4_0"
BLINKI_LLAMA = {"repo": "https://github.com/ggml-org/llama.cpp", "tag": "b12000", "commit": "68d20b884c3878217de79eade0a249efde96ab38"}
BLINKI_CMAKE = ("-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DGGML_NATIVE=ON", "-DLLAMA_BUILD_TESTS=OFF",
                "-DLLAMA_BUILD_EXAMPLES=OFF", "-DLLAMA_BUILD_APP=OFF", "-DLLAMA_BUILD_SERVER=ON", "-DLLAMA_BUILD_UI=OFF",
                "-DLLAMA_USE_PREBUILT_UI=OFF", "-DLLAMA_OPENSSL=OFF", "-DLLAMA_CONNECT=OFF")   # options checked in the source of b12000
BLINKI_APT = ("git", "cmake", "build-essential")
BLINKI_IDLE_S = 15 * 60
BLINKI_MAX_TOKENS = 380
BLINKI_JOB_S = 300.0                    # one answer at most (paused time does not count)
BLINKI_HOT_C, BLINKI_COOL_C = 80.0, 75.0
BLINKI_CALM_S = 3.0
_BLINKI_ID = re.compile(r"^[0-9a-f]{12}$")

for _k, _v in {"blinki_model": BLINKI_MODEL_DEFAULT, "blinki_threads": 2, "blinki_speak": False}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v)
    if "FACTORY_CFG" in globals():
        FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update({"blinki_model", "blinki_threads"})

BLINKI = {"lock": threading.Lock(), "proc": None, "port": 0, "model": "", "state": "off", "err": "", "held": "", "stopped": False,
          "calm_t": 0.0, "last": 0.0, "mgr": None, "want": False, "install": "", "step": "", "pct": 0, "jobs": {}, "order": [],
          "queue": None, "worker": None}
BLINKI_DL = {"model": "", "running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": ""}


def blinki_dir():
    return os.path.join(DATA_DIR, "blinki")


def blinki_model_path(mid):
    m = BLINKI_MODELS.get(mid)
    return os.path.join(blinki_dir(), m["file"]) if m else ""


def blinki_model_url(mid):
    m = BLINKI_MODELS[mid]
    return BLINKI_HF["url"] + m["repo"] + "/resolve/" + m["rev"] + "/" + m["file"] + "?download=true"


def blinki_pinned(mid):
    m = BLINKI_MODELS.get(mid) or {}
    return bool(m.get("size")) and bool(re.fullmatch(r"[0-9a-f]{64}", str(m.get("sha256") or ""))) and bool(re.fullmatch(r"[0-9a-f]{40}", str(m.get("rev") or "")))


def blinki_model_ok(mid=None):
    """the model is there with the pinned size and was checked once at the download (marker <file>.ok holds the sha256)"""
    mid = mid or CFG.get("blinki_model") or BLINKI_MODEL_DEFAULT
    m = BLINKI_MODELS.get(mid)
    if not m or not blinki_pinned(mid):
        return False
    p = blinki_model_path(mid)
    try:
        if os.path.getsize(p) != m["size"]:
            return False
        with open(p + ".ok", encoding="utf-8") as f:
            return f.read().strip() == m["sha256"]
    except OSError:
        return False


def blinki_download(mid=None, wait=False):
    """«Load the model» in the background; (ok, english reason)"""
    mid = mid or CFG.get("blinki_model") or BLINKI_MODEL_DEFAULT
    if mid not in BLINKI_MODELS:
        return False, "unknown model"
    if not blinki_pinned(mid):
        return False, "This model is not pinned yet (comes with an update)"
    if blinki_model_ok(mid):
        return True, ""
    if BLINKI_DL["running"]:
        return False, "already running"
    m = BLINKI_MODELS[mid]
    try:
        os.makedirs(blinki_dir(), exist_ok=True)
        free = shutil.disk_usage(blinki_dir()).free
    except OSError:
        free = 1 << 40
    part = blinki_model_path(mid) + ".part"
    have = os.path.getsize(part) if os.path.isfile(part) else 0
    if free + have < m["size"] + 500 * 1024 * 1024:
        return False, "not enough free space on the memory card"
    BLINKI_DL.update(model=mid, running=True, got=0, total=m["size"], msg="", stop=False, done="")

    def work():
        try:
            dest = blinki_model_path(mid)
            try:
                os.remove(dest + ".ok")
            except OSError:
                pass
            piper_fetch(blinki_model_url(mid), dest, {"size": m["size"], "sha256": m["sha256"]}, BLINKI_DL)
            with open(dest, "rb") as f:
                if f.read(4) != b"GGUF":
                    os.remove(dest)
                    raise ValueError("the file is not a GGUF model")
            with open(dest + ".ok", "w", encoding="utf-8") as f:
                f.write(m["sha256"])
            BLINKI_DL["done"] = mid
            log_event("sys", f"Blinki: model {m['name']} loaded and checked ({m['licence'][:30]})")
        except InterruptedError:
            BLINKI_DL["msg"] = "cancelled"
        except Exception as e:
            try:
                BLINKI_DL["msg"] = (_upd_error(e) if hasattr(e, "code") or hasattr(e, "reason") else str(e))[:160]
            except Exception:
                BLINKI_DL["msg"] = str(e)[:160]
            log_event("sys", "Blinki: model not loaded: " + BLINKI_DL["msg"])
        finally:
            BLINKI_DL["running"] = False
    if wait:
        work()
        return not BLINKI_DL["msg"], BLINKI_DL["msg"]
    threading.Thread(target=work, daemon=True, name="blinki-dl").start()
    return True, ""


def blinki_delete(mid=None):
    mid = mid or CFG.get("blinki_model") or BLINKI_MODEL_DEFAULT
    if mid not in BLINKI_MODELS or (BLINKI_DL["running"] and BLINKI_DL["model"] == mid):
        return False, "unknown model"
    blinki_stop("model deleted")
    p = blinki_model_path(mid)
    for x in (p, p + ".ok", p + ".part"):
        try:
            os.remove(x)
        except OSError:
            pass
    log_event("sys", f"Blinki: model deleted (frees about {BLINKI_MODELS[mid]['size'] // 1048576} MB)")
    return True, ""


# ---- the engine: llama-server --------------------------------------------------------------------------------------------------
def blinki_engine():
    """path of llama-server: MoveEye's own build first, then one of the system; '' = none"""
    own = os.path.join(blinki_dir(), "bin", "llama-server")
    if os.path.isfile(own) and os.access(own, os.X_OK):
        return own
    return shutil.which("llama-server") or ""


def _blinki_apt(pkgs):
    """missing packages with apt (same privilege path as 639zzb: root or sudo -n, never a password) - (ok, english reason)"""
    need = [p for p in pkgs if not (shutil.which("g++") if p == "build-essential" else shutil.which(p))]
    if not need:
        return True, ""
    apt = shutil.which("apt-get")
    if not apt:
        return False, "no apt-get on this system - install by hand: " + " ".join(need)
    pre = [] if (hasattr(os, "geteuid") and os.geteuid() == 0) else ["sudo", "-n"]
    if pre and not shutil.which("sudo"):
        return False, "MoveEye has no rights for apt (no sudo) - in a terminal: sudo apt install " + " ".join(need)
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", APT_LISTCHANGES_FRONTEND="none")
    out, rc = "", 1
    for args in (["install", "-y", "--no-install-recommends"] + need, ["update"], ["install", "-y", "--no-install-recommends"] + need):
        BLINKI["step"] = "apt " + args[0]
        try:
            r = subprocess.run(pre + [apt] + args, capture_output=True, text=True, timeout=1200, env=env, stdin=subprocess.DEVNULL)
            rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
        except (OSError, subprocess.SubprocessError) as e:
            rc, out = -1, str(e)
        if rc == 0 and args[0] == "install":
            return True, ""
        if args[0] == "install" and not re.search(r"Unable to locate package|has no installation candidate|Failed to fetch", out):
            break
    low = out.lower()
    if pre and ("password is required" in low or "a terminal is required" in low or "not in the sudoers" in low):
        return False, "MoveEye has no rights for apt (sudo asks for a password) - in a terminal: sudo apt install " + " ".join(need)
    return False, (out.strip().splitlines() or ["apt failed"])[-1][:140]


def _blinki_run(cmd, cwd=None, timeout=3600, progress=None):
    """one step of the build (nice 19, the output only read for the percent); (rc, last lines)"""
    tail = []
    try:
        p = subprocess.Popen(["nice", "-n", "19"] + cmd if shutil.which("nice") else cmd, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, stdin=subprocess.DEVNULL)
    except OSError as e:
        return -1, str(e)
    t0 = time.time()
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-6:]
        if progress is not None:
            m = re.match(r"\[\s*(\d+)%\]", line)
            if m:
                progress["pct"] = int(m.group(1))
        if time.time() - t0 > timeout:
            p.kill(); break
    rc = p.wait()
    return rc, "\n".join(tail)


# what «set up» builds: name -> (state dict, pinned source, cmake options, target); 639zzzzk_blinki_z_sprache adds whisper.cpp
BLINKI_BUILDS = {"llm": (BLINKI, BLINKI_LLAMA, BLINKI_CMAKE, "llama-server", "llama.cpp")}


def blinki_install(kind="llm"):
    """«Set up the engine»: build the program once from the pinned source (background)"""
    st, spec, opts, target, name = BLINKI_BUILDS[kind]
    if st["install"] == "running" or any(v[0]["install"] == "running" for v in BLINKI_BUILDS.values()):
        return False, "already running"
    if os.access(os.path.join(blinki_dir(), "bin", target), os.X_OK):
        return True, ""
    st.update(install="running", step="", pct=0)

    def work():
        src = os.path.join(blinki_dir(), "src-" + kind)
        try:
            os.makedirs(blinki_dir(), exist_ok=True)
            if shutil.disk_usage(blinki_dir()).free < 1500 * 1024 * 1024:
                raise RuntimeError("not enough free space on the memory card")
            ok, why = _blinki_apt(BLINKI_APT)
            if not ok:
                raise RuntimeError(why)
            shutil.rmtree(src, ignore_errors=True)
            st["step"] = "git clone " + spec["tag"]
            rc, out = _blinki_run(["git", "clone", "--depth", "1", "--branch", spec["tag"], spec["repo"], src], timeout=1800)
            if rc != 0:
                raise RuntimeError("download of the source failed: " + out[-120:])
            head = subprocess.run(["git", "-C", src, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip()
            if head != spec["commit"]:
                raise RuntimeError("the source is not the pinned version - not built")
            st["step"] = "cmake"
            rc, out = _blinki_run(["cmake", "-B", "build"] + list(opts), cwd=src, timeout=900)
            if rc != 0:
                raise RuntimeError("cmake: " + out[-140:])
            st["step"] = "build"
            rc, out = _blinki_run(["cmake", "--build", "build", "--target", target, "-j", "2"], cwd=src, timeout=4 * 3600, progress=st)
            exe = os.path.join(src, "build", "bin", target)
            if rc != 0 or not os.path.isfile(exe):
                raise RuntimeError("build failed: " + out[-140:])
            os.makedirs(os.path.join(blinki_dir(), "bin"), exist_ok=True)
            dst = os.path.join(blinki_dir(), "bin", target)
            shutil.copy2(exe, dst + ".new"); os.chmod(dst + ".new", 0o755); os.replace(dst + ".new", dst)
            st["install"] = "done"
            log_event("sys", f"Blinki: engine {name} {spec['tag']} built")
        except Exception as e:
            st["install"] = "failed: " + str(e)[:160]
            log_event("sys", f"Blinki: engine {name} not built: " + str(e)[:160])
        finally:
            shutil.rmtree(src, ignore_errors=True)            # the source (~ 300 MB with the build) is not needed any more
            st["step"] = ""
    threading.Thread(target=work, daemon=True, name="blinki-install").start()
    return True, ""


def blinki_mem_mb():
    """(total, available) MB from /proc/meminfo; (None, None) elsewhere"""
    try:
        d = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                d[k] = int(v.split()[0]) // 1024
        return d.get("MemTotal"), d.get("MemAvailable")
    except (OSError, ValueError):
        return None, None


def blinki_hold_reason():
    """why the model must wait now ('' = it may compute): the protection always goes first"""
    try:
        if (globals().get("LED") or {}).get("alarm"):
            return "alarm"
        snd = globals().get("SOUND") or {}
        if snd.get("playing") and snd.get("kind") in ("siren", "alarm"):
            return "alarm"
        pres = set(str(x) for x in (STATE.get("present") or []))
        if STATE.get("tracking") or (STATE.get("persons") or 0) > 0 or pres & {"person", "warm"} or (STATE.get("warm") or 0) > 0:
            return "motion"
        t = STATE.get("cpu_temp")
        if t is not None:
            if float(t) >= BLINKI_HOT_C or (BLINKI["held"] == "heat" and float(t) > BLINKI_COOL_C):
                return "heat"
    except Exception:
        pass
    return ""


def _blinki_signal(sig):
    p = BLINKI["proc"]
    if p is not None and p.poll() is None:
        try:
            os.kill(p.pid, sig)
            return True
        except OSError:
            pass
    return False


def _blinki_pre():                                       # the child: low priority, the last cores, dies with MoveEye
    try:
        os.nice(15)
    except OSError:
        pass
    try:
        n = os.cpu_count() or 1
        if n >= 4:
            os.sched_setaffinity(0, set(range(n - 2, n)))
    except (AttributeError, OSError):
        pass
    f = _RADIO_PRCTL[0] if _RADIO_PRCTL else None
    if f is not None:
        try:
            f(1, 9)
        except Exception:
            pass


def _blinki_start_proc():
    """start llama-server (only in the thread «blinki-mgr»); sets BLINKI state / err"""
    mid = CFG.get("blinki_model") or BLINKI_MODEL_DEFAULT
    exe = blinki_engine()
    if not exe:
        BLINKI.update(state="error", err="no engine"); return
    if not blinki_model_ok(mid):
        BLINKI.update(state="error", err="no model"); return
    _tot, avail = blinki_mem_mb()
    if avail is not None and avail < BLINKI_MODELS[mid]["ram_mb"] * 0.8:
        BLINKI.update(state="error", err="not enough free memory (RAM)"); return
    with _bsock_free() as port:
        pass
    _radio_prctl()
    thr = max(1, min(4, int(CFG.get("blinki_threads") or 2)))
    cmd = [exe, "-m", blinki_model_path(mid), "--host", "127.0.0.1", "--port", str(port), "-c", str(BLINKI_MODELS[mid]["ctx"]),
           "-t", str(thr), "-tb", str(thr), "-np", "1", "--no-webui"]
    try:
        logf = open(os.path.join(blinki_dir(), "server.log"), "w")
        p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, preexec_fn=_blinki_pre, close_fds=True)
    except OSError as e:
        BLINKI.update(state="error", err=str(e)[:120]); return
    BLINKI.update(proc=p, port=port, model=mid, state="starting", err="", stopped=False, last=time.time())
    log_event("sys", f"Blinki: engine started ({BLINKI_MODELS[mid]['name']}, {thr} cores)")


class _bsock_free:
    """a free port on 127.0.0.1 (the socket is closed before llama-server binds it)"""
    def __enter__(self):
        import socket as _s
        self.s = _s.socket(); self.s.bind(("127.0.0.1", 0))
        return self.s.getsockname()[1]

    def __exit__(self, *a):
        self.s.close()


def _blinki_health():
    try:
        c = _bhttp.HTTPConnection("127.0.0.1", BLINKI["port"], timeout=2)
        c.request("GET", "/health"); r = c.getresponse(); r.read(); c.close()
        return r.status == 200
    except (OSError, _bhttp.HTTPException):
        return False


def blinki_stop(why=""):
    with BLINKI["lock"]:
        p = BLINKI["proc"]
        BLINKI.update(proc=None, state="off", want=False)
    if p is not None:
        try:
            os.kill(p.pid, _bsig.SIGCONT)
        except OSError:
            pass
        _radio_kill(p)
        if why:
            log_event("sys", "Blinki: engine stopped (" + why + ")")


def _blinki_mgr():
    """the one thread that starts, pauses and ends llama-server"""
    while True:
        try:
            now = time.time()
            why = blinki_hold_reason()
            p = BLINKI["proc"]
            if why:
                BLINKI["calm_t"] = now
                if BLINKI["held"] != why:
                    BLINKI["held"] = why
                if p is not None and not BLINKI["stopped"] and _blinki_signal(_bsig.SIGSTOP):
                    BLINKI["stopped"] = True
            elif BLINKI["held"] and now - BLINKI["calm_t"] >= BLINKI_CALM_S:
                BLINKI["held"] = ""
                if BLINKI["stopped"]:
                    _blinki_signal(_bsig.SIGCONT)
                    BLINKI["stopped"] = False
            if p is not None and p.poll() is not None:
                BLINKI.update(proc=None, state="error", err="the engine stopped (code %s) - see blinki/server.log" % p.returncode)
                p = None
            if BLINKI["want"] and p is None and BLINKI["state"] != "error" and not BLINKI["held"]:
                _blinki_start_proc()
            if BLINKI["proc"] is not None and BLINKI["state"] == "starting" and not BLINKI["stopped"]:
                if _blinki_health():
                    BLINKI["state"] = "ready"
                elif now - BLINKI["last"] > 180:
                    blinki_stop("did not start"); BLINKI.update(state="error", err="the engine did not start in 3 min")
            if BLINKI["proc"] is not None and not _blinki_busy() and now - BLINKI["last"] > BLINKI_IDLE_S:
                blinki_stop("not used for %d min" % (BLINKI_IDLE_S // 60))
        except Exception as e:
            BLINKI["err"] = str(e)[:120]
        time.sleep(0.5)


def blinki_ensure():
    """the manager thread runs; the engine is wanted (starts when model + engine are there)"""
    with BLINKI["lock"]:
        if BLINKI["mgr"] is None or not BLINKI["mgr"].is_alive():
            BLINKI["mgr"] = threading.Thread(target=_blinki_mgr, daemon=True, name="blinki-mgr")
            BLINKI["mgr"].start()
        if BLINKI["state"] == "error":
            BLINKI.update(state="off", err="")
        BLINKI["want"] = True
        BLINKI["last"] = time.time()


def _blinki_busy():
    return any(j["state"] in ("wait", "think", "write") for j in BLINKI["jobs"].values())


# ---- questions: one after the other --------------------------------------------------------------------------------------------
def blinki_job_new(mode, q, lang, messages, extra=None):
    import queue as _q
    jid = os.urandom(6).hex()
    j = {"id": jid, "t": time.time(), "mode": mode, "q": q, "lang": lang, "messages": messages, "text": "", "state": "wait",
         "err": "", "stop": False, "t_first": None, "t_end": None, "n_tok": 0}
    j.update(extra or {})
    with BLINKI["lock"]:
        BLINKI["jobs"][jid] = j; BLINKI["order"].append(jid)
        while len(BLINKI["order"]) > 30:
            BLINKI["jobs"].pop(BLINKI["order"].pop(0), None)
        if BLINKI["queue"] is None:
            BLINKI["queue"] = _q.Queue()
        if BLINKI["worker"] is None or not BLINKI["worker"].is_alive():
            BLINKI["worker"] = threading.Thread(target=_blinki_worker, daemon=True, name="blinki-ask")
            BLINKI["worker"].start()
    BLINKI["queue"].put(jid)
    return j


def _blinki_worker():
    while True:
        jid = BLINKI["queue"].get()
        j = BLINKI["jobs"].get(jid)
        if j is None:
            continue
        if j["stop"]:                                      # stopped while waiting: never «busy» again
            j.update(state="stopped", t_end=time.time()); continue
        try:
            blinki_answer(j)
        except Exception as e:
            j.update(state="error", err=str(e)[:160])
        if j["state"] not in ("error", "stopped"):
            j["state"] = "done"
        j["t_end"] = time.time()
        BLINKI["last"] = time.time()


def blinki_answer(j):
    """run one question against the engine of the job (offline; 639zzzzk_blinki_cloud adds the cloud)"""
    blinki_ensure()
    t0 = time.time()
    while BLINKI["state"] != "ready" or BLINKI["held"]:
        if j["stop"]:
            j["state"] = "stopped"; return
        if BLINKI["state"] == "error":
            j.update(state="error", err=BLINKI["err"] or "the engine does not run"); return
        if not BLINKI["held"] and time.time() - t0 > 240:
            j.update(state="error", err="the engine did not start in 3 min"); return
        j["state"] = "wait"
        time.sleep(0.3)
    j["state"] = "think"
    _blinki_stream(j, "127.0.0.1", BLINKI["port"], "/v1/chat/completions", {}, j["messages"])


def _blinki_stream(j, host, port, path, headers, messages, tls=False, body_extra=None):
    """POST a chat with «stream» and append the pieces to j["text"] (OpenAI-compatible server-sent events)"""
    body = {"messages": messages, "stream": True, "max_tokens": int(j.get("max_tokens") or BLINKI_MAX_TOKENS), "temperature": float(j.get("temp") or 0.3),
            "top_p": 0.9, "cache_prompt": True}
    body.update(body_extra or {})
    body = {k: v for k, v in body.items() if v is not None}
    data = json.dumps(body, ensure_ascii=False).encode()
    c = (_bhttp.HTTPSConnection if tls else _bhttp.HTTPConnection)(host, port, timeout=20)
    W = {"busy": 0.0, "end": False, "why": ""}

    def watch():                                          # a paused engine sends nothing: only the time it may compute counts
        t = time.time()
        while not W["end"]:
            time.sleep(0.25)
            now = time.time()
            if not BLINKI["held"] or tls:
                W["busy"] += now - t
            t = now
            if j["stop"] or W["busy"] > BLINKI_JOB_S:
                W["why"] = "stop" if j["stop"] else "time"
                try:
                    c.sock.shutdown(2)
                except (OSError, AttributeError):
                    pass
                return
    try:
        c.request("POST", path, data, dict({"Content-Type": "application/json", "Connection": "close"}, **headers))
        r = c.getresponse()
        if r.status != 200:
            raise RuntimeError("the engine answered %d: %s" % (r.status, r.read(300).decode("utf-8", "replace")[:200]))
        try:
            c.sock.settimeout(None)
        except (OSError, AttributeError):
            pass
        threading.Thread(target=watch, daemon=True, name="blinki-watch").start()
        while True:
            try:
                ch = r.fp.readline()
            except (OSError, ValueError):
                ch = b""
            if not ch:
                break
            line = ch.strip()
            if not line.startswith(b"data:"):
                continue
            d = line[5:].strip()
            if d == b"[DONE]":
                break
            try:
                ev = json.loads(d)
            except ValueError:
                continue
            if isinstance(ev, dict) and ev.get("type") == "message_stop":
                break                                      # Anthropic Messages: the end of the answer
            piece = blinki_piece(ev)
            if piece:
                if j["t_first"] is None:
                    j["t_first"] = time.time()
                j["state"] = "write"
                j["text"] += piece; j["n_tok"] += 1
                BLINKI["last"] = time.time()
        if W["why"] == "stop" or j["stop"]:
            j["state"] = "stopped"
        elif W["why"] == "time":
            raise RuntimeError("no answer in time")
    finally:
        W["end"] = True
        c.close()


def blinki_piece(ev):
    """the text of one stream event: OpenAI («choices[0].delta.content») or Anthropic («delta.text»)"""
    try:
        ch = ev.get("choices")
        if ch:
            return str((ch[0].get("delta") or {}).get("content") or "")
        if ev.get("type") == "content_block_delta":
            return str((ev.get("delta") or {}).get("text") or "")
    except (AttributeError, IndexError, TypeError):
        pass
    return ""


def blinki_job_view(j, start=0):
    """what the page gets for one question (the text from <start> on)"""
    st = j["state"]
    out = {"id": j["id"], "state": st, "text": j["text"][start:], "n": len(j["text"]), "held": BLINKI["held"] if st in ("wait", "think", "write") else "",
           "err": j["err"], "links": j.get("links") or [], "sources": j.get("sources") or [], "fixes": j.get("fixes") or [],
           "secs": round((j["t_end"] or time.time()) - j["t"], 1), "engine": j.get("engine", "offline"), "mode": j.get("mode", ""), "q": j.get("q", "")}
    if st == "wait" and not BLINKI["held"]:
        out["queue"] = sum(1 for k in BLINKI["order"] if BLINKI["jobs"].get(k, {}).get("state") == "wait" and k < j["id"] and BLINKI["jobs"][k]["t"] < j["t"])
    return out


def blinki_state():
    mid = CFG.get("blinki_model") or BLINKI_MODEL_DEFAULT
    m = BLINKI_MODELS.get(mid) or {}
    tot, avail = blinki_mem_mb()
    try:
        free = shutil.disk_usage(DATA_DIR).free // 1048576
    except OSError:
        free = None
    return {"model": {"id": mid, "name": m.get("name", ""), "mb": int(m.get("size", 0) / 1048576), "ok": blinki_model_ok(mid),
                      "pinned": blinki_pinned(mid), "licence": m.get("licence", ""), "ram_mb": m.get("ram_mb")},
            "dl": {k: BLINKI_DL[k] for k in ("running", "got", "total", "msg", "done")},
            "engine": {"ok": bool(blinki_engine()), "own": blinki_engine().startswith(blinki_dir()), "install": BLINKI["install"],
                       "step": BLINKI["step"], "pct": BLINKI["pct"], "tag": BLINKI_LLAMA["tag"]},
            "server": BLINKI["state"], "err": BLINKI["err"], "held": BLINKI["held"], "busy": _blinki_busy(),
            "ram": {"total": tot, "avail": avail}, "disk_free_mb": free, "speak": bool(CFG.get("blinki_speak")),
            "threads": int(CFG.get("blinki_threads") or 2)}
'''
zd_exec(BLINKI_KERN_PY, '639zzzzk_blinki_kern.py')
