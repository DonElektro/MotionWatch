#!/bin/bash
# MoveEye Dauerrechnen - Prüfung ohne HP (CI-Job «HP-Update»; lokal: bash werkzeuge/test_runner/dauer_test.sh). Kein root nötig.
#  1. hp_wache.py: Status-Dienst (rechnet / spielen), Lauscher auf den Simulator-Ports beim Rechnen: nur /info (Suche von
#     MoveEye) ist noch kein Wunsch, eine echte Anfrage schon -> Spielen-Datei, Ports werden freigegeben.
#  2. dauer.py halten: Test läuft, «Spielen» -> Test in wenigen Sekunden angehalten, Pause-Datei weg (Bildschirm frei), Stand
#     gesichert (nur ganze Fälle); 15 Min. ohne Spielen (schnelle Uhr: das Datum der Spielen-Datei wird zurückgestellt) ->
#     Pause wieder da, der Test rechnet genau dort weiter (kein Fall doppelt, keiner fehlt).
#  3. dauer.py waehlen / rechnen: Spielen -> «nichts»; HP-Update fällig -> «nichts»; reihum Erkennung -> KI -> Langzeit;
#     angehaltenes Paket kommt beim nächsten Lauf wieder dran und wird fertig.
# Ersatz-Programm statt Simulator / MoveEye (MW_DAUER_ERSATZ), schnelle Takte (MW_DAUER_TAKT).
# shellcheck disable=SC2015,SC2317  # «A && ok || fehler»: ok gibt immer 0 zurück; Hilfen laufen über «warte»
set -u
HIER="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
R="$(cd "$HIER/../.." && pwd)"
W="$(mktemp -d)"
PIDS=()
# shellcheck disable=SC2154  # p: in der Falle
trap 'for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done; rm -rf "$W"' EXIT
F=0
ok() { echo "  ok: $*"; }
fehler() { echo "  FEHLER: $*"; F=$((F + 1)); }
warte() {   # warte SEKUNDEN BEDINGUNG…: bis die Bedingung gilt
	local t=$(( $(date +%s) + $1 )); shift
	while ! "$@"; do [ "$(date +%s)" -ge "$t" ] && return 1; sleep 0.2; done
	return 0
}
mkdir -p "$W/run/test" "$W/run/spiel" "$W/home"
export MW_KIOSK_PAUSE="$W/run/test/kiosk_pause" MW_SPIEL="$W/run/spiel/spielen" MW_RUNNER_HOME="$W/home"
export MW_HPU_STEMPEL="$W/letzter_lauf" MW_DAUER_TAKT=0.2
D="$HIER/dauer.py"
spielen() { printf '{"grund": "test", "seit": %s}\n' "$(date +%s)" > "$MW_SPIEL"; }
ruhig_15min() { touch -d '16 minutes ago' "$MW_SPIEL"; }     # schnelle Uhr: 16 Min. ohne Spielen
pause_da() { [ -f "$MW_KIOSK_PAUSE" ]; }
pause_weg() { [ ! -e "$MW_KIOSK_PAUSE" ]; }
zeilen() { [ -f "$1" ] && grep -c . "$1" || echo 0; }

# Ersatz für die Arbeit: ein «Fall» alle 0,3 s, fortsetzbar (zählt, was schon da ist); SIGTERM = sofort aus (der angefangene
# Fall wird nicht geschrieben - wie beim echten Test)
cat > "$W/ersatz.py" <<'EOF'
import argparse, json, os, time
ap = argparse.ArgumentParser()
ap.add_argument("--art", default="erkennung"); ap.add_argument("--aus", required=True); ap.add_argument("--faelle", type=int, default=20)
a = ap.parse_args()
os.makedirs(a.aus, exist_ok=True)
if a.art == "ki":
    os.makedirs(os.path.join(a.aus, "pakete"), exist_ok=True)
    while len(os.listdir(os.path.join(a.aus, "pakete"))) < 6:
        time.sleep(0.3)
        n = len(os.listdir(os.path.join(a.aus, "pakete")))
        open(os.path.join(a.aus, "pakete", "ki_%02d.zip" % (n + 1)), "w").write("x")
elif a.art == "langzeit":
    p = os.path.join(a.aus, "proben.jsonl")
    while (sum(json.loads(l)["dt"] for l in open(p)) if os.path.exists(p) else 0) < 180 * 60:
        time.sleep(0.3)
        open(p, "a").write(json.dumps({"t": int(time.time()), "dt": 540, "bed": "nacht", "fehl": 0}) + "\n")
