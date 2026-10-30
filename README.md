# GEMSDOESASS2 — auditable geothermal fault discovery

## 🚦 Current decision (verified 2026-10-30): DOWNLOAD READY — SUBMISSION BLOCKED

| Question | Answer |
|---|---|
| Can I download the TIF? | **Yes.** [`gemsdoesass2-sparse-blind-conduit-22163-…-zeros.tif`](docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif) (123 KB; SHA-256 `65e3a775ad8b3fd3f3c55a501c84d48d05554219065cad69fa9ebfb54d572661`). Float32, EPSG 32611, 100 m, values in [0, 1], 22,163 dots. |
| Can I submit it now? | **No.** It fails the protocol's lattice rule: **99.74%** of its dots lie within 3 px of the 13GEMSDOE registry lattice (limit 70%). Receipt: [`docs/data/gate-and-lineage-recheck.json`](docs/data/gate-and-lineage-recheck.json). |
| What unblocks it? | An owner ruling on the lattice rule. Options A/B/C are on the [front page](docs/index.html). Any interior dot set fails the literal rule, because the lattice's 3 px halo covers all but 6,649 footprint cells, and those are edge cells. |
| Name | `GEMSDOESASS2-SPARSE-BLIND-CC522684` |
| Note (≤140 chars) | `GEMSDOESASS2 sparse-blind-conduit 22163d B=2 sep3 \| off-catalogue blind faults \| cc522684 \| research` |
| Estimated leaderboard score | **NOT ESTIMABLE.** No organizer receipt, no valid holdout. |

**Verdict: NEGATIVE / research only. OK to submit: NO. DO NOT SUBMIT.** Full-registry uniqueness is not established.

**Corrections (2026-10-30):** the earlier card and README said "OK to download and submit", based on a 70% test that left out the 13GEMSDOE lattice. That claim is withdrawn; the card now reads `blocked-owner-ruling`. The zeros file was checked against the official rules: outside cells are masked, with raw value 0, and the NaN twin fails the whole-array [0, 1] check. See [IRREGULARITIES.md](IRREGULARITIES.md) (IR-S-15 to IR-S-24).

**Links:** [current review run card](evidence/review_run_card_20261030.json) (from main) · [front page and nine-site table](docs/index.html) · [how to submit](docs/executive-summary.html) · [run card](docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-audit.json) · [research and next steps](research/2026-10-30-review.md)

---

## 📋 STANDING PROJECT PROMPT — read at the start of every session

Review the repository. Focus on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36; maintain an executive summary showing each site's historical best, file, score evidence and novelty. The highest urgency is to **generate an original, validated competition GeoTIFF, not copy an old submission**; make its download, unique name, ≤140-character note and eligibility unambiguous. Estimate performance only with evidence, distinguish a holdout from an organizer score, and never invent a projection. A local format pass alone is not submission approval. Study the reported 0.2778 GEMSDOE32 file, use official sources, propose 3–5 materially distinct geological hypotheses before implementation, check feature leakage and validate the best on a buffered spatial holdout before spending a slot. Maintain a simple GitHub Pages site and step-by-step submission guide; diagnose the user's range-error report only if its rejected bytes and response are actually available.

### Parallel-run protocol (operative text)

1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds **0.90**, or more than **70%** of your dots fall within **3 px** of one registry raster's dots, log a duplicate and stop. Check the surface before placement and the final dots. The supplied prompt references a method paragraph but does not actually contain one; do not present a self-assigned lane as user-assigned.
2. **REUSE, DON'T REBUILD.** Use the shared template's cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Hide whole fault segments with a buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and score pooled DTI (α 0.2, β 0.8, 300 m triangular kernel). Fix a shared defect once upstream; never keep a private evaluator fork.
3. **LABEL NUMBERS.** Results are `HOLDOUT-DTI` with evaluator version, withheld positives and 95% CI, or `ORGANIZER-CONFIRMED` from a submission-page receipt. Owner/user reports must remain explicitly unverified; a projection is never a score.
4. **LEAKAGE CANARY.** Test each feature alone on holdout; AUC above 0.90 is leakage until disproved.
5. **RUN CARD.** End with one JSON card containing hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, registry correlations/overlaps, raster SHA-256, saved-byte validator output, submission name, note of at most 140 characters and `promote`/`negative` verdict. Negative results are deliverables.
6. **BUDGET.** Stop after three experiments or two hours. Do not pick a real submission: promotion to a weekly slot is a separate selector step, subject to the allowance on the submission page.

