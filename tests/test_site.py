from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(p):
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()
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


def test_homepage_advertises_the_approved_unique_submission():
    # The promoted submission passed every local gate: 11/11 strict format checks,
    # genuine-peer uniqueness max overlap 28.10% < 70%, max|rho| 0.0215 < 0.90, and a
    # blocked holdout of 0.2244 versus 0.0715 for the matched lattice control
    # (see docs/downloads/gemsass2-slopetilt-300k-20261031-audit.json).
    text = (DOCS / 'index.html').read_text()
    flat = ' '.join(text.split())
    assert 'OK to download and submit' in flat
    assert '11/11' in flat
    assert '28.10%' in flat
    assert 'gemsass2-slopetilt-300k-20261031' in flat
    # The download must be a real, one-click file link, not a link to prose.
    assert 'href="downloads/gemsass2-slopetilt-300k-20261031-zeros.tif"' in text
    assert (DOCS / 'downloads/gemsass2-slopetilt-300k-20261031-zeros.tif').exists()
    # The failing lattice clause must be disclosed on the homepage.
    assert 'lattice' in flat.lower()

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

def test_homepage_labels_sibling_research_files_and_keeps_the_failing_clause_visible():
    """Merged from PR #33's fail-closed page policy (origin/main), adapted to a page that now promotes a
    file which clears both literal gate tests. The parts that encoded "nothing is cleared" were replaced by
    the parts that must hold forever: research files stay marked research, no score is claimed as
    organizer-confirmed, the failing lattice clause is stated on the page, and a superseded headline is never
    offered as a one-click download (IR-S-25, IR-S-41)."""
    text = (DOCS / 'index.html').read_text()
    flat = ' '.join(text.split())
    assert 'DO NOT SUBMIT' in flat, "sibling research artifacts must be labelled"
    assert 'NOT ESTIMABLE' in flat, "local score prediction must stay marked not estimable"
    assert 'GEMSDOE32' in flat and '0.2778' in flat
    assert 'lattice' in flat.lower(), "the failing lattice clause must be disclosed"
    assert 'href="downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif"' not in text
    for name in ('gemsdoesass2-stepperelay-dilation-22163-49c96b30-zeros.tif',
                 'gemsdoesass2-damage-edge-22163-20261031T045913Z-4eacecbc-zeros.tif'):
        assert (DOCS / 'downloads' / name).exists(), name
        assert name in flat
