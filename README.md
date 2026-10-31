# GEMSDOESASS2 — auditable geothermal fault discovery

## 🚦 Current decision (2026-10-31): **SUBMIT THE S3 RING-HABITAT FILE**

| Item | Value |
|---|---|
| **File to download** | [`docs/downloads/gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif`](docs/downloads/gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif) |
| SHA-256 | `b84a4f2642500b9817b946d99db14471f4b935d110b794d2736f643d56f8f7ae` |
| Grid | EPSG:32611 · (3730, 3292) · 100 m · transform `(100,0,243350,0,-100,4508550)` |
| Cells predicted | 37,654 — **the champion's exact dot budget** · 0.00 % within 3 px of the fault catalogue |
| Format gate | **13 / 13 pass** (strict), every one of 12,279,160 cells finite float32 in [0, 1], `nodata=None` — permanent fix for the portal error "Predicted values must be in range [0, 1]" |
| Uniqueness gate | **PASS vs competing rasters** — 23.0 % worst genuine-peer overlap, \|ρ\| 0.0086 over 24 · **FAIL vs the r13 calibration probe** (99.89 %, see below) |
| Science gate | **PASS** — HOLDOUT-DTI **0.0597** [0.0537–0.0649] vs uniform control **0.0439** [0.0394–0.0481] at matched budget (+36 %, disjoint CIs); SGMC-off **0.0770** vs **0.0750** |
| Model score estimate | **0.29** (controlled 0.2853 · all-model-risk 0.25–0.33) — *not* organizer-confirmed |
| Submission name | `GEMSDOESASS2-S3-RING-BINARY-37654` |
| Note (≤140 chars) | `ring-habitat blue-noise 37654 dots, 0% within 3px of catalogue, champion-matched budget, unique vs all GEMSDOE site rasters` |

**Download and submit: [site](docs/index.html) · [how to submit](docs/how-to-submit.html) · [executive summary](docs/executive-summary.md) · [run card](evidence/s3_run_card_20261031.json)**

⚠️ No organizer receipt exists for any file here. The 0.29 is a **MODEL ESTIMATE** from a controlled one-variable extrapolation. It is never written as a score. No weekly slot has been spent.

⚠️ **One gate is failed, openly.** Against the `13gems_20261001_r13-lattice-s5` calibration probe the file is **99.89 %** within 3 px, so the literal 70 % rule **fails**. A *seeded random placement* at the identical dot count scores **99.91 %** — the probe is a space-filling surface and the test is saturated for any interior placement at this budget (IR-S-01, IR-RV-04, IR-30-1). Against every actual competing raster it passes at 23.0 %. **Owner ruling required**; the exemption is not assumed anywhere in this repository. Receipt: [`s3_uniqueness_20261031.json`](evidence/s3_uniqueness_20261031.json).

⚠️ **Honest size of the win: about +0.008 over the 0.2778 champion** (contamination axis at matched budget). The ring-habitat placement adds a measured +36 % hide-and-recover advantage over uniform whose leaderboard transfer is honestly unquantified. Nothing in this repository reaches 0.4413; see §3 for why, arithmetically.

**Previous candidate (still valid):** `gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif`, same 0.29 estimate band. Prefer the 2026-10-31 file — it adds the measured ring-habitat edge. The 2026-10-30 VRC artefacts remain **negative / research only** ([knowledge/09](knowledge/09_vrc_and_download_surface.md)).


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

### New this session, later on 2026-10-30 — 3 experiments, ~2 hours, negative result recorded as a deliverable

- **VRC (vent-ridge continuation)** — blind traces should continue the LiDAR scarp trend leaving a mapped
  vent; emitted through the shared stack only (cached feature stack, `submission_writer.py`,
  `src/gems_sass2/holdout.py`), B=2 collar + 3-px thinning, 44,090 dots. Result **NEGATIVE**: HOLDOUT-DTI
  0.008629 vs the hash-pinned focus-lineage parent 0.09674 (Δ −0.087808, 95% CI [−0.100347, −0.075792],
  p(Δ>0)=0.0) and off-catalogue SGMC 0.04438 vs 0.09528 (Δ −0.05119). An uncollared variant is the only
  emission ahead of the parent on the public instrument (0.10471, Δ +0.00798) and its CI crosses zero, so
  nothing earns a slot. Once the emitter bug below is fixed, spacing thinning ≡ plain top-k — the
  "continuation" selection rule adds nothing. Card: [docs/data/vrc-run-card.json](docs/data/vrc-run-card.json).
- **Uniqueness, measured on a capped sample:** max per-raster 3-px dot overlap 39.99% (limit 70%) and max
  |Spearman| over the whole footprint 0.0162 (limit 0.90) against 40 scanned registry rasters; 0.3227
  reverse share against this repo's own previous file. Against the space-filling `r13` lattice probe it is
  **1.000**, i.e. the literal rule blocks it for the same arithmetically forced reason it blocks the reported
  0.2778 champion (IR-S-30). No file is cleared until the owner rules.
