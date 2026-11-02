#!/bin/bash
# MoveEye USB-Installer - Prüfungen ohne echten PC (CI-Job «USB-Installer»; lokal geht es auch, mit docker).
#   pruefen.sh statisch       shellcheck; user-data für 24.04 und 26.04 bauen (Ventoy-Modus, Test-Passwort, nichts wird
#                             geschrieben ausser in einen Temp-Ordner); YAML gegen das autoinstall-Schema von subiquity;
#                             eingebettete Skripte = Dateien hier
#   pruefen.sh pakete BILD    alle Pakete der user-data in BILD (z. B. ubuntu:26.04) installierbar? (apt-get -s)
#   pruefen.sh retten BILD    Trockenlauf «erststart.sh --retten» in BILD: nur cdrom-Quelle (wie nach dem Abbruch),
#                             Ersatz-Benutzer und Ersatz-Zip; prüft Quellen, Pakete, Rechte beim Entpacken, Kiosk-Aufruf
# shellcheck disable=SC2016  # Befehle in '…' laufen erst im Container bzw. in den Ersatz-Skripten
set -euo pipefail
HIER="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
SCHEMA_URL="${SCHEMA_URL:-https://raw.githubusercontent.com/canonical/subiquity/main/autoinstall-schema.json}"
W="$(mktemp -d)"
trap 'rm -rf "$W"' EXIT
pakete_liste() { sed -n '/^PAKETE=(/,/)/p' "$HIER/erststart.sh" | tr -d '()' | sed 's/^PAKETE=//' | xargs; }

