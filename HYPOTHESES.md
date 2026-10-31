# Geological hypotheses — current status (2026-10-30)

The live hypothesis register — what was tried, what was measured, and what is still open — is
**README §5** ("Hypothesis register"). Supporting files:

- [research/2026-10-30-hypotheses-ranked.md](research/2026-10-30-hypotheses-ranked.md) — ranked
  mechanisms, physical signatures, non-fault mimics and official data sources, with a
  post-merge reconciliation against the tested register.
- [research/2026-10-28-hypotheses-and-review.md](research/2026-10-28-hypotheses-and-review.md) —
  earlier XGHF-family proposals (historical).
- [research/2026-10-31-new-hypotheses.md](research/2026-10-31-new-hypotheses.md) — five
  NEW candidates not yet tried in this repo, ranked by expected DTI improvement and
  implementation cost; H_STEPOVER (catalogue segment tip step-over / relay-ramp dilation)
  is selected for holdout validation and submission generation in this session.

**Current state:** H1 (STRAIN-RIDGE off-catalogue blind faults) is implemented and promoted —
see the [decision table](README.md). H2 (magnetic tilt) and H3 (radiometric Th/K point values)
are measured **negative**. H4 (2 m probe temperature residual kriging) is untried but public
and unused. H_STEPOVER is the new top candidate: labels.tif-only, no external download, and
its dot budget (≤ 22,163) passes the literal 70 %-within-3-px lane rule arithmetically.
Negative results are deliverables; every number is labelled HOLDOUT-DTI or MODEL ESTIMATE,
never an organizer score. See [IRREGULARITIES.md](IRREGULARITIES.md) for the full
corrections ledger.
