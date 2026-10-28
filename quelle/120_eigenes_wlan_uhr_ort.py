#@ Motion Watch – Teil 120: eigenes WLAN, Uhr vom Handy, Ort (GPS) vom Handy. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Own Wi-Fi of the Pi (access point / hotspot): the phone connects directly to the Pi - works without any mobile network.
#   NetworkManager connection "MotionWatch-Hotspot" (WPA2, 2.4 GHz for range). The page is then at http://10.42.0.1:<port>/
# ----------------------------------------------------------------------------
HOTSPOT_CON = "MotionWatch-Hotspot"
_PW_ALPHA = "abcdefghjkmnpqrstuvwxyz23456789"           # no 0/O, 1/l/i: easy to type on a phone


def hotspot_password():
    pw = CFG["hotspot_password"]
    if not (isinstance(pw, str) and 8 <= len(pw) <= 63):
        import secrets
        pw = "".join(secrets.choice(_PW_ALPHA) for _ in range(10))
        CFG["hotspot_password"] = pw; save_settings()
    return pw


def _nm_active_names():
    code, out, _e = _run(["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"], 10)
    return [_nm_split(l)[0] for l in out.splitlines()] if code == 0 else []


def _hotspot_clients(iface):
    code, out, _e = _run(["iw", "dev", iface, "station", "dump"], 5)
    return sum(1 for l in out.splitlines() if l.startswith("Station")) if code == 0 else 0


def hotspot_refresh():
    b = wifi_backend()
    on = b == "nm" and HOTSPOT_CON in _nm_active_names()
    ap_if = WIFI.get("ap_iface") or WIFI["iface"]
    STATE["hotspot"] = {"on": on, "ssid": CFG["hotspot_ssid"] if on else "", "clients": _hotspot_clients(ap_if) if on else 0,
                        "ip": wifi_ip(ap_if) if on else "", "repeater": bool(on and DUAL["on"]), "busy": WIFI.get("hs_busy", False), "available": b == "nm", "msg": WIFI.get("hs_msg", "")}
    return STATE["hotspot"]


def hotspot_set(on, persist=True):
    """Switch the own Wi-Fi on / off (blocking, a few seconds). Off = NetworkManager goes back to the known networks."""
    b = wifi_backend()
    if b != "nm":
        return False, "the own Wi-Fi needs NetworkManager (Raspberry Pi OS Bookworm or newer)"
    iface, ssid = (WIFI.get("ap_iface") if DUAL["on"] else "") or WIFI["iface"], CFG["hotspot_ssid"] or "MotionWatch"
    with _WIFI_LOCK:
        if on:
            pw = hotspot_password()
            code, out, _e = _run(["nmcli", "-t", "-f", "NAME", "connection", "show"], 10)
            exists = HOTSPOT_CON in [_nm_split(l)[0] for l in out.splitlines()]
            sec = ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", pw, "wifi-sec.proto", "rsn", "wifi-sec.pairwise", "ccmp", "wifi-sec.group", "ccmp"]
            if exists:
                code, out, err = _run(["nmcli", "connection", "modify", "id", HOTSPOT_CON, "802-11-wireless.ssid", ssid,
                                       "connection.interface-name", iface] + sec, 20)
            else:
                code, out, err = _run(["nmcli", "connection", "add", "type", "wifi", "ifname", iface, "con-name", HOTSPOT_CON, "autoconnect", "no",
                                       "ssid", ssid, "802-11-wireless.mode", "ap", "802-11-wireless.band", "bg", "ipv4.method", "shared"] + sec, 20)
            if code == 0:
                code, out, err = _run(["nmcli", "--wait", "40", "connection", "up", "id", HOTSPOT_CON], 50)
        else:
            code, out, err = _run(["nmcli", "connection", "down", "id", HOTSPOT_CON], 30)
            if code != 0 and "not an active connection" in (err or "").lower():
                code = 0
    ok = code == 0
    if ok:
        if persist:
            CFG["hotspot_on"] = on; save_settings()
        log_event("sys", f"Own Wi-Fi «{ssid}» switched ON (page: {page_address('10.42.0.1')})" if on else "Own Wi-Fi switched OFF - back to the known networks")
    else:
        log_event("sys", f"Own Wi-Fi could not be switched {'on' if on else 'off'}: {_perm_hint(err)}")
    WIFI["refresh"] = True
    return ok, "" if ok else _perm_hint(err)


def hotspot_switch_later(on, delay=1.5):
    """In the background, a little later: the web page that asked must still get its answer before the network changes."""
    WIFI["hs_busy"] = True; WIFI["hs_msg"] = ""
    def work():
        time.sleep(delay)
        try:
            ok, err = hotspot_set(on)
            WIFI["hs_msg"] = "" if ok else err
        finally:
            WIFI["hs_busy"] = False
            try:
                hotspot_refresh()
            except Exception:
                pass
    threading.Thread(target=work, daemon=True).start()


# ----------------------------------------------------------------------------
# Clock from the phone: the Pi has no clock with a battery (except Pi 5 with battery). Without internet it starts with a
# wrong time, then schedules, sunset and the names of recordings are wrong. Every page sends the time of the phone.
# ----------------------------------------------------------------------------
TIME = {"last": 0.0}


def _ntp_synced():
    code, out, _e = _run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], 5)
    return code == 0 and out.strip() == "yes"


def _set_timezone(tz):
    if not (isinstance(tz, str) and re.fullmatch(r"[A-Za-z_]+(/[A-Za-z0-9_+\-]+){0,2}", tz) and os.path.isfile(os.path.join("/usr/share/zoneinfo", tz))):
        return ""
    code, out, _e = _run(["timedatectl", "show", "-p", "Timezone", "--value"], 5)
    if code != 0 or out.strip() == tz:
        return ""
    code, out, err = _run(["timedatectl", "set-timezone", tz], 10)
    if code == 0:
        try:
            time.tzset()
        except AttributeError:
            pass
        log_event("sys", f"Time zone set from the phone: {tz}")
        return f"time zone {tz}"
    return ""


