#@ MoveEye – Teil 639y: Ruhebild – ein ruhiges Platzhalterbild statt Schwarz / «NO CAMERA FOUND», solange der Simulator startet, sich aktualisiert, eine Szene lädt oder nicht erreichbar ist (Web, Pi-Fenster, MJPEG / JPEG). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (01.11.2026): nach dem Aktualisieren war das Live-Bild schwarz, weil der Simulator gerade sein Update lud und
# neu startete (Chip «SIMULATION · PC 1 % · ⟳ Update 3.25.0»). Jetzt:
#   * simwait_reason(): warum gerade keine Bilder vom Simulator kommen - «update» (Simulator meldet busy.what = update, oder
#     MoveEye hat das Update angestossen / kennt eine neuere Version und die Verbindung ist eben abgerissen), «scene» (Szene /
#     Ort lädt: busy.what = scene, oder MoveEye hat eben eine Szene gewählt), «start» (antwortet, aber noch kein Bild), sonst
#     «connect». Nur wenn die Bildquelle der Simulator ist (CFG sim_on + source sim:…); sonst None.
#   * calm_frame(): das gerenderte Bild (dunkler Verlauf, Bergsilhouette, Blinki ohne Kegel bzw. das Logo, Text je nach
#     Grund, Dauer seit Beginn, Fortschritt, nach 3 Min. der Hinweis «Dauert länger als üblich …»). Statisch (keine Bewegung
#     im Bild), nur die Sekunden zählen. 410 no_camera_frame nimmt es -> /video_feed, Gast-Links, Vorschau, Pi-Fenster.
#     Ohne Simulation: dieselbe ruhige Art, aber klar als Fehler (rot, «Keine Kamera gefunden»). Ohne PIL: das alte Bild.
#   * simwait_jpeg(): dasselbe als JPEG für /sim/view.jpg und /sim/view.mjpg (550: Vorführung, Trailer, Simulator-Fenster).
#   * Web (530): eine Ebene über dem Live-Bild (#simwait, Live und Vollbild) mit Blinki, das leicht atmet
#     (prefers-reduced-motion: still), Text aus /api/state «simwait», Links «Reiter Simulator» und «Anleitung».
#   * Simulator (main.gd busy_reply, update.gd busy): «busy» in der Antwort auf /state (schnittstelle.json).
# ----------------------------------------------------------------------------
SIMWAIT = {"why": None, "t0": 0.0, "busy": None, "busy_t": 0.0, "scene_t": 0.0, "vers": None, "vers_t": 0.0, "cache": {}}
SIMWAIT_LONG = 180.0                                       # after 3 minutes: «takes longer than usual»

