from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Iterable, Mapping

from .defects import DefectInteractionGraph
from .genome import SolidGenome
from .hypergraph import SolidHyperGraph
from .invariants import build_signature
from .models import EpistemicStatus, GateStatus


@dataclass(frozen=True, slots=True)
class GateResult:
    gate: str
    status: GateStatus
    score: float
    messages: tuple[str, ...]
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValueError("Gate score must be within [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "status": self.status.value,
            "score": self.score,
            "messages": list(self.messages),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class OAKReport:
    genome_id: str
    status: GateStatus
    score: float
    gates: tuple[GateResult, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    promotion_rule: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "status": self.status.value,
            "score": self.score,
            "gates": [gate.to_dict() for gate in self.gates],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "promotion_rule": self.promotion_rule,
        }


def _status_from_score(score: float, *, hard_failure: bool = False) -> GateStatus:
    if hard_failure or score < 0.45:
        return GateStatus.FAIL
    if score < 0.8:
        return GateStatus.WARN
    return GateStatus.PASS


def _gate_physical_coherence(genome: SolidGenome) -> GateResult:
    messages: list[str] = []
    score = 1.0
    if not genome.properties:
        score -= 0.35
        messages.append("No observable property is encoded.")
    empty_units = [record.name for record in genome.properties if not record.quantity.unit.strip()]
    if empty_units:
        score = 0.0
        messages.append(f"Properties without units: {empty_units}")
    if genome.geometry.get("porosity") is not None:
        value = float(genome.geometry["porosity"])
        if not 0 <= value < 1:
            score = 0.0
            messages.append("Porosity is outside [0, 1).")
    if not genome.assumptions:
        score -= 0.15
        messages.append("No explicit assumptions are recorded.")
    if genome.status in {
        EpistemicStatus.FERTILE_HYPOTHESIS,
        EpistemicStatus.PROPOSED_DESIGN,
    }:
        messages.append("Exploratory status is preserved; no claim promotion is implied.")
    return GateResult(
        "physical_coherence",
        _status_from_score(max(0.0, score)),
        max(0.0, score),
        tuple(messages),
        {
            "property_count": len(genome.properties),
            "assumption_count": len(genome.assumptions),
            "status": genome.status.value,
        },
    )


def _gate_stability(genome: SolidGenome) -> GateResult:
    messages: list[str] = []
    score = 1.0
    signature = build_signature(genome)
    defect_graph = DefectInteractionGraph.infer(genome)
    cascade = defect_graph.cascade_risk()
    if cascade > 0.8:
        score -= 0.45
        messages.append("High heuristic defect-cascade risk; validate against a physics model.")
    elif cascade > 0.5:
        score -= 0.2
        messages.append("Moderate heuristic defect-cascade risk.")
    if not genome.phases:
        score -= 0.2
        messages.append("No phase record; thermodynamic/kinetic stability is unrepresented.")
    if not any("stability" in experiment.lower() for experiment in genome.next_experiments):
        score -= 0.1
        messages.append("No explicit stability experiment is scheduled.")
    return GateResult(
        "stability",
        _status_from_score(max(0.0, score)),
        max(0.0, score),
        tuple(messages),
        {
            "phase_count": len(genome.phases),
            "defect_criticality": signature.defect_criticality,
            "defect_cascade_risk": cascade,
        },
    )


def _gate_reproducibility(genome: SolidGenome) -> GateResult:
    messages: list[str] = []
    process_named = sum(bool(step.get("name") or step.get("operation")) for step in genome.process)
    process_coverage = process_named / len(genome.process) if genome.process else 0.0
    property_metadata = sum(
        bool(record.quantity.source and record.quantity.method)
        for record in genome.properties
    )
    property_coverage = property_metadata / len(genome.properties) if genome.properties else 0.0
    provenance = 1.0 if genome.provenance else 0.0
    score = 0.45 * property_coverage + 0.35 * process_coverage + 0.20 * provenance
    if not genome.process:
        messages.append("No fabrication or preparation process is recorded.")
    if provenance == 0:
        messages.append("No external provenance record is attached.")
    if property_coverage < 1:
        messages.append("Some properties lack source or method metadata.")
    return GateResult(
        "reproducibility",
        _status_from_score(score),
        score,
        tuple(messages),
        {
            "process_coverage": process_coverage,
            "property_metadata_coverage": property_coverage,
            "provenance_present": bool(genome.provenance),
        },
    )


def _gate_baselines(genome: SolidGenome) -> GateResult:
    baseline_tokens = ("baseline", "compare", "reference", "gibson", "hall", "finite-element")
    experiments = " ".join(genome.next_experiments).lower()
    assumptions = " ".join(genome.assumptions).lower()
    has_baseline = any(token in experiments or token in assumptions for token in baseline_tokens)
    score = 1.0 if has_baseline else 0.55
    messages = () if has_baseline else ("No explicit baseline comparison is encoded.",)
    return GateResult(
        "baselines",
        _status_from_score(score),
        score,
        messages,
        {"baseline_reference_detected": has_baseline},
    )


def _gate_uncertainty(genome: SolidGenome) -> GateResult:
    if not genome.properties:
        return GateResult(
            "uncertainty",
            GateStatus.FAIL,
            0.0,
            ("No properties are available for uncertainty assessment.",),
            {"coverage": 0.0},
        )
    coverage = sum(
        record.quantity.uncertainty is not None for record in genome.properties
    ) / len(genome.properties)
    messages = () if coverage == 1 else (f"Uncertainty coverage is {coverage:.1%}.",)
    return GateResult(
        "uncertainty",
        _status_from_score(coverage),
        coverage,
        messages,
        {"coverage": coverage, "property_count": len(genome.properties)},
    )


def _gate_fabricability(genome: SolidGenome) -> GateResult:
    messages: list[str] = []
    process_score = min(1.0, len(genome.process) / 3.0)
    geometry_score = 1.0
    min_feature = genome.geometry.get("minimum_feature_m")
    if min_feature is not None and float(min_feature) <= 0:
        geometry_score = 0.0
        messages.append("Minimum feature size must be positive.")
    if genome.status is EpistemicStatus.PROPOSED_DESIGN:
        messages.append("Proposed design requires fabrication coupons before promotion.")
        geometry_score = min(geometry_score, 0.75)
    if not genome.process:
        messages.append("No fabrication route is encoded.")
    score = 0.6 * process_score + 0.4 * geometry_score
    return GateResult(
        "fabricability",
        _status_from_score(score),
        score,
        tuple(messages),
        {
            "process_steps": len(genome.process),
            "minimum_feature_m": min_feature,
        },
    )


def _gate_function(genome: SolidGenome) -> GateResult:
    application_score = min(1.0, len(genome.applications) / 2.0)
    property_score = min(1.0, len(genome.properties) / 4.0)
    experiment_score = min(1.0, len(genome.next_experiments) / 2.0)
    score = 0.35 * application_score + 0.4 * property_score + 0.25 * experiment_score
    messages: list[str] = []
    if not genome.applications:
        messages.append("No target application is encoded.")
    if not genome.next_experiments:
        messages.append("No discriminating next experiment is encoded.")
    return GateResult(
        "system_function",
        _status_from_score(score),
        score,
        tuple(messages),
        {
            "applications": len(genome.applications),
            "properties": len(genome.properties),
            "next_experiments": len(genome.next_experiments),
        },
    )


def _gate_hypergraph(genome: SolidGenome) -> GateResult:
    graph = SolidHyperGraph.from_genome(genome)
    issues = graph.validate()
    components = graph.connected_components()
    score = 1.0 if not issues and len(components) == 1 else 0.0 if issues else 0.6
    messages: list[str] = list(issues)
    if len(components) != 1:
        messages.append(f"Hypergraph has {len(components)} disconnected components.")
    return GateResult(
        "hypergraph_integrity",
        _status_from_score(score, hard_failure=bool(issues)),
        score,
        tuple(messages),
        {
            "node_count": len(graph.nodes),
            "hyperedge_count": len(graph.edges),
            "component_count": len(components),
        },
    )


_GATE_FUNCTIONS: tuple[Callable[[SolidGenome], GateResult], ...] = (
    _gate_physical_coherence,
    _gate_stability,
    _gate_reproducibility,
    _gate_baselines,
    _gate_uncertainty,
    _gate_fabricability,
    _gate_function,
    _gate_hypergraph,
)


def run_oak_gate(
    genome: SolidGenome,
    *,
    extra_gates: Iterable[Callable[[SolidGenome], GateResult]] = (),
) -> OAKReport:
    gates = tuple(function(genome) for function in (*_GATE_FUNCTIONS, *tuple(extra_gates)))
    hard_failures = [gate for gate in gates if gate.status is GateStatus.FAIL]
    weights = {
        "physical_coherence": 1.5,
        "stability": 1.2,
        "reproducibility": 1.2,
        "baselines": 0.8,
        "uncertainty": 1.1,
        "fabricability": 1.0,
        "system_function": 1.0,
        "hypergraph_integrity": 1.2,
    }
    denominator = sum(weights.get(gate.gate, 1.0) for gate in gates)
    score = sum(gate.score * weights.get(gate.gate, 1.0) for gate in gates) / denominator
    status = (
        GateStatus.FAIL
        if hard_failures
        else GateStatus.PASS
        if score >= 0.8
        else GateStatus.WARN
    )
    blockers = tuple(
        f"{gate.gate}: {message}"
        for gate in hard_failures
        for message in (gate.messages or ("gate failed",))
    )
    warnings = tuple(
        f"{gate.gate}: {message}"
        for gate in gates
        if gate.status is GateStatus.WARN
        for message in (gate.messages or ("gate requires review",))
    )
    return OAKReport(
        genome.identifier,
        status,
        score,
        gates,
        blockers,
        warnings,
        (
            "Promotion requires no failed gate, score >= 0.80, explicit provenance, "
            "and human review for safety-, IP-, fabrication-, or publication-sensitive claims."
        ),
    )
