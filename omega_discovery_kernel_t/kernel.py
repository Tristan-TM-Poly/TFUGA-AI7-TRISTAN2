"""Closed-loop discovery ledger and bridges to HyperKnowledge and MorphIR."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from omega_generator_discovery_t.core import MorphIR
from omega_wiki_t.knowledge_cell import ClaimAtom, EvidenceRecord, KnowledgeCell

from .catalog import EVENT_TYPES, catalog_manifest, event_spec
from .events import DiscoveryEvent, canonical_json, parse_timestamp, stable_id


CORE_LOOP_EVENT_TYPES = (
    "ObservationEvent",
    "ClaimEvent",
    "GeneratorCandidate",
    "ExperimentSpec",
    "ResultPacket",
    "OAKTransition",
    "MMinusRule",
    "ActionProposal",
)

PROMOTED_STATUSES = {
    "DEMONSTRATED",
    "MEASURED",
    "CANONICAL",
    "CERTIFIED_MATH",
    "CERTIFIED_COMPUTATIONAL",
    "CERTIFIED_PHYSICS",
}


@dataclass(frozen=True, slots=True)
class KernelFinding:
    finding_id: str
    severity: str
    category: str
    message: str
    event_id: str | None = None
    subject_id: str | None = None
    suggested_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KernelAudit:
    findings: list[KernelFinding]
    metrics: dict[str, float | int]
    subject_status: dict[str, str]
    boundary: str = (
        "Workflow integrity and evidence routing only. A complete loop does not certify a scientific claim."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "omega_discovery_kernel.audit.v0.2",
            "findings": [item.to_dict() for item in self.findings],
            "metrics": self.metrics,
            "subject_status": self.subject_status,
            "boundary": self.boundary,
        }


@dataclass
class DiscoveryLedger:
    events: list[DiscoveryEvent] = field(default_factory=list)

    @classmethod
    def from_dicts(cls, values: Iterable[Mapping[str, Any]]) -> "DiscoveryLedger":
        ledger = cls()
        for value in values:
            ledger.append(DiscoveryEvent.from_dict(value))
        return ledger

    @classmethod
    def read_jsonl(cls, path: str | Path) -> "DiscoveryLedger":
        values = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                values.append(json.loads(line))
        return cls.from_dicts(values)

    def event_map(self) -> dict[str, DiscoveryEvent]:
        return {event.event_id: event for event in self.events}

    def events_for_subject(self, subject_id: str) -> list[DiscoveryEvent]:
        return [event for event in self.events if event.subject_id == subject_id]

    def append(self, event: DiscoveryEvent) -> DiscoveryEvent:
        issues = event.validate()
        if issues:
            raise ValueError("; ".join(issues))
        existing = self.event_map()
        if event.event_id in existing:
            raise ValueError(f"Duplicate event_id: {event.event_id}")
        unknown = [parent for parent in event.parent_ids if parent not in existing]
        if unknown:
            raise ValueError(f"Unknown parent events: {unknown}")
        if self.events and parse_timestamp(event.timestamp) < parse_timestamp(self.events[-1].timestamp):
            raise ValueError("Events must be appended in chronological order")
        for parent_id in event.parent_ids:
            parent = existing[parent_id]
            if parent.subject_id != event.subject_id and not bool(event.payload.get("cross_subject", False)):
                raise ValueError(f"Cross-subject parent {parent_id} requires payload.cross_subject=true")
        self._enforce_transition_gates(event, existing)
        self.events.append(event)
        return event

    def extend(self, events: Iterable[DiscoveryEvent]) -> None:
        for event in events:
            self.append(event)

    def _ancestors(self, event: DiscoveryEvent, existing: Mapping[str, DiscoveryEvent]) -> list[DiscoveryEvent]:
        result: list[DiscoveryEvent] = []
        pending = list(event.parent_ids)
        visited: set[str] = set()
        while pending:
            event_id = pending.pop()
            if event_id in visited or event_id not in existing:
                continue
            visited.add(event_id)
            parent = existing[event_id]
            result.append(parent)
            pending.extend(parent.parent_ids)
        return result

    def _enforce_transition_gates(
        self,
        event: DiscoveryEvent,
        existing: Mapping[str, DiscoveryEvent],
    ) -> None:
        parents = [existing[parent] for parent in event.parent_ids]
        ancestors = parents + self._ancestors(event, existing)
        ancestor_types = {item.event_type for item in ancestors}
        spec = event_spec(event.event_type)
        if spec.required_parent_any and not (set(spec.required_parent_any) & ancestor_types):
            raise ValueError(
                f"{event.event_type} requires ancestry containing one of "
                f"{spec.required_parent_any}; observed {sorted(ancestor_types)}"
            )
        if event.event_type == "OAKTransition":
            target = str(event.payload.get("to_status", ""))
            if target in PROMOTED_STATUSES and "ResultPacket" not in ancestor_types:
                raise ValueError(f"Promotion to {target} requires a ResultPacket ancestor")
        if event.event_type == "MMinusRule":
            failed_result = any(
                item.event_type == "ResultPacket" and not bool(item.payload.get("success", False))
                for item in ancestors
            )
            refutation = any(
                item.event_type in {"RefutationEvent", "ModelRejectedEvent"}
                or (item.event_type == "OAKTransition" and item.payload.get("to_status") == "REFUTED")
                for item in ancestors
            )
            if not (failed_result or refutation):
                raise ValueError("MMinusRule requires a failed ResultPacket or refutation ancestor")
        if event.event_type == "PromotionEvent" and not ({"ReplicationEvent", "ProofEvent"} & ancestor_types):
            raise ValueError("PromotionEvent requires a ReplicationEvent or ProofEvent ancestor")
        if event.event_type in {"PublicationEvent", "DeploymentEvent", "RetirementEvent"} and not event.human_approval:
            raise ValueError(f"{event.event_type} requires explicit human approval")

    def ledger_hash(self) -> str:
        return sha256(canonical_json([event.event_hash for event in self.events]).encode("utf-8")).hexdigest()

    def validate(self) -> list[str]:
        issues: list[str] = []
        reconstructed = DiscoveryLedger()
        for event in self.events:
            try:
                reconstructed.append(event)
            except ValueError as exc:
                issues.append(f"{event.event_id}: {exc}")
        return issues

    def subject_event_types(self, subject_id: str) -> set[str]:
        return {event.event_type for event in self.events_for_subject(subject_id)}

    def missing_event_types(self, subject_id: str) -> tuple[str, ...]:
        observed = self.subject_event_types(subject_id)
        return tuple(event_type for event_type in CORE_LOOP_EVENT_TYPES if event_type not in observed)

    def optional_event_types(self, subject_id: str) -> tuple[str, ...]:
        observed = self.subject_event_types(subject_id)
        return tuple(event_type for event_type in EVENT_TYPES if event_type in observed and event_type not in CORE_LOOP_EVENT_TYPES)

    def closed_loop_status(self, subject_id: str) -> str:
        missing = self.missing_event_types(subject_id)
        return "closed_loop_recorded_not_certified" if not missing else "open_loop_missing_" + "_".join(missing)

    def audit(self) -> KernelAudit:
        findings: list[KernelFinding] = []
        integrity_issues = self.validate()
        for issue in integrity_issues:
            findings.append(
                KernelFinding(
                    finding_id=stable_id("finding", "integrity", issue),
                    severity="P0",
                    category="ledger_integrity",
                    message=issue,
                    suggested_action="Repair event ordering, parentage, hashes, catalog contracts, or OAK gates.",
                )
            )

        subjects = sorted({event.subject_id for event in self.events})
        subject_status: dict[str, str] = {}
        for subject_id in subjects:
            missing = self.missing_event_types(subject_id)
            subject_status[subject_id] = self.closed_loop_status(subject_id)
            if missing:
                findings.append(
                    KernelFinding(
                        finding_id=stable_id("finding", subject_id, "missing", missing),
                        severity="P2",
                        category="open_discovery_loop",
                        message=f"Subject is missing core events: {', '.join(missing)}",
                        subject_id=subject_id,
                        suggested_action=f"Create the next missing core event: {missing[0]}",
                    )
                )

        results = [event for event in self.events if event.event_type == "ResultPacket"]
        failed_results = [event for event in results if not bool(event.payload.get("success", False))]
        mminus = [event for event in self.events if event.event_type == "MMinusRule"]
        event_map = self.event_map()
        failed_with_mminus = 0
        for result in failed_results:
            if any(
                result.event_id in event.parent_ids
                or result.event_id in {ancestor.event_id for ancestor in self._ancestors(event, event_map)}
                for event in mminus
            ):
                failed_with_mminus += 1
            else:
                findings.append(
                    KernelFinding(
                        finding_id=stable_id("finding", result.event_id, "missing_mminus"),
                        severity="P1",
                        category="failed_result_without_negative_memory",
                        message="Failed result has not yet produced a reusable M-minus rule.",
                        event_id=result.event_id,
                        subject_id=result.subject_id,
                        suggested_action="Encode the failure context, prohibited inference, and reusable rule.",
                    )
                )

        unsafe_actions = [
            event
            for event in self.events
            if event.event_type in {"ActionProposal", "DeploymentEvent", "PublicationEvent"}
            and (
                (event.status == "autonomous_execution" and (not event.reversible or not event.human_approval))
                or (event.event_type in {"DeploymentEvent", "PublicationEvent"} and not event.human_approval)
            )
        ]
        for event in unsafe_actions:
            findings.append(
                KernelFinding(
                    finding_id=stable_id("finding", event.event_id, "unsafe_action"),
                    severity="P0",
                    category="unsafe_action",
                    message="External or autonomous action is irreversible or lacks explicit human approval.",
                    event_id=event.event_id,
                    subject_id=event.subject_id,
                    suggested_action="Downgrade to draft/simulation or obtain explicit approval with rollback.",
                )
            )

        total = len(self.events)
        complete_subjects = sum(not self.missing_event_types(subject) for subject in subjects)
        observed_types = {event.event_type for event in self.events}
        metrics: dict[str, float | int] = {
            "events": total,
            "subjects": len(subjects),
            "complete_subjects": complete_subjects,
            "closed_loop_coverage": round(complete_subjects / len(subjects), 4) if subjects else 1.0,
            "catalog_event_types": len(EVENT_TYPES),
            "observed_event_types": len(observed_types),
            "event_catalog_coverage": round(len(observed_types) / len(EVENT_TYPES), 4),
            "failed_results": len(failed_results),
            "negative_memory_coverage": round(failed_with_mminus / len(failed_results), 4) if failed_results else 1.0,
            "provenance_coverage": round(
                sum(bool(event.provenance or event.source_hash) for event in self.events) / total, 4
            ) if total else 1.0,
            "unit_coverage": round(sum(bool(event.units) for event in results) / len(results), 4) if results else 1.0,
            "uncertainty_coverage": round(
                sum(bool(event.uncertainty) for event in results) / len(results), 4
            ) if results else 1.0,
        }
        findings.sort(key=lambda item: (item.severity, item.category, item.subject_id or "", item.event_id or ""))
        return KernelAudit(findings=findings, metrics=metrics, subject_status=subject_status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "omega_discovery_kernel.ledger.v0.2",
            "ledger_hash": self.ledger_hash(),
            "core_loop_event_types": list(CORE_LOOP_EVENT_TYPES),
            "events": [event.to_dict() for event in self.events],
        }

    def write(self, output_dir: str | Path) -> Path:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        audit = self.audit()
        manifest = {
            "schema": "omega_discovery_kernel.manifest.v0.2",
            "event_count": len(self.events),
            "subject_count": len(audit.subject_status),
            "ledger_hash": self.ledger_hash(),
            "event_type_count": len(EVENT_TYPES),
            "event_types": list(EVENT_TYPES),
            "core_loop_event_types": list(CORE_LOOP_EVENT_TYPES),
            "metrics": audit.metrics,
            "oak_status": "R0.2_CLOSED_LOOP_LEDGER_NOT_SCIENTIFIC_CERTIFICATION",
        }
        (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output / "event-catalog.json").write_text(
            json.dumps(catalog_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "ledger.json").write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with (output / "events.jsonl").open("w", encoding="utf-8") as stream:
            for event in self.events:
                stream.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        (output / "audit.json").write_text(json.dumps(audit.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output / "graph.json").write_text(json.dumps(self.graph_view(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output / "report.md").write_text(self.render_report(audit), encoding="utf-8")
        return output

    def graph_view(self) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": event.event_id,
                    "type": event.event_type,
                    "family": event_spec(event.event_type).family,
                    "subject_id": event.subject_id,
                    "status": event.status,
                    "timestamp": event.timestamp,
                }
                for event in self.events
            ],
            "edges": [
                {"source": parent_id, "target": event.event_id, "relation": "precedes_and_supports"}
                for event in self.events
                for parent_id in event.parent_ids
            ],
        }

    def render_report(self, audit: KernelAudit | None = None) -> str:
        audit = audit or self.audit()
        lines = [
            "# Ω-DISCOVERY-KERNEL-T∞ R0.2 report",
            "",
            f"- Events: **{len(self.events)}**",
            f"- Subjects: **{len(audit.subject_status)}**",
            f"- Catalog: **{len(EVENT_TYPES)} event contracts**",
            f"- Ledger hash: `{self.ledger_hash()}`",
            "",
            "## Closed-loop status",
            "",
        ]
        for subject_id, status in audit.subject_status.items():
            lines.append(f"- `{subject_id}`: `{status}`")
        lines.extend(["", "## Metrics", "", "| Metric | Value |", "|---|---:|"])
        for key, value in audit.metrics.items():
            lines.append(f"| {key} | {value} |")
        lines.extend(["", "## Findings", ""])
        if not audit.findings:
            lines.append("No structural findings.")
        for finding in audit.findings:
            lines.append(f"- **{finding.severity} {finding.category}** — {finding.message}")
        lines.extend([
            "",
            "## OAK boundary",
            "",
            audit.boundary,
            "A complete event chain records that the loop was executed; it does not establish causal truth,",
            "scientific superiority, patentability, safety, or product-market fit.",
            "",
        ])
        return "\n".join(lines)


def claim_events_from_cell(
    cell: KnowledgeCell,
    observation_event: DiscoveryEvent,
    *,
    timestamp: str,
) -> list[DiscoveryEvent]:
    if observation_event.event_type != "ObservationEvent":
        raise ValueError("observation_event must be an ObservationEvent")
    events: list[DiscoveryEvent] = []
    for claim in cell.claims:
        events.append(
            DiscoveryEvent.create(
                "ClaimEvent",
                cell.cell_id,
                timestamp,
                parent_ids=(observation_event.event_id,),
                provenance=tuple(claim.source_paths or cell.source_paths),
                domain=claim.domain,
                status=claim.status,
                payload={
                    "claim_id": claim.claim_id,
                    "text": claim.text,
                    "canonical_key": claim.canonical_key,
                    "polarity": claim.polarity,
                    "scope": claim.scope,
                    "assumptions": list(claim.assumptions),
                    "failure_conditions": list(claim.failure_conditions),
                    "knowledge_cell_id": cell.cell_id,
                },
            )
        )
    return events


def generator_event_from_morph_ir(
    morph: MorphIR,
    claim_event: DiscoveryEvent,
    *,
    timestamp: str,
    subject_id: str | None = None,
) -> DiscoveryEvent:
    if claim_event.event_type != "ClaimEvent":
        raise ValueError("claim_event must be a ClaimEvent")
    return DiscoveryEvent.create(
        "GeneratorCandidate",
        subject_id or claim_event.subject_id,
        timestamp,
        parent_ids=(claim_event.event_id,),
        provenance=claim_event.provenance,
        domain=morph.domain,
        status=morph.status,
        payload={
            "name": morph.name,
            "domain": morph.domain,
            "codomain": morph.codomain,
            "continuous_generators": list(morph.continuous_generators),
            "discrete_events": list(morph.discrete_events),
            "singular_events": list(morph.singular_events),
            "invariants": list(morph.invariants),
            "residual": morph.residual,
            "uncertainty": morph.uncertainty,
        },
        units={"residual": "1"},
        uncertainty={"model": morph.uncertainty},
    )


def result_event_to_evidence_record(
    result: DiscoveryEvent,
    claim: ClaimAtom,
) -> EvidenceRecord:
    if result.event_type != "ResultPacket":
        raise ValueError("result must be a ResultPacket")
    success = bool(result.payload.get("success", False))
    return EvidenceRecord(
        evidence_id=stable_id("evd", result.event_id, claim.claim_id),
        kind="result" if success else "counterexample",
        title=str(result.payload.get("title", "Discovery-kernel result")),
        source_path=(result.provenance[0] if result.provenance else None),
        locator=result.event_id,
        content_hash=result.event_hash,
        status="reproduced" if result.status.startswith("reproduced") else "candidate",
        supports_claim_ids=(claim.claim_id,) if success else (),
        contradicts_claim_ids=() if success else (claim.claim_id,),
        metadata={
            "discovery_subject_id": result.subject_id,
            "units": dict(result.units),
            "uncertainty": dict(result.uncertainty),
            "protocol": result.payload.get("protocol"),
            "baseline": result.payload.get("baseline"),
        },
    )
