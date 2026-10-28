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

## Repository review — 28 October 2026

### Pass 1 — establish the current state

- Confirmed the active worktree is `arena/bf7b1641-gemsdoesass2`, clean at start, based on the recorded main commit. The required standing prompt is transcribed in `README.md` and `knowledge/00_standing_prompt.md`.
- Verified that current XGHF evidence is explicitly `ok_to_download=true`, `ok_to_submit=false`, `verdict=negative`. The local GeoTIFF preflight passes against the repository bridge sample (EPSG:32611, 3730×3292, 100 m grid, all finite and in `[0,1]`), but that does not establish organizer acceptance.
- Found two actionable correctness/UI issues: the Python audit lockfile omitted `scikit-image` (test collection failed on a clean audit install), and the old HVFD-EXP3 page still used a green `PROMOTE` badge and displayed an upload-portal button despite the literal calibration-lattice overlap failing the protocol.

### Pass 2 — fix and exercise

- Added the missing direct audit/test dependencies (`scikit-image`, `scikit-learn`, `pyproj`) to `requirements-audit.txt`; updated the second GitHub Actions workflow to install that same file, avoiding drift from the test environment.
- Rewrote the HVFD-EXP3 page to make its negative decision prominent, remove the upload CTA, label its downloads research-only, and state the measured calibration-lattice failure. Updated the home page and README wording to distinguish artifact downloadability from submission clearance.
- Added browser-test assertions that the HVFD page says “DO NOT SUBMIT,” has a negative verdict, and has no “VERDICT: PROMOTE” claim.

### Pass 3 — recheck

- `.venv/bin/python -m pytest -q`: **69 passed** (27 Rasterio deprecation warnings only).
- `npm run test:site`: **4 site scenarios passed**; `node --check docs/assets/app.js`: passed.
- `scripts/validate_tif.py` on the XGHF artifact against `data/bridge/sample_submission.tif`: strict local format pass; its own output retains `organizer_accepted: null` and `ok_to_submit: false`.
- Recomputed SHA-256 for the HVFD and XGHF GeoTIFFs; both agree with their recorded run cards. No new experiment was run and no submission slot was used. The current candidate remains **not cleared for competition submission** because the literal all-registry calibration-lattice test fails and selector authorization is absent.

### Remaining review flags

1. The official authenticated submission sample and account-specific slot allowance/receipt are not available in this checkout; the bridge sample is an owner mirror. Do not describe local preflight as organizer validation.
2. A private/offline current full registry cannot be proven exhaustive solely from pinned repository refs. Retain fail-closed uniqueness until an authorized complete registry and written protocol treatment of calibration probes are supplied.
3. Historical run cards are immutable evidence records and may contain their original `promote` text; the current site must treat those records as superseded where they conflict with the final negative literal gate.
