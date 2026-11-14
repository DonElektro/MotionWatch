#@ MoveEye – Teil 639zzzz: «⏪ Zeitfenster» im Live-Bild – Damals / Jetzt pro Blickrichtung mit Trennbalken, Änderungen markieren, «wann hat sich das geändert?» (binäre Suche) mit Sprung in die Zeitleiste, tägliches Ausdünnen mit Obergrenze. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (14.11.2026, alle drei Stufen freigegeben, höchstens 5 GB, nur Administrator):
#   Stufe 1 – Bilder sammeln OHNE zusätzliche Kopfbewegung: der Zeitraffer-Fotograf (220) meldet jedes Foto mit seiner Kopf-Richtung,
#     an jedem Halt der Runde (160 / 162) ein Bild (pro Richtung höchstens alle ZF_STOP_GAP s) und einmal pro Stunde, solange der Kopf
#     still steht (Schalter zf_hourly). Gespeichert klein (ZF_W px, JPEG ZF_Q) unter <Aufnahmen>/zeitfenster/JJJJMMTT/zf_*.jpg, dazu
#     pro Tag ein Index idx_JJJJMMTT.jsonl (eine Zeile pro Bild: Zeit, Schwenk / Neigung in Grad, Kamera, Quelle) – nur angehängt,
#     ausser beim Ausdünnen. Eine Richtung = Schwenk und Neigung je höchstens ±ZF_TOL°. Das Bild kommt aus der Kamera-Schleife (410) vor
#     Rahmen und Wärmebild, Privatsphäre-Zonen schon schwarz; während Alarm / Person / Aufnahme / Folgen wird nichts gesammelt.
#     Live: Knopf «⏪» (nur Administrator) → Leiste unter dem Bild: Schieber mit Halten «1 h · gestern · 1 Woche · 1 Monat · 1 Jahr» und
#     freiem Ziehen; gezeigt wird das nächste Bild der JETZIGEN Kopf-Richtung, links «damals», rechts «jetzt» (Trennbalken ziehen).
#   Stufe 2 – Änderungen: Vergleich klein (ZF_SMALL px), grau, Helligkeit angeglichen (Mittel / Streuung), um die Kopf-Abweichung
#     verschoben (Phasenkorrelation); Bezug möglichst von derselben Tageszeit ±1 h. Rahmen um geänderte Bereiche; ein Band oben
#     (Himmel / Bäume, zf_mask_top %) zählt nicht. Nur auf Wunsch gerechnet, zwischengespeichert, immer nur einer zugleich.
#   Stufe 3 – Antippen eines Rahmens: binäre Suche über die Bilder dieser Richtung, wann sich der Bereich geändert hat; Sprung in die
#     Zeitleiste (425) bzw. zu Aufnahmen in diesem Zeitraum. Ausdünnen täglich (Faden mit tiefer Priorität): letzte 24 h alles, bis 7 Tage
#     1 pro Stunde und Richtung, älter 1 pro Tag und Richtung; dann höchstens zf_max_gb (älteste zuerst). Zeitraffer-Fotos und
#     Aufnahmen werden nie angefasst (eigener Ordner, eigene Namen).
#   Fenster (Tk): Karte «Zeitfenster» in den Einstellungen mit «⏪ Damals ansehen» (einfaches Fenster mit Schieber).
# Tests: werkzeuge/zeitfenster_test.py.
# ----------------------------------------------------------------------------
ZF_W, ZF_Q = 960, 70              # stored stills: width px, JPEG quality
ZF_TOL = 3.0                      # one direction: pan and tilt each within ±3°
ZF_STOP_SETTLE = 2.5              # s on a stop of the round before the still (picture calm)
ZF_STOP_GAP = 600.0               # s: at most one still per direction from the round
ZF_STILL_S = 60.0                 # s the head must stand still before the hourly still
ZF_HOUR = 3600.0
ZF_SMALL = 192                    # px: width of the comparison
ZF_THR = 24.0                     # grey levels (small, blurred picture) = a change
ZF_SECTION = "Window to the past"
ZF_NO_PIC = "No picture from back then for this direction yet. MoveEye collects one at every stop of the round, with every timelapse photo and every hour while the head stands still."
ZF_FILE_RE = re.compile(r"^(\d{8})/zf_\d{6}_\d{3}\.jpg$")
ZF_IDX_RE = re.compile(r"^idx_(\d{8})\.jsonl$")
ZF = {"items": None, "lock": threading.Lock(), "calc": threading.Lock(), "chk": 0.0, "last": {}, "want": 0.0, "live": None,
      "ev": threading.Event(), "cache": {}, "thin": None, "saving": False}
for _k, _v in {"zf_on": True, "zf_max_gb": 5.0, "zf_hourly": True, "zf_mask_top": 0.0}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update({"zf_on", "zf_max_gb", "zf_hourly", "zf_mask_top"})        # admin only (Besitzer)


def zf_dir():
    return os.path.join(os.path.abspath(CFG["record_dir"]), "zeitfenster")


def zf_path(f):
    """absolute path of a still (guards against path tricks) or None"""
    if not isinstance(f, str) or not ZF_FILE_RE.match(f):
        return None
    p = os.path.join(zf_dir(), f)
    return p if os.path.isfile(p) else None


def zf_items():
    """all stills [t, pan°, tilt°, file, source, bytes, cam] sorted by time (index loaded once, then kept in memory)"""
    with ZF["lock"]:
        if ZF["items"] is None:
            out = []
            try:
                names = sorted(n for n in os.listdir(zf_dir()) if ZF_IDX_RE.match(n))
            except OSError:
                names = []
            for n in names:
                try:
                    with open(os.path.join(zf_dir(), n), encoding="utf-8") as fh:
                        for line in fh:
                            try:
                                d = json.loads(line)
                                if ZF_FILE_RE.match(d["f"]):
                                    out.append([float(d["t"]), float(d["p"]), float(d["q"]), d["f"], str(d.get("s", "")),
                                                int(d.get("n", 0)), str(d.get("c", "head"))])
                            except (ValueError, KeyError, TypeError):
                                continue
                except OSError:
                    continue
            out.sort(key=lambda it: it[0])
            ZF["items"] = out
        return ZF["items"]


def zf_same_dir(it, p, q, cam="head", tol=ZF_TOL):
    return it[6] == cam and abs((it[1] - p + 180.0) % 360.0 - 180.0) <= tol and abs(it[2] - q) <= tol


def zf_dir_items(p, q, cam="head"):
    return [it for it in zf_items() if zf_same_dir(it, p, q, cam)]


def zf_nearest(items, t):
    return min(items, key=lambda it: abs(it[0] - t)) if items else None


