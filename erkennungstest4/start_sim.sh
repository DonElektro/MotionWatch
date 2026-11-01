#!/bin/bash
# Test 3: Xvfb :184, Simulator 9284 (gleicher Simulator wie Test 2: wt_erk2, 3.8.0)
B=/tmp/claude-0/erkt4
Xvfb :184 -screen 0 1280x720x24 > $B/xvfb.log 2>&1 &
echo $! > $B/xvfb.pid
sleep 2
cd /tmp/claude-0/erkt4/sim38/simulator3d
DISPLAY=:184 HOME=$B/home nice -n -10 /tmp/claude-0/godot/Godot_v4.3-stable_linux.x86_64 --max-fps 8 --path . -- --no-update --stream --scene camping --hour 12 --port 9284 --quality simple --mini-tiny > $B/sim.log 2>&1 &
echo $! > $B/sim.pid
