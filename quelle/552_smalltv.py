#@ MoveEye – Teil 552: Zusatz-Bildschirm GeekMagic SmallTV Ultra (Status, Alarmbild, Spiel-Anzeige, Nacht dunkel + rot, mehrere Bildschirme, Suche im Netz, virtueller SmallTV des Simulators). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Plan Daniel 30.10.2026 (docs/SmallTV_Anzeige_Plan.md). Gerät: GeekMagic SmallTV Ultra, Firmware Ultra-V9.0.40, 240×240,
# ESP8266, HTTP ohne Passwort. Was MoveEye zeigt (pro Bildschirm wählbar):
#   status  Zustand Aus / Wachsam / Voll, Akku (auch der 🧪 simulierte), letzte Meldung, «Stand» (Uhrzeit)
#   alarm   Bildausschnitt mit «Fuchs · 91 % · 6 m» (Tiere); Personen: Standard nur Symbol + Text, Schalter «Bild auch bei
#           Personen» (stv_person_pic); kurz hell, dann zurück
#   game    während einer Runde im 3D-Simulator: Countdown / Restzeit, Punkte, «Erwischt!» (Simulator: «game_live» in der
#           Antwort auf /state, simulator3d/scripts/smalltv.gd)
# Nachts (is_dark: Simulator oder Sonnenzeit) gedimmt und rot wie die Rotlicht-Ansicht (578), bei Alarm kurz hell.
# Schonung des Geräts: ein Bildschirm = ein Faden, eine Anfrage nach der anderen (Pause 0,3 s), hochladen nur bei
# Änderung (Hash), immer dieselben zwei Dateien me_a.jpg / me_b.jpg abwechselnd (das neue Bild ist ganz da, bevor es
# gezeigt wird), höchstens ein Bild alle stv_gap_s (Alarm sofort), die Uhr nur alle stv_clock_min Minuten neu.
# Firmware-Macken: Upload antwortet manchmal «400», obwohl gespeichert -> /filelist prüfen; langsame Antworten -> 30 s.
# Mit dem Simulator (3D-4.19) kommt der virtuelle SmallTV von selbst dazu (🧪, Adresse = Simulator, gleiche Schnittstelle).
# Einstellungen + Fenster: 599b, Übersetzungen + Anleitung: 562.
# ----------------------------------------------------------------------------
STV_CFG = {"stv_on": True, "stv_list": [], "stv_sim": {"on": True, "status": True, "alarm": True, "game": True, "brt": 60},
           "stv_person_pic": False, "stv_animals": True, "stv_night": True, "stv_night_brt": 10, "stv_alarm_s": 60,
           "stv_bright_s": 20, "stv_gap_s": 5, "stv_clock_min": 10}
for _k, _v in STV_CFG.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
STV_MAX = 6                                    # höchstens so viele Bildschirme
STV_SIZE = 240
STV_NAMES = ("me_a.jpg", "me_b.jpg")
STV_HOTSPOT = "GIFTV"                          # das eigene WLAN des SmallTV beim Einrichten
STV_SETUP_URL = "http://192.168.4.1"
STV = {"lock": threading.Lock(), "devs": {}, "alarm": None, "seen_animal": 0.0, "game": None, "game_t": 0.0, "caught": None,
       "k": {}, "sim_ok": None, "sim_t": 0.0, "scan": {"busy": False, "found": [], "t": 0.0, "msg": ""}, "started": False,
       "renders": {}, "msg_seq": 0}
_STV_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # im eigenen Netz: nie über einen Proxy
_STV_ANIMAL_H = {"cat": 0.3, "dog": 0.55, "fox": 0.4, "bird": 0.2, "horse": 1.6, "sheep": 0.8, "cow": 1.4, "bear": 1.0, "deer": 1.0,
                 "boar": 0.8, "hedgehog": 0.15, "badger": 0.3, "hare": 0.35, "elephant": 2.8, "zebra": 1.4, "giraffe": 4.5}


# ---- the list of displays -----------------------------------------------------------------------------------------------
def stv_norm_addr(a):
    """«192.168.1.77», «smalltv.local», «http://host:port» -> «http://host[:port]» or '' (only plain http: the device has no https)"""
    a = str(a or "").strip().rstrip("/")
    if not a:
        return ""
    if not a.startswith(("http://", "https://")):
        a = "http://" + a
    if not re.fullmatch(r"http://[A-Za-z0-9.\-]{1,80}(:\d{1,5})?", a):
        return ""
    return a


def _stv_clean(e):
    if not isinstance(e, dict):
        return None
    addr = stv_norm_addr(e.get("addr"))
    sid = str(e.get("id") or "")
    if not addr or not re.fullmatch(r"[0-9a-f]{6,12}", sid):
        return None
    try:
        brt = max(0, min(100, int(e.get("brt", 60))))
    except (TypeError, ValueError):
        brt = 60
    return {"id": sid, "name": str(e.get("name") or "SmallTV")[:30], "addr": addr, "on": bool(e.get("on", True)),
            "status": bool(e.get("status", True)), "alarm": bool(e.get("alarm", True)), "game": bool(e.get("game", True)), "brt": brt}


def stv_entries(with_sim=True):
    """the displays: the saved ones + the virtual one of the simulator (🧪, only while connected and it answers)"""
    out = [x for x in (_stv_clean(e) for e in (CFG.get("stv_list") or [])[:STV_MAX]) if x]
    if with_sim and stv_sim_ok():
        s = CFG.get("stv_sim") if isinstance(CFG.get("stv_sim"), dict) else {}
        try:
            brt = max(0, min(100, int(s.get("brt", 60))))
        except (TypeError, ValueError):
            brt = 60
        out.append({"id": "sim", "name": "Simulator", "addr": sim_base(), "sim": True, "on": bool(s.get("on", True)),
                    "status": bool(s.get("status", True)), "alarm": bool(s.get("alarm", True)), "game": bool(s.get("game", True)), "brt": brt})
    return out


def stv_sim_ok():
    """the simulator is connected and has the virtual SmallTV (3D-4.19: GET /v.json) - checked at most every 30 s"""
    if not (CFG.get("sim_on") and simval_live()):
        return False
    now = time.time()
    if STV["sim_ok"] is None or now - STV["sim_t"] > 30:
        STV["sim_t"] = now
        ok = False
        try:
            d = _stv_json(sim_base(), "/v.json", 3.0)
            ok = stv_is_geekmagic(d) and bool(d.get("sim"))
        except Exception:
            ok = False
        if ok != STV["sim_ok"] and STV["sim_ok"] is not None:
            log_event("sys", "SmallTV: virtual display of the simulator " + ("found" if ok else "gone"))
        STV["sim_ok"] = ok
    return bool(STV["sim_ok"])


def stv_is_geekmagic(d):
    """an answer of /v.json that looks like a GeekMagic SmallTV (Ultra, Pro …)"""
    if not isinstance(d, dict):
        return False
    s = " ".join(str(d.get(k, "")) for k in ("m", "model", "v", "version", "name")).lower()
    return any(w in s for w in ("smalltv", "geekmagic", "ultra-v", "giftv"))


