# Session record — 2026-10-31 · branch `arena/a8aac5cd-gemsdoesass2`

## What was blocked before, and what unblocked it

Every previous session in this repository ran without the competition feature stack,
because the DrivenData data tab is login-walled. This session restored it from the
hash-pinned public mirrors listed in `registry/data_manifest.json` using `git`
blob-less sparse clones of `github.com` (the only reachable host):

| Restored | Bytes | SHA-256 (verified) |
|---|---|---|
| `training_features.tif` (19 bands, float32, 100 m, EPSG:32611) — reassembled from five parts | 418,912,844 | `4371c82e…c5` |
| 12-band LiDAR scarp features (USGS 3DEP 1 m derived) | 36,943,606 | pinned |
| GeoDAWN radiometrics K/Th/U/TC + extensions Th/K, U/K, U/Th, TMI_up150 | 53,745,895 | pinned |
| 10 m DEM derived topography (9 ch) + chi/ksn (5 ch) | 45,300,427 | pinned |
| GDR 1391 2 m probes, paleo deposits, vents, SGMC faults, TIGER roads | — | pinned |

Assembly commands: `scripts/build_cube.py` (→ `.cache/work/cube.f32`, 58 bands),
`scripts/build_catalogues.py`, `scripts/build_proxy_split.py`,
`scripts/fetch_registry_rasters.py` (9 SHA-pinned champions, all hash-match),
`scripts/fetch_score_anchors.py` (31 of 36 default-branch anchors).

## Findings

### F1 — The metric collapses to a three-term form
`TP_w + FN_w = |G|` exactly, so
**DTI = TP_w / (0.2·TP_w + 0.2·FP_w + 0.8·|G|)**.
Consequences used in the build: the FP bill is driven by emitted *mass* Σp, not pixel
count; a pixel on a thin trace earns credit from ~5 truth pixels; the marginal
emission rule is *emit at x iff k(d(x,G)) > 0.2·DTI* (≈283 m at DTI 0.28).

### F2 — The champion is genuinely informed (positive result)
Independent gradient-boosted lineament model (56 bands + 12 structure-tensor fields,
spatially blocked out-of-fold AUC **0.6975**, in-sample 0.9137). Mean model
probability at the champion's 37,654 dots = **0.2563** vs **0.1424** for random
footprint cells → **1.799× enrichment**. The reported 0.2778 is not a lucky lattice.

### F3 — No proxy truth predicts the leaderboard (negative result, the headline)
40 owner-scored rasters (9 SHA-pinned + 31 HEAD anchors, 0.0107–0.2778) scored
against three measurable catalogue-disjoint fault sets:

| Proxy | Cells | Spearman vs reported | p | LOO R² |
|---|---|---|---|---|
| SGMC faults ≥200 m outside the catalogue | 62,649 | 0.169 | 0.296 | −0.122 |
| SGMC faults ≥100 m outside | 68,641 | 0.182 | 0.262 | −0.116 |
| all SGMC faults | 82,151 | 0.211 | 0.191 | −0.083 |
| the competition label raster | 60,988 | 0.198 | 0.222 | −0.061 |
| dot count (control) | — | 0.026 | 0.876 | −0.386 |

Every leave-one-out R² is negative: no proxy beats predicting the mean. Receipt
`evidence/proxy_calibration.json`.

### F4 — The competition labels already cover the Quaternary catalogue
The INGENIOUS/USGS Quaternary trace database rasterises to **79,318** cells inside
the footprint; `labels.tif` holds **60,988**; their intersection is **58,303**
(recall 0.956). Of the 21,015 cells in the database but not in the labels, only **6**
survive a 1-px buffer — they are rasterisation slivers of the same traces. So there is
no hidden pool of catalogued Quaternary faults to hold out.
⚠️ **This contradicts the previous session's claim** that the complete database holds
156,418 cells and that 95,452 mapped fault cells are missing from the bridge copy.
That number is not reproducible here; it is logged as **IR-31-03** and the
"0.00 % against a 156,418-cell catalogue" claim on the previous promoted file is
withdrawn pending re-measurement.
The one genuinely disjoint fault set is **USGS SGMC geologic-map faults**: 82,151
cells, only 3,718 (4.5 %) of which are in `labels.tif`.

### F5 — The candidate loses on the proxy
At the champion's exact emitted mass (37,654), best model-driven emission scores
`P_SGMC2` **0.08138** vs the champion's **0.094686** (−14.05 %), `P_SGMC0` 0.06588 vs
0.088005 (−25.14 %), and beats it on catalogue-DTI (0.0000 vs 0.006709).

### F6 — α was a no-op (design flaw, disclosed)
The sweep varied an "enrichment exponent" α ∈ {0, 0.5, 1, 2}. Under top-K selection
p^α is monotone in p, so every α ≥ 0.5 returned an identical cell set. The
pre-registered argmax (`a0.0_sep6_c3`, 0.082206) is therefore an arbitrary scan-order
selection, not a model-driven placement. `a1.0_sep3_c2` (0.08138, 1.0 % behind) was
shipped instead. **IR-31-02**.

### F7 — Shared-tool fix
`scripts/validate_tif.py` scored `strict_local_format_pass = all(checks.values())`,
but `whole_array_finite_in_0_1` and `outside_masked_or_nan` are mutually exclusive for
any file with values outside the footprint, so the check could never pass. Fixed to
require the structural checks + the inside-footprint range check + **one** of the two
outside-bounds encodings, and a new `portal_range_safe` flag marks the file that
cannot trigger "Predicted values must be in range [0, 1]". **IR-31-01**.

## Artifact
`docs/downloads/gemsass2-hcorr-lineament-offcat-37654-20261031T000000Z-{zeros,nan}.{tif,zip}`
Run card `evidence/run_card_20261031.json`. Verdict **promote-with-caveat**,
MODEL ESTIMATE 0.23 (range 0.18–0.28), from E1 0.2777 / E2 0.2388 / E3 0.1823.
