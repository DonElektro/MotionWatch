#!/bin/bash
# MoveEye Test-Runner: nach jedem Job (ACTIONS_RUNNER_HOOK_JOB_COMPLETED), als Benutzer mwrunner. Gehört root.
# Kiosk-Simulator wieder starten (Pause-Datei, Fortschritt und Bild fürs Testbild weg), Arbeitsordner und Reste des Jobs aufräumen.
# Quelle: werkzeuge/test_runner/job_ende.sh (runner_einrichten.sh und moveeye-hp-update spielen ihn ein).
set -u
P="${MW_KIOSK_PAUSE:-/run/moveeye-test/kiosk_pause}"
# Reste des Tests dieses Benutzers (wie reste_beenden() in dauer.py): Simulator (MoveEyeSim3D, Godot), Xvfb, MoveEye
# (webcam_bewegung_*.py) - der Prüfstand startet sie in eigenen Sitzungen; nach einem abgebrochenen Job könnten sie
# weiterlaufen. Die Pause fällt erst, wenn keiner mehr läuft: nie zwei Simulatoren am HP. MW_RESTE_NUR (nur Tests): nur
# Prozesse, deren Befehlszeile diesen Text enthält.
reste() {
	local d pid comm cmd ich=$$
	for d in /proc/[0-9]*; do
		pid="${d#/proc/}"
		[ "$pid" = "$ich" ] && continue
		[ -O "$d" ] || continue
		comm="$(cat "$d/comm" 2>/dev/null)" || continue
		[[ "$(cat "$d/stat" 2>/dev/null)" =~ \)\ Z\  ]] && continue          # Zombie: schon beendet, wartet nur aufs Abholen
		cmd="$(tr '\0' ' ' < "$d/cmdline" 2>/dev/null)" || continue
		[ -n "${MW_RESTE_NUR:-}" ] && [[ "$cmd" != *"$MW_RESTE_NUR"* ]] && continue
		case "$comm" in
			MoveEyeSim3D*|Godot*|Xvfb*) echo "$pid" ;;
			*) [[ "$cmd" =~ webcam_bewegung_[0-9_]+\.py ]] && echo "$pid" ;;
		esac
	done
}
reste_beenden() {   # TERM, nach 15 s KILL; Exit 0, wenn keiner mehr läuft
	local sig t r
	for sig in TERM KILL; do
		r="$(reste)"
		[ -z "$r" ] && return 0
		echo "Reste des Jobs beenden ($sig): $(echo "$r" | tr '\n' ' ')"
		# shellcheck disable=SC2086  # eine PID pro Wort
		kill -s "$sig" $r 2>/dev/null
		t=$(( $(date +%s) + $([ "$sig" = TERM ] && echo "${MW_RESTE_WARTEN:-15}" || echo 5) ))
		while [ -n "$(reste)" ] && [ "$(date +%s)" -lt "$t" ]; do sleep 0.2; done
	done
	[ -z "$(reste)" ]
}
if reste_beenden; then
	rm -f -- "$P" && echo "Kiosk-Simulator: Pause beendet (das Testbild zeigt noch 2 Min. die Zusammenfassung)"
else
	echo "Reste des Jobs lassen sich nicht beenden ($(reste | tr '\n' ' ')) - Kiosk-Pause bleibt (höchstens 7 Std.)"
fi
D="$(dirname "$P")"
rm -f -- "$D/fortschritt.json" "$D/fortschritt.json.neu" "$D/bild.png" "$D/bild.png.neu" "$D/bild_klein.png" "$D/bild_klein.png.neu"
BASIS="${MW_RUNNER_HOME:-/var/lib/mwrunner}/runner/_work/"
W="${GITHUB_WORKSPACE:-}"
case "$W" in
	"$BASIS"?*) [ -d "$W" ] && find "$W" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + && echo "Arbeitsordner geleert: $W" ;;
esac
# Reste von Prüfstand / Erkennungstest dieses Benutzers in /tmp (nur die eigenen, nur diese Namen)
find "${MW_JOBENDE_TMP:-/tmp}" -maxdepth 1 -user "$(id -u)" \( -name 'mw_pruefstand_*' -o -name 'mw_erk_lauf_*' -o -name 'mw_erkennung_*' \) \
	-exec rm -rf -- {} + 2>/dev/null
echo "Platz: $(df -h "${MW_RUNNER_HOME:-/var/lib/mwrunner}" | awk 'NR==2 {print $4}') frei"
exit 0
