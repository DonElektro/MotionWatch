#!/bin/bash
# MoveEye Test-Runner: nach jedem Job (ACTIONS_RUNNER_HOOK_JOB_COMPLETED), als Benutzer mwrunner. Gehört root.
# Kiosk-Simulator wieder starten (Pause-Datei, Fortschritt und Bild fürs Testbild weg), Arbeitsordner und Reste des Jobs aufräumen.
# Quelle: werkzeuge/test_runner/job_ende.sh (runner_einrichten.sh und moveeye-hp-update spielen ihn ein).
set -u
P="${MW_KIOSK_PAUSE:-/run/moveeye-test/kiosk_pause}"
rm -f -- "$P" && echo "Kiosk-Simulator: Pause beendet (das Testbild zeigt noch 2 Min. die Zusammenfassung)"
D="$(dirname "$P")"
rm -f -- "$D/fortschritt.json" "$D/fortschritt.json.neu" "$D/bild.png" "$D/bild.png.neu" "$D/bild_klein.png" "$D/bild_klein.png.neu"
BASIS="${MW_RUNNER_HOME:-/var/lib/mwrunner}/runner/_work/"
W="${GITHUB_WORKSPACE:-}"
case "$W" in
	"$BASIS"?*) [ -d "$W" ] && find "$W" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + && echo "Arbeitsordner geleert: $W" ;;
esac
# Reste von Prüfstand / Erkennungstest dieses Benutzers in /tmp (nur die eigenen, nur diese Namen)
find /tmp -maxdepth 1 -user "$(id -u)" \( -name 'mw_pruefstand_*' -o -name 'mw_erk_lauf_*' -o -name 'mw_erkennung_*' \) \
	-exec rm -rf -- {} + 2>/dev/null
echo "Platz: $(df -h "${MW_RUNNER_HOME:-/var/lib/mwrunner}" | awk 'NR==2 {print $4}') frei"
exit 0
