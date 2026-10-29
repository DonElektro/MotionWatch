#@ Motion Watch – Teil 190: Relais, Wetter-Analyse, Auto-Tuner, Tracker. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Relays: each one Off / On / Auto. Auto = on while its trigger is in view (+ hold time)
# ----------------------------------------------------------------------------
TRIGGERS = (["person", "motion", "prealarm", "warm", "noise", "remote", "animal", "cat", "dog", "bird", "car", "truck", "bicycle", "motorcycle", "bus"]
            + sorted(set(COCO_LABELS.values()) - {"person", "cat", "dog", "bird", "car", "truck", "bicycle", "motorcycle", "bus"}))
ANIMALS = {COCO_LABELS[i] for i in range(16, 26)}
TRIGGER_EN = {"motion": "motion (anything)", "prealarm": "pre-alarm (any movement)", "warm": "warm body (thermal camera)",
              "noise": "noise (microphone)", "animal": "animal (any)",
               "remote": "remote access (somebody watches from outside)"}
RELAY_NOTE = ("Auto: the relay switches on while its trigger is in view and stays on for the hold time. "
              "Animal and object triggers (e.g. cat) need the AI model. "
              "Pre-alarm switches on at the first movement in the picture, long before a person is confirmed. "
              "Remote access switches on while somebody watches over Tailscale - also when disarmed (e.g. a small warning lamp).")


def tr_trigger(key, lang=None):
    return tr(TRIGGER_EN.get(key, key), lang)


def _clean_relay(r, i, used):
    """Validate one relay loaded from the settings file. Returns None if no GPIO is left."""
    out = {"name": f"Relay {i + 1}", "gpio": None, "mode": "off", "trigger": "person", "hold": 5.0, "active_low": False}
    if isinstance(r.get("name"), str) and r["name"].strip():
        out["name"] = r["name"].strip()[:24]
    g = r.get("gpio")
    if isinstance(g, int) and 2 <= g <= 27 and g not in GPIO_RESERVED and g not in used:
        out["gpio"] = g
    else:
        out["gpio"] = next((x for x in FREE_GPIOS if x not in used and x not in GPIO_RESERVED), None)
    if out["gpio"] is None:
        return None
    if r.get("mode") in ("off", "on", "auto"):
        out["mode"] = r["mode"]
    if r.get("trigger") in TRIGGERS:
        out["trigger"] = r["trigger"]
    try:
        h = float(r.get("hold", 5.0))
        if math.isfinite(h):
            out["hold"] = max(0.5, min(600.0, h))
    except (TypeError, ValueError):
        pass
    out["active_low"] = bool(r.get("active_low", False))
    return out


def relay_update(idx, field, value):
    """Validated change of one relay setting (desktop + web). Returns (ok, error_message)."""
    if not (isinstance(idx, int) and 0 <= idx < len(RELAYS)):
        return False, "unknown relay"
    r = RELAYS[idx]
    if field == "name":
        v = str(value).strip()[:24] or f"Relay {idx + 1}"
    elif field == "gpio":
        try:
            v = int(float(value))
        except (TypeError, ValueError):
            return False, "GPIO must be a number"
        if not 2 <= v <= 27:
            return False, "GPIO must be between 2 and 27"
        if v in GPIO_RESERVED:
            return False, f"GPIO {v} is used by a servo"
        if v in thermal_gpios():
            return False, f"GPIO {v} is used by the thermal camera"
        if f"gpio:{v}" in (CFG["light_white_out"], CFG["light_ir_out"]):
            return False, f"GPIO {v} is used by a light"
        if any(i != idx and o["gpio"] == v for i, o in enumerate(RELAYS)):
            return False, f"GPIO {v} is already used by another relay"
    elif field == "mode":
        if value not in ("off", "on", "auto"):
            return False, "mode must be off / on / auto"
        v = value
    elif field == "trigger":
        if value not in TRIGGERS:
            return False, "unknown trigger"
        v = value
    elif field == "hold":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False, "hold time must be a number"
        if not math.isfinite(v):
            return False, "hold time must be a number"
        v = max(0.5, min(600.0, v))
    elif field == "active_low":
        v = bool(value)
    else:
        return False, "unknown field"
    if r.get(field) == v:
        return True, ""
    with LOCK:
        r[field] = v
    if field in ("mode", "trigger", "gpio"):
        log_event("servo", f"{r['name']}: {field} -> {v}")
    save_settings()
    return True, ""


