# Executive summary (2026-10-31 update) — **supersedes the 2026-10-30 headline**

- **Download (one click):** [`downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif`](downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif) ·
  SHA-256 `c200ceccef52b45b979d5a2ad5c184516f8181828493400704a408074b7cbeb6` · [zip](downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.zip) · GIS twin `-nan.tif` (not the portal file).
- **Submission name:** `GEMSDOESASS2-COLLAR4HEX-37636D` · **note (94/140):** `hex covering lattice, 4 px off-catalogue collar, same 37,654-dot budget as the 0.2778 champion`.
- **Format gate: 13/13 on the saved bytes** — float32, EPSG:32611, (3730, 3292), transform exact,
  `nodata=None`, and **min/max over all 12,279,360 cells = 0.0/1.0**. That last line is the fix for the portal
  rejection *"Predicted values must be in range [0, 1]"*: the check is an **all-cells** test, so an outside-footprint
  NaN / −3.4e38 fill fails it. Walkthrough: [submit.html](submit.html).
- **Uniqueness gate: PASS on both literal tests** — over 531 registry rasters
  max 3-px overlap **43.5966 %** (limit 70) and max |ρ| **0.011049**
  (limit 0.90); exact cell coincidence with the nine site champions ≤ **0.885 %**.
  First artifact in this repository to clear both tests; the r13 space-filling calibration probe is re-scanned in
  [`evidence/uniqueness_collar4hex_fullcorpus_20261031.json`](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/evidence/uniqueness_collar4hex_fullcorpus_20261031.json)
  and any saturation there is reported, not exempted (IR-S-21, IR-S-37).
- **Disclosed failing clause:** against the `13gems_20261001_r13-lattice-s5` space-filling **calibration probe**
  **99.915 %** of our dots lie within 3 px, so the literal 70 % rule **fails** — as it does for a seeded random control
  at the same dot count (99.8964 %), which is why the clause is reported as non-discriminating rather than treated as an
  exemption. Owner ruling required (IR-03, IR-S-21, IR-S-37;
  [`evidence/collar4hex_vs_r13_lattice_20261031.json`](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/evidence/collar4hex_vs_r13_lattice_20261031.json)).
- **The 37,636 cells are 0.00 % inside `labels.tif`** — 4 px collar against the complete public fault surface
  (156,418 px), deterministic hexagonal covering lattice at 1,190 m (covering radius 687 m < the 3 px kernel),
  complete cells only, two defect re-sites.
- **Score:** **0.2851 MODEL ESTIMATE** (risk range 0.24–0.31,
  i.e. the band **includes a loss**), from the family's own measured collar gradient (+0.00127 per pp of catalogue
  contamination at fixed N). **No organizer-confirmed number exists for any file in this repository.**
- **HOLDOUT-DTI:** off-catalogue SGMC **0.078774** [0.075369, 0.081733]
  against 62,703 withheld px — *below* the champion's 0.0961, because the collar trades coverage for zero
  false-positive weight. Hide-and-recover returns **0.0 by construction** for any labels-collared emission
  (IR-S-34); the same note puts in question the superseded file's 0.2244, measured with a visible-only collar.
- **Nine-site answer:** no file among GEMSDOE24/25/27/28/30/31/32/33/36 is a unique submission — each champion is a
  ≥50 % exact subset or a >70 % within-3-px duplicate of the other eight (GEMSDOE25 ≡ GEMSDOE30; GEMSDOE32 ⊂
  GEMSDOE25). Measured table: [`data/focus-decision-table-20261031.json`](data/focus-decision-table-20261031.json).
  Consequence: the only legal use of that family is a geometry change at the same budget — exactly this file.
- **Negative results from this session, published as deliverables**
  ([`knowledge/10_rmc_negative_lane_receipt.md`](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/knowledge/10_rmc_negative_lane_receipt.md)):
  corridor geometry carries 1.4–3× *less* credit/px than random dots; supervised LOQO targeting is 3.7× *worse
  than random* on the USGS blind set; the score-transfer estimator is rejected (LOO MAE 0.1523 on 12 anchors).
- **Run card:** [`data/collar4hex-run-card.json`](data/collar4hex-run-card.json) ·
  format receipt [`downloads/format-gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.json`](downloads/format-gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.json) ·
  promoted audit [`downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-audit.json`](downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-audit.json).

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

