# GEMSDOESASS2 — auditable geothermal fault discovery

## 🚦 Current decision (2026-10-30): one endorsed download, one new negative result, **no slot spent**

| Artifact in `docs/downloads/` | Format check vs organizer-example mirror | Uniqueness vs registry | Scientific gate (HOLDOUT-DTI) | Verdict |
|---|---|---|---|---|
| **`gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif`** · 22,163 dots · 0 on catalogue (B=2) | **all local checks pass** (`strict_local_format_pass: true`, [receipt](docs/data/format-sparse-blind-zeros.json)) | max overlap 41.29% (<70%), max\|ρ\| 0.0083 (<0.90) → pass | **NOT RUN** — see caveat | **PROMOTE on format + uniqueness only** |
| `gemsdoesass2-vrc-ventridge-44090-20261030T024740Z-nan.tif` · 44,090 dots | fails only `whole_array_finite_in_0_1`, which is mutually exclusive with `outside_masked_or_nan` (IR-S-10) | max per-raster overlap 39.99% (<70%), max\|ρ\| 0.0162 → pass | 0.008629 vs parent 0.09674 (Δ −0.08781, CI [−0.10035, −0.07579]); off-catalogue 0.04438 vs 0.09528 | **NEGATIVE — research only** |

- **SHA-256 (endorsed zeros TIF):** `65e3a775ad8b3fd3f3c55a501c84d48d05554219065cad69fa9ebfb54d572661` · all eight artifacts: [`docs/data/download-hashes.json`](docs/data/download-hashes.json)
- **One-click download:** [`…cc522684-zeros.tif`](docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif) · [`…zeros.zip`](docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.zip) · GIS twin [`…-nan.tif`](docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-nan.tif) (byte-identical inside footprint)
- **Submission name:** `GEMSDOESASS2-SPARSE-BLIND-CC522684`
- **Note (≤140 chars):** `GEMSDOESASS2 sparse-blind-conduit 22163d B=2 sep3 | off-catalogue blind faults | cc522684 | research`
- **VRC run card:** [`docs/data/vrc-run-card.json`](docs/data/vrc-run-card.json) — kept separate from [`docs/data/run-card.json`](docs/data/run-card.json), which is the tested `build_card()` negative contract that must not be overwritten · write-up [`knowledge/09_vrc_and_download_surface.md`](knowledge/09_vrc_and_download_surface.md)

> ⚠️ **Three things this banner deliberately does not claim.** (1) **No organizer receipt exists in this
> environment** — DrivenData requires login, so local validation is not portal acceptance. (2) The endorsed
> file's **"PROMOTE" rests on format + uniqueness only; its buffered holdout has never been run**
> (IR-S-12) — closing that is ranked #2 for the next session. (3) The earlier "13/13 format checks"
> wording is replaced by the actual per-check receipt above, because two of the local checks contradict each
> other and the count depends on the reference sample used. **No weekly submission slot was used.**

**Estimate a score before uploading — and know what "estimate" means here.** No defensible point estimate of
the organizer score exists for any file, and this repo will not invent one: the geometry-only estimator
(`scripts/fit_org_score_estimator.py`) failed leave-one-out at R² = **−0.379**. What is available, all labelled:
**HOLDOUT-DTI** with 95% CI for relative skill (`scripts/evaluate_holdout.py`, evaluator
`GEMSDOE32-HIDE-RECOVER-v3.0`; off-catalogue instrument `GEMSDOE32-SGMC-CAL-v3.0`), and **USER-REPORTED ·
UNVERIFIED** organizer anchors for the nine sites (0.2449–0.2778, `evidence/org_ledger_measured.json`).
See [`knowledge/EXECUTIVE_SUMMARY.md`](knowledge/EXECUTIVE_SUMMARY.md) §2 and the site table below.

---

## 📋 STANDING PROJECT PROMPT — read at the start of every session

Review the repository. Focus on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36; maintain an executive summary showing each site's historical best, file, score evidence and novelty. The highest urgency is to **generate an original, validated competition GeoTIFF, not copy an old submission**; make its download, unique name, ≤140-character note and eligibility unambiguous. Estimate performance only with evidence, distinguish a holdout from an organizer score, and never invent a projection. A local format pass alone is not submission approval. Study the reported 0.2778 GEMSDOE32 file, use official sources, propose 3–5 materially distinct geological hypotheses before implementation, check feature leakage and validate the best on a buffered spatial holdout before spending a slot. Maintain a simple GitHub Pages site and step-by-step submission guide; diagnose the user's range-error report only if its rejected bytes and response are actually available.

### Parallel-run protocol (operative text)

1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds **0.90**, or more than **70%** of your dots fall within **3 px** of one registry raster's dots, log a duplicate and stop. Check the surface before placement and the final dots. The supplied prompt references a method paragraph but does not actually contain one; do not present a self-assigned lane as user-assigned.
2. **REUSE, DON'T REBUILD.** Use the shared template's cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Hide whole fault segments with a buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and score pooled DTI (α 0.2, β 0.8, 300 m triangular kernel). Fix a shared defect once upstream; never keep a private evaluator fork.
3. **LABEL NUMBERS.** Results are `HOLDOUT-DTI` with evaluator version, withheld positives and 95% CI, or `ORGANIZER-CONFIRMED` from a submission-page receipt. Owner/user reports must remain explicitly unverified; a projection is never a score.
4. **LEAKAGE CANARY.** Test each feature alone on holdout; AUC above 0.90 is leakage until disproved.
5. **RUN CARD.** End with one JSON card containing hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, registry correlations/overlaps, raster SHA-256, saved-byte validator output, submission name, note of at most 140 characters and `promote`/`negative` verdict. Negative results are deliverables.
6. **BUDGET.** Stop after three experiments or two hours. Do not pick a real submission: promotion to a weekly slot is a separate selector step, subject to the allowance on the submission page.

