#@ Motion Watch – Teil 560: Übersetzungen Deutsch. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Translations (English text is the key; German below). tr() is used everywhere.
# ----------------------------------------------------------------------------
DE = {
    # sections
    "Camera / Servos": "Kamera / Servos", "Patrol": "Patrouille", "AI detection": "KI-Erkennung",
    "Relay / Alarm": "Relais / Alarm", "Notifications": "Benachrichtigungen", "Web stream": "Web-Stream",
    "Auto-tune": "Auto-Abstimmung", "Detection": "Erkennung", "Low light": "Schwachlicht",
    "Walking recognition": "Geh-Erkennung", "Vehicle filter": "Fahrzeugfilter", "Rain": "Regen", "Wind": "Wind",
    "Recording": "Aufnahme", "Appearance": "Darstellung",
    # sliders
    "Pan (%)": "Schwenken (%)", "Tilt (%)": "Neigen (%)", "Tracking gain": "Verfolgungsstärke",
    "Tracking dead zone": "Verfolgungs-Totzone", "Dwell at waypoint (s)": "Verweilzeit am Wegpunkt (s)",
    "Patrol speed (%/s)": "Patrouillen-Geschwindigkeit (%/s)", "Patrol tilt (%)": "Patrouillen-Neigung (%)",
    "Confidence threshold": "Konfidenz-Schwelle", "Run every N frames": "Alle N Bilder ausführen",
    "Object confidence": "Objekt-Konfidenz", "JPEG quality": "JPEG-Qualität", "Stream width (px)": "Stream-Breite (px)",
    "Hold after person (s)": "Halten nach Person (s)", "Walking time needed (s)": "Nötige Gehzeit (s)",
    "Sensitivity": "Empfindlichkeit", "Shadow: max brightness ratio": "Schatten: max. Helligkeitsverhältnis",
    "Shadow: min brightness ratio": "Schatten: min. Helligkeitsverhältnis", "Min object size (px²)": "Min. Objektgrösse (px²)",
    "Frames of steady motion": "Bilder gleichmässiger Bewegung", "Min speed (px/frame)": "Min. Geschwindigkeit (px/Bild)",
    "Max speed (px/frame)": "Max. Geschwindigkeit (px/Bild)", "Speed consistency": "Geschwindigkeits-Konstanz",
    "Vehicle aspect ratio": "Fahrzeug-Seitenverhältnis", "Vehicle speed (px/frame)": "Fahrzeug-Geschwindigkeit (px/Bild)",
    "Rain threshold": "Regen-Schwelle", "Wind threshold": "Wind-Schwelle", "Max trigger boost": "Max. Auslöse-Verstärkung",
    "Keep recording after (s)": "Nachlaufzeit Aufnahme (s)", "Max recordings folder (GB)": "Max. Aufnahmeordner (GB)",
    "Low-light threshold (brightness)": "Schwachlicht-Schwelle (Helligkeit)", "Cooldown between alarms (s)": "Pause zwischen Alarmen (s)",
    # toggles
    "Follow detected person (auto pan/tilt)": "Erkannter Person folgen (auto Schwenk/Neige)",
    "Invert pan direction": "Schwenkrichtung umkehren", "Invert tilt direction": "Neigerichtung umkehren",
    "Patrol active": "Patrouille aktiv", "Patrol route": "Patrouillen-Route",
    "back and forth (1-2-3-2-1)": "hin und zurück (1-2-3-2-1)", "round trip (1-2-3-1-2-3)": "Runde (1-2-3-1-2-3)", "AI person detection (SSD MobileNet V2)": "KI-Personenerkennung (SSD MobileNet V2)",
    "Mark all detected objects (cars, animals, ...)": "Alle erkannten Objekte markieren (Autos, Tiere, ...)",
    "Motion persons need AI confirmation": "Bewegungs-Personen brauchen KI-Bestätigung",
    "Switch relay when person detected": "Relais bei Person schalten", "Relay ON (manual)": "Relais EIN (manuell)",
    "Web stream + remote control (port 5000)": "Web-Stream + Fernsteuerung (Port 5000)", "Automatic tuning": "Automatische Abstimmung",
    "Detection (master switch)": "Erkennung (Hauptschalter)", "Highlight persons red": "Personen rot hervorheben",
    "Show movement tracks": "Bewegungsspuren anzeigen", "Show motion mask": "Bewegungsmaske anzeigen",
    "Show HUD overlay": "HUD-Einblendung anzeigen", "Shadow filter (ignore person shadows)": "Schattenfilter (Schatten ignorieren)",
    "Keep person flagged while tracked": "Person markiert lassen solange verfolgt", "Ignore cars / vehicles": "Autos / Fahrzeuge ignorieren",
    "Auto rain detection": "Automatische Regenerkennung", "Rain mode (manual, if auto off)": "Regenmodus (manuell, wenn Auto aus)",
    "Auto wind detection": "Automatische Winderkennung", "Record when person seen": "Aufnehmen wenn Person erkannt",
    "Save snapshot JPG per detection": "Schnappschuss-JPG pro Erkennung", "Auto low-light mode (contrast boost)": "Auto-Schwachlichtmodus (Kontrast)",
    # badges / stats / buttons / misc
    "No person": "Keine Person", "PERSON DETECTED": "PERSON ERKANNT", "PERSONS DETECTED": "PERSONEN ERKANNT",
    "Persons total": "Personen gesamt", "No rain": "Kein Regen", "RAIN MODE": "REGENMODUS", "Wind": "Wind",
    "Idle": "Bereit", "REC": "AUFN", "Relay off": "Relais aus", "RELAY ON": "RELAIS EIN", "Patrol off": "Patrouille aus",
    "TRACKING": "VERFOLGT", "Light ok": "Licht ok", "LOW LIGHT": "SCHWACHLICHT", "Auto": "Auto",
    "FPS": "FPS", "PERSONS NOW": "PERSONEN JETZT", "DETECTIONS": "ERKENNUNGEN", "VEHICLES IGNORED": "FAHRZEUGE IGNORIERT",
    "SHADOW % REMOVED": "SCHATTEN % ENTFERNT", "SYSTEM · CPU": "SYSTEM · CPU", "WEATHER": "WETTER",
    "Rain score": "Regen-Wert", "Wind score": "Wind-Wert", "Trigger multiplier (wind)": "Auslöse-Faktor (Wind)",
    "EVENT LOG": "EREIGNISPROTOKOLL", "important": "Wichtiges", "Expand all": "Alle öffnen", "Collapse all": "Alle schliessen",
    "Centre camera": "Kamera zentrieren", "Snapshot": "Schnappschuss", "Add current pan as waypoint": "Aktuelle Position als Wegpunkt",
    "Clear": "Löschen", "Recalibrate (scene empty)": "Neu kalibrieren (Szene leer)", "Reset all settings": "Alle Einstellungen zurücksetzen",
    "Test notification": "Test-Benachrichtigung", "Test all channels": "Alle Kanäle testen", "testing …": "teste …", "No channel set up.": "Kein Kanal eingerichtet.", "Webhook URL (POST JSON on person; e.g. https://ntfy.sh/my-topic)":
        "Webhook-URL (POST JSON bei Person; z. B. https://ntfy.sh/mein-thema)",
    "backend": "Backend", "pan": "Schwenk", "tilt": "Neigung", "waypoints": "Wegpunkte", "none": "keine",
    "AI persons": "KI-Personen", "objects": "Objekte", "automatic changes": "automatische Änderungen", "status": "Status",
    "Settings": "Einstellungen", "recordings": "Aufnahmen", "brightness": "Helligkeit", "cores": "Kerne", "last 60 s": "letzte 60 s",
    "no CPU data (pip install psutil)": "keine CPU-Daten (pip install psutil)",
    "Fullscreen (F11)": "Vollbild (F11)", "Exit fullscreen (Esc)": "Vollbild verlassen (Esc)",
    "Dark": "Dunkel", "Light": "Hell", "Theme": "Design", "Language": "Sprache",
    "Double-click video: video only · F11: fullscreen · Esc: back": "Doppelklick aufs Video: nur Video · F11: Vollbild · Esc: zurück",
    "Build": "Build", "Pan/Tilt surveillance with AI, patrol & relay": "Schwenk/Neige-Überwachung mit KI, Patrouille & Relais",
    "MoveEye - desktop window opened": "MoveEye - Desktop-Fenster geöffnet",
    # 1.2.3: relays, view menu, camera control
    "Relays": "Relais", "Off": "Aus", "On": "Ein", "on": "an", "View": "Ansicht", "Show all": "Alle einblenden",
    "Settings panel": "Einstellungsbereich", "Header": "Kopfzeile",
    "Remote access": "Fernzugriff", "Remote": "Fern", "not installed": "nicht installiert", "watching now": "schaut gerade zu",
    "Night report": "Nachtbericht", "Battery": "Akku", "Guest access": "Gast-Zugang", "Diary": "Tagebuch",
    "Pause the program for": "Programm pausieren für", "Pause program": "Programm pausieren",
    "UPS HAT": "USV-Akku", "on battery": "Akkubetrieb", "charging": "lädt", "mains power": "Netzbetrieb",
    "UPS HAT: capacity of ONE 18650 cell (mAh)": "USV-Akku: Kapazität EINER 18650-Zelle (mAh)",
    "UPS HAT: shut the Pi down at (%, 0 = never)": "USV-Akku: Pi ausschalten bei (%, 0 = nie)",
    "UPS HAT (battery pack on the Pi): use it when found": "USV-Akku (Akku-Modul auf dem Pi): verwenden, wenn vorhanden",
    "UPS HAT: push message at a power cut / when power is back": "USV-Akku: Push-Nachricht bei Stromausfall / wenn der Strom wieder da ist",
    "UPS HAT: charging and discharging are shown the wrong way round": "USV-Akku: Laden und Entladen werden verkehrt angezeigt",
    "UPS HAT: address (I2C)": "USV-Akku: Adresse (I2C)",
    "New version": "Neue Version", "click to update": "zum Aktualisieren klicken",
    "Install new versions automatically": "Neue Versionen automatisch installieren",
    "Test mode: get new versions at once (looks on GitHub every minute and installs right away, also while armed; while on, the other update switches do not count)": "Entwicklungsphase: neue Versionen sofort holen (schaut jede Minute auf GitHub und installiert gleich, auch wenn der Schutz an ist; solange an, gelten die anderen Update-Schalter nicht)",
    "QR code for the phone": "QR-Code fürs Handy", "Markings in recordings and alarm pictures": "Markierungen in Aufnahmen und Alarmbildern",
    "thin corner marks (face stays free)": "dünne Eckmarken (Gesicht bleibt frei)", "none (clean picture)": "keine (sauberes Bild)",
    "like the live picture (red boxes)": "wie im Live-Bild (rote Rahmen)", "please write a few words": "bitte ein paar Worte schreiben",
    "at most 5 messages per hour": "höchstens 5 Nachrichten pro Stunde", "Feedback to the developer": "Rückmeldung an den Entwickler",
    "Ideas, errors, praise - everything helps. The message is sent anonymously: no name, no address, unless you write one.": "Ideen, Fehler, Lob – alles hilft. Die Nachricht geht anonym weg: kein Name, keine Adresse, ausser du schreibst sie dazu.",
    "Idea": "Idee", "Error": "Fehler", "Praise": "Lob", "Other": "Sonstiges", "Send": "Senden", "Cancel": "Abbrechen",
    "Add technical details (version, device, last important events - no pictures, no passwords)": "Technische Angaben mitsenden (Version, Gerät, letzte wichtige Ereignisse – keine Bilder, keine Passwörter)", "Thank you! The message is on its way.": "Danke! Die Nachricht ist unterwegs.", "need 2+ waypoints": "mindestens 2 Wegpunkte nötig", "Person": "Person", "SMS (LTE stick)": "SMS (LTE-Stick)", "Send test SMS": "Test-SMS senden", "SMS sent": "SMS gesendet",
    "Phone numbers (e.g. +41791234567, several with commas)": "Telefonnummern (z. B. +41791234567, mehrere mit Komma)", "Stick / way": "Stick / Weg",
    "Serial port (only for AT commands)": "Serieller Anschluss (nur für AT-Befehle)", "Address of a Huawei HiLink stick": "Adresse eines Huawei-HiLink-Sticks",
    "Alarm also as SMS (person, sabotage, warm body, noise)": "Alarm auch als SMS (Person, Sabotage, warmer Körper, Geräusch)",
    "Only when push messages cannot be sent (no internet)": "Nur wenn keine Push-Nachricht möglich ist (kein Internet)",
    "At most one SMS every (minutes)": "Höchstens eine SMS alle (Minuten)", "At most SMS per day": "Höchstens SMS pro Tag",
    "automatic": "automatisch", "AT commands (serial port)": "AT-Befehle (serieller Anschluss)",
    "no phone number set": "keine Telefonnummer eingetragen", "pause between two SMS": "Pause zwischen zwei SMS", "daily limit reached": "Tageslimit erreicht",
    "mmcli missing (sudo apt install modemmanager)": "mmcli fehlt (sudo apt install modemmanager)", "no modem found (stick plugged in? mmcli -L)": "kein Modem gefunden (Stick eingesteckt? mmcli -L)",
    "the modem does not answer (wrong port?)": "das Modem antwortet nicht (falscher Anschluss?)", "the modem refuses the SMS": "das Modem nimmt die SMS nicht an",
    "SMS not sent (credit / network?)": "SMS nicht gesendet (Guthaben / Netz?)", "HiLink stick not found (address?)": "HiLink-Stick nicht gefunden (Adresse?)",
    "phone numbers like +41791234567": "Telefonnummern wie +41791234567", "a port like /dev/ttyUSB2": "ein Anschluss wie /dev/ttyUSB2",
    "A USB LTE stick with a SIM card (with credit). Works also where there is only the mobile network. Costs per SMS - mind the limits.": "Ein USB-LTE-Stick mit SIM-Karte (mit Guthaben). Funktioniert auch dort, wo es nur Mobilfunk gibt. Jede SMS kostet – Grenzen beachten.",
    "MQTT broker (address, e.g. 192.168.1.10 or homeassistant.local)": "MQTT-Broker (Adresse, z. B. 192.168.1.10 oder homeassistant.local)",
    "MQTT user name": "MQTT-Benutzername", "MQTT password": "MQTT-Passwort", "Topic prefix": "Themen-Anfang", "MQTT port": "MQTT-Port",
    "MQTT on (state, events, commands)": "MQTT ein (Zustand, Ereignisse, Befehle)", "Encrypted (TLS, usually port 8883)": "Verschlüsselt (TLS, meist Port 8883)",
    "Home Assistant finds MoveEye by itself (discovery)": "Home Assistant findet MoveEye von selbst (Discovery)",
    "only letters, digits, - _ /": "nur Buchstaben, Ziffern, - _ /", "port 1-65535": "Port 1–65535", "Other devices": "Weitere Geräte", "overview on the web page: Cameras": "Übersicht auf der Webseite: Kameras",
    "password wrong": "Passwort falsch", "not reachable": "nicht erreichbar",
    "announces itself but does not answer - its firewall or security software blocks MoveEye: use the tunnel":
        "meldet sich im Netz, antwortet aber nicht – die Firewall oder Sicherheitssoftware des PCs sperrt MoveEye: den Tunnel verwenden (unten)", "invalid address (e.g. http://192.168.1.20:5000)": "ungültige Adresse (z. B. http://192.168.1.20:5000)",
    "this device is in the list already": "dieses Gerät ist schon in der Liste", "this is this device itself": "das ist dieses Gerät selbst", "at most 12 devices": "höchstens 12 Geräte", "Shared pictures and videos with a small MoveEye logo": "Geteilte Bilder und Videos mit kleinem MoveEye-Logo", "Backup": "Sicherung", "Theft protection": "Diebstahlschutz", "Deterrence": "Abschreckung",
    "Person: sound": "Person: Ton", "Big animal (bear, cow, horse, ...)": "Grosses Tier (Bär, Kuh, Pferd, …)", "Big animal: sound": "Grosses Tier: Ton",
    "Small animal (cat, dog, bird)": "Kleines Tier (Katze, Hund, Vogel)", "Small animal: sound": "Kleines Tier: Ton",
    "Warm body (thermal camera, e.g. fox, boar)": "Warmer Körper (Wärmebild, z. B. Fuchs, Wildschwein)", "Warm body: sound": "Warmer Körper: Ton",
    "nothing": "nichts", "sound": "Ton", "light flashes": "Lichtblitze", "sound + light flashes": "Ton + Lichtblitze", "light": "Licht",
    "Also when disarmed (e.g. keep animals out of the garden)": "Auch wenn der Schutz aus ist (z. B. Tiere aus dem Garten fernhalten)",
    "Duration of sound / flashing (s)": "Dauer von Ton / Blitzen (s)", "Pause between two reactions (s)": "Pause zwischen zwei Reaktionen (s)",
    "High whistle (animals)": "Hohes Pfeifen (Tiere)", "Bangs / claps (animals)": "Knallen / Klatschen (Tiere)", "warm": "warmer Körper",
    "Sabotage alarm: camera covered or turned away (when armed)": "Sabotage-Alarm: Kamera abgedeckt oder weggedreht (wenn der Schutz an ist)",
    "Motion sensor (MPU-6050, if fitted): alarm when the device is moved or knocked over": "Bewegungssensor (MPU-6050, falls eingebaut): Alarm, wenn das Gerät bewegt oder umgeworfen wird",
    "Power cut while armed = alarm (needs the UPS HAT)": "Strom getrennt bei eingeschaltetem Schutz = Alarm (braucht den USV-Akku)",
    "Motion sensor: alarm from a tilt of (degrees)": "Bewegungssensor: Alarm ab Neigung von (Grad)",
    "Motion sensor": "Bewegungssensor", "found": "gefunden", "not fitted": "nicht eingebaut",
    "What is seen decides the reaction. Animals need the AI detection, warm bodies the thermal camera. Light flashes: the white light.": "Was erkannt wird, bestimmt die Reaktion. Tiere brauchen die KI-Erkennung, warme Körper die Wärmebildkamera. Lichtblitze: das weisse Licht.", "learning the picture": "lernt das Bild", "on guard": "wacht", "Copy recordings to": "Aufnahmen kopieren nach",
    "WebDAV folder (address, e.g. Nextcloud)": "WebDAV-Ordner (Adresse, z. B. Nextcloud)",
    "WebDAV user name": "WebDAV-Benutzername", "WebDAV password (Nextcloud: app password)": "WebDAV-Passwort (Nextcloud: App-Passwort)",
    "Folder (USB stick / NAS, e.g. /media/pi/STICK/MotionWatch)": "Ordner (USB-Stick / NAS, z. B. /media/pi/STICK/MotionWatch)",
    "Copy all recordings (otherwise only alarm recordings: armed or with a person)": "Alle Aufnahmen kopieren (sonst nur Alarm-Aufnahmen: Schutz an oder mit Person)",
    "WebDAV (Nextcloud, NAS, cloud)": "WebDAV (Nextcloud, NAS, Cloud)", "Folder (USB stick / NAS)": "Ordner (USB-Stick / NAS)",
    "Telegram (video, max. 50 MB)": "Telegram (Video, max. 50 MB)", "waiting": "wartet",
    "Test the backup": "Sicherung testen", "Test file copied - the settings work.": "Testdatei kopiert – die Einstellungen stimmen.",
    "no folder set": "kein Ordner eingetragen", "folder not found (USB stick / NAS connected?)": "Ordner nicht gefunden (USB-Stick / NAS angeschlossen?)",
    "no WebDAV folder set": "kein WebDAV-Ordner eingetragen", "backup is off": "Sicherung ist aus",
    "Telegram bot token / chat id missing (Notifications)": "Telegram-Bot-Token / Chat-ID fehlt (Benachrichtigungen)",
    "too big for Telegram (max. 50 MB)": "zu gross für Telegram (max. 50 MB)", "a folder like /media/... expected": "ein Ordner wie /media/... erwartet",
    "Web push: alarm messages also to browsers that switched it on (no app needed)": "Web-Push: Alarm-Nachrichten auch an Browser, die es eingeschaltet haben (ohne App)",
    "Tailscale is not installed": "Tailscale ist nicht installiert", "no device reached": "kein Gerät erreicht", "set a web password first": "zuerst ein Web-Passwort setzen",
    "invalid subscription": "ungültige Anmeldung",
    "python3-cryptography is missing (sudo apt install python3-cryptography)": "python3-cryptography fehlt (sudo apt install python3-cryptography)", "Close": "Schliessen", "Welcome to MoveEye": "Willkommen bei MoveEye",
    "Scan a code with the phone camera and open the page - the setup assistant continues there (password, push messages).":
        "Einen Code mit der Handy-Kamera scannen und die Seite öffnen – dort geht der Einrichtungs-Assistent weiter (Passwort, Push-Nachrichten).",
    "Own Wi-Fi of the device": "Eigenes WLAN des Geräts", "Home network": "Heimnetz", "On the road (Tailscale)": "Unterwegs (Tailscale)",
    "No address found (network?)": "Keine Adresse gefunden (Netzwerk?)",
    "Also accept unsigned versions (not recommended - only for own builds)": "Auch nicht signierte Versionen annehmen (nicht empfohlen – nur für eigene Versionen)",
    "this version is not signed by the developer - not installed (only with the setting «Also accept unsigned versions»)":
        "diese Version ist nicht vom Entwickler signiert – nicht installiert (nur mit der Einstellung «Auch nicht signierte Versionen annehmen»)",
    "signed": "signiert", "not signed": "nicht signiert",
    "Automatic update also while armed (otherwise only when disarmed)": "Automatisches Update auch wenn der Schutz an ist (sonst nur bei Schutz aus)",
    "Automatic update at (o'clock)": "Automatisches Update um (Uhr)",
    "Look for new versions by itself (every 3 hours)": "Selbst nach neuen Versionen suchen (alle 3 Stunden)",
    "Push message when a new version is there": "Push-Nachricht, wenn es eine neue Version gibt",
    "Event log: status line every N minutes (0 = off)": "Ereignisprotokoll: Statuszeile alle N Minuten (0 = aus)",
    "Event log: keep the archive (days)": "Ereignisprotokoll: Archiv aufbewahren (Tage)", "Open event log & archive (browser)": "Ereignisprotokoll & Archiv öffnen (Browser)",
    "Operator mode": "Bedienmodus", "Operator mode (lock settings)": "Bedienmodus (Einstellungen sperren)", "Unlock": "Entsperren",
    "Settings are locked - only the main switches can be used.": "Einstellungen sind gesperrt – nur die wichtigsten Schalter sind bedienbar.",
    "Set a new PIN? (No = keep the current PIN)": "Neue PIN festlegen? (Nein = bisherige PIN behalten)",
    "New PIN for unlocking (4-8 digits):": "Neue PIN zum Entsperren (4–8 Ziffern):", "Repeat the PIN:": "PIN wiederholen:",
    "The PINs are not the same": "Die PINs sind nicht gleich", "PIN:": "PIN:", "Arm": "Schutz an",
    "Lock the settings now? Only the main switches stay usable. Unlocking needs the PIN.": "Einstellungen jetzt sperren? Nur die wichtigsten Schalter bleiben bedienbar. Entsperren nur mit der PIN.",
    "locked - settings can only be changed after unlocking (PIN)": "gesperrt – Einstellungen erst nach dem Entsperren (PIN) änderbar",
    "the PIN must have 4 to 8 digits": "die PIN muss 4 bis 8 Ziffern haben", "set a PIN first": "zuerst eine PIN festlegen",
    "too many wrong PINs - try again in 5 minutes": "zu viele falsche PINs – in 5 Minuten wieder versuchen", "wrong PIN": "falsche PIN",
    "Switch the program off now and start it again in": "Programm jetzt ausschalten und wieder starten in",
    "While paused there is no monitoring and there are no alarms.": "Während der Pause gibt es keine Überwachung und keine Alarme.",
    "Program is pausing …": "Programm wird pausiert …", "a restart is already running": "ein Neustart läuft bereits",
    "Night report: push message in the morning with what happened in the night": "Nachtbericht: Push-Nachricht am Morgen mit dem, was in der Nacht los war",
    "Note animals, persons and noises (animal diary + night report)": "Tiere, Personen und Geräusche notieren (Tier-Tagebuch + Nachtbericht)",
    "The night starts at (o'clock)": "Die Nacht beginnt um (Uhr)", "Send the report at (o'clock)": "Bericht senden um (Uhr)",
    "Keep diary entries (days, ★ always)": "Tagebuch-Einträge behalten (Tage, ★ immer)",
    "Powerbank capacity (mAh, as on the label; 0 = off)": "Kapazität der Powerbank (mAh, wie aufgedruckt; 0 = aus)",
    "Other devices (W): camera, USB, servos": "Weitere Geräte (W): Kamera, USB, Servos",
    "Send now": "Jetzt senden", "Open animal diary (browser)": "Tier-Tagebuch öffnen (Browser)", "Battery is full now": "Akku ist jetzt voll",
    "Create link (24 h)": "Link erstellen (24 h)", "Create link (no limit)": "Link erstellen (unbegrenzt)", "End guest access": "Gast-Zugang beenden",
    "Copy link": "Link kopieren", "Guest access is off": "Gast-Zugang ist aus", "Guest access is on": "Gast-Zugang ist an", "until": "bis",
    "no time limit": "unbegrenzt", "watching": "schauen zu", "Last report": "Letzter Bericht", "sent": "gesendet", "not sent": "nicht gesendet",
    "No report sent yet - the first one comes in the morning.": "Noch kein Bericht – der erste kommt am Morgen.",
    "Off - enter the capacity of the powerbank.": "Aus – Kapazität der Powerbank eintragen.",
    "Press 'Battery is full now' after charging.": "Nach dem Laden «Akku ist jetzt voll» drücken.", "left": "übrig", "estimated": "geschätzt",
    "The guest must be able to reach the Pi: same Wi-Fi / hotspot or Tailscale.": "Der Gast muss den Pi erreichen können: selbes WLAN / Hotspot oder Tailscale.",
    "Link copied": "Link kopiert", "unknown entry": "unbekannter Eintrag",
    "nobody from outside": "niemand von aussen",
    "remote access (somebody watches from outside)": "Fernzugriff (jemand schaut von aussen zu)",
    "Push message when somebody watches from outside (Tailscale)": "Push-Nachricht, wenn jemand von aussen zuschaut (Tailscale)", "Statistics": "Statistiken", "Panels": "Bereiche",
    "Settings sections": "Einstellungsabschnitte", "Title": "Titel", "Header buttons": "Schaltflächen oben",
    "Persons": "Personen", "Objects": "Objekte", "Light level": "Lichtverhältnisse", "Persons now": "Personen jetzt",
    "Detections": "Erkennungen", "Vehicles ignored": "Fahrzeuge ignoriert", "Shadow % removed": "Schatten % entfernt",
    "Camera control": "Kamerasteuerung", "Weather": "Wetter", "System · CPU": "System · CPU", "Event log": "Ereignisprotokoll",
    "Settings status": "Einstellungs-Status", "OBJECTS": "OBJEKTE", "CAMERA CONTROL": "KAMERASTEUERUNG", "RELAYS": "RELAIS",
    "Step": "Schritt", "Arrow keys move the camera": "Pfeiltasten bewegen die Kamera", "MANUAL": "MANUELL",
    "Manual control - tracking / patrol paused": "Handsteuerung - Verfolgung / Patrouille pausiert",
    "Tracking person": "Person wird verfolgt", "Pan": "Schwenk", "Tilt": "Neigung", "+ Waypoint": "+ Wegpunkt",
    "Centre": "Mitte", "no relays": "keine Relais", "needs AI model": "braucht das KI-Modell", "Hold (s)": "Halten (s)",
    "Active low": "Low-aktiv", "Remove relay": "Relais entfernen", "Remove this relay?": "Dieses Relais entfernen?",
    "+ Add relay": "+ Relais hinzufügen", "Manual control pause (s)": "Pause nach Handsteuerung (s)",
    "Double-click video: video only · F11: fullscreen · Esc: back · Ctrl+B: settings panel · right-click video: show / hide fields":
        "Doppelklick aufs Video: nur Video · F11: Vollbild · Esc: zurück · Strg+B: Einstellungsbereich · Rechtsklick aufs Video: Felder ein-/ausblenden",
    RELAY_NOTE: "Auto: Das Relais schaltet ein, solange sein Auslöser im Bild ist, und bleibt für die Haltezeit an. "
                "Tier- und Objekt-Auslöser (z. B. Katze) brauchen das KI-Modell. "
                "Der Voralarm schaltet schon bei der ersten Bewegung im Bild ein, lange bevor eine Person bestätigt ist. "
                "Fernzugriff schaltet ein, solange jemand über Tailscale zuschaut – auch bei Schutz aus (z. B. kleine Warnlampe).",
    # relay triggers (COCO object names)
    "person": "Person", "motion (anything)": "Bewegung (alles)", "animal (any)": "Tier (alle)", "cat": "Katze", "dog": "Hund",
    "bird": "Vogel", "car": "Auto", "truck": "Lkw", "bicycle": "Fahrrad", "motorcycle": "Motorrad", "bus": "Bus",
    "horse": "Pferd", "sheep": "Schaf", "cow": "Kuh", "elephant": "Elefant", "bear": "Bär", "zebra": "Zebra",
    "giraffe": "Giraffe", "airplane": "Flugzeug", "train": "Zug", "boat": "Boot", "traffic light": "Ampel",
    "fire hydrant": "Hydrant", "stop sign": "Stoppschild", "parking meter": "Parkuhr", "bench": "Bank",
    "backpack": "Rucksack", "umbrella": "Regenschirm", "handbag": "Handtasche", "tie": "Krawatte", "suitcase": "Koffer",
    "frisbee": "Frisbee", "skis": "Ski", "snowboard": "Snowboard", "sports ball": "Ball", "kite": "Drachen",
    "skateboard": "Skateboard", "surfboard": "Surfbrett", "bottle": "Flasche", "cup": "Tasse", "chair": "Stuhl",
    "couch": "Sofa", "potted plant": "Topfpflanze", "bed": "Bett", "dining table": "Esstisch", "tv": "Fernseher",
    "laptop": "Laptop", "cell phone": "Handy", "book": "Buch", "clock": "Uhr", "vase": "Vase", "scissors": "Schere",
    "teddy bear": "Teddybär", "knife": "Messer", "bowl": "Schüssel", "banana": "Banane", "apple": "Apfel", "pizza": "Pizza",
    # relay errors
    "unknown relay": "unbekanntes Relais", "GPIO must be a number": "GPIO muss eine Zahl sein",
    "GPIO must be between 2 and 27": "GPIO muss zwischen 2 und 27 liegen", "mode must be off / on / auto": "Modus muss Aus / Ein / Auto sein",
    "unknown trigger": "unbekannter Auslöser", "hold time must be a number": "Haltezeit muss eine Zahl sein",
    "unknown field": "unbekanntes Feld", "no free GPIO left": "kein freier GPIO mehr", "unknown action": "unbekannte Aktion",
}


