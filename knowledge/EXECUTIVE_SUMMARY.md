# Executive summary — decisions, evidence, and what is deliberately not claimed

Read `00_standing_prompt.md` first; it is the contract this file is written under. Every number below is
labelled **HOLDOUT-DTI** (this repo's evaluator, with 95% CI) or **ORGANIZER-CONFIRMED** (a submission-page
receipt — there are none in this environment) or **USER-REPORTED · UNVERIFIED**. A projection is never a score.

## 1. Files available for one-click download (updated 2026-10-30)

**Policy after PR #26 merged: every file below is `blocked-owner-ruling` — downloadable for research, NOT
submittable** — because the literal 70% lattice rule is arithmetically unsatisfiable for any footprint-wide
dot set (only 6,649 of 5,167,373 cells lie >3 px from the pinned lattice; IR-S-15/IR-S-16). Nothing in this
table should be read as "cleared for upload"; "verdict" below separates *format/uniqueness status* from the
*scientific* result, both of which must fail or pass independently.

| file (in `docs/downloads/`) | dots | local format check vs organizer-example mirror | uniqueness vs registry | scientific gate | verdict |
|---|---|---|---|---|---|
| `gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif` (+ `.zip`) | 22,163 | **all checks pass** (`strict_local_format_pass: true`, `docs/data/format-sparse-blind-zeros.json`) | max 3-px overlap 41.29%, max \|ρ\| 0.0083 → pass | **NOT RUN** (IR-S-24) | **PROMOTE on format + uniqueness only → now `blocked-owner-ruling` / NOT CLEARED** (99.74% of dots within 3 px of the pinned lattice, IR-S-15; holdout still owed, IR-S-26) |
| `…cc522684-nan.tif` (+ `.zip`) | 22,163 | fails only `whole_array_finite_in_0_1` — the check that is mutually exclusive with `outside_masked_or_nan` (IR-S-23) | identical dots | not run | GIS twin, byte-identical inside footprint; same lattice block |

| `gemsdoesass2-vrc-ventridge-44090-20261030T024740Z-nan.tif` (+ `.zip`) | 44,090 | fails only `whole_array_finite_in_0_1` | max per-raster overlap 39.99%, max \|ρ\| 0.0162 → pass | loses both instruments | **negative — research only** (`docs/data/vrc-run-card.json`; generator receipt `evidence/vrc_run_card.json`) |
| `…44090-…-zeros.tif` (+ `.zip`) | 44,090 | fails only `outside_masked_or_nan` | same | same | negative — research only |

Hashes for all eight artifacts: `docs/data/download-hashes.json`. **No weekly slot was used this session**
(protocol rule 6: promotion is a separate selector step, and nothing here earned it).

## 2. Score estimation: what can and cannot be said

* **No defensible point estimate of the organizer score exists for any file.** A geometry-only estimator
  fitted on the ledger (`scripts/fit_org_score_estimator.py`) failed leave-one-out, R² = **−0.379** on
  38 measured rows — dot geometry does not predict score at the resolution required. Publishing a number
  anyway would be the invention the standing prompt forbids.
* **Organizer-confirmed:** nothing (DrivenData `/data/` and the submission page are login-gated here).
* **USER-REPORTED · UNVERIFIED anchors** (`evidence/org_ledger_measured.json`, geometry measured locally):
  0.2778 @ 37,654 · 0.2750 @ 38,854 · 0.2710 @ 37,660/35,307 · 0.2708 @ 40,199 · 0.2632 @ 41,865 ·
  0.2600 @ 44,090 · 0.2477 @ 60,069 · 0.2449 @ 61,328; controls 0.0904 (lattice), 0.0512 (SGMC
  off-catalogue), 0.0041 (habitat mask).
* **HOLDOUT-DTI, public-catalogue instrument** (`GEMSDOE32-HIDE-RECOVER-v3.0`, whole fault segments
  withheld + buffer, catalogue features from visible faults only, pooled DTI α 0.2 / β 0.8, 300 m
  triangular kernel, 256-block bootstrap CI): hash-pinned focus parent 0.09674; VRC candidate 0.008629
  (Δ −0.087808, CI [−0.100347, −0.075792], p(Δ>0) = 0.000); uncollared learned surface 0.10471
  (Δ +0.00798, CI [−0.00794, +0.02247]).
