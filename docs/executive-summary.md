> **Historical snapshot:** This document describes an earlier empty checkout. Three parallel branches later added research candidates, all of which fail the literal registry rule. See the [current executive summary](executive-summary.html) and [parallel review](parallel-review.html); none is approved for submission.

# Executive summary: site review, evidence, and next actions

**Review date:** 2026-10-27 (UTC)
**Checkout reviewed:** `arena/16c827db-gemsdoesass2`, base `25172e6`
**Decision:** **NO-GO — no locally generated TIFF exists, no validated candidate exists, and no file is approved for submission.** This is a repository capability finding, not a claim that no candidate elsewhere exists.

## What is verifiable now

The repository inspected in this session contained only a 14-byte README (the initial heading was concatenated with the commit hash). No scripts, source code, test suite, geospatial inputs, raster registry, prior TIFFs, evaluator, or writer were present. The README now accurately records the standing protocol and blocker. The user-provided leaderboard/site scores below are catalogued as **USER-REPORTED**, not organizer-confirmed. The submission pages/receipts and raster files were not available in this checkout to independently link each score to its raster.

The official DrivenData problem description says the task predicts geological faults, existing public fault labels are incomplete and may contain inaccuracies, expert-labelled new faults form a test set, and the metric is distance-weighted Tversky. It describes provided geophysical/topographic features and 1 m DEM links, with UTM 11N / EPSG:32611. This supports treating the task as spatial generalization rather than ordinary random-pixel classification. It does **not** establish that any participant-reported score is reproducible on this repo's holdout.

## Requested nine-site leaderboard snapshot

All scores in this table are **USER-REPORTED values supplied in the request**, not `HOLDOUT-DTI` and not `ORGANIZER-CONFIRMED` (no receipt was supplied). “Best listed” is a max among the provided numbers for that site only; it is not a recommendation to download or submit. Values are rounded/copied as provided.

| Site | Best listed submission (per user) | Reported score | Duplicate/uniqueness status | File/submit recommendation |
|---|---|---:|---|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Unknown; no raster bytes/registry comparison | Do not submit on this evidence |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Unknown | Do not submit on this evidence |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Unknown | Do not submit on this evidence |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Unknown; other listed variants are lower | Do not submit on this evidence |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Unknown | Do not submit on this evidence |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Unknown | Do not submit on this evidence |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | Unknown from supplied score alone; participant page inspected, but no auditable local raster bytes/receipt used here | Do not submit/resubmit on this evidence |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Unknown | Do not submit on this evidence |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Unknown | Do not submit on this evidence |

**Important score context:** the request also states a current leaderboard high of 0.3195/0.4413 in different places. These are inconsistent, unattributed snapshots. No date-stamped official leaderboard receipt was captured here; therefore neither should be treated as current/confirmed. A web visit to the GEMSDOE32 participant page displayed the page's own status and explicitly cautioned against upload of its then-current research artifacts; that page is participant-maintained, not an organizer receipt. Treat all competitor-site content as a lead, not validation.

## Why the reported GEMSDOE32 result may be strong — and what cannot be inferred

The user reports the 0.2778 result as the highest among the requested nine sites. The official task description explains that hidden expert-labelled faults are absent from the existing fault catalogue, so a method that generalizes structural/geophysical signatures beyond known catalogue lines has a plausible path to reward. But the score alone does not identify the method's causal contribution, prove generalization, or show it beats the private test/expanded-label score. We cannot attribute the result to “zeros,” a particular feature, or a specific geological mechanism without its raster, experiment record, exact scoring receipt, and controlled ablations. Nor can we promise >0.2778. The official metric is distance-weighted Tversky; in the absence of the exact evaluator and holdout, these site numbers cannot be compared directly to a local score.

## Candidate hypotheses to preregister (not tested; repo has no feature stack)

Ranking is a qualitative research prioritization, **not a score estimate**. “Difference” means absent from this checkout (there is no implementation). Before implementation, inspect the full shared template and its existing registry so “new” is assessed against reality, not this empty checkout. All feature transforms must be derived per fold and tested alone for leakage.

