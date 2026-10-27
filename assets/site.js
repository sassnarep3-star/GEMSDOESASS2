/* Public metadata only: never infer a score, approval, or raster novelty. */
(() => {
  const feed = document.querySelector('[data-feed-url]');
  if (feed) {
    fetch(feed.dataset.feedUrl, {cache: 'no-store'})
      .then(r => { if (!r.ok) throw new Error('feed unavailable'); return r.json(); })
      .then(data => {
        const item = data.observation;
        const score = document.getElementById('official-score');
        const when = document.getElementById('official-date');
        if (!item || typeof item.score !== 'string' || !/^(?:0(?:\.\d+)?|1(?:\.0+)?)$/.test(item.score)) {
          if (score) score.textContent = 'Unavailable';
          if (when) when.textContent = data.status || 'No valid observation available';
          return;
        }
        if (score) score.textContent = item.score;
        if (when) when.textContent = `${item.observed_utc} · ${data.status}`;
      }).catch(() => {
        const when = document.getElementById('official-date');
        if (when) when.textContent += ' · feed unavailable';
      });
  }

  const states = Array.from(document.querySelectorAll('[data-repo][data-pin]'));
  const status = document.getElementById('watch-status');
  const refresh = document.getElementById('refresh-watch');
  async function checkSources() {
    if (!states.length) return;
    if (refresh) refresh.disabled = true;
    if (status) status.textContent = 'Checking public GitHub repository heads…';
    let checked = 0;
    await Promise.all(states.map(async (element) => {
      const name = element.dataset.repo;
      if (!/^GEMSDOE(?:24|25|27|28|30|31|32|33|36)$/.test(name)) return;
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 10000);
      try {
        const url = `https://api.github.com/repos/buffedlizard55-lab/${name}/commits/main`;
        const response = await fetch(url, {signal: controller.signal, cache: 'no-store'});
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (!/^[a-f0-9]{40}$/.test(data.sha)) throw new Error('bad revision');
        checked++;
        element.textContent = data.sha === element.dataset.pin ? 'matches pinned ref' : `newer/different head · ${data.sha.slice(0, 7)}`;
      } catch (_) {
        element.textContent = 'unavailable / rate limited';
      } finally { clearTimeout(timer); }
    }));
    if (status) status.textContent = `${checked}/${states.length} public heads checked at ${new Date().toISOString().replace('T',' ').slice(0,19)} UTC. This does not refresh scores or re-audit files.`;
    if (refresh) refresh.disabled = false;
  }
  if (refresh) refresh.addEventListener('click', checkSources);
  checkSources();
})();
