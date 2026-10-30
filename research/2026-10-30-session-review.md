# Session review — 2026-10-30 (branch `arena/d5ff2b98-gemsdoesass2`)

## What changed

The previous session's headline ("UNIQUE SUBMISSION READY — OK TO DOWNLOAD AND SUBMIT") did not
survive re-measurement. Applying the parallel-run protocol's literal lane rule to the saved
bytes shows the sparse-blind candidate is a lattice duplicate:

| Measurement | Value | Receipt |
|---|---|---|
| Candidate dots within 3 px of the pinned 13GEMSDOE lattice | 22,106 / 22,163 = **99.7428%** (limit 70%) | `evidence/lattice_gate_recheck_20261030.json` |
| Footprint cells farther than 3 px from the lattice | 6,649 of 5,167,373 — **all within 2.24 px of the study-area border** | same |
| Max overlap vs focus-site rasters (18-raster scope) | 41.29% (XGHF nan twin) · max \|Spearman\| 0.0134 — peer gate PASS in this scope | `evidence/focus_uniqueness_20261030.json` |
| Max overlap vs the full public corpus (2,282 rasters) | **98.41%** vs GEMSDOE86 `gems86-gmc-linepost-90568d` — peer gate FAIL; 103 space-filling rasters excluded by measured density; own nan twin excluded as self | `evidence/focus_uniqueness_full_registry_20261030.json` |
| Shared format validator, zeros twin | PASS 11/11 (`scripts/validate_tif.py`) | `docs/downloads/…-cc522684-audit.json` |
| Generator-internal 13-check list | 13/13 (labelled as internal) | same |

Verdict corrected to `negative`; every page now says **NOT CLEARED FOR SUBMISSION**. The earlier
"pass" came from `focus_uniqueness_check.py`'s name-based probe exemption, not the literal rule
(IR-30-01/02). The run card's arithmetic-bound justification was a non-sequitur: the bound
proves only that counts ≥ 22,164 must fail.

## Verified line by line (saved bytes, official sources)

- Nine pinned focus-site rasters re-fetched from GitHub at their pinned commits; all SHA-256
  values match `docs/data/audit.json` (`scripts/fetch_pinned_registry.py`).
- Lineage: GEMSDOE32 (0.2778, 37,654 dots) is an exact-pixel subset of GEMSDOE25 (44,090); the
  6,436 removed dots are exactly the parent's dots within 2 px of the USGS catalogue. GEMSDOE25
  and GEMSDOE30 have identical dot sets. All nine fail the literal lattice rule at ~99.9%
  (`evidence/focus_pairwise_matrix_20261030.json`).
- Official spec re-read at source: float32, one band, [0,1], EPSG:32611, 100 m, NaN/null allowed
  outside bounds; the official notebook (`aebe92f`) writes float64 with no NaN (IR-S-07 persists).
- `data/bridge/sample_submission.tif` is not "total fault absence": its positives equal
  `labels.tif` exactly (60,988 cells) — flagged IR-30-06.
- The 19-band feature cache contains no radiometric channel; `REVIEW_NOTES.md`'s claim that
  radiometrics were already used is unsupported (IR-30-07). H1 (GeoDAWN Th/K alteration) is
  therefore novel relative to this repo, and the official USGS release
  (DOI 10.5066/P93LGLVQ) covers 99.94% of footprint cell centres by bounding box.
- Full registry: 113 public GEMS-named repos listed, 112 fetched at default-branch HEAD
  (`scripts/fetch_gems_registry_full.py`, list in `research/gems_site_repos.txt`), 3,569 TIFs,
  one repo with broken symlinks under `data/` (8 real TIFs recovered; IR-30-08). The uniqueness
  gate runs over it with two template fixes: corrupt-TIFF resilience (IR-30-05) and probe/self
  classification by measured density and content identity (IR-30-10). Result: the candidate is
  not unique in the full corpus — GEMSDOE86's gmc-linepost-90568d covers 98.41% of its dots.

## Corrections to shared tools (fixed once, in the template)

1. `scripts/focus_uniqueness_check.py`: unreadable/corrupt registry rasters are recorded in
   `registry_unreadable` and skipped instead of crashing the gate.
2. New `scripts/fetch_pinned_registry.py` (SHA-pinned, blobless fetch + verification),
   `scripts/fetch_gems_registry_full.py` (explicit repo list, literal pathspecs),
   `scripts/focus_pairwise_matrix.py` (pairwise 3 px matrix + exact-pixel subset relations),
   `scripts/lattice_gate_recheck.py` (literal rule, border-cell analysis).

## Decision state

- **No file is approved.** Promotion to a weekly slot is a separate selector step and no slot
  was used; this environment cannot reach the DrivenData submission form anyway.
- An **owner ruling** is required on the literal lattice rule: as written, only border-placed
  rasters can pass, which blocks geology rather than duplication (four options listed on the
  executive-summary page).
- Ranked hypotheses H1–H5 (radiometric alteration; DTI-optimal soft emission; 1 m lidar
  micro-scarps; earthquake×conductivity upflow concordance; Holocene vent proximity) are
  written in `research/2026-10-30-hypotheses-ranked.md`, **all UNTESTED**, each with an official
  data source. None may reach a submission slot before a buffered spatial holdout.

## What the next session must do

1. Obtain the owner ruling on the lattice rule (or redefine "dots" for probability maps).
2. Obtain organizer data (login-gated) or build the fold-local comparator to produce any
   HOLDOUT-DTI; until then no score estimate may be published.
3. Test H2 (soft emission) first — it needs no new data and the official metric rewards it;
   then H1 (GeoDAWN radiometrics), whose coverage must be verified against the survey polygons.
4. Keep the weekly-slot selector step separate; three submissions per week per entity (rules
   §3.2) is the hard cap.
