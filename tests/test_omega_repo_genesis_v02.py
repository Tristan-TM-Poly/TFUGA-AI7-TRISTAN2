import json
from pathlib import Path

from omega_repo_genesis_t.github_api import GitHubRepoFactory
from omega_repo_genesis_t.model import RepoSpec
from omega_repo_genesis_t.plan import bootstrap_files, build_plan, evaluate_visibility, load_constellation

PATH_V2 = Path("data/omega_repo_genesis_t/constellation_v02.json")


def test_v2_has_four_public_and_four_private_candidates():
    c = load_constellation(PATH_V2)
    plan = build_plan(c)
    assert len(c.repositories) == 8
    assert plan["counts"] == {"declared": 8, "create_candidates": 8, "holds": 0}
    assert plan["visibility_counts"]["public_candidates"] == 4
    assert plan["visibility_counts"]["private_candidates"] == 4
    assert plan["policy"]["public_creation_allowed"] is True
    assert plan["policy"]["public_materialization_requires_explicit_allow_public"] is True


def test_public_gate_fails_closed_on_private_blocker():
    spec = RepoSpec.from_dict({
        "name": "public-but-sensitive",
        "description": "x",
        "role": "x",
        "visibility": "public",
        "visibility_gate": {
            "public_drivers": ["protocol"],
            "private_blockers": ["unpublished_ip"],
        },
    })
    decision = evaluate_visibility(spec)
    assert decision.allowed is False
    assert decision.decision == "HOLD"


def test_public_gate_requires_explicit_driver():
    spec = RepoSpec.from_dict({
        "name": "public-without-driver",
        "description": "x",
        "role": "x",
        "visibility": "public",
    })
    assert evaluate_visibility(spec).allowed is False


def test_public_bootstrap_carries_visibility_without_auto_publication():
    c = load_constellation(PATH_V2)
    plan = build_plan(c)
    public_candidate = next(r for r in plan["create_candidates"] if r["visibility"] == "public")
    files = bootstrap_files(public_candidate, c)
    genome = json.loads(files["repo.genome.json"])
    assert genome["visibility"] == "public"
    assert genome["visibility_gate"]["allowed"] is True
    assert genome["authority"]["automatic_merge"] is False
    assert genome["authority"]["automatic_publication"] is False
    assert genome["authority"]["public_release_requires_review"] is True


def test_factory_holds_public_repo_without_explicit_allow_public():
    calls = []

    def transport(method, url, payload=None):
        calls.append((method, url, payload))
        if method == "GET":
            return 404, {}
        if method == "POST":
            return 201, {"owner": {"login": "Tristan-TM-Poly"}}
        if method == "PUT":
            return 201, {}
        raise AssertionError(method)

    factory = GitHubRepoFactory("token", transport=transport)
    result = factory.create_repository(
        "Tristan-TM-Poly",
        "omega-protocol",
        "x",
        visibility="public",
        allow_public=False,
    )
    assert result["status"] == "HOLD_PUBLIC_REQUIRES_EXPLICIT_ALLOW_PUBLIC"
    assert not any(method == "POST" for method, _, _ in calls)


def test_factory_public_creation_uses_private_false_only_when_explicit():
    calls = []

    def transport(method, url, payload=None):
        calls.append((method, url, payload))
        if method == "GET":
            return 404, {}
        if method == "POST":
            return 201, {"owner": {"login": "Tristan-TM-Poly"}}
        raise AssertionError(method)

    factory = GitHubRepoFactory("token", transport=transport)
    result = factory.create_repository(
        "Tristan-TM-Poly",
        "omega-protocol",
        "x",
        visibility="public",
        allow_public=True,
    )
    assert result["status"] == "CREATED_PUBLIC"
    post = next(payload for method, _, payload in calls if method == "POST")
    assert post["private"] is False
