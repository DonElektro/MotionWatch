#@ MoveEye – Teil 639zy: Paket «Fehlalarme und Pushes» – doppelte Bestätigung messbar (ab Werk in einer Zeile), Fehlalarm-Stellen lernen (3 × in 7 Tagen -> eine Frage «künftig ignorieren?»), Windschutz für Pflanzen-Bereiche, Pushes bündeln («+N weitere in M Min.» mit Bildstreifen), Zonen-Name im Push, kurzer Clip, «Bilder bleiben zu Hause». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket des Besitzers «Fehlalarme und Pushes» (07.11.2026). Alles in diesem Teil, nur Hüllen um vorhandene Funktionen
# (alarm_gate 066/639zw, Notifier.person / _dispatch 060, push_short / push_long 635b, alx_label 066, rec_set_false 430,
# sx_push_jpg 578/579a, email_send 060, WeatherAnalyzer.wind 190, alarm_ctx_note 066) - keine Änderung am Zonen-Editor
# und an den Klassenlisten der Erkennung.
#  1  Doppelte Bestätigung (alarm_confirm2, 066) messbar: der Erkennungstest kennt «--variante bestaetigung2 / _aus»
#     (werkzeuge/erkennungstest), das Dauerrechnen am HP misst main zusätzlich mit der Variante und schreibt varianten.md
#     (Erkennung und Pushes/h nebeneinander). Ab Werk: ALARM_CONFIRM2_WERK unten (eine Zeile). Gilt nur für neue Geräte und
#     Werkseinstellungen - gespeicherte Einstellungen behalten ihren Wert (für alle Geräte bräuchte es eine Umstellung).
#  2  Fehlalarm-Stellen: «Fehlalarm» (Push-Knopf, Aufnahmen) bzw. «Was war das? → Nichts» merkt die Stelle (Fusspunkt des
#     grössten Rahmens, grobes Raster 6 × 4 pro Kamera und Kopf-Richtung). 3 × dieselbe Stelle in 7 Tagen -> EINE Push-Frage
#     «Hier kommen oft Fehlalarme – künftig ignorieren?» mit «Ja, ignorieren» (Ignorier-Zone nur für Personen auf diesem Feld,
#     mit Kopf: bleibt am Ort) / «Nein» (30 Tage Ruhe). Nie von selbst ignoriert. Adressen /na/fs/<schlüssel>/yes|no (wie die
#     Push-Knöpfe: zufälliger Schlüssel, 3 Tage gültig) und /api/fehlalarm_stellen (Hauptseite: Karte mit derselben Frage).
#     Nicht im Simulator-Betrieb (eine Zone aus der Simulation darf nicht in den echten Betrieb).
#  3  Windschutz (wind_guard, ab Werk an, vorsichtig): Pflanzen-Bereiche = Felder (8 × 6), in denen sich in der letzten
#     Minute fast immer etwas bewegt (Blätter flackern, ohne Personen-Rahmen; aus WeatherAnalyzer.wind). Bei starkem Wind
#     (gemessen / Simulator: STATE storm Böen ≥ wind_guard_kmh, sonst Bild «strong / storm») braucht eine Bewegungs-Person
#     dort die KI oder das Wärmebild - oder sie bleibt 6 s länger, dann gilt sie doch. Protokoll «Wind protection: …»,
#     Zähler /api/fehlalarm_stellen (wind).
#  4  Pushes bündeln (push_bundle, ab Werk an): in der Pause zwischen Alarmen wird nichts verworfen - die nächste Meldung sagt
#     «+N weitere in M Min.» und hat unten einen Bildstreifen (bis 4 kleine Bilder) im Bild (ntfy, Telegram, Pushover, E-Mail).
#     push_bundle_after (ab Werk aus): nach der Pause die Sammlung auch ohne neuen Alarm schicken.
#  5  Zonen-Name im Push (push_zone_name, ab Werk an): «Person bei «Eingangstür»» statt «Person erkannt» (Zonen der
#     Hauptkamera mit eigenem Namen, Fusspunkt darin; automatische Namen «Zone 3» nicht).
#  6  Kurzer Clip (push_clip, ab Werk aus): 3-5 s um den Alarm (60 % davor, 40 % danach), klein (320 px, 6 Bilder/s, kleiner
#     wenn nötig), höchstens push_clip_kb; ntfy als GIF-Anhang, Telegram als Video (MP4 über ffmpeg, sonst OpenCV) - als zweite
#     Meldung kurz nach dem Bild. Nicht im Test-Postfach, nicht bei «ohne Bild».
#  7  «Bilder bleiben zu Hause» (push_home_pics, ab Werk AUS - Entscheid des Besitzers offen): Meldungen nur mit Text und dem
#     Link /pb/<id> auf MoveEye (Bild, Clip; hinter dem Web-Passwort, über die Adresse der Seite = zu Hause und über den
#     Fernzugang); auch die E-Mail ohne Anhang. Das Test-Postfach und die Liste «Nachrichten» behalten das Bild (sie sind auf dem Pi).
# Selbsttest: fp_selftest (Stellen lernen, Bündel-Text, Zonen-Name, Windschutz, Clip-Grenze, Link zu Hause).
# ----------------------------------------------------------------------------
ALARM_CONFIRM2_WERK = False          # 1: True = doppelte Bestätigung ab Werk an (Besitzer entscheidet nach den HP-Messungen)
for _k, _v in {"alarm_confirm2": ALARM_CONFIRM2_WERK, "fp_spot_learn": True, "wind_guard": True, "wind_guard_kmh": 40.0,
               "push_bundle": True, "push_bundle_after": False, "push_zone_name": True, "push_clip": False, "push_clip_s": 4.0,
               "push_clip_kb": 800.0, "push_home_pics": False}.items():
    if _k == "alarm_confirm2":
        CFG[_k] = _v; DEFAULTS[_k] = _v; FACTORY_CFG[_k] = _v          # before load_settings: the saved value still wins
        continue
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)   # 636 took its copy before this part

FP_GRID = (6, 4)                     # 2: coarse grid of the false-alarm spots (columns, rows)
FP_NEED, FP_DAYS, FP_NO_DAYS, FP_TOK_DAYS = 3, 7, 30, 3
WG_GRID = (8, 6)                     # 3: grid of the plant areas
WG_TAU_S, WG_VEG, WG_HOLD_S = 60.0, 0.5, 6.0
CLIP_FPS, CLIP_KEEP_S = 6.0, 7.0
PB_KEEP, PB_DAYS = 200, 14
_FP_LOCK = threading.Lock()
FPS = {"file": "", "data": None, "busy": False}
WG = {"occ": None, "t": 0.0, "seen": {}, "held": 0, "passed": 0, "log_t": 0.0, "why": "", "since": time.time()}
FPB = {"lock": threading.Lock(), "items": [], "n": 0, "first": 0.0}
CLIP = {"buf": deque(), "last": 0.0, "state": {}}
PB_RE = re.compile(r"^[0-9a-f]{16}$")
_FP_TOK_RE = re.compile(r"^[A-Za-z0-9_\-]{20,40}$")


# ---- 2: false-alarm spots -------------------------------------------------------------------------------------------------
def fp_file():
    return FPS["file"] or os.path.join(DATA_DIR, "fehlalarm_stellen.json")


