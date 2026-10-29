#@ MoveEye – Teil 255: Wecker mit Schlafplatz und Gesten (2.98.7). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Idea of Daniel's daughter: MoveEye stands somewhere in the room. While you sleep the camera looks away (a set direction,
# e.g. the door). When the alarm rings it turns to the sleeping place and understands two gestures:
#   wave (hand to and fro)  -> snooze (again after N minutes)
#   sit up / get up         -> alarm off
# The sleeping place is a zone of the kind "sleep" (zone editor): it is covered in black in every picture, in every direction
# of the camera (030: sleep_polys). Only the gesture detection here gets the picture of the bed - small, grey, in memory,
# only while the alarm rings, never stored or sent.
# ----------------------------------------------------------------------------
WAKE = {"state": "off", "due": 0.0, "until": 0.0, "t0": 0.0, "snoozes": 0, "done": 0.0, "msg": "", "gest": "", "gest_t": 0.0,
        "test": False, "light_prev": None, "light_t": 0.0, "snd_t": 0.0, "level": 0.0, "last": "", "pos_t": 0.0}
WAKE_LOCK = threading.Lock()
WAKE_DAYS = {"all": (0, 1, 2, 3, 4, 5, 6), "mon-fri": (0, 1, 2, 3, 4), "sat-sun": (5, 6), "sun-thu": (6, 0, 1, 2, 3), "once": (0, 1, 2, 3, 4, 5, 6)}
_HM_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _hm(s):
    m = _HM_RE.match(str(s or "").strip())
    return (int(m.group(1)), int(m.group(2))) if m else None


def wake_next(now=None):
    """the next moment the alarm rings (timestamp) or 0"""
    if not CFG.get("wake_on"):
        return 0.0
    hm = _hm(CFG.get("wake_time"))
    if hm is None:
        return 0.0
    now = time.time() if now is None else now
    days = WAKE_DAYS.get(CFG.get("wake_days"), WAKE_DAYS["all"])
    d0 = datetime.fromtimestamp(now)
    for k in range(0, 9):
        d = (d0 + timedelta(days=k)).replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        if d.weekday() in days and d.timestamp() > now:
            return d.timestamp()
    return 0.0


def wake_sleep_from(due):
    """when the night before the alarm `due` starts (the camera looks away from then on) - 0 = not wanted.
    2.98.9: the ONE night time of MoveEye (report_from, Einstellungen → Nachtbericht) - also for the night report and
    «Heute Nacht bewachen»."""
    if not CFG.get("wake_away_night", True) or not due:
        return 0.0
    d = datetime.fromtimestamp(due)
    s = d.replace(hour=int(CFG.get("report_from", 22)) % 24, minute=0, second=0, microsecond=0)
    if s >= d:
        s -= timedelta(days=1)
    return s.timestamp()


def bed_zone():
    zs = sleep_zones()
    return zs[0] if zs else None


def _pct(deg, axis):
    return max(0.0, min(100.0, 50.0 + deg / servo_half(axis) * 50.0))


def bed_view():
    """(pan %, tilt %) that looks at the middle of the sleeping place, or None"""
    z = bed_zone()
    if not z:
        return None
    a = sum(p[0] for p in z["ang"]) / len(z["ang"]); e = sum(p[1] for p in z["ang"]) / len(z["ang"])
    return round(_pct(a, "pan"), 2), round(_pct(e, "tilt"), 2)


def away_view():
    p, t = float(CFG.get("wake_away_pan", -1)), float(CFG.get("wake_away_tilt", -1))
    return (p, t) if 0 <= p <= 100 and 0 <= t <= 100 else None


def wake_clap_listens():
    """2.98.9: while the alarm rings, clapping 2 times = snooze (the melody pauses 8 s of every 20 s so the microphone hears it)"""
    sim_ear = AUDIO is not None and time.time() - AUDIO.sim_t < 3.0        # 2.98.11: the simulator supplies the sound
    return WAKE["state"] == "ring" and bool(CFG.get("wake_clap", True)) and (bool(CFG.get("audio_in")) or sim_ear)


