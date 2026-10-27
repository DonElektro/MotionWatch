#@ Motion Watch – Teil 220: Zeitraffer. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Timelapse: every N minutes the camera drives to a chosen position, waits until the picture is calm and saves a photo.
# An alarm (person seen, recording running, tracking) always has priority: then nothing moves, and the photo is taken
# only after the alarm is over. Photos: <recordings>/timelapse/tl_YYYYmmdd_HHMMSS.jpg   videos: tlv_*.mp4 in the same folder.
# ----------------------------------------------------------------------------
TL_HOLD = {"on": False}                          # True while the camera is parked for a photo: the patrol must not move it
TL_PHOTO_RE = re.compile(r"^tl_(\d{8})_(\d{6})\.jpg$")
TL_VIDEO_RE = re.compile(r"^tlv_[0-9A-Za-z_\-]{1,40}\.mp4$")
_TL_RENDER_LOCK = threading.Lock()


def servo_hold():
    """Something other than tracking is holding the servos (hand control, timelapse position)."""
    return manual_active() or TL_HOLD["on"]


def tl_dir():
    return os.path.join(os.path.abspath(CFG["record_dir"]), "timelapse")


def tl_photos(day=""):
    try:
        names = sorted(n for n in os.listdir(tl_dir()) if TL_PHOTO_RE.match(n) and (not day or n[3:11] == day))
    except OSError:
        names = []
    return names


def tl_overview():
    photos = tl_photos(); days = {}
    for n in photos:
        days[n[3:11]] = days.get(n[3:11], 0) + 1
    videos = []
    try:
        for n in sorted(os.listdir(tl_dir()), reverse=True):
            if TL_VIDEO_RE.match(n):
                st = os.stat(os.path.join(tl_dir(), n))
                videos.append({"name": n, "size": st.st_size, "time": int(st.st_mtime)})
    except OSError:
        pass
    return {"count": len(photos), "latest": photos[-1] if photos else "", "videos": videos[:30],
            "days": [{"day": d, "count": c} for d, c in sorted(days.items(), reverse=True)[:60]],
            "status": STATE["timelapse"], "render": STATE["timelapse_render"], "on": bool(CFG["timelapse_on"])}


def tl_path(name):
    """Absolute path of a timelapse photo / video (guards against path tricks), or None."""
    if not isinstance(name, str) or not (TL_PHOTO_RE.match(name) or TL_VIDEO_RE.match(name)):
        return None
    p = os.path.join(tl_dir(), name)
    return p if os.path.isfile(p) else None


def tl_cleanup():
    limit = CFG["timelapse_max_gb"] * 1024 ** 3
    try:
        files = [(n, os.path.getsize(os.path.join(tl_dir(), n))) for n in os.listdir(tl_dir()) if TL_PHOTO_RE.match(n)
                 and not _read_sidecar("timelapse/" + n).get("fav")]          # starred photos stay
    except OSError:
        return
    files.sort()
    total = sum(sz for _n, sz in files); removed = 0
    while total > limit and len(files) > 1:
        n, sz = files.pop(0)
        try:
            os.remove(os.path.join(tl_dir(), n)); total -= sz; removed += 1
        except OSError:
            break
    if removed:
        log_event("servo", f"Cleanup: {removed} old photo(s) deleted")


