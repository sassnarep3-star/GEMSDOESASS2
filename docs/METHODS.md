# Methods and Automated Gates

## CDCC-01: cross-domain contact concordance

**Hypothesis.** An uncatalogued fault can occur at a co-located magnetic and
radiometric boundary even when it lacks a mapped surface trace.

**Static layers used in the research rerun.**

- GeoDAWN extensions band 4: peer manifest names it `TMI_up150`.
- GeoDAWN radiometric band 3: peer manifest names it `U/Th`.

The peer cache encodes quantized ranks (not original physical units), so this is
only a research rerun. It must not be interpreted as a direct reanalysis of the
original USGS assets.

**Surface construction.** On jointly valid finite/positive sensor pixels:

1. Gaussian-smooth each uint8 rank layer with σ = 0.8 pixel.
2. Calculate gradient magnitude.
3. Normalize each edge-energy map using its 5th and 99.5th percentiles.
4. Fuse with the geometric mean: `sqrt(magnetic_edge × radiometric_edge)`.
5. Set unsupported pixels to zero.

No label, known-fault catalogue, registry raster, historical dot pattern, or
leaderboard score is passed to steps 1–4. The final public-catalogue mask is
used only for output eligibility.

## Holdout protocol

The checked result is explicitly **HOLDOUT-DTI**, not an organizer score.

1. Convert the public known-fault proxy raster to 8-connected components.
2. Assign each complete component to one of four broad spatial quadrants by
   component centroid. A component is never split across train/test.
3. For each fold, hide all components assigned to that quadrant. Dilate the
   hidden segment by 3 pixels before defining the visible catalogue, so no
   nearby visible catalogue segment can be used in a catalogue-derived step.
4. Because CDCC is static and label-free, the sole catalogue operation is
   pixel-exact masking of visible faults before selecting dots.
5. Select 37,654 positive 3×3 local maxima per fold with stable row-major
   tie-breaking; do not fill a shortfall with zeros.
6. Pool false-positive/false-negative/true-positive components across blocks,
   then calculate DTI once. Bootstrap complete spatial blocks 2,000 times for
   a 95% interval.

### Local DTI implementation

For prediction probability `p`, truth `g`, and distance `d` in pixels, the
triangular credit is:

```text
k(d) = max(1 - d / 3, 0)
DTI = TP_w / (TP_w + 0.2 * FP_w + 0.8 * FN_w)
```

The 3-pixel radius is derived from 300 m / 100 m only after the local template
validates the pixel size. The code supports soft probabilities, but CDCC emits
binary `{0, 1}` dots.

## Leakage canary

Every source/transformed feature is scored by a deterministic balanced
rank-based ROC-AUC against each withheld spatial fold. A max AUC greater than
0.90 is a hard failure. The canary is a leak diagnostic—not a performance
metric and not proof a signal is geological.

## Novelty protocol

The checked [focus registry](../registry/focus_registry.json) contains nine
public peer artifacts pinned by Git commit, Git blob SHA, and file SHA-256.

1. **Before placement:** calculate `abs(Spearman rho)` from the CDCC surface to
   each raster. Continuous-vs-binary comparisons use a deterministic 250,000
   cell sample because the full footprint has over five million cells.
2. **After placement:** calculate directed candidate-dot overlap. A candidate
   fails if more than 70% of its dots lie within Euclidean 3 pixels of any
   peer's dots.

A pass is only “unique against these nine immutable pins,” never proof of
uniqueness against all past or future competition submissions.

## Portal-safe writer

The local template is used only for shape, CRS, affine geotransform, and finite
footprint. The writer rejects invalid values rather than clipping them silently,
then writes `float32` with **finite zero** outside the footprint. The validator
requires all cells to be finite and in `[0,1]`, plus one band and exact grid
identity. This intentionally avoids the observed portal message:

> Predicted values must be in range [0, 1]

Format validation only says the local writer produced a conservative-compatible
file; DrivenData remains the authoritative acceptance system.

## Run-card policy

Every experimental output includes the following required fields:

- hypothesis and mechanism;
- a named non-fault mimicking process;
- HOLDOUT-DTI evaluator/version, withheld positives, and 95% CI;
- surface and final-dot registry evidence;
- raster SHA-256;
- strict validator output;
- a filename and ≤140-character note; and
- a fail-closed `promote`/`negative` verdict.

The [CDCC-01 run card](data/cdcc_20261027_run_card.json) is the authoritative
machine-readable result for this checkout.
