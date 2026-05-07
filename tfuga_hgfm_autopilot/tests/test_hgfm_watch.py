from pathlib import Path

import tfuga_hgfm_autopilot.scripts.hgfm_watch as hgfm_watch
from tfuga_hgfm_autopilot.scripts.hgfm_watch import has_danger, is_blocked


def test_blocks_env_file(tmp_path: Path) -> None:
    target = tmp_path / '.env'
    target.write_text('placeholder')
    assert is_blocked(target)


def test_blocks_large_file_without_writing_large_blob(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / 'large.txt'
    target.write_text('small placeholder')
    monkeypatch.setattr(hgfm_watch, 'MAX_FILE_MB', 0.000001)
    assert is_blocked(target)


def test_detects_sensitive_marker(tmp_path: Path) -> None:
    repo = tmp_path
    target = repo / 'note.txt'
    marker = 'TO' + 'KEN='
    target.write_text(marker + 'placeholder')
    dangers = has_danger(repo, [target])
    assert dangers
