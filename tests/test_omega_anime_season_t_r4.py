import hashlib
import json
from pathlib import Path

from omega_anime_episode_t import build_eighth_fire_episode_01_r3
from omega_anime_season_t import (
    EPISODE_ARTIFACT_NAMES,
    SEASON_ROOT_ARTIFACT_NAMES,
    build_eighth_fire_season_01_r4,
    compile_season_bundle,
)


def test_season_has_twelve_episodes():
    season = build_eighth_fire_season_01_r4()
    assert len(season.episodes) == 12
    assert [episode.blueprint.number for episode in season.episodes] == list(range(1, 13))


def test_every_episode_is_exactly_twenty_minutes():
    season = build_eighth_fire_season_01_r4()
    assert all(episode.timeline.duration_s == 1200.0 for episode in season.episodes)


def test_every_episode_has_twelve_scenes_and_114_shots():
    season = build_eighth_fire_season_01_r4()
    assert all(len(episode.timeline.scenes) == 12 for episode in season.episodes)
    assert all(len(episode.timeline.shots) == 114 for episode in season.episodes)


def test_season_totals_are_exact():
    season = build_eighth_fire_season_01_r4()
    assert season.total_duration_s == 14_400.0
    assert season.total_scenes == 144
    assert season.total_shots == 1_368


def test_first_episode_is_the_validated_r3_episode():
    season = build_eighth_fire_season_01_r4()
    r3 = build_eighth_fire_episode_01_r3()
    assert season.episodes[0].timeline.to_dict() == r3.to_dict()


def test_episode_titles_are_unique():
    season = build_eighth_fire_season_01_r4()
    titles = [episode.blueprint.title for episode in season.episodes]
    assert len(titles) == len(set(titles)) == 12


def test_project_ids_are_unique():
    season = build_eighth_fire_season_01_r4()
    ids = [episode.timeline.project_id for episode in season.episodes]
    assert len(ids) == len(set(ids)) == 12


def test_primary_questions_are_unique():
    season = build_eighth_fire_season_01_r4()
    questions = [episode.blueprint.primary_question for episode in season.episodes]
    assert len(questions) == len(set(questions)) == 12


def test_hooks_match_next_entry_conditions():
    season = build_eighth_fire_season_01_r4()
    for current, following in zip(season.episodes, season.episodes[1:]):
        assert current.blueprint.hook == following.blueprint.entry_condition


def test_debt_chain_leaves_only_season_two_seed():
    season = build_eighth_fire_season_01_r4()
    active: set[str] = set()
    for episode in season.episodes:
        blueprint = episode.blueprint
        if blueprint.debt_closed:
            assert blueprint.debt_closed in active
            active.remove(blueprint.debt_closed)
        active.add(blueprint.debt_opened)
    assert active == {"DEBT-SEASON2-001"}


def test_four_phases_have_three_episodes_each():
    season = build_eighth_fire_season_01_r4()
    counts: dict[str, int] = {}
    for episode in season.episodes:
        counts[episode.blueprint.phase] = counts.get(episode.blueprint.phase, 0) + 1
    assert counts == {"Éveil": 3, "Expansion": 3, "Fracture": 3, "Confrontation": 3}


def test_every_timeline_is_structurally_valid():
    season = build_eighth_fire_season_01_r4()
    assert season.validate() == []
    assert all(episode.timeline.validate() == [] for episode in season.episodes)


def test_every_episode_starts_at_zero_and_ends_at_1200():
    season = build_eighth_fire_season_01_r4()
    for episode in season.episodes:
        assert episode.timeline.shots[0].start_s == 0.0
        assert episode.timeline.shots[-1].end_s == 1200.0


def test_every_generated_episode_has_contiguous_shots():
    season = build_eighth_fire_season_01_r4()
    for episode in season.episodes[1:]:
        assert all(
            left.end_s == right.start_s
            for left, right in zip(episode.timeline.shots, episode.timeline.shots[1:])
        )


def test_shot_ids_are_unique_across_the_season():
    season = build_eighth_fire_season_01_r4()
    ids = [shot.shot_id for episode in season.episodes for shot in episode.timeline.shots]
    assert len(ids) == len(set(ids)) == 1_368


