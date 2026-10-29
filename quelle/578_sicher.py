#@ MoveEye – Teil 578: «Sicher» – Aus in der Push nur mit PIN, Push nach Stromausfall, freundliche Fehlerseiten, Dunkle Ansicht, Bildschirmleser, Aufnahmen nach N Tagen löschen, Push ohne Bild. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (29.10.2026):
#  1  «Aus» in der Push-Nachricht nur mit PIN: der Knopf öffnet eine kleine Seite mit dem PIN-Feld (Schutz-PIN; ohne PIN das
#     Web-Passwort; ohne beides: «Bitte zuerst eine Schutz-PIN setzen», nichts wird ausgeschaltet). Falsche PINs: dieselbe Sperre
#     wie beim Ausschalten im Web (5 in 10 Minuten, ab 3 Diebstahl-Alarm). «Fehlalarm» und «Sirene» bleiben ohne PIN. (066)
#  2  Nach einem unsauberen Ende (Strom weg, Absturz) eine Info-Push «MoveEye war 14 Min. aus (Strom/Absturz) – jetzt wieder
#     Wachsam». Nicht nach einem Update / Neustart (die enden sauber, 390 run_state.json «clean»).
#  3  Fehlermeldungen des Web-Servers in der eigenen Sprache als kleine Seite (Anmeldung, zu viele Versuche, fremde Seite,
#     Gast-Link, unbekannte Adresse). Basic-Realm «MoveEye» (Gäste sehen ihn); das Vertrauens-Cookie bleibt gleich.
#  4  «Rotlicht-Ansicht» (bis 2.98.22 «Nachtblick», 2.98.23 «Dunkle Ansicht»): ganze Seite sehr dunkel und rot, Livebild gedimmt – für
#     einen kurzen Blick im Zelt (pro Browser gemerkt, mw-night). Ab 573 die 3. Stufe des Knopfs «Hell / dunkel»: Hell → Dunkel → Rotlicht
#     (Web 510/530 toggleTheme, Fenster ◐ mit tk_night) - kein eigener 🌑-Knopf und kein Schnellschalter mehr.
#  5  Bildschirmleser: Knöpfe und Symbole bekommen aria-label / title in der eigenen Sprache (Hauptseite, Kopf, Navigation).
#  6  «Aufnahmen nach … Tagen löschen» (0 = nie) neben der Grössen-Grenze; Knopf «Ferien vorbei: alle Aufnahmen löschen»
#     (Bestätigung; ⭐ Favoriten bleiben, ausser man hakt es an).
#  7  «Bilder in Push-Nachrichten: mitschicken / nur Text (Bild nur in MoveEye)» für ntfy, Telegram und Pushover (060).
# ----------------------------------------------------------------------------
_SX_CFG = {"rec_keep_days": 0, "push_pics": "with", "tk_night": False}
for _k, _v in _SX_CFG.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)

SX = {"lock": threading.Lock(), "pw_fails": [], "hk": False, "last_prune": 0.0, "pc": None}
WEB_UI_LOCAL.add("mw-night")                         # 4: the night view is per browser (not copied to the other devices)


# ---- settings (web and window read the same lists) -----------------------------------------------------------------------
def _sx_put_after(lst, after_key, item, idx=1):
    lst[:] = [x for x in lst if x[idx] != item[idx]]
    for i, x in enumerate(lst):
        if x[idx] == after_key:
            lst.insert(i + 1, item)
            return
    lst.append(item)


_sx_put_after(SLIDERS, "record_max_gb", ("Recording", "rec_keep_days", "Delete recordings after … days (0 = never)", 0, 365, 1))
_sx_put_after(TEXTS, "notify_type", ("Notifications", "push_pics", "Pictures in push messages", "enum", "push_pics"))
TEXT_SPECS["push_pics"] = ("enum", "push_pics")
SIMPLE_KEYS.update({"rec_keep_days", "push_pics"})
SX_PUSH_PICS = (("with", "send along"), ("text", "text only (picture only in MoveEye)"))

_text_choice_pairs_before_sx = text_choice_pairs


def text_choice_pairs(key):                                 # + 7: pictures in push messages
    if TEXT_SPECS.get(key, (None, None))[1] == "push_pics":
        return [(k, tr(l)) for k, l in SX_PUSH_PICS]
    return _text_choice_pairs_before_sx(key)


# ---- 7: push without picture ---------------------------------------------------------------------------------------------
def sx_push_jpg(jpg):
    """the picture for ntfy / Telegram / Pushover - None when the owner wants text only (the picture stays in MoveEye)"""
    return None if CFG.get("push_pics") == "text" else jpg


# ---- 1: «Off» in the push message only with the PIN ----------------------------------------------------------------------
def sx_off_mode():
    """how «Off» from a push message is confirmed: pin / pw (web password) / none (nothing set: not possible)"""
    if CFG.get("protect_pin"):
        return "pin"
    if web_pw_active():
        return "pw"
    return "none"


