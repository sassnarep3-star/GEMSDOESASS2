"""Integration tests exercise the retrieved upstream template, not a fork."""
from pathlib import Path
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / '.cache/template/src'
pytestmark = pytest.mark.skipif(not (TEMPLATE / 'gems57/uniqueness.py').exists(),
                                reason='run scripts/fetch_inputs.py --template-only to test shared tools')
sys.path.insert(0, str(TEMPLATE))


def test_exact_soft_metric_matches_bruteforce():
    from gems57.metric import dti_exact, dti_bruteforce, dti_binary
    p = np.zeros((8, 8), dtype='float32')
    p[1, 1] = 1
    p[3, 4] = .4
    p[7, 7] = .7
    g = np.zeros_like(p, dtype=bool)
    g[1, 2] = True
    g[4, 4] = True
    actual, reference = dti_exact(p, g), dti_bruteforce(p, g)
    for key in ('tp', 'fp', 'fn', 'dti'):
        assert actual[key] == pytest.approx(reference[key], abs=1e-7)
    assert dti_binary(p > 0, g)['dti'] == pytest.approx(dti_exact((p > 0).astype(float), g)['dti'])


def test_shared_dot_overlap_is_directional_and_uses_euclidean_radius():
    from gems57.uniqueness import dot_overlap
    mine = np.zeros((10, 10), bool)
    other = np.zeros_like(mine)
    mine[3, 3], mine[8, 8] = True, True
    other[3, 6] = True  # exactly 3 pixels from first dot
    assert dot_overlap(mine, other) == .5
    assert dot_overlap(other, mine) == 1.0
    other[:] = False
    other[4, 6] = True  # sqrt(10) > 3
    assert dot_overlap(mine, other) == 0


def test_positive_everywhere_witness_and_grid_mismatch(tmp_path):
    from gems57.uniqueness import saturation_certificate
    path = tmp_path / 'surface.tif'
    transform = from_origin(0, 500, 100, 100)
    with rasterio.open(path, 'w', driver='GTiff', height=5, width=5, count=1,
                       dtype='float32', crs='EPSG:32611', transform=transform) as out:
        out.write(np.full((5, 5), .1, dtype='float32'), 1)
    fp = np.ones((5, 5), bool)
    with rasterio.open(path) as ds:
        grid = (ds.shape, ds.crs, ds.transform)
    cert = saturation_certificate(path, fp, expected_grid=grid)
    assert cert['uncovered_allowed_pixels'] == 0 and cert['universal_overlap_blocker']
    with pytest.raises(ValueError, match='CRS/transform'):
        saturation_certificate(path, fp, expected_grid=((5, 5), grid[1], from_origin(100, 500, 100, 100)))
