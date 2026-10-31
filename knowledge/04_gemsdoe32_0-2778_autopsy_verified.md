# GEMSDOE32 reported 0.2778: saved-byte autopsy and limits (reviewed 2026-10-31)

> **Decision:** 0.2778 is **USER-REPORTED / UNVERIFIED** in this repository. No organizer receipt binds the score to the pinned TIF. This document distinguishes saved-byte measurements from plausible explanations; it does not establish why the competition score occurred or predict a higher score. Current decision: [review run card](../evidence/review_run_card_20261031.json) — **no candidate cleared**.

## Verified saved-byte relationships

The pinned input records in [`docs/data/audit.json`](../docs/data/audit.json) and [`evidence/focus_pairwise_matrix_20261030.json`](../evidence/focus_pairwise_matrix_20261030.json) report:

- GEMSDOE32 has 37,654 positive pixels; GEMSDOE25 has 44,090.
- In the local audit, GEMSDOE32's positive mask equals GEMSDOE25's mask after removing the 6,436 dots within 2 pixels of the bridge catalogue. GEMSDOE31 is another catalogue-distance prune from the same family.
- GEMSDOE25 and GEMSDOE30 positive masks are pixel-identical in the saved pairwise matrix.
- Focus-site scores copied into the audit are user-provided, not organizer receipts. The measured raster relationships do not prove that scores resulted from the pruning operation or even that the score was attached to those exact bytes.

These records support the description “highly related variants of a sparse, binary, catalogue-distance-filtered raster family.” They do not support “nine independent models.”

## Why pruning could help—and why it is not a proved cause

The official [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) states that experts identified test faults absent from the public USGS database. It specifies the distance-weighted Tversky index with α = 0.2, β = 0.8, and a triangular 300 m kernel. Consequently, removing predictions close to mapped faults could reduce weighted false-positive contribution if those predictions have low probability of matching the hidden expert-labelled faults.

That is only a conditional mechanism. Close mapped-fault neighborhoods can contain unmapped splays, stepovers, misalignment, and mapping gaps. The DTI is non-additive in individual predicted cells: each ground-truth fault pixel uses a maximum confidence-distance contribution, and changes to predictions may alter weighted true positives, false negatives, and false positives. Therefore, the informal argument “every nearby dot is a guaranteed false positive worth 0.2” is not valid without hidden truth and the exact evaluator.

**Best explanation supported today:** the highest reported focus value is associated with the sparsest/most strongly pruned member of a highly similar family. This is a descriptive association and a plausible metric trade-off, not a measured precision gain, geologic discovery, or causal autopsy.

## Can this repo estimate a score higher than 0.2778?

**No reliable estimate is available.** The earlier 0.29 estimate in `evidence/score_estimate.json` extrapolated a three-point user-reported family relationship and has been withdrawn from the live site. The full competition target is newly expert-labelled faults, whereas local labelled holdouts use already mapped features; these populations are not interchangeable without calibration. No organizer receipt, authenticated hidden labels, valid shared-template holdout, or validated transfer model exists in the current checkout.

The official competition page also describes a later expert review and rescore against expanded labels. Thus a submission is not merely a leaderboard-optimized raster; a defensible fault hypothesis matters. A score above 0.2778 is possible in principle, but this repository cannot currently predict that it will happen.

## Findings that block promotion

1. The literal lane threshold is over 70% of dots within 3 px of any registry raster or rank-correlation over 0.90. The pinned dense r13 lattice overlaps the focus family at about 99.9% (see [lattice receipt](../evidence/lattice_gate_recheck_20261030.json)). The protocol contains no calibration-probe exception, so no exception is assumed.
2. The shared evaluator probe records correctness failures in false-negative duplicate detection and false-positive accounting (`docs/data/upstream-check.json`). `scripts/evaluate_holdout.py` is intentionally fail-closed. Do not use a local fork to claim promotion.
3. Feature-cache metadata exists, but its `.npy` arrays are absent in this checkout; its source is described as a third-party bridge, not organizer-authenticated data.
4. The DrivenData data page redirects to login in this environment. The failed upload bytes and portal receipt are also absent, so the reported `[0, 1]` error cannot be attributed to any specific file encoding.

## Future tests (not run)

- Test a geologically distinct hypothesis (ranked in [the 2026-10-31 review](../research/2026-10-31-repo-review.md)) only after restoring the upstream evaluator, cache, and assigned lane.
- Hide complete fault segments with spatial buffers, derive catalogue-based features from visible faults only, mask them pixel-exactly, and report pooled HOLDOUT-DTI with evaluator version, number of withheld positive pixels, and 95% CI.
- Run single-feature leakage canaries first; AUC > 0.90 is a stop condition pending explanation.
- Compare pre-placement surfaces and final dots to the complete registry. Stop at the literal threshold; do not game a dense lattice by pushing predictions to the footprint edge.
- A model score estimate is permitted only after an independent benchmark can be calibrated against organizer feedback. Until then write **NOT ESTIMABLE**, not a number.
