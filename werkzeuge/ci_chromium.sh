#!/bin/bash
# CI (Jobs «MoveEye · Web · <Gruppe>», .github/workflows/ci.yml): Chromium für Playwright und seine Systempakete - ohne dass
# ein hängender apt-Spiegel den Job aufhält (22.11.2026: «Chromium: Versuch 1 ging nicht» in vielen Läufen).
#   bash werkzeuge/ci_chromium.sh DEB_ORDNER
# 1. Chromium selbst: aus dem Zwischenspeicher ~/.cache/ms-playwright (ci.yml) oder geladen (kein apt).
# 2. Systempakete: nur die, die «playwright install-deps» bräuchte UND die hier fehlen. Ihre .deb-Dateien bleiben in
#    DEB_ORDNER (Zwischenspeicher von ci.yml, Schlüssel = Abbild des Runners + Playwright-Version): beim nächsten Lauf
#    «dpkg -i» ohne Netz und ohne «apt-get update». Fehlt nichts, läuft gar kein apt.
# 3. Geht das nicht: wie bisher apt mit Wiederholen (Zeitgrenzen aus /etc/apt/apt.conf.d/80-mw-robust).
# Am Schluss muss Chromium starten, sonst Exit 1.
set -u
D="${1:?Ordner für die .deb-Dateien}"
mkdir -p "$D/partial"
export DEBIAN_FRONTEND=noninteractive
starten() { timeout 90 python3 -c "from playwright.sync_api import sync_playwright as s; p = s().start(); b = p.chromium.launch(); b.close(); p.stop()"; }

# 1. Chromium (nur Herunterladen, ohne --with-deps)
for i in 1 2 3; do
	timeout 300 python3 -m playwright install chromium && break
	echo "::warning::Chromium laden: Versuch $i ging nicht - nochmal"; sleep 5
done

# 2. welche Systempakete braucht Chromium? (Playwright 1.55 druckt den apt-Befehl, neuere nur die fehlenden)
liste=$(timeout 60 python3 -m playwright install-deps --dry-run chromium 2>/dev/null \
	| grep -oE -- '--no-install-recommends[^"&;]*' | head -n 1 | sed 's/--no-install-recommends//')
fehlt() {
	local p f=""
	for p in $liste; do
		[[ "$p" =~ ^[a-z0-9][a-z0-9.+:-]{1,80}$ ]] || continue
		dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q 'install ok installed' || f="$f $p"
	done
	printf '%s' "$f"
}
f="$(fehlt)"
echo "Chromium braucht $(wc -w <<< "$liste") Systempakete, davon fehlen $(wc -w <<< "$f")${f:+:$f}"
if [ -n "$f" ] && compgen -G "$D/*.deb" > /dev/null; then
	echo "aus dem Zwischenspeicher: $(find "$D" -maxdepth 1 -name '*.deb' | wc -l) .deb-Dateien (ohne Netz)"
	sudo timeout 300 dpkg -i --skip-same-version "$D"/*.deb 2>&1 | tail -n 3 || echo "::warning::dpkg -i aus dem Zwischenspeicher meldet Fehler - apt"
	f="$(fehlt)"
fi
if [ -n "$f" ]; then
	for i in 1 2 3; do
		# shellcheck disable=SC2086  # f: Paketnamen, oben geprüft
		sudo timeout 360 sh -c "apt-get update -qq && apt-get install -y -q -f --no-install-recommends \
			-o Dir::Cache::archives='$D' -o APT::Keep-Downloaded-Packages=true $f" > /dev/null && break
		echo "::warning::Chromium-Pakete: Versuch $i ging nicht - nochmal"
	done
	f="$(fehlt)"
	[ -z "$f" ] || echo "::warning::noch fehlende Pakete:$f"
fi
sudo rm -rf "$D/partial" "$D/lock" 2> /dev/null
sudo chmod -R a+rX "$D" 2> /dev/null
if ! starten; then
	echo "::warning::Chromium startet nicht - wie bisher «playwright install --with-deps»"
	timeout 600 python3 -m playwright install --with-deps chromium || true
	starten || { echo "::error::Chromium startet nicht"; exit 1; }
fi
echo "Chromium startet"