def stv_edit(action, d, who="web"):
    """add / remove / update a display -> (ok, error)"""
    lst = [x for x in (_stv_clean(e) for e in (CFG.get("stv_list") or [])) if x]
    sid = str(d.get("id") or "")
    if action == "add":
        addr = stv_norm_addr(d.get("addr"))
        if not addr:
            return False, "invalid address"
        if any(x["addr"] == addr for x in lst):
            return False, "this display is already in the list"
        if len(lst) >= STV_MAX:
            return False, "too many displays"
        import secrets as _sec
        e = _stv_clean({"id": _sec.token_hex(4), "name": str(d.get("name") or "").strip() or "SmallTV", "addr": addr})
        lst.append(e)
        CFG["stv_list"] = lst
        save_settings()
        log_event("web", f"SmallTV added: {e['name']} ({addr}, {who})")
        stv_kick()
        return True, ""
    if sid == "sim":
        s = dict(CFG.get("stv_sim") if isinstance(CFG.get("stv_sim"), dict) else {})
        if action != "update":
            return False, "the display of the simulator comes by itself"
        f = str(d.get("field") or "")
        if f in ("on", "status", "alarm", "game"):
            s[f] = bool(d.get("value"))
        elif f == "brt":
            s[f] = max(0, min(100, int(float(d.get("value") or 0))))
        else:
            return False, "unknown field"
        CFG["stv_sim"] = s
        save_settings()
        stv_kick()
        return True, ""
    e = next((x for x in lst if x["id"] == sid), None)
    if e is None:
        return False, "unknown display"
    if action == "remove":
        lst = [x for x in lst if x["id"] != sid]
        CFG["stv_list"] = lst
        save_settings()
        log_event("web", f"SmallTV removed: {e['name']} ({who})")
        return True, ""
    if action == "update":
        f = str(d.get("field") or "")
        v = d.get("value")
        if f in ("on", "status", "alarm", "game"):
            e[f] = bool(v)
        elif f == "brt":
            try:
                e[f] = max(0, min(100, int(float(v))))
            except (TypeError, ValueError):
                return False, "not a number"
        elif f == "name":
            e[f] = str(v or "").strip()[:30] or "SmallTV"
        elif f == "addr":
            a = stv_norm_addr(v)
            if not a:
                return False, "invalid address"
            e[f] = a
        else:
            return False, "unknown field"
        CFG["stv_list"] = lst
        save_settings()
        stv_kick()
        return True, ""
    return False, "unknown action"


# ---- the device: plain HTTP, one request after the other -------------------------------------------------------------
def _stv_req(base, path, data=None, ctype=None, timeout=10.0):
    """(HTTP code, body bytes); a code like 400 is returned (not raised) - the firmware says 400 although it worked"""
    h = {"User-Agent": "MoveEye"}
    if ctype:
        h["Content-Type"] = ctype
    req = urllib.request.Request(base + path, data=data, headers=h, method="POST" if data is not None else "GET")
    try:
        with _STV_OPENER.open(req, timeout=timeout) as r:
            return r.status, r.read(200000)
    except urllib.error.HTTPError as e:
        try:
            b = e.read(2000)
        except Exception:
            b = b""
        return e.code, b


def _stv_json(base, path, timeout=5.0):
    code, b = _stv_req(base, path, timeout=timeout)
    if code != 200:
        raise OSError(f"HTTP {code}")
    return json.loads(b.decode("utf-8", "replace") or "{}")


def stv_files(base, timeout=10.0):
    """the names in /image/ (the firmware answers with a little HTML list)"""
    code, b = _stv_req(base, "/filelist?dir=/image/", timeout=timeout)
    if code != 200:
        return None
    return sorted(set(re.findall(r"([A-Za-z0-9_\-.]{1,60}\.(?:jpg|jpeg|gif|png))", b.decode("utf-8", "replace"), re.I)))


