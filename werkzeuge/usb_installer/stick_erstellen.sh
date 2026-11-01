#!/bin/bash
# MoveEye USB-Installer - macht aus dem offiziellen Ubuntu-24.04-Server-ISO einen Stick, der den Simulator-PC
# (HP EliteDesk 800 G1 DM) ohne Fragen neu aufsetzt und danach direkt im Kiosk mit MoveEye Sim startet.
#   ./stick_erstellen.sh ubuntu-24.04.x-live-server-amd64.iso              fragt alles, baut das ISO, schreibt den Stick
#   ./stick_erstellen.sh ISO --geraet /dev/sdX                             Stick gleich angeben (wird trotzdem bestätigt)
#   ./stick_erstellen.sh ISO --nur-iso                                     nur moveeye-<iso> bauen (z. B. für Rufus «DD»)
#   ./stick_erstellen.sh ISO --nur-dateien ORDNER                          nur Dateien für einen Ventoy-Stick (auch Windows/Git Bash)
#   weitere Optionen: --tastatur de|ch   --ssh-schluessel ~/.ssh/id_ed25519.pub
# Passwort, WLAN und Hash landen nur im Arbeitsordner (wird gelöscht), im neuen ISO und auf dem Stick - nie im Repository.
# Braucht: openssl, und für ISO/Stick xorriso (sudo apt install xorriso) und sudo für das Schreiben auf den Stick.
set -u

TASTATUR="de"      # Standard-Tastatur: de = Deutschland, ch = Schweiz (wird beim Start noch einmal gefragt)

HIER="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
VORLAGE="$HIER/user-data"
META="$HIER/meta-data"
ERSTSTART="$HIER/erststart.sh"

ISO="" GERAET="" NUR_ISO=0 NUR_DATEIEN="" SSHKEY="" TAST_ARG=""
while [ $# -gt 0 ]; do
	case "$1" in
		--geraet) GERAET="${2:-}"; shift ;;
		--nur-iso) NUR_ISO=1 ;;
		--nur-dateien) NUR_DATEIEN="${2:-}"; shift ;;
		--tastatur) TAST_ARG="${2:-}"; shift ;;
		--ssh-schluessel) SSHKEY="${2:-}"; shift ;;
		-h|--hilfe|--help) sed -n '2,11p' "$0"; exit 0 ;;
		-*) echo "Unbekannte Option: $1 (--hilfe)"; exit 2 ;;
		*) ISO="$1" ;;
	esac
	shift
done

stopp() { echo "FEHLER: $*" >&2; exit 1; }
[ -n "$ISO" ] || { sed -n '2,11p' "$0"; exit 2; }
[ -f "$ISO" ] || stopp "ISO nicht gefunden: $ISO"
ISO="$(readlink -f "$ISO")"
ISONAME="$(basename "$ISO")"
case "$ISONAME" in
	ubuntu-24.04*-live-server-amd64.iso) ;;
	*) echo "WARNUNG: $ISONAME sieht nicht nach ubuntu-24.04.x-live-server-amd64.iso aus (geprüft ist nur dieses)." ;;
esac
for f in "$VORLAGE" "$META" "$ERSTSTART"; do [ -r "$f" ] || stopp "Datei fehlt: $f"; done
command -v openssl >/dev/null || stopp "openssl fehlt (Linux: sudo apt install openssl; Windows: Git Bash verwenden)"
if [ -z "$NUR_DATEIEN" ]; then
	command -v xorriso >/dev/null || stopp "xorriso fehlt: sudo apt install xorriso"
fi

W="$(mktemp -d)"
chmod 700 "$W"
trap 'rm -rf "$W"' EXIT
mkdir -p "$W/moveeye"

yaml_text() {   # Text sicher in "…" für YAML
	local s="${1//\\/\\\\}"
	s="${s//\"/\\\"}"
	printf '"%s"' "$s"
}

echo "=== MoveEye USB-Installer ==="
echo "ACHTUNG: Der Stick setzt den PC komplett neu auf - die ganze interne Platte wird gelöscht."
echo

# --- Tastatur
T="${TAST_ARG:-}"
if [ -z "$T" ]; then
	read -r -p "Tastatur: de (Deutschland) oder ch (Schweiz)? [Enter = $TASTATUR] " T
	T="${T:-$TASTATUR}"
fi
case "$T" in de|ch) ;; *) stopp "Tastatur «$T» unbekannt (de oder ch)" ;; esac

# --- Passwort (nur als Hash weiter)
while :; do
	read -r -s -p "Passwort für den Benutzer «don» (für Anmeldung, SSH und sudo): " P1; echo
	read -r -s -p "Passwort wiederholen: " P2; echo
	if [ -z "$P1" ]; then echo "Leer geht nicht."; continue; fi
	if [ "$P1" != "$P2" ]; then echo "Nicht gleich - noch einmal."; continue; fi
	[ "${#P1}" -lt 8 ] && echo "Hinweis: kürzer als 8 Zeichen - SSH ist offen, besser ein längeres Passwort."
	break
