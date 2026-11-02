#!/bin/bash
# MoveEye HP-Update - Prüfung ohne echten HP (CI-Job «HP-Update»; lokal: sudo bash werkzeuge/test_runner/hp_update_test.sh).
#  1. Prüfkette mit den echten Dateien dieses Stands (versions.json, Programmdatei, Linux-ZIP): gültig wird angenommen,
#     jede Verfälschung (Signatur, Prüfsumme im Manifest, Programmdatei, ZIP, unsignierte Liste) abgelehnt.
#  2. Einspielen in einem Ersatz-Wurzelordner mit einem TEST-Schlüssel (nur in der Kopie dieses Tests; das echte Skript kennt
#     nur den Schlüssel des Besitzers): Kiosk, Haken, Dienst-Einstellungen, Simulator, sich selbst; zweiter Lauf ändert
#     nichts; Pause-Datei = verschoben; ältere Version = abgelehnt. systemctl / apt-get werden nur aufgezeichnet.
# Der echte Signierschlüssel wird nie gebraucht. Braucht root (runuser, chown), python3, unzip, zip, curl.
# shellcheck disable=SC2015,SC2016  # «A && ok || fehler»: ok gibt immer 0 zurück; Ersatz-Befehle in '…' laufen erst später
set -u
HIER="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
R="$(cd "$HIER/../.." && pwd)"
U="$HIER/hp_update.sh"
W="$(mktemp -d)"
trap 'rm -rf "$W"' EXIT
F=0
ok() { echo "  ok: $*"; }
fehler() { echo "  FEHLER: $*"; F=$((F + 1)); }
[ "$(id -u)" -eq 0 ] || { echo "Bitte als root (sudo) starten"; exit 1; }

# ---------------------------------------------------------------- 1. echte Prüfkette
NEUSTE="$(cd "$R" && python3 -c 'import json; print(json.load(open("versions.json"))["versions"][0]["file"])')"
quelle() {   # quelle NAME: Ersatz-Quelle mit Kopien der echten Dateien
	mkdir -p "$W/$1/main/simulator3d"
	cp "$R/versions.json" "$R/$NEUSTE" "$W/$1/main/"
	cp "$R/simulator3d/MoveEyeSim3D_Linux.zip" "$W/$1/main/simulator3d/"
}
pruefe() {   # pruefe NAME ERWARTET(0|1) BESCHREIBUNG
	local rc
	MOVEEYE_HP_QUELLE="file://$W/$1" bash "$U" --pruefen > "$W/$1.log" 2>&1; rc=$?
	if { [ "$2" -eq 0 ] && [ $rc -eq 0 ]; } || { [ "$2" -ne 0 ] && [ $rc -ne 0 ] && grep -q ABGELEHNT "$W/$1.log"; }; then
		ok "$3 ($(grep -E 'ABGELEHNT|Prüfung OK' "$W/$1.log" | sed 's/^[0-9: -]*//' | head -n 1))"
	else
		fehler "$3 (Exit $rc)"; sed 's/^/    /' "$W/$1.log"
	fi
}
json() { python3 - "$@"; }
echo "--- 1. Prüfkette mit den echten Dateien ($NEUSTE)"
python3 -c 'import json; e=json.load(open("'"$R"'/versions.json"))["versions"][0]; exit(0 if e.get("sig") else 1)' || {
	echo "  (neuste Version noch nicht signiert - Teil 1 übersprungen, der Besitzer signiert später)"; NEUSTE=""; }
if [ -n "$NEUSTE" ]; then
	quelle gut; pruefe gut 0 "gültig signiert"
	quelle sig; json "$W/sig/main/versions.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
for e in d["versions"]:
    e["sig"] = ("0" if e.get("sig", "x")[0] != "0" else "1") + e.get("sig", "")[1:]
json.dump(d, open(sys.argv[1], "w"))
EOF
	pruefe sig 1 "Signatur verfälscht"
	quelle sha; json "$W/sha/main/versions.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
for e in d["versions"]:
    e["sha256"] = "0" * 64
