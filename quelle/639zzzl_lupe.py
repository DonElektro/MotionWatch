#@ MoveEye – Teil 639zzzl: «🔍 Lupe» im Live-Bild – nur das Bild vergrössern (nicht die Seite): Rahmen ziehen, mit zwei Fingern zoomen, mit einem Finger verschieben, Doppeltipp = ganzes Bild; der vergrösserte Bereich kommt scharf aus der vollen Auflösung der Kamera (Pi-Kamera: Sensor-Standbild), Privatsphäre-Zonen bleiben schwarz; mit Kopf-Recht dreht der Kopf den Bereich in die Mitte, der Ausschnitt folgt dem Ort. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (13.11.2026, entschieden): er kann heute nur die ganze Browser-Seite zoomen, er will nur das Live-Bild.
#   * Gesten (Entscheid hier, damit nichts mit dem Bestehenden kollidiert):
#       - normales Live-Bild: wie bisher (1 Finger = Seite scrollen, Antippen = Knöpfe 4 s (639zzj), Doppeltipp = Vollbild (530));
#         NEU: zwei Finger auf dem Bild = Lupe geht auf und zoomt sofort (die Seite zoomt dabei nicht); PC: Strg + Mausrad bzw.
#         Zwei-Finger-Zoom des Trackpads über dem Bild.
#       - Knopf «🔍+ Lupe» (in der Knopfleiste des Live-Bilds #lv-tools, im Vollbild oben rechts #vo-lupe) = Lupen-Modus: jetzt
#         zieht ein Finger (PC: Maus) einen Rahmen = dieser Bereich gross; vergrössert: ein Finger verschiebt, zwei Finger zoomen,
#         Mausrad zoomt; Doppeltipp = ganzes Bild (1:1), Doppeltipp im ganzen Bild = Lupe zu; «✕ Lupe», «1:1», Esc.
#       - In der Lupe sind die Knopfleiste, die Kamera-Kacheln und im Vollbild ⇆ / 🚜 ausgeblendet (body.lupe-on) – der Joystick
#         bleibt; «✕ Lupe» ist immer sichtbar (der Weg zurück). Untersuchen (639zze) wird beim Öffnen geschlossen.
#       - touch-action: none nur auf der Lupen-Ebene über dem Bild; die Seite bleibt sonst normal (scrollen, zoomen).
#   * Scharfer Ausschnitt (/api/lupe/crop.jpg, Recht «live» wie das Live-Bild): der Bereich wird aus dem Bild mit der grössten
#     Auflösung geschnitten, die es gibt:
#       - Pi-Kamera (picamera2): ein Standbild in voller Sensor-Auflösung (Camera Module 3: 4608 × 2592) über
#         switch_mode_and_capture_array – IM FADEN DER KAMERA-SCHLEIFE (Wrapper um PiCamSource.read, nie zwei Zugriffe zugleich),
#         auf das Blickfeld des Video-Stroms zugeschnitten (ScalerCrop der Metadaten), gedreht / gespiegelt wie das Live-Bild,
#         Privatsphäre-Zonen und Schlafplätze geschwärzt (apply_privacy) – erst dann wird geschnitten. Kostet eine Pause der
#         Kamera-Schleife (geschätzt 0.3 – 0.8 s pro Standbild), darum höchstens alle LUPE_GAP_S Sekunden, für alle Zuschauer
#         gemeinsam, und PAUSIERT während Alarm / Person im Bild / Aufnahme / Folgen, Akku-Sparen und während der Kopf fährt
#         (dann der volle Kamera-Frame, siehe unten). ScalerCrop allein (zoomt auch die Erkennung) und ein zweiter Strom in
#         Sensor-Auflösung (Speicher, Bilder/s immer) sind dafür nicht der richtige Weg.
#       - USB- / Netzwerk-Kamera, Simulator: der volle Frame der Kamera (frame_raw, vor dem Verkleinern auf web_width und ohne
#         Rahmen / Statuszeile; Privatsphäre schon geschwärzt, 410). Die Auflösung der USB-Kamera wird nicht umgeschaltet.
#       - Weitwinkel (Zusatzkamera 440): ihr voller Frame (ExtraCam.raw); Wärmebild-Ansicht: das gezeigte Bild (kein schärferes –
#         Sensor 80 × 62 / 160 × 120), nur vergrössert.
#       - Demo-Kamera: ein Standbild in dreifacher Auflösung mit feinen Einzelheiten (Schild beim Zelt) – für die Tests.
#     Grenzen: Koordinaten 0..1 geprüft (Zahlen, endlich, im Bild), Ausgabe höchstens LUPE_OUT_MAX px breit, pro Benutzer / Gast-
#     Adresse höchstens LUPE_RATE Anfragen (Eimer), sonst 429. Die Seite holt alle LUPE_REFRESH_MS ms ein neues Bild.
#   * Kopf folgt (POST /api/lupe action aim, Recht «head» wie Joystick / Pfeile; Gäste und Benutzer ohne Kopf-Recht: nur zoomen):
#     nach dem Rahmen dreht der Kopf die Mitte des Bereichs in die Bildmitte (kopf_pic_to_pan, Planer 072). Die Lupe ist dabei
#     «Hand» wie der Joystick (manual_hold): die Runde / der Wertsachen-Blick warten diese Sekunden. Sie dreht den Kopf NICHT
#     (Hinweis mit Grund) bei Not-Aus / Störung, «Aus» (Kopf schaut weg), Folgen / Alarm, Gehtest, Referenz-Scan,
#     Zeitraffer-Position, Wecker, Spielrunde der Spieler, Simulator-Aufgabe (simtask_busy: Testlauf, Platz einrichten …).
#     Morse (639zzz) braucht den Kopf nicht – beides läuft nebeneinander.
#   * Der Ausschnitt folgt dem Ort («Welt»): die Seite merkt den Bereich zusammen mit der Kopf-Richtung (Grad) und rechnet ihn
#     mit der Kopf-Richtung von jetzt (und der des Standbilds) um – dreht der Kopf (Lupe, Runde, Hand), bleibt die Lupe auf dem
#     Ort; ist er nicht mehr im Bild: Hinweis + «🎯» (mit Kopf-Recht). Nur die Kopf-Kamera; Weitwinkel / Wärmebild: fest im Bild.
# Tests: werkzeuge/lupe_test.py (Rechte, Grenzen, Rate, Maske, schärfer als der Strom, Kopf erlaubt / nicht, Browser Handy + PC).
# ----------------------------------------------------------------------------
LUPE_GAP_S = 2.5                  # Pi camera: at most one full-sensor still per 2.5 s (all viewers together)
LUPE_GAP_CHEAP = 0.5              # a source whose sharp picture costs nothing extra (demo)
LUPE_HI_MAX_AGE = 8.0             # a sharp still older than this is not used any more (the frame of the camera instead)
LUPE_WAIT_S = 3.0                 # the request waits this long for a new still (the camera loop takes it)
LUPE_OUT_MAX = 2048               # px: the widest picture a crop returns (phone in landscape, 3x)
LUPE_OUT_MIN = 160
LUPE_MIN_BOX = 0.02               # the smallest region (1/50 of the picture)
LUPE_RATE = (6, 3.0)              # per user / guest address: burst of 6, then 3 per second
LUPE_REFRESH_MS = 1000            # the page fetches a new sharp picture every second while zoomed
LUPE_ZMAX = 12                    # the page zooms at most 12 x
LUPE_DEMO_K = 3                   # the demo still: 3 x the demo picture (2880 x 1620)
LUPE_HI = {"want": 0.0, "ev": threading.Event(), "frame": None, "t": 0.0, "pose": None, "src": 0, "ms": 0, "err": "", "err_t": 0.0,
           "used": 0.0, "n": 0, "size": None}
LUPE_RL = {}
WEB_UI_LOCAL.add("mw-lupe")       # per browser: «🎯 Kopf folgt» / «◐ Scharf»

for _p in ("live",):
    PERM_GET[_p] = tuple(PERM_GET.get(_p, ())) + ("/api/lupe",)       # /api/lupe and /api/lupe/crop.jpg (perm_get_ok)
PERM_POST["head"] = set(PERM_POST.get("head", ())) | {"/api/lupe"}    # POST = turn the head (same right as the joystick)


def lupe_num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def lupe_box(x, y, w, h):
    """a region of the picture 0..1 from the page: numbers, finite - clamped into the picture; None = not usable"""
    v = [lupe_num(a) for a in (x, y, w, h)]
    if any(a is None for a in v):
        return None
    x, y, w, h = v
    w, h = min(1.0, max(LUPE_MIN_BOX, w)), min(1.0, max(LUPE_MIN_BOX, h))
    x, y = min(1.0 - w, max(0.0, x)), min(1.0 - h, max(0.0, y))
    return [x, y, w, h]


def lupe_world_xy(box, ref, pose, fov):
    """(x, y) of a region chosen at head direction ref (pan, tilt °) in a picture taken at pose (°) - not clamped"""
    x, y = box[0], box[1]
    if ref is not None and pose is not None and fov:
        dp = (ref[0] - pose[0] + 180.0) % 360.0 - 180.0
        x += dp / max(1e-6, float(fov[0]))
        y -= (ref[1] - pose[1]) / max(1e-6, float(fov[1]))
    return x, y


def lupe_shift(box, ref, pose, fov):
    """the region chosen while the head looked at ref (pan, tilt °) - where it is in a picture taken at pose (°): the place in
    the world stays, the picture moved. -> (box clamped, how much of it was outside 0..1)"""
    w, h = box[2], box[3]
    x, y = lupe_world_xy(box, ref, pose, fov)
    cx, cy = min(1.0 - w, max(0.0, x)), min(1.0 - h, max(0.0, y))
    return [cx, cy, w, h], max(abs(cx - x) / w, abs(cy - y) / h)


def lupe_rate(key):
    """a bucket per user / guest address: LUPE_RATE[0] at once, then LUPE_RATE[1] per second"""
    now = time.time()
    n, t0 = LUPE_RL.get(key) or (float(LUPE_RATE[0]), now)
    n = min(float(LUPE_RATE[0]), n + (now - t0) * LUPE_RATE[1])
    if n < 1.0:
        LUPE_RL[key] = (n, now)
        return False
    LUPE_RL[key] = (n - 1.0, now)
    if len(LUPE_RL) > 400:
        for k in sorted(LUPE_RL, key=lambda k: LUPE_RL[k][1])[:200]:
            LUPE_RL.pop(k, None)
    return True


def lupe_head_block():
    """'' = the magnifier may turn the head now; else why not (English). The magnifier is «by hand» (like the joystick), but it
    never takes the head from an alarm / following, a measurement or the privacy look-away."""
    if servo_blocked():
        return "emergency stop or servo fault"
    if CFG.get("kopf_parked") and CFG.get("kopf_park") and CFG.get("kopf_on"):
        return "protection is off - the camera looks away"
    if STATE.get("tracking") or KOPF.get("alarm") or KOPF.get("tamper") or KOPF.get("back"):
        return "MoveEye follows a person or an alarm"
    try:
        if walktest_on():
            return "walk test running"
    except NameError:
        pass
    if REFSCAN.get("busy"):
        return "reference scan running"
    if TL_HOLD.get("on"):
        return "timelapse position"
    try:
        if wake_hold():
            return "wake-up alarm"
    except NameError:
        pass
    try:
        if kopf_game_hand():
            return "game round - the players steer"
    except Exception:
        pass
    try:
        if simtask_busy(""):
            return "a simulator task is running"
    except NameError:
        pass
    return ""


def lupe_still_block(w=None):
    """'' = a sharp still may be taken now; else a code: alarm / moving / eco (security and the detection come first)"""
    if STATE.get("persons") or STATE.get("recording") or STATE.get("tracking") or KOPF.get("alarm"):
        return "alarm"
    if not servo_arrived():
        return "moving"
    w = w if w is not None else WATCH_REF.get("w")
    try:
        if (w is not None and getattr(w, "eco_slow", False)) or batt_save_active():
            return "eco"
    except NameError:
        pass
    return ""


