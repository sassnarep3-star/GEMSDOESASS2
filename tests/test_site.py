from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and ((tag == 'a' and key == 'href') or
                          (tag == 'link' and key == 'href') or
                          (tag == 'script' and key == 'src')):
                self.paths.append(value)


def test_generated_pages_have_valid_local_links_and_clear_negative_state():
    for page in [ROOT / 'index.html', ROOT / 'docs/executive-summary.html',
                 ROOT / 'docs/research.html', ROOT / 'docs/sources.html',
                 ROOT / 'docs/research/audit.html', ROOT / 'docs/research/hypotheses.html',
                 ROOT / 'docs/research/sources.html', ROOT / 'docs/research/concurrent-main.html']:
        content = page.read_text()
        parser = LocalLinks()
        parser.feed(content)
        for href in parser.paths:
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            assert (page.parent / url.path).exists(), (page, href)
    index = (ROOT / 'index.html').read_text()
    summary = (ROOT / 'docs/executive-summary.html').read_text()
    assert 'No new file is cleared.' in index
    assert 'No competition-ready file' in summary
    assert 'Not estimable' in index and 'NOT OK TO SUBMIT' in summary
    assert index.count('DO NOT RESUBMIT') == 9


def test_build_pages_stages_no_cached_rasters(tmp_path):
    # Staging is intentionally restricted to a safe _site dir inside the repo.
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_pages.py')],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    output = ROOT / '_site'
    assert (output / 'index.html').exists()
    assert not (output / '.cache').exists()
    assert not list(output.rglob('*.tif'))
