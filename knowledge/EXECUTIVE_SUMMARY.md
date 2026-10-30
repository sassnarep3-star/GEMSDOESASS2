# Executive summary — current decision (2026-10-30)

**NOT CLEARED FOR SUBMISSION. No file in this project is approved.** The strongest unique
candidate (`gemsdoesass2-sparse-blind-conduit-22163-…-cc522684-zeros.tif`) passes the shared
format validator and the peer-uniqueness gates but **fails the literal lane duplicate rule**:
99.7428% (22,106 / 22,163) of its dots lie within 3 px of the pinned 13GEMSDOE lattice
(limit 70%). The earlier "OK TO DOWNLOAD AND SUBMIT" claims are withdrawn
([IR-30-01](../IRREGULARITIES.md)); the corrected run card records `verdict: negative`.

Historical site scores are **USER-REPORTED / UNVERIFIED** — no receipt ties any score to any
pinned raster. No calibrated leaderboard estimate exists for any file, and none is projected.

| File | Role | Format (shared validator) | Uniqueness | Estimate | Verdict |
|---|---|---|---|---|---|
| `…cc522684-zeros.tif` | best local candidate | PASS 11/11 | focus scope 41.29% PASS · full corpus 98.41% FAIL · lattice 99.74% FAIL | Unavailable | **negative — held** |
| nine focus-site variants | research only | mixed | >97% peer overlap | Unavailable | duplicates |

What would clear the candidate: an owner ruling on the lattice rule (the only footprint cells
that could satisfy it are 6,649 border cells — no interior placement can pass as written; see
[recheck receipt](../evidence/lattice_gate_recheck_20261030.json)), plus a HOLDOUT-DTI on a
buffered spatial holdout, which requires organizer labels this environment does not have.

See the [dashboard](../docs/index.html), the [submission guide](../docs/executive-summary.html),
the [corrected run card](../evidence/unique_run_card_cc522684.json) and the
[ranked hypotheses](../research/2026-10-30-hypotheses-ranked.md).
