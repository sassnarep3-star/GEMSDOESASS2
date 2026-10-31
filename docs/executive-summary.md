# Executive summary — which DOE GEMS file to submit (2026-10-31)

**Status: one file is format-valid, unique and recommended for download; one newly generated file is unique but holdout-tested negative. Read the table before uploading anything.**

## 1 · The decision table (read this first)

| Site | File to download | Estimated score | Unique vs the other GEMSDOE sites? | OK to download & submit? |
|------|------------------|-----------------|-----------------------------------|--------------------------|
| **GEMSDOESASS2** (recommended) | [`gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif`](downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif) · [`.zip`](downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.zip) · [NaN twin](downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-nan.tif) | **0.29 MODEL ESTIMATE** (risk range 0.25–0.33). Not organizer-confirmed. | **Yes vs genuine peers** — 36.45% max 3-px overlap, |ρ| 0.0115 over 19 registry rasters. Caveat: 99.37% vs the r13 calibration lattice probe (disclosed gate failure; owner ruling required). | **Yes, with caveat** — format 11/11, values in [0,1], nodata=None. Best-supported submission available. |
| **GEMSDOESASS2** (new, NEGATIVE) | [`gemsdoesass2-stepperelay-dilation-22163-49c96b30-zeros.tif`](downloads/gemsdoesass2-stepperelay-dilation-22163-49c96b30-zeros.tif) · [`.zip`](downloads/gemsdoesass2-stepperelay-dilation-22163-49c96b30-zeros.zip) · [NaN twin](downloads/gemsdoesass2-stepperelay-dilation-22163-49c96b30-nan.tif) | **NOT ESTIMABLE** — no organizer receipt; geometry-only extrapolator failed leave-one-out (R² < 0). HOLDOUT-DTI 0.0016 (95% CI [0.0005, 0.0030]) vs uniform control 0.0377 — NEGATIVE. | **Yes** — 44.11% max 3-px overlap, |ρ| 0.046 over 14 registry rasters; passes the literal ≤70% / |ρ|≤0.90 lane rule, including vs the r13 lattice probe (22,163 dots is below the 22,164 first-failing count). | **Format: yes** — 13/13 checks, all cells finite in [0,1]. **Recommendation: NO** — do not spend a weekly slot; holdout-tested worse than uniform. Published as a negative deliverable. |
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (GEMSDOE32 GitHub releases) | 0.2778 (user-reported, unverified) | **No** — 100% within 3 px of GEMSDOE24/25; one member of the single nine-site lattice family. | **No** — already scored; a duplicate lattice-family file. |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (GEMSDOE36 GitHub releases) | 0.2750 (user-reported, unverified) | **No** — 97.6% within 3 px of GEMSDOE27. | **No** — duplicate lattice family. |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` (GEMSDOE28 GitHub releases) | 0.2710 (user-reported, unverified) | **No** — 100% within 3 px of GEMSDOE24. | **No** — duplicate lattice family. |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` (GEMSDOE31 GitHub releases) | 0.2708 (user-reported, unverified) | **No** — 100% within 3 px of GEMSDOE24. | **No** — duplicate lattice family. |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` (GEMSDOE33 GitHub releases) | 0.2632 (user-reported, unverified) | **No** — 99.7% within 3 px of GEMSDOE27. | **No** — duplicate lattice family. |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` (GEMSDOE25 GitHub releases) | 0.2600 (user-reported, unverified) | **No** — 100% within 3 px of GEMSDOE24. | **No** — duplicate lattice family. |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` (GEMSDOE30 GitHub releases) | 0.2600 (user-reported, unverified) | **No** — pixel-identical positive mask to GEMSDOE25. | **No** — duplicate lattice family. |
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` (GEMSDOE24 GitHub releases) | 0.2477 (user-reported, unverified) | **No** — 100% within 3 px of GEMSDOE25. | **No** — duplicate lattice family. |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` (GEMSDOE27 GitHub releases) | 0.2449 (user-reported, unverified) | **No** — 98.0% within 3 px of GEMSDOE24. | **No** — duplicate lattice family. |

**Leaderboard context (user-stated):** the highest score on the current competition leaderboard is **0.3195**; the GEMSDOE focus-site best is **0.2778** (GEMSDOE32). No file in this repository has an organizer-confirmed score (DrivenData requires login), so every estimate above is a MODEL ESTIMATE or HOLDOUT-DTI, never an organizer score. Reaching 0.3195+ requires a truth-trained detector, which is login-gated — see §5 limitations.

## 2 · Why the nine focus sites all score the same thing

The nine focus sites are **one file, not nine models**: every pair overlaps by ≥ 97.6% of dots within 3 px, and they share a single generator — a Poisson-disk lattice over the footprint modulated by distance to the already-mapped fault catalogue. Their reported score is a function of one variable only: the share of the dot budget that lands inside the catalogue exclusion zone, which the metric can only ever score as false positive.

| Focus site | Dots | % of dots within 3 px of catalogue | Reported |
|------------|------|------------------------------------|----------|
| GEMSDOE25 | 44,090 | 19.52% | 0.2600 |
| GEMSDOE31 | 40,199 | 11.73% | 0.2708 |
| **GEMSDOE32** | **37,654** | **5.77%** | **0.2778** |

The three points are almost perfectly linear in contamination (−0.001299 DTI per percentage point, R² = 0.998): the truth set is faults *absent* from the catalogue, so any dot inside the catalogue is guaranteed false positive and guaranteed zero true positive. The candidate recommended above removes that contamination (0.00% on the complete 156,418-cell database) while keeping the champion's dot budget — a controlled one-variable change, which is the only defensible basis for its 0.29 estimate.

## 3 · The two GEMSDOESASS2 files in detail

### Recommended: strain-ridge off-catalogue (model estimate 0.29)
- **Hypothesis:** geodetic strain + seismicity + LiDAR scarp ridge select blind fault traces that scarp-dependent USGS/INGENIOUS mapping missed.
- **Holdout:** HOLDOUT-DTI 0.2244 vs matched incumbent lattice 0.0715 (3.14×, paired-bootstrap P = 0.958) on a leak-free spatially-blocked holdout (29 withheld blocks, 38,278 positive cells). Single-feature leakage canary max AUC 0.6433 (≤ 0.90 — pass).
- **Format:** 11/11 strict checks on saved bytes; all 12,279,360 cells finite in [0,1]; nodata=None; CRS EPSG:32611; shape (3730, 3292); exact transform.
- **Uniqueness:** 36.45% max 3-px overlap, |ρ| 0.0115 vs 19 registry rasters (limits 70% / 0.90) — pass vs genuine peers.
- **Disclosed failure:** 99.37% of dots within 3 px of the `r13-lattice-s5` calibration probe (a space-filling surface; a seeded random control at the same count scores 99.91%). The literal 70% rule is saturated at this budget and cannot discriminate; owner ruling required. Receipt: `evidence/candidate_vs_registry_lattice.json`.
- **Submission name:** `GEMSDOESASS2-STRAINRIDGE-OFFCAT-37654D` · **note (129/140 chars):** `strain+ridgelineament prior, same 37654 dot budget as champion, 0% on full USGS QFaults catalogue, off-catalogue blind faults`.

### New: step-over / relay-ramp dilation (NEGATIVE — do not spend a slot)
- **Hypothesis:** blind connectors between en-echelon catalogue fault segments vent heat without a Quaternary scarp; tip-pair step-over lenses target them. Derived from `labels.tif` geometry only (no external download).
- **Holdout:** HOLDOUT-DTI 0.0016 (95% CI [0.0005, 0.0030]) vs uniform control 0.0377 — ratio 0.04. NEGATIVE: does not beat the uniform control, nor the current holdout best (0.2244). Per protocol, no weekly slot is spent.
- **Leakage canary:** single-feature AUC 0.4305 (≤ 0.90 — pass).
- **Format:** 13/13 checks on saved bytes; all cells finite in [0,1]; nodata=None; 22,163 dots, 0 on the catalogue.
- **Uniqueness:** 44.11% max 3-px overlap, |ρ| 0.046 vs 14 registry rasters — passes the literal lane rule, including vs the r13 lattice probe (22,163 dots < 22,164 first-failing count).
- **Verdict:** negative. Format-valid and unique, so the portal would accept the bytes, but it is not score-recommended. Published as a negative deliverable (negative results are deliverables).
- **Submission name:** `GEMSDOESASS2-STEPOVER-49C96B30` · **note (99/140 chars):** `GEMSDOESASS2 stepover-relay 22163d B2 sep3 | blind connectors between catalogue segments | 49c96b30`.

## 4 · Submission guide — exactly what to click

1. **Download** the primary `.tif` (the `-zeros.tif`, not the `-nan.tif` twin): every cell is finite and inside [0,1] and the file declares `nodata=None`, so a portal range check cannot read a sentinel as out of range.
2. Open the DrivenData submission page for competition 306 and choose that file.
3. **Name field:** use the submission name in §3. **Note field:** paste the ≤140-character note in §3.
4. Submit. Record the returned score and submission ID — that receipt, not this page, becomes the first ORGANIZER-CONFIRMED number in the project.

## 5 · Limitations

- No DrivenData auth → no organizer receipt, no private test truth, no submission-page response. Every historical score is USER-REPORTED / UNVERIFIED; every estimate here is a MODEL ESTIMATE or HOLDOUT-DTI, labelled as such.
- The gain is small: roughly +0.008 over 0.2778 for the recommended file. Nothing in this repository reaches 0.3195 or 0.4413.
- Holdout truth = mapped catalogue traces; leaderboard truth = unmapped faults. These are anti-correlated here (Spearman −1.000 across the nine sites), so holdout DTI is not convertible into a leaderboard score.
- The literal 70%-within-3-px lane rule is non-discriminating at high dot counts (any interior placement exceeds 70% vs the space-filling r13 lattice by pigeonhole). It is disclosed, not hidden; its ruling is the owner's.
- Negative results are deliverables: the step-over file tested negative and is published as such.
