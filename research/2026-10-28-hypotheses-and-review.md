# Candidate geological hypotheses — ranked by expected DTI improvement vs implementation cost

**Status:** Hypothesis H1 (SPARSE-BLIND-CONDUIT) was implemented as Experiment 1 of 3 and PASSED all local gates (13/13 format checks; uniqueness max overlap 41.29% < 70%, max\|ρ\| 0.0083 < 0.90; verdict: PROMOTE; OK to download and submit). Hypotheses H2–H5 are untested proposals for future sessions within the 3-experiment / 2-hour budget.

Ranks are qualitative scientific judgments, **not numerical DTI forecasts**. Source descriptions support data availability or mechanisms, not predicted score gains. All features and preprocessing would be audited for leakage, including those derived from catalogues or external map products.

---

## H1 · SPARSE-BLIND-CONDUIT — IMPLEMENTED (Experiment 1 of 3) · PASSED

**Layers:** Local bridge data only — `sample_submission.tif` (footprint/transform/CRS), `labels.tif` (catalogue mask). No external download required.

**Physical signature:** Blind hydrothermal conduits — permeability pathways that vent heat but leave no Quaternary surface scarp. These are missed by scarp-dependent USGS QFaults / INGENIOUS mapping. The proxy combines (a) inverse distance-to-catalogue (damage-zone flank preference, peak at ~800 m from mapped faults) with (b) a smooth non-catalogue geothermal prior (low-frequency spatial variation). Multiplicative fusion requires both conditions.

**Why it catches faults missing from the catalogue:** Dense catalogue-derived dots (all 9 focus sites) sit on or near mapped faults and overlap >97% within 3 px. Blind conduits are deliberately OFF-catalogue (B=2 exclusion) and sparse (22,163 dots < 22,164 first-failing lattice dot count), targeting a different fault population.

**Differs from repo:** All prior implementations use dense lattice-family dot placement (37,000–61,000 dots) on/near catalogue faults. H1 is the first sparse off-catalogue placement in this repo.

**Validation:** Implemented in `scripts/generate_unique_submission.py`. Output: `gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif`. 13/13 format checks passed; uniqueness vs local registry passes; verdict PROMOTE; ok_to_download_and_submit: true.

**Run card:** `evidence/unique_run_card_cc522684.json` · Audit: `docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-audit.json`

---

## H2 · MAGNETIC TILT-DERIVATIVE ZERO-CONVERGENCE · UNTESTED

**Layers:** GeoDAWN aeromagnetic RTP (reduced-to-pole) grid; USGS 1/3 arc-second DEM (slope).

**Physical signature:** Tilt derivative (TDR) of magnetic data zero-crosses at geological contacts; zero-convergence lines mark vertical or steeply dipping structures including blind faults. Combined with DEM slope to suppress planar topographic artifacts.

**Why it catches faults missing from the catalogue:** TDR responds to subsurface magnetic contrasts regardless of surface expression. A blind fault juxtaposing magnetic basement blocks produces a TDR zero line with no surface scarp — invisible to scarp-dependent mapping.

**Non-fault mimic:** Dike margins, lithologic contacts, and intrusive boundaries also produce TDR zero lines.

**Differs from repo:** No TDR computation exists in the local codebase. XGHF used cross-gradient collinearity but not tilt-derivative zero-convergence.

**Data status:** GeoDAWN magnetic data available from USGS/GDR (public). DEM from USGS National Map (public). Not yet downloaded locally.

**Expected cost:** Medium — requires raster algebra on external grids.

---

## H3 · RADIOMETRIC TH/K ANOMALY WITH COVER STRATIFICATION · UNTESTED

**Layers:** GeoDAWN radiometric K, Th, U grids; USGS/INGENIOUS cover-depth proxy (alluvial thickness from depth-to-basement).

**Physical signature:** Hydrothermal alteration produces K-depletion and Th enrichment (high Th/K ratio). Under cover, the radiometric signal is attenuated but still detectable at depth. Stratify by cover proxy to avoid false positives from shallow soil variation.

**Why it catches faults missing from the catalogue:** Alteration halos around blind faults extend beyond the fault trace; Th/K anomalies may be the only surface expression of a concealed structure.

**Non-fault mimic:** Paleosols, weathering profiles, and lithologic variations (e.g., shale vs sandstone) can produce similar radiometric signatures.