DE.update({
    "Fixed times": "Feste Zeiten", "Sunset → sunrise": "Sonnenuntergang → Sonnenaufgang", "Sunrise → sunset": "Sonnenaufgang → Sonnenuntergang",
    "Shift (minutes)": "Versatz (Minuten)", "Time window": "Zeitfenster", "Applies": "Gilt", "Always": "Immer",
    "Only when nobody is home": "Nur wenn niemand zuhause ist", "Only when somebody is home": "Nur wenn jemand zuhause ist",
    "Skip dates": "Ausnahmedaten", "Clear": "Löschen", "set": "gesetzt", "Test notification": "Test-Nachricht senden",
    "Open camera grid (browser)": "Kamera-Übersicht öffnen (Browser)", "Open zone editor (browser)": "Zonen-Editor öffnen (Browser)",
    "Notification type": "Art der Benachrichtigung", "Webhook / ntfy URL": "Webhook- / ntfy-URL", "Telegram bot token": "Telegram-Bot-Token",
    "GitHub key (token) - only for a private repository": "GitHub-Schlüssel (Token) – nur für ein privates Repository",
    "invalid GitHub key (it starts with github_pat_ or ghp_)": "ungültiger GitHub-Schlüssel (er beginnt mit github_pat_ oder ghp_)",
    "not found - is the repository private? Then enter the GitHub key (token)": "nicht gefunden – ist das Repository privat? Dann den GitHub-Schlüssel (Token) eintragen",
    "GitHub refused the key - check that it is valid and may read this repository": "GitHub hat den Schlüssel abgelehnt – prüfen, ob er gültig ist und dieses Repository lesen darf",
    "Telegram chat id": "Telegram-Chat-ID", "Address of this page for links (e.g. https://pi.local:5000)": "Adresse dieser Seite für Links (z. B. https://pi.local:5000)",
    "Latitude (sunrise / sunset)": "Breitengrad (Sonnenauf-/untergang)", "Longitude (sunrise / sunset)": "Längengrad (Sonnenauf-/untergang)",
    "Phones / devices for presence (IP or name, comma separated)": "Handys / Geräte für Anwesenheit (IP oder Name, mit Komma getrennt)",
    "Setup": "Einrichtung", "Away after N minutes without answer": "Abwesend nach N Minuten ohne Antwort",
    "Pre-roll: video before the detection (s)": "Vorlauf: Video vor der Erkennung (s)",
    "In the dark also brighten the picture you see (live, recordings)": "Im Dunkeln auch das sichtbare Bild aufhellen (Live, Aufnahmen)", "Show zones in the picture": "Zonen im Bild zeigen",
    "Cameras": "Kameras", "Zones": "Zonen", "Live": "Live", "Recordings": "Aufzeichnungen", "Manual": "Anleitung",
    "invalid value": "ungültiger Wert", "out of range": "ausserhalb des erlaubten Bereichs", "invalid device name or address": "ungültiger Gerätename oder ungültige Adresse",
    "invalid URL (http:// or https:// expected)": "ungültige URL (http:// oder https:// erwartet)", "invalid Telegram bot token": "ungültiger Telegram-Bot-Token",
    "invalid Telegram chat id": "ungültige Telegram-Chat-ID", "this camera is already in use": "diese Kamera wird schon benutzt",
    "notification is not configured": "Benachrichtigung ist nicht eingerichtet", "invalid zones": "ungültige Zonen", "not a number": "keine Zahl",
    "Remove this network camera?": "Diese Netzwerk-Kamera entfernen?", "Remove this schedule?": "Diesen Zeitplan entfernen?",
    "off": "aus", "Video source": "Videoquelle", "Schedule": "Zeitplan", "Source": "Quelle", "Snapshots": "Schnappschüsse",
    "Person tracking": "Personenverfolgung", "Auto relays": "Auto-Relais", "Auto relays enabled": "Auto-Relais aktiv",
    "Send notifications": "Benachrichtigungen senden",
    "Scan for cameras": "Nach Kameras suchen", "Scanning…": "Suche läuft …", "Remove network camera": "Netzwerk-Kamera entfernen",
    "Add network camera (RTSP / HTTP stream, Wi-Fi cams)": "Netzwerk-Kamera hinzufügen (RTSP / HTTP-Stream, WLAN-Kameras)",
    "Add": "Hinzufügen", "Automatic (first working USB camera)": "Automatisch (erste funktionierende USB-Kamera)",
    "+ Add schedule": "+ Zeitplan hinzufügen", "Edit schedule": "Zeitplan bearbeiten", "Edit": "Bearbeiten", "Days": "Tage",
    "From": "Von", "To": "Bis", "unchanged": "unverändert", "ON": "EIN", "OFF": "AUS", "Enabled": "Aktiv", "Save": "Speichern",
    "Cancel": "Abbrechen", "Features": "Funktionen", "no schedules": "keine Zeitpläne", "active now": "aktiv",
    "Open recordings preview (browser)": "Aufzeichnungs-Vorschau öffnen (Browser)",
    "connected": "verbunden", "connecting…": "verbinde …", "failed": "fehlgeschlagen", "switch failed": "Wechsel fehlgeschlagen", "still using": "weiter mit", "starting": "startet",
    "connection lost - reconnecting": "Verbindung verloren - verbinde neu", "in use": "in Benutzung",
    "Name": "Name", "Network camera": "Netzwerk-Kamera", "every day": "täglich", "none": "keine",
    "Web stream could not start (is flask installed?)": "Web-Stream konnte nicht starten (ist flask installiert?)",
    "Time must look like 07:30": "Die Zeit muss so aussehen: 07:30",
    SCHED_NOTE: "Solange ein Zeitplan aktiv ist, werden die gewählten Funktionen fest EIN oder AUS geschaltet. Danach gilt wieder "
                "deine eigene Einstellung. Wer von Hand schaltet, überstimmt den Zeitplan bis zu dessen nächster Änderung.",
    "unknown source": "unbekannte Quelle", "unknown network camera": "unbekannte Netzwerk-Kamera", "connected - only watching (another MoveEye steers the simulator)": "verbunden – schaut nur zu (ein anderes MoveEye steuert den Simulator)", "this is the main camera already": "das ist schon die Hauptkamera",
    "invalid URL (rtsp:// or http:// expected)": "ungültige URL (rtsp:// oder http:// erwartet)",
    "too many network cameras": "zu viele Netzwerk-Kameras", "invalid schedule": "ungültiger Zeitplan",
    "unknown schedule": "unbekannter Zeitplan",
})
DE.update({
    "Messages": "Nachrichtentexte", "standard": "Standard", "Device name (placeholder {name})": "Gerätename (Platzhalter {name})",
    "Person: title": "Person: Titel", "Person: text": "Person: Text", "Pre-alarm: title": "Voralarm: Titel", "Pre-alarm: text": "Voralarm: Text",
    "Thermal alarm: title": "Wärmebild-Alarm: Titel", "Thermal alarm: text": "Wärmebild-Alarm: Text",
    "Empty = standard text. Placeholders:": "Leer = Standardtext. Platzhalter:", "Send test message": "Testnachricht senden",
    "text too long or with control characters": "Text zu lang oder mit Steuerzeichen",
    "needs NetworkManager": "braucht NetworkManager", "paused (switched by hand)": "pausiert (von Hand geschaltet)",
    "own Wi-Fi on": "eigenes WLAN an", "searching known networks …": "suche bekannte Netze …",
    "Alarm & camping": "Alarm & Camping", "Detection": "Erkennung", "Camera & servos": "Kamera & Servos",
    "Recordings & timelapse": "Aufnahmen & Zeitraffer", "Thermal camera": "Wärmebild", "Relays & schedule": "Relais & Zeitplan",
    "System & network": "System & Netz", "Advanced": "Erweitert", "Notifications": "Benachrichtigungen",
    "Network": "Netzwerk", "Automatic: known networks (e.g. phone hotspot), otherwise own Wi-Fi": "Automatik: bekannte Netze (z. B. Handy-Hotspot), sonst eigenes WLAN",
    "Own Wi-Fi at boot": "Beim Hochfahren eigenes WLAN", "Only known networks": "Nur bekannte Netze",
    "Automatic: wait for a known network (s)": "Automatik: auf bekanntes Netz warten (s)",
    "Automatic: look for known networks every (min, 0 = never)": "Automatik: nach bekannten Netzen suchen alle (Min., 0 = nie)",
    "Autostart ON": "Autostart an", "Autostart OFF": "Autostart aus",
    "autostart needs systemd (Raspberry Pi OS)": "Autostart braucht systemd (Raspberry Pi OS)",
    "Camping / protection": "Camping / Schutz", "Armed (alarms)": "Schutz an (Alarme)", "Thermal alarm": "Wärmebild-Alarm",
    "Take the clock from the phone (when the Pi has no internet time)": "Uhrzeit vom Handy übernehmen (wenn der Pi keine Internetzeit hat)",
    "Alarm when a warm body moves inside the zones": "Alarm, wenn sich ein warmer Körper in den Zonen bewegt",
    "Only warm bodies that move (ignore warm stones, engines)": "Nur bewegte warme Körper (warme Steine, Motoren ignorieren)",
    "Thermal alarm: warmer than the scene by (%)": "Wärmebild-Alarm: wärmer als die Umgebung um (%)",
    "Thermal alarm: minimum size (% of the picture)": "Wärmebild-Alarm: Mindestgrösse (% des Bildes)",
    "Arming countdown (s)": "Countdown bis der Schutz startet (s)", "Own Wi-Fi: name": "Eigenes WLAN: Name",
    "Own Wi-Fi: password (8-63 characters)": "Eigenes WLAN: Passwort (8-63 Zeichen)", "warm body (thermal camera)": "warmer Körper (Wärmebild)",
    "the own Wi-Fi needs NetworkManager (Raspberry Pi OS Bookworm or newer)": "das eigene WLAN braucht NetworkManager (Raspberry Pi OS Bookworm oder neuer)",
    "Armed": "Schutz an", "Disarmed": "Schutz aus", "Arm (countdown)": "Schutz an (Countdown)", "Arm now": "Sofort an", "Disarm": "Schutz aus",
    "Camping profile": "Camping-Profil", "Camping ON": "Camping an", "Camping OFF": "Camping aus", "Own Wi-Fi ON": "Eigenes WLAN an",
    "Own Wi-Fi OFF": "Eigenes WLAN aus", "Armed in": "Schutz an in", "devices": "Geräte", "Clock": "Uhrzeit",
    "Saved": "Gespeichert",
    "Wi-Fi / hotspot": "WLAN / Hotspot", "Search networks": "Netze suchen", "Connect now": "Jetzt verbinden",
    "Only save (connects automatically)": "Nur speichern (verbindet automatisch)", "Forget network": "Netz vergessen",
    "Password": "Passwort", "prefer this network": "dieses Netz bevorzugen", "Searching …": "Suche läuft …",
    "Push message with the address when the Pi joins a network": "Push-Nachricht mit der Adresse, wenn der Pi in ein Netz kommt",
    "set a web password first (--web-password) - otherwise anybody in the network could change the Wi-Fi":
        "zuerst ein Web-Passwort setzen (--web-password) - sonst könnte jeder im Netz das WLAN umstellen",
    "invalid network name": "ungültiger Netzname", "the password must have 8 to 63 characters": "das Passwort muss 8 bis 63 Zeichen haben",
    "busy": "beschäftigt - bitte kurz warten", "unknown network": "unbekanntes Netz",
    "Wi-Fi management not available (NetworkManager / wpa_supplicant not found)": "WLAN-Verwaltung nicht verfügbar (NetworkManager / wpa_supplicant fehlt)",
    "could not connect (wrong password or too far away?)": "Verbindung nicht möglich (falsches Passwort oder zu weit weg?)",
    "calm": "ruhig", "breezy": "böig", "strong": "stark", "storm": "Sturm",
    "Alarm sound in the browser": "Alarmton im Browser",
    "Alarm sound in open browsers (switch on with the bell at the top)": "Alarmton in geöffneten Browsern (oben mit der Glocke einschalten)",
    "Wi-Fi": "WLAN", "not connected": "nicht verbunden", "Internet": "Internet", "online": "online", "offline": "offline",
    "Pre-alarm push": "Voralarm-Push", "Pre-alarm: min. time between messages (s)": "Voralarm: Mindestabstand zwischen Meldungen (s)",
    "Pre-alarm push: message at the first movement": "Voralarm-Push: Meldung bei der ersten Bewegung",
    "Pre-alarm push with a small picture": "Voralarm-Push mit kleinem Bild",
    "Timelapse": "Zeitraffer", "Thermal camera": "Wärmebildkamera", "Thermal overlay": "Wärmebild-Überlagerung",
    "Photo every N minutes": "Foto alle N Minuten", "Position: pan (%)": "Position: Schwenk (%)", "Position: tilt (%)": "Position: Neigung (%)",
    "Wait after moving (s)": "Wartezeit nach dem Fahren (s)", "Video: frames per second": "Video: Bilder pro Sekunde",
    "Max timelapse folder (GB)": "Max. Zeitraffer-Ordner (GB)", "Overlay strength": "Stärke der Überlagerung",
    "Hot areas only: warmest N percent": "Nur heisse Bereiche: wärmste N Prozent",
    "Timelapse active": "Zeitraffer aktiv", "Return to the previous position afterwards": "Danach zur vorherigen Position zurückfahren",
    "Overlay the thermal picture": "Wärmebild überlagern", "Show only the hot areas (people, animals, engines)": "Nur heisse Bereiche zeigen (Personen, Tiere, Motoren)",
    "Thermal camera (run the camera scan first)": "Wärmebildkamera (zuerst Kamera-Scan ausführen)", "Colours": "Farben",
    "inferno": "Inferno", "jet": "Jet", "hot": "Hot", "turbo": "Turbo", "grey": "Grau",
    "pre-alarm (any movement)": "Voralarm (jede Bewegung)",
    "Use current position": "Aktuelle Position übernehmen", "Photo now": "Foto jetzt", "Create video": "Video erstellen",
    "need at least 2 photos": "mindestens 2 Fotos nötig", "a video is already being made": "es wird schon ein Video erstellt",
    "next photo in": "nächstes Foto in", "making video": "Video wird erstellt", "off": "aus", "waiting: alarm has priority": "wartet: Alarm hat Vorrang", "waiting: manual control": "wartet: Handsteuerung",
    "moving to the photo position": "fährt zur Fotoposition", "photo saved": "Foto gespeichert",
    "no thermal camera selected": "keine Wärmebildkamera gewählt", "same camera as the main picture": "gleiche Kamera wie das Hauptbild",
    "connecting…": "verbinde …",
    # 1.7.6 audio + power
    "Microphone": "Mikrofon", "Loudspeaker": "Lautsprecher", "Audio": "Audio", "System default": "Systemstandard",
    "not connected": "nicht angeschlossen", "Siren (rising and falling)": "Sirene (auf- und abschwellend)",
    "Two-tone horn": "Zweiklang-Horn (Tatü-Tata)", "Fast beeps": "Schnelle Pieptöne", "Horn": "Hupe",
    "person alarm": "bei Personen-Alarm", "person, thermal and noise alarm": "bei Personen-, Wärme- und Geräusch-Alarm",
    "every alarm, also the pre-alarm (movement)": "bei jedem Alarm, auch beim Voralarm (Bewegung)",
    "Siren at an alarm (only when armed)": "Sirene bei Alarm (nur wenn der Schutz an ist)", "Sound": "Ton",
    "Noise alarm: title": "Geräusch-Alarm: Titel", "Noise alarm: text": "Geräusch-Alarm: Text",
    "Microphone gain (dB)": "Mikrofon-Verstärkung (dB)", "Noise alarm: louder than the background by (dB)": "Geräusch-Alarm: lauter als der Hintergrund um (dB)",
    "Noise alarm: at least (s)": "Geräusch-Alarm: mindestens (s)", "Volume (%)": "Lautstärke (%)", "Duration of the siren (s)": "Dauer der Sirene (s)",
    "Siren: min. pause between two alarms (s)": "Sirene: min. Pause zwischen zwei Alarmen (s)",
    "Noise alarm: alarm when it gets loud (cracking, rustling, voices)": "Geräusch-Alarm: Alarm, wenn es laut wird (Knacken, Rascheln, Stimmen)",
    "Noise alarm: push message": "Geräusch-Alarm: Push-Nachricht", "Sound in the recordings": "Ton in den Aufnahmen",
    "Noise alarm": "Geräusch-Alarm", "noise (microphone)": "Geräusch (Mikrofon)",
    "no loudspeaker selected": "kein Lautsprecher gewählt", "no microphone selected": "kein Mikrofon gewählt",
    "aplay is missing (sudo apt install alsa-utils)": "aplay fehlt (sudo apt install alsa-utils)",
    "arecord is missing (sudo apt install alsa-utils)": "arecord fehlt (sudo apt install alsa-utils)",
    "sound file not found": "Tondatei nicht gefunden", "the sound file could not be read": "die Tondatei konnte nicht gelesen werden",
    "Shut down Pi": "Pi ausschalten", "Restart Pi": "Pi neu starten", "Shut down the Raspberry Pi now?": "Raspberry Pi jetzt herunterfahren?",
    "Restart the Raspberry Pi now?": "Raspberry Pi jetzt neu starten?",
    "A running recording is finished first. To switch it on again: unplug the power and plug it in again.":
        "Eine laufende Aufnahme wird vorher abgeschlossen. Wieder einschalten: Strom aus- und wieder einstecken.",
    "The Pi is shutting down …": "Der Pi fährt herunter …", "The Pi is restarting …": "Der Pi startet neu …",
    "Test sound": "Testton", "Siren now": "Sirene jetzt", "Stop": "Stopp", "Search devices": "Geräte suchen",
    "microphone on": "Mikrofon an", "starting …": "startet …", "playing …": "spielt …", "background": "Hintergrund",
    "noise alarm from": "Geräusch-Alarm ab", "Own sounds (.wav / .mp3): put the files into": "Eigene Töne (.wav / .mp3): Dateien ablegen in",
    "Push message when less free space than (MB)": "Push-Nachricht, wenn weniger frei ist als (MB)",
    "the password was given on the command line (--web-password) - change it there": "das Passwort wurde beim Start angegeben (--web-password) - dort ändern",
    "the password must have 6 to 64 characters (letters, digits, signs, no umlauts)": "das Passwort braucht 6 bis 64 Zeichen (Buchstaben, Ziffern, Zeichen, keine Umlaute)",
    "not a MoveEye settings file": "keine MoveEye-Einstellungsdatei", "Web password": "Web-Passwort", "set": "gesetzt",
    "Set password": "Passwort setzen", "Remove password": "Passwort entfernen", "Save settings …": "Einstellungen sichern …",
    "Load settings …": "Einstellungen laden …", "under-voltage": "Unterspannung", "free": "frei", "Supply": "Strom",
    "awake": "wach", "Power saving": "Stromsparen", "Pictures per second while quiet": "Bilder pro Sekunde, wenn ruhig",
    "Full speed after an event for (s)": "Nach einem Ereignis volle Geschwindigkeit für (s)",
    "Full speed while somebody watches the live picture": "Volle Geschwindigkeit, solange jemand das Livebild anschaut",
    "Bluetooth": "Bluetooth", "Search Bluetooth": "Bluetooth suchen", "Connect": "Verbinden", "Disconnect": "Trennen",
    "searching …": "Suche läuft …", "connected": "verbunden", "paired": "gekoppelt",
    "invalid Bluetooth address": "ungültige Bluetooth-Adresse", "bluetoothctl is missing (sudo apt install bluez)": "bluetoothctl fehlt (sudo apt install bluez)",
    "pairing failed - is the loudspeaker in pairing mode (blue light blinking)?": "Koppeln fehlgeschlagen - ist der Lautsprecher im Kopplungsmodus (blaues Licht blinkt)?",
    "could not connect - switch the loudspeaker on and bring it closer": "keine Verbindung - Lautsprecher einschalten und näher zum Pi bringen",
    "Bluetooth sound needs the program as normal user (not with sudo / not as system service)": "Bluetooth-Ton geht nur, wenn das Programm als normaler Benutzer läuft (nicht mit sudo / nicht als System-Dienst)",
    "paplay is missing (sudo apt install pulseaudio-utils)": "paplay fehlt (sudo apt install pulseaudio-utils)",
    "the Bluetooth loudspeaker is being connected - try again in a few seconds": "der Bluetooth-Lautsprecher wird verbunden - in ein paar Sekunden nochmals versuchen",
    "Updates": "Updates", "Search versions": "Nach Versionen suchen", "Switch to this version": "Zu dieser Version wechseln",
    "Running now": "Läuft jetzt", "searched at": "gesucht um", "list from": "Liste vom", "running now": "läuft jetzt", "on the Pi": "auf dem Pi", "available": "verfügbar", "Searching …": "Suche läuft …",
    "Switch to version": "Zu Version wechseln", "Downloading and checking …": "Wird geladen und geprüft …", "Switching to version": "Wechsle zu Version",
    "The program restarts (about 20 seconds). Settings, recordings and zones stay.": "Das Programm startet neu (ca. 20 Sekunden). Einstellungen, Aufnahmen und Zonen bleiben.",
    "Where new versions come from (address of versions.json, or a folder e.g. USB stick)": "Woher neue Versionen kommen (Adresse von versions.json oder ein Ordner, z. B. USB-Stick)",
    "https://... address or a folder (/media/...) expected": "https://...-Adresse oder ein Ordner (/media/...) erwartet",
    "set a web password first - otherwise anybody in the network could install a program": "zuerst ein Web-Passwort festlegen - sonst könnte jeder im Netz ein Programm installieren",
    "an update is already running": "es läuft schon ein Update", "unknown version": "unbekannte Version", "this version is already running": "diese Version läuft schon",
    "the file does not look like MoveEye": "die Datei ist kein MoveEye", "the file is damaged (checksum does not match) - try again": "die Datei ist beschädigt (Prüfsumme stimmt nicht) - nochmals versuchen",
    "the file is not a working Python program": "die Datei ist kein lauffähiges Python-Programm", "folder not found": "Ordner nicht gefunden",
    "Fine-tuning": "Feineinstellungen", "Light & sound": "Licht & Ton", "Protection & network": "Schutz & Netzwerk",
    "Push messages": "Push-Nachrichten", "Switches": "Schalter", "Power saving mode: fewer pictures while all is quiet": "Stromsparmodus: weniger Bilder, solange alles ruhig ist",
    "Power saving: full speed while somebody watches the live picture": "Stromsparen: volle Geschwindigkeit, solange jemand das Livebild anschaut",
    "Power saving: pictures per second while quiet": "Stromsparen: Bilder pro Sekunde, wenn ruhig",
    "Power saving: full speed after an event for (s)": "Stromsparen: nach einem Ereignis volle Geschwindigkeit für (s)",
    "power saving": "Stromsparen", "few pictures": "wenige Bilder", "full speed": "volle Geschwindigkeit",
    "Power ON": "Ein", "Power": "Ein / Aus", "Lights": "Licht", "night": "Nacht", "day": "Tag", "ON": "AN", "Servo driver": "Servo-Treiber", "channel": "Kanal",
    "White light: connected to": "Weisses Licht: angeschlossen an", "White light: Auto means": "Weisses Licht: «Auto» heisst",
    "Infrared light: connected to": "Infrarot-Licht: angeschlossen an", "Infrared light: Auto means": "Infrarot-Licht: «Auto» heisst",
    "Picture": "Bild", "at an alarm, only at night": "bei Alarm, nur nachts", "at an alarm, day and night": "bei Alarm, Tag und Nacht",
    "the whole night (sunset to sunrise)": "die ganze Nacht (Sonnenuntergang bis -aufgang)", "colour": "farbig",
    "grey at night (good with a NoIR camera)": "nachts grau (gut mit NoIR-Kamera)", "always grey": "immer grau",
    "automatic: PCA9685 if found, otherwise GPIO 17 / 27": "automatisch: PCA9685 falls gefunden, sonst GPIO 17 / 27",
    "directly on GPIO 17 / 27": "direkt an GPIO 17 / 27", "PCA9685 address (I2C)": "PCA9685-Adresse (I2C)",
    "Pan limit: max. degrees from the middle": "Schwenk-Grenze: max. Grad aus der Mitte",
    "Tilt limit: max. degrees from the middle": "Neige-Grenze: max. Grad aus der Mitte",
    "Light stays on after an alarm (s)": "Licht bleibt nach einem Alarm an (s)", "PCA9685 channel pan": "PCA9685-Kanal Schwenken",
    "PCA9685 channel tilt": "PCA9685-Kanal Neigen", "Push message when the CPU is hotter than (°C)": "Push-Nachricht, wenn die CPU heisser ist als (°C)",
    "Thermal: zoom - part the camera sees (%)": "Wärmebild: Zoom - Ausschnitt der Kamera (%)",
    "Thermal: shift left / right (%)": "Wärmebild: verschieben links / rechts (%)", "Thermal: shift up / down (%)": "Wärmebild: verschieben oben / unten (%)",
    "White light": "Weisses Licht", "Infrared light": "Infrarot-Licht", "White": "Weiss", "Infrared": "Infrarot",
    "the Thermal-90 can only be used as thermal camera": "die Thermal-90 geht nur als Wärmebildkamera", "Speaking from the phone: volume boost (dB)": "Sprechen vom Handy: Lautstärke-Anhebung (dB)",
    "invalid sound data": "ungültige Tondaten", "the loudspeaker could not be opened": "der Lautsprecher konnte nicht geöffnet werden",
})