def _set_clock(epoch):
    stamp = datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(os, "geteuid") and os.geteuid() == 0 and shutil.which("date"):
        code, out, err = _run(["date", "-s", "@%d" % int(epoch)], 10)
        return code == 0, err
    code, out, err = _run(["timedatectl", "set-time", stamp], 10)
    if code != 0 and "automatic time synchronization" in (err or "").lower():
        _run(["timedatectl", "set-ntp", "false"], 10)              # allowed to set by hand only while NTP is off ...
        code, out, err = _run(["timedatectl", "set-time", stamp], 10)
        _run(["timedatectl", "set-ntp", "true"], 10)               # ... and it takes over again as soon as there is internet
    return code == 0, err


# ---- location (GPS) from the phone: photos get EXIF GPS data, videos a location tag ----
GPS = {"lat": None, "lon": None, "acc": None, "t": 0.0}
GPSMOD = {"lat": None, "lon": None, "t": 0.0, "sats": None, "status": "off", "via": "", "anchor": None, "away": 0, "alarm_t": 0.0, "upd_t": 0.0}
GPS_DEFAULT = (47.37, 8.54)                      # the factory setting is not a real location


def gps_set(lat, lon, acc=None):
    """A position sent by the browser of a phone (only https pages may read the location)."""
    try:
        lat, lon = float(lat), float(lon); acc = float(acc) if acc is not None else None
    except (TypeError, ValueError):
        return False, "invalid value"
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or not (math.isfinite(lat) and math.isfinite(lon)):
        return False, "invalid value"
    if not CFG["gps_phone"]:
        return False, "off"
    first = GPS["lat"] is None
    GPS.update(lat=round(lat, 6), lon=round(lon, 6), acc=round(acc) if acc is not None else None, t=time.time())
    if abs(lat - float(CFG["latitude"])) > 0.01 or abs(lon - float(CFG["longitude"])) > 0.01:     # ~1 km: new place
        CFG["latitude"], CFG["longitude"] = round(lat, 4), round(lon, 4); save_settings()
        log_event("sys", f"Location from the phone: {lat:.4f}, {lon:.4f}")
    elif first:
        log_event("sys", f"Location from the phone: {lat:.4f}, {lon:.4f}")
    return True, ""


def gps_now():
    """(lat, lon, source) for the pictures: the phone (the last 6 hours), otherwise the place in the settings
    (not the factory value), otherwise None."""
    if CFG["gpsmod_on"] and GPSMOD["lat"] is not None and time.time() - GPSMOD["t"] < 300:
        return GPSMOD["lat"], GPSMOD["lon"], "module"
    if CFG["gps_phone"] and GPS["lat"] is not None and time.time() - GPS["t"] < 6 * 3600:
        return GPS["lat"], GPS["lon"], "phone"
    lat, lon = float(CFG["latitude"]), float(CFG["longitude"])
    if (round(lat, 2), round(lon, 2)) != GPS_DEFAULT:
        return lat, lon, "fixed"
    return None


def gps_state():
    g = gps_now()
    if g and g[2] == "module":
        return {"lat": g[0], "lon": g[1], "src": "module", "age": int(time.time() - GPSMOD["t"]), "acc": None, "sats": GPSMOD["sats"]}
    return {"lat": g[0], "lon": g[1], "src": g[2], "age": int(time.time() - GPS["t"]) if g[2] == "phone" else None,
            "acc": GPS["acc"] if g[2] == "phone" else None} if g else None


def exif_gps(lat, lon):
    """A small EXIF block (APP1) with the GPS position - photo apps then show the picture on the map."""
    import struct

    def rat(v):
        v = abs(v); d = int(v); m = int((v - d) * 60); sec = round(((v - d) * 60 - m) * 60 * 1000)
        return struct.pack("<6I", d, 1, m, 1, sec, 1000)

    ifd0 = struct.pack("<H", 1) + struct.pack("<HHII", 0x8825, 4, 1, 26) + struct.pack("<I", 0)
    gps = struct.pack("<H", 5)
    gps += struct.pack("<HHI", 0x0000, 1, 4) + bytes((2, 3, 0, 0))
    gps += struct.pack("<HHI", 0x0001, 2, 2) + (b"N" if lat >= 0 else b"S") + b"\0\0\0"
    gps += struct.pack("<HHII", 0x0002, 5, 3, 92)
    gps += struct.pack("<HHI", 0x0003, 2, 2) + (b"E" if lon >= 0 else b"W") + b"\0\0\0"
    gps += struct.pack("<HHII", 0x0004, 5, 3, 116) + struct.pack("<I", 0)
    tiff = b"II*\0" + struct.pack("<I", 8) + ifd0 + gps + rat(lat) + rat(lon)
    body = b"Exif\0\0" + tiff
    return b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body


def gps_tag_jpg(path):
    """Add the GPS position to a saved JPEG (when wanted and known)."""
    g = gps_now() if CFG["gps_tag"] else None
    if not g:
        return
    try:
        with open(path, "rb") as f:
            data = f.read()
        if data[:2] != b"\xff\xd8" or b"Exif\0\0" in data[:64]:
            return
        tmp = path + ".gps"
        with open(tmp, "wb") as f:
            f.write(data[:2] + exif_gps(g[0], g[1]) + data[2:])
        os.replace(tmp, path)
    except OSError:
        pass


def gps_iso6709(g):
    return f"{g[0]:+08.4f}{g[1]:+09.4f}/"


