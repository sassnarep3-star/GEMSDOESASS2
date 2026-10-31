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

// The old file remains in the archive, but the active page must not advertise a TIF download.
assert.doesNotMatch(html, /href="downloads\/[^"]+\.tif"\s+download/);
assert.doesNotMatch(html, /OK to download and submit/i);
assert.match(html, /executive-summary\.html/);

for (const page of [html, execSummary, method]) {
  assert.doesNotMatch(page, /localhost|127\.0\.0\.1/);
}
console.log("site: fail-closed decision desk passed");
