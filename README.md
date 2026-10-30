# GEMSDOESASS2 — auditable geothermal fault discovery

## 🚦 Current decision (2026-10-30): **SUBMIT THE STRAIN-RIDGE FILE**

| Item | Value |
|---|---|
| **File to download** | [`docs/downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif`](docs/downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif) |
| SHA-256 | `6d00f58a35005a253e352e21c8adde0e108aa0abb4b810db9797af89d94dd615` |
| Grid | EPSG:32611 · (3730, 3292) · 100 m · transform `(100,0,243350,0,-100,4508550)` |
| Cells predicted | 37,654 — **the champion's exact dot budget** · 0.00 % inside the fault catalogue |
| Format gate | **11 / 11 pass** (strict), every one of 12,279,360 cells finite in [0, 1], `nodata=None` |
| Uniqueness gate | **PASS vs competing rasters** — 36.45 % max overlap, \|ρ\| 0.0115 over 19 · **FAIL vs the r13 calibration probe** (99.37 %, see below) |
| Science gate | **PASS** — HOLDOUT-DTI **0.2244** vs matched incumbent **0.0715**, ratio **3.14×** (P = 0.958) |
| Model score estimate | **0.29** (controlled 0.2853 · slope-range 0.2815–0.2890 · all-model-risk 0.25–0.33) — *not* organizer-confirmed |
| Submission name | `GEMSDOESASS2-STRAINRIDGE-OFFCAT-37654D` |
| Note (≤140 chars) | `strain+ridgelineament prior, same 37654 dot budget as champion, 0% on full USGS QFaults catalogue, off-catalogue blind faults` |

**Download and submit: [site](docs/index.html) · [executive summary](docs/executive-summary.html) · [why 0.2778 scored](docs/method.html) · [run card](evidence/strain_ridge_run_card.json)**

⚠️ No organizer receipt exists for any file here. The 0.29 is a **MODEL ESTIMATE** from a controlled one-variable extrapolation. It is never written as a score. No weekly slot has been spent.

⚠️ **One gate is failed, openly.** Against the `13gems_20261001_r13-lattice-s5` calibration probe the file is **99.37 %** within 3 px, so the literal 70 % rule **fails**. A *seeded random placement* at the identical dot count scores **99.91 %** — the probe is a space-filling surface and the test is saturated for any interior placement at this budget (IR-S-01, IR-RV-04). Against every actual competing raster it passes at 36.45 %. **Owner ruling required**; the exemption is not assumed anywhere in this repository. Receipt: [`candidate_vs_registry_lattice.json`](evidence/candidate_vs_registry_lattice.json).

⚠️ **Honest size of the win: about +0.008 over the 0.2778 champion.** This is the best-supported move available, not a leap. Nothing in this repository reaches 0.4413; see §3 for why, arithmetically.

---

## 📋 STANDING PROJECT PROMPT — read at the start of every session

Review the repository. Focus on **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36**; maintain an executive summary showing each site's historical best, file, score evidence and novelty. The highest urgency is to **generate an original, validated competition GeoTIFF, not copy an old submission**; make its download, unique name, ≤140-character note and eligibility unambiguous. Estimate performance only with evidence, distinguish a holdout from an organizer score, and never invent a projection. A local format pass alone is not submission approval. Study the reported 0.2778 GEMSDOE32 file, use official sources, propose 3–5 materially distinct geological hypotheses before implementation, check feature leakage and validate the best on a buffered spatial holdout before spending a slot. Maintain a simple GitHub Pages site and step-by-step submission guide; diagnose the user's range-error report only if its rejected bytes and response are actually available.

Work line by line from official verified sources with links for manual review. Flag irregularities. No hallucinations. Multiple passes: implement → review/fix → re-check. Create a PR and merge it; list remaining work and limitations for the next session.

### Parallel-run protocol (operative text)

