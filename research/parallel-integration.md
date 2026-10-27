# Parallel-branch integration and withdrawn submission claims

**Review date:** 2026-10-27 UTC. While this audit branch was running, pull requests #2, #3 and #4 merged separate research candidates into `main`. Their raster bytes and earlier reports remain available in Git; the [pre-correction main snapshot](https://github.com/sassnarep3-star/GEMSDOESASS2/tree/4a88f3750933e3e147312bf2a6d220f777103574) preserves what they originally said. This review did not generate them or independently rerun their experiments. **None is approved for submission.**

## Independent saved-byte novelty check

The reference is the pinned registered 13GEMSDOE lattice `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2`, not an arbitrary new exception. Candidate dots are counted in the owner-mirror sample footprint; overlap is the fraction within Euclidean distance ≤3 pixels of the lattice. Geometry, candidate hash and all counts are reproducible from [`docs/data/audit.json`](../docs/data/audit.json) and the hash-pinned [`research/priority_sources.json`](priority_sources.json). One failing registry raster suffices to stop under the user's literal rule. The complete current registry and surface correlations were **not** checked.

| Parallel candidate | SHA-256 (zeros TIFF) | Dots within 3 px of lattice | Literal result |
|---|---|---:|---|
| TTC-A1 | `b8be5398deea3c71c301fdb0732c234159da78746666e0cdcb51f4df090e6fe8` | 37,637 / 37,654 = **99.9549%** | FAIL |
| ALEDGE | `cc854482215ec665a17175447474066e3418692c9604f150cc4f5459dc459707` | 43,792 / 44,090 = **99.3241%** | FAIL |
| SCU1 | `0ab88d8ab85c9bbfc690557bca0e8bf6d92dcd7657825306c9eaf294dab3fe6d` | 36,945 / 37,000 = **99.8514%** | FAIL |

The TTC and SCU NaN twins have the same dot masks as their zero twins and fail identically; each twin has its own hash in the audit. Comparisons against only nine focus champions, a small subset, or sibling candidates cannot establish the all-entry gate. Narrower earlier PASS claims are superseded, not retroactively widened. A score estimate would not undo the duplicate stop.

## Saved-byte format findings

The three zero-outside files match the mirror sample's shape, EPSG:32611, 100 m north-up affine and float32 band, and every stored value is finite in `[0,1]`. All three have 7,111,787 unmasked finite cells outside the mirror footprint, so they fail this repository's deliberately conservative outside-null/mask policy. The TTC and SCU NaN twins mask their outside pixels but contain outside NaNs, so they fail the same policy's whole-array-finite check. See the five [`format-parallel-*.json`](../docs/data/) receipts. The sample is an owner mirror, not an authenticated organizer download, and this conservative policy is not an organizer acceptance determination. The rejected file and response underlying the user's earlier range error are unavailable; its cause is unknown.

## Why the previous promotion claims were withdrawn

- **TTC:** the [original generator](https://github.com/sassnarep3-star/GEMSDOESASS2/blob/4a88f3750933e3e147312bf2a6d220f777103574/scripts/generate_submission.py#L482-L508) states that no real holdout had been run, then inserts fixed numerical holdout/CI values into its output. Those values and the claimed promotion are **withdrawn**, not treated as measured `HOLDOUT-DTI`. Its thermal layer is synthetic; its uniqueness routine sampled binary final-dot masks rather than the required pre-placement surface, and excluded the lattice. Prior assertions about the cause of the portal error are unsupported.
- **SCU:** the parallel run reports private `GEMSDOESASS2-HRv1` experiments and an extrapolated calibration from user-reported, same-family values. This audit did not reproduce those experiments; the evaluator was not the required shared template, the lane was self-declared rather than assigned in the supplied prompt, and the lattice was omitted. The proposed numeric leaderboard projection is not defensibly calibrated. Its former `candidate-unique-validated` recommendation is withdrawn.
- **ALEDGE:** the parallel run already reported a negative selector result with a paired confidence interval crossing zero. Its private evaluator and scoped nine-site comparison were not independently reproduced here; the new lattice measurement supplies an additional independent stop.

The legacy local generators, partial uniqueness checks and site/card rebuilders now stop with exit code 2 instead of emitting promotion claims or overwriting the audited site. Their source remains below the stop and in Git history for review. Compatibility validator entry points now invoke the saved-byte inspector and cannot authorize upload. This is not a private replacement for the upstream shared evaluator or writer: those require an authorized upstream fix and a separately assigned lane.

## Scope and next steps

This audit ran no geological experiment or competition submission. Parallel runs reported their own experiments; their budget and external data provenance have not been independently reconciled. An owner should resolve the lane assignment, full registry semantics and upstream tool defects, obtain authenticated data and a frozen comparable holdout, and only then run a new within-budget experiment. A promotion decision is separate and must not rely on the withdrawn artifacts above.
