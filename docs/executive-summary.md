# Executive summary (2026-10-30)

**Status: one unique, validated file is approved for download. Read the gate failure below before uploading.**

- **Download:** `gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif` — SHA-256 `6d00f58a35005a253e352e21c8adde0e108aa0abb4b810db9797af89d94dd615`. 37,654 cells, 0.00 % inside the complete fault catalogue, `nodata=None`, all 12,279,360 cells finite in [0, 1].
- **Submission name:** `GEMSDOESASS2-STRAINRIDGE-OFFCAT-37654D` · **note (129/140):** `strain+ridgelineament prior, same 37654 dot budget as champion, 0% on full USGS QFaults catalogue, off-catalogue blind faults`.
- **Estimated score: 0.29 (MODEL ESTIMATE, not organizer-confirmed).** Controlled one-variable extrapolation: champion 0.2778 with 5.77 % catalogue contamination → same 37,654 dots at 0.00 % contamination = 0.2853; slope ±50 % gives 0.2815–0.2890; all model risk 0.25–0.33.
- **What that means:** about **+0.008** over the best focus site. Nothing here reaches 0.4413, and the README explains what would be required.
- **Gates passed:** format **11/11**; uniqueness **36.45 %** max overlap and **0.0115** max |ρ| over 19 competing rasters; blocked holdout **HOLDOUT-DTI 0.2244** vs matched incumbent **0.0715** (3.14×, P = 0.958).
- **Gate failed, disclosed:** the literal 70 %-within-3-px rule against the `13gems_20261001_r13-lattice-s5` calibration probe — **99.37 %**. A seeded random placement at the same dot count scores **99.91 %**, so the test is saturated and non-discriminating (IR-S-01, IR-RV-04). The probe is a calibration surface, not a competing submission. **Owner ruling required.**
- **Why 0.2778 happened:** the nine focus sites are one collar sweep, not nine models. 19.52 % contamination → 0.2600, 11.73 % → 0.2708, 5.77 % → 0.2778; +0.0012 per point removed (R² = 0.998). All nine overlap each other by ≥97.58 % within 3 px, and the catalogue they used is missing 95,452 mapped fault cells.

Full detail: [front page](index.html) · [how to submit](executive-summary.html) · [why 0.2778 scored](method.html) · [irregularities IR-S-11 to IR-S-20](../IRREGULARITIES.md).