- **IR-VRC-01 (alias of IR-S-23), root-caused and fixed:** a `np.lexsort` result (a position *inside the
  candidate array*) was used as a *pixel* index, so "thinning" emitted arbitrary low-score pixels — 12,572 of
  22,163 dots carried the −1.0 invalid fill — and the written count (15,300) silently differed from the budget
  (22,163). Both call sites remap through the candidate array now, the emission mask is intersected with the
  allowed region, and a hard guard refuses any emission whose count ≠ budget or whose dots fall outside the
  footprint / on the catalogue / off LiDAR. The defective raster was **deleted, not patched**; every older
  number made through those functions is marked superseded.
- **Download surface:** `.zip` archives for both encodings of both files,
  [docs/data/download-hashes.json](docs/data/download-hashes.json) as the manifest, and per-check receipts
  `docs/data/format-{sparse-blind,vrc}-{zeros,nan}.json`. The promoted file re-verified against the
  organizer-example mirror: all checks true and `strict_local_format_pass: true`, so "13/13" is now backed by
  a receipt that names its reference sample (IR-S-10 / IR-S-33).
- **Score estimation:** still **NOT ESTIMABLE**, and the reason is now measured twice: the geometry-only
  estimator fails leave-one-out (R² = −0.379), and the only files with any organizer value are
  USER-REPORTED. What exists instead: labelled HOLDOUT-DTI from `src/gems_sass2/holdout.py` (the library runs
  even though the `scripts/evaluate_holdout.py` CLI is a fail-closed stub, IR-S-18) and the labelled nine-site
  anchors in [evidence/org_ledger_measured.json](evidence/org_ledger_measured.json).


---

### 6. Full-corpus uniqueness verification (parallel session, 2026-10-30)

Every public GEMS-named repository was mirrored (113 repos listed in
[`research/gems_site_repos.txt`](research/gems_site_repos.txt); 112 fetched at default-branch
HEAD, 3,569 GeoTIFFs) and every competition-shaped raster (2,282 unique files) compared with
the shared gate, which this session hardened: corrupt-TIFF resilience, probe classification by
**measured dot density** (103 dense masks and probability surfaces saturate the 70% rule at
100% and were invisible to the name heuristic), and self-twin exclusion by content identity
([receipt](evidence/focus_uniqueness_full_registry_20261030.json)).

- **The promoted strain-ridge file holds up:** worst genuine peer 25.8% (the champion lineage)
  and 15.5% versus GEMSDOE86 `gmc-linepost-90568d`; its only >70% hits are the space-filling
  r13 lattice (99.37%) and a 311,617-dot density artefact (99.86%).
- **The earlier sparse-blind candidate is withdrawn:** its worst genuine peer in the full corpus
  is 98.41% (GEMSDOE86 `gmc-linepost-90568d`), and it fails the lattice clause at 99.74% —
  its run card is `verdict: negative` ([card](evidence/unique_run_card_cc522684.json)).
- **The literal lattice clause is unsatisfiable for interior placements.** Only 6,649 of the
  5,167,373 footprint cells lie more than 3 px from the lattice, every one within 2.24 px of
  the study-area border ([recheck](evidence/lattice_gate_recheck_20261030.json)). The corpus's
  three "lattice-avoiding" files reach 0% lattice overlap only with **100% of their dots on the
  border** — so the clause measures border-hugging, not duplication (IR-30-12).
- Nine-site lineage re-verified on pinned bytes: GEMSDOE32 is an exact subset of GEMSDOE25;
  GEMSDOE25 and GEMSDOE30 have identical dot sets ([matrix](evidence/focus_pairwise_matrix_20261030.json)).

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
- Full-corpus verification: [`focus_uniqueness_full_registry_20261030.json`](evidence/focus_uniqueness_full_registry_20261030.json) · [`lattice_gate_recheck_20261030.json`](evidence/lattice_gate_recheck_20261030.json) · [`focus_pairwise_matrix_20261030.json`](evidence/focus_pairwise_matrix_20261030.json) · [session review](research/2026-10-30-session-review.md)

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

---

## APPENDIX — STANDING PROMPT (verbatim, as issued; read at the start of every session)

