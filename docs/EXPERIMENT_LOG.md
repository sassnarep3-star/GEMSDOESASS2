# Experiment Log

## E01 — CDCC-01 (completed; negative)

- **Lane:** cross-domain GeoDAWN contact concordance. The static surface uses
  no catalogue, labels, peer rasters, historical dots, or score values.
- **Fixed layers/transform:** peer-mirror `TMI_up150` rank (extensions band 4)
  and `U/Th` rank (radiometric band 3); σ=0.8 gradient energy; 5th–99.5th
  percentile normalization; geometric-mean fusion; 37,654 3×3 local maxima.
- **Scientific mechanism:** a concealed structural boundary can cause a
  co-located magnetic and radiometric contrast.
- **Non-fault confounds:** lithologic contacts, intrusive margins, survey seams,
  processing seams, and alteration fronts.
- **Source warning:** the source is hash-pinned public peer mirror data, not
  organizer-authenticated or raw USGS assets. Its sample template equals its
  public label proxy, which blocks promotion.
- **Canary:** all standalone feature AUC values were ≤0.90; maximum 0.65403.
- **Surface novelty:** pass against nine pins; maximum absolute rank correlation
  0.01702.
- **Final-dot novelty:** pass against nine pins; max directed 3-pixel overlap
  24.52%.
- **HOLDOUT-DTI:** `0.05211`, 95% CI `[0.02315, 0.08277]`, evaluator
  `gemsdoesass2-segment-pooled-v1`, 60,988 withheld public-catalogue proxy
  positives. The paired delta versus the best feature-alone radiometric control
  is `+0.02034`, CI `[-0.00983, +0.05019]`.
- **Format:** strict portal-safe writer/validator pass; all output values are
  finite in `[0,1]`.
- **Weekly slots spent:** 0.
- **Verdict:** `negative`; **DO NOT SUBMIT**.
- **Reproducibility check:** A fresh download from the pinned GitHub blob manifest
  reproduced the GeoTIFF byte-for-byte: SHA-256
  `e3e797424e2ac3dc1f1be1106d549c88fd3382eea75f13b8398cce1768494b19`.

The complete immutable result is
[`data/cdcc_20261027_run_card.json`](data/cdcc_20261027_run_card.json).

## Next experiment

**None is authorized yet.** The candidate queue is documented in
[`HYPOTHESES.md`](HYPOTHESES.md). The next session must first obtain authorized
competition data, verify source hashes/provenance, and preregister one distinct
lane before consuming experiment 2 of 3.
