#!/bin/bash
# MoveEye HP-Update - hält den Simulator-PC (HP: Kiosk und Test-Runner) aktuell, nur mit SIGNIERTEN Versionen.
#   sudo moveeye-hp-update                  neueste signierte Version holen, prüfen, einspielen (sofort, von Hand)
#   moveeye-hp-update --zeitplan            so startet es der Dienst moveeye-hp-update (Zeitplan: alle 15 Min. und 8 Min.
#                                           nach jedem Start): nur in einer Pause - nie, während der HP rechnet oder jemand
#                                           spielt - und nur, wenn die letzte Prüfung über 6 Std. her ist (sonst still fertig)
#   sudo bash hp_update.sh --einrichten     sich selbst als /usr/local/sbin/moveeye-hp-update einrichten (Dienst, Zeitplan),
#                                           danach einmal laufen lassen (--ohne-lauf: nur einrichten)
#   moveeye-hp-update --pruefen             nur laden und prüfen (Signatur, Prüfsummen), nichts einspielen (geht ohne sudo)
#   moveeye-hp-update --immer               auch einspielen, wenn diese Version schon eingespielt ist
#   moveeye-hp-update --status              eingespielte Version, Zeitplan, letzte Zeilen des Protokolls
#   moveeye-hp-update --entfernen           Dienst und Zeitplan entfernen (eingespielte Dateien bleiben)
# Prüfkette (dieselbe wie beim Pi, nichts Neues zu signieren): versions.json -> Eintrag mit gültiger Ed25519-Signatur über
# «MotionWatch|Version|Datei|SHA-256» (öffentlicher Schlüssel wie im Programm, Teil 380). Drei Spuren (HP_FASSUNG 3): der
# Simulator hat eine eigene Nummer und steht als Block «sim» in versions.json, das Linux-Paket mit eigener Signatur über
# «MotionWatch|Sim-Version|simulator3d/MoveEyeSim3D_Linux.zip|SHA-256» -> MoveEyeSim3D_Linux.zip mit genau dieser SHA-256.
# Ohne gültigen Block «sim» (Listen von vor den drei Spuren) wie bisher: webcam_bewegung_X_Y_Z.py mit der signierten SHA-256
# -> darin SIM3D_LINUX (Teil 300) -> Linux-ZIP. Im Paket: kiosk_sitzung.sh, testbild.py, hp/ (dieses Skript, Haken,
# Dienst-Einstellungen). Stimmt etwas nicht, wird nichts eingespielt. MoveEye- und Sim-Nummer werden je für sich gemerkt
# (ZUSTAND/version, ZUSTAND/sim_version); ältere als die eingespielten werden abgelehnt. Der geheime Schlüssel ist nie nötig.
# Spielt ein: Kiosk (kiosk_sitzung.sh, testbild.py, Logo), Haken und Dienst-Einstellungen des Test-Runners, fehlende Pakete,
# den Simulator im Ordner des Kiosks und sich selbst. Fasst die Anmeldung des Runners (Token, .runner, .credentials, .env)
# nie an. Läuft ein Test (Pause-Datei des Kiosks oder ein Job des Runners) oder wird gespielt, wird alles verschoben.
# Dauerrechnen (3.55.0): der HP rechnet rund um die Uhr; darum prüft der Zeitplan alle 15 Min., ob gerade eine Pause ist.
# Nach jeder Prüfung schreibt es /var/lib/moveeye-hp-update/letzter_lauf; ist der über 20 Std. alt, lässt das Dauerrechnen
# (werkzeuge/test_runner/dauer.py) den HP frei, bis das Update gelaufen ist - so kommt es mindestens einmal am Tag dran.
# Dazu: hp_wache.py (Spielen-Wunsch, Status fürs eigene Netz, Port 8761), Ordner /run/moveeye-spiel für den Benutzer des
# Kiosks, libxss1; ist die Firewall ufw an, Port 8761 nur fürs eigene Netz.
# Einstellungen: /etc/moveeye-hp-update.conf (SIMULATOR=nein: den Simulator nicht ersetzen). Protokoll: /var/log/moveeye-hp-update.log
set -u
REPO_RAW="${MOVEEYE_HP_QUELLE:-https://raw.githubusercontent.com/DonElektro/MotionWatch}"   # nur zum Prüfen änderbar
UPDATE_PUBKEY="91d5eab3ab9f6e092d78081ca511144235cb9b22b770c3b1047e011d978bd416"            # wie Teil 380 (UPDATE_PUBKEY)
SELBST="/usr/local/sbin/moveeye-hp-update"
DIENST="/etc/systemd/system/moveeye-hp-update.service"
ZEITPLAN="/etc/systemd/system/moveeye-hp-update.timer"
ZUSTAND="/var/lib/moveeye-hp-update"
LOG="/var/log/moveeye-hp-update.log"
CONF="/etc/moveeye-hp-update.conf"
KIOSK_LIB="/usr/local/lib/moveeye-kiosk"
KIOSK_CONF="/etc/moveeye-kiosk.conf"
RUNNER_LIB="/usr/local/lib/moveeye-runner"
RD="/var/lib/mwrunner/runner"
RU="mwrunner"
PAUSE="/run/moveeye-test/kiosk_pause"
SPIEL="/run/moveeye-spiel/spielen"
SPIEL_TMPFILES="/etc/tmpfiles.d/moveeye-spiel.conf"
HP_FASSUNG=3                     # 3 = drei Spuren (Sim aus versions.json «sim»); erhöhen, wenn dieses Skript bei gleicher Version mehr einspielt als die Fassung davor
STATUS_PORT=8761
# Pakete, die Kiosk und Testbild brauchen (nur fehlende werden installiert, nichts wird entfernt)
PAKETE="python3-tk x11-xserver-utils libxss1 unzip curl"
MUSTER='^([^ ]*/)?MoveEyeSim3D\.x86_64( |$)'

