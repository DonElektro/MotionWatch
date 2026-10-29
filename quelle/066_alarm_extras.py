#@ MoveEye – Teil 066: Alarm-Extras – Knöpfe in der Push-Nachricht, Akku-Prognose, Morgen-Push mit Bildstreifen, «Was war das?», doppelte Bestätigung, Ansage beim Einschalten, «Bist du's?». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (29.10.2026):
#  1  Knöpfe in der Push-Nachricht (ntfy «Actions», Telegram: Link-Knöpfe): «Fehlalarm», «Sirene», «Aus». Jede Nachricht hat
#     ihren eigenen Schlüssel (zufällig, 1 h gültig, jeder Knopf nur einmal) – kein Passwort in der Adresse. Adresse /na/<schlüssel>/<knopf>.
#  2  Akku-Prognose beim Einschalten («Akku reicht bis 06:40 bei Wachsam») – Schutz-Seite, Fenster, Antwort / Meldung beim Einschalten.
#  3  Morgen-Push: der Nachtbericht als ein Satz und ein Bildstreifen der Nacht (bis 4 Bilder aus dem Tagebuch).
#  4  «Was war das?»: nach jedem Personen-Alarm das Bild mit Person / Tier / Nichts – gespeichert als Trainingsdaten
#     (alarm_labels/: Bild + Rahmen + Antwort); «Nichts» zählt als Fehlalarm (Aufnahme markiert, Bild nach fa_learn/).
#  6  Doppelte Bestätigung (aus ab Werk): ein Personen-Alarm erst, wenn KI und Wärmebild übereinstimmen oder die KI die
#     Person zweimal nacheinander sieht – sonst nur ein Voralarm.
#  7  Ansage beim Einschalten über den Lautsprecher: «Akku 80 Prozent, WLAN gut, Kamera frei» oder was fehlt.
#  8  «Bist du's?»: kommt das Handy des Besitzers zurück, warten Personen-Alarme 60 s und eine Push-Nachricht fragt
#     «Bist du's?» mit dem Knopf «Aus».
# (5 – Zonen nach Art – steht bei den Zonen in Teil 030.)
# ----------------------------------------------------------------------------
_ALX_CFG = {"push_actions": True, "alarm_confirm2": False, "arm_announce": True, "back_ask": False, "back_hold_s": 60,
            "report_strip": True}
for _k, _v in _ALX_CFG.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

ALX = {"lock": threading.Lock(), "tok": {}, "fails": {}, "ctx": None, "hold_until": 0.0, "started": False,
       "g": {"sig": None, "hits": 0, "ok": False, "last_p": 0.0, "pre_t": 0.0, "hold_log": 0.0}}
ALX_TTL = 3600                       # a button of a push message works for one hour
ALX_ACTS = ("fa", "siren", "off")
ALX_LABELS = ("person", "animal", "nothing")


# ---- 1: one key per message ------------------------------------------------------------------------------------------
def alx_base():
    """the address of this page for the buttons (the same as the «tap» link of the message); empty: no buttons"""
    pub = str(CFG.get("public_url") or "").strip().rstrip("/")
    return pub if pub.startswith(("http://", "https://")) else ""


def alx_token(p):
    """a new key for the buttons of one message (or '' when it gets none). Kept in memory only - after a restart the old
    buttons no longer work (that is fine: they are for the next minutes)."""
    if not CFG.get("push_actions", True) or not alx_base():
        return ""
    ev = p.get("event")
    acts = tuple(p.get("alx_acts") or (ALX_ACTS if ev in ("person", "prealarm", "warm", "noise") else (("fa", "off") if ev == "tamper" else ())))
    if not acts:
        return ""
    now = time.time()
    ctx = ALX["ctx"] if ev == "person" and ALX["ctx"] and now - ALX["ctx"]["t"] < 180 else None
    tok = secrets.token_urlsafe(18)
    with ALX["lock"]:
        for k in [k for k, v in ALX["tok"].items() if now - v["t"] > ALX_TTL]:
            ALX["tok"].pop(k, None)
        while len(ALX["tok"]) > 200:
            ALX["tok"].pop(next(iter(ALX["tok"])))
        ALX["tok"][tok] = {"t": now, "ev": ev, "acts": list(acts), "used": [], "ctx": ctx["id"] if ctx else ""}
    return tok


def alx_buttons(p, lang=None):
    """[(label, url, clear)] of the message p (its key made once, kept in p for the retries)"""
    if "alx_tok" not in p:
        p["alx_tok"] = alx_token(p)
    tok = p.get("alx_tok") or ""
    if not tok:
        return []
    base = alx_base()
    with ALX["lock"]:
        acts = list((ALX["tok"].get(tok) or {}).get("acts") or [])
    names = {"fa": "False alarm", "siren": "Siren", "off": "Off"}
    return [(tr(names[a], lang), f"{base}/na/{tok}/{a}", a != "siren") for a in acts if a in names]


