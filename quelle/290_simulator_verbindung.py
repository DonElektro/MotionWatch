#@ Motion Watch – Teil 290: Verbindung zum Simulator. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Simulator connection: a separate program (motionwatch_simulator.py, protocol in motionwatch_sim_interface.py) simulates two
#   cameras, a thermal camera, day / night, weather and sensors. One switch: the sources change to the simulator, MoveEye
#   sends what it does (servos, lights, relays, sound, armed) about 10 x per second and takes the world from the answer.
# ----------------------------------------------------------------------------
SIM = {"mover": False, "t": 0.0, "ok": False, "msg": "off", "dark": False, "ambient": 15.0, "pressure": 1013.0, "wind": 0.0, "last_event": 0,
       "seen_event": 0, "info": None, "sent": 0, "since": 0.0, "errs": 0, "rtt": 0.0, "events_n": 0, "th_times": deque(maxlen=30)}


def sim_base():
    u = str(CFG.get("sim_url") or "http://127.0.0.1:8765").strip().rstrip("/")
    return u if re.match(r"^https?://[A-Za-z0-9.\-\[\]:]{1,120}$", u) else "http://127.0.0.1:8765"


_SIM_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # the simulator is in the own network: never via a proxy


def _sim_get(path, timeout=2.0):
    with _SIM_OPENER.open(urllib.request.Request(sim_base() + path, headers={"User-Agent": "MotionWatch"}), timeout=timeout) as r:
        return r.read(), r.headers


class SimThermalSource:
    """The thermal camera of the simulator: temperatures in °C (like the Waveshare Thermal-90)."""
    def __init__(self):
        self.size = None; self.t = 0.0

    def ok(self):
        r = self.read()
        return r[0]

    def read(self):
        try:                                             # 557: the model of the simulator (Thermal-90: 15 fps like the driver, 080)
            fps_ = max(2.0, min(25.0, float(((SIM.get("info") or {}).get("thermal") or {}).get("fps") or 8.0)))
        except (TypeError, ValueError):
            fps_ = 8.0
        wait = (1.0 / sim_cam_fps(1) if sim_eco_now() else 1.0 / fps_ - 0.005) - (time.time() - self.t)
        if wait > 0:
            time.sleep(wait)
        self.t = time.time()
        try:
            data, hd = _sim_get("/thermal.bin", 2.0)
            a = np.frombuffer(data, dtype="<f4").reshape(int(hd["X-Height"]), int(hd["X-Width"])).copy()
            self.size = (a.shape[1], a.shape[0]); SIM["th_times"].append(time.time())
            return True, a
        except Exception:
            return False, None

    def set_fps(self, fps):
        pass

    def release(self):
        pass


def cam_fov():
    """2.98.1: field of view (horizontal, vertical in degrees) of the main camera - known in the simulation (/info),
    otherwise the Camera Module 3 (66° x 41°) or what is set"""
    try:
        if CFG.get("sim_on") and str(CFG["source"]).startswith("sim:"):
            info = SIM.get("info") or {}
            cam = next((c for c in info.get("cameras") or [] if str(c.get("id")) == str(CFG["source"])[4:]), None)
            if cam and cam.get("fov_h"):
                hf = float(cam["fov_h"])
                vf = math.degrees(2 * math.atan(math.tan(math.radians(hf) / 2) * float(cam.get("h") or 9) / float(cam.get("w") or 16)))
                return hf, vf
    except (TypeError, ValueError, KeyError):
        pass
    try:
        return cam_fov_hv(None)[:2]                      # 2.98.30: the field of view per camera (318: model, own value, picamera2)
    except NameError:
        return float(CFG.get("cam_hfov") or 66.0), float(CFG.get("cam_vfov") or 41.0)