done
HASH="$(printf '%s' "$P1" | openssl passwd -6 -stdin)"
unset P1 P2
# shellcheck disable=SC2016  # wörtlich $6$
case "$HASH" in '$6$'*) ;; *) stopp "openssl passwd -6 hat keinen Hash geliefert" ;; esac

# --- WLAN (freiwillig; LAN-Kabel ist sicherer)
WLAN_BLOCK=""
read -r -p "WLAN-Name (SSID) für den PC? [Enter = nur LAN-Kabel] " SSID
if [ -n "$SSID" ]; then
	while :; do
		read -r -s -p "WLAN-Passwort für «$SSID»: " WPW; echo
		[ "${#WPW}" -ge 8 ] && [ "${#WPW}" -le 63 ] && break
		echo "WLAN-Passwörter haben 8 bis 63 Zeichen - noch einmal."
	done
	WLAN_BLOCK="    wifis:
      wlan:
        match:
          name: \"wl*\"
        dhcp4: true
        optional: true
        access-points:
          $(yaml_text "$SSID"):
            password: $(yaml_text "$WPW")"
	unset WPW
	echo "Hinweis: das WLAN-Passwort steht dann auf dem Stick (und später im PC). Stick danach sicher aufbewahren oder neu formatieren."
fi

# --- SSH-Schlüssel (freiwillig, öffentlicher Teil)
if [ -z "$SSHKEY" ] && [ -r "$HOME/.ssh/id_ed25519.pub" ]; then
	read -r -p "Deinen SSH-Schlüssel ~/.ssh/id_ed25519.pub übernehmen (Anmelden ohne Passwort)? (j/n) [j] " a
	case "${a:-j}" in j|J|ja|y|Y) SSHKEY="$HOME/.ssh/id_ed25519.pub" ;; esac
fi
SSH_BLOCK=""
if [ -n "$SSHKEY" ]; then
	[ -r "$SSHKEY" ] || stopp "SSH-Schlüssel nicht lesbar: $SSHKEY"
	case "$SSHKEY" in *.pub) ;; *) stopp "Nur den öffentlichen Schlüssel (.pub) angeben" ;; esac
	SSH_BLOCK="    authorized-keys:"
	while IFS= read -r z; do
		case "$z" in ssh-*|ecdsa-*|sk-*) SSH_BLOCK="$SSH_BLOCK
      - $(yaml_text "$z")" ;; esac
	done < "$SSHKEY"
	[ "$SSH_BLOCK" = "    authorized-keys:" ] && stopp "In $SSHKEY steht kein SSH-Schlüssel"
fi

# --- user-data für den Stick zusammensetzen
B64="$(base64 -w0 < "$ERSTSTART" 2>/dev/null || base64 < "$ERSTSTART" | tr -d '\n')"
M_TAST="$T" M_HASH="$HASH" M_B64="$B64" M_WLAN="$WLAN_BLOCK" M_SSH="$SSH_BLOCK" awk '
	function ersetze(s, alt, neu,   i) {
		while ((i = index(s, alt)) > 0) s = substr(s, 1, i - 1) neu substr(s, i + length(alt))
		return s
	}
	/^[[:space:]]*#@@WLAN@@[[:space:]]*$/ { if (ENVIRON["M_WLAN"] != "") print ENVIRON["M_WLAN"]; next }
	/^    authorized-keys: \[\][[:space:]]*$/ && ENVIRON["M_SSH"] != "" { print ENVIRON["M_SSH"]; next }
	{
		z = ersetze($0, "@@TASTATUR@@", ENVIRON["M_TAST"])
		z = ersetze(z, "@@PASSWORT_HASH@@", ENVIRON["M_HASH"])
		z = ersetze(z, "@@ERSTSTART_B64@@", ENVIRON["M_B64"])
		print z
	}' "$VORLAGE" > "$W/moveeye/user-data"
unset HASH WLAN_BLOCK
cp "$META" "$W/moveeye/meta-data"
grep -Eq '@@[A-Z_]+@@' "$W/moveeye/user-data" && stopp "Platzhalter in user-data nicht ersetzt"
chmod 600 "$W/moveeye/user-data"

# --- nur Dateien für Ventoy
if [ -n "$NUR_DATEIEN" ]; then
	mkdir -p "$NUR_DATEIEN/moveeye" "$NUR_DATEIEN/ventoy" || stopp "Ordner $NUR_DATEIEN geht nicht"
	cp "$W/moveeye/user-data" "$W/moveeye/meta-data" "$NUR_DATEIEN/moveeye/"
	cat > "$NUR_DATEIEN/ventoy/ventoy.json" <<EOF
{
  "auto_install": [
    { "image": "/$ISONAME", "template": "/moveeye/user-data" }
  ]
}
EOF
	echo
	echo "Fertig: $NUR_DATEIEN/moveeye/ und $NUR_DATEIEN/ventoy/ventoy.json"
	echo "Auf den Ventoy-Stick kopieren: $ISONAME (ins Hauptverzeichnis), dazu die Ordner moveeye und ventoy."
	exit 0