def alx_ntfy_actions(p):
    """the «Actions» header of ntfy: http buttons (the phone sends a POST in the background)"""
    out = []
    for lab, url, clear in alx_buttons(p):
        lab = lab.replace(",", " ").replace(";", " ")
        if url.endswith("/off"):                         # (578): «Off» opens the page with the PIN field - never in the background
            out.append(f"view, {lab}, {url}" + (", clear=true" if clear else ""))
            continue
        out.append(f"http, {lab}, {url}, method=POST" + (", clear=true" if clear else ""))
    return "; ".join(out)


def alx_telegram_markup(p):
    """Telegram: link buttons (they open the small confirmation page of MoveEye)"""
    b = alx_buttons(p)
    return {"inline_keyboard": [[{"text": lab, "url": url} for lab, url, _c in b]]} if b else None


def alx_use(tok, act):
    """(ok, error, entry) - the key must exist, be young enough and the button not used yet"""
    if act not in ALX_ACTS or not isinstance(tok, str) or not re.fullmatch(r"[A-Za-z0-9_\-]{20,40}", tok):
        return False, "unknown", None
    with ALX["lock"]:
        e = ALX["tok"].get(tok)
        if e is None:
            return False, "unknown", None
        if time.time() - e["t"] > ALX_TTL:
            ALX["tok"].pop(tok, None)
            return False, "expired", None
        if act not in e["acts"]:
            return False, "unknown", None
        if act in e["used"]:
            return False, "used", None
        e["used"].append(act)
        if act == "off":
            ALX["tok"].pop(tok, None)                    # switched off: the other buttons of this message are done too
        return True, "", dict(e)


def alx_do(act, e, who="push"):
    """carry out a button; returns (ok, text in the current language)"""
    if act == "fa":
        cid = e.get("ctx") or ""
        if cid:
            ok, err = alx_label(cid, "nothing", who)
            return ok, tr("Thanks - marked as false alarm, MoveEye learns from it.") if ok else tr_err(err)
        log_event("person", f"False alarm reported by {who} ({e.get('ev')})")
        return True, tr("Thanks - noted as false alarm.")
    if act == "siren":
        if not out_selected():
            return False, tr("No loudspeaker chosen")
        SOUND["last_alarm"] = time.time()
        ok, err = sound_play(None, None, None, reason="push button")
        log_event("sys", f"Siren started from the push message ({who})")
        return bool(ok), tr("Siren on") if ok else tr_err(err or "error")
    if act == "off":
        try:
            protect_cancel_escalation()
        except NameError:
            pass
        CFG["protect_level"] = "off"
        disarm()
        sound_stop()
        ALX["hold_until"] = 0.0
        log_event("sys", f"Protection switched off from the push message ({who})")
        return True, tr("Protection off")
    return False, "unknown"