def lupe_follow_ok():
    """the place in the world can be followed (a pan / tilt head, the head camera)"""
    try:
        return bool(live_has_head())
    except Exception:
        return False


# ---- the camera loop: a sharp still when a page asks (in the thread of the loop - never two users of the camera at once) ----
def lupe_service(src):
    """called by the read() of a source with lupe_hires() before its normal picture"""
    hi = LUPE_HI
    now = time.time()
    if hi["frame"] is not None and now - hi["used"] > 30.0:
        hi["frame"] = None                                       # nobody looks any more: free the memory (up to 36 MB)
    if not hi["want"] or now > hi["want"]:
        return
    w = WATCH_REF.get("w")
    if w is None or getattr(w, "cap", None) is not src:
        return
    hi["want"] = 0.0
    try:
        if getattr(src, "_lupe_off", 0.0) > now:
            raise RuntimeError(getattr(src, "_lupe_why", "") or "off")
        why = lupe_still_block(w)
        if not why:
            t0 = time.time()
            pose = servo_pos_deg()
            img = src.lupe_hires()                               # BGR, the field of view of the video stream, not turned yet
            img = cam_orient(img)
            pm = CFG.get("picture_mode")
            if pm == "grey" or (pm == "night_grey" and (LIGHTS.get("dark") or (STATE.get("lights") or {}).get("ir"))):
                img = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
            img = apply_privacy(img)                             # privacy zones / sleeping places: black, like the live picture
            hi.update(frame=img, t=time.time(), pose=pose, src=id(src), ms=int((time.time() - t0) * 1000), err="", n=hi["n"] + 1,
                      size=(img.shape[1], img.shape[0]))
    except Exception as e:
        src._lupe_off = time.time() + 60.0
        src._lupe_why = str(e)[:120]
        if time.time() - hi["err_t"] > 60:
            log_event("sys", f"Magnifier: no sharp still from the camera ({str(e)[:120]}) - the live frame is used")
        hi.update(err=str(e)[:120], err_t=time.time())
    finally:
        hi["ev"].set()


def _lupe_pi_hires(self):
    """picamera2: one still in full sensor resolution, cut to the field of view of the video stream (its ScalerCrop)"""
    cam = self.cam
    vc = None
    try:
        vc = (cam.capture_metadata() or {}).get("ScalerCrop")    # the part of the sensor the 1280 x 720 stream shows
    except Exception:
        vc = None
    cfg = getattr(self, "_lupe_cfg", None)
    if cfg is None:
        full = tuple(int(v) for v in cam.sensor_resolution)
        cfg = cam.create_still_configuration(main={"size": full, "format": "RGB888"}, buffer_count=1)
        self._lupe_cfg = cfg
    arr = cam.switch_mode_and_capture_array(cfg, "main")         # stops the video, one still, back to the video
    H, W = arr.shape[:2]
    try:
        aw, ah = (int(v) for v in cam.sensor_resolution)         # the full-resolution mode reads the whole active area
        if vc and len(vc) == 4 and aw > 0 and ah > 0:
            x0, y0 = int(vc[0] / aw * W), int(vc[1] / ah * H)
            x1, y1 = int((vc[0] + vc[2]) / aw * W), int((vc[1] + vc[3]) / ah * H)
            if x1 - x0 > 32 and y1 - y0 > 32:
                arr = arr[max(0, y0):min(H, y1), max(0, x0):min(W, x1)]
    except Exception:
        pass
    return arr