def servo_half(axis):
    """half the turning range of a servo in degrees: 0 … 100 % = -half … +half (the pan servo may turn 270° or 360°)"""
    try:
        r = float(CFG.get("pan_servo_range") or CFG["servo_range"]) if axis == "pan" else float(CFG["servo_range"])
    except (TypeError, ValueError):
        r = 180.0
    return max(10.0, min(360.0, r)) / 2.0


def _sim_refscan_info():
    try:
        st = refscan_state()
        r = st["reports"][0] if st["reports"] else None
        return {"busy": st["busy"], "step": st["step"], "n": st["n"], "ref": bool(st["ref"]), "ref_n": (st["ref"] or {}).get("n", 0),
                "last": {"missing": r["missing"], "new": r["new"], "changed": r["changed"], "t": r["t"], "gone": r.get("gone") or []} if r else None,
                "night_ref": bool((st.get("refs") or {}).get("night")),
                "cmd_seen": int(SIM.get("cmd_seen") or 0)}
    except Exception:
        return None


def _simtask_now():
    try:
        return simtask_local()
    except NameError:
        return ""


def sim_state():
    hp, ht = servo_half("pan"), servo_half("tilt")
    pl, tl = min(float(CFG["pan_limit"]), hp), min(float(CFG["tilt_limit"]), ht)
    L = STATE.get("lights") or {}
    rs = STATE.get("relay_states") or []
    return {"v": 1, "t": time.time(), "device": CFG["device_name"] or "MoveEye", "armed": is_armed(),
            "uid": f"{device_uid()}:{CFG.get('web_port')}", "helper": bool(STATE.get("helper_arg")), "picture_mode": CFG["picture_mode"],   # 2.98.29: uid/helper - one MoveEye leads the simulator (3D-4.9)
            "mw_version": APP_VERSION, "ai_status": str(STATE.get("ai_status") or ""),     # 2.95.67: for the test bench in the simulator
            "refscan": _sim_refscan_info(),                                                  # 2.95.97: the reference scan, for the button there
            # 2.98.35: the REAL position of the motion planner (072, ramps) + its speed (the simulator goes on with it between
            # two packets) and the goal (it never goes past it)
            "servo": {"pan": round((sp_ := servo_pos())[0], 2), "tilt": round(sp_[1], 2), "pan_deg": round((sp_[0] - 50) / 50 * hp, 2),
                      "tilt_deg": round((sp_[1] - 50) / 50 * ht, 2), "pan_limit": pl, "tilt_limit": tl,
                      "pan_dps": round((sv_ := servo_speed_deg())[0], 1), "tilt_dps": round(sv_[1], 1),
                      "pan_goal": round((CFG["pan"] - 50) / 50 * hp, 2), "tilt_goal": round((CFG["tilt"] - 50) / 50 * ht, 2),
                      "estop": bool(servo_blocked()),
                      "pan_range": round(2 * hp, 1),             # the whole turning range of the pan servo (2.95.24, for the Python simulator)
                      "moving": bool(SRV["moving"]) or time.time() - SERVO_MOVE["t"] < 0.5,
                      # 2.98.1: «Folgen» on, and following something right now - the simulator lets the head follow then (not the patrol)
                      "track": bool(CFG["track_person"] or CFG["track_motion"]), "tracking": bool(STATE.get("tracking")),
                      "track_what": str(STATE.get("track_what") or "")},
            "lights": {"white": bool(L.get("white")), "ir": bool(L.get("ir")), "white_level": 1.0, "ir_level": 1.0},
            "wake": {"state": WAKE["state"], "snoozes": WAKE["snoozes"], "t0": round(WAKE["t0"], 2)},       # 2.98.9: the sleeper in the bedroom scene reacts
            "relays": [{"name": r["name"], "on": bool(rs[i]) if i < len(rs) else False} for i, r in enumerate(RELAYS)],
            "sound": (CFG["siren_sound"] or "siren") if SOUND["playing"] else ("talk" if TALK["proc"] is not None else ""),
            "simtask": (stk_ := _simtask_now()), "simtask_de": tr(stk_, "de") if stk_ else "",   # 2.98.13: one lock (147)
            "eco": STATE.get("eco") or "off",     # power saving of MoveEye: «saving» = quiet - the simulator may calculate slower (3D-3.30)
            # automatic update: the simulator compares these checksums with its own files and fetches /sim/simulator.zip
            "sim_files": sim_files(), "mw_scheme": "https" if WEB_OPTS.get("https") else "http", "mw_port": int(CFG["web_port"]),
            # CPU in % of the whole computer: total, MoveEye, simulator (None = not on this computer / unknown)
            "cpu": {"total": STATE.get("cpu"), "mw": STATE.get("cpu_mw"), "sim": STATE.get("cpu_sim")},
            # what MoveEye detects right now: the simulator compares it with the truth (test run, game «MoveEye decides»)
            "real_look": real_look(),               # 2.98.6: the look of the real pictures (146_echt_abgleich.py, realism.gd 3D-3.94)
            "det": {"persons": int(STATE.get("persons") or 0), "present": list(STATE.get("present") or []), "armed": is_armed(),
                    "boxes": list(STATE.get("person_boxes") or []) if STATE.get("persons") else [],   # 2.95.75: 0..1 of the head camera
                    "sure": list(STATE.get("person_sure") or []) if STATE.get("persons") else [],     # KI-Hilfe: confirmed by the AI (542)
                    "noise": bool(AUDIO is not None and AUDIO.noisy()),
                    "pushes": msglog_recent(4)},             # after 2.98.17: the test bench counts real pushes (068)
            # the tracks of the mover: -1 … 1 each (from 2.94.0)
            "drive": {"l": MOVER["l"], "r": MOVER["r"]},
            # 2.96.5 (makeover 9 / 10): the twin - zones (0..1 of the picture), patrol points (degrees), the place
            "zones": [{"name": z.get("name", ""), "mode": z.get("mode", "ignore"), "points": z.get("points", [])} for z in ZONES[:12]],
            "waypoints": [[round((float(w[0]) - 50) / 50 * hp, 1), round((float(w[1]) - 50) / 50 * ht, 1)] for w in WAYPOINTS[:12]
                          if isinstance(w, (list, tuple)) and len(w) >= 2]}