json.dump(d, open(sys.argv[1], "w"))
EOF
	pruefe sha 1 "Prüfsumme im Manifest geändert"
	quelle ohne; json "$W/ohne/main/versions.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
for e in d["versions"]:
    e.pop("sig", None)
json.dump(d, open(sys.argv[1], "w"))
EOF
	pruefe ohne 1 "nur unsignierte Versionen"
	quelle prog; printf '\n# verändert\n' >> "$W/prog/main/$NEUSTE"; pruefe prog 1 "Programmdatei verändert"
	quelle zip; python3 -c 'import sys; f=open(sys.argv[1], "r+b"); f.seek(-100, 2); b=f.read(1); f.seek(-100, 2); f.write(bytes([b[0] ^ 255]))' \
		"$W/zip/main/simulator3d/MoveEyeSim3D_Linux.zip"
	pruefe zip 1 "Linux-ZIP verändert (1 Byte)"
	rm -rf "$W/gut" "$W/sig" "$W/sha" "$W/ohne" "$W/prog" "$W/zip"
fi

# ---------------------------------------------------------------- 2. Einspielen mit Test-Schlüssel
echo "--- 2. Einspielen (Ersatz-Wurzel, Test-Schlüssel)"
X="$W/wurzel"
B="$W/bin"
mkdir -p "$X/usr/local/lib/moveeye-kiosk" "$X/usr/local/lib/moveeye-runner" "$X/var/lib/mwrunner/runner" "$X/etc" \
	"$X/run/moveeye-test" "$X/usr/local/sbin" "$B"
echo "actions.runner.Test-Repo.moveeye-hp.service" > "$X/var/lib/mwrunner/runner/.service"
echo '{"geheim": "bleibt"}' > "$X/var/lib/mwrunner/runner/.credentials"
SIMD="$X/home/kiosk/MoveEyeSim3D"
mkdir -p "$SIMD"
printf '#!/bin/sh\necho alt\n' > "$SIMD/MoveEyeSim3D.x86_64"; chmod 755 "$SIMD/MoveEyeSim3D.x86_64"
chown -R nobody "$X/home/kiosk"
printf 'SIM=%q\nSIM_ARGS=(--fullscreen)\n' "$SIMD/MoveEyeSim3D.x86_64" > "$X/etc/moveeye-kiosk.conf"; chmod 644 "$X/etc/moveeye-kiosk.conf"
for b in systemctl apt-get systemd-run; do
	printf '#!/bin/sh\necho "%s $*" >> "%s/aufrufe.txt"\n[ "%s $1 $2" = "systemctl is-active -q" ] && exit 0\nexit 0\n' "$b" "$W" "$b" > "$B/$b"
	chmod 755 "$B/$b"
done
# Test-Schlüssel und signierte Ersatz-Version 9.0.0 mit einer Linux-ZIP aus linux_paket.sh
printf '#!/bin/sh\necho neu\n' > "$W/sim.x86_64"
bash "$R/werkzeuge/linux_paket.sh" "$W/sim.x86_64" "$W/q/main/simulator3d/MoveEyeSim3D_Linux.zip" > /dev/null || fehler "linux_paket.sh"
python3 - "$R/quelle/380_updates.py" "$W" <<'EOF'
import hashlib, json, os, re, sys
src, w = sys.argv[1:]
t = open(src, encoding="utf-8").read()
a = t.index("def _ed25519_impl"); b = t.index("return public, sign, verify", a) + len("return public, sign, verify")
ns = {"hashlib": hashlib}; exec(t[a:b], ns)
public, sign, verify = ns["_ed25519_impl"]()
seed = hashlib.sha256(b"nur ein Test-Schluessel").digest()
open(os.path.join(w, "pub.txt"), "w").write(public(seed).hex())
z = open(os.path.join(w, "q/main/simulator3d/MoveEyeSim3D_Linux.zip"), "rb").read()
def version(v, ordner):
    fn = "webcam_bewegung_%s.py" % v.replace(".", "_")
    prog = ('APP_VERSION = "%s"\nSIM3D_LINUX = {"version": "%s", "file": "simulator3d/MoveEyeSim3D_Linux.zip", "size": %d,\n'
            '               "sha256": "%s", "stem": "MoveEyeSim3D_Linux"}\n') % (v, v, len(z), hashlib.sha256(z).hexdigest())
    open(os.path.join(w, ordner, "main", fn), "w").write(prog)
    sha = hashlib.sha256(prog.encode()).hexdigest()
    return {"version": v, "file": fn, "sha256": sha, "sig": sign(seed, ("MotionWatch|%s|%s|%s" % (v, fn, sha)).encode()).hex()}
