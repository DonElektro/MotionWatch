#!/bin/bash
# MoveEye USB-Installer - erster Start des frisch installierten PCs (Ubuntu 24.04 Server).
# stick_erstellen.sh packt diese Datei in die user-data; der Installer legt sie als /usr/local/sbin/moveeye-erststart ab.
#   moveeye-erststart --einrichten   (im Installer, chroot) Dienst anlegen, automatische Sicherheitsupdates, grafischer Start
#   moveeye-erststart                (Dienst beim ersten Start, als root) Simulator laden, installieren.sh, kiosk_ein.sh --ja,
#                                    dann neu starten. Klappt der Download nicht (kein Netz), beim nächsten Start noch einmal.
# Protokoll: /var/log/moveeye-erststart.log (und auf dem Bildschirm). Fertig-Marke: /var/lib/moveeye/erststart_fertig
set -u
BENUTZER="${MOVEEYE_BENUTZER:-don}"
URL="${MOVEEYE_URL:-https://github.com/DonElektro/MotionWatch/raw/main/simulator3d/MoveEyeSim3D_Linux.zip}"
MARKE="/var/lib/moveeye/erststart_fertig"
LOG="/var/log/moveeye-erststart.log"
DIENST="/etc/systemd/system/moveeye-erststart.service"
SELBST="/usr/local/sbin/moveeye-erststart"

einrichten() {
	cat > "$DIENST" <<EOF
[Unit]
Description=MoveEye: Simulator laden und Kiosk einrichten (nur beim ersten Start)
Wants=network-online.target
After=network-online.target
Before=display-manager.service
ConditionPathExists=!$MARKE

[Service]
Type=oneshot
ExecStart=$SELBST
RemainAfterExit=yes
TimeoutStartSec=0
StandardOutput=journal+console
StandardError=journal+console

[Install]
WantedBy=multi-user.target
EOF
	systemctl enable moveeye-erststart.service
	# automatische Sicherheitsupdates (unattended-upgrades: nur «-security»); Neustart nachts, falls ein Update ihn braucht
	cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
	cat > /etc/apt/apt.conf.d/52moveeye-unattended <<'EOF'
// MoveEye USB-Installer: nach Sicherheitsupdates, die einen Neustart brauchen, um 04:30 neu starten (der Kiosk kommt von selbst)
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:30";
EOF
	systemctl enable unattended-upgrades.service 2>/dev/null
	systemctl set-default graphical.target
	echo "moveeye-erststart: eingerichtet"
}

erststart() {
	exec > >(tee -a "$LOG") 2>&1
	echo "=== MoveEye: erster Start ($(date '+%F %T')) ==="
	local heim zip ordner i
	heim="$(getent passwd "$BENUTZER" | cut -d: -f6)"
	[ -n "$heim" ] || { echo "Benutzer $BENUTZER fehlt - abgebrochen"; return 1; }
	ordner="$heim/MoveEyeSim3D"

	# Firewall gleich zu Beginn (auch wenn der Download später nicht klappt): SSH und Simulator offen
	ufw allow 22/tcp comment "MoveEye Kiosk SSH" >/dev/null
	ufw allow 8765/tcp comment "MoveEye Kiosk Simulator" >/dev/null
	ufw allow out 8764/udp comment "MoveEye Kiosk Suche" >/dev/null
	ufw default deny incoming >/dev/null
	ufw default allow outgoing >/dev/null
	ufw --force enable

	zip="$(mktemp /tmp/moveeye_sim_XXXXXX.zip)"
	# bis ~20 Minuten auf Netz warten (WLAN braucht manchmal länger)
	for i in $(seq 1 40); do
		echo "Simulator laden (Versuch $i/40): $URL"
		if curl -fsSL --retry 2 --connect-timeout 20 -o "$zip" "$URL" && unzip -tq "$zip" >/dev/null 2>&1; then
			break
		fi
		[ "$i" -eq 40 ] && { echo "Kein Download möglich (Netz?) - beim nächsten Start noch einmal."; rm -f "$zip"; return 0; }
		sleep 30
	done
	runuser -u "$BENUTZER" -- unzip -oq "$zip" -d "$heim" || { echo "Entpacken fehlgeschlagen"; rm -f "$zip"; return 0; }
	rm -f "$zip"
	chmod +x "$ordner"/*.sh "$ordner/MoveEyeSim3D.x86_64"

	echo "--- installieren.sh (Startmenü-Eintrag)"
	runuser -u "$BENUTZER" -- env HOME="$heim" bash "$ordner/installieren.sh" || true
	echo "--- kiosk_ein.sh --ja"
	# kiosk_ein.sh läuft als root für den Benutzer aus SUDO_USER (so wie «sudo ./kiosk_ein.sh»), ohne Rückfrage
	if env SUDO_USER="$BENUTZER" bash "$ordner/kiosk_ein.sh" --ja; then
		echo "Kiosk eingerichtet."
	else
		echo "kiosk_ein.sh meldet Fehler - Protokoll in $heim/.moveeye_kiosk/. Der PC startet trotzdem neu."
	fi
	mkdir -p "$(dirname "$MARKE")"
	date '+%F %T' > "$MARKE"
	systemctl disable moveeye-erststart.service 2>/dev/null
	echo "=== Fertig. Neustart in 10 s - danach startet der Simulator im Vollbild. ==="
	sleep 10
	systemctl reboot --no-block
}

case "${1:-}" in
	--einrichten) einrichten ;;
	"") erststart ;;
	*) sed -n '2,8p' "$0"; exit 2 ;;
esac
