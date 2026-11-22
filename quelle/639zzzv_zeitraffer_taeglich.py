#@ MoveEye – Teil 639zzzv: Zeitraffer – jeden Tag automatisch ein Video (kurz nach Mitternacht aus den Fotos von gestern, verpasste Tage nachholen). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (14.11.2026): der Zeitraffer (Teil 220) macht jeden Tag von selbst ein Video, nicht nur auf Knopfdruck.
#   * Schalter «Jeden Tag automatisch ein Video» (timelapse_daily) unter Einstellungen → Zeitraffer, ab Werk an; nach dem
#     Update einmal auf allen Geräten an (tld_migrate) mit einem Hinweis in «Neu in dieser Version» (Web und Fenster).
#   * Nacht-Fenster 00:20 bis 06:00 Ortszeit: gestern zuerst, dann verpasste Tage (höchstens die letzten 7, z. B. nach einer
#     Pause des Geräts), ein Video pro Minute. Ein Tag braucht mindestens 2 Fotos; hat er schon ein Video (auch ein von Hand
#     gemachtes tlv_JJJJMMTT_*.mp4), bleibt er, wie er ist. Name: tlv_JJJJMMTT_auto.mp4 (passt zu TL_VIDEO_RE, die Liste der
#     Zeitraffer-Seite zeigt es mit «automatisch»).
#   * ffmpeg mit nice 19 / ionice idle, direkt aus den Fotos (Muster tl_JJJJMMTT_*.jpg) - die Kamera-Schleife merkt nichts.
#     Nie während Alarm, Aufnahme, Folgen (gleiche Regel wie das Zeitraffer-Foto, Wrapper um Timelapse.update) - wartet und
#     versucht es jede Minute wieder bis 06:00; beginnt ein Alarm mitten im Video, wird ffmpeg abgebrochen und später neu
#     gemacht. Akku schwach (Akku-Sparen, Teil 105 batt_save_active) = diese Nacht nichts, nächste Nacht nachholen.
#   * Grenze sicher: vorher eine Schätzung, die nie zu gross ist (1 KiB + 16 Bytes pro Foto - weniger Platz = ohne ffmpeg
#     übersprungen), danach zählt die echte Grösse der fertigen Datei (darüber = gelöscht, übersprungen).
#   * Die Fotos bleiben; ist der Schalter an, räumt tl_cleanup (220) die Fotos schon bei 90 % von timelapse_max_gb auf
#     (älteste zuerst, Videos nie) - Platz für die Videos. Wäre der Zeitraffer-Ordner mit dem Video grösser als
#     timelapse_max_gb, kommt das Video nicht dazu (eine Zeile im Protokoll, der Tag in tld_skip, kein neuer Versuch); ebenso
#     ein Tag, an dem ffmpeg scheitert.
# Test: werkzeuge/zeitraffer_taeglich_test.py (falsche Uhr, falsche Fotos, echtes ffmpeg falls da).
# ----------------------------------------------------------------------------
for _k, _v in {"timelapse_daily": True, "tld_mig": True, "tld_note": "", "tld_seen": [], "tld_skip": []}.items():
    CFG.setdefault(_k, _v)
    DEFAULTS.setdefault(_k, _v)
TLD = {"loop": False, "alarm_t": 0.0, "night": "", "waitlog": ""}
TLD_FROM = (0, 20)                   # from 00:20 local time ...
TLD_TO_H = 6                         # ... until 06:00
TLD_DAYS = 7                         # missed days: at most the last 7
TLD_NOTE = ("New: the timelapse makes one video per day by itself - shortly after midnight from the photos of yesterday, quietly "
            "in the background, never during an alarm. Now on for all devices, yours too. The photos stay. "
            "Switch off: Settings → Timelapse → «Every day a video automatically».")
