#@ MoveEye – Teil 411: Nebel-Modus (Kontrast vor der KI anheben, Wärmebild zählt mehr, kein Sabotage-Alarm «Kamera verdreht» im Nebel) und strengere Dämmerung / Wind (Person erst nach 2–3 Treffern in Folge). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Detection test 31.10.2026 (REAL_ERKENNUNG.md, Schattwald, day, fog): nothing recognised, not even «movement» - and in the
# empty fog picture a sabotage push «Kamera verdreht / Bild verändert». Dusk with wind 55 km/h: person pushes without a person.
#
# Fog mode (part of the low-light automatic «lowlight_auto» - both lift the contrast, so no new switch):
#   detect    a bright, grey picture with little contrast: fog_measure() on a small copy (80 x 45) every 0.5 s.
#             Optional: the weather says fog (simulator scene, or Open-Meteo weather code 45 / 48 when «weather_on») ->
#             the limits are a bit wider. On after 10 s, off after 30 s (hysteresis like the low light, 410 _lowlight_decide).
#   then      the picture for the AI and for the movement gets its contrast back (fog_ai_input / fog_gray: stretch the
#             brightness p1..p99 to 0..255, then CLAHE), the thermal persons (232) run by day too and the double
#             confirmation (066) takes the thermal camera alone - the camera sees little in fog.
#   sabotage  TamperGuard (060) gives no «camera turned» while it is foggy (or was in the last 60 s) and «covered» by a
#             flat picture only when nearly every edge is gone (a cloth, not fog). Black = covered stays as before.
#   hint      STATE["fog"] -> the light chip on the page and in the window: «🌫 Nebel – Sicht eingeschränkt».
#
# Stricter at dusk / in wind (strict_gate, called by 410 classify): a track becomes a person only after 2 hits in a row
#   (dusk OR wind) or 3 (dusk AND wind); after 2 hits and 1 s it counts anyway, so a walking person is reported at most
#   about 1 s later. An AI hit counts once per new AI result (the AI keeps its boxes between runs), a movement hit once per
#   picture; one missed picture in between is allowed (a real person in the noise flickers too).
#   dusk      the camera changes from day to night exposure: the smoothed brightness of the low-light mode (410) is in
#             the band lowlight_threshold - gap .. + 2 x gap (45..90 with 60 / 15), or the picture noise is 1.6 x the
#             noise of this camera by day (up to + 3 x gap = 105). Not darker and not in a grey (infrared) night picture -
#             there «nachts strenger» applies.
#   wind      measured: wind meter / simulator (280 StormWatch: 60-s mean >= 20 km/h or gust >= 39 km/h), or the wind seen
#             in the picture is «strong» / «storm» (410).
#   Bound to the existing switch «nachts strenger» (night_strict), no new control.
# ----------------------------------------------------------------------------
FOG = {"on": False, "raw": False, "raw_t": 0.0, "t": 0.0, "hist": deque(maxlen=200), "since": None, "score": None,
       "sat": None, "mean": None, "wx": False, "wx_t": 0.0, "lim_g": None, "lim_l": None, "clahe": None}
TWI = {"on": False, "t": 0.0, "noise": None, "base": None, "last_why": 0.0, "why": ""}
STRICT = {"n": 1, "why": ""}
STATE.setdefault("fog", False); STATE.setdefault("strict", {"n": 1, "why": ""})

# Why these limits (measured on the pictures of the detection test, 80 x 45 grey, rel = (p95 - p5) / mean):
#   fog (Schattwald)  mean 215, rel 0.20-0.23, saturation 9-10; live run E2 (thinner fog): mean 190, rel 0.33, saturation 16
#   snow (Stellplatz) mean 187, rel 0.50, saturation 20      rain (Camping) mean 175, rel 0.64, saturation 37
#   clear day         rel 0.7-1.0, saturation 48-85          dusk / night   mean < 130, rel > 0.9
# 0.40 / 30 lie between fog and snow (first 0.32: the thinner fog of the live run needed 4 min); with fog in the weather
# 0.46 / 40 (still below snow 0.50). mean >= 90: fog by day
# is bright grey; below that it is dusk / night, where the low-light mode lifts the contrast already.
FOG_REL, FOG_SAT, FOG_REL_WX, FOG_SAT_WX, FOG_MEAN = 0.40, 30.0, 0.46, 40.0, 90.0
FOG_ON_S, FOG_OFF_S = 10.0, 30.0          # fog comes and goes in minutes; 10 s: a white van filling the picture (2-5 s) is no fog
TWI_NOISE_K = 1.6                         # noise dusk / day in the test: 1.8-2.2 (three places); rain 0.85, snow 0.6
WIND_MEAN_KMH, WIND_GUST_KMH = 20.0, 39.0  # Beaufort 4 (20-28 km/h): twigs move; Beaufort 6 (39-49 km/h): big branches move


