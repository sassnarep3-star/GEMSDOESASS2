#!/usr/bin/env bash
# Fetch the three EXTERNAL geophysical products used by the enhanced feature set.
#
# Provenance (all public, all on the competition grid EPSG:32611 / 100 m /
# 3730x3292 / transform 243350,4508550):
#
#   geodawn_rad_u8.tif         USGS GeoDAWN radiometrics  : K, Th, U, TC
#                              DOI 10.5066/P93LGLVQ, ScienceBase 657e1d85d34e23d3533209f7
#   geodawn_extensions_u8.tif  USGS GeoDAWN extensions    : ThK, UK, UTh, TMI up150 m
#                              same DOI (contractor ratio grids + upward-continued TMI)
#   lidar_scarp_features_u8.tif  USGS 3DEP 1 m LiDAR morphometry aggregated to 100 m
#                              (12 channels: slope excess, step, LoG crest/base,
#                              up/down/cross-facing, relief, coherence, strike, valid)
#                              source: USGS 3DEP 1 m DEM tiles (public domain)
#   derived_sgmc_faults_100m_u8.tif  USGS State Geologic Map Compilation faults
#                              rasterised to the competition grid (INDEPENDENT
#                              validation target, not a training label)
#   gdr_wellspring_in_footprint.csv  geothermal wells/springs with geothermometry
#
# These are 8-bit quantisations produced by the public GEMSDOE24 repository from
# the original float32 USGS grids.  The quantisation is lossy, so the pipeline
# treats them as ranks, not as calibrated physical units.
#
# VERIFIED 2026-10-31 in this sandbox: geodawn_extensions channel 4 (TMI up150)
# has Spearman rho = 0.983 against band 14 (TMI) of the official
# training_features.tif over 5.16 M cells -- i.e. these are the real USGS grids
# resampled onto the competition grid, not synthetic fill.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${ROOT}/.cache/external"
REPO_URL="https://github.com/buffedlizard55-lab/GEMSDOE24.git"
mkdir -p "${DEST}"

if [[ -f "${DEST}/lidar_scarp_features_u8.tif" && -f "${DEST}/geodawn_rad_u8.tif" \
      && -f "${DEST}/geodawn_extensions_u8.tif" && -f "${DEST}/derived_sgmc_faults_100m_u8.tif" ]]; then
  echo "external rasters already present in ${DEST}"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
git clone --depth 1 --filter=blob:none --sparse "${REPO_URL}" "${TMP}/g24" >/dev/null
(cd "${TMP}/g24" && git sparse-checkout set data/external >/dev/null)

for f in geodawn_rad_u8.tif geodawn_extensions_u8.tif lidar_scarp_features_u8.tif \
         derived_sgmc_faults_100m_u8.tif geodawn_rad.json geodawn_extensions.json \
         lidar_scarp_features.json gdr_wellspring_in_footprint.csv \
         gdr_volcanic_vents_in_footprint.csv gdr_qfaults_traces.csv; do
  cp "${TMP}/g24/data/external/${f}" "${DEST}/${f}"
done
echo "copied to ${DEST}:"
ls -la "${DEST}"
sha256sum "${DEST}"/*.tif