def gps_tag_video(path):
    """Write the location into a finished MP4 (copied, not encoded again)."""
    g = gps_now() if CFG["gps_tag"] else None
    if not g or not shutil.which("ffmpeg") or not os.path.isfile(path):
        return
    name = os.path.basename(path); tmp = os.path.join(os.path.dirname(path), "gps_" + name)
    LIVE_RECS.add(name)
    try:
        r = subprocess.run((["nice", "-n", "10"] if shutil.which("nice") else []) + ["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-map", "0",
                           "-c", "copy", "-metadata", "location=" + gps_iso6709(g), "-metadata", "location-eng=" + gps_iso6709(g),
                           "-movflags", "+faststart", tmp], capture_output=True, timeout=600)
        if r.returncode == 0 and os.path.isfile(tmp) and os.path.getsize(tmp) > 1000:
            os.replace(tmp, path)
    except (OSError, subprocess.SubprocessError):
        pass
    finally:
        LIVE_RECS.discard(name)
        try:
            os.remove(tmp)
        except OSError:
            pass


HEALTH_ORDER = ("bad", "warn", "ok", "off")


QUICK_GUIDE = {
"de": ("Kurzanleitung", [
  ("⚡", "Aufstellen", ["Kamera auf den Platz richten, Temperaturfühler ausserhalb des Gehäuses.", "Powerbank anschliessen (Pi 5: 5 V / 5 A). Nach etwa 1 Minute ist alles bereit."]),
  ("📱", "Verbinden", ["Handy-Hotspot einschalten – der Pi verbindet sich selbst. Oder mit dem WLAN «MotionWatch» des Pi verbinden.", "Seite öffnen: im WLAN des Pi <b>http://10.42.0.1:5000</b>. Für Standort und Mikrofon die https-Seite nehmen.", "«🖨 QR-Codes zum Verbinden» (unter System) druckt die Codes zum Verbinden."]),
  ("🌙", "Am Abend", ["<b>«🌙 Heute Nacht bewachen»</b> antippen.", "Was unter «Fehlt noch» steht, erledigen.", "Während des Countdowns den Bereich verlassen."]),
  ("🚨", "Bei Alarm", ["Push-Nachricht antippen → Live-Bild ansehen.", "Sirene oder Licht über die Schnellschalter.", "War es nichts? In den Aufnahmen <b>👎 «War nichts»</b> antippen – das Programm schlägt dann bessere Einstellungen vor."]),
  ("☀", "Am Morgen", ["Nachtbericht lesen (Push-Nachricht, Standard 7 Uhr).", "Unscharf schalten, Powerbank laden.", "Im Tagebuch die Tiere der Nacht ansehen."]),
  ("🩺", "Wenn etwas nicht geht", ["Rote <b>🩺</b>-Anzeige oben antippen: jede Ampel sagt, was zu tun ist.", "Kein Bild → Kabel und Videoquelle prüfen. Keine Push-Nachricht → Internet / Hotspot prüfen.", "Alles Weitere: Reiter «Anleitung»."]),
]),
"en": ("Quick guide", [
  ("⚡", "Set up", ["Point the camera at the pitch; temperature sensor outside the housing.", "Connect the powerbank (Pi 5: 5 V / 5 A). After about 1 minute everything is ready."]),
  ("📱", "Connect", ["Switch on the phone hotspot – the Pi joins it by itself. Or join the Pi's Wi-Fi «MotionWatch».", "Open the page: in the Pi's Wi-Fi <b>http://10.42.0.1:5000</b>. For location and microphone use the https page.", "«🖨 QR codes for connecting» (under System) prints the codes."]),
  ("🌙", "In the evening", ["Tap <b>«🌙 Guard tonight»</b>.", "Fix what is listed under «Still missing».", "Leave the area during the countdown."]),
  ("🚨", "On an alarm", ["Tap the push message → watch the live picture.", "Siren or light with the quick switches.", "Was it nothing? In the recordings tap <b>👎 «Was nothing»</b> – the program then suggests better settings."]),
  ("☀", "In the morning", ["Read the night report (push message, 7 o'clock by default).", "Disarm, charge the powerbank.", "Look at the animals of the night in the diary."]),
  ("🩺", "If something does not work", ["Tap the red <b>🩺</b> badge at the top: every traffic light says what to do.", "No picture → check cable and video source. No push message → check internet / hotspot.", "Everything else: tab «Manual»."]),
]),
"fr": ("Guide rapide", [
  ("⚡", "Installer", ["Orienter la caméra vers l'emplacement ; sonde de température hors du boîtier.", "Brancher la batterie (Pi 5 : 5 V / 5 A). Après environ 1 minute, tout est prêt."]),
  ("📱", "Se connecter", ["Activer le point d'accès du portable – le Pi s'y connecte seul. Ou rejoindre le Wi-Fi «MotionWatch» du Pi.", "Ouvrir la page : dans le Wi-Fi du Pi <b>http://10.42.0.1:5000</b>. Pour la position et le micro, utiliser la page https.", "«🖨 Codes QR pour se connecter» (sous Système) imprime les codes."]),
  ("🌙", "Le soir", ["Toucher <b>«🌙 Surveiller cette nuit»</b>.", "Régler ce qui figure sous «Il manque encore».", "Quitter la zone pendant le compte à rebours."]),
  ("🚨", "En cas d'alarme", ["Toucher la notification → regarder l'image en direct.", "Sirène ou lumière avec les interrupteurs rapides.", "Ce n'était rien ? Dans les enregistrements, toucher <b>👎 «Ce n'était rien»</b> – le programme propose alors de meilleurs réglages."]),
  ("☀", "Le matin", ["Lire le rapport de nuit (notification, 7 h par défaut).", "Désarmer, recharger la batterie.", "Voir les animaux de la nuit dans le journal."]),
  ("🩺", "Si quelque chose ne marche pas", ["Toucher le badge rouge <b>🩺</b> en haut : chaque feu dit quoi faire.", "Pas d'image → vérifier câble et source vidéo. Pas de notification → vérifier Internet / point d'accès.", "Tout le reste : onglet «Mode d'emploi»."]),
]),
"it": ("Guida rapida", [
  ("⚡", "Installare", ["Puntare la telecamera sulla piazzola; sensore di temperatura fuori dalla custodia.", "Collegare il powerbank (Pi 5: 5 V / 5 A). Dopo circa 1 minuto è tutto pronto."]),
  ("📱", "Collegarsi", ["Accendere l'hotspot del cellulare – il Pi si collega da solo. Oppure collegarsi al Wi-Fi «MotionWatch» del Pi.", "Aprire la pagina: nel Wi-Fi del Pi <b>http://10.42.0.1:5000</b>. Per posizione e microfono usare la pagina https.", "«🖨 Codici QR per collegarsi» (in Sistema) stampa i codici."]),
  ("🌙", "La sera", ["Toccare <b>«🌙 Sorvegliare stanotte»</b>.", "Sistemare ciò che appare sotto «Manca ancora».", "Lasciare la zona durante il conto alla rovescia."]),
  ("🚨", "In caso di allarme", ["Toccare la notifica → guardare l'immagine dal vivo.", "Sirena o luce con gli interruttori rapidi.", "Non era niente? Nelle registrazioni toccare <b>👎 «Non era niente»</b> – il programma propone poi impostazioni migliori."]),
  ("☀", "Al mattino", ["Leggere il rapporto notturno (notifica, di default alle 7).", "Disinserire, ricaricare il powerbank.", "Guardare gli animali della notte nel diario."]),
  ("🩺", "Se qualcosa non funziona", ["Toccare il badge rosso <b>🩺</b> in alto: ogni semaforo dice cosa fare.", "Nessuna immagine → controllare cavo e sorgente video. Nessuna notifica → controllare Internet / hotspot.", "Tutto il resto: scheda «Istruzioni»."]),
]),
"rm": ("Introducziun curta", [
  ("⚡", "Installar", ["Drizzar la camera sin la plazza; sensur da temperatura ordaifer la chascha.", "Colliar il powerbank (Pi 5: 5 V / 5 A). Suenter var 1 minuta è tut pront."]),
  ("📱", "Colliar", ["Activar il hotspot dal telefonin – il Pi sa collia sez. U sa colliar cun il WLAN «MotionWatch» dal Pi.", "Avrir la pagina: en il WLAN dal Pi <b>http://10.42.0.1:5000</b>. Per la posiziun ed il microfon duvrar la pagina https.", "«🖨 Codes QR per colliar» (sut Sistem) stampa ils codes."]),
  ("🌙", "La saira", ["Smatgar <b>«🌙 Survegliar questa notg»</b>.", "Reglar quai che stat sut «Manca anc».", "Bandunar la zona durant il countdown."]),
  ("🚨", "Tar in alarm", ["Smatgar l'avis push → guardar il maletg live.", "Sirena u glisch cun ils cumutaturs svelts.", "Na era nagut? En las registraziuns smatgar <b>👎 «Na era nagut»</b> – il program propona lura meglras configuraziuns."]),
  ("☀", "La damaun", ["Leger il rapport da notg (avis push, standard a las 7).", "Disarmar, chargiar il powerbank.", "Guardar en il diari ils animals da la notg."]),
  ("🩺", "Sch'insatge na funcziuna betg", ["Smatgar l'indicaziun cotschna <b>🩺</b> survart: mintga semafor di tge far.", "Nagin maletg → controllar cabel e funtauna da video. Nagin avis → controllar internet / hotspot.", "Tut il rest: register «Instrucziuns»."]),
]),
}


