#!/bin/bash
# MoveEye Kiosk EIN - macht aus einem PC mit Linux Mint (Cinnamon, LightDM, x11) eine reine Simulator-Maschine.
#   ./kiosk_ein.sh             zeigt, was es tut, fragt einmal «Fortfahren? (j/n)», dann mit sudo
#   ./kiosk_ein.sh --trocken   zeigt nur, was passieren würde (ändert nichts, braucht kein sudo)
#   ./kiosk_ein.sh --ja        ohne Rückfrage
# Nichts wird deinstalliert oder gelöscht; alles macht ./kiosk_aus.sh wieder rückgängig (SSH bleibt).
# Sicherung und Protokoll: ~/.moveeye_kiosk/ . Mehrmals ausführen ist kein Problem (die erste Sicherung bleibt).
set -u
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
EXE="$DIR/MoveEyeSim3D.x86_64"
LIB="/usr/local/lib/moveeye-kiosk"
CONF="/etc/moveeye-kiosk.conf"
XSESSION="/usr/share/xsessions/moveeye-kiosk.desktop"
LDM_DROPIN="/etc/lightdm/lightdm.conf.d/99-moveeye-kiosk.conf"
LDM_CONF="/etc/lightdm/lightdm.conf"
MARKE="#moveeye-kiosk# "
# Dienste, die eine Simulator-Maschine nicht braucht (nur deaktiviert, nicht entfernt; Bluetooth bleibt für Tastaturen)
DIENSTE="cups.service cups.socket cups.path cups-browsed.service ModemManager.service kerneloops.service apport.service whoopsie.service"
SCHLAF="sleep.target suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target"
PAKETE="openbox openssh-server ufw python3-tk"   # python3-tk: Testbild während der Tests (testbild.py)

TROCKEN=0 JA=0
for a in "$@"; do
	case "$a" in
		--trocken|-n) TROCKEN=1 ;;
		--ja|-y) JA=1 ;;
		-h|--hilfe|--help) sed -n '2,7p' "$0"; exit 0 ;;
		*) echo "Unbekannte Option: $a (--trocken, --ja, --hilfe)"; exit 2 ;;
	esac
done

# --- wer: der angemeldete Benutzer (auch wenn jemand «sudo ./kiosk_ein.sh» tippt)
if [ "$(id -u)" -eq 0 ]; then
	BENUTZER="${SUDO_USER:-}"
	if [ -z "$BENUTZER" ] || [ "$BENUTZER" = root ]; then echo "Bitte als normaler Benutzer starten (ohne sudo): ./kiosk_ein.sh"; exit 1; fi
	SUDO=""
else
	BENUTZER="$(id -un)"
	SUDO="sudo"
fi
LESE="$SUDO"                                  # nur lesen (ufw status): im Trockenlauf nie nach dem Passwort fragen
[ $TROCKEN -eq 1 ] && [ -n "$SUDO" ] && LESE="sudo -n"
HEIM="$(getent passwd "$BENUTZER" | cut -d: -f6)"
[ -n "$HEIM" ] || HEIM="$HOME"
KD="$HEIM/.moveeye_kiosk"
SICH="$KD/sicherung"
STAMP="$(date +%Y%m%d_%H%M%S)"

als_benutzer() { if [ "$(id -u)" -eq 0 ]; then sudo -u "$BENUTZER" "$@"; else "$@"; fi; }
als_benutzer mkdir -p "$KD"
if [ $TROCKEN -eq 1 ]; then LOG="$KD/kiosk_ein_${STAMP}_trocken.log"; else LOG="$KD/kiosk_ein_${STAMP}.log"; fi
als_benutzer touch "$LOG"
exec > >(tee -a "$LOG") 2>&1

