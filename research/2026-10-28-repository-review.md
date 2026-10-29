# Repository review — 2026-10-28 (Arena review pass)

## Executive decision

**DO NOT SUBMIT any GeoTIFF currently checked into this repository.** No candidate, holdout result, or organizer receipt was produced in this review. The existing fail-closed state is correct and should remain in place: the current run card is negative, `ok_to_submit=false`, and the most recent research rasters fail the literal 70% registered-raster overlap rule.

This is a repository/code review, not a geological experiment. Historical scores listed in the project are owner/user-reported unless accompanied by a DrivenData submission-page receipt. No new leaderboard score or projection is claimed.

## Review passes

### Pass 1 — repository and evidence inventory

- Worktree began clean on `arena/5305769d-gemsdoesass2`, at `88e8a73` (the checked-out `origin/main` base).
- Read the standing prompt, README, current negative run card, nine-site summary, registry/audit evidence, hypothesis shortlist, irregularities log, submission inspector, current static site and project test configuration.
- Confirmed that the home page presents a clear negative decision and disabled submission download; the nine historical site winners are identified as research-only, with no defensible new leaderboard estimate.
- Confirmed that the alleged 19-band feature source is an owner-hosted mirror, not authenticated DrivenData data. The included bridge sample is likewise not evidence of organizer acceptance.

### Pass 2 — exercise user-facing paths and unsafe legacy entry points

- `npm ci && npm run test:site && node --check docs/assets/app.js`: **PASS**; all four site source-check scenarios (`ok`, `changed`, `limited`, `missing`) passed.
- Installed the pinned audit dependencies from `requirements-audit.txt` in an ignored virtual environment and ran `.venv/bin/python -m pytest -q`: **PASS — 111 tests**, with 27 Rasterio `PendingDeprecationWarning`s.
- Ran the saved-byte inspector on both currently highlighted research GeoTIFFs against `data/bridge/sample_submission.tif`:
  - HVFD-EXP3, SHA-256 `28bb9419d592797dcac1bfb1eb19fcffa7581a51718230f1f4f957a3e3d610d6`: strict local-format pass; `organizer_accepted=null`; `ok_to_submit=false`.
  - SASS2-XGHF, SHA-256 `2a122a409c7a7d5977a311dce271d6f333f21a697cd9effd59b45c6c0f0e8ec7`: strict local-format pass; `organizer_accepted=null`; `ok_to_submit=false`.
- Exercised the XGHF runner, evaluator, writer, legacy site builder, TTC generator and SCU pipeline. Each exits with code 2 and an explicit fail-closed warning. These stops are important protections, not successful model/holdout functionality.

### Pass 3 — consistency and edge review

- Rechecked that the current card and visible site do not translate local format validation into upload approval, nor translate an unverified holdout into a leaderboard estimate.
- Confirmed old green/promotion-era implementations remain behind fail-closed stops; they must not be run or revived as-is. Their source bodies and older receipts contain claims that are superseded by the current audit.
- Confirmed no new TIF was generated, no geological experiment was run, no external submission slot was spent, and no current account quota or organizer receipt is available.
- `git diff --check` is expected after this report is added; the full code/test state otherwise remains unchanged.

## Findings and severity

| Severity | Finding | Evidence / effect |
|---|---|---|
| **Blocker** | The reusable evaluator and writer are deliberately disabled; the shared upstream implementation has known synthetic-contract issues. | `scripts/evaluate_holdout.py`, `scripts/submission_writer.py`, `scripts/run_sass2_xghf.py` exit 2. This checkout cannot currently complete the required validated generate→holdout→write workflow. Do not replace the guard with a private implementation. |
| **Blocker** | The complete, current registry and the account's official reference sample / slot allowance are not established. | Pinned owner mirrors and existing receipts are not equivalent to a complete live registry or authenticated organizer data. Novelty and portal acceptance cannot be certified. |
| **Blocker** | Literal overlap with the calibration lattice makes the previous 37,654-dot candidates duplicates under the supplied rule. | The negative run card records 37,617/37,654 and 37,636/37,654 within 3 px (both far above 70%). Do not exempt the lattice without an explicit protocol change. |
| **High** | No reliable leaderboard-score estimate exists for a new candidate. | No same-protocol validated calibration to the private score is available. Show “unavailable,” not a projected score. |
| **High** | Method lane is ambiguous. | The supplied parallel protocol refers to a “single method paragraph” but does not identify one. Repository XGHF descriptions are prior project proposals, not proof of a user-assigned lane. |
| **Maintenance** | Legacy scripts remain as long historical files below their safety guards. | Clear warnings prevent their normal CLI use; tests currently pass. Keep tests around the fail-closed behavior and do not rely on old embedded comments/cards as current results. |
| **Maintenance** | Rasterio emits 27 pending-deprecation warnings in format tests. | Non-failing and upstream-originated; can be cleaned up separately, without changing geotransform semantics. |

