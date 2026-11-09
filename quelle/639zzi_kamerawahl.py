#@ MoveEye – Teil 639zzi: «Kamerawahl» – auf echter Hardware kleine Bilder (Kacheln) aller Videoquellen auf dem Live-Bild (Kopf, Weitwinkel, Wärmebild, USB-, Pi- und Netzwerk-Kameras); antippen = diese Kamera gross, NUR die Anzeige (Erkennung und Einstellungen bleiben); fehlt Kopf / Weitwinkel / Wärmebild, eine graue Kachel «nicht angeschlossen» mit Hinweis; mehr als Platz hat: «⋯ Kameras». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (09.11.2026, «Kamerawahl im Live-Bild»): im Simulator-Betrieb zeigt die Live-Seite kleine Bilder
# (Weitwinkel oben links, Simulator unten rechts), am echten Pi nur «Pi camera 0». Entscheid (bestätigt):
#   * Am echten Gerät (nicht im Simulator-Betrieb) eine Reihe kleiner Bilder oben links im Live-Bild, im gleichen Aussehen wie
#     das kleine Übersichtsbild von 639zv (#v3-mini, das bleibt die erste Kachel: Kopf ⇄ Weitwinkel). Je eine Kachel für jede
#     Videoquelle: 🎯 Kopf (Hauptkamera), 🔭 Weitwinkel, 🌡 Wärmebild, jede Zusatzkamera (440), weitere Pi-Kameras, USB-Kameras
#     (ohne sie zu öffnen gefunden: /sys/class/video4linux, Knoten «index 0», ohne die internen Knoten des Pi) und die
#     Netzwerk-Kameras aus den Einstellungen (ip_sources).
#   * Antippen = diese Kamera im grossen Bild. NUR die Anzeige: keine Einstellung ändert, die Erkennung behält ihre Quelle
#     (kein /api/set, kein request_source, kein thermal_on - das Wärmebild gross ist das reine Wärmebild, nicht die Überlagerung).
#     Gemerkt pro Gerät (localStorage «mw-kamwahl», WEB_UI_LOCAL). Der Knopf «Ansicht» und das Menü von 639zv bleiben, wie sie sind.
#   * Höchstens 3 Kacheln nebeneinander (Handy; ab 600 px Bildbreite 4, ab 900 px 5), die angeschlossenen zuerst; gibt es mehr,
#     wird die letzte zu «⋯ Kameras +n» = kleines Menü mit allen Quellen (wie das Menü «Ansicht»).
#   * Kopf / Weitwinkel / Wärmebild nicht angeschlossen: graue Kachel «nicht angeschlossen», nicht wählbar; antippen = kurzer
#     Hinweis, wo man sie einrichtet (Einstellungen → Kameras & Kopf).
#   * Im Simulator-Betrieb kommt nichts davon (Liste leer): dort bleibt alles wie bisher (639zt / 549 / 639zv).
#   * Rechte: wie das Live-Bild (Recht «live», 040 PERM_GET); ohne dieses Recht keine Kacheln.
# Schonung des Pi (CPU):
#   * Kacheln holen Einzelbilder /cam_thumb/<quelle> (keepStream «snap», 1 pro Sekunde) - zu, sobald die Seite verdeckt, die
#     Kachel weggescrollt / versteckt oder die Reihe aus ist. Ein Kachelbild: 256 px breit, JPEG-Qualität 60, pro Quelle höchstens
#     1 pro Sekunde gerechnet (Zwischenspeicher, gleich für alle Zuschauer).
#   * Kopf: aus dem fertigen Bild des Hauptprogramms (frame_out) - der Kopf rechnet dafür kein grosses JPEG (kein web_viewers).
#     Zusatzkameras: nur solange jemand eine Kachel ansieht, legt ihre Schleife 1× pro Sekunde ein kleines Bild ab (ExtraCam).
#     Wärmebild: die Wärmebildkamera (230) bleibt offen, solange eine Kachel / das grosse Bild sie ansieht (Ausleihe, 5 s) -
#     ein Gerät, kein zweites Öffnen.
#   * Quellen, die sonst niemand offen hat (USB, Pi, Netz): eine Vorschau öffnet sie erst beim ersten Bild, USB klein (640×360,
#     10 Bilder/s), höchstens 3 gleichzeitig, zu nach 8 s ohne Zuschauer und sofort, wenn MoveEye die Quelle selbst braucht
#     (Hauptkamera, Zusatzkamera, Wärmebild, Kamera-Suche, Hauptkamera verbindet sich gerade).
#   * Grosses Bild einer solchen Quelle: /cam_view/<quelle>, MJPEG höchstens 6 Bilder/s, 640 px; weiter EIN Strom (keepStream.retarget).
# Netzwerk-Kameras: die Adresse (mit Benutzer / Passwort) bleibt auf dem Gerät; der Browser kennt nur «url:<id>» und den Namen,
# das Bild kommt über MoveEye (Proxy), Fehler nur mit mask_url.
# Pi-Fenster (Tk): hat die drei Ansichten von 639zv (Kopf / Wärmebild / Weitwinkel + kleines Bild), keine Kacheln aller Quellen.
# Übersetzungen: unten (_HX_KW, alle 5 Sprachen). Test: werkzeuge/kamerawahl_test.py.
# ----------------------------------------------------------------------------
KW_THUMB_W = 256            # px width of a tile picture
KW_THUMB_Q = 60             # JPEG quality of a tile picture
KW_THUMB_EVERY = 1.0        # s: a tile picture of a source at most this often
KW_VIEW_W = 640             # px: the big picture of a source without its own stream
KW_VIEW_FPS = 6.0
KW_LEASE = 5.0              # s: a picture keeps the source (thermal camera, extra camera) awake this long
KW_PV_MAX = 3               # previews of otherwise closed sources at the same time
KW_PV_IDLE = 8.0            # s without a viewer: the preview closes
KW = {"pv": {}, "thumbs": {}, "th_until": 0.0, "usb": ([], 0.0), "pi": ([], -1e9), "list": ([], 0.0)}
KW_LOCK = threading.Lock()
WEB_UI_LOCAL.add("mw-kamwahl")                            # per device: which camera this phone shows big
PERM_GET["live"] = tuple(PERM_GET.get("live", ())) + ("/cam_thumb/", "/cam_view/")