cat <<EOF
=== MoveEye Kiosk EIN ===$( [ $TROCKEN -eq 1 ] && echo "   (TROCKENLAUF: nichts wird geändert)" )
Benutzer: $BENUTZER    Simulator: $EXE
Das passiert:
 1. Fehlende Pakete installieren: $PAKETE (nichts wird deinstalliert)
 2. Sicherung des jetzigen Zustands nach $SICH (nur beim ersten Mal)
 3. Neue Sitzung «MoveEye Kiosk» (Openbox + Simulator im Vollbild, sendet an MoveEye, startet nach Absturz neu)
 4. Automatisch anmelden als $BENUTZER in diese Sitzung (LightDM)
 5. Bildschirmschoner, Sperre, Energiesparen und Suspend aus
 6. Unnötige Dienste deaktivieren (nicht entfernen): Drucker (cups), ModemManager, Fehlerberichte
 7. SSH-Server ein; Firewall (ufw): nur SSH 22, Simulator 8765/TCP, ausgehend 8764/UDP
Ctrl+Alt+D im Kiosk = normales Mint (Cinnamon); Abmelden = zurück in den Kiosk. Rückgängig: ./kiosk_aus.sh
Eigene Dateien im persönlichen Ordner werden nicht verändert. Protokoll: $LOG
EOF

if [ $JA -eq 0 ]; then
	read -r -p "Fortfahren? (j/n) " antwort
	case "$antwort" in j|J|ja|Ja|JA|y|Y) ;; *) echo "Abgebrochen - nichts geändert."; exit 0 ;; esac
fi

FEHLER=0
schritt() { echo; echo "--- $*"; }
tu() {   # einen Befehl mit Rechten ausführen (Trockenlauf: nur zeigen)
	if [ $TROCKEN -eq 1 ]; then echo "[trocken] $SUDO $*"; return 0; fi
	echo "+ $*"
	$SUDO "$@" || { echo "  (Fehler: $*)"; FEHLER=$((FEHLER + 1)); return 1; }
}
schreibe() {   # schreibe ZIEL MODUS  <inhalt  (mit Rechten; Trockenlauf: Inhalt zeigen)
	local ziel="$1" modus="$2" tmp
	tmp="$(mktemp)"; cat > "$tmp"
	if [ $TROCKEN -eq 1 ]; then
		echo "[trocken] würde schreiben: $ziel (Modus $modus)"; sed 's/^/           | /' "$tmp"
	else
		echo "+ schreibe $ziel"
		$SUDO install -D -m "$modus" "$tmp" "$ziel" || { echo "  (Fehler beim Schreiben von $ziel)"; FEHLER=$((FEHLER + 1)); }
	fi
	rm -f "$tmp"
}
sichere() {   # sichere NAME  <inhalt   (nur, wenn es die Sicherung noch nicht gibt)
	local f="$SICH/$1"
	if [ -e "$f" ]; then cat > /dev/null; echo "  Sicherung $1: schon da (bleibt vom ersten Mal)"; return 0; fi
	if [ $TROCKEN -eq 1 ]; then
		echo "[trocken] würde sichern: $f"; sed 's/^/           | /'
	else
		als_benutzer mkdir -p "$SICH"
		als_benutzer tee "$f" > /dev/null
		echo "  gesichert: $f"
	fi
}
einheit_da() { [ -n "$(systemctl list-unit-files --no-legend "$1" 2>/dev/null)" ]; }

# --- Vorprüfungen
schritt "Prüfen"
[ -x "$EXE" ] || { echo "MoveEyeSim3D.x86_64 fehlt in $DIR - den ganzen Ordner aus der ZIP entpacken und hier starten."; [ $TROCKEN -eq 1 ] || exit 1; }
DM="$(cat /etc/X11/default-display-manager 2>/dev/null)"
case "$DM" in *lightdm*) echo "Anmeldung: LightDM ($DM)" ;;
	*) echo "WARNUNG: Anmeldung ist nicht LightDM ('${DM:-unbekannt}') - automatisches Anmelden wird trotzdem für LightDM eingetragen." ;; esac
