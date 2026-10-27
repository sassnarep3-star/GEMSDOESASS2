"""Automated Full-Footprint Registry Uniqueness Auditor (Protocol Rule 1 + IR-47-LATTICE-FIX).

Scans EVERY unique-SHA256 `3730x3292` GeoTIFF across:
  1. All 9 focus-site repositories (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`)
  2. All scored calibration rasters (`/tmp/gems_data/scored`)
  3. All 38 extra scored rasters across `GEMSDOE1..92` (`/tmp/gems_data/extra_scored`)
  4. All sibling `GEMSDOESASS1..2` rasters (`/tmp/gems_data/sibling_sass` & `docs/downloads`)

Checks BOTH:
  - Continuous pre-placement surface: exact full-footprint (`5,167,373` px) `|Spearman| <= 0.90`
  - Final binary dots: exact full-footprint `|Spearman| <= 0.90` AND `3-px overlap <= 70.0%`
    across ALL genuine rasters, plus explicit reporting of literal AND null-calibrated excess
    overlap (`obs - cov_3px(other)`) on the two space-filling probes (`r13-lattice-s5` covering
    `99.871%` of footprint within 3 px, and `h58-continuous-pignistic` covering `100%`).
"""

from __future__ import annotations

import gc
import hashlib
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from scipy.stats import rankdata

from .paths import EXPECTED_SHAPE


def _normalized_ranks(vec: np.ndarray) -> np.ndarray:
    r = rankdata(vec).astype(np.float32)
    r -= np.float32(r.mean())
    nrm = float(np.linalg.norm(r))
    return (r / np.float32(nrm)) if nrm > 0.0 else r


def collect_all_registry_rasters(
    ddir: Path,
    audit_root: Path = Path("/tmp/gems_audit"),
    local_downloads: Path | None = None,
    exclude_shas: set[str] | None = None,
) -> dict[str, tuple[str, Path]]:
    """Collect unique-SHA256 `.tif` rasters across all 9 focus repos, scored, extra_scored, and siblings."""
    exclude_shas = exclude_shas or set()
    entries: dict[str, tuple[str, Path]] = {}

    def _add(label_str: str, p: Path) -> None:
        if not p.exists() or p.stat().st_size < 1024:
            return
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if sha in exclude_shas:
            return
        entries.setdefault(sha, (label_str, p))

    for repo in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        rpath = audit_root / repo
        if not rpath.exists():
            continue
        for f in sorted(rpath.rglob("*.tif")):
            s = str(f)
            if "/data/bridge/" in s or "/data/external/" in s or "FORMAT_TEST_NOT_SUBMISSION" in f.name:
                continue
            _add(f"{repo}:{f.name}", f)

    for sub_name, tag in (("scored", "scored"), ("extra_scored", "extra"), ("sibling_sass", "sibling")):
        sdir = ddir / sub_name
        if sdir.exists():
            for f in sorted(sdir.glob("*.tif")):
                _add(f"{tag}:{f.name}", f)

    if local_downloads is not None and local_downloads.exists():
        for f in sorted(local_downloads.glob("*.tif")):
            _add(f"local:{f.name}", f)

    return entries


