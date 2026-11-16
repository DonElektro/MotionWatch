#@ MoveEye – Teil 639zzzzm: «📍 Markier-Karte» (experimentell, ab Werk aus) – eine gedruckte Karte mit einem grossen ArUco-Marker vor die Kopf-Kamera halten: MoveEye piepst, folgt der Karte mit dem Kopf, und «Karte kurz umdrehen und wieder zeigen» speichert die Kopfstellung als Teach-in-Punkt «Punkt 1», «Punkt 2» … (mit geschätztem Abstand, gleich in der Runde). Nur bei Schutz «Aus», nur Marker dieses Geräts. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entscheide des Besitzers (15.11.2026, nach Vorschau, Messung und Simulator-Test auf dem Zweig mw-markier-karte):
#   * Karte = ArUco-Marker (Wörterbuch 4×4_50) mit einer Nummer aus MK_IDS (40–49, fest für dieses Gerät, höchstens 10 Karten) +
#     ein kleiner QR-Code «MK» + Kennung + Prüfnummer (HMAC mit dem Schlüssel der QR-Karten, qrk_key / qrk_mac, Teil 639zzp).
#     Der Marker allein reicht zum Start (nur Nummern einer Karte dieses Geräts); der QR-Code ist freiwillig: wird er aus der Nähe
#     gelesen, steht «QR bestätigt» in der Sitzung. Drucken A4 / A5 in der Karten-Werkstatt (/karten, Abschnitt «📍 Markier-Karten»).
#   * Nur bei Schutz «Aus» (CFG armed = False, kein Gehtest): bei Wachsam / Voll wird die Karte ignoriert, im Live-Bild ein oranger
#     Rahmen «Markier-Karte nur bei Schutz Aus» und eine Zeile im Protokoll (höchstens alle 10 min). Die Karte schaltet nie etwas aus.
#   * Folgen: eigener Beweger «marker» in KOPF_PRIO (162) gleich nach «alarm» - Hand und Alarm gehen vor, Runde / Parken warten.
#     Solange eine Sitzung läuft, macht das Folgen der Person (410 track, track_person / track_motion) Pause (kopf_track_blocked).
#     Der Kopf wird wie bei 410 track() gesteuert: Ziel = Winkel der Karte zur Bildmitte (kopf_pic_to_pan), ein Teil des Weges
#     (MK_GAIN), Totzone MK_DEAD, dann kurz warten, bis das Bild die neue Richtung zeigt; der Bewegungsplaner (072) fährt.
#   * Punkt merken: Karte MK_GAP_MIN … MK_GAP_MAX s weg (umgedreht) und wieder da, vorher ruhig gehalten (die Richtung der Karte
#     schwankte in den 0,8 s davor um höchstens 2 × MK_STILL_DEG, sie war in mind. 80 % der Bilder zu sehen) und am selben Ort
#     zurück (± 1,5°). Eine Person, die durchs Bild geht, deckt < 0,6 s ab; wer mit der Karte geht, hält sie nicht ruhig - beides
#     gibt keinen Punkt (gemessen in der Simulation: ohne «ruhig» entstanden falsche Punkte). Höchstens alle 3 s, doppelt (gleicher
#     Ort ± 1°) = Ton «schon gespeichert».
#   * Punkte: teach_add (076) mit «Punkt n» (erster freie Nummer), gleich in der Runde (Entscheid 4); Abstand aus der Seitenlänge
#     des Markers in Pixeln, der Brennweite (Bildbreite, cam_fov) und der gedruckten Markergrösse - steht in CFG mk_dist (Name →
#     m; Umbenennen / Löschen ziehen mit) und in der Teach-in-Liste («📍 ~7.4 m»). Der Punkt selbst bleibt [pan, tilt, Name]:
#     ältere MoveEye verlieren so nichts (ein 5. Feld würde wp_clean verwerfen).
#   * Annahme Neigung (Entscheid 6, nicht beim Besitzer nachgefragt): Schwenken / Neigen der Karte = die Servo-Stellung, in der die
#     Karte in der Bildmitte ist (kopf_pic_to_pan mit servo_pos und cam_fov - dieselbe Kalibrierung wie Teach-in, Verfolgen und
#     «zum Alarm drehen»). Die Kamera sitzt dabei auf der Achse des Kopfs; ein fester Einbauwinkel (im Simulator schaut die Kamera
#     bei Neigen 0 um 6° nach unten, main.gd) verschiebt Punkt und spätere Anfahrt gleich - «▶ Anfahren» zeigt die Karte wieder in
#     der Mitte. Die angezeigten Grad sind Servo-Grad, keine Höhenwinkel über dem Horizont.
#   * Töne (sound_play, Teil 250): erkannt = beep2, Punkt gespeichert = beep3, schon gespeichert = beep1, verloren (MK_LOST_S ohne
#     Karte, der Kopf bleibt stehen) und Sitzung zu Ende (MK_END_S) = beeplow. Schalter mk_beep.
#   * Lesen: eigener Faden mit tiefer Priorität (nice 10); ohne Sitzung 1× pro Sekunde das ganze Bild, in der Sitzung bis ~8×/s ein
#     Ausschnitt um die Karte (kleine Karte bis 3× vergrössert) und jedes 4. Bild das ganze Bild. Bild: frame_raw der Kopf-Kamera
#     über qrk_grab (Ausleihe raw_until). Pause: Werkzeug-Modus, Akku-Sparen, Kopf geparkt (Privatsphäre: die Kamera schaut weg -
#     mit dem Joystick bewegen beendet das Parken). Läuft auch in der Simulation (Test mit dem Requisit markierkarte.gd).
#   * OpenCV: ab 4.7 cv2.aruco.ArucoDetector, Raspberry Pi OS Bookworm (python3-opencv 4.6 mit contrib) detectMarkers; ohne aruco
#     (pip opencv-python-headless < 4.7) schaltet sich die Funktion ab und sagt warum (mk_state «no_aruco»).
# Reichweite (Kopf-Kamera 66°, 1280 × 720, A4 / Marker 180 mm, Simulator - nicht echte Kamera; sim_probe.py, 3 Läufe 16.11.2026):
# 7,2 m und 5,4 m 3 von 3 gemerkt (Fehler < 0,5°, Abstand ±5 %), 14,3 m 1 von 3 (richtig); Folgen bis etwa 10 m (darüber zeitweise verloren).
# Versprochen wird nur das: A4 folgt bis etwa 10 m, merkt sicher bis etwa 6 m, bei gutem Licht oft weiter; A5 etwa 0,7 × so weit.
# Werkzeuge: werkzeuge/markier_karte/ (Messung, synthetische Sequenz, Probe gegen den Simulator); Test werkzeuge/markier_karte_test.py.
# ----------------------------------------------------------------------------
MK_IDS = tuple(range(40, 50))
MK_SIZES = {"a4": (210, 297, 180, 42), "a5": (148, 210, 128, 34)}     # paper w, h, marker side, QR side (mm)
MK_RANGE = {"a4": (10, 6, 4), "a5": (7, 4, 3)}                         # m: follow by day, mark reliably, dusk (Sim, see the head)
MK_GAP_MIN, MK_GAP_MAX = 0.6, 3.0
MK_STILL_DEG = 0.8
MK_LOST_S, MK_END_S = 6.0, 90.0
MK_DEAD, MK_GAIN = 0.04, 0.6
MK_ARMED_LOG_S = 600.0
MK_SECTION = "Marker cards"
MK_DEF = {"mk_on": False, "mk_beep": True, "mk_cards": [], "mk_dist": {}}
for _k, _v in MK_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
    FACTORY_CFG.setdefault(_k, json.loads(json.dumps(_v)))
USER_SETTINGS_DENY.update(MK_DEF)
APPKEY_DENY_KEYS.update(MK_DEF)
APPKEY_DENY_PATHS.update({"/api/mk", "/karten/markier"})
LOCK_DENY_PATHS.add("/api/mk")
MK = {"lock": threading.RLock(), "thread": None, "det": None, "why": "", "ses": None, "last": None, "armed_log": 0.0, "ms": None,
      "n": 0, "pause": "off"}