KW_TRIO_HINT = {"head": "Check the camera under Settings → Cameras & head → Video source.",
                "wide": "Add the wide-angle camera under Settings → Cameras & head (extra camera as overview).",
                "thermal": "Choose the thermal camera under Settings → Cameras & head → Thermal camera."}


def kw_usb_cams():
    """USB cameras that are plugged in, WITHOUT opening them (10 s cache): [(spec, name)]. The capture node of a camera has
    «index» 0 (the second node of most webcams is metadata); the internal nodes of the Pi are left out (V4L_SKIP).
    MW_TEST_V4L="5:Name,6:Name" replaces the search (tests)."""
    lst, t = KW["usb"]
    if time.time() - t < 10.0:
        return lst
    out = []
    env = os.environ.get("MW_TEST_V4L")
    if env is not None:
        for part in env.split(","):
            n, _, nm = part.partition(":")
            if n.strip().isdigit():
                out.append(("usb:" + n.strip(), "USB camera: " + (nm.strip() or "video" + n.strip())))
    elif sys.platform.startswith("linux"):
        for p in sorted(glob.glob("/sys/class/video4linux/video*"), key=lambda x: int(re.sub(r"\D", "", x) or 0)):
            n = re.sub(r"\D", "", os.path.basename(p))
            if not n or int(n) > 99:
                continue
            nm = _v4l_name(int(n))
            if any(b in nm.lower() for b in V4L_SKIP):
                continue
            try:
                with open(os.path.join(p, "index")) as f:
                    if f.read().strip() not in ("", "0"):
                        continue
            except OSError:
                pass
            out.append(("usb:" + n, "USB camera: " + (nm or "video" + n)))
    KW["usb"] = (out, time.time())
    return out


def kw_pi_cams():
    """further Raspberry Pi cameras (CSI), 60 s cache"""
    lst, t = KW["pi"]
    if time.time() - t < 60.0:
        return lst
    out = [f"pi:{n}" for n in _pi_cams()]
    KW["pi"] = (out, time.time())
    return out


def kw_used():
    """sources MoveEye itself has (or wants) open - a preview never takes them"""
    u = {str(CFG.get("source") or ""), str(STATE.get("source_id") or ""), str(CFG.get("thermal_source") or ""), str(CFG.get("kopf_ov") or "")}
    u |= {str(c.spec) for c in CAMS} | {str(x) for x in (CFG.get("extra_cams") or [])}
    u.discard(""); u.discard("auto")
    return u


def kw_icon(spec):
    k = str(spec).split(":")[0]
    return {"usb": "📷", "pi": "🎥", "url": "🌐", "senxor": "🌡"}.get(k, "📹")


def kw_head_ok():
    st = str(STATE.get("source_status") or "")
    return st == "connected" or st.startswith("switch failed")


def kw_thermal_ok():
    sp = str(CFG.get("thermal_source") or "")
    if not sp or sp == STATE.get("source_id"):
        return False
    if str(STATE.get("thermal") or "").startswith(THERMAL_NOT_FOUND) or thermal_absent(sp, ""):
        return False
    return True


def kw_list():
    """the tiles for the live page (in /api/state → extra[0].kw); empty in the simulator mode (there: as before, 639zt / 549).
    Each: k (key = what /cam_thumb/<k> takes), ic, lb (English key, the three views) or name, ok, trio, big (address of the
    big picture), hint (English key, only when a view of the trio is missing). Never an address of a network camera."""
    if CFG.get("sim_on"):
        return []
    lst, t = KW["list"]
    if time.time() - t < 1.5:
        return lst
    out = [{"k": "head", "ic": "🎯", "lb": "Head view", "name": str(STATE.get("source_label") or source_label(str(CFG.get("source") or "auto"))),
            "ok": kw_head_ok(), "trio": True, "big": "/video_feed"}]
    wc = view3_wide_cam()
    out.append({"k": "wide", "ic": "🔭", "lb": "Wide view", "name": wc.label if wc else "", "ok": bool(wc and wc.status == "connected"),
                "trio": True, "big": f"/cam_feed/{wc.idx}" if wc else ""})
    tsp = str(CFG.get("thermal_source") or "")
    out.append({"k": "thermal", "ic": "🌡", "lb": "Thermal view", "name": source_label(tsp) if tsp else "", "ok": kw_thermal_ok(),
                "trio": True, "big": "/cam_view/thermal"})
    for it in out:
        if not it["ok"]:
            it["hint"] = KW_TRIO_HINT[it["k"]]
    for c in list(CAMS):
        if wc is not None and c is wc:
            continue
        out.append({"k": str(c.spec), "ic": kw_icon(c.spec), "name": c.label, "ok": c.status == "connected", "trio": False, "big": f"/cam_feed/{c.idx}"})
    used = kw_used()
    others = [(sp, source_label(sp)) for sp in kw_pi_cams()] + kw_usb_cams() + [("url:" + s["id"], s["name"]) for s in CFG.get("ip_sources") or []]
    for sp, nm in others:
        if sp in used or any(x["k"] == sp for x in out):
            continue
        pv = KW["pv"].get(sp)
        out.append({"k": sp, "ic": kw_icon(sp), "name": str(nm)[:48], "ok": not (pv is not None and pv.err), "trio": False,
                    "big": "/cam_view/" + sp})
    KW["list"] = (out, time.time())
    return out


