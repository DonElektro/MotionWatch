#!/bin/bash
# Test 3: MoveEye-Variante starten. $1 = Variante, $2 = Programmdatei, $3 = MW_ERK_AUS (Regeln aus, nur Testbau)
B=/tmp/claude-0/erkt3
V=$1; F=$2
[ -f $B/mw.pid ] && kill $(cat $B/mw.pid) 2>/dev/null; sleep 3
rm -rf $B/mw_$V; cp -r $B/mw_tpl $B/mw_$V
cd $B/mw_$V
MW_ERK_AUS="$3" HOME=$B/home DISPLAY=:183 python3 $F --headless --port 5183 --bind 127.0.0.1 --config $B/mw_$V > $B/mw_$V.out 2>&1 &
echo $! > $B/mw.pid
for i in $(seq 1 60); do curl -s -m 3 http://127.0.0.1:5183/api/state >/dev/null && break; sleep 3; done
sleep 30
