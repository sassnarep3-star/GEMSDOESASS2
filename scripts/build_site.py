#!/usr/bin/env python3
"""Render the static Pages site from the checked-in audit and run card.

Fail closed if the card no longer describes the negative no-file state: a
future release must implement and verify its own evidence-bound presentation.
"""
from html import escape
import json
from pathlib import Path
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / 'evidence/portfolio-audit.json').read_text())
card = json.loads((ROOT / 'evidence/run-card.json').read_text())
manifest = json.loads((ROOT / 'data/inputs.json').read_text())
feed = json.loads((ROOT / 'docs/data/live-feed.json').read_text())
concurrent = json.loads((ROOT / 'evidence/concurrent-main-audit.json').read_text())
if any(row.get('decision') != 'negative' or row.get('ok_to_submit') is not False
       for row in concurrent.get('candidates', [])) or len(concurrent.get('candidates', [])) != 3:
    raise SystemExit('Unexpected concurrent release state; refusing to render a stale decision')
if (card.get('verdict') != 'negative' or card.get('ok_to_submit') is not False
        or card.get('raster_sha256') is not None or audit.get('current_candidate') is not None):
    raise SystemExit('Unexpected release state; refusing to render the no-file decision')
rows = sorted(audit['focus_history'], key=lambda x: float(x['owner_reported_score']), reverse=True)
items = {row['id']: row for row in manifest['items']}
candidates = {row['id']: row for row in audit['candidate_counterexamples']}
observed = feed.get('observation') or {}


def e(value):
    return escape(str(value), quote=True)


def header(prefix, active):
    links = [('Overview', 'index.html'), ('Executive summary', 'docs/executive-summary.html'),
             ('Research', 'docs/research.html'), ('Sources', 'docs/sources.html')]
    def nav_link(label, path):
        current = ' aria-current="page"' if label == active else ''
        return f'<a href="{prefix}{path}"{current}>{label}</a>'
    nav = ''.join(nav_link(label, path) for label, path in links)
    return f'''<a class="skip" href="#main">Skip to content</a><header class="site-header"><div class="wrap nav">
      <a class="brand" href="{prefix}index.html"><span class="brand-mark">G</span><span>GEMS FIELDNOTE<small>DISCOVERY RESEARCH</small></span></a>
      <nav class="nav-links" aria-label="Main navigation">{nav}</nav><div class="nav-end">Evidence first</div></div></header>'''


def footer(prefix):
    return f'''<footer class="footer"><div class="wrap footer-inner"><p>GEMS FIELDNOTE · Independent research, not an organizer website.</p>
      <div><a href="{prefix}evidence/run-card.json">Run card</a><a href="{prefix}evidence/portfolio-audit.json">Audit JSON</a>
      <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData ↗</a></div></div></footer>'''


