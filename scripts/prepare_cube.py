#!/usr/bin/env python3
"""Warp every official layer onto the competition 100 m grid and cache a .npz.

Layers and their official provenance (all public, no login):

===================  ==========================================================  ==============  =======
key                  product                                                      publisher       native
===================  ==========================================================  ==============  =======
dem, rtp, tmi,       GeoDAWN airborne geophysics, DOI 10.5066/P93LGLVQ,           USGS            50 m
tmi_hg, tmi_vg,      ScienceBase item 657e1d85d34e23d3533209f7,
upcont, k, th, u,    archives 22103_area1_tiffs.zip / 22103_area2_tiffs.zip
tc, thk, uk, uth
geod_dilatrate,      INGENIOUS geodetic strain-rate model                        GBCGE           500 m
geod_shearrate,
geod_2ndinv
ieq_n100a10,         INGENIOUS earthquake rate density                           GBCGE           500 m
deq_n100a10,
ieq_n200a05
lid_*                LiDAR scarp stack derived from the USGS 3DEP 1 m DEM        third-party     100 m
                     (12 bands, quantised uint8, published in the GEMSDOE24      mirror
                     repository ``data/external``)
sgmc                 USGS State Geologic Map Compilation bedrock faults          USGS            100 m
===================  ==========================================================  ==============  =======

The competition's own 19-band ``training_features.tif`` is only obtainable from
the DrivenData data page, which requires an account; it is **not** used here and
is **not** needed for this pipeline.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.paths import EXPECTED_SHAPE  # noqa: E402

GEOD = [
    ("geod_dilatrate", "geodetics_INGENIOUS_regional_data/geotiffs/geod_dilatrate.tif", "bilinear"),
    ("geod_shearrate", "geodetics_INGENIOUS_regional_data/geotiffs/geod_shearrate.tif", "bilinear"),
    ("geod_2ndinv", "geodetics_INGENIOUS_regional_data/geotiffs/geod_2ndinv.tif", "bilinear"),
]
SEIS = [
    ("ieq_n100a10", "seismicity_INGENIOUS_regional_data/independent_eq/geotiffs/ieq_n100a10.tif", "nearest"),
    ("deq_n100a10", "seismicity_INGENIOUS_regional_data/dependent_eq/geotiffs/deq_n100a10.tif", "nearest"),
    ("ieq_n200a05", "seismicity_INGENIOUS_regional_data/independent_eq/geotiffs/ieq_n200a05.tif", "nearest"),
]
LIDAR_BANDS = [
    "ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max", "downface_max",
    "upface_max", "cross_max", "relief", "coh100", "strike", "valid",
]
GEODAWN = ["dem", "rtp", "tmi", "tmi_hg", "tmi_vg", "upcont", "k", "th", "u",
           "tc", "thk", "uk", "uth"]


def _warp(path: pathlib.Path, transform, crs, shape, resampling):
    with rasterio.open(path) as src:
        dst = np.full(shape, np.nan, dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1), destination=dst,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=transform, dst_crs=crs,
            resampling=getattr(Resampling, resampling),
            src_nodata=src.nodata, dst_nodata=np.nan,
        )
        return dst


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True, type=pathlib.Path)
    ap.add_argument("--geodawn-dir", type=pathlib.Path)
    ap.add_argument("--ingenious-dir", type=pathlib.Path)
    ap.add_argument("--lidar-tif", type=pathlib.Path)
    ap.add_argument("--sgmc-tif", type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()

    with rasterio.open(args.sample) as ds:
        transform, crs, shape = ds.transform, ds.crs, (ds.height, ds.width)
    if shape != EXPECTED_SHAPE:
        raise SystemExit(f"grid mismatch {shape} != {EXPECTED_SHAPE}")

    out: dict[str, np.ndarray] = {}
    manifest: list[dict] = []

    if args.geodawn_dir:
        for key in GEODAWN:
            acc = None
            for area in ("2", "1"):          # area 2 is the higher-resolution block
                p = args.geodawn_dir / f"22103_{key}_a{area}.tif"
                if not p.exists():
                    continue
                w = _warp(p, transform, crs, shape, "bilinear")
                acc = w if acc is None else np.where(np.isfinite(w), w, acc)
                manifest.append({"key": key, "source": str(p)})
            if acc is not None:
                out[key] = acc

    if args.ingenious_dir:
        for key, rel, rs in GEOD + SEIS:
            p = args.ingenious_dir / rel
            if p.exists():
                out[key] = _warp(p, transform, crs, shape, rs)
                manifest.append({"key": key, "source": str(p)})

    if args.lidar_tif:
        with rasterio.open(args.lidar_tif) as d:
            for i, name in enumerate(LIDAR_BANDS):
                a = d.read(i + 1).astype(np.float32)
                a[a == 0] = np.nan
                out[f"lid_{name}"] = a
        manifest.append({"key": "lid_*", "source": str(args.lidar_tif)})

    if args.sgmc_tif:
        with rasterio.open(args.sgmc_tif) as d:
            out["sgmc"] = d.read(1).astype(np.float32)
        manifest.append({"key": "sgmc", "source": str(args.sgmc_tif)})

    if not out:
        raise SystemExit("no layers were found — check the input paths")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, **{k: v.astype(np.float32) for k, v in out.items()})
    args.out.with_suffix(".manifest.json").write_text(json.dumps({
        "grid": {"shape": list(shape), "crs": str(crs), "transform": list(transform)[:6]},
        "layers": sorted(out), "sources": manifest,
    }, indent=2))
    print(json.dumps({"out": str(args.out), "n_layers": len(out),
                      "layers": sorted(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
