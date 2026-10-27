# GEMSDOESASS2 — GEMS fault-discovery research

> **Standing project brief — read before every project task.** Build a reproducible, scientifically defensible workflow for discovering faults indicative of geothermal resources in the DOE GEMS challenge. Maximize the probability of a valid, well-evidenced result; own the outcome and publish failures as well as successes. Do not claim a leaderboard improvement without measured evidence. Do not spend a competition slot on an unvalidated candidate.

## Non-negotiable workflow and safety rules

1. **Unique method lane.** Before placement and on final dots, compare every candidate against the available registry rasters. Stop and label duplicate/drift if any absolute rank-correlation exceeds 0.90 or >70% of dots are within 3 px of a registry raster. Record the registry coverage and computation; absence of a registry is not a pass.
2. **Reuse the shared template tools.** Use its cached feature stack and shared `evaluate_holdout.py` and `submission_writer.py`; correct shared-tool defects in the shared template, never a private fork. Holdout hides whole fault segments with a buffer. Catalogue-derived features must use visible faults only; visible faults are masked pixel-exactly. Evaluate pooled distance-weighted Tversky (alpha 0.2, beta 0.8; 300 m triangular kernel), and test each feature alone as a leakage canary (AUC >0.90 is presumed leakage until demonstrated otherwise).
3. **Label every score.** A score is either `HOLDOUT-DTI` with evaluator/version, number of withheld positives and 95% CI, or `ORGANIZER-CONFIRMED` copied from a submission-page receipt. Scores pasted into user prompts and third-party project sites are not receipts. A projection/estimate is never a score.
4. **Run card for each experiment.** JSON fields: hypothesis; mechanism; named non-fault mimic; holdout DTI and CI; correlation/overlap vs registry; raster SHA-256; validator result (no NaN inside footprint, values [0,1], CRS/shape/transform match); submission name and <=140-character note; verdict `promote` or `negative`.
5. **Budget:** maximum 3 experiments or 2 hours, whichever comes first. A positive research result is not slot authorization. A separate selector must confirm the weekly submission cap and approve a real slot.
6. **Submission file:** never call a TIFF ready unless the saved GeoTIFF itself passes single-band, footprint, finite/range [0,1], CRS, dimensions, transform, and organizer-format validation. Never invent an estimate, validation result, registry comparison, checksum, or downloadable file. Clearly state whether it is safe to download and whether it is authorized to submit.
7. **Sources and provenance:** distinguish official competition/scientific sources from participant-maintained sites and user-supplied score claims. Preserve URLs and retrieval date; flag conflicts and missing receipts.

## Project status / important limitation

This checkout currently contains **only this README**: there is no feature stack, competition data, evaluator, submission writer, registry raster set, tests, or generated TIFF. Consequently this checkout cannot execute a holdout, validate a scientific score, establish raster uniqueness, or safely produce an organizer-compatible submission. **No TIFF is available or authorized for submission.** Do not infer readiness from the existence of participant-site downloads. See [Executive summary and research plan](docs/executive-summary.md).

Competition data is available through the DrivenData competition data page and may require an authenticated account. Do not try to bypass access controls. Inputs must be placed locally under a documented data convention; large/private data are not committed to Git. The supplied prior-session claim that scripts exist is not true of this checkout as inspected.

## Competition facts / official sources

- [Problem description and evaluation overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — fault discovery, incomplete existing fault labels, datasets, and distance-weighted Tversky metric.
- [Competition home / rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login may be required)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611](https://epsg.io/32611)
- [GEMS technical report (NLR)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

## Working practice

For every change: read this brief; inspect current repository and data availability; preregister hypotheses before implementation; run tests and record exact commands/results; perform at least three review passes for completeness, edge cases, and alignment; update evidence and limitations. Only publish a GitHub Pages site after there is maintainable site content and a build/deploy workflow. No automated competition submission or account access is assumed.
