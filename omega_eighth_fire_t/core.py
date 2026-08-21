from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping
import time

from omega_capability_os_t.core import stable_digest

SCHEMA_VERSION = "0.1.0"
HARD_GATES = (
    "evidence",
    "safety",
    "non_domination",
    "attribution_consent",
    "regeneration",
    "beneficiary_autonomy",
    "rollback_contestability",
)


@dataclass(frozen=True)
class GateResult:
    passed: bool
    evidence: str = ""


@dataclass(frozen=True)
class FireMetrics:
    verified_capability_gain: float
    transfer: float
    autonomy: float
    regeneration: float
    reciprocity: float
    reach: float
    cost: float
    risk: float
    complexity: float
    debt: float
    capture: float
    dependency_half_life_days: float | None = None
    capability_half_life_days: float | None = None
    forkability: float = 0.0
    local_ownership: float = 0.0
    future_optionality: float = 0.0

    def __post_init__(self) -> None:
        unit = (
            "verified_capability_gain", "transfer", "autonomy", "regeneration",
            "reciprocity", "reach", "risk", "capture", "forkability",
            "local_ownership", "future_optionality",
        )
        for name in unit:
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1]")
        for name in ("cost", "complexity", "debt"):
            if float(getattr(self, name)) < 0.0:
                raise ValueError(f"{name} must be >= 0")
        for name in ("dependency_half_life_days", "capability_half_life_days"):
            value = getattr(self, name)
            if value is not None and float(value) < 0.0:
                raise ValueError(f"{name} must be >= 0 when supplied")


@dataclass(frozen=True)
class FireProposal:
    proposal_id: str
    purpose: str
    beneficiaries: tuple[str, ...]
    capability: str
    method: str
    metrics: FireMetrics
    gates: Mapping[str, GateResult]
    provenance: tuple[str, ...] = ()
    falsifiers: tuple[str, ...] = ()
    exit_path: str = ""
    rollback: str = ""
    rights_notes: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.proposal_id.strip():
            raise ValueError("proposal_id must be non-empty")
        if not self.beneficiaries:
            raise ValueError("beneficiaries must be non-empty")


@dataclass(frozen=True)
class EvaluationReceipt:
    proposal_id: str
    decision: str
    gate_pass: bool
    failed_gates: tuple[str, ...]
    operational_score: float | None
    anti_capture_flags: tuple[str, ...]
    n_plus_1_probes: tuple[str, ...]
    fingerprint: str
    generated_at_unix: int
    oak_boundary: str = (
        "ELIGIBLE/REVIEW/HOLD is a bounded engineering decision under supplied evidence. "
        "It is not scientific, ethical, cultural, legal, or social proof."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def all_hard_gates_pass(gates: Mapping[str, GateResult]) -> tuple[bool, tuple[str, ...]]:
    failed = tuple(name for name in HARD_GATES if name not in gates or not gates[name].passed)
    return not failed, failed


def operational_score(metrics: FireMetrics) -> float:
    numerator = (
        metrics.verified_capability_gain
        * metrics.transfer
        * metrics.autonomy
        * metrics.regeneration
        * metrics.reciprocity
        * metrics.reach
    )
    denominator = metrics.cost + metrics.risk + metrics.complexity + metrics.debt + metrics.capture + 1e-9
    return round(numerator / denominator, 9)


def anti_capture_scan(proposal: FireProposal) -> tuple[str, ...]:
    m = proposal.metrics
    flags: list[str] = []
    if m.capture > 0.5:
        flags.append("high_capture_risk")
    if m.transfer > 0.6 and m.autonomy < 0.4:
        flags.append("transfer_without_autonomy")
    if m.forkability < 0.3 and m.local_ownership < 0.3:
        flags.append("low_exit_control")
    if m.dependency_half_life_days is not None and m.dependency_half_life_days > 365:
        flags.append("long_dependency_half_life")
    if not proposal.exit_path.strip():
        flags.append("missing_exit_path")
    if not proposal.rollback.strip():
        flags.append("missing_rollback")
    if not proposal.provenance:
        flags.append("missing_provenance")
    if not proposal.falsifiers:
        flags.append("missing_falsifiers")
    return tuple(flags)


def n_plus_1_probes(proposal: FireProposal) -> tuple[str, ...]:
    probes = [
        "omitted_beneficiary",
        "hidden_persistent_dependency",
        "simpler_comparable_intervention",
        "metric_goodhart_attack",
        "externalized_cost_or_harm",
        "practical_revocation_test",
        "vanishing_system_test",
        "lower_capture_decentralized_alternative",
    ]
    if proposal.metrics.future_optionality < 0.5:
        probes.append("higher_future_optionality_variant")
    if proposal.metrics.regeneration < 0.5:
        probes.append("higher_regeneration_variant")
    return tuple(probes)


def evaluate(proposal: FireProposal) -> EvaluationReceipt:
    gate_pass, failed = all_hard_gates_pass(proposal.gates)
    flags = anti_capture_scan(proposal)
    score = operational_score(proposal.metrics) if gate_pass else None
    decision = "HOLD" if not gate_pass else ("REVIEW" if flags else "ELIGIBLE")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "proposal_id": proposal.proposal_id,
        "decision": decision,
        "failed_gates": failed,
        "score": score,
        "flags": flags,
        "probes": n_plus_1_probes(proposal),
    }
    return EvaluationReceipt(
        proposal_id=proposal.proposal_id,
        decision=decision,
        gate_pass=gate_pass,
        failed_gates=failed,
        operational_score=score,
        anti_capture_flags=flags,
        n_plus_1_probes=n_plus_1_probes(proposal),
        fingerprint=stable_digest(payload),
        generated_at_unix=int(time.time()),
    )