def fog_weather(now=None):
    """the weather says fog: the simulated scene, or Open-Meteo (weather code 45 / 48) for this hour - cached 5 min"""
    now = now or time.time()
    if now - FOG["wx_t"] < 300:
        return FOG["wx"]
    FOG["wx_t"] = now; wx = False
    try:
        if simval_live():
            wx = str((sim_forecast() or {}).get("weather") or "") == "fog"
        elif CFG.get("weather_on"):
            d = datetime.now(); day = weather_day(d.strftime("%Y-%m-%d")) or {}
            row = (day.get("hourly") or {}).get(d.strftime("%H"))
            wx = bool(row) and len(row) > 3 and row[3] in (45, 48)
    except Exception:
        wx = False
    FOG["wx"] = wx
    return wx


def fog_look(small):
    """(fog-like now, rel contrast, saturation, mean) of one picture"""
    s = cv2.resize(small, (80, 45), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY) if s.ndim == 3 else s
    mean = float(g.mean())
    p5, p95 = np.percentile(g, (5, 95))
    rel = float(p95 - p5) / max(1.0, mean)
    sat = float(cv2.cvtColor(s, cv2.COLOR_BGR2HSV)[:, :, 1].mean()) if s.ndim == 3 else 0.0
    wx = fog_weather()
    raw = mean >= FOG_MEAN and rel < (FOG_REL_WX if wx else FOG_REL) and sat < (FOG_SAT_WX if wx else FOG_SAT)
    return raw, rel, sat, mean


def fog_decide(raw, t0, lowlight):
    """hysteresis: on when >= 70 % of the last 10 s looked like fog for FOG_ON_S, off when <= 30 % for FOG_OFF_S"""
    h = FOG["hist"]; h.append((t0, bool(raw)))
    while h and h[0][0] < t0 - 10.0:
        h.popleft()
    if not CFG.get("lowlight_auto", True) or lowlight:
        FOG["since"] = None
        return False
    frac = sum(1 for _, r in h if r) / float(len(h))
    cur = FOG["on"]
    want = frac >= 0.3 if cur else frac >= 0.7
    if want == cur:
        FOG["since"] = None
        return cur
    if FOG["since"] is None:
        FOG["since"] = t0
    if t0 - FOG["since"] >= (FOG_ON_S if want else FOG_OFF_S):
        FOG["since"] = None
        return want
    return cur


def fog_frame(small, t0, lowlight):
    """410: every picture (cheap: the real work every 0.5 s on 80 x 45)"""
    if t0 - FOG["t"] >= 0.5:
        FOG["t"] = t0
        raw, rel, sat, mean = fog_look(small)
        FOG.update(raw=raw, score=round(rel, 3), sat=round(sat, 1), mean=round(mean))
        if raw:
            FOG["raw_t"] = t0
        on = fog_decide(raw, t0, lowlight)
        if on != FOG["on"]:
            FOG["on"] = on; FOG["lim_g"] = FOG["lim_l"] = None
            log_event("auto", f"Fog mode {'ON - contrast lifted, thermal camera counts more, no «camera turned»' if on else 'OFF'}"
                              f" (contrast {rel:.2f}, brightness {mean:.0f}{', weather: fog' if FOG['wx'] else ''})")
    STATE["fog"] = FOG["on"]


def fog_on():
    return bool(FOG["on"])


def fog_tamper_quiet(t0=None):
    """060 TamperGuard: fog now or in the last 60 s (fog lifts and comes back in patches) - the picture loses its edges"""
    return bool(FOG["on"] or (FOG["raw_t"] and (t0 or time.time()) - FOG["raw_t"] < 60.0))


