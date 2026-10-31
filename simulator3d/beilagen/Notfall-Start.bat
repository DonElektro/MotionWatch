@echo off
rem MoveEye Sim 3D - Notfall-Start: wenn sich das Fenster gleich nach dem Start wieder schliesst.
rem Startet EINMAL mit der einfachsten Grafik: ANGLE (Direct3D 11), Grafik-Modus Lite, ohne Foto-Inhalte,
rem ohne Update-Suche und ohne Grafikstufe "Hoch". Die gespeicherten Einstellungen bleiben (nur dieser Start).
rem Liegt MoveEyeSim3D.console.exe daneben, laeuft der Simulator in diesem Fenster: die letzten Meldungen
rem bleiben stehen, falls er abstuerzt. Danach "Fehlerbericht sammeln.bat" doppelklicken und die ZIP schicken.
rem Braucht keine Adminrechte.
setlocal
set "ME_ARGS=--rendering-driver opengl3_angle -- --angle-tried --grafik lite --no-inhalte --no-update --no-hoch"
if not exist "%~dp0MoveEyeSim3D.exe" goto fehlt
if exist "%~dp0MoveEyeSim3D.console.exe" goto konsole
start "" "%~dp0MoveEyeSim3D.exe" %ME_ARGS%
exit /b 0

:konsole
echo MoveEye Sim 3D - Notfall-Start (ANGLE, Lite, ohne Foto-Inhalte, ohne Update-Suche, ohne Hoch)
echo Dieses Fenster offen lassen: hier steht, was der Simulator meldet.
echo.
"%~dp0MoveEyeSim3D.console.exe" %ME_ARGS%
echo.
echo Der Simulator ist beendet. Ist er abgestuerzt: "Fehlerbericht sammeln.bat" doppelklicken.
pause
exit /b 0

:fehlt
echo MoveEyeSim3D.exe fehlt in diesem Ordner:
echo "%~dp0"
echo Den ganzen Ordner aus der ZIP-Datei entpacken und diese Datei im selben Ordner starten.
pause
exit /b 1
