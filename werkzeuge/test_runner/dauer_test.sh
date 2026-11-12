#!/bin/bash
# MoveEye Dauerrechnen - Prüfung ohne HP (CI-Job «HP-Update»; lokal: bash werkzeuge/test_runner/dauer_test.sh). Kein root nötig.
#  1. hp_wache.py: Status-Dienst (rechnet / spielen); eine dauernde Verbindung MoveEye <-> Simulator ohne Zuschauer ist KEIN
#     Spielen (Entscheid Besitzer 03.11.2026); ein Zuschauer-Puls von MoveEye (POST /zuschauer, nur Daten, höchstens 256 Bytes)
#     und die Handy-Seite des Spiels schon -> Spielen-Datei.
#  1b. Controller (Gamepad) = Spielen: Ersatz-Geräte (FIFO statt /dev/input/js0 bzw. event0 mit udev-Eintrag): Taste oder
#     deutlicher Stick-Ausschlag -> Spielen-Datei (auch während gerechnet wird), Rauschen / Startwerte nicht; frischt auf.
#  2. dauer.py halten mit hp_wache.py: Test läuft (MoveEye verbunden, niemand schaut), Zuschauer-Puls -> Test in Sekunden
#     angehalten, Pause-Datei weg (Bildschirm frei), Stand gesichert (nur ganze Fälle); Puls hört auf, 15 Min. später
#     (schnelle Uhr: das Datum der Spielen-Datei wird zurückgestellt) -> Pause wieder da, der Test rechnet genau dort weiter.
#  3. dauer.py waehlen / rechnen: Spielen -> «nichts»; HP-Update fällig -> «nichts»; reihum Erkennung -> KI -> Langzeit;
#     angehaltenes Paket kommt beim nächsten Lauf wieder dran und wird fertig.
#  4. KI-Trainingsbilder mit Ersatz-Simulator: Absturz (Neustart, weiter; fertige Bilder als Teilpaket), langsame Antworten,
#     Dauer-Absturz, Hänger;
#     der Grund steht als ::error:: im Job-Protokoll.
#  5. Erkennung messen: Absturz (Neustart, beim selben Fall weiter, Fall zweimal -> übersprungen, Code 3 mit Grund);
#     Stand ohne MoveEye / Simulator-Paket -> Code 7, sofort abgeschlossen, das nächste Paket kommt dran.
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
export MW_HPU_STEMPEL="$W/letzter_lauf" MW_HPU_WARTET="$W/hpu_wartet" MW_HPU_FASSUNG="$W/hpu_fassung" MW_DAUER_TAKT=0.2
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
echo "--- 1. hp_wache.py (Status, Zuschauer, Spielen-Wunsch)"
python3 -c 'import sys; print(sys.version.split()[0])' >/dev/null || { echo "python3 fehlt"; exit 1; }
PB=$(( 20000 + RANDOM % 20000 ))
SP1=$((PB + 1)) SP2=$((PB + 2)) STP=$((PB + 3))
touch "$MW_KIOSK_PAUSE"
mkdir -p "$W/keine_pads"
python3 -I "$R/simulator3d/beilagen_linux/hp_wache.py" --spiel-datei "$MW_SPIEL" --pause "$MW_KIOSK_PAUSE" --ruhe-s 900 \
	--status-port "$STP" --sim-ports "$SP2" --zuschauer-s 3 --pad-quelle "$W/keine_pads" > "$W/wache.log" 2>&1 &
