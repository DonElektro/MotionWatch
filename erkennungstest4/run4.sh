#!/bin/bash
# Ursache: Varianten nacheinander, gleiche Fälle (sel_ursache.txt), Lastschwelle 3. VARIANTS="a t1 alle wind ..."
B=/tmp/claude-0/erkt4
T=$B/tools
MAIN=/tmp/claude-0/wt_erk4t/webcam_bewegung_3_35_0.py
FIX=${FIX:-/tmp/claude-0/erkt4/builds/fix2/webcam_bewegung_3_35_0.py}
OLD=/tmp/claude-0/erkt3/v298/webcam_bewegung_2_98_110.py
SELF=${SELF:-$T/sel_ursache.txt}
PLACES=${PLACES:-camping,wald,stellplatz}
run() {  # name file off tpl
  echo "$(date +%T) Variante $1 ($3) load $(cut -d' ' -f1 /proc/loadavg)" >> $B/out/ursache.log
  bash $T/start_mw.sh "$1" "$2" "$3" "$4"
  cd $T && VARIANT=$1 SEL=$SELF SEL_LEER=1 NOBLIND=${NOBLIND:-1} FPSMIN=${FPSMIN:-2.8} PAUSE_AT=${PAUSE_AT:-99} LOADMAX=${LOADMAX:-3.0} LOADWAIT=${LOADWAIT:-7200} python3 driver.py $PLACES >> $B/out/run_$1.out 2>&1
  cp $B/mw_$1/motionwatch.log $B/out/$1/motionwatch.log 2>/dev/null
}
for v in $VARIANTS; do
  case $v in
    a) run a $MAIN "" ;;
    t1) run t1 $MAIN "" $B/mw_tpl_t1 ;;
    v298) run v298 $OLD "" ;;
    fix*) run $v $FIX "" ;;
    *) run $v $MAIN "${v//+/,}" ;;
  esac
done
kill $(cat $B/mw.pid) 2>/dev/null
echo "$(date +%T) ENDE $VARIANTS" >> $B/out/ursache.log
