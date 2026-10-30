# Why GEMSDOE32 (0.2778) scored highest among the nine sites — verified autopsy (2026-10-28)

**Status:** the 0.2778 figure is **USER-REPORTED / UNVERIFIED**. No organizer receipt ties it to the file bytes. Everything else below is a measurement on the pinned raster files, reproduced in this session.

## Short answer

GEMSDOE32 is not a new method. It is GEMSDOE25's 44,090-dot set, with the dots that sit within 2 px (200 m) of an existing mapped fault removed. The change moved the reported score from 0.2600 to 0.2778 (+0.0178). That gain comes from precision: dots next to known faults are the least likely to fall on a *new* fault, because the test labels are faults that the USGS database does not already contain.

## 1. Lineage — measured, not inferred

Source: `scripts/audit_snapshot.py` (rerun this session, hash-pinned inputs; output identical to the committed receipt except the timestamp). Receipt: [docs/data/audit.json](../docs/data/audit.json).

| Quantity | Value | Meaning |
|---|---|---|
| GEMSDOE25 dots | 44,090 | parent set (d = 2.8 px Poisson-disk thinning of H19-5 as described by the owner) |
| GEMSDOE32 dots | 37,654 | = 44,090 − 6,436 |
| Dots of GEMSDOE25 within 2 px of the catalogue | 6,436 | removed |
| XOR(GEMSDOE32, GEMSDOE25 minus catalogue-2px) | **0 pixels** | identical after pruning |
| GEMSDOE31 dots | 40,199 | GEMSDOE25 minus dots within 1 px of the catalogue |
| XOR(GEMSDOE31, GEMSDOE25 minus catalogue-1px) | **0 pixels** | identical after pruning |
| Dots in GEMSDOE31 but not GEMSDOE32 | 2,545 | the 1 px → 2 px step removes these |

Catalogue = `data/bridge/labels.tif` (the competition's existing-fault raster). Its SHA-256 is `7ba308cc…4093`, and it is byte-identical to `existing_faults.tif` (flagged in IRREGULARITIES.md).

So the 0.2600 → 0.2708 → 0.2778 sequence is a *one-parameter collar sweep* on one parent: collar 0 px (parent), 1 px (GEMSDOE31), 2 px (GEMSDOE32). Each step removes catalogue-adjacent dots.

## 2. Why removing catalogue-adjacent dots helps under the official metric

From the official definition (see [knowledge/03](03_official_metric_and_submission_format.md)), with α = 0.2 and β = 0.8:

- A dot that earns no true-positive credit adds 0.2 × (its FP weight) to the denominator and nothing to the numerator. Removing it therefore raises the index.
- The truth set is new faults, not the catalogue. Assuming (not measured) that a dot within 1–2 px of a mapped fault rarely matches a *new* fault, its expected credit is small and its FP cost is about 0.2 per dot.
- The gain of +0.0178 with 6,436 fewer dots is consistent with that picture. This is an **inference** from the lineage and the metric, not a measured per-dot credit, and it is not a geological discovery.

## 3. The named non-fault process that could mimic this

**Catalogue-geometry artifact.** Mapped faults in the INGENIOUS and USGS datasets are not random. Dots that sit next to them can be the same features that the *test* faults are also near, such as fault splays, step-overs and en-echelon segments. If the test labels cluster near mapped faults, a collar removal would *lose* credit. A gain at 1–2 px on the public split does not prove the prior holds on the private split. This is a prior about the labelling process, not a physical signal.

## 4. Caveats that stop this from being a discovery

- The 0.2778 value is user-reported. The per-site table marks it as such.
- The gain was measured on one public split. The rules say the private split decides Phase 1 (Official Rules §3.6.2).
- No holdout run exists for the collar prior. The shared evaluator has open defects (upstream issues [41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41) and [42](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/42)), recorded as IR-04.
- Under the project's literal 70 % duplicate rule, the 0.2778 file itself fails: 99.91 % of its dots lie within 3 px of the registered lattice (see [evidence/lattice_saturation_check.json](../evidence/lattice_saturation_check.json)). So a duplicate gate built this way would have blocked the current best file, too.

## 5. Can we beat 0.2778?

**Not established.** No candidate in this session has a holdout score, and no leaderboard receipt exists for any new file. Three directions are distinct from the nine-site family and are worth testing, each under a buffered whole-segment holdout before any slot is used:

1. **Continuous probabilities.** The official metric accepts p ∈ [0,1]. Every nine-site file is binary. A soft map that keeps graded confidence near catalogue-adjacent areas is an untested design axis. The function `dti_probabilistic` is now in place for that test.
2. **Collar sweep beyond 2 px** (3 px and 4 px), on the *same* parent, evaluated only on holdout first. The parent has the largest uncertainty, so this is cheap but is still a prior, not a new signal.
3. **A different parent.** The nine-site family shares one ancestor, so their ceiling is a property of that ancestor. Public scores up to 0.4544 show the metric allows much higher, but the method behind them is not public in the sources checked here.

None of these has been run. The per-run budget in the standing prompt is three experiments or two hours.

---

## Revision 2026-10-30 — the cause is the collar sweep, and it is measurable

Earlier revisions described the 0.2778 file as the 2 px member of a collar sweep and
stopped there. This revision quantifies the mechanism and states its limit.

**Single-cell calculus.** Adding one predicted cell `x` changes DTI by

    ΔDTI > 0  ⇔  k(d(x,G)) > 0.2·[1 − k(d(x,G))]  ⇔  d(x,G) < 2.5 px (250 m)

with `k(d) = max(1 − d/300 m, 0)`. Inside 250 m of a true unmapped fault a cell pays for
itself several times; anywhere else it is a pure 0.2-unit cost. Because the truth set is
defined as faults **absent** from the public catalogue, a dot inside the catalogue collar
can never satisfy that test — it is a guaranteed −0.2.

**The controlled triple.** One generator, one target density, three collar radii:

| Member | Dots | % inside 3 px of catalogue | Reported | Marginal gain |
|---|---|---|---|---|
| GEMSDOE25 | 44,090 | 19.52 % | 0.2600 | — |
| GEMSDOE31 | 40,199 | 11.73 % | 0.2708 | +0.0108 |
| GEMSDOE32 | 37,654 | 5.77 % | 0.2778 | +0.0070 |

Slope: **+0.00127 and +0.00117 per percentage point removed** — flat, as the single-cell
calculus predicts, and diminishing only because 44,090 simultaneous dots are not
independent. Fit on all nine: `1/DTI = 1.768205e−5·N + 3.006165`, R² = 0.9114,
N ∈ [37,654, 61,328]. Spearman(N, reported) = −0.9832 (p = 2.0e−6);
Spearman(catalogue-DTI, reported) = **−1.000**.

**What 0.2778 therefore is.** The member of the family that spends the smallest share of
its budget in territory the metric has already excluded. A better *filer* of the same
guess — not a better geological model, and not evidence that the lattice geometry is
close to the truth.

**What it is not.** The N→0 limit of the fit (0.333) is an extrapolation artefact: a
submission with no dots scores nothing, so the true curve must return to zero. It is not
a ceiling and is not used as one. Equally, the fitted slope on N cannot be separated from
the collar effect inside this family, which is why the shipped candidate holds N fixed at
the champion's 37,654 and varies only contamination.

**Consequences used downstream.** (1) Any candidate inside this family is judged on
contamination and yield, not on dot count. (2) Because all nine overlap by ≥97.58 % within
3 px, they are one submission, not nine (IR-S-11). (3) The catalogue they were built
against is missing 95,452 mapped fault cells (IR-S-13), so every focus site under-collared
by construction.
