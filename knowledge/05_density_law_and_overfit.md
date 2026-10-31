# 05 — The density law, the overfit, and the one band that survived

Session of 2026-10-31. Four experiments, all reproducible from `scripts/`.
Every number below is a **MODEL ESTIMATE** or a **HOLDOUT-DTI** measurement; none is an
organizer score, and no organizer receipt exists anywhere in this ecosystem.

## 0. The measurement problem, stated first

The competition's truth is *faults identified by experts that are not in the public database*.
Nothing in the repository observes that set. Every proxy available has a defect:

| Proxy | Size (in-footprint cells) | Defect |
|---|---|---|
| `data/bridge/labels.tif` (QFaults subset) | 60,988 | it is the label the model was trained on |
| QFaults + INGENIOUS union | 156,418 | 76 % of it is outside `labels.tif`; rasterisation fidelity unverified |
| SGMC-derived compilation | 83,593 (79,615 off-catalogue) | different mapping programme and scale convention |

The SGMC-derived raster is the best analogue because 95.2 % of it is *absent from the
catalogue* — structurally the same definition as the competition target. It is still an
analogue, and every claim below is bounded by that.

## 1. The density law (`evidence/emission_optimum.json`)

The official identity `DTI = T/(0.2T + 0.2F + 0.8|G|)` (from `FN = |G| − T`) can be collapsed
to a one-parameter family for a fixed design. Fitting

```
DTI = C / (0.2 N + 0.8 (G − C))
```

to the nine owner-reported scores gives **C = 10,950** (truth cells recovered) and
**G = 51,734** (implied hidden truth), **R² = 0.903**, max residual **0.0051**.

Residuals: 24 −0.0024, 25 +0.0042, 27 −0.0010, 28 +0.0017, 30 +0.0042, 31 −0.0015,
32 −0.0051, 33 +0.0039, 36 −0.0039.

Read: across this family, the reported score is almost entirely a function of **how many cells
are spent**. `C/N` for the corpus is 0.30, and `C/G` is 0.21 — it recovers a fifth of the truth
while spending ~72 % of its budget on cells that recover nothing. `C` and `G` are *effective
parameters of a fit*, not measurements; the degeneracy between them is real.

## 2. The overfit (`evidence/emission_controls.json`, `evidence/emission_avoidance.json`)

At an identical 250,000-cell budget:

| Arm | Catalogue DTI (in-sample) | Independent DTI |
|---|---|---|
| fitted model, tilt 1.0 | 0.4563 | 0.1814 |
| fitted model, tilt 0.35 | 0.3656 | 0.2298 |
| fitted model + soft collar 0.85 | 0.3662 | 0.2441 |
| space-filling lattice | 0.2663 | 0.2507 |

At 350,000 cells, two seeds each, the same pattern holds: uniform 0.2755 / 0.2752,
hard catalogue avoidance 0.2817 / 0.2845, model + collar 0.2073 / 0.2074.

**The catalogue ranking is the reverse of the independent ranking.** A model fitted to the
catalogue learns the catalogue's specific traces and its corridor context, not a transferable
fault signature. The more its ranking is trusted (tilt 0 → 1), the worse the transfer.
This is the mechanism that also explains why all nine focus sites sit at ~0.10 on SGMC:
they were all selected against the catalogue.

Dilated "ribbons" were also tested and rejected: at 250k, dilation by one pixel multiplies
cells 7.8× for 1.75× coverage, and independent DTI falls from 0.244 to 0.102.

## 3. The band that survived (`evidence/sgmc_transfer_auc.json`, `b19_confound_check.json`)

Single-band AUC for SGMC-off-catalogue faults vs background, all 19 official bands:

| Band | Description | AUC |
|---|---|---|
| 19 | detrended elevation slope | **0.7570** |
| 12 | detrended elevation | 0.7068 |
| 15 | depth to base of conductive surface | 0.6665 (inverted) |
| 13 | isostatic gravity anomaly | 0.6138 |
| all others | — | 0.49–0.57 |

**Confound check:** stratifying by decile of detrended elevation, band 19's AUC falls from 0.84
in low deciles to 0.52 in the highest, positive-weighted mean **0.636**. So roughly half of the
apparent skill is "faults occur in rugged, low-standing ground"; the remainder is genuine
within-terrain discrimination. The design is a terrain-and-slope prior, not a fault detector,
and is documented as such.

## 4. The selected emission (`evidence/feature_tilt_sweep.json`, `final_run_card.json`)

Density ∝ Gaussian-smoothed (σ = 5 px = 500 m) band 19, tilt 1.0, domain = footprint ∩
feature coverage ∩ (not within 1 px of the catalogue):

| n | 200k | 300k | 400k | 500k |
|---|---|---|---|---|
| independent DTI | 0.394 | **0.403** | 0.367 | 0.340 |

Smoothing scale is immaterial (raw 0.3985, σ2 0.4004, σ5 0.4026 at 300k) — a plateau, not a spike.
Chosen: **n = 300,000, tilt = 1.0, σ = 5**, seed 20261031.

Independent-target terms: T = 34,045 of |G| = 62,122 (coverage 0.548), F = 276,409.

## 5. Score estimate, and why it is a range

`c = T/|G| = 0.548`, `F = 276,409`. Sweeping the unobservable `|G|`:

| |G| | 25k | 35k | 51.7k (law) | 62.1k (SGMC) | 120k |
|---|---|---|---|---|---|
| implied DTI | 0.176 | 0.220 | **0.277** | 0.304 | 0.400 |

So the honest statement is: **0.28–0.40, centred ≈ 0.30**, against the incumbent 0.2778.
The law-consistent value is a tie; the proxy value is a 10 % win. Neither is a promised score.

## 6. What would actually break the ceiling

The metric's marginal exchange rate is `ΔT/ΔF > 0.2·DTI/(1 − 0.2·DTI)` ≈ 1 recovered truth
cell per 17 wasted cells at DTI 0.28. Density cannot exploit that because false mass grows
linearly while coverage saturates. Only **coverage per predicted cell** moves the score
materially. At `DTI = 0.45` the leaders must be covering ~29 % of the truth with near-perfect
precision (T ≈ 15,400 at F ≈ 0). The open problem is a feature or model that predicts
independently mapped faults at trace scale — band 19 gets part of the way; the fitted
125-feature model gets none.

## 7. Reproduction

```
.venv/bin/python scripts/estimate_emission_optimum.py     # law + budget sweep + ribbons
.venv/bin/python scripts/emission_controls.py             # uniform / model / collar / sharp
.venv/bin/python scripts/emission_avoidance.py            # catalogue avoidance, two seeds
.venv/bin/python scripts/build_band19_submission.py       # writes the promoted pair
.venv/bin/python scripts/finalize_run_card.py \
    --candidate docs/downloads/gemsass2-slopetilt-300k-20261031-zeros.tif \
    --out evidence/final_run_card.json                    # uniqueness + score sweep + run card
```

Requires `.cache/features/training_features.tif` (official 19-band stack, sha256 `4371c82e…`,
reassembled by `scripts/fetch_training_features.sh`) and `.cache/external/` from
`scripts/fetch_externals.sh`. Both live in `.cache/`, which is excluded from snapshots — rebuild
them at the start of a session.
