#!/usr/bin/env python3
"""Inspect a GeoTIFF; a format pass is not an upload or uniqueness approval."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.fetch import CACHE
from gems_audit.validation import validate_candidate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('candidate', type=Path)
    p.add_argument('--sample', type=Path, default=CACHE / 'inputs/sample.tif')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = validate_candidate(args.candidate, args.sample)
    text = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)
    essential = ['driver_is_geotiff', 'standalone_geotiff', 'one_band', 'float32',
                 'identity_scale_offset', 'crs_matches_reference', 'shape_matches_reference',
                 'transform_matches_reference', 'epsg_32611', 'finite_values_in_0_1',
                 'no_infinity_anywhere', 'inside_finite_and_in_0_1', 'inside_valid_mask',
                 'candidate_bytes_stable_during_validation', 'reference_files_stable_during_validation']
    return 0 if all(report['checks'][key] for key in essential) else 1


if __name__ == '__main__':
    raise SystemExit(main())