def wake_hold():
    """the wake-up alarm holds the head (sleeping: looks away, ringing: looks at the bed) - tracking, patrol and the
    timelapse leave it alone"""
    return WAKE["state"] in ("sleep", "ring", "snooze")


def _look(pos):
    if pos and not manual_active() and (abs(CFG["pan"] - pos[0]) > 0.3 or abs(CFG["tilt"] - pos[1]) > 0.3):
        CFG["pan"], CFG["tilt"] = float(pos[0]), float(pos[1])
        WAKE["pos_t"] = time.time()


def _light(on):
    if not CFG.get("wake_light"):
        return
    try:
        if on:
            if WAKE["light_prev"] is None:
                WAKE["light_prev"] = CFG.get("light_white") or "auto"
            light_set("white", "on")
        elif WAKE["light_prev"] is not None:
            light_set("white", WAKE["light_prev"])
            WAKE["light_prev"] = None
        WAKE["light_t"] = time.time()
    except Exception as e:
        log_event("sys", f"Wake-up light: {e}")


def _ring_sound(now):
    """the melody again every 20 s, a little louder each time (from 40 % up to the set volume in about 2 minutes)"""
    if now - WAKE["snd_t"] < 20.0:
        return
    WAKE["snd_t"] = now
    full = float(CFG.get("wake_volume", 60))
    WAKE["level"] = min(full, max(full * 0.4, WAKE["level"] + full * 0.1)) if WAKE["level"] else full * 0.4
    kind = CFG.get("wake_sound") or "chime"
    ok, err = sound_play(kind, 12.0 if wake_clap_listens() else 19.0, WAKE["level"], reason="wake-up alarm")
    if not ok:
        WAKE["msg"] = err


def wake_ring(test=False, who="time"):
    with WAKE_LOCK:
        WAKE.update(state="ring", t0=time.time(), test=bool(test), snd_t=0.0, level=0.0, gest="", until=0.0)
    WAKEG.reset()
    MANUAL["until"] = 0.0                                  # the alarm wins over a hand-moved camera
    _look(bed_view())
    _light(True)
    log_event("sys", "Wake-up alarm rings" + (" (test)" if test else "") + f" ({who})")


def wake_snooze(who="web"):
    if WAKE["state"] != "ring":
        return False, "the alarm does not ring"
    sound_stop()
    _light(False)
    mins = float(CFG.get("wake_snooze", 9))
    with WAKE_LOCK:
        WAKE.update(state="snooze", until=time.time() + mins * 60.0, snoozes=WAKE["snoozes"] + 1, last=f"snooze ({who})")
    MANUAL["until"] = 0.0
    _look(away_view())
    log_event("sys", f"Wake-up alarm: snooze {mins:g} min ({who})")
    return True, ""


def wake_stop(who="web"):
    if WAKE["state"] not in ("ring", "snooze", "sleep"):
        return False, "the alarm is not on"
    was = WAKE["state"]
    sound_stop()
    _light(False)
    with WAKE_LOCK:
        if was in ("ring", "snooze"):
            WAKE["done"] = WAKE["due"] or time.time()
        WAKE.update(state="off", until=0.0, test=False, last=f"off ({who})", snoozes=0)
    if was in ("ring", "snooze") and CFG.get("wake_days") == "once" and not WAKE.get("test"):
        CFG["wake_on"] = False; save_settings()
    log_event("sys", f"Wake-up alarm off ({who})")
    return True, ""


def wake_sleep_now(who="web"):
    """«Gute Nacht»: look away now (until the alarm)"""
    if not WAKE["due"]:
        return False, "no alarm set"
    WAKE["state"] = "sleep"; WAKE["sleep_now"] = WAKE["due"]
    _look(away_view())
    log_event("sys", f"Wake-up alarm: good night - the camera looks away ({who})")
    return True, ""