_HX_RUHE = {
    "The simulator is being updated{v} … back in a moment": (
        "Der Simulator wird aktualisiert{v} … gleich wieder da", "Le simulateur se met à jour{v} … de retour dans un instant",
        "Il simulatore si sta aggiornando{v} … torna subito", "Il simulatur vegn actualisà{v} … immediat puspè qua"),
    "The simulator is starting …": ("Der Simulator startet …", "Le simulateur démarre …", "Il simulatore si avvia …",
                                    "Il simulatur starta …"),
    "Connecting to the simulator …": ("Verbinde mit dem Simulator …", "Connexion au simulateur …", "Connessione al simulatore …",
                                      "Colliaziun cun il simulatur …"),
    "The simulator is loading a scene …": ("Der Simulator lädt eine Szene …", "Le simulateur charge une scène …",
                                           "Il simulatore carica una scena …", "Il simulatur chargia ina scena …"),
    "for {t}": ("seit {t}", "depuis {t}", "da {t}", "dapi {t}"),
    "The picture comes back by itself.": ("Das Bild kommt von selbst zurück.", "L’image revient toute seule.",
                                          "L’immagine torna da sola.", "Il maletg turna da sez."),
    "This takes longer than usual – is the simulator running on the PC?": (
        "Dauert länger als üblich – läuft der Simulator am PC?",
        "Cela prend plus de temps que d’habitude – le simulateur tourne-t-il sur le PC ?",
        "Ci vuole più del solito – il simulatore è in esecuzione sul PC?",
        "Quai dura pli ditg che usità – funcziuna il simulatur sin il PC?"),
    "If its window closes at once: «Notfall-Start.bat» next to the .exe": (
        "Schliesst sich sein Fenster gleich wieder: «Notfall-Start.bat» neben der .exe",
        "Si sa fenêtre se ferme aussitôt : «Notfall-Start.bat» à côté du .exe",
        "Se la sua finestra si chiude subito: «Notfall-Start.bat» accanto al .exe",
        "Sche sia fanestra sa serra immediat: «Notfall-Start.bat» sper il .exe"),
    "Open the Simulator tab": ("Reiter Simulator öffnen", "Ouvrir l’onglet Simulateur", "Apri la scheda Simulatore",
                               "Avrir il register Simulatur"),
    "Help": ("Anleitung", "Aide", "Aiuto", "Agid"),
    "No camera found": ("Keine Kamera gefunden", "Aucune caméra trouvée", "Nessuna telecamera trovata", "Nagina camera chattada"),
    "Connecting to the camera …": ("Verbinde mit der Kamera …", "Connexion à la caméra …", "Connessione alla telecamera …",
                                   "Colliaziun cun la camera …"),
    "Check the camera and the cable or network – MoveEye keeps trying by itself.": (
        "Kamera und Kabel bzw. Netz prüfen – MoveEye versucht es selbst weiter.",
        "Vérifie la caméra et le câble ou le réseau – MoveEye réessaie tout seul.",
        "Controlla la telecamera e il cavo o la rete – MoveEye riprova da solo.",
        "Controllar la camera ed il cabel u la rait – MoveEye emprova vinavant sez."),
}
for _k, _v in _HX_RUHE.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_RUHE_TITLE = {"update": "The simulator is being updated{v} … back in a moment", "start": "The simulator is starting …",
               "connect": "Connecting to the simulator …", "scene": "The simulator is loading a scene …"}


# wraps: simvals_take
_simvals_take_639y = simvals_take


def simvals_take(rep):                                    # + 639y: «busy» of the simulator (update / scene / start)
    _simvals_take_639y(rep)
    try:
        b = rep.get("busy")
        b = b if isinstance(b, dict) and str(b.get("what") or "") in ("update", "scene", "start") else None
        SIMWAIT["busy"] = {"what": str(b["what"]), "ver": str(b.get("ver") or "")[:20],
                           "pct": max(0, min(100, int(b["pct"]))) if isinstance(b.get("pct"), (int, float)) else None} if b else None
        SIMWAIT["busy_t"] = time.time()
        if time.time() - SIMWAIT["vers_t"] > 20:              # the newest known version (no network here: 300 caches it)
            SIMWAIT["vers_t"] = time.time()
            v = sim_versions()
            SIMWAIT["vers"] = (bool(v.get("newer")), str(v.get("latest") or ""))
    except Exception:
        pass


# wraps: sim_control
_sim_control_639y = sim_control


def sim_control(d=None):                                   # + 639y: a scene / place chosen from MoveEye -> «loads a scene»
    if isinstance(d, dict) and (d.get("action") == "scenario" or (d.get("action") == "set" and str(d.get("id") or "") in ("scene", "ort", "place"))):
        SIMWAIT["scene_t"] = time.time()
    return _sim_control_639y(d)


def _simwait_picture_ok():
    w = WATCH_REF.get("w")
    if w is None or getattr(w, "cap", None) is None:
        return False
    if not str(STATE.get("source_id") or "").startswith("sim:"):
        return True                                        # another camera stands in (switch failed, 410): its picture is shown
    return sim_picture_ok()


