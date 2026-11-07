#!/bin/bash
# MoveEye Kiosk - PS5-Controller (DualSense) per Bluetooth koppeln, ohne Tippen (Knopf «Controller koppeln» im Testbild,
# Ctrl+Alt+B im Kiosk). Läuft als root, aber nur über den Dienst moveeye-controller-koppeln.service (moveeye-hp-update
# richtet ihn ein) oder von Hand: sudo /usr/local/lib/moveeye-kiosk/controller_koppeln.sh
# Sicherheit: der Benutzer des Kiosks bekommt KEIN root. Er legt nur die leere Wunsch-Datei WUNSCH an (sein Ordner
# /run/moveeye-spiel); die Pfad-Einheit moveeye-controller-koppeln.path startet dann diesen Dienst. Das Skript nimmt keine
# Angaben vom Benutzer an (keine Optionen, der Inhalt der Wunsch-Datei wird nie gelesen), tut immer dasselbe und höchstens
# SUCH_S lang: Bluetooth an, «pairable» an, suchen, nur einen Sony-DualSense (Modalias v054C p0CE6 / p0DF2; ohne Modalias
# nur der genaue Name) koppeln, vertrauen, verbinden, «pairable» wieder aus. Der Rechner selbst wird nicht sichtbar
# (discoverable bleibt aus): der Controller im Kopplungs-Modus ist sichtbar, der HP sucht ihn.
# Fortschritt für den Bildschirm: STATUS (JSON {"schritt", "text", "ok", "rest_s", "t"}, nur feste Texte, keine Adressen).
# Schritte: start, suche, koppeln, fertig (ok), kein_adapter, nicht_gefunden, fehler.
# shellcheck disable=SC2317  # aufraeumen läuft über trap EXIT
set -u
# nur zum Prüfen änderbar (controller_test.sh; systemd startet ohne diese Variablen)
BTCTL="${MW_BTCTL:-bluetoothctl}"
SYS="${MW_BT_SYS:-/sys/class/bluetooth}"
STATUS_DIR="${MW_BT_STATUS_DIR:-/run/moveeye-controller}"
WUNSCH="${MW_BT_WUNSCH:-/run/moveeye-spiel/controller_koppeln}"
SUCH_S="${MW_BT_SUCH_S:-60}"
TAKT="${MW_BT_TAKT:-2}"
NAMEN_RE='^(DualSense Wireless Controller|DualSense Edge Wireless Controller)$'
MODALIAS_RE='^usb:v054Cp(0CE6|0DF2)'
MAC_RE='^([0-9A-F]{2}:){5}[0-9A-F]{2}$'
SCAN=0

log() { printf '%s controller: %s\n' "$(date '+%F %T')" "$*"; }

status() {   # status SCHRITT OK(true|false|null) REST_S TEXT - nur feste Texte aus diesem Skript
	local tmp="$STATUS_DIR/.status.neu"
	mkdir -p "$STATUS_DIR" 2>/dev/null && chmod 755 "$STATUS_DIR" 2>/dev/null
	printf '{"schritt": "%s", "ok": %s, "rest_s": %d, "t": %d, "text": "%s"}\n' "$1" "$2" "$3" "$(date +%s)" "$4" > "$tmp" \
		&& chmod 644 "$tmp" && mv -f "$tmp" "$STATUS_DIR/status.json"
	[ "$1" = suche ] || log "$1: $4"
}

bt() { timeout 20 "$BTCTL" "$@" 2>/dev/null | sed 's/\x1b\[[0-9;]*[A-Za-z]//g; s/\r//g'; }   # ohne Farben
info_hat() { bt info "$1" | grep -qiE "^[[:space:]]*$2"; }

aufraeumen() {   # (über trap EXIT)
	[ "$SCAN" -gt 0 ] && kill "$SCAN" 2>/dev/null
	SCAN=0
	bt scan off >/dev/null
	bt pairable off >/dev/null
}

geraete() {   # Adressen aller bekannten Geräte (nur gültige Adressen, Namen werden nie ausgeführt)
	bt devices | sed -n 's/^Device \([0-9A-Fa-f:]\{17\}\) .*/\1/p' | tr 'a-f' 'A-F' | grep -E "$MAC_RE" | sort -u
}

dualsense() {   # dualsense MAC: ist das ein Sony DualSense? (Modalias, ohne Modalias nur der genaue Name)
	local i m n
	i="$(bt info "$1")"
	m="$(printf '%s\n' "$i" | sed -n 's/^[[:space:]]*Modalias:[[:space:]]*\([^ ]*\).*/\1/p' | head -n 1)"
	if [ -n "$m" ]; then
		printf '%s' "$m" | grep -qiE "$MODALIAS_RE"
		return
	fi
	n="$(printf '%s\n' "$i" | sed -n 's/^[[:space:]]*Name:[[:space:]]*//p' | head -n 1)"
	printf '%s' "$n" | grep -qE "$NAMEN_RE"
}

