#@ MoveEye – Teil 316: Panorama-Bericht «Fehlende Gegenstände» (aus dem Referenz-Scan). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.1: a separate report next to the night report (switch «refscan_pano_on»): one panorama picture made of the reference
# photos (all directions of the scan side by side, rows by tilt), on it every change of the night marked - red = gone,
# green = new (put there), orange = changed - with the time it was first noticed (and when it was back again, if so).
# Comes in the morning with the night report (report_hour) as push with the picture; kept in refscan/panorama/ (14 days).
# ----------------------------------------------------------------------------
PANO = {"busy": False, "day": "", "msg": ""}
PANO_COL = {"missing": (60, 60, 230), "new": (80, 200, 60), "changed": (40, 160, 245)}


def pano_dir(*p):
    return refscan_dir("panorama", *p)


def _pano_reports(since, until):
    out = []
    try:
        for x in sorted(os.listdir(refscan_dir("reports"))):
            r = refscan_report(x)
            if r and since <= float(r.get("t", 0)) <= until:
                out.append(r)
    except OSError:
        pass
    return out


def _pano_track(reps):
    """the same change in several reports = one mark: first seen, last seen, back again (not in a later report)"""
    marks = []
    for r in reps:
        seen_now = set()
        for p in r.get("positions") or []:
            for c in p.get("changes") or []:
                if c["w"] * c["h"] > 0.45:
                    continue                               # nearly the whole picture: the light changed, not a thing
                cx, cy = c["x"] + c["w"] / 2.0, c["y"] + c["h"] / 2.0
                hit = None
                for m in marks:
                    if m["pos"] == p["i"] and m["kind"] == c["kind"] and abs(m["cx"] - cx) < 0.08 and abs(m["cy"] - cy) < 0.08:
                        hit = m
                        break
                if hit is None:
                    hit = {"pos": p["i"], "kind": c["kind"], "cx": cx, "cy": cy, "box": [c["x"], c["y"], c["w"], c["h"]], "first": r["t"], "last": r["t"],
                           "back": None, "name": ""}
                    marks.append(hit)
                hit["last"] = r["t"]
                hit["back"] = None
                seen_now.add(id(hit))
        for w_ in r.get("watch") or []:                    # the guarded things: their names
            if w_.get("gone"):
                for m in marks:
                    if m["pos"] == w_["pos"] and abs(m["cx"] - (w_["x"] + w_["w"] / 2)) < 0.12 and abs(m["cy"] - (w_["y"] + w_["h"] / 2)) < 0.12:
                        m["name"] = w_["name"]
        for m in marks:
            if id(m) not in seen_now and m["back"] is None and m["last"] < r["t"]:
                m["back"] = r["t"]                         # in this report it was not there any more
    return marks


