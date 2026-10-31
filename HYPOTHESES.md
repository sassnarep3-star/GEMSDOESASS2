# Geological hypotheses — current status (2026-10-30)

The live hypothesis register — what was tried, what was measured, and what is still open — is
**README §5** ("Hypothesis register"). Supporting files:

- [research/2026-10-30-hypotheses-ranked.md](research/2026-10-30-hypotheses-ranked.md) — ranked
  mechanisms, physical signatures, non-fault mimics and official data sources, with a
  post-merge reconciliation against the tested register.
- [research/2026-10-28-hypotheses-and-review.md](research/2026-10-28-hypotheses-and-review.md) —
  earlier XGHF-family proposals (historical).

**Current state:** H1 (STRAIN-RIDGE off-catalogue blind faults) is implemented and promoted —
see the [decision table](README.md). H2 (magnetic tilt) and H3 (radiometric Th/K point values)
are measured **negative**. The strongest untried lead is the 2 m probe temperature residual
kriging (INGENIOUS shallow-temperature archive). Negative results are deliverables; every
number is labelled HOLDOUT-DTI or MODEL ESTIMATE, never an organizer score. See
[IRREGULARITIES.md](IRREGULARITIES.md) for the full corrections ledger.

## 2026-10-31 — hypotheses H10–H13, ranked before implementation

Each names (a) the data layer, (b) the physical signature, (c) why it could catch a fault the
public catalogue misses, (d) how it differs from everything already in this repository.

| # | Hypothesis | Layer (a) | Signature (b) | Why it is not the catalogue (c) | Difference from repo (d) | Expected gain | Cost | Verdict |
|---|---|---|---|---|---|---|---|---|
| **H10** | **Detrended-elevation-slope density.** Faults express as slope breaks in locally detrended relief; a density prior on that field, at the metric's optimum, recovers more independent faults per cell than any fitted model. | Official band 19, `det_elev_slope` (100 m); Gaussian sigma 5 px. | Slope magnitude of the detrended surface, smoothed to the 500 m fault-correlation scale. | Band 19 is a physical measurement, not a label; it fires on structural lineaments wherever they are, including where the QFaults compilation has nothing. | No model, no training, no catalogue-derived feature, no collar geometry — three choices total. | **+0.108 independent DTI** (0.403 vs 0.295 control) | 20 min | **PROMOTED** |
| H11 | Multi-scale lineament coherence. Faults are continuous linear features; a structure-tensor/Hough coherence field at 300–1500 m should beat a pointwise slope field. | Band 19 + 12 (detrended elevation) + 6 (curvature). | Orientation-consistent ridge response, not raw magnitude. | Coherence rejects the isotropic "rough ground" response that survives in H10 and is exactly the terrain confound measured here. | Replaces the pointwise density with an oriented one; never tried in this repo. | +0.03–0.08 | 2–3 h | untried |
| H12 | Structure-tensor ridge on the 1 m DEM at 2 m posting. Fault scarps are metre-scale; 100 m bands alias them. | USGS 3DEP 1 m DEM → 12-channel morphometry at 100 m. | Fine-scale scarp ridge / curvature, aggregated to the competition grid. | A 1 m DEM sees scarps that no 100 m product resolves, so it can find faults the regional compilation missed. | Uses an external 1 m product the official stack does not contain. | +0.02–0.06 | 4–6 h (download blocked outside GitHub) | blocked |
| H13 | Vent/spring proximity kernel. Thermal springs and volcanic vents sit on conduits; a kernel around the 22 vents and 27,093 wells might localise blind faults. | GDR vent and well inventories (`.cache/external`). | Distance-decay kernel around thermal features. | Conduits are structurally controlled; a vent on an unmapped fault marks it. | Distance-to-feature rather than a raster field. | −0.05 to +0.05 | 1 h | untried, low prior |

Ranking rule: expected DTI gain first, implementation cost second. H10 was the only one whose
signal was verified **before** the design was built (band 19 AUC 0.757 on the independent
compilation, measured first), so it was the only one allowed to spend the slot. H12 stays
blocked: the 1 m DEM is not reachable from this sandbox (only github.com egress).
