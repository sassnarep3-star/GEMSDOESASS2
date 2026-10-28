> **Current audit note (2026-10-27):** This is a parallel branch’s deduplicated transcription, not an authenticated source for reported scores or current leaderboard position. Interpret its retrospective claims about all raster families as unverified. No parallel candidate is approved; see [the current review](../research/parallel-integration.md).

# Standing prompt (recorded 2026-10-27, deduplicated — the original message contains the full text twice)

Read this every session before working. It is the project's base specification.

## Mission
- Review the repo. Focus on the highest-scoring submissions from GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36.
- Produce an executive summary per site making it obvious which file to submit for a high leaderboard score, with a table: **file to download · estimated score · unique (yes/no)**.
- **HIGHEST URGENCY: MUST GENERATE A UNIQUE TIF SUBMISSION. DO NOT COPY A PREVIOUS SUBMISSION** (prior files are for learning only). It must be obvious whether the generated TIF is OK to download and submit.
- Inspection/validation must be fully automated through the project — no human inspector.
- Easy one-click download of the submission TIF at the very start of the site.
- Study why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (GEMSDOE32) scored **0.2778** (the focus-site best) at PhD level, and use the answer to generate a unique submission that can beat it.
- Current GEMSDOE leaderboard high: **0.4413**. Current own high to beat: **0.3195**.
- Create an executive-summary subpage explaining exactly how to submit; cure the portal error `"Predicted values must be in range [0, 1]"`; provide a unique name and a ≤140-char note for every file.
- Before implementing, generate 3–5 untried geological hypotheses (layers, physical signature, why it catches a fault missing from USGS/INGENIOUS, how it differs from this repo), rank by expected DTI gain vs cost, and validate the top one on the spatially-blocked holdout before touching a weekly slot.
- Put this prompt in the repo README and re-read it every session. Work line by line from official verified sources with links for manual review; flag irregularities; no hallucinations; multiple passes (implement → review/fix → re-check). Create a PR and merge it; list remaining work and limitations for the next session.

## PARALLEL-RUN PROTOCOL (verbatim)
1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots. *(No method paragraph was actually supplied — IR-SASS2-04; lane SCU self-declared.)*
2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack, evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.
3. **LABEL EVERY NUMBER** as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.
4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.
5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.
6. **BUDGET.** Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

