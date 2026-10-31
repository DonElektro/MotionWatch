#@ MoveEye – Teil 397: Zusatzdaten nachladen (moveeye_daten_X_Y_Z.zip über die Update-Quelle holen, prüfen, einmal neu starten), alte Zusatzdateien aufräumen, Brücken-Version. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «MoveEye-Datei verkleinern» (31.10.2026). Loading is in part 012 (ZD, _zd, zd_source). Here:
#   zusatz_start()          called by main() after start_guard(): without the zip a thread fetches it (same update source
#                           as the program: GitHub address of versions.json or a USB folder), checks the SHA-256 that is
#                           written into this signed program (ZD_SHA256) and restarts once (same PID, like an update).
#   zusatz_mitholen(...)    called by update_install() (390) after a new program file was saved: its zip comes along at once
#                           (so a device from this version on has no minute without web pages).
# Older devices (2.98.x up to the last version without data zip) only fetch the .py - the new program fetches its zip itself (zusatz_start).
# Brücke (Entscheid Daniel 31.10.2026): UPD_BRIDGE (3.0.2, one file below 8 MiB, no zip needed) stays in versions.json and in
# the repository for ever. A version entry with «needs» (lowest version that may install it directly) is offered only to
# devices with at least that version; older ones get the newest bridge first (update_pick(), used by update_check()).
# ----------------------------------------------------------------------------
ZDL = {"state": "", "msg": "", "t": 0.0, "tries": 0}
UPD_BRIDGE = "3.0.2"                                       # versionen.py BRUECKE - never removed from versions.json / repository
ZD_MAX_BYTES = 64 * 1024 * 1024


def _zd_name_of(text):
    """(ZD_FILE, ZD_SHA256) written into a program text, ("", "") for a file without data zip"""
    m = re.search(r'^ZD_FILE = "(moveeye_daten_\d{1,3}_\d{1,3}_\d{1,3}\.zip)"\s*\nZD_SHA256 = "([0-9a-f]{64})"', text, re.M)
    return (m.group(1), m.group(2)) if m else ("", "")


def _zd_fetch_bytes(name, src_url="", src_dir=""):
    """the bytes of the data zip <name> from the update source (https address of a program file / versions.json, or a folder)"""
    if src_dir:
        p = os.path.join(src_dir, name)
        with open(p, "rb") as f:
            return f.read(ZD_MAX_BYTES + 1)
    url = src_url.rsplit("/", 1)[0] + "/" + name
    if not url.startswith("https://"):
        raise ValueError("no update source")
    with urllib.request.urlopen(_upd_request(url), timeout=60) as r:
        parts, n = [], 0
        while n <= ZD_MAX_BYTES:
            b = r.read(min(65536, ZD_MAX_BYTES + 1 - n))
            if not b:
                break
            parts.append(b); n += len(b)
    return b"".join(parts)


def _zd_check_bytes(data, sha, version):
    """"" = this zip belongs to <version> and has the checksum <sha>; else the reason"""
    import io as _io
    if not data or len(data) > ZD_MAX_BYTES:
        return "no data file"
    if hashlib.sha256(data).hexdigest() != sha:
        return "the data file does not match the program (checksum)"
    try:
        with zipfile.ZipFile(_io.BytesIO(data)) as z:
            d = json.loads(z.read("daten.json").decode("utf-8"))
    except Exception:
        return "the data file is damaged"
    if str(d.get("version")) != version or not d.get("entries"):
        return "the data file belongs to an other version"
    return ""


def _zd_save(folder, name, data):
    p = os.path.join(folder, name)
    tmp = p + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, p)
    return p


def zusatz_mitholen(text, version, src_url="", src_dir=""):
    """update_install (390): the new program file <text> was saved next to this one - fetch its data zip too.
    Never stops the update: without the zip the new version fetches it itself after the start."""
    try:
        name, sha = _zd_name_of(text)
        if not name:
            return ""
        p = os.path.join(HERE, name)
        if os.path.isfile(p):
            with open(p, "rb") as f:
                if not _zd_check_bytes(f.read(ZD_MAX_BYTES + 1), sha, version):
                    return ""
        data = _zd_fetch_bytes(name, src_url, src_dir)
        err = _zd_check_bytes(data, sha, version)
        if err:
            log_event("sys", f"Update {version}: data file not taken ({err}) - the new version fetches it itself")
            return err
        _zd_save(HERE, name, data)
        log_event("sys", f"Update {version}: data file {name} downloaded")
        return ""
    except Exception as e:
        log_event("sys", f"Update {version}: data file not downloaded ({_upd_error(e)})"[:220])
        return str(e)[:200]


def _zd_restart_ok():
    """at most one automatic restart per version and 30 minutes (never a loop)"""
    p = os.path.join(DATA_DIR, "zusatz_restart.json")
    try:
        with open(p) as f:
            d = json.load(f)
        if d.get("version") == APP_VERSION and time.time() - float(d.get("t", 0)) < 1800:
            return False
    except (OSError, ValueError, TypeError):
        pass
    try:
        with open(p, "w") as f:
            json.dump({"version": APP_VERSION, "t": time.time()}, f)
    except OSError:
        pass
    return True


