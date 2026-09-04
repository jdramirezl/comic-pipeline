# Comic Pipeline — Stage 2 v3

The previous live-search version used Python's basic urllib client. ReadComicOnline can reject that client, which caused every title to appear missing.

This version:
- uses ReadComicOnline's own `/Search/Comic?keyword=...` endpoint;
- uses `cloudscraper`, the same Cloudflare-oriented dependency used by Comic-DL;
- still downloads **zero comic pages/issues**;
- retains deterministic candidate URL guesses if live verification is blocked, so the review step can continue.

## Run on Windows

Double-click `RUN_SEARCH.bat`.

Or in PowerShell:

```powershell
python -m pip install requests beautifulsoup4 cloudscraper
python .\search_comics.py
```

Then upload:

`results\search_results.md`
