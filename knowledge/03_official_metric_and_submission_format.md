# Official metric and submission format — verified from primary sources (2026-10-28)

Every claim below was read from the source named beside it on 2026-10-28 UTC. Quotations are short and exact. Where a source is silent, this file says so. Nothing here is an organizer receipt for any file.

## 1. Sources checked

| Source | What it governs | Link |
|---|---|---|
| DrivenData problem description, "Performance metric" and "Submission format" (page/967) | Metric formula, α/β, kernel, file format | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ |
| Official Rules (NLR, Sept 2026), §1.1, §3.2, §3.4, §3.5, §3.6 | Prize rounds, submission counts, final selection, AI disclosure | https://docs.nlr.gov/docs/fy26osti/96647.pdf |
| DrivenData leaderboard (public) | Public DW-Tversky scores, ranks | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ |
| Reference solution, `drivendataorg/gems-prize-reference-solution` @ `aebe92f7c8a990f0e3443451b7a825d9afd6336b` (commit dated 2026-06-16) | Official baseline output format and loss | https://github.com/drivendataorg/gems-prize-reference-solution |

## 2. The metric is probabilistic, not a dot count

From the problem description (page/967, "Performance metric"):

- "you will submit a GeoTIFF raster with fault predictions represented as pixel-wise probabilities or confidence scores between 0 and 1."
- Triangular kernel, range R = 300 m = 3 px: k(d) = max(1 − d/R, 0).
- α = 0.2 (false positives), β = 0.8 (false negatives).
- TP_w = Σ_g max_{x: d(x,g) ≤ R} p(x)·k(d(x,g))
- FP_w = Σ_{x: p(x) > 0} p(x)·[1 − max_g k(d(x,g))]
- FN_w = Σ_g [1 − max_{x: d(x,g) ≤ R} p(x)·k(d(x,g))]
- DTI = TP_w / (TP_w + α·FP_w + β·FN_w + ε). The value of ε is not published on the page.

**Consequence.** For binary inputs (p ∈ {0,1}) this reduces to the dot formulation used throughout this repository. For continuous p it does not. The repository previously had no implementation of the continuous form. It now has `dti_probabilistic` in `src/gems/metric.py`, with tests for binary equivalence, the official definitions and the range rule. Its arithmetic matches the page's worked example (TP 3.00, FP 1.89, FN 2.00 → 0.60; the test checks this). The page's own schematic raster is not published, so the example cannot be reproduced cell-by-cell.

## 3. Submission format

From the problem description, "Submission format":

- Same projected CRS as the training data (EPSG:32611, UTM zone 11N).
- Same resolution (100 m) and same bounds as the training data.
- "data outside the bounds is null or nan."
- "a single layer with datatype of 32-bit float (`float32`) with values between 0 and 1 indicating the confidence or probability of fault presence."

**Implication for the reported "Predicted values must be in range [0, 1]" error.** The official spec explicitly allows NaN outside the bounds. A NaN-outside file is therefore not, by itself, a spec violation. Every top-scoring site file the repository could pin (nine hash-pinned files, see `evidence/lattice_saturation_check.json`) and the organizer sample contain only finite values in [0,1] inside the footprint. None of the local copies reproduces the error. The rejected bytes and the portal response were not supplied, so the cause remains unknown.

## 4. Official rules facts that constrain the workflow

From the Official Rules (NLR), verbatim:

- "You can make multiple submissions, subject to the limits specified on the competition website (three submissions per week)." (§3.2)
- "Using generative artificial intelligence technology in the development of your prize submission is allowed. However, you must **indicate in the narrative** … the extent to which, if any, you used generative AI technology…" (§3.2)
- "each participating entity … may submit more than one set of predictions for automated scoring … up to three per week" and "you must select only one set of predictions to use as your final submission" (§3.4).
- The Phase 1 score uses a privately withheld set; the public leaderboard shows a public-split score (§3.6.1–3.6.2).

The official rules define **no** overlap or duplicate test against other submissions. The "70% within 3 px of a registry raster" rule is the project's own protocol, not an organizer rule. See `docs/executive-summary.html` for how that protocol now behaves.

## 5. Official reference solution (verified in the notebook)

- Labels: `known faults` from `data/labels.tif`; features from `data/numeric_features.tif`.
- Loss: `TverskyLoss(alpha=0.2, beta=0.8, mode="binary")`.
- Output: `F.sigmoid(outputs)` averaged over Monte Carlo test splits, giving probabilities in (0,1). Pixels never in a test patch stay 0.
- Notebook comment: "NOTE: it may be advantageous to threshold this map for better scoring".
- **Irregularity:** `y_out = np.zeros(...)` and `unpatchify` inherit float64, and the GeoTIFF is written with `dtype=y_final.dtype` (float64). The spec asks for float32. The notebook also writes no NaN outside the footprint. Flagged for review; the repository's own writers use float32.

## 6. Leaderboard snapshot (verified 2026-10-28, dynamic)

From the public leaderboard page read on 2026-10-28: #1 xiaofanhu 0.4544 (33 submissions); #2 cfld__ 0.3916; #3 Batik Shirt Brothers 0.3911; #4 BrandenKMurray 0.3724; #5 op01 0.3635. Ranks 1–22 are all shown with scores ≥ 0.3262 (rank 22 = nchuzhoy, 0.3262); the page was truncated after rank 23's name. Every nine-site file (best user-reported 0.2778) is therefore below rank 22 on this snapshot. The leaderboard changes; this is not an organizer receipt for any file of ours.

Note: the user's messages cite 0.3195, 0.4413 and 0.4544 as the "highest" score at different times. These are different snapshots. Only the live page is authoritative, and it is dated.

## 7. What is not in these sources

- The value of ε in the denominator.
- Exactly how the public and private splits are chosen, beyond the rules' description.
- Whether the organizer treats NaN-inside-footprint values as errors, or how it applies the "[0,1]" check. The rejected bytes are needed to answer this.
- Any per-submission receipt for the nine sites' files.
