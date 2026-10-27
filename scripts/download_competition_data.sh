#!/usr/bin/env bash
# The official competition data page requires a participant login. This
# diagnostic does not authenticate, store credentials, or invent file URLs.
set -euo pipefail
echo "Obtain official data through https://www.drivendata.org/competitions/306/competition-doe-gems/data/"
echo "Place organizer-provided sample and labels locally; verify provenance before using them."
echo "The optional python scripts/restore_training_mirror.py restores a hash-pinned owner mirror, not an authenticated organizer download or the shared prepared cache."
