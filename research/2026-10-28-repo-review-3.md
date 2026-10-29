# Repo review — 2026-10-28 (branch `arena/99eabcc5-gemsdoesass2`)

Scope: verify the repository's current claims line by line against the checked-in artifacts, the pinned owner-mirror sources, and the official leaderboard. No new raster was generated and no weekly slot was used.

## Decision (unchanged)

**DO NOT SUBMIT any GeoTIFF in this repository.** The lattice-overlap gate still fails for both candidate families, and the owner ruling on the lattice probe (see below) has not been given. Format checks are not an approval.

## What was verified in this session

| # | Check | Command / source | Result |
|---|---|---|---|
| 1 | Python test suite | `.venv/bin/python -m pytest -q` (after `pip install -r requirements-audit.txt`) | **111 passed**, 27 Rasterio deprecation warnings only |
| 2 | Site behavior tests | `npm ci && npm run test:site` | **PASS** (`ok`, `changed`, `limited`, `missing`) |
| 3 | Sample template SHA-256 | `GEMSDOE24` @ `07345ea0604953d7efb858d9cfbc21e20c7aca0b` via `codeload.github.com` | `2176d08e…35cbc` — **matches pin** in `research/priority_sources.json` |
| 4 | Labels SHA-256 | same commit, `data/bridge/labels.tif` | `7ba308cc…4093` — **matches pin** |
| 5 | Lattice SHA-256 | same commit, `inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` | `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2` — **matches pin**; this is the raster the overlap gate depends on |
| 6 | Local sample format | `data/bridge/sample_submission.tif` | EPSG:32611, shape 3730×3292, 100 m pixels, values {0, 1, NaN}; 7,111,787 NaN cells |
| 7 | Saved-byte GeoTIFF format of all 8 files in `docs/downloads/` | rasterio read | CRS, shape and transform match the sample for every file; all finite values lie in [0,1]; no inf |
| 8 | NaN outside footprint | same | `*-nan.tif` variants carry 7,111,787 NaN cells outside the footprint (same count as the sample); `*-zeros.tif` variants carry none |
| 9 | Validator on the SASS2-XGHF zeros file | `scripts/validate_tif.py … --sample …` | strict local format pass; `ok_to_submit: false`, `organizer_accepted: null` |
| 10 | Official leaderboard, rank #1 | [drivendata leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) (fetched 2026-10-28) | **0.4544** (xiaofanhu, 33 submissions); #2 0.3916; this is a public observation, not an organizer receipt for any file here |
| 11 | CI on `main` | `gh run list` | latest runs on `main` (merge of PR #17) succeeded |

### Lattice-bound arithmetic (re-derived)

- Footprint cells outside the lattice halo: 6,649 (from `docs/data/audit.json`, not re-derived here because the 19-band cache is ignored).
- For n = 37,654 dots: minimum overlapping dots ≥ n − 6,649 = **31,005**, fraction = 31,005 / 37,654 = **82.34%**. This matches `docs/data/run-card.json`.
- Largest file that could pass the 70% rule by arithmetic: 6,649 / (1 − 0.70) ≈ 22,163 dots; the run card records the first failing count as 22,164.

## Irregularities found in this review

| ID | Finding | Disposition |
|---|---|---|
| IR-RV3-01 | `README.md` and `IRREGULARITIES.md` label the review addenda with branch `arena/6c861f74-gemsdoesass2`, which is already merged (PR #17). Readers may take it as the active branch. | Relabelled as historical in this commit. |
| IR-RV3-02 | Open PR **#15** (`arena/a3ca86a7-gemsdoesass2`, "Harden GEMS submission safety and audit handoff") was opened from another session and remains OPEN. Its merge state is `UNKNOWN`. | **Not touched.** It belongs to a different branch. Owner should decide whether it is superseded by this review. |
| IR-RV3-03 | The leaderboard top score is **0.4544** on the live page, while the user's brief cites 0.4413 and 0.3195 as the "current" high. These are different dated snapshots. | Recorded; the live page is the official reference. Not a score for any submission here. |
| IR-RV3-04 | The user's rejected upload ("Predicted values must be in range [0, 1]") is still unexplained. The repository holds no rejected bytes, and the `*-nan.tif` variants contain NaN outside the footprint, which is the same pattern as the official sample. | Not diagnosed; see IR-09. An owner must supply the rejected file or the portal's response text to test the hypothesis. |
| IR-RV3-05 | `docs/downloads/*.tif` all pass the local [0,1] check, so the range error is not reproducible from the repository's files alone. | Recorded. |

## Owner ruling required (single blocker)

The `r13-lattice-s5` lattice (pinned above, verified in this session) is treated as a registry raster. Under the stated 70% rule, any full-size (37,654-dot) candidate must overlap it by at least 82.34%, so no full-size candidate can pass the literal rule. Options:

1. Rule that the lattice is excluded from the registry for the overlap gate, and rerun the gate against the remaining registry rasters.
2. Keep the literal rule, and accept only a file of at most ~22,163 dots placed in the lattice holes (not scientifically meaningful per the prior review).
3. Keep the current stop: no new submission this cycle.

## Next steps (ordered)

1. Owner ruling on the lattice probe (above).
2. Obtain the complete current registry: the set of all GEMSDOE site rasters at their pinned commits, with hashes, so the 3-px and rank-correlation gates can be computed against all of them and not only against the lattice.
3. Recheck GEMSDOE32 shared-evaluator defects (IR-04, upstream issues 41 and 42) before any holdout DTI is reported.
4. Run the hypothesis list only after 1–2 are done, within the 3-experiment / 2-hour budget.