def wake_tick():
    """once a second (Scheduler thread)"""
    now = time.time()
    st = WAKE["state"]
    if st in ("off", "sleep"):
        due = wake_next(now - 90.0)                          # an alarm of the last 90 s still rings (a busy second is not lost)
        if due and due <= WAKE["done"] + 1.0:
            due = wake_next(max(now, WAKE["done"] + 1.0))
        WAKE["due"] = due
        if due and now >= due and due > WAKE["done"]:
            wake_ring(False, "time")
            return
        sf = wake_sleep_from(due)
        night = bool(due) and ((sf and sf <= now < due) or WAKE.get("sleep_now") == due)
        if night and away_view() is not None:
            if st != "sleep":
                log_event("sys", "Wake-up alarm: night - the camera looks away from the sleeping place")
            WAKE["state"] = "sleep"
            _look(away_view())
        elif st == "sleep":
            WAKE["state"] = "off"
        return
    if st == "snooze":
        _look(away_view())
        if now >= WAKE["until"]:
            wake_ring(WAKE["test"], "snooze over")
        return
    if st == "ring":
        _look(bed_view())
        _ring_sound(now)
        g = WAKE.get("gest") if now - WAKE.get("gest_t", 0.0) < 3.0 else ""
        if g == "wave":
            WAKE["gest"] = ""; wake_snooze("gesture: waving")
        elif g == "up":
            WAKE["gest"] = ""; wake_stop("gesture: got up")
        elif now - WAKE["t0"] > float(CFG.get("wake_ring_max", 15)) * 60.0:
            wake_stop("nobody reacted")
            try:
                w_ = WATCH_REF.get("w")
                if w_ is not None:
                    w_.notifier.alert("{name}: " + tr("Wake-up alarm"), tr("The alarm rang without a reaction and stopped by itself."), None)
            except Exception:
                pass


def wake_state(lang=None):
    z = bed_zone()
    return {"on": bool(CFG.get("wake_on")), "state": WAKE["state"], "due": int(WAKE["due"] or wake_next()), "until": int(WAKE["until"]),
            "snoozes": WAKE["snoozes"], "bed": bool(z), "bed_name": (z or {}).get("name", ""), "away": away_view() is not None,
            "gest": WAKE.get("gest_show", ""), "last": WAKE["last"], "msg": WAKE["msg"], "spk": bool(out_selected()),
            "sleep_from": int(wake_sleep_from(WAKE["due"] or wake_next())), "gestures": bool(CFG.get("wake_gestures", True))}


