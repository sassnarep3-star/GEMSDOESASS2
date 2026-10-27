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