def stv_upload(base, name, jpg, timeout=30.0):
    """POST /doUpload?dir=/image/ (multipart, field «file») -> (ok, note). HTTP 400 or a timeout: the file list decides."""
    import secrets as _sec
    bd = "----MoveEye" + _sec.token_hex(8)
    body = (f"--{bd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() \
        + jpg + f"\r\n--{bd}--\r\n".encode()
    try:
        code, _b = _stv_req(base, "/doUpload?dir=/image/", body, "multipart/form-data; boundary=" + bd, timeout)
    except Exception as e:
        code, note = 0, str(e)[:80]
    else:
        note = f"HTTP {code}"
    if code == 200:
        return True, ""
    time.sleep(0.3)
    try:
        fl = stv_files(base)
    except Exception:
        fl = None
    if fl is not None and name in fl:
        return True, note + " – " + "stored anyway (firmware)"
    return False, note


class StvDev:
    """one display: its own thread; the manager (stv_loop) puts the wanted picture + brightness, the thread sends it"""
    def __init__(self, sid):
        self.id = sid
        self.ev = threading.Event()
        self.want = None              # {"jpg", "sig", "kind", "brt", "now": send at once}
        self.sent_sig = None
        self.sent_brt = None
        self.shown = ""               # the file name now on the screen
        self.last_up = 0.0
        self.theme_t = 0.0
        self.ups = 0
        self.bytes = 0
        self.errs = 0
        self.jpg = None               # the last picture that went out (for the page and the window)
        self.kind = ""
        self.h = {"ok": None, "t": 0.0, "fw": "", "model": "", "free": None, "total": None, "err": "", "note": "", "sent_t": 0.0}
        self.alive = True
        self.th = threading.Thread(target=self.run, daemon=True, name="smalltv-" + sid)
        self.th.start()

    def entry(self):
        return next((e for e in stv_entries() if e["id"] == self.id), None)

    def check(self, base, force=False):
        """v.json + space.json (health); at most every 2 minutes unless forced"""
        if not force and time.time() - self.h["t"] < 120:
            return
        self.h["t"] = time.time()
        try:
            v = _stv_json(base, "/v.json", 6.0)
            time.sleep(0.25)
            self.h.update(ok=stv_is_geekmagic(v) or bool(v), fw=str(v.get("v") or v.get("version") or "")[:40],
                          model=str(v.get("m") or v.get("model") or "")[:40], err="" if stv_is_geekmagic(v) else "not a GeekMagic SmallTV?")
            try:
                s = _stv_json(base, "/space.json", 6.0)
                self.h.update(free=int(s.get("free")) if s.get("free") is not None else None, total=int(s.get("total")) if s.get("total") is not None else None)
            except Exception:
                pass
        except Exception as e:
            if self.h["ok"] is not False:
                log_event("sys", f"SmallTV {base}: not reachable ({str(e)[:60]})")
            self.h.update(ok=False, err=str(e)[:80] or "not reachable")

    def send(self, base, w):
        if time.time() - self.theme_t > 600:            # the photo album (after a restart the device shows the clock)
            for p in ("/set?theme=3", "/set?autoplay=0"):
                try:
                    _stv_req(base, p, timeout=10.0)
                except Exception:
                    pass
                time.sleep(0.3)
            self.theme_t = time.time()
        name = STV_NAMES[1] if self.shown == STV_NAMES[0] else STV_NAMES[0]   # the other one: the new picture is complete before it shows
        ok, note = stv_upload(base, name, w["jpg"])
        time.sleep(0.3)
        if ok:
            code, _b = _stv_req(base, "/set?img=" + urllib.parse.quote("/image//" + name, safe="/"), timeout=10.0)
            ok = code == 200
            note = note or ("" if ok else f"show: HTTP {code}")
        if ok:
            self.shown = name; self.sent_sig = w["sig"]; self.ups += 1; self.bytes += len(w["jpg"]); self.jpg = w["jpg"]; self.kind = w["kind"]
            self.h.update(ok=True, err="", note=note, sent_t=time.time())
            if note:
                self.h["note"] = note
        else:
            self.errs += 1
            self.h.update(err=note or "upload failed")
            if self.h["ok"] is not False:
                log_event("sys", f"SmallTV {base}: picture not sent ({note})"[:160])
            self.h["ok"] = False
            self.theme_t = 0.0
        self.last_up = time.time()
        return ok

    def run(self):
        while self.alive:
            self.ev.wait(2.0)
            self.ev.clear()
            e = self.entry()
            if e is None:
                self.alive = False
                break
            base = e["addr"]
            try:
                self.check(base, force=self.h["ok"] is None)
                w = self.want
                if w is None or not e["on"]:
                    continue
                gap = max(5.0, float(CFG.get("stv_gap_s", 5) or 5))
                if self.h["ok"] is False and time.time() - self.last_up < 30 and not w.get("now"):
                    continue                              # not reachable: try again every 30 s
                if w["sig"] != self.sent_sig and (w.get("now") or time.time() - self.last_up >= gap):
                    self.send(base, w)
                    time.sleep(0.3)
                if w["brt"] != self.sent_brt:
                    code, _b = _stv_req(base, f"/set?brt={int(w['brt'])}", timeout=10.0)
                    if code == 200:
                        self.sent_brt = w["brt"]
                    time.sleep(0.3)
            except Exception as ex:
                self.errs += 1
                self.h.update(ok=False, err=str(ex)[:80])
                self.last_up = time.time()


def stv_kick():
    for d in list(STV["devs"].values()):
        d.ev.set()


# ---- what happens (hooks into the camera loop and the simulator link) --------------------------------------------------
_species_update_180 = species_update


# wraps: species_update
def species_update(objs, frame, pw, ph, t0):            # + 552: an animal -> alarm picture on the SmallTV
    try:
        stv_see_animals(objs, frame, pw, ph)
    except Exception:
        pass
    return _species_update_180(objs, frame, pw, ph, t0)


def stv_see_animals(objs, frame, pw, ph):
    if not (CFG.get("stv_on") and CFG.get("stv_animals")) or frame is None:
        return
    an = [o for o in objs if COCO_LABELS.get(o[5]) in ANIMALS]
    now = time.time()
    if not an:
        return
    new_visit = now - STV["seen_animal"] > 30.0           # a new visit: nothing seen for 30 s
    STV["seen_animal"] = now
    if not (is_armed() or kopf_wild_active()) or not stv_entries():
        return
    o = max(an, key=lambda b: b[2] * b[3])
    sp = species_for(tuple(o[:4]))
    lab = sp[0] if sp else COCO_LABELS.get(o[5], "animal")
    conf = float(sp[1]) if sp else float(o[4])
    a = STV["alarm"]
    if not new_visit and a and a.get("kind") == "animal" and (a.get("label") == lab or now - a["t"] < float(CFG.get("stv_alarm_s", 60))):
        return
    dist = None
    try:
        dm = person_dist_m(float(o[3]), ph)
        if dm:
            dist = dist_round(dm * _STV_ANIMAL_H.get(str(lab).lower(), 0.5) / PERSON_H_M)
    except Exception:
        dist = None
    stv_alarm("animal", lab, conf, dist, _stv_crop(frame, o[:4], pw, ph))


def _stv_crop(frame, box, pw, ph):
    """a piece of the picture around the box in the shape of the picture area of the alarm screen (240 × 176), a copy"""
    try:
        H, W = frame.shape[:2]
        sx, sy = W / float(pw), H / float(ph)
        x, y, w, h = box[0] * sx, box[1] * sy, box[2] * sx, box[3] * sy
        asp = STV_SIZE / float(STV_SIZE - 64)
        cw = max(w * 1.5 + 16, h * 1.5 * asp + 16)
        cw = min(cw, W, H * asp)
        ch = cw / asp
        cx, cy = x + w / 2, y + h / 2
        x0, y0 = int(max(0, min(W - cw, cx - cw / 2))), int(max(0, min(H - ch, cy - ch / 2)))
        return frame[y0:y0 + int(ch), x0:x0 + int(cw)].copy()
    except Exception:
        return None


_alarm_ctx_note_066 = alarm_ctx_note


# wraps: alarm_ctx_note
def alarm_ctx_note(w, stamp, snap, frame, persons):     # + 552: a person alarm -> the SmallTV (symbol, or the picture if wanted)
    try:
        if CFG.get("stv_on") and stv_entries():
            crop = None
            if CFG.get("stv_person_pic") and persons and frame is not None:
                pw, ph = getattr(w, "_proc_size", None) or (int(CFG["proc_width"]), 0)
                if pw and ph:
                    b = max(persons, key=lambda b_: b_[2] * b_[3])
                    crop = _stv_crop(frame, b[:4], pw, ph)
            dist = None
            try:
                bst = ERK.get("best")
                if bst and time.time() - ERK["t"] < 6:
                    dist = int(bst["m"])
            except Exception:
                dist = None
            stv_alarm("person", "person", None, dist, crop, n=len(persons))
    except Exception as e:
        log_event("sys", f"SmallTV: {e}"[:160])
    return _alarm_ctx_note_066(w, stamp, snap, frame, persons)


def stv_alarm(kind, label, conf, dist, crop, n=1):
    if kind == "person" and _stv_playing(time.time()):
        return                                             # a game round: the players are the persons (the game shows «Erwischt!»)
    STV["alarm"] = {"t": time.time(), "kind": kind, "label": str(label), "conf": conf, "dist": dist, "crop": crop, "n": int(n),
                    "clock": sim_now().strftime("%H:%M")}
    log_event("sys", f"SmallTV: alarm picture ({kind} {label})")
    STV["wake"] = True


_simvals_take_285 = simvals_take


# wraps: simvals_take
def simvals_take(rep):                                    # + 552: the game of the simulator for the SmallTV (3D-4.19 «game_live»)
    _simvals_take_285(rep)
    try:
        g = rep.get("game_live")
        g = g if isinstance(g, dict) else None
        if g is not None:
            for p in g.get("players") or []:            # «Erwischt!»: somebody was caught since the last answer
                nm = str(p.get("n", ""))[:20]
                k = int(p.get("k", 0) or 0)
                if g.get("round") == "play" and nm in STV["k"] and k > STV["k"][nm]:
                    STV["caught"] = (time.time(), nm)
                STV["k"][nm] = k
            if g.get("round") in ("lobby", "countdown"):
                STV["k"] = {str(p.get("n", ""))[:20]: int(p.get("k", 0) or 0) for p in g.get("players") or []}
        if g is not None and g.get("round") == "end":
            if not (STV["game"] or {}).get("round") == "end":
                STV["end_t"] = time.time()             # the end screen stays 60 s, then the status again
        STV["game"] = g
        STV["game_t"] = time.time()
    except Exception:
        pass


_msglog_add_065 = msglog_add


# wraps: msglog_add
def msglog_add(title, text, ev, jpg=None, status="sent", where=""):    # + 552: «last message» on the status picture
    _msglog_add_065(title, text, ev, jpg, status, where)
    STV["msg_seq"] += 1


# ---- the pictures (PIL, 240 × 240) --------------------------------------------------------------------------------------
def _stv_txt(s):
    """the fonts have no colour emojis: away with them (and with the joiners)"""
    s = "".join(ch for ch in str(s) if ord(ch) < 0x1F000 and ch not in "️‍⃣")
    return re.sub(r"\s+", " ", s).strip()


def _stv_fit(d, text, font, maxw):
    if d.textlength(text, font=font) <= maxw:
        return text
    while text and d.textlength(text + "…", font=font) > maxw:
        text = text[:-1]
    return text + "…"


def _stv_wrap(d, text, font, maxw, lines=2):
    words, out, cur = text.split(" "), [], ""
    for wd in words:
        t_ = (cur + " " + wd).strip()
        if d.textlength(t_, font=font) <= maxw:
            cur = t_
        else:
            if cur:
                out.append(cur)
            cur = wd
            if len(out) >= lines:
                break
    if cur and len(out) < lines:
        out.append(cur)
    if len(out) == lines and " ".join(out) != text:
        out[-1] = _stv_fit(d, out[-1] + " …", font, maxw)
    return [_stv_fit(d, x, font, maxw) for x in out]


def _stv_logo(size):
    try:
        from PIL import Image
        ic = cv2.imdecode(np.frombuffer(app_icon_png(64), np.uint8), cv2.IMREAD_COLOR)
        return Image.fromarray(cv2.cvtColor(ic, cv2.COLOR_BGR2RGB)).resize((size, size))
    except Exception:
        return None


def _stv_canvas():
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (STV_SIZE, STV_SIZE), (10, 14, 20))
    return im, ImageDraw.Draw(im)


