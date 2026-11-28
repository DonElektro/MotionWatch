#@ MoveEye – Teil 639zzzzzzg: GoPro Hero 8 über Bluetooth (inoffiziell) – wecken, GoPro-WLAN ein, Modus, Aufnahme über die älteren GoPro-BLE-Befehle; Vorschaubild über das GoPro-WLAN auf einem 2. WLAN-Stick (wlan1), Heim-WLAN (wlan0) bleibt. Weg «hero8_ble» für die GoPro-Anbindung (#44, Kern 639zzzzzze). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer 28.11.2026 (Fragebogen 19:24, Komplettpaket #44): «Hero 8 über Bluetooth, inoffiziell, mit 2. WLAN-Stick».
# Gemeinsame Schnittstelle: /home/claude/helfer/gopro_schnittstelle.md (G1 Kern + Seite, G2 Open GoPro BLE, G3 = dieser Teil).
#
# Was die Hero 8 kann (inoffiziell – Open GoPro gilt erst ab Hero 9, https://gopro.github.io/OpenGoPro/faq):
#   * BLE-GATT wie bei Open GoPro (Basis b5f9xxxx-aa8d-11e3-9046-0002a5d5c51b, Werbung mit 0xFEA6, einmal koppeln):
#     0072 Befehl / 0073 Antwort, 0074 Einstellung / 0075, 0076 Abfrage / 0077, 0002 WLAN-Name, 0003 WLAN-Passwort (lesen,
#     nur gekoppelt). Quellen: https://gopro.github.io/OpenGoPro/docs/ble/protocol/ble_setup,
#     https://gethypoxic.com/blogs/technical/gopro-hero5-interfaces (Tabelle der älteren Befehle).
#   * Befehle (Länge, Befehl, Parameter-Länge, Wert): WLAN ein 03 17 01 01 / aus 03 17 01 00, Aufnahme 03 01 01 01 / 00,
#     Modus-Gruppe Video 03 02 01 00 / Foto 03 02 01 01, Piepsen 03 16 01 01 / 00, Schlafen 01 05.
#     Quellen: https://gopro.github.io/OpenGoPro/tutorials/connect-wifi (03 17 01 01),
#     https://github.com/KonradIT/goprowifihack/blob/master/Bluetooth/Platforms/RaspberryPi.md (03170101, 03160101),
#     hypoxic (1,1,1 Aufnahme, 2,1,0 Modus, 5 Schlafen). Wecken: das Verbinden über BLE weckt die Kamera (ble_setup).
#   * Vorschau über das GoPro-WLAN (Kamera 10.5.5.9): HTTP GET /gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart,
#     danach alle 2.5 s ein UDP-Paket «_GPHD_:1:0:2:0.000000\n» an 10.5.5.9:8554 (Hero 8 / 9: «1», ältere «0»); die Kamera
#     schickt MPEG-TS an Port 8554 des Absenders. Quellen: https://gist.github.com/KonradIT/acc2ab5c89567037e3d0077982de2da5,
#     https://systemausfall.org/wikis/howto/GoPro_Hero_Streaming (Hero8/9-Paket). Akku: /gp/gpControl/status, Status 70.
#   * Ungeprüft an einer echten Hero 8 (keine hier): Modus-Befehl, Akku-Feld, Keep-alive über BLE. Kann mit jeder
#     GoPro-Firmware brechen – das steht überall, wo man den Weg wählt.
# Ablauf (h8_start): 2. WLAN-Stick suchen (nie wlan0 / das Netz von MoveEye, nie ein Stick des Repeaters 150 DUAL) →
#   BLE verbinden (weckt), WLAN ein, WLAN-Name + Passwort lesen → NetworkManager-Verbindung «MoveEye-GoPro-<id>» nur auf
#   dem Stick (ipv4.never-default, keine DNS, kein IPv6: nur die Route 10.5.5.0/24 über den Stick, wlan0 unverändert;
#   geprüft mit «ip route get» und «ip route show default») → Vorschau starten → ein Faden empfängt den UDP-Strom auf 8554,
#   schickt das Keep-alive vom selben Socket und reicht die Pakete an 127.0.0.1:<frei> weiter: die Videoquelle für
#   open_source ist «udp://127.0.0.1:<port>?…». Kommen 6 s keine Pakete: Neustart (Vorschau neu → WLAN neu → BLE + WLAN
#   ein), Pause 3 / 10 / 30 / 60 s, stille Protokollzeile.
# Passwort (Koordinator 28.11.2026: so machen): nur im Speicher (H8_SECRET). Die NetworkManager-Verbindung hat psk-flags=2
#   («nicht speichern»), das Passwort geht bei jedem Verbinden über stdin (passwd-file /dev/stdin) an nmcli – nie in
#   argv, nie in eine Datei, nie ins Protokoll, nie an den Browser (h8_scrub über jede Meldung).
# BLE: die Grundfunktionen von G2 (gopro_ble_client / gopro_ble_scan, Teil 639zzzzzzf), wenn vorhanden; sonst ein kleiner
#   Rückfall mit bleak (nur wenn installiert). Tests: H8["ble_factory"].
# Rechte: Steuern nur der Administrator (nacht_may, nicht im Bedienermodus). /api/gopro/hero8 (GET Stand, POST do=…).
# Bedienung: G1s Seite «GoPro hinzufügen» (Einstellungen → Kameras); dieser Teil liefert dafür window.goproH8.render(el, id)
#   (H8_JS) und den Hilfe-Absatz (DE / EN). Test: werkzeuge/gopro_hero8_test.py (Fake-BLE, erfundenes nmcli / ip, UDP-Strom
#   mit ffmpeg testsrc).
# ----------------------------------------------------------------------------
# Programmtext in der ZIP (wie 639zzzzk / 639n): der Teil gehört nicht zu Start, Schutz, Alarm, Update oder Reparatur – ohne
# ZIP fehlt einfach der Weg «hero8_ble». Was ohne ZIP gelten muss (Einstellung, Sperrlisten), steht hier oben.
for _k, _v in {"gopro_h8": {}}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v)
USER_SETTINGS_DENY.add("gopro_h8")
LOCK_DENY_KEYS.add("gopro_h8")

if "zd_exec" not in globals():                              # only without 639zzzzk (Blinki defines it first)
    # wraps: zd_exec
    def zd_exec(src, name):
        """run the program text of a part that bauen.py moved into the data zip (same as 639zzzzk)"""
        if not src:
            return False
        import linecache
        linecache.cache[name] = (len(src), None, src.splitlines(True), name)
        exec(compile(src, name, "exec"), globals())
        return True


