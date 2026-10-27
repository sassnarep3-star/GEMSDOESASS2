# Proposed hypotheses, ranked before implementation

**Status:** conceptual, unrun; none is an assigned parallel-run lane. Ranking is
qualitative scientific judgment, **not a score prediction**. This repository
started empty, so none is implemented here. Similar ideas exist in the wider
parallel portfolio; the complete, current method registry is unavailable and
novelty against every other session cannot be asserted.

| Rank / expected DTI opportunity | Layers and signature | Why it might find catalogue-missing faults | Difference / competing explanation | Cost and data readiness |
|---|---|---|---|---|
| 1 · relatively promising, uncertain | Provided reduced-to-pole magnetics, isostatic gravity anomaly and detrended elevation. Compare oriented, normalized **two-sided magnetic texture matches** at several cross-strike offsets, require the inferred offset sign to persist with scale and be consistent with a gravity-side contrast; use elevation only as an independent, nonmandatory corroborator. | A fault can displace magnetically contrasting strata even when young cover conceals its surface trace. The candidate must be derived without the withheld catalogue; the visible catalogue is used only as permitted by the fold. | More specific than a single magnetic-edge or crest detector: tests a repeated, signed correspondence across the suspected trace, with a scale-stability negative control. Displaced-lag/marker work exists in sibling sites; distinction from every implementation is **unverified**. Mimics: a meandering depositional/lithological boundary, intrusive contact, survey leveling seam. | Medium/high CPU. Layers are described by the [official competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/); the required prepared shared cache is not available here. Not currently runnable under the protocol. [USGS magnetic-strata study](https://www.usgs.gov/publications/aeromagnetic-anomalies-over-faulted-strata) and [Dixie Valley case](https://www.usgs.gov/publications/preliminary-results-a-high-resolution-aeromagnetic-survey-identify-buried-faults-dixie) motivate, but do not validate, the test. |
| 2 · moderate, uncertain | GeoDAWN potassium, equivalent thorium and magnetics: robust centered log-ratio contrasts on **both sides** of a magnetic lineament, after conditioning on mapped lithology/cover and measurement coverage. | Fault displacement or alteration could generate a compositional boundary under modest cover without a catalogue trace; a field is considered only where all inputs exist. | Distinct from a bare radiometric edge by testing flank asymmetry and conditioning on composition and coverage. Other sites have tested radiometric/magnetic fusion; full method exclusivity is not known. Mimics: unfaulted bedrock contacts, sediment sorting, radon disequilibrium and survey seams. | Medium/high. [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) publicly lists radiometric products and CC0, and [ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) lists grids. Listing was accessed; binary files, coverage and units were **not** fetched or validated in this sandbox. Lithology source and licenses still need checking; **data-blocked, not yet viable**. |
| 3 · moderate/low, uncertain | USGS 3DEP bare-earth elevation plus mapped drainage: seek repeated, similarly oriented **cross-valley profile steps or stream offsets**; reject steps following contours or mapped infrastructure. | Small tectonic scarps on alluvial surfaces may be absent from a coarse or older fault catalogue. | Requires multiple independently displaced profiles rather than thresholding one scarp or drainage line; sibling 3DEP/scarp work is extensive and exhaustive novelty is unverified. Mimics: alluvial terraces, shorelines, landslides and roads. | High: tile acquisition, co-registration and negative-control masks. [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) states its products are free; coverage for the specific area has not been verified, and no binary tiles were retrieved here. **Data-blocked.** |
| 4 · exploratory, high uncertainty | GDR INGENIOUS two-metre temperature probes and spring/well geochemistry, with magnetic/gravity lineaments. Test **along-line thermal/geochemical concordance** against matched sampling-density and hydrogeology controls. | A permeable concealed structural corridor might influence heat and fluid transport where no mapped surface trace exists. | Tests a directional multi-site contrast instead of distance to a single vent; prior hydrothermal-conduit approaches exist. Mimics: groundwater mixing and lateral flow, shallow solar heating, and biased survey placement. The target remains a *fault*, not an automatically discovered vent. | High; sparse and biased measurements. [GDR 1391](https://gdr.openei.org/submissions/1391) publicly lists downloadable probes, wells and springs under CC BY 4.0; the landing page was verified, but binary packages, applicability and license for each linked dataset were not independently checked. **Data-blocked.** |

## Frozen validation plan once blockers are resolved

1. Receive one explicit method lane; verify it does not conflict with a concurrent
   registry lane. Freeze the candidate, nuisance controls, dot budget and seeds.
2. Restore the **shared prepared feature cache**, not an independently rebuilt
   one, and use the unmodified shared `evaluate_holdout.py` and
   `submission_writer.py`. Authenticate the official template and labels.
3. Before placing dots, measure rank correlation and literal support overlap
   against the complete current registry. Stop at the prescribed threshold.
4. Hide buffered whole fault segments, rebuild every catalogue-derived feature
   from the visible catalogue in each fold, mask visible faults pixel-exactly,
   and evaluate each feature independently for leakage. AUC above 0.90 is a
   leak alarm, not evidence of performance.
5. Use pooled distance-weighted Tversky (α 0.2, β 0.8, 300 m triangular kernel)
   and a paired spatial-block 95% confidence interval against the **same
   evaluator's** frozen current best. Catalogue holdout is only a proxy for
   newly expert-mapped faults; it is not a leaderboard score or guarantee.
6. If and only if the pre-placement checks pass, place dots, repeat the literal
   uniqueness test on the final saved raster, run the shared writer and
   saved-byte validation, and emit an immutable run card. Stop at three
   experiments or two hours; a later separate selector decides about a slot.

No step above was executed in this preflight. Reinterpreting the dense-surface
or lattice witnesses without a protocol change would silently weaken the rule.
