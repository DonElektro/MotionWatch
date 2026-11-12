#!/bin/bash
# MoveEye Kiosk - die Knöpfe des Simulator-PCs (HP_FASSUNG 8, Besitzer 12.11.2026): «Ausschalten», «Browser», «Controller
# koppeln». Läuft als Benutzer des Kiosks in seiner Sitzung, OHNE Rechte: der Simulator (Karte «Simulator-PC», hp_kiosk.gd)
# und Openbox (Ctrl+Alt+Z) rufen es auf. kiosk_sitzung.sh sagt dem Simulator über MOVEEYE_HP_KIOSK, wo es liegt.
#   hp_knoepfe.sh info                 eine Zeile JSON: {"fassung", "test", "aus", "bios", "browser", "koppeln"}
#   hp_knoepfe.sh aus herunterfahren | neustart | bios
#                                      legt nur die leere Wunsch-Datei /run/moveeye-spiel/aus_<was> an; der Dienst
#                                      moveeye-aus (root, hp_aus.sh, feste Befehle) schaltet aus. Kein sudo, keine polkit-Regel.
#   hp_knoepfe.sh browser              den Browser öffnen, der schon da ist (Firefox, sonst Chromium), über dem Kiosk:
#                                      eigenes Profil und eigener Download-Ordner in ~/MoveEye-Browser, oben die Leiste
#                                      «‹ Zurück zum Simulator» (browser_leiste.py). Der Simulator wird solange angehalten
#                                      (SIGSTOP: kein Ton, keine Rechenlast, sein Speicher darf ausgelagert werden - der HP
#                                      hat 4 GB) und läuft danach genau dort weiter (SIGCONT). Die Marke
#                                      /run/moveeye-spiel/browser_offen sagt hp_wache.py: es wird «gespielt» (kein Rechnen).
#                                      Läuft ein Test, öffnet er nicht (Status «test»). Wird der Browser geschlossen oder
#                                      stürzt er ab, kommt der Simulator von selbst zurück.
#   hp_knoepfe.sh zurueck              (Ctrl+Alt+Z, Leiste) den Browser schliessen, zurück zum Simulator
#   hp_knoepfe.sh koppeln              Fenster «Controller koppeln» (wie Ctrl+Alt+B)
# Status für den Simulator (nur Daten): /run/moveeye-spiel/browser_status.json {"schritt": offen | zu | test | kein_browser, "t"}
set -u
LIB="${MW_HPK_LIB:-/usr/local/lib/moveeye-kiosk}"
SPIEL_DIR="${MW_HPK_SPIEL_DIR:-/run/moveeye-spiel}"
PAUSE_DATEI="/run/moveeye-test/kiosk_pause"
PAUSE_MAX_S=25200
# shellcheck source=/dev/null
[ -z "${MW_HPK_PAUSE:-}" ] && [ -r /etc/moveeye-kiosk-test.conf ] && . /etc/moveeye-kiosk-test.conf
PAUSE_DATEI="${MW_HPK_PAUSE:-$PAUSE_DATEI}"
RUNNER="${MW_HPK_RUNNER:-mwrunner}"
BROWSER_DIR="${MW_HPK_BROWSER_DIR:-$HOME/MoveEye-Browser}"       # sichtbarer Ordner: auch ein Firefox als Snap darf dort hinein
EFI="${MW_HPK_EFI:-/sys/firmware/efi}"
LOGDIR="${MW_HPK_LOGDIR:-$HOME/.moveeye_kiosk}"
RUN="${XDG_RUNTIME_DIR:-/tmp}/moveeye-kiosk-$(id -u)"
MUSTER="${MW_HPK_SIM_MUSTER:-^([^ ]*/)?MoveEyeSim3D\\.x86_64( |\$)}"   # der Simulator des Kiosks (wie kiosk_sitzung.sh)
BROWSER_LISTE="${MW_HPK_BROWSER:-firefox firefox-esr chromium chromium-browser}"
HP_FASSUNG=8
MARKE="$SPIEL_DIR/browser_offen"
ZU="$SPIEL_DIR/browser_zu"
STATUS="$SPIEL_DIR/browser_status.json"

log() { mkdir -p "$LOGDIR" 2>/dev/null; printf '%s %s\n' "$(date '+%F %T')" "$*" >> "$LOGDIR/knoepfe.log" 2>/dev/null; }