def tl_status_text(text):
    """Status strings with numbers (timelapse) for the desktop window."""
    m = re.fullmatch(r"next photo in (\d+) min", text or "")
    if m:
        return tr("next photo in") + " " + m.group(1) + " min"
    m = re.fullmatch(r"making video (\d+)/(\d+)", text or "")
    if m:
        return tr("making video") + " " + m.group(1) + "/" + m.group(2)
    return tr(text)


def tr_err(msg, lang=None):
    """Translate an error message (some contain numbers). Romansh: own text, otherwise German."""
    L = cur_lang(lang)
    if L == "en":
        return msg
    if L in ("fr", "it", "rm"):
        for pat, key in ((r"GPIO (\d+) is used by a servo", "GPIO {n} is used by a servo"), (r"GPIO (\d+) is already used by another relay", "GPIO {n} is already used by another relay"),
                         (r"GPIO (\d+) is used by the thermal camera", "GPIO {n} is used by the thermal camera"), (r"GPIO (\d+) is used by a light", "GPIO {n} is used by a light"),
                         (r"maximum (\d+) relays", "maximum {n} relays"), (r"maximum (\d+) schedules", "maximum {n} schedules"),
                         (r"maximum (\d+) extra cameras", "maximum {n} extra cameras")):
            m_ = re.fullmatch(pat, msg)
            if m_ and TRX[L].get(key):
                return TRX[L][key].format(n=m_.group(1))
        if TRX[L].get(msg):
            return TRX[L][msg]
        if L != "rm":
            return msg
    if msg.startswith("autostart is on, but it only starts after a login"):
        return "Autostart ist an, startet aber erst nach einer Anmeldung, bis du einmal ausführst: " + msg.split("run once: ", 1)[-1].replace("(or: ", "(oder: ")
    if msg.startswith("a system service exists"):
        return "Es gibt einen System-Dienst - ändern mit sudo oder entfernen: sudo systemctl disable --now motionwatch"
    if msg.startswith("the system service can only be switched off with sudo"):
        return "Der System-Dienst lässt sich nur mit sudo ausschalten: sudo systemctl disable motionwatch"
    m_ = re.match(r"^(login refused|cannot create the day folder|upload refused) \(HTTP (\d+)\)(.*)$", msg)
    if m_:
        return {"login refused": "Anmeldung abgelehnt", "cannot create the day folder": "Tagesordner kann nicht angelegt werden",
                "upload refused": "Hochladen abgelehnt"}[m_.group(1)] + f" (HTTP {m_.group(2)})" + (" – Benutzername / App-Passwort?" if m_.group(3) else "")
    if msg.startswith("update source not reachable"):
        rest = msg[len("update source not reachable"):]
        return "Update-Quelle nicht erreichbar" + (": " + DE.get(rest[2:], rest[2:]) if rest.startswith(": ") else rest)
    if msg.startswith("update failed"):
        rest = msg[len("update failed"):]
        return "Update fehlgeschlagen" + (": " + DE.get(rest[2:], rest[2:]) if rest.startswith(": ") else rest)
    if msg.startswith("no permission to shut down") or msg.startswith("no permission to restart"):
        what = "Herunterfahren" if msg.startswith("no permission to shut down") else "Neustarten"
        return f"keine Berechtigung zum {what} - einmalig erlauben mit: " + msg.split("with: ", 1)[-1]
    if msg.startswith("no permission to change Wi-Fi"):
        return "keine Berechtigung, das WLAN zu ändern - Programm mit sudo starten oder einmalig erlauben mit: " + msg.split("with: ", 1)[-1]
    for pat, de in ((r"GPIO (\d+) is used by a servo", r"GPIO \1 wird von einem Servo benutzt"),
                    (r"GPIO (\d+) is already used by another relay", r"GPIO \1 wird schon von einem anderen Relais benutzt"),
                    (r"GPIO (\d+) is used by the thermal camera", r"GPIO \1 wird von der Wärmebildkamera benutzt"),
                    (r"GPIO (\d+) is used by a light", r"GPIO \1 wird von einem Licht benutzt"),
                    (r"maximum (\d+) relays", r"maximal \1 Relais"),
                    (r"maximum (\d+) schedules", r"maximal \1 Zeitpläne"),
                    (r"maximum (\d+) extra cameras", r"maximal \1 Zusatzkameras")):
        if re.fullmatch(pat, msg):
            return re.sub(pat, de, msg)
    return DE.get(msg, msg)


