# Repository review — 28 October 2026

## Executive result

The repository is an evidence-first static decision site with useful defensive checks, but it is **not currently a runnable submission-generation / validated-model pipeline**. The safest current decision remains **DO NOT SUBMIT**. No new geological experiment, holdout DTI, or TIFF was produced in this review, and no competition slot was used. A local-format pass is not proof of organizer acceptance.

One presentation ambiguity found in the nine-site page was corrected here: the best restricted-comparison candidate is now explicitly labeled **not approved for download or submission**, not shown in a green success banner. The fallback “no issues” copy now describes only checksum status and explicitly notes unresolved provenance and eligibility issues.

## Findings

### P1 — Candidate evaluation and writing are intentionally disabled

`scripts/evaluate_holdout.py` and `scripts/submission_writer.py` exit with status 2 before reaching their argument parsers or implementation. The same fail-closed pattern protects legacy generators, uniqueness checks, and the site builder. The tests assert these refusals. This is a deliberate safety guard after defects were recorded in shared upstream probes, not an accidental runtime failure; however, it means this checkout cannot run the requested holdout evaluator or submission writer through those entry points, and cannot meet the experiment → validated candidate → TIFF workflow today.

**Next action:** resolve the upstream synthetic-probe failures in the shared source/template (not in a private fork), pin the corrected source, rerun probes, then re-enable only the shared compliant entry points. Do not bypass guards or create a TIFF until the fold-local evaluator, complete registry check, and independent saved-byte validation all work.

### P1 — No defensible current score estimate or promotion evidence

The current run card has null holdout DTI, CI, raster hash, and submission name; it records zero new experiments and a negative verdict. The focus-site score records are user-reported and are not tied to organizer receipts for those exact raster bytes. The reported GEMSDOE32 B2 mask is documented as a two-cell prune of a related mask; that observation alone does not establish the cause of its reported leaderboard score or predict a better one.

**Next action:** retain “NOT ESTIMABLE” until a same-protocol, leakage-audited spatial holdout beats a frozen fold-local incumbent and an organizer receipt ties any actual leaderboard score to the submitted artifact.

### P1 — Novelty and input provenance remain gated

The current negative evidence says the recent 37,654-dot candidates have 37,617/37,654 and 37,636/37,654 dots, respectively, within three pixels of the registered lattice. Those are far above the literal 70% stop threshold. The restored 19-band feature stack is pinned but comes from an owner-hosted mirror, not an authenticated competition download. The report also lacks proof that the local registry is exhaustive/current.

**Next action:** obtain an authorized complete registry and settle the written treatment of calibration/probe rasters before designing another dot budget. Obtain the authenticated organizer sample/data where available. Do not infer uniqueness from the nine-site subset or from a mirror-only inventory.

### P2 — Nine-site page could imply a green light despite the overall stop

`docs/focus-sites.html` previously showed SASS2-XGHF in a green “best genuine receipts” panel while also saying it failed the literal lattice gate. That mixed visual signal was inconsistent with the project's “obvious whether it is OK to submit” requirement. The generator and committed page now use a red fail-closed panel with explicit “NOT approved for download or submission” wording. The same section previously said “None — every historic raster re-hashed and matched”; it now limits the statement to checksum mismatches and names the unresolved review caveats.

**Regression test:** `tests/test_site.py` asserts the explicit negative label, disallows the old green research-candidate banner, and checks the qualified checksum wording.

## Existing strengths

- The homepage and executive summary prominently say **DO NOT SUBMIT**, disable the approved-download CTA, and separate historic reports from estimates.
- The run card distinguishes unverified owner reports, holdout metrics, and organizer receipts; no score projection is presented as a score.
- The local GeoTIFF validator checks single-band float32, CRS, shape, transform, finite `[0,1]` values, and mask/footprint conditions, while explicitly returning `ok_to_submit: false` and `organizer_accepted: null`.
- Data retrieval and cache-restoration tests cover hashes, atomic replacement, symlink refusal, and preservation of existing user data.
- The research note lays out four proposed within-family hypotheses, their layers/transforms, plausible non-fault mimics, novelty caveats, and an evaluation plan. They remain hypotheses, not measured improvements.

## Verification performed

- `python -m pytest -q` initially could not run because the base interpreter had no pytest. Created the repository-local ignored `.venv`, installed `requirements-audit.txt`, and ran the suite: **111 passed**, 27 Rasterio pending-deprecation warnings.
- `npm ci`: completed; audit reported 0 vulnerabilities.
- `node --check docs/assets/app.js`: passed.
- `npm run test:site`: all four freshness scenarios passed (`ok`, `changed`, `limited`, `missing`).
- `git diff --check`: passed after the edits.
- No competition data was freshly downloaded; no new TIFF, holdout, external scientific claim, or official score was generated/verified during this review.

## Recommended sequence

1. Fix and pin the shared upstream evaluator/surface gate; rerun the existing synthetic counterexamples.
2. Confirm the full registry scope and a written treatment for calibration probes; retain fail-closed checks until this is resolved.
3. Confirm authenticated reference rasters and holdout labels, then reproduce the exact protocol on a frozen fold-local comparator.
4. Run the leakage canary for each individual feature before any candidate evaluation; cap the work at three experiments/two hours.
5. Only if the top candidate beats the comparator, run final-surface and final-dot uniqueness, write with the shared writer, reopen and validate saved bytes, and prepare the ≤140-character submission note.
6. Keep promotion to an actual weekly slot separate and require its own selector decision and organizer receipt.

## Review verdict

**Negative / no candidate promoted.** Current repository quality is good on transparent evidence labeling, conservative file validation, and automated safety tests. The primary blocker is scientific/evaluation workflow readiness, not TIFF byte formatting. The user should not download or submit any artifact currently labeled research-only.
