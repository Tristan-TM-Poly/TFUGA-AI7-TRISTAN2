from omega_game.engines.github_realm import GitHubRealmEngine, RepoQuest, RepoWorld, RepoZone, demo_repo_world
from omega_game.kernel import GameEngineKernel


def test_repo_zone_requires_valid_health():
    try:
        RepoZone("docs", 2.0)
    except ValueError as exc:
        assert "health" in str(exc)
    else:
        raise AssertionError("RepoZone accepted health outside [0, 1]")


def test_repo_quest_converts_to_action():
    quest = RepoQuest("update_readme_map", "docs", 0.2, 0.05, ["docs"])
    action = quest.to_action()

    assert action.name == "update_readme_map"
    assert "docs" in action.tags
    assert 0.0 <= action.risk <= 1.0


def test_repo_world_health_and_state():
    repo = demo_repo_world()
    state = repo.to_world_state()

    assert 0.0 <= repo.health() <= 1.0
    assert state.domain == "github_realm"
    assert "repo_health" in state.metrics


def test_github_realm_engine_runs_best_action():
    repo = demo_repo_world()
    state = repo.to_world_state()
    result = GameEngineKernel().run_best_action(GitHubRealmEngine(), state)

    assert result.engine == "GitHubRealmEngine-T"
    assert 0.0 <= result.score <= 1.0
    assert result.oak_status in {"accepted", "caution", "blocked"}
    assert "no_remote_action_performed" in result.m_minus


def test_github_realm_simulation_improves_or_tracks_repo_health():
    repo = demo_repo_world()
    state = repo.to_world_state()
    engine = GitHubRealmEngine()
    action = [item for item in engine.propose_actions(state) if item.name == "prepare_oak_review"][0]
    result = engine.simulate(state, action)

    assert result.after.metrics["repo_health"] >= 0.0
    assert result.after.metrics["oak"] >= result.before.metrics["oak"]


def test_repo_world_serializes():
    payload = demo_repo_world().to_dict()

    assert set(payload) == {"repo_name", "zones", "quests", "oak_controls", "health"}
    assert payload["zones"]
    assert payload["quests"]
