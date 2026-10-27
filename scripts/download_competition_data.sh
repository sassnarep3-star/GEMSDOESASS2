#!/usr/bin/env bash
# Autonomous competition + USGS/DOE external dataset downloader & SHA-256 verifier.
# Populates .cache/gems_data (git-ignored) and writes data/restore_receipt.json.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

echo "[GEMSDOESASS2] Verifying / fetching 33 SHA-256 pinned competition & external datasets..."
"${PYTHON_BIN}" "${ROOT}/scripts/fetch_data.py" --dest "${ROOT}/.cache/gems_data" --receipt "${ROOT}/data/restore_receipt.json"
echo "[GEMSDOESASS2] All 33 datasets verified bit-for-bit."
