#!/bin/bash
# Paket Linux (Daniel 01.11.2026): packt den exportierten Linux-Simulator (Preset «Linux», x86_64) in die ZIP für Linux-PCs.
#   werkzeuge/linux_paket.sh <MoveEyeSim3D.x86_64> [ziel.zip]      (Standard: simulator3d/MoveEyeSim3D_Linux.zip)
# Inhalt: MoveEyeSim3D/ mit MoveEyeSim3D.x86_64 (ausführbar), installieren.sh (Startmenü + Desktop, ohne sudo),
# moveeye-sim.png (Symbol) und «Lies mich.txt». Danach schreibt `versionen.py --sim-json` den Block «linux» in version.json
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
cp "$R/simulator3d/beilagen_linux/installieren.sh" "$W/MoveEyeSim3D/"
cp "$R/simulator3d/icon_sim3d.png" "$W/MoveEyeSim3D/moveeye-sim.png"
cp "$R/simulator3d/Lies mich.txt" "$W/MoveEyeSim3D/"
chmod 755 "$W/MoveEyeSim3D/MoveEyeSim3D.x86_64" "$W/MoveEyeSim3D/installieren.sh"
chmod 644 "$W/MoveEyeSim3D/moveeye-sim.png" "$W/MoveEyeSim3D/Lies mich.txt"
rm -f "$OUT.tmp"
(cd "$W" && zip -q -9 -r "$OUT.tmp" MoveEyeSim3D)
mv -f "$OUT.tmp" "$OUT"
echo "Linux-Paket: $OUT ($(stat -c %s "$OUT") Bytes)"