def _stv_head(im, d, right=""):
    """top line: small logo + «MoveEye», right: the time"""
    lg = _stv_logo(22)
    if lg is not None:
        im.paste(lg, (8, 7))
    d.text((36, 8), "MoveEye", font=_font(17), fill=(232, 238, 245))
    if right:
        f = _font(17)
        d.text((STV_SIZE - 8 - d.textlength(right, font=f), 8), right, font=f, fill=(170, 185, 205))


def _stv_battery(d, x, y, pct, sim=False, charging=False):
    """a drawn battery (no emoji) with the percent; «SIM» for the simulated one"""
    w, h = 40, 20
    col = (63, 207, 107) if pct > 50 else (245, 154, 74) if pct > 20 else (255, 77, 77)
    d.rounded_rectangle((x, y, x + w, y + h), radius=4, outline=(200, 210, 225), width=2)
    d.rectangle((x + w + 1, y + 6, x + w + 4, y + h - 6), fill=(200, 210, 225))
    fw = int((w - 6) * max(0, min(100, pct)) / 100)
    if fw > 0:
        d.rectangle((x + 3, y + 3, x + 3 + fw, y + h - 3), fill=col)
    t_ = f"{int(pct)} %" + (" +" if charging else "")
    d.text((x + w + 10, y - 2), t_, font=_font(20), fill=(232, 238, 245))
    if sim:
        tx = x + w + 14 + d.textlength(t_, font=_font(20))
        d.rounded_rectangle((tx, y + 1, tx + 38, y + h - 1), radius=5, fill=(70, 50, 120))
        d.text((tx + 5, y + 2), "SIM", font=_font(14), fill=(225, 210, 255))


def _stv_person(d, cx, cy, s, col):
    """a person symbol (head + body), drawn"""
    r = s * 0.17
    d.ellipse((cx - r, cy - s * 0.48, cx + r, cy - s * 0.48 + 2 * r), fill=col)
    d.rounded_rectangle((cx - s * 0.27, cy - s * 0.1, cx + s * 0.27, cy + s * 0.5), radius=int(s * 0.18), fill=col)


def _stv_red(im):
    """night: red like the «Rotlicht-Ansicht» (578: --txt #c0392b on black) - nothing white that dazzles"""
    g = np.asarray(im.convert("L"), np.float32) / 255.0
    rgb = np.stack([g * 205 + 8, g * 34, g * 22], axis=-1).clip(0, 255).astype(np.uint8)
    from PIL import Image
    return Image.fromarray(rgb, "RGB")


def _stv_jpg(im, red=False):
    if red:
        im = _stv_red(im)
    import io
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    return b.getvalue()


def stv_level_name(lang=None):
    lv = protect_level()
    if lv == "off":
        return tr("Off", lang), (90, 100, 115)
    if STATE.get("arm_state") == "arming":
        return tr("Watchful", lang) if lv == "watch" else tr("Full", lang), (180, 140, 40)
    return (tr("Watchful", lang), (40, 120, 230)) if lv == "watch" else (tr("Full", lang), (215, 45, 45))


def stv_render_status(lang=None, red=False):
    im, d = _stv_canvas()
    now = sim_now()
    _stv_head(im, d, now.strftime("%H:%M"))
    name, col = stv_level_name(lang)
    if walktest_on():
        name, col = tr("Walk test", lang), (180, 140, 40)
    d.rounded_rectangle((8, 38, STV_SIZE - 8, 104), radius=14, fill=col)
    f = _font(40)
    while d.textlength(name, font=f) > STV_SIZE - 40 and getattr(f, "size", 0) > 22:
        f = _font(f.size - 2)
    d.text(((STV_SIZE - d.textlength(name, font=f)) / 2, 71 - f.size * 0.62), name, font=f, fill=(255, 255, 255))
    b = STATE.get("battery") or {}
    if b.get("on") and b.get("pct") is not None:
        _stv_battery(d, 12, 116, int(b["pct"]), bool(b.get("sim")), bool(b.get("charging")))
    else:
        d.text((12, 114), tr("Mains power", lang), font=_font(18, False), fill=(170, 185, 205))
    d.line((8, 146, STV_SIZE - 8, 146), fill=(40, 52, 68), width=1)
    try:
        m = (msglog_list(1) or [None])[0]
    except Exception:
        m = None
    if m:
        f1, f2 = _font(16), _font(16, False)
        tm = (now - timedelta(seconds=max(0.0, time.time() - float(m.get("t", 0))))).strftime("%H:%M")   # (the clock of the simulation too)
        tt = _stv_txt(m.get("title", "")).replace("[SIM] ", "")
        tt = re.sub(r"^MW-[A-Z]+ · ", "", tt)
        tt = re.sub(r"^[^:]{1,30}: ", "", tt) or tt                      # «MoveEye: Person» -> «Person» (the name is on top)
        d.text((10, 152), tm, font=f1, fill=(245, 154, 74))
        d.text((62, 152), _stv_fit(d, tt, f1, STV_SIZE - 72), font=f1, fill=(232, 238, 245))
        for i, ln in enumerate(_stv_wrap(d, _stv_txt(m.get("text", "")), f2, STV_SIZE - 20, 2)):
            d.text((10, 174 + i * 20), ln, font=f2, fill=(170, 185, 205))
    else:
        d.text((10, 160), tr("No messages yet", lang), font=_font(16, False), fill=(138, 155, 176))
    d.text((10, STV_SIZE - 22), _stv_fit(d, tr("as of", lang) + " " + now.strftime("%H:%M") + ("  ·  " + tr("simulator", lang) if CFG.get("sim_on") and simval_live() else ""),
                                         _font(14, False), STV_SIZE - 20), font=_font(14, False), fill=(110, 125, 145))
    return _stv_jpg(im, red)


