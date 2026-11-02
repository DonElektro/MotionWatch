# USB-Stick: Simulator-PC neu aufsetzen

Für den HP EliteDesk 800 G1 DM. Der Stick installiert Ubuntu Server 24.04 LTS oder 26.04 LTS ohne Fragen. Danach startet der PC direkt
im Kiosk mit MoveEye Sim.

> ⚠️ **Die ganze interne Platte wird gelöscht.** Alles, was darauf ist, ist danach weg.

## 0. Daten sichern

Fotos, Dokumente, Einstellungen vom HP auf einen anderen Datenträger kopieren. Danach gibt es kein Zurück.

## 1. ISO laden

[ubuntu.com/download/server](https://ubuntu.com/download/server) → **Ubuntu Server 26.04.x LTS** (oder 24.04.x LTS) →
Datei `ubuntu-26.04.x-live-server-amd64.iso` bzw. `ubuntu-24.04.x-live-server-amd64.iso` (ca. 3 GB).
Beide gehen; 24.04 ist länger erprobt, 26.04 hat länger Updates (bis 2031).

## 2. Stick erstellen (Stick ab 4 GB, wird gelöscht)

**Linux** (Mint/Ubuntu), im Ordner `werkzeuge/usb_installer`:

```bash
sudo apt install xorriso
./stick_erstellen.sh ~/Downloads/ubuntu-26.04.x-live-server-amd64.iso
```

Fragt: Tastatur (`de` oder `ch`), Passwort für «don», WLAN (Enter = nur Kabel), SSH-Schlüssel, Stick
(z. B. `/dev/sdb`, zur Bestätigung zweimal eintippen). Braucht ca. 3 GB frei neben dem ISO.

**Windows** (mit [Ventoy](https://www.ventoy.net) und Git Bash):

1. Ventoy2Disk.exe → Stick wählen → *Install*.
2. In Git Bash im Ordner `werkzeuge/usb_installer`:
   `./stick_erstellen.sh /c/Users/<du>/Downloads/ubuntu-26.04.x-live-server-amd64.iso --nur-dateien /e/`
   (`/e/` = Laufwerk des Ventoy-Sticks).
3. Das ISO auf den Stick kopieren (ins Hauptverzeichnis, Name nicht ändern).
4. Beim Start: ISO wählen → Vorlage `/moveeye/user-data` wählen.

Rufus geht auch: unter Linux `--nur-iso` bauen, dann in Rufus das `moveeye-…iso` im **DD-Modus** schreiben.

## 3. Am HP starten

1. **LAN-Kabel einstecken** – nötig, das Installieren lädt Pakete aus dem Internet. Fehlt das Internet, erscheint
   **«KEIN INTERNET – LAN-Kabel einstecken, dann Enter»**, bevor etwas gelöscht wird; die Installation wartet dann.
   (`aus` + Enter schaltet den PC aus, ohne etwas zu löschen.)
2. Stick einstecken, einschalten, sofort mehrmals **F9** → *USB Hard Drive* (UEFI) wählen.
3. Menü: **«MoveEye: PC NEU AUFSETZEN»** → Enter. (Das Menü wartet; ohne Enter passiert nichts.)

Kein USB im F9-Menü: **F10** → *Advanced → Boot Options* → USB-Start einschalten. Secure Boot darf an bleiben.

## 4. Warten

- Installieren: ca. 20–40 Min. Danach **schaltet sich der PC aus**.
- **Stick abziehen**, PC einschalten.
- Erster Start: lädt den Simulator von GitHub, richtet den Kiosk ein (Text auf dem Bildschirm, einige Min.), startet neu.
- Danach: MoveEye Sim im Vollbild. Bei jedem Start wieder.

SSH von einem anderen PC: `ssh don@moveeye-sim` (oder `ssh don@<IP>`; IP im Router).
Firewall offen: 22 (SSH), 8765/TCP (Simulator). Sicherheitsupdates laufen automatisch (Neustart nachts um 04:30, falls nötig).
Kiosk wieder aus: `~/MoveEyeSim3D/kiosk_aus.sh`.

## 5. Fehlersuche

| Problem | Lösung |
|---|---|
| Stick fehlt im F9-Menü | F10 → USB-Start an; anderen USB-Anschluss (hinten) versuchen |
| Installer fragt «Continue with autoinstall?» | `yes` tippen (kommt bei Ventoy vor) |
| «KEIN INTERNET» | LAN-Kabel einstecken, Enter. Router an? Die Platte ist noch nicht gelöscht |
| Installer bricht ab (rot) | Protokoll: `/var/log/installer/`. Startet danach ein halbes System: Abschnitt 6 |
| PC startet wieder ins Stick-Menü | Stick abziehen, neu starten |
| Kein Simulator nach dem ersten Start | kein Netz beim Download: Kabel prüfen, neu starten (versucht es wieder). Protokoll: `/var/log/moveeye-erststart.log` |
| Schwarzes Bild / Simulator stürzt ab | per SSH: `~/.moveeye_kiosk/sim.log` und `sitzung.log` ansehen |
| Tastatur falsch | `sudo dpkg-reconfigure keyboard-configuration` |
| Passwort vergessen | Stick neu erstellen, neu aufsetzen |

Ctrl+Alt+D (normales Mint) gibt es hier nicht – es ist nur der Kiosk installiert.
Der Stick enthält den Passwort-Hash (und ggf. das WLAN-Passwort): sicher aufbewahren oder neu formatieren.

## 6. Installation abgebrochen? So rettest du sie

Gilt, wenn die Installation mittendrin abgebrochen hat (z. B. ohne Netz bei einem älteren Stick), der PC aber in ein
schwarzes Textfenster startet («moveeye-sim login:»). Anmelden als `don` mit deinem Passwort, LAN-Kabel einstecken.

**Tastatur zuerst:** `sudo loadkeys ch` (Schweiz) bzw. `sudo loadkeys de` (Deutschland).
Vorher ist oft die US-Tastatur aktiv: `y`/`z` vertauscht, `-` liegt auf der Taste `'` (ch) bzw. `ß` (de), `/` auf der
Taste `-`. Danach (ch und de): `/` = Shift+7, `|` = AltGr+7 (ch) bzw. AltGr+`<` (de), `>` = Shift+`<`.
`~` braucht es nicht – unten steht überall `/home/don` bzw. `/tmp`.

Internet prüfen: `ping -c 3 archive.ubuntu.com` (Antworten = gut).

**Kurzweg** (macht alles: Paketquelle, Pakete, erster Start, Neustart):

```bash
curl -fLo /tmp/erststart.sh https://raw.githubusercontent.com/DonElektro/MotionWatch/main/werkzeuge/usb_installer/erststart.sh
sudo bash /tmp/erststart.sh --retten
```

(ohne `curl`: `wget -O /tmp/erststart.sh` und dieselbe Adresse). Dauert 10–30 Min., danach Neustart in den Kiosk.

**Von Hand** (falls der Kurzweg nicht geht), Befehl für Befehl:

1. Paketquelle setzen – die alte `cdrom`-Quelle abschalten, die Online-Quelle eintragen:

   ```bash
   sudo sed -i 's/^deb.*cdrom.*/# &/' /etc/apt/sources.list
   grep -l cdrom /etc/apt/sources.list.d/*
   ```

   Zeigt `grep` eine Datei (z. B. `/etc/apt/sources.list.d/cdrom.sources`), sie zur Seite legen:
   `sudo mv /etc/apt/sources.list.d/cdrom.sources /root/`. Dann (der Name `resolute` bzw. `noble` kommt von selbst):

   ```bash
   sudo sh -c '. /etc/os-release; echo "deb http://archive.ubuntu.com/ubuntu $VERSION_CODENAME main restricted universe multiverse" >> /etc/apt/sources.list.d/moveeye.list'
   sudo sh -c '. /etc/os-release; echo "deb http://archive.ubuntu.com/ubuntu $VERSION_CODENAME-updates main restricted universe multiverse" >> /etc/apt/sources.list.d/moveeye.list'
   sudo sh -c '. /etc/os-release; echo "deb http://security.ubuntu.com/ubuntu $VERSION_CODENAME-security main restricted universe multiverse" >> /etc/apt/sources.list.d/moveeye.list'
   ```

2. Pakete installieren:

   ```bash
   sudo apt update
   sudo apt install -y xorg openbox lightdm lightdm-gtk-greeter x11-xserver-utils libgl1-mesa-dri libglx-mesa0 mesa-vulkan-drivers mesa-utils alsa-utils openssh-server ufw unattended-upgrades curl unzip wpasupplicant
   ```

3. Erster Start (lädt den Simulator, richtet Kiosk, Firewall und Updates ein, startet neu):

   ```bash
   curl -fLo /tmp/erststart.sh https://raw.githubusercontent.com/DonElektro/MotionWatch/main/werkzeuge/usb_installer/erststart.sh
   sudo install -m 755 /tmp/erststart.sh /usr/local/sbin/moveeye-erststart
   sudo moveeye-erststart --einrichten
   sudo moveeye-erststart
   ```

Fehlt der Benutzer `don` (`id don` meldet «no such user»): `sudo adduser don` und `sudo adduser don sudo`, dann von vorn.
Protokoll: `/var/log/moveeye-erststart.log`. Geht gar nichts: Stick neu erstellen (mit LAN-Kabel) und neu aufsetzen.

## Warum dieser Weg

Linux: das offizielle ISO wird mit `xorriso` um die Autoinstall-Daten und einen eigenen ersten Menüpunkt ergänzt und dann
1:1 auf den Stick geschrieben. Ein Stick, ein Menüpunkt, kein Zusatzprogramm beim Start – und das Menü wartet auf Enter,
damit nichts aus Versehen gelöscht wird. Windows hat kein `xorriso`, darum dort Ventoy (gleiche `user-data`).