def _lupe_demo_bg(self):
    """the demo scene in LUPE_DEMO_K x the size, with details only a sharp picture shows (a sign next to the tent);
    from now on the normal demo picture is this scene made small (the same scene in both)"""
    hi = getattr(self, "_lupe_bg", None)
    if hi is not None:
        return hi
    k = LUPE_DEMO_K
    W, H = DEMO["size"]
    hi = cv2.resize(np.clip(self.bg, 0, 255).astype(np.uint8), (W * k, H * k), interpolation=cv2.INTER_CUBIC)
    x0, y0 = 772 * k, (self.hz + 58) * k
    cv2.rectangle(hi, (x0 - 2 * k, y0 - 2 * k), (x0 + 64 * k, y0 + 40 * k), (40, 40, 40), -1)
    cv2.rectangle(hi, (x0, y0), (x0 + 62 * k, y0 + 38 * k), (235, 235, 235), -1)
    cv2.putText(hi, "MoveEye", (x0 + 3 * k, y0 + 13 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.36 * k, (20, 20, 20), max(1, k // 2), cv2.LINE_AA)
    cv2.putText(hi, "LUPE 3x", (x0 + 3 * k, y0 + 25 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.30 * k, (30, 30, 160), max(1, k // 2), cv2.LINE_AA)
    for i in range(0, 60 * k, 2):                                # fine stripes: 1 px at 3 x, grey in the small picture
        cv2.line(hi, (x0 + i, y0 + 29 * k), (x0 + i, y0 + 36 * k), (0, 0, 0), 1)
    self._lupe_bg = hi
    self.bg = cv2.resize(hi, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)
    return hi


def _lupe_demo_hires(self):
    """the demo still: the scene as read() draws it, LUPE_DEMO_K x bigger"""
    k = LUPE_DEMO_K
    img = _lupe_demo_bg(self).copy()
    W, H = DEMO["size"]
    t = time.time() - self.t0
    for i, (cx, cy) in enumerate(((120, 60), (420, 90), (760, 50))):
        x = int((cx + t * (6 + i * 2)) % (W + 200)) - 100
        cv2.ellipse(img, (x * k, cy * k), (70 * k, 22 * k), 0, 0, 360, (245, 245, 245), -1)
    cyc = t % 90.0
    if 12 < cyc < 26:
        q = (cyc - 12) / 14.0
        self._person(img, (-40 + q * (W + 80)) * k, (self.hz + 150) * k, 110 * k)
    if 55 < cyc < 66:
        q = (cyc - 55) / 11.0
        big = int(t // 90) % 3 == 2
        self._animal(img, (W + 60 - q * (W + 120)) * k, (self.hz + 210) * k, (2.2 if big else 1.1) * k, (40, 50, 70) if big else (40, 110, 200))
    return img


_lupe_pi_read_base = PiCamSource.read
_lupe_demo_read_base = DemoSource.read


def _lupe_pi_read(self):
    lupe_service(self)
    return _lupe_pi_read_base(self)


def _lupe_demo_read(self):
    _lupe_demo_bg(self)
    lupe_service(self)
    return _lupe_demo_read_base(self)


PiCamSource.lupe_hires = _lupe_pi_hires
PiCamSource.lupe_gap = LUPE_GAP_S
DemoSource.lupe_hires = _lupe_demo_hires
DemoSource.lupe_gap = LUPE_GAP_CHEAP
# wraps: PiCamSource.read
PiCamSource.read = _lupe_pi_read
# wraps: DemoSource.read
DemoSource.read = _lupe_demo_read


# ---- the picture to cut from --------------------------------------------------------------------------------------------------
def lupe_picture(cam):
    """-> (BGR, kind, pose ° or None, age s, note code) or (None, english reason, …). kind: sensor (full-sensor still), frame
    (full camera frame), wide (full frame of the wide-angle camera), shown (the picture as shown: thermal view)"""
    now = time.time()
    if cam == "wide":
        c = view3_wide_cam()
        if c is None:
            return None, "no wide-angle camera", None, 0, ""
        c.raw_until = now + 10
        for _i in range(25):
            if c.raw is not None and now - float(getattr(c, "raw_t", 0) or 0) < 5.0:
                return c.raw, "wide", None, max(0.0, now - float(c.raw_t or now)), ""
            time.sleep(0.06)
        return (c.raw, "wide", None, 0.0, "") if c.raw is not None else (None, "no picture of the wide-angle camera", None, 0, "")
    w = WATCH_REF.get("w")
    if w is None:
        return None, "no camera picture yet", None, 0, ""
    if cam == "thermal":
        f = w.frame_out
        return (f, "shown", servo_pos_deg(), 0.0, "") if f is not None else (None, "no camera picture yet", None, 0, "")
    src = getattr(w, "cap", None)
    note = ""
    if callable(getattr(src, "lupe_hires", None)) and not CFG.get("sim_on"):
        hi = LUPE_HI
        hi["used"] = now
        note = lupe_still_block(w)
        if getattr(src, "_lupe_off", 0.0) > now:
            note = "error"
        elif not note and now - hi["t"] >= float(getattr(src, "lupe_gap", LUPE_GAP_S)):
            hi["ev"].clear()
            hi["want"] = now + LUPE_WAIT_S
            hi["ev"].wait(LUPE_WAIT_S)
            if hi["err"] and now <= hi["err_t"]:
                note = "error"
        f = hi["frame"]
        if f is not None and hi["src"] == id(src) and time.time() - hi["t"] <= LUPE_HI_MAX_AGE:
            return f, "sensor", hi["pose"], max(0.0, time.time() - hi["t"]), note
    if now > w.raw_until:
        w.frame_raw = None
    w.raw_until = now + 10
    for _i in range(25):
        if w.frame_raw is not None:
            break
        time.sleep(0.06)
    f = w.frame_raw
    if f is None:
        return None, "no camera picture yet", None, 0, ""
    return f, "frame", servo_pos_deg(), 0.0, note


def lupe_crop(cam, box, ref, ow):
    """-> (jpeg, headers) or (None, english reason)"""
    img, kind, pose, age, note = lupe_picture(cam)
    if img is None:
        return None, kind
    follow = cam == "head" and lupe_follow_ok()
    b, out = lupe_shift(box, ref if follow else None, pose if follow else None, cam_fov() if follow else None)
    H, W = img.shape[:2]
    x0, y0 = int(b[0] * W), int(b[1] * H)
    x1, y1 = max(x0 + 1, int(round((b[0] + b[2]) * W))), max(y0 + 1, int(round((b[1] + b[3]) * H)))
    part = img[y0:min(H, y1), x0:min(W, x1)]
    ow = int(max(LUPE_OUT_MIN, min(LUPE_OUT_MAX, ow)))
    if part.shape[1] > ow:
        part = cv2.resize(part, (ow, max(1, int(part.shape[0] * ow / part.shape[1]))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", part, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not ok:
        return None, "encode error"
    rb = [x0 / W, y0 / H, (min(W, x1) - x0) / W, (min(H, y1) - y0) / H]
    hd = {"X-Lupe-Src": kind, "X-Lupe-Box": ",".join("%.5f" % v for v in rb), "X-Lupe-Size": "%dx%d" % (W, H),
          "X-Lupe-Age": "%.1f" % age, "X-Lupe-Note": note or "", "X-Lupe-Out": "%.2f" % out,
          "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}
    if follow and pose is not None:
        hd["X-Lupe-Pose"] = "%.3f,%.3f" % (pose[0], pose[1])
    return buf.tobytes(), hd


def lupe_state(who, lang):
    """what the page needs: rights, head, field of view, where the head looks, what is sharp"""
    L = norm_lang(lang)
    w = WATCH_REF.get("w")
    src = getattr(w, "cap", None) if w is not None else None
    hf, vf = cam_fov()
    p, t = servo_pos_deg()
    hr = bool(who and who.get("head"))
    blk = lupe_head_block()
    return {"ok": True, "head_right": hr, "has_head": lupe_follow_ok(), "fov": [round(float(hf), 3), round(float(vf), 3)],
            "pose": [round(p, 3), round(t, 3)], "moving": not servo_arrived(), "block": tr(blk, L) if blk else "",
            "sharp": "sensor" if callable(getattr(src, "lupe_hires", None)) and not CFG.get("sim_on") else "frame",
            "pause": lupe_still_block(w) if src is not None else "", "refresh_ms": LUPE_REFRESH_MS, "zmax": LUPE_ZMAX,
            "wide": bool(view3_wide_cam())}


def lupe_aim(box, who_panel, lang):
    """turn the head so that the middle of the region comes to the middle of the picture -> (ok, http code, reply)"""
    L = norm_lang(lang)
    why = lupe_head_block()
    if why:
        return False, 409, {"ok": False, "msg": tr("The head does not follow:", L) + " " + tr(why, L), "block": tr(why, L)}
    p0 = servo_pos_deg()
    pan, tilt = kopf_pic_to_pan(box[0] + box[2] / 2, box[1] + box[3] / 2)
    if not servo_goto(pan, tilt, who="lupe", wait=False):
        return False, 409, {"ok": False, "msg": tr("The head does not follow:", L) + " " + tr("emergency stop or servo fault", L)}
    MANUAL["until"] = time.time() + float(CFG.get("manual_hold", 5.0))        # by hand, like the joystick (the round waits)
    try:
        servo_driver_note(who_panel, "lupe")
    except Exception:
        pass
    return True, 200, {"ok": True, "from": [round(p0[0], 3), round(p0[1], 3)], "to": [round(pan, 3), round(tilt, 3)]}


# ---- web: /api/lupe (GET state, POST aim), /api/lupe/crop.jpg; guests /g/<token>/lupe(/crop.jpg) -------------------------------
_smalltv_routes_639zzzl = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzzl
    _smalltv_routes_639zzzl(app, reply, body)
    from flask import Response, request, g

    def crop_reply(a, key, cam, L):
        if not lupe_rate(key):
            return reply({"ok": False, "msg": tr("Too many requests in a short time - wait a few minutes.", L)}, 429)
        box = lupe_box(a.get("x"), a.get("y"), a.get("w"), a.get("h"))
        if box is None:
            return reply({"ok": False, "msg": "x, y, w, h: numbers 0..1"}, 400)
        ref = None
        if a.get("ref"):
            r = [lupe_num(v) for v in str(a.get("ref")).split(",")[:2]]
            if len(r) != 2 or None in r or abs(r[0]) > 400 or abs(r[1]) > 400:
                return reply({"ok": False, "msg": "ref: pan,tilt in degrees"}, 400)
            ref = r
        ow = lupe_num(a.get("ow")) or 1024
        jpg, hd = lupe_crop(cam, box, ref, ow)
        if jpg is None:
            return reply({"ok": False, "msg": tr_err(hd, L)}, 503)
        return Response(jpg, mimetype="image/jpeg", headers=hd)

    def cam_of(a):
        c = str(a.get("cam") or "head")
        return c if c in ("head", "wide", "thermal") else "head"

    @app.route("/api/lupe", methods=["GET", "POST"])
    def api_lupe():
        who = unt_perms(g)
        if request.method == "GET":
            L = norm_lang(request.args.get("lang") or CFG.get("lang"))
            if not who["live"]:
                return reply({"ok": False, "msg": tr("not allowed for your user", L)}, 403)
            return reply(lupe_state(who, L))
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        if not who["head"]:
            return reply({"ok": False, "msg": tr("You may zoom but not move the head.", L)}, 403)
        if d.get("action") != "aim":
            return reply({"ok": False, "msg": "unknown action"}, 400)
        if cam_of(d) != "head":
            return reply({"ok": False, "msg": tr("The head follows only in the head view.", L)}, 400)
        b = d.get("box") if isinstance(d.get("box"), list) else []
        box = lupe_box(*(b + [None] * 4)[:4])
        if box is None:
            return reply({"ok": False, "msg": "box: [x, y, w, h] 0..1"}, 400)
        ok, code, res = lupe_aim(box, servo_client(request, d), L)
        return reply(res, code)

    @app.route("/api/lupe/crop.jpg")
    def api_lupe_crop():
        who = unt_perms(g)
        L = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if not who["live"]:
            return reply({"ok": False, "msg": tr("not allowed for your user", L)}, 403)
        return crop_reply(request.args, "u|" + who["key"], cam_of(request.args), L)

    def guest_cam():                                     # the guest stream is the main picture (with the thermal picture over it)
        return "thermal" if CFG.get("thermal_on") and CFG.get("thermal_source") else "head"

    @app.route("/g/<token>/lupe")
    def guest_lupe(token):
        if not guest_ok(token):
            return reply({"ok": False}, 404)
        return reply(dict(lupe_state(None, sx_req_lang()), cam=guest_cam()))

    @app.route("/g/<token>/lupe/crop.jpg")
    def guest_lupe_crop(token):
        if not guest_ok(token):
            return reply({"ok": False}, 404)
        return crop_reply(request.args, "g|" + (request.remote_addr or "?"), guest_cam(), sx_req_lang())

    @app.after_request
    def lupe_guest_inject(resp):
        try:
            p = request.path
            if (p.startswith("/g/") and p.count("/") == 2 and resp.status_code == 200 and resp.mimetype == "text/html"
                    and not resp.direct_passthrough):
                html = resp.get_data(as_text=True)
                if "/*LUPEG*/" in html:
                    html = html.replace("/*LUPEG*/", lupe_guest_js(sx_req_lang(), p.split("/")[2]).replace("</script", "<\\/script"), 1)
                    resp.set_data(html)
        except Exception:
            pass
        return resp


# ---- the page (component: one button in #lv-tools / #vo-lupe in full screen + one layer over the picture) -----------------------
LUPE_CSS = r"""
/* 639zzzl «Lupe»: one layer exactly over the shown picture (above the picture, below the joystick #lv-joy z5 and the buttons z6) */
.lupe-ov{position:absolute;z-index:4;overflow:hidden;touch-action:none;-webkit-touch-callout:none;-webkit-user-select:none;user-select:none;
  outline:2px solid rgba(255,211,77,.85);outline-offset:-2px;cursor:crosshair}
.lupe-ov.zoomed{cursor:grab;outline-color:rgba(255,211,77,.45)}
.lupe-ov .lupe-hi{position:absolute;max-width:none;pointer-events:none;display:block}
.lupe-ov .lupe-hi[hidden]{display:none}
.lupe-ov .lupe-sel{position:absolute;border:2px dashed #ffd34d;background:rgba(255,211,77,.12);box-sizing:border-box;pointer-events:none}
.lupe-ov .lupe-sel[hidden]{display:none}
.lupe-ov .lupe-top{position:absolute;left:6px;top:6px;right:6px;display:flex;flex-direction:column;align-items:flex-start;gap:5px;pointer-events:none}
.lupe-ov .lupe-bar{display:flex;flex-wrap:wrap;gap:5px;max-width:100%;pointer-events:auto}
/* same look as the buttons on the live picture (#lv-tools 536) */
.lupe-ov .lupe-bar button{height:38px;min-width:38px;padding:0 8px;border-radius:10px;border:1px solid rgba(255,255,255,.3);background:rgba(8,12,20,.55);
  color:#fff;font:600 13px/1 system-ui,-apple-system,sans-serif;display:inline-flex;align-items:center;justify-content:center;gap:4px;cursor:pointer;
  white-space:nowrap;-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px);touch-action:manipulation}
.lupe-ov .lupe-bar button.on{background:rgba(47,129,247,.75);border-color:rgba(255,255,255,.7)}
.lupe-ov .lupe-bar button[hidden]{display:none}
.lupe-ov .lupe-bar button:focus-visible{outline:2px solid #ffd34d;outline-offset:2px}
.lupe-ov .lupe-msg{max-width:100%;box-sizing:border-box;padding:4px 8px;border-radius:8px;background:rgba(8,12,20,.66);color:#fff;
  font:12.5px/1.35 system-ui,-apple-system,sans-serif;overflow-wrap:anywhere;pointer-events:none}   /* the picture under it stays usable */
.lupe-ov .lupe-msg:empty{display:none}
.lupe-ov .lupe-msg button{margin-left:6px;height:28px;padding:0 8px;border-radius:8px;border:1px solid rgba(255,255,255,.4);background:rgba(47,129,247,.7);color:#fff;font:inherit;pointer-events:auto}
body.lupe-on #lv-tools,body.lupe-on #kw-row,body.lupe-on #v3-mini,body.lupe-on #vo-side,body.lupe-on #vo-mv,body.lupe-on #vo-lupe,
body.lupe-on #unt-ov{display:none!important}
#vo-lupe{display:none}
body.videoonly #vo-lupe{display:flex;position:absolute;top:max(10px,env(safe-area-inset-top));right:calc(max(10px,env(safe-area-inset-right)) + 112px);z-index:60;
  width:44px;height:44px;align-items:center;justify-content:center;border-radius:50%;border:1px solid rgba(255,255,255,.35);
  background:rgba(0,0,0,.55);color:#fff;padding:0;cursor:pointer;transition:opacity .2s ease}
body.videoonly.moveravail #vo-lupe{right:calc(max(10px,env(safe-area-inset-right)) + 168px)}
body.sim-on.videoonly #vo-lupe{right:calc(max(10px,env(safe-area-inset-right)) + 56px)}
body.lvc-auto:not(.lvc-show) #vo-lupe{opacity:0!important;pointer-events:none!important;transition:opacity .7s ease}
#vo-lupe svg,#lv-b-lupe svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
#g-lupe{margin:8px auto 0;display:block;background:#1a2433;color:#fff;border:1px solid #2a3442;border-radius:10px;padding:8px 16px;font:inherit}
"""

LUPE_JS = r"""
(function () {
  if (window.mwLupe) return;
  const G = window.LUPE_CFG || {};                         // {api, img, tools: "live" | "guest", guest}
  const TX = window.LUPE_TX || null;
  const t = k => (TX && TX[k]) || (typeof window.t === "function" ? window.t(k) : k);
  const E = (tag, cls, x) => { const e = document.createElement(tag); if (cls) e.className = cls; if (x != null) e.textContent = x; return e; };
  const L = () => (typeof LANG !== "undefined" ? LANG : "");
  const img = () => document.querySelector(G.img);
  const IC = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21M10.5 7.5v6M7.5 10.5h6"/></svg>';
  const S = {on: false, v: [0, 0, 1], R: null, P: [0, 0], info: {}, follow: true, sharp: true, hi: null, busy: false, timer: 0, poll: 0,
             fast: 0, g: null, tap: null, note: "", rnote: "", hint: "", hintT: 0, aimMsg: "", aimT: 0, cam: "head", n: 0, back: 0, url: ""};
  let OV = null, HI = null, SEL = null, BAR = null, MSG = null, B1 = null, BH = null, BS = null, WRAP = null;
  try { const s = JSON.parse(localStorage.getItem("mw-lupe") || "{}"); if (s.follow === 0) S.follow = false; if (s.sharp === 0) S.sharp = false; } catch (e) {}
  const save = () => { try { localStorage.setItem("mw-lupe", JSON.stringify({follow: S.follow ? 1 : 0, sharp: S.sharp ? 1 : 0})); } catch (e) {} };
  const api = p => G.api + p;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const ZMAX = () => S.info.zmax || 12;
  // ---- which camera the big picture shows (head / wide / thermal) - another source (Kamerawahl) is only enlarged ----
  function cam() {
    if (G.guest) return S.info.cam || "head";
    const im = img(); let s = (im && (im.src || "")) || ""; if (!s || s.startsWith("data:") || s.startsWith("blob:")) s = (im && im.dataset.src) || "";
    if (s.indexOf("/cam_view/") >= 0) return "digital";
    if (s.indexOf("/cam_feed/") >= 0) return S.info.wide ? "wide" : "digital";
    if (s.indexOf("/video_feed") < 0 && s) return "digital";
    const J = (typeof QSJ !== "undefined" && QSJ) || {};
    if ((J.cfg || {}).thermal_on && (J.cfg || {}).thermal_source) return "thermal";
    return "head";
  }
  const followOk = () => S.cam === "head" && !!S.info.has_head && Array.isArray(S.info.fov);
  const canAim = () => !G.guest && S.cam === "head" && !!S.info.head_right && !!S.info.has_head;
  // ---- geometry: the shown picture inside its box (object-fit: contain) ----
  function rect() {
    const im = img(); if (!im || !im.naturalWidth || !im.offsetWidth) return null;
    const ow = im.offsetWidth, oh = im.offsetHeight, nw = im.naturalWidth, nh = im.naturalHeight || 1;
    const k = Math.min(ow / nw, oh / nh), cw = nw * k, ch = nh * k;
    return {ow: ow, oh: oh, cx: (ow - cw) / 2, cy: (oh - ch) / 2, cw: cw, ch: ch, L: im.offsetLeft, T: im.offsetTop};
  }
  function shift(b, ref) {                              // a region at head direction ref -> the picture of now (the place stays)
    let x = b[0], y = b[1];
    if (ref && followOk()) { const f = S.info.fov; let dp = ((ref[0] - S.P[0] + 540) % 360) - 180; x += dp / f[0]; y -= (ref[1] - S.P[1]) / f[1]; }
    return [x, y];
  }
  function view() {                                     // the view in the coordinates of the picture now, clamped
    const s = S.v[2], [x, y] = shift(S.v, S.R);
    const cx = clamp(x, 0, 1 - s), cy = clamp(y, 0, 1 - s);
    return [cx, cy, s, Math.max(Math.abs(cx - x), Math.abs(cy - y)) / s];
  }
  function setView(x, y, s) {                           // from a gesture: relative to the head direction of now
    s = clamp(s, 1 / ZMAX(), 1);
    S.v = [clamp(x, 0, 1 - s), clamp(y, 0, 1 - s), s]; S.R = followOk() ? S.P.slice() : null;
    paint();
  }
  function unstyle() { const im = img(); if (!im) return; im.style.transform = ""; im.style.transformOrigin = ""; im.style.clipPath = ""; im.style.webkitClipPath = ""; }
  function paint() {
    if (!OV) return;
    const im = img(), r = rect();
    if (!im || !r || im.parentNode !== WRAP) { if (im && im.parentNode !== WRAP) close(); return; }
    OV.style.left = (r.L + r.cx) + "px"; OV.style.top = (r.T + r.cy) + "px"; OV.style.width = r.cw + "px"; OV.style.height = r.ch + "px";
    const [x, y, s, out] = view(), z = 1 / s;
    OV.classList.toggle("zoomed", s < 0.999);
    if (s >= 0.999) unstyle();
    else {
      const tx = r.cx * (1 - z) - z * x * r.cw, ty = r.cy * (1 - z) - z * y * r.ch;
      im.style.transformOrigin = "0 0"; im.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + z + ")";
      const ci = "inset(" + ((r.cy - ty) / z) + "px " + (r.ow - (r.cx + r.cw - tx) / z) + "px " + (r.oh - (r.cy + r.ch - ty) / z) + "px " + ((r.cx - tx) / z) + "px)";
      im.style.clipPath = ci; im.style.webkitClipPath = ci;
    }
    const c = S.hi;
    if (c && S.sharp && s < 0.95 && S.cam !== "digital") {
      const [bx, by] = c.pose ? shift(c.box, c.pose) : [c.box[0], c.box[1]];
      HI.style.left = ((bx - x) / s * 100) + "%"; HI.style.top = ((by - y) / s * 100) + "%";
      HI.style.width = (c.box[2] / s * 100) + "%"; HI.style.height = (c.box[3] / s * 100) + "%"; HI.hidden = false;
    } else HI.hidden = true;
    if (BH) { BH.hidden = !canAim(); BH.classList.toggle("on", S.follow); BH.setAttribute("aria-pressed", S.follow ? "true" : "false"); }
    if (BS) { BS.hidden = S.cam === "digital"; BS.classList.toggle("on", S.sharp); BS.setAttribute("aria-pressed", S.sharp ? "true" : "false"); }
    if (B1) B1.hidden = s >= 0.999;
    message(z, out);
  }
  function message(z, out) {
    const now = Date.now(), parts = [];
    const head = "×" + (z < 9.95 ? z.toFixed(1) : Math.round(z));
    let src = "";
    if (z > 1.001) {
      if (S.cam === "digital" || S.cam === "thermal") src = t("only enlarged - no sharper source");
      else if (!S.sharp) src = t("live picture, enlarged");
      else if (S.hi) src = ({sensor: t("sharp: full camera sensor"), frame: t("sharp: full camera picture"), wide: t("sharp: full wide-angle picture"),
                             shown: t("only enlarged - no sharper source")})[S.hi.src] || "";
      if (S.hi && S.sharp && S.hi.src === "sensor" && S.hi.age >= 1.5) src += " · " + Math.round(S.hi.age) + " s";
    }
    parts.push(head + (src ? " · " + src : ""));
    const nt = S.sharp && z > 1.001 && S.hi ? S.hi.note : "";
    if (nt) parts.push(({alarm: t("Sharp picture paused: alarm or person in view"), moving: t("Sharp picture paused while the head moves"),
                         eco: t("Sharp picture paused: battery saving"), error: t("No sharp picture from the camera - the live picture is used")})[nt] || "");
    if (S.note) parts.push(S.note);
    if (S.rnote) parts.push(S.rnote);
    if (S.aimMsg && now < S.aimT) parts.push(S.aimMsg);
    if (S.hint && now < S.hintT) parts.push(S.hint);
    const txt = parts.filter(Boolean).join(" · ");
    const showOut = out > 0.5 && z > 1.001 && followOk();
    const key = txt + (showOut ? "|o" + canAim() : "");
    if (MSG.dataset.k === key) return;
    MSG.dataset.k = key; MSG.textContent = txt;
    if (showOut) {
      MSG.append(document.createTextNode(" · " + t("The area is no longer in the picture")));
      if (canAim()) { const b = E("button", "", "🎯"); b.type = "button"; b.title = t("Turn the head there"); b.setAttribute("aria-label", t("Turn the head there"));
        b.onclick = e => { e.stopPropagation(); const v = S.v; const [x, y] = shift(v, S.R); aim([x, y, v[2], v[2]]); }; MSG.append(b); }
    }
  }
  // ---- open / close ----
  function build() {
    const im = img(); if (!im) return false;
    WRAP = im.parentNode;
    OV = E("div", "lupe-ov"); OV.id = "lupe-ov"; OV.setAttribute("role", "application"); OV.setAttribute("aria-label", t("Magnifier"));
    HI = E("img", "lupe-hi"); HI.alt = ""; HI.hidden = true; HI.draggable = false;
    SEL = E("div", "lupe-sel"); SEL.hidden = true;
    const top = E("div", "lupe-top"); BAR = E("div", "lupe-bar"); MSG = E("div", "lupe-msg"); MSG.setAttribute("aria-live", "polite");
    const btn = (txt, tip, fn) => { const b = E("button", "", txt); b.type = "button"; b.title = t(tip); b.setAttribute("aria-label", t(tip));
      b.addEventListener("click", e => { e.stopPropagation(); fn(); }); b.addEventListener("dblclick", e => e.stopPropagation()); BAR.append(b); return b; };
    const bx = btn("✕ " + t("Magnifier"), "Close the magnifier (Esc)", close); bx.id = "lupe-x";
    B1 = btn("1:1", "Whole picture (double tap)", () => { S.v = [0, 0, 1]; S.R = null; S.hi = null; paint(); }); B1.id = "lupe-1";
    BH = btn("🎯 " + t("Head follows"), "The head turns the chosen area to the middle", () => { S.follow = !S.follow; save(); paint(); }); BH.id = "lupe-head";
    BS = btn("◐ " + t("Sharp"), "Sharp picture from the camera (off: live picture, only enlarged)", () => { S.sharp = !S.sharp; save(); if (S.sharp) fetchHi(); paint(); }); BS.id = "lupe-sharp";
    top.append(BAR, MSG); OV.append(HI, SEL, top); WRAP.appendChild(OV);
    OV.addEventListener("click", e => e.stopPropagation());
    OV.addEventListener("dblclick", e => { e.stopPropagation(); e.preventDefault(); });
    OV.addEventListener("contextmenu", e => e.preventDefault());
    OV.addEventListener("mousedown", mDown);
    OV.addEventListener("wheel", wheel, {passive: false});
    OV.addEventListener("gesturestart", e => e.preventDefault());      // iPhone Safari: no page zoom inside the picture
    OV.addEventListener("gesturechange", e => e.preventDefault());
    return true;
  }
  async function open(why) {
    if (S.on) return true;
    try { if (window.mwUntersuchen) window.mwUntersuchen.close(); } catch (e) {}
    if (!build()) return false;
    S.on = true; S.v = [0, 0, 1]; S.R = null; S.hi = null; S.note = ""; S.rnote = ""; S.cam = cam();
    document.body.classList.add("lupe-on");
    S.hint = t("Drag a box over the area or zoom with two fingers (PC: mouse wheel). Double tap = whole picture."); S.hintT = Date.now() + 4000;
    paint();
    await info(); S.cam = cam(); paint();
    if (!S.info.ok && S.info.msg) { S.note = S.info.msg; paint(); }
    else if (!G.guest && S.cam === "head" && S.info.has_head && !S.info.head_right) { S.rnote = t("You may zoom but not move the head."); paint(); }
    pollLoop(); S.timer = setTimeout(fetchHi, 300);
    return true;
  }
  function close() {
    if (!S.on) return;
    S.on = false; S.g = null; clearTimeout(S.timer); clearTimeout(S.poll); unstyle();
    if (OV) OV.remove(); OV = null; if (S.url) { URL.revokeObjectURL(S.url); S.url = ""; }
    document.body.classList.remove("lupe-on");
  }
  async function info() {
    try { const r = await fetch(api("?lang=" + L()), {cache: "no-store"}); const j = await r.json(); if (r.ok) { S.info = j; if (Array.isArray(j.pose)) S.P = j.pose; } else S.info = {ok: false, msg: j.msg || ""}; }
    catch (e) { S.info = S.info || {}; }
  }
  function pollLoop() {                                   // where the head looks now (fast for a few seconds after «aim»)
    clearTimeout(S.poll); if (!S.on) return;
    const fast = Date.now() < S.fast || !!S.info.moving;
    S.poll = setTimeout(async () => { if (!S.on) return; await info(); paint(); pollLoop(); }, fast ? 200 : (followOk() ? 1000 : 2500));
  }
  // ---- the sharp picture from MoveEye ----
  async function fetchHi() {
    clearTimeout(S.timer); if (!S.on) return;
    const again = ms => { S.timer = setTimeout(fetchHi, ms); };
    const [x, y, s] = view();
    if (S.busy) return;
    if (!S.sharp || s >= 0.95 || S.cam === "digital" || S.g) return again(S.info.refresh_ms || 1000);
    S.busy = true;
    const r = OV.getBoundingClientRect(), ow = Math.round(clamp(r.width * (window.devicePixelRatio || 1), 160, 2048));
    let q = "cam=" + S.cam + "&x=" + x.toFixed(5) + "&y=" + y.toFixed(5) + "&w=" + s.toFixed(5) + "&h=" + s.toFixed(5) + "&ow=" + ow + "&lang=" + L();
    if (followOk()) q += "&ref=" + S.P[0].toFixed(3) + "," + S.P[1].toFixed(3);
    let wait = S.info.refresh_ms || 1000;
    try {
      const res = await fetch(api("/crop.jpg?" + q + "&n=" + (++S.n)), {cache: "no-store"});
      if (res.status === 429) wait = 2500;
      else if (res.ok) {
        const H = k => res.headers.get(k) || "";
        const b = await res.blob(), u = URL.createObjectURL(b);
        const pi = new Image(); pi.src = u; try { await pi.decode(); } catch (e) {}
        if (!S.on) { URL.revokeObjectURL(u); S.busy = false; return; }
        HI.src = u; if (S.url) URL.revokeObjectURL(S.url); S.url = u;
        const box = H("X-Lupe-Box").split(",").map(Number), pp = H("X-Lupe-Pose");
        S.hi = {box: box.length === 4 && box.every(isFinite) ? box : [x, y, s, s], pose: pp ? pp.split(",").map(Number) : null, src: H("X-Lupe-Src"),
                age: parseFloat(H("X-Lupe-Age")) || 0, note: H("X-Lupe-Note"), size: H("X-Lupe-Size")};
        if (S.note && !S.info.block) S.note = "";
      } else { let j = {}; try { j = await res.json(); } catch (e) {} S.hi = null; S.note = j.msg || ""; wait = 3000; }
    } catch (e) { wait = 3000; }
    S.busy = false; paint(); if (S.on) again(wait);
  }
  const soon = () => { clearTimeout(S.timer); S.timer = setTimeout(fetchHi, 220); };
  // ---- the head turns the area to the middle ----
  async function aim(box) {
    if (!canAim() || !S.follow) return;
    S.aimMsg = "🎯 " + t("The head turns to the area …"); S.aimT = Date.now() + 4000; paint();
    let j = {};
    try { const r = await fetch(api(""), {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: "aim", cam: S.cam, box: box, lang: L()})}); j = await r.json(); j._c = r.status; }
    catch (e) { j = {ok: false, msg: t("No connection to MoveEye.")}; }
    if (!j.ok) { S.aimMsg = j.msg || ""; S.aimT = Date.now() + 7000; }
    else {                                                // the box belongs to the head direction of this moment (the page may know an older one)
      if (Array.isArray(j.from) && followOk()) { const sh = shift(S.v, S.R); S.P = j.from.slice(); S.v = [sh[0], sh[1], S.v[2]]; S.R = j.from.slice(); }
      S.fast = Date.now() + 6000; pollLoop();
    }
    paint();
  }
  // ---- gestures: touch (finger), mouse (PC) ----
  function nrm(cx, cy) { const r = OV.getBoundingClientRect(); return [(cx - r.left) / r.width, (cy - r.top) / r.height]; }
  function start(pts) {
    const [x, y, s] = view();
    if (pts.length >= 2) {
      const a = pts[0], b = pts[1], d = Math.hypot(a[0] - b[0], a[1] - b[1]) || 0.01, m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      S.g = {k: "pinch", d0: d, s0: s, p: [x + m[0] * s, y + m[1] * s], moved: true}; SEL.hidden = true;
    } else {
      const p = pts[0];
      S.g = {k: s < 0.999 ? "pan" : "box", a: p, last: p, t0: Date.now(), moved: false, v0: [x, y, s]};
    }
  }
  function move(pts) {
    const g = S.g; if (!g) return;
    if (g.k === "pinch" && pts.length >= 2) {
      const a = pts[0], b = pts[1], d = Math.hypot(a[0] - b[0], a[1] - b[1]) || 0.01, m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      const s = clamp(g.s0 * g.d0 / d, 1 / ZMAX(), 1);
      setView(g.p[0] - m[0] * s, g.p[1] - m[1] * s, s);
      return;
    }
    if (g.k === "pinch") return;
    const p = pts[0];
    if (Math.hypot((p[0] - g.a[0]) * OV.clientWidth, (p[1] - g.a[1]) * OV.clientHeight) > 8) g.moved = true;
    if (g.k === "pan") { const [x, y, s] = view(); setView(x - (p[0] - g.last[0]) * s, y - (p[1] - g.last[1]) * s, s); g.last = p; }
    else if (g.moved) {
      const x0 = clamp(Math.min(g.a[0], p[0]), 0, 1), y0 = clamp(Math.min(g.a[1], p[1]), 0, 1), x1 = clamp(Math.max(g.a[0], p[0]), 0, 1), y1 = clamp(Math.max(g.a[1], p[1]), 0, 1);
      g.box = [x0, y0, x1 - x0, y1 - y0];
      SEL.hidden = false; SEL.style.left = x0 * 100 + "%"; SEL.style.top = y0 * 100 + "%"; SEL.style.width = (x1 - x0) * 100 + "%"; SEL.style.height = (y1 - y0) * 100 + "%";
    }
  }
  function end(p) {
    const g = S.g; S.g = null; SEL.hidden = true; if (!g) return;
    if (g.k === "box" && g.moved && g.box && g.box[2] > 0.02 && g.box[3] > 0.02) {
      const [vx, vy, vs] = g.v0, b = [vx + g.box[0] * vs, vy + g.box[1] * vs, g.box[2] * vs, g.box[3] * vs];
      const s = clamp(Math.max(b[2], b[3]), 1 / ZMAX(), 1);
      setView(b[0] + b[2] / 2 - s / 2, b[1] + b[3] / 2 - s / 2, s);
      S.hint = t("One finger moves, two fingers zoom, double tap = whole picture."); S.hintT = Date.now() + 5000;
      aim(b); soon(); paint(); return;
    }
    if (g.k !== "pinch" && !g.moved && Date.now() - g.t0 < 400 && p) {            // a tap: a second one soon after = double tap
      const n = Date.now(), q = S.tap;
      if (q && n - q.t < 350 && Math.hypot((p[0] - q.p[0]) * OV.clientWidth, (p[1] - q.p[1]) * OV.clientHeight) < 40) { S.tap = null; dbl(); return; }
      S.tap = {t: n, p: p}; return;
    }
    soon();
  }
  function dbl() { if (view()[2] < 0.999) { S.v = [0, 0, 1]; S.R = null; S.hi = null; paint(); } else close(); }
  // touch: the listener sits on the box of the picture (capture), so a pinch that starts on the normal picture opens the magnifier
  const TT = e => Array.from(e.touches).map(x => nrm(x.clientX, x.clientY));
  const onBar = e => !!(e.target && e.target.closest && e.target.closest(".lupe-bar, .lupe-msg button"));
  const blocked = el => !!(el && el.closest && el.closest("#lv-tools, #lv-joy, #kw-row, #v3-mini, #vo-ctl, #vo-exit, #vo-side, #vo-mv, #vo-lupe, button, a, input, .unt-ov.sel, #unt-bar"));
  function tStart(e) {
    if (S.on && S.g) { e.preventDefault(); if (e.touches.length >= 2) start(TT(e)); return; }
    if (S.on) {
      if (!OV || !OV.contains(e.target) || onBar(e)) return;
      e.preventDefault(); start(TT(e)); return;
    }
    if (e.touches.length === 2 && !blocked(e.touches[0].target) && !blocked(e.touches[1].target) && !document.body.classList.contains("pv-on")
        && !document.querySelector(".unt-ov.sel") && img() && img().naturalWidth) {
      e.preventDefault();
      open("pinch");                                      // builds the layer at once (before its first await): the pinch goes on there
      if (S.on && OV && !S.g) start(TT(e));
    }
  }
  function tMove(e) { if (!S.on || !S.g) return; e.preventDefault(); const pts = TT(e); if (pts.length) move(pts); }
  function tEnd(e) {
    if (!S.on || !S.g) return; e.preventDefault();
    if (e.touches.length >= 1) { if (S.g.k === "pinch") { S.g = {k: "pan", a: TT(e)[0], last: TT(e)[0], t0: 0, moved: true}; } return; }
    const c = e.changedTouches && e.changedTouches[0];
    end(c ? nrm(c.clientX, c.clientY) : null);
  }
  // mouse (PC): drag = box (whole picture) or move (zoomed), wheel = zoom at the pointer, double click = 1:1, Esc = close
  function mDown(e) {
    if (e.button !== 0 || onBar(e)) return; e.preventDefault();
    start([nrm(e.clientX, e.clientY)]);
    const mm = ev => move([nrm(ev.clientX, ev.clientY)]);
    const mu = ev => { removeEventListener("mousemove", mm, true); removeEventListener("mouseup", mu, true); end(nrm(ev.clientX, ev.clientY)); };
    addEventListener("mousemove", mm, true); addEventListener("mouseup", mu, true);
  }
  function wheelAt(e) {
    const [mx, my] = nrm(e.clientX, e.clientY), [x, y, s] = view();
    const k = Math.exp(clamp(e.deltaY, -200, 200) * (e.ctrlKey ? 0.01 : 0.0022)), ns = clamp(s * k, 1 / ZMAX(), 1);
    setView(x + mx * s - mx * ns, y + my * s - my * ns, ns); soon();
  }
  function wheel(e) { if (!S.on) return; e.preventDefault(); e.stopPropagation(); wheelAt(e); }
  function hook() {
    const im = img(); if (!im) return setTimeout(hook, 500);
    const w = im.parentNode;
    if (w.dataset.lupe === "1") return; w.dataset.lupe = "1";
    w.addEventListener("touchstart", tStart, {passive: false, capture: true});
    w.addEventListener("touchmove", tMove, {passive: false, capture: true});
    w.addEventListener("touchend", tEnd, {passive: false, capture: true});
    w.addEventListener("touchcancel", tEnd, {passive: false, capture: true});
    w.addEventListener("wheel", e => {                    // trackpad pinch / Ctrl + wheel over the normal picture: the magnifier, not the page
      if (S.on || !e.ctrlKey || blocked(e.target) || !img() || !img().naturalWidth) return;
      e.preventDefault(); open("wheel"); if (S.on && OV) wheelAt(e);
    }, {passive: false});
    if (G.tools === "live" && !document.getElementById("vo-lupe")) {      // full screen: a round button next to ✕ / ⇆
      const b = E("button"); b.id = "vo-lupe"; b.type = "button"; b.innerHTML = IC; b.title = t("Magnifier: drag a box, zoom with two fingers");
      b.setAttribute("aria-label", t("Magnifier")); b.addEventListener("click", e => { e.stopPropagation(); S.on ? close() : open("button"); });
      b.addEventListener("dblclick", e => e.stopPropagation()); w.appendChild(b);
    }
  }
  addEventListener("keydown", e => { if (S.on && e.key === "Escape") { e.preventDefault(); close(); } });
  addEventListener("resize", () => { if (S.on) paint(); });
  setInterval(() => { if (S.on) { const c = cam(); if (c !== S.cam) { S.cam = c; S.hi = null; } paint(); } }, 400);
  function tools() {
    if (G.tools === "live") {
      const tb = document.getElementById("lv-tools"); if (!tb) return setTimeout(tools, 400);
      if (document.getElementById("lv-b-lupe")) return;
      const b = E("button"); b.type = "button"; b.id = "lv-b-lupe"; b.innerHTML = IC; b.title = t("Magnifier: drag a box, zoom with two fingers");
      b.setAttribute("aria-label", t("Magnifier"));
      b.onclick = e => { e.stopPropagation(); S.on ? close() : open("button"); }; b.addEventListener("dblclick", e => e.stopPropagation());
      tb.insertBefore(b, document.getElementById("lv-b-view") || null);
    } else if (G.tools === "guest") {
      const f = document.getElementById("ft"); if (!f || document.getElementById("g-lupe")) return;
      const b = E("button", "", "🔍 " + t("Magnifier")); b.id = "g-lupe"; b.type = "button"; b.onclick = () => (S.on ? close() : open("button"));
      f.parentNode.insertBefore(b, f.nextSibling);
    }
  }
  window.mwLupe = {open: open, close: close, state: () => ({on: S.on, view: view(), ref: S.R, pose: S.P, cam: S.cam, hi: S.hi, follow: S.follow, sharp: S.sharp,
                   canAim: canAim(), info: S.info, msg: MSG ? MSG.textContent : ""}), zoomTo: b => { const s = clamp(Math.max(b[2], b[3]), 1 / ZMAX(), 1);
                   setView(b[0] + b[2] / 2 - s / 2, b[1] + b[3] / 2 - s / 2, s); soon(); }};
  tools(); hook();
})();
"""



# ---- the window (Tk, Besitzer: «Web und Fenster immer beide»): «🔍 Lupe» on the live picture ------------------------------------
# The same source and rules as the web: the sharp part comes from lupe_crop() (Pi: full-sensor still in the camera loop, privacy
# zones black, pauses), the bucket lupe_rate("tk|window"), turning the head lupe_aim() / lupe_head_block() (the window is the
# administrator at the device, like «Untersuchen» 639zze), the place in the world lupe_shift() / lupe_world_xy(). Only drawing and the
# mouse are here: drag = box (whole picture) or move (zoomed), wheel = zoom at the pointer, double click = 1:1 / close, Esc / «✕ Lupe».
# The touch screen of the Pi gives Tk mouse events (one finger: drag / double tap; no pinch in Tk - the wheel or a box instead).
LUPE_TK_KEY = "tk|window"


def lupe_tk_cam():
    """which camera the big picture of the window shows (639zv): head / wide / thermal"""
    try:
        return v3_cur()
    except Exception:
        return "thermal" if CFG.get("thermal_on") else "head"


def lupe_tk_new():
    return {"on": False, "v": [0.0, 0.0, 1.0], "R": None, "hi": None, "busy": False, "next": 0.0, "g": None, "sel": None,
            "follow": True, "sharp": True, "msg": "", "msg_t": 0.0, "geo": None, "click": 0.0, "n": 0}


def lupe_tk_follow():
    """the place in the world can be followed in the window: a head and the head camera"""
    return lupe_tk_cam() == "head" and lupe_follow_ok()


def lupe_tk_view(L):
    """the view in the coordinates of the picture now -> ([x, y, s], how far out)"""
    x, y, s = L["v"]
    f = lupe_tk_follow()
    b, out = lupe_shift([x, y, s, s], L["R"] if f else None, servo_pos_deg() if f else None, cam_fov() if f else None)
    return [b[0], b[1], s], out


def lupe_tk_set(L, x, y, s):
    """a new view from the mouse: relative to the head direction of now"""
    s = min(1.0, max(1.0 / LUPE_ZMAX, s))
    L["v"] = [min(1.0 - s, max(0.0, x)), min(1.0 - s, max(0.0, y)), s]
    L["R"] = list(servo_pos_deg()) if lupe_tk_follow() else None


def lupe_tk_render(L, frame, w, h):
    """the picture for the window: the live picture of the view, enlarged, and over it the sharp part where it is -> BGR"""
    fh, fw = frame.shape[:2]
    k = min(w / fw, h / fh)
    ow, oh = max(1, int(fw * k)), max(1, int(fh * k))
    (x, y, s), _out = lupe_tk_view(L)
    x0, y0 = int(x * fw), int(y * fh)
    x1, y1 = max(x0 + 1, int(round((x + s) * fw))), max(y0 + 1, int(round((y + s) * fh)))
    out = cv2.resize(frame[y0:y1, x0:x1], (ow, oh), interpolation=cv2.INTER_LINEAR if s < 1.0 else cv2.INTER_AREA)
    hi = L["hi"]
    if hi is not None and L["sharp"] and s < 0.95 and hi["img"] is not None:
        f = lupe_tk_follow()
        hx, hy = lupe_world_xy(hi["box"], hi["pose"] if f else None, servo_pos_deg() if f else None, cam_fov() if f else None)
        tx, ty = int(round((hx - x) / s * ow)), int(round((hy - y) / s * oh))
        tw, th = max(1, int(round(hi["box"][2] / s * ow))), max(1, int(round(hi["box"][3] / s * oh)))
        if tw * th < 25_000_000:
            part = cv2.resize(hi["img"], (tw, th), interpolation=cv2.INTER_AREA if tw < hi["img"].shape[1] else cv2.INTER_LINEAR)
            a0, b0, a1, b1 = max(0, tx), max(0, ty), min(ow, tx + tw), min(oh, ty + th)
            if a1 > a0 and b1 > b0:
                out = out.copy()
                out[b0:b1, a0:a1] = part[b0 - ty:b1 - ty, a0 - tx:a1 - tx]
    if L["sel"]:
        sx, sy, sw, sh = L["sel"]
        cv2.rectangle(out, (int(sx * ow), int(sy * oh)), (int((sx + sw) * ow), int((sy + sh) * oh)), (77, 211, 255), 2)
    return out


def lupe_tk_fetch(L):
    """one sharp part (in a thread): the same function, bucket and rules as /api/lupe/crop.jpg"""
    try:
        (x, y, s), _out = lupe_tk_view(L)
        f = lupe_tk_follow()
        if not lupe_rate(LUPE_TK_KEY):
            return
        jpg, hd = lupe_crop(lupe_tk_cam(), [x, y, s, s], list(servo_pos_deg()) if f else None, 1600)
        if jpg is None:
            L.update(hi=None, msg=tr_err(hd), msg_t=time.time() + 5)
            return
        img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        box = [float(v) for v in hd["X-Lupe-Box"].split(",")]
        pose = [float(v) for v in hd["X-Lupe-Pose"].split(",")] if hd.get("X-Lupe-Pose") else None
        L["hi"] = {"img": img, "box": box, "pose": pose, "src": hd.get("X-Lupe-Src"), "note": hd.get("X-Lupe-Note") or "",
                   "age": float(hd.get("X-Lupe-Age") or 0)}
    except Exception as e:
        L.update(hi=None, msg=str(e)[:80], msg_t=time.time() + 5)
    finally:
        L["busy"] = False
        L["next"] = time.time() + LUPE_REFRESH_MS / 1000.0


def lupe_tk_status(L):
    """the line under the buttons (the same texts as the web page)"""
    (x, y, s), out = lupe_tk_view(L)
    z = 1.0 / s
    parts = ["×%.1f" % z if z < 9.95 else "×%d" % round(z)]
    hi = L["hi"]
    cam = lupe_tk_cam()
    if z > 1.001:
        if cam == "thermal":
            parts.append(tr("only enlarged - no sharper source"))
        elif not L["sharp"]:
            parts.append(tr("live picture, enlarged"))
        elif hi:
            parts.append(tr({"sensor": "sharp: full camera sensor", "frame": "sharp: full camera picture", "wide": "sharp: full wide-angle picture"}
                            .get(hi["src"], "only enlarged - no sharper source")))
            note = {"alarm": "Sharp picture paused: alarm or person in view", "moving": "Sharp picture paused while the head moves",
                    "eco": "Sharp picture paused: battery saving", "error": "No sharp picture from the camera - the live picture is used"}.get(hi["note"])
            if note:
                parts.append(tr(note))
        if out > 0.5 and lupe_tk_follow():
            parts.append(tr("The area is no longer in the picture"))
    else:
        parts.append(tr("Drag a box over the area or zoom with two fingers (PC: mouse wheel). Double tap = whole picture."))
    if L["msg"] and time.time() < L["msg_t"]:
        parts.append(L["msg"])
    return " · ".join(p for p in parts if p)


def lupe_tk_box_done(L, box, lang=None):
    """a box was drawn (picture coordinates of now): zoom to it, and the head turns it to the middle (when allowed)"""
    s = min(1.0, max(1.0 / LUPE_ZMAX, max(box[2], box[3])))
    lupe_tk_set(L, box[0] + box[2] / 2 - s / 2, box[1] + box[3] / 2 - s / 2, s)
    L["next"] = 0.0
    if L["follow"] and lupe_tk_cam() == "head" and lupe_follow_ok():
        ok, _code, res = lupe_aim(box, "window", lang)
        if ok:
            L["R"] = list(res["from"])
            L["msg"], L["msg_t"] = "🎯 " + tr("The head turns to the area …", lang), time.time() + 4
        else:
            L["msg"], L["msg_t"] = res.get("msg", ""), time.time() + 7
    return L


def lupe_tk_wheel(L, nx, ny, up):
    """the wheel at (nx, ny) of the shown view: zoom in (up) / out, the point under the pointer stays"""
    (x, y, s), _o = lupe_tk_view(L)
    ns = min(1.0, max(1.0 / LUPE_ZMAX, s * (0.8 if up else 1.25)))
    lupe_tk_set(L, x + nx * s - nx * ns, y + ny * s - ny * ns, ns)
    L["next"] = time.time() + 0.25


if GUI_OK:
    def _lupe_tk_xy(self, e):
        """a mouse position on the picture -> 0..1 of the shown view (None outside)"""
        g = self._lupe.get("geo")
        if not g:
            return None
        ox, oy, ow, oh = g
        return min(1.0, max(0.0, (e.x - ox) / ow)), min(1.0, max(0.0, (e.y - oy) / oh))

    def _lupe_tk_down(self, e):
        L = self._lupe
        if not L["on"]:
            return
        p = _lupe_tk_xy(self, e)
        if p is None:
            return "break"
        (x, y, s), _o = lupe_tk_view(L)
        L["g"] = {"k": "pan" if s < 0.999 else "box", "a": p, "last": p, "v0": [x, y, s], "moved": False}
        return "break"

    def _lupe_tk_move(self, e):
        L = self._lupe
        g = L.get("g")
        if not L["on"] or not g:
            return
        p = _lupe_tk_xy(self, e)
        if p is None:
            return "break"
        if abs(p[0] - g["a"][0]) + abs(p[1] - g["a"][1]) > 0.01:
            g["moved"] = True
        if g["k"] == "pan":
            (x, y, s), _o = lupe_tk_view(L)
            lupe_tk_set(L, x - (p[0] - g["last"][0]) * s, y - (p[1] - g["last"][1]) * s, s)
            g["last"] = p
        elif g["moved"]:
            L["sel"] = [min(p[0], g["a"][0]), min(p[1], g["a"][1]), abs(p[0] - g["a"][0]), abs(p[1] - g["a"][1])]
        return "break"

    def _lupe_tk_up(self, e):
        L = self._lupe
        g, L["g"] = L.get("g"), None
        sel, L["sel"] = L.get("sel"), None
        if not L["on"] or not g:
            return
        if g["k"] == "box" and sel and sel[2] > 0.02 and sel[3] > 0.02:
            vx, vy, vs = g["v0"]
            lupe_tk_box_done(L, [vx + sel[0] * vs, vy + sel[1] * vs, sel[2] * vs, sel[3] * vs])
        else:
            L["next"] = time.time() + 0.25
        return "break"

    def _lupe_tk_wheel_ev(self, e):
        L = self._lupe
        if not L["on"]:
            return
        p = _lupe_tk_xy(self, e) or (0.5, 0.5)
        up = getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0
        lupe_tk_wheel(L, p[0], p[1], up)
        return "break"

    def _lupe_tk_dbl(self, e):
        L = self._lupe
        if not L["on"]:
            return self.toggle_video_only()
        if L["v"][2] < 0.999:
            L.update(v=[0.0, 0.0, 1.0], R=None, hi=None)
        else:
            self._lupe_close()
        return "break"

    def _lupe_tk_open(self):
        L = self._lupe
        if L["on"] or self.video is None:
            return
        L.update(on=True, v=[0.0, 0.0, 1.0], R=None, hi=None, sel=None, g=None, msg="")
        vh = self.video.master
        bar = tk.Frame(vh, bg="#0b0f14")
        bk = dict(bg="#1a2433", fg="#ffffff", activebackground="#2f81f7", activeforeground="#ffffff", relief="flat", bd=0, padx=8, pady=4,
                  font=("DejaVu Sans", 10, "bold"), cursor="hand2")

        def tog(key, b):
            L[key] = not L[key]
            b.config(bg="#2f81f7" if L[key] else "#1a2433")
            if key == "sharp":
                L["next"] = 0.0
        tk.Button(bar, text="✕ " + tr("Magnifier"), command=self._lupe_close, **bk).pack(side="left", padx=(0, 4))
        tk.Button(bar, text="1:1", command=lambda: L.update(v=[0.0, 0.0, 1.0], R=None, hi=None), **bk).pack(side="left", padx=(0, 4))
        if lupe_follow_ok():
            bh = tk.Button(bar, text="🎯 " + tr("Head follows"), **bk)
            bh.config(command=lambda: tog("follow", bh), bg="#2f81f7" if L["follow"] else "#1a2433"); bh.pack(side="left", padx=(0, 4))
        bs = tk.Button(bar, text="◐ " + tr("Sharp"), **bk)
        bs.config(command=lambda: tog("sharp", bs), bg="#2f81f7" if L["sharp"] else "#1a2433"); bs.pack(side="left")
        bar.place(x=8, y=8)
        st = tk.Label(vh, text="", bg="#0b0f14", fg="#ffffff", font=("DejaVu Sans", 9), justify="left", anchor="w", padx=6, pady=2)
        st.place(x=8, y=48)
        self._lupe_w = (bar, st)
        v = self.video
        for seq, fn in (("<ButtonPress-1>", self._lupe_down), ("<B1-Motion>", self._lupe_move), ("<ButtonRelease-1>", self._lupe_up),
                        ("<MouseWheel>", self._lupe_wheel), ("<Button-4>", self._lupe_wheel), ("<Button-5>", self._lupe_wheel)):
            v.bind(seq, fn, add="+")
        v.bind("<Double-Button-1>", self._lupe_dbl)               # instead of «full screen» while the magnifier is open
        v.config(cursor="crosshair")
        if getattr(self, "b_lupe", None) is not None:
            self.b_lupe.place_forget()

    def _lupe_tk_close(self):
        L = self._lupe
        L.update(on=False, g=None, sel=None, hi=None)
        for w_ in getattr(self, "_lupe_w", ()) or ():
            try:
                w_.destroy()
            except Exception:
                pass
        self._lupe_w = ()
        v = self.video
        if v is not None:
            try:
                for seq in ("<ButtonPress-1>", "<B1-Motion>", "<MouseWheel>", "<Button-4>", "<Button-5>"):
                    v.unbind(seq)
                v.bind("<Double-Button-1>", lambda e: self.toggle_video_only())
                v.config(cursor="hand2")
                if getattr(self, "b_lupe", None) is not None:
                    self.b_lupe.place(relx=1.0, x=-8, y=8, anchor="ne")
            except Exception:
                pass

    def _lupe_tk_esc(self, e=None):
        if self._lupe["on"]:
            self._lupe_close()
            return "break"

    _lupe_tk_build_left_base = App._build_left

    def _lupe_tk_build_left(self, left):
        if not hasattr(self, "_lupe"):
            self._lupe = lupe_tk_new()
        if self._lupe["on"]:                                     # the live area is built again: start without magnifier
            self._lupe_close()
        self.b_lupe = None
        _lupe_tk_build_left_base(self, left)
        if self.tab == "live" and self.video is not None:
            b = tk.Button(self.video.master, text="🔍 " + tr("Magnifier"), command=self._lupe_open, bg="#1a2433", fg="#ffffff",
                          activebackground="#2f81f7", activeforeground="#ffffff", relief="flat", bd=0, padx=8, pady=4,
                          font=("DejaVu Sans", 10, "bold"), cursor="hand2")
            b.place(relx=1.0, x=-8, y=8, anchor="ne")
            self.b_lupe = b
            try:
                Tip(b, tr("Magnifier: drag a box, zoom with two fingers"))
            except Exception:
                pass
            if not getattr(self, "_lupe_esc", False):
                self._lupe_esc = True
                self.root.bind("<Escape>", self._lupe_esc_ev, add="+")

    _lupe_tk_update_video_base = App._update_video

    def _lupe_tk_update_video(self):
        L = getattr(self, "_lupe", None)
        if not L or not L["on"]:
            return _lupe_tk_update_video_base(self)
        try:
            v = self.video
            frame = None
            if lupe_tk_cam() == "wide" and getattr(self, "_v3_cam", None) is not None:
                frame = _v3_wide_img(self, self._v3_cam)
            if frame is None:
                frame = self.watch.frame_out                      # the shown picture (privacy zones already black, 410)
            if frame is not None and v is not None and v.winfo_exists():
                w = max(160, v.winfo_width()); h = max(90, v.winfo_height())
                out = lupe_tk_render(L, frame, w, h)
                oh, ow = out.shape[:2]
                L["geo"] = ((w - ow) / 2.0, (h - oh) / 2.0, float(ow), float(oh))
                self._v3_pip = None                               # no «tap = swap» on the small picture while the magnifier is open
                if CFG.get("tk_night"):
                    gy = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
                    img = np.zeros((gy.shape[0], gy.shape[1], 3), dtype=np.uint8); img[:, :, 0] = (gy * 0.42).astype(np.uint8)
                else:
                    img = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
                self.photo = ImageTk.PhotoImage(Image.fromarray(img)); v.config(image=self.photo)
                (_x, _y, s), _o = lupe_tk_view(L)
                if (L["sharp"] and s < 0.95 and not L["busy"] and not L.get("g") and time.time() >= L["next"]
                        and lupe_tk_cam() in ("head", "wide")):
                    L["busy"] = True
                    threading.Thread(target=lupe_tk_fetch, args=(L,), daemon=True, name="lupe-tk").start()
                st = (getattr(self, "_lupe_w", None) or (None, None))[1]
                if st is not None:
                    t_ = lupe_tk_status(L)
                    if st.cget("text") != t_:
                        st.config(text=t_, wraplength=max(200, int(w) - 30))
        except Exception as e:
            if time.time() - getattr(self, "_lupe_err_t", 0) > 30:
                self._lupe_err_t = time.time()
                log_event("sys", f"Window magnifier: {str(e)[:120]}")
        finally:
            self.root.after(33, self._update_video)

    for _n, _f in (("_lupe_down", _lupe_tk_down), ("_lupe_move", _lupe_tk_move), ("_lupe_up", _lupe_tk_up), ("_lupe_wheel", _lupe_tk_wheel_ev),
                   ("_lupe_dbl", _lupe_tk_dbl), ("_lupe_open", _lupe_tk_open), ("_lupe_close", _lupe_tk_close), ("_lupe_esc_ev", _lupe_tk_esc)):
        setattr(App, _n, _f)
    # wraps: App._build_left (570): the button «🔍 Lupe» on the live picture
    App._build_left = _lupe_tk_build_left
    # wraps: App._update_video (570 / 578 / 639zv): the view of the magnifier while it is open
    App._update_video = _lupe_tk_update_video


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_LUPE = {
    "Magnifier": ("Lupe", "Loupe", "Lente", "Lupa"),
    "Magnifier: drag a box, zoom with two fingers": ("Lupe: Rahmen ziehen, mit zwei Fingern zoomen", "Loupe : tracer un cadre, zoomer à deux doigts",
                                                     "Lente: traccia un riquadro, zooma con due dita", "Lupa: trair in rom, zoomar cun dus dets"),
    "Close the magnifier (Esc)": ("Lupe schliessen (Esc)", "Fermer la loupe (Échap)", "Chiudere la lente (Esc)", "Serrar la lupa (Esc)"),
    "Whole picture (double tap)": ("Ganzes Bild (Doppeltipp)", "Image entière (double toucher)", "Immagine intera (doppio tocco)", "Entir maletg (tutgar duas giadas)"),
    "Head follows": ("Kopf folgt", "La tête suit", "La testa segue", "Il chau suonda"),
    "The head turns the chosen area to the middle": ("Der Kopf dreht den gewählten Bereich in die Mitte", "La tête amène la zone choisie au centre",
                                                     "La testa porta l’area scelta al centro", "Il chau volva il sectur tschernì en il center"),
    "Sharp": ("Scharf", "Net", "Nitido", "Precis"),
    "Sharp picture from the camera (off: live picture, only enlarged)": (
        "Scharfes Bild von der Kamera (aus: Live-Bild, nur vergrössert)", "Image nette de la caméra (désactivé : image en direct, seulement agrandie)",
        "Immagine nitida dalla telecamera (spento: immagine dal vivo, solo ingrandita)", "Maletg precis da la camera (stizzà: maletg live, mo engrondì)"),
    "Drag a box over the area or zoom with two fingers (PC: mouse wheel). Double tap = whole picture.": (
        "Rahmen über den Bereich ziehen oder mit zwei Fingern zoomen (PC: Mausrad). Doppeltipp = ganzes Bild.",
        "Trace un cadre sur la zone ou zoome à deux doigts (PC : molette). Double toucher = image entière.",
        "Traccia un riquadro sull’area o zooma con due dita (PC: rotella). Doppio tocco = immagine intera.",
        "Trai in rom sur il sectur u zoomescha cun dus dets (PC: rodella da la mieur). Tutgar duas giadas = entir maletg."),
    "One finger moves, two fingers zoom, double tap = whole picture.": (
        "Ein Finger verschiebt, zwei Finger zoomen, Doppeltipp = ganzes Bild.", "Un doigt déplace, deux doigts zooment, double toucher = image entière.",
        "Un dito sposta, due dita zoomano, doppio tocco = immagine intera.", "In det spusta, dus dets zoomeschan, tutgar duas giadas = entir maletg."),
    "only enlarged - no sharper source": ("nur vergrössert – keine schärfere Quelle", "seulement agrandi – pas de source plus nette",
                                          "solo ingrandito – nessuna fonte più nitida", "mo engrondì – nagina funtauna pli precisa"),
    "live picture, enlarged": ("Live-Bild, vergrössert", "image en direct, agrandie", "immagine dal vivo, ingrandita", "maletg live, engrondì"),
    "sharp: full camera sensor": ("scharf: voller Kamera-Sensor", "net : capteur entier de la caméra", "nitido: sensore intero della telecamera",
                                  "precis: entir sensor da la camera"),
    "sharp: full camera picture": ("scharf: volles Kamerabild", "net : image complète de la caméra", "nitido: immagine completa della telecamera",
                                   "precis: entir maletg da la camera"),
    "sharp: full wide-angle picture": ("scharf: volles Weitwinkelbild", "net : image grand angle complète", "nitido: immagine grandangolare completa",
                                       "precis: entir maletg da grond angul"),
    "Sharp picture paused: alarm or person in view": ("Scharfbild pausiert: Alarm oder Person im Bild", "Image nette en pause : alarme ou personne dans l’image",
                                                      "Immagine nitida in pausa: allarme o persona nell’immagine", "Maletg precis en pausa: alarm u persuna en il maletg"),
    "Sharp picture paused while the head moves": ("Scharfbild pausiert, solange der Kopf fährt", "Image nette en pause pendant que la tête bouge",
                                                  "Immagine nitida in pausa mentre la testa si muove", "Maletg precis en pausa durant ch’il chau sa mova"),
    "Sharp picture paused: battery saving": ("Scharfbild pausiert: Akku sparen", "Image nette en pause : économie de batterie",
                                             "Immagine nitida in pausa: risparmio batteria", "Maletg precis en pausa: spargnar l’accu"),
    "No sharp picture from the camera - the live picture is used": ("Kein Scharfbild von der Kamera – das Live-Bild wird genommen",
                                                                    "Pas d’image nette de la caméra – l’image en direct est utilisée",
                                                                    "Nessuna immagine nitida dalla telecamera – si usa l’immagine dal vivo",
                                                                    "Nagin maletg precis da la camera – il maletg live vegn duvrà"),
    "The area is no longer in the picture": ("Der Bereich ist nicht mehr im Bild", "La zone n’est plus dans l’image", "L’area non è più nell’immagine",
                                             "Il sectur n’è betg pli en il maletg"),
    "Turn the head there": ("Kopf dorthin drehen", "Tourner la tête vers là", "Girare la testa lì", "Volver il chau là"),
    "The head turns to the area …": ("Der Kopf dreht zum Bereich …", "La tête tourne vers la zone …", "La testa gira verso l’area …", "Il chau sa volva vers il sectur …"),
    "The head does not follow:": ("Der Kopf folgt nicht:", "La tête ne suit pas :", "La testa non segue:", "Il chau na suonda betg:"),
    "You may zoom but not move the head.": ("Du darfst zoomen, aber den Kopf nicht bewegen.", "Tu peux zoomer, mais pas bouger la tête.",
                                            "Puoi zoomare, ma non muovere la testa.", "Ti dastas zoomar, ma betg mover il chau."),
    "The head follows only in the head view.": ("Der Kopf folgt nur in der Kopf-Ansicht.", "La tête ne suit que dans la vue tête.",
                                                "La testa segue solo nella vista testa.", "Il chau suonda mo en la vista dal chau."),
    "emergency stop or servo fault": ("Not-Aus oder Servo-Störung", "arrêt d’urgence ou panne de servo", "arresto d’emergenza o guasto del servo",
                                      "stop d’urgenza u disturbi dal servo"),
    "protection is off - the camera looks away": ("Schutz ist aus – die Kamera schaut weg", "protection désactivée – la caméra regarde ailleurs",
                                                  "protezione spenta – la telecamera guarda altrove", "la protecziun è stizzada – la camera guarda davent"),
    "MoveEye follows a person or an alarm": ("MoveEye folgt einer Person oder einem Alarm", "MoveEye suit une personne ou une alarme",
                                             "MoveEye segue una persona o un allarme", "MoveEye suonda ina persuna u in alarm"),
    "walk test running": ("Gehtest läuft", "test de marche en cours", "test di camminata in corso", "il test da chaminar curra"),
    "reference scan running": ("Referenz-Scan läuft", "scan de référence en cours", "scansione di riferimento in corso", "il scan da referenza curra"),
    "timelapse position": ("Zeitraffer-Position", "position du timelapse", "posizione del timelapse", "posiziun dal timelapse"),
    "wake-up alarm": ("Wecker", "réveil", "sveglia", "svegliarin"),
    "game round - the players steer": ("Spielrunde – die Spieler steuern", "manche de jeu – les joueurs dirigent", "turno di gioco – i giocatori guidano",
                                       "runda da gieu – ils giugaders dirigan"),
    "a simulator task is running": ("eine Simulator-Aufgabe läuft", "une tâche du simulateur est en cours", "è in corso un compito del simulatore",
                                    "ina incumbensa dal simulatur curra"),
}
for _k, _v in _HX_LUPE.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_LUPE_DE = {_k: _v[0] for _k, _v in _HX_LUPE.items()}
_LUPE_JS_KEYS = ("No connection to MoveEye.", "Too many requests in a short time - wait a few minutes.")


def lupe_live_html():
    de = dict(_LUPE_DE)
    de.update({k: DE.get(k, k) for k in _LUPE_JS_KEYS})
    return ("<style id=\"lupe-css\">" + LUPE_CSS + "</style><script>\ntry { Object.assign(I18N.de, " + json.dumps(de, ensure_ascii=False)
            + "); } catch (e) {}\nif (document.body.dataset.tab === \"live\") { window.LUPE_CFG = {api: \"/api/lupe\", img: \"#video\", tools: \"live\"};\n"
            + LUPE_JS + "}\n</script>")


if 'id="lupe-css"' not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace("</body>", lupe_live_html() + "</body>", 1)

_GUEST_LUPE = "<style>" + LUPE_CSS + "</style><script>/*LUPEG*/</script>"
if "/*LUPEG*/" not in GUEST_PAGE and "\nst();\n" in GUEST_PAGE:
    GUEST_PAGE = GUEST_PAGE.replace("</body>", _GUEST_LUPE + "</body>", 1)


def lupe_guest_js(lang, token):
    L = norm_lang(lang)
    tx = {k: tr(k, L) for k in _HX_LUPE}
    tx.update({k: tr(k, L) for k in _LUPE_JS_KEYS})
    return ("window.LUPE_TX = " + json.dumps(tx, ensure_ascii=False) + ";\nwindow.LUPE_CFG = {api: " + json.dumps("/g/" + token + "/lupe")
            + ", img: \"#v\", tools: \"guest\", guest: true};\n" + LUPE_JS)


# ---- the manual: one point in «Ansichten» (views) ------------------------------------------------------------------------------
HELP_LUPE = {
    "de": '<li id="lupe-help"><b>🔍 Lupe – nur das Live-Bild vergrössern:</b> Knopf mit der Lupe auf dem Bild (im Vollbild oben rechts) oder einfach mit zwei Fingern auf dem Bild zoomen (PC: Strg + Mausrad). In der Lupe: Rahmen ziehen = dieser Bereich gross, ein Finger verschiebt, zwei Finger zoomen, Doppeltipp = ganzes Bild, nochmals = Lupe zu; «✕ Lupe» / Esc. Die Seite selbst zoomt dabei nicht. Der Ausschnitt kommt <b>scharf</b> aus der vollen Auflösung der Kamera (Pi-Kamera: Standbild vom ganzen Sensor, etwa alle 2–3 s; während Alarm, Person im Bild oder Akku sparen nur das volle Kamerabild), Privatsphäre-Zonen bleiben schwarz. Mit dem Recht «Kopf steuern» dreht der Kopf den Bereich in die Mitte («🎯 Kopf folgt»), nicht aber bei Alarm / Folgen, Gehtest, «Aus» oder Not-Aus; der Ausschnitt bleibt dabei auf dem Ort. Wärmebild und andere Kameras: nur vergrössert. Im Fenster am Pi: Knopf «🔍 Lupe» oben rechts auf dem Live-Bild – Rahmen ziehen, Mausrad, Ziehen verschiebt, Doppelklick, Esc.</li>',
    "en": '<li id="lupe-help"><b>🔍 Magnifier – enlarge only the live picture:</b> the magnifier button on the picture (full screen: top right) or simply zoom with two fingers on the picture (PC: Ctrl + mouse wheel). In the magnifier: drag a box = this area big, one finger moves, two fingers zoom, double tap = whole picture, again = close; «✕ Magnifier» / Esc. The page itself does not zoom. The area comes <b>sharp</b> from the full resolution of the camera (Pi camera: a still of the whole sensor, about every 2–3 s; during an alarm, a person in view or battery saving only the full camera frame); privacy zones stay black. With the right «steer the head» the head turns the area to the middle («🎯 Head follows»), but not during an alarm / following, a walk test, «Off» or the emergency stop; the area stays on its place. Thermal picture and other cameras: only enlarged. In the window on the Pi: button «🔍 Magnifier» top right on the live picture – drag a box, mouse wheel, drag moves, double click, Esc.</li>',
    "fr": '<li id="lupe-help"><b>🔍 Loupe – agrandir seulement l’image en direct :</b> bouton loupe sur l’image (plein écran : en haut à droite) ou zoomer à deux doigts sur l’image (PC : Ctrl + molette). Dans la loupe : tracer un cadre = cette zone en grand, un doigt déplace, deux doigts zooment, double toucher = image entière, encore = fermer. La page ne zoome pas. La zone vient <b>nette</b> de la pleine résolution de la caméra ; les zones de confidentialité restent noires. Avec le droit «tête», la tête amène la zone au centre (pas pendant une alarme, un test de marche, «Arrêt» ou l’arrêt d’urgence). Image thermique et autres caméras : seulement agrandies.</li>',
    "it": '<li id="lupe-help"><b>🔍 Lente – ingrandire solo l’immagine dal vivo:</b> pulsante lente sull’immagine (schermo intero: in alto a destra) o zoomare con due dita sull’immagine (PC: Ctrl + rotella). Nella lente: tracciare un riquadro = quest’area grande, un dito sposta, due dita zoomano, doppio tocco = immagine intera, ancora = chiudere. La pagina non zooma. L’area arriva <b>nitida</b> dalla piena risoluzione della telecamera; le zone di privacy restano nere. Con il diritto «testa» la testa porta l’area al centro (non durante un allarme, un test di camminata, «Spento» o l’arresto d’emergenza). Immagine termica e altre telecamere: solo ingrandite.</li>',
    "rm": '<li id="lupe-help"><b>🔍 Lupa – engrondir mo il maletg live:</b> buttun lupa sin il maletg (entir visur: sura a dretga) u zoomar cun dus dets sin il maletg (PC: Ctrl + rodella). En la lupa: trair in rom = quest sectur grond, in det spusta, dus dets zoomeschan, tutgar duas giadas = entir maletg, anc ina giada = serrar. La pagina na zoomescha betg. Il sectur vegn <b>precis</b> da la resoluziun cumplaina da la camera; las zonas da privatezza restan naira. Cun il dretg «chau» volva il chau il sectur en il center (betg durant in alarm, in test da chaminar, «Ora» u il stop d’urgenza). Maletg termic ed autras cameras: mo engrondì.</li>',
}


def _help_lupe(doc, lang):
    i = doc.find('<section id="views"')
    if i < 0 or 'id="lupe-help"' in doc:
        return doc
    j = doc.find("</ul></section>", i)
    return doc[:j] + HELP_LUPE[lang] + doc[j:] if j >= 0 else doc


_hp_en_lupe = HELP_PAGE.find('<div lang="en">')
if _hp_en_lupe > 0:
    HELP_PAGE = _help_lupe(HELP_PAGE[:_hp_en_lupe], "de") + _help_lupe(HELP_PAGE[_hp_en_lupe:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_lupe(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def lupe_selftest():
    assert lupe_box(0.5, 0.5, 0.2, 0.2) == [0.5, 0.5, 0.2, 0.2]
    assert lupe_box(-3, 2, 9, 0.001) == [0.0, 1.0 - LUPE_MIN_BOX, 1.0, LUPE_MIN_BOX]
    assert lupe_box("x", 0, 1, 1) is None and lupe_box(float("nan"), 0, 0.5, 0.5) is None and lupe_box(0, 0, float("inf"), 1) is None
    b, out = lupe_shift([0.4, 0.4, 0.2, 0.2], (10.0, 0.0), (0.0, 0.0), (66.0, 41.0))
    assert abs(b[0] - (0.4 + 10 / 66)) < 1e-9 and out == 0.0, b                  # the head turned left by 10°: the place is further right
    b, out = lupe_shift([0.4, 0.4, 0.2, 0.2], (0.0, 0.0), (0.0, 20.5), (66.0, 41.0))
    assert abs(b[1] - 0.8) < 1e-9 and abs(out - 0.5) < 1e-9, (b, out)                      # head up: the place moves down, half out of the picture
    assert lupe_shift([0.1, 0.1, 0.2, 0.2], None, (5, 5), (66, 41))[0] == [0.1, 0.1, 0.2, 0.2]
    LUPE_RL.pop("selftest", None)
    n = sum(1 for _i in range(int(LUPE_RATE[0]) + 3) if lupe_rate("selftest"))
    assert n == int(LUPE_RATE[0]), n
    LUPE_RL.pop("selftest", None)
    assert "/api/lupe" in PERM_GET["live"] and "/api/lupe" in PERM_POST["head"]
    assert role_allows("view", "/api/lupe/crop.jpg", "GET", {}) and not role_allows("view", "/api/lupe", "POST", {})
    assert role_allows("family", "/api/lupe", "POST", {}) and not role_allows("custom", "/api/lupe/crop.jpg", "GET", {}, set())
    assert 'id="lupe-css"' in WEB_PAGE and "/*LUPEG*/" in GUEST_PAGE and HELP_PAGE.count('id="lupe-help"') == 2
    assert PiCamSource.read is _lupe_pi_read and callable(PiCamSource.lupe_hires) and DemoSource.lupe_gap == LUPE_GAP_CHEAP
    assert not GUI_OK or (App._update_video is _lupe_tk_update_video and App._build_left is _lupe_tk_build_left), "window magnifier"
    for k, v in _HX_LUPE.items():
        assert len(v) == 4 and all(v) and "ß" not in "".join(v), k
    assert tr("Magnifier", "de") == "Lupe" and tr("Head follows", "rm") == "Il chau suonda"
    return "region bounds, world shift, rate, rights, page hooks, camera wrappers, texts"


SELFTEST_EXTRA.append(("Magnifier «🔍 Lupe» in the live picture (639zzzl)", lupe_selftest))