WP=$!; PIDS+=("$WP")
get() { python3 -c 'import sys, urllib.request
try:
    with urllib.request.urlopen(sys.argv[1], timeout=3) as r: print(r.status, r.read(400).decode("utf-8", "replace"))
except urllib.error.HTTPError as e: print(e.code)
except Exception as e: print("weg", type(e).__name__)' "$1"; }
post() { python3 -c 'import sys, urllib.request
r = urllib.request.Request(sys.argv[1], data=sys.argv[2].encode(), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(r, timeout=3) as x: print(x.status)
except urllib.error.HTTPError as e: print(e.code)
except Exception as e: print("weg", type(e).__name__)' "$1" "$2"; }
zuschauer() { post "http://127.0.0.1:$STP/zuschauer" '{"was": "live"}' | grep -q '^200'; }
status_ist() { get "http://127.0.0.1:$STP/status.json" | grep -q "\"zustand\": \"$1\""; }
handy_lauscht() { get "http://127.0.0.1:$SP2/info" | grep -q '^503'; }
warte 10 status_ist rechnet && ok "Status: rechnet" || { fehler "Status nicht «rechnet»"; cat "$W/wache.log"; }
# MoveEye bleibt dauernd mit dem Simulator verbunden (Pi im Simulator-Betrieb): das allein ist kein Spielen. Ersatz: eine
# Gegenstelle auf einem Simulator-Port, MoveEye hält die Verbindung und fragt ständig Bilder ab.
python3 - "$SP1" > /dev/null 2>&1 <<'EOF2' &
import socket, sys, time
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", int(sys.argv[1]))); s.listen(4)
c, _ = s.accept(); t = time.time() + 30
while time.time() < t:
    try:
        c.settimeout(1); c.recv(100)
    except OSError:
        pass
EOF2
PIDS+=($!); sleep 0.5
python3 - "$SP1" > /dev/null 2>&1 <<'EOF2' &
import socket, sys, time
c = socket.create_connection(("127.0.0.1", int(sys.argv[1])))
for _ in range(25):
    c.sendall(b"GET /frame.jpg HTTP/1.1\r\n\r\n"); time.sleep(0.4)
EOF2
VP=$!; PIDS+=("$VP")
sleep 5
[ ! -e "$MW_SPIEL" ] && status_ist rechnet && ok "MoveEye dauernd mit dem Simulator verbunden, niemand schaut: der HP rechnet weiter" \
	|| fehler "Verbindung ohne Zuschauer hat Spielen ausgelöst"
get "http://127.0.0.1:$STP/zuschauer" | grep -q '^404' && [ ! -e "$MW_SPIEL" ] && ok "GET /zuschauer: abgelehnt (nur POST)" || fehler "GET /zuschauer"
post "http://127.0.0.1:$STP/zuschauer" '{"was": "rm -rf /"}' | grep -q '^404' && [ ! -e "$MW_SPIEL" ] && ok "unbekannter Puls: abgelehnt" || fehler "Puls-Inhalt"
post "http://127.0.0.1:$STP/zuschauer" "{\"was\": \"live\", \"x\": \"$(printf 'x%.0s' {1..400})\"}" | grep -q '^404' && [ ! -e "$MW_SPIEL" ] \
	&& ok "zu grosser Puls (über 256 Bytes): abgelehnt" || fehler "grosser Puls"
zuschauer && warte 5 test -f "$MW_SPIEL" && ok "Zuschauer in MoveEye (Live offen) -> Spielen-Datei" || fehler "Zuschauer ohne Wirkung"
python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); assert d["grund"] == "zuschauer" and d["seit"] > 0' "$MW_SPIEL" \
	&& ok "Spielen-Datei: nur Daten (grund, seit)" || fehler "Inhalt der Spielen-Datei"
warte 5 status_ist spielen && ok "Status: spielen" || fehler "Status nicht «spielen»"
get "http://127.0.0.1:$STP/bild.png" | grep -q '^404' && ok "kein Bild beim Spielen" || fehler "/bild.png"
get "http://127.0.0.1:$STP/../../etc/passwd" | grep -q '^404' && ok "unbekannte Pfade: 404" || fehler "Pfad"
sleep 4; ruhig_15min
warte 5 status_ist rechnet && ok "Puls vorbei, 15 Min. ruhig -> wieder «rechnet»" || fehler "nach 15 Min."
rm -f "$MW_SPIEL"
warte 5 handy_lauscht; warte 5 test -f "$MW_SPIEL" && python3 -c 'import json, sys; assert json.load(open(sys.argv[1]))["grund"] == "handy"' "$MW_SPIEL" \
	&& ok "Handy öffnet die Spiel-Seite -> Spielen" || fehler "Handy-Seite"
rm -f "$MW_SPIEL" "$MW_KIOSK_PAUSE"

# ---------------------------------------------------------------- 1b. Controller = Spielen (Ersatz-Geräte)
echo "--- 1b. hp_wache.py: Controller (Gamepad) zählt als Spielen"
kill "$WP" 2>/dev/null; wait "$WP" 2>/dev/null
mkdir -p "$W/pads" "$W/pads_ev" "$W/udev"
mkfifo "$W/pads/js0" "$W/pads_ev/event0"
exec 7<>"$W/pads/js0" 8<>"$W/pads_ev/event0"         # Schreib-Ende offen halten (wie ein Gerät: nie «zu Ende»)
echo "E:ID_INPUT_JOYSTICK=1" > "$W/udev/c0:0"          # FIFO: Gerätenummer 0:0 -> «udev kennt es als Joystick»
js() { python3 -c 'import struct, sys
a = sys.argv[1:]
sys.stdout.buffer.write(b"".join(struct.pack("IhBB", 0, int(a[i + 1]), int(a[i], 0), int(a[i + 2])) for i in range(0, len(a), 3)))' "$@" >&7; }
ev() { python3 -c 'import struct, sys
a = sys.argv[1:]
sys.stdout.buffer.write(b"".join(struct.pack("llHHi", 0, 0, int(a[i], 0), int(a[i + 1], 0), int(a[i + 2])) for i in range(0, len(a), 3)))' "$@" >&8; }
STP2=$((PB + 4)) SP3=$((PB + 5))
touch "$MW_KIOSK_PAUSE"
python3 -I "$R/simulator3d/beilagen_linux/hp_wache.py" --spiel-datei "$MW_SPIEL" --pause "$MW_KIOSK_PAUSE" --ruhe-s 900 \
	--status-port "$STP2" --sim-ports "$SP3" --pad-quelle "$W/pads" --pad-scan-s 0.3 > "$W/wache_pad.log" 2>&1 &
WP=$!; PIDS+=("$WP")
status2() { get "http://127.0.0.1:$STP2/status.json" | grep -q "\"zustand\": \"$1\""; }
warte 10 status2 rechnet && warte 5 grep -q "Controller js0 erkannt" "$W/wache_pad.log" && ok "Controller erkannt, der HP rechnet" \
	|| { fehler "Controller nicht erkannt"; cat "$W/wache_pad.log"; }
js 0x81 0 0  0x81 0 1  0x82 0 0  0x82 -32767 2               # Startwerte (INIT): Tasten los, Sticks Mitte, Trigger unten
js 2 300 0  2 -200 1  2 500 0                               # Rauschen eines ruhig liegenden Controllers
sleep 4
[ ! -e "$MW_SPIEL" ] && status2 rechnet && ok "Startwerte und Rauschen: kein Spielen" || fehler "Rauschen hat Spielen ausgelöst"
T0=$(date +%s%N)
js 1 1 0  1 0 0                                              # Taste A gedrückt, losgelassen
warte 5 test -f "$MW_SPIEL" && python3 -c 'import json, sys; assert json.load(open(sys.argv[1]))["grund"] == "controller"' "$MW_SPIEL" \
	&& ok "Taste am Controller während des Rechnens -> Spielen nach $(( ($(date +%s%N) - T0) / 1000000 )) ms (grund «controller»)" \
	|| { fehler "Taste ohne Wirkung"; cat "$W/wache_pad.log"; }
warte 5 status2 spielen && ok "Status: spielen" || fehler "Status nicht «spielen»"
touch -d '10 minutes ago' "$MW_SPIEL"
js 2 -30000 0                                                # Stick ganz nach links
sleep 4
[ "$(( $(date +%s) - $(stat -c %Y "$MW_SPIEL") ))" -lt 60 ] && ok "Stick-Ausschlag beim Spielen frischt die Spielen-Datei auf" || fehler "nicht aufgefrischt"
touch -d '10 minutes ago' "$MW_SPIEL"
sleep 4                                                      # der Stick bleibt am Anschlag (keine neuen Ereignisse)
[ "$(( $(date +%s) - $(stat -c %Y "$MW_SPIEL") ))" -lt 60 ] && ok "gehaltener Stick (am Anschlag, ohne neue Ereignisse) zählt weiter als Spielen" || fehler "gehaltener Stick zählt nicht"
js 2 -1000 0                                                 # losgelassen: zurück zur Mitte
sleep 21                                                     # eine Eingabe gilt 20 s
ruhig_15min
warte 6 status2 rechnet && ok "15 Min. ohne Controller -> wieder «rechnet»" || fehler "nach 15 Min."
rm -f "$MW_SPIEL"
js 2 300 0  2 -300 0  2 400 0  2 -200 0                      # Rauschen um die Mitte summiert sich nicht
sleep 4
[ ! -e "$MW_SPIEL" ] && ok "Rauschen um die Ruhelage: kein Spielen" || fehler "Rauschen hat Spielen ausgelöst"
js 2 1500 0  2 3000 0  2 4500 0  2 6000 0  2 7500 0  2 9000 0  2 10500 0  2 12000 0   # langsam geschoben, kleine Schritte
warte 5 test -f "$MW_SPIEL" && ok "Stick langsam geschoben (viele kleine Schritte, wie ein echter Stick) -> Spielen" || fehler "langsamer Stick ohne Wirkung"
# Fenster «Controller koppeln» offen (Marke fenster_offen): Tasten am Controller sind kein Spielen
js 2 0 0
sleep 21
ruhig_15min; warte 6 status2 rechnet; rm -f "$MW_SPIEL"
( for _ in 1 2 3 4 5 6 7 8; do touch "$(dirname "$MW_SPIEL")/fenster_offen"; sleep 1; done ) &
MARKE=$!
sleep 1; js 1 1 0  1 0 0  1 1 1  1 0 1                       # ✕ und ○ gedrückt (Fenster bedienen)
sleep 5
[ ! -e "$MW_SPIEL" ] && ok "Fenster «Controller koppeln» offen: Tasten am Controller sind kein Spielen" || fehler "Bedienen des Fensters hat Spielen ausgelöst"
wait "$MARKE"; rm -f "$(dirname "$MW_SPIEL")/fenster_offen"
sleep 9                                                      # Marke abgelaufen (8 s)
js 1 1 0  1 0 0
warte 5 test -f "$MW_SPIEL" && ok "Fenster zu: die nächste Taste am Controller -> Spielen" || fehler "nach dem Fenster keine Wirkung"
kill "$WP" 2>/dev/null; wait "$WP" 2>/dev/null
rm -f "$MW_SPIEL"
# ohne js*: event-Gerät, das udev als Joystick kennt (nur Tasten / Steuerkreuz)
python3 -I "$R/simulator3d/beilagen_linux/hp_wache.py" --spiel-datei "$MW_SPIEL" --pause "$MW_KIOSK_PAUSE" --ruhe-s 900 \
	--status-port "$STP2" --sim-ports "$SP3" --pad-quelle "$W/pads_ev" --pad-scan-s 0.3 --pad-udev "$W/udev" > "$W/wache_ev.log" 2>&1 &
WP=$!; PIDS+=("$WP")
warte 10 grep -q "Controller event0 erkannt" "$W/wache_ev.log" || { fehler "event-Gerät nicht erkannt"; cat "$W/wache_ev.log"; }
ev 3 0 1200  0 0 0  1 0x110 1                               # Stick (zählt hier nicht), Maustaste BTN_LEFT (kein Controller)
sleep 3
[ ! -e "$MW_SPIEL" ] && ok "event-Gerät: Stick-Werte und Nicht-Controller-Tasten zählen nicht" || fehler "event: falsch ausgelöst"
ev 1 0x130 1  0 0 0                                          # BTN_SOUTH (A) gedrückt
warte 5 test -f "$MW_SPIEL" && ok "event-Gerät (udev: Joystick): Taste -> Spielen" || { fehler "event-Taste ohne Wirkung"; cat "$W/wache_ev.log"; }
kill "$WP" 2>/dev/null; wait "$WP" 2>/dev/null
exec 7>&- 8>&-
rm -f "$MW_SPIEL" "$MW_KIOSK_PAUSE"
# die Wache von Teil 1 wieder (Teil 2 schickt ihr Zuschauer-Pulse)
python3 -I "$R/simulator3d/beilagen_linux/hp_wache.py" --spiel-datei "$MW_SPIEL" --pause "$MW_KIOSK_PAUSE" --ruhe-s 900 \
	--status-port "$STP" --sim-ports "$SP2" --zuschauer-s 3 --pad-quelle "$W/keine_pads" >> "$W/wache.log" 2>&1 &
WP=$!; PIDS+=("$WP")
warte 10 status_ist frei || fehler "Wache startet nicht wieder"

# ---------------------------------------------------------------- 2. halten: Zuschauer -> Pause + Sicherung -> 15 Min. -> weiter
echo "--- 2. dauer.py halten (Zuschauer hält an, Stand gesichert, ohne Puls nach 15 Min. weiter)"
O="$W/erk"
touch "$MW_KIOSK_PAUSE"
python3 "$D" halten --warten-max 120 -- python3 "$W/ersatz.py" --aus "$O" --faelle 20 > "$W/halten.log" 2>&1 &
HP=$!; PIDS+=("$HP")
mehr_als() { [ "$(zeilen "$O/results.jsonl")" -ge "$1" ]; }
warte 10 mehr_als 5 && ok "Test rechnet (5 Fälle), MoveEye-Verbindung ohne Zuschauer stört nicht" || fehler "Test rechnet nicht"
[ ! -e "$MW_SPIEL" ] || fehler "Spielen ohne Zuschauer"
T0=$(date +%s%N)
zuschauer
warte 5 pause_weg && ok "Zuschauer-Puls -> Pause-Datei weg nach $(( ($(date +%s%N) - T0) / 1000000 )) ms (Bildschirm frei)" || fehler "Pause bleibt"
N1=$(zeilen "$O/results.jsonl")
for _ in 1 2 3; do zuschauer; sleep 0.6; done              # schaut weiter zu
N2=$(zeilen "$O/results.jsonl")
[ "$N1" = "$N2" ] && [ "$N1" -ge 5 ] && [ "$N1" -lt 20 ] && ok "Test angehalten, Stand gesichert: $N1 von 20 Fällen" || fehler "Test läuft weiter ($N1 -> $N2)"
pgrep -f "^python3 $W/ersatz.py" >/dev/null && fehler "Ersatz-Test läuft noch" || ok "Test-Prozess beendet (Simulator / MoveEye wären zu)"
kill -0 "$HP" 2>/dev/null && ok "Job wartet (es wird zugeschaut)" || fehler "Job beendet statt zu warten"
pause_weg && ok "Pause bleibt weg, solange zugeschaut wird" || fehler "Pause zu früh zurück"
sleep 4                                                    # Puls hört auf (Zuschauer-Zeit im Test 3 s) ...
ruhig_15min                                                # ... und 15 Min. vergehen (schnelle Uhr)
warte 10 pause_da && ok "kein Puls mehr, 15 Min. später -> Pause wieder da (Kiosk-Simulator aus)" || fehler "Pause nicht zurück"
warte 20 mehr_als 20 && ok "weitergerechnet bis 20 Fälle" || fehler "nicht fertig ($(zeilen "$O/results.jsonl"))"
wait "$HP"; rc=$?
[ "$rc" = 0 ] && ok "halten: Exit 0" || fehler "halten: Exit $rc"
dopp=$(python3 -c 'import json, sys; k = [json.loads(l)["key"] for l in open(sys.argv[1])]; print(len(k) - len(set(k)), len(set(k)))' "$O/results.jsonl")
[ "$dopp" = "0 20" ] && ok "kein Fall doppelt, keiner fehlt" || fehler "Fälle: doppelt/eindeutig = $dopp"
grep -q "weiter, wo es stand" "$W/halten.log" && ok "Protokoll: weiter, wo es stand" || fehler "Protokoll"
kill "$WP" 2>/dev/null; wait "$WP" 2>/dev/null
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
echo "9.0.0 9.0.0" > "$MW_HPU_WARTET"
waehle "$K"; [ "$(wert art "$W/aus")" = nichts ] && grep -q Update "$W/aus" && ok "neues HP-Update wartet (Marke): kein neues Paket, HP bleibt frei" || fehler "Marke «wartet» nicht beachtet"
touch -d '9 hours ago' "$MW_HPU_WARTET"
waehle "$K"; [ "$(wert art "$W/aus")" != nichts ] && ok "alte Marke «wartet» (über 8 Std.) hält nicht mehr auf" || fehler "alte Marke hält auf"
rm -f "$MW_HPU_WARTET"; : > "$W/aus"
echo 5 > "$MW_HPU_FASSUNG"; touch -d '7 hours ago' "$MW_HPU_STEMPEL"
waehle "$K"; [ "$(wert art "$W/aus")" = nichts ] && grep -q Update "$W/aus" && ok "altes HP-Update (Fassung 5, über 6 Std.): HP bleibt frei" || fehler "Übergang Fassung 5"
echo 6 > "$MW_HPU_FASSUNG"
waehle "$K"; [ "$(wert art "$W/aus")" != nichts ] && ok "neue Fassung 6: rechnet weiter" || fehler "Fassung 6 hält auf"
touch "$MW_HPU_STEMPEL"; rm -f "$MW_HPU_FASSUNG"; : > "$W/aus"
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

# ---------------------------------------------------------------- 4. KI-Trainingsbilder mit Ersatz-Simulator
# Der echte Fehler am HP (03.11.2026, «Code 1» dreimal): unter Xvfb (ohne Grafikkarte) stürzt der Simulator beim Export
# (Vielfalt hoch) nach einigen Minuten ab (SIGSEGV) bzw. antwortet beim Szenenwechsel über 20 s nicht - ki-teil starb an der
# ersten Zeitüberschreitung, ohne Grund im Job-Protokoll. Ersatz-Simulator (HTTP /control wie der echte) mit den Fällen: stürzt einmal ab, antwortet
# langsam, stürzt immer ab, hängt.
echo "--- 4. KI-Trainingsbilder: Absturz, langsame Antworten, Hänger, klare Meldung"
unset MW_DAUER_ERSATZ
cat > "$W/ersatz_sim.py" <<'EOF'
#!/usr/bin/env python3
import json, os, signal, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
arg = sys.argv[1:]
port = int(arg[arg.index("--port") + 1])
grafik = arg[arg.index("--grafik") + 1] if "--grafik" in arg else "?"
modus = os.environ.get("ERSATZ_SIM_MODUS", "")
zf = os.environ["ERSATZ_SIM_ZAEHLER"]
start = (int(open(zf).read()) if os.path.exists(zf) else 0) + 1
open(zf, "w").write(str(start))
with open(os.environ["ERSATZ_SIM_PROTOKOLL"], "a") as f:
    f.write("start %d grafik %s\n" % (start, grafik))
print("Ersatz-Simulator Start %d, Grafik %s, Modus %s" % (start, grafik, modus), flush=True)
z = {"busy": False, "bis": 0.0, "gets": 0}
lock = threading.Lock()
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        out = {"ok": True}
        if d.get("action") == "dataset":
            with lock:
                if d.get("op") == "export":
                    z.update(busy=True, bis=time.time() + 0.6)
                    out = {"ok": True, "busy": True, "msg": "Paket: Bild 1 von %s" % d.get("n")}
                else:
                    z["gets"] += 1
                    g = z["gets"]
                    if modus == "teil" and start == 1:      # 6 Bilder fertig, das 7. nur halb - dann Absturz
                        e = os.path.join(os.environ["HOME"], ".local/share/godot/app_userdata/MoveEye Sim/trainingsbilder/20261103_1200_hoch")
                        for i in range(7):
                            t = "val" if i % 7 == 6 else "train"
                            for u in ("images", "labels", "labels_meta"):
                                os.makedirs(os.path.join(e, u, t), exist_ok=True)
                            open(os.path.join(e, "images", t, "%05d_wald_tag.jpg" % i), "wb").write(b"\xff\xd8" + os.urandom(500))
                            if i < 6:
                                open(os.path.join(e, "labels", t, "%05d_wald_tag.txt" % i), "w").write("0 0.5 0.5 0.1 0.3\n")
                                open(os.path.join(e, "labels_meta", t, "%05d_wald_tag.json" % i), "w").write("{}")
                    if modus == "immer" or (modus in ("absturz1", "teil") and start == 1):
                        print("Speicherzugriffsfehler (nachgestellt)", flush=True)
                        os.kill(os.getpid(), signal.SIGSEGV)
                    if modus == "haengt" or (modus == "langsam" and g <= 2):
                        time.sleep(100 if modus == "haengt" else 2.5)   # länger als MW_KI_ANTWORT_S
                    if z["busy"] and time.time() > z["bis"]:
                        d0 = os.path.join(os.environ["HOME"], ".local/share/godot/app_userdata/MoveEye Sim")
                        os.makedirs(d0, exist_ok=True)
                        with open(os.path.join(d0, "MoveEye-Trainingsbilder_%d.zip" % int(time.time() * 1000)), "wb") as f:
                            f.write(b"PK" + os.urandom(2048))
                        z["busy"] = False
                    out = {"ok": True, "busy": z["busy"], "msg": "fertig" if not z["busy"] else "Paket: Bild 7 von 150"}
        b = json.dumps(out).encode()
        try:
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        except OSError:
            pass
    def do_GET(self):
        self.send_response(404); self.end_headers()
ThreadingHTTPServer.daemon_threads = True
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
EOF
chmod +x "$W/ersatz_sim.py"
export ERSATZ_SIM_PROTOKOLL="$W/sim_starts.log" ERSATZ_SIM_ZAEHLER="$W/sim_zaehler" MW_KI_PORT=$(( 40000 + RANDOM % 20000 ))
ki() {   # ki MODUS MENGE AUSGABE [ENV=…]: ki-teil mit dem Ersatz-Simulator, ohne Bildschirm -> Exit-Code
	local m=$1 n=$2 aus=$3; shift 3
	rm -f "$ERSATZ_SIM_PROTOKOLL" "$ERSATZ_SIM_ZAEHLER"
	env ERSATZ_SIM_MODUS="$m" MW_KI_ANTWORT_S=1 MW_KI_STILL_S=6 "$@" python3 "$D" ki-teil --repo "$R" --sim-bin "$W/ersatz_sim.py" --aus "$aus" \
		--anzeige keine --menge "$n" --stand-name main > "$aus.log" 2>&1
}
ki absturz1 2 "$W/ki1" MW_KI_GRAFIK=lite; rc=$?
[ "$rc" = 0 ] && [ -s "$W/ki1/pakete/ki_01.zip" ] && [ -s "$W/ki1/pakete/ki_02.zip" ] && [ -s "$W/ki1/simulator_absturz_1.log" ] \
	&& grep -q "SIGSEGV" "$W/ki1.log" && ok "Simulator stürzt ab (SIGSEGV): Protokoll gesichert, Neustart, beide Bildpakete fertig" \
	|| { fehler "Absturz nicht überstanden (Exit $rc)"; cat "$W/ki1.log"; }
[ "$(grep -c '^start .* grafik lite' "$ERSATZ_SIM_PROTOKOLL")" = 2 ] && ok "MW_KI_GRAFIK=lite gilt auch nach dem Neustart" \
	|| { fehler "Grafik"; cat "$ERSATZ_SIM_PROTOKOLL"; }
ki teil 2 "$W/ki5" MW_KI_TEIL_MIN=5; rc=$?
[ "$rc" = 0 ] && [ "$(grep -c '^start' "$ERSATZ_SIM_PROTOKOLL")" = 2 ] && python3 -c 'import sys, zipfile
z = zipfile.ZipFile(sys.argv[1]); n = z.namelist()
assert sum(x.endswith(".jpg") for x in n) == 6 and sum(x.startswith("labels/") for x in n) == 6 and "data.yaml" in n, n
y = z.read([x for x in n if x.endswith("data.yaml")][0]).decode()
assert "names:" in y and "  0: person" in y and "Teilpaket" in y' "$W/ki5/pakete/ki_01.zip" && [ -s "$W/ki5/pakete/ki_02.zip" ] \
	&& ok "Absturz mitten im Bildpaket: 6 fertige Bilder als Teilpaket gesichert (data.yaml aus dataset.gd), weiter mit Paket 2" \
	|| { fehler "Teilpaket (Exit $rc)"; cat "$W/ki5.log"; }
ki langsam 1 "$W/ki2"; rc=$?
[ "$rc" = 0 ] && [ -s "$W/ki2/pakete/ki_01.zip" ] && ok "langsame Antworten (Szenenwechsel unter Xvfb): kein Abbruch" \
	|| { fehler "langsame Antworten (Exit $rc)"; cat "$W/ki2.log"; }
ki immer 2 "$W/ki3"; rc=$?
[ "$rc" = 4 ] && grep -q "abgestürzt" "$W/ki3/fehler.txt" && grep -q "SIGSEGV" "$W/ki3/fehler.txt" && [ "$(grep -c '^start' "$ERSATZ_SIM_PROTOKOLL")" = 3 ] \
	&& ok "stürzt immer ab: Exit 4 nach 2 Neustarts, Grund in fehler.txt ($(head -c 70 "$W/ki3/fehler.txt") …)" \
	|| { fehler "Dauer-Absturz (Exit $rc)"; cat "$W/ki3.log"; }
ki haengt 1 "$W/ki4"; rc=$?
[ "$rc" = 5 ] && grep -q "hängt" "$W/ki4/fehler.txt" && ok "hängt: Exit 5, Grund in fehler.txt" || { fehler "Hänger (Exit $rc)"; cat "$W/ki4.log"; }
pgrep -f "$W/ersatz_sim.py" >/dev/null && fehler "Ersatz-Simulator läuft noch" || ok "kein Simulator bleibt übrig"
# ganze Kette wie am HP: waehlen -> rechnen; der Grund steht im Job-Protokoll (::error::), nicht nur «Code 1»
export MW_RUNNER_HOME="$W/home4"
mkdir -p "$MW_RUNNER_HOME"
waehle "$K" >/dev/null; : > "$W/aus"
python3 "$D" waehlen --kandidaten "$K" --arbeit ki --ausgabe "$W/aus" > /dev/null 2>&1
P4=$(wert paket "$W/aus")
rm -f "$ERSATZ_SIM_ZAEHLER"
ERSATZ_SIM_MODUS=immer MW_KI_ANTWORT_S=1 python3 "$D" rechnen --paket "$P4" --stand "$R" --sim-bin "$W/ersatz_sim.py" --anzeige keine \
	--stunden 1 --ausgabe "$W/r6" > "$W/r6.log" 2>&1
grep -q '^::error title=Dauerrechnen KI-Trainingsbilder::Simulator 3-mal abgestürzt' "$W/r6.log" && grep -q "Versuch 1): Simulator" "$W/r6.log" \
	&& grep -q "::group::Ende von dauer.log" "$W/r6.log" && [ "$(wert weiter "$W/r6")" = 0 ] \
	&& ok "rechnen: Grund als ::error:: im Job-Protokoll, Ende von dauer.log dabei, kein Sofort-Neustart" \
	|| { fehler "Meldung im Job-Protokoll"; cat "$W/r6.log"; }
python3 "$D" status > "$W/st4.json" 2>&1; grep -q '"versuche": 1' "$W/st4.json" && ok "Paket bleibt angefangen (Versuch 1 von 3)" || fehler "Versuche"

# ---------------------------------------------------------------- 5. Erkennung messen: Absturz, Stand nicht brauchbar
# Der echte Fehler am HP (03.11.2026, «Code 3» dreimal für main, dann für v3.54.0): Simulator oder MoveEye beendete sich
# mitten im Plan, erkennungstest.py gab nach dem Schritt sofort Code 3 zurück, ohne zu sagen, wer und warum; jeder neue
# Versuch scheiterte nach rund 2 Min. wieder. Jetzt: Protokoll sichern, neu starten, beim selben Fall weiter; derselbe Fall
# zweimal -> übersprungen; Stand ohne MoveEye / Simulator -> Code 7, sofort abgeschlossen (nicht dreimal).
echo "--- 5. Erkennung messen: Absturz überstehen, Fall überspringen, unbrauchbaren Stand nicht wiederholen"
python3 - "$R/werkzeuge/erkennungstest" "$W/erk5" > "$W/erk5.log" 2>&1 <<'EOF'
import os, sys
sys.path.insert(0, sys.argv[1])
import erkennungstest as E, faelle as F
out = sys.argv[2]
def lauf(name, faelle, absturz, neustart_ok=True):
    o = os.path.join(out, name); os.makedirs(o, exist_ok=True); F.K["out"] = o
    st = {"tot": False, "neustarts": 0}
    def schritt(s):
        done = F.done_keys()
        for k in faelle:
            if k in done:
                continue
            F.ST["fall"] = k
            if absturz(k, st):
                st["tot"] = True                       # wie am HP: Simulator weg, die nächste Anfrage scheitert
                raise ConnectionRefusedError("Simulator weg")
            F.save({"key": k})
    tote = lambda: [("Simulator", "Code -11 = Speicherzugriffsfehler (SIGSEGV)")] if st["tot"] else []
    def neustart(t, n):
        st["neustarts"] += 1; st["tot"] = False
        return "" if neustart_ok else "nicht wieder verbunden"
    rc, grund, fe = E.plan_rechnen([("orte", "x", {})], schritt, tote, neustart, log=lambda *a: None)
    return rc, grund, st["neustarts"], sorted(F.done_keys()), [u["key"] for u in F.uebersprungene()]
K = ["a", "b", "c", "d"]
r = lauf("einmal", K, lambda k, st: k == "b" and st["neustarts"] == 0)
assert r[:3] == (0, "", 1) and r[3] == K and r[4] == [], r
r = lauf("immer_c", K, lambda k, st: k == "c")
assert r[0] == 0 and r[2] == 2 and r[3] == K and r[4] == ["c"], r
r = lauf("alles", ["f%02d" % i for i in range(20)], lambda k, st: True)
assert r[0] == 3 and "8-mal abgestürzt" in r[1] and "SIGSEGV" in r[1] and r[2] == 7, r
r = lauf("neustart", K, lambda k, st: k == "a", neustart_ok=False)
assert r[0] == 3 and "gescheitert" in r[1] and "beim Fall a" in r[1], r
EOF
rc=$?
[ "$rc" = 0 ] && ok "Absturz: Neustart, beim selben Fall weiter; zweimal beim selben Fall -> übersprungen; 8 Abstürze / Neustart gescheitert -> Code 3 mit Grund" \
	|| { fehler "plan_rechnen (Exit $rc)"; cat "$W/erk5.log"; }
# ganze Kette: ein Stand ohne MoveEye-Datei (bzw. ohne Simulator-Paket) -> Code 7, Paket sofort abgeschlossen, das nächste kommt dran
export MW_RUNNER_HOME="$W/home5"
mkdir -p "$MW_RUNNER_HOME" "$W/leerer_stand"
erk_paket() { : > "$W/aus"; python3 "$D" waehlen --kandidaten "$K" --arbeit erkennung --ausgabe "$W/aus" > /dev/null 2>&1; wert paket "$W/aus"; }
P5=$(erk_paket)
python3 "$D" rechnen --paket "$P5" --stand "$W/leerer_stand" --sim-bin "$W/ersatz_sim.py" --anzeige keine --stunden 1 \
	--ausgabe "$W/r7" > "$W/r7.log" 2>&1
grep -q '^::error title=Dauerrechnen Erkennung messen::Stand main nicht brauchbar: MoveEye (webcam_bewegung_X_Y_Z.py) fehlt' "$W/r7.log" \
	&& grep -q "(Code 7)" "$W/r7.log" && grep -q "kein weiterer Versuch" "$W/r7.log" && [ "$(wert weiter "$W/r7")" = 1 ] \
	&& ok "Stand ohne MoveEye: Code 7 mit klarem Grund, kein zweiter Versuch, nächstes Paket darf gleich starten" \
	|| { fehler "Stand ohne MoveEye"; cat "$W/r7.log" "$W/r7"; }
sleep 1   # Paket-IDs sind sekundengenau
P6=$(erk_paket)
[ -n "$P6" ] && [ "$P6" != "$P5" ] && [ "$(wert stand "$W/aus")" = v3.53.0 ] && ok "danach: der nächste Stand (v3.53.0), nicht noch einmal main" \
	|| { fehler "nach übersprungenem Stand"; cat "$W/aus"; }
python3 "$D" rechnen --paket "$P6" --stand "$R" --sim-bin "" --anzeige keine --stunden 1 --ausgabe "$W/r8" > "$W/r8.log" 2>&1
grep -q '::error title=Dauerrechnen Erkennung messen::Stand v3.53.0 (bbbbbbbbbb) nicht brauchbar: Simulator fehlt' "$W/r8.log" \
	&& python3 "$D" status > "$W/st5.json" 2>&1 && grep -q '"aktiv": null' "$W/st5.json" && ok "Stand ohne Simulator-Paket: ohne Start übersprungen, Grund im Job-Protokoll" \
	|| { fehler "Stand ohne Simulator"; cat "$W/r8.log"; }
python3 -c 'import json, sys; z = json.load(open(sys.argv[1]))["erledigt"]
assert sum(1 for e in z.values() if e["status"].startswith("übersprungen: Stand nicht brauchbar")) == 2, z' \
	"$MW_RUNNER_HOME/dauer/zustand.json" && ok "Zustand: beide als «übersprungen: Stand nicht brauchbar» erledigt" || fehler "Zustand nach Code 7"

# ---------------------------------------------------------------- 6. Varianten (Paket «Fehlalarme und Pushes»)
# Sind alle Stände mit allen Plänen gemessen, misst das Dauerrechnen main zusätzlich mit jeder Variante (z. B. doppelte
# Bestätigung an) und schreibt varianten.md (Erkennung und Pushes/h nebeneinander, gegen dieselbe Messung ohne Variante).
echo "--- 6. Varianten: nach allen Ständen main mit der Variante, Bericht nebeneinander"
MW_DAUER="$W/dauer6" python3 - "$R/werkzeuge/test_runner" "$R/werkzeuge/erkennungstest" > "$W/var6.log" 2>&1 <<'EOF6'
import json, os, sys, time
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import dauer as D, bericht as B
kand = D.kandidaten_lesen(json.dumps({"main": {"name": "main", "sha": "a" * 40}, "vorher": {"name": "v1", "sha": "b" * 40}}))
z = {"erledigt": {}}
for plan in D.ERK_PLAENE:
    for k in kand:
        z["erledigt"][D.erk_key(k["sha"], plan)] = {"t": 1, "status": "fertig", "paket": "20261107-100000-erkennung"}
n = D.naechstes(z, kand, "erkennung", time.time())
assert n and n["sha"] == "a" * 40 and n.get("variante") == "bestaetigung2" and n["plan"] == D.ERK_VAR_PLAENE[0], n
assert D.erk_key(n["sha"], n["plan"], n["variante"]) == "erkennung|%s|%s@bestaetigung2" % ("a" * 40, n["plan"])
assert D.naechstes(z, kand, "erkennung", time.time(), ()) is None, "--varianten keine: nichts mehr"
for plan in D.ERK_VAR_PLAENE:
    z["erledigt"][D.erk_key("a" * 40, plan, "bestaetigung2")] = {"t": 2, "status": "fertig", "paket": "x"}
# Flora Paket 4 B: danach die Tier-Varianten, Runde für Runde abwechselnd Grundformen / Modelle (Pläne tier, nacht)
n = D.naechstes(z, kand, "erkennung", time.time())
assert n and n["variante"] == "tiere_grundformen" and n["plan"] == "tier" and n["runde"] == 1 and n["laeufe"] == 1, n
folge = []
for i in range(4 * D.TIERE_RUNDEN):
    n = D.naechstes(z, kand, "erkennung", time.time())
    if n is None:
        break
    k = D.erk_key(n["sha"], n["plan"], n["variante"], n["runde"])
    assert k not in z["erledigt"], k
    folge.append((n["runde"], n["variante"], n["plan"]))
    z["erledigt"][k] = {"t": 3, "status": "fertig", "paket": "20261108-0%05d-erkennung" % i, "stand": "main"}
assert len(folge) == 4 * D.TIERE_RUNDEN, len(folge)
assert folge[:4] == [(1, "tiere_grundformen", "tier"), (1, "tiere_grundformen", "nacht"), (1, "tiere_modelle", "tier"), (1, "tiere_modelle", "nacht")], folge[:4]
assert folge[4][0] == 2 and D.erk_key("a" * 40, "tier", "tiere_modelle", 2).endswith("tier@tiere_modelle#2")
assert D.naechstes(z, kand, "erkennung", time.time()) is None, "alles gemessen"
# tiere.md: alle Pakete der Tier-Varianten zusammen
def tfall(key, art, det, pers):
    return {"key": key, "event": "tier", "animal": art, "detected": det, "false_person": pers, "cond": "tag", "fps": 4.0, "pushes": []}
for i, (r, v, plan) in enumerate(folge[:4]):
    os.makedirs(os.path.join(D.DAUER, "pakete", "20261108-0%05d-erkennung" % i), exist_ok=True)
    R = [tfall("t1", "deer", v == "tiere_modelle", False), tfall("t2", "dog", False, v == "tiere_grundformen")]
    with open(os.path.join(D.DAUER, "pakete", "20261108-0%05d-erkennung" % i, "results.jsonl"), "w") as f:
        f.write("".join(json.dumps(x) + "\n" for x in R))
ak4 = {"id": "20261108-000003-erkennung", "sha": "a" * 40, "stand": "main", "plan": "nacht", "laeufe": 1, "variante": "tiere_modelle", "runde": 1}
D.erk_vergleich(z, ak4)
md = open(os.path.join(D.DAUER, "tiere.md"), encoding="utf-8").read()
assert "| **alle** | 0 % Tier · 50 % Person (4) | 50 % Tier · 0 % Person (4) |" in md, md
assert "| deer | 0 % Tier · 0 % Person (2) | 100 % Tier · 0 % Person (2) |" in md, md
# Bericht nebeneinander: weniger Pushes, eine Person weniger erkannt
def fall(key, ev, det, pushes, secs=60):
    return {"key": key, "event": ev, "detected": det, "pushes": [[p, 5] for p in pushes], "secs": secs, "place": "camping", "cond": "tag"}
std = [fall("a", "gehen", True, ["person"]), fall("b", "kind", True, ["person"]), fall("c", "leer", False, ["person", "prealarm"])]
var = [fall("a", "gehen", True, ["person"]), fall("b", "kind", False, []), fall("c", "leer", False, [])]
os.makedirs(os.path.join(D.DAUER, "pakete", "20261107-100000-erkennung"), exist_ok=True)
os.makedirs(os.path.join(D.DAUER, "pakete", "20261107-110000-erkennung"), exist_ok=True)
for pid, R in (("20261107-100000-erkennung", std), ("20261107-110000-erkennung", var)):
    with open(os.path.join(D.DAUER, "pakete", pid, "results.jsonl"), "w") as f:
        f.write("".join(json.dumps(r) + "\n" for r in R))
ak = {"id": "20261107-110000-erkennung", "sha": "a" * 40, "stand": "main", "plan": D.ERK_PLAENE[0], "laeufe": 3, "variante": "bestaetigung2"}
D.erk_vergleich(z, ak)
md = open(os.path.join(D.DAUER, "pakete", ak["id"], "varianten.md"), encoding="utf-8").read()
assert "| Kennzahl | standard | bestaetigung2 |" in md and "Pushes pro Stunde" in md and "2/2 (100 %) | 1/2 (50 %)" in md, md
assert "Personen erkannt -50 Prozentpunkte, Pushes/h 80.0 → 20.0, falsche Pushes/h 120.0 → 0.0" in md, md
print("ok")
EOF6
rc=$?
[ "$rc" = 0 ] && ok "Varianten: nach allen Ständen main mit doppelter Bestätigung, «keine» schaltet ab, varianten.md mit Erkennung und Pushes/h; Tier-Varianten Runde für Runde, tiere.md" \
	|| { fehler "Varianten (Exit $rc)"; cat "$W/var6.log"; }

# 6b. Nur bestimmte Varianten (dauer_hp.yml «varianten», z. B. die Tier-Stichprobe tagsüber): ohne die Grundpläne der Stände
echo "--- 6b. --varianten … --nur-varianten: gleich die Tier-Varianten; ohne Angabe wie bisher"
MW_DAUER="$W/dauer6b" python3 - "$R/werkzeuge/test_runner" "$R/werkzeuge/erkennungstest" > "$W/var6b.log" 2>&1 <<'EOF6B'
import json, sys, time
sys.path.insert(0, sys.argv[1])
import dauer as D
kand = D.kandidaten_lesen(json.dumps({"main": {"name": "main", "sha": "a" * 40}, "vorher": {"name": "v1", "sha": "b" * 40}}))
z = {"erledigt": {}}
n = D.naechstes(z, kand, "erkennung", time.time())
assert n["plan"] == D.ERK_PLAENE[0] and not n.get("variante"), ("ohne Angabe: Grundplan zuerst", n)
n = D.naechstes(z, kand, "erkennung", time.time(), D.TIERE_VAR)
assert n["plan"] == D.ERK_PLAENE[0] and not n.get("variante"), ("--varianten ohne --nur-varianten: wie bisher", n)
n = D.naechstes(z, kand, "erkennung", time.time(), (), True)
assert n["plan"] == D.ERK_PLAENE[0] and not n.get("variante"), ("«keine» mit --nur-varianten: wirkungslos", n)
n = D.naechstes(z, kand, "erkennung", time.time(), D.TIERE_VAR, True)
assert n["variante"] == "tiere_grundformen" and n["plan"] == "tier" and n["runde"] == 1 and n["sha"] == "a" * 40, n
n = D.naechstes(z, kand, "erkennung", time.time(), ("bestaetigung2",), True)
assert n["variante"] == "bestaetigung2" and n["sha"] == "a" * 40, n
# neuer main-Stand: die Tier-Runden zählen weiter (über Stände der letzten 14 Tage), Grundpläne / bestaetigung2 pro Stand
jetzt = time.time()
for plan in ("tier", "nacht"):
    z["erledigt"][D.erk_key("a" * 40, plan, "tiere_grundformen")] = {"t": int(jetzt) - 3600, "status": "fertig", "paket": "x"}
z["erledigt"][D.erk_key("a" * 40, D.ERK_VAR_PLAENE[0], "bestaetigung2")] = {"t": int(jetzt) - 3600, "status": "fertig", "paket": "x"}
kand2 = D.kandidaten_lesen(json.dumps({"main": {"name": "main", "sha": "c" * 40}, "vorher": {"name": "v1", "sha": "b" * 40}}))
n = D.naechstes(z, kand2, "erkennung", jetzt, D.TIERE_VAR, True)
assert n["sha"] == "c" * 40 and n["variante"] == "tiere_modelle" and n["plan"] == "tier" and n["runde"] == 1, ("neuer Stand: weiter bei Modelle", n)
n = D.naechstes(z, kand2, "erkennung", jetzt, ("bestaetigung2",), True)
assert n["sha"] == "c" * 40 and n["variante"] == "bestaetigung2" and n["plan"] == D.ERK_VAR_PLAENE[0], ("bestaetigung2 pro Stand", n)
n = D.naechstes(z, kand2, "erkennung", jetzt)
assert n["sha"] == "c" * 40 and n["plan"] == D.ERK_PLAENE[0] and not n.get("variante"), ("Grundplan pro Stand", n)
for k in list(z["erledigt"]):
    if "tiere_grundformen" in k:
        z["erledigt"][k]["t"] = int(jetzt) - 15 * 86400
n = D.naechstes(z, kand2, "erkennung", jetzt, D.TIERE_VAR, True)
assert n["variante"] == "tiere_grundformen" and n["runde"] == 1, ("älter als 14 Tage: zählt nicht mehr", n)
# Aufräumen: alte Tier-Pakete behalten results.jsonl (tiere.md zählt sie weiter), andere alte Pakete gehen wie bisher
import os
sys.path.insert(0, sys.argv[2])
pk = os.path.join(D.DAUER, "pakete")
zt = {"erledigt": {}}
tier_alt, norm_alt, tier_uralt = "20261101-000001-erkennung", "20261101-000002-erkennung", "20261101-000003-erkennung"
zt["erledigt"][D.erk_key("d" * 40, "tier", "tiere_grundformen")] = {"t": int(jetzt) - 86400, "status": "fertig", "paket": tier_alt, "stand": "main"}
zt["erledigt"][D.erk_key("d" * 40, "ursache")] = {"t": int(jetzt) - 86400, "status": "fertig", "paket": norm_alt, "stand": "main"}
zt["erledigt"][D.erk_key("e" * 40, "tier", "tiere_modelle")] = {"t": int(jetzt) - 15 * 86400, "status": "fertig", "paket": tier_uralt, "stand": "main"}
fall = lambda key: {"key": key, "event": "tier", "animal": "deer", "detected": False, "false_person": True, "cond": "nacht", "fps": 4.0, "pushes": []}
for n in [tier_alt, norm_alt, tier_uralt] + ["20261108-1000%02d-erkennung" % i for i in range(D.BEHALTEN)]:
    os.makedirs(os.path.join(pk, n, "protokolle"), exist_ok=True)
    with open(os.path.join(pk, n, "results.jsonl"), "w") as f:
        f.write(json.dumps(fall("t1")) + "\n" + json.dumps(fall("t2")) + "\n")
    open(os.path.join(pk, n, "simulator.log"), "w").write("x" * 1000)
    open(os.path.join(pk, n, "protokolle", "a.log"), "w").write("x")
D.aufraeumen(zt)
assert sorted(os.listdir(os.path.join(pk, tier_alt))) == ["results.jsonl"], ("Tier-Paket: nur results.jsonl", os.listdir(os.path.join(pk, tier_alt)))
assert not os.path.exists(os.path.join(pk, norm_alt)), "anderes altes Paket: gelöscht wie bisher"
assert not os.path.exists(os.path.join(pk, tier_uralt)), "Tier-Paket älter als 14 Tage: gelöscht"
assert len([n for n in os.listdir(pk) if n.startswith("20261108-1000")]) == D.BEHALTEN, "die letzten BEHALTEN bleiben ganz"
assert os.path.exists(os.path.join(pk, "20261108-100000-erkennung", "simulator.log")), "neue Pakete unverändert"
o = os.path.join(D.DAUER, "out6b"); os.makedirs(o, exist_ok=True)
D.tiere_bericht(zt, o)
md = open(os.path.join(o, "tiere.md"), encoding="utf-8").read()
assert "grundformen (2 Fälle)" in md, md
EOF6B
rc=$?
[ "$rc" = 0 ] && ok "naechstes: nur_varianten lässt die Grundpläne aus, ohne Angabe unverändert; Tier-Runden zählen über main-Stände (14 Tage); alte Tier-Pakete behalten results.jsonl" || { fehler "nur-varianten (Exit $rc)"; cat "$W/var6b.log"; }
: > "$W/aus6b"
MW_DAUER="$W/dauer6b_cli" python3 "$D" waehlen --kandidaten "$K" --arbeit erkennung --varianten tiere_grundformen,tiere_modelle --nur-varianten \
	--ausgabe "$W/aus6b" > "$W/w6b.log" 2>&1
[ "$(wert variante "$W/aus6b")" = tiere_grundformen ] && [ "$(wert plan "$W/aus6b")" = tier ] && ok "waehlen --varianten tiere_… --nur-varianten: Paket tier@tiere_grundformen" \
	|| { fehler "waehlen --nur-varianten: $(tr '\n' ' ' < "$W/aus6b")"; cat "$W/w6b.log"; }
: > "$W/aus6b"
MW_DAUER="$W/dauer6b_cli2" python3 "$D" waehlen --kandidaten "$K" --arbeit erkennung --ausgabe "$W/aus6b" > "$W/w6b.log" 2>&1
[ "$(wert variante "$W/aus6b")" = standard ] && [ "$(wert plan "$W/aus6b")" = ursache ] \
	&& ok "waehlen ohne --varianten: Grundplan «ursache» wie bisher" || { fehler "waehlen ohne Angabe: $(tr '\n' ' ' < "$W/aus6b")"; cat "$W/w6b.log"; }

echo
if [ $F -eq 0 ]; then echo "Dauerrechnen-Test: OK"; else echo "Dauerrechnen-Test: $F Fehler"; fi
exit $F