def zf_save(img, pose, src, t=None, extra=None):
    """store one small still with its direction (called in a thread) -> the index row or None"""
    t = time.time() if t is None else t
    try:
        h, w = img.shape[:2]
        if w > ZF_W:
            img = cv2.resize(img, (ZF_W, max(1, int(round(h * ZF_W / w)))), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, ZF_Q])
        if not ok:
            return None
        while True:
            lt = time.localtime(t)
            day = time.strftime("%Y%m%d", lt)
            f = day + "/zf_" + time.strftime("%H%M%S", lt) + "_%03d.jpg" % (int(t * 1000) % 1000)
            if not os.path.exists(os.path.join(zf_dir(), f)):
                break
            t += 0.001
        os.makedirs(os.path.join(zf_dir(), day), exist_ok=True)
        with open(os.path.join(zf_dir(), f), "wb") as fh:
            fh.write(buf.tobytes())
        row = {"t": round(t, 2), "p": round(pose[0], 2), "q": round(pose[1], 2), "f": f, "s": src, "n": len(buf), "c": "head"}
        row.update(extra or {})
        with ZF["lock"]:
            with open(os.path.join(zf_dir(), "idx_" + day + ".jsonl"), "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            if ZF["items"] is not None:
                ZF["items"].append([row["t"], row["p"], row["q"], f, src, row["n"], "head"])
                if len(ZF["items"]) > 1 and ZF["items"][-2][0] > row["t"]:
                    ZF["items"].sort(key=lambda it: it[0])
        return row
    except (OSError, cv2.error, ValueError) as e:
        log_event("sys", f"Window to the past: still not saved: {e}"[:160])
        return None


def zf_save_bg(frame, pose, src, extra=None):
    if ZF["saving"]:
        return
    ZF["saving"] = True
    h, w = frame.shape[:2]
    small = cv2.resize(frame, (ZF_W, max(1, int(round(h * ZF_W / w)))), interpolation=cv2.INTER_AREA) if w > ZF_W else frame.copy()

    def work():
        try:
            zf_save(small, pose, src, extra=extra)
        finally:
            ZF["saving"] = False
    threading.Thread(target=work, daemon=True, name="zf-save").start()


def zf_feed(frame, alarm):
    """every camera frame (the clean picture, 410 via Timelapse.update): never moves the head - only looks whether a still is due"""
    now = time.time()
    if ZF["want"] > now and frame is not None:                    # a comparison waits for the live picture
        h, w = frame.shape[:2]
        ZF["live"] = (now, cv2.resize(frame, (ZF_W, max(1, int(round(h * ZF_W / w)))), interpolation=cv2.INTER_AREA) if w > ZF_W
                      else frame.copy(), servo_pos_deg())
        ZF["want"] = 0.0; ZF["ev"].set()
    if not CFG.get("zf_on") or now - ZF["chk"] < 1.0 or frame is None:
        return
    ZF["chk"] = now
    if ZF["thin"] is None:
        ZF["thin"] = threading.Thread(target=zf_thin_loop, daemon=True, name="zf-thin"); ZF["thin"].start()
    if alarm or STATE.get("tracking") or not servo_arrived():
        return
    still = now - float(SRV.get("arrive_t") or 0.0)
    pose = servo_pos_deg()
    key = "%.0f/%.0f" % (pose[0] / ZF_TOL, pose[1] / ZF_TOL)
    if KOPF.get("round_on") and not STATE.get("patrol_moving") and still >= ZF_STOP_SETTLE:
        src, gap = "stop", ZF_STOP_GAP
    elif CFG.get("zf_hourly") and still >= ZF_STILL_S:
        src, gap = "hour", ZF_HOUR
    else:
        return
    if now - ZF["last"].get(key, 0.0) < gap:
        return
    near = [it for it in zf_items()[-400:] if zf_same_dir(it, pose[0], pose[1])]
    if near and now - near[-1][0] < gap:
        ZF["last"][key] = near[-1][0]
        return
    ZF["last"][key] = now
    zf_save_bg(frame, pose, src)


# the camera loop gives every frame to the timelapse (220): there the Zeitfenster looks too, and every timelapse photo gets its direction
_zf_tl_update_base = Timelapse.update
_zf_tl_shoot_base = Timelapse._shoot


def _zf_tl_update(self, frame, alarm):
    _zf_tl_update_base(self, frame, alarm)
    try:
        zf_feed(frame, alarm)
    except Exception as e:
        log_event("sys", f"Window to the past: {e}"[:160])


def _zf_tl_shoot(self, frame, now):
    before = STATE.get("timelapse_last")
    pose = servo_pos_deg()
    _zf_tl_shoot_base(self, frame, now)
    if CFG.get("zf_on") and STATE.get("timelapse_last") and STATE.get("timelapse_last") != before:
        zf_save_bg(frame, pose, "tl", {"tl": STATE["timelapse_last"]})


# wraps: Timelapse.update
Timelapse.update = _zf_tl_update
# wraps: Timelapse._shoot
Timelapse._shoot = _zf_tl_shoot


# ---- compare (stage 2) --------------------------------------------------------------------------------------------------------------
def zf_load(f):
    p = zf_path(f)
    return cv2.imread(p) if p else None


def zf_small(img, w=ZF_SMALL):
    """small, blurred, float: the 3 colour channels (a red box on green grass has the same grey) - a grey picture stays grey"""
    h0, w0 = img.shape[:2]
    g = cv2.resize(img, (w, max(8, int(round(h0 * w / w0)))), interpolation=cv2.INTER_AREA)
    g = cv2.GaussianBlur(g, (5, 5), 0).astype(np.float32)
    return g if g.ndim == 3 else g[:, :, None]


def zf_compare(old, new, top=0.0, guess=(0.0, 0.0)):
    """where the picture changed: old / new BGR -> {"boxes": [[x, y, w, h, score] 0..1], "mask": bool array (new size), "shift", "light"}.
    Grey and colour channels, global light (one gain per channel) taken out, the old picture moved onto the new one
    (head ±3°, phase correlation of the grey pictures), a band at the top ignored."""
    a, b = zf_small(old), zf_small(new)
    H, W = b.shape[:2]
    if a.shape[:2] != b.shape[:2]:
        a = cv2.resize(a, (W, H), interpolation=cv2.INTER_AREA).reshape(H, W, -1)
    if a.shape[2] != b.shape[2]:
        a, b = a.mean(axis=2, keepdims=True), b.mean(axis=2, keepdims=True)
    ga, gb = a.mean(axis=2), b.mean(axis=2)
    dx, dy = float(guess[0]) * W, float(guess[1]) * H
    try:
        (px, py), resp = cv2.phaseCorrelate(ga.copy(), gb.copy(), cv2.createHanningWindow((W, H), cv2.CV_32F))   # it writes into its inputs
        if resp > 0.08 and abs(px) < 0.12 * W and abs(py) < 0.12 * H:
            dx, dy = px, py
    except cv2.error:
        pass
    a = cv2.warpAffine(a, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_REPLICATE).reshape(H, W, -1)
    ga = a.mean(axis=2)
    m = (ga > 4) & (gb > 4)                                          # privacy zones (black) never count
    bx, by = int(abs(dx)) + 2, int(abs(dy)) + 2
    m[:by, :] = False; m[H - by:, :] = False; m[:, :bx] = False; m[:, W - bx:] = False
    m[:int(H * max(0.0, min(90.0, float(top or 0))) / 100.0), :] = False
    if m.sum() < 0.05 * W * H:
        return {"boxes": [], "mask": np.zeros((H, W), bool), "shift": [dx / W, dy / H], "light": 1.0}
    d = np.zeros((H, W), np.float32)
    for c in range(b.shape[2]):                                      # light: one gain per channel from the medians (a new thing hardly moves them)
        ac, bc = a[:, :, c], b[:, :, c]
        k = (float(np.median(bc[m])) + 1.0) / (float(np.median(ac[m])) + 1.0)
        d = np.maximum(d, np.abs(ac * k - bc) / ZF_THR)
    bw = ((d > 1.0) & m).astype(np.uint8)
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    boxes = []
    for c in cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]:
        x, y, w, h = cv2.boundingRect(c)
        if w * h >= 0.003 * W * H and cv2.contourArea(c) >= 0.0015 * W * H:
            boxes.append([round(x / W, 4), round(y / H, 4), round(w / W, 4), round(h / H, 4), round(float(d[y:y + h, x:x + w].mean()), 2)])
    boxes.sort(key=lambda r: -r[2] * r[3])
    return {"boxes": boxes[:8], "mask": bw.astype(bool), "shift": [round(dx / W, 4), round(dy / H, 4)],
            "light": round((float(gb[m].mean()) + 1) / (float(ga[m].mean()) + 1), 2)}


def zf_region_changed(res, box):
    """a region [x, y, w, h] 0..1 changed in a comparison: more than a fifth of it marked"""
    mk = res["mask"]
    H, W = mk.shape
    x0, y0 = int(box[0] * W), int(box[1] * H)
    x1, y1 = max(x0 + 1, int(round((box[0] + box[2]) * W))), max(y0 + 1, int(round((box[1] + box[3]) * H)))
    return float(mk[y0:y1, x0:x1].mean()) > 0.2


