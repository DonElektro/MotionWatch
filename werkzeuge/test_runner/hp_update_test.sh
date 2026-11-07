#!/bin/bash
# MoveEye HP-Update - Prüfung ohne echten HP (CI-Job «HP-Update»; lokal: sudo bash werkzeuge/test_runner/hp_update_test.sh).
#  1. Prüfkette mit den echten Dateien dieses Stands (versions.json, Programmdatei, Linux-ZIP): gültig wird angenommen,
#     jede Verfälschung (Signatur, Prüfsumme im Manifest, Programmdatei, ZIP, unsignierte Liste) abgelehnt.
#     Drei Spuren (HP_FASSUNG 3): hat die echte Liste einen Block «sim», dazu dessen Verfälschungen.
#  2. Einspielen in einem Ersatz-Wurzelordner mit einem TEST-Schlüssel (nur in der Kopie dieses Tests; das echte Skript kennt
#     nur den Schlüssel des Besitzers): Kiosk, Haken, Dienst-Einstellungen, Simulator, sich selbst; zweiter Lauf ändert
#     nichts; Pause-Datei = verschoben; ältere Version = abgelehnt. systemctl / apt-get werden nur aufgezeichnet.
#  3. Drei Spuren: ein Sim-Release allein (Block «sim» in versions.json, ohne neue Programmdatei) wird eingespielt;
#     verfälschter Block «sim» = abgelehnt (kein Ausweichen auf die Programmdatei), ältere Sim = abgelehnt, neue MoveEye bei
#     gleicher Sim = nichts zu laden.
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
	# Drei Spuren: mit Block «sim» lädt der HP die Programmdatei gar nicht (Sim-Prüfsummen aus der signierten Liste) - dann
	# ändert eine veränderte Programmdatei nichts am HP; ohne Block «sim» muss sie abgelehnt werden
	if python3 -c 'import json, sys; sys.exit(0 if (json.load(open("'"$R"'/versions.json")).get("sim") or {}).get("linux", {}).get("sig") else 1)'; then
		quelle prog; printf '\n# verändert\n' >> "$W/prog/main/$NEUSTE"; pruefe prog 0 "Programmdatei verändert, Block «sim» da: Programmdatei nicht gebraucht"
	else
		quelle prog; printf '\n# verändert\n' >> "$W/prog/main/$NEUSTE"; pruefe prog 1 "Programmdatei verändert"
	fi
	quelle zip; python3 -c 'import sys; f=open(sys.argv[1], "r+b"); f.seek(-100, 2); b=f.read(1); f.seek(-100, 2); f.write(bytes([b[0] ^ 255]))' \
		"$W/zip/main/simulator3d/MoveEyeSim3D_Linux.zip"
	pruefe zip 1 "Linux-ZIP verändert (1 Byte)"
	if python3 -c 'import json, sys; sys.exit(0 if (json.load(open("'"$R"'/versions.json")).get("sim") or {}).get("linux", {}).get("sig") else 1)'; then
		quelle simsig; json "$W/simsig/main/versions.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
s = d["sim"]["linux"]["sig"]; d["sim"]["linux"]["sig"] = ("0" if s[0] != "0" else "1") + s[1:]
json.dump(d, open(sys.argv[1], "w"))
EOF
		pruefe simsig 1 "Block «sim»: Signatur verfälscht"
		quelle simsha; json "$W/simsha/main/versions.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
d["sim"]["linux"]["sha256"] = "0" * 64
json.dump(d, open(sys.argv[1], "w"))
EOF
		pruefe simsha 1 "Block «sim»: Prüfsumme geändert"
		rm -rf "$W/simsig" "$W/simsha"
	else
		echo "  (versions.json noch ohne Block «sim» - Prüfung über die Programmdatei)"
	fi
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
for b in systemctl apt-get systemd-run systemd-tmpfiles; do
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
	-e "s#\"/run/moveeye-spiel/#\"$X/run/moveeye-spiel/#g" \
	-e "s#/run/lock/moveeye-hp-update.lock#$W/sperre#g" "$U" > "$T"
