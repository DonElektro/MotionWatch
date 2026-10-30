#@ MoveEye – Teil 553: SmallTV «Live-Bild und Wechsel» (Entscheide Daniel 30.10.2026 Abend): tagsüber alle 30 s Live-Bild ↔ Akku und Strom, Alarm als animiertes GIF (60 s), danach das Standbild 5 min, Bilder pro Tag. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Pro Bildschirm ein Schalter «Live-Bild und Wechsel» (Feld «rot» in stv_list, 552). Aus = wie bisher (Statusseite).
# Ein (nur tagsüber - nachts bleibt die rote, gedimmte Statusseite):
#   alle STV_ROT_S = 30 s wechselt die Seite: gerade Zeitscheibe «Live-Bild» (Standbild der Hauptkamera, 240 × 240 mit
#   Leiste Uhrzeit · Aus/Wachsam/Voll · Akku), ungerade «Akku und Strom» (grosser Akku, Laden/Solar, Verbrauch, Restlaufzeit,
#   «SIM» bei Simulator-Werten). Das Live-Bild ist nur bei jeder zweiten Live-Zeitscheibe neu (Daniel 30.10.: halb so viele
#   Uploads, ein neues Bild alle 2 min, beim Zeigen höchstens 60 s alt); dazwischen wird es nur wieder gezeigt;
#   das Bild ist das reine Kamerabild ohne Leiste «Tilt … | CPU …» und ohne Rahmen (410 frame_clean, nur auf Anfrage);
#   die Akku-Seite liegt noch auf dem Gerät (me_a / me_b, 552 StvDev.send «stored»): unverändert wird sie nur wieder gezeigt
#   (/set?img=…, kein Schreiben in den Flash). Ohne Akku-Werte ist die zweite Seite die Statusseite.
#   Personen im Live-Bild: Privatzonen sind schon geschwärzt (frame_out, 030 apply_privacy); ohne «Bild auch bei Personen»
#   werden die erkannten Personen (STATE person_boxes) grob verpixelt (faces_pixelate, 375).
# Alarm (Vorrang wie bisher: Alarm, Spielrunde): zuerst ein animiertes GIF 240 × 240 (8 Bilder, pulsierender roter Rahmen,
#   blinkendes ⚠ + Art), stv_alarm_s (60 s), danach das Alarmbild als JPEG mit ⚠ stv_alarm_keep_min (5 min), dann zurück.
#   Das GIF geht wie ein JPEG nach /image/ (me_a.gif / me_b.gif); die Datei mit der anderen Endung am gleichen Platz wird
#   gelöscht (552 StvDev._drop), so liegen nie mehr als zwei Bilder auf dem Gerät.
# Schonung: «ca. N Bilder/Tag» je Bildschirm in der Liste und im Protokoll (stv_per_day).
# ----------------------------------------------------------------------------
STV_ROT_S = 30
STV_GIF_FRAMES = 8


