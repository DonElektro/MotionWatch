#!/bin/bash
# MoveEye Kiosk - Controller (PS5 DualSense, auch DualShock 4 und Xbox-Controller) per Bluetooth koppeln und verwalten, ohne
# Tippen (Knopf «Controller koppeln» im Testbild, Knopf in der Ecke des Kiosks, Ctrl+Alt+B). Läuft als root, aber nur über
# den Dienst moveeye-controller-koppeln.service (moveeye-hp-update richtet ihn ein) oder von Hand:
#   sudo /usr/local/lib/moveeye-kiosk/controller_koppeln.sh
# Sicherheit: der Benutzer des Kiosks bekommt KEIN root. Er legt nur leere Wunsch-Dateien in seinem Ordner /run/moveeye-spiel
# an; die Pfad-Einheit moveeye-controller-koppeln.path startet dann diesen Dienst. Es zählt nur der NAME der Datei (festes
# Muster, sonst wird sie ohne Wirkung weggeräumt), der Inhalt wird nie gelesen:
#   controller_koppeln             SUCH_S lang suchen, den ersten Controller im Kopplungs-Modus koppeln, vertrauen, verbinden
#   controller_abbrechen           eine laufende Suche beenden
#   controller_liste               nur die Liste neu schreiben
#   controller_trennen.<Kürzel>    diesen gekoppelten Controller trennen (er schaltet sich aus)
#   controller_vergessen.<Kürzel>  diese Kopplung löschen
#   controller_ruhe                alle verbundenen Controller trennen (hp_wache.py: lange keine Eingabe - schont den Akku)
# <Kürzel> = 10 Hex-Zeichen aus liste.json (von diesem Skript vergeben, nie eine Adresse). Ohne Wunsch (Start durch udev,
# wenn ein Bluetooth-Adapter auftaucht - USB-Stick eingesteckt oder beim Hochfahren): Bluetooth einschalten, Liste schreiben;
# gekoppelte Controller verbinden sich dann mit der PS-Taste von selbst wieder.
# Gekoppelt wird nur ein Gamepad: Hersteller-Kennung (Modalias) von Sony DualSense / DualSense Edge / DualShock 4 oder eines
# Xbox-Controllers; ohne Modalias der genaue Name, und die Geräteklasse darf nichts anderes sagen (der Allerweltsname
# «Wireless Controller» und die Xbox-Namen gelten nur mit der Klasse / dem Symbol «Gamepad»). Nie Tastaturen, Kopfhörer, Handys.
# Der Rechner selbst wird nicht sichtbar (discoverable bleibt aus), «pairable» nur während der Suche.
# Für den Bildschirm (controller_fenster.py), nur feste Texte, keine Adressen, keine Namen aus dem Funk:
#   STATUS_DIR/status.json  {"schritt", "text", "ok", "rest_s", "t"}   Schritte: start, suche, koppeln, fertig (ok),
#                           kein_adapter, nicht_gefunden, abgebrochen, fehler
#   STATUS_DIR/liste.json   {"t", "adapter", "liste": [{"id", "art", "verbunden", "akku"}]}   (akku: Prozent oder null)
# shellcheck disable=SC2317  # aufraeumen läuft über trap EXIT
set -u
# nur zum Prüfen änderbar (controller_test.sh; systemd startet ohne diese Variablen)
BTCTL="${MW_BTCTL:-bluetoothctl}"
SYS="${MW_BT_SYS:-/sys/class/bluetooth}"
STROM="${MW_BT_STROM:-/sys/class/power_supply}"
STATUS_DIR="${MW_BT_STATUS_DIR:-/run/moveeye-controller}"
WUNSCH="${MW_BT_WUNSCH:-/run/moveeye-spiel/controller_koppeln}"
WUNSCH_DIR="$(dirname "$WUNSCH")"
SUCH_S="${MW_BT_SUCH_S:-60}"
TAKT="${MW_BT_TAKT:-2}"
BREMSE="${MW_BT_BREMSE:-1}"
MAC_RE='^([0-9A-F]{2}:){5}[0-9A-F]{2}$'
ID_RE='^[0-9a-f]{10}$'
KEIN_ADAPTER="Kein Bluetooth-Adapter gefunden – USB-Bluetooth-Stick einstecken oder Controller per USB-C-Kabel anschliessen"
HALTEN="PS-Taste und Create-Taste gedrückt halten, bis die Leiste schnell blau blinkt"
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
feld() { sed -n "s/^[[:space:]]*$1:[[:space:]]*//p" | head -n 1; }                            # feld NAME < «bluetoothctl info»
hat() { printf '%s\n' "$1" | grep -qiE "^[[:space:]]*$2"; }                                   # hat «info» 'Paired: yes'
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

