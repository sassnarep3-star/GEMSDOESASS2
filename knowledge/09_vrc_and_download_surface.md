# 09 — VENT-RIDGE CONTINUATION (IR-VRC-01): the index bug, the corrected numbers, and the download surface

Evidence class of every number below: **HOLDOUT-DTI** (this repo's evaluator, with CI) or
**DATA-MEASUREMENT**. Nothing here is an organizer score; **ORGANIZER-CONFIRMED** values are only
the ones the user reported and are labelled as such in `evidence/org_ledger_measured.json`.

## 1. What was tested

Hypothesis **VRC (vent-ridge continuation)**: mapped vents are surface expressions of conduit
breaching, so the strongest LiDAR scarp *continuations* leaving a vent should carry blind fault
trace. Named non-fault mimics that produce the same signal: **road cut, terrace riser,
palaeo-shoreline, mining step, landslide head scarp** (`data/external/*.json` band descriptions
say so explicitly: "uncalibrated terrain descriptors, not fault detections").

Surfaces emitted, each through the shared tools only (`submission_writer.write_submission`,
`holdout.evaluate_hide_and_recover`, `holdout.evaluate_sgmc_with_ci`, no forked copies):

| id | surface | rule | budget |
|---|---|---|---|
| `learned` | fold-aware logistic scarp detector (8 folds, whole fault segments withheld, catalogue features from the visible faults only, pooled DTI α 0.2 / β 0.8, 300 m triangular kernel) | B=2 collar + 3-px vent-ridge thinning | 44,090 |
| `learned+vent` | learned surface + `vent_boost` | same | 44,090 |
| `amp` | scarp amplitude only (control, no learning) | same | 44,090 |
| `topk` variants | plain top-k instead of spacing thinning | — | 37,654 / 44,090 |

## 2. IR-VRC-01 — the bug that invalidated the first pass (fixed)

`cell_of_max*` in `scripts/generate_vrc_candidate.py` and `scripts/exp_scarp_continuity.py` used
`np.lexsort(...)` output — an index **into the candidate array** — directly as a **pixel index**:

```python
order = np.lexsort((-flat[sel], -near[sel]))          # positions inside `sel`
chosen = sel[order[:k]]                               # WRONG: order indexes sel, not pixels
```

Consequence: most emitted dots were arbitrary low-score pixels (12,572 of 22,163 carried the −1.0
invalid fill value), and the emitted count silently diverged from the requested budget
(22,163 requested → 15,300 actually written in the shipped file). Fix (both scripts, commented with
this ID):

```python
chosen = cand[order[first][:n_dots]]                  # remap through the candidate array
...
mask &= allowed                                       # footprint ∧ LiDAR-valid ∧ ¬catalogue ∧ ¬on catalogue
assert outside == 0 and on_catalogue == 0              # hard emission guard
```

The defective raster was **deleted**, not patched: `evidence/unique_run_card_cc522684.json` describes
the sparse-blind-conduit file (a different generator, `scripts/generate_unique_submission.py`), whose
22,163-dot count reconciles exactly and which validates cleanly, so it stands.

**Rule going forward:** any emitter must assert `n_dots_written == budget` and zero dots outside the
allowed footprint, or it does not get a run card.

## 3. Corrected measurements (the interesting part)

Full-8-fold re-run: `evidence/exp2_scarp_continuity_full.json`, `evidence/exp8_vrc_variants.json`
(both instruments, paired 256-block bootstrap against the hash-pinned parent `gems24-h25-1-dotted-h19-5-d2-8-…-allfinite.tif`, 44,090 dots, holdout 0.09674, off-catalogue SGMC 0.09528).

| emission | HOLDOUT-DTI (public catalogue) | Δ vs parent [95% CI] | off-catalogue SGMC | Δ [95% CI] |
|---|---|---|---|---|
| `learned`, no collar, thin, 44,090 | **0.10471** | +0.00798 [−0.00794, +0.02247] | **0.00680** | −0.08860 [−0.0996, −0.0780] |
| `learned`, B=2 collar, thin, 44,090 | 0.00862 | −0.08782 [−0.1003, −0.0758] | 0.04438 | −0.05119 [−0.0672, −0.0338] |
| `amp` control, B=2 collar, thin, 44,090 | 0.00209 | −0.09465 | **0.10684** | +0.01002 [−0.0223, +0.0460] |
| VRC final (as published) | 0.0086294568 | −0.087807630 [−0.1003465, −0.0757916] | 0.04438 | −0.05119 |

Readings:

1. **The two instruments disagree about which mechanism is real**, and the disagreement is the result.
   The learned detector's advantage exists only on the *public-catalogue* instrument (the one that rewards
   continuing mapped structures) and is *not* significant (CI crosses 0). Off catalogue — where the blind
   faults actually live — it collapses by ~0.09 absolute. The amplitude-only control shows the mirror image:
   best off-catalogue reading of the whole session (0.10684, CI includes 0 against the parent) and worst
   on the public instrument.
2. **Once IR-VRC-01 is fixed, spacing thinning ≈ plain top-k.** Every "vent-ridge continuation thinning"
   advantage in earlier sessions was the bug pushing dots off the high-score set.
3. **The collar is not optional and is not free.** B=2 is what historically moved 0.2600 → 0.2778
   (FP discount to −0.4 within 3 px), but it also costs ~7,000–9,000 usable cells at 44,090 dots and is
   what destroys the learned surface's off-catalogue reading.

