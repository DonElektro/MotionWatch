#@ Motion Watch – Teil 030: Zonen, Anwesenheit, Text-Einstellungen, Zeitpläne. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Zones: polygons on the picture (normalised 0..1). "ignore" = detections whose feet are inside are dropped,
# "only" = when at least one such zone exists, only detections inside it count.
# ----------------------------------------------------------------------------
MAX_ZONES = 12
ZONES = []              # [{"id", "name", "mode": "ignore"|"only"|"privacy", "points": [[x, y], ...], "kinds": "person"|"animal" (optional)}]
# "privacy" = the area is painted black right after the camera, before anything else sees it: live picture, recordings,
# snapshots, timelapse, detection and the zone editor never contain it (neighbour's tent, a path, a window).
# 2.98.7: "sleep" = the sleeping place - a privacy zone that stays on the bed when the head turns: its corners are kept as
# directions (degrees, "ang") and drawn into every picture for the direction the camera has (and had in the last 2 s, the
# picture comes a little later than the servo moves). The wake-up alarm turns the camera to it.


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _clean_zone(z, i):
    if not isinstance(z, dict):
        return None
    pts = []
    for p in (z.get("points") or [])[:40] if isinstance(z.get("points"), list) else []:
        if isinstance(p, (list, tuple)) and len(p) == 2 and _num(p[0]) and _num(p[1]):
            pts.append([round(min(1.0, max(0.0, float(p[0]))), 4), round(min(1.0, max(0.0, float(p[1]))), 4)])
    mode = z.get("mode") if z.get("mode") in ("only", "privacy", "line", "loiter", "sleep") else "ignore"
    if mode == "line":
        if len(pts) < 2:
            return None
        pts = pts[:2]
    elif len(pts) < 3:
        return None
    zid = str(z.get("id") or "")
    out = {"id": zid if re.fullmatch(r"[0-9a-f]{8}", zid) else uuid.uuid4().hex[:8],
           "name": str(z.get("name") or "").strip()[:40] or f"Zone {i + 1}", "mode": mode, "points": pts}
    if mode == "line":
        out["dir"] = z.get("dir") if z.get("dir") in ("ab", "ba") else "both"
    if mode in ("ignore", "only") and z.get("kinds") in ("person", "animal"):
        out["kinds"] = z["kinds"]                         # 2.98.13: the zone acts only on persons / only on animals (066)
    if mode == "loiter":
        try:
            out["secs"] = int(max(3, min(600, float(z.get("secs") or 20))))
        except (TypeError, ValueError):
            out["secs"] = 20
    if mode in FIXED_MODES:
        ang = z.get("ang")
        if isinstance(ang, list) and len(ang) == len(pts) and all(isinstance(a, (list, tuple)) and len(a) == 2 and _num(a[0]) and _num(a[1]) for a in ang):
            out["ang"] = [[round(float(a[0]), 3), round(float(a[1]), 3)] for a in ang]
    return out


# ---- 2.98.7: the sleeping place stays where the bed is, wherever the camera looks ----
SLEEP_POS = deque(maxlen=60)          # (time, pan %, tilt %) - the picture comes later than the servo: mask every recent direction
SLEEP_MARGIN = 3.0                    # degrees around the bed (the servo and the field of view are not exact)


def _cam_deg(pan, tilt):
    return (float(pan) - 50.0) / 50.0 * servo_half("pan"), (float(tilt) - 50.0) / 50.0 * servo_half("tilt")


def sleep_to_ang(points, pan=None, tilt=None):
    """picture points 0..1 (camera at pan / tilt) -> directions in degrees (right +, up +)"""
    hf, vf = cam_fov()
    a0, e0 = _cam_deg(CFG["pan"] if pan is None else pan, CFG["tilt"] if tilt is None else tilt)
    th, tv = math.tan(math.radians(hf / 2.0)), math.tan(math.radians(vf / 2.0))
    return [[round(a0 + math.degrees(math.atan((x - 0.5) * 2.0 * th)), 3), round(e0 + math.degrees(math.atan((0.5 - y) * 2.0 * tv)), 3)] for x, y in points]


def sleep_project(ang, pan=None, tilt=None, margin=0.0):
    """directions in degrees -> picture points 0..1 for the camera at pan / tilt (may lie outside the picture). The edges are
    cut into small steps, so the straight lines of the bed stay right also near the border of the picture."""
    if not ang:
        return []
    hf, vf = cam_fov()
    a0, e0 = _cam_deg(CFG["pan"] if pan is None else pan, CFG["tilt"] if tilt is None else tilt)
    th, tv = math.tan(math.radians(hf / 2.0)), math.tan(math.radians(vf / 2.0))
    ca = sum(a[0] for a in ang) / len(ang); ce = sum(a[1] for a in ang) / len(ang)
    pts = []
    for a, e in ang:                                     # a little bigger: margin degrees away from the middle
        d = math.hypot(a - ca, e - ce) or 1.0
        pts.append((a + (a - ca) / d * margin, e + (e - ce) / d * margin))
    out = []
    for i in range(len(pts)):
        (a1, e1), (a2, e2) = pts[i], pts[(i + 1) % len(pts)]
        for k in range(8):
            a = a1 + (a2 - a1) * k / 8.0; e = e1 + (e2 - e1) * k / 8.0
            da = max(-80.0, min(80.0, a - a0)); de = max(-80.0, min(80.0, e - e0))
            out.append([0.5 + math.tan(math.radians(da)) / (2.0 * th), 0.5 - math.tan(math.radians(de)) / (2.0 * tv)])
    return out


FIXED_MODES = ("privacy", "sleep")    # 2.98.9: privacy zones stay on their place too (before: fixed to the picture - a turning
                                      # head showed the neighbour's tent for a moment)


def fixed_zones():
    return [z for z in ZONES if z["mode"] in FIXED_MODES and z.get("ang")]


def sleep_zones():
    return [z for z in ZONES if z["mode"] == "sleep" and z.get("ang")]


def fixed_migrate():
    """2.98.9: privacy zones of older versions have no directions yet - they were drawn at the position the camera has now
    (the start position is saved), so they get their directions from there once"""
    n = 0
    for z in ZONES:
        if z["mode"] in FIXED_MODES and not z.get("ang"):
            try:
                z["ang"] = sleep_to_ang(z["points"]); n += 1
            except Exception:
                pass
    return n


def sleep_update(now=None):
    """remember where the camera looks and move the corners of the sleeping places (for the zone editor and zone_allows)"""
    now = time.time() if now is None else now
    pos = (round(float(CFG["pan"]), 2), round(float(CFG["tilt"]), 2))
    if not SLEEP_POS or SLEEP_POS[-1][1:] != pos:
        SLEEP_POS.append((now,) + pos)
    for z in fixed_zones():
        if z.get("_at") != pos:
            z["_at"] = pos
            pp = sleep_project(z["ang"], *pos)
            corners = pp[::8]                                # the corners (every 8th point)
            z["points"] = [[round(min(1.0, max(0.0, x)), 4), round(min(1.0, max(0.0, y)), 4)] for x, y in corners]
            z["vis"] = any(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 for x, y in pp)


