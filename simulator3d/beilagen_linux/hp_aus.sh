#!/bin/bash
# MoveEye Kiosk - Simulator-PC ausschalten (HP_FASSUNG 8, Besitzer 12.11.2026). Läuft als root, aber nur über den Dienst
# moveeye-aus.service: die Pfad-Einheit moveeye-aus.path startet ihn, sobald der Benutzer des Kiosks eine leere Wunsch-Datei
# in seinem Ordner /run/moveeye-spiel anlegt (Knopf «Ausschalten» im Simulator -> hp_knoepfe.sh aus …):
#   aus_herunterfahren   systemctl poweroff
#   aus_neustart         systemctl reboot
#   aus_bios             systemctl reboot --firmware-setup   (nur, wenn der PC das kann; sonst passiert nichts)
# Es zählt nur der NAME der Datei, der Inhalt wird nie gelesen; alles andere wird ohne Wirkung weggeräumt. Das Skript nimmt
# keine Angaben an und führt nur diese drei festen Befehle aus. Kein sudo, keine polkit-Regel, kein Passwort.
# Warum so und nicht über logind direkt: herunterfahren und neu starten dürfte die Sitzung am Bildschirm auch selbst
# (polkit: allow_active), «ins BIOS» aber nur mit Administrator-Passwort - und ob polkit am HP so eingestellt ist, lässt sich
# von aussen nicht prüfen. Der Weg über die Wunsch-Datei ist am HP schon erprobt (Controller koppeln), gibt dem Benutzer des
# Kiosks nichts, was er nicht ohnehin kann (er sitzt am Einschaltknopf), und schreibt mit, ob gerade ein Test lief.
# Schutz vor Schleifen: /run ist nach jedem Start leer; die Wunsch-Datei wird zuerst gelöscht; älter als ALT_S zählt sie nicht.
# Läuft ein Test (Job des Runners), beendet das Herunterfahren ihn wie jeden Dienst (SIGTERM): der Job gilt auf GitHub als
# abgebrochen, das Dauerrechnen hat seinen Stand nach jedem ganzen Fall gesichert und rechnet beim nächsten Lauf dort weiter.
set -u
# nur zum Prüfen änderbar (hp_knoepfe_test.sh; systemd startet ohne diese Variablen)
WUNSCH_DIR="${MW_AUS_DIR:-/run/moveeye-spiel}"
STATUS_DIR="${MW_AUS_STATUS_DIR:-/run/moveeye-aus}"
SYSTEMCTL="${MW_AUS_SYSTEMCTL:-systemctl}"
EFI="${MW_AUS_EFI:-/sys/firmware/efi}"
RUNNER="${MW_AUS_RUNNER:-mwrunner}"
PAUSE="${MW_AUS_PAUSE:-/run/moveeye-test/kiosk_pause}"
ALT_S=120

log() { printf '%s aus: %s\n' "$(date '+%F %T')" "$*"; }
status() {   # status SCHRITT - nur feste Wörter
	mkdir -p "$STATUS_DIR" 2>/dev/null && chmod 755 "$STATUS_DIR" 2>/dev/null
	printf '{"schritt": "%s", "t": %d}\n' "$1" "$(date +%s)" > "$STATUS_DIR/.status.neu" 2>/dev/null \
		&& chmod 644 "$STATUS_DIR/.status.neu" && mv -f "$STATUS_DIR/.status.neu" "$STATUS_DIR/status.json"
}
bios_geht() {
	[ -d "$EFI" ] || return 1
	command -v busctl >/dev/null 2>&1 || return 1
	timeout 5 busctl call org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager CanRebootToFirmwareSetup 2>/dev/null \
		| grep -q '"yes"'
}
test_laeuft() {
	[ -f "$PAUSE" ] && return 0
	id "$RUNNER" >/dev/null 2>&1 && pgrep -u "$RUNNER" -f 'Runner\.Worker' >/dev/null 2>&1
}

WAS=""
for f in "$WUNSCH_DIR"/aus_*; do          # alle Wünsche annehmen und wegräumen; nie lesen, nie folgen
	[ -e "$f" ] || [ -L "$f" ] || continue
	n="${f##*/}"
	alt=$(( $(date +%s) - $(stat -c %Y -- "$f" 2>/dev/null || echo 0) ))
	normal=0; [ -f "$f" ] && [ ! -L "$f" ] && normal=1
	rm -rf -- "$f" 2>/dev/null
	[ $normal -eq 1 ] || { log "Wunsch ist keine normale Datei - ohne Wirkung"; continue; }
	[ "$alt" -le "$ALT_S" ] || { log "alter Wunsch ($alt s) - ohne Wirkung"; continue; }
	case "$n" in
		aus_herunterfahren) WAS="herunterfahren" ;;                        # geht vor
		aus_bios) [ "$WAS" = herunterfahren ] || WAS="bios" ;;
		aus_neustart) [ -n "$WAS" ] || WAS="neustart" ;;
		*) log "unbekannter Wunsch - ohne Wirkung" ;;
	esac
done
[ -n "$WAS" ] || { sleep 1; exit 0; }
test_laeuft && log "Achtung: es läuft ein Test - er wird abgebrochen (das Dauerrechnen macht beim nächsten Lauf beim letzten ganzen Fall weiter)"
case "$WAS" in
	herunterfahren)
		log "Herunterfahren (Knopf im Simulator)"; status herunterfahren
		"$SYSTEMCTL" poweroff ;;
	neustart)
		log "Neu starten (Knopf im Simulator)"; status neustart
		"$SYSTEMCTL" reboot ;;
	bios)
		if bios_geht; then
			log "Neu starten ins BIOS (Knopf im Simulator)"; status bios
			"$SYSTEMCTL" reboot --firmware-setup
		else
			log "Neu starten ins BIOS geht an diesem PC nicht (kein UEFI-Start oder die Firmware kann es nicht) - nichts getan"
			status bios_geht_nicht
		fi ;;
esac
sleep 1                                   # Bremse: der Dienst lässt sich nicht im Kreis jagen
exit 0
