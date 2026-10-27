# Nine-site forensic audit and unresolved gates

**Decision: NO new submission file is approved or generated in this session.**
This review ran no geological experiments and spent no competition slots. See
[`evidence/run-card.json`](../../evidence/run-card.json) for nulls rather than
invented holdout scores, a raster hash, or a submission note.

## Evidence and provenance

The nine history rows are the highest *user-listed* scores for each focus site,
not a complete leaderboard scrape. They are **USER/OWNER-REPORTED, UNVERIFIED**:
there is no organizer submission-page receipt binding these scores to the
corresponding raster hashes. The byte-pinned files are owner-mirrored variants;
a sibling variant's decoded support can be audited, but exact identity with an
uploaded file has not been established. The reference sample/labels are also
owner mirrors, not independently authenticated organizer files.

Reproduce the measurements with `python scripts/fetch_inputs.py` followed by
`python scripts/audit_portfolio.py`. The [JSON receipt](../../evidence/portfolio-audit.json)
records the pinned sources, SHA-256 hashes, grid, sample-based footprint, nine
by nine **directional** dot overlaps, bounds and validator observations.
It does **not** claim to enumerate the entire current registry. Individual
witnesses are sufficient to establish a failure, not a universal uniqueness pass.
Concurrent sessions subsequently merged additional TIFFs to main. Their exact
bytes were independently rechecked and also fail the lattice stop; see the
[concurrent-session review](concurrent-main.html) and its [machine evidence](../../evidence/concurrent-main-audit.json).

## The reported GEMSDOE32 result

The user-reported historical value **0.2778** is the highest among the nine
listed claims, not an authenticated score. Reopening the pinned rasters shows:

* GEMSDOE32 H33-B2's active support is a subset of GEMSDOE31's B1 support;
  B1 has 2,545 additional positive pixels and B2 has none outside it.
* GEMSDOE36's Anderson raster contains B2 and 1,200 additional positive pixels.
* GEMSDOE25 and GEMSDOE30 contain identical active support in this sample
  footprint, although their TIFF bytes are different.
* Each selected site file exceeds the 70% directional overlap threshold against
  at least one of the other eight selected files. They should not be presented
  as a new independent entry.

The [official metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric)
uses a 300 m triangular distance kernel and weights false negatives more heavily
than false positives. Removing spatially redundant predictions can lower
false-positive mass while retaining nearby true-positive coverage. That is a
plausible reason thinning and B2 pruning performed well, **not proof**: the
hidden expert labels and score-to-file receipts are unavailable. Known-fault
pixels, not an entire near-fault buffer, are masked according to [DrivenData
staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4).
Do not infer that all unknown faults within 200 m of a mapped fault have zero
credit. An improvement over the reported historical value is possible, but
no local evidence supports a numeric prediction or a claim it will happen.

## Independent literal-registry stop

