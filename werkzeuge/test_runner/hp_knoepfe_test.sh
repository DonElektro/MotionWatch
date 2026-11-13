#!/bin/bash
# MoveEye Knöpfe des Simulator-PCs (HP_FASSUNG 8: Ausschalten, Browser) - Prüfung ohne HP, ohne root, ohne echten Browser
# (läuft am Ende von controller_test.sh im CI-Job «HP-Update»; lokal: bash werkzeuge/test_runner/hp_knoepfe_test.sh).
# Ersatz für systemctl / busctl / firefox und ein Ersatz-«Simulator» (ein Prozess, der nur wartet).
#  1. hp_knoepfe.sh info: Test läuft (Pause-Datei), Browser da / nicht da, «ins BIOS» nur mit UEFI und wenn logind es kann.
#  2. hp_knoepfe.sh aus: nur drei feste Wörter, nur eine leere Wunsch-Datei.
#  3. hp_aus.sh (der Dienst, hier ohne root mit Ersatz-systemctl): genau ein fester Befehl pro Wunsch; unbekannte Namen,
#     Verknüpfungen, Ordner und alte Wünsche ohne Wirkung; «ins BIOS» nur, wenn der PC es kann; Herunterfahren geht vor.
#  4. hp_knoepfe.sh browser: eigenes Profil (700), Downloads im eigenen Ordner, nichts merken; Marke «browser_offen»
#     (= Spielen); der Simulator wird angehalten und läuft nach «zurück», nach dem Schliessen und nach einem Absturz des
#     Browsers weiter; läuft ein Test oder fehlt der Browser: öffnet nicht; beginnt ein Test: Browser zu.
#  5. hp_wache.py: Marke «browser_offen» -> Spielen-Datei (Grund «browser»), auch während gerechnet wird.
#  6. browser_leiste.py (Daten-Teil), kiosk_sitzung.sh / openbox.xml (Ctrl+Alt+Z, Rand, Sicherung «nie angehalten bleiben»).
# shellcheck disable=SC2015,SC2016  # «A && ok || fehler»: ok gibt immer 0 zurück; Ersatz-Befehle in «…» laufen erst später
set -u
HIER="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
R="$(cd "$HIER/../.." && pwd)"
BL="$R/simulator3d/beilagen_linux"
K="$BL/hp_knoepfe.sh"
A="$BL/hp_aus.sh"
W="$(mktemp -d)"
PIDS=()
# shellcheck disable=SC2154  # p: in der Falle
trap 'for p in "${PIDS[@]}"; do kill -CONT "$p" 2>/dev/null; kill "$p" 2>/dev/null; done; pkill -f "$W/bin/" 2>/dev/null; rm -rf "$W"' EXIT
F=0
ok() { echo "  ok: $*"; }
fehler() { echo "  FEHLER: $*"; F=$((F + 1)); }
warte() {   # warte SEKUNDEN BEDINGUNG…
	local t=$(( $(date +%s) + $1 )); shift
	while ! "$@"; do [ "$(date +%s)" -ge "$t" ] && return 1; sleep 0.2; done
	return 0
}
mkdir -p "$W/bin" "$W/spiel" "$W/test" "$W/efi" "$W/home" "$W/log" "$W/status"
: > "$W/aufrufe"
printf '#!/bin/sh\necho "systemctl $*" >> "%s/aufrufe"\n[ "$1" = is-active ] && [ -e "%s/aus_fehlt" ] && exit 3\nexit 0\n' "$W" "$W" > "$W/bin/systemctl"
printf '#!/bin/sh\necho "s \\"$(cat "%s/bios" 2>/dev/null || echo na)\\""\n' "$W" > "$W/bin/busctl"
cat > "$W/bin/firefox" <<EOF
#!/bin/bash
# Ersatz-Browser: merkt sich die Optionen und wartet, bis er beendet wird (oder $W/absturz erscheint)
printf '%s\n' "\$@" > "$W/firefox_args"
trap 'echo TERM >> "$W/firefox_ende"; exit 0' TERM
while [ ! -e "$W/absturz" ]; do sleep 0.2; done
exit 139
EOF
printf '#!/bin/bash\n# Ersatz-Simulator\nwhile :; do sleep 0.2; done\n' > "$W/bin/MoveEyeSim3D.x86_64"
chmod 755 "$W/bin/"*
kn() {   # hp_knoepfe.sh mit Ersatz-Umgebung
	PATH="$W/bin:$PATH" HOME="$W/home" XDG_RUNTIME_DIR="$W" MW_HPK_LIB="$BL" MW_HPK_SPIEL_DIR="$W/spiel" MW_HPK_PAUSE="$W/test/kiosk_pause" \
		MW_HPK_RUNNER="gibt-es-nicht" MW_HPK_BROWSER_DIR="$W/home/MoveEye-Browser" MW_HPK_EFI="$W/efi" MW_HPK_LOGDIR="$W/log" \
		MW_HPK_SIM_MUSTER="$W/bin/MoveEyeSim3D\\.x86_64\$" bash "$K" "$@"
}
feld() { python3 -c 'import json, sys; print(json.loads(sys.argv[1])[sys.argv[2]])' "$1" "$2" 2>/dev/null; }
st() { python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["schritt"])' "$1" 2>/dev/null; }

