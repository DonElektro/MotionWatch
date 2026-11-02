#!/bin/bash
# MoveEye Kiosk - die Sitzung «MoveEye Kiosk» (Linux Mint, x11). kiosk_ein.sh kopiert diese Datei nach
# /usr/local/lib/moveeye-kiosk/ und meldet sie bei LightDM an (/usr/share/xsessions/moveeye-kiosk.desktop).
#   kiosk_sitzung.sh sitzung    die ganze Sitzung: Openbox + Simulator im Vollbild; Ctrl+Alt+D -> normales Mint (Cinnamon),
#                               nach dem Abmelden aus Cinnamon wieder der Kiosk
#   kiosk_sitzung.sh schleife   startet den Simulator und nach einem Absturz oder Beenden wieder neu
#   kiosk_sitzung.sh desktop    (Ctrl+Alt+D) Kiosk beenden, Cinnamon starten
#   kiosk_sitzung.sh neustart   (Ctrl+Alt+R) nur den Simulator neu starten
# Einstellungen: /etc/moveeye-kiosk.conf (SIM = Programmdatei, SIM_ARGS = Startoptionen). Protokolle: ~/.moveeye_kiosk/
# Testlauf-Pause (werkzeuge/test_runner): /etc/moveeye-kiosk-test.conf setzt PAUSE_DATEI. Solange diese Datei da ist (und
# jünger als PAUSE_MAX_S), ist der Simulator aus und startet nicht neu - der Test-Runner hat Grafik und Speicher für sich.
# TEST_BENUTZER: dieser lokale Benutzer darf den Bildschirm benutzen (xhost, nur wenn bei runner_einrichten.sh gewählt).
# Testbild (3.53.0): während der Pause zeigt testbild.py (python3-tk) Logo, «Test läuft – bitte nicht ausschalten» und den
# Fortschritt aus FORTSCHRITT_DATEI (nur Daten, JSON) samt Live-Bild; nach dem Test 2 Min. eine Zusammenfassung, dann
# startet der Simulator. Ohne python3-tk bleibt der Bildschirm dunkel.
set -u
LIB="/usr/local/lib/moveeye-kiosk"
CONF="/etc/moveeye-kiosk.conf"
LOGDIR="$HOME/.moveeye_kiosk"
RUN="${XDG_RUNTIME_DIR:-/tmp}/moveeye-kiosk-$(id -u)"
FLAG="$RUN/desktop"
# pgrep -f: der Simulator, auch wenn er sich nach einem Update selbst neu gestartet hat. Nur Befehlszeilen, die MIT dem
# Programm beginnen (sonst träfe es z. B. ein Terminal, in dem jemand «pgrep MoveEyeSim3D» tippt)
MUSTER='^([^ ]*/)?MoveEyeSim3D\.x86_64( |$)'
NAME='^MoveEyeSim3D'                     # dazu der Prozessname (auch bei Leerzeichen im Ordnerpfad)
sim_laeuft() { pgrep -u "$(id -u)" -f "$MUSTER" >/dev/null || pgrep -u "$(id -u)" "$NAME" >/dev/null; }
sim_signal() { pkill "-$1" -u "$(id -u)" -f "$MUSTER" 2>/dev/null; pkill "-$1" -u "$(id -u)" "$NAME" 2>/dev/null; return 0; }
SIM=""
SIM_ARGS=(--fullscreen -- --stream --no-update)
# shellcheck source=/dev/null
[ -r "$CONF" ] && . "$CONF"
PAUSE_DATEI=""
PAUSE_MAX_S=25200                         # 7 Std.: eine vergessene Pause-Datei hält den Kiosk nicht für immer an
TEST_BENUTZER=""
FORTSCHRITT_DATEI=""
TESTBILD_ENDE_S=120                       # so lange bleibt nach dem Test die Zusammenfassung stehen
# shellcheck source=/dev/null
[ -r /etc/moveeye-kiosk-test.conf ] && . /etc/moveeye-kiosk-test.conf
[ -z "$FORTSCHRITT_DATEI" ] && [ -n "$PAUSE_DATEI" ] && FORTSCHRITT_DATEI="$(dirname "$PAUSE_DATEI")/fortschritt.json"
TESTBILD="$LIB/testbild.py"
LOGO="$LIB/moveeye.png"
mkdir -p "$LOGDIR" "$RUN"

