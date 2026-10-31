# S3 hypotheses register — generated 2026-10-31, ranked, top candidate validated

Protocol compliance: 5 candidate hypotheses generated **before** implementation of the
shipped raster; each names the layer(s), the physical signature, why it should catch a
fault missing from the USGS/INGENIOUS catalogue, and how it differs from everything in
this repo.  Ranking is by expected HOLDOUT-DTI improvement per unit cost (a judgement,
not a measurement).  The top-ranked candidate was validated on the spatially-blocked
hide-and-recover holdout (GEMSDOE32-HIDE-RECOVER-v3.0) and the off-catalogue SGMC
instrument (GEMSDOE32-SGMC-CAL-v3.0) **before** any submission-slot decision; no weekly
slot has been spent by this session.

All data below were restored by `scripts/fetch_data.py` from hash-pinned public mirrors
(`registry/data_manifest.json`) of official USGS / GBCGE / GDR releases — links in
`docs/sources.html`. Numbers are HOLDOUT-DTI unless marked otherwise.

---

## S3-H1 · CATALOGUE-RING HABITAT EMISSION (rank 1 — IMPLEMENTED AND VALIDATED)

- **Layers:** `labels.tif` catalogue geometry (repeller + ring distance), footprint mask.
- **Signature:** annular emission density peaking 1–1.2 km outside the mapped fault
  database and decaying to a 20 % uniform floor — the damage-zone / splay / continuation
  habitat, never the mapped trace itself (hard 3 px collar).
- **Why it catches catalogue-missing faults:** every measured population in this project
  shows off-catalogue truth clustering on the *same fault systems* the catalogue maps:
  the nine-site champions put their dots at a median 15–20 px from the catalogue and
  score 0.2449–0.2778; the SGMC-off population (62,703 px of USGS state-map faults the
  competition catalogue lacks) lies in the same corridors.  Blind splays and along-strike
  continuations with no independent scarp are exactly the class the scarp-dependent
  catalogue misses.
- **Difference from this repo/registry:** no registry raster is ring-modulated blue-noise;
  the nine-site family modulates by *lineament* habitat, the strain-ridge lane by strain
  corridors.  Measured unique: max 3 px overlap 23.0 % vs any genuine raster, max
  |Spearman| 0.0086 (`evidence/s3_uniqueness_20261031.json`).
- **Non-fault mimic:** alluvial-fan toes and playa-margin reworking inside the ring;
  the 3 px collar removes mapped mimics, the uniform floor bounds the rest.
- **Validation (2026-10-31):** IHR pooled DTI **0.0597** [CI 0.0537–0.0649] vs uniform
  control 0.0439 [0.0394–0.0481] at matched 37,654-dot budget (+36 %, disjoint CIs);
  SGMC-off **0.0770** [0.0715–0.0827] vs 0.0750 [0.0717–0.0782].
  N = 24,000 variant negative on both instruments.  Verdict: **PROMOTE** the
  37,654-dot raster (MODEL ESTIMATE 0.285–0.29; risk band 0.25–0.33 — never a score).
  Run card: `evidence/s3_run_card_20261031.json`.
- **Cost:** trivial (already paid).

## S3-H2 · DTI-OPTIMAL SOFT EMISSION (rank 2 — partially tested; leaderboard axis untested)

- **Layers:** any placement field; the change is the output form (continuous p ∈ [0,1]).
- **Signature:** plateau/kernel probability mass around each sampled centre instead of a
  binary dot; insures the FN term (β = 0.8) against 1–3 px positional misalignment of
  hidden truth (the problem page states parts of the existing fault data are misaligned).
- **Why off-catalogue:** hidden truth is misaligned with every structural prior; a soft
  fringe recovers cover that binary dots lose to FN.
- **Difference:** every measured registry raster is binary (`is_binary_emission=True` in
  all 38 rows of `docs/data/org-ledger-measured.csv`); the official reference notebook
  emits sigmoid probabilities.
