import pytest
from omega_workmax_t.cross_repo import RepoSnapshot, CrossRepoCapability, CrossRepoRegistry, compile_cross_repo_plan

SHA_A = "a" * 40
SHA_B = "b" * 40

def test_exact_sha_required():
    with pytest.raises(ValueError):
        RepoSnapshot("owner/repo", "abc")

def test_stale_capability_binding_rejected():
    repo = RepoSnapshot("owner/repo", SHA_A)
    cap = CrossRepoCapability("cap", "owner/repo", SHA_B, "Capability")
    with pytest.raises(ValueError, match="stale capability binding"):
        CrossRepoRegistry([repo], [cap])

def test_private_capability_routes_without_content_disclosure():
    repo = RepoSnapshot("owner/private", SHA_A, ref="main", visibility="private")
    cap = CrossRepoCapability("private-vault", "owner/private", SHA_A, "Private vault", domains=("vault", "drive"), evidence_weight=.9)
    registry = CrossRepoRegistry([repo], [cap])
    match = registry.route("drive vault")[0]
    assert match.content_disclosure == "opaque_private_capability_metadata_only"
    plan = registry.build_plan("drive vault")
    assert not any(key in plan for key in ("source", "files", "raw_content", "private_payload"))
    assert plan["cross_repository_writes_authorized"] is False

def test_dependency_closure_is_cycle_safe():
    r1 = RepoSnapshot("o/a", SHA_A)
    r2 = RepoSnapshot("o/b", SHA_B)
    a = CrossRepoCapability("a", "o/a", SHA_A, "A", depends_on=("b",))
    b = CrossRepoCapability("b", "o/b", SHA_B, "B")
    assert CrossRepoRegistry([r1, r2], [a, b]).dependency_closure("a") == ("b",)
    cyc_b = CrossRepoCapability("b", "o/b", SHA_B, "B", depends_on=("a",))
    with pytest.raises(ValueError, match="cycle"):
        CrossRepoRegistry([r1, r2], [a, cyc_b])

def test_control_plane_routing_prefers_matching_capability():
    payload = {
        "intent": "github control plane repository orchestration",
        "repositories": [
            {"repository": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2", "head_sha": SHA_A},
            {"repository": "Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2", "head_sha": SHA_B},
        ],
        "capabilities": [
            {"capability_id": "omega-workmax", "repository": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2", "head_sha": SHA_A, "name": "Work optimization", "domains": ["work", "optimization"], "evidence_weight": .8},
            {"capability_id": "omega-github-control-plane", "repository": "Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2", "head_sha": SHA_B, "name": "GitHub control plane", "domains": ["github", "control", "plane", "repository", "orchestration"], "evidence_weight": .9},
        ],
    }
    plan = compile_cross_repo_plan(payload)
    assert plan["selected_capability"] == "omega-github-control-plane"
    assert f"Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2@{SHA_B}" in plan["planned_repository_identities"]
    assert plan["automatic_merge_authorized"] is False