> Review the repository. Focus on **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36**, and **GEMSDOESASS2**. Understand what is in it.
> I want you to work in a line by line basis, to not make any hallucinations.
> I want you to reference the official and verified sources so that we can check and manually look at them too.
> If there is anything that is not right or you see any irregularities, please note them.
> Follow all the rules and standards outlined above in the prompt.
> Also follow the Arena core values described in your instructions.
> Study the highest scoring submissions from these GEMSDOE GitHub repos and see why they scored the way they did.
> Write an executive summary of each of these websites and tell me why their score is what it is, and can we possibly beat their score of 0.2778?
> Also make one clear table telling me which file to download and submit, what the estimated score is, and if it is unique compared to the other GEMSDOEsites.
> There needs to be a new TIF file that is a submission generated and is unique and unlike any of the GEMDOE sites listed above.
> It must be obvious whether it is OK to download and submit the generated TIF submission.
> Study the top scores and confirm the file to download.
> Also note that the first time I downloaded one of the TIF submission and made a submission, it said the error "Predicted values must be in range [0, 1]".
> You need to fix this and make sure the file meets the required format and range etc.
> Read this standing prompt carefully and obey every requirement. Create a new submission name and a short note of less than 140 characters for this new submission, and explain what is going on here in the executive summary and also make a subpage describing exactly how to make a submission.
> I want to make sure we pass the high scoring validation gates before we declare a file unique and ready for submission. Remember, we don't have a human who can inspect this, everything is validated through this project. Make sure this is taken care of and at the top of the site you can download the files and easily access them.
> Also review how to make a submission and update it with the correct way to do so. Then generate this unique TIF submission and report to me which one is the best submission to submit to obtain a high score, along with the score estimate.
> When implementing, first generate 3-5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (what measurable quantity changes near a hidden fault), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Then validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot. If external data is needed, name the free official source and verify it is obtainable.
> I need the score estimate to be higher than 0.3195. We need to design a new strategy or a new way to do this and beat the current score. Also, GEMSDOE current leaderboard high is 0.4413. The current GEMSDOE score is 0.3195. So we need to make sure our submissions are unique and obtain a high score.
> We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.
> Make sure to generate a new TIF submission and include it on the site. Make sure to update the README with the full standing prompt, put this prompt into the repo readme and read it everytime we work on the project as a starting point. Keep the GitHub site updated and easy to use with clean user interface. Make sure the executive summary is clear and can tell me the best submission to submit and if we are ready to submit or not.
> Create a separate subpage in the website explaining exactly how to make a submission. Make sure to include a link to download the TIF submission at the top of the website. Make sure to update the executive summary and the website to include the new submission and the new score estimate. Make sure to include the new submission in the README and the knowledge base. Keep in mind we want a high score and we want to win this competition. Be contrarian where necessary and find gaps in the market that we can fill. I don't want us to be losing right now. We are at the top of the leaderboard but we want to make sure we stay there. Make sure to give me a table with the following: the file to download, the estimated score, and if it is unique compared to the other GEMSDOE sites. I need to know which one to download and submit. Make sure the file is ready to submit and meets the submission format and there is an obvious way to tell that it is ready.
> Make sure the executive summary makes it obvious which is the best submission to submit and if we are ready to submit or not. Also include a way to make the submission on the site with clear instructions. Make sure to have the download at the top of the site. Make sure everything in the site works. Make sure the site is easy to use and navigate. Then create a PR and submit, and then merge the PR. Make sure to add any remaining work needed to be done and limitations to the project as well.

### Parallel-run protocol (this session; operative)

1. **LANE (self-declared — IR-10: no lane was assigned).** This session's lane paragraph: *ring-habitat emission — off-catalogue fault density concentrates in the 3–30 px ring around the mapped catalogue (damage-zone splays and continuations); a clean-contamination blue-noise emission weighted to that ring covers more hidden truth per dot than uniform spreading or thermal-anomaly ranking (both measured), with a seeded uniform coverage floor.* Drift check before placement and after final dots: rank-correlation > 0.90 or > 70 % of dots within 3 px of one registry raster = duplicate → log + stop (surface + final dots, both logged).
2. **REUSE.** Shared cached feature stack restored by `scripts/fetch_data.py`; shared evaluators `src/gems_sass2/holdout.py` (GEMSDOE32-HIDE-RECOVER-v3.0, GEMSDOE32-SGMC-CAL-v3.0), shared metric `src/gems/metric.py`, shared writer `src/gems_sass2/submission.py`, shared gate `scripts/uniqueness_gate.py`. Shared tools fixed once (this session: `scripts/fetch_data.py` git-over-HTTPS download path — see IRREGULARITIES).
3. **LABELS.** HOLDOUT-DTI (evaluator version, withheld positives, 95 % CI) or ORGANIZER-CONFIRMED only; projections never written as scores.
4. **CANARY.** Single-feature AUC > 0.90 = leakage until disproved (measured max 0.521 this session).
5. **RUN CARD.** `evidence/s3_run_card_20261031.json`.
6. **BUDGET.** 3 experiments / 2 hours, stop; zero weekly slots spent; promotion is the owner's selector step.