def quick_guide_html(lang=None):
    L = norm_lang(lang) if lang else cur_lang()
    title, blocks = QUICK_GUIDE.get(L) or QUICK_GUIDE["en"]
    name = html_escape(CFG["device_name"] or "MoveEye")
    cards = "".join('<section class="qg"><h2><span>' + ic + '</span> ' + html_escape(h) + '</h2><ol>' + "".join("<li>" + x + "</li>" for x in items)
                    + "</ol></section>" for ic, h, items in blocks)
    return ('<!doctype html><html lang="' + L + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>MoveEye – ' + html_escape(title) + '</title><style>'
            'body{margin:0;background:#fff;color:#111;font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}'
            'main{max-width:960px;margin:0 auto;padding:18px}'
            '.top{display:flex;align-items:center;gap:12px;border-bottom:3px solid #f08c2e;padding-bottom:8px;margin-bottom:12px}'
            '.top h1{margin:0;font-size:24px}.top .sub{color:#666;font-size:13px}.top .sp{flex:1}'
            '.top button,.top a{font:600 14px system-ui;padding:8px 12px;border-radius:8px;border:1px solid #ccc;background:#f5f5f5;color:#111;text-decoration:none;cursor:pointer}'
            '.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}'
            '.qg{border:1.5px solid #ddd;border-radius:12px;padding:10px 12px;break-inside:avoid}'
            '.qg h2{margin:0 0 4px;font-size:17px}.qg h2 span{font-size:20px}.qg ol{margin:0;padding-left:20px}.qg li{margin:3px 0}'
            '.foot{margin-top:10px;color:#777;font-size:12px;text-align:center}'
            '@media(max-width:640px){.grid{grid-template-columns:1fr}}'
            '@media print{@page{size:A4;margin:12mm}.noprint{display:none}main{padding:0}body{font-size:12.5px}.qg h2{font-size:15px}}'
            '</style></head><body><main><div class="top"><h1>🎥 ' + name + '</h1><div><b>' + html_escape(title) + '</b><div class="sub">MoveEye '
            + APP_VERSION + '</div></div><span class="sp"></span><a class="noprint" href="/setup-card?lang=' + L + '">' + html_escape("🖨 QR codes for connecting" if L == "en" else tr("🖨 Quick start (QR)", L))
            + '</a><button class="noprint" onclick="print()">🖨</button></div><div class="grid">' + cards + '</div>'
            '<div class="foot">' + html_escape(tr("Manual", L)) + ': /help</div></main></body></html>')


