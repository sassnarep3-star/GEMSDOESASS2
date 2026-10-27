# GEMSDOESASS2 — DOE GEMS Prize: unique, validated TIF submission system

**Site:** `docs/index.html` (GitHub Pages) · **Executive summary & how-to-submit:** `docs/executive-summary.html`

## 🟢 Current decision — 2026-10-27 (automated, fail-closed)

**✅ OK TO DOWNLOAD AND SUBMIT — unique TIF generated this session, not a copy of any prior GEMSDOE submission.**

| | |
|---|---|
| **File to submit** | [`docs/downloads/gemsdoesass2-scu1-scarpcorridor-uth-37000-20261027T120000Z-zeros.zip`](docs/downloads/gemsdoesass2-scu1-scarpcorridor-uth-37000-20261027T120000Z-zeros.zip) (or the raw [`.tif`](docs/downloads/gemsdoesass2-scu1-scarpcorridor-uth-37000-20261027T120000Z-zeros.tif)) |
| **SHA-256** | `0ab88d8ab85c9bbfc690557bca0e8bf6d92dcd7657825306c9eaf294dab3fe6d` |
| **Suggested submission name** | `GEMSDOESASS2-SCU1-0AB88D8A` |
| **Suggested note (110/140 chars)** | `SASS2 SCU scarp-corridor-UTh 37000d B2 sep2 | SGMC 0.135 vs champ 0.094 | HR 0.0163 | est 0.14-0.40 | 0ab88d8a` |
| **Estimated score** | **ESTIMATE 0.144 – 0.399** (point 0.27; two leak-free methods, §Estimates below). *Never a score; the only real number comes from the organizer.* |
| **Unique?** | **YES** — worst 3-px dot overlap vs any registry raster **24.5%** (gate ≤70%); max \|Spearman\| ≤ 0.90 pass; byte-hash distinct. The nine prior site-bests overlap each other ≥99%. |
| **Format** | 13/13 validator checks PASS: single-band float32, 3730×3292, EPSG:32611, transform (100,0,243350,0,−100,4508550), **all 12,279,160 cells finite in [0,1]** (cures the portal error `Predicted values must be in range [0, 1]`), 0 positives on the masked catalogue, zip contains exactly one tif. |
| **Verdict** | `candidate-unique-validated` (promotion to a weekly slot is the separate selector step per protocol §6) |

Everything above is produced by `scripts/run_pipeline.py` → `scripts/sgmc_calibration.py` → `scripts/finalize_card.py` → `scripts/build_site.py` with **no manual input**; evidence in [`evidence/run_card.json`](evidence/run_card.json).

---

## Executive summary — the 9 focus sites (what to download, score, unique?)

All historical figures are **OWNER-REPORTED** (from the standing prompt / site READMEs). No organizer receipt exists in any repo. Every one of the nine prior site-bests has **already been submitted and scored** — resubmitting an exact duplicate wastes a weekly slot and violates the uniqueness requirement.

