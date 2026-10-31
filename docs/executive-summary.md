# Executive summary — 2026-10-31 decision (merged across parallel sessions)

## ✅ SUBMIT THIS FILE — one promoted card (IR-S-41)

| Item | Value |
|---|---|
| **File to download** | [`docs/downloads/gemsass2-slopetilt-300k-20261031-zeros.tif`](downloads/gemsass2-slopetilt-300k-20261031-zeros.tif) |
| SHA-256 | `b84a4f2642500b9817b946d99db14471f4b935d110b794d2736f643d56f8f7ae` |
| Grid | EPSG:32611 · (3730, 3292) · 100 m · transform `(100,0,243350,0,-100,4508550)` |
| Cells predicted | 37,654 (champion-matched budget) · **0.00 % within 3 px of `labels.tif`** |
| Format gate | **13 / 13** (`src/gems_sass2/submission.py::validate_geotiff`): all 12,279,160 cells finite float32 in [0, 1], `nodata=None`, zero on 60,988 catalogue cells — the permanent fix for the portal error *"Predicted values must be in range [0, 1]"* |
| Uniqueness gate | **PASS vs every genuine raster** — worst 23.0 % within 3 px (candidate→ref direction), max \|ρ\| 0.0086, 24 references incl. all nine focus champions. The literal 70 % clause fails **only** vs the r13 space-filling calibration probe (99.89 %; a random interior placement scores 99.91 % — IR-S3-6, IR-S-37; owner ruling pending) |
| Science gate | recipe-level hide-and-recover **HOLDOUT-DTI 0.0597** [0.0537, 0.0649] vs uniform **0.0439** [0.0394, 0.0481] (+36 %, disjoint CIs, evaluator GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 withheld positives, fold-local visible-only collars); shipped-bytes SGMC-off **0.0770** [0.0715, 0.0827] vs 0.0750 (CIs overlap — not statistically resolved) |
| Leakage canary | PASS — max single-feature symmetric AUC 0.521 (limit 0.90) |
| **Estimated score** | **MODEL ESTIMATE 0.29** (controlled anchor 0.2853, risk band 0.25–0.33) — **not an organizer score** |
| Submission name | `GEMSASS2-SLOPETILT-300K-20261031` |
| Note (≤140 chars) | `ring-habitat blue-noise 37654 dots, 0% within 3px of catalogue, champion-matched budget, unique vs all GEMSDOE site rasters` |
| Run card | [`evidence/s3_run_card_20261031.json`](../evidence/s3_run_card_20261031.json) |

**Verdict: OK TO DOWNLOAD AND SUBMIT.** Weekly slots spent: 0 — promotion is the owner's selector step (cap 3/week).

⚠️ **Scope of the hide-and-recover number (IR-S-34 / IR-S3-7).** The 0.0597 measures the *lane recipe* with the
catalogue collar rebuilt from each holdout cell's visible faults only (protocol rule 2, evaluator mode
`fold_local_visible_only_oof`). The shipped static raster — like every emission that collars the full catalogue —
scores hide-and-recover **0.0 by construction**, because that truth is a subset of `labels.tif`. The shipped-bytes
measurement is the SGMC-off instrument. Do not mix the two scopes in one claim.

## 🅰 Alternate — equally estimated, mutually redundant (promote-alternate)

[`gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif`](downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif)
(sha `c200cecc…beb6`, 37,636 dots, MODEL ESTIMATE 0.2851 [0.24–0.31], SGMC-off 0.0788 [0.0754, 0.0817],
uniqueness over 531 registry rasters max 43.60 %). **Spend at most ONE weekly slot on this pair.**
The selector may substitute the alternate; its audit card is `verdict: promote-alternate` under the
one-promoted-card invariant (IR-S-41).

**Supersedes:** the 2026-10-30 headline `gemsass2-strainridge-offcat-37654d` (sha `6d00f58a…d615`) —
fails the literal uniqueness clause (99.37 % vs the probe) and its HOLDOUT-DTI 0.2244 came from a visible-only
collar variant, not the shipped mask (IR-S-34) — **do not submit it** until reproduced from its saved bytes.
Its score row is otherwise **NOT ESTIMABLE** above the anchor band. Sibling 2026-10-31 artifacts
(H_STEPOVER stepperelay, damage-edge, SCU/XGHF/HVFD/VRC families) are **research only — do not submit**.

## Focus-site table (GEMSDOE24/25/27/28/30/31/32/33/36)

