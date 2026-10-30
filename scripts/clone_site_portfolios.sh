#!/usr/bin/env bash
# Sparse-clone the GEMSDOE site portfolios (git protocol; not the GitHub REST API).
# Only blobs < 800k are fetched, so big rasters are skipped and small submission
# GeoTIFFs are downloaded for measurement. Idempotent: existing clones are updated.
set -uo pipefail
DEST="${1:-.cache/repos}"
mkdir -p "$DEST"; cd "$DEST"
SITES=(GEMSDOE GEMSDOE2 GEMSDOE3 GEMSDOE9 GEMSDOE10 GEMSDOE21 GEMSDOE23 GEMSDOE24 GEMSDOE25 GEMSDOE27 GEMSDOE28 GEMSDOE29 GEMSDOE30 GEMSDOE31 GEMSDOE32 GEMSDOE33 GEMSDOE36 GEMSDOE48 GEMSDOE49 GEMSDOE63 GEMSDOE67 GEMSDOE70 GEMSDOE73 GEMSDOE75 GEMSDOE76 GEMSDOE78 GEMSDOE82 GEMSDOE91 6GEMSDOE 7GEMSDOE 8GEMSDOE 11GEMSDOE 12GEMSDOE 13GEMSDOE 14GEMSDOE 15GEMSDOE 16GEMSDOE 17GEMSDOE 18GEMSDOE 19GEMSDOE 20GEMSDOE 55GEMSDOE)
for s in "${SITES[@]}"; do
  if [ -d "$s/.git" ]; then echo "SKIP $s"; continue; fi
  if timeout 300 git clone --depth 1 --filter=blob:limit=800k --sparse \
       "https://github.com/buffedlizard55-lab/$s.git" "$s" >/dev/null 2>&1; then
    ( cd "$s" && git sparse-checkout set docs/downloads inputs data/external docs/data evidence 2>/dev/null )
    echo "CLONED $s $(du -sh "$s" 2>/dev/null | cut -f1)"
  else
    echo "FAILED $s"
  fi
done
echo DONE
