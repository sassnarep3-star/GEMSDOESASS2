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

