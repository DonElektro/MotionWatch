#!/bin/bash
# MoveEye USB-Installer - Internet prüfen, BEVOR die Platte gelöscht wird (läuft im Installer als «early-commands»).
# Ohne Internet bricht die Ubuntu-Installation sonst erst nach dem Löschen ab (Pakete wie xorg werden geladen).
# stick_erstellen.sh packt diese Datei in die user-data; der Installer legt sie als /tmp/moveeye-netz.sh ab und startet sie.
#   netzpruefung.sh            prüfen; ohne Internet eine Meldung auf eigenem Bildschirm, warten und immer wieder prüfen.
#                              Endet erst, wenn Internet da ist (dann geht die Installation weiter) - die Platte bleibt
#                              bis dahin unberührt. «aus» + Enter schaltet den PC aus.
#   netzpruefung.sh --einmal   nur prüfen (Exit 0 = Internet da, 1 = nicht)
set -u
ADRESSEN="${MOVEEYE_NETZ_ADRESSEN:-http://archive.ubuntu.com/ubuntu/ http://security.ubuntu.com/ubuntu/}"

online() {   # 0 = eine der Adressen antwortet
	local u
	for u in $ADRESSEN; do
		if command -v curl >/dev/null 2>&1; then
			curl -fsS -o /dev/null --connect-timeout 8 --max-time 20 "$u" 2>/dev/null && return 0
		elif command -v wget >/dev/null 2>&1; then
			wget -q -O /dev/null -T 15 -t 1 "$u" && return 0
		else
			python3 -c 'import sys, urllib.request; urllib.request.urlopen(sys.argv[1], timeout=15)' "$u" 2>/dev/null && return 0
		fi
	done
	return 1
}

meldung() {   # ASCII: die Schrift der Installer-Konsole kennt nicht immer Umlaute
	cat <<'EOF'

  ==============================================================
     MoveEye:  KEIN INTERNET
  ==============================================================

     Die Installation braucht Internet (Pakete werden geladen).
     Die Festplatte wurde NICHT geloescht.

     ->  LAN-Kabel einstecken, dann Enter druecken.
         (Alle 15 Sekunden wird auch von selbst geprueft.)

     "aus" und Enter: PC ausschalten - es wird nichts geloescht.
  ==============================================================

EOF
}

dialog() {   # läuft auf eigener Konsole (openvt), liest die Tastatur
	local a
	while :; do
		clear 2>/dev/null || printf '\033c'
		meldung
		a=""
		read -r -t 15 a || true
		case "$a" in
			aus|AUS|Aus) echo "  PC wird ausgeschaltet ..."; poweroff; sleep 60 ;;
		esac
		echo "  Pruefe Internet ..."
		if online; then echo "  Internet ok - die Installation geht weiter."; sleep 3; return 0; fi
	done
}

case "${1:-}" in
	--einmal) online; exit $? ;;
	--dialog) dialog; exit $? ;;
esac

# nach dem Start braucht DHCP manchmal einige Sekunden
for i in 1 2 3 4 5 6; do
	online && { echo "MoveEye: Internet ok"; exit 0; }
	[ "$i" -lt 6 ] && sleep 5
done
echo "MoveEye: kein Internet - die Platte wird NICHT geloescht, warte auf LAN-Kabel (Meldung auf dem Bildschirm)"
if command -v openvt >/dev/null 2>&1; then
	# eigene Konsole mit Tastatur, der Installer-Bildschirm (Konsole 1) bleibt unberührt
	openvt -s -w -- /bin/bash "$0" --dialog 2>/dev/null
	chvt 1 2>/dev/null || true
fi
# ohne openvt (oder falls die Konsole nicht ging): Meldung auf den Bildschirm, alle 15 s neu prüfen
while ! online; do
	meldung > /dev/console 2>/dev/null || meldung
	sleep 15
done
echo "MoveEye: Internet ok"
exit 0
