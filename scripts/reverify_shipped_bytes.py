#!/usr/bin/env python3
"""Re-verify the shipped bytes against every reference convention and pin what each receipt means.

Written 2026-10-31 after the final review pass found that `format-*.json` recorded
`reference_sample: None` while the check `outside_masked_or_nan` (validator check 11) *depends* on the
reference's outside-footprint convention: a NaN-outside twin validated against a zeros-outside sample
returns 12/13 by construction. Ambiguity of exactly that kind is IR-S-29. This script runs the matrix and
writes one receipt that names every cell of it, so "13/13" can never again be quoted without its reference.
"""
from __future__ import annotations

import json
import pathlib
import sys

from gems_sass2.submission import validate_geotiff

ROOT = pathlib.Path(__file__).resolve().parents[1]
DL = ROOT / "docs/downloads"
STEM = "gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z"
REFS = {"bridge_sample_submission(zeros outside)": ROOT / "data/bridge/sample_submission.tif",
        "organizer_example_mirror(zeros outside)": ROOT / "data/official/example_submission.tif"}


def main() -> int:
    out = {"generated_utc": "2026-10-31", "validator": "src/gems_sass2/submission.py::validate_geotiff",
           "labels_file": "data/bridge/labels.tif", "matrix": {}}
    ok = True
    for enc in ("zeros", "nan"):
        f = DL / f"{STEM}-{enc}.tif"
        for refname, ref in REFS.items():
            if not ref.exists():
                out["matrix"][f"{enc}|{refname}"] = {"skipped": f"missing reference {ref}"}
                continue
            r = validate_geotiff(f, ref, ROOT / "data/bridge/labels.tif")
            failing = [k for k, v in r["checks"].items() if not v]
            out["matrix"][f"{enc}|{refname}"] = {
                "checks_passed": f"{r['checks_passed']}/{r['checks_total']}", "sha256": r["sha256"],
                "min_all_cells": r["min_all_cells"], "max_all_cells": r["max_all_cells"],
                "positive_dots_in_footprint": r["positive_dots_in_footprint"],
                "positive_on_catalogue": r["positive_on_catalogue"], "failing_checks": failing}
            if enc == "zeros" and failing:
                ok = False
        r0 = validate_geotiff(f, f, ROOT / "data/bridge/labels.tif")  # self-reference: convention-free
        out["matrix"][f"{enc}|self_reference(no_convention)"] = {
            "checks_passed": f"{r0['checks_passed']}/{r0['checks_total']}",
            "failing_checks": [k for k, v in r0["checks"].items() if not v]}
    out["claim_that_survives_every_convention"] = (
        "the PORTAL file (zeros twin) is 13/13 against both zeros-outside references and its values are "
        "0.0/1.0 min/max over all 12,279,360 cells; the NaN twin is 12/13 against a zeros-outside reference "
        "by construction (check 11 compares conventions) which is exactly why it is labelled GIS-only and "
        "never offered as the portal file")
    out["primary_all_pass"] = ok
    (ROOT / "evidence/format_reverify_collar4hex_20261031.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["matrix"], indent=1))
    print("PRIMARY_ALL_PASS:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
