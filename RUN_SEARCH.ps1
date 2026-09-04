Set-Location $PSScriptRoot
Write-Host "Installing/updating search dependencies..."
python -m pip install -q requests beautifulsoup4 cloudscraper
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ""
Write-Host "Searching ReadComicOnline..."
python .\search_comics.py