def zf_tod(t):
    lt = time.localtime(t)
    return lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec


def zf_reference(it, now_t):
    """the still to compare with: the chosen one, or one of the same direction from the same time of day (±1 h) close to it"""
    near = lambda x: abs((zf_tod(x[0]) - zf_tod(now_t) + 43200) % 86400 - 43200) <= 3600
    if near(it):
        return it, True
    c = [x for x in zf_dir_items(it[1], it[2], it[6]) if abs(x[0] - it[0]) <= 36 * 3600 and near(x)]
    r = zf_nearest(c, it[0])
    return (r, True) if r else (it, False)


def zf_live(wait=2.5):
    """the live picture of the head camera (small, clean) -> (t, img, pose) or None"""
    lv = ZF["live"]
    if lv and time.time() - lv[0] < 3.0:
        return lv
    ZF["ev"].clear(); ZF["want"] = time.time() + wait
    ZF["ev"].wait(wait)
    return ZF["live"] if ZF["live"] and time.time() - ZF["live"][0] < wait + 1 else None


def zf_item(f):
    return next((it for it in reversed(zf_items()) if it[3] == f), None)


def zf_now(g):
    """the «now» side: a newer still g, else the live picture -> (t, img, pose) or None"""
    if g:
        it = zf_item(g); im = zf_load(g) if it else None
        return (it[0], im, (it[1], it[2])) if im is not None else None
    return zf_live()


def zf_diff(f, g="", top=None):
    """then (f) against now (live or g): the marked regions; cached, one at a time (Pi CPU)"""
    it = zf_item(f)
    if not it:
        return {"ok": False, "msg": "no such picture"}
    top = float(CFG.get("zf_mask_top") or 0) if top is None else max(0.0, min(90.0, float(top)))
    key = (f, g or int(time.time() / 4), top)
    if key in ZF["cache"]:
        return ZF["cache"][key]
    with ZF["calc"]:
        t0 = time.time()
        now = zf_now(g)
        if now is None:
            return {"ok": False, "msg": "no live picture"}
        ref, same = zf_reference(it, now[0])
        old = zf_load(ref[3])
        if old is None:
            return {"ok": False, "msg": "no such picture"}
        fov = cam_fov()
        guess = (-((now[2][0] - ref[1] + 180) % 360 - 180) / max(1.0, fov[0]), (now[2][1] - ref[2]) / max(1.0, fov[1]))   # like lupe_world_xy
        r = zf_compare(old, now[1], top, guess)
        out = {"ok": True, "boxes": r["boxes"], "shift": r["shift"], "light": r["light"], "ref": {"f": ref[3], "t": ref[0]},
               "same_tod": same, "top": top, "ms": int((time.time() - t0) * 1000)}
        if len(ZF["cache"]) > 12:
            ZF["cache"].clear()
        ZF["cache"][key] = out
        return out


def zf_when(f, box, g=""):
    """stage 3: when did the region change? Binary search over the stills of this direction between then (f) and now (g / live)"""
    it = zf_item(f)
    old = zf_load(f) if it else None
    if old is None:
        return {"ok": False, "msg": "no such picture"}
    end = zf_item(g) if g else None
    t_end = end[0] if end else time.time() + 1
    cand = [x for x in zf_dir_items(it[1], it[2], it[6]) if it[0] < x[0] < t_end][-4000:]
    with ZF["calc"]:
        steps = [0]

        def changed(i):
            steps[0] += 1
            im = zf_load(cand[i][3])
            return im is not None and zf_region_changed(zf_compare(old, im, 0.0), box)
        lo, hi = -1, len(cand)                                   # lo: not changed (then), hi: changed (the newest / live)
        if end is not None and cand and not changed(len(cand) - 1):
            return {"ok": True, "found": False, "steps": steps[0]}
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if changed(mid):
                hi = mid
            else:
                lo = mid
    a = cand[lo] if lo >= 0 else it
    b = cand[hi] if hi < len(cand) else None
    tb = b[0] if b else time.time()
    out = {"ok": True, "found": True, "steps": steps[0], "n": len(cand), "before": {"t": a[0], "f": a[3]},
           "after": {"t": b[0], "f": b[3]} if b else None,
           "timeline": "/timeline?day=" + time.strftime("%Y-%m-%d", time.localtime(tb)) + "&mode=day", "recs": []}
    try:
        for r in _tl_recordings(datetime.fromtimestamp(a[0]), datetime.fromtimestamp(tb))[:3]:
            out["recs"].append({"name": r["name"], "t": r["t"], "url": "/recordings?open=" + urllib.parse.quote(r["name"])
                                + "&day=" + time.strftime("%Y-%m-%d", time.localtime(r["t"]))})
    except Exception:
        pass
    return out


# ---- thinning (stage 3) ---------------------------------------------------------------------------------------------------------------
def zf_thin(now=None, cap_gb=None):
    """keep: last 24 h all, until 7 days 1 per hour and direction, older 1 per day and direction (the one nearest to noon); then at most
    zf_max_gb, oldest first. Only files of this folder (never timelapse photos or recordings). -> (deleted, bytes left)"""
    now = time.time() if now is None else now
    cap = float(CFG.get("zf_max_gb") or 5.0) if cap_gb is None else float(cap_gb)
    items = list(zf_items())
    snap = {it[3] for it in items}
    keep, best = [], {}
    for it in items:
        age = now - it[0]
        if age <= 86400:
            keep.append(it); continue
        lt = time.localtime(it[0])
        k = (it[6], round(it[1] / (2 * ZF_TOL)), round(it[2] / (2 * ZF_TOL)), time.strftime("%Y%m%d" + ("%H" if age <= 7 * 86400 else ""), lt))
        score = (it[4] != "tl", abs(zf_tod(it[0]) - 43200) if age > 7 * 86400 else it[0])
        if k not in best or score < best[k][0]:
            best[k] = (score, it)
    keep += [v[1] for v in best.values()]
    keep.sort(key=lambda it: it[0])
    total = sum(it[5] for it in keep)
    while keep and total > cap * 1024 ** 3:
        total -= keep.pop(0)[5]
    kept = {it[3] for it in keep}
    gone = [it for it in items if it[3] not in kept]
    if not gone:
        return 0, total
    for it in gone:
        try:
            os.remove(os.path.join(zf_dir(), it[3]))
        except OSError:
            pass
    with ZF["lock"]:
        days = {}
        for it in keep:
            days.setdefault(it[3][:8], []).append(it)
        for day in {it[3][:8] for it in gone}:
            p = os.path.join(zf_dir(), "idx_" + day + ".jsonl")
            rows = days.get(day, [])
            try:
                if rows:
                    with open(p + ".tmp", "w", encoding="utf-8") as fh:
                        for it in rows:
                            fh.write(json.dumps({"t": it[0], "p": it[1], "q": it[2], "f": it[3], "s": it[4], "n": it[5], "c": it[6]}) + "\n")
                    os.replace(p + ".tmp", p)
                else:
                    os.remove(p)
                    os.rmdir(os.path.join(zf_dir(), day))
            except OSError:
                pass
        ZF["items"] = sorted(keep + [it for it in (ZF["items"] or []) if it[3] not in snap], key=lambda it: it[0])   # + saved meanwhile
    ZF["cache"].clear()
    log_event("sys", f"Window to the past: {len(gone)} old stills thinned out, {total / 1024 ** 2:.0f} MB left")
    return len(gone), total


def zf_thin_loop():
    try:
        os.setpriority(os.PRIO_PROCESS, threading.get_native_id(), 19)        # low priority (Linux: per thread)
    except (AttributeError, OSError):
        pass
    time.sleep(900)
    while True:
        try:
            zf_thin()
        except Exception as e:
            log_event("sys", f"Window to the past: thinning {e}"[:160])
        time.sleep(86400)


