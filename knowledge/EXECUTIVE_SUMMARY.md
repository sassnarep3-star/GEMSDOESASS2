# Executive summary — 2026-10-31

**SUBMIT:** `docs/downloads/gemsass2-slopetilt-300k-20261031-zeros.tif`
SHA-256 `af4d17511fd68fd01d742b4eee0c5be0f3569512e50207b940e5bb23b5f41e7f`,
300,000 cells, binary {0,1}, all 12,279,160 values finite, EPSG:32611, 3730 x 3292, 100 m.
Name `GEMSASS2-SLOPETILT-300K-20261031`; note (104 chars)
`density - detrended-elevation-slope prior at the metric optimum; zero cells on the public fault database`.
Format gate 11/11. Uniqueness gate over 12 registry rasters: max 3-px overlap 28.10 %
(limit 70), max |rho| 0.0215 (limit 0.90). MODEL ESTIMATE 0.28-0.40, centred ~0.30,
against the incumbent 0.2778. No organizer score exists.

**What it is.** Emission density proportional to one official band — band 19,
detrended-elevation slope — Gaussian-smoothed at sigma = 5 px (500 m), at the density
optimum of 300,000 cells, with every cell within 100 m of the public fault database removed.
One band, one smoothing scale, one budget. Nothing fitted to the catalogue.

**Why it replaced the previous candidate.** A fitted 125-feature LightGBM scored 0.37 on
the catalogue but 0.192 on an independent fault compilation, worse than a same-size
space-filling lattice (0.295). The previous candidate (band-19-free model + 12 px collar)
scored 0.207-0.244 there. Band 19 alone, unfitted, reaches 0.403.

**The four experiments (all in `evidence/`).**
1. `emission_optimum.json` — the nine-site density law `DTI = C/(0.2N + 0.8(G-C))` fits all
   nine owner-reported scores to within +-0.005 (C = 10,950, G = 51,734, R2 = 0.903); the
   budget peaks near 3e5 cells; dilated "ribbons" are much worse (F grows 8x for 1.75x coverage).
2. `emission_controls.json` — a fitted model loses 7-33 % on an independent compilation and the
   loss grows with tilt (0.2507 uniform -> 0.2298 tilt 0.35 -> 0.1814 tilt 1.0). Overfit.
3. `emission_avoidance.json` — at equal budget, deleting the 100 m collar around known faults is
   the only structure that helps out-of-sample (+2.8 %, both seeds).
4. `sgmc_transfer_auc.json` + `feature_tilt_sweep.json` — band 19 transfers at AUC 0.757
   (highest of 19) and a density on it reaches 0.403 vs 0.295 for uniform.

**Honest caveats.**
- The independent target is an analogue, not the truth: 0.403 is DTI against a different expert
  compilation. The nine-site law applied to this file gives 0.277 — a tie with the incumbent.
- Terrain confound: within deciles of detrended elevation, band 19's AUC falls to a weighted 0.636,
  so part of the gain is "faults sit in rugged, low-standing ground".
- 300k / sigma 5 was selected on the same proxy it is reported on; the plateau is broad
  (200k-300k within 0.01) but the selection is not independent.
- All historical site scores are USER-REPORTED / UNVERIFIED. No organizer receipt exists.
- Three submissions per week; this file consumes one slot and there is no A/B budget.
