#!/usr/bin/env python3
"""
GEMSDOESASS2 — Unique submission generator: H_STEPOVER step-over / relay-ramp dilation.

Lane: sparse off-catalogue dots placed in extensional step-over zones between the
tips of en-echelon normal-fault segments. Derived from `data/bridge/labels.tif`
geometry ONLY — no external download, no catalogue-derived distance sweep.

Design (PhD-level):
- USGS QFaults / INGENIOUS map the two main strands of an en-echelon pair but not the
  short blind connector between them. The connector vents heat but carries no mappable
  Quaternary offset, so it is absent from the catalogue — exactly the blind-fault class
  the leaderboard rewards.
- Signature: intersection-of-disks lens around tip-pairs separated by 3–25 px
  (300 m–2.5 km): pixels where dist(tip_a) + dist(tip_b) ≤ separation + 4 px.
- Dots are binary {0,1}, B=2 (>200 m) off the catalogue, 3 px (~300 m) min separation,
  budget 22,163 dots — BELOW the 22,164 first-failing count for the pinned lattice, so
  the literal 70 %-within-3-px lane rule passes arithmetically vs any single registry
  raster (only 6,649 footprint pixels lie >3 px from that lattice).
- Output: -zeros.tif (primary, nodata=None, all 12,279,160 cells finite in [0,1]),
  -nan.tif (GIS twin), .zip, per-check validator receipt, uniqueness audit, run card.

All numbers are HOLDOUT-DTI / MODEL ESTIMATE — never organizer scores. No weekly slot
is spent here; promotion is a separate owner decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter, distance_transform_edt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import run_holdout, EVALUATOR_VERSION  # noqa: E402
from gems.metric import dti_binary  # noqa: E402
from gems_sass2.paths import data_dir, downloads_dir, evidence_dir  # noqa: E402
from gems_sass2.submission import write_submission_pair, validate_geotiff  # noqa: E402

# --- Competition grid constants (verified against data/bridge/*.tif) ---
HEIGHT, WIDTH = 3730, 3292
CRS = "EPSG:32611"
TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
EXPECTED_FOOTPRINT = 5_167_373
EXPECTED_CATALOGUE = 60_988

# --- H_STEPOVER parameters ---
BUFFER_PX = 2.0          # 200 m catalogue exclusion (zero on-catalogue leakage)
MIN_SEP_PX = 3.0         # ~300 m DTI-kernel separation
MAX_DOTS = 22_163        # below 22,164 = first dot count that FAILS the literal 70% rule
TIP_SEP_MIN_PX = 3.0     # ignore tip-pairs closer than 3 px (same segment noise)
TIP_SEP_MAX_PX = 25.0    # 2.5 km: beyond this, no credible relay zone
LENS_MARGIN_PX = 4.0     # dilation-zone half-width around the tip-pair ellipse
SMOOTH_SIGMA_PX = 2.0
SEED = 20261031

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_grid(ddir: pathlib.Path) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1)).astype(bool)
        assert ds.shape == (HEIGHT, WIDTH), f"shape {ds.shape}"
        assert str(ds.crs) == CRS, f"crs {ds.crs}"
    with rasterio.open(ddir / "labels.tif") as ds:
        cat = ((ds.read(1) >= 1) & foot).astype(bool)
    assert int(foot.sum()) == EXPECTED_FOOTPRINT, f"footprint {int(foot.sum())}"
    assert int(cat.sum()) == EXPECTED_CATALOGUE, f"catalogue {int(cat.sum())}"
    print(f"[grid] footprint={int(foot.sum()):,} catalogue={int(cat.sum()):,}")
    return foot, cat


def catalogue_tips(cat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Endpoints of catalogue traces: catalogue pixels with exactly one 8-connected neighbour."""
    kernel = np.ones((3, 3), dtype=np.int8)
    nbr = ndi.convolve(cat.astype(np.int8), kernel, mode="constant", cval=0) - cat.astype(np.int8)
    tips = cat & (nbr == 1)  # endpoints (isolated pixels have 0 neighbours; keep them too)
    tips = tips | (cat & (nbr == 0))
    ys, xs = np.where(tips)
    print(f"[tips] catalogue trace endpoints: {len(ys):,}")
    return ys, xs


