@echo off
cd /d "%~dp0"
echo Installing/updating dependencies...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo.
  echo Dependency install failed.
  pause
  exit /b 1
)
echo.
echo Inspecting approved GetComics landing pages...
python inspect_getcomics.py
echo.
pause