_ALX_PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye</title><style>body{font-family:system-ui,sans-serif;background:#0f141b;color:#e8edf3;margin:0;display:flex;min-height:100vh;
align-items:center;justify-content:center}.c{background:#18202b;border-radius:16px;padding:24px;max-width:360px;text-align:center}
button{font-size:18px;padding:12px 26px;border-radius:12px;border:0;background:#2f81f7;color:#fff;margin-top:14px}
p{color:#9aa6b4}</style></head><body><div class="c"><h2>%s</h2><p>%s</p>%s</div></body></html>"""


def alx_routes(app, watch, reply, body):
    """the addresses of the extras (called once by the web server, 550)"""
    from flask import Response, request, send_file
    import html as _html
    alx_start()

    @app.route("/na/<tok>/<act>", methods=["GET", "POST"])
    def alx_push_button(tok, act):
        ip = request.remote_addr or "?"
        now = time.time()
        rec = [x for x in ALX["fails"].get(ip, []) if now - x < 600]
        if len(rec) >= 20:
            return sx_err(429, "keys")                   # in the own language (578)
        names = {"fa": "False alarm", "siren": "Siren", "off": "Off"}
        if request.method == "GET":                      # a browser (Telegram link): ask first - a link preview must not switch anything
            with ALX["lock"]:
                e = ALX["tok"].get(tok)
            if not e or act not in e["acts"] or now - e["t"] > ALX_TTL:
                rec.append(now); ALX["fails"][ip] = rec
                return Response(_ALX_PAGE % ("MoveEye", _html.escape(tr("This button is no longer valid.")), ""), 404, mimetype="text/html")
            if act == "off":                             # (578): switching off needs the protection PIN (or the web password)
                L_ = sx_req_lang()
                return Response(sx_page(tr("Switch the protection off?", L_), sx_off_form(L_), "⏻", L_), mimetype="text/html")
            form = ('<form method="post"><button type="submit">' + _html.escape(tr(names.get(act, act))) + "</button></form>")
            return Response(_ALX_PAGE % ("MoveEye", _html.escape(tr("Tap to confirm.")), form), mimetype="text/html")
        if act == "off":                                 # (578): first the key (not used up), then the PIN, then switch off
            with ALX["lock"]:
                e0 = ALX["tok"].get(tok)
            if e0 and act in e0["acts"] and act not in e0["used"] and now - e0["t"] <= ALX_TTL:
                L_ = sx_req_lang()
                ok_, err_ = sx_off_check(request.form.get("pin", ""), request.form.get("pw", ""), "push button")
                if not ok_:
                    if "text/html" in (request.headers.get("Accept") or "") or request.form:
                        return Response(sx_page(tr("Switch the protection off?", L_), sx_off_form(L_, err_), "⏻", L_), 403, mimetype="text/html")
                    return Response(tr("Off needs the protection PIN - open the message and tap «Off» there.", L_), 403, mimetype="text/plain")
        ok, err, e = alx_use(tok, act)
        if not ok:
            if err == "unknown":
                rec.append(now); ALX["fails"][ip] = rec
            msg = {"used": "This button was already used.", "expired": "This button is no longer valid."}.get(err, "This button is no longer valid.")
            code = 409 if err == "used" else (410 if err == "expired" else 404)
            if "text/html" in (request.headers.get("Accept") or ""):
                return Response(_ALX_PAGE % ("MoveEye", _html.escape(tr(msg)), ""), code, mimetype="text/html")
            return Response(tr(msg), code, mimetype="text/plain")
        done, txt = alx_do(act, e, "push button")
        if not done:                                     # did not work (e.g. no loudspeaker): the button may be tried again
            with ALX["lock"]:
                e2 = ALX["tok"].get(tok)
                if e2 and act in e2["used"]:
                    e2["used"].remove(act)
        if "text/html" in (request.headers.get("Accept") or ""):
            return Response(_ALX_PAGE % ("MoveEye", ("✓ " if done else "⚠ ") + _html.escape(txt), ""), mimetype="text/html")
        return Response(txt, 200 if done else 500, mimetype="text/plain")

    @app.route("/api/alarmlabel", methods=["GET", "POST"])
    def api_alarmlabel():
        if request.method == "POST":
            d = body(); lang = norm_lang(d.get("lang") or CFG.get("lang"))
            ok, err = alx_label(str(d.get("id") or ""), str(d.get("label") or ""), "web")
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None}, 200 if ok else 400)
        lang = norm_lang(request.args.get("lang") or CFG.get("lang"))
        try:
            n = max(1, min(30, int(request.args.get("n", 10))))
        except ValueError:
            n = 10
        return reply({"ok": True, "items": alx_label_list(n), "forecast": arm_forecast(lang), "tx": alx_web_texts(lang), "lang": lang})

    @app.route("/api/alarmlabel/img/<lid>")
    def api_alarmlabel_img(lid):
        p = alx_label_path(lid, ".jpg")
        if not p or not os.path.exists(p):
            return Response("not found", 404)
        return send_file(p, mimetype="image/jpeg", max_age=3600)

    @app.route("/alx/what.js")
    def alx_what_js():
        return Response(ALX_WHAT_JS, mimetype="application/javascript", headers={"Cache-Control": "no-cache"})


# ---- 4: «Was war das?» – the alarm pictures as training data -----------------------------------------------------------
def _alx_label_dir():
    return os.path.join(DATA_DIR, "alarm_labels")


def alx_label_path(lid, ext):
    if not re.fullmatch(r"\d{8}_\d{6}(_\d{1,3})?", str(lid or "")):
        return None
    return os.path.join(_alx_label_dir(), lid + ext)


def alarm_ctx_note(w, stamp, snap, frame, persons):
    """called by the camera loop (410) right before the person alarm goes out: keep the picture and the boxes"""
    try:
        now = time.time()
        pw, ph = getattr(w, "_proc_size", None) or (int(CFG["proc_width"]), 0)
        if not pw or not ph:
            h0, w0 = frame.shape[:2]; pw, ph = int(CFG["proc_width"]), int(h0 * int(CFG["proc_width"]) / max(1, w0))
        boxes = [[round(b[0] / pw, 4), round(b[1] / ph, 4), round(b[2] / pw, 4), round(b[3] / ph, 4)] for b in persons[:8]]
        lid = stamp
        n = 0
        while alx_label_path(lid, ".json") and os.path.exists(alx_label_path(lid, ".json")) and n < 50:
            n += 1; lid = f"{stamp}_{n}"
        ctx = {"id": lid, "t": now, "stamp": stamp, "kind": "person", "count": len(persons), "boxes": boxes, "label": "",
               "snap": os.path.basename(snap) if snap else "", "src": str(STATE.get("source_label") or "")[:40], "sim": bool(CFG.get("sim_on"))}
        ALX["ctx"] = ctx
        w.raw_until = max(getattr(w, "raw_until", 0.0), now + 2.0)    # the next picture without marks, for the training
        old = getattr(w, "frame_raw", None)
        pic = frame.copy()

        def keep():
            t_end = time.time() + 1.5
            img = None
            while time.time() < t_end:
                f_ = getattr(w, "frame_raw", None)
                if f_ is not None and f_ is not old:
                    img = f_; break
                time.sleep(0.1)
            img = img if img is not None else pic
            try:
                d = _alx_label_dir(); os.makedirs(d, exist_ok=True)
                h, wd = img.shape[:2]
                if wd > 1280:
                    img = cv2.resize(img, (1280, int(h * 1280 / wd)), interpolation=cv2.INTER_AREA)
                cv2.imwrite(os.path.join(d, lid + ".jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
                ctx["w"], ctx["h"] = int(img.shape[1]), int(img.shape[0])
                _alx_label_save(ctx)
                _alx_label_prune()
            except Exception as e:
                log_event("sys", f"Alarm picture for «What was it?» not kept: {e}"[:160])
        threading.Thread(target=keep, daemon=True, name="alx-keep").start()
        return lid
    except Exception as e:
        log_event("sys", f"Alarm picture: {e}"[:160])
        return ""


def _alx_label_save(ctx):
    p = alx_label_path(ctx["id"], ".json")
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(ctx, f, ensure_ascii=False)
    os.replace(p + ".tmp", p)


def _alx_label_load(lid):
    p = alx_label_path(lid, ".json")
    if not p:
        return None
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _alx_label_prune(keep=300, days=14):
    """at most 300 pictures; unanswered ones older than 14 days go (answered ones are training data and stay)"""
    d = _alx_label_dir()
    try:
        js = sorted(f for f in os.listdir(d) if f.endswith(".json"))
    except OSError:
        return
    old = time.time() - days * 86400
    drop = []
    for f in js:
        x = _alx_label_load(f[:-5])
        if x and not x.get("label") and float(x.get("t") or 0) < old:
            drop.append(f[:-5])
    rest = [f[:-5] for f in js if f[:-5] not in drop]
    drop += rest[:max(0, len(rest) - keep)]
    for lid in drop:
        for ext in (".json", ".jpg"):
            try:
                os.remove(os.path.join(d, lid + ext))
            except OSError:
                pass


def alx_label_list(n=10):
    d = _alx_label_dir()
    try:
        js = sorted((f for f in os.listdir(d) if f.endswith(".json")), reverse=True)[:n]
    except OSError:
        return []
    out = []
    for f in js:
        x = _alx_label_load(f[:-5])
        if x and os.path.exists(os.path.join(d, x["id"] + ".jpg")):
            out.append({"id": x["id"], "t": x.get("t"), "label": x.get("label") or "", "boxes": x.get("boxes") or [],
                        "count": x.get("count", 0), "sim": bool(x.get("sim"))})
    return out


def alx_label(lid, label, who="web"):
    """the answer to «What was it?» (also «False alarm» from the push = «nothing»)"""
    if label not in ALX_LABELS:
        return False, "unknown answer"
    x = _alx_label_load(lid)
    if x is None:
        return False, "not found"
    was = x.get("label") or ""
    x["label"] = label; x["label_t"] = int(time.time()); x["label_by"] = who
    try:
        _alx_label_save(x)
    except OSError as e:
        return False, str(e)[:100]
    names = [f"person_{x.get('stamp')}.mp4", f"person_{x.get('stamp')}.jpg"]
    try:
        names = [n_ for n_ in names if rec_path(n_)]
    except NameError:
        names = []
    w = WATCH_REF.get("w")
    if label == "nothing":
        if names:
            rec_set_false(names, "other", w)             # the false alarm list and its suggestions (430) see it
        try:                                             # a «no person» example for the training, like the false alarm learning
            fd = os.path.join(DATA_DIR, "fa_learn", f"{x.get('stamp')}_label")
            os.makedirs(fd, exist_ok=True)
            shutil.copy2(alx_label_path(lid, ".jpg"), os.path.join(fd, "00.jpg"))
            with open(os.path.join(fd, "info.json"), "w") as f_:
                json.dump({"label": "no_person", "cause": "other", "from": "alarm label", "boxes": x.get("boxes") or []}, f_)
        except OSError:
            pass
        try:
            if CFG.get("fa_learn_auto", True) and names and names[0].endswith(".mp4") and sim_ready():
                falearn_start(names[0], "other")         # re-enacted in the simulator (143)
        except Exception:
            pass
    elif was == "nothing" and names:
        rec_set_false(names, "", w)                      # changed the mind: real again
    log_event("person", f"Alarm {lid}: «what was it?» = {label} ({who})")
    return True, ""


def alx_web_texts(lang):
    keys = ("What was it?", "Person", "Animal", "Nothing", "Thanks - MoveEye learns from it.", "Your answer", "Alarm",
            "Answers are kept as training pictures (picture + boxes); «Nothing» counts as a false alarm.", "simulation")
    return {k: tr(k, lang) for k in keys}


# ---- 2: battery forecast -------------------------------------------------------------------------------------------------
def arm_forecast(lang=None):
    """{text, ok, hint, pct} - how long the battery lasts with the protection on; None without a battery"""
    b = STATE.get("battery") or {}
    if not b.get("on") or b.get("pct") is None:
        return None
    L = norm_lang(lang) if lang else cur_lang()
    pct = int(b["pct"])
    lv = tr("Full protection", L) if CFG.get("protect_level") == "full" else tr("Watchful", L)
    if b.get("on_battery") is False:
        return {"text": trf("Battery {pct} % · on mains power", L, pct=pct), "ok": True, "hint": "", "pct": pct}
    cap, use = float(b.get("cap_wh") or 0), float(b.get("use_w") or 0)
    if cap <= 0 or use <= 0:
        return {"text": trf("Battery {pct} %", L, pct=pct), "ok": pct >= 30, "hint": "", "pct": pct}
    have_h = pct / 100.0 * cap / max(0.5, use)
    try:
        nf = night_forecast()
    except Exception:
        nf = None
    now = datetime.now()
    until = now + timedelta(hours=have_h)
    if have_h >= 36:
        text = trf("Battery lasts {d} days at {level}", L, d=int(have_h // 24), level=lv)
    else:
        hm = until.strftime("%H:%M")
        if until.date() != now.date():
            hm = tr("tomorrow", L) + " " + hm
        text = trf("Battery lasts until {t} at {level}", L, t=hm, level=lv)
    ok = bool(nf["enough"]) if nf else have_h >= 8
    if not ok and nf:
        text += " · " + trf("sunrise {t}", L, t=nf["sunrise"])
    hint = "" if ok or CFG.get("eco_on") else tr("Tip: switch on power saving (Settings → Power supply) - it lasts longer.", L)
    return {"text": text, "ok": ok, "hint": hint, "pct": pct}


def arm_forecast_text(lang=None):
    f = arm_forecast(lang)
    return "" if not f else (("" if f["ok"] else "⚠ ") + f["text"] + ((" · " + f["hint"]) if f["hint"] else ""))


# ---- 7: what the loudspeaker says when the protection is switched on ---------------------------------------------------
def arm_announce_text(lang=None):
    L = norm_lang(lang) if lang else cur_lang()
    T = lambda x: tr(x, L)
    parts, bad = [], []
    b = STATE.get("battery") or {}
    if b.get("on") and b.get("pct") is not None:
        parts.append(trf("battery {pct} percent", L, pct=int(b["pct"])))
        f = arm_forecast(L)
        if f and not f["ok"]:
            bad.append(T("the battery does not last the night"))
    wf = STATE.get("wifi") or {}
    hs = STATE.get("hotspot") or {}
    if hs.get("on"):
        parts.append(T("own Wi-Fi on"))
    elif wf.get("connected"):
        dbm = wf.get("dbm")
        parts.append(T("Wi-Fi weak") if isinstance(dbm, (int, float)) and dbm < -75 else T("Wi-Fi good"))
    else:
        bad.append(T("no Wi-Fi"))
    if (STATE.get("net") or {}).get("online") is False and not hs.get("on"):
        bad.append(T("no internet"))
    fps = float(STATE.get("fps") or 0)
    ln = STATE.get("lens") or {}
    if fps < 1:
        bad.append(T("the camera has no picture"))
    elif ln.get("state") == "fogged":
        bad.append(T("the lens is blurred"))
    else:
        parts.append(T("camera clear"))
    if not Notifier.configured():
        bad.append(T("push messages are not set up"))
    try:
        for x in health_check(L)["items"]:
            if x["level"] == "bad" and x["id"] not in ("cam", "lens", "net", "push", "batt"):
                bad.append(x["title"] + " " + T("not ok"))
    except Exception:
        pass
    out = ", ".join(parts)
    if bad:
        out = (out + ". " if out else "") + T("Attention") + ": " + ", ".join(bad[:3])
    return out + "."


def _alx_announce():
    if not CFG.get("arm_announce", True) or not out_selected():
        return
    try:
        if sandbox_active():
            return                                       # drill / game / test inbox: the loudspeaker stays quiet
    except NameError:
        pass
    txt = arm_announce_text()
    ok, err = tts_say(txt)
    log_event("sys", f"Announcement when arming: «{txt[:80]}»" + ("" if ok else f" - not spoken: {err}")[:80])


# ---- 6 / 8: the gate of the person alarm --------------------------------------------------------------------------------
def alarm_gate(w, frame, persons, now):
    """called by the camera loop (410) for every picture: returns the persons that may raise a person alarm now.
    «Bist du's?» holds them back for a moment; the double confirmation lets them through only when the AI and the thermal
    camera agree or when the AI saw a person in two runs one after the other - otherwise it stays a pre-alarm."""
    alx_start()
    G = ALX["g"]
    ai = getattr(w, "ai", None)
    ab = list(getattr(ai, "boxes", None) or [])
    sig = (getattr(ai, "_last_run", None), tuple(tuple(int(v) for v in b_[:4]) for b_ in ab))
    if sig != G["sig"]:                                  # a new result of the AI
        G["sig"] = sig
        G["hits"] = G["hits"] + 1 if ab else 0
    if not persons:
        if now - G["last_p"] > 5.0:
            G["ok"] = False
        return persons
    G["last_p"] = now
    if ALX["hold_until"] > now and is_armed():
        if now - G["hold_log"] > 20:
            G["hold_log"] = now
            log_event("person", f"Person seen - held back «Is it you?» ({int(ALX['hold_until'] - now)} s left)")
        return []
    if not CFG.get("alarm_confirm2") or G["ok"]:
        return persons
    ai_on = str(STATE.get("ai_status") or "").startswith(("ready", "running", "PC", "demo"))
    warm = now - float(getattr(w, "last_warm", 0.0) or 0.0) < 3.0
    why = ""
    if ab and warm:
        why = "AI and thermal camera agree"
    elif G["hits"] >= 2:
        why = "the AI saw the person twice in a row"
    elif warm and not ai_on:
        why = "thermal camera (the AI is off)"
    if why:
        G["ok"] = True
        log_event("person", f"Double confirmation: {why} - alarm")
        return persons
    if now - G["pre_t"] > 30:
        G["pre_t"] = now
        log_event("person", "Person not confirmed yet (double confirmation) - only a pre-alarm")
    try:
        w.notifier.prealarm(frame)                       # with its own cooldown; only when the pre-alarm push is on
    except Exception:
        pass
    return []


def _alx_back_ask():
    """8: the phone of the owner is back - hold the person alarms and ask"""
    hold = max(10, min(600, int(CFG.get("back_hold_s", 60) or 60)))
    ALX["hold_until"] = time.time() + hold
    log_event("sys", f"Presence: your device is back - person alarms wait {hold} s («Is it you?»)")
    w = WATCH_REF.get("w")
    if w is None or not (Notifier.configured() and CFG.get("notify_on")):
        return
    pub = alx_base()
    p = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"),
         "text": trf("Your phone is back. Person alarms wait {s} s. Not you? Do nothing - the alarm comes.", s=hold),
         "info_title": "{name}: " + tr("Is it you?"), "snapshot": None, "rain": False, "wind": "", "source": STATE.get("source_label", ""),
         "link": pub + "/" if pub else "", "alx_acts": ["off"]}
    jpg = None
    try:
        f_ = w.frame_out
        if f_ is not None:
            ok_, buf = cv2.imencode(".jpg", f_, [cv2.IMWRITE_JPEG_QUALITY, 70]); jpg = buf.tobytes() if ok_ else None
    except Exception:
        jpg = None
    threading.Thread(target=w.notifier._dispatch, args=(p, jpg, "back.jpg" if jpg else ""), daemon=True).start()


def alx_start():
    if ALX["started"]:
        return
    ALX["started"] = True
    threading.Thread(target=_alx_loop, daemon=True, name="alarm-extras").start()


def _alx_loop():
    armed = bool(CFG.get("armed")); home = None; back_t = 0.0
    try:
        home = presence_home()
    except Exception:
        pass
    while True:
        time.sleep(1.0)
        try:
            a = bool(CFG.get("armed"))
            if a and not armed:                          # switched on (by hand, schedule, presence ...)
                STATE["arm_forecast"] = arm_forecast_text()
                if STATE["arm_forecast"]:
                    log_event("sys", f"Battery forecast: {arm_forecast_text('en')}")
                threading.Thread(target=_alx_announce, daemon=True, name="arm-announce").start()
            if not a:
                ALX["hold_until"] = 0.0
            armed = a
            try:
                h = presence_home()
            except Exception:
                h = None
            if h is True and home is False and presence_back_mode() == "ask":     # 2.98.15: the choice presence_back (577)
                back_t = time.time() + 3.0               # first let the presence switch off the protection by itself (150)
            home = h if h is not None else home
            if back_t and time.time() >= back_t:
                back_t = 0.0
                if CFG.get("armed"):
                    _alx_back_ask()
        except Exception as e:
            log_event("sys", f"Alarm extras: {e}"[:160])


# ---- 3: the morning push: one sentence and a picture strip of the night -------------------------------------------------
def alx_morning(r, lang=None):
    """(sentence, jpg or None) for the night report r of report_build() (090)"""
    L = cur_lang(lang)
    a, b = r.get("from") or "", r.get("to") or ""
    sight_load()
    with SIGHT_LOCK:
        ev = [dict(e) for e in SIGHT["list"] if a <= e.get("start", "") < b]
    animals = sum(1 for e in ev if e.get("label") in ANIMALS)
    persons = sum(1 for e in ev if e.get("label") == "person")
    bt = STATE.get("battery") or {}
    parts = [trf("{n} animals" if animals != 1 else "{n} animal", L, n=animals), trf("{n} persons" if persons != 1 else "{n} person", L, n=persons)]
    if bt.get("on") and bt.get("pct") is not None:
        parts.append(trf("battery {pct} %", L, pct=int(bt["pct"])))
    try:
        st, en = datetime.fromisoformat(a), datetime.fromisoformat(b)
        span = f"{st.strftime('%H')}–{en.strftime('%H')} " + tr("o'clock", L)
    except ValueError:
        span = ""
    sent = tr("Night", L) + (f" {span}" if span else "") + ": " + ", ".join(parts) + "."
    pics = [e for e in ev if e.get("img")]
    pics.sort(key=lambda e: (e.get("label") == "person", float(e.get("conf") or 0)), reverse=True)
    seen, pick = set(), []
    for e in pics:                                       # different kinds first, then the best ones
        if e.get("label") not in seen:
            seen.add(e.get("label")); pick.append(e)
    pick += [e for e in pics if e not in pick]
    pick = sorted(pick[:4], key=lambda e: e.get("start", ""))
    tiles = []
    for e in pick:
        try:
            img = cv2.imread(os.path.join(diary_dir(), e["img"]))
        except Exception:
            img = None
        if img is None:
            continue
        h, wd = img.shape[:2]
        img = cv2.resize(img, (max(1, int(wd * 200 / h)), 200), interpolation=cv2.INTER_AREA)
        if img.shape[1] > 300:                           # wide: the middle part
            x0 = (img.shape[1] - 300) // 2; img = img[:, x0:x0 + 300]
        lab = (e.get("start", "")[11:16] + " " + str(tr_trigger(e.get("label", ""), L)).split(" (")[0]).encode("ascii", "replace").decode()
        cv2.rectangle(img, (0, 0), (img.shape[1], 24), (0, 0, 0), -1)     # on top: the logo (bottom right) stays free
        cv2.putText(img, lab[:30], (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(img)
        tiles.append(np.full((200, 4, 3), 255, np.uint8))
    jpg = None
    if tiles:
        strip = cv2.hconcat(tiles[:-1])
        try:
            if CFG.get("share_logo"):
                strip = brand_image(strip, tr("Night report", L) + " " + datetime.now().strftime("%d.%m.%Y"))
        except Exception:
            pass
        ok, buf = cv2.imencode(".jpg", strip, [cv2.IMWRITE_JPEG_QUALITY, 78])
        jpg = buf.tobytes() if ok else None
    return sent, jpg


# ---- 5: zones by kind in the window (Tk) - the web page has it in the zone editor -------------------------------------
def alx_tk_zones(app, parent):
    """a short list of the ignore / only-here zones with «applies to» (everything / persons / animals)"""
    from tkinter import ttk
    box = ttk.Frame(parent); box.pack(fill="x", pady=(8, 0))
    ttk.Label(box, text=tr("Zones: applies to")).pack(anchor="w")
    rows = ttk.Frame(box); rows.pack(fill="x")
    opts = [("all", tr("everything")), ("person", tr("persons only")), ("animal", tr("animals only"))]

    def fill():
        for c in rows.winfo_children():
            c.destroy()
        zs = [z for z in ZONES if z["mode"] in ("ignore", "only")]
        if not zs:
            ttk.Label(rows, text=tr("no zones") + " · " + tr("Open zone editor (browser)"), style="Mut.TLabel").pack(anchor="w")
            return
        for z in zs:
            r = ttk.Frame(rows); r.pack(fill="x", pady=1)
            ttk.Label(r, text=f"{z['name']} ({tr('Ignore zone' if z['mode'] == 'ignore' else 'Only-here zone')})", width=28).pack(side="left")
            cb = ttk.Combobox(r, state="readonly", values=[l for _k, l in opts], width=16)
            cb.current([k for k, _l in opts].index(z.get("kinds", "all")) if z.get("kinds", "all") in ("all", "person", "animal") else 0)
            cb.pack(side="left", padx=(4, 0))

            def pick(_e=None, zid=z["id"], cb=cb):
                k = opts[cb.current()][0]
                lst = [dict(x, kinds=k) if x["id"] == zid else dict(x) for x in ZONES]
                zones_set(lst)
            cb.bind("<<ComboboxSelected>>", pick)
    fill()
    ttk.Button(box, text="↻", width=3, command=fill).pack(anchor="e")


# ---- the web part of «Was war das?» (Live page and Verlauf → Nachrichten) ------------------------------------------------
ALX_WHAT_JS = r"""(function () {
  function lng() { try { return LANG; } catch (e) { return document.documentElement.lang || "en"; } }
  var L = "", LL = "en";
  var box = document.getElementById("alx-what"), main = !box;
  if (main) {                                            // the Live page: below the picture
    var vc = document.getElementById("vcard"); if (!vc) return;
    box = document.createElement("div"); box.id = "alx-what"; vc.parentNode.insertBefore(box, vc.nextSibling);
  }
  var st = document.createElement("style");
  st.textContent = "#alx-what .aw{background:var(--panel,#18202b);border:1px solid var(--line,#2a3442);border-radius:12px;padding:10px;margin:10px 0}" +
    "#alx-what .aw-h{font-weight:700;margin-bottom:6px}#alx-what .aw-i{display:flex;gap:10px;align-items:flex-start;flex-wrap:wrap;margin-top:8px}" +
    "#alx-what .aw-p{position:relative;width:220px;max-width:100%;flex:none}#alx-what .aw-p img{width:100%;display:block;border-radius:8px;background:#000}" +
    "#alx-what .aw-p i{position:absolute;border:2px solid #ff453a;border-radius:3px}#alx-what .aw-b{display:flex;gap:6px;flex-wrap:wrap;align-items:center}" +
    "#alx-what .aw-b button{padding:7px 12px}#alx-what .aw-b button.on{outline:3px solid var(--acc,#2f81f7)}#alx-what .aw-m{color:var(--mut,#8a96a6);font-size:12.5px}" +
    "body[data-tab]:not([data-tab=live]) #alx-what{display:none}";
  document.head.appendChild(st);
  var TX = {};
  function tx(k) { return TX[k] || k; }
  function E(t, c, s) { var e = document.createElement(t); if (c) e.className = c; if (s != null) e.textContent = s; return e; }
  async function answer(id, lab, row) {
    var r = await fetch("/api/alarmlabel", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({id: id, label: lab, lang: L})})
      .then(function (x) { return x.json(); }).catch(function () { return {ok: false}; });
    if (r.ok) { if (typeof toast === "function") toast("✓ " + tx("Thanks - MoveEye learns from it.")); load(); }
    else if (typeof toast === "function") toast("⚠ " + (r.error || "error"));
  }
  function item(m) {
    var row = E("div", "aw-i"), p = E("div", "aw-p"), im = E("img"); im.loading = "lazy"; im.src = "/api/alarmlabel/img/" + m.id; im.alt = "";
    p.appendChild(im);
    (m.boxes || []).forEach(function (b) { var i = E("i"); i.style.left = (b[0] * 100) + "%"; i.style.top = (b[1] * 100) + "%";
      i.style.width = (b[2] * 100) + "%"; i.style.height = (b[3] * 100) + "%"; p.appendChild(i); });
    var bd = E("div"); var d = new Date((m.t || 0) * 1000);
    bd.appendChild(E("div", "aw-m", "🚨 " + tx("Alarm") + " " + d.toLocaleString(LL === "de" || LL === "rm" ? "de-CH" : LL, {weekday: "short", hour: "2-digit", minute: "2-digit"}) + (m.sim ? " · " + tx("simulation") : "")));
    var bs = E("div", "aw-b");
    [["person", "🚶 " + tx("Person")], ["animal", "🦊 " + tx("Animal")], ["nothing", "🍃 " + tx("Nothing")]].forEach(function (x) {
      var b = E("button", m.label === x[0] ? "on" : "sec", x[1]); b.type = "button"; b.onclick = function () { answer(m.id, x[0], row); }; bs.appendChild(b); });
    bd.appendChild(bs); row.append(p, bd); return row;
  }
  async function load() {
    L = lng();
    var r = await fetch("/api/alarmlabel?n=" + (main ? 3 : 8) + "&lang=" + encodeURIComponent(L)).then(function (x) { return x.json(); }).catch(function () { return null; });
    if (!r || !r.ok) return;
    TX = r.tx || {}; LL = r.lang || L;
    var items = (r.items || []).filter(function (m) { return main ? (!m.label && Date.now() / 1000 - m.t < 12 * 3600) : true; });
    box.textContent = "";
    if (!items.length) return;
    var c = E("div", "aw"); c.appendChild(E("div", "aw-h", "❓ " + tx("What was it?")));
    items.slice(0, main ? 1 : 8).forEach(function (m) { c.appendChild(item(m)); });
    c.appendChild(E("div", "aw-m", tx("Answers are kept as training pictures (picture + boxes); «Nothing» counts as a false alarm.")));
    box.appendChild(c);
  }
  setTimeout(load, 1200); setInterval(function () { if (!document.hidden) load(); }, 20000);
  setInterval(function () { if (lng() !== L) load(); }, 2000);    // the language was set / switched
})();
"""
