# GEMS Field Notes

**Current decision: DO NOT SUBMIT. No new TIFF or leaderboard estimate was produced.** The checked-out repository initially contained only this README. The supplied parallel-run protocol has no single assigned method paragraph, and independent checks found both a literal registry conflict and defects in the shared tools. Zero geological experiments and zero competition slots were used in this session.

- [Decision site and nine-site table](https://sassnarep3-star.github.io/GEMSDOESASS2/)
- [Executive summary and future upload instructions](docs/executive-summary.html)
- [Ranked geological hypotheses and champion analysis](docs/research.html)
- [Sources and provenance](docs/sources.html)
- [Run card](docs/data/run-card.json) · [independent historical-raster audit](docs/data/audit.json) · [shared-tool probes](docs/data/upstream-check.json) · [user-reported historical ledger](docs/data/user-reported-ledger.csv)

## Starting point for every session

The project’s mission is to develop a **new, genuinely unique fault-prediction GeoTIFF** capable of competing in the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/), without copying a prior entry or presenting a proxy as an organizer score. A useful result must be reproducible, automatically inspected, scientifically justified, and honest about its limits. The immediate prediction target is **faults** indicative of geothermal resources—not direct detection of geothermal vents. See the [official problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).

**Core values:** Maximize P(Win) by protecting scarce opportunities and weighing evidence, risk and tradeoffs. Own the Outcome by fixing or reporting defects, testing end to end, and treating negative results as deliverables. Never turn missing evidence into an approval. The instructions below preserve the essential operational parts of the user request; they are **not a verbatim archive of the entire repeated prompt**.

### Parallel-run protocol (user supplied)