1. **LANE.** Stay inside one method paragraph. If the raster's rank-correlation with any registry raster exceeds **0.90**, or more than **70%** of its dots fall within 3 px of one registry raster's dots, log a duplicate and stop. Check the surface before placement *and* the final dots. Implemented: `scripts/uniqueness_gate.py` (exits 2 on failure).
2. **REUSE, DON'T REBUILD.** Use `scripts/holdout_strain_ridge.py`, `scripts/holdout_bootstrap.py`, `src/gems/metric.py`, `src/gems_sass2/submission.py`. Hide whole fault features with a buffer; derive every catalogue-based feature only from visible faults; mask visible faults pixel-exactly; score pooled DTI (α 0.2, β 0.8, 300 m triangular kernel). Fix a shared defect once; never keep a private fork.
3. **LABEL EVERY NUMBER** as **HOLDOUT-DTI** (evaluator, withheld positives, 95% CI) or **ORGANIZER-CONFIRMED** (submission-page receipt). A projection is never written as a score.
4. **LEAKAGE CANARY.** Test each feature alone on the holdout; AUC above 0.90 is leakage until disproved.
5. **RUN CARD.** One JSON card: hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI + CI, registry correlations/overlaps, raster SHA-256, validator output, submission name + ≤140-character note, verdict.
6. **BUDGET.** Stop after three experiments or two hours. Promotion to a real slot is a separate owner decision inside the weekly cap.

### Core values

**Maximize P(Win)** — weigh evidence, risk and scarce slots; put the outcome first.
**Own the Outcome** — own results end to end; fix shared tools; report negatives honestly.

---

## What this session established

### 1. Why GEMSDOE32 scored 0.2778 — it is a collar sweep, not a model

All nine focus sites are one family: a Poisson-disk lattice over the whole GeoDAWN footprint, lightly modulated by distance to the **already-mapped** catalogue. Median dot-to-catalogue distance is 14–20 cells (1.4–2.0 km); 30–42 % of dots sit more than 1 km from any mapped fault. None is an on-fault prediction and none uses an independent geophysical field.

The reported scores are, to measurement precision, a function of how much of the dot budget lands somewhere the metric can never reward. The truth set is defined as faults **absent** from the catalogue, so a dot within the collar is guaranteed false-positive and guaranteed zero true-positive:

| Focus site | Dots | % within 3 px of catalogue | Reported |
|---|---|---|---|
| GEMSDOE25 | 44,090 | 19.52 % | 0.2600 |
| GEMSDOE31 | 40,199 | 11.73 % | 0.2708 |
| **GEMSDOE32** | **37,654** | **5.77 %** | **0.2778** |

Across all nine: Spearman(dot count, reported) = **−0.9832** (p = 2.0×10⁻⁶); Spearman(DTI scored against the catalogue, reported) = **−1.000**; `1/DTI = 1.768205×10⁻⁵·N + 3.006165`, **R² = 0.9114**. Receipts: [`nine_site_forensics.json`](evidence/nine_site_forensics.json), [`nine_site_pairwise_overlap.json`](evidence/nine_site_pairwise_overlap.json).

Two corollaries matter. First, **the nine are one file, not nine**: every pair overlaps by **≥ 97.6 %** within 3 px, so under the project's own 70 % lane rule none of them is unique. Second, the family spans only 0.2449–0.2778 — there is no configuration of this generator that reaches 0.4413.

### 2. The catalogue every focus site placed against is incomplete — by 2.6×

`data/bridge/labels.tif` holds 60,988 fault cells. The **complete** official USGS Quaternary Faults + GBCGE INGENIOUS database rasterises to **156,418** cells inside the footprint and contains every bridge label cell (recall 0.9996, precision 0.3898). **95,452 mapped fault cells are missing from the copy the whole family was built against.** The new submission collars at 400 m against the complete database, so its contamination is 0.00 % where the champion's is 5.77 %. Receipt: [`catalogue_completeness.json`](evidence/catalogue_completeness.json).

### 3. The score estimate — one variable changed, no free parameters

The candidate deliberately carries the champion's exact 37,654 dots, so the only thing that differs is contamination:

| Step | Value |
|---|---|
| Champion anchor (37,654 dots, 5.77 % contaminated) | 0.2778 |
| Remove remaining contamination: 5.77 pp × (−0.001299) | +0.0075 |
| **Estimate** | **0.2853** |
| Slope ±50 % | 0.2815 – 0.2890 |
| **Quoted** (all model risk included) | **0.29** · risk range 0.25 – 0.33 |

Receipt: [`score_estimate.json`](evidence/score_estimate.json).

**The strain prior contributes nothing to this number, deliberately.** Its holdout advantage is measured against *mapped* faults, and the leaderboard ranks catalogue fidelity in reverse (ρ = −1.000). Converting that into score would be a category error, so it is reported separately below and excluded from the headline.

### 4. The science gate — real, leak-free, and honest about its limits

* **Leakage canary** — best single-feature AUC **0.6433** (`geod_2ndinv`); nothing near the 0.90 alarm.
* **Prior independence** — Spearman(prior, distance-to-catalogue) = **−0.165**, AUC 0.598: the prior is a genuinely independent field, not a catalogue proxy. Receipt: [`run card`](evidence/strain_ridge_run_card.json).
* **Holdout** — 144 spatial blocks, 29 withheld whole (38,278 positive cells), collar rebuilt from visible features only, scored with the shared exact evaluator.

