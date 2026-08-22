"""Ω-AXIOME-TRISTAN R0.1 — proof-carrying claim and axiom primitives.

This module deliberately separates generated structure from verified knowledge.
No heuristic score or generated candidate grants scientific truth, publication
permission, or external action authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from math import isfinite
from typing import Any


class EpistemicKind(str, Enum):
    AXIOM = "AXIOM"
    FORMAL_AXIOM = "FORMAL_AXIOM"
    POSTULATE = "POSTULATE"
    HYPOTHESIS = "HYPOTHESIS"
    CONJECTURE = "CONJECTURE"
    ENGINEERING_PRINCIPLE = "ENGINEERING_PRINCIPLE"
    INVARIANT = "INVARIANT"
    OPERATIONAL_RULE = "OPERATIONAL_RULE"


class EpistemicStatus(str, Enum):
    IDEA = "IDEA"
    CONJECTURE = "CONJECTURE"
    FORMALIZED = "FORMALIZED"
    TESTABLE = "TESTABLE"
    TESTED = "TESTED"
    CORROBORATED = "CORROBORATED"
    REPLICATED = "REPLICATED"
    FORMALLY_VERIFIED = "FORMALLY_VERIFIED"
    REFUTED = "REFUTED"
    BOUNDED = "BOUNDED"


class EvidenceType(str, Enum):
    OBSERVATION = "OBSERVATION"
    EXPERIMENT = "EXPERIMENT"
    REPLICATION = "REPLICATION"
    FORMAL_PROOF = "FORMAL_PROOF"
    SIMULATION = "SIMULATION"
    BENCHMARK = "BENCHMARK"
    DERIVATION = "DERIVATION"


_STATUS_LEVEL = {
    EpistemicStatus.IDEA: 0,
    EpistemicStatus.CONJECTURE: 1,
    EpistemicStatus.FORMALIZED: 2,
    EpistemicStatus.TESTABLE: 3,
    EpistemicStatus.TESTED: 4,
    EpistemicStatus.BOUNDED: 4,
    EpistemicStatus.CORROBORATED: 5,
    EpistemicStatus.REPLICATED: 6,
    EpistemicStatus.FORMALLY_VERIFIED: 6,
    EpistemicStatus.REFUTED: 4,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    evidence_type: EvidenceType
    source: str
    supports_scope: tuple[str, ...] = ()
    independent: bool = False
    strength: float = 0.5
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must be non-empty")
        if not self.source.strip():
            raise ValueError("source must be non-empty")
        if not isfinite(float(self.strength)) or not 0.0 <= float(self.strength) <= 1.0:
            raise ValueError("strength must be finite and in [0, 1]")


@dataclass(frozen=True)
class Prediction:
    prediction_id: str
    variable: str
    expected: str
    condition: str = "default"
    falsifier: str = ""

    def __post_init__(self) -> None:
        for name in ("prediction_id", "variable", "expected"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True)
class ClaimPassport:
    claim_id: str
    statement: str
    kind: EpistemicKind
    domain: str
    definitions: tuple[str, ...]
    scope: tuple[str, ...]
    assumptions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    evidence: tuple[EvidenceItem, ...] = ()
    counterevidence: tuple[EvidenceItem, ...] = ()
    uncertainty: dict[str, float] = field(default_factory=dict)
    falsifiers: tuple[str, ...] = ()
    proof_obligations: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    version: str = "0.1.0"
    status: EpistemicStatus = EpistemicStatus.IDEA
    generator_id: str = ""
    judge_id: str = ""
    revenue_score: float | None = None

    def __post_init__(self) -> None:
        for name in ("claim_id", "statement", "domain", "version"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be non-empty")
        for key, value in self.uncertainty.items():
            if not key.strip() or not isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError("uncertainty components must be named values in [0, 1]")
        if self.revenue_score is not None and not isfinite(float(self.revenue_score)):
            raise ValueError("revenue_score must be finite when supplied")

    def digest(self) -> str:
        return stable_digest(_primitive(asdict(self)))


@dataclass(frozen=True)
class AxiomGenome:
    passport: ClaimPassport
    consequences: tuple[str, ...] = ()
    predictions: tuple[Prediction, ...] = ()
    tests: tuple[str, ...] = ()
    boundary_conditions: tuple[str, ...] = ()
    parent_ids: tuple[str, ...] = ()
    mutation_label: str = "SEED"
    generated_candidate: bool = False

    def digest(self) -> str:
        return stable_digest(_primitive(asdict(self)))


@dataclass(frozen=True)
class GateResult:
    gate: str
    passed: bool
    reason: str


@dataclass(frozen=True)
class OAKReport:
    claim_id: str
    passed: bool
    promotion_eligible: bool
    results: tuple[GateResult, ...]
    report_digest: str


@dataclass(frozen=True)
class NegativeMemoryEntry:
    signature: str
    detection_rule: str
    countermeasure: str
    transfer_rule: str
    source_claim_id: str


def _primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _primitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitive(v) for v in value]
    return value


def _scope_coverage(passport: ClaimPassport) -> set[str]:
    coverage: set[str] = set()
    for item in passport.evidence:
        coverage.update(item.supports_scope)
    return coverage


def _evidence_types(passport: ClaimPassport) -> set[EvidenceType]:
    return {item.evidence_type for item in passport.evidence}


def oak_audit(passport: ClaimPassport) -> OAKReport:
    results: list[GateResult] = []

    def gate(name: str, passed: bool, reason: str) -> None:
        results.append(GateResult(name, bool(passed), reason))

    gate("EXPLICIT_DEFINITIONS", bool(passport.definitions), "at least one operational definition is required")
    gate("EXPLICIT_SCOPE", bool(passport.scope), "claim scope must be explicit")
    gate("PROVENANCE", bool(passport.provenance), "at least one provenance pointer is required")
    gate("FALSIFIER_OR_PROOF_OBLIGATION", bool(passport.falsifiers or passport.proof_obligations), "empirical claims need falsifiers; formal claims need proof obligations")
    separated = not passport.generator_id or not passport.judge_id or passport.generator_id != passport.judge_id
    gate("GENERATOR_NE_JUDGE", separated, "generator and judge must be separated when both are declared")

    evidence_types = _evidence_types(passport)
    only_simulation = bool(passport.evidence) and evidence_types <= {EvidenceType.SIMULATION, EvidenceType.DERIVATION}
    if passport.status in {EpistemicStatus.CORROBORATED, EpistemicStatus.REPLICATED}:
        gate("SIMULATION_NE_REALITY", not only_simulation, "simulation/derivation alone cannot justify corroborated or replicated status")
    else:
        gate("SIMULATION_NE_REALITY", True, "no prohibited empirical promotion requested")

    if passport.status == EpistemicStatus.REPLICATED:
        rep_ok = any(e.evidence_type == EvidenceType.REPLICATION and e.independent for e in passport.evidence)
        gate("REPLICATION_REQUIRES_INDEPENDENCE", rep_ok, "replicated status requires independent replication evidence")
    else:
        gate("REPLICATION_REQUIRES_INDEPENDENCE", True, "replicated status not requested")

    if passport.status == EpistemicStatus.FORMALLY_VERIFIED:
        formal_ok = passport.kind in {EpistemicKind.FORMAL_AXIOM, EpistemicKind.INVARIANT, EpistemicKind.CONJECTURE} and EvidenceType.FORMAL_PROOF in evidence_types
        gate("FORMAL_STATUS_REQUIRES_FORMAL_EVIDENCE", formal_ok, "formal verification needs formal-proof evidence and a compatible claim type")
    else:
        gate("FORMAL_STATUS_REQUIRES_FORMAL_EVIDENCE", True, "formal verification status not requested")

    if _STATUS_LEVEL[passport.status] >= _STATUS_LEVEL[EpistemicStatus.TESTED] and passport.scope:
        coverage = _scope_coverage(passport)
        missing = set(passport.scope) - coverage
        gate("CLAIM_SCOPE_LE_EVIDENCE_SCOPE", not missing, f"uncovered scope dimensions: {sorted(missing)}" if missing else "declared scope is covered by supporting evidence")
    else:
        gate("CLAIM_SCOPE_LE_EVIDENCE_SCOPE", True, "evidence-scope coverage not required before TESTED status")

    no_counterevidence_ignored = passport.status == EpistemicStatus.REFUTED or not passport.counterevidence or _STATUS_LEVEL[passport.status] <= _STATUS_LEVEL[EpistemicStatus.TESTED]
    gate("COUNTEREVIDENCE_VISIBLE", no_counterevidence_ignored, "strong promotions must not ignore declared counterevidence")
    gate("REVENUE_NE_TRUTH", True, "revenue metadata is non-epistemic and cannot promote status")

    passed = all(r.passed for r in results)
    promotion_eligible = passed and passport.status not in {EpistemicStatus.IDEA, EpistemicStatus.REFUTED}
    digest_payload = {
        "claim_id": passport.claim_id,
        "passed": passed,
        "promotion_eligible": promotion_eligible,
        "results": [_primitive(asdict(r)) for r in results],
    }
    return OAKReport(passport.claim_id, passed, promotion_eligible, tuple(results), stable_digest(digest_payload))


def compile_failure_to_mminus(passport: ClaimPassport, report: OAKReport) -> tuple[NegativeMemoryEntry, ...]:
    entries: list[NegativeMemoryEntry] = []
    for result in report.results:
        if result.passed:
            continue
        entries.append(NegativeMemoryEntry(
            signature=f"{result.gate}:{passport.kind.value}:{passport.status.value}",
            detection_rule=f"reject when gate {result.gate} fails",
            countermeasure=result.reason,
            transfer_rule=f"apply {result.gate} to future claims with status >= {passport.status.value}",
            source_claim_id=passport.claim_id,
        ))
    return tuple(entries)


def passport_to_dict(passport: ClaimPassport) -> dict[str, Any]:
    return _primitive(asdict(passport))


def genome_to_dict(genome: AxiomGenome) -> dict[str, Any]:
    return _primitive(asdict(genome))


def oak_to_dict(report: OAKReport) -> dict[str, Any]:
    return _primitive(asdict(report))
