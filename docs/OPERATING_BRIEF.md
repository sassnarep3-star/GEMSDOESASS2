# Canonical Operating Brief — Read Before Every GEMS Session

> This is the deduplicated, implementation-safe version of the project request. It
> preserves the governing requirements and deliberately does **not** convert
> owner-reported scores, a local proxy holdout, or a format check into an
> organizer-confirmed score.

## Goal

Build an auditable system for the DrivenData **GEMS Prize Challenge** that:

1. researches scientifically defensible ways to detect previously uncatalogued
   geothermal-fault targets;
2. creates a single-band GeoTIFF that matches the supplied submission template;
3. validates it without a human-inspection fallback;
4. makes the download/submission decision unambiguous; and
5. never copies or renames an older submission as a purportedly new result.

The project aims to maximize the probability of a legitimate high leaderboard
result, not merely generate a file that uploads.

## Non-negotiable submission protocol

1. **One lane at a time.** Before dot placement, compare the candidate surface
   with every pinned registry raster. After placement, compare final dots. Stop
   as a duplicate if `abs(rank correlation) > 0.90` or more than `70%` of the
   candidate dots fall within 3 pixels of any registry raster's dots.
2. **Reuse shared mechanisms.** Use the cached feature stack when it exists;
   evaluate with a hide-and-recover whole-segment spatial holdout; derive any
   catalogue feature from visible faults only; and mask visible faults
   pixel-exactly. The local DTI protocol is pooled `alpha=0.2`, `beta=0.8`,
   300 m triangular kernel.
3. **Label every number.** A number is either **HOLDOUT-DTI** (evaluator
   version, withheld positive count, and 95% CI included) or
   **ORGANIZER-CONFIRMED** (copied from a submission-page receipt). A forecast
   is never called a score.
4. **Leakage canary.** Evaluate every raw/transformed feature alone. A holdout
   AUC above `0.90` is leakage until independently disproven.
5. **Run card.** Each experiment ends with: hypothesis; mechanism; named
   non-fault mimic; HOLDOUT-DTI + CI; registry correlation/overlap; raster
   SHA-256; validator output; name/note; and `promote` or `negative` verdict.
6. **Budget.** Stop after at most 3 experiments or 2 hours. Selecting a real
   weekly submission slot is a separate action and must obey the competition
   cap.
7. **Fail closed.** A format-valid TIFF is not submission-authorized unless all
   scientific, provenance, novelty, and slot-selector gates pass. No manual
   reviewer may override an automated failed gate by rebranding the artifact.

## Focus sites and historical claims to audit

The focused peer sites are **GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28,
GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36**. Their historical
claimed leaders are preserved in `registry/focus_registry.json` with immutable
GitHub commit, Git blob, and SHA-256 pins. These values are **OWNER-REPORTED**
unless a primary submission-page receipt is stored.

The prominent historical claim is GEMSDOE32 `h33-h33-2-b2-…-zeros` at `0.2778`.
The project must explain its observed raster relationship without claiming a
hidden-label causal mechanism or a live leaderboard forecast.

## Required project outputs

- A clean static GitHub Pages site with a prominent status card and an executive
  summary/submission guide.
- A table covering all nine focus sites: historical file, claimed score
  provenance, exact/lane-duplicate finding, and a clear download/submit
  decision.
- A research knowledge base with official-source links, access status, and
  explicit irregularities.
- Reproducible scripts for data preparation, feature construction, holdout
  evaluation, peer-registry checks, strict GeoTIFF writing, and validation.
- No automatic DrivenData upload. A user may upload only a file that the
  independent release selector explicitly marks `OK_TO_SUBMIT`.

## Input and format constraints

- DrivenData competition data may require authenticated download. It is never
  silently fetched with unverified URLs.
- A portal-safe submission is a single-band, aligned GeoTIFF with all values
  finite and within `[0,1]`; this conservative policy addresses the observed
  portal error: **“Predicted values must be in range [0, 1]”.**
- The file must match the template CRS, shape, and geotransform. The current
  pinned template grid is EPSG:32611 at 100 m only when verified from a local
  template; that fact must not be hard-coded as a substitute for validation.
- External sources must be free/public and official where used for a promoted
  result. A peer mirror is reproducibility evidence only, not official data
  authentication.

## Research discipline

Before implementation, rank 3–5 distinct geological hypotheses by expected DTI
benefit and implementation cost. Each must identify layers, physical signature,
why it could find an uncatalogued fault, difference from prior work, source
availability, and a non-fault confound. Do not spend a weekly slot before the
best locally validated hypothesis beats the current comparable holdout control.

## Core values

- **Maximize P(Win):** make evidence-based tradeoffs that maximize the chance of
  a legitimate successful outcome.
- **Own the Outcome:** act end-to-end, preserve negative results, repair shared
  tooling once, and state blockers plainly instead of passing them to a human
  inspector.

## Current hard stop

The checked-in CDCC-01 GeoTIFF is intentionally named
`RESEARCH-DO-NOT-SUBMIT`. It is format-valid and unique only against the nine
pinned historical artifacts, but its paired holdout confidence interval crosses
zero and its inputs are an untrusted peer mirror with a template/label identity
anomaly. It is therefore **not** an approved competition submission.