def zf_state():
    p, q = servo_pos_deg()
    its = zf_dir_items(p, q)
    every = zf_items()
    return {"ok": True, "on": bool(CFG.get("zf_on")), "pose": [round(p, 2), round(q, 2)], "moving": not servo_arrived(), "tol": ZF_TOL,
            "items": [[round(it[0]), it[3], it[4]] for it in its], "count": len(every), "mb": round(sum(it[5] for it in every) / 1024 ** 2, 1),
            "dirs": len({(round(it[1] / (2 * ZF_TOL)), round(it[2] / (2 * ZF_TOL))) for it in every}), "max_gb": CFG.get("zf_max_gb"),
            "mask_top": CFG.get("zf_mask_top"), "fov": list(cam_fov()), "oldest": round(every[0][0]) if every else None}


# ---- web: /api/zeitfenster (GET state), /api/zeitfenster/bild, /diff, /wann - administrator only --------------------------------
_smalltv_routes_639zzzz = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzzz
    _smalltv_routes_639zzzz(app, reply, body)
    from flask import Response, request, g

    def admin():
        return bool(unt_perms(g).get("admin"))

    def lang():
        return norm_lang(request.args.get("lang") or CFG.get("lang"))

    @app.route("/api/zeitfenster")
    def api_zf():
        if not admin():
            return reply({"ok": False, "msg": tr("not allowed for your user", lang())}, 403)
        return reply(zf_state())

    @app.route("/api/zeitfenster/bild")
    def api_zf_img():
        p = zf_path(request.args.get("f")) if admin() else None
        if not p:
            return reply({"ok": False}, 403 if not admin() else 404)
        with open(p, "rb") as fh:
            return Response(fh.read(), mimetype="image/jpeg", headers={"Cache-Control": "private, max-age=86400"})

    @app.route("/api/zeitfenster/diff")
    def api_zf_diff():
        if not admin():
            return reply({"ok": False}, 403)
        try:
            r = zf_diff(str(request.args.get("f") or ""), str(request.args.get("g") or ""), request.args.get("top"))
        except (ValueError, TypeError):
            r = {"ok": False, "msg": "bad value"}
        return reply(r, 200 if r.get("ok") else 404)

    @app.route("/api/zeitfenster/wann")
    def api_zf_when():
        if not admin():
            return reply({"ok": False}, 403)
        b = lupe_box(*(str(request.args.get("box") or "").split(",") + [None] * 4)[:4])
        if b is None:
            return reply({"ok": False, "msg": "box: x,y,w,h 0..1"}, 400)
        r = zf_when(str(request.args.get("f") or ""), b, str(request.args.get("g") or ""))
        return reply(r, 200 if r.get("ok") else 404)


# ---- the page (one button in #lv-tools, one layer over the picture, one bar under it) - from the data zip ----------------------
ZF_CSS = r"""
/* 639zzzz «Zeitfenster»: the layer lies under the buttons (z 6), the joystick (z 5), Lupe / CPU chip / compass (z 4) */
#zf-ov{position:absolute;z-index:3;overflow:hidden;touch-action:pan-y;cursor:ew-resize;-webkit-user-select:none;user-select:none}
#zf-ov>img{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:fill;pointer-events:none}
#zf-bar{position:absolute;top:0;bottom:0;width:2px;margin-left:-1px;background:#ffd34d;box-shadow:0 0 0 1px rgba(0,0,0,.45);pointer-events:none}
#zf-grip{position:absolute;width:30px;height:30px;margin:-15px 0 0 -15px;border-radius:50%;background:#ffd34d;color:#111;display:flex;
  align-items:center;justify-content:center;font:700 12px system-ui,sans-serif;box-shadow:0 1px 5px rgba(0,0,0,.55);pointer-events:none}
.zf-m{position:absolute;border:3px solid #ff3df2;border-radius:6px;background:rgba(255,61,242,.12);box-shadow:0 0 0 1px #fff,0 0 6px rgba(0,0,0,.6);cursor:pointer}
.zf-m.sel{border-color:#ffd34d;background:rgba(255,211,77,.2)}
#zf-panel{margin:8px 9px 2px;padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:var(--panel2);display:flex;flex-direction:column;gap:8px;font-size:14px}
#zf-panel[hidden]{display:none}
#zf-panel .zf-h{display:flex;align-items:center;gap:8px;flex-wrap:wrap}#zf-panel .zf-h b{font-size:15px}
#zf-panel .zf-t{flex:1;min-width:150px;color:var(--txt)}#zf-panel .zf-t small{color:var(--mut)}
#zf-panel input[type=range]{width:100%;margin:2px 0;accent-color:#ffd34d}
#zf-panel .zf-s{display:flex;gap:6px;flex-wrap:wrap}
#zf-panel button{min-height:34px;padding:4px 11px;border-radius:9px;border:1px solid var(--line);background:var(--btn2);color:var(--txt);font:inherit;cursor:pointer}
#zf-panel button.on{border-color:#ffd34d;color:#ffd34d}
#zf-panel .zf-msg{color:var(--mut);font-size:13px}#zf-panel .zf-msg:empty{display:none}
#zf-panel .zf-r{display:flex;align-items:center;gap:8px;flex-wrap:wrap}#zf-panel .zf-r label{display:flex;align-items:center;gap:6px;flex:1 1 220px;color:var(--mut);font-size:13px}#zf-panel .zf-r label input{flex:1;min-width:70px}#zf-panel .zf-r label span{white-space:nowrap;min-width:34px}
#zf-panel .zf-find{border-top:1px solid var(--line);padding-top:8px;display:flex;flex-direction:column;gap:6px}#zf-panel .zf-find[hidden]{display:none}
#lv-tools #lv-b-zf{font-size:17px;line-height:1}#lv-tools #lv-b-zf.on{color:#ffd34d;border-color:#ffd34d}
body.zf-on #kw-row{display:none!important}
body.zf-on #vcard .vtag{z-index:4}
"""

