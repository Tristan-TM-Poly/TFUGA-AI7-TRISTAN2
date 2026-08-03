from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_github_mycelium_t.campaign import PRCampaignPlanner, plan_dependency_order
from omega_github_mycelium_t.compiler import ArtifactCompiler
from omega_github_mycelium_t.graph import MyceliumGraph
from omega_github_mycelium_t.intent import IntentCompiler
from omega_github_mycelium_t.live_github import GitHubReadOnlyScanner
from omega_github_mycelium_t.memory import MemoryEvent, MemoryLedger
from omega_github_mycelium_t.models import (
    ArtifactSpec,
    FindingSeverity,
    PullRequestSnapshot,
    RepositorySnapshot,
    RouteDecision,
    RouteDecisionRecord,
)
from omega_github_mycelium_t.oak import CampaignOAKAuditor, oak_report
from omega_github_mycelium_t.orchestrator import MyceliumOrchestrator
from omega_github_mycelium_t.registry import build_creation_registry, find_creation
from omega_github_mycelium_t.routing import RepoRouter, RepositoryProfile
from omega_github_mycelium_t.snapshot import SnapshotBundle


def _snapshot(*, complete: bool = True) -> SnapshotBundle:
    public = RepositorySnapshot(
        full_name="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        visibility="public",
        permissions=("admin", "push"),
        packages=("omega-depth-t",),
        workflows=("oakbench",),
        tests=("pytest",),
        docs=("docs",),
        topics=("tfuga", "oak"),
    )
    private = RepositorySnapshot(
        full_name="Tristan-TM-Poly/TFACC",
        visibility="private",
        permissions=("admin", "push"),
        packages=("omega-pdf-hypergraph-github-t",),
        topics=("private", "ip"),
    )
    pull_request = PullRequestSnapshot(
        repo_full_name=public.full_name,
        number=330,
        title="feat/docs: Ω-DEPTH-T∞ and Ω-DOC-T",
        draft=True,
        mergeable=True,
        head_branch="docs/public-positioning-life-project",
    )
    return SnapshotBundle(
        repositories=(public, private),
        pull_requests=(pull_request,),
        source="test",
        completeness=(
            "all_owned_repositories_and_open_pull_requests_returned_by_paginated_api"
            if complete
            else "representative"
        ),
    )


def test_intent_compiler_is_deterministic_and_infers_creation() -> None:
    compiler = IntentCompiler()
    first = compiler.compile("Construire un audit de documentation et de code.")
    second = compiler.compile("Construire un audit de documentation et de code.")
    assert first == second
    assert first.root_creation == "omega-doc-t"
    assert first.remote_mutations_authorized is False
    assert "no_automatic_merge" in first.constraints


def test_snapshot_rejects_pr_for_unknown_repository() -> None:
    with pytest.raises(ValueError, match="unknown repositories"):
        SnapshotBundle(
            repositories=(),
            pull_requests=(
                PullRequestSnapshot(
                    repo_full_name="Tristan-TM-Poly/missing",
                    number=1,
                    title="missing",
                ),
            ),
        )


def test_live_scanner_paginates_read_only_fixture() -> None:
    calls: list[str] = []

    def transport(url: str, headers: dict[str, str], timeout: float):
        calls.append(url)
        assert headers["User-Agent"].startswith("omega-github-mycelium")
        assert timeout == 5.0
        if "/user/repos" in url:
            payload = [
                {
                    "id": 1,
                    "full_name": "Tristan-TM-Poly/demo",
                    "visibility": "public",
                    "default_branch": "main",
                    "archived": False,
                    "size": 4,
                    "permissions": {"admin": True, "push": True},
                    "topics": ["demo"],
                }
            ]
        else:
            payload = [
                {
                    "number": 7,
                    "title": "feat: demo",
                    "body": "bounded body",
                    "draft": True,
                    "head": {"ref": "feat/demo", "sha": "a" * 40},
                    "base": {"ref": "main"},
                    "html_url": "https://github.com/Tristan-TM-Poly/demo/pull/7",
                    "labels": [],
                    "updated_at": "2026-08-03T00:00:00Z",
                }
            ]
        return 200, json.dumps(payload).encode(), {}

    snapshot = GitHubReadOnlyScanner(timeout_seconds=5.0, transport=transport).scan_owner("Tristan-TM-Poly")
    assert len(snapshot.repositories) == 1
    assert len(snapshot.pull_requests) == 1
    assert snapshot.pull_requests[0].body_digest is not None
    assert snapshot.pull_requests[0].metadata["updated_at"] == "2026-08-03T00:00:00Z"
    assert len(calls) == 2


def test_creation_registry_has_forty_roots_and_pr_relations() -> None:
    records = build_creation_registry(_snapshot().pull_requests)
    assert len(records) == 40
    doc = find_creation(records, "omega-doc-t")
    assert doc.creation_id == "omega_doc_t"
    assert "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2#330" in doc.related_prs


