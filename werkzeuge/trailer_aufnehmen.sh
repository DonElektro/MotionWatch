#!/usr/bin/env bash
# Trailer der Geschichten als Videodatei (MP4, H.264) aufnehmen – Daniel 31.10.2026, Simulator: scripts/trailer.gd.
#
#   bash werkzeuge/trailer_aufnehmen.sh                       # beide Trailer, Deutsch, 1080p, 25 fps
#   bash werkzeuge/trailer_aufnehmen.sh --id maggie --sprache fr --hoehe 720
#   bash werkzeuge/trailer_aufnehmen.sh --sprache alle        # de fr it rm en nacheinander (dauert lange)
#   bash werkzeuge/trailer_aufnehmen.sh --id grossvater --ab 0 --bis 25 --hoehe 720   # kurze Probe
#
# Optionen: --id grossvater|maggie|beide · --sprache de|fr|it|rm|en|alle · --hoehe 1080|720 · --fps 25 ·
#           --ab S / --bis S (nur ein Stück) · --untertitel auto|an|aus · --grafik normal|lite|hoch ·
#           --ziel ORDNER (Standard: ./trailer_videos) · --godot PFAD (Standard: $GODOT oder «godot» im PATH)
#
# Ablauf je Trailer und Sprache:
#   1. Simulator mit dem Godot Movie Maker (--write-movie, feste fps: rendert unabhängig vom Tempo des PCs, Ton inklusive)
#      in einem frischen Benutzerordner (HOME), ohne Fenster nötig (startet selbst ein Xvfb, falls kein DISPLAY da ist).
#      Der Trailer schreibt die Zeiten der Erzählersätze in cues.json.
#   2. Erzähler: espeak-ng (falls installiert und die Sprache eine Stimme hat) spricht jeden Satz; ffmpeg legt ihn zur
#      richtigen Zeit auf die Tonspur. Ohne Stimme (z. B. Romanisch) brennt der Simulator Untertitel ins Bild.
#   3. ffmpeg: H.264 (-preset veryfast, CRF 20, yuv420p) + AAC, Lautheit auf -16 LUFS (loudnorm); der Vorlauf vor dem
#      Trailer wird abgeschnitten.
# Es werden keine Zugangsdaten, Themen oder Schlüssel gebraucht oder gespeichert.
set -u

HIER="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HIER/.." && pwd)"
SIM="$REPO/simulator3d"
IDS="beide"; SPRACHEN="de"; HOEHE=1080; FPS=25; AB=""; BIS=""; UT="auto"; GRAFIK="normal"
ZIEL="$PWD/trailer_videos"; GODOT_BIN="${GODOT:-}"

while [ $# -gt 0 ]; do
  case "$1" in
    --id) shift; IDS="${1:-beide}" ;;
    --sprache) shift; SPRACHEN="${1:-de}" ;;
    --hoehe) shift; HOEHE="${1:-1080}" ;;
    --fps) shift; FPS="${1:-25}" ;;
    --ab) shift; AB="${1:-}" ;;
    --bis) shift; BIS="${1:-}" ;;
    --untertitel) shift; UT="${1:-auto}" ;;
    --grafik) shift; GRAFIK="${1:-normal}" ;;
    --ziel) shift; ZIEL="${1:-$ZIEL}" ;;
    --godot) shift; GODOT_BIN="${1:-}" ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) echo "Unbekannte Option: $1 (--help)"; exit 2 ;;
  esac
  shift
done

[ "$IDS" = "beide" ] && IDS="grossvater maggie"
[ "$SPRACHEN" = "alle" ] && SPRACHEN="de fr it rm en"
case "$HOEHE" in 720) BREITE=1280 ;; 1080) BREITE=1920 ;; *) echo "--hoehe 720 oder 1080"; exit 2 ;; esac

if [ -z "$GODOT_BIN" ]; then
  for k in godot godot4 Godot_v4.3-stable_linux.x86_64 /tmp/claude-0/godot/Godot_v4.3-stable_linux.x86_64; do
    if command -v "$k" >/dev/null 2>&1; then GODOT_BIN="$(command -v "$k")"; break; fi
  done