The shared-template gate defines support as **finite prediction > 0**. The
[pinned template's own registry](https://github.com/buffedlizard55-lab/57GEMSDOE/blob/822a0ce5546c7b6749cdd82eb145b6b3e616603d/evidence/registry_refreshed.json)
includes the [17GEMSDOE continuous surface](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/6fc71d19d49dca4960d5434bd81b6dd06fcc030a/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif).
We re-read it on the pinned sample grid: it is positive at **every** finite
footprint pixel. Under the literal support rule, any nonempty in-footprint
dot set has 100% directional overlap within three pixels, and must stop.
Whether continuous surfaces should be treated as dot sets is a real protocol
ambiguity; silently exempting this entry would change the shared rule.

Even if that ambiguity were explicitly resolved, the separately registered
[pinned spacing-five lattice](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea0604953d7efb858d9cfbc21e20c7aca0b/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif)
leaves only 6,649 of 5,167,373 sample-footprint cells outside its three-pixel
halo. For any N-dot set, at least `(N − 6649) / N` dots lie inside the halo
(when N > 6649). At the historically common 37,654-dot budget the lower
bound is **82.34%**, so the requested **>70%** stop is unavoidable. This bound
by itself does not prove every smaller candidate fails. Rearranging dots solely
to dodge the check would not establish geological discovery or a high score.

Two site claims were rechecked against the actual saved bytes, not adopted as
our release policy:

* GEMSDOE28 S22C: **99.62%** overlap against the lattice. Its own run card
  notes the reported holdout was not buffered; it is not our protocol-cleared
  candidate.
* GEMSDOE36 KPL-36: **99.17%** overlap against the lattice. Its site promotes
  it against the nine-site subset; that is not a pass against the literal
  expanded registry. Its own receipt also separates format from upload approval.

These are overlap measurements, not scores. Their pre-placement surfaces
were not retrieved or checked, and no claim of full registry coverage is made.
The universal positive-surface witness additionally blocks each under the
unchanged literal implementation. See the full hashes and values in the JSON.

## Format and the reported range error

The official problem description requests a single-band `float32` GeoTIFF,
EPSG:32611, 100 m resolution, the same bounds/grid as the training data, and
probabilities in [0,1], with null/NaN outside the stated bounds. Exact
shape/transform must be verified against the participant's organizer-provided
sample. The error message alone does **not** identify which file, pixel,
metadata or outside-footprint encoding caused the rejection.

`python scripts/check_geotiff.py FILE --sample SAMPLE` reopens bytes, compares
the grid, checks finite values, NaN/Inf and [0,1] inside the reference
footprint, reports the dataset mask, and invokes the unchanged shared-template
validator. That validator imposes a stricter all-finite policy; an official-
style NaN-outside file may fail that local policy. Conversely, zero-filled
outside-footprint pixels can be all finite but are not marked null by a dataset
mask. The official words “outside the bounds” and a nonrectangular footprint,
and the portal's treatment of masks/NaN, have not been reconciled. Neither
local encoding alone proves portal acceptance. No clipping or silent repair.

The owner-mirrored sample has 60,988 positive pixels, all on the owner-mirrored
catalogue, whereas the official page describes a total-absence sample. This is
a provenance discrepancy; those bytes must not be called organizer-authenticated.

## Next steps

Resolve the literal registry/surface definition explicitly; identify the one
assigned method; obtain the intact shared prepared feature stack, a complete
versioned current registry, and the official sample and labels; rerun the same-
protocol best with stored paired bootstrap draws; then execute the frozen
canaries and buffered holdout. Format validation, novelty, independent positive
paired holdout evidence and a separate account-aware selector are all necessary.
The [rules PDF §3.4](https://docs.nlr.gov/docs/fy26osti/96647.pdf) describes up
to three feedback submissions per week, but the current account quota is not
available here. The official private test set is unavailable, as expected.

## Three review passes (2026-10-27)

1. **Build and verify:** pinned fifteen owner TIFFs, the shared template and
   historical registry snapshot; recomputed mask geometry, directional
   overlaps, the lattice lower bound and dense-surface witness. The registry
   snapshot's exact membership is verified by SHA-256 and source path, but its
   695 entries are a dated accessible-owner inventory, not the current or
   organizer registry. Ranked four unrun, sourced hypotheses and restored the
   optional hash-checked 19-band raw mirror without creating a prepared cache.
2. **Edge-case review:** fixed reference masks with finite nodata, invalid
   in-footprint candidate masks, non-GeoTIFF/nonidentity encodings and external
   sidecars; verify every shared-template source hash on each use. Added
   strict-threshold, metric oracle, missing-registry, duplicate, bad-value,
   stale-feed and no-repair tests. The novelty diagnostic stops on the first
   failure and never confers slot approval. Improved small-text contrast and
   keyboard access to horizontally scrollable tables.
3. **Requirements re-check:** retained explicit negative release and null
   score/hash instead of presenting old files as new; distinguished the public
   leaderboard from organizer receipts and score projections; rechecked the
   official format, exact known-fault masking and challenge deadline. The
   desktop (1440 px) and mobile (390 px) pages loaded without runtime errors,
   horizontal document overflow, or automated axe WCAG 2/2.1 A/AA violations;
   these automated checks are not a substitute for human accessibility review.
   Recomputed the published evidence and ran the tests. No scientific holdout,
   experiment, complete-current-registry clearance, upload or selection was
   performed. Scheduled deployment and live-source availability must be
   confirmed separately after GitHub Pages configuration.
