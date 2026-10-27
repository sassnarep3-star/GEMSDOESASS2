# Contest Submission Guide — Automated Gates First

## Current state

# **STOP: there is no approved file to submit.**

The only checked-in GeoTIFF is visibly named
`RESEARCH-DO-NOT-SUBMIT`, and its run card has `ok_to_submit: false`. Do not use
it in the DrivenData form. Its direct download exists to make the research
artifact auditable, not to solicit a weekly leaderboard slot.

## The only allowed release path

A future file can be submitted only if its immutable run card contains all of
these exact conditions:

```json
{
  "verdict": "promote",
  "ok_to_submit": true,
  "gates": {
    "leakage_canary": true,
    "surface_novelty": true,
    "final_dot_novelty": true,
    "holdout_promotion": true,
    "input_provenance_and_integrity": true,
    "portal_safe_format": true
  }
}
```

No person should infer authorization from a pretty map, a filename, a high
owner-reported historical claim, a local score, a file hash, or a green
format-only validator.

## Automated preflight commands

For organizer-authenticated local data (not the peer-mirror research data):

```bash
python scripts/prepare_data.py --data-dir data/raw
python scripts/fetch_focus_registry.py
python scripts/run_cdcc_experiment.py \
  --template data/raw/sample_submission.tif \
  --labels data/raw/labels.tif \
  --extensions path/to/official_geodawn_extensions.tif \
  --radiometric path/to/official_geodawn_radiometric.tif \
  --registry-dir data/registry_rasters \
  --input-provenance organizer_authenticated_local \
  --output-dir artifacts/cdcc
```

The runner performs these checks without manual raster inspection:

1. exact CRS, shape, transform, and single-band checks;
2. all finite values in `[0,1]` across the whole output array;
3. whole-segment spatial hide-and-recover HOLDOUT-DTI with confidence interval;
4. individual feature leakage canaries;
5. surface rank-correlation and final-dot 3-pixel overlap against all nine
   pinned historical rasters;
6. output SHA-256, note length, and one-TIFF ZIP verification.

Run the standalone format check if a file was moved or copied:

```bash
python scripts/validate_submission.py artifacts/cdcc/FILE.tif \
  --template data/raw/sample_submission.tif \
  --report artifacts/cdcc/FILE.validator.json
```

The conservative writer uses finite zero outside the template footprint. This
is deliberate: it prevents the observed portal error:

> Predicted values must be in range [0, 1]

## When a future run card is actually approved

The DrivenData submission interface described in the request accepts a
single-band `.tif` or a `.zip` containing exactly one GeoTIFF. After an
independent weekly-slot selector confirms eligibility:

1. select the `.tif` named in the approved run card (or the matching verified
   one-TIFF `.zip`);
2. paste the run-card `submission.note`, which is capped at 140 characters;
3. submit through the official [DrivenData submission form](https://www.drivendata.org/competitions/306/competition-doe-gems/);
4. retain the resulting primary submission-page receipt; and
5. add the receipt date, exact uploaded SHA-256, and organizer result to a new
   evidence record. Only then label that result **ORGANIZER-CONFIRMED**.

This project intentionally has no automated upload endpoint: the competition
account, rules, and weekly cap must remain under the authorized participant's
control. The lack of automated upload does not require manual raster
inspection; all scientific and format gates above are programmatic.

## Current research file (not submission-ready)

- [Research GeoTIFF — DO NOT SUBMIT](downloads/gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.tif)
- [Single-TIFF ZIP — DO NOT SUBMIT](downloads/gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.zip)
- [Run card](downloads/gemsdoesass2-cdcc-geodawn-contact-concordance-20261027-b0a765b2c644-RESEARCH-DO-NOT-SUBMIT-zeros.run-card.json)

The run card records a valid format and nine-pin novelty pass, but a negative
scientific/provenance decision. It must remain quarantined.
