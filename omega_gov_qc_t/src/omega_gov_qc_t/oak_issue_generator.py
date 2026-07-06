"""OAK-safe GitHub issue draft generator for Ω-GOV-QC-T.

The generator creates local issue *drafts* from demo artifacts. It does not open
GitHub issues, does not accuse anyone, and does not classify review signals as
final findings.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from typing import Any, Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class OAKIssueDraft:
    """A review-safe GitHub issue draft.

    The body is intentionally framed as review work, not as a conclusion.
    """

    issue_id: str
    title: str
    body_markdown: str
    labels: Tuple[str, ...]
    priority: str
    issue_type: str
    source: str
    oak_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OAKIssueBundle:
    """Bundle of local issue drafts."""

    schema: str
    generated_at: str
    source_bundle: str
    issues: Tuple[OAKIssueDraft, ...]
    disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "source_bundle": self.source_bundle,
            "issues": [issue.to_dict() for issue in self.issues],
            "disclaimer": self.disclaimer,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines: List[str] = [
            "# Ω-GOV-QC-T OAK Issue Drafts",
            "",
            f"Generated at: {self.generated_at}",
            f"Source bundle: `{self.source_bundle}`",
            "",
            "> These are local review drafts. They are not accusations, findings, or public-authority decisions.",
            "",
            "## Summary",
            "",
            f"- Draft issues: {len(self.issues)}",
            "- Network fetch: disabled",
            "- Auto-publish to GitHub: disabled",
            "- Human review: required before opening any issue",
            "",
        ]
        for issue in self.issues:
            lines.extend(
                [
                    f"## {issue.title}",
                    "",
                    f"- ID: `{issue.issue_id}`",
                    f"- Type: `{issue.issue_type}`",
                    f"- Priority: `{issue.priority}`",
                    f"- OAK status: `{issue.oak_status}`",
                    f"- Labels: {', '.join(issue.labels)}",
                    "",
                    issue.body_markdown,
                    "",
                ]
            )
        lines.extend(["## Disclaimer", "", self.disclaimer, ""])
        return "\n".join(lines)


class OAKIssueGenerator:
    """Generate conservative local issue drafts from artifacts."""

    DEFAULT_DISCLAIMER = (
        "Dataset, graph and risk signals are review aids only. They do not establish "
        "fraud, misconduct, illegality, negligence or final institutional findings. "
        "Any high-impact use requires authorized sources, privacy review, security review, "
        "legal/contextual review and accountable human oversight."
    )

    def from_demo_artifacts(self, artifacts: Any) -> OAKIssueBundle:
        """Create local issue drafts from MunicipalDemoArtifacts-like objects."""

        metadata = dict(getattr(artifacts, "metadata", {}) or {})
        dataset_health = dict(metadata.get("dataset_health", {}) or {})
        ingestion_warnings = list(metadata.get("ingestion_warnings", []) or [])
        oak_deployable = bool(metadata.get("oak_deployable", False))

        issues = [
            self._source_authorization_issue(),
            self._dataset_health_issue(dataset_health, ingestion_warnings),
            self._oak_human_review_issue(oak_deployable),
            self._graph_semantics_issue(),
        ]
        return OAKIssueBundle(
            schema="omega_gov_qc_t.oak_issue_bundle.v0.8",
            generated_at=datetime.now(timezone.utc).isoformat(),
            source_bundle="municipal_demo_bundle",
            issues=tuple(issues),
            disclaimer=self.DEFAULT_DISCLAIMER,
        )

    def _source_authorization_issue(self) -> OAKIssueDraft:
        return OAKIssueDraft(
            issue_id="oak-issue:source-authorization-before-pilot",
            title="OAK review: verify source authorization before any municipal pilot",
            labels=("omega-gov-qc", "oak-review", "source-governance"),
            priority="P1",
            issue_type="source_governance",
            source="municipal_demo_local_csv",
            oak_status="review_required_before_pilot",
            body_markdown=(
                "## Review target\n\n"
                "Confirm that every dataset used beyond the embedded demo is public, authorized, "
                "licensed, or otherwise explicitly allowed for the intended pilot.\n\n"
                "## OAK boundary\n\n"
                "This issue does not claim that any source is invalid. It only blocks promotion "
                "from demo to pilot until source rights and provenance are documented.\n\n"
                "## Acceptance checklist\n\n"
                "- [ ] Source locator documented\n"
                "- [ ] Permission/license documented\n"
                "- [ ] Retrieval date documented\n"
                "- [ ] Data owner or publisher identified where applicable\n"
                "- [ ] Privacy/security review completed if data is not purely public"
            ),
        )

    def _dataset_health_issue(self, dataset_health: Dict[str, Any], ingestion_warnings: Sequence[str]) -> OAKIssueDraft:
        band = str(dataset_health.get("band", "unknown"))
        missing_ratio = dataset_health.get("missing_ratio", "unknown")
        duplicate_ratio = dataset_health.get("duplicate_ratio", "unknown")
        warnings = "\n".join(f"- {warning}" for warning in ingestion_warnings) or "- None recorded"
        priority = "P1" if band in {"poor", "blocked"} else "P2"
        return OAKIssueDraft(
            issue_id="oak-issue:dataset-health-baseline",
            title="OAK review: document dataset health baseline before dashboards",
            labels=("omega-gov-qc", "oak-review", "dataset-health"),
            priority=priority,
            issue_type="dataset_health",
            source="dataset:municipal_demo",
            oak_status="review_signal_not_final_judgment",
            body_markdown=(
                "## Dataset health signal\n\n"
                f"- Band: `{band}`\n"
                f"- Missing ratio: `{missing_ratio}`\n"
                f"- Duplicate ratio: `{duplicate_ratio}`\n\n"
                "## Ingestion warnings\n\n"
                f"{warnings}\n\n"
                "## OAK boundary\n\n"
                "Dataset health signals identify review needs. They are not evidence of wrongdoing "
                "and must not be used as final public-sector judgments.\n\n"
                "## Acceptance checklist\n\n"
                "- [ ] Expected schema documented\n"
                "- [ ] Missing fields classified as required/optional\n"
                "- [ ] Duplicate policy documented\n"
                "- [ ] Health thresholds reviewed by accountable owner\n"
                "- [ ] Dashboard text states review-signal status"
            ),
        )

    def _oak_human_review_issue(self, oak_deployable: bool) -> OAKIssueDraft:
        return OAKIssueDraft(
            issue_id="oak-issue:human-review-gate",
            title="OAK review: confirm human-review gate for high-impact contexts",
            labels=("omega-gov-qc", "oak-gate", "human-review"),
            priority="P1",
            issue_type="oak_gate",
            source="OAKGate",
            oak_status="deployable_demo_only" if oak_deployable else "blocked_until_review",
            body_markdown=(
                "## Gate target\n\n"
                "Make the human-review requirement explicit before using generated reports, risk "
                "signals, dataset health, or graph exports in high-impact settings.\n\n"
                "## OAK boundary\n\n"
                "Automation supports triage and explanation. It must not replace accountable "
                "public-sector, legal, domain or institutional review.\n\n"
                "## Acceptance checklist\n\n"
                "- [ ] High-impact contexts defined\n"
                "- [ ] Human reviewer role documented\n"
                "- [ ] Appeal/correction path documented\n"
                "- [ ] Report disclaimer visible\n"
                "- [ ] Non-accusation policy visible"
            ),
        )

    def _graph_semantics_issue(self) -> OAKIssueDraft:
        return OAKIssueDraft(
            issue_id="oak-issue:graph-semantics-review",
            title="OAK review: validate GovGraph and GraphML relation semantics",
            labels=("omega-gov-qc", "graph", "semantic-review"),
            priority="P2",
            issue_type="graph_semantics",
            source="GovGraph/GraphML",
            oak_status="semantic_review_required",
            body_markdown=(
                "## Review target\n\n"
                "Check that node types, edge relation names, confidence values and GraphML exports "
                "remain descriptive and non-accusatory.\n\n"
                "## OAK boundary\n\n"
                "A graph edge represents a modeled relationship or review signal. It is not by "
                "itself proof of wrongdoing or institutional failure.\n\n"
                "## Acceptance checklist\n\n"
                "- [ ] Relation vocabulary documented\n"
                "- [ ] Confidence meaning documented\n"
                "- [ ] GraphML consumers warned about review-signal status\n"
                "- [ ] Counter-explanations preserved where evidence is uncertain\n"
                "- [ ] No defamatory or final-judgment relation labels"
            ),
        )