ZF_JS = r"""
window.zfPanel = function (d) {                       // 639zzzz: Einstellungen → Kameras & Kopf → Zeitfenster: what is stored
  if (!d || d.querySelector(".zf-p")) return;
  const st = el("div", "mut zf-p"); st.style.cssText = "font-size:13px;margin:4px 0 8px";
  const sum = d.querySelector("summary"); if (sum && sum.nextSibling) d.insertBefore(st, sum.nextSibling); else d.appendChild(st);
  const tick = async () => { let j = null; try { j = await (await fetch("/api/zeitfenster", {cache: "no-store"})).json(); } catch (e) {}
    if (!j || !j.ok) return;
    st.textContent = j.count + " " + t("pictures") + " · " + j.dirs + " " + t("directions") + " · " + j.mb + " MB / " + j.max_gb + " GB"
      + (j.oldest ? " · " + t("oldest") + ": " + new Date(j.oldest * 1000).toLocaleDateString() : "") + " · Live → ⏪"; };
  d.addEventListener("toggle", () => { if (d.open) tick(); }); if (d.open) tick();
};
(function () {
  if (window.mwZf || document.body.dataset.tab !== "live") return;
  const t = k => (typeof window.t === "function" ? window.t(k) : k);
  const E = (tag, cls, x) => { const e = document.createElement(tag); if (cls) e.className = cls; if (x != null) e.textContent = x; return e; };
  const LG = () => (typeof LANG !== "undefined" ? LANG : "de");
  const API = "/api/zeitfenster";
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const STOPS = [["1 h", 3600], ["yesterday", 86400], ["1 week", 604800], ["1 month", 2592000], ["1 year", 31536000]];
  const A0 = 300, AM = 34000000, v2a = v => A0 * Math.pow(AM / A0, v / 1000), a2v = a => 1000 * Math.log(Math.max(A0, a) / A0) / Math.log(AM / A0);
  const S = {on: false, info: null, items: [], cur: null, split: 0.5, age: 86400, marks: false, diff: null, dkey: "", poll: 0, sel: -1, gy: 0.5};
  let OV, OLD, MK, BAR, GRIP, P, TXT, RNG, MSG, BM, MASK, MV, FIND, BTN;
  const img = () => document.getElementById("video");
  const vis = e => !!(e && !e.hidden && e.getClientRects().length && getComputedStyle(e).display !== "none" && getComputedStyle(e).visibility !== "hidden");
  const loc = () => ({de: "de-CH", fr: "fr-CH", it: "it-CH", rm: "de-CH"})[LG()] || "en-GB";
  const fmt = s => new Date(s * 1000).toLocaleString(loc(), {weekday: "short", day: "numeric", month: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit"});
  function ago(s) { const d = Date.now() / 1000 - s; return d < 5400 ? Math.round(d / 60) + " min" : d < 172800 ? Math.round(d / 3600) + " h" : Math.round(d / 86400) + " " + t("days"); }
  function rect() {
    const im = img(); if (!im || !im.naturalWidth || !im.offsetWidth) return null;
    const ow = im.offsetWidth, oh = im.offsetHeight, k = Math.min(ow / im.naturalWidth, oh / (im.naturalHeight || 1));
    const cw = im.naturalWidth * k, ch = (im.naturalHeight || 1) * k;
    return {L: im.offsetLeft + (ow - cw) / 2, T: im.offsetTop + (oh - ch) / 2, cw: cw, ch: ch};
  }
  function headCam() {
    const s = ((img() || {}).src || "");
    if (s.indexOf("/cam_view/") >= 0 || s.indexOf("/cam_feed/") >= 0) return false;
    const J = (typeof QSJ !== "undefined" && QSJ) || {};
    return !((J.cfg || {}).thermal_on && (J.cfg || {}).thermal_source);
  }
  async function get(p) { try { const r = await fetch(API + p, {cache: "no-store"}); return r.ok ? await r.json() : (r.status === 403 ? {forbidden: true} : await r.json().catch(() => null)); } catch (e) { return null; } }
  function build() {
    const im = img(); if (!im) return false;
    const W = im.parentNode;
    OV = E("div"); OV.id = "zf-ov"; OLD = E("img"); OLD.alt = ""; OLD.draggable = false; MK = E("div"); MK.style.cssText = "position:absolute;inset:0";
    BAR = E("div"); BAR.id = "zf-bar"; GRIP = E("div", "", "◀▶"); GRIP.id = "zf-grip";
    OV.append(OLD, MK, BAR, GRIP); W.appendChild(OV);
    P = E("div"); P.id = "zf-panel"; P.setAttribute("aria-live", "polite");
    const h = E("div", "zf-h"); h.append(E("b", "", "⏪ " + t("Then")));
    TXT = E("span", "zf-t"); const x = E("button", "", "✕"); x.type = "button"; x.title = t("Close"); x.setAttribute("aria-label", t("Close")); x.onclick = close;
    h.append(TXT, x);
    RNG = E("input"); RNG.type = "range"; RNG.min = 0; RNG.max = 1000; RNG.step = 1; RNG.setAttribute("aria-label", t("How long ago"));
    RNG.oninput = () => { S.age = v2a(+RNG.value); pick(); };
    const st = E("div", "zf-s");
    STOPS.forEach(([k, a]) => { const b = E("button", "", t(k)); b.type = "button"; b.dataset.a = a; b.onclick = () => { S.age = a; RNG.value = Math.round(a2v(a)); pick(); }; st.append(b); });
    const r = E("div", "zf-r");
    BM = E("button", "", "▢ " + t("Mark changes")); BM.type = "button"; BM.id = "zf-marks"; BM.onclick = () => { S.marks = !S.marks; S.dkey = ""; S.diff = null; paint(); diff(); };
    const lb = E("label"); MASK = E("input"); MASK.type = "range"; MASK.min = 0; MASK.max = 80; MASK.step = 5; MV = E("span");
    MASK.oninput = () => { MV.textContent = MASK.value + " %"; };
    MASK.onchange = async () => { try { await fetch("/api/set", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({key: "zf_mask_top", value: +MASK.value})}); } catch (e) {}
      if (S.info) S.info.mask_top = +MASK.value; S.dkey = ""; diff(); };
    lb.append(document.createTextNode(t("Ignore at the top (sky, trees)")), MASK, MV); r.append(BM, lb);
    MSG = E("div", "zf-msg"); FIND = E("div", "zf-find"); FIND.hidden = true;
    P.append(h, RNG, st, r, MSG, FIND);
    W.parentNode.insertBefore(P, W.nextSibling);
    OV.addEventListener("pointerdown", e => { if (e.target.classList.contains("zf-m")) return; OV.setPointerCapture(e.pointerId); drag(e); OV.onpointermove = drag; });
    const up = () => { OV.onpointermove = null; };
    OV.addEventListener("pointerup", up); OV.addEventListener("pointercancel", up);
    OV.addEventListener("click", e => e.stopPropagation()); OV.addEventListener("dblclick", e => { e.stopPropagation(); e.preventDefault(); });
    return true;
  }
  function drag(e) { const b = OV.getBoundingClientRect(); if (b.width > 0) { S.split = clamp((e.clientX - b.left) / b.width, 0, 1); paint(); } }
  function grip(b) {                         // the grip never lies on a button, the CPU chip, the compass, the small picture or the joystick
    const others = [...document.querySelectorAll("#lv-tools button, #lv-cpu, #lv-comp, #v3-mini, #lv-joy, .vtag, #vo-lupe, #lupe-ov .lupe-bar")].filter(vis).map(e => e.getBoundingClientRect());
    const x = b.left + S.split * b.width;
    for (const f of [0.5, 0.4, 0.6, 0.3, 0.7, 0.22, 0.78]) {
      const y = b.top + f * b.height;
      if (!others.some(o => o.right > x - 17 && o.left < x + 17 && o.bottom > y - 17 && o.top < y + 17)) return f;
    }
    return 0.5;
  }
  function paint() {
    if (!OV) return;
    const r = rect();
    if (!S.on || !r || !S.cur || !headCam()) { OV.hidden = true; return; }
    OV.hidden = false;
    OV.style.left = r.L + "px"; OV.style.top = r.T + "px"; OV.style.width = r.cw + "px"; OV.style.height = r.ch + "px";
    const sh = (S.diff && S.diff.shift) || [0, 0];
    OLD.style.transform = "translate(" + (sh[0] * 100) + "%," + (sh[1] * 100) + "%)";      // the old picture moved onto the live one
    const cut = (1 - S.split) * 100 + sh[0] * 100;
    OLD.style.clipPath = OLD.style.webkitClipPath = "inset(0 " + Math.max(0, cut) + "% 0 0)";
    BAR.style.left = GRIP.style.left = (S.split * 100) + "%";
    const b = OV.getBoundingClientRect(); S.gy = grip(b); GRIP.style.top = (S.gy * 100) + "%";
    MK.textContent = "";
    if (S.marks && S.diff && S.diff.ok) S.diff.boxes.forEach((m, i) => {
      const d = E("div", "zf-m" + (i === S.sel ? " sel" : "")); d.style.left = m[0] * 100 + "%"; d.style.top = m[1] * 100 + "%"; d.style.width = m[2] * 100 + "%"; d.style.height = m[3] * 100 + "%";
      d.title = t("When did this change?"); d.onclick = e => { e.stopPropagation(); when(i); }; MK.append(d); });
    BM.classList.toggle("on", S.marks);
  }
  function pick() {
    const its = S.items, target = Date.now() / 1000 - S.age;
    let best = null; for (const it of its) if (!best || Math.abs(it[0] - target) < Math.abs(best[0] - target)) best = it;
    const was = S.cur && S.cur[1];
    S.cur = best;
    if (!best) {
      TXT.textContent = "";
      MSG.textContent = !headCam() ? t("Only in the picture of the head camera.") : S.info && S.info.moving ? t("The head is moving …")
        : t("No picture from back then for this direction yet. MoveEye collects one at every stop of the round, with every timelapse photo and every hour while the head stands still.");
    } else {
      TXT.innerHTML = ""; TXT.append(document.createTextNode(fmt(best[0]) + " "), E("small", "", "(" + t("ago") + " " + ago(best[0]) + ")"));
      MSG.textContent = S.marks && S.diff && S.diff.ok ? marksText() : "";
      if (best[1] !== was) { OLD.src = API + "/bild?f=" + encodeURIComponent(best[1]); S.diff = null; S.dkey = ""; S.sel = -1; FIND.hidden = true; diff(); }
    }
    paint();
  }
  function marksText() {
    const d = S.diff, n = d.boxes.length;
    let s = n ? n + " " + t(n === 1 ? "change marked - tap it: when did it change?" : "changes marked - tap one: when did it change?") : t("No change found.");
    if (!d.same_tod) s += " · " + t("No picture from the same time of day - light changes can show up as marks.");
    return s;
  }
  let dT = 0;
  function diff() {
    clearTimeout(dT); if (!S.marks || !S.cur) { paint(); return; }
    dT = setTimeout(async () => {
      const key = S.cur[1] + "|" + (S.info ? S.info.mask_top : 0);
      if (key === S.dkey && S.diff) return;
      S.dkey = key; MSG.textContent = t("Comparing …");
      const j = await get("/diff?f=" + encodeURIComponent(S.cur[1]) + "&lang=" + LG());
      if (S.dkey !== key) return;
      S.diff = j && j.ok ? j : null; MSG.textContent = S.diff ? marksText() : t("No live picture to compare.");
      paint();
    }, 250);
  }
  async function when(i) {
    if (!S.diff || !S.cur) return;
    S.sel = i; paint(); const m = S.diff.boxes[i];
    FIND.hidden = false; FIND.textContent = t("Searching when this changed …");
    const j = await get("/wann?f=" + encodeURIComponent(S.cur[1]) + "&box=" + m.slice(0, 4).join(",") + "&lang=" + LG());
    FIND.textContent = "";
    if (!j || !j.ok) { FIND.textContent = t("No connection to MoveEye."); return; }
    if (!j.found) { FIND.textContent = t("No change found."); return; }
    FIND.append(E("div", "", t("Changed between") + " " + fmt(j.before.t) + " " + t("and") + " " + (j.after ? fmt(j.after.t) : t("now")) + " (" + j.steps + " " + t("comparisons") + ")"));
    const row = E("div", "zf-s");
    const a = E("button", "", "🕒 " + t("Open the timeline")); a.type = "button"; a.onclick = () => { location.href = j.timeline; }; row.append(a);
    (j.recs || []).forEach(r => { const b = E("button", "", "🎞 " + new Date(r.t * 1000).toLocaleTimeString(loc(), {hour: "2-digit", minute: "2-digit"})); b.type = "button"; b.onclick = () => { location.href = r.url; }; row.append(b); });
    if (j.after) { const s = E("button", "", "⏪ " + t("Show this moment")); s.type = "button"; s.onclick = () => { S.age = Date.now() / 1000 - j.after.t + 1; RNG.value = Math.round(a2v(S.age)); pick(); }; row.append(s); }
    FIND.append(row);
  }
  async function load() {
    const j = await get("?lang=" + LG());
    if (!j || !j.ok) return;
    const sig = j.items.map(x => x[1]).join(",");
    S.info = j; if (document.activeElement !== MASK) { MASK.value = j.mask_top || 0; MV.textContent = MASK.value + " %"; }
    if (sig !== S.sig) { S.sig = sig; S.items = j.items; pick(); } else if (!S.cur) pick();
  }
  function open() {
    if (!OV && !build()) return;
    try { if (window.mwLupe && window.mwLupe.state().on) window.mwLupe.close(); } catch (e) {}
    S.on = true; P.hidden = false; document.body.classList.add("zf-on"); if (BTN) BTN.classList.add("on");
    RNG.value = Math.round(a2v(S.age)); load(); clearInterval(S.poll); S.poll = setInterval(() => { if (document.body.classList.contains("lupe-on") || document.body.classList.contains("videoonly")) close(); else load(); }, 4000);
    paint();
  }
  function close() { S.on = false; clearInterval(S.poll); if (P) P.hidden = true; if (OV) OV.hidden = true; document.body.classList.remove("zf-on"); if (BTN) BTN.classList.remove("on"); }
  addEventListener("resize", () => { if (S.on) paint(); });
  setInterval(() => { if (S.on) paint(); }, 1000);
  async function tools() {
    const tb = document.getElementById("lv-tools"); if (!tb) return setTimeout(tools, 400);
    const j = await get("?lang=" + LG());
    if (!j || !j.ok || !j.on || document.getElementById("lv-b-zf")) return;          // the administrator only (403 for everybody else)
    BTN = E("button", "", "⏪"); BTN.type = "button"; BTN.id = "lv-b-zf"; BTN.title = t("Then / now: the same direction back then"); BTN.setAttribute("aria-label", t("Then / now"));
    BTN.onclick = e => { e.stopPropagation(); S.on ? close() : open(); }; BTN.addEventListener("dblclick", e => e.stopPropagation());
    tb.insertBefore(BTN, document.getElementById("lv-b-view") || null);
    try { if (window.mwLupe) window.mwLupe.fit(); } catch (e) {}
  }
  window.mwZf = {open: open, close: close, state: () => ({on: S.on, cur: S.cur, split: S.split, diff: S.diff, items: S.items.length, gy: S.gy, msg: MSG ? MSG.textContent : ""}),
                 set: (age, split) => { if (split != null) S.split = split; if (age != null) { S.age = age; if (RNG) RNG.value = Math.round(a2v(age)); } pick(); },
                 marks: on => { S.marks = !!on; S.dkey = ""; diff(); }, when: when};
  setTimeout(tools, 1200);
})();
"""



# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_ZF = {
    "Window to the past": ("Zeitfenster", "Fenêtre sur le passé", "Finestra sul passato", "Fanestra en il passà"),
    "Then": ("Damals", "Autrefois", "Allora", "Lura"),
    "Then / now": ("Damals / Jetzt", "Autrefois / maintenant", "Allora / adesso", "Lura / ussa"),
    "Then / now: the same direction back then": ("Damals / Jetzt: dieselbe Richtung von damals", "Autrefois / maintenant : la même direction à l’époque",
                                                 "Allora / adesso: la stessa direzione di allora", "Lura / ussa: la medema direcziun da lura"),
    "How long ago": ("Wie lange her", "Il y a combien de temps", "Quanto tempo fa", "Quant ditg è quai"),
    "yesterday": ("gestern", "hier", "ieri", "ier"),
    "1 week": ("1 Woche", "1 semaine", "1 settimana", "1 emna"),
    "1 month": ("1 Monat", "1 mois", "1 mese", "1 mais"),
    "1 year": ("1 Jahr", "1 an", "1 anno", "1 onn"),
    "days": ("Tagen", "jours", "giorni", "dis"),
    "ago": ("vor", "il y a", "fa", "avant"),
    "Mark changes": ("Änderungen markieren", "Marquer les changements", "Segnare i cambiamenti", "Marcar las midadas"),
    "Ignore at the top (sky, trees)": ("Oben nicht beachten (Himmel, Bäume)", "Ignorer en haut (ciel, arbres)", "Ignorare in alto (cielo, alberi)",
                                       "Ignorar survart (tschiel, plantas)"),
    "Comparing …": ("Vergleiche …", "Comparaison …", "Confronto …", "Cumparar …"),
    "No change found.": ("Keine Änderung gefunden.", "Aucun changement trouvé.", "Nessun cambiamento trovato.", "Nagina midada chattada."),
    "change marked - tap it: when did it change?": ("Änderung markiert – antippen: wann hat sie sich geändert?", "changement marqué – touche-le : quand a-t-il changé ?",
                                                    "cambiamento segnato – toccalo: quando è cambiato?", "midada marcada – tutgar: cura è ella sa midada?"),
    "changes marked - tap one: when did it change?": ("Änderungen markiert – eine antippen: wann hat sie sich geändert?", "changements marqués – touche-en un : quand a-t-il changé ?",
                                                      "cambiamenti segnati – toccane uno: quando è cambiato?", "midadas marcadas – tutgar ina: cura è ella sa midada?"),
    "No picture from the same time of day - light changes can show up as marks.": (
        "Kein Bild von derselben Tageszeit – Lichtwechsel können als Markierung erscheinen.",
        "Pas d’image de la même heure – les changements de lumière peuvent apparaître comme marques.",
        "Nessuna immagine della stessa ora – i cambi di luce possono apparire come segni.",
        "Nagin maletg da la medema ura – midadas da la glisch pon cumparair sco marcas."),
    "No live picture to compare.": ("Kein Live-Bild zum Vergleichen.", "Pas d’image en direct pour comparer.", "Nessuna immagine dal vivo da confrontare.",
                                    "Nagin maletg live per cumparar."),
    "When did this change?": ("Wann hat sich das geändert?", "Quand cela a-t-il changé ?", "Quando è cambiato?", "Cura è quai sa midà?"),
    "Searching when this changed …": ("Suche, wann sich das geändert hat …", "Recherche du moment du changement …", "Cerco quando è cambiato …",
                                      "Tschertgar cura che quai è sa midà …"),
    "Changed between": ("Geändert zwischen", "Changé entre", "Cambiato tra", "Midà tranter"),
    "and": ("und", "et", "e", "e"),
    "now": ("jetzt", "maintenant", "adesso", "ussa"),
    "comparisons": ("Vergleiche", "comparaisons", "confronti", "cumparegliaziuns"),
    "Open the timeline": ("Zeitleiste öffnen", "Ouvrir la chronologie", "Aprire la cronologia", "Avrir la lingia dal temp"),
    "Show this moment": ("Diesen Moment zeigen", "Montrer ce moment", "Mostrare questo momento", "Mussar quest mument"),
    "Only in the picture of the head camera.": ("Nur im Bild der Kopf-Kamera.", "Seulement dans l’image de la caméra de tête.",
                                                "Solo nell’immagine della telecamera della testa.", "Mo en il maletg da la camera dal chau."),
    "The head is moving …": ("Der Kopf fährt …", "La tête bouge …", "La testa si muove …", "Il chau sa mova …"),
    "No picture from back then for this direction yet. MoveEye collects one at every stop of the round, with every timelapse photo and every hour while the head stands still.": (
        "Für diese Richtung gibt es noch kein Bild von damals. MoveEye sammelt eines an jedem Halt der Runde, bei jedem Zeitraffer-Foto und jede Stunde, wenn der Kopf still steht.",
        "Pas encore d’image d’autrefois pour cette direction. MoveEye en prend une à chaque arrêt de la ronde, à chaque photo du timelapse et chaque heure quand la tête est immobile.",
        "Per questa direzione non c’è ancora un’immagine di allora. MoveEye ne raccoglie una a ogni sosta del giro, a ogni foto del timelapse e ogni ora quando la testa è ferma.",
        "Per questa direcziun n’èsi anc nagin maletg da lura. MoveEye fa in a mintga fermada da la runda, cun mintga foto dal timelapse ed mintga ura, cura ch’il chau stat airi."),
    "Collect pictures for «then / now»": ("Bilder für «Damals / Jetzt» sammeln", "Collecter des images pour «autrefois / maintenant»",
                                         "Raccogliere immagini per «allora / adesso»", "Rimnar maletgs per «lura / ussa»"),
    "One picture every hour while the head stands still": ("Jede Stunde ein Bild, wenn der Kopf still steht", "Une image par heure quand la tête est immobile",
                                                           "Un’immagine ogni ora quando la testa è ferma", "In maletg mintga ura, cura ch’il chau stat airi"),
    "At most (GB)": ("Höchstens (GB)", "Au maximum (Go)", "Al massimo (GB)", "Maximalmain (GB)"),
    "Ignore at the top (%)": ("Oben nicht beachten (%)", "Ignorer en haut (%)", "Ignorare in alto (%)", "Ignorar survart (%)"),
    "pictures": ("Bilder", "images", "immagini", "maletgs"),
    "directions": ("Richtungen", "directions", "direzioni", "direcziuns"),
    "oldest": ("ältestes", "le plus ancien", "il più vecchio", "il pli vegl"),
    "Show then": ("Damals ansehen", "Voir autrefois", "Vedere allora", "Guardar lura"),
}
for _k, _v in _HX_ZF.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_ZF_JS_KEYS = ("Close", "No connection to MoveEye.", "not allowed for your user")