# ---- the detector (OpenCV 4.6 contrib / >= 4.7 / none) ---------------------------------------------------------------------------
class MkDetector:
    def __init__(self):
        a = getattr(cv2, "aruco", None)
        self.ok, self.api, self.last, self.n = False, "", None, 0
        if a is None or not hasattr(a, "getPredefinedDictionary"):
            self.why = "no_aruco"
            return
        self.dic = a.getPredefinedDictionary(a.DICT_4X4_50)
        p = a.DetectorParameters() if hasattr(a, "ArucoDetector") else a.DetectorParameters_create()
        # minMarkerDistanceRate only for the old API (OpenCV 4.6, Pi OS Bookworm): it keeps the white edge of the paper (half a cell)
        # as the candidate and reads nothing. OpenCV 4.7+ reads fine without it, and with it the corners shrink and jitter (measured)
        for k, v in (("minMarkerPerimeterRate", 0.012), ("adaptiveThreshWinSizeMin", 3), ("adaptiveThreshWinSizeMax", 23),
                     ("adaptiveThreshWinSizeStep", 10), ("polygonalApproxAccuracyRate", 0.05), ("perspectiveRemovePixelPerCell", 8),
                     ("errorCorrectionRate", 0.6), ("minMarkerDistanceRate", None if hasattr(a, "ArucoDetector") else 0.01), ("cornerRefinementMethod", getattr(a, "CORNER_REFINE_SUBPIX", 1))):
            try:
                if v is not None:
                    setattr(p, k, v)
            except (AttributeError, TypeError, cv2.error):
                pass
        if hasattr(a, "ArucoDetector"):
            self._det = a.ArucoDetector(self.dic, p).detectMarkers
            self.api = "ArucoDetector"
        else:
            self._det = lambda g: a.detectMarkers(g, self.dic, parameters=p)
            self.api = "detectMarkers"
        self.ok, self.why = True, ""

    def image(self, mid, px):
        a = cv2.aruco
        return (a.generateImageMarker if hasattr(a, "generateImageMarker") else a.drawMarker)(self.dic, int(mid), int(px))

    def _find(self, g, ids, x0=0, y0=0, k=1.0):
        try:
            corners, found, _r = self._det(g)
        except cv2.error:
            return []
        if found is None:
            return []
        return [(int(i), c.reshape(4, 2) / k + np.float32([x0, y0])) for c, i in zip(corners, found.flatten()) if int(i) in ids]

    def detect(self, img, ids, track=False):
        """-> {id, pts (4×2 px), cx, cy (0..1), side (px), w, h} of the biggest own marker, or None"""
        g = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        H, W = g.shape[:2]
        self.n += 1
        found = []
        if track and self.last is not None:                     # a crop around the card, a small card enlarged
            cx, cy, side = self.last
            r = int(max(160, side * 2.5))
            x0, y0 = int(max(0, min(W - 2 * r, cx - r))), int(max(0, min(H - 2 * r, cy - r)))
            k = max(1.0, min(3.0, 60.0 / max(side, 1.0), 640.0 / (2 * r)))
            crop = g[y0:y0 + 2 * r, x0:x0 + 2 * r]
            found = self._find(cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC) if k > 1.0 else crop, ids, x0, y0, k)
        if not found and (not track or self.last is None or self.n % 4 == 0):
            found = self._find(g, ids)
        if not found:
            return None
        i, q = max(found, key=lambda f: cv2.contourArea(f[1]))
        side = float(max(np.linalg.norm(q[0] - q[3]), np.linalg.norm(q[1] - q[2])))     # vertical sides: not shortened by a turn
        c = q.mean(axis=0)
        self.last = (float(c[0]), float(c[1]), side)
        return {"id": i, "pts": q, "cx": float(c[0]) / W, "cy": float(c[1]) / H, "side": side, "w": W, "h": H}


def mk_detector():
    if MK["det"] is None:
        MK["det"] = MkDetector()
    return MK["det"]


# ---- the cards ---------------------------------------------------------------------------------------------------------------------
def mk_cards():
    return [c for c in CFG.get("mk_cards") or [] if isinstance(c, dict) and isinstance(c.get("id"), str) and c.get("mid") in MK_IDS]


def mk_card_by_mid(mid):
    return next((c for c in mk_cards() if c["mid"] == mid), None)


def mk_card(cid):
    return next((c for c in mk_cards() if c["id"] == cid), None)


def mk_qr_payload(card, key=None):
    """the small QR code: «MK» + id + check number over id and marker number (key of the QR cards, 639zzp)"""
    return "MK" + card["id"] + qrk_mac(card["id"], "K", str(card["mid"]), key)


def mk_qr_check(text):
    t = str(text or "")
    k = qrk_key(False)
    if not t.startswith("MK") or len(t) != 2 + QRK_ID_LEN + QRK_MAC_LEN or not k:
        return None
    c = mk_card(t[2:2 + QRK_ID_LEN])
    return c if c is not None and hmac.compare_digest(t, mk_qr_payload(c, k)) else None


def mk_create(name, size="a4", who="web"):
    used = {c["mid"] for c in mk_cards()}
    free = [m for m in MK_IDS if m not in used]
    if not free:
        return None, "at most 10 marker cards"
    name = re.sub(r"[\x00-\x1f<>\"]", "", str(name or "")).strip()[:QRK_NAME_MAX] or tr("Marker card")
    qrk_key(True)
    cid = "".join(secrets.choice(QRK_ALPHA) for _ in range(QRK_ID_LEN))
    c = {"id": cid, "mid": free[0], "name": name, "size": size if size in MK_SIZES else "a4", "t": int(time.time()), "used": 0, "n": 0}
    CFG["mk_cards"] = mk_cards() + [c]
    save_settings()
    log_event("sys", f"Marker card «{name}» made (marker {c['mid']}, {who})")
    return c, ""


def mk_delete(cid, who="web"):
    c = mk_card(cid)
    if c is None:
        return False, "unknown card"
    CFG["mk_cards"] = [x for x in mk_cards() if x["id"] != cid]
    if MK["ses"] and MK["ses"]["card"]["id"] == cid:
        mk_end("card deleted")
    save_settings()
    log_event("sys", f"Marker card «{c['name']}» deleted ({who})")
    return True, ""


def mk_range(size):
    return MK_RANGE.get(size, MK_RANGE["a4"])


