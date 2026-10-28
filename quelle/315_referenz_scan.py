#@ Motion Watch – Teil 315: Referenz-Scan (2.95.97). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# The camera head drives a grid of directions and keeps a few photos of each as the reference. Later it drives the same
# directions again, compares and writes a report: what is missing, what is new, what changed. Started from the web page
# (assistant), the window, automatically when armed / every N minutes, or from the 3D simulator (button).

REFSCAN = {"busy": "", "step": 0, "n": 0, "msg": "", "stop": False, "t": 0.0, "last": None, "next_t": 0.0}
_REFSCAN_LOCK = threading.Lock()


def refscan_dir(*p):
    d = os.path.join(DATA_DIR, "refscan", *p)
    return d


def refscan_positions():
    """the directions of the scan: pan steps from .. to, tilt steps around the middle (in % like the servos)"""
    n = max(1, min(12, int(CFG.get("refscan_pan_steps", 6))))
    a, b = float(CFG.get("refscan_pan_from", 10)), float(CFG.get("refscan_pan_to", 90))
    pans = [round((a + b) / 2.0, 1)] if n == 1 else [round(a + (b - a) * i / (n - 1), 1) for i in range(n)]
    m = max(1, min(3, int(CFG.get("refscan_tilt_steps", 1))))
    sp = float(CFG.get("refscan_tilt_span", 16))
    c = float(CFG.get("refscan_tilt_mid", 50))
    tilts = [round(c, 1)] if m == 1 else [round(c - sp / 2.0 + sp * j / (m - 1), 1) for j in range(m)]
    out = []
    for j, t in enumerate(tilts):                       # a snake: left to right, then right to left (short ways)
        row = pans if j % 2 == 0 else list(reversed(pans))
        out += [(p, t) for p in row]
    return out


