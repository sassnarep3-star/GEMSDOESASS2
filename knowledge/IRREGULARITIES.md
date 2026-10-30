# Irregularities ledger — pointer

The canonical ledger is the repository-root [`../IRREGULARITIES.md`](../IRREGULARITIES.md) (IR-01…IR-12, review
passes 1–3, session 3 = IR-S-01…10, 2026-10-30 re-verification = IR-S-15…24, 2026-10-30 second pass =
**IR-S-25…33** plus the `IR-VRC-01` alias). It lives at the root because GitHub Pages publishes `docs/` only,
so a page under `docs/` must not link outside `docs/` — that is IR-S-09.

The entries that change how every gate statement in this repo must be read:

- **IR-S-15 / IR-S-16** — the endorsed sparse-blind file has 99.74% of its dots within 3 px of the pinned
  registry lattice (limit 70%), so it is downloadable but **not** submittable until the owner rules; the rule
  is arithmetically unsatisfiable for any interior raster (only 6,649 of 5,167,373 footprint cells lie >3 px
  from the lattice), which also blocks the reported 0.2778 champion and our VRC candidate (1.000).
- **IR-S-10** — `validate_tif.py`'s `whole_array_finite_in_0_1` and `outside_masked_or_nan` are mutually
  exclusive, so `strict_local_format_pass: true` is unreachable for a NaN-outside file and exactly one of the
  two passes for any encoding. Read every "N/N checks passed" claim together with the reference sample used
  (IR-S-32).
- **IR-S-18 / IR-S-26** — the holdout *CLI* is a fail-closed stub, but the *library*
  (`src/gems_sass2/holdout.py`) runs and produced real HOLDOUT-DTI + paired CIs on 2026-10-30. "No holdout is
  possible here" is therefore wrong; "no holdout has been run for this particular raster" is right.
- **IR-S-25** — the emitter index bug (`lexsort` position used as a pixel index) that voided the first VRC
  pass; fixed with a hard count/footprint guard, defective raster deleted.
- **IR-S-31** — all uniqueness numbers in this repo come from a capped sample (40 registry rasters), not a
  complete registry.

Nothing here is a score claim; organizer values remain USER-REPORTED · UNVERIFIED (IR-07, IR-09, IR-S-20).
