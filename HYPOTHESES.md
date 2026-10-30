# Geological hypotheses — current status

The current ranked XGHF-family proposals, their physical signatures, non-fault mimics, differences from the
local implementation, data-access status and preregistered tests are in
[research/2026-10-28-hypotheses-and-review.md](research/2026-10-28-hypotheses-and-review.md).

## Session 2026-10-30 — what was tested, and the outcome

| id | hypothesis | mechanism | named non-fault mimic | instrument result | status |
|---|---|---|---|---|---|
| **VRC** | vent-ridge continuation: scarps that *continue* a mapped vent trend carry blind fault trace | fold-aware logistic scarp detector (8 folds, whole segments withheld, catalogue features from visible faults only) → B=2 collar → 3-px vent-ridge thinning, 44,090 dots | road cut · terrace riser · palaeo-shoreline · mining step · landslide head scarp | **HOLDOUT-DTI 0.008629** vs pinned parent 0.09674 (Δ −0.08781, CI [−0.10035, −0.07579]); off-catalogue SGMC 0.04438 vs 0.09528 (Δ −0.05119) | **NEGATIVE** — `evidence/vrc_run_card_final.json` |
| VRC-control | scarp amplitude only, no learning (isolates whether the detector matters) | same emission pipeline, amplitude surface | same | off-catalogue SGMC **0.10684** (Δ +0.01002, CI [−0.0223, +0.0460]) — only emission not significantly behind the parent off catalogue; public instrument 0.00209 | informative negative; seeds the next experiment |
| VRC-ablation | spacing thinning vs plain top-k, budgets 37,654 / 44,090 | same surface, different selection rule | — | thin ≈ topk everywhere once IR-VRC-01 is fixed | thinning carries **no** skill; the earlier apparent gain was the bug |
| prior lane | sparse-blind conduit (22,163 dots, B=2, sep 3) | off-catalogue conduit dots from the thermal/vent stack | spring-and-seep artefacts, geothermal lease grading, steam plumes | format + uniqueness pass; **holdout never run** (IR-S-12) | still the only download this repo endorses, with that caveat attached |

**Prior HVFD `promote` recommendation stays withdrawn:** the saved TIFF fails the literal registered-lattice
overlap rule (see `docs/data/lattice_saturation_check.json` — the rule is arithmetically unsatisfiable for a
full-footprint raster, IR-S-01). Previous claims of numerical DTI gains, live-score ceilings and
guaranteed superiority were not independently established; earlier text remains in Git history.
See [IRREGULARITIES.md](IRREGULARITIES.md) and [the current run card](docs/data/run-card.json).

## Ranked shortlist for the next session (3 slots, none spent yet)

1. **Instrument reconciliation (highest information per minute).** Score both holdout instruments on the
   published focus-site champions, whose organizer values are known (0.2449–0.2778), and keep the instrument
   whose *ordering* matches the ledger. If neither matches, every promotion decision this repo has made is
   being driven by a mis-specified gate — including the negative verdict on VRC. Offline measurement, no slot.
2. **Run the missing holdout for the endorsed sparse-blind file** (`scripts/evaluate_holdout.py`, same
   fold definition). This closes IR-S-12 and turns a format-only PROMOTE into a defensible one — or withdraws it.
3. **Collar-aware amplitude emission at the 37,654 budget** (the one configuration whose off-catalogue CI does
   not exclude the parent). Preregistered promotion condition before running: off-catalogue SGMC pooled DTI
   > 0.1150 with paired CI excluding 0 against the pinned parent **and** public-instrument DTI > 0.0700.
   If the second condition fails, the variant is another negative result and no slot is requested.

Deferred: **HYDRO-COLLAPSE** (thermal-anomaly–spring geometric pairing; leakage-safe only if `dist_known_fault_px`
is never read — IR-08 (GDR `dist_known_fault_px` is label-derived)) and **THERMAL-TILT** (now measured as the `amp` control above, which is its
honest downgrade). Blocked: MAG-DEEP (no magnetic raster in the pinned mirror), STRAIN-RATE (needs InSAR time
series not present), SEGMENT-TIP (needs a verified segment polygon source; the SGMC polylines available here are
already the off-catalogue truth, so using them as a feature is circular).
