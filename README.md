# GEMS Fieldnote — research and submission readiness

> **CURRENT DECISION: DO NOT SUBMIT. No candidate is cleared.** This audit run
> generated no TIFF; candidates from concurrent sessions exist but fail the
> registered lattice check. The literal registry rule is blocked, the explicit
> parallel lane and shared prepared cache are missing, and no new holdout was
> run here. There is no defensible leaderboard estimate or file-specific
> organizer receipt. This audit used no weekly slot. [Executive summary](docs/executive-summary.html) ·
> [Run card](evidence/run-card.json) · [Concurrent recheck](docs/research/concurrent-main.md)

## Standing project brief — read at the start of every session

The user's objective is to produce an independently validated, **new**, unique
single-band GeoTIFF that can compete in the DOE GEMS fault-mapping challenge;
make it easy to find and download only when it is honestly authorized. Review
GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36, explain their reported high
submissions, make score provenance and uncertainty explicit, and never copy an
old submission as a new one. An automated technical, scientific, leakage and
novelty check is required; a human geological inspection is not a substitute.
Before implementation, rank 3–5 novel geological hypotheses with layers,
signatures, off-catalogue mechanism, alternatives, cost and data provenance.
Validate the top assigned hypothesis on a spatial holdout before considering a
competition slot. Do not promise a leaderboard score from a proxy. Maintain an
accessible executive submission guide, research/source ledger, and a current
source feed. Identify limitations and follow-up work. Verify all claims against
credible sources; flag uncertainty instead of inventing results.

