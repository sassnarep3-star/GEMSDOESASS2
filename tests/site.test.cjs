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
assert.match(execSummary, /gemsass2-strainridge-offcat-37654d/i);
assert.match(method, /why.*0\.2778/is);

// ---- the headline download is a real file with a verifiable hash -----------------
const downloadMatch = html.match(/href="(downloads\/[^"]+-zeros\.tif)"\s+download/);
assert.ok(downloadMatch, "homepage must carry a one-click download of the primary TIF");
const downloadPath = path.join(docs, downloadMatch[1]);
assert.ok(fs.existsSync(downloadPath), `advertised download missing: ${downloadMatch[1]}`);

const auditFiles = fs
  .readdirSync(path.join(docs, "downloads"))
  .filter((name) => name.endsWith("-audit.json"));
const promoted = auditFiles
  .map((name) => JSON.parse(fs.readFileSync(path.join(docs, "downloads", name), "utf8")))
  .filter((card) => card.verdict === "promote" && card.ok_to_download_and_submit);

assert.equal(promoted.length, 1, "exactly one promoted submission may be advertised");
const card = promoted[0];
assert.ok(flat.includes(path.basename(downloadPath)), "homepage must advertise the promoted file");
assert.equal(card.validator_output.all_passed, true, "promoted file must pass every format check");
assert.equal(card.correlation_overlap_vs_registry.passes_lane, true, "promoted file must pass the lane gate");
assert.ok(card.submission_note_140.length <= 140, "submission note must fit 140 characters");

const digest = crypto.createHash("sha256").update(fs.readFileSync(downloadPath)).digest("hex");
assert.equal(digest, card.raster_sha256, "advertised bytes must match the audit receipt");

// ---- the nine-site table is present, complete and honest ------------------------
const sites = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
  "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"];
for (const site of sites) assert.ok(html.includes(site), `missing focus site ${site}`);
assert.match(flat, /GEMSDOE32/);
assert.ok(flat.includes("0.2778"), "the champion value must appear");
assert.ok(flat.includes("USER-REPORTED"), "historical values must be marked unverified");

// ---- no research artifact may be presented as submittable ----------------------
assert.match(hvfdHtml, /DO NOT SUBMIT/i);
assert.doesNotMatch(hvfdHtml, /VERDICT: PROMOTE/i);

// ---- no local-only hosts may leak into a published page ------------------------
for (const page of [html, execSummary, method]) {
  assert.doesNotMatch(page, /localhost|127\.0\.0\.1/);
}

console.log("site: static decision desk passed");