def mk_card_svg(card, size=None, lang=None):
    """the whole card in mm: marker on top, QR + name + how-to below"""
    L = norm_lang(lang)
    size = size if size in MK_SIZES else card.get("size", "a4")
    W, H, MS, QS = MK_SIZES[size]
    k = W / 210.0
    det = mk_detector()
    b = det.image(card["mid"], 6) > 127 if det.ok else np.ones((6, 6), bool)
    x0, y0, cell = (W - MS) / 2.0, 12 * k, MS / 6.0
    path = "".join(f"M{x0 + c * cell:.2f},{y0 + r * cell:.2f}h{cell:.2f}v{cell:.2f}h{-cell:.2f}z" for r in range(6) for c in range(6) if not b[r, c])
    M = qr_matrix(mk_qr_payload(card))
    n = len(M)
    qy = y0 + MS + 9 * k
    qp = "".join(f"M{x},{y}h1v1h-1z" for y in range(n) for x in range(n) if M[y][x])
    fol, mark, _d = mk_range(size)
    rows = [(6, "📍 " + tr("Marker card", L), 7.2, 700), (13, f"MoveEye «{CFG.get('device_name') or 'MoveEye'}» · «{card['name']}»", 3.9, 400),
            (20, trf("Follows up to about {a} m, marks reliably up to about {b} m", L, a=fol, b=mark), 3.4, 700)]
    rows += [(27 + 5.5 * i, x, 3.4, 400) for i, x in enumerate(("1  " + tr("Hold the card in front of MoveEye – it beeps.", L),
             "2  " + tr("Walk away – the head looks along.", L), "3  " + tr("Mark a point: stand still, turn the card for 1–2 s,", L),
             "    " + tr("show it again – a second sound.", L)))]
    txt = "".join(f'<text x="{x0 + QS + 7 * k:.1f}" y="{qy + y * k:.1f}" font-size="{fs * k:.2f}" font-weight="{w}">{html_escape(x)}</text>'
                  for y, x, fs, w in rows)
    foot = html_escape(f"📍 MoveEye · {tr('Marker card', L)} · {card['mid']} · {card['id']} · {size.upper()}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}"><style>text{{font-family:DejaVu Sans,'
            f'Helvetica,Arial,sans-serif;fill:#222}}</style><rect width="{W}" height="{H}" fill="#fff"/><path d="{path}" shape-rendering="crispEdges"/>'
            f'<g transform="translate({x0:.2f},{qy:.2f}) scale({QS / n:.5f})"><path d="{qp}" shape-rendering="crispEdges"/></g>{txt}'
            f'<text x="{W / 2}" y="{H - 7 * k:.1f}" font-size="{2.9 * k:.2f}" text-anchor="middle" style="fill:#777">{foot}</text></svg>')


def mk_print_page(card, size=None, lang=None):
    L = norm_lang(lang)
    size = size if size in MK_SIZES else card.get("size", "a4")
    h = MK_PRINT_HTML
    for k_, v_ in (("{LANG}", L), ("{TITLE}", html_escape(tr("Marker card", L) + " – " + card["name"])), ("{PRINT}", html_escape(tr("Print", L))),
                   ("{CLOSE}", html_escape(tr("Close", L))), ("{ID}", card["id"]), ("{SIZE}", size),
                   ("{NOTE}", html_escape(trf("Print at 100 %, matt paper. Up to about {a} m by day ({s}). Only for this MoveEye.", L,
                                              a=mk_range(size)[0], s=size.upper()))), ("{CARD}", mk_card_svg(card, size, L))):
        h = h.replace(k_, v_)
    return h


# ---- the session ------------------------------------------------------------------------------------------------------------------
def mk_beep(kind):
    if not CFG.get("mk_beep", True):
        return
    k, s = {"found": ("beep2", 0.4), "mark": ("beep3", 0.6), "same": ("beep1", 0.2), "lost": ("beeplow", 0.2), "end": ("beeplow", 0.2)}[kind]
    try:
        sound_play(k, s, CFG.get("clap_volume", 60), reason="marker card")
    except Exception:
        pass


def mk_active():
    """a session holds the head (follows or waits for the card to come back)"""
    s = MK["ses"]
    return bool(s) and s["state"] in ("follow", "lost")


def mk_end(why="", beep=True):
    s = MK["ses"]
    if not s:
        return
    MK["ses"] = None
    if mk_detector().ok:
        mk_detector().last = None
    log_event("servo", f"Marker card «{s['card']['name']}»: session ended ({why}) - {s['marks']} points")
    if beep:
        mk_beep("end")


def mk_card_dir(obs):
    """(pan %, tilt %) where the head must look to have the card in the middle - see the head: assumption tilt"""
    return kopf_pic_to_pan(obs["cx"], obs["cy"])


def mk_point_name():
    base = tr("Point")
    names = {wp_name(w) for w in WAYPOINTS}
    n = 1
    while f"{base} {n}" in names:
        n += 1
    return f"{base} {n}"


def mk_step(t, obs, now_img_w=1280):
    """one picture of the session state machine; obs = detection or None. Returns the head target (pan %, tilt %) or None"""
    s = MK["ses"]
    hist = s["hist"]
    d = mk_card_dir(obs) if obs else None
    hist.append((t, obs is not None, d))
    while hist and t - hist[0][0] > 4.0:
        hist.pop(0)
    ppd_p, ppd_t = kopf_pct_per_deg("pan"), kopf_pct_per_deg("tilt")
    if obs is None:
        if s["gap"] is None and s["seen"]:
            s["gap"] = s["seen"]
        if s["state"] == "follow" and s["gap"] is not None and t - s["gap"] > MK_LOST_S:
            s["state"] = "lost"
            mk_beep("lost")
            log_event("servo", f"Marker card «{s['card']['name']}» lost - the head stays")
        if s["seen"] and t - s["seen"] > MK_END_S:
            mk_end("not seen for 90 s")
        return None
    if s["gap"] is not None:
        gap = t - s["gap"]
        if s["state"] == "lost":
            s["state"] = "follow"
            mk_beep("found")
        elif MK_GAP_MIN <= gap <= MK_GAP_MAX:
            before = [h for h in hist if s["gap"] - 1.0 <= h[0] <= s["gap"]]
            dirs = [h[2] for h in hist if h[1] and s["gap"] - 0.8 <= h[0] <= s["gap"]]
            still = len(dirs) >= 3 and (max(x[0] for x in dirs) - min(x[0] for x in dirs)) <= 2 * MK_STILL_DEG * ppd_p \
                and (max(x[1] for x in dirs) - min(x[1] for x in dirs)) <= 2 * MK_STILL_DEG * ppd_t
            if len(before) >= 4 and sum(1 for h in before if h[1]) / len(before) >= 0.8 and still:
                s["pending"] = {"t": t, "gap": round(gap, 2),
                                "before": (sum(x[0] for x in dirs[-4:]) / len(dirs[-4:]), sum(x[1] for x in dirs[-4:]) / len(dirs[-4:]))}
            else:
                s["note"] = "not still"
        s["gap"] = None
    s["seen"] = t
    s["side"] = obs["side"]
    tgt = None
    ex, ey = obs["cx"] - 0.5, obs["cy"] - 0.5
    if t >= s["settle"] and (abs(ex) > MK_DEAD or abs(ey) > MK_DEAD):
        p0, q0 = servo_pos()
        tgt = (p0 + (d[0] - p0) * MK_GAIN, q0 + (d[1] - q0) * MK_GAIN)
        s["settle"] = t + 0.15
    p = s["pending"]
    if p is not None:
        after = [h for h in hist if h[0] >= p["t"]]
        if len(after) >= 3 and all(h[1] for h in after):
            s["pending"] = None
            pm = (sum(h[2][0] for h in after) / len(after), sum(h[2][1] for h in after) / len(after))
            if abs(pm[0] - p["before"][0]) <= 1.5 * ppd_p and abs(pm[1] - p["before"][1]) <= 1.5 * ppd_t and t - s["mark_t"] >= 3.0:
                mk_mark(t, obs, ((pm[0] + p["before"][0]) / 2, (pm[1] + p["before"][1]) / 2), now_img_w)
    return tgt


def mk_dist(obs, card):
    hf, _vf = cam_fov()
    f = (obs["w"] / 2.0) / math.tan(math.radians(hf) / 2.0)
    return round(f * MK_SIZES.get(card.get("size", "a4"), MK_SIZES["a4"])[2] / 1000.0 / max(obs["side"], 1.0), 1)


def mk_mark(t, obs, pos, img_w=1280):
    """save the place of the card as a taught point «Punkt n» (in the round) with its distance"""
    s = MK["ses"]
    card = s["card"]
    for w in WAYPOINTS:
        if abs(float(w[0]) - pos[0]) < kopf_pct_per_deg("pan") and abs(float(w[1]) - pos[1]) < kopf_pct_per_deg("tilt"):
            mk_beep("same")
            s["note"] = "same point"
            return None
    dist = mk_dist(obs, card)
    nm = mk_point_name()
    ok, err, i = teach_add(nm, "marker card", pos[0], pos[1], True)
    if not ok:
        s["note"] = err
        log_event("servo", f"Marker card: point not saved ({err})")
        return None
    CFG.setdefault("mk_dist", {})[nm] = dist
    s["mark_t"] = t
    s["marks"] += 1
    s["last_mark"] = {"name": nm, "dist": dist, "t": time.time()}
    for c in CFG["mk_cards"]:
        if c.get("id") == card["id"]:
            c["n"] = int(c.get("n") or 0) + 1
    save_settings()
    mk_beep("mark")
    log_event("servo", f"Marker card: «{nm}» saved (pan {pos[0]:.1f} % / tilt {pos[1]:.1f} %, about {dist} m)")
    return nm


def mk_pause_reason():
    if not CFG.get("mk_on"):
        return "off"
    if not mk_detector().ok:
        return "OpenCV without ArUco"
    if not mk_cards():
        return "no cards yet"
    try:
        if toolmode_on():
            return "tool mode"
    except NameError:
        pass
    try:
        if batt_save_active():
            return "battery saver"
    except NameError:
        pass
    if CFG.get("kopf_parked") and CFG.get("kopf_park") and CFG.get("kopf_on"):
        return "the head is parked"
    return ""


def mk_armed():
    return bool(CFG.get("armed")) or walktest_on()


def mk_tick(img=None, t=None):
    """one round of the thread (img / t for the self-test) -> seconds until the next round"""
    why = mk_pause_reason()
    MK["pause"] = why
    if why:
        if MK["ses"]:
            mk_end(why, beep=False)
        return 2.0 if why != "OpenCV without ArUco" else 30.0
    if img is None:
        img, _src = qrk_grab("head")
        if img is None:
            return 0.5
    t = time.time() if t is None else t
    det = mk_detector()
    ids = {c["mid"] for c in mk_cards()}
    t0 = time.time()
    obs = det.detect(img, ids, track=bool(MK["ses"]))
    MK["ms"] = round((time.time() - t0) * 1000.0, 1)
    MK["n"] += 1
    if obs is not None:
        P = [[round(float(x) / obs["w"], 4), round(float(y) / obs["h"], 4)] for x, y in obs["pts"]]
    if mk_armed():
        if MK["ses"]:
            mk_end("protection on", beep=False)
        if obs is not None:
            qrk_show("head", P, "off", "📍 " + tr("Marker card only when the protection is off"))
            if t - MK["armed_log"] >= MK_ARMED_LOG_S:
                MK["armed_log"] = t
                log_event("sys", "Marker card ignored: only when the protection is off")
        return 1.0
    card = mk_card_by_mid(obs["id"]) if obs else None
    if MK["ses"] is None:
        if card is None:
            det.last = None
            return 1.0
        MK["ses"] = {"card": card, "state": "follow", "t0": t, "seen": None, "gap": None, "hist": [], "pending": None, "settle": 0.0,
                     "mark_t": -99.0, "marks": 0, "side": 0.0, "note": "", "last_mark": None, "qr": False}
        for c in CFG["mk_cards"]:
            if c.get("id") == card["id"]:
                c["used"] = int(time.time())
        mk_beep("found")
        log_event("servo", f"Marker card «{card['name']}» seen - the head follows (patrol / following of persons paused)")
    s = MK["ses"]
    if obs is not None and obs["id"] != s["card"]["mid"]:
        obs = None                                              # another card of this device in the picture: the first one counts
    tgt = mk_step(t, obs, img.shape[1])
    if MK["ses"] is None:
        return 1.0
    if obs is not None:
        lm = s.get("last_mark")
        lab = f"📍 {s['card']['name']} · ~{mk_dist(obs, s['card'])} m"
        if lm and time.time() - lm["t"] < 4.0:
            lab = "📍 ✓ " + lm["name"] + f" (~{lm['dist']} m)"
        qrk_show("head", P, "ok", lab)
        if not s["qr"] and obs["side"] > 0.3 * obs["h"]:           # close: the small QR code (optional)
            txt, _p = qrk_decode(img)
            if txt and mk_qr_check(txt) is not None:
                s["qr"] = True
                log_event("servo", f"Marker card «{s['card']['name']}»: QR code confirmed")
    if tgt is not None and kopf_may("marker") and not servo_blocked() and not manual_active():
        CFG["pan"] = max(0.0, min(100.0, tgt[0]))
        CFG["tilt"] = max(0.0, min(100.0, tgt[1]))
    return 0.12


def mk_loop():
    try:
        os.setpriority(os.PRIO_PROCESS, threading.get_native_id(), 10)
    except (AttributeError, OSError):
        pass
    err_t = 0.0
    while True:
        try:
            gap = mk_tick()
        except Exception as e:
            gap = 3.0
            if time.time() - err_t > 300:
                err_t = time.time()
                log_event("sys", f"Marker card: {type(e).__name__}: {e}"[:160])
        time.sleep(gap)


def mk_start():
    if MK["thread"] is None:
        with MK["lock"]:
            if MK["thread"] is None:
                MK["thread"] = threading.Thread(target=mk_loop, daemon=True, name="marker-card")
                MK["thread"].start()


def mk_state(lang=None):
    L = norm_lang(lang)
    s = MK["ses"]
    why = MK["pause"] if CFG.get("mk_on") else "off"
    det = mk_detector()
    return {"on": bool(CFG.get("mk_on")), "pause": why, "pause_t": tr(why, L) if why else "", "api": det.api, "aruco": det.ok,
            "ms": MK["ms"], "armed": mk_armed(), "ids": [MK_IDS[0], MK_IDS[-1]],
            "ses": {"card": s["card"]["name"], "state": s["state"], "marks": s["marks"], "since": int(time.time() - s["t0"]),
                    "qr": s["qr"], "last": s["last_mark"]} if s else None}


def mk_card_json(c, lang=None):
    r = mk_range(c.get("size", "a4"))
    return dict(c, range=r[0], mark=r[1], made=datetime.fromtimestamp(c["t"]).strftime("%d.%m.%Y"),
                last=datetime.fromtimestamp(c["used"]).strftime("%d.%m. %H:%M") if c.get("used") else "")


# ---- the head: own mover «marker» after «alarm»; following of persons pauses during a session ---------------------------------
KOPF_PRIO = ("manual", "alarm", "marker", "walktest", "glance", "round", "park")
_kopf_claims_mk = kopf_claims


# wraps: kopf_claims
def kopf_claims():                                           # + 639zzzzm: the marker card holds the head
    c = _kopf_claims_mk()
    if mk_active():
        if "alarm" in c and not (KOPF["alarm"] or KOPF["tamper"] or KOPF["back"]):
            c.discard("alarm")                               # only «following a person» (paused, decision 3)
        c.add("marker")
    return c


_kopf_track_blocked_mk = kopf_track_blocked


# wraps: kopf_track_blocked
def kopf_track_blocked():                                    # + 639zzzzm: no following of the person with the card
    return mk_active() or _kopf_track_blocked_mk()


# ---- taught points: the distance travels with the name ------------------------------------------------------------------------------
_teach_list_mk = teach_list


# wraps: teach_list
def teach_list(lang=None):                                   # + 639zzzzm: «📍 ~7.4 m» for points of a marker card
    out = _teach_list_mk(lang)
    dd = CFG.get("mk_dist") or {}
    for p in out:
        if p["name"] and p["name"] in dd:
            p["mk_m"] = dd[p["name"]]
    return out


_teach_edit_mk = teach_edit


# wraps: teach_edit
def teach_edit(op, i, value=None, who="web"):                # + 639zzzzm: rename / delete carry the distance
    old = wp_name(WAYPOINTS[int(i)]) if str(i).lstrip("-").isdigit() and 0 <= int(i) < len(WAYPOINTS) else ""
    r = _teach_edit_mk(op, i, value, who)
    dd = CFG.get("mk_dist") or {}
    if r[0] and old in dd:
        names = {wp_name(w) for w in WAYPOINTS}
        if old not in names:
            m = dd.pop(old)
            new = wp_name(WAYPOINTS[int(i)]) if op in ("rename", "patrol", "park", "home") and int(i) < len(WAYPOINTS) else ""
            if new:
                dd[new] = m
            save_settings()
    return r


SERVO_PAGE = SERVO_PAGE.replace('(p.home ? " · 🏠 " + t("home") : "")', '(p.home ? " · 🏠 " + t("home") : "") + (p.mk_m ? " · 📍 ~" + p.mk_m + " m" : "")', 1)

# ---- the QR cards: the small code of a marker card is no «foreign card» --------------------------------------------------------------
_qrk_seen_mk = qrk_seen


# wraps: qrk_seen
def qrk_seen(cam, text, pts, img, src=None, now=None):        # + 639zzzzm: «MK…» = the QR code of an own marker card
    c = mk_qr_check(text)
    if c is not None:
        if MK["ses"] and MK["ses"]["card"]["id"] == c["id"]:
            MK["ses"]["qr"] = True
        qrk_show(cam, pts, "ok", "📍 " + c["name"], src)
        return "marker"
    return _qrk_seen_mk(cam, text, pts, img, src, now)


# ---- the live picture: start the thread with the first picture (the frame itself is drawn by qrk_draw, 639zzp) ---------------------
_walktest_draw_mk = walktest_draw


# wraps: walktest_draw
def walktest_draw(frame):                                    # + 639zzzzm: start the marker thread
    _walktest_draw_mk(frame)
    if MK["thread"] is None:
        mk_start()


# ---- the web: workshop section, API, print page -------------------------------------------------------------------------------------
_smalltv_routes_mk = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                        # + 639zzzzm: /api/mk, card pictures, print page (administrator)
    _smalltv_routes_mk(app, reply, body)
    from flask import Response, request, g
    mk_start()

    def nope():
        if not qrk_admin_ok(g):
            return reply({"ok": False, "error": tr("Only for the administrator", norm_lang(request.args.get("lang")))}, 403)
        return None

    @app.route("/api/mk", methods=["GET", "POST"])
    def api_mk():
        n = nope()
        if n is not None:
            return n
        if request.method == "GET":
            L = norm_lang(request.args.get("lang") or CFG.get("lang"))
            return reply({"ok": True, "state": mk_state(L), "cards": [mk_card_json(c, L) for c in mk_cards()]})
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        a = str(d.get("action") or "")
        if a == "create":
            c, err = mk_create(d.get("name"), str(d.get("size") or "a4"), "web")
            return reply({"ok": c is not None, "card": mk_card_json(c, L) if c else None, "error": tr_err(err, L) if err else None}, 200 if c else 400)
        if a == "delete":
            ok, err = mk_delete(str(d.get("id") or ""), "web")
            return reply({"ok": ok, "error": tr_err(err, L) if err else None}, 200 if ok else 400)
        if a == "end":
            mk_end("ended on the web page")
            return reply({"ok": True})
        return reply({"ok": False, "error": "unknown action"}, 400)

    @app.route("/karten/markier")
    def mk_print():
        n = nope()
        if n is not None:
            return n
        c = mk_card(str(request.args.get("id") or ""))
        if c is None:
            return Response("not found", 404)
        a_, L = request.args, request.args.get("lang") or CFG.get("lang")
        if a_.get("svg") == "1":                              # «⬇ SVG»: the card alone
            return Response(mk_card_svg(c, a_.get("size"), L), mimetype="image/svg+xml", headers={"Cache-Control": "no-store",
                            "Content-Disposition": f'attachment; filename="moveeye_markier_{c["mid"]}_{c["id"]}.svg"'})
        return Response(mk_print_page(c, a_.get("size"), L), mimetype="text/html", headers={"Cache-Control": "no-store"})


MK_PRINT_HTML = r"""<!doctype html><html lang="{LANG}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><title>MoveEye – {TITLE}</title><style>
@page{size:A4 portrait;margin:8mm}html,body{background:#fff;color:#111}
body{font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;padding:12px 16px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 10px}
.bar button,.bar a{font:inherit;padding:8px 12px;border-radius:8px;border:1px solid #999;background:#f4f4f4;color:#111;cursor:pointer;text-decoration:none;min-height:40px;box-sizing:border-box;display:inline-flex;align-items:center}
.bar a.on{background:#1f6feb;border-color:#1f6feb;color:#fff}.m{color:#555;margin:0 0 10px;font-size:13px}
.cv{display:flex;justify-content:center}.cv svg{max-width:100%;height:auto;box-shadow:0 1px 6px rgba(0,0,0,.25)}
@media print{.bar,.m{display:none}body{padding:0}.cv svg{box-shadow:none;max-width:none}}
</style></head><body><div class="bar"><button type="button" onclick="print()">🖨 {PRINT}</button><a href="?id={ID}&amp;size=a4">A4</a><a href="?id={ID}&amp;size=a5">A5</a>
<a href="?id={ID}&amp;size={SIZE}&amp;svg=1">⬇ SVG</a>
<button type="button" onclick="history.length>1?history.back():close()">{CLOSE}</button></div><div class="m">{NOTE}</div>
<div class="cv">{CARD}</div><script>window.__mwExit = true;
document.querySelectorAll(".bar a").forEach(a => { if (a.search.indexOf("size={SIZE}") > 0 && a.search.indexOf("svg") < 0) a.className = "on"; });</script></body></html>"""

MK_WORKSHOP_JS = r"""<script>
(function () {                                            // 639zzzzm: «📍 Markier-Karten» in the card workshop
  const $i = id => document.getElementById(id);
  // texts only this section uses (en key: de, fr, it, rm) - the rest comes from the table of the part (I18N.de / TRX)
  const MT = {
    "intro": ["Ein grosser Marker, den MoveEye von weit her sieht: es piepst, der Kopf folgt der Karte. Stehen bleiben, Karte 1–2 s umdrehen und wieder zeigen = die Stelle wird als «Punkt 1», «Punkt 2» … im Teach-in gespeichert (in der Runde). Nur bei Schutz Aus.",
      "Un grand repère que MoveEye voit de loin : il bipe, la tête suit la carte. S’arrêter, retourner la carte 1–2 s et la remontrer = l’endroit est enregistré comme «Point 1», «Point 2» … dans le teach-in (dans la ronde). Seulement si la protection est arrêtée.",
      "Un grande marcatore che MoveEye vede da lontano: emette un bip, la testa segue la carta. Fermarsi, girare la carta per 1–2 s e mostrarla di nuovo = il posto viene salvato come «Punto 1», «Punto 2» … nel teach-in (nel giro). Solo con protezione spenta.",
      "In grond marcader che MoveEye vesa da lunsch: el pipa, il chau suonda la carta. Star airi, volver la carta 1–2 s e la mussar puspè = il lieu vegn memorisà sco «Punct 1», «Punct 2» … en il teach-in (en la runda). Mo cun protecziun deactivada.",
      "A big marker that MoveEye sees from far away: it beeps, the head follows the card. Stand still, turn the card for 1–2 s and show it again = the place is saved as «Point 1», «Point 2» … in the teach-in (in the round). Only when the protection is off."],
    "Size": ["Grösse", "Taille", "Dimensione", "Grondezza"],
    "Follows the card": ["Folgt der Karte", "Suit la carte", "Segue la carta", "Suonda la carta"],
    "points": ["Punkte", "points", "punti", "puncts"],
    "Marker numbers": ["Marker-Nummern", "Numéros de repère", "Numeri del marcatore", "Numers dal marcader"],
    "only this MoveEye": ["nur dieses MoveEye", "seulement ce MoveEye", "solo questo MoveEye", "mo quest MoveEye"],
    "follows up to about": ["folgt bis etwa", "suit jusqu’à env.", "segue fino a circa", "suonda fin circa"],
    "marks reliably up to about": ["merkt sicher bis etwa", "marque sûrement jusqu’à env.", "segna con sicurezza fino a circa", "marca segir fin circa"],
    "made": ["erstellt", "créée", "creata", "creada"],
    "last used": ["zuletzt", "dernière utilisation", "ultimo uso", "l’ultima giada"],
    "End": ["Beenden", "Terminer", "Terminare", "Terminar"],
    "Delete this card?": ["Diese Karte löschen?", "Supprimer cette carte ?", "Eliminare questa carta?", "Stizzar questa carta?"]};
  const mt = k => { const i = {de: 0, fr: 1, it: 2, rm: 3}[L()]; const v = MT[k]; return v ? (i == null ? (v[4] || k) : v[i]) : t(k); };
  const anchor = document.querySelector('#qk-list') && document.querySelector('#qk-list').closest("section");
  if (!anchor || $i("mk-sec")) return;
  const sec = document.createElement("section"); sec.className = "card"; sec.id = "mk-sec";
  sec.innerHTML = '<h3 style="margin:0 0 6px" id="mk-t"></h3><div class="mut" id="mk-intro" style="margin:0 0 8px"></div><div class="qk-st" id="mk-st">…</div>'
    + '<div class="qk-f"><label><span id="mk-l-name"></span><input type="text" id="mk-name" maxlength="40" autocomplete="off"></label>'
    + '<label><span id="mk-l-size"></span><select id="mk-size"><option value="a4">A4</option><option value="a5">A5</option></select></label>'
    + '<div class="qk-row"><button type="button" id="mk-go"></button></div><div class="qk-hint bad" id="mk-err"></div></div><div class="qk-list" id="mk-list" style="margin-top:10px"></div>';
  anchor.parentNode.insertBefore(sec, anchor);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const api = async (b) => { try { const r = await fetch("/api/mk", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, b || {}))});
    return await r.json(); } catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  $i("mk-t").textContent = "📍 " + t("Marker cards"); $i("mk-l-name").textContent = t("Name on the card"); $i("mk-l-size").textContent = mt("Size");
  $i("mk-go").textContent = "📍 " + t("Make the card");
  $i("mk-intro").textContent = mt("intro");
  let J = null;
  async function load() {
    try { J = await (await fetch("/api/mk?lang=" + encodeURIComponent(L()), {cache: "no-store"})).json(); } catch (e) { J = null; }
    if (!J || !J.ok) { $i("mk-sec").hidden = true; return; }
    const s = J.state, b = $i("mk-st"); b.textContent = ""; b.classList.toggle("on", s.on && !s.pause);
    const lab = E("label", "qk-sw"), cb = E("input"); cb.type = "checkbox"; cb.checked = !!s.on;
    cb.onchange = async () => { cb.disabled = true; try { await fetch("/api/set", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({key: "mk_on", value: cb.checked})}); } catch (e) {} cb.disabled = false; load(); };
    lab.append(cb, E("span", "", t("Marker cards (experimental)"))); b.appendChild(lab);
    let st = !s.aruco ? "⚠ " + t("OpenCV without ArUco") : !s.on ? t("Off – nothing is read.") : s.ses ? "▶ " + mt("Follows the card") + " «" + s.ses.card + "» · " + s.ses.marks + " " + mt("points")
      : s.pause ? "⏸ " + t("Pause") + ": " + s.pause_t : s.armed ? "⏸ " + t("Marker card only when the protection is off") : "▶ " + t("Looking for cards");
    b.appendChild(E("b", "", st));
    b.appendChild(E("div", "mut", mt("Marker numbers") + " " + s.ids[0] + "–" + s.ids[1] + " · " + mt("only this MoveEye") + (s.api ? " · " + s.api + (s.ms != null ? " (" + Math.round(s.ms) + " ms)" : "") : "")));
    if (s.ses) { const x = E("button", "sec", "⏹ " + mt("End")); x.type = "button"; x.onclick = async () => { await api({action: "end"}); load(); }; b.appendChild(x); }
    const box = $i("mk-list"); box.textContent = "";
    J.cards.forEach(c => {
      const r = E("div", "qk-c"), pv = E("div", "pv"), im = E("img"); im.src = "/karten/markier?svg=1&id=" + c.id + "&lang=" + L(); im.alt = ""; pv.appendChild(im);
      const m = E("div"); m.append(E("b", "", c.name)); const tg = E("span", "qk-tag", "📍 " + c.mid); m.appendChild(tg);
      m.appendChild(E("div", "w", c.size.toUpperCase() + " · " + mt("follows up to about") + " " + c.range + " m · " + mt("marks reliably up to about") + " " + c.mark + " m"));
      m.appendChild(E("div", "mut", mt("made") + " " + c.made + (c.last ? " · " + mt("last used") + " " + c.last : "") + " · " + (c.n || 0) + " " + mt("points")));
      const bb = E("div", "bb");
      const a = E("a", "btn sec", "🖨 " + t("Print")); a.href = "/karten/markier?id=" + c.id + "&lang=" + L(); bb.appendChild(a);
      const p = E("a", "btn sec", "⬇ SVG"); p.href = "/karten/markier?svg=1&id=" + c.id + "&lang=" + L(); bb.appendChild(p);
      const d = E("button", "sec", "🗑"); d.type = "button"; d.onclick = async () => { if (confirm(mt("Delete this card?"))) { await api({action: "delete", id: c.id}); load(); } };
      bb.appendChild(d); m.appendChild(bb); r.append(pv, m); box.appendChild(r);
    });
  }
  $i("mk-go").onclick = async () => {
    $i("mk-err").textContent = "";
    const j = await api({action: "create", name: $i("mk-name").value, size: $i("mk-size").value});
    if (!j.ok) { $i("mk-err").textContent = j.error || "?"; return; }
    $i("mk-name").value = ""; load(); window.open("/karten/markier?id=" + j.card.id + "&lang=" + L(), "_blank");
  };
  load(); setInterval(() => { if (!document.hidden) load(); }, 6000);
})();
</script>"""

if "639zzzzm" not in QRK_PAGE:
    QRK_PAGE = QRK_PAGE.replace("</body>", MK_WORKSHOP_JS + "</body>", 1)

# ---- the settings: Einstellungen → Kameras & Kopf → «Markier-Karten» ----------------------------------------------------------------
TOGGLES.extend([(MK_SECTION, "mk_on", "Marker cards (experimental)"), (MK_SECTION, "mk_beep", "Beep when the card is seen, a point is saved, the card is lost")])
SECTIONS.append(MK_SECTION)
SIMPLE_SECTIONS.add(MK_SECTION)
SIMPLE_KEYS.add("mk_on")
MENU_TITLES.setdefault(MK_SECTION, "Marker cards")
TK_SUB_ICONS[MK_SECTION] = "📍"
for _g in TK_GROUPS:
    if _g[0] == "camera" and MK_SECTION not in _g[2]:
        _g[2].append(MK_SECTION)
SET_HELP.update({"mk_on": ("Card workshop → «📍 Marker cards»: hold the card in front of the head camera (protection off) - the head follows; "
                           "turn it for 1–2 s = a taught point.", "off (experimental)")})
_MK_GRP = '{sec: "QR command cards", title: "QR command cards", ic: "▦"}'
if _MK_GRP in WEB_PAGE and '{sec: "Marker cards"' not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_MK_GRP, _MK_GRP + ', {sec: "Marker cards", title: "Marker cards", ic: "📍"}', 1)

# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_MK = {
    "Marker card": ("Markier-Karte", "Carte de repérage", "Carta di marcatura", "Carta da marcar"),
    "Marker cards": ("Markier-Karten", "Cartes de repérage", "Carte di marcatura", "Cartas da marcar"),
    "Marker cards (experimental)": ("Markier-Karten (experimentell)", "Cartes de repérage (expérimental)", "Carte di marcatura (sperimentale)",
                                    "Cartas da marcar (experimental)"),
    "Beep when the card is seen, a point is saved, the card is lost": (
        "Piepsen, wenn die Karte erkannt, ein Punkt gespeichert oder die Karte verloren ist",
        "Bip quand la carte est vue, un point enregistré ou la carte perdue",
        "Bip quando la carta è vista, un punto salvato o la carta persa",
        "Pip, cura che la carta vegn vesida, in punct memorisà u la carta persa"),
    "Marker card only when the protection is off": ("Markier-Karte nur bei Schutz Aus", "Carte de repérage seulement si la protection est arrêtée",
                                                    "Carta di marcatura solo con protezione spenta", "Carta da marcar mo cun protecziun deactivada"),
    "Marker card ignored: only when the protection is off": ("Markier-Karte ignoriert: nur bei Schutz Aus",
                                                             "Carte de repérage ignorée : seulement si la protection est arrêtée",
                                                             "Carta di marcatura ignorata: solo con protezione spenta",
                                                             "Carta da marcar ignorada: mo cun protecziun deactivada"),
    "Hold the card in front of MoveEye – it beeps.": ("Karte vor MoveEye halten – es piepst.", "Tenir la carte devant MoveEye – il bipe.",
                                                      "Tenere la carta davanti a MoveEye – emette un bip.", "Tegnair la carta davant MoveEye – el pipa."),
    "Walk away – the head looks along.": ("Weggehen – der Kopf schaut mit.", "S’éloigner – la tête suit.", "Allontanarsi – la testa segue.",
                                          "Ir davent – il chau guarda cun."),
    "Mark a point: stand still, turn the card for 1–2 s,": ("Punkt merken: stehen bleiben, Karte 1–2 s umdrehen,",
                                                            "Marquer un point : s’arrêter, retourner la carte 1–2 s,",
                                                            "Segnare un punto: fermarsi, girare la carta per 1–2 s,",
                                                            "Marcar in punct: star airi, volver la carta 1–2 s,"),
    "show it again – a second sound.": ("wieder zeigen – zweiter Ton.", "la remontrer – deuxième son.", "mostrarla di nuovo – secondo suono.",
                                        "la mussar puspè – segund tun."),
    "Follows up to about {a} m, marks reliably up to about {b} m": ("Folgt bis ca. {a} m, merkt Punkte sicher bis ca. {b} m",
                                                                    "Suit jusqu’à env. {a} m, marque sûrement jusqu’à env. {b} m",
                                                                    "Segue fino a circa {a} m, segna con sicurezza fino a circa {b} m",
                                                                    "Suonda fin circa {a} m, marca segir fin circa {b} m"),
    "Print at 100 %, matt paper. Up to about {a} m by day ({s}). Only for this MoveEye.": (
        "Mit 100 % auf mattes Papier drucken. Bei Tag bis etwa {a} m ({s}). Gilt nur für dieses MoveEye.",
        "Imprimer à 100 %, papier mat. De jour jusqu’à env. {a} m ({s}). Seulement pour ce MoveEye.",
        "Stampare al 100 %, carta opaca. Di giorno fino a circa {a} m ({s}). Solo per questo MoveEye.",
        "Stampar cun 100 %, palpiri mat. Da di fin circa {a} m ({s}). Mo per quest MoveEye."),
    "Card workshop → «📍 Marker cards»: hold the card in front of the head camera (protection off) - the head follows; turn it for 1–2 s = a taught point.": (
        "Karten-Werkstatt → «📍 Markier-Karten»: Karte vor die Kopf-Kamera halten (Schutz Aus) – der Kopf folgt; 1–2 s umdrehen = Teach-in-Punkt.",
        "Atelier des cartes → «📍 Cartes de repérage» : tenir la carte devant la caméra de la tête (protection arrêtée) – la tête suit ; la retourner 1–2 s = un point.",
        "Laboratorio delle carte → «📍 Carte di marcatura»: tenere la carta davanti alla telecamera della testa (protezione spenta) – la testa segue; girarla 1–2 s = un punto.",
        "Ufficina da cartas → «📍 Cartas da marcar»: tegnair la carta davant la camera dal chau (protecziun deactivada) – il chau suonda; volver 1–2 s = in punct."),
    "OpenCV without ArUco": ("OpenCV ohne ArUco", "OpenCV sans ArUco", "OpenCV senza ArUco", "OpenCV senza ArUco"),
    "the head is parked": ("der Kopf ist geparkt", "la tête est parquée", "la testa è parcheggiata", "il chau è parcà"),
    "at most 10 marker cards": ("höchstens 10 Markier-Karten", "au plus 10 cartes de repérage", "al massimo 10 carte di marcatura",
                                "maximalmain 10 cartas da marcar"),
}
for _k, _v in _HX_MK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_QRK_DE.update({_k: DE.get(_k, _v[0]) for _k, _v in _HX_MK.items()})
_QRK_DE.update({k: DE.get(k, k) for k in ("Print", "Pause", "Looking for cards", "Off – nothing is read.", "Name on the card", "Make the card")})

