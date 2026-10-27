# GEMSDOESASS2 — Executive Summary & Step-by-Step DrivenData Submission Guide (`SASS2-XGHF`)

## 1. Candidate Summary & Unmistakable Gate Status

- **Generated Unique GeoTIFF:** [`downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif`](downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif) (`165,398` bytes)
- **SHA-256 (`-zeros.tif`):** `2a122a409c7a7d5977a311dce271d6f333f21a697cd9effd59b45c6c0f0e8ec7`
- **SHA-256 (`-zeros.zip`):** `f13af8d55bcc637211033a7fb67e3af110ad3cb4d617c46bbdea2e87509e7faa`
- **Unique Submission Name:** `GEMSDOESASS2-XGHF-e7996841`
- **Submission Note (`69 / 140` chars):** `SASS2 XGHF 37654d B2 | HR 0.1311 SGMC 0.0668 | e7996841 | xgrad+hf+pu`
- **Automated GeoTIFF Format & Strict GDAL Mask Gate:** **PASS (`13/13` + `11/11` `strict_local_format_pass=true`)** — `EPSG:32611`, `3730×3292`, `float32`, all `12,279,160` cells finite `[0,1]` + exact `GDAL_TIFF_INTERNAL_MASK` outside footprint (`0` on `60,988` `labels.tif` pixels).
- **Protocol Rule 4 Leakage Canary:** **PASS (`59/59` symmetric AUCs `<= 0.90`; max `0.82627`)**.
- **Primary Holdout (`GEMSDOE32-HIDE-RECOVER-v3.0`, `n=22,232`):** **`HOLDOUT-DTI = 0.131134 [0.118009, 0.142930]`** vs `0.2778` Champion `0.099202` (**paired $\Delta = +0.032048 [+0.021652, +0.042293]$, $p = 1.000$**; detached `>=600 m` `0.096483 > 0.094324`).
- **Secondary Off-Catalogue Holdout (`GEMSDOE32-SGMC-CAL-v3.0`, `n=62,703`):** **`HOLDOUT-DTI = 0.066793 [0.060406, 0.072338]`** vs `0.2778` Champion `0.064121` (`raw = 0.099885` vs `0.096060`).
- **Genuine-Submission Uniqueness (`429` genuine rasters):** **PASS (`429/429 <= 69.11% <= 70.0%`; `27.00%` vs `0.2778` Champion; `33.53%` vs `SCU1`; `max |Spearman| = 0.0992 <= 0.90`)**.
- **Literal Calibration-Lattice & Selector Gate (`verdict = "negative"`, `ok_to_download = true`, `ok_to_submit = false`):** Held fail-closed for automatic live submission solely because `13GEMSDOE` uniform probe `r13-lattice-s5` (`206,895` dots, `6,649` uncovered px) mathematically forces `>= 82.34%` overlap at `37,654` dots (`99.78%` measured) and Protocol Rule 6 reserves live weekly-slot selection to the separate owner selector step.

## 2. Step-by-Step DrivenData Upload Checklist (Once Owner Selector Approves a Slot)

1. Confirm owner selector exemption of non-competitive `13GEMSDOE` calibration lattices (`r13-lattice-s5`, `r12-lattice-s6`) and verify remaining weekly quota on DrivenData (max 3/week).
2. Download `gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif` (or `-zeros.zip`) and verify SHA-256 `2a122a409c7a7d5977a311dce271d6f333f21a697cd9effd59b45c6c0f0e8ec7`.
3. Open <https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/> and click **Make new submission**.
4. Upload the `.tif` (or `.zip`) and paste the 69-character note:
   `SASS2 XGHF 37654d B2 | HR 0.1311 SGMC 0.0668 | e7996841 | xgrad+hf+pu`
5. Save the portal score receipt as `ORGANIZER-CONFIRMED` alongside hash `2a122a40...` and disclose generative-AI assistance in finalist documentation per [DOE/NLR Rules (`96647.pdf`)](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