def stv_render_alarm(a, lang=None, red=False):
    from PIL import Image
    im, d = _stv_canvas()
    band = 64
    kind = a.get("kind")
    if a.get("crop") is not None:
        c = a["crop"]
        try:
            pic = Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB))
            ph = STV_SIZE - band
            sw, sh = pic.size
            k = max(STV_SIZE / float(sw), ph / float(sh))
            pic = pic.resize((max(1, int(sw * k)), max(1, int(sh * k))))
            x0, y0 = (pic.size[0] - STV_SIZE) // 2, (pic.size[1] - ph) // 2
            im.paste(pic.crop((x0, y0, x0 + STV_SIZE, y0 + ph)), (0, 0))
        except Exception:
            pass
    else:
        d.rectangle((0, 0, STV_SIZE, STV_SIZE - band), fill=(40, 8, 10) if kind == "person" else (20, 28, 36))
        if kind == "person":
            _stv_person(d, STV_SIZE / 2, 92, 120, (255, 90, 90))
            if a.get("n", 1) > 1:
                d.text((STV_SIZE - 50, 20), f"×{a['n']}", font=_font(26), fill=(255, 200, 200))
        else:
            d.ellipse((70, 40, 170, 140), outline=(245, 154, 74), width=6)
    d.rectangle((0, 0, STV_SIZE - 1, STV_SIZE - 1), outline=(255, 60, 60), width=4)
    d.rectangle((0, STV_SIZE - band, STV_SIZE, STV_SIZE), fill=(160, 20, 24))
    lab = tr(a.get("label") or "", lang)
    lab = lab[:1].upper() + lab[1:]
    parts = [lab]
    if a.get("conf") is not None:
        parts.append(f"{int(round(float(a['conf']) * 100))} %")
    if a.get("dist"):
        parts.append(f"{int(a['dist'])} m")
    line = " · ".join(parts)
    f = _font(24)
    while d.textlength(line, font=f) > STV_SIZE - 16 and getattr(f, "size", 0) > 16:
        f = _font(f.size - 1)
    d.text(((STV_SIZE - d.textlength(line, font=f)) / 2, STV_SIZE - band + 6), line, font=f, fill=(255, 255, 255))
    sub = (tr("Alarm", lang) if kind == "person" else tr("Animal", lang)) + " · " + str(a.get("clock") or "")
    f2 = _font(16, False)
    d.text(((STV_SIZE - d.textlength(sub, font=f2)) / 2, STV_SIZE - 26), sub, font=f2, fill=(255, 215, 215))
    return _stv_jpg(im, red)


def stv_render_game(g, caught=None, lang=None, red=False):
    im, d = _stv_canvas()
    r = str(g.get("round") or "lobby")
    names = {"lobby": "Waiting for players", "countdown": "Get ready", "play": "Round running", "end": "Round over"}
    _stv_head(im, d, tr("Game", lang))
    d.text((10, 36), _stv_fit(d, tr(names.get(r, r), lang), _font(18), STV_SIZE - 20), font=_font(18), fill=(245, 154, 74))
    big = ""
    if r == "countdown":
        big = str(int(g.get("cd", 0) or 0))
    elif r == "play":
        left = int(g.get("left", 0) or 0)
        big = f"{left // 60}:{left % 60:02d}"
    elif r == "end":
        big = tr("End", lang)
    else:
        big = str(len(g.get("players") or []))
    fb = _font(64)
    while d.textlength(big, font=fb) > STV_SIZE - 20 and getattr(fb, "size", 0) > 28:
        fb = _font(fb.size - 4)
    if not caught:
        d.text(((STV_SIZE - d.textlength(big, font=fb)) / 2, 58), big, font=fb, fill=(255, 77, 77) if g.get("lm") and r == "play" else (232, 238, 245))
    rows = []
    if r == "end" and g.get("top"):
        rows = [(str(x.get("n", "")), int(x.get("pt", 0) or 0)) for x in g["top"][:3]]
    else:
        ps = sorted(g.get("players") or [], key=lambda p: -int(p.get("pt", 0) or 0))
        rows = [(str(p.get("n", "")) + (f"  {int(p.get('k', 0))}×" if int(p.get("k", 0) or 0) else ""), int(p.get("pt", 0) or 0)) for p in ps[:3]]
    y = 152 if caught else 140
    f = _font(18, False)
    for i, (n_, pt) in enumerate(rows):
        n_ = _stv_txt(n_)
        pts = str(pt)
        d.text((12, y), _stv_fit(d, f"{i + 1}. {n_}", f, STV_SIZE - 80), font=f, fill=(232, 238, 245))
        d.text((STV_SIZE - 12 - d.textlength(pts, font=_font(18)), y), pts, font=_font(18), fill=(63, 207, 107))
        y += 24
    if g.get("mw"):
        d.text((12, STV_SIZE - 22), _stv_fit(d, trf("MoveEye caught {n}", lang, n=int(g["mw"])), _font(14, False), STV_SIZE - 24), font=_font(14, False), fill=(138, 155, 176))
    if caught:
        d.rectangle((0, 60, STV_SIZE, 146), fill=(200, 24, 30))
        t1 = tr("Caught!", lang)
        f1 = _font(40)
        d.text(((STV_SIZE - d.textlength(t1, font=f1)) / 2, 64), t1, font=f1, fill=(255, 255, 255))
        nm = _stv_fit(d, _stv_txt(caught), _font(22), STV_SIZE - 20)
        d.text(((STV_SIZE - d.textlength(nm, font=_font(22))) / 2, 112), nm, font=_font(22), fill=(255, 230, 230))
    return _stv_jpg(im, red)


