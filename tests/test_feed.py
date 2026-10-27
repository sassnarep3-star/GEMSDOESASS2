import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('refresh_feed', ROOT / 'scripts/refresh_feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

HTML = '''<!doctype html><table><tr><th>Rank</th><th>Team members</th><th>Participant</th>
<th>Best<br>public<br>DW-Tversky<br>(in descending order)</th><th>Shared work</th></tr>
<tr><td>#1</td><td><a href="/x"><img alt="profile"></a></td><td>person<br>5h ago</td><td>0.4544</td><td></td></tr>
<tr><td>#2</td><td></td><td>Other</td><td>0.3916</td><td></td></tr></table>'''


def test_parse_only_rank_one_from_official_table_shape():
    assert feed.parse_leaderboard(HTML) == '0.4544'


@pytest.mark.parametrize('content', [
    '<p>Please log in</p>', HTML.replace('#1', '#10'),
    HTML.replace('DW-Tversky', 'Unrelated'), HTML.replace('0.4544', '2.4'),
    HTML.replace('0.4544', '0.4 projected'),
])
def test_parse_fails_closed_on_unrecognized_html(content):
    with pytest.raises(ValueError):
        feed.parse_leaderboard(content)


def test_failure_preserves_observation_and_marks_stale(tmp_path):
    path = tmp_path / 'feed.json'
    path.write_text(json.dumps({'observation': {'score': '0.1234', 'observed_utc': '2026-01-01'}}))
    result = feed.refresh(path, fetch=lambda: '<html>Login</html>', now='2026-10-27T00:00:00Z')
    assert result['observation']['score'] == '0.1234'
    assert 'stale' in result['status'] and result['last_attempt_utc'] == '2026-10-27T00:00:00Z'


def test_success_records_official_public_observation_not_project_score(tmp_path):
    path = tmp_path / 'feed.json'
    result = feed.refresh(path, fetch=lambda: HTML, now='2026-10-27T00:00:00Z')
    assert result['status'] == 'fresh' and result['observation']['score'] == '0.4544'
    assert 'PUBLIC LEADERBOARD' in result['observation']['evidence_class']
    assert json.loads(path.read_text()) == result
