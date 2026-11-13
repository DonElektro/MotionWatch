#!/bin/bash
# MoveEye HP-Update - hält den Simulator-PC (HP: Kiosk und Test-Runner) aktuell, nur mit SIGNIERTEN Versionen.
#   sudo moveeye-hp-update                  neueste signierte Version holen, prüfen, einspielen (sofort, von Hand)
#   moveeye-hp-update --zeitplan            so startet es der Dienst moveeye-hp-update (Zeitplan: alle 15 Min. und 8 Min.
#                                           nach jedem Start): nur in einer Pause - nie, während der HP rechnet oder jemand
#                                           spielt. Ab HP_FASSUNG 5 (08.11.2026): jedes Mal ein kurzer Blick in die signierte
#                                           versions.json (10 KB); nichts Neues: höchstens stündlich eine Zeile; Neues während
#                                           eines Tests: wartet (Zeile mit Grund, Marke ZUSTAND/wartet: das Dauerrechnen
#                                           startet dann kein neues Paket), nach 6 Std. trotzdem (Neustarts erst danach).
#                                           Spielen hat immer Vorrang. Jedes Verschieben schreibt eine Zeile mit dem Grund.
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
# Controller (HP_FASSUNG 4): bluez + rfkill, der Treiber hid-playstation (fehlt er: linux-modules-extra des laufenden Kerns),
# controller_koppeln.sh / controller_fenster.py, die Einheiten moveeye-controller-koppeln.path / .service (der Benutzer des
# Kiosks legt nur die leere Wunsch-Datei /run/moveeye-spiel/controller_koppeln an, dann koppelt der Dienst als root einen
# PS5-Controller - kein sudo, keine polkit-Regel) und Ctrl+Alt+B in der Openbox-Einstellung des Kiosks.
# Controller verwalten (HP_FASSUNG 7, Besitzer 11.11.2026): Fenster mit Liste, Akku, «Trennen», «Vergessen» (Wunsch-Dateien
# controller_*: die Pfad-Einheit schaut auf das Muster, es zählt nur der Dateiname), auch DualShock 4 und Xbox-Controller;
# udev-Regel 71-moveeye-controller.rules: das Touchpad des Controllers ist im Kiosk keine Maus, und taucht ein
# Bluetooth-Adapter auf (USB-Stick eingesteckt, Hochfahren), schaltet der Dienst ihn ein - gekoppelte Controller verbinden
# sich dann mit der PS-Taste von selbst. Ohne Adapter läuft nichts davon (kein Fehler, keine Verzögerung beim Start).
# bluetooth.service wird eingeschaltet (startet nur mit Adapter), der Treiber btusb wie hid-playstation geprüft; dazu
# usbutils / pciutils (HP-Diagnose: lsusb, lspci).
# Knöpfe des Simulator-PCs (HP_FASSUNG 8, Besitzer 12.11.2026): hp_knoepfe.sh (Benutzer des Kiosks, ohne Rechte), hp_aus.sh
# mit moveeye-aus.path / .service (Wunsch-Dateien aus_herunterfahren / aus_neustart / aus_bios im Ordner des Kiosks -> der
# Dienst schaltet als root aus; drei feste Befehle, kein sudo, keine polkit-Regel), browser_leiste.py und in openbox.xml
# Ctrl+Alt+Z, der Rand oben für die Leiste und «Browser maximiert». Ein Browser wird NICHT installiert (der Knopf nimmt den,
# der da ist, und sagt sonst «kein Browser»). Dazu eine Prüfung (nur lesen, nur eine Zeile im Protokoll): der Ordner des
# Test-Runners darf für andere Benutzer nicht lesbar sein - der Browser läuft als Benutzer des Kiosks.
# Simulator-Anhang (Besitzer 12.11.2026, «Ablage entlasten»; kommt mit Sim 3.67.2 zusammen mit HP_FASSUNG 7 auf den HP): ab der
# Version NACH Sim 3.67.2 liegt das Linux-Paket nicht mehr im Repository, sondern als Asset am GitHub-Release «sim-X.Y.Z».
# Es steht dann signiert unter «sim» -> «anhang» -> «linux» in versions.json: «file» = simulator3d/anhang/MoveEyeSim3D_Linux.zip
# (anderer Name als das Paket im Repository: die Signatur passt nie an dessen Platz), «url» muss genau
# ANHANG_BASIS/sim-<Nummer>/MoveEyeSim3D_Linux.zip sein (die Adresse folgt aus der signierten Nummer). Das neuere gültig
# signierte Paket gewinnt (Repository oder Anhang); ein Anhang, der nicht stimmt, wird abgelehnt (kein Ausweichen).
# «sim.linux» bleibt für immer Sim 3.67.2 (Paket im Repository): ein HP mit einem älteren Skript spielt wie bisher 3.67.2
# ein, bekommt damit dieses Skript und holt beim nächsten Lauf den Anhang (zwei Schritte). Geladen wird in den
# Arbeitsordner; fehlt das Asset, stimmt die Prüfsumme nicht oder antwortet GitHub nicht: nichts wird eingespielt.
# Einstellungen: /etc/moveeye-hp-update.conf (SIMULATOR=nein: den Simulator nicht ersetzen). Protokoll: /var/log/moveeye-hp-update.log
set -u
REPO_RAW="${MOVEEYE_HP_QUELLE:-https://raw.githubusercontent.com/DonElektro/MotionWatch}"   # nur zum Prüfen änderbar
ANHANG_BASIS="${MOVEEYE_HP_ANHANG:-https://github.com/DonElektro/MotionWatch/releases/download}"   # Release-Assets; nur zum Prüfen änderbar
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
KIOSK_TEST="/etc/moveeye-kiosk-test.conf"   # von runner_einrichten.sh (Pause-Datei, TEST_BENUTZER); runner_entfernen.sh nimmt sie weg
HP_FASSUNG=8                     # 8 = Knöpfe des Simulator-PCs (Ausschalten, Browser; moveeye-aus, openbox.xml); 7 = Controller verwalten (Liste, Trennen, Vergessen, udev-Regel, Adapter einstecken genügt); 6 = Zeitplan prüft jedes Mal kurz, Neues wartet höchstens 6 Std. auf eine Pause (Marke «wartet»); 5 = Bildschirm für die Testläufe (TEST_BENUTZER, xhost), 4 = Controller koppeln (Bluetooth), 3 = drei Spuren (Sim aus versions.json «sim»); erhöhen, wenn dieses Skript bei gleicher Version mehr einspielt als die Fassung davor
STATUS_PORT=8761
# Pakete, die Kiosk und Testbild brauchen (nur fehlende werden installiert, nichts wird entfernt)
PAKETE="python3-tk x11-xserver-utils libxss1 unzip curl bluez rfkill usbutils pciutils"   # bluez, rfkill: Controller per Bluetooth koppeln; usbutils, pciutils: HP-Diagnose (lsusb, lspci)
KOPPELN_DIENST="/etc/systemd/system/moveeye-controller-koppeln.service"
KOPPELN_PFAD="/etc/systemd/system/moveeye-controller-koppeln.path"
UDEV_REGEL="/etc/udev/rules.d/71-moveeye-controller.rules"
AUS_DIENST="/etc/systemd/system/moveeye-aus.service"
AUS_PFAD="/etc/systemd/system/moveeye-aus.path"
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
elif cmd == "sim":               # sim VERSIONS_JSON PUBKEY ANHANG_BASIS -> «SHA Grösse Version Adresse» des signierten
    pfad, pub, basis = args      # Linux-Pakets (Block «sim»); Adresse «-» = Paket im Repository, sonst das Release-Asset
    try:
        with open(pfad, encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, ValueError) as e:
        fail("versions.json unlesbar: %s" % e)
    s = m.get("sim") if isinstance(m, dict) else None
    e = s.get("linux") if isinstance(s, dict) else None
    ah = s.get("anhang") if isinstance(s, dict) else None
    a = ah.get("linux") if isinstance(ah, dict) else None      # Simulator-Anhang: das Linux-Paket als Release-Asset
    if not isinstance(e, dict) and not isinstance(a, dict):
        fail("kein Block «sim» mit Linux-Paket in versions.json")

    def paket(e, name, datei, wo):
        v, fn, sh, sig = (str(e.get(k) or "") for k in ("ver", "file", "sha256", "sig"))
        size = e.get("size")
        if not VER_RE.match(v) or fn != datei or not re.fullmatch(r"[0-9a-f]{64}", sh) \
                or not isinstance(size, int) or not 0 < size <= 400000000:
            fail("Block «%s»: Linux-Paket unvollständig" % name)
        url = "-"
        if wo:
            url = str(e.get("url") or "")
            if url != "%s/sim-%s/MoveEyeSim3D_Linux.zip" % (wo.rstrip("/"), v):
                fail("Block «%s»: Adresse des Linux-Pakets unvollständig oder fremd" % name)
        try:
            ok = ed25519_verify(bytes.fromhex(pub), ("MotionWatch|%s|%s|%s" % (v, fn, sh)).encode(), bytes.fromhex(sig))
        except ValueError:
            ok = False
        if not ok:
            fail("Block «%s»: Signatur des Linux-Pakets ungültig" % name)
        return sh, size, v, url

    best = paket(e, "sim", "simulator3d/MoveEyeSim3D_Linux.zip", "") if isinstance(e, dict) else None
    if isinstance(a, dict):
        x = paket(a, "sim.anhang", "simulator3d/anhang/MoveEyeSim3D_Linux.zip", basis)
        if best is None or vkey(x[2]) > vkey(best[2]):         # bei gleicher Nummer: das Paket im Repository
            best = x
    print(*best)
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
	curl -fsSL --proto '=https,file' --proto-redir '=https' --retry 3 --connect-timeout 20 --max-time 1800 --max-filesize "$3" -o "$2" "$1"
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
beschaeftigt() {   # Grund, warum jetzt nicht eingespielt wird (leer = Pause); TROTZ_TEST=1: ein Test hält nicht mehr auf
	if spielt; then echo "Am HP wird gespielt"; elif [ "${TROTZ_TEST:-0}" != 1 ] && test_laeuft; then echo "Es läuft ein Test"; fi
}
WARTE_MAX_S=21600                # so lange wartet ein neues Update auf eine Pause zwischen Tests, danach wird es trotzdem eingespielt
plog() {   # Zeitplan: Zeilen sammeln, bis klar ist, ob es Neues gibt (sonst stünde alle 15 Min. dasselbe im Protokoll)
	if [ "${STILL:-0}" = 1 ]; then PUFFER="${PUFFER:-}$(date '+%F %T') $*"$'\n'; else log "$*"; fi
}
nichts_neu() {   # nichts Neues: im Zeitplan höchstens stündlich eine Zeile (Marke ZUSTAND/nichts_neu), von Hand immer
	if [ "${STILL:-0}" = 1 ]; then
		STILL=0; PUFFER=""
		if [ ! -f "$ZUSTAND/nichts_neu" ] || [ $(( $(date +%s) - $(stat -c %Y "$ZUSTAND/nichts_neu") )) -ge 3600 ]; then
			mkdir -p "$ZUSTAND" && touch "$ZUSTAND/nichts_neu"
			log "Geprüft: nichts Neues (MoveEye ${v:-?}${lx_ver:+ · Sim $lx_ver}; nächste solche Zeile in einer Stunde)."
		fi
	else
		log "$*"
	fi
	rm -f "$ZUSTAND/wartet"
}
laut() { if [ "${STILL:-0}" = 1 ]; then STILL=0; printf '%s' "${PUFFER:-}"; PUFFER=""; fi; }
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

