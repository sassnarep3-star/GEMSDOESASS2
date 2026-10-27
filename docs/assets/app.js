(() => {
  "use strict";
  const table = document.querySelector("[data-sites-body]");
  const freshness = document.querySelector("[data-freshness]");
  const refresh = document.querySelector("[data-refresh]");
  let snapshot = null;
  const element = (tag, text, className) => {
    const el = document.createElement(tag);
    if (text != null) el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  const link = (href, text) => {
    const a = element("a", text);
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  };
  function renderSites(sites) {
    if (!table) return;
    table.replaceChildren();
    [...sites]
      .sort((a, b) => b.reported - a.reported)
      .forEach((site) => {
        const row = element("tr");
        const name = element("td");
        name.append(link(site.site_url, site.site));
        const value = element("td");
        value.append(
          element("strong", Number(site.reported).toFixed(4)),
          element("small", "User-reported; no receipt"),
        );
        const file = element("td");
        file.append(element("span", "No file approved", "negative"));
        const detail = element("small", null, "file");
        detail.append(
          link(site.artifact_url, site.path.split("/").pop()),
          document.createTextNode(" · archived variant, research only"),
        );
        file.append(detail);
        const estimate = element("td", "Unavailable");
        estimate.append(element("small", "No defensible leaderboard estimate"));
        const novelty = element("td");
        novelty.append(
          element("span", "No", "negative"),
          element(
            "small",
            `${(site.max_overlap_fraction * 100).toFixed(2)}% within 3 px of ${site.max_overlap_peer}`,
          ),
        );
        row.append(name, value, file, estimate, novelty);
        table.append(row);
      });
  }
  async function currentRef(site) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
    try {
      const url = `https://api.github.com/repos/buffedlizard55-lab/${encodeURIComponent(site.site)}/commits/main`;
      const response = await fetch(url, {
        headers: { Accept: "application/vnd.github+json" },
        signal: controller.signal,
        cache: "no-store",
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!/^[a-f0-9]{40}$/.test(data.sha || ""))
        throw new Error("Missing commit SHA");
      return { site: site.site, changed: data.sha !== site.observed_main_ref };
    } finally {
      clearTimeout(timer);
    }
  }
  async function checkFreshness() {
    if (!snapshot || !freshness || !refresh) return;
    refresh.disabled = true;
    freshness.textContent = "Checking GitHub repository heads…";
    const checked = await Promise.allSettled(
      snapshot.historical_sites.map(currentRef),
    );
    const unknown = checked.filter((r) => r.status === "rejected").length;
    const changed = checked
      .filter((r) => r.status === "fulfilled" && r.value.changed)
      .map((r) => r.value.site);
    const time = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
    let message;
    if (unknown)
      message = `Source watch incomplete (${unknown} unavailable; possibly rate-limited).`;
    else if (changed.length)
      message = `New commits: ${changed.join(", ")}. A changed ref is not proof of a new raster.`;
    else message = "Repository heads match the recorded snapshot.";
    freshness.textContent = `${message} Checked ${time}. This does not certify registry completeness or authorize a submission.`;
    refresh.disabled = false;
  }
  const needsData = table || (freshness && refresh);
  if (!needsData) return;
  fetch("data/audit.json", { cache: "no-store" })
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((data) => {
      if (
        !Array.isArray(data.historical_sites) ||
        data.historical_sites.length !== 9
      )
        throw new Error("Incomplete snapshot");
      snapshot = data;
      renderSites(data.historical_sites);
      document.querySelectorAll("[data-audit-time]").forEach((el) => {
        el.textContent = data.audited_utc;
      });
      if (refresh) refresh.addEventListener("click", checkFreshness);
      if (freshness && refresh) checkFreshness();
    })
    .catch(() => {
      if (table) {
        table.replaceChildren();
        const row = element("tr");
        const cell = element(
          "td",
          "Evidence unavailable. Open the audit JSON directly; do not infer that any file is approved.",
        );
        cell.colSpan = 5;
        row.append(cell);
        table.append(row);
      }
      if (freshness)
        freshness.textContent =
          "Evidence or source watch unavailable. Submission remains blocked.";
      if (refresh) refresh.disabled = true;
    });
})();
