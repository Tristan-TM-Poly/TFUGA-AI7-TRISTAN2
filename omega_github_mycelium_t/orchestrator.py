from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .campaign import PRCampaignPlanner, plan_dependency_order
from .canon import CanonSynchronizer
from .compiler import ArtifactCompiler
from .graph import MyceliumGraph
from .memory import MemoryLedger
from .models import EvidenceBundle, FindingSeverity, IntentContract, canonical_json, sha256_digest
from .oak import CampaignOAKAuditor, oak_report
from .registry import build_creation_registry, find_creation
from .routing import RepoRouter, RepositoryProfile
from .snapshot import SnapshotBundle


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _manifest(root: Path, excluded: set[str] | None = None) -> dict[str, Any]:
    excluded = excluded or set()
    files: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        payload = path.read_bytes()
        files.append({"path": relative, "bytes": len(payload), "sha256": sha256_digest(payload.decode("utf-8"))})
    return {
        "files": files,
        "file_count": len(files),
        "aggregate_sha256": sha256_digest(files),
        "remote_mutations_performed": False,
    }


class MyceliumOrchestrator:
    """Compile a snapshot and intention into a reviewable evidence-bearing plan."""

    def compile(
        self,
        intent: IntentContract,
        snapshot: SnapshotBundle,
        output_dir: str | Path,
    ) -> dict[str, Any]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        creations = build_creation_registry(snapshot.pull_requests)
        creation = find_creation(creations, intent.root_creation)
        graph = MyceliumGraph.build(snapshot.repositories, snapshot.pull_requests, creations)
        artifacts = ArtifactCompiler().compile(intent)
        router = RepoRouter(RepositoryProfile.from_snapshot(repo) for repo in snapshot.repositories)
        preferred = intent.candidate_repositories or (creation.canonical_repository,)
        routes = router.route_all(artifacts, preferred_repositories=preferred)
        campaign = PRCampaignPlanner().plan(
            intent,
            artifacts,
            routes,
            default_branches={repo.full_name: repo.default_branch for repo in snapshot.repositories},
        )
        findings = CampaignOAKAuditor().audit(snapshot, artifacts, routes, campaign)
        oak = oak_report(findings)

        artifact_digests = {
            artifact.artifact_id: artifact.content_digest or sha256_digest(artifact.to_dict())
            for artifact in artifacts
        }
        evidence = EvidenceBundle(
            evidence_id=f"evidence.{sha256_digest({'intent': intent.intent_id, 'campaign': campaign.campaign_id})[:20]}",
            intent_id=intent.intent_id,
            campaign_id=campaign.campaign_id,
            source_snapshot_digest=snapshot.digest,
            artifact_digests=artifact_digests,
            claims=(
                "A deterministic dry-run campaign was compiled from the supplied snapshot and intent.",
                "No remote mutation, merge, publication or deployment was performed by this compiler.",
            ),
            limitations=(
                "Artifact contracts are not completed implementations.",
                "Repository routing is a transparent heuristic requiring human review.",
                "GitHub snapshot quality and freshness remain external inputs.",
                "CI, scientific validity, IP and product value require separate evidence.",
            ),
            residuals=tuple(
                finding.message for finding in findings if finding.severity is not FindingSeverity.INFO
            ),
            status="planned_evidence",
        )
        canon_plan = CanonSynchronizer().propose(creation, campaign, artifacts, findings)

        ledger = MemoryLedger()
        for finding in findings:
            if finding.severity is FindingSeverity.INFO:
                continue
            ledger.append(
                polarity="m_minus",
                event_type=finding.code.lower(),
                subject=finding.subject,
                lesson=finding.message,
                prevention_rule=finding.remediation or "retain human review",
                source_refs=(campaign.campaign_id, snapshot.digest),
            )

        _write_json(output / "intent.json", intent.to_dict())
        _write_json(output / "snapshot-summary.json", snapshot.summary())
        _write_jsonl(output / "creation-registry.jsonl", [record.to_dict() for record in creations])
        _write_json(output / "mycelium-graph.json", graph.to_dict())
        (output / "mycelium-graph.graphml").write_text(graph.to_graphml(), encoding="utf-8")
        _write_jsonl(output / "artifacts.jsonl", [artifact.to_dict() for artifact in artifacts])
        _write_jsonl(output / "route-decisions.jsonl", [route.to_dict() for route in routes])
        _write_json(output / "campaign.json", campaign.to_dict())
        _write_json(output / "oak-report.json", oak)
        _write_json(output / "evidence-bundle.json", evidence.to_dict())
        _write_json(output / "canon-update-plan.json", canon_plan)
        ledger.write_jsonl(output / "m_minus.jsonl")

        ordered = plan_dependency_order(campaign)
        report_lines = [
            "# Ω-GITHUB-MYCELIUM-T∞ — Campaign Report",
            "",
            f"- Intent: `{intent.intent_id}`",
            f"- Creation: `{creation.creation_id}`",
            f"- Snapshot: `{snapshot.digest}`",
            f"- Repositories observed: **{len(snapshot.repositories)}**",
            f"- Open PRs observed: **{sum(pr.state == 'open' for pr in snapshot.pull_requests)}**",
            f"- Artifacts planned: **{len(artifacts)}**",
            f"- PR plans: **{len(campaign.pull_requests)}**",
            f"- OAK status: **{oak['status']}**",
            "",
            "## PR dependency order",
            "",
        ]
        report_lines.extend(f"{index}. `{plan_id}`" for index, plan_id in enumerate(ordered, start=1))
        report_lines.extend(
            [
                "",
                "## Hard boundary",
                "",
                "This materialization performs no branch creation, commit, push, PR creation, merge, publication, deployment, deletion or permission change.",
                "",
                "Every remote mutation remains a separately authorized and human-reviewed action.",
            ]
        )
        (output / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

        manifest = _manifest(output, {"manifest.json"})
        _write_json(output / "manifest.json", manifest)
        return {
            "intent_id": intent.intent_id,
            "campaign_id": campaign.campaign_id,
            "creation_id": creation.creation_id,
            "snapshot": snapshot.summary(),
            "graph": graph.summary(),
            "artifact_count": len(artifacts),
            "route_count": len(routes),
            "pull_request_plan_count": len(campaign.pull_requests),
            "pull_request_dependency_order": list(ordered),
            "oak": oak,
            "manifest": manifest,
            "output_dir": str(output),
        }