| Site | File to download (best historical) | Score | Unique? |
|---|---|---|---|
| [GEMSDOE24](https://github.com/buffedlizard55-lab/GEMSDOE24) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1` | 0.2477 OWNER-REP | NO — D1.5 lattice ancestor of the family |
| [GEMSDOE25](https://github.com/buffedlizard55-lab/GEMSDOE25) | `dotted-h19-5-d2-8-20261002-e56ea318af89` | 0.2600 OWNER-REP | NO — dot-identical to GEMSDOE30 best |
| [GEMSDOE27](https://github.com/buffedlizard55-lab/GEMSDOE27) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1` | 0.2449 OWNER-REP | NO — gap-closure increment on D1.5 |
| [GEMSDOE28](https://github.com/buffedlizard55-lab/GEMSDOE28) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f` | 0.2710 OWNER-REP | NO — same lattice family (best of its 4) |
| [GEMSDOE30](https://github.com/buffedlizard55-lab/GEMSDOE30) | `d28-poisson300m-offcat-44090-20261003T233156Z` | 0.2600 OWNER-REP | NO — dot-identical to GEMSDOE25 |
| [GEMSDOE31](https://github.com/buffedlizard55-lab/GEMSDOE31) | `h27-4-solo-d28-20261004-8acb75e1` | 0.2708 OWNER-REP | NO — duplicate of GEMSDOE28 `h27-4-r1` |
| [GEMSDOE32](https://github.com/buffedlizard55-lab/GEMSDOE32) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` **(champion)** | **0.2778 OWNER-REP** | NO — family champion, **already submitted, do not resubmit** |
| [GEMSDOE33](https://github.com/buffedlizard55-lab/GEMSDOE33) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 OWNER-REP | NO — tip/step-over variant of the family |
| [GEMSDOE36](https://github.com/buffedlizard55-lab/GEMSDOE36) | `anderson-geothermal-pinn-38854-20261004T230000Z` | 0.2750 OWNER-REP | NO — champion + 1,200 extra dots |
| **THIS REPO** | **`gemsdoesass2-scu1-…-0ab88d8a-zeros.tif`** | **ESTIMATE 0.144–0.399** | **YES — passes every gate; the file to submit** |

## Why `h33-h33-2-b2` scored 0.2778 (PhD-level answer, verified line by line)

1. **Metric algebra.** The score is a pooled distance-weighted Tversky index, `DTI = T/(T + 0.2·FP + 0.8·FN)` with a 300 m (3 px) triangular kernel (α=0.2, β=0.8 — [Tversky index](https://en.wikipedia.org/wiki/Tversky_index)). FP is weighted 4× less than FN, and one binary dot costs at most 0.2 FP-weight while earning kernel credit over a 3-px radius. **Sparse binary dots therefore dominate continuous confidence maps** — verified in `src/gems/metric.py` + `tests/test_metric.py` against the champion's own audit JSON.
2. **Catalogue masking.** Known USGS/INGENIOUS fault pixels are masked at scoring ([staff post #11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)); prediction mass on them is pure waste. The champion is *literally* the 0.2708 base with every dot within 2 px (200 m) of the catalogue deleted (its audit JSON: "0.2708 base with every dot at d(catalogue) <= 2 px deleted, 37,654 dots") — FP down, T unchanged → 0.2778.
3. **Corridor placement.** The surviving dots tile the catalogue flank corridors where undiscovered sub-parallel strands cluster (Basin-and-Range fault systems grow as strand arrays).
4. **Can it be beaten? Yes.** The leaderboard top is 0.4413, so ≥0.16 of truth-coverage headroom exists. At DTI≈0.28 a new dot must earn ≥0.2·DTI ≈ 0.056 kernel credit to pay for itself: the path is **better placement, not more dots** (GEMSDOE36 added 1,200 dots to the champion and *lost* 0.0028).

**This repo's answer (lane SCU):** keep the champion's three structural wins (binary dots, B=2 prune, corridor confinement) but place dots by *evidence* — lidar scarp morphology (step/slope-excess/crest-convexity from the 1 m DEM stack) × GeoDAWN U/Th fluid-pathway corroboration — instead of resampling the same lattice. On the leak-free SGMC off-catalogue instrument it recovers **+43.7%** more known-but-uncatalogued faults than the champion (0.13506 vs 0.09397), and it is the best of all 13 rasters measured.

## Estimates and instruments (every number labeled)

- **HOLDOUT-DTI** (`GEMSDOESASS2-HRv1`, hide-and-recover, 4 spatially-blocked folds, catalogue features rebuilt from visible faults only, visible masked pixel-exact, ~59k withheld positives, cluster-bootstrap 95% CI): ours **0.01632 [0.0108, 0.0227]** vs champion **0.00473 [0.0040, 0.0055]** on the identical instrument.
- **SGMC off-catalogue DTI** (truth = USGS SGMC geologic-map faults >300 m off the catalogue; leak-free both directions): ours **0.13506**, champion **0.09397**, family range 0.0919–0.0996.
- **ESTIMATE 0.144–0.399** — low = within-family SGMC regression (extrapolated), high = champion-ratio on the SGMC instrument. `evidence/sgmc_calibration.json`.
- **Leakage canary:** max single-feature AUC **0.579** ≤ 0.90 → PASS.

## Negative results & irregularities (deliverables, flagged for review)

- **EXP3 (NEGATIVE):** strike-resonance weighting `cos²(θ_lidar−θ_cat)` *reduced* HOLDOUT-DTI at every dot budget in all 4 folds → removed from the shipped surface (`evidence/experiments.json`).
- **IR-SASS2-01:** the as-submitted hide-and-recover arm structurally punishes B=2-pruned rasters (withheld truth *is* catalogue, which the prune avoids); its ratio estimate is withdrawn. Mirrors GEMSDOE32 `IR-45-EVAL-02`.
- **IR-SASS2-02:** EXP2 dot-budget sweep favors more dots only because the FP break-even at holdout DTI≈0.02 is ~14× looser than at live 0.2778 — selection not transferable; N kept at the pre-registered 37,000.
- **IR-SASS2-03:** all 12 calibration points are one raster family inside 0.2449–0.2778; extrapolating to a unique raster is the dominant estimate uncertainty.
- **IR-SASS2-04:** no lane paragraph was supplied in the parallel-run protocol; lane SCU was self-declared and logged (mirrors GEMSDOE32 `IR-45-LANE-01`).
- **IR-SASS2-05:** no ORGANIZER-CONFIRMED receipt exists for any historical score in any of the 90+ GEMSDOE repos; all are OWNER-REPORTED.

## Reproduce (fully automated, no manual input)

```bash
pip install rasterio numpy scipy
bash scripts/fetch_registry.sh          # pulls data caches from the public GEMSDOE repos (github.com)
python3 scripts/run_pipeline.py         # surface → canary → emission → validate → holdout → uniqueness → run card
python3 scripts/sgmc_calibration.py docs/downloads/<slug>-zeros.tif
python3 scripts/finalize_card.py && python3 scripts/build_site.py
python3 scripts/check_submission.py docs/downloads/<slug>-zeros.tif   # exit 0 = portal-ready
```

Data provenance (official sources, linked for manual review): competition [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login-gated; bridge copies of `existing_faults.tif`/`sample_submission.tif` are in `data/bridge/`, grid-verified against [EPSG:32611](https://epsg.io/32611)); [GeoDAWN DOI 10.5066/P93LGLVQ](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and); [GDR submission 1391](https://gdr.openei.org/submissions/1391); [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution); [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf); [INGENIOUS](https://gbcge.org/current-projects/ingenious/).

## Next steps (this or next session)

1. **Submit** the generated file in a weekly slot (selector step) and record the ORGANIZER-CONFIRMED receipt in `evidence/` — the single highest-information action available; it anchors the SGMC→live calibration for all future candidates.
2. Once the receipt lands, refit the calibration with a genuinely out-of-family point and tighten the estimate band.
3. Candidate hypotheses not yet spent (ranked, see `knowledge/01_findings.md`): line-density prior, Getis-Ord Gi* hotspot gating, 1–4 km wavelet multiscale ridge, gravity regional-residual (needs free USGS Bouguer grid — obtainable).
4. Limitations: no DrivenData auth from the sandbox (cannot read the live leaderboard or submit automatically); outbound net restricted to github/pypi hosts (registry caches cover all required data); OWNER-REPORTED scores cannot be independently re-verified.

## Core values

- **Maximize P(Win):** weekly slots are scarce information capital — only a unique, fully-validated, holdout-superior file earns one.
- **Own the Outcome:** negative results (EXP3) and instrument defects (IR-SASS2-01/02) are reported, not hidden; shared tools are fixed in-template, never forked privately.

---

<details>
<summary><b>Standing prompt (read every session — verbatim, deduplicated; the original message repeats itself twice)</b></summary>

See [`knowledge/00_standing_prompt.md`](knowledge/00_standing_prompt.md) for the full text including the PARALLEL-RUN PROTOCOL (lane discipline, reuse-don't-rebuild, number labeling, leakage canary, run card, budget), the nine focus sites, the full OWNER-REPORTED score ledger for all GEMSDOE sites, the 0.2778 champion study question, the 0.3195/0.4413 targets, submission-format requirements, data links, site requirements, Arena core values, and the multi-pass verification rules.

</details>
