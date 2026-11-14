#@ MoveEye – Teil 639zzzw: «🔥 Glut-Wächter» – Feuerstelle einmal merken (Kopf + heisser Bereich im Wärmebild), «Ist das Feuer aus?» (Kopf dreht hin, ein paar Wärmebilder, höchste Temperatur der Feuerstelle), Nachtwache «Feuer überwachen» (wieder heiss / neuer heisser Punkt daneben → leiser steigender Ton + Push). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (14.11.2026, freigegeben):
#  Merken      «Feuerstelle merken» (Schutz → Modus, sichtbar bei Camping / Lagerfeuer oder wenn die Wache läuft; Pi-Fenster im
#              Abschnitt «Camping / Schutz»): den Kopf vorher von Hand aufs brennende Feuer richten. Gespeichert werden die
#              Kopfstellung (servo_pos, %) und der heisse Bereich im Wärmebild (Rechteck 0..1 um den heissesten Fleck + 2 Pixel
#              Rand, damit ein kleines Zielen daneben nichts ausmacht). Ohne Fleck ab GLUT_TEACH_MIN °C: nichts gemerkt.
#  Prüfen      «Ist das Feuer aus?»: der Kopf fährt zur Feuerstelle (Planer 072, wie der Wertsachen-Blick 162: Anspruch
#              KOPF["glance"], ein Alarm geht vor und bricht ab), GLUT_FRAMES Wärmebilder, höchste Temperatur im Bereich,
#              zurück zur alten Stellung. Unter glut_off_c (40 °C) «✅ aus – höchstens 38 °C», sonst «⚠️ Glut noch 180 °C –
#              mehr Wasser, umrühren». Immer der ehrliche Hinweis: nur die Oberfläche, Glut unter Asche / Erde kann fehlen –
#              kein Ersatz fürs richtige Löschen (Almanach «Feuer richtig löschen», 630).
#  Gesperrt    Transportmodus (Kopf-Transport 639zzzt oder Modus «Transport / Ruhe») und Not-Aus / Störung: der Kopf fährt nie;
#              steht er schon an der Feuerstelle, wird trotzdem gemessen. Alarm / Folgen: der Knopf sagt «Alarm geht vor», die
#              Wache versucht es 30 s später wieder (danach wieder zum Feuer).
#  Wache       «Feuer überwachen» (glut_watch, bleibt nach Neustart): alle glut_every_min Minuten (über mode_tick, alle 10 s,
#              kein eigener Faden; das Wärmebild-Modul wird nur für die Messung geöffnet – wenig Rechenzeit). Alarm, wenn
#              (a) die Feuerstelle deutlich wieder heisser wird (Median der Bilder ≥ glut_off_c und ≥ tiefster Wert seit dem
#              Einschalten + max(glut_rise_k, 30 %)) oder (b) ausserhalb des Bereichs ein NEUER Punkt ≥ glut_new_c erscheint
#              (in mindestens 2 Bildern: Funke / kriechendes Feuer). Alarm: drei leise, steigende Tonfolgen am Gerät
#              (sound_play «beep4», 35 / 60 / 90 % der Sirenen-Lautstärke), Push mit Wärmebild (notifier.alert, wenn
#              eingerichtet), Protokoll; dieselbe Art höchstens alle GLUT_COOL_S.
#  Anzeige     Ergebnis-Karte (Web + Fenster-Text), Wärmebild der letzten Messung mit Umriss + Höchstwert (/api/glut/bild.jpg),
#              im Live-Wärmebild (thermal_on) derselbe Umriss mit dem Höchstwert, solange der Kopf an der Feuerstelle steht.
#  Sensor      Waveshare Thermal-90 (MI48): −40 … +400 °C, ±1.5 °C nur zwischen 10 und 70 °C, 1 Pixel ≈ 1.1° – kleine Glut
#              weit weg wird mit der Umgebung gemittelt (zeigt zu wenig), über 400 °C steht «400+».
# Rechte: wie der Modus («arm»). Texte: _HX_GLUT (5 Sprachen). Test: werkzeuge/glut_test.py.
# ----------------------------------------------------------------------------
GLUT_DEF = {"glut_spot": {}, "glut_off_c": 40.0, "glut_watch": False, "glut_every_min": 2.0, "glut_rise_k": 15.0, "glut_new_c": 60.0}
for _k, _v in GLUT_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
    FACTORY_CFG.setdefault(_k, json.loads(json.dumps(_v)))
GLUT_TEACH_MIN = 50.0             # °C: only a spot at least this hot is taken as the fire
GLUT_FRAMES = 5                   # thermal pictures per check
GLUT_AT = 1.5                     # % pan / tilt: the head counts as «at the fire spot»
GLUT_RING = 2                     # px around the fire region that belong to it (embers spread, aiming is never exact)
GLUT_COOL_S = 600.0               # the same kind of alarm at most every 10 min
GLUT_MAX_C = 400.0                # end of the range of the MI48
GLUT = {"busy": False, "last": None, "jpg": None, "low": None, "next": 0.0, "need_until": 0.0, "note": "", "alarm": None, "cool": {}}
_GLUT_LOCK = threading.Lock()
PERM_GET["arm"] = tuple(PERM_GET.get("arm", ())) + ("/api/glut",)        # /api/glut and /api/glut/bild.jpg
PERM_POST["arm"] = set(PERM_POST.get("arm", ())) | {"/api/glut"}


def glut_taught():
    s = CFG.get("glut_spot")
    return isinstance(s, dict) and len(s.get("box") or []) == 4


def glut_transport():
    return bool(CFG.get("kopf_transport")) or CFG.get("mode") == "transport" or servo_blocked() == "transport"


def glut_alarm_busy():
    return bool(STATE.get("persons") or STATE.get("tracking") or KOPF.get("alarm") or KOPF.get("tamper") or KOPF.get("turn_req"))


def glut_at_spot(s):
    p, t = servo_pos()
    return abs(p - float(s["pan"])) <= GLUT_AT and abs(t - float(s["tilt"])) <= GLUT_AT


def glut_alm_link():
    try:
        i = [a[0] for c in ALMANAC for a in c[3]].index("Feuer richtig löschen")
        return "/almanach/#a%d" % i
    except (NameError, ValueError):
        return "/almanach/"


# ---- the thermal pictures: the module is opened only for a measurement (ThermalCam.wanted) -------------------------------------
_glut_wanted_base = ThermalCam.wanted


def _glut_wanted(self):
    w = _glut_wanted_base(self)
    if not w and time.time() < GLUT["need_until"]:
        spec = str(CFG.get("thermal_source") or "")
        return spec if spec and spec != STATE.get("source_id") else ""
    return w


# wraps: ThermalCam.wanted
ThermalCam.wanted = _glut_wanted


