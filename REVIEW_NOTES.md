# Repository review — 2026-10-28

## Decision

**DO NOT SUBMIT any GeoTIFF currently checked into this repository.** The current audit receipt is [`docs/data/run-card.json`](docs/data/run-card.json): no candidate was generated in that audit, no holdout DTI/CI is available, the complete current registry was not checked, and the recorded verdict is `negative` / `ok_to_submit: false`. Older experiment receipts, including ones whose own verdict is `promote`, are historical reports and do not supersede the current audit or the literal registry-lattice gate. Local format validation only establishes file-format properties; it does not establish uniqueness, leaderboard performance, or organizer acceptance.

The user-supplied historical scores are retained as **USER-REPORTED** (not organizer-confirmed):

| Site | Best score in supplied snapshot | Submission (short name) | Caution |
|---|---:|---|---|
| GEMSDOE24 | 0.2477 | `h25-1-dotted-h19-5-d1-5` | Same dotted H19-5 family as later leaders, per repository's owner-mirror audit. |
| GEMSDOE25 | 0.2600 | `dotted-h19-5-d2-8` | Near-duplicate family, not a distinct strategy by itself. |
| GEMSDOE27 | 0.2449 | `topo-gap-closure-t-v2-on-d1-5` | User-supplied score; local audit records this as family-related. |
| GEMSDOE28 | 0.2710 | `h36-1-rung30-blind-r1` | Highest among listed GEMSDOE28 entries. |
| GEMSDOE30 | 0.2600 | `d28-poisson300m-offcat-44090` | User-supplied score. |
| GEMSDOE31 | 0.2708 | `h27-4-solo-d28` | Audit indicates strong dot-mask overlap with related candidates. |
| GEMSDOE32 | 0.2778 | `h33-h33-2-b2` | Highest in the requested-site snapshot; not the current public contest leaderboard score. |
| GEMSDOE33 | 0.2632 | `h33d-analog-tip-stepover-r30` | User-supplied score. |
| GEMSDOE36 | 0.2750 | `anderson-geothermal-pinn-38854` | User-supplied score; artifact-specific format/uniqueness concerns are documented in `IRREGULARITIES.md`. |

These are historical page/prompt observations, not estimates of a new submission's score. No defensible live-score estimate can be computed from the evidence currently available. In particular, a local holdout DTI cannot be translated to organizer leaderboard DTI without a validated calibration relationship and matched evaluation protocol.

## Findings and changes made

1. The README previously opened with an old HVFD-EXP3 “OK TO DOWNLOAD: YES” headline even though the latest root audit card is negative and records no new raster. Added an explicit current decision at the top.
2. The site homepage showed older “OK to Download: YES” language and its HVFD detail page said `VERDICT: PROMOTE`, directly conflicting with the root audit and fail-closed decision. Reworded these as archived research artifacts and placed an explicit **DO NOT SUBMIT** warning on the HVFD page. Historical files were not deleted.
3. The README and audit record had potentially confusing distinction between downloadability, format validity, and submission authorization. The current notice states these are separate gates.

## Hypothesis shortlist — not tested or promoted

The protocol assigns a single SASS2-XGHF lane and caps work at three experiments/two hours. The checkout's latest audit says its reusable shared prepared cache/evaluator and complete registry are unavailable, and its synthetic probes found shared-tool issues. Consequently the following are prospective questions, **not experiment results**; none can be claimed novel against every external site without a complete registry audit. Do not generate or select a submission until prerequisites are restored.

