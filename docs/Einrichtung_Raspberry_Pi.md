# Einrichtung auf dem Raspberry Pi 5 (MoveEye 2.98)

Für einen frischen Raspberry Pi 5 mit **Raspberry Pi OS Bookworm (64 Bit)**. Am einfachsten mit dem Einrichtungs-Skript
(Abschnitt 1); was es tut, steht in den Abschnitten 2–6 – so geht es auch von Hand.

## 1. Mit dem Skript (empfohlen)

Auf dem Pi im Terminal (als normaler Benutzer, **ohne** `sudo` davor – das Skript fragt selbst nach dem Passwort):

```
git clone https://github.com/DonElektro/MotionWatch.git
cd MotionWatch
bash werkzeuge/einrichten.sh --trocken     # zuerst nur ansehen, was es tun würde (ändert nichts)
bash werkzeuge/einrichten.sh               # einrichten
```

Ohne `git`: nur die Datei `werkzeuge/einrichten.sh` herunterladen und mit `bash einrichten.sh` starten – sie holt die neuste
MoveEye-Version selbst von GitHub (Prüfsumme aus `versions.json`).

Das Skript
1. installiert die Pakete (Abschnitt 2),
2. schaltet I2C, SPI und die Kamera ein (Abschnitt 3; die `config.txt` wird vorher gesichert),
3. legt MoveEye in den Ordner `~/MoveEye`,
4. gibt die Berechtigungen (`--allow-wifi`) und richtet den Autostart als Dienst ein (`--install-service`),
5. fragt, ob **Tailscale** (Fernzugriff) dazu soll,
6. lädt das KI-Modell (SSD, etwa 70 MB, von OpenCV geprüft) und – falls veröffentlicht – das eigene MoveEye-Modell
   (sha256 aus dem Manifest),
7. macht den Selbsttest und zeigt eine kurze Zusammenfassung (✓ / !) mit der Adresse der Webseite,
8. fragt **vor** einem nötigen Neustart.

Mehrmals laufen lassen schadet nicht: was schon da ist, wird übersprungen; gelöscht wird nichts.
Optionen: `--ja` (keine Rückfragen: kein Tailscale, kein Neustart), `--tailscale`, `--ordner ORDNER`, `--datei DATEI.py`.

## 2. Pakete (von Hand)

Bookworm erlaubt `pip install` nur in einer venv – darum alles aus den System-Paketen:

```
sudo apt update
sudo apt install python3-numpy python3-opencv python3-pil python3-pil.imagetk python3-tk python3-flask python3-psutil \
  python3-cryptography python3-gpiozero python3-picamera2 python3-smbus python3-spidev i2c-tools ffmpeg alsa-utils \
  openssl bluez pulseaudio-utils curl
```

Wärmebildkamera Thermal-90: im Waveshare-Wiki `Thermal_Camera_Hat.zip` laden, entpacken, im Ordner `pysenxor-master`
`pip install --break-system-packages -e ./` (oder in einer venv mit `--system-site-packages`).
Bluetooth-Lautsprecher und Tracker-Suche brauchen zusätzlich `bleak` (gleich installieren wie pysenxor).

## 3. I2C, SPI und Kamera

`sudo raspi-config` → Interface Options → I2C und SPI einschalten. Dann `sudo nano /boot/firmware/config.txt` und am
**Ende unter `[all]`** (nicht unter `[cm4]` / `[cm5]`!) eintragen:

```
[all]
dtparam=spi=on
dtparam=i2c_arm=on
dtoverlay=spi0-0cs
camera_auto_detect=1
```

Speichern (Strg+O), schliessen (Strg+X), neu starten. Prüfen: `ls /dev/spidev* /dev/i2c*`, `sudo i2cdetect -y 1`
(erwartet: 40 = Thermal-90, 41 = PCA9685 nach der Lötbrücke A0, 42 = UPS HAT) und `rpicam-hello --list-cameras`
(Camera Module 3 NoIR).

## 4. Berechtigungen und Autostart