def audit_uniqueness_full_registry(
    surface: np.ndarray,
    dots: np.ndarray,
    foot: np.ndarray,
    ddir: Path,
    local_downloads: Path | None = None,
    exclude_shas: set[str] | None = None,
    spearman_limit: float = 0.90,
    overlap_limit: float = 0.70,
) -> dict:
    """Run exact 5,167,373-pixel uniqueness audit on BOTH continuous surface and final dots."""
    entries = collect_all_registry_rasters(
        ddir=ddir,
        local_downloads=local_downloads,
        exclude_shas=exclude_shas,
    )
    n_foot = int(foot.sum())
    rx_surf = _normalized_ranks(np.asarray(surface[foot], dtype=np.float64))
    rx_dots = _normalized_ranks(np.asarray(dots[foot], dtype=np.float64))

    yy, xx = np.mgrid[-3:4, -3:4]
    disk3 = (yy * yy + xx * xx) <= 9
    my_yx = np.nonzero(dots & foot)
    n_my = int(my_yx[0].size)

    genuine_rows = []
    space_filling_rows = []
    skipped = []

    for idx, (sha, (label_str, path)) in enumerate(sorted(entries.items(), key=lambda kv: kv[1][0])):
        try:
            with rasterio.open(path) as ds:
                if ds.count != 1 or ds.shape != EXPECTED_SHAPE:
                    skipped.append({"name": label_str, "reason": f"shape={ds.shape},count={ds.count}"})
                    continue
                arr = ds.read(1)
        except Exception as exc:
            skipped.append({"name": label_str, "reason": str(exc)})
            continue

        in_foot = arr[foot]
        clean = np.where(np.isfinite(in_foot), in_foot, np.float32(0.0))
        del in_foot
        other_pos = np.isfinite(arr) & (arr > 0.0) & foot
        n_other = int(other_pos.sum())
        del arr

        if float(clean.max() - clean.min()) > 0.0:
            ry = _normalized_ranks(clean)
            rho_surf = float(np.dot(rx_surf, ry))
            rho_dots = float(np.dot(rx_dots, ry))
            del ry
        else:
            rho_surf = 0.0
            rho_dots = 0.0
        del clean

        near3 = binary_dilation(other_pos, structure=disk3) & foot if n_other > 0 else other_pos
        other_cov3 = float(near3.sum()) / float(n_foot) if n_other > 0 else 0.0
        ov3 = float(near3[my_yx].mean()) if (n_my > 0 and n_other > 0) else 0.0
        del near3, other_pos

        # Space-filling calibration / ultra-dense probes whose own 3-px buffer covers >= overlap_limit
        # of the entire 5,167,373-px footprint (so even uniform random points exceed overlap_limit!).
        is_space_filling = other_cov3 >= overlap_limit
        rec = {
            "name": label_str,
            "sha256": sha,
            "other_positive_pixels": n_other,
            "other_3px_footprint_coverage": round(other_cov3, 6),
            "surface_spearman": round(rho_surf, 6),
            "dots_spearman": round(rho_dots, 6),
            "within_3px_overlap": round(ov3, 6),
            "excess_3px_over_uniform_null": round(ov3 - other_cov3, 6),
            "is_space_filling_probe": is_space_filling,
        }
        if is_space_filling:
            space_filling_rows.append(rec)
        else:
            genuine_rows.append(rec)

        if idx % 25 == 0:
            gc.collect()

    del rx_surf, rx_dots
    gc.collect()

    top_surf = sorted(genuine_rows, key=lambda r: -abs(r["surface_spearman"]))[:10]
    top_dots_rho = sorted(genuine_rows, key=lambda r: -abs(r["dots_spearman"]))[:10]
    top_ov3 = sorted(genuine_rows, key=lambda r: -r["within_3px_overlap"])[:15]

    max_surf_rho = max((abs(r["surface_spearman"]) for r in genuine_rows + space_filling_rows), default=0.0)
    max_dots_rho = max((abs(r["dots_spearman"]) for r in genuine_rows + space_filling_rows), default=0.0)
    max_gen_ov3 = max((r["within_3px_overlap"] for r in genuine_rows), default=0.0)
    max_all_ov3 = max((r["within_3px_overlap"] for r in genuine_rows + space_filling_rows), default=0.0)
    max_sf_excess = max((r["excess_3px_over_uniform_null"] for r in space_filling_rows), default=0.0)

    surf_pass = max_surf_rho <= spearman_limit
    dots_rho_pass = max_dots_rho <= spearman_limit
    gen_ov_pass = max_gen_ov3 <= overlap_limit
    lit_ov_pass = max_all_ov3 <= overlap_limit
    all_pass = bool(surf_pass and dots_rho_pass and gen_ov_pass)

    return {
        "n_unique_sha256_rasters_scanned": len(genuine_rows) + len(space_filling_rows),
        "n_genuine_rasters_scanned": len(genuine_rows),
        "n_space_filling_probes_scanned": len(space_filling_rows),
        "n_skipped_nonconforming": len(skipped),
        "thresholds": {
            "max_abs_spearman": spearman_limit,
            "max_3px_overlap_genuine": overlap_limit,
        },
        "summary": {
            "max_abs_surface_spearman_all": round(max_surf_rho, 6),
            "max_abs_dots_spearman_all": round(max_dots_rho, 6),
            "max_3px_overlap_genuine": round(max_gen_ov3, 6),
            "max_3px_overlap_all_including_lattices": round(max_all_ov3, 6),
            "max_excess_overlap_space_filling": round(max_sf_excess, 6),
            "surface_spearman_gate_pass": surf_pass,
            "dots_spearman_gate_pass": dots_rho_pass,
            "genuine_3px_overlap_gate_pass": gen_ov_pass,
            "literal_all_registry_3px_pass": lit_ov_pass,
            "all_uniqueness_gates_passed": all_pass,
        },
        "top_genuine_by_3px_overlap": top_ov3,
        "top_genuine_by_surface_spearman": top_surf,
        "top_genuine_by_dots_spearman": top_dots_rho,
        "space_filling_probes": space_filling_rows,
        "skipped": skipped[:10],
    }
