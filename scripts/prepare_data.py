#!/usr/bin/env python3
"""Restore the shared template's hash-pinned feature cache, without approving a submission.

The source is an owner-hosted mirror, not an authenticated DrivenData download.
Large rasters and cached bands stay in ignored data/official and .cache. Use
--fetch --cache-bands to restore them; the default only verifies placed inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def load_shared_template(root: Path):
    source = root / "vendor/template57/prepare_data.py"
    manifest = json.loads((root / "vendor/PROVENANCE.json").read_text())
    expected = manifest["files"]["vendor/template57/prepare_data.py"]
    if not source.is_file() or digest(source) != expected:
        raise ValueError("Shared cache builder does not match its pinned source hash")
    spec = importlib.util.spec_from_file_location("gems57_shared_prepare", source)
    if spec is None or spec.loader is None:
        raise ValueError("Could not load the shared cache builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_or_link(root: Path, name: str, expected: str) -> Path:
    """Preserve existing files: a wrong or broken reference is never overwritten."""
    target = root / "data/official" / name
    bridge = root / "data/bridge" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not target.is_file() or digest(target) != expected:
            raise ValueError(f"Existing {target} does not match the mirror pin; not overwriting")
    elif target.is_symlink():
        raise ValueError(f"Broken reference link {target}; not overwriting")
    else:
        if not bridge.is_file() or digest(bridge) != expected:
            raise ValueError(f"Missing or wrong-hash mirror reference: {bridge}")
        target.symlink_to(os.path.relpath(bridge, target.parent))
    return target


def verified_band_cache(root: Path, source_sha: str) -> dict:
    """Verify every existing cached band; never silently reuse partial output."""
    cache = root / ".cache/features"
    receipt = root / "evidence/feature_cache.json"
    if cache.is_symlink() or not cache.is_dir() or receipt.is_symlink() or not receipt.is_file():
        raise ValueError("Existing feature cache or its receipt is missing or unsafe; not overwriting")
    report = json.loads(receipt.read_text())
    bands = report.get("bands", [])
    if report.get("source_sha256") != source_sha or report.get("count") != 19 or len(bands) != 19:
        raise ValueError("Existing feature cache receipt does not match the 19-band source; not overwriting")
    for index, band in enumerate(bands, 1):
        expected_path = f".cache/features/band-{index:02d}.npy"
        path = root / expected_path
        if (band.get("band") != index or band.get("cache_file") != expected_path
                or path.is_symlink() or not path.is_file() or digest(path) != band.get("sha256")):
            raise ValueError(f"Existing band {index} is missing or wrong-hash; not overwriting")
    return report


def ensure_band_cache(root: Path, template, source_sha: str) -> tuple[dict, bool]:
    """Reuse verified bands or stage the unchanged template builder before publishing."""
    cache = root / ".cache/features"
    if cache.exists() or cache.is_symlink():
        return verified_band_cache(root, source_sha), False
    cache.parent.mkdir(parents=True, exist_ok=True)
    receipt = root / "evidence/feature_cache.json"
    if receipt.is_symlink() or (receipt.exists() and not receipt.is_file()):
        raise ValueError("Feature receipt is not a regular file; not overwriting")
    with tempfile.TemporaryDirectory(prefix=".band-build-", dir=cache.parent) as directory:
        stage = Path(directory)
        (stage / "data").mkdir()
        (stage / "data/official").symlink_to((root / "data/official").resolve(), target_is_directory=True)
        report = template.cache_bands(stage)
        staged_receipt = stage / "evidence/feature_cache.json"
        if not staged_receipt.is_file():
            raise ValueError("Shared builder did not write a cache receipt")
        # Check every output, including the source digest, before publishing it.
        verified_band_cache(stage, source_sha)
        if report != json.loads(staged_receipt.read_text()):
            raise ValueError("Shared builder report and receipt differ")
        if receipt.exists() and json.loads(receipt.read_text()) != report:
            raise ValueError("Existing feature receipt differs from staged cache; not overwriting")
        if cache.exists() or cache.is_symlink():
            raise ValueError("Feature cache appeared while staging; not overwriting")
        os.rename(stage / ".cache/features", cache)
        if not receipt.exists():
            receipt.parent.mkdir(parents=True, exist_ok=True)
            with receipt.open("x", encoding="utf-8") as stream:
                stream.write(staged_receipt.read_text())
        return report, True


def prepare(root: Path, *, fetch: bool, cache_bands: bool) -> dict:
    template = load_shared_template(root)
    references = {}
    for name in ("sample_submission.tif", "labels.tif", "existing_faults.tif"):
        expected = template.PIN[f"data/official/{name}"]
        references[name] = str(verify_or_link(root, name, expected).relative_to(root))

    feature = root / "data/official/training_features.tif"
    feature_expected = template.PIN["data/official/training_features.tif"]
    assembly = None
    if feature.exists():
        if not feature.is_file() or digest(feature) != feature_expected:
            raise ValueError(f"Existing {feature} does not match the mirror pin; not overwriting")
    elif feature.is_symlink():
        raise ValueError(f"Broken feature link {feature}; not overwriting")
    elif fetch:
        # The unchanged shared builder writes fixed paths. Preflight them first so
        # it cannot clobber an existing cache, part, or partial download.
        cached = root / ".cache/training_features.tif"
        partial = cached.with_suffix(".tif.partial")
        if partial.exists() or partial.is_symlink():
            raise ValueError(f"Existing partial assembly {partial}; not overwriting")
        if cached.is_symlink() or (cached.exists() and not cached.is_file()):
            raise ValueError(f"Unsafe feature cache {cached}; not overwriting")
        if cached.is_file():
            if digest(cached) != feature_expected:
                raise ValueError(f"Existing {cached} has the wrong hash; not overwriting")
            feature.parent.mkdir(parents=True, exist_ok=True)
            feature.symlink_to(os.path.relpath(cached, feature.parent))
        else:
            for index, (size, expected) in enumerate(template.PARTS):
                part = root / f".cache/source_parts/gems-geodawn-numerical-features.tif.part-{index:03d}"
                part_partial = part.with_name(part.name + ".partial")
                if part_partial.exists() or part_partial.is_symlink():
                    raise ValueError(f"Existing partial source part {part_partial}; not overwriting")
                if part.is_symlink() or (part.exists() and (not part.is_file() or part.stat().st_size != size or digest(part) != expected)):
                    raise ValueError(f"Existing source part {part} is unsafe or wrong-hash; not overwriting")
            assembly = template.assemble_features(root)
    else:
        raise FileNotFoundError("Missing feature raster; run scripts/prepare_data.py --fetch --cache-bands")
    if not feature.is_file() or digest(feature) != feature_expected:
        raise ValueError("Restored feature raster failed its SHA-256 pin")

    # Check shape/count/grid before using the template's per-band cache builder.
    import rasterio
    with rasterio.open(feature) as src, rasterio.open(root / references["sample_submission.tif"]) as sample:
        if src.count != 19 or (src.shape, src.crs, src.transform) != (sample.shape, sample.crs, sample.transform):
            raise ValueError("Feature stack must have 19 bands and match the reference grid")
    cache, created = ensure_band_cache(root, template, feature_expected) if cache_bands else (None, False)
    return {
        "feature_sha256": feature_expected,
        "reference_files": references,
        "source": "Hash-pinned owner mirror; NOT authenticated organizer data",
        "assembled_now": assembly is not None,
        "bands_available": cache["count"] if cache else None,
        "bands_cached_now": cache["count"] if created else 0,
        "cache_reused": bool(cache and not created),
        "cache_receipt": "evidence/feature_cache.json" if cache else None,
        "ok_to_submit": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Download missing pinned feature parts via gh")
    parser.add_argument("--cache-bands", action="store_true", help="Use the shared template to write the ignored per-band cache")
    args = parser.parse_args()
    try:
        report = prepare(ROOT, fetch=args.fetch, cache_bands=args.cache_bands)
    except (FileNotFoundError, ValueError, OSError, RuntimeError) as error:
        print(f"Data preparation failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
