from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


class ParsePage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.text = []
        self.main = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'):
            assert values['id'] not in self.ids, f"Duplicate id {values['id']}"
            self.ids.add(values['id'])
        if tag == 'main': self.main += 1
        for attr in ('href', 'src'):
            if values.get(attr): self.links.append(values[attr])
        if tag == 'a' and values.get('target') == '_blank':
            assert 'noopener' in values.get('rel', '').split()

    def handle_data(self, data): self.text.append(data)


def test_site_links_and_accessible_main():
    pages = {}
    for path in DOCS.glob('*.html'):
        page = ParsePage(); page.feed(path.read_text()); pages[path.resolve()] = page
        assert page.main == 1
        assert any('Skip to content' in text for text in page.text)
    assert len(pages) >= 4
    for page_path, page in pages.items():
        for link in page.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc: continue
            target = (page_path.parent / unquote(parsed.path)).resolve() if parsed.path else page_path
            assert target.exists(), f'{page_path}: broken link {link}'
            if parsed.fragment and target.suffix == '.html':
                assert target in pages and parsed.fragment in pages[target].ids, f'{page_path}: missing anchor {link}'


def test_pages_root_redirects_to_docs_with_fallback():
    text = (ROOT / 'index.html').read_text()
    assert 'url=docs/' in text
    assert 'href="docs/"' in text


def test_homepage_advertises_the_download_and_blocks_submission():
    # The TIF is downloadable, but the lattice gate fails (99.74% > 70%).
    # The homepage must say BLOCKED and must not say OK to submit.
    text = (DOCS / 'index.html').read_text()
    flat = ' '.join(text.split())
    assert 'BLOCKED — DO NOT SUBMIT YET' in flat
    assert 'OK to download and submit' not in flat
    assert 'Download the TIF' in flat
    assert '99.74%' in flat
    assert '30.3%' in flat and '41.3%' in flat
    assert 'gemsdoesass2-sparse-blind-conduit-22163' in flat
    assert 'focus-sites.html' in text


def test_hvfd_candidate_is_marked_do_not_submit():
    text = ' '.join((DOCS / 'hvfd-exp3.html').read_text().split())
    assert 'DO NOT SUBMIT THIS FILE' in text
    assert '70.58%' in text
    assert 'Hedge-v2' in text


def test_focus_sites_page_has_every_site_and_a_main_landmark():
    text = (DOCS / 'focus-sites.html').read_text()
    for site in ('GEMSDOE24', 'GEMSDOE25', 'GEMSDOE27', 'GEMSDOE28', 'GEMSDOE30',
                 'GEMSDOE31', 'GEMSDOE32', 'GEMSDOE33', 'GEMSDOE36'):
        assert f'<b>{site}</b>' in text, site
    assert '<main id="main">' in text
    assert 'NOT ESTIMABLE' in text
    # A candidate that fails the literal lattice gate must not be presented in green
    # or described as eligible even if its restricted genuine-raster comparison is best.
    assert 'Research-only comparison leader — NOT approved for download or submission' in text
    assert '<div class="banner good"><b>Research-only' not in text
    assert 'No checksum mismatches were recorded' in text
    assert 'not a general clean bill' in text
