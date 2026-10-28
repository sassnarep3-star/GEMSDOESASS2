# Executive summary and submission instructions

**DO NOT SUBMIT:** no qualifying new GeoTIFF is available. Previously generated HVFD-EXP3 and XGHF files both fail the literal registered-lattice overlap gate, even though each passed a local saved-byte format check against an owner-mirror sample. No new holdout, CI, reliable leaderboard estimate, or organizer acceptance receipt exists for this session. [Dashboard](index.html) · [Evidence](data/audit.json) · [Negative run card](data/run-card.json).

The nine historical site-best values shown in the [HTML table](executive-summary.html) are **USER-REPORTED / UNVERIFIED**. The linked raster variants are research-only, not files to re-upload.

## Once a future candidate is approved by the separate selector

1. Verify that its run card records a passed pre-placement and final uniqueness check against the complete registry; individual-feature canaries; a comparable buffered holdout with 95% CI; a valid saved-byte GeoTIFF; and separate selector approval. Do not reuse today's negative artifacts.
2. Confirm the current allowance and rules in the account's [DrivenData competition](https://www.drivendata.org/competitions/306/competition-doe-gems/). The account-specific quota is not accessible here.
3. Download that candidate's `.tif` or a `.zip` containing exactly one TIFF. Verify the SHA-256 against the run card. Predictions must be a single `float32` band in `[0,1]`, aligned to the organizer template, with no invalid inside-footprint cells. The [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) requires matching CRS, resolution and bounds and null/NaN outside the bounds.
4. Open the competition's **New submission** form, choose the approved file, enter its unique short note (at most 140 characters under the project protocol), and submit. Record the file hash, note, timestamp and actual score receipt. Disclose applicable AI assistance as required by the [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

A successful local validator does not guarantee portal acceptance. The bytes that produced the user's earlier range error are unavailable, so its cause remains unknown.