def sleep_polys(w, h, now=None):
    """pixel polygons of the sleeping places for every direction of the last 2 s"""
    now = time.time() if now is None else now
    zs = fixed_zones()
    if not zs:
        return []
    L = list(SLEEP_POS)
    poss = {(round(float(CFG["pan"]), 2), round(float(CFG["tilt"]), 2))}
    for i, p in enumerate(L):                            # every direction the camera had during the last 2 s
        end = L[i + 1][0] if i + 1 < len(L) else now
        if now - end < 2.0:
            poss.add(p[1:])
    out = []
    for z in zs:
        for pos in poss:
            pp = sleep_project(z["ang"], pos[0], pos[1], SLEEP_MARGIN)
            if pp:
                out.append(np.array([(int(round(x * w)), int(round(y * h))) for x, y in pp], np.int32))
    return out


def _side(a, b, p):
    """> 0: p is on the right-hand side of the line a -> b (screen coordinates, y down)."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def _segments_cross(p1, p2, a, b):
    d1, d2, d3, d4 = _side(a, b, p1), _side(a, b, p2), _side(p1, p2, a), _side(p1, p2, b)
    return (d1 > 0) != (d2 > 0) and d1 != 0 and d2 != 0 and (d3 > 0) != (d4 > 0)


class ZoneWatch:
    """Lines (crossed, optionally only in one direction) and dwell areas (a person stays longer than N s). Works on the
    person tracks; the point that counts is the feet (bottom middle of the box), like the other zones."""
    def __init__(self):
        self.st = {}

    def update(self, persons, pw, ph, frame, now):
        zs = [z for z in ZONES if z["mode"] in ("line", "loiter")]
        if not zs:
            self.st.clear(); return []
        if STATE.get("tracking") or manual_active() or str(STATE.get("patrol_status", "")).startswith("moving"):
            self.st.clear(); return []                        # the camera moves: positions are not comparable
        events, seen = [], set()
        for t in persons:
            x, y, w, h = t.box[:4]
            p = ((x + w / 2.0) / pw, (y + h * 0.95) / ph)
            seen.add(t.id)
            s_ = self.st.setdefault(t.id, {"p": p, "t": now, "in": {}, "done": set(), "last": {}})
            for z in zs:
                if z["mode"] == "line" and z["id"] not in s_["done"]:
                    a, b = z["points"]
                    sd = _side(a, b, p)
                    if abs(sd) < 1e-9:
                        continue                                  # exactly on the line: decide with the next point
                    old = s_["last"].get(z["id"])
                    s_["last"][z["id"]] = (p, sd)
                    if old is None or (old[1] > 0) == (sd > 0):
                        continue
                    q = old[0]                                    # the side changed: did the way pass through the line itself?
                    if _side(q, p, a) * _side(q, p, b) <= 0:
                        if z.get("dir", "both") == "both" or (z["dir"] == "ab") == (sd > 0):
                            s_["done"].add(z["id"]); events.append(("line", z))
                elif z["mode"] == "loiter" and z["id"] not in s_["done"]:
                    if point_in_poly(p[0], p[1], z["points"]):
                        t_in = s_["in"].setdefault(z["id"], now)
                        if now - t_in >= z.get("secs", 20):
                            s_["done"].add(z["id"]); events.append(("loiter", z))
                    else:
                        s_["in"].pop(z["id"], None)
            s_["p"] = p; s_["t"] = now
        for k in [k for k, v in self.st.items() if k not in seen and now - v["t"] > 10]:
            self.st.pop(k, None)
        for kind, z in events:
            zone_event(kind, z, frame)
        return events


def zone_event(kind, z, frame):
    if kind == "line":
        txt = trf("Person crossed the line «{zone}»", zone=z["name"])
        log_event("person", f"Person crossed the line «{z['name']}»")
    else:
        txt = trf("Person stays in «{zone}» for more than {secs} s", zone=z["name"], secs=z.get("secs", 20))
        log_event("person", f"Person stays in «{z['name']}» for more than {z.get('secs', 20)} s")
    STATE["zone_last"] = {"t": time.time(), "text": txt}
    push_alert("person", txt, zone=z["name"])
    w = WATCH_REF.get("w")
    if w is not None and is_armed():
        jpg = None
        try:
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            jpg = buf.tobytes() if ok else None
        except cv2.error:
            pass
        w.notifier.info(txt, "", title="{name}: " + tr("line" if kind == "line" else "dwell area"), jpg=jpg, fname="zone.jpg")


def apply_privacy(frame):
    """Paint the privacy zones and the sleeping places black (in place). Returns the frame. Both stay where they are when
    the head turns (directions in degrees); a privacy zone without directions (should not happen) is painted as drawn."""
    zs = [z for z in ZONES if z["mode"] == "privacy" and not z.get("ang")]
    if zs and fixed_migrate():                          # older zones: directions once, from where the camera looks now
        zs = [z for z in ZONES if z["mode"] == "privacy" and not z.get("ang")]
        try:
            save_settings(); log_event("sys", "Privacy zones: they now stay on their place when the head turns")
        except Exception:
            pass
    sl = any(z["mode"] in FIXED_MODES and z.get("ang") for z in ZONES)
    if (not zs and not sl) or frame is None:
        return frame
    h, w = frame.shape[:2]
    if not frame.flags.writeable:
        frame = frame.copy()
    polys = [np.array([(int(round(x * w)), int(round(y * h))) for x, y in z["points"]], np.int32) for z in zs]
    if sl:
        sleep_update()
        polys += sleep_polys(w, h)
    if polys:
        cv2.fillPoly(frame, polys, (0, 0, 0))
    return frame


def point_in_poly(x, y, pts):
    inside, j = False, len(pts) - 1
    for i in range(len(pts)):
        xi, yi, xj, yj = pts[i][0], pts[i][1], pts[j][0], pts[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def zone_allows(nx, ny, kind=None):
    """kind: "person" / "animal" / "other" or None (= every zone counts, as before 2.98.13). An ignore / only-here zone
    with «applies to» persons or animals (z["kinds"]) acts only on that kind; the other kinds see it as if it did not exist."""
    zs = ZONES
    if not zs:
        return True
    ap = lambda z: kind is None or z.get("kinds", "all") in ("all", kind)
    for z in zs:
        if z["mode"] in ("ignore", "privacy", "sleep") and (z["mode"] != "ignore" or ap(z)) and point_in_poly(nx, ny, z["points"]):
            return False
    only = [z for z in zs if z["mode"] == "only" and ap(z)]
    return (not only) or any(point_in_poly(nx, ny, z["points"]) for z in only)


def zone_box_ok(b, pw, ph, kind=None):
    """Box (x, y, w, h, ...) in processing-frame pixels; the point that counts is the middle of the feet region."""
    if not ZONES:
        return True
    return zone_allows((b[0] + b[2] / 2.0) / pw, (b[1] + b[3] * 0.85) / ph, kind)


def zones_set(lst):
    if not isinstance(lst, list):
        return False, "invalid zones"
    out = []
    old = {z["id"]: z for z in ZONES if z["mode"] in FIXED_MODES}
    for z in lst[:MAX_ZONES]:
        c = _clean_zone(z, len(out))
        if c:
            if c["mode"] in FIXED_MODES:                # 2.98.7 / 2.98.9: corners as directions from where the camera looks now
                o = old.get(c["id"])
                same = o and o.get("ang") and len(o.get("points") or []) == len(c["points"]) and all(
                    abs(a[0] - b[0]) < 0.003 and abs(a[1] - b[1]) < 0.003 for a, b in zip(o["points"], c["points"]))
                c["ang"] = o["ang"] if same else sleep_to_ang(c["points"])
                c.pop("_at", None)
            out.append(c)
    with LOCK:
        ZONES[:] = out
    save_settings(); log_event("sys", f"Zones updated ({len(out)})")
    return True, ""


def presence_home():
    """2.97.0: one answer to «is somebody home?» from both ways: the ping of the devices (presence_hosts) and the phone /
    watch seen in the Wi-Fi or by Bluetooth (presence_macs / presence_bt). True if one of them sees somebody."""
    a = PRESENCE["home"]
    try:
        P = TOOLS["presence"]
        b = P.get("here") if (CFG.get("presence_macs") or CFG.get("presence_bt")) else None
    except (NameError, KeyError):
        b = None
    if a is True or b is True:
        return True
    if a is None and b is None:
        return None
    return False


# ----------------------------------------------------------------------------
# Presence: is somebody home? (ping the phones / devices from the settings)
# ----------------------------------------------------------------------------
PRESENCE = {"home": None, "seen": {}, "start": time.time()}
_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-:]{0,79}$")


def _ping(host):
    try:
        return subprocess.run(["ping", "-c", "1", "-W", "1", host], capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


class PresenceMonitor:
    """Every 20 s: ping the configured devices. 'home' = one of them answered within the last 'away_after' minutes
    (phones sleep their Wi-Fi, so a single missed ping means nothing)."""
    def __init__(self):
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            try:
                self.check()
            except Exception as e:
                log_event("sys", f"Presence error: {e}")
            time.sleep(20.0)

    def check(self):
        hosts = [h for h in CFG["presence_hosts"] if isinstance(h, str) and _HOST_RE.match(h)]
        if not hosts or shutil.which("ping") is None:
            PRESENCE["home"] = None; STATE["presence"] = "unknown"; return
        ts = [threading.Thread(target=lambda h=h: PRESENCE["seen"].__setitem__(h, time.time()) if _ping(h) else None, daemon=True) for h in hosts]
        for t in ts:
            t.start()
        for t in ts:
            t.join(6.0)
        now, grace = time.time(), CFG["away_after"] * 60.0
        seen = [PRESENCE["seen"].get(h, 0.0) for h in hosts]
        if any(now - x < grace for x in seen):
            home = True
        elif not any(seen) and now - PRESENCE["start"] < grace:
            home = None                                    # just started, nothing answered yet -> unknown
        else:
            home = False
        if home != PRESENCE["home"]:
            log_event("sched", "Presence: " + {True: "somebody is home", False: "nobody home", None: "unknown"}[home])
        PRESENCE["home"] = home
        STATE["presence"] = {True: "home", False: "away", None: "unknown"}[home]


# ----------------------------------------------------------------------------
# Text settings (notifications, location, presence) - validated, shared by desktop window and web page
# ----------------------------------------------------------------------------
NOTIFY_TYPES = ("webhook", "ntfy", "telegram")
BACKUP_TYPES = ("off", "webdav", "folder", "telegram")
THERMAL_MAPS = {"inferno": cv2.COLORMAP_INFERNO, "jet": cv2.COLORMAP_JET, "hot": cv2.COLORMAP_HOT, "turbo": cv2.COLORMAP_TURBO,
                "grey": None}
TEXTS = [  # (section, key, label, kind, extra)
    ("Notifications", "notify_type", "Notification type", "enum", NOTIFY_TYPES),
    ("Notifications", "notify_url", "Webhook / ntfy URL", "str", None),
    ("Notifications", "telegram_token", "Telegram bot token", "secret", None),
    ("Notifications", "pushover_user", "Pushover: user key", "secret", None),
    ("Notifications", "msg_keyword_prefix", "Keyword at the start of every message (e.g. MW gives MW-ALARM)", "str", None),
    ("Notifications", "email_to", "E-mail: to (your address)", "str", None),
    ("Notifications", "email_host", "E-mail: SMTP server (e.g. smtp.gmail.com, mail.gmx.net)", "str", None),
    ("Notifications", "email_port", "E-mail: port (587 or 465)", "str", None),
    ("Notifications", "email_user", "E-mail: user name (usually the address)", "str", None),
    ("Notifications", "email_password", "E-mail: password (Gmail / iCloud: app password)", "secret", None),
    ("Notifications", "email_events", "E-mail: which messages", "enum", "email_events"),
    ("Notifications", "pushover_token", "Pushover: app token (API token of your own app at pushover.net)", "secret", None),
    ("Deterrence", "deter_person_act", "Person", "enum", "deter_acts"),
    ("Deterrence", "deter_person_sound", "Person: sound", "enum", "sounds"),
    ("Deterrence", "deter_big_act", "Big animal (bear, cow, horse, ...)", "enum", "deter_acts"),
    ("Deterrence", "deter_big_sound", "Big animal: sound", "enum", "sounds"),
    ("Deterrence", "deter_small_act", "Small animal (cat, dog, bird)", "enum", "deter_acts"),
    ("Deterrence", "deter_small_sound", "Small animal: sound", "enum", "sounds"),
    ("Deterrence", "deter_warm_act", "Warm body (thermal camera, e.g. fox, boar)", "enum", "deter_acts"),
    ("Deterrence", "deter_warm_sound", "Warm body: sound", "enum", "sounds"),
    ("SMS (LTE stick)", "sms_numbers", "Phone numbers (e.g. +41791234567, several with commas)", "str", None),
    ("SMS (LTE stick)", "sms_mode", "Stick / way", "enum", "sms_modes"),
    ("SMS (LTE stick)", "sms_port", "Serial port (only for AT commands)", "str", None),
    ("SMS (LTE stick)", "sms_hilink", "Address of a Huawei HiLink stick", "str", None),
    ("MQTT / Home Assistant", "mqtt_host", "MQTT broker (address, e.g. 192.168.1.10 or homeassistant.local)", "str", None),
    ("MQTT / Home Assistant", "mqtt_port", "MQTT port", "str", None),
    ("MQTT / Home Assistant", "mqtt_user", "MQTT user name", "str", None),
    ("MQTT / Home Assistant", "mqtt_password", "MQTT password", "secret", None),
    ("MQTT / Home Assistant", "mqtt_prefix", "Topic prefix", "str", None),
    ("Recording", "rec_marks", "Markings in recordings and alarm pictures", "enum", "rec_marks"),
    ("Night report", "weekrep_day", "Weekly detection report: day", "enum", ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")),
    ("Backup", "backup_type", "Copy recordings to", "enum", "backup_types"),
    ("Patrol", "patrol_mode", "Patrol route", "enum", "patrol_modes"),
    ("Backup", "backup_url", "WebDAV folder (address, e.g. Nextcloud)", "str", None),
    ("Backup", "backup_user", "WebDAV user name", "str", None),
    ("Backup", "backup_password", "WebDAV password (Nextcloud: app password)", "secret", None),
    ("Backup", "backup_folder", "Folder (USB stick / NAS, e.g. /media/pi/STICK/MotionWatch)", "str", None),
    ("Notifications", "telegram_chat", "Telegram chat id", "str", None),
    ("Notifications", "public_url", "Address of this page for links (e.g. https://pi.local:5000)", "str", None),
    ("Thermal camera", "thermal_source", "Thermal camera (run the camera scan first)", "enum", "thermal_choices"),
    ("Thermal camera", "thermal_map", "Colours", "enum", tuple(THERMAL_MAPS)),
    ("Messages", "device_name", "Device name (placeholder {name})", "str", None),
    ("Messages", "msg_person_title", "Person: title", "str", None),
    ("Messages", "msg_person_text", "Person: text", "str", None),
    ("Messages", "msg_prealarm_title", "Pre-alarm: title", "str", None),
    ("Messages", "msg_prealarm_text", "Pre-alarm: text", "str", None),
    ("Messages", "msg_warm_title", "Thermal alarm: title", "str", None),
    ("Messages", "msg_warm_text", "Thermal alarm: text", "str", None),
    ("Messages", "msg_noise_title", "Noise alarm: title", "str", None),
    ("Messages", "msg_noise_text", "Noise alarm: text", "str", None),
    ("Microphone", "audio_in", "Microphone", "enum", "audio_in"),
    ("Loudspeaker", "audio_out", "Loudspeaker", "enum", "audio_out"),
    ("Loudspeaker", "siren_on", "Siren at an alarm (only when armed)", "enum", "siren_on"),
    ("Clap switch", "clap_2", "Clap 2×", "enum", "clap_acts"),
    ("Clap switch", "clap_3", "Clap 3×", "enum", "clap_acts"),
    ("Clap switch", "clap_4", "Clap 4×", "enum", "clap_acts"),
    ("Bless you", "sneeze_reply", "Answer", "enum", "sneeze_replies"),
    ("Setup", "tips_level", "Explanations the first time something is opened (dots = never opened, NEW = new)", "enum", "tips_levels"),
    ("Setup", "use_case", "What is MoveEye for? («Simple» shows only what fits)", "enum", "use_cases"),
    ("Wake-up alarm", "wake_time", "Wake-up time (HH:MM)", "str", None),
    ("Wake-up alarm", "wake_days", "Days", "enum", "wake_days"),
    ("Wake-up alarm", "wake_sound", "Sound", "enum", "wake_sounds"),
    ("Bless you", "sneeze_texts", "Words (several: separate with |)", "str", None),
    ("Loudspeaker", "siren_sound", "Sound", "enum", "sounds"),
    ("Lights", "light_white_out", "White light: connected to", "enum", "light_white_out"),
    ("Lights", "light_white_auto", "White light: Auto means", "enum", "light_auto"),
    ("Lights", "light_ir_out", "Infrared light: connected to", "enum", "light_ir_out"),
    ("Lights", "light_ir_auto", "Infrared light: Auto means", "enum", "light_auto"),
    ("Lights", "picture_mode", "Picture", "enum", "picture_mode"),
    ("AI detection", "ai_model", "AI model", "enum", "ai_models"),
    ("AI detection", "ai_own_url", "Own model: address of its description (moveeye_model.json)", "str", None),
    ("AI detection", "species_model", "Animal species: model", "enum", "species_model"),
    ("AI detection", "species_norm", "Animal species: picture preparation of the model", "enum", "species_norm"),
    ("Solar panel", "solar_addr", "Current meter: address (I2C)", "enum", "pca_address"),
    ("GPS module", "gpsmod_port", "Connection", "enum", "gpsmod_port"),
    ("Mover", "mover_mode", "Mover (tracked vehicle)", "enum", "mover_mode"),
    ("Mover", "mover_driver", "Motor driver", "enum", "mover_driver"),
    ("Mover", "mover_addr", "Motor driver: address (I2C)", "enum", "mover_addr"),
    ("Simulator", "sim_url", "Address of the simulation program", "str", None),
    ("Storm warning", "wind_gpio", "Wind meter (anemometer) connected to", "enum", "wind_gpio"),
    ("Camera / Servos", "cam_rotate", "Turn picture (camera mounted sideways or upside down)", "enum", "cam_rotate"),
    ("Servo driver", "servo_driver", "Servo driver", "enum", "servo_driver"),
    ("Servo driver", "pca_address", "PCA9685 address (I2C)", "enum", "pca_address"),
    ("Battery", "ups_model", "UPS HAT: model", "enum", "ups_model"),
    ("Battery", "ups_addr", "UPS HAT (A/B/C): address (I2C)", "enum", "pca_address"),
    ("Camping / protection", "net_mode", "Network", "enum", "net_modes"),
    ("Camping / protection", "hotspot_ssid", "Own Wi-Fi: name", "str", None),
    ("Camping / protection", "hotspot_password", "Own Wi-Fi: password (8-63 characters)", "str", None),
    ("Updates", "update_url", "Where new versions come from (address of versions.json, or a folder e.g. USB stick)", "str", None),
    ("Updates", "update_token", "GitHub key (token) - only for a private repository", "secret", None),
    ("Setup", "latitude", "Latitude (sunrise / sunset)", "float", (-66.0, 66.0)),
    ("Setup", "longitude", "Longitude (sunrise / sunset)", "float", (-180.0, 180.0)),
    ("Setup", "presence_hosts", "Phones / devices for presence (IP or name, comma separated)", "hosts", None),
    ("Camping / protection", "presence_back", "When my phone comes back", "enum", "presence_back"),      # 2.98.15 (577)
]
TEXT_SPECS = {k: (kind, extra) for s, k, l, kind, extra in TEXTS}


def text_choice_pairs(key):
    """[(value, label)] of an enum setting. The thermal camera list changes with the camera scan, so it is computed."""
    kind, extra = TEXT_SPECS[key]
    if extra == "presence_back":                              # 2.98.15 (577): the choice at the return of the phone
        return [(k, tr(l)) for k, l in PRESENCE_BACK]
    if str(extra).startswith("mover_"):
        return mover_choice_pairs(extra)
    if extra == "net_modes":
        return [("auto", tr("Automatic: known networks (e.g. phone hotspot), otherwise own Wi-Fi")),
                ("hotspot", tr("Own Wi-Fi at boot")), ("client", tr("Only known networks"))]
    if extra in ("light_white_out", "light_ir_out"):
        return light_out_pairs(extra[6:-4])
    if extra == "email_events":
        return [("alarms", tr("only alarms (person, warm, noise, sabotage)")), ("all", tr("all messages"))]
    if extra == "patrol_modes":
        return [("pendulum", tr("back and forth (1-2-3-2-1)")), ("loop", tr("round trip (1-2-3-1-2-3)"))]
    if extra == "rec_marks":
        return [("thin", tr("thin corner marks (face stays free)")), ("none", tr("none (clean picture)")), ("full", tr("like the live picture (red boxes)"))]
    if extra == "sms_modes":
        return [("auto", tr("automatic")), ("mmcli", "ModemManager (mmcli)"), ("at", tr("AT commands (serial port)")), ("hilink", "Huawei HiLink (192.168.8.1)")]
    if extra == "deter_acts":
        return [("off", tr("nothing")), ("sound", tr("sound")), ("light", tr("light flashes")), ("both", tr("sound + light flashes"))]
    if extra == "backup_types":
        return [("off", tr("off")), ("webdav", tr("WebDAV (Nextcloud, NAS, cloud)")), ("folder", tr("Folder (USB stick / NAS)")),
                ("telegram", tr("Telegram (video, max. 50 MB)"))]
    if extra == "light_auto":
        return [("alarm_dark", tr("at an alarm, only at night")), ("alarm", tr("at an alarm, day and night")),
                ("dark", tr("the whole night (sunset to sunrise)"))]
    if extra == "ups_model":
        return [("auto", tr("automatic")), ("e", "UPS HAT (E) – 4 × 21700, I2C 0x2D"), ("ina", "UPS HAT (A / B / C) – INA219")]
    if extra == "species_model":
        cur = str(CFG.get("species_model") or "")
        ms = species_models() + ([cur] if cur and cur not in species_models() else [])
        return [("", "– " + tr("none") + " –")] + [(m, m) for m in ms]
    if extra == "ai_models":                         # part 195: own MoveEye model (YOLO, ONNX) next to the standard
        return [("ssd", tr("Standard (SSD MobileNet V2)")), ("own", tr("Own (MoveEye model)"))]
    if extra == "species_norm":
        return [("imagenet", "ImageNet (mean / std)"), ("01", "0 … 1"), ("-11", "-1 … 1")]
    if extra == "gpsmod_port":
        ports = sorted(set(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*") + [p for p in ("/dev/serial0", "/dev/ttyAMA0") if os.path.exists(p)]))
        cur = str(CFG.get("gpsmod_port") or "auto")
        if cur not in ("auto", "gpsd") and cur not in ports:
            ports.append(cur)
        return [("auto", tr("automatic")), ("gpsd", "gpsd")] + [(p, p) for p in ports]
    if extra == "wind_gpio":
        cur = str(CFG.get("wind_gpio") or "")
        gs = sens_free_gpios() + ([int(cur)] if cur.isdigit() else [])
        return [("", "– " + tr("none") + " –")] + [(str(g), f"GPIO {g}") for g in sorted(set(gs))]
    if extra == "cam_rotate":
        return [("0", tr("not turned")), ("90", tr("90° to the right")), ("180", tr("upside down (180°)")), ("270", tr("90° to the left"))]
    if extra == "picture_mode":
        return [("color", tr("colour")), ("night_grey", tr("grey at night (good with a NoIR camera)")), ("grey", tr("always grey"))]
    if extra == "servo_driver":
        return [("auto", tr("automatic: PCA9685 if found, otherwise GPIO 17 / 27")), ("pca9685", "PCA9685 (I2C)"),
                ("gpio", tr("directly on GPIO 17 / 27"))]
    if extra == "pca_address":
        return [(f"0x{a:02x}", f"0x{a:02x}") for a in range(0x40, 0x48)]
    if extra in ("audio_in", "audio_out"):
        return audio_choice_pairs(extra[6:])
    if extra == "sounds":
        return sound_choice_pairs()
    if extra == "clap_acts":
        return clap_act_pairs()
    if extra == "sneeze_replies":
        return sneeze_reply_pairs()
    if extra == "tips_levels":
        return [("off", tr("off")), ("basic", tr("only the most important")), ("normal", tr("normal")), ("all", tr("nearly every detail"))]
    if extra == "use_cases":
        return [("", tr("everything (not chosen)")), ("camping", tr("Camping: tent, caravan")), ("home", tr("House and garden")),
                ("wild", tr("Watching animals")), ("holiday", tr("Holiday house, alpine hut")), ("room", tr("In the room: wake-up alarm"))]
    if extra == "wake_days":
        return [("mon-fri", tr("Monday to Friday")), ("all", tr("every day")), ("sat-sun", tr("Saturday and Sunday")),
                ("sun-thu", tr("Sunday to Thursday")), ("once", tr("only once (next time)"))]
    if extra == "wake_sounds":
        return [("chime", tr("Soft melody")), ("birds", tr("Birdsong")), ("beeps", tr("Fast beeps")), ("marmot", tr("Marmot whistle"))] + \
               [("file:" + f, "♪ " + f) for f in own_sounds()]
    if extra == "siren_on":
        return [("off", tr("off")), ("person", tr("person alarm")), ("alarm", tr("person, thermal and noise alarm")),
                ("all", tr("every alarm, also the pre-alarm (movement)"))]
    if extra == "thermal_choices":
        act = STATE["source_id"]
        return ([("", "– " + tr("none") + " –"), ("senxor:0", "Waveshare Thermal-90 / 44 (SPI)")]
                + [(i["id"], i["name"]) for i in list_sources() if i["id"] not in ("auto", act)])
    return [(c, tr(c)) for c in extra]


def _http_ok(u):
    if not (isinstance(u, str) and len(u) <= 500 and re.match(r"^https?://[^\s]+$", u, re.I) is not None):
        return False
    try:                                                 # 2.95.35: a real server name (ntfy..sh stopped the internet check)
        from urllib.parse import urlparse
        h = urlparse(u).hostname or ""
        if not h or ".." in h or h.startswith((".", "-")) or h.endswith("-"):
            return False
        h.encode("idna")
        urlparse(u).port
    except (ValueError, UnicodeError):
        return False
    return True


I2C_KEYS = {"pca_address": "servo board (PCA9685)", "solar_addr": "solar meter (INA219)", "mover_addr": "motor driver (mover)",
            "ups_addr": "UPS HAT"}


def _i2c_active(key, cfg=None):
    c = cfg or CFG
    pca_on = c.get("servo_driver") == "pca9685" or (c.get("servo_driver") == "auto" and str(STATE.get("servo_backend", "")).startswith("pca9685"))
    return {"pca_address": pca_on, "solar_addr": bool(c.get("solar_on")),
            "mover_addr": c.get("mover_mode") != "off", "ups_addr": bool(c.get("ups_on"))}.get(key, False)


def i2c_conflicts(cfg=None):
    """2.95.35: two devices that are switched on with the same I2C address read each other's registers (wrong values)"""
    c = cfg or CFG; seen = {}; out = []
    for k in I2C_KEYS:
        if not _i2c_active(k, c):
            continue
        a = str(c.get(k, "")).lower()
        if a in seen:
            out.append((seen[a], k, a))
        else:
            seen[a] = k
    return out


