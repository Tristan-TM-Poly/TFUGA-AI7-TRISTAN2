from __future__ import annotations

import subprocess
from importlib.metadata import distribution


def test_distribution_metadata_and_console_script_are_installed() -> None:
    dist = distribution("omega-game-t")
    assert dist.version == "1.0.3"
    console_scripts = {
        entry.name: entry.value
        for entry in dist.entry_points
        if entry.group == "console_scripts"
    }
    assert console_scripts["omega-game"] == "omega_game.__main__:main"


def test_installed_console_script_help_runs() -> None:
    completed = subprocess.run(
        ["omega-game", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "oakbench" in completed.stdout
    assert "compile-spec" in completed.stdout