pausiert() {   # Pause-Datei des Test-Runners da und nicht zu alt (wie kiosk_sitzung.sh)
	[ -f "$PAUSE_DATEI" ] || return 1
	local m
	m=$(stat -c %Y "$PAUSE_DATEI" 2>/dev/null) || return 1
	[ $(( $(date +%s) - m )) -lt "$PAUSE_MAX_S" ]
}
test_laeuft() {   # ein Test rechnet (Pause-Datei) oder ein Job des Runners ist unterwegs (auch wenn er gerade wartet)
	pausiert && return 0
	id "$RUNNER" >/dev/null 2>&1 && pgrep -u "$RUNNER" -f 'Runner\.Worker' >/dev/null 2>&1
}
browser_finden() {   # der erste Browser, der schon installiert ist (nichts wird nachinstalliert)
	local b
	for b in $BROWSER_LISTE; do
		command -v "$b" 2>/dev/null && return 0
	done
	return 1
}
bios_geht() {   # kann dieser PC direkt ins BIOS neu starten? (UEFI gestartet und logind sagt nicht «na»)
	[ -d "$EFI" ] || return 1
	command -v busctl >/dev/null 2>&1 || return 1
	timeout 5 busctl call org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager CanRebootToFirmwareSetup 2>/dev/null \
		| grep -qE '"(yes|challenge)"'
}
aus_bereit() { [ -d "$SPIEL_DIR" ] && [ -w "$SPIEL_DIR" ] && systemctl is-active -q moveeye-aus.path 2>/dev/null; }
ja() { if "$@"; then printf true; else printf false; fi; }
status() { printf '{"schritt": "%s", "t": %d}\n' "$1" "$(date +%s)" > "$STATUS.neu" 2>/dev/null && mv -f "$STATUS.neu" "$STATUS" 2>/dev/null; }
sim_signal() { pkill "-$1" -u "$(id -u)" -f "$MUSTER" 2>/dev/null; return 0; }

info() {
	local b
	b="$(browser_finden)" || b=""
	printf '{"fassung": %d, "test": %s, "aus": %s, "bios": %s, "browser": "%s", "koppeln": %s}\n' "$HP_FASSUNG" "$(ja test_laeuft)" \
		"$(ja aus_bereit)" "$(ja bios_geht)" "$(basename "${b:-}" | tr -cd 'a-z-')" "$(ja test -r "$LIB/controller_fenster.py")"
}

aus() {   # nur die leere Wunsch-Datei; ausgeschaltet wird vom Dienst moveeye-aus
	case "${1:-}" in herunterfahren|neustart|bios) ;; *) echo "aus: herunterfahren, neustart oder bios"; return 2 ;; esac
	[ -d "$SPIEL_DIR" ] || { echo "Ordner $SPIEL_DIR fehlt (moveeye-hp-update)"; return 1; }
	rm -f -- "$SPIEL_DIR/aus_$1" 2>/dev/null
	( set -C; : > "$SPIEL_DIR/aus_$1" ) 2>/dev/null || { echo "Wunsch nicht angelegt"; return 1; }
	log "Ausschalten gewünscht: $1$(test_laeuft && echo ' (ein Test läuft)')"
	echo "ok"
}

profil_schreiben() {   # Firefox: eigenes Profil - nichts merken, was Zugang gibt; Downloads in den eigenen Ordner
	local dl="${BROWSER_DIR//\\/\\\\}/Downloads"
	dl="${dl//\"/\\\"}"
	cat > "$BROWSER_DIR/profil/user.js" <<EOF
// MoveEye Kiosk (hp_knoepfe.sh): wird bei jedem Start des Browsers neu geschrieben.
user_pref("browser.download.dir", "$dl");
user_pref("browser.download.folderList", 2);
user_pref("browser.download.useDownloadDir", true);
user_pref("browser.download.always_ask_before_handling_new_types", true);
user_pref("signon.rememberSignons", false);
user_pref("signon.autofillForms", false);
user_pref("signon.management.page.breach-alerts.enabled", false);
user_pref("extensions.formautofill.creditCards.enabled", false);
user_pref("extensions.formautofill.addresses.enabled", false);
user_pref("identity.fxaccounts.enabled", false);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("browser.tabs.warnOnClose", false);
user_pref("browser.warnOnQuit", false);
user_pref("browser.tabs.inTitlebar", 1);
user_pref("network.protocol-handler.external-default", false);
user_pref("dom.security.https_only_mode", true);
EOF
}

