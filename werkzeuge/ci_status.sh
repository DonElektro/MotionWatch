#!/usr/bin/env bash
# CI-Stand (GitHub Actions, Workflow «CI») für einen Zweig oder Commit – statt lokal zu rechnen auf das CI warten.
#   werkzeuge/ci_status.sh                    # aktueller Zweig: letzte Läufe
#   werkzeuge/ci_status.sh real-xyz           # ein Zweig
#   werkzeuge/ci_status.sh 1a2b3c4            # ein Commit (kurz oder lang)
#   werkzeuge/ci_status.sh real-xyz --warten  # auf den neusten Lauf warten (Exit 0 = grün, 1 = rot)
#   werkzeuge/ci_status.sh --warten --fehler  # warten, bei Rot die Protokolle der fehlgeschlagenen Schritte zeigen
#   werkzeuge/ci_status.sh --start            # Lauf von Hand auf dem Zweig starten (workflow_dispatch, mit Export)
# Braucht gh (angemeldet). Repository: DonElektro/MotionWatch (CI_REPO überschreibt).
set -u
REPO="${CI_REPO:-DonElektro/MotionWatch}"
WF="${CI_WORKFLOW:-ci.yml}"      # file (for --start)
NAME="${CI_NAME:-CI}"           # workflow name (list / wait: also works before ci.yml is on main)
ziel="" warten=0 fehler=0 start=0
for a in "$@"; do
  case "$a" in
    --warten|-w) warten=1 ;;
    --fehler|-f) fehler=1 ;;
    --start) start=1 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) ziel="$a" ;;
  esac
done
[ -n "$ziel" ] || ziel=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
[ -n "$ziel" ] || { echo "kein Zweig / Commit"; exit 2; }

sel=(--branch "$ziel") art="Zweig"
if [[ "$ziel" =~ ^[0-9a-f]{7,40}$ ]] && ! git show-ref -q --verify "refs/heads/$ziel" 2>/dev/null; then
  voll=$(git rev-parse --verify -q "$ziel^{commit}" 2>/dev/null || echo "$ziel")
  sel=(--commit "$voll") art="Commit"; ziel="$voll"
fi

if [ $start -eq 1 ]; then
  [ "$art" = "Zweig" ] || { echo "--start braucht einen Zweig"; exit 2; }
  gh workflow run "$WF" -R "$REPO" --ref "$ziel" || exit 1
  echo "gestartet auf $ziel"; sleep 5; warten=1
fi

echo "CI «$NAME» · $art $ziel"
gh run list -R "$REPO" "${sel[@]}" -L 40 \
  --json databaseId,status,conclusion,headSha,event,createdAt,displayTitle,workflowName \
  -t '{{range .}}{{if eq .workflowName "'"$NAME"'"}}{{printf "%-11s %-9s %.7s %-17s %s  #%.0f  %.50s\n" .status .conclusion .headSha .event (timefmt "02.01. 15:04" .createdAt) .databaseId .displayTitle}}{{end}}{{end}}' || exit 1

[ $warten -eq 1 ] || exit 0
id=""
for _ in $(seq 1 24); do                     # just pushed: the run appears after a few seconds
  id=$(gh run list -R "$REPO" "${sel[@]}" -L 40 --json databaseId,workflowName \
       -q "[.[] | select(.workflowName == \"$NAME\")][0].databaseId // empty" 2>/dev/null)
  [ -n "$id" ] && break
  sleep 5
done
[ -n "$id" ] || { echo "kein Lauf gefunden (noch nicht gepusht?)"; exit 2; }
echo "warte auf Lauf #$id  (https://github.com/$REPO/actions/runs/$id)"
gh run watch "$id" -R "$REPO" -i 20 --exit-status >/dev/null
rc=$?
gh run view "$id" -R "$REPO" --json jobs,conclusion \
  -t '{{range .jobs}}{{printf "  %-9s %s\n" .conclusion .name}}{{end}}Ergebnis: {{.conclusion}}{{"\n"}}'
if [ $rc -ne 0 ] && [ $fehler -eq 1 ]; then gh run view "$id" -R "$REPO" --log-failed | tail -120; fi
[ $rc -eq 0 ]
