#!/bin/bash
# Simulator + Läufe in einem Prozessbaum ($1 = Läufer-Skript, Rest = env schon gesetzt)
B=/tmp/claude-0/erkt3
bash $B/tools/start_sim.sh
for i in $(seq 1 60); do curl -s -m 3 http://127.0.0.1:9283/control -d '{"action":"get"}' >/dev/null && break; sleep 3; done
sleep 10
bash "$@"
kill $(cat $B/mw.pid) $(cat $B/sim.pid) $(cat $B/xvfb.pid) 2>/dev/null
