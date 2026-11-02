#!/bin/bash
# MoveEye Test-Runner EINRICHTEN - der Simulator-PC rechnet die langen Tests (Erkennung, Prüfstand) für GitHub Actions.
#   sudo bash runner_einrichten.sh               fragt einmal «Fortfahren? (j/n)» und den Registrierungs-Token, richtet alles ein
#   sudo bash runner_einrichten.sh --bildschirm  dazu: Tests dürfen den Bildschirm (Grafikkarte) benutzen, solange sie laufen
#   Optionen: --ja (ohne Rückfrage), --name NAME (Standard moveeye-hp), --zweig ZWEIG (woher kiosk_sitzung.sh und
#   runner_entfernen.sh kommen, Standard main), --hilfe
# Was passiert: eigener Benutzer «mwrunner» (ohne sudo), GitHub-Runner (actions-runner, Linux x64) in /var/lib/mwrunner,
# als systemd-Dienst; Labels self-hosted, linux, x64, moveeye-hp; Pakete für die Tests (Python wie im CI, Xvfb); Haken vor /
# nach jedem Job (Kiosk-Simulator pausieren, Arbeitsordner aufräumen). Der Token wird nie gespeichert.
# Rückgängig: sudo bash /usr/local/lib/moveeye-runner/runner_entfernen.sh   Anleitung: werkzeuge/test_runner/ANLEITUNG.md
set -u
REPO="DonElektro/MotionWatch"
REPO_URL="https://github.com/$REPO"
RU="mwrunner"                                   # der Benutzer, unter dem die Tests laufen
RH="/var/lib/mwrunner"                          # sein Zuhause: runner/, venv/, cache/
RD="$RH/runner"
LIB="/usr/local/lib/moveeye-runner"             # Haken und runner_entfernen.sh (gehören root, der Runner kann sie nicht ändern)
CONF="/etc/moveeye-runner.conf"
PAUSE_DIR="/run/moveeye-test"
PAUSE="$PAUSE_DIR/kiosk_pause"
TMPFILES="/etc/tmpfiles.d/moveeye-test.conf"
KIOSK_LIB="/usr/local/lib/moveeye-kiosk"
KIOSK_TEST="/etc/moveeye-kiosk-test.conf"
LABELS="self-hosted,linux,x64,moveeye-hp"
NAME="moveeye-hp"
ZWEIG="main"
JA=0 BILDSCHIRM=0
HIER="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

while [ $# -gt 0 ]; do
	case "$1" in
		--ja|-y) JA=1 ;;
		--bildschirm) BILDSCHIRM=1 ;;
		--name) shift; NAME="${1:-}" ;;
		--zweig) shift; ZWEIG="${1:-main}" ;;
		-h|--hilfe|--help) sed -n '2,10p' "$0"; exit 0 ;;
		*) echo "Unbekannte Option: $1 (--ja, --bildschirm, --name, --zweig, --hilfe)"; exit 2 ;;
	esac
	shift
done
[[ "$NAME" =~ ^[A-Za-z0-9._-]{1,64}$ ]] || { echo "Ungültiger Name: $NAME"; exit 2; }
[[ "$ZWEIG" =~ ^[A-Za-z0-9._/-]{1,100}$ ]] || { echo "Ungültiger Zweig: $ZWEIG"; exit 2; }
RAW="https://raw.githubusercontent.com/$REPO/$ZWEIG"

if [ "$(id -u)" -ne 0 ]; then echo "Bitte mit sudo starten: sudo bash $0"; exit 1; fi
[ "$(uname -m)" = x86_64 ] || { echo "Nur für Linux x64 (dieser PC: $(uname -m))"; exit 1; }
command -v systemctl >/dev/null || { echo "systemd fehlt - abgebrochen."; exit 1; }
WER="${SUDO_USER:-root}"

cat <<EOF
=== MoveEye Test-Runner EINRICHTEN ===
Repository: $REPO_URL    Runner: $NAME    Labels: $LABELS
Das passiert:
 1. Pakete: Python (opencv, numpy, flask, pillow, cryptography, psutil), Xvfb, Bibliotheken für den Simulator, git, curl
 2. Benutzer «$RU» (Systembenutzer, kein sudo, keine Anmeldung), Ordner $RH
 3. GitHub-Runner (neuste Version, Prüfsumme) nach $RD, Python-Umgebung $RH/venv
 4. Haken vor / nach jedem Job: Kiosk-Simulator pausieren und wieder starten, Arbeitsordner aufräumen ($LIB)
 5. Kiosk: Pause-Funktion (kiosk_sitzung.sh neu)$( [ $BILDSCHIRM -eq 1 ] && echo ", Bildschirm für $RU freigegeben (Grafikkarte)" )
 6. Token abfragen (wird nicht gespeichert), Runner bei GitHub anmelden, Dienst einrichten und starten
