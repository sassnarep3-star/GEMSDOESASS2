"use strict";

// Static-site safety checks: no stale historical run card may be rendered as approval.
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const root = path.join(__dirname, "..");
const docs = path.join(root, "docs");
const html = fs.readFileSync(path.join(docs, "index.html"), "utf8");
const execSummary = fs.readFileSync(path.join(docs, "executive-summary.html"), "utf8");
const method = fs.readFileSync(path.join(docs, "method.html"), "utf8");
const report = fs.readFileSync(path.join(root, "research/2026-10-31-repo-review.md"), "utf8");
const runCard = JSON.parse(fs.readFileSync(path.join(root, "evidence/review_run_card_20261031.json"), "utf8"));
const flat = html.replace(/\s+/g, " ");

assert.match(flat, /no repository TIF is cleared/i);
assert.match(flat, /DO NOT SUBMIT/i);
assert.match(flat, /NOT ESTIMABLE/i);
assert.match(execSummary, /0\.2778/);
assert.match(execSummary, /USER-REPORTED \/ UNVERIFIED/);
assert.match(execSummary, /NOT ESTIMABLE/);
assert.match(execSummary, /Unique vs focus sites\?/);
assert.doesNotMatch(execSummary, /OK TO DOWNLOAD AND SUBMIT/);
assert.match(method, /why.*0\.2778/is);

// Nine-site summary is complete, references historic artifacts, and has no estimated score.
const sites = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
  "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"];
for (const site of sites) {
  assert.ok(execSummary.includes(site), `missing focus site ${site}`);
  assert.ok(report.includes(site), `missing audited row for ${site}`);
}
assert.match(report, /USER-REPORTED \/ UNVERIFIED/);
assert.match(report, /NOT ESTIMABLE/);
assert.equal(runCard.verdict, "negative");
assert.equal(runCard.experiments_run_this_review, 0);
assert.equal(runCard.leaderboard_score_estimate.label, "NOT ESTIMABLE");
assert.equal(runCard.weekly_submission_slots_used, 0);

// Policy resolution 2026-10-31 (IR-S-41). PR #33 encoded a blanket ban: no page may advertise any TIF.
// The owner's standing instruction is the opposite — one file must be obviously downloadable when the project's
// own gates clear it, and no human inspector is involved. The ban is therefore replaced by the invariant that
// actually protects us: a download link on the active page is legal only if exactly one promoted audit covers
// that byte string, every other linked artifact is labelled research, and the superseded headline is never
// offered as a submission.
const fs2 = require("node:fs");
const dl = path.join(docs, "downloads");
const audits = fs2.readdirSync(dl).filter(f => f.endsWith("-audit.json"))
  .map(f => JSON.parse(fs2.readFileSync(path.join(dl, f), "utf8")));
const promoted = audits.filter(a => a.verdict === "promote" && a.ok_to_download_and_submit);
assert.equal(promoted.length, 1, `exactly one promoted card may exist, found ${promoted.length}`);
const crypto = require("node:crypto");
const sha = f => crypto.createHash("sha256").update(fs2.readFileSync(path.join(dl, f))).digest("hex");
assert.equal(sha(promoted[0].artifact), promoted[0].raster_sha256, "promoted bytes must match the audit");
assert.match(html, new RegExp(`href="downloads/${promoted[0].artifact}" download`),
  "the promoted artifact must be a one-click download on the front page");
assert.doesNotMatch(html, /href="downloads\/gemsass2-strainridge-offcat-[^"]+" download/,
  "a superseded headline may never be offered as a download");
for (const m of html.matchAll(/href="downloads\/([^"]+\.tif)" download/g)) {
  const linked = m[1];
  const stem = promoted[0].artifact.replace(/-zeros\.tif$/, "");
  const cleared = linked === promoted[0].artifact || linked.startsWith(`format-${stem}`) ||
    // the GIS twin of the promoted raster is the same emission with NaN outside; it is linked with an
    // explicit "not the portal file" label, so it is admitted by stem identity, not by a second promotion.
    (linked.startsWith(`${stem}-`) && linked.endsWith("-nan.tif")) ||
    audits.some(a => a.artifact === linked && a.verdict === "promote" && a.ok_to_download_and_submit);
  if (!cleared) {
    const around = html.slice(Math.max(0, m.index - 3000), m.index + 300);
    assert.match(around, /DO NOT SUBMIT|research/i, `unlabelled non-promoted download link: ${linked}`);
  }
}
assert.match(html, /executive-summary\.html/);

for (const page of [html, execSummary, method]) {
  assert.doesNotMatch(page, /localhost|127\.0\.0\.1/);
}
console.log("site: decision desk passed (one receipt-backed promotion, research labelled, no score claim)");
