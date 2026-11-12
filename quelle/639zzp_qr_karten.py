#@ MoveEye – Teil 639zzp: «▦ QR-Befehls-Karten» (experimentell, ab Werk aus) – eine gedruckte Karte (oder ein Handy-Bildschirm) mit einem QR-Code vor die Kamera halten, MoveEye liest den Code und führt den Befehl darin aus. Nur eigene Karten gelten (Prüfnummer HMAC mit einem Schlüssel dieses Geräts), Karten sperren, «Karten-Werkstatt» im Web. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Idee 13 des Besitzers (Entscheide 10.11.2026, fest):
#   * Befehle der ersten Version: Push (Text aus dem Code, auf Wunsch mit dem Foto) · Text über den Lautsprecher vorlesen
#     (tts_say, Piper 639zzb) · Notiz mit Foto im Verlauf · Aufnahme starten (Dauer) · Licht / Relais ein / aus · Kopf auf eine
#     gespeicherte Position (Teach-in 076) · Profil wechseln (Erkennungsprofil 639zz oder Modus 130). NICHT: MQTT, Zeitschaltuhr,
#     Ausschalten / Pause des Schutzes (kein Weg zu «Aus»: ein Modus, der den Schutz ausschalten würde, wird abgelehnt -
#     mode_disarms 135, wie die PIN-Regeln von 3.72.0).
#   * Nur Karten DIESES MoveEye gelten: jeder Code trägt eine Prüfnummer = HMAC-SHA256 über Kennung + Befehl + Werte mit einem
#     zufälligen Schlüssel des Geräts (CFG qrk_secret, nur in den Einstellungen, nie im Code), gekürzt auf 50 Bit. Fremde oder
#     veränderte Codes: eine kurze Zeile «fremde Karte ignoriert» im Protokoll (höchstens 1× pro Minute, nie der Inhalt - er
#     könnte ein WLAN-Passwort sein). Sperren: pro Karte (Liste CFG qrk_cards, gelöscht = ungültig) oder alle mit einem neuen
#     Schlüssel (Warnung; jede Karte kann danach neu gedruckt werden).
#   * Zwei Formen, pro Karte wählbar (Entscheid Besitzer 11.11.2026 nach der Messung):
#       «Text auf dem MoveEye» (Standard; immer bei Licht / Relais / Kopf / Profil / Aufnahme): der Code ist nur
#         «M1» + Kennung (5) + Befehl (1) + Prüfnummer (10) = 18 Bytes = 25 × 25 Module; Text und Werte stehen im Karten-Eintrag
#         auf dem Gerät. Die Prüfnummer deckt Kennung + Befehl - darum bleibt die gedruckte Karte gültig, wenn der Text später
#         geändert wird (qrk_set_text); sperren / löschen wirkt über den Eintrag, «neuer Schlüssel» über die Prüfnummer.
#       «Text im Code» (nur Push / Vorlesen / Notiz): dieselben 18 Bytes + der Text (höchstens QRK_TEXT_MAX Bytes UTF-8), die
#         Prüfnummer deckt auch den Text; grösserer Code = kürzerer Abstand, Text nur mit neuer Karte änderbar.
#     Streng: jede Karte hat genau einen gültigen Code (die kurze Form einer «Text im Code»-Karte gilt nicht und umgekehrt).
#     Alphabet der Kennung / Prüfnummer: 32 Zeichen ohne I, O, 0, 1. Kein Passwort, kein WLAN, kein Zugang im Code: die
#     Werkstatt lehnt Texte mit bekannten Geheimnissen / WLAN-Namen ab (qrk_secret_hit); der Push geht wie jeder andere
#     durch push_no_ssid (635c).
#   * Werkstatt «/karten» (nur Administrator, kein App-Schlüssel, nicht im Bedienermodus): Befehl wählen, Text / Werte,
#     Vorschau mit geschätzter Reichweite, Karte drucken (Seite für die Druckfunktion des Browsers: Postkarte 10 × 15 cm mit
#     QR 8 cm, A5 oder A4), PNG / SVG laden, Liste mit Name, Befehl, erstellt, zuletzt benutzt, sperren / freigeben / löschen,
#     «▶ Ausprobieren» (führt den Befehl ohne Kamera aus). Eingang: Mehr → «▦ Karten-Werkstatt» und Einstellungen →
#     Kameras & Kopf → «QR-Befehls-Karten» (dort der Schalter, er gehört zur Kamera wie Zeitraffer und Videoquelle).
#   * Lesen: nur wenn eingeschaltet, 1× pro Sekunde (qrk_rate 0.5 … 2), ein eigener Faden mit tiefer Priorität (nice 10) -
#     die Erkennung wartet nie auf ihn. Bilder: das saubere Bild der Kopf-Kamera (frame_raw, 410) und / oder der
#     Weitwinkel-Kamera (raw, 440) über die vorhandene Ausleihe raw_until, nie das Wärmebild. Grösser als 1280 px wird
#     verkleinert; kleiner nicht (die Messung zeigt: halbe Grösse = ein Drittel weniger Reichweite).
#     Pause: Simulation, Werkzeug-Modus, Akku-Sparen (105), CPU über qrk_cpu_max (Rückkehr 10 % darunter), Erkennung unter
#     2 Bildern/s; der Faden braucht höchstens etwa 1/8 einer CPU (misst seine eigene Zeit und wartet länger).
#   * Sperrzeit pro Karte: ausgeführt wird erst wieder, wenn die Karte QRK_GONE_S aus dem Bild war UND qrk_cooldown vorbei ist
#     (hält man sie 30 s vor die Kamera, läuft der Befehl einmal).
#   * Rückmeldung: «Verstanden» gesprochen (oder kurzer Ton, oder nichts - qrk_feedback), Rahmen + Schild um die Karte im
#     Live-Bild für QRK_SHOW_S (grün = ausgeführt, orange = gesperrt, rot = fremd) - gezeichnet ins Bild der Kamera wie die
#     Rahmen der Erkennung (Web, Fenster, SmallTV gleich), nicht in die Aufnahmen. Jede Ausführung: Zeile im Protokoll und
#     (qrk_photo, ab Werk an) ein Foto mit Notiz in Verlauf → Aufnahmen (Quelle «QR card»; in der Simulation keine Fotos).
# Messung vor dem Bau (Simulation, nicht echte Kamera): werkzeuge/qr_karten_test.py --messen. Ergebnis im Bericht an den
# Besitzer: Postkarte mit QR 8 cm am Kopf (66°, 1280 × 720) bei Tag etwa 0,6–0,9 m, Weitwinkel 0,3–0,4 m; kurze Texte reichen
# weiter (weniger Module), A4 etwa doppelt so weit.
# Test: werkzeuge/qr_karten_test.py (Demo-Kamera mit einer Karte im Bild, Befehle, Sperrzeit, fremd / verändert / gesperrt,
# aus = kein Lesen, Rechte, Browser in Handy-Breite).
# ----------------------------------------------------------------------------
QRK_PREFIX = "M1"
QRK_ID_LEN = 5
QRK_MAC_LEN = 10                       # 10 × 5 bit = 50 bit
QRK_HEAD = len(QRK_PREFIX) + QRK_ID_LEN + 1 + QRK_MAC_LEN
QRK_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
QRK_TEXT_MAX = 100                     # bytes UTF-8 of a text (push, announcement, note)
QRK_NAME_MAX = 40
QRK_DESC_MAX = 120
QRK_CARDS_MAX = 100
QRK_SCAN_W = 1280                      # px: bigger pictures are made smaller before reading
QRK_GONE_S = 3.0                       # s out of view before the same card works again
QRK_SHOW_S = 4.0                       # s the frame stays around the card in the live picture
QRK_FOREIGN_LOG_S = 60.0               # «foreign card ignored» at most once a minute
QRK_REC_MAX = 600                      # s: at most 10 minutes (like the quick switch «Record»)
QRK_RANGE_K = 0.26                     # m per mm of module size: simulation, head camera 66°, 1280 px, day (see the head)
QRK_SIZES = {"card": (100, 150, 80, "Postcard 10 × 15 cm"), "a5": (148, 210, 120, "A5"), "a4": (210, 297, 180, "A4")}
QRK_CMDS = {   # letter: (name, icon, label)
    "P": ("push", "📲", "Push message"),
    "S": ("say", "🔊", "Read aloud"),
    "N": ("note", "📝", "Note with photo"),
    "R": ("rec", "⏺", "Start a recording"),
    "L": ("light", "💡", "Light on / off"),
    "Y": ("relay", "⚡", "Relay on / off"),
    "H": ("head", "🎯", "Head to a position"),
    "F": ("profile", "🎛️", "Switch profile"),
}
QRK_CMD_ORDER = "PSNRLYHF"
QRK_TEXT_CMDS = "PSN"                  # commands with a text: the text on the device (default) or in the code
QRK_SECTION = "QR command cards"
QRK_DEF = {"qrk_on": False, "qrk_cam_head": True, "qrk_cam_wide": True, "qrk_rate": 1.0, "qrk_cooldown": 10, "qrk_feedback": "speak",
           "qrk_photo": True, "qrk_cpu_max": 85, "qrk_cards": [], "qrk_secret": ""}
for _k, _v in QRK_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
    FACTORY_CFG.setdefault(_k, json.loads(json.dumps(_v)))              # 636 took its copy before this part
# only the administrator: the switch, the cards, the key (never a user with «settings», never an app key)
USER_SETTINGS_DENY.update(QRK_DEF)
APPKEY_DENY_KEYS.update(QRK_DEF)
APPKEY_DENY_PATHS.update({"/api/qrk", "/karten"})
LOCK_DENY_PATHS.add("/api/qrk")                                         # operator mode (390): no new cards, no new key

QRK = {"lock": threading.RLock(), "run_lock": threading.Lock(), "thread": None, "pause": "off", "dec": "", "ms": None, "scans": 0,
       "seen": {}, "show": {}, "log_t": {}, "uses": deque(maxlen=30), "last": None, "cpu_hold": False, "err_t": 0.0}


# ---- the code: check number, make, read --------------------------------------------------------------------------------------------
def _qrk_b32(b, n):
    v, bits, out = 0, 0, []
    for x in b:
        v = (v << 8) | x; bits += 8
        while bits >= 5 and len(out) < n:
            bits -= 5; out.append(QRK_ALPHA[(v >> bits) & 31])
    return "".join(out)[:n]


