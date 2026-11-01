#!/bin/bash
# MoveEye Kiosk AUS - stellt zurück, was ./kiosk_ein.sh eingerichtet hat (aus der Sicherung in ~/.moveeye_kiosk/sicherung).
#   ./kiosk_aus.sh             zeigt, was es tut, fragt einmal «Fortfahren? (j/n)», dann mit sudo
#   ./kiosk_aus.sh --trocken   zeigt nur, was passieren würde (ändert nichts, braucht kein sudo)
#   ./kiosk_aus.sh --ja        ohne Rückfrage
# SSH bleibt eingeschaltet (und in der Firewall offen). Pakete (openbox, openssh-server, ufw) bleiben installiert.
# Mehrmals ausführen ist kein Problem. Protokoll: ~/.moveeye_kiosk/
set -u
LIB="/usr/local/lib/moveeye-kiosk"
CONF="/etc/moveeye-kiosk.conf"
XSESSION="/usr/share/xsessions/moveeye-kiosk.desktop"
LDM_DROPIN="/etc/lightdm/lightdm.conf.d/99-moveeye-kiosk.conf"
LDM_CONF="/etc/lightdm/lightdm.conf"
MARKE="#moveeye-kiosk# "

TROCKEN=0 JA=0
for a in "$@"; do
	case "$a" in
		--trocken|-n) TROCKEN=1 ;;
		--ja|-y) JA=1 ;;
		-h|--hilfe|--help) sed -n '2,7p' "$0"; exit 0 ;;
		*) echo "Unbekannte Option: $a (--trocken, --ja, --hilfe)"; exit 2 ;;
	esac
done

if [ "$(id -u)" -eq 0 ]; then
	BENUTZER="${SUDO_USER:-}"
	if [ -z "$BENUTZER" ] || [ "$BENUTZER" = root ]; then echo "Bitte als normaler Benutzer starten (ohne sudo): ./kiosk_aus.sh"; exit 1; fi
	SUDO=""
else
	BENUTZER="$(id -un)"
	SUDO="sudo"
fi
LESE="$SUDO"
[ $TROCKEN -eq 1 ] && [ -n "$SUDO" ] && LESE="sudo -n"
HEIM="$(getent passwd "$BENUTZER" | cut -d: -f6)"
[ -n "$HEIM" ] || HEIM="$HOME"
KD="$HEIM/.moveeye_kiosk"
SICH="$KD/sicherung"
STAMP="$(date +%Y%m%d_%H%M%S)"

als_benutzer() { if [ "$(id -u)" -eq 0 ]; then sudo -u "$BENUTZER" "$@"; else "$@"; fi; }
als_benutzer mkdir -p "$KD"
if [ $TROCKEN -eq 1 ]; then LOG="$KD/kiosk_aus_${STAMP}_trocken.log"; else LOG="$KD/kiosk_aus_${STAMP}.log"; fi
als_benutzer touch "$LOG"
exec > >(tee -a "$LOG") 2>&1

cat <<EOF
=== MoveEye Kiosk AUS ===$( [ $TROCKEN -eq 1 ] && echo "   (TROCKENLAUF: nichts wird geändert)" )
Benutzer: $BENUTZER    Sicherung: $SICH
Das passiert:
 1. Automatisches Anmelden wie vorher (Kiosk-Eintrag weg, eigene autologin-Zeilen in lightdm.conf wieder aktiv)
 2. Sitzung «MoveEye Kiosk» abmelden (nur die Dateien, die kiosk_ein.sh angelegt hat)
 3. Dienste und Suspend wie vorher (aus der Sicherung)
 4. Firewall: Simulator-Regeln weg, Zustand wie vorher; SSH (22) bleibt offen
 5. Autostarts: waren nie verändert (liefen nur in der Kiosk-Sitzung nicht)
SSH bleibt eingeschaltet. Pakete bleiben installiert. Eigene Dateien werden nicht verändert. Protokoll: $LOG
EOF
[ -d "$SICH" ] || echo "HINWEIS: keine Sicherung in $SICH - Dienste und Suspend bleiben, wie sie jetzt sind."

if [ $JA -eq 0 ]; then
	read -r -p "Fortfahren? (j/n) " antwort
	case "$antwort" in j|J|ja|Ja|JA|y|Y) ;; *) echo "Abgebrochen - nichts geändert."; exit 0 ;; esac
fi

FEHLER=0
schritt() { echo; echo "--- $*"; }
tu() {
	if [ $TROCKEN -eq 1 ]; then echo "[trocken] $SUDO $*"; return 0; fi
	echo "+ $*"
	$SUDO "$@" || { echo "  (Fehler: $*)"; FEHLER=$((FEHLER + 1)); return 1; }
}
weg() {   # eine Datei, die kiosk_ein.sh angelegt hat, wieder wegnehmen (genau dieser Pfad, keine Muster)
	if [ -e "$1" ]; then tu rm -f -- "$1"; else echo "  $1: schon weg"; fi
}
zustand() { [ -r "$SICH/$1" ] && cat "$SICH/$1"; }
einheit_da() { [ -n "$(systemctl list-unit-files --no-legend "$1" 2>/dev/null)" ]; }