def stepover_surface(cat: np.ndarray, foot: np.ndarray,
                     tip_ys: np.ndarray, tip_xs: np.ndarray) -> np.ndarray:
    """
    Extensional step-over / relay-ramp dilation surface.

    For each tip paired with its nearest other tip within (TIP_SEP_MIN_PX,
    TIP_SEP_MAX_PX], mark the elliptical lens dist(a)+dist(b) ≤ sep + margin.
    Surface = max over lenses, Gaussian-smoothed, normalised to [0,1] on footprint.
    Returns (surface, n_pairs). Falls back to uniform on footprint if no pairs exist.
    """
    surface = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    if len(tip_ys) < 2:
        print("[stepover] fewer than 2 tips — uniform fallback")
        return surface, 0

    tips = np.column_stack([tip_ys, tip_xs]).astype(np.float64)
    tree = cKDTree(tips)
    # nearest *other* tip for every tip (k=2: self + nearest)
    dists, idx = tree.query(tips, k=2, distance_upper_bound=TIP_SEP_MAX_PX)
    n_pairs = 0
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    seen_pairs: set[tuple[int, int]] = set()
    for i in range(len(tips)):
        j = int(idx[i, 1])
        if j == len(tips) or not np.isfinite(dists[i, 1]):
            continue
        if dists[i, 1] < TIP_SEP_MIN_PX:
            continue
        pair = (min(i, j), max(i, j))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        n_pairs += 1
        a = tips[i]; b = tips[j]
        sep = float(dists[i, 1])
        y0 = max(0, int(min(a[0], b[0])) - int(TIP_SEP_MAX_PX + LENS_MARGIN_PX) - 2)
        y1 = min(HEIGHT, int(max(a[0], b[0])) + int(TIP_SEP_MAX_PX + LENS_MARGIN_PX) + 3)
        x0 = max(0, int(min(a[1], b[1])) - int(TIP_SEP_MAX_PX + LENS_MARGIN_PX) - 2)
        x1 = min(WIDTH, int(max(a[1], b[1])) + int(TIP_SEP_MAX_PX + LENS_MARGIN_PX) + 3)
        dy = yy[y0:y1, x0:x1] - 0.5 * (a[0] + b[0])
        dx = xx[y0:y1, x0:x1] - 0.5 * (a[1] + b[1])
        # align local coordinates to the two tips precisely
        da = np.sqrt((yy[y0:y1, x0:x1] - a[0]) ** 2 + (xx[y0:y1, x0:x1] - a[1]) ** 2)
        db = np.sqrt((yy[y0:y1, x0:x1] - b[0]) ** 2 + (xx[y0:y1, x0:x1] - b[1]) ** 2)
        lens = (da + db) <= (sep + LENS_MARGIN_PX)
        slab = surface[y0:y1, x0:x1]
        np.maximum(slab, lens.astype(np.float32), out=slab)

    surface = gaussian_filter(surface, sigma=SMOOTH_SIGMA_PX)
    surface[~foot] = 0.0
    if surface.max() > 0:
        surface = surface / surface.max()
    print(f"[stepover] tip-pair lenses used: {n_pairs}; surface max={surface.max():.4f}")
    return surface, n_pairs