echo "--- 0. Form"
for f in "$K" "$A"; do bash -n "$f" && ok "bash -n $(basename "$f")" || fehler "bash -n $f"; done
if command -v shellcheck >/dev/null 2>&1; then shellcheck -x "$K" "$A" && ok "shellcheck hp_knoepfe.sh hp_aus.sh" || fehler "shellcheck"; else echo "  (shellcheck fehlt hier)"; fi
python3 -m py_compile "$BL/browser_leiste.py" && ok "py_compile browser_leiste.py" || fehler "py_compile"
! grep -n 'sudo\|pkexec\|polkit-1\|eval \|chmod [0-7]*[2367] ' "$K" "$A" | grep -v '^[^:]*:[0-9]*:#' | grep -q . && ok "kein sudo / pkexec / eval in den Skripten" || fehler "sudo / pkexec / eval gefunden"

echo "--- 1. hp_knoepfe.sh info"
echo challenge > "$W/bios"
I="$(kn info)"
[ "$(feld "$I" test)" = False ] && [ "$(feld "$I" aus)" = True ] && [ "$(feld "$I" bios)" = True ] && [ "$(feld "$I" browser)" = firefox ] && [ "$(feld "$I" fassung)" = 8 ] \
	&& ok "frei, Browser da, UEFI + logind «challenge»: $I" || fehler "info: $I"
touch "$W/test/kiosk_pause"; I="$(kn info)"; [ "$(feld "$I" test)" = True ] && ok "Pause-Datei des Test-Runners: «test»: true" || fehler "info test: $I"
touch -d '8 hours ago' "$W/test/kiosk_pause"; I="$(kn info)"; [ "$(feld "$I" test)" = False ] && ok "vergessene Pause-Datei (über 7 Std.): kein Test" || fehler "alte Pause: $I"
rm -f "$W/test/kiosk_pause"
echo na > "$W/bios"; I="$(kn info)"; [ "$(feld "$I" bios)" = False ] && ok "logind «na» (Firmware kann es nicht): «bios»: false" || fehler "bios na: $I"
echo yes > "$W/bios"; rmdir "$W/efi"; I="$(kn info)"; [ "$(feld "$I" bios)" = False ] && ok "kein UEFI-Start (/sys/firmware/efi fehlt): «bios»: false" || fehler "bios ohne efi: $I"
mkdir "$W/efi"
touch "$W/aus_fehlt"; I="$(kn info)"; [ "$(feld "$I" aus)" = False ] && ok "moveeye-aus.path nicht aktiv: «aus»: false" || fehler "aus: $I"
rm -f "$W/aus_fehlt"
mv "$W/bin/firefox" "$W/firefox.weg"
I="$(PATH="$W/bin:/usr/bin:/bin" MW_HPK_BROWSER="firefox-gibt-es-nicht" kn info)"; [ "$(feld "$I" browser)" = "" ] && ok "kein Browser installiert: «browser»: leer" || fehler "browser leer: $I"
mv "$W/firefox.weg" "$W/bin/firefox"

