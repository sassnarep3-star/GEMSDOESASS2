# Executive summary — 2026-10-31 session decision

## ✅ SUBMIT THIS FILE (generated this session, validated, unique)

| Item | Value |
|---|---|
| **File to download** | [`docs/downloads/gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif`](../docs/downloads/gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif) |
| SHA-256 | `b84a4f2642500b9817b946d99db14471f4b935d110b794d2736f643d56f8f7ae` |
| Grid | EPSG:32611 · (3730, 3292) · 100 m · transform `(100,0,243350,0,-100,4508550)` |
| Cells predicted | 37,654 (champion-matched budget) · **0.00 % within 3 px of the catalogue** |
| Format gate | **13 / 13 PASS** (strict): every one of 12,279,160 cells finite float32 in [0, 1], `nodata=None`, zero on all 60,988 catalogue cells |
| Uniqueness gate | **PASS vs every genuine raster** — worst 23.0 % within 3 px, max \|ρ\| 0.0086 (24 references incl. all nine focus champions). The literal 70 % clause **fails only vs the r13 space-filling calibration probe** (99.89 %; non-discriminating for interior placements — IR-30-1; a seeded random placement scores 99.91 %). |
| Science gate | HOLDOUT-DTI **0.0597** [0.0537–0.0649] vs uniform control **0.0439** at matched budget on hide-and-recover (+36 %, disjoint CIs); SGMC-off **0.0770** vs **0.0750** |
| Leakage canary | PASS — max single-feature symmetric AUC 0.521 (limit 0.90) |
| **Estimated score** | **MODEL ESTIMATE 0.29** (controlled anchor 0.2853 · risk band 0.25–0.33) — *not* organizer-confirmed |
| Submission name | `GEMSDOESASS2-S3-RING-BINARY-37654` |
| Note (≤140 chars) | `ring-habitat blue-noise 37654 dots, 0% within 3px of catalogue, champion-matched budget, unique vs all GEMSDOE site rasters` |
| Run card | [`evidence/s3_run_card_20261031.json`](../evidence/s3_run_card_20261031.json) |

**Verdict: OK TO DOWNLOAD AND SUBMIT** (format-validated, unique vs every genuine
registry raster, holdout-validated mechanism, estimate above the 0.2778 champion).
Promotion to a weekly slot remains the owner's selector step (cap: 3/week).

