import pytest
from omega_re_t.cleanroom_agents import AgentIdentity, CleanRoomArtifact, CleanRoomLedger, CleanRoomRole, audit_clean_room
from omega_re_t.genealogy import VersionArtifact, infer_minimum_genealogy, localize_regression
from omega_re_t.hybrid import AffineDynamics, Guard, HybridMode, HybridObservation, HybridSystem, fit_affine_mode


def test_hybrid_simulation_and_fit():
    system = HybridSystem(
        modes={
            "heat": HybridMode("heat", AffineDynamics(((0.0,),), ((1.0,),), (0.0,)), (Guard(0, ">=", 2.0, "cool"),)),
            "cool": HybridMode("cool", AffineDynamics(((-1.0,),), ((0.0,),), (0.0,)), (Guard(0, "<=", 0.5, "heat"),)),
        },
        initial_mode="heat",
    )
    trace = system.simulate((0.0,), ((1.0,),) * 4, dt=1.0)
    assert any(mode == "cool" for mode, _ in trace)
    observations = [
        HybridObservation("m", (x,), (u,), (x + 0.5 * (2.0 * x + 3.0 * u + 1.0),), 0.5)
        for x, u in [(0, 0), (1, 0), (0, 1), (1, 1), (2, -1)]
    ]
    report = fit_affine_mode(observations, "m")
    assert report.identifiable
    assert report.mean_absolute_residual < 1e-6


def test_genealogy_and_regression():
    versions = (
        VersionArtifact("v1", frozenset({"base"}), {"status": "ok"}, "2026-01-01"),
        VersionArtifact("v2", frozenset({"base", "fast"}), {"status": "ok"}, "2026-01-02"),
        VersionArtifact("v3", frozenset({"base", "fast", "new"}), {"status": "bad"}, "2026-01-03"),
    )
    graph = infer_minimum_genealogy(versions)
    assert graph.roots() == ("v1",)
    lineage = graph.lineage("v3")
    result = localize_regression(graph, lineage, "status", "ok")
    assert result.first_bad_version == "v3"
    assert result.candidate_edges == (("v2", "v3"),)


def make_clean_ledger():
    ledger = CleanRoomLedger()
    for role in CleanRoomRole:
        ledger.register_agent(AgentIdentity(role.value, role, ("synthetic",)))
    ledger.add_artifact(CleanRoomArtifact.from_text("obs", "observation", "observer", "observations"))
    ledger.add_artifact(CleanRoomArtifact.from_text("spec", "specification", "specifier", "neutral spec", source_artifact_ids=("obs",)))
    ledger.add_artifact(CleanRoomArtifact.from_text("impl", "implementation", "implementer", "fresh code", source_artifact_ids=("spec",)))
    ledger.add_artifact(CleanRoomArtifact.from_text("audit", "audit", "auditor", "audit", source_artifact_ids=("obs", "spec", "impl")))
    return ledger


def test_cleanroom_pass_and_contamination():
    ledger = make_clean_ledger()
    assert audit_clean_room(ledger).passed
    bad = CleanRoomLedger(dict(ledger.agents), dict(ledger.artifacts))
    bad.add_artifact(CleanRoomArtifact.from_text("secret", "observation", "observer", "restricted", contains_restricted_material=True))
    bad.add_artifact(CleanRoomArtifact.from_text("bad_impl", "implementation", "implementer", "copy", source_artifact_ids=("secret",)))
    audit = audit_clean_room(bad)
    assert not audit.passed
    assert any("Forbidden source path" in blocker for blocker in audit.blockers)