echo "--- 2. hp_knoepfe.sh aus"
: > "$W/aufrufe"
kn aus neustart > /dev/null && [ -f "$W/spiel/aus_neustart" ] && [ ! -s "$W/spiel/aus_neustart" ] && ok "aus neustart: leere Wunsch-Datei" || fehler "aus neustart"
rm -f "$W/spiel/aus_neustart"
for x in "" formatieren "neustart; touch $W/boese" ../x; do kn aus "$x" > /dev/null 2>&1 && fehler "aus «$x» angenommen"; done
[ -z "$(ls -A "$W/spiel")" ] && [ ! -e "$W/boese" ] && ok "anderes als herunterfahren / neustart / bios: abgelehnt, keine Datei" || fehler "aus: falsche Wörter"
ln -s "$W/ziel" "$W/spiel/aus_bios"; kn aus bios > /dev/null; [ -f "$W/spiel/aus_bios" ] && [ ! -L "$W/spiel/aus_bios" ] && [ ! -e "$W/ziel" ] \
	&& ok "liegt dort eine Verknüpfung: ersetzt, nie gefolgt" || fehler "aus: Verknüpfung"
rm -f "$W/spiel/aus_bios"
! grep -q "poweroff\|reboot" "$W/aufrufe" && ok "hp_knoepfe.sh schaltet selbst nie aus (kein systemctl poweroff / reboot)" || fehler "hp_knoepfe.sh ruft systemctl poweroff / reboot"

echo "--- 3. hp_aus.sh (Dienst, hier mit Ersatz-systemctl)"
dienst() { PATH="$W/bin:$PATH" MW_AUS_DIR="$W/spiel" MW_AUS_STATUS_DIR="$W/status" MW_AUS_EFI="$W/efi" MW_AUS_RUNNER="gibt-es-nicht" \
	MW_AUS_PAUSE="$W/test/kiosk_pause" bash "$A" > "$W/aus.log" 2>&1; }
rufe() { grep -c "poweroff\|reboot" "$W/aufrufe"; }
: > "$W/aufrufe"; dienst; [ "$(rufe)" = 0 ] && ok "kein Wunsch: nichts" || fehler "ohne Wunsch ausgeschaltet"
touch "$W/spiel/aus_herunterfahren"; dienst
[ "$(grep -c . "$W/aufrufe")" = 1 ] && grep -qx "systemctl poweroff" "$W/aufrufe" && [ ! -e "$W/spiel/aus_herunterfahren" ] && [ "$(st "$W/status/status.json")" = herunterfahren ] \
	&& ok "aus_herunterfahren: genau «systemctl poweroff», Wunsch weggeräumt" || { fehler "herunterfahren"; cat "$W/aufrufe" "$W/aus.log"; }
: > "$W/aufrufe"; touch "$W/spiel/aus_neustart"; dienst; [ "$(grep -c . "$W/aufrufe")" = 1 ] && grep -qx "systemctl reboot" "$W/aufrufe" && ok "aus_neustart: genau «systemctl reboot»" || fehler "neustart"
: > "$W/aufrufe"; echo yes > "$W/bios"; touch "$W/spiel/aus_bios"; dienst
grep -qx "systemctl reboot --firmware-setup" "$W/aufrufe" && [ "$(rufe)" = 1 ] && ok "aus_bios (PC kann es): «systemctl reboot --firmware-setup»" || fehler "bios"
: > "$W/aufrufe"; echo na > "$W/bios"; touch "$W/spiel/aus_bios"; dienst
[ "$(rufe)" = 0 ] && [ "$(st "$W/status/status.json")" = bios_geht_nicht ] && ok "aus_bios, die Firmware kann es nicht: nichts getan (kein gewöhnlicher Neustart)" || fehler "bios na"
: > "$W/aufrufe"; echo yes > "$W/bios"; rmdir "$W/efi"; touch "$W/spiel/aus_bios"; dienst; mkdir "$W/efi"
[ "$(rufe)" = 0 ] && ok "aus_bios ohne UEFI-Start: nichts getan" || fehler "bios ohne efi"
: > "$W/aufrufe"; touch "$W/spiel/aus_formatieren" "$W/spiel/aus_" "$W/spiel/aus_neustart.bak" "$W/spiel/aus_HERUNTERFAHREN"
ln -s /etc/hostname "$W/spiel/aus_neustart"; mkdir "$W/spiel/aus_herunterfahren"; touch "$W/spiel/aus_herunterfahren/x" "$W/spiel/spielen" "$W/spiel/controller_koppeln"
dienst
[ "$(rufe)" = 0 ] && [ -z "$(find "$W/spiel" -name 'aus_*')" ] && [ -e /etc/hostname ] && [ -e "$W/spiel/spielen" ] && [ -e "$W/spiel/controller_koppeln" ] \
	&& ok "unbekannte Namen, Verknüpfung, Ordner: ohne Wirkung, alle weggeräumt; andere Dateien des Kiosks bleiben" || { fehler "falsche Wünsche"; cat "$W/aufrufe"; ls -la "$W/spiel"; }