def test_each_episode_final_dialogue_is_its_hook():
    season = build_eighth_fire_season_01_r4()
    for episode in season.episodes[1:]:
        assert episode.timeline.shots[-1].dialogue == episode.blueprint.hook


def test_compile_creates_exactly_91_files(tmp_path: Path):
    manifest = compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    files = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert len(files) == 91
    assert manifest["artifact_count"] == 91


def test_compile_creates_exact_root_artifacts(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    root_names = {path.name for path in tmp_path.iterdir() if path.is_file()}
    assert root_names == SEASON_ROOT_ARTIFACT_NAMES


def test_compile_creates_twelve_episode_directories(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    episode_dirs = sorted(path for path in (tmp_path / "episodes").iterdir() if path.is_dir())
    assert len(episode_dirs) == 12
    assert episode_dirs[0].name == "episode-01"
    assert episode_dirs[-1].name == "episode-12"


def test_each_episode_directory_has_exact_artifact_set(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    for episode_dir in (tmp_path / "episodes").iterdir():
        assert {path.name for path in episode_dir.iterdir()} == EPISODE_ARTIFACT_NAMES


def test_compilation_is_byte_deterministic(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    season = build_eighth_fire_season_01_r4()
    first_manifest = compile_season_bundle(season, first)
    second_manifest = compile_season_bundle(season, second)
    assert first_manifest["manifest_sha256"] == second_manifest["manifest_sha256"]
    for first_path in sorted(path for path in first.rglob("*") if path.is_file()):
        rel = first_path.relative_to(first)
        assert first_path.read_bytes() == (second / rel).read_bytes()


def test_manifest_counts_and_hashes_are_correct(tmp_path: Path):
    manifest = compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    assert manifest["episode_count"] == 12
    assert manifest["total_duration_s"] == 14_400.0
    assert manifest["total_scenes"] == 144
    assert manifest["total_shots"] == 1_368
    assert manifest["episode_artifact_count"] == 84
    assert len(manifest["manifest_sha256"]) == 64
    for rel, record in manifest["files"].items():
        path = tmp_path / rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]


def test_players_and_dashboard_have_no_network_calls(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    html_files = [tmp_path / "season-dashboard.html"] + sorted(
        (tmp_path / "episodes").glob("episode-*/player.html")
    )
    assert len(html_files) == 13
    for path in html_files:
        content = path.read_text(encoding="utf-8")
        assert "fetch(" not in content
        assert "http://" not in content
        assert "https://" not in content


def test_all_episode_players_use_canvas_and_webaudio(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    for path in sorted((tmp_path / "episodes").glob("episode-*/player.html")):
        content = path.read_text(encoding="utf-8")
        assert "<canvas" in content
        assert "AudioContext" in content
        assert "requestAnimationFrame" in content


def test_every_subtitle_track_reaches_twenty_minutes(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    for path in sorted((tmp_path / "episodes").glob("episode-*/subtitles.fr.vtt")):
        content = path.read_text(encoding="utf-8")
        assert "00:20:00.000" in content


def test_episode_index_has_twelve_records(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    lines = (tmp_path / "episode-index.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert len(records) == 12
    assert records[0]["number"] == 1
    assert records[-1]["number"] == 12


def test_continuity_ledger_has_eleven_matched_edges(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    lines = (tmp_path / "continuity-ledger.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert len(records) == 11
    assert all(record["matched"] is True for record in records)


def test_causal_debt_ledger_finishes_with_season_two_seed(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    lines = (tmp_path / "causal-debt-ledger.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert len(records) == 12
    assert records[-1]["active_after"] == ["DEBT-SEASON2-001"]


def test_outline_contains_all_episode_titles(tmp_path: Path):
    season = build_eighth_fire_season_01_r4()
    compile_season_bundle(season, tmp_path)
    outline = (tmp_path / "season-outline.md").read_text(encoding="utf-8")
    assert all(episode.blueprint.title in outline for episode in season.episodes)


def test_dashboard_contains_all_episode_numbers(tmp_path: Path):
    compile_season_bundle(build_eighth_fire_season_01_r4(), tmp_path)
    dashboard = (tmp_path / "season-dashboard.html").read_text(encoding="utf-8")
    assert "1 368" in dashboard
    assert "240" in dashboard
    assert '"number":1' in dashboard
    assert '"number":12' in dashboard