statisch() {
	echo "--- shellcheck"
	shellcheck -x "$HIER"/*.sh
	echo "--- autoinstall-Schema laden"
	curl -fsSL -o "$W/schema.json" "$SCHEMA_URL"
	local v iso out
	for v in 24.04.3 26.04.1; do
		echo "--- user-data für $v"
		iso="$W/ubuntu-$v-live-server-amd64.iso"
		: > "$iso"
		out="$(printf 'ch\nCi-Testpasswort-1\nCi-Testpasswort-1\n\n' | HOME="$W" bash "$HIER/stick_erstellen.sh" "$iso" --nur-dateien "$W/$v")"
		echo "$out"
		if grep -q WARNUNG <<<"$out"; then echo "FEHLER: Warnung für $v"; exit 1; fi
		python3 - "$W/$v/moveeye/user-data" "$W/schema.json" "$HIER" <<'EOF'
import base64, json, pathlib, re, sys
import jsonschema, yaml
ud, schema, hier = sys.argv[1:]
text = pathlib.Path(ud).read_text()
assert not re.search(r"@@[A-Z_]+@@", text), "Platzhalter übrig"
a = yaml.safe_load(text)["autoinstall"]
jsonschema.validate(a, json.loads(pathlib.Path(schema).read_text()))
print("Schema: OK")
eingebettet = {}
for c in a["early-commands"] + a["late-commands"]:
    m = re.fullmatch(r"echo '([A-Za-z0-9+/=]+)' \| base64 -d > (\S+)", c)
    if m:
        eingebettet[m.group(2)] = base64.b64decode(m.group(1))
for ziel, datei in (("/tmp/moveeye-netz.sh", "netzpruefung.sh"), ("/target/usr/local/sbin/moveeye-erststart", "erststart.sh")):
    assert eingebettet.get(ziel) == pathlib.Path(hier, datei).read_bytes(), f"{datei} nicht (richtig) eingebettet"
    print(f"eingebettet: {datei} -> {ziel}")
assert a["early-commands"][-1] == "bash /tmp/moveeye-netz.sh", "Netzprüfung nicht in early-commands"
assert a["apt"]["fallback"] == "abort" and a["apt"]["geoip"] is True, "apt: fallback/geoip"
assert a["identity"]["password"].startswith("$6$"), "Passwort-Hash"
print("Pakete:", " ".join(a["packages"]))
EOF
	done
	echo "statisch: OK"
}

pakete() {
	local bild="$1"
	echo "--- Pakete in $bild: $(pakete_liste)"
	docker run --rm -e PK="$(pakete_liste)" "$bild" bash -euc '
		grep -E "^(VERSION|VERSION_CODENAME)=" /etc/os-release
		apt-get update -q >/dev/null
		for p in $PK; do printf "%-22s %s\n" "$p" "$(apt-cache policy "$p" | sed -n "s/^ *Candidate: //p")"; done
		DEBIAN_FRONTEND=noninteractive apt-get install -s -q $PK > /tmp/s.txt
		echo "apt-get -s: $(grep -c "^Inst" /tmp/s.txt) Pakete würden installiert - OK"'
}

retten() {
	local bild="$1"
	# Ersatz-Zip wie MoveEyeSim3D_Linux.zip: die Skripte schreiben nur auf, wer sie wie aufruft
	mkdir -p "$W/zip/MoveEyeSim3D"
	printf '#!/bin/sh\necho ersatz\n' > "$W/zip/MoveEyeSim3D/MoveEyeSim3D.x86_64"
	printf '#!/bin/bash\nid -un > "$HOME/installieren.txt"\n' > "$W/zip/MoveEyeSim3D/installieren.sh"
	printf '#!/bin/bash\necho "$(id -un) SUDO_USER=$SUDO_USER $*" > /tmp/kiosk.txt\n' > "$W/zip/MoveEyeSim3D/kiosk_ein.sh"
	mkdir -p "$W/zip/MoveEyeSim3D/hp"
	printf '#!/bin/bash\necho "$(id -un) $*" > /tmp/hpupdate.txt\n' > "$W/zip/MoveEyeSim3D/hp/hp_update.sh"
	(cd "$W/zip" && python3 -c 'import shutil; shutil.make_archive("sim", "zip", ".", "MoveEyeSim3D")')
	cp "$HIER/erststart.sh" "$W/"
	cat > "$W/innen.sh" <<'EOF'
#!/bin/bash
set -eu
apt-get update -q >/dev/null
DEBIAN_FRONTEND=noninteractive apt-get install -y -q curl >/dev/null   # auf dem halben System schon da
# Zustand nach dem Abbruch: nur die cdrom-Quelle
mkdir -p /root/quellen-weg && mv /etc/apt/sources.list.d/* /root/quellen-weg/ 2>/dev/null || true
echo 'deb [check-date=no] file:///cdrom '"$(. /etc/os-release; echo "$VERSION_CODENAME")"' main restricted' > /etc/apt/sources.list
rm -rf /var/lib/apt/lists/*
useradd -m -s /bin/bash simtest
# kein systemd im Container: systemctl und ufw nur aufzeichnen
mkdir -p /ersatz /etc/systemd/system
for b in systemctl ufw; do printf '#!/bin/sh\necho "%s $*" >> /tmp/aufrufe.txt\n' "$b" > /ersatz/$b; chmod 755 /ersatz/$b; done
cp /t/erststart.sh /tmp/erststart.sh
PATH="/ersatz:$PATH" MOVEEYE_BENUTZER=simtest MOVEEYE_URL=file:///t/zip/sim.zip bash /tmp/erststart.sh --retten
echo "--- Ergebnis"
cat /etc/apt/sources.list; ls /etc/apt/sources.list.d/; cat /tmp/kiosk.txt; cat /tmp/aufrufe.txt
f=0
grep -q '^# moveeye: cdrom aus' /etc/apt/sources.list || { echo "FEHLER: cdrom-Quelle aktiv"; f=1; }
grep -q 'archive.ubuntu.com' /etc/apt/sources.list.d/ubuntu.sources || { echo "FEHLER: keine Online-Quelle"; f=1; }
for p in $(sed -n '/^PAKETE=(/,/)/p' /t/erststart.sh | tr -d '()' | sed 's/^PAKETE=//'); do
	dpkg-query -W -f='${Status}' "$p" | grep -q 'install ok installed' || { echo "FEHLER: Paket $p fehlt"; f=1; }
done
[ "$(stat -c %U /home/simtest/MoveEyeSim3D/kiosk_ein.sh)" = simtest ] || { echo "FEHLER: Entpackt nicht als simtest"; f=1; }
[ -x /home/simtest/MoveEyeSim3D/MoveEyeSim3D.x86_64 ] || { echo "FEHLER: nicht ausführbar"; f=1; }
[ "$(cat /home/simtest/installieren.txt)" = simtest ] || { echo "FEHLER: installieren.sh nicht als simtest"; f=1; }
[ "$(cat /tmp/kiosk.txt)" = "root SUDO_USER=simtest --ja" ] || { echo "FEHLER: kiosk_ein.sh falsch aufgerufen"; f=1; }
[ "$(cat /tmp/hpupdate.txt 2>/dev/null)" = "root --einrichten --ohne-lauf" ] || { echo "FEHLER: moveeye-hp-update nicht eingerichtet"; f=1; }
[ -s /var/lib/moveeye/erststart_fertig ] || { echo "FEHLER: Fertig-Marke fehlt"; f=1; }
[ -x /usr/local/sbin/moveeye-erststart ] || { echo "FEHLER: nicht installiert"; f=1; }
grep -q 'ExecStart=/usr/local/sbin/moveeye-erststart' /etc/systemd/system/moveeye-erststart.service || { echo "FEHLER: Dienst"; f=1; }
grep -q 'systemctl reboot' /tmp/aufrufe.txt || { echo "FEHLER: kein Neustart"; f=1; }
grep -q 'ufw --force enable' /tmp/aufrufe.txt || { echo "FEHLER: Firewall"; f=1; }
ls /tmp/moveeye_sim_*.zip 2>/dev/null && { echo "FEHLER: Zip bleibt liegen"; f=1; }
[ $f -eq 0 ] && echo "retten: OK"
exit $f
EOF
	echo "--- Trockenlauf erststart --retten in $bild"
	docker run --rm -v "$W":/t:ro "$bild" bash /t/innen.sh
}

case "${1:-}" in
	statisch) statisch ;;
	pakete) pakete "${2:?BILD fehlt, z. B. ubuntu:26.04}" ;;
	retten) retten "${2:?BILD fehlt, z. B. ubuntu:26.04}" ;;
	*) sed -n '2,8p' "$0"; exit 2 ;;
esac
