#!/usr/bin/env python3
"""Exact pairwise lane check among the nine pinned focus files and the candidate.

For every ordered pair (i, j): fwd = share of i's dots within 3 px of a dot of j (lane rule: > 0.70 = duplicate),
and |Spearman| of the two rasters over the fixed 200k footprint sample (lane rule: > 0.90 = duplicate).
Exact, no sampling of the dots. Writes evidence/focus_pairwise.json.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gate_candidate import TEMPLATE, fraction_within, positives  # noqa: E402
from gate_batch import sample_idx  # noqa: E402

CACHE = Path(os.environ.get("GEMS_REGISTRY", str(Path.home() / ".cache" / "registry")))
FILES = [("candidate-cc522684-zeros", ROOT / "docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif")]
FILES += [(s, CACHE / "focus" / f"{s}.tif") for s in
          ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]]


def main() -> int:
    idx = sample_idx()
    data = {}
    for name, p in FILES:
        with rasterio.open(p) as ds:
            a = ds.read(1)
        pos = positives(a)
        data[name] = {"pts": np.argwhere(pos), "shape": pos.shape, "s": a.ravel()[idx].astype(np.float64),
                      "n": int(pos.sum()), "path": str(p.relative_to(ROOT)) if str(p).startswith(str(ROOT)) else str(p)}
    names = list(data)
    fwd = {}
    for i in names:
        fwd[i] = {}
        for j in names:
            fwd[i][j] = 1.0 if i == j else round(fraction_within(data[i]["pts"], data[j]["pts"], data[j]["shape"]), 6)
    rho = {}
    for i in names:
        rho[i] = {}
        for j in names:
            if i == j:
                rho[i][j] = 1.0; continue
            ok = np.isfinite(data[i]["s"]) & np.isfinite(data[j]["s"])
            rho[i][j] = round(abs(float(spearmanr(data[i]["s"][ok], data[j]["s"][ok]).statistic)), 6) if ok.sum() > 2 else None
    rows = []
    for i in names:
        others = [j for j in names if j != i]
        worst = max(others, key=lambda j: fwd[i][j])
        rows.append({"file": i, "path": data[i]["path"], "dots": data[i]["n"],
                     "max_fwd_overlap_vs_other": {"with": worst, "value": fwd[i][worst]},
                     "max_abs_spearman_vs_other": {"with": max(others, key=lambda j: rho[i][j]), "value": max(rho[i][j] for j in others)},
                     "lane_duplicate": bool(fwd[i][worst] > 0.70 or max(rho[i][j] for j in others) > 0.90)})
    out = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "scope": "pairwise among the nine pinned focus files and the candidate (NOT the full 2,277-raster registry)",
           "rules": {"overlap_3px_max": 0.70, "abs_spearman_max": 0.90},
           "fwd_overlap": fwd, "abs_spearman": rho, "summary": rows}
    (ROOT / "evidence/focus_pairwise.json").write_text(json.dumps(out, indent=1) + "\n")
    for r in rows:
        print(r["file"], r["dots"], r["max_fwd_overlap_vs_other"], r["max_abs_spearman_vs_other"], "DUP" if r["lane_duplicate"] else "ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