class WakeGestures:
    """2.98.7: two gestures in the picture of the sleeping place while the alarm rings - without any AI model, also in the
    dark (infrared): the difference between two pictures shows what moves.
      waving  = a small moving area whose middle goes to and fro (3 turns in 3 s; at a low frame rate: moving most of
                the time over 2 s with a clear sideways range)
      getting up = a big part of the bed and of the area above it moves for more than ~1.5 s
    The first 2 s after the head turned or the light went on are ignored (everything changes then)."""
    W = 320

    def __init__(self):
        self.reset()

    def reset(self):
        self.prev = None; self.hist = deque(); self.t0 = time.time(); self.roi = None
        self.base = None; self.changed_t = 0.0                  # the picture of the bed when it started to ring (sitting up = differs)

    def _roi(self, w, h):
        z = bed_zone()
        if not z:
            return None
        pp = sleep_project(z["ang"], CFG["pan"], CFG["tilt"])
        if not pp:
            return None
        xs = [p[0] for p in pp]; ys = [p[1] for p in pp]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        bw, bh = x1 - x0, y1 - y0
        x0 -= bw * 0.15; x1 += bw * 0.15; y0 -= bh * 0.8          # above the bed: sitting up, a raised hand
        x0, x1 = max(0.0, x0), min(1.0, x1); y0, y1 = max(0.0, y0), min(1.0, y1)
        if x1 - x0 < 0.05 or y1 - y0 < 0.05:
            return None
        return int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)

    def feed(self, frame, now=None):
        """frame: BGR picture before the privacy mask. Returns "wave", "up" or ""."""
        if not CFG.get("wake_gestures", True) or frame is None:
            return ""
        now = time.time() if now is None else now
        H, W = frame.shape[:2]
        h = int(H * self.W / W)
        g = cv2.cvtColor(cv2.resize(frame, (self.W, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        roi = self._roi(self.W, h)
        if roi is None:
            self.prev = None
            return ""
        x0, y0, x1, y1 = roi
        r = cv2.GaussianBlur(g[y0:y1, x0:x1], (5, 5), 0).astype(np.float32)
        if self.prev is not None and self.prev.shape == r.shape and float(cv2.absdiff(r, self.prev).max()) < 1.5:
            return ""                                          # the same picture again (the camera is slower than the loop)
        prev, self.prev = self.prev, r
        quiet = max(WAKE.get("pos_t", 0.0), WAKE.get("light_t", 0.0), float(SERVO_MOVE.get("t", 0.0)), self.t0)
        if prev is None or prev.shape != r.shape or now - quiet < 2.0:
            self.hist.clear(); self.base = None; self.changed_t = 0.0
            return ""
        if self.base is None or self.base.shape != r.shape:
            self.base = r.copy()
        thr = max(6.0, 0.035 * float(prev.mean()))            # little contrast (infrared, a washed-out bright room): a low threshold
        m = (cv2.absdiff(r, prev) > thr).astype(np.uint8)
        m = cv2.dilate(cv2.erode(m, np.ones((2, 2), np.uint8)), np.ones((3, 3), np.uint8))   # no single grains, thin arms stay
        frac = float(m.mean())
        if frac > 0.85:                                        # everything changed (light, a jolt): not a gesture
            self.hist.clear()
            return ""
        cx = None
        if frac > 0.0012:                                      # the biggest moving thing (not the moths at the lamp, not the grain)
            nl, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
            if nl > 1:
                j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
                frac = float(st[j, cv2.CC_STAT_AREA]) / float(m.size)
                cx = float(cen[j][0]) / max(1, m.shape[1])
            if frac <= 0.0012:
                cx = None
        self.hist.append((now, cx, frac))
        while self.hist and now - self.hist[0][0] > 4.0:
            self.hist.popleft()
        # sitting up / out of bed: the picture stays different from the one when it began to ring (and nothing moves now)
        bd = (cv2.absdiff(r - float(r.mean()), self.base - float(self.base.mean())) > thr * 1.5).astype(np.uint8)   # brightness drift (exposure) does not count
        bfrac = float(cv2.morphologyEx(bd, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).mean())
        self.bfrac = bfrac
        if bfrac > 0.03 and frac < 0.01:
            if not self.changed_t:
                self.changed_t = now
            elif now - self.changed_t >= 2.5:
                return "up"
        elif bfrac <= 0.03:
            self.changed_t = 0.0
        return self._judge(now)

    @staticmethod
    def _turns(cs, step=0.03):
        turns, d, ref = 0, 0, cs[0]
        for c in cs[1:]:
            if abs(c - ref) >= step:
                s = 1 if c > ref else -1
                if d and s != d:
                    turns += 1
                d, ref = s, c
        return turns

    def _judge(self, now):
        """2.98.9: measured in the 3D simulator (bedroom scene, 2-3 pictures per second, 4 m away): the arm is small in the
        picture, getting up is a path across the picture rather than a big area"""
        H_ = list(self.hist)
        n_all = max(1, len(H_))
        pts = [(t, c, f) for t, c, f in H_ if c is not None]
        if not pts:
            return ""
        cs = [c for _t, c, _f in pts]
        span = pts[-1][0] - pts[0][0]
        rng = max(cs) - min(cs)
        moving = len(pts) / n_all
        meanf = sum(f for _t, _c, f in pts) / len(pts)
        turns = self._turns(cs)
        # getting up: a big moving area for 1.2 s, or something big enough travels across (out of the bed)
        big = [(t, f) for t, _c, f in pts if now - t <= 2.5 and f > 0.12]
        if len(big) >= 3 and big[-1][0] - big[0][0] >= 1.2:
            return "up"
        if span >= 2.0 and moving >= 0.6 and meanf >= 0.008 and abs(cs[-1] - cs[0]) >= 0.3 and turns <= 1:
            return "up"
        # waving: a small area going to and fro in one place - and the bed looks as before (sitting up changes it a lot)
        if len(pts) >= 4 and meanf < 0.025 and rng < 0.5 and getattr(self, "bfrac", 0.0) < 0.03:
            if turns >= 3:
                return "wave"
            if span >= 2.0 and moving >= 0.6 and meanf < 0.025 and rng < 0.35 and abs(cs[-1] - cs[0]) < 0.2 and len(pts) <= 14:
                return "wave"                                   # few pictures per second: the hand moves on and on in one place
        return ""


WAKEG = WakeGestures()


def wake_feed(frame):
    """from the main loop, before the privacy mask - only while the alarm rings"""
    if WAKE["state"] != "ring":
        return
    try:
        g = WAKEG.feed(frame)
    except Exception as e:
        log_event("sys", f"Wake-up gestures: {e}")
        return
    if g:
        WAKE["gest"] = g; WAKE["gest_t"] = time.time()
        WAKE["gest_show"] = g
        WAKEG.hist.clear()


def wake_text(lang=None):
    """one status line (window and web page)"""
    lang = norm_lang(lang or CFG["lang"])
    st = WAKE["state"]
    hm = lambda ts: datetime.fromtimestamp(ts).strftime("%H:%M")
    if st == "ring":
        return "🔔 " + tr("rings", lang) + (" – " + tr("wave = snooze, sit up = off", lang) if CFG.get("wake_gestures", True) else "")
    if st == "snooze":
        return "😴 " + tr("snoozing until", lang) + " " + hm(WAKE["until"])
    if st == "sleep":
        return "🌙 " + tr("night: the camera looks away until", lang) + " " + hm(WAKE["due"])
    if not CFG.get("wake_on"):
        return tr("off", lang)
    due = WAKE["due"] or wake_next()
    days = {"de": "Mo Di Mi Do Fr Sa So", "rm": "Gli Ma Me Gie Ve So Du", "fr": "lu ma me je ve sa di", "it": "lu ma me gi ve sa do"}.get(lang, "Mon Tue Wed Thu Fri Sat Sun").split()
    txt = (tr("next alarm", lang) + ": " + days[datetime.fromtimestamp(due).weekday()] + " " + hm(due)) if due else tr("no time set", lang)
    warn = []
    if not bed_zone():
        warn.append(tr("no sleeping place yet (Zones → + Sleeping place)", lang))
    if away_view() is None and CFG.get("wake_away_night", True):
        warn.append(tr("no direction for the night yet (button «Look here at night»)", lang))
    if not out_selected():
        warn.append(tr("no loudspeaker selected", lang))
    return txt + ("".join(" · ⚠ " + w for w in warn))


def wake_away_here(who="web"):
    CFG["wake_away_pan"] = round(float(CFG["pan"]), 2); CFG["wake_away_tilt"] = round(float(CFG["tilt"]), 2)
    save_settings()
    log_event("sys", f"Wake-up alarm: direction for the night = pan {CFG['pan']:.0f} %, tilt {CFG['tilt']:.0f} % ({who})")
    return True, ""


def wake_action(a, who="web"):
    """web / window / MQTT: test | snooze | stop | away_here | sleep_now"""
    if a == "test":
        if not bed_zone():
            return False, "no sleeping place yet (Zones → + Sleeping place)"
        wake_ring(True, who); return True, ""
    if a == "snooze":
        return wake_snooze(who)
    if a == "stop":
        return wake_stop(who)
    if a == "away_here":
        return wake_away_here(who)
    if a == "sleep_now":
        return wake_sleep_now(who)
    return False, "unknown action"
