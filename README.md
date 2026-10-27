# GEMSDOESASS2 — Evidence Before a Leaderboard Slot

> ## Current release decision: **NO FILE IS APPROVED TO SUBMIT**
>
> A unique, portal-safe GeoTIFF was generated and validated, but its experiment
> verdict is **negative**. It is a research/audit artifact only:
> [`gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.tif`](docs/downloads/gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.tif).
>
> **Do not upload it to DrivenData.** Its paired HOLDOUT-DTI confidence interval
> crosses zero and the peer-mirror inputs have a template/label integrity
> anomaly. A locally valid TIFF is not a scientifically authorized submission.

[![Static site](https://img.shields.io/badge/site-GitHub%20Pages-0b5e46)](docs/index.html)
[![Protocol](https://img.shields.io/badge/protocol-fail--closed-a52828)](docs/OPERATING_BRIEF.md)

## Mandatory start-of-session reading

**Before any experiment, read this README and the complete
[Canonical Operating Brief](docs/OPERATING_BRIEF.md).** The brief is the
repository's normalized, deduplicated implementation of the project request.
It is deliberately fail-closed: no historical owner-reported score, local
proxy holdout, or file-format check can become a leaderboard forecast or an
upload authorization.

- **[Live static site / decision card](docs/index.html)**
- **[Nine-site executive summary](docs/executive-summary.html)**
- **[Exact submission guide](docs/submission-guide.html)**
- **[Candidate hypotheses and completed holdout](docs/HYPOTHESES.md)**
- **[Official-source register and access limitations](docs/DATA_ACCESS.md)**
- **[CDCC-01 machine-readable run card](docs/data/cdcc_20261027_run_card.json)**

## What was found in the initial repository review

The branch started from commit `25172e6` with only this one-line README; there
was no application, data pipeline, cached feature stack, validation code,
website, model, source register, or submission artifact. This implementation
adds a reproducible, deterministic analytical research lane rather than
pretending prior code or data existed.

## Executive answer

| Question | Evidence-bounded answer |
|---|---|
| Which focused historical artifact has the largest reported claim? | GEMSDOE32 H33-B2 at **OWNER-REPORTED** `0.2778`. It is not organizer-confirmed. |
| Why may H33-B2 have reported well? | The pinned bytes show it is an exact 37,654-dot subset of 44,090-dot D2.8 after removing 6,436 dots within 2 pixels of the public catalogue proxy. Metric-aware false-positive pruning is a plausible explanation, not causal proof. |
| Which historical file should be submitted? | **None.** Every one of the nine focus artifacts fails the literal novelty rule against at least one other pinned focus artifact. |
| Was a unique TIF generated? | **Yes, against the nine pinned peer artifacts only.** CDCC-01 has max surface |ρ| `0.01702` and max final-dot 3-pixel overlap `24.52%`. |
| Is the generated TIF okay to submit? | **No.** It is visibly named `RESEARCH-DO-NOT-SUBMIT`; see its run card and gate failures. |
| Can the project claim it will beat 0.2778 / 0.3195 / 0.4413? | **No.** There is no authenticated live leaderboard receipt or defensible calibrated leaderboard estimate in this checkout. |

## The canonical operating requirements

This is the required operating prompt in implementation form. The full version
is in [`docs/OPERATING_BRIEF.md`](docs/OPERATING_BRIEF.md), and must be read at
the start of every work session.

### Goal and urgency

- Build a clean, auditable GEMS geothermal-fault research and submission system.
- Generate a **new** GeoTIFF rather than copying or renaming an old one.
- Make it obvious whether an artifact is safe to download for research and
  whether it is okay to submit. Those are separate decisions.
- Validate automatically; no manual-inspection escape hatch is permitted.
- Focus forensic review on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36.
- Aim for a legitimate high leaderboard result through geological reasoning and
  validated generalization—not a historical mask clone.

### Parallel-run protocol

1. **Lane:** Use one method lane. Check the candidate surface before placement
   and final dots after placement. Stop if `abs(rank correlation) > 0.90` or if
   more than `70%` of candidate dots are within 3 pixels of any registry raster.
2. **Reuse instead of rebuilding:** Use the shared feature cache when available,
   whole-fault-segment hide-and-recover holdout, pixel-exact visible-fault mask,
   and pooled DTI with alpha `0.2`, beta `0.8`, and a 300 m triangular kernel.
3. **Number labels:** Every result is **HOLDOUT-DTI** with evaluator, withheld
   positives, and 95% CI, or **ORGANIZER-CONFIRMED** from a submission-page
   receipt. A projection is never called a score.
4. **Leakage canary:** Test each source/transformed feature alone. AUC `>0.90`
   is leakage until independently proven otherwise.
5. **Run card:** Record hypothesis, mechanism, named non-fault mimic, holdout,
   registry evidence, SHA-256, validator result, bounded note, and
   `promote`/`negative` verdict.
6. **Budget:** Stop after at most 3 experiments or 2 hours. Weekly-slot
   selection is a separate action governed by competition limits.
7. **Fail closed:** A structurally valid TIFF never authorizes an upload by
   itself. All input, novelty, holdout, format, and weekly-slot gates must pass.

### Core values

- **Maximize P(Win):** choose evidence-based work that increases the chance of
  a legitimate successful outcome, even if that means rejecting an attractive
  but weak artifact.
- **Own the Outcome:** preserve negative results, repair shared tooling once,
  surface blockers clearly, and do not wait for a human to notice an automated
  failure.

## Current CDCC-01 result

CDCC-01 is a label-free physical hypothesis: a concealed fault may coincide
with both an upward-continued magnetic (`TMI_up150`) edge and an `U/Th`
radiometric edge. Its named alternatives are lithologic contacts, intrusive
margins, acquisition/processing seams, and alteration fronts.

| Arm | Result type | Result |
|---|---|---:|
| Magnetic edge control | HOLDOUT-DTI, `gemsdoesass2-segment-pooled-v1`, 60,988 withheld proxy positives, 95% CI | `0.02702` `[0.00796, 0.04771]` |
| Radiometric edge control | HOLDOUT-DTI, same protocol | `0.03177` `[0.02306, 0.03842]` |
| CDCC consensus | HOLDOUT-DTI, same protocol | `0.05211` `[0.02315, 0.08277]` |
| CDCC vs. best feature-alone control | Paired spatial-block HOLDOUT-DTI delta, 2,000 draws | `+0.02034` `[-0.00983, +0.05019]` |

The candidate passes feature-alone leakage canaries (max `0.65403` ≤ `0.90`),
surface novelty, final-dot novelty, and strict GeoTIFF validation. It **fails**
scientific promotion because the paired CI includes zero; it also fails input
trust because the only locally available research mirror's template exactly
matches its label raster. No competition slot was spent.

- [Research TIFF — **DO NOT SUBMIT**](docs/downloads/gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.tif)
- [One-TIFF ZIP — **DO NOT SUBMIT**](docs/downloads/gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.zip)
- [Run card](docs/downloads/gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.run-card.json)

## Reproduce the automated pipeline

### Install

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
pytest
```

### Reproduce the checked negative research run

This uses hash-pinned **peer mirror** inputs and remains non-submittable by
construction:

```bash
python scripts/fetch_public_research_inputs.py
python scripts/fetch_focus_registry.py
python scripts/run_cdcc_experiment.py \
  --template data/cache/cdcc_research_mirror/sample_submission.tif \
  --labels data/cache/cdcc_research_mirror/labels.tif \
  --extensions data/cache/cdcc_research_mirror/geodawn_extensions_u8.tif \
  --radiometric data/cache/cdcc_research_mirror/geodawn_rad_u8.tif \
  --registry-dir data/registry_rasters \
  --output-dir artifacts/cdcc
```

### Prepare authorized competition data

The official competition data endpoint is login-gated in this environment, so
this repository does **not** download or bypass it. After an authorized copy is
placed in `data/raw/`, run:

```bash
python scripts/prepare_data.py --data-dir data/raw
```

The script validates grid identity, records hashes, and builds an ignored
on-disk feature cache. It does not forge organizer provenance.

### Standalone strict validation

```bash
python scripts/validate_submission.py path/to/candidate.tif \
  --template data/raw/sample_submission.tif \
  --report path/to/candidate.validator.json
```

The writer/validator enforces a one-band float32 GeoTIFF on the exact template
grid with **all** values finite in `[0,1]`, including finite zeros outside the
finite template footprint. This conservatively addresses the observed portal
error: `Predicted values must be in range [0, 1]`.

## Sources and access state

| Resource | Manual-review link | Status |
|---|---|---|
| Competition overview and metric | [DrivenData GEMS overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Link recorded; no authenticated live access here |
| Competition data | [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Login-gated; not auto-downloaded |
| Official reference implementation | [GEMS Prize reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Public GitHub README inspected |
| GeoDAWN | [USGS landing page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOI](https://doi.org/10.5066/P93LGLVQ) | Raw official assets not fetched here |
| INGENIOUS | [GBCGE project page](https://gbcge.org/current-projects/ingenious/) | Context source, not locally versioned |
| GDR resource | [OpenEI GDR submission 1391](https://gdr.openei.org/submissions/1391) | Not fetched in this environment |
| CRS lookup | [EPSG:32611](https://epsg.io/32611) | Lookup aid only; local template is the authority |

See [DATA_ACCESS.md](docs/DATA_ACCESS.md) for the complete limitation and
integrity register.

## What remains before any real submission

1. Obtain current, organizer-authenticated template, labels/catalogue, and
   numeric feature data through authorized competition access.
2. Resolve the template/label integrity anomaly using official inputs.
3. Acquire and hash verified official external source layers before using them
   in a promoted model.
4. Run one preregistered next hypothesis in a non-overlapping lane, with all
   canaries and the full nine-pin registry loaded.
5. Beat the comparable local holdout control with a paired confidence interval
   strictly above zero.
6. Run the separate weekly-slot selector, upload through the authorized
   competition account, and retain the submission-page receipt.

Until then, **do not submit any checked-in GeoTIFF**.