class Timelapse:
    """State machine, called once per camera frame with the untouched picture.
       idle -> (interval over, no alarm) -> moving (camera driven to the position, settle time) -> photo -> idle."""
    def __init__(self):
        self.state = "idle"; self.t = 0.0; self.last_shot = 0.0; self.saved = None; self.target = None; self.pending_now = False

    def request_now(self):
        self.pending_now = True

    def _back(self):
        """Drive back to where the camera was - but only if nobody (tracking, hand control) has moved it since."""
        if CFG["timelapse_return"] and self.saved and self.target and abs(CFG["pan"] - self.target[0]) < 1 and abs(CFG["tilt"] - self.target[1]) < 1:
            CFG["pan"], CFG["tilt"] = self.saved

    def _abort(self, why):
        self._back()
        TL_HOLD["on"] = False; self.state = "idle"
        log_event("servo", f"Photo postponed: {why}")

    def update(self, frame, alarm):
        now = time.time()
        if not CFG["timelapse_on"] and not self.pending_now:
            if self.state != "idle":
                self._back(); TL_HOLD["on"] = False; self.state = "idle"
            STATE["timelapse"] = "off"
            return
        busy = alarm or manual_active()
        if self.state == "idle":
            due = self.pending_now or now - self.last_shot >= CFG["timelapse_interval"] * 60.0
            if not due:
                STATE["timelapse"] = f"next photo in {int(max(1, (self.last_shot + CFG['timelapse_interval'] * 60.0 - now) / 60.0 + 0.5))} min"
                return
            if busy:
                STATE["timelapse"] = "waiting: alarm has priority" if alarm else "waiting: manual control"
                return
            tp = float(max(0.0, min(100.0, CFG["timelapse_pan"]))); tt = float(max(0.0, min(100.0, CFG["timelapse_tilt"])))
            self.saved = (CFG["pan"], CFG["tilt"]); self.target = (tp, tt)
            TL_HOLD["on"] = True
            CFG["pan"], CFG["tilt"] = tp, tt
            self.state = "moving"; self.t = now
            log_event("servo", f"Driving to the photo position (pan {tp:.0f}%, tilt {tt:.0f}%)")
            STATE["timelapse"] = "moving to the photo position"
            return
        # state == "moving": the alarm may start at any time and wins immediately
        if busy:
            self._abort("alarm" if alarm else "manual control")
            STATE["timelapse"] = "waiting: alarm has priority" if alarm else "waiting: manual control"
            return
        if now - self.t < CFG["timelapse_settle"]:
            STATE["timelapse"] = "moving to the photo position"
            return
        self._shoot(frame, now)

    def _shoot(self, frame, now):
        try:
            os.makedirs(tl_dir(), exist_ok=True)
            name = datetime.now().strftime("tl_%Y%m%d_%H%M%S.jpg")
            ok = cv2.imwrite(os.path.join(tl_dir(), name), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if ok:
                gps_tag_jpg(os.path.join(tl_dir(), name))
        except (OSError, cv2.error) as e:
            ok, name = False, ""
            log_event("servo", f"Photo could not be saved: {e}")
        self.last_shot = now; self.pending_now = False
        if ok:
            STATE["timelapse_last"] = name
            log_event("servo", f"Photo saved: {name}")
            tl_cleanup()
        self._back()
        TL_HOLD["on"] = False; self.state = "idle"
        STATE["timelapse"] = "photo saved"


def timelapse_render(day="", fps=None):
    """Make a video from the photos of one day (or all). Runs in the background; progress is in STATE['timelapse_render']."""
    day = day if isinstance(day, str) and re.fullmatch(r"\d{8}", day) else ""
    try:
        fps = max(5.0, min(60.0, float(fps if fps is not None else CFG["timelapse_fps"])))
    except (TypeError, ValueError):
        fps = 25.0
    files = tl_photos(day)[-20000:]
    if len(files) < 2:
        return False, "need at least 2 photos"
    if not _TL_RENDER_LOCK.acquire(blocking=False):
        return False, "a video is already being made"

    def work():
        enc_before = STATE["recording_enc"]
        try:
            first = cv2.imread(os.path.join(tl_dir(), files[0]))
            if first is None:
                STATE["timelapse_render"] = "error: first photo unreadable"; return
            h, w = first.shape[:2]
            name = f"tlv_{day or 'all'}_{datetime.now().strftime('%H%M%S')}.mp4"
            path = os.path.join(tl_dir(), name)
            writer, _codec = open_writer(path, fps, (w, h))
            if writer is None:
                STATE["timelapse_render"] = "error: no video encoder available"; return
            for i, n in enumerate(files):
                img = cv2.imread(os.path.join(tl_dir(), n))
                if img is None:
                    continue
                if img.shape[:2] != (h, w):
                    img = cv2.resize(img, (w, h))
                writer.write(img)
                if hasattr(writer, "q"):
                    while writer.q.qsize() > 30:                 # the ffmpeg pipe drops frames when it is full: wait for it
                        time.sleep(0.01)
                STATE["timelapse_render"] = f"making video {i + 1}/{len(files)}"
            writer.release()
            STATE["timelapse_render"] = "video ready: " + name
            log_event("servo", f"Video made: {name} ({len(files)} photos, {fps:.0f} fps)")
        except Exception as e:
            STATE["timelapse_render"] = "error: " + str(e)[:100]
        finally:
            STATE["recording_enc"] = enc_before
            _TL_RENDER_LOCK.release()
    STATE["timelapse_render"] = "making video 0/" + str(len(files))
    threading.Thread(target=work, daemon=True).start()
    return True, ""


