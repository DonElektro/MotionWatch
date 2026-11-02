#!/bin/bash
B=/tmp/claude-0/erkt4; T=$B/tools
cd $T && FPSMIN=2.4 REP=2 VARIANTS="a fix2" bash run4.sh
echo "$(date +%T) Diagnose (fix2)" >> $B/out/ursache.log
bash $T/start_mw.sh diag $B/builds/fix2/webcam_bewegung_3_35_0.py ""
cd $T && VARIANT=diag FPSMIN=2.4 PAUSE_AT=99 LOADMAX=3.0 LOADWAIT=7200 python3 diag4.py >> $B/out/run_diag.out 2>&1
cp $B/mw_diag/motionwatch.log $B/out/diag/motionwatch.log 2>/dev/null
echo "$(date +%T) warte auf builds/final/READY" >> $B/out/ursache.log
while [ ! -f $B/builds/final/READY ]; do sleep 20; done
bash $T/test3.sh t3nach $(cat $B/builds/final/READY)
bash $T/test3.sh t3vor /tmp/claude-0/wt_erk4t/webcam_bewegung_3_35_0.py
cd $T && FPSMIN=2.4 REP=1 VARIANTS="t1 alle wind tier" bash run4.sh
echo "$(date +%T) PLAN2 ENDE" >> $B/out/ursache.log