def pano_canvas(pos, load, tw=320, head=0, foot=0, geo=None):
    """2.98.30: the panorama picture of the reference-scan directions - used by the morning report (pano_build) and by
    «Platz einrichten» (317). pos: [{"i", "pan", "tilt", …}], load(p) -> picture or None.
    geo None: every photo whole, side by side (columns = pan, rows = tilt, looking up = the upper row) as before.
    geo {"hf", "vf", "hp", "ht", "wrap", "a0"?, "a1"?, "e0"?, "e1"?}: a stitched panorama in degrees - of every photo only the
    part up to the middle between it and its neighbours, so x / y of the canvas are directions: az = a0 + x / k,
    el = e_top - (y - head) / k (k pixels per degree). wrap (a 360° head): the first column is repeated after the seam.
    Returns (canvas, cells) - cells {i: {"col", "row", "tw", "th", "x0", "y0", "x1", "y1"}}; with geo also cells["_geo"]."""
    if geo is None:
        pans = sorted({p["pan"] for p in pos})
        tilts = sorted({p["tilt"] for p in pos}, reverse=True)
        th = None
        tiles = {}
        for p in pos:
            im = load(p)
            if im is None:
                continue
            h = int(round(im.shape[0] * tw / im.shape[1]))
            th = th or h
            tiles[p["i"]] = (cv2.resize(im, (tw, th)), pans.index(p["pan"]), tilts.index(p["tilt"]))
        if not tiles:
            return None, {}
        W, H = tw * len(pans), th * len(tilts) + head + foot
        can = np.full((H, W, 3), 22, np.uint8)
        cells = {}
        for i, (im, cx, cy) in tiles.items():
            can[head + cy * th: head + (cy + 1) * th, cx * tw: (cx + 1) * tw] = im
            cells[i] = {"col": cx, "row": cy, "tw": tw, "th": th, "x0": cx * tw, "y0": head + cy * th, "x1": (cx + 1) * tw, "y1": head + (cy + 1) * th}
        return can, cells
    hf, vf, hp, ht = float(geo["hf"]), float(geo["vf"]), float(geo["hp"]), float(geo["ht"])
    wrap = bool(geo.get("wrap"))
    k = tw / hf                                            # pixels per degree (the same both ways)
    azs = sorted({(float(p["pan"]) - 50.0) / 50.0 * hp for p in pos})
    els = sorted({(float(p["tilt"]) - 50.0) / 50.0 * ht for p in pos}, reverse=True)

    def bounds(cs, fov, wrap_):
        out = []
        for j, c in enumerate(cs):
            if wrap_ and len(cs) > 1:
                st = 360.0 / len(cs)
                lo, hi = c - st / 2.0, c + st / 2.0
            else:
                lo = (cs[j - 1] + c) / 2.0 if j > 0 else c - fov / 2.0
                hi = (cs[j + 1] + c) / 2.0 if j + 1 < len(cs) else c + fov / 2.0
            out.append((max(lo, c - fov / 2.0), min(hi, c + fov / 2.0)))
        return out
    ab = bounds(azs, hf, wrap)
    eb = [(b, a) for a, b in bounds(sorted(els), vf, False)][::-1]    # (top, bottom) from the top row down
    eb = [(hi, lo) for (hi, lo) in eb]
    a0 = float(geo.get("a0", ab[0][0])); a1 = float(geo.get("a1", ab[-1][1]))
    e_top = float(geo.get("e0", max(x[0] for x in eb))); e_bot = float(geo.get("e1", min(x[1] for x in eb)))
    seam = min(hf / 2.0, 360.0 - (a1 - a0) + hf / 2.0) if wrap else 0.0
    W = max(8, int(round((a1 - a0 + seam) * k))); H = max(8, int(round((e_top - e_bot) * k))) + head + foot
    can = np.full((H, W, 3), 22, np.uint8)
    th_, tv_ = math.tan(math.radians(hf / 2.0)), math.tan(math.radians(vf / 2.0))
    cells = {}
    for p in pos:
        az = (float(p["pan"]) - 50.0) / 50.0 * hp; el = (float(p["tilt"]) - 50.0) / 50.0 * ht
        ci = min(range(len(azs)), key=lambda q: abs(azs[q] - az)); ri = min(range(len(els)), key=lambda q: abs(els[q] - el))
        im = load(p)
        if im is None:
            continue
        ih, iw = im.shape[:2]
        (lo, hi), (top, bot) = ab[ci], eb[ri]
        u0 = int(round((0.5 + math.tan(math.radians(lo - az)) / (2 * th_)) * iw)); u1 = int(round((0.5 + math.tan(math.radians(hi - az)) / (2 * th_)) * iw))
        v0 = int(round((0.5 - math.tan(math.radians(top - el)) / (2 * tv_)) * ih)); v1 = int(round((0.5 - math.tan(math.radians(bot - el)) / (2 * tv_)) * ih))
        u0, u1 = max(0, min(iw - 1, u0)), max(1, min(iw, u1)); v0, v1 = max(0, min(ih - 1, v0)), max(1, min(ih, v1))
        cw = int(round((hi - a0) * k)) - int(round((lo - a0) * k)); chh = int(round((e_top - bot) * k)) - int(round((e_top - top) * k))   # no 1-px gaps
        if u1 - u0 < 2 or v1 - v0 < 2 or cw < 2 or chh < 2:
            continue
        part = cv2.resize(im[v0:v1, u0:u1], (cw, chh), interpolation=cv2.INTER_AREA)
        for off in ((0.0, 360.0) if wrap else (0.0,)):     # wrap: the columns after the seam once more
            x = int(round((lo + off - a0) * k)); y = head + int(round((e_top - top) * k))
            if x >= W or x + cw <= 0 or y >= H:
                continue
            xs, xe = max(0, x), min(W, x + cw); ys, ye = max(0, y), min(H - foot, y + chh)
            if xe > xs and ye > ys:
                can[ys:ye, xs:xe] = part[ys - y:ye - y, xs - x:xe - x]
            if off == 0.0:
                cells[p["i"]] = {"col": ci, "row": ri, "tw": cw, "th": chh, "x0": x, "y0": y, "x1": x + cw, "y1": y + chh}
    if not cells:
        return None, {}
    cells["_geo"] = {"a0": round(a0, 3), "a1": round(a1, 3), "e_top": round(e_top, 3), "e_bot": round(e_bot, 3), "k": round(k, 5), "head": head,
                     "w": W, "h": H, "wrap": wrap, "seam": round(seam, 3), "hf": hf, "vf": vf, "hp": hp, "ht": ht}
    return can, cells


