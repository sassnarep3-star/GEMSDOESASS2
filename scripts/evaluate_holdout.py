#!/usr/bin/env python3
"""Shared Automated Holdout Evaluator (`GEMSDOE32-HIDE-RECOVER-v3.0` & `GEMSDOE32-SGMC-CAL-v3.0`).

Reuses and hardens the shared template evaluator (fixing `IR-TEMPLATE-STATIC-VS-FOLD-02` by
persisting deterministic 256-block spatial bootstrap vectors so paired Delta-DTI 95% CIs are
always available).

Usage:
  python scripts/evaluate_holdout.py --raster path/to/candidate-zeros.tif --out evidence/eval.json
  python scripts/evaluate_holdout.py --cells-npz path/to/oof_cells.npz --full-raster path/to/candidate-zeros.tif --out evidence/eval.json
"""

from __future__ import annotations

# Fail closed: historical source is retained below for forensic review.
import sys as _legacy_sys
_LEGACY_REASON = 'Legacy evaluator is a private fork with known pooled-accounting issues; use the shared template after its upstream fix.'
if __name__ == "__main__":
    print(_LEGACY_REASON + " DO NOT SUBMIT.", file=_legacy_sys.stderr)
    raise SystemExit(2)
raise RuntimeError(_LEGACY_REASON)

import argparse
import json
import pathlib
import sys

import numpy as np
import rasterio

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.holdout import (  # noqa: E402
    evaluate_hide_and_recover,
    evaluate_sgmc_with_ci,
    load_holdout_context,
    paired_bootstrap_delta,
)
from gems_sass2.paths import data_dir  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raster", type=pathlib.Path, help="Static full-map GeoTIFF (.tif) to evaluate")
    ap.add_argument("--cells-npz", type=pathlib.Path, help="Optional fold-local OOF cell masks (.npz) for uncensored HIDE-RECOVER")
    ap.add_argument("--b-visible-px", type=float, default=2.0, help="Visible-catalogue exclusion radius in pixels (default 2.0)")
    ap.add_argument("--name", type=str, default="candidate")
    ap.add_argument("--out", type=pathlib.Path, default=None)
    args = ap.parse_args()

    if args.raster is None and args.cells_npz is None:
        ap.error("Provide --raster and/or --cells-npz")

    ddir = data_dir()
    ctx = load_holdout_context(ddir)

    # Load 0.2778 Champion fold-local B=2 reference & static 0.2778 Champion raster
    d28_cands = list((ddir / "scored").glob("*d2-8*.tif"))
    champ_hr = None
    if d28_cands:
        with rasterio.open(d28_cands[0]) as ds:
            a = ds.read(1)
            d28_mask = np.isfinite(a) & (a > 0) & ctx.foot
        champ_hr = evaluate_hide_and_recover(
            {c.key: d28_mask for c in ctx.cells},
            ctx,
            b_visible_px=2.0,
            name="GEMSDOE32_02778_fold_local_B2",
        )

    champ_tif_cands = list(pathlib.Path("/tmp/gems_audit/GEMSDOE32").rglob("*h33-2-b2*-zeros.tif"))
    champ_sg = None
    if champ_tif_cands:
        with rasterio.open(champ_tif_cands[0]) as ds:
            a = ds.read(1)
            c_mask = np.isfinite(a) & (a > 0) & ctx.foot
        champ_sg = evaluate_sgmc_with_ci(c_mask, ctx, name="GEMSDOE32_02778_static")

    report: dict = {"candidate_id": args.name}

    if args.cells_npz is not None:
        npz = np.load(args.cells_npz)
        cell_dict = {k: npz[k].astype(bool) for k in npz.files}
        hr = evaluate_hide_and_recover(cell_dict, ctx, b_visible_px=args.b_visible_px, name=args.name)
    else:
        with rasterio.open(args.raster) as ds:
            a = ds.read(1)
            m = np.isfinite(a) & (a > 0) & ctx.foot
        hr = evaluate_hide_and_recover(m, ctx, b_visible_px=args.b_visible_px, name=args.name)

    hr_clean = {k: v for k, v in hr.items() if not k.startswith("_")}
    hr_clean["detached_600m"] = {k: v for k, v in hr["detached_600m"].items() if not k.startswith("_")}
    if champ_hr is not None:
        hr_clean["paired_delta_vs_02778_champion"] = paired_bootstrap_delta(hr["_boots"], champ_hr["_boots"])
        hr_clean["detached_600m"]["paired_delta_vs_02778_champion"] = paired_bootstrap_delta(
            hr["detached_600m"]["_boots"], champ_hr["detached_600m"]["_boots"]
        )
    report["hide_and_recover_v3"] = hr_clean

    if args.raster is not None:
        with rasterio.open(args.raster) as ds:
            a = ds.read(1)
            m_full = np.isfinite(a) & (a > 0) & ctx.foot
        sg = evaluate_sgmc_with_ci(m_full, ctx, name=args.name)
        sg_clean = {k: v for k, v in sg.items() if not k.startswith("_")}
        if champ_sg is not None:
            sg_clean["paired_raw_delta_vs_02778_champion"] = paired_bootstrap_delta(sg["_raw_boots"], champ_sg["_raw_boots"])
            sg_clean["paired_cal_delta_vs_02778_champion"] = paired_bootstrap_delta(sg["_cal_boots"], champ_sg["_cal_boots"])
        report["sgmc_off_catalogue_v3"] = sg_clean

    out_txt = json.dumps(report, indent=2)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out_txt + "\n")
    print(out_txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