# ---- the manual -----------------------------------------------------------------------------------------------------------------------
_HELP_MK = {
    "de": ('<section id="markierkarte" data-icon="📍"><h2>Markier-Karte (experimentell)</h2><ul>'
           '<li><b>Was:</b> eine gedruckte Karte mit einem grossen Marker (und einem kleinen QR-Code). MoveEye erkennt sie von weit her, piepst und folgt ihr mit dem Kopf. '
           'So gehst du über den Platz und speicherst unterwegs Stellen, die der Kopf später anfahren soll – ohne Joystick.</li>'
           '<li><b>Einschalten und drucken:</b> Mehr → «▦ Karten-Werkstatt» → «📍 Markier-Karten»: Schalter ein, Name, A4 oder A5, «Karte erstellen», mit 100 % auf mattes Papier drucken. '
           'Höchstens 10 Karten; jede Karte gilt nur für dieses MoveEye (eigene Marker-Nummern 40–49).</li>'
           '<li><b>Nur bei Schutz «Aus»:</b> bei Wachsam / Voll wird die Karte ignoriert (Hinweis im Live-Bild und im Protokoll). Ist der Kopf in «Aus» geparkt (Privatsphäre), '
           'ihn kurz mit dem Joystick bewegen – dann sucht MoveEye die Karte.</li>'
           '<li><b>So geht es:</b> Karte vor die Kopf-Kamera halten – Ton. Weggehen, die Karte zur Kamera halten – der Kopf schaut mit (Folgen von Personen und die Runde machen solange Pause). '
           '<b>Punkt merken:</b> stehen bleiben, die Karte 1–2 s umdrehen und wieder zeigen – zweiter Ton. Die Stelle steht als «Punkt 1», «Punkt 2» … im Teach-in '
           '(Einstellungen → Servos → Positionen) mit dem geschätzten Abstand, gleich in der Runde; umbenennen wie jeden Punkt. Ein tiefer Ton heisst «verloren» (6 s ohne Karte, der Kopf bleibt stehen); '
           'nach 90 s ohne Karte endet die Sitzung.</li>'
           '<li><b>Abstand:</b> geprüft im Simulator (nicht mit echter Kamera): A4 folgt bis etwa 10 m und merkt Punkte sicher bis etwa 5–6 m; bei gutem Licht geht es oft weiter, '
           'in der Dämmerung weniger weit; A5 etwa 0,7 × so weit. Karte gerade und ruhig halten, nicht spiegelnd.</li></ul></section>\n'),
    "en": ('<section id="markierkarte" data-icon="📍"><h2>Marker card (experimental)</h2><ul>'
           '<li><b>What:</b> a printed card with a big marker (and a small QR code). MoveEye sees it from far away, beeps and follows it with the head. '
           'Walk over the place and save spots the head should look at later – without a joystick.</li>'
           '<li><b>Switch on and print:</b> More → «▦ Card workshop» → «📍 Marker cards»: switch on, name, A4 or A5, «Make the card», print at 100 % on matt paper. '
           'At most 10 cards; every card counts only for this MoveEye (own marker numbers 40–49).</li>'
           '<li><b>Only with the protection «Off»:</b> in Watchful / Full the card is ignored (a hint in the live picture and in the log). If the head is parked in «Off» (privacy), '
           'move it a little with the joystick – then MoveEye looks for the card.</li>'
           '<li><b>How:</b> hold the card in front of the head camera – a sound. Walk away holding the card towards the camera – the head looks along (following persons and the round pause meanwhile). '
           '<b>Mark a point:</b> stand still, turn the card for 1–2 s and show it again – a second sound. The spot is saved as «Point 1», «Point 2» … in the teach-in '
           '(Settings → Servos → Positions) with its estimated distance, in the round; rename it like any point. A low sound means «lost» (6 s without the card, the head stays); '
           'after 90 s without the card the session ends.</li>'
           '<li><b>Distance:</b> checked in the simulator (not with a real camera): A4 follows up to about 10 m and marks points reliably up to about 5–6 m; in good light it often works further, '
           'less far at dusk; A5 about 0.7 × as far. Hold the card straight and still, not shiny.</li></ul></section>\n'),
    "fr": ('<section id="markierkarte" data-icon="📍"><h2>Carte de repérage (expérimental)</h2><ul><li>Une carte imprimée avec un grand repère : MoveEye la voit de loin, bipe '
           'et la suit avec la tête. S’arrêter, retourner la carte 1–2 s et la remontrer : l’endroit est enregistré comme «Point 1», «Point 2» … dans le teach-in (avec la distance, dans la ronde). '
           'Seulement si la protection est arrêtée. Créer et imprimer : Plus → Atelier des cartes → Cartes de repérage. Distance (simulateur) : A4 suit jusqu’à env. 10 m, '
           'marque sûrement jusqu’à env. 5–6 m ; par bonne lumière souvent plus loin, au crépuscule moins ; A5 env. 0,7 ×.</li></ul></section>\n'),
    "it": ('<section id="markierkarte" data-icon="📍"><h2>Carta di marcatura (sperimentale)</h2><ul><li>Una carta stampata con un grande marcatore: MoveEye la vede da lontano, emette '
           'un bip e la segue con la testa. Fermarsi, girare la carta per 1–2 s e mostrarla di nuovo: il posto viene salvato come «Punto 1», «Punto 2» … nel teach-in (con la distanza, nel giro). '
           'Solo con protezione spenta. Creare e stampare: Altro → Laboratorio delle carte → Carte di marcatura. Distanza (simulatore): A4 segue fino a circa 10 m, '
           'segna con sicurezza fino a circa 5–6 m; con buona luce spesso oltre, al crepuscolo meno; A5 circa 0,7 ×.</li></ul></section>\n'),
    "rm": ('<section id="markierkarte" data-icon="📍"><h2>Carta da marcar (experimental)</h2><ul><li>Ina carta stampada cun in grond marcader: MoveEye la vesa da lunsch, pipa '
           'e la suonda cun il chau. Star airi, volver la carta 1–2 s e la mussar puspè: il lieu vegn memorisà sco «Punct 1», «Punct 2» … en il teach-in (cun la distanza, en la runda). '
           'Mo cun protecziun deactivada. Crear e stampar: Dapli → Ufficina da cartas → Cartas da marcar. Distanza (simulatur): A4 suonda fin circa 10 m, '
           'marca segir fin circa 5–6 m; cun bun glisch savens pli lunsch, en il crepuscul main; A5 circa 0,7 ×.</li></ul></section>\n'),
}


