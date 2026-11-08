#!/bin/bash
# Bilder/s mit Tieren (Flora Paket 3) auf dem HP: Normal und Hoch, je mit den Grundformen (MW_TIERE=alt) und den Modellen
# (MW_TIERE=modell). Aufruf: tier_fps.sh GODOT PROJEKT(simulator3d) AUSGABE   (DISPLAY wie gewünscht: :0 = Grafikkarte)
# Ergebnis: Zeilen «TIERFPS stufe tiere ansicht fps draw_calls primitives» im Log und AUSGABE/ergebnis.txt.
VULKAN_OK=0
G="$1"; P="$2"; O="$3"; H="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$O" "$O/home"
: > "$O/ergebnis.txt"
# hoch = Forward+ (Vulkan); geht Vulkan nicht, kommt zusätzlich hoch_gl (Stufe Hoch mit OpenGL, ohne Neustart: --no-hoch)
for stufe in normal hoch hoch_gl; do
  [ "$stufe" = hoch_gl ] && [ "$VULKAN_OK" = 1 ] && continue
  EX=""; UA=""; GR=$stufe
  [ "$stufe" = hoch ] && EX="--rendering-method forward_plus"
  [ "$stufe" = hoch_gl ] && { GR=hoch; UA="--no-hoch"; }
  for tiere in alt modell; do
    L="$O/log_${stufe}_${tiere}.txt"
    ( cd "$P" && MW_TIERE=$tiere HOME="$O/home" timeout 600 "$G" $EX --path . -s "$H/tier_bilder.gd" -- --no-update $UA \
        --grafik $GR --ansichten "$H/tier_fps_ansichten.json" --aus "$O/${stufe}_${tiere}_" > "$L" 2>&1 )
    [ "$stufe" = hoch ] && grep -aq "TIERE view" "$L" && VULKAN_OK=1
    grep -a "TIERE flora=" "$L" | head -1 | sed "s/^/[$stufe $tiere] /" | tee -a "$O/ergebnis.txt"
    grep -a "TIERE view" "$L" | sed "s/^TIERE view /TIERFPS $stufe $tiere /" | tee -a "$O/ergebnis.txt"
    grep -a -m3 "SCRIPT ERROR\|Vulkan\|vulkan" "$L" | sed "s/^/[$stufe $tiere] /"
  done
done
