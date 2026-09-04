@echo off
cd /d "%~dp0"
echo Installing/updating search dependencies...
python -m pip install -q requests beautifulsoup4 cloudscraper
if errorlevel 1 (
  echo.
  echo Dependency install failed.
  pause
  exit /b 1
)
echo.
echo Searching ReadComicOnline...
python search_comics.py
echo.
pause