def page(title, description, prefix, active, body):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="description" content="{e(description)}"><title>{e(title)} · GEMS Fieldnote</title><link rel="stylesheet" href="{prefix}assets/site.css">
    <script defer src="{prefix}assets/site.js"></script></head><body>{header(prefix, active)}{body}{footer(prefix)}</body></html>'''


def history_table():
    result = []
    for r in rows:
        peer = r['worst_of_other_eight'].upper()
        overlap = f'{r["worst_overlap_3px"] * 100:.1f}%'
        label = 'NO' if not r['unique_among_other_eight'] else 'WITHIN THIS SUBSET ONLY'
        result.append(f'''<tr><td class="site-name">{e(r['site'])}</td><td><a class="file-link" href="{e(r['source'])}">{e(r['filename'])} ↗</a>
          <div class="subtext">Historical owner-mirror bytes · not an upload</div></td>
          <td><span class="score">{e(r['owner_reported_score'])}</span><div class="subtext">USER/OWNER-REPORTED<br>unverified</div></td>
          <td><span class="blocked">{label}</span><div class="subtext">{overlap} near {e(peer)}</div></td>
          <td><span class="blocked">DO NOT RESUBMIT</span></td></tr>''')
    return '''<p class="scroll-hint">On small screens, scroll the table horizontally to see scores and status.</p><div class="table-box" tabindex="0" role="region" aria-label="Nine-site historical comparison; scroll horizontally"><table><thead><tr><th scope="col">Site</th><th scope="col">Historical file · reference only</th><th scope="col">User-listed score</th><th scope="col">Unique vs other eight?</th><th scope="col">Action</th></tr></thead><tbody>''' + ''.join(result) + '''</tbody></table></div>
    <p class="table-note">Scores are reported by the user/owners, not backed by an organizer receipt linking score to these bytes. Uniqueness here is the <em>directional 3-pixel overlap</em> against the other eight selected files only. These are not candidate leaderboard estimates or a complete registry scan. <a href="evidence/portfolio-audit.json">See the byte audit ↗</a></p>'''


def concurrent_rows():
    return ''.join(f'''<tr><td><strong>{e(r['label'])}</strong><div class="subtext">Prior concurrent session</div></td>
      <td>Not estimable</td><td><span class="blocked">NO</span><div class="subtext">{r['overlap_registered_lattice_3px']*100:.2f}% vs lattice · 100% vs literal dense witness</div></td>
      <td class="blocked">NO</td></tr>''' for r in concurrent['candidates'])


def watch_rows():
    return ''.join(f'''<li><a href="https://github.com/{e(items[r['id']]['repo'])}">{e(r['site'])} ↗</a>
        <span class="source-state" data-repo="{e(r['site'])}" data-pin="{e(items[r['id']]['ref'])}">Not checked</span></li>'''
        for r in sorted(rows, key=lambda x: x['site']))


lattice_bound = audit['certificates']['lattice']['budget_example']['minimum_possible_overlap'] * 100
s22_overlap = candidates['s22c_28']['overlap_lattice'] * 100
kpl_overlap = candidates['kpl36']['overlap_lattice'] * 100
index_body = f'''<main id="main"><section class="hero"><div class="wrap hero-grid"><div>
  <div class="eyebrow">Geothermal discovery &nbsp; / &nbsp; Research desk 01</div>
  <h1>Find the fault.<br><em>Protect the next submission.</em></h1>
  <p class="hero-copy">A clear, evidence-led view of the GEMS Prize: what we know, what the data can support, and when a new prediction is genuinely ready.</p>
  <div class="actions"><a class="button button-primary" href="docs/executive-summary.html">Read the decision <span aria-hidden="true">↗</span></a><a class="button button-ghost" href="#portfolio">Explore the nine sites <span aria-hidden="true">↓</span></a></div></div>
  <aside class="decision" aria-labelledby="decision-title"><div class="decision-top"><span class="overline">Current release gate</span><span class="pill pill-red">Do not submit</span></div>
  <h2 id="decision-title">No new file is cleared.</h2><p>No unique, validated submission TIFF was generated in this run. Three concurrent-session candidates also fail the registered lattice check.</p>
  <div class="decision-list"><div class="decision-line"><span>File to download</span><strong>None available</strong></div><div class="decision-line"><span>Estimated leaderboard score</span><strong>Not estimable</strong></div><div class="decision-line"><span>This run: holdout / novelty</span><strong>Blocked before experiment</strong></div></div>
  <a class="decision-link" href="docs/executive-summary.html">Understand the blockers →</a></aside></div></section>
  <div class="facts"><div class="fact"><div class="overline">Best of the nine · unverified</div><div class="fact-number">0.2778</div><p>USER/OWNER-REPORTED · GEMSDOE32 H33-B2</p></div>
  <div class="fact" data-feed-url="docs/data/live-feed.json"><div class="overline">Official public leader · observation</div><div class="fact-number" id="official-score">{e(observed.get('score', 'Unavailable'))}</div><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Leaderboard ↗</a> · <span id="official-date">{e(observed.get('observed_utc', 'unknown'))} · {e(feed['status'])}</span></p></div>
  <div class="fact"><div class="overline">This preflight</div><div class="fact-number">0 / 3</div><p>Geological experiments run / budget · no slot spent</p></div></div>
  <section class="content" id="portfolio"><div class="wrap"><div class="section-head"><div><div class="section-label">01 / The portfolio</div><h2>Nine sites. One honest picture.</h2></div><p class="section-intro">The best user-listed file from each focus site, compared by its reopened pixels—not by filename alone.</p></div>
  {history_table()}</div></section>
  <section class="content" id="evidence"><div class="wrap"><div class="section-head"><div><div class="section-label">02 / What the evidence says</div><h2>A strong result, with limits.</h2></div><p class="section-intro">Separate a useful scientific explanation from a score claim we cannot verify.</p></div><div class="two-col">
  <article class="panel"><div class="overline">Why the reported 0.2778 may lead</div><h3>Less redundant, not necessarily more certain.</h3><p>The pinned H33-B2 support is a subset of the B1 file, with 2,545 fewer positive pixels. The GEMSDOE36 historical file contains B2 plus 1,200 more.</p><p>Under the official distance-weighted metric, thinning can reduce false-positive mass while preserving nearby coverage. Hidden labels and score receipts are unavailable, so this is a plausible mechanism—not a proven cause or a score forecast.</p><a class="mini-link" href="docs/research/audit.html">Read the forensic analysis →</a></article>
  <article class="panel proof"><div class="overline">The hard stop · registry measurement</div><div class="proof-number">{lattice_bound:.2f}%</div><p>Minimum overlap with the registered lattice for <strong>any</strong> 37,654-dot placement in the mirrored footprint. The protocol stops above 70%.</p><div class="proof-grid"><div><strong>99.62%</strong><small>GEMSDOE28 S22C vs lattice</small></div><div><strong>99.17%</strong><small>GEMSDOE36 KPL-36 vs lattice</small></div></div><p class="fineprint">A registered continuous positive-everywhere surface also makes the unchanged literal support rule impossible for any nonempty candidate. A protocol decision is needed; no exemption was invented.</p><a class="mini-link" href="docs/research/concurrent-main.html">See the concurrent candidate recheck →</a></article></div></div></section>
  <section class="content"><div class="wrap"><div class="section-head"><div><div class="section-label">03 / Research direction</div><h2>Curious, but not careless.</h2></div><p class="section-intro">Ranked ideas are hypotheses—not assigned lanes, measured improvements, or submission recommendations.</p></div><div class="cards">
  <article class="card"><div class="number">01 / FIRST TO TEST</div><h3>Displaced magnetic texture</h3><p>Test multi-scale, signed cross-strike texture shifts against gravity contrast. Unfaulted lithologic contacts can mimic the signature.</p></article>
  <article class="card"><div class="number">02 / DATA BLOCKED</div><h3>Compositional contrasts</h3><p>Compare radiometric flank ratios around magnetic edges, with cover and survey bias controls. File-level coverage is not verified.</p></article>
  <article class="card"><div class="number">03 / DATA BLOCKED</div><h3>Repeated terrain steps</h3><p>Look for aligned topographic profile breaks. Shorelines, alluvial terraces and engineered cuts are serious alternatives.</p></article></div>
  <p><a class="mini-link" href="docs/research.html">See all hypotheses &amp; validation plan →</a></p></div></section>
  <section class="content watch"><div class="wrap watch-grid"><div><div class="section-label">04 / Source watch</div><h2 class="article-title">Know when the inputs move.</h2><p class="section-intro" style="margin-top:18px">On page load, the public GitHub API checks current repository heads against the pinned audit refs. A changed head means the audit may be stale; it does not update a score or validate a file.</p>
  <p class="fineprint" id="watch-status" aria-live="polite">JavaScript unavailable: live source heads not checked.</p><button class="button" id="refresh-watch" type="button">Refresh source heads ↻</button>
  <p class="fineprint">The leaderboard observation is separately dated. Automated refresh depends on the Pages workflow; consult the official leaderboard for current results.</p></div><ul class="watch-list" aria-label="Focus site repository status">{watch_rows()}</ul></div></section></main>'''

summary_body = f'''<main id="main"><div class="subhero"><div class="wrap"><div class="section-label">Executive summary / Submission guide</div><h1>The next submission starts here.</h1><p>A practical path from evidence to upload, without mistaking an old file or a format pass for an approved entry.</p></div></div><div class="wrap article">
<section><div class="alert"><strong>NOT OK TO SUBMIT · No new submission TIFF exists.</strong><p>This preflight has no candidate hash, defensible leaderboard estimate or upload note. It ran no experiment and used no weekly slot; the prior parallel-session files are reviewed separately.</p></div>
<h2 style="margin-top:32px">What can I download today?</h2><p>No competition-ready file. Three candidates from concurrent sessions were rechecked and all fail the lattice rule, despite earlier narrower approval claims. Historical files below are linked only for learning and audit. Do not upload or rename them to create an apparent new entry. <a href="research/concurrent-main.html">See the recheck →</a></p>
<div class="table-box" tabindex="0" role="region" aria-label="Candidate status; scroll horizontally"><table><thead><tr><th scope="col">Candidate</th><th scope="col">Estimated leaderboard score</th><th scope="col">Unique vs registry?</th><th scope="col">OK to submit?</th></tr></thead><tbody>{concurrent_rows()}<tr><td>This audit run: <strong>no candidate produced</strong></td><td>Not estimable</td><td>Not applicable</td><td class="blocked">NO</td></tr></tbody></table></div></section>
<section><h2>Why is the gate closed?</h2><ul><li>The prompt refers to a single assigned method lane, but no such paragraph was supplied; the prepared shared feature cache is also absent.</li><li>The shared literal support rule counts every positive cell of a registered continuous surface as support. We measured a positive value over every footprint cell, so every nonempty candidate would exceed the overlap threshold.</li><li>The registered lattice independently forces at least {lattice_bound:.2f}% overlap at the historically common 37,654-dot budget. GEMSDOE28 S22C ({s22_overlap:.2f}%) and GEMSDOE36 KPL-36 ({kpl_overlap:.2f}%) also fail against that lattice, despite narrower site-level claims.</li><li>There is no newly run buffered holdout, per-feature canary, full registry scan, exact saved-byte validation, or account-aware selector decision. No leaderboard prediction is defensible.</li></ul><p><a href="../evidence/portfolio-audit.json">Read the machine audit</a> · <a href="research/audit.html">Read the explanation and proof</a></p></section>
<section><h2>How to make a submission—once authorized</h2><p>The <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">published competition deadline</a> is December 3, 2026 at 23:59 UTC; confirm the current rules before acting.</p><ol><li>Run the frozen lane using the shared prepared features, buffered whole-segment hide-and-recover evaluator and shared writer. Every feature must pass the leakage canary; compare the pooled holdout and paired 95% CI with the best on the <em>same</em> evaluator.</li><li>Check the surface <em>before</em> placement and the final dots with <code>python scripts/check_registry.py</code> against the complete current indexed registry; run it once per phase. A missing raster or duplicate stops the check. A separate selector must confirm slot eligibility.</li><li>Automatically reopen the exact TIFF and verify its hash, one float32 band, template-matching CRS/shape/transform, finite in-footprint values in [0,1], and the nodata/footprint policy. Run <code>python scripts/check_geotiff.py FILE --sample OFFICIAL_SAMPLE</code>. A local format pass is not organizer acceptance.</li><li>Confirm the remaining quota in the authenticated <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData submission page</a>. The <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules PDF §3.4</a> says up to three feedback submissions per week; this account's allowance is unknown.</li><li>Only when the separate selector approves, download that newly generated TIFF, open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData</a>, select <em>Submit → Make new submission</em>, attach it under <em>File to submit</em>, and paste the run card's unique note (at most 140 characters). Verify the filename and hash before upload.</li><li>Save the organizer's score receipt with the file hash, and select one final entry for both prize rounds as required by the rules. Never relabel a projection as a score.</li></ol>
<p><strong>About the range error:</strong> The rejected file's bytes and organizer diagnosis are not available. The owner-mirrored training raster has a large negative nodata sentinel; such a value would fail a [0,1] prediction check if written into a prediction, but we cannot say it caused your error. NaN outside the footprint versus zero-filled values is also unresolved. See <a href="research/audit.html">format caveats</a>.</p></section>
<section><h2>All nine sites, in context</h2><p>These are the highest scores supplied in the request, not independently authenticated organizer receipts. Score values cannot be used to estimate a new file's hidden score.</p>{history_table().replace('href="evidence/', 'href="../evidence/')}</section></div></main>'''

