#!/bin/bash
# Fortsetzung nach Unterbruch: Simulator+MoveEye starten, Rest des Tests nachholen
B=/tmp/claude-0/erkt2
bash $B/tools/start.sh > $B/out/start3.out 2>&1 &
ST=$!
for i in $(seq 1 90); do
  curl -s -m 3 http://127.0.0.1:9282/control -d '{"action":"get"}' >/dev/null && curl -s -m 3 http://127.0.0.1:5182/api/state >/dev/null && break
  sleep 3
done
sleep 20
cd $B/tools
python3 driver.py camping,wald,stellplatz
python3 sync.py >> ../out/sync.log 2>&1
LEERWIND=12 NOBLIND=1 python3 driver.py festival:tag+nacht,garten:tag+nachtregen,baustelle:nacht,wild:tag+nacht,camping:dunkel,schlafzimmer
python3 extra.py diag,kopf,blend,linse
python3 sync.py >> ../out/sync.log 2>&1
kill $(cat $B/sim.pid) 2>/dev/null
sleep 3
kill $ST 2>/dev/null
echo ENDE
