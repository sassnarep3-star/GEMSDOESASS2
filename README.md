# GEMSDOESASS2 — DOE GEMS Prize Challenge (DrivenData #306)

**Standing prompt (read at the start of every session).** Focus on the highest-scoring
submissions from GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31,
GEMSDOE32, GEMSDOE33, GEMSDOE36. Produce an executive summary per site making it obvious
which file is best, generate a **unique** TIF (never copy a previous submission except for
learning/education), validate it **without human intervention**, label every number
HOLDOUT-DTI (evaluator, n withheld, 95% CI) or ORGANIZER-CONFIRMED, never write a
projection as a score, run the leakage canary (single-feature AUC > 0.90 = leakage),
check surface + final-dot uniqueness (Spearman > 0.90 or > 70% dots within 3 px of a
registry raster = duplicate, stop), end with a JSON run card, stop after 3 experiments.
Fix the reported portal error *"Predicted values must be in range [0, 1]"* (every value
finite in [0,1]). Give every TIF a unique name + ≤140-char note. Beat 0.2778
(GEMSDOE32, USER-REPORTED) — leaderboard top cited inconsistently as 0.3195 / 0.4413 /
observed 0.4437 (IR-2); target only with a holdout-proven, non-duplicate lane.

**Core values.** Maximize P(Win) — every weekly slot is an experiment, not a lottery
ticket. Own the Outcome — own results end to end; failure is a signal, published as such.

## Current status (2026-10-27): ✅ DOWNLOAD YES · 🛑 SUBMIT NO
- Unique TIF: `docs/downloads/gemsass2-ass2-altedge-hgb-44090-20261027-cc854482215e-zeros.tif` (validator PASS, SHA-256 cc854482215e…)
- Verdict: **negative** — SGMC paired bootstrap CI vs champion crosses zero. Do not spend a slot.
- Full autopsy: `knowledge/EXECUTIVE_SUMMARY.md` · Site: `docs/index.html` (GitHub Pages: enable Pages → /docs)

## Our lane (single method paragraph)
Radiometric–magnetic alteration-edge HGB: gradient edges of GeoDAWN radiometric ratios
(ThK/UK/UTh) + K/Th/U/TC + TMI_up150 gradient, with USGS 3DEP LiDAR scarp bands, trained
only on visible catalogue faults (whole-component quadrant hide-and-recover); binary dots
emitted by descending score, ≥2.83 px separation, >2 px off catalogue, inside footprint.
Non-fault mimic: unfaulted lithologic/playa/caldera contacts. This lane, its hypotheses
ranking (#2 heat-flow/INGENIOUS next), data provenance (GEMSDOE24 public cache of USGS
GeoDAWN DOI 10.5066/P93LGLVQ + USGS 3DEP; competition data itself needs DrivenData login —
sandbox has no DrivenData auth, Dropbox/DrivenData hosts unreachable from here), and
limitations are documented in `knowledge/EXECUTIVE_SUMMARY.md`.

## Reproduce
```bash
pip install numpy rasterio scipy scikit-learn   # --break-system-packages if needed
python3 scripts/build_submission.py            # needs /tmp registry + GEMSDOE24 cache (see script header paths)
python3 scripts/check_uniqueness_sgmc.py
python3 scripts/bootstrap_ci.py
python3 scripts/validate_submission.py docs/downloads/gemsass2-ass2-altedge-hgb-44090-20261027-cc854482215e-zeros.tif <sample_submission.tif>
```
Known limitation: build script reads the feature cache from a sparse clone of
github.com/buffedlizard55-lab/GEMSDOE24 (/tmp/g24) and registry rasters in /tmp/registry —
pinning those into this repo (or a data manifest with hashes) is the top next task,
followed by hypothesis #2 (heat-flow) with a pre-registered blind-instrument gate.
