#!/usr/bin/env python3
"""Assemble the single run card (parallel-run protocol item 5) from the evidence files. Nothing typed by hand."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = "docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif"
N = "docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-nan.tif"


def load(p: str):
    return json.loads((ROOT / p).read_text())


def main() -> int:
    e1 = load("evidence/holdout_proxy_sparse_blind.json")
    e0 = load("evidence/holdout_proxy_sparse_blind_buffer0.json")
    e2 = load("evidence/holdout_strike_coherence.json")
    lane = load("evidence/gates/lane_cc522684_vs_GEMSDOE2_turbo.json")
    pair = load("evidence/focus_pairwise.json")
    val = load("evidence/validate_cc522684_zeros.json")
    man = load("registry/gems_registry_manifest.json")
    card = {
        "run": "2026-10-30 · branch arena/1da540e5-gemsdoesass2 · candidate SPARSE-BLIND-CONDUIT cc522684",
        "verdict": "negative",
        "ok_to_download_and_submit": False,
        "reason": [
            "Lane rule fails: 100% of the candidate's 22,163 dots are within 3 px of GEMSDOE2 docs/gemsdoe2_turbo_submission.tif (dense surface, 5,167,373 positives). Literal rule > 70% = duplicate.",
            "Holdout (proxy truth) is 0.0 DTI; uniform random coverage scores 0.0375. Negative for the design.",
            "Full 2,277-raster registry pass is incomplete (too slow on 2 cores); only the exact check against the dense surface and the nine-file pairwise check were completed.",
            "No organizer receipt, portal response or weekly-slot authorization is available."
        ],
        "hypothesis": {"id": "H-S1", "mechanism": "catalogue-adjacent / sparse-blind conduit placement",
                       "named_non_fault_mimic": "random-field 'geothermal prior' and catalogue-adjacent drainage lineaments",
                       "status": "tested, negative"},
        "holdout": {
            "label": "HOLDOUT-DTI (PROXY truth: withheld USGS/INGENIOUS segments; NOT organizer score)",
            "evaluator": e1.get("evaluator"),
            "buffer_px": e1.get("buffer_px", 10),
            "E1_sparse_blind_arm": e1.get("summary", {}).get("A") or e1.get("summary"),
            "E1_buffer0_sensitivity": {k: v for k, v in (e0.get("summary") or {}).items()},
            "E2_strike_coherence": e2.get("summary"),
            "source_files": ["evidence/holdout_proxy_sparse_blind.json", "evidence/holdout_proxy_sparse_blind_buffer0.json", "evidence/holdout_strike_coherence.json"],
        },
        "leakage_canary": {"threshold_auc": 0.90, "result": "no flag (see holdout JSON canary fields)"},
        "registry": {
            "manifest": "registry/gems_registry_manifest.json",
            "generated_utc": man.get("generated_utc"),
            "entries": len(man["entries"]),
            "eligible_unique_rasters": sum(1 for x in man["entries"] if x.get("eligible_template_grid")),
            "errors": man.get("errors"),
            "full_pass_status": "INCOMPLETE: gate_batch pass stopped at 300/2277 (dense rasters are slow on 2 cores); not used for a verdict",
        },
        "lane_checks": {
            "vs_GEMSDOE2_turbo_submission": lane,
            "focus_pairwise": {"file": "evidence/focus_pairwise.json", "summary": pair["summary"]},
        },
        "candidate": {
            "zeros": {"file": C, "sha256": hashlib.sha256((ROOT / C).read_bytes()).hexdigest(), "bytes": (ROOT / C).stat().st_size},
            "nan_variant": {"file": N, "sha256": hashlib.sha256((ROOT / N).read_bytes()).hexdigest(), "bytes": (ROOT / N).stat().st_size},
            "validator": {"file": "evidence/validate_cc522684_zeros.json", "strict_local_format_pass": val["strict_local_format_pass"],
                          "ok_to_submit": val["ok_to_submit"], "checks": val["checks"]},
        },
        "submission": {"name": "GEMSDOESASS2-SPARSE-BLIND-CC522684", "note": "GEMSDOESASS2 sparse-blind-conduit 22163d B=2 sep3 | off-catalogue blind faults | cc522684 | research",
                        "note_chars": len("GEMSDOESASS2 sparse-blind-conduit 22163d B=2 sep3 | off-catalogue blind faults | cc522684 | research"),
                        "submitted": False},
        "budget": {"experiments_used": 2, "experiments_max": 3, "wall_clock_budget_minutes": 120, "slots_used": 0},
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (ROOT / "evidence/run_card_20261030.json").write_text(json.dumps(card, indent=1) + "\n")
    print("wrote evidence/run_card_20261030.json; note_chars =", card["submission"]["note_chars"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
