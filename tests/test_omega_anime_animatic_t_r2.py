from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from omega_anime_animatic_t import (
    ARTIFACT_NAMES,
    TimelineValidationError,
    build_eighth_fire_animatic_r2,
    compile_animatic_bundle,
)


def test_timeline_has_five_scenes_and_thirty_shots():
    timeline = build_eighth_fire_animatic_r2()
    assert len(timeline.scenes) == 5
    assert len(timeline.shots) == 30


def test_timeline_is_exactly_180_seconds():
    timeline = build_eighth_fire_animatic_r2()
    assert timeline.duration_s == 180.0
    assert timeline.shots[0].start_s == 0.0
    assert timeline.shots[-1].end_s == 180.0


def test_shots_are_contiguous():
    timeline = build_eighth_fire_animatic_r2()
    assert all(
        left.end_s == right.start_s
        for left, right in zip(timeline.shots, timeline.shots[1:])
    )


def test_scene_intervals_match_their_shots():
    timeline = build_eighth_fire_animatic_r2()
    for scene in timeline.scenes:
        shots = [shot for shot in timeline.shots if shot.scene_id == scene.scene_id]
        assert shots[0].start_s == scene.start_s
        assert shots[-1].end_s == scene.end_s
        assert sum(shot.duration_s for shot in shots) == scene.duration_s


def test_final_dialogue_is_the_canonical_hook():
    timeline = build_eighth_fire_animatic_r2()
    assert timeline.shots[-1].dialogue == "Et maintenant, elle te voit."


def test_all_shots_have_visual_and_audio_intent():
    timeline = build_eighth_fire_animatic_r2()
    for shot in timeline.shots:
        assert shot.caption
        assert shot.purpose
        assert shot.framing
        assert shot.camera_motion
        assert shot.audio_cue
        assert 0.0 <= shot.intensity <= 1.0


def test_publication_remains_private_draft():
    timeline = build_eighth_fire_animatic_r2()
    assert timeline.publication_state == "private-draft"
    assert len(timeline.disclaimers) >= 3


def test_validation_rejects_a_gap():
    timeline = build_eighth_fire_animatic_r2()
    broken = replace(timeline.shots[1], start_s=timeline.shots[1].start_s + 1)
    invalid = replace(timeline, shots=(timeline.shots[0], broken, *timeline.shots[2:]))
    with pytest.raises(TimelineValidationError):
        invalid.require_valid()


def test_validation_rejects_invalid_intensity():
    timeline = build_eighth_fire_animatic_r2()
    broken = replace(timeline.shots[0], intensity=1.5)
    invalid = replace(timeline, shots=(broken, *timeline.shots[1:]))
    assert any("intensity" in error for error in invalid.validate())


def test_compile_produces_exact_artifact_set(tmp_path: Path):
    timeline = build_eighth_fire_animatic_r2()
    compile_animatic_bundle(timeline, tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == ARTIFACT_NAMES


def test_compilation_is_byte_deterministic(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    timeline = build_eighth_fire_animatic_r2()
    compile_animatic_bundle(timeline, first)
    compile_animatic_bundle(timeline, second)
    for name in ARTIFACT_NAMES:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_manifest_has_required_proof_fields(tmp_path: Path):
    manifest = compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    assert manifest["scene_count"] == 5
    assert manifest["shot_count"] == 30
    assert manifest["duration_s"] == 180.0
    assert manifest["self_contained_browser_player"] is True
    assert manifest["external_network_dependencies"] == 0
    assert manifest["guide_audio_only"] is True
    assert len(manifest["manifest_sha256"]) == 64


def test_manifest_hashes_match_files(tmp_path: Path):
    manifest = compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    for name, record in manifest["files"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == record["sha256"]
        assert (tmp_path / name).stat().st_size == record["bytes"]


def test_html_player_is_self_contained(tmp_path: Path):
    compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    content = (tmp_path / "eighth-fire-animatic.html").read_text(encoding="utf-8")
    assert "<canvas" in content
    assert "AudioContext" in content
    assert "requestAnimationFrame" in content
    assert "fetch(" not in content
    assert "http://" not in content
    assert "https://" not in content


def test_html_embeds_all_thirty_shots(tmp_path: Path):
    compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    content = (tmp_path / "eighth-fire-animatic.html").read_text(encoding="utf-8")
    assert content.count('"shot_id"') == 30
    assert "Et maintenant, elle te voit." in content


def test_contact_sheet_contains_thirty_panels(tmp_path: Path):
    compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    content = (tmp_path / "storyboard-contact-sheet.svg").read_text(encoding="utf-8")
    assert content.count("data-shot=") == 30
    assert "Storyboard R2" in content


def test_subtitles_cover_entire_timeline(tmp_path: Path):
    compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    content = (tmp_path / "subtitles.fr.vtt").read_text(encoding="utf-8")
    assert content.startswith("WEBVTT")
    assert "00:00:00.000 -->" in content
    assert "00:03:00.000" in content
    assert "Et maintenant, elle te voit." in content


def test_edl_contains_header_plus_thirty_rows(tmp_path: Path):
    compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    lines = (tmp_path / "edit-decision-list.csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 31
    assert lines[0].startswith("shot_id,scene_id")


def test_audio_cues_are_jsonl_and_guide_only(tmp_path: Path):
    compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    lines = (tmp_path / "audio-cues.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 30
    records = [json.loads(line) for line in lines]
    assert all(record["guide_only"] is True for record in records)
    assert all(record["cue"] for record in records)


def test_report_states_epistemic_boundary(tmp_path: Path):
    compile_animatic_bundle(build_eighth_fire_animatic_r2(), tmp_path)
    content = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "animation finale" in content
    assert "validation artistique" in content
