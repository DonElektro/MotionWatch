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


def refscan_is_dark():
    if CFG.get("sim_on") and SIM.get("ok"):
        return bool(SIM.get("dark"))                     # the simulation knows its own night
    return bool(LIGHTS.get("dark"))


REFSCAN_KINDS = {"day": "ref", "night": "ref_night"}  # 2.95.98: an own reference for the night (infrared picture)


def refscan_meta(kind=None):
    """the reference: of this kind (day | night), or the one that fits the light now - the other one if it is missing"""
    order = [kind] if kind else (["night", "day"] if refscan_is_dark() else ["day", "night"])
    for k in order:
        try:
            with open(refscan_dir(REFSCAN_KINDS[k], "meta.json"), encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                d["_kind"] = k
                return d
        except (OSError, ValueError, KeyError):
            continue
    return None


def refscan_save_meta(meta):
    m = {k: v for k, v in meta.items() if not k.startswith("_")}
    with open(refscan_dir(REFSCAN_KINDS[meta["_kind"]], "meta.json"), "w", encoding="utf-8") as f:
        json.dump(m, f)


def refscan_set_watch(kind, items):
    """2.95.98: things to guard (a box drawn on a reference photo): when one is missing -> alarm at once"""
    meta = refscan_meta(kind)
    if not meta:
        return False
    out = []
    np_ = len(meta.get("positions") or [])
    for it in (items or [])[:30]:
        try:
            i = int(it.get("pos")); x, y, w_, h_ = (max(0.0, min(1.0, float(it.get(k)))) for k in ("x", "y", "w", "h"))
        except (TypeError, ValueError):
            continue
        if 0 <= i < np_ and w_ > 0.005 and h_ > 0.005:
            out.append({"pos": i, "x": round(x, 4), "y": round(y, 4), "w": round(w_, 4), "h": round(h_, 4),
                        "name": re.sub(r"[\x00-\x1f<>]", "", str(it.get("name") or ""))[:40] or tr("Thing")})
    meta["watch"] = out
    refscan_save_meta(meta)
    log_event("sys", f"Reference scan: {len(out)} things to guard")
    return True


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


def refscan_start(op, reason="by hand", kind=None):
    """op: scan | compare. Runs in the background; False when something else runs or there is no reference."""
    with _REFSCAN_LOCK:
        if REFSCAN["busy"]:
            return False, "a scan is already running"
        if WATCH_REF.get("w") is None:
            return False, "no camera"
        if op == "compare" and not refscan_meta(kind):
            return False, "no reference yet - scan first"
        REFSCAN.update(busy=op, step=0, n=len(refscan_positions()) if op == "scan" else len((refscan_meta(kind) or {}).get("positions") or []),
                       msg="", stop=False, t=time.time())
    threading.Thread(target=_refscan_run, args=(op, reason, kind), daemon=True, name="refscan").start()
    log_event("sys", f"Reference scan: {'scan' if op == 'scan' else 'compare'} started ({reason})")
    return True, ""


def refscan_stop():
    REFSCAN["stop"] = True


def _refscan_run(op, reason, kind=None):
    w = WATCH_REF.get("w")
    old = (CFG["pan"], CFG["tilt"])
    try:
        if op == "scan":
            _refscan_do_scan(w)
        else:
            _refscan_do_compare(w, reason, kind)
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
    kind = "night" if refscan_is_dark() else "day"
    old = refscan_meta(kind) or {}
    meta = {"t": time.time(), "positions": [], "source": STATE.get("source_label", ""), "sim": bool(CFG.get("sim_on")),
            "dark": kind == "night", "photos": int(CFG.get("refscan_photos", 2)), "kind": kind,
            "watch": old.get("watch") if len(old.get("positions") or []) == len(refscan_positions()) else []}   # same grid: keep the guarded things
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
    shutil.rmtree(refscan_dir(REFSCAN_KINDS[kind]), ignore_errors=True)
    os.replace(tmp, refscan_dir(REFSCAN_KINDS[kind]))
    REFSCAN["msg"] = "night reference saved" if kind == "night" else "reference saved"
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
    return out[:12], (round(float(dx), 1), round(float(dy), 1)), (d, thr)


def _refscan_watch_check(it, dmap, changes):
    """is a guarded thing still there? changed pixels inside its box, or a change box over it"""
    d, thr = dmap
    H, W = d.shape
    x0, y0 = int(it["x"] * W), int(it["y"] * H)
    x1, y1 = max(x0 + 2, int((it["x"] + it["w"]) * W)), max(y0 + 2, int((it["y"] + it["h"]) * H))
    part = d[y0:y1, x0:x1]
    frac = float(np.mean(part > thr * 0.8)) if part.size else 0.0
    over = 0.0
    for c in changes:
        ix = max(0.0, min(it["x"] + it["w"], c["x"] + c["w"]) - max(it["x"], c["x"]))
        iy = max(0.0, min(it["y"] + it["h"], c["y"] + c["h"]) - max(it["y"], c["y"]))
        if c["kind"] != "new":
            over = max(over, ix * iy / max(1e-6, it["w"] * it["h"]))
    return frac > 0.22 or over > 0.35, round(max(frac, over), 2)


def _ascii(t):
    """OpenCV writes only ASCII: ä -> ae ..."""
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("é", "e"), ("è", "e"), ("à", "a"), ("ç", "c")):
        t = t.replace(a, b)
    return t.encode("ascii", "replace").decode()


