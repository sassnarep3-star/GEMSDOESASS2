# GEMSDOESASS2 — auditable geothermal fault discovery

## 🚦 Current decision: **NOT CLEARED FOR SUBMISSION — no file is approved**

Every GeoTIFF in this repository is **research material**. The most recent unique candidate,
`gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif`, passes the
shared format validator and the peer-uniqueness gates, but **fails the literal lane duplicate
rule**: 99.74% of its dots lie within 3 px of the pinned 13GEMSDOE lattice (limit 70%).
Earlier pages that said "OK TO DOWNLOAD AND SUBMIT" are withdrawn
([IR-30-01](IRREGULARITIES.md)).

| Artifact | Shared format (validate_tif.py) | Peer overlap (max vs 18 registry rasters) | Literal lattice gate | Verdict | OK to download & submit? |
|---|---|---|---|---|---|
| `…sparse-blind-conduit-22163-…-cc522684-zeros.tif` | PASS (11/11 checks) | 41.29% (< 70%) · \|ρ\| 0.0134 (< 0.90) — *focus-site scope* | **FAIL — 99.74%** | **negative** | **NO — not cleared** |

Scope note: the 41.29% figure is measured against the nine focus-site rasters plus local
variants (18 rasters). Against the full public corpus (2,282 unique competition-shaped rasters
from 113 GEMS-named repos, [`evidence/focus_uniqueness_full_registry_20261030.json`](evidence/focus_uniqueness_full_registry_20261030.json))
the candidate is **not unique**: its worst genuine peer is GEMSDOE86's `gems86-gmc-linepost-90568d`
at **98.41%** within 3 px (limit 70%). Space-filling rasters — the 13GEMSDOE lattice, dense
`top37654` masks with 5.1M positive pixels, and continuous probability surfaces (103 files) —
cover 100% of any candidate's dots and are excluded from the peer gate by measured dot density
(IR-30-10). Every scope fails the literal lattice test.

- **Why it cannot pass as the rule is written:** only 6,649 of the 5,167,373 footprint cells lie
  more than 3 px from the lattice, and every one of them is within 2.24 px of the study-area
  border ([receipt](evidence/lattice_gate_recheck_20261030.json)). Clearing 70% would require
  ~30% of a submission's dots on the border. **Owner ruling needed** before any interior
  placement can clear the gate. This is a project-protocol rule, not an organizer rule.
- **SHA-256:** `65e3a775ad8b3fd3f3c55a501c84d48d05554219065cad69fa9ebfb54d572661`
- **Run card (verdict negative):** [evidence/unique_run_card_cc522684.json](evidence/unique_run_card_cc522684.json)
- **No HOLDOUT-DTI exists** for any local candidate: the environment has no authenticated
  organizer labels, so no score estimate may be written. No weekly submission slot was used,
  and none can be used from this environment (DrivenData requires login).

---

## 📋 STANDING PROJECT PROMPT — read at the start of every session

Read this every session before working. It is the project's base specification. The full
transcript, including the complete owner-reported score ledger, is in
[knowledge/00_standing_prompt.md](knowledge/00_standing_prompt.md).

### Mission

- Review the repo. Focus on the highest-scoring submissions from GEMSDOE24, 25, 27, 28, 30,
  31, 32, 33, 36. Maintain an executive summary per site with a table: **file to download ·
  estimated score · unique (yes/no)**.
- **HIGHEST URGENCY: MUST GENERATE A UNIQUE TIF SUBMISSION. DO NOT COPY A PREVIOUS
  SUBMISSION** unless it is for learning/education. It must be obvious whether the generated
  TIF is OK to download and submit.
- Inspection/validation must run through the project with no human inspector. The site must
  offer an easy one-click submission TIF download, and an executive-summary subpage explaining
  exactly how to submit (file, unique name, ≤140-character note).