def kw_find(k):
    return next((x for x in kw_list() if x["k"] == k), None)


# ---- pictures --------------------------------------------------------------------------------------------------------------------
class KwPreview:
    """a source nobody else has open (USB, Pi, network camera), opened only while somebody looks at its tile / big picture"""
    def __init__(self, spec):
        self.spec = spec; self.frame = None; self.t = 0.0; self.seen = time.time(); self.stop = False; self.err = ""
        threading.Thread(target=self.loop, daemon=True, name="kwprev").start()

    def touch(self):
        self.seen = time.time()

    def busy(self):
        """MoveEye needs the source itself (or the main camera is connecting / the camera search runs): give way"""
        if self.spec in kw_used() or SOURCES.get("scanning") or CFG.get("sim_on") or toolmode_on():
            return True
        return self.spec.split(":")[0] in ("usb", "pi") and not kw_head_ok()

    def _open(self):
        kind, _, arg = self.spec.partition(":")
        if kind == "usb" and not DEMO["on"]:
            idx = int(arg)
            if _v4l_internal(idx):
                return None, "no camera"
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            if not cap.isOpened():
                cap.release(); return None, f"no picture from /dev/video{idx}"
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            cap.set(cv2.CAP_PROP_FPS, 10); cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ok, fr = cap.read()
            if not ok:
                cap.release(); return None, f"no picture from /dev/video{idx}"
            return CvSource(cap, (fr.shape[1], fr.shape[0])), ""
        src, _sid, _lb, err = open_source(self.spec)      # network cameras: the address stays here; err is masked (mask_url)
        return src, err

    def loop(self):
        src = None
        try:
            if self.busy():
                self.err = "in use"; return
            src, err = self._open()
            if src is None:
                self.err = err or "no picture"; return
            live = self.spec.startswith("url:")            # a network stream must be read all the time (else it lags)
            fails, last = 0, 0.0
            while not self.stop and time.time() - self.seen < KW_PV_IDLE and not self.busy():
                t0 = time.time()
                ok, fr = src.read()
                if not ok or fr is None:
                    fails += 1
                    if fails >= 30:
                        self.err = "connection lost"; break
                    time.sleep(0.05); continue
                fails = 0
                if t0 - last >= 1.0 / KW_VIEW_FPS:
                    self.frame, self.t, last = fr, time.time(), t0
                if not live:
                    time.sleep(max(0.0, 1.0 / KW_VIEW_FPS - (time.time() - t0)))
        except Exception as e:
            self.err = str(e)[:120]
        finally:
            if src is not None:
                try:
                    src.release()
                except Exception:
                    pass
            self.frame = None
            with KW_LOCK:
                if KW["pv"].get(self.spec) is self and not self.err:
                    KW["pv"].pop(self.spec, None)
                elif KW["pv"].get(self.spec) is self:
                    self.t = time.time()                    # keep the error a while (tile shows ⚠), then it may try again


def kw_pv(spec):
    """the preview of an otherwise closed source (started on demand), or None"""
    with KW_LOCK:
        p = KW["pv"].get(spec)
        if p is not None and p.err and time.time() - p.t > 15.0:
            KW["pv"].pop(spec, None); p = None                # tried again after 15 s
        if p is None:
            if sum(1 for x in KW["pv"].values() if not x.err) >= KW_PV_MAX:
                return None
            p = KwPreview(spec); KW["pv"][spec] = p
        p.touch()
        return p


def kw_pv_close(kinds=("usb", "pi"), wait=2.0):
    """close the previews (of these kinds) - before MoveEye opens cameras itself"""
    ps = [p for s, p in list(KW["pv"].items()) if s.split(":")[0] in kinds]
    for p in ps:
        p.stop = True
    end = time.time() + wait
    while ps and time.time() < end and any(p.frame is not None for p in ps):
        time.sleep(0.05)


_scan_sources_kw = scan_sources


def scan_sources(active_id=""):                           # + 639zzi: the camera search must find the cameras the previews hold
    kw_pv_close()
    return _scan_sources_kw(active_id)


_ThermalCam_wanted_kw = ThermalCam.wanted


def _kw_thermal_wanted(self):
    w = _ThermalCam_wanted_kw(self)
    if not w and time.time() < KW["th_until"] and not CFG.get("sim_on"):
        sp = str(CFG.get("thermal_source") or "")
        if sp and sp != STATE.get("source_id"):
            return sp                                     # a tile looks at the thermal picture: keep it open (no setting changes)
    return w


ThermalCam.wanted = _kw_thermal_wanted                    # wraps: ThermalCam.wanted

_ExtraCam_process_kw = ExtraCam._process


