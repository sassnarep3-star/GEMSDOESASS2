# New geological hypotheses — 2026-10-31 (pre-implementation ranking)

Protocol rules observed: LANE (≤ 70 % of dots within 3 px of any one registry raster; |Spearman| ≤ 0.90), REUSE (shared holdout stack, submission_writer, 13-check validator), LABEL EVERY NUMBER (HOLDOUT-DTI or MODEL ESTIMATE — never organizer score), LEAKAGE CANARY (single-feature AUC ≤ 0.90), RUN CARD (one JSON per experiment), BUDGET (stop after 3 experiments or 2 hours).

Layers available locally WITHOUT login: `data/bridge/sample_submission.tif` (footprint), `data/bridge/labels.tif` (bridge catalogue, 60,988 cells), `data/bridge/existing_faults.tif`. No GeoDAWN rasters, no LiDAR stack, no INGENIOUS tables are present locally. Anything needing them is flagged below with the specific free official source.

## Candidates not yet tried in this repo

Tried already (README §5): H1 strain+ridge (holdout 0.2244, promoted), H2 magnetic tilt-derivative zero-convergence (negative), H3 radiometric Th/K point values (negative, AUC 0.44–0.48), H4 2-m probe temperature residual kriging (untried, public, unused), H5 19-band strain-tensor tip dilation (untried, login-gated).

### H_STEPOVER — catalogue segment tip step-over / relay-ramp dilation (TOP CANDIDATE — implement first)

- **Layers:** USGS Quaternary Faults + GBCGE INGENIOUS catalogue trace geometry only — derivable from `labels.tif` alone. No external download required. Obtainability check: N/A (already local).
- **Physical signature:** extensional step-over / relay-ramp dilation between the tips of en-echelon normal-fault segments. Signature = intersection-of-disks lens around tip-pairs separated by 3–25 px (300 m–2.5 km): pixels within `dist(tip_a) + dist(tip_b) ≤ separation + 4 px`. Dilatation opens the permeability pathway that feeds blind hydrothermal upflow; the connecting strand has no continuous Quaternary surface scarp.
- **Why it catches catalogue-missing faults:** USGS QFaults / INGENIOUS map the two main strands but not the short blind connector between them. The connector vents heat but carries no mappable Quaternary offset, so it is absent from the catalogue — exactly the target class (blind faults).
- **How it differs from repo implementations:** every focus site and every repo candidate (XGHF, HVFD, ALTEDGE, STRAIN-RIDGE, VRC, sparse-blind) places dots uniformly or by distance-to-catalogue over the whole footprint. None uses tip-to-tip relay geometry derived from segment endpoints.
- **Implementation cost:** LOW — labels.tif only; tip detection via 8-connectivity, KDTree nearest-tip pairing, local-box lens rasterisation, greedy weighted placement; runs in minutes.
- **Expected DTI improvement:** MODERATE over uniform-lattice control at the same dot budget; relay zones are classic blind-strand locations, so per-dot yield should exceed a uniform lattice.

### H_CURVATURE — mapped-trace curvature splays

- **Layers:** catalogue trace geometry only (`labels.tif`).
- **Physical signature:** curvature transform of trace centerlines — high-curvature bends (releasing/restraining bends) computed as the Laplacian of the trace centreline or the rate of change of trace orientation along itself. Edge/curvature transform, not distance-to-catalogue.
- **Why it catches catalogue-missing faults:** bends on normal faults generate secondary off-trace splays and step-over fractures that are not separately mapped; blind splays vent without a continuous scarp.
- **How it differs:** no repo candidate uses trace curvature; all use uniform/distance-to-catalogue geographies.
- **Implementation cost:** LOW — centreline extraction + curvature along traces; labels.tif only.
- **Expected DTI improvement:** LOW–MODERATE. Curvature is a weaker, noisier signal than step-over dilation.

### H_INTERSEGMENT — inter-segment strain-transfer corridors

