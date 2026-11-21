#@ MoveEye – Teil 639zzzzzg: «🔦 Gäste erwartet» – Führungslicht: Gäste lösen keinen Alarm aus (nur ein leiser Push «Gast kommt»), das weisse Licht blendet weich auf und leuchtet etwa 2 m vor die Füsse in Gehrichtung, bis zum Ziel (Zelt, Feuerstelle, Punkt) und beim Gehen wieder hinaus. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (21.11.2026, freigegeben):
#  Ein / aus   Schalter «Gäste erwartet» (Einstellungen → Schutz → «Gäste erwartet», Web und Pi-Fenster, nur Administrator:
#              USER_SETTINGS_DENY / APPKEY_DENY_KEYS / Bedienermodus), freiwillig «bis HH:MM» (gl_until, danach von selbst aus)
#              und im Zeitplan (Teil 030: SCHED_FEATURES «gl_on» - derselbe Zeitplan wie alles andere).
#  Wer         jede erkannte Person (KI-Person oder Wärmebild), Schalter «auch Tiere» (gl_animals, ab Werk an).
#  Schutz      solange es an ist, lösen Person, Wärmekörper, Vorwarnung (Bewegung) und Abschreckung KEINEN Alarm aus: kein
#              Personen-Push, kein Browser-Alarm, keine Sirene, kein Alarm-Licht, keine Relais auf Person / Wärme / Bewegung /
#              Tier, keine Tier-Pushes (639zz) - nur Protokoll «Gast kommt» und (Schalter gl_push) ein leiser Info-Push, höchstens
#              alle GL_NOTE_S. Sabotage, Diebstahl, Notruf / SOS-Lampe, Alarm von Hand, Geräusch, Sensoren, Temperatur, Akku
#              gehen unverändert (diese Wege werden nicht angefasst). Die Haken stehen in der Hauptdatei (kleine Hüllen, zuerst
#              der Schalter, sonst genau der alte Weg); ohne Zusatz-ZIP gibt es das Führungslicht nicht und es gilt der alte
#              Schutz (GL_ZD["ok"] = False -> gl_active() ist nie wahr).
#  Licht       weisses Licht, weich auf (gl_fade_in_s) und ab (gl_fade_out_s), Helligkeit gl_pct. Mit dem Dimmen in Prozent
#              (MoveEye 4.18.0, light_pct) wirklich gedimmt, sonst ein / aus (an ab der Hälfte der Rampe). Im Simulator
#              lights.white_level = Helligkeit (der Simulator dimmt seinen Scheinwerfer). Nur im Dunkeln (gl_dark_only).
#              SOS-Lampe, Morse, Abschreck-Blitzen und ein Alarm-Licht gehen vor (das Führungslicht schaltet nur dazu ein).
#  Zielen      Bodenpunkt der Person = Richtung (Kopf-Schwenk + Stelle im Bild) + Abstand der Füsse (foot_estimate 232:
#              Kamerahöhe + Neigung; sonst die Grösse 1.7 m, 415). Daraus x / y in m (x rechts, y geradeaus bei Schwenk 50 %),
#              geglättet, Gehrichtung aus den letzten GL_HIST_S s. Ziel des Lichts = Füsse + GL_AHEAD_M in Gehrichtung; dreht
#              die Person um (Richtung gegen die alte länger als GL_FLIP_S), zeigt das Licht sofort auf die andere Seite.
#              Der Kopf fährt dorthin über den Kopf-Koordinator 162 (eigener Beweger «guide» gleich nach «alarm» / «marker»:
#              Hand, Alarm, Sabotage-Blick gehen vor; Runde, Wertsachen-Blick, Parken warten; Folgen 410 pausiert) - wie
#              «Abschrecken mit Ziel» (396) Licht und Kopf gemeinsam.
#  Abwägung    Kamera und Licht sitzen auf demselben Kopf: zielt der Kopf 2 m vor die Person, kann sie aus dem Bild laufen
#              (dann sieht MoveEye nichts mehr). Darum: verfolgt nur die Kopf-Kamera, bleibt die Person sicher im Bild (Rand
#              GL_MARGIN des Bildwinkels, Füsse und Kopf) - das Licht zeigt dann so weit wie möglich nach vorn, bei nahen
#              Personen weniger als 2 m. Sieht die Weitwinkel-Kamera fest am Gerät (nicht am Kopf, cam_on_head) die Person
#              (639zw, Treffer < GL_WIDE_S), darf der Kopf frei zielen: die Richtung kommt dann vom Weitwinkel. Das Wärmebild
#              sitzt beim Gerät mit am Kopf (gleiche Grenze, es macht die Person nur nachts sicherer sichtbar).
#  Ziel        freiwillig: Zelt («Platz einrichten» 317), Feuerstelle (Glut-Wächter 639zzzw), ein Teach-in-Punkt (076, mit
#              Abstand der Markier-Karte 639zzzzm), «wohin der Kopf jetzt schaut» oder ein Punkt im Bild antippen. Gespeichert
#              als Bodenpunkt (gl_target). Erreicht der Gast das Ziel (gl_target_r, ~2 m), blendet das Licht aus; der Kopf
#              schaut aufs Ziel. Geht er später wieder (weiter als Radius + GL_FAREWELL_M), leuchtet es wieder 2 m voraus,
#              bis er aus dem Bild ist.
#  Aus         ohne Ziel (und auf dem Weg zum Ziel): aus dem Bild gl_lost_s (10 s), steht still gl_still_s (30 s), höchstens
#              gl_max_min (5 min). Danach startet am selben Ort erst nach GL_BLOCK_S wieder eine Führung (wer still steht,
#              bekommt nicht gleich wieder Licht).
# Nicht mit echter Hardware getestet: echte Servos / echtes Licht (nur Simulator und Tests ohne Gerät).
# Test: werkzeuge/gaeste_licht_test.py, Simulator: werkzeuge/gaeste_spot_test.gd.
# ----------------------------------------------------------------------------
GL_DEF = {"gl_on": False, "gl_until": "", "gl_until_t": 0.0, "gl_animals": True, "gl_dark_only": True, "gl_push": True, "gl_pct": 60,
          "gl_fade_in_s": 3.0, "gl_fade_out_s": 4.0, "gl_lost_s": 10, "gl_still_s": 30, "gl_max_min": 5, "gl_target_r": 2.0, "gl_target": {}}
for _k, _v in GL_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
    FACTORY_CFG.setdefault(_k, json.loads(json.dumps(_v)))
USER_SETTINGS_DENY.update(GL_DEF)       # only the administrator (never a user with «settings», never an app key, not in operator mode)
APPKEY_DENY_KEYS.update(GL_DEF)
APPKEY_DENY_PATHS.update({"/api/gaeste"})
LOCK_DENY_PATHS.add("/api/gaeste")
LOCK_DENY_KEYS.update(GL_DEF)
SCHED_FEATURES.append(("gl_on", "Guests expected (guide light)"))
SCHED_KEYS.append("gl_on")
GL_KINDS = ("person", "prealarm", "warm")      # what a guest may cause - never tamper, theft, SOS, by hand, noise, sensors
GL_ZD = {"ok": False}                           # True once the program text of the data zip ran (below)
GL_LIGHT = {"drive": False, "pct": 0.0, "was": False}
GL_DIM = "light_pct" in globals()               # 4.18.0: white light dimmed in percent (PCA9685), else on / off


def gl_active(now=None):
    """«Gäste erwartet» is on now (switch / schedule, before the end time) - only with the program text of the data zip"""
    if not (GL_ZD["ok"] and CFG.get("gl_on")):
        return False
    u = CFG.get("gl_until_t") or 0
    return not (isinstance(u, (int, float)) and 0 < u <= (time.time() if now is None else now))


def _gl_call(name, *a):
    """a function of the data zip - never raises, None when it is missing or fails (then everything runs as before)"""
    try:
        f = globals().get(name)
        return f(*a) if f is not None and GL_ZD["ok"] else None
    except Exception:
        return None


def _gl_quiet(kind):
    try:
        if kind in GL_KINDS and gl_active():
            _gl_call("gl_guest_note", kind)
            return True
    except Exception:
        pass
    return False


# ---- the hooks of protection / alarm (main file: the switch first, otherwise exactly the old way) ------------------------------
_gl_push_alert = push_alert


# wraps: push_alert
def push_alert(kind, text="", **extra):                     # + 639zzzzzg: a guest gives no browser alarm, no escalation, no LED
    if _gl_quiet(kind):
        return None
    return _gl_push_alert(kind, text, **extra)


_gl_siren_alarm = siren_alarm


# wraps: siren_alarm
def siren_alarm(kind):                                      # + 639zzzzzg: no siren for a guest (tamper / sensor: as before)
    if _gl_quiet(kind):
        return None
    return _gl_siren_alarm(kind)


_gl_light_alarm = light_alarm


# wraps: light_alarm
def light_alarm():                                          # + 639zzzzzg: no alarm light for a guest (the guide light is gentler)
    if gl_active() and (STATE.get("persons") or STATE.get("warm") or "prealarm" in (STATE.get("present") or [])):
        return None
    return _gl_light_alarm()


_gl_np_person = Notifier.person
_gl_np_prealarm = Notifier.prealarm


def _gl_person(self, count, snapshot_path=None, frame=None):
    if count and _gl_quiet("person"):
        STATE["notify_status"] = "guests expected"
        return None
    return _gl_np_person(self, count, snapshot_path, frame)


def _gl_prealarm(self, frame, event="prealarm"):
    if event in ("prealarm", "warm") and _gl_quiet(event):
        return False
    return _gl_np_prealarm(self, frame, event)


# wraps: Notifier.person
Notifier.person = _gl_person
# wraps: Notifier.prealarm
Notifier.prealarm = _gl_prealarm
_gl_relays_update = RelayManager.update


def _gl_relays(self, present):
    if gl_active():
        present = set(present) - {"person", "warm", "prealarm", "animal"}
    return _gl_relays_update(self, present)


# wraps: RelayManager.update
RelayManager.update = _gl_relays
_gl_deter_check = Deterrence.check


def _gl_deter(self, present, t0):
    if gl_active():
        self.seen.clear()
        return None                                          # no deterrence while guests are expected (person or animal)
    return _gl_deter_check(self, present, t0)


# wraps: Deterrence.check
Deterrence.check = _gl_deter
_gl_crawl_push = crawl_push