grep -q "$(cat "$W/pub.txt")" "$T" || fehler "Test-Schlüssel nicht eingesetzt"
mkdir -p "$X/var/log"
lauf() { PATH="$B:$PATH" MOVEEYE_HP_QUELLE="file://$W/$1" bash "$T" > "$W/lauf.log" 2>&1; }

chmod 755 "$W" "$X" "$X/home"
PATH="$B:$PATH" bash "$T" --einrichten --ohne-lauf > "$W/lauf.log" 2>&1 || { fehler "--einrichten"; sed 's/^/    /' "$W/lauf.log"; }
grep -q "systemctl enable moveeye-hp-update.timer" "$W/aufrufe.txt" && ok "--einrichten: Zeitplan eingeschaltet" || fehler "Zeitplan"
grep -q -- "--zeitplan" "$X/etc/systemd/system/moveeye-hp-update.service" && grep -q "OnCalendar=\*:07/15" "$X/etc/systemd/system/moveeye-hp-update.timer" \
	&& ok "--einrichten: Dienst (--zeitplan) und Zeitplan alle 15 Min." || fehler "Dienst-/Zeitplan-Datei"
cmp -s "$T" "$X/usr/local/sbin/moveeye-hp-update" && ok "--einrichten: sich selbst abgelegt" || fehler "nicht abgelegt"
: > "$W/aufrufe.txt"
lauf q || { fehler "erster Lauf (Exit $?)"; sed 's/^/    /' "$W/lauf.log"; }
grep -q "Fertig: MoveEye 9.0.0 · Sim 9.0.0 eingespielt" "$W/lauf.log" && ok "erster Lauf: eingespielt" || { fehler "nicht eingespielt"; sed 's/^/    /' "$W/lauf.log"; }
for f in usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh usr/local/lib/moveeye-kiosk/testbild.py usr/local/lib/moveeye-kiosk/moveeye.png \
	usr/local/lib/moveeye-kiosk/hp_wache.py etc/tmpfiles.d/moveeye-spiel.conf \
	usr/local/lib/moveeye-runner/job_start.sh usr/local/lib/moveeye-runner/job_ende.sh usr/local/lib/moveeye-runner/runner_entfernen.sh \
	etc/systemd/system/actions.runner.Test-Repo.moveeye-hp.service.d/moveeye.conf usr/local/sbin/moveeye-hp-update; do
	[ -f "$X/$f" ] || { fehler "$f fehlt"; continue; }
	[ "$(stat -c %U "$X/$f")" = root ] || fehler "$f gehört nicht root"
done
cmp -s "$X/usr/local/lib/moveeye-kiosk/kiosk_sitzung.sh" "$R/simulator3d/beilagen_linux/kiosk_sitzung.sh" && ok "kiosk_sitzung.sh wie im Paket" || fehler "kiosk_sitzung.sh"
cmp -s "$X/usr/local/sbin/moveeye-hp-update" "$U" && ok "sich selbst eingespielt" || fehler "moveeye-hp-update"
grep -q "^d $X/run/moveeye-spiel 0755 nobody nobody -" "$X/etc/tmpfiles.d/moveeye-spiel.conf" && ok "Spielen-Ordner für den Benutzer des Kiosks" || fehler "Spielen-Ordner"
[ -s "$X/var/lib/moveeye-hp-update/letzter_lauf" ] && [ "$(stat -c %a "$X/var/lib/moveeye-hp-update/letzter_lauf")" = 644 ] && ok "Stempel letzter_lauf (fürs Dauerrechnen lesbar)" || fehler "Stempel"
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
echo "8.0.0" > "$X/var/lib/moveeye-hp-update/version"; echo "8.0.0" > "$X/var/lib/moveeye-hp-update/sim_version"; echo 0 > "$X/var/lib/moveeye-hp-update/sim_sha256"
touch "$X/run/moveeye-test/kiosk_pause"
echo "# alt" > "$X/usr/local/lib/moveeye-kiosk/testbild.py"
lauf q; grep -q "Es läuft ein Test - verschoben" "$W/lauf.log" && [ "$(cat "$X/usr/local/lib/moveeye-kiosk/testbild.py")" = "# alt" ] \
	&& ok "Test läuft: verschoben, nichts geändert" || { fehler "trotz Pause eingespielt"; sed 's/^/    /' "$W/lauf.log"; }
