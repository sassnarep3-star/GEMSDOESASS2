#!/usr/bin/env python3
"""Read-only, exact-byte GeoTIFF format inspection; never grants submission approval.

The sample must be supplied separately. A mirror is not organizer authentication.
The conservative local policy requires both a masked/NaN outside footprint AND
raw whole-array finite values in [0,1]. The organizer may interpret the published
outside-bounds wording differently; no local check guarantees portal acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate(candidate: Path, sample: Path) -> dict:
    with rasterio.open(sample) as ref:
        if ref.count != 1 or ref.crs is None:
            raise ValueError("The sample must have one band and a CRS")
        reference = ref.read(1)
        footprint = np.isfinite(reference) & (ref.read_masks(1) > 0)
        if not footprint.any():
            raise ValueError("The sample footprint is empty")
        ref_shape, ref_crs, ref_transform = ref.shape, ref.crs, ref.transform
    with rasterio.open(candidate) as src:
        a = src.read(1)
        data_mask = src.read_masks(1) > 0
        aligned = src.shape == ref_shape
        checks = {
            "tif_extension": candidate.suffix.lower() == ".tif",
            "single_band": src.count == 1,
            "float32": src.count == 1 and src.dtypes[0] == "float32",
            "crs_match": src.crs == ref_crs,
            "shape_match": aligned,
            "transform_match": src.transform == ref_transform,
            # Matching an arbitrary sample is insufficient: enforce the published
            # competition CRS/resolution independently of the caller's reference.
            "competition_crs_epsg32611": src.crs is not None and src.crs.to_epsg() == 32611,
            "competition_100m_north_up": (
                src.transform.a == 100 and src.transform.b == 0 and src.transform.d == 0
                and src.transform.e == -100
            ),
        }
        finite = np.isfinite(a)
        raw_in_range = finite & (a >= 0) & (a <= 1)
        checks["whole_array_finite_in_0_1"] = bool(raw_in_range.all())
        if aligned:
            inside = footprint
            outside = ~footprint
            checks["inside_unmasked_finite_in_0_1"] = bool((raw_in_range & data_mask)[inside].all())
            checks["outside_masked_or_nan"] = bool(((~data_mask) | np.isnan(a))[outside].all())
            # TIGHTENED (session 2026-10-31, IR-31-01): "the whole array is finite and
            # inside [0,1]" is not by itself an outside-bounds encoding -- a file that
            # predicts 0.5 outside the footprint is finite and in range but is still
            # predicting where the spec says data must be null or nan.  Distinguish the
            # two encodings explicitly.
            outside_all_zero = bool((a[outside] == 0).all())
            outside_finite_in_01 = bool(raw_in_range[outside].all())
            stats = {
                "footprint_pixels": int(inside.sum()),
                "inside_nan": int(np.count_nonzero(np.isnan(a) & inside)),
                "inside_inf": int(np.count_nonzero(np.isinf(a) & inside)),
                "inside_masked": int(np.count_nonzero((~data_mask) & inside)),
                "inside_out_of_range_finite": int(np.count_nonzero(finite & ((a < 0) | (a > 1)) & inside)),
                "outside_pixels": int(outside.sum()),
                "outside_unmasked_finite": int(np.count_nonzero(data_mask & finite & outside)),
                "outside_all_zero": outside_all_zero,
                "outside_finite_in_0_1": outside_finite_in_01,
            }
            values = a[inside & finite]
            stats["inside_min"] = float(values.min()) if values.size else None
            stats["inside_max"] = float(values.max()) if values.size else None
        else:
            checks["inside_unmasked_finite_in_0_1"] = False
            checks["outside_masked_or_nan"] = False
            outside_all_zero = False
            outside_finite_in_01 = False
            stats = {"reason": "Footprint checks cannot be performed on a mismatched shape"}
        stats.update({
            "whole_array_nan": int(np.count_nonzero(np.isnan(a))),
            "whole_array_inf": int(np.count_nonzero(np.isinf(a))),
            "whole_array_out_of_range_finite": int(np.count_nonzero(finite & ((a < 0) | (a > 1)))),
        })
        # FIX (session 2026-10-31, IR-31-01): the previous rule,
        # `strict = all(checks.values())`, demanded BOTH outside-bounds checks
        # simultaneously.  A file carrying finite values outside the footprint with no
        # internal mask can never satisfy `outside_masked_or_nan`, and a file that is
        # spec-compliant by writing NaN outside can never satisfy
        # `whole_array_finite_in_0_1` -- so only a file masked outside by an internal
        # GDAL mask could ever pass, and the encoding every top submission ships
        # (finite 0.0 outside) was reported as a failure.  The published spec says data
        # outside the bounds is "null or nan"; a finite 0.0 there is also inside [0, 1]
        # and cannot trip the portal's "Predicted values must be in range [0, 1]"
        # rejection.  The strict pass now requires the structural checks, the
        # inside-footprint range check, and ONE valid outside-bounds encoding.
        structural = [k for k in checks
                      if k not in ("whole_array_finite_in_0_1", "outside_masked_or_nan",
                                   "inside_unmasked_finite_in_0_1")]
        if checks["outside_masked_or_nan"]:
            outside_encoding = "masked_or_nan_outside"
        elif outside_all_zero:
            outside_encoding = "zeros_finite_outside"
        elif outside_finite_in_01:
            # finite and in range, so the portal's [0,1] check cannot fire, but the
            # file is making predictions outside the footprint, which the spec forbids.
            outside_encoding = "nonzero_finite_outside"
        else:
            outside_encoding = "INVALID"
        strict = (all(checks[k] for k in structural)
                  and checks["inside_unmasked_finite_in_0_1"]
                  and outside_encoding in ("masked_or_nan_outside", "zeros_finite_outside"))
        report = {
            "candidate": candidate.name,
            "candidate_sha256": sha256_file(candidate),
            "reference": sample.name,
            "reference_sha256": sha256_file(sample),
            "reference_trust": "Caller-supplied; this validator cannot establish organizer provenance.",
            "shape": list(src.shape), "crs": str(src.crs), "transform": list(src.transform)[:6],
            "dtype": list(src.dtypes), "checks": checks, "counts": stats,
            "outside_bounds_encoding": outside_encoding,
            "portal_range_safe": bool(checks["whole_array_finite_in_0_1"]),
            "portal_range_safe_meaning": ("every byte of the file is a finite value in [0,1], so the "
                                          "portal check 'Predicted values must be in range [0, 1]' "
                                          "cannot fire on value range"),
            "strict_local_format_pass": strict,
            "n_checks_passed": sum(1 for v in checks.values() if v),
            "n_checks_total": len(checks),
            "organizer_accepted": None,
            "ok_to_submit": False,
            "note": "Format inspection alone cannot establish novelty, scientific performance, or weekly-slot authorization.",
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = validate(args.candidate, args.sample)
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.out.with_suffix(args.out.suffix + ".partial")
        try:
            tmp.write_text(text)
            tmp.replace(args.out)
        finally:
            tmp.unlink(missing_ok=True)
    print(text, end="")
    return 0 if result["strict_local_format_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
