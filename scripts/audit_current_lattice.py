#!/usr/bin/env python3
"""Independently check saved research dots against one pinned registry witness.

This is a stop test, not an all-registry uniqueness or performance test. The
sample is an owner mirror, not an authenticated organizer reference.
"""
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from audit_snapshot import ROOT, binary_mask, fetch_pinned, overlap_fraction, sha256_file

CANDIDATES = {
    'HVFD': 'gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif',
    'XGHF': 'gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif',
}


def main():
    config = json.loads((ROOT / 'research/priority_sources.json').read_text())
    spec = config['inputs']['lattice']
    lattice_path = fetch_pinned(spec, ROOT / '.cache/audit/lattice.tif', True)
    sample = ROOT / 'data/bridge/sample_submission.tif'
    if sha256_file(sample) != config['inputs']['template']['sha256']:
        raise ValueError('Wrong sample mirror hash')
    results = {}
    with rasterio.open(sample) as template:
        foot = np.isfinite(template.read(1)) & (template.read_masks(1) > 0)
        lattice = binary_mask(lattice_path, template, foot)
        if not lattice.any():
            raise ValueError('Empty lattice')
        near = distance_transform_edt(~lattice) <= 3
        for name, filename in CANDIDATES.items():
            path = ROOT / 'docs/downloads' / filename
            result = overlap_fraction(binary_mask(path, template, foot), near)
            result.update(filename=filename, sha256=sha256_file(path),
                          exceeds_70_percent=result['fraction'] > .70)
            results[name] = result
    output = {'scope': 'One pinned lattice witness; not complete uniqueness or an organizer receipt',
              'reference': spec, 'sample_sha256': sha256_file(sample), 'candidates': results}
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