def qrk_key(make=True):
    """the secret key of this device (32 bytes as hex in the settings) - made with the first card"""
    k = str(CFG.get("qrk_secret") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", k):
        if not make:
            return ""
        k = secrets.token_hex(32)
        CFG["qrk_secret"] = k
        save_settings()
    return k


def qrk_key_fp(k=None):
    """a short fingerprint of the key (which key a card was printed with) - never the key itself"""
    k = qrk_key(False) if k is None else k
    return hashlib.sha256(("fp|" + k).encode()).hexdigest()[:8] if k else ""


def qrk_mac(cid, cmd, param, key=None):
    k = bytes.fromhex(key or qrk_key())
    return _qrk_b32(hmac.new(k, (QRK_PREFIX + cid + cmd + param).encode("utf-8"), hashlib.sha256).digest(), QRK_MAC_LEN)


def qrk_in_code(card):
    """is the text of this card inside the QR code («Text im Code»)? Else the code holds only id + command + check number and
    text / values live in the card record on the device («Text auf dem MoveEye»: smaller code, text can be changed later)"""
    return bool(card.get("tc")) and card["cmd"] in QRK_TEXT_CMDS


def qrk_payload(card, key=None):
    """the text in the QR code of a card: short form (18 bytes, values on the device) or with the text («Text im Code»)"""
    p = card["p"] if qrk_in_code(card) else ""
    return QRK_PREFIX + card["id"] + card["cmd"] + qrk_mac(card["id"], card["cmd"], p, key) + p


def qrk_parse(text):
    """(id, cmd, mac, param) or None when it is no MoveEye card at all"""
    t = str(text or "")
    if not t.startswith(QRK_PREFIX) or len(t) < QRK_HEAD:
        return None
    cid, cmd, mac, p = t[2:2 + QRK_ID_LEN], t[2 + QRK_ID_LEN], t[3 + QRK_ID_LEN:QRK_HEAD], t[QRK_HEAD:]
    if cmd not in QRK_CMDS or any(c not in QRK_ALPHA for c in cid + mac):
        return None
    return cid, cmd, mac, p


def qrk_cards():
    """the cards of the settings, cleaned (wrong entries are left out)"""
    out = []
    for c in CFG.get("qrk_cards") or []:
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or c.get("cmd") not in QRK_CMDS or not isinstance(c.get("p"), str):
            continue
        out.append(c)
    return out


def qrk_card(cid):
    return next((c for c in qrk_cards() if c["id"] == cid), None)


def qrk_check(text):
    """("ok", card) · ("revoked", card) · ("unknown", None) - right number but the card was deleted · ("foreign", None)"""
    r = qrk_parse(text)
    k = qrk_key(False)
    if r is None or not k:
        return "foreign", None
    cid, cmd, mac, p = r
    if not hmac.compare_digest(mac, qrk_mac(cid, cmd, p, k)):
        return "foreign", None                              # another MoveEye, an old key or changed by somebody
    c = qrk_card(cid)
    if c is None or c["cmd"] != cmd or p != (c["p"] if qrk_in_code(c) else ""):   # strict: each card has exactly one valid code
        return "unknown", None
    if c.get("off"):
        return "revoked", c
    return "ok", c


def qrk_qr_size(payload):
    """(QR version, modules per side) of a code"""
    n = len(qr_matrix(payload))
    return (n - 17) // 4, n


def qrk_range(modules, qr_mm):
    """estimated reading distance in m (simulation: head camera, day) for a code of `modules` printed `qr_mm` wide"""
    return round(QRK_RANGE_K * qr_mm / max(1, modules), 1)


# ---- what is allowed in a card ---------------------------------------------------------------------------------------------------
_QRK_SECRET_WORDS = re.compile(r"WIFI:|://[^/\s:@]+:[^/\s@]+@|pass(?:wort|word)|kennwort|mot de passe|\bpin\s*[:=]", re.I)


def qrk_secret_hit(text):
    """True when the text contains a password, an access code, a push topic or the name of a Wi-Fi (never on a card)"""
    t = str(text or "")
    if not t:
        return False
    if _QRK_SECRET_WORDS.search(t):
        return True
    low = t.lower()
    vals = [CFG.get(k) for k in ("hotspot_password", "web_password", "protect_pin", "lock_pin", "telegram_token", "telegram_chat",
                                 "pushover_token", "pushover_user", "email_password", "mqtt_password", "update_token", "guest_token",
                                 "ext_token", "qrk_secret")]
    url = str(CFG.get("notify_url") or "").strip().rstrip("/")
    if url:
        vals.append(url)
        vals.append(url.rsplit("/", 1)[-1])                  # the ntfy topic
    try:
        vals += push_ssids()
    except Exception:
        pass
    hs = str(CFG.get("hotspot_ssid") or "").strip()
    if hs and hs.lower() != "moveeye":
        vals.append(hs)
    for v in vals:
        v = str(v or "").strip()
        if len(v) >= 4 and v.lower() in low:
            return True
    return False


def qrk_points():
    return [wp_name(w) for w in WAYPOINTS if wp_name(w)]


def qrk_modes():
    """the modes a card may choose (never one that would switch the protection off now - mode_disarms, 135)"""
    out = []
    for m, ic, nm in MODES:
        if m == "transport":
            continue                                         # «Ruhe» switches the detection off: never by card
        out.append((m, ic, nm))
    return out


def qrk_make_param(cmd, d):
    """(param, "") from the fields of the workshop, or ("", English error)"""
    if cmd in "PSN":
        txt = re.sub(r"[\x00-\x1f\x7f]", " ", str(d.get("text") or "")).strip()
        if not txt:
            return "", "the text is empty"
        if len(txt.encode("utf-8")) > QRK_TEXT_MAX:
            return "", "the text is too long"
        if qrk_secret_hit(txt):
            return "", "This text contains a password, an access code or a Wi-Fi name - not allowed on a card."
        return (("1" if d.get("photo") else "0") + txt) if cmd == "P" else txt, ""
    if cmd == "R":
        try:
            s = int(float(d.get("secs") or 60))
        except (TypeError, ValueError):
            return "", "invalid value"
        return str(max(10, min(QRK_REC_MAX, s))), ""
    if cmd == "L":
        n = {"white": "w", "ir": "i"}.get(str(d.get("light") or ""))
        if not n:
            return "", "invalid value"
        return n + ("1" if d.get("on") else "0"), ""
    if cmd == "Y":
        try:
            i = int(d.get("relay"))
        except (TypeError, ValueError):
            return "", "unknown relay"
        if not 0 <= i < len(RELAYS):
            return "", "unknown relay"
        return f"{i}:{'1' if d.get('on') else '0'}", ""
    if cmd == "H":
        nm = str(d.get("point") or "").strip()
        if nm not in qrk_points():
            return "", "no such point"
        if len(nm.encode("utf-8")) > QRK_TEXT_MAX:
            return "", "the text is too long"
        return nm, ""
    if cmd == "F":
        v = str(d.get("profile") or "")
        if v.startswith("p:") and (v[2:] == "" or v[2:] in PROFILES):
            return v, ""
        if v.startswith("m:") and v[2:] in [m for m, _i, _n in qrk_modes()] + [""]:
            return v, ""
        return "", "unknown profile"
    return "", "unknown command"


def qrk_what(card, lang=None, icon=True):
    """a short text: what the card does («💡 White light on»; icon=False for the printed card - fonts there have no emoji)"""
    L = norm_lang(lang)
    cmd, p = card["cmd"], card["p"]
    ic = QRK_CMDS[cmd][1] if icon else ""
    if cmd == "P":
        return ic + " " + tr("Push", L) + (" + " + tr("photo", L) if p[:1] == "1" else "") + ": «" + p[1:] + "»"
    if cmd in "SN":
        return ic + " " + tr(QRK_CMDS[cmd][2], L) + ": «" + p + "»"
    if cmd == "R":
        return ic + " " + trf("Recording {s} s", L, s=p)
    if cmd == "L":
        return ic + " " + tr(LIGHT_NAMES.get("white" if p[:1] == "w" else "ir"), L) + " " + tr("on" if p[1:] == "1" else "off", L)
    if cmd == "Y":
        i, _s, on = p.partition(":")
        nm = RELAYS[int(i)]["name"] if i.isdigit() and int(i) < len(RELAYS) else tr("Relay", L) + " " + str(int(i) + 1 if i.isdigit() else "?")
        return ic + " " + nm + " " + tr("on" if on == "1" else "off", L)
    if cmd == "H":
        return ic + " " + tr("Head to", L) + " «" + p + "»"
    if cmd == "F":
        if p.startswith("p:"):
            d = prof_def(p[2:])
            return ic + " " + tr("Detection profile", L) + ": " + (d["icon"] + " " if icon else "") + tr(d["name"], L)
        m = next(((ic_, nm) for mm, ic_, nm in MODES if mm == p[2:]), ("⚙️", "Own settings"))
        return ic + " " + tr("Mode", L) + ": " + (m[0] + " " if icon else "") + tr(m[1], L)
    return ic


def qrk_create(d, who="admin"):
    """a new card from the workshop -> (card, "") or (None, English error)"""
    cmd = str(d.get("cmd") or "")
    if cmd not in QRK_CMDS:
        return None, "unknown command"
    name = re.sub(r"[\x00-\x1f\x7f]", " ", str(d.get("name") or "")).strip()[:QRK_NAME_MAX]
    desc = re.sub(r"[\x00-\x1f\x7f]", " ", str(d.get("desc") or "")).strip()[:QRK_DESC_MAX]
    if not name:
        return None, "the name is empty"
    if qrk_secret_hit(name) or qrk_secret_hit(desc):
        return None, "This text contains a password, an access code or a Wi-Fi name - not allowed on a card."
    p, err = qrk_make_param(cmd, d)
    if err:
        return None, err
    with QRK["lock"]:
        lst = qrk_cards()
        if len(lst) >= QRK_CARDS_MAX:
            return None, "too many cards"
        key = qrk_key()
        ids = {c["id"] for c in lst}
        cid = ""
        while not cid or cid in ids:
            cid = "".join(secrets.choice(QRK_ALPHA) for _ in range(QRK_ID_LEN))
        card = {"id": cid, "name": name, "desc": desc, "cmd": cmd, "p": p, "made": datetime.now().isoformat(timespec="seconds"),
                "used": "", "n": 0, "off": False, "fp": qrk_key_fp(key), "tc": bool(d.get("tc")) and cmd in QRK_TEXT_CMDS}
        lst.append(card)
        CFG["qrk_cards"] = lst
    save_settings()
    log_event("sys", f"QR card made ({who}): «{name}» - {QRK_CMDS[cmd][0]}")
    return card, ""


def qrk_edit(action, cid, who="admin"):
    """revoke / unrevoke / delete one card -> (ok, English error)"""
    with QRK["lock"]:
        lst = qrk_cards()
        c = next((x for x in lst if x["id"] == cid), None)
        if c is None:
            return False, "unknown card"
        if action == "revoke":
            c["off"] = True
        elif action == "unrevoke":
            c["off"] = False
        elif action == "delete":
            lst.remove(c)
        else:
            return False, "unknown action"
        CFG["qrk_cards"] = lst
    save_settings()
    log_event("sys", f"QR card {action} ({who}): «{c['name']}»")
    return True, ""


def qrk_set_text(cid, d, who="admin"):
    """change the text of a card whose text lives on the device - the printed card stays valid (its check number covers
    only id + command) -> (ok, English error)"""
    with QRK["lock"]:
        lst = qrk_cards()
        c = next((x for x in lst if x["id"] == cid), None)
        if c is None:
            return False, "unknown card"
        if c["cmd"] not in QRK_TEXT_CMDS:
            return False, "this card has no text"
        if qrk_in_code(c):
            return False, "the text is in the code - make a new card"
        dd = dict(d)
        if c["cmd"] == "P" and "photo" not in dd:
            dd["photo"] = c["p"][:1] == "1"
        p, err = qrk_make_param(c["cmd"], dd)
        if err:
            return False, err
        c["p"] = p
        c["edited"] = datetime.now().isoformat(timespec="seconds")
        CFG["qrk_cards"] = lst
    save_settings()
    log_event("sys", f"QR card text changed ({who}): «{c['name']}»")
    return True, ""


def qrk_rotate(who="admin"):
    """a new key: every printed card is invalid at once (each can be printed again)"""
    with QRK["lock"]:
        CFG["qrk_secret"] = ""
        qrk_key()
    log_event("sys", f"QR cards: new key ({who}) - all printed cards are invalid")
    return True, ""


# ---- reading: the pictures, the decoder, the pauses ----------------------------------------------------------------------------------
def qrk_decoder_name():
    return "QRCodeDetectorAruco" if hasattr(cv2, "QRCodeDetectorAruco") else "QRCodeDetector"


_QRK_TL = threading.local()


def qrk_detector():
    d = getattr(_QRK_TL, "det", None)                       # one per thread (OpenCV detectors are not shared between threads)
    if d is None:
        d = cv2.QRCodeDetectorAruco() if hasattr(cv2, "QRCodeDetectorAruco") else cv2.QRCodeDetector()
        _QRK_TL.det = d
    return d


def qrk_decode(img):
    """(text, [[x, y] × 4] 0..1) of the QR code in a picture, or ("", None)"""
    if img is None or img.size == 0:
        return "", None
    H, W = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    if W > QRK_SCAN_W:
        g = cv2.resize(g, (QRK_SCAN_W, max(1, int(H * QRK_SCAN_W / W))), interpolation=cv2.INTER_AREA)
    h, w = g.shape[:2]
    try:
        txt, pts, _s = qrk_detector().detectAndDecode(g)
    except cv2.error:
        return "", None
    if not txt or pts is None:
        return "", None
    try:
        P = [[round(float(x) / w, 4), round(float(y) / h, 4)] for x, y in np.asarray(pts, np.float32).reshape(-1, 2)[:4]]
    except (TypeError, ValueError):
        P = None
    return txt, P


def qrk_cams():
    out = []
    if CFG.get("qrk_cam_head", True):
        out.append("head")
    if CFG.get("qrk_cam_wide", True):
        out.append("wide")
    return out


def qrk_grab(cam):
    """the newest clean picture of a camera (head: frame_raw of 410, wide: raw of 440) - by the lease raw_until, or None"""
    now = time.time()
    if cam == "head":
        w = WATCH_REF.get("w")
        if w is None:
            return None, None
        prev = getattr(w, "frame_raw", None)
        w.raw_until = max(float(getattr(w, "raw_until", 0.0) or 0.0), now + 0.4)
        end = now + 0.6
        while time.time() < end:
            f = getattr(w, "frame_raw", None)
            if f is not None and f is not prev:
                return f, w
            time.sleep(0.03)
        return None, w
    c = view3_wide_cam()
    if c is None or c.status != "connected":
        return None, None
    t_prev = float(getattr(c, "raw_t", 0.0) or 0.0)
    c.raw_until = max(float(getattr(c, "raw_until", 0.0) or 0.0), now + 0.4)
    end = now + 0.6
    while time.time() < end:
        if c.raw is not None and float(c.raw_t or 0.0) > t_prev:
            return c.raw, c
        time.sleep(0.03)
    return None, c


def qrk_pause_reason():
    """"" = reading may run now, else the English reason"""
    if not CFG.get("qrk_on"):
        return "off"
    if not qrk_cams():
        return "no camera chosen"
    if not qrk_cards():
        return "no cards yet"
    if CFG.get("sim_on"):
        return "simulation"
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
    cpu = STATE.get("cpu")
    lim = float(CFG.get("qrk_cpu_max") or 85)
    if cpu is not None:
        if cpu > lim or (QRK["cpu_hold"] and cpu > lim - 10):
            QRK["cpu_hold"] = True
            return "CPU busy"
        QRK["cpu_hold"] = False
    w = WATCH_REF.get("w")
    fps = STATE.get("fps")
    if w is not None and CFG.get("detection_on") and fps is not None and STATE.get("frames", 0) > 30 and float(fps) < 2.0:
        return "detection is slow"
    return ""


def qrk_tick():
    """one round: read every chosen camera once; returns the seconds until the next round"""
    why = qrk_pause_reason()
    QRK["pause"] = why
    if why:
        return 1.0
    busy = 0.0
    for cam in qrk_cams():
        img, src = qrk_grab(cam)
        if img is None:
            continue
        t0 = time.time()
        txt, pts = qrk_decode(img)
        dt = time.time() - t0
        busy += dt
        QRK["ms"] = round(dt * 1000.0 if QRK["ms"] is None else 0.8 * QRK["ms"] + 200.0 * dt, 1)
        QRK["scans"] += 1
        if txt:
            qrk_seen(cam, txt, pts, img, src)
    rate = max(0.5, min(2.0, float(CFG.get("qrk_rate") or 1.0)))
    return max(1.0 / rate, busy * 8.0)                       # at most about 1/8 of one CPU core


def qrk_loop():
    try:
        os.setpriority(os.PRIO_PROCESS, threading.get_native_id(), 10)    # lower than the detection
    except (AttributeError, OSError):
        pass
    QRK["dec"] = qrk_decoder_name()
    while True:
        try:
            gap = qrk_tick()
        except Exception as e:
            gap = 3.0
            if time.time() - QRK["err_t"] > 300:
                QRK["err_t"] = time.time()
                log_event("sys", f"QR cards: {type(e).__name__}: {e}"[:160])
        time.sleep(gap)


def qrk_start():
    """start the reading thread once (it sleeps while the function is off)"""
    if QRK["thread"] is not None:
        return
    with QRK["lock"]:
        if QRK["thread"] is None:
            QRK["thread"] = threading.Thread(target=qrk_loop, daemon=True, name="qr-cards")
            QRK["thread"].start()


# ---- a card was seen ----------------------------------------------------------------------------------------------------------------
def qrk_show(cam, pts, kind, label, src=None):
    QRK["show"][cam] = {"t": time.time(), "pts": pts, "kind": kind, "label": label, "src": src, "img": None}


def qrk_seen(cam, text, pts, img, src=None, now=None):
    """the scanner read a QR code -> "run" (the command starts), "hold" (cooldown / still in view), "revoked", "unknown",
    "foreign" (never logged with its content)"""
    now = time.time() if now is None else now
    L = norm_lang(CFG.get("lang"))
    st, card = qrk_check(text)
    if st == "foreign":
        qrk_show(cam, pts, "bad", "✕ " + tr("foreign card", L), src)
        if now - QRK["log_t"].get("foreign", 0.0) >= QRK_FOREIGN_LOG_S:
            QRK["log_t"]["foreign"] = now
            log_event("sys", "QR card: foreign card ignored")
        return "foreign"
    if st in ("revoked", "unknown"):
        nm = card["name"] if card else "?"
        qrk_show(cam, pts, "off", "⛔ " + tr("card revoked", L) + (": " + nm if card else ""), src)
        key = "rev|" + (card["id"] if card else text[2:7])
        if now - QRK["log_t"].get(key, 0.0) >= QRK_FOREIGN_LOG_S:
            QRK["log_t"][key] = now
            log_event("sys", f"QR card «{nm}» is revoked - ignored" if card else "QR card: deleted card ignored")
        return st
    s = QRK["seen"].setdefault(card["id"], {"last": 0.0, "fired": 0.0})
    gone = now - s["last"] >= QRK_GONE_S
    s["last"] = now
    cool = max(3.0, float(CFG.get("qrk_cooldown") or 10))
    qrk_show(cam, pts, "ok", "✓ " + card["name"], src)
    if not gone or now - s["fired"] < cool:
        return "hold"
    s["fired"] = now
    qrk_spawn(card, img.copy() if img is not None else None, cam)
    return "run"


def qrk_spawn(card, img, cam):
    """the command runs in its own thread - reading goes on"""
    threading.Thread(target=qrk_run, args=(card, img, cam), daemon=True, name="qr-card-run").start()


def qrk_feedback(lang=None):
    """«Verstanden» on the loudspeaker (or a short sound, or nothing)"""
    fb = str(CFG.get("qrk_feedback") or "speak")
    if fb == "off":
        return False, "off"
    L = norm_lang(lang or CFG.get("lang"))
    if fb == "speak":
        ok, err = tts_say(tr("Understood", L), L)
        if ok:
            return True, ""
    return sound_play("beep2", 0.46, CFG.get("clap_volume", 60), reason="test")


def _qrk_jpg(img, q=85):
    if img is None:
        return None
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return buf.tobytes() if ok else None


def qrk_photo(card, img, note):
    """the picture of the camera + a note into Verlauf → Aufnahmen (source «QR card»); "" = saved, else the English reason"""
    if img is None:
        return "no camera picture yet"
    if CFG.get("sim_on"):
        return "Simulation: no recordings"
    try:
        d = rec_dir()
        os.makedirs(d, exist_ok=True)
        name = f"qrcard_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{card['id'].lower()}.jpg"
        path = os.path.join(d, name)
        if not cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 88]):
            return "could not save the picture"
        try:
            gps_tag_jpg(path)
        except Exception:
            pass
        _write_sidecar(name, {"source": "QR card", "note": str(note)[:240], "qrcard": card["id"]})
        return ""
    except OSError as e:
        return str(e)[:120]


