#@ Motion Watch – Teil 430: PDF-Bericht. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Event report (PDF) - a small PDF writer of its own (no extra package): A4 pages, text in Helvetica (WinAnsi, so umlauts
#   work), JPEG pictures embedded as they are.
# ----------------------------------------------------------------------------
class MiniPDF:
    W, H = 595.0, 842.0

    def __init__(self):
        self.pages = []; self.images = []; self.cur = None; self.y = 0.0; self.new_page()

    def new_page(self):
        self.cur = []; self.pages.append(self.cur); self.y = self.H - 50

    @staticmethod
    def _esc(t):
        b = str(t).encode("cp1252", "replace")
        return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")

    def text(self, t, size=10, bold=False, x=50, gap=1.35, color=(0, 0, 0)):
        width = int((self.W - x - 50) / (size * 0.5))           # rough line length for Helvetica
        lines = []
        for para in str(t).split("\n"):
            while len(para) > width:
                cut = para.rfind(" ", 0, width)
                cut = cut if cut > width // 2 else width
                lines.append(para[:cut]); para = para[cut:].lstrip()
            lines.append(para)
        for ln in lines:
            if self.y < 60:
                self.new_page()
            self.cur.append(b"BT %.3f %.3f %.3f rg /%s %d Tf %.1f %.1f Td (" % (color[0], color[1], color[2], b"F2" if bold else b"F1", size, x, self.y)
                            + self._esc(ln) + b") Tj ET")
            self.y -= size * gap

    def space(self, h=8):
        self.y -= h

    def line(self):
        self.cur.append(b"0.75 0.75 0.75 RG 0.6 w 50 %.1f m %.1f %.1f l S" % (self.y + 4, self.W - 50, self.y + 4)); self.y -= 8

    def image(self, jpg, w, h, max_w=495.0, max_h=250.0, caption=""):
        k = min(max_w / w, max_h / h, 1.0 if w > max_w else max_w / w)
        dw, dh = w * k, h * k
        if self.y - dh - (14 if caption else 0) < 50:
            self.new_page()
        if caption:
            self.text(caption, 9, color=(0.35, 0.35, 0.35))
        self.images.append((jpg, w, h)); n = len(self.images)
        self.cur.append(b"q %.1f 0 0 %.1f 50 %.1f cm /Im%d Do Q" % (dw, dh, self.y - dh, n))
        self.y -= dh + 10

    def output(self):
        objs = []                                              # (number, bytes)
        def add(b):
            objs.append(b); return len(objs)
        cat = add(b""); pages_n = add(b"")
        f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        imgs = []
        for jpg, w, h in self.images:
            imgs.append(add(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n" % (w, h, len(jpg))
                            + jpg + b"\nendstream"))
        xo = b" ".join(b"/Im%d %d 0 R" % (i + 1, o) for i, o in enumerate(imgs))
        res = b"<< /Font << /F1 %d 0 R /F2 %d 0 R >> /XObject << %s >> >>" % (f1, f2, xo)
        kids = []
        for i, pg in enumerate(self.pages):
            foot = b"BT 0.5 0.5 0.5 rg /F1 8 Tf 50 30 Td (Motion Watch - %d / %d) Tj ET" % (i + 1, len(self.pages))
            body = b"\n".join(pg + [foot])
            c = add(b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream")
            kids.append(add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 595 842] /Resources %s /Contents %d 0 R >>" % (pages_n, res, c)))
        objs[cat - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_n
        objs[pages_n - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offs = []
        for i, o in enumerate(objs):
            offs.append(len(out)); out += b"%d 0 obj\n" % (i + 1) + o + b"\nendobj\n"
        xref = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % x for x in offs)
        out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, cat, xref)
        return bytes(out)


def _report_jpg(img, width=900):
    h, w = img.shape[:2]
    if w > width:
        img = cv2.resize(img, (width, int(h * width / w)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return (buf.tobytes(), img.shape[1], img.shape[0]) if ok else None


def _report_log(dt, minutes=10):
    """Log lines from minutes before to minutes after the event (today's log and the packed day logs)."""
    import gzip
    a, b = dt - timedelta(minutes=minutes), dt + timedelta(minutes=minutes)
    day = dt.strftime("%Y-%m-%d"); out = []
    files = [LOG_FILE] + sorted(glob.glob(os.path.join(log_dir(), f"motionwatch_{day}*.log.gz")))
    for p in files:
        try:
            op = gzip.open if p.endswith(".gz") else open
            with op(p, "rt", errors="replace") as f:
                for ln in f:
                    try:
                        t = datetime.strptime(ln[:19], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                    if a <= t <= b:
                        out.append(ln.rstrip())
        except OSError:
            continue
    return sorted(set(out))[:120]


def rec_report_pdf(name, lang=None):
    """PDF with what is known about one recording: for the police / the insurance."""
    T = lambda x: tr(x, lang)
    p = rec_path(name)
    if not p:
        return None
    st = os.stat(p); is_video = name.lower().endswith(".mp4")
    meta = rec_meta(name, st, probe=True) if not name.startswith("timelapse/") else {}
    dt = parse_stamp(os.path.basename(name)) or datetime.fromtimestamp(st.st_mtime)
    snap = os.path.splitext(name)[0] + ".jpg" if is_video else None
    if snap and not rec_path(snap):
        snap = None
    gps = rec_gps(os.path.basename(name), meta, os.path.dirname(p), os.path.basename(snap) if snap else None)
    pdf = MiniPDF()
    pdf.text(T("Event report"), 18, bold=True); pdf.space(2)
    pdf.text(((CFG["device_name"] + " · ") if CFG["device_name"] else "") + "Motion Watch " + APP_VERSION, 10, color=(0.35, 0.35, 0.35))
    pdf.line()
    rows = [(T("Date / time"), dt.strftime("%d.%m.%Y %H:%M:%S")), (T("File"), name),
            (T("Kind"), T("Video") if is_video else T("Picture")), (T("Size"), f"{st.st_size / 1e6:.1f} MB")]
    if meta.get("duration") is not None:
        rows.append((T("Duration"), f"{meta['duration']:.0f} s"))
    if meta.get("persons"):
        rows.append((T("Persons seen"), str(meta["persons"])))
    if meta.get("source"):
        rows.append((T("Camera"), str(meta["source"])))
    if meta.get("false"):
        rows.append((T("Marked as"), T("false alarm")))
    if gps:
        rows.append((T("Place"), f"{gps[0]:.5f}, {gps[1]:.5f}"))
        rows.append(("", osm_link(gps[0], gps[1])))
    else:
        rows.append((T("Place"), T("unknown")))
    for k, v in rows:
        pdf.text((k + ": " if k else "    ") + v, 10)
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    pdf.space(4); pdf.text(T("Checksum of the original file (SHA-256) - shows that it was not changed:"), 8, color=(0.35, 0.35, 0.35))
    pdf.text(h.hexdigest(), 8, color=(0.35, 0.35, 0.35))
    pdf.line(); pdf.text(T("Pictures"), 13, bold=True); pdf.space(2)
    pics = []
    if snap or not is_video:
        img = cv2.imread(rec_path(snap) if snap else p)
        if img is not None:
            pics.append((T("Alarm picture"), img))
    if is_video:
        cap = cv2.VideoCapture(p)
        try:
            n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0); fps = cap.get(cv2.CAP_PROP_FPS) or 0
            for frac in ((0.1, 0.5, 0.9) if n > 10 else ()):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * frac)); ok, fr = cap.read()
                if ok and fr is not None:
                    pics.append((T("From the video") + (f" ({int(n * frac / fps)} s)" if fps else ""), fr))
        finally:
            cap.release()
    for cap_, img in pics[:4]:
        j = _report_jpg(img)
        if j:
            pdf.image(*j, caption=cap_)
    if not pics:
        pdf.text(T("no picture"), 10)
    pdf.line(); pdf.text(T("Log around the event (10 minutes before and after)"), 13, bold=True); pdf.space(2)
    lines = _report_log(dt)
    for ln in lines or [T("no entries")]:
        pdf.text(ln, 7.5, gap=1.25)
    pdf.space(6); pdf.text(T("Created") + ": " + datetime.now().strftime("%d.%m.%Y %H:%M") + " · " + T("The original video file is on the device (recordings)."), 8, color=(0.35, 0.35, 0.35))
    return pdf.output()


def rec_path(name):
    """Absolute path of a file in the recordings folder, or None (guards against path tricks like ../).
    "timelapse/<file>" = a timelapse photo or video (shown in the recordings list too)."""
    if isinstance(name, str) and name.startswith("timelapse/"):
        return tl_path(name[10:])
    if isinstance(name, str) and LOOP_RE.match(name):
        p = os.path.join(rec_dir(), name)
        return p if os.path.isfile(p) else None
    if not isinstance(name, str) or not REC_NAME_RE.match(name) or ".." in name:
        return None
    p = os.path.join(rec_dir(), name)
    return p if os.path.isfile(p) else None


def parse_stamp(name):
    m = _STAMP_RE.search(name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _read_sidecar(name):
    try:
        with open(os.path.join(rec_dir(), os.path.splitext(name)[0] + ".json")) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def rec_meta(name, st, probe=False):
    """Info about a video: the info file, completed by looking into the file itself (codec, duration) when asked."""
    e = _REC_META.get(name)
    if e is None or e[0] != st.st_mtime or e[1] != st.st_size:
        e = _REC_META[name] = [st.st_mtime, st.st_size, _read_sidecar(name), False]
        if len(_REC_META) > 5000:                           # keep the cache small
            for k in list(_REC_META)[:1000]:
                _REC_META.pop(k, None)
    meta = e[2]
    if probe and not e[3] and not (meta.get("codec") and meta.get("duration") is not None):
        e[3] = True
        cap = None
        try:
            cap = cv2.VideoCapture(os.path.join(rec_dir(), name))
            if cap.isOpened():
                v = int(cap.get(cv2.CAP_PROP_FOURCC))
                fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
                meta.setdefault("codec", "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4)).strip().lower())
                if meta.get("duration") is None and fps > 0 and frames > 0:
                    meta["duration"] = round(frames / fps, 1)
        except Exception:
            pass
        finally:
            if cap is not None:
                cap.release()
    return meta


def _parse_day(s):
    try:
        return datetime.strptime(str(s), "%Y-%m-%d")
    except ValueError:
        return None


def list_recordings(args, watch=None):
    """Filtered, sorted, paged list of recordings. Filters: kind, from, to, schedule, source, q, sort, offset, limit."""
    d = rec_dir()
    try:
        names = os.listdir(d)
    except OSError:
        names = []
    files, total_bytes = {}, 0
    for n in names:
        if n.startswith(".") or not REC_NAME_RE.match(n):
            continue
        stem, ext = os.path.splitext(n)
        try:
            st = os.stat(os.path.join(d, n))
        except OSError:
            continue
        total_bytes += st.st_size
        kind = REC_EXTS.get(ext.lower())
        if kind:
            files.setdefault(stem, {})[kind] = (n, st)
    with LOCK:
        plans = [dict(s) for s in SCHEDULES]
    live = watch.rec_name if watch is not None else ""
    live_set = {n for n in LIVE_RECS if not n.startswith("loop/")} | ({live} if live else set())

    items = []
    for stem, kinds in files.items():
        if "video" in kinds:
            n, st = kinds["video"]; kind = "video"; snap = kinds.get("image")
        else:
            n, st = kinds["image"]; kind = "image"; snap = None
        dt = parse_stamp(n) or datetime.fromtimestamp(st.st_mtime)
        meta = rec_meta(n, st)
        items.append({"n": n, "st": st, "kind": kind, "dt": dt, "meta": meta, "snap": snap[0] if snap else None,
                      "sched": [i for i, s in enumerate(plans) if schedule_window_contains(s, dt)],
                      "gps": rec_gps(n, meta, d, snap[0] if snap else None)})
    # timelapse: the videos always, the single photos only with the filter "Timelapse"
    kind_req = args.get("kind", "")
    if kind_req in ("", "timelapse", "video"):
        try:
            tl_names = os.listdir(tl_dir())
        except OSError:
            tl_names = []
        for n in tl_names:
            is_v = bool(TL_VIDEO_RE.match(n))
            if not is_v and not (kind_req == "timelapse" and TL_PHOTO_RE.match(n)):
                continue
            try:
                st = os.stat(os.path.join(tl_dir(), n))
            except OSError:
                continue
            name = "timelapse/" + n
            dt = parse_stamp(n) or datetime.fromtimestamp(st.st_mtime)
            meta = dict(rec_meta(name, st)); meta.setdefault("source", "Timelapse")
            items.append({"n": name, "st": st, "kind": "video" if is_v else "image", "dt": dt, "meta": meta, "snap": None,
                          "sched": [], "tl": True, "gps": rec_gps(n, meta, tl_dir()) if not is_v else None})

    # filters that do not depend on the schedule
    kind_f, src_f, q = args.get("kind", ""), args.get("source", ""), (args.get("q", "") or "").strip().lower()
    d_from, d_to = _parse_day(args.get("from", "")), _parse_day(args.get("to", ""))
    sources = sorted({it["meta"].get("source") for it in items if it["meta"].get("source")})
    places = places_assign(items)
    no_place = sum(1 for it in items if not it.get("gps"))
    if kind_f in ("video", "image"):
        items = [it for it in items if it["kind"] == kind_f]
    elif kind_f == "timelapse":
        items = [it for it in items if it.get("tl")]
    if d_from:
        items = [it for it in items if it["dt"] >= d_from]
    if d_to:
        items = [it for it in items if it["dt"] < d_to.replace(hour=0) + timedelta(days=1)]
    if src_f:
        items = [it for it in items if it["meta"].get("source") == src_f]
    if q:
        items = [it for it in items if q in it["n"].lower()]
    pl_f = args.get("place", "")
    if pl_f == "none":
        items = [it for it in items if not it.get("gps")]
    elif pl_f:
        items = [it for it in items if it.get("place") == pl_f]

    if args.get("fa") == "1":
        items = [it for it in items if it["meta"].get("false")]
    if args.get("fav") == "1":
        items = [it for it in items if it["meta"].get("fav")]
    counts = {"all": len(items), "any": sum(1 for it in items if it["sched"]), "none": sum(1 for it in items if not it["sched"])}
    for i in range(len(plans)):
        counts[str(i)] = sum(1 for it in items if i in it["sched"])
    sch_f = args.get("schedule", "")
    if sch_f == "any":
        items = [it for it in items if it["sched"]]
    elif sch_f == "none":
        items = [it for it in items if not it["sched"]]
    elif sch_f.isdigit():
        items = [it for it in items if int(sch_f) in it["sched"]]

    sort = args.get("sort", "new")
    if sort == "old":
        items.sort(key=lambda it: it["dt"])
    elif sort == "size":
        items.sort(key=lambda it: it["st"].st_size, reverse=True)
    else:
        items.sort(key=lambda it: it["dt"], reverse=True)

    try:
        offset = max(0, int(args.get("offset", 0))); limit = max(1, min(200, int(args.get("limit", 48))))
    except (TypeError, ValueError):
        offset, limit = 0, 48
    page = []
    for it in items[offset:offset + limit]:
        meta = rec_meta(it["n"], it["st"], probe=True) if it["kind"] == "video" else it["meta"]
        codec = (meta.get("codec") or "").lower()
        page.append({"name": it["n"], "kind": it["kind"], "time": it["dt"].strftime("%Y-%m-%d %H:%M:%S"),
                     "size": it["st"].st_size, "duration": meta.get("duration"), "source": meta.get("source"),
                     "persons": meta.get("persons"), "schedules": [plans[i]["name"] for i in it["sched"]],
                     "playable": (codec in BROWSER_CODECS) if codec else None, "snap": it["snap"], "fav": bool(meta.get("fav")),
                     "recording": it["n"] in live_set, "timelapse": bool(it.get("tl")), "gps": it.get("gps"), "place": it.get("place"),
                     "false": it["meta"].get("false")})
    now = datetime.now()
    points = None
    if args.get("map") == "1":                      # every filtered recording with a location (for the map)
        points = [{"name": it["n"], "kind": it["kind"], "time": it["dt"].strftime("%Y-%m-%d %H:%M:%S"), "size": it["st"].st_size,
                   "lat": it["gps"][0], "lon": it["gps"][1], "place": it.get("place"), "source": it["meta"].get("source"),
                   "duration": it["meta"].get("duration"), "fav": bool(it["meta"].get("fav")), "timelapse": bool(it.get("tl")),
                   "schedules": [plans[i]["name"] for i in it["sched"]], "persons": it["meta"].get("persons"), "snap": it["snap"],
                   "recording": it["n"] in live_set}
                  for it in items if it.get("gps")][:3000]
    return {"total": len(items), "items": page, "counts": counts, "sources": sources, "recording": bool(live_set),
            "places": places, "no_place": no_place, "points": points, "map_online": bool(CFG["map_online"]),
            "schedules": [{"index": i, "name": s["name"], "enabled": s["enabled"], "days": s["days"], "start": s["start"],
                           "end": s["end"], "active_now": schedule_active(s, now), "count": counts.get(str(i), 0)}
                          for i, s in enumerate(plans)],
            "disk": {"files": len(files), "mb": int(total_bytes / 1024 ** 2), "limit_gb": CFG["record_max_gb"]},
            "ffmpeg": shutil.which("ffmpeg") is not None}


def _write_sidecar(name, meta):
    stem = os.path.splitext(name)[0]
    p = os.path.join(rec_dir(), stem + ".json")
    tmp = p + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(meta, f)
        os.replace(tmp, p)
    except OSError:
        return False
    for k in (stem + ".mp4", stem + ".jpg"):
        _REC_META.pop(k, None)
    return True


FA_CAUSES = ("animal", "wind", "light", "rain", "car", "other")


def rec_set_false(names, cause, watch=None):
    """Mark recordings as false alarm (cause) or as real again (cause empty)."""
    n = 0
    for name in (names if isinstance(names, list) else [])[:500]:
        if not rec_path(name) or name.lower().endswith(".json") or name.startswith("timelapse/") or _is_live(name, watch):
            continue
        meta = _read_sidecar(name)
        if cause in FA_CAUSES:
            meta["false"] = cause; meta["false_t"] = int(time.time())
        else:
            meta.pop("false", None); meta.pop("false_t", None)
        if _write_sidecar(name, meta):
            n += 1
    if n:
        log_event("rec", f"{n} recording(s) marked as " + (f"false alarm ({cause})" if cause in FA_CAUSES else "real"))
    return n


def fa_suggestions(lang=None, days=14):
    """Look at the recordings marked «was nothing» and suggest settings that would have avoided them."""
    L = norm_lang(lang) if lang else cur_lang()
    since = datetime.now() - timedelta(days=days)
    total, causes = 0, {}
    d = rec_dir()
    try:
        names = os.listdir(d)
    except OSError:
        names = []
    stems = {}
    for n in names:
        st_, ext = os.path.splitext(n)
        if ext.lower() in (".mp4", ".jpg") and REC_NAME_RE.match(n):
            stems.setdefault(st_, n if ext.lower() == ".mp4" else stems.get(st_, n))
    for st_, n in stems.items():
        dt = parse_stamp(n)
        if dt is None or dt < since:
            continue
        total += 1
        c = _read_sidecar(n).get("false")
        if c in FA_CAUSES:
            causes[c] = causes.get(c, 0) + 1
    nf = sum(causes.values())
    out = []

    def sug(sid, text, changes, n):
        ch = {k: v for k, v in changes.items() if k in CFG and CFG[k] != v}
        if ch:
            out.append({"id": sid, "text": tr(text, L), "n": n, "changes": ch})

    if causes.get("animal", 0) >= 2:
        sug("animal", "Alarm only when the AI confirms a person (animals no longer count)", {"ai_enabled": True, "ai_require": True}, causes["animal"])
    if causes.get("wind", 0) >= 2:
        if not CFG["wind_auto"]:
            sug("wind", "Switch on the automatic wind detection", {"wind_auto": True}, causes["wind"])
        else:
            sug("wind", "Ignore small movements (branches, grass): bigger minimum size", {"min_area": round(min(8000, CFG["min_area"] * 1.3))}, causes["wind"])
    if causes.get("light", 0) >= 2:
        if not CFG["shadow_filter"] or not CFG["lowlight_auto"]:
            sug("light", "Switch on the shadow filter and the low-light automatic", {"shadow_filter": True, "lowlight_auto": True}, causes["light"])
        else:
            sug("light", "Less sensitive to light changes", {"sensitivity": max(10, CFG["sensitivity"] - 10)}, causes["light"])
    if causes.get("rain", 0) >= 2:
        if not CFG["rain_auto"]:
            sug("rain", "Switch on the automatic rain detection", {"rain_auto": True}, causes["rain"])
        else:
            sug("rain", "Detect rain earlier", {"rain_threshold": round(max(0.15, CFG["rain_threshold"] - 0.05), 2)}, causes["rain"])
    if causes.get("car", 0) >= 2:
        if not CFG["car_filter"]:
            sug("car", "Switch on the vehicle filter", {"car_filter": True}, causes["car"])
        else:
            out.append({"id": "zones", "text": tr("Draw an ignore zone over the road (tab Zones)", L), "n": causes["car"], "changes": {}, "link": "/zones"})
    if nf >= 5 and nf >= 0.4 * max(1, total) and not out:
        sug("sens", "Somewhat less sensitive overall", {"sensitivity": max(10, CFG["sensitivity"] - 10)}, nf)
    return {"days": days, "total": total, "false": nf, "causes": causes, "suggestions": out}


def fa_apply(sid, lang=None):
    for x in fa_suggestions(lang)["suggestions"]:
        if x["id"] == sid and x["changes"]:
            for k, v in x["changes"].items():
                CFG[k] = v; sched_user_changed(k)
            save_settings()
            log_event("sys", "False alarms: settings taken over - " + ", ".join(f"{k}={v}" for k, v in x["changes"].items()))
            return True
    return False


def rec_set_fav(names, value, watch=None):
    """Star / un-star recordings. Starred recordings are never removed by the automatic cleanup."""
    n = 0
    for name in (names if isinstance(names, list) else [])[:500]:
        if rec_path(name) and not name.lower().endswith(".json") and _is_live(name, watch):
            def later(nm=name):                          # 2.95.34: still being written - star it when it is finished
                for _ in range(80):
                    time.sleep(15)
                    if not _is_live(nm, watch):
                        rec_set_fav([nm], value, watch); return
            threading.Thread(target=later, daemon=True).start()
            n += 1
            continue
        if not rec_path(name) or name.lower().endswith(".json"):
            continue
        meta = _read_sidecar(name)
        if value:
            meta["fav"] = True
        else:
            meta.pop("fav", None)
        if _write_sidecar(name, meta):
            n += 1
    return n


def rec_clean_tmp():
    tdir = os.path.join(rec_dir(), ".tmp")
    try:
        for f in os.listdir(tdir):
            p = os.path.join(tdir, f)
            if time.time() - os.path.getmtime(p) > 3600:
                os.remove(p)
    except OSError:
        pass


_ZIP_LOCK = threading.Lock()


def rec_zip(names, watch=None):
    """Pack recordings (video + snapshot) into one ZIP in the temp folder. Returns the path or None.
    2.95.34: one at a time, only when there is room for it (+ 500 MB), nothing left behind after an error."""
    if not _ZIP_LOCK.acquire(blocking=False):
        return None
    tmp = None
    try:
        files, seen = [], set()
        for name in (names if isinstance(names, list) else [])[:300]:
            if not rec_path(name) or _is_live(name, watch):
                continue
            stem, ext = os.path.splitext(name)
            for e in ((".mp4", ".jpg") if ext.lower() == ".mp4" else (ext.lower(),)):
                p = os.path.join(rec_dir(), stem + e)
                if os.path.isfile(p) and p not in seen:
                    seen.add(p); files.append(p)
        if not files:
            return None
        need = sum(os.path.getsize(p) for p in files) + 500 * (1 << 20)
        if shutil.disk_usage(rec_dir()).free < need:
            log_event("rec", "ZIP download refused: not enough free space on the drive")
            return None
        tdir = os.path.join(rec_dir(), ".tmp")
        os.makedirs(tdir, exist_ok=True)
        fd, tmp = tempfile.mkstemp(suffix=".zip", dir=tdir); os.close(fd)
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
            for p in files:
                z.write(p, os.path.basename(p))
        return tmp
    except Exception as e:
        log_event("rec", f"ZIP failed: {e}"[:160])
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass
        return None
    finally:
        _ZIP_LOCK.release()


def _scan_events():
    """[(datetime, name, kind)] - one entry per recorded event (the video if there is one, else the picture)."""
    d = rec_dir()
    try:
        names = os.listdir(d)
    except OSError:
        return []
    files = {}
    for n in names:
        if n.startswith(".") or not REC_NAME_RE.match(n):
            continue
        stem, ext = os.path.splitext(n)
        kind = REC_EXTS.get(ext.lower())
        if kind:
            files.setdefault(stem, {})[kind] = n
    out = []
    for stem, k in files.items():
        n = k.get("video") or k["image"]
        dt = parse_stamp(n)
        if dt is None:
            try:
                dt = datetime.fromtimestamp(os.path.getmtime(os.path.join(d, n)))
            except OSError:
                continue
        out.append((dt, n, "video" if "video" in k else "image"))
    return out


_STATS = {"t": 0.0, "key": None, "val": None}


def rec_stats(days=14, day=None):
    """Events per day / hour for the statistics card of the preview page + the events of one day for the timeline."""
    try:
        days = max(1, min(90, int(days)))
    except (TypeError, ValueError):
        days = 14
    key = (days, day, len(os.listdir(rec_dir())) if os.path.isdir(rec_dir()) else 0)
    if _STATS["key"] == key and time.time() - _STATS["t"] < 10:
        return _STATS["val"]
    events = _scan_events()
    today = datetime.now().date(); start = today - timedelta(days=days - 1)
    per_day, heat = {}, [[0] * 24 for _ in range(7)]
    for dt, name, kind in events:
        dd = dt.date()
        if start <= dd <= today:
            per_day.setdefault(dd, [0] * 24)[dt.hour] += 1
            heat[dt.weekday()][dt.hour] += 1
    lst = []
    for i in range(days):
        dd = start + timedelta(days=i); hrs = per_day.get(dd, [0] * 24)
        lst.append({"date": dd.isoformat(), "hours": hrs, "count": sum(hrs)})
    ev = []
    dd = _parse_day(day) if day else None
    if dd:
        ev = sorted(({"m": dt.hour * 60 + dt.minute, "t": dt.strftime("%H:%M:%S"), "name": n, "kind": k}
                     for dt, n, k in events if dt.date() == dd.date()), key=lambda e: e["m"])
    val = {"days": lst, "heat": heat, "events": ev, "day": day, "total": len(events)}
    _STATS.update(t=time.time(), key=key, val=val)
    return val


def rec_thumb(name):
    """Path of a small cached JPEG thumbnail (320 px wide) for a video or snapshot, or None."""
    path = rec_path(name)
    if not path:
        return None
    tdir = os.path.join(rec_dir(), ".thumbs")
    tp = os.path.join(tdir, name + ".jpg")
    try:
        if os.path.isfile(tp) and os.path.getmtime(tp) >= os.path.getmtime(path):
            return tp
        os.makedirs(os.path.dirname(tp), exist_ok=True)
        img = None
        if name.lower().endswith(".jpg"):
            img = cv2.imread(path)
        else:
            snap = path[:-4] + ".jpg"                          # the snapshot of the same event is the cheapest thumbnail
            if os.path.isfile(snap):
                img = cv2.imread(snap)
            if img is None:
                cap = cv2.VideoCapture(path)
                try:
                    ok, img = cap.read()
                    img = img if ok else None
                finally:
                    cap.release()
        if img is None:
            return None
        h, w = img.shape[:2]
        img = cv2.resize(img, (320, max(1, int(h * 320 / w))), interpolation=cv2.INTER_AREA)
        cv2.imwrite(tp, img, [cv2.IMWRITE_JPEG_QUALITY, 72])
        return tp
    except Exception:
        return None


def _cache_path(name):
    return os.path.join(rec_dir(), ".cache", os.path.splitext(name)[0] + ".h264.mp4")


def _transcode(name, src, dst):
    tmp = dst + ".part.mp4"
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        cmd = (["nice", "-n", "10"] if shutil.which("nice") else []) + [
            "ffmpeg", "-y", "-loglevel", "error", "-i", src, "-c:a", "aac", "-b:a", "64k", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp]
        with _TRANSCODE_SEM:
            r = subprocess.run(cmd, capture_output=True, timeout=1800)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode(errors="replace").strip()[-200:] or f"ffmpeg exit {r.returncode}")
        os.replace(tmp, dst)
        _TRANSCODE[name] = "done"
    except Exception as e:
        _TRANSCODE[name] = f"error: {e}"
        try:
            os.remove(tmp)
        except OSError:
            pass


def rec_play_state(name, watch=None):
    """What the browser can play for this video: ready (url) / converting / unsupported / error / missing."""
    path = rec_path(name)
    if not path or not name.lower().endswith(".mp4"):
        return {"state": "missing"}
    if _is_live(name, watch):
        return {"state": "live"}                                # still being written, the file is not complete yet
    try:
        meta = rec_meta(name, os.stat(path), probe=True)
    except OSError:
        return {"state": "missing"}
    if (meta.get("codec") or "").lower() in BROWSER_CODECS:
        return {"state": "ready", "url": "/rec/file/" + name}
    dst = _cache_path(name)
    if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(path):
        return {"state": "ready", "url": "/rec/play/" + name}
    if shutil.which("ffmpeg") is None:
        return {"state": "unsupported", "url": "/rec/file/" + name + "?dl=1"}
    with _TRANSCODE_LOCK:
        cur = _TRANSCODE.get(name, "")
        if cur == "running":
            return {"state": "converting"}
        if cur.startswith("error"):
            _TRANSCODE.pop(name, None)
            return {"state": "error", "error": cur[7:]}
        _TRANSCODE[name] = "running"
    threading.Thread(target=_transcode, args=(name, path, dst), daemon=True).start()
    return {"state": "converting"}


def rec_purge_extras(stem):
    """Remove cached thumbnails / converted copies that belong to a recording."""
    for p in (os.path.join(rec_dir(), ".thumbs", stem + ".mp4.jpg"), os.path.join(rec_dir(), ".thumbs", stem + ".jpg.jpg"),
              os.path.join(rec_dir(), ".cache", stem + ".h264.mp4"), os.path.join(rec_dir(), ".cache", stem + ".nogps.mp4"),
              os.path.join(rec_dir(), ".cache", stem + ".share.mp4"), os.path.join(rec_dir(), ".cache", stem + ".share.gps.mp4")):
        try:
            os.remove(p)
        except OSError:
            pass
    for k in (stem + ".mp4", stem + ".jpg"):
        _REC_META.pop(k, None); _TRANSCODE.pop(k, None)


def rec_delete(names, watch=None):
    """Delete recordings (video + snapshot + info file of each). Returns how many were deleted."""
    n_ok = 0
    for name in (names if isinstance(names, list) else [])[:500]:
        path = rec_path(name)
        if not path or _is_live(name, watch) or os.path.splitext(name)[1].lower() not in (".mp4", ".jpg"):
            continue
        stem = os.path.splitext(name)[0]
        for ext in ((".mp4", ".jpg", ".json") if name.lower().endswith(".mp4") else (os.path.splitext(name)[1].lower(),)):
            try:
                os.remove(os.path.join(rec_dir(), stem + ext))
            except OSError:
                pass
        rec_purge_extras(stem)
        n_ok += 1
    if n_ok:
        log_event("rec", f"{n_ok} recording(s) deleted from the preview page")
    return n_ok


