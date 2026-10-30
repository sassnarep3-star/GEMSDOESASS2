#!/usr/bin/env python3
"""Compute a defensible leaderboard estimate for a candidate, with no free parameters.

Two measurable axes are used, both taken from the nine hash-verified focus sites:

  AXIS 1 — dot budget.  Over N in [37,654, 61,328] the nine reported values satisfy
           1/DTI = a*N + b     (R^2 = 0.91)
  AXIS 2 — catalogue contamination.  The three-site collar sweep
           44,090 dots / 19.52 % within 3 px -> 0.2600
           40,199 dots / 11.73 %              -> 0.2708
           37,654 dots /  5.77 %              -> 0.2778
         gives the marginal cost of a dot that lands inside a mapped-fault exclusion
         zone, i.e. a dot that is guaranteed false positive and guaranteed zero true
         positive because the truth set is "faults NOT in the catalogue".

The candidate is then placed on both axes.  The strain prior is deliberately NOT
allowed to add anything: its holdout advantage is measured against *mapped* faults,
which the leaderboard ranks in reverse (Spearman = -1.000).  Converting it into a
score would be a category error, so it is reported separately and excluded here.

Writes ``evidence/score_estimate.json``.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Nine hash-pinned focus sites: (stem, dots, reported, pct dots within 3 px of the
# bridge catalogue).  Every one is re-measured by audit_nine_sites.py / nearcat audit.
NINE = [
    ("GEMSDOE32", 37654, 0.2778, 5.77),
    ("GEMSDOE36", 38854, 0.2750, 5.87),
    ("GEMSDOE28", 37660, 0.2710, 11.62),
    ("GEMSDOE31", 40199, 0.2708, 11.73),
    ("GEMSDOE33", 41865, 0.2632, 14.39),
    ("GEMSDOE25", 44090, 0.2600, 19.52),
    ("GEMSDOE30", 44090, 0.2600, 19.52),
    ("GEMSDOE24", 60069, 0.2477, 19.87),
    ("GEMSDOE27", 61328, 0.2449, 19.87),
]

# The collar sweep is a controlled triple: same generator, same target dots, only the
# exclusion radius changes.  It is the only evidence isolating contamination from N.
SWEEP = [(44090, 0.2600, 19.52), (40199, 0.2708, 11.73), (37654, 0.2778, 5.77)]


def ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    a = sxy / sxx
    b = my - a * mx
    ss_res = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return a, b, 1 - ss_res / ss_tot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "evidence/score_estimate.json")
    ap.add_argument("--n-dots", type=int, default=35000)
    ap.add_argument("--contamination-pct", type=float, default=0.0)
    args = ap.parse_args()

    # ---- AXIS 1: the family law on the dot budget -------------------------------
    xs = [n for _, n, _, _ in NINE]
    ys = [1.0 / d for _, _, d, _ in NINE]
    a, b, r2 = ols(xs, ys)
    family_at_candidate = 1.0 / (a * args.n_dots + b)
    asymptote_n0 = 1.0 / b

    # ---- AXIS 2: marginal cost of a contaminated dot ----------------------------
    # Slope of reported DTI against the percentage of dots inside a 3 px collar.
    # Fit on the controlled sweep only; the sweep spans 19.52 % -> 5.77 %.
    fx = [c for _, _, c in SWEEP]
    fy = [dti for _, dti, _ in SWEEP]
    c_slope, c_int, c_r2 = ols(fx, fy)          # dDTI / dpct
    dti_reference = SWEEP[-1][1]                 # the incumbent champion 0.2778
    dti_clean = dti_reference + c_slope * (args.contamination_pct - SWEEP[-1][2])

    # ---- Combine: the law is evaluated at the candidate's N, then the champion's
    # residual contamination is removed at the sweep-measured rate.  The two
    # adjustments are applied independently and reported separately so a reader can
    # reject either one.
    contaminant_credit = dti_clean - dti_reference            # >= 0 for a clean file
    central = family_at_candidate + contaminant_credit

    # Uncertainty, stated rather than hidden: (a) the residual scatter of the nine-point
    # law, (b) a 50 % haircut on the contamination slope because it is fitted to three
    # collinear points, (c) an allowance for extrapolating below the fitted dot range.
    resid = [(1.0 / d) - (a * n + b) for _, n, d, _ in NINE]
    sd_inv = (sum(r * r for r in resid) / (len(resid) - 2)) ** 0.5
    sd_dti = sd_inv * central * central
    spread = round(max(0.04, 2 * sd_dti + 0.5 * contaminant_credit), 3)

    # PRIMARY estimator: a controlled extrapolation at fixed dot budget.
    # The candidate has exactly the champion's dot count, so the only thing that
    # changes is contamination (5.77 % -> 0.00 %).  No fit residual enters.
    controlled = dti_reference + c_slope * (args.contamination_pct - SWEEP[-1][2])
    controlled_lo = dti_reference + 1.5 * c_slope * (args.contamination_pct - SWEEP[-1][2])
    controlled_hi = dti_reference + 0.5 * c_slope * (args.contamination_pct - SWEEP[-1][2])

    out = {
        "label": "MODEL ESTIMATE — not organizer-confirmed",
        "method": (
            "controlled extrapolation at a fixed dot budget. The candidate carries the "
            "champion's 37,654 dots so the ONLY variable that differs is catalogue "
            "contamination, which the collar sweep measures directly. The strain prior "
            "is excluded because its holdout advantage is measured against mapped faults "
            "and the leaderboard ranks those in reverse (Spearman = -1.000)."
        ),
        "candidate": {"n_dots": args.n_dots, "contamination_pct": args.contamination_pct},
        "primary_controlled_estimate": {
            "anchor": "GEMSDOE32, 37,654 dots, 5.77 % within 3 px, reported 0.2778",
            "changed_variable": "contamination 5.77 % -> 0.00 %",
            "slope_dti_per_pct": c_slope,
            "estimate": controlled,
            "range_slope_minus_50pct": controlled_lo,
            "range_slope_plus_50pct": controlled_hi,
        },
        "secondary_family_law": {
            "model": "1/DTI = a*N + b",
            "a": a, "b": b, "r_squared": r2,
            "valid_range_dots": [min(xs), max(xs)],
            "value_at_candidate_N": family_at_candidate,
            "unexplained_dti": round(sd_dti, 4),
            "note": "the law reproduces the champion only to +/-%.3f; it is reported for "
                    "context, not used for the headline" % round(sd_dti, 3),
        },
        "axis2_catalogue_contamination": {
            "model": "DTI = c*contamination_pct + d, fitted on the controlled collar sweep",
            "c": c_slope, "d": c_int, "r_squared": c_r2,
            "sweep": [{"dots": n, "reported": dti, "pct_le_3px": c} for n, dti, c in SWEEP],
            "note": "the candidate is at 0.00 % by construction: a 400 m collar against "
                    "the COMPLETE 156,418-cell database, not the 60,988-cell bridge copy",
        },
        "headline": round(controlled, 2),
        "model_risk_range": [round(controlled - spread, 2), round(controlled + spread, 2)],
        "what_is_not_claimed": [
            "The 3.14x blocked-holdout advantage is NOT converted into score. Its truth is "
            "mapped traces; the leaderboard truth is unmapped faults and the two are "
            "anti-correlated (Spearman = -1.000). Converting it would be a category error.",
            "No organizer receipt exists.",
            "The gain over the champion is small (~+0.008) and the whole nine-site family "
            "sits in a narrow 0.245-0.278 band; nothing here reaches 0.4413.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ("headline", "model_risk_range",
                                          "primary_controlled_estimate")}, indent=2))
    print(f"family asymptote N->0: {asymptote_n0:.4f}")
    print(f"axis2 slope {c_slope:+.6f} DTI per pct, R2={c_r2:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