def text_value(key):
    v = CFG[key]
    return ", ".join(v) if isinstance(v, list) else v


def set_text(key, value):
    spec = TEXT_SPECS.get(key)
    if spec is None:
        return False, "unknown setting"
    kind, extra = spec
    if kind == "enum":
        if value not in [c for c, _l in text_choice_pairs(key)]:
            return False, "invalid value"
        if key in I2C_KEYS or key in ("servo_driver", "mover_mode"):
            cf = i2c_conflicts(dict(CFG, **{key: value}))
            if cf:
                a_, b_, ad = cf[0]
                return False, trf("I2C address {a} is already used by the {x} - choose another address", a=ad, x=tr(I2C_KEYS[a_ if a_ != key else b_]))
        if key == "use_case":
            return use_case_set(value, "settings")
        CFG[key] = value
        if key == "ai_model":
            own_ai_switched()                           # part 195: load the chosen model (falls back to the standard)
        if key == "net_mode":
            NETAUTO["paused"] = False
            log_event("sys", f"Network mode: {value}")
        if key in ("servo_driver", "pca_address"):
            HW_REINIT["want"] = True                     # the servo driver is opened again (no restart needed)
        if key == "thermal_source" and value.startswith("senxor") and float(CFG["thermal_zoom"]) >= 99.9:
            CFG["thermal_zoom"] = 65                     # Thermal-90 (90 degrees) next to the Camera Module 3 (66 degrees)
        if key in ("audio_in", "audio_out"):
            log_event("sys", ("Microphone: " if key == "audio_in" else "Loudspeaker: ") + (dict(text_choice_pairs(key)).get(value) or "-"))
            if key == "audio_out" and not value:
                sound_stop()
    elif kind == "float":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False, "not a number"
        if not math.isfinite(v) or not extra[0] <= v <= extra[1]:
            return False, "out of range"
        CFG[key] = round(v, 4)
    elif kind == "hosts":
        hosts = [h for h in re.split(r"[,; ]+", str(value or "")) if h]
        if len(hosts) > 8 or not all(_HOST_RE.match(h) for h in hosts):
            return False, "invalid device name or address"
        CFG[key] = hosts
    else:
        v = str(value or "").strip()
        if v:
            if key == "mqtt_host" and not re.fullmatch(r"[A-Za-z0-9.\-:\[\]]{1,120}", v):
                return False, "invalid device name or address"
            if key == "sms_numbers" and not all(_PHONE_RE.match(n) for n in re.split(r"[,; ]+", v) if n):
                return False, "phone numbers like +41791234567"
            if key == "sms_port" and not re.fullmatch(r"/dev/[A-Za-z0-9_\-/]{2,40}", v):
                return False, "a port like /dev/ttyUSB2"
            if key == "sms_hilink" and not re.fullmatch(r"[A-Za-z0-9.\-]{3,60}(:\d{1,5})?", v):
                return False, "invalid device name or address"
            if key == "mqtt_port" and not (v.isdigit() and 1 <= int(v) <= 65535):
                return False, "port 1-65535"
            if key == "mqtt_prefix" and not re.fullmatch(r"[A-Za-z0-9_\-/]{1,60}", v):
                return False, "only letters, digits, - _ /"
            if key == "mqtt_user" and (len(v) > 120 or any(ord(c) < 32 for c in v)):
                return False, "text too long or with control characters"
            if key == "backup_url" and not re.match(r"^https?://[^\s]{4,500}$", v):
                return False, "invalid URL (http:// or https:// expected)"
            if key == "backup_folder" and not (v.startswith("/") and len(v) < 300 and ".." not in v):
                return False, "a folder like /media/... expected"
            if key == "backup_user" and (len(v) > 120 or any(ord(c) < 32 for c in v)):
                return False, "text too long or with control characters"
            if key == "sim_url" and not re.fullmatch(r"https?://[A-Za-z0-9.\-\[\]:]{1,120}/?", v):
                return False, "invalid URL (http:// or https:// expected)"
            if key == "ai_own_url" and not (v.startswith("https://") and _http_ok(v) and v.lower().endswith(".json")):
                return False, "https://... address of moveeye_model.json expected"
            if key in ("notify_url", "public_url") and not _http_ok(v):
                return False, "invalid URL (http:// or https:// expected)"
            if key == "wake_time" and not _HM_RE.match(v):
                return False, "a time like 07:00"
            if key == "msg_keyword_prefix" and not re.fullmatch(r"[A-Za-z0-9]{1,12}", v):
                return False, "1 to 12 letters or digits"
            if key == "email_to" and not _EMAIL_RE.fullmatch(v):
                return False, "invalid e-mail address"
            if key == "email_host" and not re.fullmatch(r"[A-Za-z0-9.\-]{3,120}", v):
                return False, "invalid device name or address"
            if key == "email_port" and v not in ("25", "465", "587", "2525"):
                return False, "port 587 or 465"
            if key == "email_user" and (len(v) > 120 or any(ord(c) < 32 for c in v)):
                return False, "text too long or with control characters"
            if key in ("pushover_user", "pushover_token") and not re.fullmatch(r"[A-Za-z0-9]{30}", v):
                return False, "30 letters and digits expected (from pushover.net)"
            if key == "telegram_token" and not re.fullmatch(r"\d{5,12}:[A-Za-z0-9_\-]{20,60}", v):
                return False, "invalid Telegram bot token"
            if key == "update_token" and not re.fullmatch(r"[A-Za-z0-9_]{20,255}", v):
                return False, "invalid GitHub key (it starts with github_pat_ or ghp_)"
            if key == "telegram_chat" and not re.fullmatch(r"-?\d{1,20}|@[A-Za-z0-9_]{3,64}", v):
                return False, "invalid Telegram chat id"
        if (key.startswith("msg_") or key == "device_name") and (len(v) > (40 if key == "device_name" else 300) or any(ord(c) < 32 for c in v)):
            return False, "text too long or with control characters"
        if key == "sneeze_texts" and (len(v) > 200 or any(ord(c) < 32 for c in v)):
            return False, "text too long or with control characters"
        if key == "update_url" and not _upd_source_ok(v):
            return False, "https://... address or a folder (/media/...) expected"
        if key == "hotspot_ssid" and (not v or len(v.encode()) > 32 or any(ord(c) < 32 for c in v)):
            return False, "invalid network name"
        if key == "hotspot_password" and not (8 <= len(v) <= 63 and all(32 <= ord(c) < 127 for c in v)):
            return False, "the password must have 8 to 63 characters"
        CFG[key] = v
    save_settings()
    return True, ""