def simwait_reason(now=None):
    """why no pictures come from the simulator right now: {"why": update|start|connect|scene, "ver", "pct", "s"} or None
    (no simulation, or its pictures arrive)."""
    now = time.time() if now is None else now
    if not CFG.get("sim_on") or not str(CFG.get("source") or "").startswith("sim:") or _simwait_picture_ok():
        SIMWAIT["why"] = None
        return None
    ok = bool(SIM.get("ok")) and now - float(SIM.get("t") or 0.0) < 5.0
    lost = now - float(SIM.get("t") or 0.0) if SIM.get("t") else 1e9      # seconds since the last answer
    b = SIMWAIT["busy"] if now - SIMWAIT["busy_t"] < 600 else None
    vers = SIMWAIT["vers"] or (False, "")
    upd_mw = any(now - float(t_) < 600 for t_ in SIM_AUTOUPD.values()) if "SIM_AUTOUPD" in globals() else False
    why, ver, pct = "connect", "", None
    if b and b["what"] == "update" and (ok or lost < 600):
        why, ver, pct = "update", b["ver"], (b["pct"] if ok else None)
    elif b and b["what"] == "scene" and (ok or lost < 120):
        why = "scene"
    elif now - SIMWAIT["scene_t"] < 90:
        why = "scene"
    elif not ok and lost < 600 and (upd_mw or vers[0]):
        why, ver = "update", vers[1]                       # older simulators say nothing: the update MoveEye knows of
    elif ok or (b and b["what"] == "start"):
        why = "start"                                      # it answers, but no picture yet
    if SIMWAIT["why"] is None:
        SIMWAIT["t0"] = now                                # the time counts from the first moment without a picture
    SIMWAIT["why"] = why
    return {"why": why, "ver": ver, "pct": pct, "s": int(max(0.0, now - SIMWAIT["t0"]))}


def _mmss(s):
    s = int(s)
    return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def simwait_texts(r, lang=None):
    """the texts of the calm picture (for the picture, the web layer and the window)"""
    L = norm_lang(lang) if lang else cur_lang()
    title = tr(_RUHE_TITLE[r["why"]], L).replace("{v}", f" ({r['ver']})" if r.get("ver") else "")
    sub = tr("for {t}", L).replace("{t}", _mmss(r["s"])) + (f" · {r['pct']} %" if r.get("pct") is not None else "") \
        + " · " + tr("The picture comes back by itself.", L)
    long_ = r["s"] >= SIMWAIT_LONG
    return {"title": title, "sub": sub, "hint": tr("This takes longer than usual – is the simulator running on the PC?", L) if long_ else "",
            "hint2": tr("If its window closes at once: «Notfall-Start.bat» next to the .exe", L) if long_ else "",
            "link": tr("Open the Simulator tab", L), "help": tr("Help", L)}


def simwait_info(lang=None):
    """for /api/state «simwait» (web layer over the live picture): None or reason + texts"""
    try:
        r = simwait_reason()
    except Exception:
        return None
    if r is None:
        return None
    return dict(r, **simwait_texts(r, lang))


# ---- the picture (numpy + PIL, the background is made once per size) ---------------------------------------------------
def _ruhe_bg(w, h, red=False, mood="normal"):
    key = ("bg", w, h, red, mood, bool(CFG.get("blinki_on", True)))
    c = SIMWAIT["cache"]
    if key in c:
        return c[key]
    y = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    top = np.array((32, 18, 11) if not red else (22, 14, 20), np.float32)          # BGR #0b1220
    bot = np.array((44, 30, 20) if not red else (26, 18, 30), np.float32)          # BGR #141e2c
    img = np.broadcast_to(top * (1 - y) + bot * y, (h, w, 3)).copy()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)                                 # a soft glow behind the figure
    g = np.exp(-(((xx - w * 0.5) / (w * 0.30)) ** 2 + ((yy - h * 0.36) / (h * 0.34)) ** 2))
    glow = np.array((60, 44, 30) if not red else (40, 30, 60), np.float32)
    img += g[..., None] * glow * 0.55
    xs = np.arange(w, dtype=np.float32) / w
    for base, amp, col, ph in ((0.70, 0.10, (54, 40, 29), 0.0), (0.80, 0.07, (40, 30, 22), 1.7)):   # two mountain ridges
        ridge = h * (base - amp * (0.55 * np.sin(xs * 6.1 + ph) + 0.30 * np.sin(xs * 13.7 + ph * 2.0) + 0.15 * np.sin(xs * 29.0 + ph)))
        m = yy >= ridge[None, :]
        img[m] = img[m] * 0.25 + np.array(col, np.float32) * 0.75
    rng = np.random.default_rng(7)                                                 # a few faint stars
    for _ in range(int(w * h / 9000)):
        sx, sy = int(rng.integers(0, w)), int(rng.integers(0, int(h * 0.55)))
        cv2.circle(img, (sx, sy), 1, (150, 140, 130), -1, cv2.LINE_AA)
    img = np.clip(img, 0, 255).astype(np.uint8)
    fig = None                                                                     # Blinki (without the fan) or the logo
    try:
        png = blinki_png(int(h * 0.22), mood, red=red) if CFG.get("blinki_on", True) else app_icon_png(int(h * 0.20))
        fig = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
    except Exception:
        fig = None
    if fig is not None:
        fh, fw = fig.shape[:2]
        x0, y0 = (w - fw) // 2, int(h * 0.36 - fh / 2)
        if 0 <= x0 and 0 <= y0 and x0 + fw <= w and y0 + fh <= h:
            roi = img[y0:y0 + fh, x0:x0 + fw].astype(np.float32)
            if fig.shape[2] == 4:
                a = fig[:, :, 3:4].astype(np.float32) / 255.0
                roi = roi * (1 - a) + fig[:, :, :3].astype(np.float32) * a
            else:
                roi = fig[:, :, :3].astype(np.float32)
            img[y0:y0 + fh, x0:x0 + fw] = roi.astype(np.uint8)
    for k_ in [k_ for k_ in c if k_[0] == "bg"][8:]:
        c.pop(k_, None)
    c[key] = img
    return img


