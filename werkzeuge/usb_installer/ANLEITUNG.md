# USB-Stick: Simulator-PC neu aufsetzen

Für den HP EliteDesk 800 G1 DM. Der Stick installiert Ubuntu 24.04 LTS Server ohne Fragen. Danach startet der PC direkt
im Kiosk mit MoveEye Sim.

> ⚠️ **Die ganze interne Platte wird gelöscht.** Alles, was darauf ist, ist danach weg.

## 0. Daten sichern

Fotos, Dokumente, Einstellungen vom HP auf einen anderen Datenträger kopieren. Danach gibt es kein Zurück.

## 1. ISO laden

[ubuntu.com/download/server](https://ubuntu.com/download/server) → **Ubuntu Server 24.04.x LTS** →
Datei `ubuntu-24.04.x-live-server-amd64.iso` (ca. 3 GB).

## 2. Stick erstellen (Stick ab 4 GB, wird gelöscht)

**Linux** (Mint/Ubuntu), im Ordner `werkzeuge/usb_installer`:

```bash
sudo apt install xorriso
./stick_erstellen.sh ~/Downloads/ubuntu-24.04.x-live-server-amd64.iso
```

Fragt: Tastatur (`de` oder `ch`), Passwort für «don», WLAN (Enter = nur Kabel), SSH-Schlüssel, Stick
(z. B. `/dev/sdb`, zur Bestätigung zweimal eintippen). Braucht ca. 3 GB frei neben dem ISO.

**Windows** (mit [Ventoy](https://www.ventoy.net) und Git Bash):

1. Ventoy2Disk.exe → Stick wählen → *Install*.
2. In Git Bash im Ordner `werkzeuge/usb_installer`:
   `./stick_erstellen.sh /c/Users/<du>/Downloads/ubuntu-24.04.x-live-server-amd64.iso --nur-dateien /e/`
   (`/e/` = Laufwerk des Ventoy-Sticks).
3. Das ISO auf den Stick kopieren (ins Hauptverzeichnis, Name nicht ändern).
4. Beim Start: ISO wählen → Vorlage `/moveeye/user-data` wählen.

Rufus geht auch: unter Linux `--nur-iso` bauen, dann in Rufus das `moveeye-…iso` im **DD-Modus** schreiben.

## 3. Am HP starten

1. LAN-Kabel einstecken (empfohlen, das Installieren lädt Pakete).
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
| Installer bricht ab (rot) | meist kein Netz: LAN-Kabel prüfen, neu starten. Protokoll: `/var/log/installer/` |
| PC startet wieder ins Stick-Menü | Stick abziehen, neu starten |
| Kein Simulator nach dem ersten Start | kein Netz beim Download: Kabel prüfen, neu starten (versucht es wieder). Protokoll: `/var/log/moveeye-erststart.log` |
| Schwarzes Bild / Simulator stürzt ab | per SSH: `~/.moveeye_kiosk/sim.log` und `sitzung.log` ansehen |
| Tastatur falsch | `sudo dpkg-reconfigure keyboard-configuration` |
| Passwort vergessen | Stick neu erstellen, neu aufsetzen |

Ctrl+Alt+D (normales Mint) gibt es hier nicht – es ist nur der Kiosk installiert.
Der Stick enthält den Passwort-Hash (und ggf. das WLAN-Passwort): sicher aufbewahren oder neu formatieren.

## Warum dieser Weg

Linux: das offizielle ISO wird mit `xorriso` um die Autoinstall-Daten und einen eigenen ersten Menüpunkt ergänzt und dann
1:1 auf den Stick geschrieben. Ein Stick, ein Menüpunkt, kein Zusatzprogramm beim Start – und das Menü wartet auf Enter,
damit nichts aus Versehen gelöscht wird. Windows hat kein `xorriso`, darum dort Ventoy (gleiche `user-data`).
