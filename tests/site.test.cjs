const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { JSDOM } = require("jsdom");

const root = path.join(__dirname, "..", "docs");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const app = fs.readFileSync(path.join(root, "assets/app.js"), "utf8");
const hvfdHtml = fs.readFileSync(path.join(root, "hvfd-exp3.html"), "utf8");
const execSummary = fs.readFileSync(path.join(root, "executive-summary.html"), "utf8");
const currentRunCard = JSON.parse(
  fs.readFileSync(path.join(root, "data/run-card.json"), "utf8"),
);
assert.equal(currentRunCard.verdict, "negative");
assert.equal(currentRunCard.ok_to_submit, false);
assert.match(html, /NOT CLEARED FOR SUBMISSION/i);
assert.doesNotMatch(html, /OK to download and submit/i);
assert.match(execSummary, /NOT CLEARED FOR SUBMISSION/i);
assert.doesNotMatch(execSummary, /OK TO DOWNLOAD AND SUBMIT/i);
assert.match(execSummary, /research only/i);
assert.match(execSummary, /gemsdoesass2-sparse-blind-conduit-22163/i);
assert.match(hvfdHtml, /DO NOT SUBMIT/i);
assert.match(hvfdHtml, /research only/i);
assert.doesNotMatch(hvfdHtml, /VERDICT: PROMOTE/i);
const data = JSON.parse(
  fs.readFileSync(path.join(root, "data/audit.json"), "utf8"),
);
const settle = () => new Promise((resolve) => setTimeout(resolve, 80));

async function check(mode) {
  const dom = new JSDOM(html, {
    url: "http://localhost:8000/",
    runScripts: "outside-only",
  });
  dom.window.AbortController = AbortController;
  dom.window.fetch = async (url) => {
    if (url === "data/audit.json") {
      if (mode === "missing") return { ok: false, status: 404 };
      return { ok: true, json: async () => data };
    }
    const name = url.split("/")[5];
    if (mode === "limited") return { ok: false, status: 403 };
    const site = data.historical_sites.find((x) => x.site === name);
    assert.ok(site, `unexpected source: ${url}`);
    return {
      ok: true,
      json: async () => ({
        sha:
          mode === "changed" && name === "GEMSDOE24"
            ? "a".repeat(40)
            : site.observed_main_ref,
      }),
    };
  };
  dom.window.eval(app);
  await settle();
  const doc = dom.window.document;
  if (mode === "missing") {
    assert.match(
      doc.querySelector("[data-sites-body]").textContent,
      /Evidence unavailable/,
    );
    assert.equal(doc.querySelector("[data-refresh]").disabled, true);
  } else {
    const rows = [...doc.querySelectorAll("[data-sites-body] tr")];
    assert.equal(rows.length, 9);
    assert.match(rows[0].textContent, /GEMSDOE32.*0\.2778/s);
    assert.equal(
      rows.filter((row) => row.textContent.includes("No file approved")).length,
      9,
    );
    assert.equal(
      rows.filter((row) => row.textContent.includes("Unavailable")).length,
      9,
    );
    const status = doc.querySelector("[data-freshness]").textContent;
    if (mode === "limited") assert.match(status, /incomplete/);
    if (mode === "changed") assert.match(status, /New commits: GEMSDOE24/);
    if (mode === "ok") assert.match(status, /heads match/);
    assert.match(status, /does not certify registry completeness/);
  }
  // The homepage now advertises an active download (no disabled button).
  dom.window.close();
  console.log(`site: ${mode} passed`);
}

(async () => {
  for (const mode of ["ok", "changed", "limited", "missing"]) await check(mode);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