rm -f "$X/run/moveeye-test/kiosk_pause"
lauf q; cmp -s "$X/usr/local/lib/moveeye-kiosk/testbild.py" "$R/simulator3d/beilagen_linux/testbild.py" && ok "nach dem Test eingespielt" || fehler "nach dem Test"

# 3.55.0: Zeitplan alle 15 Min. - nur in Pausen (kein Test, niemand spielt), höchstens alle 6 Std.; neue Fassung = nochmal
zp() { PATH="$B:$PATH" MOVEEYE_HP_QUELLE="file://$W/q" MOVEEYE_HP_UPTIME=99999 bash "$T" --zeitplan > "$W/lauf.log" 2>&1; }
alt6() { echo $(( $(date +%s) - 25200 )) > "$X/var/lib/moveeye-hp-update/letzter_lauf"; }
zp; [ ! -s "$W/lauf.log" ] && ok "--zeitplan: vor kurzem geprüft -> still fertig" || { fehler "--zeitplan prüft zu oft"; sed 's/^/    /' "$W/lauf.log"; }
alt6; mkdir -p "$X/run/moveeye-spiel"; echo '{"grund": "test"}' > "$X/run/moveeye-spiel/spielen"
echo "# alt" > "$X/usr/local/lib/moveeye-kiosk/testbild.py"; echo "8.0.0" > "$X/var/lib/moveeye-hp-update/version"; echo 0 > "$X/var/lib/moveeye-hp-update/sim_sha256"
zp; grep -q "Am HP wird gespielt - verschoben" "$W/lauf.log" && [ "$(cat "$X/usr/local/lib/moveeye-kiosk/testbild.py")" = "# alt" ] \
	&& ok "--zeitplan: es wird gespielt -> verschoben" || { fehler "beim Spielen eingespielt"; sed 's/^/    /' "$W/lauf.log"; }
rm -f "$X/run/moveeye-spiel/spielen" "$X/var/lib/moveeye-hp-update/verschoben"; touch "$X/run/moveeye-test/kiosk_pause"
zp; grep -q "Es läuft ein Test - verschoben" "$W/lauf.log" && ok "--zeitplan: der HP rechnet -> verschoben" || { fehler "beim Rechnen"; sed 's/^/    /' "$W/lauf.log"; }
zp; [ ! -s "$W/lauf.log" ] && ok "--zeitplan: «verschoben» höchstens einmal pro Stunde im Protokoll" || fehler "Protokoll zu gesprächig"
rm -f "$X/run/moveeye-test/kiosk_pause"
zp; grep -q "Fertig: MoveEye 9.0.0 · Sim 9.0.0 eingespielt" "$W/lauf.log" && cmp -s "$X/usr/local/lib/moveeye-kiosk/testbild.py" "$R/simulator3d/beilagen_linux/testbild.py" \
	&& ok "--zeitplan: in der Pause eingespielt" || { fehler "in der Pause nicht eingespielt"; sed 's/^/    /' "$W/lauf.log"; }
echo 1 > "$X/var/lib/moveeye-hp-update/fassung"; rm -f "$X/usr/local/lib/moveeye-kiosk/hp_wache.py"
lauf q; grep -q "neue Fassung" "$W/lauf.log" && [ -f "$X/usr/local/lib/moveeye-kiosk/hp_wache.py" ] \
	&& ok "gleiche Version, neue Fassung des Updates: spielt nach (hp_wache.py)" || { fehler "neue Fassung"; sed 's/^/    /' "$W/lauf.log"; }