## Nine-site result, correctly qualified

The executive summary and `docs/data/summary.json` cover GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. The supplied highest values (0.2477, 0.2600, 0.2449, 0.2710, 0.2600, 0.2708, 0.2778, 0.2632 and 0.2750 respectively) are **historical USER-REPORTED / UNVERIFIED values**, not organizer-confirmed scores. The pinned raster audit finds strong overlap/lineage among the selected variants, so none is represented as unique or as an endorsed download for resubmission. A score for a future submission is **not estimable** from this evidence.

The reported GEMSDOE32 0.2778 may be consistent with a denser/selected descendant of a shared dotted H19-5 family, where catalog pruning or sampling changes false-positive/false-negative tradeoffs under the distance-weighted Tversky metric. The raster lineage supports a shared-mask explanation; it does **not** establish the organizer's hidden confusion components or prove why that result scored 0.2778. A claim that a new raster beats it needs a same-protocol holdout result and ultimately an organizer receipt.

## Next steps, ordered to maximize evidence per slot

1. Obtain authoritative agreement on the intended lane and a current full registry (including raster/surface artifacts used by the literal duplicate test); preserve immutable hashes.
2. Resolve the shared evaluator/template synthetic failures upstream, then use the shared cached stack, hide-and-recover split, whole-segment buffers, visible-only catalogue features, exact mask, pooled 300 m triangular DTI and documented 95% CI. No private fork.
3. Reproduce a frozen comparable baseline; test each candidate feature alone for leakage (AUC > 0.90 is a stop pending explanation); run no more than three pre-registered experiments / two hours.
4. Only a candidate that improves the same-protocol HOLDOUT-DTI and passes surface and final-dot novelty scans should reach the shared writer. Validate the exact saved bytes against an authenticated organizer sample, record SHA-256, and keep `ok_to_submit=false` until the separate selector gate and account allowance are verified.
5. Do not use a weekly competition slot until the full evidence bundle passes. On upload, retain the submission-page receipt; only then label its score ORGANIZER-CONFIRMED.

## Run card (negative; no new raster)

```json
{
  "hypothesis": "No new geological hypothesis tested in this review; the repository's current multiscale cross-gradient proposal remains unvalidated.",
  "mechanism": "No experiment run. Existing candidate assessments remain subject to the pinned registered-raster audit.",
  "named_non_fault_process": "Lithologic contacts and dike swarms can mimic aligned magnetic/gravity boundaries.",
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": null,
    "withheld_positives": null,
    "dti": null,
    "ci95": null,
    "status": "NOT RUN"
  },
  "correlation_overlap_vs_registry": {
    "new_surface_spearman": null,
    "new_final_dot_overlap": null,
    "status": "No new candidate; previous 37,654-dot candidates fail the literal lattice-overlap gate."
  },
  "raster_sha256": null,
  "validator_output": {
    "new_raster": null,
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "status": "No new raster. Two existing artifacts pass local format inspection only against an owner-mirror sample; neither is approved."
  },
  "submission_name": null,
  "note": "Negative repository review; no new candidate or submission approval.",
  "verdict": "negative"
}
```

## Source links for review

- [Official competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem and metric description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Data page (requires account access)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official leaderboard (dynamic)](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN dataset](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [Current audit receipt](../docs/data/audit.json) · [negative run card](../docs/data/run-card.json) · [irregularities register](../IRREGULARITIES.md)