**Parallel-run protocol (the user's instructions):**

1. **Lane.** “Your lane is the single method paragraph below. Stay inside it. If
   your raster's rank-correlation with any registry raster exceeds [0.90], or
   more than [70%] of your dots fall within 3 px of one registry raster's dots,
   you have drifted into another lane: log it as a duplicate and stop. Check
   this on the surface before placement AND on the final dots.”
2. **Reuse, don't rebuild.** Use the template's cached feature stack,
   `evaluate_holdout.py` and `submission_writer.py`. Hide whole fault segments
   with a buffer, derive catalogue-based features only from visible faults,
   mask visible faults pixel-exactly, and score pooled DTI (alpha 0.2, beta 0.8,
   300 m triangular kernel). Fix shared-tool problems in the template rather
   than maintaining a private fork.
3. **Label every score.** A holdout result must say `HOLDOUT-DTI`, name the
   evaluator, the withheld positives and 95% CI; `ORGANIZER-CONFIRMED` requires
   a submission-page receipt. User/owner claims without a receipt are clearly
   labelled unverified. A projection is never written as a score.
4. **Leakage canary.** Test each feature alone; AUC above 0.90 is leakage until
   proven otherwise.
5. **Run card.** End with one JSON card including hypothesis, mechanism,
   named non-fault mimic, holdout DTI and CI, registry correlation/overlap,
   raster SHA-256, validator results (NaN/range/CRS/shape/transform), unique
   name and note ≤140 characters, and verdict `promote` or `negative`. Negative
   results are deliverables.
6. **Budget.** Stop after three experiments or two hours. Do not pick a real
   submission slot in the research run; a separate selector checks the weekly
   allowance and decides whether to promote.

**Core values.** Maximize P(Win): compare tradeoffs, protect scarce slots, and
avoid unsupported certainty. Own the Outcome: investigate defects end to end,
record and fix what can be fixed, and retain negative evidence. Work in three
passes: implement and verify; review assumptions and fix defects; re-check the
original request, improve and verify again. Offer actionable next steps.

This is a durable brief, not a verbatim transcript of the lengthy duplicated
request. The conversation is authoritative. A prior session's separately
recorded excerpt, whose completeness is itself unverified, is retained in
[`docs/research/prior-recorded-prompt.md`](docs/research/prior-recorded-prompt.md).
The present request contains no actual single-method paragraph; a prior
session's assigned lane must not be silently reused.

## What the audit found

* The checkout originally contained only a minimal README; the claimed local
  training/inference pipeline and cached stack were not present. We restored
  owner-mirrored raw inputs from pinned GitHub commits for inspection, including
  a 19-band training TIFF. The raw mirror is **not** a shared prepared stack or
  an organizer-authenticated file. Large inputs are ignored, not committed.
* Across the nine focus files, **0.2778 USER/OWNER-REPORTED** for GEMSDOE32
  H33-B2 is the highest among the supplied claims, but no organizer receipt
  binds a score to the bytes. The public official leaderboard is separate and
  changes over time. The [dated source observation](docs/data/live-feed.json)
  is not a project score.
* H33-B2 is a strict subset of the GEMSDOE31 B1 support; thinning may reduce
  redundant false-positive mass in the official DTI. This is a plausible
  explanation, not causal proof or a numerical projection. Hidden labels are
  unavailable. Each of the nine chosen history files overlaps another chosen
  file by more than 70% of its dots within three pixels.
* The unchanged shared template treats every finite positive pixel as support.
  Its registry contains a positive-everywhere surface; remeasurement shows any
  nonempty candidate would overlap it completely. A second, genuine
  spacing-five lattice alone forces at least 82.34% overlap at the usual
  37,654-dot budget. The prompt says stop above 70%. No exception is assumed.
  A scope/representation decision is needed before a compliant attempt.
* Sibling sites make narrower release claims. We reopened their exact candidate
  bytes: GEMSDOE28 S22C and GEMSDOE36 KPL-36 overlap the lattice by 99.62% and
  99.17%, respectively. They are **not** cleared by this literal protocol.
  Their pre-placement surfaces and complete registries were not checked here.
* While this audit was in progress, concurrent work landed on main. Reopening
  the prior sessions' SCU1, TTC-A1 and ASS2-ALEDGE TIFFs showed lattice overlap
  of **99.8514%**, **99.9549%** and **99.3241%**, respectively. They also each
  overlap the positive-everywhere witness under its literal support rule. Their
  prior narrower release claims must not be interpreted as full-registry or
  selector approval. The unmodified prior evidence is preserved; see the
  [concurrent-session audit](docs/research/concurrent-main.md).
* The official data and submission pages require login. The mirrored sample has
  positives on the catalogue even though the official page describes an all-
  absence example. Do not infer organizer origin from the mirror hash. The cause
  of the user's `[0, 1]` rejection is unknown; no rejected bytes were supplied.

Detailed evidence: [forensic audit](docs/research/audit.md),
[hypothesis slate](docs/research/hypotheses.md), [official source ledger](docs/research/sources.md),
[machine audit](evidence/portfolio-audit.json),
[raw mirror metadata](evidence/raw-mirror-metadata.json), and
[submission guide](docs/executive-summary.html).

## Reproduce this audit

Requirements: Python 3.11+, GitHub CLI (`gh`) with access to public GitHub
repositories, and the packages below. Internet access is required for the
hash-pinned owner mirrors. No DrivenData credentials are stored or requested.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_inputs.py          # pinned rasters, historical registry + shared template
python scripts/audit_portfolio.py        # writes evidence/portfolio-audit.json
python scripts/audit_concurrent.py       # independently recheck prior-session candidates
python scripts/write_run_card.py         # negative no-experiment card
python scripts/preflight.py             # prints blockers and exits 2 (not a release gate)
python scripts/build_site.py            # render local static site from evidence
python -m http.server 8000              # open /index.html
python -m pytest -q
```

For the optional 419 MB **raw owner mirror**, not the prepared feature cache:

```bash
python scripts/restore_training_mirror.py
python scripts/record_training_metadata.py
```

The external template modules are retrieved unmodified into ignored `.cache/`
from [57GEMSDOE at the pinned commit](https://github.com/buffedlizard55-lab/57GEMSDOE/tree/822a0ce5546c7b6749cdd82eb145b6b3e616603d).
Their file hashes and provenance are in `data/template.json`. No explicit
GitHub license was detected for that repository; check redistribution rights.
The shared tools are not copied into this repository. No cached feature stack is
created or substituted by these scripts.

A candidate-format check can be run without authorizing an upload:

```bash
python scripts/check_geotiff.py candidate.tif --sample official_sample_submission.tif
```

It reports saved-byte SHA-256, in-footprint finite/range and valid-mask checks,
CRS/shape/transform, external sidecars, and the shared template's stricter
all-finite policy. The local CLI rejects masked in-footprint cells, nonidentity
scale/offset and TIFFs that depend on external sidecars. It uses the supplied
sample's GDAL validity mask to determine its footprint and lists hashes of its
reference files. It conservatively requires all finite stored values—including
masked-out cells—to be in [0,1]. It does not repair values, check geological
performance or authorize a slot.
The official text permits null/NaN outside stated bounds; whether the irregular
footprint is intended as those bounds and how the portal interprets nodata are
unresolved. A local pass is not organizer acceptance.

When a complete, current indexed registry and its referenced raster cache are
actually available, run the unmodified shared comparison **twice**, once before
placement and once on saved dots. Supply an authoritative sample and the root
from which that index's relative `cache_file` paths resolve:

```bash
python scripts/check_registry.py surface.tif --phase surface --sample official_sample.tif \
  --registry-index current_registry.json --registry-root /path/to/registry/root --output surface-check.json
python scripts/check_registry.py candidate.tif --phase dots --sample official_sample.tif \
  --registry-index current_registry.json --registry-root /path/to/registry/root --output dot-check.json
```

The command stops at the first duplicate, invalid/missing registry file or time
budget, writes a negative report, and exits 2. Its current pinned dense witness
can prove a stop without scanning the rest. A diagnostic pass applies only to
the supplied accessible index; it is not proof that all prior submissions were
included, scientific validation, or selector approval. The shared comparison
also requires finite, zero-filled values outside the footprint; an outside-NaN
file stops until that local-policy conflict is resolved rather than being
silently rewritten. The checked-in historical registry snapshot is not current.

## Follow-up order

1. Resolve how the literal overlap gate treats registered continuous surfaces
   and the calibration lattice; do not silently relax it. Specify one lane and
   inventory concurrent work.
2. Obtain the exact shared prepared cache, a complete versioned current
   registry, and independently authenticated organizer sample/labels. The
   pinned owner files are reproducible but not official-origin proof.
3. Re-run the frozen same-evaluator best, retain paired bootstrap draws, test
   each feature for leakage, and perform the buffered whole-segment holdout
   before placement. Keep catalog-derived features fold-local.
4. If the surface survives, place dots, run final uniqueness and exact saved-
   byte checks with the shared writer, then write a complete, hash-bound card.
   A separate selector must check the account's current quota. The rules PDF
   describes up to three weekly feedback submissions and one final selection.

The GitHub Pages site is static. Its browser-side source watch checks public
GitHub heads, not scores or file validity; a changed head makes the frozen audit
potentially stale. A scheduled Pages workflow is supplied for refreshing the
public leaderboard observation when Pages is configured for Actions; failed
refreshes retain an explicitly dated snapshot. The Actions staging script uses
an explicit allowlist and never publishes unapproved TIFFs. Account quota and
private submission receipts cannot be accessed without the appropriate account
session.

## Concurrent-session compatibility and preservation

The main-branch sessions and their original artifacts remain in Git history at
commit `4a88f375` and their methods/data are retained in this checkout. The
current copies of their run cards now add the independent negative lattice
recheck; the earlier verdicts and unmodified original cards remain available at
that pinned commit. Older release-generating entry points are intentionally
blocked because their focus-only uniqueness checks and private holdout do not
satisfy the requested shared protocol. `scripts/check_submission.py` and
`scripts/validate_submission.py` now delegate their CLI to the stricter saved-
byte preflight; `scripts/check_uniqueness.py` delegates to the shared-template
registry diagnostic. No legacy script can grant organizer acceptance or a
weekly slot. The existing `data/bridge/` sample/labels match the owner-mirror
hashes; that does not authenticate them as organizer bytes.