# ---------------------------------------------------------------- 3. Drei Spuren: Simulator mit eigener Nummer (Block «sim»)
echo "--- 3. Drei Spuren (Block «sim» in versions.json, Test-Schlüssel)"
printf '#!/bin/sh\necho sim91\n' > "$W/sim91.x86_64"
bash "$R/werkzeuge/linux_paket.sh" "$W/sim91.x86_64" "$W/s/main/simulator3d/MoveEyeSim3D_Linux.zip" > /dev/null || fehler "linux_paket.sh (Sim 9.1.0)"
python3 - "$R/quelle/380_updates.py" "$W" <<'EOF'
import hashlib, json, os, shutil, sys
src, w = sys.argv[1:]
t = open(src, encoding="utf-8").read()
a = t.index("def _ed25519_impl"); b = t.index("return public, sign, verify", a) + len("return public, sign, verify")
ns = {"hashlib": hashlib}; exec(t[a:b], ns)
public, sign, verify = ns["_ed25519_impl"]()
seed = hashlib.sha256(b"nur ein Test-Schluessel").digest()
fl = "simulator3d/MoveEyeSim3D_Linux.zip"
mw = json.load(open(os.path.join(w, "q/main/versions.json")))["versions"][0]      # MoveEye 9.0.0 (signiert, Teil 2)
def sim(v, zp, kaputt=False):
    z = open(zp, "rb").read(); sh = hashlib.sha256(z).hexdigest()
    sig = sign(seed, ("MotionWatch|%s|%s|%s" % (v, fl, sh)).encode()).hex()
    if kaputt:
        sig = ("0" if sig[0] != "0" else "1") + sig[1:]
    return {"ver": v, "linux": {"ver": v, "file": fl, "size": len(z), "sha256": sh, "sig": sig}}
def quelle(name, versions, s, zip_von=None):
    os.makedirs(os.path.join(w, name, "main/simulator3d"), exist_ok=True)
    json.dump({"versions": versions, "sim": s}, open(os.path.join(w, name, "main/versions.json"), "w"))
    if zip_von and zip_von != name:
        shutil.copyfile(os.path.join(w, zip_von, "main", fl), os.path.join(w, name, "main", fl))
s91 = os.path.join(w, "s/main", fl)
quelle("s", [mw], sim("9.1.0", s91))                                  # Sim-Release allein: KEINE Programmdatei in der Quelle
quelle("skaputt", [mw], sim("9.1.0", s91, kaputt=True), "s")
quelle("salt", [mw], sim("9.0.5", s91), "s")
mw92 = dict(mw, version="9.2.0", file="webcam_bewegung_9_2_0.py")   # neue MoveEye, gleiche Sim (nur der Eintrag zählt hier)
mw92["sig"] = sign(seed, ("MotionWatch|9.2.0|webcam_bewegung_9_2_0.py|%s" % mw92["sha256"]).encode()).hex()
quelle("sgleich", [mw92, mw], sim("9.1.0", s91))                      # ohne ZIP: es darf nichts geladen werden
EOF
[ -f "$W/s/main/webcam_bewegung_9_0_0.py" ] && fehler "Testaufbau: Programmdatei in der Sim-Quelle"
: > "$W/aufrufe.txt"
lauf skaputt; grep -q "ABGELEHNT: Block «sim»: Signatur" "$W/lauf.log" && grep -q '^echo neu' "$SIMD/MoveEyeSim3D.x86_64" \
	&& ok "Block «sim» verfälscht: abgelehnt, kein Ausweichen auf die Programmdatei" || { fehler "verfälschter Block «sim»"; sed 's/^/    /' "$W/lauf.log"; }
lauf s; grep -q "Fertig: MoveEye 9.0.0 · Sim 9.1.0 eingespielt" "$W/lauf.log" && grep -q '^echo sim91' "$SIMD/MoveEyeSim3D.x86_64" \
	&& [ "$(cat "$X/var/lib/moveeye-hp-update/sim_version")" = 9.1.0 ] && [ "$(cat "$X/var/lib/moveeye-hp-update/version")" = 9.0.0 ] \
	&& ok "Sim-Release allein (ohne neue MoveEye, ohne Programmdatei): Sim 9.1.0 eingespielt" || { fehler "Sim-Release allein"; sed 's/^/    /' "$W/lauf.log"; }
