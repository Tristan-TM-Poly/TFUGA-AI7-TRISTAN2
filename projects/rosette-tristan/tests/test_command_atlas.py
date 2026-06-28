from pathlib import Path

from rosette_tristan.command_atlas import atlas_markdown, build_command_atlas, load_scripts


def test_load_scripts_reads_pyproject():
    version, scripts = load_scripts()
    assert version
    assert "rosette" in scripts
    assert "rosette-doctor" in scripts


def test_build_command_atlas_has_metadata():
    report = build_command_atlas()
    assert report.oak_status == "atlas_passed_not_certified"
    assert report.command_count >= 11
    names = {command.name for command in report.commands}
    assert "rosette-doctor" in names
    assert not report.missing_metadata


def test_atlas_markdown_contains_table():
    report = build_command_atlas()
    markdown = atlas_markdown(report)
    assert "# Rosette Command Atlas" in markdown
    assert "| Command | Layer | Purpose | Docs |" in markdown
    assert "rosette-bench" in markdown


def test_atlas_outputs_can_be_written(tmp_path: Path):
    report = build_command_atlas()
    out = tmp_path / "atlas.md"
    out.write_text(atlas_markdown(report), encoding="utf-8")
    assert out.exists()
    assert "OAK lock" in out.read_text(encoding="utf-8")