log() { printf '%s %s\n' "$(date '+%F %T')" "$*" >> "$LOGDIR/sitzung.log"; }

pausiert() {   # läuft ein Testlauf (Pause-Datei des Test-Runners da und nicht zu alt)?
	[ -n "$PAUSE_DATEI" ] && [ -f "$PAUSE_DATEI" ] || return 1
	local m
	m=$(stat -c %Y "$PAUSE_DATEI" 2>/dev/null) || return 1
	[ $(( $(date +%s) - m )) -lt "$PAUSE_MAX_S" ]
}

kuerzen() {   # Protokoll höchstens ~2 MB, die letzten Zeilen bleiben
	local f="$1"
	if [ -f "$f" ] && [ "$(stat -c %s "$f" 2>/dev/null || echo 0)" -gt 2000000 ]; then
		tail -n 5000 "$f" > "$f.neu" && mv -f "$f.neu" "$f"
	fi
}

TB=0 TB_N=0
testbild_an() {   # Testbild zeigen (läuft es schon, nichts tun; stürzt es ab, höchstens 5-mal neu)
	if [ "$TB" -gt 0 ] && kill -0 "$TB" 2>/dev/null; then return 0; fi
	[ "$TB" -gt 0 ] && { wait "$TB" 2>/dev/null; TB=0; }
	[ "$TB_N" -ge 5 ] && return 0
	TB_N=$((TB_N + 1))
	if [ -r "$TESTBILD" ] && python3 -c 'import tkinter' 2>/dev/null; then
		python3 -I "$TESTBILD" --pause "$PAUSE_DATEI" --fortschritt "$FORTSCHRITT_DATEI" --logo "$LOGO" \
			--ende-s "$TESTBILD_ENDE_S" >> "$LOGDIR/testbild.log" 2>&1 &
		TB=$!
		[ "$TB_N" -eq 1 ] && log "Testbild an"
	else
		[ "$TB_N" -eq 1 ] && log "Testbild fehlt ($TESTBILD oder python3-tk) - nur dunkler Hintergrund"
		TB_N=5
		command -v xsetroot >/dev/null 2>&1 && xsetroot -solid '#0f1624' 2>/dev/null
	fi
	return 0
}
testbild_nachlauf() {   # nach dem Test: die Zusammenfassung des Testbilds (2 Min.) abwarten, höchstens 150 s
	local i=0
	while [ "$TB" -gt 0 ] && kill -0 "$TB" 2>/dev/null && [ $i -lt 75 ]; do
		pausiert && return 0                      # schon der nächste Test: Testbild läuft weiter
		kill -0 "$eltern" 2>/dev/null || break
		sleep 2 & kind=$!; wait "$kind"; kind=0
		i=$((i + 1))
	done
	testbild_aus
}
testbild_aus() {
	if [ "$TB" -gt 0 ]; then kill -TERM "$TB" 2>/dev/null; wait "$TB" 2>/dev/null; fi
	TB=0 TB_N=0
	kuerzen "$LOGDIR/testbild.log"
	return 0
}

sim_stoppen() {
	sim_signal TERM
	local i
	for i in 1 2 3 4 5 6 7 8 9 10; do
		sim_laeuft || return 0
		sleep 0.5; : "$i"
	done
	sim_signal KILL
}

