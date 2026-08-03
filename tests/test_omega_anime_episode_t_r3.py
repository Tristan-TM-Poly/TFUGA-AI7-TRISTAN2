import hashlib
import json
from pathlib import Path

from omega_anime_animatic_t.timeline import build_eighth_fire_animatic_r2
from omega_anime_episode_t import (
    EPISODE_ARTIFACT_NAMES,
    EPISODE_DURATION_S,
    build_eighth_fire_episode_01_r3,
    compile_episode_bundle,
)


def test_episode_is_exactly_twenty_minutes():
    episode = build_eighth_fire_episode_01_r3()
    assert episode.duration_s == EPISODE_DURATION_S == 1200.0
    assert episode.shots[0].start_s == 0.0
    assert episode.shots[-1].end_s == 1200.0


def test_episode_has_twelve_scenes_and_114_shots():
    episode = build_eighth_fire_episode_01_r3()
    assert len(episode.scenes) == 12
    assert len(episode.shots) == 114


def test_r2_is_preserved_as_the_cold_open():
    r2 = build_eighth_fire_animatic_r2()
    episode = build_eighth_fire_episode_01_r3()
    assert episode.scenes[:5] == r2.scenes
    assert episode.shots[:30] == r2.shots
    assert episode.shots[29].end_s == 180.0


def test_all_shots_are_contiguous():
    episode = build_eighth_fire_episode_01_r3()
    assert all(left.end_s == right.start_s for left, right in zip(episode.shots, episode.shots[1:]))


def test_scene_durations_sum_to_episode_duration():
    episode = build_eighth_fire_episode_01_r3()
    assert sum(scene.duration_s for scene in episode.scenes) == 1200.0


def test_scene_orders_are_contiguous():
    episode = build_eighth_fire_episode_01_r3()
    assert [scene.order for scene in episode.scenes] == list(range(1, 13))


def test_new_scenes_have_twelve_shots_each():
    episode = build_eighth_fire_episode_01_r3()
    for scene in episode.scenes[5:]:
        shots = [shot for shot in episode.shots if shot.scene_id == scene.scene_id]
        assert len(shots) == 12
        assert [shot.order for shot in shots] == list(range(1, 13))


def test_episode_final_hook_names_the_network():
    episode = build_eighth_fire_episode_01_r3()
    assert episode.shots[-1].dialogue == "La Station des Absents."
    assert episode.shots[-13].dialogue == "Le réseau a appris ton nom."


def test_episode_remains_private_draft():
    episode = build_eighth_fire_episode_01_r3()
    assert episode.publication_state == "private-draft"
    assert len(episode.disclaimers) == 4


def test_compile_produces_exact_artifact_set(tmp_path: Path):
    compile_episode_bundle(build_eighth_fire_episode_01_r3(), tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == EPISODE_ARTIFACT_NAMES


def test_compilation_is_byte_deterministic(tmp_path: Path):
    first, second = tmp_path / "first", tmp_path / "second"
    episode = build_eighth_fire_episode_01_r3()
    compile_episode_bundle(episode, first)
    compile_episode_bundle(episode, second)
    for name in EPISODE_ARTIFACT_NAMES:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_manifest_has_twenty_minute_proofs(tmp_path: Path):
    manifest = compile_episode_bundle(build_eighth_fire_episode_01_r3(), tmp_path)
    assert manifest["duration_s"] == 1200.0
    assert manifest["duration_minutes"] == 20.0
    assert manifest["scene_count"] == 12
    assert manifest["shot_count"] == 114
    assert manifest["cold_open_duration_s"] == 180.0
    assert manifest["external_network_dependencies"] == 0
    assert len(manifest["manifest_sha256"]) == 64


def test_manifest_hashes_match_files(tmp_path: Path):
    manifest = compile_episode_bundle(build_eighth_fire_episode_01_r3(), tmp_path)
    for name, record in manifest["files"].items():
        path = tmp_path / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
        assert path.stat().st_size == record["bytes"]


def test_html_player_is_self_contained_and_twenty_minutes(tmp_path: Path):
    compile_episode_bundle(build_eighth_fire_episode_01_r3(), tmp_path)
    content = (tmp_path / "episode-01.html").read_text(encoding="utf-8")
    assert "AudioContext" in content
    assert "TIMELINE.duration_s" in content
    assert "20:00" in content
    assert "fetch(" not in content
    assert "http://" not in content
    assert "https://" not in content


def test_contact_sheet_contains_all_114_panels(tmp_path: Path):
    compile_episode_bundle(build_eighth_fire_episode_01_r3(), tmp_path)
    content = (tmp_path / "storyboard-contact-sheet.svg").read_text(encoding="utf-8")
    assert content.count("data-shot=") == 114
    assert "20 minutes" in content


def test_subtitles_reach_exactly_twenty_minutes(tmp_path: Path):
    compile_episode_bundle(build_eighth_fire_episode_01_r3(), tmp_path)
    content = (tmp_path / "subtitles.fr.vtt").read_text(encoding="utf-8")
    assert content.startswith("WEBVTT")
    assert "00:20:00.000" in content
    assert "La Station des Absents." in content


def test_edl_contains_header_plus_114_rows(tmp_path: Path):
    compile_episode_bundle(build_eighth_fire_episode_01_r3(), tmp_path)
    rows = (tmp_path / "edit-decision-list.csv").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 115


def test_audio_cues_are_guide_only(tmp_path: Path):
    compile_episode_bundle(build_eighth_fire_episode_01_r3(), tmp_path)
    records = [json.loads(line) for line in (tmp_path / "audio-cues.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(records) == 114
    assert all(record["guide_only"] is True for record in records)


def test_outline_lists_all_twelve_scenes(tmp_path: Path):
    episode = build_eighth_fire_episode_01_r3()
    compile_episode_bundle(episode, tmp_path)
    content = (tmp_path / "episode-outline.md").read_text(encoding="utf-8")
    assert content.count("### ") == 12
    assert "Durée canonique : **20:00**" in content