os.makedirs(os.path.join(w, "alt/main/simulator3d"), exist_ok=True)
json.dump({"versions": [version("9.0.0", "q")]}, open(os.path.join(w, "q/main/versions.json"), "w"))
json.dump({"versions": [version("8.0.0", "alt")]}, open(os.path.join(w, "alt/main/versions.json"), "w"))
os.link(os.path.join(w, "q/main/simulator3d/MoveEyeSim3D_Linux.zip"), os.path.join(w, "alt/main/simulator3d/MoveEyeSim3D_Linux.zip"))
EOF
# Kopie des Skripts: Test-Schlüssel, Pfade in der Ersatz-Wurzel (das echte Skript bleibt unverändert)
T="$W/hp_update_kopie.sh"
sed -e "s#^UPDATE_PUBKEY=\"[0-9a-f]*\"#UPDATE_PUBKEY=\"$(cat "$W/pub.txt")\"#" \
	-e "s#\"/usr/local/#\"$X/usr/local/#g" -e "s#\"/etc/#\"$X/etc/#g" -e "s#\"/var/lib/#\"$X/var/lib/#g" \
	-e "s#\"/var/log/#\"$X/var/log/#g" -e "s#\"/run/moveeye-test/#\"$X/run/moveeye-test/#g" \
	-e "s#/run/lock/moveeye-hp-update.lock#$W/sperre#g" "$U" > "$T"
grep -q "$(cat "$W/pub.txt")" "$T" || fehler "Test-Schlüssel nicht eingesetzt"
mkdir -p "$X/var/log"
lauf() { PATH="$B:$PATH" MOVEEYE_HP_QUELLE="file://$W/$1" bash "$T" > "$W/lauf.log" 2>&1; }

chmod 755 "$W" "$X" "$X/home"
PATH="$B:$PATH" bash "$T" --einrichten --ohne-lauf > "$W/lauf.log" 2>&1 || { fehler "--einrichten"; sed 's/^/    /' "$W/lauf.log"; }
grep -q "systemctl enable moveeye-hp-update.timer" "$W/aufrufe.txt" && ok "--einrichten: Zeitplan eingeschaltet" || fehler "Zeitplan"
[ -f "$X/etc/systemd/system/moveeye-hp-update.service" ] && grep -q "OnCalendar=\*-\*-\* 03:17" "$X/etc/systemd/system/moveeye-hp-update.timer" \
	&& ok "--einrichten: Dienst und Zeitplan 03:17" || fehler "Dienst-/Zeitplan-Datei"
cmp -s "$T" "$X/usr/local/sbin/moveeye-hp-update" && ok "--einrichten: sich selbst abgelegt" || fehler "nicht abgelegt"
: > "$W/aufrufe.txt"
lauf q || { fehler "erster Lauf (Exit $?)"; sed 's/^/    /' "$W/lauf.log"; }
grep -q "Fertig: MoveEye 9.0.0 eingespielt" "$W/lauf.log" && ok "erster Lauf: eingespielt" || { fehler "nicht eingespielt"; sed 's/^/    /' "$W/lauf.log"; }
for f in usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh usr/local/lib/moveeye-kiosk/testbild.py usr/local/lib/moveeye-kiosk/moveeye.png \
	usr/local/lib/moveeye-runner/job_start.sh usr/local/lib/moveeye-runner/job_ende.sh usr/local/lib/moveeye-runner/runner_entfernen.sh \
	etc/systemd/system/actions.runner.Test-Repo.moveeye-hp.service.d/moveeye.conf usr/local/sbin/moveeye-hp-update; do
	[ -f "$X/$f" ] || { fehler "$f fehlt"; continue; }
	[ "$(stat -c %U "$X/$f")" = root ] || fehler "$f gehört nicht root"
