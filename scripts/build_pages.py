#!/usr/bin/env python3
"""Stage an explicit public-site allowlist; never publish cached/unapproved TIFFs."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    '.nojekyll', 'index.html',
    'assets/site.css', 'assets/site.js',
    'docs/index.html', 'docs/ass2-altedge.html', 'docs/ass2-executive-summary.html',
    'docs/executive-summary.html', 'docs/research.html', 'docs/sources.html',
    'docs/data/live-feed.json',
    'docs/research/audit.md', 'docs/research/audit.html',
    'docs/research/concurrent-main.md', 'docs/research/concurrent-main.html',
    'docs/research/hypotheses.md', 'docs/research/hypotheses.html',
    'docs/research/sources.md', 'docs/research/sources.html',
    'docs/research/prior-recorded-prompt.md',
    'data/inputs.json', 'data/template.json', 'data/registry.json', 'data/concurrent.json',
    'data/training-mirror.json',
    'evidence/portfolio-audit.json', 'evidence/concurrent-main-audit.json',
    'evidence/run-card.json', 'evidence/raw-mirror-metadata.json',
    'evidence/gemsdoe31-format-audit.json', 'evidence/kpl36-format-audit.json',
)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT / '_site')
    args = p.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT not in out.parents or out.name != '_site':
        raise SystemExit('Output must be an _site directory inside the repository')
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in PUBLIC_FILES:
        source = ROOT / name
        if not source.is_file():
            raise SystemExit(f'Missing required public file: {name}')
        dest = out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    print(f'Static Pages staged in {out}; no cache or unapproved TIFFs included')


if __name__ == '__main__':
    main()