def web_texts(lang=None):
    """Schema + current values for the web page (secrets are never sent, only whether they are set)."""
    out = []
    for sec, key, label, kind, extra in TEXTS:
        v = text_value(key)
        ph = ""
        m_ = re.fullmatch(r"msg_(person|prealarm|warm|noise)_(title|text)", key)
        if m_:
            ph = msg_defaults(lang)[m_.group(1)][0 if m_.group(2) == "title" else 1]
        elif key == "device_name":
            ph = "MoveEye"
        elif key == "backup_url":
            ph = "https://cloud.example.ch/remote.php/dav/files/USER/MotionWatch/"
        out.append({"section": sec, "key": key, "label": tr(label, lang), "placeholder": ph,
                    "kind": kind, "choices": [c for c, _l in text_choice_pairs(key)] if kind == "enum" else None,
                    "labels": {c: l for c, l in text_choice_pairs(key)} if kind == "enum" else None,
                    "value": "" if kind == "secret" else v, "set": bool(v)})
    return out


# ----------------------------------------------------------------------------
# Schedules (time plans): switch features on / off at certain times
#   A schedule = name + weekdays + start/end time + a list of "feature -> ON / OFF".
#   While a schedule is active its features are forced; when it ends they go back to the value
#   the user had set.  Changing a forced switch by hand wins until the schedule changes.
#   Windows may cross midnight (22:00 -> 06:00 belongs to the day it starts on).
# ----------------------------------------------------------------------------
MAX_SCHEDULES = 12
MAX_EXTRA = 3
SCHEDULES = []          # [{"name", "enabled", "days": [0=Mon .. 6=Sun], "start": "HH:MM", "end": "HH:MM", "actions": {key: bool}}]
SCHED = {"base": {}, "manual": set(), "last": {}, "active": []}
SCHED_FEATURES = [      # (config key, label) - everything a schedule may switch
    ("detection_on", "Detection"), ("record", "Recording"), ("snapshot_on_person", "Snapshots"),
    ("track_person", "Person tracking"), ("patrol", "Patrol"), ("ai_enabled", "AI detection"),
    ("relays_on", "Auto relays"), ("notify_on", "Notifications"), ("timelapse_on", "Timelapse"), ("thermal_on", "Thermal overlay"),
    ("notify_prealarm", "Pre-alarm push"), ("browser_alarm", "Alarm sound in the browser"),
    ("armed", "Armed (alarms)"), ("thermal_alarm", "Thermal alarm"), ("noise_alarm", "Noise alarm"), ("eco_on", "Power saving"),
]
SCHED_KEYS = [k for k, _ in SCHED_FEATURES]
SCHED_NOTE = ("While a schedule is active, the listed features are forced ON or OFF. Afterwards they return to your own setting. "
              "Switching one by hand overrides the schedule until its next change.")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _clean_time(v, default):
    return v if isinstance(v, str) and _TIME_RE.match(v) else default