def relay_add():
    if len(RELAYS) >= MAX_RELAYS:
        return False, f"maximum {MAX_RELAYS} relays"
    used = {r["gpio"] for r in RELAYS}
    gpio = next((g for g in FREE_GPIOS if g not in used and g not in GPIO_RESERVED), None)
    if gpio is None:
        return False, "no free GPIO left"
    new = {"name": f"Relay {len(RELAYS) + 1}", "gpio": gpio, "mode": "off", "trigger": "cat", "hold": 10.0, "active_low": False}
    with LOCK:
        RELAYS.append(new)
    log_event("servo", f"{new['name']} added on GPIO{gpio}")
    save_settings()
    return True, ""


def relay_remove(idx):
    if not (isinstance(idx, int) and 0 <= idx < len(RELAYS)):
        return False, "unknown relay"
    with LOCK:
        r = RELAYS.pop(idx)
    log_event("servo", f"{r['name']} (GPIO{r['gpio']}) removed")
    save_settings()
    return True, ""


class RelayManager:
    """Decides every frame which relay is on: mode On / Off, or Auto = trigger in view (+ hold time)."""
    def __init__(self):
        self.last_seen = {}; self.was_on = {}

    def update(self, present):
        now = time.time()
        with LOCK:
            relays = list(RELAYS)
        if STATE.get("remote"):
            present = set(present) | {"remote"}
        states, out = [], []
        for r in relays:
            k = id(r)
            if PAUSING["on"]:
                on = False
            elif r["mode"] == "on":
                on = True
            elif r["mode"] == "auto":
                if not CFG["relays_on"] or (not is_armed() and r["trigger"] != "remote"):
                    on = False
                else:
                    if r["trigger"] in present:
                        self.last_seen[k] = now
                    on = now - self.last_seen.get(k, 0.0) < r["hold"]
            else:
                on = False
            if on != self.was_on.get(k, False):
                why = tr_trigger(r["trigger"], "en") if r["mode"] == "auto" else r["mode"]
                log_event("servo", f"{r['name']} (GPIO{r['gpio']}) {'ON' if on else 'OFF'} ({why})")
            self.was_on[k] = on
            states.append(on); out.append((r["gpio"], on, bool(r["active_low"])))
        STATE["relay_states"] = states
        STATE["relay_out"] = out
        STATE["relay"] = bool(states and states[0])




def class_color(cls):
    """Stable BGR colour per class. Hues avoid red, which is reserved for persons."""
    hsv = np.uint8([[[30 + (int(cls) * 37) % 110, 210, 255]]])
    b, g, r = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
    return int(b), int(g), int(r)