research_body = '''<main id="main"><div class="subhero"><div class="wrap"><div class="section-label">Research / Hypothesis ledger</div><h1>New ideas, tested honestly.</h1><p>Geology motivates a hypothesis. Only a leakage-safe, comparable holdout can test it; neither a proxy nor a publication guarantees the private score.</p></div></div><div class="wrap article">
<section><div class="alert"><strong>No geological experiment was run.</strong><p>No method lane was specified and the shared prepared cache and valid literal uniqueness pathway are missing.</p></div></section>
<section><h2>Ranked proposals</h2><ol><li><strong>Signed cross-strike magnetic texture shifts + gravity.</strong> Seek a stable, oriented displacement of magnetic patterns across a possible trace; a bedrock contact or survey seam may mimic it. Uses competition RTP magnetics and gravity; prepared cache unavailable.</li><li><strong>Radiometric flank asymmetry + magnetic lineaments.</strong> Test contrasting potassium/thorium ratios rather than an isolated edge. Lithology, sediment sorting and radon can mimic it. Public USGS products are listed, but files, coverage and units have not been verified in this sandbox.</li><li><strong>Repeated 3DEP topographic steps.</strong> Search multiple aligned profiles rather than an individual scarp; shoreline, terrace, landslide and road features are competing explanations. Tile-level coverage and bytes not checked.</li><li><strong>Directional geothermal fluid signals.</strong> Evaluate matched multi-site temperature/chemistry trends near independent lineaments. Groundwater mixing and selective surveys are alternatives. GDR lists public resources, but the individual files were not fetched here.</li></ol><p>Expected DTI opportunity is a <strong>qualitative ordering only</strong>; no numerical forecast is claimed. Related hypotheses have been explored in sibling projects; a complete parallel novelty check is not available.</p><p><a href="research/hypotheses.html">Read the complete hypothesis table and frozen test plan →</a></p></section>
<section><h2>Build confidence, not a projection</h2><p>Use whole fault segments and a spatial buffer, derive catalogue features from visible faults only, mask those visible pixels exactly, test every feature alone for leakage, and pool DTI components before calculating a paired spatial-block confidence interval. A catalogue holdout is a proxy and cannot establish the private leaderboard score.</p><p><a href="../evidence/run-card.json">Current negative run card →</a></p></section></div></main>'''

