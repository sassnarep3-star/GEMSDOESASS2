#!/usr/bin/env python3
"""Generate the SASS2 candidate submission raster for this session's lane.

Lane (self-declared, because the standing prompt references a method paragraph that
was never supplied - see IR-10): **VENT-RIDGE CONTINUATION (VRC)**.

Emission rule
    dots are placed by cell-of-maximum thinning (spacing 2.8 px, matching the
    organizer-validated spacing of the d2-8 lineage) on a fused propensity surface

        logit(p) = logit(p_scarp_continuity)  +  w_vent * vent_prior  +  w_cont * continuity

    where
      * `p_scarp_continuity` is the fold-aware logistic detector from
        scripts/exp_scarp_continuity.py (trained on visible catalogue faults only,
        out-of-fold predictions everywhere else);
      * `vent_prior` = exp(-d/1500 m) for distance to the nearest documented
        hot spring / fumarole / Quaternary vent in the GDR 1391 in-footprint table
        (DOI 10.15121/1881483) plus the 20 Quaternary vents in the mirror;
      * `continuity` = ridge-linearity of the 2 m LiDAR scarp stack
        (max over an 11 px window minus min over the same window of the 3 px ridge).

    Catalogue exclusion: pixels within 2 px (200 m) of the public catalogue are
    excluded (the B=2 collar; the only collar value that improved an organizer score
    in the focus-site lineage, 0.2600 -> 0.2778, see knowledge/04).
    LiDAR requirement: pixels with no LiDAR coverage are excluded.

Everything computed here is HOLDOUT-DTI or a measurement. No organizer score is
claimed, and no leaderboard number is projected from the holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.holdout import (  # noqa: E402
    evaluate_hide_and_recover,
    load_holdout_context,
    paired_bootstrap_delta,
)

DATA = ROOT / "data" / "official"
LIDAR = ROOT / "data" / "external" / "lidar_scarp_features_u8.tif"
STACK = DATA / "training_features.tif"
SAMPLE = DATA / "sample_submission.tif"
VENTS_GDR = ROOT / ".cache" / "ext" / "gdr_volcanic_vents_in_footprint.csv"
SHAPE = (3730, 3292)
TRANSFORM = from_origin(243350.0, 4508550.0, 100.0, 100.0)
CRS = "EPSG:32611"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def vent_distance() -> np.ndarray | None:
    if not VENTS_GDR.is_file():
        return None
    seeds = np.zeros(SHAPE, bool)
    n = n_wells = 0
    for line in VENTS_GDR.read_text().splitlines()[1:]:
        parts = line.split(",")
        try:
            r, c = int(float(parts[3])), int(float(parts[4]))
        except (ValueError, IndexError):
            continue
        if 0 <= r < SHAPE[0] and 0 <= c < SHAPE[1]:
            seeds[r, c] = True
            n += 1
    if not seeds.any():
        return None
    d = ndi.distance_transform_edt(~seeds).astype(np.float32)
    vent_d = d
    # documented producing geothermal wells, when present in the mirror
    wells = ROOT / ".cache" / "ext" / "gdr_wellspring_in_footprint.csv"
    if wells.is_file():
        import csv as _csv
        with wells.open() as fh:
            for rec in _csv.DictReader(fh):
                # only documented HOT springs/wells carry the geothermal signal;
                # the file's `dist_known_fault_px` column is label-derived and is
                # deliberately never read (GEMSDOE24 manifest instruction).
                if (rec.get("thermalclass") or "").strip().lower() != "hot":
                    continue
                try:
                    r, c = int(float(rec["row"])), int(float(rec["col"]))
                except (ValueError, KeyError, TypeError):
                    continue
                if 0 <= r < SHAPE[0] and 0 <= c < SHAPE[1]:
                    vent_d[r, c] = 0.0
            n_wells += 0
        vent_d = ndi.distance_transform_edt(vent_d > 0).astype(np.float32)
    return vent_d, n


def cell_of_max(score: np.ndarray, allowed: np.ndarray, sep_px: float, n_dots: int) -> np.ndarray:
    s = np.where(allowed, score, -1.0).astype(np.float32)
    flat = s.ravel()
    cand = np.flatnonzero(flat > 0)
    if cand.size == 0:
        return np.zeros(s.shape, bool)
    h, w = s.shape
    cy, cx = np.divmod(cand, w)
    cell = max(int(round(sep_px)), 1)
    key = (cy // cell) * (w // cell + 2) + (cx // cell)
    order = np.lexsort((cand, key, -flat[cand]))
    ks = key[order]
    first = np.concatenate(([True], ks[1:] != ks[:-1]))
    # NOTE: `order` indexes INTO `cand`; it is not a pixel index. The previous
    # version used it directly to set the mask, which emitted the wrong pixels
    # (found 2026-10-30, see IRREGULARITIES.md IR-VRC-01).
    chosen = cand[order[first][:n_dots]]
    m = np.zeros(h * w, bool)
    m[chosen] = True
    m = m.reshape(h, w) & allowed
    # Guard: emission must be inside the footprint, off the catalogue, and on
    # LiDAR-covered ground. `allowed` enforces all three by construction.
    return m


def write_tif(mask: np.ndarray, value: float, path: Path) -> dict:
    arr = np.zeros(SHAPE, dtype=np.float32)
    arr[mask] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = dict(driver="GTiff", width=SHAPE[1], height=SHAPE[0], count=1, dtype="float32",
                   crs=CRS, transform=TRANSFORM, nodata=None, compress="deflate", predictor=1)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)
        dst.update_tags(
            method="GEMSDOESASS2 VENT-RIDGE CONTINUATION (VRC)",
            hypothesis="blind geothermal conduits reactivate linear, vent-proximal scarps that the scarp-dependent catalogue misses",
            detector="fold-aware logistic on 17 static bands + catalogue tip corridor; out-of-fold",
            emission=f"cell-of-max thinning, spacing 2.8 px, B=2 catalogue collar, LiDAR-required, value {value}",
            data_provenance="DrivenData files via owner mirrors (hash-pinned, NOT organizer-authenticated); "
                            "USGS 3DEP 1 m LiDAR-derived scarp stack and USGS GeoDAWN radiometric grids (GEMSDOE24 mirrors); "
                            "GDR 1391 vents/wells table (DOI 10.15121/1881483)",
            score_evidence="HOLDOUT-DTI only; no organizer score claimed",
        )
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path),
            "dots": int(mask.sum()), "value": float(value)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=44090, help="dot budget; 44090 is the organizer-validated count of the focus lineage")
    ap.add_argument("--spacing", type=float, default=2.8)
    ap.add_argument("--collar", type=float, default=2.0, help="px excluded around the public catalogue; 2.0 matches the focus-lineage B=2 collar")
    ap.add_argument("--w-vent", type=float, default=0.35)
    ap.add_argument("--w-cont", type=float, default=0.25)
    ap.add_argument("--tag", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    ap.add_argument("--out-dir", type=Path, default=ROOT / "docs" / "downloads")
    ap.add_argument("--evidence", type=Path, default=ROOT / "evidence" / "vrc_run_card.json")
    args = ap.parse_args()

    ctx = load_holdout_context(DATA)
    foot, labels = ctx.foot, ctx.labels
    learned = np.load(ROOT / ".cache" / "surf_learned.npy")
    if learned.shape != SHAPE:
        raise SystemExit("cached learned surface missing: run scripts/exp_scarp_continuity.py first")

    with rasterio.open(LIDAR) as src:
        ex = src.read(1).astype(np.float32)
        step = src.read(3).astype(np.float32)
        up = src.read(7).astype(np.float32)
        down = src.read(6).astype(np.float32)
        valid = src.read(12)
    amp = np.maximum.reduce([ex, step, up, down])
    del ex, step, up, down
    ridge_short = ndi.maximum_filter(amp, size=3)
    continuity = ndi.maximum_filter(ridge_short, size=11) - ndi.minimum_filter(ridge_short, size=11)
    continuity = (continuity / max(float(np.percentile(continuity, 99.9)), 1e-6)).clip(0, 1)
    del amp, ridge_short

    vd = vent_distance()
    if isinstance(vd, tuple):
        vent_d, n_vents = vd
    else:
        vent_d, n_vents = None, 0
    if vent_d is None:
        vent_prior = np.zeros(SHAPE, np.float32)
    else:
        vent_prior = np.exp(-vent_d / 15.0).astype(np.float32)   # 15 px = 1.5 km decay
        del vent_d

    eps = 1e-6
    p = np.clip(learned, eps, 1 - eps)
    logit = np.log(p / (1 - p))
    surface = 1.0 / (1.0 + np.exp(-(logit + args.w_vent * vent_prior + args.w_cont * continuity)))
    del logit, p, vent_prior, continuity, learned

    allowed = foot & (valid > 0) & (ndi.distance_transform_edt(~labels) > args.collar)
    mask = cell_of_max(surface, allowed, args.spacing, args.budget)
    if int((mask & ~foot).sum()) or int((mask & labels).sum()) or int((mask & ~(valid > 0)).sum()):
        raise SystemExit("emission guard failed: dots outside footprint/catalogue/LiDAR")
    res = evaluate_hide_and_recover(mask, ctx, b_visible_px=0.0, name="VRC-candidate")
    par_mask = None
    parent = ROOT / ".cache" / "ref" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-allfinite.tif"
    paired = None
    if parent.is_file():
        with rasterio.open(parent) as src:
            a = src.read(1)
        par_mask = np.isfinite(a) & (a > 0) & foot
        pres = evaluate_hide_and_recover(par_mask, ctx, b_visible_px=0.0, name="parent-d2-8-proxy")
        d = paired_bootstrap_delta(res["_boots"], pres["_boots"])
        paired = {"parent_holdout_dti": pres["pooled_dti"], "delta_mean": d["mean_delta"],
                  "delta_ci95": d["ci95"], "p_gt_zero": d["prob_gt_zero"],
                  "note": "The public-catalogue proxy rewards catalogue adjacency; the parent is catalogue-derived "
                          "and the candidate is off-catalogue by construction, so this paired delta is reported as a "
                          "measurement, not as a leaderboard signal (see knowledge/04 §4)."}

    stem = f"gemsdoesass2-vrc-ventridge-{int(mask.sum())}-{args.tag}"
    files = {
        "zeros": write_tif(mask, 1.0, args.out_dir / f"{stem}-zeros.tif"),
        "nan": None,
    }
    nan_path = args.out_dir / f"{stem}-nan.tif"
    arr = np.zeros(SHAPE, dtype=np.float32)
    arr[mask] = 1.0
    arr[~foot] = np.float32(np.nan)
    nan_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(nan_path, "w", driver="GTiff", width=SHAPE[1], height=SHAPE[0], count=1,
                       dtype="float32", crs=CRS, transform=TRANSFORM, nodata=np.float32(np.nan)) as dst:
        dst.write(arr, 1)
    files["nan"] = {"path": str(nan_path), "bytes": nan_path.stat().st_size,
                    "sha256": sha256(nan_path), "dots": int(mask.sum())}

    card = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "VENT-RIDGE CONTINUATION (VRC)",
        "hypothesis": "Blind geothermal conduits and their bounding structures reactivate as short, linear, "
                      "vent-proximal scarps that the scarp-dependent USGS/INGENIOUS catalogue never traced; "
                      "they are recoverable from LiDAR scarp linearity, not from catalogue proximity.",
        "mechanism": f"fold-aware logistic propensity (out-of-fold, visible catalogue only) + "
                     f"{n_vents} documented vents/wells proximity prior (1.5 km decay) + scarp ridge-continuity term; "
                     f"cell-of-max thinning at {args.spacing} px, B={args.collar} px catalogue collar, "
                     f"LiDAR-valid pixels only, budget {args.budget} dots.",
        "named_non_fault_process": "alluvial-fan toes, paleo-shoreline benches, terrace risers, lava-flow margins and "
                                   "road cuts all produce linear scarp-like steps; mitigated by requiring ridge "
                                   "continuity AND a vent-proximity term AND catalogue detachment, but not eliminated.",
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": res["evaluator_version"],
            "withheld_positive_pixels": res["n_withheld_positives"],
            "pooled_dti": res["pooled_dti"],
            "ci95": res["ci95_cluster_bootstrap"],
            "detached_600m_dti": res["detached_600m"]["pooled_dti"],
            "detached_ci95": res["detached_600m"]["ci95_cluster_bootstrap"],
            "n_dots": int(mask.sum()),
            "public_catalogue_proxy_only": True,
            "paired_vs_parent": paired,
        },
        "params": vars(args) | {"out_dir": str(args.out_dir), "evidence": str(args.evidence)},
        "files": files,
        "score_evidence": "No organizer receipt exists in this environment; no organizer score is claimed. "
                          "USER-REPORTED portfolio statistics are used for the estimate band, labelled as such.",
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    mask_path = ROOT / ".cache" / "vrc_mask.npy"
    np.save(mask_path, mask)
    print(json.dumps({k: v for k, v in card.items() if k not in ("params",)}, indent=2, allow_nan=False))
    print(f"[mask] {mask_path} dots={int(mask.sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
