"""STRAIN-RIDGE placement model for off-catalogue geothermal fault discovery.

Why this module exists
----------------------
Every one of the nine focus-site champions (GEMSDOE24/25/27/28/30/31/32/33/36)
is a pure function of the *already mapped* fault catalogue: a Poisson-disk
lattice whose density is modulated by distance to the catalogue.  Measured on
the nine hash-pinned rasters (see ``evidence/nine_site_forensics.json``):

* reported leaderboard value vs dot count ``N``  : Spearman rho = -0.983
* reported leaderboard value vs overlap with the  : Spearman rho = -1.000
  mapped catalogue (DTI scored against the
  catalogue itself)

i.e. within that family the score is governed almost entirely by how many dots
are spent and how many of them are wasted on faults that are already mapped.
None of the nine uses an independent geophysical field to decide *where* to
put a dot.

This module supplies such a field.  It combines two official, independently
produced INGENIOUS / GeoDAWN products that no focus-site raster uses:

1. **Geodetic strain rate** (``geod_dilatrate``, ``geod_shearrate``,
   ``geod_2ndinv``; GBCGE INGENIOUS regional data, 500 m) and **earthquake
   rate density** (``ieq_n100a10``).  Active faults concentrate strain and
   seismicity, so these fields localise *where faulting is happening* without
   reference to the mapped catalogue.
2. **Oriented topographic ridge response** from the 1 m-LiDAR-derived scarp
   stack (structure tensor on the slope-excess / band-passed step / antislope
   facet channels, 12 bands at 100 m).  This turns "somewhere in this corridor"
   into "along this lineament".

The two are combined as ``z(strain) + W_RIDGE * z(max(ridge, 0))`` and dots are
drawn greedily from the top of that field with a minimum separation and a hard
collar around the *complete* official USGS/INGENIOUS fault database.

Nothing in this module reads the competition labels.  Dots are excluded from
the catalogue, never attracted to it.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

# --- fixed, pre-registered parameters (do not tune on the leaderboard) -------
W_RIDGE = 0.5          # weight of the ridge term relative to the strain term
MIN_SEP_PX = 3.0       # Poisson-disk minimum separation (1 cell = 100 m)
COLLAR_PX = 4.0        # hard exclusion around the complete fault database
DEFAULT_N = 35_000     # dot budget (see evidence/strain_ridge_run_card.json)

STRAIN_KEYS = ("geod_2ndinv", "geod_shearrate", "ieq_n100a10")
LIDAR_KEYS = (
    "lid_ex_max",
    "lid_downface_max",
    "lid_upface_max",
    "lid_cross_max",
    "lid_step_max",
    "lid_lappos_max",
)


def _fillnan(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(a, dtype=np.float32)
    valid = np.isfinite(a)
    if valid.all():
        return a, valid
    out = a.copy()
    out[~valid] = float(np.median(a[valid])) if valid.any() else 0.0
    return out, valid


def zscore(a: np.ndarray) -> np.ndarray:
    """Standardise a layer over its valid cells; invalid cells become the mean."""
    filled, valid = _fillnan(a)
    if not valid.any():
        return np.zeros_like(filled, dtype=np.float32)
    m = float(filled[valid].mean())
    s = float(filled[valid].std())
    s = s if s > 1e-9 else 1.0
    return ((filled - m) / s).astype(np.float32)


def composite(cube: dict[str, np.ndarray], keys: tuple[str, ...]) -> np.ndarray:
    """Mean of z-scored layers, with invalid cells excluded from the average."""
    acc = np.zeros(next(iter(cube.values())).shape, dtype=np.float32)
    n = np.zeros_like(acc)
    for k in keys:
        z = zscore(cube[k])
        valid = np.isfinite(cube[k]).astype(np.float32)
        acc += z * valid
        n += valid
    return np.where(n > 0, acc / np.maximum(n, 1.0), 0.0).astype(np.float32)


def structure_tensor_ridge(layer: np.ndarray, sigma: float = 3.0) -> np.ndarray:
    """Orientation-coherent ridge strength of a scalar field.

    ``J = G_sigma * (grad I grad I^T)``; eigenvalues L1 >= L2.  The response
    ``sqrt(L1 + L2) * (L1 - L2) / (L1 + L2)`` is large only where there is both
    gradient energy (a real contrast) and a single dominant orientation (a
    line, not an edge crossing or a blob).  This is the standard structure
    tensor / coherence detector used for lineament mapping.
    """
    img, _ = _fillnan(layer)
    gx = ndi.sobel(img, axis=1, mode="nearest")
    gy = ndi.sobel(img, axis=0, mode="nearest")
    jxx = ndi.gaussian_filter(gx * gx, sigma)
    jyy = ndi.gaussian_filter(gy * gy, sigma)
    jxy = ndi.gaussian_filter(gx * gy, sigma)
    trace = jxx + jyy
    disc = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy * jxy)
    coherence = disc / (trace + 1e-9)
    energy = np.sqrt(np.maximum(trace, 0.0))
    return (coherence * energy).astype(np.float32)


def build_prior(cube: dict[str, np.ndarray], w_ridge: float = W_RIDGE) -> np.ndarray:
    """The STRAIN-RIDGE placement field (higher = more prospective)."""
    strain = composite(cube, STRAIN_KEYS)
    ridge = structure_tensor_ridge(composite(cube, LIDAR_KEYS))
    return (zscore(strain) + w_ridge * zscore(np.clip(ridge, 0.0, None))).astype(np.float32)


def greedy_dots(
    score: np.ndarray,
    candidate: np.ndarray,
    n_dots: int,
    min_sep_px: float = MIN_SEP_PX,
    overdraw: int = 70,
) -> np.ndarray:
    """Greedily accept the highest-scoring candidate cells subject to a
    minimum-separation constraint (a Poisson-disk / blue-noise sample of the
    prior).  Returns a flat index array of accepted cells."""
    h, w = score.shape
    rad = int(np.ceil(min_sep_px / 2.0))
    s = np.where(candidate, score, -np.inf).ravel()
    order = np.argsort(-s, kind="stable")[: min(n_dots * overdraw, s.size)]
    occ = np.zeros((h, w), dtype=bool)
    keep: list[int] = []
    for idx in order:
        if not np.isfinite(s[idx]):
            break
        r, c = divmod(int(idx), w)
        r0, r1 = max(0, r - rad), min(h, r + rad + 1)
        c0, c1 = max(0, c - rad), min(w, c + rad + 1)
        if occ[r0:r1, c0:c1].any():
            continue
        occ[r, c] = True
        keep.append(int(idx))
        if len(keep) >= n_dots:
            break
    return np.asarray(keep, dtype=np.int64)


def dots_to_raster(dots: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Binary 1-cell emission (the holdout-optimal width at N <= 100k)."""
    out = np.zeros(shape[0] * shape[1], dtype=np.float32)
    out[dots] = 1.0
    return out.reshape(shape)


def collar_mask(faults: np.ndarray, collar_px: float = COLLAR_PX) -> np.ndarray:
    """Distance-to-mapped-fault map; True where a dot is allowed."""
    if not faults.any():
        return np.ones_like(faults, dtype=bool)
    d = ndi.distance_transform_edt(~faults)
    return d > collar_px