def health_check(lang=None):
    """Traffic lights for the parts of the system - only from what is known anyway (no waiting, no hardware access)."""
    L = norm_lang(lang) if lang else cur_lang()
    T = lambda x: tr(x, L)
    out = []

    def add(key, icon, title, level, text="", tip=""):
        out.append({"id": key, "icon": icon, "title": T(title), "level": level, "text": text, "tip": T(tip) if tip else ""})

    fps = float(STATE.get("fps") or 0)
    if fps >= 1:
        add("cam", "📷", "Camera", "ok", f"{STATE.get('source_label') or ''} · {fps:.0f} fps")
    else:
        add("cam", "📷", "Camera", "bad", T("no picture") + (" · " + tl_status_text(STATE.get("source_status") or "") if STATE.get("source_status") else ""),
            "Check the cable and the video source under Setup.")
    ai = str(STATE.get("ai_status") or "")
    if ai.startswith(("ready", "running")):
        add("ai", "🧠", "AI (person detection)", "ok", T("ready") + (f" · {STATE.get('ai_ms')} ms" if STATE.get("ai_ms") else ""))
    elif ai == "demo":
        add("ai", "🧠", "AI (person detection)", "warn", T("demo"), "")
    elif ai in ("off", ""):
        add("ai", "🧠", "AI (person detection)", "off", T("off"))
    elif AI_MODEL["busy"]:
        add("ai", "🧠", "AI (person detection)", "warn", T("downloading the AI model …") + f" {AI_MODEL['pct']} %")
    else:
        add("ai", "🧠", "AI (person detection)", "bad", T(ai) + (" · " + T("download failed") + AI_MODEL["msg"][6:] if AI_MODEL["msg"].startswith("failed") else ""),
            "Tap «Download AI model» (about 70 MB, needs internet).")
        out[-1]["action"] = "ai_dl"
    sb = str(STATE.get("servo_backend") or "")
    if sb.startswith("simulation") or not sb:
        add("servo", "🎯", "Servos (pan / tilt)", "warn", T("not found - the camera does not move"),
            "Check wiring and power of the servos; for the PCA9685 switch on I2C (raspi-config).")
    else:
        add("servo", "🎯", "Servos (pan / tilt)", "ok", sb)
    th = str(STATE.get("thermal") or "off")
    if th == "connected":
        add("thermal", "♨", "Thermal camera", "ok", T("connected") + (f" · {STATE['thermal_res']}" if STATE.get("thermal_res") else ""))
    elif th.startswith(("off", "no thermal camera", "same camera")):
        add("thermal", "♨", "Thermal camera", "off", tl_status_text(th))
    else:
        add("thermal", "♨", "Thermal camera", "warn", tl_status_text(th), "Check the USB cable of the thermal camera.")
    au = (STATE.get("audio") or {}).get("status") or "off"
    if au == "listening":
        add("mic", "🎤", "Microphone", "ok", T("listening"))
    elif au == "off":
        add("mic", "🎤", "Microphone", "off", T("off"))
    else:
        add("mic", "🎤", "Microphone", "bad" if au.startswith("error") else "warn", tl_status_text(au), "Choose the microphone again under Microphone → Search devices.")
    if out_selected():
        dev = CFG["audio_out"]
        add("spk", "🔊", "Loudspeaker", "ok", ("Bluetooth " + dev[3:]) if dev.startswith("bt:") else dev.replace("plughw:CARD=", "").split(",")[0])
    else:
        add("spk", "🔊", "Loudspeaker", "off", T("none chosen"), "For the siren: Settings → Loudspeaker.")
    ln = STATE.get("lens") or {}
    if CFG["lens_check"] and fps >= 1:
        if ln.get("state") == "fogged":
            add("lens", "🔍", "Lens", "bad", T("blurred") + (f" · {ln['pct']} %" if ln.get("pct") is not None else ""), "Wipe the lens and look for dew or a spider web.")
        elif ln.get("state") == "clear":
            add("lens", "🔍", "Lens", "ok", T("clear") + (f" · {ln['pct']} %" if ln.get("pct") is not None else ""))
        else:
            add("lens", "🔍", "Lens", "ok", T("learning (1 hour)"))
    e = STATE.get("env")
    if not CFG["env_on"]:
        add("env", "🌡", "Temperature sensor", "off", T("off"))
    elif e:
        ta = TEMPA["state"] if CFG["temp_alarm_on"] else ""
        add("env", "🌡", "Temperature sensor", "bad" if ta in ("hot", "cold") else "ok",
            f"{e['t']:.1f} °C" + (f" · {e['h']} %" if e.get("h") is not None else "") + f" ({e.get('src', '')})"
            + (" · " + T({"hot": "too hot", "cold": "too cold"}[ta]) if ta in ("hot", "cold") else (" · " + T("alarm") + f" < {CFG['temp_cold']:.0f} / > {CFG['temp_hot']:.0f} °C" if ta else "")))
    else:
        add("env", "🌡", "Temperature sensor", "off", T("none connected"), "BME280 on I2C or DS18B20 on GPIO 4 - see the housing document.")
    g = gps_state()
    if g:
        add("gps", "📍", "Location", "ok", f"{g['lat']:.4f}, {g['lon']:.4f} · " + (T("from the phone") if g["src"] == "phone" else T("fixed (settings)")))
    else:
        add("gps", "📍", "Location", "warn", T("unknown"), "Settings → Setup → Location: automatically (https page) or pick it on the map.")
    ts = str(STATE.get("time_status") or "")
    if ts.startswith("could not"):
        add("clock", "🕑", "Clock", "bad", tl_status_text(ts), "Open the page on the phone once - the Pi takes the time from it.")
    else:
        add("clock", "🕑", "Clock", "ok", datetime.now().strftime("%H:%M") + (" · " + tl_status_text(ts) if ts else ""))
    net = STATE.get("net") or {}
    if net.get("online"):
        add("net", "🌐", "Internet", "ok", f"{net.get('ms', '?')} ms")
    elif net.get("online") is False:
        add("net", "🌐", "Internet", "warn", T("offline - push messages wait"), "Phone hotspot on? Settings → Camping / protection → Network.")
    else:
        add("net", "🌐", "Internet", "off", T("not checked yet"))
    ns = str(STATE.get("notify_status") or "")
    if not Notifier.configured():
        add("push", "📲", "Push messages", "bad", T("not set up"), "Notifications: set up ntfy, Telegram or web push and send a test message.")
    elif ns.startswith("error"):
        add("push", "📲", "Push messages", "bad", ns[:120] + (" · " + trf("{n} alarm(s) waiting in the outbox", L, n=outbox_count()) if outbox_count() else ""),
            "Send a test message; check the address / token of the push service.")
    elif outbox_count():
        add("push", "📲", "Push messages", "warn", trf("{n} alarm(s) waiting in the outbox", L, n=outbox_count()), "They are sent as soon as the connection works.")
    else:
        add("push", "📲", "Push messages", "ok", tl_status_text(ns) if ns else T("ready"))
    dk = STATE.get("disk") or {}
    fr = dk.get("free_mb")
    if fr is None:
        add("disk", "💾", "Memory card", "off", T("not checked yet"))
    else:
        add("disk", "💾", "Memory card", "bad" if fr < 500 else "warn" if fr < 2000 else "ok",
            f"{fr / 1024:.1f} GB " + T("free"), "" if fr >= 2000 else "Delete old recordings or lower «max. size of the recordings».")
    ct = STATE.get("cpu_temp")
    if ct is None:
        add("temp", "🔥", "CPU temperature", "off", T("unknown"))
    else:
        add("temp", "🔥", "CPU temperature", "bad" if ct >= 80 else "warn" if ct >= 70 else "ok", f"{ct:.0f} °C",
            "" if ct < 70 else "Shade for the housing, a fan, or switch off night vision / thermal camera.")
    sp = STATE.get("supply") or {}
    if not sp.get("known"):
        add("power", "⚡", "Power supply", "off", T("unknown"))
    elif sp.get("uv_now"):
        add("power", "⚡", "Power supply", "bad", T("under-voltage now"), "Use a stronger power supply / powerbank (Pi 5: 5 V 5 A) and a short thick cable.")
    elif sp.get("uv_boot") or sp.get("throttled"):
        add("power", "⚡", "Power supply", "warn", T("under-voltage since the start"), "Use a stronger power supply / powerbank (Pi 5: 5 V 5 A) and a short thick cable.")
    else:
        add("power", "⚡", "Power supply", "ok", (f"{sp['volt']:.2f} V" if sp.get("volt") else T("ok")))
    b = STATE.get("battery") or {}
    if not b.get("on"):
        add("batt", "🔋", "Battery", "off", T("off"))
    else:
        pct = b.get("pct")
        nf = STATE.get("night")
        lvl = "off" if pct is None else "bad" if pct < 20 else "warn" if pct < 40 else "ok"
        if nf and not nf["enough"] and nf.get("night") and lvl == "ok":
            lvl = "warn"
        add("batt", "🔋", "Battery", lvl,
            ("–" if pct is None else f"{pct} %") + (" · " + trf("lasts until sunrise ({sr})", L, sr=nf["sunrise"]) if nf and nf["enough"]
                                                    else " · " + trf("too little until sunrise ({sr})", L, sr=nf["sunrise"]) if nf else ""),
            "" if (pct is None or pct >= 40) and not (nf and not nf["enough"]) else "Charge the powerbank soon.")
    if web_pw_active():
        add("pw", "🔑", "Password", "ok", T("set"))
    else:
        add("pw", "🔑", "Password", "bad", T("no password"), "Without a password everyone in the same network can watch and control everything.")
    if STATE.get("https_port"):
        add("https", "🔒", "https page", "ok", f"Port {STATE['https_port']}")
    else:
        add("https", "🔒", "https page", "warn", T("off"), "Phone location and talking through the Pi need the https page (start with --https).")
    try:
        si = storage_info()
        KIND = {"sd": T("memory card"), "ssd": "SSD (NVMe)", "usb": T("USB drive"), "other": T("drive")}
        if si["fallback"]:
            add("store", "🗄", "Storage", "bad", T("chosen drive missing - recordings on the memory card"), "Connect the SSD / USB drive and restart, or choose another place under Settings → Recording.")
        else:
            txt = T("program") + ": " + KIND[si["system"]] + " · " + T("recordings") + ": " + KIND[si["rec"]]
            add("store", "🗄", "Storage", "warn" if si["rec"] == "sd" and si["candidates"] else "ok", txt,
                "An SSD / USB drive is connected: put the recordings there (Settings → Recording) - it lasts longer than a memory card."
                if si["rec"] == "sd" and si["candidates"] else "")
    except Exception:
        pass
    bt = CFG["backup_type"]
    if bt == "off":
        add("backup", "☁", "Backup", "warn", T("off"), "If the Pi is stolen, the recordings are gone: Settings → Backup (Telegram, WebDAV / NAS or USB stick).")
    else:
        bs = str(STATE.get("backup_status") or "")
        add("backup", "☁", "Backup", "bad" if bs.startswith("⚠") else "ok", bt + (" · " + bs[:80] if bs else ""),
            "Check the backup settings and send a test." if bs.startswith("⚠") else "")
    lr = RUNGUARD.get("last")
    if lr:
        det = [T("ended unexpectedly after") + f" {lr['ran_s'] // 60} min"]
        if isinstance(lr.get("cpu_temp"), (int, float)):
            det.append(f"CPU {lr['cpu_temp']:.0f} °C")
        if lr.get("uv"):
            det.append(T("under-voltage"))
        if lr.get("ai"):
            det.append(T("AI was running"))
        tip = ("Safe start: AI, thermal camera, night vision, IR light and patrol were switched off. Use a 5 V / 5 A power supply and "
               "cooling (heat sink / fan), then switch them on again one by one." if RUNGUARD["safe"] else
               "Power cut, power supply too weak (Pi 5: 5 V / 5 A) or too hot. If it happens again, switch the AI off for a test.")
        add("lastrun", "🔌", "Last run", "bad" if RUNGUARD["safe"] else "warn", " · ".join(det), tip)
    for a_, b_, ad in i2c_conflicts():
        add("i2c_" + ad, "🔌", "I2C address conflict", "bad", f"{ad}: {T(I2C_KEYS[a_])} + {T(I2C_KEYS[b_])}", "Settings → hardware: give one of them another address.")
    hb = time.time() - HEART["t"]                          # 2.95.35: the detection itself
    if toolmode_on():
        add("loop", "🫀", "Detection loop", "off", T("paused (tool mode)"))
    elif hb > 20:
        add("loop", "🫀", "Detection loop", "bad", trf("no sign of life for {s} s", L, s=int(hb)), "Restart MoveEye; look at the log for «Camera loop error».")
    else:
        add("loop", "🫀", "Detection loop", "ok", T("running"))
    if REC_HEALTH["fail_t"] and time.time() - REC_HEALTH["fail_t"] < 900:
        add("rec", "🎬", "Recording", "bad" if REC_HEALTH["fail_n"] >= 3 else "warn", T(REC_HEALTH["msg"] or "recording failed"),
            "Check the drive (full? unplugged?) under Settings → Recording.")
    elif CFG["record"]:
        add("rec", "🎬", "Recording", "ok", STATE.get("recording_enc") or T("ready"))
    if CFG.get("loop_on"):
        lb = BEATS.get("looprec")
        if lb and time.monotonic() - lb[0] > lb[1]:
            add("looprec", "🔁", "Continuous recording", "bad", T("stopped"), "Check the drive; look at the log.")
        else:
            add("looprec", "🔁", "Continuous recording", "ok", T("running"))
    dead = [b[2] for b in BEATS.values() if time.monotonic() - b[0] > b[1]]
    if dead:
        add("bg", "⚙", "Background tasks", "bad", ", ".join(T(x) for x in dead)[:150], "Restart MoveEye; send the diagnosis package if it happens again.")
    elif BEATS:
        add("bg", "⚙", "Background tasks", "ok", trf("{n} running", L, n=len(BEATS)))
    if STATE.get("update_new"):
        add("upd", "⬆", "Updates", "warn", T("new version available") + f": {STATE['update_new']}", "Settings → Updates.")
    out.sort(key=lambda x: HEALTH_ORDER.index(x["level"]))
    cnt = {k: sum(1 for x in out if x["level"] == k) for k in HEALTH_ORDER}
    return {"items": out, "count": cnt}


