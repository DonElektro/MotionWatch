#!/usr/bin/env bash
# MoveEye auf einem frischen Raspberry Pi einrichten (Raspberry Pi OS Bookworm, Pi 5) - 2.98.18.
#
#   bash einrichten.sh              # fragt bei Tailscale und vor dem Neustart
#   bash einrichten.sh --trocken    # zeigt nur, was es tun würde (ändert nichts)
#   bash einrichten.sh --ja         # ohne Rückfragen (Tailscale nein, kein Neustart)
#   bash einrichten.sh --tailscale  # Tailscale ohne Rückfrage dazu
#   bash einrichten.sh --ordner ~/MoveEye --datei webcam_bewegung_X_Y_Z.py
#
# Als normaler Benutzer starten (nicht mit sudo): für die Schritte, die es braucht, fragt sudo selbst nach dem Passwort.
# Mehrmals laufen lassen schadet nicht: was schon da ist, wird übersprungen. Es wird nichts gelöscht; die config.txt wird
# vor einer Änderung gesichert (config.txt.vor-moveeye-DATUM). Neu gestartet wird nur nach Rückfrage.
set -u

TROCKEN=0; JA=0; TAILSCALE=""; ORDNER=""; DATEI=""
REPO_RAW="https://raw.githubusercontent.com/DonElektro/MotionWatch/main"
SSD_TGZ_URL="https://storage.googleapis.com/download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz"
SSD_PBTXT_URL="https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"
# sha256 des SSD-Archivs. Leer = noch nicht eingetragen: dann prüft OpenCV, ob sich das Modell laden lässt, und die Prüfsumme
# wird angezeigt (der GitHub-Lauf «Prüfsatz» zeigt sie auch). Das eigene MoveEye-Modell hat seine sha256 im Manifest.
SSD_TGZ_SHA256="${SSD_TGZ_SHA256:-}"
OWN_JSON_URL="https://github.com/DonElektro/MotionWatch/releases/download/ki-modell/moveeye_model.json"

while [ $# -gt 0 ]; do
  case "$1" in
    --trocken|--dry-run) TROCKEN=1 ;;
    --ja|--yes) JA=1 ;;
    --tailscale) TAILSCALE=ja ;;
    --ohne-tailscale) TAILSCALE=nein ;;
    --ordner) shift; ORDNER="${1:-}" ;;
    --datei) shift; DATEI="${1:-}" ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "Unbekannte Option: $1 (--help)"; exit 2 ;;
  esac
  shift
done

if [ "$(id -u)" -eq 0 ]; then
  if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != root ]; then
    echo "Bitte ohne sudo starten:  bash $0   (sudo wird für die nötigen Schritte selbst gefragt)"; exit 2
  fi
  echo "Bitte als normaler Benutzer starten (z. B. pi), nicht als root."; exit 2
fi
BENUTZER="$(id -un)"
HEIM="$HOME"
ORDNER="${ORDNER:-$HEIM/MoveEye}"
DATEN="${MOTIONWATCH_HOME:-$HEIM/.config/motionwatch}"
HIER="$(cd "$(dirname "$0")" && pwd)"
ERG=()          # result lines
NEUSTART=0

ok()   { local s="$*"; [ "$TROCKEN" -eq 1 ] && s="$s (Trockenlauf)"; ERG+=("✓ $s"); echo "✓ $s"; }
warn() { ERG+=("! $*"); echo "! $*"; }
info() { echo "· $*"; }
# run a command - or only show it (--trocken)
tu() {
  if [ "$TROCKEN" -eq 1 ]; then echo "  [trocken] $*"; return 0; fi
  "$@"
}
frage() {      # frage "Text" -> 0 = ja
  [ "$JA" -eq 1 ] && return 1
  [ "$TROCKEN" -eq 1 ] && { echo "  [trocken] Frage: $1 → nein"; return 1; }
  local a; read -r -p "$1 [j/N] " a || return 1
  case "$a" in j|J|ja|Ja|y|Y|yes) return 0 ;; *) return 1 ;; esac
}
sha() { sha256sum "$1" | cut -d' ' -f1; }

echo "MoveEye einrichten für Benutzer $BENUTZER – Programmordner $ORDNER, Einstellungen $DATEN"
[ "$TROCKEN" -eq 1 ] && echo "(Trockenlauf: es wird nichts geändert)"