def glut_frames(n=GLUT_FRAMES, timeout=10.0):
    """-> ([float °C pictures], '') or ([], english reason). Waits for pictures taken after the call (the head stands)."""
    if not str(CFG.get("thermal_source") or ""):
        return [], "No thermal camera chosen (Settings → Thermal camera)."
    t0 = time.time()
    GLUT["need_until"] = t0 + timeout + 5.0
    out, last = [], 0.0
    try:
        while time.time() - t0 < timeout and len(out) < n:
            th = THERMAL
            fr, ft = (getattr(th, "frame", None), float(getattr(th, "t", 0.0) or 0.0)) if th is not None else (None, 0.0)
            if fr is not None and ft > t0 + 0.3 and ft != last:
                if fr.dtype == np.uint8 or (fr.ndim == 3 and fr.shape[2] != 1):
                    return [], "This thermal source gives no temperatures (only colours) - the fire watch needs the Thermal-90."
                out.append(np.array(fr, np.float32).reshape(fr.shape[:2])); last = ft
            time.sleep(0.05)
    finally:
        GLUT["need_until"] = 0.0
    if not out:
        return [], "The thermal camera gives no picture: " + str(STATE.get("thermal") or "?")
    return out, ""


# ---- teach and measure (pure: pictures in, numbers out) ----------------------------------------------------------------------
def glut_find(f):
    """the hot region around the hottest spot -> ([x, y, w, h] 0..1, hottest °C) or (None, hottest °C)"""
    mx = float(f.max())
    if mx < GLUT_TEACH_MIN:
        return None, mx
    med = float(np.median(f))
    m = (f >= max(med + 0.25 * (mx - med), float(CFG.get("glut_off_c") or 40))).astype(np.uint8)
    _n, lab = cv2.connectedComponents(m)
    y, x = np.unravel_index(int(np.argmax(f)), f.shape)
    ys, xs = np.nonzero(lab == lab[y, x])
    H, W = f.shape
    x0, x1 = max(0, xs.min() - GLUT_RING), min(W, xs.max() + 1 + GLUT_RING)
    y0, y1 = max(0, ys.min() - GLUT_RING), min(H, ys.max() + 1 + GLUT_RING)
    return [x0 / W, y0 / H, (x1 - x0) / W, (y1 - y0) / H], mx


def glut_px(box, shape, ring=0):
    H, W = shape[:2]
    x0, y0 = int(math.floor(box[0] * W)) - ring, int(math.floor(box[1] * H)) - ring
    x1, y1 = int(math.ceil((box[0] + box[2]) * W)) + ring, int(math.ceil((box[1] + box[3]) * H)) + ring
    return max(0, x0), max(0, y0), min(W, max(x0 + 1, x1)), min(H, max(y0 + 1, y1))


def glut_measure(frames, box, new_c):
    """-> {max, med, over, new: [[x, y, °C] 0..1]} - fire region maximum over all pictures, new hot spots outside"""
    x0, y0, x1, y1 = glut_px(box, frames[0].shape)
    mxs = [float(f[y0:y1, x0:x1].max()) for f in frames]
    hits, best = 0, None
    for f in frames:
        g = f.copy()
        a0, b0, a1, b1 = glut_px(box, f.shape, GLUT_RING)
        g[b0:b1, a0:a1] = -999.0
        if float(g.max()) >= new_c:
            hits += 1
            if best is None or float(g.max()) > float(best.max()):
                best = g
    new = []
    if best is not None and hits >= min(2, len(frames)):
        _n, lab, st, _c = cv2.connectedComponentsWithStats((best >= new_c).astype(np.uint8))
        H, W = best.shape
        for i in sorted(range(1, _n), key=lambda i: -st[i, cv2.CC_STAT_AREA])[:3]:
            ys, xs = np.nonzero(lab == i)
            j = int(np.argmax(best[ys, xs]))
            new.append([round((xs[j] + 0.5) / W, 3), round((ys[j] + 0.5) / H, 3), round(float(best[ys[j], xs[j]]), 1)])
    mx = max(mxs)
    return {"max": round(min(mx, GLUT_MAX_C), 1), "med": round(float(np.median(mxs)), 1), "over": mx >= GLUT_MAX_C - 0.5, "new": new}


def _glut_put(img, txt, x, y, col, k=0.5):
    """text with a drawn degree sign (the cv2 fonts have none): «38 °C» is written as «38», a small ring, «C»"""
    a, b = txt.split("°", 1) if "°" in txt else (txt, None)
    for c_, th in (((0, 0, 0), 3), (col, 1)):
        cv2.putText(img, a, (x, y), cv2.FONT_HERSHEY_SIMPLEX, k, c_, th, cv2.LINE_AA)
    if b is not None:
        w = cv2.getTextSize(a, cv2.FONT_HERSHEY_SIMPLEX, k, 1)[0][0]
        r = max(2, int(4 * k))
        cv2.circle(img, (x + w + r + 1, y - int(22 * k)), r, col, 1, cv2.LINE_AA)
        for c_, th in (((0, 0, 0), 3), (col, 1)):
            cv2.putText(img, b, (x + w + 2 * r + 3, y), cv2.FONT_HERSHEY_SIMPLEX, k, c_, th, cv2.LINE_AA)


def glut_temp_txt(t, over=False):
    return ("%d+ °C" % GLUT_MAX_C) if over else ("%.0f °C" % t)


