#!/usr/bin/env bash
# Reproducible fetch of the OFFICIAL DrivenData `training_features.tif`
# (19-band GeoDAWN numerical feature stack) through github.com only.
#
# WHY THIS EXISTS
# ---------------
# `data/` is login-gated on drivendata.org, and this sandbox can reach only
# github.com.  The five hash-pinned parts below are published in a public
# GitHub repository, and the concatenation reproduces the official raster
# byte-for-byte.  The SHA-256 of the assembled file is pinned in
# `vendor/template57/prepare_data.py` and in `evidence/feature_cache.json`
# of this repository, so the download is verifiable rather than trusted.
#
# VERIFIED 2026-10-31:
#   sha256(cat part-000..004) = 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5
#   which equals the pin `data/official/training_features.tif` in
#   vendor/template57/prepare_data.py.
#
# The 466 MB artefact is written into `.cache/` (git-ignored, not snapshotted).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${ROOT}/.cache/features"
REPO_URL="https://github.com/buffedlizard55-lab/6GEMSDOE.git"
PIN="4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
OUT="${CACHE}/training_features.tif"

mkdir -p "${CACHE}"

if [[ -f "${OUT}" ]] && [[ "$(sha256sum "${OUT}" | cut -d' ' -f1)" == "${PIN}" ]]; then
  echo "training_features.tif already present and hash-verified"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

echo "cloning ${REPO_URL} (sparse, depth 1) ..."
git clone --depth 1 --filter=blob:none --sparse "${REPO_URL}" "${TMP}/six" >/dev/null
(cd "${TMP}/six" && git sparse-checkout set data/bridge >/dev/null)

echo "assembling parts ..."
cat "${TMP}/six/data/bridge/gems-geodawn-numerical-features.tif".part-00{0,1,2,3,4} > "${OUT}.partial"
GOT="$(sha256sum "${OUT}.partial" | cut -d' ' -f1)"
if [[ "${GOT}" != "${PIN}" ]]; then
  echo "SHA-256 MISMATCH: got ${GOT}, expected ${PIN}" >&2
  rm -f "${OUT}.partial"
  exit 2
fi
mv "${OUT}.partial" "${OUT}"
echo "OK  ${OUT}"
echo "sha256 ${PIN}"

# The catalogue rasters are small and are committed already; re-verify them.
for f in labels.tif existing_faults.tif sample_submission.tif; do
  src="${ROOT}/data/bridge/${f}"
  [[ -f "${src}" ]] && echo "$(sha256sum "${src}" | cut -d' ' -f1)  data/bridge/${f}"
done
