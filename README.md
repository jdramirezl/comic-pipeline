# Comic Pipeline

Goal: take a curated list of complete comic runs, resolve them to verified source pages, inspect the approved packages, and organize legitimately obtained files for Mihon's local source.

## Current status

### Stage 1 — canonical wanted list ✅
`wanted.json` contains the curated comic targets: title, year, creator, and wanted issue range.

### Stage 2 — ReadComicOnline discovery retired ⚠️
The live-search experiment against `readcomiconline.li` failed because the hostname no longer resolves from the test machine. The generated report showed DNS `NameResolutionError` failures before any HTTP request could reach the site.

`search_comics.py` remains in the repo only for reference.

### Stage 3 — approved GetComics mapping ✅
`approved_getcomics.json` maps all 52 current wanted entries to the previously reviewed GetComics landing pages, including package notes such as TPB, issue bundle, master-series subset, extras, and known gaps.

Important caveats are recorded directly in the manifest, especially for:
- Nightwing (2016) Tom Taylor trades;
- Nightwing (1996) master-series subset;
- JLA (1997) Morrison subset;
- Hulk: Future Imperfect reprint packaging;
- Moon Knight (2021) fan-made omnibus packaging.

### Stage 4 — landing-page inspection 🟡
`inspect_getcomics.py` checks every approved landing page without downloading comic files. It records:
- HTTP status and final URL;
- page title/H1;
- short text snippets useful for verifying collected contents/issue ranges;
- external host names present on the page (not direct file URLs).

Run on Windows:

```powershell
git pull
python -m pip install -r requirements.txt
python .\inspect_getcomics.py
```

Or double-click `RUN_INSPECT.bat`.

Then review/upload:

`results\getcomics_inspection.md`

### Next — Mihon organizer
After the package inspection is reviewed, the next deterministic tool will organize files you have obtained from sources you are authorized to use into:

`Mihon/local/<Series>/`

It will normalize names, convert/repack supported archives when needed, create `details.json`, and avoid overwriting existing files.

## Windows setup

First clone:

```powershell
git clone https://github.com/jdramirezl/comic-pipeline.git
cd comic-pipeline
```

Later updates:

```powershell
git pull
```
