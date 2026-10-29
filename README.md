# GEMSDOESASS2 — auditable geothermal fault discovery

## 🚦 Current decision: **DO NOT SUBMIT**

**No new unique, submission-ready GeoTIFF was generated in this session.** The two most recently promoted research artifacts fail the user's literal registry rule, despite passing a local format inspection. Their historical promotion claims are withdrawn. **Do not upload them or an earlier file to DrivenData.** No weekly submission slot was used.

| Previously generated artifact | Saved-byte 3-pixel overlap against registered lattice | Local format check | Decision |
|---|---:|---|---|
| [HVFD-EXP3 — research only](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif) | 37,617 / 37,654 = **99.9017%** | Pass against owner-mirror sample; not organizer acceptance | **Duplicate; do not submit** |
| [SASS2-XGHF — research only](docs/downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif) | 37,636 / 37,654 = **99.9522%** | Pass against owner-mirror sample; not organizer acceptance | **Duplicate; do not submit** |

The stop threshold is **more than 70%** within 3 pixels of any registry raster. The registered lattice itself is [pinned by SHA-256](research/priority_sources.json), and [the independently reproduced receipt](docs/data/audit.json) reports the exact counts; a concurrent review independently recorded the [same two witness counts](evidence/lattice_recheck_20261028.json). With only 6,649 footprint cells outside its halo, any 37,654-distinct-dot candidate must have at least 31,005 overlapping dots (82.34%); therefore, the prior proposed budget cannot pass the literal rule. This is a lower bound, not a claim that a smaller candidate would be unique. Do not silently exempt the lattice.

**[Open the executive dashboard](docs/index.html)** · **[Submission instructions and nine-site table](docs/executive-summary.html)** · **[Research, 3-pass review and next steps](research/2026-10-28-review.md)** · **[Current negative JSON run card](docs/data/run-card.json)**

The owner-supplied 0.2778 for the GEMSDOE32 champion is **USER-REPORTED / UNVERIFIED**, not a receipt-linked organizer score. No reliable leaderboard estimate for a new candidate is available. The official public leaderboard showed **0.4544** at #1 when checked on 2026-10-28 UTC; that dynamic public observation is not an organizer receipt for any of our files. See the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

---

**Latest review:** [research/2026-10-28-repo-review-3.md](research/2026-10-28-repo-review-3.md) (branch `arena/99eabcc5-gemsdoesass2`). Verified: 111 Python tests pass; the pinned sample, labels and lattice SHA-256 values match the owner repo at the pinned commit; the official leaderboard top is 0.4544. Still **DO NOT SUBMIT** pending an owner ruling on the lattice probe.

## Review addendum — 2026-10-28 (historical branch `arena/6c861f74-gemsdoesass2`, merged)

- **Verdict unchanged: nothing is cleared for submission.** No slot was used. No holdout proxy here estimates a leaderboard score (**Estimated leaderboard score: NOT ESTIMABLE**).
- **Genuine-raster check, no lattice probe** ([evidence/focus_uniqueness_downloads.json](evidence/focus_uniqueness_downloads.json)): SASS2-XGHF **49.84%** (worst |ρ| 0.0443); HVFD-EXP3 **70.58%** against `8GEMSDOE Hedge-v2` (fails, limit 70%); ass2-altedge 49.96% but fails strict format (7,111,787 unmasked values outside the footprint); thermo-tilt 72.52% and scu1 76.50% (both fail).
- **The real decision is an owner ruling on the lattice probe.** The `r13-lattice-s5` probe leaves only 6,649 footprint pixels uncovered. For any candidate with *n* dots, overlap is at least (n − 6,649)/n, which is about 82.3% at n = 37,654. The literal rule can be met only by a file of at most ~22,163 dots placed in those lattice holes, which is not a scientifically meaningful placement. Until the owner rules, SASS2-XGHF stays **research-only, not cleared**.
- **Per-site audit** (main, [evidence/nine_sites_audit.json](evidence/nine_sites_audit.json), verdict *negative*): no focus variant is unique against the nine. Per-site table with receipts: [docs/focus-sites.html](docs/focus-sites.html) (built by `scripts/build_focus_summary.py`).
- **Feature stack:** the 19-band cache is restored from an owner mirror ([evidence/feature_cache.json](evidence/feature_cache.json), [receipt](evidence/data_restoration_20261028.json)). This supersedes the earlier "features unavailable" blocker. No model has been retrained, and no hypothesis has been run.
- **Not done in this session:** leakage canary review of SASS2-XGHF, a 3–5 hypothesis run with holdout validation, and any new candidate TIF. Those need the owner's go-ahead, and they count against the 3-experiment / 2-hour budget.

## 📋 STANDING PROJECT PROMPT — read at the start of every session

Review the repository. Focus on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36; maintain an executive summary showing each site's historical best, file, score evidence and novelty. The highest urgency is to **generate an original, validated competition GeoTIFF, not copy an old submission**; make its download, unique name, ≤140-character note and eligibility unambiguous. Estimate performance only with evidence, distinguish a holdout from an organizer score, and never invent a projection. A local format pass alone is not submission approval. Study the reported 0.2778 GEMSDOE32 file, use official sources, propose 3–5 materially distinct geological hypotheses before implementation, check feature leakage and validate the best on a buffered spatial holdout before spending a slot. Maintain a simple GitHub Pages site and step-by-step submission guide; diagnose the user's range-error report only if its rejected bytes and response are actually available.

