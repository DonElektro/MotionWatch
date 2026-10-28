#@ Motion Watch – Teil 410: KERN: die Erkennungs-Schleife (Bewegung, Personen, Alarm). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
class MotionWatch:
    def __init__(self):
        self.cap = None                    # the video source (CvSource / PiCamSource), opened in a background thread
        self.bg = cv2.createBackgroundSubtractorMOG2(history=400, varThreshold=28, detectShadows=False)
        self.weather = WeatherAnalyzer(); self.tracker = Tracker(); self.tuner = AutoTuner(); self.zwatch = ZoneWatch()
        self.ai = AIDetector(); self.hw = Hardware(); self.patrol = Patrol(); self.relays = RelayManager()
        self.frame_out = None; self.jpeg = None; self.jpeg_seq = 0
        self.frame_raw = None; self.raw_until = 0.0
        self.sysmon = SysMonitor(); self.netmon = NetMonitor(); self.remotemon = RemoteMonitor()
        self.sights = SightingTracker(); self.reports = ReportScheduler(); self.battmon = BatteryMonitor()
        self.logkeeper = LogKeeper(); self.updwatch = UpdateWatcher()
        self.mask_buf = deque(maxlen=5)
        self.color_bg = None               # slow colour background for the shadow filter
        self.writer = None; self.last_person_time = 0; self.last_relay_time = 0
        self.rec_name = ""; self.rec_info = None; self.rec_size = None; self._rec_retry = 0.0
        self.preroll = deque()
        self.frame_times = deque(maxlen=30)
        self.seen_t = deque(maxlen=40)           # 2.95.64: when each picture was analysed -> the REAL frame rate
        self.mt = {"id": None, "t": 0.0, "moved": 0.0, "tpl": None, "box": None}  # follow movement: target, its look, last own move
        self.frame_gaps = deque(maxlen=60); self._last_t0 = 0.0     # time between camera frames -> real frame rate of a recording
        self.eco_wake_t = 0.0; self.eco_slow = False; self._eco_src = None
        self.read_failures = 0; self.web_viewers = 0
        self.pre_since = 0.0; self.pre_last = 0.0; self.pre_alerted = False
        self.last_warm = 0.0; self.warm_alerted = False
        self.notifier = Notifier(); self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        self.last_cleanup = 0
        self._open_lock = threading.Lock(); self._open_gen = 0; self._opened = None; self._opening = False; self._retry_at = 0.0
        self._switch_fail_until = 0.0; self._sim_retry_at = 0.0
        if CFG.get("sim_on") and not str(CFG.get("source", "")).startswith("sim:"):
            CFG["source"] = "sim:0"                           # 2.95.55: an older version kept the webcam for good after a failed switch
        os.makedirs(CFG["record_dir"], exist_ok=True); rec_clean_tmp()
        atexit.register(self.close)
        self.presence = PresenceMonitor()
        self.scheduler = Scheduler()
        global THERMAL, AUDIO, BACKUP
        self.timelapse = Timelapse(); THERMAL = ThermalCam()
        if BACKUP is None:
            BACKUP = Backup()
        global TAMPER, LENS
        if LENS is None:
            LENS = LensCheck()
        if TAMPER is None:
            TAMPER = TamperGuard()
            global ENV
            if ENV is None:
                ENV = EnvSensor()
                threading.Thread(target=weather_loop, daemon=True, name="weather").start()
            threading.Thread(target=fleet_loop, daemon=True, name="fleet").start()
            threading.Thread(target=feedback_loop, daemon=True, name="feedback").start()
        global MQTT_BRIDGE, SENSHUB
        if MQTT_BRIDGE is None:
            MQTT_BRIDGE = MqttBridge()
        if SENSHUB is None:
            SENSHUB = SensorHub()
        global STORMWATCH, GPSMODULE
        if STORMWATCH is None:
            STORMWATCH = StormWatch()
        if GPSMODULE is None:
            GPSMODULE = GpsModule()
        global MOVERCTL
        if MOVERCTL is None:
            MOVERCTL = MoverControl()
        global SOLARMON, SIMLINK
        if SOLARMON is None:
            SOLARMON = SolarMonitor()
        if SIMLINK is None:
            SIMLINK = SimLink()
            SimDiscovery()
            ToolsWatch(); UplinkWatch(); WifiGuard()
            threading.Thread(target=sim_autoupdate, daemon=True, name="simupdate").start()
        if AUDIO is None:
            AUDIO = AudioMonitor()
            SOUNDEV_OBJ["o"] = SoundEvents()
            if bt_available():
                threading.Thread(target=lambda: (bt_list(), bt_keeper()), daemon=True, name="bt").start()
        hotspot_password()                                 # the own Wi-Fi has its password from the start (shown on the page)
        WATCH_REF["w"] = self
        self.request_source(CFG["source"])

    def close(self):
        if self.writer is not None:
            self.writer.release(); self.writer = None
            self._finish_recording()
        sound_stop()
        save_settings_now()

    # ---- recordings folder housekeeping ---------------------------------
    def cleanup_recordings(self):
        """Delete the oldest recordings (video + snapshot + info file belong together) until below record_max_gb.
        Favourites (star in the preview page) are never deleted."""
        groups = {}
        for f in glob.glob(os.path.join(CFG["record_dir"], "*")):
            if os.path.isfile(f):
                groups.setdefault(os.path.splitext(os.path.basename(f))[0], []).append(f)
        items = []
        for stem, fs in groups.items():
            try:
                items.append((max(os.path.getmtime(f) for f in fs), sum(os.path.getsize(f) for f in fs), stem, fs))
            except OSError:
                pass
        items.sort(key=lambda g: g[0])
        total = sum(g[1] for g in items)
        removable = [g for g in items if not _read_sidecar(g[2] + ".json").get("fav")]
        limit = CFG["record_max_gb"] * 1024 ** 3
        removed = 0

        def card_full():
            try:
                return shutil.disk_usage(CFG["record_dir"]).free < 400 * 1024 ** 2      # keep 400 MB free for the system
            except OSError:
                return False
        while (total > limit or card_full()) and removable and len(items) - removed > 1:
            _mt, size, stem, fs = removable.pop(0)
            if any(os.path.basename(f) in LIVE_RECS or os.path.basename(f) == self.rec_name for f in fs):
                continue                                          # never delete what is being recorded right now
            try:
                for f in fs:
                    os.remove(f)
            except OSError:
                break
            rec_purge_extras(stem)
            total -= size; removed += 1
        STATE["rec_dir_mb"] = int(total / 1024 ** 2)
        if removed:
            log_event("rec", f"Cleanup: {removed} old recording(s) deleted, folder now {STATE['rec_dir_mb']} MB")

    # ---- video source ----------------------------------------------------
    def request_source(self, spec):
        """Switch to another video source (any thread). The running camera keeps working until the new one delivers a picture."""
        CFG["source"] = spec; save_settings()
        active = STATE["source_id"]
        if self.cap is not None and (spec == active or (spec == "auto" and active.startswith("usb:"))):
            return                                                # that camera is already running
        self._open_gen += 1
        self._start_opener(spec)

    def _start_opener(self, spec, quiet=False):
        gen = self._open_gen
        self._opening = True
        if not quiet:
            STATE["source_status"] = "connecting…"

        def work():
            res = open_source(spec)
            with self._open_lock:
                if gen == self._open_gen:
                    self._opened = res; self._opening = False
                elif res[0] is not None:
                    res[0].release()                              # a newer request replaced this one
        threading.Thread(target=work, daemon=True).start()

    def _take_opened(self):
        with self._open_lock:
            res, self._opened = self._opened, None
        return res

    def _apply_opened(self, res):
        src, sid, label, err = res
        if src is None:
            log_event("sys", f"Video source '{label}' not available: {err}")
            if self.cap is not None and str(STATE.get("source_id", "")).startswith("sim:") and not CFG["sim_on"]:
                self.cap.release(); self.cap = None                # simulation switched off: never keep the simulator picture
                STATE["source_status"] = f"failed: {err}"; self._retry_at = time.time() + 3.0
            elif self.cap is not None and str(sid).startswith("sim:") and CFG["sim_on"]:
                # 2.95.55: the simulation is on but its camera gives no picture (slow PC / VM, firewall): keep the working
                # camera for now, but stay with the simulator and try again - before, the webcam stayed for good
                STATE["source_status"] = f"switch failed: simulator camera - {err}, next try in 10 s (still using {STATE['source_label']})"
                self._switch_fail_until = time.time() + 12.0; self._sim_retry_at = time.time() + 10.0
            elif self.cap is not None:                            # a switch failed: keep the working camera
                STATE["source_status"] = f"switch failed: {err} (still using {STATE['source_label']})"
                self._switch_fail_until = time.time() + 60.0   # yellow note for a minute, the camera keeps working
                CFG["source"] = STATE["source_id"]; save_settings()
            else:
                STATE["source_status"] = f"failed: {err}"
                self._retry_at = time.time() + 3.0
            return
        old, self.cap = self.cap, src
        if old is not None:
            old.release()
        self.reset_scene()
        size = getattr(src, "size", None)
        STATE.update(source_id=sid, source_label=label, source_status="connected",
                     source_res=f"{size[0]}x{size[1]}" if size else "")
        log_event("rec", f"Video source: {label}" + (f" ({STATE['source_res']})" if STATE["source_res"] else ""))

    def reset_scene(self):
        """New camera = new picture size and scene: forget everything that depends on the old picture."""
        if self.writer is not None:
            self.writer.release(); self.writer = None
            self._finish_recording()
        self.bg = cv2.createBackgroundSubtractorMOG2(history=400, varThreshold=28, detectShadows=False)
        self.weather = WeatherAnalyzer(); self.tracker = Tracker()
        self.mask_buf.clear(); self.color_bg = None; self.preroll.clear()
        self.tuner.reset()
        self.read_failures = 0

    def no_camera_frame(self):
        img = np.zeros((360, 640, 3), np.uint8)
        busy = STATE["source_status"].startswith(("connecting", "connection lost"))
        ascii_ = lambda s: str(s).encode("ascii", "replace").decode()
        cv2.putText(img, "CONNECTING..." if busy else "NO CAMERA FOUND", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.1,
                    (0, 200, 255) if busy else (0, 0, 255), 3)
        cv2.putText(img, ascii_(source_label(CFG["source"]))[:50], (150, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2)
        cv2.putText(img, ascii_(STATE["source_status"])[:60], (150, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        cv2.putText(img, "check the camera / network  |  ls /dev/video*", (150, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        return img

    # ---- processing ------------------------------------------------------
    def preprocess(self, gray, rain_mode):
        if rain_mode:
            g = cv2.medianBlur(cv2.GaussianBlur(gray, (9, 9), 0), 5)
            self.mask_buf.append(g)
            if len(self.mask_buf) >= 3:
                g = np.median(np.array(self.mask_buf), axis=0).astype(np.uint8)
            return g
        self.mask_buf.clear()
        return cv2.GaussianBlur(gray, (5, 5), 0)

    def remove_shadows(self, fg, small):
        """Drop moving pixels that are only a darker copy of the background (= shadows)."""
        if self.color_bg is None:
            self.color_bg = small.astype(np.float32)
            return fg
        cv2.accumulateWeighted(small, self.color_bg, 0.002)
        if not CFG["shadow_filter"] or not np.any(fg):
            return fg
        bg = self.color_bg.astype(np.uint8)
        hsv_c = cv2.cvtColor(small, cv2.COLOR_BGR2HSV); hsv_b = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
        vb = hsv_b[:, :, 2].astype(np.float32) + 1.0
        ratio = hsv_c[:, :, 2].astype(np.float32) / vb
        dh = np.abs(hsv_c[:, :, 0].astype(np.int16) - hsv_b[:, :, 0].astype(np.int16))
        dh = np.minimum(dh, 180 - dh)
        ds = np.abs(hsv_c[:, :, 1].astype(np.int16) - hsv_b[:, :, 1].astype(np.int16))
        # on grey / low-saturation ground (asphalt, concrete, dusk) the hue is numerically unstable,
        # so the hue test is skipped there and only brightness ratio + saturation decide
        low_sat = (hsv_b[:, :, 1] < 50) & (hsv_c[:, :, 1] < 70)
        hue_ok = (dh < 12) | low_sat
        shadow = ((ratio > CFG["shadow_ratio_min"]) & (ratio < CFG["shadow_ratio_max"])
                  & hue_ok & (ds < 45) & (fg > 0)).astype(np.uint8) * 255
        # smooth the shadow mask so single person pixels are not punched out
        shadow = cv2.morphologyEx(shadow, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        shadow = cv2.morphologyEx(shadow, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        total = np.count_nonzero(fg)
        STATE["shadow_pct"] = int(100 * np.count_nonzero(shadow) / max(1, total))
        return cv2.bitwise_and(fg, cv2.bitwise_not(shadow))

    def foreground(self, gray, small, rain_mode, wind_boost):
        sens = CFG["sensitivity"] / 100.0
        self.bg.setVarThreshold(16 + (1 - sens) * 40 + (12 if rain_mode else 0))
        lr = 0.004 if rain_mode else 0.002
        mv = self.mt["moved"]
        if mv > self.mt.get("bg_reset", 0.0) and time.time() - mv > 0.3:
            lr = 1.0; self.mt["bg_reset"] = time.time()          # the camera turned to follow movement and stands again: new background at once
        elif time.time() - self.mt.get("bg_reset", 0.0) < 1.5:
            lr = 0.08                                            # ... and the "ghost" of the animal in it fades quickly
        fg = self.bg.apply(gray, learningRate=lr)
        _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        fg = self.remove_shadows(fg, small)                      # colour based shadow removal
        k = 5 if rain_mode or wind_boost > 1.5 else 3
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        return cv2.dilate(fg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 13)), 1)

    def classify(self, t, frame_area, wind_boost, ai_boxes):
        x, y, w, h = t.box
        aspect = w / float(h + 1e-6); area = w * h; sp = t.speed()
        t.ai_confirmed = any(iou(t.box, b) > 0.2 for b in ai_boxes)
        if CFG["car_filter"] and not t.ai_confirmed:
            vehicle = (aspect > CFG["car_aspect"] and sp > 3.0) or sp > CFG["car_speed"] or \
                      (area > CFG["car_area_frac"] * frame_area and aspect > 1.2 and sp > 1.0)
            if vehicle:
                if not t.is_vehicle:
                    STATE["ignored_vehicles"] += 1
                    log_event("car", f"Vehicle-like object #{t.id} ignored (aspect {aspect:.2f}, speed {sp:.1f})")
                t.is_vehicle, t.is_person = True, False
                return
            t.is_vehicle = False                               # shape became person-like again -> re-evaluate
        need_frames = int(CFG["walk_frames"] * wind_boost)
        walking = (len(t.speeds) >= need_frames and CFG["walk_min_speed"] <= sp <= CFG["walk_max_speed"]
                   and t.steadiness() >= CFG["speed_consistency"] and aspect < CFG["car_aspect"])
        if t.ai_confirmed:
            walking = True                                  # AI says person -> person
        elif CFG["ai_require"] and self.ai.net is not None and CFG["ai_enabled"]:
            walking = False                                 # needs AI confirmation
        elif t.is_person and CFG["person_sticky"] and sp <= CFG["walk_max_speed"]:
            walking = True                                  # keep flag while tracked (may stand still)
        if walking and not t.is_person:
            STATE["detections_total"] += 1
            log_event("person", f"Person #{t.id} {'AI-confirmed' if t.ai_confirmed else 'walking'}, speed {sp:.1f} px/f")
        t.is_person = walking

    # ---- servo tracking --------------------------------------------------
    def motion_target(self, candidates, animals, pw, ph, gray):
        """Something that is not a person but really goes somewhere (an animal, also one the AI does not know):
        big enough, moving for some time and away from where it started (branches in the wind swing back and forth).
        Once chosen it is followed by its look (template), so the turning camera does not lose it."""
        now = time.time(); area = float(pw * ph); mt = self.mt
        if STATE.get("wind_boost", 1.0) > 1.6 or STATE.get("wind_level") in ("strong", "storm"):
            mt.update(id=None, tpl=None); return None    # strong wind: everything moves, do not chase it

        def keep(b):                                      # remember where it was; something that only swings to and fro is let go
            tr = mt.setdefault("trail", deque(maxlen=60)); tr.append((now, b[0] + b[2] / 2.0, b[1] + b[3] / 2.0))
            pts = [p for p in tr if now - p[0] <= 4.0]
            if len(pts) >= 8 and now - pts[0][0] >= 3.0 and now - mt.get("since", now) > 4.0:
                path = sum(math.hypot(pts[i][1] - pts[i - 1][1], pts[i][2] - pts[i - 1][2]) for i in range(1, len(pts)))
                net = math.hypot(pts[-1][1] - pts[0][1], pts[-1][2] - pts[0][2])
                if path > 0.08 * pw and net < 0.25 * path and now - mt["moved"] > 1.0:
                    log_event("servo", "Followed movement only swings to and fro (branch in the wind?) - released")
                    mt.update(id=None, tpl=None); mt["trail"].clear(); return None
            mt["box"] = b; mt["t"] = now
            return b
        def tight(b):                                     # the movement boxes are made bigger (dilate 7 x 13): back to the animal
            x, y, w, h = [int(v) for v in b[:4]]
            if w > 14 and h > 20:
                x, y, w, h = x + 3, y + 6, w - 6, h - 12
            w = max(8, w); h = max(8, h)
            return max(0, min(pw - w, x)), max(0, min(ph - h, y)), w, h
        if mt.get("tpl") is not None and now - mt["moved"] > 1.0:   # camera stands still: the movement itself is the best guide
            x, y, w, h = mt["box"]; cx, cy = x + w / 2.0, y + h / 2.0
            near = [t for t in candidates if not t.lost and math.hypot(t.center()[0] - cx, t.center()[1] - cy) < max(max(w, h) * 2.5 + 20, 0.2 * pw)
                    and t.box[2] * t.box[3] < 0.2 * area]
            if near:
                t = min(near, key=lambda t: math.hypot(t.center()[0] - cx, t.center()[1] - cy))
                b = tight(t.box); tpl = gray[b[1]:b[1] + b[3], b[0]:b[0] + b[2]].copy()
                if tpl.shape[0] >= 8 and tpl.shape[1] >= 8:
                    mt.update(tpl=tpl, move_t=now)
                    return keep(b)
        if mt.get("tpl") is not None:                     # camera turns / nothing moves: find it again by its look
            x, y, w, h = mt["box"]; th_, tw_ = mt["tpl"].shape
            r = int(max(w, h) * 2.5) + (int(0.35 * pw) if now - mt["moved"] < 1.5 else 0)
            x0, y0 = max(0, x - r), max(0, y - r); x1, y1 = min(pw, x + w + r), min(ph, y + h + r)
            best = None
            if x1 - x0 > tw_ and y1 - y0 > th_:
                res = cv2.matchTemplate(gray[y0:y1, x0:x1], mt["tpl"], cv2.TM_CCOEFF_NORMED)
                _mn, sc, _l, loc = cv2.minMaxLoc(res)
                if sc >= 0.5:
                    best = (x0 + loc[0], y0 + loc[1], tw_, th_)
                    if sc > 0.65:                             # it changes its look while walking: learn slowly
                        cur = gray[best[1]:best[1] + th_, best[0]:best[0] + tw_]
                        if cur.shape == mt["tpl"].shape:
                            mt["tpl"] = cv2.addWeighted(mt["tpl"], 0.8, cur, 0.2, 0)
            if best is not None:
                if any(iou(t.box, best) > 0.05 for t in candidates if not t.lost):
                    mt["move_t"] = now
                if now - mt["moved"] > 1.5 and now - mt.get("move_t", now) > 3.0:
                    log_event("servo", "Followed movement: nothing moves there any more - released")   # stands still or gone
                    mt.update(id=None, tpl=None); return None
                return keep(best)
            if now - mt["t"] > 2.0:
                bx = mt["box"]; cx = (bx[0] + bx[2] / 2.0) / pw
                if (cx < 0.2 or cx > 0.8) and now - mt["moved"] > 0.4:     # it left the picture at the side: one look after it
                    p0 = CFG["pan"]; self.track((int((0.1 if cx < 0.5 else 0.9) * pw), int(ph / 2), 1, 1), pw, ph, 1.5)
                    if CFG["pan"] != p0:
                        mt["moved"] = now
                    log_event("servo", "Followed movement left the picture - looking after it")
                mt.update(id=None, tpl=None)
            return None
        amin = max(0.0002, float(CFG["track_motion_min"]) / 100.0) * area
        ok = []
        for t in candidates:
            a = t.box[2] * t.box[3]
            if t.lost or (t.is_vehicle and a > 0.02 * area):   # a small animal walking sideways looks "vehicle-like" - a car is big
                continue
            if a < amin or a > 0.35 * area:
                continue
            ok.append(t)
        box = None
        if animals:                                       # an animal the AI knows: at once
            b = max(animals, key=lambda o: o[2] * o[3]); box = tuple(int(v) for v in b[:4]); what = "animal (AI)"
        else:
            hold = float(CFG["track_motion_hold"])
            def goes(t):                                  # really goes somewhere: far enough and mostly in one direction
                net = math.hypot(t.center()[0] - t.start[0], t.center()[1] - t.start[1])
                h_ = list(t.hist); path = sum(math.hypot(h_[i][0] - h_[i - 1][0], h_[i][1] - h_[i - 1][1]) for i in range(1, len(h_)))
                net_h = math.hypot(h_[-1][0] - h_[0][0], h_[-1][1] - h_[0][1]) if len(h_) > 1 else 0.0
                return net >= 0.06 * pw and net_h >= 0.6 * max(path, 1e-6)
            good = [t for t in ok if now - t.born >= hold and goes(t)]
            if good:
                t = max(good, key=lambda t: t.box[2] * t.box[3]); box = tuple(int(v) for v in t.box); what = f"#{t.id}"
        if box is None:
            return None
        x, y, w, h = tight(box)
        tpl = gray[y:y + h, x:x + w].copy()
        if tpl.shape[0] < 8 or tpl.shape[1] < 8:
            return None
        log_event("servo", f"Following movement {what} ({w}x{h} px, not a person)")
        mt.update(id=what, tpl=tpl, box=(x, y, w, h), t=now, move_t=now, since=now); mt.setdefault("trail", deque(maxlen=60)).clear()
        return (x, y, w, h)

    def track(self, target_box, pw, ph, gain=1.0):
        x, y, w, h = target_box[:4]
        ex = (x + w / 2.0) / pw - 0.5          # -0.5 .. 0.5  (right = positive)
        ey = (y + h / 2.0) / ph - 0.5          # down  = positive
        dz = CFG["track_deadzone"]
        g = CFG["track_gain"] * 10.0 * gain
        if abs(ex) > dz:
            CFG["pan"] = max(0.0, min(100.0, CFG["pan"] + ex * g))
        if abs(ey) > dz:
            CFG["tilt"] = max(0.0, min(100.0, CFG["tilt"] - ey * g))

    # ---- recording ----------------------------------------------
    def handle_recording(self, frame, persons):
        now = time.time()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")          # video and snapshot of one event share the same name
        if not is_armed():
            persons = []                                  # disarmed: no snapshots, no notifications, no new recordings
        settle = now - SIM.get("off_t", 0.0) < 30.0       # just back from the simulation: the camera learns its picture
        if settle:
            persons = []; self.last_person_time = 0
        new_person = bool(persons) and (now - self.last_person_time) > CFG["record_tail"]
        if persons:
            self.last_person_time = now
        if new_person:
            snap = None
            if CFG["snapshot_on_person"] and not CFG["sim_on"]:
                snap = os.path.join(CFG["record_dir"], f"person_{stamp}.jpg")
                cv2.imwrite(snap, frame, [cv2.IMWRITE_JPEG_QUALITY, 85]); gps_tag_jpg(snap)
            self.notifier.person(len(persons), snap, frame)
            try:
                alarm_track_begin("person", stamp, snap)
            except Exception:
                pass
            if snap and BACKUP is not None and CFG["backup_type"] != "off":
                BACKUP.add(snap, {"first": True})                 # off the device at once - a thief may take the Pi
            push_alert("person", "person", count=len(persons), source=STATE["source_label"])
            siren_alarm("person")
        man_rec = now < QUICK["rec_until"]
        want = man_rec or CFG["record"] and ((self.last_person_time > 0 and (now - self.last_person_time) < CFG["record_tail"])
                                  or (CFG["thermal_alarm"] and is_armed() and now - self.last_warm < CFG["record_tail"])
                                  or (CFG["noise_alarm"] and AUDIO is not None and now - AUDIO.last_noise < CFG["record_tail"]))
        if POWER["pending"] or CFG["sim_on"] or settle:
            want = False                                  # the Pi shuts down / simulation: no (or finish the) recording
        h, w = frame.shape[:2]
        if self.writer is not None and (self.rec_size != (w, h) or getattr(self.writer, "failed", False)):
            early = getattr(self.writer, "failed", False) and time.time() - getattr(self.writer, "t_open", 0) < 15
            if early:                                          # 2.95.33: died right away -> other encoder, wait before trying
                _BAD_CODECS.add("ffmpeg_hw" if getattr(self.writer, "hw", False) else "ffmpeg")
                self._rec_retry = now + 15.0
                log_event("rec", "The video encoder stopped right after the start - trying another one in 15 s")
                REC_HEALTH.update(fail_t=time.time(), fail_n=REC_HEALTH["fail_n"] + 1, msg="the video encoder stopped right after the start")
            self.writer.release(); self.writer = None          # picture size changed (camera switched) or the encoder died
            self._finish_recording()
        pre = float(CFG["pre_roll"])
        if self.writer is None and not want and pre > 0 and CFG["record"] and not CFG["sim_on"]:
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])      # small ring buffer of recent frames
            if ok:
                self.preroll.append((now, buf.tobytes()))
        while self.preroll and (pre <= 0 or now - self.preroll[0][0] > pre + 0.5):
            self.preroll.popleft()
        if want and self.writer is None and now >= self._rec_retry:
            if now - self.last_cleanup > 60:
                self.cleanup_recordings(); self.last_cleanup = now
            name = os.path.join(CFG["record_dir"], (f"manual_{stamp}.mp4" if man_rec else f"person_{stamp}.mp4"))
            real = len(self.frame_gaps) / sum(self.frame_gaps) if len(self.frame_gaps) >= 5 and sum(self.frame_gaps) > 0 else 0.0
            fps = max(2.0, min(30.0, real or float(STATE["fps"]) or 15.0))     # real frame rate -> correct playback speed
            self.writer, codec = open_writer(name, fps, (w, h))
            if self.writer is None:
                self._rec_retry = now + 30.0
                log_event("rec", "Recording failed: no video encoder could be opened (retry in 30 s)")
                REC_HEALTH.update(fail_t=time.time(), fail_n=REC_HEALTH["fail_n"] + 1, msg="no video encoder could be opened (drive full or missing?)")
            else:
                self.rec_name = os.path.basename(name); self.rec_size = (w, h); STATE["rec_name"] = self.rec_name
                REC_HEALTH.update(fail_n=0)
                self.rec_info = {"start": now - (now - self.preroll[0][0] if self.preroll else 0.0), "fps": fps, "frames": 0, "persons": 0,
                                 "codec": codec, "source": STATE["source_label"], "source_id": STATE["source_id"],
                                 "schedules": list(SCHED["active"])}
                n = 0
                for _t, jb in self.preroll:                            # the seconds before the detection come first
                    img = cv2.imdecode(np.frombuffer(jb, np.uint8), cv2.IMREAD_COLOR)
                    if img is not None and img.shape[:2] == (h, w):
                        self.writer.write(img); n += 1
                self.preroll.clear(); self.rec_info["frames"] += n
                if AUDIO is not None and AUDIO.rec_start(name, self.rec_info["start"]):
                    self.rec_info["audio"] = name
                log_event("rec", f"Recording started: {self.rec_name} ({fps:.0f} fps, {STATE['recording_enc'] or codec}"
                                 + (f", {n} pre-roll frames" if n else "") + ")")
        elif not want and self.writer is not None:
            self.writer.release(); self.writer = None
            self._finish_recording()
            log_event("rec", "Recording stopped")
        if self.writer is not None:
            rs = tuple(getattr(self, "rec_size", ()) or ())
            if len(rs) == 2 and (frame.shape[1], frame.shape[0]) != rs:
                frame = cv2.resize(frame, rs)             # picture turned during a recording: keep the size of the file
            self.writer.write(frame)
            self.rec_info["frames"] += 1; self.rec_info["persons"] = max(self.rec_info["persons"], len(persons))
        STATE["recording"] = self.writer is not None

    def _finish_recording(self):
        """Write the small info file (<name>.json) next to a finished recording: source, schedules, duration, codec ..."""
        info, name = self.rec_info, self.rec_name
        self.rec_info = None; self.rec_name = ""; STATE["rec_name"] = ""
        if not info or not name:
            return
        meta = {"start": datetime.fromtimestamp(info["start"]).isoformat(timespec="seconds"),
                "end": datetime.now().isoformat(timespec="seconds"),
                "duration": round(info["frames"] / info["fps"], 1) if info["fps"] else 0.0,
                "frames": info["frames"], "fps": round(info["fps"], 1), "codec": info["codec"],
                "persons": info["persons"], "source": info["source"], "source_id": info["source_id"],
                "schedules": info["schedules"]}
        g = gps_now() if CFG["gps_tag"] else None
        if g:
            meta["gps"] = {"lat": g[0], "lon": g[1], "src": g[2]}
        try:
            with open(os.path.join(CFG["record_dir"], os.path.splitext(name)[0] + ".json"), "w") as f:
                json.dump(meta, f)
        except OSError:
            pass
        if info.get("audio") and AUDIO is not None:
            AUDIO.rec_stop(info["audio"], info["frames"], info["fps"])       # joins the sound with the video (background)
        elif g:
            threading.Thread(target=gps_tag_video, args=(os.path.join(CFG["record_dir"], name),), daemon=True).start()
        if BACKUP is not None and CFG["backup_type"] != "off" and (CFG["backup_all"] or info["persons"] or is_armed()):
            BACKUP.add(os.path.join(CFG["record_dir"], name), meta)

    # ---- power saving --------------------------------------------------
    def _eco(self, present, t0):
        """Power saving: while nothing happens only eco_fps pictures per second (camera slower, less CPU = less current).
        Movement, noise, an alarm, a recording, manual control or (if wanted) somebody watching = full speed for eco_wake s."""
        if not CFG["eco_on"]:
            if self.eco_slow:
                self._eco_set(False)
            STATE["eco"] = "off"; return
        busy = (bool(present & {"prealarm", "motion", "person", "warm", "noise"}) or self.writer is not None or STATE["tracking"] or manual_active() or TL_HOLD["on"]
                or (CFG["eco_view_full"] and self.web_viewers > 0) or (AUDIO is not None and AUDIO.noisy())
                or TALK["proc"] is not None or POWER["pending"] or time.time() - SENS["pir_t"] < 3)
        if busy:
            self.eco_wake_t = t0
        slow = t0 - self.eco_wake_t > float(CFG["eco_wake"])
        if slow != self.eco_slow or self._eco_src is not self.cap:
            self._eco_set(slow)
        STATE["eco"] = "saving" if slow else "awake"
        if slow:
            wait = 1.0 / eco_fps_now() - (time.time() - t0)
            end = time.time() + max(0.0, wait)
            while time.time() < end and self.eco_slow and CFG["eco_on"]:
                if (CFG["eco_view_full"] and self.web_viewers > 0) or manual_active() or (AUDIO is not None and AUDIO.noisy()) or time.time() - SENS["pir_t"] < 1:
                    self.eco_wake_t = time.time(); break               # wake up at once
                time.sleep(0.05)

    def _eco_set(self, slow):
        if slow != self.eco_slow:
            log_event("sys", "Power saving: few pictures (all quiet)" if slow else "Power saving: full speed")
        self.eco_slow = slow; self._eco_src = self.cap
        if self.cap is not None and hasattr(self.cap, "set_fps"):
            self.cap.set_fps(eco_fps_now() if slow else None)
        self._last_t0 = 0.0

    # ---- main loop -------------------------------------------------------
    def toolmode_frame(self):
        img = np.zeros((360, 640, 3), np.uint8)
        cv2.putText(img, "|| TOOL MODE", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 200, 255), 3)
        cv2.putText(img, "monitoring paused until " + datetime.fromtimestamp(TOOLMODE["until"]).strftime("%H:%M"), (150, 195),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2)
        cv2.putText(img, "all computing power for the tools", (150, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        return img

    def run(self):
        """2.95.33: the camera loop must never stop for good. An error is logged, the scene is learnt again and the loop
        goes on; after several errors in a row while armed, a push message says so."""
        errs = deque(maxlen=20)
        while True:
            try:
                self._run_loop()
            except Exception as e:
                now = time.time(); errs.append(now)
                import traceback
                tb = traceback.format_exc(limit=4).strip().splitlines()
                log_event("sys", f"Camera loop error (restarted): {type(e).__name__}: {e}"[:200] + " | " + " / ".join(x.strip() for x in tb[-3:])[:300])
                try:
                    self._reset_models()
                except Exception:
                    pass
                recent = [x for x in errs if now - x < 300]
                if len(recent) == 5 and is_armed():
                    try:
                        self.notifier.alert("{name}: " + tr("Camera loop disturbed"), tr("The detection had 5 errors in 5 minutes and keeps restarting - please check the log."), None)
                    except Exception:
                        pass
                time.sleep(min(10.0, 0.5 * len(recent)))

    def _reset_models(self):
        """only the learnt background / trackers (picture size changed) - a running recording goes on"""
        self.bg = cv2.createBackgroundSubtractorMOG2(history=400, varThreshold=28, detectShadows=False)
        self.weather = WeatherAnalyzer(); self.tracker = Tracker()
        self.mask_buf.clear(); self.color_bg = None
        self.tuner.reset()

    def _run_loop(self):
        tm_was = False
        while True:
            HEART["t"] = time.time()
            a_now = is_armed()
            if a_now != getattr(self, "_armed_was", a_now):     # 2.95.33: a warm body / movement seen while disarmed
                self.warm_alerted = False; self.pre_alerted = False   # must still alarm after arming
            self._armed_was = a_now
            if toolmode_on():                             # tool mode: the camera is closed, nothing is detected
                if not tm_was:
                    tm_was = True
                    if self.cap is not None:
                        try:
                            self.cap.release()
                        except Exception:
                            pass
                        self.cap = None
                    try:
                        self.reset_scene()                # a running recording is finished, the scene is learnt again later
                    except Exception:
                        pass
                    self.relays.update(set()); STATE["present"] = []; STATE["persons"] = 0; STATE["tracking"] = False
                    STATE["source_status"] = "tool mode"
                    self.frame_out = self.toolmode_frame()
                    ok_, buf_ = cv2.imencode(".jpg", self.frame_out, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    self._tm_jpeg = buf_.tobytes() if ok_ else None
                if getattr(self, "_tm_jpeg", None):              # the live picture shows the pause picture (once a second)
                    self.jpeg = self._tm_jpeg; self.jpeg_seq += 1
                time.sleep(1.0); continue
            if tm_was:
                tm_was = False; self._retry_at = 0.0
                STATE["source_status"] = "connecting"
                log_event("sys", "Tool mode over - camera and detection run again")
            opened = self._take_opened()
            if opened is not None:
                self._apply_opened(opened)
            if self.cap is None:
                self.relays.update(set()); STATE["present"] = []
                self.frame_out = self.no_camera_frame(); time.sleep(0.5)
                if not self._opening and time.time() >= self._retry_at:
                    self._start_opener(CFG["source"])
                continue
            if self._switch_fail_until and time.time() >= self._switch_fail_until:
                self._switch_fail_until = 0.0
                if STATE["source_status"].startswith(("switch failed", "simulator camera")):
                    STATE["source_status"] = "connected"
            if (CFG["sim_on"] and str(CFG["source"]).startswith("sim:") and not str(STATE.get("source_id", "")).startswith("sim:")
                    and not self._opening and time.time() >= self._sim_retry_at):
                self._sim_retry_at = time.time() + 10.0          # 2.95.55: simulation on, but another camera runs: try the simulator again
                self._open_gen += 1; self._start_opener(CFG["source"], quiet=True)
            ok, frame = self.cap.read()
            if not ok:
                self.read_failures += 1
                if self.read_failures >= 60:            # ~3 s without a frame -> reconnect the source
                    log_event("sys", "Camera stopped delivering frames - reconnecting")
                    STATE["source_status"] = "connection lost - reconnecting"
                    if self.writer is not None:          # 2.95.33: the recording up to now is kept and backed up
                        try:
                            self.writer.release()
                        except Exception:
                            pass
                        self.writer = None; self._finish_recording()
                    if is_armed() and not CFG["sim_on"] and time.time() - getattr(self, "_lost_alert", 0) > 600:
                        self._lost_alert = time.time()
                        try:
                            self.notifier.alert("{name}: " + tr("Camera lost"), tr("The camera stopped delivering pictures - reconnecting."), self.frame_out)
                        except Exception:
                            pass
                    self.cap.release()
                    self.cap = None; self.read_failures = 0; self._retry_at = time.time() + 2.0
                time.sleep(0.05); continue
            self.read_failures = 0
            ok_ = (str(CFG.get("cam_rotate", "0")), bool(CFG.get("cam_mirror")))
            if ok_ != getattr(self, "_orient", ok_):        # turned / mirrored now: a new scene for the detection
                self.reset_scene()
                if TAMPER is not None:
                    TAMPER.ref = None; TAMPER.settle = time.time() + 10   # no "camera turned" alarm because of this
                log_event("sys", f"Camera picture: turned {ok_[0]}°" + (", mirrored" if ok_[1] else ""))
            self._orient = ok_
            frame = cam_orient(frame)                     # turned / mirrored as set, before zones and detection
            frame = apply_privacy(frame)                  # privacy zones: black before anything else sees the picture
            rec_clean = frame.copy() if (CFG["record"] or QUICK["rec_until"] > 0 or self.writer is not None) and CFG["rec_marks"] != "full" else None
            rec_animals = []
            t0 = time.time()
            pm = CFG["picture_mode"]
            if pm == "grey" or (pm == "night_grey" and (LIGHTS["dark"] or (STATE.get("lights") or {}).get("ir"))):
                frame = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
            if self._last_t0 and t0 - self._last_t0 < 2.0 and not self.eco_slow:
                self.frame_gaps.append(t0 - self._last_t0)
            self._last_t0 = t0
            # timelapse: an alarm (person seen, recording running, tracking) always has priority over the photo
            alarm = (self.writer is not None or STATE["persons"] > 0 or STATE["tracking"]
                     or (self.last_person_time > 0 and t0 - self.last_person_time < CFG["record_tail"] + 1.0))
            if not CFG["sim_on"]:                         # simulation: no timelapse photos, no continuous recording
                self.timelapse.update(frame, alarm)
            if LOOPREC is not None and not CFG["sim_on"]:
                LOOPREC.feed(frame, t0)                         # continuous recording: a copy now and then
            if t0 < self.raw_until:
                self.frame_raw = frame.copy()
            H, W = frame.shape[:2]
            pw = CFG["proc_width"]; ph = int(H * pw / W); sx = W / pw; sy = H / ph
            if (pw, ph) != getattr(self, "_proc_size", (pw, ph)):     # power mode / camera changed the working size
                self._reset_models()
            self._proc_size = (pw, ph)
            small = cv2.resize(frame, (pw, ph))
            if TAMPER is not None:
                TAMPER.feed(small, t0)
            if LENS is not None:
                LENS.feed(small, t0)
            nv_on = NIGHTVISION.active()
            STATE["nightvision"] = nv_on
            if CFG["thermal_on"] and THERMAL is not None and not nv_on:
                frame = THERMAL.overlay(frame)             # detection keeps using `small` (the normal picture)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            bright = float(gray.mean()); STATE["brightness"] = int(bright)
            lowlight = CFG["lowlight_auto"] and bright < CFG["lowlight_threshold"]
            if lowlight != STATE["lowlight"]:
                log_event("auto", f"Low-light mode {'ON' if lowlight else 'OFF'} (brightness {bright:.0f})")
                STATE["lowlight"] = lowlight
            if lowlight:
                gray = self.clahe.apply(cv2.medianBlur(gray, 5))   # denoise, then boost contrast so dark figures separate
            if lowlight and CFG["lowlight_view"] and bright > 1.5:
                # the picture you see: gamma curve that lifts the average brightness to ~115 (dark parts much more than bright ones)
                gm = max(0.3, min(1.0, math.log(115.0 / 255.0) / math.log(max(bright, 2.0) / 255.0)))
                gm = round(gm, 2)
                if getattr(self, "_lut_g", None) != gm:
                    self._lut_g = gm
                    self._lut = np.array([min(255, int(round(255.0 * (i / 255.0) ** gm))) for i in range(256)], np.uint8)
                frame = cv2.LUT(frame, self._lut)
                STATE["view_gain"] = gm
            else:
                STATE["view_gain"] = 1.0
            if nv_on:
                frame = NIGHTVISION.apply(frame)           # night vision look (the detection keeps using the normal picture)

            rain_score = self.weather.rain(gray) if CFG["rain_auto"] else 0.0
            rain_mode = (rain_score > CFG["rain_threshold"]) if CFG["rain_auto"] else CFG["rain_mode"]
            if rain_mode != STATE["rain_mode"]:
                log_event("rain", "Rain mode ON - filtering rain" if rain_mode else "Rain mode OFF")
            wind_boost = STATE["wind_boost"]

            persons, candidates, person_boxes = [], [], []
            present = set()                      # what is in view right now -> relay triggers
            if CFG["detection_on"]:
                g = self.preprocess(gray, rain_mode)
                fg = self.foreground(g, small, rain_mode, wind_boost)
                ai_boxes = [b for b in self.ai.detect(small) if zone_box_ok(b, pw, ph)]
                ai_objs = [o for o in self.ai.objects if zone_box_ok(o, pw, ph)]
                rec_animals = [o for o in ai_objs if COCO_LABELS.get(o[5]) in ANIMALS]
                objects = ai_objs if (CFG["show_objects"] and CFG["ai_enabled"]) else []
                counts = {}
                for o in objects:
                    nm = COCO_LABELS.get(o[5], "object"); counts[nm] = counts.get(nm, 0) + 1
                STATE["objects"] = len(objects)
                STATE["object_summary"] = ", ".join(f"{n} x{c}" for n, c in counts.items())
                min_area = CFG["min_area"] * (1.0 - CFG["sensitivity"] / 200.0) * wind_boost
                cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                # following movement also sees smaller things (a cat, a fox far away) - they never count as a person / alarm
                small_area = min(min_area, float(CFG["track_motion_min"]) / 100.0 * pw * ph) if CFG["track_motion"] else min_area
                boxes = [b for b in (cv2.boundingRect(c) for c in cnts if cv2.contourArea(c) >= small_area) if zone_box_ok(b, pw, ph)]
                if any(b[2] * b[3] >= min_area for b in boxes):
                    present.add("prealarm")              # pre-alarm: anything at all moves in the picture (before it is judged to be a person)
                boxes = merge_boxes(boxes + [b[:4] for b in ai_boxes])   # AI persons become tracks too
                tracks = self.tracker.update(boxes)
                for t in tracks:
                    if t.lost:
                        continue
                    self.classify(t, pw * ph, wind_boost, ai_boxes)
                    if t.is_person and not t.ai_confirmed and t.box[2] * t.box[3] < min_area * 0.8:
                        t.is_person = False                     # too small for a person (only seen for following movement)
                    if t.is_person:
                        persons.append(t); person_boxes.append(t.box)
                    else:
                        candidates.append(t)            # anything else that moves -> white
                try:
                    alarm_track_sample(persons, rec_animals, pw, ph)       # 2.95.53: for the Alarm-Rückblick in 3D
                except Exception:
                    pass
                if person_boxes or ai_boxes:
                    present.add("person")
                try:
                    self.zwatch.update(persons, pw, ph, frame, t0)
                except Exception as e:                     # never break the camera loop
                    log_event("sys", f"Zones: {e}"[:160])
                if persons or candidates:
                    present.add("motion")
                present.update(COCO_LABELS.get(o[5], "object") for o in ai_objs)
                if present & ANIMALS:
                    present.add("animal")
                species_update(ai_objs, frame, pw, ph, t0)
                if CFG["diary_on"] and not CFG["sim_on"]:  # animal diary + night report: best picture of every visit (not in the simulation)
                    for o in ai_objs:
                        lab = COCO_LABELS.get(o[5], "object")
                        if lab in ANIMALS:
                            sp = species_for(o[:4]) if CFG["species_on"] else None
                            self.sights.see(sp[0] if sp else lab, t0, frame, o, sp[1] if sp else o[4], pw, ph)
                    if "person" in present:
                        pb = person_boxes or [b[:4] for b in ai_boxes]
                        if pb:
                            self.sights.see("person", t0, frame, max(pb, key=lambda b: b[2] * b[3]), 0.9, pw, ph)
                self.tuner.observe(fg, tracks, persons, STATE["fps"])
                if CFG["wind_auto"]:
                    ws = self.weather.wind(fg, person_boxes)
                    STATE["wind_score"] = ws
                    boost = 1.0 + max(0.0, ws - CFG["wind_threshold"]) / (1 - CFG["wind_threshold"]) * (CFG["wind_boost_max"] - 1)
                    STATE["wind_boost"] = round(min(CFG["wind_boost_max"], boost), 2)
                    lvl = "calm" if ws < CFG["wind_threshold"] else ("breezy" if ws < 0.55 else ("strong" if ws < 0.8 else "storm"))
                    if lvl != STATE["wind_level"]:
                        log_event("wind", f"Wind: {lvl} (score {ws:.2f}, threshold x{STATE['wind_boost']})")
                    STATE["wind_level"] = lvl
                else:
                    STATE["wind_boost"] = 1.0; STATE["wind_score"] = 0.0; STATE["wind_level"] = "off"

                # servo tracking: follow the largest person
                # (paused while the camera is moved by hand: pad, arrow keys, web page)
                manual = manual_active()
                if CFG["track_person"] and person_boxes and not manual:
                    target = max(person_boxes, key=lambda b: b[2] * b[3])
                    self.track(target, pw, ph)
                    if not STATE["tracking"]:
                        log_event("servo", "Tracking person - patrol paused")
                    STATE["tracking"] = True
                elif CFG["track_motion"] and not manual and (mt_box := self.motion_target(candidates + persons, rec_animals, pw, ph, gray)) is not None:
                    if t0 - self.mt["moved"] > 0.4:                # move, let the picture settle a moment, look again
                        p0, q0 = CFG["pan"], CFG["tilt"]
                        self.track(mt_box, pw, ph, 1.0)
                        if (CFG["pan"], CFG["tilt"]) != (p0, q0):
                            self.mt["moved"] = t0
                    if not STATE["tracking"]:
                        log_event("servo", "Following movement (animal or something unknown) - patrol paused")
                    STATE["tracking"] = True; STATE["track_what"] = "motion"
                    mx_, my_, mw_, mh_ = [int(v) for v in (mt_box[0] * sx, mt_box[1] * sy, mt_box[2] * sx, mt_box[3] * sy)]
                    cv2.rectangle(frame, (mx_, my_), (mx_ + mw_, my_ + mh_), (0, 220, 255), 2)
                    cv2.putText(frame, "FOLLOW", (mx_, max(14, my_ - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1, cv2.LINE_AA)
                    cv2.drawMarker(frame, (W // 2, H // 2), (0, 220, 255), cv2.MARKER_CROSS, 24, 1)
                elif STATE["tracking"] and (manual or (time.time() - self.last_person_time > 2.0 and time.time() - self.mt["t"] > 3.0)):
                    was = STATE.get("track_what"); STATE["tracking"] = False; STATE["track_what"] = ""
                    log_event("servo", "Manual control - tracking paused" if manual else
                              ("Movement lost - patrol may resume" if was == "motion" else "Person lost - patrol may resume"))
                    self.mt["id"] = None
                if person_boxes:
                    STATE["track_what"] = "person" if STATE["tracking"] else ""

                # drawing
                if CFG["show_mask"]:                      # the picture stays as it is, movement gets a soft red tint
                    mk = cv2.resize(fg, (W, H), interpolation=cv2.INTER_NEAREST) > 0
                    if mk.any():
                        px = frame[mk].astype(np.uint16)
                        frame[mk] = ((px * 7 + np.array([40, 40, 255], np.uint16) * 3) // 10).astype(np.uint8)    # 30 % red
                for t in candidates:
                    x, y, w, h = [int(v) for v in (t.box[0] * sx, t.box[1] * sy, t.box[2] * sx, t.box[3] * sy)]
                    draw_outline(frame, cnts, t.box, sx, sy, (255, 255, 255), 1)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 1)
                    cv2.putText(frame, "vehicle" if t.is_vehicle else "motion", (x, max(14, y - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
                for obj in objects:
                    draw_object(frame, obj, sx, sy)
                for t in persons:
                    x, y, w, h = [int(v) for v in (t.box[0] * sx, t.box[1] * sy, t.box[2] * sx, t.box[3] * sy)]
                    if CFG["highlight_red"]:
                        roi = frame[max(0, y):y + h, max(0, x):x + w]
                        msrc = fg[t.box[1]:t.box[1] + t.box[3], t.box[0]:t.box[0] + t.box[2]]
                        mroi = cv2.resize(msrc, (roi.shape[1], roi.shape[0])) if roi.size and msrc.size else None
                        if mroi is not None:
                            red = np.zeros_like(roi); red[:, :, 2] = 255
                            tint = cv2.addWeighted(roi, 0.45, red, 0.55, 0)
                            roi[mroi > 0] = tint[mroi > 0]
                    draw_outline(frame, cnts, t.box, sx, sy, (0, 0, 255), 2)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                    cv2.putText(frame, f"PERSON #{t.id}{' AI' if t.ai_confirmed else ''}  {t.speed():.1f}px/f",
                                (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    if CFG["show_tracks"] and len(t.hist) > 1:
                        pts = np.array([(int(px * sx), int(py * sy)) for px, py in t.hist], np.int32)
                        cv2.polylines(frame, [pts], False, (0, 0, 255), 2)
                if person_boxes and CFG["track_person"]:
                    cv2.drawMarker(frame, (W // 2, H // 2), (0, 255, 255), cv2.MARKER_CROSS, 24, 1)
            else:
                STATE["objects"] = 0; STATE["object_summary"] = ""
                if STATE["tracking"]:
                    STATE["tracking"] = False; STATE["track_what"] = ""

            if CFG["show_zones"] and ZONES:
                for z in ZONES:
                    if z["mode"] == "privacy":
                        continue
                    pts = np.array([(int(px * W), int(py * H)) for px, py in z["points"]], np.int32)
                    col = {"ignore": (0, 160, 255), "line": (255, 210, 60), "loiter": (60, 220, 255)}.get(z["mode"], (80, 200, 80))
                    cv2.polylines(frame, [pts], z["mode"] != "line", col, 2 if z["mode"] == "line" else 1, cv2.LINE_AA)
                    if z["mode"] == "line" and z.get("dir", "both") != "both":
                        (ax, ay), (bx, by) = pts[0], pts[1]
                        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0; nx, ny = -(by - ay), (bx - ax)
                        ln = math.hypot(nx, ny) or 1.0; sgn = 1 if z["dir"] == "ab" else -1
                        cv2.arrowedLine(frame, (int(mx), int(my)), (int(mx + sgn * nx / ln * 28), int(my + sgn * ny / ln * 28)), col, 2, cv2.LINE_AA, tipLength=0.4)
                    cv2.putText(frame, z["name"][:24].encode("ascii", "replace").decode(), (int(pts[0][0]) + 4, int(pts[0][1]) + 14),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.42, col, 1, cv2.LINE_AA)
            warm_boxes = []
            if CFG["thermal_alarm"] and CFG["detection_on"] and THERMAL is not None:
                warm_boxes = THERMAL.detect()                 # (x, y, w, h) 0..1 of the picture, already checked against the zones
                if warm_boxes:
                    present.add("warm"); self.last_warm = t0
                    for bx, by, bw, bh in warm_boxes:
                        p1 = (int(bx * W), int(by * H)); p2 = (int((bx + bw) * W), int((by + bh) * H))
                        cv2.rectangle(frame, p1, p2, (0, 140, 255), 3)
                        cv2.putText(frame, "WARM", (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)
                    if not self.warm_alerted:
                        self.warm_alerted = True
                        push_alert("warm", "warm", count=len(warm_boxes), source=STATE["source_label"])
                        siren_alarm("warm")
                        if self.notifier.prealarm(frame, "warm"):
                            log_event("person", "Thermal alarm: warm body in the zone - push message sent")
                        else:
                            log_event("person", "Thermal alarm: warm body in the zone" + ("" if is_armed() else " (disarmed - no alarm)"))
                elif self.warm_alerted and t0 - self.last_warm > 5.0:
                    self.warm_alerted = False
            STATE["warm"] = len(warm_boxes)
            if AUDIO is not None and AUDIO.noisy():
                present.add("noise")                      # relay trigger: loud noise at the microphone
            if CFG["diary_on"]:
                for lab in ("warm", "noise"):
                    if lab in present:
                        self.sights.see(lab, t0)
            self.sights.tick(t0)
            if is_armed() and present & {"person", "warm", "noise"}:
                light_alarm()                             # lights in "Auto" (after an alarm) switch on
            frame = apply_privacy(frame)                  # again after the overlays (thermal picture, boxes)
            if rec_clean is not None:                     # recordings / alarm pictures without the big red boxes (faces stay visible)
                if CFG["rec_marks"] == "thin":
                    for b_, col in [(b, (0, 0, 255)) for b in person_boxes] + [(o, (0, 200, 255)) for o in rec_animals]:
                        corner_marks(rec_clean, [int(b_[0] * sx), int(b_[1] * sy), int(b_[2] * sx), int(b_[3] * sy)], col)
                self.handle_recording(rec_clean, person_boxes)
            else:
                self.handle_recording(frame, person_boxes)
            self.relays.update(present)
            STATE["present"] = sorted(present); STATE["manual"] = manual_active()
            if "prealarm" in present:
                self.pre_last = t0
                if not self.pre_since:
                    self.pre_since = t0
                elif t0 - self.pre_since >= 0.5:
                    if not self.pre_alerted:                # one browser alarm per movement phase (5 s of calm ends it)
                        self.pre_alerted = True
                        push_alert("prealarm", "movement", source=STATE["source_label"])
                        siren_alarm("prealarm")
                    if CFG["notify_prealarm"] and self.notifier.prealarm(frame):
                        log_event("person", "Pre-alarm: movement - push message sent")
            else:
                self.pre_since = 0.0
                if self.pre_alerted and t0 - self.pre_last > 5.0:
                    self.pre_alerted = False

            if CFG["show_hud"]:
                hud = (f"{'RAIN MODE' if rain_mode else 'No rain'} | Wind: {STATE['wind_level']} x{STATE['wind_boost']} | "
                       f"Persons: {len(person_boxes)} | Pan {CFG['pan']:.0f}% Tilt {CFG['tilt']:.0f}% | {STATE['patrol_status']}"
                       + (f" | CPU {STATE['cpu']:.0f}%" if STATE["cpu"] is not None else "")
                       + (f" {STATE['cpu_temp']:.0f}C" if STATE["cpu"] is not None and STATE["cpu_temp"] is not None else "")
                       + (" | MANUAL" if STATE["manual"] else "")
                       + (" | IR" if CFG["thermal_on"] and STATE["thermal"] == "connected" else "")
                       + (f" | WiFi {STATE['wifi']['dbm']}dBm" if STATE["wifi"] and STATE["wifi"]["connected"] else "")
                       + (" | TIMELAPSE" if TL_HOLD["on"] else ""))
                cv2.rectangle(frame, (0, 0), (W, 34), (0, 0, 0), -1)
                cv2.putText(frame, hud, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 160, 255) if rain_mode else (230, 230, 230), 2)
                if STATE["recording"]:
                    cv2.circle(frame, (W - 24, 17), 8, (0, 0, 255), -1)

            self.frame_times.append(time.time() - t0)
            self.seen_t.append(t0)
            # 2.95.64: «fps» is the real number of pictures per second that are analysed (camera, simulator, power saving).
            # Before it was 1 / processing time - far too high with a slow source (simulator: 100 instead of 2.5), and the
            # auto-tuner then asked for up to 24 pictures of walking before a person counted: at low frame rates nobody did.
            span = self.seen_t[-1] - self.seen_t[0] if len(self.seen_t) >= 5 else 0.0
            proc_fps = 1.0 / max(1e-3, np.mean(self.frame_times))
            real_fps = (len(self.seen_t) - 1) / span if span > 0.2 else proc_fps
            with LOCK:
                STATE.update(rain_score=round(rain_score, 2), rain_mode=rain_mode, persons=len(person_boxes),
                             candidates=len(candidates), fps=round(min(real_fps, proc_fps), 1), proc_fps=round(proc_fps, 1),
                             frames=STATE["frames"] + 1, uptime=int(time.time() - START))
            frame = apply_privacy(frame)
            self.frame_out = frame
            DETER.check(present, t0)
            self._eco(present, t0)
            if CFG["web_stream"] and self.web_viewers > 0:
                out, ww = frame, int(CFG["web_width"])
                if W > ww:
                    out = cv2.resize(frame, (ww, int(H * ww / W)), interpolation=cv2.INTER_AREA)
                ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, int(CFG["web_quality"])])
                if ok:
                    self.jpeg = buf.tobytes(); self.jpeg_seq += 1