grep -q "Signatur gültig: Sim 9.1.0" "$W/lauf.log" && ok "Sim-Nummer aus dem signierten Block «sim»" || fehler "Sim-Nummer"
lauf s; grep -q "Schon eingespielt" "$W/lauf.log" && ok "Sim 9.1.0 zweimal: nichts zu tun" || { fehler "Sim zweimal"; sed 's/^/    /' "$W/lauf.log"; }
lauf salt; grep -q "ABGELEHNT: Sim 9.0.5 ist älter als die eingespielte Sim 9.1.0" "$W/lauf.log" && ok "ältere Sim abgelehnt" || { fehler "Sim-Rückschritt"; sed 's/^/    /' "$W/lauf.log"; }
lauf q; grep -qE "ABGELEHNT: Sim 9.0.0 ist älter|Schon eingespielt" "$W/lauf.log" && grep -q '^echo sim91' "$SIMD/MoveEyeSim3D.x86_64" \
	&& ok "alte Liste ohne «sim» (Programmdatei mit Sim 9.0.0): Simulator bleibt 9.1.0" || { fehler "Rückschritt über die Programmdatei"; sed 's/^/    /' "$W/lauf.log"; }
echo 1 > "$X/var/lib/moveeye-hp-update/fassung"
lauf q; grep -q "ABGELEHNT: Sim 9.0.0 ist älter als die eingespielte Sim 9.1.0" "$W/lauf.log" && grep -q '^echo sim91' "$SIMD/MoveEyeSim3D.x86_64" \
	&& ok "alte Liste, neue Fassung: Sim 9.0.0 aus der Programmdatei abgelehnt" || { fehler "Rückschritt (neue Fassung)"; sed 's/^/    /' "$W/lauf.log"; }
sed -n 's/^HP_FASSUNG=\([0-9]*\).*/\1/p' "$U" > "$X/var/lib/moveeye-hp-update/fassung"
lauf sgleich; grep -q "Neue MoveEye 9.2.0, der Simulator bleibt Sim 9.1.0" "$W/lauf.log" && [ "$(cat "$X/var/lib/moveeye-hp-update/version")" = 9.2.0 ] \
	&& ok "neue MoveEye, gleiche Sim: nichts geladen, MoveEye-Nummer gemerkt" || { fehler "neue MoveEye, gleiche Sim"; sed 's/^/    /' "$W/lauf.log"; }
MOVEEYE_HP_QUELLE="file://$W/s" bash "$T" --pruefen > "$W/lauf.log" 2>&1 && grep -q "aus: versions.json «sim»" "$W/lauf.log" \
	&& ok "--pruefen: Linux-Paket aus dem Block «sim»" || { fehler "--pruefen mit «sim»"; sed 's/^/    /' "$W/lauf.log"; }
python3 -c 'import sys; f=open(sys.argv[1], "r+b"); f.seek(-100, 2); b=f.read(1); f.seek(-100, 2); f.write(bytes([b[0] ^ 255]))' "$W/salt/main/simulator3d/MoveEyeSim3D_Linux.zip"
python3 - "$W/salt/main/versions.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1])); d["sim"] = json.load(open(sys.argv[1].replace("salt", "s")))["sim"]; json.dump(d, open(sys.argv[1], "w"))
EOF
MOVEEYE_HP_QUELLE="file://$W/salt" bash "$T" --pruefen > "$W/lauf.log" 2>&1; grep -q "ABGELEHNT: kein Linux-Paket mit der signierten Prüfsumme" "$W/lauf.log" \
	&& ok "Sim-ZIP verändert (1 Byte): abgelehnt" || { fehler "verändertes Sim-ZIP"; sed 's/^/    /' "$W/lauf.log"; }

echo
if [ $F -eq 0 ]; then echo "HP-Update-Test: OK"; else echo "HP-Update-Test: $F Fehler"; fi
exit $F