else:
    p = os.path.join(a.aus, "results.jsonl")
    fertig = sum(1 for _ in open(p)) if os.path.exists(p) else 0
    for i in range(fertig, a.faelle):
        time.sleep(0.3)
        with open(p, "a") as f:
            f.write(json.dumps({"key": "fall|%02d" % i}) + "\n")
EOF

# ---------------------------------------------------------------- 1. hp_wache.py
echo "--- 1. hp_wache.py (Status, Lauscher, Spielen-Wunsch)"
python3 -c 'import sys; print(sys.version.split()[0])' >/dev/null || { echo "python3 fehlt"; exit 1; }
PB=$(( 20000 + RANDOM % 20000 ))
SP1=$((PB + 1)) SP2=$((PB + 2)) STP=$((PB + 3))
touch "$MW_KIOSK_PAUSE"
python3 -I "$R/simulator3d/beilagen_linux/hp_wache.py" --spiel-datei "$MW_SPIEL" --pause "$MW_KIOSK_PAUSE" --ruhe-s 900 \
	--status-port "$STP" --sim-ports "$SP1,$SP2" > "$W/wache.log" 2>&1 &
PIDS+=($!)
get() { python3 -c 'import sys, urllib.request
try:
    with urllib.request.urlopen(sys.argv[1], timeout=3) as r: print(r.status, r.read(400).decode("utf-8", "replace"))
except urllib.error.HTTPError as e: print(e.code)
except Exception as e: print("weg", type(e).__name__)' "$1"; }
status_ist() { get "http://127.0.0.1:$STP/status.json" | grep -q "\"zustand\": \"$1\""; }
lauscht() { get "http://127.0.0.1:$SP1/info" | grep -q '^503'; }
warte 10 status_ist rechnet && ok "Status: rechnet" || { fehler "Status nicht «rechnet»"; cat "$W/wache.log"; }
warte 10 lauscht && ok "lauscht beim Rechnen auf dem Simulator-Port" || fehler "lauscht nicht"
[ ! -e "$MW_SPIEL" ] && ok "nur /info (Suche von MoveEye): kein Spielen" || fehler "Suche hat Spielen ausgelöst"
get "http://127.0.0.1:$SP1/frame.jpg" >/dev/null
warte 5 test -f "$MW_SPIEL" && ok "MoveEye verbindet sich -> Spielen-Datei" || fehler "keine Spielen-Datei"
python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); assert d["grund"] == "moveeye" and d["seit"] > 0' "$MW_SPIEL" \
	&& ok "Spielen-Datei: nur Daten (grund, seit)" || fehler "Inhalt der Spielen-Datei"
warte 5 status_ist spielen && ok "Status: spielen" || fehler "Status nicht «spielen»"
weg() { get "http://127.0.0.1:$SP1/info" | grep -q '^weg'; }
warte 5 weg && ok "Simulator-Port frei (für den Kiosk-Simulator)" || fehler "Port noch belegt"
get "http://127.0.0.1:$STP/bild.png" | grep -q '^404' && ok "kein Bild beim Spielen" || fehler "/bild.png"
get "http://127.0.0.1:$STP/../../etc/passwd" | grep -q '^404' && ok "unbekannte Pfade: 404" || fehler "Pfad"
ruhig_15min
warte 5 status_ist rechnet && ok "15 Min. ruhig -> wieder «rechnet», Lauscher wieder auf" || fehler "nach 15 Min."
rm -f "$MW_SPIEL"
handy() { get "http://127.0.0.1:$SP2/" | grep -q '^503'; }
warte 5 handy; warte 5 test -f "$MW_SPIEL" && python3 -c 'import json, sys; assert json.load(open(sys.argv[1]))["grund"] == "handy"' "$MW_SPIEL" \
	&& ok "Handy öffnet die Spiel-Seite -> Spielen" || fehler "Handy-Seite"
kill "${PIDS[0]}" 2>/dev/null; wait "${PIDS[0]}" 2>/dev/null
rm -f "$MW_SPIEL" "$MW_KIOSK_PAUSE"