1. **LANE.** The lane is the single method paragraph assigned to the session. If rank-correlation with any registry raster exceeds 0.90, or more than 70% of dots fall within 3 px of one registry raster’s dots, log a duplicate and stop. Check the surface before placement **and** the final dots. The present prompt did not identify a single method paragraph; a speculative hypothesis is not an assignment.
2. **REUSE, DON’T REBUILD.** Use the template’s cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Hold out whole fault segments with a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly; pool DTI with α=0.2, β=0.8 and a 300 m triangular kernel. Fix an incorrect shared tool once upstream and report it; never maintain a private evaluator fork.
3. **LABEL EVIDENCE.** A measured `HOLDOUT-DTI` needs its evaluator version, number of withheld positives and 95% CI. An `ORGANIZER-CONFIRMED` result requires an actual submission-page receipt. A projection is never a score. Unverified user reports must not be relabeled as organizer-confirmed.
4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any result. AUC above 0.90 means leakage until proven otherwise.
5. **RUN CARD.** Record hypothesis, mechanism, named non-fault mimic, holdout/CI, registry correlation and overlap, raster SHA-256, saved-file validation, submission name and ≤140-character note, and verdict `promote` or `negative`. A negative result is a deliverable.
6. **BUDGET.** Stop after three experiments or two hours. A separate selector, not the scientific run, chooses whether to spend a real slot. Follow the current limit on the submission page; [DrivenData staff say the website limit prevails](https://community.drivendata.org/t/submission-amount-question/11553/2).

Before implementing, document 3–5 specific geological hypotheses, including layers, transforms, off-catalogue rationale, confounders, difference from prior work, implementation cost and official sources. Validate the top assigned candidate on a spatially blocked holdout against the current comparable best before considering any slot. Record the limits of the available registry and data. The current four **untested proposals** are in [the research brief](docs/research.html#hypotheses); their exclusivity across all sibling projects remains unverified.

## What the independent audit found

The [user-reported ledger](docs/data/user-reported-ledger.csv) transcribes the broader list from the request, including blank values; it is not independently authenticated or a complete live raster registry. The [nine-site table](docs/index.html#nine-sites) compares the requested historical variants from GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Their values are **user-reported, not organizer-confirmed**. All 72 directional dot comparisons among those nine variants exceed the 70% stop; this does not constitute a complete current registry.

The pinned owner-mirror GEMSDOE32 B2 mask equals the GEMSDOE25 dotted mask after removing 6,436 pixels within two pixels of the mirror catalogue. That can plausibly reduce false-positive mass under the metric, but it can also discard nearby new faults; no hidden score components or upload receipt exist to establish causality. Higher performance is possible but unproven.

A separately registered 13GEMSDOE lattice has only 6,649 mirror-footprint pixels outside its 3-px neighborhood. At the historical 37,654-dot budget, at least 31,005/37,654 = 82.34% of candidate dots must overlap it. This is a strict pigeonhole bound, not a measured score or geological-similarity claim. Smaller budgets are **not** automatically unique. Existing GEMSDOE24, 27, 28 and 36 candidates were independently measured at 100.00%, 99.61%, 99.62% and 99.17% overlap, respectively; narrower site-level claims cannot override the literal all-entry rule. Do not move dots merely to evade the test.

The reviewed shared GEMSDOE32 template has open issues: [zero-truth cells lose pooled false-positive mass](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41), [the surface gate ignores preview-dot overlap](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/42), and [the CLI/writer silently binarize probability fields](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37). We reproduced the first two with synthetic unit probes at the recorded source hashes. The upstream repository is read-only for this account, and existing issues already report the defects; no private fork was created.

The owner-mirror sample and historical variants are hash-pinned, **not authenticated organizer downloads**. The official data tab redirects to login. The rejected TIFF and organizer diagnosis for the reported range error were not available. No assumption that zero or NaN outside automatically solves the portal error is justified.

GitHub Pages is configured to publish `main` from `/`; the root `index.html` redirects to the evidence site in `docs/`. The local preview command below serves `docs/` directly.

## Reproduce the audit

Requires Python 3.11, `gh`, and access to the public pinned GitHub files. The audit retrieves historical artifacts only into ignored `.cache/`; it does **not** generate a new candidate or use a competition slot.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-audit.txt
.venv/bin/python scripts/audit_snapshot.py  # fetches and SHA-verifies missing pinned mirrors
.venv/bin/python scripts/build_run_card.py
.venv/bin/python -m pytest -q
npm ci && npm run test:site
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

For a saved TIFF, independently inspect exact bytes against an **authorized** sample (format pass alone is not scientific or slot approval):

```bash
.venv/bin/python scripts/validate_tif.py candidate.tif --sample /path/to/official_sample.tif --out receipt.json
```

The inspector separately reports inside-footprint validity, whole-array finite/range behavior, and whether the mirror-derived outside footprint is masked or NaN. Its combined local policy is intentionally conservative; organizer acceptance remains unverified. It returns exit code 2 for a local policy failure.

To probe the actual shared implementation without copying it, pass a trusted local template checkout to `scripts/check_upstream.py --template-root /path/to/GEMSDOE32`. It returns 2 if either synthetic probe fails. The recorded files match the contents at [`GEMSDOE32@1398109`](https://github.com/buffedlizard55-lab/GEMSDOE32/tree/1398109a23f04a2ace71c1bd2f527cfba87860b5); see [the receipt](docs/data/upstream-check.json). This repository is an audit and static site, **not** a complete train→inference pipeline.

## Next session / limitations

1. Obtain a specifically assigned, non-overlapping lane and the actual reusable prepared cache, frozen same-protocol comparator, and complete current registry; do not invent missing inputs or reconstruct catalogue features from full labels.
2. Resolve the literal lattice/budget conflict without silently exempting registry entries; a smaller, geologically justified budget remains a hypothesis, not a uniqueness pass.
3. Have the upstream owner fix the shared evaluator and surface gate, then rerun the synthetic probes. Do not trust historical holdout results affected by untested edge cases.
4. Use authenticated competition data and sample, run feature-alone canaries and matched buffered whole-segment holdouts with paired spatial 95% intervals, then measure both stages of registry uniqueness.
5. Only after an independently audited TIFF and separate selector approval should a file and short note be offered for upload. Preserve the organizer receipt and disclose generative-AI assistance as the [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) require.

The GitHub Pages source-watch checks repository heads only; it is not a live DrivenData submission feed and does not certify complete coverage. The two historical leaderboard figures supplied in the prompt are not current guarantees. The official public leader observed on 27 October 2026 was 0.4544; see the [live leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) for changes.