def stv_rot_page(now):
    """«live» or «batt»: the page of the 30-s slot of this time (real clock, so every display switches at the same moment)"""
    return "live" if int(now // STV_ROT_S) % 2 == 0 else "batt"


def _stv_batt_ok():
    b = STATE.get("battery") or {}
    return bool(b.get("on") and b.get("pct") is not None)


def stv_rot_plan(now, lang):
    """(kind, key, render function) of the rotation, or None (-> the status page)"""
    slot = int(now // STV_ROT_S)
    if stv_rot_page(now) == "live":
        return "live", ("live", slot // 4, lang), lambda: stv_render_live(lang)   # every second live slot new (slots 4k and 4k+2)
    if not _stv_batt_ok():
        return None
    b = STATE.get("battery") or {}
    sol = _stv_solar_w(b)
    clock = int(sim_now().timestamp() // (60 * max(1, int(CFG.get("stv_clock_min", 10) or 10))))
    key = ("batt", int(b.get("pct") or 0), None if sol is None else int(round(sol)), round(float(b.get("use_w") or 0) * 2) / 2,
           None if b.get("hours") is None else round(float(b["hours"]) * 2) / 2, bool(b.get("charging")), bool(b.get("on_battery")),
           bool(b.get("sim")), b.get("full_min"), clock, lang)
    return "batt", key, lambda: stv_render_batt(lang)


def _stv_solar_w(b):
    w_ = b.get("solar_w")
    if w_ is None and CFG.get("solar_on"):
        w_ = (STATE.get("solar") or {}).get("w")
    try:
        return None if w_ is None else float(w_)
    except (TypeError, ValueError):
        return None


# ---- the live still -----------------------------------------------------------------------------------------------------
def stv_clean_frame(w, wait=1.5):
    """the pure camera picture (after the privacy zones and the grey picture mode, before HUD, boxes and marks): 410 copies
    it only while asked (clean_until) - None when no fresh one comes"""
    w.clean_until = time.time() + 4.0
    t_end = time.time() + wait
    while True:
        f, ft = getattr(w, "frame_clean", None), float(getattr(w, "frame_clean_t", 0.0) or 0.0)
        if f is not None and time.time() - ft < 3.0:
            return f
        if time.time() >= t_end or not getattr(w, "running", True):
            return None
        time.sleep(0.1)


def stv_live_frame(person_pic=None):
    """a copy of the picture of the main camera (privacy zones already black) - persons pixelated unless «Bild auch bei Personen».
    Daniel 30.10.: the pure picture without the strip «Tilt 50% | CPU …» and the marks of MoveEye (stv_clean_frame);
    only when there is none, the picture of the page without its text line (as before)"""
    w = WATCH_REF.get("w") if "WATCH_REF" in globals() else None
    if w is None:
        return None
    f = stv_clean_frame(w)
    if f is not None:
        f = f.copy()
    else:
        f = getattr(w, "frame_out", None)
        if f is None:
            return None
        f = f.copy()
        if CFG.get("show_hud") and f.shape[0] > 120:
            f = f[34:]                                    # without the text line on top of the live picture (410 HUD)
    if not (CFG.get("stv_person_pic") if person_pic is None else person_pic):
        stv_hide_persons(f, STATE.get("person_boxes") if STATE.get("persons") else [])
    return f


def stv_hide_persons(f, boxes):
    """the person boxes (0..1 of the picture) as coarse blocks - the same helper as «Gesichter verpixeln» (375)"""
    H, W = f.shape[:2]
    px = []
    for b in boxes or []:
        try:
            px.append((int(b[0] * W), int(b[1] * H), max(2, int(b[2] * W)), max(2, int(b[3] * H))))
        except (TypeError, ValueError, IndexError):
            continue
    if px:
        faces_pixelate(f, px, pad=0.15)
    return len(px)


def stv_render_live(lang=None, frame=None):
    from PIL import Image
    im, d = _stv_canvas()
    f = stv_live_frame() if frame is None else frame
    bar = 30
    if f is not None:
        try:
            H, W = f.shape[:2]
            s_ = min(H, W)
            x0, y0 = (W - s_) // 2, (H - s_) // 2
            sq = cv2.resize(f[y0:y0 + s_, x0:x0 + s_], (STV_SIZE, STV_SIZE), interpolation=cv2.INTER_AREA)
            im.paste(Image.fromarray(cv2.cvtColor(sq, cv2.COLOR_BGR2RGB)), (0, 0))
        except Exception:
            f = None
    if f is None:
        d.rounded_rectangle((80, 70, 160, 130), radius=10, outline=(110, 125, 145), width=4)
        d.ellipse((104, 84, 136, 116), outline=(110, 125, 145), width=4)
        t_ = tr("No camera picture", lang)
        d.text(((STV_SIZE - d.textlength(t_, font=_font(16))) / 2, 146), t_, font=_font(16), fill=(170, 185, 205))
    # small «● LIVE» top left
    d.rounded_rectangle((6, 6, 62, 26), radius=6, fill=(0, 0, 0))
    d.ellipse((11, 11, 21, 21), fill=(255, 60, 60))
    d.text((25, 7), "LIVE", font=_font(14), fill=(255, 255, 255))
    # the bar: time · state · battery
    d.rectangle((0, STV_SIZE - bar, STV_SIZE, STV_SIZE), fill=(8, 12, 18))
    now = sim_now()
    d.text((8, STV_SIZE - bar + 5), now.strftime("%H:%M"), font=_font(17), fill=(232, 238, 245))
    name, col = stv_level_name(lang)
    if walktest_on():
        name, col = tr("Walk test", lang), (180, 140, 40)
    f2 = _font(15)
    name = _stv_fit(d, name, f2, 86)
    tw = d.textlength(name, font=f2)
    cx = 120
    d.rounded_rectangle((cx - tw / 2 - 8, STV_SIZE - bar + 4, cx + tw / 2 + 8, STV_SIZE - 4), radius=8, fill=col)
    d.text((cx - tw / 2, STV_SIZE - bar + 6), name, font=f2, fill=(255, 255, 255))
    b = STATE.get("battery") or {}
    if b.get("on") and b.get("pct") is not None:
        pct = int(b["pct"])
        x, y, w_, h_ = 178, STV_SIZE - bar + 9, 22, 12
        c_ = (63, 207, 107) if pct > 50 else (245, 154, 74) if pct > 20 else (255, 77, 77)
        d.rectangle((x, y, x + w_, y + h_), outline=(200, 210, 225), width=1)
        d.rectangle((x + w_ + 1, y + 3, x + w_ + 3, y + h_ - 3), fill=(200, 210, 225))
        fw = int((w_ - 4) * max(0, min(100, pct)) / 100)
        if fw > 0:
            d.rectangle((x + 2, y + 2, x + 2 + fw, y + h_ - 2), fill=c_)
        pt = f"{pct}%"
        d.text((STV_SIZE - 6 - d.textlength(pt, font=_font(13)), STV_SIZE - bar + 8), pt, font=_font(13), fill=(232, 238, 245))
    return _stv_jpg(im)


# ---- the battery page ---------------------------------------------------------------------------------------------------
def _stv_bolt(d, x, y, s, col):
    """a lightning bolt (charging), drawn"""
    d.polygon([(x + s * 0.55, y), (x + s * 0.1, y + s * 0.58), (x + s * 0.45, y + s * 0.58), (x + s * 0.3, y + s),
               (x + s * 0.9, y + s * 0.38), (x + s * 0.55, y + s * 0.38), (x + s * 0.75, y)], fill=col, outline=(20, 20, 20))


def _stv_hours(h):
    try:
        h = float(h)
    except (TypeError, ValueError):
        return "–"
    if h >= 48:
        return f"{h / 24.0:.1f} d"
    hh, mm = int(h), int(round((h - int(h)) * 60))
    if mm == 60:
        hh, mm = hh + 1, 0
    return f"{hh} h {mm:02d} min" if hh else f"{mm} min"


def stv_render_batt(lang=None):
    im, d = _stv_canvas()
    now = sim_now()
    _stv_head(im, d, now.strftime("%H:%M"))
    b = STATE.get("battery") or {}
    t_ = tr("Battery and power", lang)
    d.text((10, 34), _stv_fit(d, t_, _font(15), STV_SIZE - 70), font=_font(15), fill=(245, 154, 74))
    if b.get("sim"):
        d.rounded_rectangle((STV_SIZE - 50, 34, STV_SIZE - 10, 52), radius=5, fill=(70, 50, 120))
        d.text((STV_SIZE - 45, 35), "SIM", font=_font(14), fill=(225, 210, 255))
    pct = int(b.get("pct") or 0)
    col = (63, 207, 107) if pct > 50 else (245, 154, 74) if pct > 20 else (255, 77, 77)
    x, y, w_, h_ = 12, 60, 112, 56                         # the big drawn battery
    d.rounded_rectangle((x, y, x + w_, y + h_), radius=8, outline=(200, 210, 225), width=3)
    d.rounded_rectangle((x + w_ + 2, y + 16, x + w_ + 9, y + h_ - 16), radius=2, fill=(200, 210, 225))
    fw = int((w_ - 10) * max(0, min(100, pct)) / 100)
    if fw > 0:
        d.rounded_rectangle((x + 5, y + 5, x + 5 + fw, y + h_ - 5), radius=4, fill=col)
    if b.get("charging"):
        _stv_bolt(d, x + w_ / 2 - 14, y + 8, 40, (255, 230, 80))
    pt = f"{pct} %"
    f = _font(40)
    while d.textlength(pt, font=f) > STV_SIZE - (x + w_ + 18) - 6 and f.size > 24:
        f = _font(f.size - 2)
    d.text((x + w_ + 18, y + 4), pt, font=f, fill=(232, 238, 245))
    rows = []
    sol = _stv_solar_w(b)
    if b.get("charging"):
        v_ = trf("full in {n} min", lang, n=int(b["full_min"])) if b.get("full_min") else tr("yes", lang)
        rows.append((tr("Charging", lang), v_))
    elif not b.get("on_battery", True):
        rows.append((tr("Charging", lang), tr("Mains power", lang)))
    if sol is not None:
        rows.append((tr("Solar", lang), f"{sol:.1f} W"))
    if b.get("use_w") is not None:
        rows.append((tr("Consumption", lang), f"{float(b['use_w']):.1f} W"))
    rows.append((tr("Runtime left", lang), _stv_hours(b.get("hours")) if b.get("on_battery", True) and not b.get("charging") else "–"))
    yy = 128
    f1, f2 = _font(16, False), _font(17)
    for lb, v_ in rows[:4]:
        d.text((12, yy), _stv_fit(d, lb, f1, 110), font=f1, fill=(170, 185, 205))
        v_ = _stv_fit(d, v_, f2, STV_SIZE - 130)
        d.text((STV_SIZE - 12 - d.textlength(v_, font=f2), yy - 1), v_, font=f2, fill=(232, 238, 245))
        yy += 23
    d.text((10, STV_SIZE - 22), _stv_fit(d, tr("as of", lang) + " " + now.strftime("%H:%M") + ("  ·  " + tr("simulator", lang) if b.get("sim") else ""),
                                         _font(14, False), STV_SIZE - 20), font=_font(14, False), fill=(110, 125, 145))
    return _stv_jpg(im)


# ---- the alarm animation (GIF) ------------------------------------------------------------------------------------------
def stv_render_alarm_gif(a, lang=None, red=False, n=STV_GIF_FRAMES, ms=160):
    """animated GIF 240 × 240: the alarm picture with a pulsing red frame and a blinking ⚠. One palette for all frames,
    from the 2nd frame only the changed pixels (the rest transparent) - so it stays small (about 30-70 KB)."""
    from PIL import Image
    import io
    fr = []
    for k in range(n):
        ph = (1 + math.cos(2 * math.pi * k / n)) / 2.0      # 1 -> 0 -> 1
        edge = 4 + int(round(8 * ph))
        ec = (int(130 + 125 * ph), int(10 + 50 * ph), int(10 + 50 * ph))
        wc = (255, 214, 0) if k < n // 2 else (255, 120, 40)
        im = _stv_alarm_im(a, lang, edge=edge, edge_col=ec, warn=True, warn_col=wc)
        fr.append(_stv_red(im) if red else im)
    strip = Image.new("RGB", (STV_SIZE, STV_SIZE * n))
    for k, im in enumerate(fr):
        strip.paste(im, (0, k * STV_SIZE))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = [np.asarray(im.quantize(palette=pal, dither=Image.Dither.NONE), np.uint8) for im in fr]
    pl = pal.getpalette()[:255 * 3] + [0, 0, 0]
    out = []
    for k, ix in enumerate(idx):
        q = ix.copy()
        if k:
            q[ix == idx[k - 1]] = 255                      # unchanged -> transparent (the frame before stays: disposal 1)
        p = Image.fromarray(q, "P")
        p.putpalette(pl)
        out.append(p)
    b = io.BytesIO()
    out[0].save(b, "GIF", save_all=True, append_images=out[1:], duration=ms, loop=0, transparency=255, disposal=1, optimize=False)
    return b.getvalue()


# ---- how many pictures a day (flash wear) -------------------------------------------------------------------------------
def _stv_day_hours():
    """hours of daylight today (sun times of the place; 12 without)"""
    try:
        st = sun_times(datetime.now().date(), float(CFG["latitude"]), float(CFG["longitude"]))
        if isinstance(st, str):
            return 0.0 if st == "dark" else 24.0
        return max(0.0, min(24.0, (st[1] - st[0]) / 60.0))
    except Exception:
        return 12.0


def stv_per_day(e):
    """about how many pictures a day go to this display (uploads = writes into its flash), without alarms / games:
    status: the clock every stv_clock_min minutes + about one change an hour; rotation by day: the live picture every
    120 s (every second live slot, Daniel 30.10.), the battery page when its values changed (about every third time), night: status"""
    if not e.get("on"):
        return 0
    clock = max(1, int(CFG.get("stv_clock_min", 10) or 10))
    st_h = 60.0 / clock + 1.0                              # status page per hour
    if not e.get("rot"):
        return int(round(24 * st_h)) if e.get("status") else 0
    day = _stv_day_hours() if CFG.get("stv_night") else 24.0
    batt_h = 20.0 if _stv_batt_ok() else (st_h if e.get("status") else 0.0)
    n = day * (3600.0 / (4 * STV_ROT_S) + batt_h) + (24.0 - day) * (st_h if e.get("status") else 0.0)
    return int(round(n / 10.0) * 10)


_stv_tick_552 = stv_tick


# wraps: stv_tick
def stv_tick():                                           # + 553: the number of pictures a day in the log when it changes
    _stv_tick_552()
    try:
        P = STV.setdefault("per_day", {})
        for e in stv_entries() if CFG.get("stv_on") else []:
            n = stv_per_day(e)
            if P.get(e["id"]) != n:
                if e["id"] in P or n:
                    log_event("sys", f"SmallTV {e['name']}: about {n} pictures/day (live picture and rotation {'on' if e.get('rot') else 'off'})")
                P[e["id"]] = n
    except Exception:
        pass


_stv_state_552 = stv_state


# wraps: stv_state
def stv_state(lang=None):                                 # + 553: «ca. N Bilder/Tag» and «only shown again» per display
    r = _stv_state_552(lang)
    for x in r.get("list") or []:
        try:
            x["per_day"] = stv_per_day(x)
            dv = STV["devs"].get(x["id"])
            x["reshows"] = getattr(dv, "reshows", 0) if dv else 0
        except Exception:
            x["per_day"] = None
    r["rot_s"] = STV_ROT_S
    return r
