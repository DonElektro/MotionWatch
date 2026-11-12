#!/bin/bash
# MoveEye Controller koppeln - Prüfung ohne Bluetooth (CI-Job «HP-Update»; lokal: bash werkzeuge/test_runner/controller_test.sh).
# Kein root, kein echtes Bluetooth: ein Ersatz-bluetoothctl (Zustand in Dateien) und Ersatz für rfkill / systemctl.
#  1. controller_koppeln.sh koppeln: kein Adapter -> «Kein Bluetooth-Adapter gefunden – …»; DualSense erscheint -> gekoppelt,
#     vertraut, verbunden («Verbunden ✔»), «pairable» wieder aus, Suche beendet; schon gekoppelter Controller im
#     Kopplungs-Modus -> entfernt und neu gekoppelt; gekoppelter, aber ausgeschalteter Controller -> bleibt unberührt;
#     falscher Hersteller (Modalias) mit DualSense-Namen, Kopfhörer mit DualSense-Namen (Geräteklasse), Tastatur -> nie
#     gekoppelt; DualShock 4 / Xbox nur mit Klasse bzw. Symbol «Gamepad»; nichts gefunden; Koppeln scheitert; bluetoothctl
#     fehlt; Name mit Befehlen wird nie ausgeführt; keine Adresse in Status / Liste / Protokoll.
#  2. Verwalten (HP_FASSUNG 7): Liste mit Akku (BlueZ bzw. Treiber), Trennen / Vergessen nur über das Kürzel aus der Liste und
#     nur für Gamepads; falsche Wunsch-Namen, Verknüpfungen, Ordner ohne Wirkung; Ruhe trennt nur Gamepads; Abbrechen beendet
#     die Suche; Start ohne Wunsch (udev: Adapter taucht auf) schaltet nur ein.
#  3. controller_fenster.py: Status / Liste nur als geprüfte Daten, Wünsche nur mit festen Namen, Bedienung (Fokus, zweimal
#     «Vergessen»), Controller als Bedienung (Ersatz-js), das ganze Fenster mit einem Ersatz-Tk (alle Zustände zeichnen,
#     klicken, Tasten); mit echtem Tk + Xvfb, wenn beides da ist.
#  4. hp_wache.py Pads: langsam geschobener Stick zählt, Rauschen nicht, gehaltener Stick höchstens 10 Min., Ruhe-Zeit.
# shellcheck disable=SC2015,SC2016  # «A && ok || fehler»: ok gibt immer 0 zurück; Ersatz-Befehle in «…» laufen erst später
set -u
HIER="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
R="$(cd "$HIER/../.." && pwd)"
H="$R/simulator3d/beilagen_linux/controller_koppeln.sh"
W="$(mktemp -d)"
trap 'pkill -f "$W/bin/bluetoothctl" 2>/dev/null; rm -rf "$W"' EXIT
F=0
ok() { echo "  ok: $*"; }
fehler() { echo "  FEHLER: $*"; F=$((F + 1)); }
mkdir -p "$W/bin"