def test_graph_connects_repositories_prs_and_creations() -> None:
    snapshot = _snapshot()
    records = build_creation_registry(snapshot.pull_requests)
    graph = MyceliumGraph.build(snapshot.repositories, snapshot.pull_requests, records)
    summary = graph.summary()
    assert summary["nodes_by_kind"]["repository"] == 2
    assert summary["nodes_by_kind"]["pull_request"] == 1
    assert summary["nodes_by_kind"]["creation"] == 40
    assert summary["validation_issues"] == []
    assert "creation:omega_doc_t" in graph.neighbors("pr:Tristan-TM-Poly/TFUGA-AI7-TRISTAN2#330")
    assert "<graphml" in graph.to_graphml()


def test_router_keeps_private_artifact_in_private_repository() -> None:
    snapshot = _snapshot()
    router = RepoRouter(RepositoryProfile.from_snapshot(repo) for repo in snapshot.repositories)
    artifact = ArtifactSpec(
        artifact_id="artifact.private.ip",
        creation_id="omega_doc_t",
        kind="ip_report",
        suggested_path="reports/ip.json",
        description="confidential invention review",
        required_visibility="private_required",
    )
    route = router.route(artifact, preferred_repositories=("Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",))
    assert route.repository == "Tristan-TM-Poly/TFACC"
    assert route.decision is RouteDecision.ADD_TO_EXISTING_REPO


def test_campaign_plans_are_draft_acyclic_and_unbounded_by_permanent_cap() -> None:
    snapshot = _snapshot()
    intent = IntentCompiler().compile(
        "Développer Ω-DOC-T",
        root_creation="omega-doc-t",
        candidate_repositories=(repo.full_name for repo in snapshot.repositories),
    )
    artifacts = ArtifactCompiler().compile(intent)
    router = RepoRouter(RepositoryProfile.from_snapshot(repo) for repo in snapshot.repositories)
    routes = router.route_all(artifacts, preferred_repositories=intent.candidate_repositories)
    campaign = PRCampaignPlanner().plan(intent, artifacts, routes)
    assert campaign.pull_requests
    assert campaign.permanent_pr_cap is None
    assert campaign.remote_mutations_authorized is False
    assert all(plan.draft and plan.human_gate_required for plan in campaign.pull_requests)
    assert set(plan_dependency_order(campaign)) == {plan.plan_id for plan in campaign.pull_requests}


def test_oak_blocks_private_artifact_routed_publicly() -> None:
    snapshot = _snapshot()
    intent = IntentCompiler().compile("IP review", root_creation="omega-doc-t", expected_outputs=("ip_report",))
    artifact = ArtifactCompiler().compile(intent)[0]
    public_route = RouteDecisionRecord(
        artifact_id=artifact.artifact_id,
        decision=RouteDecision.ADD_TO_EXISTING_REPO,
        repository="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        score=99.0,
        reasons=("adversarial_fixture",),
    )
    campaign = PRCampaignPlanner().plan(intent, (artifact,), (public_route,))
    findings = CampaignOAKAuditor().audit(snapshot, (artifact,), (public_route,), campaign)
    report = oak_report(findings)
    assert report["status"] == "blocked"
    assert any(finding.code == "PRIVATE_ARTIFACT_PUBLIC_ROUTE" for finding in findings)


def test_memory_ledger_detects_tampering() -> None:
    ledger = MemoryLedger()
    event = ledger.append(
        polarity="m_minus",
        event_type="baseline_missing",
        subject="ffwt",
        lesson="No promotion without a baseline.",
        prevention_rule="require classical wavelet baseline",
    )
    assert ledger.verify()
    tampered = MemoryEvent(
        event_id=event.event_id,
        polarity=event.polarity,
        event_type=event.event_type,
        subject=event.subject,
        lesson="tampered",
        prevention_rule=event.prevention_rule,
        source_refs=event.source_refs,
        previous_hash=event.previous_hash,
        event_hash=event.event_hash,
        metadata=event.metadata,
    )
    with pytest.raises(ValueError, match="digest mismatch"):
        MemoryLedger((tampered,))


def test_orchestrator_materializes_complete_review_bundle(tmp_path: Path) -> None:
    snapshot = _snapshot(complete=True)
    intent = IntentCompiler().compile(
        "Détecter une divergence entre documentation et code.",
        root_creation="omega-doc-t",
        candidate_repositories=("Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",),
    )
    result = MyceliumOrchestrator().compile(intent, snapshot, tmp_path)
    expected = {
        "intent.json",
        "snapshot-summary.json",
        "creation-registry.jsonl",
        "mycelium-graph.json",
        "mycelium-graph.graphml",
        "artifacts.jsonl",
        "route-decisions.jsonl",
        "campaign.json",
        "oak-report.json",
        "evidence-bundle.json",
        "canon-update-plan.json",
        "m_minus.jsonl",
        "report.md",
        "manifest.json",
    }
    assert expected == {path.name for path in tmp_path.iterdir()}
    assert result["snapshot"]["repository_count"] == 2
    assert result["artifact_count"] == 10
    assert result["oak"]["blocker_count"] == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["file_count"] == len(expected) - 1
    assert manifest["remote_mutations_performed"] is False