def sx_off_check(pin="", pw="", source="push button"):
    """(ok, error) - the same lock as disarming on the web page: 5 wrong tries in 10 minutes, from 3 on a theft alarm"""
    now = time.time()
    mode = sx_off_mode()
    if mode == "none":
        return False, "Please set a protection PIN first"
    if mode == "pin":
        PROTECT["pin_fails"] = [t for t in PROTECT["pin_fails"] if now - t < 600]
        if len(PROTECT["pin_fails"]) >= 5:
            return False, "too many wrong PINs - try again in 10 minutes"
        if protect_pin_ok(pin) and str(pin or "").strip():
            PROTECT["pin_fails"] = []
            return True, ""
        PROTECT["pin_fails"].append(now)
        log_event("sys", f"Protection: wrong PIN for disarming ({source})")
        if len(PROTECT["pin_fails"]) >= 3:
            w = WATCH_REF.get("w")
            try:
                if w is not None:
                    w.notifier.tamper(tr("Somebody tries to disarm with a wrong PIN"), w.frame_out)
            except Exception:
                pass
            try:
                siren_alarm("tamper")
            except Exception:
                pass
        return False, "wrong PIN"
    with SX["lock"]:
        SX["pw_fails"] = [t for t in SX["pw_fails"] if now - t < 600]
        if len(SX["pw_fails"]) >= 5:
            return False, "too many wrong passwords - try again in 10 minutes"
    who = user_login("", str(pw or "")) if pw else None
    if who and who[1] == "admin":
        with SX["lock"]:
            SX["pw_fails"] = []
        return True, ""
    with SX["lock"]:
        SX["pw_fails"].append(now)
    log_event("web", f"Wrong web password for «Off» in the push message ({source})")
    return False, "wrong password"


def sx_off_form(lang, err=""):
    """the small form under «Off» (PIN or web password); without either only the note"""
    import html as _h
    E = lambda s: _h.escape(tr(s, lang))
    mode = sx_off_mode()
    if mode == "none":
        return ('<p class="err">' + E("Please set a protection PIN first") + "</p><p>" + E("MoveEye → Protection → PIN. Until then «Off» works only on the page of MoveEye.") + "</p>")
    if mode == "pin":
        fld = ('<label for="pin">' + E("Protection PIN") + '</label><input id="pin" name="pin" type="password" inputmode="numeric" '
               'pattern="[0-9]*" maxlength="8" autocomplete="one-time-code" autofocus required>')
    else:
        fld = ('<label for="pw">' + E("Web password") + '</label><input id="pw" name="pw" type="password" autocomplete="current-password" autofocus required>')
    return ((('<p class="err" role="alert">⚠ ' + _h.escape(tr_err(err, lang)) + "</p>") if err else "")
            + '<form method="post">' + fld + '<button type="submit">⏻ ' + E("Switch the protection off") + "</button></form>")


# ---- 3: friendly error pages in the own language -------------------------------------------------------------------------
SX_PAGE = """<!doctype html><html lang="%(lang)s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>MoveEye</title><style>
:root{--bg:#0a0e14;--panel:#111822;--txt:#e8eef5;--mut:#8a9bb0;--acc:#3b8cff;--red:#ff6b6b}
@media(prefers-color-scheme:light){:root{--bg:#eef2f7;--panel:#fff;--txt:#18212d;--mut:#5a6b80;--acc:#1f6feb;--red:#d1242f}}
html.sxnight{--bg:#000;--panel:#0a0000;--txt:#b8322a;--mut:#7d1f1a;--acc:#7a160e;--red:#c0392b}
body{font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--txt);margin:0;display:flex;min-height:100vh;
align-items:center;justify-content:center;padding:16px;box-sizing:border-box}
main{background:var(--panel);border-radius:16px;padding:24px;max-width:380px;width:100%%;text-align:center;box-shadow:0 8px 30px rgba(0,0,0,.25)}
.ic{font-size:40px;line-height:1}h1{font-size:21px;margin:10px 0 6px}p{color:var(--mut);margin:8px 0}.err{color:var(--red);font-weight:600}
label{display:block;text-align:left;font-size:14px;color:var(--mut);margin:14px 0 4px}
input{width:100%%;box-sizing:border-box;font-size:20px;padding:10px 12px;border-radius:10px;border:1px solid var(--mut);background:var(--bg);color:var(--txt);letter-spacing:.15em}
button,.btn{display:inline-block;font-size:17px;padding:12px 22px;border-radius:12px;border:0;background:var(--acc);color:#fff;margin-top:14px;text-decoration:none;cursor:pointer}
button{width:100%%}a{color:var(--acc)}
</style><script>try{if(localStorage.getItem("mw-night")==="1")document.documentElement.classList.add("sxnight")}catch(e){}</script></head>
<body><main><div class="ic" aria-hidden="true">%(ic)s</div><h1>%(h)s</h1>%(body)s</main></body></html>"""

SX_ERRS = {   # key: (symbol, title, text)
    "login": ("🔒", "Login required", "This MoveEye is protected with a password. Reload the page and enter the password (any user name)."),
    "toomany": ("⏳", "Too many wrong passwords", "For safety the login is blocked for a few minutes. Please wait 5 minutes and try again."),
    "foreign": ("🛡", "Request blocked", "This action came from another web page and was refused for your safety. Open MoveEye directly and try again."),
    "guest": ("⌛", "Guest link not valid", "This guest link is not valid (any more). Ask the owner for a new link."),
    "keys": ("⏳", "Too many wrong keys", "Too many wrong keys from this device. Please wait 10 minutes."),
    "notfound": ("🧭", "Page not found", "This address does not exist on MoveEye."),
    "error": ("⚠", "Something went wrong", "MoveEye could not answer this request. Please try again in a moment."),
}


def sx_req_lang():
    """the language of a request without a page: ?lang=, the saved page language is unknown here - so the browser
    language (Accept-Language), else the language of the device"""
    try:
        from flask import request
        q = str(request.args.get("lang") or "")[:2].lower()
        if q in LANGS:
            return q
        for part in str(request.headers.get("Accept-Language") or "").split(","):
            c = part.strip()[:2].lower()
            if c in LANGS:
                return c
            if c == "gs":                                    # Swiss German (gsw)
                return "de"
    except Exception:
        pass
    return cur_lang()