def _help_mk(doc, lang):
    if 'id="markierkarte"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_MK[lang] + doc[i:] if i >= 0 else doc


_hp_en_mk = HELP_PAGE.find('<div lang="en">')
if _hp_en_mk > 0:
    HELP_PAGE = _help_mk(HELP_PAGE[:_hp_en_mk], "de") + _help_mk(HELP_PAGE[_hp_en_mk:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_mk(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def mk_selftest():
    keep = {k: json.loads(json.dumps(CFG.get(k))) for k in list(MK_DEF) + ["armed", "pan", "tilt", "qrk_secret", "kopf_parked"]}
    wp = [list(w) for w in WAYPOINTS]
    sv, lg, sp, gr = save_settings, log_event, globals()["sound_play"], globals()["servo_pos"]
    beeps = []
    try:
        globals()["save_settings"] = lambda *a, **k: None
        globals()["log_event"] = lambda *a, **k: None
        globals()["sound_play"] = lambda k, *a, **kw: beeps.append(k) or (True, "")
        assert KOPF_PRIO.index("alarm") < KOPF_PRIO.index("marker") < KOPF_PRIO.index("round")
        assert "mk_cards" in USER_SETTINGS_DENY and "/api/mk" in APPKEY_DENY_PATHS and '639zzzzm' in QRK_PAGE and 'id="markierkarte"' in HELP_PAGE
        assert tr("Marker card only when the protection is off", "de") == "Markier-Karte nur bei Schutz Aus"
        assert not role_allows("family", "/api/mk", "POST", {"action": "create"}) and not role_allows("family", "/karten/markier", "GET", {})
        CFG.update(mk_cards=[], mk_dist={}, mk_on=True, armed=False, kopf_parked=False)
        WAYPOINTS[:] = []
        det = mk_detector()
        if not det.ok:
            assert mk_pause_reason() == "OpenCV without ArUco"
            return "no ArUco in this OpenCV: switched off cleanly (" + det.why + ")"
        c, err = mk_create("Zelt", "a4", "selftest")
        assert c and c["mid"] == MK_IDS[0] and not err
        assert mk_qr_check(mk_qr_payload(c)) == c and mk_qr_check("MK" + c["id"] + "A" * QRK_MAC_LEN) is None
        assert "<svg" in mk_card_svg(c) and "<path" in mk_card_svg(c, "a5")
        img = np.full((720, 1280), 120, np.uint8)
        m = det.image(c["mid"], 120)
        img[300:420, 600:720] = 255
        img[310:410, 610:710] = cv2.resize(m, (100, 100), interpolation=cv2.INTER_NEAREST)
        assert det.detect(img, {c["mid"]})["id"] == c["mid"] and det.detect(img, {41}) is None, "only own numbers"
        pos = [50.0, 50.0]
        globals()["servo_pos"] = lambda: tuple(pos)
        CFG["armed"] = True
        assert mk_tick(img, 1000.0) == 1.0 and MK["ses"] is None, "protection on: ignored"
        CFG["armed"] = False
        mk_tick(img, 1000.0)
        assert MK["ses"] and mk_active() and "marker" in kopf_claims() and kopf_track_blocked() and beeps[-1] == "beep2"
        blank = np.full((720, 1280), 120, np.uint8)
        t = 1000.0
        for _ in range(12):
            t += 0.12; mk_tick(img, t)
        n0 = len(WAYPOINTS)
        for _ in range(10):
            t += 0.12; mk_tick(blank, t)                         # 1.2 s turned away
        for _ in range(5):
            t += 0.12; mk_tick(img, t)
        assert len(WAYPOINTS) == n0 + 1 and wp_name(WAYPOINTS[-1]).startswith(tr("Point")) and wp_patrol(WAYPOINTS[-1]), WAYPOINTS[-1:]
        nm = wp_name(WAYPOINTS[-1])
        assert 1.0 < CFG["mk_dist"][nm] < 20.0 and beeps[-1] == "beep3"
        assert any(p.get("mk_m") for p in teach_list())
        for _ in range(3):
            t += 0.12; mk_tick(blank, t)                         # 0.36 s: somebody walks through - no point
        for _ in range(5):
            t += 0.12; mk_tick(img, t)
        assert len(WAYPOINTS) == n0 + 1
        teach_edit("rename", len(WAYPOINTS) - 1, "Zelt vorne")
        assert "Zelt vorne" in CFG["mk_dist"] and nm not in CFG["mk_dist"]
        for _ in range(60):
            t += 0.12; mk_tick(blank, t)
        assert MK["ses"]["state"] == "lost" and beeps[-1] == "beeplow"
        t += 100.0; mk_tick(blank, t)
        assert MK["ses"] is None and not mk_active()
        assert mk_delete(c["id"])[0] and not mk_cards()
    finally:
        MK["ses"] = None
        globals()["save_settings"], globals()["log_event"], globals()["sound_play"], globals()["servo_pos"] = sv, lg, sp, gr
        WAYPOINTS[:] = wp
        CFG.update(keep)
    return "ArUco " + mk_detector().api + ", own numbers only, protection off only, follow, mark (turned 1.2 s), no point when hidden 0.4 s, rename, lost / end, rights, page hooks"


SELFTEST_EXTRA.append(("Marker card «📍 Markier-Karte» (639zzzzm)", mk_selftest))
