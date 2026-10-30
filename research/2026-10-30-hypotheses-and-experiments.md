# Hypotheses, experiments and verdicts — 2026-10-30 session

Status key: **TESTED** = run on the proxy holdout in this session · **NOT TESTED** = blocked (named blocker) · every number is labelled.

Scope and budget (parallel-run protocol): 3 experiments or 2 hours. **Used: 2 experiments** (E1, E2). E3 reserved for H-F1 once the official feature file is authorised.

## 1. Evaluation harness (shared, not forked)

| Item | Where | Notes |
|---|---|---|
| Official DTI | `src/gems/metric.py` (`dti_binary`, `per_component_terms`, `bootstrap_dti`) | alpha 0.2, beta 0.8, R = 3 px (300 m) triangular kernel. Official definition: [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Placement | `scripts/generate_unique_submission.py` (`build_propensity`, `place_dots`) | reused unchanged; the budget was overridden via the module constant |
| Folds | 4 spatial folds of whole USGS/INGENIOUS segments (8-connected), 700 px blocks | `scripts/holdout_proxy_experiment.py` |
| Buffer | 10 px (primary). Visible faults within 10 px of a withheld segment are dropped | 0 px run kept as sensitivity only |
| Masking | every catalogue pixel except the withheld truth is masked from scoring | mirrors the organizer rule: known-fault pixels are excluded from evaluation ([DrivenData staff, 2026-09-16](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)) |
| Truth | withheld USGS/INGENIOUS segments, **not** the organizer's new-fault set | **PROXY**. A proxy DTI is never an organizer score |

## 2. Hypotheses (ranked by expected DTI gain per unit cost)

| Rank | ID | Layers | Physical signature targeted | Why it could catch a fault missing from USGS/INGENIOUS | Non-fault mimic | Difference from implemented repo methods | Status |
|---|---|---|---|---|---|---|---|
| 1 | **H-S1** strike-coherence echelon corridor | Visible USGS/INGENIOUS trace geometry only | Regional strike coherence of mapped traces (structure tensor, 30 px pooling) × off-trace band 15–35 px | En-echelon, sub-parallel fault arrays in extensional provinces put unmapped faults 1–4 km off mapped traces | Erosional/drainage lineaments and piedmont breaks aligned with the same stress field | Orientation coherence + band; the generator uses a distance-only gamma term plus a random field | **TESTED (E2): negative.** 0.0076 [0.0060, 0.0092] vs random 0.0375; AUC 0.18–0.26 |
| 2 | **H-F1** feature-stack model with buffered holdout | competition `training_features.tif` (19 bands: conductivity, elevation, strain, gravity, magnetics, earthquake density) | Multi-layer boundary/tilt response of basement-offsetting faults | Geophysical contrast persists under cover where the scarp does not | Lithologic contacts, intrusions, acquisition/leveling artifacts | The repo has no trained model on the official feature stack; the reference solution does | **NOT TESTED.** Blocker: the official file is login-walled. The only copy is a third-party mirror (`buffedlizard55-lab/GEMSDOE` @ `c0c06ac`), which is not organizer-authenticated |
| 3 | **H-R1** radiometric K/Th/U boundary persistence | USGS GeoDAWN radiometric grids (K, Th, U) | Boundary persistence of potassium/thorium contrast across scales (fault-controlled alteration) | Altered fault zones can show radiometric contrast under thin cover | Soil and lithology changes, radon and flight-height artifacts | New source (not in the feature stack) | **NOT TESTED.** Blocker: the GeoDAWN data release is CC0 and free ([USGS](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)), but the sandbox allowlist blocks the download hosts |
| 4 | **H-G1** geodetic shear/dilation tendency | INGENIOUS geodetic shear and dilation models; Quaternary slip and dilation tendency | Dilational tendency of mapped and unmapped structures | Dilating structures are preferred fluid pathways | Subsidence and creep signals | New source | **NOT TESTED.** Blocker: the GDR 1391 files are CC BY 4.0 ([GDR](https://gdr.openei.org/submissions/1391)), but gdr.openei.org is not on the allowlist |
| 5 | **H-P1** uniform random coverage (baseline) | none | none (null model) | — | — | — | **TESTED (E1 arm C) — the baseline to beat.** 0.0375 [0.0355, 0.0395] |

Pre-registered decision rule: a candidate is promoted to a real slot only if its proxy DTI beats the random-coverage baseline with non-overlapping 95% CIs, its canary AUC is below 0.90, and its file passes the lane gate.

## 3. Experiment results (PROXY truth; buffer 10 px; 4 folds; 60,988 withheld positives in 3,199 segments)

Source: [`evidence/holdout_proxy_sparse_blind.json`](../evidence/holdout_proxy_sparse_blind.json) (E1) and [`evidence/holdout_strike_coherence.json`](../evidence/holdout_strike_coherence.json) (E2). Evaluator: `src/gems/metric.py`. Label: **HOLDOUT-DTI (PROXY)**.

| Arm | Dots (scored) | Pooled DTI | 95% CI (cluster bootstrap over withheld segments) | TP_w | Verdict |
|---|---|---|---|---|---|
| A — sparse-blind generator as shipped (`generate_unique_submission.py`) | 22,163 placed per fold (88,635 scored across 4 folds) | **0.0000** | [0.0000, 0.0000] | 0.0 | negative |
| A0 — same, random field removed | 22,163 per fold (88,633 scored) | 0.0000 | [0.0000, 0.0000] | 0.0 | negative (the random "geothermal prior" adds nothing) |
| B — dense adjacency (off-fault term only) | 37,654 per fold (150,587 scored) | 0.0000 | [0.0000, 0.0000] | 0.0 | negative |
| **C — uniform random coverage (baseline)** | 22,163 per fold (88,648 scored) | **0.0375** | [0.0355, 0.0395] | 2,506.7 | baseline |
| E2 H-S1 strike-coherence corridor | 22,163 per fold | 0.0076 | [0.0060, 0.0092] | — | negative (below baseline) |

Leakage canary (each feature alone, AUC on withheld truth vs. unmasked background; threshold 0.90): off-fault term from visible faults 0.15–0.24; generator random field 0.47–0.54; H-S1 propensity 0.18–0.26. **No leakage flag.** The random field carries no information (AUC ≈ 0.5), so the generator's "geothermal prior" is confirmed to be noise.

Sensitivity (buffer 0 px; leakage-prone; NOT used for decisions): A 0.0024, A0 0.0032, B 0.0043, C 0.0375 — [`evidence/holdout_proxy_sparse_blind_buffer0.json`](../evidence/holdout_proxy_sparse_blind_buffer0.json). Removing the buffer does not rescue the catalogue-adjacency designs.

### What the proxy says, and what it does not

- Under a buffered holdout, dots placed next to visible faults earn no credit: withheld segments sit at least 10 px from visible traces, and the adjacency preference points away from them (AUC < 0.5).
- Uniform random coverage beats every catalogue-geometry design here. This is a property of the proxy truth, not evidence that random placement would score on the organizer's new-fault set.
- A proxy DTI is not an organizer score. The organizer's test set is new faults that are expert-labelled, and the leaderboard top is 0.4544 on the live page (verified 2026-10-30; see [`docs/data/leaderboard-snapshot-2026-10-30.json`](../docs/data/leaderboard-snapshot-2026-10-30.json)). Nothing in this session gives a score that could compete with that.

## 4. Named limitations that block the next real step

1. **Official feature stack.** `training_features.tif` (19 bands) is login-walled on DrivenData ([data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)). Without it, no feature-based model can be trained or holdout-tested on the competition's own inputs. A third-party mirror exists but is not organizer-authenticated and is not used for any claim here.
2. **Free official sources are blocked in this sandbox.** GeoDAWN ([USGS](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)) and INGENIOUS ([GDR 1391](https://gdr.openei.org/submissions/1391)) are free and reachable on the public web, but the sandbox allowlist permits only github.com, codeload.github.com, api.github.com, registry.npmjs.org, pypi.org and files.pythonhosted.org. Either the allowlist must be extended, or the files must be placed in `data/external/` by the owner.
3. **No organizer receipt.** Every historical score in the nine-site table is user-reported. No portal receipt for any file is available in this environment.
4. **Weekly slots.** The per-week limit is three ([Official Rules, §3.2](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). The account's remaining allowance is not visible here.

## 5. Recommended next experiment (E3, reserved)

H-F1 on the official `training_features.tif`, once the owner provides an authenticated copy: per-band canary (AUC < 0.90 each), then a gradient-boosted classifier trained on visible faults only, scored with the same folds, buffer, masking and evaluator, against the random-coverage baseline. Promotion rule as in §2.