rm -f "$W/spiel/spielen" "$W/spiel/controller_koppeln"
: > "$W/aufrufe"; touch -d '10 minutes ago' "$W/spiel/aus_herunterfahren"; dienst
[ "$(rufe)" = 0 ] && [ ! -e "$W/spiel/aus_herunterfahren" ] && ok "alter Wunsch (10 Min.): ohne Wirkung" || fehler "alter Wunsch"
: > "$W/aufrufe"; touch "$W/spiel/aus_neustart" "$W/spiel/aus_bios" "$W/spiel/aus_herunterfahren"; dienst
[ "$(rufe)" = 1 ] && grep -qx "systemctl poweroff" "$W/aufrufe" && ok "mehrere Wünsche: ein Befehl, Herunterfahren geht vor" || { fehler "mehrere Wünsche"; cat "$W/aufrufe"; }
: > "$W/aufrufe"; touch "$W/test/kiosk_pause" "$W/spiel/aus_neustart"; dienst; rm -f "$W/test/kiosk_pause"
[ "$(rufe)" = 1 ] && grep -q "es läuft ein Test" "$W/aus.log" && ok "läuft ein Test: wird ausgeführt (der Simulator hat gefragt) und steht im Protokoll" || fehler "Test-Hinweis"
! grep -qiE '([0-9a-f]{2}:){5}' "$W/status/status.json" && python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); assert set(d) == {"schritt", "t"}' "$W/status/status.json" \
	&& ok "Status: nur «schritt» und «t»" || fehler "Status-Datei"

echo "--- 4. hp_knoepfe.sh browser"
bash "$W/bin/MoveEyeSim3D.x86_64" &
SIM=$!; PIDS+=("$SIM")
zustand() { ps -o stat= -p "$SIM" 2>/dev/null | cut -c1; }
angehalten() { [ "$(zustand)" = T ]; }
laeuft() { case "$(zustand)" in S|R) return 0 ;; esac; return 1; }
bpid() { pgrep -f "^/bin/bash $W/bin/firefox " | head -n 1; }
P="$W/home/MoveEye-Browser"
touch "$W/test/kiosk_pause"; kn browser > "$W/b.out" 2>&1; rc=$?; rm -f "$W/test/kiosk_pause"
[ $rc -eq 3 ] && [ "$(st "$W/spiel/browser_status.json")" = test ] && [ ! -e "$W/firefox_args" ] && [ ! -e "$W/spiel/browser_offen" ] && laeuft \
	&& ok "ein Test läuft: der Browser öffnet nicht (Status «test»), der Simulator läuft weiter" || { fehler "Browser trotz Test"; cat "$W/b.out"; }
PATH="$W/bin:/usr/bin:/bin" MW_HPK_BROWSER="firefox-gibt-es-nicht" kn browser > "$W/b.out" 2>&1; rc=$?
[ $rc -eq 4 ] && [ "$(st "$W/spiel/browser_status.json")" = kein_browser ] && ok "kein Browser installiert: Status «kein_browser», nichts wird installiert" || fehler "ohne Browser"
kn browser > "$W/b.out" 2>&1 &
KP=$!; PIDS+=("$KP")
warte 10 test -s "$W/firefox_args" && warte 5 test -e "$W/spiel/browser_offen" && [ "$(st "$W/spiel/browser_status.json")" = offen ] \
	&& ok "Browser gestartet, Marke «browser_offen» (zählt als Spielen), Status «offen»" || { fehler "Browser startet nicht"; cat "$W/b.out" "$W/log/"* 2>/dev/null; }
grep -qx -- "--no-remote" "$W/firefox_args" && grep -qx -- "--profile" "$W/firefox_args" && grep -qx "$P/profil" "$W/firefox_args" \
	&& ok "eigenes Profil ($P/profil), eigene Instanz (--no-remote)" || { fehler "Profil-Optionen"; cat "$W/firefox_args"; }
