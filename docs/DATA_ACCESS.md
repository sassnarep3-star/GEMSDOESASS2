# Data Access, Provenance, and Hard Limits

## Decision rule

Only a local file that is hash-recorded, grid-validated, and traceable to an
organizer or official provider may advance beyond research. A public GitHub
mirror is useful for reproducibility and peer-forensics but is **not** proof
that the file is identical to the organizer's current asset.

| Need | Primary manual-review link | Access status in this checkout | Permitted use now |
|---|---|---:|---|
| Competition overview / metric / rules | [DrivenData GEMS overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Not fetched in this environment | Read rules manually; do not infer a live score |
| Competition downloads / submission template | [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | **Blocked:** requires authenticated competition access | Place authorized files in `data/raw/` then run `scripts/prepare_data.py` |
| Reference baseline implementation | [DrivenData reference solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) | Repository README inspected from GitHub | Code/reference only; its README says users must place downloaded data in `data/` |
| GeoDAWN magnetic and radiometric data | [USGS GeoDAWN landing page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOI](https://doi.org/10.5066/P93LGLVQ) | Link recorded; raw USGS assets not fetched in this environment | No promoted result may rely on a peer mirror as substitute |
| INGENIOUS context | [Great Basin Center for Geothermal Energy — INGENIOUS](https://gbcge.org/current-projects/ingenious/) | Link recorded; not fetched here | Context only until a versioned official input is acquired |
| GDR resource cited in request | [OpenEI GDR submission 1391](https://gdr.openei.org/submissions/1391) | Not fetched in this environment | Candidate ideas requiring it are blocked |
| GEMS PDF cited in request | [NLR document 96647](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Not fetched in this environment | Manual format/rules review needed |
| CRS lookup aid | [EPSG:32611 lookup](https://epsg.io/32611) | Link only; third-party lookup | Do not treat it as the submission-grid authority; validate against template |

## Why the data tab is still a blocker

The reference solution's current README was inspected from its public GitHub
repository. It instructs the user to download the challenge data and place it
locally; it does not contain the challenge rasters. The documented public
competition data endpoint is login-gated. This environment does not have
DrivenData authentication or a permitted way to bypass it. No script in this
repository attempts to bypass that access control.

## Expected local layout

```text
data/raw/
  sample_submission.tif        # organizer-provided grid/footprint
  labels.tif                   # public known-fault catalogue / training target
  numeric_features.tif         # organizer-provided numerical feature stack
```

Names such as `example_submission.tif`, `existing_faults.tif`, and
`gems-geodawn-numerical-features.tif` are accepted aliases by
`prepare_data.py`. The script checks grid alignment and writes an ignored,
disk-backed `feature_stack.npy` cache plus a hash manifest. It makes no claim
that a local file is official merely because it has the right name.

```bash
python -m pip install -e '.[test]'
python scripts/prepare_data.py --data-dir data/raw
```

## The checked-in CDCC research mirror

`registry/cdcc_research_input_manifest.json` pins four public GitHub blobs from
a peer repository. The pins are used solely to reproduce the checked-in
**negative** CDCC-01 experiment. The manifest includes the peer's claimed USGS
GeoDAWN DOI but labels the mirror **unverified**.

To reproduce the research result without copying a historical submission:

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

The runner defaults to `peer_mirror_unverified`, detects the observed
sample-template/label equality, and will not authorize submission.

## Irregularities that block promotion

1. **Template/label identity in the peer mirror.** The checked CDCC mirror has
   the same finite footprint and binary values as its label raster. The project
   records this as an integrity anomaly; it does **not** call it an organizer
   leak or use those template values as features/targets.
2. **No submission-page receipts.** The peer artifact scores are owner-reported
   historical claims. An artifact hash cannot prove that the same bytes were
   uploaded or yielded the reported score.
3. **Conflicting live-leader statements.** The original request includes
   `0.3195` and `0.4413`; peer documentation contains another manual read.
   None is a current authenticated leaderboard feed in this checkout.
4. **No authenticated live feed.** A static GitHub Page cannot establish an
   up-to-date DrivenData leaderboard without a legitimate accessible source.
   `docs/data/leaderboard_status.json` is intentionally absent rather than
   inventing a value.

## What access would unblock the next promoted experiment

1. Authorized local copies of the competition's current template, public
   catalogue/training labels, and numeric feature stack.
2. A saved submission-page receipt (not a screenshot claim) after an explicitly
   approved slot is used.
3. For external data, a versioned official URL/file checksum and license/usage
   review. The exact source must be added to `registry/` before it becomes a
   feature.
