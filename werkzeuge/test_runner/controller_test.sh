#!/bin/bash
# MoveEye Controller koppeln - Prüfung ohne Bluetooth (CI-Job «HP-Update»; lokal: bash werkzeuge/test_runner/controller_test.sh).
# Kein root, kein echtes Bluetooth: ein Ersatz-bluetoothctl (Zustand in Dateien) und Ersatz für rfkill / systemctl.
#  1. controller_koppeln.sh: kein Adapter -> «Kein Bluetooth – USB-Stick nötig …»; DualSense erscheint -> gekoppelt,
#     vertraut, verbunden, «pairable» wieder aus, Suche beendet; schon gekoppelter Controller im Kopplungs-Modus -> entfernt
#     und neu gekoppelt; falscher Hersteller (Modalias) mit DualSense-Namen und Kopfhörer -> nicht gekoppelt; nichts
#     gefunden; Koppeln scheitert; bluetoothctl fehlt; Name mit Befehlen wird nie ausgeführt; keine Adresse im Status.
#  2. controller_fenster.py: Status nur als geprüfte Daten (Verknüpfung, Grösse, unbekannter Schritt), Wunsch-Datei leer.
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
# Ersatz: Geräte in $FAKE_BT/geraete/<Adresse>/{name,modalias,paired,trusted,connected}; $FAKE_BT/kommt/<Adresse> erscheint
# während einer Suche nach $FAKE_BT/verzoegerung s
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
			mkdir -p "$S/geraete"; for d in "$S"/kommt/*; do [ -d "$d" ] && mv "$d" "$S/geraete/"; done
			sleep "$T"; rm -f "$S/suche"
		else
			rm -f "$S/suche"; echo "Discovery stopped"
		fi ;;
	devices) for d in "$S"/geraete/*; do [ -d "$d" ] && echo "Device $(basename "$d") $(cat "$d/name")"; done ;;
	info)
		d="$S/geraete/$1"
		[ -d "$d" ] || { echo "Device $1 not available"; exit 1; }
		printf 'Device %s (public)\n\tName: %s\n' "$1" "$(cat "$d/name")"
		[ -f "$d/modalias" ] && printf '\tModalias: %s\n' "$(cat "$d/modalias")"
		printf '\tPaired: %s\n\tTrusted: %s\n\tConnected: %s\n' "$(feld "$1" paired)" "$(feld "$1" trusted)" "$(feld "$1" connected)" ;;
	pair)
		[ -d "$S/geraete/$1" ] || { echo "Device $1 not available"; exit 1; }
		[ -e "$S/pair_fehler" ] && { echo "Failed to pair: org.bluez.Error.AuthenticationFailed"; exit 1; }
		echo yes > "$S/geraete/$1/paired"; echo "Pairing successful" ;;
	trust) echo yes > "$S/geraete/$1/trusted" ;;
	connect) echo yes > "$S/geraete/$1/connected"; echo "Connection successful" ;;
	remove) mkdir -p "$S/kommt"; rm -f "$S/geraete/$1/paired" "$S/geraete/$1/trusted"; mv "$S/geraete/$1" "$S/kommt/"; echo "Device has been removed" ;;
	*) echo "unbekannt: $c"; exit 1 ;;
esac
exit 0
EOF
for b in rfkill systemctl; do   # systemctl is-active: «aus» (dann muss das Skript bluetooth.service starten)
	printf '#!/bin/sh\necho "%s $*" >> "$FAKE_BT/aufrufe"\n[ "$1" = is-active ] && exit 3\nexit 0\n' "$b" > "$W/bin/$b"
done
chmod 755 "$W/bin/"*

geraet() {   # geraet ORT ADRESSE NAME [MODALIAS] [paired] [connected]
	local d="$FAKE_BT/$1/$2"
	mkdir -p "$d"; printf '%s\n' "$3" > "$d/name"
	[ -n "${4:-}" ] && printf '%s\n' "$4" > "$d/modalias"
	[ -n "${5:-}" ] && echo yes > "$d/paired"
	[ -n "${6:-}" ] && echo yes > "$d/connected"
	return 0
}
neu() {   # neu NAME: frischer Zustand (Adapter da)
	export FAKE_BT="$W/$1"
	mkdir -p "$FAKE_BT/sys/hci0" "$FAKE_BT/status" "$FAKE_BT/spiel" "$FAKE_BT/geraete" "$FAKE_BT/kommt"
	touch "$FAKE_BT/spiel/controller_koppeln"
}
koppeln() {   # koppeln [SUCH_S]: das Skript wie der Dienst (ohne Optionen), Ersatz-Werkzeuge vorne im PATH
	PATH="$W/bin:$PATH" MW_BT_SYS="$FAKE_BT/sys" MW_BT_STATUS_DIR="$FAKE_BT/status" MW_BT_WUNSCH="$FAKE_BT/spiel/controller_koppeln" \
		MW_BT_SUCH_S="${1:-6}" MW_BT_TAKT=0.3 timeout 120 bash "$H" > "$FAKE_BT/log" 2>&1
}
st() { python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); print(d[sys.argv[2]])' "$FAKE_BT/status/status.json" "$1" 2>/dev/null; }
hat() { grep -q -- "$1" "$FAKE_BT/aufrufe"; }
feld() { cat "$FAKE_BT/geraete/$1/$2" 2>/dev/null; }
DS="A0:AB:51:12:34:56"                                          # erfundene Adressen
keine_adresse() { ! grep -qiE '([0-9a-f]{2}:){5}[0-9a-f]{2}' "$FAKE_BT/status/status.json" "$FAKE_BT/log"; }

echo "--- 1. controller_koppeln.sh (Ersatz-bluetoothctl)"
bash -n "$H" && ok "bash -n" || fehler "bash -n"

neu ohne; rmdir "$FAKE_BT/sys/hci0"
koppeln; [ "$(st schritt)" = kein_adapter ] && [ "$(st text)" = "Kein Bluetooth – USB-Stick nötig oder Controller per USB-C-Kabel" ] \
	&& [ "$(st ok)" = False ] && ok "kein Adapter: «$(st text)»" || { fehler "kein Adapter"; cat "$FAKE_BT/log"; }
[ ! -e "$FAKE_BT/spiel/controller_koppeln" ] && ok "Wunsch-Datei weggeräumt (keine Schleife der Pfad-Einheit)" || fehler "Wunsch-Datei bleibt"

neu dienst; touch "$FAKE_BT/kein_dienst"
koppeln; [ "$(st schritt)" = kein_adapter ] && ok "Adapter da, Bluetooth antwortet nicht: ebenso «Kein Bluetooth»" || fehler "Dienst antwortet nicht"
hat "rfkill unblock bluetooth" && hat "systemctl start bluetooth.service" && ok "rfkill unblock, bluetooth.service gestartet" || fehler "rfkill / Dienst"

neu gut
geraet kommt "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100"
geraet geraete "11:22:33:44:55:66" "Kopfhoerer X" "usb:v1234p0001d0001"
echo 1 > "$FAKE_BT/verzoegerung"
koppeln 8; [ "$(st schritt)" = fertig ] && [ "$(st ok)" = True ] && [ "$(feld "$DS" paired)" = yes ] && [ "$(feld "$DS" trusted)" = yes ] \
	&& [ "$(feld "$DS" connected)" = yes ] && ok "DualSense erscheint: gekoppelt, vertraut, verbunden («$(st text)»)" || { fehler "DualSense"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }
hat "^--agent NoInputNoOutput --timeout 30 pair $DS" && ok "Koppeln mit eigenem Agenten (NoInputNoOutput)" || fehler "Agent"
[ ! -e "$FAKE_BT/geraete/11:22:33:44:55:66/paired" ] && ! hat "pair 11:22:33:44:55:66" && ok "Kopfhörer nicht angefasst" || fehler "Kopfhörer gekoppelt"
[ "$(cat "$FAKE_BT/pairable")" = off ] && ok "«pairable» danach wieder aus" || fehler "pairable bleibt an"
hat "discoverable" && fehler "HP sichtbar gemacht (discoverable)" || ok "HP selbst nicht sichtbar (discoverable unberührt)"
pgrep -f "$W/bin/bluetoothctl.*scan on" >/dev/null && fehler "Suche läuft noch" || ok "Suche beendet"
keine_adresse && ok "keine Bluetooth-Adresse im Status / Protokoll" || fehler "Adresse im Status / Protokoll"
python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); assert set(d) == {"schritt", "ok", "rest_s", "t", "text"}' "$FAKE_BT/status/status.json" \
	&& [ "$(stat -c %a "$FAKE_BT/status/status.json")" = 644 ] && ok "Status: gültiges JSON, nur bekannte Felder, lesbar (644)" || fehler "Status-Datei"

neu wieder
geraet geraete "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100" ja
echo 0 > "$FAKE_BT/verzoegerung"
koppeln 6; [ "$(st schritt)" = fertig ] && hat "^remove $DS" && [ "$(feld "$DS" connected)" = yes ] \
	&& ok "schon gekoppelt, wieder im Kopplungs-Modus: entfernt, neu gesucht, neu gekoppelt" || { fehler "neu koppeln"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }

neu falsch
geraet kommt "$DS" "DualSense Wireless Controller" "usb:v1234p0CE6d0100"
geraet kommt "22:33:44:55:66:77" 'DualSense Wireless Controller$(touch '"$W"'/boese)' ""
echo 0 > "$FAKE_BT/verzoegerung"
koppeln 3; [ "$(st schritt)" = nicht_gefunden ] && ! hat "pair " && ok "DualSense-Name mit falschem Hersteller / Name mit Befehl: nicht gekoppelt («$(st text)»)" \
	|| { fehler "falscher Hersteller gekoppelt"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }
[ ! -e "$W/boese" ] && ok "Gerätename wird nie ausgeführt" || fehler "Gerätename ausgeführt"

neu namen
geraet kommt "$DS" "DualSense Wireless Controller"
echo 0 > "$FAKE_BT/verzoegerung"
koppeln 4; [ "$(st schritt)" = fertig ] && ok "ohne Modalias: der genaue Name genügt" || { fehler "ohne Modalias"; cat "$FAKE_BT/log"; }

neu leer
koppeln 2; [ "$(st schritt)" = nicht_gefunden ] && [ "$(st ok)" = False ] && ok "nichts gefunden: «$(st text)»" || fehler "nichts gefunden"

neu schon
geraet geraete "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100" ja ja
koppeln 2; [ "$(st schritt)" = fertig ] && [ "$(st ok)" = True ] && ! hat "^remove" && ok "schon verbunden, kein neuer: «$(st text)»" || { fehler "schon verbunden"; cat "$FAKE_BT/log"; }

neu scheitert
geraet kommt "$DS" "DualSense Wireless Controller" "usb:v054Cp0CE6d0100"; touch "$FAKE_BT/pair_fehler"; echo 0 > "$FAKE_BT/verzoegerung"
koppeln 4; [ "$(st schritt)" = fehler ] && [ "$(grep -c "pair $DS" "$FAKE_BT/aufrufe")" = 2 ] && [ "$(cat "$FAKE_BT/pairable")" = off ] \
	&& ok "Koppeln scheitert: zweimal versucht, «$(st text)»" || { fehler "Koppeln scheitert"; cat "$FAKE_BT/log" "$FAKE_BT/aufrufe"; }

neu ohne_bluez
PATH="/usr/bin:/bin" MW_BTCTL="$W/fehlt/bluetoothctl" MW_BT_SYS="$FAKE_BT/sys" MW_BT_STATUS_DIR="$FAKE_BT/status" \
	MW_BT_WUNSCH="$FAKE_BT/spiel/controller_koppeln" bash "$H" > "$FAKE_BT/log" 2>&1
[ "$(st schritt)" = fehler ] && grep -q bluez "$FAKE_BT/status/status.json" && ok "bluetoothctl fehlt: «$(st text)»" || fehler "ohne bluez"

# ---------------------------------------------------------------- 2. Fenster: Status nur als Daten
echo "--- 2. controller_fenster.py (Status geprüft lesen, Wunsch-Datei)"
python3 -m py_compile "$R/simulator3d/beilagen_linux/controller_fenster.py" && ok "py_compile" || fehler "py_compile"
python3 -I - "$R/simulator3d/beilagen_linux/controller_fenster.py" "$W/f" <<'EOF' && ok "Status: Verknüpfung, zu gross, unbekannter Schritt, falsche Typen -> leer; Wunsch-Datei leer, nie über eine Verknüpfung" || fehler "controller_fenster.py"
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("cf", sys.argv[1]); cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
w = sys.argv[2]; os.makedirs(w)
p = os.path.join(w, "status.json")
json.dump({"schritt": "suche", "ok": None, "rest_s": 40, "t": 5, "text": "Suche\x1b[31m …"}, open(p, "w"))
d = cf.status_lesen(p); assert d["schritt"] == "suche" and d["rest_s"] == 40 and "\x1b" not in d["text"], d
json.dump({"schritt": "rm -rf", "t": 1}, open(p, "w")); assert cf.status_lesen(p) == {}
json.dump({"schritt": "fertig", "t": True, "rest_s": "9", "ok": "ja", "text": 5}, open(p, "w"))
d = cf.status_lesen(p); assert d == {"schritt": "fertig", "t": 0, "rest_s": 0, "text": "", "ok": None}, d
open(p, "w").write("x" * 5000); assert cf.status_lesen(p) == {}
os.remove(p); os.symlink("/etc/hostname", p); assert cf.status_lesen(p) == {}
wu = os.path.join(w, "controller_koppeln")
assert cf.wunsch_schreiben(wu) and os.path.getsize(wu) == 0
os.remove(wu); os.symlink(os.path.join(w, "ziel"), wu); assert not cf.wunsch_schreiben(wu) and not os.path.exists(os.path.join(w, "ziel"))
assert not cf.wunsch_schreiben(os.path.join(w, "fehlt", "controller_koppeln"))
EOF

echo
if [ $F -eq 0 ]; then echo "Controller-Test: OK"; else echo "Controller-Test: $F Fehler"; fi
exit $F