[ "${XDG_SESSION_TYPE:-x11}" = "wayland" ] && echo "WARNUNG: jetzt läuft Wayland - der Kiosk braucht x11 (Mint/Cinnamon: Standard)."
command -v systemctl >/dev/null || { echo "systemd fehlt - abgebrochen."; exit 1; }
if [ $TROCKEN -eq 0 ] && [ -n "$SUDO" ]; then
	echo "sudo fragt jetzt nach dem Passwort von $BENUTZER:"
	sudo -v || { echo "Ohne sudo geht es nicht - abgebrochen."; exit 1; }
fi

# --- 1. Pakete
schritt "1. Pakete"
FEHLT=""
for p in $PAKETE; do
	if dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed"; then echo "  $p: schon da"; else FEHLT="$FEHLT $p"; fi
done
if [ -n "$FEHLT" ]; then
	tu env DEBIAN_FRONTEND=noninteractive apt-get update -q
	# shellcheck disable=SC2086
	tu env DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends $FEHLT
	# shellcheck disable=SC2086
	[ $TROCKEN -eq 1 ] || printf '%s\n' $FEHLT | als_benutzer tee -a "$KD/pakete_von_kiosk.txt" > /dev/null
fi

# --- 2. Sicherung
schritt "2. Sicherung ($SICH)"
{
	for u in $DIENSTE; do
		einheit_da "$u" && printf '%s %s\n' "$u" "$(systemctl is-enabled "$u" 2>/dev/null || true)"
	done
} | sichere dienste_vorher.txt
{
	for u in $SCHLAF; do
		einheit_da "$u" && printf '%s %s\n' "$u" "$(systemctl is-enabled "$u" 2>/dev/null || true)"
	done
} | sichere schlaf_vorher.txt
{
	for f in /etc/xdg/autostart/*.desktop "$HEIM"/.config/autostart/*.desktop; do
		[ -e "$f" ] && echo "$f"
	done
} | sichere autostarts.txt
{
	echo "aktiv $( (LC_ALL=C $LESE ufw status 2>/dev/null || echo 'Status: unbekannt') | sed -n 's/^Status: //p' | head -n 1)"
	sed -n 's/^\(DEFAULT_INPUT_POLICY\|DEFAULT_OUTPUT_POLICY\)=/\1 /p' /etc/default/ufw 2>/dev/null | tr -d '"'
} | sichere ufw_vorher.txt
{
	if [ -r "$LDM_CONF" ]; then cat "$LDM_CONF"; else echo "# (keine $LDM_CONF)"; fi
} | sichere lightdm.conf_vorher
{
	for u in ssh.service ssh.socket; do
		z="$(systemctl is-enabled "$u" 2>/dev/null || true)"; echo "$u ${z:-fehlt}"
	done
} | sichere ssh_vorher.txt

# --- 3. Sitzung «MoveEye Kiosk»
schritt "3. Sitzung «MoveEye Kiosk»"
if [ $TROCKEN -eq 1 ]; then echo "[trocken] $SUDO install -D -m 755 $DIR/kiosk_sitzung.sh $LIB/kiosk_sitzung.sh"
else tu install -D -m 755 "$DIR/kiosk_sitzung.sh" "$LIB/kiosk_sitzung.sh"; fi
# Testbild während der Tests (Test-Runner): Programm und Logo neben die Sitzung (fehlen sie, bleibt der Bildschirm dunkel)
for f in testbild.py:testbild.py moveeye-sim.png:moveeye.png; do
	[ -r "$DIR/${f%%:*}" ] || { echo "  ${f%%:*} fehlt in $DIR (älteres Paket) - ohne Testbild"; continue; }
	if [ $TROCKEN -eq 1 ]; then echo "[trocken] $SUDO install -D -m 644 $DIR/${f%%:*} $LIB/${f##*:}"
	else tu install -D -m 644 "$DIR/${f%%:*}" "$LIB/${f##*:}"; fi
done
schreibe "$CONF" 644 <<EOF
# MoveEye Kiosk (kiosk_ein.sh, $(date '+%F %T')). Wird beim nächsten Start der Sitzung gelesen.
# SIM: Programmdatei des Simulators (das Update ersetzt sie am selben Ort). Ordner verschoben: kiosk_ein.sh dort neu starten.
SIM=$(printf '%q' "$EXE")
# vor «--» Godot (Vollbild), danach der Simulator: an MoveEye senden, beim Start nicht nach Updates fragen (niemand da)
SIM_ARGS=(--fullscreen -- --stream --no-update)
# Grafik-Modus (kiosk_sitzung.sh hängt «--grafik» an): normal (Standard, auch ohne diese Zeile) | auto | lite | hoch | "" (nichts)
#GRAFIK=normal
EOF
schreibe "$LIB/openbox.xml" 644 <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!-- MoveEye Kiosk: Openbox nur als schlanker Fenstermanager. Ctrl+Alt+D = normales Mint, Ctrl+Alt+R = Simulator neu,
     Ctrl+Alt+B = Controller koppeln (Bluetooth), Ctrl+Alt+Z = vom Browser zurück zum Simulator. Der Rand oben gehört der
     Leiste «Zurück zum Simulator» (browser_leiste.py); der Simulator im Vollbild nutzt ihn trotzdem. -->
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <focus><focusNew>yes</focusNew><followMouse>no</followMouse></focus>
  <placement><policy>Smart</policy></placement>
  <desktops><number>1</number></desktops>
  <keyboard>
    <keybind key="C-A-d"><action name="Execute"><command>/usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh desktop</command></action></keybind>
    <keybind key="C-A-r"><action name="Execute"><command>/usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh neustart</command></action></keybind>
    <keybind key="C-A-b"><action name="Execute"><command>/usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh koppeln</command></action></keybind>
    <keybind key="A-Tab"><action name="NextWindow"/></keybind>
    <keybind key="C-A-z"><action name="Execute"><command>/usr/local/lib/moveeye-kiosk/hp_knoepfe.sh zurueck</command></action></keybind>
  </keyboard>
  <mouse><context name="Root"></context></mouse>
  <margins><top>40</top><bottom>0</bottom><left>0</left><right>0</right></margins>
  <applications>
    <application class="*" type="normal"><decor>no</decor></application>
    <application class="?irefox*" type="normal"><decor>no</decor><maximized>yes</maximized><focus>yes</focus></application>
    <application class="?hromium*" type="normal"><decor>no</decor><maximized>yes</maximized><focus>yes</focus></application>
  </applications>
</openbox_config>
EOF
schreibe "$XSESSION" 644 <<'EOF'
[Desktop Entry]
Type=Application
Name=MoveEye Kiosk
Comment=Nur der MoveEye-Simulator im Vollbild (Ctrl+Alt+D: normales Mint)
Exec=/usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh sitzung
DesktopNames=MoveEye-Kiosk
EOF

# --- 4. Automatisch anmelden
schritt "4. Automatisch anmelden ($BENUTZER, Sitzung moveeye-kiosk)"
schreibe "$LDM_DROPIN" 644 <<EOF
# MoveEye Kiosk (kiosk_ein.sh). Entfernen: ./kiosk_aus.sh
[Seat:*]
autologin-user=$BENUTZER
autologin-user-timeout=0
autologin-session=moveeye-kiosk
EOF
# lightdm.conf wird NACH den Dateien in lightdm.conf.d gelesen: dortige autologin-Zeilen nur auskommentieren (mit Marke)
if [ -r "$LDM_CONF" ] && grep -Eq '^[[:space:]]*autologin-(user|user-timeout|session)[[:space:]]*=' "$LDM_CONF"; then
	echo "  $LDM_CONF hat eigene autologin-Zeilen - werden mit «$MARKE» auskommentiert (kiosk_aus.sh nimmt das zurück)"
	tu sed -i -E "s/^([[:space:]]*autologin-(user|user-timeout|session)[[:space:]]*=)/$MARKE\1/" "$LDM_CONF"
else
	echo "  $LDM_CONF: keine störenden autologin-Zeilen"
fi
for f in /etc/lightdm/lightdm.conf.d/*.conf; do
	[ -e "$f" ] && [ "$f" != "$LDM_DROPIN" ] && grep -Eq '^[[:space:]]*autologin-' "$f" && \
		echo "  HINWEIS: $f setzt auch autologin - die Datei $LDM_DROPIN kommt danach und gilt."
done

# --- 5. Schlaf aus
schritt "5. Bildschirmschoner, Sperre und Energiesparen aus"
echo "  In der Kiosk-Sitzung: kein Bildschirmschoner, keine Sperre (Cinnamon läuft dort nicht), xset s off / -dpms."
for u in $SCHLAF; do
	einheit_da "$u" || continue
	if [ "$(systemctl is-enabled "$u" 2>/dev/null)" = masked ]; then echo "  $u: schon aus"; else tu systemctl mask "$u"; fi
done

# --- 6. Dienste
schritt "6. Unnötige Dienste deaktivieren (nicht entfernen)"
for u in $DIENSTE; do
	einheit_da "$u" || { echo "  $u: nicht vorhanden"; continue; }
	case "$(systemctl is-enabled "$u" 2>/dev/null)" in
		enabled|enabled-runtime) tu systemctl disable --now "$u" ;;
		*) echo "  $u: schon aus"; systemctl is-active -q "$u" 2>/dev/null && tu systemctl stop "$u" ;;
	esac
done
echo "  Autostarts (Liste in $SICH/autostarts.txt): laufen in der Kiosk-Sitzung nicht, im normalen Mint unverändert."

# --- 7. SSH und Firewall
schritt "7. SSH und Firewall"
if einheit_da ssh.socket && [ "$(systemctl is-enabled ssh.socket 2>/dev/null)" != masked ] && ! systemctl is-active -q ssh.service 2>/dev/null; then
	tu systemctl enable --now ssh.socket
elif einheit_da ssh.service || [ $TROCKEN -eq 1 ]; then
	tu systemctl enable --now ssh.service
else
	echo "  SSH-Dienst fehlt (Paket openssh-server?)"; FEHLER=$((FEHLER + 1))
fi
REGELN=$( (LC_ALL=C $LESE ufw show added 2>/dev/null) || true)
regel() {   # regel BESCHREIBUNG ufw-argumente…  (merkt sich, was der Kiosk neu dazugetan hat)
	local name="$1"; shift
	if printf '%s\n' "$REGELN" | grep -Fq -- "ufw $*"; then
		echo "  Regel schon da: ufw $*"
	else
		tu ufw "$@" comment "MoveEye Kiosk $name" && [ $TROCKEN -eq 0 ] && \
			{ grep -Fxq -- "$*" "$KD/ufw_von_kiosk.txt" 2>/dev/null || echo "$*" | als_benutzer tee -a "$KD/ufw_von_kiosk.txt" > /dev/null; }
	fi
}
regel SSH allow 22/tcp
regel Simulator allow 8765/tcp
regel Suche allow out 8764/udp
if LC_ALL=C $LESE ufw status 2>/dev/null | grep -q "Status: active"; then
	echo "  Firewall: schon aktiv (bestehende Regeln bleiben)"
else
	tu ufw default deny incoming
	tu ufw default allow outgoing
	tu ufw --force enable
fi

schritt "Fertig"
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ $TROCKEN -eq 1 ]; then
	echo "Trockenlauf - nichts geändert. Ohne --trocken starten, um den Kiosk einzurichten."
else
	[ "$FEHLER" -gt 0 ] && echo "ACHTUNG: $FEHLER Schritt(e) mit Fehler - siehe oben bzw. $LOG"
	echo "Kiosk eingerichtet. Neu starten (sudo reboot): danach startet der Simulator von selbst im Vollbild."
fi
echo "SSH von einem anderen PC: ssh $BENUTZER@${IP:-<IP>}"
echo "Ctrl+Alt+D = normales Mint, Abmelden = zurück in den Kiosk. Alles zurück: ./kiosk_aus.sh"
[ "$FEHLER" -eq 0 ]
