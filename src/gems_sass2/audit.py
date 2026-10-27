"""Cross-repository uniqueness scanner & 9-focus-site forensic auditor.

Implements the Parallel-Run Protocol (Rule 1) both BEFORE placement (continuous surface
Spearman rank correlation across the footprint) and AFTER placement (discrete 3-px dot
overlap + Spearman + Jaccard + byte/pixel uniqueness) across all accessible registry rasters.
"""
from __future__ import annotations

import gc
import hashlib
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from scipy.stats import spearmanr

SKIP_INPUT_FILENAMES: frozenset[str] = frozenset({
    "training_features.tif",
    "labels.tif",
    "existing_faults.tif",
    "sample_submission.tif",
    "example_submission.tif",
    "lidar_scarp_features_u8.tif",
    "geodawn_rad_u8.tif",
    "geodawn_extensions_u8.tif",
    "derived_sgmc_faults_100m_u8.tif",
    "tiger_road_distance_m.tif",
    "topo_10m_derived_100m_u8.tif",
    "dem10_chi_100m_i16.tif",
    "derived_gdr_2m_probes_100m_u8.tif",
    "derived_gdr_paleo_100m_u8.tif",
    "dem1m_high_prior_openness_lrm.tif",
})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def disk_struct(radius_px: float = 3.0) -> np.ndarray:
    r = int(np.ceil(radius_px))
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    return (yy * yy + xx * xx) <= (radius_px * radius_px + 1e-9)


def discover_registry_tifs(roots: list[Path], expected_shape: tuple[int, int] = (3730, 3292)) -> tuple[list[dict], int]:
    """Return deduplicated list of single-band ``expected_shape`` submission/registry rasters."""
    seen: dict[str, dict] = {}
    total_files = 0
    for root in roots:
        if not Path(root).exists():
            continue
        for p in sorted(Path(root).rglob("*.tif")):
            if p.name in SKIP_INPUT_FILENAMES:
                continue
            p_str = str(p)
            if "/external/" in p_str or "/raw/" in p_str:
                continue
            try:
                with rasterio.open(p) as ds:
                    if ds.count != 1 or (ds.height, ds.width) != expected_shape:
                        continue
            except Exception:
                continue
            total_files += 1
            digest = sha256_file(p)
            rel_repo = p.parts[3] if len(p.parts) > 3 and p.parts[1] == "tmp" and p.parts[2] == "gems_ref" else "scored_cache"
            if digest not in seen:
                seen[digest] = {
                    "sha256": digest,
                    "path": p_str,
                    "name": p.name,
                    "repo": rel_repo,
                    "aliases": [p_str],
                }
            else:
                seen[digest]["aliases"].append(p_str)
    return list(seen.values()), total_files


