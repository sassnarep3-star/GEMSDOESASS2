# Executive summary — GEMSDOESASS2 (2026-10-30)

**Verdict: DO NOT SUBMIT.** No file passes the lane gate. The unique candidate is format-valid, but 100% of its dots lie within 3 px of a dense GEMSDOE2 surface (rule: more than 70% = duplicate).

- **Download (research only):** [gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif](docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif) — sha256 `65e3a775ad8b3fd3f3c55a501c84d48d05554219065cad69fa9ebfb54d572661`
- **Estimated score:** not estimable. The only numbers are PROXY holdout results for the design class, labelled HOLDOUT-DTI. No ORGANIZER-CONFIRMED score exists here.
- **Unique?** No. Lane rule: more than 70% of dots within 3 px of another raster = duplicate.

## Nine focus sites

Historical values are USER-REPORTED / UNVERIFIED.

| Site | Historical value | File to download (pinned) | Estimated score | Unique? |
|---|---|---|---|---|
| GEMSDOE32 | 0.2778 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/400b60d4a6d99f425ee90504e6c4552227556dd1/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) · 219,065 B | Not estimable | **NO** — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE36 | 0.2750 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/32c2660001d98f6fa9084a0971b3a9d5062d49b9/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) · 318,190 B | Not estimable | **NO** — 97.58% within 3 px of GEMSDOE27 |
| GEMSDOE28 | 0.2710 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/2c839d10f57ec9b074829e93c84bc39935f52896/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) · 825,430 B | Not estimable | **NO** — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE31 | 0.2708 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/eeb7da54ca4a8ae056f45e5b23eeef586ad79bf2/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) · 154,580 B | Not estimable | **NO** — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE33 | 0.2632 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/efa438d3104893c3e8aedf3817ac22167b1c681a/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) · 917,544 B | Not estimable | **NO** — 99.71% within 3 px of GEMSDOE27 |
| GEMSDOE25 | 0.2600 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/b4e74b3f9b191fbc214b6447e9ff1f3fa67552c4/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) · 836,982 B | Not estimable | **NO** — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE30 | 0.2600 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/9c0d637c0171407196b61b780444bc772ce75438/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) · 806,758 B | Not estimable | **NO** — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE24 | 0.2477 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/a433b430b74b813a9118ebd4ec438b12cbc69f46/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) · 863,902 B | Not estimable | **NO** — 100.00% within 3 px of GEMSDOE25 |
| GEMSDOE27 | 0.2449 (user-reported) | [pinned file](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/bef7ae8e8f63b69d299c9214c75988c8f5055f9c/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) · 866,160 B | Not estimable | **NO** — 98.02% within 3 px of GEMSDOE24 |
| **Unique candidate** `gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif` | — | [download](docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif) · 123,328 B | Not estimable — proxy DTI 0.0 | **NO** — 100% within 3 px of GEMSDOE2 dense surface |

## Evidence

- Proxy holdout (HOLDOUT-DTI, proxy truth, not organizer score): this design scores 0.0; uniform random coverage scores 0.0375 [0.0355, 0.0395].
- Pairwise lane check of the nine pinned focus files plus the candidate: [evidence/focus_pairwise.json](../evidence/focus_pairwise.json)
- Candidate vs dense GEMSDOE2 surface: [evidence/gates/lane_cc522684_vs_GEMSDOE2_turbo.json](../evidence/gates/lane_cc522684_vs_GEMSDOE2_turbo.json)
- Format validator (strict local pass; `ok_to_submit: false`): [evidence/validate_cc522684_zeros.json](../evidence/validate_cc522684_zeros.json)
- Run card: [evidence/run_card_20261030.json](../evidence/run_card_20261030.json)
- Hypotheses and experiments: [research/2026-10-30-hypotheses-and-experiments.md](../research/2026-10-30-hypotheses-and-experiments.md)

## Remaining work

1. Finish the full 2,277-raster lane pass (slow on 2 cores; the script is `scripts/gate_batch.py --no-rho`).
2. Owner ruling on the lane rule for dense probability surfaces (IR-S-01 / IR-RV-04). Literally, a dense surface makes almost any dot set a duplicate.
3. Authenticated access to the official `training_features.tif` (login-walled). This is needed for H-F1.
4. Allowlist access to USGS GeoDAWN and GDR 1391 INGENIOUS (H-R1, H-G1).
5. Organizer receipt for any submission. No weekly slot has been used.

Limitations: proxy truth is USGS/INGENIOUS segments, not the organizer's new faults. The historical scores are unverified. No organizer acceptance receipt exists here.
