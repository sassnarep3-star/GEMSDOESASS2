# GEMSDOESASS2 — Executive Summary & Download-First Submission Guide (HVFD / SASS2-XGHF)

## 1. Candidate summary and gate status

The current saved candidate is a **genuinely generated, single-band GeoTIFF**. It is a research artifact that passes local format checks; it is **not authorized for a competition upload** in this checkout.

- **Download TIF:** [`downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif`](downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif)
- **Download ZIP:** [`downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.zip`](downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.zip) — one TIFF member only
- **TIF SHA-256:** `28bb9419d592797dcac1bfb1eb19fcffa7581a51718230f1f4f957a3e3d610d6`
- **ZIP SHA-256:** `b5f0f1f7469155c05f9b2275f00e4b8325bd3eaca24624fe90aa947c7b92e98d`
- **Candidate name:** `GEMSDOESASS2-HVFD-EXP3-HYDROCOLLINEAR-37654-fc98343e`
- **Submission note:** `GEMSDOESASS2 hvfd-exp3-hydrocollinear LOQO B=2 37654px HOLDOUT-DTI=0.1184 blind8km=0.1763 max3pxOv=68.3%` (`105 / 140` characters)
- **Local GeoTIFF validation:** **PASS** — single band, float32, `EPSG:32611`, `3730×3292`, exact sample transform, finite values in `[0,1]`, and zero outside the reference footprint. The saved strict validator reports `strict_local_format_pass=true`; the submission-writer validation reports `13/13` checks passed.
- **Leakage canary:** **PASS** — `54/54` channels, symmetric-AUC limit `0.90`, maximum `0.78508`.
- **Primary result:** **HOLDOUT-DTI** (`gems57-pooled-hide-v2`, `N=11,321` withheld positives, 95% CI `[0.10255, 0.13426]`): `0.11842`.
- **Blind result:** **HOLDOUT-DTI** (`gems57-pooled-hide-v2` with `spatial.folds`, `buffer_px=80`, `N=60,988`, 95% CI `[0.15434, 0.19659]`): `0.17630`.
- **Uniqueness gate:** **PASS against the available registry** — `451` unique rasters checked; maximum pre-placement Spearman `0.21786`, maximum post-placement Spearman `0.06540`, and maximum 3-pixel dot overlap `0.68266`. The registry is not proven complete, so this is not organizer clearance.
- **Decision:** **OK TO DOWNLOAD: YES. OK TO SUBMIT: NO.** `evidence/hvfd_exp3_run_card.json` records `verdict=promote` only for research-artifact promotion and explicitly records `ok_to_submit=false`; no weekly slot was spent.

## 2. Why the reported GEMSDOE32 value is 0.2778

`GEMSDOE32` is the highest value in the nine-site historical ledger at **0.2778**, but it is labeled **USER-REPORTED / UNVERIFIED** because this checkout contains no submission-page receipt tying that number to the exact bytes. The forensic explanation is a pruning/spacing chain: the H19-5 family removes dense self-overlap, applies a zero-credit catalogue collar, and reaches the reported 37,654-dot artifact. This explains the reported number without claiming it is an organizer-confirmed score.

The nine focus sites and their historical best files, reported values, and peer-uniqueness status are listed in the [HTML executive table](executive-summary.html#nine-site-summary). The historical artifacts are owner reports for manual review, not new candidates to submit; the family contains exact or near duplicates, including the GEMSDOE25/GEMSDOE30 byte/dot twin relationship.

## 3. Download-first, submit-last procedure

1. Download the TIF or one-member ZIP above. Verify its SHA-256 before opening or transferring it.
2. Run the local gate from the repository root:

   ```bash
   .venv/bin/python scripts/submission_preflight.py \
     docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif \
     --sample data/bridge/sample_submission.tif \
     --run-card evidence/hvfd_exp3_run_card.json
   ```

   The expected current decision is `OK TO DOWNLOAD; DO NOT SUBMIT` with exit code `2`. The bridge sample is a geometry witness, not authenticated private-test truth; replace it with an authenticated competition sample and record that provenance before a live run.
3. Do **not** upload while `ok_to_submit=false`. A holdout win, a projection, a local format pass, or `verdict=promote` never spends a weekly slot.
4. Only after an explicit selector authorizes this exact candidate and the account's weekly quota is confirmed, use the official [DrivenData submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/). Keep the upload receipt, candidate hash, submission name, note, timestamp, and slot count together.
5. Label a numeric portal result **ORGANIZER-CONFIRMED** only when copied from that submission-page receipt. Until then, it is not a score; all model metrics above remain **HOLDOUT-DTI** with their evaluator version, withheld-positive count, and 95% CI.

## 4. Sources, limitations, and current-feed plan

- [Official DOE GEMS rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — governance and prize rules.
- [Official DrivenData competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/) and [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — current instructions and authenticated data download.
- [USGS GeoDAWN](https://doi.org/10.5066/P93LGLVQ), [USGS SGMC](https://doi.org/10.3133/ds1052), and [GDR 1391](https://gdr.openei.org/submissions/1391) — public external-source references; use only when the manifest and license/provenance checks pass.

The full feature cache is absent from this checkout, so the saved experiments are not being presented as reproducible new runs here. `data/bridge` cannot substitute for training features or private holdout labels. The current-feed approach is to re-check the official competition data page, rules/administrator notices, public leaderboard, site heads, and the hash-pinned manifest before any future experiment; a changed source, registry, evaluator, or quota is an irregularity that blocks promotion until logged and reviewed. No organizer submission, live score, or weekly slot is claimed by this artifact.
