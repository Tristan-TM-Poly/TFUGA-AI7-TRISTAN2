"""Core typed objects for Ω-REVOLUTION-DIVERSIFICATION-T∞.

The module distinguishes hypotheses, evidence, negative memory, implementation
artifacts, experiments, value hypotheses, and OAK status.  It deliberately does
not treat internal coherence, hashes, or generated volume as scientific truth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import math
from typing import Any, Iterable, Mapping, Sequence


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_id(prefix: str, payload: Any) -> str:
    digest = sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:24]
    return f"urn:omega:{prefix}:{digest}"


class OakStatus(str, Enum):
    IDEA = "IDEA"
    FORMALIZED = "FORMALIZED"
    IMPLEMENTED = "IMPLEMENTED"
    SIMULATED = "SIMULATED"
    DEMONSTRATED = "DEMONSTRATED"
    REPLICATED = "REPLICATED"
    REFORMULATED = "REFORMULATED"
    REFUTED = "REFUTED"
    CANONICAL = "CANONICAL"
    ARCHIVED = "ARCHIVED"


class EvidenceKind(str, Enum):
    DEFINITION = "definition"
    EQUATION = "equation"
    DERIVATION = "derivation"
    CODE = "code"
    TEST = "test"
    DATASET = "dataset"
    BASELINE = "baseline"
    SIMULATION = "simulation"
    MEASUREMENT = "measurement"
    RESULT = "result"
    REPLICATION = "replication"
    COUNTEREXAMPLE = "counterexample"
    USER_EVIDENCE = "user_evidence"
    MARKET_EVIDENCE = "market_evidence"
    SAFETY_EVIDENCE = "safety_evidence"
    PROVENANCE = "provenance"
    NEGATIVE_MEMORY = "negative_memory"


class ActionSensitivity(str, Enum):
    REVERSIBLE = "reversible"
    REVIEW_REQUIRED = "review_required"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    PROHIBITED_AUTONOMOUSLY = "prohibited_autonomously"


class ConductorDecision(str, Enum):
    EXPAND = "EXPAND"
    RESHARD = "RESHARD"
    HOLD = "HOLD"
    REDESIGN = "REDESIGN"
    STOP = "STOP"


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str
    uncertainty: float | None = None
    distribution: str = "unspecified"
    calibration_ref: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not math.isfinite(self.value):
            errors.append("quantity.value must be finite")
        if not self.unit.strip():
            errors.append("quantity.unit is required")
        if self.uncertainty is not None:
            if not math.isfinite(self.uncertainty) or self.uncertainty < 0:
                errors.append("quantity.uncertainty must be finite and non-negative")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Evidence:
    kind: EvidenceKind
    title: str
    source: str
    supports: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()
    independence: str = "internal"
    reproducibility: str = "unknown"
    uncertainty: float | None = None
    limitations: tuple[str, ...] = ()
    content_hash: str | None = None
    evidence_id: str = ""
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if not self.evidence_id:
            payload = {
                "kind": self.kind.value,
                "title": self.title,
                "source": self.source,
                "supports": self.supports,
                "contradicts": self.contradicts,
            }
            object.__setattr__(self, "evidence_id", stable_id("evidence", payload))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.title.strip():
            errors.append(f"{self.evidence_id}: title is required")
        if not self.source.strip():
            errors.append(f"{self.evidence_id}: source is required")
        if self.uncertainty is not None and not 0 <= self.uncertainty <= 1:
            errors.append(f"{self.evidence_id}: uncertainty must be in [0,1]")
        if set(self.supports) & set(self.contradicts):
            errors.append(f"{self.evidence_id}: cannot support and contradict the same claim")
        return errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["supports"] = list(self.supports)
        data["contradicts"] = list(self.contradicts)
        data["limitations"] = list(self.limitations)
        return data


@dataclass(frozen=True)
class Hypothesis:
    statement: str
    domain: str
    assumptions: tuple[str, ...]
    falsification_conditions: tuple[str, ...]
    value_potential: float
    information_gain: float
    falsifiability: float
    reusability: float
    cost: float
    time_cost: float
    operational_uncertainty: float
    dependency_load: float
    prior_probability: float = 0.5
    hypothesis_id: str = ""
    status: OakStatus = OakStatus.IDEA

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            payload = {
                "statement": self.statement,
                "domain": self.domain,
                "assumptions": self.assumptions,
            }
            object.__setattr__(self, "hypothesis_id", stable_id("hypothesis", payload))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.statement.strip():
            errors.append(f"{self.hypothesis_id}: statement is required")
        if not self.domain.strip():
            errors.append(f"{self.hypothesis_id}: domain is required")
        if not self.assumptions:
            errors.append(f"{self.hypothesis_id}: at least one assumption is required")
        if not self.falsification_conditions:
            errors.append(f"{self.hypothesis_id}: falsification conditions are required")
        bounded = {
            "value_potential": self.value_potential,
            "information_gain": self.information_gain,
            "falsifiability": self.falsifiability,
            "reusability": self.reusability,
            "operational_uncertainty": self.operational_uncertainty,
            "prior_probability": self.prior_probability,
        }
        for name, value in bounded.items():
            if not 0 <= value <= 1:
                errors.append(f"{self.hypothesis_id}: {name} must be in [0,1]")
        for name, value in {
            "cost": self.cost,
            "time_cost": self.time_cost,
            "dependency_load": self.dependency_load,
        }.items():
            if not math.isfinite(value) or value < 0:
                errors.append(f"{self.hypothesis_id}: {name} must be finite and non-negative")
        return errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["assumptions"] = list(self.assumptions)
        data["falsification_conditions"] = list(self.falsification_conditions)
        return data


@dataclass(frozen=True)
class MMinusRule:
    trigger: str
    root_cause: str
    forbidden_inference: str
    safe_replacement: str
    prevention_test: str
    domain: str
    severity: int = 2
    source_event_ids: tuple[str, ...] = ()
    rule_id: str = ""
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if not self.rule_id:
            payload = {
                "trigger": self.trigger,
                "root_cause": self.root_cause,
                "domain": self.domain,
                "prevention_test": self.prevention_test,
            }
            object.__setattr__(self, "rule_id", stable_id("mminus", payload))

    def validate(self) -> list[str]:
        errors: list[str] = []
        required = {
            "trigger": self.trigger,
            "root_cause": self.root_cause,
            "forbidden_inference": self.forbidden_inference,
            "safe_replacement": self.safe_replacement,
            "prevention_test": self.prevention_test,
            "domain": self.domain,
        }
        for name, value in required.items():
            if not value.strip():
                errors.append(f"{self.rule_id}: {name} is required")
        if not 1 <= self.severity <= 5:
            errors.append(f"{self.rule_id}: severity must be in [1,5]")
        return errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_event_ids"] = list(self.source_event_ids)
        return data


@dataclass(frozen=True)
class ActionProposal:
    title: str
    rationale: str
    sensitivity: ActionSensitivity
    reversible: bool
    expected_value: float
    required_approvals: tuple[str, ...] = ()
    action_id: str = ""

    def __post_init__(self) -> None:
        if not self.action_id:
            payload = {
                "title": self.title,
                "rationale": self.rationale,
                "sensitivity": self.sensitivity.value,
            }
            object.__setattr__(self, "action_id", stable_id("action", payload))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.title.strip():
            errors.append(f"{self.action_id}: title is required")
        if not self.rationale.strip():
            errors.append(f"{self.action_id}: rationale is required")
        if not 0 <= self.expected_value <= 1:
            errors.append(f"{self.action_id}: expected_value must be in [0,1]")
        if self.sensitivity in {
            ActionSensitivity.HUMAN_APPROVAL_REQUIRED,
            ActionSensitivity.PROHIBITED_AUTONOMOUSLY,
        } and not self.required_approvals:
            errors.append(f"{self.action_id}: sensitive action requires explicit approvals")
        if self.sensitivity is ActionSensitivity.REVERSIBLE and not self.reversible:
            errors.append(f"{self.action_id}: reversible sensitivity conflicts with irreversible flag")
        return errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["sensitivity"] = self.sensitivity.value
        data["required_approvals"] = list(self.required_approvals)
        return data


@dataclass
class DiscoveryCell:
    title: str
    domain: str
    problem: str
    user: str
    observable_pain: str
    current_baseline: str
    hypotheses: list[Hypothesis]
    evidence: list[Evidence] = field(default_factory=list)
    m_minus: list[MMinusRule] = field(default_factory=list)
    quantities: dict[str, Quantity] = field(default_factory=dict)
    code_refs: list[str] = field(default_factory=list)
    test_refs: list[str] = field(default_factory=list)
    next_actions: list[ActionProposal] = field(default_factory=list)
    scientific_value: float = 0.0
    engineering_value: float = 0.0
    product_value: float = 0.0
    ip_status: str = "unclassified"
    status: OakStatus = OakStatus.IDEA
    parent_ids: list[str] = field(default_factory=list)
    supersedes: list[str] = field(default_factory=list)
    cell_id: str = ""
    version: str = "0.1.0"
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if not self.cell_id:
            self.cell_id = stable_id(
                "discovery-cell",
                {"title": self.title, "domain": self.domain, "problem": self.problem},
            )

    @property
    def claim_ids(self) -> set[str]:
        return {h.hypothesis_id for h in self.hypotheses}

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in {
            "title": self.title,
            "domain": self.domain,
            "problem": self.problem,
            "user": self.user,
            "observable_pain": self.observable_pain,
            "current_baseline": self.current_baseline,
        }.items():
            if not value.strip():
                errors.append(f"{self.cell_id}: {name} is required")
        if not self.hypotheses:
            errors.append(f"{self.cell_id}: at least one hypothesis is required")
        ids = [h.hypothesis_id for h in self.hypotheses]
        if len(ids) != len(set(ids)):
            errors.append(f"{self.cell_id}: duplicate hypothesis IDs")
        evidence_ids = [e.evidence_id for e in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            errors.append(f"{self.cell_id}: duplicate evidence IDs")
        for hypothesis in self.hypotheses:
            errors.extend(hypothesis.validate())
        for evidence in self.evidence:
            errors.extend(evidence.validate())
            unknown = (set(evidence.supports) | set(evidence.contradicts)) - self.claim_ids
            if unknown:
                errors.append(
                    f"{self.cell_id}: evidence {evidence.evidence_id} references unknown claims {sorted(unknown)}"
                )
        for rule in self.m_minus:
            errors.extend(rule.validate())
        for quantity in self.quantities.values():
            errors.extend(quantity.validate())
        for action in self.next_actions:
            errors.extend(action.validate())
        for name, value in {
            "scientific_value": self.scientific_value,
            "engineering_value": self.engineering_value,
            "product_value": self.product_value,
        }.items():
            if not 0 <= value <= 1:
                errors.append(f"{self.cell_id}: {name} must be in [0,1]")
        if self.status in {OakStatus.DEMONSTRATED, OakStatus.REPLICATED, OakStatus.CANONICAL}:
            result_kinds = {
                EvidenceKind.RESULT,
                EvidenceKind.MEASUREMENT,
                EvidenceKind.REPLICATION,
            }
            if not any(e.kind in result_kinds for e in self.evidence):
                errors.append(f"{self.cell_id}: promoted status requires result evidence")
            if not any(e.kind is EvidenceKind.BASELINE for e in self.evidence):
                errors.append(f"{self.cell_id}: promoted status requires a baseline")
        return errors

    def evidence_coverage(self) -> float:
        if not self.hypotheses:
            return 0.0
        covered = set()
        for evidence in self.evidence:
            covered.update(evidence.supports)
            covered.update(evidence.contradicts)
        return len(covered & self.claim_ids) / len(self.claim_ids)

    def falsification_coverage(self) -> float:
        if not self.hypotheses:
            return 0.0
        return sum(bool(h.falsification_conditions) for h in self.hypotheses) / len(self.hypotheses)

    def negative_memory_coverage(self) -> float:
        if not self.hypotheses:
            return 0.0
        linked = set()
        for rule in self.m_minus:
            linked.update(rule.source_event_ids)
        domain_rules = sum(not r.source_event_ids for r in self.m_minus)
        return min(1.0, (len(linked & self.claim_ids) + domain_rules) / len(self.hypotheses))

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "version": self.version,
            "title": self.title,
            "domain": self.domain,
            "problem": self.problem,
            "user": self.user,
            "observable_pain": self.observable_pain,
            "current_baseline": self.current_baseline,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "evidence": [e.to_dict() for e in self.evidence],
            "m_minus": [m.to_dict() for m in self.m_minus],
            "quantities": {key: value.to_dict() for key, value in self.quantities.items()},
            "code_refs": list(self.code_refs),
            "test_refs": list(self.test_refs),
            "next_actions": [a.to_dict() for a in self.next_actions],
            "scientific_value": self.scientific_value,
            "engineering_value": self.engineering_value,
            "product_value": self.product_value,
            "ip_status": self.ip_status,
            "status": self.status.value,
            "parent_ids": list(self.parent_ids),
            "supersedes": list(self.supersedes),
            "created_at": self.created_at,
            "metrics": {
                "evidence_coverage": self.evidence_coverage(),
                "falsification_coverage": self.falsification_coverage(),
                "negative_memory_coverage": self.negative_memory_coverage(),
            },
        }


def validate_cells(cells: Iterable[DiscoveryCell]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for cell in cells:
        if cell.cell_id in seen:
            errors.append(f"duplicate cell ID: {cell.cell_id}")
        seen.add(cell.cell_id)
        errors.extend(cell.validate())
    return errors
