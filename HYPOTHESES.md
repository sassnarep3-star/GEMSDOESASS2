# Geological hypotheses — new candidates, 2026-10-31

The live hypothesis register — what was tried, what was measured, and what is still open — is
**README §5** ("Hypothesis register"). This file documents **five new hypotheses not previously
tried in this repository**, ranked by expected HOLDOUT-DTI improvement per unit implementation
cost. None is a score, a projection, or a claim of superiority.

**Testing rule:** a candidate must beat the holdout baseline and pass the uniqueness gate
(with the literal lattice rule resolved — IR-S-01) before any weekly submission slot is spent.
No holdout DTI is computable locally (organizer truth is login-gated), so the first experiment
that produces a defensible holdout number wins by default.

---

## H6 · DAMAGE-ZONE EDGE TARGETING — rank 1 (IMPLEMENTED)

- **Layers:** catalogue geometry only (`labels.tif` / `existing_faults.tif`), both local bridge rasters.
- **Physical signature:** gradient magnitude of the Euclidean distance-to-catalogue field,
  \|∇d(catalogue)\|. This is maximal at damage-zone boundaries — the transition from
  fault-proximal to off-fault material — where blind splays, step-overs and en-echelon strands
  concentrate.
- **Why it catches faults missing from USGS/INGENIOUS:** USGS QFaults maps the principal
  Quaternary trace; blind faults offset from the mapped trace cluster at damage-zone margins
  (near enough to share the stress field, far enough to be absent from the scarp-dependent
  catalogue). The hidden truth is explicitly "new faults not in the USGS database."
- **How it differs from this repo:** cc522684 sparse-blind-conduit used inverse-distance × random
  prior (prefers mid-distance broadly, not edges); strain-ridge used geodetic strain + LiDAR
  ridge prior (external geophysics); the lattice family used catalogue-modulated Poisson disk
  (dense, on/near traces). No previous submission uses \|∇d(catalogue)\| edge maxima.
- **Non-fault mimic:** alluvial-fan toes, terrace risers, paleo-shoreline benches. Mitigated by
  restricting to the damage-zone annulus (200 m–1.5 km) and requiring edge strength.
- **Data source:** local only — no external download required.
- **Cost:** low. Implemented in `scripts/generate_damage_edge_submission.py`.
- **Result:** 22,163 dots, 0 on catalogue, 13/13 format pass, max 3-px overlap 29.84% (limit 70%),
  max |ρ| 0.0181 (limit 0.90). Run card: `evidence/damage_edge_run_card_4eacecbc.json`.
  Download: `docs/downloads/gemsdoesass2-damage-edge-22163-20261031T045913Z-4eacecbc-zeros.tif`.

---

## H7 · DISTANCE-BAND CURVATURE (Laplacian of distance-to-catalogue) — rank 2

- **Layers:** catalogue geometry only (`labels.tif`).
- **Physical signature:** Laplacian (curvature) of the distance-to-catalogue field,
  ∇²d(catalogue). Positive curvature marks local minima of the distance field (fault cores),
  negative curvature marks local maxima (inter-fault basins). Blind faults at damage-zone edges
  sit where curvature changes sign — the "hinge" between fault and off-fault domains.
- **Why it catches faults missing from USGS/INGENIOUS:** curvature sign-change lines trace
  distributed deformation zones, not just the principal mapped trace. Faults in step-over
  belts and relay ramps produce curvature extrema with no surface scarp.
- **How it differs from this repo:** H6 uses the gradient magnitude (first derivative); H7 uses
  the Laplacian (second derivative) — a different physical transform, no overlap in placement
  field. No previous submission uses any second-derivative transform of catalogue distance.
- **Non-fault mimic:** erosional depressions, volcanic cones, alluvial fan apices. Mitigated by
  requiring concurrence with gradient magnitude (H6 edge field).
- **Data source:** local only — no external download required.
- **Cost:** low. One experiment with the existing bridge data.

---

## H8 · EXISTING-FAULTS MINUS LABELS DELTA — rank 3

- **Layers:** `existing_faults.tif` minus `labels.tif` (both local bridge rasters).
- **Physical signature:** pixels present in `existing_faults.tif` but absent from `labels.tif`
  represent faults mapped by one source but not the other — candidate blind or mis-mapped
  traces. Dot placement at these delta pixels, dilated by 1–2 cells.
- **Why it catches faults missing from USGS/INGENIOUS:** if the two rasters differ, the
  difference set is exactly the class of faults one catalogue has and the other lacks — the
  same class the hidden truth is drawn from.