def _day_ok(d):
    return isinstance(d, (int, float)) and not isinstance(d, bool) and math.isfinite(d) and 0 <= d <= 6


def _clean_schedule(s, i):
    """Validate / normalise one schedule dict (from the settings file, web page or desktop dialog)."""
    if not isinstance(s, dict):
        return None
    name = str(s.get("name") or "").strip()[:40] or f"Schedule {i + 1}"
    days = s.get("days", list(range(7)))
    days = sorted({int(d) for d in days if _day_ok(d)}) if isinstance(days, list) else list(range(7))
    acts = s.get("actions") if isinstance(s.get("actions"), dict) else {}
    off = s.get("sun_offset", 0)
    off = 0 if isinstance(off, bool) or not isinstance(off, (int, float)) or not math.isfinite(off) else int(max(-180, min(180, off)))
    return {"name": name, "enabled": bool(s.get("enabled", True)), "days": days,
            "start": _clean_time(s.get("start"), "22:00"), "end": _clean_time(s.get("end"), "06:00"),
            "sun": s.get("sun") if s.get("sun") in ("dark", "light") else "",        # "dark" = sunset..sunrise, "light" = sunrise..sunset
            "sun_offset": off,                                                       # minutes added to sunrise and sunset
            "presence": s.get("presence") if s.get("presence") in ("away", "home") else "",
            "skip": re.sub(r"[^0-9.,; \-]", "", str(s.get("skip") or ""))[:200].strip(),   # dates on which the schedule does not run
            "actions": {k: acts[k] for k in SCHED_KEYS if isinstance(acts.get(k), bool)}}


