#!/bin/bash
# MoveEye Test-Runner: vor jedem Job (ACTIONS_RUNNER_HOOK_JOB_STARTED), als Benutzer mwrunner. Gehört root.
# Lässt nur erlaubte Anlässe zu (nie Pull-Requests), pausiert den Kiosk-Simulator (Pause-Datei, kiosk_sitzung.sh) und
# legt den ersten Stand für das Testbild des Kiosks an (fortschritt.json, nur Daten; der Test schreibt ihn weiter).
# Quelle: werkzeuge/test_runner/job_start.sh (runner_einrichten.sh und moveeye-hp-update spielen ihn ein).
# 3.55.0: wird am HP gerade gespielt (Spielen-Datei von hp_wache.py / testbild.py, jünger als 15 Min.), bleibt der Kiosk
# an - die Jobs sehen das selbst (werkzeuge/test_runner/dauer.py) und warten bzw. hören gleich auf. HP-Diagnose: Testbild ohne
# Zusammenfassung am Schluss («ende»: false).
set -u
ERLAUBTE_REFS="refs/heads/main"
# shellcheck source=/dev/null
[ -r /etc/moveeye-runner.conf ] && . /etc/moveeye-runner.conf
P="${MW_KIOSK_PAUSE:-/run/moveeye-test/kiosk_pause}"
F="$(dirname "$P")/fortschritt.json"
S="${MW_SPIEL:-/run/moveeye-spiel/spielen}"
spielt() { [ -f "$S" ] && [ ! -L "$S" ] && [ $(( $(date +%s) - $(stat -c %Y "$S" 2>/dev/null || echo 0) )) -lt 900 ]; }
echo "MoveEye-Runner: ${GITHUB_REPOSITORY:-?} · ${GITHUB_WORKFLOW:-?} · Anlass ${GITHUB_EVENT_NAME:-?} · ${GITHUB_REF:-?}"
# zweite Sperre neben den Workflows selbst (fehlen die Angaben, nur warnen - der Runner gehört ohnehin nur zu diesem Repository)
case "${GITHUB_REPOSITORY:-}" in
	DonElektro/MotionWatch) ;;
	"") echo "Hinweis: GITHUB_REPOSITORY fehlt" ;;
	*) echo "::error::Fremdes Repository - abgelehnt"; exit 1 ;;
esac
case "${GITHUB_EVENT_NAME:-}" in
	workflow_dispatch|schedule|push) ;;
	"") echo "Hinweis: GITHUB_EVENT_NAME fehlt" ;;
	*) echo "::error::Anlass «${GITHUB_EVENT_NAME}» ist auf diesem Runner nicht erlaubt (nur von Hand, Zeitplan, Push auf main)"; exit 1 ;;
esac
if [ -n "${GITHUB_REF:-}" ]; then
	ok=0
	for r in $ERLAUBTE_REFS; do [ "$GITHUB_REF" = "$r" ] && ok=1; done
	[ $ok -eq 1 ] || { echo "::error::Workflows laufen hier nur vom Stand ${ERLAUBTE_REFS} (jetzt $GITHUB_REF)"; exit 1; }
fi
fremder_sim() { ps -eo uid=,comm= | awk -v me="$(id -u)" '$1 != me && $2 ~ /^MoveEyeSim3D/ {n++} END {exit n ? 0 : 1}'; }
if spielt; then
	echo "Am HP wird gerade gespielt - der Kiosk bleibt an (der Job wartet bzw. hört gleich auf)"
elif [ -d "$(dirname "$P")" ] && [ -w "$(dirname "$P")" ]; then
	# Testbild: Name des Workflows und Startzeit (JSON über python3, damit Sonderzeichen sicher verpackt sind)
	rm -f -- "$F" "$(dirname "$P")/bild.png" "$(dirname "$P")/bild_klein.png"
	if python3 -c 'import json, sys, time
d = {"titel": sys.argv[1][:40], "start": int(time.time())}
if sys.argv[1] == "HP-Diagnose":
    d["ende"] = False                       # kurze Prüfung: keine Zusammenfassung am Schluss
print(json.dumps(d))' "${GITHUB_WORKFLOW:-Test}" > "$F.neu" 2>/dev/null; then
		chmod 644 "$F.neu" && mv -f -- "$F.neu" "$F"
	else
		rm -f -- "$F.neu"
	fi
	printf 'Lauf %s %s\n' "${GITHUB_RUN_ID:-?}" "$(date '+%F %T')" > "$P"
	chmod 644 "$P"
	echo "Kiosk-Simulator: Pause angefordert (Testbild am HP)"
	i=0
	while fremder_sim && [ $i -lt 30 ]; do sleep 2; i=$((i + 1)); done
	if fremder_sim; then echo "Hinweis: der Kiosk-Simulator läuft noch (kiosk_sitzung.sh ohne Pause? runner_einrichten.sh noch einmal, dann neu starten)"
	else echo "Kiosk-Simulator ist aus"; fi
else
	echo "Hinweis: $(dirname "$P") fehlt - der Kiosk läuft weiter (runner_einrichten.sh noch einmal)"
fi
echo "Speicher: $(free -m | awk '/^Mem/ {print $7 " MB frei von " $2}') · Platz: $(df -h "${MW_RUNNER_HOME:-/var/lib/mwrunner}" | awk 'NR==2 {print $4}') frei"
exit 0
