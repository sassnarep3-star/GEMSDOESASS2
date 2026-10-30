# Geological hypotheses — ranked, 2026-10-30 session

> **Post-merge reconciliation (2026-10-30, after PR #27/#28 landed).** A parallel session's
> hypothesis register (README §5) reports: magnetic tilt-derivative **tested negative**
> (ridge alone 0.0396 vs 0.0489 uniform) and radiometric Th/K point values **tested negative**
> (point AUC 0.44–0.48, `evidence/exp1_halo_geometry.json` + register). The H2/H3 rows below
> are therefore superseded in their *point-value* forms; the **edge-concordance** variant of H1
> (Th/K corridor edges requiring a second structural edge) is not covered by that test and
> remains untried but is demoted accordingly. The register's H4 (2-m probe temperature residual
> kriging, INGENIOUS shallow-temperature archive — public and unused) is the strongest remaining
> lead and now outranks everything below. Use this file for mechanisms and data-source
> verification; use the README register for tested status.

Status of every hypothesis below: **UNTESTED** (see reconciliation above where this differs). None is a score, a projection, or a claim of
superiority. Each entry names the layer(s), the physical signature, why it should catch a fault
missing from the USGS/INGENIOUS catalogue, how it differs from anything in this repository, the
non-fault mimic, the data source with an official link, and the cost. Ranking is by expected
HOLDOUT-DTI improvement per unit cost; the ranking is a judgement, not a measurement.

Baseline for comparison: the current best local candidate (SPARSE-BLIND-CONDUIT, 22,163 dots) has
no HOLDOUT-DTI at all, so "improvement" is against *no validated local baseline*; the first
candidate that produces a defensible holdout number wins by default.

---

## H1 · RADIOMETRIC ALTERATION HALO (Th/K + eU edge concordance) — rank 1

- **Layers:** GeoDAWN airborne radiometric grids — potassium (K), equivalent thorium (eTh),
  equivalent uranium (eU), plus total counts — from the USGS data release (DOI
  [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ), item
  [657e1d85d34e23d3533209f7](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7)).
  The release ships GeoTIFF exports of the geophysical grids (verified in the item summary,
  2026-10-30). The release bounding box (−120.0024…−116.1415 E, 37.3641…40.7247 N) contains
  **99.94% of the competition footprint's cell centres** (measured: 5,164,015 of 5,167,373;
  receipt to be produced by the H1 experiment). This is a bounding-box test only — the survey
  polygon outlines inside the release must still be checked before assuming full coverage.
- **Physical signature:** Hydrothermal fluid pathways alter wall rock: K-metasomatism (K
  enrichment) and, where leached, Th enrichment relative to K. Target the *edge* of the Th/K
  ratio and the eU/Th ratio along lineaments, not the raw grids. Alteration halos are broader
  than the permeable structure itself, so the signature is a corridor, not a trace.
- **Why it catches faults the catalogue misses:** USGS QFaults/INGENIOUS mapping is
  scarp-dependent. Blind upflow zones (no Quaternary scarp) still alter their wall rock, so a
  radiometric corridor with no mapped scarp is exactly the missing-fault class the hidden test
  truth is drawn from ("new faults not in the USGS database", problem description).
- **Difference from this repository:** The restored 19-band competition feature stack
  (`evidence/feature_cache.json`) contains magnetics, gravity, geodesy, earthquake density,
  conductivity and detrended elevation — **no radiometric channel of any kind**. The problem
  page's provided-features list is the same 19 bands. The competition shows a radiometric
  figure in its own problem description but does not provide the radiometrics in
  `training_features.tif`, so this information is available to anyone who fetches GeoDAWN and
  is absent from the obvious feature stack. **Irregularity:** `REVIEW_NOTES.md` claims
  radiometric layers are "already used in this lane"; the band list contradicts that. Flagged
  in `IRREGULARITIES.md`.
- **Non-fault mimic:** Lithologic contacts, ash-fall gradients, playa shoreline reworking and
  road/base-camp construction materials produce K/Th contrasts with no fault. Mitigation:
  require concurrence with a second independent structural edge (magnetic tilt `tc` band 6 or
  gravity HG band 18) before emitting.
- **Data source (free, official, verified reachable 2026-10-30):** USGS ScienceBase GeoDAWN
  release, https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7. Download is by
  ScienceBase file URL; the item lists per-file MD5 checksums. GEMS Prize rules allow external
  data with a compatible licence; USGS data releases are public domain.
- **Cost:** medium–high. Grids are large (hundreds of MB zipped), need reprojection to
  EPSG:32611/100 m and ratio/edge transforms. 1–2 sessions.

## H2 · DTI-OPTIMAL SOFT EMISSION (probabilistic raster, no dot placement) — rank 2

