from __future__ import annotations

import json
from dataclasses import replace

import pytest

from omega_anime_t import (
    NarrativeLinter,
    OakStatus,
    ProjectValidationError,
    build_eighth_fire_project,
    compile_project_bundle,
)


def test_eighth_fire_project_is_valid() -> None:
    project = build_eighth_fire_project()
    assert project.validate() == []
    project.require_valid()


def test_pilot_duration_is_exactly_three_minutes() -> None:
    project = build_eighth_fire_project()
    assert project.target_duration_seconds == 180
    assert sum(beat.estimated_seconds for beat in project.episode_beats) == 180


def test_every_power_has_a_distinct_limitation() -> None:
    project = build_eighth_fire_project()
    assert all(character.power for character in project.characters)
    assert all(character.limitation for character in project.characters)
    assert all(
        character.power.lower() != character.limitation.lower()
        for character in project.characters
    )


def test_linter_allows_canonical_seed() -> None:
    project = build_eighth_fire_project()
    findings = NarrativeLinter().lint(project)
    assert NarrativeLinter.decision(findings) == "PROCEED"
    assert not [finding for finding in findings if finding.severity == "BLOCKING"]


def test_linter_blocks_project_without_information_flow() -> None:
    project = build_eighth_fire_project()
    beats = tuple(replace(beat, information_revealed=()) for beat in project.episode_beats)
    findings = NarrativeLinter().lint(replace(project, episode_beats=beats))
    codes = {finding.code for finding in findings}
    assert "NO_INFORMATION_FLOW" in codes
    assert NarrativeLinter.decision(findings) == "HOLD"


def test_linter_warns_when_risk_ledger_is_empty() -> None:
    project = replace(build_eighth_fire_project(), risks=())
    findings = NarrativeLinter().lint(project)
    assert "NO_RISK_LEDGER" in {finding.code for finding in findings}


def test_duplicate_beat_order_is_invalid() -> None:
    project = build_eighth_fire_project()
    beats = list(project.episode_beats)
    beats[1] = replace(beats[1], order=beats[0].order)
    errors = replace(project, episode_beats=tuple(beats)).validate()
    assert any("order must be unique" in error for error in errors)


def test_short_logline_is_invalid() -> None:
    project = replace(build_eighth_fire_project(), logline="Trop court")
    assert any("logline" in error for error in project.validate())
    with pytest.raises(ProjectValidationError):
        project.require_valid()


def test_theme_must_be_a_question() -> None:
    project = replace(build_eighth_fire_project(), theme_question="Le pouvoir et la responsabilité")
    assert any("theme_question" in error for error in project.validate())


def test_demonstrated_status_requires_evidence() -> None:
    project = replace(
        build_eighth_fire_project(),
        oak_status=OakStatus.DEMONSTRATED,
        evidence=(),
    )
    assert any("evidence is required" in error for error in project.validate())


def test_replicated_status_requires_independent_evidence() -> None:
    project = replace(
        build_eighth_fire_project(),
        oak_status=OakStatus.REPLICATED,
        evidence=("internal audience test",),
    )
    assert any("independent evidence" in error for error in project.validate())


def test_character_validation_rejects_empty_limitation() -> None:
    project = build_eighth_fire_project()
    invalid = replace(project.characters[0], limitation="")
    errors = invalid.validate()
    assert any("limitation" in error for error in errors)


def test_information_reveals_are_sequences_and_serialize_as_arrays() -> None:
    project = build_eighth_fire_project()
    assert all(isinstance(beat.information_revealed, tuple) for beat in project.episode_beats)
    payload = project.to_dict()
    assert all(
        isinstance(beat["information_revealed"], list)
        for beat in payload["episode_beats"]
    )


def test_scalar_information_reveal_is_rejected() -> None:
    project = build_eighth_fire_project()
    beats = list(project.episode_beats)
    beats[0] = replace(beats[0], information_revealed="scalar reveal")
    errors = replace(project, episode_beats=tuple(beats)).validate()
    assert any("must be a sequence of strings" in error for error in errors)


def test_bundle_contains_manifest_project_lint_and_report(tmp_path) -> None:
    manifest = compile_project_bundle(build_eighth_fire_project(), tmp_path)
    assert manifest["decision"] == "PROCEED"
    assert len(manifest["manifest_sha256"]) == 64
    assert set(path.name for path in tmp_path.iterdir()) == {
        "manifest.json",
        "oak-lint.json",
        "project.json",
        "report.md",
    }
    loaded = json.loads((tmp_path / "project.json").read_text(encoding="utf-8"))
    assert loaded["title"] == "Le Huitième Feu"
    assert loaded["oak_status"] == "FORMALIZED"


def test_bundle_is_deterministic(tmp_path) -> None:
    first = compile_project_bundle(build_eighth_fire_project(), tmp_path / "first")
    second = compile_project_bundle(build_eighth_fire_project(), tmp_path / "second")
    assert first == second
    assert (tmp_path / "first" / "project.json").read_bytes() == (
        tmp_path / "second" / "project.json"
    ).read_bytes()


def test_project_payload_is_json_serializable() -> None:
    payload = build_eighth_fire_project().to_dict()
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    assert "Le Huitième Feu" in encoded
    assert "FORMALIZED" in encoded


def test_cast_overload_warning_for_short_pilot() -> None:
    project = build_eighth_fire_project()
    base = project.characters[0]
    extra = tuple(
        replace(base, character_id=f"extra-{index}", name=f"Extra {index}")
        for index in range(7)
    )
    overloaded = replace(project, characters=project.characters + extra)
    findings = NarrativeLinter().lint(overloaded)
    assert "CAST_OVERLOAD" in {finding.code for finding in findings}


def test_duplicate_irreversible_change_is_reported() -> None:
    project = build_eighth_fire_project()
    beats = list(project.episode_beats)
    beats[1] = replace(
        beats[1], irreversible_change=beats[0].irreversible_change
    )
    findings = NarrativeLinter().lint(replace(project, episode_beats=tuple(beats)))
    assert "DUPLICATE_CHANGE" in {finding.code for finding in findings}