def draw_object(frame, obj, sx, sy):
    """Box + label for a generic detected object. obj = (x, y, w, h, conf, cls) in processing coords."""
    x, y, w, h, conf, cls = obj
    X, Y, BW, BH = int(x * sx), int(y * sy), int(w * sx), int(h * sy)
    col = class_color(cls)
    cv2.rectangle(frame, (X, Y), (X + BW, Y + BH), col, 2)
    sp = species_for((x, y, w, h)) if CFG["species_on"] and SPECIES["cache"] else None
    label = f"{sp[0]} {int(sp[1] * 100)}%" if sp else f"{COCO_LABELS.get(cls, 'object')} {int(conf * 100)}%"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(0, Y - th - 8)
    cv2.rectangle(frame, (X, top), (X + tw + 6, top + th + 8), col, -1)
    cv2.putText(frame, label, (X + 3, top + th + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)


def corner_marks(img, box, color):
    """Thin corner brackets around a box: shows where something is without covering it (e.g. the face)."""
    x, y, w, h = box
    L = max(6, int(min(w, h) * 0.22)); t = max(1, img.shape[1] // 640)
    for (cx, cy, dx, dy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        cv2.line(img, (cx, cy), (cx + dx * L, cy), color, t, cv2.LINE_AA)
        cv2.line(img, (cx, cy), (cx, cy + dy * L), color, t, cv2.LINE_AA)


def draw_outline(frame, contours, box, sx, sy, color, thickness):
    """Draw the silhouette contours that lie inside `box` (processing coords) onto the full frame."""
    x, y, w, h = box[:4]
    for c in contours:
        cx, cy, cw, ch = cv2.boundingRect(c)
        if cx + cw / 2 >= x and cx + cw / 2 <= x + w and cy + ch / 2 >= y and cy + ch / 2 <= y + h:
            pts = (c.reshape(-1, 2) * np.array([sx, sy])).astype(np.int32)
            cv2.polylines(frame, [pts], True, color, thickness, cv2.LINE_AA)


def merge_boxes(boxes, gap_x=12, gap_y=30):
    """Union boxes that touch or nearly touch (a person often splits into head/torso/legs)."""
    boxes = [list(b[:4]) for b in boxes]
    merged = True
    while merged and len(boxes) > 1:
        merged = False
        out = []
        while boxes:
            a = boxes.pop(0)
            i = 0
            while i < len(boxes):
                b = boxes[i]
                if (a[0] - gap_x < b[0] + b[2] and b[0] - gap_x < a[0] + a[2] and
                        a[1] - gap_y < b[1] + b[3] and b[1] - gap_y < a[1] + a[3]):
                    x1, y1 = min(a[0], b[0]), min(a[1], b[1])
                    x2, y2 = max(a[0] + a[2], b[0] + b[2]), max(a[1] + a[3], b[1] + b[3])
                    a = [x1, y1, x2 - x1, y2 - y1]; boxes.pop(i); merged = True
                else:
                    i += 1
            out.append(a)
        boxes = out
    return [tuple(int(v) for v in b) for b in boxes]


def iou(a, b):
    ax, ay, aw, ah = a[:4]; bx, by, bw, bh = b[:4]
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx)); iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    return inter / float(aw * ah + bw * bh - inter + 1e-6)


# ----------------------------------------------------------------------------
# Weather analysis
# ----------------------------------------------------------------------------
class WeatherAnalyzer:
    def __init__(self):
        self.prev_gray = None
        self.rain_hist = deque(maxlen=30)
        self.wind_hist = deque(maxlen=45)

    def rain(self, gray):
        if self.prev_gray is None:
            self.prev_gray = gray
            return 0.0
        diff = cv2.absdiff(gray, self.prev_gray)
        self.prev_gray = gray
        _, th = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
        vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        hk = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        streaks = cv2.subtract(cv2.morphologyEx(th, cv2.MORPH_OPEN, vk), cv2.morphologyEx(th, cv2.MORPH_OPEN, hk))
        n, _, stats, _ = cv2.connectedComponentsWithStats(streaks, 8)
        if n <= 1:
            score = 0.0
        else:
            areas = stats[1:, cv2.CC_STAT_AREA]
            tiny = np.sum((areas >= 3) & (areas <= 60))
            h, w = gray.shape
            cells = np.zeros((4, 4), np.uint8)
            cx = stats[1:, cv2.CC_STAT_LEFT] * 4 // w; cy = stats[1:, cv2.CC_STAT_TOP] * 4 // h
            cells[np.clip(cy, 0, 3), np.clip(cx, 0, 3)] = 1
            score = min(1.0, tiny / 160.0) * (0.4 + 0.6 * cells.mean())
        self.rain_hist.append(score)
        return float(np.mean(self.rain_hist))

    def wind(self, fg_mask, person_boxes):
        mask = fg_mask.copy()
        for (x, y, w, h) in person_boxes:
            mask[y:y + h, x:x + w] = 0
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        if n <= 1:
            score = 0.0
        else:
            areas = stats[1:, cv2.CC_STAT_AREA]
            small = areas[(areas >= 8) & (areas <= 900)]
            score = min(1.0, small.sum() / float(mask.size) * 25.0 + len(small) / 220.0)
        self.wind_hist.append(score)
        return float(np.mean(self.wind_hist))


# ----------------------------------------------------------------------------
# Auto-tuner
# ----------------------------------------------------------------------------
class AutoTuner:
    def __init__(self):
        self.reset()

    def reset(self):
        self.t_start = time.time(); self.calibrated = False
        self.noise_areas, self.noise_frac = [], []
        self.last_eval = time.time()
        self.new_candidates = self.became_person = self.near_miss = self.walkers = 0
        self.seen_ids = set()
        self.base_min_area = None
        STATE["auto_status"] = "calibrating…"
        log_event("auto", "Auto-tune: calibrating - keep the scene empty for a few seconds")

    @staticmethod
    def _set(key, value, why):
        value = round(value, 2) if isinstance(CFG[key], float) else int(value)
        if value != CFG[key]:
            old = CFG[key]; CFG[key] = value
            STATE["auto_changes"] += 1
            log_event("auto", f"Auto-tune: {key} {old} -> {value} ({why})")

    def observe(self, fg, tracks, persons, fps):
        if not CFG["auto_tune"]:
            STATE["auto_status"] = "off"; return
        if autotune_paused():                                   # 2.98.14: every measurement / training (312), not only three
            STATE["auto_status"] = "paused (test run)"; return   # 2.97.0: a measurement needs fixed values
        now = time.time()
        if fps > 1:
            self._set("walk_frames", max(4, min(24, round(fps * CFG["walk_seconds"]))), "fps")
        if not self.calibrated:
            n, _, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
            if n > 1:
                self.noise_areas.extend(stats[1:, cv2.CC_STAT_AREA].tolist())
            self.noise_frac.append(np.count_nonzero(fg) / float(fg.size))
            left = CFG["calib_seconds"] - (now - self.t_start)
            STATE["auto_status"] = f"calibrating… {max(0, left):.0f}s"
            if left <= 0:
                self.calibrated = True
                if self.noise_areas:
                    self._set("min_area", max(600, min(4000, float(np.percentile(self.noise_areas, 95)) * 2.5)), "scene noise")
                self.base_min_area = float(CFG["min_area"])
                frac = float(np.mean(self.noise_frac)) if self.noise_frac else 0.0
                if frac > 0.02:
                    self._set("sensitivity", max(10, CFG["sensitivity"] - 20), "noisy scene")
                elif frac < 0.001:
                    self._set("sensitivity", min(90, CFG["sensitivity"] + 10), "very quiet scene")
                STATE["auto_status"] = "tuned"
                log_event("auto", "Auto-tune: calibration done, now adjusting live")
            return
        for t in tracks:
            # 2.98.13: something that walks steadily somewhere is no «false blob» even when it is not a person (yet) - before,
            # every person that was not recognised made the minimum size bigger, until no person was recognised at all
            walker = len(t.speeds) >= 4 and t.steadiness() >= 0.3 and t.speed() >= CFG["walk_min_speed"]
            if not getattr(t, "_seen", False) and not walker and t.age >= 2:
                t._seen = True; self.new_candidates += 1
            elif walker and not getattr(t, "_walker", False):
                t._walker = True; self.walkers += 1
            if t.is_person and not getattr(t, "_counted", False):
                t._counted = True; self.became_person += 1
            if (not t.is_person and not t.is_vehicle and t.age >= CFG["walk_frames"]
                    and CFG["walk_min_speed"] <= t.speed() <= CFG["walk_max_speed"] * fps_k()
                    and 0.3 <= t.steadiness() < CFG["speed_consistency"]):
                self.near_miss += 1
        if now - self.last_eval < 10:
            return
        minutes = (now - self.last_eval) / 60.0
        self.last_eval = now
        false_rate = (self.new_candidates - self.became_person) / minutes
        if not persons:
            if false_rate > 25 and self.walkers == 0:              # 2.98.13: not while somebody walks; at most 2.5 × the calibrated size
                cap = min(8000, 2.5 * (self.base_min_area or CFG["min_area"]))
                self._set("min_area", min(cap, CFG["min_area"] * 1.2), f"{false_rate:.0f} false blobs/min")
            elif false_rate > 12:
                self._set("sensitivity", max(10, CFG["sensitivity"] - 5), "many false blobs")
            elif false_rate < 2 and self.became_person == 0:
                self._set("min_area", max(500, CFG["min_area"] * 0.93), "scene calm, more sensitive")
        if self.near_miss > 20 and self.became_person == 0:
            self._set("speed_consistency", max(0.3, CFG["speed_consistency"] - 0.05), "steady walkers not passing")
        elif self.became_person > 0 and false_rate < 5:
            self._set("speed_consistency", min(0.7, CFG["speed_consistency"] + 0.02), "persons detected, tightening")
        STATE["auto_status"] = f"tuned · {false_rate:.0f} false/min"
        self.new_candidates = self.became_person = self.near_miss = self.walkers = 0


# ----------------------------------------------------------------------------
# Tracker
# ----------------------------------------------------------------------------
def fps_k():
    """2.95.65: the speed limits (pixels per picture) were made for about 12 pictures per second. With fewer pictures
    (power saving, night, a slow simulator) a walking person moves much further from one picture to the next - before it
    then counted as a vehicle and was ignored, or the tracker lost it. Factor 1 … 6 for these limits."""
    fps = float(STATE.get("fps") or 0)
    return max(1.0, min(6.0, 12.0 / fps)) if fps > 0.5 else 1.0


class Track:
    _next = 1

    def __init__(self, box):
        self.id = Track._next; Track._next += 1
        self.box = box
        self.hist = deque(maxlen=40); self.speeds = deque(maxlen=40)
        self.hist.append(self.center())
        self.lost = 0; self.age = 0; self.born = time.time(); self.start = self.center()
        self.is_person = self.is_vehicle = self.ai_confirmed = False

    def center(self):
        x, y, w, h = self.box
        return (x + w / 2.0, y + h / 2.0)

    def update(self, box):
        old = self.center(); self.box = box; c = self.center()
        self.hist.append(c); self.speeds.append(math.hypot(c[0] - old[0], c[1] - old[1]))
        self.lost = 0; self.age += 1

    def speed(self):
        return float(np.mean(self.speeds)) if self.speeds else 0.0

    def steadiness(self):
        if len(self.speeds) < 4:
            return 0.0
        sp = np.array(self.speeds)
        if sp.mean() < 1e-3:
            return 0.0
        cv = sp.std() / sp.mean()
        pts = np.array(self.hist)
        path = np.sum(np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))) + 1e-6
        net = math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
        return float(max(0.0, 1.0 - cv * 0.6) * (0.3 + 0.7 * net / path))


class Tracker:
    def __init__(self):
        self.tracks = []

    def update(self, boxes, max_dist=60):
        max_dist = max_dist * fps_k()                             # 2.95.65: fewer pictures -> bigger steps between them
        unmatched = list(range(len(boxes)))
        for t in self.tracks:
            best, bd = None, max_dist
            tc = t.center()
            for i in unmatched:
                x, y, w, h = boxes[i]
                d = math.hypot(x + w / 2 - tc[0], y + h / 2 - tc[1])
                if d < bd:
                    best, bd = i, d
            if best is not None:
                t.update(boxes[best]); unmatched.remove(best)
            else:
                t.lost += 1
        for i in unmatched:
            self.tracks.append(Track(boxes[i]))
        self.tracks = [t for t in self.tracks if t.lost < 8]
        return self.tracks