### Parallel-run protocol (operative text)

1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds **0.90**, or more than **70%** of your dots fall within **3 px** of one registry raster's dots, log a duplicate and stop. Check the surface before placement and the final dots. The supplied prompt references a method paragraph but does not actually contain one; do not present a self-assigned lane as user-assigned.
2. **REUSE, DON'T REBUILD.** Use the shared template's cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Hide whole fault segments with a buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and score pooled DTI (α 0.2, β 0.8, 300 m triangular kernel). Fix a shared defect once upstream; never keep a private evaluator fork.
3. **LABEL NUMBERS.** Results are `HOLDOUT-DTI` with evaluator version, withheld positives and 95% CI, or `ORGANIZER-CONFIRMED` from a submission-page receipt. Owner/user reports must remain explicitly unverified; a projection is never a score.
4. **LEAKAGE CANARY.** Test each feature alone on holdout; AUC above 0.90 is leakage until disproved.
5. **RUN CARD.** End with one JSON card containing hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, registry correlations/overlaps, raster SHA-256, saved-byte validator output, submission name, note of at most 140 characters and `promote`/`negative` verdict. Negative results are deliverables.
6. **BUDGET.** Stop after three experiments or two hours. Do not pick a real submission: promotion to a weekly slot is a separate selector step, subject to the allowance on the submission page.

The project's core values are **Maximize P(Win)** (weigh evidence, risks and scarce slots) and **Own the Outcome** (verify end to end and correct failures transparently). Work independently, use official sources and explicit caveats, and perform implementation, bug-review and final recheck passes. The deduplicated fuller brief and original user-provided historical ledger are in [knowledge/00_standing_prompt.md](knowledge/00_standing_prompt.md) and [docs/data/user-reported-ledger.csv](docs/data/user-reported-ledger.csv); Git retains earlier reports. These are transcriptions, not organizer receipts.

### Previously proposed lane: XGHF (not user-assigned in this message)

The earlier project proposed combining competition magnetic/gravity/radiometric/geodetic features, cross-gradient collinearity, tilt boundaries and hydrothermal data with visible-only crack-tip fields and anisotropic placement. The earlier implementation and metrics are **historical research**, not a validated current run. [Four within-family candidate hypotheses](research/2026-10-28-hypotheses-and-review.md) specify inputs, transformations, counterexamples, costs and current data limitations; none was tested in this session.

---

## Data restoration and automated checks

This session restored the shared template's 19-band feature raster from an immutable **owner-hosted GitHub mirror**, verified the five part hashes and assembled SHA-256 (`4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`), and invoked the template's band-cache builder. See [restoration receipt](evidence/data_restoration_20261028.json) and [band receipt](evidence/feature_cache.json). The mirror is not an authenticated DrivenData download; only the authenticated sample can establish organizer provenance. Large data and `.cache` are ignored and do **not** persist with this Git patch. Recreate them when needed:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-audit.txt
.venv/bin/python scripts/prepare_data.py --fetch --cache-bands
```

The operation uses `gh` and may download hundreds of MB. It refuses to overwrite conflicting inputs and never approves a submission. The data tab currently [redirects to DrivenData login](https://www.drivendata.org/competitions/306/competition-doe-gems/data/); no credentials are stored here.

```bash
# Saved-byte inspection; format is necessary but not sufficient to submit.
.venv/bin/python scripts/validate_tif.py \
  docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif \
  --sample data/bridge/sample_submission.tif

# Reproduce the pinned historical-raster audit (uses GitHub and ignored cache).
.venv/bin/python scripts/audit_snapshot.py
.venv/bin/python -m pytest -q
npm ci && npm run test:site
```

Legacy private evaluators, writers, generators and site rebuilders now stop rather than publish unsupported approvals. The vendored grid and writer have been restored to their pinned shared-source bytes; the upstream writer's zero-outside encoding does not satisfy this project's deliberately conservative external-mask policy. This is a local preflight interpretation, not a claim of organizer rejection.

## What blocks the next real candidate

- The exact assigned lane and complete current registry are not supplied. The literal lattice rule defeats the earlier 37,654-dot budget; no exemption or separate selector approval is implied.
- The latest checked shared GEMSDOE32 code still fails two synthetic probes: [zero-truth pooled false positives](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41) and [surface-stage dot overlap](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/42). We have read-only access to that repository and have not maintained a private fix. The earlier XGHF private evaluator has the same empty-truth accounting pattern. [Probe receipt](docs/data/upstream-check.json).
- A frozen, fold-local, same-protocol incumbent and complete registry/surface inventory are unavailable. Earlier parent-raster comparisons can leak full-catalogue information and do not establish a leaderboard improvement.
- Authenticated DrivenData sample/data, submission receipts, private test truth and the account's current weekly allowance are unavailable here. The [published rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) and [staff quota clarification](https://community.drivendata.org/t/submission-amount-question/11553/2) should be checked for the live account. Generative-AI assistance must be disclosed as required by the rules.

Address these blockers before running the top proposal, and only then use a separate selector decision. This repository cannot independently modify all nine external sites; their historical results are centralized here with pinned sources and freshness warnings.