| Priority | Candidate question within the assigned geophysical/hydrothermal lane | Target layers / transform | Why it might find an unmapped fault | Difference from listed repo methods | Cost / validation readiness |
|---|---|---|---|---|---|
| 1 | Multi-scale edge persistence under modality-specific perturbation | Existing magnetic RTP/TMI and gravity channels; compare gradient/tilt boundaries across scales and modest smoothing/noise perturbations | A buried structure may yield co-located, persistent boundaries even where surface scarps are absent; lithologic contacts/dikes remain confounders | Tests boundary *stability* rather than single-scale cross-gradient or fixed corridor ranking; a related prospective note is already in current `docs/data/run-card.json`, so it is not established as new | Low compute; cannot validate until shared evaluator/cache and same-protocol incumbent exist |
| 2 | Cross-gradient sign/angle coherence conditioned on hydrothermal residual | Gravity and magnetic derivatives plus existing temperature/geothermometry channels; spatial coherence/angle of cross-gradient minima | Fault-related juxtaposition may align geophysical contacts and hydrothermal transport; suppresses isolated anomalies | Uses scale/azimuth-consistency and conditional coupling, not only cross-gradient magnitude fusion | Medium; all layers are alleged to be available in cached features, but the current cache is not verified present |
| 3 | Competing-scale curvature-vs-slope discriminator for blind basin-margin structures | Existing DEM-derived elevation; profile curvature, plan curvature, and multi-radius slope breaks | Buried or subdued fault scarps may preserve linear curvature transitions under alluvium | Separates directional curvature signatures from previous scarp/dotted-ridge ranking; erosion, shorelines and roads are strong confounders | Medium; DEM-derived features may already exist; no new external source required if cache confirms it |
| 4 | Hydrothermal anomaly residual after explicit playa/shoreline/road nuisance regression | Existing radiometric/geothermal layers plus Lahontan shoreline and road-distance nuisance layers already used in this lane | Fault-fed flow can produce spatially coherent thermal/geochemical residuals beyond the known nuisance footprints | Tests residualization and spatially blocked generalization rather than adding more hydrothermal channels to an ensemble | Medium; uses in-repo sources but needs fold-safe recalculation and canary |
| 5 | Fault-parallel thermal/geochemical corridor continuity versus isotropic clustering | Existing hydrothermal point/raster channels and magnetic/gravity lineament orientation | A connected conduit may align with structural grain and extend beyond mapped fault endpoints | Measures directional continuity rather than the current anisotropic dot-placement objective; must avoid using visible target faults as direct predictors | Medium/high; fold-safe orientation estimation and buffered component holdout required |

No candidate above has been tested in this review. Given the explicit “one lane / reuse shared tool / maximum three experiments” protocol, do not treat this shortlist as authorization to launch five experiments. The highest-ranked candidate is only a pre-registration suggestion; first restore and verify the shared evaluator/cache and define the same-protocol baseline. The present environment did not have Python dependencies installed (`pytest` and `numpy` missing), and no model or new raster was run.

## Verification

- `npm ci && npm run test:site`: **PASS**, including site behavior states `ok`, `changed`, `limited`, and `missing`.
- `pytest -q`: **NOT RUN**; `pytest` executable is absent.
- `python -m unittest discover -s tests -v`: **BLOCKED**; test imports fail because `pytest` and `numpy` are not installed.
- No new TIF was generated, no organizer portal was accessed, and no competition slot was used.

## Next work (ordered)

1. Provision dependencies from the lock/requirements files in a clean environment and run the full tests; resolve failures rather than inferring success from the static-site tests.
2. Obtain and checksum the authorized official sample, labels, prepared feature stack and the exact shared evaluator; repair shared evaluator defects centrally and rerun its synthetic contract tests.
3. Restore a complete current comparison registry, including pre-placement surfaces where available. Recheck both rank correlation and 3-px dot overlap for all existing candidates; preserve source hashes and mark stale/unavailable sources.
4. Reproduce the relevant historical incumbent and the top candidate on one identical spatially blocked hide-and-recover protocol; run each feature's leakage canary first. Record withheld-positive counts and bootstrap/appropriate 95% CIs.
5. Only if all gates pass, regenerate through the shared writer, validate against the official sample reference and range `[0,1]`, and issue a new run card. Submission-slot selection is separate and must obey the current account quota. Do not infer organizer acceptance until a portal receipt exists.
