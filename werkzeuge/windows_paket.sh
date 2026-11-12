#!/bin/bash
# Windows-Paket des Simulators packen (Simulator-Anhang, ab der Version nach Sim 3.67.2 im Workflow «Sim-Pakete»):
#   werkzeuge/windows_paket.sh <MoveEyeSim3D.exe> <ziel.zip>
# Inhalt wie bisher (simpack_lauf.sh): MoveEyeSim3D/MoveEyeSim3D.exe, die Konsolen-Fassung MoveEyeSim3D.console.exe (wenn sie
# neben der .exe liegt - Notfall-Start.bat braucht sie), die .bat aus simulator3d/beilagen/ und «Lies mich.txt».
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"
EXE="$1"; OUT="$2"
[ -s "$EXE" ] && [ -n "$OUT" ] || { echo "windows_paket.sh <MoveEyeSim3D.exe> <ziel.zip>"; exit 2; }
command -v zip >/dev/null 2>&1 || { echo "zip fehlt"; exit 1; }
W="$(mktemp -d)"
trap 'rm -rf -- "$W"' EXIT
mkdir -p "$W/MoveEyeSim3D"
cp "$EXE" "$W/MoveEyeSim3D/MoveEyeSim3D.exe"
K="$(dirname "$EXE")/MoveEyeSim3D.console.exe"
if [ -s "$K" ]; then cp "$K" "$W/MoveEyeSim3D/"; else echo "Hinweis: keine MoveEyeSim3D.console.exe neben der .exe"; fi
cp "$R"/simulator3d/beilagen/*.bat "$W/MoveEyeSim3D/"
cp "$R/simulator3d/Lies mich.txt" "$W/MoveEyeSim3D/"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
rm -f "$OUT"
(cd "$W" && zip -q -9 -r "$OUT" MoveEyeSim3D)
echo "Windows-Paket: $OUT ($(stat -c %s "$OUT") Bytes)"
unzip -Z1 "$OUT" | sed 's/^/  /'
