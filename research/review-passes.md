# Review passes and handoff — 27 October 2026

## Pass 1 — implement and measure

- Started from an essentially empty checkout; did not assume the requested template/cache existed here.
- Read the official problem, metric, rules, masking and quota clarifications; reviewed the nine requested owner sites and pinned their historical artifacts.
- Downloaded only hash-pinned owner mirrors for an educational/forensic audit, kept in ignored `.cache/`. Independently measured all 72 directed nine-site overlaps, the B2/D2.8 pruning identity, the registered lattice footprint, and four newer site artifacts, including three with narrower site-level claims. See [`docs/data/audit.json`](../docs/data/audit.json). GEMSDOE24's [owner-reported TMCG holdout](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/6e4a85a3456dfe6312d25b6d81187c765a10c847/docs/data/tmcg_run_card.json) is negative (0.07157, 95% CI 0.06271–0.08168; `gems-segment-pooled-v1`; 60,988 withheld); it was not independently rerun here.
- Ran synthetic probes against the actual upstream template files, matched by SHA-256 to commit `1398109a23f04a2ace71c1bd2f527cfba87860b5`. Reproduced existing [issues 41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41) and [42](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/42); source access was read-only. This audit did not fork the shared template or run a new model experiment; parallel branches used private evaluators, whose promotion entry points now stop.
- Implemented a standalone, read-only GeoTIFF inspector and a static decision site. The inspector cannot establish organizer acceptance, a holdout win, or slot approval.

## Pass 2 — inspect failure paths

- Added tests for invalid values, NaN/Inf, masked interior, unmasked exterior, null exterior, multi-band, wrong CRS/shape/transform/extension, strict overlap boundary, wrong hashes and incomplete evidence. The local format policy requires both whole-array finite `[0,1]` and a null/masked outside; this is deliberately conservative, not an organizer statement.
- The exact GEMSDOE36 KPL witness is finite `[0,1]` across its array but its outside footprint is unmasked; it fails the conservative local interpretation. Its literal lattice overlap independently fails. Neither finding diagnoses the historical portal error.
- The official staff clarification makes the **website limit** authoritative over the rules’ parenthetical; the account-specific allowance is unknown. Historical values remain `USER-REPORTED / UNVERIFIED` rather than falsely labeled organizer-confirmed.

## Pass 3 — recheck scope and remaining work

- No single assigned method paragraph, reusable prepared cache, current complete registry, authenticated competition sample, comparable frozen incumbent, or account receipt is present. The upstream issue reports already exist and the current account has read-only access. These are separate blockers; “data placement alone” is not sufficient.
- Rechecked the inspector against a deliberately incorrect reference: matching an arbitrary sample is insufficient, so it now separately requires EPSG:32611 and a 100 m north-up grid. Raster audits now reject masked interior cells and positive reference pixels outside the footprint rather than undercounting overlaps. A second audit downloaded all pinned inputs into an empty cache and reproduced every substantive field exactly.
- The site has a visibly disabled submission download, explicit negative card, archived-variant-only table, exact source links, dated public-leader observation and a GitHub-head freshness check. Python tests cover local links and format edge cases; JavaScript DOM tests exercise matching, changed, rate-limited and unavailable-source paths. It does not scrape DrivenData or pretend to operate on the other repositories. A changed source ref flags possible staleness, not new raster content; an unchanged ref does not prove registry completeness.
- A parallel branch added a deduplicated standing-prompt transcription; the full repeated original prompt is not preserved verbatim, and the README records the operative protocol. The broader user-reported list is transcribed in CSV with blanks preserved, but only the nine requested priority variants were compared byte by byte; the broader list is not a complete live registry. This run does not claim to have generated, scored or submitted a unique TIF, nor to have modified the nine other sites.
- Follow the next-session checklist in the README. A new scientifically grounded, smaller-budget attempt might be possible, but must still pass the entire literal registry protocol and all other gates; no outcome is projected.

## Concurrent-branch reconciliation

- Four other pull requests merged while this audit was in progress. The new TTC, ALEDGE and SCU research rasters were preserved and reopened against the same hash-pinned registered lattice. Their respective measured overlaps are 99.9549%, 99.3241% and 99.8514%; all fail the literal rule. Their NaN twins preserve the same dot masks. See [parallel integration](parallel-integration.md).
- Withdrew TTC's hard-coded, unmeasured holdout claims and the TTC/SCU promotion claims; labeled other parallel reports as not independently reproduced and their private evaluators as noncompliant with the requested shared-tool protocol. No prior portal failure is diagnosed.
- Replaced conflicting public submit instructions with a no-submit decision, corrected the current parallel cards, kept earlier source/report versions in Git history, and guarded legacy generators, partial uniqueness checks and site rebuilders so they cannot silently republish unsupported approvals. Inspector-compatible entry points now require a sample and explicitly do not authorize submission.
- The bridge sample and labels now exist in the merged repository as owner mirrors, not authenticated organizer data. The reusable prepared feature stack, frozen comparator and complete registry remain unavailable for this audit.