- **Layers:** the existing 19-band stack plus the public catalogue geometry (`labels.tif`).
- **Physical signature:** none new; the change is the *output form*. The official DTI formula
  rewards soft confidence: `TP_w = Σ_g max_x p(x)k(d(x,g))` is maximised by placing graded
  probability mass around likely fault locations, and `FN_w` is charged per ground-truth pixel
  against the best-matching prediction. Every raster this project has produced is binary
  {0,1}; the official reference notebook emits `sigmoid` probabilities and comments "it may be
  advantageous to threshold this map for better scoring" (notebook cell 17,
  [aebe92f](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb)).
  A calibrated soft raster (e.g. `p = exp(-d/λ)` ridged by feature-space similarity) covers
  misaligned ground truth without paying the full FP cost that a same-size dot field pays.
- **Why uncatalogued faults benefit:** the hidden truth is *misaligned* from the public
  catalogue (problem description: "portions of the existing fault data may be misaligned from
  the true location"). Soft corridors spanning ±300 m absorb rasterisation and misalignment
  error that dot submissions lose to `FN_w`.
- **Difference from this repository:** `dti_probabilistic` exists in `src/gems/metric.py`, but
  no generated submission uses continuous values. All downloads are binary.
- **Non-fault mimic:** broad regional gradients (heat-flow provinces) produce diffuse
  low-confidence everywhere, which still pays `α·FP_w = 0.2·FP_w`. Mitigation: cap total
  emitted probability mass; validate emission budget on holdout.
- **Data source:** in-repo; no external data needed.
- **Cost:** low. Testable in one experiment with the existing cache.

## H3 · 1 m LIDAR MICRO-SCARP HIGHPASS (3DEP) — rank 3

- **Layers:** the 1 m DEM list supplied by the competition (`1m_DEM_links.csv`, data page),
  USGS 3DEP lidar; detrended elevation band 12/19 as the regional control.
- **Physical signature:** micro-scarps and lineament offsets below QFaults mapping scale;
  high-pass curvature / openness at 1–3 m, aggregated to the 100 m grid as fraction-of-window
  aligned-edge energy.
- **Why uncatalogued faults:** sub-metre scarps are invisible at the scale the USGS database
  was compiled at; they are the physical expression of recent slip on the faults the hidden
  truth contains.
- **Difference from this repository:** no code here reads the DEM links or a 1 m DEM. Some
  GEMSDOE-family sites used "lidarscarp" rasters (reported 0.1461 and 0.0430) but none paired
  micro-scarp energy with the damage-zone-flank exclusion geometry used here.
- **Non-fault mimic:** fluvial nick points, terrace risers, road cuts, shoreline benches.
  Mitigation: require strike persistence >2 km and cross-check against `tc`/gravity edges.
- **Data source:** competition-provided `1m_DEM_links.csv` (login needed) or USGS 3DEP
  directly (free, https://www.usgs.gov/3d-elevation-program).
- **Cost:** high (DEM volumes), but the download list is official and the links file is
  already enumerated by the competition.

## H4 · DEEP-UPFLOW CONCORDANCE (earthquake-density × conductivity-depth) — rank 4

- **Layers:** bands 16 (`ieq_n100a15` earthquake density), 17 (`cond_surf` conductivity) and
  15 (`depth_to_base_surf`) from the supplied stack.
- **Physical signature:** convective geothermal systems concentrate microseismicity above
  upflow and show conductive (clay-cap) signatures; target the *intersection* of high
  earthquake density and shallow conductive base, offset laterally from the catalogue.
- **Difference from this repository:** the HVFD lane used hydro-features separately; no
  in-repo test of the density×conductivity intersection product on a holdout.
- **Non-fault mimic:** reservoir-induced seismicity, aquifer drawdown, tectonic swarms.
- **Data source:** in-repo; no external data.
- **Cost:** low.

## H5 · HOLOCENE VENT / VOLCANIC-CENTRE PROXIMITY — rank 5

- **Layers:** Smithsonian Global Volcanism Program Holocene centres
  (https://volcano.si.edu/, public domain) or USGS Quaternary volcanic deposits; distance to
  vent ∩ fault-edge concordance.
- **Physical signature:** young magmatic heat sources drive fault-valve behaviour at vent–fault
  intersections (Steamboat Springs, Beowawe, Beowawe-type systems in the Great Basin).
- **Difference from this repository:** nothing here references volcanic centres.
- **Non-fault mimic:** lava-flow edges, cooling joints.
- **Data source:** free official; needs a shapefile harvest and EPSG:32611 reprojection.
- **Cost:** medium.

---

## Preregistered validation plan (before any submission slot)

1. Build a spatially blocked holdout exactly as the shared protocol requires: withhold whole
   fault segments with a buffer, derive every catalogue-derived feature only from visible
   faults, mask visible faults pixel-exactly, score pooled DTI (α 0.2, β 0.8, 300 m triangular
   kernel) with a 95% CI.
2. Leakage canary per feature: AUC > 0.90 on the holdout means leakage until disproved.
3. A candidate must beat the holdout baseline and pass the uniqueness gate **with the literal
   lattice rule resolved** (see `evidence/lattice_gate_recheck_20261030.json` — the rule as
   written is unsatisfiable for interior placements).
4. Budget: 3 experiments or 2 hours, then stop and report, including negative results.
5. No weekly submission slot is spent until a selector step signs off; this environment has no
   DrivenData credentials, so no submission can be made from here anyway.
