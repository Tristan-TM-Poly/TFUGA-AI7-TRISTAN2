from pathlib import Path

from tfuga_hgfm_autopilot.scripts.hgfm_watch import is_blocked, has_danger


def test_blocks_env_file(tmp_path: Path) -> None:
    target = tmp_path / '.env'
    target.write_text('placeholder')
    assert is_blocked(target)


def test_blocks_large_file(tmp_path: Path) -> None:
    target = tmp_path / 'large.txt'
    target.write_bytes(b'0' * (26 * 1024 * 1024))
    assert is_blocked(target)


def test_detects_sensitive_marker(tmp_path: Path) -> None:
    repo = tmp_path
    target = repo / 'note.txt'
    marker = 'TO' + 'KEN='
    target.write_text(marker + 'placeholder')
    dangers = has_danger(repo, [target])
    assert dangers
