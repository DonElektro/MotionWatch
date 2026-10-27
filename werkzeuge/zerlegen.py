#!/usr/bin/env python3
"""Einmalig (und bei Bedarf wieder): zerlegt eine fertige webcam_bewegung_X.py in die Teile in quelle/.

Die Teile sind nach Thema geordnet; werkzeuge/bauen.py setzt sie wieder genau gleich zusammen (Byte für Byte).
Jeder Teil beginnt mit einer Kopfzeile «#@ …», die beim Bauen wegfällt.

  python3 werkzeuge/zerlegen.py webcam_bewegung_2_95_62.py
"""
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
QUELLE = os.path.join(REPO, "quelle")

# (Dateiname, erste Zeile des Teils als regulärer Ausdruck, Beschreibung). Die Reihenfolge ist die der Datei.
TEILE = [
    ("000_kopf_aenderungen.py", None, "Kopf: Beschreibung und die Liste aller Änderungen (neueste oben)"),
    ("010_grundlagen.py", r"^import argparse", "Importe, Version (APP_VERSION), Ordner für Einstellungen"),
    ("020_einstellungen.py", r"^# Configuration \(everything", "CFG: alle Einstellungen mit Standardwerten"),
    ("030_zonen_anwesenheit_zeitplaene.py", r"^# Zones: polygons", "Zonen, Anwesenheit, Text-Einstellungen, Zeitpläne"),
    ("040_speichern_passwort.py", r"^# Settings persistence", "Einstellungen speichern, Web-Passwort"),
    ("050_meldungen_push.py", r"^# Notifications: webhook", "Meldungen (ntfy, Telegram, Webhook), Web-Push"),
    ("060_sicherung_schutz_klima.py", r"^# Backup: copy finished", "Sicherung, Diebstahlschutz, Linse, Klima, Wetter, Postausgang, Notifier"),
    ("070_hardware_servos_licht.py", r"^# Hardware: servos", "Servos, PCA9685, Mover, Licht, Disco-Licht"),
    ("080_waermebild_modul.py", r"^# Waveshare Thermal-90", "Treiber Wärmebild-Modul, Klasse Hardware"),
    ("090_system_fern_sichtungen.py", r"^# System monitor: CPU", "System, Fernzugriff, Sichtungen, Nachtbericht, Gast-Zugang"),
    ("100_akku.py", r"^# UPS HAT", "Akku / USV, Systemüberwachung"),
    ("110_netz_wlan.py", r"^# Network: Wi-Fi signal", "Netz, WLAN suchen und verbinden, QR-Codes"),
    ("120_eigenes_wlan_uhr_ort.py", r"^# Own Wi-Fi of the Pi", "eigenes WLAN, Uhr vom Handy, Ort (GPS) vom Handy"),
    ("130_scharf_profile_modi.py", r"^# Armed / disarmed", "Scharf / unscharf, Camping-Profil, einfache Einstellungen, Modi"),
    ("140_autostart.py", r"^# Autostart: when switched on", "Autostart"),
    ("150_zweites_wlan_tv_netzcheck.py", r"^# Second Wi-Fi adapter", "zweites WLAN, USB-Tethering, TV-Anzeige, Netz-Check, WLAN-Wächter"),
    ("160_netzautomatik_patrouille.py", r"^# Network automatic", "Netz-Automatik, Patrouille"),
    ("170_ki_personen.py", r"^# AI person detector", "KI-Modell laden und herunterladen"),
    ("180_ki_tierarten_helfer_tunnel.py", r"^# Animal species", "Tierarten, Alarm-Rückblick, KI-Rechenhilfe, KI-Prüfung, Tunnel, AIDetector"),
    ("190_relais_wetter_tracker.py", r"^# Relays: each one", "Relais, Wetter-Analyse, Auto-Tuner, Tracker"),
    ("200_erkennung_videoquellen.py", r"^# Main detector", "Video-Quellen (USB, Pi-Kamera, Netz)"),
    ("210_demo.py", r"^# Demo mode", "Demo-Modus"),
    ("220_zeitraffer.py", r"^# Timelapse:", "Zeitraffer"),
    ("230_waermebild.py", r"^# Thermal camera: a second", "Wärmebild-Überlagerung, Nachtsicht, Easter Egg (Herz)"),
    ("240_audio.py", r"^# Audio: microphone", "Mikrofon, Geräusch-Alarm"),
    ("250_klatschen_bluetooth_ton.py", r"^# Clap switch", "Klatschschalter, Bluetooth, Lautsprecher, Sprachausgabe"),
    ("260_mehrere_geraete.py", r"^# Several devices", "mehrere Motion-Watch-Geräte"),
    ("270_mqtt.py", r"^# MQTT / Home Assistant", "MQTT / Home Assistant"),
    ("280_sms_sensoren_sturm_gps_solar.py", r"^# SMS over an LTE", "SMS, Sensoren, Sturmwarnung, GPS, Solar"),
    ("290_simulator_verbindung.py", r"^# Simulator connection: a separate", "Verbindung zum Simulator"),
    ("300_werkzeuge_simulator3d.py", r"^# Tools \(page /tools\)", "Werkzeuge, 3D-Simulator für Windows und den Pi, Simulator-Suche"),
    ("310_testlaeufe.py", r"^# ---- test runs with evaluation", "Testläufe mit Auswertung und Optimierung"),
    ("320_spielecke.py", r"^# ---- game corner \(2\.95\.29\)", "Extras: Spielecke und Spieleabend"),
    ("330_usb_geraete.py", r"^# USB devices \(2\.95\.30\)", "USB-Geräte, Spielesammlung, Seite verlassen (✕ Zurück)"),
    ("340_spiele_seiten.py", r"^SPIELE_PAGE = ", "Extras: Seiten der Spielecke und des Spieleabends"),
    ("350_simulator_link.py", r"^class SimLink:", "Verbindung zum Simulator (Schleife)"),
    ("360_daten_simulator_python.py", r"^SIM_ZIP_B64 = ", "Daten: der Python-Simulator als ZIP"),
    ("370_rueckmeldung_teilen_abschreckung.py", r"^# Feedback to the developer", "Rückmeldung, Teilen, Abschreckung, Gegensprechen"),
    ("380_updates.py", r"^# Updates: choose a version", "Updates"),
    ("390_protokoll_bedienermodus.py", r"^# Event log on the SD card", "Protokoll, Bedienermodus, Pause, Update-Wächter"),
    ("400_ausschalten.py", r"^# Power: shut down", "Pi ausschalten / neu starten"),
    ("410_motionwatch_kern.py", r"^class MotionWatch:", "KERN: die Erkennungs-Schleife (Bewegung, Personen, Alarm)"),
    ("420_webzugang_aufnahmen.py", r"^# Web access options", "Web-Zugang, Aufnahmen, Speicher, Bild für andere Programme"),
    ("430_pdf_bericht.py", r"^# Event report \(PDF\)", "PDF-Bericht"),
    ("440_zusatzkameras.py", r"^# More cameras at the same time", "zusätzliche Kameras"),
    ("450_web_gemeinsam.py", r"^# Web stream \+ remote control", "Web: gemeinsames Aussehen (CSS), Bluetooth-Teil"),
    ("460_web_werkzeugseite.py", r"^TOOLS_PAGE = ", "Web: Seite Werkzeuge"),
    ("470_web_simulatorseite.py", r"^SIMMAP_JS = ", "Web: Seite Simulator"),
    ("480_daten_app_symbole.py", r"^APP_ICONS_PNG = ", "Daten: App-Symbole (PNG)"),
    ("490_daten_simulator_symbole.py", r"^SIM_ICONS_PNG = ", "Daten: Symbole der Simulatoren"),
    ("500_web_seitenbau.py", r"^APP_ICON_LIST = ", "Web: App-Symbol, Seiten zusammensetzen"),
    ("510_web_kopf_alarm.py", r"^SW_JS = ", "Web: Service Worker, Kopf, Alarm, gemeinsames JavaScript"),
    ("520_web_seiten_kameras_zonen_tagebuch.py", r"^CAMS_PAGE = ", "Web: Kameras, Zonen, Tagebuch, Gast, Protokoll"),
    ("530_web_hauptseite.py", r"^WEB_PAGE = ", "Web: Hauptseite"),
    ("540_web_anleitung_aufnahmen.py", r"^HELP_PAGE = ", "Web: Anleitung, Aufnahmen"),
    ("550_web_server.py", r"^class WebStream:", "Web: der Server (alle Adressen)"),
    ("560_uebersetzungen_de.py", r"^# Translations \(English text is the key", "Übersetzungen Deutsch"),
    ("570_fenster.py", r"^# Desktop GUI \(Tkinter\)", "Fenster auf dem Pi / PC (Tkinter)"),
    ("580_uebersetzungen_fr.py", r"^# Translations: French, Italian", "Übersetzungen Französisch"),
    ("590_uebersetzungen_it.py", r"^TRX\['it'\]\.update", "Übersetzungen Italienisch"),
    ("600_uebersetzungen_rm.py", r"^TRX\['rm'\]\.update", "Übersetzungen Rätoromanisch, Anleitungen"),
    ("610_anleitung_ergaenzungen.py", r"^# ---- guide: the parts added", "Anleitung: Ergänzungen in allen Sprachen"),
    ("620_daten_produktseite.py", r"^# ---- the product page \(2\.95\.52\)", "Daten: Produktseite für Gäste (/info/)"),
    ("630_almanach.py", r"^# ---- Überlebens-Almanach", "Extras: Überlebens-Almanach"),
    ("640_start.py", r'^if __name__ == "__main__":', "Start: Befehlszeile, Selbsttest, Programmstart"),
]
RULE = re.compile(r"^# -{20,}$")


