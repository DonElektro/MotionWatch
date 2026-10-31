#!/bin/bash
# Test 3: Xvfb :183, Simulator 9283 (gleicher Simulator wie Test 2: wt_erk2, 3.8.0)
B=/tmp/claude-0/erkt3
Xvfb :183 -screen 0 1280x720x24 > $B/xvfb.log 2>&1 &
echo $! > $B/xvfb.pid
sleep 2
cd /tmp/claude-0/wt_erk2/simulator3d
DISPLAY=:183 HOME=$B/home /tmp/claude-0/godot/Godot_v4.3-stable_linux.x86_64 --path . -- --no-update --stream --scene camping --hour 12 --port 9283 --quality simple --mini-tiny > $B/sim.log 2>&1 &
echo $! > $B/sim.pid
