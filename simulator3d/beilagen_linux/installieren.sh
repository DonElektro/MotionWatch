#!/bin/bash
# MoveEye Sim 3D - Startmenü-Eintrag und Symbol auf dem Desktop (Linux Mint, Ubuntu; ohne sudo).
#   ./installieren.sh             Eintrag im Startmenü (~/.local/share/applications) und auf dem Desktop anlegen
#   ./installieren.sh --entfernen beide Einträge und das Symbol wieder wegnehmen (der Ordner bleibt)
# Der Eintrag zeigt auf MoveEyeSim3D.x86_64 in DIESEM Ordner. Das Update des Simulators ersetzt die Datei am selben Ort,
# der Eintrag bleibt also gültig. Wird der Ordner verschoben: dieses Skript im neuen Ordner noch einmal starten.
set -u
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
EXE="$DIR/MoveEyeSim3D.x86_64"
# Sim 3.57.0: dasselbe Skript liegt im Pi-Paket (MoveEyeSim3D_Pi.zip, Raspberry Pi 5, arm64) - dort heisst die Datei .arm64
case "$(uname -m)" in
	aarch64|arm64) EXE="$DIR/MoveEyeSim3D.arm64" ;;
esac
ID="moveeye-sim"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICONDIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/512x512/apps"
ICON="$ICONDIR/$ID.png"

desktop_dir() {
	local d=""
	command -v xdg-user-dir >/dev/null 2>&1 && d="$(xdg-user-dir DESKTOP 2>/dev/null)"
	if [ -z "$d" ] || [ "$d" = "$HOME" ] || [ ! -d "$d" ]; then
		for c in "$HOME/Schreibtisch" "$HOME/Desktop"; do
			[ -d "$c" ] && { d="$c"; break; }
		done
	fi
	[ -n "$d" ] && [ "$d" != "$HOME" ] && [ -d "$d" ] && echo "$d"
}

if [ "${1:-}" = "--entfernen" ]; then
	rm -f "$APPS/$ID.desktop" "$ICON"
	D="$(desktop_dir)"; [ -n "$D" ] && rm -f "$D/$ID.desktop"
	command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q "$APPS" 2>/dev/null
	echo "MoveEye Sim: Einträge entfernt (der Ordner $DIR bleibt)."
	exit 0
fi

if [ ! -f "$EXE" ]; then
	echo "$(basename "$EXE") fehlt in $DIR - den ganzen Ordner aus der ZIP-Datei entpacken und hier starten."
	case "$(uname -m)" in
		aarch64|arm64) [ -f "$DIR/MoveEyeSim3D.x86_64" ] && echo "Das ist das Paket für PCs (x86_64). Auf dem Raspberry Pi: MoveEyeSim3D_Pi.zip - oder in MoveEye, Reiter Simulator, «Simulator intern (auf diesem Pi) ausprobieren»." ;;
	esac
	exit 1
fi
chmod +x "$EXE" "$DIR"/*.sh 2>/dev/null

mkdir -p "$APPS" "$ICONDIR"
if [ -f "$DIR/$ID.png" ]; then
	cp -f "$DIR/$ID.png" "$ICON"
else
	ICON="utilities-system-monitor"
fi

# Pfad für Exec= (Desktop-Entry-Regeln: in "…", dabei " ` $ \ mit \ schützen)
Q="$(printf '%s' "$EXE" | sed -e 's/\\/\\\\\\\\/g' -e 's/"/\\\\"/g' -e 's/`/\\\\`/g' -e 's/\$/\\\\$/g')"
TMP="$(mktemp)"
cat > "$TMP" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=MoveEye Sim
GenericName=MoveEye 3D-Simulator
Comment=3D-Simulator von MoveEye (Wildtier- und Personenwarnung)
Exec="$Q"
Path=$DIR
Icon=$ICON
Terminal=false
Categories=Education;Science;Simulation;
Keywords=MoveEye;Simulator;3D;
StartupNotify=true
Actions=notfall;

[Desktop Action notfall]
Name=Notfall-Start (Lite, ohne Foto-Inhalte, ohne Update)
Exec="$Q" -- --grafik lite --no-inhalte --no-update --no-hoch
EOF
install -m 755 "$TMP" "$APPS/$ID.desktop"
echo "Startmenü: $APPS/$ID.desktop"

D="$(desktop_dir)"
if [ -n "$D" ]; then
	install -m 755 "$TMP" "$D/$ID.desktop"
	# Mint/Cinnamon und GNOME starten Desktop-Symbole erst, wenn sie als vertrauenswürdig markiert sind
	command -v gio >/dev/null 2>&1 && gio set "$D/$ID.desktop" metadata::trusted true 2>/dev/null
	echo "Desktop:   $D/$ID.desktop"
else
	echo "Kein Desktop-Ordner gefunden - nur der Eintrag im Startmenü."
fi
rm -f "$TMP"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q "$APPS" 2>/dev/null
command -v xdg-desktop-menu >/dev/null 2>&1 && xdg-desktop-menu forceupdate 2>/dev/null
echo "Fertig: MoveEye Sim steht im Startmenü (Bildung / Wissenschaft) und auf dem Desktop."
exit 0
