#!/usr/bin/env bash
# Uniqueness gate for the candidate (zeros + NaN variants) and the nine pinned focus files.
# One registry pass via scripts/gate_batch.py. Inputs: candidate in docs/downloads; focus files
# fetched by scripts/fetch_focus_files.py into ~/.cache/registry/focus/.
set -u
cd "$(dirname "$0")/.."
C=docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif
N=docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-nan.tif
F=""
for site in GEMSDOE24 GEMSDOE25 GEMSDOE27 GEMSDOE28 GEMSDOE30 GEMSDOE31 GEMSDOE32 GEMSDOE33 GEMSDOE36; do
  F="$F $HOME/.cache/registry/focus/$site.tif"
done
.venv/bin/python scripts/gate_batch.py evidence/gates "$C" "$N" $F --no-rho
echo GATES_DONE