- **Layers:** catalogue trace geometry only (`labels.tif`).
- **Physical signature:** medial-axis / distance-transform ridges inside wide inter-segment gaps — pixels whose nearest catalogue cell is far (gap interior) but which sit between two segments whose ends face each other (strain must transfer across the gap). Essentially distance-to-catalogue ridges gated to segment-facing gaps.
- **Why it catches catalogue-missing faults:** strain crossing a wide gap between mapped segments localizes on unmapped structures in the corridor centre; catalogues trace segments, not the transfer structures between them.
- **How it differs:** plain distance-to-catalogue (used by every focus site) avoids the catalogue; this targets the *gaps between facing segment ends* specifically.
- **Implementation cost:** LOW — labels.tif only.
- **Expected DTI improvement:** LOW–MODERATE; gap centres are diffuse targets.

### H_TEMP — INGENIOUS 2-m temperature probe residual kriging (untried lead — needs external data)

- **Layers:** INGENIOUS shallow temperature archive (544 wells/springs, gbcge.org/current-projects/ingenious/) + 100 m DEM trend.
- **Physical signature:** kriged residual temperature anomaly (observed 2 m temperature minus elevation trend), a smooth >2 km halo over blind hydrothermal conduits. Thermal, not structural.
- **Why it catches catalogue-missing faults:** blind faults vent heat with no Quaternary scarp; temperature anomalies see the conduit where the catalogue sees nothing. Completely independent physical mechanism from H1–H3 (which were negative).
- **How it differs:** no repo candidate uses thermal data; H3 (radiometric point values) was negative, but a kriged 2-m residual is a different measurement.
- **Implementation cost:** MEDIUM — need to download and verify the INGENIOUS temperature table is public and obtainable before this is viable. Specific source: https://gbcge.org/current-projects/ingenious/ (INGENIOUS regional data: geodetic strain rate, earthquake rate density, wells/springs).
- **Expected DTI improvement:** HIGH if obtainable (novel mechanism); otherwise not viable.

### H_STRAIN_TIP — 19-band strain tensor tip-stepover dilation (parked)

- **Layers:** login-gated 19-band strain tensor (`training_features.tif` / DrivenData, requires auth). Not obtainable in this environment.
- **Cost:** HIGH — blocked by DrivenData login. Not proposed for this session.

## Ranking (expected DTI improvement × implementation cost)

| Rank | Hypothesis | Layers | Cost | Expected DTI vs uniform control | Verdict for this session |
|------|------------|--------|------|----------------------------------|--------------------------|
| 1 | H_STEPOVER step-over/relay-ramp dilation | catalogue only | LOW | MODERATE | **IMPLEMENT & VALIDATE ON HOLDOUT** |
| 2 | H_CURVATURE trace-curvature splays | catalogue only | LOW | LOW–MODERATE | holdout if H1 slot remains |
| 3 | H_INTERSEGMENT strain-transfer corridors | catalogue only | LOW | LOW–MODERATE | holdout if slots remain |
| 4 | H_TEMP 2-m temperature residual kriging | INGENIOUS probes (public, must verify obtainable) | MEDIUM | HIGH | validate obtainability first |
| 5 | H_STRAIN_TIP strain tensor tip dilation | 19-band strain tensor (login-gated) | HIGH | UNKNOWN | parked |

## Holdout validation plan (top candidate H_STEPOVER)

Run `src/gems/holdout.run_holdout(make_dots, labels, footprint)`:
- `make_dots(visible)` rebuilds the step-over surface from VISIBLE faults only, places dots at B=2 (>200 m) from visible faults with 3 px min separation, budget 22,163 dots (below the 22,164 first-failing lattice count → literal lane rule passes arithmetically).
- Pooled DTI (alpha 0.2, beta 0.8, 300 m triangular) against withheld segments; cluster bootstrap 95% CI over withheld components.
- Leakage canary: single-feature AUC of the step-over surface vs withheld truth — must be ≤ 0.90.
- Then: 13-check format validator, uniqueness gate vs local registry, run card + audit JSON. No weekly slot spent until the holdout beats the matched uniform control.
