# Executive summary — current decision (2026-10-30, post-merge)

**SUBMIT THE STRAIN-RIDGE FILE** — [`gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif`](../docs/downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif),
SHA-256 `6d00f58a35005a253e352e21c8adde0e108aa0abb4b810db9797af89d94dd615`, name
`GEMSDOESASS2-STRAINRIDGE-OFFCAT-37654D`. Format 11/11 · genuine-peer uniqueness 36.45% /
|ρ| 0.0115 (full corpus: worst genuine peer 25.8%) · HOLDOUT-DTI 0.2244 vs 0.0715 lattice
control (3.14×, P=0.958, with the mapped-truth caveat) · **MODEL ESTIMATE 0.29**
(controlled 0.2853, risk 0.25–0.33 — *not* an organizer score).

**One internal gate fails, openly:** the literal lattice clause (99.37% within 3 px of the r13
calibration probe; a seeded random placement scores 99.91%). The clause is non-discriminating
for interior placements — only border-hugging rasters can pass it (IR-30-12) — and the owner
must rule on it. No organizer receipt exists; no weekly slot has been spent.

Everything else is **research only**: the sparse-blind candidate (`cc522684`) is withdrawn
(`verdict: negative` — 98.41% genuine-peer overlap in the full corpus), and the VRC
vent-ridge artifact is a measured negative result. Historical site scores remain
**USER-REPORTED / UNVERIFIED**.

See the [dashboard](../docs/index.html), [executive summary](../docs/executive-summary.html),
[why 0.2778 scored](../docs/method.html), the [run card](../evidence/strain_ridge_run_card.json)
and the [full-corpus receipt](../evidence/focus_uniqueness_full_registry_20261030.json).

---

# Update — 2026-10-31 (session C): S3 ring-habitat emission replaces strain-ridge as the recommended file

**Recommendation changes to** `docs/downloads/gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif`
(sha256 `b84a4f2642500b9817b946d99db14471f4b935d110b794d2736f643d56f8f7ae`), submit name
`GEMSDOESASS2-S3-RING-BINARY-37654`. The strain-ridge file of 2026-10-30 remains valid and
unique; prefer the new file because its placement prior is **measured** better than uniform
on both holdout instruments at the champion's budget.

What changed, all in `evidence/s3_run_card_20261031.json`:

* Five new hypotheses were ranked **before** implementation
  (`research/2026-10-31-hypotheses-s3.md`); the top-ranked ring-habitat prior was
  validated on the spatially-blocked hide-and-recover holdout before any slot decision.
* EXP-1 falsified the register's former rank-1 lead (thermal/well-spring temperature
  anomaly ranking loses to uniform on both instruments). The thermal share axis was also
  shown to collapse to a rank axis (greedy sampling is rank-equivalent).
* EXP-2 chose the placement: ring-binary-37654 (IHR 0.0597 [0.0537–0.0649] vs uniform
  0.0439 [0.0394–0.0481]; SGMC-off 0.0770 [0.0715–0.0827] vs 0.0750). N = 24,000 is
  negative on both instruments. Soft plateau emission is a split verdict (SGMC +20 %,
  IHR −48 %) and stays untested for the leaderboard.
* EXP-3 wrote the submission pair (13/13 strict checks; all 12,279,160 cells finite
  float32 in [0,1]; `nodata=None`) — this is the standing fix for the portal error
  "Predicted values must be in range [0, 1]".
* Uniqueness: worst genuine-peer overlap **23.0 %**, max |ρ| **0.0086** over 24
  references including all nine focus champions. The literal 70 % clause fails only
  against the known non-discriminating r13 space-filling probe (IR-S3-6; owner ruling
  pending).
* Score estimate unchanged in kind: **MODEL ESTIMATE 0.29** (controlled anchor 0.2853,
  risk band 0.25–0.33). The ring edge over uniform is NOT converted into score — the
  holdout instruments mis-transfer to the leaderboard in opposite directions (run card
  §holdout), and the leaderboard remains unmeasured for this portfolio.

No weekly submission slot was spent. Promotion remains the owner's selector step.