- **Non-fault mimic:** none physical; the risk is FP mass dilution (the FP term charges
  every unit of p).
- **Validation 2026-10-31 (partial):** plateau1 at ring-37,654: SGMC 0.0925 (+20 % vs
  binary) but IHR 0.0312 (−48 %; the visible-fault pixel-exact mask eats plateau mass —
  an instrument artifact).  Split verdict; the leaderboard response to softness is
  **unmeasured**.  Ship binary until a weekly slot is deliberately spent on this axis.

## S3-H3 · FLUVIAL CHI-ANOMALY CORRIDORS (rank 3 — untried)

- **Layers:** `external/dem10_chi_100m_i16.tif` (USGS 3DEP 10 m DEM chi-integral profile
  analysis, Perron & Royden 2013; restored, hash-pinned, used by no lane).
- **Signature:** kinks / slope-break clusters in chi profiles mark lithologic contacts
  and tectonic base-level steps; a fault-bounded range front produces a coherent chi
  discontinuity without a Quaternary scarp.
- **Why off-catalogue:** fault-bounded bedrock fronts with no young surface rupture are
  invisible to scarp-dependent mapping but leave drainage-geometry scars.
- **Difference:** no lane or registry raster uses chi; DEM-10 m derived but distinct from
  the LiDAR scarp stack (that lane measured negative on ridge alone: 0.0396 vs 0.0489).
- **Non-fault mimic:** lithologic contacts, lava dams, drainage capture.
- **Cost:** low (raster in hand).  Expected gain: modest.

## S3-H4 · PALEO-HYDROTHERMAL DEPOSIT HALOS (rank 4 — untried in halo form)

- **Layers:** `paleo_geothermal_regional` (709 sinter/travertine deposits, INGENIOUS
  GDR 1391) + `geodawn_extensions_u8` Th/K alteration channel.
- **Signature:** 1–2 km halos around fossil sinter/travertine mounds mark abandoned
  focused-upflow conduits; the bounding strands of those conduits are faults the
  catalogue never traced.
- **Why off-catalogue:** dead hydrothermal systems have no young scarp expression and no
  current thermal anomaly — the two classes every other lane keys on.
- **Difference:** the VRC lane used 21 *active* vent points' proximity decay and measured
  negative (holdout 0.0086); deposits+alteration halos are a different population and a
  different transform.
- **Non-fault mimic:** pedogenic carbonate, lake-marginal tufa.
- **Cost:** low.  Expected gain: small (the thermal family measured negative in EXP-1).

## S3-H5 · SHALLOW-TEMPERATURE RESIDUAL GRADIENT EDGES (rank 5 — untried in edge form)

- **Layers:** INGENIOUS 2-m probe `F2mDAB` residuals + well/spring geothermometer table
  (GDR 1391, 8,718 temperatures, 1,247 geothermometer estimates).
- **Signature:** *edges* of localized positive residual anomalies (upflow conduit
  margins), not the anomaly ranks.
- **Why off-catalogue:** blind permeable faults express themselves hydrothermally where
  they have no surface rupture.
- **Difference:** EXP-1 tested the *rank* form of this field and it **lost to uniform**
  on both instruments (IHR 0.0287 vs 0.0439; SGMC 0.0329 vs 0.0750).  The edge form is
  untried but the family is demoted to last.
- **Non-fault mimic:** basin-fill groundwater advection, volcanic heat, ranch/road
  measurement clusters.
- **Cost:** low.  Expected gain: low (family measured negative).

---

### Register updates to earlier documents

- `research/2026-10-30-hypotheses-ranked.md` H4 ("2-m probe temperature residual
  kriging") is **tested-negative in its rank form** by EXP-1 (see above); its edge form
  survives as S3-H5.  H2 soft emission remains open (S3-H2).
- The leakage canary for every S3 input field (wellspring IDW, probe IDW, paleo IDW,
  composite, smoothed rank) passed: max symmetric AUC **0.52101** (`probe`), limit 0.90
  (`evidence/exp1_thermal_share_sweep.json`).
