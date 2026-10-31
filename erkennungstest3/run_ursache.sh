#!/bin/bash
# Ursache: Varianten nacheinander, gleiche Fälle (sel_ursache.txt), Lastschwelle 3
B=/tmp/claude-0/erkt3
T=$B/tools
MAIN=/tmp/claude-0/wt_erk3t/webcam_bewegung_3_13_0.py
OLD=$B/v298/webcam_bewegung_2_98_110.py
run() {  # name file off
  echo "$(date +%T) Variante $1 ($3)" >> $B/out/ursache.log
  bash $T/start_mw.sh "$1" "$2" "$3"
  cd $T && VARIANT=$1 SEL=$T/sel_ursache.txt SEL_LEER=1 NOBLIND=1 LOADMAX=3.0 python3 driver.py camping,wald,stellplatz >> $B/out/ursache_$1.out 2>&1
  cp $B/mw_$1/motionwatch.log $B/out/$1/motionwatch.log 2>/dev/null
}
for v in $VARIANTS; do
  case $v in
    a) run a $MAIN "" ;;
    c) run c $OLD "" ;;
    alle) run alle $MAIN "alle" ;;
    *) run $v $MAIN "$v" ;;
  esac
done
echo "$(date +%T) ENDE $VARIANTS" >> $B/out/ursache.log
