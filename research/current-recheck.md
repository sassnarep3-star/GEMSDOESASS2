> **Subsequent update (2026-10-28):** This is an earlier parallel review. A 19-band cache was later restored from a hash-pinned owner mirror, not authenticated organizer data. The separate comparator, full registry and both shared-tool blockers remain unresolved. See [the latest review](2026-10-28-review.md).

# Current independent recheck — 2026-10-28

**Decision: no candidate approved; no new geological experiment or competition submission was run.** The prompt does not identify the promised single method paragraph. The prepared cached stack and complete, current registry are absent, and the shared template's documented holdout defects remain unresolved ([issue 41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41), [issue 42](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/42)). Running a new lane or claiming a clean holdout under those circumstances would violate the protocol.

## Pass 1: saved-byte check

Using the pinned [lattice mirror](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea0604953d7efb858d9cfbc21e20c7aca0b/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif), the owner-mirror sample footprint and Euclidean radius of 3 pixels, the independently reproducible [receipt](../evidence/lattice_recheck_20261028.json) reports:

| Historical artifact | Within radius / total | Literal gate |
|---|---:|---|
| HVFD | 37,617 / 37,654 (99.9017%) | Fail |
| XGHF | 37,636 / 37,654 (99.9522%) | Fail |

Reproduce with `python scripts/audit_current_lattice.py` after installing `requirements-audit.txt`; it retrieves and hash-checks the pinned witness using `gh`. A single failing witness is enough to stop, not evidence of complete registry coverage. Both rasters remain available for research; neither is authorized for submission. The earlier XGHF card claimed 99.78% for this witness; its number is not reproduced by this check. The HVFD card's former promote verdict omitted the lattice and is withdrawn. Historical holdout/canary estimates are parallel-branch claims, not independently rerun here and not leaderboard projections.

The HVFD local format inspector passed with an owner-mirror reference: all stored values finite in [0,1], no masked or invalid interior values, matching shape, CRS and transform. This cannot prove organizer acceptance, novelty, or the cause of the reported range error. An authenticated sample remains necessary to establish authoritative geometry. The scientific and scoring explanation for the historical 0.2778 is uncertain; sparse, spaced, off-catalogue dots are a plausible metric-related mechanism, not proof of why that score occurred or a basis to claim a higher future score. The figure itself is user-reported, not a receipt.

## Pass 2: failure paths

The top-level pages now prominently override conflicting historical promotion text and the HVFD run card is negative. Added the missing `scikit-image` dependency, required by `features.py`. A TIF format pass alone never authorizes a slot. Retained older content and files as archival evidence rather than implying the original experiments have been independently replicated.

## Pass 3: unresolved work

1. Restore authenticated data and establish the full registry's scope; the current environment has network access restricted to selected package and GitHub hosts, not the organizer data portal.
2. Resolve the missing lane assignment and literal lattice rule. Do not silently exempt a registry member. Fix the shared evaluator upstream, not in a private fork, then freeze comparable fold-local data and a holdout incumbent.
3. Design candidate hypotheses against the actual assigned lane, run per-feature canaries, measure pre-placement surface and final-dot novelty against the whole registry, and run up to three experiments on the shared evaluator and writer. Compare using paired uncertainty, not a projected live score.
4. A separate selector, informed by the actual account's available quota, must decide whether an eligible artifact can occupy a submission slot. No update was made to the other nine repositories; their pages are independent projects.

Official references: [competition](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Access to non-GitHub links was not independently checked in this session.
