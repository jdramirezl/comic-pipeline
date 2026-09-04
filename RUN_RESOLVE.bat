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
echo Resolving candidate host links from approved landing pages...
python resolve_download_links.py
echo.
pause
