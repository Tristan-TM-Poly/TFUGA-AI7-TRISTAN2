"""Ω-DISCOVERY-OPERATING-SYSTEM-T∞² R0.4 contracts.

This module turns the R0.1-R0.3 meta-science primitives into a small,
deterministic contract layer for typed claims, semantic theory diffs,
dependency-aware scientific rebuilds, proof-carrying claims and bounded
discovery-value accounting.

All operations are local to explicitly supplied declarations. A PASS here is a
software/contract result, not a proof that a scientific statement is true.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, Mapping, Sequence


ClaimKind = Literal[
    "observation",
    "correlation",
    "causal",
    "simulation",
    "experimental",
    "theorem",
    "conjecture",
    "hypothesis",
    "supported",
]
EvidenceKind = Literal[
    "observation",
    "simulation",
    "experiment",
    "causal_design",
    "formal_proof",
    "replication",
    "provenance",
]
OAKStatus = Literal["PASS", "CONDITIONAL", "BLOCK"]


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    kind: EvidenceKind
    provenance: str
    reproducible: bool = True
    independent_group: str = "default"


@dataclass(frozen=True, slots=True)
class ScientificClaim:
    claim_id: str
    statement: str
    kind: ClaimKind
    domain: str
    provenance: str
    uncertainty: float
    evidence_ids: tuple[str, ...] = ()
    counterevidence_ids: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EpistemicTypeReport:
    claim_id: str
    source_kind: ClaimKind
    target_kind: ClaimKind
    allowed: bool
    blockers: tuple[str, ...]
    resolved_evidence: tuple[str, ...]
    oak_boundary: str = (
        "typed promotion over declared evidence only; not a truth or causality certificate"
    )


def check_claim_type(
    claim: ScientificClaim,
    evidence: Mapping[str, EvidenceRecord],
    *,
    target_kind: ClaimKind | None = None,
) -> EpistemicTypeReport:
    """Fail closed on invalid claim contracts or unsupported promotions."""

    target = claim.kind if target_kind is None else target_kind
    blockers: list[str] = []
    if not claim.claim_id.strip():
        blockers.append("missing_claim_id")
    if not claim.statement.strip():
        blockers.append("missing_statement")
    if not claim.domain.strip():
        blockers.append("missing_domain")
    if not claim.provenance.strip():
        blockers.append("missing_provenance")
    if not 0.0 <= claim.uncertainty <= 1.0:
        blockers.append("uncertainty_out_of_range")

    resolved: list[EvidenceRecord] = []
    for evidence_id in claim.evidence_ids:
        item = evidence.get(evidence_id)
        if item is None:
            blockers.append(f"missing_evidence:{evidence_id}")
            continue
        if not item.provenance.strip():
            blockers.append(f"evidence_missing_provenance:{evidence_id}")
        resolved.append(item)

    kinds = {item.kind for item in resolved}
    reproducible = any(item.reproducible for item in resolved)

    if target == "causal" and "causal_design" not in kinds:
        blockers.append("causal_claim_requires_causal_design")
    if target == "theorem" and "formal_proof" not in kinds:
        blockers.append("theorem_requires_formal_proof")
    if target == "experimental" and "experiment" not in kinds:
        blockers.append("experimental_claim_requires_experiment")
    if target == "supported":
        if not resolved:
            blockers.append("supported_claim_requires_evidence")
        if resolved and not reproducible:
            blockers.append("supported_claim_requires_reproducible_evidence")

    return EpistemicTypeReport(
        claim_id=claim.claim_id,
        source_kind=claim.kind,
        target_kind=target,
        allowed=not blockers,
        blockers=tuple(sorted(set(blockers))),
        resolved_evidence=tuple(item.evidence_id for item in resolved),
    )


@dataclass(frozen=True, slots=True)
class TheorySnapshot:
    theory_id: str
    version: str
    assumptions: tuple[str, ...]
    laws: tuple[str, ...]
    domain: str
    evidence_ids: tuple[str, ...]
    representations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TheoryDiffReport:
    theory_id: str
    old_version: str
    new_version: str
    assumptions_added: tuple[str, ...]
    assumptions_removed: tuple[str, ...]
    laws_added: tuple[str, ...]
    laws_removed: tuple[str, ...]
    evidence_added: tuple[str, ...]
    evidence_removed: tuple[str, ...]
    representations_added: tuple[str, ...]
    representations_removed: tuple[str, ...]
    domain_changed: bool
    change_classes: tuple[str, ...]


def _added(old: Sequence[str], new: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(new) - set(old)))


def _removed(old: Sequence[str], new: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(old) - set(new)))


def theory_diff(old: TheorySnapshot, new: TheorySnapshot) -> TheoryDiffReport:
    """Semantic diff that separates assumption/model/evidence/representation change."""

    if old.theory_id != new.theory_id:
        raise ValueError("theory_id mismatch")
    assumptions_added = _added(old.assumptions, new.assumptions)
    assumptions_removed = _removed(old.assumptions, new.assumptions)
    laws_added = _added(old.laws, new.laws)
    laws_removed = _removed(old.laws, new.laws)
    evidence_added = _added(old.evidence_ids, new.evidence_ids)
    evidence_removed = _removed(old.evidence_ids, new.evidence_ids)
    representations_added = _added(old.representations, new.representations)
    representations_removed = _removed(old.representations, new.representations)
    domain_changed = old.domain != new.domain

    classes: list[str] = []
    if assumptions_added or assumptions_removed:
        classes.append("assumption_change")
    if laws_added or laws_removed:
        classes.append("model_change")
    if evidence_added or evidence_removed:
        classes.append("evidence_change")
    if representations_added or representations_removed:
        classes.append("representation_change")
    if domain_changed:
        classes.append("domain_change")
    if not classes:
        classes.append("no_semantic_change")

    return TheoryDiffReport(
        old.theory_id,
        old.version,
        new.version,
        assumptions_added,
        assumptions_removed,
        laws_added,
        laws_removed,
        evidence_added,
        evidence_removed,
        representations_added,
        representations_removed,
        domain_changed,
        tuple(classes),
    )


@dataclass(frozen=True, slots=True)
class BuildNode:
    node_id: str
    kind: str
    dependencies: tuple[str, ...] = ()
    fingerprint: str = ""


@dataclass(frozen=True, slots=True)
class BuildGraphAudit:
    valid: bool
    blockers: tuple[str, ...]
    topological_order: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BuildInvalidationReport:
    changed: tuple[str, ...]
    invalidated: tuple[str, ...]
    unaffected: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScientificBuildGraph:
    nodes: tuple[BuildNode, ...]

    def audit(self) -> BuildGraphAudit:
        by_id: dict[str, BuildNode] = {}
        blockers: list[str] = []
        for node in self.nodes:
            if not node.node_id.strip():
                blockers.append("missing_node_id")
                continue
            if node.node_id in by_id:
                blockers.append(f"duplicate_node:{node.node_id}")
            by_id[node.node_id] = node
        for node in self.nodes:
            for dependency in node.dependencies:
                if dependency not in by_id:
                    blockers.append(f"missing_dependency:{node.node_id}:{dependency}")

        indegree = {node_id: 0 for node_id in by_id}
        outgoing = {node_id: [] for node_id in by_id}
        if not blockers:
            for node in self.nodes:
                for dependency in node.dependencies:
                    indegree[node.node_id] += 1
                    outgoing[dependency].append(node.node_id)

        queue = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        order: list[str] = []
        while queue:
            current = queue.pop(0)
            order.append(current)
            for child in sorted(outgoing[current]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
                    queue.sort()

        if len(order) != len(by_id) and not blockers:
            blockers.append("dependency_cycle")

        return BuildGraphAudit(not blockers, tuple(sorted(set(blockers))), tuple(order))

    def invalidated_by(self, changed: Sequence[str]) -> BuildInvalidationReport:
        audit = self.audit()
        if not audit.valid:
            raise ValueError(f"invalid build graph: {audit.blockers}")
        by_id = {node.node_id: node for node in self.nodes}
        changed_set = set(changed)
        unknown = sorted(changed_set - set(by_id))
        if unknown:
            raise ValueError(f"unknown changed nodes: {unknown}")

        reverse = {node_id: set() for node_id in by_id}
        for node in self.nodes:
            for dependency in node.dependencies:
                reverse[dependency].add(node.node_id)

        invalidated = set(changed_set)
        frontier = list(sorted(changed_set))
        while frontier:
            current = frontier.pop(0)
            for child in sorted(reverse[current]):
                if child not in invalidated:
                    invalidated.add(child)
                    frontier.append(child)

        unaffected = set(by_id) - invalidated
        return BuildInvalidationReport(
            tuple(sorted(changed_set)),
            tuple(sorted(invalidated)),
            tuple(sorted(unaffected)),
        )


@dataclass(frozen=True, slots=True)
class ClaimCertificate:
    claim: ScientificClaim
    target_kind: ClaimKind
    oak_status: OAKStatus
    tests_passed: tuple[str, ...]
    counterevidence_reviewed: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ClaimCertificateReport:
    certified: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    type_report: EpistemicTypeReport
    oak_boundary: str = (
        "certificate validates declared evidence/tests/OAK gates; it does not prove external truth"
    )


def validate_claim_certificate(
    certificate: ClaimCertificate,
    evidence: Mapping[str, EvidenceRecord],
) -> ClaimCertificateReport:
    type_report = check_claim_type(
        certificate.claim,
        evidence,
        target_kind=certificate.target_kind,
    )
    blockers = list(type_report.blockers)
    warnings: list[str] = []
    if certificate.oak_status != "PASS":
        blockers.append(f"oak_status:{certificate.oak_status}")
    if not certificate.tests_passed:
        blockers.append("missing_tests")
    declared_counterevidence = set(certificate.claim.counterevidence_ids)
    reviewed_counterevidence = set(certificate.counterevidence_reviewed)
    missing_review = sorted(declared_counterevidence - reviewed_counterevidence)
    warnings.extend(f"counterevidence_not_reviewed:{item}" for item in missing_review)
    return ClaimCertificateReport(
        certified=not blockers,
        blockers=tuple(sorted(set(blockers))),
        warnings=tuple(warnings),
        type_report=type_report,
    )


@dataclass(frozen=True, slots=True)
class VerifiedDiscoveryMetrics:
    uncertainty_reduction: float
    reproducibility: float
    generalization: float
    artifact_maturity: float
    novelty_evidence: float
    oak_pass: bool


@dataclass(frozen=True, slots=True)
class VerifiedDiscoveryUnit:
    score: float
    components: tuple[tuple[str, float], ...]
    oak_pass: bool
    oak_boundary: str = (
        "bounded portfolio metric for internal comparison; not a universal unit of scientific value"
    )


def verified_discovery_unit(metrics: VerifiedDiscoveryMetrics) -> VerifiedDiscoveryUnit:
    components = {
        "uncertainty_reduction": metrics.uncertainty_reduction,
        "reproducibility": metrics.reproducibility,
        "generalization": metrics.generalization,
        "artifact_maturity": metrics.artifact_maturity,
        "novelty_evidence": metrics.novelty_evidence,
    }
    for name, value in components.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0,1]")
    weights = {
        "uncertainty_reduction": 0.30,
        "reproducibility": 0.25,
        "generalization": 0.20,
        "artifact_maturity": 0.15,
        "novelty_evidence": 0.10,
    }
    raw = sum(weights[name] * value for name, value in components.items())
    score = raw if metrics.oak_pass else 0.0
    return VerifiedDiscoveryUnit(
        score=score,
        components=tuple((name, components[name]) for name in sorted(components)),
        oak_pass=metrics.oak_pass,
    )


@dataclass(frozen=True, slots=True)
class DiscoveryROIInput:
    expected_value: float
    validation_probability: float
    compute_cost: float = 0.0
    experiment_cost: float = 0.0
    human_cost: float = 0.0
    risk_cost: float = 0.0


@dataclass(frozen=True, slots=True)
class DiscoveryROIReport:
    expected_validated_value: float
    total_cost: float
    roi: float
    oak_boundary: str = (
        "decision surrogate from supplied value/probability/cost assumptions; not a valuation guarantee"
    )


def discovery_roi(item: DiscoveryROIInput) -> DiscoveryROIReport:
    values = (
        item.expected_value,
        item.compute_cost,
        item.experiment_cost,
        item.human_cost,
        item.risk_cost,
    )
    if any(value < 0.0 for value in values):
        raise ValueError("value and costs must be non-negative")
    if not 0.0 <= item.validation_probability <= 1.0:
        raise ValueError("validation_probability must be in [0,1]")
    total_cost = item.compute_cost + item.experiment_cost + item.human_cost + item.risk_cost
    if total_cost <= 0.0:
        raise ValueError("total cost must be positive")
    expected_validated_value = item.expected_value * item.validation_probability
    return DiscoveryROIReport(
        expected_validated_value,
        total_cost,
        expected_validated_value / total_cost,
    )


@dataclass(frozen=True, slots=True)
class DiscoveryOSReport:
    rejected_promotion: EpistemicTypeReport
    accepted_promotion: EpistemicTypeReport
    theory_diff: TheoryDiffReport
    build_audit: BuildGraphAudit
    invalidation: BuildInvalidationReport
    claim_certificate: ClaimCertificateReport
    vdu: VerifiedDiscoveryUnit
    roi: DiscoveryROIReport


def run_discovery_os_demo() -> DiscoveryOSReport:
    """Deterministic cross-primitive R0.4 fixture."""

    evidence = {
        "E_obs": EvidenceRecord("E_obs", "observation", "fixture:observatory"),
        "E_causal": EvidenceRecord("E_causal", "causal_design", "fixture:randomized-design"),
        "E_rep": EvidenceRecord("E_rep", "replication", "fixture:independent-replication"),
    }
    correlation = ScientificClaim(
        claim_id="C_relation",
        statement="x and y co-vary in the declared fixture",
        kind="correlation",
        domain="fixture-domain",
        provenance="fixture:R0.4",
        uncertainty=0.2,
        evidence_ids=("E_obs",),
        tests=("association-test",),
    )
    rejected = check_claim_type(correlation, evidence, target_kind="causal")
    causal_candidate = ScientificClaim(
        claim_id="C_relation",
        statement="intervention on x changes y in the declared fixture",
        kind="correlation",
        domain="fixture-domain",
        provenance="fixture:R0.4",
        uncertainty=0.1,
        evidence_ids=("E_obs", "E_causal", "E_rep"),
        tests=("association-test", "intervention-test"),
    )
    accepted = check_claim_type(causal_candidate, evidence, target_kind="causal")

    old = TheorySnapshot(
        "T_demo",
        "0.3",
        ("smoothness", "closed-system"),
        ("y=x",),
        "x>=0",
        ("E_obs",),
        ("native",),
    )
    new = TheorySnapshot(
        "T_demo",
        "0.4",
        ("smoothness",),
        ("y=x", "dy/dx=1"),
        "x>=0",
        ("E_obs", "E_rep"),
        ("native", "log-view"),
    )
    diff = theory_diff(old, new)

    graph = ScientificBuildGraph(
        (
            BuildNode("instrument", "instrument"),
            BuildNode("dataset", "dataset", ("instrument",)),
            BuildNode("model", "model", ("dataset",)),
            BuildNode("claim", "claim", ("model",)),
            BuildNode("artifact", "artifact", ("claim",)),
        )
    )
    audit = graph.audit()
    invalidation = graph.invalidated_by(("dataset",))

    certificate = ClaimCertificate(
        claim=causal_candidate,
        target_kind="causal",
        oak_status="PASS",
        tests_passed=("association-test", "intervention-test"),
    )
    certificate_report = validate_claim_certificate(certificate, evidence)

    vdu = verified_discovery_unit(
        VerifiedDiscoveryMetrics(
            uncertainty_reduction=0.8,
            reproducibility=0.9,
            generalization=0.6,
            artifact_maturity=0.7,
            novelty_evidence=0.4,
            oak_pass=True,
        )
    )
    roi = discovery_roi(
        DiscoveryROIInput(
            expected_value=100.0,
            validation_probability=0.4,
            compute_cost=5.0,
            experiment_cost=20.0,
            human_cost=10.0,
            risk_cost=5.0,
        )
    )
    return DiscoveryOSReport(
        rejected,
        accepted,
        diff,
        audit,
        invalidation,
        certificate_report,
        vdu,
        roi,
    )


def report_to_dict(report: DiscoveryOSReport) -> dict[str, object]:
    return asdict(report)
