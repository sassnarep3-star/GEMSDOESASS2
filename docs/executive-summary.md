# Executive summary (2026-10-30)

**Status: download ready, submission BLOCKED.** Do not submit yet.

- Downloadable file: `gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif` (SHA-256 `65e3a775ad8b3fd3f3c55a501c84d48d05554219065cad69fa9ebfb54d572661`). Format-valid, and unique by every measured gate except one.
- Blocking gate: 99.74% of its dots lie within 3 px of the 13GEMSDOE registry lattice (protocol limit 70%). The lattice rule is saturated for interior geology, so the owner must rule (see `index.html` options A/B/C).
- Estimated score: NOT ESTIMABLE. No organizer receipt and no runnable holdout (`scripts/evaluate_holdout.py` is a fail-closed stub).
- Nine focus sites: all pinned files verified; each duplicates another site's file by 97.6–100% of dots; reported scores are USER-REPORTED. The highest reported is GEMSDOE32 at 0.2778, which is GEMSDOE25 minus 6,436 near-catalogue dots.

Full detail: [front page](index.html) · [how to submit](executive-summary.html) · [research and hypotheses](../research/2026-10-30-review.md) · [irregularities IR-S-15 to IR-S-24](../IRREGULARITIES.md).

## Added later on 2026-10-30 (second pass, PR #27) — negative result + download surface

- **VRC (vent-ridge continuation) — NEGATIVE, research only.** Emitted at 44,090 dots through the shared
  stack. HOLDOUT-DTI 0.0086294568 vs the hash-pinned focus-lineage parent 0.09674 (Δ −0.087807630, 95% CI
  [−0.1003465, −0.0757916], p(Δ>0) = 0.0); off-catalogue SGMC 0.04438 vs 0.09528 (Δ −0.05119, CI [−0.0672,
  −0.0338]). Format and per-raster uniqueness pass (max 3-px overlap 39.99% of 40 scanned registry rasters,
  limit 70%; max |Spearman| 0.0162, limit 0.90), and it fails the lattice rule at 1.000 like every other
  interior raster — so it is neither promoted nor submittable. Card:
  [`data/vrc-run-card.json`](data/vrc-run-card.json); write-up:
  [`../knowledge/09_vrc_and_download_surface.md`](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/knowledge/09_vrc_and_download_surface.md).
- **Emitter bug fixed** (`IR-VRC-01`, alias of IR-S-25): a `np.lexsort` position was used as a pixel index, so
  the first VRC pass emitted 12,572 invalid-fill dots and wrote 15,300 against a 22,163 budget. Both call sites
  now remap through the candidate array and a hard guard refuses any emission whose count ≠ budget or whose dots
  leave the allowed footprint. The defective raster was deleted, not patched.
- **Download surface:** `.zip` for both encodings of both files, manifest
  [`data/download-hashes.json`](data/download-hashes.json), per-check receipts
  [`data/format-sparse-blind-zeros.json`](data/format-sparse-blind-zeros.json) (all checks true,
  `strict_local_format_pass: true` against the organizer-example mirror),
  [`data/format-sparse-blind-nan.json`](data/format-sparse-blind-nan.json),
  [`data/format-vrc-zeros.json`](data/format-vrc-zeros.json),
  [`data/format-vrc-nan.json`](data/format-vrc-nan.json).
- **Score estimate: NOT ESTIMABLE** stays true, now for two independent measured reasons — the geometry-only
  estimator fails leave-one-out (R² = −0.379) and no organizer receipt exists in this environment. The
  available labels are HOLDOUT-DTI (from `src/gems_sass2/holdout.py`) and USER-REPORTED · UNVERIFIED anchors
  ([`../evidence/org_ledger_measured.json`](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/evidence/org_ledger_measured.json)).
- **Ledger:** IR-S-25…IR-S-33 added to [`../IRREGULARITIES.md`](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/IRREGULARITIES.md).