klasse_gamepad() {   # klasse_gamepad 0x002508: Geräteklasse «Eingabegerät», Art Joystick oder Gamepad?
	local c
	[[ "$1" =~ ^0x[0-9A-Fa-f]{1,8}$ ]] || return 1
	c=$(( $1 ))
	[ $(( (c >> 8) & 31 )) -eq 5 ] || return 1
	case $(( (c >> 2) & 15 )) in 1|2) return 0 ;; esac
	return 1
}

pad_art() {   # pad_art «info»: ein Gamepad, das wir kennen? -> fester Name (nie der Name aus dem Funk)
	local i="$1" m n k s
	m="$(printf '%s\n' "$i" | feld Modalias | cut -d' ' -f1 | tr '[:lower:]' '[:upper:]')"
	n="$(printf '%s\n' "$i" | feld Name)"
	k="$(printf '%s\n' "$i" | feld Class | cut -d' ' -f1)"
	s="$(printf '%s\n' "$i" | feld Icon | cut -d' ' -f1)"
	if [ -n "$m" ]; then          # Hersteller-Kennung da: nur sie zählt
		m="${m#USB:}"; m="${m#BLUETOOTH:}"
		case "$m" in
			V054CP0CE6*) echo "DualSense" ;;
			V054CP0DF2*) echo "DualSense Edge" ;;
			V054CP05C4*|V054CP09CC*) echo "DualShock 4" ;;
			V045EP02E0*|V045EP02FD*|V045EP0B05*|V045EP0B12*|V045EP0B13*|V045EP0B20*|V045EP0B21*|V045EP0B22*) echo "Xbox-Controller" ;;
			*) return 1 ;;
		esac
		return 0
	fi
	if [ -n "$k" ] && ! klasse_gamepad "$k"; then return 1; fi          # die Klasse sagt etwas anderes (Kopfhörer, Tastatur …)
	case "$n" in
		"DualSense Wireless Controller") echo "DualSense"; return 0 ;;
		"DualSense Edge Wireless Controller") echo "DualSense Edge"; return 0 ;;
	esac
	# Allerweltsnamen: nur, wenn Klasse oder Symbol «Gamepad» sagen
	if { [ -n "$k" ] && klasse_gamepad "$k"; } || [ "$s" = input-gaming ]; then
		case "$n" in
			"Wireless Controller") echo "DualShock 4"; return 0 ;;
			"Xbox Wireless Controller"|"Xbox Elite Wireless Controller"|"Xbox Adaptive Controller") echo "Xbox-Controller"; return 0 ;;
		esac
	fi
	return 1
}

kennung() { printf 'moveeye|%s' "$1" | sha256sum | cut -c1-10; }   # Kürzel für die Liste (statt der Adresse)