def zf_live_html():
    de = {k: v[0] for k, v in _HX_ZF.items()}
    de.update({k: DE.get(k, k) for k in _ZF_JS_KEYS})
    return ("<style id=\"zf-css\">" + ZF_CSS + "</style><script>\ntry { Object.assign(I18N.de, " + json.dumps(de, ensure_ascii=False)
            + "); } catch (e) {}\n" + ZF_JS + "</script>")


if 'id="zf-css"' not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace("</body>", zf_live_html() + "</body>", 1)
_ZF_GRP = '{sec: "Timelapse", ic: "⏱️"}'
if _ZF_GRP in WEB_PAGE and '{sec: "Window to the past"' not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_ZF_GRP, _ZF_GRP + ', {sec: "Window to the past", title: "Window to the past", ic: "⏪"}', 1)
_ZF_SEC = 'if (sec.id === "Extra display" && window.stvPanel) stvPanel(d);'
if _ZF_SEC in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_ZF_SEC, _ZF_SEC + '\n    if (sec.id === "Window to the past" && window.zfPanel) zfPanel(d);   // 639zzzz', 1)

# ---- the settings: Einstellungen → Kameras & Kopf → «Zeitfenster» (web and window read the same lists) ---------------------------
TOGGLES.extend([(ZF_SECTION, "zf_on", "Collect pictures for «then / now»"),
                (ZF_SECTION, "zf_hourly", "One picture every hour while the head stands still")])
SLIDERS.extend([(ZF_SECTION, "zf_max_gb", "At most (GB)", 0.5, 20, 0.5), (ZF_SECTION, "zf_mask_top", "Ignore at the top (%)", 0, 80, 5)])
SECTIONS.append(ZF_SECTION)
MENU_TITLES.setdefault(ZF_SECTION, ZF_SECTION)
TK_SUB_ICONS[ZF_SECTION] = "⏪"
for _g in TK_GROUPS:
    if _g[0] == "camera" and ZF_SECTION not in _g[2]:
        _g[2].append(ZF_SECTION)
SET_HELP.update({
    "zf_on": ("Small pictures per head direction for «⏪» on Live, without extra head movement (round, timelapse, hourly). Thinned out daily.", "on"),
    "zf_max_gb": ("Above this the oldest pictures are deleted (never timelapse photos or recordings).", "5 GB"),
    "zf_mask_top": ("This band at the top (sky, trees) is never marked as a change.", "0 - 30 %"),
})


# ---- the window (Tk): «⏪ Damals ansehen» - a simple window with a slider (same stills, same direction rule) -------------------------
def zf_tk_window(app):
    import base64
    win = tk.Toplevel(app.root); win.title("MoveEye – " + tr("Window to the past"))
    lab = ttk.Label(win); lab.pack(padx=8, pady=8)
    txt = ttk.Label(win, text=""); txt.pack()
    sc = ttk.Scale(win, from_=0, to=1000, orient="horizontal", length=480); sc.pack(fill="x", padx=8, pady=6)
    ttk.Button(win, text="✕ " + tr("Close"), command=win.destroy).pack(pady=(0, 8))
    keep = {}

    def show(_v=None):
        age = 300 * (34000000 / 300) ** (float(sc.get()) / 1000)
        p, q = servo_pos_deg()
        it = zf_nearest(zf_dir_items(p, q), time.time() - age)
        im = zf_load(it[3]) if it else None
        if im is None:
            lab.config(image=""); txt.config(text=tr(ZF_NO_PIC), wraplength=460)
            return
        im = cv2.resize(im, (480, max(1, int(im.shape[0] * 480 / im.shape[1]))), interpolation=cv2.INTER_AREA)
        keep["p"] = tk.PhotoImage(data=base64.b64encode(cv2.imencode(".png", im)[1].tobytes()).decode())
        lab.config(image=keep["p"]); txt.config(text="⏪ " + tr("Then") + ": " + datetime.fromtimestamp(it[0]).strftime("%d.%m.%Y %H:%M"))
    sc.config(command=show); sc.set(1000 * math.log(86400 / 300) / math.log(34000000 / 300)); show()