# wraps: crawl_push
def crawl_push(notifier, frame, d, ln):                     # + 639zzzzzg: «something big at the ground» is a guest too
    if _gl_quiet("prealarm"):
        return False
    return _gl_crawl_push(notifier, frame, d, ln)


_gl_obj_push = obj_push


# wraps: obj_push
def obj_push(ev, ic, title, text, jpg=None, gap_key=None):  # + 639zzzzzg: animals with names (639zz) - no push while guests come
    if ev == "obj_animal" and gl_active():
        return False
    return _gl_obj_push(ev, ic, title, text, jpg, gap_key)


# ---- the head: own mover «guide» right after «alarm» / «marker» (162); the light; the simulator ---------------------------------
_gl_kp = [p for p in KOPF_PRIO if p != "guide"]
_gl_ki = _gl_kp.index("marker") + 1 if "marker" in _gl_kp else _gl_kp.index("alarm") + 1
KOPF_PRIO = tuple(_gl_kp[:_gl_ki] + ["guide"] + _gl_kp[_gl_ki:])
_gl_kopf_claims = kopf_claims


# wraps: kopf_claims
def kopf_claims():                                           # + 639zzzzzg: the guide light holds the head while it guides
    c = _gl_kopf_claims()
    if _gl_call("gl_holds_head"):
        if "alarm" in c and not (KOPF["alarm"] or KOPF["tamper"] or KOPF["back"]):
            c.discard("alarm")                               # only «following a person» (paused while guiding)
        c.add("guide")
    return c


_gl_kopf_track_blocked = kopf_track_blocked


# wraps: kopf_track_blocked
def kopf_track_blocked():                                    # + 639zzzzzg: 410 does not follow the person - the guide aims ahead of it
    return bool(_gl_call("gl_holds_head")) or _gl_kopf_track_blocked()


_gl_kopf_frame = kopf_frame


# wraps: kopf_frame (410 calls it for every picture)
def kopf_frame(w, candidates, person_boxes, warm_boxes, present, frame, pw, ph, t0):
    r = _gl_kopf_frame(w, candidates, person_boxes, warm_boxes, present, frame, pw, ph, t0)
    _gl_call("gl_frame", w, candidates, person_boxes, warm_boxes, pw, ph, t0)
    return r


_gl_lights_tick = lights_tick


# wraps: lights_tick
def lights_tick():                                           # + 639zzzzzg: the guide light (the way of the SOS lamp 639zzt)
    _gl_call("gl_lights_pre")
    res = _gl_lights_tick()
    _gl_call("gl_lights_post", res)
    return res


if GL_DIM:
    _gl_light_pct = light_pct

    # wraps: light_pct (4.18.0)
    def light_pct(n):                                        # + 639zzzzzg: the guide light fades
        return GL_LIGHT["pct"] if n == "white" and GL_LIGHT["drive"] else _gl_light_pct(n)
_gl_sim_state = sim_state


# wraps: sim_state
def sim_state():                                              # + 639zzzzzg: «guests» - the simulator sends guests to the target
    d = _gl_sim_state()
    d["guests"] = _gl_call("gl_sim_patch", d) or {"on": False}
    return d


