"""Official GeoDAWN 19-band feature stack -> multi-scale structural feature cube.

Everything here is derived from the OFFICIAL ``training_features.tif``
(SHA-256 ``4371c82e...``, verified by ``scripts/fetch_training_features.sh``).
No label information enters this module: the fault catalogue is never read, so
a model trained on these features cannot leak the catalogue through a
distance-to-known-fault shortcut.  That is deliberate -- the competition truth
set is faults *absent* from the catalogue, so a catalogue-proximity feature
would be actively harmful (see ``evidence/nine_site_forensics.json``:
catalogue proximity correlates *negatively* with the leaderboard).

Physics of the feature set
--------------------------
A fault is a linear discontinuity in one or more potential fields.  The
classical, published detectors for that are:

* multi-scale Gaussian smoothing (which scale does the anomaly live at?),
* the Laplacian-of-Gaussian / second-derivative ridge detector, which peaks on
  the crest of a linear anomaly and is the standard "lineament" filter,
* the gradient magnitude (edge detector) at the resolution of the survey,
* smoothed *derivative* bands (the supplied ``*_hg`` / ``*_vg`` layers are
  already first derivatives; their smoothed versions are the low-frequency
  expression of the same structure).

All three are computed at several scales because a 5 km basin-bounding fault
and a 500 m scarp do not share a spatial frequency.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter, gaussian_laplace

#: External USGS products on the identical competition grid (see
#: scripts/fetch_externals.sh for DOI / ScienceBase provenance).
EXTERNAL_BLOCKS = (
    ("geodawn_rad_u8.tif", ("K", "Th", "U", "TC")),
    ("geodawn_extensions_u8.tif", ("ThK", "UK", "UTh", "TMI_up150")),
    ("lidar_scarp_features_u8.tif",
     ("ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max", "downface_max",
      "upface_max", "cross_max", "relief", "coh100", "strike", "valid")),
)
EXTERNAL_SMOOTH = 2.0
#: channels treated as circular degrees (encoded as sin/cos of the doubled angle)
CIRCULAR_CHANNELS = {"strike"}

NODATA_SENTINEL = -1e38

#: Multi-scale treatment: 0-based band indices of the official stack.
MULTISCALE_BANDS = {
    11: "detrended_elevation",
    18: "detrended_elevation_slope",
    1: "rtp_magnetic",
    2: "tmi_horizontal_gradient",
    14: "depth_to_basement",
    12: "isostatic_gravity_anomaly",
    4: "isostatic_gravity_slope",
    3: "geodetic_second_invariant",
}

SCALES = (1.5, 4.0, 10.0)
GRAD_SCALES = (1.5, 4.0)


def stack_path(root: Path) -> Path:
    return Path(root) / ".cache" / "features" / "training_features.tif"


def build_clean_stack(root: Path) -> tuple[np.memmap, np.ndarray]:
    """Inpaint nodata by nearest valid neighbour and z-score each band, on disk.

    Returns (stack float32 (19,H,W) memmap in `.cache/`, coverage bool (H,W)).
    Inpainting matters because every structural filter is a convolution: a
    NaN edge would otherwise propagate zeros into the survey margin and create
    an artificial "lineament" along the flight-line boundary.

    Streamed one band at a time: this sandbox has 3 GB of RAM and the full
    float64 intermediate representation would not fit alongside the cube.
    """
    root = Path(root)
    path = root / ".cache" / "features" / "clean_stack.npy"
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(stack_path(root)) as ds:
        h, w = ds.height, ds.width
        out = np.lib.format.open_memmap(path, mode="w+", dtype=np.float32, shape=(ds.count, h, w))
        coverage = None
        for b in range(ds.count):
            band = ds.read(b + 1).astype(np.float32)
            band[band < NODATA_SENTINEL] = np.nan
            if coverage is None:
                coverage = np.isfinite(band)
            bad = ~np.isfinite(band)
            if bad.any():
                idx = distance_transform_edt(bad, return_distances=False, return_indices=True)
                band = band[tuple(idx)]
            mu = float(np.mean(band[coverage]))
            sd = float(np.std(band[coverage]))
            out[b] = (band - mu) / (sd if sd > 0 else 1.0)
            del band
    out.flush()
    return out, coverage


def feature_names() -> list[str]:
    names: list[str] = []
    for b, label in MULTISCALE_BANDS.items():
        for s in SCALES:
            names.append(f"b{b + 1:02d}_{label}_gauss{s:g}")
        for s in SCALES:
            names.append(f"b{b + 1:02d}_{label}_log{s:g}")
        for s in GRAD_SCALES:
            names.append(f"b{b + 1:02d}_{label}_grad{s:g}")
    names.extend(f"b{b + 1:02d}_raw" for b in range(19))
    for fname, chans in EXTERNAL_BLOCKS:
        for ch in chans:
            tag = f"ext_{fname.split('_u8')[0].replace('geodawn_', '')}_{ch}"
            if ch in CIRCULAR_CHANNELS:
                names.extend([f"{tag}_sin2", f"{tag}_cos2",
                              f"{tag}_sin2_gauss{EXTERNAL_SMOOTH:g}",
                              f"{tag}_cos2_gauss{EXTERNAL_SMOOTH:g}"])
            else:
                names.append(f"{tag}_raw")
                names.append(f"{tag}_gauss{EXTERNAL_SMOOTH:g}")
    return names


def _grad_mag(a: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(a)
    return np.hypot(gy, gx)


def build_feature_cube(root: Path, cache_dir: Path | None = None) -> tuple[np.memmap, np.ndarray, list[str]]:
    """Write the full derived feature cube to a disk memmap.

    Returns (cube float32 (n_feat, H, W), coverage bool (H,W), names).
    The cube is ~4 GB for the 83-feature configuration; it lives in `.cache/`
    and is never committed.
    """
    root = Path(root)
    cache_dir = Path(cache_dir) if cache_dir else root / ".cache" / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)

    clean, coverage = build_clean_stack(root)
    names = feature_names()
    h, w = coverage.shape
    path = cache_dir / "feature_cube.npy"
    cube = np.lib.format.open_memmap(path, mode="w+", dtype=np.float32, shape=(len(names), h, w))

    i = 0
    for b in MULTISCALE_BANDS:
        arr = clean[b]
        for s in SCALES:
            cube[i] = gaussian_filter(arr, s, mode="nearest")
            i += 1
        for s in SCALES:
            cube[i] = gaussian_laplace(arr, s, mode="nearest")
            i += 1
        for s in GRAD_SCALES:
            cube[i] = _grad_mag(gaussian_filter(arr, s, mode="nearest"))
            i += 1
    for b in range(19):
        cube[i] = clean[b]
        i += 1
    del clean
    ext_dir = cache_dir.parent / "external"
    for fname, chans in EXTERNAL_BLOCKS:
        path_e = ext_dir / fname
        if not path_e.exists():
            raise FileNotFoundError(
                f"{path_e} missing -- run scripts/fetch_externals.sh")
        with rasterio.open(path_e) as ds:
            assert (ds.height, ds.width) == (h, w), (fname, ds.height, ds.width)
            data = ds.read().astype(np.float32)
        for b, ch in enumerate(chans):
            band = data[b]
            if ch == "valid":
                arr = (band > 0).astype(np.float32)
            else:
                arr = np.where(band > 0, band, np.nan)
                bad = ~np.isfinite(arr)
                if bad.any():
                    idx = distance_transform_edt(bad, return_distances=False,
                                                 return_indices=True)
                    arr = arr[tuple(idx)]
                if ch in CIRCULAR_CHANNELS:
                    theta = np.deg2rad(arr) * 2.0
                    cube[i] = np.sin(theta)
                    cube[i + 1] = np.cos(theta)
                    cube[i + 2] = gaussian_filter(np.sin(theta), EXTERNAL_SMOOTH, mode="nearest")
                    cube[i + 3] = gaussian_filter(np.cos(theta), EXTERNAL_SMOOTH, mode="nearest")
                    i += 4
                    continue
                arr = (arr - float(arr.mean())) / (float(arr.std()) or 1.0)
            cube[i] = arr
            i += 1
            cube[i] = gaussian_filter(arr, EXTERNAL_SMOOTH, mode="nearest")
            i += 1
        del data
    assert i == len(names), (i, len(names))
    cube.flush()
    return cube, coverage, names


def sample_rows(cube: np.memmap, coverage: np.ndarray, labels: np.ndarray,
                n_neg: int, seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X, y, row_index) for a class-balanced random sample.

    All catalogue positives inside the feature coverage are used; negatives are
    drawn at random from the covered, non-catalogue cells.
    """
    rng = np.random.default_rng(seed)
    pos = (labels >= 1) & coverage
    py, px = np.nonzero(pos)
    n_pos = py.size
    neg_mask = coverage & ~pos
    ny, nx = np.nonzero(neg_mask)
    take = rng.choice(ny.size, size=min(n_neg, ny.size), replace=False)
    sy = np.concatenate([py, ny[take]])
    sx = np.concatenate([px, nx[take]])
    y = np.concatenate([np.ones(n_pos, np.int8), np.zeros(take.size, np.int8)])
    order = rng.permutation(y.size)
    sy, sx, y = sy[order], sx[order], y[order]
    x = cube[:, sy, sx].T.astype(np.float32)
    return x, y, np.stack([sy, sx], axis=1)