def refscan_meta():
    try:
        with open(refscan_dir("ref", "meta.json"), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _refscan_move(pan, tilt):
    CFG["pan"] = max(0.0, min(100.0, float(pan))); CFG["tilt"] = max(0.0, min(100.0, float(tilt)))
    MANUAL["until"] = time.time() + 60                  # following / patrol pause while the scan drives the head


def _refscan_next(w, after, end):
    """the next picture (without boxes and texts) that is newer than `after`: (time, picture) or (None, None)"""
    while time.time() < end and not REFSCAN["stop"]:
        w.raw_until = time.time() + 20
        fr = w.frame_raw
        t0 = float(getattr(w, "_last_t0", 0) or 0)
        if fr is not None and t0 > after:
            return t0, fr.copy()
        time.sleep(0.04)
    return None, None


def _refscan_small(img):
    return cv2.cvtColor(cv2.resize(img, (160, 90), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)


def _refscan_grab(w, settle, count):
    """wait until the head stands and the picture no longer changes (a servo or the simulator may be late), then a few
    pictures (without boxes and texts) -> median"""
    time.sleep(settle)
    end = time.time() + 15 + count * 2
    t_last, prev = _refscan_next(w, time.time() - 0.01, end)
    stable = 0
    while prev is not None and stable < 2 and time.time() < end:      # still turning? two quiet pictures in a row
        t_last, cur = _refscan_next(w, t_last, end)
        if cur is None:
            break
        d = float(np.mean(cv2.absdiff(_refscan_small(prev), _refscan_small(cur))))
        stable = stable + 1 if d < 3.0 else 0
        prev = cur
    if prev is None:
        return None
    pics = [prev]
    while len(pics) < count and time.time() < end:
        t_last, cur = _refscan_next(w, t_last, end)
        if cur is None:
            break
        pics.append(cur)
    if len(pics) == 1:
        return pics[0]
    try:
        return np.median(np.stack(pics[:5]), axis=0).astype(np.uint8)
    except ValueError:
        return pics[-1]


def _refscan_settle():
    return max(0.3, float(CFG.get("refscan_settle", 1.5))) + (1.5 if CFG.get("sim_on") else 0.0)   # the simulator answers later


def refscan_start(op, reason="by hand"):
    """op: scan | compare. Runs in the background; False when something else runs or there is no reference."""
    with _REFSCAN_LOCK:
        if REFSCAN["busy"]:
            return False, "a scan is already running"
        if WATCH_REF.get("w") is None:
            return False, "no camera"
        if op == "compare" and not refscan_meta():
            return False, "no reference yet - scan first"
        REFSCAN.update(busy=op, step=0, n=len(refscan_positions()) if op == "scan" else len((refscan_meta() or {}).get("positions") or []),
                       msg="", stop=False, t=time.time())
    threading.Thread(target=_refscan_run, args=(op, reason), daemon=True, name="refscan").start()
    log_event("sys", f"Reference scan: {'scan' if op == 'scan' else 'compare'} started ({reason})")
    return True, ""


def refscan_stop():
    REFSCAN["stop"] = True


def _refscan_run(op, reason):
    w = WATCH_REF.get("w")
    old = (CFG["pan"], CFG["tilt"])
    try:
        if op == "scan":
            _refscan_do_scan(w)
        else:
            _refscan_do_compare(w, reason)
    except Exception as e:                               # never leave the head in a strange place
        REFSCAN["msg"] = "error: " + str(e)[:120]
        log_event("sys", f"Reference scan failed: {e}")
    finally:
        _refscan_move(*old)
        MANUAL["until"] = time.time() + 2
        REFSCAN["busy"] = ""; REFSCAN["stop"] = False


def _refscan_do_scan(w):
    pos = refscan_positions()
    tmp = refscan_dir("ref_new")
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp, exist_ok=True)
    meta = {"t": time.time(), "positions": [], "source": STATE.get("source_label", ""), "sim": bool(CFG.get("sim_on")),
            "dark": bool(LIGHTS.get("dark")), "photos": int(CFG.get("refscan_photos", 2))}
    for i, (p, t) in enumerate(pos):
        if REFSCAN["stop"]:
            REFSCAN["msg"] = "stopped"; shutil.rmtree(tmp, ignore_errors=True); return
        REFSCAN["step"] = i + 1
        _refscan_move(p, t)
        img = _refscan_grab(w, _refscan_settle() if i else _refscan_settle() + 1.0, max(1, min(5, int(CFG.get("refscan_photos", 2)))))
        if img is None:
            REFSCAN["msg"] = "no picture from the camera"; shutil.rmtree(tmp, ignore_errors=True); return
        fn = f"pos_{i:02d}.jpg"
        cv2.imwrite(os.path.join(tmp, fn), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        meta["positions"].append({"i": i, "pan": p, "tilt": t, "file": fn})
    with open(os.path.join(tmp, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    shutil.rmtree(refscan_dir("ref"), ignore_errors=True)
    os.replace(tmp, refscan_dir("ref"))
    REFSCAN["msg"] = "reference saved"
    log_event("sys", f"Reference scan: {len(pos)} directions saved as the reference")


def _refscan_prep(img, width=640):
    h, w_ = img.shape[:2]
    s = width / float(w_)
    g = cv2.cvtColor(cv2.resize(img, (width, int(h * s)), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    g = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)
    return cv2.GaussianBlur(g, (3, 3), 0), s


def refscan_compare_images(ref, cur):
    """the changes between two pictures of the same direction: [{x, y, w, h (0..1), kind: missing | new | changed, score}]"""
    a, _ = _refscan_prep(ref)
    b, _ = _refscan_prep(cur)
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]))
    H, W = a.shape
    try:                                                 # the head never stands exactly where it stood: shift it back
        win = cv2.createHanningWindow((W, H), cv2.CV_32F)
        (dx, dy), _r = cv2.phaseCorrelate(a.astype(np.float32), b.astype(np.float32), win)
        if abs(dx) < W * 0.12 and abs(dy) < H * 0.12:
            b = cv2.warpAffine(b, np.float32([[1, 0, -dx], [0, 1, -dy]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
    except cv2.error:
        dx = dy = 0.0
    # brightness of the whole picture may differ (sun, clouds): both to the same mean and spread
    af, bf = a.astype(np.float32), b.astype(np.float32)
    bf = (bf - bf.mean()) / max(1.0, bf.std()) * max(1.0, af.std()) + af.mean()
    d1 = cv2.absdiff(af, bf)
    ga = cv2.magnitude(cv2.Sobel(af, cv2.CV_32F, 1, 0), cv2.Sobel(af, cv2.CV_32F, 0, 1))
    gb = cv2.magnitude(cv2.Sobel(bf, cv2.CV_32F, 1, 0), cv2.Sobel(bf, cv2.CV_32F, 0, 1))
    d2 = cv2.absdiff(cv2.GaussianBlur(ga, (9, 9), 0), cv2.GaussianBlur(gb, (9, 9), 0)) * 0.5
    d = cv2.GaussianBlur(0.55 * d1 + 0.45 * d2, (7, 7), 0)
    sens = max(5.0, min(100.0, float(CFG.get("refscan_sens", 50))))
    thr = 52.0 - sens * 0.45                              # 50 % -> 29.5 grey values
    m = (d > thr).astype(np.uint8) * 255
    bx = int(W * 0.03); by = int(H * 0.03)
    m[:by, :] = 0; m[-by:, :] = 0; m[:, :bx] = 0; m[:, -bx:] = 0      # the border (shifted picture) does not count
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))   # thin things (a bike, a chair) first become areas
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_a = W * H * max(0.05, float(CFG.get("refscan_min_area", 0.6))) / 100.0
    out = []
    for c in cnts:
        if cv2.contourArea(c) < min_a:
            continue
        x, y, w_, h_ = cv2.boundingRect(c)
        ea = float(ga[y:y + h_, x:x + w_].mean()); eb = float(gb[y:y + h_, x:x + w_].mean())
        kind = "missing" if ea > eb * 1.3 + 2 else ("new" if eb > ea * 1.3 + 2 else "changed")
        out.append({"x": round(x / W, 4), "y": round(y / H, 4), "w": round(w_ / W, 4), "h": round(h_ / H, 4), "kind": kind,
                    "score": round(float(d[y:y + h_, x:x + w_].mean()), 1)})
    out.sort(key=lambda r: -r["w"] * r["h"])
    return out[:12], (round(float(dx), 1), round(float(dy), 1))


REFSCAN_COLORS = {"missing": (60, 60, 255), "new": (255, 160, 60), "changed": (40, 170, 255)}


def _refscan_mark(img, changes):
    out = img.copy(); H, W = out.shape[:2]
    lab = {"missing": tr("missing"), "new": tr("new"), "changed": tr("changed")}
    for c in changes:
        x, y, w_, h_ = int(c["x"] * W), int(c["y"] * H), int(c["w"] * W), int(c["h"] * H)
        col = REFSCAN_COLORS.get(c["kind"], (255, 255, 255))
        cv2.rectangle(out, (x, y), (x + w_, y + h_), col, max(2, W // 320))
        txt = lab.get(c["kind"], c["kind"]).encode("ascii", "replace").decode()
        cv2.putText(out, txt, (x + 4, max(18, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, max(0.5, W / 1400), col, 2, cv2.LINE_AA)
    return out


def _refscan_do_compare(w, reason):
    meta = refscan_meta() or {}
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rd = refscan_dir("reports", stamp)
    os.makedirs(rd, exist_ok=True)
    rep = {"id": stamp, "t": time.time(), "reason": reason, "ref_t": meta.get("t"), "positions": [], "missing": 0, "new": 0, "changed": 0}
    for k, p in enumerate(meta.get("positions") or []):
        if REFSCAN["stop"]:
            REFSCAN["msg"] = "stopped"; break
        REFSCAN["step"] = k + 1
        ref = cv2.imread(refscan_dir("ref", p["file"]))
        _refscan_move(p["pan"], p["tilt"])
        cur = _refscan_grab(w, _refscan_settle() if k else _refscan_settle() + 1.0, max(1, min(5, int(CFG.get("refscan_photos", 2)))))
        if ref is None or cur is None:
            continue
        if cur.shape != ref.shape:
            cur = cv2.resize(cur, (ref.shape[1], ref.shape[0]))
        ch, sh = refscan_compare_images(ref, cur)
        for c in ch:
            rep[c["kind"]] += 1
        cv2.imwrite(os.path.join(rd, f"cur_{p['i']:02d}.jpg"), _refscan_mark(cur, ch), [cv2.IMWRITE_JPEG_QUALITY, 82])
        cv2.imwrite(os.path.join(rd, f"ref_{p['i']:02d}.jpg"), _refscan_mark(ref, [c for c in ch if c["kind"] != "new"]), [cv2.IMWRITE_JPEG_QUALITY, 82])
        rep["positions"].append({"i": p["i"], "pan": p["pan"], "tilt": p["tilt"], "changes": ch, "shift": sh})
    with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f)
    _refscan_trim()
    REFSCAN["last"] = refscan_summary(rep)
    REFSCAN["msg"] = "report ready"
    n = rep["missing"] + rep["new"] + rep["changed"]
    log_event("sys", f"Reference scan compared ({reason}): {rep['missing']} missing, {rep['new']} new, {rep['changed']} changed")
    if n and CFG.get("refscan_push", True) and (rep["missing"] or CFG.get("refscan_push_all", False)) and w is not None:
        try:
            w.notifier.info(trf("Reference scan: {m} missing, {n} new, {c} changed - see the report", m=rep["missing"], n=rep["new"], c=rep["changed"]),
                            title="{name}: " + tr("Reference scan"))
        except Exception:
            pass


def _refscan_trim(keep=20):
    try:
        ids = sorted(os.listdir(refscan_dir("reports")))
        for x in ids[:-keep]:
            shutil.rmtree(refscan_dir("reports", x), ignore_errors=True)
    except OSError:
        pass


def refscan_report(rid):
    if not re.fullmatch(r"\d{8}_\d{6}", str(rid or "")):
        return None
    try:
        with open(refscan_dir("reports", rid, "report.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def refscan_summary(rep):
    return {"id": rep["id"], "t": rep["t"], "reason": rep.get("reason", ""), "missing": rep["missing"], "new": rep["new"], "changed": rep["changed"],
            "positions": len(rep.get("positions") or [])}


def refscan_reports():
    out = []
    try:
        for x in sorted(os.listdir(refscan_dir("reports")), reverse=True)[:20]:
            r = refscan_report(x)
            if r:
                out.append(refscan_summary(r))
    except OSError:
        pass
    return out


def refscan_state():
    meta = refscan_meta()
    return {"busy": REFSCAN["busy"], "step": REFSCAN["step"], "n": REFSCAN["n"], "msg": REFSCAN["msg"],
            "ref": {"t": meta.get("t"), "n": len(meta.get("positions") or []), "sim": meta.get("sim"),
                    "positions": meta.get("positions")} if meta else None,
            "plan": len(refscan_positions()), "reports": refscan_reports(), "next_t": REFSCAN["next_t"] or None}


def refscan_status_text():
    st = refscan_state()
    if st["busy"]:
        return trf("{what}: direction {i} of {n} …", what=tr("Scanning") if st["busy"] == "scan" else tr("Comparing"), i=st["step"], n=st["n"])
    s = (trf("Reference: {n} directions, {t}", n=st["ref"]["n"], t=datetime.fromtimestamp(st["ref"]["t"]).strftime("%d.%m. %H:%M"))
         if st["ref"] else tr("No reference yet"))
    if st["reports"]:
        r = st["reports"][0]
        s += " · " + trf("last check: {m} missing, {n} new, {c} changed", m=r["missing"], n=r["new"], c=r["changed"])
    return s


def refscan_on_armed():
    """armed now: compare with the reference (if wanted and there is one)"""
    if CFG.get("refscan_on_arm") and refscan_meta() and not REFSCAN["busy"]:
        refscan_start("compare", "armed")


def refscan_tick():
    """every N minutes while armed (called by the background loop)"""
    every = float(CFG.get("refscan_every", 0) or 0)
    if every <= 0 or not CFG.get("armed") or STATE.get("arm_state") != "armed" or not refscan_meta():
        REFSCAN["next_t"] = 0.0
        return
    now = time.time()
    if not REFSCAN["next_t"]:
        REFSCAN["next_t"] = now + every * 60
    if now >= REFSCAN["next_t"] and not REFSCAN["busy"] and STATE.get("persons", 0) == 0:
        REFSCAN["next_t"] = now + every * 60
        refscan_start("compare", "every %d min" % int(every))


def _refscan_loop():
    while True:
        time.sleep(20)
        try:
            refscan_tick()
        except Exception:
            pass


threading.Thread(target=_refscan_loop, daemon=True, name="refscantick").start()