def _kw_extra_process(self, frame, bg):
    _ExtraCam_process_kw(self, frame, bg)
    now = time.time()
    if now < getattr(self, "kw_until", 0.0) and now - getattr(self, "kw_t", 0.0) >= KW_THUMB_EVERY * 0.9:
        self.kw_t = now; self.kw_frame = kw_small(frame, KW_THUMB_W)


ExtraCam._process = _kw_extra_process                     # wraps: ExtraCam._process


def kw_small(fr, w):
    H, W = fr.shape[:2]
    if W == w:
        return fr
    return cv2.resize(fr, (w, max(1, int(H * w / W))), interpolation=cv2.INTER_AREA if W > w else cv2.INTER_CUBIC)


def kw_frame(k, it=None):
    """(BGR picture or None, its time) of a source right now; keeps it awake (lease)"""
    it = it or kw_find(k)
    if not it:
        return None, 0.0
    now = time.time()
    if k == "head":
        w = WATCH_REF.get("w")
        f = getattr(w, "frame_out", None) if w is not None else None
        return f, now
    if k == "thermal":
        KW["th_until"] = now + KW_LEASE
        th = THERMAL
        if th is None or th.frame is None or now - th.t > 3.0:
            return None, 0.0
        return th.color(th.crop(th.frame))[0], th.t
    c = view3_wide_cam() if k == "wide" else next((x for x in CAMS if str(x.spec) == k), None)
    if c is not None:
        c.kw_until = now + KW_LEASE
        return getattr(c, "kw_frame", None), getattr(c, "kw_t", 0.0)
    if k.startswith(("usb:", "pi:", "url:")):
        p = kw_pv(k)
        return (p.frame, p.t) if p is not None else (None, 0.0)
    return None, 0.0


def kw_thumb(k):
    """JPEG bytes of the tile picture (at most one new one per second and source, the same for every viewer) or None"""
    it = kw_find(k)
    if not it or (it["trio"] and not it["ok"]):
        return None
    now = time.time()
    c_ = KW["thumbs"].get(k)
    if c_ and now - c_[0] < KW_THUMB_EVERY:
        kw_frame(k, it)                                      # keep the lease
        return c_[1]
    end = now + 2.5
    while True:
        f, _t = kw_frame(k, it)
        if f is not None or time.time() >= end:
            break
        time.sleep(0.1)                                      # just started (preview, thermal camera, extra camera): wait a moment
    if f is None:
        return c_[1] if c_ else None
    try:
        ok, buf = cv2.imencode(".jpg", kw_small(f, KW_THUMB_W), [cv2.IMWRITE_JPEG_QUALITY, KW_THUMB_Q])
    except cv2.error:
        return None
    if not ok:
        return None
    KW["thumbs"][k] = (time.time(), buf.tobytes())
    return KW["thumbs"][k][1]


