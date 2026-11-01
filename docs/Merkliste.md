# MoveEye – Merkliste (offene Erinnerungen)

Stand: 01.11.2026, MoveEye 3.46.0. Wird im Haupt-Chat nachgeführt. Was vor der Veröffentlichung erledigt sein muss,
steht zusätzlich in der Abhak-Liste «MoveEye Startklar» (claude.ai/artifact/KhF1nTmGfBeZf6nZQpvX9D).

## Erst ganz am Schluss (vor Veröffentlichung)
- **Trailer** (Grossvater + Maggie) aufnehmen, sobald Grafik/Gelände fertig sind. Stand: Zweig `real-trailer-final`
  (1edd0c2, 7ccce3c), Aufnahme ca. 3–4 h pro Trailer, 720p, nacheinander. Vorher verbessern: verzerrte Felstextur in
  der tiefen Schlucht (Gelände zu tief), Wasserfall-Szene, Foto-Inhalte (Fehler 403).
- **SD-Karten-Image** (Raspberry Pi OS + MoveEye fertig eingerichtet), danach in der Werkstatt verlinken.
- **USB-Stick-Installer** Linux-Kiosk (`werkzeuge/usb_installer/`) final mit echtem ISO am HP testen.
- Produktfotos vom echten Gerät, Übersetzungen prüfen lassen, Schalter `projekt_veroeffentlicht` auf true.

## Erkennung
- Ziel ≥ 75 % erkannte Personen im Erkennungstest 3 (Basis 28 %, 9/32). Fix 5042c16 (Auto-Tune-Deckel, Wind-Regel
  kürzer, KI-Person sofort «Person?», aufrecht nie «Tier»), Zweig `real-erkennung-fix`. Kinder teils als «horse».
- Läuft, wenn sonst nichts läuft (Regel Daniel).

## Hardware / Bau
- Offene Entscheide: Lampentreiber + Widerstand, PCA9685 Original oder Nachbau, Wert Vorwiderstand IR-Modul (Kanal 4).
- Nachmessen: IR-Modul, Weitwinkel-Linse, Lage CAM0/CAM1, UPS HAT (E), USB-C/HDMI am Pi, SD-Halter (18 mm),
  Sicherungshalter.
- Mover: Masse folgen später (dann Platz im Gehäuse planen).
- Solo-Variante (nur Kamera) später: braucht Software-Option «kein Kopf» + Flachdeckel. Mobil später.
- «Varianten wählbar in Bauen» (Paket wählen → Teileliste/Schritte/Druckteile) noch nicht beauftragt.

## Verkauf
- Fixfertig bestellen läuft über die Rückmeldung (Bauen, Simulator-Werkstatt, Pi-Fenster, /info/).
  Vor Veröffentlichung klären: Preise, Lieferzeit, Gewährleistung, Rechtliches (Fachperson).
- Das Formular auf der öffentlichen Homepage kopiert nur in die Zwischenablage; echtes Senden nur über /info/ am Pi.

## Später / vorgemerkt
- Foto-Wunschliste (10 Sujets) wieder vorlegen: Camping, Nachtlicht, Kamera-Sicht, Tiere, Wetter, Jahreszeiten,
  Alpbetrieb, Wasser, Rastplatz, Gipfel (ohne Gesichter/Autonummern).
- Praxistest-Checkliste PC/iPad/Pi anbieten.
- Maggie-Feinschliff; Easter-Egg-Wand im Wärmebild kühler.
- Kapitel 6–8 der Bergtal-Geschichte (zweite Karte) – offen.
- Code-Prüfung: zwei hohe Funde später (Sim: Hospiz-Weiterspielen über /control ohne Passwort;
  MoveEye: Kartenlink im Kurzformat des Diebstahl-Alarms).
- Zwei MoveEye koppeln (nach Hardware-Aufbau), BME280-Erweiterungen.