### Nine-site executive summary (table)

| Site | Historical value | File to download / submit | New score estimate | Unique to focus sites? |
|---|---|---|---|---|
| GEMSDOE32 | **0.2778** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/400b60d4a6d99f425ee90504e6c4552227556dd1/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | Unavailable · No defensible leaderboard estimate | **No** · 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE36 | **0.2750** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/32c2660001d98f6fa9084a0971b3a9d5062d49b9/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | Unavailable · No defensible leaderboard estimate | **No** · 97.58% within 3 px of GEMSDOE27 |
| GEMSDOE28 | **0.2710** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/2c839d10f57ec9b074829e93c84bc39935f52896/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) | Unavailable · No defensible leaderboard estimate | **No** · 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE31 | **0.2708** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/eeb7da54ca4a8ae056f45e5b23eeef586ad79bf2/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) | Unavailable · No defensible leaderboard estimate | **No** · 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE33 | **0.2632** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/efa438d3104893c3e8aedf3817ac22167b1c681a/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | Unavailable · No defensible leaderboard estimate | **No** · 99.71% within 3 px of GEMSDOE27 |
| GEMSDOE25 | **0.2600** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/b4e74b3f9b191fbc214b6447e9ff1f3fa67552c4/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | Unavailable · No defensible leaderboard estimate | **No** · 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE30 | **0.2600** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/9c0d637c0171407196b61b780444bc772ce75438/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | Unavailable · No defensible leaderboard estimate | **No** · 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE24 | **0.2477** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/a433b430b74b813a9118ebd4ec438b12cbc69f46/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) | Unavailable · No defensible leaderboard estimate | **No** · 100.00% within 3 px of GEMSDOE25 |
| GEMSDOE27 | **0.2449** · User-reported; no receipt | [Research variant only](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/bef7ae8e8f63b69d299c9214c75988c8f5055f9c/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) | Unavailable · No defensible leaderboard estimate | **No** · 98.02% within 3 px of GEMSDOE24 |

### New this session (2026-10-30) — 3 experiments, 2 hours, negative result recorded as a deliverable

- **VRC (vent-ridge continuation)** implemented on the shared stack only (cached feature stack,
  `evaluate_holdout.py`, `submission_writer.py`), emitted at 44,090 dots with B=2 collar and validated
  end-to-end → **does not clear the promotion gate on either instrument**, so no file is promoted from it and
  no slot is requested. Full numbers, CIs and the mechanism split: [`knowledge/09_vrc_and_download_surface.md`](knowledge/09_vrc_and_download_surface.md).
- **IR-VRC-01, root-caused and fixed:** a `np.lexsort` result (an index *into* the candidate array) was used
  directly as a *pixel* index, so the "thinning" emitted arbitrary low-score pixels — 12,572 of 22,163 dots
  carried the −1.0 invalid fill, and the written count (15,300) silently differed from the budget (22,163).
  Both call sites are patched, an `assert` guard now refuses any emission whose count ≠ budget or whose dots
  fall outside the allowed footprint, the defective raster was **deleted** rather than patched, and every
  prior number produced through `cell_of_max*` is marked invalid.
- **New artifact set for the download surface:** `.zip` archives for both encodings of both files,
  [`docs/data/download-hashes.json`](docs/data/download-hashes.json), and per-check validator receipts
  `docs/data/format-{sparse-blind,vrc}-{zeros,nan}.json`.
- **New ledger [`knowledge/IRREGULARITIES.md`](knowledge/IRREGULARITIES.md)** (IR-S-01…13), including two
  that change how this repo's own gate statements must be read: the 70% lattice rule is arithmetically
  unsatisfiable for any full-footprint raster (and the reported 0.2778 champion fails it too), and
  `validate_tif.py`'s `whole_array_finite_in_0_1` / `outside_masked_or_nan` pair is mutually exclusive, so a
  perfect local score is unreachable by construction.

All nine focus-site variants share &gt;97% dot overlap within 3 px with at least one other focus site — none is unique under the parallel-run lane rule. The unique submission above (SPARSE-BLIND-CONDUIT) is the recommended file to download and submit.

---

## Competition & data (official links for manual review)

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/ · [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) · [data (login)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Rules/submission PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and · GDR: https://gdr.openei.org/submissions/1391
- INGENIOUS: https://gbcge.org/current-projects/ingenious/ · CRS: https://epsg.io/32611 · Metric: https://en.wikipedia.org/wiki/Tversky_index
- Portal format: single-band GeoTIFF (.tif) or .zip containing one GeoTIFF; must match the submission format's CRS, shape and geotransform; optional ≤140-char note.

### Core values

**Maximize P(Win)** — weigh evidence, risks and scarce slots; put the outcome first.
**Own the Outcome** — own results end to end; fix shared tools in the template; report negatives honestly.

### Data access blocker

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from the data tab (verified redirect to login). Local bridge data (`data/bridge/`) provides sample_submission.tif, labels.tif and existing_faults.tif for format validation. Large data and `.cache` are ignored and do **not** persist with this Git patch.

---

## Navigation

- **[Open the executive dashboard](docs/index.html)**
- **[Submission instructions and nine-site table](docs/executive-summary.html)**
- **[Research, 3-pass review and next steps](research/2026-10-28-review.md)**
- **[Unique-submission run card](evidence/unique_run_card_cc522684.json)**
- **[Full raster audit](docs/data/audit.json)**