_tl_ti = next((i for i, t_ in enumerate(TOGGLES) if t_[1] == "timelapse_return"), len(TOGGLES) - 1)
TOGGLES.insert(_tl_ti + 1, (TOGGLES[_tl_ti][0] if TOGGLES[_tl_ti][1] == "timelapse_return" else "Timelapse", "timelapse_daily",
                            "Every day a video automatically"))


def tld_now():
    return datetime.now()                                 # the test replaces it (fake clock)


def tld_busy():
    """alarm, recording or tracking now (or the last alarm picture less than 2 minutes ago): no video now"""
    w = WATCH_REF.get("w")
    if STATE.get("recording") or STATE.get("persons") or STATE.get("tracking"):
        return True
    if w is not None and getattr(w, "writer", None) is not None:
        return True
    return time.time() - TLD["alarm_t"] < 120.0


def tld_has_video(day):
    try:
        return any(TL_VIDEO_RE.match(n) and (n == f"tlv_{day}.mp4" or n.startswith(f"tlv_{day}_")) for n in os.listdir(tl_dir()))
    except OSError:
        return False


def tld_days(now):
    """the days that still need a video: yesterday first, at most TLD_DAYS back, at least 2 photos"""
    out = []
    for i in range(1, TLD_DAYS + 1):
        d = (now - timedelta(days=i)).strftime("%Y%m%d")
        if d not in (CFG.get("tld_skip") or []) and not tld_has_video(d) and len(tl_photos(d)) >= 2:
            out.append(d)
    return out


def tld_folder_bytes():
    n = 0
    try:
        for f in os.listdir(tl_dir()):
            if TL_PHOTO_RE.match(f) or TL_VIDEO_RE.match(f):
                n += os.path.getsize(os.path.join(tl_dir(), f))
    except OSError:
        pass
    return n


def _tld_skip(day, msg):
    CFG["tld_skip"] = ([d for d in (CFG.get("tld_skip") or []) if d != day] + [day])[-30:]
    save_settings()
    log_event("servo", msg)
    return "skipped"


def tld_render(day):
    """one day -> tlv_<day>_auto.mp4 with ffmpeg (nice / ionice); stopped when an alarm starts. Returns what happened."""
    d = tl_dir(); files = tl_photos(day)
    limit = float(CFG["timelapse_max_gb"]) * 1024 ** 3
    if tld_folder_bytes() >= limit:
        return _tld_skip(day, f"Daily timelapse video {day} skipped: the timelapse folder is full (max. {CFG['timelapse_max_gb']:g} GB)")
    if tld_folder_bytes() + 1024 + 16 * len(files) > limit:   # less than the smallest possible MP4 (header + a little per photo) left
        return _tld_skip(day, f"Daily timelapse video {day} skipped: it would exceed the max. timelapse folder ({CFG['timelapse_max_gb']:g} GB)")
    ff = shutil.which("ffmpeg")
    if not ff:
        log_event("servo", "Daily timelapse video: ffmpeg missing (sudo apt install ffmpeg) - next night again")
        return "no ffmpeg"
    first = cv2.imread(os.path.join(d, files[0]))
    if first is None:
        return _tld_skip(day, f"Daily timelapse video {day} failed: first photo unreadable")
    h, w = first.shape[:2]
    fps = max(5.0, min(60.0, float(CFG["timelapse_fps"])))
    name = f"tlv_{day}_auto.mp4"; part = os.path.join(d, f".tlv_{day}_auto.part.mp4")
    cmd = [ff, "-y", "-nostdin", "-loglevel", "error", "-framerate", f"{fps:.2f}", "-pattern_type", "glob", "-i", f"tl_{day}_*.jpg",
           "-an", "-vf", f"scale={w // 2 * 2}:{h // 2 * 2},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
           "-threads", "2", "-movflags", "+faststart", "-progress", "pipe:1", "-f", "mp4", part]
    if shutil.which("ionice"):
        cmd = ["ionice", "-c3"] + cmd
    if shutil.which("nice"):
        cmd = ["nice", "-n", "19"] + cmd
    out = []
    STATE["timelapse_render"] = f"making video 0/{len(files)}"
    p = subprocess.Popen(cmd, cwd=d, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True)

    def pump():
        for ln in p.stdout:
            ln = ln.strip()
            if ln.startswith("frame="):
                STATE["timelapse_render"] = f"making video {min(len(files), int(ln[6:] or 0))}/{len(files)}"
            elif ln and "=" not in ln:
                out.append(ln)
    th = threading.Thread(target=pump, daemon=True); th.start()
    t0 = time.time(); why = ""
    while True:
        if tld_busy():
            why = "alarm"
        elif time.time() - t0 > 3 * 3600:
            why = "too long"
        if why or p.poll() is not None:
            break
        time.sleep(0.25)
    if why:
        p.kill()
    p.wait(); th.join(5)
    if why or p.returncode != 0 or not os.path.isfile(part):
        try:
            os.remove(part)
        except OSError:
            pass
        if why == "alarm":
            STATE["timelapse_render"] = "waiting: alarm has priority"
            return "busy"
        STATE["timelapse_render"] = "error: " + (out[-1] if out else why or f"ffmpeg {p.returncode}")[:100]
        return _tld_skip(day, f"Daily timelapse video {day} failed: " + (out[-1] if out else why or f"ffmpeg {p.returncode}")[:120])
    if tld_folder_bytes() + os.path.getsize(part) > limit:
        os.remove(part)
        STATE["timelapse_render"] = ""
        return _tld_skip(day, f"Daily timelapse video {day} skipped: it would exceed the max. timelapse folder ({CFG['timelapse_max_gb']:g} GB)")
    os.replace(part, os.path.join(d, name))
    STATE["timelapse_render"] = "video ready: " + name
    log_event("servo", f"Daily timelapse video made: {name} ({len(files)} photos, {fps:.0f} fps)")
    return "made " + name


