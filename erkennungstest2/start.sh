#!/bin/bash
# Erkennungstest 2: Xvfb :182, Simulator 9282, MoveEye 5182 (eigenes HOME) - gleiche Optionen wie Test 1
B=/tmp/claude-0/erkt2
Xvfb :182 -screen 0 1280x720x24 > $B/xvfb.log 2>&1 &
XV=$!
sleep 2
cd /tmp/claude-0/wt_erk2/simulator3d
DISPLAY=:182 HOME=$B/home /tmp/claude-0/godot/Godot_v4.3-stable_linux.x86_64 --path . -- --no-update --stream --scene camping --hour 12 --port 9282 --quality simple --mini-tiny > $B/sim.log 2>&1 &
SIM=$!
echo $SIM > $B/sim.pid
cd $B/mw
HOME=$B/home DISPLAY=:182 python3 /tmp/claude-0/wt_erk2/webcam_bewegung_3_8_0.py --headless --port 5182 --bind 127.0.0.1 --config $B/mw > $B/mw.log 2>&1 &
MW=$!
echo $MW > $B/mw.pid
wait $SIM
kill $MW $XV