fi

# --- Startmenü im ISO: eigener erster Eintrag mit «autoinstall», wartet auf Enter (kein Löschen aus Versehen)
xorriso -osirrox on -indev "$ISO" -extract /boot/grub/grub.cfg "$W/grub.orig" >/dev/null 2>&1 \
	|| stopp "boot/grub/grub.cfg nicht im ISO - ist es wirklich das Server-ISO?"
chmod u+w "$W/grub.orig"
grep -q '/casper/vmlinuz' "$W/grub.orig" || stopp "grub.cfg ohne /casper/vmlinuz - unbekanntes ISO"
{
	echo "set timeout=-1"
	echo "set default=0"
	awk '
		/^[[:space:]]*set[[:space:]]+(timeout|default)=/ { next }
		/^[[:space:]]*menuentry/ && !fertig {
			print "menuentry \"MoveEye: PC NEU AUFSETZEN - loescht die ganze Platte!\" {"
			print "\tset gfxpayload=keep"
			print "\tlinux\t/casper/vmlinuz autoinstall ds=nocloud\\;s=/cdrom/moveeye/ ---"
			print "\tinitrd\t/casper/initrd"
			print "}"
			print "menuentry \"Abbrechen: von der Festplatte starten\" {"
			print "\texit 1"
			print "}"
			fertig = 1
		}
		{ print }' "$W/grub.orig"
} > "$W/grub.cfg"

NEU="$(dirname "$ISO")/moveeye-$ISONAME"
FREI="$(df -P -B1 "$(dirname "$ISO")" | awk 'NR == 2 { print $4 }')"
GROESSE="$(stat -c %s "$ISO")"
[ "${FREI:-0}" -gt $((GROESSE + 100000000)) ] || stopp "zu wenig Platz in $(dirname "$ISO") (braucht ~$((GROESSE / 1000000 + 100)) MB)"
echo
echo "--- Baue $NEU"
rm -f "$NEU"
if ! xorriso -indev "$ISO" -outdev "$NEU" \
	-map "$W/moveeye" /moveeye \
	-map "$W/grub.cfg" /boot/grub/grub.cfg \
	-boot_image any replay > "$W/xorriso.log" 2>&1 || [ ! -s "$NEU" ]; then
	tail -n 20 "$W/xorriso.log"; rm -f "$NEU"; stopp "xorriso hat kein ISO gebaut"
fi
chmod 600 "$NEU"   # enthält den Passwort-Hash
echo "ISO fertig: $NEU"
if [ $NUR_ISO -eq 1 ]; then
	echo "Auf den Stick schreiben: Linux «sudo dd if=$NEU of=/dev/sdX bs=4M status=progress oflag=sync», Windows Rufus im DD-Modus."
	exit 0
fi

# --- Stick wählen und schreiben
echo
echo "USB-Geräte:"
lsblk -dpno NAME,SIZE,TRAN,MODEL | awk '$3 == "usb"' | sed 's/^/  /'
if [ -z "$GERAET" ]; then
	read -r -p "Welches Gerät ist der Stick (z. B. /dev/sdb)? " GERAET
fi
[ -b "$GERAET" ] || stopp "$GERAET ist kein Laufwerk"
[ "$(lsblk -dno TYPE "$GERAET")" = disk ] || stopp "$GERAET ist eine Partition - das ganze Gerät angeben (z. B. /dev/sdb, nicht /dev/sdb1)"
lsblk -no MOUNTPOINT "$GERAET" | grep -Eqx '/|/boot|/boot/efi|/home' && stopp "$GERAET ist die Platte dieses PCs!"
if [ "$(lsblk -dno TRAN "$GERAET")" != usb ]; then
	echo "WARNUNG: $GERAET ist kein USB-Gerät."
fi
echo
lsblk -po NAME,SIZE,MODEL,LABEL,MOUNTPOINT "$GERAET"
echo "ALLES auf $GERAET wird gelöscht."
read -r -p "Zum Bestätigen den Gerätenamen noch einmal eintippen: " nochmal
[ "$nochmal" = "$GERAET" ] || stopp "nicht bestätigt - nichts geschrieben"
for p in $(lsblk -lnpo NAME "$GERAET" | tail -n +2); do
	sudo umount "$p" 2>/dev/null
done
sudo dd if="$NEU" of="$GERAET" bs=4M status=progress conv=fsync || stopp "Schreiben auf $GERAET fehlgeschlagen"
sync
echo
echo "Stick fertig. Am HP: Stick einstecken, einschalten, F9 drücken, den USB-Stick wählen,"
echo "im Menü «MoveEye: PC NEU AUFSETZEN» mit Enter starten. Wenn der PC sich ausschaltet: Stick abziehen, einschalten."
read -r -p "Das gebaute ISO $NEU (enthält den Passwort-Hash) jetzt löschen? (j/n) [j] " a
case "${a:-j}" in j|J|ja|y|Y) rm -f "$NEU"; echo "gelöscht." ;; *) echo "bleibt: $NEU" ;; esac
exit 0