# ---- the program text (data zip): the guide itself, the page, the window, the texts, the manual -----------------------------------
GAESTE_PY = r'''
GL_AHEAD_M = 2.0          # m ahead of the feet (Besitzer: «etwa 2 m»)
GL_HIST_S = 1.2           # s of positions for the walking direction
GL_WALK_MS = 0.3          # m/s: slower is no walking direction (standing, the noise of the distance estimate)
GL_FLIP_S = 0.5           # s: walking against the old direction this long = turned back
GL_STILL_M = 0.8          # m: moving less than this counts as standing still
GL_ALPHA = 0.45           # smoothing of the ground position (the foot distance jumps from picture to picture)
GL_GATE_M = 3.5           # m: an observation farther from the guest is somebody else
GL_FAREWELL_M = 1.0       # m beyond the target radius: the guest leaves (hysteresis)
GL_STAY_MAX_S = 4 * 3600  # at the target at most 4 h, then the guide ends (the head is free again)
GL_BLOCK_S = 120.0        # after «stands still» / «max. duration»: no new guide at the same place for 2 min
GL_BLOCK_M = 3.0
GL_MARGIN = 0.12          # part of the field of view kept free at each edge (the person stays in the picture)
GL_HEAD_DPS = 35.0        # °/s the guide turns the head at most
GL_HEAD_DEAD = 0.8        # ° dead zone
GL_WIDE_S = 1.5           # s: a hit of the fixed wide camera counts this long
GL_PERSON_H = 1.7
GL_LOOK_S = 0.25          # the head gets a new aim at most every 0.25 s (the planner 072 drives smoothly)
GL = {"core": None, "aim": None, "look": None, "pan_t": 0.0, "last_end": None, "src": "", "seen": "", "wide": False,
      "lv": 0.0, "lv_t": 0.0, "want": False, "frames": 0, "obs_n": 0, "until_log": 0.0, "targets_t": 0.0}
GL_NOTE_S = 120.0         # «Gast kommt»: log + quiet push at most every 2 min
GL_NOTE = {"t": 0.0, "n": 0, "kind": "", "err_t": 0.0}


def gl_guest_note(kind, force=False):
    """a guest (person / warm body / movement / animal) - no alarm: one log line and one quiet push at most every GL_NOTE_S"""
    now = time.time()
    GL_NOTE["n"] += 1; GL_NOTE["kind"] = kind
    if not force and now - GL_NOTE["t"] < GL_NOTE_S:
        return False
    GL_NOTE["t"] = now
    log_event("person", f"Guests expected: a guest is coming ({kind}) - no alarm")
    if CFG.get("gl_push", True):
        w = WATCH_REF.get("w")
        try:
            if w is not None:
                w.notifier.info("🔦 " + tr("A guest is coming – no alarm (guests expected)."), title="{name}: " + tr("Guest arriving"))
        except Exception as e:
            log_event("sys", f"Guests expected: push {e}"[:160])
    return True


def gl_lights_pre():
    L = STATE.get("lights")
    if isinstance(L, dict) and "gl" in L:                    # the light rules (070) compare with their own last result
        L = dict(L, white=bool(L["gl"])); L.pop("gl", None); STATE["lights"] = L


def gl_lights_post(res):
    """the guide switches the white light on - only when nothing else has it (SOS lamp, Morse, deterrence flashing, pause, an
    alarm light or the own setting «on» go first)"""
    drive, pct = False, 0.0
    try:
        now = time.time()
        frac, top = gl_light_want(now)
        busy = (bool((globals().get("ALM_SOS") or {}).get("on")) or (globals().get("MORSE") or {}).get("tx") is not None
                or now < float(LIGHTS.get("strobe_until", 0.0) or 0.0) or PAUSING["on"])
        if frac > 0.0 and not res.get("white") and not busy and (CFG.get("light_white_out") or CFG.get("sim_on")):
            pct = max(5.0, min(100.0, float(top) * frac))
            drive = frac >= 0.02 if (GL_DIM or CFG.get("sim_on")) else frac >= 0.5
    except Exception:
        drive = False
    if drive:
        res["white"] = True
        STATE["lights"] = dict(STATE.get("lights") or {}, white=True, gl=False)
    if drive != GL_LIGHT["was"]:
        GL_LIGHT["was"] = drive
        log_event("relay", "Guide light " + ("ON" if drive else "OFF"))
    GL_LIGHT.update(drive=drive, pct=round(pct, 1))


def gl_sim_patch(d):
    """sim_state: the brightness of the guide light (white_level) and «guests»"""
    if GL_LIGHT.get("drive") and isinstance(d.get("lights"), dict):
        d["lights"] = dict(d["lights"], white=True, white_level=round(float(GL_LIGHT["pct"]) / 100.0, 3))
    return gl_sim_info()


# ---- geometry (pure: angles in degrees, ground in m - x right, y straight ahead at pan 50 %) -----------------------------------------
def gl_dir_ground(az, pitch, h):
    """direction (azimuth, pitch: + up) from the head at height h -> ground point (x, y), None at / above the horizon"""
    dep = -float(pitch)
    if dep < 1.0:
        return None
    d = float(h) / math.tan(math.radians(dep))
    a = math.radians(float(az))
    return (d * math.sin(a), d * math.cos(a))


def gl_ground_dir(x, y, h):
    """ground point -> (azimuth, pitch, distance)"""
    d = math.hypot(x, y)
    return math.degrees(math.atan2(x, y)), -math.degrees(math.atan2(float(h), max(0.05, d))), d


def gl_angdiff(a, b):
    return (float(a) - float(b) + 180.0) % 360.0 - 180.0


def gl_aim_angles(t, p, h, fov=None, margin=GL_MARGIN, person_h=GL_PERSON_H):
    """where the head (light = camera axis) points to light the ground point t. fov = (h, v) of the camera that tracks the person
    from the same head: then the person at p stays inside the picture (GL_MARGIN at the edges, feet and head) - the light points
    as far ahead as that allows. fov None = a camera that does not move with the head tracks: aim freely. -> (az, pitch)"""
    az, pitch, _d = gl_ground_dir(t[0], t[1], h)
    if fov is None or p is None:
        return az, pitch
    hf, vf = float(fov[0]), float(fov[1])
    azp, _pp, dp = gl_ground_dir(p[0], p[1], h)
    mh = hf * (0.5 - margin)
    off = gl_angdiff(az, azp)
    if abs(off) > mh:
        az = azp + math.copysign(mh, off)
    mv = vf * (0.5 - margin)
    e_feet = -math.degrees(math.atan2(float(h), max(0.05, dp)))
    e_head = math.degrees(math.atan2(float(person_h) - float(h), max(0.05, dp)))
    lo, hi = e_head - mv, e_feet + mv
    pitch = min(max(pitch, lo), hi)
    return (az + 180.0) % 360.0 - 180.0, pitch


class GuideCore:
    """the guide without camera and head (self-test + werkzeuge/gaeste_licht_test.py): observations [(x, y, kind)] in, the phase,
    the aim (ground point) and whether the light is wanted out. Phases: idle -> guide -> (arrived -> farewell ->) idle."""

    def __init__(self):
        self.last_end = None
        self.block = None
        self.reset()

    def reset(self, why=""):
        self.phase = "idle"
        self.t0 = self.phase_t = self.seen_t = self.move_t = 0.0
        self.p = None
        self.hist = deque(maxlen=200)
        self.head = None
        self.flip_t = None
        self.anchor = None
        self.kind = ""
        self.v = (0.0, 0.0)
        self.speed = 0.0

    def _end(self, now, why):
        self.last_end = {"t": now, "why": why, "p": self.p, "kind": self.kind}
        if why in ("still", "max") and self.p is not None:
            self.block = (self.p, now)
        self.reset(why)
        return "end:" + why

    def _pick(self, obs, now):
        if self.p is None:
            free = [o for o in obs if not (self.block and now - self.block[1] < GL_BLOCK_S
                                           and math.hypot(o[0] - self.block[0][0], o[1] - self.block[0][1]) < GL_BLOCK_M)]
            if not free:
                return None
            rank = {"person": 0, "warm": 1, "animal": 2}
            return min(free, key=lambda o: (rank.get(o[2], 3), math.hypot(o[0], o[1])))
        gate = GL_GATE_M + 2.0 * max(0.0, now - self.seen_t)
        best = min(obs, key=lambda o: math.hypot(o[0] - self.p[0], o[1] - self.p[1]), default=None)
        if best is None or math.hypot(best[0] - self.p[0], best[1] - self.p[1]) > gate:
            return None
        return best

    def _update(self, o, now):
        if self.p is None:
            self.p = (float(o[0]), float(o[1]))
            self.anchor = self.p; self.move_t = now
        else:
            a = GL_ALPHA
            self.p = (self.p[0] + a * (o[0] - self.p[0]), self.p[1] + a * (o[1] - self.p[1]))
        self.seen_t = now
        self.hist.append((now, self.p[0], self.p[1]))
        pts = [h for h in self.hist if now - h[0] <= GL_HIST_S]
        self.v, self.speed = (0.0, 0.0), 0.0
        if len(pts) >= 3 and pts[-1][0] - pts[0][0] >= 0.4:
            n = len(pts); mt = sum(p[0] for p in pts) / n
            mx = sum(p[1] for p in pts) / n; my = sum(p[2] for p in pts) / n
            st = sum((p[0] - mt) ** 2 for p in pts) or 1e-9
            vx = sum((p[0] - mt) * (p[1] - mx) for p in pts) / st
            vy = sum((p[0] - mt) * (p[2] - my) for p in pts) / st
            self.v, self.speed = (vx, vy), math.hypot(vx, vy)
        if self.speed >= GL_WALK_MS:
            u = (self.v[0] / self.speed, self.v[1] / self.speed)
            if self.head is None:
                self.head = u; self.flip_t = None
            elif u[0] * self.head[0] + u[1] * self.head[1] < -0.2:
                if self.flip_t is None:
                    self.flip_t = now
                elif now - self.flip_t >= GL_FLIP_S:
                    self.head = u; self.flip_t = None            # turned back: the light goes to the other side at once
            else:
                self.flip_t = None
                hx, hy = 0.7 * self.head[0] + 0.3 * u[0], 0.7 * self.head[1] + 0.3 * u[1]
                n_ = math.hypot(hx, hy) or 1.0
                self.head = (hx / n_, hy / n_)
        if math.hypot(self.p[0] - self.anchor[0], self.p[1] - self.anchor[1]) >= GL_STILL_M:
            self.anchor = self.p; self.move_t = now

    def step(self, now, obs, target=None, r=2.0, lost_s=10.0, still_s=30.0, max_s=300.0):
        """-> list of events ("start", "arrived", "farewell", "back", "end:lost|still|max|gone|stay")"""
        ev = []
        o = self._pick(obs or [], now) if obs else None
        if self.phase == "idle":
            if o is None:
                return ev
            self.reset(); self.kind = o[2]; self._update(o, now)
            self.t0 = self.phase_t = now
            if target is not None and math.hypot(self.p[0] - target[0], self.p[1] - target[1]) <= r:
                self.phase = "arrived"                         # already at the target (the fire): light only when leaving
            else:
                self.phase = "guide"
            return ["start"]
        if o is not None:
            self._update(o, now)
        dt = math.hypot(self.p[0] - target[0], self.p[1] - target[1]) if target is not None else None
        if self.phase == "guide":
            if dt is not None and dt <= r:
                self.phase, self.phase_t = "arrived", now
                return ["arrived"]
            if now - self.seen_t > lost_s:
                return [self._end(now, "lost")]
            if now - self.move_t > still_s:
                return [self._end(now, "still")]
            if now - self.phase_t > max_s:
                return [self._end(now, "max")]
        elif self.phase == "arrived":
            if target is None:
                return [self._end(now, "gone")]
            if dt is not None and dt > r + GL_FAREWELL_M and now - self.seen_t < 1.0:
                self.phase, self.phase_t = "farewell", now
                self.head = None; self.flip_t = None             # the direction comes new: away from the target
                return ["farewell"]
            if now - self.phase_t > GL_STAY_MAX_S:
                return [self._end(now, "stay")]
        elif self.phase == "farewell":
            if dt is not None and dt <= r:
                self.phase, self.phase_t = "arrived", now
                return ["back"]
            if now - self.seen_t > lost_s:
                return [self._end(now, "gone")]
            if now - self.phase_t > max_s:
                return [self._end(now, "max")]
        return ev

    def light_wanted(self):
        return self.phase in ("guide", "farewell")

    def aim(self, target=None):
        """ground point for the light (guide / farewell), the target to watch (arrived), None idle"""
        if self.p is None or self.phase == "idle":
            return None
        if self.phase == "arrived":
            return target or self.p
        if self.head is None:
            return self.p
        return (self.p[0] + GL_AHEAD_M * self.head[0], self.p[1] + GL_AHEAD_M * self.head[1])


GL["core"] = GuideCore()


# ---- the camera: picture -> ground ---------------------------------------------------------------------------------------------------
def gl_sim_head():
    return bool(CFG.get("sim_on")) and str(CFG.get("source") or "").startswith("sim:")


def gl_pitch_off():
    """servo tilt° minus the pitch of camera and light: the simulator's head looks 6° down at tilt 0 (main.gd), a real head 0"""
    return 6.0 if gl_sim_head() else 0.0


def gl_head_deg():
    """(pan°, pitch°) of the head the last picture came from (simulator: its real head, else the planned position)"""
    p, t = servo_pos_deg()
    if gl_sim_head() and isinstance(SIM.get("head"), list) and len(SIM["head"]) >= 2:
        try:
            p, t = float(SIM["head"][0]), float(SIM["head"][1])
        except (TypeError, ValueError):
            pass
    return p, t - gl_pitch_off()


def gl_cam_h():
    try:
        return float(_foot_cam_h())
    except Exception:
        return float(CFG.get("cam_height") or 1.6)


def gl_box_ground(box, kind, ph_px=0, h_px=0):
    """a box (x, y, w, h 0..1 of the head picture) -> ground point (x, y) m, or None (feet cut off and no size)"""
    hf, vf = cam_fov()
    pan, _pitch = gl_head_deg()
    cx = box[0] + box[2] / 2.0
    az = pan + math.degrees(math.atan((cx - 0.5) * 2.0 * math.tan(math.radians(hf) / 2.0)))
    d = None
    try:
        fe = foot_estimate(box)
        d = fe[0] if fe else None
    except Exception:
        d = None
    if d is None and kind in ("person", "warm") and ph_px and h_px:
        d = person_dist_m(float(h_px), float(ph_px))
    if d is None or not math.isfinite(d):
        return None
    d = max(0.5, min(60.0, float(d)))
    a = math.radians(az)
    return (d * math.sin(a), d * math.cos(a))


def gl_wide_hit(now):
    """the fixed wide camera (not on the head) sees a person / animal now -> azimuth°, else None"""
    try:
        sp = CFG.get("kopf_ov")
        if not sp or cam_on_head(sp):
            return None
        hits = [h for h in (globals().get("WK") or {}).get("hits", []) if now - h[0] < GL_WIDE_S and h[1] in ("person", "animal")]
        if not hits:
            return None
        return float(max(hits, key=lambda h: h[0])[4])
    except Exception:
        return None


def gl_obs(w, candidates, person_boxes, warm_boxes, pw, ph):
    """the guests in this picture: [(x, y, kind)]"""
    out = []
    for b in person_boxes or []:
        g = gl_box_ground((b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph), "person", ph, b[3])
        if g:
            out.append((g[0], g[1], "person"))
    for b in warm_boxes or []:
        g = gl_box_ground(tuple(b[:4]), "warm", ph, b[3] * ph)
        if g:
            out.append((g[0], g[1], "warm"))
    if CFG.get("gl_animals", True):
        seen = []
        ai = getattr(w, "ai", None)
        for o in list(getattr(ai, "objects", None) or []):
            try:
                if COCO_LABELS.get(o[5]) in ANIMALS:
                    seen.append(tuple(o[:4]))
            except Exception:
                pass
        for t in candidates or []:
            if getattr(t, "animal_like", False) and not getattr(t, "lost", False):
                seen.append(tuple(t.box))
        for b in seen:
            g = gl_box_ground((b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph), "animal")
            if g:
                out.append((g[0], g[1], "animal"))
    return out


# ---- the switch, the end time, the target ------------------------------------------------------------------------------------------
def gl_until_parse(hm, now=None):
    """«HH:MM» -> the next such moment (epoch), «» -> 0, else None"""
    hm = str(hm or "").strip()
    if not hm:
        return 0.0
    m = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", hm)
    if not m:
        return None
    d = datetime.fromtimestamp(time.time() if now is None else now)
    t = d.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
    if t <= d:
        t += timedelta(days=1)
    return t.timestamp()


def gl_set(on=None, until=None, who="web"):
    """the switch and the end time -> (ok, english message)"""
    if until is not None:
        ts = gl_until_parse(until)
        if ts is None:
            return False, "Time like 23:30"
        CFG["gl_until"] = str(until).strip() if ts else ""
        CFG["gl_until_t"] = ts
    if on is not None:
        CFG["gl_on"] = bool(on)
        try:
            sched_user_changed("gl_on")
        except Exception:
            pass
        if not on:
            CFG["gl_until"] = ""; CFG["gl_until_t"] = 0.0
            GL["core"].reset("off")
        log_event("sys", f"Guests expected {'ON' if on else 'OFF'} ({who})" + (f" until {CFG['gl_until']}" if on and CFG.get("gl_until") else ""))
    save_settings()
    return True, ""


def gl_tick(now):
    """the end time passed: switch off (once), the guide ends. Switched on again (web, window, schedule) with an old end
    time from before: the old end time is dropped, not the switch."""
    u = float(CFG.get("gl_until_t") or 0.0)
    on = bool(CFG.get("gl_on"))
    if on and not GL.get("on_was") and u > 0.0 and now >= u:
        CFG["gl_until"] = ""; CFG["gl_until_t"] = 0.0; u = 0.0
    GL["on_was"] = on
    if on and u > 0.0 and now >= u:
        CFG["gl_on"] = False; CFG["gl_until"] = ""; CFG["gl_until_t"] = 0.0
        GL["core"].reset("until")
        log_event("sys", "Guests expected OFF (end time reached)")
        save_settings()


def gl_target():
    t = CFG.get("gl_target")
    if isinstance(t, dict) and isinstance(t.get("x"), (int, float)) and isinstance(t.get("y"), (int, float)):
        return (float(t["x"]), float(t["y"]))
    return None


def gl_pct_dir(pan, tilt):
    """servo % -> (az°, pitch°)"""
    return (float(pan) - 50.0) / 50.0 * servo_half("pan"), (float(tilt) - 50.0) / 50.0 * servo_half("tilt") - gl_pitch_off()


def gl_targets(lang=None):
    """what the owner can choose: [{id, name, x, y}] (only what can be put on the ground)"""
    h = gl_cam_h()
    out = []
    try:
        pi = place_info()
        tent = pi.get("tent") if pi.get("done") else None
        if tent:
            az, pitch = gl_pct_dir(tent["pan"], float(tent["tilt"]) - float(tent.get("h_tilt") or 0.0) / 2.0)
            g = gl_dir_ground(az, pitch, h)
            if g:
                out.append({"id": "tent", "name": "⛺ " + tr("Tent", lang), "x": round(g[0], 2), "y": round(g[1], 2)})
    except Exception:
        pass
    try:
        s = CFG.get("glut_spot")
        if isinstance(s, dict) and s.get("pan") is not None:
            az, pitch = gl_pct_dir(s["pan"], s["tilt"])
            g = gl_dir_ground(az, pitch, h)
            if g:
                out.append({"id": "fire", "name": "🔥 " + tr("Fire spot", lang), "x": round(g[0], 2), "y": round(g[1], 2)})
    except Exception:
        pass
    dd = CFG.get("mk_dist") or {}
    for i, w in enumerate(WAYPOINTS[:20]):
        try:
            nm = wp_name(w)
            az, pitch = gl_pct_dir(w[0], w[1])
            if nm in dd:
                a = math.radians(az); g = (float(dd[nm]) * math.sin(a), float(dd[nm]) * math.cos(a))
            else:
                g = gl_dir_ground(az, pitch, h)
            if g:
                out.append({"id": "wp%d" % i, "name": "📍 " + nm, "x": round(g[0], 2), "y": round(g[1], 2)})
        except Exception:
            continue
    return out


def gl_set_target(d, lang=None):
    """{kind: none | here | tap (cx, cy) | point (x, y, name) | an id of gl_targets()} -> (ok, english message)"""
    k = str(d.get("kind") or "")
    h = gl_cam_h()
    g, name = None, ""
    if k in ("none", ""):
        CFG["gl_target"] = {}
        save_settings()
        return True, ""
    if k == "here":
        p, t = servo_pos()
        g = gl_dir_ground(*gl_pct_dir(p, t), h); name = tr("Where the head looks", lang)
    elif k == "tap":
        try:
            cx, cy = float(d.get("cx")), float(d.get("cy"))
        except (TypeError, ValueError):
            return False, "cx, cy: numbers 0 … 1"
        if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0):
            return False, "cx, cy: numbers 0 … 1"
        hf, vf = cam_fov()
        pan, pitch = gl_head_deg()
        az = pan + math.degrees(math.atan((cx - 0.5) * 2.0 * math.tan(math.radians(hf) / 2.0)))
        pt = pitch - math.degrees(math.atan((cy - 0.5) * 2.0 * math.tan(math.radians(vf) / 2.0)))
        g = gl_dir_ground(az, pt, h); name = tr("Point in the picture", lang)
    elif k == "point":
        try:
            g = (float(d.get("x")), float(d.get("y")))
        except (TypeError, ValueError):
            return False, "x, y: numbers"
        if not all(math.isfinite(v) and abs(v) <= 200.0 for v in g):
            return False, "x, y: numbers"
        name = str(d.get("name") or tr("Point", lang))[:40]
    else:
        it = next((t for t in gl_targets(lang) if t["id"] == k), None)
        if it is None:
            return False, "unknown target"
        g, name = (it["x"], it["y"]), it["name"]
        k = "tent" if k == "tent" else ("fire" if k == "fire" else "point")
    if g is None:
        return False, "This point is at or above the horizon - aim lower (the ground must be in the picture)."
    if math.hypot(*g) > 80.0:
        return False, "Too far away (more than 80 m)."
    CFG["gl_target"] = {"kind": k if k in ("tent", "fire") else "point", "name": name, "x": round(g[0], 2), "y": round(g[1], 2), "t": time.time()}
    save_settings()
    log_event("sys", f"Guests expected: target «{name}» at {g[0]:.1f} / {g[1]:.1f} m")
    return True, ""


# ---- each picture (410 -> kopf_frame -> here) ------------------------------------------------------------------------------------------
def gl_holds_head():
    c = GL["core"]
    return c.phase != "idle" and gl_active() and bool(CFG.get("kopf_on", True))


def gl_dark_ok():
    if not CFG.get("gl_dark_only", True):
        return True
    try:
        return bool(is_dark())
    except Exception:
        return True


def gl_frame(w, candidates, person_boxes, warm_boxes, pw, ph, t0):
    try:
        _gl_frame(w, candidates, person_boxes, warm_boxes, pw, ph, t0)
    except Exception as e:
        if time.time() - GL_NOTE["err_t"] > 300:
            GL_NOTE["err_t"] = time.time()
            log_event("sys", f"Guide light: {type(e).__name__}: {e}"[:160])


def _gl_frame(w, candidates, person_boxes, warm_boxes, pw, ph, t0):
    now = time.time()
    gl_tick(now)
    c = GL["core"]
    if not gl_active() or not gl_dark_ok():
        if c.phase != "idle":
            c.reset("off")
        gl_phase_watch(now)
        GL.update(aim=None, look=None)
        gl_light_set(False, now)
        return
    GL["frames"] += 1
    obs = gl_obs(w, candidates, person_boxes, warm_boxes, pw, ph)
    wa = gl_wide_hit(now)
    GL["wide"] = wa is not None
    if not obs and wa is not None and c.p is not None:      # the head camera lost the guest, the fixed wide camera sees it
        d = math.hypot(*c.p)
        obs = [(d * math.sin(math.radians(wa)), d * math.cos(math.radians(wa)), c.kind or "person")]
    GL["obs_n"] = len(obs)
    tg = gl_target()
    ev = c.step(now, obs, tg, float(CFG.get("gl_target_r") or 2.0), float(CFG.get("gl_lost_s") or 10.0),
                float(CFG.get("gl_still_s") or 30.0), 60.0 * float(CFG.get("gl_max_min") or 5.0))
    for e in ev:
        gl_event(e, now)
    gl_phase_watch(now)
    gl_light_set(c.light_wanted(), now)
    a = c.aim(tg)
    GL["aim"] = a
    if a is None:
        return
    gl_head_to(a, c.p if c.phase != "arrived" else None, now)


def gl_event(e, now):
    c = GL["core"]
    if e == "start":
        gl_guest_note(c.kind or "person")
        log_event("servo", f"Guide light: guest ({c.kind}) - the light goes ahead" + (" (at the target)" if c.phase == "arrived" else ""))
    elif e == "arrived":
        log_event("servo", "Guide light: the guest reached the target - the light fades out")
    elif e == "farewell":
        log_event("servo", "Guide light: the guest leaves the target - the light guides again")
    elif e == "back":
        log_event("servo", "Guide light: the guest is back at the target")
    elif e.startswith("end:"):
        log_event("servo", "Guide light: ends (" + {"lost": "out of the picture", "still": "stands still", "max": "maximum time",
                                                     "gone": "gone", "stay": "long at the target"}.get(e[4:], e[4:]) + ")")


def gl_phase_watch(now):
    """the guide starts: remember where the head belongs (a «back home» of 162 would hold the rank «alarm» and stop the guide);
    the guide ends: 162 drives the head home kopf_return_s later (as after following)"""
    ph_ = GL["core"].phase
    was = GL.get("phase_was", "idle")
    GL["phase_was"] = ph_
    if was == "idle" and ph_ != "idle":
        bk = KOPF.get("back")
        GL["home"] = tuple(bk["pos"]) if bk and bk.get("pos") else (tuple(KOPF["home"]) if KOPF.get("home") else servo_pos())
        if bk and bk.get("why") != "protection on":
            KOPF["back"] = None
    elif was != "idle" and ph_ == "idle" and GL.get("home"):
        if not KOPF.get("back"):
            KOPF["back"] = {"pos": GL["home"], "since": time.time(), "why": "after the guide light"}
        GL["home"] = None


def gl_head_to(g, person, now):
    """turn the head to the ground point g (light), keeping the person in the picture of the head camera"""
    if now - GL["pan_t"] < GL_LOOK_S:
        return
    GL["pan_t"] = now
    if not CFG.get("kopf_on", True) or not kopf_may("guide") or servo_blocked() or manual_active() or CFG.get("kopf_transport"):
        return
    h = gl_cam_h()
    fov = None if (GL["wide"] or person is None) else cam_fov()
    az, pitch = gl_aim_angles(g, person, h, fov)
    GL["look"] = (round(az, 1), round(pitch, 1))
    p0, t0 = servo_pos_deg()
    want_t = pitch + gl_pitch_off()
    dpan, dtilt = gl_angdiff(az, p0), want_t - t0
    if abs(dpan) < GL_HEAD_DEAD and abs(dtilt) < GL_HEAD_DEAD:
        return
    step = GL_HEAD_DPS * GL_LOOK_S * 2.0
    dpan = max(-step, min(step, dpan)); dtilt = max(-step, min(step, dtilt))
    cp, ct = servo_pos()
    CFG["pan"] = kopf_pan_add(cp, dpan)
    CFG["tilt"] = kopf_tilt_add(ct, dtilt)


# ---- the light level (time based: fades without a picture too) ---------------------------------------------------------------------------
def gl_level(now):
    f = float(CFG.get("gl_fade_in_s") or 3.0) if GL["want"] else float(CFG.get("gl_fade_out_s") or 4.0)
    k = (now - GL["lv_t"]) / max(0.05, f)
    return min(1.0, GL["lv"] + k) if GL["want"] else max(0.0, GL["lv"] - k)


def gl_light_set(want, now):
    want = bool(want) and gl_active() and gl_dark_ok()
    if want != GL["want"]:
        GL["lv"] = gl_level(now); GL["lv_t"] = now; GL["want"] = want


def gl_light_want(now):
    """(fraction 0 … 1 eased, top brightness %) for lights_tick (070, hook in the main file)"""
    c = GL["core"]
    if c.phase != "idle" and now - c.seen_t > float(CFG.get("gl_lost_s") or 10.0) + 2.0 and c.phase in ("guide", "farewell"):
        gl_light_set(False, now)                              # no pictures any more (camera stopped): the light still goes out
    if not gl_active():
        gl_light_set(False, now)
    x = gl_level(now)
    x = x * x * (3.0 - 2.0 * x)                                # smooth start: it does not dazzle
    return x, max(5.0, min(100.0, float(CFG.get("gl_pct") or 60)))


def gl_sim_info():
    tg = CFG.get("gl_target") if gl_target() else None
    c = GL["core"]
    return {"on": gl_active(), "phase": c.phase, "lvl": round(gl_light_want(time.time())[0], 3),
            "target": {"kind": tg.get("kind", "point"), "x": tg["x"], "y": tg["y"]} if tg else None}


def gl_state(lang=None):
    L = norm_lang(lang)
    c = GL["core"]
    tg = CFG.get("gl_target") if gl_target() else None
    le = c.last_end
    return {"on": bool(CFG.get("gl_on")), "active": gl_active(), "until": CFG.get("gl_until") or "", "until_t": float(CFG.get("gl_until_t") or 0.0),
            "phase": c.phase, "kind": c.kind, "level": round(gl_light_want(time.time())[0], 2), "light": GL_LIGHT["drive"], "pct": GL_LIGHT["pct"],
            "dim": bool(GL_DIM), "dark": gl_dark_ok(), "dark_only": bool(CFG.get("gl_dark_only", True)), "wide": GL["wide"],
            "pos": [round(v, 1) for v in c.p] if c.p else None, "aim": [round(v, 1) for v in GL["aim"]] if GL["aim"] else None,
            "target": tg, "targets": gl_targets(L), "last_end": {"why": le["why"], "t": le["t"]} if le else None,
            "notes": GL_NOTE["n"], "light_out": bool(CFG.get("light_white_out")) or bool(CFG.get("sim_on")),
            "sched": "gl_on" in (SCHED.get("base") or {})}


def gl_phase_text(s, lang=None):
    if not s["active"]:
        return tr("off", lang)
    p = {"idle": "waiting for guests", "guide": "guiding a guest", "arrived": "guest at the target - light off",
         "farewell": "guiding the guest out"}.get(s["phase"], s["phase"])
    t = tr(p, lang)
    if s["phase"] == "idle" and s["dark_only"] and not s["dark"]:
        t += " · " + tr("light only in the dark", lang)
    return t


# ---- web: /api/gaeste (administrator only: a new address) ------------------------------------------------------------------------------
_smalltv_routes_gl = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzzzzg
    _smalltv_routes_gl(app, reply, body)
    from flask import request

    @app.route("/api/gaeste", methods=["GET", "POST"])
    def api_gaeste():
        L = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if request.method == "GET":
            s = gl_state(L)
            s["text"] = gl_phase_text(s, L)
            return reply(s)
        d = body()
        L = norm_lang(d.get("lang") or L)
        who = servo_client(request, d)[1]
        a = d.get("action")
        if a == "set":
            ok, msg = gl_set(d.get("on") if "on" in d else None, d.get("until") if "until" in d else None, who)
        elif a == "target":
            ok, msg = gl_set_target(d, L)
        else:
            return reply({"ok": False, "msg": "unknown action"}, 400)
        s = gl_state(L); s["text"] = gl_phase_text(s, L)
        return reply({"ok": ok, "msg": tr(msg, L) if msg else "", "gl": s}, 200 if ok else 409)


# ---- the settings: Einstellungen → Schutz → «Gäste erwartet» (web and window read the same lists) -----------------------------------
GL_SECTION = "Guests expected"
TOGGLES.extend([(GL_SECTION, "gl_on", "Guests expected (guide light)"), (GL_SECTION, "gl_animals", "Animals too"),
                (GL_SECTION, "gl_dark_only", "Light only in the dark"), (GL_SECTION, "gl_push", "Quiet push «guest arriving»")])
SLIDERS.extend([(GL_SECTION, "gl_pct", "Brightness (%)", 5, 100, 5), (GL_SECTION, "gl_fade_in_s", "Fade in (s)", 0.5, 10, 0.5),
                (GL_SECTION, "gl_fade_out_s", "Fade out (s)", 0.5, 15, 0.5), (GL_SECTION, "gl_target_r", "Target reached within (m)", 1, 5, 0.5),
                (GL_SECTION, "gl_lost_s", "Off: out of the picture for (s)", 3, 60, 1), (GL_SECTION, "gl_still_s", "Off: standing still for (s)", 5, 120, 5),
                (GL_SECTION, "gl_max_min", "Off: at most (min)", 1, 30, 1)])
SECTIONS.append(GL_SECTION)
MENU_TITLES.setdefault(GL_SECTION, GL_SECTION)
TK_SUB_ICONS[GL_SECTION] = "🔦"
for _g in TK_GROUPS:
    if _g[0] == "alarm" and GL_SECTION not in _g[2]:
        _g[2].append(GL_SECTION)
SET_HELP.update({
    "gl_on": ("While on, persons, warm bodies and animals raise no alarm - only a quiet push «guest arriving». Sabotage, theft, SOS, "
              "the alarm by hand and the sensors stay as they are. The white light fades in and goes about 2 m ahead of the guest.", "off"),
    "gl_animals": ("The guide light follows animals too (they raise no alarm either way while guests are expected).", "on"),
    "gl_dark_only": ("By day the guide light stays off (the alarms stay quiet all the same).", "on"),
    "gl_push": ("One quiet info push «guest arriving» at most every 2 minutes.", "on"),
    "gl_pct": ("How bright the guide light gets (dimmed from MoveEye 4.18.0, before only on / off).", "60 %"),
    "gl_fade_in_s": ("The light comes up softly - it does not dazzle the guest.", "3 s"),
    "gl_fade_out_s": ("How softly the light goes out.", "4 s"),
    "gl_target_r": ("Within this distance of the target (tent, fire …) the light fades out.", "2 m"),
    "gl_lost_s": ("The guest is not seen for this long: the light goes out.", "10 s"),
    "gl_still_s": ("The guest stands still for this long: the light goes out.", "30 s"),
    "gl_max_min": ("The light goes out after this time at the latest.", "5 min"),
})


GL_CSS = """
#gl-p{margin:4px 0 10px;padding:10px 12px;border-radius:12px;background:rgba(255,214,90,.08);border-left:4px solid #f5c94a}
#gl-p .gl-st{font-weight:700;font-size:15px}
#gl-p .gl-row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px}
#gl-p .gl-row select,#gl-p .gl-row input{flex:1 1 140px;min-width:0}
#gl-p .gl-row button{padding:8px 10px;min-width:0}
#gl-p .gl-pic{position:relative;margin-top:8px;max-width:480px}
#gl-p .gl-pic img{display:block;width:100%;border-radius:8px;cursor:crosshair}
#gl-p .gl-note{margin-top:6px;font-size:12.5px;line-height:1.4}
"""
GL_JS = r"""
// 639zzzzzg «Gäste erwartet»: the panel in Einstellungen → Schutz → «Gäste erwartet» (administrator)
window.glPanel = function (d) {
  if (!d || d.querySelector("#gl-p")) return;
  const P = el("div", ""); P.id = "gl-p";
  const sum = d.querySelector("summary"); if (sum && sum.nextSibling) d.insertBefore(P, sum.nextSibling); else d.appendChild(P);
  const G = {busy: false, key: ""};
  async function act(o) {
    if (G.busy) return; G.busy = true;
    try { const x = await post("/api/gaeste", Object.assign({lang: LANG}, o));
      if (x && x.msg) toast((x.ok ? "✓ " : "⚠ ") + x.msg);
      if (x && x.gl) paint(x.gl, true); }
    catch (e) { toast("⚠ " + t("No connection to MoveEye.")); }
    G.busy = false;
  }
  function paint(s, force) {
    const key = JSON.stringify([s.on, s.active, s.until, s.phase, s.target, s.targets, s.light, s.dark, LANG]);
    if (!force && key === G.key) { const st = P.querySelector(".gl-st"); if (st) st.textContent = "🔦 " + s.text + (s.light ? " · 💡 " + Math.round(s.pct) + " %" : ""); return; }
    G.key = key; P.textContent = "";
    P.appendChild(el("div", "gl-st", "🔦 " + s.text + (s.light ? " · 💡 " + Math.round(s.pct) + " %" : "")));
    if (s.until) P.appendChild(el("div", "mut", t("until") + " " + s.until));
    const r1 = el("div", "gl-row"); const ut = document.createElement("input"); ut.type = "time"; ut.value = s.until || "";
    ut.setAttribute("aria-label", t("until (time, optional)"));
    const b1 = el("button", "sec", "⏱ " + t("Until")); b1.type = "button"; b1.onclick = () => act({action: "set", until: ut.value || ""});
    r1.append(el("span", "", t("until (time, optional)")), ut, b1); P.appendChild(r1);
    const r2 = el("div", "gl-row"); const sel = document.createElement("select"); sel.setAttribute("aria-label", t("Target"));
    const add = (v, n) => { const o = document.createElement("option"); o.value = v; o.textContent = n; sel.appendChild(o); };
    add("none", "– " + t("no target") + " –");
    (s.targets || []).forEach(x => add(x.id, x.name + " · " + Math.round(Math.hypot(x.x, x.y)) + " m"));
    add("here", "🎯 " + t("Where the head looks"));
    if (s.target) { const o = document.createElement("option"); o.value = "cur"; o.textContent = "✓ " + s.target.name + " · " + Math.round(Math.hypot(s.target.x, s.target.y)) + " m"; sel.insertBefore(o, sel.firstChild); sel.value = "cur"; }
    const b2 = el("button", "", t("Set target")); b2.type = "button";
    b2.onclick = () => { if (sel.value !== "cur") act({action: "target", kind: sel.value}); };
    r2.append(el("span", "", t("Target")), sel, b2); P.appendChild(r2);
    const tap = el("button", "sec", "👆 " + t("Tap the target in the picture")); tap.type = "button"; tap.style.marginTop = "8px";
    const pic = el("div", "gl-pic"); pic.hidden = true;
    tap.onclick = () => { pic.hidden = !pic.hidden; if (!pic.hidden) { pic.textContent = ""; const im = document.createElement("img"); im.alt = t("Tap the target in the picture");
      im.src = "/api/frame.jpg?t=" + Date.now(); im.onclick = ev => { const r = im.getBoundingClientRect();
        act({action: "target", kind: "tap", cx: (ev.clientX - r.left) / r.width, cy: (ev.clientY - r.top) / r.height}); pic.hidden = true; }; pic.appendChild(im); } };
    P.append(tap, pic);
    if (!s.light_out) P.appendChild(el("div", "mut gl-note", "⚠ " + t("No white light connected (Settings → Lights) - the alarms stay quiet, but nothing lights.")));
    P.appendChild(el("div", "mut gl-note", "ℹ️ " + t("Persons and animals raise no alarm while this is on. Sabotage, theft, SOS and the alarm by hand stay as they are.")));
  }
  let was = false;
  const tick = async () => { const on = document.body.contains(P);
    if (!on) { if (!was) setTimeout(tick, 500); return; }      // built before it is in the page: wait; removed later: stop
    was = true; let j = null;
    try { j = await (await fetch("/api/gaeste?lang=" + LANG, {cache: "no-store"})).json(); } catch (e) {}
    if (j && j.phase !== undefined) paint(j, false); else if (j && !j.phase) P.hidden = true;
    setTimeout(tick, 2500); };
  tick();
};
"""
GL_JS_KEYS = ("No connection to MoveEye.", "off")
_GL_SEC = 'if (sec.id === "Extra display" && window.stvPanel) stvPanel(d);'
if _GL_SEC in WEB_PAGE and 'window.glPanel) glPanel(d)' not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_GL_SEC, _GL_SEC + '\n    if (sec.id === "Guests expected" && window.glPanel) glPanel(d);   // 639zzzzzg', 1)
_GL_GRP = '{sec: "Camping / protection", title: "Arming and own Wi-Fi", ic: "🏕️"}'
if _GL_GRP in WEB_PAGE and '{sec: "Guests expected"' not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_GL_GRP, _GL_GRP + ', {sec: "Guests expected", title: "Guests expected", ic: "🔦"}', 1)


# ---- the Pi window: the state, the end time and the target in «Gäste erwartet» ----------------------------------------------------------
_gl_tk_build_section_base = App._build_section


def _gl_tk_build_section(self, sec, sbody, settings_parent=None):
    _gl_tk_build_section_base(self, sec, sbody, settings_parent)
    if sec != GL_SECTION:
        return
    try:
        lab = ttk.Label(sbody, text="", wraplength=380, justify="left"); lab.pack(anchor="w", pady=(8, 2))
        r1 = ttk.Frame(sbody); r1.pack(fill="x", pady=(4, 0))
        ttk.Label(r1, text=tr("until (time, optional)")).pack(side="left")
        uv = tk.StringVar(value=CFG.get("gl_until") or "")
        ttk.Entry(r1, textvariable=uv, width=7).pack(side="left", padx=4)
        msg = {"t": 0.0, "txt": ""}

        def until():
            ok, m_ = gl_set(None, uv.get(), tr("Window"))
            msg.update(t=time.time(), txt=("✓ " if ok else "⚠ ") + (tr(m_) if m_ else tr("Until") + " " + (CFG.get("gl_until") or "–")))
        ttk.Button(r1, text="⏱ " + tr("Until"), command=until).pack(side="left")
        r2 = ttk.Frame(sbody); r2.pack(fill="x", pady=(4, 0))
        ttk.Label(r2, text=tr("Target")).pack(side="left")
        opts = [("none", "– " + tr("no target") + " –")] + [(x["id"], x["name"]) for x in gl_targets()] + [("here", "🎯 " + tr("Where the head looks"))]
        cv = tk.StringVar(value=opts[0][1])
        ttk.Combobox(r2, textvariable=cv, values=[o[1] for o in opts], state="readonly", width=24).pack(side="left", padx=4)

        def target():
            k = next((o[0] for o in opts if o[1] == cv.get()), "none")
            ok, m_ = gl_set_target({"kind": k})
            msg.update(t=time.time(), txt=("✓ " if ok else "⚠ ") + (tr(m_) if m_ else tr("Set target")))
        ttk.Button(r2, text=tr("Set target"), command=target).pack(side="left")
        ttk.Label(sbody, text="ℹ️ " + tr("Persons and animals raise no alarm while this is on. Sabotage, theft, SOS and the alarm by hand stay as they are."),
                  style="Mut.TLabel", wraplength=380, justify="left").pack(anchor="w", pady=(6, 0))

        def paint():
            try:
                if not lab.winfo_exists():
                    return
                s = gl_state()
                txt = "🔦 " + gl_phase_text(s) + (" · 💡 %d %%" % round(s["pct"]) if s["light"] else "")
                if s["until"]:
                    txt += " · " + tr("until") + " " + s["until"]
                if s["target"]:
                    txt += "\n" + tr("Target") + ": " + s["target"]["name"]
                if time.time() - msg["t"] < 15:
                    txt += "\n" + msg["txt"]
                lab.config(text=txt)
                lab.after(1500, paint)
            except Exception:
                pass
        paint()
    except Exception as e:
        log_event("sys", f"Window: guests expected: {e}"[:160])


# wraps: App._build_section (570)
App._build_section = _gl_tk_build_section


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------------
_HX_GL = {
    "Guests expected (guide light)": ("Gäste erwartet (Führungslicht)", "Invités attendus (lumière de guidage)", "Ospiti attesi (luce guida)",
                                      "Giasts spetgads (glisch da guidar)"),
    "Guest arriving": ("Gast kommt", "Un invité arrive", "Arriva un ospite", "In giast arriva"),
    "A guest is coming – no alarm (guests expected).": ("Ein Gast kommt – kein Alarm (Gäste erwartet).", "Un invité arrive – pas d’alarme (invités attendus).",
                                                        "Arriva un ospite – nessun allarme (ospiti attesi).", "In giast arriva – nagin alarm (giasts spetgads)."),
    "Guests expected": ("Gäste erwartet", "Invités attendus", "Ospiti attesi", "Giasts spetgads"),
    "Animals too": ("Auch Tiere", "Aussi les animaux", "Anche gli animali", "Er ils animals"),
    "Light only in the dark": ("Licht nur im Dunkeln", "Lumière seulement dans l’obscurité", "Luce solo al buio", "Glisch mo en il stgir"),
    "Quiet push «guest arriving»": ("Leiser Push «Gast kommt»", "Push discret « un invité arrive »", "Push discreto «arriva un ospite»",
                                    "Push quiet «in giast arriva»"),
    "Brightness (%)": ("Helligkeit (%)", "Luminosité (%)", "Luminosità (%)", "Clerezza (%)"),
    "Fade in (s)": ("Aufblenden (s)", "Allumage progressif (s)", "Accensione graduale (s)", "Far pli cler (s)"),
    "Fade out (s)": ("Ausblenden (s)", "Extinction progressive (s)", "Spegnimento graduale (s)", "Far pli stgir (s)"),
    "Target reached within (m)": ("Ziel erreicht innerhalb (m)", "But atteint à moins de (m)", "Meta raggiunta entro (m)", "Destinaziun cuntanschida entaifer (m)"),
    "Off: out of the picture for (s)": ("Aus: nicht mehr im Bild seit (s)", "Éteint : hors de l’image depuis (s)", "Spento: fuori dall’immagine da (s)",
                                        "Ora: betg pli en il maletg dapi (s)"),
    "Off: standing still for (s)": ("Aus: steht still seit (s)", "Éteint : immobile depuis (s)", "Spento: fermo da (s)", "Ora: stat airi dapi (s)"),
    "Off: at most (min)": ("Aus: spätestens nach (min)", "Éteint : au plus tard après (min)", "Spento: al più tardi dopo (min)", "Ora: il pli tard suenter (min)"),
    "waiting for guests": ("wartet auf Gäste", "attend des invités", "in attesa di ospiti", "spetga giasts"),
    "guiding a guest": ("führt einen Gast", "guide un invité", "guida un ospite", "guida in giast"),
    "guest at the target - light off": ("Gast am Ziel – Licht aus", "invité arrivé au but – lumière éteinte", "ospite alla meta – luce spenta",
                                        "giast a la destinaziun – glisch ora"),
    "guiding the guest out": ("führt den Gast hinaus", "raccompagne l’invité", "accompagna fuori l’ospite", "accumpogna il giast ora"),
    "light only in the dark": ("Licht nur im Dunkeln", "lumière seulement dans l’obscurité", "luce solo al buio", "glisch mo en il stgir"),
    "until": ("bis", "jusqu’à", "fino alle", "fin"),
    "Until": ("Bis", "Jusqu’à", "Fino alle", "Fin"),
    "until (time, optional)": ("bis (Uhrzeit, freiwillig)", "jusqu’à (heure, facultatif)", "fino alle (ora, facoltativo)", "fin (ura, facultativ)"),
    "Target": ("Ziel", "But", "Meta", "Destinaziun"),
    "no target": ("kein Ziel", "pas de but", "nessuna meta", "nagina destinaziun"),
    "Set target": ("Ziel setzen", "Définir le but", "Imposta meta", "Fixar la destinaziun"),
    "Where the head looks": ("Wohin der Kopf schaut", "Là où regarde la tête", "Dove guarda la testa", "Nua ch’il chau guarda"),
    "Tap the target in the picture": ("Ziel im Bild antippen", "Touche le but dans l’image", "Tocca la meta nell’immagine", "Tutga la destinaziun en il maletg"),
    "Point in the picture": ("Punkt im Bild", "Point dans l’image", "Punto nell’immagine", "Punct en il maletg"),
    "Point": ("Punkt", "Point", "Punto", "Punct"),
    "Tent": ("Zelt", "Tente", "Tenda", "Tenda"),
    "Time like 23:30": ("Uhrzeit wie 23:30", "Heure comme 23:30", "Ora come 23:30", "Ura sco 23:30"),
    "unknown target": ("unbekanntes Ziel", "but inconnu", "meta sconosciuta", "destinaziun nunenconuschenta"),
    "This point is at or above the horizon - aim lower (the ground must be in the picture).": (
        "Dieser Punkt liegt am oder über dem Horizont – tiefer zielen (der Boden muss im Bild sein).",
        "Ce point est à l’horizon ou au-dessus – vise plus bas (le sol doit être dans l’image).",
        "Questo punto è all’orizzonte o sopra – mira più in basso (il suolo deve essere nell’immagine).",
        "Quest punct è a l’orizont u sur el – mira pli bass (il terren sto esser en il maletg)."),
    "Too far away (more than 80 m).": ("Zu weit weg (mehr als 80 m).", "Trop loin (plus de 80 m).", "Troppo lontano (più di 80 m).",
                                       "Memia lontan (dapli che 80 m)."),
    "cx, cy: numbers 0 … 1": ("cx, cy: Zahlen 0 … 1", "cx, cy : nombres 0 … 1", "cx, cy: numeri 0 … 1", "cx, cy: dumbers 0 … 1"),
    "x, y: numbers": ("x, y: Zahlen", "x, y : nombres", "x, y: numeri", "x, y: dumbers"),
    "No white light connected (Settings → Lights) - the alarms stay quiet, but nothing lights.": (
        "Kein weisses Licht angeschlossen (Einstellungen → Licht) – die Alarme bleiben still, aber nichts leuchtet.",
        "Aucune lumière blanche branchée (Réglages → Lumières) – les alarmes restent muettes, mais rien n’éclaire.",
        "Nessuna luce bianca collegata (Impostazioni → Luci) – gli allarmi restano muti, ma niente illumina.",
        "Nagina glisch alva colliada (Parameters → Glischs) – ils alarms restan quiets, ma nagut na glischa."),
    "Persons and animals raise no alarm while this is on. Sabotage, theft, SOS and the alarm by hand stay as they are.": (
        "Solange das an ist, lösen Personen und Tiere keinen Alarm aus. Sabotage, Diebstahl, SOS und der Alarm von Hand bleiben wie sie sind.",
        "Tant que c’est activé, personnes et animaux ne déclenchent pas d’alarme. Sabotage, vol, SOS et l’alarme manuelle restent inchangés.",
        "Finché è attivo, persone e animali non fanno scattare allarmi. Sabotaggio, furto, SOS e l’allarme manuale restano invariati.",
        "Uschè ditg che quai è activ, na declerian persunas ed animals nagin alarm. Sabotascha, engul, SOS ed l’alarm a maun restan sco ch’els èn."),
    "Fire spot": ("Feuerstelle", "Foyer", "Focolare", "Fieu"),
    "Window": ("Fenster", "Fenêtre", "Finestra", "Fanestra"),
}
for _k, _v in _HX_GL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_GL_HELP_TX = {
    "While on, persons, warm bodies and animals raise no alarm - only a quiet push «guest arriving». Sabotage, theft, SOS, "
    "the alarm by hand and the sensors stay as they are. The white light fades in and goes about 2 m ahead of the guest.": (
        "Solange es an ist, lösen Personen, Wärmekörper und Tiere keinen Alarm aus – nur ein leiser Push «Gast kommt». Sabotage, Diebstahl, SOS, "
        "der Alarm von Hand und die Sensoren bleiben wie sie sind. Das weisse Licht blendet weich auf und leuchtet etwa 2 m vor den Gast.",
        "Tant que c’est activé, personnes, corps chauds et animaux ne déclenchent pas d’alarme – seulement un push discret « un invité arrive ». "
        "Sabotage, vol, SOS, l’alarme manuelle et les capteurs restent inchangés. La lumière blanche s’allume doucement et éclaire environ 2 m devant l’invité.",
        "Finché è attivo, persone, corpi caldi e animali non fanno scattare allarmi – solo un push discreto «arriva un ospite». Sabotaggio, furto, SOS, "
        "l’allarme manuale e i sensori restano invariati. La luce bianca si accende piano e illumina circa 2 m davanti all’ospite.",
        "Uschè ditg ch’i è activ, na declerian persunas, corps chauds ed animals nagin alarm – mo in push quiet «in giast arriva». Sabotascha, engul, SOS, "
        "l’alarm a maun ed ils sensurs restan sco ch’els èn. La glisch alva vegn plaunsieu pli clera e glischa var 2 m avant il giast."),
    "The guide light follows animals too (they raise no alarm either way while guests are expected).": (
        "Das Führungslicht folgt auch Tieren (einen Alarm lösen sie so oder so nicht aus, solange Gäste erwartet werden).",
        "La lumière de guidage suit aussi les animaux (de toute façon, ils ne déclenchent pas d’alarme tant que des invités sont attendus).",
        "La luce guida segue anche gli animali (in ogni caso non fanno scattare allarmi finché si attendono ospiti).",
        "La glisch da guidar suonda er ils animals (in alarm na declerian els tuttina betg, uschè ditg che giasts vegnan spetgads)."),
    "By day the guide light stays off (the alarms stay quiet all the same).": (
        "Am Tag bleibt das Führungslicht aus (die Alarme bleiben trotzdem still).", "De jour, la lumière de guidage reste éteinte (les alarmes restent muettes quand même).",
        "Di giorno la luce guida resta spenta (gli allarmi restano comunque muti).", "Di resta la glisch da guidar ora (ils alarms restan tuttina quiets)."),
    "One quiet info push «guest arriving» at most every 2 minutes.": (
        "Ein leiser Info-Push «Gast kommt» höchstens alle 2 Minuten.", "Un push d’info discret « un invité arrive » au plus toutes les 2 minutes.",
        "Un push informativo discreto «arriva un ospite» al massimo ogni 2 minuti.", "In push d’infurmaziun quiet «in giast arriva» il pli savens mintga 2 minutas."),
    "How bright the guide light gets (dimmed from MoveEye 4.18.0, before only on / off).": (
        "Wie hell das Führungslicht wird (ab MoveEye 4.18.0 gedimmt, vorher nur ein / aus).",
        "Intensité de la lumière de guidage (atténuée dès MoveEye 4.18.0, avant seulement allumée / éteinte).",
        "Quanto diventa luminosa la luce guida (attenuata da MoveEye 4.18.0, prima solo accesa / spenta).",
        "Co clera che la glisch da guidar daventa (sfiarada a partir da MoveEye 4.18.0, avant mo en / ora)."),
    "The light comes up softly - it does not dazzle the guest.": (
        "Das Licht kommt weich – es blendet den Gast nicht.", "La lumière arrive doucement – elle n’éblouit pas l’invité.",
        "La luce arriva piano – non abbaglia l’ospite.", "La glisch vegn plaunsieu – ella na sblendegia betg il giast."),
    "How softly the light goes out.": ("Wie weich das Licht ausgeht.", "Avec quelle douceur la lumière s’éteint.", "Quanto piano si spegne la luce.",
                                       "Co plaunsieu che la glisch va ora."),
    "Within this distance of the target (tent, fire …) the light fades out.": (
        "Innerhalb dieser Entfernung vom Ziel (Zelt, Feuer …) blendet das Licht aus.", "À moins de cette distance du but (tente, feu …), la lumière s’éteint doucement.",
        "Entro questa distanza dalla meta (tenda, fuoco …) la luce si spegne piano.", "Entaifer questa distanza da la destinaziun (tenda, fieu …) va la glisch plaunsieu ora."),
    "The guest is not seen for this long: the light goes out.": (
        "Der Gast ist so lange nicht mehr zu sehen: das Licht geht aus.", "L’invité n’est plus vu pendant ce temps : la lumière s’éteint.",
        "L’ospite non si vede per questo tempo: la luce si spegne.", "Il giast na vegn betg vis uschè ditg: la glisch va ora."),
    "The guest stands still for this long: the light goes out.": (
        "Der Gast steht so lange still: das Licht geht aus.", "L’invité reste immobile pendant ce temps : la lumière s’éteint.",
        "L’ospite resta fermo per questo tempo: la luce si spegne.", "Il giast stat uschè ditg airi: la glisch va ora."),
    "The light goes out after this time at the latest.": (
        "Das Licht geht spätestens nach dieser Zeit aus.", "La lumière s’éteint au plus tard après ce temps.",
        "La luce si spegne al più tardi dopo questo tempo.", "La glisch va ora il pli tard suenter quest temp."),
}
for _k, _v in _GL_HELP_TX.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def gl_page_hooks(page):
    if 'id="gl-css"' not in page:
        de = {k: v[0] for k, v in _HX_GL.items()}
        de.update({k: v[0] for k, v in _GL_HELP_TX.items()})
        de.update({k: DE.get(k, k) for k in GL_JS_KEYS + ("Guests expected (guide light)",) if DE.get(k)})
        page = page.replace("</body>", "<style id=\"gl-css\">" + GL_CSS + "</style><script>\ntry { Object.assign(I18N.de, "
                            + json.dumps(de, ensure_ascii=False) + "); } catch (e) {}\n" + GL_JS + "</script></body>", 1)
    return page


WEB_PAGE = gl_page_hooks(WEB_PAGE)

# ---- the manual: one paragraph at the end of «Alarm & Camping» --------------------------------------------------------------------------
HELP_GL = {
    "de": '<p id="gl-help"><b>🔦 Gäste erwartet (Einstellungen → Schutz → «Gäste erwartet», nur Administrator; auch im Pi-Fenster und im Zeitplan):</b> Kommen Gäste, schalte «Gäste erwartet» ein – auf Wunsch «bis 23:30». Solange es an ist, lösen Personen, Wärmekörper, Bewegung und Tiere keinen Alarm aus (keine Sirene, kein Alarm-Licht, keine Abschreckung, keine Personen-Pushes) – nur ein Eintrag im Protokoll und ein leiser Push «Gast kommt». Sabotage, Diebstahl, SOS, der Alarm von Hand und die Sensoren bleiben wie sie sind. Im Dunkeln blendet das weisse Licht weich auf und leuchtet etwa 2 m vor die Füsse des Gastes in Gehrichtung, auch wenn er umdreht. Mit einem Ziel (Zelt aus «Platz einrichten», Feuerstelle des Glut-Wächters, ein Teach-in-Punkt, «wohin der Kopf schaut» oder ein Punkt im Bild) blendet es am Ziel aus (ab Werk 2 m) und begleitet den Gast später wieder hinaus. Ohne Ziel geht es aus, wenn der Gast 10 s nicht mehr zu sehen ist, 30 s still steht oder nach 5 min. Helligkeit, Auf- und Ausblenden und die drei Zeiten sind einstellbar; gedimmt ab MoveEye 4.18.0, vorher nur ein / aus. <b>Abwägung:</b> Kamera und Licht sitzen auf demselben Kopf. Damit MoveEye den Gast nicht verliert, bleibt er im Bild – bei nahen Gästen zeigt das Licht darum etwas weniger weit voraus. Sieht eine fest montierte Weitwinkel-Kamera den Gast, zielt der Kopf frei. Mit echtem Licht und echten Servos noch nicht getestet (nur Simulator).</p>',
    "en": '<p id="gl-help"><b>🔦 Guests expected (Settings → Protection → «Guests expected», administrator only; also in the Pi window and in the schedule):</b> when guests come, switch on «Guests expected» – optionally «until 23:30». While it is on, persons, warm bodies, movement and animals raise no alarm (no siren, no alarm light, no deterrence, no person pushes) – only a line in the log and a quiet push «guest arriving». Sabotage, theft, SOS, the alarm by hand and the sensors stay as they are. In the dark the white light fades in softly and lights about 2 m ahead of the guest’s feet in the walking direction, also when they turn back. With a target (the tent of «Set up the place», the fire spot of the fire watch, a taught point, «where the head looks» or a point in the picture) it fades out at the target (2 m from the factory) and later guides the guest out again. Without a target it goes out when the guest is not seen for 10 s, stands still for 30 s or after 5 min. Brightness, fading and the three times can be set; dimmed from MoveEye 4.18.0, before only on / off. <b>Trade-off:</b> camera and light sit on the same head. So that MoveEye does not lose the guest, the guest stays in the picture – for near guests the light therefore points a little less far ahead. When a fixed wide-angle camera sees the guest, the head aims freely. Not yet tested with a real light and real servos (simulator only).</p>',
    "fr": '<p id="gl-help"><b>🔦 Invités attendus (Réglages → Protection → « Invités attendus », administrateur seulement ; aussi dans la fenêtre du Pi et dans le programme horaire) :</b> quand des invités arrivent, active « Invités attendus » – si tu veux « jusqu’à 23:30 ». Tant que c’est activé, personnes, corps chauds, mouvements et animaux ne déclenchent pas d’alarme (pas de sirène, pas de lumière d’alarme, pas de dissuasion, pas de push personne) – seulement une ligne dans le journal et un push discret « un invité arrive ». Sabotage, vol, SOS, l’alarme manuelle et les capteurs restent inchangés. Dans l’obscurité, la lumière blanche s’allume doucement et éclaire environ 2 m devant les pieds de l’invité dans le sens de la marche, même s’il fait demi-tour. Avec un but (la tente de « Configurer l’emplacement », le foyer du gardien des braises, un point appris, « là où regarde la tête » ou un point dans l’image), elle s’éteint au but (2 m d’usine) et raccompagne plus tard l’invité. Sans but, elle s’éteint si l’invité n’est plus vu pendant 10 s, reste immobile 30 s ou après 5 min. Luminosité, allumage / extinction et les trois durées sont réglables ; atténuée dès MoveEye 4.18.0, avant seulement allumée / éteinte. <b>Compromis :</b> caméra et lumière sont sur la même tête ; pour ne pas perdre l’invité, il reste dans l’image – pour un invité proche, la lumière éclaire donc un peu moins loin devant. Si une caméra grand angle fixe voit l’invité, la tête vise librement. Pas encore testé avec une vraie lumière et de vrais servos (seulement le simulateur).</p>',
    "it": '<p id="gl-help"><b>🔦 Ospiti attesi (Impostazioni → Protezione → «Ospiti attesi», solo amministratore; anche nella finestra del Pi e nella programmazione):</b> quando arrivano ospiti, attiva «Ospiti attesi» – se vuoi «fino alle 23:30». Finché è attivo, persone, corpi caldi, movimenti e animali non fanno scattare allarmi (niente sirena, niente luce d’allarme, niente dissuasione, niente push persone) – solo una riga nel registro e un push discreto «arriva un ospite». Sabotaggio, furto, SOS, l’allarme manuale e i sensori restano invariati. Al buio la luce bianca si accende piano e illumina circa 2 m davanti ai piedi dell’ospite nella direzione di marcia, anche quando torna indietro. Con una meta (la tenda di «Configura il posto», il focolare del guardiano delle braci, un punto appreso, «dove guarda la testa» o un punto nell’immagine) si spegne alla meta (2 m di fabbrica) e più tardi accompagna di nuovo fuori l’ospite. Senza meta si spegne se l’ospite non si vede per 10 s, resta fermo 30 s o dopo 5 min. Luminosità, accensione / spegnimento graduale e i tre tempi sono regolabili; attenuata da MoveEye 4.18.0, prima solo accesa / spenta. <b>Compromesso:</b> telecamera e luce stanno sulla stessa testa; per non perdere l’ospite, questo resta nell’immagine – per ospiti vicini la luce illumina quindi un po’ meno avanti. Se una telecamera grandangolare fissa vede l’ospite, la testa mira liberamente. Non ancora provato con una luce vera e servo veri (solo simulatore).</p>',
    "rm": '<p id="gl-help"><b>🔦 Giasts spetgads (Parameters → Protecziun → «Giasts spetgads», mo administratur; er en la fanestra dal Pi ed en il plan da temp):</b> sche giasts vegnan, activescha «Giasts spetgads» – sche ti vuls «fin las 23:30». Uschè ditg ch’i è activ, na declerian persunas, corps chauds, moviments ed animals nagin alarm (nagina sirena, nagina glisch d’alarm, nagina deterrenza, nagins push da persunas) – mo ina lingia en il protocol ed in push quiet «in giast arriva». Sabotascha, engul, SOS, l’alarm a maun ed ils sensurs restan sco ch’els èn. En il stgir vegn la glisch alva plaunsieu pli clera e glischa var 2 m avant ils pes dal giast en la direcziun da chaminar, er sch’el returna. Cun ina destinaziun (la tenda da «Endrizzar la plazza», il fieu dal guardian da la brasa, in punct emprendì, «nua ch’il chau guarda» u in punct en il maletg) va ella ora a la destinaziun (2 m da fabrica) e accumpogna il giast pli tard puspè ora. Senza destinaziun va ella ora, sch’il giast na vegn betg vis 10 s, stat airi 30 s u suenter 5 min. Clerezza, far pli cler / pli stgir ed ils trais temps èn reglabels; sfiarada a partir da MoveEye 4.18.0, avant mo en / ora. <b>Cumpromiss:</b> camera e glisch sesan sin il medem chau; per che MoveEye na perda betg il giast, resta el en il maletg – per giasts damanaivel glischa la glisch perquai in pau main lunsch ordavant. Sche ina camera da grond angul fixa vesa il giast, mira il chau liberamain. Anc betg testà cun glisch vaira e servos vairs (mo simulatur).</p>',
}


def _help_gl(doc, lang):
    i = doc.find('<section id="alarm"')
    if i < 0 or 'id="gl-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_GL[lang] + doc[j:] if j >= 0 else doc


_hp_en_gl = HELP_PAGE.find('<div lang="en">')
if _hp_en_gl > 0:
    HELP_PAGE = _help_gl(HELP_PAGE[:_hp_en_gl], "de") + _help_gl(HELP_PAGE[_hp_en_gl:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_gl(HELP_X[_L], _L)


# ---- self-test -----------------------------------------------------------------------------------------------------------------------------
def gl_selftest():
    h = 1.6
    t = gl_aim_angles((0.0, 10.0), None, h)
    assert abs(t[0]) < 1e-6 and abs(t[1] + math.degrees(math.atan2(1.6, 10.0))) < 1e-6, t
    g = gl_dir_ground(30.0, -10.0, h)
    az, pitch, d = gl_ground_dir(g[0], g[1], h)
    assert abs(az - 30.0) < 1e-6 and abs(pitch + 10.0) < 1e-6, (az, pitch)
    assert gl_dir_ground(0.0, 0.5, h) is None, "at the horizon: no ground point"
    c = GuideCore()
    for i in range(30):                                       # walks to the right at 1 m/s, 8 m away
        c.step(100.0 + i * 0.1, [(-3.0 + i * 0.1, 8.0, "person")])
    a = c.aim()
    assert c.phase == "guide" and a[0] > c.p[0] + 1.8 and abs(a[1] - c.p[1]) < 0.4, (c.p, a)
    for i in range(30):                                       # turns back
        c.step(103.0 + i * 0.1, [(-0.1 - i * 0.1, 8.0, "person")])
    a = c.aim()
    assert a[0] < c.p[0] - 1.5, ("turned back: the light is on the other side", c.p, a)
    c2 = GuideCore()
    ev = []
    for i in range(80):
        ev += c2.step(200.0 + i * 0.1, [(0.0, 10.0 - i * 0.1, "person")], target=(0.0, 3.0), r=2.0)
    assert "arrived" in ev and c2.phase == "arrived" and not c2.light_wanted(), ev
    for i in range(40):
        ev += c2.step(208.0 + i * 0.1, [(i * 0.12, 3.0 + i * 0.12, "person")], target=(0.0, 3.0), r=2.0)
    assert "farewell" in ev and c2.light_wanted(), ev
    c3 = GuideCore(); c3.step(300.0, [(1.0, 5.0, "person")])
    assert c3.step(311.0, [], lost_s=10.0) == ["end:lost"]
    assert "guide" in KOPF_PRIO and KOPF_PRIO.index("guide") > KOPF_PRIO.index("alarm"), KOPF_PRIO
    assert ("gl_on", "Guests expected (guide light)") in SCHED_FEATURES and "gl_on" in USER_SETTINGS_DENY
    assert 'id="gl-css"' in WEB_PAGE and "glPanel(d)" in WEB_PAGE and HELP_PAGE.count('id="gl-help"') == 2
    for k, v in list(_HX_GL.items()) + list(_GL_HELP_TX.items()):
        assert len(v) == 4 and all(v) and "ß" not in "".join(v), k
    assert gl_until_parse("7:5") is None and gl_until_parse("") == 0.0 and gl_until_parse("23:30") > time.time()
    return "ground point, 2 m ahead, turn back, target -> off -> farewell, lost, head rank, schedule, page, texts"


SELFTEST_EXTRA.append(("Guests expected «🔦 guide light» (639zzzzzg)", gl_selftest))
GL_ZD["ok"] = True
'''
zd_exec(GAESTE_PY, '639zzzzzg_gaeste_licht.py')
