# Executive Summary — Nine Focus Sites and Submission Decision

## Decision at a glance

# **NO FILE IS APPROVED TO SUBMIT**

This is the highest-confidence decision available from the checked evidence.
Every historical high artifact listed below fails the literal nine-site lane rule
against at least one other pinned artifact. The newly generated CDCC-01 GeoTIFF
is format-valid and passes the nine-pin novelty test, but its paired HOLDOUT-DTI
interval crosses zero and its peer-mirror input has a template/label integrity
anomaly. It is **RESEARCH / DO NOT SUBMIT**.

There is therefore no honest recommendation to download an older high-scoring
file “for a high score.” Downloading a historical file is allowed only for
education/audit; uploading it would violate the project's uniqueness rule.

## What the labels mean

- **OWNER-REPORTED** — historical value transcribed from public peer material;
  no submission-page receipt is stored here. It is not organizer-confirmed and
  not a prediction for a new file.
- **HOLDOUT-DTI** — local proxy measurement, always accompanied by evaluator,
  withheld-positive count, and CI. It is not a leaderboard score or forecast.
- **UNIQUE AGAINST NINE PINS** — passed only against the exact immutable
  artifacts in `registry/focus_registry.json`; it is not global uniqueness.

The original request contains conflicting claims for the live leader (`0.3195`
and `0.4413`), while peer documentation records another manual value. None is
an authenticated live feed in this checkout, so this project does not display a
“current high score.”

## Download and submission table

| Site / artifact | Historical claim | Exact audit finding | Unique under literal 9-site lane rule? | File decision |
|---|---:|---|---|---|
| [GEMSDOE24 H25-1 D1.5](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) | **OWNER-REPORTED** `0.2477` | 60,069 dots; all directed overlap with GEMSDOE25 D2.8 is 100% within 3 px. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| [GEMSDOE25 D2.8](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/e40b9b5e3871cb34d138f586bde97f5099658d01/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) | **OWNER-REPORTED** `0.2600` | 44,090 dots; exact binary-mask duplicate of GEMSDOE30 D28. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| [GEMSDOE27 topo-gap](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/927322eadbde56be42ae129ccdfb9b37540d8e60/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) | **OWNER-REPORTED** `0.2449` | 61,328 dots; 98.02% directed overlap with GEMSDOE24 H25-1 within 3 px. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| [GEMSDOE28 H36-1](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/e6321461066f89080e3b1bb670d3951ab20d3638/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) | **OWNER-REPORTED** `0.2710` | 37,660 dots; 99.76% of its dots lie within 3 px of GEMSDOE31 H27-4 solo. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| [GEMSDOE30 D28](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/760af3005dd40b9f36d8fef97d6dc384fd9f2a2f/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | **OWNER-REPORTED** `0.2600` | 44,090 dots; exact binary-mask duplicate of GEMSDOE25 D2.8. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| [GEMSDOE31 H27-4 solo](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/597b04cd1afb65d1ebbe3e9417fd952be48e3d74/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) | **OWNER-REPORTED** `0.2708` | 40,199 dots; 99.56% directed overlap with GEMSDOE28 H36-1 within 3 px. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| [GEMSDOE32 H33-B2](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/5fc7792c5887735ecd3aa9a612787da588a7bf2c/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | **OWNER-REPORTED** `0.2778` | 37,654 dots; exact subset of D2.8 after deleting 6,436 dots. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| [GEMSDOE33 H33D](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/f618cc54773bd9b4d6c2b3ebf78103a05cc10cb6/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | **OWNER-REPORTED** `0.2632` | 41,865 dots; 99.98% of GEMSDOE32 B2 dots are within 3 px of this mask. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| [GEMSDOE36 Anderson](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/c5a8ae7da3bd2fcff5aa5855afd44c7a3346c16f/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | **OWNER-REPORTED** `0.2750` | 38,854 dots; 100% of B2 dots fall within 3 px and the binary rank correlation is `0.98432`. | **NO** | Audit/learning only. **DO NOT SUBMIT.** |
| **[GEMSDOESASS2 CDCC-01 research TIFF](downloads/gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.tif)** | **HOLDOUT-DTI** `0.05211` `[0.02315, 0.08277]`; evaluator `gemsdoesass2-segment-pooled-v1`; 60,988 proxy withheld positives | Max surface `abs rho = 0.01702`; max final-dot directed 3-px overlap `24.52%`, both vs nine pins. | **YES — only against nine pinned artifacts** | Download for research only. **DO NOT SUBMIT.** |

Full exact structural evidence is available in the machine-readable
[focus-site audit](data/focus_site_audit_20261027.json), with a
[registry-fetch hash receipt](data/focus_registry_fetch_receipt_20261027.json).

## Why H33-B2 plausibly had the highest reported value among these sites

This repository independently re-opened the pinned historical bytes. It found:

- D2.8 has **44,090** binary dots; H33-B2 has **37,654**.
- Every H33-B2 dot is in D2.8 (an exact binary subset).
- H33-B2 removes exactly **6,436** D2.8 dots.
- Relative to the public catalogue proxy used in this audit, **3,891** removed
  dots are at distance ≤1 pixel and **2,545** are at >1 to ≤2 pixels; none are
  farther than 2 pixels.

That pattern is consistent with a metric-aware pruning operation: predictions
immediately flanking public mapped faults can incur false-positive weight while
adding little independent hidden-fault credit. With DTI's `0.2` false-positive
and `0.8` false-negative weights, removing low-credit near-catalogue dots can
improve the observed ratio without discovering a new geological structure.

This is a **mechanism hypothesis, not causal proof**. The hidden organizer
truth, the actual score components, and a submission-page receipt tying the
pinned bytes to `0.2778` are not available. Therefore the correct statement is:

> H33-B2 is the largest owner-reported historical value in the nine selected
> pins, and its bytes are a D2.8 subset with near-catalogue deletions. We cannot
> prove that those deletions caused the reported score, nor claim a new file
> will exceed it.

## Can this project claim a result above `0.2778`?

**No.** It would be a hallucination to turn a local public-catalogue proxy
HOLDOUT-DTI into a leaderboard prediction. CDCC-01 did not clear its paired
holdout gate, has no organizer-authenticated inputs, and has no organizer
receipt. The project has not spent a weekly submission slot.

## CDCC-01 release status

| Gate | Automated result | Effect |
|---|---|---|
| Feature-alone leakage canary | Pass; maximum AUC `0.65403` ≤ `0.90` | Necessary but not sufficient |
| Surface registry check | Pass; maximum `abs rho = 0.01702` ≤ `0.90` | Unique only vs nine pins |
| Final-dot registry check | Pass; maximum overlap `24.52%` ≤ `70%` | Unique only vs nine pins |
| Best feature-alone control comparison | Point gain `+0.02034` | Not sufficient |
| Paired spatial-block CI | `[-0.00983, +0.05019]` crosses zero | **FAIL** |
| Input provenance / integrity | Peer mirror plus template/label identity detected | **FAIL** |
| GeoTIFF validator | Pass: 1 band, aligned grid, all finite `[0,1]` | Format only |

**Final verdict: `negative`; `OK_TO_SUBMIT = false`.**

See the [full run card](data/cdcc_20261027_run_card.json), [method](METHODS.md),
and [step-by-step contest guide](SUBMISSION_GUIDE.md).
