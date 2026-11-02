#!/bin/bash
# MoveEye USB-Installer - erster Start des frisch installierten PCs (Ubuntu 24.04 oder 26.04 Server).
# stick_erstellen.sh packt diese Datei in die user-data; der Installer legt sie als /usr/local/sbin/moveeye-erststart ab.
#   moveeye-erststart --einrichten   (im Installer, chroot) Dienst anlegen, automatische Sicherheitsupdates, grafischer Start
#   moveeye-erststart                (Dienst beim ersten Start, als root) Paketquellen prüfen, Simulator laden, installieren.sh,
#                                    kiosk_ein.sh --ja, dann neu starten. Klappt etwas nicht (kein Netz), beim nächsten Start noch einmal.
#   sudo bash erststart.sh --retten  (von Hand) nach einer abgebrochenen Installation: Paketquellen setzen (cdrom weg),
#                                    fehlende Pakete installieren, sich selbst einrichten und den ersten Start sofort ausführen
# Protokoll: /var/log/moveeye-erststart.log (und auf dem Bildschirm). Fertig-Marke: /var/lib/moveeye/erststart_fertig
set -u
BENUTZER="${MOVEEYE_BENUTZER:-don}"
URL="${MOVEEYE_URL:-https://github.com/DonElektro/MotionWatch/raw/main/simulator3d/MoveEyeSim3D_Linux.zip}"
MARKE="${MOVEEYE_MARKE:-/var/lib/moveeye/erststart_fertig}"
LOG="${MOVEEYE_LOG:-/var/log/moveeye-erststart.log}"
APT="${MOVEEYE_APT:-/etc/apt}"
DIENST="/etc/systemd/system/moveeye-erststart.service"
SELBST="/usr/local/sbin/moveeye-erststart"
# gleiche Liste wie «packages:» in user-data (stick_erstellen.sh prüft, dass beide gleich sind)
PAKETE=(xorg openbox lightdm lightdm-gtk-greeter x11-xserver-utils libgl1-mesa-dri libglx-mesa0 mesa-vulkan-drivers mesa-utils
	alsa-utils openssh-server ufw unattended-upgrades curl unzip wpasupplicant)

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