def tld_tick(now=None):
    """one step of the night job (the loop calls it every minute). Returns what it did."""
    now = now or tld_now()
    night = now.strftime("%Y%m%d")
    if not CFG.get("timelapse_daily"):
        return "off"
    if (now.hour, now.minute) < TLD_FROM or now.hour >= TLD_TO_H:
        return "not now"
    if TLD["night"] == night:
        return "done tonight"
    days = tld_days(now)
    if not days:
        TLD["night"] = night
        return "nothing to do"
    if batt_save_active():
        TLD["night"] = night
        log_event("servo", f"Daily timelapse video: battery low - next night ({len(days)} day(s) waiting)")
        return "battery low"
    if tld_busy():
        if TLD["waitlog"] != night:
            TLD["waitlog"] = night
            log_event("servo", "Daily timelapse video waits: alarm has priority")
        return "busy"
    if not _TL_RENDER_LOCK.acquire(blocking=False):
        return "busy"                                     # a video by hand is being made right now
    try:
        return tld_render(days[0])
    finally:
        _TL_RENDER_LOCK.release()


def tld_loop():
    time.sleep(30)
    while True:
        try:
            tld_tick()
        except Exception as e:
            TLD["night"] = tld_now().strftime("%Y%m%d")       # not every minute the same error
            log_event("servo", f"Daily timelapse video: {e}"[:160])
        time.sleep(60)


_tl_update_639zzzv = Timelapse.update


def _tld_tl_update(self, frame, alarm):                  # + 639zzzv: the alarm rule of the photo; the night job starts with the camera loop
    if alarm:
        TLD["alarm_t"] = time.time()
    if not TLD["loop"]:
        TLD["loop"] = True
        threading.Thread(target=tld_loop, daemon=True, name="tldaily").start()
    return _tl_update_639zzzv(self, frame, alarm)


# wraps: Timelapse.update
Timelapse.update = _tld_tl_update


