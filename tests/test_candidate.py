from __future__ import annotations

import numpy as np

from gemsdoesass2.candidate import compute_cdcc_surface


def test_cdcc_is_label_free_and_zero_outside_joint_support() -> None:
    magnetic = np.arange(100, dtype=np.float32).reshape(10, 10) + 1
    radiometric = np.flipud(magnetic.copy())
    footprint = np.ones((10, 10), dtype=bool)
    footprint[0, :] = False
    radiometric[3, 3] = 0.0
    surface, features, support = compute_cdcc_surface(magnetic, radiometric, footprint)
    assert surface.shape == footprint.shape
    assert not bool(support[3, 3])
    assert surface[0, :].max() == 0.0
    assert surface[3, 3] == 0.0
    assert set(features) == {"magnetic_up150_edge", "radiometric_u_th_edge", "cdcc_consensus"}
    assert np.isfinite(surface).all()
    assert np.all((surface >= 0.0) & (surface <= 1.0))