[ "$(stat -c %a "$P")" = 700 ] && [ "$(stat -c %a "$P/profil")" = 700 ] && [ -d "$P/Downloads" ] \
	&& grep -qx "user_pref(\"browser.download.dir\", \"$P/Downloads\");" "$P/profil/user.js" && grep -q '"signon.rememberSignons", false' "$P/profil/user.js" \
	&& grep -q '"identity.fxaccounts.enabled", false' "$P/profil/user.js" && grep -q '"browser.download.folderList", 2' "$P/profil/user.js" \
	&& ok "Profil nur für den Benutzer (700); Downloads in den eigenen Ordner; keine Passwörter merken, kein Konto / Sync" || { fehler "Profil"; cat "$P/profil/user.js"; }
warte 8 angehalten && ok "der Simulator ist angehalten (kein Ton, keine Rechenlast), solange der Browser offen ist" || fehler "Simulator nicht angehalten ($(zustand))"
kn browser 2>&1 | grep -q "schon offen" && [ "$(pgrep -fc "^/bin/bash $W/bin/firefox ")" = 1 ] && ok "zweiter Druck auf den Knopf: kein zweiter Browser" || fehler "zweiter Browser"
M0=$(stat -c %Y "$W/spiel/browser_offen"); sleep 6; [ "$(stat -c %Y "$W/spiel/browser_offen")" -gt "$M0" ] && ok "die Marke wird laufend aufgefrischt (Puls)" || fehler "Marke ohne Puls"
kn zurueck
warte 10 laeuft && warte 10 test ! -e "$W/spiel/browser_offen" && ! kill -0 "$KP" 2>/dev/null && [ -z "$(bpid)" ] && [ "$(st "$W/spiel/browser_status.json")" = zu ] \
	&& grep -q TERM "$W/firefox_ende" && ok "«Zurück» (Leiste / Ctrl+Alt+Z): Browser sauber beendet, Simulator läuft weiter, Marke weg, Status «zu»" || { fehler "Zurück"; cat "$W/b.out"; }
rm -f "$W/firefox_args" "$W/firefox_ende"
kn browser > "$W/b.out" 2>&1 &
KP=$!; PIDS+=("$KP")
warte 10 test -s "$W/firefox_args" && warte 8 angehalten || fehler "zweiter Start"
touch "$W/absturz"
warte 10 laeuft && warte 5 test ! -e "$W/spiel/browser_offen" && ! kill -0 "$KP" 2>/dev/null \
	&& ok "Browser stürzt ab / wird geschlossen: der Simulator kommt von selbst zurück" || { fehler "nach Absturz bleibt der Simulator stehen ($(zustand))"; cat "$W/b.out"; }
rm -f "$W/absturz" "$W/firefox_args" "$W/firefox_ende"
kn browser > "$W/b.out" 2>&1 &
KP=$!; PIDS+=("$KP")
warte 10 test -s "$W/firefox_args" && warte 8 angehalten || fehler "dritter Start"
touch "$W/test/kiosk_pause"
warte 10 laeuft && [ -z "$(bpid)" ] && grep -q "Ein Test beginnt" "$W/log/knoepfe.log" && ok "ein Test beginnt, während der Browser offen ist: Browser zu, Simulator weiter" || fehler "Test beginnt"
rm -f "$W/test/kiosk_pause" "$W/firefox_args"
kn browser > "$W/b.out" 2>&1 &
KP=$!; PIDS+=("$KP")
warte 10 test -s "$W/firefox_args" && warte 8 angehalten || fehler "vierter Start"
kill -KILL "$KP" 2>/dev/null; sleep 0.5
angehalten && kn zurueck && warte 5 laeuft && ok "wird hp_knoepfe.sh hart beendet: «zurück» (Ctrl+Alt+Z) lässt den Simulator trotzdem weiterlaufen" || fehler "Simulator bleibt angehalten"
pkill -f "^/bin/bash $W/bin/firefox " 2>/dev/null
kill "$SIM" 2>/dev/null

