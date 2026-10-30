# Irregularities ledger — pointer

The canonical ledger is the repository-root [`../IRREGULARITIES.md`](../IRREGULARITIES.md): IR-01…IR-12,
review passes 1–3, session 3 (IR-S-01…10), **review pass 4 — 2026-10-30** (IR-S-11…22, the STRAIN-RIDGE /
format-estimate branch) and **review pass 5 — 2026-10-30** (IR-S-23…31, this branch: the emitter bug, the
download surface, and the holdout-availability correction). It lives at the root because GitHub Pages publishes
`docs/` only, so a page under `docs/` must not link outside `docs/`.

Numbers to know before quoting any gate statement:

- **IR-S-01 / IR-S-03 / IR-S-21** — the literal 70% lattice rule is saturated: only 6,649 of 5,167,373
  footprint cells lie >3 px from the pinned `r13` lattice, so ≥82.34% overlap is arithmetically forced at
  37,654+ dots; the reported 0.2778 champion, the promoted STRAIN-RIDGE file (99.37%) and this branch's VRC
  candidate (1.000) all fail it. A seeded random placement at the same budget scores 99.91%, i.e. the rule
  cannot distinguish design from noise.
- **IR-S-23** — `validate_tif.py`'s `whole_array_finite_in_0_1` and `outside_masked_or_nan` are mutually
  exclusive, so `strict_local_format_pass: true` is unreachable for a NaN-outside file and exactly one of the
  two passes for any encoding. "N/N checks" is meaningless without its reference sample (IR-S-28).
- **IR-S-24** — the claim "no holdout can be run here" is only half true: the CLI
  `scripts/evaluate_holdout.py` is a fail-closed stub, while the library `src/gems_sass2/holdout.py`
  (`GEMSDOE32-HIDE-RECOVER-v3.0`, `GEMSDOE32-SGMC-CAL-v3.0`) runs and produced real HOLDOUT-DTI + paired
  bootstrap CIs on 2026-10-30. What is missing is the run for a given raster, not the tool.
- **IR-S-30** — this branch and PR #26 encoded opposite policies and PR #28 resolved it in favour of promoting
  one file; the flip-flop itself is the finding, and `IR-VRC-01` is the alias of IR-S-23.

Nothing in this ledger is a score claim: organizer values stay USER-REPORTED · UNVERIFIED, and a MODEL ESTIMATE
is never written as a score.