def tld_migrate(cfg_in):
    """once per settings file (Besitzer 14.11.2026): the daily video on for existing devices too, with a one-time notice"""
    if not isinstance(cfg_in, dict) or cfg_in.get("tld_mig"):
        return []
    CFG["tld_mig"] = True; CFG["tld_note"] = "pending"; CFG["tld_seen"] = []
    CFG["timelapse_daily"] = True
    return ["timelapse: one video per day switched on"]


_news_state_639zzzv = news_state
_news_seen_639zzzv = news_seen


# wraps: news_state
def news_state(who="web", lang=None):                     # + 639zzzv: the one-time notice of the daily video
    st = _news_state_639zzzv(who, lang)
    if CFG.get("tld_note") == "pending" and who not in (CFG.get("tld_seen") or []):
        it = {"v": APP_VERSION, "t": "⏱ " + tr(TLD_NOTE, lang), "href": "/settings?setting=timelapse_daily"}
        st = dict(st, items=[it] + list(st.get("items") or []), show=True)
    return st


# wraps: news_seen
def news_seen(who="web"):                                 # + 639zzzv
    if CFG.get("tld_note") == "pending":
        CFG["tld_seen"] = sorted(set(CFG.get("tld_seen") or []) | {who})
    return _news_seen_639zzzv(who)


# ---- translations (English key: Deutsch, Français, Italiano, Rumantsch) ----------------------------------------------------
_HX_TLD = {
    "Every day a video automatically": (
        "Jeden Tag automatisch ein Video", "Chaque jour une vidéo automatiquement", "Ogni giorno un video automaticamente",
        "Mintga di automaticamain in video"),
    TLD_NOTE: (
        "Neu: Der Zeitraffer macht jeden Tag von selbst ein Video – kurz nach Mitternacht aus den Fotos von gestern, leise im "
        "Hintergrund, nie während eines Alarms. Ab jetzt auf allen Geräten an, auch auf deinem. Die Fotos bleiben. "
        "Abschalten: Einstellungen → Zeitraffer → «Jeden Tag automatisch ein Video».",
        "Nouveau : le timelapse fait tout seul une vidéo par jour – peu après minuit avec les photos d’hier, discrètement en "
        "arrière-plan, jamais pendant une alarme. Désormais activé sur tous les appareils, le tien aussi. Les photos restent. "
        "Désactiver : Réglages → Timelapse → «Chaque jour une vidéo automatiquement».",
        "Novità: il timelapse fa da solo un video al giorno – poco dopo mezzanotte con le foto di ieri, in silenzio in "
        "sottofondo, mai durante un allarme. Ora attivo su tutti i dispositivi, anche sul tuo. Le foto restano. "
        "Disattivare: Impostazioni → Timelapse → «Ogni giorno un video automaticamente».",
        "Nov: Il timelapse fa mintga di sez in video – curt suenter mesanotg cun las fotos dad ier, quietamain en il "
        "fund, mai durant in alarm. Ussa activ sin tut ils apparats, er sin il tes. Las fotos restan. "
        "Deactivar: Parameters → Timelapse → «Mintga di automaticamain in video»."),
}
for _k, _v in _HX_TLD.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