sources_body = '''<main id="main"><div class="subhero"><div class="wrap"><div class="section-label">Sources / Evidence ledger</div><h1>Trace every claim.</h1><p>Official competition and research sources, plus a clear distinction between organizer materials and the owner mirrors used for this audit.</p></div></div><div class="wrap article"><section><h2>Start with the primary sources</h2><ul class="source-list">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData · problem, metric and submission format ↗</a><br>Authoritative challenge description; labels for the private test set are not public.</li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE/NLR · GEMS Prize official rules ↗</a><br>Read the current rules and submission requirements in full.</li>
<li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">DrivenData staff · known-fault masking ↗</a><br>Known fault pixels are excluded; the statement does not extend that exclusion to a surrounding buffer.</li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS · GeoDAWN data release ↗</a><br>Airborne magnetic and radiometric data, surveys and limitations; CC0 stated on the page.</li>
<li><a href="https://www.usgs.gov/publications/aeromagnetic-anomalies-over-faulted-strata">USGS · aeromagnetic anomalies over faulted strata ↗</a><br>Physical motivation; not validation of this project's hypothetical detector.</li>
<li><a href="https://www.usgs.gov/publications/discovery-a-blind-geothermal-system-southern-gabbs-valley-western-nevada-through">USGS · Southern Gabbs Valley blind system ↗</a><br>Case study of multi-scale geothermal exploration without surface hot springs.</li>
<li><a href="https://gdr.openei.org/submissions/1391">GDR · INGENIOUS regional compilation ↗</a><br>Public data listing; landing page states CC BY 4.0. Specific downloaded bytes are not checked here.</li>
<li><a href="https://www.usgs.gov/3d-elevation-program">USGS · 3DEP elevation data ↗</a><br>USGS says its 3DEP products are free. Local tile availability remains unverified.</li></ul>
<p><a href="research/sources.html">Open the complete source ledger and access limitations →</a></p></section><section><h2>Owner files are not organizer receipts</h2><p>Our <a href="../data/inputs.json">input manifest</a> pins public owner-mirror hashes and commit paths. This establishes reproducibility of those bytes, not official origin or the score associated with a submitted file. Competition data and account-specific receipts require access to the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">login-protected data tab</a>.</p></section></div></main>'''