fi
[ -x "${GODOT_BIN:-}" ] || { echo "Godot 4.3 nicht gefunden (--godot PFAD oder Umgebungsvariable GODOT)"; exit 2; }
command -v ffmpeg >/dev/null 2>&1 || { echo "ffmpeg fehlt"; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 fehlt"; exit 2; }
mkdir -p "$ZIEL"

XVFB_PID=""
if [ -z "${DISPLAY:-}" ]; then
  command -v Xvfb >/dev/null 2>&1 || { echo "Kein Bildschirm und kein Xvfb"; exit 2; }
  for d in $(seq 240 260); do
    if [ ! -e "/tmp/.X11-unix/X$d" ]; then
      Xvfb ":$d" -screen 0 "${BREITE}x${HOEHE}x24" >/dev/null 2>&1 &
      XVFB_PID=$!; export DISPLAY=":$d"; sleep 1; break
    fi
  done
fi
aufraeumen() { [ -n "$XVFB_PID" ] && kill "$XVFB_PID" 2>/dev/null; }
trap aufraeumen EXIT

stimme_fuer() {   # espeak-ng-Stimme für eine Sprache ("" = keine)
  command -v espeak-ng >/dev/null 2>&1 || { echo ""; return; }
  case "$1" in
    de) v=de ;; fr) v=fr-fr ;; it) v=it ;; en) v=en-gb ;; *) v="" ;;
  esac
  if [ -n "$v" ] && espeak-ng --voices 2>/dev/null | awk '{print $2}' | grep -qx "$v"; then echo "$v"; else echo ""; fi
}

ERG=()
for ID in $IDS; do
  for L in $SPRACHEN; do
    ARB="$(mktemp -d "${TMPDIR:-/tmp}/trailer_${ID}_${L}_XXXX")"
    STIMME="$(stimme_fuer "$L")"
    UTX="$UT"
    if [ "$UTX" = "auto" ]; then [ -n "$STIMME" ] && UTX="aus" || UTX="an"; fi
    EXTRA=()
    [ -n "$AB" ] && EXTRA+=(--trailer-ab "$AB")
    [ -n "$BIS" ] && EXTRA+=(--trailer-bis "$BIS")
    echo "== $ID ($L): Aufnahme ${BREITE}x${HOEHE} @ ${FPS} fps, Stimme: ${STIMME:-keine (Untertitel)} – das dauert (Movie Maker rendert jedes Bild) …"
    T0=$(date +%s)
    ( cd "$SIM" && HOME="$ARB/home" "$GODOT_BIN" --resolution "${BREITE}x${HOEHE}" --path . \
        --write-movie "$ARB/film.avi" --fixed-fps "$FPS" -- --no-update --grafik "$GRAFIK" \
        --trailer "$ID" --trailer-sprache "$L" --trailer-untertitel "$UTX" --trailer-cues "$ARB/cues.json" --trailer-quit "${EXTRA[@]}" \
        > "$ARB/godot.log" 2>&1 )
    if [ ! -s "$ARB/film.avi" ] || [ ! -s "$ARB/cues.json" ]; then
      echo "!! Aufnahme fehlgeschlagen ($ID $L) – siehe $ARB/godot.log"; ERG+=("✗ $ID $L"); continue
    fi
    VOR=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['vorlauf'])" "$ARB/cues.json")
    # the narrator: one wav per sentence, delayed to its time (relative to the start of the trailer)
    INS=(); FIL=""; N=0
    if [ -n "$STIMME" ]; then
      while IFS=$'\t' read -r REL TEXT; do
        [ -z "$TEXT" ] && continue
        N=$((N+1))
        espeak-ng -v "$STIMME" -s 140 -p 30 -w "$ARB/s$N.wav" "$TEXT" 2>/dev/null || continue
        INS+=(-i "$ARB/s$N.wav")
        MS=$(python3 -c "import sys; print(int(round(float(sys.argv[1])*1000)))" "$REL")
        FIL="$FIL[$N:a]aresample=48000,volume=1.6,adelay=${MS}|${MS}[v$N];"
      done < <(python3 -c "
import json,sys
d=json.load(open(sys.argv[1])); ab=float(d.get('ab',0))
for s in d['saetze']: print('%.3f\t%s' % (float(s['rel'])-ab, s['text'].replace('\t',' ')))" "$ARB/cues.json")
    fi
    OUT="$ZIEL/trailer_${ID}_${L}${AB:+_ab$AB}${BIS:+_bis$BIS}.mp4"
    if [ "$N" -gt 0 ]; then
      MIX="[0:a]volume=1.0[m];$FIL[m]"
      for i in $(seq 1 "$N"); do MIX="$MIX[v$i]"; done
      MIX="${MIX}amix=inputs=$((N+1)):normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
      ffmpeg -loglevel error -y -ss "$VOR" -i "$ARB/film.avi" "${INS[@]}" -filter_complex "$MIX" -map 0:v -map "[a]" \
        -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
    else
      ffmpeg -loglevel error -y -ss "$VOR" -i "$ARB/film.avi" -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:v libx264 -preset veryfast \
        -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
    fi
    if [ -s "$OUT" ]; then
      ERG+=("✓ $OUT ($(( $(date +%s)-T0 )) s, Stimme: ${STIMME:-keine})")
      rm -f "$ARB/film.avi"
    else
      ERG+=("✗ $ID $L (ffmpeg) – Rohdatei: $ARB/film.avi")
    fi
  done
done
echo; printf '%s\n' "${ERG[@]}"