### Nine-site executive summary (verified 2026-10-30)

Every focus-site file was downloaded from its pinned commit and matched its SHA-256 pin. Scores are USER-REPORTED / UNVERIFIED. Estimated score is NOT ESTIMABLE for every row. Full table: [docs/index.html#nine](docs/index.html#nine) · [CSV](docs/data/focus-sites-verified.csv).

| Site | Reported best (USER-REPORTED) | Best file (research reference) | Unique among the nine? | Submit now? |
|---|---|---|---|---|
| GEMSDOE24 | 0.2477 | `gems24-h25-1-dotted-h19-5-d1-5-…-allfinite.tif` | No · 100.0% vs GEMSDOE25 | No |
| GEMSDOE25 | 0.2600 | `gems25-dotted-h19-5-d2-8-…-zeros.tif` | No · 100.0% vs GEMSDOE24 | No |
| GEMSDOE27 | 0.2449 | `gems27-topo-gap-closure-…-allfinite.tif` | No · 98.0% vs GEMSDOE24 | No |
| GEMSDOE28 | 0.2710 | `gems28-h36-1-rung30-blind-r1-…-allfinite.tif` | No · 100.0% vs GEMSDOE24 | No |
| GEMSDOE30 | 0.2600 | `gemsdoe30-d28-poisson300m-offcat-44090-…-91eae1ca.tif` | No · 100.0% vs GEMSDOE24 | No |
| GEMSDOE31 | 0.2708 | `gemsdoe31-h27-4-solo-d28-…-allfinite.tif` | No · 100.0% vs GEMSDOE24 | No |
| GEMSDOE32 | **0.2778** (highest) | `gemsdoe32-h33-h33-2-b2-…-zeros.tif` | No · pixel-exact subset of GEMSDOE25 | No |
| GEMSDOE33 | 0.2632 | `GEMSDOE33-h33d-analog-tip-stepover-r30-…tif` | No · 99.7% vs GEMSDOE27 | No |
| GEMSDOE36 | 0.2750 | `gemsdoe36-anderson-geothermal-pinn-38854-…-zeros.tif` | No · 97.6% vs GEMSDOE27 | No |

**Why 0.2778 scored highest, in one paragraph:** GEMSDOE32 is GEMSDOE25's 44,090-dot set minus the 6,436 dots within 2 px of the known catalogue (pixel-exact; [receipt](docs/data/gate-and-lineage-recheck.json)). Under the metric, removing a dot raises DTI only if its hit probability is below α·DTI, about 5.2% here. So the gain means those removed dots were low-yield for new faults. This is an inference from user-reported scores, not a measurement.

**Public leaderboard (fetched 2026-10-30):** top score 0.4544 ([DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)). Your brief's 0.4413 and 0.3195 figures are older or different snapshots; see IRREGULARITIES IR-S-08.

---

## Competition & data (official links for manual review)

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/ · [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) · [data (login)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Rules/submission PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and · GDR: https://gdr.openei.org/submissions/1391
- INGENIOUS: https://gbcge.org/current-projects/ingenious/ · CRS: https://epsg.io/32611 · Metric: https://en.wikipedia.org/wiki/Tversky_index
- Portal format: single-band GeoTIFF (.tif) or .zip containing one GeoTIFF; must match the submission format's CRS, shape and geotransform; optional ≤140-char note.

### Core values

**Maximize P(Win)** — weigh evidence, risks and scarce slots; put the outcome first.
**Own the Outcome** — own results end to end; fix shared tools in the template; report negatives honestly.

### Data access blocker

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from the data tab (verified redirect to login). Local bridge data (`data/bridge/`) provides sample_submission.tif, labels.tif and existing_faults.tif for format validation. Large data and `.cache` are ignored and do **not** persist with this Git patch.

---

## Navigation

- **[Open the executive dashboard](docs/index.html)**
- **[Submission instructions and nine-site table](docs/executive-summary.html)**
- **[Research, 3-pass review and next steps](research/2026-10-28-review.md)**
- **[Unique-submission run card](evidence/unique_run_card_cc522684.json)**
- **[Full raster audit](docs/data/audit.json)**