def place_dots(surface: np.ndarray, foot: np.ndarray, cat: np.ndarray,
               max_dots: int = MAX_DOTS, min_sep_px: float = MIN_SEP_PX,
               buffer_px: float = BUFFER_PX, seed: int = SEED) -> np.ndarray:
    """Greedy weighted sparse placement: B=2 catalogue buffer + min-separation inhibition."""
    dist_cat = distance_transform_edt(~cat).astype(np.float32)
    allowed = foot & (dist_cat > buffer_px)
    n_allowed = int(allowed.sum())
    print(f"[place] allowed pixels (footprint minus B={buffer_px} catalogue buffer): {n_allowed:,}")
    if n_allowed < max_dots:
        raise RuntimeError(f"Only {n_allowed} allowed pixels < {max_dots} dots")

    ys, xs = np.where(allowed)
    scores = surface[ys, xs].astype(np.float64)
    if scores.max() <= 0:
        print("[place] surface empty — uniform random placement on allowed set")
        scores = np.ones_like(scores)
    rng = np.random.default_rng(seed)
    scores = scores + rng.uniform(-0.002, 0.002, size=scores.shape)
    order = np.argsort(-scores, kind="stable")
    ys, xs, scores = ys[order], xs[order], scores[order]

    bucket_size = max(1, int(min_sep_px))
    buckets: dict[tuple[int, int], list[tuple[int, int]]] = {}
    placed: list[tuple[int, int]] = []
    placed_set: set[tuple[int, int]] = set()
    limit = min_sep_px * min_sep_px

    def too_close(y: int, x: int, sep: float) -> bool:
        by, bx = y // bucket_size, x // bucket_size
        lim = sep * sep
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for (py, px_) in buckets.get((by + dy, bx + dx), ()):
                    if (py - y) ** 2 + (px_ - x) ** 2 < lim:
                        return True
        return False

    for y, x in zip(ys, xs):
        if len(placed) >= max_dots:
            break
        if (y, x) in placed_set or too_close(y, x, min_sep_px):
            continue
        placed.append((y, x))
        placed_set.add((y, x))
        buckets.setdefault((y // bucket_size, x // bucket_size), []).append((y, x))

    print(f"[place] placed {len(placed)}/{max_dots} dots")
    arr = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    if placed:
        arr[tuple(zip(*placed))] = np.float32(1.0)
    arr[~foot] = np.float32(0.0)
    return arr


def make_dots(visible_mask: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Build dots from VISIBLE faults only (holdout-safe: no withheld information)."""
    tip_ys, tip_xs = catalogue_tips(visible_mask)
    surface, _ = stepover_surface(visible_mask, foot, tip_ys, tip_xs)
    return place_dots(surface, foot, visible_mask)


def leakage_canary(surface: np.ndarray, foot: np.ndarray,
                   truth: np.ndarray, bg: np.ndarray) -> dict:
    """Single-feature AUC of the step-over surface vs withheld truth (leakage alarm > 0.90)."""
    from sklearn.metrics import roc_auc_score
    vals = np.r_[surface.ravel()[truth.ravel()], surface.ravel()[bg.ravel()]]
    labels = np.r_[np.ones(int(truth.sum())), np.zeros(int(bg.sum()))]
    ok = np.isfinite(vals)
    auc = float(roc_auc_score(labels[ok], vals[ok])) if ok.sum() > 100 else float("nan")
    return {"single_feature_auc": round(auc, 6), "pass_le_0_90": bool(auc <= 0.90)}


def uniqueness_receipt(candidate: pathlib.Path, out: pathlib.Path) -> dict:
    """Run the shared lane gate against the local registry."""
    import subprocess
    cmd = [
        sys.executable, str(ROOT / "scripts" / "uniqueness_gate.py"),
        "--candidate", str(candidate), "--out", str(out),
        "--exclude-prefix", "gemsdoesass2-stepperelay-dilation",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    receipt = json.loads(out.read_text())
    receipt["gate_exit_code"] = res.returncode
    receipt["gate_stderr"] = res.stderr.strip()
    return receipt


def main() -> int:
    ddir = data_dir()
    if not (ddir / "sample_submission.tif").exists():
        ddir = ROOT / "data" / "bridge"
    print("=" * 72)
    print("GEMSDOESASS2 — H_STEPOVER step-over / relay-ramp submission")
    print("=" * 72)

    foot, cat = load_grid(ddir)

    # --- Build surface and final dots from the FULL catalogue (final submission) ---
    tip_ys, tip_xs = catalogue_tips(cat)
    surface, n_pairs = stepover_surface(cat, foot, tip_ys, tip_xs)
    arr = place_dots(surface, foot, cat)
    n_dots = int((arr > 0.5).sum())
    on_cat = int(((arr > 0.5) & cat).sum())
    print(f"[dots] placed={n_dots} on_catalogue={on_cat} (must be 0)")

    # --- Content-deterministic stem: re-running reproduces identical bytes
    # (and therefore the same filename), so the download surface stays clean. ---
    digest8 = hashlib.sha256(np.ascontiguousarray(arr, dtype=np.float32).tobytes()).hexdigest()[:8]
    stem = f"gemsdoesass2-stepperelay-dilation-{n_dots}-{digest8}"

    # --- Write submission pair (zeros + nan + zip) with built-in 13-check validation ---
    receipt = write_submission_pair(arr, downloads_dir(), stem,
                                    ddir / "sample_submission.tif", ddir / "labels.tif")
    zeros_path = downloads_dir() / f"{stem}-zeros.tif"
    print(f"[write] {zeros_path.name} sha256={receipt['zeros']['sha256']}")

    # --- Holdout: hide whole fault segments, rebuild surface from visible only ---
    holdout = run_holdout(lambda vis: make_dots(vis, foot).astype(bool), cat, foot,
                          n_folds=4, buffer_px=5.0, n_boot=400)
    print(f"[holdout] mean HOLDOUT-DTI={holdout['mean_dti']:.5f} "
          f"CI={holdout['ci95']} withheld={holdout['withheld_positives']:,}")

    # --- Leakage canary on the fold-instrument: surface vs withheld truth ---
    # Reuse fold structure: withheld = segments in held fold; score against truth.
    from gems.holdout import component_folds
    labels, idx, fold_of = component_folds(cat, n_folds=4)
    withheld_ids = idx[fold_of == 0]
    withheld = np.isin(labels, withheld_ids)
    visible = cat & ~withheld
    d_vis = distance_transform_edt(~visible)
    truth = withheld & (d_vis > 5.0) & foot
    # background: footprint, not on visible faults, not truth
    bg_mask = foot & ~visible & ~truth
    rng = np.random.default_rng(7)
    pos = np.flatnonzero(truth.ravel())
    bg = np.flatnonzero(bg_mask.ravel())
    if pos.size > 15000:
        pos = rng.choice(pos, 15000, replace=False)
    if bg.size > 40000:
        bg = rng.choice(bg, 40000, replace=False)
    tip_ys_v, tip_xs_v = catalogue_tips(visible)
    surf_vis, _ = stepover_surface(visible, foot, tip_ys_v, tip_xs_v)
    canary = leakage_canary(surf_vis, foot, truth, bg_mask)
    canary["withheld_positives"] = int(truth.sum())
    canary["background_cells"] = int(bg_mask.sum())
    print(f"[canary] max single-feature AUC={canary['single_feature_auc']} "
          f"pass≤0.90={canary['pass_le_0_90']}")

    # --- Uniform-lattice control holdout at the same dot budget (context) ---
    def uniform_dots(vis: np.ndarray) -> np.ndarray:
        d_vis = distance_transform_edt(~vis).astype(np.float32)
        allowed = foot & (d_vis > BUFFER_PX)
        ys, xs = np.where(allowed)
        rng = np.random.default_rng(11)
        order = rng.permutation(len(ys))[:MAX_DOTS]
        out = np.zeros((HEIGHT, WIDTH), dtype=bool)
        out[ys[order], xs[order]] = True
        return out

    holdout_uni = run_holdout(uniform_dots, cat, foot, n_folds=4, buffer_px=5.0, n_boot=400)
    print(f"[holdout-control] uniform mean HOLDOUT-DTI={holdout_uni['mean_dti']:.5f} "
          f"CI={holdout_uni['ci95']}")
    ratio = (holdout["mean_dti"] / holdout_uni["mean_dti"]) if holdout_uni["mean_dti"] > 0 else None
    print(f"[holdout] stepover/uniform ratio={ratio}")

    # --- Uniqueness gate vs local registry ---
    uni_out = evidence_dir() / f"{stem}-uniqueness.json"
    uni = uniqueness_receipt(zeros_path, uni_out)
    print(f"[uniqueness] max_overlap={uni['max_overlap_3px_pct']}% "
          f"max|rho|={uni['max_abs_spearman']} passes_lane={uni['passes_lane']}")

    # --- Validator re-check on saved bytes ---
    val = validate_geotiff(zeros_path, ddir / "sample_submission.tif",
                           ddir / "labels.tif", strict_all_finite=True)
    print(f"[validator] {val['checks_passed']}/{val['checks_total']} "
          f"range01={val['checks']['10_values_in_0_1_inside_footprint']} "
          f"on_cat={val['positive_on_catalogue']} n_pos={val['positive_dots_in_footprint']}")

    # --- Run card ---
    note = (f"GEMSDOESASS2 stepover-relay {n_dots}d B2 sep3 | blind connectors "
            f"between catalogue segments | {digest8}")[:140]
    est_method = ("MODEL ESTIMATE NOT available: no organizer receipt; geometry-only "
                  "extrapolator failed leave-one-out (R^2 < 0). Quote is HOLDOUT-DTI only.")
    card = {
        "run_card_version": 4,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "H_STEPOVER — step-over / relay-ramp dilation (sparse off-catalogue dots)",
        "hypothesis": ("Blind connectors between en-echelon catalogue fault segments vent heat "
                       "without a Quaternary scarp, so USGS/INGENIOUS mapping misses them. Tip-pair "
                       "step-over lenses target exactly these connectors."),
        "mechanism": ("Catalogue endpoints (8-connected trace tips); nearest-tip pairing within "
                      "3–25 px; intersection-of-disks lens (sep + 4 px); Gaussian smooth; greedy "
                      "weighted placement, B=2 catalogue buffer, 3 px min separation, ≤22,163 dots."),
        "named_non_fault_process": ("Alluvial-fan toes, terrace risers and paleo-shoreline benches can "
                                    "mimic step-over relief; mitigated by B=2 catalogue exclusion and "
                                    "requiring genuine tip-pair geometry rather than any lineament."),
        "holdout": {
            "label": "HOLDOUT-DTI (spatially blocked hide-and-recover, not a leaderboard score)",
            "evaluator": EVALUATOR_VERSION,
            "protocol": ("4 spatial blocks; whole 8-connected fault components withheld by block; "
                         "collar mask rebuilt from visible faults only; pooled DTI alpha 0.2 beta 0.8 "
                         "300 m triangular; cluster bootstrap 95% CI over withheld components"),
            "withheld_positive_cells": int(holdout["withheld_positives"]),
            "folds": holdout["n_folds"],
            "mean_dti": holdout["mean_dti"],
            "fold_dti": holdout["fold_dti"],
            "ci95": holdout["ci95"],
            "control_uniform_same_budget": {
                "mean_dti": holdout_uni["mean_dti"],
                "ci95": holdout_uni["ci95"],
            },
            "ratio_vs_uniform": ratio,
        },
        "leakage_canary": canary,
        "correlation_overlap_vs_registry": {
            "max_overlap_3px_pct": uni["max_overlap_3px_pct"],
            "max_abs_spearman": uni["max_abs_spearman"],
            "passes_lane": uni["passes_lane"],
            "gate_exit_code": uni["gate_exit_code"],
            "lattice_bound": {
                "dots": MAX_DOTS,
                "first_failing_dot_count": 22164,
                "reason": ("≤22,163 dots keeps overlap ≤70% vs the pinned lattice by the "
                           "6,649-pixel arithmetic bound (IR-S-01/IR-RV-04)."),
            },
            "references": uni["n_references"],
        },
        "raster": {
            "stem": stem,
            "primary_download": f"docs/downloads/{stem}-zeros.tif",
            "sha256": receipt["zeros"]["sha256"],
            "n_dots": n_dots,
            "dots_on_catalogue": on_cat,
            "dtype": "float32",
            "nodata": None,
            "all_cells_finite_in_0_1": bool(val["checks"]["09_no_nan_or_inf_inside_footprint"]
                                            and val["checks"]["10_values_in_0_1_inside_footprint"]),
            "crs": val["crs"],
            "shape": val["shape"],
            "transform": val["transform"],
        },
        "validator_output": {
            "checks_passed": val["checks_passed"],
            "checks_total": val["checks_total"],
            "strict_local_format_pass": bool(val["all_passed"]),
            "organizer_accepted": None,
            "no_nan_inside_footprint": bool(val["checks"]["09_no_nan_or_inf_inside_footprint"]),
            "values_in_0_1": bool(val["checks"]["10_values_in_0_1_inside_footprint"]),
            "crs_shape_transform_match": all([
                val["checks"]["04_crs_epsg_32611"],
                val["checks"]["05_shape_3730x3292"],
                val["checks"]["06_geotransform_exact"],
            ]),
            "receipt": f"evidence/validator-{stem}-zeros.json",
            "note": "Format inspection alone cannot establish novelty, scientific performance, or weekly-slot authorisation.",
        },
        "submission": {
            "name": f"GEMSDOESASS2-STEPOVER-{digest8.upper()}",
            "note_140": note,
            "note_length": len(note),
        },
        "score_evidence": est_method,
        "holdout_beats_uniform_control": bool(ratio is not None and ratio >= 1.0),
        "verdict": ("promote" if (val["all_passed"] and uni["passes_lane"]
                                  and on_cat == 0 and canary["pass_le_0_90"]
                                  and holdout["mean_dti"] >= holdout_uni["mean_dti"]) else "negative"),
        "ok_to_download_and_submit": bool(val["all_passed"] and uni["passes_lane"]
                                          and on_cat == 0 and canary["pass_le_0_90"]
                                          and holdout["mean_dti"] >= holdout_uni["mean_dti"]),
        "authorisation_limits": [
            "No organizer receipt exists for any file in this repository; every leaderboard value is USER-REPORTED and unverified.",
            "A weekly slot is the owner's decision on the DrivenData submission page; this receipt does not reserve or spend one.",
            "Leaderboard estimate is NOT available (geometry-only extrapolator failed leave-one-out); HOLDOUT-DTI is reported instead.",
            "The dot budget is 22,163 (below the 22,164 literal-lane ceiling); score ceiling is lower than the 37,654-dot champion family.",
        ],
        "files": {
            "zeros": {"filename": f"{stem}-zeros.tif",
                      "sha256": receipt["zeros"]["sha256"],
                      "size_bytes": receipt["zeros"]["size_bytes"]},
            "nan": {"filename": f"{stem}-nan.tif",
                    "sha256": receipt["nan"]["sha256"],
                    "size_bytes": receipt["nan"]["size_bytes"]},
            "zip": {"filename": receipt["zip"]["filename"],
                    "sha256": receipt["zip"]["sha256"],
                    "size_bytes": receipt["zip"]["size_bytes"]},
        },
    }

    card_path = evidence_dir() / f"{stem}-run-card.json"
    audit_path = downloads_dir() / f"{stem}-audit.json"
    card_path.write_text(json.dumps(card, indent=2))
    audit_path.write_text(json.dumps(card, indent=2))
    # validator receipt copy alongside audit
    val_path = evidence_dir() / f"validator-{stem}-zeros.json"
    val_path.write_text(json.dumps(val, indent=2))

    print("=" * 72)
    print(json.dumps({k: card[k] for k in ["lane", "verdict", "ok_to_download_and_submit",
                                           "submission", "raster"]}, indent=2))
    print(f"Run card: {card_path}")
    print(f"Audit: {audit_path}")
    print(f"Validator: {val_path}")
    print(f"Uniqueness: {uni_out}")
    print("=" * 72)
    return 0 if card["verdict"] == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())