modul_pakete() {   # Treiber des PS5-Controllers (hid-playstation) und für USB-Bluetooth-Sticks (btusb): fehlt einer,
	local p m fehlt=""   # linux-modules-extra des laufenden Kerns
	command -v modinfo >/dev/null 2>&1 || return 0
	for m in hid_playstation btusb; do
		modinfo "$m" >/dev/null 2>&1 || fehlt="$fehlt $m"
	done
	[ -z "$fehlt" ] && return 0
	p="linux-modules-extra-$(uname -r)"
	[[ "$p" =~ ^[a-z0-9][a-z0-9.+-]{1,60}$ ]] || return 0
	if dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q 'install ok installed'; then
		log "Hinweis: Treiber fehlt im Kern $(uname -r):$fehlt ($p ist installiert)"; return 0
	fi
	apt-cache show "$p" >/dev/null 2>&1 || { log "Hinweis: Treiber fehlt:$fehlt - $p gibt es nicht"; return 0; }
	log "Treiber für Controller / Bluetooth nachinstallieren ($fehlt ): $p"
	DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends "$p" >/dev/null 2>&1 || log "FEHLER: $p nicht installiert"
}

kiosk() {   # kiosk ORDNER -> setzt KIOSK_NEU
	local d="$1"
	KIOSK_NEU=0
	[ -d "$KIOSK_LIB" ] || { log "Kiosk nicht eingerichtet ($KIOSK_LIB fehlt) - übersprungen"; return 0; }
	einspielen "$d/kiosk_sitzung.sh" "$KIOSK_LIB/kiosk_sitzung.sh" 755 && KIOSK_NEU=1
	einspielen "$d/testbild.py" "$KIOSK_LIB/testbild.py" 644
	einspielen "$d/hp_wache.py" "$KIOSK_LIB/hp_wache.py" 644
	einspielen "$d/moveeye-sim.png" "$KIOSK_LIB/moveeye.png" 644
	einspielen "$d/controller_koppeln.sh" "$KIOSK_LIB/controller_koppeln.sh" 755
	einspielen "$d/controller_fenster.py" "$KIOSK_LIB/controller_fenster.py" 644
	einspielen "$d/hp_knoepfe.sh" "$KIOSK_LIB/hp_knoepfe.sh" 755
	einspielen "$d/hp_aus.sh" "$KIOSK_LIB/hp_aus.sh" 755
	einspielen "$d/browser_leiste.py" "$KIOSK_LIB/browser_leiste.py" 644
	spiel_ordner
	koppeln_dienst
	controller_udev
	aus_dienst
	openbox_taste && KIOSK_NEU=1
	openbox_browser && KIOSK_NEU=1
	browser_schutz
	status_firewall
	test_bildschirm
	return 0
}

