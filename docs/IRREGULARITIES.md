# Irregularities Register

This register separates observed byte-level facts from explanations. None of
these entries is an accusation or an organizer ruling.

| ID | Observation | Evidence | Impact / automated action |
|---|---|---|---|
| IR-INPUT-01 | The peer-mirror `sample_submission.tif` has the same finite footprint and binary in-footprint values as `labels.tif`. | Exact local array comparison; hashes recorded in the CDCC run card. | Promotion blocked. Template values are used only for grid/footprint; never as feature or target. |
| IR-REGISTRY-01 | GEMSDOE25 D2.8 and GEMSDOE30 D28 are exact binary-mask duplicates. | Nine-pin audit: equal masks, rank correlation 1.0, directed overlap 100% both ways. | Both fail literal uniqueness; neither can be resubmitted. |
| IR-REGISTRY-02 | GEMSDOE32 B2 is an exact subset of D2.8 after 6,436 near-catalogue removals. | Nine-pin audit plus catalogue-distance bins. | Historical mechanism discussion is bounded to an observable pruning relationship. No causal score claim. |
| IR-REGISTRY-03 | Every one of the nine historical focus masks exceeds the lane threshold against at least one other pin. | `docs/data/focus_site_audit_20261027.json`. | All historical files are DO NOT SUBMIT. |
| IR-FORMAT-01 | The peer template uses NaN outside its finite footprint, while the user reported a portal range error. | Local template inspection and user-reported portal error. | Writer produces finite zero outside footprint and validates full-array [0,1]. Portal acceptance is still not guaranteed. |
| IR-SCORE-01 | The request contains conflicting current-leader claims; peer pages contain unreceipted values. | Original operating brief and source URLs. | No current leaderboard number or score estimate is shown. |
| IR-ACCESS-01 | Competition data cannot be obtained through this environment's unauthenticated access. | Official data URL is documented as authentication-gated in this project. | No claimed organizer-trained model or organizer-confirmed result. |

A new irregularity must be added here and to the relevant run card before a
candidate can advance. A human may investigate an issue, but cannot erase an
automated failed gate without a new reproducible source/evaluation record.
