# GEMSDOESASS2 — Executive Summary (`SASS2-XGHF` + 9-Site Audit)

- **Generated Unique GeoTIFF:** `docs/downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif` (`165,398 B`, SHA-256 `2a122a409c7a7d5977a311dce271d6f333f21a697cd9effd59b45c6c0f0e8ec7`)
- **ZIP SHA-256:** `f13af8d55bcc637211033a7fb67e3af110ad3cb4d617c46bbdea2e87509e7faa`
- **Submission Name / Note (`69/140` chars):** `GEMSDOESASS2-XGHF-e7996841` · `SASS2 XGHF 37654d B2 | HR 0.1311 SGMC 0.0668 | e7996841 | xgrad+hf+pu`
- **Format & Strict GDAL Mask:** `13/13` `validate_geotiff` PASS + `11/11` `validate_tif.py` `strict_local_format_pass=true` (all `12,279,160` cells finite `[0,1]` + exact `GDAL_TIFF_INTERNAL_MASK`).
- **59-Channel Leakage Canary:** `59/59 <= 0.90` (`max = 0.82627`).
- **Dual-Instrument Holdout (`HOLDOUT-DTI`):**
  - `GEMSDOE32-HIDE-RECOVER-v3.0` (`n=22,232`): **`0.131134 [0.118009, 0.142930]`** vs `0.2778` Champion `0.099202` (**paired $\Delta = +0.032048 [+0.021652, +0.042293]$, $p = 1.000$**).
  - `GEMSDOE32-SGMC-CAL-v3.0` (`n=62,703`): **`0.066793 [0.060406, 0.072338]`** vs `0.2778` Champion `0.064121`.
- **Uniqueness & Selector Verdict:** `429/429` genuine rasters `<= 69.11% <= 70.0%` (`27.00%` vs `0.2778` Champion; `33.53%` vs `SCU1`; `max |Spearman| = 0.0992 <= 0.90`). Overall strict Run Card `verdict = "negative"` (`ok_to_download = true`, `ok_to_submit = false`) pending owner selector exemption of non-competitive `13GEMSDOE` calibration lattice `r13-lattice-s5` (`99.78% > 70%`, Pigeonhole floor `82.34%` at `37,654` dots) and weekly-slot approval.
