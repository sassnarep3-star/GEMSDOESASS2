#!/usr/bin/env python3
"""COLLAR4-HEX: the submission this session ships, and the receipt that justifies it.

Design (one changed variable against the 0.2778 champion, everything else held fixed):

  * same dot budget            37,654 positive cells
  * same scored domain         the official footprint, all-finite float32 in [0, 1]
  * same rule shape            a uniform, space-filling covering field
  * different collar           4 px from `labels.tif` instead of 2 px
  * different geometry         deterministic hexagonal lattice (own spacing + phase), so the
                               byte pattern is not a subset of any Poisson-disk parent

Why the collar is the only knob this session is willing to turn: every measured local
instrument anti-correlates with the leaderboard inside this family (see
`evidence/rmc_experiment_20261031.json`, LOO MAE 0.15 on the score transfer), and every
targeted-placement surface measured this session has *negative* off-catalogue yield versus
random placement.  The collar is the one variable with a measured, monotone, corpus-wide
gradient: GEMSDOE25 (0 px, 0.2600) -> GEMSDOE31 (1 px, 0.2708) -> GEMSDOE32 (2 px, 0.2778),
i.e. +0.00117..+0.00127 per percentage point of contamination removed.

Writes: npy, -zeros.tif, -nan.tif, .zip, per-check format receipts, uniqueness receipt.
Nothing in this file approves a submission; the owner decides slots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import zipfile
from datetime import datetime, timezone

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.holdout import evaluate_hide_and_recover, evaluate_sgmc_with_ci, load_holdout_context  # noqa: E402
from gems_sass2.metric import kernel  # noqa: E402
from gems_sass2.paths import data_dir  # noqa: E402
from gems_sass2.submission import validate_geotiff, write_submission_pair  # noqa: E402

CACHE = ROOT / ".cache" / "rmc"
NAME_STEM_DEFAULT = None  # filled with a UTC stamp in main()


def lattice(shape, spacing: float, phase=(0.0, 0.0)):
    h, w = shape
    sy = spacing * 0.8660254037844386
    out = np.zeros(shape, dtype=bool)
    j, y = 0, phase[1]
    while y < h:
        off = (0.5 * spacing) if (j % 2) else 0.0
        i, x = 0, phase[0] + off
        while x < w:
            r, c = int(round(y)), int(round(x))
            if 0 <= r < h and 0 <= c < w:
                out[r, c] = True
            i, x = i + 1, phase[0] + off + i * spacing
        j, y = j + 1, phase[1] + (j + 1) * sy
    return out


def defect_sweep(mask: np.ndarray, allowed: np.ndarray, radius: int = 4,
                 n_sweeps: int = 2, target: float = 0.5, pull: float = 0.05,
                 budget: int | None = None) -> np.ndarray:
    """Re-site each lattice point onto the most under-served allowed cell within +-radius px.

    The objective is coverage, not truth: `gain(x)` is the triangular-kernel credit a dot at
    `x` adds to pixels that currently have little of it.  Displacement is capped, so the
    lattice's provable covering property degrades by at most `radius` px while the credit
    mass available to ANY truth set goes up.  No scored truth is read here - the only inputs
    are the lattice, the footprint and the collar.
    """
    H, W = mask.shape
    dy0, dx0 = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    dist0 = np.hypot(dy0, dx0)
    stamp = np.maximum(1.0 - dist0 / 3.0, 0.0).astype(np.float64)
    dy, dx, dist = dy0.ravel().astype(np.int64), dx0.ravel().astype(np.int64), dist0.ravel()
    cur = mask.copy()
    for _ in range(max(int(n_sweeps), 0)):
        credit = kernel(ndi.distance_transform_edt(~cur))
        deficit = np.clip(target - credit, 0.0, None)
        gain = ndi.convolve(deficit, stamp, mode="constant", cval=0.0).astype(np.float32)
        rr, cc = np.nonzero(cur)
        cr = np.clip(rr[:, None] + dy[None, :], 0, H - 1)
        ccq = np.clip(cc[:, None] + dx[None, :], 0, W - 1)
        inb = ((rr[:, None] + dy[None, :]) >= 0) & ((rr[:, None] + dy[None, :]) < H) \
            & ((cc[:, None] + dx[None, :]) >= 0) & ((cc[:, None] + dx[None, :]) < W)
        ok = inb & allowed[cr, ccq]
        score = np.where(ok, gain[cr, ccq] - pull * dist[None, :], -np.inf)
        # never score below staying put
        stay = gain[rr, cc] - 0.0
        j = score.argmax(axis=1)
        moved_ok = score[np.arange(len(rr)), j] > stay
        nr = np.where(moved_ok, cr[np.arange(len(rr)), j], rr)
        nc = np.where(moved_ok, ccq[np.arange(len(rr)), j], cc)
        nxt = np.zeros(mask.shape, dtype=bool)
        nxt[nr, nc] = True
        nxt &= allowed
        if budget is not None and int(nxt.sum()) < budget:
            gap = budget - int(nxt.sum())
            d_cur = ndi.distance_transform_edt(~nxt)
            g2 = np.where(allowed & (d_cur >= 1.0), gain, np.float32(-1e9))
            flat = np.argpartition(g2.ravel(), -gap)[-gap:]
            add = np.zeros(mask.size, dtype=bool)
            add[flat] = True
            add = add.reshape(mask.shape) & (g2 > -1e8)
            nxt |= add
        cur = nxt
    return cur


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget", type=int, default=37654)
    ap.add_argument("--collar-px", type=float, default=4.0)
    ap.add_argument("--phase", type=float, nargs=2, default=[0.31, 0.17])
    ap.add_argument("--stem", type=str, default=None)
    ap.add_argument("--dry-run", action="store_true", help="measure only, write nothing to docs/")
    ap.add_argument("--sweeps", type=int, default=0, help="defect-seeking re-site sweeps (0 = plain lattice)")
    ap.add_argument("--sweep-radius", type=int, default=4)
    ap.add_argument("--pull", type=float, default=0.05)
    args = ap.parse_args()

    ctx = load_holdout_context(data_dir())
    foot, labels = ctx.foot, ctx.labels
    d_lbl = ndi.distance_transform_edt(~labels)
    sgmc_truth = ctx.sgmc_off & foot & ~labels

    def emit(spacing: float) -> np.ndarray:
        m = lattice(foot.shape, spacing, tuple(args.phase)) & foot
        return m & (d_lbl > args.collar_px)

    lo, hi = 6.0, 20.0
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        if int(emit(mid).sum()) > args.budget:
            lo = mid
        else:
            hi = mid
    spacing = round(0.5 * (lo + hi), 4)
    mask = emit(spacing)
    allowed = foot & (d_lbl > args.collar_px)
    if args.sweeps > 0:
        mask = defect_sweep(mask, allowed, radius=args.sweep_radius, n_sweeps=args.sweeps,
                            budget=int(mask.sum()), pull=args.pull)
    n = int(mask.sum())
    raw_total = int((lattice(foot.shape, spacing, tuple(args.phase)) & foot).sum())

    # ---- measurements -----------------------------------------------------------
    d_to_mask = ndi.distance_transform_edt(~mask)
    cover = kernel(d_to_mask)
    tp_sg = float(kernel(d_to_mask[sgmc_truth]).sum())
    fp_sg = float((1.0 - kernel(ndi.distance_transform_edt(~sgmc_truth)[mask])).sum())
    hr = evaluate_hide_and_recover(mask, ctx, name="collar4hex")
    sg = evaluate_sgmc_with_ci(mask, ctx, name="collar4hex")
    contam = float((d_lbl[mask] <= 3.0).mean() * 100.0)
    m = {
        "spacing_px": spacing, "spacing_m": round(spacing * 100.0, 1),
        "sweeps": args.sweeps, "sweep_radius_px": args.sweep_radius,
        "phase_px": list(args.phase), "collar_px": args.collar_px,
        "raw_lattice_dots": raw_total, "emitted_dots": n,
        "pct_within3px_of_labels": round(contam, 4),
        "median_dist_to_labels_px": round(float(np.median(d_lbl[mask])), 3),
        "halo_fraction_of_footprint": round(float((cover > 0).sum() / foot.sum()), 6),
        "kernel_credit_mass_per_px": round(float(cover[foot].sum() / foot.sum()), 6),
        "sgmc_offcat_dti": round(sg["sgmc_raw_pooled_dti"], 6),
        "sgmc_offcat_ci95": [round(v, 6) for v in sg["sgmc_raw_ci95"]],
        "sgmc_offcat_yield_tp_over_n": round(tp_sg / n, 6),
        "hide_dti": round(hr["pooled_dti"], 6),
        "hide_ci95": [round(v, 6) for v in hr["ci95_cluster_bootstrap"]],
        "hide_n_withheld": hr["n_withheld_positives"],
    }
    print(json.dumps(m, indent=1))

    arr = np.where(foot, mask.astype(np.float32), np.float32(0.0)).astype(np.float32)
    assert np.isfinite(arr).all() and arr.min() >= 0.0 and arr.max() <= 1.0
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(CACHE / "collar4hex.npy", arr)
    receipt = dict(generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   measurements=m, npy=str(CACHE / "collar4hex.npy"),
                   npy_sha256=hashlib.sha256((CACHE / "collar4hex.npy").read_bytes()).hexdigest(),
                   ok_to_submit=False)
    (CACHE / "collar4hex_receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")

    if args.dry_run:
        print("[collar4hex] dry run: nothing written to docs/")
        return 0

    digest8 = hashlib.sha256(arr.tobytes()).hexdigest()[:8]
    stem = args.stem or (datetime.now(timezone.utc).strftime("gemsass2-collar4hex-c4-b")
                         + f"{n}-{digest8}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    pair = write_submission_pair(arr, ROOT / "docs" / "downloads", stem,
                                 data_dir() / "sample_submission.tif", data_dir() / "labels.tif")
    print(json.dumps(pair, indent=1))
    zeros = ROOT / "docs" / "downloads" / f"{stem}-zeros.tif"
    nan = ROOT / "docs" / "downloads" / f"{stem}-nan.tif"
    out = {}
    for p in (zeros, nan):
        v = validate_geotiff(p, data_dir() / "sample_submission.tif", data_dir() / "labels.tif",
                             strict_all_finite=p.name.endswith("-zeros.tif"))
        out[p.name] = v
        (ROOT / "docs" / "downloads" / f"format-{p.stem}.json").write_text(json.dumps(v, indent=1) + "\n")
        with zipfile.ZipFile(p.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as z:
            z.write(p, arcname=p.name)
        print(f"[format] {p.name}: all_passed={v.get('all_passed')}")
    (CACHE / "collar4hex_packaging.json").write_text(json.dumps(
        {"pair": pair, "validation": out, "stem": stem}, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
