# Einrichtung auf dem Raspberry Pi 5 (Motion Watch 2.0.5)

## 1. Pakete

```
sudo apt update
sudo apt install python3-pil.imagetk python3-tk python3-gpiozero ffmpeg python3-picamera2 alsa-utils openssl bluez pulseaudio-utils
pip install opencv-python numpy pillow flask psutil        # in einer venv: --system-site-packages verwenden
```

Wärmebildkamera Thermal-90: im Waveshare-Wiki `Thermal_Camera_Hat.zip` laden, entpacken, im Ordner `pysenxor-master`:
`pip install -e ./` (dazu `spidev`, `smbus` bzw. `smbus2`).

## 2. I2C und SPI einschalten

`sudo raspi-config` → Interface Options → I2C und SPI einschalten. Dann `sudo nano /boot/firmware/config.txt`
und am **Ende unter `[all]`** (nicht unter `[cm4]` / `[cm5]`!) eintragen:

```
[all]
dtparam=spi=on
dtparam=i2c_arm=on
dtoverlay=spi0-0cs
```

Speichern (Strg+O), schliessen (Strg+X), neu starten. Prüfen: `ls /dev/spidev* /dev/i2c*` und `sudo i2cdetect -y 1`
(erwartet: 40 = Thermal-90, 41 = PCA9685 nach der Lötbrücke A0).

## 3. Einmalige Berechtigungen

```
sudo python3 webcam_bewegung_2_0_5.py --allow-wifi
```

Erlaubt dem normalen Benutzer: WLAN / eigenes WLAN, Uhrzeit, Autostart, Pi ausschalten / neu starten.
Schaltet ausserdem den Hardware-Watchdog ein (ein eingefrorener Pi startet nach 15 s von selbst neu).
Wer --allow-wifi schon früher ausgeführt hat: bitte mit der neuen Version noch einmal ausführen.

## 4. Starten

```
python3 webcam_bewegung_2_0_5.py                       # Fenster + Webseite (Port 5000)
python3 webcam_bewegung_2_0_5.py --headless            # nur Webseite (ohne Bildschirm)
python3 webcam_bewegung_2_0_5.py --web-password GEHEIM # Passwort beim Start (sonst auf der Webseite festlegen)
```

Webseite: `http://<IP-des-Pi>:5000/`, im eigenen WLAN des Pi `http://10.42.0.1:5000/`.
Sichere Seite (zum Sprechen über den Lautsprecher): Port 5001 mit `https://`.
Autostart: in der Webseite unter «Alarm & Camping» einschalten.

Einstellungen, Protokoll und Zertifikat liegen in `~/.config/motionwatch/` und bleiben bei neuen Versionen erhalten.
Eigene Töne (.wav / .mp3) für die Sirene: `~/.config/motionwatch/sounds/`.

## 5. Weitere Optionen

`--port`, `--source usb:0 | pi:0 | rtsp://…`, `--notify-url`, `--bind 127.0.0.1`, `--https`, `--config <ordner>`,
`--print-service`, `--install-service` (siehe `python3 webcam_bewegung_2_0_5.py --help`).

## 6. Updates über das Internet (GitHub)

Alle Versionen liegen im Repository **github.com/DonElektro/MotionWatch** (muss öffentlich sein).
Auf der Webseite unter «System & Netz → Updates» als Quelle eintragen:

```
https://raw.githubusercontent.com/DonElektro/MotionWatch/main/versions.json
```

«Nach Versionen suchen» → gewünschte Version → «Aktualisieren» bzw. «Wechseln». Danach erscheint unten «Neu laden».
Neue Version selbst veröffentlichen: Datei in den Repository-Ordner, `python3 webcam_bewegung_X_Y_Z.py --make-manifest .`,
beide Dateien hochladen.

Ohne Internet: die .py-Dateien auf einen USB-Stick kopieren und als Quelle den Ordner eintragen, z. B. `/media/<benutzer>/STICK`.

## 7. Fernzugriff mit Tailscale

```
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up            # Link öffnen, mit demselben Konto anmelden wie auf dem Handy
tailscale ip -4              # Adresse 100.x.y.z
```

Auf dem Handy die Tailscale-App einschalten und `http://100.x.y.z:5000` öffnen. Motion Watch zeigt unter System die
Tailscale-Adresse und oben «🌐 Fern: Gerät», solange jemand von aussen zuschaut.
Als App-Symbol speichern (Safari: Teilen → Zum Home-Bildschirm): über die Heimadresse grün «MW Intern», über Tailscale rot «MW Extern».