def qrk_exec(card, img, who="QR card"):
    """run the command of a card with the functions MoveEye already has -> (ok, English message)"""
    cmd, p = card["cmd"], card["p"]
    L = norm_lang(CFG.get("lang"))
    nm = card["name"]
    if cmd == "P":
        w = WATCH_REF.get("w")
        n = getattr(w, "notifier", None) if w is not None else None
        if n is None:
            return False, "no camera loop"
        jpg = _qrk_jpg(img) if p[:1] == "1" and CFG.get("push_pics") != "text" else None
        pub = str(CFG.get("public_url") or "").strip().rstrip("/")
        msg = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": p[1:],
               "info_title": "{name}: ▦ " + nm, "obj_ic": "▦", "obj_title": nm, "obj_ev": "qrcard", "snapshot": None,
               "rain": bool(STATE.get("rain_mode")), "wind": STATE.get("wind_level", ""), "source": STATE.get("source_label", ""),
               "link": pub + "/" if pub else ""}
        threading.Thread(target=n._dispatch, args=(msg, jpg, "karte.jpg"), daemon=True).start()   # 635c: never a Wi-Fi name
        return True, "" if n.configured() else "push messages are not set up - only in the message list"
    if cmd == "S":
        return tts_say(p, L)
    if cmd == "N":
        err = qrk_photo(card, img, "📝 " + p)
        return (not err), err
    if cmd == "R":
        if CFG.get("sim_on"):
            return False, "Simulation: no recordings"
        secs = max(10, min(QRK_REC_MAX, int(p) if p.isdigit() else 60))
        QUICK["rec_until"] = max(QUICK["rec_until"], time.time() + secs)
        log_event("rec", f"Recording started by the QR card «{nm}» ({secs} s)")
        return True, ""
    if cmd == "L":
        return light_set("white" if p[:1] == "w" else "ir", "on" if p[1:] == "1" else "off")
    if cmd == "Y":
        i, _s, on = p.partition(":")
        if not i.isdigit():
            return False, "unknown relay"
        return relay_update(int(i), "mode", "on" if on == "1" else "off")
    if cmd == "H":
        i = next((j for j, w in enumerate(WAYPOINTS) if wp_name(w) == p), None)
        if i is None:
            return False, "no such point"
        return teach_goto(i, who="qrcard")
    if cmd == "F":
        kind, _s, v = p.partition(":")
        if kind == "p":
            return prof_set(v, who)
        if v == "transport" or mode_disarms(v):
            return False, "this would switch the protection off - not by card"
        return mode_set(v, who="qrcard")
    return False, "unknown command"


def qrk_run(card, img, cam, who="QR card", feedback=True):
    """a card was read: feedback, the command, the line in the log, the photo in the history"""
    if not QRK["run_lock"].acquire(timeout=20):
        return False, "busy"
    try:
        L = norm_lang(CFG.get("lang"))
        if feedback and card["cmd"] != "S":                  # the announcement speaks itself
            try:
                qrk_feedback(L)
            except Exception:
                pass
        try:
            ok, msg = qrk_exec(card, img, who)
        except Exception as e:
            ok, msg = False, f"{type(e).__name__}: {e}"[:160]
        now = datetime.now()
        with QRK["lock"]:
            lst = qrk_cards()
            c = next((x for x in lst if x["id"] == card["id"]), None)
            if c is not None:
                c["used"] = now.isoformat(timespec="seconds"); c["n"] = int(c.get("n") or 0) + 1
                CFG["qrk_cards"] = lst
        save_settings()
        what = qrk_what(card, "en")
        log_event("sys", f"QR card «{card['name']}» ({cam}): {QRK_CMDS[card['cmd']][0]} - " + ("done" if ok and not msg else (msg or "done") if ok else "not done: " + str(msg)))
        pe = ""
        if card["cmd"] != "N" and CFG.get("qrk_photo", True) and cam in ("head", "wide"):
            pe = qrk_photo(card, img, "▦ " + card["name"] + " · " + what)
        QRK["last"] = {"t": time.time(), "id": card["id"], "name": card["name"], "ok": bool(ok), "msg": str(msg or ""), "cam": cam}
        QRK["uses"].appendleft({"t": now.strftime("%Y-%m-%d %H:%M:%S"), "id": card["id"], "name": card["name"], "cmd": card["cmd"],
                                "ok": bool(ok), "msg": str(msg or ""), "cam": cam, "photo": not pe})
        return ok, msg
    finally:
        QRK["run_lock"].release()


# ---- the frame around the card in the live picture (head: walktest_draw 410, wide: weit_ki_frame 440) -----------------------------
_QRK_COL = {"ok": (80, 220, 90), "off": (40, 160, 245), "bad": (70, 70, 240)}


