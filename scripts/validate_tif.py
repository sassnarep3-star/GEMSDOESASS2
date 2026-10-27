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
            stats = {
                "footprint_pixels": int(inside.sum()),
                "inside_nan": int(np.count_nonzero(np.isnan(a) & inside)),
                "inside_inf": int(np.count_nonzero(np.isinf(a) & inside)),
                "inside_masked": int(np.count_nonzero((~data_mask) & inside)),
                "inside_out_of_range_finite": int(np.count_nonzero(finite & ((a < 0) | (a > 1)) & inside)),
                "outside_pixels": int(outside.sum()),
                "outside_unmasked_finite": int(np.count_nonzero(data_mask & finite & outside)),
            }
            values = a[inside & finite]
            stats["inside_min"] = float(values.min()) if values.size else None
            stats["inside_max"] = float(values.max()) if values.size else None
        else:
            checks["inside_unmasked_finite_in_0_1"] = False
            checks["outside_masked_or_nan"] = False
            stats = {"reason": "Footprint checks cannot be performed on a mismatched shape"}
        stats.update({
            "whole_array_nan": int(np.count_nonzero(np.isnan(a))),
            "whole_array_inf": int(np.count_nonzero(np.isinf(a))),
            "whole_array_out_of_range_finite": int(np.count_nonzero(finite & ((a < 0) | (a > 1)))),
        })
        report = {
            "candidate": candidate.name,
            "candidate_sha256": sha256_file(candidate),
            "reference": sample.name,
            "reference_sha256": sha256_file(sample),
            "reference_trust": "Caller-supplied; this validator cannot establish organizer provenance.",
            "shape": list(src.shape), "crs": str(src.crs), "transform": list(src.transform)[:6],
            "dtype": list(src.dtypes), "checks": checks, "counts": stats,
            "strict_local_format_pass": all(checks.values()),
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
