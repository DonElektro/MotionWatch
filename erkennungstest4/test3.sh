#!/bin/bash
# Test 3 für eine Fassung: $1 = Name (t3nach / t3vor), $2 = Programmdatei
B=/tmp/claude-0/erkt4; T=$B/tools; V=$1; F=$2
echo "$(date +%T) Test 3 $V ($F)" >> $B/out/ursache.log
bash $T/start_mw.sh $V $F ""
G="FPSMIN=2.4 PAUSE_AT=99 LOADMAX=3.0 LOADWAIT=7200"
cd $T && env VARIANT=$V REP=1 NOBLIND=1 FPSMIN=2.4 PAUSE_AT=99 LOADMAX=3.0 LOADWAIT=7200 python3 driver.py camping,wald,stellplatz >> $B/out/run_$V.out 2>&1
cd $T && env VARIANT=$V REP=1 NOBLIND=1 LEERWIND=12 FPSMIN=2.4 PAUSE_AT=99 LOADMAX=3.0 LOADWAIT=7200 python3 driver.py festival:tag+nacht,garten:tag+nachtregen,baustelle:nacht,wild:tag+nacht,camping:dunkel,schlafzimmer >> $B/out/run_$V.out 2>&1
cd $T && env VARIANT=$V FPSMIN=2.4 PAUSE_AT=99 LOADMAX=3.0 LOADWAIT=7200 python3 extra.py kopf,blend >> $B/out/run_$V.out 2>&1
cp $B/mw_$V/motionwatch.log $B/out/$V/motionwatch.log 2>/dev/null
echo "$(date +%T) Test 3 $V ENDE" >> $B/out/ursache.log
