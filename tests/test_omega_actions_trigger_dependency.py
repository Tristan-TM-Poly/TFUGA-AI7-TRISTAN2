from __future__ import annotations

from pathlib import Path

from omega_actions_t.trigger_dependency import audit_trigger_dependency


def _workflow(root: Path, name: str, job: str) -> None:
    path = root / ".github" / "workflows" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'on:\n  pull_request:\n    paths:\n      - "pyproject.toml"\n      - "src/**"\njobs:\n'
        + job
        + "\n",
        encoding="utf-8",
    )


def test_no_runtime_signal_is_candidate(tmp_path: Path) -> None:
    _workflow(
        tmp_path,
        "a.yml",
        "  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest -q tests/test_a.py",
    )
    report = audit_trigger_dependency(tmp_path, "pyproject.toml")
    assert report["workflows"][0]["status"] == "NO_DIRECT_RUNTIME_SIGNAL"
    assert report["workflows"][0]["migration_candidate"] is True


def test_project_install_signal_blocks_candidate(tmp_path: Path) -> None:
    _workflow(
        tmp_path,
        "a.yml",
        "  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: python -m pip install -e .",
    )
    row = audit_trigger_dependency(tmp_path, "pyproject.toml")["workflows"][0]
    assert row["status"] == "PROJECT_INSTALL_SIGNAL"
    assert row["migration_candidate"] is False


def test_direct_runtime_reference_blocks_candidate(tmp_path: Path) -> None:
    _workflow(
        tmp_path,
        "a.yml",
        "  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: cat pyproject.toml",
    )
    row = audit_trigger_dependency(tmp_path, "pyproject.toml")["workflows"][0]
    assert row["status"] == "DIRECT_RUNTIME_REFERENCE"
    assert row["migration_candidate"] is False
