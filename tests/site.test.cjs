/**
 * Static-site regression tests for the GitHub Pages decision desk.
 *
 * The site became fully static in this revision: the nine-site table is rendered in
 * HTML rather than fetched at runtime, so the page works with JavaScript disabled and
 * cannot silently show a stale "no file approved" verdict. These tests therefore assert
 * on the served HTML directly, and additionally assert that every advertised download
 * exists on disk and matches the SHA-256 recorded in its audit receipt.
 */
const assert = require("node:assert");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const docs = path.join(root, "docs");
const html = fs.readFileSync(path.join(docs, "index.html"), "utf8");
const execSummary = fs.readFileSync(path.join(docs, "executive-summary.html"), "utf8");
const method = fs.readFileSync(path.join(docs, "method.html"), "utf8");
const hvfdHtml = fs.readFileSync(path.join(docs, "hvfd-exp3.html"), "utf8");

const flat = html.replace(/\s+/g, " ");

// ---- the approved submission is unmistakable ------------------------------------
assert.match(flat, /OK to download and submit/i);
assert.match(flat, /Unique submission available/i);
assert.match(execSummary, /OK TO DOWNLOAD AND SUBMIT/);
assert.match(execSummary, /research only/i);
assert.match(execSummary, /MODEL ESTIMATE/);
// The file the lattice clause blocks is named, not glossed over (IR-31-03 demotes it).
assert.match(execSummary, /gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros\.tif/);
assert.match(execSummary, /RESEARCH ONLY/);
assert.match(method, /0\.2778/);

// ---- the headline download is a real file with a verifiable hash -----------------
const downloadMatch = html.match(/href="(downloads\/[^"]+-zeros\.tif)"\s+download/);
assert.ok(downloadMatch, "homepage must carry a one-click download of the primary TIF");
const downloadPath = path.join(docs, downloadMatch[1]);
assert.ok(fs.existsSync(downloadPath), `advertised download missing: ${downloadMatch[1]}`);

// ---- the promoted card is unique and its bytes are the advertised bytes ---------
// As of 2026-10-31 the promoted artifact carries the v3 run card at
// docs/data/run-card-20261031.json (mirrored in evidence/). Legacy `*-audit.json`
// cards may still exist but none of them may claim promotion any more.
const auditFiles = fs
  .readdirSync(path.join(docs, "downloads"))
  .filter((name) => name.endsWith("-audit.json"));
const legacyPromoted = auditFiles
  .map((name) => JSON.parse(fs.readFileSync(path.join(docs, "downloads", name), "utf8")))
  .filter((c) => c.verdict === "promote" && c.ok_to_download_and_submit);
assert.equal(legacyPromoted.length, 0,
  "the 2026-10-30 promoted audit card must have been demoted (IR-31-03)");

const card = JSON.parse(fs.readFileSync(path.join(docs, "data", "run-card-20261031.json"), "utf8"));
assert.equal(card.verdict, "promote-with-caveat", "the reviewed verdict must be published");
assert.equal(card.weekly_slots_spent, 0, "no submission slot may have been spent");
assert.ok(flat.includes(path.basename(downloadPath)), "homepage must advertise the promoted file");
assert.equal(card.validator.zeros.strict_local_format_pass, true, "promoted file must pass format");
assert.equal(card.validator.zeros.portal_range_safe, true, "ship the range-safe encoding");
assert.equal(card.uniqueness.passes_lane, true, "promoted file must pass the lane gate");
assert.ok(card.uniqueness.max_overlap_3px_pct <= 70, "3-px overlap must be inside 70%");
assert.ok(card.uniqueness.max_abs_spearman <= 0.9, "|Spearman| must be inside 0.90");
assert.ok(card.submission.note.length <= 140, "submission note must fit 140 characters");
// The science gate is negative and the card must say so rather than hide it.
assert.ok(card.holdout_dti.candidate.P_SGMC2 < card.holdout_dti.champion_GEMSDOE32.P_SGMC2,
  "the proxy shortfall must be recorded");
assert.match(card.holdout_dti.verdict, /NEGATIVE/);

const digest = crypto.createHash("sha256").update(fs.readFileSync(downloadPath)).digest("hex");
assert.equal(digest, card.validator.zeros.candidate_sha256,
  "advertised bytes must match the run card");

// ---- the nine-site table is present, complete and honest ------------------------
const sites = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
  "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"];
for (const site of sites) assert.ok(execSummary.includes(site), `missing focus site ${site}`);
assert.ok(execSummary.includes("0.2778"), "the champion value must appear");
assert.ok(execSummary.includes("USER-REPORTED"), "historical values must be marked unverified");
assert.match(execSummary, /MODEL ESTIMATE/);
assert.doesNotMatch(execSummary, /ORGANIZER-CONFIRMED\s*[:=]?\s*0\./i);

// ---- no research artifact may be presented as submittable ----------------------
assert.match(hvfdHtml, /DO NOT SUBMIT/i);
assert.doesNotMatch(hvfdHtml, /VERDICT: PROMOTE/i);

// ---- no local-only hosts may leak into a published page ------------------------
for (const page of [html, execSummary, method]) {
  assert.doesNotMatch(page, /localhost|127\.0\.0\.1/);
}

console.log("site: static decision desk passed");
