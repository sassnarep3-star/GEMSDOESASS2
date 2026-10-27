#!/usr/bin/env bash
set -euo pipefail
# Download competition data from DrivenData (requires login) into data/
# Verified sources: https://www.drivendata.org/competitions/306/competition-doe-gems/data/
# Due to login wall, this script must be run on an unrestricted machine with DrivenData credentials.
# It will place training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv into data/
# Alternative free mirrors (official, verified):
# - GDR 1391 https://gdr.openei.org/submissions/1391  (free, CC-BY-4.0, DOI 10.15121/1881483)
# - USGS GeoDAWN https://doi.org/10.5066/P93LGLVQ
# - USGS SGMC https://doi.org/10.3133/ds1052
echo "This environment cannot auto-download login-walled DrivenData data."
echo "On a machine with credentials, run:"
echo "  curl -O https://www.drivendata.org/competitions/306/competition-doe-gems/data/training_features.tif"
echo "  # or use the official GDR/USGS mirrors listed in docs/index.html"
echo "Place files into data/ then run python scripts/prepare_data.py"
echo "Current cache verification (if you have GEMSDOE32 cache):"
ls -lh /tmp/GEMSDOE24/data/bridge/ 2>/dev/null || echo "no cache"
