# Package Review

Reviewed from `getcomics_inspection.md`.

## Result

- 52 wanted comic targets
- 66 approved landing-page packages
- 57/66 returned HTTP 200 in the user's local inspection
- 9/66 returned HTTP 429 (rate-limited), not 404/missing
- The 9 rate-limited pages were checked separately and their landing pages/content were confirmed.
- Therefore: **all 66 approved landing-page URLs are valid enough to move to host-link resolution.**

## Packaging caveats

### Needs special handling

1. **Nightwing (2016), Tom Taylor, #78-118**
   - The seven TPBs in the current manifest are not a strict contiguous #78-118 set.
   - They omit #84-86 and #110, and include some extras/tie-ins.
   - Do not treat the seven TPBs as exact coverage.
   - Keep this target in `REVIEW` until we select a better combination.

2. **Nightwing (1996), Chuck Dixon, wanted #1-70**
   - The matched landing page is the full #1-153 series.
   - Download/import logic must select only the wanted subset.

3. **JLA (1997), Grant Morrison, wanted #1-41**
   - The matched master page is #1-125.
   - The useful first chunks extend to #45.
   - Download/import logic must trim to #1-41 if using issue files.

### Acceptable contained packages with extras

These remain good reading packages for this project; extras should not block them:

- Grayson #1-20 bundle: annual/Futures End extras.
- Wonder Woman by George Pérez: annuals and War of the Gods material appear in the collected volumes.
- Green Lantern: War Journal: backup/epilogue material in the trades.
- The Flash by Mark Waid / Geoff Johns: collected-book packaging may contain annuals/related material.
- Daredevil (2011): bundle includes the Annual.
- Hulk: Future Imperfect: reprint collection contains the original two-part story.
- Moon Knight (2021): fan-made omnibus contains #1-30 plus related material.
- Mister Miracle Deluxe: #1-12 plus sketches/scripts/art extras.
- DC: The New Frontier: #1-6 plus the New Frontier Special.

## Rate-limited locally but independently confirmed

- DC: The New Frontier
- Mister Miracle
- Doctor Strange: The Oath
- Spider-Man: Spider's Shadow
- Punisher: Born
- Hulk: Grand Design
- Daredevil (2011)
- Moon Knight (1980)
- Marvels

## Decision

Proceed to **download-link resolution** for everything except Nightwing (2016), which remains a coverage-review target.