verbundene() {   # Zahl der verbundenen DualSense
	local mac n=0
	for mac in $(geraete); do
		dualsense "$mac" && info_hat "$mac" 'Connected: yes' && n=$((n + 1))
	done
	echo "$n"
}

# ---------------------------------------------------------------- los
# der Wunsch ist angenommen: Datei weg (sonst startet die Pfad-Einheit gleich noch einmal); nie lesen, nie folgen
rm -f -- "$WUNSCH" 2>/dev/null; [ -d "$WUNSCH" ] && rmdir -- "$WUNSCH" 2>/dev/null
status start null "$SUCH_S" "Bluetooth wird vorbereitet …"
if ! compgen -G "$SYS/hci*" >/dev/null; then
	status kein_adapter false 0 "Kein Bluetooth – USB-Stick nötig oder Controller per USB-C-Kabel"
	exit 0
fi
if ! command -v "$BTCTL" >/dev/null 2>&1; then
	status fehler false 0 "Bluetooth-Programme fehlen (bluez) – das HP-Update installiert sie, später noch einmal"
	exit 0
fi
command -v rfkill >/dev/null 2>&1 && rfkill unblock bluetooth 2>/dev/null
if command -v systemctl >/dev/null 2>&1 && ! systemctl is-active -q bluetooth.service 2>/dev/null; then
	systemctl start bluetooth.service 2>/dev/null || log "bluetooth.service startet nicht"
fi
bereit=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
	if bt show | grep -q '^Controller '; then bereit=1; break; fi
	sleep 1
done
if [ $bereit -eq 0 ]; then
	status kein_adapter false 0 "Kein Bluetooth – USB-Stick nötig oder Controller per USB-C-Kabel"
	exit 0
fi
trap 'aufraeumen' EXIT
trap 'exit 1' TERM INT
bt power on >/dev/null
bt pairable on >/dev/null
schon="$(verbundene)"
# suchen: der Such-Auftrag gilt, solange dieser bluetoothctl läuft (BlueZ: pro Teilnehmer); gefundene Geräte sieht jeder
"$BTCTL" --timeout "$SUCH_S" scan on >/dev/null 2>&1 &
SCAN=$!
ende=$(( $(date +%s) + SUCH_S ))
ziel=""
while [ "$(date +%s)" -lt "$ende" ]; do
	status suche null $(( ende - $(date +%s) )) "Suche Controller … PS-Taste und Create-Taste halten, bis das Licht schnell blinkt"
	for mac in $(geraete); do
		info_hat "$mac" 'Connected: yes' && continue           # schon verbunden: nicht im Kopplungs-Modus
		if dualsense "$mac"; then ziel="$mac"; break; fi
	done
	[ -n "$ziel" ] && break
	sleep "$TAKT"
done
kill "$SCAN" 2>/dev/null; wait "$SCAN" 2>/dev/null; SCAN=0
bt scan off >/dev/null
if [ -z "$ziel" ]; then
	if [ "${schon:-0}" -gt 0 ]; then
		status fertig true 0 "Kein neuer Controller gefunden – schon verbunden: $schon"
	else
		status nicht_gefunden false 0 "Kein Controller gefunden – PS + Create halten, bis das Licht schnell blinkt, dann noch einmal"
	fi
	exit 0
fi
status koppeln null 0 "Controller gefunden – wird gekoppelt …"
# war er schon gekoppelt und ist wieder im Kopplungs-Modus, kennt er den alten Schlüssel nicht mehr: neu koppeln
if info_hat "$ziel" 'Paired: yes'; then
	bt remove "$ziel" >/dev/null                          # BlueZ vergisst das Gerät ganz: kurz neu suchen, bis es wieder da ist
	"$BTCTL" --timeout 20 scan on >/dev/null 2>&1 &
	SCAN=$!
	for _ in $(seq 1 20); do
		bt info "$ziel" | grep -q 'Name:' && break
		sleep 1
	done
	kill "$SCAN" 2>/dev/null; wait "$SCAN" 2>/dev/null; SCAN=0
	bt scan off >/dev/null
fi
gekoppelt=0
for _ in 1 2; do
	timeout 40 "$BTCTL" --agent NoInputNoOutput --timeout 30 pair "$ziel" >/dev/null 2>&1
	if info_hat "$ziel" 'Paired: yes'; then gekoppelt=1; break; fi
	sleep 2
done
if [ $gekoppelt -eq 0 ]; then
	status fehler false 0 "Koppeln hat nicht geklappt – PS + Create noch einmal halten und neu versuchen"
	exit 0
fi
bt trust "$ziel" >/dev/null
verbunden=0
for _ in 1 2 3 4 5; do
	info_hat "$ziel" 'Connected: yes' && { verbunden=1; break; }
	bt connect "$ziel" >/dev/null
	info_hat "$ziel" 'Connected: yes' && { verbunden=1; break; }
	sleep 2
done
if [ $verbunden -eq 1 ]; then
	status fertig true 0 "Controller verbunden ✓ – beim nächsten Mal genügt die PS-Taste"
else
	status fehler false 0 "Gekoppelt, aber nicht verbunden – PS-Taste drücken"
fi
exit 0