def kw_routes(app):
    from flask import Response, request

    @app.route("/cam_thumb/<path:key>")
    def cam_thumb(key):
        if not kw_find(key):
            return Response("unknown camera", 404, headers={"Cache-Control": "no-store"})
        jpg = kw_thumb(key)
        if not jpg:
            return Response("no picture yet", 503, headers={"Cache-Control": "no-store"})
        return Response(jpg, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

    @app.route("/cam_view/<path:key>")
    def cam_view(key):
        it = kw_find(key)
        if not it or not str(it.get("big") or "").startswith("/cam_view/") or (it["trio"] and not it["ok"]):
            return Response("unknown camera", 404)
        rip = request.remote_addr or ""

        def gen():
            last = None
            try:
                remote_stream(rip, +1)
            except Exception:
                pass
            try:
                while True:
                    t0 = time.time()
                    f, ft = kw_frame(key, it)
                    if f is not None and ft != last:
                        last = ft
                        w = KW_VIEW_W if key != "thermal" else 480
                        ok, buf = cv2.imencode(".jpg", kw_small(f, w), [cv2.IMWRITE_JPEG_QUALITY, 70])
                        if ok:
                            jpg = buf.tobytes()
                            yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                    time.sleep(max(0.02, 1.0 / KW_VIEW_FPS - (time.time() - t0)))
            finally:
                try:
                    remote_stream(rip, -1)
                except Exception:
                    pass
        return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame", headers={"Cache-Control": "no-store"})


_smalltv_routes_639zzi = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzi: /cam_thumb/<quelle>, /cam_view/<quelle>
    _smalltv_routes_639zzi(app, reply, body)
    kw_routes(app)


_cams_status_kw = cams_status


def cams_status(watch=None):                              # + 639zzi: the tiles of every camera (live page)
    out = _cams_status_kw(watch)
    try:
        out[0]["kw"] = kw_list()
    except Exception:
        out[0]["kw"] = []
    return out


_HX_KW = {   # English (key): Deutsch, Français, Italiano, Rumantsch
    "Not connected": ("nicht angeschlossen", "non connectée", "non collegata", "betg colliada"),
    "In the big picture": ("Im grossen Bild", "Dans la grande image", "Nell’immagine grande", "En il grond maletg"),
    "Tap: show this camera big (only the view - detection and settings stay)": (
        "Antippen: diese Kamera gross zeigen (nur die Anzeige – Erkennung und Einstellungen bleiben)",
        "Toucher : afficher cette caméra en grand (seulement l’affichage – détection et réglages restent)",
        "Tocca: mostra questa telecamera grande (solo la vista – rilevamento e impostazioni restano)",
        "Tutgar: mussar questa camera grond (mo la vista – la detecziun ed ils parameters restan)"),
    "All cameras": ("Alle Kameras", "Toutes les caméras", "Tutte le telecamere", "Tut las cameras"),
    "No picture right now": ("Gerade kein Bild", "Pas d’image pour l’instant", "Al momento nessuna immagine", "Ussa nagin maletg"),
    "Check the camera under Settings → Cameras & head → Video source.": (
        "Kamera prüfen unter Einstellungen → Kameras & Kopf → Videoquelle.",
        "Vérifier la caméra sous Réglages → Caméras & tête → Source vidéo.",
        "Controlla la telecamera in Impostazioni → Telecamere & testa → Sorgente video.",
        "Controllar la camera sut Parameters → Cameras & chau → Funtauna da video."),
    "Add the wide-angle camera under Settings → Cameras & head (extra camera as overview).": (
        "Weitwinkel-Kamera einrichten unter Einstellungen → Kameras & Kopf (Zusatzkamera als Übersicht).",
        "Ajouter la caméra grand angle sous Réglages → Caméras & tête (caméra supplémentaire comme vue d’ensemble).",
        "Aggiungi la telecamera grandangolare in Impostazioni → Telecamere & testa (telecamera aggiuntiva come panoramica).",
        "Agiuntar la camera da grond angul sut Parameters → Cameras & chau (camera supplementara sco survista)."),
    "Choose the thermal camera under Settings → Cameras & head → Thermal camera.": (
        "Wärmebildkamera wählen unter Einstellungen → Kameras & Kopf → Wärmebild.",
        "Choisir la caméra thermique sous Réglages → Caméras & tête → Caméra thermique.",
        "Scegli la termocamera in Impostazioni → Telecamere & testa → Termocamera.",
        "Tscherner la camera termica sut Parameters → Cameras & chau → Camera termica."),
}
for _k, _v in _HX_KW.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

KAMWAHL_JS = r"""
<style id="kw-css">
#kw-row{position:absolute;z-index:4;left:8px;top:8px;display:flex;gap:6px;align-items:flex-start;pointer-events:none;max-width:calc(100% - 16px)}
#kw-row[hidden]{display:none}
#kw-row .kw-t{pointer-events:auto;position:relative;flex:none;display:block;width:var(--kw-w,110px);aspect-ratio:16/9;padding:0;margin:0;min-height:0;
  border:2px solid rgba(255,255,255,.8);border-radius:8px;overflow:hidden;background:#000;color:#fff;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.5);
  touch-action:manipulation;-webkit-tap-highlight-color:transparent;font:inherit}
#kw-row .kw-t img{display:block;width:100%;height:100%;object-fit:cover;min-height:0;max-height:none;-webkit-user-drag:none;pointer-events:none}
#kw-row .kwl{position:absolute;left:4px;bottom:4px;right:4px;z-index:2;font:700 10px/1.15 system-ui,sans-serif;color:#fff;text-align:left;pointer-events:none;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#kw-row .kwl b{font-weight:700;background:rgba(0,0,0,.6);padding:3px 5px;border-radius:4px;display:inline-block;max-width:100%;overflow:hidden;text-overflow:ellipsis;vertical-align:bottom}
#kw-row .kw-t.na{border-style:dashed;border-color:rgba(255,255,255,.45);background:rgba(22,28,38,.86);cursor:help;box-shadow:none}
#kw-row .kw-t.na .kwn{position:absolute;left:0;right:0;top:10%;text-align:center;font:600 9.5px/1.15 system-ui,sans-serif;color:#c3ccd8;padding:0 4px;
  overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow-wrap:anywhere}
#kw-row .kw-t.na .kwl b{background:transparent;color:#aeb8c6;padding:0 1px}
#kw-row .kw-t.kw-wait::after{content:"⏳";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:14px;background:rgba(0,0,0,.35)}
#kw-row .kw-t.kw-err::before{content:"⚠";position:absolute;right:4px;top:3px;z-index:3;font-size:12px}
#kw-row .kw-more{background:rgba(8,12,20,.78);border-color:rgba(255,255,255,.55);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;
  font:700 12px/1.1 system-ui,sans-serif}
#kw-row .kw-more small{font-size:10.5px;font-weight:600;opacity:.8}
#kw-menu{position:fixed;z-index:400;min-width:240px;max-width:calc(100vw - 24px);max-height:calc(100vh - 24px);overflow-y:auto;background:var(--panel,#121821);color:var(--txt,#e8eef5);
  border:1px solid var(--line,#2a3442);border-radius:12px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.5);font-family:system-ui,-apple-system,sans-serif}
#kw-menu[hidden]{display:none}
#kw-menu .v3mh{font-size:12px;font-weight:700;opacity:.7;padding:4px 8px 6px}
#kw-menu button{display:flex;width:100%;align-items:center;gap:10px;text-align:left;padding:8px 10px;min-height:46px;border-radius:8px;background:transparent;
  border:0;color:inherit;font:inherit;font-size:15px;cursor:pointer}
#kw-menu button.on{background:var(--acc,#3b8cff);color:#fff}
#kw-menu button.na{opacity:.48}
#kw-menu .v3i{font-size:20px;width:26px;text-align:center;flex:none}
#kw-menu small{display:block;font-size:11px;opacity:.78;margin-top:1px}
</style>
<script>
(function () {
  if (document.body.dataset.tab !== "live") return;
  try { const D = /*KWDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const say = m => { try { toast(m); } catch (e) {} };
  const vimg = document.getElementById("video");
  if (!vimg) return;
  const KEY = "mw-kamwahl";                                // per device: which camera is big on this phone (view only)
  const S = {sel: null};
  try { const o = JSON.parse(localStorage.getItem(KEY) || "{}"); if (typeof o.sel === "string") S.sel = o.sel; } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify({sel: S.sel})); } catch (e) {} };
  const J = () => (typeof QSJ !== "undefined" && QSJ) || {};
  const ST = () => J().state || {};
  const list = () => { const x = ST().extra; return (x && x[0] && Array.isArray(x[0].kw)) ? x[0].kw : []; };
  const may = () => { const me = ST().me; return !me || !Array.isArray(me.perms) || me.perms.indexOf("live") >= 0; };   // the right «live», like the picture
  const V3 = () => window.mwView3 || null;
  const active = () => list().length > 0 && may() && !document.body.classList.contains("sv-on") && !document.body.classList.contains("sim-on");
  const find = k => list().find(x => x.k === k) || null;
  const nm = it => it.lb ? T(it.lb) : it.name;
  function selItem() {                                    // another camera big (not head / wide: they belong to 639zv)
    if (!S.sel || !active()) return null;
    const it = find(S.sel);
    return it && it.big && it.k !== "head" && it.k !== "wide" && (it.ok || !it.trio) ? it : null;
  }
  function bigKey() { const it = selItem(); if (it) return it.k; return V3() && V3().cur() === "wide" ? "wide" : "head"; }
  function miniKey() { const m = document.getElementById("v3-mini"); return m && !m.hidden ? (bigKey() === "wide" ? "head" : "wide") : null; }
  function pick(k, quiet) {
    const it = find(k); if (!it) return false;
    if (it.trio && !it.ok) { say(it.ic + " " + T(it.lb) + ": " + T("Not connected") + " – " + T(it.hint || "")); return false; }
    if (k === "head" || k === "wide") { S.sel = null; save(); if (V3()) V3().look(k); }
    else { S.sel = k; save(); if (V3()) V3().apply(); }
    paint();
    if (!quiet) say(it.ic + " " + nm(it));
    return true;
  }
  // ---- the tiles ----
  const ROW = E("div"); ROW.id = "kw-row"; ROW.hidden = true;
  const TL = {};                                          // key -> {b, img, sig}
  let MORE = null, lastW = 0;
  function tile(it) {
    const sig = [it.k, it.ok, it.trio, nm(it), it.ic].join("|");
    let x = TL[it.k];
    if (x && x.sig === sig) return x.b;
    if (x) x.b.remove();
    const b = E("button", "kw-t" + (it.trio && !it.ok ? " na" : "")); b.type = "button"; b.dataset.k = it.k;
    const lab = E("span", "kwl"), lb = E("b", "", it.ic + " " + nm(it)); lab.appendChild(lb);
    let img = null;
    if (it.trio && !it.ok) {
      b.append(E("span", "kwn", T("Not connected")), lab);
      b.title = T(it.lb) + ": " + T("Not connected") + " – " + T(it.hint || "");
    } else {
      img = E("img"); img.alt = ""; img.draggable = false; b.append(img, lab);
      b.title = nm(it) + (it.trio && it.name ? " (" + it.name + ")" : "") + " · " + T("Tap: show this camera big (only the view - detection and settings stay)");
      keepStream(img, {snap: "/cam_thumb/" + encodeURIComponent(it.k), every: 1000, onlost: on => b.classList.toggle("kw-wait", on)});
    }
    b.setAttribute("aria-label", b.title);
    b.addEventListener("click", e => { e.stopPropagation(); e.preventDefault(); pick(it.k); });
    b.addEventListener("dblclick", e => e.stopPropagation());
    TL[it.k] = {b: b, img: img, sig: sig};
    return b;
  }
  function paint() {
    const MB = document.getElementById("v3-mini"), h = MB && MB.parentNode;
    const on = active() && !!h && vimg.parentNode === h && !(V3() && V3().state().pip === false);
    if (!on) {
      ROW.hidden = true;
      if (MB && MB.dataset.kww) { MB.style.width = ""; delete MB.dataset.kww; }
      if (S.sel && list().length && !find(S.sel)) { S.sel = null; save(); }
      return;
    }
    if (ROW.parentNode !== h) h.appendChild(ROW);
    const W = h.clientWidth || 360, slots = W >= 900 ? 5 : W >= 600 ? 4 : 3;
    const tw = Math.max(72, Math.min(170, Math.floor((W * 0.8 - 6 * (slots - 1)) / slots)));
    if (tw !== lastW) { ROW.style.setProperty("--kw-w", tw + "px"); lastW = tw; }
    const mini = miniKey();
    if (MB && mini) { MB.style.width = tw + "px"; MB.dataset.kww = "1"; }
    else if (MB && MB.dataset.kww) { MB.style.width = ""; delete MB.dataset.kww; }
    const big = bigKey();
    const rest = list().filter(x => x.k !== big && x.k !== mini).map((x, i) => [x, i])
      .sort((a, b) => ((b[0].ok ? 1 : 0) - (a[0].ok ? 1 : 0)) || a[1] - b[1]).map(x => x[0]);   // connected first, else as listed
    const free = slots - (mini ? 1 : 0);
    const vis = rest.length > free ? rest.slice(0, Math.max(0, free - 1)) : rest, more = rest.length - vis.length;
    // beside the tool buttons of the picture (536 #lv-tools, top right) when there is room, else in a second line under them
    const top0 = h.closest && h.closest("#pv") ? 30 : 8, n = vis.length + (more > 0 ? 1 : 0);
    let left = 8 + (mini ? tw + 6 : 0), top = top0;
    const tools = document.getElementById("lv-tools"), hr = h.getBoundingClientRect();
    if (tools && tools.getClientRects().length && h.contains(tools)) {
      const r = tools.getBoundingClientRect();
      if (left + n * tw + 6 * Math.max(0, n - 1) > r.left - hr.left - 6) { left = 8; top = Math.max(top0 + (mini ? Math.round(tw * 9 / 16) + 10 : 0), r.bottom - hr.top + 6); }
    }
    ROW.style.left = left + "px"; ROW.style.top = top + "px";
    const want = vis.map(tile);
    if (more > 0) {
      if (!MORE) { MORE = E("button", "kw-t kw-more"); MORE.type = "button"; MORE.id = "kw-more";
        MORE.addEventListener("click", e => { e.stopPropagation(); e.preventDefault(); menu(MORE); }); MORE.addEventListener("dblclick", e => e.stopPropagation()); }
      MORE.textContent = ""; MORE.append(E("span", "", "⋯ " + T("Cameras")), E("small", "", "+" + more));
      MORE.title = T("All cameras"); MORE.setAttribute("aria-label", MORE.title + " (+" + more + ")");
      want.push(MORE);
    }
    want.forEach((b, i) => { if (ROW.children[i] !== b) ROW.insertBefore(b, ROW.children[i] || null); });
    while (ROW.children.length > want.length) ROW.lastChild.remove();
    for (const k in TL) {                                 // tiles of sources that are gone
      if (!find(k)) { TL[k].b.remove(); delete TL[k]; continue; }
      const it = find(k); TL[k].b.classList.toggle("kw-err", !it.ok && !it.trio);
    }
    ROW.hidden = false;
  }
  // ---- «⋯ Kameras»: every source ----
  const MN = E("div"); MN.id = "kw-menu"; MN.hidden = true; MN.setAttribute("role", "menu"); document.body.appendChild(MN);
  function menu(anchor) {
    MN.textContent = ""; const big = bigKey();
    MN.appendChild(E("div", "v3mh", "📷 " + T("All cameras")));
    list().forEach(it => {
      const na = it.trio && !it.ok, b = E("button", it.k === big ? "on" : na ? "na" : ""); b.type = "button"; b.dataset.k = it.k; b.setAttribute("role", "menuitemradio");
      const tx = E("span"); tx.append(nm(it), E("small", "", it.k === big ? T("In the big picture") : na ? T("Not connected") : !it.ok ? T("No picture right now") : (it.lb ? it.name : "")));
      b.append(E("span", "v3i", it.ic), tx);
      b.onclick = e => { e.stopPropagation(); MN.hidden = true; pick(it.k); };
      MN.appendChild(b);
    });
    MN.hidden = false;
    const r = anchor.getBoundingClientRect(), mw = MN.offsetWidth, mh = MN.offsetHeight;
    let x = Math.min(innerWidth - mw - 8, Math.max(8, r.left)), y = r.bottom + 6;
    if (y + mh > innerHeight - 8) y = Math.max(8, r.top - mh - 6);
    MN.style.left = x + "px"; MN.style.top = y + "px";
  }
  document.addEventListener("click", e => { if (!MN.hidden && !MN.contains(e.target) && !(MORE && MORE.contains(e.target))) MN.hidden = true; }, true);
  addEventListener("keydown", e => { if (e.key === "Escape" && !MN.hidden) MN.hidden = true; });
  window.mwKamWahl = {
    big: () => { const it = selItem(); return it ? {src: it.big, ic: it.ic, lb: nm(it), k: it.k} : null; },
    clear: () => { if (S.sel) { S.sel = null; save(); } },
    pick: pick, paint: paint, menu: () => menu(MORE || ROW),
    state: () => ({sel: S.sel, big: bigKey(), mini: miniKey(), on: !ROW.hidden, tiles: [...ROW.children].map(b => b.dataset.k || "more"), list: list().map(x => x.k)})};
  addEventListener("resize", () => setTimeout(paint, 80));
  setInterval(paint, 1000);
  setTimeout(paint, 0);
})();
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", KAMWAHL_JS.replace("/*KWDE*/{}", json.dumps({_k: _v[0] for _k, _v in _HX_KW.items()}, ensure_ascii=False), 1)
                            + "</body>", 1)

_HELP_KW = {
    "de": '<li><b>Alle Kameras als kleine Bilder</b> (am echten Gerät): oben links im Live-Bild je ein kleines Bild für Kopf, Weitwinkel, Wärmebild, USB-, Pi- und Netzwerk-Kameras. Antippen = diese Kamera gross – nur die Anzeige, die Erkennung und die Einstellungen bleiben. Fehlt Kopf, Weitwinkel oder Wärmebild: graue Kachel «nicht angeschlossen» (antippen = wo einrichten). Mehr Kameras als Platz: «⋯ Kameras».</li>',
    "en": '<li><b>Every camera as a small picture</b> (on the real device): top left in the live picture one small picture each for head, wide angle, thermal, USB, Pi and network cameras. Tap = this camera big – only the view, detection and settings stay. Head, wide angle or thermal missing: grey tile «not connected» (tap = where to set it up). More cameras than room: «⋯ Cameras».</li>',
    "fr": '<li><b>Toutes les caméras en petites images</b> (sur l’appareil réel) : en haut à gauche de l’image en direct, une petite image pour la tête, le grand angle, l’image thermique, les caméras USB, Pi et réseau. Toucher = cette caméra en grand – seulement l’affichage, la détection et les réglages restent. Tête, grand angle ou thermique manquant : vignette grise « non connectée » (toucher = où la configurer). Plus de caméras que de place : « ⋯ Caméras ».</li>',
    "it": '<li><b>Tutte le telecamere come immagini piccole</b> (sul dispositivo reale): in alto a sinistra nell’immagine live una piccola immagine per testa, grandangolo, immagine termica, telecamere USB, Pi e di rete. Tocca = questa telecamera grande – solo la vista, rilevamento e impostazioni restano. Testa, grandangolo o termica mancante: riquadro grigio «non collegata» (tocca = dove configurarla). Più telecamere che spazio: «⋯ Telecamere».</li>',
    "rm": '<li><b>Tut las cameras sco pitschens maletgs</b> (sin l’apparat real): sura a sanestra en il maletg live in pitschen maletg per chau, grond angul, maletg termic, cameras USB, Pi e da rait. Tutgar = questa camera grond – mo la vista, la detecziun ed ils parameters restan. Chau, grond angul u maletg termic manca: plattina grischa «betg colliada» (tutgar = nua configurar). Dapli cameras che plaz: «⋯ Cameras».</li>',
}


def _help_kw(doc, lang):
    i = doc.find('<section id="views"')
    if i < 0 or 'id="kw-help"' in doc:
        return doc
    j = doc.find("</ul></section>", i)
    if j < 0:
        return doc
    return doc[:j] + _HELP_KW[lang].replace("<li>", '<li id="kw-help">', 1) + doc[j:]


_hp_en_kw = HELP_PAGE.find('<div lang="en">')
if _hp_en_kw > 0:
    HELP_PAGE = _help_kw(HELP_PAGE[:_hp_en_kw], "de") + _help_kw(HELP_PAGE[_hp_en_kw:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_kw(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def kamwahl_selftest():
    html = WEB_PAGE
    assert html.count('id="kw-css"') == 1 and "/*KWDE*/" not in html, "Kamerawahl not in the live page"
    assert html.find('id="kw-css"') > html.find('id="v3-css"') > 0, "after 639zv"
    for need in ("window.mwKamWahl", '"/cam_thumb/"', "keepStream(img", '"mw-kamwahl"', 'me.perms.indexOf("live")', "V3().look(k)"):
        assert need in KAMWAHL_JS, "Kamerawahl: missing " + need
    for bad in ("/api/set", "thermal_on", "/api/source"):
        assert bad not in KAMWAHL_JS, "Kamerawahl must not change settings: " + bad
    assert "kwClear()" in VIEW3_JS and "kb ? kb.src" in VIEW3_JS and "look: look" in VIEW3_JS, "639zv: hooks for the tiles"
    for k, v in _HX_KW.items():
        assert len(v) == 4 and all(v), k
        assert k in DE and k in TRX["fr"] and k in TRX["it"] and k in TRX["rm"], k
    for v in KW_TRIO_HINT.values():
        assert v in _HX_KW, v
    assert "mw-kamwahl" in WEB_UI_LOCAL
    assert role_allows("custom", "/cam_thumb/usb:2", "GET", {}, {"live"}) and not role_allows("custom", "/cam_thumb/usb:2", "GET", {}, set())
    assert role_allows("custom", "/cam_view/thermal", "GET", {}, {"live"}) and not role_allows("custom", "/cam_view/thermal", "GET", {}, {"rec"})
    assert HELP_PAGE.count('id="kw-help"') == 2, "manual: tiles"
    keep = ({k: CFG.get(k) for k in ("sim_on", "ip_sources", "thermal_source", "kopf_ov", "source", "extra_cams")}, dict(KW), os.environ.get("MW_TEST_V4L"))
    try:
        os.environ["MW_TEST_V4L"] = "7:Test cam"
        KW.update(list=([], 0.0), usb=([], 0.0), pi=([], 1e18))
        CFG.update(sim_on=False, thermal_source="", kopf_ov="", source="usb:7", extra_cams=[],
                   ip_sources=[{"id": "0123abcd", "name": "Gate", "url": "rtsp://user:geheim@10.0.0.9/live"}])
        L = kw_list(); ks = [x["k"] for x in L]
        assert ks[:3] == ["head", "wide", "thermal"], ks
        assert not L[1]["ok"] and not L[2]["ok"] and L[1]["hint"] and L[2]["hint"], L[1:3]
        assert "usb:7" not in ks, "the main camera is no extra tile"
        assert "url:0123abcd" in ks and "geheim" not in json.dumps(L) and "rtsp" not in json.dumps(L), "network camera: no address to the browser"
        CFG["source"] = "pi:0"; KW["list"] = ([], 0.0); KW["usb"] = ([], 0.0)
        assert "usb:7" in [x["k"] for x in kw_list()]
        CFG["sim_on"] = True; KW["list"] = ([], 0.0)
        assert kw_list() == [], "simulator: as before"
        assert "kw" in cams_status()[0]
    finally:
        CFG.update(keep[0]); KW.clear(); KW.update(keep[1])
        if keep[2] is None:
            os.environ.pop("MW_TEST_V4L", None)
        else:
            os.environ["MW_TEST_V4L"] = keep[2]
    return "tiles of every camera: list, no network address, rights, simulator unchanged, view only"


SELFTEST_EXTRA.append(("Camera tiles in the live picture: every source, view only (639zzi)", kamwahl_selftest))