# ---------------------------------------------------------------- 2. halten: Spielen -> Pause + Sicherung -> 15 Min. -> weiter
echo "--- 2. dauer.py halten (anhalten, sichern, weiterrechnen)"
O="$W/erk"
touch "$MW_KIOSK_PAUSE"
python3 "$D" halten --warten-max 120 -- python3 "$W/ersatz.py" --aus "$O" --faelle 20 > "$W/halten.log" 2>&1 &
HP=$!; PIDS+=("$HP")
mehr_als() { [ "$(zeilen "$O/results.jsonl")" -ge "$1" ]; }
warte 10 mehr_als 5 && ok "Test rechnet (5 Fälle)" || fehler "Test rechnet nicht"
T0=$(date +%s%N)
spielen
warte 5 pause_weg && ok "Spielen -> Pause-Datei weg nach $(( ($(date +%s%N) - T0) / 1000000 )) ms (Bildschirm frei)" || fehler "Pause bleibt"
N1=$(zeilen "$O/results.jsonl")
sleep 1.5
N2=$(zeilen "$O/results.jsonl")
[ "$N1" = "$N2" ] && [ "$N1" -ge 5 ] && [ "$N1" -lt 20 ] && ok "Test angehalten, Stand gesichert: $N1 von 20 Fällen" || fehler "Test läuft weiter ($N1 -> $N2)"
pgrep -f "^python3 $W/ersatz.py" >/dev/null && fehler "Ersatz-Test läuft noch" || ok "Test-Prozess beendet (Simulator / MoveEye wären zu)"
kill -0 "$HP" 2>/dev/null && ok "Job wartet (Spielen)" || fehler "Job beendet statt zu warten"
sleep 1
pause_weg && ok "Pause bleibt weg, solange gespielt wird" || fehler "Pause zu früh zurück"
ruhig_15min
warte 10 pause_da && ok "15 Min. ohne Spielen -> Pause wieder da (Kiosk-Simulator aus)" || fehler "Pause nicht zurück"
warte 20 mehr_als 20 && ok "weitergerechnet bis 20 Fälle" || fehler "nicht fertig ($(zeilen "$O/results.jsonl"))"
wait "$HP"; rc=$?
[ "$rc" = 0 ] && ok "halten: Exit 0" || fehler "halten: Exit $rc"
dopp=$(python3 -c 'import json, sys; k = [json.loads(l)["key"] for l in open(sys.argv[1])]; print(len(k) - len(set(k)), len(set(k)))' "$O/results.jsonl")
[ "$dopp" = "0 20" ] && ok "kein Fall doppelt, keiner fehlt" || fehler "Fälle: doppelt/eindeutig = $dopp"
grep -q "weiter, wo es stand" "$W/halten.log" && ok "Protokoll: weiter, wo es stand" || fehler "Protokoll"
rm -f "$MW_KIOSK_PAUSE" "$MW_SPIEL"

# ---------------------------------------------------------------- 3. waehlen / rechnen
echo "--- 3. dauer.py waehlen / rechnen"
export MW_DAUER_ERSATZ="$W/ersatz.py"
K='{"main": {"name": "main", "sha": "'"$(printf 'a%.0s' {1..40})"'"}, "vorher": {"name": "v3.53.0", "sha": "'"$(printf 'b%.0s' {1..40})"'"}}'
wert() { sed -n "s/^$1=//p" "$2" | tail -n 1; }
waehle() { : > "$W/aus"; python3 "$D" waehlen --kandidaten "$1" --ausgabe "$W/aus" > "$W/w.log" 2>&1 || { fehler "waehlen"; cat "$W/w.log"; }; }
spielen
waehle "$K"; [ "$(wert art "$W/aus")" = nichts ] && grep -q gespielt "$W/aus" && ok "Spielen: nichts rechnen" || fehler "trotz Spielen gewählt"
rm -f "$MW_SPIEL"
touch -d '21 hours ago' "$MW_HPU_STEMPEL"
waehle "$K"; [ "$(wert art "$W/aus")" = nichts ] && grep -q Update "$W/aus" && ok "HP-Update fällig: HP bleibt frei" || fehler "Update-Fenster"
touch "$MW_HPU_STEMPEL"
python3 "$D" waehlen --kandidaten '{"zweige": []}' --ausgabe /dev/null > /dev/null 2>&1 && fehler "Kandidaten ohne main angenommen" || ok "Kandidaten ohne main abgelehnt"
python3 "$D" waehlen --kandidaten '{"main": {"name": "x;rm", "sha": "123"}}' --ausgabe /dev/null > /dev/null 2>&1 && fehler "ungültiger Stand angenommen" || ok "ungültiger Stand / SHA abgelehnt"
waehle "$K"; P1=$(wert paket "$W/aus")
[ "$(wert art "$W/aus")" = erkennung ] && [ "$(wert plan "$W/aus")" = ursache ] && [ "$(wert laeufe "$W/aus")" = 3 ] \
	&& ok "zuerst: Erkennung messen (Plan ursache, 3 Läufe pro Fall, Stand $(wert stand "$W/aus"))" || { fehler "erste Wahl"; cat "$W/aus"; }