- **How it differs from this repo:** no previous submission compares the two bridge rasters.
  IR-S-05 flags that they are byte-identical (SHA-256 `7ba308cc…4093`) — if confirmed identical,
  this hypothesis is **falsified at zero cost** and should be dropped immediately.
- **Non-fault mimic:** mapping inconsistencies, digitization artifacts. Mitigated by requiring
  spatial coherence (connected components > 5 cells).
- **Data source:** local only — no external download required.
- **Cost:** trivial (raster subtraction). First step: verify whether the two rasters differ.

---

## H9 · 2-M PROBE TEMPERATURE RESIDUAL KRIGING — rank 4

- **Layers:** INGENIOUS shallow temperature archive (2-m probe residuals), public and unused.
- **Physical signature:** convective geothermal upflow leaves a shallow thermal anomaly;
  residual temperature (after regional trend removal) kriged to the 100 m grid marks blind
  upflow zones with no surface expression.
- **Why it catches faults missing from USGS/INGENIOUS:** blind faults host hydrothermal
  convection; the temperature anomaly is the physical expression of the fault, independent of
  scarp mapping. The hidden truth is drawn from faults the catalogue misses — precisely blind
  upflow zones.
- **How it differs from this repo:** H4 in the old register proposed this but was never tested.
  No code in this repo reads the INGENIOUS temperature archive. Completely new physical layer.
- **Non-fault mimic:** shallow groundwater circulation, lithologic conductivity contrasts,
  recent surface disturbance. Mitigated by depth-stratified residuals and requiring coherence
  with strain/earthquake corridors.
- **Data source:** INGENIOUS regional data, https://gbcge.org/current-projects/ingenious/
  (free; needs harvest and EPSG:32611 reprojection).
- **Cost:** medium. Temperature data harvest + kriging + holdout test: 1–2 sessions.

---

## H10 · MAGNETIC TILT-DERIVATIVE ZERO-CONVERGENCE CORRIDORS — rank 5

- **Layers:** GeoDAWN airborne magnetics — RTP TMI, tilt derivative `tc`, upward-continued TMI
  (DOI 10.5066/P93LGLVQ, ScienceBase item 657e1d85d34e23d3533209f7).
- **Physical signature:** magnetic zero-contour lines of the tilt derivative mark near-vertical
  contacts and faults; corridors where the zero line persists across multiple continuation
  heights indicate a deep-seated, blind structure.
- **Why it catches faults missing from USGS/INGENIOUS:** magnetic methods see through cover;
  a fault with no Quaternary scarp still offsets magnetic basement. Zero-convergence across
  scales selects deep structures the scarp-dependent catalogue misses.
- **How it differs from this repo:** H2 in the old register tested magnetic tilt-derivative
  ridge alone (0.0396 vs 0.0489 uniform → negative). H10 is different: **zero-convergence
  corridors across multiple heights**, not ridge magnitude at one height. No previous submission
  uses multi-scale magnetic zero-convergence.
- **Non-fault mimic:** lithologic contacts, dike swarms, alteration zones. Mitigated by requiring
  persistence across ≥ 2 continuation heights and concordance with gravity edges.
- **Data source:** USGS GeoDAWN release, https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7
  (public domain; needs reprojection to EPSG:32611/100 m).
- **Cost:** medium–high. Grids are large (hundreds of MB zipped).

---

## Ranking summary

| Rank | Hypothesis | Expected DTI gain | Cost | Implementable locally? |
|------|-----------|-------------------|------|------------------------|
| 1 | H6 Damage-zone edge targeting | High (novel target, sparse budget) | Low | **Yes — implemented** |
| 2 | H7 Distance-band curvature (Laplacian) | Medium | Low | Yes |
| 3 | H8 Existing-faults minus labels delta | Low (likely falsified: rasters identical) | Trivial | Yes — verify first |
| 4 | H9 2-m probe temperature residual kriging | Medium–high | Medium | No — needs INGENIOUS harvest |
| 5 | H10 Magnetic tilt zero-convergence corridors | Medium | Medium–high | No — needs GeoDAWN download |

---

## Validation plan (before any submission slot)

1. Build a spatially blocked holdout: withhold whole fault segments with a buffer, derive every
   catalogue-based feature only from visible faults, mask visible faults pixel-exactly, score
   pooled DTI (α 0.2, β 0.8, 300 m triangular kernel) with a 95% CI.
2. Leakage canary per feature: AUC > 0.90 on the holdout means leakage until disproved.
3. A candidate must beat the holdout baseline and pass the uniqueness gate (lattice rule
   resolved — IR-S-01).
4. Budget: 3 experiments or 2 hours, then stop and report, including negative results.
5. No weekly submission slot is spent until a selector step signs off. This environment has no
   DrivenData credentials, so no submission can be made from here.