def pano_build(since=None, until=None, label=""):
    """the panorama with the marks; returns (path, marks) or (None, error)"""
    now = time.time()
    until = until or now
    if since is None:
        y = datetime.now() - timedelta(days=1)
        since = y.replace(hour=18, minute=0, second=0, microsecond=0).timestamp()
    reps = _pano_reports(since, until)
    kind = reps[-1].get("ref_kind") if reps else None
    meta = refscan_meta("day") or refscan_meta(kind)       # the day reference is easier to read
    if not meta or not meta.get("positions"):
        return None, "no reference yet - scan first"
    pos = meta["positions"]
    head = 54
    can, cells = pano_canvas(pos, lambda p: cv2.imread(refscan_dir(REFSCAN_KINDS[meta["_kind"]], p["file"])), head=head, foot=30)
    if can is None:
        return None, "no reference yet - scan first"
    H, W = can.shape[:2]
    tiles = {i: (None, c["col"], c["row"]) for i, c in cells.items()}
    tw, th = cells[next(iter(cells))]["tw"], cells[next(iter(cells))]["th"]
    marks = _pano_track(reps)
    fmt = lambda t: datetime.fromtimestamp(t).strftime("%H:%M")
    for m in marks:
        if m["pos"] not in tiles:
            continue
        _im, cx, cy = tiles[m["pos"]]
        x0 = cx * tw + int(m["box"][0] * tw); y0 = head + cy * th + int(m["box"][1] * th)
        x1 = x0 + max(6, int(m["box"][2] * tw)); y1 = y0 + max(6, int(m["box"][3] * th))
        col = PANO_COL.get(m["kind"], (200, 200, 200))
        cv2.rectangle(can, (x0, y0), (x1, y1), col, 3 if m["back"] is None else 1, cv2.LINE_AA)
        txt = {"missing": tr("gone"), "new": tr("new"), "changed": tr("changed")}.get(m["kind"], "")
        txt = (m["name"] + " " if m["name"] else "") + txt + " " + fmt(m["first"]) + (" - " + tr("back") + " " + fmt(m["back"]) if m["back"] else "")
        txt = _ascii(txt)
        (tw_, th_), _b = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        ty = y0 - 4 if y0 - 4 - th_ > head else y1 + th_ + 4
        cv2.rectangle(can, (x0, ty - th_ - 3), (x0 + tw_ + 4, ty + 3), col, -1)
        cv2.putText(can, txt, (x0 + 2, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    # head line and legend
    title = _ascii("%s - %s %s - %s" % (CFG.get("device_name") or "MoveEye", tr("Missing things"), datetime.fromtimestamp(since).strftime("%d.%m. %H:%M"),
                                         datetime.fromtimestamp(until).strftime("%d.%m. %H:%M")))
    cv2.putText(can, title, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA)
    lx = 10
    for k, n in (("missing", tr("gone")), ("new", tr("new")), ("changed", tr("changed"))):
        cv2.rectangle(can, (lx, 34), (lx + 14, 46), PANO_COL[k], -1)
        cv2.putText(can, _ascii(n), (lx + 20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA)
        lx += 110
    foot = _ascii(trf("{n} checks in this time, {m} changes", n=len(reps), m=len(marks)) if reps else tr("no comparison in this time"))
    cv2.putText(can, foot, (10, H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
    os.makedirs(pano_dir(), exist_ok=True)
    name = datetime.fromtimestamp(until).strftime("%Y%m%d_%H%M") + ".jpg"
    path = pano_dir(name)
    cv2.imwrite(path, can, [cv2.IMWRITE_JPEG_QUALITY, 85])
    js = [{"kind": m["kind"], "name": m["name"], "pos": m["pos"], "first": m["first"], "back": m["back"]} for m in marks]
    with open(path[:-4] + ".json", "w", encoding="utf-8") as f:
        json.dump({"since": since, "until": until, "checks": len(reps), "marks": js}, f)
    try:                                                   # keep 14
        fs = sorted(x for x in os.listdir(pano_dir()) if x.endswith(".jpg"))
        for x in fs[:-14]:
            for e in (x, x[:-4] + ".json"):
                try:
                    os.remove(pano_dir(e))
                except OSError:
                    pass
    except OSError:
        pass
    log_event("sys", f"Panorama report: {len(marks)} changes from {len(reps)} checks")
    return path, js


def pano_list():
    out = []
    try:
        for x in sorted((x for x in os.listdir(pano_dir()) if x.endswith(".jpg")), reverse=True)[:14]:
            d = {}
            try:
                with open(pano_dir(x[:-4] + ".json"), encoding="utf-8") as f:
                    d = json.load(f)
            except (OSError, ValueError):
                pass
            out.append({"file": x, "checks": d.get("checks", 0), "marks": d.get("marks", []), "since": d.get("since"), "until": d.get("until")})
    except OSError:
        pass
    return out


def pano_send(path, js):
    w = WATCH_REF.get("w")
    if w is None or not path:
        return
    gone = [m for m in js if m["kind"] == "missing" and not m["back"]]
    new = [m for m in js if m["kind"] == "new" and not m["back"]]
    txt = trf("Missing things: {g} gone, {n} new, {c} changes in all", g=len(gone), n=len(new), c=len(js))
    try:
        with open(path, "rb") as f:
            jpg = f.read()
        if morning_add("🧭 " + txt, jpg):                 # 2.98.1: with the night report (one push in the morning)
            return
        w.notifier.info(txt, title="{name}: " + tr("Missing things"), jpg=jpg, fname="panorama.jpg")
    except Exception:
        pass


def pano_tick():
    """once a morning at the hour of the night report (when switched on)"""
    if not CFG.get("refscan_pano_on") or PANO["busy"]:
        return
    d = datetime.now()
    day = d.strftime("%Y-%m-%d")
    if d.hour < int(CFG.get("report_hour", 7)) or PANO["day"] == day or CFG.get("refscan_pano_day") == day:
        return
    PANO["day"] = day
    CFG["refscan_pano_day"] = day
    save_settings()
    PANO["busy"] = True
    try:
        path, js = pano_build()
        if path:
            pano_send(path, js)
        else:
            PANO["msg"] = js
    finally:
        PANO["busy"] = False


def _pano_loop():
    while True:
        time.sleep(60)
        try:
            pano_tick()
        except Exception as e:
            PANO["msg"] = str(e)[:100]


threading.Thread(target=_pano_loop, daemon=True, name="panorama").start()
