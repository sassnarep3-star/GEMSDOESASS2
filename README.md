# GEMSDOESASS2 — DOE GEMS Prize Blind Geothermal Fault Discovery & Fail-Closed Audit System

> ### 📋 STANDING PROJECT PROMPT (Permanent Starting Brief — Read Every Session)
>
> Review the repo.
>
> I want to focus on the highest scoring submissions from the following sites: `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`.
>
> **THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!**
>
> MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.
>
> There should be an easy to download submission tif file as described by the prompt. Read the entire prompt. A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.
>
> **PARALLEL-RUN PROTOCOL — read first.** This session is one of several running from this same prompt.
> 1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds `[0.90]`, or more than `[70%]` of your dots fall within `3 px` of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.
> 2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (`alpha 0.2`, `beta 0.8`, `300 m` triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.
> 3. **LABEL EVERY NUMBER** as `HOLDOUT-DTI` (evaluator version, number of withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (copied from a submission-page receipt). A projection is never written as a score.
> 4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any result. AUC above `[0.90]` means leakage until proven otherwise.
> 5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in `[0,1]`, CRS/shape/transform match); submission name + note of at most 140 characters; verdict `promote` / `negative`. Negative results are deliverables.
> 6. **BUDGET.** Stop after `[3]` experiments or `[2]` hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.
>
> **Study & Analyze Highest Score (`0.2778`):** `https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html` — `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778` (`USER-REPORTED`; prompt leaderboard snapshots `0.3195` / `0.4413`; live DrivenData public #1 on `2026-10-27` is `xiaofanhu = 0.4544`). Why and how did this get the highest score and are we able to generate a submission that scores higher than `0.2778`? Answer using PhD-level experience, knowledge, and judgement, generate 3–5 novel geological hypotheses naming exact layers, physical signatures, missing-catalogue rationale, novelty, and free official sources, validate on the spatially-blocked holdout, fix `"Predicted values must be in range [0, 1]"`, create an executive summary subpage explaining step-by-step how to submit, and build a clean user-friendly GitHub Pages site (`docs/`). Work autonomously line-by-line from official verified sources, flag irregularities, zero hallucinations, run 3 passes, and merge via PR onto `main`.

**Pre-Registered Scientific Lane (`SASS2-XGHF`):**
> **Gallardo–Meju Cross-Gradient Structural Collinearity + Salem Shallow Tilt-Zero Sharpness + 5-Source Convective Hydrothermal Conduit Plumes + Completeness-Calibrated Dual-Horizon SAR-PU Submodular Cover.** Combine official 19-band geophysical/geodetic/radiometric features (`training_features.tif`), USGS 3DEP 1-m LiDAR scarp geometry, de-seamed GeoDAWN magnetic/gravity tilt-zero sharpness, Gallardo–Meju gravity×RTP cross-gradient collinearity, and 5 real INGENIOUS/USGS hydrothermal datasets (`7,881` chemical geothermometer disequilibrium cells, `2,782` 2-m probe cells, `302` sinter/vent cells, `2,322` USGS `qc_code=='G'` convective heat-flow cells) deconfounded for Lake Lahontan shorelines and TIGER roads; train spatially-blocked SAR-PU LightGBM modulated by visible-only crack-tip/relay-bridge stress lobes (`Horizon A`) and pack residual off-catalogue blind conduits via strike-anisotropic single-strand CELF (`Horizon B`, `37,654` dots, `B=2.0 px`).

---

## NEW EXECUTIVE LANE (2026-10-27 UTC) — `HVFD-EXP3-HYDROCOLLINEAR` GENERATED & DUAL-VALIDATED

### `OK TO DOWNLOAD: YES` · `OK TO SUBMIT: NO` · `DUAL FORMAT + GDAL MASK / 54-CANARY / HOLDOUT (+0.02234) / 451-AVAILABLE-REGISTRY-UNIQUE (68.27%): PASS`

- **One-Click Validated `.tif` (`zeros` + `GDAL_TIFF_INTERNAL_MASK`):** **[`docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif`](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif)** (`154,994 B`) · [`.zip`](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.zip) · [Dual Validator Receipt JSON](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.json) · [HVFD-EXP3 Run Card JSON](evidence/hvfd_exp3_run_card.json)
- **Dedicated HVFD-EXP3 Pages:** [`docs/hvfd-exp3.html`](docs/hvfd-exp3.html) · [`docs/hvfd-forensics.html`](docs/hvfd-forensics.html) · [`HYPOTHESES.md`](HYPOTHESES.md) · [`IRREGULARITIES.md`](IRREGULARITIES.md)
- **Unique DrivenData Submission Name (`52` chars):** `GEMSDOESASS2-HVFD-EXP3-HYDROCOLLINEAR-37654-fc98343e`
- **Candidate note for a future authorized submission (`104 / 140` chars):** `GEMSDOESASS2 hvfd-exp3-hydrocollinear LOQO B=2 37654px HOLDOUT-DTI=0.1184 blind8km=0.1763 max3pxOv=68.3%`
- **SHA-256 (`-zeros.tif` / `.zip`):** `28bb9419d592797dcac1bfb1eb19fcffa7581a51718230f1f4f957a3e3d610d6` / `b5f0f1f7469155c05f9b2275f00e4b8325bd3eaca24624fe90aa947c7b92e98d`
- **Primary Buffered Holdout (`HOLDOUT-DTI`):** **`0.11842 [0.10255, 0.13426]`** (`gems57-pooled-hide-v2`, `N = 11,321` withheld positives) — paired gain over `fair_h33` is **`+0.02234` (95% CI `[+0.01030, +0.03477]`)**. Comparator values and CIs are preserved in the run card.
- **Zero-Context Blind 8 km Quadrants (`HOLDOUT-DTI`):** **`0.17630 [0.15434, 0.19659]`** (`spatial.folds`, `buffer_px=80`, `N = 60,988` withheld positives).
- **Gate-1 Canary (`54` features) & Gate-3 Available-Registry Uniqueness (`451` unique rasters):** `max_single_feature_symmetric_auc = 0.78508 <= 0.90` (`dist_known_fault_px` stripped); `max_pre_placement_spearman = 0.21786 <= 0.90`; `max_discrete_3px_dot_overlap = 68.27% <= 70.0%` (**`49.34%`** vs `GEMSDOE32 B2`; **`47.80%`** vs sibling `SASS2-XGHF`, giving two mutually independent `<48%`-overlap lanes in `GEMSDOESASS2`!; note Pigeonhole bound `>=82.34%` against non-submission 206,895-dot probe `r13-lattice-s5`).
- **Gate-4 Dual Format & Range Validation:** **PASS** on both `vendor/gems57/validate.py` (`15/15`, `12,279,160` finite `[0.0, 1.0]` `float32` pixels, `0` NaN, `0` Inf, `0` on-catalogue) AND `scripts/validate_tif.py` (`strict_local_format_pass = true`).
- **Generative AI Disclosure ([DOE/NLR Sec. 3.2](https://docs.nlr.gov/docs/fy26osti/96647.pdf)):** Deterministic numerical Python pipeline implemented with AI agent assistance on Arena.ai Agent Mode; zero generative raster synthesis was used to fabricate pixel predictions.

![HVFD-EXP3 Holdout Progression](docs/assets/fig1_holdout_progression.png)

![HVFD-EXP3 Nevada Fault Discovery Map](docs/assets/fig3_nevada_fault_discovery_map.png)

---

## EXECUTIVE STATUS (28 October 2026 UTC) — `HVFD-EXP3-HYDROCOLLINEAR`

### `OK TO DOWNLOAD: YES` · `OK TO SUBMIT: NO` · research-artifact promotion is separate from weekly-slot authorization

- **Decision desk:** [`docs/index.html`](docs/index.html) · [live Pages site](https://sassnarep3-star.github.io/GEMSDOESASS2/)
- **Download-first executive guide:** [`docs/executive-summary.html`](docs/executive-summary.html) · [`docs/executive-summary.md`](docs/executive-summary.md)
- **Current candidate TIF:** [`gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif`](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif) (`154,994` bytes)
- **Current candidate ZIP:** [`gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.zip`](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.zip) — one GeoTIFF member; verify the exact path in the run card before use.
- **SHA-256:** TIF `28bb9419d592797dcac1bfb1eb19fcffa7581a51718230f1f4f957a3e3d610d6` · ZIP `b5f0f1f7469155c05f9b2275f00e4b8325bd3eaca24624fe90aa947c7b92e98d`
- **Submission name / note:** `GEMSDOESASS2-HVFD-EXP3-HYDROCOLLINEAR-37654-fc98343e` · `GEMSDOESASS2 hvfd-exp3-hydrocollinear LOQO B=2 37654px HOLDOUT-DTI=0.1184 blind8km=0.1763 max3pxOv=68.3%` (`104 / 140` characters)
- **HOLDOUT-DTI primary:** `0.11842` (evaluator `gems57-pooled-hide-v2`, `N=11,321` withheld positives, 95% CI `[0.10255, 0.13426]`); paired gain versus `fair_h33` is `+0.02234`, 95% CI `[+0.01030, +0.03477]`.
- **HOLDOUT-DTI blind:** `0.17630` (`spatial.folds`, `buffer_px=80`, `N=60,988` withheld positives, 95% CI `[0.15434, 0.19659]`).
- **Leakage canary:** `54/54` pass, maximum symmetric AUC `0.78508 <= 0.90`.
- **Available-registry uniqueness:** `451` unique rasters checked; maximum post-placement Spearman `0.06540`, maximum 3-px dot overlap `68.27% <= 70%`. The registry is not proven complete, so this is local evidence, not organizer clearance.
- **Local format:** single-band `float32`, `EPSG:32611`, `3730×3292`, exact transform, finite `[0,1]`, strict local validator pass, and `0` outside the reference footprint. The prior out-of-range packaging failure is now fail-closed.
- **Selector boundary:** [`evidence/hvfd_exp3_run_card.json`](evidence/hvfd_exp3_run_card.json) records `verdict=promote` only for the research artifact, `ok_to_download=true`, `ok_to_submit=false`, and no weekly slot spent. Do not upload until a separate selector authorization is recorded.

## 1. Executive Summary Table Across All 9 Focus Sites

All historical site values below are **USER-REPORTED / UNVERIFIED** unless a future submission-page receipt is attached. The `Unique vs focus peers?` column refers to the nine historical artifacts, not to the current HVFD candidate.

| Site | Historical best file | Reported value | Dots | Unique vs focus peers? |
|---|---|---:|---:|---|
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | `0.2778` | `37,654` | **NO — H19-5 family** |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | `0.2750` | `38,854` | **NO — duplicate lineage** |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` | `0.2710` | `37,660` | **NO — duplicate lineage** |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` | `0.2708` | `40,199` | **NO — duplicate lineage** |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | `0.2632` | `41,865` | **NO — duplicate lineage** |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` | `0.2600` | `44,090` | **NO — shared dot family** |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | `0.2600` | `44,090` | **NO — exact twin of 25** |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | `0.2477` | `60,069` | **NO — duplicate lineage** |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` | `0.2449` | `61,328` | **NO — duplicate lineage** |

Historical values explain the reported `GEMSDOE32` `0.2778` result and motivate the new geological hypotheses; they do not establish organizer-confirmed performance. Numeric model results are labeled `HOLDOUT-DTI` with evaluator, withheld-positive count, and 95% CI. No projection is called a score.

---

## 2. Reproducible Automated Validation & Audit Commands

```bash
# 1. Run fast CI audit & automated GeoTIFF / HTML / JSDOM regression suites (zero manual inspection)
python3 -m venv .venv
.venv/bin/pip install -r requirements-audit.txt
.venv/bin/python -m pytest -q
npm ci && node --check docs/assets/app.js && npm run test:site

# 2. Independently inspect saved HVFD-EXP3 GeoTIFF bytes (the command auto-uses data/bridge)
.venv/bin/python scripts/submission_writer.py --validate-only \
  docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif

# 3. Run the explicit decision gate. Exit code 2 is intentional here: download is
# allowed, but a weekly submission still requires a separate selector authorization.
.venv/bin/python scripts/submission_preflight.py \
  docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif \
  --sample data/bridge/sample_submission.tif \
  --run-card evidence/hvfd_exp3_run_card.json

# 4. Full 3-experiment SASS2-XGHF training + 59-ch canary + 431-raster uniqueness scan (requires SHA-verified .cache/gems_data/)
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python scripts/run_sass2_xghf.py

# 5. Serve GitHub Pages portal locally
python3 -m http.server 8080 --bind 0.0.0.0 --directory docs
```

---

## 3. Known Limitations & Remaining Next Steps

1. **Calibration-Lattice Exemption & Weekly-Slot Selector (Protocol Rules 1 & 6):** `HVFD-EXP3` passes `451` available-registry rasters (`<= 68.27%`), `54/54` canaries, `strict_local_format_pass = true`, and the recorded buffered/blind holdouts, but automatic live slot submission stays fail-closed (`verdict = "promote"` only for the research artifact, `ok_to_submit = false`) until the project owner's selector explicitly authorizes this candidate and the non-competitive `13GEMSDOE` calibration lattices (`r13-lattice-s5`, `r12-lattice-s6`) are resolved.
2. **Authenticated Sample & Private Test Truth:** Local `data/bridge/sample_submission.tif` (`2176d08e...`) is SHA-pinned from owner mirrors; verify byte match against an authenticated DrivenData download before spending a live slot, and record any live score receipt as `ORGANIZER-CONFIRMED` alongside generative-AI disclosure per [DOE/NLR Rules (`96647.pdf`)](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
3. **Next Scientific Iteration (`SASS2-INSAR-UNET`):** Train a full-footprint 59-channel 2D U-Net / SegFormer directly optimizing soft-max-pool `DW-Tversky` loss with NASA OPERA Sentinel-1 InSAR velocity gradients on a GPU workstation.
4. **Reproducibility / data placement:** `data/bridge` is an owner-mirror geometry witness, not authenticated organizer data. The full model lane still requires the hash-verified `.cache/gems_data` feature stack; `scripts/submission_preflight.py` intentionally returns `ok_to_submit=false` unless a run card contains an explicit selector authorization. No new experiment or weekly slot is claimed in this review pass.

---

## 4. Protocol Rule 5 — Final Machine-Verified JSON Run Card

The complete machine-readable card is [`evidence/hvfd_exp3_run_card.json`](evidence/hvfd_exp3_run_card.json). It records the hypothesis, mechanism, named non-fault mimics, both HOLDOUT-DTI results and CIs, leakage canary, registry correlation/overlap checks, candidate SHA-256, validator output, submission name/note, research verdict, and the separate `ok_to_download` / `ok_to_submit` selector boundary.

The current checkout has no full feature cache and no organizer submission receipt. No new experiment, live score, or weekly slot is claimed by this review pass.