def stv_render_test(name, lang=None):
    """«Testbild senden»: colour bars, the name, a check mark - shows that address, upload and brightness work"""
    im, d = _stv_canvas()
    _stv_head(im, d, sim_now().strftime("%H:%M"))
    cols = [(255, 255, 255), (255, 221, 0), (0, 200, 220), (40, 200, 70), (220, 40, 200), (230, 40, 40), (40, 80, 230), (0, 0, 0)]
    for i, c in enumerate(cols):
        d.rectangle((i * 30, 36, i * 30 + 30, 96), fill=c)
    d.line((70, 150, 100, 180), fill=(63, 207, 107), width=10)
    d.line((100, 180, 170, 110), fill=(63, 207, 107), width=10)
    t1 = tr("Test picture", lang)
    d.text(((STV_SIZE - d.textlength(t1, font=_font(22))) / 2, 188), t1, font=_font(22), fill=(232, 238, 245))
    nm = _stv_fit(d, _stv_txt(name), _font(16, False), STV_SIZE - 20)
    d.text(((STV_SIZE - d.textlength(nm, font=_font(16, False))) / 2, 214), nm, font=_font(16, False), fill=(138, 155, 176))
    return _stv_jpg(im)


# ---- the manager: what each display should show -------------------------------------------------------------------------
def stv_night():
    try:
        return bool(CFG.get("stv_night")) and is_dark()
    except Exception:
        return False


def _stv_cached(key, fn):
    R = STV["renders"]
    if key not in R:
        if len(R) > 12:
            R.clear()
        R[key] = fn()
    return R[key]


def _stv_playing(now):
    g = STV["game"]
    return bool(g and now - STV["game_t"] < 10 and g.get("round") in ("countdown", "play"))


def stv_plan(e, now=None):
    """(kind, picture sig, render function, brightness, at once) for one display"""
    now = now or time.time()
    lang = CFG.get("lang")
    red = stv_night()
    a = STV["alarm"]
    alarm_on = a is not None and now - a["t"] < float(CFG.get("stv_alarm_s", 60) or 60)
    if red:
        brt = int(CFG.get("stv_night_brt", 10))
    else:
        brt = int(e.get("brt", 60))
    if e.get("alarm") and alarm_on and now - a["t"] < float(CFG.get("stv_bright_s", 20) or 0) and not _stv_playing(now):
        brt = 100                                          # an alarm: bright for a moment, then back
    g = STV["game"]
    playing = bool(e.get("game") and g and now - STV["game_t"] < 10 and g.get("round") in ("countdown", "play"))
    if e.get("alarm") and alarm_on and not playing:        # in a round the players are the persons: the game shows «Erwischt!»
        key = ("alarm", a["t"], red, lang)
        return "alarm", key, lambda: stv_render_alarm(a, lang, red), brt, True
    if playing or (e.get("game") and g and now - STV["game_t"] < 10 and g.get("round") == "end" and now - STV.get("end_t", 0.0) < 60):
        c = STV["caught"]
        cn = c[1] if c and now - c[0] < 5.0 else None
        sig_p = tuple((p.get("n"), p.get("pt"), p.get("k")) for p in (g.get("players") or [])[:4])
        key = ("game", g.get("round"), g.get("cd"), None if cn else g.get("left"), sig_p, tuple((x.get("n"), x.get("pt")) for x in g.get("top") or []), cn, g.get("mw"), red, lang)
        return "game", key, lambda: stv_render_game(g, cn, lang, red), brt, bool(cn)
    if e.get("status"):
        b = STATE.get("battery") or {}
        bp = int(b.get("pct") // 5 * 5) if b.get("on") and b.get("pct") is not None else None
        clock = int(sim_now().timestamp() // (60 * max(1, int(CFG.get("stv_clock_min", 10) or 10))))
        key = ("status", protect_level(), STATE.get("arm_state"), walktest_on(), bp, bool(b.get("sim")), bool(b.get("charging")), STV["msg_seq"], clock, red, lang)
        return "status", key, lambda: stv_render_status(lang, red), brt, False
    return "", None, None, brt, False


def stv_tick():
    ents = stv_entries() if CFG.get("stv_on") else []
    ids = {e["id"] for e in ents}
    for sid in list(STV["devs"]):
        if sid not in ids:
            STV["devs"][sid].alive = False
            STV["devs"][sid].ev.set()
            STV["devs"].pop(sid, None)
    now = time.time()
    for e in ents:
        dv = STV["devs"].get(e["id"])
        if dv is None or not dv.alive:
            dv = STV["devs"][e["id"]] = StvDev(e["id"])
        ov = getattr(dv, "override", None)
        if ov and now < ov["until"]:
            continue
        kind, key, fn, brt, at_once = stv_plan(e, now)
        if key is None:
            if dv.want and dv.want.get("brt") != brt:
                dv.want = dict(dv.want, brt=brt); dv.ev.set()
            continue
        sig = hash(key)
        if dv.want is None or dv.want["sig"] != sig or dv.want["brt"] != brt:
            jpg = _stv_cached(key, fn)
            dv.want = {"jpg": jpg, "sig": sig, "kind": kind, "brt": brt, "now": at_once}
            dv.ev.set()


def stv_loop():
    while True:
        try:
            stv_tick()
        except Exception as e:
            log_event("sys", f"SmallTV: {e}"[:160])
            time.sleep(5)
        w = 1.0
        for _i in range(int(w * 10)):
            if STV.pop("wake", False):
                break
            time.sleep(0.1)


def stv_start():
    if STV["started"]:
        return
    STV["started"] = True
    threading.Thread(target=stv_loop, daemon=True, name="smalltv").start()


def stv_test(sid, lang=None):
    """«Testbild senden»: at once, 15 s on the screen, then the normal picture again"""
    e = next((x for x in stv_entries() if x["id"] == sid), None)
    if e is None:
        return False, "unknown display"
    stv_tick()
    dv = STV["devs"].get(sid)
    if dv is None:
        return False, "the display is switched off"
    jpg = stv_render_test(e["name"], lang)
    dv.override = {"until": time.time() + 15}
    dv.want = {"jpg": jpg, "sig": hash(("test", time.time())), "kind": "test", "brt": max(30, int(e["brt"])), "now": True}
    dv.h["t"] = 0.0                                        # check the health at once too
    dv.ev.set()
    return True, ""


def stv_scan():
    """«Im Netz suchen»: every address of the own /24 networks asks GET /v.json (0.8 s each, 32 at a time) - only on the button"""
    S = STV["scan"]
    if S["busy"]:
        return False
    S.update(busy=True, found=[], msg="")

    def run():
        import ipaddress
        from concurrent.futures import ThreadPoolExecutor
        nets = set()
        try:
            for ip_ in [wifi_ip()] + (["10.42.0.1"] if CFG.get("hotspot_on") else []):
                if ip_:
                    nets.add(str(ipaddress.ip_network(ip_ + "/24", strict=False)))
        except Exception:
            pass
        if not nets:
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("10.255.255.255", 1)); ip_ = s.getsockname()[0]; s.close()
                if not ip_.startswith("127."):
                    nets.add(str(ipaddress.ip_network(ip_ + "/24", strict=False)))
            except Exception:
                pass
        hosts = [str(h) for n in nets for h in ipaddress.ip_network(n).hosts()][:1024]
        known = {e["addr"] for e in stv_entries(False)}

        def ask(h):
            try:
                d = _stv_json("http://" + h, "/v.json", 0.8)
                if stv_is_geekmagic(d):
                    return {"addr": "http://" + h, "model": str(d.get("m") or "")[:40], "fw": str(d.get("v") or "")[:40], "known": "http://" + h in known}
            except Exception:
                return None
            return None
        found = []
        try:
            with ThreadPoolExecutor(32) as ex:
                for r in ex.map(ask, hosts):
                    if r:
                        found.append(r)
        except Exception as e:
            S["msg"] = str(e)[:80]
        S.update(busy=False, found=found, t=time.time(), msg=S["msg"] or ("" if hosts else "no network"))
        log_event("web", f"SmallTV search: {len(found)} found in {', '.join(sorted(nets)) or '-'}")
    threading.Thread(target=run, daemon=True, name="smalltv-scan").start()
    return True


def stv_state(lang=None):
    out = []
    for e in stv_entries():
        dv = STV["devs"].get(e["id"])
        h = dict(dv.h) if dv else {"ok": None}
        for k_ in ("note", "err"):                     # the threads write English: translated for the page / the window
            if h.get(k_):
                h[k_] = h[k_].replace("stored anyway (firmware)", tr("stored anyway (firmware)", lang)).replace(
                    "upload failed", tr("upload failed", lang)).replace("not a GeekMagic SmallTV?", tr("not a GeekMagic SmallTV?", lang))
        out.append(dict(e, health=h, ups=dv.ups if dv else 0, kb=round((dv.bytes if dv else 0) / 1024.0, 1), kind=dv.kind if dv else "",
                        has_img=bool(dv and dv.jpg), errs=dv.errs if dv else 0))
    S = STV["scan"]
    hs = STATE.get("hotspot") or {}
    return {"ok": True, "on": bool(CFG.get("stv_on")), "list": out, "night": stv_night(), "max": STV_MAX,
            "scan": {"busy": S["busy"], "found": S["found"], "t": S["t"], "msg": S["msg"]},
            "setup": {"hotspot": STV_HOTSPOT, "url": STV_SETUP_URL, "wifi_qr": f"WIFI:T:nopass;S:{STV_HOTSPOT};;",
                      "own_wifi": CFG.get("hotspot_ssid") or "MotionWatch", "own_on": bool(CFG.get("hotspot_on")), "own_clients": hs.get("clients")},
            "sim": bool(CFG.get("sim_on")), "sim_has": bool(STV["sim_ok"])}


def stv_img(sid):
    dv = STV["devs"].get(str(sid))
    return dv.jpg if dv else None


def smalltv_routes(app, reply, body):
    """the addresses (called once by the web server, 550)"""
    from flask import request, g, Response
    stv_start()                                        # the manager thread (does nothing without displays)

    @app.route("/api/smalltv", methods=["GET", "POST"])
    def api_smalltv():
        lang = norm_lang(request.args.get("lang") or (body().get("lang") if request.method == "POST" else None))
        if request.method == "GET":
            return reply(stv_state(lang))
        if getattr(g, "role", "admin") != "admin":
            return reply({"ok": False, "error": tr_err("not allowed", lang)}, 403)
        d = body(); a = str(d.get("action") or "")
        who = getattr(g, "user", "") or "web"
        if a in ("add", "remove", "update"):
            ok, err = stv_edit(a, d, who)
        elif a == "test":
            ok, err = stv_test(str(d.get("id") or ""), lang)
        elif a == "check":
            dv = STV["devs"].get(str(d.get("id") or ""))
            ok, err = (True, "") if dv else (False, "unknown display")
            if dv:
                dv.h["t"] = 0.0; dv.ev.set()
        elif a == "scan":
            ok, err = stv_scan(), ""
        else:
            ok, err = False, "unknown action"
        r = stv_state(lang)
        r.update(ok=ok, error=tr_err(err, lang) if err else None)
        return reply(r, 200 if ok else 400)

    @app.route("/api/smalltv/img/<sid>.jpg")
    def api_smalltv_img(sid):
        b = stv_img(sid)
        if not b:
            return Response(b"", status=404)
        return Response(b, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})


