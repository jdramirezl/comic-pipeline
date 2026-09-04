# Comic Pipeline

Goal: take a curated list of complete comic runs, resolve them to verified source pages, download only approved packages, and organize the result for Mihon's local source.

## Current status

### Stage 1 — canonical wanted list ✅
`wanted.json` contains the curated comic targets: title, year, creator, and wanted issue range.

### Stage 2 — ReadComicOnline discovery retired ⚠️
The live-search experiment against `readcomiconline.li` failed because the hostname no longer resolves from the test machine. The generated report showed DNS `NameResolutionError` failures before any HTTP request could reach the site. Do not keep rerunning this stage unless the site/domain returns.

`search_comics.py` remains in the repo for reference, but it is no longer the preferred path.

### Stage 3 — approved GetComics mapping ✅
`approved_getcomics.json` maps all 52 current wanted entries to hand-verified GetComics landing pages, including packaging notes such as TPB, issue bundle, master-series subset, extras, and known gaps.

Important caveats are recorded directly in the manifest, especially for:
- Nightwing (2016) Tom Taylor trades;
- Nightwing (1996) master-series subset;
- JLA (1997) Morrison subset;
- Hulk: Future Imperfect reprint packaging;
- Moon Knight (2021) fan-made omnibus packaging.

### Next — downloader + Mihon organizer
The next program will read only `approved_getcomics.json`, never fuzzy-search during download, and will:
1. inspect each approved landing page;
2. expose the available download package/host options;
3. require/use the approved package selection;
4. download into an incoming directory;
5. normalize/convert archives where needed;
6. place them under `Mihon/local/<Series>/` with Mihon-friendly naming and metadata.

## Windows setup

Clone/update:

```powershell
git clone https://github.com/jdramirezl/comic-pipeline.git
cd comic-pipeline
```

Later updates:

```powershell
git pull
```

The ReadComicOnline search script is retained only as an experiment; the active manifest is `approved_getcomics.json`.