quellen() {
	# Paketquellen: «cdrom» abschalten (bleibt nach einem Abbruch der Installation zurück, der Stick ist dann weg) und
	# sicherstellen, dass eine Online-Quelle da ist. Nichts wird gelöscht: Dateien werden umbenannt, Zeilen auskommentiert.
	local f codename
	for f in "$APT/sources.list" "$APT"/sources.list.d/*.list; do
		[ -f "$f" ] || continue
		if grep -Eq '^[[:space:]]*deb[^#]*(cdrom:|file:/+cdrom)' "$f"; then
			sed -i -E 's%^([[:space:]]*deb[^#]*(cdrom:|file:/+cdrom).*)$%# moveeye: cdrom aus # \1%' "$f"
			echo "Paketquelle: cdrom in $f abgeschaltet"
		fi
	done
	for f in "$APT"/sources.list.d/*.sources; do
		[ -f "$f" ] || continue
		if grep -Eiq '^[[:space:]]*URIs:.*(cdrom:|file:/+cdrom)' "$f"; then
			mv "$f" "$f.moveeye-aus"
			echo "Paketquelle: $f abgeschaltet (cdrom), jetzt $f.moveeye-aus"
		fi
	done
	if grep -Eqs '^[^#]*(URIs:|deb )[^#]*https?://' "$APT/sources.list" "$APT"/sources.list.d/*.list "$APT"/sources.list.d/*.sources; then
		return 0
	fi
	# shellcheck disable=SC1091  # /etc/os-release gibt es auf jedem Ubuntu
	codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"
	[ -n "$codename" ] || { echo "Paketquelle: Ubuntu-Version unbekannt (/etc/os-release)"; return 1; }
	mkdir -p "$APT/sources.list.d"
	f="$APT/sources.list.d/ubuntu.sources"
	[ -e "$f" ] && mv "$f" "$f.moveeye-alt"
	cat > "$f" <<EOF
## MoveEye: Online-Paketquellen (gesetzt von moveeye-erststart)
Types: deb
URIs: http://archive.ubuntu.com/ubuntu/
Suites: $codename $codename-updates $codename-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

Types: deb
URIs: http://security.ubuntu.com/ubuntu/
Suites: $codename-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF
	echo "Paketquelle: $f gesetzt ($codename, archive.ubuntu.com)"
}

pakete() {   # fehlende Pakete der user-data nachinstallieren (z. B. nach einer abgebrochenen Installation)
	local p rc fehlt=() sperre=""
	for p in "${PAKETE[@]}"; do
		dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q 'install ok installed' || fehlt+=("$p")
	done
	[ ${#fehlt[@]} -eq 0 ] && return 0
	echo "--- Pakete nachinstallieren: ${fehlt[*]}"
	# Dienste (lightdm!) während der Installation nicht starten: dieser Dienst läuft «Before=display-manager» und würde
	# sonst auf sich selbst warten. Sie starten nach dem Neustart am Schluss.
	if [ ! -e /usr/sbin/policy-rc.d ]; then
		printf '#!/bin/sh\n# MoveEye erststart: vorübergehend\nexit 101\n' > /usr/sbin/policy-rc.d && chmod 755 /usr/sbin/policy-rc.d &&
			sperre=/usr/sbin/policy-rc.d
	fi
	DEBIAN_FRONTEND=noninteractive apt-get update -q &&
		DEBIAN_FRONTEND=noninteractive apt-get install -y -q "${fehlt[@]}"
	rc=$?
	[ -n "$sperre" ] && rm -f "$sperre"
	return $rc
}

firewall() {   # SSH und Simulator offen, sonst eingehend zu
	command -v ufw >/dev/null 2>&1 || return 0
	ufw allow 22/tcp comment "MoveEye Kiosk SSH" >/dev/null
	ufw allow 8765/tcp comment "MoveEye Kiosk Simulator" >/dev/null
	ufw allow out 8764/udp comment "MoveEye Kiosk Suche" >/dev/null
	ufw default deny incoming >/dev/null
	ufw default allow outgoing >/dev/null
	ufw --force enable
}

erststart() {
	exec > >(tee -a "$LOG") 2>&1
	echo "=== MoveEye: erster Start ($(date '+%F %T')) ==="
	local heim="" zip ordner i
	# der Benutzer entsteht beim ersten Start (cloud-init) - kurz warten, falls er noch fehlt
	for i in $(seq 1 24); do
		heim="$(getent passwd "$BENUTZER" | cut -d: -f6)"
		[ -n "$heim" ] && [ -d "$heim" ] && break
		[ "$i" -eq 24 ] && { echo "Benutzer $BENUTZER (oder sein Ordner) fehlt - abgebrochen"; return 1; }
		sleep 5
	done
	ordner="$heim/MoveEyeSim3D"

	firewall   # gleich zu Beginn (auch wenn der Download später nicht klappt)
	quellen || echo "Paketquellen nicht in Ordnung - Pakete können fehlen."

	zip="$(mktemp /tmp/moveeye_sim_XXXXXX.zip)"
	# bis ~20 Minuten auf Netz warten (WLAN braucht manchmal länger); fehlende Pakete (curl, unzip ...) zuerst nachholen
	for i in $(seq 1 40); do
		echo "Simulator laden (Versuch $i/40): $URL"
		if pakete && curl -fsSL --retry 2 --connect-timeout 20 -o "$zip" "$URL" && unzip -tq "$zip" >/dev/null 2>&1; then
			break
		fi
		[ "$i" -eq 40 ] && { echo "Kein Download möglich (Netz? Paketquelle?) - beim nächsten Start noch einmal."; rm -f "$zip"; return 0; }
		sleep 30
	done
	firewall   # falls ufw eben erst installiert wurde
	# mktemp legt die Datei für root mit 0600 an - der Benutzer muss sie zum Entpacken lesen können
	chmod 644 "$zip"
	runuser -u "$BENUTZER" -- unzip -oq "$zip" -d "$heim" || { echo "Entpacken fehlgeschlagen"; rm -f "$zip"; return 0; }
	rm -f "$zip"
	[ -d "$ordner" ] || { echo "Ordner $ordner fehlt nach dem Entpacken - beim nächsten Start noch einmal."; return 0; }
	chmod +x "$ordner"/*.sh "$ordner/MoveEyeSim3D.x86_64"

	echo "--- installieren.sh (Startmenü-Eintrag)"
	( cd "$heim" && runuser -u "$BENUTZER" -- env HOME="$heim" bash "$ordner/installieren.sh" ) || true
	echo "--- kiosk_ein.sh --ja"
	# kiosk_ein.sh läuft als root für den Benutzer aus SUDO_USER (so wie «sudo ./kiosk_ein.sh»), ohne Rückfrage
	if ( cd "$heim" && env SUDO_USER="$BENUTZER" bash "$ordner/kiosk_ein.sh" --ja ); then
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

retten() {   # halbes System nach einer abgebrochenen Installation fertig machen
	[ "$(id -u)" -eq 0 ] || { echo "Bitte mit sudo starten: sudo bash $0 --retten"; exit 1; }
	getent passwd "$BENUTZER" >/dev/null || { echo "Benutzer $BENUTZER fehlt - zuerst anlegen: sudo adduser $BENUTZER"; exit 1; }
	echo "=== MoveEye: abgebrochene Installation retten ==="
	quellen || exit 1
	pakete || { echo "Pakete konnten nicht installiert werden (Ausgabe oben). Kein Internet? LAN-Kabel einstecken, noch einmal starten."; exit 1; }
	if [ "$(readlink -f "$0")" != "$SELBST" ]; then
		install -m 755 "$0" "$SELBST" && echo "installiert: $SELBST"
	fi
	einrichten
	erststart
}

case "${1:-}" in
	--einrichten) einrichten ;;
	--retten) retten ;;
	"") erststart ;;
	*) sed -n '2,10p' "$0"; exit 2 ;;
esac