akku() {   # akku MAC «info»: Prozent (BlueZ, sonst der Treiber: /sys/class/power_supply/…<adresse>/capacity) oder nichts
	local p d klein
	p="$(printf '%s\n' "$2" | sed -n 's/^[[:space:]]*Battery Percentage:.*(\([0-9]\{1,3\}\)).*/\1/p' | head -n 1)"
	if [ -z "$p" ]; then
		klein="$(printf '%s' "$1" | tr 'A-F' 'a-f')"
		for d in "$STROM"/*"$klein"* "$STROM"/*"$1"*; do
			[ -r "$d/capacity" ] || continue
			p="$(head -c 8 "$d/capacity" | tr -cd '0-9')"; break
		done
	fi
	[[ "$p" =~ ^[0-9]{1,3}$ ]] && [ "$p" -le 100 ] && printf '%s' "$p"
}

liste_schreiben() {   # liste_schreiben ADAPTER(true|false): gekoppelte Gamepads -> liste.json (höchstens 8)
	local tmp="$STATUS_DIR/.liste.neu" mac i art a v n=0 trenner=""
	mkdir -p "$STATUS_DIR" 2>/dev/null && chmod 755 "$STATUS_DIR" 2>/dev/null
	{
		printf '{"t": %d, "adapter": %s, "liste": [' "$(date +%s)" "$1"
		if [ "$1" = true ]; then
			for mac in $(geraete); do
				i="$(bt info "$mac")"
				hat "$i" 'Paired: yes' || continue
				art="$(pad_art "$i")" || continue
				a="$(akku "$mac" "$i")"
				if hat "$i" 'Connected: yes'; then v=true; else v=false; fi
				printf '%s{"id": "%s", "art": "%s", "verbunden": %s, "akku": %s}' "$trenner" "$(kennung "$mac")" "$art" "$v" "${a:-null}"
				trenner=", "
				n=$((n + 1)); [ $n -ge 8 ] && break
			done
		fi
		printf ']}\n'
	} > "$tmp" && chmod 644 "$tmp" && mv -f "$tmp" "$STATUS_DIR/liste.json"
}

# ---------------------------------------------------------------- Wünsche (nur Dateinamen)
W_KOPPELN=0 W_RUHE=0 W_TRENNEN="" W_VERGESSEN="" W_ZAHL=0
wuensche() {   # alle Wunsch-Dateien annehmen und wegräumen (sonst startet die Pfad-Einheit gleich noch einmal); nie lesen, nie folgen
	local f n id
	W_KOPPELN=0 W_RUHE=0 W_TRENNEN="" W_VERGESSEN="" W_ZAHL=0
	for f in "$WUNSCH_DIR"/controller_*; do
		[ -e "$f" ] || [ -L "$f" ] || continue
		n="${f##*/}"
		rm -rf -- "$f" 2>/dev/null
		W_ZAHL=$((W_ZAHL + 1))
		case "$n" in
			controller_koppeln) W_KOPPELN=1 ;;
			controller_ruhe) W_RUHE=1 ;;
			controller_trennen.*) id="${n#controller_trennen.}"; [[ "$id" =~ $ID_RE ]] && W_TRENNEN="$W_TRENNEN $id" ;;
			controller_vergessen.*) id="${n#controller_vergessen.}"; [[ "$id" =~ $ID_RE ]] && W_VERGESSEN="$W_VERGESSEN $id" ;;
			*) ;;                                           # controller_liste, controller_abbrechen, Unbekanntes: nur die Liste
		esac
	done
}
anderer_wunsch() {   # liegt während der Suche ein anderer Wunsch da (Abbrechen, Trennen, Vergessen)? -> die Suche endet
	local f
	for f in "$WUNSCH_DIR"/controller_*; do
		[ -e "$f" ] || [ -L "$f" ] || continue
		case "${f##*/}" in controller_koppeln|controller_liste) rm -rf -- "$f" 2>/dev/null ;; *) return 0 ;; esac
	done
	return 1
}

mac_zu() {   # mac_zu KÜRZEL -> Adresse eines bekannten Gamepads mit diesem Kürzel
	local mac
	for mac in $(geraete); do
		[ "$(kennung "$mac")" = "$1" ] || continue
		pad_art "$(bt info "$mac")" >/dev/null || return 1
		printf '%s' "$mac"; return 0
	done
	return 1
}

verwalten() {   # Vergessen, Trennen, Ruhe - nur Gamepads, die wir kennen
	local id mac
	for id in $W_VERGESSEN; do
		mac="$(mac_zu "$id")" || { log "vergessen: Kürzel unbekannt"; continue; }
		bt remove "$mac" >/dev/null; log "Controller vergessen (Kopplung gelöscht)"
	done
	for id in $W_TRENNEN; do
		mac="$(mac_zu "$id")" || { log "trennen: Kürzel unbekannt"; continue; }
		bt disconnect "$mac" >/dev/null; log "Controller getrennt"
	done
	if [ $W_RUHE -eq 1 ]; then
		for mac in $(geraete); do
			info_hat "$mac" 'Connected: yes' || continue
			pad_art "$(bt info "$mac")" >/dev/null || continue
			bt disconnect "$mac" >/dev/null; log "Controller getrennt (lange keine Eingabe - schont den Akku; die PS-Taste verbindet wieder)"
		done
	fi
}

verbundene() {   # Zahl der verbundenen Gamepads
	local mac i n=0
	for mac in $(geraete); do
		i="$(bt info "$mac")"
		hat "$i" 'Connected: yes' && pad_art "$i" >/dev/null && n=$((n + 1))
	done
	echo "$n"
}

