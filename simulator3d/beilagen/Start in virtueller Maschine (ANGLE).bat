@echo off
rem Fuer virtuelle Maschinen (VMware, VirtualBox): Grafik ueber ANGLE / Direct3D 11. Ab 3D-1.8 macht der Simulator das selbst.
start "" "%~dp0MoveEyeSim3D.exe" --rendering-driver opengl3_angle -- --angle-tried
