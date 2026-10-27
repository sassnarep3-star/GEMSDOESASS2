# Concurrent main-branch candidates: independent recheck

**Decision: DO NOT SUBMIT any of these files under the unchanged literal
parallel-run protocol.** Another session merged three candidate families into
`main` while this audit was underway. We did not generate, train, rescore or
submit them. We reopened their exact zero-filled TIFF bytes from immutable
commit [`4a88f375`](https://github.com/sassnarep3-star/GEMSDOESASS2/tree/4a88f3750933e3e147312bf2a6d220f777103574),
then compared their positive pixels against the registered witnesses using the
unchanged shared-template geometry. The evidence and hashes are in
[`evidence/concurrent-main-audit.json`](../../evidence/concurrent-main-audit.json).

| Prior-session candidate | Positive pixels | Within 3 px of the registered lattice | Literal dense-surface overlap | Decision |
|---|---:|---:|---:|---|
| SCU1 (`0ab88d8a…`) | 37,000 | 99.8514% | 100% | STOP |
| TTC-A1 (`b8be5398…`) | 37,654 | 99.9549% | 100% | STOP |
| ASS2-ALEDGE (`cc854482…`) | 44,090 | 99.3241% | 100% | STOP |

The strict stop is **greater than 70%** of candidate dots within three pixels
of *any* registered raster. The lattice is a genuine dot pattern. The separate
dense-surface result is conditional on the shared template's literal
finite-positive support definition; whether a continuous raster should count
as “dots” is a protocol question, not an exemption we can invent. Pairwise
comparison of only these three or the nine highlighted sites does not satisfy
the all-registry rule. Neither their surfaces nor a complete current registry
were independently checked in this audit; the positive witness suffices to
stop, not to certify the remaining comparisons.

All three zero-filled files reopened as single-band float32 on the
**owner-mirrored** sample grid and their stored values were finite in [0,1].
The zero-filled outside-footprint cells are not marked null. These are local
format observations, not organizer acceptance and not a diagnosis of the
previous range error. Their NaN-outside variants were not rechecked here.

## Why the earlier green release claims are not sufficient

* The [SCU1 prior card](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/4a88f3750933e3e147312bf2a6d220f777103574/evidence/run_card.json)
  reports a maximum overlap against its **12 listed focus comparisons**, not
  the registered lattice and dense witness above. Its “unique” and “OK to
  submit” wording is therefore too broad. The related
  [registry manifest](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/4a88f3750933e3e147312bf2a6d220f777103574/registry/registry_manifest.json)
  does not establish a complete current registry.
* The prior SCU1 card reports **OWNER-REPORTED HOLDOUT-DTI** on evaluator
  `GEMSDOESASS2-HRv1`, 60,289 withheld positives: visible-only mean 0.01632,
  stated 95% interval [0.01076, 0.02271], versus a fixed submitted champion
  mean 0.00473, stated interval [0.00401, 0.00553]. We did not rerun these
  numbers. The [code](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/4a88f3750933e3e147312bf2a6d220f777103574/scripts/run_pipeline.py#L107-L121)
  rebuilds the candidate from visible faults but keeps the champion fixed,
  and the [evaluator](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/4a88f3750933e3e147312bf2a6d220f777103574/src/gems/holdout.py#L58-L80)
  averages per-fold DTI values and interval endpoints. This is not the
  requested pooled-component, paired shared-template comparison. These
  intervals are prior author claims, not independently validated CIs or
  evidence of a leaderboard improvement.
* The [TTC-A1 card](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/4a88f3750933e3e147312bf2a6d220f777103574/evidence/ttc_run_card_d8f85365.json)
  describes its cited holdout as **simulated**. It cannot be treated as an
  actual holdout result or organizer receipt.
* The [ASS2-ALEDGE card](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/4a88f3750933e3e147312bf2a6d220f777103574/registry/run_card.json)
  itself records a negative decision and a paired proxy interval crossing
  zero, and explicitly acknowledges that its comparison was limited to the
  focus champions. Our lattice recheck supplies an independent stop as well.

The prior work, byte files, methods and records remain in Git history and the
repository; this audit corrects the present release status, not the past
experimental record. It does not establish that a future, scientifically
validated candidate is impossible if the ambiguous registry protocol is
explicitly resolved.