REFSCAN_COLORS = {"missing": (60, 60, 255), "new": (255, 160, 60), "changed": (40, 170, 255)}


def _refscan_mark(img, changes):
    out = img.copy(); H, W = out.shape[:2]
    lab = {"missing": tr("missing"), "new": tr("new"), "changed": tr("changed")}
    for c in changes:
        x, y, w_, h_ = int(c["x"] * W), int(c["y"] * H), int(c["w"] * W), int(c["h"] * H)
        col = REFSCAN_COLORS.get(c["kind"], (255, 255, 255))
        cv2.rectangle(out, (x, y), (x + w_, y + h_), col, max(2, W // 320))
        txt = _ascii(lab.get(c["kind"], c["kind"]))
        cv2.putText(out, txt, (x + 4, max(18, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, max(0.5, W / 1400), col, 2, cv2.LINE_AA)
    return out


def _refscan_mark_watch(img, items):
    H, W = img.shape[:2]
    for it in items:
        x, y, w_, h_ = int(it["x"] * W), int(it["y"] * H), int(it["w"] * W), int(it["h"] * H)
        col = (40, 40, 255) if it["gone"] else (80, 210, 80)
        for k in range(0, w_, 12):                          # dashed: a guarded thing
            cv2.line(img, (x + k, y), (x + min(w_, k + 6), y), col, 2); cv2.line(img, (x + k, y + h_), (x + min(w_, k + 6), y + h_), col, 2)
        for k in range(0, h_, 12):
            cv2.line(img, (x, y + k), (x, y + min(h_, k + 6)), col, 2); cv2.line(img, (x + w_, y + k), (x + w_, y + min(h_, k + 6)), col, 2)
        txt = _ascii(str(it["name"]) + (" !" if it["gone"] else " ok"))
        cv2.putText(img, txt, (x + 4, y + h_ - 6), cv2.FONT_HERSHEY_SIMPLEX, max(0.5, W / 1400), col, 2, cv2.LINE_AA)
    return img


def _refscan_do_compare(w, reason, kind=None):
    meta = refscan_meta(kind) or {}
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rd = refscan_dir("reports", stamp)
    os.makedirs(rd, exist_ok=True)
    rep = {"id": stamp, "t": time.time(), "reason": reason, "ref_t": meta.get("t"), "positions": [], "missing": 0, "new": 0, "changed": 0,
           "ref_kind": meta.get("_kind", "day"), "dark_now": refscan_is_dark(), "watch": []}
    for k, p in enumerate(meta.get("positions") or []):
        if REFSCAN["stop"]:
            REFSCAN["msg"] = "stopped"; break
        REFSCAN["step"] = k + 1
        ref = cv2.imread(refscan_dir(REFSCAN_KINDS[meta.get("_kind", "day")], p["file"]))
        _refscan_move(p["pan"], p["tilt"])
        cur = _refscan_grab(w, _refscan_settle() if k else _refscan_settle() + 1.0, max(1, min(5, int(CFG.get("refscan_photos", 2)))))
        if ref is None or cur is None:
            continue
        if cur.shape != ref.shape:
            cur = cv2.resize(cur, (ref.shape[1], ref.shape[0]))
        ch, sh, dmap = refscan_compare_images(ref, cur)
        for c in ch:
            rep[c["kind"]] += 1
        for it in [x for x in (meta.get("watch") or []) if int(x.get("pos", -1)) == int(p["i"])]:
            gone, sc = _refscan_watch_check(it, dmap, ch)
            rep["watch"].append({"name": it["name"], "pos": p["i"], "gone": gone, "score": sc, "x": it["x"], "y": it["y"], "w": it["w"], "h": it["h"]})
        wl = [x for x in rep["watch"] if x["pos"] == p["i"]]
        cv2.imwrite(os.path.join(rd, f"cur_{p['i']:02d}.jpg"), _refscan_mark_watch(_refscan_mark(cur, ch), wl), [cv2.IMWRITE_JPEG_QUALITY, 82])
        cv2.imwrite(os.path.join(rd, f"ref_{p['i']:02d}.jpg"), _refscan_mark(ref, [c for c in ch if c["kind"] != "new"]), [cv2.IMWRITE_JPEG_QUALITY, 82])
        rep["positions"].append({"i": p["i"], "pan": p["pan"], "tilt": p["tilt"], "changes": ch, "shift": sh})
    with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f)
    _refscan_trim()
    REFSCAN["last"] = refscan_summary(rep)
    REFSCAN["msg"] = "report ready"
    n = rep["missing"] + rep["new"] + rep["changed"]
    log_event("sys", f"Reference scan compared ({reason}): {rep['missing']} missing, {rep['new']} new, {rep['changed']} changed")
    gone = [x["name"] for x in rep["watch"] if x["gone"]]
    if gone:                                             # 2.95.98: a guarded thing is missing -> alarm at once
        txt = trf("Guarded thing missing: {names}", names=", ".join(gone))
        log_event("alarm", "Reference scan: guarded thing missing: " + ", ".join(gone))
        push_alert("refscan", txt)
        try:
            img = cv2.imread(os.path.join(rd, f"cur_{int([x for x in rep['watch'] if x['gone']][0]['pos']):02d}.jpg"))
            w.notifier.alert("{name}: " + tr("Reference scan"), txt, img)
        except Exception:
            pass
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
            "positions": len(rep.get("positions") or []), "ref_kind": rep.get("ref_kind", "day"), "dark_now": rep.get("dark_now", False),
            "gone": [x["name"] for x in rep.get("watch") or [] if x.get("gone")], "watched": len(rep.get("watch") or [])}


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
    one = lambda m: {"t": m.get("t"), "n": len(m.get("positions") or []), "sim": m.get("sim"), "kind": m.get("_kind"),
                     "dir": REFSCAN_KINDS[m.get("_kind", "day")], "positions": m.get("positions"), "watch": m.get("watch") or []} if m else None
    return {"busy": REFSCAN["busy"], "step": REFSCAN["step"], "n": REFSCAN["n"], "msg": REFSCAN["msg"], "dark": refscan_is_dark(),
            "ref": one(meta), "refs": {"day": one(refscan_meta("day")), "night": one(refscan_meta("night"))},
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
