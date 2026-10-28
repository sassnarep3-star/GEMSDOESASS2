# GEMSDOESASS2 — Executive Summary (current checkout)

## Candidate and safety boundary

- **Current generated artifact:** `docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif`
- **ZIP:** `docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.zip` (one TIFF member)
- **TIF SHA-256:** `28bb9419d592797dcac1bfb1eb19fcffa7581a51718230f1f4f957a3e3d610d6`
- **ZIP SHA-256:** `b5f0f1f7469155c05f9b2275f00e4b8325bd3eaca24624fe90aa947c7b92e98d`
- **Name:** `GEMSDOESASS2-HVFD-EXP3-HYDROCOLLINEAR-37654-fc98343e`
- **Note:** `GEMSDOESASS2 hvfd-exp3-hydrocollinear LOQO B=2 37654px HOLDOUT-DTI=0.1184 blind8km=0.1763 max3pxOv=68.3%`
- **Local validation:** single-band float32, EPSG:32611, `3730×3292`, matching transform, finite `[0,1]`, strict local format pass, zero outside the reference footprint.
- **HOLDOUT-DTI:** `0.11842` (`gems57-pooled-hide-v2`, `N=11,321` withheld positives, 95% CI `[0.10255, 0.13426]`); blind `0.17630` (`spatial.folds`, `N=60,988`, 95% CI `[0.15434, 0.19659]`).
- **Uniqueness:** 451 available-registry rasters checked; maximum post-placement Spearman `0.06540`, maximum 3-pixel overlap `68.27%`. Registry completeness is not proven.
- **Selector status:** **OK TO DOWNLOAD: YES. OK TO SUBMIT: NO.** The full receipt is [`evidence/hvfd_exp3_run_card.json`](../evidence/hvfd_exp3_run_card.json). Research `verdict=promote` is not a live-slot authorization.

## GEMSDOE32 and the nine-site audit

The reported `GEMSDOE32` value `0.2778` is the highest historical value in the nine-site ledger, but it is **USER-REPORTED / UNVERIFIED** because no submission-page receipt tying the number to the exact raster is bundled here. Its H19-5 pruning, spacing, and zero-credit catalogue-collar lineage explains the reported result without upgrading its provenance.

The nine sites are `GEMSDOE24`, `25`, `27`, `28`, `30`, `31`, `32`, `33`, and `36`. Their exact historical best filenames, reported values, duplicate-family status, and source links are maintained in [`README.md`](../README.md), [`docs/executive-summary.html`](../docs/executive-summary.html), and [`evidence/nine_sites_audit.json`](../evidence/nine_sites_audit.json).

## Reproduction and limitations

The full feature cache is absent from this checkout. The tracked `data/bridge` files are only a geometry/format witness and not authenticated training or private holdout truth. No new experiment, organizer submission, live score, or weekly slot is claimed. Before a future selector decision, restore the hash-pinned feature stack, rerun the shared evaluator/writer, refresh the registry and current official feed, and attach a submission-page receipt before labeling any portal number `ORGANIZER-CONFIRMED`.
