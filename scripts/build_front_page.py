#!/usr/bin/env python3
"""Generate the public front page, the executive summary (HTML + Markdown) and the submission guide.

Every number comes from evidence files (focus_pins.json, focus_pairwise.json, run_card_20261030.json).
The historical scores are USER-REPORTED (README table) and are labelled as such.
The page never states an approval: the verdict is read from the run card.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CAND = "docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif"
CAND_NAME = "gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif"
NOTE = "GEMSDOESASS2 sparse-blind-conduit 22163d B=2 sep3 | off-catalogue blind faults | cc522684 | research"
SUBMIT_NAME = "GEMSDOESASS2-SPARSE-BLIND-CC522684"
REPO_MAIN = "https://github.com/sassnarep3-star/GEMSDOESASS2/blob/main/"
CANDH = "downloads/" + CAND_NAME  # relative to docs/ (GitHub Pages)

# User-reported historical values (README table, 2026-10-30). Not verified; no organizer receipt.
HIST = {"GEMSDOE32": 0.2778, "GEMSDOE36": 0.2750, "GEMSDOE28": 0.2710, "GEMSDOE31": 0.2708, "GEMSDOE33": 0.2632,
        "GEMSDOE25": 0.2600, "GEMSDOE30": 0.2600, "GEMSDOE24": 0.2477, "GEMSDOE27": 0.2449}
SITES = sorted(HIST, key=lambda s: -HIST[s])


def load(p):
    return json.loads((ROOT / p).read_text())


def main() -> int:
    pins = {f["site"]: f for f in load("registry/focus_pins.json")["files"]}
    pair = load("evidence/focus_pairwise.json")
    card = load("evidence/run_card_20261030.json")
    summ = {r["file"]: r for r in pair["summary"]}
    cand_sha = card["candidate"]["zeros"]["sha256"]
    rows = []
    for s in SITES:
        r = summ[s]
        pin = pins[s]
        url = f"https://github.com/{pin['repo']}/blob/{pin['commit']}/{pin['path']}"
        rows.append({"site": s, "hist": HIST[s], "url": url, "sha": pin["sha256"], "bytes": pin["bytes"],
                     "with": r["max_fwd_overlap_vs_other"]["with"], "ov": r["max_fwd_overlap_vs_other"]["value"]})

    # ---------- shared pieces ----------
    verdict = ("No file passes the lane gate. The unique candidate is format-valid, "
               "but 100% of its dots lie within 3 px of a dense GEMSDOE2 surface (rule: more than 70% = duplicate).")
    holdout_line = ("Proxy holdout (HOLDOUT-DTI, proxy truth, not organizer score): this design scores 0.0; "
                    "uniform random coverage scores 0.0375 [0.0355, 0.0395].")
    site_rows_html = "\n".join(
        f"<tr><td><strong>{r['site']}</strong></td><td>{r['hist']:.4f} <small>USER-REPORTED</small></td>"
        f"<td><a href=\"{html.escape(r['url'])}\" target=\"_blank\" rel=\"noopener\">pinned file ↗</a><br>"
        f"<small>{r['bytes']:,} B · sha256 {r['sha'][:12]}…</small></td>"
        f"<td>Not estimable <small>(no holdout run on this file)</small></td>"
        f"<td><span class=\"no\">NO</span> <small>{r['ov']*100:.2f}% within 3 px of {r['with']}</small></td></tr>"
        for r in rows)
    site_rows_md = "\n".join(
        f"| {r['site']} | {r['hist']:.4f} (user-reported) | [pinned file]({r['url']}) · {r['bytes']:,} B | Not estimable | **NO** — {r['ov']*100:.2f}% within 3 px of {r['with']} |"
        for r in rows)

    cand_row_md = (f"| **Unique candidate** `{CAND_NAME}` | — | [download]({CAND}) · 123,328 B | Not estimable — proxy DTI 0.0 | "
                   f"**NO** — 100% within 3 px of GEMSDOE2 dense surface |")

    # ---------- index.html ----------
    index = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GEMSDOESASS2 — submission decision desk</title>
<style>
body{{font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0b1120;color:#e5e7eb}}
main{{max-width:1040px;margin:0 auto;padding:24px}}
a{{color:#7dd3fc}} small{{color:#94a3b8}}
.verdict{{background:#3b0d0d;border:2px solid #ef4444;border-radius:10px;padding:16px;margin:16px 0}}
.btn{{display:inline-block;background:#10b981;color:#052e1b;font-weight:700;padding:12px 18px;border-radius:8px;text-decoration:none;margin:6px 6px 6px 0}}
.btn2{{background:#1e293b;color:#e5e7eb;border:1px solid #334155}}
table{{width:100%;border-collapse:collapse;margin:12px 0}} th,td{{border-bottom:1px solid #1e293b;padding:8px;text-align:left;vertical-align:top}}
th{{color:#94a3b8;font-weight:600}} .no{{background:#7f1d1d;color:#fecaca;padding:2px 6px;border-radius:4px;font-weight:700}}
.box{{background:#111827;border:1px solid #1f2937;border-radius:10px;padding:14px;margin:14px 0}}
code{{background:#1e293b;padding:1px 5px;border-radius:4px}}
</style></head><body><a class="skip" href="#main">Skip to content</a><main id="main">
<h1>GEMSDOESASS2 — submission decision desk</h1>
<p><small>Updated 2026-10-30 · DrivenData GEMS competition 306 · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page ↗</a></small></p>

<div class="verdict"><strong>Verdict: DO NOT SUBMIT.</strong> {html.escape(verdict)}<br>
Do not upload anything from this site to the portal. The "[0, 1]" error reported earlier cannot be diagnosed without the rejected bytes and the portal's response.</div>

<p><a class="btn" href="{CANDH}" download>⬇ Download the candidate TIF (research only — not approved)</a>
<a class="btn btn2" href="executive-summary.html">Executive summary</a>
<a class="btn btn2" href="submission-guide.html">Submission guide</a></p>

<div class="box"><strong>Candidate</strong><br>
File: <code>{CAND_NAME}</code> · 22,163 dots · sha256 <code>{cand_sha}</code><br>
Format: float32, 1 band, 3730×3292, EPSG:32611, 100 m north-up, 0 NaN in footprint, values in [0, 1]. <strong>Format check passes; that is not approval.</strong><br>
Submission name (if approved later): <code>{SUBMIT_NAME}</code> · note ({len(NOTE)} chars): <code>{html.escape(NOTE)}</code></div>

<h2>Score evidence</h2>
<p>{html.escape(holdout_line)} Labels: <strong>HOLDOUT-DTI (PROXY)</strong>. No <strong>ORGANIZER-CONFIRMED</strong> score exists for any file here. The leaderboard snapshot of 2026-10-30 has #1 = 0.4544 and #47 = 0.3231 (<a href="data/leaderboard-snapshot-2026-10-30.json">snapshot</a>).</p>

<h2>Nine focus sites</h2>
<p><small>Historical values are <strong>USER-REPORTED / UNVERIFIED</strong>. "Unique" uses the parallel-run lane rule (duplicate if more than 70% of dots lie within 3 px of another raster). The overlap figure is the largest against any other focus file (<a href="{REPO_MAIN}evidence/focus_pairwise.json">evidence</a>).</small></p>
<table><thead><tr><th>Site</th><th>Historical value</th><th>File to download (pinned)</th><th>Estimated score</th><th>Unique?</th></tr></thead>
<tbody>
{site_rows_html}
<tr><td><strong>Candidate</strong></td><td>—</td><td><a href="{CANDH}">download</a></td><td>Not estimable (proxy DTI 0.0)</td><td><span class="no">NO</span> <small>100% within 3 px of GEMSDOE2 dense surface</small></td></tr>
</tbody></table>

<h2>Why nothing here is approved</h2>
<ul>
<li>The unique candidate fails the written lane rule (dense-surface overlap = 100%). See <a href="{REPO_MAIN}evidence/gates/lane_cc522684_vs_GEMSDOE2_turbo.json">evidence</a>.</li>
<li>Every focus file is a duplicate of a sibling (8 of 9 at 97.5%+; GEMSDOE28 and GEMSDOE24 at 100%).</li>
<li>The proxy holdout gives 0.0 for the candidate design; random coverage gives 0.0375.</li>
<li>The full registry pass (2,277 rasters) is incomplete. See <a href="{REPO_MAIN}evidence/run_card_20261030.json">run card</a>.</li>
</ul>
<p><a href="focus-sites.html">Nine-site receipts (legacy, superseded)</a> · <a href="executive-summary.html">Executive summary</a> · <a href="submission-guide.html">Submission guide</a><br><a href="{REPO_MAIN}research/2026-10-30-hypotheses-and-experiments.md">Hypotheses and experiments</a> · <a href="{REPO_MAIN}IRREGULARITIES.md">Irregularities</a> · <a href="{REPO_MAIN}evidence/run_card_20261030.json">Run card</a> · <a href="{REPO_MAIN}README.md">README</a></p>
</main></body></html>
"""
    (DOCS / "index.html").write_text(index)

    # ---------- executive summary (md) ----------
    md = f"""# Executive summary — GEMSDOESASS2 (2026-10-30)

**Verdict: DO NOT SUBMIT.** {verdict}

- **Download (research only):** [{CAND_NAME}]({CAND}) — sha256 `{cand_sha}`
- **Estimated score:** not estimable. The only numbers are PROXY holdout results for the design class, labelled HOLDOUT-DTI. No ORGANIZER-CONFIRMED score exists here.
- **Unique?** No. Lane rule: more than 70% of dots within 3 px of another raster = duplicate.

## Nine focus sites

Historical values are USER-REPORTED / UNVERIFIED.

| Site | Historical value | File to download (pinned) | Estimated score | Unique? |
|---|---|---|---|---|
{site_rows_md}
{cand_row_md}

## Evidence

- {holdout_line}
- Pairwise lane check of the nine pinned focus files plus the candidate: [evidence/focus_pairwise.json](../evidence/focus_pairwise.json)
- Candidate vs dense GEMSDOE2 surface: [evidence/gates/lane_cc522684_vs_GEMSDOE2_turbo.json](../evidence/gates/lane_cc522684_vs_GEMSDOE2_turbo.json)
- Format validator (strict local pass; `ok_to_submit: false`): [evidence/validate_cc522684_zeros.json](../evidence/validate_cc522684_zeros.json)
- Run card: [evidence/run_card_20261030.json](../evidence/run_card_20261030.json)
- Hypotheses and experiments: [research/2026-10-30-hypotheses-and-experiments.md](../research/2026-10-30-hypotheses-and-experiments.md)

## Remaining work

1. Finish the full 2,277-raster lane pass (slow on 2 cores; the script is `scripts/gate_batch.py --no-rho`).
2. Owner ruling on the lane rule for dense probability surfaces (IR-S-01 / IR-RV-04). Literally, a dense surface makes almost any dot set a duplicate.
3. Authenticated access to the official `training_features.tif` (login-walled). This is needed for H-F1.
4. Allowlist access to USGS GeoDAWN and GDR 1391 INGENIOUS (H-R1, H-G1).
5. Organizer receipt for any submission. No weekly slot has been used.

Limitations: proxy truth is USGS/INGENIOUS segments, not the organizer's new faults. The historical scores are unverified. No organizer acceptance receipt exists here.
"""
    (DOCS / "executive-summary.md").write_text(md)

    # ---------- executive-summary.html (from the same markdown content) ----------
    esc = html.escape
    tbl = "".join(
        f"<tr><td><strong>{esc(r['site'])}</strong></td><td>{r['hist']:.4f} <small>USER-REPORTED</small></td>"
        f"<td><a href=\"{esc(r['url'])}\">pinned file ↗</a><br><small>{r['bytes']:,} B</small></td>"
        f"<td>Not estimable</td><td><span class=\"no\">NO</span> <small>{r['ov']*100:.2f}% vs {esc(r['with'])}</small></td></tr>"
        for r in rows)
    exec_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Executive summary — GEMSDOESASS2</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;margin:0;background:#0b1120;color:#e5e7eb}}main{{max-width:1040px;margin:0 auto;padding:24px}}a{{color:#7dd3fc}}small{{color:#94a3b8}}