echo "--- 5. hp_wache.py: Browser offen = Spielen"
rm -f "$W/spiel/"*
python3 -I - "$BL/hp_wache.py" "$W" <<'EOF' && ok "Marke «browser_offen» frisch: Spielen (Grund «browser»), auch während gerechnet wird; alte Marke: nichts" || fehler "hp_wache.py Browser"
import importlib.util, json, os, sys, time, types
spec = importlib.util.spec_from_file_location("hw", sys.argv[1]); hw = importlib.util.module_from_spec(spec); spec.loader.exec_module(hw)
hw.log = lambda *a: None
w = sys.argv[2]
a = types.SimpleNamespace(spiel_datei=os.path.join(w, "spiel", "spielen"), pause=os.path.join(w, "test", "kiosk_pause"), pause_max_s=25200, ruhe_s=900,
                          status_port=0, zuschauer_s=60, pad_quelle="", pad_scan_s=5.0, pad_udev="", sim_ports=[], pad_ruhe_s=1200)
wa = hw.Wache(a)
marke = os.path.join(w, "spiel", "browser_offen")
wa.aktivitaet(wa.neu_zustand()); assert not os.path.exists(a.spiel_datei)
open(marke, "w").close(); os.utime(marke, (time.time() - 300, time.time() - 300))
wa.aktivitaet(wa.neu_zustand()); assert not os.path.exists(a.spiel_datei), "alte Marke"
os.utime(marke, None)
assert wa.neu_zustand() == "frei"
wa.aktivitaet("frei"); assert json.load(open(a.spiel_datei))["grund"] == "browser"
assert wa.neu_zustand() == "spielen"
os.utime(a.spiel_datei, (time.time() - 600, time.time() - 600)); wa.aktivitaet("spielen")
assert time.time() - os.stat(a.spiel_datei).st_mtime < 5, "nicht aufgefrischt"
os.remove(a.spiel_datei); open(a.pause, "w").close()
assert wa.neu_zustand() == "rechnet"
wa.aktivitaet("rechnet"); assert json.load(open(a.spiel_datei))["grund"] == "browser"
EOF
rm -f "$W/test/kiosk_pause"

echo "--- 6. Leiste, Sitzung, Openbox"
python3 -I - "$BL/browser_leiste.py" "$W/leiste" <<'EOF' && ok "browser_leiste.py: «zurück» ist nur eine leere Datei, nie über eine Verknüpfung; Höhe = Rand in openbox.xml" || fehler "browser_leiste.py"
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("bl", sys.argv[1]); bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
w = sys.argv[2]; os.makedirs(w); p = os.path.join(w, "browser_zu")
assert bl.zu_schreiben(p) and os.path.getsize(p) == 0
os.remove(p); os.symlink(os.path.join(w, "ziel"), p); assert not bl.zu_schreiben(p) and not os.path.exists(os.path.join(w, "ziel"))
assert not bl.zu_schreiben(os.path.join(w, "fehlt", "x")) and bl.HOEHE == 40
EOF
OB="$W/openbox.xml"
sed -n "/^schreibe \"\$LIB\/openbox.xml\" 644 <<'EOF'\$/,/^EOF\$/p" "$BL/kiosk_ein.sh" | sed '1d;$d' > "$OB"
python3 -c 'import sys, xml.dom.minidom; xml.dom.minidom.parse(sys.argv[1])' "$OB" && grep -q 'key="C-A-z".*hp_knoepfe.sh zurueck' "$OB" \
	&& grep -q '<margins><top>40</top>' "$OB" && grep -q 'class="?irefox\*".*<maximized>yes</maximized>' "$OB" \
	&& ok "openbox.xml (kiosk_ein.sh): gültig, Ctrl+Alt+Z, Rand 40 für die Leiste, Browser maximiert" || fehler "openbox.xml in kiosk_ein.sh"
S="$BL/kiosk_sitzung.sh"
grep -q 'export MOVEEYE_HP_KIOSK="$KNOEPFE"' "$S" && grep -q 'browser_offen || sim_signal CONT' "$S" \
	&& ok "kiosk_sitzung.sh: sagt dem Simulator, wo die Knöpfe sind; ohne offenen Browser bleibt der Simulator nie angehalten" || fehler "kiosk_sitzung.sh"
grep -q 'hp_knoepfe.sh hp_aus.sh browser_leiste.py' "$R/werkzeuge/linux_paket.sh" && ok "linux_paket.sh packt die drei neuen Dateien ein" || fehler "linux_paket.sh"

echo
if [ $F -eq 0 ]; then echo "HP-Knöpfe-Test: OK"; else echo "HP-Knöpfe-Test: $F Fehler"; fi
exit $F