* **HOLDOUT-DTI, off-catalogue instrument** (`GEMSDOE32-SGMC-CAL-v3.0`, truth = 62,703 SGMC fault pixels
  >300 m from the public catalogue): parent 0.09528; VRC 0.04438 (Δ −0.05119, CI [−0.0672, −0.0338]);
  amplitude-control 0.10684 (Δ +0.01002, CI [−0.0223, +0.0460] — the only emission not significantly behind
  the parent off catalogue, and it collapses on the public instrument).
* Public-leaderboard context (not a receipt): rank-1 0.4544 on the 2026-10-28 official public snapshot of
  the sibling competition; this competition's own recorded highs moved 0.4413 → 0.4437 on earlier days.
  Irreconcilable → IR-S-08; no ceiling claim is made.

## 3. Autopsy of the reported 0.2778 (GEMSDOE32, `h33-2-b2`)

1. The number is **user-reported**; no receipt exists here (`knowledge/04_gemsdoe32_0-2778_autopsy_verified.md`).
2. Its decisive property is the **B=2 collar**: because the DTI discount reaches −0.4 for false positives
   within 3 px of the catalogue, removing catalogue-adjacent dots is what moved the same lineage from
   0.2600 → 0.2778 (37,654 dots vs 44,090), not a better detector.
3. It **fails the repo's own 70% lattice gate** (99.91% of its dots within 3 px) — see IR-S-01 — so any
   rule that blocks our files would have blocked the reported best. This is an owner decision, not a measurement.
4. Coverage, not geometry, explains the sparse/dense gap: the parent covers 37.96% of pooled truth within
   3 px against 89% for the 206,895-dot r13 lattice; the internal proxy saturates near 0.35.

## 4. `[0,1]` rejection: measured, not guessed

* The rejected bytes and the portal response are not in this environment, so the failure cannot be diagnosed
  from the primary source; nothing here claims otherwise.
* Measured instead: **both** encodings of both shipped files have every stored value finite in [0,1]
  (`inside_min/inside_max` = 0.0/1.0, `inside_out_of_range_finite = 0`, `docs/data/format-*.json`), so a
  genuine range violation is not the cause of any currently shipped file.
* The leading (still **unverified**) explanation is encoding, not range: the organizer validator plausibly
  treats an absent nodata flag as "all pixels valid" and then rejects NaN — which is why the `-nan`
  variants must not be the primary ship recommendation even though the NaN encoding matches
  `example_submission.tif` exactly, and why `submission_writer.py` emits a `nodata=-9999.0` diagnostic
  variant (never the primary).
* Corollary, logged as IR-S-10: the local validator cannot be satisfied by any file (the finiteness and
  masked-NaN checks are mutually exclusive), so "0 validator failures" must be read as "the one check the
  chosen encoding contradicts".

## 5. Hypotheses and their status

Ranked shortlist with gate results: `../HYPOTHESES.md` (repo root). This session's new work: **VRC (vent-ridge
continuation)** — negative on both instruments, root-caused to IR-VRC-01, written up in
`09_vrc_and_download_surface.md`. The mechanism split (learned surface wins only where catalogue
continuation is rewarded; amplitude wins only off catalogue) is the most informative negative result of the
session and defines the next experiment: score both instruments on the published champions whose organizer
scores are known, and keep the instrument whose ordering matches.

## 6. Uniqueness of our own outputs

Nine-site table: every focus-site variant shares ≥97.58% of dots within 3 px with another focus site — none
unique (README table, `docs/data/uniqueness-summary.json`). Against the 40 scanned registry rasters our VRC
file reaches 39.99% (limit 70%) and \|ρ\| 0.0162 (limit 0.90); 0.3227 of the previous sparse-blind dots lie
within 3 px of it, so it is not a superset of our own earlier file. Full 42-site clone scan was attempted
and did not complete at 2 cores (904 TIFFs); the scan is capped and recorded in
`evidence/registry_overlap_vrc.json` (`n_rasters_scanned: 40`) — treat it as a sample, not the complete
registry (IR-S-01's own caveat applies to us too).