Nur Jobs aus Workflow-Läufen von Hand, nach Zeitplan oder Push auf main (Stand main) laufen hier - nie Pull-Requests.
Rückgängig: sudo bash $LIB/runner_entfernen.sh
EOF
if [ $JA -eq 0 ]; then
	read -r -p "Fortfahren? (j/n) " antwort
	case "$antwort" in j|J|ja|Ja|JA|y|Y) ;; *) echo "Abgebrochen - nichts geändert."; exit 0 ;; esac
fi

FEHLER=0
schritt() { echo; echo "--- $*"; }
warn() { echo "  WARNUNG: $*"; FEHLER=$((FEHLER + 1)); }
als_ru() { (cd "$RH" 2>/dev/null || cd /; sudo -u "$RU" -H -- "$@"); }
beilage() {   # beilage ZIEL QUELLE_IM_REPO MODUS: aus dem Repository neben diesem Skript, sonst von GitHub ($ZWEIG)
	local ziel="$1" rel="$2" modus="$3" tmp
	tmp="$(mktemp)"
	if [ -r "$HIER/../../$rel" ]; then
		cp "$HIER/../../$rel" "$tmp"
	elif ! curl -fsSL --retry 3 -o "$tmp" "$RAW/$rel"; then
		rm -f "$tmp"; warn "$rel nicht geladen ($RAW)"; return 1
	fi
	head -n 1 "$tmp" | grep -q '^#!/bin/bash' || { rm -f "$tmp"; warn "$rel ist kein Skript"; return 1; }
	install -D -m "$modus" -o root -g root "$tmp" "$ziel"; rm -f "$tmp"
	echo "  $ziel"
}

# --- 1. Pakete
schritt "1. Pakete"
PAKETE="ca-certificates curl git tar unzip xvfb x11-xserver-utils python3 python3-venv python3-pip python3-numpy python3-opencv
python3-flask python3-pil python3-cryptography python3-psutil libgl1 libgl1-mesa-dri libglu1-mesa libxcursor1 libxinerama1
libxrandr2 libxi6 libasound2t64"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q || warn "apt-get update"
# shellcheck disable=SC2086
if ! apt-get install -y -q --no-install-recommends $PAKETE; then
	echo "  einzeln versuchen …"
	for p in $PAKETE; do apt-get install -y -q --no-install-recommends "$p" >/dev/null 2>&1 || warn "Paket $p fehlt"; done
fi

# --- 2. Benutzer
schritt "2. Benutzer «$RU»"
if id "$RU" >/dev/null 2>&1; then
	echo "  schon da"
else
	useradd --system --user-group --create-home --home-dir "$RH" --shell /usr/sbin/nologin \
		--comment "MoveEye Test-Runner (GitHub Actions)" "$RU" || { echo "useradd fehlgeschlagen - abgebrochen"; exit 1; }
	echo "  angelegt (Systembenutzer, ohne Passwort, ohne Anmeldung)"
fi
passwd -l "$RU" >/dev/null 2>&1 || true
for g in sudo admin wheel adm lxd docker; do
	if id -nG "$RU" | tr ' ' '\n' | grep -qx "$g"; then gpasswd -d "$RU" "$g" >/dev/null && echo "  aus Gruppe $g entfernt"; fi
done
if sudo -l -U "$RU" 2>/dev/null | grep -q "may run"; then warn "$RU darf sudo benutzen (sudoers-Eintrag?) - bitte entfernen"; fi
if [ $BILDSCHIRM -eq 1 ]; then
	for g in video render; do getent group "$g" >/dev/null && usermod -aG "$g" "$RU"; done
	echo "  Gruppen video, render (Grafikkarte)"
fi
install -d -m 750 -o "$RU" -g "$RU" "$RH" "$RH/cache"

