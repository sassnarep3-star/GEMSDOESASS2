# Executive summary and submission instructions (2026-10-30)

**NOT CLEARED FOR SUBMISSION:** no qualifying GeoTIFF is approved. The best unique candidate
passes local format checks and the peer-uniqueness gates but fails the literal registered-lattice
duplicate rule (99.74% of its dots within 3 px of the pinned 13GEMSDOE lattice). Its run card
records `verdict: negative`. No HOLDOUT-DTI, no leaderboard estimate and no organizer receipt
exists in this environment.

The nine historical site-best values are **USER-REPORTED / UNVERIFIED**. The linked raster
variants are research-only, not files to re-upload.

## How to submit (once a file is cleared)

1. Confirm the file's run card says `verdict: promote`, `ok_to_submit: true`, with a passed
   uniqueness check (surface and final dots), individual-feature leakage canaries and a
   HOLDOUT-DTI with 95% CI. The separate selector step owns promotion to a real slot.
2. Download the cleared `.tif` (or a `.zip` containing exactly one GeoTIFF) and verify the
   SHA-256 against the run card.
3. Check the format: single `float32` band, EPSG:32611, 100 m, shape 3730×3292, geotransform
   `(100, 0, 243350, 0, -100, 4508550)`, values in [0,1] inside the study area, NaN or masked
   zeros outside ([spec](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format)).
4. On the [submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/),
   choose the file in "File to submit" and paste the run card's unique note (≤140 characters).
5. Record the submission-page receipt (file, timestamp, score) — only that turns a number into
   ORGANIZER-CONFIRMED. Rules allow three submissions per week ([§3.2](https://docs.nlr.gov/docs/fy26osti/96647.pdf)).

The reported portal error `"Predicted values must be in range [0, 1]"` is analysed in the
[HTML guide](executive-summary.html#range-error): the rejected bytes are unavailable,
so no cause is confirmed; the zeros convention avoids any NaN-related range ambiguity.

A successful local validator does not guarantee portal acceptance. See
[IRREGULARITIES.md](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/IRREGULARITIES.md) and the [dashboard](index.html).