```
sudo python3 webcam_bewegung_X_Y_Z.py --allow-wifi          # WLAN / eigenes WLAN, Uhr, Ausschalten, Hardware-Watchdog
sudo python3 webcam_bewegung_X_Y_Z.py --install-service     # Dienst «motionwatch»: startet beim Einschalten ohne Bildschirm
```

`--allow-wifi` nach grösseren Updates noch einmal auszuführen schadet nicht. Den Autostart kann man auch auf der Webseite
ein- und ausschalten (Einstellungen). Neue Versionen übernimmt der Dienst von selbst. Zustand: `systemctl status motionwatch`,
Protokoll: `journalctl -u motionwatch -f`.

## 5. Starten von Hand

```
python3 webcam_bewegung_X_Y_Z.py                       # Fenster + Webseite (Port 5000)
python3 webcam_bewegung_X_Y_Z.py --headless            # nur Webseite (ohne Bildschirm)
python3 webcam_bewegung_X_Y_Z.py --self-test .         # Selbsttest (im Ordner mit versions.json: auch die Signaturen)
python3 webcam_bewegung_X_Y_Z.py --help                # alle Optionen
```

Webseite: `http://<IP-des-Pi>:5000/`, im eigenen WLAN des Pi `http://10.42.0.1:5000/`. Beim ersten Öffnen fragt die Seite
nach einem **Web-Passwort** – unbedingt festlegen. Sichere Seite (Sprechen über den Lautsprecher): Port 5001 mit `https://`.
Die Seite hat sechs Reiter: **Live · Schutz · Verlauf · Einstellungen · Simulator · Mehr**; der Zustand heisst
**Aus / Wachsam / Voll**.

Einstellungen, Protokoll, Aufnahmen und Zertifikat liegen in `~/.config/motionwatch/` und bleiben bei neuen Versionen
erhalten. KI-Modelle: `~/.config/motionwatch/models/`. Eigene Töne (.wav / .mp3): `~/.config/motionwatch/sounds/`.

## 6. KI-Modell

Ohne KI-Modell meldet MoveEye nur Bewegung. Laden: im Selbstcheck oder unter Einstellungen → KI-Erkennung
«KI-Modell herunterladen» (SSD MobileNet V2, etwa 70 MB). Das **eigene MoveEye-Modell** (auf GitHub trainiert, siehe
`ki_training/README.md`): «Eigenes Modell herunterladen» – MoveEye nimmt es nur, wenn die sha256 stimmt.
Wie gut die KI echte Bilder erkennt, misst GitHub mit dem Echtbild-Prüfsatz (`ki_training/pruefsatz/LIESMICH.md`).

## 7. Updates

Unter Einstellungen → Updates als Quelle eintragen (falls noch leer):

```
https://raw.githubusercontent.com/DonElektro/MotionWatch/main/versions.json
```

MoveEye installiert **nur signierte** Versionen. Ohne Internet: die .py-Datei und `versions.json` auf einen USB-Stick
kopieren und als Quelle den Ordner eintragen, z. B. `/media/<benutzer>/STICK`.

## 8. Fernzugriff mit Tailscale

```
curl -fsSL https://tailscale.com/install.sh | sh      # oder: bash werkzeuge/einrichten.sh --tailscale
sudo tailscale up            # Link öffnen, mit demselben Konto anmelden wie auf dem Handy
tailscale ip -4              # Adresse 100.x.y.z
```

Auf dem Handy die Tailscale-App einschalten und `http://100.x.y.z:5000` öffnen. MoveEye zeigt die Tailscale-Adresse und
oben «🌐 Fern: Gerät», solange jemand von aussen zuschaut. Als App-Symbol speichern (Safari: Teilen → Zum Home-Bildschirm).

## 9. Noch nicht auf echter Hardware geprüft

Das Skript ist auf einem PC im Trockenlauf geprüft (`bash -n`, `--trocken`), noch nicht auf einem echten Pi 5. Ebenso
noch offen: Thermal-90 (pysenxor), Servos, Lautsprecher, Licht, Mikrofon, Akku-Anzeige – siehe `docs/Testabend_Checkliste.md`.