BP=0 LP=0
browser_ende() {   # (trap EXIT) Browser und Leiste zu, Simulator weiter, Marken weg - auch nach einem Absturz
	trap - EXIT TERM INT HUP
	if [ "$BP" -gt 0 ]; then
		pkill -TERM -s "$BP" 2>/dev/null; kill -TERM "$BP" 2>/dev/null
		local i
		for i in 1 2 3 4 5 6 7 8 9 10; do
			pgrep -s "$BP" >/dev/null 2>&1 || break
			sleep 0.5; : "$i"
		done
		pkill -KILL -s "$BP" 2>/dev/null
	fi
	[ "$LP" -gt 0 ] && kill -TERM "$LP" 2>/dev/null
	sim_signal CONT
	rm -f -- "$MARKE" "$ZU" 2>/dev/null
	status zu
	log "Browser zu - zurück zum Simulator"
}

browser() {
	local b n=0 art
	mkdir -p "$RUN" 2>/dev/null
	exec 8> "$RUN/browser.lock"
	flock -n 8 || { echo "Der Browser ist schon offen."; return 0; }
	if test_laeuft; then status test; log "Browser: es läuft ein Test - nicht geöffnet"; echo "test"; return 3; fi
	b="$(browser_finden)" || { status kein_browser; log "Browser: keiner installiert"; echo "kein_browser"; return 4; }
	if [ ! -d "$SPIEL_DIR" ] || [ ! -w "$SPIEL_DIR" ]; then echo "Ordner $SPIEL_DIR fehlt"; return 1; fi
	( umask 077; mkdir -p "$BROWSER_DIR/profil" "$BROWSER_DIR/Downloads" ) || { echo "Ordner $BROWSER_DIR geht nicht"; return 1; }
	chmod 700 "$BROWSER_DIR" "$BROWSER_DIR/profil" 2>/dev/null
	rm -f -- "$ZU" 2>/dev/null
	: > "$MARKE"
	status offen
	trap browser_ende EXIT
	trap 'exit 0' TERM INT HUP
	art="$(basename "$b")"
	log "Browser öffnet ($art, Profil $BROWSER_DIR/profil)"
	if [ -r "$LIB/browser_leiste.py" ] && python3 -c 'import tkinter' 2>/dev/null; then
		python3 -I "$LIB/browser_leiste.py" --zu "$ZU" >> "$LOGDIR/browser.log" 2>&1 8>&- &
		LP=$!
	fi
	case "$art" in
		firefox*)
			profil_schreiben
			setsid "$b" --no-remote --profile "$BROWSER_DIR/profil" >> "$LOGDIR/browser.log" 2>&1 8>&- & ;;
		*)
			setsid "$b" --user-data-dir="$BROWSER_DIR/profil" --no-first-run --no-default-browser-check \
				--password-store=basic >> "$LOGDIR/browser.log" 2>&1 8>&- & ;;
	esac
	BP=$!
	while kill -0 "$BP" 2>/dev/null || pgrep -s "$BP" >/dev/null 2>&1; do
		[ -e "$ZU" ] && break                                # «Zurück zum Simulator» (Leiste, Ctrl+Alt+Z)
		if pausiert; then log "Ein Test beginnt - Browser wird geschlossen"; break; fi
		[ $n -eq 4 ] && sim_signal STOP                      # nach 2 s (das Browser-Fenster ist da): Simulator anhalten
		[ $((n % 10)) -eq 0 ] && touch "$MARKE"              # Puls für hp_wache.py: «es wird gespielt»
		n=$((n + 1))
		sleep 0.5
	done
	return 0                                                 # browser_ende räumt auf (trap EXIT)
}

case "${1:-}" in
	info) info ;;
	aus) aus "${2:-}" ;;
	browser) browser ;;
	zurueck) [ -e "$MARKE" ] && : > "$ZU"; sim_signal CONT ;;
	koppeln)
		if [ -r "$LIB/controller_fenster.py" ]; then
			python3 -I "$LIB/controller_fenster.py" --wunsch "$SPIEL_DIR/controller_koppeln" >> "$LOGDIR/controller.log" 2>&1 &
		else
			echo "controller_fenster.py fehlt"; exit 1
		fi ;;
	*) sed -n '2,20p' "$0"; exit 2 ;;
esac