# ---- manual: one sentence in the timelapse paragraph (5 languages) ---------------------------------------------------------
for _L, _a, _b in (
        ("de", "Ein Alarm hat immer Vorrang. Die Zeitraffer-Videos",
         "Ein Alarm hat immer Vorrang. <b>Jeden Tag automatisch ein Video</b> (ab Werk an): kurz nach Mitternacht macht MoveEye "
         "aus den Fotos von gestern ein Video (in der Liste mit «automatisch») – leise im Hintergrund, nie während eines Alarms, "
         "bei schwachem Akku in der nächsten Nacht; verpasste Tage (höchstens 7) holt es nach. Die Fotos bleiben. Die Zeitraffer-Videos"),
        ("en", "An alarm always has priority. Timelapse videos",
         "An alarm always has priority. <b>Every day a video automatically</b> (on from the factory): shortly after midnight MoveEye "
         "makes a video from the photos of yesterday (marked «automatic» in the list) – quietly in the background, never during an "
         "alarm, with a low battery the next night; missed days (at most 7) are made later. The photos stay. Timelapse videos"),
        ("fr", "Une alarme a toujours la priorité. Les vidéos timelapse",
         "Une alarme a toujours la priorité. <b>Chaque jour une vidéo automatiquement</b> (activé d’usine) : peu après minuit, "
         "MoveEye fait une vidéo avec les photos d’hier (marquée «automatique» dans la liste) – discrètement en arrière-plan, jamais "
         "pendant une alarme, avec une batterie faible la nuit suivante ; les jours manqués (7 au plus) sont rattrapés. Les photos "
         "restent. Les vidéos timelapse"),
        ("it", "Un allarme ha sempre la precedenza. I video timelapse",
         "Un allarme ha sempre la precedenza. <b>Ogni giorno un video automaticamente</b> (attivo di fabbrica): poco dopo mezzanotte "
         "MoveEye fa un video con le foto di ieri (segnato «automatico» nella lista) – in silenzio in sottofondo, mai durante un "
         "allarme, con la batteria scarica la notte seguente; i giorni persi (al massimo 7) vengono recuperati. Le foto restano. "
         "I video timelapse"),
        ("rm", "In alarm ha adina la precedenza. Ils videos da timelapse",
         "In alarm ha adina la precedenza. <b>Mintga di automaticamain in video</b> (activ da fabrica): curt suenter mesanotg fa "
         "MoveEye in video cun las fotos dad ier (marcà «automatic» en la glista) – quietamain en il fund, mai durant in alarm, cun "
         "in accu flaivel la proxima notg; ils dis manchentads (al pli 7) vegnan recuperads. Las fotos restan. Ils videos da timelapse")):
    if _L in ("de", "en"):
        HELP_PAGE = HELP_PAGE.replace(_a, _b, 1)
    elif _L in HELP_X:
        HELP_X[_L] = HELP_X[_L].replace(_a, _b, 1)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def tld_selftest():
    keep = ({k: CFG.get(k) for k in ("timelapse_daily", "tld_mig", "tld_note", "tld_seen", "tld_skip", "record_dir")}, dict(TLD),
            dict(STATE), globals()["save_settings"], globals()["log_event"], BATT_SAVE["on"], globals()["tld_render"])
    tmp = tempfile.mkdtemp(prefix="mw_tld_"); logs = []; made = []
    try:
        globals()["save_settings"] = lambda *a, **k: None
        globals()["log_event"] = lambda kind, msg, *a, **k: logs.append(msg)
        globals()["tld_render"] = lambda day: made.append(day) or "made"
        CFG.update(record_dir=tmp, timelapse_daily=True, tld_skip=[]); TLD.update(night="", waitlog="", alarm_t=0.0)
        STATE.update(recording=False, persons=0, tracking=False); BATT_SAVE["on"] = False
        os.makedirs(tl_dir())
        for day in ("20261113", "20261112", "20261105", "20261104"):
            for s in ("100000", "110000"):
                open(os.path.join(tl_dir(), f"tl_{day}_{s}.jpg"), "wb").close()
        open(os.path.join(tl_dir(), "tl_20261111_100000.jpg"), "wb").close()                  # one photo: no video
        open(os.path.join(tl_dir(), "tlv_20261112_101010.mp4"), "wb").close()                 # made by hand: stays
        n = datetime(2026, 11, 14, 0, 25)
        assert tld_days(n) == ["20261113"], tld_days(n)          # 12 has a video, 11 one photo, 05 / 04 more than 7 days back
        assert tld_tick(datetime(2026, 11, 14, 0, 10)) == "not now" and tld_tick(datetime(2026, 11, 14, 6, 0)) == "not now"
        STATE["persons"] = 1
        assert tld_tick(n) == "busy" and not made and len(logs) == 1
        STATE["persons"] = 0
        assert tld_tick(n) == "made" and made == ["20261113"]
        TLD["night"] = n.strftime("%Y%m%d")
        assert tld_tick(n) == "done tonight"
        TLD["night"] = ""; BATT_SAVE["on"] = True
        assert tld_tick(n) == "battery low" and made == ["20261113"]
        BATT_SAVE["on"] = False; TLD["night"] = ""
        assert tld_days(datetime(2026, 11, 12, 1, 0)) == ["20261105"], "catch-up: 7 days back"
        CFG["timelapse_daily"] = False
        assert tld_tick(n) == "off"
        CFG.update(tld_mig=False, tld_note="", timelapse_daily=False)
        assert tld_migrate({"timelapse_daily": False, "tld_mig": True}) == [] and not CFG["timelapse_daily"], "migrated once only"
        assert tld_migrate({"timelapse_on": True}) and CFG["timelapse_daily"] and CFG["tld_note"] == "pending"
        assert any("⏱" in it.get("t", "") for it in news_state("web", "de").get("items") or [])
        assert any(t_[1] == "timelapse_daily" for t_ in TOGGLES)
        for k, v in _HX_TLD.items():
            assert len(v) == 4 and all(v) and "ß" not in "".join(v) and all(k in TRX[L] for L in ("fr", "it", "rm")), k
        assert "Jeden Tag automatisch ein Video" in HELP_PAGE and "Every day a video automatically" in HELP_PAGE
        return "night window, busy waits, yesterday once, battery low, catch-up 7 days, off, migration once, notice, texts"
    finally:
        CFG.update(keep[0]); TLD.clear(); TLD.update(keep[1]); STATE.clear(); STATE.update(keep[2])
        globals()["save_settings"] = keep[3]; globals()["log_event"] = keep[4]; BATT_SAVE["on"] = keep[5]
        globals()["tld_render"] = keep[6]
        shutil.rmtree(tmp, ignore_errors=True)


