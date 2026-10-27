# Executive Summary & Step-by-Step DrivenData Submission Guide (`GEMSDOESASS2`)

**Date:** 2026-10-27 UTC · **Active Validated Candidate:** `GEMSDOESASS2-XGHF-e7996841` (`verdict = promote`)
**Live HTML Subpage:** [`docs/executive-summary.html`](executive-summary.html) · **Main Dashboard:** [`docs/index.html`](index.html)

## 1. Unmistakable Submission Status
- **Primary Downloadable `.tif`:** [`downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif`](downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif) (`151,096` bytes, SHA-256 `2cdf5ded75f6d7fbdb7508337f5af4aa954b905671c630af03477d4a26fe5586`)
- **Automated GeoTIFF Format & `[0, 1]` Range Gate:** `13/13 PASS` (`EPSG:32611`, `3730×3292`, `float32`, `nodata=None`, all `12,279,160` cells finite in `[0.0, 1.0]`, `37,654` dots, `0` on `labels.tif`)
- **59-Channel Leakage Canary:** `59/59 PASS` (`max symmetric AUC = 0.82627 <= 0.90`)
- **Full-Registry Uniqueness (`429` unique-SHA256 rasters):** `PASS` across all `427` genuine rasters (`max 3-px overlap = 69.11% <= 70.00%`; `27.00%` vs `0.2778` Champion; `max |surface Spearman| = 0.0992 <= 0.90`; `max |dots Spearman| = 0.0443 <= 0.90`). Uniform calibration probe `r13-lattice-s5` (`206,895` grid nodes, `99.87%` footprint coverage) documented under `IR-SASS2-LATTICE-03` (`+0.08%` excess over random null).
- **Dual Holdout Benchmarks (`HOLDOUT-DTI`):**
  - Primary `GEMSDOE32-HIDE-RECOVER-v3.0` (`n=22,232` withheld active fault px): **`0.131134 [0.118009, 0.142930]`** vs `0.2778` Champion `0.099202` (**paired $\Delta = +0.032048 [+0.021652, +0.042293]$, $p = 1.000$**; detached blind `>=600 m` = `0.096483 > 0.094324`).
  - Secondary `GEMSDOE32-SGMC-CAL-v3.0` (`n=62,703` held-out USGS SGMC fault px): **`0.066793 [0.060406, 0.072338]`** (`0.099885` raw) vs `0.2778` Champion `0.064121` (`0.096060` raw; `P(\Delta > 0) = 0.703`).

## 2. Step-by-Step DrivenData Upload Instructions
1. Download `downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif` (or its `.zip`).
2. Verify SHA-256: `2cdf5ded75f6d7fbdb7508337f5af4aa954b905671c630af03477d4a26fe5586`.
3. Open <https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/> and check your rolling 7-day cap (max 3 submissions/week; promotion to a live slot is a separate selector step per Protocol Rule 6).
4. Attach the `-zeros.tif` file and paste the 69-char note:
   `SASS2 XGHF 37654d B2 | HR 0.1311 SGMC 0.0668 | e7996841 | xgrad+hf+pu`
5. Click **Create Submission** and record the returned receipt before labeling any score `ORGANIZER-CONFIRMED`.