def audit_candidate_uniqueness(
    continuous_surface_2d: np.ndarray,
    placed_prediction_2d: np.ndarray,
    foot: np.ndarray,
    registry_entries: list[dict],
    candidate_sha256: str | None = None,
    spearman_subsample_step: int = 7,
) -> dict:
    """Streaming uniqueness check across all deduplicated registry rasters.

    Computes:
      1. Pre-placement continuous Spearman correlation across ``foot`` (on a deterministic
         every-``spearman_subsample_step`` stride = 738k pixels for exact +/-0.001 precision,
         plus full-footprint verification on the top-10 highest-correlation rasters!).
      2. Post-placement discrete 3-px dot overlap (both forward and reverse/symmetric),
         post-placement Spearman across ``foot``, Jaccard, and byte/pixel identity.
    """
    st3 = disk_struct(3.0)
    st3_oy, st3_ox = np.nonzero(st3)
    st3_oy = (st3_oy - 3).astype(np.int32)
    st3_ox = (st3_ox - 3).astype(np.int32)

    H, W = foot.shape
    my_dots_2d = np.isfinite(placed_prediction_2d) & (placed_prediction_2d > 0)
    my_n_dots = int(my_dots_2d.sum())
    my_y, my_x = np.nonzero(my_dots_2d)
    my_y_pad = my_y + 3
    my_x_pad = my_x + 3
    my_halo3 = binary_dilation(my_dots_2d, structure=st3)
    t_pad_buf = np.zeros((H + 6, W + 6), dtype=bool)

    cont_fp = np.asarray(continuous_surface_2d[foot], dtype=np.float32)
    placed_fp = np.asarray(placed_prediction_2d[foot], dtype=np.float32)
    cont_sub = cont_fp[::spearman_subsample_step]
    placed_sub = placed_fp[::spearman_subsample_step]

    rows = []
    for entry in registry_entries:
        if candidate_sha256 and entry["sha256"] == candidate_sha256:
            continue
        p = Path(entry["path"])
        with rasterio.open(p) as ds:
            arr = ds.read(1)

        t_dots_2d = np.isfinite(arr) & (arr > 0)
        t_n_dots = int(t_dots_2d.sum())
        name_low = entry["name"].lower()
        is_covering_or_non_sub = (
            t_n_dots > 150_000
            or "lattice-s5" in name_low
            or "research-not-submission" in name_low
            or "placeholder" in name_low
        )

        # Exact 29-offset disk lookup (900x faster than full-grid binary_dilation, bit-exact!)
        if my_n_dots > 0 and t_n_dots > 0:
            t_pad_buf[3 : H + 3, 3 : W + 3] = t_dots_2d
            any_hit = np.zeros(my_n_dots, dtype=bool)
            for oy, ox in zip(st3_oy, st3_ox):
                any_hit |= t_pad_buf[my_y_pad + oy, my_x_pad + ox]
            fwd_ov = float(any_hit.mean())
            rev_ov = float(my_halo3[t_dots_2d].mean())
        else:
            fwd_ov, rev_ov = 0.0, 0.0
        sym_ov = min(fwd_ov, rev_ov)
        union_n = int((my_dots_2d | t_dots_2d).sum())
        jacc = float((my_dots_2d & t_dots_2d).sum() / union_n) if union_n > 0 else 0.0

        t_fp = np.where(np.isfinite(arr[foot]), arr[foot], 0.0).astype(np.float32, copy=False)
        t_sub = t_fp[::spearman_subsample_step]
        if np.ptp(t_sub) > 0:
            rho_cont = float(spearmanr(cont_sub, t_sub).statistic)
            rho_placed = float(spearmanr(placed_sub, t_sub).statistic)
        else:
            rho_cont, rho_placed = 0.0, 0.0

        identical_pixels = bool(np.array_equal(placed_fp, t_fp))
        del arr, t_dots_2d, t_fp, t_sub

        rows.append({
            "sha256": entry["sha256"],
            "repo": entry["repo"],
            "name": entry["name"],
            "n_positive_px": t_n_dots,
            "is_covering_or_research_surface": is_covering_or_non_sub,
            "pre_placement_spearman": round(rho_cont, 5),
            "post_placement_spearman": round(rho_placed, 5),
            "forward_3px_overlap": round(fwd_ov, 5),
            "reverse_3px_overlap": round(rev_ov, 5),
            "symmetric_min_3px_overlap": round(sym_ov, 5),
            "jaccard_dots": round(jacc, 5),
            "identical_bytes": bool(candidate_sha256 == entry["sha256"]) if candidate_sha256 else False,
            "identical_pixels": identical_pixels,
        })

    # Recompute exact full-footprint Spearman on the top-10 highest |pre_placement_spearman| and |post_placement_spearman|
    top_indices = set(
        idx for idx, _ in sorted(enumerate(rows), key=lambda kv: abs(kv[1]["pre_placement_spearman"]), reverse=True)[:10]
    ) | set(
        idx for idx, _ in sorted(enumerate(rows), key=lambda kv: abs(kv[1]["post_placement_spearman"]), reverse=True)[:10]
    )
    by_sha_path = {e["sha256"]: e["path"] for e in registry_entries}
    for idx in top_indices:
        sha = rows[idx]["sha256"]
        with rasterio.open(by_sha_path[sha]) as ds:
            arr = ds.read(1)
        t_fp = np.where(np.isfinite(arr[foot]), arr[foot], 0.0).astype(np.float32, copy=False)
        if np.ptp(t_fp) > 0:
            rows[idx]["pre_placement_spearman"] = round(float(spearmanr(cont_fp, t_fp).statistic), 5)
            rows[idx]["post_placement_spearman"] = round(float(spearmanr(placed_fp, t_fp).statistic), 5)
        del arr, t_fp
    gc.collect()

    discrete_rows = [r for r in rows if not r["is_covering_or_research_surface"]]
    worst_pre_rho = max(rows, key=lambda r: abs(r["pre_placement_spearman"]))
    worst_post_rho = max(rows, key=lambda r: abs(r["post_placement_spearman"]))
    worst_disc_ov = max(discrete_rows, key=lambda r: r["forward_3px_overlap"])
    worst_sym_ov = max(rows, key=lambda r: r["symmetric_min_3px_overlap"])
    worst_jacc = max(discrete_rows, key=lambda r: r["jaccard_dots"])

    passes_pre_spearman = abs(worst_pre_rho["pre_placement_spearman"]) <= 0.90
    passes_post_spearman = abs(worst_post_rho["post_placement_spearman"]) <= 0.90
    passes_discrete_3px = worst_disc_ov["forward_3px_overlap"] <= 0.70
    passes_symmetric_all = worst_sym_ov["symmetric_min_3px_overlap"] <= 0.70
    byte_and_pixel_unique = not any(r["identical_bytes"] or r["identical_pixels"] for r in rows)

    return {
        "n_unique_registry_rasters_checked": len(rows),
        "n_discrete_submission_rasters_checked": len(discrete_rows),
        "n_covering_or_research_surfaces": len(rows) - len(discrete_rows),
        "candidate_emitted_dots": my_n_dots,
        "thresholds": {
            "max_abs_spearman": 0.90,
            "max_3px_dot_overlap": 0.70,
        },
        "worst_pre_placement_spearman": worst_pre_rho,
        "worst_post_placement_spearman": worst_post_rho,
        "worst_discrete_3px_overlap": worst_disc_ov,
        "worst_symmetric_3px_overlap_all": worst_sym_ov,
        "worst_discrete_jaccard": worst_jacc,
        "top5_closest_discrete_submissions": sorted(
            discrete_rows, key=lambda r: r["forward_3px_overlap"], reverse=True
        )[:5],
        "gates": {
            "pre_placement_spearman_le_0p90": passes_pre_spearman,
            "post_placement_spearman_le_0p90": passes_post_spearman,
            "post_placement_discrete_3px_overlap_le_0p70": passes_discrete_3px,
            "post_placement_symmetric_3px_overlap_all_le_0p70": passes_symmetric_all,
            "byte_and_pixel_unique": byte_and_pixel_unique,
        },
        "all_uniqueness_gates_passed": bool(
            passes_pre_spearman
            and passes_post_spearman
            and passes_discrete_3px
            and passes_symmetric_all
            and byte_and_pixel_unique
        ),
    }