done
cmp -s "$X/usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh" "$R/simulator3d/beilagen_linux/kiosk_sitzung.sh" && ok "kiosk_sitzung.sh wie im Paket" || fehler "kiosk_sitzung.sh"
cmp -s "$X/usr/local/sbin/moveeye-hp-update" "$U" && ok "sich selbst eingespielt" || fehler "moveeye-hp-update"
[ "$(stat -c %a "$X/usr/local/lib/moveeye-runner/job_start.sh")" = 755 ] && ok "Haken ausführbar" || fehler "Haken-Rechte"
grep -q '^echo neu' "$SIMD/MoveEyeSim3D.x86_64" && [ "$(stat -c %U "$SIMD/MoveEyeSim3D.x86_64")" = nobody ] && [ -x "$SIMD/MoveEyeSim3D.x86_64" ] \
	&& ok "Simulator ersetzt (als Benutzer des Kiosks)" || fehler "Simulator nicht ersetzt"
[ -e "$SIMD/hp_update.sh" ] && fehler "hp/ in den Simulator-Ordner kopiert"
[ "$(cat "$X/var/lib/mwrunner/runner/.credentials")" = '{"geheim": "bleibt"}' ] && ok "Anmeldung des Runners unberührt" || fehler ".credentials verändert"
grep -q "apt-get install .*python3-tk" "$W/aufrufe.txt" && ok "fehlende Pakete nachinstalliert" || echo "  (python3-tk war schon da)"
grep -q "systemctl restart actions.runner.Test-Repo.moveeye-hp.service" "$W/aufrufe.txt" && ok "Runner-Dienst neu gestartet" || fehler "Runner-Dienst nicht neu gestartet"
grep -q "systemctl restart display-manager" "$W/aufrufe.txt" && ok "Kiosk neu gestartet" || fehler "Kiosk nicht neu gestartet"

: > "$W/aufrufe.txt"
lauf q; grep -q "Schon eingespielt" "$W/lauf.log" && ok "zweiter Lauf: nichts zu tun" || { fehler "zweiter Lauf"; sed 's/^/    /' "$W/lauf.log"; }
PATH="$B:$PATH" MOVEEYE_HP_QUELLE="file://$W/q" bash "$T" --immer > "$W/lauf.log" 2>&1
grep -q "(0 Datei(en) neu)" "$W/lauf.log" && ! grep -q "restart" "$W/aufrufe.txt" && ok "--immer: idempotent, kein Neustart" \
	|| { fehler "--immer nicht idempotent"; sed 's/^/    /' "$W/lauf.log" "$W/aufrufe.txt"; }
lauf alt; grep -q "ABGELEHNT: 8.0.0 ist älter" "$W/lauf.log" && ok "ältere Version abgelehnt" || { fehler "Rückschritt nicht abgelehnt"; sed 's/^/    /' "$W/lauf.log"; }
echo "8.0.0" > "$X/var/lib/moveeye-hp-update/version"
touch "$X/run/moveeye-test/kiosk_pause"
echo "# alt" > "$X/usr/local/lib/moveeye-kiosk/testbild.py"
lauf q; grep -q "Es läuft ein Test - verschoben" "$W/lauf.log" && [ "$(cat "$X/usr/local/lib/moveeye-kiosk/testbild.py")" = "# alt" ] \
	&& ok "Test läuft: verschoben, nichts geändert" || { fehler "trotz Pause eingespielt"; sed 's/^/    /' "$W/lauf.log"; }
rm -f "$X/run/moveeye-test/kiosk_pause"
lauf q; cmp -s "$X/usr/local/lib/moveeye-kiosk/testbild.py" "$R/simulator3d/beilagen_linux/testbild.py" && ok "nach dem Test eingespielt" || fehler "nach dem Test"

echo
if [ $F -eq 0 ]; then echo "HP-Update-Test: OK"; else echo "HP-Update-Test: $F Fehler"; fi
exit $F
