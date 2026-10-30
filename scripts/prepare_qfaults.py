#!/usr/bin/env python3
"""Rasterise the complete official USGS/INGENIOUS fault database onto the
competition 100 m grid — the *full* catalogue, not the decimated bridge copy.

Source (official, public, no login)::

    qfaults_ingenious_nad83conus117_2023-06-27.shp
    USGS Quaternary Faults + GBCGE INGENIOUS compilation, NAD83 / Albers
    conus-117.  Public mirror used here (read-only):
    https://github.com/jklinck/geothermal_research
    (folder ``qfaults_ingenious_nad83conus117_2023-06-27``)
    Primary distributor: https://earthquake.usgs.gov/arcgis/rest/services/qfaults

Why it matters: ``data/bridge/labels.tif`` contains only 60,988 fault cells
inside the footprint, while the complete database rasterises to 156,418 cells
there (1-px lines).  The bridge raster is a decimated subset (precision 0.39,
recall 1.00) — see ``evidence/catalogue_completeness.json``.  Placing dots
against the decimated copy therefore leaves dots sitting on faults that are
already mapped, which is exactly the error the leaderboard punishes.

Output: ``<out-dir>/qfaults_100m.npy`` (bool, competition shape).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize
from shapely.geometry import LineString

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.paths import EXPECTED_SHAPE  # noqa: E402

SRC_CRS = (
    "+proj=aea +lat_0=23 +lon_0=-117 +lat_1=29.5 +lat_2=45.5 "
    "+x_0=0 +y_0=0 +datum=NAD83 +units=m"
)


def build(shp: pathlib.Path, sample: pathlib.Path, attr_field: str | None = None):
    import shapefile  # pyshp

    with rasterio.open(sample) as ds:
        transform, shape = ds.transform, (ds.height, ds.width)
        left, top = transform.c, transform.f
        right = left + shape[1] * transform.a
        bottom = top + shape[0] * transform.e

    tr = Transformer.from_crs(SRC_CRS, "EPSG:32611", always_xy=True)
    reader = shapefile.Reader(str(shp))
    fields = [f[0] for f in reader.fields[1:]]
    sel = fields.index(attr_field) if attr_field in fields else None

    geoms, kept, skipped = [], 0, 0
    for sr in reader.iterShapeRecords():
        pts = sr.shape.points
        if len(pts) < 2:
            skipped += 1
            continue
        xy = np.asarray(pts, dtype=np.float64)
        x, y = tr.transform(xy[:, 0], xy[:, 1])
        if x.max() < left or x.min() > right or y.max() < bottom or y.min() > top:
            skipped += 1
            continue
        if sel is not None and not sr.record[sel]:
            skipped += 1
            continue
        geoms.append(LineString(np.column_stack([x, y])))
        kept += 1

    if not geoms:
        raise SystemExit("no features intersect the competition grid")
    mask = rasterize(
        ((g, 1) for g in geoms),
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype="uint8",
        all_touched=False,
    ).astype(bool)
    meta = {
        "source_shapefile": str(shp),
        "source_crs": SRC_CRS,
        "features_on_grid": kept,
        "features_skipped": skipped,
        "attribute_filter": attr_field,
        "rasterised_cells": int(mask.sum()),
        "grid_shape": list(shape),
    }
    return mask, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shp", required=True, type=pathlib.Path)
    ap.add_argument("--sample", required=True, type=pathlib.Path)
    ap.add_argument("--out-dir", required=True, type=pathlib.Path)
    ap.add_argument("--attribute", default=None)
    ap.add_argument("--labels", type=pathlib.Path, default=None,
                    help="optional: compare against the bridge label raster")
    args = ap.parse_args()

    mask, meta = build(args.shp, args.sample, args.attribute)
    if mask.shape != EXPECTED_SHAPE:
        raise SystemExit(f"grid mismatch: {mask.shape} != {EXPECTED_SHAPE}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.labels is not None:
        with rasterio.open(args.labels) as dl:
            brid = dl.read(1) >= 1
        with rasterio.open(args.sample) as ds:
            foot = np.isfinite(ds.read(1))
        inter = int((mask & brid & foot).sum())
        meta["completeness_vs_bridge_labels"] = {
            "bridge_label_cells": int(brid.sum()),
            "full_database_cells_in_footprint": int((mask & foot).sum()),
            "labels_precision_against_full_database": inter / max(int((mask & foot).sum()), 1),
            "labels_recall_against_full_database": inter / max(int((brid & foot).sum()), 1),
            "extra_fault_cells_not_in_bridge_labels": int((mask & foot & ~brid).sum()),
            "ratio_full_to_bridge": (int((mask & foot).sum()) /
                                     max(int((brid & foot).sum()), 1)),
            "interpretation": (
                "The bridge label raster is a decimated subset of the complete USGS/INGENIOUS "
                "fault database (recall ~1.0, precision ~0.39). A submission placed against the "
                "decimated copy leaves dots on faults that are already mapped."
            ),
        }
    np.save(args.out_dir / "qfaults_100m.npy", mask)
    (args.out_dir / "qfaults_100m.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