| Rank | Hypothesis / input layers | Physical target and missing-fault rationale | Non-fault mimic / key risk | Difference and cost | Holdout status |
|---|---|---|---|---|---|
| 1 | Multi-scale magnetic analytic-signal and horizontal-gradient direction coherence (GeoDAWN TMI/RTP and derivatives) | Curvilinear, scale-persistent magnetic boundaries may reveal concealed basement structures beyond mapped surface traces; use orientation coherence and boundary persistence, not just raw edge magnitude | Lithologic contact, survey seam, cultural magnetic source, processing artefact | Candidate transforms not present in this repo; medium cost, existing feature layers likely sufficient | Not tested; requires official stack + shared evaluator |
| 2 | DEM profile-curvature / drainage-aligned scarp discontinuity, conditioned on slope and local relief (1 m DEM mosaics) | Subtle, repeated scarps and aligned channel offsets can expose young surface deformation missed in generalized catalogues; scale-space persistence rejects isolated roughness | Fluvial incision, terrace edge, road/earthwork, lithologic slope break | New DEM-derived multiscale context absent here; high cost (download/mosaic/quality control) | Not tested; confirm free official DEM endpoints, licensing/coverage and obtainable URLs before viability |
| 3 | Joint radiometric K-U-Th compositional-boundary concordance with magnetic/DEM structural edges (GeoDAWN radiometric + magnetic + DEM) | Coincident alteration/bedrock contrasts and structural edges can prioritize concealed or weakly expressed fault corridors; look for concordance rather than any single high radiometric value | Lithologic boundary, regolith/moisture, flight-line seam, topographic attenuation | Cross-sensor conditional interaction absent in this checkout; medium-high cost | Not tested; stack availability must be verified; no claim of hydrothermal alteration without field evidence |
| 4 | Strain-rate tensor invariant + gravity-gradient directional intersection and persistence (provided strain and isostatic gravity layers) | Intersections or gradients consistent across independent potential-field and deformation proxies may capture deep structures lacking mapped surficial expression | Regional tectonic gradient, interpolation artefact, unrelated basin boundary | Independent-source geometry / interaction feature absent here; medium cost | Not tested; evaluate fold-local transforms and spatial-block leakage |
| 5 | Multi-resolution DEM drainage-network capture/deflection plus terrain openness, with magnetic structural context | Persistent channel deflection across scales may indicate subtle lineaments missed by catalogue mapping | Lithologic control, erosional anisotropy, human drainage alteration | Explicit network graph/scale stability differs from the nonexistent local implementation; high cost | Not tested; external source not required if provided DEM coverage is adequate |

**Top candidate for first experiment:** rank 1, only if the official numerical feature stack and shared template evaluator are placed in this workspace. It is comparatively cheap and does not require new external data. This is a proposal, not a result. It cannot proceed under the parallel-run cap until shared evaluator, baseline, fold masks, and registry rasters are available.

## Gate before any TIFF is promoted

1. Obtain/verify competition data through authorized access; preserve metadata and hashes. Inspect official reference-solution code and adapt shared template tools rather than creating a private evaluator.
2. Implement spatially blocked, buffered hide-and-recover folds with fold-local catalogue features and pixel-exact masking. Establish same-version holdout baseline and confidence interval; test every feature alone (AUC canary).
3. Run no more than three preregistered experiments / two hours. Compare paired block-bootstrap DTI vs the current same-evaluator best; a point estimate alone is insufficient.
4. Compare both pre-placement surface and final dots to every available registry raster; compute Spearman rank correlation and 3-pixel overlap. Missing registries mean uniqueness unproven.
5. Generate TIFF only after a positive, statistically supported holdout improvement and uniqueness gates. Validate the saved bytes against sample submission CRS, transform, dimensions, band count, footprint and [0,1] range; test re-open. Record SHA-256 and run card. A candidate failing any gate remains a negative research artifact, not upload-ready.
6. Separately check organizer submission page / weekly quota and selector approval. Never upload automatically.

## Submission guidance

**File to download:** none. **Estimated score:** none; a numeric projection would be misleading and protocol-ineligible. **Unique vs requested sites:** unknown, because raster bytes are not locally available for comparison. **OK to submit:** **NO**. No TIFF has been generated or validated by this repository. A legitimate downloadable file requires authorized competition-format template/data and the full scientific/uniqueness/format gate above.

## Limitations and outstanding work

- No DrivenData authentication or competition data in this workspace; do not bypass login or use undocumented access. The README's former claim that scripts are present is disproved by inspection of this checkout.
- No reusable feature stack, shared holdout evaluator/writer, test suite, baseline, registry raster archive, or score receipts. Thus no valid holdout DTI, CI, AUC canary, leakage analysis, uniqueness calculation, TIFF, or score estimate can be produced now.
- Participant GitHub Pages may be stale, incomplete, or edited; the requested list is not the complete competition registry. User-provided score claims require receipt confirmation and raster byte provenance.
- No scientific literature review can be represented as completed here. The hypotheses are testable concepts, not established discoveries; use primary USGS/official sources and published peer-reviewed literature before attributing geological meaning.
- No site was built or deployed; the repository had no existing site. First build reproducible pipeline and records; then provide a static executive-summary site with obvious eligibility status and direct download only for authorized artifacts.

## Source links for review

- [DrivenData problem description (official)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition rules/home (official)](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Competition data page (official; may require login)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Current leaderboard (official; capture date/receipt when verifying)](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Reference solution (organizer GitHub)](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [NLR GEMS technical report](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [EPSG:32611](https://epsg.io/32611)
- [Participant GEMSDOE32 page (not organizer evidence)](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

## Required run card (negative; no experiment was executable)

```json
{
  "hypothesis": "No experiment run: repository contains no data, feature stack, evaluator, or writer.",
  "mechanism": "Not evaluated.",
  "named_non_fault_mimic": "Not evaluated; for magnetic boundary hypotheses, lithologic contacts and survey artefacts are plausible mimics.",
  "holdout_dti": null,
  "holdout_ci_95": null,
  "evaluator_version": null,
  "withheld_positives": null,
  "correlation_overlap_vs_registry": "Not computed; registry rasters and candidate raster absent.",
  "raster_sha256": null,
  "validator_output": "NOT RUN: no raster. NaN/range/CRS/shape/transform cannot be assessed.",
  "submission_name": null,
  "submission_note": "No candidate generated; do not submit.",
  "verdict": "negative"
}
```