test_bildschirm() {   # HP_FASSUNG 5 (Besitzer 08.11.2026): der Test-Runner darf den Bildschirm (echte Grafikkarte) benutzen
	# 1. TEST_BENUTZER=$RU in $KIOSK_TEST (die anderen Zeilen bleiben; kiosk_sitzung.sh gibt den Bildschirm damit bei jedem
	#    Start der Sitzung frei). 2. Sofort, ohne Neustart: läuft die Sitzung des Kiosks, dort «xhost +SI:localuser:$RU» -
	#    nur dieser eine lokale Benutzer, nie «xhost +» für alle. Nur wenn der Runner eingerichtet ist; nur in einer Pause
	#    (wie alles in lauf()). Zurück: runner_entfernen.sh (entfernt $KIOSK_TEST und nimmt die Freigabe zurück).
	local tmp u pid xa=""
	id "$RU" >/dev/null 2>&1 || return 0
	if [ ! -f "$KIOSK_TEST" ] || [ -L "$KIOSK_TEST" ] || [ "$(stat -c %u "$KIOSK_TEST")" != 0 ]; then
		log "Bildschirm für Tests: $KIOSK_TEST fehlt (runner_einrichten.sh) - übersprungen"; return 0
	fi
	if ! grep -qx "TEST_BENUTZER=$RU" "$KIOSK_TEST"; then
		tmp="$(mktemp)"
		grep -v '^TEST_BENUTZER=' "$KIOSK_TEST" > "$tmp"
		echo "TEST_BENUTZER=$RU" >> "$tmp"
		install -m 644 "$tmp" "$KIOSK_TEST" && log "Bildschirm für Tests: TEST_BENUTZER=$RU in $KIOSK_TEST"
		rm -f "$tmp"
		GEAENDERT=$((GEAENDERT + 1))
	fi
	command -v xhost >/dev/null 2>&1 || return 0
	u="$(kiosk_benutzer)" || return 0
	if [ -n "${MOVEEYE_HP_XAUTH:-}" ]; then
		xa="$MOVEEYE_HP_XAUTH"                                    # nur zum Prüfen (hp_update_test.sh)
	else
		for pid in $(pgrep -u "$u" 2>/dev/null); do          # die laufende Sitzung des Kiosks auf :0: ihre XAUTHORITY
			tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | grep -qx 'DISPLAY=:0' || continue
			xa="$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | sed -n 's/^XAUTHORITY=//p' | head -n 1)"
			[ -n "$xa" ] && break
		done
	fi
	if [ -z "$xa" ] || [ ! -r "$xa" ]; then log "Bildschirm für Tests: keine laufende Sitzung auf :0 - gilt ab dem nächsten Start der Sitzung"; return 0; fi
	if runuser -u "$u" -- env DISPLAY=:0 XAUTHORITY="$xa" xhost 2>/dev/null | grep -qx "SI:localuser:$RU"; then return 0; fi
	if runuser -u "$u" -- env DISPLAY=:0 XAUTHORITY="$xa" xhost "+SI:localuser:$RU" >/dev/null 2>&1; then
		log "Bildschirm für Tests: in der laufenden Sitzung freigegeben (nur der lokale Benutzer $RU)"
	else
		log "Hinweis: xhost in der laufenden Sitzung ging nicht - gilt ab dem nächsten Start der Sitzung"
	fi
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

koppeln_dienst() {   # Controller koppeln: Pfad-Einheit (Wunsch-Datei des Kiosks) startet den Dienst (root, feste Aufgabe)
	local tmp neu=0 wunsch
	[ -f "$KIOSK_LIB/controller_koppeln.sh" ] || return 0
	wunsch="$(dirname "$SPIEL")/controller_koppeln"
	tmp="$(mktemp)"
	cat > "$tmp" <<EOF
# MoveEye: Controller (PS5 DualSense und andere) per Bluetooth koppeln und verwalten (moveeye-hp-update). Startet nur über
# moveeye-controller-koppeln.path (Wunsch-Dateien des Kiosks: es zählt nur der Dateiname), über udev (ein Bluetooth-Adapter
# taucht auf) oder von Hand; nimmt keine Angaben an. Kein Startlimit: das Skript bremst selbst (1 s pro Lauf).
[Unit]
Description=MoveEye: Controller per Bluetooth koppeln
After=bluetooth.service
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=$KIOSK_LIB/controller_koppeln.sh
TimeoutStartSec=420
RuntimeDirectory=moveeye-controller
RuntimeDirectoryMode=0755
RuntimeDirectoryPreserve=yes
NoNewPrivileges=yes
ProtectHome=yes
ProtectSystem=full
PrivateTmp=yes
EOF
	neu_ist "$tmp" "$KOPPELN_DIENST" && install -D -m 644 "$tmp" "$KOPPELN_DIENST" && neu=1
	cat > "$tmp" <<EOF
# MoveEye: Wunsch «Controller koppeln» (Knopf im Testbild / in der Ecke, Ctrl+Alt+B) und Wünsche aus dem Fenster
# (Liste, Trennen, Vergessen, Abbrechen: leere Dateien controller_*) -> moveeye-controller-koppeln.service
[Unit]
Description=MoveEye: Wunsch «Controller koppeln» vom Kiosk

[Path]
PathExists=$wunsch
PathExistsGlob=$(dirname "$SPIEL")/controller_*
Unit=moveeye-controller-koppeln.service

[Install]
WantedBy=paths.target
EOF
	neu_ist "$tmp" "$KOPPELN_PFAD" && install -D -m 644 "$tmp" "$KOPPELN_PFAD" && neu=1
	rm -f "$tmp"
	if [ $neu -eq 1 ]; then
		log "neu: Controller koppeln ($KOPPELN_PFAD, $KOPPELN_DIENST)"
		GEAENDERT=$((GEAENDERT + 1))
		systemctl daemon-reload
		systemctl enable moveeye-controller-koppeln.path >/dev/null 2>&1 || log "FEHLER: moveeye-controller-koppeln.path nicht eingeschaltet"
		systemctl restart moveeye-controller-koppeln.path >/dev/null 2>&1
	elif ! systemctl is-enabled -q moveeye-controller-koppeln.path 2>/dev/null; then
		systemctl enable --now moveeye-controller-koppeln.path >/dev/null 2>&1 || log "FEHLER: moveeye-controller-koppeln.path nicht eingeschaltet"
	fi
	return 0
}

controller_udev() {   # HP_FASSUNG 7: udev-Regel (Touchpad des Controllers keine Maus; Adapter taucht auf -> einschalten) und
	local tmp        # bluetooth.service eingeschaltet. Ohne Adapter passiert nichts: kein Fehler, keine Verzögerung beim Start.
	[ -f "$KIOSK_LIB/controller_koppeln.sh" ] || return 0
	tmp="$(mktemp)"
	cat > "$tmp" <<'EOF'
# MoveEye (moveeye-hp-update, HP_FASSUNG 7): Controller am Simulator-PC. Entfernen: diese Datei löschen.
# 1. Das Touchpad des PS5- / PS4-Controllers ist keine Maus: sonst bewegt jede Berührung den Mauszeiger des Kiosks und
#    klickt im Simulator (libinput lässt nur dieses Teil-Gerät weg; Tasten, Sticks und das Gamepad selbst bleiben).
ACTION!="remove", SUBSYSTEM=="input", KERNEL=="event*", ATTRS{name}=="*Controller Touchpad", ENV{LIBINPUT_IGNORE_DEVICE}="1"
# 2. Ein Bluetooth-Adapter taucht auf (USB-Stick eingesteckt oder beim Hochfahren): der Dienst schaltet ihn ein und
#    schreibt die Liste - gekoppelte Controller verbinden sich dann mit der PS-Taste von selbst. Ohne Adapter läuft nichts.
ACTION=="add", SUBSYSTEM=="bluetooth", KERNEL=="hci[0-9]*", TAG+="systemd", ENV{SYSTEMD_WANTS}+="moveeye-controller-koppeln.service"
EOF
	if einspielen "$tmp" "$UDEV_REGEL" 644 "Touchpad des Controllers keine Maus; Bluetooth-Adapter einstecken genügt"; then
		command -v udevadm >/dev/null 2>&1 && { udevadm control --reload >/dev/null 2>&1 || log "Hinweis: udev nicht neu geladen (gilt nach dem nächsten Start)"; }
		# ist schon ein Adapter da: jetzt einmal einschalten (sonst erst beim nächsten Einstecken / Start)
		if compgen -G '/sys/class/bluetooth/hci*' >/dev/null; then systemctl start --no-block moveeye-controller-koppeln.service >/dev/null 2>&1; fi
	fi
	rm -f "$tmp"
	# bluetooth.service: eingeschaltet lassen bzw. einschalten (er startet nur, wenn es einen Adapter gibt:
	# ConditionPathIsDirectory=/sys/class/bluetooth) - sonst käme ein später eingesteckter Stick nicht von selbst in Gang
	if systemctl cat bluetooth.service >/dev/null 2>&1 && ! systemctl is-enabled -q bluetooth.service 2>/dev/null; then
		if systemctl enable bluetooth.service >/dev/null 2>&1; then log "bluetooth.service eingeschaltet (startet nur mit Adapter)"
		else log "Hinweis: bluetooth.service nicht eingeschaltet"; fi
	fi
	return 0
}

aus_dienst() {   # HP_FASSUNG 8: «Ausschalten» im Simulator - Pfad-Einheit (Wunsch-Datei des Kiosks) startet den Dienst (root)
	local tmp neu=0
	[ -f "$KIOSK_LIB/hp_aus.sh" ] || return 0
	tmp="$(mktemp)"
	cat > "$tmp" <<EOF
# MoveEye: Simulator-PC ausschalten / neu starten / neu starten ins BIOS (moveeye-hp-update). Startet nur über
# moveeye-aus.path (leere Wunsch-Datei des Kiosks: es zählt nur der Dateiname) oder von Hand; nimmt keine Angaben an und
# führt nur drei feste Befehle aus (hp_aus.sh). Kein Startlimit: das Skript bremst selbst (1 s pro Lauf).
[Unit]
Description=MoveEye: Simulator-PC ausschalten (Knopf im Simulator)
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=$KIOSK_LIB/hp_aus.sh
TimeoutStartSec=60
RuntimeDirectory=moveeye-aus
RuntimeDirectoryMode=0755
RuntimeDirectoryPreserve=yes
NoNewPrivileges=yes
ProtectHome=yes
ProtectSystem=full
PrivateTmp=yes
EOF
	neu_ist "$tmp" "$AUS_DIENST" && install -D -m 644 "$tmp" "$AUS_DIENST" && neu=1
	cat > "$tmp" <<EOF
# MoveEye: Wunsch «Ausschalten» vom Kiosk (leere Dateien aus_herunterfahren / aus_neustart / aus_bios) -> moveeye-aus.service
[Unit]
Description=MoveEye: Wunsch «Ausschalten» vom Kiosk

[Path]
PathExistsGlob=$(dirname "$SPIEL")/aus_*
Unit=moveeye-aus.service

[Install]
WantedBy=paths.target
EOF
	neu_ist "$tmp" "$AUS_PFAD" && install -D -m 644 "$tmp" "$AUS_PFAD" && neu=1
	rm -f "$tmp"
	rm -f -- "$(dirname "$SPIEL")"/aus_herunterfahren "$(dirname "$SPIEL")"/aus_neustart "$(dirname "$SPIEL")"/aus_bios 2>/dev/null   # nie mit einem alten Wunsch einschalten
	if [ $neu -eq 1 ]; then
		log "neu: Ausschalten aus dem Simulator ($AUS_PFAD, $AUS_DIENST)"
		GEAENDERT=$((GEAENDERT + 1))
		systemctl daemon-reload
		systemctl enable moveeye-aus.path >/dev/null 2>&1 || log "FEHLER: moveeye-aus.path nicht eingeschaltet"
		systemctl restart moveeye-aus.path >/dev/null 2>&1
	elif ! systemctl is-enabled -q moveeye-aus.path 2>/dev/null; then
		systemctl enable --now moveeye-aus.path >/dev/null 2>&1 || log "FEHLER: moveeye-aus.path nicht eingeschaltet"
	fi
	return 0
}

openbox_browser() {   # HP_FASSUNG 8: Ctrl+Alt+Z (zurück vom Browser), Rand oben für die Leiste, Browser maximiert; Exit 0 = geändert
	local ob="$KIOSK_LIB/openbox.xml" tmp
	[ -f "$ob" ] && [ ! -L "$ob" ] || return 1
	[ -f "$KIOSK_LIB/hp_knoepfe.sh" ] || return 1
	grep -q 'hp_knoepfe.sh zurueck' "$ob" && return 1
	tmp="$(mktemp)"
	if ! python3 -I -c 'import sys, xml.dom.minidom
z = open(sys.argv[1], encoding="utf-8").read().splitlines(keepends=True)
def vor(marke, neu):
    for i, ln in enumerate(z):
        if marke in ln:
            z[i:i] = [x + "\n" for x in neu]
            return
    sys.exit(1)
vor("</keyboard>", [chr(32) * 4 + "<keybind key=\"C-A-z\"><action name=\"Execute\"><command>/usr/local/lib/moveeye-kiosk/hp_knoepfe.sh zurueck</command></action></keybind>"])
if not any("<margins>" in ln for ln in z):
    vor("<applications>", ["  <margins><top>40</top><bottom>0</bottom><left>0</left><right>0</right></margins>"])
vor("</applications>", [chr(32) * 4 + "<application class=\"?irefox*\" type=\"normal\"><decor>no</decor><maximized>yes</maximized><focus>yes</focus></application>",
                        chr(32) * 4 + "<application class=\"?hromium*\" type=\"normal\"><decor>no</decor><maximized>yes</maximized><focus>yes</focus></application>"])
t = "".join(z)
xml.dom.minidom.parseString(t.encode("utf-8"))
open(sys.argv[2], "w", encoding="utf-8").write(t)' "$ob" "$tmp" 2>/dev/null; then
		rm -f "$tmp"; log "Hinweis: openbox.xml sieht anders aus als erwartet - Ctrl+Alt+Z und die Browser-Regeln nicht eingetragen"; return 1
	fi
	if grep -q 'hp_knoepfe.sh zurueck' "$tmp" && einspielen "$tmp" "$ob" 644 "Ctrl+Alt+Z: vom Browser zurück; Rand für die Leiste"; then
		rm -f "$tmp"; return 0
	fi
	rm -f "$tmp"
	return 1
}

browser_schutz() {   # HP_FASSUNG 8, nur lesen: der Browser läuft als Benutzer des Kiosks - an die Dateien des Runners darf er nicht
	local d m u b
	[ -f "$KIOSK_LIB/hp_knoepfe.sh" ] || return 0
	for d in "$(dirname "$RD")" "$RD"; do
		[ -d "$d" ] || continue
		m="$(stat -c %a "$d")"
		(( 8#$m & 007 )) && log "WARNUNG: $d ist für alle Benutzer zugänglich (Rechte $m) - sollte 750 sein (runner_einrichten.sh); der Browser des Kiosks könnte die Anmeldung des Runners lesen"
	done
	u="$(kiosk_benutzer)" || return 0
	if id -nG "$u" 2>/dev/null | tr ' ' '\n' | grep -qx "$RU"; then
		log "WARNUNG: der Benutzer des Kiosks ist in der Gruppe $RU - damit kann der Browser Dateien des Runners lesen"
	fi
	b=""
	for d in firefox firefox-esr chromium chromium-browser; do command -v "$d" >/dev/null 2>&1 && { b="$d"; break; }; done
	[ -f "$ZUSTAND/browser_gemeldet" ] && [ "$(cat "$ZUSTAND/browser_gemeldet" 2>/dev/null)" = "${b:-keiner}" ] && return 0
	mkdir -p "$ZUSTAND" && echo "${b:-keiner}" > "$ZUSTAND/browser_gemeldet"
	if [ -n "$b" ]; then log "Browser für den Knopf im Simulator: $b (nichts installiert)"
	else log "Hinweis: kein Browser installiert (firefox / chromium) - der Knopf «Browser» im Simulator sagt das; installieren: sudo apt install firefox"; fi
	return 0
}

openbox_taste() {   # Ctrl+Alt+B (Controller koppeln) in die Openbox-Einstellung des Kiosks; Exit 0 = geändert
	local ob="$KIOSK_LIB/openbox.xml" tmp
	[ -f "$ob" ] && [ ! -L "$ob" ] || return 1
	grep -q 'kiosk_sitzung.sh koppeln' "$ob" && return 1
	grep -q 'kiosk_sitzung.sh neustart</command></action></keybind>' "$ob" || return 1
	tmp="$(mktemp)"
	sed '/kiosk_sitzung.sh neustart<\/command><\/action><\/keybind>/a\
    <keybind key="C-A-b"><action name="Execute"><command>/usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh koppeln</command></action></keybind>' \
		"$ob" > "$tmp"
	if grep -q 'kiosk_sitzung.sh koppeln' "$tmp" && einspielen "$tmp" "$ob" 644 "Ctrl+Alt+B: Controller koppeln"; then
		rm -f "$tmp"; return 0
	fi
	rm -f "$tmp"
	return 1
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
	local nur_pruefen="$1" w v fn sh lx_sha="" lx_size="" lx_ver="" lx_url="" alt="" sim_alt="" sim_sha_alt="" zip_ok=0 u herkunft urls
	w="$(mktemp -d /var/tmp/moveeye-hp-update.XXXXXX)" || { log "FEHLER: kein Arbeitsordner"; return 1; }
	# shellcheck disable=SC2064
	trap "rm -rf -- '$w'" EXIT
	pruefer_schreiben "$w/pruefer.py"
	[ -r "$ZUSTAND/version" ] && alt="$(tr -cd '0-9.' < "$ZUSTAND/version")"
	[ -r "$ZUSTAND/sim_version" ] && sim_alt="$(tr -cd '0-9.' < "$ZUSTAND/sim_version")"
	[ -r "$ZUSTAND/sim_sha256" ] && sim_sha_alt="$(tr -cd '0-9a-f' < "$ZUSTAND/sim_sha256")"
	[ "$nur_pruefen" -eq 0 ] && [ "$(readlink -f "$0")" = "$SELBST" ] && einheiten
	STILL=0 PUFFER="" TROTZ_TEST=0
	if [ "$nur_pruefen" -eq 0 ] && [ "$PLANLAUF" -eq 1 ]; then
		# Zeitplan (alle 15 Min.): Spielen hat Vorrang (jedes Mal eine Zeile). Sonst ein kurzer Blick in die signierte Liste;
		# ob ein Test läuft, zählt erst, wenn es etwas Neues gibt (unten).
		if spielt; then log "Am HP wird gespielt - verschoben (nächster Versuch in 15 Min.)."; return 0; fi
		STILL=1
	fi
	plog "=== MoveEye HP-Update (eingespielt: ${alt:-nichts}) ==="
	if [ "$nur_pruefen" -eq 0 ] && [ "$PLANLAUF" -eq 0 ]; then
		local b
		b="$(beschaeftigt)"
		if [ -n "$b" ]; then log "$b - verschoben."; return 0; fi
	fi
	laden "$REPO_RAW/main/versions.json" "$w/versions.json" 4000000 || { log "FEHLER: versions.json nicht geladen (Netz?)"; return 1; }
	read -r v fn sh < <(pruefer manifest "$w/versions.json" "$UPDATE_PUBKEY" 2> "$w/fehler") || true
	if [ -z "${sh:-}" ]; then log "ABGELEHNT: $(cat "$w/fehler")"; return 1; fi
	plog "Signatur gültig: MoveEye $v ($fn)"
	read -r lx_sha lx_size lx_ver lx_url < <(pruefer sim "$w/versions.json" "$UPDATE_PUBKEY" "$ANHANG_BASIS" 2> "$w/fehler_sim") || true
	if [ -n "${lx_ver:-}" ] && [ "${lx_url:--}" != "-" ]; then
		herkunft="versions.json «sim.anhang»"
		plog "Signatur gültig: Sim $lx_ver (Linux-Paket als Release-Asset, eigene Spur)"
	elif [ -n "${lx_ver:-}" ]; then
		herkunft="versions.json «sim»"
		plog "Signatur gültig: Sim $lx_ver (Linux-Paket, eigene Spur)"
	elif grep -q 'Signatur\|unvollständig' "$w/fehler_sim"; then
		log "ABGELEHNT: $(cat "$w/fehler_sim")"; return 1       # ein Block «sim», der nicht stimmt: nie auf die Programmdatei ausweichen
	else
		herkunft="Programmdatei"
	fi
	if [ -n "$alt" ] && [ "$IMMER" -eq 0 ] && [ "$nur_pruefen" -eq 0 ]; then
		if [ "$alt" != "$v" ] && ! pruefer vergleich "$v" "$alt"; then log "ABGELEHNT: $v ist älter als die eingespielte $alt"; return 1; fi
		if [ "$herkunft" = Programmdatei ] && [ "$alt" = "$v" ] && [ "$(cat "$ZUSTAND/fassung" 2>/dev/null)" = "$HP_FASSUNG" ]; then
			nichts_neu "Schon eingespielt - nichts zu tun."; stempel; return 0
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
			if [ "$alt" != "$v" ]; then laut; log "Neue MoveEye $v, der Simulator bleibt Sim $lx_ver - am HP nichts einzuspielen."
			else nichts_neu "Schon eingespielt - nichts zu tun."; fi
			mkdir -p "$ZUSTAND" && echo "$v" > "$ZUSTAND/version"
			stempel; return 0
		fi
		[ "$sim_sha_alt" = "$lx_sha" ] && plog "Gleiche Version, neue Fassung dieses Updates - spiele noch einmal ein."
	fi
	# Es gibt Neues. Zeitplan: läuft ein Test, warten (Marke ZUSTAND/wartet: das Dauerrechnen startet dann kein neues Paket,
	# so kommt das Update zwischen zwei Tests dran); nach WARTE_MAX_S trotzdem - nur Spielen hält es dann noch auf.
	if [ "$nur_pruefen" -eq 0 ] && [ "$PLANLAUF" -eq 1 ]; then
		laut
		mkdir -p "$ZUSTAND"
		[ -f "$ZUSTAND/wartet" ] || { printf '%s %s\n' "$v" "$lx_ver" > "$ZUSTAND/wartet"; chmod 644 "$ZUSTAND/wartet"; }
		if test_laeuft; then
			local seit=$(( $(date +%s) - $(stat -c %Y "$ZUSTAND/wartet" 2>/dev/null || date +%s) ))
			if [ "$seit" -lt "$WARTE_MAX_S" ]; then
				log "Neu: MoveEye $v · Sim $lx_ver - es läuft ein Test, wartet auf die Pause danach (seit $((seit / 60)) Min., spätestens nach $((WARTE_MAX_S / 3600)) Std.; das Dauerrechnen startet so lange nichts Neues)."
				return 0
			fi
			log "Neu: MoveEye $v · Sim $lx_ver wartet seit über $((WARTE_MAX_S / 3600)) Std. - spiele trotz laufendem Test ein (Neustarts erst danach)."
			TROTZ_TEST=1
		fi
	fi
	urls="$REPO_RAW/main/simulator3d/MoveEyeSim3D_Linux.zip"
	if [ "$herkunft" = Programmdatei ]; then urls="$REPO_RAW/v$v/simulator3d/MoveEyeSim3D_Linux.zip $urls"
	elif [ "${lx_url:--}" != "-" ]; then urls="$lx_url"          # Simulator-Anhang: nur das Release-Asset (nicht im Repository)
	else urls="$REPO_RAW/sim-$lx_ver/simulator3d/MoveEyeSim3D_Linux.zip $urls"; fi
	for u in $urls; do
		rm -f "$w/linux.zip"
		if ! laden "$u" "$w/linux.zip" 400000000; then
			[ "${lx_url:--}" != "-" ] && log "Linux-Paket (Release-Asset) nicht geladen: $u - fehlt es, oder antwortet GitHub nicht?"
			continue
		fi
		if pruefer datei "$w/linux.zip" "$lx_sha" "$lx_size" > /dev/null 2> "$w/fehler"; then zip_ok=1; break; fi
		log "Linux-Paket von $u: $(cat "$w/fehler") - nicht verwendet"
	done
	[ $zip_ok -eq 1 ] || { rm -f "$w/linux.zip"; log "ABGELEHNT: kein Linux-Paket mit der signierten Prüfsumme gefunden - nichts eingespielt"; return 1; }
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
	modul_pakete
	kiosk "$d"
	runner "$d"
	simulator "$d" "$w"
	einspielen "$d/hp/hp_update.sh" "$SELBST" 755 "dieses Update, gilt ab dem nächsten Lauf"
	# Neu starten, was neu ist - nie während eines Tests oder beim Spielen
	if [ -n "$(beschaeftigt)" ] || test_laeuft; then
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
	rm -f "$ZUSTAND/wartet"
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