def _qrk_label_img(text, color, hgt):
    """the label as (BGR, alpha 0..1) - PIL with a real font (umlauts), else cv2"""
    try:
        from PIL import Image, ImageDraw
        f = _font(int(hgt * 0.62))
        tmp = ImageDraw.Draw(Image.new("RGB", (4, 4)))
        tw = int(tmp.textlength(text, font=f)) + hgt
        im = Image.new("RGBA", (tw, hgt), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, tw - 1, hgt - 1), radius=hgt // 3, fill=(color[2], color[1], color[0], 235))
        d.text((hgt // 2, int(hgt * 0.14)), text, font=f, fill=(0, 0, 0, 255))
        a = np.asarray(im)
        return cv2.cvtColor(a[:, :, :3], cv2.COLOR_RGB2BGR), a[:, :, 3:4].astype(np.float32) / 255.0
    except Exception:
        t = text.encode("ascii", "replace").decode()
        (tw, th), _b = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, hgt / 40.0, 2)
        im = np.zeros((hgt, tw + hgt, 3), np.uint8); im[:] = color
        cv2.putText(im, t, (hgt // 2, int(hgt * 0.72)), cv2.FONT_HERSHEY_SIMPLEX, hgt / 40.0, (0, 0, 0), 2, cv2.LINE_AA)
        return im, np.ones((hgt, tw + hgt, 1), np.float32)


def qrk_draw(frame, cam, src=None):
    """frame + label around the card for a few seconds"""
    s = QRK["show"].get(cam)
    if not s or time.time() - s["t"] > QRK_SHOW_S or frame is None:
        return
    if src is not None and s.get("src") is not None and s["src"] is not src:
        return
    try:
        H, W = frame.shape[:2]
        col = _QRK_COL.get(s["kind"], (255, 255, 255))
        pts = s.get("pts")
        if pts:
            P = np.array([[int(x * W), int(y * H)] for x, y in pts], np.int32).reshape(-1, 1, 2)
            cv2.polylines(frame, [P], True, (0, 0, 0), 7, cv2.LINE_AA)
            cv2.polylines(frame, [P], True, col, 4, cv2.LINE_AA)
            x0, y0, y1 = int(P[:, 0, 0].min()), int(P[:, 0, 1].min()), int(P[:, 0, 1].max())
        else:
            x0, y0, y1 = W // 3, H // 3, H // 3
        hgt = max(24, H // 16)
        if s["img"] is None or s["img"][2] != hgt:
            b, a = _qrk_label_img(str(s["label"])[:48], col, hgt)
            s["img"] = (b, a, hgt)
        b, a, _h = s["img"]
        lh, lw = b.shape[:2]
        x, y = max(0, min(W - lw, x0)), y0 - lh - 6
        if y < 40:                                            # no room above (the HUD line): under the card
            y = min(H - lh, y1 + 6)
        if lw > W or lh > H:
            return
        roi = frame[y:y + lh, x:x + lw]
        frame[y:y + lh, x:x + lw] = (roi * (1 - a) + b * a).astype(np.uint8)
    except (cv2.error, ValueError, TypeError, IndexError):
        pass


_walktest_draw_qrk = walktest_draw


# wraps: walktest_draw
def walktest_draw(frame):                                    # + 639zzp: the frame around a QR card (head camera) - after the marks, before the HUD
    _walktest_draw_qrk(frame)
    if QRK["show"].get("head"):
        qrk_draw(frame, "head")
    if QRK["thread"] is None:
        qrk_start()


_weit_ki_frame_qrk = weit_ki_frame


# wraps: weit_ki_frame
def weit_ki_frame(c, frame):                                 # + 639zzp: the frame around a QR card in the wide picture
    _weit_ki_frame_qrk(c, frame)
    if QRK["show"].get("wide"):
        qrk_draw(frame, "wide", c)


# ---- state for the pages --------------------------------------------------------------------------------------------------------
def qrk_card_json(c, lang=None):
    L = norm_lang(lang)
    key = qrk_key(False)
    pl = qrk_payload(c, key) if key else ""
    ver, n = qrk_qr_size(pl) if pl else (0, 0)
    txt = (c["p"][1:] if c["cmd"] == "P" else c["p"]) if c["cmd"] in QRK_TEXT_CMDS else ""
    return {"id": c["id"], "name": c["name"], "desc": c.get("desc", ""), "cmd": c["cmd"], "icon": QRK_CMDS[c["cmd"]][1],
            "tc": qrk_in_code(c), "text": txt, "editable": c["cmd"] in QRK_TEXT_CMDS and not qrk_in_code(c), "edited": c.get("edited", ""),
            "kind": tr(QRK_CMDS[c["cmd"]][2], L), "what": qrk_what(c, L), "made": c.get("made", ""), "used": c.get("used", ""),
            "n": int(c.get("n") or 0), "off": bool(c.get("off")), "reprint": bool(c.get("fp")) and c.get("fp") != qrk_key_fp(key),
            "ver": ver, "modules": n, "range": {k: qrk_range(n, v[2]) for k, v in QRK_SIZES.items()}}


def qrk_state(lang=None):
    L = norm_lang(lang)
    why = QRK["pause"] if CFG.get("qrk_on") else "off"
    last = QRK["last"]
    return {"on": bool(CFG.get("qrk_on")), "pause": why, "pause_t": tr(why, L) if why else "", "dec": QRK["dec"] or qrk_decoder_name(),
            "ms": QRK["ms"], "scans": QRK["scans"], "cams": qrk_cams(), "rate": CFG.get("qrk_rate"), "cooldown": CFG.get("qrk_cooldown"),
            "last": dict(last, ago=int(time.time() - last["t"]), msg_t=tr_err(last["msg"], L) if last.get("msg") else "") if last else None,
            "uses": [dict(u, msg_t=tr_err(u["msg"], L) if u.get("msg") else "") for u in list(QRK["uses"])[:10]]}


def qrk_choices(lang=None):
    L = norm_lang(lang)
    return {"cmds": [{"c": c, "icon": QRK_CMDS[c][1], "label": tr(QRK_CMDS[c][2], L)} for c in QRK_CMD_ORDER],
            "points": qrk_points(),
            "relays": [{"i": i, "name": r["name"]} for i, r in enumerate(RELAYS)],
            "lights": [{"v": "white", "name": tr("White light", L)}, {"v": "ir", "name": tr("Infrared light", L)}],
            "profiles": [{"v": "p:" + k, "name": PROFILES[k]["icon"] + " " + tr(PROFILES[k]["name"], L), "group": tr("Detection profile", L)} for k in PROF_ORDER]
                        + [{"v": "p:", "name": PROF_NONE["icon"] + " " + tr(PROF_NONE["name"], L), "group": tr("Detection profile", L)}]
                        + [{"v": "m:" + m, "name": ic + " " + tr(nm, L), "group": tr("Mode", L)} for m, ic, nm in qrk_modes()],
            "text_max": QRK_TEXT_MAX, "name_max": QRK_NAME_MAX, "desc_max": QRK_DESC_MAX, "rec_max": QRK_REC_MAX,
            "sizes": [{"v": k, "name": tr(v[3], L), "qr_cm": v[2] / 10} for k, v in QRK_SIZES.items()], "range_k": QRK_RANGE_K}


# ---- the card as SVG / PNG / print page --------------------------------------------------------------------------------------------
def _qrk_wrap(text, n):
    words, lines, cur = str(text or "").split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 > n and cur:
            lines.append(cur); cur = w_
        else:
            cur = (cur + " " + w_).strip()
    if cur:
        lines.append(cur)
    return lines[:3]


def qrk_card_svg(card, size="card", lang=None):
    """the whole card (QR, name, short description, small footer) in mm - for the print page and «⬇ SVG»"""
    L = norm_lang(lang)
    W, H, Q, _n = QRK_SIZES.get(size, QRK_SIZES["card"])
    M = qr_matrix(qrk_payload(card))
    n = len(M)
    k = Q / 80.0                                            # the text grows with the card
    x0, y0 = (W - Q) / 2.0, (W - Q) / 2.0
    path = "".join(f"M{x},{y}h1v1h-1z" for y in range(n) for x in range(n) if M[y][x])
    nm = html_escape(card["name"])
    fs = min(9.0, 150.0 / max(8, len(card["name"]))) * k
    y = y0 + Q + 12 * k
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
             f'<rect x="0.3" y="0.3" width="{W - 0.6}" height="{H - 0.6}" rx="{4 * k:.1f}" fill="#fff" stroke="#999" stroke-width="0.3" stroke-dasharray="2 1.5"/>',
             f'<g transform="translate({x0:.2f},{y0:.2f}) scale({Q / n:.5f})"><path d="{path}" fill="#000" shape-rendering="crispEdges"/></g>',
             f'<text x="{W / 2}" y="{y:.1f}" font-family="DejaVu Sans,Helvetica,Arial,sans-serif" font-size="{fs:.2f}" font-weight="700" text-anchor="middle" fill="#111">{nm}</text>']
    y += 7 * k
    for ln in _qrk_wrap(card.get("desc") or qrk_what(card, L, icon=False).strip(), 40):
        parts.append(f'<text x="{W / 2}" y="{y:.1f}" font-family="DejaVu Sans,Helvetica,Arial,sans-serif" font-size="{4.2 * k:.2f}" text-anchor="middle" fill="#333">{html_escape(ln)}</text>')
        y += 5.4 * k
    foot = "▦ MoveEye · " + tr("QR card", L) + " · " + tr(QRK_CMDS[card["cmd"]][2], L) + " · " + card["id"]
    parts.append(f'<text x="{W / 2}" y="{H - 6 * k:.1f}" font-family="DejaVu Sans,Helvetica,Arial,sans-serif" font-size="{3.1 * k:.2f}" text-anchor="middle" fill="#777">{html_escape(foot)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def qrk_card_png(card, size="card", lang=None, dpmm=12):
    """the card as a picture (12 px per mm ≈ 300 dpi); without PIL only the QR code with a white border"""
    L = norm_lang(lang)
    W, H, Q, _n = QRK_SIZES.get(size, QRK_SIZES["card"])
    M = np.array(qr_matrix(qrk_payload(card)), bool)
    n = M.shape[0]
    qpx = int(Q * dpmm) // n * n
    q = np.where(np.kron(M, np.ones((qpx // n, qpx // n), bool)), 0, 255).astype(np.uint8)
    img = np.full((int(H * dpmm), int(W * dpmm)), 255, np.uint8)
    x0 = (img.shape[1] - qpx) // 2; y0 = x0
    img[y0:y0 + qpx, x0:x0 + qpx] = q
    try:
        from PIL import Image, ImageDraw
        im = Image.fromarray(img).convert("RGB")
        d = ImageDraw.Draw(im)
        k = Q / 80.0
        f1, f2, f3 = _font(int(min(9.0, 150.0 / max(8, len(card["name"]))) * k * dpmm)), _font(int(4.2 * k * dpmm), bold=False), _font(int(3.1 * k * dpmm), bold=False)
        y = y0 + qpx + int(4 * k * dpmm)
        d.text((im.width // 2, y), card["name"], font=f1, fill=(17, 17, 17), anchor="mt")
        y += int(11 * k * dpmm)
        for ln in _qrk_wrap(card.get("desc") or qrk_what(card, L, icon=False).strip(), 40):
            d.text((im.width // 2, y), ln, font=f2, fill=(51, 51, 51), anchor="mt"); y += int(5.4 * k * dpmm)
        d.text((im.width // 2, im.height - int(8 * k * dpmm)), "MoveEye · " + tr("QR card", L) + " · " + tr(QRK_CMDS[card["cmd"]][2], L) + " · " + card["id"],
               font=f3, fill=(119, 119, 119), anchor="mt")
        img = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
    except Exception:
        pass
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes() if ok else b""


def qrk_print_page(card, size="card", lang=None, auto=False):
    L = norm_lang(lang)
    T = lambda s: html_escape(tr(s, L))
    W, H, Q, _n = QRK_SIZES.get(size, QRK_SIZES["card"])
    links = " ".join(f'<a href="/karten/print?id={card["id"]}&amp;size={k}&amp;lang={L}"{" class=on" if k == size else ""}>{T(v[3])}</a>'
                     for k, v in QRK_SIZES.items())
    page_size = "A4" if size in ("card", "a5") else "A4"
    return ('<!doctype html><html lang="' + L + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="referrer" content="no-referrer"><title>MoveEye – ' + T("QR card") + ' – ' + html_escape(card["name"]) + '</title><style>'
            '@page{size:' + page_size + ' portrait;margin:10mm}html,body{background:#fff;color:#111}'
            'body{font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;padding:12px 16px}'
            '.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 10px}.bar button,.bar a{font:inherit;padding:8px 12px;border-radius:8px;'
            'border:1px solid #999;background:#f4f4f4;color:#111;cursor:pointer;text-decoration:none;min-height:40px;box-sizing:border-box;display:inline-flex;align-items:center}'
            '.bar a.on{background:#1f6feb;border-color:#1f6feb;color:#fff}.m{color:#555;margin:0 0 10px;font-size:13px}'
            '.cv{display:flex;justify-content:center}.cv svg{max-width:100%;height:auto}'
            '@media print{.bar,.m{display:none}body{padding:0}.cv svg{width:' + str(W) + 'mm;height:' + str(H) + 'mm;max-width:none}}'
            '</style></head><body><div class="bar"><button type="button" onclick="print()">🖨 ' + T("Print") + '</button>' + links
            + '<button type="button" onclick="history.length>1?history.back():close()">' + T("Close") + '</button></div>'
            '<div class="m">' + T("Print at 100 % (no «fit to page»). Cut along the dashed line. Card and phone screen work the same.") + '</div>'
            '<div class="cv">' + qrk_card_svg(card, size, L) + '</div>'
            + ('<script>addEventListener("load",function(){setTimeout(function(){try{print();}catch(e){}},300);});</script>' if auto else "")
            + '<script>window.__mwExit = true;</script></body></html>')


# ---- the web: /karten (workshop), /api/qrk, card pictures, print page -----------------------------------------------------------------
def qrk_admin_ok(g_):
    return getattr(g_, "role", "admin") == "admin" and not getattr(g_, "appkey", None)


_smalltv_routes_qrk = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzp: the workshop and its API (only the administrator)
    _smalltv_routes_qrk(app, reply, body)
    from flask import Response, request, g
    qrk_start()

    def nope():
        if not qrk_admin_ok(g):
            return reply({"ok": False, "error": tr("Only for the administrator", norm_lang(request.args.get("lang")))}, 403)
        return None

    @app.route("/api/qrk", methods=["GET", "POST"])
    def api_qrk():
        n = nope()
        if n is not None:
            return n
        if request.method == "GET":
            L = norm_lang(request.args.get("lang") or CFG.get("lang"))
            return reply({"ok": True, "state": qrk_state(L), "cards": [qrk_card_json(c, L) for c in qrk_cards()][::-1], "choices": qrk_choices(L),
                          "fp": qrk_key_fp()})
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        a = str(d.get("action") or "")
        if a == "create":
            card, err = qrk_create(d, "web")
            if card is None:
                return reply({"ok": False, "error": tr_err(err, L)}, 400)
            return reply({"ok": True, "card": qrk_card_json(card, L)})
        if a in ("revoke", "unrevoke", "delete"):
            ok, err = qrk_edit(a, str(d.get("id") or ""), "web")
            return reply({"ok": ok, "error": tr_err(err, L) if err else None}, 200 if ok else 400)
        if a == "rotate":
            if not d.get("confirm"):
                return reply({"ok": False, "error": tr("Please confirm.", L)}, 400)
            qrk_rotate("web")
            return reply({"ok": True})
        if a == "try":
            c = qrk_card(str(d.get("id") or ""))
            if c is None:
                return reply({"ok": False, "error": tr_err("unknown card", L)}, 400)
            if c.get("off"):
                return reply({"ok": False, "error": tr("This card is revoked.", L)}, 400)
            img, _src = qrk_grab("head")
            ok, msg = qrk_run(c, img.copy() if img is not None else None, "workshop", "QR card (workshop)", feedback=False)
            return reply({"ok": ok, "msg": tr_err(msg, L) if msg else ""}, 200)
        if a == "check":                                     # the workshop: size and range before the card is made
            cmd = str(d.get("cmd") or "")
            if cmd not in QRK_CMDS:
                return reply({"ok": False, "error": tr_err("unknown command", L)}, 400)
            tc = bool(d.get("tc")) and cmd in QRK_TEXT_CMDS
            p, err = qrk_make_param(cmd, d)
            if err and tc:
                return reply({"ok": False, "error": tr_err(err, L)})
            p = p if tc else ""                              # short form: the size never depends on the text
            ver, mods = qrk_qr_size(QRK_PREFIX + "A" * QRK_ID_LEN + cmd + "A" * QRK_MAC_LEN + p)
            return reply({"ok": True, "ver": ver, "modules": mods, "bytes": QRK_HEAD + len(p.encode("utf-8")), "tc": tc,
                          "warn": tr_err(err, L) if err and err != "the text is empty" else "",
                          "range": {k: qrk_range(mods, v[2]) for k, v in QRK_SIZES.items()}})
        if a == "text":
            ok, err = qrk_set_text(str(d.get("id") or ""), d, "web")
            return reply({"ok": ok, "error": tr_err(err, L) if err else None}, 200 if ok else 400)
        return reply({"ok": False, "error": "unknown action"}, 400)

    @app.route("/api/qrk/card/<cid>.<ext>")
    def api_qrk_card(cid, ext):
        n = nope()
        if n is not None:
            return n
        c = qrk_card(cid)
        if c is None or ext not in ("svg", "png"):
            return Response("not found", 404)
        size = request.args.get("size") if request.args.get("size") in QRK_SIZES else "card"
        L = norm_lang(request.args.get("lang") or CFG.get("lang"))
        fname = "moveeye_karte_" + re.sub(r"[^A-Za-z0-9_-]+", "_", c["name"])[:30] + "_" + c["id"] + "." + ext
        h = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
        if request.args.get("dl") == "1":
            h["Content-Disposition"] = f'attachment; filename="{fname}"'
        if ext == "svg":
            return Response(qrk_card_svg(c, size, L), mimetype="image/svg+xml", headers=h)
        return Response(qrk_card_png(c, size, L), mimetype="image/png", headers=h)

    @app.route("/karten")
    def qrk_page():
        n = nope()
        if n is not None:
            return n
        return Response(render_page(QRK_PAGE, "more"), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/karten/print")
    def qrk_print():
        n = nope()
        if n is not None:
            return n
        c = qrk_card(str(request.args.get("id") or ""))
        if c is None:
            return Response("not found", 404)
        size = request.args.get("size") if request.args.get("size") in QRK_SIZES else "card"
        return Response(qrk_print_page(c, size, request.args.get("lang") or CFG.get("lang"), request.args.get("p") == "1"),
                        mimetype="text/html", headers={"Cache-Control": "no-store"})


QRK_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>MoveEye - QR command cards</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:900px;margin:0 auto;box-sizing:border-box}
.qk-top{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:0 0 6px}.qk-top h2{margin:0;flex:1 1 220px;font-size:20px}
.qk-exp{font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid var(--yel);color:var(--yel);white-space:nowrap}
.qk-st{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin:0 0 14px}
.qk-st.on{border-color:var(--grn)}.qk-st b{flex:1 1 200px}.qk-st .mut{font-size:12.5px;flex-basis:100%}
.qk-sw{display:flex;align-items:center;gap:8px;font-weight:600;min-height:40px}
.qk-f{display:grid;grid-template-columns:1fr;gap:10px}.qk-f label{display:flex;flex-direction:column;gap:4px;font-size:13px;color:var(--mut)}
.qk-f label.chk{flex-direction:row;align-items:center;gap:8px;color:var(--txt);font-size:14px;min-height:40px}
.qk-f input[type=text],.qk-f input[type=number],.qk-f select,.qk-f textarea{font:inherit;font-size:16px;min-height:42px;box-sizing:border-box;width:100%}
.qk-f textarea{min-height:70px;resize:vertical;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:8px 10px}
.qk-cmds{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}@media(max-width:520px){.qk-cmds{grid-template-columns:repeat(2,minmax(0,1fr))}}
.qk-cmds button{min-height:52px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-size:12.5px;padding:6px 4px;line-height:1.15}
.qk-cmds button i{font-style:normal;font-size:20px}.qk-cmds button.on{outline:2px solid var(--acc);background:var(--glow)}
.qk-hint{font-size:12.5px;color:var(--mut)}.qk-hint.bad{color:var(--red)}.qk-hint.warn{color:var(--yel)}
.qk-row{display:flex;gap:8px;flex-wrap:wrap}.qk-row button{min-height:42px;flex:1 1 auto}
.qk-list{display:flex;flex-direction:column;gap:10px}
.qk-c{display:grid;grid-template-columns:96px minmax(0,1fr);gap:12px;border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:10px}
.qk-c.off{opacity:.62}.qk-c .pv{background:#fff;border-radius:8px;padding:3px;aspect-ratio:2/3;cursor:zoom-in;overflow:hidden}.qk-c .pv img{width:100%;height:100%;object-fit:contain;display:block}
.qk-c b{font-size:15px;overflow-wrap:anywhere}.qk-c .w{font-size:13px;overflow-wrap:anywhere}.qk-c .mut{font-size:12px}
.qk-c .bb{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}.qk-c .bb button,.qk-c .bb a{min-height:38px;padding:4px 10px;font-size:13px}
.qk-tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:999px;border:1px solid var(--line);margin-left:6px;vertical-align:middle}
.qk-tag.off{border-color:var(--org);color:var(--org)}.qk-tag.re{border-color:var(--yel);color:var(--yel)}
.qk-new{display:none;gap:12px;align-items:flex-start;flex-wrap:wrap;margin-top:12px}.qk-new.on{display:flex}
.qk-new .pv{background:#fff;border-radius:10px;padding:6px;width:min(220px,60vw)}.qk-new .pv img{width:100%;display:block}
.qk-danger{border-color:var(--red)!important}.qk-uses{font-size:12.5px;margin:4px 0 0;padding-left:18px}
details.card>summary{cursor:pointer;font-weight:600}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <div class="qk-top"><h2 id="qk-title">▦ Card workshop</h2><span class="qk-exp" id="qk-exp">experimental</span></div>
  <div class="mut" id="qk-intro" style="margin:0 0 12px"></div>
  <div class="qk-st" id="qk-st">…</div>
  <section class="card" id="qk-make">
    <h3 id="qk-make-t" style="margin:0 0 10px">New card</h3>
    <div class="qk-f">
      <div class="qk-cmds" id="qk-cmds"></div>
      <label><span id="qk-l-name">Name on the card</span><input type="text" id="qk-name" maxlength="40" autocomplete="off"></label>
      <div id="qk-fields" class="qk-f"></div>
      <label><span id="qk-l-desc">Short description (under the code)</span><input type="text" id="qk-desc" maxlength="120" autocomplete="off"></label>
      <div class="qk-hint" id="qk-size"></div>
      <div class="qk-row"><button type="button" id="qk-go">▦ Make the card</button></div>
      <div class="qk-hint bad" id="qk-err"></div>
    </div>
    <div class="qk-new" id="qk-new"><div class="pv"><img id="qk-new-img" alt=""></div><div style="flex:1 1 200px"><b id="qk-new-n"></b><div class="mut" id="qk-new-w"></div>
      <div class="qk-row" style="margin-top:8px" id="qk-new-b"></div></div></div>
  </section>
  <section class="card"><h3 id="qk-list-t" style="margin:0 0 10px">My cards</h3><div class="qk-list" id="qk-list">…</div></section>
  <details class="card qk-danger"><summary id="qk-rot-s">Make all cards invalid</summary>
    <p class="mut" id="qk-rot-p"></p><button type="button" class="sec" id="qk-rot">⚠ New key</button></details>
  <details class="card"><summary id="qk-how-s">How it works</summary><ul id="qk-how" class="mut"></ul></details>
</main>
<script>
/*COMMON*/
/*QRKDE*/
(async function () {
  try { await initAppearance(); } catch (e) {}
  const $i = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const api = async (b) => { try { const r = await fetch("/api/qrk", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, b || {}))});
    return await r.json(); } catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  document.title = "MoveEye – " + t("Card workshop");
  $i("qk-title").textContent = "▦ " + t("Card workshop"); $i("qk-exp").textContent = t("experimental");
  $i("qk-intro").textContent = t("Make a card with a QR code: hold it in front of the camera and MoveEye does what is on it. Only cards of this MoveEye count.");
  $i("qk-make-t").textContent = t("New card"); $i("qk-list-t").textContent = t("My cards");
  $i("qk-l-name").textContent = t("Name on the card"); $i("qk-l-desc").textContent = t("Short description (under the code)");
  $i("qk-go").textContent = "▦ " + t("Make the card"); $i("qk-rot-s").textContent = "⚠ " + t("Make all cards invalid");
  $i("qk-rot-p").textContent = t("A new key makes every printed card invalid at once (lost or copied cards). You can print each card again afterwards.");
  $i("qk-rot").textContent = "⚠ " + t("New key"); $i("qk-how-s").textContent = t("How it works");
  ["Hold the card still, about an arm’s length in front of the head camera (wide angle: closer). Short texts read from further away.",
   "MoveEye says «Understood» and shows a green frame around the card in the live picture. The same card works again only after it was out of view for a moment (cooldown).",
   "Every use is in the log and, with a photo, in History → Recordings (source «QR card»).",
   "A card cannot switch the protection off. No passwords or Wi-Fi names on a card.",
   "Reading runs only when it is switched on, about once a second, and pauses by itself when the Pi is busy."].forEach(s => $i("qk-how").appendChild(E("li", "", t(s))));
  let J = null, CMD = "P", F = {};
  async function load() {
    try { J = await (await fetch("/api/qrk?lang=" + encodeURIComponent(L()), {cache: "no-store"})).json(); } catch (e) { J = null; }
    if (!J || !J.ok) { $i("qk-list").textContent = "⚠ " + ((J && J.error) || t("Only for the administrator")); $i("qk-st").textContent = ""; return; }
    paintState(); if (!$i("qk-cmds").childElementCount) paintCmds(); paintList();
  }
  function paintState() {
    const s = J.state, b = $i("qk-st"); b.textContent = ""; b.classList.toggle("on", s.on && !s.pause);
    const lab = E("label", "qk-sw"), cb = E("input"); cb.type = "checkbox"; cb.id = "qk-on"; cb.checked = !!s.on;
    cb.onchange = async () => { cb.disabled = true; await post("/api/set", {key: "qrk_on", value: cb.checked}); cb.disabled = false; load(); };
    lab.append(cb, E("span", "", t("Read QR cards (experimental)"))); b.appendChild(lab);
    b.appendChild(E("b", "", s.on ? (s.pause ? "⏸ " + t("Pause") + ": " + s.pause_t : "▶ " + t("Looking for cards") + " · " + (s.cams || []).map(c => t(c === "head" ? "Head view" : "Wide view")).join(" + ")) : t("Off – nothing is read.")));
    const m = [t("Decoder") + ": " + s.dec + (s.ms != null ? " (" + Math.round(s.ms) + " ms)" : "")];
    if (s.last) m.push(t("Last card") + ": «" + s.last.name + "» " + (s.last.ok ? "✓" : "✕ " + (s.last.msg_t || "")));
    m.push(t("Settings → Cameras & head → QR command cards"));
    b.appendChild(E("div", "mut", m.join(" · ")));
  }
  function paintCmds() {
    const box = $i("qk-cmds"); box.textContent = "";
    J.choices.cmds.forEach(c => { const b = E("button", "sec" + (c.c === CMD ? " on" : "")); b.type = "button"; b.dataset.c = c.c;
      b.append(E("i", "", c.icon), E("span", "", c.label)); b.onclick = () => { CMD = c.c; paintCmds(); paintFields(); }; box.appendChild(b); });
    paintFields();
  }
  function inp(lbl, el_) { const l = E("label"); l.append(E("span", "", lbl), el_); return l; }
  function sel(opts, val) { const s = E("select"); opts.forEach(o => { const x = E("option", "", o[1]); x.value = o[0]; s.appendChild(x); }); if (val != null) s.value = val; return s; }
  function onoff() { return sel([["1", t("on")], ["0", t("off")]], "1"); }
  function paintFields() {
    const box = $i("qk-fields"), C = J.choices; box.textContent = ""; F = {};
    if ("PSN".includes(CMD)) {
      F.text = E("textarea"); F.text.id = "qk-text"; F.text.maxLength = C.text_max;
      box.appendChild(inp(CMD === "P" ? t("Text of the push message") : CMD === "S" ? t("Text to read aloud") : t("Text of the note"), F.text));
      if (CMD === "P") { const l = E("label", "chk"); F.photo = E("input"); F.photo.type = "checkbox"; F.photo.checked = true; l.append(F.photo, E("span", "", t("with the photo of the camera"))); box.appendChild(l); }
      F.tc = sel([["0", t("Text on the MoveEye (recommended)")], ["1", t("Text in the code")]], "0"); F.tc.id = "qk-tc";
      box.appendChild(inp(t("Where is the text?"), F.tc));
      const tn = E("div", "qk-hint"); tn.id = "qk-tc-n"; box.appendChild(tn);
      const tcn = () => { tn.textContent = F.tc.value === "1" ? t("The text is inside the QR code: the code gets bigger and reads only from closer; to change the text you print a new card.")
        : t("The code stays small and reads from further away; you can change the text later without printing again."); };
      F.tc.addEventListener("change", tcn); tcn();
    } else if (CMD === "R") {
      F.secs = sel([[30, "30 s"], [60, "1 min"], [120, "2 min"], [300, "5 min"], [600, "10 min"]], 60); box.appendChild(inp(t("Duration"), F.secs));
    } else if (CMD === "L") {
      F.light = sel(C.lights.map(x => [x.v, x.name])); F.on = onoff(); box.append(inp(t("Which light"), F.light), inp(t("On or off"), F.on));
    } else if (CMD === "Y") {
      if (!C.relays.length) box.appendChild(E("div", "qk-hint warn", t("No relay set up yet (Settings → Extra devices → Relays).")));
      F.relay = sel(C.relays.map(x => [x.i, x.name])); F.on = onoff(); box.append(inp(t("Relay"), F.relay), inp(t("On or off"), F.on));
    } else if (CMD === "H") {
      if (!C.points.length) box.appendChild(E("div", "qk-hint warn", t("No saved position yet (Teach-in under Head).")));
      F.point = sel(C.points.map(x => [x, x])); box.appendChild(inp(t("Position"), F.point));
    } else if (CMD === "F") {
      F.profile = E("select"); const gs = {};
      C.profiles.forEach(p => { let g = gs[p.group]; if (!g) { g = gs[p.group] = E("optgroup"); g.label = p.group; F.profile.appendChild(g); } const o = E("option", "", p.name); o.value = p.v; g.appendChild(o); });
      box.appendChild(inp(t("Profile"), F.profile)); box.appendChild(E("div", "qk-hint", t("A card never switches the protection off (no «Transport / rest»).")));
    }
    Object.values(F).forEach(x => { x.addEventListener("input", sizeSoon); x.addEventListener("change", sizeSoon); });
    sizeSoon();
  }
  function fields() {
    const d = {cmd: CMD, name: $i("qk-name").value, desc: $i("qk-desc").value};
    if (F.text) d.text = F.text.value; if (F.photo) d.photo = F.photo.checked; if (F.secs) d.secs = +F.secs.value;
    if (F.light) d.light = F.light.value; if (F.on) d.on = F.on.value === "1"; if (F.relay) d.relay = F.relay.value === "" ? null : +F.relay.value;
    if (F.point) d.point = F.point.value; if (F.profile) d.profile = F.profile.value; if (F.tc) d.tc = F.tc.value === "1"; return d;
  }
  let ST = 0;
  function sizeSoon() { clearTimeout(ST); ST = setTimeout(size, 250); }
  async function size() {
    const h = $i("qk-size"), r = await api(Object.assign(fields(), {action: "check"}));
    if (!r.ok) { h.className = "qk-hint"; h.textContent = r.error && (F.text && F.text.value) ? "⚠ " + r.error : ""; return; }
    h.className = "qk-hint" + (r.range.card < 0.45 || r.warn ? " warn" : "");
    h.textContent = trf("QR code {m} × {m} modules · reads at about {a} cm (postcard) / {b} m (A4) – estimate from a simulation", {m: r.modules, a: Math.round(r.range.card * 20) * 5, b: fmt(r.range.a4)})
      + (r.tc ? " · " + t("Text in the code: shorter distance, a shorter text reads further.") : "") + (r.warn ? " · ⚠ " + r.warn : "");
  }
  const fmt = v => (Math.round(v * 10) / 10).toLocaleString(L());
  const trf = (k, o) => t(k).replace(/\{(\w+)\}/g, (m, x) => o[x] != null ? o[x] : m);
  $i("qk-go").onclick = async () => {
    const b = $i("qk-go"); b.disabled = true; $i("qk-err").textContent = "";
    const r = await api(Object.assign(fields(), {action: "create"})); b.disabled = false;
    if (!r.ok) { $i("qk-err").textContent = "⚠ " + (r.error || "error"); return; }
    const c = r.card, box = $i("qk-new"); box.classList.add("on");
    $i("qk-new-img").src = "/api/qrk/card/" + c.id + ".svg?lang=" + L() + "&t=" + Date.now(); $i("qk-new-n").textContent = "✓ " + c.name; $i("qk-new-w").textContent = c.what;
    const bb = $i("qk-new-b"); bb.textContent = ""; buttons(c, bb, true);
    $i("qk-name").value = ""; $i("qk-desc").value = ""; if (F.text) F.text.value = ""; await load();
    box.scrollIntoView({behavior: "smooth", block: "nearest"});
  };
  function buttons(c, bb, fresh) {
    const a = (txt, href, dl) => { const x = E("a", "btn sec", txt); x.href = href; if (dl) x.setAttribute("download", ""); else { x.target = "_blank"; x.rel = "noopener"; } bb.appendChild(x); return x; };
    a("🖨 " + t("Print"), "/karten/print?id=" + c.id + "&lang=" + L());
    a("⬇ PNG", "/api/qrk/card/" + c.id + ".png?dl=1&lang=" + L(), true); a("⬇ SVG", "/api/qrk/card/" + c.id + ".svg?dl=1&lang=" + L(), true);
    if (fresh) return;
    const bt = (txt, fn, cls) => { const x = E("button", cls || "sec", txt); x.type = "button"; x.onclick = fn; bb.appendChild(x); return x; };
    if (c.editable) bt("✎ " + t("Change the text"), async () => { const v = prompt(t("New text (the printed card stays valid):"), c.text); if (v == null) return;
      const r = await api({action: "text", id: c.id, text: v}); toast(r.ok ? "✓ " + t("Text changed – no new print needed.") : "⚠ " + (r.error || "error")); load(); });
    if (!c.off) bt("▶ " + t("Try out"), async () => { const r = await api({action: "try", id: c.id}); toast(r.ok ? "✓ " + c.name + (r.msg ? " · " + r.msg : "") : "⚠ " + (r.error || r.msg || "error")); load(); });
    bt(c.off ? "✓ " + t("Allow again") : "⛔ " + t("Revoke card"), async () => { await api({action: c.off ? "unrevoke" : "revoke", id: c.id}); load(); });
    bt("🗑 " + t("Delete"), async () => { if (!confirm(t("Delete this card? Printed copies stop working."))) return; await api({action: "delete", id: c.id}); load(); });
  }
  function paintList() {
    const box = $i("qk-list"); box.textContent = "";
    if (!J.cards.length) { box.appendChild(E("div", "mut", t("No cards yet."))); return; }
    J.cards.forEach(c => {
      const r = E("div", "qk-c" + (c.off ? " off" : "")); r.dataset.id = c.id;
      const pv = E("div", "pv"), im = E("img"); im.loading = "lazy"; im.alt = ""; im.src = "/api/qrk/card/" + c.id + ".svg?lang=" + L(); pv.appendChild(im);
      pv.onclick = () => window.open("/karten/print?id=" + c.id + "&lang=" + L(), "_blank", "noopener");
      const b = E("div"); const h = E("b", "", c.icon + " " + c.name);
      if (c.tc) h.appendChild(E("span", "qk-tag", t("Text in the code")));
      if (c.off) h.appendChild(E("span", "qk-tag off", t("card revoked"))); else if (c.reprint) h.appendChild(E("span", "qk-tag re", t("print again (new key)")));
      b.append(h, E("div", "w", c.what));
      const d = s => s ? s.replace("T", " ").slice(0, 16) : "";
      b.appendChild(E("div", "mut", t("made on") + " " + d(c.made) + " · " + (c.used ? t("last used") + " " + d(c.used) + " (" + c.n + "×)" : t("never used"))
        + " · " + trf("about {a} m", {a: fmt(c.range.card)})));
      const bb = E("div", "bb"); buttons(c, bb, false); b.appendChild(bb);
      r.append(pv, b); box.appendChild(r);
    });
    const u = J.state.uses || [];
    if (u.length) { const ul = E("ul", "qk-uses mut"); u.forEach(x => ul.appendChild(E("li", "", x.t.slice(5, 16) + " · " + x.name + " · " + (x.ok ? "✓" : "✕ " + (x.msg_t || ""))))); box.appendChild(E("b", "", t("Last uses"))); box.appendChild(ul); }
  }
  $i("qk-rot").onclick = async () => {
    if (!confirm(t("Really make ALL printed cards invalid? They stop working at once; you can print them again."))) return;
    const r = await api({action: "rotate", confirm: true}); toast(r.ok ? "✓ " + t("New key – print the cards again.") : "⚠ " + (r.error || "error")); load();
  };
  await load();
  setInterval(() => { if (!document.hidden && J && J.ok) fetch("/api/qrk?lang=" + encodeURIComponent(L()), {cache: "no-store"}).then(r => r.json()).then(j => { if (j && j.ok) { J.state = j.state; paintState(); } }).catch(() => {}); }, 4000);
})();
/*ALERTS*/
</script>
</body></html>
"""

QRK_MORE_ITEM = ('<a class="mi" href="/karten" id="m-qrk"><i>▦</i><span><b data-i18n="Card workshop">Card workshop</b>'
                 '<small data-i18n="QR command cards: make, print, revoke">QR command cards: make, print, revoke</small></span><span class="ar">›</span></a>\n  ')

_render_page_qrk = render_page


# wraps: render_page
def render_page(page, active):                               # + 639zzp: the German texts of the workshop, its item under «Mehr» (administrator)
    out = _render_page_qrk(page, active)
    if "/*QRKDE*/" in out:
        out = out.replace("/*QRKDE*/", "Object.assign(I18N.de, " + json.dumps(_QRK_DE, ensure_ascii=False).replace("</", "<\\/") + ");", 1)
    if active == "more" and 'href="/karten"' not in out and '<a class="mi" href="/tools">' in out:
        try:
            from flask import g as _g
            admin = qrk_admin_ok(_g)
        except Exception:
            admin = False
        if admin:
            i = out.find('<a class="mi" href="/tools">')
            out = (out[:i] + QRK_MORE_ITEM + out[i:]).replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps(
                {k: _QRK_DE[k] for k in ("Card workshop", "QR command cards: make, print, revoke")}, ensure_ascii=False) + ");</script></body>", 1)
    return out


# ---- the settings: Einstellungen → Kameras & Kopf → «QR-Befehls-Karten» (web and window read the same lists) ---------------------
TOGGLES.extend([
    (QRK_SECTION, "qrk_on", "Read QR cards (experimental)"),
    (QRK_SECTION, "qrk_cam_head", "with the head camera"),
    (QRK_SECTION, "qrk_cam_wide", "with the wide-angle camera"),
    (QRK_SECTION, "qrk_photo", "Photo of every use in the history"),
])
SLIDERS.extend([
    (QRK_SECTION, "qrk_rate", "Looks per second", 0.5, 2.0, 0.5),
    (QRK_SECTION, "qrk_cooldown", "Cooldown per card (s)", 3, 60, 1),
    (QRK_SECTION, "qrk_cpu_max", "Pause above CPU (%)", 50, 95, 5),
])
TEXTS.extend([(QRK_SECTION, "qrk_feedback", "Feedback when a card is read", "enum", "qrk_feedback")])
TEXT_SPECS.update({k: (kind, extra) for s, k, l, kind, extra in TEXTS if k == "qrk_feedback"})
SECTIONS.append(QRK_SECTION)
SIMPLE_SECTIONS.add(QRK_SECTION)
SIMPLE_KEYS.add("qrk_on")                                   # «Einfach»: the switch; the rest is folded («Feineinstellungen»)
MENU_TITLES.setdefault(QRK_SECTION, "QR command cards")
TK_SUB_ICONS[QRK_SECTION] = "▦"
for _g in TK_GROUPS:
    if _g[0] == "camera" and QRK_SECTION not in _g[2]:
        _g[2].append(QRK_SECTION)
SET_HELP.update({
    "qrk_on": ("Hold a card with a QR code from the card workshop (More → Card workshop) in front of the camera: MoveEye does what is on it "
               "(push, announcement, note, recording, light, relay, head position, profile). Only cards of this MoveEye count. "
               "Reading about once a second; it pauses by itself when the Pi is busy.", "off (experimental)"),
    "qrk_cooldown": ("The same card works again only after it was out of view for 3 s and this time is over.", "10 s"),
    "qrk_cpu_max": ("Above this CPU load reading pauses (back 10 % below) - the detection always comes first.", "85 %"),
})
_text_choice_pairs_qrk = text_choice_pairs


# wraps: text_choice_pairs
def text_choice_pairs(key):                                  # + 639zzp: the feedback of a card
    ex = (TEXT_SPECS.get(key) or (None, None))[1]
    if ex == "qrk_feedback":
        return [("speak", tr("spoken «Understood»")), ("beep", tr("short sound")), ("off", tr("nothing"))]
    return _text_choice_pairs_qrk(key)


# the web group «Kameras & Kopf»: the section after «Zeitraffer»; its panel (state + link to the workshop)
_QRK_GRP = '{sec: "Timelapse", ic: "⏱️"}]},'
if _QRK_GRP in WEB_PAGE and '{sec: "QR command cards"' not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_QRK_GRP, '{sec: "Timelapse", ic: "⏱️"}, {sec: "QR command cards", title: "QR command cards", ic: "▦"}]},', 1)
_QRK_SEC = 'if (sec.id === "Extra display" && window.stvPanel) stvPanel(d);'
if _QRK_SEC in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_QRK_SEC, _QRK_SEC + '\n    if (sec.id === "QR command cards" && window.qrkPanel) qrkPanel(d);   // 639zzp: QR command cards', 1)

QRK_PANEL_JS = r"""<script>
Object.assign(I18N.de, /*QRKPDE*/{});
window.qrkPanel = function (d) {                       // 639zzp: Einstellungen → Kameras & Kopf → QR-Befehls-Karten
  if (!d || d.querySelector(".qrk-p")) return;
  const box = el("div", "qrk-p"); box.style.cssText = "margin:4px 0 10px;display:flex;flex-direction:column;gap:6px";
  const st = el("div", "mut"); st.style.fontSize = "13px";
  const a = el("a", "btn", "▦ " + t("Open the card workshop")); a.href = "/karten"; a.style.cssText = "align-self:flex-start;min-height:40px;display:inline-flex;align-items:center";
  box.append(st, a);
  const sum = d.querySelector("summary"); if (sum && sum.nextSibling) d.insertBefore(box, sum.nextSibling); else d.appendChild(box);
  let tm = 0;
  const tick = async () => {
    clearTimeout(tm); if (!document.body.contains(box)) return;
    let j = null; try { j = await (await fetch("/api/qrk?lang=" + LANG, {cache: "no-store"})).json(); } catch (e) {}
    if (!j || !j.ok) { st.textContent = ""; return; }
    const s = j.state;
    st.textContent = (s.on ? (s.pause ? "⏸ " + t("Pause") + ": " + s.pause_t : "▶ " + t("Looking for cards")) : t("Off – nothing is read."))
      + " · " + j.cards.length + " " + t("cards") + (s.last ? " · " + t("Last card") + ": «" + s.last.name + "» " + (s.last.ok ? "✓" : "✕") : "");
    if (d.open) tm = setTimeout(tick, 5000);
  };
  d.addEventListener("toggle", () => { if (d.open) tick(); });
  if (d.open) tick();                                // nothing is fetched while the section is closed
};
</script>"""


# ---- the window (Tk): the section shows the state and opens the workshop in the browser -------------------------------------------
def _qrk_tk_build_section(self, sec, sbody, settings_parent=None):
    _qrk_tk_build_section_before(self, sec, sbody, settings_parent)
    if sec != QRK_SECTION:
        return
    try:
        box = ttk.Frame(sbody); box.pack(fill="x", pady=(6, 0))
        lab = ttk.Label(box, text="", wraplength=340, justify="left", style="Mut.TLabel"); lab.pack(anchor="w")
        ttk.Button(box, text="▦ " + tr("Open the card workshop"), command=lambda: self._open_page("/karten")).pack(anchor="w", pady=(4, 0))

        def tick():
            try:
                if not lab.winfo_exists():
                    return
                s = qrk_state()
                lab.config(text=(("⏸ " + tr("Pause") + ": " + s["pause_t"]) if s["on"] and s["pause"] else ("▶ " + tr("Looking for cards")) if s["on"]
                                 else tr("Off – nothing is read.")) + f" · {len(qrk_cards())} " + tr("cards")
                           + ((" · " + tr("Last card") + ": «" + s["last"]["name"] + "»") if s["last"] else ""))
                self.root.after(4000, tick)
            except Exception:
                pass
        tick()
    except Exception as e:
        log_event("sys", f"Window: QR cards: {e}"[:160])


_qrk_tk_build_section_before = App._build_section
# wraps: App._build_section
App._build_section = _qrk_tk_build_section


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_QRK = {
    "QR command cards": ("QR-Befehls-Karten", "Cartes de commande QR", "Carte di comando QR", "Cartas da cumond QR"),
    "Card workshop": ("Karten-Werkstatt", "Atelier des cartes", "Laboratorio delle carte", "Ufficina da cartas"),
    "QR command cards: make, print, revoke": ("QR-Befehls-Karten: erstellen, drucken, sperren", "Cartes de commande QR : créer, imprimer, bloquer",
                                              "Carte di comando QR: creare, stampare, bloccare", "Cartas da cumond QR: crear, stampar, bloccar"),
    "experimental": ("experimentell", "expérimental", "sperimentale", "experimental"),
    "Make a card with a QR code: hold it in front of the camera and MoveEye does what is on it. Only cards of this MoveEye count.": (
        "Eine Karte mit QR-Code erstellen: vor die Kamera halten, und MoveEye macht, was darauf steht. Es gelten nur Karten dieses MoveEye.",
        "Crée une carte avec un code QR : tiens-la devant la caméra et MoveEye fait ce qui est dessus. Seules les cartes de ce MoveEye comptent.",
        "Crea una carta con un codice QR: tienila davanti alla telecamera e MoveEye fa ciò che c’è scritto. Valgono solo le carte di questo MoveEye.",
        "Crear ina carta cun code QR: la tegnair davant la camera, e MoveEye fa quai che stat sin ella. I valan mo cartas da quest MoveEye."),
    "New card": ("Neue Karte", "Nouvelle carte", "Nuova carta", "Nova carta"),
    "My cards": ("Meine Karten", "Mes cartes", "Le mie carte", "Mias cartas"),
    "Name on the card": ("Name auf der Karte", "Nom sur la carte", "Nome sulla carta", "Num sin la carta"),
    "Short description (under the code)": ("Kurze Beschreibung (unter dem Code)", "Courte description (sous le code)", "Breve descrizione (sotto il codice)",
                                           "Curta descripziun (sut il code)"),
    "Make the card": ("Karte erstellen", "Créer la carte", "Creare la carta", "Crear la carta"),
    "Make all cards invalid": ("Alle Karten ungültig machen", "Rendre toutes les cartes invalides", "Rendere non valide tutte le carte", "Far nunvalaivlas tut las cartas"),
    "A new key makes every printed card invalid at once (lost or copied cards). You can print each card again afterwards.": (
        "Ein neuer Schlüssel macht jede gedruckte Karte sofort ungültig (verlorene oder kopierte Karten). Danach kannst du jede Karte neu drucken.",
        "Une nouvelle clé rend aussitôt invalide chaque carte imprimée (cartes perdues ou copiées). Tu peux ensuite réimprimer chaque carte.",
        "Una nuova chiave rende subito non valida ogni carta stampata (carte perse o copiate). Poi puoi ristampare ogni carta.",
        "Ina nova clav fa immediat nunvalaivla mintga carta stampada (cartas persas u copiadas). Suenter pos ti stampar danovamain mintga carta."),
    "New key": ("Neuer Schlüssel", "Nouvelle clé", "Nuova chiave", "Nova clav"),
    "How it works": ("So geht es", "Comment ça marche", "Come funziona", "Uschia funcziuna quai"),
    "Hold the card still, about an arm’s length in front of the head camera (wide angle: closer). Short texts read from further away.": (
        "Die Karte ruhig halten, etwa eine Armlänge vor der Kopf-Kamera (Weitwinkel: näher). Kurze Texte lassen sich von weiter weg lesen.",
        "Tiens la carte immobile, à environ une longueur de bras de la caméra de tête (grand angle : plus près). Les textes courts se lisent de plus loin.",
        "Tieni ferma la carta, a circa un braccio dalla telecamera della testa (grandangolo: più vicino). I testi brevi si leggono da più lontano.",
        "Tegnair quiet la carta, circa ina lunghezza da bratsch davant la camera dal chau (grond angul: pli datiers). Texts curts sa laschan leger da pli lunsch."),
    "MoveEye says «Understood» and shows a green frame around the card in the live picture. The same card works again only after it was out of view for a moment (cooldown).": (
        "MoveEye sagt «Verstanden» und zeigt im Live-Bild einen grünen Rahmen um die Karte. Dieselbe Karte wirkt erst wieder, wenn sie kurz aus dem Bild war (Sperrzeit).",
        "MoveEye dit «Compris» et montre un cadre vert autour de la carte dans l’image en direct. La même carte ne refonctionne qu’après être sortie un moment de l’image (délai).",
        "MoveEye dice «Capito» e mostra una cornice verde attorno alla carta nell’immagine dal vivo. La stessa carta funziona di nuovo solo dopo essere uscita un momento dall’immagine (pausa).",
        "MoveEye di «Chapì» e mussa en il maletg live in rom verd enturn la carta. La medema carta funcziuna pir puspè, cura ch’ella è stada curt ordaifer il maletg (temp da bloccada)."),
    "Every use is in the log and, with a photo, in History → Recordings (source «QR card»).": (
        "Jede Benutzung steht im Protokoll und mit Foto in Verlauf → Aufnahmen (Quelle «QR-Karte»).",
        "Chaque utilisation est dans le journal et, avec une photo, dans Historique → Enregistrements (source «Carte QR»).",
        "Ogni uso è nel protocollo e, con una foto, in Cronologia → Registrazioni (fonte «Carta QR»).",
        "Mintga utilisaziun stat en il protocol e cun foto en Istorgia → Registraziuns (funtauna «Carta QR»)."),
    "A card cannot switch the protection off. No passwords or Wi-Fi names on a card.": (
        "Eine Karte kann den Schutz nicht ausschalten. Keine Passwörter und keine WLAN-Namen auf einer Karte.",
        "Une carte ne peut pas désactiver la protection. Pas de mots de passe ni de noms de Wi-Fi sur une carte.",
        "Una carta non può spegnere la protezione. Niente password né nomi di Wi-Fi su una carta.",
        "Ina carta na po betg stizzar la protecziun. Nagins pleds-clav e nagins nums da WLAN sin ina carta."),
    "Reading runs only when it is switched on, about once a second, and pauses by itself when the Pi is busy.": (
        "Gelesen wird nur, wenn es eingeschaltet ist, etwa einmal pro Sekunde, und es pausiert von selbst, wenn der Pi viel zu tun hat.",
        "La lecture ne fonctionne que si elle est activée, environ une fois par seconde, et se met en pause d’elle-même quand le Pi est occupé.",
        "La lettura funziona solo se è attivata, circa una volta al secondo, e si mette in pausa da sola quando il Pi è occupato.",
        "I vegn mo legì, sch’igl è activà, circa ina giada per secunda, e quai fa da sez pausa, cura ch’il Pi ha bler da far."),
    "Read QR cards (experimental)": ("QR-Karten lesen (experimentell)", "Lire les cartes QR (expérimental)", "Leggere le carte QR (sperimentale)",
                                     "Leger cartas QR (experimental)"),
    "with the head camera": ("mit der Kopf-Kamera", "avec la caméra de tête", "con la telecamera della testa", "cun la camera dal chau"),
    "with the wide-angle camera": ("mit der Weitwinkel-Kamera", "avec la caméra grand angle", "con la telecamera grandangolare", "cun la camera da grond angul"),
    "Photo of every use in the history": ("Foto jeder Benutzung im Verlauf", "Photo de chaque utilisation dans l’historique", "Foto di ogni uso nella cronologia",
                                          "Foto da mintga utilisaziun en l’istorgia"),
    "Looks per second": ("Blicke pro Sekunde", "Regards par seconde", "Sguardi al secondo", "Egliadas per secunda"),
    "Cooldown per card (s)": ("Sperrzeit pro Karte (s)", "Délai par carte (s)", "Pausa per carta (s)", "Temp da bloccada per carta (s)"),
    "Pause above CPU (%)": ("Pause über CPU (%)", "Pause au-dessus de CPU (%)", "Pausa sopra CPU (%)", "Pausa sur CPU (%)"),
    "Feedback when a card is read": ("Rückmeldung, wenn eine Karte gelesen wird", "Retour quand une carte est lue", "Conferma quando una carta è letta",
                                     "Resposta, cura ch’ina carta vegn legida"),
    "spoken «Understood»": ("gesprochen «Verstanden»", "parlé «Compris»", "parlato «Capito»", "discurrì «Chapì»"),
    "short sound": ("kurzer Ton", "son court", "suono breve", "tun curt"),
    "nothing": ("nichts", "rien", "niente", "nagut"),
    "Understood": ("Verstanden", "Compris", "Capito", "Chapì"),
    "Pause": ("Pause", "Pause", "Pausa", "Pausa"),
    "Looking for cards": ("Sucht Karten", "Cherche des cartes", "Cerca carte", "Tschertga cartas"),
    "Off – nothing is read.": ("Aus – es wird nichts gelesen.", "Désactivé – rien n’est lu.", "Spento – non si legge niente.", "Stizzà – i na vegn legì nagut."),
    "Decoder": ("Decoder", "Décodeur", "Decodificatore", "Decoder"),
    "Last card": ("Letzte Karte", "Dernière carte", "Ultima carta", "Ultima carta"),
    "Last uses": ("Letzte Benutzungen", "Dernières utilisations", "Ultimi usi", "Ultimas utilisaziuns"),
    "Settings → Cameras & head → QR command cards": ("Einstellungen → Kameras & Kopf → QR-Befehls-Karten", "Réglages → Caméras et tête → Cartes de commande QR",
                                                    "Impostazioni → Telecamere e testa → Carte di comando QR", "Configuraziuns → Cameras e chau → Cartas da cumond QR"),
    "Open the card workshop": ("Karten-Werkstatt öffnen", "Ouvrir l’atelier des cartes", "Aprire il laboratorio delle carte", "Avrir l’ufficina da cartas"),
    "cards": ("Karten", "cartes", "carte", "cartas"),
    "Push message": ("Push-Nachricht", "Message push", "Messaggio push", "Messadi push"),
    "Read aloud": ("Vorlesen", "Lire à haute voix", "Leggere ad alta voce", "Leger ad aulta vusch"),
    "Note with photo": ("Notiz mit Foto", "Note avec photo", "Nota con foto", "Notizia cun foto"),
    "Start a recording": ("Aufnahme starten", "Démarrer un enregistrement", "Avviare una registrazione", "Cumenzar ina registraziun"),
    "Light on / off": ("Licht ein / aus", "Lumière on / off", "Luce on / off", "Glisch en / ora"),
    "Relay on / off": ("Relais ein / aus", "Relais on / off", "Relè on / off", "Relais en / ora"),
    "Head to a position": ("Kopf auf Position", "Tête vers une position", "Testa in una posizione", "Chau sin ina posiziun"),
    "Switch profile": ("Profil wechseln", "Changer de profil", "Cambiare profilo", "Midar profil"),
    "Text of the push message": ("Text der Push-Nachricht", "Texte du message push", "Testo del messaggio push", "Text dal messadi push"),
    "Text to read aloud": ("Text zum Vorlesen", "Texte à lire", "Testo da leggere", "Text da leger"),
    "Text of the note": ("Text der Notiz", "Texte de la note", "Testo della nota", "Text da la notizia"),
    "with the photo of the camera": ("mit dem Foto der Kamera", "avec la photo de la caméra", "con la foto della telecamera", "cun la foto da la camera"),
    "Duration": ("Dauer", "Durée", "Durata", "Durada"),
    "Which light": ("Welches Licht", "Quelle lumière", "Quale luce", "Tge glisch"),
    "On or off": ("Ein oder aus", "Allumer ou éteindre", "Acceso o spento", "En u ora"),
    "Relay": ("Relais", "Relais", "Relè", "Relais"),
    "Position": ("Position", "Position", "Posizione", "Posiziun"),
    "Mode": ("Modus", "Mode", "Modalità", "Modus"),
    "No relay set up yet (Settings → Extra devices → Relays).": ("Noch kein Relais eingerichtet (Einstellungen → Zusatzgeräte → Relais).",
                                                                  "Pas encore de relais (Réglages → Appareils supplémentaires → Relais).",
                                                                  "Ancora nessun relè (Impostazioni → Dispositivi extra → Relè).",
                                                                  "Anc nagin relais (Configuraziuns → Apparats supplementars → Relais)."),
    "No saved position yet (Teach-in under Head).": ("Noch keine gespeicherte Position (Teach-in beim Kopf).", "Pas encore de position enregistrée (apprentissage sous Tête).",
                                                     "Ancora nessuna posizione salvata (apprendimento sotto Testa).", "Anc nagina posiziun memorisada (Teach-in tar il chau)."),
    "A card never switches the protection off (no «Transport / rest»).": ("Eine Karte schaltet den Schutz nie aus (kein «Transport / Ruhe»).",
                                                                          "Une carte ne désactive jamais la protection (pas de «Transport / repos»).",
                                                                          "Una carta non spegne mai la protezione (niente «Trasporto / riposo»).",
                                                                          "Ina carta na stizza mai la protecziun (nagin «Transport / ruaus»)."),
    "QR code {m} × {m} modules · reads at about {a} cm (postcard) / {b} m (A4) – estimate from a simulation": (
        "QR-Code {m} × {m} Module · liest sich auf ca. {a} cm (Postkarte) / {b} m (A4) – Schätzung aus einer Simulation",
        "Code QR {m} × {m} modules · se lit à env. {a} cm (carte postale) / {b} m (A4) – estimation d’une simulation",
        "Codice QR {m} × {m} moduli · si legge a circa {a} cm (cartolina) / {b} m (A4) – stima da una simulazione",
        "Code QR {m} × {m} moduls · sa lascha leger sin ca. {a} cm (carta postala) / {b} m (A4) – stimaziun d’ina simulaziun"),
    "Text in the code: shorter distance, a shorter text reads further.": (
        "Text im Code: kürzerer Abstand, ein kürzerer Text reicht weiter.", "Texte dans le code : distance plus courte, un texte plus court se lit de plus loin.",
        "Testo nel codice: distanza più breve, un testo più corto si legge da più lontano.", "Text en il code: distanza pli curta, in text pli curt tanscha pli lunsch."),
    "Where is the text?": ("Wo steht der Text?", "Où est le texte ?", "Dove sta il testo?", "Nua stat il text?"),
    "Text on the MoveEye (recommended)": ("Text auf dem MoveEye (empfohlen)", "Texte sur le MoveEye (recommandé)", "Testo sul MoveEye (consigliato)", "Text sin il MoveEye (recumandà)"),
    "Text in the code": ("Text im Code", "Texte dans le code", "Testo nel codice", "Text en il code"),
    "The text is inside the QR code: the code gets bigger and reads only from closer; to change the text you print a new card.": (
        "Der Text steht im QR-Code: der Code wird grösser und lässt sich nur von näher lesen; für einen anderen Text druckst du eine neue Karte.",
        "Le texte est dans le code QR : le code devient plus grand et ne se lit que de plus près ; pour changer le texte, tu imprimes une nouvelle carte.",
        "Il testo è nel codice QR: il codice diventa più grande e si legge solo da più vicino; per cambiare il testo stampi una nuova carta.",
        "Il text stat en il code QR: il code vegn pli grond e sa lascha leger mo da pli datiers; per in auter text stampas ti ina nova carta."),
    "The code stays small and reads from further away; you can change the text later without printing again.": (
        "Der Code bleibt klein und lässt sich von weiter weg lesen; den Text kannst du später ändern, ohne neu zu drucken.",
        "Le code reste petit et se lit de plus loin ; tu peux changer le texte plus tard sans réimprimer.",
        "Il codice resta piccolo e si legge da più lontano; puoi cambiare il testo più tardi senza ristampare.",
        "Il code resta pitschen e sa lascha leger da pli lunsch; il text pos ti midar pli tard senza stampar danovamain."),
    "Change the text": ("Text ändern", "Changer le texte", "Cambiare il testo", "Midar il text"),
    "New text (the printed card stays valid):": ("Neuer Text (die gedruckte Karte bleibt gültig):", "Nouveau texte (la carte imprimée reste valable) :",
                                                 "Nuovo testo (la carta stampata resta valida):", "Nov text (la carta stampada resta valaivla):"),
    "Text changed – no new print needed.": ("Text geändert – kein neuer Druck nötig.", "Texte changé – pas besoin de réimprimer.",
                                            "Testo cambiato – non serve ristampare.", "Text midà – i na dovra nagin nov stampar."),
    "this card has no text": ("diese Karte hat keinen Text", "cette carte n’a pas de texte", "questa carta non ha testo", "questa carta n’ha nagin text"),
    "the text is in the code - make a new card": ("der Text steht im Code – erstelle eine neue Karte", "le texte est dans le code – crée une nouvelle carte",
                                                  "il testo è nel codice – crea una nuova carta", "il text stat en il code – crea ina nova carta"),
    "Print": ("Drucken", "Imprimer", "Stampare", "Stampar"),
    "Close": ("Schliessen", "Fermer", "Chiudi", "Serrar"),
    "Try out": ("Ausprobieren", "Essayer", "Provare", "Empruvar"),
    "Revoke card": ("Sperren", "Bloquer", "Bloccare", "Bloccar"),
    "Allow again": ("Wieder freigeben", "Réautoriser", "Riattivare", "Puspè permetter"),
    "Delete": ("Löschen", "Supprimer", "Eliminare", "Stizzar"),
    "Delete this card? Printed copies stop working.": ("Diese Karte löschen? Gedruckte Exemplare wirken dann nicht mehr.",
                                                       "Supprimer cette carte ? Les exemplaires imprimés ne marcheront plus.",
                                                       "Eliminare questa carta? Le copie stampate non funzioneranno più.",
                                                       "Stizzar questa carta? Exemplars stampads na funcziunan lura betg pli."),
    "No cards yet.": ("Noch keine Karten.", "Pas encore de cartes.", "Ancora nessuna carta.", "Anc naginas cartas."),
    "card revoked": ("gesperrt", "bloquée", "bloccata", "bloccada"),
    "print again (new key)": ("neu drucken (neuer Schlüssel)", "réimprimer (nouvelle clé)", "ristampare (nuova chiave)", "stampar danovamain (nova clav)"),
    "made on": ("erstellt", "créée le", "creata il", "creada ils"),
    "last used": ("zuletzt benutzt", "dernière utilisation", "ultimo uso", "utilisada l’ultima giada"),
    "never used": ("noch nie benutzt", "jamais utilisée", "mai usata", "anc mai utilisada"),
    "about {a} m": ("etwa {a} m", "env. {a} m", "circa {a} m", "circa {a} m"),
    "Really make ALL printed cards invalid? They stop working at once; you can print them again.": (
        "Wirklich ALLE gedruckten Karten ungültig machen? Sie wirken sofort nicht mehr; du kannst sie neu drucken.",
        "Vraiment rendre TOUTES les cartes imprimées invalides ? Elles cessent aussitôt de fonctionner ; tu peux les réimprimer.",
        "Rendere davvero non valide TUTTE le carte stampate? Smettono subito di funzionare; puoi ristamparle.",
        "Propi far nunvalaivlas TUT las cartas stampadas? Ellas na funcziunan immediat betg pli; ti las pos stampar danovamain."),
    "New key – print the cards again.": ("Neuer Schlüssel – Karten neu drucken.", "Nouvelle clé – réimprime les cartes.", "Nuova chiave – ristampa le carte.",
                                         "Nova clav – stampar danovamain las cartas."),
    "Please confirm.": ("Bitte bestätigen.", "Merci de confirmer.", "Per favore conferma.", "Per plaschair confermar."),
    "This card is revoked.": ("Diese Karte ist gesperrt.", "Cette carte est bloquée.", "Questa carta è bloccata.", "Questa carta è bloccada."),
    "QR card": ("QR-Karte", "Carte QR", "Carta QR", "Carta QR"),
    "foreign card": ("fremde Karte", "carte étrangère", "carta estranea", "carta estra"),
    "Postcard 10 × 15 cm": ("Postkarte 10 × 15 cm", "Carte postale 10 × 15 cm", "Cartolina 10 × 15 cm", "Carta postala 10 × 15 cm"),
    "Print at 100 % (no «fit to page»). Cut along the dashed line. Card and phone screen work the same.": (
        "Mit 100 % drucken (nicht «an Seite anpassen»). Entlang der gestrichelten Linie ausschneiden. Karte und Handy-Bildschirm wirken gleich.",
        "Imprimer à 100 % (pas «ajuster à la page»). Découper le long de la ligne pointillée. Carte et écran du téléphone fonctionnent pareil.",
        "Stampa al 100 % (non «adatta alla pagina»). Ritaglia lungo la linea tratteggiata. Carta e schermo del telefono funzionano allo stesso modo.",
        "Stampar cun 100 % (betg «adattar a la pagina»). Tagliar ora lung la lingia puntada. Carta e visur dal telefonin funcziunan tuttina."),
    "Push": ("Push", "Push", "Push", "Push"),
    "photo": ("Foto", "photo", "foto", "foto"),
    "Recording {s} s": ("Aufnahme {s} s", "Enregistrement {s} s", "Registrazione {s} s", "Registraziun {s} s"),
    "Head to": ("Kopf zu", "Tête vers", "Testa verso", "Chau vers"),
    "Head view": ("Kopf", "Tête", "Testa", "Chau"),
    "Wide view": ("Weitwinkel", "Grand angle", "Grandangolo", "Grond angul"),
    # pauses and errors (tr / tr_err)
    "off": ("aus", "désactivé", "spento", "ora"),
    "on": ("ein", "activé", "acceso", "en"),
    "no camera chosen": ("keine Kamera gewählt", "aucune caméra choisie", "nessuna telecamera scelta", "nagina camera tschernida"),
    "no cards yet": ("noch keine Karten", "pas encore de cartes", "ancora nessuna carta", "anc naginas cartas"),
    "simulation": ("Simulation", "simulation", "simulazione", "simulaziun"),
    "tool mode": ("Werkzeug-Modus", "mode outil", "modalità strumento", "modus d’utensil"),
    "battery saver": ("Akku sparen", "économie de batterie", "risparmio batteria", "spargnar accu"),
    "CPU busy": ("CPU ausgelastet", "CPU occupé", "CPU occupata", "CPU occupada"),
    "detection is slow": ("Erkennung ist langsam", "la détection est lente", "il rilevamento è lento", "l’identificaziun è plauna"),
    "unknown command": ("unbekannter Befehl", "commande inconnue", "comando sconosciuto", "cumond nunenconuschent"),
    "unknown card": ("unbekannte Karte", "carte inconnue", "carta sconosciuta", "carta nunenconuschenta"),
    "the name is empty": ("der Name fehlt", "le nom manque", "manca il nome", "il num manca"),
    "the text is empty": ("der Text fehlt", "le texte manque", "manca il testo", "il text manca"),
    "the text is too long": ("der Text ist zu lang", "le texte est trop long", "il testo è troppo lungo", "il text è memia lung"),
    "too many cards": ("zu viele Karten", "trop de cartes", "troppe carte", "memia bleras cartas"),
    "unknown profile": ("unbekanntes Profil", "profil inconnu", "profilo sconosciuto", "profil nunenconuschent"),
    "This text contains a password, an access code or a Wi-Fi name - not allowed on a card.": (
        "Dieser Text enthält ein Passwort, einen Zugangscode oder einen WLAN-Namen – auf einer Karte nicht erlaubt.",
        "Ce texte contient un mot de passe, un code d’accès ou un nom de Wi-Fi – interdit sur une carte.",
        "Questo testo contiene una password, un codice di accesso o un nome di Wi-Fi – non consentito su una carta.",
        "Quest text cuntegna in pled-clav, in code d’access u in num da WLAN – betg permess sin ina carta."),
    "this would switch the protection off - not by card": ("das würde den Schutz ausschalten – nicht per Karte", "cela désactiverait la protection – pas par carte",
                                                           "questo spegnerebbe la protezione – non con una carta", "quai stizzass la protecziun – betg cun ina carta"),
    "push messages are not set up - only in the message list": ("Push-Nachrichten sind nicht eingerichtet – nur in der Liste «Nachrichten»",
                                                                "les messages push ne sont pas configurés – seulement dans la liste des messages",
                                                                "i messaggi push non sono configurati – solo nell’elenco dei messaggi",
                                                                "messadis push n’èn betg endrizzads – mo en la glista dals messadis"),
    "no camera loop": ("die Kamera läuft nicht", "la caméra ne tourne pas", "la telecamera non è attiva", "la camera na lavura betg"),
    "no camera picture yet": ("noch kein Kamerabild", "pas encore d’image de caméra", "ancora nessuna immagine della telecamera", "anc nagin maletg da la camera"),
    "could not save the picture": ("Bild konnte nicht gespeichert werden", "l’image n’a pas pu être enregistrée", "impossibile salvare l’immagine", "il maletg n’ha betg pudì vegnir memorisà"),
    "busy": ("besetzt", "occupé", "occupato", "occupà"),
    # the log (Protokoll)
    "QR card: foreign card ignored": ("QR-Karte: fremde Karte ignoriert", "Carte QR : carte étrangère ignorée", "Carta QR: carta estranea ignorata",
                                      "Carta QR: carta estra ignorada"),
    "QR card: deleted card ignored": ("QR-Karte: gelöschte Karte ignoriert", "Carte QR : carte supprimée ignorée", "Carta QR: carta eliminata ignorata",
                                      "Carta QR: carta stizzada ignorada"),
}
for _k, _v in _HX_QRK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_QRK_DE = {_k: DE.get(_k, _v[0]) for _k, _v in _HX_QRK.items()}
_QRK_DE.update({k: DE.get(k, k) for k in ("No connection to MoveEye.", "Only for the administrator", "Detection profile", "Profile")})
WEB_PAGE = WEB_PAGE.replace("</body>", QRK_PANEL_JS.replace("/*QRKPDE*/{}", json.dumps(
    {k: _QRK_DE[k] for k in ("Open the card workshop", "Pause", "Looking for cards", "Off – nothing is read.", "cards", "Last card", "QR command cards")},
    ensure_ascii=False), 1) + "</body>", 1)

# ---- the manual: a section «QR-Befehls-Karten» -------------------------------------------------------------------------------------
_HELP_QRK = {
    "de": ('<section id="qrkarten" data-icon="▦"><h2>QR-Befehls-Karten (experimentell)</h2><ul>'
           '<li><b>Was:</b> eine gedruckte Karte (oder ein Handy-Bildschirm) mit QR-Code vor die Kamera halten – MoveEye macht, was darauf steht: '
           'Push-Nachricht (Text aus der Karte, auf Wunsch mit Foto), Text vorlesen, Notiz mit Foto im Verlauf, Aufnahme starten, Licht oder Relais ein / aus, '
           'Kopf auf eine gespeicherte Position, Profil wechseln. Den Schutz ausschalten kann eine Karte nie.</li>'
           '<li><b>Einschalten:</b> Einstellungen → Kameras &amp; Kopf → «QR-Befehls-Karten» (ab Werk aus, nur der Administrator). Gelesen wird mit der Kopf- und / oder '
           'der Weitwinkel-Kamera (nie mit dem Wärmebild), etwa einmal pro Sekunde; bei viel Arbeit des Pi, im Akku-Sparen und in der Simulation macht es Pause.</li>'
           '<li><b>Karten-Werkstatt:</b> Mehr → «▦ Karten-Werkstatt»: Befehl wählen, Text eingeben, Karte drucken (Postkarte 10 × 15 cm, A5 oder A4 – mit der '
           'Druckfunktion des Browsers, 100 %) oder als PNG / SVG speichern. Die Liste zeigt Name, Befehl, erstellt, zuletzt benutzt; Karten sperren, freigeben, löschen, ausprobieren.</li>'
           '<li><b>Wo steht der Text?</b> «Text auf dem MoveEye» (empfohlen): der Code bleibt klein (25 × 25) und liest sich von weiter weg, den Text kannst du später ändern, ohne neu zu drucken. '
           '«Text im Code»: der Text steht im QR-Code selbst – grösserer Code, kürzerer Abstand, ein anderer Text braucht eine neue Karte.</li>'
           '<li><b>Sicher:</b> nur Karten dieses MoveEye gelten (eine Prüfnummer mit einem geheimen Schlüssel des Geräts). Fremde oder veränderte Codes werden ignoriert '
           '(eine kurze Zeile im Protokoll). «Alle Karten ungültig machen» erzeugt einen neuen Schlüssel – danach jede Karte neu drucken. Auf einer Karte stehen keine Passwörter und keine WLAN-Namen.</li>'
           '<li><b>Rückmeldung:</b> «Verstanden» (oder ein Ton), ein grüner Rahmen um die Karte im Live-Bild; dieselbe Karte wirkt erst wieder, wenn sie kurz weg war '
           '(Sperrzeit). Jede Benutzung steht im Protokoll und mit Foto in Verlauf → Aufnahmen.</li>'
           '<li><b>Abstand:</b> geschätzt aus einer Simulation: Postkarte bei Tag etwa 0,8 m vor der Kopf-Kamera (Text im Code: 0,3–0,6 m), Weitwinkel näher; A4 etwa doppelt so weit. Kurze Texte reichen weiter. '
           'Nachts mit Infrarot kürzer; ein Handy-Bildschirm spiegelt im Infrarot oft.</li></ul></section>\n'),
    "en": ('<section id="qrkarten" data-icon="▦"><h2>QR command cards (experimental)</h2><ul>'
           '<li><b>What:</b> hold a printed card (or a phone screen) with a QR code in front of the camera – MoveEye does what is on it: push message (text from the card, '
           'optionally with a photo), read a text aloud, a note with a photo in the history, start a recording, light or relay on / off, head to a saved position, switch profile. '
           'A card can never switch the protection off.</li>'
           '<li><b>Switch on:</b> Settings → Cameras &amp; head → «QR command cards» (off by default, administrator only). Head and / or wide-angle camera (never thermal), '
           'about once a second; it pauses when the Pi is busy, in battery saving and in the simulation.</li>'
           '<li><b>Card workshop:</b> More → «▦ Card workshop»: choose the command, type the text, print the card (postcard 10 × 15 cm, A5 or A4 – with the browser’s print, 100 %) '
           'or save it as PNG / SVG. The list shows name, command, made, last used; revoke, allow again, delete, try out.</li>'
           '<li><b>Where is the text?</b> «Text on the MoveEye» (recommended): the code stays small (25 × 25) and reads from further away; you can change the text later without printing again. '
           '«Text in the code»: the text is inside the QR code – a bigger code, a shorter distance, another text needs a new card.</li>'
           '<li><b>Safe:</b> only cards of this MoveEye count (a check number with a secret key of the device). Foreign or changed codes are ignored (a short log line). '
           '«Make all cards invalid» makes a new key – print every card again afterwards. No passwords and no Wi-Fi names on a card.</li>'
           '<li><b>Feedback:</b> «Understood» (or a sound) and a green frame around the card in the live picture; the same card works again only after it was away for a moment '
           '(cooldown). Every use is in the log and, with a photo, in History → Recordings.</li>'
           '<li><b>Distance:</b> estimated from a simulation: postcard by day about 0.8 m in front of the head camera (text in the code: 0.3–0.6 m), wide angle closer; A4 about twice as far. Short texts read further. '
           'Shorter at night with infrared; a phone screen often reflects in infrared.</li></ul></section>\n'),
    "fr": ('<section id="qrkarten" data-icon="▦"><h2>Cartes de commande QR (expérimental)</h2><ul><li>Tenir une carte avec un code QR devant la caméra : MoveEye exécute '
           'la commande (push, lecture à voix haute, note avec photo, enregistrement, lumière / relais, position de la tête, profil). Jamais désactiver la protection. '
           'Activer : Réglages → Caméras et tête. Créer et imprimer : Plus → Atelier des cartes. Seules les cartes de ce MoveEye comptent ; une nouvelle clé invalide toutes les cartes. '
           'Distance (simulation) : carte postale env. 0,8 m, A4 env. le double ; «texte dans le code» : plus court, texte non modifiable sans réimprimer.</li></ul></section>\n'),
    "it": ('<section id="qrkarten" data-icon="▦"><h2>Carte di comando QR (sperimentale)</h2><ul><li>Tenere una carta con un codice QR davanti alla telecamera: MoveEye esegue '
           'il comando (push, lettura ad alta voce, nota con foto, registrazione, luce / relè, posizione della testa, profilo). Mai spegnere la protezione. '
           'Attivare: Impostazioni → Telecamere e testa. Creare e stampare: Altro → Laboratorio delle carte. Valgono solo le carte di questo MoveEye; una nuova chiave invalida tutte le carte. '
           'Distanza (simulazione): cartolina circa 0,8 m, A4 circa il doppio; «testo nel codice»: più corta, testo non modificabile senza ristampare.</li></ul></section>\n'),
    "rm": ('<section id="qrkarten" data-icon="▦"><h2>Cartas da cumond QR (experimental)</h2><ul><li>Tegnair ina carta cun code QR davant la camera: MoveEye exequescha '
           'il cumond (push, leger ad aulta vusch, notizia cun foto, registraziun, glisch / relais, posiziun dal chau, profil). Mai stizzar la protecziun. '
           'Activar: Configuraziuns → Cameras e chau. Crear e stampar: Dapli → Ufficina da cartas. I valan mo cartas da quest MoveEye; ina nova clav fa nunvalaivlas tut las cartas. '
           'Distanza (simulaziun): carta postala circa 0,8 m, A4 circa il dubel; «text en il code»: pli curta, text betg midabel senza stampar danovamain.</li></ul></section>\n'),
}


def _help_qrk(doc, lang):
    if 'id="qrkarten"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_QRK[lang] + doc[i:] if i >= 0 else doc


_hp_en_qrk = HELP_PAGE.find('<div lang="en">')
if _hp_en_qrk > 0:
    HELP_PAGE = _help_qrk(HELP_PAGE[:_hp_en_qrk], "de") + _help_qrk(HELP_PAGE[_hp_en_qrk:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_qrk(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def qrk_selftest():
    keep = {k: json.loads(json.dumps(CFG.get(k))) for k in QRK_DEF}
    sv, lg = save_settings, log_event
    keep_q = {k: (dict(QRK[k]) if isinstance(QRK[k], dict) else QRK[k]) for k in ("seen", "show", "log_t", "last")}
    try:
        globals()["save_settings"] = lambda *a, **k: None
        globals()["log_event"] = lambda *a, **k: None
        CFG.update(qrk_cards=[], qrk_secret="")
        card, err = qrk_create({"cmd": "L", "name": "Licht an", "light": "white", "on": True}, "selftest")
        assert card and not err and re.fullmatch(r"[0-9a-f]{64}", CFG["qrk_secret"]), err
        pl = qrk_payload(card)
        assert pl.startswith("M1" + card["id"] + "L") and len(pl) == QRK_HEAD and qrk_qr_size(pl)[1] == 25, pl   # values on the device
        assert CFG["qrk_secret"] not in pl and CFG["qrk_secret"][:10] not in pl
        assert qrk_check(pl) == ("ok", qrk_card(card["id"]))
        bad = pl[:7] + "Y" + pl[8:]                             # another command with the old check number
        assert qrk_check(bad)[0] == "foreign" and qrk_check("https://example.org/")[0] == "foreign" and qrk_check("")[0] == "foreign"
        assert qrk_check(pl + "w0")[0] == "foreign", "values added to a short card"
        other = QRK_PREFIX + card["id"] + "L" + qrk_mac(card["id"], "L", "", "ab" * 32)
        assert qrk_check(other)[0] == "foreign", "a card of another MoveEye"
        dev, _e = qrk_create({"cmd": "P", "name": "Essen", "text": "Essen ist fertig", "photo": True}, "selftest")
        inc, _e = qrk_create({"cmd": "S", "name": "Ansage", "text": "Willkommen", "tc": True}, "selftest")
        pd, pi = qrk_payload(dev), qrk_payload(inc)
        assert len(pd) == QRK_HEAD and pi.endswith("Willkommen") and qrk_check(pd)[0] == "ok" and qrk_check(pi)[0] == "ok"
        assert qrk_set_text(dev["id"], {"text": "Kaffee ist fertig"}) == (True, "") and qrk_payload(qrk_card(dev["id"])) == pd
        assert qrk_check(pd)[1]["p"] == "1Kaffee ist fertig", "text changed on the device: the printed card stays valid"
        assert qrk_set_text(inc["id"], {"text": "x"})[0] is False and qrk_set_text(card["id"], {"text": "x"})[0] is False
        assert qrk_check(pi[:-1] + "m")[0] == "foreign", "text in the code changed"
        assert qrk_check(pi[:QRK_HEAD])[0] == "foreign" and qrk_check(pd + "1Hallo")[0] == "foreign", "the other form of a card never counts"
        for _c in (dev, inc):
            qrk_edit("revoke", _c["id"], "selftest")
        assert qrk_check(pd)[0] == "revoked" and qrk_check(pi)[0] == "revoked"
        img = cv2.imdecode(np.frombuffer(qr_png(pl, 6), np.uint8), cv2.IMREAD_COLOR)
        img = cv2.copyMakeBorder(img, 60, 60, 120, 120, cv2.BORDER_CONSTANT, value=(140, 140, 140))
        txt, pts = qrk_decode(img)
        assert txt == pl and pts and len(pts) == 4, (txt, pts)
        ran = []
        globals()["qrk_spawn"] = lambda c, im, cam: ran.append(c["id"])
        try:
            t0 = 1000.0
            QRK["seen"].clear()
            assert qrk_seen("head", pl, pts, img, now=t0) == "run"
            assert qrk_seen("head", pl, pts, img, now=t0 + 1) == "hold", "held in view: once"
            assert qrk_seen("head", pl, pts, img, now=t0 + 2.5) == "hold"
            assert qrk_seen("head", pl, pts, img, now=t0 + 6) == "hold", "away for 3.5 s but the cooldown (10 s) is not over"
            assert qrk_seen("head", pl, pts, img, now=t0 + 20) == "run", "away and cooldown over"
            qrk_edit("revoke", card["id"], "selftest")
            assert qrk_seen("head", pl, pts, img, now=t0 + 60) == "revoked"
            qrk_edit("unrevoke", card["id"], "selftest")
            assert qrk_check(pl)[0] == "ok"
            qrk_rotate("selftest")
            assert qrk_check(pl)[0] == "foreign" and qrk_card_json(qrk_card(card["id"]))["reprint"], "new key: all old cards invalid"
            assert qrk_check(qrk_payload(qrk_card(card["id"])))[0] == "ok", "printed again with the new key"
        finally:
            globals()["qrk_spawn"] = _qrk_spawn_real
        assert len(ran) == 2, ran
        assert qrk_create({"cmd": "P", "name": "x", "text": "WIFI:T:WPA;S:Zelt;P:geheim123;;"})[0] is None
        assert qrk_create({"cmd": "P", "name": "x", "text": "Das Passwort ist 1234"})[0] is None
        assert qrk_create({"cmd": "S", "name": "x", "text": "ä" * 60})[1] == "the text is too long"
        assert qrk_create({"cmd": "F", "name": "x", "profile": "m:transport"})[1] == "unknown profile", "never «Ruhe» by card"
        assert qrk_make_param("R", {"secs": 99999})[0] == str(QRK_REC_MAX)
        CFG["qrk_on"] = False
        assert qrk_pause_reason() == "off"
        assert "qrk_secret" in USER_SETTINGS_DENY and "qrk_on" in USER_SETTINGS_DENY and "/api/qrk" in APPKEY_DENY_PATHS
        assert not role_allows("family", "/karten", "GET", {}) and not role_allows("family", "/api/qrk", "POST", {"action": "create"})
        assert '{sec: "QR command cards"' in WEB_PAGE and "window.qrkPanel" in WEB_PAGE and 'id="qrkarten"' in HELP_PAGE
        assert tr("Card workshop", "de") == "Karten-Werkstatt" and tr("Understood", "rm") == "Chapì" and tr("QR card: foreign card ignored", "de").endswith("ignoriert")
        assert "<svg" in qrk_card_svg(qrk_card(card["id"])) and qrk_card_png(qrk_card(card["id"]))[:4] == b"\x89PNG"
    finally:
        globals()["save_settings"] = sv
        globals()["log_event"] = lg
        CFG.update(keep)
        for k, v in keep_q.items():
            if isinstance(QRK[k], dict):
                QRK[k].clear(); QRK[k].update(v)
            else:
                QRK[k] = v
    return "check number (own / changed / other device), text on the device / in the code, read a code, cooldown, revoke, new key, no secrets on a card, rights, page hooks"


_qrk_spawn_real = qrk_spawn
SELFTEST_EXTRA.append(("QR command cards «▦ Karten-Werkstatt» (639zzp)", qrk_selftest))