touch "$MW_KIOSK_PAUSE"
python3 "$D" rechnen --paket "$P1" --stunden 1 --ausgabe "$W/r1" > "$W/r1.log" 2>&1 &
RP=$!; PIDS+=("$RP")
O1="$MW_RUNNER_HOME/dauer/pakete/$P1"
O="$O1"
warte 10 mehr_als 4 || fehler "rechnet nicht"
spielen
wait "$RP"
[ "$(wert status "$W/r1")" = gespielt ] && [ "$(wert weiter "$W/r1")" = 0 ] && pause_weg && ok "Spielen: Lauf hört auf (kein Weiterstarten), Bildschirm frei" \
	|| { fehler "rechnen beim Spielen"; cat "$W/r1" "$W/r1.log"; }
N1=$(zeilen "$O1/results.jsonl")
waehle "$K"; [ "$(wert art "$W/aus")" = nichts ] && ok "solange gespielt wird: nichts" || fehler "gewählt trotz Spielen"
ruhig_15min
waehle "$K"; [ "$(wert paket "$W/aus")" = "$P1" ] && grep -q "angefangenes" "$W/aus" && ok "danach: dasselbe Paket wieder ($N1 Fälle gesichert)" || fehler "anderes Paket"
touch "$MW_KIOSK_PAUSE"
python3 "$D" rechnen --paket "$P1" --stunden 1 --ausgabe "$W/r2" > "$W/r2.log" 2>&1
[ "$(wert status "$W/r2")" = fertig ] && [ "$(wert weiter "$W/r2")" = 1 ] && [ "$(zeilen "$O1/results.jsonl")" = 20 ] \
	&& ok "Paket fertig, genau 20 Fälle, nächstes Paket darf starten" || { fehler "zweiter Lauf"; cat "$W/r2" "$W/r2.log"; }
waehle "$K"; [ "$(wert art "$W/aus")" = ki ] && ok "reihum: dann KI-Trainingsbilder" || { fehler "nicht KI"; cat "$W/aus"; }
P2=$(wert paket "$W/aus")
python3 "$D" rechnen --paket "$P2" --stunden 1 --ausgabe "$W/r3" > "$W/r3.log" 2>&1
[ "$(wert status "$W/r3")" = fertig ] && ok "KI-Paket fertig (6 Bildpakete)" || { fehler "KI-Paket"; cat "$W/r3.log"; }
waehle "$K"; [ "$(wert art "$W/aus")" = langzeit ] && ok "reihum: dann Langzeittest" || { fehler "nicht Langzeit"; cat "$W/aus"; }
P3=$(wert paket "$W/aus")
python3 "$D" rechnen --paket "$P3" --stunden 0.0008 --ausgabe "$W/r4" > "$W/r4.log" 2>&1
[ "$(wert status "$W/r4")" = zeit ] && [ "$(wert weiter "$W/r4")" = 1 ] && ok "Zeit um: Stand gesichert, nächster Lauf macht weiter" || { fehler "Zeit"; cat "$W/r4" "$W/r4.log"; }
waehle "$K"; [ "$(wert paket "$W/aus")" = "$P3" ] && ok "angefangener Langzeittest kommt wieder dran" || fehler "Langzeit nicht fortgesetzt"
python3 "$D" rechnen --paket "$P3" --stunden 1 --ausgabe "$W/r5" > "$W/r5.log" 2>&1
[ "$(wert status "$W/r5")" = fertig ] && ok "Langzeittest fertig (180 Min.)" || { fehler "Langzeit"; cat "$W/r5.log"; }
waehle "$K"; [ "$(wert art "$W/aus")" = erkennung ] && [ "$(wert stand "$W/aus")" = v3.53.0 ] && [ "$(wert plan "$W/aus")" = ursache ] \
	&& ok "reihum: Erkennung, jetzt der Vergleichs-Stand" || { fehler "Vergleichs-Stand"; cat "$W/aus"; }
python3 "$D" status > "$W/st.json" && grep -q '"erledigt": 3' "$W/st.json" && ok "Zustand: 3 Pakete erledigt" || { fehler "Zustand"; cat "$W/st.json"; }

echo
if [ $F -eq 0 ]; then echo "Dauerrechnen-Test: OK"; else echo "Dauerrechnen-Test: $F Fehler"; fi
exit $F