if [ $TROCKEN -eq 0 ] && [ -n "$SUDO" ]; then
	echo "sudo fragt jetzt nach dem Passwort von $BENUTZER:"
	sudo -v || { echo "Ohne sudo geht es nicht - abgebrochen."; exit 1; }
fi

schritt "1. Automatisches Anmelden"
weg "$LDM_DROPIN"
if [ -r "$LDM_CONF" ] && grep -q "^$MARKE" "$LDM_CONF"; then
	tu sed -i "s/^$MARKE//" "$LDM_CONF"
else
	echo "  $LDM_CONF: nichts auskommentiert"
fi

schritt "2. Sitzung «MoveEye Kiosk»"
weg "$XSESSION"
weg "$CONF"
weg "$LIB/openbox.xml"
weg "$LIB/kiosk_sitzung.sh"
if [ -d "$LIB" ]; then tu rmdir --ignore-fail-on-non-empty -- "$LIB"; fi

schritt "3. Dienste und Suspend"
if zustand schlaf_vorher.txt > /dev/null; then
	while read -r u vorher; do
		[ -n "$u" ] || continue
		if [ "$vorher" = masked ]; then echo "  $u: war schon vorher aus - bleibt"
		elif [ "$(systemctl is-enabled "$u" 2>/dev/null)" = masked ]; then tu systemctl unmask "$u"
		else echo "  $u: schon wie vorher"; fi
	done < <(zustand schlaf_vorher.txt)
else
	echo "  keine Sicherung: Suspend bleibt, wie er jetzt ist (einschalten: sudo systemctl unmask sleep.target suspend.target)"
fi
if zustand dienste_vorher.txt > /dev/null; then
	while read -r u vorher; do
		[ -n "$u" ] || continue
		einheit_da "$u" || { echo "  $u: nicht mehr vorhanden"; continue; }
		case "$vorher" in
			enabled|enabled-runtime)
				if [ "$(systemctl is-enabled "$u" 2>/dev/null)" = enabled ]; then echo "  $u: schon ein"
				else tu systemctl enable --now "$u"; fi ;;
			*) echo "  $u: war vorher «$vorher» - bleibt" ;;
		esac
	done < <(zustand dienste_vorher.txt)
fi

schritt "4. Firewall"
if [ -r "$KD/ufw_von_kiosk.txt" ]; then
	while read -r r; do
		[ -n "$r" ] || continue
		case "$r" in
			"allow 22/tcp") echo "  SSH-Regel (22/tcp) bleibt" ;;
			*) # shellcheck disable=SC2086
			   tu ufw delete $r ;;
		esac
	done < "$KD/ufw_von_kiosk.txt"
	[ $TROCKEN -eq 1 ] || { grep -Fx "allow 22/tcp" "$KD/ufw_von_kiosk.txt" > "$KD/ufw_von_kiosk.neu"; mv -f "$KD/ufw_von_kiosk.neu" "$KD/ufw_von_kiosk.txt"; }
else
	echo "  keine Simulator-Regeln vom Kiosk vermerkt"
fi
if zustand ufw_vorher.txt > /dev/null; then
	while read -r k v; do
		case "$k" in
			DEFAULT_INPUT_POLICY) case "$v" in ACCEPT) tu ufw default allow incoming ;; DROP) tu ufw default deny incoming ;; REJECT) tu ufw default reject incoming ;; esac ;;
			DEFAULT_OUTPUT_POLICY) case "$v" in ACCEPT) tu ufw default allow outgoing ;; DROP) tu ufw default deny outgoing ;; REJECT) tu ufw default reject outgoing ;; esac ;;
		esac
	done < <(zustand ufw_vorher.txt)
	if [ "$(sed -n 's/^aktiv //p' "$SICH/ufw_vorher.txt")" = inactive ]; then
		if LC_ALL=C $LESE ufw status 2>/dev/null | grep -q "Status: active"; then tu ufw disable; else echo "  Firewall: schon aus (wie vorher)"; fi
	else
		echo "  Firewall: bleibt an (war schon vorher an)"
	fi
fi

schritt "5. Autostarts"
echo "  Unverändert (Liste: $SICH/autostarts.txt) - sie laufen im normalen Mint wie immer."

schritt "Sicherung"
if [ -d "$SICH" ]; then
	if [ $TROCKEN -eq 1 ]; then echo "[trocken] würde umbenennen: $SICH -> $SICH.zurueck_$STAMP"
	else als_benutzer mv -- "$SICH" "$SICH.zurueck_$STAMP" && echo "  aufbewahrt als $SICH.zurueck_$STAMP"; fi
fi

schritt "Fertig"
echo "HINWEIS: SSH bleibt eingeschaltet (Port 22 offen). Ausschalten: sudo systemctl disable --now ssh.socket ssh.service"
echo "Pakete openbox, openssh-server, ufw bleiben installiert (nichts wird deinstalliert)."
if [ $TROCKEN -eq 1 ]; then echo "Trockenlauf - nichts geändert."
else
	[ "$FEHLER" -gt 0 ] && echo "ACHTUNG: $FEHLER Schritt(e) mit Fehler - siehe oben bzw. $LOG"
	echo "Zurückgestellt. Neu starten (sudo reboot): danach wieder das normale Mint wie vorher."
fi
[ "$FEHLER" -eq 0 ]