def _fog_lut(img, which):
    """brightness p1..p99 -> 0..255, from a histogram of every picture (~0.1 ms). Every picture: the fog gets thicker and
    thinner all the time - with a fixed curve each small change of the whole picture would be lifted x4 and «move» (test with
    two fog pictures 25 s apart: 27'000 instead of 6'000 moving pixels). The limits follow smoothly (EMA 0.3) so the curve
    does not jump; a person (a few hundred pixels) hardly moves p1 / p99 (1 % = 1'300 pixels at 480 x 270)."""
    hist = cv2.calcHist([img], [0], None, [256], [0, 256]).ravel()
    c = np.cumsum(hist); n = c[-1] or 1.0
    lo = float(np.searchsorted(c, 0.01 * n)); hi = float(np.searchsorted(c, 0.99 * n))
    old = FOG.get("lim_" + which)
    if old is not None:
        lo, hi = old[0] * 0.7 + lo * 0.3, old[1] * 0.7 + hi * 0.3
    FOG["lim_" + which] = (lo, hi)
    span = max(24.0, hi - lo)                              # at most x10: thin fog is not blown up into pure noise
    if FOG["clahe"] is None:
        FOG["clahe"] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))   # 2.0: less than the low light (2.5) - stretched already
    return np.clip((np.arange(256, dtype=np.float32) - lo) * 255.0 / span, 0, 255).astype(np.uint8)


def fog_gray(gray, t0=None):
    """the grey picture for the movement detection in fog (410), else unchanged. Median 5 first like the low light (410):
    fewer specks of lifted noise (test: 4'800 instead of 6'300 moving pixels away from the person, the person stays whole)."""
    if not FOG["on"]:
        FOG["lim_g"] = None
        return gray
    g = cv2.medianBlur(gray, 5)
    lut = _fog_lut(g, "g")
    return FOG["clahe"].apply(cv2.LUT(g, lut))


def fog_ai_input(small, t0=None):
    """the colour picture for the AI in fog: the same on the lightness (LAB L), colours kept, no median (the AI needs the
    details) - ~2 ms at 480 x 270 on a Pi 5"""
    if not FOG["on"] or small is None or small.ndim != 3:
        FOG["lim_l"] = None
        return small
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    l_ = lab[:, :, 0].copy()
    lut = _fog_lut(l_, "l")
    lab[:, :, 0] = FOG["clahe"].apply(cv2.LUT(l_, lut))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


# ---- dusk and wind: stricter --------------------------------------------------
def picture_noise(gray):
    """noise sigma of a grey picture (Immerkær 1996, «Fast noise variance estimation»), on 320 pixels width"""
    h, w = gray.shape[:2]
    g = cv2.resize(gray, (320, max(8, int(h * 320 / max(1, w)))), interpolation=cv2.INTER_AREA).astype(np.float32)
    m = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    s = np.abs(cv2.filter2D(g, -1, m))[1:-1, 1:-1]
    return float(math.sqrt(math.pi / 2.0) / 6.0 * s.mean())


def twilight_decide(smooth, noise, base, mono, dark):
    """(dusk now, why) - smooth = brightness of the low-light mode (median of 10 s), noise / base = now / by day"""
    thr = float(CFG.get("lowlight_threshold", 60)); gap = max(0.0, float(CFG.get("lowlight_gap", 15)))
    if mono:                                    # grey picture: infrared at night (or «grey» picture mode) - no colour test
        return (not dark and thr - gap <= smooth <= thr + 2 * gap), "brightness"
    if thr - gap <= smooth <= thr + 2 * gap:
        return True, "brightness"
    if base and noise is not None and noise >= TWI_NOISE_K * base and thr - gap <= smooth < thr + 3 * gap:   # darker: night rules
        return True, "noise"
    return False, ""