H8_PY = r'''
import asyncio as _h8_asyncio
import socket as _h8_socket
import select as _h8_select

# ---- texts (5 languages: key = English, then de, fr, it, rm) -----------------------------------------------------------------
_HX_H8 = {
    "Hero 8 over Bluetooth (unofficial)": ("Hero 8 über Bluetooth (inoffiziell)", "Hero 8 par Bluetooth (non officiel)",
                                           "Hero 8 via Bluetooth (non ufficiale)", "Hero 8 via Bluetooth (betg uffizial)"),
    "Unofficial: GoPro does not support this way for the Hero 8 (Open GoPro starts with the Hero 9). It uses older Bluetooth and Wi-Fi commands and may stop working after a GoPro firmware update.":
        ("Inoffiziell: GoPro unterstützt diesen Weg für die Hero 8 nicht (Open GoPro gilt erst ab Hero 9). Er nutzt ältere Bluetooth- und WLAN-Befehle und kann nach einem Firmware-Update der GoPro nicht mehr gehen.",
         "Non officiel : GoPro ne prend pas en charge cette voie pour la Hero 8 (Open GoPro commence avec la Hero 9). Elle utilise d'anciennes commandes Bluetooth et Wi-Fi et peut cesser de fonctionner après une mise à jour du firmware GoPro.",
         "Non ufficiale: GoPro non supporta questa via per la Hero 8 (Open GoPro inizia con la Hero 9). Usa comandi Bluetooth e Wi-Fi più vecchi e può smettere di funzionare dopo un aggiornamento del firmware GoPro.",
         "Betg uffizial: GoPro na sustegna betg questa via per la Hero 8 (Open GoPro cumenza cun la Hero 9). Ella dovra cumonds Bluetooth e WLAN pli vegls e po smetter da funcziunar suenter in update dal firmware da la GoPro."),
    "Needs a second Wi-Fi stick (wlan1): the GoPro makes its own Wi-Fi, the home Wi-Fi stays on wlan0.":
        ("Braucht einen 2. WLAN-Stick (wlan1): die GoPro macht ein eigenes WLAN, das Heim-WLAN bleibt auf wlan0.",
         "Nécessite une deuxième clé Wi-Fi (wlan1) : la GoPro crée son propre Wi-Fi, le Wi-Fi de la maison reste sur wlan0.",
         "Serve una seconda chiavetta Wi-Fi (wlan1): la GoPro crea il proprio Wi-Fi, il Wi-Fi di casa resta su wlan0.",
         "Basegna in segund stick WLAN (wlan1): la GoPro fa ses agen WLAN, il WLAN da chasa resta sin wlan0."),
    "A second Wi-Fi stick is needed (wlan1) - plug in a USB Wi-Fi stick.":
        ("Ein 2. WLAN-Stick ist nötig (wlan1) – bitte einen USB-WLAN-Stick einstecken.",
         "Une deuxième clé Wi-Fi est nécessaire (wlan1) – branche une clé Wi-Fi USB.",
         "Serve una seconda chiavetta Wi-Fi (wlan1) – inserisci una chiavetta Wi-Fi USB.",
         "In segund stick WLAN è necessari (wlan1) – tacca in stick WLAN USB."),
    "The second Wi-Fi stick is in use (repeater or own Wi-Fi) - switch the repeater off or plug in another stick.":
        ("Der 2. WLAN-Stick ist schon belegt (Repeater oder eigenes WLAN) – Repeater ausschalten oder einen weiteren Stick einstecken.",
         "La deuxième clé Wi-Fi est déjà utilisée (répéteur ou Wi-Fi propre) – éteins le répéteur ou branche une autre clé.",
         "La seconda chiavetta Wi-Fi è già in uso (ripetitore o Wi-Fi proprio) – spegni il ripetitore o inserisci un'altra chiavetta.",
         "Il segund stick WLAN è gia occupà (repeater u agen WLAN) – stizzar il repeater u tacar in ulteriur stick."),
    "The GoPro Wi-Fi needs NetworkManager.": ("Das GoPro-WLAN braucht NetworkManager.", "Le Wi-Fi de la GoPro nécessite NetworkManager.",
                                              "Il Wi-Fi della GoPro richiede NetworkManager.", "Il WLAN da la GoPro basegna NetworkManager."),
    "Wi-Fi stick for the GoPro: {s}": ("WLAN-Stick für die GoPro: {s}", "Clé Wi-Fi pour la GoPro : {s}", "Chiavetta Wi-Fi per la GoPro: {s}",
                                       "Stick WLAN per la GoPro: {s}"),
    "Search GoPro (Bluetooth)": ("GoPro suchen (Bluetooth)", "Chercher la GoPro (Bluetooth)", "Cerca GoPro (Bluetooth)", "Tschertgar la GoPro (Bluetooth)"),
    "Pair the GoPro first: on the camera Preferences → Connections → Connect device → GoPro App, then search here.":
        ("Zuerst koppeln: an der Kamera Einstellungen → Verbindungen → Gerät verbinden → GoPro App, dann hier suchen.",
         "D'abord appairer : sur la caméra Préférences → Connexions → Connecter un appareil → App GoPro, puis chercher ici.",
         "Prima abbina: sulla telecamera Preferenze → Connessioni → Connetti dispositivo → App GoPro, poi cerca qui.",
         "L'emprim accumplir: sin la camera Preferenzas → Colliaziuns → Colliar apparat → App GoPro, lura tschertgar qua."),
    "No GoPro found - is the camera on and in pairing mode?": ("Keine GoPro gefunden – ist die Kamera an und im Kopplungsmodus?",
                                                               "Aucune GoPro trouvée – la caméra est-elle allumée et en mode appairage ?",
                                                               "Nessuna GoPro trovata – la telecamera è accesa e in modalità abbinamento?",
                                                               "Nagina GoPro chattada – è la camera en ed en il modus d'accumplir?"),
    "Bluetooth library missing (python3-bleak).": ("Bluetooth-Bibliothek fehlt (python3-bleak).", "Bibliothèque Bluetooth manquante (python3-bleak).",
                                                   "Manca la libreria Bluetooth (python3-bleak).", "La biblioteca Bluetooth manca (python3-bleak)."),
    "GoPro Wi-Fi password": ("Passwort des GoPro-WLANs", "Mot de passe du Wi-Fi de la GoPro", "Password del Wi-Fi della GoPro", "Pled-clav dal WLAN da la GoPro"),
    "Normally the Hero 8 sends it over Bluetooth. Type it only if that fails (camera: Preferences → Connections → Camera Info). It is kept in memory only and never saved.":
        ("Normalerweise schickt die Hero 8 es über Bluetooth. Nur eintippen, wenn das nicht klappt (Kamera: Einstellungen → Verbindungen → Kamera-Info). Es bleibt nur im Speicher und wird nie gespeichert.",
         "Normalement la Hero 8 l'envoie par Bluetooth. Ne le tape que si cela échoue (caméra : Préférences → Connexions → Infos caméra). Il reste seulement en mémoire et n'est jamais enregistré.",
         "Di solito la Hero 8 lo invia via Bluetooth. Digitala solo se non funziona (telecamera: Preferenze → Connessioni → Info telecamera). Resta solo in memoria e non viene mai salvata.",
         "Normalmain trametta la Hero 8 el via Bluetooth. Endatar mo sch'quai na funcziuna betg (camera: Preferenzas → Colliaziuns → Infos da la camera). El resta mo en la memoria e na vegn mai memorisà."),
    "Keep in memory": ("Im Speicher behalten", "Garder en mémoire", "Tieni in memoria", "Tegnair en la memoria"),
    "Forget": ("Vergessen", "Oublier", "Dimentica", "Emblidar"),
    "Password: in memory (not saved)": ("Passwort: im Speicher (nicht gespeichert)", "Mot de passe : en mémoire (non enregistré)",
                                        "Password: in memoria (non salvata)", "Pled-clav: en la memoria (betg memorisà)"),
    "Start recording": ("Aufnahme starten", "Démarrer l'enregistrement", "Avvia registrazione", "Cumenzar la registraziun"),
    "Stop recording": ("Aufnahme stoppen", "Arrêter l'enregistrement", "Ferma registrazione", "Fermar la registraziun"),
    "Video mode": ("Modus Video", "Mode vidéo", "Modalità video", "Modus video"),
    "Photo mode": ("Modus Foto", "Mode photo", "Modalità foto", "Modus foto"),
    "Locate (beep)": ("Suchen (piepsen)", "Localiser (bip)", "Trova (bip)", "Tschertgar (pip)"),
    "Choose": ("Wählen", "Choisir", "Scegli", "Tscherner"),
    "Bluetooth: {s}": ("Bluetooth: {s}", "Bluetooth : {s}", "Bluetooth: {s}", "Bluetooth: {s}"),
    "Only the administrator may control the GoPro.": ("Nur der Administrator darf die GoPro steuern.", "Seul l'administrateur peut commander la GoPro.",
                                                      "Solo l'amministratore può comandare la GoPro.", "Mo l'administratur dastga manar la GoPro."),
    # states (status()["zustand"]) and errors
    "waking the camera …": ("Kamera wird geweckt …", "réveil de la caméra …", "risveglio della telecamera …", "la camera vegn dasdada …"),
    "joining the GoPro Wi-Fi …": ("GoPro-WLAN wird verbunden …", "connexion au Wi-Fi de la GoPro …", "connessione al Wi-Fi della GoPro …",
                                  "il WLAN da la GoPro vegn collià …"),
    "starting the preview …": ("Vorschau wird gestartet …", "démarrage de l'aperçu …", "avvio dell'anteprima …", "la prevista vegn startada …"),
    "picture running": ("Bild läuft", "image en cours", "immagine attiva", "il maletg cuorra"),
    "picture interrupted - restarting …": ("Bild unterbrochen – Neustart …", "image interrompue – redémarrage …", "immagine interrotta – riavvio …",
                                           "maletg interrut – nova partenza …"),
    "stopped": ("gestoppt", "arrêté", "fermato", "fermà"),
    "Bluetooth: no connection to the GoPro.": ("Bluetooth: keine Verbindung zur GoPro.", "Bluetooth : pas de connexion à la GoPro.",
                                               "Bluetooth: nessuna connessione alla GoPro.", "Bluetooth: nagina colliaziun cun la GoPro."),
    "No Wi-Fi name or password from the GoPro - type the password.": ("Kein WLAN-Name oder Passwort von der GoPro – bitte das Passwort eintippen.",
                                                                       "Pas de nom de Wi-Fi ou de mot de passe de la GoPro – tape le mot de passe.",
                                                                       "Nessun nome Wi-Fi o password dalla GoPro – digita la password.",
                                                                       "Nagin num da WLAN u pled-clav da la GoPro – endatar il pled-clav."),
    "Could not join the GoPro Wi-Fi.": ("Das GoPro-WLAN liess sich nicht verbinden.", "Impossible de rejoindre le Wi-Fi de la GoPro.",
                                        "Impossibile connettersi al Wi-Fi della GoPro.", "Il WLAN da la GoPro n'ha betg pudì vegnir collià."),
    "The route to the GoPro does not go over the Wi-Fi stick.": ("Der Weg zur GoPro geht nicht über den WLAN-Stick.",
                                                                 "La route vers la GoPro ne passe pas par la clé Wi-Fi.",
                                                                 "Il percorso verso la GoPro non passa dalla chiavetta Wi-Fi.",
                                                                 "La via a la GoPro na va betg sur il stick WLAN."),
    "The GoPro does not answer (10.5.5.9).": ("Die GoPro antwortet nicht (10.5.5.9).", "La GoPro ne répond pas (10.5.5.9).",
                                              "La GoPro non risponde (10.5.5.9).", "La GoPro na respunda betg (10.5.5.9)."),
    "UDP port 8554 is busy.": ("UDP-Port 8554 ist belegt.", "Le port UDP 8554 est occupé.", "La porta UDP 8554 è occupata.", "Il port UDP 8554 è occupà."),
    "The home Wi-Fi uses 10.5.5.x like the GoPro - the GoPro Wi-Fi would disturb it.":
        ("Das Heim-WLAN nutzt 10.5.5.x wie die GoPro – das GoPro-WLAN würde es stören.",
         "Le Wi-Fi de la maison utilise 10.5.5.x comme la GoPro – le Wi-Fi de la GoPro le perturberait.",
         "Il Wi-Fi di casa usa 10.5.5.x come la GoPro – il Wi-Fi della GoPro lo disturberebbe.",
         "Il WLAN da chasa dovra 10.5.5.x sco la GoPro – il WLAN da la GoPro al disturbass."),
    "Choose the GoPro over Bluetooth first.": ("Zuerst die GoPro über Bluetooth wählen.", "Choisis d'abord la GoPro par Bluetooth.",
                                               "Scegli prima la GoPro via Bluetooth.", "L'emprim tscherner la GoPro via Bluetooth."),
}
for _k, _v in _HX_H8.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

# ---- constants ---------------------------------------------------------------------------------------------------------------
H8_WEG = "hero8_ble"


def h8_uuid(short):
    return "b5f9%s-aa8d-11e3-9046-0002a5d5c51b" % short


H8_CMD = {"wifi_on": b"\x03\x17\x01\x01", "wifi_off": b"\x03\x17\x01\x00", "rec_on": b"\x03\x01\x01\x01", "rec_off": b"\x03\x01\x01\x00",
          "mode_video": b"\x03\x02\x01\x00", "mode_photo": b"\x03\x02\x01\x01", "locate_on": b"\x03\x16\x01\x01",
          "locate_off": b"\x03\x16\x01\x00", "sleep": b"\x01\x05"}
H8_UI_CMDS = ("rec_on", "rec_off", "mode_video", "mode_photo", "locate_on", "locate_off")
H8_NET = {"ip": "10.5.5.9", "net": "10.5.5.", "cam_port": 8554, "rx_port": 8554, "http": 80}   # the tests change ports / ip
H8_KA_MSG = b"_GPHD_:1:0:2:0.000000\n"        # Hero 8 / 9 (older models: _GPHD_:0:0:2:0.000000)
H8_KA_S = 2.5
H8_STALL_S = 6.0                              # no packet for 6 s = the picture broke off
H8_STATUS_S = 30.0                            # battery / alive over HTTP
H8_BACKOFF = (3.0, 10.0, 30.0, 60.0)
H8 = {"devs": {}, "ble_factory": None, "lock": threading.RLock()}
H8_SECRET = {}                                # id -> {"ssid", "pw"}: only in memory, never saved / logged / sent


def h8_scrub(text, dev_id=None):
    """every message that leaves this part: never the Wi-Fi password"""
    s = str(text or "")
    for k, v in list(H8_SECRET.items()):
        if dev_id is not None and k != dev_id:
            pass
        pw = (v or {}).get("pw") or ""
        if pw and len(pw) >= 3:
            s = s.replace(pw, "***")
    return s[:300]


def _h8_log(text, dev_id=None):
    try:
        log_event("sys", "GoPro Hero 8: " + h8_scrub(text, dev_id))
    except Exception:
        pass


# ---- the second Wi-Fi stick -------------------------------------------------------------------------------------------------
def h8_sticks():
    """(all adapters, free ones): never the adapter of MoveEye's own network (WIFI iface / own Wi-Fi), never one of the
    repeater (150 DUAL). USB sticks first."""
    try:
        ads = wifi_adapters()
    except Exception:
        ads = []
    busy = {WIFI.get("iface") or "", WIFI.get("ap_iface") or ""}
    if DUAL.get("on"):
        busy |= {DUAL.get("ap") or "", DUAL.get("up") or ""}
    if not (WIFI.get("iface") or "") and ads:
        busy.add(next((a["iface"] for a in ads if not a.get("usb")), ads[0]["iface"]))      # no home adapter known: the built-in one
    own = {d.get("stick") for d in H8["devs"].values() if d.get("stick")}
    free = [a for a in ads if a["iface"] not in busy or a["iface"] in own]
    free.sort(key=lambda a: (not a.get("usb"), a["iface"]))
    return ads, free


def h8_stick():
    """-> (iface, '') or ('', English error text)"""
    ads, free = h8_sticks()
    if len(ads) < 2:
        return "", "A second Wi-Fi stick is needed (wlan1) - plug in a USB Wi-Fi stick."
    if not free:
        return "", "The second Wi-Fi stick is in use (repeater or own Wi-Fi) - switch the repeater off or plug in another stick."
    if wifi_backend() != "nm":
        return "", "The GoPro Wi-Fi needs NetworkManager."
    return free[0]["iface"], ""


def h8_home_clash():
    """the home network uses 10.5.5.x itself -> the GoPro Wi-Fi would break it"""
    home = WIFI.get("iface") or "wlan0"
    code, out, _e = _run(["ip", "-4", "-o", "addr", "show", "dev", home], 6)
    return code == 0 and (" " + H8_NET["net"]) in out


# ---- NetworkManager: one connection, only on the stick, password only over stdin --------------------------------------------
def h8_conn_name(dev_id):
    return "MoveEye-GoPro-" + re.sub(r"[^A-Za-z0-9_-]", "", str(dev_id))[:24]


def h8_nm_args(name, stick, ssid):
    """the settings of the GoPro connection (no secret in it: psk-flags 2 = NetworkManager never stores the password)"""
    return ["connection.interface-name", stick, "802-11-wireless.ssid", ssid, "802-11-wireless.mode", "infrastructure",
            "802-11-wireless-security.key-mgmt", "wpa-psk", "802-11-wireless-security.psk-flags", "2",
            "connection.autoconnect", "no", "ipv4.method", "auto", "ipv4.never-default", "yes", "ipv4.ignore-auto-dns", "yes",
            "ipv4.route-metric", "900", "ipv6.method", "disabled"]


def h8_wifi_up(dev_id, stick, ssid, pw):
    """join the GoPro Wi-Fi on the stick only. -> '' or English error"""
    name = h8_conn_name(dev_id)
    code, out, _e = _run(["nmcli", "-t", "-f", "NAME", "connection", "show"], 10)
    have = code == 0 and name in [_nm_split(ln)[0] for ln in out.splitlines() if ln.strip()]
    if have:
        code, _o, err = _run(["nmcli", "connection", "modify", "id", name] + h8_nm_args(name, stick, ssid), 15)
    else:
        code, _o, err = _run(["nmcli", "connection", "add", "type", "wifi", "con-name", name, "ifname", stick, "ssid", ssid]
                             + h8_nm_args(name, stick, ssid), 15)
    if code != 0:
        _h8_log("NetworkManager: " + (err or "connection not saved"), dev_id)
        return "Could not join the GoPro Wi-Fi."
    last = ""
    for i in range(3):                                   # the GoPro needs a few seconds after «Wi-Fi on»
        _run(["nmcli", "device", "wifi", "rescan", "ifname", stick], 10)
        code, _o, err = _run(["nmcli", "--wait", "30", "connection", "up", "id", name, "ifname", stick, "passwd-file", "/dev/stdin"], 45,
                             inp="802-11-wireless-security.psk:" + pw + "\n")
        if code == 0:
            break
        last = err
        time.sleep(H8.get("up_pause", 4.0))
    else:
        _h8_log("Wi-Fi: " + (last or "no connection"), dev_id)
        return "Could not join the GoPro Wi-Fi."
    return h8_route_ok(stick)


def h8_route_ok(stick):
    """only 10.5.5.0/24 over the stick; the default route stays where it was (wlan0)"""
    code, out, _e = _run(["ip", "-4", "route", "get", H8_NET["ip"]], 6)
    if code != 0 or (" dev " + stick + " ") not in (out + " "):
        return "The route to the GoPro does not go over the Wi-Fi stick."
    code, out, _e = _run(["ip", "-4", "route", "show", "default"], 6)
    if code == 0 and (" dev " + stick + " ") in (" " + out + " "):
        return "The route to the GoPro does not go over the Wi-Fi stick."
    return ""


def h8_wifi_down(dev_id):
    _run(["nmcli", "connection", "down", "id", h8_conn_name(dev_id)], 15)


# ---- Bluetooth (G2's basics when there, else bleak) -------------------------------------------------------------------------
class _H8Bleak:
    """small fallback with bleak (BlueZ): connect (wakes the camera), pair, notifications, write / read"""

    def __init__(self, addr):
        self.addr, self.c, self.q, self.loop = addr, None, {}, None

    def _do(self, coro, t):
        return _h8_asyncio.run_coroutine_threadsafe(coro, self.loop).result(t)

    def _cb(self, short):
        qq = self.q.setdefault(short, queue.Queue())
        return lambda _h, data: qq.put(bytes(data))

    def connect(self, timeout=20.0):
        import bleak
        self.loop = _h8_asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True, name="h8-ble").start()

        async def go():
            self.c = bleak.BleakClient(self.addr, timeout=timeout)
            await self.c.connect()
            try:
                await self.c.pair()
            except Exception:
                pass
            for s in ("0073", "0075", "0077"):
                try:
                    await self.c.start_notify(h8_uuid(s), self._cb(s))
                except Exception:
                    pass
        self._do(go(), timeout + 10)

    def write(self, short, data, wait=3.0):
        resp = "%04x" % (int(short, 16) + 1)
        qq = self.q.setdefault(resp, queue.Queue())
        while not qq.empty():
            qq.get_nowait()
        self._do(self.c.write_gatt_char(h8_uuid(short), bytes(data), response=True), 10)
        try:
            return qq.get(timeout=wait)
        except queue.Empty:
            return None

    def read(self, short):
        return bytes(self._do(self.c.read_gatt_char(h8_uuid(short)), 10))

    def close(self):
        try:
            if self.c is not None:
                self._do(self.c.disconnect(), 10)
        except Exception:
            pass
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass


def h8_ble_ok():
    if H8.get("ble_factory") or "gopro_ble_client" in globals():
        return True
    try:
        import importlib.util
        return importlib.util.find_spec("bleak") is not None
    except Exception:
        return False


def h8_ble(addr):
    f = H8.get("ble_factory") or globals().get("gopro_ble_client")
    if f:
        return f(addr)
    if not h8_ble_ok():
        raise RuntimeError("Bluetooth library missing (python3-bleak).")
    return _H8Bleak(addr)


def h8_scan(timeout=8.0):
    """-> ([{addr, name, rssi}], English error or '')"""
    if H8.get("scan_factory"):
        res = H8["scan_factory"](timeout)
    elif "gopro_ble_scan" in globals():
        res = globals()["gopro_ble_scan"](timeout)
    elif h8_ble_ok():
        import bleak

        async def go():
            found = await bleak.BleakScanner.discover(timeout=timeout, return_adv=True)
            out = []
            for d, adv in found.values():
                uu = [u.lower() for u in (adv.service_uuids or [])]
                if any(u.startswith("0000fea6") for u in uu) or (d.name or "").lower().startswith("gopro"):
                    out.append({"addr": d.address, "name": (d.name or "GoPro")[:40], "rssi": adv.rssi})
            return out
        try:
            res = _h8_asyncio.run(go())
        except Exception as e:
            return [], "Bluetooth: " + str(e)[:120]
    else:
        return [], "Bluetooth library missing (python3-bleak)."
    res = [r for r in (res or []) if isinstance(r, dict) and r.get("addr")]
    return res, ("" if res else "No GoPro found - is the camera on and in pairing mode?")


def _h8_resp_ok(r):
    return r is None or len(r) < 3 or r[2] == 0          # [len, cmd, status]; no answer = sent (older firmware)


def h8_ble_session(dev_id, cmds=(), want_wifi=False):
    """connect (wakes the camera), send commands, read Wi-Fi name + password. -> (ok, English error)"""
    addr = h8_addr(dev_id)
    if not addr:
        return False, "Choose the GoPro over Bluetooth first."
    cl = None
    try:
        cl = h8_ble(addr)
        cl.connect(20.0)
        for c in cmds:
            r = cl.write("0072", H8_CMD[c])
            if not _h8_resp_ok(r):
                _h8_log("Bluetooth command %s: answer %s" % (c, r.hex() if r else "-"), dev_id)
        if want_wifi:
            ssid = pw = ""
            try:
                ssid = cl.read("0002").decode("utf-8", "replace").strip("\x00 ")
                pw = cl.read("0003").decode("utf-8", "replace").strip("\x00 ")
            except Exception:
                pass
            old = H8_SECRET.get(dev_id) or {}
            if ssid or pw:
                H8_SECRET[dev_id] = {"ssid": ssid or old.get("ssid", ""), "pw": pw or old.get("pw", "")}
        return True, ""
    except RuntimeError as e:
        return False, str(e) if "bleak" in str(e) else "Bluetooth: no connection to the GoPro."
    except Exception as e:
        _h8_log("Bluetooth: " + type(e).__name__ + " " + str(e)[:80], dev_id)
        return False, "Bluetooth: no connection to the GoPro."
    finally:
        try:
            if cl is not None:
                cl.close()
        except Exception:
            pass


def h8_addr(dev_id):
    d = (CFG.get("gopro_h8") or {}).get(str(dev_id)) or {}
    g = (globals().get("GOPRO") or {}).get(dev_id) or {}
    return str(d.get("addr") or g.get("addr") or g.get("ble_addr") or "")


def h8_cmd(dev_id, cmd):
    if cmd not in H8_CMD:
        return False, "invalid value"
    return h8_ble_session(dev_id, (cmd,))


# ---- HTTP to the camera (never over a proxy) --------------------------------------------------------------------------------
def h8_http(path, timeout=4.0):
    url = "http://%s:%d%s" % (H8_NET["ip"], H8_NET["http"], path)
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with op.open(url, timeout=timeout) as r:
        return r.read(200000)


def h8_stream_start():
    try:
        h8_http("/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart")
        return True
    except Exception:
        return False


def h8_battery():
    try:
        st = json.loads(h8_http("/gp/gpControl/status").decode("utf-8", "replace")).get("status") or {}
        v = st.get("70")
        return int(v) if v is not None and 0 <= int(v) <= 100 else None
    except Exception:
        return None


# ---- the stream: receive on 8554, keep-alive from the same socket, hand on to 127.0.0.1:<port> -------------------------------
def _h8_free_port():
    s = _h8_socket.socket(_h8_socket.AF_INET, _h8_socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close()
    return p


def _h8_dev(dev_id):
    with H8["lock"]:
        return H8["devs"].setdefault(dev_id, {"id": dev_id, "zustand": "stopped", "fehler": "", "stick": "", "streamt": False,
                                              "verbunden": False, "akku": None, "pkts": 0, "bytes": 0, "last_pkt": 0.0, "ka": 0,
                                              "neustarts": 0, "port": 0, "stop": None, "thread": None, "sock": None})


def _h8_set(d, zustand=None, fehler=None, **kw):
    if zustand is not None:
        d["zustand"] = zustand
    if fehler is not None:
        d["fehler"] = h8_scrub(fehler, d["id"])
    d.update(kw)


def _h8_connect(d, wake=True):
    """BLE (wake, Wi-Fi on, name + password), then the Wi-Fi on the stick, then the preview. -> '' or English error"""
    did = d["id"]
    stick, err = h8_stick()
    if err:
        return err
    if h8_home_clash():
        return "The home Wi-Fi uses 10.5.5.x like the GoPro - the GoPro Wi-Fi would disturb it."
    d["stick"] = stick
    if wake:
        _h8_set(d, "waking the camera …")
        ok, berr = h8_ble_session(did, ("wifi_on",), want_wifi=True)
        if not ok and not (H8_SECRET.get(did) or {}).get("pw"):
            return berr
        if not ok:
            _h8_log("Bluetooth failed - trying the Wi-Fi with the typed password", did)
    sec = H8_SECRET.get(did) or {}
    if not sec.get("ssid") or not sec.get("pw"):
        return "No Wi-Fi name or password from the GoPro - type the password."
    _h8_set(d, "joining the GoPro Wi-Fi …")
    err = h8_wifi_up(did, stick, sec["ssid"], sec["pw"])
    if err:
        return err
    d["verbunden"] = True
    _h8_set(d, "starting the preview …")
    if not h8_stream_start():
        return "The GoPro does not answer (10.5.5.9)."
    return ""


def _h8_sock(d):
    s = _h8_socket.socket(_h8_socket.AF_INET, _h8_socket.SOCK_DGRAM)
    s.setsockopt(_h8_socket.SOL_SOCKET, _h8_socket.SO_REUSEADDR, 1)
    try:                                                 # only from the stick (needs CAP_NET_RAW; without it the route does it)
        s.setsockopt(_h8_socket.SOL_SOCKET, 25, (d["stick"] + "\0").encode())
    except OSError:
        pass
    s.bind(("0.0.0.0", H8_NET["rx_port"]))
    s.setblocking(False)
    return s


def _h8_loop(d, stop):
    did = d["id"]
    out = _h8_socket.socket(_h8_socket.AF_INET, _h8_socket.SOCK_DGRAM)
    t_ka = t_st = 0.0
    t_go = time.monotonic(); fails = 0
    while not stop.is_set():
        now = time.monotonic()
        s = d.get("sock")
        if s is not None and now - t_ka >= H8_KA_S:
            t_ka = now
            try:
                s.sendto(H8_KA_MSG, (H8_NET["ip"], H8_NET["cam_port"])); d["ka"] += 1
            except OSError:
                pass
        if now - t_st >= H8_STATUS_S:
            t_st = now
            b = h8_battery()
            if b is not None:
                d["akku"] = b
        try:
            r, _w, _x = _h8_select.select([s] if s is not None else [], [], [], 0.25)
        except (OSError, ValueError):
            r = []
        if r:
            for _i in range(64):
                try:
                    data, src = s.recvfrom(65536)
                except (BlockingIOError, OSError):
                    break
                if src[0] != H8_NET["ip"]:
                    continue
                try:
                    out.sendto(data, ("127.0.0.1", d["port"]))
                except OSError:
                    pass
                d["pkts"] += 1; d["bytes"] += len(data); d["last_pkt"] = time.monotonic()
                if not d["streamt"]:
                    _h8_set(d, "picture running", "", streamt=True); fails = 0
        last = d["last_pkt"] or t_go
        if time.monotonic() - last > H8_STALL_S and not stop.is_set():
            # the picture broke off: preview again -> Wi-Fi again -> Bluetooth (wake + Wi-Fi on) again
            if d["streamt"]:
                _h8_log("picture interrupted - restarting", did)
            _h8_set(d, "picture interrupted - restarting …", streamt=False)
            d["neustarts"] += 1
            ok = h8_stream_start()
            if not ok:
                d["verbunden"] = False
                err = ""
                sec = H8_SECRET.get(did) or {}
                if sec.get("pw") and d.get("stick"):
                    err = h8_wifi_up(did, d["stick"], sec.get("ssid", ""), sec["pw"])
                if err or not sec.get("pw"):
                    err = _h8_connect(d, wake=True)
                else:
                    err = "" if h8_stream_start() else "The GoPro does not answer (10.5.5.9)."
                if err:
                    _h8_set(d, fehler=err)
                    stop.wait(H8_BACKOFF[min(fails, len(H8_BACKOFF) - 1)]); fails += 1
                else:
                    d["verbunden"] = True
            t_go = time.monotonic(); d["last_pkt"] = 0.0
    try:
        out.close()
    except OSError:
        pass


def h8_start(dev):
    """start(dev) of the interface: -> the video source for open_source (udp://127.0.0.1:<port>?…). Raises RuntimeError with
    the English text on failure (the core shows it)."""
    did = str(dev.get("id") if isinstance(dev, dict) else dev)
    d = _h8_dev(did)
    with H8["lock"]:
        if d.get("thread") and d["thread"].is_alive():
            return h8_source(did)
    _h8_set(d, "waking the camera …", "", streamt=False, neustarts=0, pkts=0, bytes=0, last_pkt=0.0, ka=0)
    err = _h8_connect(d, wake=True)
    if not err:
        try:
            d["sock"] = _h8_sock(d)
        except OSError:
            err = "UDP port 8554 is busy."
    if err:
        _h8_set(d, "stopped", err, verbunden=False)
        _h8_log(err, did)
        raise RuntimeError(err)
    d["port"] = d.get("port") or _h8_free_port()
    stop = threading.Event()
    d["stop"] = stop
    d["thread"] = threading.Thread(target=_h8_loop, args=(d, stop), daemon=True, name="h8-" + did)
    d["thread"].start()
    _h8_log("started (Wi-Fi on %s, preview on 127.0.0.1:%d)" % (d["stick"], d["port"]), did)
    return h8_source(did)


def h8_source(dev_id):
    d = _h8_dev(str(dev_id))
    return "udp://127.0.0.1:%d?overrun_nonfatal=1&fifo_size=1000000" % d["port"] if d.get("port") else ""


def h8_stop(dev, sleep=True):
    did = str(dev.get("id") if isinstance(dev, dict) else dev)
    d = _h8_dev(did)
    if d.get("stop"):
        d["stop"].set()
    t = d.get("thread")
    if t is not None and t is not threading.current_thread():
        t.join(5)
    try:
        if d.get("sock") is not None:
            d["sock"].close()
    except OSError:
        pass
    d["sock"] = None; d["thread"] = None
    if d.get("verbunden"):
        h8_wifi_down(did)
    if sleep and h8_addr(did):
        h8_ble_session(did, ("wifi_off", "sleep"))            # save the GoPro's battery (best effort)
    _h8_set(d, "stopped", "", streamt=False, verbunden=False)


def h8_status(dev):
    did = str(dev.get("id") if isinstance(dev, dict) else dev)
    d = _h8_dev(did)
    return {"verbunden": bool(d["verbunden"]), "akku": d["akku"], "streamt": bool(d["streamt"]), "fehler": d["fehler"],
            "zustand": d["zustand"], "stick": d["stick"], "neustarts": d["neustarts"], "keepalive": d["ka"],
            "pw_im_speicher": bool((H8_SECRET.get(did) or {}).get("pw")), "addr": h8_addr(did), "inoffiziell": True}


def h8_faehig(dev=None):
    """can this way work here? -> {ok, grund (English), hinweise}"""
    stick, err = h8_stick()
    if not err and not h8_ble_ok():
        err = "Bluetooth library missing (python3-bleak)."
    return {"ok": not err, "grund": err, "stick": stick, "inoffiziell": True,
            "hinweise": ["Unofficial: GoPro does not support this way for the Hero 8 (Open GoPro starts with the Hero 9). It uses older Bluetooth and Wi-Fi commands and may stop working after a GoPro firmware update.",
                         "Needs a second Wi-Fi stick (wlan1): the GoPro makes its own Wi-Fi, the home Wi-Fi stays on wlan0."]}


# ---- registration with the core (G1, 639zzzzzze); until it exists a small stand-in -------------------------------------------
def _h8_reg_stub(name, *, start, stop, status, faehig):
    globals().setdefault("GOPRO_WEGE", {})[name] = {"start": start, "stop": stop, "status": status, "faehig": faehig}


globals().setdefault("GOPRO", {})
globals().setdefault("gopro_register_weg", _h8_reg_stub)
gopro_register_weg(H8_WEG, start=h8_start, stop=h8_stop, status=h8_status, faehig=h8_faehig)


# ---- web: /api/gopro/hero8 (administrator only) -----------------------------------------------------------------------------
def h8_api(d, method, role="admin"):
    """-> (dict, http code). Never sends the password back."""
    if not nacht_may(role):
        return {"ok": False, "error": "Only the administrator may control the GoPro."}, 403
    L = norm_lang((d or {}).get("lang") or CFG.get("lang"))
    T = lambda x: tr(x, L)
    if method == "GET":
        ads, free = h8_sticks()
        f = h8_faehig()
        devs = {k: h8_status(k) for k in set(H8["devs"]) | set((CFG.get("gopro_h8") or {}))}
        for v in devs.values():
            v["zustand_text"] = T(v["zustand"]); v["fehler_text"] = T(v["fehler"]) if v["fehler"] else ""
        return {"ok": True, "faehig": f["ok"], "grund": T(f["grund"]) if f["grund"] else "", "stick": f["stick"],
                "sticks": [{"iface": a["iface"], "usb": a.get("usb"), "chip": a.get("chip", "")} for a in ads],
                "frei": [a["iface"] for a in free], "ble": h8_ble_ok(), "hinweise": [T(x) for x in f["hinweise"]], "devs": devs}, 200
    do = str(d.get("do") or "")
    did = re.sub(r"[^A-Za-z0-9_-]", "", str(d.get("id") or ""))[:40]
    if do == "scan":
        res, err = h8_scan(float(H8.get("scan_s", 8.0)))
        return {"ok": not err, "found": res, "error": T(err) if err else None}, 200
    if not did:
        return {"ok": False, "error": T("invalid value")}, 400
    if do == "addr":
        addr = str(d.get("addr") or "").strip().upper()
        if not re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", addr):
            return {"ok": False, "error": T("invalid value")}, 400
        m = dict(CFG.get("gopro_h8") or {}); m[did] = {"addr": addr, "name": str(d.get("name") or "GoPro")[:40]}
        CFG["gopro_h8"] = m
        try:
            save_settings()
        except Exception:
            pass
        return {"ok": True, "status": h8_status(did)}, 200
    if do == "pw":                                        # only in memory
        pw = str(d.get("pw") or "")
        if not (8 <= len(pw) <= 63):
            return {"ok": False, "error": T("invalid value")}, 400
        old = H8_SECRET.get(did) or {}
        H8_SECRET[did] = {"ssid": str(d.get("ssid") or old.get("ssid") or "")[:32], "pw": pw}
        return {"ok": True, "status": h8_status(did)}, 200
    if do == "forget":
        H8_SECRET.pop(did, None)
        return {"ok": True, "status": h8_status(did)}, 200
    if do == "cmd":
        ok, err = h8_cmd(did, str(d.get("cmd") or ""))
        return {"ok": ok, "error": T(err) if err else None, "status": h8_status(did)}, 200
    if do in ("start", "stop"):
        try:
            src = h8_start({"id": did}) if do == "start" else (h8_stop({"id": did}) or "")
            return {"ok": True, "quelle": bool(src), "status": h8_status(did)}, 200
        except RuntimeError as e:
            return {"ok": False, "error": T(str(e)), "status": h8_status(did)}, 200
    return {"ok": False, "error": T("invalid value")}, 400


_smalltv_routes_639zzzzzzg = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzzzzzg: /api/gopro/hero8
    _smalltv_routes_639zzzzzzg(app, reply, body)
    from flask import request

    @app.route("/api/gopro/hero8", methods=["GET", "POST"])
    def api_gopro_hero8():
        d = dict(request.args) if request.method == "GET" else (body() or {})
        res, code = h8_api(d, request.method, _nacht_role())
        return reply(res, code)


# ---- the panel for G1's page «GoPro hinzufügen»: window.goproH8.render(el, id) ----------------------------------------------
H8_JS = r"""
<script>
(function () {
  try { const D = /*H8DE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  const P = async (o) => { try { return await (await fetch("/api/gopro/hero8", {method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify(Object.assign({lang: L()}, o))})).json(); } catch (e) { return {ok: false, error: String(e)}; } };
  const say = m => { if (typeof toast === "function") toast(m); };
  async function render(el, id) {
    el.textContent = ""; const bx = E("div", "auxbox"); bx.id = "h8-box"; el.appendChild(bx);
    let F = null; try { F = await (await fetch("/api/gopro/hero8?lang=" + L(), {cache: "no-store"})).json(); } catch (e) {}
    if (!F || !F.ok) { bx.appendChild(E("div", "mut", "⚠ " + ((F && F.error) || "error"))); return; }
    bx.appendChild(E("b", "", "🎥 " + T("Hero 8 over Bluetooth (unofficial)")));
    (F.hinweise || []).forEach(h => { const w = E("div", "mut", "⚠ " + h); w.style.marginTop = "4px"; bx.appendChild(w); });
    const st = E("div", "", F.faehig ? "📶 " + T("Wi-Fi stick for the GoPro: {s}").replace("{s}", F.stick) : "⛔ " + F.grund);
    st.id = "h8-stick"; st.style.marginTop = "8px"; bx.appendChild(st);
    const S = (F.devs || {})[id] || {};
    const row = E("div"); row.style.cssText = "margin-top:8px;display:flex;flex-wrap:wrap;gap:6px";
    const sb = E("button", "btn", "🔍 " + T("Search GoPro (Bluetooth)")); row.appendChild(sb); bx.appendChild(row);
    bx.appendChild(E("div", "mut", T("Pair the GoPro first: on the camera Preferences → Connections → Connect device → GoPro App, then search here.")));
    const found = E("div"); found.id = "h8-found"; bx.appendChild(found);
    if (S.addr) bx.appendChild(E("div", "mut", T("Bluetooth: {s}").replace("{s}", S.addr)));
    sb.onclick = async () => {
      sb.disabled = true; found.textContent = "…"; const q = await P({do: "scan"}); sb.disabled = false; found.textContent = "";
      if (!q.ok) { found.appendChild(E("div", "mut", "⚠ " + (q.error || ""))); return; }
      q.found.forEach(g => { const b = E("button", "btn", T("Choose") + ": " + g.name + " (" + g.addr + ")"); b.style.marginTop = "4px";
        b.onclick = async () => { const r = await P({do: "addr", id: id, addr: g.addr, name: g.name}); say(r.ok ? "✓" : "⚠ " + (r.error || "")); render(el, id); };
        found.appendChild(b); });
    };
    const pw = E("div"); pw.style.marginTop = "10px";
    pw.appendChild(E("label", "", T("GoPro Wi-Fi password")));
    const inp = E("input"); inp.type = "password"; inp.autocomplete = "off"; inp.id = "h8-pw"; inp.maxLength = 63; inp.style.width = "100%";
    inp.setAttribute("aria-label", T("GoPro Wi-Fi password"));
    const kb = E("button", "btn", T("Keep in memory")), fb = E("button", "btn", T("Forget"));
    const r2 = E("div"); r2.style.cssText = "margin-top:4px;display:flex;flex-wrap:wrap;gap:6px"; r2.append(kb, fb);
    pw.append(inp, r2, E("div", "mut", T("Normally the Hero 8 sends it over Bluetooth. Type it only if that fails (camera: Preferences → Connections → Camera Info). It is kept in memory only and never saved.")));
    if (S.pw_im_speicher) pw.appendChild(E("div", "", "🔑 " + T("Password: in memory (not saved)")));
    kb.onclick = async () => { const r = await P({do: "pw", id: id, pw: inp.value}); inp.value = ""; say(r.ok ? "✓" : "⚠ " + (r.error || "")); render(el, id); };
    fb.onclick = async () => { await P({do: "forget", id: id}); render(el, id); };
    bx.appendChild(pw);
    const cm = E("div"); cm.style.cssText = "margin-top:10px;display:flex;flex-wrap:wrap;gap:6px";
    [["rec_on", "⏺ " + T("Start recording")], ["rec_off", "⏹ " + T("Stop recording")], ["mode_video", "🎬 " + T("Video mode")],
     ["mode_photo", "📷 " + T("Photo mode")], ["locate_on", "🔔 " + T("Locate (beep)")]].forEach(([c, n]) => {
      const b = E("button", "btn", n); b.dataset.cmd = c;
      b.onclick = async () => { b.disabled = true; const r = await P({do: "cmd", id: id, cmd: c}); b.disabled = false; say(r.ok ? "✓" : "⚠ " + (r.error || "")); };
      cm.appendChild(b); });
    bx.appendChild(cm);
    const z = E("div", "mut", (S.zustand_text || "") + (S.fehler_text ? " · ⚠ " + S.fehler_text : "") + (S.akku != null ? " · 🔋 " + S.akku + " %" : ""));
    z.id = "h8-state"; z.style.marginTop = "8px"; bx.appendChild(z);
  }
  window.goproH8 = {render: render};
})();
</script>
"""
H8_KEYS = list(_HX_H8)
WEB_PAGE = WEB_PAGE.replace("</body>", H8_JS.replace("/*H8DE*/{}", json.dumps({k: DE.get(k, k) for k in H8_KEYS}, ensure_ascii=False), 1) + "</body>", 1)


# ---- manual (DE / EN): in the GoPro section of the core, else under «Camera & Servos» ---------------------------------------
HELP_H8 = {
    "de": '<p id="h8-help"><b>🎥 GoPro Hero 8 über Bluetooth (inoffiziell):</b> MoveEye weckt die Hero 8 über Bluetooth, schaltet ihr '
          'WLAN ein, liest WLAN-Name und Passwort und holt das Vorschaubild über das GoPro-WLAN (Kamera 10.5.5.9, Strom über UDP '
          '8554). Dafür braucht es einen <b>2. WLAN-Stick</b> (wlan1): nur er verbindet sich mit der GoPro, das Heim-WLAN auf wlan0 '
          'bleibt, und nur die Adressen 10.5.5.x gehen über den Stick. Einmal koppeln: an der Kamera <i>Einstellungen → Verbindungen '
          '→ Gerät verbinden → GoPro App</i>, dann auf der Seite «GoPro hinzufügen» <i>GoPro suchen</i>. Das WLAN-Passwort bleibt nur '
          'im Speicher und wird nie gespeichert (wenn nötig von Hand eintippen). Aufnahme starten / stoppen, Modus Video / Foto und '
          'Piepsen gehen auch über Bluetooth. Bricht das Bild ab, startet MoveEye es selbst neu. <b>Inoffiziell:</b> GoPro unterstützt '
          'diesen Weg für die Hero 8 nicht (Open GoPro gilt ab Hero 9); ein Firmware-Update der GoPro kann ihn jederzeit brechen.</p>',
    "en": '<p id="h8-help"><b>🎥 GoPro Hero 8 over Bluetooth (unofficial):</b> MoveEye wakes the Hero 8 over Bluetooth, switches its '
          'Wi-Fi on, reads the Wi-Fi name and password and fetches the preview over the GoPro Wi-Fi (camera 10.5.5.9, stream over UDP '
          '8554). This needs a <b>second Wi-Fi stick</b> (wlan1): only the stick joins the GoPro, the home Wi-Fi on wlan0 stays, and '
          'only the addresses 10.5.5.x go over the stick. Pair once: on the camera <i>Preferences → Connections → Connect device → '
          'GoPro App</i>, then <i>Search GoPro</i> on the page «Add GoPro». The Wi-Fi password is kept in memory only and never saved '
          '(type it by hand if needed). Start / stop recording, video / photo mode and beeping work over Bluetooth too. If the picture '
          'breaks off, MoveEye restarts it by itself. <b>Unofficial:</b> GoPro does not support this way for the Hero 8 (Open GoPro '
          'starts with the Hero 9); a GoPro firmware update may break it at any time.</p>',
}


def _help_h8(doc, lang):
    if 'id="h8-help"' in doc:
        return doc
    i = doc.find('<section id="gopro"')
    if i < 0:
        i = doc.find('<section id="camera"')
    if i < 0:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_H8[lang] + doc[j:] if j >= 0 else doc


_hp_en_h8 = HELP_PAGE.find('<div lang="en">')
if _hp_en_h8 > 0:
    HELP_PAGE = _help_h8(HELP_PAGE[:_hp_en_h8], "de") + _help_h8(HELP_PAGE[_hp_en_h8:], "en")


# ---- self-test ----------------------------------------------------------------------------------------------------------------
def h8_selftest():
    assert H8_CMD["wifi_on"] == bytes([3, 0x17, 1, 1]) and H8_CMD["rec_on"] == bytes([3, 1, 1, 1]), "commands"
    assert h8_uuid("0072") == "b5f90072-aa8d-11e3-9046-0002a5d5c51b", "uuid"
    a = h8_nm_args("MoveEye-GoPro-x", "wlan1", "GP123")
    assert "never-default" in " ".join(a) and "psk-flags" in " ".join(a) and "psk" not in [x for x in a if x.endswith(".psk")], "nm args"
    H8_SECRET["_t"] = {"ssid": "s", "pw": "geheim123"}
    try:
        assert "geheim123" not in h8_scrub("x geheim123 y"), "scrub"
    finally:
        H8_SECRET.pop("_t", None)
    for k in _HX_H8:
        assert all(TRX[L].get(k) for L in ("fr", "it", "rm")) and DE.get(k), "texts " + k
    assert H8_WEG in (globals().get("GOPRO_WEGE") or {}) or globals().get("gopro_register_weg") is not _h8_reg_stub, "registered"
    assert HELP_PAGE.count('id="h8-help"') == 2, "manual de / en"
    assert "window.goproH8" in WEB_PAGE, "panel"
    r, c = h8_api({}, "GET", "user")
    assert c == 403, "admin only"


SELFTEST_EXTRA.append(("GoPro Hero 8 over Bluetooth (639zzzzzzg)", h8_selftest))
'''
zd_exec(H8_PY and "\n" * 57 + H8_PY, "639zzzzzzg_gopro_hero8.py")   # line 1 of H8_PY = line 58: the line numbers are those of this file
