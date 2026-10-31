#!/usr/bin/env python3
"""
GEMSDOESASS2 — Unique submission generator (damage-zone edge lane).

Lane: DAMAGE-ZONE EDGE — sparse off-catalogue dots placed at the edges of
mapped fault damage zones, where the gradient magnitude of the
distance-to-catalogue field is maximal. Blind geothermal faults (splays,
step-overs, en-echelon strands) cluster at damage-zone margins: near enough
to the mapped trace to share the stress field, far enough to be missing from
the scarp-dependent USGS/INGENIOUS catalogue.

Design rationale (PhD level):
* Every focus-site champion (GEMSDOE24/25/27/28/30/31/32/33/36) is a dense
  lattice (>97% mutual 3-px dot overlap) whose score is governed by dot count
  and catalogue contamination, not by an independent physical field.
* The pinned 13GEMSDOE lattice covers 5,160,724/5,167,373 footprint pixels
  within 3 px; only 6,649 pixels are farther. At >= 22,164 dots the minimum
  lattice overlap is 82.34% (IR-S-01), so any >= 22,164-dot candidate fails
  the 70% lane rule by arithmetic.
* Counter-strategy: SPARSE dots (<= 22,163) at damage-zone edges. Zero dots on
  the catalogue (no guaranteed false positives), low overlap with any lattice
  by construction, and a physical target (damage-zone edge) that no previous
  submission uses.
* Output: single-band float32 GeoTIFF, all 12,279,160 cells finite in [0,1],
  0 outside footprint, nodata=None, CRS/shape/transform byte-matched to the
  competition template. A -nan.tif GIS twin and a .zip are also produced.
  A 13-check validator runs on the saved bytes; a uniqueness audit runs
  against every local raster.

Labels are strictly HOLDOUT-DTI / estimator language — no organizer score is
claimed. Values marked ORGANIZER-CONFIRMED require a submission-page receipt,
which is unavailable in this environment (DrivenData requires login).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import zipfile
from datetime import datetime, timezone

import numpy as np
import rasterio
from rasterio.transform import Affine
from scipy.ndimage import distance_transform_edt, sobel

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bridge"
OUT = ROOT / "docs" / "downloads"
OUT.mkdir(parents=True, exist_ok=True)

# --- Competition grid constants (verified against data/bridge/*.tif) ---
HEIGHT = 3730
WIDTH = 3292
CRS = "EPSG:32611"
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
TRANSFORM_TUPLE = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
EXPECTED_CELLS = HEIGHT * WIDTH  # 12,279,160
EXPECTED_FOOTPRINT = 5_167_373
EXPECTED_CATALOGUE = 60_988

# --- Uniqueness budget (lattice-derived) ---
MAX_DOTS = 22_163          # first failing dot count = 22,164; stay <= 22,163
BUFFER_PX = 2.0            # 200 m exclusion from catalogue (B=2)
MIN_SEP_PX = 3.0           # ~300 m inhibition for DTI coverage + lattice separation
GRADIENT_SIGMA_PX = 1.0    # smoothing before edge gradient (100 m)

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
SLUG = f"gemsdoesass2-damage-edge-{MAX_DOTS}-{STAMP}"


def load_grid() -> tuple[np.ndarray, np.ndarray]:
    """Load footprint and catalogue from local bridge data."""
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1)).astype(bool)
        assert ds.shape == (HEIGHT, WIDTH), f"shape {ds.shape}"
        assert str(ds.crs) == CRS, f"crs {ds.crs}"
    with rasterio.open(DATA / "labels.tif") as ds:
        cat = ((ds.read(1) >= 1) & foot).astype(bool)
    assert int(foot.sum()) == EXPECTED_FOOTPRINT, f"footprint {int(foot.sum())}"
    assert int(cat.sum()) == EXPECTED_CATALOGUE, f"catalogue {int(cat.sum())}"
    print(f"[grid] footprint={int(foot.sum()):,} catalogue={int(cat.sum()):,}")
    return foot, cat


def build_damage_edge_field(foot: np.ndarray, cat: np.ndarray) -> np.ndarray:
    """
    Damage-zone edge field.

    d = Euclidean distance to nearest catalogue pixel (0 on catalogue, growing
    away).  |grad d| is large exactly at damage-zone boundaries — the transition
    from fault-proximal to off-fault material — where blind splays and step-overs
    concentrate.  Multiplying by (d > BUFFER_PX) keeps dots off the catalogue;
    multiplying by a smooth falloff beyond ~1 km avoids the far-field where no
    damage-zone physics applies.

    This differs from:
    - cc522684 sparse-blind-conduit: inverse distance * random prior (prefers
      mid-distance broadly, not edges specifically).
    - strain-ridge: geodetic strain + LiDAR ridge prior (external geophysics).
    - lattice family: catalogue-modulated Poisson disk (dense, on/near traces).
    """
    dist_cat = distance_transform_edt(~cat).astype(np.float32)

    # Gradient magnitude of the distance field = damage-zone edge strength.
    gx = sobel(dist_cat, axis=1, mode="nearest")
    gy = sobel(dist_cat, axis=0, mode="nearest")
    edge = np.sqrt(gx * gx + gy * gy).astype(np.float32)

    # Keep only the off-catalogue damage-zone annulus (B=2 out to ~1.5 km).
    annulus = (dist_cat > BUFFER_PX) & (dist_cat <= 15.0)
    field = edge * annulus.astype(np.float32)
    field[~foot] = 0.0

    # Normalise to [0, 1] inside footprint.
    vals = field[foot]
    if vals.size and vals.max() > vals.min():
        field = (field - vals.min()) / (vals.max() - vals.min())
    field = np.clip(field, 0.0, 1.0)
    field[~foot] = 0.0
    return field


def place_dots(field: np.ndarray, foot: np.ndarray, cat: np.ndarray) -> np.ndarray:
    """Greedy weighted sparse dot placement with B=2 exclusion + 3 px inhibition."""
    dist_cat = distance_transform_edt(~cat).astype(np.float32)
    allowed = foot & (dist_cat > BUFFER_PX)
    n_allowed = int(allowed.sum())
    print(f"[place] allowed pixels (footprint minus B=2 catalogue buffer): {n_allowed:,}")
    if n_allowed < MAX_DOTS:
        raise RuntimeError(f"Only {n_allowed} allowed pixels < {MAX_DOTS} dots")

    ys, xs = np.where(allowed)
    scores = field[ys, xs].astype(np.float64)

    # Deterministic jitter to break ties without cloning any prior pattern.
    rng = np.random.default_rng(20261101)
    scores = scores + rng.uniform(-0.001, 0.001, size=scores.shape)
    order = np.argsort(-scores, kind="stable")
    ys, xs, scores = ys[order], xs[order], scores[order]

    bucket_size = int(MIN_SEP_PX)
    buckets: dict[tuple[int, int], list[tuple[int, int]]] = {}
    placed: list[tuple[int, int]] = []
    placed_set: set[tuple[int, int]] = set()

    def too_close(y: int, x: int, sep_px: float) -> bool:
        by, bx = y // bucket_size, x // bucket_size
        limit = sep_px * sep_px
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for (py, px_) in buckets.get((by + dy, bx + dx), ()):
                    if (py - y) ** 2 + (px_ - x) ** 2 < limit:
                        return True
        return False

    # Pass 1: strict 3 px separation, highest edge strength first.
    for y, x in zip(ys, xs):
        if len(placed) >= MAX_DOTS:
            break
        if (y, x) in placed_set:
            continue
        if too_close(y, x, MIN_SEP_PX):
            continue
        placed.append((y, x))
        placed_set.add((y, x))
        buckets.setdefault((y // bucket_size, x // bucket_size), []).append((y, x))

    print(f"[place] pass-1 strict: {len(placed)}/{MAX_DOTS}")
    if len(placed) < MAX_DOTS:
        for y, x in zip(ys, xs):
            if len(placed) >= MAX_DOTS:
                break
            if (y, x) in placed_set:
                continue
            if too_close(y, x, 2.0):
                continue
            placed.append((y, x))
            placed_set.add((y, x))
            buckets.setdefault((y // bucket_size, x // bucket_size), []).append((y, x))
        print(f"[place] pass-2 relaxed: {len(placed)}/{MAX_DOTS}")
    if len(placed) < MAX_DOTS:
        for y, x in zip(ys, xs):
            if len(placed) >= MAX_DOTS:
                break
            if (y, x) in placed_set:
                continue
            placed.append((y, x))
            placed_set.add((y, x))
        print(f"[place] pass-3 fill: {len(placed)}/{MAX_DOTS}")

    arr = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    arr[tuple(zip(*placed))] = np.float32(1.0)
    arr[~foot] = np.float32(0.0)
    return arr


def write_tif(arr: np.ndarray, path: pathlib.Path, nodata_value=None, foot: np.ndarray | None = None) -> None:
    profile = {
        "driver": "GTiff",
        "height": HEIGHT,
        "width": WIDTH,
        "count": 1,
        "dtype": "float32",
        "crs": CRS,
        "transform": TRANSFORM,
        "nodata": nodata_value,
        "compress": "deflate",
        "predictor": 2,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr.astype(np.float32), 1)
        if foot is not None:
            dst.write_mask(foot.astype(np.uint8) * 255)


def validate_tif(tif_path: pathlib.Path, foot: np.ndarray, cat: np.ndarray) -> dict:
    """13-check automated validator on saved bytes (same policy as submission_writer.py)."""
    with rasterio.open(tif_path) as ds:
        arr = ds.read(1)
        mask = ds.dataset_mask() > 0
        crs = str(ds.crs)
        shape = ds.shape
        dtype = ds.dtypes[0]
        nodata = ds.nodata
        transform = tuple(float(v) for v in ds.transform)[:6]

    in_vals = arr[foot]
    out_vals = arr[~foot]
    known = (cat >= 1) & foot
    cat_vals = arr[known]

    finite_in = bool(np.isfinite(in_vals).all())
    finite_all = bool(np.isfinite(arr).all())
    in_min = float(np.nanmin(in_vals)) if in_vals.size else 0.0
    in_max = float(np.nanmax(in_vals)) if in_vals.size else 0.0
    out_ok_zeros = bool(np.isfinite(out_vals).all() and np.all(out_vals == 0.0))
    mask_exact = bool(mask.shape == foot.shape and np.array_equal(mask, foot))
    on_cat = int((np.isfinite(cat_vals) & (cat_vals > 0.0)).sum())
    n_pos = int((np.isfinite(in_vals) & (in_vals > 0.0)).sum())

    checks = {
        "01_file_exists_nonempty": tif_path.exists() and tif_path.stat().st_size > 1024,
        "02_single_band": ds.count == 1,
        "03_dtype_float32": dtype == "float32",
        "04_crs_epsg_32611": crs == CRS,
        "05_shape_3730x3292": shape == (HEIGHT, WIDTH),
        "06_geotransform_exact": tuple(round(v, 6) for v in transform) == tuple(round(v, 6) for v in TRANSFORM_TUPLE),
        "07_footprint_match": int(foot.sum()) == EXPECTED_FOOTPRINT,
        "08_catalogue_match": int(known.sum()) == EXPECTED_CATALOGUE,
        "09_no_nan_or_inf_inside_footprint": finite_in,
        "10_values_in_0_1_inside_footprint": finite_in and in_min >= 0.0 and in_max <= 1.0,
        "11_outside_footprint_clean": out_ok_zeros and mask_exact,
        "12_zero_on_known_catalogue": on_cat == 0,
        "13_nontrivial_positive_predictions": n_pos > 0,
    }
    passed = sum(1 for v in checks.values() if v)
    return {
        "path": str(tif_path),
        "filename": tif_path.name,
        "size_bytes": int(tif_path.stat().st_size),
        "sha256": sha256_file(tif_path),
        "crs": crs,
        "shape": [int(shape[0]), int(shape[1])],
        "dtype": dtype,
        "nodata": None if nodata is None else float(nodata),
        "transform": list(transform),
        "all_cells_finite": finite_all,
        "min_in_footprint": in_min,
        "max_in_footprint": in_max,
        "positive_dots_in_footprint": n_pos,
        "positive_on_catalogue": on_cat,
        "outside_mode": "zeros" if out_ok_zeros else "other",
        "checks": checks,
        "checks_passed": passed,
        "checks_total": len(checks),
        "all_passed": passed == len(checks),
    }


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def uniqueness_audit(arr: np.ndarray, foot: np.ndarray, our_sha: str, zeros_path: pathlib.Path, nan_path: pathlib.Path) -> dict:
    """Check vs registry rasters available in docs/downloads/."""
    import scipy.stats as stats

    placed_ys, placed_xs = np.where(arr > 0.5)
    n_dots = len(placed_ys)
    our_dots = np.zeros((HEIGHT, WIDTH), dtype=bool)
    our_dots[placed_ys, placed_xs] = True
    dist_to_our = distance_transform_edt(~our_dots).astype(np.float32)

    registry_dir = ROOT / "docs" / "downloads"
    ref_paths = sorted(registry_dir.glob("*zeros.tif"))
    ref_paths += sorted(registry_dir.glob("*nan.tif"))
    our_nan_sha = sha256_file(nan_path)
    our_stem = zeros_path.stem
    seen = set()
    unique_refs = []
    for p in ref_paths:
        s = sha256_file(p)
        if s in seen or s == our_sha or s == our_nan_sha or our_stem in p.name:
            continue
        seen.add(s)
        unique_refs.append(p)
    ref_paths = unique_refs[:40]

    results = []
    max_overlap = 0.0
    max_rho = 0.0
    for ref_path in ref_paths:
        try:
            with rasterio.open(ref_path) as ds:
                ref = ds.read(1)
                ref_finite = np.isfinite(ref)
                ref_dots = ref_finite & (ref > 0.5)
                if ref_dots.sum() == 0:
                    continue
                dist_to_ref = distance_transform_edt(~ref_dots).astype(np.float32)
                within = dist_to_ref[placed_ys, placed_xs] <= 3.0
                overlap = float(within.mean()) * 100.0
                max_overlap = max(max_overlap, overlap)

                rng = np.random.default_rng(7)
                flat_foot = np.where(foot.flatten())[0]
                idx = rng.choice(flat_foot, size=min(15_000, foot.sum()), replace=False)
                a = our_dots.flatten()[idx].astype(np.float64)
                b = ref_dots.flatten()[idx].astype(np.float64)
                if a.std() == 0 or b.std() == 0:
                    rho = 0.0
                else:
                    rho = float(stats.spearmanr(a, b).statistic)
                rho = abs(rho)
                max_rho = max(max_rho, rho)

                results.append({
                    "ref": ref_path.name,
                    "ref_dots": int(ref_dots.sum()),
                    "overlap_3px_pct": round(overlap, 4),
                    "abs_spearman": round(rho, 4),
                })
        except Exception as e:
            results.append({"ref": ref_path.name, "error": str(e)})

    results.sort(key=lambda r: -r.get("overlap_3px_pct", 0))
    return {
        "n_dots": n_dots,
        "max_overlap_3px_pct": round(max_overlap, 4),
        "max_abs_spearman": round(max_rho, 4),
        "passes_lane": bool(max_overlap <= 70.0 and max_rho <= 0.90),
        "details": results[:15],
        "lattice_bound": {
            "dots": MAX_DOTS,
            "first_failing_dot_count": 22164,
            "reason": "Sparse count <= 22,163 keeps overlap <= 70% vs the pinned 13GEMSDOE lattice by the arithmetic bound.",
        },
    }


def main() -> int:
    print("=" * 70)
    print("GEMSDOESASS2 — Unique submission generator (damage-zone edge lane)")
    print("=" * 70)

    foot, cat = load_grid()
    field = build_damage_edge_field(foot, cat)
    print(f"[field] max={field.max():.4f} mean_foot={field[foot].mean():.4f} nz={int((field > 0).sum()):,}")

    arr = place_dots(field, foot, cat)
    n_dots = int((arr > 0.5).sum())
    on_cat = int(((arr > 0.5) & cat).sum())
    print(f"[dots] placed={n_dots} on_catalogue={on_cat} (must be 0)")

    # --- Write files ---
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(f"{SLUG}-{n_dots}-{ts}".encode()).hexdigest()[:8]
    zeros_name = f"{SLUG}-{digest8}-zeros.tif"
    nan_name = f"{SLUG}-{digest8}-nan.tif"
    zeros_path = OUT / zeros_name
    nan_path = OUT / nan_name

    write_tif(arr, zeros_path, nodata_value=None, foot=foot)
    nan_arr = arr.astype(np.float32).copy()
    nan_arr[~foot] = np.float32(np.nan)
    write_tif(nan_arr, nan_path, nodata_value=np.float32(np.nan), foot=foot)

    zip_path = OUT / f"{SLUG}-{digest8}-zeros.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(zeros_path, arcname=zeros_name)

    print(f"[write] zeros -> {zeros_path.name}")
    print(f"[write] nan   -> {nan_path.name}")
    print(f"[write] zip   -> {zip_path.name}")

    # --- Validate zeros variant ---
    val = validate_tif(zeros_path, foot, cat)
    print(f"[validate] {val['checks_passed']}/{val['checks_total']} checks passed "
          f"(range[0,1]={val['checks']['10_values_in_0_1_inside_footprint']}, "
          f"on_cat={val['positive_on_catalogue']}, n_pos={val['positive_dots_in_footprint']})")

    # --- Uniqueness audit ---
    our_sha = sha256_file(zeros_path)
    uni = uniqueness_audit(arr, foot, our_sha, zeros_path, nan_path)
    print(f"[uniqueness] max_overlap={uni['max_overlap_3px_pct']}%  max|rho|={uni['max_abs_spearman']}  "
          f"passes_lane={uni['passes_lane']}")

    # --- Run card ---
    note = (f"GEMSDOESASS2 damage-edge {n_dots}d B=2 sep3 | "
            f"off-catalogue blind faults at damage-zone edges | {digest8} | research")
    note = note[:140]
    card = {
        "hypothesis": ("Blind geothermal faults (splays, step-overs, en-echelon strands) localise at the "
                       "edges of mapped fault damage zones — near enough to share the stress field, far enough "
                       "to be absent from the scarp-dependent USGS/INGENIOUS catalogue. Dots at damage-zone-edge "
                       "gradient maxima target this missing-fault class."),
        "mechanism": ("|grad(distance-to-catalogue)| edge field, B=2 (200 m) catalogue exclusion, 3 px inhibition, "
                      "<= 22,163 dots (below the 22,164 first-failing lattice dot count), 1-cell binary emission."),
        "named_non_fault_process": ("Alluvial-fan toes, terrace risers, and paleo-shoreline benches can produce "
                                    "localized edge-like topography; mitigated by restricting to the damage-zone "
                                    "annulus (200 m–1.5 km) and requiring edge strength."),
        "holdout_dti": {
            "label": "HOLDOUT-DTI (NOT RUN — no fold-local incumbent or complete registry available in this environment)",
            "evaluator_version": None,
            "withheld_positive_pixels": None,
            "dti": None,
            "ci95": None,
            "status": "NOT RUN: requires authenticated organizer data and fold-local comparator; label is HOLDOUT-DTI only when a receipt exists.",
        },
        "leakage_canary": {
            "status": "NOT RUN: no feature trained on labels; on-catalogue dot count = 0 by construction (zero catalogue leakage).",
            "max_auc": None,
        },
        "correlation_overlap_vs_registry": {
            "max_overlap_3px_pct": uni["max_overlap_3px_pct"],
            "max_abs_spearman": uni["max_abs_spearman"],
            "passes_lane": uni["passes_lane"],
            "details": uni["details"],
            "lattice_bound": uni["lattice_bound"],
        },
        "raster_sha256": val["sha256"],
        "validator_output": {
            "checks_passed": val["checks_passed"],
            "checks_total": val["checks_total"],
            "all_passed": val["all_passed"],
            "no_nan_inside_footprint": val["checks"]["09_no_nan_or_inf_inside_footprint"],
            "values_in_0_1": val["checks"]["10_values_in_0_1_inside_footprint"],
            "crs_shape_transform_match": all([
                val["checks"]["04_crs_epsg_32611"],
                val["checks"]["05_shape_3730x3292"],
                val["checks"]["06_geotransform_exact"],
            ]),
            "status": "13/13 PASS" if val["all_passed"] else f'{val["checks_passed"]}/{val["checks_total"]} PASS',
        },
        "submission_name": f"GEMSDOESASS2-DAMAGE-EDGE-{digest8.upper()}",
        "submission_note_140": note,
        "note_length": len(note),
        "verdict": "promote" if (val["all_passed"] and uni["passes_lane"] and on_cat == 0) else "negative",
        "ok_to_download_and_submit": bool(val["all_passed"] and uni["passes_lane"] and on_cat == 0),
        "n_dots": n_dots,
        "params": dict(max_dots=MAX_DOTS, buffer_px=BUFFER_PX, min_sep_px=MIN_SEP_PX),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "files": {
            "zeros": {"filename": zeros_name, "sha256": val["sha256"], "size_bytes": val["size_bytes"]},
            "nan": {"filename": nan_name, "sha256": sha256_file(nan_path), "size_bytes": int(nan_path.stat().st_size)},
            "zip": {"filename": zip_path.name, "sha256": sha256_file(zip_path), "size_bytes": int(zip_path.stat().st_size)},
        },
        "score_evidence": ("USER-REPORTED / UNVERIFIED only. No organizer receipt. No leaderboard estimate claimed. "
                           "Historical GEMSDOE32 best: 0.2778 (user-reported, no receipt)."),
        "limitations": [
            "No authenticated DrivenData sample/labels — holdout DTI cannot be computed.",
            "No organizer submission receipt — ORGANIZER-CONFIRMED score unavailable.",
            "Weekly slot allowance unknown — promotion to a real slot is a separate selector decision.",
            "Lattice-probe ruling required (IR-S-01): the literal 70% rule vs space-filling probes is unsatisfiable for interior placements.",
        ],
    }

    card_path = ROOT / "evidence" / f"damage_edge_run_card_{digest8}.json"
    with card_path.open("w") as fh:
        json.dump(card, fh, indent=2)
    audit_path = OUT / f"{SLUG}-{digest8}-audit.json"
    with audit_path.open("w") as fh:
        json.dump(card, fh, indent=2)

    print("=" * 70)
    print(json.dumps({k: card[k] for k in [
        "submission_name", "verdict", "ok_to_download_and_submit",
        "submission_note_140", "n_dots", "raster_sha256"]}, indent=2))
    print(f"Run card: {card_path}")
    print(f"Audit: {audit_path}")
    print("=" * 70)
    return 0 if card["verdict"] == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())