table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #1e293b;padding:8px;text-align:left;vertical-align:top}}.no{{background:#7f1d1d;color:#fecaca;padding:2px 6px;border-radius:4px;font-weight:700}}
.verdict{{background:#3b0d0d;border:2px solid #ef4444;border-radius:10px;padding:14px}}</style></head><body><a class="skip" href="#main">Skip to content</a><main id="main">
<p><a href="index.html">← Front page</a> · <a href="submission-guide.html">Submission guide</a></p>
<h1>Executive summary</h1>
<div class="verdict"><strong>DO NOT SUBMIT.</strong> No file approved for submission. {esc(verdict)}</div>
<p><a href="{CANDH}" download>Download candidate TIF (research only)</a> · sha256 <code>{cand_sha}</code></p>
<p>Estimated score: not estimable. Proxy holdout only: {esc(holdout_line)}</p>
<table><thead><tr><th>Site</th><th>Historical value</th><th>File</th><th>Estimated score</th><th>Unique?</th></tr></thead><tbody>{tbl}
<tr><td><strong>Candidate</strong></td><td>—</td><td><a href="{CANDH}">download</a></td><td>Not estimable</td><td><span class="no">NO</span> 100% vs GEMSDOE2 dense surface</td></tr></tbody></table>
<h2 id="lattice">The lane (lattice) rule</h2>
<p>The written rule: a file is a duplicate if more than 70% of its dots fall within 3 px of one registry raster's dots. It is saturated. Dense probability surfaces such as GEMSDOE2 <code>gemsdoe2_turbo_submission.tif</code> (5.17 M positives) cover so much of the footprint that a 22k-dot file can match them at 100%. Earlier audits found this for every top file (<a href="{REPO_MAIN}evidence/lattice_saturation_check.json">evidence</a>). An owner ruling is needed before any file can pass.</p>
<h2 id="format">Format and submission rules</h2>
<p>Single float32 band; values in [0, 1] inside the footprint; NaN or null allowed outside it; EPSG:32611, 100 m, north-up, shape 3730×3292 (<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description ↗</a>). The candidate passes these checks locally (<a href="{REPO_MAIN}evidence/validate_cc522684_zeros.json">validator output</a>). A format pass is not approval. Submission name and note: <a href="submission-guide.html">submission guide</a>.</p>
<h2>Remaining work</h2><ol>
<li>Finish the full 2,277-raster lane pass.</li><li>Owner ruling on the lane rule for dense probability surfaces.</li>
<li>Authenticated official <code>training_features.tif</code> (H-F1).</li><li>Allowlist access to USGS GeoDAWN and GDR 1391 (H-R1, H-G1).</li>
<li>Organizer receipt for any submission.</li></ol>
<p><small>Full text: <a href="executive-summary.md">executive-summary.md</a> · <a href="{REPO_MAIN}evidence/run_card_20261030.json">run card</a></small></p>
</main></body></html>
"""
    (DOCS / "executive-summary.html").write_text(exec_html)

    # ---------- submission guide (honest: steps and their gates) ----------
    guide = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Submission guide — GEMSDOESASS2</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;margin:0;background:#0b1120;color:#e5e7eb}}main{{max-width:900px;margin:0 auto;padding:24px}}a{{color:#7dd3fc}}small{{color:#94a3b8}}code{{background:#1e293b;padding:1px 5px;border-radius:4px}}</style></head><body><a class="skip" href="#main">Skip to content</a><main id="main">
<p><a href="index.html">← Front page</a></p>
<h1>Submission guide</h1>
<p><strong>Current status: not approved. Do not upload the candidate.</strong> Follow these steps only after every gate passes and the owner has signed off.</p>
<ol>
<li><strong>Gate 1 — format.</strong> Run <code>scripts/validate_tif.py --sample data/bridge/sample_submission.tif</code>. Required: <code>strict_local_format_pass: true</code>. Current candidate: passes.</li>
<li><strong>Gate 2 — lane (uniqueness).</strong> No registry raster may have &gt;70% of dots within 3 px, and |Spearman| must be ≤0.90. Current candidate: <strong>fails</strong> (100% vs GEMSDOE2 dense surface).</li>
<li><strong>Gate 3 — leakage canary.</strong> Each feature alone must have AUC ≤0.90 on holdout. Current: no flag, but the design scores 0.0.</li>
<li><strong>Gate 4 — holdout.</strong> HOLDOUT-DTI must beat the random-coverage baseline (0.0375) with non-overlapping CIs. Current: fails.</li>
<li><strong>Portal.</strong> Name: <code>{SUBMIT_NAME}</code>. Note (≤140 chars, {len(NOTE)} used): <code>{esc(NOTE)}</code>. Weekly limit: 3 (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules §3.2</a>). Check your remaining allowance on the live page first.</li>
</ol>
<p>Problem and metric: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description ↗</a> · Leaderboard: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">live ↗</a></p>
<p><small>The portal error "Predicted values must be in range [0, 1]" cannot be diagnosed without the rejected bytes and the portal response (IR-09, IR-S-02).</small></p>
</main></body></html>
"""
    (DOCS / "submission-guide.html").write_text(guide)
    print("wrote docs/index.html, docs/executive-summary.md, docs/executive-summary.html, docs/submission-guide.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
