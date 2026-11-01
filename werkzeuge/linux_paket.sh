#!/bin/bash
# Paket Linux (Daniel 01.11.2026): packt den exportierten Linux-Simulator (Preset «Linux», x86_64) in die ZIP für Linux-PCs.
#   werkzeuge/linux_paket.sh <MoveEyeSim3D.x86_64> [ziel.zip]      (Standard: simulator3d/MoveEyeSim3D_Linux.zip)
# Inhalt: MoveEyeSim3D/ mit MoveEyeSim3D.x86_64 (ausführbar), installieren.sh (Startmenü + Desktop, ohne sudo),
# moveeye-sim.png (Symbol) und «Lies mich.txt»; dazu der Kiosk (Daniel 01.11.2026): kiosk_ein.sh / kiosk_aus.sh (reine
# Simulator-Maschine mit Linux Mint, rückgängig machbar) und kiosk_sitzung.sh (die Sitzung «MoveEye Kiosk»). Danach schreibt `versionen.py --sim-json` den Block «linux» in version.json
# (der Linux-Simulator holt sein Update dort, update.gd linux_info). Gleich aufgebaut wie die Windows-ZIP (simpack.sh).
set -e
BIN="$1"
R="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
OUT="${2:-$R/simulator3d/MoveEyeSim3D_Linux.zip}"
test -s "$BIN" || { echo "Linux-Export fehlt: $BIN"; exit 1; }
W="$OUT.d"                        # Arbeitsordner neben der Ziel-ZIP (nur dieser wird wieder entfernt)
rm -rf "$W"; trap 'rm -rf "$W"' EXIT
mkdir -p "$W/MoveEyeSim3D"
cp "$BIN" "$W/MoveEyeSim3D/MoveEyeSim3D.x86_64"
for f in installieren.sh kiosk_ein.sh kiosk_aus.sh kiosk_sitzung.sh; do
	cp "$R/simulator3d/beilagen_linux/$f" "$W/MoveEyeSim3D/"
done
cp "$R/simulator3d/icon_sim3d.png" "$W/MoveEyeSim3D/moveeye-sim.png"
cp "$R/simulator3d/Lies mich.txt" "$W/MoveEyeSim3D/"
chmod 755 "$W/MoveEyeSim3D/MoveEyeSim3D.x86_64" "$W/MoveEyeSim3D/installieren.sh" "$W/MoveEyeSim3D/kiosk_ein.sh" \
	"$W/MoveEyeSim3D/kiosk_aus.sh" "$W/MoveEyeSim3D/kiosk_sitzung.sh"
chmod 644 "$W/MoveEyeSim3D/moveeye-sim.png" "$W/MoveEyeSim3D/Lies mich.txt"
rm -f "$OUT.tmp"
(cd "$W" && zip -q -9 -r "$OUT.tmp" MoveEyeSim3D)
mv -f "$OUT.tmp" "$OUT"
echo "Linux-Paket: $OUT ($(stat -c %s "$OUT") Bytes)"
