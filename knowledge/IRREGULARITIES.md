# Irregularities ledger — pointer

The canonical ledger is the repository-root [`../IRREGULARITIES.md`](../IRREGULARITIES.md) (IR-01…IR-12,
review passes 1–3, session 3, and **session 2026-10-30 = IR-S-11…IR-S-18**). It lives at the root because
`docs/` is what GitHub Pages publishes, and a page in `docs/` must not link outside `docs/`.

Entries most relevant to reading the download surface today:

- **IR-S-10** — `validate_tif.py`'s `whole_array_finite_in_0_1` and `outside_masked_or_nan` are mutually
  exclusive, so `strict_local_format_pass: true` is unreachable for a NaN-outside file and exactly one of
  the two passes for any encoding. Read every "N/N checks passed" claim together with the reference sample
  used (IR-S-18).
- **IR-S-01** — the 70% lattice gate is arithmetically unsatisfiable for a full-footprint raster: only
  6,649 of 5,167,373 footprint cells lie >3 px from the pinned lattice, so the reported 0.2778 champion
  fails it (99.91%) exactly as our VRC candidate does (1.000). Owner ruling required.
- **IR-S-11** — the emitter index bug (`lexsort` position used as a pixel index) that voided the first VRC
  pass; fixed with a hard count/footprint guard, defective raster deleted.
- **IR-S-12** — the endorsed sparse-blind file is PROMOTE on **format + uniqueness only**; its buffered
  holdout has never been run.
- **IR-S-17** — all uniqueness numbers in this repo come from a capped sample (40 registry rasters), not a
  complete registry.

Nothing in this ledger is a score claim; organizer values remain USER-REPORTED · UNVERIFIED (IR-07, IR-09).
