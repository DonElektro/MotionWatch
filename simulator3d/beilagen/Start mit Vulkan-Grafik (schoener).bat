@echo off
rem Schoenere Grafik (Vulkan, Forward+). Geht nicht auf jedem PC: schliesst sich das Fenster gleich wieder, die .exe direkt starten.
start "" "%~dp0MoveEyeSim3D.exe" --rendering-driver vulkan --rendering-method forward_plus