schleife() {
	local kind=0 t0 rc dauer schnell=0 pause warte=0
	trap '[ "$kind" -gt 0 ] && kill -TERM "$kind" 2>/dev/null; [ "$TB" -gt 0 ] && kill -TERM "$TB" 2>/dev/null; exit 0' TERM INT
	kuerzen "$LOGDIR/sim.log"
	local eltern=$PPID
	while :; do
		kill -0 "$eltern" 2>/dev/null || { log "Sitzung ist zu - Schleife endet"; exit 0; }   # abgemeldet / X beendet
		if [ -z "$SIM" ] || [ ! -x "$SIM" ]; then
			log "Simulator fehlt: '$SIM' - neuer Versuch in 30 s (kiosk_ein.sh im Ordner des Simulators starten)"
			sleep 30 & kind=$!; wait "$kind"; kind=0
			continue
		fi
		if pausiert; then                                 # Testlauf: Simulator aus, warten, danach wieder starten
			log "Testlauf ($PAUSE_DATEI): Simulator pausiert"
			sim_laeuft && sim_stoppen
			while pausiert; do
				kill -0 "$eltern" 2>/dev/null || { testbild_aus; log "Sitzung ist zu - Schleife endet"; exit 0; }
				testbild_an
				sleep 5 & kind=$!; wait "$kind"; kind=0
			done
			testbild_nachlauf
			pausiert && continue
			log "Testlauf fertig: Simulator startet wieder"
			schnell=0
			continue
		fi
		# nach einem Update startet sich der Simulator selbst neu (neuer Prozess): warten, bis er wieder zu ist
		while sim_laeuft; do
			pausiert && { sim_stoppen; break; }
			sleep 3 & kind=$!; wait "$kind"; kind=0
		done
		pausiert && continue
		log "Simulator startet: $SIM ${SIM_ARGS[*]}"
		t0=$(date +%s)
		( cd "$(dirname "$SIM")" && exec "$SIM" "${SIM_ARGS[@]}" ) >> "$LOGDIR/sim.log" 2>&1 &
		kind=$!
		if [ -n "$PAUSE_DATEI" ]; then                   # alle 3 s schauen, ob ein Testlauf den Bildschirm braucht
			while kill -0 "$kind" 2>/dev/null; do
				if pausiert; then sim_stoppen; break; fi
				sleep 3 & warte=$!; wait "$warte"
			done
		fi
		wait "$kind"; rc=$?; kind=0
		kill -0 "$eltern" 2>/dev/null || { log "Sitzung ist zu - Schleife endet"; exit 0; }
		if pausiert; then schnell=0; log "Simulator für einen Testlauf beendet"; continue; fi
		dauer=$(( $(date +%s) - t0 ))
		if [ "$dauer" -lt 60 ]; then schnell=$((schnell + 1)); else schnell=0; fi
		pause=2
		[ "$schnell" -ge 3 ] && pause=30                 # stürzt er immer gleich wieder ab: nicht im Sekundentakt
		log "Simulator beendet (Code $rc nach $dauer s) - neu in $pause s"
		kuerzen "$LOGDIR/sim.log"
		sleep "$pause" & kind=$!; wait "$kind"; kind=0
	done
}