def glut_image(f, box, res=None, scale=8):
    """the thermal picture (inferno) with the outline of the fire region, its maximum and the new hot spots -> BGR"""
    lo = float(np.percentile(f, 2)); hi = max(float(f.max()), lo + 5.0)
    g = np.clip((f - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
    img = cv2.resize(cv2.applyColorMap(g, cv2.COLORMAP_INFERNO), (f.shape[1] * scale, f.shape[0] * scale), interpolation=cv2.INTER_CUBIC)
    H, W = img.shape[:2]
    if box:
        x0, y0, x1, y1 = glut_px(box, f.shape)
        cv2.rectangle(img, (x0 * scale, y0 * scale), (x1 * scale - 1, y1 * scale - 1), (255, 255, 255), 2, cv2.LINE_AA)
        if res:
            _glut_put(img, glut_temp_txt(res["max"], res.get("over")), x0 * scale + 4, max(18, y0 * scale - 6), (255, 255, 255), 0.6)
    for x, y, t in (res or {}).get("new", []):
        cv2.circle(img, (int(x * W), int(y * H)), 14, (60, 60, 255), 2, cv2.LINE_AA)
        _glut_put(img, glut_temp_txt(t), int(x * W) + 16, int(y * H) + 5, (90, 90, 255), 0.5)
    return img


def glut_err_tr(e, lang=None, **kw):
    k = "The thermal camera gives no picture: "
    return tr(k, lang) + str(e)[len(k):] if str(e).startswith(k) else trf(str(e), lang, **kw)


def glut_result_text(r, lang=None):
    if not r:
        return ""
    if r.get("kind") == "err":
        return "⚠ " + glut_err_tr(r.get("err", ""), lang)
    t = glut_temp_txt(r["max"], r.get("over"))
    return ("✅ " + trf("out – at most {t}", lang, t=t)) if r["kind"] == "out" else ("⚠️ " + trf("Embers still {t} – more water, stir", lang, t=t))


# ---- the head: to the fire spot and back -----------------------------------------------------------------------------------
def _glut_abort():
    return glut_alarm_busy() or bool(servo_blocked())


def glut_head_to(s):
    """-> (moved, old position, english reason or ''). Never moves in the transport mode; an alarm comes first."""
    if glut_at_spot(s):
        return False, None, ""
    if glut_transport():
        return False, None, "Transport mode: the head does not move - it is not looking at the fire."
    if glut_alarm_busy():
        return False, None, "An alarm comes first - try again in a moment."
    if servo_blocked():
        return False, None, "Emergency stop or servo fault - the head does not move."
    if KOPF.get("glance"):
        return False, None, "The head is busy (quick look) - try again in a moment."
    old = servo_pos()
    KOPF["glance"] = "fire"                                  # the round / parking wait, an alarm (higher rank) takes over
    if not servo_goto(float(s["pan"]), float(s["tilt"]), "glut", wait=True, stop=_glut_abort, timeout=25.0):
        return True, old, "An alarm comes first - try again in a moment." if glut_alarm_busy() else "The head was interrupted."
    time.sleep(0.8)                                          # settle (the module filters over ~0.2 s)
    return True, old, ""


def _glut_head_back(moved, old):
    try:
        if moved and old is not None and not _glut_abort() and not glut_transport():
            servo_goto(old[0], old[1], "glut", wait=False)
    finally:
        if KOPF.get("glance") == "fire":
            KOPF["glance"] = ""


# ---- teach, check, watch -------------------------------------------------------------------------------------------------
def glut_teach(who="web"):
    """the head looks at the burning fire: remember its position and the hot region -> (ok, english message, {t})"""
    if not _GLUT_LOCK.acquire(blocking=False):
        return False, "A check is already running.", {}
    try:
        GLUT["busy"] = True
        fr, err = glut_frames(3)
        if err:
            return False, err, {}
        f = np.mean(np.stack(fr), axis=0)
        box, mx = glut_find(f)
        if box is None:
            return False, "No fire in the thermal picture (hottest {t}) - remember the spot while the fire burns or the embers are hot.", {"t": glut_temp_txt(mx)}
        p, t = servo_pos()
        CFG["glut_spot"] = {"pan": round(p, 2), "tilt": round(t, 2), "box": [round(v, 4) for v in box], "max": round(min(mx, GLUT_MAX_C), 1),
                            "t": time.time(), "by": str(who)[:60]}
        res = {"max": round(min(mx, GLUT_MAX_C), 1), "over": mx >= GLUT_MAX_C - 0.5, "new": []}
        ok, buf = cv2.imencode(".jpg", glut_image(f, box, res), [cv2.IMWRITE_JPEG_QUALITY, 85])
        GLUT.update(jpg=buf.tobytes() if ok else None, low=None, last=None)
        save_settings()
        log_event("sys", f"Fire watch: fire spot remembered ({who}) at pan {p:.1f} % / tilt {t:.1f} %, hottest {mx:.0f} °C")
        return True, "Fire spot remembered (hottest {t}).", {"t": glut_temp_txt(mx, mx >= GLUT_MAX_C - 0.5)}
    finally:
        GLUT["busy"] = False
        _GLUT_LOCK.release()


def glut_check(who="web", auto=False):
    """«Is the fire out?» -> result dict {kind: out / glow / err, max, med, over, new, err, t}"""
    if not glut_taught():
        return {"kind": "err", "err": "Remember the fire spot first.", "t": time.time()}
    if not _GLUT_LOCK.acquire(blocking=False):
        return {"kind": "err", "err": "A check is already running.", "t": time.time()}
    moved, old = False, None
    try:
        GLUT["busy"] = True
        s = CFG["glut_spot"]
        r = None
        if not str(CFG.get("thermal_source") or ""):
            r = {"kind": "err", "err": "No thermal camera chosen (Settings → Thermal camera)."}
        else:
            moved, old, why = glut_head_to(s)
            if why:
                r = {"kind": "err", "err": why}
        if r is None:
            fr, err = glut_frames()
            if err:
                r = {"kind": "err", "err": err}
            else:
                r = glut_measure(fr, s["box"], float(CFG.get("glut_new_c") or 60))
                r["kind"] = "out" if r["max"] < float(CFG.get("glut_off_c") or 40) else "glow"
                img = glut_image(fr[int(np.argmax([float(f.max()) for f in fr]))], s["box"], r)
                ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
                GLUT["jpg"] = buf.tobytes() if ok else GLUT["jpg"]
                if auto:
                    glut_watch_eval(r, img)
        r.update(t=time.time(), auto=bool(auto))
        GLUT["last"] = r
        if not auto or r["kind"] == "err":
            log_event("sys", f"Fire watch: check ({who}): " + glut_result_text(r, "en"))
        return r
    finally:
        _glut_head_back(moved, old)
        GLUT["busy"] = False
        _GLUT_LOCK.release()


def glut_watch_eval(r, img):
    """night watch: (a) the fire region heats up again by a clear margin, (b) a new hot spot outside it"""
    low = GLUT["low"]
    off_c = float(CFG.get("glut_off_c") or 40)
    if low is not None and r["med"] >= off_c and r["med"] >= low + max(float(CFG.get("glut_rise_k") or 15), 0.3 * low):
        if glut_alarm("reflare", trf("The fire heats up again: {t} (was {b})", t=glut_temp_txt(r["max"], r.get("over")), b=glut_temp_txt(low)), img):
            low = r["med"]                                   # a new base: it warns again only when it rises further
    GLUT["low"] = r["med"] if low is None else min(low, r["med"])
    if r["new"]:
        glut_alarm("spot", trf("New hot spot next to the fire: {t} - spark or creeping fire?", t=glut_temp_txt(max(n[2] for n in r["new"]))), img)


def glut_alarm(kind, text, img=None):
    now = time.time()
    if now - GLUT["cool"].get(kind, 0.0) < GLUT_COOL_S:
        return False
    GLUT["cool"][kind] = now
    GLUT["alarm"] = {"kind": kind, "text": text, "t": now}
    log_event("alarm", "Fire watch: " + text)

    def tone():
        for k in (0.35, 0.6, 0.9):                          # soft, then louder: three rising beeps
            if not sound_play("beep4", 1.2, float(CFG.get("siren_volume") or 70) * k, reason="fire")[0]:
                return
            time.sleep(3.0)
    threading.Thread(target=tone, daemon=True, name="glut-tone").start()
    w = WATCH_REF.get("w")
    try:
        if w is not None:
            w.notifier.alert("{name}: 🔥 " + tr("Fire watch"), text, img)
    except Exception as e:
        log_event("sys", f"Fire watch push: {e}"[:160])
    return True


def glut_set_watch(on, who="web"):
    CFG["glut_watch"] = bool(on)
    GLUT.update(low=None, next=time.time() + 3.0, note="", cool={})
    save_settings()
    log_event("sys", f"Fire watch {'ON' if on else 'OFF'} ({who})")


def glut_tick():
    """every 10 s (mode_tick): the night watch starts a check when it is due - an alarm on persons comes first"""
    if not (CFG.get("glut_watch") and glut_taught()) or GLUT["busy"]:
        return
    now = time.time()
    if now < GLUT["next"]:
        return
    if (glut_alarm_busy() or KOPF.get("glance") or not kopf_may("glance")) and not glut_at_spot(CFG["glut_spot"]):
        GLUT.update(next=now + 30.0, note="alarm")
        return
    GLUT.update(next=now + max(1.0, min(30.0, float(CFG.get("glut_every_min") or 2))) * 60.0, note="")
    threading.Thread(target=glut_check, args=("watch", True), daemon=True, name="glut-watch").start()


_glut_mode_tick = mode_tick


# wraps: mode_tick (130, every 10 s from the battery loop 100)
def mode_tick():
    _glut_mode_tick()
    try:
        glut_tick()
    except Exception as e:
        log_event("sys", f"Fire watch: {e}"[:160])


def glut_state():
    s = CFG.get("glut_spot") if glut_taught() else None
    a = GLUT["alarm"]
    return {"taught": bool(s), "spot_t": s.get("t", 0) if s else 0, "spot_max": s.get("max") if s else None, "busy": GLUT["busy"],
            "watch": bool(CFG.get("glut_watch")), "every": float(CFG.get("glut_every_min") or 2), "off_c": float(CFG.get("glut_off_c") or 40),
            "last": GLUT["last"], "img": bool(GLUT["jpg"]), "next": GLUT["next"] if CFG.get("glut_watch") else 0, "note": GLUT["note"],
            "alarm": a if a and time.time() - a["t"] < 3600 else None, "alm": glut_alm_link(), "transport": glut_transport()}


_glut_mode_state = mode_state


# wraps: mode_state (130): the page reads the fire watch with the mode
def mode_state():
    d = _glut_mode_state()
    d["glut"] = glut_state()
    return d


# ---- the live thermal picture: the outline and the maximum while the head looks at the fire spot -------------------------------
def glut_shown_box(shape, box):
    """the fire region in the shown (cropped / fitted) thermal picture, 0..1 - the same maths as ThermalCam.crop / fit"""
    H, W = shape[:2]
    g = ThermalCam.sim_geom()
    if g is not None:
        oW, oH = max(2, int(round(W / g[0]))), max(2, int(round(H / g[1])))
        ax, sx, ay, sy = -((oW - W) // 2), oW, -((oH - H) // 2), oH
    else:
        z = max(0.3, min(1.0, float(CFG["thermal_zoom"]) / 100.0))
        if z >= 0.999 and not CFG["thermal_dx"] and not CFG["thermal_dy"]:
            ax, sx, ay, sy = 0.0, W, 0.0, H
        else:
            w = W * z; h = min(float(H), w * ThermalCam.main_aspect)
            ax = max(0.0, min(W - w, W * (0.5 + float(CFG["thermal_dx"]) / 100.0) - w / 2)); sx = w
            ay = max(0.0, min(H - h, H * (0.5 - float(CFG["thermal_dy"]) / 100.0) - h / 2)); sy = h
    return [(box[0] * W - ax) / sx, (box[1] * H - ay) / sy, box[2] * W / sx, box[3] * H / sy]


_glut_overlay_base = ThermalCam.overlay


def _glut_overlay(self, frame):
    out = _glut_overlay_base(self, frame)
    try:
        fr = self.frame
        s = CFG.get("glut_spot")
        if out is frame or fr is None or not glut_taught() or not glut_at_spot(s) or fr.dtype == np.uint8:
            return out
        f = fr.reshape(fr.shape[:2])
        x0, y0, x1, y1 = glut_px(s["box"], f.shape)
        mx = float(f[y0:y1, x0:x1].max())
        b = glut_shown_box(f.shape, s["box"])
        H, W = out.shape[:2]
        p0 = (int(max(0.0, b[0]) * W), int(max(0.0, b[1]) * H))
        p1 = (int(min(1.0, b[0] + b[2]) * W) - 1, int(min(1.0, b[1] + b[3]) * H) - 1)
        if p1[0] > p0[0] and p1[1] > p0[1]:
            col = (80, 220, 80) if mx < float(CFG.get("glut_off_c") or 40) else (60, 160, 255)
            cv2.rectangle(out, p0, p1, col, 2, cv2.LINE_AA)
            _glut_put(out, glut_temp_txt(min(mx, GLUT_MAX_C), mx >= GLUT_MAX_C - 0.5), p0[0] + 4, max(20, p0[1] - 8), col, 0.6)
    except Exception:
        pass
    return out


# wraps: ThermalCam.overlay (230)
ThermalCam.overlay = _glut_overlay


# ---- web: /api/glut (GET state, POST teach / check / watch / set), /api/glut/bild.jpg ------------------------------------------
_smalltv_routes_glut = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzzw
    _smalltv_routes_glut(app, reply, body)
    from flask import Response, request

    @app.route("/api/glut", methods=["GET", "POST"])
    def api_glut():
        if request.method == "GET":
            return reply(glut_state())
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        who = servo_client(request, d)[1]
        a = d.get("action")
        if a == "teach":
            ok, msg, kw = glut_teach(who)
            return reply({"ok": ok, "msg": glut_err_tr(msg, L, **kw), "glut": glut_state()}, 200 if ok else 409)
        if a == "check":
            r = glut_check(who)
            return reply({"ok": r["kind"] != "err", "msg": glut_result_text(r, L), "glut": glut_state()}, 200 if r["kind"] != "err" else 409)
        if a == "watch":
            if d.get("on") and not glut_taught():
                return reply({"ok": False, "msg": tr("Remember the fire spot first.", L)}, 409)
            glut_set_watch(bool(d.get("on")), who)
            return reply({"ok": True, "glut": glut_state()})
        if a == "set":
            try:
                v = float(d.get("off_c"))
            except (TypeError, ValueError):
                return reply({"ok": False, "msg": "off_c: number"}, 400)
            CFG["glut_off_c"] = max(20.0, min(100.0, v)); save_settings()
            return reply({"ok": True, "glut": glut_state()})
        return reply({"ok": False, "msg": "unknown action"}, 400)

    @app.route("/api/glut/bild.jpg")
    def api_glut_bild():
        j = GLUT["jpg"]
        if not j:
            return reply({"ok": False}, 404)
        return Response(j, mimetype="image/jpeg", headers={"Cache-Control": "private, no-store"})


# ---- the page: one box below the mode (Schutz), shown with Camping / Lagerfeuer or while the watch runs ----------------------
GLUT_CSS = r"""
#glut-box{margin-top:10px;padding:10px 12px;border-radius:12px;background:rgba(255,140,40,.07);border-left:4px solid #f59a4a}
#glut-box .gl-b{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px}
#glut-box .gl-b button{padding:10px 4px;font-size:14px;min-width:0;overflow-wrap:anywhere}
#glut-box .gl-res{margin-top:8px;padding:10px 12px;border-radius:10px;font-size:17px;font-weight:700;line-height:1.3}
#glut-box .gl-res.out{background:rgba(63,207,107,.16);border:1px solid #3fcf6b}
#glut-box .gl-res.glow{background:rgba(229,72,77,.16);border:1px solid #e5484d}
#glut-box .gl-res.err{background:rgba(242,163,58,.14);border:1px solid #f2a33a;font-size:14px;font-weight:600}
#glut-box .gl-res small{display:block;font-weight:400;font-size:12px;opacity:.75;margin-top:2px}
#glut-box img{display:block;width:100%;max-width:480px;margin-top:8px;border-radius:8px;image-rendering:auto}
#glut-box .gl-note{margin-top:8px;font-size:12.5px;line-height:1.4}
#glut-box .gl-note a{color:#f59a4a}
#glut-box .gl-alarm{margin-top:8px;padding:8px 10px;border-radius:8px;background:rgba(229,72,77,.25);font-weight:700}
#glut-box .gl-th{justify-content:flex-start;gap:8px;margin-top:6px}
#glut-box .gl-th input{width:72px;flex:none}
"""
GLUT_JS = r"""
// 639zzzw «Glut-Wächter»: painted with the mode (window.__lastState.mode.glut), the buttons wait for the answer
(function () {
  const G = {key: "", busy: false};
  const tt = (k, o) => { let s = t(k); for (const n in (o || {})) s = s.replace("{" + n + "}", o[n]); return s; };
  const temp = (v, over) => over ? "400+ °C" : Math.round(v) + " °C";
  const hm = s => new Date(s * 1000).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
  function resText(r) {
    const k = "The thermal camera gives no picture: ";
    if (r.kind === "err") return "⚠ " + (r.err.startsWith(k) ? t(k) + r.err.slice(k.length) : t(r.err));
    return r.kind === "out" ? "✅ " + tt("out – at most {t}", {t: temp(r.max, r.over)}) : "⚠️ " + tt("Embers still {t} – more water, stir", {t: temp(r.max, r.over)});
  }
  async function act(o, btn) {
    if (G.busy) return; G.busy = true; if (btn) btn.disabled = true;
    const box = $("#glut-box"); const r0 = box && box.querySelector(".gl-res");
    if (r0 && o.action === "check") { r0.className = "gl-res err"; r0.textContent = "🔥 " + t("The head turns to the fire …"); }
    try { const x = await post("/api/glut", Object.assign({lang: LANG}, o));
      if (x && x.msg && o.action === "teach") toast((x.ok ? "✓ " : "⚠ ") + x.msg);
      if (x && !x.ok && x.msg && o.action === "watch") toast("⚠ " + x.msg);
      if (x && x.glut) { G.key = ""; paint(x.glut, true); } }
    catch (e) { toast("⚠ " + t("No connection to MoveEye.")); }
    G.busy = false; if (btn) btn.disabled = false;
  }
  function paint(g, force) {
    const host = $("#glut-box"); if (!host || !g) return;
    const key = JSON.stringify([g, LANG]); if (key === G.key && !force) return; G.key = key;
    host.textContent = "";
    const head = el("div", "row"); head.style.cssText = "justify-content:space-between;align-items:center";
    head.append(el("b", "", "🔥 " + t("Fire watch")), el("span", "mut", g.taught ? t("Fire spot") + " " + hm(g.spot_t) : t("not taught")));
    host.appendChild(head);
    if (!g.taught) host.appendChild(el("div", "mut", t("Point the head at the burning fire, then «Remember the fire spot».")));
    const bs = el("div", "gl-b");
    const b1 = el("button", "sec", "📍 " + t("Remember the fire spot")); b1.type = "button"; b1.onclick = () => act({action: "teach"}, b1);
    const b2 = el("button", "", "🔥 " + t("Is the fire out?")); b2.type = "button"; b2.disabled = !g.taught || g.busy; b2.onclick = () => act({action: "check"}, b2);
    bs.append(b1, b2); host.appendChild(bs);
    if (g.alarm) host.appendChild(el("div", "gl-alarm", "🚨 " + hm(g.alarm.t) + " · " + g.alarm.text));
    const r = g.last;
    if (r) { const c = el("div", "gl-res " + r.kind, resText(r)); c.appendChild(el("small", "", (r.auto ? t("Night watch") + " · " : "") + t("last check") + " " + hm(r.t))); host.appendChild(c); }
    if (g.img && (!r || r.kind !== "err")) { const im = document.createElement("img"); im.alt = t("Thermal picture of the fire spot"); im.src = "/api/glut/bild.jpg?t=" + ((r && r.t) || g.spot_t); host.appendChild(im); }
    const w = el("label", "row pr-sw"); const cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!g.watch;
    cb.onchange = () => act({action: "watch", on: cb.checked});
    w.append(el("span", "", "🌙 " + tt("Watch the fire (every {n} min)", {n: g.every})), cb); host.appendChild(w);
    if (g.watch) host.appendChild(el("div", "mut", (g.note === "alarm" ? t("waiting: an alarm comes first") : g.next ? t("next check") + " " + hm(g.next) : "")
      + (g.transport ? " · " + t("Transport mode: the head does not move") : "")));
    const th = el("div", "row gl-th"); const ni = document.createElement("input"); ni.type = "number"; ni.min = 20; ni.max = 100; ni.step = 1; ni.value = Math.round(g.off_c);
    ni.onchange = () => act({action: "set", off_c: +ni.value}); th.append(el("span", "", t("«out» below")), ni, el("span", "", "°C")); host.appendChild(th);
    const n = el("div", "mut gl-note", "ℹ️ " + t("Only the surface: embers under ash or soil can be missed. Not a substitute for putting the fire out properly.") + " "); const a = document.createElement("a"); a.href = g.alm; a.textContent = "📖 " + t("Put the fire out properly"); n.appendChild(a); host.appendChild(n);
  }
  window.glutPaint = function (s) {
    const host = $("#glut-box"), M = s && s.mode; if (!host || !M || !M.glut) return;
    const show = M.id === "camping" || M.id === "fire" || M.glut.watch || !!M.glut.alarm;
    host.hidden = !show; if (show) paint(M.glut, false);
  };
})();
"""
GLUT_JS_KEYS = ("No connection to MoveEye.",)


def glut_page_hooks(page):
    for a, b in (('<div id="mode-tv"></div>', '<div id="mode-tv"></div><div id="glut-box" hidden></div>'),
                 ("tvPaint(s.tv); discoPaint(s.disco);", "tvPaint(s.tv); discoPaint(s.disco); if (window.glutPaint) glutPaint(s);")):
        if a in page and b not in page:
            page = page.replace(a, b, 1)
    if 'id="glut-css"' not in page:
        de = {k: v[0] for k, v in _HX_GLUT.items()}
        de.update({k: DE.get(k, k) for k in GLUT_JS_KEYS if DE.get(k)})
        page = page.replace("</body>", "<style id=\"glut-css\">" + GLUT_CSS + "</style><script>\ntry { Object.assign(I18N.de, "
                            + json.dumps(de, ensure_ascii=False) + "); } catch (e) {}\n" + GLUT_JS + "</script></body>", 1)
    return page


# ---- the Pi window: buttons and the result text in «Camping / protection» -------------------------------------------------------
_glut_tk_build_section_base = App._build_section


def _glut_tk_build_section(self, sec, sbody, settings_parent=None):
    _glut_tk_build_section_base(self, sec, sbody, settings_parent)
    if sec != "Camping / protection":
        return
    try:
        ttk.Label(sbody, text="🔥 " + tr("Fire watch")).pack(anchor="w", pady=(10, 2))
        bf = ttk.Frame(sbody); bf.pack(fill="x")
        lab = ttk.Label(sbody, text="", wraplength=380, justify="left"); lab.pack(anchor="w", pady=(4, 0))
        wv = tk.BooleanVar(value=bool(CFG.get("glut_watch")))

        def run(f):
            threading.Thread(target=f, daemon=True, name="glut-tk").start()

        msg = {"t": 0.0, "txt": ""}                          # the answer of «Remember» (the threads only write this, Tk paints it)

        def teach():
            ok, m_, kw = glut_teach(tr("Window"))
            msg.update(t=time.time(), txt=("✓ " if ok else "⚠ ") + glut_err_tr(m_, **kw))

        def check():
            msg.update(t=0.0)
            glut_check(tr("Window"))

        def watch():
            if wv.get() and not glut_taught():
                wv.set(False); msg.update(t=time.time(), txt="⚠ " + tr("Remember the fire spot first.")); return
            glut_set_watch(wv.get(), tr("Window"))
        ttk.Button(bf, text="📍 " + tr("Remember the fire spot"), command=lambda: run(teach)).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(bf, text="🔥 " + tr("Is the fire out?"), command=lambda: run(check)).pack(side="left", expand=True, fill="x")
        ttk.Checkbutton(sbody, text="🌙 " + trf("Watch the fire (every {n} min)", n="%g" % float(CFG.get("glut_every_min") or 2)), variable=wv,
                        command=watch).pack(anchor="w", pady=(4, 0))
        ttk.Label(sbody, text="ℹ️ " + tr("Only the surface: embers under ash or soil can be missed. Not a substitute for putting the fire out properly."), style="Mut.TLabel", wraplength=380, justify="left").pack(anchor="w", pady=(4, 0))

        def paint():
            try:
                if not lab.winfo_exists():
                    return
                a = GLUT["alarm"]
                txt = ("🔥 " + tr("The head turns to the fire …")) if GLUT["busy"] else glut_result_text(GLUT["last"]) or (
                    "" if glut_taught() else tr("Point the head at the burning fire, then «Remember the fire spot»."))
                if time.time() - msg["t"] < 20:
                    txt = msg["txt"]
                if a and time.time() - a["t"] < 3600:
                    txt = "🚨 " + a["text"] + ("\n" + txt if txt else "")
                lab.config(text=txt)
                lab.after(1500, paint)
            except Exception:
                pass
        paint()
    except Exception as e:
        log_event("sys", f"Window: fire watch: {e}"[:160])


# wraps: App._build_section (570)
App._build_section = _glut_tk_build_section


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_GLUT = {
    "Fire watch": ("Glut-Wächter", "Gardien des braises", "Guardiano delle braci", "Guardian da la brasa"),
    "Remember the fire spot": ("Feuerstelle merken", "Mémoriser le foyer", "Memorizza il focolare", "Memorisar il fieu"),
    "Is the fire out?": ("Ist das Feuer aus?", "Le feu est-il éteint ?", "Il fuoco è spento?", "È il fieu stizzà?"),
    "out – at most {t}": ("aus – höchstens {t}", "éteint – au plus {t}", "spento – al massimo {t}", "stizzà – maximalmain {t}"),
    "Embers still {t} – more water, stir": ("Glut noch {t} – mehr Wasser, umrühren", "Braises encore à {t} – plus d’eau, remuer",
                                            "Braci ancora a {t} – più acqua, mescolare", "Brasa anc {t} – dapli aua, revolver"),
    "Only the surface: embers under ash or soil can be missed. Not a substitute for putting the fire out properly.": ("Nur die Oberfläche: Glut unter Asche oder Erde kann übersehen werden. Kein Ersatz für richtiges Löschen.",
                  "Seulement la surface : des braises sous la cendre ou la terre peuvent échapper. Ne remplace pas une extinction correcte.",
                  "Solo la superficie: braci sotto la cenere o la terra possono sfuggire. Non sostituisce uno spegnimento corretto.",
                  "Mo la surfatscha: brasa sut tschendra u terra po vegnir survesida. Nagin remplazzament per stizzar endretg."),
    "Put the fire out properly": ("Feuer richtig löschen", "Bien éteindre un feu", "Spegnere bene il fuoco", "Stizzar endretg il fieu"),
    "Fire spot": ("Feuerstelle", "Foyer", "Focolare", "Fieu"),
    "not taught": ("nicht gemerkt", "pas mémorisé", "non memorizzato", "betg memorisà"),
    "Point the head at the burning fire, then «Remember the fire spot».": (
        "Kopf auf das brennende Feuer richten, dann «Feuerstelle merken».", "Oriente la tête vers le feu qui brûle, puis « Mémoriser le foyer ».",
        "Punta la testa sul fuoco acceso, poi «Memorizza il focolare».", "Drizza il chau sin il fieu che arda, lura «Memorisar il fieu»."),
    "Fire spot remembered (hottest {t}).": ("Feuerstelle gemerkt (heissester Punkt {t}).", "Foyer mémorisé (point le plus chaud {t}).",
                                            "Focolare memorizzato (punto più caldo {t}).", "Fieu memorisà (punct il pli chaud {t})."),
    "No fire in the thermal picture (hottest {t}) - remember the spot while the fire burns or the embers are hot.": (
        "Kein Feuer im Wärmebild (heissester Punkt {t}) – die Feuerstelle merken, solange es brennt oder die Glut heiss ist.",
        "Pas de feu dans l’image thermique (point le plus chaud {t}) – mémorise le foyer pendant que le feu brûle ou que les braises sont chaudes.",
        "Nessun fuoco nell’immagine termica (punto più caldo {t}) – memorizza il focolare mentre il fuoco arde o le braci sono calde.",
        "Nagin fieu en il maletg termic (punct il pli chaud {t}) – memorisescha il fieu durant ch’el arda u la brasa è chauda."),
    "Remember the fire spot first.": ("Zuerst die Feuerstelle merken.", "Mémorise d’abord le foyer.", "Prima memorizza il focolare.",
                                      "L’emprim memorisar il fieu."),
    "A check is already running.": ("Eine Prüfung läuft schon.", "Une vérification est déjà en cours.", "Un controllo è già in corso.",
                                    "Ina controlla è gia en lavur."),
    "No thermal camera chosen (Settings → Thermal camera).": ("Kein Wärmebild gewählt (Einstellungen → Wärmebild).",
                                                             "Aucune caméra thermique choisie (Réglages → Caméra thermique).",
                                                             "Nessuna termocamera scelta (Impostazioni → Termocamera).",
                                                             "Nagina camera termica tschernida (Parameters → Camera termica)."),
    "The thermal camera gives no picture: ": ("Das Wärmebild liefert kein Bild: ", "La caméra thermique ne donne pas d’image : ",
                                              "La termocamera non dà immagini: ", "La camera termica na dat nagin maletg: "),
    "This thermal source gives no temperatures (only colours) - the fire watch needs the Thermal-90.": (
        "Diese Wärmebild-Quelle liefert keine Temperaturen (nur Farben) – der Glut-Wächter braucht den Thermal-90.",
        "Cette source thermique ne donne pas de températures (seulement des couleurs) – le gardien des braises a besoin du Thermal-90.",
        "Questa sorgente termica non dà temperature (solo colori) – il guardiano delle braci ha bisogno del Thermal-90.",
        "Questa funtauna termica na dat naginas temperaturas (mo colurs) – il guardian da la brasa basegna il Thermal-90."),
    "Transport mode: the head does not move - it is not looking at the fire.": (
        "Transportmodus: der Kopf bewegt sich nicht – er schaut nicht aufs Feuer.", "Mode transport : la tête ne bouge pas – elle ne regarde pas le feu.",
        "Modalità trasporto: la testa non si muove – non guarda il fuoco.", "Modus da transport: il chau na sa mova betg – el na guarda betg sin il fieu."),
    "Transport mode: the head does not move": ("Transportmodus: der Kopf bewegt sich nicht", "Mode transport : la tête ne bouge pas",
                                               "Modalità trasporto: la testa non si muove", "Modus da transport: il chau na sa mova betg"),
    "An alarm comes first - try again in a moment.": ("Ein Alarm geht vor – gleich nochmals versuchen.", "Une alarme passe d’abord – réessaie dans un instant.",
                                                     "Un allarme ha la precedenza – riprova tra poco.", "In alarm ha la precedenza – emprova pli tard anc ina giada."),
    "Emergency stop or servo fault - the head does not move.": ("Not-Aus oder Servo-Störung – der Kopf bewegt sich nicht.",
                                                               "Arrêt d’urgence ou panne de servo – la tête ne bouge pas.",
                                                               "Arresto d’emergenza o guasto del servo – la testa non si muove.",
                                                               "Stop d’urgenza u disturbi dal servo – il chau na sa mova betg."),
    "The head is busy (quick look) - try again in a moment.": (
        "Der Kopf ist beschäftigt (kurzer Blick) – gleich nochmals versuchen.", "La tête est occupée (coup d’œil) – réessaie dans un instant.",
        "La testa è occupata (occhiata) – riprova tra poco.", "Il chau è occupà (in sguard) – emprova pli tard anc ina giada."),
    "The head was interrupted.": ("Der Kopf wurde unterbrochen.", "La tête a été interrompue.", "La testa è stata interrotta.", "Il chau è vegnì interrut."),
    "The head turns to the fire …": ("Der Kopf dreht zum Feuer …", "La tête tourne vers le feu …", "La testa gira verso il fuoco …", "Il chau sa volva vers il fieu …"),
    "Watch the fire (every {n} min)": ("Feuer überwachen (alle {n} min)", "Surveiller le feu (toutes les {n} min)", "Sorvegliare il fuoco (ogni {n} min)",
                                       "Survegliar il fieu (mintga {n} min)"),
    "Night watch": ("Nachtwache", "Garde de nuit", "Guardia notturna", "Guardia da notg"),
    "last check": ("letzte Prüfung", "dernière vérification", "ultimo controllo", "ultima controlla"),
    "next check": ("nächste Prüfung", "prochaine vérification", "prossimo controllo", "proxima controlla"),
    "waiting: an alarm comes first": ("wartet: ein Alarm geht vor", "en attente : une alarme passe d’abord", "in attesa: un allarme ha la precedenza",
                                      "spetga: in alarm ha la precedenza"),
    "«out» below": ("«aus» unter", "« éteint » sous", "«spento» sotto", "«stizzà» sut"),
    "Thermal picture of the fire spot": ("Wärmebild der Feuerstelle", "Image thermique du foyer", "Immagine termica del focolare", "Maletg termic dal fieu"),
    "The fire heats up again: {t} (was {b})": ("Das Feuer wird wieder heiss: {t} (vorher {b})", "Le feu se réchauffe : {t} (avant {b})",
                                               "Il fuoco si riscalda di nuovo: {t} (prima {b})", "Il fieu vegn puspè chaud: {t} (avant {b})"),
    "New hot spot next to the fire: {t} - spark or creeping fire?": (
        "Neuer heisser Punkt neben dem Feuer: {t} – Funke oder kriechendes Feuer?", "Nouveau point chaud près du feu : {t} – étincelle ou feu rampant ?",
        "Nuovo punto caldo vicino al fuoco: {t} – scintilla o fuoco strisciante?", "Nov punct chaud sper il fieu: {t} – sbrinzla u fieu che sa derasa?"),
}
for _k, _v in _HX_GLUT.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
WEB_PAGE = glut_page_hooks(WEB_PAGE)


# ---- the manual: one paragraph at the end of «Alarm & Camping» --------------------------------------------------------------------
HELP_GLUT = {
    "de": '<p id="glut-help"><b>🔥 Glut-Wächter (Schutz → Modus, bei Camping / Lagerfeuer; auch im Pi-Fenster):</b> Kopf von Hand auf das brennende Feuer richten und «Feuerstelle merken» – MoveEye merkt sich die Kopfstellung und den heissen Bereich im Wärmebild. «Ist das Feuer aus?» dreht den Kopf hin, misst ein paar Wärmebilder und zeigt «✅ aus – höchstens 38 °C» (unter der Schwelle, ab Werk 40 °C) oder «⚠️ Glut noch 180 °C – mehr Wasser, umrühren», mit Wärmebild und Umriss; im Live-Wärmebild steht derselbe Umriss mit dem Höchstwert, solange der Kopf aufs Feuer schaut. «Feuer überwachen» prüft nachts alle 2 Minuten und warnt mit einem leisen, steigenden Ton und einem Push, wenn die Feuerstelle deutlich wieder heiss wird oder daneben ein neuer heisser Punkt auftaucht (Funke, kriechendes Feuer). Im Transportmodus fährt der Kopf nie; ein Alarm wegen Personen geht vor, danach geht es zurück zum Feuer. <b>Ehrlich:</b> das Wärmebild sieht nur die Oberfläche – Glut unter Asche oder Erde kann fehlen, kleine Glut weit weg wird mit der Umgebung gemittelt (Thermal-90: −40 bis +400 °C, ±1.5 °C nur zwischen 10 und 70 °C). Kein Ersatz für richtiges Löschen (Almanach «Feuer richtig löschen»).</p>',
    "en": '<p id="glut-help"><b>🔥 Fire watch (Protection → Mode, with Camping / Campfire; also in the Pi window):</b> point the head at the burning fire by hand and tap «Remember the fire spot» – MoveEye keeps the head position and the hot region of the thermal picture. «Is the fire out?» turns the head there, measures a few thermal pictures and shows «✅ out – at most 38 °C» (below the threshold, 40 °C from the factory) or «⚠️ Embers still 180 °C – more water, stir», with the thermal picture and the outline; the live thermal picture shows the same outline with the maximum while the head looks at the fire. «Watch the fire» checks every 2 minutes at night and warns with a soft rising tone and a push when the fire spot clearly heats up again or a new hot spot appears next to it (spark, creeping fire). In the transport mode the head never moves; an alarm on persons comes first, then it goes back to the fire. <b>Honestly:</b> the thermal picture only sees the surface – embers under ash or soil can be missed, small embers far away are averaged with the surroundings (Thermal-90: −40 to +400 °C, ±1.5 °C only between 10 and 70 °C). Not a substitute for putting the fire out properly (almanac «Feuer richtig löschen»).</p>',
    "fr": '<p id="glut-help"><b>🔥 Gardien des braises (Protection → Mode, avec Camping / Feu de camp ; aussi dans la fenêtre du Pi) :</b> oriente la tête vers le feu qui brûle et touche « Mémoriser le foyer » – MoveEye garde la position de la tête et la zone chaude de l’image thermique. « Le feu est-il éteint ? » tourne la tête vers le foyer, mesure quelques images thermiques et affiche « ✅ éteint – au plus 38 °C » (sous le seuil, 40 °C d’usine) ou « ⚠️ Braises encore à 180 °C – plus d’eau, remuer », avec l’image thermique et le contour. « Surveiller le feu » vérifie la nuit toutes les 2 minutes et avertit par un son doux et montant et un push si le foyer se réchauffe nettement ou si un nouveau point chaud apparaît à côté. En mode transport, la tête ne bouge jamais ; une alarme personnes passe d’abord. <b>Honnêtement :</b> l’image thermique ne voit que la surface – des braises sous la cendre ou la terre peuvent échapper (Thermal-90 : −40 à +400 °C, ±1,5 °C seulement entre 10 et 70 °C). Ne remplace pas une extinction correcte (almanach « Feuer richtig löschen »).</p>',
    "it": '<p id="glut-help"><b>🔥 Guardiano delle braci (Protezione → Modalità, con Campeggio / Fuoco; anche nella finestra del Pi):</b> punta la testa sul fuoco acceso e tocca «Memorizza il focolare» – MoveEye memorizza la posizione della testa e la zona calda dell’immagine termica. «Il fuoco è spento?» gira la testa verso il focolare, misura alcune immagini termiche e mostra «✅ spento – al massimo 38 °C» (sotto la soglia, 40 °C di fabbrica) o «⚠️ Braci ancora a 180 °C – più acqua, mescolare», con l’immagine termica e il contorno. «Sorvegliare il fuoco» controlla di notte ogni 2 minuti e avvisa con un suono dolce e crescente e un push se il focolare si riscalda chiaramente o se accanto appare un nuovo punto caldo. In modalità trasporto la testa non si muove mai; un allarme persone ha la precedenza. <b>Onestamente:</b> l’immagine termica vede solo la superficie – braci sotto la cenere o la terra possono sfuggire (Thermal-90: da −40 a +400 °C, ±1,5 °C solo tra 10 e 70 °C). Non sostituisce uno spegnimento corretto (almanacco «Feuer richtig löschen»).</p>',
    "rm": '<p id="glut-help"><b>🔥 Guardian da la brasa (Protecziun → Modus, cun Camping / Fieu; er en la fanestra dal Pi):</b> drizza il chau sin il fieu che arda e tutga «Memorisar il fieu» – MoveEye memorisescha la posiziun dal chau e la zona chauda dal maletg termic. «È il fieu stizzà?» volva il chau vers il fieu, mesira intgins maletgs termics e mussa «✅ stizzà – maximalmain 38 °C» (sut la limita, 40 °C da fabrica) u «⚠️ Brasa anc 180 °C – dapli aua, revolver», cun il maletg termic ed il contur. «Survegliar il fieu» controllescha la notg mintga 2 minutas ed avertescha cun in tun lev che crescha ed in push, sch’il fieu vegn puspè cleramain chaud u sch’i cumpara sper el in nov punct chaud. En il modus da transport na sa mova il chau mai; in alarm da persunas ha la precedenza. <b>Onestamain:</b> il maletg termic vesa mo la surfatscha – brasa sut tschendra u terra po vegnir survesida (Thermal-90: −40 fin +400 °C, ±1.5 °C mo tranter 10 e 70 °C). Nagin remplazzament per stizzar endretg (almanac «Feuer richtig löschen»).</p>',
}


def _help_glut(doc, lang):
    i = doc.find('<section id="alarm"')
    if i < 0 or 'id="glut-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_GLUT[lang] + doc[j:] if j >= 0 else doc


_hp_en_glut = HELP_PAGE.find('<div lang="en">')
if _hp_en_glut > 0:
    HELP_PAGE = _help_glut(HELP_PAGE[:_hp_en_glut], "de") + _help_glut(HELP_PAGE[_hp_en_glut:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_glut(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def glut_selftest():
    f = np.full((62, 80), 15.0, np.float32)
    f[30:34, 40:45] = 180.0
    box, mx = glut_find(f)
    assert box and mx == 180.0 and box[0] < 40 / 80 < box[0] + box[2] and box[1] < 30 / 62 < box[1] + box[3], box
    f2 = f.copy(); f2[30:34, 40:45] = 35.0; f2[5, 5] = 90.0
    r = glut_measure([f2, f2], box, 60.0)
    assert r["max"] == 35.0 and len(r["new"]) == 1 and r["new"][0][2] == 90.0, r
    assert glut_measure([f2], box, 60.0)["new"] and not glut_measure([f2, f], box, 60.0)["new"]   # in 2 of the pictures
    assert glut_find(np.full((62, 80), 30.0, np.float32))[0] is None
    assert glut_shown_box((62, 80), [0.25, 0.25, 0.5, 0.5]) == [0.25, 0.25, 0.5, 0.5] or ThermalCam.sim_geom() or CFG["thermal_zoom"] != 100
    assert ThermalCam.overlay is _glut_overlay and ThermalCam.wanted is _glut_wanted and "/api/glut" in PERM_POST["arm"]
    assert 'id="glut-box"' in WEB_PAGE and "glutPaint(s)" in WEB_PAGE and HELP_PAGE.count('id="glut-help"') == 2
    # our wrapper is the outermost one - or the saved predecessor of a later one (and 557 wraps late, _TALIGN_TK; 3.95.0)
    assert not GUI_OK or _glut_tk_build_section in (App._build_section, (globals().get("_TALIGN_TK") or {}).get("before"),
                                    *[v for k, v in globals().items() if k.startswith("_") and k.endswith(("_build_section_before", "_build_section_base"))]), "window buttons"
    for k, v in _HX_GLUT.items():
        assert len(v) == 4 and all(v) and "ß" not in "".join(v), k
    assert tr("Is the fire out?", "de") == "Ist das Feuer aus?" and "{t}" in tr("out – at most {t}", "rm")
    return "teach region, measure, new hot spot in 2 pictures, page hooks, texts"


SELFTEST_EXTRA.append(("Fire watch «🔥 Glut-Wächter» (639zzzw)", glut_selftest))
