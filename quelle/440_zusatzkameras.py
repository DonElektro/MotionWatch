#@ Motion Watch – Teil 440: zusätzliche Kameras. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# More cameras at the same time (motion recording only: no AI, no servos)
#   The first camera (the "source") does the full job. Extra cameras watch for movement, record clips (cam<n>_<time>.mp4 + snapshot)
#   and can be viewed in the grid at /cams. They follow the same switches (detection, recording) and schedules.
# ----------------------------------------------------------------------------
CAMS = []
LIVE_RECS = set()                    # file names that are being written right now (never deleted / zipped)
WATCH_REF = {"w": None}


def _is_live(name, watch=None):
    return name in LIVE_RECS or (watch is not None and bool(watch.rec_name) and watch.rec_name == name)


class ExtraCam:
    def __init__(self, idx, spec):
        self.idx, self.spec = idx, spec
        self.stop = False
        self.jpeg = None; self.seq = 0; self.viewers = 0; self._enc_t = 0.0
        self.status = "connecting…"; self.label = source_label(spec); self.res = ""; self.fps = 0.0
        self.motion = False; self.recording = False
        self.writer = None; self.rec_name = ""; self.rec_info = None; self.last_motion = 0.0; self.streak = 0
        self.boxes = []; self.times = deque(maxlen=30); self.ftimes = deque(maxlen=31); self.n = 0; self.last_cleanup = 0.0
        self.raw = None; self.raw_t = 0.0; self.raw_until = 0.0        # 2.98.30: a clean picture for the panorama (317), only when asked
        self.thread = threading.Thread(target=self.loop, daemon=True); self.thread.start()

    def info(self):
        return {"n": self.idx, "id": self.spec, "label": self.label, "status": self.status, "res": self.res,
                "fps": round(self.fps, 1), "motion": self.motion, "recording": self.recording}

    def close(self):
        self.stop = True
        self.thread.join(4.0)
        self._stop_rec()

    def _sleep(self, sec):
        end = time.time() + sec
        while not self.stop and time.time() < end:
            time.sleep(0.2)

    def loop(self):
        while not self.stop:
            if toolmode_on():                                    # tool mode: this camera rests too
                self.status = "tool mode"; self.motion = False; self._sleep(1.0); continue
            src, sid, label, err = open_source(self.spec)
            if src is None:
                self.status = f"failed: {err}"; self._sleep(6.0); continue
            self.label = label; self.status = "connected"
            self.res = f"{src.size[0]}x{src.size[1]}" if getattr(src, "size", None) else ""
            bg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=28, detectShadows=False)
            fails, self.n = 0, 0
            try:
                while not self.stop:
                    if toolmode_on():
                        break
                    ok, frame = src.read()
                    if not ok:
                        fails += 1
                        if fails >= 60:
                            break
                        time.sleep(0.05); continue
                    fails = 0
                    self._process(frame, bg)
            except Exception as e:
                log_event("sys", f"Camera {self.label}: {e}")
            finally:
                src.release(); self._stop_rec()
            if not self.stop and not toolmode_on():
                self.status = "connection lost - reconnecting"; self.motion = False; self._sleep(2.0)

    def _process(self, frame, bg):
        t0 = time.time()
        self.n += 1
        if t0 < self.raw_until:
            self.raw = frame.copy(); self.raw_t = t0
        H, W = frame.shape[:2]
        if self.n % 2 == 0 or not self.times:                  # detection on every 2nd frame is enough
            pw = 320; ph = max(1, int(H * pw / W)); sx = W / pw; sy = H / ph
            gray = cv2.GaussianBlur(cv2.cvtColor(cv2.resize(frame, (pw, ph)), cv2.COLOR_BGR2GRAY), (5, 5), 0)
            fg = bg.apply(gray)
            fg = cv2.dilate(cv2.erode(cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)[1], None, iterations=1), None, iterations=2)
            cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            amin = CFG["min_area"] * (1.0 - CFG["sensitivity"] / 200.0) * (320.0 / 480.0) ** 2
            self.boxes = [(int(x * sx), int(y * sy), int(w * sx), int(h * sy)) for x, y, w, h in
                          (cv2.boundingRect(c) for c in cnts if cv2.contourArea(c) >= amin)] if self.n > 30 else []
            self.motion = bool(self.boxes) and CFG["detection_on"]
            self.streak = self.streak + 1 if self.motion else 0
        now = time.time()
        if self.motion and self.streak >= 3:
            self.last_motion = now
        for x, y, w, h in self.boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 1)
        cv2.rectangle(frame, (0, 0), (W, 26), (0, 0, 0), -1)
        cv2.putText(frame, self.label.encode("ascii", "replace").decode()[:40] + ("   MOTION" if self.motion else ""), (8, 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 160, 255) if self.motion else (230, 230, 230), 1, cv2.LINE_AA)
        want = CFG["record"] and CFG["detection_on"] and self.last_motion > 0 and now - self.last_motion < CFG["record_tail"]
        if want and self.writer is None:
            self._start_rec(frame)
        elif not want and self.writer is not None:
            self._stop_rec()
        if self.writer is not None:
            self.writer.write(frame); self.rec_info["frames"] += 1
        self.recording = self.writer is not None
        self.times.append(time.time() - t0)
        self.ftimes.append(t0)
        if self.n % 15 == 0 and len(self.ftimes) >= 2:          # 2.98.24: the real picture rate (was: 1 / time of the work = 700 fps)
            self.fps = (len(self.ftimes) - 1) / max(1e-3, self.ftimes[-1] - self.ftimes[0])
        if self.viewers > 0 and now - self._enc_t >= 0.1:        # only encode while somebody watches
            self._enc_t = now
            out = frame if W <= 640 else cv2.resize(frame, (640, int(H * 640 / W)), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 65])
            if ok:
                self.jpeg = buf.tobytes(); self.seq += 1

    def _start_rec(self, frame):
        if CFG.get("sim_on"):
            self.last_motion = 0.0; return                 # simulation: no recordings
        h, w = frame.shape[:2]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"cam{self.idx}_{stamp}"
        wr, codec = open_writer(os.path.join(CFG["record_dir"], base + ".mp4"), 12.0, (w, h))
        if wr is None:
            self.last_motion = 0.0; return
        if time.time() - self.last_cleanup > 60 and WATCH_REF["w"] is not None:
            WATCH_REF["w"].cleanup_recordings(); self.last_cleanup = time.time()
        if CFG["snapshot_on_person"]:
            cv2.imwrite(os.path.join(CFG["record_dir"], base + ".jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            gps_tag_jpg(os.path.join(CFG["record_dir"], base + ".jpg"))
        self.writer = wr; self.rec_name = base + ".mp4"; LIVE_RECS.add(self.rec_name)
        fps = max(5.0, min(30.0, self.fps or 12.0))
        self.rec_info = {"start": time.time(), "fps": fps, "frames": 0, "codec": codec, "schedules": list(SCHED["active"])}
        log_event("rec", f"Recording started: {self.rec_name} ({self.label})")

    def _stop_rec(self):
        if self.writer is None:
            return
        wr, self.writer = self.writer, None
        wr.release()
        info, name = self.rec_info, self.rec_name
        self.rec_info = None; self.recording = False
        try:
            meta = {"start": datetime.fromtimestamp(info["start"]).isoformat(timespec="seconds"),
                    "end": datetime.now().isoformat(timespec="seconds"), "frames": info["frames"],
                    "duration": round(info["frames"] / max(1.0, info["fps"]), 1), "fps": round(info["fps"], 1), "codec": info["codec"],
                    "persons": 0, "motion": True, "source": self.label, "source_id": self.spec, "schedules": info["schedules"]}
            with open(os.path.join(CFG["record_dir"], os.path.splitext(name)[0] + ".json"), "w") as f:
                json.dump(meta, f)
        except OSError:
            pass
        LIVE_RECS.discard(name); self.rec_name = ""
        log_event("rec", f"Recording stopped: {name}")


def cams_apply():
    """Start / stop the extra camera threads so they match the settings."""
    want = [x for x in CFG["extra_cams"] if x != CFG.get("source")]     # 2.98.27: never the main camera a second time
    for c in list(CAMS):
        if c.spec not in want:
            CAMS.remove(c); threading.Thread(target=c.close, daemon=True).start()
    have = {c.spec for c in CAMS}
    used = {c.idx for c in CAMS}
    for spec in want:
        if spec not in have:
            idx = next(i for i in range(1, 99) if i not in used); used.add(idx)
            CAMS.append(ExtraCam(idx, spec))


def cams_status(watch=None):
    main = {"n": 0, "id": STATE["source_id"] or CFG["source"], "label": STATE["source_label"] or source_label(CFG["source"]),
            "status": STATE["source_status"], "res": STATE["source_res"], "fps": STATE["fps"],
            "motion": bool(STATE["persons"] or STATE["candidates"]), "recording": STATE["recording"]}
    return [main] + [c.info() for c in CAMS]


def cams_add(spec):
    if not isinstance(spec, str) or not SRC_RE.match(spec) or spec == "auto":
        return False, "unknown source"
    if spec == CFG.get("source") or spec == STATE.get("source_id"):
        return False, "this is the main camera already"         # 2.98.27: a Pi camera can be open only once
    if spec.startswith("url:") and not find_ip_source(spec[4:]):
        return False, "unknown network camera"
    if spec in CFG["extra_cams"] or spec == STATE["source_id"]:
        return False, "this camera is already in use"
    if len(CFG["extra_cams"]) >= MAX_EXTRA:
        return False, f"maximum {MAX_EXTRA} extra cameras"
    CFG["extra_cams"] = CFG["extra_cams"] + [spec]
    save_settings(); cams_apply(); log_event("sys", f"Extra camera added: {source_label(spec)}")
    return True, ""


def cams_remove(spec):
    if spec not in CFG["extra_cams"]:
        return False, "unknown source"
    CFG["extra_cams"] = [x for x in CFG["extra_cams"] if x != spec]
    save_settings(); cams_apply(); log_event("sys", f"Extra camera removed: {source_label(spec)}")
    return True, ""


def cams_close_all():
    for c in list(CAMS):
        c.stop = True
    for c in list(CAMS):
        c.thread.join(3.0); c._stop_rec()


atexit.register(cams_close_all)


