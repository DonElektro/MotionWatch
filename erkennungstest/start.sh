#!/bin/bash
# Grosser Erkennungstest: Xvfb :163, Simulator 9263, MoveEye 5163 (eigenes HOME)
Xvfb :163 -screen 0 1280x720x24 > /tmp/claude-0/erk2/xvfb.log 2>&1 &
XV=$!
sleep 2
cd /tmp/claude-0/wt_erk/simulator3d
DISPLAY=:163 HOME=/tmp/claude-0/erk2/home /tmp/claude-0/godot/Godot_v4.3-stable_linux.x86_64 --path . -- --no-update --stream --scene camping --hour 12 --port 9263 --quality simple --mini-tiny > /tmp/claude-0/erk2/sim.log 2>&1 &
SIM=$!
echo $SIM > /tmp/claude-0/erk2/sim.pid
cd /tmp/claude-0/erk2/mw
HOME=/tmp/claude-0/erk2/home DISPLAY=:163 python3 /tmp/claude-0/wt_erk/webcam_bewegung_2_98_110.py --headless --port 5163 --bind 127.0.0.1 --config /tmp/claude-0/erk2/mw > /tmp/claude-0/erk2/mw.log 2>&1 &
MW=$!
echo $MW > /tmp/claude-0/erk2/mw.pid
wait $SIM
kill $MW $XV
