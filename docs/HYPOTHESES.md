# Candidate Geological Hypotheses — Preregistered Queue

## Scope warning

At the starting commit this repository contained only a one-line README, so it
had no implemented geological detector to compare against. The public peer
repositories contain many experiments, but names and public artifacts cannot
prove that a mechanism has never been tried globally. The rows below therefore
mean **not implemented in this repository before this session** and avoid the
focused historical families (dotted/pruned D2.8, topology gap closure, Euler,
analog tip/step-over, and Anderson/PINN) where possible.

“Expected DTI opportunity” is a qualitative prioritization, **not a score
estimate**. A blocked idea is not viable until its named source is actually
obtained, hash-recorded, and screened for leakage.

| Rank | Hypothesis and specific layers | Physical signature / uncatalogued-fault rationale | Named non-fault mimic | Difference from focused historical files / this repo | Expected DTI opportunity | Cost / source readiness |
|---:|---|---|---|---|---|---|
| 1 | **CDCC-01: GeoDAWN cross-domain contact concordance.** `TMI_up150` (GeoDAWN extensions band 4) × `U/Th` (radiometric band 3). | Robust short-scale gradient magnitude is calculated independently in each sensor and fused by geometric mean. A concealed structural boundary can juxtapose magnetic basement contrast and near-surface alteration/lithology without appearing as a catalogued surface trace. | Lithologic contact, intrusive margin, acquisition/processing seam, alteration front. | It is a label-free two-sensor edge *intersection*, not D2.8 pruning, Poisson placement, topology closure, an analog transfer, or a PINN. No prior code existed here. | Medium | **Tested once** using an untrusted peer mirror; source values are rank-quantized and cannot promote a result. Medium compute cost. |
| 2 | **Potential-field edge orthogonality under cover.** Competition `rtp`, `tmi_hg`, `tmi_vg`, `iso_grav_anom`, and gravity derivatives. | Fit local gradient/tensor directions; prioritize consistent magnetic–gravity discontinuities with cross-gradient geometry that is incompatible with a single smooth lithologic boundary. Transfer faults beneath basin fill may perturb both fields while lack surface scarps. | Density/magnetization contrast at an intrusive or stratigraphic contact; flight-line processing artifact. | Distinct from single-field Euler/ridge families because it requires an explicit cross-field directional consistency test and tests under-cover pixels separately. | Medium–high | **Blocked.** Requires the organizer `numeric_features.tif` with verified band metadata in `data/raw/`. The official competition data tab is login-gated here. |
| 3 | **Radiometric redox-halo termination test.** GeoDAWN `U/Th`, `Th/K`, `U/K`, and `TMI_up150`. | Look for an annular or paired isotope-ratio anomaly terminating a magnetic edge, rather than generic radiometric high values. Hydrothermal fluid pathways can alter U/Th and K/Th around a blind fault termination. | Lithologic weathering/soil moisture variation, surficial alluvium boundary, survey block seam. | Unlike the focused historical masks, this uses an endpoint/halo geometry and explicit block-seam control rather than adding dots along an existing fault-prior lattice. | Medium | **Blocked as a viable proposal** until original, official GeoDAWN rasters—not the peer’s uint8 ranks—are downloaded, checksummed, and license-reviewed from the [USGS release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). |
| 4 | **Distributed-deformation swath persistence.** Official 3DEP 1 m DEM tiles plus slope, curvature, and orientation persistence across multiple drainage basins. | Detect a broad, low-amplitude, consistently oriented deformation swath instead of a sharp scarp. A fault under thin cover may cause aligned subtle warping where a catalogue emphasizes obvious scarps. | Roads, channels, terrace risers, paleo-shorelines, mines, landslides. | Existing peer names include scarp/D8/knickpoint work; this proposal is deliberately a basin-persistent deformation statistic with nuisance controls, not an isolated edge detector. | Medium | **Blocked.** Need the organizer-provided DEM-link inventory or a verified official 3DEP tile inventory, projection/datum provenance, and no-road/no-channel confound layers. |
| 5 | **Fault-fluid graph intersections.** Official thermal spring/well/temperature observations, structural lineaments, and public catalogue only for fold-local masking. | Build a graph of independent fluid/thermal observations and physical geophysical corridors; prioritize intersections or conduits rather than proximity to a single point. A structurally controlled geothermal pathway can be uncatalogued at the surface. | Basin groundwater flow, drilling/observation selection bias, mining/water infrastructure. | It is an evidence-graph hypothesis rather than a raster lattice or point-density emitter. It deliberately excludes catalogue-derived targets from the static surface. | Potentially high but uncertain | **Blocked.** The user-cited [OpenEI GDR resource](https://gdr.openei.org/submissions/1391) must be obtained from a free official endpoint, versioned, and bias-audited first. It was not accessible from this environment, so it is not proposed as currently viable. |

## Top-candidate result — CDCC-01

**Experiment count:** 1 of 3; **weekly slots spent:** 0.

| Arm | Result type | Result | Interpretation |
|---|---|---:|---|
| Magnetic edge control | HOLDOUT-DTI, `gemsdoesass2-segment-pooled-v1`, 60,988 withheld public-catalogue positives, 95% CI | `0.02702` `[0.00796, 0.04771]` | Feature-alone control only |
| Radiometric edge control | HOLDOUT-DTI, same evaluator/count/CI method | `0.03177` `[0.02306, 0.03842]` | Best predeclared feature-alone control |
| CDCC consensus | HOLDOUT-DTI, same evaluator/count/CI method | `0.05211` `[0.02315, 0.08277]` | Higher point estimate, but not a competition/leaderboard estimate |
| CDCC minus best control | paired spatial-block HOLDOUT-DTI delta, 2,000 bootstrap draws | `+0.02034` `[-0.00983, +0.05019]` | CI crosses zero; promotion gate fails |

All three feature-alone leakage canaries passed the `AUC <= 0.90` rule (maximum
across all tested features/folds `0.65403`; CDCC consensus maximum `0.60737`). This does **not** rescue the failed paired
holdout gate or the input-integrity gate.

**Decision: negative / DO NOT SUBMIT.** The candidate is a unique research
artifact against the nine pins, but neither local uncertainty nor untrusted
mirror provenance justifies a weekly submission slot.

See the complete [run card](data/cdcc_20261027_run_card.json) and
[method details](METHODS.md).