# --- 3. Runner und Python
schritt "3. GitHub-Runner"
NEU=1
if [ -f "$RD/.runner" ]; then
	echo "  Runner ist schon angemeldet ($(sed -n 's/.*"agentName": *"\([^"]*\)".*/\1/p' "$RD/.runner" | head -n 1))."
	if [ $JA -eq 1 ]; then antwort=n; else read -r -p "  Neu anmelden (neuer Token nötig)? (j/n) " antwort; fi
	case "$antwort" in
		j|J|ja|Ja|JA|y|Y)
			if [ -f "$RD/.service" ]; then (cd "$RD" && ./svc.sh stop; ./svc.sh uninstall) >/dev/null 2>&1; fi
			rm -f "$RD/.runner" "$RD/.credentials" "$RD/.credentials_rsaparams" "$RD/.service" ;;
		*) NEU=0; echo "  bleibt angemeldet (nur Haken, Pakete und Python werden erneuert)" ;;
	esac
fi
if [ $NEU -eq 1 ]; then
	INFO="$(curl -fsSL --retry 3 https://api.github.com/repos/actions/runner/releases/latest)" || { echo "GitHub nicht erreichbar - abgebrochen"; exit 1; }
	VER="$(printf '%s' "$INFO" | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))')"
	SHA="$(printf '%s' "$INFO" | python3 -c 'import json,re,sys
b = json.load(sys.stdin).get("body") or ""
m = re.search(r"BEGIN SHA linux-x64 -->\s*([0-9a-f]{64})", b)
print(m.group(1) if m else "")')"
	[[ "$VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Runner-Version unbekannt ($VER) - abgebrochen"; exit 1; }
	DATEI="actions-runner-linux-x64-$VER.tar.gz"
	TMP="$(mktemp -d)"; chmod 755 "$TMP"
	echo "  lade $DATEI"
	curl -fsSL --retry 3 -o "$TMP/$DATEI" "https://github.com/actions/runner/releases/download/v$VER/$DATEI" || { rm -rf "$TMP"; echo "Download fehlgeschlagen"; exit 1; }
	if [ -n "$SHA" ]; then
		echo "$SHA  $TMP/$DATEI" | sha256sum -c --quiet || { rm -rf "$TMP"; echo "Prüfsumme falsch - abgebrochen"; exit 1; }
		echo "  Prüfsumme stimmt"
	else
		warn "keine Prüfsumme in den Release-Angaben gefunden"
		if [ $JA -eq 0 ]; then
			read -r -p "  Trotzdem weiter? (j/n) " antwort
			case "$antwort" in j|J|ja|Ja|JA|y|Y) ;; *) rm -rf "$TMP"; echo "Abgebrochen."; exit 1 ;; esac
		fi
	fi
	chmod 644 "$TMP/$DATEI"
	install -d -m 750 -o "$RU" -g "$RU" "$RD"
	als_ru tar xzf "$TMP/$DATEI" -C "$RD" || { rm -rf "$TMP"; echo "Entpacken fehlgeschlagen"; exit 1; }
	rm -rf "$TMP"
	echo "  Runner $VER in $RD"
	if ! "$RD/bin/installdependencies.sh" >/dev/null 2>&1; then
		echo "  installdependencies.sh ging nicht - Bibliotheken von Hand"
		ICU="$(apt-cache search --names-only '^libicu[0-9]+$' 2>/dev/null | awk '{print $1}' | sort -V | tail -n 1)"
		for p in ${ICU:-libicu-dev} libkrb5-3 zlib1g liblttng-ust1t64 libssl3t64; do
			apt-get install -y -q --no-install-recommends "$p" >/dev/null 2>&1 || echo "  ($p nicht installiert)"
		done
	fi
fi
schritt "3b. Python-Umgebung $RH/venv (Pakete wie im CI)"
[ -x "$RH/venv/bin/python" ] || als_ru python3 -m venv --system-site-packages "$RH/venv" || warn "venv"
if [ -x "$RH/venv/bin/python" ]; then
	als_ru "$RH/venv/bin/python" -m pip install -q --upgrade opencv-python-headless numpy flask pillow cryptography psutil \
		|| echo "  pip ging nicht - es gelten die Pakete von Ubuntu (python3-opencv usw.)"
	als_ru "$RH/venv/bin/python" -c "import cv2, numpy, flask, PIL, cryptography, psutil; print('  Python', __import__('sys').version.split()[0], 'opencv', cv2.__version__)" \
		|| warn "Python-Pakete fehlen"
