#!/usr/bin/env python3
"""Build the nine-focus-site executive summary (evidence JSON + docs/focus-sites.html).

Inputs (all in the repo except the registry cache):
  * evidence/nine_sites_audit.json          - per-site historic best file, sha256, live score
  * evidence/focus_uniqueness_downloads.json - genuine-gate receipts for our candidates
  * ~/.cache/registry/<SITE>/...             - the historic-best rasters (sha256 re-verified here)

Outputs:
  * evidence/focus_sites_summary.json
  * docs/focus-sites.html

Labels follow the PARALLEL-RUN PROTOCOL rule 3:
  ORGANIZER-CONFIRMED - copied from a leaderboard/portal receipt quoted in the audit
  USER-REPORTED       - score from the user's submission list, not authenticated
  HOLDOUT-DTI         - our evaluator; never presented as a leaderboard score
A projected leaderboard score is never written; the table says "not estimable".
"""
from __future__ import annotations

import glob
import hashlib
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = Path(os.environ.get("GEMS_REGISTRY", Path.home() / ".cache" / "registry"))
RADIUS = 3.0

OUR_CANDIDATES = {
    "SASS2-XGHF (zeros.tif)": "docs/downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif",
    "HVFD-EXP3 (zeros.tif)": "docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif",
    "ASS2-ALTEDGE (zeros.tif)": "docs/downloads/gemsass2-ass2-altedge-hgb-44090-20261027-cc854482215e-zeros.tif",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dot_coords(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        arr = ds.read(1)
    mask = np.isfinite(arr) & (arr > 0) & footprint
    return np.argwhere(mask)[:, ::-1].astype(np.float64)


def overlap(cand: np.ndarray, other: np.ndarray) -> float:
    if len(cand) == 0 or len(other) == 0:
        return 0.0
    d, _ = cKDTree(other).query(cand, k=1)
    return float((d <= RADIUS).mean())


def find_historic(site: str, filename: str) -> Path | None:
    hits = glob.glob(str(REGISTRY / site / "**" / filename), recursive=True)
    return Path(hits[0]) if hits else None


def main() -> int:
    audit = json.loads((ROOT / "evidence" / "nine_sites_audit.json").read_text())
    uniq = json.loads((ROOT / "evidence" / "focus_uniqueness_downloads.json").read_text())
    uniq_by_name = {c["candidate"]: c for c in uniq["candidates"]}

    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as ref:
        footprint = np.isfinite(ref.read(1)) & (ref.read_masks(1) > 0)

    cand_coords = {}
    for label, rel in OUR_CANDIDATES.items():
        cand_coords[label] = dot_coords(ROOT / rel, footprint)

    rows = []
    problems = []
    for s_ in audit["sites"]:
        site = s_["site"]
        hb = s_["historic_best"]
        fname = os.path.basename(hb["artifact_url"])
        path = find_historic(site, fname)
        if path is None:
            problems.append(f"{site}: historic raster {fname} not found in registry cache")
            rows.append({"site": site, "error": "raster not found"})
            continue
        sha = sha256_file(path)
        if sha != hb["artifact_sha256"]:
            problems.append(f"{site}: sha256 mismatch ({sha} != {hb['artifact_sha256']})")
        coords = dot_coords(path, footprint)
        overlaps = {label: round(overlap(cand_coords[label], coords), 4) for label in OUR_CANDIDATES}
        rows.append({
            "site": site,
            "historic_best_file": fname,
            "historic_best_sha256": sha,
            "artifact_url": hb["artifact_url"],
            "dots": int(len(coords)),
            "live_score": hb.get("reported_score"),
            "live_score_label": hb.get("score_label"),
            "audit_max_overlap_peer": hb.get("max_overlap_peer"),
            "audit_max_overlap_fraction": hb.get("max_overlap_fraction"),
            "audit_unique_against_nine": hb.get("unique_against_nine"),
            "our_candidate_3px_overlap_with_this_historic_best": overlaps,
            "may_resubmit": False,
            "recommended_action": "Do not resubmit: already scored, and it duplicates another focus variant (audit).",
            "estimated_leaderboard_score": "NOT ESTIMABLE",
        })

    xghf = uniq_by_name.get(Path(OUR_CANDIDATES["SASS2-XGHF (zeros.tif)"]).name, {})
    summary = {
        "schema": "focus-sites-summary-v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sites": rows,
        "our_candidates": {
            label: {
                "file": rel,
                "sha256": sha256_file(ROOT / rel),
                "genuine_worst_overlap_3px": (uniq_by_name.get(Path(rel).name) or {}).get("genuine_worst_overlap_3px"),
                "genuine_worst_abs_spearman": (uniq_by_name.get(Path(rel).name) or {}).get("genuine_worst_abs_spearman"),
                "genuine_gates_pass": (uniq_by_name.get(Path(rel).name) or {}).get("genuine_gates_pass"),
                "literal_all_gates_pass": (uniq_by_name.get(Path(rel).name) or {}).get("literal_all_gates_pass"),
            }
            for label, rel in OUR_CANDIDATES.items()
        },
        "problems": problems,
        "label_legend": {
            "ORGANIZER-CONFIRMED": "copied from a leaderboard/portal receipt quoted in the audit",
            "USER-REPORTED": "score from the user's submission list; not authenticated",
            "HOLDOUT-DTI": "our evaluator (gems57-pooled-hide-v2); not a leaderboard score",
        },
        "xghf_repo_reported_holdout": {
            "label": "HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, repo-reported, NOT re-run in this session)",
            "dti": 0.131134, "ci95": [0.118009, 0.142930], "n_withheld": 22232,
            "source": "docs/executive-summary.md",
        },
        "xghf_genuine_gate_receipt": xghf,
    }
    (ROOT / "evidence" / "focus_sites_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    html_path = ROOT / "docs" / "focus-sites.html"
    html_path.write_text(render_html(summary))
    print(f"wrote {html_path} and evidence/focus_sites_summary.json; problems={len(problems)}")
    for p in problems:
        print("PROBLEM:", p)
    return 1 if problems else 0


def render_html(summary: dict) -> str:
    esc = html.escape
    def fmt(x):
        return "—" if x is None else (f"{x:.4f}" if isinstance(x, float) else esc(str(x)))

    site_rows = []
    for r in summary["sites"]:
        if "error" in r:
            site_rows.append(f"<tr><td>{esc(r['site'])}</td><td colspan='6'>ERROR: {esc(r['error'])}</td></tr>")
            continue
        site_rows.append(
            "<tr>"
            f"<td><b>{esc(r['site'])}</b></td>"
            f"<td><code>{esc(r['historic_best_file'])}</code><br><span class='small'>sha256 {esc(r['historic_best_sha256'][:16])}… · {r['dots']:,} dots</span></td>"
            f"<td>{fmt(r['live_score'])}<br><span class='small'>{esc(r['live_score_label'])}</span></td>"
            f"<td>{fmt(r['audit_max_overlap_fraction'])}<br><span class='small'>vs {esc(str(r['audit_max_overlap_peer']))}</span></td>"
            f"<td><span class='no'>NO — do not resubmit</span><br><span class='small'>unique against nine (audit): {esc(str(r['audit_unique_against_nine']))}</span></td>"
            f"<td>{esc(r['estimated_leaderboard_score'])}</td>"
            f"<td>{esc(r['recommended_action'])}</td>"
            "</tr>"
        )

    cand_rows = []
    for label, c in summary["our_candidates"].items():
        ok = c["genuine_gates_pass"]
        cand_rows.append(
            "<tr>"
            f"<td><b>{esc(label)}</b><br><code>{esc(os.path.basename(c['file']))}</code></td>"
            f"<td>{fmt(c['genuine_worst_overlap_3px'])}</td>"
            f"<td>{fmt(c['genuine_worst_abs_spearman'])}</td>"
            f"<td><span class='{'yes' if ok else 'no'}'>{'PASS' if ok else 'FAIL'}</span></td>"
            f"<td><span class='small'>{esc(c['sha256'])}</span></td>"
            "</tr>"
        )

    x = summary["xghf_repo_reported_holdout"]
    probs = "".join(f"<li>{esc(p)}</li>" for p in summary["problems"]) or "<li>None — every historic raster re-hashed and matched.</li>"

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GEMSDOESASS2 — nine focus sites: executive summary</title>
<link rel="stylesheet" href="assets/site.css">
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#f6f8fa;color:#1f2328}}
.wrap{{max-width:1180px;margin:0 auto;padding:22px}}
.card{{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:16px 20px;margin:14px 0}}
.banner{{border-radius:10px;padding:16px 20px;margin:14px 0;font-size:16px}}
.bad{{background:#ffebe9;border:2px solid #cf222e}} .good{{background:#dafbe1;border:2px solid #1a7f37}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:14px;margin:12px 0}}
th,td{{border:1px solid #d0d7de;padding:8px 10px;text-align:left;vertical-align:top}}
th{{background:#eaeef2}} code{{background:#eff2f5;padding:1px 5px;border-radius:4px;font-size:12px;word-break:break-all}}
.small{{font-size:12px;color:#57606a}} .no{{color:#a40e26;font-weight:700}} .yes{{color:#1a7f37;font-weight:700}}
a{{color:#0969da}}
</style></head><body><div class="wrap">
<a href="#main" class="skip">Skip to content</a>
<p><a href="index.html">← Dashboard</a> · <a href="executive-summary.html">Submission guide</a></p>
<main id="main">
<h1>Nine focus sites — executive summary</h1>
<p>Focus sites: GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36. Generated {esc(summary['generated_utc'])} from
<code>evidence/nine_sites_audit.json</code> and <code>evidence/focus_uniqueness_downloads.json</code>.</p>

<div class="banner bad"><b>NO FILE IS CLEARED FOR SUBMISSION (fail-closed; consistent with the repo decision in README.md).</b><br>
Every current candidate fails the literal rule “more than 70% of dots within 3 px of any registry raster”, because the <code>13GEMSDOE r13-lattice-s5</code> probe covers about 99.9% of the footprint. Ignoring that probe (see §4), the genuine receipts give the picture below. An owner decision on the probe exemption is required before any slot is used.</div>

<div class="banner bad"><b>HVFD-EXP3 is not unique even among genuine submissions:</b> {fmt(summary['our_candidates']['HVFD-EXP3 (zeros.tif)']['genuine_worst_overlap_3px'])} of its dots lie within 3 px of the registered <code>8GEMSDOE Hedge-v2_submission</code> raster (limit 70%). Do not submit it.</div>

<div class="banner good"><b>Research-only candidate with the best genuine receipts:</b> SASS2-XGHF <code>…e7996841-zeros.tif</code>, worst genuine overlap <b>{fmt(summary['our_candidates']['SASS2-XGHF (zeros.tif)']['genuine_worst_overlap_3px'])}</b>, worst |Spearman| {fmt(summary['our_candidates']['SASS2-XGHF (zeros.tif)']['genuine_worst_abs_spearman'])}. It still fails the literal lattice rule, so it is <b>not cleared</b>.<br>
<b>Estimated leaderboard score: NOT ESTIMABLE.</b> No proxy here predicts the leaderboard (see §3). Only an organizer receipt after a submission is a score.</div>

<div class="card"><h2>1. Our candidates against the genuine submission rasters</h2>
<p class="small">Genuine = every unique-SHA256 3730×3292 submission GeoTIFF in the local registry cache (452 rasters after the feature-stack exclusion). The space-filling probe <code>r13-lattice-s5</code> is reported separately (see §4).</p>
<table><tr><th>Candidate</th><th>Worst 3-px overlap</th><th>Worst |Spearman|</th><th>Genuine gates (≤70% / ≤0.90)</th><th>SHA-256</th></tr>
{''.join(cand_rows)}</table></div>

<div class="card"><h2>2. Per-site: best historic submission and what to do</h2>
<p class="small">Each historic best is re-hashed against <code>evidence/nine_sites_audit.json</code> and matched. Main’s audit verdict is <b>negative</b>: no focus variant is unique against the nine.</p>
<table><tr><th>Site</th><th>Historic best file</th><th>Reported score (label)</th><th>Audit max 3-px overlap vs another focus variant</th><th>Resubmit?</th><th>Estimated leaderboard score</th><th>Action</th></tr>
{''.join(site_rows)}</table></div>

<div class="card"><h2>3. Why no leaderboard estimate is written</h2>
<ul>
<li>The audit states that current scores are USER-REPORTED / UNVERIFIED: no organizer receipt ties a reported score to the pinned raster bytes.</li>
<li>Earlier retrospective holdout figures (about 0.003–0.09 for the H19-5 family, live scores 0.2449–0.2778) do not reproduce the leaderboard ordering, so no holdout proxy here estimates a leaderboard score.</li>
<li>SASS2-XGHF’s repo-reported holdout (older run card; not re-run here) is <b>{x['dti']:.6f} [{x['ci95'][0]:.6f}, {x['ci95'][1]:.6f}]</b>, n={x['n_withheld']:,} (label: {esc(x['label'])}). The 19-band feature cache is now restored from an owner mirror (see <code>evidence/feature_cache.json</code>), but no model was retrained in this session.</li>
</ul></div>

<div class="card"><h2>4. Space-filling probe exception (owner decision required)</h2>
<p><code>13GEMSDOE r13-lattice-s5</code> covers about 99.9% of the footprint within 3 px. Any 37,654-dot file therefore overlaps it near 100%, so the literal “any registry raster ≤70%” rule cannot be met by any submission. The receipts exclude probes from the genuine gates and list their overlaps separately. The owner must rule on this exemption before a weekly slot is used.</p></div>

<div class="card"><h2>5. Irregularities and checks</h2><ul>{probs}</ul>
<p class="small">Full list: <a href="../IRREGULARITIES.md">IRREGULARITIES.md</a>. Receipts: <a href="../evidence/focus_sites_summary.json">focus_sites_summary.json</a>, <a href="../evidence/focus_uniqueness_downloads.json">focus_uniqueness_downloads.json</a>.</p></div>
</main></div></body></html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