def exif_read_gps(path):
    """(lat, lon) from the EXIF block of a JPEG (ours or a camera's), otherwise None."""
    import struct
    try:
        with open(path, "rb") as f:
            data = f.read(65536)
    except OSError:
        return None
    i = data.find(b"Exif\0\0")
    if data[:2] != b"\xff\xd8" or i < 0:
        return None
    t = data[i + 6:]
    try:
        e = "<" if t[:2] == b"II" else ">" if t[:2] == b"MM" else None
        if not e:
            return None
        def ifd(off):
            n = struct.unpack(e + "H", t[off:off + 2])[0]; out = {}
            for k in range(n):
                tag, typ, cnt, val = struct.unpack(e + "HHI4s", t[off + 2 + 12 * k: off + 14 + 12 * k]); out[tag] = (typ, cnt, val)
            return out
        d0 = ifd(struct.unpack(e + "I", t[4:8])[0])
        if 0x8825 not in d0:
            return None
        g = ifd(struct.unpack(e + "I", d0[0x8825][2])[0])
        def deg(tag):
            o = struct.unpack(e + "I", g[tag][2])[0]
            v = struct.unpack(e + "6I", t[o:o + 24])
            return v[0] / (v[1] or 1) + v[2] / (v[3] or 1) / 60 + v[4] / (v[5] or 1) / 3600
        lat, lon = deg(2), deg(4)
        if g.get(1, (0, 0, b"N"))[2][:1] == b"S":
            lat = -lat
        if g.get(3, (0, 0, b"E"))[2][:1] == b"W":
            lon = -lon
        if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
            return None
        return round(lat, 6), round(lon, 6)
    except (struct.error, KeyError, IndexError, ZeroDivisionError):
        return None


