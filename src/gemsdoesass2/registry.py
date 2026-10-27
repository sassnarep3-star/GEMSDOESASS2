"""Pinned peer-raster retrieval and literal novelty checks.

The registry is evidence about the nine user-named public GitHub artifacts.  It
is *not* an organizer-owned registry and cannot establish global competition
uniqueness.  A candidate passes only relative to every successfully hash-checked
pinned entry; a missing entry fails closed.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

from .io import assert_same_grid, sha256_file, template_footprint

RANK_CORRELATION_LIMIT = 0.90
DOT_OVERLAP_LIMIT = 0.70
DEFAULT_RANK_SAMPLE_SIZE = 250_000


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text())
    if manifest.get("schema") != "gemsdoesass2-focus-registry-v1":
        raise ValueError("Unexpected focus registry schema")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Registry must contain at least one entry")
    return manifest


def _github_json(api_path: str) -> dict[str, Any]:
    request = Request(
        "https://api.github.com" + api_path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "GEMSDOESASS2-registry-audit"},
    )
    with urlopen(request, timeout=120) as response:  # noqa: S310 -- host is fixed above
        return json.load(response)


def fetch_entry(entry: dict[str, Any], destination: str | Path) -> Path:
    """Fetch one immutable Git blob and verify its full SHA-256."""

    destination = Path(destination)
    payload = _github_json(f"/repos/{entry['repository']}/git/blobs/{entry['git_blob_sha']}")
    if payload.get("encoding") != "base64":
        raise RuntimeError(f"{entry['id']}: GitHub blob response is not base64")
    data = base64.b64decode(payload["content"])
    actual = hashlib.sha256(data).hexdigest()
    if actual != entry["sha256"]:
        raise RuntimeError(f"{entry['id']}: SHA-256 mismatch ({actual} != {entry['sha256']})")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return destination


def fetch_registry(manifest_path: str | Path, destination_dir: str | Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    destination_dir = Path(destination_dir)
    receipt: dict[str, Any] = {"manifest": str(manifest_path), "entries": []}
    for entry in manifest["entries"]:
        target = destination_dir / entry["local_filename"]
        reused = target.is_file() and sha256_file(target) == entry["sha256"]
        if not reused:
            fetch_entry(entry, target)
        receipt["entries"].append(
            {
                "id": entry["id"],
                "path": str(target),
                "sha256": sha256_file(target),
                "reused_existing_verified_file": reused,
            }
        )
    receipt["pass"] = all(item["sha256"] == entry["sha256"] for item, entry in zip(receipt["entries"], manifest["entries"], strict=True))
    return receipt


def _pearson_correlation(left: np.ndarray, right: np.ndarray) -> float:
    """Pearson helper; Spearman is Pearson on tie-aware rank vectors."""

    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = np.sqrt(np.dot(left_centered, left_centered) * np.dot(right_centered, right_centered))
    if denominator == 0:
        return 0.0
    return float(np.dot(left_centered, right_centered) / denominator)


def rank_correlation(
    left: np.ndarray,
    right: np.ndarray,
    footprint: np.ndarray,
    *,
    sample_size: int = DEFAULT_RANK_SAMPLE_SIZE,
    seed: int = 20261027,
) -> tuple[float, str, int]:
    """Return absolute Spearman rank correlation with a documented deterministic mode."""

    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    footprint = np.asarray(footprint, dtype=bool)
    if left.shape != right.shape or left.shape != footprint.shape:
        raise ValueError("Rank comparison grids must be identical")
    valid = footprint & np.isfinite(left) & np.isfinite(right)
    indices = np.flatnonzero(valid.ravel())
    if len(indices) < 2:
        raise ValueError("At least two common finite footprint cells are required")
    left_values = left.ravel()[indices]
    right_values = right.ravel()[indices]
    left_binary = np.unique(left_values).size <= 2
    right_binary = np.unique(right_values).size <= 2
    if left_binary and right_binary:
        return abs(_pearson_correlation(left_values, right_values)), "exact_binary", len(indices)
    if len(indices) > sample_size:
        rng = np.random.default_rng(seed)
        indices = np.sort(rng.choice(indices, size=sample_size, replace=False))
        left_values = left.ravel()[indices]
        right_values = right.ravel()[indices]
        mode = "deterministic_sampled_spearman"
    else:
        mode = "exact_spearman"
    return abs(_pearson_correlation(rankdata(left_values, method="average"), rankdata(right_values, method="average"))), mode, len(indices)


def _read_registry_values(path: Path, template_path: Path) -> tuple[np.ndarray, np.ndarray]:
    assert_same_grid(template_path, path, left_name="template", right_name=f"registry raster {path.name}")
    with rasterio.open(path) as dataset:
        if dataset.count != 1:
            raise ValueError(f"Registry raster {path.name} is not single-band")
        values = dataset.read(1).astype(np.float32)
    return values, np.nan_to_num(values, nan=0.0) > 0.0


def _verified_entry_paths(manifest: dict[str, Any], registry_dir: Path) -> tuple[list[tuple[dict[str, Any], Path]], list[str]]:
    ready: list[tuple[dict[str, Any], Path]] = []
    missing: list[str] = []
    for entry in manifest["entries"]:
        path = registry_dir / entry["local_filename"]
        if not path.is_file() or sha256_file(path) != entry["sha256"]:
            missing.append(entry["id"])
        else:
            ready.append((entry, path))
    return ready, missing


def audit_surface(
    surface: np.ndarray,
    *,
    template_path: str | Path,
    manifest_path: str | Path,
    registry_dir: str | Path,
) -> dict[str, Any]:
    """Run the required pre-placement surface correlation check."""

    template_path = Path(template_path)
    manifest = load_manifest(manifest_path)
    footprint, _, _ = template_footprint(template_path)
    surface = np.asarray(surface, dtype=np.float32)
    if surface.shape != footprint.shape or not np.isfinite(surface[footprint]).all():
        raise ValueError("Surface must be aligned and finite inside the template footprint")
    ready, missing = _verified_entry_paths(manifest, Path(registry_dir))
    comparisons: list[dict[str, Any]] = []
    for entry, path in ready:
        peer_values, _ = _read_registry_values(path, template_path)
        correlation, mode, n_cells = rank_correlation(surface, peer_values, footprint)
        comparisons.append(
            {
                "id": entry["id"],
                "site": entry["site"],
                "file": entry["historical_file"],
                "surface_abs_rank_correlation": correlation,
                "surface_correlation_mode": mode,
                "surface_comparison_pixels": n_cells,
                "surface_pass": correlation <= RANK_CORRELATION_LIMIT,
            }
        )
    offenders = [item["id"] for item in comparisons if not item["surface_pass"]]
    return {
        "pass": not missing and not offenders,
        "verdict": "surface_pass" if not missing and not offenders else "duplicate_surface_or_incomplete_registry",
        "scope": "Nine pinned peer artifacts only; not global competition uniqueness.",
        "limit_abs_rank_correlation": RANK_CORRELATION_LIMIT,
        "max_abs_rank_correlation": max((item["surface_abs_rank_correlation"] for item in comparisons), default=None),
        "offenders": offenders,
        "missing_or_invalid_entries": missing,
        "comparisons": comparisons,
    }


def audit_final_dots(
    final_prediction: np.ndarray,
    *,
    template_path: str | Path,
    manifest_path: str | Path,
    registry_dir: str | Path,
) -> dict[str, Any]:
    """Run the required post-placement directed 3-pixel-overlap check."""

    template_path = Path(template_path)
    manifest = load_manifest(manifest_path)
    footprint, _, _ = template_footprint(template_path)
    final_prediction = np.asarray(final_prediction, dtype=np.float32)
    if final_prediction.shape != footprint.shape:
        raise ValueError("Final prediction and template footprint must share shape")
    if not np.isfinite(final_prediction).all() or np.any((final_prediction < 0) | (final_prediction > 1)):
        raise ValueError("Final prediction must be finite and in [0,1] everywhere")
    final_dots = (final_prediction > 0.0) & footprint
    if not final_dots.any():
        raise ValueError("A final-dot novelty audit needs at least one positive candidate cell")
    ready, missing = _verified_entry_paths(manifest, Path(registry_dir))
    comparisons: list[dict[str, Any]] = []
    for entry, path in ready:
        _, peer_dots = _read_registry_values(path, template_path)
        proximity = distance_transform_edt(~peer_dots)
        overlap = float((final_dots & (proximity <= 3.0)).sum() / final_dots.sum())
        comparisons.append(
            {
                "id": entry["id"],
                "site": entry["site"],
                "file": entry["historical_file"],
                "candidate_dot_count": int(final_dots.sum()),
                "peer_dot_count": int((peer_dots & footprint).sum()),
                "candidate_dot_overlap_within_3px": overlap,
                "dot_overlap_pass": overlap <= DOT_OVERLAP_LIMIT,
            }
        )
    offenders = [item["id"] for item in comparisons if not item["dot_overlap_pass"]]
    return {
        "pass": not missing and not offenders,
        "verdict": "final_dot_overlap_pass" if not missing and not offenders else "duplicate_final_dots_or_incomplete_registry",
        "scope": "Nine pinned peer artifacts only; not global competition uniqueness.",
        "limit_directed_dot_overlap_within_3px": DOT_OVERLAP_LIMIT,
        "max_directed_dot_overlap_within_3px": max((item["candidate_dot_overlap_within_3px"] for item in comparisons), default=None),
        "offenders": offenders,
        "missing_or_invalid_entries": missing,
        "comparisons": comparisons,
    }


def audit_novelty(
    surface: np.ndarray,
    final_prediction: np.ndarray,
    *,
    template_path: str | Path,
    manifest_path: str | Path,
    registry_dir: str | Path,
) -> dict[str, Any]:
    """Convenience aggregate of the pre-placement and post-placement audits."""

    surface_report = audit_surface(
        surface,
        template_path=template_path,
        manifest_path=manifest_path,
        registry_dir=registry_dir,
    )
    final_report = audit_final_dots(
        final_prediction,
        template_path=template_path,
        manifest_path=manifest_path,
        registry_dir=registry_dir,
    )
    return {
        "pass": bool(surface_report["pass"] and final_report["pass"]),
        "surface": surface_report,
        "final_dots": final_report,
        "max_abs_rank_correlation": surface_report["max_abs_rank_correlation"],
        "max_directed_dot_overlap_within_3px": final_report["max_directed_dot_overlap_within_3px"],
    }