def fp_load():
    if FPS["data"] is not None and FPS.get("for") == fp_file():
        return FPS["data"]
    d = None
    try:
        with open(fp_file(), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = None
    if not isinstance(d, dict):
        d = {}
    d.setdefault("v", 1)
    d["notes"] = [n for n in d.get("notes") or [] if isinstance(n, dict) and isinstance(n.get("key"), str)][-400:]
    d["asked"] = {k: v for k, v in (d.get("asked") or {}).items() if isinstance(v, dict)}
    FPS["data"], FPS["for"] = d, fp_file()
    return d


def fp_save():
    d = FPS["data"]
    if d is None:
        return
    try:
        p = fp_file()
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
        with open(p + ".tmp", "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(p + ".tmp", p)
    except OSError as e:
        log_event("sys", f"False alarm spots not saved: {e}"[:160])


def fp_cell(fx, fy):
    c = max(0, min(FP_GRID[0] - 1, int(float(fx) * FP_GRID[0])))
    r = max(0, min(FP_GRID[1] - 1, int(float(fy) * FP_GRID[1])))
    return c, r


def fp_feet(boxes):
    """the feet point (0..1) of the biggest box [x, y, w, h] (normalised) - the point the zones use (030 zone_box_ok)"""
    bs = [b for b in boxes or [] if isinstance(b, (list, tuple)) and len(b) >= 4]
    if not bs:
        return None
    b = max(bs, key=lambda b_: float(b_[2]) * float(b_[3]))
    return (float(b[0]) + float(b[2]) / 2.0, float(b[1]) + float(b[3]) * 0.85)


def fp_key(x):
    """camera | head direction (5 % steps, «-» without servos) | cell"""
    pt = fp_feet(x.get("boxes"))
    if pt is None:
        return None, None
    c, r = fp_cell(*pt)
    pb = "%d/%d" % (round(float(x.get("pan") or 50) / 5.0), round(float(x.get("tilt") or 50) / 5.0)) if x.get("srv") else "-"
    return "%s|%s|%d,%d" % (str(x.get("src") or "?")[:40], pb, c, r), pt


def fp_spot_note(x, now=None):
    """a false alarm with its picture context (alarm_labels json) -> note the spot; may ask once. Returns the key or None."""
    if not CFG.get("fp_spot_learn", True) or not isinstance(x, dict) or x.get("sim") or CFG.get("sim_on"):
        return None
    key, pt = fp_key(x)
    if key is None:
        return None
    now = time.time() if now is None else now
    sid = str(x.get("stamp") or x.get("id") or "")
    with _FP_LOCK:
        d = fp_load()
        if any(n.get("id") == sid for n in d["notes"]):
            return key                                   # the same alarm twice (push button and recording list)
        d["notes"].append({"id": sid, "lid": str(x.get("id") or sid), "t": float(x.get("t") or now), "key": key,
                           "pt": [round(pt[0], 3), round(pt[1], 3)], "pan": x.get("pan"), "tilt": x.get("tilt"),
                           "srv": bool(x.get("srv")), "src": str(x.get("src") or "")[:40]})
        d["notes"] = [n for n in d["notes"] if now - float(n.get("t") or 0) < 30 * 86400][-400:]
        fp_save()
    log_event("person", f"False alarm spot noted ({key.rsplit('|', 1)[-1]})")
    fp_spot_check(key, now)
    return key


def fp_spot_forget(sid):
    with _FP_LOCK:
        d = fp_load()
        n0 = len(d["notes"])
        d["notes"] = [n for n in d["notes"] if n.get("id") != sid and n.get("lid") != sid]
        if len(d["notes"]) != n0:
            fp_save()


def fp_spot_due(key, now):
    """the notes of this spot in the last 7 days, when a question is due (else None)"""
    d = fp_load()
    ns = [n for n in d["notes"] if n.get("key") == key and now - float(n.get("t") or 0) < FP_DAYS * 86400]
    if len(ns) < FP_NEED:
        return None
    a = d["asked"].get(key)
    if a and (a.get("ans") == "yes" or now - float(a.get("t") or 0) < FP_NO_DAYS * 86400):
        return None                                      # asked already: once (after «No» or no answer: 30 days quiet)
    return ns


def fp_spot_check(key, now):
    with _FP_LOCK:
        ns = fp_spot_due(key, now)
        if not ns:
            return None
        last = max(ns, key=lambda n: float(n.get("t") or 0))
        c, r = (int(v) for v in key.rsplit("|", 1)[-1].split(","))
        tok = secrets.token_urlsafe(18)
        e = {"t": now, "tok": tok, "ans": "", "n": len(ns), "lid": last.get("lid"), "cell": [c, r], "pan": last.get("pan"),
             "tilt": last.get("tilt"), "srv": bool(last.get("srv")), "src": last.get("src", "")}
        fp_load()["asked"][key] = e
        fp_save()
    log_event("person", f"{len(ns)} false alarms at the same spot in {FP_DAYS} days - asking once whether to ignore it")
    try:
        fp_spot_ask(key, e)
    except Exception as ex:
        log_event("sys", f"False alarm spot question: {ex}"[:160])
    return tok


def fp_by_tok(tok):
    if not isinstance(tok, str) or not _FP_TOK_RE.match(tok):
        return None, None
    for k, e in fp_load()["asked"].items():
        if e.get("tok") and secrets.compare_digest(str(e["tok"]), tok):
            return k, e
    return None, None


def fp_open(e, now=None):
    now = time.time() if now is None else now
    return bool(e) and not e.get("ans") and now - float(e.get("t") or 0) < FP_TOK_DAYS * 86400


def fp_cell_points(cell):
    c, r = cell
    x0, x1 = c / float(FP_GRID[0]), (c + 1) / float(FP_GRID[0])
    y0, y1 = r / float(FP_GRID[1]), (r + 1) / float(FP_GRID[1])
    return [[round(x0, 4), round(y0, 4)], [round(x1, 4), round(y0, 4)], [round(x1, 4), round(y1, 4)], [round(x0, 4), round(y1, 4)]]


def fp_spot_answer(tok, act, who="push"):
    """(ok, text in the current language) - «yes» adds the ignore zone, «no» leaves it (30 days quiet)"""
    if act not in ("yes", "no"):
        return False, tr("This question is no longer open.")
    with _FP_LOCK:
        key, e = fp_by_tok(tok)
        if not fp_open(e):
            return False, tr("This question is no longer open.")
        if act == "no":
            e["ans"], e["ans_t"] = "no", int(time.time())
            fp_save()
            log_event("person", f"False alarm spot {key.rsplit('|', 1)[-1]}: not ignored ({who})")
            return True, tr("OK - this spot is not ignored. MoveEye does not ask again for 30 days.")
        if e.get("src") and str(STATE.get("source_label") or "")[:40] != e["src"]:
            return False, tr("The camera has changed since - no zone added.")
        if len(ZONES) >= MAX_ZONES:
            return False, tr("Too many zones - delete one under Zones first.")
        pts = fp_cell_points(e["cell"])
        n = 1 + sum(1 for z in ZONES if str(z.get("name", "")).startswith(tr("False alarm spot")))
        z = {"name": ("%s %d" % (tr("False alarm spot"), n))[:40], "mode": "ignore", "kinds": "person", "points": pts}
        if e.get("srv"):
            try:                                         # the head turns: the zone stays on its place (directions, 030)
                z["anchor"] = True
                z["ang"] = sleep_to_ang(pts, float(e.get("pan") or 50), float(e.get("tilt") or 50))
            except Exception:
                z.pop("anchor", None); z.pop("ang", None)
        ok, err = zones_set([dict(z_) for z_ in ZONES] + [z])
        if not ok:
            return False, tr_err(err)
        e["ans"], e["ans_t"] = "yes", int(time.time())
        fp_save()
    log_event("person", f"False alarm spot {key.rsplit('|', 1)[-1]}: ignore zone «{z['name']}» added ({who})")
    return True, tr("Done - an ignore zone was added here. You can change it under Zones.")


def fp_spot_pic(e):
    """the latest alarm picture of the spot with the field marked (JPEG) or None"""
    try:
        p = alx_label_path(str(e.get("lid") or ""), ".jpg")
        img = cv2.imread(p) if p and os.path.exists(p) else None
        if img is None:
            return None
        h, w = img.shape[:2]
        pts = fp_cell_points(e["cell"])
        x0, y0 = int(pts[0][0] * w), int(pts[0][1] * h)
        x1, y1 = int(pts[2][0] * w) - 1, int(pts[2][1] * h) - 1
        ov = img.copy()
        cv2.rectangle(ov, (x0, y0), (x1, y1), (0, 200, 255), -1)
        img = cv2.addWeighted(ov, 0.25, img, 0.75, 0)
        cv2.rectangle(img, (x0, y0), (x1, y1), (0, 200, 255), 3)
        if w > 800:
            img = cv2.resize(img, (800, int(h * 800 / w)), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
        return buf.tobytes() if ok else None
    except Exception:
        return None


def fp_spot_ask(key, e):
    """the ONE push question (info, with the buttons «Yes, ignore» / «No»); without push only the card on the main page"""
    w = WATCH_REF.get("w")
    if w is None or not (Notifier.configured() and CFG.get("notify_on")):
        return False
    base = alx_base()
    p = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"),
         "text": tr("False alarms often come from here – ignore this spot from now on?"),
         "info_title": "{name}: " + tr("False alarm spot"), "snapshot": None, "rain": False, "wind": "",
         "source": STATE.get("source_label", ""), "link": (base + "/na/fs/" + e["tok"]) if base else "", "fs_tok": e["tok"]}
    jpg = fp_spot_pic(e)
    threading.Thread(target=w.notifier._dispatch, args=(p, jpg, "spot.jpg" if jpg else ""), daemon=True).start()
    return True


def fp_buttons(p, lang=None):
    tok = p.get("fs_tok") or ""
    base = alx_base()
    if not tok or not base:
        return []
    return [(tr("Yes, ignore", lang), f"{base}/na/fs/{tok}/yes"), (tr("No", lang), f"{base}/na/fs/{tok}/no")]


_fp_ntfy_actions_before = alx_ntfy_actions
_fp_tg_markup_before = alx_telegram_markup


# wraps: alx_ntfy_actions
def alx_ntfy_actions(p):                                  # + 639zy: the two buttons of the spot question
    if p.get("fs_tok"):
        return "; ".join(f"http, {' '.join(lab.replace(',', ' ').replace(';', ' ').split())}, {url}, method=POST, clear=true" for lab, url in fp_buttons(p))
    return _fp_ntfy_actions_before(p)


# wraps: alx_telegram_markup
def alx_telegram_markup(p):                               # + 639zy
    if p.get("fs_tok"):
        b = fp_buttons(p)
        return {"inline_keyboard": [[{"text": lab, "url": url} for lab, url in b]]} if b else None
    return _fp_tg_markup_before(p)


def fp_pending(now=None):
    now = time.time() if now is None else now
    out = []
    for k, e in fp_load()["asked"].items():
        if fp_open(e, now):
            out.append({"tok": e["tok"], "n": int(e.get("n") or 0), "t": int(e.get("t") or 0), "cell": e.get("cell")})
    return sorted(out, key=lambda x: -x["t"])


_fp_alx_label_before = alx_label


def alx_label(lid, label, who="web"):                     # + 639zy: «Nothing» / «False alarm» notes the spot
    ok, err = _fp_alx_label_before(lid, label, who)
    if ok:
        try:
            x = _alx_label_load(lid)
            if label == "nothing":
                fp_spot_note(x)
            elif x:
                fp_spot_forget(str(x.get("stamp") or lid))
        except Exception as e:
            log_event("sys", f"False alarm spot: {e}"[:160])
    return ok, err


_fp_rec_set_false_before = rec_set_false
_FP_REC_STAMP = re.compile(r"^person_(\d{8}_\d{6})\.(mp4|jpg)$")


def rec_set_false(names, cause, watch=None):              # + 639zy: «False alarm» in the recordings notes the spot too
    n = _fp_rec_set_false_before(names, cause, watch)
    try:
        for name in (names if isinstance(names, list) else [])[:50]:
            m = _FP_REC_STAMP.match(os.path.basename(str(name)))
            if not m:
                continue
            if cause in FA_CAUSES:
                x = _alx_label_load(m.group(1))
                if x:
                    fp_spot_note(x)
            else:
                fp_spot_forget(m.group(1))
    except Exception as e:
        log_event("sys", f"False alarm spot: {e}"[:160])
    return n


_fp_ctx_note_before = alarm_ctx_note


# wraps: alarm_ctx_note
def alarm_ctx_note(w, stamp, snap, frame, persons):       # + 639zy: the head direction for the spot (saved with the context)
    lid = _fp_ctx_note_before(w, stamp, snap, frame, persons)
    try:
        ctx = ALX.get("ctx")
        if ctx and ctx.get("id") == lid:
            pan, tilt = servo_pos()
            ctx.update(pan=round(float(pan), 1), tilt=round(float(tilt), 1), srv=SRV.get("pos") is not None)
    except Exception:
        pass
    return lid


# ---- 3: wind protection for plant areas ---------------------------------------------------------------------------------------
def wg_feed(fg_mask, person_boxes, now=None):
    """called with every foreground mask (WeatherAnalyzer.wind): how often each field moved in the last minute"""
    if not CFG.get("wind_guard", True) or fg_mask is None or fg_mask.size == 0:
        return
    now = time.time() if now is None else now
    m = (fg_mask > 0).astype(np.uint8)
    for b in person_boxes or []:
        x, y, w, h = (int(v) for v in b[:4])
        m[max(0, y):y + h, max(0, x):x + w] = 0
    frac = cv2.resize(m.astype(np.float32), WG_GRID, interpolation=cv2.INTER_AREA)
    act = (frac > 0.004).astype(np.float32)
    dt = min(5.0, max(0.0, now - WG["t"])) if WG["t"] else 0.2
    WG["t"] = now
    a = 1.0 - math.exp(-dt / WG_TAU_S)
    WG["occ"] = act * a + (WG["occ"] if WG["occ"] is not None and WG["occ"].shape == act.shape else np.zeros_like(act)) * (1.0 - a)


def wg_veg(fx, fy):
    o = WG["occ"]
    if o is None:
        return False
    c = max(0, min(WG_GRID[0] - 1, int(fx * WG_GRID[0])))
    r = max(0, min(WG_GRID[1] - 1, int(fy * WG_GRID[1])))
    return bool(o[r, c] >= WG_VEG)


def wg_wind():
    """'' = no strong wind, else why (measured / simulated gusts, else the picture)"""
    lim = max(10.0, float(CFG.get("wind_guard_kmh") or 40.0))
    st = STATE.get("storm") or {}
    try:
        g = st.get("gust")
        if g is not None and float(g) >= lim:
            return f"gusts {float(g):.0f} km/h"
        v = st.get("wind")
        if v is not None and float(v) >= lim * 0.6:
            return f"wind {float(v):.0f} km/h"
    except (TypeError, ValueError):
        pass
    if STATE.get("wind_level") in ("strong", "storm"):
        return "picture: " + str(STATE.get("wind_level"))
    return ""


def wind_guard_filter(w, persons, now):
    """3: in strong wind a person from movement alone on a plant field needs the AI or heat - or 6 s longer"""
    if not persons or not CFG.get("wind_guard", True) or WG["occ"] is None:
        return persons
    why = wg_wind()
    if not why:
        WG["seen"].clear()
        return persons
    pw, ph = getattr(w, "_proc_size", None) or (0, 0)
    if not pw or not ph:
        return persons
    ai = [b for b in (getattr(getattr(w, "ai", None), "boxes", None) or [])]
    warm = now - float(getattr(w, "last_warm", 0.0) or 0.0) < 3.0
    out, held = [], 0
    for b in persons:
        x, y, bw, bh = (float(v) for v in b[:4])
        fx, fy = (x + bw / 2.0) / pw, (y + bh * 0.85) / ph
        cx, cy = (x + bw / 2.0) / pw, (y + bh / 2.0) / ph
        if warm or not (wg_veg(fx, fy) or wg_veg(cx, cy)) or any(iou(tuple(b[:4]), tuple(a[:4])) > 0.2 for a in ai):
            out.append(b)
            continue
        k = (int(cx * WG_GRID[0]), int(cy * WG_GRID[1]))
        first, last = WG["seen"].get(k, (now, now))
        if now - last > 2.0:
            first = now
        WG["seen"][k] = (first, now)
        if now - first >= WG_HOLD_S:
            out.append(b)
            if now - first < WG_HOLD_S + 0.6:
                WG["passed"] += 1
                log_event("wind", f"Wind protection: movement in a plant area stayed {WG_HOLD_S:.0f} s - counts ({why})")
            continue
        held += 1
    if held:
        WG["held"] += held; WG["why"] = why
        if now - WG["log_t"] > 30:
            WG["log_t"] = now
            log_event("wind", f"Wind protection: movement in a plant area held back ({why}; no AI person, no heat)")
    return out


_fp_wind_before = WeatherAnalyzer.wind


def _fp_wind(self, fg_mask, person_boxes):
    r = _fp_wind_before(self, fg_mask, person_boxes)
    try:
        wg_feed(fg_mask, person_boxes)
    except Exception:
        pass
    return r


# wraps: WeatherAnalyzer.wind
WeatherAnalyzer.wind = _fp_wind


# ---- 4: bundling -----------------------------------------------------------------------------------------------------------
def _fp_thumb(frame, wd=240):
    if frame is None:
        return None
    h, w = frame.shape[:2]
    return cv2.resize(frame, (wd, max(2, int(h * wd / max(1, w)))), interpolation=cv2.INTER_AREA) if w > wd else frame.copy()


def fp_bundle_add(frame, now=None):
    now = time.time() if now is None else now
    with FPB["lock"]:
        if not FPB["n"]:
            FPB["first"] = now
        FPB["n"] += 1
        t_ = _fp_thumb(frame)
        if t_ is not None:
            FPB["items"].append((now, t_))
            if len(FPB["items"]) > 8:
                FPB["items"].pop(4)                     # keep the first few and the newest


def fp_bundle_pop():
    with FPB["lock"]:
        out = (FPB["n"], FPB["first"], list(FPB["items"]))
        FPB.update(n=0, first=0.0, items=[])
    return out


def fp_pick4(items):
    if len(items) <= 4:
        return [f for _t, f in items]
    idx = sorted({round(i * (len(items) - 1) / 3.0) for i in range(4)})
    return [items[i][1] for i in idx]


def fp_strip(jpg, thumbs, width=None):
    """the picture with a strip of up to 4 small pictures below (JPEG); without a picture only the strip"""
    if not thumbs:
        return jpg
    main = None
    if jpg:
        try:
            main = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        except Exception:
            main = None
    W = int(width or (main.shape[1] if main is not None else 960))
    cw = W // 4
    ch = max(int(t_.shape[0] * cw / max(1, t_.shape[1])) for t_ in thumbs)
    strip = np.full((ch + 6, W, 3), 24, np.uint8)
    for i, t_ in enumerate(thumbs[:4]):
        th = cv2.resize(t_, (cw - 4, max(2, int(t_.shape[0] * (cw - 4) / max(1, t_.shape[1])))), interpolation=cv2.INTER_AREA)
        strip[3:3 + th.shape[0], i * cw + 2:i * cw + 2 + th.shape[1]] = th[:ch]
    img = strip if main is None else np.vstack([main, strip])
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buf.tobytes() if ok else jpg


def fp_more_text(n, m):
    return pk_trf("+{n} more in {m} min", n=int(n), m=int(m))


def fp_bundle_take(p, jpg, now=None):
    """the next push after the pause: «+N more in M min» and the strip"""
    now = time.time() if now is None else now
    if not CFG.get("push_bundle", True):
        fp_bundle_pop()
        return jpg
    if not p.get("more"):
        return jpg
    n, first, items = fp_bundle_pop()
    if not n:
        return jpg
    p["more_min"] = max(1, int(math.ceil((now - first) / 60.0)))
    return fp_strip(jpg, fp_pick4(items)) if items else jpg


def fp_bundle_tick(w, now):
    """push_bundle_after: when the pause is over and nothing new came, the collection goes out on its own"""
    if not (CFG.get("push_bundle", True) and CFG.get("push_bundle_after")) or not FPB["n"]:
        return
    n_ = getattr(w, "notifier", None)
    if n_ is None or now - float(getattr(n_, "last", 0.0)) < float(CFG["notify_cooldown"]):
        return
    if now - FPB["first"] < 5:
        return
    n, first, items = fp_bundle_pop()
    if not n or not (n_.configured() and CFG.get("notify_on") and is_armed()):
        return
    n_.more = 0
    pub = str(CFG.get("public_url") or "").strip().rstrip("/")
    p = {"event": "person", "persons": 1, "time": datetime.fromtimestamp(first).isoformat(timespec="seconds"), "snapshot": None,
         "rain": bool(STATE.get("rain_mode")), "wind": STATE.get("wind_level", ""), "source": STATE.get("source_label", ""),
         "link": pub + "/recordings" if pub else "", "more": n, "more_min": max(1, int(math.ceil((now - first) / 60.0))),
         "bundle_only": True, "_fp": 1}
    jpg = fp_strip(None, fp_pick4(items), 720) if items else None
    log_event("web", f"Bundle of {n} detections in the pause sent")
    threading.Thread(target=n_._dispatch, args=(p, jpg, "bundle.jpg" if jpg else ""), daemon=True).start()


_fp_person_before = Notifier.person


def _fp_person(self, count, snapshot_path=None, frame=None):
    try:
        if count and CFG.get("push_bundle", True) and is_armed() and CFG["notify_on"] and self.configured() \
                and time.time() - self.last < CFG["notify_cooldown"] and push_allowed("person")[0]:
            fp_bundle_add(frame)
    except Exception:
        pass
    return _fp_person_before(self, count, snapshot_path, frame)


# wraps: Notifier.person
Notifier.person = _fp_person


# ---- 5: zone name ----------------------------------------------------------------------------------------------------------
_FP_AUTO_NAME = re.compile(r"^(Zone|Zona)\s*\d+$", re.I)


def fp_zone_name(boxes):
    """the name of the smallest own-named zone of the main camera with the feet of the biggest box inside ('' = none)"""
    pt = fp_feet(boxes)
    if pt is None:
        return ""
    best, ba = "", 9.0
    for z in list(ZONES):
        if z.get("mode") in ("privacy", "sleep", "line") or not zone_here(z):
            continue
        nm = str(z.get("name") or "").strip()
        if not nm or _FP_AUTO_NAME.match(nm) or len(z.get("points") or []) < 3:
            continue
        if point_in_poly(pt[0], pt[1], z["points"]):
            pts = z["points"]
            a = abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2.0
            if a < ba:
                best, ba = nm[:40], a
    return best


_fp_push_short_before = push_short


def push_short(p):                                        # + 639zy: zone name in the title, «+N more in M min», «picture at home»
    q = p
    if p.get("more") and p.get("more_min"):
        q = dict(p); q.pop("more", None)
    r = _fp_push_short_before(q)
    try:
        ev = Notifier._event(p)
        if ev == "person" and p.get("zone") and CFG.get("push_zone_name", True) and not str(CFG.get("msg_person_title") or "").strip():
            n = int(p.get("persons") or 1)
            old = pk_tr("Person detected") if n <= 1 else pk_trf("{n} persons", n=n)
            new = pk_trf("Person at «{zone}»", zone=p["zone"]) if n <= 1 else trf("{n} persons at «{zone}»", n=n, zone=p["zone"])
            if old in r["title"]:
                r["title"] = pk_line(r["title"].replace(old, new, 1), 60)
        extra = []
        if q is not p:
            extra.append(fp_more_text(p["more"], p["more_min"]))
        if p.get("home_id"):
            extra.append("🏠 " + tr("picture at home"))
        if extra:
            r["text"] = pk_line(" · ".join(x for x in [r["text"]] + extra if x))
    except Exception:
        pass
    return r


_fp_push_long_before = push_long


def push_long(p):                                         # + 639zy (e-mail)
    q = p
    if p.get("more") and p.get("more_min"):
        q = dict(p); q.pop("more", None)
    t_ = _fp_push_long_before(q)
    try:
        if p.get("zone") and CFG.get("push_zone_name", True) and Notifier._event(p) == "person":
            t_ += " · " + trf("Zone «{zone}»", zone=p["zone"])
        if q is not p:
            t_ += " " + trf("(+{n} more detections in {m} min)", n=int(p["more"]), m=int(p["more_min"]))
        if p.get("home_id") and p.get("link"):
            t_ += " · 🏠 " + tr("picture at home") + ": " + p["link"]
    except Exception:
        pass
    return t_


# ---- 7: pictures stay at home ------------------------------------------------------------------------------------------------
def pb_dir():
    return os.path.join(DATA_DIR, "push_bilder")


def pb_prune():
    d = pb_dir()
    try:
        fs = sorted(os.listdir(d), key=lambda f_: os.path.getmtime(os.path.join(d, f_)))
    except OSError:
        return
    old = time.time() - PB_DAYS * 86400
    ids = []
    for f_ in fs:
        i = f_.split(".")[0]
        if i not in ids:
            ids.append(i)
    drop = set(ids[:max(0, len(ids) - PB_KEEP)])
    for f_ in fs:
        try:
            if f_.split(".")[0] in drop or os.path.getmtime(os.path.join(d, f_)) < old:
                os.remove(os.path.join(d, f_))
        except OSError:
            pass


def pb_store(data, ext, pid=None):
    """keep a picture / clip of a message on the Pi: returns the id (16 hex) or ''"""
    if not data or ext not in ("jpg", "mp4", "gif"):
        return ""
    pid = pid if pid and PB_RE.match(pid) else secrets.token_hex(8)
    try:
        os.makedirs(pb_dir(), exist_ok=True)
        with open(os.path.join(pb_dir(), pid + "." + ext), "wb") as f:
            f.write(data)
        pb_prune()
        return pid
    except OSError as e:
        log_event("web", f"Picture of the message not kept: {e}"[:160])
        return ""


def pb_link(pid):
    base = alx_base()
    return (base + "/pb/" + pid) if base and pid else ""


def fp_home(p, jpg):
    """7: the picture stays on the Pi - the message gets the link instead (the channels drop the picture, sx_push_jpg)"""
    if not CFG.get("push_home_pics") or not jpg:
        return
    pid = pb_store(jpg, "jpg")
    if not pid:
        return
    p["home_id"] = pid
    if Notifier._event(p) in ("person", "prealarm", "warm", "noise", "tamper", "test"):
        p["link"] = pb_link(pid) or p.get("link", "")


_fp_sx_push_jpg_before = sx_push_jpg


def sx_push_jpg(jpg):                                     # + 639zy: «pictures stay at home» - no picture leaves the Pi
    if CFG.get("push_home_pics"):
        return None
    return _fp_sx_push_jpg_before(jpg)


_fp_email_send_before = email_send


def email_send(subject, text, jpg=None, fname="photo.jpg"):   # + 639zy: the e-mail without the picture too
    if CFG.get("push_home_pics"):
        jpg = None
    return _fp_email_send_before(subject, text, jpg, fname)


# ---- 6: short clip ----------------------------------------------------------------------------------------------------------
def fp_clip_feed(frame, now):
    if not CFG.get("push_clip") or frame is None or not is_armed():
        if CLIP["buf"]:
            CLIP["buf"].clear()
        return
    if now - CLIP["last"] < 1.0 / CLIP_FPS:
        return
    CLIP["last"] = now
    CLIP["buf"].append((now, _fp_thumb(frame, 320)))
    while CLIP["buf"] and now - CLIP["buf"][0][0] > CLIP_KEEP_S:
        CLIP["buf"].popleft()


def _fp_even(frames, wd):
    out = []
    for f_ in frames:
        h, w = f_.shape[:2]
        nw = max(16, int(wd) // 2 * 2); nh = max(16, int(h * nw / max(1, w)) // 2 * 2)
        out.append(cv2.resize(f_, (nw, nh), interpolation=cv2.INTER_AREA))
    return out


def fp_clip_gif(frames, fps):
    from PIL import Image
    ims = [Image.fromarray(cv2.cvtColor(f_, cv2.COLOR_BGR2RGB)).convert("P", palette=Image.ADAPTIVE, colors=64) for f_ in frames]
    import io as _io
    b = _io.BytesIO()
    ims[0].save(b, format="GIF", save_all=True, append_images=ims[1:], duration=int(1000 / max(1.0, fps)), loop=0, optimize=True)
    return b.getvalue()


def fp_clip_mp4(frames, fps):
    h, w = frames[0].shape[:2]
    tmp = tempfile.mkdtemp(prefix="mw_clip_")
    out = os.path.join(tmp, "clip.mp4")
    try:
        if shutil.which("ffmpeg"):
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", f"{fps:.2f}",
                                "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "32", "-pix_fmt", "yuv420p",
                                "-movflags", "+faststart", out], input=b"".join(f_.tobytes() for f_ in frames), capture_output=True, timeout=40)
            if r.returncode == 0 and os.path.getsize(out) > 0:
                with open(out, "rb") as f:
                    return f.read()
        vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        if not vw.isOpened():
            return b""
        for f_ in frames:
            vw.write(f_)
        vw.release()
        with open(out, "rb") as f:
            return f.read()
    except (OSError, subprocess.SubprocessError):
        return b""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fp_clip_make(frames, fps, fmt, cap_kb):
    """(bytes, fps, width) under cap_kb or (b'', …): smaller and fewer pictures until it fits"""
    cap = int(max(50, float(cap_kb)) * 1024)
    last = (b"", 0, 0)
    for wd, step in ((320, 1), (240, 2), (160, 3)):
        fr = _fp_even(frames[::step], wd)
        f2 = fps / step
        try:
            data = fp_clip_gif(fr, f2) if fmt == "gif" else fp_clip_mp4(fr, f2)
        except Exception:
            data = b""
        last = (data, f2, wd)
        if data and len(data) <= cap:
            return last
    return (b"", last[1], last[2]) if not last[0] or len(last[0]) > cap else last


def _fp_multipart(fields, fname, ctype, data, field):
    b = uuid.uuid4().hex
    parts = [f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields]
    parts.append((f'--{b}\r\nContent-Disposition: form-data; name="{field}"; filename="{fname}"\r\n'
                  f'Content-Type: {ctype}\r\n\r\n').encode() + data + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    return b"".join(parts), "multipart/form-data; boundary=" + b


def fp_clip_channel():
    """'ntfy' / 'telegram' / '' - the main channel that can take a clip"""
    kind = CFG.get("notify_type")
    if kind == "telegram" and CFG.get("telegram_token") and CFG.get("telegram_chat"):
        return "telegram"
    url = str(CFG.get("notify_url") or "").strip()
    if url and (kind == "ntfy" or push_url_is_ntfy(url)):
        return "ntfy"
    return ""


def fp_clip_send(notifier, p, data, fmt):
    title = notifier._title(p) + " · 🎬"
    ch = fp_clip_channel()
    if ch == "ntfy":
        h = {"Title": _hdr(title), "Filename": "clip." + fmt, "Message": _hdr(tr("Clip of the alarm")), "Priority": "default"}
        if p.get("link"):
            h["Click"] = p["link"]
        req = urllib.request.Request(str(CFG["notify_url"]).strip(), data=data, headers=h, method="PUT")
    elif ch == "telegram":
        base = f"{TELEGRAM_API}/bot{CFG['telegram_token']}"
        field, meth, ct = ("video", "/sendVideo", "video/mp4") if fmt == "mp4" else ("animation", "/sendAnimation", "image/gif")
        body_, ctype = _fp_multipart((("chat_id", CFG["telegram_chat"]), ("caption", title)), "clip." + fmt, ct, data, field)
        req = urllib.request.Request(base + meth, data=body_, headers={"Content-Type": ctype})
    else:
        return False, "no channel"
    with urllib.request.urlopen(req, timeout=30) as r:
        return True, f"HTTP {r.status}"


def fp_clip_job(notifier, p, t0):
    dur = max(3.0, min(5.0, float(CFG.get("push_clip_s") or 4.0)))
    pre, post = dur * 0.6, dur * 0.4
    time.sleep(max(0.0, t0 + post + 0.3 - time.time()))
    frames = [f_ for t_, f_ in list(CLIP["buf"]) if t0 - pre <= t_ <= t0 + post]
    st = {"t": int(time.time()), "frames": len(frames), "bytes": 0, "fmt": "", "sent": "", "home": ""}
    CLIP["state"] = st
    if len(frames) < 6:
        st["sent"] = "too few pictures"
        return st
    home = bool(CFG.get("push_home_pics"))
    ch = fp_clip_channel()
    fmt = "gif" if (ch == "ntfy" and not home) else "mp4"
    data, fps, wd = fp_clip_make(frames, len(frames) / dur, fmt, CFG.get("push_clip_kb") or 800)
    st.update(bytes=len(data), fmt=fmt, width=wd)
    if not data:
        st["sent"] = "too big"
        log_event("web", f"Clip not sent: bigger than {int(float(CFG.get('push_clip_kb') or 800))} KB also when small")
        return st
    if home:
        st["home"] = pb_store(data, fmt, p.get("home_id")) or ""
        st["sent"] = "home"
        return st
    try:
        if sandbox_active():
            st["sent"] = "test inbox"
            return st
    except NameError:
        pass
    if sim_net_down() or not ch or not CFG.get("notify_on"):
        st["sent"] = "no channel"
        return st
    try:
        ok, msg = fp_clip_send(notifier, p, data, fmt)
        st["sent"] = "ok" if ok else msg
        log_event("web", f"Clip sent ({fmt}, {len(data) // 1024} KB, {ch})")
    except Exception as e:
        msg = str(e)
        for s_ in (CFG.get("telegram_token"), str(CFG.get("notify_url") or "").strip()):
            if s_:
                msg = msg.replace(s_, "***")
        st["sent"] = "failed"
        log_event("web", f"Clip failed: {msg}"[:200])
    return st


# ---- the one place where every message passes: 4, 5, 6, 7 -------------------------------------------------------------------
_fp_dispatch_before = Notifier._dispatch


def _fp_dispatch(self, p, jpg, fname):
    try:
        ev = Notifier._event(p)
        if ev == "person" and not p.get("late") and not p.get("_fp"):
            p["_fp"] = 1
            now = time.time()
            ctx = ALX.get("ctx")
            if ctx and now - float(ctx.get("t") or 0) < 15 and CFG.get("push_zone_name", True) and "zone" not in p:
                z = fp_zone_name(ctx.get("boxes"))
                if z:
                    p["zone"] = z
            jpg = fp_bundle_take(p, jpg, now)
            if jpg and fname in ("", None):
                fname = "snapshot.jpg"
            fp_home(p, jpg)
            if CFG.get("push_clip") and int(p.get("persons") or 0) > 0:
                threading.Thread(target=fp_clip_job, args=(self, dict(p), now), daemon=True, name="fp-clip").start()
        elif ev == "person" and p.get("bundle_only") and not p.get("home_id"):
            fp_home(p, jpg)
        elif ev != "person" and not p.get("home_id") and not p.get("late"):
            fp_home(p, jpg)
    except Exception as e:
        log_event("sys", f"Push extras: {e}"[:160])
    return _fp_dispatch_before(self, p, jpg, fname)


# wraps: Notifier._dispatch
Notifier._dispatch = _fp_dispatch

# ---- the gate: clip pictures, wind protection, the bundle on its own --------------------------------------------------------
_alarm_gate_639zy = alarm_gate


def alarm_gate(w, frame, persons, now):                   # + 639zy (the camera loop calls it for every picture, 410)
    try:
        fp_clip_feed(frame, now)
    except Exception:
        pass
    try:
        persons = wind_guard_filter(w, persons, now)
    except Exception as e:
        if now - WG.get("err_t", 0.0) > 300:
            WG["err_t"] = now
            log_event("sys", f"Wind protection: {e}"[:160])
    out = _alarm_gate_639zy(w, frame, persons, now)
    try:
        fp_bundle_tick(w, now)
    except Exception:
        pass
    return out


def fp_state():
    return {"pending": fp_pending(), "notes": len(fp_load()["notes"]), "learn": bool(CFG.get("fp_spot_learn", True)),
            "wind": {"on": bool(CFG.get("wind_guard", True)), "strong": wg_wind(), "held": WG["held"], "passed": WG["passed"],
                     "plant_fields": int((WG["occ"] >= WG_VEG).sum()) if WG["occ"] is not None else 0},
            "bundle": {"on": bool(CFG.get("push_bundle", True)), "waiting": FPB["n"]},
            "clip": {"on": bool(CFG.get("push_clip")), "last": CLIP.get("state") or {}},
            "home_pics": bool(CFG.get("push_home_pics")), "confirm2": bool(CFG.get("alarm_confirm2"))}


# ---- web: /na/fs/<key>/<yes|no> (public with the key), /api/fehlalarm_stellen, /pb/<id> (behind the password) ---------------
_smalltv_routes_639zy = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zy
    _smalltv_routes_639zy(app, reply, body)
    from flask import Response, request
    import html as _html

    def _fails(ip, now):
        rec = [x for x in ALX["fails"].get(ip, []) if now - x < 600]
        ALX["fails"][ip] = rec
        return rec

    @app.route("/na/fs/<tok>/<act>", methods=["GET", "POST"])
    def fp_web_answer(tok, act):
        ip = request.remote_addr or "?"
        now = time.time()
        rec = _fails(ip, now)
        if len(rec) >= 20:
            return sx_err(429, "keys")
        with _FP_LOCK:
            key, e = fp_by_tok(tok)
        if not fp_open(e, now) or act not in ("yes", "no", "bild.jpg"):
            rec.append(now)
            return Response(_ALX_PAGE % ("MoveEye", _html.escape(tr("This question is no longer open.")), ""), 404, mimetype="text/html")
        if act == "bild.jpg":
            jpg = fp_spot_pic(e)
            return Response(jpg, mimetype="image/jpeg", headers={"Cache-Control": "no-store"}) if jpg else Response("not found", 404)
        if request.method == "GET":                      # a browser / Telegram: ask first (a link preview must not change anything)
            img = f'<p><img src="/na/fs/{tok}/bild.jpg" alt="" style="max-width:100%;border-radius:10px"></p>'
            q = _html.escape(tr("False alarms often come from here – ignore this spot from now on?"))
            info = _html.escape(trf("{n} false alarms in 7 days", n=int(e.get("n") or 0)))
            btn = lambda a, lab, bg: (f'<form method="post" action="/na/fs/{tok}/{a}" style="display:inline-block;margin:4px">'
                                      f'<button type="submit" style="background:{bg}">{_html.escape(lab)}</button></form>')
            return Response(_ALX_PAGE % ("🎯 " + _html.escape(tr("False alarm spot")), info + "</p>" + img + "<p>" + q,
                                         btn("yes", tr("Yes, ignore"), "#2f81f7") + btn("no", tr("No"), "#4a5361")), mimetype="text/html")
        ok, txt = fp_spot_answer(tok, act, "push button")
        if "text/html" in (request.headers.get("Accept") or "") or request.form is not None and request.content_type and "form" in request.content_type:
            return Response(_ALX_PAGE % ("MoveEye", ("✓ " if ok else "⚠ ") + _html.escape(txt), ""), 200 if ok else 409, mimetype="text/html")
        return Response(txt, 200 if ok else 409, mimetype="text/plain")

    @app.route("/api/fehlalarm_stellen", methods=["GET", "POST"])
    def fp_api():
        if request.method == "POST":
            d = body()
            ok, txt = fp_spot_answer(str(d.get("tok") or ""), str(d.get("act") or ""), "web")
            return reply({"ok": ok, "text": txt, "error": None if ok else txt}, 200 if ok else 409)
        return reply(fp_state())

    @app.route("/pb/<name>")
    def pb_web(name):
        m = re.fullmatch(r"([0-9a-f]{16})(?:\.(jpg|mp4|gif))?", name or "")
        if not m:
            return Response("not found", 404)
        pid, ext = m.group(1), m.group(2)
        if ext:
            p_ = os.path.join(pb_dir(), pid + "." + ext)
            if not os.path.isfile(p_):
                return Response("not found", 404)
            from flask import send_file
            return send_file(p_, mimetype={"jpg": "image/jpeg", "mp4": "video/mp4", "gif": "image/gif"}[ext], max_age=3600)
        have = [x for x in ("jpg", "gif", "mp4") if os.path.isfile(os.path.join(pb_dir(), pid + "." + x))]
        if not have:
            return Response(_ALX_PAGE % ("MoveEye", _html.escape(tr("not found")), ""), 404, mimetype="text/html")
        parts = []
        for x in have:
            parts.append(f'<p><video src="/pb/{pid}.mp4" controls autoplay muted playsinline loop style="max-width:100%"></video></p>'
                         if x == "mp4" else f'<p><img src="/pb/{pid}.{x}" alt="" style="max-width:100%;border-radius:10px"></p>')
        return Response(_ALX_PAGE % ("🏠 " + _html.escape(tr("Picture of the message")), "", "".join(parts)
                                     + '<p><a href="/recordings" style="color:#8ab4f8">' + _html.escape(tr("Recordings")) + "</a></p>"),
                        mimetype="text/html", headers={"Cache-Control": "no-store"})


# ---- settings (web + window: the same lists; in the web under Push → Advanced) -----------------------------------------------
_FP_TG = [
    ("fp_spot_learn", "Learn false-alarm spots: after 3 false alarms at the same place within 7 days, ask once whether to ignore it (never without your answer)"),
    ("push_bundle", "Bundle alarms during the pause: the next message says «+N more in M min» with a strip of up to 4 small pictures"),
    ("push_bundle_after", "After the pause, send the bundle also on its own (without a new alarm)"),
    ("push_zone_name", "Zone name in the message («Person at «Entrance»»)"),
    ("push_clip", "Short clip with the alarm (3-5 s, small; ntfy and Telegram)"),
    ("push_home_pics", "Pictures stay at home: messages contain only text and a link to the picture / clip on MoveEye"),
]
_fp_i = next((i for i, t_ in enumerate(TOGGLES) if t_[1] == "sim_info_push"), len(TOGGLES) - 1)
for _j, (_k, _l) in enumerate(_FP_TG):
    TOGGLES.insert(_fp_i + 1 + _j, ("Notifications", _k, _l))
_fp_s = next((i for i, s_ in enumerate(SLIDERS) if s_[1] == "notify_cooldown"), len(SLIDERS) - 1)
SLIDERS.insert(_fp_s + 1, ("Notifications", "push_clip_s", "Clip length (s)", 3.0, 5.0, 0.5))
SLIDERS.insert(_fp_s + 2, ("Notifications", "push_clip_kb", "Clip at most (KB)", 200.0, 3000.0, 100.0))
_fp_c = next((i for i, t_ in enumerate(TOGGLES) if t_[1] == "alarm_heat_fusion"), len(TOGGLES) - 1)
_fp_sec = TOGGLES[_fp_c][0] if 0 <= _fp_c < len(TOGGLES) and TOGGLES[_fp_c][1] == "alarm_heat_fusion" else "Detection"
TOGGLES.insert(_fp_c + 1, (_fp_sec, "wind_guard",
                           "Wind protection: in strong wind, movement in plant areas (leaves that move all the time) needs the AI or the thermal camera - or 6 s longer"))
_fp_w = next((i for i, s_ in enumerate(SLIDERS) if s_[0] == _fp_sec), len(SLIDERS) - 1)
SLIDERS.insert(_fp_w + 1, (_fp_sec, "wind_guard_kmh", "Wind protection from gusts of (km/h)", 20.0, 80.0, 5.0))
PK_TITLES.setdefault("False alarm spot", ("🎯", "False alarm spot", "info", False))

# ---- translations (English key: Deutsch, Français, Italiano, Rumantsch) ----------------------------------------------------
_HX_FP = {
    "Learn false-alarm spots: after 3 false alarms at the same place within 7 days, ask once whether to ignore it (never without your answer)": (
        "Fehlalarm-Stellen lernen: nach 3 Fehlalarmen an derselben Stelle in 7 Tagen einmal fragen, ob sie ignoriert werden soll (nie ohne deine Antwort)",
        "Apprendre les endroits de fausses alarmes : après 3 fausses alarmes au même endroit en 7 jours, demander une fois s’il faut l’ignorer (jamais sans ta réponse)",
        "Imparare i punti dei falsi allarmi: dopo 3 falsi allarmi nello stesso punto in 7 giorni, chiedere una volta se ignorarlo (mai senza la tua risposta)",
        "Emprender ils lieus dad alarms faussas: suenter 3 alarms faussas al medem lieu en 7 dis dumandar ina giada sch’el duai vegnir ignorà (mai senza tia resposta)"),
    "Bundle alarms during the pause: the next message says «+N more in M min» with a strip of up to 4 small pictures": (
        "Alarme in der Pause bündeln: die nächste Meldung sagt «+N weitere in M Min.» mit einem Streifen von bis zu 4 kleinen Bildern",
        "Regrouper les alarmes pendant la pause : le message suivant dit «+N autres en M min» avec une bande de jusqu’à 4 petites images",
        "Raggruppare gli allarmi durante la pausa: il messaggio successivo dice «+N altri in M min» con una striscia di fino a 4 piccole immagini",
        "Unir ils alarms durant la pausa: il proxim messadi di «+N ulteriurs en M min» cun ina strivla da fin a 4 maletgs pitschens"),
    "After the pause, send the bundle also on its own (without a new alarm)": (
        "Nach der Pause die Sammlung auch allein schicken (ohne neuen Alarm)",
        "Après la pause, envoyer aussi le groupe seul (sans nouvelle alarme)",
        "Dopo la pausa, inviare il gruppo anche da solo (senza nuovo allarme)",
        "Suenter la pausa trametter la collecziun er sulet (senza nov alarm)"),
    "Zone name in the message («Person at «Entrance»»)": (
        "Zonen-Name in der Meldung («Person bei «Eingangstür»»)", "Nom de la zone dans le message («Personne à «Entrée»»)",
        "Nome della zona nel messaggio («Persona a «Ingresso»»)", "Num da la zona en il messadi («Persuna tar «Entrada»»)"),
    "Short clip with the alarm (3-5 s, small; ntfy and Telegram)": (
        "Kurzer Clip zum Alarm (3–5 s, klein; ntfy und Telegram)", "Court clip avec l’alarme (3–5 s, petit ; ntfy et Telegram)",
        "Breve clip con l’allarme (3–5 s, piccola; ntfy e Telegram)", "Curt clip cun l’alarm (3–5 s, pitschen; ntfy e Telegram)"),
    "Pictures stay at home: messages contain only text and a link to the picture / clip on MoveEye": (
        "Bilder bleiben zu Hause: Meldungen nur mit Text und einem Link zum Bild / Clip auf dem MoveEye",
        "Les images restent à la maison : messages seulement avec texte et un lien vers l’image / le clip sur MoveEye",
        "Le immagini restano a casa: messaggi solo con testo e un link all’immagine / clip su MoveEye",
        "Ils maletgs restan a chasa: messadis mo cun text ed ina colliaziun al maletg / clip sin MoveEye"),
    "Clip length (s)": ("Länge des Clips (s)", "Durée du clip (s)", "Durata della clip (s)", "Lunghezza dal clip (s)"),
    "Clip at most (KB)": ("Clip höchstens (KB)", "Clip au plus (Ko)", "Clip al massimo (KB)", "Clip al pli (KB)"),
    "Wind protection: in strong wind, movement in plant areas (leaves that move all the time) needs the AI or the thermal camera - or 6 s longer": (
        "Windschutz: bei starkem Wind braucht Bewegung in Pflanzen-Bereichen (Blätter, die sich dauernd bewegen) die KI oder das Wärmebild – oder 6 s länger",
        "Protection contre le vent : par vent fort, un mouvement dans les zones de plantes (feuilles toujours en mouvement) a besoin de l’IA ou de la caméra thermique – ou de 6 s de plus",
        "Protezione dal vento: con vento forte, un movimento nelle zone di piante (foglie sempre in movimento) ha bisogno dell’IA o della termocamera – o di 6 s in più",
        "Protecziun cunter il vent: cun vent ferm dovra in moviment en secturs da plantas (feglia che sa mova adina) l’IA u il maletg termic – u 6 s pli ditg"),
    "Wind protection from gusts of (km/h)": (
        "Windschutz ab Böen von (km/h)", "Protection contre le vent dès des rafales de (km/h)",
        "Protezione dal vento da raffiche di (km/h)", "Protecziun cunter il vent a partir da buffs da (km/h)"),
    "False alarm spot": ("Fehlalarm-Stelle", "Endroit de fausses alarmes", "Punto di falsi allarmi", "Lieu dad alarms faussas"),
    "False alarms often come from here – ignore this spot from now on?": (
        "Hier kommen oft Fehlalarme – künftig ignorieren?", "Les fausses alarmes viennent souvent d’ici – ignorer cet endroit désormais ?",
        "Da qui arrivano spesso falsi allarmi – ignorare questo punto d’ora in poi?", "Qua vegnan savens alarms faussas – ignorar quest lieu en futur?"),
    "Yes, ignore": ("Ja, ignorieren", "Oui, ignorer", "Sì, ignora", "Gea, ignorar"),
    "No": ("Nein", "Non", "No", "Na"),
    "+{n} more in {m} min": ("+{n} weitere in {m} Min.", "+{n} autres en {m} min", "+{n} altri in {m} min", "+{n} ulteriurs en {m} min"),
    "(+{n} more detections in {m} min)": (
        "(+{n} weitere Erkennungen in {m} Min.)", "(+{n} autres détections en {m} min)",
        "(+{n} altri rilevamenti in {m} min)", "(+{n} ulteriuras identificaziuns en {m} min)"),
    "{n} persons at «{zone}»": ("{n} Personen bei «{zone}»", "{n} personnes à «{zone}»", "{n} persone a «{zone}»", "{n} persunas tar «{zone}»"),
    "Zone «{zone}»": ("Zone «{zone}»", "Zone «{zone}»", "Zona «{zone}»", "Zona «{zone}»"),
    "picture at home": ("Bild zu Hause", "image à la maison", "immagine a casa", "maletg a chasa"),
    "Picture of the message": ("Bild der Meldung", "Image du message", "Immagine del messaggio", "Maletg dal messadi"),
    "Clip of the alarm": ("Clip zum Alarm", "Clip de l’alarme", "Clip dell’allarme", "Clip da l’alarm"),
    "{n} false alarms in 7 days": ("{n} Fehlalarme in 7 Tagen", "{n} fausses alarmes en 7 jours", "{n} falsi allarmi in 7 giorni", "{n} alarms faussas en 7 dis"),
    "This question is no longer open.": (
        "Diese Frage ist nicht mehr offen.", "Cette question n’est plus ouverte.", "Questa domanda non è più aperta.", "Questa dumonda n’è betg pli averta."),
    "Done - an ignore zone was added here. You can change it under Zones.": (
        "Erledigt – hier gibt es jetzt eine Ignorier-Zone. Ändern kannst du sie unter Zonen.",
        "C’est fait – une zone ignorée a été ajoutée ici. Tu peux la modifier sous Zones.",
        "Fatto – qui è stata aggiunta una zona ignorata. Puoi modificarla in Zone.",
        "Fatg – qua è ina zona ignorada ussa. Ti pos la midar sut Zonas."),
    "OK - this spot is not ignored. MoveEye does not ask again for 30 days.": (
        "Gut – diese Stelle wird nicht ignoriert. MoveEye fragt 30 Tage lang nicht mehr.",
        "D’accord – cet endroit n’est pas ignoré. MoveEye ne redemande pas pendant 30 jours.",
        "Va bene – questo punto non viene ignorato. MoveEye non chiede più per 30 giorni.",
        "Bun – quest lieu na vegn betg ignorà. MoveEye na dumonda betg pli durant 30 dis."),
    "The camera has changed since - no zone added.": (
        "Die Kamera ist inzwischen eine andere – keine Zone angelegt.", "La caméra a changé entre-temps – aucune zone ajoutée.",
        "Nel frattempo la telecamera è cambiata – nessuna zona aggiunta.", "La camera è entant midada – nagina zona agiuntada."),
    "Too many zones - delete one under Zones first.": (
        "Zu viele Zonen – zuerst unter Zonen eine löschen.", "Trop de zones – supprime d’abord une zone sous Zones.",
        "Troppe zone – elimina prima una zona in Zone.", "Memia bleras zonas – stizza l’emprim ina sut Zonas."),
}
for _k, _v in _HX_FP.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_FP_DE = {_k: _v[0] for _k, _v in _HX_FP.items()}

# ---- the main page: the open spot question as a card (also without push) ----------------------------------------------------
FP_WEB_JS = r"""
<script>
Object.assign(I18N.de, /*FPDE*/{});
(function () {                                             // 639zy: «False alarms often come from here – ignore?» (once per spot)
  let shown = "";
  function ask() {
    if (document.hidden) return;
    fetch("/api/fehlalarm_stellen").then(r => r.json()).then(j => {
      const p = (j.pending || [])[0], old = document.getElementById("fp-ask");
      if (!p) { if (old) old.remove(); shown = ""; return; }
      if (old && shown === p.tok) return;
      if (old) old.remove();
      shown = p.tok;
      const d = el("div", "card"); d.id = "fp-ask";
      d.style.cssText = "position:fixed;left:12px;right:12px;bottom:12px;max-width:520px;margin:0 auto;z-index:60;box-shadow:0 6px 24px #0008";
      const h = el("div", "", "🎯 " + t("False alarm spot") + " · " + t("{n} false alarms in 7 days").replace("{n}", p.n)); h.style.fontWeight = "600";
      const im = el("img"); im.src = "/na/fs/" + p.tok + "/bild.jpg"; im.alt = ""; im.style.cssText = "max-width:100%;border-radius:8px;margin:6px 0"; im.onerror = () => im.remove();
      const q = el("div", "", t("False alarms often come from here – ignore this spot from now on?"));
      const bs = el("div", "btns"); bs.style.marginTop = "8px";
      const go = act => fetch("/api/fehlalarm_stellen", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({tok: p.tok, act: act, lang: LANG})})
        .then(r => r.json()).then(r => { d.remove(); if (typeof toast === "function") toast((r.ok ? "✓ " : "⚠ ") + (r.text || "")); }).catch(() => {});
      const y = el("button", "", t("Yes, ignore")); y.onclick = () => go("yes");
      const n = el("button", "sec", t("No")); n.onclick = () => go("no");
      bs.append(y, n); d.append(h, im, q, bs); document.body.appendChild(d);
    }).catch(() => {});
  }
  setTimeout(ask, 2500); setInterval(ask, 90000);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", FP_WEB_JS.replace("/*FPDE*/{}", json.dumps(_FP_DE, ensure_ascii=False), 1) + "</body>", 1)

# ---- the manual: «Fehlalarme und Pushes» (all 5 languages) ----------------------------------------------------------------
_HELP_FP = {
    "de": ('<section id="false-pushes" data-icon="🎯"><h2>Fehlalarme und Pushes</h2><ul>'
           '<li><b>Fehlalarm-Stellen:</b> Tippst du «Fehlalarm» oder «Was war das? → Nichts», merkt sich MoveEye die Stelle im Bild. '
           'Kommen dort 3 Fehlalarme in 7 Tagen, fragt MoveEye <i>einmal</i>: «Hier kommen oft Fehlalarme – künftig ignorieren?». '
           '«Ja, ignorieren» legt eine Ignorier-Zone (nur Personen) für dieses Feld an, «Nein» lässt alles, wie es ist. Ohne deine Antwort wird nie etwas ignoriert.</li>'
           '<li><b>Windschutz:</b> Bei starkem Wind braucht Bewegung in Bereichen, in denen sich dauernd Blätter bewegen, die KI oder das Wärmebild – oder sie muss 6 s länger dauern.</li>'
           '<li><b>Gebündelt:</b> Alarme in der Pause gehen nicht verloren: die nächste Meldung sagt «+N weitere in M Min.» und zeigt unten bis 4 kleine Bilder.</li>'
           '<li><b>Zonen-Name:</b> Hat eine Zone einen eigenen Namen, steht er in der Meldung («Person bei «Eingangstür»»).</li>'
           '<li><b>Clip</b> (ab Werk aus): 3–5 s kleines Video kurz nach dem Bild (ntfy, Telegram).</li>'
           '<li><b>Bilder bleiben zu Hause</b> (ab Werk aus): Meldungen nur mit Text und Link; Bild und Clip bleiben auf dem MoveEye (zu Hause und über den Fernzugang).</li>'
           '</ul></section>\n'),
    "en": ('<section id="false-pushes" data-icon="🎯"><h2>False alarms and pushes</h2><ul>'
           '<li><b>False alarm spots:</b> when you tap «False alarm» or «What was it? → Nothing», MoveEye notes the spot in the picture. '
           'After 3 false alarms there within 7 days MoveEye asks <i>once</i>: «False alarms often come from here – ignore this spot from now on?». '
           '«Yes, ignore» adds an ignore zone (persons only) for this field, «No» leaves everything as it is. Nothing is ever ignored without your answer.</li>'
           '<li><b>Wind protection:</b> in strong wind, movement in areas where leaves move all the time needs the AI or the thermal camera – or has to last 6 s longer.</li>'
           '<li><b>Bundled:</b> alarms during the pause are not lost: the next message says «+N more in M min» and shows up to 4 small pictures below.</li>'
           '<li><b>Zone name:</b> when a zone has its own name, the message says it («Person at «Entrance»»).</li>'
           '<li><b>Clip</b> (off by default): a small 3–5 s video right after the picture (ntfy, Telegram).</li>'
           '<li><b>Pictures stay at home</b> (off by default): messages with text and a link only; picture and clip stay on MoveEye (at home and via remote access).</li>'
           '</ul></section>\n'),
    "fr": ('<section id="false-pushes" data-icon="🎯"><h2>Fausses alarmes et notifications</h2><ul>'
           '<li><b>Endroits de fausses alarmes :</b> quand tu touches «Fausse alarme» ou «Qu’est-ce que c’était ? → Rien», MoveEye note l’endroit dans l’image. '
           'Après 3 fausses alarmes en 7 jours, MoveEye demande <i>une fois</i> s’il faut ignorer cet endroit. «Oui, ignorer» ajoute une zone ignorée (personnes seulement), '
           '«Non» laisse tout tel quel. Rien n’est jamais ignoré sans ta réponse.</li>'
           '<li><b>Protection contre le vent :</b> par vent fort, un mouvement là où les feuilles bougent sans cesse a besoin de l’IA ou de la caméra thermique – ou doit durer 6 s de plus.</li>'
           '<li><b>Regroupé :</b> les alarmes pendant la pause ne se perdent pas : le message suivant dit «+N autres en M min» avec jusqu’à 4 petites images.</li>'
           '<li><b>Nom de la zone :</b> si une zone a un nom, il figure dans le message.</li>'
           '<li><b>Clip</b> (désactivé par défaut) : petite vidéo de 3–5 s juste après l’image (ntfy, Telegram).</li>'
           '<li><b>Les images restent à la maison</b> (désactivé par défaut) : messages avec texte et lien seulement ; image et clip restent sur MoveEye.</li>'
           '</ul></section>\n'),
    "it": ('<section id="false-pushes" data-icon="🎯"><h2>Falsi allarmi e notifiche</h2><ul>'
           '<li><b>Punti dei falsi allarmi:</b> quando tocchi «Falso allarme» o «Che cos’era? → Niente», MoveEye annota il punto nell’immagine. '
           'Dopo 3 falsi allarmi in 7 giorni MoveEye chiede <i>una volta</i> se ignorare quel punto. «Sì, ignora» aggiunge una zona ignorata (solo persone), '
           '«No» lascia tutto com’è. Niente viene mai ignorato senza la tua risposta.</li>'
           '<li><b>Protezione dal vento:</b> con vento forte, un movimento dove le foglie si muovono di continuo ha bisogno dell’IA o della termocamera – o deve durare 6 s in più.</li>'
           '<li><b>Raggruppati:</b> gli allarmi durante la pausa non vanno persi: il messaggio successivo dice «+N altri in M min» con fino a 4 piccole immagini.</li>'
           '<li><b>Nome della zona:</b> se una zona ha un nome, compare nel messaggio.</li>'
           '<li><b>Clip</b> (disattivata di fabbrica): piccolo video di 3–5 s subito dopo l’immagine (ntfy, Telegram).</li>'
           '<li><b>Le immagini restano a casa</b> (disattivato di fabbrica): messaggi solo con testo e link; immagine e clip restano su MoveEye.</li>'
           '</ul></section>\n'),
    "rm": ('<section id="false-pushes" data-icon="🎯"><h2>Alarms faussas e messadis</h2><ul>'
           '<li><b>Lieus dad alarms faussas:</b> sche ti tippas «Alarm fauss» u «Tge era quai? → Nagut», nota MoveEye il lieu en il maletg. '
           'Suenter 3 alarms faussas en 7 dis dumonda MoveEye <i>ina giada</i>, sch’il lieu duai vegnir ignorà. «Gea, ignorar» agiunta ina zona ignorada (mo persunas), '
           '«Na» lascha tut sco ch’i è. Senza tia resposta na vegn mai ignorà nagut.</li>'
           '<li><b>Protecziun cunter il vent:</b> cun vent ferm dovra in moviment là nua che la feglia sa mova adina l’IA u il maletg termic – u el sto durar 6 s pli ditg.</li>'
           '<li><b>Unì:</b> alarms durant la pausa na van betg a perder: il proxim messadi di «+N ulteriurs en M min» cun fin a 4 maletgs pitschens.</li>'
           '<li><b>Num da la zona:</b> sch’ina zona ha in num, stat el en il messadi.</li>'
           '<li><b>Clip</b> (deactivà da fabrica): pitschen video da 3–5 s curt suenter il maletg (ntfy, Telegram).</li>'
           '<li><b>Ils maletgs restan a chasa</b> (deactivà da fabrica): messadis mo cun text e colliaziun; maletg e clip restan sin MoveEye.</li>'
           '</ul></section>\n'),
}


def _help_fp(doc, lang):
    if 'id="false-pushes"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_FP[lang] + doc[i:] if i >= 0 else doc


_hp_en_fp = HELP_PAGE.find('<div lang="en">')
if _hp_en_fp > 0:
    HELP_PAGE = _help_fp(HELP_PAGE[:_hp_en_fp], "de") + _help_fp(HELP_PAGE[_hp_en_fp:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_fp(HELP_X[_L], _L)


# ---- self-test: one check for every point ------------------------------------------------------------------------------------
def fp_selftest():
    keep = {k: CFG.get(k) for k in ("fp_spot_learn", "wind_guard", "wind_guard_kmh", "push_bundle", "push_bundle_after", "push_zone_name",
                                    "push_clip", "push_clip_s", "push_clip_kb", "push_home_pics", "sim_on", "public_url", "lang",
                                    "msg_person_title", "notify_cooldown", "msg_icons")}
    keep_st = {k: STATE.get(k) for k in ("storm", "wind_level", "source_label")}
    keep_z = [dict(z) for z in ZONES]
    keep_fps = dict(FPS); keep_wg = dict(WG); keep_ctx = ALX.get("ctx")
    tmp = tempfile.mkdtemp(prefix="mw_fp_")
    _ls = log_event
    g = globals()
    sv = {k: g[k] for k in ("fp_spot_ask", "zones_set", "save_settings", "pb_dir", "alx_base")}
    try:
        g["log_event"] = lambda *a, **k: None
        g["save_settings"] = lambda *a, **k: None
        CFG.update(sim_on=False, lang="de", fp_spot_learn=True, msg_person_title="", msg_icons=True)
        STATE["source_label"] = "Pi-Kamera 0"
        FPS.update(file=os.path.join(tmp, "stellen.json"), data=None)
        asked = []
        g["fp_spot_ask"] = lambda key, e: asked.append((key, e["tok"])) or True
        g["alx_base"] = lambda: "https://moveeye.example"
        # 1: the factory default comes from one line, the switch exists
        assert DEFAULTS["alarm_confirm2"] is ALARM_CONFIRM2_WERK and FACTORY_CFG["alarm_confirm2"] is ALARM_CONFIRM2_WERK
        assert any(x[1] == "alarm_confirm2" for x in TOGGLES)
        # 2: spots - 3 false alarms in the same field within 7 days -> one question; a 4th -> no second one
        now = time.time()
        bx = lambda x, y: {"boxes": [[x, y, 0.06, 0.2]], "src": "Pi-Kamera 0", "srv": False}
        for i, (x, y) in enumerate([(0.10, 0.60), (0.12, 0.62), (0.11, 0.58)]):
            fp_spot_note(dict(bx(x, y), id="20261101_10000%d" % i, stamp="20261101_10000%d" % i, t=now - 3600 * (i + 1)), now)
        assert len(asked) == 1, asked
        key, tok = asked[0]
        assert key.endswith("|-|0,3"), key
        fp_spot_note(dict(bx(0.11, 0.60), id="20261101_100009", stamp="20261101_100009", t=now - 60), now)
        fp_spot_note(dict(bx(0.11, 0.60), id="20261101_100009", stamp="20261101_100009", t=now - 60), now)   # the same alarm twice
        assert len(asked) == 1 and len(fp_load()["notes"]) == 4, "asked once, the same alarm counted once"
        fp_spot_note(dict(bx(0.8, 0.2), id="20261101_100010", stamp="20261101_100010", t=now), now)
        assert len(asked) == 1, "other field: no question"
        FPS["data"] = None; fp_load()                    # survives a restart
        old_notes = [n for n in fp_load()["notes"] if n["key"] == key]
        assert len(old_notes) == 4 and fp_open(fp_by_tok(tok)[1])
        for n in fp_load()["notes"]:                     # older than 7 days: no question
            n["t"] -= 8 * 86400
        fp_load()["asked"].clear()
        assert fp_spot_due(key, now) is None
        for n in fp_load()["notes"]:
            n["t"] += 8 * 86400
        assert fp_spot_due(key, now) and fp_spot_check(key, now)
        tok = fp_pending(now)[0]["tok"]
        CFG["sim_on"] = True
        assert fp_spot_note(dict(bx(0.5, 0.5), id="x1", stamp="x1"), now) is None, "never in the simulation"
        CFG["sim_on"] = False
        made = []
        g["zones_set"] = lambda lst: made.append(lst) or (True, "")
        assert fp_spot_answer(tok, "maybe")[0] is False
        STATE["source_label"] = "USB 1"
        assert fp_spot_answer(tok, "yes")[0] is False and not made, "other camera: no zone"
        STATE["source_label"] = "Pi-Kamera 0"
        ok, txt = fp_spot_answer(tok, "yes")
        assert ok and made and made[-1][-1]["mode"] == "ignore" and made[-1][-1]["kinds"] == "person", made
        assert made[-1][-1]["points"] == [[0.0, 0.75], [0.1667, 0.75], [0.1667, 1.0], [0.0, 1.0]], made[-1][-1]["points"]
        assert fp_spot_answer(tok, "no")[0] is False, "a key works once"
        assert fp_spot_due(key, now + 40 * 86400) is None, "after «yes»: never again"
        fp_load()["asked"][key].update(ans="no", t=now - 31 * 86400)
        assert fp_spot_due(key, now), "after «no»: again after 30 days"
        ntf = alx_ntfy_actions({"fs_tok": tok})
        assert ntf.count("http, ") == 2 and f"/na/fs/{tok}/yes" in ntf and "Ja ignorieren" in ntf, ntf
        tg = alx_telegram_markup({"fs_tok": tok})
        assert [b["text"] for b in tg["inline_keyboard"][0]] == ["Ja, ignorieren", "Nein"]
        # 3: wind protection - a flickering field + strong wind: motion alone held, AI / heat / long enough pass
        WG.update(occ=None, t=0.0, seen={}, held=0, passed=0, log_t=0.0)
        fg = np.zeros((270, 480), np.uint8); fg[0:90, 0:120] = 255                  # leaves in the upper left all the time
        for i in range(400):
            wg_feed(fg, [], now - 120 + i * 0.3)
        assert wg_veg(0.1, 0.1) and not wg_veg(0.8, 0.8), WG["occ"]

        class _Ai:
            boxes = []

        class _W:
            _proc_size = (480, 270); ai = _Ai(); last_warm = 0.0
        P = [(20, 10, 30, 60)]
        CFG["wind_guard"] = True
        STATE.update(storm={"gust": 20, "wind": 5}, wind_level="calm")
        assert wind_guard_filter(_W(), P, now) == P, "no strong wind: as before"
        STATE["storm"] = {"gust": 55, "wind": 30}
        assert wind_guard_filter(_W(), P, now) == [] and WG["held"] == 1, "strong wind, plant field, motion only: held"
        assert wind_guard_filter(_W(), [(380, 180, 30, 60)], now) == [(380, 180, 30, 60)], "outside the plant fields: as before"
        _W.ai.boxes = [(22, 12, 28, 58, 0.8)]
        assert wind_guard_filter(_W(), P, now + 1) == P, "the AI sees a person: alarm"
        _W.ai.boxes = []; _W.last_warm = now + 1
        assert wind_guard_filter(_W(), P, now + 1.5) == P, "heat: alarm"
        _W.last_warm = 0.0
        held = [wind_guard_filter(_W(), P, now + 10 + dt) for dt in (0.0, 1.5, 3.0, 4.5)]
        assert held == [[]] * 4 and wind_guard_filter(_W(), P, now + 16.1) == P, "6 s longer: counts"
        CFG["wind_guard"] = False
        assert wind_guard_filter(_W(), P, now + 20) == P, "switch off: as before"
        CFG["wind_guard"] = True; STATE["storm"] = {}; STATE["wind_level"] = "storm"
        assert wg_wind().startswith("picture"), "without a wind meter: the picture"
        # 4: bundling text and strip
        FPB.update(n=0, first=0.0, items=[])
        fr = np.full((270, 480, 3), 90, np.uint8)
        for i in range(6):
            fp_bundle_add(fr, now - 240 + i * 30)
        p = {"event": "person", "persons": 1, "time": "2026-11-07T22:10:00", "more": 6}
        ok_, buf = cv2.imencode(".jpg", fr)
        j2 = fp_bundle_take(p, buf.tobytes(), now)
        im2 = cv2.imdecode(np.frombuffer(j2, np.uint8), cv2.IMREAD_COLOR)
        assert p["more_min"] == 4 and im2.shape[1] == 480 and im2.shape[0] > 270 and FPB["n"] == 0, (p, im2.shape)
        s = push_short(p)
        assert "+6 weitere in 4 Min." in s["text"] and "+6 weitere ·" not in s["text"] + " ·", s
        assert "(+6 weitere Erkennungen in 4 Min.)" in push_long(p)
        assert len(fp_pick4([(i, i) for i in range(8)])) == 4
        # 5: zone name
        ZONES[:] = [{"id": "aaaaaaaa", "name": "Eingangstür", "mode": "only", "points": [[0, 0.5], [0.5, 0.5], [0.5, 1], [0, 1]]},
                    {"id": "bbbbbbbb", "name": "Zone 2", "mode": "only", "points": [[0, 0.6], [0.3, 0.6], [0.3, 1], [0, 1]]},
                    {"id": "cccccccc", "name": "Nachbar", "mode": "privacy", "points": [[0, 0], [1, 0], [1, 1], [0, 1]]}]
        assert fp_zone_name([[0.1, 0.5, 0.1, 0.3]]) == "Eingangstür" and fp_zone_name([[0.7, 0.1, 0.1, 0.2]]) == ""
        s = push_short({"event": "person", "persons": 1, "time": "2026-11-07T22:10:00", "zone": "Eingangstür"})
        assert "Person bei «Eingangstür»" in s["title"], s
        s = push_short({"event": "person", "persons": 2, "time": "2026-11-07T22:10:00", "zone": "Eingangstür"})
        assert "2 Personen bei «Eingangstür»" in s["title"], s
        CFG["push_zone_name"] = False
        assert "Eingangstür" not in push_short({"event": "person", "persons": 1, "time": "2026-11-07T22:10:00", "zone": "Eingangstür"})["title"]
        CFG["push_zone_name"] = True
        # 6: clip - small enough, or none at all
        frames = [np.random.RandomState(i).randint(0, 255, (180, 320, 3), np.uint8) for i in range(24)]
        try:
            import PIL  # noqa: F401
            have_pil = True
        except ImportError:
            have_pil = False
        d_, f_, w_ = fp_clip_make(frames, 6.0, "gif", 3000)
        assert (d_[:6] in (b"GIF89a", b"GIF87a") and len(d_) <= 3000 * 1024) or (not have_pil and d_ == b""), len(d_)
        d_, f_, w_ = fp_clip_make(frames, 6.0, "gif", 50)
        assert d_ == b"" or len(d_) <= 50 * 1024, "never above the limit"
        m_, f_, w_ = fp_clip_make([np.full((180, 320, 3), 60, np.uint8)] * 24, 6.0, "mp4", 800)
        assert m_ == b"" or (len(m_) <= 800 * 1024 and m_[4:8] == b"ftyp"), len(m_)
        if shutil.which("ffmpeg"):
            assert m_, "ffmpeg is there: a clip"
        # 7: pictures stay at home - the link instead of the picture
        g["pb_dir"] = lambda: os.path.join(tmp, "pb")
        CFG["push_home_pics"] = True
        p = {"event": "person", "persons": 1, "time": "2026-11-07T22:10:00", "link": "https://moveeye.example/recordings"}
        fp_home(p, b"\xff\xd8jpg")
        assert PB_RE.match(p["home_id"]) and p["link"] == "https://moveeye.example/pb/" + p["home_id"], p
        assert os.path.isfile(os.path.join(tmp, "pb", p["home_id"] + ".jpg"))
        assert sx_push_jpg(b"x") is None and "🏠 Bild zu Hause" in push_short(p)["text"]
        CFG["push_home_pics"] = False
        q = {"event": "person", "persons": 1, "time": "2026-11-07T22:10:00", "link": "x"}
        fp_home(q, b"jpg")
        assert "home_id" not in q and q["link"] == "x" and sx_push_jpg(b"x") == b"x", "off: as before"
        # settings, translations, pages
        for k in ("fp_spot_learn", "wind_guard", "push_bundle", "push_bundle_after", "push_zone_name", "push_clip", "push_home_pics"):
            assert any(x[1] == k for x in TOGGLES), k
        assert DEFAULTS["push_clip"] is False and DEFAULTS["push_home_pics"] is False and DEFAULTS["push_bundle"] is True
        for k, v in _HX_FP.items():
            assert len(v) == 4 and all(v) and k in DE and all(k in TRX[L] for L in ("fr", "it", "rm")), k
        assert "fp-ask" in WEB_PAGE or not WEB_PAGE.strip()
        assert HELP_PAGE.count('<section id="false-pushes"') in (0, 2)
    finally:
        g.update(sv)
        g["log_event"] = _ls
        CFG.update(keep); STATE.update(keep_st); ZONES[:] = keep_z
        FPS.clear(); FPS.update(keep_fps); WG.clear(); WG.update(keep_wg); ALX["ctx"] = keep_ctx
        FPB.update(n=0, first=0.0, items=[])
        shutil.rmtree(tmp, ignore_errors=True)
    return "Fehlalarme und Pushes: spots (3 in 7 days, once, yes/no), wind protection, bundle «+N in M min» + strip, zone name, clip limit, pictures at home"


SELFTEST_EXTRA.append(("False alarms and pushes: spots, wind protection, bundling, zone name, clip, pictures at home (639zy)", fp_selftest))