def detail_page(name, title, section, active):
    text = (ROOT / f'docs/research/{name}.md').read_text(encoding='utf-8')
    # The file's first heading is represented by the page's styled hero.
    if text.startswith('# '):
        text = text.split('\n', 1)[1]
    rendered = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    rendered = re.sub(r'(<table>.*?</table>)',
        r'<div class="table-box" tabindex="0" role="region" aria-label="Evidence table; scroll horizontally">\1</div>',
        rendered, flags=re.DOTALL)
    back = '../sources.html' if active == 'Sources' else '../research.html'
    body = f'''<main id="main"><div class="subhero"><div class="wrap"><div class="section-label">{e(section)}</div>
      <h1>{e(title)}</h1><p>Auditable detail from the pinned research record.</p></div></div>
      <div class="wrap article prose"><p><a href="{back}">← Back to {e(active.lower())} overview</a></p>{rendered}</div></main>'''
    return page(title, f'{title} — source and audit details.', '../../', active, body)


outputs = {
    'index.html': page('Overview', 'Evidence-led GEMS competition research and submission status.', '', 'Overview', index_body),
    'docs/executive-summary.html': page('Executive summary', 'Decision and step-by-step GEMS submission guidance.', '../', 'Executive summary', summary_body),
    'docs/research.html': page('Research', 'Ranked geological hypotheses and leakage-safe evaluation.', '../', 'Research', research_body),
    'docs/sources.html': page('Sources', 'Official source ledger and data provenance.', '../', 'Sources', sources_body),
    'docs/research/audit.html': detail_page('audit', 'Nine-site forensic audit', 'Evidence / Audit details', 'Research'),
    'docs/research/hypotheses.html': detail_page('hypotheses', 'Proposed hypotheses, ranked', 'Research / Hypothesis details', 'Research'),
    'docs/research/sources.html': detail_page('sources', 'Official source ledger', 'Sources / Detailed ledger', 'Sources'),
    'docs/research/concurrent-main.html': detail_page('concurrent-main', 'Concurrent candidate recheck', 'Evidence / Parallel sessions', 'Research'),
}
for path, content in outputs.items():
    (ROOT / path).write_text(content + '\n', encoding='utf-8')
    print(path)