SELFTEST_EXTRA.append(("Timelapse: every day a video automatically (639zzzv)", tld_selftest))


# 4.17.1: the hint of the history page when «Timelapse → Videos» has no video yet (the page itself has the German text)
_HX_VTL = {"No timelapse video yet – one is made every night at about 00:20 from yesterday's photos (Settings → Timelapse)":
               ("Noch kein Zeitraffer-Video – entsteht jede Nacht um ca. 00:20 aus den Fotos von gestern (Einstellungen → Zeitraffer)",
                "Pas encore de vidéo accélérée – elle est créée chaque nuit vers 00:20 à partir des photos d’hier (Réglages → Accéléré)",
                "Ancora nessun video timelapse – viene creato ogni notte verso le 00:20 dalle foto di ieri (Impostazioni → Timelapse)",
                "Anc nagin video accelerà – el vegn fatg mintga notg enturn las 00:20 ord las fotos dad ier (Parameters → Accelerà)"),
           "back to {d}": ("bis {d}", "jusqu’au {d}", "fino al {d}", "fin ils {d}"),     # 4.18.1: chip in the history (oldest kept recording)
           "Oldest kept recording – when the folder is full, the oldest are deleted first (time-lapse and continuous recording have their own limits)":
               ("Älteste noch vorhandene Aufnahme – ist der Ordner voll, werden die ältesten zuerst gelöscht (Zeitraffer und Daueraufnahme haben eigene Grenzen)",
                "Plus ancien enregistrement conservé – quand le dossier est plein, les plus anciens sont effacés en premier (l’accéléré et l’enregistrement continu ont leurs propres limites)",
                "Registrazione più vecchia conservata – quando la cartella è piena, le più vecchie vengono cancellate per prime (timelapse e registrazione continua hanno limiti propri)",
                "La pli veglia registraziun anc avant maun – sch'il ordinatur è plain, vegnan las pli veglias stizzadas l'emprim (accelerà e registraziun permanenta han atgnas limitas)")}
for _k, _v in _HX_VTL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