kiosk_teil() {
	# Bildschirmschoner, Schwarzschalten und Energiesparen des Bildschirms aus (nur in dieser Sitzung)
	xset s off 2>/dev/null; xset s noblank 2>/dev/null; xset -dpms 2>/dev/null
	# Test-Runner darf den Bildschirm (Grafikkarte) benutzen - nur dieser lokale Benutzer, nur wenn so eingerichtet
	if [ -n "$TEST_BENUTZER" ] && command -v xhost >/dev/null 2>&1; then
		xhost "+SI:localuser:$TEST_BENUTZER" >/dev/null 2>&1 && log "Bildschirm freigegeben für $TEST_BENUTZER (Testläufe)"
	fi
	export XDG_CURRENT_DESKTOP=MoveEye-Kiosk XDG_SESSION_DESKTOP=moveeye-kiosk DESKTOP_SESSION=moveeye-kiosk
	rm -f "$FLAG"
	"$LIB/kiosk_sitzung.sh" schleife &
	local sp=$! t0 n=0
	# shellcheck disable=SC2064   # sp jetzt einsetzen
	trap "kill -TERM $sp 2>/dev/null; sim_stoppen; exit 0" TERM HUP INT
	if command -v openbox >/dev/null 2>&1; then
		while :; do
			t0=$(date +%s)
			openbox --config-file "$LIB/openbox.xml" >> "$LOGDIR/sitzung.log" 2>&1
			[ -f "$FLAG" ] && break
			if [ $(( $(date +%s) - t0 )) -lt 10 ]; then n=$((n + 1)); else n=0; fi
			log "Openbox beendet (ohne Ctrl+Alt+D) - neu"
			if [ "$n" -ge 5 ]; then
				log "Openbox startet nicht - Simulator läuft ohne Fenstermanager (ohne Ctrl+Alt+D)"
				wait "$sp"
				break
			fi
			sleep 1
		done
	else
		log "openbox fehlt (kiosk_ein.sh noch einmal starten) - Simulator ohne Fenstermanager, ohne Ctrl+Alt+D"
		wait "$sp"
	fi
	kill -TERM "$sp" 2>/dev/null
	wait "$sp" 2>/dev/null
	sim_stoppen
	trap - TERM HUP INT
}

cinnamon_teil() {
	local exe="cinnamon-session-cinnamon" t0
	if [ -r /usr/share/xsessions/cinnamon.desktop ]; then
		exe=$(sed -n 's/^Exec=//p' /usr/share/xsessions/cinnamon.desktop | head -n 1)
	fi
	command -v "${exe%% *}" >/dev/null 2>&1 || exe="cinnamon-session"
	log "Ctrl+Alt+D: normales Mint ($exe)"
	xset s default 2>/dev/null; xset +dpms 2>/dev/null
	export XDG_CURRENT_DESKTOP=X-Cinnamon XDG_SESSION_DESKTOP=cinnamon DESKTOP_SESSION=cinnamon GDMSESSION=cinnamon
	command -v dbus-update-activation-environment >/dev/null 2>&1 && \
		dbus-update-activation-environment --systemd DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP DESKTOP_SESSION GDMSESSION 2>/dev/null
	t0=$(date +%s)
	# shellcheck disable=SC2086   # Exec= kann Optionen enthalten
	$exe >> "$LOGDIR/sitzung.log" 2>&1
	log "Cinnamon beendet nach $(( $(date +%s) - t0 )) s (Abmelden) - zurück in den Kiosk"
	# was vom Desktop übrig bleiben könnte und über dem Simulator läge (Sperrbildschirm, Leiste, Desktop-Symbole)
	pkill -TERM -u "$(id -u)" -x cinnamon-screensaver 2>/dev/null
	pkill -TERM -u "$(id -u)" -x nemo-desktop 2>/dev/null
	pkill -TERM -u "$(id -u)" -x cinnamon 2>/dev/null
	sleep 1
}

sitzung() {
	kuerzen "$LOGDIR/sitzung.log"
	log "Sitzung «MoveEye Kiosk» beginnt (Benutzer $(id -un), DISPLAY=${DISPLAY:-?})"
	while :; do
		kiosk_teil
		if [ -f "$FLAG" ]; then
			rm -f "$FLAG"
			cinnamon_teil
			command -v dbus-update-activation-environment >/dev/null 2>&1 && \
				XDG_CURRENT_DESKTOP=MoveEye-Kiosk dbus-update-activation-environment --systemd XDG_CURRENT_DESKTOP 2>/dev/null
		else
			sleep 2
		fi
	done
}

case "${1:-}" in
	sitzung) sitzung ;;
	schleife) schleife ;;
	desktop)
		touch "$FLAG"
		log "Ctrl+Alt+D gedrückt"
		openbox --exit 2>/dev/null || sim_stoppen
		;;
	neustart)
		log "Ctrl+Alt+R: Simulator neu starten"
		sim_stoppen
		;;
	*) sed -n '2,9p' "$0"; exit 2 ;;
esac