def twilight_frame(w, gray, bright, t0):
    """410: every picture, the work every 0.5 s. gray = the picture before CLAHE."""
    if t0 - TWI["t"] < 0.5:
        return
    TWI["t"] = t0
    thr = float(CFG.get("lowlight_threshold", 60)); gap = max(0.0, float(CFG.get("lowlight_gap", 15)))
    hist = getattr(w, "_ll_hist", None)
    vals = sorted(v for _, v in hist) if hist else []
    smooth = vals[len(vals) // 2] if vals else bright
    nz = picture_noise(gray); TWI["noise"] = round(nz, 2)
    if smooth >= thr + 3 * gap and not FOG["on"]:        # clearly day: learn the noise of this camera (time constant ~50 s)
        TWI["base"] = nz if TWI["base"] is None else TWI["base"] * 0.99 + nz * 0.01
    mono = FOG["sat"] is not None and FOG["sat"] < 4.0
    try:
        dark = bool(is_dark())
    except Exception:
        dark = False
    on, why = twilight_decide(smooth, nz, TWI["base"], mono, dark)
    if on:
        TWI["last_why"] = t0; TWI["why"] = why
    was = TWI["on"]
    TWI["on"] = on or (was and t0 - TWI["last_why"] < 20.0)      # off only after 20 s without a reason (no flapping)
    if TWI["on"] != was:
        log_event("auto", f"Dusk: {'stricter - a person only after hits in a row' if TWI['on'] else 'over'}"
                          f" (brightness {smooth:.0f}, noise {nz:.1f}" + (f" / day {TWI['base']:.1f}" if TWI["base"] else "") + ")")


def wind_strong():
    """measured wind (wind meter / simulator, 280) or the wind seen in the picture (410) is strong"""
    st = STATE.get("storm") or {}
    try:
        if st.get("wind") is not None and float(st["wind"]) >= WIND_MEAN_KMH:
            return True
        if st.get("gust") is not None and float(st["gust"]) >= WIND_GUST_KMH:
            return True
    except (TypeError, ValueError):
        pass
    return STATE.get("wind_level") in ("strong", "storm")


def strict_update():
    """how many hits in a row a new person needs now (1 = as before)"""
    if not CFG.get("night_strict", True) or not CFG.get("detection_on", True):
        n, why = 1, ""
    else:
        d, wd = bool(TWI["on"]), wind_strong()
        n = 1 + int(d) + int(wd)
        why = " + ".join(x for x, on in (("dusk", d), ("wind", wd)) if on)
    STRICT["n"] = n; STRICT["why"] = why
    STATE["strict"] = {"n": n, "why": why}
    return n


def strict_gate(w, t, walking, t0):
    """410 classify: a NEW person only after STRICT["n"] hits in a row (see the top). Returns the new «walking»."""
    n = STRICT["n"]
    sg = getattr(t, "_sg", None)
    if t.is_person or n <= 1:
        t._sg = None
        return walking
    if not walking:
        if sg is not None:
            sg["miss"] += 1
            if sg["miss"] >= 2:                              # two pictures without a hit: start again
                t._sg = None
        return False
    if sg is None:
        sg = t._sg = {"n": 0, "key": None, "t": t0, "miss": 0}
    ai = getattr(w, "ai", None)
    key = (("ai", getattr(ai, "_last_run", 0.0), id(getattr(ai, "boxes", None))) if t.ai_confirmed
           else ("f", STATE.get("frames", 0)))
    if key != sg["key"]:
        sg["key"] = key; sg["n"] += 1; sg["miss"] = 0
    if sg["n"] >= n or (sg["n"] >= 2 and t0 - sg["t"] >= 1.0):
        log_event("person", f"Person #{t.id}: {sg['n']} hits in a row ({STRICT['why']}) - confirmed")
        t._sg = None
        return True
    return False


def fog_twi_frame(w, small, gray, bright, lowlight, t0):
    """410: once per picture, before the contrast boost"""
    try:
        fog_frame(small, t0, lowlight)
        twilight_frame(w, gray, bright, t0)
        strict_update()
    except Exception as e:
        if t0 - FOG.get("err_t", 0.0) > 600:
            FOG["err_t"] = t0; log_event("sys", f"Fog / dusk: {e}"[:160])


# ---- self-test ------------------------------------------------------------------
def fog_selftest():
    rng = np.random.RandomState(7)
    keep = {k: CFG.get(k) for k in ("lowlight_auto", "night_strict", "detection_on", "lowlight_threshold", "lowlight_gap", "tamper_on")}
    fkeep = {k: (v.copy() if isinstance(v, deque) else v) for k, v in FOG.items()}
    tkeep, skeep, stkeep = dict(TWI), dict(STRICT), STATE.get("storm")
    try:
        CFG.update(lowlight_auto=True, night_strict=True, detection_on=True, lowlight_threshold=60, lowlight_gap=15, tamper_on=True)
        FOG.update(wx=False, wx_t=time.time() + 3600)        # no weather in the test
        # a structured day scene: dark trees / bright sky / green meadow
        day = np.zeros((270, 480, 3), np.uint8); day[:] = (60, 140, 70)
        day[:110] = (230, 190, 150)
        for x in range(20, 480, 60):
            cv2.rectangle(day, (x, 60), (x + 18, 230), (30, 50, 40), -1)
        day = cv2.add(day, rng.randint(0, 12, day.shape).astype(np.uint8))
        fog = cv2.addWeighted(day, 0.15, np.full_like(day, 225), 0.85, 0)            # thick fog: grey-white, edges faint
        snow = day.copy(); snow[110:] = (225, 228, 230); snow = cv2.addWeighted(snow, 0.8, np.full_like(snow, 200), 0.2, 0)
        dusk = (day * 0.35).astype(np.uint8)
        assert fog_look(fog)[0], fog_look(fog)
        assert not fog_look(day)[0] and not fog_look(snow)[0] and not fog_look(dusk)[0], (fog_look(day), fog_look(snow), fog_look(dusk))
        # hysteresis: on after ~10 s of fog, not after 5 s; off only after ~30 s without
        FOG.update(on=False, since=None); FOG["hist"].clear(); FOG["t"] = 0.0
        t = 1000.0
        for _ in range(10):                                  # 5 s
            t += 0.5; fog_frame(fog, t, False)
        assert not FOG["on"], "fog after 5 s"
        for _ in range(30):
            t += 0.5; fog_frame(fog, t, False)
        assert FOG["on"] and STATE["fog"], "no fog mode after 20 s of fog"
        g_ai = fog_ai_input(fog, t); g_gr = fog_gray(cv2.cvtColor(fog, cv2.COLOR_BGR2GRAY), t)
        assert g_ai.shape == fog.shape and float(g_gr.std()) > 2.5 * float(cv2.cvtColor(fog, cv2.COLOR_BGR2GRAY).std()), "contrast not lifted"
        for _ in range(20):                                  # 10 s clear: still fog (patchy fog)
            t += 0.5; fog_frame(day, t, False)
        assert FOG["on"], "fog off too early"
        for _ in range(60):
            t += 0.5; fog_frame(day, t, False)
        assert not FOG["on"], "fog mode stays on"
        for _ in range(40):                                  # low light wins: no fog mode in the dark
            t += 0.5; fog_frame(fog, t, True)
        assert not FOG["on"]
        # sabotage: fog rolls in -> no «turned»; a really turned camera without fog -> «turned»
        tg = object.__new__(TamperGuard); fired = []
        tg.alarm = lambda what, looked=None: fired.append(what)
        def tg_reset():
            tg.ref = None; tg.settle = 0.0; tg.t_last = 0.0; tg.pos = (round(CFG["pan"], 1), round(CFG["tilt"], 1)); tg.n_cov = tg.n_mov = 0
        STATE.setdefault("tamper", {"sensor": False, "last": "", "state": "learning"})
        st_keep = {k: STATE.get(k) for k in ("tracking", "patrol_moving", "persons")}
        STATE.update(tracking=False, patrol_moving=False, persons=0)
        try:
            tg_reset(); FOG.update(on=False, raw_t=0.0, since=None); FOG["hist"].clear(); FOG["t"] = 0.0
            t = 2000.0; tg.feed(day, t)
            for i in range(12):                              # the camera sees fog (as in the Schattwald test)
                t += 1.0; fog_frame(fog, t, False); tg.feed(fog, t)
            assert not fired, f"sabotage in fog: {fired}"
            turned = np.ascontiguousarray(day[:, ::-1]); turned = np.roll(turned, 97, axis=1)
            tg_reset(); FOG.update(on=False, raw_t=0.0); FOG["hist"].clear(); t = 3000.0; tg.feed(day, t)
            for i in range(8):
                t += 1.0; fog_frame(turned, t, False); tg.feed(turned, t)
            assert "turned" in fired, f"turned camera not found: {fired}"
            fired.clear(); tg_reset(); FOG.update(on=True, raw_t=t); t += 1.0; tg.feed(day, t)
            for i in range(5):                               # a white cloth in fog (no edges at all): still covered
                t += 1.0; tg.feed(np.full_like(day, 200), t)
            assert "covered" in fired, f"cloth in fog: {fired}"
        finally:
            STATE.update(st_keep)
        # dusk: band of the low-light brightness, noise against the day
        assert twilight_decide(70, 2.0, 2.0, False, False)[0] and twilight_decide(50, 2.0, 2.0, False, False)[0]
        assert not twilight_decide(160, 5.0, 2.0, False, False)[0], "bright day is no dusk"
        assert twilight_decide(100, 4.0, 2.0, False, False) == (True, "noise") and not twilight_decide(100, 2.4, 2.0, False, False)[0]
        assert not twilight_decide(30, 5.0, 2.0, False, False)[0] and not twilight_decide(70, 5.0, 2.0, True, True)[0], "night"
        n0 = picture_noise(cv2.cvtColor(day, cv2.COLOR_BGR2GRAY))
        noisy = cv2.add(dusk, rng.randint(0, 22, dusk.shape).astype(np.uint8))
        assert picture_noise(cv2.cvtColor(noisy, cv2.COLOR_BGR2GRAY)) > 1.6 * n0
        # strict gate: hits in a row
        class _T:
            def __init__(s):
                s.is_person = False; s.ai_confirmed = False; s.id = 1
        class _AI:
            _last_run = 0.0; boxes = []
        class _W:
            ai = _AI()
        w = _W()
        def run(n, seq, ai=False, dt=0.33):
            """seq of True / False per picture -> index of the picture at which the person counts (None = never)"""
            STRICT["n"] = n; tr_ = _T(); tr_.ai_confirmed = ai; t_ = 5000.0
            for i, hit in enumerate(seq):
                t_ += dt; STATE["frames"] = STATE.get("frames", 0) + 1
                if ai:
                    w.ai._last_run = t_; w.ai.boxes = [i]            # a new AI result in every picture
                r = strict_gate(w, tr_, hit, t_)
                tr_.is_person = r
                if r:
                    return i
            return None
        assert run(1, [True]) == 0, "normal: at once"
        assert run(2, [True, True]) == 1 and run(3, [True, True, True]) == 2
        assert run(2, [True, False, True, False, False, True]) == 2, "one miss allowed"
        assert run(3, [True, False, False, True, False, False, True, False, False]) is None, "single flickers never count"
        # the walking person at dusk + wind, 3 pictures/s like the simulator, the AI each time: <= 1 s later
        assert run(3, [True] * 6, ai=True, dt=0.33) == 2
        # Pi 5, 12 pictures/s, the AI only every 0.3 s: the cached AI boxes count once per run
        STRICT["n"] = 3; tr_ = _T(); tr_.ai_confirmed = True; t_ = 6000.0; got = None
        for i in range(40):
            t_ += 1 / 12.0; STATE["frames"] = STATE.get("frames", 0) + 1
            if i % 4 == 0:
                w.ai._last_run = t_; w.ai.boxes = [i]
            if strict_gate(w, tr_, True, t_):
                got = t_ - 6000.0; break
        assert got is not None and 0.5 < got <= 1.1, f"Pi: confirmed after {got} s"
        # reasons: wind from the wind meter / simulator, switch «nachts strenger» off = as before
        TWI["on"] = True; STATE["storm"] = {"wind": 55.0, "gust": 70.0}
        assert strict_update() == 3 and STRICT["why"] == "dusk + wind"
        TWI["on"] = False; STATE["storm"] = {"wind": 5.0, "gust": 10.0}; wl = STATE.get("wind_level"); STATE["wind_level"] = "calm"
        assert strict_update() == 1
        STATE["wind_level"] = wl
        CFG["night_strict"] = False; TWI["on"] = True
        assert strict_update() == 1
        return None
    finally:
        CFG.update(keep)
        for k, v in fkeep.items():
            FOG[k] = v
        TWI.clear(); TWI.update(tkeep); STRICT.clear(); STRICT.update(skeep)
        STATE["storm"] = stkeep; STATE["fog"] = bool(FOG["on"]); STATE["strict"] = dict(STRICT)


SELFTEST_EXTRA.append(("Fog mode (contrast, no «camera turned»), dusk / wind: person after hits in a row (411)", fog_selftest))