MODUS=lauf OHNE_LAUF=0 IMMER=0 PLANLAUF=0
for a in "$@"; do
	case "$a" in
		--einrichten) MODUS=einrichten ;;
		--ohne-lauf) OHNE_LAUF=1 ;;
		--pruefen) MODUS=pruefen ;;
		--immer) IMMER=1 ;;
		--zeitplan) PLANLAUF=1 ;;
		--status) MODUS=status ;;
		--entfernen) MODUS=entfernen ;;
		--einheiten) MODUS=einheiten ;;
		-h|--hilfe|--help) sed -n '2,13p' "$0"; exit 0 ;;
		*) echo "Unbekannte Option: $a (--einrichten, --ohne-lauf, --pruefen, --immer, --zeitplan, --status, --entfernen, --hilfe)"; exit 2 ;;
	esac
done

log() { printf '%s %s\n' "$(date '+%F %T')" "$*"; }
root_noetig() { [ "$(id -u)" -eq 0 ] || { echo "Bitte mit sudo starten: sudo $0 $*"; exit 1; }; }

# ------------------------------------------------------------------ Prüfen (Python, nur Standardbibliothek)
PRUEFER=""
pruefer_schreiben() {   # pruefer_schreiben DATEI: das Prüfprogramm (Ed25519 wie Teil 380, RFC 8032) ablegen
	PRUEFER="$1"
	cat > "$PRUEFER" <<'PY'
import hashlib, json, re, sys

def ed25519_verify(pub, msg, sig):
    p = 2 ** 255 - 19
    q = 2 ** 252 + 27742317777372353535851937790883648493
    d = -121665 * pow(121666, p - 2, p) % p
    I = pow(2, (p - 1) // 4, p)

    def add(P, Q):
        A = (P[1] - P[0]) * (Q[1] - Q[0]) % p; B = (P[1] + P[0]) * (Q[1] + Q[0]) % p
        C = 2 * P[3] * Q[3] * d % p; D = 2 * P[2] * Q[2] % p
        E, F, G, H = B - A, D - C, D + C, B + A
        return (E * F % p, G * H % p, F * G % p, E * H % p)

    def mul(s, P):
        Q = (0, 1, 1, 0)
        while s > 0:
            if s & 1:
                Q = add(Q, P)
            P = add(P, P); s >>= 1
        return Q

    def eq(P, Q):
        return (P[0] * Q[2] - Q[0] * P[2]) % p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % p == 0

    def recover_x(y, sign):
        if y >= p:
            return None
        x2 = (y * y - 1) * pow(d * y * y + 1, p - 2, p)
        if x2 == 0:
            return None if sign else 0
        x = pow(x2, (p + 3) // 8, p)
        if (x * x - x2) % p != 0:
            x = x * I % p
        if (x * x - x2) % p != 0:
            return None
        if (x & 1) != sign:
            x = p - x
        return x

    def decompress(s):
        if len(s) != 32:
            return None
        y = int.from_bytes(s, "little"); sign = y >> 255; y &= (1 << 255) - 1
        x = recover_x(y, sign)
        return None if x is None else (x, y, 1, x * y % p)

    gy = 4 * pow(5, p - 2, p) % p
    G = (recover_x(gy, 0), gy, 1, recover_x(gy, 0) * gy % p)
    if len(pub) != 32 or len(sig) != 64:
        return False
    A = decompress(pub); R = decompress(sig[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= q:
        return False
    h = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(), "little") % q
    return eq(mul(s, G), add(R, mul(h, A)))

VER_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$")

def vkey(v):
    return tuple(int(x) for x in v.split("."))

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

cmd, args = sys.argv[1], sys.argv[2:]
if cmd == "manifest":            # manifest VERSIONS_JSON PUBKEY -> «Version Datei SHA» der neusten gültig signierten Version
    pfad, pub = args
    try:
        with open(pfad, encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, ValueError) as e:
        fail("versions.json unlesbar: %s" % e)
    best = None
    for e in (m.get("versions") or []) if isinstance(m, dict) else []:
        if not isinstance(e, dict):
            continue
        v, fn, sh, sig = (str(e.get(k) or "") for k in ("version", "file", "sha256", "sig"))
        if not VER_RE.match(v) or fn != "webcam_bewegung_%s.py" % v.replace(".", "_") or not re.fullmatch(r"[0-9a-f]{64}", sh):
            continue
        try:
            ok = ed25519_verify(bytes.fromhex(pub), ("MotionWatch|%s|%s|%s" % (v, fn, sh)).encode(), bytes.fromhex(sig))
        except ValueError:
            ok = False
        if ok and (best is None or vkey(v) > vkey(best[0])):
            best = (v, fn, sh)
    if not best:
        fail("keine gültig signierte Version in versions.json")
    print(*best)
elif cmd == "sim":               # sim VERSIONS_JSON PUBKEY -> «SHA Grösse Version» des signierten Linux-Pakets (Block «sim»)
    pfad, pub = args
    try:
        with open(pfad, encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, ValueError) as e:
        fail("versions.json unlesbar: %s" % e)
    s = m.get("sim") if isinstance(m, dict) else None
    e = s.get("linux") if isinstance(s, dict) else None
    if not isinstance(e, dict):
        fail("kein Block «sim» mit Linux-Paket in versions.json")
    v, fn, sh, sig = (str(e.get(k) or "") for k in ("ver", "file", "sha256", "sig"))
    size = e.get("size")
    if not VER_RE.match(v) or fn != "simulator3d/MoveEyeSim3D_Linux.zip" or not re.fullmatch(r"[0-9a-f]{64}", sh) \
            or not isinstance(size, int) or not 0 < size <= 400000000:
        fail("Block «sim»: Linux-Paket unvollständig")
    try:
        ok = ed25519_verify(bytes.fromhex(pub), ("MotionWatch|%s|%s|%s" % (v, fn, sh)).encode(), bytes.fromhex(sig))
    except ValueError:
        ok = False
    if not ok:
        fail("Block «sim»: Signatur des Linux-Pakets ungültig")
    print(sh, size, v)
elif cmd == "programm":          # programm DATEI SHA VERSION -> «SHA Grösse» der Linux-ZIP (SIM3D_LINUX)
    pfad, sh, v = args
    if sha256(pfad) != sh:
        fail("Programmdatei: Prüfsumme stimmt nicht mit der signierten überein")
    with open(pfad, encoding="utf-8", errors="replace") as f:
        t = f.read()
    av = re.search(r'^APP_VERSION = "([0-9.]+)"', t, re.M)
    if not av or av.group(1) != v:
        fail("Programmdatei: Version passt nicht (%s statt %s)" % (av.group(1) if av else "?", v))
    lx = re.search(r'^SIM3D_LINUX = \{"version": "([0-9.]+)", "file": "simulator3d/MoveEyeSim3D_Linux\.zip", "size": (\d+),\s*'
                   r'"sha256": "([0-9a-f]{64})"', t, re.M)
    if not lx:
        fail("Programmdatei: kein SIM3D_LINUX (Linux-Paket) gefunden")
    print(lx.group(3), lx.group(2), lx.group(1))
elif cmd == "datei":             # datei PFAD SHA [GRÖSSE]
    import os
    pfad, sh = args[0], args[1]
    if len(args) > 2 and os.path.getsize(pfad) != int(args[2]):
        fail("%s: Grösse stimmt nicht" % pfad)
    if sha256(pfad) != sh:
        fail("%s: Prüfsumme stimmt nicht" % pfad)
    print("ok")
elif cmd == "vergleich":         # vergleich A B -> Exit 0, wenn A neuer als B ist
    sys.exit(0 if VER_RE.match(args[0]) and (not VER_RE.match(args[1]) or vkey(args[0]) > vkey(args[1])) else 1)
else:
    fail("unbekannt: " + cmd)
PY
}
pruefer() { python3 -I "$PRUEFER" "$@"; }

# ------------------------------------------------------------------ Laden
laden() {   # laden URL ZIEL MAX_BYTES
	case "$1" in https://*|file://*) ;; *) log "Adresse abgelehnt: $1"; return 1 ;; esac
	curl -fsSL --proto '=https,file' --retry 3 --connect-timeout 20 --max-time 1800 --max-filesize "$3" -o "$2" "$1"
}

# ------------------------------------------------------------------ Zustand am HP
test_laeuft() {   # läuft gerade ein Test? (Pause-Datei des Kiosks oder ein Job des Runners)
	[ -e "$PAUSE" ] && return 0
	id "$RU" >/dev/null 2>&1 && pgrep -u "$RU" -f 'Runner\.Worker' >/dev/null 2>&1 && return 0
	return 1
}
spielt() {   # wird am HP gespielt? (Spielen-Datei von hp_wache.py / testbild.py, jünger als 15 Min.) - Kiosk nicht neu starten
	[ -f "$SPIEL" ] && [ ! -L "$SPIEL" ] && [ $(( $(date +%s) - $(stat -c %Y "$SPIEL" 2>/dev/null || echo 0) )) -lt 900 ]
}
beschaeftigt() {   # Grund, warum jetzt nicht eingespielt wird (leer = Pause)
	if test_laeuft; then echo "Es läuft ein Test"; elif spielt; then echo "Am HP wird gespielt"; fi
}
stempel() {   # nach jeder vollständigen Prüfung: Zeit und Fassung merken (lesbar für das Dauerrechnen)
	mkdir -p "$ZUSTAND" && date +%s > "$ZUSTAND/letzter_lauf" && chmod 644 "$ZUSTAND/letzter_lauf"
	echo "$HP_FASSUNG" > "$ZUSTAND/fassung"
}
kiosk_benutzer() {   # Benutzer des Kiosks: dem gehört der Ordner des Kiosk-Simulators
	local s u
	s="$(sim_pfad)" || return 1
	[ -n "$s" ] && [ -e "$s" ] || return 1
	u="$(stat -c %U "$(dirname "$s")")"
	[ "$u" != root ] && [[ "$u" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]] && id "$u" >/dev/null 2>&1 && printf '%s' "$u"
}
spaeter() {   # neuer Versuch in 30 Min. (bis 3.54; ab 3.55 nicht mehr nötig: der Zeitplan schaut alle 15 Min.)
	[ "$(readlink -f "$0")" = "$SELBST" ] || return 0
	systemctl list-units --all --no-legend 'moveeye-hp-update-spaeter.*' 2>/dev/null | grep -q . && return 0
	systemd-run --quiet --unit=moveeye-hp-update-spaeter --on-active=30min --timer-property=AccuracySec=1min \
		"$SELBST" >/dev/null 2>&1 && log "Neuer Versuch in 30 Min."
	return 0
}
neu_ist() {   # neu_ist QUELLE ZIEL: ist die Quelle anders als das Ziel (oder fehlt das Ziel)?
	[ -f "$2" ] && cmp -s "$1" "$2" && return 1
	return 0
}
GEAENDERT=0
einspielen() {   # einspielen QUELLE ZIEL MODUS [BESCHREIBUNG] -> Exit 0 = geändert
	[ -f "$1" ] || return 1
	neu_ist "$1" "$2" || return 1
	install -D -m "$3" -o root -g root "$1" "$2" || { log "FEHLER beim Schreiben von $2"; return 1; }
	log "neu: $2${4:+ ($4)}"
	GEAENDERT=$((GEAENDERT + 1))
	return 0
}
cinnamon_offen() { pgrep -x cinnamon >/dev/null 2>&1 || pgrep -x cinnamon-session >/dev/null 2>&1 || pgrep -f '^cinnamon-session' >/dev/null 2>&1; }
runner_dienst() {   # Name des Runner-Dienstes (svc.sh schreibt ihn nach .service)
	local u
	u="$(cat "$RD/.service" 2>/dev/null)"
	[[ "$u" =~ ^[A-Za-z0-9._@-]{1,200}\.service$ ]] && printf '%s' "$u"
}
sim_pfad() {   # Programmdatei des Kiosk-Simulators aus /etc/moveeye-kiosk.conf (nur, wenn root sie geschrieben hat)
	[ -f "$KIOSK_CONF" ] || return 1
	[ "$(stat -c %u "$KIOSK_CONF")" = 0 ] || return 1
	(( 8#$(stat -c %a "$KIOSK_CONF") & 022 )) && return 1
	# shellcheck disable=SC2016  # wird in der Unter-Shell ausgewertet
	bash -c 'SIM=""; . "$1" >/dev/null 2>&1; printf "%s" "$SIM"' _ "$KIOSK_CONF"
}

# ------------------------------------------------------------------ Einspielen
pakete() {
	local p fehlt=""
	for p in $PAKETE; do
		[[ "$p" =~ ^[a-z0-9][a-z0-9.+-]{1,60}$ ]] || continue
		dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q 'install ok installed' || fehlt="$fehlt $p"
	done
	[ -z "$fehlt" ] && return 0
	log "Pakete nachinstallieren:$fehlt"
	export DEBIAN_FRONTEND=noninteractive
	apt-get update -q >/dev/null 2>&1 || log "Hinweis: apt-get update meldet Fehler"
	# shellcheck disable=SC2086
	apt-get install -y -q --no-install-recommends $fehlt >/dev/null 2>&1 || log "FEHLER: Pakete nicht installiert:$fehlt"
}

kiosk() {   # kiosk ORDNER -> setzt KIOSK_NEU
	local d="$1"
	KIOSK_NEU=0
	[ -d "$KIOSK_LIB" ] || { log "Kiosk nicht eingerichtet ($KIOSK_LIB fehlt) - übersprungen"; return 0; }
	einspielen "$d/kiosk_sitzung.sh" "$KIOSK_LIB/kiosk_sitzung.sh" 755 && KIOSK_NEU=1
	einspielen "$d/testbild.py" "$KIOSK_LIB/testbild.py" 644
	einspielen "$d/hp_wache.py" "$KIOSK_LIB/hp_wache.py" 644
	einspielen "$d/moveeye-sim.png" "$KIOSK_LIB/moveeye.png" 644
	spiel_ordner
	status_firewall
	return 0
}

spiel_ordner() {   # /run/moveeye-spiel gehört dem Benutzer des Kiosks (hp_wache.py / testbild.py schreiben dort «spielen»)
	local u tmp
	u="$(kiosk_benutzer)" || { log "Spielen: Benutzer des Kiosks unbekannt - Ordner nicht eingerichtet"; return 0; }
	tmp="$(mktemp)"
	printf '# MoveEye: Spielen-Wunsch des Kiosks für das Dauerrechnen (moveeye-hp-update)\nd %s 0755 %s %s -\n' \
		"$(dirname "$SPIEL")" "$u" "$u" > "$tmp"
	if neu_ist "$tmp" "$SPIEL_TMPFILES"; then
		install -D -m 644 "$tmp" "$SPIEL_TMPFILES" && log "neu: $SPIEL_TMPFILES (Benutzer $u)"
		GEAENDERT=$((GEAENDERT + 1))
	fi
	rm -f "$tmp"
	[ -d "$(dirname "$SPIEL")" ] || systemd-tmpfiles --create "$SPIEL_TMPFILES" >/dev/null 2>&1 || log "Hinweis: $(dirname "$SPIEL") nicht angelegt"
	return 0
}

status_firewall() {   # ist ufw an: Port 8761 (Status für MoveEye «HP rechnet») nur aus den eigenen Netzen erlauben
	command -v ufw >/dev/null 2>&1 || return 0
	ufw status 2>/dev/null | grep -q '^Status: active' || return 0
	local n
	for n in $(ip -o -4 addr show scope global 2>/dev/null | awk '{print $4}' | python3 -I -c 'import ipaddress, sys
for z in sys.stdin.read().split():
    try:
        n = ipaddress.ip_interface(z).network
    except ValueError:
        continue
    if n.is_private and n.prefixlen >= 8:
        print(n)'); do
		ufw status 2>/dev/null | grep -q "^$STATUS_PORT/tcp .*ALLOW.*$n" && continue
		ufw allow from "$n" to any port "$STATUS_PORT" proto tcp comment 'MoveEye HP-Status' >/dev/null 2>&1 \
			&& log "Firewall: Port $STATUS_PORT für $n erlaubt (nur eigenes Netz)"
	done
	return 0
}

runner() {   # runner ORDNER -> setzt RUNNER_NEU
	local d="$1/hp" u
	RUNNER_NEU=0
	[ -d "$RUNNER_LIB" ] || { log "Test-Runner nicht eingerichtet ($RUNNER_LIB fehlt) - übersprungen"; return 0; }
	einspielen "$d/job_start.sh" "$RUNNER_LIB/job_start.sh" 755
	einspielen "$d/job_ende.sh" "$RUNNER_LIB/job_ende.sh" 755
	einspielen "$d/runner_entfernen.sh" "$RUNNER_LIB/runner_entfernen.sh" 755
	u="$(runner_dienst)"
	if [ -n "$u" ]; then
		einspielen "$d/runner_dienst.conf" "/etc/systemd/system/$u.d/moveeye.conf" 644 "Dienst $u" && RUNNER_NEU=1
	fi
	return 0
}

simulator() {   # simulator ORDNER -> setzt SIM_NEU, SIM_BENUTZER
	local d="$1" sim ordner f name modus tmpd
	SIM_NEU=0 SIM_BENUTZER=""
	if [ -r "$CONF" ] && grep -Eq '^SIMULATOR=(nein|no|0|aus)' "$CONF"; then log "Simulator: aus ($CONF)"; return 0; fi
	sim="$(sim_pfad)" || { log "Simulator: kein Kiosk ($KIOSK_CONF) - übersprungen"; return 0; }
	{ [ -n "$sim" ] && [ -f "$sim" ]; } || { log "Simulator: '$sim' fehlt - übersprungen"; return 0; }
	ordner="$(dirname "$sim")"
	[ "$(basename "$sim")" = MoveEyeSim3D.x86_64 ] || { log "Simulator: unerwarteter Name ($sim) - übersprungen"; return 0; }
	SIM_BENUTZER="$(stat -c %U "$ordner")"
	if [ "$SIM_BENUTZER" = root ] || ! id "$SIM_BENUTZER" >/dev/null 2>&1; then log "Simulator: Ordner gehört '$SIM_BENUTZER' - übersprungen"; return 0; fi
	tmpd="$2"
	for f in "$d"/*; do
		[ -f "$f" ] || continue
		name="$(basename "$f")"
		[[ "$name" =~ ^[A-Za-z0-9._\ -]{1,80}$ ]] || continue
		[ -f "$ordner/$name" ] && cmp -s "$f" "$ordner/$name" && continue
		case "$name" in *.x86_64|*.sh) modus=755 ;; *) modus=644 ;; esac
		# als Benutzer des Kiosks schreiben (sein Ordner), dann umbenennen: der laufende Simulator behält die alte Datei
		{ cp "$f" "$tmpd/s" && chmod 644 "$tmpd/s"; } || { log "FEHLER: $name"; continue; }
		if runuser -u "$SIM_BENUTZER" -- install -m "$modus" "$tmpd/s" "$ordner/.hp-neu-$name" &&
			runuser -u "$SIM_BENUTZER" -- mv -f -T "$ordner/.hp-neu-$name" "$ordner/$name"; then
			log "neu: $ordner/$name"
			GEAENDERT=$((GEAENDERT + 1))
			[ "$name" = MoveEyeSim3D.x86_64 ] && SIM_NEU=1
		else
			runuser -u "$SIM_BENUTZER" -- rm -f -- "$ordner/.hp-neu-$name" 2>/dev/null
			log "FEHLER: $ordner/$name nicht ersetzt"
		fi
		rm -f "$tmpd/s"
	done
	return 0
}

einheiten() {   # Dienst und Zeitplan schreiben (idempotent: nur, was anders ist; jeder Lauf ruft das, so gilt nach einem
	local tmp neu=0  # Selbst-Update beim nächsten Lauf auch der Zeitplan der neuen Fassung)
	tmp="$(mktemp)"
	cat > "$tmp" <<EOF
# MoveEye HP-Update (werkzeuge/test_runner/hp_update.sh). Entfernen: sudo moveeye-hp-update --entfernen
[Unit]
Description=MoveEye HP-Update (signierte Version holen, prüfen, einspielen)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=$SELBST --zeitplan
Nice=10
IOSchedulingClass=idle
TimeoutStartSec=1h
EOF
	neu_ist "$tmp" "$DIENST" && install -D -m 644 "$tmp" "$DIENST" && neu=1
	cat > "$tmp" <<'EOF'
# MoveEye HP-Update: alle 15 Min. nachschauen (eingespielt wird nur in einer Pause, höchstens alle 6 Std. geprüft) und
# 8 Min. nach jedem Start
[Unit]
Description=MoveEye HP-Update (in den Pausen des Dauerrechnens und nach dem Start)

[Timer]
OnCalendar=*:07/15
RandomizedDelaySec=3min
OnBootSec=8min
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF
	neu_ist "$tmp" "$ZEITPLAN" && install -D -m 644 "$tmp" "$ZEITPLAN" && neu=1
	rm -f "$tmp"
	if [ $neu -eq 1 ]; then
		systemctl daemon-reload
		systemctl enable moveeye-hp-update.timer >/dev/null 2>&1 || log "FEHLER: Zeitplan nicht eingeschaltet"
		systemctl restart moveeye-hp-update.timer >/dev/null 2>&1
		log "Dienst und Zeitplan geschrieben ($DIENST, $ZEITPLAN)"
	elif ! systemctl is-enabled -q moveeye-hp-update.timer 2>/dev/null; then
		systemctl enable --now moveeye-hp-update.timer >/dev/null 2>&1 || log "FEHLER: Zeitplan nicht eingeschaltet"
	fi
	return 0
}

lauf() {   # einmal: laden, prüfen, einspielen
	local nur_pruefen="$1" w v fn sh lx_sha="" lx_size="" lx_ver="" alt="" sim_alt="" sim_sha_alt="" zip_ok=0 u herkunft urls
	w="$(mktemp -d /var/tmp/moveeye-hp-update.XXXXXX)" || { log "FEHLER: kein Arbeitsordner"; return 1; }
	# shellcheck disable=SC2064
	trap "rm -rf -- '$w'" EXIT
	pruefer_schreiben "$w/pruefer.py"
	[ -r "$ZUSTAND/version" ] && alt="$(tr -cd '0-9.' < "$ZUSTAND/version")"
	[ -r "$ZUSTAND/sim_version" ] && sim_alt="$(tr -cd '0-9.' < "$ZUSTAND/sim_version")"
	[ -r "$ZUSTAND/sim_sha256" ] && sim_sha_alt="$(tr -cd '0-9a-f' < "$ZUSTAND/sim_sha256")"
	[ "$nur_pruefen" -eq 0 ] && [ "$(readlink -f "$0")" = "$SELBST" ] && einheiten
	if [ "$nur_pruefen" -eq 0 ] && [ "$PLANLAUF" -eq 1 ]; then
		# Zeitplan (alle 15 Min.): still fertig, wenn vor kurzem geprüft (ausser kurz nach dem Start); beschäftigt: höchstens
		# einmal pro Stunde ins Protokoll
		local zuletzt=0 up
		[ -r "$ZUSTAND/letzter_lauf" ] && zuletzt="$(tr -cd '0-9' < "$ZUSTAND/letzter_lauf")"
		up="${MOVEEYE_HP_UPTIME:-$(cut -d. -f1 /proc/uptime 2>/dev/null || echo 9999)}"   # nur zum Prüfen änderbar
		if [ $(( $(date +%s) - ${zuletzt:-0} )) -lt 21600 ] && [ "${up:-9999}" -gt 1200 ] && \
			[ "$(cat "$ZUSTAND/fassung" 2>/dev/null)" = "$HP_FASSUNG" ]; then return 0; fi
		local b
		b="$(beschaeftigt)"
		if [ -n "$b" ]; then
			if [ ! -f "$ZUSTAND/verschoben" ] || [ $(( $(date +%s) - $(stat -c %Y "$ZUSTAND/verschoben") )) -gt 3600 ]; then
				mkdir -p "$ZUSTAND" && touch "$ZUSTAND/verschoben"
				log "$b - verschoben (nächster Versuch in 15 Min.)."
			fi
			return 0
		fi
	fi
	log "=== MoveEye HP-Update (eingespielt: ${alt:-nichts}) ==="
	if [ "$nur_pruefen" -eq 0 ]; then
		local b
		b="$(beschaeftigt)"
		if [ -n "$b" ]; then log "$b - verschoben."; return 0; fi
	fi
	laden "$REPO_RAW/main/versions.json" "$w/versions.json" 4000000 || { log "FEHLER: versions.json nicht geladen (Netz?)"; return 1; }
	read -r v fn sh < <(pruefer manifest "$w/versions.json" "$UPDATE_PUBKEY" 2> "$w/fehler") || true
	if [ -z "${sh:-}" ]; then log "ABGELEHNT: $(cat "$w/fehler")"; return 1; fi
	log "Signatur gültig: MoveEye $v ($fn)"
	read -r lx_sha lx_size lx_ver < <(pruefer sim "$w/versions.json" "$UPDATE_PUBKEY" 2> "$w/fehler_sim") || true
	if [ -n "${lx_ver:-}" ]; then
		herkunft="versions.json «sim»"
		log "Signatur gültig: Sim $lx_ver (Linux-Paket, eigene Spur)"
	elif grep -q 'Signatur\|unvollständig' "$w/fehler_sim"; then
		log "ABGELEHNT: $(cat "$w/fehler_sim")"; return 1       # ein Block «sim», der nicht stimmt: nie auf die Programmdatei ausweichen
	else
		herkunft="Programmdatei"
	fi
	if [ -n "$alt" ] && [ "$IMMER" -eq 0 ] && [ "$nur_pruefen" -eq 0 ]; then
		if [ "$alt" != "$v" ] && ! pruefer vergleich "$v" "$alt"; then log "ABGELEHNT: $v ist älter als die eingespielte $alt"; return 1; fi
		if [ "$herkunft" = Programmdatei ] && [ "$alt" = "$v" ] && [ "$(cat "$ZUSTAND/fassung" 2>/dev/null)" = "$HP_FASSUNG" ]; then
			log "Schon eingespielt - nichts zu tun."; stempel; return 0
		fi
	fi
	if [ "$herkunft" = Programmdatei ]; then
		if ! { laden "$REPO_RAW/v$v/$fn" "$w/programm.py" 64000000 || laden "$REPO_RAW/main/$fn" "$w/programm.py" 64000000; }; then
			log "FEHLER: $fn nicht geladen"; return 1
		fi
		read -r lx_sha lx_size lx_ver < <(pruefer programm "$w/programm.py" "$sh" "$v" 2> "$w/fehler") || true
		if [ -z "${lx_ver:-}" ]; then log "ABGELEHNT: $(cat "$w/fehler")"; return 1; fi
		log "Programmdatei geprüft (SHA-256 wie signiert), Linux-Paket $lx_ver: $lx_sha"
	fi
	if [ -n "$sim_alt" ] && [ "$IMMER" -eq 0 ] && [ "$nur_pruefen" -eq 0 ]; then
		if [ "$sim_alt" != "$lx_ver" ] && ! pruefer vergleich "$lx_ver" "$sim_alt"; then
			log "ABGELEHNT: Sim $lx_ver ist älter als die eingespielte Sim $sim_alt"; return 1
		fi
		if [ "$sim_sha_alt" = "$lx_sha" ] && [ "$(cat "$ZUSTAND/fassung" 2>/dev/null)" = "$HP_FASSUNG" ]; then
			[ "$alt" != "$v" ] && log "Neue MoveEye $v, der Simulator bleibt Sim $lx_ver - am HP nichts einzuspielen."
			[ "$alt" = "$v" ] && log "Schon eingespielt - nichts zu tun."
			mkdir -p "$ZUSTAND" && echo "$v" > "$ZUSTAND/version"
			stempel; return 0
		fi
		[ "$sim_sha_alt" = "$lx_sha" ] && log "Gleiche Version, neue Fassung dieses Updates - spiele noch einmal ein."
	fi
	urls="$REPO_RAW/main/simulator3d/MoveEyeSim3D_Linux.zip"
	if [ "$herkunft" = Programmdatei ]; then urls="$REPO_RAW/v$v/simulator3d/MoveEyeSim3D_Linux.zip $urls"
	else urls="$REPO_RAW/sim-$lx_ver/simulator3d/MoveEyeSim3D_Linux.zip $urls"; fi
	for u in $urls; do
		rm -f "$w/linux.zip"
		laden "$u" "$w/linux.zip" 400000000 || continue
		if pruefer datei "$w/linux.zip" "$lx_sha" "$lx_size" > /dev/null 2> "$w/fehler"; then zip_ok=1; break; fi
		log "Linux-Paket von $u: $(cat "$w/fehler") - nicht verwendet"
	done
	[ $zip_ok -eq 1 ] || { log "ABGELEHNT: kein Linux-Paket mit der signierten Prüfsumme gefunden"; return 1; }
	log "Linux-Paket geprüft (SHA-256 und Grösse wie signiert, aus: $herkunft)"
	if [ "$nur_pruefen" -eq 1 ]; then
		unzip -Z1 "$w/linux.zip" | grep '^MoveEyeSim3D/.*[^/]$' | sed 's/^/  /'
		log "Prüfung OK - nichts eingespielt (--pruefen)."
		return 0
	fi
	command -v unzip >/dev/null 2>&1 || pakete
	{ mkdir -p "$w/x" && unzip -q -o "$w/linux.zip" 'MoveEyeSim3D/*' -d "$w/x"; } || { log "FEHLER: Entpacken"; return 1; }
	local d="$w/x/MoveEyeSim3D"
	[ -f "$d/kiosk_sitzung.sh" ] || { log "FEHLER: kiosk_sitzung.sh fehlt im Paket"; return 1; }
	if [ ! -f "$d/hp/hp_update.sh" ]; then
		log "Dieses Paket hat noch keinen HP-Teil (vor 3.53.0) - nichts eingespielt, warte auf die nächste Version."
		mkdir -p "$ZUSTAND" && echo "$v" > "$ZUSTAND/version" && echo "$lx_ver" > "$ZUSTAND/sim_version" && echo "$lx_sha" > "$ZUSTAND/sim_sha256"
		stempel
		return 0
	fi
	# kurz vor dem Einspielen noch einmal: ist inzwischen ein Test gestartet oder wird gespielt?
	local b2
	b2="$(beschaeftigt)"
	if [ -n "$b2" ]; then log "$b2 - verschoben."; return 0; fi
	chmod 755 "$w" "$w/x" "$d"
	GEAENDERT=0
	pakete
	kiosk "$d"
	runner "$d"
	simulator "$d" "$w"
	einspielen "$d/hp/hp_update.sh" "$SELBST" 755 "dieses Update, gilt ab dem nächsten Lauf"
	# Neu starten, was neu ist - nie während eines Tests oder beim Spielen
	if [ -n "$(beschaeftigt)" ]; then
		log "Inzwischen läuft ein Test oder es wird gespielt - Neustarts verschoben (Dateien sind eingespielt, gelten danach bzw. nach dem nächsten Start)."
	else
		if [ "${RUNNER_NEU:-0}" -eq 1 ] && u="$(runner_dienst)" && [ -n "$u" ]; then
			systemctl daemon-reload
			if systemctl restart "$u"; then log "Dienst $u neu gestartet (neue Einstellungen)"; else log "FEHLER: $u startet nicht"; fi
		fi
		if [ "${KIOSK_NEU:-0}" -eq 1 ] && systemctl is-active -q display-manager 2>/dev/null; then
			if cinnamon_offen; then
				log "Kiosk neu: gilt nach dem Abmelden aus Cinnamon bzw. nach dem nächsten Start"
			elif systemctl restart display-manager; then
				log "Kiosk neu gestartet (neue kiosk_sitzung.sh)"
			fi
		elif [ "${SIM_NEU:-0}" -eq 1 ] && [ -n "${SIM_BENUTZER:-}" ]; then
			if pkill -TERM -u "$SIM_BENUTZER" -f "$MUSTER" 2>/dev/null; then log "Simulator neu gestartet (die Kiosk-Schleife startet ihn)"; fi
		fi
	fi
	mkdir -p "$ZUSTAND" && echo "$v" > "$ZUSTAND/version" && echo "$lx_ver" > "$ZUSTAND/sim_version" && echo "$lx_sha" > "$ZUSTAND/sim_sha256"
	stempel
	log "Fertig: MoveEye $v · Sim $lx_ver eingespielt ($GEAENDERT Datei(en) neu)."
	return 0
}

kuerzen() { if [ -f "$LOG" ] && [ "$(stat -c %s "$LOG")" -gt 1000000 ]; then tail -n 3000 "$LOG" > "$LOG.neu" && mv -f "$LOG.neu" "$LOG"; fi; }

case "$MODUS" in
	pruefen)
		IMMER=1
		lauf 1
		;;
	status)
		echo "Eingespielt: MoveEye $(cat "$ZUSTAND/version" 2>/dev/null || echo -) · Sim $(cat "$ZUSTAND/sim_version" 2>/dev/null || echo -)"
		systemctl list-timers --no-pager moveeye-hp-update.timer 2>/dev/null | head -n 2
		tail -n 15 "$LOG" 2>/dev/null
		;;
	einheiten)
		root_noetig "$@"
		einheiten
		;;
	entfernen)
		root_noetig "$@"
		systemctl disable --now moveeye-hp-update.timer >/dev/null 2>&1
		rm -f -- "$ZEITPLAN" "$DIENST"
		systemctl daemon-reload
		echo "Dienst und Zeitplan entfernt (eingespielte Dateien und $SELBST bleiben)."
		;;
	einrichten)
		root_noetig "$@"
		if [ "$(readlink -f "$0")" != "$SELBST" ]; then
			install -D -m 755 -o root -g root "$0" "$SELBST" && echo "eingerichtet: $SELBST"
		fi
		einheiten
		echo "Zeitplan: alle 15 Min. (nur in Pausen, höchstens alle 6 Std.) und 8 Min. nach jedem Start. Protokoll: $LOG"
		if [ "$OHNE_LAUF" -eq 0 ]; then
			echo "Erster Lauf jetzt:"
			kuerzen
			exec 9> /run/lock/moveeye-hp-update.lock
			flock -n 9 || { echo "Läuft schon."; exit 0; }
			lauf 0 2>&1 | tee -a "$LOG"
			exit "${PIPESTATUS[0]}"
		fi
		;;
	lauf)
		root_noetig "$@"
		kuerzen
		exec 9> /run/lock/moveeye-hp-update.lock
		flock -n 9 || { log "Läuft schon - beendet."; exit 0; }
		lauf 0 2>&1 | tee -a "$LOG"
		exit "${PIPESTATUS[0]}"
		;;
esac