- Study why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (GEMSDOE32) scored **0.2778** at
  PhD level and use the answer to generate a unique submission that can beat it. Current
  GEMSDOE leaderboard high cited in the brief: 0.4413; own high to beat: 0.3195. (Live public
  leaderboard 2026-10-30: #1 0.4544, #22 0.3334 — snapshots, not receipts.)
- Before implementing, generate 3–5 untried geological hypotheses (layers, physical signature,
  why it catches a fault missing from USGS/INGENIOUS, how it differs from this repo), rank by
  expected DTI gain vs cost, and validate the top one on a spatially-blocked holdout before
  touching a weekly submission slot. If new external data is needed, name the free official
  source and verify it is obtainable first.
- Work line by line from official verified sources with links for manual review; flag
  irregularities; no hallucinations; multiple passes (implement → review/fix → re-check).
  Create a PR and merge it; list remaining work and limitations for the next session.
- Diagnose the reported portal error `"Predicted values must be in range [0, 1]"` only if the
  rejected bytes and the portal response are available (they are not; see IR-09).
- Design for a top-of-leaderboard result: deep research on the science of geothermal
  vents/faults, official sources stored in the knowledge base, contrarian but grounded
  hypotheses, and an automated current feed instead of manual checking.

### Parallel-run protocol (operative text)

1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If your raster's
   rank-correlation with any registry raster exceeds **0.90**, or more than **70%** of your
   dots fall within **3 px** of one registry raster's dots, you have drifted into another lane:
   log it as a duplicate and stop. Check the surface before placement AND the final dots. The
   supplied prompt references a method paragraph but does not actually contain one; do not
   present a self-assigned lane as user-assigned.
2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack, `evaluate_holdout.py`
   and `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with
   a buffer, derive every catalogue-based feature only from the visible faults, mask visible
   faults pixel-exactly, score pooled DTI (α 0.2, β 0.8, 300 m triangular kernel). If a shared
   tool is wrong, fix it once in the template and report it; never keep a private fork.
3. **LABEL EVERY NUMBER** as `HOLDOUT-DTI` (evaluator version, withheld positives, 95% CI) or
   `ORGANIZER-CONFIRMED` (copied from a submission-page receipt). A projection is never
   written as a score. Owner/user reports stay explicitly unverified.
4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any result. AUC
   above **0.90** means leakage until proven otherwise.
5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; named non-fault mimic; holdout
   DTI + CI; correlation/overlap vs registry; raster SHA-256; validator output (no NaN inside
   the footprint, values in [0,1], CRS/shape/transform match); submission name; note of at
   most 140 characters; verdict `promote`/`negative`. Negative results are deliverables.
6. **BUDGET.** Stop after **3** experiments or **2** hours. Do not pick submissions:
   promotion to a real slot is a separate selector step, within the weekly cap shown on the
   submission page.

### Core values

**Maximize P(Win)** — weigh evidence, risks and scarce slots; put the outcome first.
**Own the Outcome** — own results end to end; fix shared tools in the template; report
negatives honestly.

---

## Nine-site executive summary (table)

All nine historical values are **USER-REPORTED / UNVERIFIED** (no organizer receipt ties a
score to the pinned bytes). "Unique?" is measured against the other eight focus sites with the
protocol's 3 px dot rule ([pairwise receipt](evidence/focus_pairwise_matrix_20261030.json)).
No defensible leaderboard estimate exists for any file; the estimate column says so rather
than inventing a projection.

| Site | Historical value | File (pinned, research-only) | New score estimate | Unique? |
|---|---|---|---|---|
| GEMSDOE32 | **0.2778** · user-reported | [h33-h33-2-b2 … e5eb6e7e zeros](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/400b60d4a6d99f425ee90504e6c4552227556dd1/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | Unavailable · no defensible estimate | **No** · 100.00% within 3 px of GEMSDOE25 |
| GEMSDOE36 | 0.2750 · user-reported | [anderson-geothermal-pinn … 9b9ea4e6 zeros](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/32c2660001d98f6fa9084a0971b3a9d5062d49b9/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | Unavailable · no defensible estimate | **No** · 97.58% within 3 px of GEMSDOE27 |
| GEMSDOE28 | 0.2710 · user-reported | [h36-1-rung30-blind-r1 … allfinite](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/2c839d10f57ec9b074829e93c84bc39935f52896/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) | Unavailable · no defensible estimate | **No** · 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE31 | 0.2708 · user-reported | [h27-4-solo-d28 … allfinite](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/eeb7da54ca4a8ae056f45e5b23eeef586ad79bf2/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) | Unavailable · no defensible estimate | **No** · 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE33 | 0.2632 · user-reported | [h33d-analog-tip-stepover … cb490425926e](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/efa438d3104893c3e8aedf3817ac22167b1c681a/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | Unavailable · no defensible estimate | **No** · 99.71% within 3 px of GEMSDOE27 |
| GEMSDOE25 | 0.2600 · user-reported | [dotted-h19-5-d2-8 … zeros](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/b4e74b3f9b191fbc214b6447e9ff1f3fa67552c4/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | Unavailable · no defensible estimate | **No** · identical dots to GEMSDOE30 |
| GEMSDOE30 | 0.2600 · user-reported | [d28-poisson300m-offcat … 91eae1ca](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/9c0d637c0171407196b61b780444bc772ce75438/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | Unavailable · no defensible estimate | **No** · identical dots to GEMSDOE25 |
| GEMSDOE24 | 0.2477 · user-reported | [h25-1-dotted-h19-5-d1-5 … allfinite](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/a433b430b74b813a9118ebd4ec438b12cbc69f46/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) | Unavailable · no defensible estimate | **No** · 100.00% within 3 px of GEMSDOE25 |
| GEMSDOE27 | 0.2449 · user-reported | [topo-gap-closure-t-v2 … allfinite](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/bef7ae8e8f63b69d299c9214c75988c8f5055f9c/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) | Unavailable · no defensible estimate | **No** · 98.02% within 3 px of GEMSDOE24 |

Lineage (measured, exact-pixel set inclusion): the nine files are nested subsets of one
parent — GEMSDOE32's 37,654 dots are an exact subset of GEMSDOE25's 44,090, and the 6,436
removed dots are exactly the parent's dots within 2 px of the USGS catalogue. GEMSDOE25 and
GEMSDOE30 have identical dot sets. Under the protocol's lane rule none of the nine is unique,
and resubmitting any of them is a duplicate.

**How to submit (once a candidate is cleared by the separate selector):** see
[docs/executive-summary.html](docs/executive-summary.html) for the step-by-step guide, the
exact file to download, the unique name and the ≤140-character note.

---

## Competition & data (official links for manual review)

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/ · [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) · [data (login)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution (notebook @ `aebe92f`)
- Rules/submission PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- GeoDAWN (USGS ScienceBase, DOI 10.5066/P93LGLVQ): https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7 · GDR: https://gdr.openei.org/submissions/1391
- INGENIOUS: https://gbcge.org/current-projects/ingenious/ · CRS: https://epsg.io/32611 · Metric: https://en.wikipedia.org/wiki/Tversky_index
- Portal format: single-band GeoTIFF (.tif) or .zip containing one GeoTIFF; must match the submission format's CRS, shape and geotransform; optional ≤140-char note; values are probabilities in [0,1]; NaN/null outside the bounds is allowed by the spec (knowledge/03).

### Data access blocker

❌ No DrivenData auth → cannot auto-download `training_features.tif`, `labels.tif`,
`sample_submission.tif`, `1m_DEM_links.csv` from the data tab (verified redirect to login).
Local bridge data (`data/bridge/`) provides `sample_submission.tif`, `labels.tif` and
`existing_faults.tif` (labels and existing_faults are byte-identical — IR-S-05) for format
validation only. Large data and `.cache` are git-ignored and do not persist.

---

## Navigation

- **[Open the executive dashboard](docs/index.html)** (GitHub Pages)
- **[Executive summary + how to submit](docs/executive-summary.html)**
- **[Ranked hypotheses (H1–H5)](research/2026-10-30-hypotheses-ranked.md)**
- **[Run card (verdict: negative)](evidence/unique_run_card_cc522684.json)**
- **[Lattice gate recheck receipt](evidence/lattice_gate_recheck_20261030.json)** · [pairwise focus-site matrix](evidence/focus_pairwise_matrix_20261030.json) · [full-registry uniqueness](evidence/focus_uniqueness_full_registry_20261030.json)
- **[Irregularities ledger](IRREGULARITIES.md)** · [official metric & format](knowledge/03_official_metric_and_submission_format.md) · [0.2778 autopsy](knowledge/04_gemsdoe32_0-2778_autopsy_verified.md)
