#!/bin/bash
# Prüfung «Hoch-Schutz» (grafik_hoch.gd, Besitzer 08.11.2026): Vulkan nur in Software -> sofort Normal; kein erstes Bild nach
# einem Hoch-Start -> der Wachhund startet mit Normal neu. Ohne Vulkan prüfbar: MW_HOCH_PROBE=software | haengt spielt den Fall.
#   bash werkzeuge/hoch_schutz_test.sh [GODOT]        (braucht Xvfb; eigener HOME in einem Temp-Ordner)
set -u
G="${1:-${GODOT:-godot}}"
R="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
F=0
U="$T/home/.local/share/godot/app_userdata/MoveEye Sim 3D"
mkdir -p "$U"
D=":$((150 + $$ % 40))"                       # eigener Xvfb für alle Starts (der Neustart bleibt auf demselben Bildschirm)
Xvfb "$D" -screen 0 640x360x24 -nolisten tcp > /dev/null 2>&1 &
XV=$!
sleep 2
ok() { echo "  ok: $*"; }
fehler() { echo "  FEHLER: $*"; F=$((F + 1)); }
starte() {  # LOG ENV… -- ARGS…  : Simulator starten, nach 25 s alle Prozesse mit diesem HOME beenden
	local log="$1"; shift
	( cd "$R/simulator3d" && env HOME="$T/home" "$@" > "$log" 2>&1 & )
	sleep 25
	pkill -f -- "--hoch-test-$$" 2>/dev/null
	sleep 2
}
lies() { python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2]))" "$U/grafik_stufe.json" "$1" 2>/dev/null; }

echo "--- 1. Vulkan nur in Software (llvmpipe / lavapipe): sofort zurück zu Normal, Hinweis, «Hoch» im Menü markiert"
echo '{"stufe": "hoch", "pending": true}' > "$U/grafik_stufe.json"
starte "$T/s1.log" MW_HOCH_PROBE=software DISPLAY="$D" "$G" --path . -- --no-update --hoch-fwd --hoch-test-$$
grep -q "runs in software only" "$T/s1.log" && ok "erkannt, Neustart mit Normal" || fehler "nicht erkannt ($(tail -3 "$T/s1.log" | tr '\n' ' '))"
[ "$(lies stufe)" = "normal" ] && [ "$(lies unmoeglich)" = "True" ] && [ "$(lies pending)" = "False" ] && ok "Merker: Normal, «unmöglich», nicht mehr «pending»" \
	|| fehler "Merker falsch: $(cat "$U/grafik_stufe.json")"
[ "$(lies failed)" = "None" ] && ok "der neue Start hat den Hinweis gezeigt (failed / grund abgeräumt)" || fehler "Hinweis nicht abgeholt: $(cat "$U/grafik_stufe.json")"
cat > "$T/modes.gd" <<'EOF'
extends SceneTree
func _initialize() -> void:
	for m in load("res://scripts/grafik_hoch.gd").modes():
		print("MODE ", m[0], " | ", m[1])
	quit(0)
EOF
( cd "$R/simulator3d" && HOME="$T/home" timeout 60 "$G" --headless --path . -s "$T/modes.gd" > "$T/modes.log" 2>&1 )
grep -q "MODE hoch | Hoch – auf diesem Rechner nicht möglich" "$T/modes.log" && grep -q "MODE normal | Normal" "$T/modes.log" \
	&& ok "System › Grafik: «Hoch – auf diesem Rechner nicht möglich», wählbar" || fehler "Menü: $(grep MODE "$T/modes.log" | tr '\n' ' ')"

echo "--- 2. Start hängt (kein erstes Bild): der Wachhund startet mit Normal neu"
echo '{"stufe": "hoch", "pending": true}' > "$U/grafik_stufe.json"
starte "$T/s2.log" MW_HOCH_PROBE=haengt MW_HOCH_WACHHUND_S=5 DISPLAY="$D" "$G" --path . -- --no-update --hoch-fwd --hoch-test-$$
grep -q "no first frame after 5 s" "$T/s2.log" && ok "Wachhund ausgelöst" || fehler "kein Wachhund ($(tail -3 "$T/s2.log" | tr '\n' ' '))"
[ "$(lies stufe)" = "normal" ] && [ "$(lies pending)" = "False" ] && ok "Merker: Normal" || fehler "Merker falsch: $(cat "$U/grafik_stufe.json")"

echo "--- 3. ohne Probe und ohne Hoch (Normal): nichts davon"
echo '{"stufe": "normal"}' > "$U/grafik_stufe.json"
starte "$T/s3.log" DISPLAY="$D" "$G" --path . -- --no-update --hoch-test-$$
grep -q "software only\|no first frame\|restart with" "$T/s3.log" && fehler "Normal-Start betroffen" || ok "Normal unverändert (kein Neustart)"

kill $XV 2>/dev/null
rm -rf "$T"
echo
if [ $F -eq 0 ]; then echo "Hoch-Schutz-Test: OK"; else echo "Hoch-Schutz-Test: $F Fehler"; fi
exit $F