fi

# --- 4. Haken und Einstellungen
schritt "4. Haken vor / nach jedem Job ($LIB)"
install -d -m 755 -o root -g root "$LIB"
cat > "$LIB/job_start.sh" <<'HAKEN'
#!/bin/bash
# MoveEye Test-Runner: vor jedem Job (ACTIONS_RUNNER_HOOK_JOB_STARTED), als Benutzer mwrunner. Gehört root.
# Lässt nur erlaubte Anlässe zu (nie Pull-Requests), pausiert den Kiosk-Simulator (Pause-Datei, kiosk_sitzung.sh).
set -u
ERLAUBTE_REFS="refs/heads/main"
# shellcheck source=/dev/null
[ -r /etc/moveeye-runner.conf ] && . /etc/moveeye-runner.conf
P="${MW_KIOSK_PAUSE:-/run/moveeye-test/kiosk_pause}"
echo "MoveEye-Runner: ${GITHUB_REPOSITORY:-?} · ${GITHUB_WORKFLOW:-?} · Anlass ${GITHUB_EVENT_NAME:-?} · ${GITHUB_REF:-?}"
# zweite Sperre neben den Workflows selbst (fehlen die Angaben, nur warnen - der Runner gehört ohnehin nur zu diesem Repository)
case "${GITHUB_REPOSITORY:-}" in
	DonElektro/MotionWatch) ;;
	"") echo "Hinweis: GITHUB_REPOSITORY fehlt" ;;
	*) echo "::error::Fremdes Repository - abgelehnt"; exit 1 ;;
esac
case "${GITHUB_EVENT_NAME:-}" in
	workflow_dispatch|schedule|push) ;;
	"") echo "Hinweis: GITHUB_EVENT_NAME fehlt" ;;
	*) echo "::error::Anlass «${GITHUB_EVENT_NAME}» ist auf diesem Runner nicht erlaubt (nur von Hand, Zeitplan, Push auf main)"; exit 1 ;;
esac
if [ -n "${GITHUB_REF:-}" ]; then
	ok=0
	for r in $ERLAUBTE_REFS; do [ "$GITHUB_REF" = "$r" ] && ok=1; done
	[ $ok -eq 1 ] || { echo "::error::Workflows laufen hier nur vom Stand ${ERLAUBTE_REFS} (jetzt $GITHUB_REF)"; exit 1; }
fi
fremder_sim() { ps -eo uid=,comm= | awk -v me="$(id -u)" '$1 != me && $2 ~ /^MoveEyeSim3D/ {n++} END {exit n ? 0 : 1}'; }
if [ -d "$(dirname "$P")" ] && [ -w "$(dirname "$P")" ]; then
	printf 'Lauf %s %s\n' "${GITHUB_RUN_ID:-?}" "$(date '+%F %T')" > "$P"
	echo "Kiosk-Simulator: Pause angefordert"
	i=0
	while fremder_sim && [ $i -lt 30 ]; do sleep 2; i=$((i + 1)); done
	if fremder_sim; then echo "Hinweis: der Kiosk-Simulator läuft noch (kiosk_sitzung.sh ohne Pause? runner_einrichten.sh noch einmal, dann neu starten)"
	else echo "Kiosk-Simulator ist aus"; fi
else
	echo "Hinweis: $(dirname "$P") fehlt - der Kiosk läuft weiter (runner_einrichten.sh noch einmal)"
fi
echo "Speicher: $(free -m | awk '/^Mem/ {print $7 " MB frei von " $2}') · Platz: $(df -h "${MW_RUNNER_HOME:-/var/lib/mwrunner}" | awk 'NR==2 {print $4}') frei"
exit 0
HAKEN
cat > "$LIB/job_ende.sh" <<'HAKEN'
#!/bin/bash
# MoveEye Test-Runner: nach jedem Job (ACTIONS_RUNNER_HOOK_JOB_COMPLETED), als Benutzer mwrunner. Gehört root.
# Kiosk-Simulator wieder starten (Pause-Datei weg), Arbeitsordner und Reste des Jobs aufräumen.
set -u
P="${MW_KIOSK_PAUSE:-/run/moveeye-test/kiosk_pause}"
rm -f -- "$P" && echo "Kiosk-Simulator: Pause beendet"
BASIS="${MW_RUNNER_HOME:-/var/lib/mwrunner}/runner/_work/"
W="${GITHUB_WORKSPACE:-}"
case "$W" in
	"$BASIS"?*) [ -d "$W" ] && find "$W" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + && echo "Arbeitsordner geleert: $W" ;;