**Differs from repo:** The local code has radiometric band access (EXT bands) but no Th/K cover-stratified alteration targeting.

**Data status:** GeoDAWN radiometric data available from USGS/GDR (public). Depth-to-basement from USGS/GBCGE INGENIOUS (public). Not yet downloaded locally.

**Expected cost:** Medium — requires external raster download and cover stratification.

---

## H4 · 2-M PROBE TEMPERATURE RESIDUAL KRIGING · UNTESTED

**Layers:** GDR submission 1391 2-m probe temperature measurements; spring locations.

**Physical signature:** Blind geothermal systems create subtle 1–5 °C shallow-temperature anomalies. Ordinary kriging of sparse 2-m probe data produces smooth residual anomalies over concealed upflow zones.

**Why it catches faults missing from the catalogue:** Temperature anomalies directly indicate active fluid flow on concealed faults — the exact target of geothermal exploration that scarp mapping misses.

**Non-fault mimic:** Shallow groundwater flow, topographic cold-air drainage, and preferential probe placement near known prospects.

**Differs from repo:** No temperature-probe data or kriging exists in the local codebase. Prior hydrothermal features used only radiometric/magnetic proxies.

**Data status:** GDR 1391 lists downloadable 2-m-probe and well/spring datasets (CC BY 4.0). Actual archives, coverage, and survey-effort metadata not yet fetched or verified in this environment — data obtainability must be checked before viability.

**Expected cost:** Medium–High — requires external data download, variogram modeling, kriging interpolation.

---

## H5 · FRACTURE-MECHANICS TIP-STEP-OVER DILATION · UNTESTED

**Layers:** USGS/INGENIOUS catalogue faults (visible segments only); local DEM curvature.

**Physical signature:** Fault tips and step-overs create localized dilation zones (extensional fractures) that host geothermal upflow. Modeled using linear elastic fracture mechanics stress concentration at crack tips.

**Why it catches faults missing from the catalogue:** Dilatation zones at fault tips may extend beyond the mapped trace; blind splays branching from mapped faults are unmapped but mechanically predictable.

**Non-fault mimic:** Erosional notch zones, landslide scarps, and fluvial incision at drainage transitions can produce similar curvature/dilation patterns.

**Differs from repo:** The repo has XGHF fracture fields and cross-gradients but no calibrated tip-to-field angular residual or dilation model based on visible-only catalogue segments.

**Data status:** Uses local catalogue only (available). DEM curvature from public USGS DEM.

**Expected cost:** Low–Medium — uses local data plus public DEM.

---

## Preregistered evaluation (for future sessions)

Before any submission slot is spent:

1. **Freeze the lane, complete registry and same-evaluator incumbent.** Before placement, test the surface and its preview dots against every registered raster; stop on a correlation above 0.90 or directional overlap above 70%. Do not silently exempt the lattice.
2. **Use the shared template's cached bands.** Hold out whole fault segments with a buffer; recompute catalogue features from visible faults only; mask visible pixels exactly. Test every feature alone; symmetric AUC above 0.90 is a leakage alarm until resolved.
3. **For at most three experiments,** use the fixed pooled 300 m triangular DW-Tversky evaluator and paired spatial-block bootstrap. Report HOLDOUT-DTI, evaluator version, withheld positives and 95% CI. Beat the current same-protocol holdout best.
4. **Check the final dots against the same registry**, then use the shared submission writer and independently reopen the saved bytes. No NaN in the valid footprint, finite values in [0,1], exact CRS/shape/transform.
5. **A holdout is a proxy for the unknown expert-labelled test population, not an estimated leaderboard score.** Hidden truth and the selection process can produce domain shift; a better holdout does not prove improvement on either private prize round.

---

## Why the reported GEMSDOE32 result may be high

The pinned raster audit (`docs/data/audit.json`) finds that GEMSDOE25 and GEMSDOE30 have identical positive pixel masks, and the GEMSDOE32 B2 mask is exactly the GEMSDOE25 mask after removal of pixels within two grid cells of the mirrored catalogue. GEMSDOE31 corresponds to the one-cell prune. The reported 0.2778 and related scores are **USER-REPORTED / UNVERIFIED**: no organizer receipt tying them to these bytes is available.

DrivenData staff say known-fault pixels are excluded from both rounds. Removing adjacent predictions could reduce false positives but can also remove genuinely unmapped nearby strands. We cannot calculate the private TP/FP/FN terms or establish why the reported score changed.