## 4. Verdict

`promote = NO` for VRC. Recorded in `docs/data/vrc-run-card.json` (the repo's tested `docs/data/run-card.json` stays the build_card() negative contract)
with `ok_to_download_and_submit: false`, `ok_to_submit: false` and `status: "blocked-owner-ruling"`.
Format and per-raster duplicate gates **pass**; the scientific gate does not, and the literal lattice gate blocks
the file for the arithmetically forced reason documented in IR-S-15/IR-S-16. Both reasons must be stated: a
reader who sees only "negative" may wrongly conclude the file would be submittable if the science improved.

Uniqueness (protocol rule 1, measured): max 3-px dot overlap vs the 40 scanned registry rasters
**0.3999** (limit 0.70); max |Spearman| over the whole footprint vs the nine focus-site champions
**0.0162** (limit 0.90); 0.7616 of its dots lie within 3 px of the **union** of the registry (reported,
not a gate — the gate is per raster); vs this repo's own other downloads the largest reverse share is
0.3227. Against the space-filling lattice probe the share is 1.000, which fails the literal rule for the
same reason the reported 0.2778 champion does — see IR-S-01 and `docs/data/lattice_saturation_check.json`
(only 6,649 footprint cells sit farther than 3 px from that lattice, so at 44,090 dots overlap is
arithmetically forced; a raster that *didn't* trip it would be a 6,649-dot toy).

## 5. The one-click download surface (what "download, estimate score, submit" now means here)

`docs/data/download-hashes.json` is the manifest; the README table is the human view.

| file | dots | local format check vs organizer-example mirror | status |
|---|---|---|---|
| `…sparse-blind-conduit-22163…-zeros.tif` (+ .zip) | 22,163 | all 11 validator checks true, `strict_local_format_pass: true` against the organizer-example mirror (`docs/data/format-sparse-blind-zeros.json`) | **downloadable, NOT submittable**: 99.74% of its dots lie within 3 px of the pinned lattice, so it is `blocked-owner-ruling` (IR-S-21); its own holdout has never been run (IR-S-24) |
| `…sparse-blind-conduit-22163…-nan.tif` (+ .zip) | 22,163 | fails only `whole_array_finite_in_0_1`, which is mutually exclusive with `outside_masked_or_nan` | GIS twin, identical inside footprint |
| `…vrc-ventridge-44090…-nan.tif` (+ .zip) | 44,090 | fails only `whole_array_finite_in_0_1` | research only; `blocked-owner-ruling` (lattice 1.000) and negative on both instruments |
| `…vrc-ventridge-44090…-zeros.tif` (+ .zip) | 44,090 | fails only `outside_masked_or_nan` (0 outside ≠ NaN reference) | research only, byte-identical inside footprint (max abs diff 0.0) |

**Score estimation, stated honestly.** There is *no* defensible point estimate of the organizer score for
any file. Two things are estimable and both are labelled:

* **HOLDOUT-DTI** — public-catalogue instrument (this repo's `evaluate_hide_and_recover`, whole-segment
  withholding + buffer) and off-catalogue instrument (`evaluate_sgmc_with_ci`, truth = 62,703 SGMC fault
  pixels >300 m from the public catalogue). These bound *relative* skill, with CIs, and their absolute scale
  is not the organizer's.
* **Organizer-confirmed anchors** (user-reported only, no receipts in this environment) — the nine-site ledger
  in `evidence/org_ledger_measured.json`: 0.2778 @ 37,654 dots, 0.2750 @ 38,854, 0.2710 @ 37,660, 0.2708 @
  40,199, 0.2632 @ 41,865, 0.2600 @ 44,090, 0.2477 @ 60,069, 0.2449 @ 61,328, and the geometry-only
  controls 0.0904 (lattice), 0.0512 (SGMC off-catalogue), 0.0041 (habitat mask). A geometry-only score
  estimator was fitted and **failed** leave-one-out (R² = −0.379, `scripts/fit_org_score_estimator.py`),
  which is why this repo refuses to convert dot geometry into a predicted leaderboard score.
* The public-leaderboard ceiling of the *sibling* competition read 0.4544 (rank 1, official public snapshot
  2026-10-28) while this competition's recorded high was 0.4413 → 0.4437 on earlier days; the contradiction
  is unresolved and logged (IR list), so no ceiling claim is made.
* Historical maximum for the focus sites is ~0.35 on the internal proxy scale; the parent covers 37.96% of
  pooled truth within 3 px against 89% for the r13 lattice, i.e. coverage alone explains most of the gap
  between sparse and dense files.

## 6. Next experiments this suggests (in priority order)

1. **Instrument reconciliation.** The learned-vs-amplitude split means one of the two instruments is
   mis-specified for blind traces. Cheapest decisive test: score both instruments on *published*
   focus-site champions (whose organizer scores are known) and see which ordering matches the ledger.
   If neither does, the promotion gate is measuring the wrong thing.
2. **Sparse-blind holdout.** The endorsed file has never been through `evaluate_holdout.py`; until it has,
   "PROMOTE" rests on format + uniqueness only. (Slot budget: this is an offline measurement, not a submission.)
3. **Collar-aware re-emission** of the amplitude surface at the 37,654 budget, the one configuration whose
   off-catalogue CI does not exclude the parent — the only live path to a positive gate result this session.