# ---- 0. what kind of computer ----------------------------------------------------------------------------------------
MODELL="$(tr -d '\0' 2>/dev/null < /proc/device-tree/model || true)"
CODENAME="$(. /etc/os-release 2>/dev/null; echo "${VERSION_CODENAME:-?}")"
info "Rechner: ${MODELL:-unbekannt}, System: $CODENAME"
case "$MODELL" in *"Raspberry Pi 5"*) ;; *) warn "kein Raspberry Pi 5 erkannt – die Hardware-Schritte passen eventuell nicht" ;; esac
[ "$CODENAME" = bookworm ] || warn "nicht Raspberry Pi OS Bookworm ($CODENAME) – Paketnamen können abweichen"
command -v sudo >/dev/null || { echo "sudo fehlt"; exit 1; }

# ---- 1. packages (from the system: Bookworm does not allow pip outside a venv) ------------------------------------------
PAKETE=(python3 python3-numpy python3-opencv python3-pil python3-pil.imagetk python3-tk python3-flask python3-psutil
        python3-cryptography python3-gpiozero python3-picamera2 python3-smbus python3-spidev i2c-tools ffmpeg alsa-utils
        openssl bluez pulseaudio-utils curl ca-certificates)
FEHLT=()
for p in "${PAKETE[@]}"; do dpkg -s "$p" >/dev/null 2>&1 || FEHLT+=("$p"); done
if [ ${#FEHLT[@]} -eq 0 ]; then
  ok "Pakete: alle schon da"
else
  info "Pakete installieren: ${FEHLT[*]}"
  tu sudo apt-get update -q
  if tu sudo apt-get install -y -q "${FEHLT[@]}"; then
    ok "Pakete installiert (${#FEHLT[@]})"
  else
    NICHT=()
    for p in "${FEHLT[@]}"; do tu sudo apt-get install -y -q "$p" >/dev/null 2>&1 || NICHT+=("$p"); done
    if [ ${#NICHT[@]} -eq 0 ]; then ok "Pakete installiert"; else warn "Pakete nicht installiert: ${NICHT[*]}"; fi
  fi
fi

# ---- 2. I2C, SPI, camera -----------------------------------------------------------------------------------------------
CONF="${MW_CONFIG_TXT:-/boot/firmware/config.txt}"; [ -f "$CONF" ] || CONF=/boot/config.txt      # MW_CONFIG_TXT: only for tests
if command -v raspi-config >/dev/null; then
  for x in i2c spi; do
    if [ "$TROCKEN" -eq 1 ]; then
      echo "  [trocken] sudo raspi-config nonint do_$x 0   (falls noch aus)"
    elif [ "$(sudo raspi-config nonint "get_$x" 2>/dev/null)" = 0 ]; then
      info "${x^^} ist schon eingeschaltet"
    else
      tu sudo raspi-config nonint "do_$x" 0 && NEUSTART=1
    fi
  done
  ok "I2C und SPI eingeschaltet"
else
  warn "raspi-config fehlt – I2C / SPI bitte von Hand einschalten (docs/Einrichtung_Raspberry_Pi.md)"
fi
if [ -f "$CONF" ]; then
  # Thermal-90: SPI with one chip select (GPIO 7), camera auto detection - at the end under [all]
  ZEILEN=()
  for z in "dtparam=spi=on" "dtparam=i2c_arm=on" "dtoverlay=spi0-0cs" "camera_auto_detect=1"; do
    grep -qE "^[[:space:]]*${z//./\\.}[[:space:]]*$" "$CONF" || ZEILEN+=("$z")
  done
  if [ ${#ZEILEN[@]} -gt 0 ]; then
    SICH="$CONF.vor-moveeye-$(date +%Y%m%d-%H%M%S)"
    info "$CONF: ${ZEILEN[*]} dazu (Sicherung: $SICH)"
    tu sudo cp -p "$CONF" "$SICH"
    if [ "$TROCKEN" -eq 0 ]; then
      { echo ""; echo "# MoveEye (einrichten.sh): Wärmebild Thermal-90 (SPI, I2C), Kamera"; echo "[all]"; printf '%s\n' "${ZEILEN[@]}"; } | sudo tee -a "$CONF" >/dev/null
    else
      echo "  [trocken] an $CONF anhängen: [all] ${ZEILEN[*]}"
    fi
    NEUSTART=1
    ok "config.txt ergänzt"
  else
    ok "config.txt: SPI, I2C, Kamera schon eingetragen"
  fi
else
  warn "config.txt nicht gefunden"
fi
if command -v rpicam-hello >/dev/null && [ "$TROCKEN" -eq 0 ]; then
  if timeout 20 rpicam-hello --list-cameras 2>/dev/null | grep -q "^[0-9] :"; then ok "Kamera gefunden"; else warn "keine Kamera gefunden (Kabel? nach dem Neustart nochmals prüfen)"; fi
fi

# ---- 3. the program --------------------------------------------------------------------------------------------------
tu mkdir -p "$ORDNER" "$DATEN/models"
if [ -z "$DATEI" ]; then        # newest file next to this script (repository) - otherwise from GitHub
  DATEI="$(ls "$HIER"/../webcam_bewegung_*.py 2>/dev/null | sort -V | tail -1)"
fi
if [ -n "$DATEI" ] && [ -f "$DATEI" ]; then
  ZIEL="$ORDNER/$(basename "$DATEI")"
  if [ -f "$ZIEL" ] && cmp -s "$DATEI" "$ZIEL"; then info "$(basename "$DATEI") ist schon im Programmordner"; else tu cp "$DATEI" "$ZIEL"; fi
  [ -f "$HIER/../versions.json" ] && tu cp "$HIER/../versions.json" "$ORDNER/versions.json"
  ok "MoveEye $(basename "$DATEI") im Ordner $ORDNER"
else
  info "neuste Version von GitHub holen"
  if tu curl -fsSL -o "$ORDNER/versions.json.neu" "$REPO_RAW/versions.json"; then
    if [ "$TROCKEN" -eq 1 ]; then
      ZIEL="$ORDNER/webcam_bewegung_X_Y_Z.py"
    else
      read -r FNAME FSHA < <(python3 -c 'import json,sys; e=json.load(open(sys.argv[1]))["versions"][0]; print(e["file"], e["sha256"])' "$ORDNER/versions.json.neu")
      ZIEL="$ORDNER/$FNAME"
      if [ ! -f "$ZIEL" ] || [ "$(sha "$ZIEL")" != "$FSHA" ]; then
        curl -fsSL -o "$ZIEL.neu" "$REPO_RAW/$FNAME" || { echo "Herunterladen fehlgeschlagen"; exit 1; }
        if [ "$(sha "$ZIEL.neu")" != "$FSHA" ]; then rm -f "$ZIEL.neu"; echo "Prüfsumme falsch – abgebrochen"; exit 1; fi
        mv "$ZIEL.neu" "$ZIEL"
      fi
      mv "$ORDNER/versions.json.neu" "$ORDNER/versions.json"
    fi
    ok "MoveEye $(basename "$ZIEL") von GitHub (sha256 geprüft)"
  else
    echo "Keine Verbindung zu GitHub und keine Datei angegeben (--datei)"; exit 1
  fi
fi

# ---- 4. permissions (Wi-Fi, clock, autostart, watchdog) and the service -------------------------------------------------
tu sudo python3 "$ZIEL" --allow-wifi >/dev/null && ok "Berechtigungen (WLAN, Uhr, Ausschalten, Watchdog)"
if [ "$TROCKEN" -eq 0 ] && XDG_RUNTIME_DIR="/run/user/$(id -u)" systemctl --user is-enabled motionwatch >/dev/null 2>&1; then
  ok "Autostart: schon eingeschaltet (Benutzer-Dienst aus MoveEye) – kein zweiter Dienst"
elif [ "$TROCKEN" -eq 0 ] && [ -f /etc/systemd/system/motionwatch.service ] && grep -qF "$ZIEL" /etc/systemd/system/motionwatch.service; then
  tu sudo systemctl enable --now motionwatch.service >/dev/null 2>&1
  ok "Autostart: Dienst motionwatch läuft schon mit dieser Version"
else
  tu sudo python3 "$ZIEL" --install-service >/dev/null && ok "Autostart: Dienst motionwatch eingerichtet (systemctl status motionwatch)"
fi

# ---- 5. Tailscale (remote access, optional) ------------------------------------------------------------------------
if command -v tailscale >/dev/null; then
  ok "Tailscale ist installiert ($(tailscale ip -4 2>/dev/null | head -1 || echo 'noch nicht angemeldet'))"
else
  if [ "$TAILSCALE" = ja ] || { [ -z "$TAILSCALE" ] && frage "Tailscale (Fernzugriff übers Internet) installieren?"; }; then
    if [ "$TROCKEN" -eq 1 ]; then echo "  [trocken] curl -fsSL https://tailscale.com/install.sh | sh; sudo tailscale up"
    else
      curl -fsSL https://tailscale.com/install.sh -o /tmp/tailscale_install.sh && sh /tmp/tailscale_install.sh && rm -f /tmp/tailscale_install.sh
      sudo tailscale up && ok "Tailscale eingerichtet: $(tailscale ip -4 2>/dev/null | head -1)" || warn "Tailscale: Anmeldung nicht fertig (später: sudo tailscale up)"
    fi
  else
    info "Tailscale ausgelassen (später: bash $0 --tailscale)"
  fi
fi

# ---- 6. the AI model ---------------------------------------------------------------------------------------------------
PB="$DATEN/models/frozen_inference_graph.pb"; PBTXT="$DATEN/models/ssd_mobilenet_v2_coco.pbtxt"
if [ -s "$PB" ] && [ -s "$PBTXT" ]; then
  ok "KI-Modell (SSD) ist schon da"
elif [ "$TROCKEN" -eq 1 ]; then
  echo "  [trocken] KI-Modell SSD laden (ca. 70 MB) nach $DATEN/models, Prüfsumme prüfen"
else
  T="$(mktemp -d)"
  if curl -fsSL -o "$T/m.tgz" "$SSD_TGZ_URL" && curl -fsSL -o "$T/x.pbtxt" "$SSD_PBTXT_URL"; then
    S="$(sha "$T/m.tgz")"
    if [ -n "$SSD_TGZ_SHA256" ] && [ "$S" != "$SSD_TGZ_SHA256" ]; then
      warn "KI-Modell: Prüfsumme falsch ($S) – nicht übernommen"
    else
      tar -xzf "$T/m.tgz" -C "$T" --wildcards "*/frozen_inference_graph.pb" 2>/dev/null
      F="$(find "$T" -name frozen_inference_graph.pb | head -1)"
      if [ -n "$F" ] && python3 -c 'import cv2,sys; cv2.dnn.readNetFromTensorflow(sys.argv[1], sys.argv[2])' "$F" "$T/x.pbtxt" 2>/dev/null; then
        mv "$F" "$PB.neu" && mv "$PB.neu" "$PB"; mv "$T/x.pbtxt" "$PBTXT"
        if [ -n "$SSD_TGZ_SHA256" ]; then ok "KI-Modell (SSD) geladen, sha256 stimmt"
        else ok "KI-Modell (SSD) geladen, von OpenCV geprüft (sha256 $S)"; fi
      else
        warn "KI-Modell: Datei beschädigt oder OpenCV kann sie nicht lesen"
      fi
    fi
  else
    warn "KI-Modell nicht geladen (Internet?) – später in MoveEye: «KI-Modell herunterladen»"
  fi
  rm -rf "$T"
fi
OJ="$DATEN/models/moveeye_model.json"; OO="$DATEN/models/moveeye_model.onnx"
if [ -s "$OJ" ] && [ -s "$OO" ]; then
  ok "Eigenes MoveEye-Modell ist schon da"
elif [ "$TROCKEN" -eq 0 ]; then
  T="$(mktemp -d)"
  if curl -fsSL -o "$T/m.json" "$OWN_JSON_URL" 2>/dev/null; then
    read -r OF OS < <(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print(m["file"], m["sha256"])' "$T/m.json" 2>/dev/null || echo "- -")
    if [ "$OF" != "-" ] && curl -fsSL -o "$T/m.onnx" "${OWN_JSON_URL%/*}/$OF" && [ "$(sha "$T/m.onnx")" = "$OS" ]; then
      mv "$T/m.onnx" "$OO"; mv "$T/m.json" "$OJ"; ok "Eigenes MoveEye-Modell geladen (sha256 stimmt) – einschalten: Einstellungen → KI-Erkennung"
    else
      warn "Eigenes MoveEye-Modell: Herunterladen oder Prüfsumme fehlgeschlagen – nicht übernommen"
    fi
  else
    info "Eigenes MoveEye-Modell: noch keins veröffentlicht"
  fi
  rm -rf "$T"
fi

# ---- 7. self-test and the result ---------------------------------------------------------------------------------------
if [ "$TROCKEN" -eq 0 ]; then
  ST="$(cd "$ORDNER" && python3 "$ZIEL" --self-test . 2>&1 | tail -1)"
  case "$ST" in *"Self-test OK"*) ok "Selbsttest bestanden" ;; *) warn "Selbsttest: $ST (Einzelheiten: python3 $ZIEL --self-test $ORDNER)" ;; esac
else
  echo "  [trocken] python3 $ZIEL --self-test $ORDNER"
fi
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo ""
echo "================ MoveEye – Ergebnis ================"
printf '%s\n' "${ERG[@]}"
echo ""
echo "Webseite: http://${IP:-<IP-des-Pi>}:5000/   (beim ersten Öffnen ein Web-Passwort festlegen – die Seite fragt danach)"
echo "Anleitung: docs/Einrichtung_Raspberry_Pi.md"
if [ "$NEUSTART" -eq 1 ]; then
  echo "Für I2C / SPI / Kamera ist ein Neustart nötig."
  if frage "Jetzt neu starten?"; then tu sudo reboot; else echo "Später neu starten: sudo reboot"; fi
fi