# ---- the web page: Settings → Devices & sensors → «Extra display (SmallTV)» (530 calls stvPanel) --------------------------
STV_JS = r"""
<script>
(function () {
  try { const D = /*STVDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const T = x => (typeof t === "function" ? t(x) : x);
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  const P = (d) => post("/api/smalltv", Object.assign({lang: L()}, d));
  let BOX = null, TM = null, SIG = "";
  const ago = s => { if (!s) return "–"; const a = Math.max(0, Math.round(Date.now() / 1000 - s)); return a < 90 ? a + " s" : Math.round(a / 60) + " min"; };
  const KIND = {status: "Status", alarm: "Alarm picture", game: "Game", test: "Test picture"};
  function row(e) {
    const c = E("div", "sens-card stv-card"); c.dataset.id = e.id;
    const h = e.health || {};
    const top = E("div", "row"); top.style.cssText = "gap:10px;align-items:flex-start";
    const im = E("img", "stv-pic"); im.alt = ""; im.width = 72; im.height = 72;
    if (e.has_img) im.src = "/api/smalltv/img/" + e.id + ".jpg?u=" + e.ups; else im.style.visibility = "hidden";
    const tx = E("div", ""); tx.style.cssText = "flex:1;min-width:0";
    const dot = h.ok === true ? "🟢" : h.ok === false ? "🔴" : "⚪";
    tx.append(E("b", "", dot + " " + (e.sim ? "🧪 " + T("Virtual SmallTV of the simulator") : e.name)));
    tx.append(E("div", "mut", e.addr.replace("http://", "") + (h.fw ? " · " + h.fw : "") + (h.free != null ? " · " + Math.round(h.free / 1024) + " KB " + T("free") : "")));
    tx.append(E("div", "mut", (h.ok === false ? "⚠ " + (h.err || T("not reachable")) : h.ok ? "✓ " + T("reachable") : T("checking …"))
      + " · " + e.ups + " " + T("pictures") + (e.kind ? " · " + T(KIND[e.kind] || e.kind) : "") + (h.sent_t ? " · " + ago(h.sent_t) : "") + (h.note ? " · " + h.note : "")));
    top.append(im, tx); c.appendChild(top);
    const ch = E("div", ""); ch.style.cssText = "display:flex;gap:6px 14px;flex-wrap:wrap;justify-content:flex-start;margin-top:6px";
    [["on", "On"], ["status", "Status"], ["alarm", "Alarm picture"], ["game", "Game"]].forEach(([f, lb]) => {
      const l = E("label", ""); l.style.cssText = "display:inline-flex;gap:4px;align-items:center";
      const cb = E("input"); cb.type = "checkbox"; cb.checked = !!e[f]; cb.className = "stv-" + f;
      cb.onchange = async () => { const r = await P({action: "update", id: e.id, field: f, value: cb.checked}); if (!r.ok) toast("⚠ " + (r.error || "error")); };
      l.append(cb, E("span", "", T(lb))); ch.appendChild(l); });
    c.appendChild(ch);
    const sl = E("div", "sl"), st = E("div", "row"), val = E("span", "val", e.brt + " %");
    st.append(E("span", "", T("Brightness (day)")), val);
    const rg = E("input"); rg.type = "range"; rg.min = 0; rg.max = 100; rg.step = 5; rg.value = e.brt; rg.className = "stv-brt";
    rg.oninput = () => { val.textContent = rg.value + " %"; };
    rg.onchange = async () => { await P({action: "update", id: e.id, field: "brt", value: +rg.value}); };
    sl.append(st, rg); c.appendChild(sl);
    const bb = E("div", "btns"); bb.style.marginTop = "6px";
    const tb = E("button", "", "🖼 " + T("Send a test picture")); tb.type = "button"; tb.className = "stv-test";
    tb.onclick = async () => { tb.disabled = true; const r = await P({action: "test", id: e.id}); tb.disabled = false;
      toast(r.ok ? "✓ " + T("Test picture on the way (shows 15 s)") : "⚠ " + (r.error || "error")); setTimeout(load, 4000); };
    const cb2 = E("button", "sec", "↻ " + T("Check")); cb2.type = "button"; cb2.onclick = async () => { await P({action: "check", id: e.id}); setTimeout(load, 2500); };
    bb.append(tb, cb2);
    if (!e.sim) { const rb = E("button", "red", "✕ " + T("Remove")); rb.type = "button";
      rb.onclick = async () => { if (!confirm(T("Remove this display?") + "\n" + e.name)) return; await P({action: "remove", id: e.id}); load(); }; bb.appendChild(rb); }
    c.appendChild(bb);
    return c;
  }
  function setup(j) {
    const s = j.setup || {}, dt = E("details", "stv-setup"); dt.style.marginTop = "10px";
    dt.appendChild(E("summary", "", "🧭 " + T("Set up a SmallTV (step by step)")));
    const ol = E("ol", ""); ol.style.cssText = "margin:6px 0 0 18px;padding:0";
    const li = (txt, qr, title) => { const x = E("li", "", txt); x.style.margin = "6px 0";
      if (qr && window.qrBtn) { const q = qrBtn(qr, title); q.style.marginLeft = "6px"; x.appendChild(q); } ol.appendChild(x); };
    li(T("Plug the SmallTV in (USB, 5 V). New or reset, it opens its own Wi-Fi «GIFTV».") + " ", s.wifi_qr, "Wi-Fi «GIFTV» (SmallTV)");
    li(T("Join «GIFTV» with the phone and open the setup page") + " " + s.url + " ", s.url, T("Setup page of the SmallTV"));
    li(T("Choose the network of MoveEye there") + ": " + (s.own_on ? "«" + s.own_wifi + "» (" + T("own Wi-Fi of MoveEye") + ")" : T("the Wi-Fi in which MoveEye is")) + ". "
       + T("The SmallTV restarts and shows its new address."));
    li(T("Back here: «Search in the network» or enter the address shown on the SmallTV."));
    dt.appendChild(ol);
    const w = E("div", "mut", "🔓 " + T("stv-security")); w.style.marginTop = "6px"; dt.appendChild(w);
    return dt;
  }
  function addForm() {
    const f = E("div", ""); f.style.marginTop = "10px";
    const r = E("div", ""); r.style.cssText = "display:flex;gap:8px;flex-wrap:wrap;align-items:center";
    const nm = E("input"); nm.type = "text"; nm.maxLength = 30; nm.placeholder = T("Name (e.g. Tent)"); nm.style.cssText = "flex:1 1 110px;width:auto;min-width:0"; nm.id = "stv-name";
    const ad = E("input"); ad.type = "text"; ad.maxLength = 90; ad.placeholder = T("Address (e.g. 192.168.1.77)"); ad.style.cssText = "flex:2 1 170px;width:auto;min-width:0"; ad.id = "stv-addr";
    const ab = E("button", "", "+ " + T("Add")); ab.type = "button"; ab.id = "stv-add";
    ab.onclick = async () => { const res = await P({action: "add", name: nm.value, addr: ad.value}); if (!res.ok) { toast("⚠ " + (res.error || "error")); return; } nm.value = ad.value = ""; load(); };
    r.append(nm, ad, ab); f.appendChild(r);
    const sb = E("button", "sec", "🔍 " + T("Search in the network")); sb.type = "button"; sb.id = "stv-scan"; sb.style.marginTop = "8px";
    const res = E("div", "stv-found");
    sb.onclick = async () => { sb.disabled = true; res.textContent = T("searching … (about 10 s)"); await P({action: "scan"}); poll(sb, res); };
    f.append(sb, res);
    return f;
  }
  async function poll(sb, res) {
    let j = null; try { j = await (await fetch("/api/smalltv?lang=" + L(), {cache: "no-store"})).json(); } catch (e) {}
    if (j && j.scan && j.scan.busy) { setTimeout(() => poll(sb, res), 1500); return; }
    sb.disabled = false; res.textContent = "";
    const fd = (j && j.scan && j.scan.found) || [];
    if (!fd.length) { res.appendChild(E("div", "mut", T("No SmallTV found. Is it in the same network? Otherwise enter the address."))); return; }
    fd.forEach(x => { const r = E("div", "row"); r.style.cssText = "gap:8px;margin-top:4px";
      r.appendChild(E("span", "", "📺 " + x.addr.replace("http://", "") + (x.fw ? " · " + x.fw : "")));
      if (x.known) r.appendChild(E("span", "mut", "✓ " + T("in the list")));
      else { const b = E("button", "", "+ " + T("Add")); b.type = "button"; b.onclick = async () => { await P({action: "add", name: "SmallTV", addr: x.addr}); load(); }; r.appendChild(b); }
      res.appendChild(r); });
  }
  async function load() {
    if (!BOX || !document.contains(BOX)) { clearInterval(TM); TM = null; return; }
    let j = null; try { j = await (await fetch("/api/smalltv?lang=" + L(), {cache: "no-store"})).json(); } catch (e) { return; }
    if (!j || !j.ok) return;
    const sig = JSON.stringify(j.list) + j.night;
    if (sig === SIG && BOX.querySelector(".stv-list")) return;
    SIG = sig;
    const ls = BOX.querySelector(".stv-list"); ls.textContent = "";
    if (j.night) ls.appendChild(E("div", "mut", "🌙 " + T("Night: the displays are dimmed and red.")));
    (j.list || []).forEach(e => ls.appendChild(row(e)));
    if (!(j.list || []).length) ls.appendChild(E("div", "mut", T("No display yet.") + (j.sim ? " " + T("The simulator has a virtual SmallTV from version 3D-4.19.") : "")));
  }
  window.stvPanel = function (d) {
    if (d.querySelector("#stvpanel")) return;
    BOX = E("div", "auxbox"); BOX.id = "stvpanel";
    BOX.appendChild(E("div", "mut", T("stv-note")));
    BOX.appendChild(E("div", "stv-list"));
    d.appendChild(BOX);
    fetch("/api/smalltv?lang=" + L(), {cache: "no-store"}).then(r => r.json()).then(j => { BOX.append(addForm(), setup(j)); SIG = ""; load(); }).catch(() => {});
    if (!TM) TM = setInterval(() => { if (BOX && BOX.offsetParent !== null) load(); }, 4000);
  };
})();
</script>
"""
