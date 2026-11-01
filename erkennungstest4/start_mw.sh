#!/bin/bash
# Erkennung 4: MoveEye-Variante starten. $1 Variante, $2 Programmdatei, $3 MW_ERK_AUS, $4 Vorlage (Einstellungen)
B=/tmp/claude-0/erkt4
V=$1; F=$2; TPL=${4:-$B/mw_tpl}
[ -f $B/mw.pid ] && kill $(cat $B/mw.pid) 2>/dev/null; sleep 3
rm -rf $B/mw_$V; cp -r $TPL $B/mw_$V
mkdir -p $B/out/$V
cd $B/mw_$V
MW_DEBUG_TRACKS=$B/out/$V/tracks.jsonl MW_ERK_AUS="$3" HOME=$B/home DISPLAY=:184 nice -n -10 python3 $F --headless --port 5184 --bind 127.0.0.1 --config $B/mw_$V > $B/mw_$V.out 2>&1 &
echo $! > $B/mw.pid
for i in $(seq 1 60); do curl -s -m 3 http://127.0.0.1:5184/api/state >/dev/null && break; sleep 3; done
sleep 30