## Source-watch follow-up

After the first PR merged, the site correctly flagged a new GEMSDOE24 source head. At pinned ref `e65cd19b255fd0edd3067142d08467c65ff5f7f7`, we independently reopened its H-UNIQUE-07 raster: 1,810 of 1,814 dots (99.7795%) are within the lattice halo. Its owner-reported negative HOLDOUT-DTI is 0.001124 (95% CI 0.000860–0.001431; `gems-segment-pooled-v1`, 60,988 withheld); that holdout was not independently rerun. The [owner run card](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/e65cd19b255fd0edd3067142d08467c65ff5f7f7/docs/data/unique_run_card_7.json) also reports a negative verdict. This is concrete evidence that a smaller dot count does not automatically pass novelty.

---

# Review passes — 28 October 2026 (this session)

## Pass 1 — repository and protocol review

- Read the standing brief in `README.md` before touching code and inspected the tracked artifacts, tests, workflows, evidence cards, and the nine-site ledger.
- Re-ran the baseline suite. The first clean audit install failed during test collection because `src/gems_sass2/features.py` imports `skimage.morphology.skeletonize`, while `requirements-audit.txt` and `.github/workflows/ci.yml` did not install `scikit-image`.
- Found a second reproducibility defect: `scripts/submission_writer.py` resolved the default sample to `/tmp/gems_data`, even though this checkout carries the geometry witness in `data/bridge`. The full feature cache and the bridge mirror were also inconsistently named (`.cache/data` versus `.cache/gems_data`).
- Found a provenance defect in `evidence/nine_sites_audit.json` and its site-summary mirror: historical numbers supplied by the prompt/site reports were labeled `ORGANIZER-CONFIRMED` without a bundled submission-page receipt. They are now labeled `USER-REPORTED / UNVERIFIED`; measured values remain `HOLDOUT-DTI`.

## Pass 2 — fail-closed fixes

- Added the missing pinned audit dependency and CI install entry; added `scikit-image` to both project dependency sets.
- Made `.cache/gems_data` the canonical restored-data location, retained `.cache/data` for compatibility, and added a separate `grid_data_dir()` that may use `data/bridge` only for format inspection/packaging. Model code still cannot mistake the bridge for a training stack.
- Changed `write_submission_pair` to reject NaN, Inf, negative, and greater-than-one predictions instead of silently clipping them. This directly protects against the portal error `Predicted values must be in range [0, 1]`.
- Added `scripts/submission_preflight.py`, which emits JSON with separate `ok_to_download` and `ok_to_submit` fields. It verifies saved bytes, the run-card hash, note length, and one-file ZIP contents, and returns a non-zero code when selector authorization is absent.
- Replaced the no-op `scripts/prepare_data.py` with a geometry/hash receipt that fails closed when core files are absent or misaligned. Updated the download helper to distinguish the official login-walled source from explicitly non-authenticated public owner mirrors.
- Corrected the HVFD run card and Pages copy so `promote` means research-artifact promotion only; the current selector decision remains `OK TO DOWNLOAD: YES` and `OK TO SUBMIT: NO`.

## Pass 3 — automated verification and handoff

- `python -m pytest -q` with the audit environment: **77 passed**, 27 known Rasterio deprecation warnings.
- `node --check docs/assets/app.js && npm run test:site`: **all site scenarios passed** (`ok`, `changed`, `limited`, `missing`). `git diff --check` and Python compilation also pass.
- Revalidated the committed HVFD-EXP3 `-zeros.tif` against the tracked bridge: **13/13 local checks**, all 12,279,160 cells finite float32 in `[0,1]`, exact geometry, zero mapped-catalogue positives, 37,654 positive dots. This is local format evidence, not organizer acceptance.
- Ran the new preflight: `OK TO DOWNLOAD; DO NOT SUBMIT`; the only blocking reason is the absent explicit weekly-slot selector authorization. No experiment beyond the recorded three, no new external data claim, and no weekly submission slot was spent in this review pass.

## Outstanding, independently verified blockers

1. The full `training_features.tif`/external cache is absent from this checkout; the prior HVFD/XGHF experiment receipts are saved artifacts and cannot be honestly re-run here.
2. The current registry is not provably complete, and the literal space-filling calibration-lattice rule mathematically blocks the 37,654-dot candidates. A selector may not be inferred from a holdout win.
3. No DrivenData submission-page receipt or current account quota is available. Any future live number must be copied from the portal and labeled `ORGANIZER-CONFIRMED`; every projection remains a projection.
