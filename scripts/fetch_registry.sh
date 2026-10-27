#!/usr/bin/env bash
# Fetch the registry caches (feature stacks, catalogue bridges, prior
# submission rasters) from the public GEMSDOE GitHub repos into
# ${GEMS_REGISTRY:-~/.cache/registry}.  Fully automated; no credentials.
set -euo pipefail
DEST="${GEMS_REGISTRY:-$HOME/.cache/registry}"
mkdir -p "$DEST"
cd "$DEST"
for r in GEMSDOE32 GEMSDOE28 GEMSDOE31 GEMSDOE36 GEMSDOE33 GEMSDOE30 GEMSDOE25 GEMSDOE27; do
  [ -d "$r" ] || git clone --depth 1 "https://github.com/buffedlizard55-lab/$r.git"
done
if [ ! -d GEMSDOE24 ]; then
  git clone --depth 1 --filter=blob:none --sparse "https://github.com/buffedlizard55-lab/GEMSDOE24.git"
  cd GEMSDOE24
  git sparse-checkout set --no-cone '/data/**' '/src/**' '/scripts/**' \
    '/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif'
fi
echo "registry cache ready at $DEST"