def _zf_tk_build_section(self, sec, sbody, settings_parent=None):
    _zf_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec == ZF_SECTION:
        try:
            ttk.Button(sbody, text="⏪ " + tr("Show then"), command=lambda: zf_tk_window(self)).pack(anchor="w", pady=(6, 0))
        except Exception as e:
            log_event("sys", f"Window: window to the past {e}"[:160])


_zf_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _zf_tk_build_section


# ---- the manual: one point in «Ansichten» (views) ------------------------------------------------------------------------------
HELP_ZF = {
    "de": '<li id="zf-help"><b>⏪ Zeitfenster – Damals / Jetzt (nur Administrator):</b> Knopf ⏪ auf dem Live-Bild. Unter dem Bild wählst du, wie lange her (1 h · gestern · 1 Woche · 1 Monat · 1 Jahr oder frei schieben); links vom gelben Balken siehst du dieselbe Blickrichtung von damals, rechts das Live-Bild – den Balken ziehen. «Änderungen markieren» rahmt ein, was anders ist (Helligkeit zählt nicht, oben ein Band für Himmel / Bäume ausblenden); einen Rahmen antippen sucht, wann es sich geändert hat, mit Sprung in die Zeitleiste oder zur Aufnahme. Die Bilder sammelt MoveEye ohne zusätzliche Kopfbewegung: an den Halten der Runde, bei den Zeitraffer-Fotos und stündlich, wenn der Kopf still steht. Täglich ausgedünnt (24 h alles, bis 7 Tage 1 pro Stunde, dann 1 pro Tag), höchstens 5 GB (Einstellungen → Kameras & Kopf → Zeitfenster). Im Fenster am Pi: dort «⏪ Damals ansehen».</li>',
    "en": '<li id="zf-help"><b>⏪ Window to the past – then / now (administrator only):</b> button ⏪ on the live picture. Under the picture choose how long ago (1 h · yesterday · 1 week · 1 month · 1 year or slide freely); left of the yellow bar the same direction back then, right the live picture – drag the bar. «Mark changes» frames what is different (brightness does not count, hide a band at the top for sky / trees); tap a frame to find when it changed, with a jump to the timeline or the recording. MoveEye collects the pictures without extra head movement: at the stops of the round, with the timelapse photos and every hour while the head stands still. Thinned out daily (24 h all, until 7 days 1 per hour, then 1 per day), at most 5 GB (Settings → Cameras & head → Window to the past). In the window on the Pi: «⏪ Show then» there.</li>',
    "fr": '<li id="zf-help"><b>⏪ Fenêtre sur le passé – autrefois / maintenant (administrateur) :</b> bouton ⏪ sur l’image en direct. Sous l’image, choisis il y a combien de temps (1 h · hier · 1 semaine · 1 mois · 1 an ou librement) ; à gauche de la barre jaune la même direction autrefois, à droite l’image en direct. «Marquer les changements» encadre ce qui a changé ; toucher un cadre cherche quand cela a changé, avec un lien vers la chronologie. Les images sont prises sans mouvement de tête supplémentaire ; au maximum 5 Go.</li>',
    "it": '<li id="zf-help"><b>⏪ Finestra sul passato – allora / adesso (amministratore):</b> pulsante ⏪ sull’immagine dal vivo. Sotto l’immagine scegli quanto tempo fa (1 h · ieri · 1 settimana · 1 mese · 1 anno o liberamente); a sinistra della barra gialla la stessa direzione di allora, a destra l’immagine dal vivo. «Segnare i cambiamenti» incornicia ciò che è cambiato; toccare un riquadro cerca quando è cambiato, con un collegamento alla cronologia. Le immagini sono raccolte senza movimenti extra della testa; al massimo 5 GB.</li>',
    "rm": '<li id="zf-help"><b>⏪ Fanestra en il passà – lura / ussa (administratur):</b> buttun ⏪ sin il maletg live. Sut il maletg tschernas ti quant ditg (1 h · ier · 1 emna · 1 mais · 1 onn u liber); a sanestra da la trav gelga la medema direcziun da lura, a dretga il maletg live. «Marcar las midadas» enturnescha quai ch’è midà; tutgar in rom tschertga cura ch’i è sa midà, cun colliaziun a la lingia dal temp. Ils maletgs vegnan rimnads senza moviment supplementar dal chau; maximalmain 5 GB.</li>',
}


def _help_zf(doc, lang):
    i = doc.find('<section id="views"')
    if i < 0 or 'id="zf-help"' in doc:
        return doc
    j = doc.find("</ul></section>", i)
    return doc[:j] + HELP_ZF[lang] + doc[j:] if j >= 0 else doc


_hp_en_zf = HELP_PAGE.find('<div lang="en">')
if _hp_en_zf > 0:
    HELP_PAGE = _help_zf(HELP_PAGE[:_hp_en_zf], "de") + _help_zf(HELP_PAGE[_hp_en_zf:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_zf(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def zf_selftest():
    rng = np.random.default_rng(7)
    base = cv2.GaussianBlur(rng.integers(40, 200, (270, 480, 3), dtype=np.uint8), (0, 0), 3)
    new = base.copy(); cv2.rectangle(new, (300, 150), (360, 210), (20, 20, 230), -1)
    r = zf_compare(base, new)
    assert r["boxes"] and abs(r["boxes"][0][0] - 300 / 480) < 0.06 and abs(r["boxes"][0][1] - 150 / 270) < 0.08, r["boxes"]
    dark = np.clip(base.astype(np.float32) * 0.6, 0, 255).astype(np.uint8)
    assert not zf_compare(base, dark)["boxes"], "global brightness is no change"
    assert zf_region_changed(r, r["boxes"][0][:4]) and not zf_region_changed(r, [0.02, 0.02, 0.15, 0.15])
    assert not zf_compare(base, new, top=80)["boxes"], "the band at the top is ignored"
    assert zf_same_dir([0, 179.0, 0, "", "", 0, "head"], -179.0, 2.0) and not zf_same_dir([0, 10.0, 0, "", "", 0, "head"], 14.0, 0)
    assert zf_path("../x.jpg") is None and zf_path("20261114/zf_101500_000.jpg/../../a") is None
    names = set(zf_feed.__code__.co_names) | set(_zf_tl_update.__code__.co_names) | set(zf_save_bg.__code__.co_names)
    assert not names & {"servo_goto", "kopf_move", "move_camera", "lupe_aim"}, "the window to the past never moves the head"
    assert Timelapse.update is _zf_tl_update and Timelapse._shoot is _zf_tl_shoot
    assert 'id="zf-css"' in WEB_PAGE and '{sec: "Window to the past"' in WEB_PAGE and HELP_PAGE.count('id="zf-help"') == 2
    assert not role_allows("view", "/api/zeitfenster", "GET", {}) and not role_allows("family", "/api/zeitfenster/bild", "GET", {})
    assert ZF_SECTION in SECTIONS and "zf_on" in USER_SETTINGS_DENY
    for k, v in _HX_ZF.items():
        assert len(v) == 4 and all(v) and "ß" not in "".join(v), k
    return "compare (object, light, sky band), direction, paths, never moves the head, page hooks, rights, texts"


SELFTEST_EXTRA.append(("Window to the past «⏪ Damals / Jetzt» (639zzzz)", zf_selftest))