def zusatz_restart():
    """like update_restart (390), but the same file and the start guard of an update stays as it is"""
    if RESTART.get("pending"):
        return False
    RESTART["pending"] = "zusatz"
    log_event("sys", "Data file is there - restarting once to load web pages, pictures and translations")

    def work():
        time.sleep(2.0)
        try:
            w = WATCH_REF["w"]
            end = time.time() + 120.0                    # wait for a running recording / alarm (never cut it)
            while time.time() < end and (STATE.get("recording") or STATE.get("persons")
                                         or (w is not None and getattr(w, "writer", None) is not None)):
                time.sleep(0.5)
            if AUDIO is not None:
                AUDIO.wait_mux(30.0)
            sound_stop(); talk_stop()
            save_settings_now()
            _close_fds_on_exec()
            os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)] + _base_args())
        except Exception as e:
            RESTART["pending"] = ""
            log_event("sys", f"Restart for the data file failed: {e}"[:200])
    threading.Thread(target=work, daemon=True, name="zusatz-restart").start()
    return True


def zusatz_holen():
    """one try: fetch the zip of this version from the update source (else the repository of the simulator updates,
    SIM3D_BASE in 300), check it, save it. "" = there now"""
    src = CFG["update_url"].strip()
    tries = []
    if src.startswith("/"):
        tries.append(("", src))
    elif src.startswith("https://"):
        tries.append((src, ""))
    try:
        if SIM3D_BASE.startswith("https://") and not src.startswith(SIM3D_BASE):
            tries.append((SIM3D_BASE + "versions.json", ""))
    except NameError:
        pass
    err = "no update source set"
    for url, folder in tries:
        try:
            data = _zd_fetch_bytes(ZD_FILE, src_url=url, src_dir=folder)
        except Exception as e:
            err = f"not reachable: {_upd_error(e)}"[:200]
            continue
        err = _zd_check_bytes(data, ZD_SHA256, APP_VERSION)
        if err:
            continue
        try:
            _zd_save(HERE, ZD_FILE, data)
        except OSError as e:
            return f"cannot save: {e}"[:200]
        return ""
    return err


def zusatz_aufraeumen():
    """data zips of program files that are no longer there go away (the zip of every program file next to it stays)"""
    try:
        names = os.listdir(HERE)
    except OSError:
        return
    for n in names:
        m = re.match(r"^moveeye_daten_(\d{1,3}_\d{1,3}_\d{1,3})\.zip(\.part)?$", n)
        if m and ("webcam_bewegung_%s.py" % m.group(1)) not in names and n != ZD_FILE:
            try:
                os.remove(os.path.join(HERE, n))
            except OSError:
                pass


def zusatz_state():
    return {"ok": bool(ZD["ok"]), "file": ZD_FILE, "err": ZD["err"], "missing": len(ZD["miss"]) if not ZD["ok"] else 0,
            "state": ZDL["state"], "msg": ZDL["msg"]}


def zusatz_start():
    """main(): with the zip only tidy up; without it the core runs and a thread fetches the zip, then one restart"""
    if ZD["ok"]:
        zusatz_aufraeumen()
        return
    STATE["zusatz_fehlt"] = True
    msg = f"Additional data missing ({ZD_FILE}: {ZD['err']}) - MoveEye protects (core), web pages / pictures / translations come after the update of the data file"
    print(msg)
    log_event("sys", msg[:240])

    def loop():
        wait = 15
        while True:
            time.sleep(wait)
            ZDL.update(state="fetch", t=time.time(), tries=ZDL["tries"] + 1)
            err = zusatz_holen()
            if not err:
                ZDL.update(state="ok", msg="")
                log_event("sys", f"Data file {ZD_FILE} fetched and checked")
                if _zd_restart_ok():
                    zusatz_restart()
                else:
                    ZDL.update(state="restart", msg="restart MoveEye to load the data file")
                return
            ZDL.update(state="wait", msg=err)
            if ZDL["tries"] in (1, 4):
                log_event("sys", f"Data file not fetched: {err}"[:220])
            wait = min(3600, 600 if ZDL["tries"] < 6 else 1800 if ZDL["tries"] < 12 else 3600)
    threading.Thread(target=loop, daemon=True, name="zusatz").start()


def update_pick(newer):
    """Brücke: from the newer installable versions (newest first) the one this device may install now - the newest whose
    «needs» (lowest version for a direct update) this version meets; else the newest bridge version (marked «bridge»)."""
    for x in newer:
        if _vkey(APP_VERSION) >= _vkey(x.get("needs") or "0"):
            return x
    br = [x for x in newer if x.get("bridge")]
    return br[0] if br else None


def zusatz_selftest():
    if not ZD_FILE:
        return "nothing moved out (built without data file)"
    assert ZD["ok"], f"{ZD_FILE}: {ZD['err']}"
    assert not ZD["miss"], f"{len(ZD['miss'])} literals not in the data file: {ZD['miss'][:5]}"
    src = zd_source()
    assert not re.search(r"_zd\('\d{3}", src), "a moved-out literal is not back in zd_source()"
    assert len(src) > os.path.getsize(os.path.abspath(__file__)), "zd_source() is not bigger than the file"
    assert update_pick([{"version": "9.0.0", "needs": "99.0.0"}, {"version": "8.0.0", "bridge": True}])["version"] == "8.0.0"
    assert update_pick([{"version": "9.0.0"}])["version"] == "9.0.0"
    return f"{ZD['used']} literals from {ZD_FILE} ({os.path.getsize(ZD['path']) // 1024} KB), program file {os.path.getsize(os.path.abspath(__file__)) // 1024} KB"


SELFTEST_EXTRA.append(("Data file (moveeye_daten zip: checksum, all literals, source), bridge update", zusatz_selftest))