_REC_GPS = {}


def rec_gps(name, meta, folder, snap=None):
    """Where a recording was taken: the info file of a video, otherwise the EXIF of the picture (or of its snapshot)."""
    gp = meta.get("gps") if isinstance(meta, dict) else None
    if isinstance(gp, dict) and gp.get("lat") is not None:
        try:
            return float(gp["lat"]), float(gp["lon"])
        except (TypeError, ValueError):
            pass
    pic = name if name.lower().endswith(".jpg") else snap
    if not pic:
        return None
    path = os.path.join(folder, pic)
    try:
        mt = os.path.getmtime(path)
    except OSError:
        return None
    e = _REC_GPS.get(path)
    if e is None or e[0] != mt:
        e = _REC_GPS[path] = (mt, exif_read_gps(path))
        if len(_REC_GPS) > 20000:
            _REC_GPS.clear()
    return e[1]


def geo_km(a, b):
    import math
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(min(1.0, math.sqrt(h)))


PLACE_KM = 2.0                          # pictures closer than this belong to the same place
PLACES = {"names": None, "busy": set()}


def places_file():
    return os.path.join(DATA_DIR, "places.json")


def places_names():
    if PLACES["names"] is None:
        try:
            with open(places_file()) as f:
                PLACES["names"] = json.load(f)
        except (OSError, ValueError):
            PLACES["names"] = {}
    return PLACES["names"]