# ---------------------------------------------------------------- Ersatz-bluetoothctl
cat > "$W/bin/bluetoothctl" <<'EOF'
#!/bin/bash
# Ersatz: Geräte in $FAKE_BT/geraete/<Adresse>/{name,modalias,klasse,symbol,akku,rssi,paired,trusted,connected};
# $FAKE_BT/kommt/<Adresse> erscheint während einer Suche nach $FAKE_BT/verzoegerung s (dann mit Signal «RSSI»)
S="$FAKE_BT"
echo "$*" >> "$S/aufrufe"
T=5
while [ $# -gt 0 ]; do case "$1" in --agent) shift 2 ;; --timeout) T="$2"; shift 2 ;; *) break ;; esac; done
c="${1:-}"; shift
feld() { cat "$S/geraete/$1/$2" 2>/dev/null || echo no; }
case "$c" in
	show) [ -e "$S/kein_dienst" ] && exit 1; printf 'Controller 00:11:22:33:44:55 (public)\n\tPowered: yes\n' ;;
	power) echo "Changing power $1 succeeded" ;;
	pairable) echo "$1" > "$S/pairable"; echo "Changing pairable $1 succeeded" ;;
	scan)
		if [ "$1" = on ]; then
			echo an > "$S/suche"; echo "Discovery started"
			sleep "$(cat "$S/verzoegerung" 2>/dev/null || echo 1)"
			mkdir -p "$S/geraete"; for d in "$S"/kommt/*; do [ -d "$d" ] && { touch "$d/rssi"; mv "$d" "$S/geraete/"; }; done
			sleep "$T"; rm -f "$S/suche"
		else
			rm -f "$S/suche"; echo "Discovery stopped"
		fi ;;
	devices) for d in "$S"/geraete/*; do [ -d "$d" ] && echo "Device $(basename "$d") $(cat "$d/name")"; done ;;
	info)
		d="$S/geraete/$1"
		[ -d "$d" ] || { echo "Device $1 not available"; exit 1; }
		printf 'Device %s (public)\n\tName: %s\n' "$1" "$(cat "$d/name")"
		[ -f "$d/klasse" ] && printf '\tClass: %s\n' "$(cat "$d/klasse")"
		[ -f "$d/symbol" ] && printf '\tIcon: %s\n' "$(cat "$d/symbol")"
		printf '\tPaired: %s\n\tTrusted: %s\n\tConnected: %s\n' "$(feld "$1" paired)" "$(feld "$1" trusted)" "$(feld "$1" connected)"
		[ -f "$d/modalias" ] && printf '\tModalias: %s\n' "$(cat "$d/modalias")"
		[ -f "$d/rssi" ] && printf '\tRSSI: -52\n'
		[ -f "$d/akku" ] && printf '\tBattery Percentage: 0x%x (%d)\n' "$(cat "$d/akku")" "$(cat "$d/akku")"
		true ;;
	pair)
		[ -d "$S/geraete/$1" ] || { echo "Device $1 not available"; exit 1; }
		[ -e "$S/pair_fehler" ] && { echo "Failed to pair: org.bluez.Error.AuthenticationFailed"; exit 1; }
		echo yes > "$S/geraete/$1/paired"; echo "Pairing successful" ;;
	trust) echo yes > "$S/geraete/$1/trusted" ;;
	connect) echo yes > "$S/geraete/$1/connected"; echo "Connection successful" ;;
	disconnect) echo no > "$S/geraete/$1/connected"; echo "Successful disconnected" ;;
	remove) mkdir -p "$S/kommt"; rm -f "$S/geraete/$1/paired" "$S/geraete/$1/trusted" "$S/geraete/$1/rssi"; mv "$S/geraete/$1" "$S/kommt/"; echo "Device has been removed" ;;
	*) echo "unbekannt: $c"; exit 1 ;;
esac
exit 0
EOF
for b in rfkill systemctl; do   # systemctl is-active: «aus» (dann muss das Skript bluetooth.service starten)
	printf '#!/bin/sh\necho "%s $*" >> "$FAKE_BT/aufrufe"\n[ "$1" = is-active ] && exit 3\nexit 0\n' "$b" > "$W/bin/$b"
done
chmod 755 "$W/bin/"*

geraet() {   # geraet ORT ADRESSE NAME [MODALIAS] [paired] [connected] [KLASSE] [SYMBOL] [rssi]
	local d="$FAKE_BT/$1/$2"
	mkdir -p "$d"; printf '%s\n' "$3" > "$d/name"
	[ -n "${4:-}" ] && printf '%s\n' "$4" > "$d/modalias"
	[ -n "${5:-}" ] && echo yes > "$d/paired"
	[ -n "${6:-}" ] && echo yes > "$d/connected"
	[ -n "${7:-}" ] && printf '%s\n' "$7" > "$d/klasse"
	[ -n "${8:-}" ] && printf '%s\n' "$8" > "$d/symbol"
	[ -n "${9:-}" ] && touch "$d/rssi"
	return 0
}
neu() {   # neu NAME [WUNSCH…]: frischer Zustand (Adapter da), Wunsch-Dateien (Standard: controller_koppeln; «-» = keine)
	export FAKE_BT="$W/$1"; shift
	mkdir -p "$FAKE_BT/sys/hci0" "$FAKE_BT/status" "$FAKE_BT/spiel" "$FAKE_BT/geraete" "$FAKE_BT/kommt" "$FAKE_BT/strom"
	: > "$FAKE_BT/aufrufe"
	[ $# -eq 0 ] && set -- controller_koppeln
	local w
	for w in "$@"; do [ "$w" = - ] || touch "$FAKE_BT/spiel/$w"; done
}
koppeln() {   # koppeln [SUCH_S]: das Skript wie der Dienst (ohne Optionen, ohne Terminal), Ersatz-Werkzeuge vorne im PATH
	PATH="$W/bin:$PATH" MW_BT_SYS="$FAKE_BT/sys" MW_BT_STATUS_DIR="$FAKE_BT/status" MW_BT_WUNSCH="$FAKE_BT/spiel/controller_koppeln" \
		MW_BT_STROM="$FAKE_BT/strom" MW_BT_SUCH_S="${1:-6}" MW_BT_TAKT=0.3 MW_BT_BREMSE=0 timeout 120 bash "$H" > "$FAKE_BT/log" 2>&1 < /dev/null
}
st() { python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); print(d[sys.argv[2]])' "$FAKE_BT/status/status.json" "$1" 2>/dev/null; }
li() { python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); print(eval(sys.argv[2], {"d": d, "L": d["liste"]}))' "$FAKE_BT/status/liste.json" "$1" 2>/dev/null; }
kuerzel() { printf 'moveeye|%s' "$1" | sha256sum | cut -c1-10; }
hat() { grep -q -- "$1" "$FAKE_BT/aufrufe"; }
feld() { cat "$FAKE_BT/geraete/$1/$2" 2>/dev/null; }
DS="A0:AB:51:12:34:56" DS2="A0:AB:51:65:43:21" KH="11:22:33:44:55:66"   # erfundene Adressen
keine_adresse() { ! grep -qiE '([0-9a-f]{2}:){5}[0-9a-f]{2}' "$FAKE_BT/status/"*.json "$FAKE_BT/log"; }
KEIN="Kein Bluetooth-Adapter gefunden – USB-Bluetooth-Stick einstecken oder Controller per USB-C-Kabel anschliessen"

echo "--- 1. controller_koppeln.sh: koppeln (Ersatz-bluetoothctl)"
bash -n "$H" && ok "bash -n" || fehler "bash -n"

neu ohne; rmdir "$FAKE_BT/sys/hci0"
koppeln; [ "$(st schritt)" = kein_adapter ] && [ "$(st text)" = "$KEIN" ] \
	&& [ "$(st ok)" = False ] && ok "kein Adapter: «$(st text)»" || { fehler "kein Adapter"; cat "$FAKE_BT/log"; }
[ ! -e "$FAKE_BT/spiel/controller_koppeln" ] && ok "Wunsch-Datei weggeräumt (keine Schleife der Pfad-Einheit)" || fehler "Wunsch-Datei bleibt"
[ "$(li 'd["adapter"], L')" = "(False, [])" ] && ok "kein Adapter: Liste leer, «adapter»: false" || fehler "Liste ohne Adapter"
! hat "scan on" && ! hat "power on" && ok "kein Adapter: kein Bluetooth-Befehl" || fehler "ohne Adapter Bluetooth-Befehle"

neu dienst; touch "$FAKE_BT/kein_dienst"
koppeln; [ "$(st schritt)" = kein_adapter ] && ok "Adapter da, Bluetooth antwortet nicht: ebenso «Kein Bluetooth-Adapter»" || fehler "Dienst antwortet nicht"
hat "rfkill unblock bluetooth" && hat "systemctl start bluetooth.service" && ok "rfkill unblock, bluetooth.service gestartet" || fehler "rfkill / Dienst"

neu gut
geraet kommt "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100" "" "" 0x002508 input-gaming
geraet geraete "$KH" "Kopfhoerer X" "usb:v1234p0001d0001"
echo 1 > "$FAKE_BT/verzoegerung"
koppeln 8; [ "$(st schritt)" = fertig ] && [ "$(st ok)" = True ] && [ "$(st text)" = "Verbunden ✔" ] && [ "$(feld "$DS" paired)" = yes ] && [ "$(feld "$DS" trusted)" = yes ] \
	&& [ "$(feld "$DS" connected)" = yes ] && ok "DualSense erscheint: gekoppelt, vertraut, verbunden («$(st text)»)" || { fehler "DualSense"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }
hat "^--agent NoInputNoOutput --timeout 30 pair $DS" && ok "Koppeln mit eigenem Agenten (NoInputNoOutput, keine Eingabe)" || fehler "Agent"
[ ! -e "$FAKE_BT/geraete/$KH/paired" ] && ! hat "pair $KH" && ok "Kopfhörer nicht angefasst" || fehler "Kopfhörer gekoppelt"
[ "$(cat "$FAKE_BT/pairable")" = off ] && ok "«pairable» danach wieder aus" || fehler "pairable bleibt an"
hat "discoverable" && fehler "HP sichtbar gemacht (discoverable)" || ok "HP selbst nicht sichtbar (discoverable unberührt)"
pgrep -f "$W/bin/bluetoothctl.*scan on" >/dev/null && fehler "Suche läuft noch" || ok "Suche beendet"
keine_adresse && ok "keine Bluetooth-Adresse in Status / Liste / Protokoll" || fehler "Adresse in Status / Liste / Protokoll"
python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); assert set(d) == {"schritt", "ok", "rest_s", "t", "text"}' "$FAKE_BT/status/status.json" \
	&& [ "$(stat -c %a "$FAKE_BT/status/status.json")" = 644 ] && ok "Status: gültiges JSON, nur bekannte Felder, lesbar (644)" || fehler "Status-Datei"
[ "$(li 'len(L), L[0]["art"], L[0]["verbunden"], L[0]["akku"], L[0]["id"]')" = "(1, 'DualSense', True, None, '$(kuerzel "$DS")')" ] \
	&& [ "$(stat -c %a "$FAKE_BT/status/liste.json")" = 644 ] && ok "Liste: 1 DualSense, verbunden, Kürzel statt Adresse" || { fehler "Liste nach dem Koppeln"; cat "$FAKE_BT/status/liste.json"; }

neu wieder
geraet geraete "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100" ja "" "" "" rssi
echo 0 > "$FAKE_BT/verzoegerung"
koppeln 6; [ "$(st schritt)" = fertig ] && hat "^remove $DS" && [ "$(feld "$DS" connected)" = yes ] \
	&& ok "schon gekoppelt, wieder im Kopplungs-Modus (Signal da): entfernt, neu gesucht, neu gekoppelt" || { fehler "neu koppeln"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }

neu aus
geraet geraete "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100" ja
koppeln 2; [ "$(st schritt)" = nicht_gefunden ] && [ "$(st text)" = "Kein Controller gefunden" ] && ! hat "^remove" && ! hat "pair $DS" && [ "$(feld "$DS" paired)" = yes ] \
	&& ok "gekoppelter Controller ist aus (kein Signal): bleibt gekoppelt, «$(st text)»" || { fehler "ausgeschalteter Controller angefasst"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }

neu falsch
geraet kommt "$DS" "DualSense Wireless Controller" "usb:v1234p0CE6d0100"
geraet kommt "22:33:44:55:66:77" 'DualSense Wireless Controller$(touch '"$W"'/boese)' ""
geraet kommt "$KH" "DualSense Wireless Controller" "" "" "" 0x240404 audio-headset
geraet kommt "33:44:55:66:77:88" "Wireless Controller"
geraet kommt "44:55:66:77:88:99" "Xbox Wireless Controller" "" "" "" 0x000540 input-keyboard
geraet kommt "55:66:77:88:99:AA" "Tastatur K" "usb:v046DpB342d0001" "" "" 0x002540 input-keyboard
echo 0 > "$FAKE_BT/verzoegerung"
koppeln 3; [ "$(st schritt)" = nicht_gefunden ] && ! hat "pair " && ok "falscher Hersteller, Name mit Befehl, Kopfhörer mit DualSense-Namen, «Wireless Controller» ohne Klasse, Tastaturen: nichts gekoppelt" \
	|| { fehler "falsches Gerät gekoppelt"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }
[ ! -e "$W/boese" ] && ok "Gerätename wird nie ausgeführt" || fehler "Gerätename ausgeführt"

neu namen
geraet kommt "$DS" "DualSense Wireless Controller"
echo 0 > "$FAKE_BT/verzoegerung"
koppeln 4; [ "$(st schritt)" = fertig ] && ok "ohne Modalias: der genaue Name genügt" || { fehler "ohne Modalias"; cat "$FAKE_BT/log"; }

neu ds4
geraet kommt "$DS" "Wireless Controller" "" "" "" 0x002508
echo 0 > "$FAKE_BT/verzoegerung"
koppeln 4; [ "$(st schritt)" = fertig ] && [ "$(li 'L[0]["art"]')" = "DualShock 4" ] && ok "DualShock 4 («Wireless Controller» mit Geräteklasse Gamepad): gekoppelt" || { fehler "DualShock 4"; cat "$FAKE_BT/log"; }

neu xbox
geraet kommt "$DS" "Xbox Wireless Controller" "" "" "" "" input-gaming
echo 0 > "$FAKE_BT/verzoegerung"
koppeln 4; [ "$(st schritt)" = fertig ] && [ "$(li 'L[0]["art"]')" = "Xbox-Controller" ] && ok "Xbox-Controller (Name mit Symbol «Gamepad»): gekoppelt" || { fehler "Xbox"; cat "$FAKE_BT/log"; }

neu leer
koppeln 2; [ "$(st schritt)" = nicht_gefunden ] && [ "$(st ok)" = False ] && ok "nichts gefunden nach der Suchzeit: «$(st text)»" || fehler "nichts gefunden"

neu schon
geraet geraete "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100" ja ja
koppeln 2; [ "$(st schritt)" = fertig ] && [ "$(st ok)" = True ] && ! hat "^remove" && ok "schon verbunden, kein neuer: «$(st text)»" || { fehler "schon verbunden"; cat "$FAKE_BT/log"; }

neu scheitert
geraet kommt "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100"; touch "$FAKE_BT/pair_fehler"; echo 0 > "$FAKE_BT/verzoegerung"
koppeln 4; [ "$(st schritt)" = fehler ] && [ "$(grep -c "pair $DS" "$FAKE_BT/aufrufe")" = 2 ] && [ "$(cat "$FAKE_BT/pairable")" = off ] \
	&& ok "Koppeln scheitert: zweimal versucht, «$(st text)»" || { fehler "Koppeln scheitert"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }

neu ohne_bluez
PATH="/usr/bin:/bin" MW_BTCTL="$W/fehlt/bluetoothctl" MW_BT_SYS="$FAKE_BT/sys" MW_BT_STATUS_DIR="$FAKE_BT/status" MW_BT_BREMSE=0 \
	MW_BT_WUNSCH="$FAKE_BT/spiel/controller_koppeln" bash "$H" > "$FAKE_BT/log" 2>&1 < /dev/null
[ "$(st schritt)" = fehler ] && grep -q bluez "$FAKE_BT/status/status.json" && ok "bluetoothctl fehlt: «$(st text)»" || fehler "ohne bluez"

# ---------------------------------------------------------------- 2. Verwalten
echo "--- 2. controller_koppeln.sh: Liste, Trennen, Vergessen, Ruhe, Abbrechen, Start ohne Wunsch"
zwei() {   # zwei gekoppelte Controller (einer verbunden, Akku von BlueZ; einer aus, Akku vom Treiber) und ein verbundener Kopfhörer
	geraet geraete "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100" ja ja 0x002508
	echo 70 > "$FAKE_BT/geraete/$DS/akku"
	geraet geraete "$DS2" "Wireless Controller" "usb:v054Cp09CCd0100" ja
	mkdir -p "$FAKE_BT/strom/ps-controller-battery-a0:ab:51:65:43:21"; echo 55 > "$FAKE_BT/strom/ps-controller-battery-a0:ab:51:65:43:21/capacity"
	geraet geraete "$KH" "Kopfhoerer X" "usb:v1234p0001d0001" ja ja 0x240404
}
neu liste controller_liste; zwei
koppeln; [ ! -e "$FAKE_BT/status/status.json" ] && ! hat "scan on" && ! hat "pairable on" \
	&& ok "Wunsch «Liste»: keine Suche, kein Kopplungs-Status" || { fehler "Liste löst eine Suche aus"; cat "$FAKE_BT/aufrufe"; }
[ "$(li 'd["adapter"], [(e["art"], e["verbunden"], e["akku"]) for e in L]')" = "(True, [('DualSense', True, 70), ('DualShock 4', False, 55)])" ] \
	&& ok "Liste: DualSense verbunden Akku 70 % (BlueZ), DualShock 4 aus Akku 55 % (Treiber); Kopfhörer steht nicht drin" || { fehler "Liste"; cat "$FAKE_BT/status/liste.json"; }
keine_adresse && ! grep -q "Kopfhoerer" "$FAKE_BT/status/liste.json" && ok "Liste: keine Adresse, kein Name aus dem Funk" || fehler "Liste verrät Adresse / Namen"

neu trennen "controller_trennen.$(kuerzel "$DS")"; zwei
koppeln; [ "$(feld "$DS" connected)" = no ] && hat "^disconnect $DS" && ! hat "disconnect $KH" && ! hat "^remove" && [ "$(feld "$DS" paired)" = yes ] \
	&& [ "$(li 'L[0]["verbunden"]')" = False ] && ok "«Trennen» (Kürzel): nur dieser Controller getrennt, bleibt gekoppelt, Liste neu" || { fehler "Trennen"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }

neu vergessen "controller_vergessen.$(kuerzel "$DS2")"; zwei
koppeln; hat "^remove $DS2" && ! hat "^remove $DS$" && [ "$(li 'len(L), L[0]["art"]')" = "(1, 'DualSense')" ] \
	&& ok "«Vergessen» (Kürzel): Kopplung dieses Controllers gelöscht, der andere bleibt" || { fehler "Vergessen"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }

neu fremd "controller_trennen.$(kuerzel "$KH")" "controller_vergessen.$(kuerzel "$KH")" "controller_vergessen.0000000000" \
	"controller_trennen.$DS" 'controller_vergessen.$(touch boese2)' "controller_trennen.ABCDEF0123" "controller_unsinn"
zwei
ln -s /etc/hostname "$FAKE_BT/spiel/controller_trennen.$(kuerzel "$DS")x"; mkdir "$FAKE_BT/spiel/controller_ordner"; touch "$FAKE_BT/spiel/controller_ordner/x"
touch "$FAKE_BT/spiel/spielen" "$FAKE_BT/spiel/fenster_offen"
( cd "$FAKE_BT/spiel" && koppeln )
! hat "disconnect" && ! hat "^remove" && [ "$(feld "$KH" connected)" = yes ] && [ "$(feld "$DS" connected)" = yes ] \
	&& ok "Kürzel eines Kopfhörers, unbekanntes Kürzel, Adresse statt Kürzel, Name mit Befehl, Unsinn: ohne Wirkung" || { fehler "falscher Wunsch hatte Wirkung"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }
[ -z "$(find "$FAKE_BT/spiel" -name 'controller_*')" ] && [ -e /etc/hostname ] && [ -e "$FAKE_BT/spiel/spielen" ] && [ -e "$FAKE_BT/spiel/fenster_offen" ] \
	&& [ ! -e "$FAKE_BT/spiel/boese2" ] && [ ! -e boese2 ] \
	&& ok "alle Wunsch-Dateien weggeräumt (auch Verknüpfung und Ordner, ohne ihnen zu folgen); Spielen-Datei und Marke bleiben" || { fehler "Wunsch-Dateien"; ls -la "$FAKE_BT/spiel"; }

neu ruhe controller_ruhe; zwei
koppeln; hat "^disconnect $DS" && ! hat "disconnect $KH" && [ "$(feld "$KH" connected)" = yes ] && [ "$(feld "$DS" paired)" = yes ] \
	&& ok "«Ruhe» (lange keine Eingabe): Controller getrennt, bleibt gekoppelt; Kopfhörer unberührt" || { fehler "Ruhe"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }

neu abbruch
T0=$(date +%s)
koppeln 40 &
KP=$!
sleep 3; [ "$(st schritt)" = suche ] || fehler "Suche läuft nicht"
touch "$FAKE_BT/spiel/controller_abbrechen"
wait "$KP"
[ "$(st schritt)" = abgebrochen ] && [ $(( $(date +%s) - T0 )) -lt 20 ] && [ "$(cat "$FAKE_BT/pairable")" = off ] && [ -z "$(find "$FAKE_BT/spiel" -name 'controller_*')" ] \
	&& ! pgrep -f "$W/bin/bluetoothctl.*scan on" >/dev/null \
	&& ok "«Abbrechen» beendet die Suche nach $(( $(date +%s) - T0 )) s (statt 40), «pairable» aus" || { fehler "Abbrechen"; cat "$FAKE_BT/log"; }

neu udev -; zwei
koppeln; hat "^power on" && ! hat "scan on" && ! hat "pairable on" && [ ! -e "$FAKE_BT/status/status.json" ] && [ "$(li 'len(L)')" = 2 ] \
	&& grep -q "Bluetooth-Adapter bereit" "$FAKE_BT/log" \
	&& ok "Start ohne Wunsch (udev: Adapter taucht auf / Stick eingesteckt): nur einschalten, Liste schreiben" || { fehler "Start ohne Wunsch"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }
neu udev_ohne -; rmdir "$FAKE_BT/sys/hci0"
T0=$(date +%s%N)
koppeln; [ ! -s "$FAKE_BT/aufrufe" ] && [ "$(li 'd["adapter"]')" = False ] && [ $(( ($(date +%s%N) - T0) / 1000000 )) -lt 3000 ] \
	&& ok "Start ohne Wunsch und ohne Adapter: nichts zu tun, sofort fertig ($(( ($(date +%s%N) - T0) / 1000000 )) ms)" || fehler "ohne Adapter nicht sofort fertig"

# ---------------------------------------------------------------- 3. Fenster
echo "--- 3. controller_fenster.py (Daten prüfen, Wünsche, Bedienung, Controller als Bedienung, Fenster mit Ersatz-Tk)"
CF="$R/simulator3d/beilagen_linux/controller_fenster.py"
python3 -m py_compile "$CF" && ok "py_compile" || fehler "py_compile"
python3 -I - "$CF" "$W/f" <<'EOF' && ok "Status / Liste: Verknüpfung, zu gross, unbekannte Werte, falsche Typen -> leer; Wünsche: nur feste Namen, leer, nie über eine Verknüpfung" || fehler "controller_fenster.py (Daten)"
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("cf", sys.argv[1]); cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
w = sys.argv[2]; os.makedirs(w)
p = os.path.join(w, "status.json")
json.dump({"schritt": "suche", "ok": None, "rest_s": 40, "t": 5, "text": "Suche\x1b[31m …"}, open(p, "w"))
d = cf.status_lesen(p); assert d["schritt"] == "suche" and d["rest_s"] == 40 and "\x1b" not in d["text"], d
json.dump({"schritt": "rm -rf", "t": 1}, open(p, "w")); assert cf.status_lesen(p) == {}
json.dump({"schritt": "fertig", "t": True, "rest_s": "9", "ok": "ja", "text": 5}, open(p, "w"))
d = cf.status_lesen(p); assert d == {"schritt": "fertig", "t": 0, "rest_s": 0, "text": "", "ok": None}, d
json.dump({"schritt": "abgebrochen", "t": 3, "text": "x" * 500}, open(p, "w")); assert len(cf.status_lesen(p)["text"]) == 160
open(p, "w").write("x" * 5000); assert cf.status_lesen(p) == {}
os.remove(p); os.symlink("/etc/hostname", p); assert cf.status_lesen(p) == {}
# Liste
L = os.path.join(w, "liste.json")
gut = {"id": "0123456789", "art": "DualSense", "verbunden": True, "akku": 70}
json.dump({"t": 9, "adapter": True, "liste": [gut, {"id": "A0:AB:51:12:34:56", "art": "DualSense"}, {"id": "abcdef0123", "art": "Kopfhörer"},
          {"id": "abcdef0124", "art": "Xbox-Controller", "verbunden": "ja", "akku": 300}, dict(gut, akku=1), "x", {"id": 5, "art": "DualSense"}]}, open(L, "w"))
d = cf.liste_lesen(L)
assert d == {"t": 9, "adapter": True, "liste": [gut, {"id": "abcdef0124", "art": "Xbox-Controller", "verbunden": False, "akku": None}]}, d
json.dump({"t": 9, "adapter": "ja", "liste": {}}, open(L, "w")); assert cf.liste_lesen(L) == {}
json.dump([1], open(L, "w")); assert cf.liste_lesen(L) == {}
os.remove(L); os.symlink("/etc/hostname", L); assert cf.liste_lesen(L) == {}
# Wünsche
wu = os.path.join(w, "controller_koppeln")
assert cf.wunsch_schreiben(wu) and os.path.getsize(wu) == 0
os.remove(wu); os.symlink(os.path.join(w, "ziel"), wu); assert not cf.wunsch_schreiben(wu) and not os.path.exists(os.path.join(w, "ziel"))
os.remove(wu)
assert not cf.wunsch_schreiben(os.path.join(w, "fehlt", "controller_koppeln"))
assert cf.wunsch(w, "koppeln") and cf.wunsch(w, "liste") and cf.wunsch(w, "abbrechen") and cf.wunsch(w, "trennen", "0123456789") and cf.wunsch(w, "vergessen", "abcdef0123")
for was, k in (("trennen", None), ("trennen", "../../etc/x"), ("vergessen", "A0:AB:51:12:34:56"), ("vergessen", "0123456789x"), ("rm", None), ("koppeln", "0123456789"), ("ruhe", None)):
    assert not cf.wunsch(w, was, k), (was, k)
da = sorted(n for n in os.listdir(w) if n.startswith("controller_"))
assert da == ["controller_abbrechen", "controller_koppeln", "controller_liste", "controller_trennen.0123456789", "controller_vergessen.abcdef0123"], da
assert all(os.path.getsize(os.path.join(w, n)) == 0 for n in da)
# Marke für hp_wache.py
m = os.path.join(w, "fenster_offen")
cf.marke_setzen(m); assert os.path.getsize(m) == 0; cf.marke_setzen(m, False); assert not os.path.exists(m); cf.marke_setzen(m, False)
EOF
python3 -I - "$CF" "$W/pad" <<'EOF' && ok "Bedienung: Fokus wandert, «Vergessen» erst beim zweiten Mal, Knöpfe folgen der Liste; Controller (Ersatz-js): Steuerkreuz / Stick / ✕ / ○" || fehler "controller_fenster.py (Bedienung)"
import importlib.util, os, struct, sys
spec = importlib.util.spec_from_file_location("cf", sys.argv[1]); cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
b = cf.Bedienung()
L = [{"id": "0123456789", "art": "DualSense", "verbunden": True, "akku": 70}, {"id": "abcdef0123", "art": "DualShock 4", "verbunden": False, "akku": None}]
k = b.knoepfe(L, False)
assert k == [("trennen", "0123456789"), ("vergessen", "0123456789"), ("vergessen", "abcdef0123"), ("koppeln",), ("zu",)], k
assert b.fokus == ("koppeln",)
assert b.waehlen(b.fokus, 100.0) == ("wunsch", "koppeln", None)
k = b.knoepfe(L, True); assert ("abbrechen",) in k and ("koppeln",) not in k and b.fokus == ("abbrechen",)   # Suche läuft: Fokus auf «Abbrechen»
assert b.waehlen(b.fokus, 101.0) == ("wunsch", "abbrechen", None)
k = b.knoepfe(L, False); assert b.fokus == ("koppeln",)
b.bewegen(k, 1); assert b.fokus == ("zu",); b.bewegen(k, 1); assert b.fokus == ("trennen", "0123456789")      # rundherum
b.bewegen(k, -1); b.bewegen(k, -1); assert b.fokus == ("koppeln",)
b.bewegen(k, -1); assert b.fokus == ("vergessen", "abcdef0123")
assert b.text(b.fokus, 200.0) == "Vergessen"
assert b.waehlen(b.fokus, 200.0) is None and b.text(b.fokus, 201.0) == "Wirklich vergessen?"                 # erst die Rückfrage
assert b.waehlen(b.fokus, 203.0) == ("wunsch", "vergessen", "abcdef0123")                                    # zweites Mal innert 6 s
assert b.waehlen(b.fokus, 300.0) is None and b.waehlen(b.fokus, 310.0) is None                               # zu spät: wieder nur die Rückfrage
assert b.waehlen(("vergessen", "0123456789"), 311.0) is None and b.waehlen(("vergessen", "abcdef0123"), 312.0) is None   # anderer Knopf: neu fragen
assert b.waehlen(("trennen", "0123456789"), 320.0) == ("wunsch", "trennen", "0123456789")
k = b.knoepfe(L[1:], False); assert b.fokus == ("koppeln",)                                                   # der Knopf ist weg: Fokus auf den Hauptknopf
assert b.waehlen(("zu",), 330.0) == ("zu",)
assert b.text(("koppeln",), 0, 0) == "Controller koppeln" and b.text(("koppeln",), 0, 2) == "Weiteren Controller koppeln"
assert len(b.knoepfe([dict(L[0], id="%010x" % i) for i in range(8)], False)) == 2 * cf.MAX_ZEILEN + 2          # höchstens 4 Zeilen
# Controller als Bedienung: FIFO statt /dev/input/js0
d = sys.argv[2]; os.makedirs(d); os.mkfifo(os.path.join(d, "js0"))
fd = os.open(os.path.join(d, "js0"), os.O_RDWR)
def js(*a):
    os.write(fd, b"".join(struct.pack("IhBB", 0, a[i + 1], a[i], a[i + 2]) for i in range(0, len(a), 3)))
p = cf.PadLeser(d)
assert p.lesen(10.0) == [] and len(p.fds) == 1 and cf.pads_da(d) == 1
js(0x81, 1, 0, 0x82, 32767, 7)                       # Startwerte (auch «gedrückt»): zählen nicht
assert p.lesen(10.1) == []
js(2, 32767, 7, 2, 0, 7, 2, -32767, 7, 2, 0, 7)       # Steuerkreuz ab, los, auf, los
assert p.lesen(10.2) == ["ab", "auf"]
js(2, 9000, 1, 2, 15000, 1, 2, 25000, 1, 2, 32000, 1, 2, 12000, 1, 2, 30000, 1, 2, 500, 1)   # linker Stick langsam nach unten: ein Schritt
assert p.lesen(10.3) == ["ab"]
js(2, -30000, 6, 2, 0, 6, 2, 30000, 0, 2, 0, 0)       # links (Steuerkreuz), rechts (Stick)
assert p.lesen(10.4) == ["auf", "ab"]
js(1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 5, 2, 30000, 3)   # ✕, ○, eine andere Taste, rechter Stick
assert p.lesen(10.5) == ["ok", "zurueck"]
os.remove(os.path.join(d, "js0")); assert p.lesen(20.0) == [] and p.fds == {}                                # abgezogen
EOF
# das ganze Fenster mit einem Ersatz-Tk: jeden Zustand zeichnen, klicken, Tasten, Controller - ohne Bildschirm
python3 -I - "$CF" "$W/tk" <<'EOF' && ok "Fenster (Ersatz-Tk): Start «auto» sucht ohne Controller sofort, zeigt mit Controller die Liste; alle Zustände, Klick, Tasten; Marke fenster_offen" || fehler "controller_fenster.py (Fenster)"
import importlib.util, json, os, sys, time, types
spec = importlib.util.spec_from_file_location("cf", sys.argv[1]); cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
w = sys.argv[2]; spiel = os.path.join(w, "spiel"); stat_d = os.path.join(w, "status"); os.makedirs(spiel); os.makedirs(stat_d); os.makedirs(os.path.join(w, "pads"))

class Canvas:
    def __init__(self, *a, **k): self.texte = []
    def pack(self, **k): pass
    def delete(self, *a): self.texte = []
    def create_text(self, *a, **k): self.texte.append(k.get("text", ""))
    def create_rectangle(self, *a, **k): pass
    create_oval = create_rectangle
    def bind(self, *a): pass
class Tk:
    def __init__(self, **k): self.da = True; self.nach = []
    def title(self, *a, **k): pass
    configure = geometry = attributes = protocol = bind_all = overrideredirect = title
    def winfo_screenwidth(self): return 1920
    def winfo_screenheight(self): return 1080
    def winfo_rootx(self): return 0
    winfo_rooty = winfo_rootx
    def winfo_exists(self): return self.da
    def after(self, ms, f): self.nach.append(f)
    def destroy(self): self.da = False
    def focus_force(self, *a, **k): pass
    lift = deiconify = withdraw = focus_force
class Font:
    def __init__(self, **k): pass
    def measure(self, t): return 8 * len(t)
cf.tk = types.SimpleNamespace(Tk=Tk, Canvas=Canvas, TclError=Exception)
cf.tkfont = types.SimpleNamespace(Font=Font, families=lambda r: ["DejaVu Sans"])

def args(start):
    return types.SimpleNamespace(wunsch=os.path.join(spiel, "controller_koppeln"), status=os.path.join(stat_d, "status.json"), start=start,
                                 fenster="900x560", pad_quelle=os.path.join(w, "pads"), ecke=None, pause="")
def status(schritt, ok=None, text="", rest=0, t=None):
    json.dump({"schritt": schritt, "ok": ok, "rest_s": rest, "t": int(time.time() if t is None else t), "text": text}, open(os.path.join(stat_d, "status.json"), "w"))
def liste(L, adapter=True, t=None):
    json.dump({"t": int(time.time() if t is None else t), "adapter": adapter, "liste": L}, open(os.path.join(stat_d, "liste.json"), "w"))
def wuensche():
    return sorted(n for n in os.listdir(spiel) if n.startswith("controller_"))
def leeren():
    for n in wuensche(): os.remove(os.path.join(spiel, n))
def klick(f, key):
    x0, y0, x1, y1 = f.boxen[key]
    f.klick(types.SimpleNamespace(x_root=(x0 + x1) // 2, y_root=(y0 + y1) // 2))
def taste(f, k):
    f.taste(types.SimpleNamespace(keysym=k))
def bild(f):
    return " | ".join(f.c.texte)
DS = {"id": "0123456789", "art": "DualSense", "verbunden": True, "akku": 70}

# Start «auto», kein Controller verbunden (leere Liste): die Suche beginnt von selbst, grosse Anleitung
f = cf.Fenster(args("auto"))
assert wuensche() == ["controller_liste"], wuensche()               # zuerst nur die Liste holen
assert os.path.exists(os.path.join(spiel, "fenster_offen"))          # Marke für hp_wache.py
liste([]); f.tick()
assert "controller_koppeln" in wuensche(), wuensche()
assert cf.HALTEN in bild(f) and "Bluetooth wird vorbereitet" in bild(f), bild(f)
assert cf.HALTEN == "PS-Taste und Create-Taste gedrückt halten, bis die Leiste schnell blau blinkt"
status("suche", rest=42); f.tick()
assert cf.HALTEN in bild(f) and "noch 42 s" in bild(f) and "Suche abbrechen" in bild(f) and ("abbrechen",) in f.boxen, bild(f)
leeren(); klick(f, ("abbrechen",)); assert wuensche() == ["controller_abbrechen"], wuensche()
status("koppeln", text="Controller gefunden – wird gekoppelt …"); f.tick(); assert "wird gekoppelt" in bild(f) and "Bitte warten" in bild(f)
status("fertig", ok=True, text="Verbunden ✔"); liste([DS]); f.tick()
assert "Verbunden ✔" in bild(f) and "DualSense  ·  verbunden  ·  Akku 70 %" in bild(f) and "Trennen" in bild(f) and "Vergessen" in bild(f), bild(f)
assert "Weiteren Controller koppeln" in bild(f) and f.ende_t is not None
status("nicht_gefunden", ok=False, text="Kein Controller gefunden"); f.tick(); assert "Kein Controller gefunden" in bild(f)
status("kein_adapter", ok=False, text=cf.KEIN_ADAPTER); f.tick(); assert cf.KEIN_ADAPTER in bild(f)
assert cf.KEIN_ADAPTER == "Kein Bluetooth-Adapter gefunden – USB-Bluetooth-Stick einstecken oder Controller per USB-C-Kabel anschliessen"
status("fehler", ok=False, text="Koppeln hat nicht geklappt"); f.tick(); assert "nicht geklappt" in bild(f) and "USB-C-Kabel" in bild(f)
g = f.gewollt; f.gewollt = time.time() - 400
status("suche", rest=10, t=time.time() - 300); f.tick(); assert "abgebrochen" in bild(f)       # der Dienst hängt: nicht ewig «Suche»
f.gewollt = g
# Trennen: ein Klick; Vergessen: erst die Rückfrage, dann der Wunsch; danach zeigt das Fenster wieder die Liste
leeren(); klick(f, ("trennen", "0123456789")); assert wuensche() == ["controller_trennen.0123456789"], wuensche()
assert "Gekoppelte Controller" in bild(f), bild(f)
leeren(); klick(f, ("vergessen", "0123456789")); assert wuensche() == [] and "Wirklich vergessen?" in bild(f), (wuensche(), bild(f))
klick(f, ("vergessen", "0123456789")); assert wuensche() == ["controller_vergessen.0123456789"], wuensche()
# Tastatur: Pfeile bewegen den Fokus, Enter wählt, Esc schliesst (Marke weg)
f.bed.fokus = ("koppeln",); f.zeichnen(); leeren()
taste(f, "Down"); assert f.bed.fokus == ("zu",); taste(f, "Up"); taste(f, "Return"); assert wuensche() == ["controller_koppeln"], wuensche()
taste(f, "Escape"); assert not f.root.da and not os.path.exists(os.path.join(spiel, "fenster_offen"))

# Start «auto», ein Controller ist schon verbunden: keine Suche, die Liste
leeren(); os.remove(os.path.join(stat_d, "status.json"))
f = cf.Fenster(args("auto")); liste([DS]); f.tick()
assert wuensche() == ["controller_liste"] and "Gekoppelte Controller" in bild(f) and "Akku 70 %" in bild(f), (wuensche(), bild(f))
f.zu()
# ohne Adapter (Liste vom Dienst): klare Meldung auch ohne Suche; Dienst fehlt ganz: «noch nicht eingerichtet»
leeren(); f = cf.Fenster(args("liste")); liste([], adapter=False); f.tick(); assert cf.KEIN_ADAPTER in bild(f) and wuensche() == ["controller_liste"]
f.zu(); leeren(); os.remove(os.path.join(stat_d, "liste.json"))
f = cf.Fenster(args("koppeln")); assert wuensche() == ["controller_koppeln", "controller_liste"]
f.gewollt -= 20; f.tick(); assert "noch nicht eingerichtet" in bild(f) and "USB-C-Kabel" in bild(f), bild(f)
f.zu()
# läuft schon eine Suche (anderes Fenster vorher): nicht noch einmal anstossen
leeren(); status("suche", rest=30); f = cf.Fenster(args("koppeln")); assert wuensche() == ["controller_liste"]; f.tick(); assert "noch 30 s" in bild(f)
f.zu()
# Ordner fehlt: klare Meldung
a = args("koppeln"); a.wunsch = os.path.join(w, "fehlt", "controller_koppeln")
f = cf.Fenster(a); f.tick(); assert "Koppeln geht hier nicht" in bild(f); f.zu()
# Knopf in der Ecke: sichtbar ohne Controller, weg mit Controller oder während eines Tests
a = args("auto"); a.ecke = "unten-rechts"; a.pause = os.path.join(w, "pause")
e = cf.Ecke(a); assert e.sichtbar
open(os.path.join(w, "pads", "js0"), "w").close(); e.tick(); assert not e.sichtbar
os.remove(os.path.join(w, "pads", "js0")); e.tick(); assert e.sichtbar
open(a.pause, "w").close(); e.tick(); assert not e.sichtbar
EOF
if python3 -c 'import tkinter' 2>/dev/null && command -v xvfb-run >/dev/null 2>&1; then
	mkdir -p "$W/echt/spiel" "$W/echt/status"
	printf '{"schritt": "suche", "ok": null, "rest_s": 40, "t": %d, "text": "Suche"}\n' "$(date +%s)" > "$W/echt/status/status.json"
	printf '{"t": %d, "adapter": true, "liste": [{"id": "0123456789", "art": "DualSense", "verbunden": true, "akku": 70}]}\n' "$(date +%s)" > "$W/echt/status/liste.json"
	timeout -s INT 6 xvfb-run -a python3 -I "$CF" --start liste --wunsch "$W/echt/spiel/controller_koppeln" --status "$W/echt/status/status.json" \
		--fenster 900x560 --pad-quelle "" > "$W/echt/log" 2>&1
	rc=$?
	{ [ $rc -eq 124 ] || [ $rc -eq 130 ] || [ $rc -eq 0 ]; } && ! grep -q "Traceback\|Error" "$W/echt/log" && [ -e "$W/echt/spiel/controller_liste" ] \
		&& ok "echtes Tk unter Xvfb: das Fenster läuft 6 s ohne Fehler" || { fehler "echtes Tk (Exit $rc)"; cat "$W/echt/log"; }
else
	echo "  (python3-tk / xvfb-run fehlen hier: das Fenster ist nur mit dem Ersatz-Tk geprüft)"
fi

# ---------------------------------------------------------------- 4. hp_wache.py: Controller-Eingaben
echo "--- 4. hp_wache.py Pads: was als Spielen zählt"
python3 -I - "$R/simulator3d/beilagen_linux/hp_wache.py" "$W/wpads" <<'EOF' && ok "langsam geschobener Stick zählt, Rauschen und Startwerte nicht; gehaltener Stick zählt höchstens 10 Min.; Ruhe-Zeit für das Trennen" || fehler "hp_wache.py Pads"
import importlib.util, os, struct, sys
spec = importlib.util.spec_from_file_location("hw", sys.argv[1]); hw = importlib.util.module_from_spec(spec); spec.loader.exec_module(hw)
hw.log = lambda *a: None
d = sys.argv[2]; os.makedirs(d); os.mkfifo(os.path.join(d, "js0"))
fd = os.open(os.path.join(d, "js0"), os.O_RDWR)
def js(*a):
    os.write(fd, b"".join(struct.pack("IhBB", 0, a[i + 1], a[i], a[i + 2]) for i in range(0, len(a), 3)))
p = hw.Pads(d, scan_s=0.0)
p.scan(1000.0); pfd = p.liste()[0]
assert p.ruhe_s(1000.0) == 0.0 and p.ruhe_s(1600.0) == 600.0            # Controller da, niemand bedient ihn
js(0x82, 0, 0, 0x82, 0, 1, 0x82, -32767, 2, 0x81, 1, 3)                 # Startwerte: Sticks Mitte, Trigger unten, eine Taste «gedrückt»
assert not p.lesen(pfd, 1001.0) and p.t_aktiv == 0.0
js(*[x for i in range(40) for x in (2, (300, -250, 180, -400)[i % 4], 0)])   # Rauschen um die Mitte: summiert sich nie
assert not p.lesen(pfd, 1002.0) and not p.gehalten(1002.0)
js(*[x for v in range(1500, 12001, 1500) for x in (2, v, 0)])           # langsam geschoben: 8 kleine Schritte bis 12000
assert p.lesen(pfd, 1003.0) and p.t_aktiv == 1003.0
js(*[x for v in range(13000, 32768, 1000) for x in (2, v, 0)])          # weiter bis zum Anschlag
assert p.lesen(pfd, 1004.0)
assert p.gehalten(1100.0) and p.t_aktiv == 1100.0                       # am Anschlag gehalten (keine Ereignisse mehr): zählt
assert p.gehalten(1604.0) and not p.gehalten(1605.0)                    # … aber höchstens 10 Min. ohne echte Bewegung (klemmender Stick)
js(2, 31000, 0); assert not p.lesen(pfd, 1700.0) and not p.gehalten(1700.0)   # Zittern am Anschlag ist keine Bewegung
js(2, 0, 0); assert p.lesen(pfd, 1800.0) and not p.gehalten(1810.0)     # losgelassen: Bewegung ja, gehalten nein
js(2, -32767 + 20000, 2); assert p.lesen(pfd, 1900.0) and p.gehalten(1901.0)  # Trigger (Ruhelage unten) halb gedrückt: gehalten
js(2, -32767, 2, 1, 1, 0, 1, 0, 0); assert p.lesen(pfd, 2000.0) and p.t_aktiv == 2000.0 and not p.gehalten(2001.0)
assert p.ruhe_s(2000.0 + 1200) == 1200.0                                # 20 Min. nach der letzten Eingabe
os.close(fd); os.remove(os.path.join(d, "js0")); p.scan(4000.0); assert p.ruhe_s(5000.0) == 0.0   # kein Controller mehr: keine Ruhe-Zeit
EOF

# ---------------------------------------------------------------- 5. Knöpfe des Simulator-PCs (HP_FASSUNG 8)
# (eigener Test, hier angehängt: so läuft er im CI-Job «HP-Update» mit, ohne dass ci.yml geändert werden muss)
echo "--- 5. hp_knoepfe_test.sh (Ausschalten, Browser)"
if bash "$HIER/hp_knoepfe_test.sh" > "$W/knoepfe.log" 2>&1; then ok "hp_knoepfe_test.sh: $(grep -c '^  ok' "$W/knoepfe.log") Prüfungen"
else fehler "hp_knoepfe_test.sh"; cat "$W/knoepfe.log"; fi

echo
if [ $F -eq 0 ]; then echo "Controller-Test: OK"; else echo "Controller-Test: $F Fehler"; fi
exit $F