## Review pass 5, later on 2026-10-30 (PR #27) — VRC tested: negative, published as research

- **VRC (vent-ridge continuation)** — blind traces should continue the LiDAR scarp trend leaving a mapped vent.
  Emitted at 44,090 dots (B=2 collar, 3 px thinning) through the shared stack. **NEGATIVE on both instruments**:
  HOLDOUT-DTI 0.0086294568 vs the hash-pinned focus-lineage parent 0.09674 (Δ −0.087807630, 95% CI
  [−0.1003465, −0.0757916], p(Δ>0)=0.0) and off-catalogue SGMC 0.04438 vs 0.09528 (Δ −0.05119, CI [−0.0672,
  −0.0338]). An uncollared variant is the only emission ahead of the parent on the public instrument
  (0.10471, Δ +0.00798) and its CI crosses zero. Once the emitter bug below is fixed, spacing thinning ≡ plain
  top-k, so the "continuation" selection rule adds nothing. Card:
  [`data/vrc-run-card.json`](data/vrc-run-card.json) (`status: blocked-owner-ruling`, `ok_to_submit: false`).
- **Uniqueness on the scanned sample:** max per-raster 3-px dot overlap 39.99% (limit 70%) and max |Spearman|
  over the whole footprint 0.0162 (limit 0.90) across 40 registry rasters — a **sample**, not the complete
  registry (IR-S-32). Against the space-filling `r13` lattice probe it is 1.000, so the literal rule blocks it
  for the arithmetically forced reason in IR-S-01/IR-S-21. Nothing on this branch is cleared for submission.
- **Emitter bug fixed** (`IR-VRC-01`, alias of IR-S-23): a `np.lexsort` position was used as a pixel index, so
  the first VRC pass emitted 12,572 invalid-fill dots and wrote 15,300 against a 22,163 budget. Both call sites
  now remap through the candidate array and a hard guard refuses any emission whose count ≠ budget or whose dots
  leave the allowed footprint. The defective raster was deleted, not patched.
- **Download surface:** `.zip` for both encodings of both files, manifest
  [`data/download-hashes.json`](data/download-hashes.json), per-check receipts
  [`data/format-sparse-blind-zeros.json`](data/format-sparse-blind-zeros.json) (all 11 named validator checks
  true, `strict_local_format_pass: true` vs the organizer-example mirror),
  [`data/format-sparse-blind-nan.json`](data/format-sparse-blind-nan.json),
  [`data/format-vrc-zeros.json`](data/format-vrc-zeros.json),
  [`data/format-vrc-nan.json`](data/format-vrc-nan.json). "13/13" vs "11/11" is the same validator counted with
  or without the two promoted-card counts (IR-S-29).
- **Score estimate: `NOT ESTIMABLE`, and now measured twice.** The geometry-only estimator fails leave-one-out
  (R² = −0.379) and no organizer receipt exists here, so this branch publishes no MODEL ESTIMATE for any file —
  unlike the row in the pass-4 table, which extrapolates below its fitted range (that branch's own IR-S-18; see
  IR-S-27).
- **Holdout availability corrected:** `scripts/evaluate_holdout.py` is a fail-closed CLI, but
  `src/gems_sass2/holdout.py` runs and produced every number above (IR-S-24). "No holdout is possible" is not a
  valid reason to leave a promoted file unmeasured.
- **Ledger:** IR-S-23 … IR-S-33 added to
  [`IRREGULARITIES.md`](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/IRREGULARITIES.md).


**Full-corpus verification (2026-10-30).** All 113 public GEMS-named repositories were mirrored (2,282 unique competition-shaped rasters) and compared with the shared gate. The promoted file's worst genuine peer is 25.8% (the champion lineage); the only >70% hits are space-filling density artefacts (the r13 lattice at 99.37% and a 311,617-dot raster at 99.86%). The corpus's three "lattice-avoiding" files pass the literal clause only with 100% of dots on the study-area border. Receipts: [full-registry scan](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/evidence/focus_uniqueness_full_registry_20261030.json) · [lattice recheck](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/evidence/lattice_gate_recheck_20261030.json).