## Competition & data (official links for manual review)
- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/ · [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) · [data (login)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Rules/submission PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and · GDR: https://gdr.openei.org/submissions/1391
- INGENIOUS: https://gbcge.org/current-projects/ingenious/ · CRS: https://epsg.io/32611 · Metric: https://en.wikipedia.org/wiki/Tversky_index
- Portal format: single-band GeoTIFF (.tif) or .zip containing one GeoTIFF; must match the submission format's CRS, shape and geotransform; optional ≤140-char note.

## Full OWNER-REPORTED score ledger (all GEMSDOE sites, as given in the prompt)
| Site | Submission : score |
|---|---|
| GEMSDOE | gems-submission-20260925T001403Z-7f00890a: 0.1563 |
| 6GEMSDOE | gems6_hgb88-topk03_33cec71ff0: 0.0286 |
| GEMSDOE3 | pindrop-v4-nodes: 0.1193 · pindrop-v4-discovery: 0.0830 · pindrop-v4-ridge: 0.1152 |
| GEMSDOE2 | gemsdoe2-dual-family-union: 0.1560 |
| GEMSDOE4 | gems-submission-20260926T163915Z-237f0063: 0.0343 |
| 5GEMSDOE | gems-submission-20260926T175114Z-7f00890a: 0.1563 |
| 7GEMSDOE | lidarscarp-ridge-top2pct: 0.1461 |
| 8GEMSDOE | Hedge-v2_submission: 0.1563 |
| GEMSDOE9 | 2314b599: 0.0107 |
| 11GEMSDOE | gems-structural-area06-v1: 0.0202 |
| 12GEMSDOE | r7-nms3-dem10-scarp: 0.1294 (both variants) |
| 15GEMSDOE | gems-tso1-conj_alteration_mag: 0.0782 |
| 14GEMSDOE | GEMS_r5-geom-horse-ensemble: 0.0020 |
| 17GEMSDOE | F-ensemble-2pct: 0.0187 |
| 18GEMSDOE | H19-C: 0.0297 |
| 19GEMSDOE | h19-4 multiline: 0.1894 · h19-5 powerlaw: 0.1922 |
| GEMSDOE10 | h16: 0.0461 · h20: 0.0921 · H25: 0.1280 · h28-dotted-ridge: 0.1839 |
| 13GEMSDOE | r13-lattice-s5_v2: 0.0904 |
| 16GEMSDOE | h16-1: 0.1855 · h18-3a: 0.0976 · h18-4: 0.0360 |
| GEMSDOE21 | h19-4-reference: 0.1894 |
| 20GEMSDOE | h20-1: 0.1890 · h20-5: 0.1859 |
| GEMSDOE22 | h23-a: 0.1002 · h23-b: 0.0748 |
| GEMSDOE23 | h30-arrangement-matched-habitat: 0.1352 |
| **GEMSDOE24** | **h25-1-dotted-h19-5-d1-5: 0.2477** · gems24-gvc1: 0.0859 |
| **GEMSDOE25** | **dotted-h19-5-d2-8: 0.2600** · gems25-h66-mgd: 0.0742 |
| GEMSDOE26 | dilcond-oof-v1: 0.1223 |
| **GEMSDOE27** | **topo-gap-closure-t-v2-on-d1-5: 0.2449** · gems27-h29 celf: 0.2190 |
| **GEMSDOE28** | **h27-4-r1: 0.2708 · h32-1: 0.2649 · h36-1: 0.2710 · h38-1: 0.2707** · gems28-s18: 0.0217 |
| GEMSDOE29 | efd28-repro: 0.2600 · wormrank-d28: 0.2560 · others 0.0041–0.0532 |
| **GEMSDOE30** | **d28-poisson300m-offcat-44090: 0.2600** · gems30-MSDB1: 0.1462 |
| **GEMSDOE31** | **h27-4-solo-d28: 0.2708** |
| **GEMSDOE32** | **h33-h33-2-b2: 0.2778 (focus-site champion)** |
| **GEMSDOE33** | **h33d-analog-tip-stepover-r30: 0.2632** |
| GEMSDOE34 | h34-scatter: 0.0778 |
| GEMSDOE35 | h35-06: 0.0418 |
| **GEMSDOE36** | **anderson-geothermal-pinn-38854: 0.2750** |
| GEMSDOE37 | h6-physics-dotted-80k: 0.1193 |
| GEMSDOE38 | D-step-3p0: 0.0763 |
| GEMSDOE39–GEMSDOE92 etc. | all ≤ 0.2478 (notable: GEMSDOE49 gate_ortho 0.2376 · GEMSDOE48 h59-cover-ds 0.2296 · GEMSDOE63 cvarlw 0.2303 · GEMSDOE70 p5-dual-submod 0.2478 · GEMSDOE76 ptcf-tiltworm 0.2343 · GEMSDOE73 mcsc-blakely 0.1917 · GEMSDOE82 submodular-punoisyor 0.1886 · GEMSDOE91 lftg 0.1823 · 62GEMSDOE datum-lahontan: 0.0000) |

**Audit correction (2026-10-28):** the score ledger is user-supplied and has no organizer receipts. Only the nine selected pinned variants were measured in the independent audit; no claim is made about every raster or score in the broader list. The pinned GEMSDOE32 B2 mask equals the pinned d2.8 mask after a two-cell catalogue prune. See [current findings](../research/2026-10-28-hypotheses-and-review.md).

## Arena core values
- **Maximize P(Win)** — weigh tradeoffs/risk, put the outcome first; weekly slots are scarce information capital.
- **Own the Outcome** — own results end to end; fix shared tools in the template; report negatives honestly.