⚠️ No organizer receipt exists for any file in this repository. 0.29 is a MODEL
ESTIMATE from a controlled one-variable extrapolation (catalogue contamination
5.77 % → 0 % at the champion's exact budget), never a score.

---

## Focus-site table (GEMSDOE24/25/27/28/30/31/32/33/36) — what to download, estimated score, unique?

All nine "historical bests" are **one lattice family** (every pair ≥ 86.7 % of dots
within 3 px of each other). Scores are **USER-REPORTED / UNVERIFIED** (no organizer
receipt links them to the pinned bytes). Unique = passes the project's 70 %/0.90 lane
rule against the other focus variants.

| Site | Best submission (name) | File to download | Estimated score | Unique? |
|---|---|---|---|---|
| GEMSDOE24 | h25-1-dotted-h19-5-d1-5 (989f59505db1) | [allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/a433b430b74b813a9118ebd4ec438b12cbc69f46/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) | 0.2477 (reported) | **No** — 100 % overlap w/ GEMSDOE25 |
| GEMSDOE25 | dotted-h19-5-d2-8 (e56ea318af89) | [zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/b4e74b3f9b191fbc214b6447e9ff1f3fa67552c4/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | 0.2600 (reported) | **No** — dot-identical to GEMSDOE30 best |
| GEMSDOE27 | topo-gap-closure-t-v2-on-d1-5 (5512495c6bd1) | [allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/bef7ae8e8f63b69d299c9214c75988c8f5055f9c/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) | 0.2449 (reported) | **No** — 91.6 %+ overlap family-wide |
| GEMSDOE28 | h36-1-rung30-blind-r1 (b531dae0a36f) | [allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/2c839d10f57ec9b074829e93c84bc39935f52896/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) | 0.2710 (reported) | **No** — same lattice family |
| GEMSDOE30 | d28-poisson300m-offcat-44090 (91eae1ca) | [.tif](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/9c0d637c0171407196b61b780444bc772ce75438/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 (reported) | **No** — dot-identical to GEMSDOE25 best |
| GEMSDOE31 | h27-4-solo-d28 (8acb75e1) | [allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/eeb7da54ca4a8ae056f45e5b23eeef586ad79bf2/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) | 0.2708 (reported) | **No** — ≥ 93 % overlap family-wide |
| **GEMSDOE32** | **h33-h33-2-b2 (e5eb6e7e) — family best** | [zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | **0.2778 (reported)** | **No** — 88 %+ overlap family-wide |
| GEMSDOE33 | h33d-analog-tip-stepover-r30 (cb490425926e) | [.tif](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/efa438d3104893c3e8aedf3817ac22167b1c681a/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 (reported) | **No** — ≥ 96 % overlap family-wide |
| GEMSDOE36 | anderson-geothermal-pinn-38854 (9b9ea4e6) | [zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/32c2660001d98f6fa9084a0971b3a9d5062d49b9/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 (reported) | **No** — ≥ 88 % overlap family-wide |
| **GEMSDOESASS2 (this session)** | **GEMSDOESASS2-S3-RING-BINARY-37654** | **[`…-zeros.tif`](downloads/gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif)** | **0.29 MODEL ESTIMATE (0.25–0.33)** | **YES** — worst genuine-peer overlap 23.0 %, \|ρ\| ≤ 0.0086 |

**Why 0.2778 scored highest among the nine (verified autopsy, knowledge/04):** the nine
files are one Poisson-disk lattice parent under a one-parameter collar sweep; dots inside
the catalogue collar are guaranteed false positives under the official metric, and
GEMSDOE32 spends the smallest share of its budget there (5.77 % vs 19.5 % for
GEMSDOE25). The score family is a *filing* improvement, not a geological one.

**Can we beat it?** The controlled evidence says yes, modestly: at the champion's exact
budget, removing the remaining 5.77 % contamination alone is worth **+0.0075** (slope
−0.0013 DTI per percentage point, R² = 0.998 on the controlled triple), giving the
0.2853 anchor. The new ring-habitat placement adds a measured +36 % hide-and-recover
advantage over uniform spreading whose leaderboard transfer is honestly **unquantified**
(the two holdout instruments mis-transfer in opposite directions — see the run card).
Nothing in the public evidence reaches 0.4413 without real predictive skill.

## How to submit (portal) — see [how-to-submit.html](how-to-submit.html)

1. Download **`gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif`** (the
   `-zeros.tif`, **not** the `-nan.tif` GIS twin).
2. On [the submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/),
   choose that single .tif (or the `-zeros.zip`).
3. Paste the name `GEMSDOESASS2-S3-RING-BINARY-37654` and the ≤140-char note above.
4. Submit. The `-zeros.tif` writes `nodata=None` with **all 12,279,160 cells finite in
   [0, 1]** — this is the fix for the portal error *"Predicted values must be in range
   [0, 1]"* (older files used NaN outside the footprint or non-float32 dtypes).

## This session's experiment ledger (3 experiments, protocol budget)

| # | Experiment | Result | Receipt |
|---|---|---|---|
| EXP-1 | Thermal-conduit share sweep (GDR 1391 wellsprings + 2 m probes + paleo deposits) | **NEGATIVE** — thermal-ranked placement loses to uniform on both instruments (IHR 0.0287 vs 0.0439; SGMC 0.0329 vs 0.0750) | `evidence/exp1_thermal_share_sweep.json` |
| EXP-2 | Placement decision: uniform vs ring habitat × N × softness | **ring-binary-37654 wins**; N = 24,000 negative; plateau1 soft = split verdict (SGMC +20 %, IHR −48 %) | `evidence/exp2_placement_decision.json` |
| EXP-3 | Final candidate write + 13-check validator + uniqueness + run card | **PROMOTE** (verdict above) | `evidence/s3_run_card_20261031.json` |

Negative results are deliverables: the register's former rank-1 lead (2-m probe
temperature residual *rank* form) is falsified as a placement prior;
`research/2026-10-31-hypotheses-s3.md` records the surviving forms.
