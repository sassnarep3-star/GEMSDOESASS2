#!/usr/bin/env python3
"""Refresh an attributed public leaderboard observation, never a file score.

The scheduled Pages build runs this without credentials. On network/HTML
failure the last checked-in observation is retained and explicitly marked stale.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request

URL = 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if self.skip:
            return
        if tag == 'table' and self.table is None:
            self.table = []
        elif tag == 'tr' and self.table is not None:
            self.row = []
        elif tag in ('th', 'td') and self.row is not None:
            self.cell = []
        elif tag == 'br' and self.cell is not None:
            self.cell.append(' ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
            return
        if self.skip:
            return
        if tag in ('th', 'td') and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None

    def handle_data(self, data):
        if not self.skip and self.cell is not None:
            self.cell.append(data)


def parse_leaderboard(html: str) -> str:
    """Return #1 score only from an identified leaderboard table, or fail."""
    parser = Tables()
    parser.feed(html)
    for table in parser.tables:
        for header_pos, header in enumerate(table):
            score_columns = [i for i, text in enumerate(header) if 'tversky' in text.lower()]
            rank_columns = [i for i, text in enumerate(header) if 'rank' in text.lower()]
            if len(score_columns) != 1 or len(rank_columns) != 1:
                continue
            score_col, rank_col = score_columns[0], rank_columns[0]
            for row in table[header_pos + 1:]:
                if max(score_col, rank_col) >= len(row):
                    continue
                if not re.fullmatch(r'\s*#?\s*1\s*', row[rank_col]):
                    continue
                score = row[score_col].strip()
                if not re.fullmatch(r'(?:0(?:\.\d+)?|1(?:\.0+)?)', score):
                    raise ValueError('rank-one score cell has unexpected contents')
                return score
    raise ValueError('official leaderboard rank-one table was not identified')


def refresh(path: Path, *, fetch=None, now=None):
    old = json.loads(path.read_text()) if path.exists() else {}
    now = now or datetime.now(timezone.utc).isoformat()
    result = {'schema': 'gems-public-feed-v1', 'last_attempt_utc': now, 'source': URL,
              'explanation': 'Official public rank-one observation only; not a receipt or score for any project file.'}
    try:
        if fetch is None:
            req = urllib.request.Request(URL, headers={'User-Agent': 'GEMS-research-audit/1.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                content = response.read(5_000_000).decode('utf-8', errors='replace')
        else:
            content = fetch()
        score = parse_leaderboard(content)
        result.update(status='fresh', observation={'rank': 1, 'score': score,
                      'observed_utc': now, 'evidence_class': 'OFFICIAL PUBLIC LEADERBOARD OBSERVATION'})
    except Exception as exc:
        # Preserve only an already recorded observation. Never fabricate one.
        result.update(status='unavailable; last observation may be stale',
                      observation=old.get('observation'), error_type=type(exc).__name__)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('docs/data/live-feed.json'))
    args = parser.parse_args()
    result = refresh(args.output)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
