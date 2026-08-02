"""Ω-HYPERKNOWLEDGE-T∞ R0.3 knowledge-cell core.

The module turns broad theory nodes into traceable cells that separate claims,
evidence, counterexamples, implementations, tests, results, risks, and OAK
history. It is deliberately dependency-light and fail-closed: structural
completeness never implies scientific truth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence


OAK_STATUSES = {
    "IDEA",
    "ACTIVE",
    "FORMALIZED",
    "IMPLEMENTED",
    "SIMULATED",
    "DEMONSTRATED",
    "MEASURED",
    "CANONICAL",
    "CERTIFIED_MATH",
    "CERTIFIED_COMPUTATIONAL",
    "CERTIFIED_PHYSICS",
    "REFUTED",
    "REFORMULATED",
    "ARCHIVED",
}

EVIDENCE_KINDS = {
    "source",
    "equation",
    "derivation",
    "code",
    "test",
    "dataset",
    "baseline",
    "simulation",
    "measurement",
    "result",
    "proof",
    "counterexample",
    "negative_memory",
    "external_reference",
}

PROMOTION_ORDER = (
    "IDEA",
    "ACTIVE",
    "FORMALIZED",
    "IMPLEMENTED",
    "SIMULATED",
    "DEMONSTRATED",
    "MEASURED",
    "CANONICAL",
)


def stable_id(prefix: str, *parts: object) -> str:
    raw = "\x1f".join(str(part).strip() for part in parts).encode("utf-8")
    return f"{prefix}_{sha256(raw).hexdigest()[:20]}"


def normalize_key(text: str) -> str:
    text = text.casefold().strip()
    text = re.sub(r"[^a-z0-9à-öø-ÿα-ω]+", " ", text)
    return " ".join(text.split())


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    kind: str
    title: str
    source_path: str | None = None
    locator: str | None = None
    content_hash: str | None = None
    status: str = "candidate"
    supports_claim_ids: tuple[str, ...] = ()
    contradicts_claim_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.kind not in EVIDENCE_KINDS:
            issues.append(f"unsupported evidence kind: {self.kind}")
        if not self.evidence_id.strip():
            issues.append("evidence_id is required")
        if not self.title.strip():
            issues.append(f"{self.evidence_id}: title is required")
        if self.status not in {"candidate", "verified_metadata", "reproduced", "disputed", "refuted"}:
            issues.append(f"{self.evidence_id}: unsupported evidence status {self.status}")
        return issues


@dataclass(frozen=True)
class ClaimAtom:
    claim_id: str
    text: str
    canonical_key: str
    domain: str
    polarity: str = "affirm"
    scope: str = "unspecified"
    status: str = "hypothesis"
    assumptions: tuple[str, ...] = ()
    failure_conditions: tuple[str, ...] = ()
    source_paths: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.claim_id.strip():
            issues.append("claim_id is required")
        if not self.text.strip():
            issues.append(f"{self.claim_id}: claim text is required")
        if not self.canonical_key.strip():
            issues.append(f"{self.claim_id}: canonical_key is required")
        if self.polarity not in {"affirm", "deny", "uncertain"}:
            issues.append(f"{self.claim_id}: unsupported polarity {self.polarity}")
        if self.status not in {
            "idea",
            "hypothesis",
            "prediction",
            "observation",
            "measured_claim",
            "theorem_candidate",
            "proven",
            "refuted",
            "context_dependent",
        }:
            issues.append(f"{self.claim_id}: unsupported claim status {self.status}")
        return issues


@dataclass(frozen=True)
class OakTransition:
    transition_id: str
    timestamp: str
    from_status: str
    to_status: str
    cause: str
    evidence_ids: tuple[str, ...] = ()
    residues: tuple[str, ...] = ()
    approved_by: str | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.from_status not in OAK_STATUSES:
            issues.append(f"{self.transition_id}: unknown from_status {self.from_status}")
        if self.to_status not in OAK_STATUSES:
            issues.append(f"{self.transition_id}: unknown to_status {self.to_status}")
        try:
            _parse_timestamp(self.timestamp)
        except ValueError:
            issues.append(f"{self.transition_id}: invalid timestamp {self.timestamp}")
        if not self.cause.strip():
            issues.append(f"{self.transition_id}: transition cause is required")
        return issues


@dataclass
class KnowledgeCell:
    cell_id: str
    subject: str
    definition: str
    domain: str
    oak_status: str
    claims: list[ClaimAtom] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    transitions: list[OakTransition] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    source_paths: list[str] = field(default_factory=list)
    owner: str | None = None
    public_disclosure: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "KnowledgeCell":
        return cls(
            cell_id=str(payload["cell_id"]),
            subject=str(payload["subject"]),
            definition=str(payload.get("definition", "")),
            domain=str(payload.get("domain", "cross-domain")),
            oak_status=str(payload.get("oak_status", "IDEA")),
            claims=[ClaimAtom(**item) for item in payload.get("claims", [])],
            evidence=[EvidenceRecord(**item) for item in payload.get("evidence", [])],
            transitions=[OakTransition(**item) for item in payload.get("transitions", [])],
            risks=list(payload.get("risks", [])),
            next_actions=list(payload.get("next_actions", [])),
            aliases=list(payload.get("aliases", [])),
            source_paths=list(payload.get("source_paths", [])),
            owner=payload.get("owner"),
            public_disclosure=bool(payload.get("public_disclosure", False)),
            metadata=dict(payload.get("metadata", {})),
        )

    @classmethod
    def read(cls, path: str | Path) -> "KnowledgeCell":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def write(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target

    def evidence_by_kind(self, kind: str) -> list[EvidenceRecord]:
        return [record for record in self.evidence if record.kind == kind]

    def claim_evidence(self, claim_id: str) -> list[EvidenceRecord]:
        return [
            record
            for record in self.evidence
            if claim_id in record.supports_claim_ids or claim_id in record.contradicts_claim_ids
        ]

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.cell_id.strip():
            issues.append("cell_id is required")
        if not self.subject.strip():
            issues.append(f"{self.cell_id}: subject is required")
        if not self.definition.strip():
            issues.append(f"{self.cell_id}: definition is required")
        if self.oak_status not in OAK_STATUSES:
            issues.append(f"{self.cell_id}: unsupported OAK status {self.oak_status}")

        claim_ids = [claim.claim_id for claim in self.claims]
        evidence_ids = [record.evidence_id for record in self.evidence]
        if len(claim_ids) != len(set(claim_ids)):
            issues.append(f"{self.cell_id}: duplicate claim IDs")
        if len(evidence_ids) != len(set(evidence_ids)):
            issues.append(f"{self.cell_id}: duplicate evidence IDs")

        claim_id_set = set(claim_ids)
        evidence_id_set = set(evidence_ids)
        for claim in self.claims:
            issues.extend(claim.validate())
        for record in self.evidence:
            issues.extend(record.validate())
            unknown = (set(record.supports_claim_ids) | set(record.contradicts_claim_ids)) - claim_id_set
            if unknown:
                issues.append(f"{record.evidence_id}: unknown claim references {sorted(unknown)}")

        previous_time: datetime | None = None
        previous_to: str | None = None
        for transition in self.transitions:
            issues.extend(transition.validate())
            try:
                current_time = _parse_timestamp(transition.timestamp)
            except ValueError:
                continue
            if previous_time is not None and current_time < previous_time:
                issues.append(f"{self.cell_id}: transitions are not chronological")
            if previous_to is not None and transition.from_status != previous_to:
                issues.append(
                    f"{transition.transition_id}: from_status {transition.from_status} does not continue {previous_to}"
                )
            unknown_evidence = set(transition.evidence_ids) - evidence_id_set
            if unknown_evidence:
                issues.append(
                    f"{transition.transition_id}: unknown evidence references {sorted(unknown_evidence)}"
                )
            previous_time = current_time
            previous_to = transition.to_status

        if self.transitions and self.transitions[-1].to_status != self.oak_status:
            issues.append(
                f"{self.cell_id}: oak_status {self.oak_status} differs from latest transition "
                f"{self.transitions[-1].to_status}"
            )
        return issues


@dataclass(frozen=True)
class AuditFinding:
    finding_id: str
    cell_id: str
    severity: str
    category: str
    message: str
    claim_id: str | None = None
    evidence_ids: tuple[str, ...] = ()
    suggested_action: str | None = None


@dataclass
class AuditReport:
    schema: str
    findings: list[AuditFinding]
    metrics: dict[str, float | int]
    oak_boundary: str = (
        "Structural audit only. Completeness, source count, or passing tests do not certify scientific truth."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "findings": [asdict(item) for item in self.findings],
            "metrics": self.metrics,
            "oak_boundary": self.oak_boundary,
        }


def _finding(
    cell: KnowledgeCell,
    severity: str,
    category: str,
    message: str,
    *,
    claim_id: str | None = None,
    evidence_ids: Sequence[str] = (),
    suggested_action: str | None = None,
) -> AuditFinding:
    return AuditFinding(
        finding_id=stable_id("finding", cell.cell_id, severity, category, claim_id or "", message),
        cell_id=cell.cell_id,
        severity=severity,
        category=category,
        message=message,
        claim_id=claim_id,
        evidence_ids=tuple(evidence_ids),
        suggested_action=suggested_action,
    )


def audit_cells(cells: Sequence[KnowledgeCell]) -> AuditReport:
    findings: list[AuditFinding] = []
    total_claims = 0
    claims_with_evidence = 0
    claims_with_failure_condition = 0
    traced_nodes = 0

    for cell in cells:
        validation_issues = cell.validate()
        for issue in validation_issues:
            findings.append(
                _finding(
                    cell,
                    "P0",
                    "structural_integrity",
                    issue,
                    suggested_action="Repair schema or references before promotion.",
                )
            )

        if cell.source_paths:
            traced_nodes += 1
        if not cell.next_actions:
            findings.append(
                _finding(
                    cell,
                    "P2",
                    "missing_next_action",
                    "Knowledge cell has no explicit next action.",
                    suggested_action="Define the smallest discriminating test or documentation step.",
                )
            )

        if cell.public_disclosure and any(
            token in normalize_key(" ".join(cell.risks))
            for token in ("patent", "brevet", "secret commercial", "confidential")
        ):
            findings.append(
                _finding(
                    cell,
                    "P0",
                    "ip_disclosure_risk",
                    "Public disclosure is active while an IP/confidentiality risk is recorded.",
                    suggested_action="Run IPGate and classify public, patentable, trade-secret, or confidential status.",
                )
            )

        evidence_ids = {record.evidence_id for record in cell.evidence}
        kinds = {record.kind for record in cell.evidence}
        for claim in cell.claims:
            total_claims += 1
            linked = cell.claim_evidence(claim.claim_id)
            if linked:
                claims_with_evidence += 1
            else:
                findings.append(
                    _finding(
                        cell,
                        "P2",
                        "unsupported_claim",
                        "Claim has no linked supporting or contradicting evidence.",
                        claim_id=claim.claim_id,
                        suggested_action="Link a source, equation, test, result, measurement, proof, or counterexample.",
                    )
                )
            if claim.failure_conditions:
                claims_with_failure_condition += 1
            else:
                findings.append(
                    _finding(
                        cell,
                        "P2",
                        "missing_failure_condition",
                        "Claim has no explicit failure or falsification condition.",
                        claim_id=claim.claim_id,
                        suggested_action="State an observation or result that would weaken or refute the claim.",
                    )
                )

            if claim.domain == "physics":
                linked_kinds = {record.kind for record in linked}
                if "equation" not in linked_kinds:
                    findings.append(
                        _finding(
                            cell,
                            "P0",
                            "physics_without_equation",
                            "Physics claim has no linked equation or dimensional model.",
                            claim_id=claim.claim_id,
                            suggested_action="Add equations, variables, units, assumptions, and validity domain.",
                        )
                    )
                if cell.oak_status in {"MEASURED", "CANONICAL", "CERTIFIED_PHYSICS"} and "measurement" not in linked_kinds:
                    findings.append(
                        _finding(
                            cell,
                            "P0",
                            "physics_without_measurement",
                            "Promoted physics claim has no linked measurement.",
                            claim_id=claim.claim_id,
                            suggested_action="Attach calibrated measurements and uncertainty before promotion.",
                        )
                    )

        if "result" in kinds and "baseline" not in kinds:
            findings.append(
                _finding(
                    cell,
                    "P0",
                    "result_without_baseline",
                    "Result evidence exists without a baseline record.",
                    evidence_ids=tuple(sorted(evidence_ids)),
                    suggested_action="Add a fair baseline with matched protocol and metrics.",
                )
            )
        if "code" in kinds and "test" not in kinds:
            findings.append(
                _finding(
                    cell,
                    "P1",
                    "code_without_test",
                    "Implementation evidence exists without test evidence.",
                    suggested_action="Add deterministic unit or integration tests.",
                )
            )
        if cell.oak_status == "CANONICAL" and not ({"proof", "measurement", "result"} & kinds):
            findings.append(
                _finding(
                    cell,
                    "P0",
                    "canonical_without_decisive_evidence",
                    "Canonical status lacks proof, measurement, or result evidence.",
                    suggested_action="Downgrade status or attach decisive reproducible evidence.",
                )
            )

    cell_count = len(cells)
    metrics: dict[str, float | int] = {
        "cells": cell_count,
        "claims": total_claims,
        "findings": len(findings),
        "evidence_coverage": round(claims_with_evidence / total_claims, 4) if total_claims else 1.0,
        "falsification_coverage": round(claims_with_failure_condition / total_claims, 4) if total_claims else 1.0,
        "traceability_coverage": round(traced_nodes / cell_count, 4) if cell_count else 1.0,
    }
    findings.sort(key=lambda item: (item.severity, item.category, item.cell_id, item.claim_id or ""))
    return AuditReport(schema="omega_hyperknowledge.audit.v0.3", findings=findings, metrics=metrics)


def read_cells(paths: Iterable[str | Path]) -> list[KnowledgeCell]:
    return [KnowledgeCell.read(path) for path in paths]
