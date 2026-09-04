# Comic Pipeline

Goal: take a curated list of complete comic runs, resolve them to verified source pages, inspect the approved packages, resolve candidate host links, and organize obtained files for Mihon's local source.

## Current status

### Stage 1 — canonical wanted list ✅
`wanted.json` contains the curated comic targets: title, year, creator, and wanted issue range.

### Stage 2 — ReadComicOnline discovery retired ⚠️
The live-search experiment against `readcomiconline.li` failed because the hostname no longer resolves from the test machine. `search_comics.py` remains only for reference.

### Stage 3 — approved GetComics mapping ✅
`approved_getcomics.json` maps all 52 current wanted entries to reviewed landing pages, including package notes such as TPB, issue bundle, master-series subset, extras, and known gaps.

### Stage 4 — landing-page inspection ✅
The uploaded inspection covered 66 package pages. 57 returned HTTP 200 locally; 9 returned HTTP 429 rate limits rather than missing-page errors. Those 9 landing pages were checked separately. See `PACKAGE_REVIEW.md`.

Important special cases:
- Nightwing (2016) #78-118: current TPB set is not exact contiguous coverage and remains REVIEW-only.
- Nightwing (1996) #1-70: master page contains more than the wanted subset.
- JLA (1997) #1-41: master page contains more than the wanted subset.

### Stage 5 — download-link resolution 🟡
`resolve_download_links.py` inspects only the already-approved landing pages and extracts candidate host links. It does **not** download comic files and does not fuzzy-search for alternate titles.

Run:

```powershell
git pull
python -m pip install -r requirements.txt
python .\resolve_download_links.py
```

Or double-click `RUN_RESOLVE.bat`.

Then send/review:

`results\download_link_candidates.md`

### Next — deterministic acquisition + Mihon organizer
After candidate host links are reviewed, the next tools will use only explicitly approved selections, then organize files into:

`Mihon/local/<Series>/`

The organizer will normalize names, repack supported archives when needed, create `details.json`, and avoid overwriting existing files.

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