def places_save():
    try:
        tmp = places_file() + ".tmp"
        with open(tmp, "w") as f:
            json.dump(PLACES["names"] or {}, f, ensure_ascii=False)
        os.replace(tmp, places_file())
    except OSError:
        pass


def place_rename(pid, name):
    if not re.fullmatch(r"-?\d+\.\d{3},-?\d+\.\d{3}", str(pid or "")):
        return False
    nm = places_names(); e = nm.setdefault(pid, {})
    name = str(name or "").strip()[:40]
    if name:
        e["own"] = name
    else:
        e.pop("own", None)
    places_save()
    return True


def place_lookup(pid, lat, lon):
    """Name of a place from OpenStreetMap (Nominatim), once per place, in the background."""
    if not CFG["map_online"] or DEMO["on"] or pid in PLACES["busy"]:
        return
    PLACES["busy"].add(pid)
    def run():
        try:
            url = "https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=14&lat=%.4f&lon=%.4f&accept-language=%s" % (lat, lon, cur_lang())
            req = urllib.request.Request(url, headers={"User-Agent": "MotionWatch/" + APP_VERSION + " (camping camera)"})
            with urllib.request.urlopen(req, timeout=15) as r:
                j = json.loads(r.read().decode())
            a = j.get("address") or {}
            nm = (a.get("village") or a.get("town") or a.get("city") or a.get("hamlet") or a.get("municipality")
                  or a.get("county") or j.get("name") or "")
            if a.get("country_code") and a.get("country_code") != "ch" and nm:
                nm += " (" + a["country_code"].upper() + ")"
            if nm:
                places_names().setdefault(pid, {})["osm"] = nm[:40]; places_save()
        except Exception:
            PLACES["busy"].discard(pid)                      # try again later (offline)
            return
    threading.Thread(target=run, daemon=True).start()


def place_name(pid, lat, lon):
    e = places_names().get(pid) or {}
    if e.get("own") or e.get("osm"):
        return e.get("own") or e.get("osm")
    place_lookup(pid, lat, lon)
    return "%.3f° %s, %.3f° %s" % (abs(lat), "N" if lat >= 0 else "S", abs(lon), "E" if lon >= 0 else "W")


def places_assign(items):
    """Group the pictures with a location into places (2 km); sets it["place"]; returns the list of places."""
    located = sorted((it for it in items if it.get("gps")), key=lambda it: it["dt"])
    centers = []
    for it in located:
        best = None
        for c in centers:
            if geo_km(c["c"], it["gps"]) < PLACE_KM:
                best = c; break
        if best is None:
            best = {"id": "%.3f,%.3f" % it["gps"], "c": it["gps"], "n": 0, "lat": 0.0, "lon": 0.0, "last": it["dt"]}
            centers.append(best)
        best["n"] += 1; best["lat"] += it["gps"][0]; best["lon"] += it["gps"][1]; best["last"] = max(best["last"], it["dt"])
        it["place"] = best["id"]
    out = []
    for c in centers:
        lat, lon = c["lat"] / c["n"], c["lon"] / c["n"]
        out.append({"id": c["id"], "name": place_name(c["id"], lat, lon), "lat": round(lat, 5), "lon": round(lon, 5), "count": c["n"],
                    "last": c["last"].strftime("%Y-%m-%d")})
    out.sort(key=lambda p: p["last"], reverse=True)
    return out


def sync_time_from_client(ms, tz="", admin=True):
    if not CFG["time_from_browser"]:
        return "off"
    try:
        client = float(ms) / 1000.0
    except (TypeError, ValueError):
        return "invalid"
    if not (1704067200 <= client <= 4102444800):             # 2024 .. 2100: anything else is not a real clock
        return "invalid"
    if not admin and abs(client - time.time()) > 3 * 86400:   # 2.95.33: a viewer must not move the clock by years (purges!)
        return "only the administrator may change the clock that much"
    msgs = [m for m in [_set_timezone(tz)] if m] if admin else []
    now = time.time(); diff = client - now
    if abs(diff) < 60:
        STATE["time_status"] = "ok" + (" · " + msgs[0] if msgs else ""); return STATE["time_status"]
    if _ntp_synced():
        STATE["time_status"] = "set by the internet (NTP)"; return STATE["time_status"]
    if now - TIME["last"] < 120:
        return "wait"
    TIME["last"] = now
    ok, err = _set_clock(client)
    if ok:
        log_event("sys", f"Clock set from the phone ({'+' if diff > 0 else '-'}{abs(diff) / 60:.0f} min): now {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        STATE["time_status"] = "taken from the phone " + datetime.now().strftime("%H:%M")
    else:
        STATE["time_status"] = "could not set the clock: " + _perm_hint(err)[:120]
    return STATE["time_status"]


