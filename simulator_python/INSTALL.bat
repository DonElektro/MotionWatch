@echo off
rem Optional: installs the Python packages the simulator needs (START SIMULATOR.bat also does this by itself).
cd /d "%~dp0"
set PY=python
%PY% --version >nul 2>&1 || set PY=py
%PY% --version >nul 2>&1 || (
  echo Python was not found. Install it from https://www.python.org/downloads/  ^(tick "Add python.exe to PATH"^)
  pause
  exit /b 1
)
%PY% -m pip install -r requirements.txt || %PY% -m pip install --user -r requirements.txt
%PY% -c "import cv2, numpy, PIL" >nul 2>&1 && (
  echo.
  echo Done. Now double-click "START SIMULATOR.bat".
) || (
  echo.
  echo Installing failed - see the messages above.
)
pause
