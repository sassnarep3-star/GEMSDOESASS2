#!/usr/bin/env python3
"""Assemble the 100 m feature cube as a DISK-BACKED float32 memmap.

Every input is a hash-pinned public GitHub mirror of an official release
(see registry/data_manifest.json). Outputs are git-ignored (.cache/).

  .cache/work/cube.f32        float32 [B, H, W] raw memmap
  .cache/work/cube_meta.json  band names, provenance, footprint stats

The cube is streamed band-by-band so peak RAM stays ~1 band.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / ".cache" / "mirror"


def open_stack(path: Path, shape):
    with rasterio.open(path) as ds:
        if ds.shape != shape:
            raise ValueError(f"{path.name}: shape {ds.shape} != {shape}")
        nod = ds.nodata
        descs = list(ds.descriptions)
        count = ds.count
        for i in range(1, count + 1):
            a = ds.read(i).astype(np.float32)
            m = ~np.isfinite(a)
            if nod is not None:
                m |= (a == np.float32(nod))
            a[m] = np.float32("nan")
            yield a, (descs[i - 1] if i - 1 < len(descs) and descs[i - 1] else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=str(MIRROR))
    ap.add_argument("--features", default=str(ROOT / ".cache/gems_data/training_features.tif"))
    ap.add_argument("--sample", default=str(ROOT / "data/bridge/sample_submission.tif"))
    ap.add_argument("--outdir", default=str(ROOT / ".cache/work"))
    args = ap.parse_args()

    M = Path(args.mirror)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(args.sample) as ds:
        shape = ds.shape
        transform = list(ds.transform.to_gdal())
        footprint = np.isfinite(ds.read(1))
    H, W = shape
    np.save(outdir / "footprint.npy", footprint)

    sources = [
        (Path(args.features), "f", "official 19-band competition feature stack (owner mirror of training_features.tif)"),
        (M / "GEMSDOE24_old/data/external/lidar_scarp_features_u8.tif", "lid",
         "USGS 3DEP 1 m DEM scarp/structure-tensor features, 12 ch, 100 m"),
        (M / "GEMSDOE24_old/data/external/geodawn_rad_u8.tif", "rad",
         "USGS GeoDAWN radiometrics K/Th/U/TC (DOI 10.5066/P93LGLVQ)"),
        (M / "GEMSDOE24_old/data/external/geodawn_extensions_u8.tif", "gde",
         "USGS GeoDAWN Th/K, U/K, U/Th, TMI upward-continued 150 m"),
        (M / "60GEMSDOE/data/external/topo_10m_derived_100m_u8.tif", "t10",
         "USGS 3DEP 10 m DEM derived topography, 9 ch"),
        (M / "60GEMSDOE/data/external/dem10_chi_100m_i16.tif", "chi",
         "USGS 3DEP 10 m DEM chi / ksn fluvial analysis, 5 ch"),
        (M / "GEMSDOE30/data/external/derived_gdr_2m_probes_100m_u8.tif", "prb",
         "GDR 1391 INGENIOUS 2 m shallow temperature probes"),
        (M / "GEMSDOE30/data/external/derived_gdr_paleo_100m_u8.tif", "pal",
         "GDR 1391 INGENIOUS paleo-geothermal sinter/travertine/tufa"),
        (M / "GEMSDOE30/data/external/derived_gdr_volcanics_100m_u8.tif", "vol",
         "GDR 1391 Quaternary volcanic vents"),
        (M / "GEMSDOE30/data/external/derived_gdr_qfaults_v2_100m_u8.tif", "qfv",
         "GDR 1391 INGENIOUS Quaternary fault traces, rasterised 100 m"),
        (M / "GEMSDOE30/data/external/derived_sgmc_faults_100m_u8.tif", "sgm",
         "USGS SGMC geologic-map faults"),
    ]

    # First pass: count bands and names.
    plan = []
    for path, prefix, desc in sources:
        if not path.exists():
            print(f"SKIP (absent) {path}")
            continue
        with rasterio.open(path) as ds:
            count = ds.count
            names = []
            for i in range(1, count + 1):
                d = ds.descriptions[i - 1] or ""
                short = d.split(" - ")[0].strip().replace(" ", "") or f"b{i}"
                names.append(f"{prefix}:{short}")
        plan.append((path, prefix, desc, names))
    total = sum(len(n) for _, _, _, n in plan)
    print(f"bands={total} grid={H}x{W}")

    mm = np.lib.format.open_memmap(outdir / "cube.f32", mode="w+", dtype=np.float32, shape=(total, H, W))
    b = 0
    stats = []
    for path, prefix, desc, names in plan:
        for arr, _d in open_stack(path, (H, W)):
            mm[b] = arr
            v = arr[footprint & np.isfinite(arr)]
            stats.append({
                "index": b, "name": names[b - sum(len(x[3]) for x in plan[:plan.index((path, prefix, desc, names))])] if False else None,
                "valid_frac": round(float(np.isfinite(arr[footprint]).mean()), 6),
                "min": float(v.min()) if v.size else None,
                "max": float(v.max()) if v.size else None,
                "mean": float(v.mean()) if v.size else None,
                "std": float(v.std()) if v.size else None,
            })
            b += 1
    # second, simpler: attach names in order
    flat_names = [n for _, _, _, ns in plan for n in ns]
    for i, nm in enumerate(flat_names):
        stats[i]["name"] = nm
    mm.flush()
    del mm

    meta = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "grid": {"crs": "EPSG:32611", "resolution_m": 100, "shape": [H, W], "transform_gdal": transform},
        "n_bands": total,
        "band_names": flat_names,
        "footprint_cells": int(footprint.sum()),
        "provenance": [{"prefix": p, "description": d, "bands": ns} for _, p, d, ns in plan],
        "bands": stats,
    }
    (outdir / "cube_meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print("wrote", outdir / "cube.f32", outdir / "cube_meta.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