def _mins(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def sun_times(d, lat, lon):
    """Sunrise / sunset as minutes after local midnight (NOAA formula, about +-2 min). 'dark' / 'light' for polar night / day."""
    n = d.timetuple().tm_yday
    g = 2 * math.pi / 365.0 * (n - 1)
    eq = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
           + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    la = math.radians(lat)
    c = math.cos(math.radians(90.833)) / (math.cos(la) * math.cos(dec)) - math.tan(la) * math.tan(dec)
    if c > 1:
        return "dark"
    if c < -1:
        return "light"
    ha = math.degrees(math.acos(c))
    try:
        tz = datetime(d.year, d.month, d.day, 12).astimezone().utcoffset().total_seconds() / 60.0
    except (OverflowError, OSError, ValueError):
        tz = 0.0
    return (720 - 4 * (lon + ha) - eq + tz, 720 - 4 * (lon - ha) - eq + tz)


@functools.lru_cache(maxsize=64)
def _parse_skip(text):
    """'2026-12-24..2026-12-26, 08-01' -> ranges. 'MM-DD' repeats every year."""
    def point(t):
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", t)
        try:
            if m:
                return ("d", datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date())
            m = re.fullmatch(r"(\d{2})-(\d{2})", t)
            if m:
                datetime(2000, int(m.group(1)), int(m.group(2)))
                return ("y", (int(m.group(1)), int(m.group(2))))
        except ValueError:
            pass
        return None
    out = []
    for tok in re.split(r"[,; ]+", text or ""):
        if not tok:
            continue
        a, _, b = tok.partition("..")
        pa, pb = point(a), point(b or a)
        if pa and pb and pa[0] == pb[0]:
            out.append((pa[0], pa[1], pb[1]))
    return tuple(out)


def _is_skipped(s, d):
    for kind, a, b in _parse_skip(s.get("skip", "")):
        if kind == "d" and a <= d <= b:
            return True
        if kind == "y" and a <= (d.month, d.day) <= b:
            return True
    return False


def _window_start(s, dt):
    """The calendar day on which the time window that contains `dt` started (None = outside). A window that crosses midnight
    belongs to the day it starts on."""
    today, cur = dt.date(), dt.hour * 60 + dt.minute
    if s.get("sun"):
        r = sun_times(today, CFG["latitude"], CFG["longitude"])
        light = s["sun"] == "light"
        if r in ("dark", "light"):
            return today if (r == "light") == light else None
        rise, sset = r[0] + s.get("sun_offset", 0), r[1] + s.get("sun_offset", 0)
        if light:
            return today if rise <= cur < sset else None
        if cur >= sset:
            return today
        return today - timedelta(days=1) if cur < rise else None
    a, b = _mins(s["start"]), _mins(s["end"])
    if a == b:                                   # same start and end = the whole day
        return today
    if a < b:
        return today if a <= cur < b else None
    if cur >= a:
        return today
    return today - timedelta(days=1) if cur < b else None


def schedule_window_contains(s, dt):
    """Is the moment `dt` inside the schedule's weekdays + time window? (ignores 'enabled' and presence)"""
    if not s["days"]:
        return False
    d = _window_start(s, dt)
    return d is not None and d.weekday() in s["days"] and not _is_skipped(s, d)


def presence_ok(s):
    p = s.get("presence")
    home = presence_home()
    if not p or home is None:                    # no rule, or presence unknown -> stay armed
        return True
    return home if p == "home" else not home


def schedule_active(s, dt=None):
    return bool(s["enabled"]) and schedule_window_contains(s, dt or datetime.now()) and presence_ok(s)


def days_text(days, names=("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
    days = sorted(days)
    if len(days) == 7:
        return "every day" if names[0] == "Mon" else "täglich"
    if days == [0, 1, 2, 3, 4]:
        return f"{names[0]}–{names[4]}"
    if days == [5, 6]:
        return f"{names[5]}, {names[6]}"
    return ", ".join(names[d] for d in days) or "–"


def schedule_tick():
    """Apply all schedules (called once per second by the Scheduler thread and after every edit)."""
    with LOCK:
        plans = [dict(s) for s in SCHEDULES]
    now = datetime.now()
    forced, active, active_idx = {}, [], []
    for i, s in enumerate(plans):
        if schedule_active(s, now):
            active.append(s["name"]); active_idx.append(i)
            forced.update(s["actions"])                  # later schedules win over earlier ones
    base, manual, last = SCHED["base"], SCHED["manual"], SCHED["last"]
    labels = dict(SCHED_FEATURES)
    prev = SCHED["active"]
    for n in active:
        if n not in prev:
            log_event("sched", f"Schedule started: {n}")
    for n in prev:
        if n not in active:
            log_event("sched", f"Schedule ended: {n}")
    SCHED["active"] = active
    for k, v in forced.items():
        if last.get(k) != v:
            manual.discard(k)                            # new window / new value -> the schedule takes over again
        if k in manual:
            continue
        if k not in base:
            base[k] = CFG[k]
        if CFG[k] != v:
            if k == "armed":                             # 2.97.0: through the arm logic (countdown, «armed now», rehearsal)
                arm_by_schedule(v, ", ".join(active))
            else:
                CFG[k] = v
            log_event("sched", f"Schedule: {labels.get(k, k)} {'ON' if v else 'OFF'}")
    for k in list(base):
        if k not in forced:                              # no schedule controls it any more -> give the user's value back
            v0 = base.pop(k); manual.discard(k)
            if k == "armed":
                arm_by_schedule(v0, "end")
            else:
                CFG[k] = v0
            log_event("sched", f"Schedule: {labels.get(k, k)} back to {'ON' if CFG[k] else 'OFF'}")
    SCHED["last"] = dict(forced)
    STATE["sched_active"] = list(active); STATE["sched_active_idx"] = active_idx
    STATE["sched_forced"] = dict(forced); STATE["sched_manual"] = sorted(manual)


def sched_user_changed(key):
    """A switch was changed by hand. If a schedule currently forces it, the user's choice wins until the schedule changes."""
    if key in SCHED["last"]:
        SCHED["manual"].add(key)
        SCHED["base"][key] = CFG[key]


def schedule_add():
    with LOCK:
        if len(SCHEDULES) >= MAX_SCHEDULES:
            return False, f"maximum {MAX_SCHEDULES} schedules"
        SCHEDULES.append(_clean_schedule({"name": f"Schedule {len(SCHEDULES) + 1}", "actions": {}}, len(SCHEDULES)))
    save_settings(); log_event("sched", "Schedule added")
    schedule_tick()
    return True, ""


def schedule_save(index, data):
    clean = _clean_schedule(data, index if isinstance(index, int) else 0)
    if clean is None:
        return False, "invalid schedule"
    with LOCK:
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(SCHEDULES):
            return False, "unknown schedule"
        SCHEDULES[index] = clean
    save_settings()
    schedule_tick()
    return True, ""


def schedule_remove(index):
    with LOCK:
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(SCHEDULES):
            return False, "unknown schedule"
        gone = SCHEDULES.pop(index)
    save_settings(); log_event("sched", f"Schedule removed: {gone['name']}")
    schedule_tick()
    return True, ""


class Scheduler:
    """Background thread: applies the time plans once per second."""
    def __init__(self):
        schedule_tick()
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            try:
                schedule_tick(); arm_tick()
                wake_tick()                             # 2.98.7: wake-up alarm
                night_guard_tick()                      # 2.98.9: «Heute Nacht bewachen» ends with the night time
            except Exception as e:                      # never let the scheduler thread die
                log_event("sys", f"Scheduler error: {e}")
            time.sleep(1.0)


