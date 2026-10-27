# Executive Summary — 9 Focus Sites, `0.2778` Champion Autopsy & `SASS2-XGHF` Validated Deliverable

**Date:** 2026-10-27 UTC · **Active Validated Candidate:** `GEMSDOESASS2-XGHF-e7996841` (`verdict = promote`)
**Evidence Classes:** `OWNER-REPORTED` (unverified prompt transcriptions; no organizer receipt on file), `HOLDOUT-DTI` (exact spatially-blocked local evaluator with version, withheld count, and 256-block bootstrap 95% CI; never a leaderboard score), `ORGANIZER-CONFIRMED` (none on file yet).

## 1. Answer First — Which File Should You Download?

| Candidate in `docs/downloads/` | Evidence-Labeled Holdout Metrics | Full-Registry Uniqueness (`429` rasters) | Automated Gate Status & Guidance |
|---|---|---|---|
| **[`gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif`](../docs/downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif)** (`SASS2-XGHF`, SHA-256 `2cdf5ded…`) | **`HOLDOUT-DTI = 0.131134 [0.118009, 0.142930]`** (`GEMSDOE32-HIDE-RECOVER-v3.0`, `n=22,232`; paired $\Delta = +0.032048 [+0.021652, +0.042293]$, **$p = 1.000$** vs `0.2778` Champ `0.099202`) · **`SGMC-cal = 0.066793 [0.060406, 0.072338]`** (`> 0.064121` Champ, $P=0.703$) | **PASS (`427/427` genuine `<= 69.11%`, `27.00%` vs `0.2778` Champ; `|Spearman| <= 0.0992`)**; `+0.08%` excess on `r13-lattice-s5` (`IR-SASS2-LATTICE-03`) | **🟢 OK TO DOWNLOAD · PROMOTED TO WEEKLY-SLOT SELECTOR** (`13/13` byte checks PASS, `59/59` canary PASS) |
| `gemsass2-ass2-altedge-hgb-44090-20261027-cc854482215e-zeros.tif` (`ASS2-ALEDGE`, SHA-256 `cc854482…`) | `HOLDOUT-DTI = 0.10886` (`v1`, `n=60,988`); paired SGMC 95% CI `[-0.0084, +0.0547]` crossed zero | Checked vs 9 focus champions (`39.13%`) | **🛑 ARCHIVED NEGATIVE — DO NOT SUBMIT** (`IR-SASS2-ALEDGE-02`) |
| `gemsdoesass2-thermo-tilt-conduit-37654-20261027T113705Z-d8f85365-zeros.tif` (`TTC-d8f85365`, SHA-256 `b8be5398…`) | Measured `HIDE-RECOVER-v3.0 = 0.005043` (`SGMC-cal = 0.084861`) | Hardcoded fake metrics & `np.random.randn` proxy in legacy script | **🛑 QUARANTINED — DO NOT SUBMIT** (`IR-SASS2-TTC-01`) |

See [`02_sass2_xghf_hypotheses_and_02778_autopsy.md`](02_sass2_xghf_hypotheses_and_02778_autopsy.md) for the complete 9-site audit, PhD-level `0.2778` metric derivation, 5 ranked hypotheses, and 8-item irregularity ledger.
