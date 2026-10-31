@echo off
rem Zweiter Simulator auf demselben PC: eigener Port 8768 (der erste hat 8765). MoveEye findet ihn von selbst.
rem Bis 3.15 hiess diese Datei "Start auf Port 8766.bat" - 8766 ist aber der Tunnel-Port von MoveEye.
rem Das Spiel dieses Simulators hat eigene Ports (9776 / 9777), es kommt dem ersten nicht in die Quere.
start "" "%~dp0MoveEyeSim3D.exe" -- --port 8768