_SIMFILES = {}


VIEWERS = {}                       # web page / guest page -> time of its last poll; the Pi screen counts as one more


def viewers_now():
    """How many watch right now: every browser (main page or guest link) that asked in the last 8 s, plus the open
    window on the Pi screen."""
    now = time.time()
    for k in [k for k, t in VIEWERS.items() if now - t > 30]:
        VIEWERS.pop(k, None)
    web = sum(1 for t in VIEWERS.values() if now - t <= 8)
    local = 1 if now - STATE.get("local_view_t", 0.0) <= 5 else 0
    return {"n": web + local, "web": web, "local": local}


PREVIEW_PAGE = r'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye – Handy / Tablet</title><style>
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--txt:#c9d1d9;--mut:#8b949e;--acc:#388bfd}
html,body{margin:0;height:100%;background:var(--bg);color:var(--txt);font:14px system-ui,-apple-system,"Segoe UI",sans-serif}
.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:10px 12px;background:var(--panel);border-bottom:1px solid var(--line)}
.bar b{margin-right:8px}.bar button{background:#21262d;color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:7px 12px;font:inherit;cursor:pointer}
.bar button.on{background:var(--acc);border-color:var(--acc);color:#fff}.bar .sp{flex:1}.bar .mut{color:var(--mut)}
#stage{position:absolute;top:var(--top,58px);left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;overflow:hidden}
#dev{position:relative;background:#000;border:12px solid #2b2f36;border-radius:42px;box-shadow:0 0 0 2px #444,0 20px 60px rgba(0,0,0,.6);transform-origin:center center}
#dev.tab{border-radius:28px;border-width:18px}
#dev iframe{display:block;border:0;width:100%;height:100%;border-radius:30px;background:#0d1117}
#dev.tab iframe{border-radius:10px}
#notch{position:absolute;background:#000;border-radius:0 0 14px 14px;z-index:2}
</style></head><body>
<div class="bar"><b>📱 MoveEye auf Handy / Tablet</b>
 <button id="b-ph" class="on">📱 Handy</button><button id="b-tb">📲 Tablet</button>
 <button id="b-po" class="on">▯ Hochformat</button><button id="b-la">▭ Querformat</button>
 <button id="b-fs" class="on">⛶ Vollbild</button><button id="b-rl">↻ Neu laden</button>
 <span class="sp"></span><span class="mut" id="info"></span><button id="b-x" data-mw-exit title="Vorschau schliessen">✕ Schliessen</button></div>
<div id="stage"><div id="dev"><div id="notch"></div><iframe id="fr" title="MoveEye"></iframe></div></div>
<script>
const S = {dev: "phone", land: false, fs: true};
try { Object.assign(S, JSON.parse(localStorage.getItem("mwprev") || "{}")); } catch (e) {}
const SIZE = {phone: [390, 844], tablet: [820, 1180]};            // CSS pixels of a usual phone / tablet
const $ = id => document.getElementById(id);
function url() { return "/?preview=1" + (S.fs ? "&vo=1" : ""); }
function fit() {
  let [w, h] = SIZE[S.dev]; if (S.land) [w, h] = [h, w];
  const d = $("dev"), st = $("stage"), b = S.dev === "phone" ? 12 : 18;
  st.style.top = document.querySelector(".bar").offsetHeight + "px";      // 2.95.53: the bar wraps on a phone
  d.style.width = w + "px"; d.style.height = h + "px"; d.classList.toggle("tab", S.dev === "tablet");
  const k = Math.min((st.clientWidth - 40) / (w + 2 * b), (st.clientHeight - 40) / (h + 2 * b), 1.5);
  d.style.transform = "scale(" + k.toFixed(3) + ")";
  const n = $("notch"); n.hidden = S.dev !== "phone";
  if (S.land) { n.style.cssText = "left:0;top:50%;width:26px;height:150px;transform:translateY(-50%);border-radius:0 14px 14px 0"; }
  else { n.style.cssText = "top:0;left:50%;width:150px;height:26px;transform:translateX(-50%)"; }
  $("info").textContent = w + " × " + h + " px · " + Math.round(k * 100) + " %";
  ["b-ph", "b-tb", "b-po", "b-la", "b-fs"].forEach(id => $(id).classList.toggle("on",
    {"b-ph": S.dev === "phone", "b-tb": S.dev === "tablet", "b-po": !S.land, "b-la": S.land, "b-fs": S.fs}[id]));
  try { localStorage.setItem("mwprev", JSON.stringify(S)); } catch (e) {}
}
function load() { $("fr").src = url(); fit(); }
$("b-ph").onclick = () => { S.dev = "phone"; fit(); };
$("b-tb").onclick = () => { S.dev = "tablet"; fit(); };
$("b-po").onclick = () => { S.land = false; fit(); };
$("b-la").onclick = () => { S.land = true; fit(); };
$("b-fs").onclick = () => { S.fs = !S.fs; load(); };
$("b-rl").onclick = load;
$("b-x").onclick = () => { if (history.length > 1 && document.referrer) history.back(); else location.href = "/"; };   // 2.95.53
addEventListener("resize", fit); load();
</script></body></html>'''


def qs_arrange(items, key=lambda q: q["id"]):
    """the quick switches in the order the user chose, without the hidden ones (new switches come at the end)"""
    lay = CFG.get("qs_layout") or {}
    order = [str(x) for x in (lay.get("order") or [])]; hidden = set(str(x) for x in (lay.get("hidden") or []))
    pos = {k: i for i, k in enumerate(order)}
    out = sorted(enumerate(items), key=lambda p: (pos.get(key(p[1]), len(order) + p[0])))
    return [q for _i, q in out if key(q) not in hidden]


def qs_layout_clean(d):
    """2.98.29: the arrangement «for all devices» (Pi default): quick switches order / hidden / favourites (max. 8) and the
    order / hidden cards of the live page. Devices without an own arrangement use it (web 536, window 581)."""
    d = d if isinstance(d, dict) else {}
    ok = lambda x: isinstance(x, str) and re.fullmatch(r"[a-z0-9_]{1,20}", x)
    L = lambda k, n=60: [x for x in (d.get(k) or []) if ok(x)][:n] if isinstance(d.get(k), list) else []
    out = {"order": L("order"), "hidden": L("hidden")}
    for k, n in (("favs", 8), ("cards", 30), ("chide", 30)):
        if isinstance(d.get(k), list):
            out[k] = L(k, n)
    return out


def qs_layout_set(order, hidden, favs=None, cards=None, chide=None):
    d = {"order": order, "hidden": hidden}
    for k, v in (("favs", favs), ("cards", cards), ("chide", chide)):
        if v is not None:
            d[k] = v
    CFG["qs_layout"] = qs_layout_clean(d); save_settings()
    lay = CFG["qs_layout"]
    log_event("web", f"Quick switches arranged for all devices: {len(lay['order']) - len([h for h in lay['hidden'] if h in lay['order']])} shown, "
                     f"{len(lay['hidden'])} hidden" + (f", {len(lay['favs'])} favourites" if "favs" in lay else ""))
    return True


_PROJ = {"t": 0.0, "d": {}, "busy": False}
_START_T = time.time()


def _dir_mb(path, skip=()):
    tot = 0; n = 0
    for root_, dirs, files in os.walk(path):
        dirs[:] = [x for x in dirs if os.path.join(root_, x) not in skip]
        for f in files:
            try:
                tot += os.path.getsize(os.path.join(root_, f)); n += 1
            except OSError:
                pass
    return round(tot / 1024 ** 2, 1), n


def project_info():
    """Size of the program and its data, and what it runs on (refreshed once a minute)."""
    if time.time() - _PROJ["t"] > 60 and not _PROJ.get("busy"):
        _PROJ["busy"] = True; _PROJ["t"] = time.time()
        threading.Thread(target=_project_scan, daemon=True, name="projinfo").start()     # walking folders: not in the request
    d = dict(_PROJ["d"])
    try:
        with open("/proc/self/status") as f:
            d["ram_mb"] = round(int(next(l for l in f if l.startswith("VmRSS:")).split()[1]) / 1024)
    except (OSError, StopIteration, ValueError):
        d["ram_mb"] = None
    d["run_s"] = int(time.time() - _START_T)
    d["version"] = APP_VERSION
    return d


def _project_scan():
    d = {}
    try:
        try:
            me = os.path.abspath(__file__)
            d["file"] = os.path.basename(me); d["file_kb"] = round(os.path.getsize(me) / 1024)
            with open(me, "rb") as f:
                d["lines"] = f.read().count(b"\n")
        except OSError:
            pass
        rec = os.path.abspath(CFG["record_dir"])
        d["rec_mb"], d["rec_n"] = _dir_mb(rec) if os.path.isdir(rec) else (0, 0)
        d["data_mb"], d["data_n"] = _dir_mb(DATA_DIR, skip=(rec,))
        d["sim_mb"] = _dir_mb(sim_dir())[0] if os.path.isdir(sim_dir()) else 0
        try:
            d["settings_kb"] = round(os.path.getsize(SETTINGS_FILE) / 1024, 1)
        except OSError:
            pass
        d["python"] = sys.version.split()[0]
        try:
            with open("/proc/device-tree/model", "rb") as f:
                d["model"] = f.read().decode("utf-8", "replace").strip("\x00 \n")[:60]
        except OSError:
            d["model"] = ""
        try:
            with open("/etc/os-release") as f:
                d["os"] = next((l.split("=", 1)[1].strip().strip('"') for l in f if l.startswith("PRETTY_NAME=")), "")[:60]
        except OSError:
            d["os"] = ""
    finally:
        _PROJ.update(t=time.time(), d=d, busy=False)


def sim_control(d=None):
    """The video scenarios (and other switches) of the simulator: GET (d=None) or POST /control."""
    lang_ = norm_lang(CFG.get("lang")) or "de"             # the simulator may show its names in this language (Accept-Language)
    if d is None:
        with _SIM_OPENER.open(urllib.request.Request(sim_base() + "/control", headers={"User-Agent": "MotionWatch", "Accept-Language": lang_}),
                              timeout=4.0) as r:
            return json.loads(r.read())
    req = urllib.request.Request(sim_base() + "/control", data=json.dumps(d).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "MotionWatch", "Accept-Language": lang_})
    with _SIM_OPENER.open(req, timeout=8.0) as r:
        return json.loads(r.read())


def sim_upload(name, stream, length):
    """Pass a video from the web page straight on to the simulator (piece by piece, nothing is kept here)."""
    import http.client
    from urllib.parse import urlsplit, quote
    u = urlsplit(sim_base())
    C = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    con = C(u.hostname, u.port or (443 if u.scheme == "https" else 80), timeout=60)
    try:
        con.putrequest("POST", "/upload?name=" + quote(name))
        con.putheader("Content-Type", "application/octet-stream"); con.putheader("Content-Length", str(length))
        con.putheader("User-Agent", "MotionWatch"); con.endheaders()
        left = length
        while left > 0:
            b = stream.read(min(1 << 20, left))
            if not b:
                break
            con.send(b); left -= len(b)
        r = con.getresponse()
        return json.loads(r.read() or b"{}")
    finally:
        con.close()


def sim_eco_now():
    """CPU saving in the simulation: its own switch, or the power saving of MoveEye (2.95.25); the power mode
    switches both off (TURBO_SET)."""
    return bool(CFG.get("sim_eco") or CFG.get("eco_on"))


def sim_cam_fps(cam):
    """Pictures per second asked from the simulator: the head camera sim_fps, the fixed camera half of it.
    Power saving on and nothing happening: at most its pictures per second (eco_fps)."""
    f = max(2, min(15, int(CFG.get("sim_fps") or 6)))
    if CFG.get("eco_on") and STATE.get("eco") == "saving":      # quiet: few pictures; something moves: full speed again
        f = max(2, min(f, int(CFG.get("eco_fps") or 3)))
    return f if str(cam) == "0" else max(2, f // 2)


def sim_files():
    """sha256 of the simulator program files this MoveEye carries (name -> checksum)."""
    if not _SIMFILES:
        import base64, hashlib, io
        try:
            with zipfile.ZipFile(io.BytesIO(base64.b64decode("".join(SIM_ZIP_B64.split())))) as z:
                for n in z.namelist():
                    if n.endswith(".py"):
                        _SIMFILES[n] = hashlib.sha256(z.read(n)).hexdigest()
        except Exception:
            pass
    return dict(_SIMFILES)


def sim_autoupdate():
    """The simulator on this Pi is older than the one inside MoveEye -> install the new one (and restart it if it runs)."""
    import hashlib
    d = sim_dir()
    if not os.path.isfile(os.path.join(d, "motionwatch_simulator.py")):
        return False
    old = []
    for n, h in sim_files().items():
        try:
            with open(os.path.join(d, n), "rb") as f:
                if hashlib.sha256(f.read()).hexdigest() == h:
                    continue
        except OSError:
            pass
        old.append(n)
    if not old:
        return False
    was = sim_running()
    if was:
        sim_stop()
    try:
        sim_install()
    except Exception as e:
        log_event("sys", f"Simulator update failed: {e}"[:200]); return False
    log_event("sys", "Simulator updated automatically to the version inside MoveEye " + APP_VERSION)
    if was:
        sim_start()
    return True


