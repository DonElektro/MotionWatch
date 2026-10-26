@echo off
rem Double-click to start the Motion Watch simulator (the simulated world - Motion Watch connects to it over the network).
rem On the first start the missing Python packages are installed automatically.
cd /d "%~dp0"

set PY=python
%PY% --version >nul 2>&1 || set PY=py
%PY% --version >nul 2>&1 || (
  echo Python was not found. Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" during the installation, then start this again.
  pause
  exit /b 1
)

%PY% -c "import cv2, numpy, PIL" >nul 2>&1
if errorlevel 1 (
  echo First start: installing the Python packages - opencv-python, numpy, pillow ...
  %PY% -m pip install -r requirements.txt || %PY% -m pip install --user -r requirements.txt
  %PY% -c "import cv2, numpy, PIL" >nul 2>&1 || (
    echo.
    echo The packages could not be installed - see the messages above.
    pause
    exit /b 1
  )
)

%PY% motion_sim.py %*
if errorlevel 1 (
  echo.
  echo Something went wrong - see the message above.
  pause
)