esac
# Reste von Prüfstand / Erkennungstest dieses Benutzers in /tmp (nur die eigenen, nur diese Namen)
find /tmp -maxdepth 1 -user "$(id -u)" \( -name 'mw_pruefstand_*' -o -name 'mw_erk_lauf_*' -o -name 'mw_erkennung_*' \) \
	-exec rm -rf -- {} + 2>/dev/null
echo "Platz: $(df -h "${MW_RUNNER_HOME:-/var/lib/mwrunner}" | awk 'NR==2 {print $4}') frei"
exit 0
HAKEN
chmod 755 "$LIB/job_start.sh" "$LIB/job_ende.sh"
chown root:root "$LIB/job_start.sh" "$LIB/job_ende.sh"
echo "  $LIB/job_start.sh, $LIB/job_ende.sh"
beilage "$LIB/runner_entfernen.sh" werkzeuge/test_runner/runner_entfernen.sh 755 || true
if [ ! -f "$CONF" ]; then
	cat > "$CONF" <<'EOF'
# MoveEye Test-Runner (runner_einrichten.sh). Von welchem Stand Workflows auf diesem PC laufen dürfen (mit Leerzeichen).
# Welcher Code getestet wird, wählt der Workflow selbst (Eingabe «stand», nur Zweige dieses Repositorys).
ERLAUBTE_REFS="refs/heads/main"
EOF
	chmod 644 "$CONF"
fi
printf 'd %s 0755 %s %s -\n' "$PAUSE_DIR" "$RU" "$RU" > "$TMPFILES"
systemd-tmpfiles --create "$TMPFILES" || warn "systemd-tmpfiles"
echo "  Pause-Datei: $PAUSE (Ordner gehört $RU)"

# --- 5. Kiosk
schritt "5. Kiosk"
if [ -d "$KIOSK_LIB" ]; then
	[ -f "$KIOSK_LIB/kiosk_sitzung.sh" ] && [ ! -f "$LIB/kiosk_sitzung.sh.vorher" ] && cp -p "$KIOSK_LIB/kiosk_sitzung.sh" "$LIB/kiosk_sitzung.sh.vorher"
	beilage "$KIOSK_LIB/kiosk_sitzung.sh" simulator3d/beilagen_linux/kiosk_sitzung.sh 755 && echo "  kiosk_sitzung.sh mit Pause-Funktion"
else
	echo "  Kein Kiosk eingerichtet ($KIOSK_LIB fehlt) - nur die Pause-Einstellung wird hinterlegt."
fi
{
	echo "# MoveEye Kiosk: Pause für Testläufe (runner_einrichten.sh, $(date '+%F %T')). Entfernen: runner_entfernen.sh"
	echo "PAUSE_DATEI=$PAUSE"
	echo "PAUSE_MAX_S=25200"
	if [ $BILDSCHIRM -eq 1 ]; then echo "TEST_BENUTZER=$RU"; else echo "TEST_BENUTZER=\"\""; fi
} > "$KIOSK_TEST"
chmod 644 "$KIOSK_TEST"
echo "  $KIOSK_TEST$( [ $BILDSCHIRM -eq 1 ] && echo " (Bildschirm für $RU freigegeben)" )"

# --- 6. Anmelden bei GitHub, Dienst
schritt "6. Bei GitHub anmelden"
if [ $NEU -eq 1 ]; then
	cat <<EOF
  Token holen (gilt 1 Stunde): auf GitHub $REPO_URL → Settings → Actions → Runners →
  «New self-hosted runner» → Linux, x64. Im Abschnitt «Configure» steht «./config.sh --url … --token XXXX»:
  nur XXXX kopieren (am einfachsten per SSH von einem anderen PC aus einfügen).