def zerlegen(path):
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines(keepends=True)
    starts = [0]
    i = 0
    for name, rx, _ in TEILE[1:]:
        r = re.compile(rx)
        while i < len(lines) and not r.match(lines[i]):
            i += 1
        if i >= len(lines):
            sys.exit("Anfang nicht gefunden: %s (%s)" % (name, rx))
        s = i - 1 if i > 0 and RULE.match(lines[i - 1].rstrip("\n")) else i      # the banner line belongs to the part
        starts.append(s)
        i += 1
    starts.append(len(lines))
    os.makedirs(QUELLE, exist_ok=True)
    for f in os.listdir(QUELLE):
        if f.endswith(".py"):
            os.remove(os.path.join(QUELLE, f))
    for k, (name, _, desc) in enumerate(TEILE):
        part = "".join(lines[starts[k]:starts[k + 1]])
        head = "#@ Motion Watch – Teil %s: %s. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.\n" % (name[:3], desc)
        with open(os.path.join(QUELLE, name), "w", encoding="utf-8", newline="") as f:
            f.write(head + part)
    print("%d Teile in %s" % (len(TEILE), os.path.relpath(QUELLE, REPO)))


if __name__ == "__main__":
    zerlegen(sys.argv[1] if len(sys.argv) > 1 else "")
