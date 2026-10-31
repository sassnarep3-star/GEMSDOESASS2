#!/usr/bin/env python3
"""Score-estimator instruments: run the SHARED holdout engines over every
organizer-scored (user-reported) registry raster, so that a leaderboard score can be
*estimated* from local measurements instead of from dot count alone.

Two instruments, both computed with the repository's shared evaluators (no fork):

  1. OFF-CATALOGUE SGMC DTI - `src/gems_sass2/holdout.evaluate_sgmc_with_ci`.
     Truth = USGS SGMC-derived fault pixels that lie >300 m outside `labels.tif`
     (62,703 px).  This is the only local truth set with the same *definition* as the
     hidden competition truth: faults that the public training catalogue does not contain.
  2. HIDE-AND-RECOVER DTI - `evaluate_hide_and_recover`, static-raster mode,
     b_visible_px = 2.  Truth = 22,232 whole fault segments withheld from the catalogue.

Every number written here is HOLDOUT-DTI (a local instrument), never an organizer score.
The paired reported scores are USER-REPORTED / UNVERIFIED (site pages, no receipt).

Usage:
  GEMS_DATA_DIR=data/official python scripts/measure_ledger_instruments.py \
      --root /home/user/registry --out evidence/ledger_instruments_20261031.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.holdout import (  # noqa: E402
    HIDE_RECOVER_EVALUATOR_VERSION,
    SGMC_EVALUATOR_VERSION,
    evaluate_hide_and_recover,
    evaluate_sgmc_with_ci,
    load_holdout_context,
)
from gems_sass2.metric import kernel  # noqa: E402
from gems_sass2.paths import data_dir  # noqa: E402


def load_rows(registry_manifest: pathlib.Path, data_manifest: pathlib.Path) -> list[dict]:
    rows: list[dict] = []
    reg = json.loads(registry_manifest.read_text())
    for r in reg["rasters"]:
        rows.append({"site": r["site"], "submission": r["name"], "path": r["path"],
                     "reported": r.get("owner_reported_score"), "family": r.get("family", "")})
    man = json.loads(data_manifest.read_text())
    for f in man["files"]:
        pid = f.get("id", "")
        if pid.startswith("scored_") and f.get("path"):
            rows.append({"site": f.get("repo", "").split("/")[-1], "submission": pid,
                         "path": f["path"], "reported": None,
                         "family": "input raster (score/unscored per site page)"})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path("/home/user/registry"),
                    help="directory holding the cloned site repos")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "evidence/ledger_instruments_20261031.json")
    args = ap.parse_args()

    ddir = data_dir()
    ctx = load_holdout_context(ddir)
    foot, labels = ctx.foot, ctx.labels
    d_to_label = distance_transform_edt(~labels)

    out_rows = []
    seen: set[str] = set()
    for row in load_rows(ROOT / "registry/registry_manifest.json", ROOT / "registry/data_manifest.json"):
        path = args.root / row["path"]
        if not path.is_file():
            out_rows.append({**row, "status": "missing", "resolved_path": str(path)})
            continue
        key = str(path.resolve())
        if key in seen:
            out_rows.append({**row, "status": "duplicate-bytes", "resolved_path": str(path)})
            continue
        seen.add(key)
        with rasterio.open(path) as ds:
            if ds.shape != foot.shape:
                out_rows.append({**row, "status": "wrong-shape", "resolved_path": str(path)})
                continue
            a = ds.read(1).astype(np.float64)
        finite = np.isfinite(a)
        mask = finite & (a > 0) & foot
        n_dots = int(mask.sum())
        rec = dict(**row, status = "measured", resolved_path=str(path), dots=n_dots,
                   nan_inside_footprint=int((~finite & foot).sum()),
                   in_foot_min=float(a[foot].min()) if foot.any() else None,
                   in_foot_max=float(a[foot].max()) if foot.any() else None,
                   value_mass=float(a[mask].sum()))
        if n_dots == 0:
            rec.update(status="empty", sgmc=0.0, hide=0.0)
            out_rows.append(rec)
            continue
        rec["pct_dots_within3px_of_catalogue"] = round(float((d_to_label[mask] <= 3.0).mean() * 100.0), 4)
        rec["median_dist_to_catalogue_px"] = round(float(np.median(d_to_label[mask])), 4)
        sg = evaluate_sgmc_with_ci(mask, ctx, name=path.name)
        rec["sgmc_dti"] = round(sg["sgmc_raw_pooled_dti"], 6)
        rec["sgmc_ci95"] = [round(v, 6) for v in sg["sgmc_raw_ci95"]]
        rec["sgmc_calibrated_dti"] = round(sg["sgmc_prevalence_calibrated_dti"], 6)
        rec["sgmc_calibrated_ci95"] = [round(v, 6) for v in sg["sgmc_calibrated_ci95"]]
        rec["sgmc_n_truth"] = int(sg["n_withheld_positives"])
        rec["sgmc_n_emitted_offcat"] = int(sg["n_emitted_off_catalogue"])
        rec["sgmc_coverage"] = round(1.0 - 0.0, 6)  # placeholder replaced below
        # coverage = 1 - FN/G; recover it from the block totals the evaluator keeps internal,
        # so fall back to an explicit recomputation instead of trusting internals.
        dp = distance_transform_edt(~mask)
        cred = kernel(dp[ctx.sgmc_truth_coords])
        rec["sgmc_coverage"] = round(float(cred.sum()) / float(ctx.sgmc_n_truth), 6)
        rec["sgmc_emitter_version"] = SGMC_EVALUATOR_VERSION
        hr = evaluate_hide_and_recover(mask, ctx, name=path.name)
        rec["hide_dti"] = round(hr["pooled_dti"], 6)
        rec["hide_ci95"] = [round(v, 6) for v in hr["ci95_cluster_bootstrap"]]
        rec["hide_n_withheld"] = hr["n_withheld_positives"]
        rec["hide_emitter_version"] = HIDE_RECOVER_EVALUATOR_VERSION
        rec["hide_detached_dti"] = round(hr["detached_600m"]["pooled_dti"], 6)
        out_rows.append(rec)

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evidence_class": "DATA-MEASUREMENT (local instruments) paired with USER-REPORTED / UNVERIFIED leaderboard scores",
        "instruments": {
            "sgmc": {"evaluator": SGMC_EVALUATOR_VERSION,
                     "truth_pixels": int(ctx.sgmc_n_truth),
                     "definition": "USGS SGMC-derived fault pixels >300 m outside labels.tif (off-catalogue)"},
            "hide": {"evaluator": HIDE_RECOVER_EVALUATOR_VERSION,
                     "truth_pixels": int(sum(c.n_truth for c in ctx.cells)),
                     "definition": "whole fault segments withheld from the catalogue, 4 quadrants x draws 20/21, 1.5 km collar"},
        },
        "rows": out_rows,
        "ok_to_submit": False,
        "score_class_note": "reported = USER-REPORTED / UNVERIFIED; sgmc_dti/hide_dti = HOLDOUT-DTI",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1) + "\n")
    measured = [r for r in out_rows if r.get("status") == "measured"]
    print(f"[ledger] {len(measured)} rasters measured of {len(out_rows)} rows -> {args.out}")
    for r in sorted(measured, key=lambda x: -(x.get("reported") or 0)):
        print(f"  {r['site']:>12} rep={r.get('reported')} dots={r['dots']:>6} "
              f"sgmcDTI={r['sgmc_dti']:.4f} hideDTI={r['hide_dti']:.4f} "
              f"contam3px={r['pct_dots_within3px_of_catalogue']:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