def tr(text, lang=None):
    """Translate an English UI string into the current language. Missing: Romansh falls back to German, the others to English."""
    L = cur_lang(lang)
    if L == "en":
        return text
    if L == "de":
        return DE.get(text, text)
    return TRX[L].get(text) or (DE.get(text, text) if L == "rm" else text)


def trf(text, lang=None, **kw):
    """tr() for a text with {placeholders}."""
    try:
        return tr(text, lang).format(**kw)
    except (KeyError, IndexError, ValueError):
        return text.format(**kw)


def tr_status(s):
    """Translate a camera status like 'failed: …' or 'switch failed: … (still using …)'."""
    for key in ("switch failed", "failed"):
        if s.startswith(key + ":"):
            return tr(key) + s[len(key):].replace("(still using ", "(" + tr("still using") + " ")
    return tr(s)


THEMES = {
    "dark": {"bg": "#0a0e14", "panel": "#111822", "line": "#1f2b3a", "txt": "#e8eef5", "mut": "#8a9bb0",     # 2.96.4: = web page and simulator
             "acc": "#3b8cff", "red": "#ff4d4d", "grn": "#3fcf6b", "yel": "#e0a526", "blu": "#5aa9ff", "org": "#f59a4a",
             "pur": "#b794f6", "field": "#0c121a", "knob_off": "#2a3542", "badge_red_bg": "#1a1216"},
    "light": {"bg": "#eef2f7", "panel": "#ffffff", "line": "#d7dfea", "txt": "#18212d", "mut": "#5a6b80",
              "acc": "#1f6feb", "red": "#d1242f", "grn": "#1a8f3c", "yel": "#9a6700", "blu": "#0969da", "org": "#bc4c00",
              "pur": "#8250df", "field": "#f2f5fa", "knob_off": "#c4ccd8", "badge_red_bg": "#ffecec"},
}