| N | STRAIN-RIDGE (HOLDOUT-DTI) | matched incumbent lattice | ratio |
|---|---|---|---|
| 20,000 | 0.2023 | 0.0420 | 4.8× |
| 50,000 | 0.2285 | 0.0891 | 2.6× |
| **37,654 (shipped)** | **0.2244** | **0.0715** | **3.14×** |
| 70,000 | 0.2264 | 0.1131 | 2.0× |

Paired cluster bootstrap over 29 withheld blocks: candidate DTI 95 % CI [0.035, 0.396], control [0.054, 0.075], ratio CI [0.64, 5.51], **P(ratio > 1) = 0.958**. Receipts: [`strain_ridge_holdout.json`](evidence/strain_ridge_holdout.json), [`strain_ridge_ci.json`](evidence/strain_ridge_ci.json).

* **Design check** — the pre-registered 300 m minimum separation was swept after the fact and is optimal; 500 m loses 17 % of holdout DTI. Receipt: [`strain_ridge_sep_sweep.json`](evidence/strain_ridge_sep_sweep.json).

**The critical caveat.** The holdout truth is *mapped* traces; the leaderboard truth is *unmapped* faults. Those are anti-correlated here. The 3.14× therefore proves the placement mechanism works, and proves nothing about leaderboard gain. That sentence is the most important one on this page.

### 5. Hypothesis register — what was tried, what was not

| # | Hypothesis | Physical signature | Status |
|---|---|---|---|
| H1 | **STRAIN-RIDGE off-catalogue blind faults** | geodetic strain + seismicity + LiDAR scarp ridge | **IMPLEMENTED · holdout 0.2244 vs 0.0715 · PROMOTE** |
| H2 | Magnetic tilt-derivative zero-convergence | RTP / upward-continued TMI | tested · magnetic ridge alone **0.0396 vs 0.0489 uniform** → negative |
| H3 | Radiometric Th/K alteration halo, cover-stratified | GeoDAWN K/Th/U | tested · point AUC 0.44–0.48 → negative |
| H4 | 2-m probe temperature residual kriging | INGENIOUS shallow temperature archive | **untried** — public and unused; the strongest remaining lead |
| H5 | Fracture-mechanics tip step-over dilation | elastic crack-tip dilatation | untried · needs the login-gated 19-band strain tensor |

Negative results are deliverables: **raw pointwise geophysics is a weak fault predictor on this grid** (AUC 0.44–0.58). Signal appears only after (a) the structure-tensor ridge transform and (b) adding the strain/seismicity corridor prior.

---

## Competition & data (official links for manual review)

- Competition: <https://www.drivendata.org/competitions/306/competition-doe-gems/> · [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) · [data (login)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- Official rules / submission PDF: <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
- Reference solution: <https://github.com/drivendataorg/gems-prize-reference-solution>
- GeoDAWN airborne magnetics + radiometrics: USGS, DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ), ScienceBase item [657e1d85d34e23d3533209f7](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) — 13 grids per survey block (`dem, k, rtp, tc, th, thk, tmi, tmi_hg, tmi_vg, u, uk, upcont_tmi150, uth`), 50 m, EPSG:32611
- INGENIOUS regional data (geodetic strain rate, earthquake rate density, wells/springs): <https://gbcge.org/current-projects/ingenious/>
- USGS Quaternary Faults database: <https://earthquake.usgs.gov/arcgis/rest/services/qfaults> (public mirror used here: <https://github.com/jklinck/geothermal_research>)
- CRS: <https://epsg.io/32611> · Metric: <https://en.wikipedia.org/wiki/Tversky_index>

### Reproducing the submission