EOF
	TOKEN=""
	for _ in 1 2 3; do
		read -r -s -p "  Token (Eingabe bleibt unsichtbar): " TOKEN < /dev/tty; echo
		TOKEN="$(printf '%s' "$TOKEN" | tr -d '[:space:]')"
		[[ "$TOKEN" =~ ^[A-Za-z0-9_-]{20,200}$ ]] && break
		echo "  Das sieht nicht wie ein Token aus - noch einmal."; TOKEN=""
	done
	[ -n "$TOKEN" ] || { echo "Kein Token - abgebrochen. Später einfach dieses Skript noch einmal starten."; exit 1; }
	# Token über die Standardeingabe weitergeben (nicht als Argument: sonst sähe ihn «ps»); config.sh liest ACTIONS_RUNNER_INPUT_TOKEN
	if printf '%s\n' "$TOKEN" | sudo -u "$RU" -H -- bash -c 'cd "$1" || exit 1; IFS= read -r t; export ACTIONS_RUNNER_INPUT_TOKEN="$t"; unset t
		exec ./config.sh --unattended --url "$2" --name "$3" --labels "$4" --no-default-labels --work _work --replace' \
		_ "$RD" "$REPO_URL" "$NAME" "$LABELS"; then
		echo "  angemeldet als «$NAME»"
	else
		TOKEN=""; echo "Anmelden fehlgeschlagen (Token abgelaufen oder falsch?) - neuen Token holen und dieses Skript noch einmal starten."; exit 1
	fi
	TOKEN=""; unset TOKEN
fi
# Einstellungen für die Jobs: Haken, Python, Pause-Datei (Datei .env des Runners, wird beim Start gelesen)
ENVF="$RD/.env"
touch "$ENVF"
for kv in "ACTIONS_RUNNER_HOOK_JOB_STARTED=$LIB/job_start.sh" "ACTIONS_RUNNER_HOOK_JOB_COMPLETED=$LIB/job_ende.sh" \
	"MW_RUNNER_HOME=$RH" "MW_RUNNER_PY=$RH/venv/bin/python" "MW_KIOSK_PAUSE=$PAUSE"; do
	k="${kv%%=*}"
	grep -v "^$k=" "$ENVF" > "$ENVF.neu" || true
	echo "$kv" >> "$ENVF.neu"
	mv -f "$ENVF.neu" "$ENVF"
done
chown "$RU:$RU" "$ENVF"; chmod 640 "$ENVF"

schritt "6b. Dienst"
if [ ! -f "$RD/.service" ]; then
	(cd "$RD" && ./svc.sh install "$RU") || { echo "svc.sh install fehlgeschlagen"; exit 1; }
fi
UNIT="$(cat "$RD/.service" 2>/dev/null)"
[ -n "$UNIT" ] || { echo "Dienstname unbekannt ($RD/.service fehlt)"; exit 1; }
install -d -m 755 "/etc/systemd/system/$UNIT.d"
cat > "/etc/systemd/system/$UNIT.d/moveeye.conf" <<'EOF'
# MoveEye Test-Runner (runner_einrichten.sh): Schutz und Grenzen. 4 GB RAM: höchstens etwa 3,4 GB für die Tests.
[Service]
NoNewPrivileges=yes
ProtectSystem=full
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
# RestrictSUIDSGID weggelassen: sperrt openat2 (Ubuntu 26.04), dann kann tar nichts entpacken. NoNewPrivileges deckt SUID ab.
LockPersonality=yes
MemoryHigh=3G
MemoryMax=3400M
Nice=5
EOF
systemctl daemon-reload
systemctl enable "$UNIT" >/dev/null 2>&1
systemctl restart "$UNIT" || warn "Dienst startet nicht (journalctl -u $UNIT)"
sleep 5
if systemctl is-active -q "$UNIT"; then echo "  Dienst $UNIT läuft"; else warn "Dienst $UNIT läuft nicht"; fi

schritt "Fertig"
[ "$FEHLER" -gt 0 ] && echo "ACHTUNG: $FEHLER Warnung(en) - siehe oben."
cat <<EOF
Prüfen: GitHub → Settings → Actions → Runners: «$NAME» steht dort als «Idle» (grün).
Hier:   systemctl status $UNIT
Kiosk:  einmal neu starten (sudo reboot), damit die Pause-Funktion im Kiosk gilt.
Sicherheit: in den Repository-Einstellungen Actions → General → «Fork pull request workflows from outside collaborators»
        auf «Require approval for all outside collaborators» stellen (ANLEITUNG.md).
Rückgängig: sudo bash $LIB/runner_entfernen.sh   (eingerichtet von $WER)
EOF
[ "$FEHLER" -eq 0 ]