def sx_page(h, body_html, ic="🛡", lang=None):
    import html as _h
    L = lang or sx_req_lang()
    return SX_PAGE % {"lang": L, "ic": ic, "h": _h.escape(h), "body": body_html}


def sx_wants_html():
    try:
        from flask import request
        return "text/html" in (request.headers.get("Accept") or "") and not request.path.startswith("/api/")
    except Exception:
        return False


def sx_err(code, key, headers=None):
    """a refused request: a small page in the own language for a browser, a short translated text for programs"""
    from flask import Response
    import html as _h
    L = sx_req_lang()
    ic, h, txt = SX_ERRS.get(key) or SX_ERRS["error"]
    if sx_wants_html():
        extra = ""
        if key in ("login", "foreign", "notfound", "toomany"):
            extra = '<a class="btn" href="/">' + _h.escape(tr("To the start page", L)) + "</a>"
        return Response(sx_page(tr(h, L), "<p>" + _h.escape(tr(txt, L)) + "</p>" + extra, ic, L), code, headers or {}, mimetype="text/html")
    return Response(tr(h, L) + ": " + tr(txt, L), code, headers or {}, mimetype="text/plain")


# ---- 2: a push after an unclean end (power cut, crash) -------------------------------------------------------------------
def sx_fmt_dur(sec, lang=None):
    m = int(round(max(0.0, float(sec)) / 60.0))
    if m < 1:
        return tr("less than a minute", lang)
    if m < 120:
        return trf("{m} min.", lang, m=m)
    return trf("{h} h {m} min.", lang, h=m // 60, m=m % 60)


def sx_unclean_info(prev):
    """from the run_state.json of the last run: None when it ended cleanly (update, restart, stop) or is unusable,
    else {"t_end": time of the last sign of life, "ran_s": how long it ran}"""
    if not isinstance(prev, dict) or prev.get("clean"):
        return None
    try:
        start = float(prev.get("start") or 0); up = max(0, int(prev.get("up") or 0))
    except (TypeError, ValueError):
        return None
    if start <= 0:
        return None
    return {"t_end": start + up, "ran_s": up}


def sx_unclean_text(info, now=None, lang=None, state=None):
    """«MoveEye war 14 Min. aus (Strom/Absturz) – jetzt wieder Wachsam»; an implausible clock (no internet time yet) -> no duration"""
    now = time.time() if now is None else now
    st = state if state is not None else protect_label(STATE.get("arm_state"), STATE.get("arm_left", 0), lang)
    off = now - float(info.get("t_end") or 0)
    if 0 <= off < 400 * 86400:
        return trf("MoveEye was off for {dur} (power cut / crash) – now {state} again", lang, dur=sx_fmt_dur(off, lang), state=st)
    return trf("MoveEye was off (power cut / crash) – now {state} again", lang, state=st)


def _sx_unclean_tell(info):
    """after the start: wait until the messages can go out and the clock is plausible (a Pi without a clock battery gets
    the right time from the internet only after a while), then one info push"""
    time.sleep(45)
    t0 = time.time()
    while time.time() - float(info["t_end"]) < 0 and time.time() - t0 < 600:
        time.sleep(15)
    for _i in range(30):                                   # the camera loop (and its notifier) may need a moment
        w = WATCH_REF.get("w")
        if w is not None and getattr(w, "notifier", None) is not None:
            break
        time.sleep(5)
    w = WATCH_REF.get("w")
    txt = sx_unclean_text(info)
    SX["pc"] = {"text": txt, "t": time.time()}
    log_event("sys", "Back after an unexpected end: " + sx_unclean_text(info, lang="en"))
    if w is None:
        return
    try:
        w.notifier.info(txt, title="{name}: " + tr("Back on"))
    except Exception as e:
        log_event("sys", f"Push after the unexpected end not sent: {e}"[:160])


_run_guard_start_before_sx = run_guard_start


def run_guard_start():
    """+ 2: the last run ended without a clean stop -> one info push with how long MoveEye was off (not with the safe start:
    that one sends its own message)"""
    prev = None
    if not DEMO["on"]:
        try:
            with open(_run_file()) as f:
                prev = json.load(f)
        except (OSError, ValueError):
            prev = None
    _run_guard_start_before_sx()
    sx_housekeeping_start()
    info = sx_unclean_info(prev) if not DEMO["on"] else None
    if info and not RUNGUARD.get("safe"):
        threading.Thread(target=_sx_unclean_tell, args=(info,), daemon=True, name="sx-back").start()


# ---- 6: recordings older than N days; «holiday over: delete all» ---------------------------------------------------------
_SX_REC_EXT = {".mp4", ".jpg", ".jpeg", ".json", ".wav", ".m4a", ".aac", ".avi", ".mkv", ".webm", ".png", ".gpx", ".srt", ".txt"}
_SX_REC_MAIN = {".mp4", ".jpg", ".jpeg", ".avi", ".mkv", ".webm"}


def _sx_rec_groups():
    """{stem: [files]} of the recordings folder (only recordings: a video or picture belongs to every group)"""
    groups = {}
    try:
        names = os.listdir(rec_dir())
    except OSError:
        return {}
    for n in names:
        p = os.path.join(rec_dir(), n)
        stem, ext = os.path.splitext(n)
        if n.startswith(".") or ext.lower() not in _SX_REC_EXT or not os.path.isfile(p):
            continue
        groups.setdefault(stem, []).append(p)
    return {k: v for k, v in groups.items() if any(os.path.splitext(f)[1].lower() in _SX_REC_MAIN for f in v)}


def _sx_live(fs):
    names = {os.path.basename(f) for f in fs}
    if names & set(LIVE_RECS):
        return True
    w = WATCH_REF.get("w")
    rn = os.path.basename(str(getattr(w, "rec_name", "") or "")) if w is not None else ""
    return bool(rn and rn in names)


def _sx_fav(stem):
    try:
        return bool(_read_sidecar(stem + ".json").get("fav"))
    except Exception:
        return False


def _sx_remove(stem, fs):
    for f in fs:
        try:
            os.remove(f)
        except OSError:
            pass
    try:
        rec_purge_extras(stem)
    except Exception:
        pass


def sx_rec_prune(days=None, now=None):
    """delete the recordings older than «rec_keep_days» days (0 = never); favourites stay. Returns the number deleted."""
    days = int(CFG.get("rec_keep_days") or 0) if days is None else int(days)
    if days <= 0:
        return 0
    now = time.time() if now is None else now
    limit = now - days * 86400
    n = 0
    for stem, fs in _sx_rec_groups().items():
        try:
            mt = max(os.path.getmtime(f) for f in fs)
        except OSError:
            continue
        if mt >= limit or _sx_fav(stem) or _sx_live(fs):
            continue
        _sx_remove(stem, fs); n += 1
    if n:
        log_event("rec", f"Cleanup: {n} recording(s) older than {days} days deleted")
    return n


def sx_rec_wipe(with_favs=False, who="web"):
    """«Holiday over»: all recordings (and the continuous recording) - favourites only when asked. Returns (deleted, kept)."""
    n = kept = 0
    for stem, fs in _sx_rec_groups().items():
        if _sx_live(fs):
            kept += 1; continue
        if not with_favs and _sx_fav(stem):
            kept += 1; continue
        _sx_remove(stem, fs); n += 1
    lr = globals().get("LOOPREC")                         # the continuous recording too (not the piece being written)
    cur = str(getattr(lr, "cur", "") or "")
    base = os.path.join(rec_dir(), "loop")
    for root, _dirs, files in os.walk(base, topdown=False):
        for fn in files:
            rel = "loop/" + os.path.relpath(os.path.join(root, fn), base).replace(os.sep, "/")
            if rel != cur and fn.lower().endswith((".mp4", ".jpg", ".json")):
                try:
                    os.remove(os.path.join(root, fn))
                except OSError:
                    pass
        if root != base:
            try:
                os.rmdir(root)
            except OSError:
                pass
    STATE["rec_dir_mb"] = 0 if not kept else STATE.get("rec_dir_mb", 0)
    log_event("rec", f"Holiday over: {n} recording(s) deleted, {kept} kept" + (" (favourites too)" if with_favs else "") + f" ({who})")
    return n, kept


def sx_rec_counts():
    g = _sx_rec_groups()
    favs = sum(1 for s in g if _sx_fav(s))
    return {"all": len(g), "favs": favs}


def sx_housekeeping_start():
    """one quiet thread: the age limit once an hour (the size limit runs before every recording, 410)"""
    if SX["hk"] or DEMO["on"]:
        return
    SX["hk"] = True

    def run():
        time.sleep(300)
        while True:
            try:
                if int(CFG.get("rec_keep_days") or 0) > 0:
                    sx_rec_prune(); SX["last_prune"] = time.time()
            except Exception as e:
                log_event("rec", f"Cleanup by age failed: {e}"[:160])
            time.sleep(3600)
    threading.Thread(target=run, daemon=True, name="sx-housekeeping").start()


# ---- the web addresses (called once by the web server, 550) --------------------------------------------------------------
def sx_routes(app, watch, reply, body):
    from flask import Response, request, g

    @app.route("/sx/ui.js")
    def sx_ui_js():
        return Response(sx_ui_js_text(), mimetype="application/javascript", headers={"Cache-Control": "no-cache"})

    @app.route("/api/sx/recwipe", methods=["GET", "POST"])
    def api_sx_recwipe():
        if request.method == "GET":
            return reply(dict(sx_rec_counts(), ok=True, keep_days=int(CFG.get("rec_keep_days") or 0)))
        if getattr(g, "role", "admin") != "admin":
            return reply({"ok": False, "error": "not allowed"}, 403)
        d = body(); lang = norm_lang(d.get("lang"))
        if d.get("confirm") is not True:
            return reply({"ok": False, "error": tr("please confirm", lang)}, 400)
        n, kept = sx_rec_wipe(bool(d.get("favs")), "web")
        return reply({"ok": True, "deleted": n, "kept": kept,
                      "text": trf("{n} recordings deleted, {k} kept", lang, n=n, k=kept)})

    @app.errorhandler(404)
    def sx_not_found(_e):
        if sx_wants_html():
            return sx_err(404, "notfound")
        return Response("not found", 404, mimetype="text/plain")


# ---- 4 + 5: night view and screen readers (all pages through render_page) ------------------------------------------------
SX_NIGHT_CSS = """<style id="sx-night-css">
html.sxnight,html.sxnight body,html.sxnight body.light{--bg:#000;--panel:#070000;--panel2:#0a0101;--line:#2a0606;--txt:#c0392b;--mut:#7d1f1a;--acc:#7a160e;
--acc2:#8e1b12;--red:#d03020;--grn:#8a2a12;--yel:#8a3a12;--blu:#7a1f2a;--org:#9a3010;--pur:#7a1f3a;--field:#050000;--btn2:#120202;--hdr:rgba(0,0,0,.94);
--glow:transparent;--shadow:none;color-scheme:dark}
html.sxnight body{background:#000!important;color:var(--txt)!important}
html.sxnight img,html.sxnight video,html.sxnight canvas{filter:grayscale(1) brightness(.38) contrast(1.1)}
html.sxnight::after{content:"";position:fixed;inset:0;background:#b81400;mix-blend-mode:multiply;pointer-events:none;z-index:2147483647}
html.sxnight button,html.sxnight .btn,html.sxnight input,html.sxnight select,html.sxnight textarea{background-color:#0d0101!important;color:#b8322a!important;border-color:#3a0a08!important}
html.sxnight .badge{background:#0d0101!important;color:#a52a20!important;border-color:#3a0a08!important}
#btn-theme.thred{background:#5a0d08!important;color:#ff6a50!important}
.sx-sr{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
</style><script>try{if(localStorage.getItem("mw-night")==="1")document.documentElement.classList.add("sxnight")}catch(e){}</script>"""

# the texts the script needs (English key -> translated by the page language)
SX_JS_KEYS = ["Red light view", "Light", "Dark", "Light / dark / red light", "View", "Settings panel", "Full screen", "Light / dark", "Language", "Exit full screen", "Close", "Copy", "Standard text",
              "Up", "Down", "Remove", "Edit", "Refresh", "Help", "Menu", "Play", "Pause", "Stop", "Delete", "Back", "Next", "Previous", "Settings",
              "Live picture", "Main navigation", "Sub navigation", "Show settings", "Hide settings", "More", "Search", "Expand all", "Collapse all",
              "Listen", "Centre", "Other side", "Take a photo", "Favourite", "Download", "Share", "Zoom in", "Zoom out", "Mute", "Sound on",
              "Holiday over: delete all recordings", "Also delete the favourites ⭐", "Delete ALL recordings now? This cannot be undone.",
              "Favourites ⭐ are kept.", "recordings", "favourites", "Deleting …", "{n} recordings deleted, {k} kept", "Simulation off",
              "Protection state", "Persons", "Self-check", "Operator mode", "Mode", "Battery", "Recording",
              "Operate with the finger (otherwise the page scrolls)", "Finger: rotate instead of move", "Large picture"]


def sx_ui_tx():
    out = {}
    for L in ("de", "fr", "it", "rm"):
        out[L] = {k: tr(k, L) for k in SX_JS_KEYS if tr(k, L) != k}
    return out


SX_UI_JS = r"""(function () {
if (window._sxui) return; window._sxui = 1;
const TX = /*TX*/{};
const D = document, H = D.documentElement;
const L = () => { try { return (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || /*DL*/"de"; } catch (e) { return /*DL*/"de"; } };
const T = k => { const l = L(), m = TX[l] || {}; if (m[k]) return m[k];
  try { if (typeof t === "function") { const x = t(k); if (x && x !== k) return x; } } catch (e) {}
  if (l === "rm" && TX.de[k]) return TX.de[k]; return k; };
const say = m => { if (typeof toast === "function") { try { toast(m); return; } catch (e) {} }
  let e = D.getElementById("sx-toast"); if (!e) { e = D.createElement("div"); e.id = "sx-toast"; e.setAttribute("role", "status");
    e.style.cssText = "position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:9999;background:#111822;color:#e8eef5;padding:9px 16px;border-radius:12px;font:14px system-ui;max-width:90vw"; D.body.appendChild(e); }
  e.textContent = m; e.hidden = false; clearTimeout(e._t); e._t = setTimeout(() => { e.hidden = true; }, 2600); };
// German texts of this script also for the page itself (quick switch label)
try { if (typeof I18N !== "undefined" && I18N.de) Object.keys(TX.de || {}).forEach(k => { if (!I18N.de[k]) I18N.de[k] = TX.de[k]; }); } catch (e) {}

// ---- 4: «Rotlicht-Ansicht» = the 3rd step of the button «Hell / dunkel» (toggleTheme in 510 / 530: Hell → Dunkel → Rotlicht) ----
const STEP = {light: "Light", dark: "Dark", red: "Red light view"};
const stepNow = () => H.classList.contains("sxnight") ? "red" : (typeof THEME !== "undefined" && THEME === "light") ? "light" : "dark";
function paintN() { const b = D.getElementById("btn-theme"); if (!b) return; const s = stepNow(), n = {light: "dark", dark: "red", red: "light"}[s];
  const tt = T("Light / dark / red light") + ": " + T(STEP[s]) + " → " + T(STEP[n]);
  if (b.getAttribute("title") !== tt) { b.setAttribute("title", tt); b.setAttribute("aria-label", tt); b.dataset.sxA = tt; b.dataset.sxT = tt; }
  b.classList.toggle("thred", s === "red"); }
window.sxThemeSaid = n => { paintN(); say((n === "red" ? "◉ " : n === "light" ? "☀ " : "☾ ") + T(STEP[n])); };

// ---- 5: names for screen readers ----
const ID = {"btn-view": "View", "btn-side": "Settings panel", "btn-fs": "Full screen", "btn-lang": "Language",
  "vo-exit": "Exit full screen", "side-close": "Hide settings", "side-open": "Show settings", "all-open": "Expand all",
  "all-close": "Collapse all", "b-sim": "Simulation off", "b-arm": "Protection state", "b-health": "Self-check", "b-lock": "Operator mode", "b-mode": "Mode",
  "btn-listen": "Listen", "stick-listen": "Listen", "lv-vin": "Zoom in", "lv-vout": "Zoom out", "lv-vctl": "Operate with the finger (otherwise the page scrolls)",
  "lv-vrot": "Finger: rotate instead of move", "lv-vbig": "Large picture"};
const SYM = {"✕": "Close", "✖": "Close", "×": "Close", "⧉": "Copy", "↺": "Standard text", "▲": "Up", "▼": "Down", "▶": "Play", "►": "Play", "⏸": "Pause",
  "⏹": "Stop", "■": "Stop", "🗑": "Delete", "🗑️": "Delete", "✏️": "Edit", "✏": "Edit", "🔄": "Refresh", "↻": "Refresh", "?": "Help", "☰": "Menu", "⚙": "Settings",
  "⚙️": "Settings", "←": "Back", "‹": "Previous", "›": "Next", "→": "Next", "⋯": "More", "…": "More", "🔍": "Search", "📷": "Take a photo", "⭐": "Favourite",
  "☆": "Favourite", "★": "Favourite", "⬇": "Download", "📤": "Share", "+": "Zoom in", "−": "Zoom out", "-": "Zoom out", "＋": "Zoom in", "－": "Zoom out", "🔇": "Mute", "🔊": "Sound on", "◀": "Back"};
const word = s => /[A-Za-zÀ-ÖØ-öø-ÿ]{2,}/.test(s || "");
function nameOf(e) {
  const tx = (e.textContent || "").trim();
  if (e.id && ID[e.id]) return T(ID[e.id]);
  if (e.dataset && e.dataset.vlabel) return T(e.dataset.vlabel);
  const ti = e.getAttribute("title"); if (ti) return ti;
  if (SYM[tx]) return T(SYM[tx]);
  return "";
}
function fixTitle(e) {                       // English titles written into the HTML: in the page language
  const ti = e.getAttribute("title"); if (!ti) return;
  if (e.dataset.sxT === ti && e.dataset.sxEn) { const n = T(e.dataset.sxEn); if (n !== ti) { e.setAttribute("title", n); e.dataset.sxT = n; } return; }
  const n = T(ti); if (n !== ti) { e.dataset.sxEn = ti; e.setAttribute("title", n); e.dataset.sxT = n; }
}
function label(e) {
  fixTitle(e);
  const own = e.getAttribute("aria-label"); if (own && e.dataset.sxA !== own) return;     // the page named it itself
  const tx = (e.textContent || "").trim();
  if (word(tx) && !(e.id && ID[e.id])) { if (e.dataset.sxA) { e.removeAttribute("aria-label"); delete e.dataset.sxA; } return; }
  const n = nameOf(e); if (!n) return;
  const full = (e.classList.contains("badge") && tx && !SYM[tx] && !(e.id && ID[e.id] && e.id !== "b-arm")) ? n + ": " + tx : n;
  if (own !== full) { e.setAttribute("aria-label", full); e.dataset.sxA = full; }
  if (!e.getAttribute("title") || (e.id && ID[e.id] && e.getAttribute("title") !== n && !e.dataset.sxEn)) { e.setAttribute("title", n); e.dataset.sxT = n; }
}
function pass() {
  paintN();
  D.querySelectorAll("button,[role=button],a.ic,header .badge,.qsw button").forEach(e => { try { label(e); } catch (x) {} });
  D.querySelectorAll("header .badge[onclick],header .badge[style*=pointer]").forEach(e => { if (!e.hasAttribute("role")) { e.setAttribute("role", "button"); e.tabIndex = 0;
    e.addEventListener("keydown", ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); e.click(); } }); } });
  D.querySelectorAll("header .badge:not([role])").forEach(e => { if (!word(e.textContent)) e.setAttribute("role", "img"); });
  D.querySelectorAll("#video,#lv-vimg").forEach(e => { if (!e.getAttribute("alt")) e.setAttribute("alt", T("Live picture")); });
  const nv = D.querySelector("nav.nav"); if (nv) nv.setAttribute("aria-label", T("Main navigation"));
  const sn = D.querySelector("nav.subnav"); if (sn) sn.setAttribute("aria-label", T("Sub navigation"));
  D.querySelectorAll("nav.nav a.on,nav.subnav a.on").forEach(a => a.setAttribute("aria-current", "page"));
  D.querySelectorAll("nav.nav a").forEach(a => { const s = a.querySelector(".nl"); if (s && !a.getAttribute("aria-label")) a.setAttribute("aria-label", s.textContent.trim()); });
  recBox();
}
let tm = null, lastL = "";
const soon = () => { clearTimeout(tm); tm = setTimeout(pass, 250); };
// ---- 6: «holiday over» in the settings section «Recording» ----
function recBox() {
  const d = D.querySelector('#settings details[data-view="sec:Recording"]'); if (!d || d.querySelector(".sx-wipe")) return;
  const box = D.createElement("div"); box.className = "sl sx-wipe";
  const b = D.createElement("button"); b.type = "button"; b.className = "sec"; b.style.width = "100%"; b.textContent = "🧹 " + T("Holiday over: delete all recordings");
  const lab = D.createElement("label"); lab.className = "row"; lab.style.cssText = "gap:8px;justify-content:flex-start;font-size:13px";
  const cb = D.createElement("input"); cb.type = "checkbox"; lab.append(cb, D.createTextNode(" " + T("Also delete the favourites ⭐")));
  const info = D.createElement("div"); info.className = "mut"; info.style.fontSize = "12px"; info.setAttribute("role", "status");
  const load = () => fetch("/api/sx/recwipe").then(r => r.json()).then(j => { info.textContent = j.all + " " + T("recordings") + " · " + j.favs + " " + T("favourites"); }).catch(() => {});
  b.onclick = async () => { if (!confirm(T("Delete ALL recordings now? This cannot be undone.") + (cb.checked ? "" : "\n" + T("Favourites ⭐ are kept.")))) return;
    b.disabled = true; info.textContent = T("Deleting …");
    try { const r = await (await fetch("/api/sx/recwipe", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({confirm: true, favs: cb.checked, lang: L()})})).json();
      say(r.ok ? "✓ " + r.text : "⚠ " + (r.error || "error")); } catch (e) { say("⚠ error"); }
    b.disabled = false; cb.checked = false; load(); };
  box.append(b, lab, info); d.appendChild(box); load();
}
function start() {
  pass();
  try { new MutationObserver(soon).observe(D.body, {childList: true, subtree: true}); } catch (e) {}
  setInterval(() => { if (L() !== lastL) { lastL = L(); pass(); } }, 1500);
}
if (D.readyState === "loading") D.addEventListener("DOMContentLoaded", start); else start();
})();
"""


def sx_ui_js_text():
    return (SX_UI_JS.replace("/*TX*/{}", json.dumps(sx_ui_tx(), ensure_ascii=False))
            .replace('/*DL*/"de"', json.dumps(cur_lang())).replace("</", "<\\/"))


_render_page_before_sx = render_page


def render_page(page, active):
    """+ 4 / 5: the night view (before the first paint, no flash) and the script with the names for screen readers"""
    out = _render_page_before_sx(page, active)
    out = out.replace("</head>", SX_NIGHT_CSS + "</head>", 1)
    i = out.rfind("</body>")
    tag = '<script src="/sx/ui.js?v=' + APP_VERSION + '" defer></script>'
    return out[:i] + tag + out[i:] if i >= 0 else out + tag


# ---- window (Tkinter): night view ◑ and «holiday over» -----------------------------------------------------------------
SX_TK_NIGHT = {"bg": "#000000", "panel": "#0a0000", "line": "#2a0606", "txt": "#c0392b", "mut": "#7d1f1a", "acc": "#6e140c", "red": "#d03020",
               "grn": "#8a2a12", "yel": "#8a3a12", "blu": "#7a1f2a", "org": "#9a3010", "pur": "#7a1f3a", "field": "#050000", "knob_off": "#1a0402",
               "badge_red_bg": "#100000"}
_apply_theme_before_sx = apply_theme


def apply_theme():
    _apply_theme_before_sx()
    if CFG.get("tk_night"):
        C.update(SX_TK_NIGHT)


def tk_theme_step():
    """the window: «light», «dark» or «red» (Rotlicht-Ansicht = tk_night on top of dark)"""
    return "red" if CFG.get("tk_night") else ("light" if CFG.get("theme") == "light" else "dark")


def tk_theme_tip():
    s = tk_theme_step(); n = {"light": "dark", "dark": "red", "red": "light"}[s]
    nm = {"light": "Light", "dark": "Dark", "red": "Red light view"}
    return tr("Light / dark / red light") + ": " + tr(nm[s]) + " → " + tr(nm[n])


def _sx_tk_toggle_theme(self):
    """the button ◐ (and Ctrl+T): Hell → Dunkel → Rotlicht → Hell"""
    n = {"light": "dark", "dark": "red", "red": "light"}[tk_theme_step()]
    CFG["tk_night"] = n == "red"
    self._set("theme", "light" if n == "light" else "dark")
    save_settings()
    self._rebuild()


def _sx_tk_update_video(self):
    """like 570, plus the night view: the picture grey, dark and red"""
    try:
        frame = self.watch.frame_out
        if frame is not None and self.video is not None and self.video.winfo_exists():
            w = max(160, self.video.winfo_width()); h = max(90, self.video.winfo_height())
            fh, fw = frame.shape[:2]; scale = min(w / fw, h / fh)
            small = cv2.resize(frame, (max(1, int(fw * scale)), max(1, int(fh * scale))))
            if CFG.get("tk_night"):
                gy = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                img = np.zeros((gy.shape[0], gy.shape[1], 3), dtype=np.uint8); img[:, :, 0] = (gy * 0.42).astype(np.uint8)
            else:
                img = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            pim = Image.fromarray(img)
            if getattr(self, "_egg_t0", 0):
                pim = self._egg_draw(pim)
            self.photo = ImageTk.PhotoImage(pim); self.video.config(image=self.photo)
    finally:
        self.root.after(33, self._update_video)


def _sx_tk_build_section(self, sec, sbody, settings_parent=None):
    _sx_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec != "Recording":
        return
    try:
        ttk.Button(sbody, text="🧹 " + tr("Holiday over: delete all recordings") + " …", command=lambda: _sx_tk_wipe(self)).pack(fill="x", pady=(8, 0))
    except Exception:
        pass


def _sx_tk_wipe(app):
    """the confirmation: how many, favourites kept unless ticked"""
    c = sx_rec_counts()
    win = tk.Toplevel(app.root); win.title("MoveEye"); win.configure(bg=C["panel"]); win.transient(app.root)
    tk.Label(win, text="🧹 " + tr("Holiday over: delete all recordings"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
    tk.Label(win, text=f"{c['all']} {tr('recordings')} · {c['favs']} {tr('favourites')}\n" + tr("Delete ALL recordings now? This cannot be undone."),
             bg=C["panel"], fg=C["mut"], justify="left", wraplength=360).pack(anchor="w", padx=14)
    fv = tk.BooleanVar(value=False)
    tk.Checkbutton(win, text=tr("Also delete the favourites ⭐"), variable=fv, bg=C["panel"], fg=C["txt"], selectcolor=C["field"],
                   activebackground=C["panel"], activeforeground=C["txt"]).pack(anchor="w", padx=10, pady=(6, 0))
    bf = tk.Frame(win, bg=C["panel"]); bf.pack(fill="x", padx=14, pady=12)

    def go():
        n, k = sx_rec_wipe(bool(fv.get()), "window")
        win.destroy()
        try:
            app._status("Recording", "✓ " + trf("{n} recordings deleted, {k} kept", n=n, k=k))
        except Exception:
            pass
        messagebox.showinfo("MoveEye", trf("{n} recordings deleted, {k} kept", n=n, k=k))
    ttk.Button(bf, text=tr("Cancel"), command=win.destroy).pack(side="right")
    ttk.Button(bf, text=tr("Delete"), command=go).pack(side="right", padx=(0, 6))


_sx_tk_build_section_before = App._build_section
# wraps: App.toggle_theme
App.toggle_theme = _sx_tk_toggle_theme
# wraps: App._build_section
App._build_section = _sx_tk_build_section
# wraps: App._update_video
App._update_video = _sx_tk_update_video


# ---- --self-test ---------------------------------------------------------------------------------------------------------
def sicher_selftest():
    """the parts that can be checked without hardware: unclean end -> text, push without picture, recordings by age,
    «holiday over», the PIN gate, error pages, the script of the pages"""
    import tempfile
    keep = {k: CFG.get(k) for k in ("push_pics", "rec_keep_days", "record_dir", "protect_pin", "web_pw_hash", "web_password")}
    fails = list(PROTECT["pin_fails"])
    try:
        now = 1_800_000_000.0
        assert sx_unclean_info({"clean": True, "start": now - 100, "up": 50}) is None, "a clean end gives no push"
        assert sx_unclean_info(None) is None and sx_unclean_info({"clean": False}) is None
        inf = sx_unclean_info({"clean": False, "start": now - 3600, "up": 2760})
        assert inf and abs(inf["t_end"] - (now - 840)) < 1e-6
        tx = sx_unclean_text(inf, now, "de", "Wachsam")
        assert "14 Min." in tx and "Wachsam" in tx and "aus" in tx, tx
        assert "(" in sx_unclean_text(inf, now - 5000, "de", "Aus") and "Min." not in sx_unclean_text(inf, now - 5000, "de", "Aus"), "clock behind: no duration"
        assert sx_fmt_dur(125 * 60, "en") == "2 h 5 min." and "2 Std. 5 Min." == sx_fmt_dur(125 * 60, "de")
        CFG["push_pics"] = "text"; assert sx_push_jpg(b"x") is None
        CFG["push_pics"] = "with"; assert sx_push_jpg(b"x") == b"x"
        assert dict(text_choice_pairs("push_pics")).keys() == {"with", "text"}
        assert any(x[1] == "rec_keep_days" for x in SLIDERS) and any(x[1] == "push_pics" for x in TEXTS)
        d = tempfile.mkdtemp(prefix="mw-sx-")
        CFG["record_dir"] = d
        old = now - 10 * 86400

        def mk(stem, t, fav=False):
            for ext in (".mp4", ".jpg"):
                with open(os.path.join(d, stem + ext), "wb") as f:
                    f.write(b"x")
                os.utime(os.path.join(d, stem + ext), (t, t))
            with open(os.path.join(d, stem + ".json"), "w") as f:
                json.dump({"fav": fav}, f)
            os.utime(os.path.join(d, stem + ".json"), (t, t))
        mk("person_a", old); mk("person_b", old, True); mk("person_c", now)
        with open(os.path.join(d, "notes.cfg"), "w") as f:
            f.write("keep")
        assert sx_rec_prune(0, now) == 0
        assert sx_rec_prune(7, now) == 1 and not os.path.exists(os.path.join(d, "person_a.mp4")), "old one gone"
        assert os.path.exists(os.path.join(d, "person_b.mp4")) and os.path.exists(os.path.join(d, "person_c.jpg")), "favourite and new one stay"
        os.makedirs(os.path.join(d, "loop", "2026-10-29")); open(os.path.join(d, "loop", "2026-10-29", "a.mp4"), "w").close()
        assert sx_rec_wipe(False, "test") == (1, 1) and os.path.exists(os.path.join(d, "person_b.mp4"))
        assert not os.path.exists(os.path.join(d, "loop", "2026-10-29")), "continuous recording deleted too"
        assert sx_rec_wipe(True, "test") == (1, 0) and os.path.exists(os.path.join(d, "notes.cfg")), "only recordings are deleted"
        shutil.rmtree(d, ignore_errors=True)
        CFG.update(protect_pin="", web_pw_hash="", web_password="")
        assert sx_off_mode() == "none" and not sx_off_check("1234")[0]
        CFG["protect_pin"] = _pin_hash("4711"); PROTECT["pin_fails"] = []
        assert sx_off_mode() == "pin" and sx_off_check("4711")[0] and not sx_off_check("0000")[0] and not sx_off_check("")[0]
        PROTECT["pin_fails"] = [time.time()] * 5
        assert sx_off_check("4711")[1].startswith("too many"), "locked after 5 wrong PINs"
        assert "pin" in sx_off_form("de") and "inputmode" in sx_off_form("fr")
        CFG["protect_pin"] = ""; assert "Schutz-PIN" in sx_off_form("de")
        js = sx_ui_js_text()
        assert "Rotlicht-Ansicht" in js and "Dunkle Ansicht" not in js and "Nachtblick" not in js and "/*TX*/" not in js
        assert "sxnight" in render_page("<html><head></head><body><header></header></body></html>", "live")
        for k, (_i, h, t_) in SX_ERRS.items():
            assert tr(h, "de") != h and tr(t_, "fr") != t_, "error page text not translated: " + h
    finally:
        CFG.update(keep); PROTECT["pin_fails"] = fails
    return True
