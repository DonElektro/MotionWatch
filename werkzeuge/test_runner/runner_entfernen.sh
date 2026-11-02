#!/bin/bash
# MoveEye Test-Runner ENTFERNEN - nimmt zurück, was runner_einrichten.sh eingerichtet hat.
#   sudo bash /usr/local/lib/moveeye-runner/runner_entfernen.sh        fragt einmal «Fortfahren? (j/n)»
#   sudo bash runner_entfernen.sh --ja                                 ohne Rückfragen (Benutzer und Ordner werden gelöscht)
# Abmelden bei GitHub: mit Entfernen-Token (GitHub → Settings → Actions → Runners → moveeye-hp → «Remove»); ohne Token
# nur hier entfernen und den Runner auf GitHub von Hand löschen. Pakete (Python, Xvfb …) bleiben installiert.
# Der Kiosk läuft danach wie vorher (kiosk_sitzung.sh bleibt, ohne Pause-Einstellung tut die Pause-Funktion nichts).
set -u
RU="mwrunner"
RH="/var/lib/mwrunner"
RD="$RH/runner"
LIB="/usr/local/lib/moveeye-runner"
CONF="/etc/moveeye-runner.conf"
PAUSE_DIR="/run/moveeye-test"
TMPFILES="/etc/tmpfiles.d/moveeye-test.conf"
KIOSK_TEST="/etc/moveeye-kiosk-test.conf"
JA=0
for a in "$@"; do
	case "$a" in
		--ja|-y) JA=1 ;;
		-h|--hilfe|--help) sed -n '2,7p' "$0"; exit 0 ;;
		*) echo "Unbekannte Option: $a (--ja, --hilfe)"; exit 2 ;;
	esac
done
if [ "$(id -u)" -ne 0 ]; then echo "Bitte mit sudo starten: sudo bash $0"; exit 1; fi

cat <<EOF
=== MoveEye Test-Runner ENTFERNEN ===
Das passiert:
 1. Dienst des Runners anhalten und entfernen
 2. Runner bei GitHub abmelden (mit Entfernen-Token, sonst auf GitHub von Hand löschen)
 3. Haken, Pause-Einstellung des Kiosks und $CONF entfernen
 4. Benutzer «$RU» und $RH (Runner, Python-Umgebung, Zwischenspeicher) löschen
Pakete bleiben installiert. Der Kiosk läuft wie vorher.
EOF
if [ $JA -eq 0 ]; then
	read -r -p "Fortfahren? (j/n) " antwort
	case "$antwort" in j|J|ja|Ja|JA|y|Y) ;; *) echo "Abgebrochen - nichts geändert."; exit 0 ;; esac
fi
FEHLER=0
schritt() { echo; echo "--- $*"; }
weg() { if [ -e "$1" ]; then rm -f -- "$1" && echo "  entfernt: $1"; else echo "  $1: schon weg"; fi; }

schritt "1. Dienst"
UNIT="$(cat "$RD/.service" 2>/dev/null)"
if [ -n "$UNIT" ] && [ -x "$RD/svc.sh" ]; then
	(cd "$RD" && ./svc.sh stop; ./svc.sh uninstall) || { echo "  (svc.sh meldet Fehler)"; FEHLER=$((FEHLER + 1)); }
	rm -f -- "/etc/systemd/system/$UNIT.d/moveeye.conf"
	rmdir --ignore-fail-on-non-empty -- "/etc/systemd/system/$UNIT.d" 2>/dev/null
	systemctl daemon-reload
else
	echo "  kein Dienst eingerichtet"
fi

schritt "2. Bei GitHub abmelden"
if [ -f "$RD/.runner" ]; then
	TOKEN=""
	if [ $JA -eq 0 ]; then
		echo "  Entfernen-Token: GitHub → Settings → Actions → Runners → moveeye-hp → «Remove» (leer lassen = nur hier entfernen)"
		read -r -s -p "  Token: " TOKEN < /dev/tty; echo
		TOKEN="$(printf '%s' "$TOKEN" | tr -d '[:space:]')"
	fi
	if [ -n "$TOKEN" ]; then
		if printf '%s\n' "$TOKEN" | sudo -u "$RU" -H -- bash -c 'cd "$1" || exit 1; IFS= read -r t; export ACTIONS_RUNNER_INPUT_TOKEN="$t"; unset t
			exec ./config.sh remove --unattended' _ "$RD"; then
			echo "  bei GitHub abgemeldet"
		else
			echo "  Abmelden ging nicht - auf GitHub unter Settings → Actions → Runners von Hand löschen"; FEHLER=$((FEHLER + 1))
		fi
	else
		echo "  ohne Token: den Runner auf GitHub unter Settings → Actions → Runners von Hand löschen (er steht dort als «Offline»)"
	fi
	TOKEN=""; unset TOKEN
else
	echo "  nicht angemeldet"
fi

schritt "3. Haken und Einstellungen"
rm -f -- "$PAUSE_DIR/kiosk_pause"
rmdir -- "$PAUSE_DIR" 2>/dev/null
weg "$TMPFILES"
weg "$KIOSK_TEST"
weg "$CONF"
weg "$LIB/job_start.sh"
weg "$LIB/job_ende.sh"
weg "$LIB/kiosk_sitzung.sh.vorher"
weg "$LIB/runner_entfernen.sh"
rmdir --ignore-fail-on-non-empty -- "$LIB" 2>/dev/null

schritt "4. Benutzer und Ordner"
loeschen=1
if [ $JA -eq 0 ]; then
	read -r -p "  Benutzer «$RU» und $RH (mit Zwischenspeicher: KI-Modell, Godot) löschen? (j/n) " antwort
	case "$antwort" in j|J|ja|Ja|JA|y|Y) ;; *) loeschen=0 ;; esac
fi
if [ $loeschen -eq 1 ] && id "$RU" >/dev/null 2>&1; then
	pkill -TERM -u "$RU" 2>/dev/null; sleep 2; pkill -KILL -u "$RU" 2>/dev/null
	if userdel "$RU"; then echo "  Benutzer $RU gelöscht"; else echo "  (userdel meldet Fehler)"; FEHLER=$((FEHLER + 1)); fi
	case "$RH" in /var/lib/mwrunner) [ -d "$RH" ] && rm -rf -- "$RH" && echo "  $RH gelöscht" ;; esac
elif [ $loeschen -eq 0 ]; then
	echo "  bleibt: Benutzer $RU und $RH"
else
	echo "  Benutzer $RU gibt es nicht mehr"
fi

schritt "Fertig"
[ "$FEHLER" -gt 0 ] && echo "ACHTUNG: $FEHLER Schritt(e) mit Fehler - siehe oben."
echo "Test-Runner entfernt. Der Kiosk läuft wie vorher (kiosk_sitzung.sh bleibt; ohne $KIOSK_TEST pausiert er nie)."
[ "$FEHLER" -eq 0 ]
