#!/usr/bin/env bash
set -euo pipefail
# The official DrivenData data tab requires an authenticated account.  This
# repository cannot mint or store those credentials and must not treat an HTML
# login response as a GeoTIFF.  Fail closed with reproducible alternatives.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f data/training_features.tif && -f data/labels.tif && -f data/sample_submission.tif ]]; then
  echo "Found authenticated-looking core files in data/. Verifying placement..."
  exec python scripts/prepare_data.py --data-dir data
fi

cat >&2 <<'MSG'
Competition data is not present in data/.

Official source (requires the user's own DrivenData login):
  https://www.drivendata.org/competitions/306/competition-doe-gems/data/

This script does not ask for, store, or automate credentials.  On an
unrestricted machine, place training_features.tif, labels.tif, and
sample_submission.tif in data/ (and 1m_DEM_links.csv if available), then run:
  python scripts/prepare_data.py --data-dir data

For the owner-mirror audit lane only, use the hash-pinned public GitHub restore
(which is explicitly NOT organizer-authenticated and may download hundreds of
MB):
  python scripts/fetch_data.py --dest .cache/gems_data
  python scripts/prepare_data.py --data-dir .cache/gems_data
MSG
exit 2