def _ruhe_draw(w, h, lines, red=False, mood="normal"):
    """lines: [(text, size, colour RGB, bold)] from the middle down. None without PIL."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    key = ("draw", w, h, red, mood, tuple(lines))               # the same texts (within one second): the same picture
    c = SIMWAIT["cache"]
    if key in c:
        return c[key].copy()
    for k_ in [k_ for k_ in c if k_[0] == "draw"]:
        c.pop(k_, None)
    c[key] = out = _ruhe_draw_new(w, h, lines, red, mood, Image, ImageDraw)
    return out.copy()


def _ruhe_draw_new(w, h, lines, red, mood, Image, ImageDraw):
    im = Image.fromarray(cv2.cvtColor(_ruhe_bg(w, h, red, mood), cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(im)
    y = int(h * 0.56)
    for txt, size, col, bold in lines:
        if not txt:
            continue
        if txt == "<bar>":                                 # the progress (size = percent)
            bw = int(w * 0.36); x0 = (w - bw) // 2
            d.rounded_rectangle((x0, y + 2, x0 + bw, y + 8), radius=3, fill=(40, 52, 68))
            d.rounded_rectangle((x0, y + 2, x0 + max(6, int(bw * size / 100.0)), y + 8), radius=3, fill=(88, 150, 255))
            y += 20; continue
        fs = max(10, int(h * size))
        f = _font(fs, bold)
        while getattr(f, "size", None) and d.textlength(txt, font=f) > w * 0.92 and fs > 10:
            fs -= 1; f = _font(fs, bold)                   # (without DejaVu: the default font of PIL, it has no size)
        tw = d.textlength(txt, font=f)
        d.text(((w - tw) / 2, y), txt, font=f, fill=col)
        y += int(fs * 1.45)
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def _calm_lines_draw(r, w, h, lang=None):
    tx = simwait_texts(r, lang)
    lines = [(tx["title"], 0.052, (232, 238, 245), True)]
    if r.get("pct") is not None:
        lines.append(("<bar>", r["pct"], None, False))
    lines += [(tx["sub"], 0.033, (139, 155, 176), False), (tx["hint"], 0.032, (255, 176, 112), False),
              (tx["hint2"], 0.028, (200, 170, 140), False), ("MoveEye · " + tr("Simulation", lang), 0.026, (90, 104, 124), False)]
    return _ruhe_draw(w, h, lines)


def calm_frame(w=960, h=540, lang=None):
    """the picture while there is no camera picture: calm for the simulator, a clear (but friendly) error for a real
    camera; None without PIL (410 draws the old picture then)"""
    r = simwait_reason()
    if r is not None:
        return _calm_lines_draw(r, w, h, lang)
    # a real camera: the same calm look, but clearly an error (red title); the old cv2 picture without PIL
    busy = str(STATE.get("source_status") or "").startswith(("connecting", "connection lost"))
    lines = [(("⏳ " + tr("Connecting to the camera …", lang)) if busy else ("⚠ " + tr("No camera found", lang)), 0.052,
              (255, 196, 90) if busy else (255, 107, 107), True),
             (str(source_label(CFG["source"]))[:60], 0.034, (232, 238, 245), False),
             (str(STATE.get("source_status") or "")[:90], 0.028, (170, 180, 195), False),
             (tr("Check the camera and the cable or network – MoveEye keeps trying by itself.", lang), 0.028, (139, 155, 176), False),
             ("ls /dev/video*", 0.024, (90, 104, 124), False)]
    return _ruhe_draw(w, h, lines, mood="think")      # Blinki thinks: clearly not «all is well»


def simwait_jpeg(w=960, q=80):
    """the calm picture as JPEG for /sim/view.jpg and /sim/view.mjpg (550); None = no reason (show the error as before)"""
    if not CFG.get("sim_on"):
        return None
    try:
        w = max(320, min(1600, int(w or 960)))
    except (TypeError, ValueError):
        w = 960
    h = int(w * 9 / 16)
    r = simwait_reason_view()
    key = ("jpg", w, q, r["why"], r["ver"], r["pct"], r["s"], cur_lang())
    c = SIMWAIT["cache"]
    if key in c:
        return c[key]
    img = _calm_lines_draw(r, w, h)
    if img is None:
        return None
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, int(q)])
    if not ok:
        return None
    for k_ in [k_ for k_ in c if k_[0] == "jpg"]:
        c.pop(k_, None)
    c[key] = buf.tobytes()
    return c[key]


def simwait_reason_view():
    """/sim/view.*: the simulator window does not answer - its reason, also while the live picture (410) is still fine
    (then only from the busy note / the connection, the time counts from now)"""
    r = simwait_reason()
    if r is not None:
        return r
    now = time.time()
    ok = bool(SIM.get("ok")) and now - float(SIM.get("t") or 0.0) < 5.0
    b = SIMWAIT["busy"] if now - SIMWAIT["busy_t"] < 600 else None
    if b and b["what"] in ("update", "scene"):
        return {"why": b["what"], "ver": b["ver"] if b["what"] == "update" else "", "pct": b["pct"] if ok else None, "s": 0}
    return {"why": "start" if ok else "connect", "ver": "", "pct": None, "s": 0}


# ---- web: a layer over the live picture (Live and full screen; the small preview shows the picture of the server) -------
SIMWAIT_CSS = r"""
#simwait{position:absolute;inset:0;z-index:3;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;
 padding:14px 16px;text-align:center;color:#e8eef5;overflow:hidden;
 background:radial-gradient(ellipse 60% 55% at 50% 38%,rgba(42,64,96,.55),transparent 70%),linear-gradient(#0b1220,#141e2c)}
#simwait[hidden]{display:none}
#simwait .sw-mt{position:absolute;left:0;right:0;bottom:0;width:100%;height:42%;pointer-events:none}
#simwait .sw-mt path:first-child{fill:#1d2836}#simwait .sw-mt path:last-child{fill:#16202c}
#simwait .sw-fig{position:relative;width:min(84px,18%);line-height:0;animation:sw-breath 4.5s ease-in-out infinite}
#simwait .sw-fig svg{display:block;width:100%;height:auto;overflow:visible}
#simwait .bk-ft{fill:#e8590c}#simwait .bk-scl{fill:#fff}#simwait .bk-rim{fill:none;stroke:#e8590c;stroke-width:2.6}
#simwait .bk-iris{fill:#ff9f43}#simwait .bk-pupil{fill:#0a0e14}#simwait .bk-hl{fill:#fff}#simwait .bk-hap{display:none}
#simwait .bk-lid{fill:#e8590c;transform-box:fill-box;transform-origin:50% 0;transform:scaleY(0);animation:sw-blink 6s infinite}
#simwait .sw-t{position:relative;font-weight:600;font-size:clamp(15px,2.6vw,22px);max-width:34em}
#simwait .sw-s{position:relative;color:#8b9bb0;font-size:clamp(12px,1.7vw,15px)}
#simwait .sw-bar{position:relative;width:min(280px,60%);height:6px;border-radius:3px;background:#283444;overflow:hidden}
#simwait .sw-bar i{display:block;height:100%;background:#5896ff;transition:width .6s ease}
#simwait .sw-h{position:relative;color:#ffb070;font-size:clamp(12px,1.7vw,15px);max-width:36em}
#simwait .sw-h small{display:block;color:#c8aa8c;margin-top:2px}
#simwait .sw-l{position:relative;display:flex;gap:14px;flex-wrap:wrap;justify-content:center;font-size:13px}
#simwait .sw-l a{color:#8fb8ff}
@keyframes sw-breath{0%,100%{transform:scale(1);opacity:.92}50%{transform:scale(1.045);opacity:1}}
@keyframes sw-blink{0%,92%,100%{transform:scaleY(0)}95%,96.5%{transform:scaleY(1)}}
@media (prefers-reduced-motion:reduce){#simwait .sw-fig,#simwait .bk-lid{animation:none!important}#simwait .sw-bar i{transition:none}}
body.videoonly #simwait{border-radius:0}
.vwrap.vlost:has(#simwait:not([hidden]))::after,.vwrap.vlost:has(#simwait:not([hidden]))::before{display:none}
@media (max-width:520px){#simwait{gap:4px;padding:8px 12px}#simwait .sw-fig{width:min(54px,15%)}#simwait .sw-l{font-size:12px}#simwait.long .sw-fig{display:none}}
@media (max-height:260px){#simwait .sw-fig{display:none}}
"""

SIMWAIT_HTML = ('<div id="simwait" hidden role="status" aria-live="polite">'
                '<svg class="sw-mt" viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">'
                '<path d="M0 22 C10 14 18 18 26 12 C34 6 40 14 50 10 C60 6 68 16 78 11 C86 7 94 13 100 10 V40 H0Z"/>'
                '<path d="M0 30 C12 24 20 28 32 22 C44 17 52 26 64 21 C76 16 86 25 100 20 V40 H0Z"/></svg>'
                '<div class="sw-fig">' + BLINKI_SVG.replace("__I__", "sw") + '</div>'
                '<div class="sw-t"></div><div class="sw-bar" hidden><i></i></div><div class="sw-s"></div>'
                '<div class="sw-h" hidden></div><div class="sw-l"><a href="/sim" class="sw-a"></a><a href="/help#ruhebild" class="sw-b"></a></div></div>')

SIMWAIT_JS = r"""
(function () {
  const base = window.simPaint;
  if (typeof base !== "function") return;
  const q = s => document.querySelector(s);
  function paint(st) {
    const B = q("#simwait"); if (!B) return;
    const W = st && st.simwait;
    if (!W) { B.hidden = true; return; }
    B.hidden = false;
    q("#simwait .sw-t").textContent = W.title;
    q("#simwait .sw-s").textContent = W.sub;
    const bar = q("#simwait .sw-bar"); bar.hidden = W.pct == null; if (W.pct != null) bar.firstChild.style.width = W.pct + "%";
    B.classList.toggle("long", !!W.hint);
    const h = q("#simwait .sw-h"); h.hidden = !W.hint; h.textContent = W.hint || "";
    if (W.hint2) { const sm = document.createElement("small"); sm.textContent = W.hint2; h.appendChild(sm); }
    q("#simwait .sw-a").textContent = W.link; q("#simwait .sw-b").textContent = W.help;
  }
  window.simPaint = function (s) { base(s); try { paint(s); } catch (e) {} };
})();
"""

if '<img id="video" src="/video_feed" alt="">' in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace('<img id="video" src="/video_feed" alt="">', '<img id="video" src="/video_feed" alt="">' + SIMWAIT_HTML, 1)
    WEB_PAGE = WEB_PAGE.replace("</script></body></html>", "</script><style>" + SIMWAIT_CSS + "</style><script>" + SIMWAIT_JS + "</script></body></html>", 1)


def ruhebild_selftest():
    keep_cfg = {k: CFG.get(k) for k in ("sim_on", "source")}
    keep_sim = {k: SIM.get(k) for k in ("ok", "t")}
    keep_w = dict(SIMWAIT); keep_ref = WATCH_REF.get("w")
    try:
        WATCH_REF["w"] = None
        CFG["sim_on"] = False
        assert simwait_reason() is None, "a reason without the simulation"
        CFG.update(sim_on=True, source="sim:0")
        SIMWAIT.update(why=None, busy={"what": "update", "ver": "3.25.0", "pct": 40}, busy_t=time.time(), scene_t=0.0, vers=None)
        SIM.update(ok=False, t=time.time() - 20)
        r = simwait_reason()
        assert r and r["why"] == "update" and r["ver"] == "3.25.0", f"update not seen: {r}"
        tx = simwait_texts(r, "de")
        assert tx["title"] == "Der Simulator wird aktualisiert (3.25.0) … gleich wieder da" and not tx["hint"], tx
        SIMWAIT.update(busy=None, vers=(True, "3.26.0"))
        assert simwait_reason()["why"] == "update" and simwait_reason()["ver"] == "3.26.0", "the known newer version"
        SIMWAIT.update(vers=(False, ""), why=None)
        SIM.update(t=time.time() - 3600)
        r = simwait_reason()
        assert r["why"] == "connect", r
        SIMWAIT["t0"] = time.time() - 200
        tx = simwait_texts(simwait_reason(), "fr")
        assert tx["hint"].startswith("Cela prend") and "Notfall-Start.bat" in tx["hint2"], "the hint after 3 minutes"
        SIM.update(ok=True, t=time.time())
        assert simwait_reason()["why"] == "start", "answers, but no picture"
        SIMWAIT["scene_t"] = time.time()
        assert simwait_reason()["why"] == "scene", "scene"
        for L in ("de", "fr", "it", "rm", "en"):
            for k in list(_RUHE_TITLE.values()) + ["for {t}", "No camera found"]:
                assert tr(k, L), (k, L)
        try:
            import PIL  # noqa: F401
            img = calm_frame(640, 360)
            assert img is not None and img.shape == (360, 640, 3) and 8 < float(img.mean()) < 120, "calm picture"
            j = simwait_jpeg(640)
            assert j and j[:2] == b"\xff\xd8", "calm JPEG"
            CFG["sim_on"] = False
            img = calm_frame(640, 360)
            assert img is not None and img.shape == (360, 640, 3), "error picture of a real camera"
        except ImportError:
            pass
        assert HELP_PAGE.count('id="ruhebild"') == 2, "the manual (DE + EN)"
        assert 'id="simwait"' in WEB_PAGE and "window.simPaint = function" in WEB_PAGE, "web layer missing"
    finally:
        CFG.update(keep_cfg); SIM.update(keep_sim); SIMWAIT.clear(); SIMWAIT.update(keep_w); WATCH_REF["w"] = keep_ref


# the manual (HELP_PAGE of 540, «Probleme lösen» / «Troubleshooting»): what the calm picture means - the link of the hint
for _a, _b in (('<section id="faq" data-icon="🛠"><h2>Probleme lösen</h2>',
                '<p id="ruhebild"><b>🏔 Ruhiges Bild statt Live-Bild (Simulator):</b> Startet der Simulator, aktualisiert er sich, lädt er '
                'eine Szene oder ist er nicht erreichbar, zeigt MoveEye ein ruhiges Bild mit Blinki und dem Grund (z. B. «Der Simulator '
                'wird aktualisiert (3.29.0) … gleich wieder da»). Das Live-Bild kommt von selbst zurück. Dauert es länger als 3 Minuten: '
                'am PC nachsehen, ob der Simulator läuft (Fenster «MoveEye Sim»); schliesst sich sein Fenster gleich wieder, '
                '«Notfall-Start.bat» neben der .exe starten. Im Reiter Simulator stehen Adresse und Verbindung. Bei einer echten Kamera '
                'erscheint stattdessen die Fehlermeldung «Keine Kamera gefunden»: Kamera, Kabel bzw. Netz prüfen.</p>'),
               ('<section id="faq" data-icon="🛠"><h2>Troubleshooting</h2>',
                '<p id="ruhebild"><b>🏔 A calm picture instead of the live picture (simulator):</b> while the simulator starts, updates, '
                'loads a scene or cannot be reached, MoveEye shows a calm picture with Blinki and the reason (e.g. «The simulator is '
                'being updated (3.29.0) … back in a moment»). The live picture comes back by itself. If it takes longer than 3 minutes: '
                'check on the PC that the simulator is running (window «MoveEye Sim»); if its window closes at once, start '
                '«Notfall-Start.bat» next to the .exe. The Simulator tab shows its address and the connection. With a real camera the '
                'error «No camera found» appears instead: check the camera and the cable or network.</p>')):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)


SELFTEST_EXTRA.append(("Calm picture while the simulator starts / updates / is not reachable (639y)", ruhebild_selftest))
