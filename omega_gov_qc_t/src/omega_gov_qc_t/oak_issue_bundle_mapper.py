"""Map local export bundles into Ω-GOV-QC-T OAK issue drafts.

This module accepts already-local JSON text. It performs no network access and
creates no remote issues. Its output is an OAKIssueBundle for human review.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Tuple

from .oak_issue_generator import OAKIssueBundle, OAKIssueDraft, OAKIssueGenerator
from .oak_issue_severity import OAKIssueSeverityPolicy, SeverityDecision


class OAKIssueBundleMapper:
    """Create issue drafts from a local ExportBundle JSON payload."""

    def __init__(self, severity_policy: OAKIssueSeverityPolicy | None = None) -> None:
        self.severity_policy = severity_policy or OAKIssueSeverityPolicy()

    def from_json_text(self, json_text: str) -> OAKIssueBundle:
        """Parse local JSON text and return issue drafts."""

        payload = json.loads(json_text)
        if not isinstance(payload, dict):
            raise ValueError("export bundle JSON must decode to an object")
        return self.from_payload(payload)

    def from_payload(self, payload: Dict[str, Any]) -> OAKIssueBundle:
        """Return issue drafts from an ExportBundle-like payload."""

        schema = str(payload.get("schema", ""))
        if schema != "omega_gov_qc_t.export_bundle.v0":
            raise ValueError(f"unsupported export bundle schema: {schema}")

        name = str(payload.get("name", "unnamed_bundle"))
        metadata = dict(payload.get("metadata", {}) or {})
        dataset_health = dict(metadata.get("dataset_health", {}) or {})
        ingestion_warnings = list(metadata.get("ingestion_warnings", []) or [])
        graph = dict(payload.get("graph", {}) or {})
        sources = dict(payload.get("sources", {}) or {})
        evidence = dict(payload.get("evidence", {}) or {})
        risks = dict(payload.get("risks", {}) or {})

        issues = [
            self._bundle_source_issue(name, sources),
            self._bundle_dataset_issue(name, dataset_health, ingestion_warnings),
            self._bundle_graph_issue(name, graph, evidence),
            self._bundle_risk_issue(name, risks),
        ]
        return OAKIssueBundle(
            schema="omega_gov_qc_t.oak_issue_bundle.v1.0",
            generated_at=datetime.now(timezone.utc).isoformat(),
            source_bundle=name,
            issues=tuple(issues),
            disclaimer=OAKIssueGenerator.DEFAULT_DISCLAIMER,
        )

    def _bundle_source_issue(self, name: str, sources: Dict[str, Any]) -> OAKIssueDraft:
        source_count = _count_items(sources)
        severity = self.severity_policy.source_registry(sources)
        return OAKIssueDraft(
            issue_id=f"oak-issue:{name}:source-review",
            title="OAK review: verify source registry for local bundle",
            labels=("omega-gov-qc", "oak-review", "source-governance", "bundle-review"),
            priority=severity.priority,
            issue_type="source_governance",
            source=name,
            oak_status=severity.status,
            body_markdown=(
                "## Review target\n\n"
                f"Local bundle `{name}` contains approximately `{source_count}` registered source item(s).\n\n"
                f"{_severity_markdown(severity)}\n\n"
                "## OAK boundary\n\n"
                "This is a provenance review task. It does not make an operational decision.\n\n"
                "## Acceptance checklist\n\n"
                "- [ ] Every source has locator/provenance context\n"
                "- [ ] Permission or public-use basis is documented\n"
                "- [ ] Retrieval/update date is documented when applicable\n"
                "- [ ] Non-public or sensitive data is excluded or separately reviewed"
            ),
        )

    def _bundle_dataset_issue(
        self,
        name: str,
        dataset_health: Dict[str, Any],
        ingestion_warnings: List[str],
    ) -> OAKIssueDraft:
        band = str(dataset_health.get("band", "unknown"))
        row_count = dataset_health.get("row_count", "unknown")
        missing_ratio = dataset_health.get("missing_ratio", "unknown")
        severity = self.severity_policy.dataset_health(dataset_health)
        warnings = "\n".join(f"- {warning}" for warning in ingestion_warnings) or "- None recorded"
        return OAKIssueDraft(
            issue_id=f"oak-issue:{name}:dataset-health",
            title="OAK review: validate dataset health signals for local bundle",
            labels=("omega-gov-qc", "oak-review", "dataset-health", "bundle-review"),
            priority=severity.priority,
            issue_type="dataset_health",
            source=name,
            oak_status=severity.status,
            body_markdown=(
                "## Dataset health signal\n\n"
                f"- Band: `{band}`\n"
                f"- Rows: `{row_count}`\n"
                f"- Missing ratio: `{missing_ratio}`\n\n"
                f"{_severity_markdown(severity)}\n\n"
                "## Ingestion warnings\n\n"
                f"{warnings}\n\n"
                "## OAK boundary\n\n"
                "A dataset health band is a review signal only. It must be interpreted with context.\n\n"
                "## Acceptance checklist\n\n"
                "- [ ] Required and optional fields are distinguished\n"
                "- [ ] Missing values have a documented interpretation\n"
                "- [ ] Thresholds are reviewed by an accountable owner\n"
                "- [ ] Output text preserves review-signal status"
            ),
        )

    def _bundle_graph_issue(self, name: str, graph: Dict[str, Any], evidence: Dict[str, Any]) -> OAKIssueDraft:
        node_count = _count_items(graph.get("nodes") if isinstance(graph, dict) else None)
        edge_count = _count_items(graph.get("edges") if isinstance(graph, dict) else None)
        evidence_count = _count_items(evidence)
        return OAKIssueDraft(
            issue_id=f"oak-issue:{name}:graph-semantics",
            title="OAK review: check graph and evidence semantics for local bundle",
            labels=("omega-gov-qc", "oak-review", "graph", "semantic-review", "bundle-review"),
            priority="P2",
            issue_type="graph_semantics",
            source=name,
            oak_status="semantic_review_required",
            body_markdown=(
                "## Graph summary\n\n"
                f"- Nodes: `{node_count}`\n"
                f"- Edges: `{edge_count}`\n"
                f"- Evidence items: `{evidence_count}`\n\n"
                "## OAK boundary\n\n"
                "Nodes, edges and evidence entries are model artifacts. They require vocabulary and context review.\n\n"
                "## Acceptance checklist\n\n"
                "- [ ] Relation names are descriptive and bounded\n"
                "- [ ] Confidence values have documented meaning\n"
                "- [ ] Evidence limitations are preserved\n"
                "- [ ] Counter-explanations are preserved where uncertainty exists"
            ),
        )

    def _bundle_risk_issue(self, name: str, risks: Dict[str, Any]) -> OAKIssueDraft:
        risk_count = _count_items(risks)
        severity = self.severity_policy.risk_register(risks)
        return OAKIssueDraft(
            issue_id=f"oak-issue:{name}:risk-register-review",
            title="OAK review: inspect risk register before operational use",
            labels=("omega-gov-qc", "oak-review", "bundle-review"),
            priority=severity.priority,
            issue_type="risk_register",
            source=name,
            oak_status=severity.status,
            body_markdown=(
                "## Risk-register signal\n\n"
                f"- Risk entries: `{risk_count}`\n\n"
                f"{_severity_markdown(severity)}\n\n"
                "## OAK boundary\n\n"
                "Risk entries guide review and mitigation planning. They are not final authority.\n\n"
                "## Acceptance checklist\n\n"
                "- [ ] High-impact use cases are identified\n"
                "- [ ] Human review path is documented\n"
                "- [ ] Reversibility and appeal/correction path are documented\n"
                "- [ ] Privacy and security gates are checked where applicable"
            ),
        )


def _severity_markdown(severity: SeverityDecision) -> str:
    reasons = "\n".join(f"- `{reason}`" for reason in severity.reasons)
    return (
        "## Local severity\n\n"
        f"- Priority: `{severity.priority}`\n"
        f"- Status: `{severity.status}`\n"
        f"- Note: {severity.oak_note}\n\n"
        "### Reasons\n\n"
        f"{reasons}"
    )


def _count_items(value: Any) -> int:
    """Best-effort count for exported bundle sections."""

    if value is None:
        return 0
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ("items", "records", "sources", "nodes", "edges", "evidence", "risks"):
            nested = value.get(key)
            if isinstance(nested, list):
                return len(nested)
            if isinstance(nested, dict):
                return len(nested)
        return len(value)
    return 0