All nine "historical bests" are one lattice family (every pair ≥ 86.7 % of dots within 3 px; GEMSDOE25 ≡ GEMSDOE30
dot sets; GEMSDOE32 is an exact subset of GEMSDOE25 — IR-S-39). Scores are **USER-REPORTED / UNVERIFIED**.
Unique = passes the project's 70 % / 0.90 lane rule against the other focus variants.

| Site | Best submission | File to download | Estimated score | Unique? |
|---|---|---|---|---|
| GEMSDOE24 | h25-1-dotted-h19-5-d1-5 | [allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/a433b430b74b813a9118ebd4ec438b12cbc69f46/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) | 0.2477 | **No** — 100 % overlap w/ GEMSDOE25 |
| GEMSDOE25 | dotted-h19-5-d2-8 | [zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/b4e74b3f9b191fbc214b6447e9ff1f3fa67552c4/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | 0.2600 | **No** — dot-identical to GEMSDOE30 |
| GEMSDOE27 | topo-gap-closure-t-v2-on-d1-5 | [allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/bef7ae8e8f63b69d299c9214c75988c8f5055f9c/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) | 0.2449 | **No** — 91.6 %+ overlap family-wide |
| GEMSDOE28 | h36-1-rung30-blind-r1 | [allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/2c839d10f57ec9b074829e93c84bc39935f52896/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) | 0.2710 | **No** — same lattice family |
| GEMSDOE30 | d28-poisson300m-offcat-44090 | [.tif](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/9c0d637c0171407196b61b780444bc772ce75438/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 | **No** — dot-identical to GEMSDOE25 |
| GEMSDOE31 | h27-4-solo-d28 | [allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/eeb7da54ca4a8ae056f45e5b23eeef586ad79bf2/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) | 0.2708 | **No** — ≥ 93 % overlap family-wide |
| **GEMSDOE32** | **h33-h33-2-b2 — family best** | [zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/400b60d4a6d99f425ee90504e6c4552227556dd1/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | **0.2778** | **No** — 88 %+ overlap family-wide |
| GEMSDOE33 | h33d-analog-tip-stepover-r30 | [.tif](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/efa438d3104893c3e8aedf3817ac22167b1c681a/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 | **No** — ≥ 96 % overlap family-wide |
| GEMSDOE36 | anderson-geothermal-pinn-38854 | [zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/32c2660001d98f6fa9084a0971b3a9d5062d49b9/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 | **No** — ≥ 88 % overlap family-wide |

**Why 0.2778 scored highest among the nine (verified autopsy, knowledge/04):** one Poisson-disk lattice parent
under a one-parameter collar sweep; dots inside the catalogue collar are guaranteed false positives under the
official metric, and GEMSDOE32 spends the smallest share there (5.77 % vs 19.5 %). The score family is a *filing*
improvement, not a geological one. The controlled next increment is **+0.0075** from removing the remaining
contamination at matched budget — the 0.2853 anchor both 2026-10-31 files target. What the public evidence cannot
do is rank the two files against each other on the leaderboard (IR-S-35: every local instrument mis-transfers);
scores outside the anchor band are **NOT ESTIMABLE** from public data.

## How to submit

See [how-to-submit.html](how-to-submit.html) (or [submit.html](submit.html)) for the step-by-step walkthrough.
Download the **`-zeros.tif`** above; paste name `GEMSASS2-SLOPETILT-300K-20261031` and the note above.

## Experiment ledger — 2026-10-31 sessions

| # | Experiment | Result | Receipt |
|---|---|---|---|
| S3 EXP-1 | Thermal-conduit share sweep (GDR 1391 wellsprings + 2 m probes + paleo deposits) | **NEGATIVE** — thermal-ranked loses to uniform on both instruments (0.0287 vs 0.0439; 0.0329 vs 0.0750) | `evidence/exp1_thermal_share_sweep.json` |
| S3 EXP-2 | Placement decision: uniform vs ring habitat × N × softness | **ring-binary-37654 wins**; N=24,000 negative; plateau1 soft = split verdict | `evidence/exp2_placement_decision.json` |
| S3 EXP-3 | Final candidate + 13-check validator + uniqueness + run card | **PROMOTE** (this page) | `evidence/s3_run_card_20261031.json` |
| RMC session | corridor/LOQO placement + score-estimator fit | **NEGATIVE** — targeted placement anti-informative; estimator rejected (LOO MAE 0.152) | `knowledge/10_rmc_negative_lane_receipt.md` |
| H_STEPOVER | stepover dilation emission | **NEGATIVE** — holdout 0.0016 vs uniform 0.0377; research only | `research/2026-10-31-new-hypotheses.md` |