koppeln() {   # SUCH_S lang suchen; den ersten Controller im Kopplungs-Modus koppeln, vertrauen, verbinden
	local schon ende ziel="" mac i gekoppelt=0 verbunden=0 abbruch=0
	bt pairable on >/dev/null
	schon="$(verbundene)"
	# suchen: der Such-Auftrag gilt, solange dieser bluetoothctl läuft (BlueZ: pro Teilnehmer); gefundene Geräte sieht jeder
	"$BTCTL" --timeout "$SUCH_S" scan on >/dev/null 2>&1 &
	SCAN=$!
	ende=$(( $(date +%s) + SUCH_S ))
	while [ "$(date +%s)" -lt "$ende" ]; do
		status suche null $(( ende - $(date +%s) )) "Suche Controller … $HALTEN"
		for mac in $(geraete); do
			i="$(bt info "$mac")"
			hat "$i" 'Connected: yes' && continue           # schon verbunden: nicht im Kopplungs-Modus
			# schon gekoppelt, aber in dieser Suche nicht zu sehen (ausgeschaltet): in Ruhe lassen, die Kopplung bleibt
			if hat "$i" 'Paired: yes' && ! hat "$i" 'RSSI:'; then continue; fi
			if pad_art "$i" >/dev/null; then ziel="$mac"; break; fi
		done
		[ -n "$ziel" ] && break
		if anderer_wunsch; then abbruch=1; break; fi
		sleep "$TAKT"
	done
	kill "$SCAN" 2>/dev/null; wait "$SCAN" 2>/dev/null; SCAN=0
	bt scan off >/dev/null
	if [ $abbruch -eq 1 ]; then
		bt pairable off >/dev/null
		status abgebrochen null 0 "Suche beendet"
		return 0
	fi
	if [ -z "$ziel" ]; then
		bt pairable off >/dev/null
		if [ "${schon:-0}" -gt 0 ]; then
			status fertig true 0 "Kein neuer Controller gefunden – schon verbunden: $schon"
		else
			status nicht_gefunden false 0 "Kein Controller gefunden"
		fi
		return 0
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
	for _ in 1 2; do
		timeout 40 "$BTCTL" --agent NoInputNoOutput --timeout 30 pair "$ziel" >/dev/null 2>&1
		if info_hat "$ziel" 'Paired: yes'; then gekoppelt=1; break; fi
		sleep 2
	done
	if [ $gekoppelt -eq 0 ]; then
		bt pairable off >/dev/null
		status fehler false 0 "Koppeln hat nicht geklappt – PS-Taste und Create-Taste noch einmal halten und neu versuchen"
		return 0
	fi
	bt trust "$ziel" >/dev/null                               # vertraut: verbindet sich später mit der PS-Taste von selbst
	for _ in 1 2 3 4 5; do
		info_hat "$ziel" 'Connected: yes' && { verbunden=1; break; }
		bt connect "$ziel" >/dev/null
		info_hat "$ziel" 'Connected: yes' && { verbunden=1; break; }
		sleep 2
	done
	bt pairable off >/dev/null
	if [ $verbunden -eq 1 ]; then
		status fertig true 0 "Verbunden ✔"
	else
		status fehler false 0 "Gekoppelt, aber nicht verbunden – PS-Taste drücken"
	fi
	return 0
}

# ---------------------------------------------------------------- los
wuensche
ANLASS=$W_ZAHL                                             # 0 = Start durch udev (Adapter aufgetaucht) oder von Hand
[ "$ANLASS" -eq 0 ] && [ -t 0 ] && W_KOPPELN=1             # von Hand am Terminal: koppeln
[ $W_KOPPELN -eq 1 ] && status start null "$SUCH_S" "Bluetooth wird vorbereitet …"
if ! compgen -G "$SYS/hci*" >/dev/null; then
	[ $W_KOPPELN -eq 1 ] && status kein_adapter false 0 "$KEIN_ADAPTER"
	liste_schreiben false
	exit 0
fi
if ! command -v "$BTCTL" >/dev/null 2>&1; then
	[ $W_KOPPELN -eq 1 ] && status fehler false 0 "Bluetooth-Programme fehlen (bluez) – das HP-Update installiert sie, später noch einmal"
	liste_schreiben false
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
	[ $W_KOPPELN -eq 1 ] && status kein_adapter false 0 "$KEIN_ADAPTER"
	liste_schreiben false
	exit 0
fi
trap 'aufraeumen' EXIT
trap 'exit 1' TERM INT
bt power on >/dev/null
[ "$ANLASS" -eq 0 ] && log "Bluetooth-Adapter bereit (eingeschaltet; gekoppelte Controller verbinden sich mit der PS-Taste)"
for _ in 1 2 3 4 5 6; do                                   # Wünsche, die während der Arbeit dazukommen, gleich mit erledigen
	verwalten
	[ $W_KOPPELN -eq 1 ] && koppeln
	liste_schreiben true
	wuensche
	[ $W_ZAHL -eq 0 ] && break
done
sleep "$BREMSE"                                            # Bremse: der Dienst lässt sich nicht im Kreis jagen
exit 0
