#!/usr/bin/env bash
# CI-Stand (GitHub Actions, Workflow «CI») für einen Zweig oder Commit – statt lokal zu rechnen auf das CI warten.
#   werkzeuge/ci_status.sh                    # aktueller Zweig: letzte Läufe
#   werkzeuge/ci_status.sh real-xyz           # ein Zweig
#   werkzeuge/ci_status.sh 1a2b3c4            # ein Commit (kurz oder lang)
#   werkzeuge/ci_status.sh real-xyz --warten  # auf den neusten Lauf warten (Exit 0 = grün, 1 = rot)
#   werkzeuge/ci_status.sh --warten --fehler  # warten, bei Rot die Protokolle der fehlgeschlagenen Schritte zeigen
#   werkzeuge/ci_status.sh --start            # Lauf von Hand auf dem Zweig starten (workflow_dispatch, mit Export) - ab
#                                             # 22.11.2026 nach den Regeln von ci_auswahl.py (nicht mehr immer alles)
#   werkzeuge/ci_status.sh --start --voll     # dasselbe, aber ALLES (Haken «alles»; auf main läuft ohnehin alles)
#   werkzeuge/ci_status.sh hp-test/<name> --warten --fehler   # HP-Testweg (hp_helfer.yml): Weiterreichen + Tests auf dem HP
# Braucht gh (angemeldet). Repository: DonElektro/MotionWatch (CI_REPO überschreibt).
set -u
REPO="${CI_REPO:-DonElektro/MotionWatch}"
WF="${CI_WORKFLOW:-ci.yml}"      # file (for --start)
NAME="${CI_NAME:-CI}"           # workflow name (list / wait: also works before ci.yml is on main)
ziel="" warten=0 fehler=0 start=0 voll_lauf=0
for a in "$@"; do
  case "$a" in
    --warten|-w) warten=1 ;;
    --fehler|-f) fehler=1 ;;
    --start) start=1 ;;
    --voll) voll_lauf=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) ziel="$a" ;;
  esac
done
[ -n "$ziel" ] || ziel=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
[ -n "$ziel" ] || { echo "kein Zweig / Commit"; exit 2; }

# HP-Testweg (hp_helfer.yml, CLAUDE.md «HP-Testweg»): der Push auf hp-test/<name> startet nur «Weiterreichen»; die Tests
# laufen in einem zweiten Lauf vom Stand main (Titel «HP-Test hp-test/<name> @<sha>»). Hier beide nacheinander verfolgen.
if [[ "$ziel" == hp-test/* ]]; then
  HPWF=hp_helfer.yml
  hp_liste() {     # $1 = "@" (test run), "(" (relay) or "" (both) -> lines "<id> <createdAt> <status> <conclusion> <title>", newest first
    gh run list -R "$REPO" --workflow "$HPWF" -L 40 --json databaseId,displayTitle,createdAt,status,conclusion \
      -q ".[] | select(.displayTitle | startswith(\"HP-Test $ziel $1\")) | \"\(.databaseId) \(.createdAt) \(.status) \(.conclusion) \(.displayTitle)\"" 2>/dev/null
  }
  if [ $start -eq 1 ]; then   # fallback only: the branch does not contain hp_helfer.yml yet (no run after the push)
    sha=$(git ls-remote origin "refs/heads/$ziel" 2>/dev/null | cut -f1)
    [ -n "$sha" ] || { echo "$ziel ist nicht auf origin (zuerst: git push origin HEAD:$ziel)"; exit 2; }
    gh workflow run "$HPWF" -R "$REPO" --ref main -f zweig="$ziel" -f sha="$sha" || exit 1
    echo "gestartet: HP-Test $ziel @$sha"; sleep 5; warten=1
  fi
  echo "HP-Testweg · $ziel"
  hp_liste "" | head -n 8
  [ $warten -eq 1 ] || exit 0
  neu=""
  for _ in $(seq 1 24); do neu=$(hp_liste "" | head -n 1); [ -n "$neu" ] && break; sleep 5; done
  [ -n "$neu" ] || { echo "kein Lauf gefunden (gepusht? enthält der Zweig .github/workflows/hp_helfer.yml von main? sonst: $0 $ziel --start)"; exit 2; }
  read -r id seit _ <<< "$neu"
  if [[ "$neu" == *"(weiterreichen)" ]]; then          # newest is the relay: wait for it, then for the test run it starts
    echo "warte auf Weiterreichen #$id"
    if ! gh run watch "$id" -R "$REPO" -i 10 --exit-status > /dev/null; then
      gh run view "$id" -R "$REPO" --log-failed | tail -40; echo "Ergebnis: nicht weitergereicht"; exit 1
    fi
    id=""
    for _ in $(seq 1 24); do
      t=$(hp_liste "@" | head -n 1)
      if [ -n "$t" ]; then read -r tid tseit _ <<< "$t"; [[ ! "$tseit" < "$seit" ]] && { id=$tid; break; }; fi
      sleep 5
    done
    [ -n "$id" ] || { echo "Testlauf (vom Stand main) nicht gefunden"; exit 2; }
  fi
  echo "warte auf HP-Test #$id  (https://github.com/$REPO/actions/runs/$id) - der HP rechnet einen Job aufs Mal, Warten ist normal"
  gh run watch "$id" -R "$REPO" -i 30 > /dev/null 2>&1
  gh run view "$id" -R "$REPO" --json jobs,conclusion \
    -t '{{range .jobs}}{{printf "  %-9s %s\n" .conclusion .name}}{{end}}Ergebnis: {{.conclusion}}{{"\n"}}'
  ok=$(gh run view "$id" -R "$REPO" --json jobs -q '[.jobs[] | select(.name == "Tests auf dem HP") | .conclusion][0] // "fehlt"')
  [ "$ok" = success ] && { echo "HP-Test grün"; exit 0; }
  echo "HP-Test nicht grün (Tests auf dem HP: ${ok:-übersprungen}) - Zusammenfassung und Artefakt: https://github.com/$REPO/actions/runs/$id"
  [ $fehler -eq 1 ] && gh run view "$id" -R "$REPO" --log-failed | tail -150
  exit 1
fi

sel=(--branch "$ziel") art="Zweig"
if [[ "$ziel" =~ ^[0-9a-f]{7,40}$ ]] && ! git show-ref -q --verify "refs/heads/$ziel" 2>/dev/null; then
  voll=$(git rev-parse --verify -q "$ziel^{commit}" 2>/dev/null || echo "$ziel")
  sel=(--commit "$voll") art="Commit"; ziel="$voll"
fi

if [ $start -eq 1 ]; then
  [ "$art" = "Zweig" ] || { echo "--start braucht einen Zweig"; exit 2; }
  gh workflow run "$WF" -R "$REPO" --ref "$ziel" -f alles="$([ $voll_lauf -eq 1 ] && echo true || echo false)" || exit 1
  echo "gestartet auf $ziel ($([ $voll_lauf -eq 1 ] && echo "alles" || echo "nach den Regeln - alles: --voll"))"; sleep 5; warten=1
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