```bash
pip install -r requirements.txt && npm ci
# 1. warp every official layer to the 100 m competition grid
python scripts/prepare_cube.py --sample data/bridge/sample_submission.tif \
    --geodawn-dir <geodawn tiffs> --ingenious-dir <ingenious root> \
    --lidar-tif <lidar_scarp_features_u8.tif> --out .cache/work/cube.npz
# 2. rasterise the COMPLETE fault database (not the bridge copy)
python scripts/prepare_qfaults.py --shp <qfaults.shp> --sample data/bridge/sample_submission.tif \
    --labels data/bridge/labels.tif --out-dir .cache/work
# 3. build (deterministic: re-running reproduces SHA-256 6d00f58a…)
python scripts/build_strain_ridge_submission.py --cube .cache/work/cube.npz \
    --qfaults .cache/work/qfaults_100m.npy --sample data/bridge/sample_submission.tif \
    --labels data/bridge/labels.tif --out-dir docs/downloads \
    --stem gemsass2-strainridge-offcat-37654d-20261030T025503Z --n-dots 37654
# 4. gates
python scripts/validate_tif.py docs/downloads/<stem>-zeros.tif --sample data/bridge/sample_submission.tif --out evidence/validator-<stem>-zeros.json
python scripts/uniqueness_gate.py --candidate docs/downloads/<stem>-zeros.tif --out evidence/strain_ridge_uniqueness.json
python scripts/holdout_bootstrap.py --cube .cache/work/cube.npz --shp <qfaults.shp> --sample data/bridge/sample_submission.tif --out evidence/strain_ridge_ci.json --n-dots 37654
python scripts/estimate_family_score.py --n-dots 37654 --contamination-pct 0
python scripts/assemble_submission_audit.py --stem <stem> --run-card evidence/strain_ridge_run_card.json --uniqueness evidence/strain_ridge_uniqueness.json --out docs/downloads/<stem>-audit.json
```

---

## Navigation

- **[Download page](docs/index.html)** · **[Executive summary](docs/executive-summary.html)** · **[Why 0.2778 scored](docs/method.html)** · **[Sources](docs/sources.html)**
- Run card: [`evidence/strain_ridge_run_card.json`](evidence/strain_ridge_run_card.json)
- Forensics: [`nine_site_forensics.json`](evidence/nine_site_forensics.json) · [`nine_site_pairwise_overlap.json`](evidence/nine_site_pairwise_overlap.json) · [`catalogue_completeness.json`](evidence/catalogue_completeness.json) · [`candidate_catalogue_distance.json`](evidence/candidate_catalogue_distance.json)
- Holdout: [`strain_ridge_holdout.json`](evidence/strain_ridge_holdout.json) · [`strain_ridge_ci.json`](evidence/strain_ridge_ci.json) · [`strain_ridge_sep_sweep.json`](evidence/strain_ridge_sep_sweep.json)
- Gates: [`strain_ridge_uniqueness.json`](evidence/strain_ridge_uniqueness.json) · [`score_estimate.json`](evidence/score_estimate.json) · [`validator`](evidence/validator-gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.json)
- Irregularities ledger: [`IRREGULARITIES.md`](IRREGULARITIES.md)

---

## Limitations and next steps

**Limitations that constrain the score**

1. **No organizer truth and no receipt.** The 19-band `training_features.tif` and the private test labels are login-gated. Every historical score in the brief is user-reported. No local check can guarantee portal acceptance.
2. **The gain is small.** +0.008 over 0.2778. The nine-site family spans 0.034 of score in total; there is no large win available inside its geometry.
3. **0.4413 is not reachable from here.** Reaching it requires roughly a 60 % higher truth-recovery rate per dot at the same budget. That needs a detector trained against the actual truth, which is login-gated.
4. **Holdout ≠ leaderboard.** The blocked holdout validates *placement machinery* against mapped traces. The leaderboard ranks catalogue fidelity in reverse, so the 3.14× is not spendable score.
5. **The bridge catalogue is a decimated stand-in.** 60,988 cells versus 156,418. Any legacy holdout built on it inherits a 2.6× under-count.
6. **Statistical power is thin.** 29 withheld blocks give a ratio CI of [0.64, 5.51]; "better than the incumbent" is supported at 95.8 %, not proven.
7. **Third-party LiDAR stack.** The 12-band scarp raster comes from a public mirror of a USGS-3DEP-derived product; provenance is the mirror, not the organizer.

**Work for the next session**

1. **Submit and record the receipt.** One real number converts every "MODEL ESTIMATE" here into a calibrated observation — worth more than another experiment.
2. **Fit the transfer constant once a receipt exists.** Today the holdout-to-leaderboard mapping is unknown, which is why the 3.14× is deliberately unspent.
3. **Test H4 (2-m temperature probes).** Public, unused, and the only untried field with a genuinely different physical mechanism.
4. **Grow the uniqueness registry.** Only 19 rasters are checked; the wider GEMSDOE corpus is ~90 sites and is not mirrored locally.
5. **Sweep contamination beyond zero.** Negative contamination is not possible, so the only remaining axis inside this family is *which* off-catalogue cells to pick — i.e. yield. That is the H4/H5 work.
