#!/bin/bash
# Paket Linux (Besitzer 01.11.2026): packt den exportierten Linux-Simulator (Preset «Linux», x86_64) in die ZIP für Linux-PCs.
#   werkzeuge/linux_paket.sh <MoveEyeSim3D.x86_64> [ziel.zip]      (Standard: simulator3d/MoveEyeSim3D_Linux.zip)
# Inhalt: MoveEyeSim3D/ mit MoveEyeSim3D.x86_64 (ausführbar), installieren.sh (Startmenü + Desktop, ohne sudo),
# moveeye-sim.png (Symbol) und «Lies mich.txt»; dazu der Kiosk (Besitzer 01.11.2026): kiosk_ein.sh / kiosk_aus.sh (reine
# Simulator-Maschine mit Linux Mint, rückgängig machbar) und kiosk_sitzung.sh (die Sitzung «MoveEye Kiosk»). Danach schreibt `versionen.py --sim-json` den Block «linux» in version.json
# (der Linux-Simulator holt sein Update dort, update.gd linux_info). Gleich aufgebaut wie die Windows-ZIP (simpack.sh).
# Dazu (HP_FASSUNG 4) controller_koppeln.sh / controller_fenster.py (PS5-Controller per Bluetooth koppeln, HP-Kiosk).
# Ab 3.53.0 dazu testbild.py (Testbild des Kiosks während der Tests), ab 3.55.0 hp_wache.py (Spielen-Wunsch, Status) und hp/ (Simulator-PC des Projekts: moveeye-hp-update,
# Haken und Dienst-Einstellungen des Test-Runners). Die SHA-256 dieser ZIP steht in der signierten Programmdatei (SIM3D_LINUX),
# darüber prüft moveeye-hp-update alles, was es einspielt.
# Ab Sim 3.57.0 auch das Pi-Paket (Besitzer 03.11.2026, «Simulator intern» auf dem Raspberry Pi 5, Preset «Linux Pi», arm64):
#   werkzeuge/linux_paket.sh --pi <MoveEyeSim3D.arm64> [ziel.zip]    (Standard: simulator3d/MoveEyeSim3D_Pi.zip)
# Inhalt abgespeckt: nur MoveEyeSim3D.arm64, installieren.sh (erkennt arm64 selbst), Symbol und «Lies mich.txt» - ohne Kiosk,
# testbild.py, hp_wache.py und hp/ (die gehören zum Simulator-PC). Danach `versionen.py --pi-json` (Block «pi» in version.json).
# Die ZIP kommt NICHT ins Repository (.gitignore), sondern als Release-Asset an den Tag sim-X.Y.Z; Grösse + SHA-256 signiert
# bauen.py --nur-signieren in versions.json «sim.pi» - nur damit nimmt MoveEye sie an (Teil 300 / 639zx).
set -e
PI=0
if [ "${1:-}" = "--pi" ]; then PI=1; shift; fi
BIN="$1"
R="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
if [ "$PI" = 1 ]; then
	OUT="${2:-$R/simulator3d/MoveEyeSim3D_Pi.zip}"
	test -s "$BIN" || { echo "Pi-Export (Preset «Linux Pi») fehlt: $BIN"; exit 1; }
	head -c 20 "$BIN" | od -An -tx1 | tr -d ' \n' | grep -q '^7f454c460201' || { echo "$BIN ist keine 64-Bit-ELF-Datei"; exit 1; }
	[ "$(od -An -tx1 -j18 -N2 "$BIN" | tr -d ' \n')" = "b700" ] || { echo "$BIN ist nicht für arm64 (aarch64) - Preset «Linux Pi» nehmen"; exit 1; }
else
	OUT="${2:-$R/simulator3d/MoveEyeSim3D_Linux.zip}"
	test -s "$BIN" || { echo "Linux-Export fehlt: $BIN"; exit 1; }
fi
W="$OUT.d"                        # Arbeitsordner neben der Ziel-ZIP (nur dieser wird wieder entfernt)
rm -rf "$W"; trap 'rm -rf "$W"' EXIT
mkdir -p "$W/MoveEyeSim3D"
if [ "$PI" = 1 ]; then
	cp "$BIN" "$W/MoveEyeSim3D/MoveEyeSim3D.arm64"
	cp "$R/simulator3d/beilagen_linux/installieren.sh" "$W/MoveEyeSim3D/"
	cp "$R/simulator3d/icon_sim3d.png" "$W/MoveEyeSim3D/moveeye-sim.png"
	cp "$R/simulator3d/Lies mich.txt" "$W/MoveEyeSim3D/"
	chmod 755 "$W/MoveEyeSim3D" "$W/MoveEyeSim3D/MoveEyeSim3D.arm64" "$W/MoveEyeSim3D/installieren.sh"
	chmod 644 "$W/MoveEyeSim3D/moveeye-sim.png" "$W/MoveEyeSim3D/Lies mich.txt"
	touch -d "2026-01-01 00:00:00" "$W/MoveEyeSim3D" "$W/MoveEyeSim3D/"*
	rm -f "$OUT.tmp"
	(cd "$W" && zip -q -9 -X -r "$OUT.tmp" MoveEyeSim3D)
	mv -f "$OUT.tmp" "$OUT"
	echo "Pi-Paket: $OUT ($(stat -c %s "$OUT") Bytes)"
	exit 0
fi
cp "$BIN" "$W/MoveEyeSim3D/MoveEyeSim3D.x86_64"
for f in installieren.sh kiosk_ein.sh kiosk_aus.sh kiosk_sitzung.sh testbild.py hp_wache.py controller_koppeln.sh controller_fenster.py; do
	cp "$R/simulator3d/beilagen_linux/$f" "$W/MoveEyeSim3D/"
done
mkdir -p "$W/MoveEyeSim3D/hp"
for f in hp_update.sh job_start.sh job_ende.sh runner_dienst.conf runner_entfernen.sh; do
	cp "$R/werkzeuge/test_runner/$f" "$W/MoveEyeSim3D/hp/"
done
cp "$R/simulator3d/icon_sim3d.png" "$W/MoveEyeSim3D/moveeye-sim.png"
cp "$R/simulator3d/Lies mich.txt" "$W/MoveEyeSim3D/"
chmod 755 "$W/MoveEyeSim3D/MoveEyeSim3D.x86_64" "$W/MoveEyeSim3D/installieren.sh" "$W/MoveEyeSim3D/kiosk_ein.sh" \
	"$W/MoveEyeSim3D/kiosk_aus.sh" "$W/MoveEyeSim3D/kiosk_sitzung.sh" "$W/MoveEyeSim3D/controller_koppeln.sh"
chmod 644 "$W/MoveEyeSim3D/moveeye-sim.png" "$W/MoveEyeSim3D/Lies mich.txt" "$W/MoveEyeSim3D/testbild.py" "$W/MoveEyeSim3D/hp_wache.py" "$W/MoveEyeSim3D/controller_fenster.py" \
	"$W/MoveEyeSim3D/hp/runner_dienst.conf"
chmod 755 "$W/MoveEyeSim3D/hp" "$W/MoveEyeSim3D/hp/"*.sh
rm -f "$OUT.tmp"
(cd "$W" && zip -q -9 -r "$OUT.tmp" MoveEyeSim3D)
mv -f "$OUT.tmp" "$OUT"
echo "Linux-Paket: $OUT ($(stat -c %s "$OUT") Bytes)"
