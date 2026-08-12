"""Ω-GREATSAGES-TIME-MACHINE-T∞ — R0.2 executable primitives.

This module deepens AIT-GreatSages without pretending to reproduce a historical
person.  It models auditable knowledge-state transformations: multi-axis time,
world/public/private/latent/counterfactual layers, causal leakage firewalls,
notation/instrument admissibility, representation morphisms, mirror algebra,
discovery genomes, cognitive operators, epistemic debt and provenance.

All counterfactual and inferred objects are explicitly typed.  Historical truth
is never certified by software alone.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
import math
from typing import Iterable, Mapping, Sequence

from sage_tristan.greatsages import (
    ClaimClass,
    Discovery,
    MirrorKind,
    SageProfile,
    discovery_by_id,
    get_profile,
)


class KnowledgeLayer(str, Enum):
    WORLD = "world"
    PUBLIC = "public"
    PRIVATE = "private"
    LATENT = "latent"
    COUNTERFACTUAL = "counterfactual"


class TemporalAxis(str, Enum):
    WORLD = "world"
    ACCESSIBLE = "accessible"
    READ = "read"
    UNDERSTOOD = "understood"
    DISCOVERED = "discovered"
    WRITTEN = "written"
    PUBLISHED = "published"


class Admissibility(str, Enum):
    ALLOWED = "allowed"
    BLOCKED_FUTURE = "blocked_future"
    BLOCKED_LAYER = "blocked_layer"
    BLOCKED_NOTATION = "blocked_notation"
    BLOCKED_INSTRUMENT = "blocked_instrument"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TemporalVector:
    world: int | None = None
    accessible: int | None = None
    read: int | None = None
    understood: int | None = None
    discovered: int | None = None
    written: int | None = None
    published: int | None = None

    def value(self, axis: TemporalAxis) -> int | None:
        return getattr(self, axis.value)

    def effective_year(self, axis: TemporalAxis) -> int | None:
        """Return the requested axis, falling back only toward less-private axes.

        Missing private timing is unknown rather than silently inferred from a
        publication date.  WORLD and ACCESSIBLE can safely fall back to WORLD.
        """
        direct = self.value(axis)
        if direct is not None:
            return direct
        if axis is TemporalAxis.ACCESSIBLE:
            return self.world
        return None


@dataclass(frozen=True, slots=True)
class ProvenanceTensor:
    source_id: str
    source_type: str
    year: int | None = None
    author: str = ""
    language: str = ""
    edition: str = ""
    directness: float = 0.5
    certainty: float = 0.5
    interpretation_depth: int = 0

    def __post_init__(self) -> None:
        for value, name in ((self.directness, "directness"), (self.certainty, "certainty")):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.interpretation_depth < 0:
            raise ValueError("interpretation_depth must be non-negative")

    @property
    def evidence_weight(self) -> float:
        depth_penalty = 1.0 / (1.0 + self.interpretation_depth)
        return round(self.directness * self.certainty * depth_penalty, 6)


@dataclass(frozen=True, slots=True)
class TimedKnowledge:
    atom_id: str
    label: str
    layer: KnowledgeLayer
    time: TemporalVector
    domains: tuple[str, ...] = ()
    notation_ids: tuple[str, ...] = ()
    instrument_ids: tuple[str, ...] = ()
    provenance: tuple[ProvenanceTensor, ...] = ()
    claim_class: ClaimClass = ClaimClass.SOURCE_REPORTED

    def admitted(self, year: int, *, axis: TemporalAxis, layers: frozenset[KnowledgeLayer]) -> Admissibility:
        if self.layer not in layers:
            return Admissibility.BLOCKED_LAYER
        effective = self.time.effective_year(axis)
        if effective is None:
            return Admissibility.UNKNOWN
        return Admissibility.ALLOWED if effective <= year else Admissibility.BLOCKED_FUTURE


@dataclass(frozen=True, slots=True)
class NotationSystem:
    notation_id: str
    label: str
    available_from_year: int
    domains: tuple[str, ...] = ()
    expressive_tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InstrumentCapability:
    instrument_id: str
    label: str
    available_from_year: int
    observables: tuple[str, ...]
    relative_precision: float | None = None

    def __post_init__(self) -> None:
        if self.relative_precision is not None and self.relative_precision <= 0:
            raise ValueError("relative_precision must be positive")


@dataclass(frozen=True, slots=True)
class HistoricalContext:
    year: int
    axis: TemporalAxis = TemporalAxis.ACCESSIBLE
    allowed_layers: frozenset[KnowledgeLayer] = frozenset({KnowledgeLayer.WORLD, KnowledgeLayer.PUBLIC, KnowledgeLayer.PRIVATE})
    notation_ids: frozenset[str] = frozenset()
    instrument_ids: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class TimeMachineSnapshot:
    sage_id: str
    context: HistoricalContext
    allowed_atom_ids: tuple[str, ...]
    blocked_atom_ids: tuple[str, ...]
    unknown_timing_atom_ids: tuple[str, ...]
    blocked_by_layer_atom_ids: tuple[str, ...]
    leakage_free: bool


@dataclass(frozen=True, slots=True)
class CausalFirewall:
    target_discovery_id: str
    masked_discovery_ids: tuple[str, ...]
    visible_discovery_ids: tuple[str, ...]
    descendants_masked: tuple[str, ...]
    target_masked: bool


@dataclass(frozen=True, slots=True)
class RepresentationMorphism:
    morphism_id: str
    source_representation: str
    target_representation: str
    preserved_invariants: tuple[str, ...]
    complexity_before: float
    complexity_after: float
    reversible: bool = False
    claim_class: ClaimClass = ClaimClass.RECONSTRUCTION

    @property
    def complexity_gain(self) -> float:
        return round(self.complexity_before - self.complexity_after, 6)


@dataclass(frozen=True, slots=True)
class MirrorExpression:
    operations: tuple[MirrorKind, ...]

    def __post_init__(self) -> None:
        if not self.operations:
            raise ValueError("mirror expression cannot be empty")

    @property
    def expression(self) -> str:
        return " ∘ ".join(operation.value for operation in self.operations)

    @property
    def claim_class(self) -> ClaimClass:
        if MirrorKind.FUTURE in self.operations:
            return ClaimClass.COUNTERFACTUAL
        if MirrorKind.TRISTAN in self.operations:
            return ClaimClass.FERTILE_HYPOTHESIS
        return ClaimClass.RECONSTRUCTION


@dataclass(frozen=True, slots=True)
class DiscoveryGenome:
    discovery_id: str
    problems: tuple[str, ...]
    observations: tuple[str, ...]
    representations: tuple[str, ...]
    symmetries: tuple[str, ...]
    invariants: tuple[str, ...]
    constraints: tuple[str, ...]
    algorithms: tuple[str, ...]
    evidence: tuple[str, ...]
    failures: tuple[str, ...]
    uncertainties: tuple[str, ...]
    positive_memory: tuple[str, ...]
    negative_memory: tuple[str, ...]

    def feature_set(self) -> frozenset[str]:
        values: set[str] = set()
        for key, items in asdict(self).items():
            if key == "discovery_id":
                continue
            for item in items:
                values.add(f"{key}:{item.strip().lower()}")
        return frozenset(values)


@dataclass(frozen=True, slots=True)
class CognitiveOperator:
    operator_id: str
    label: str
    action: str
    evidence_discovery_ids: tuple[str, ...]
    source_ids: tuple[str, ...] = ()
    confidence: float = 0.5
    counter_operator_id: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class OperatorProgram:
    operator_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.operator_ids:
            raise ValueError("operator program cannot be empty")

    @property
    def assembly(self) -> str:
        return " -> ".join(self.operator_ids)


@dataclass(frozen=True, slots=True)
class EpistemicDebt:
    untested_assumptions: int = 0
    weak_dependencies: int = 0
    uncertain_attributions: int = 0
    missing_reproductions: int = 0
    unresolved_counterexamples: int = 0
    provenance_penalty: float = 0.0

    def __post_init__(self) -> None:
        integer_fields = (
            self.untested_assumptions,
            self.weak_dependencies,
            self.uncertain_attributions,
            self.missing_reproductions,
            self.unresolved_counterexamples,
        )
        if any(value < 0 for value in integer_fields) or self.provenance_penalty < 0:
            raise ValueError("epistemic debt components must be non-negative")

    @property
    def score(self) -> float:
        raw = (
            1.5 * self.untested_assumptions
            + 1.2 * self.weak_dependencies
            + 1.4 * self.uncertain_attributions
            + 1.3 * self.missing_reproductions
            + 1.6 * self.unresolved_counterexamples
            + self.provenance_penalty
        )
        return round(raw, 6)


@dataclass(frozen=True, slots=True)
class LineageReceipt:
    artifact_id: str
    source_ids: tuple[str, ...]
    operator_ids: tuple[str, ...]
    transformations: tuple[str, ...]
    tests: tuple[str, ...]
    claim_class: ClaimClass

    @property
    def lineage_hash(self) -> str:
        payload = json.dumps(
            {
                "artifact_id": self.artifact_id,
                "source_ids": self.source_ids,
                "operator_ids": self.operator_ids,
                "transformations": self.transformations,
                "tests": self.tests,
                "claim_class": self.claim_class.value,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class KnowledgeField:
    known_ids: tuple[str, ...]
    frontier_ids: tuple[str, ...]
    unknown_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        sets = [set(self.known_ids), set(self.frontier_ids), set(self.unknown_ids)]
        if any(sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3)):
            raise ValueError("knowledge field partitions must be disjoint")


@dataclass(frozen=True, slots=True)
class DiscoveryPotential:
    problem_id: str
    proximity: float
    representation_access: float
    data_access: float
    proof_access: float
    invariant_access: float
    instrument_access: float
    notation_access: float
    dependency_access: float

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if key == "problem_id":
                continue
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{key} must be between 0 and 1")

    @property
    def accessibility(self) -> float:
        values = [
            self.proximity,
            self.representation_access,
            self.data_access,
            self.proof_access,
            self.invariant_access,
            self.instrument_access,
            self.notation_access,
            self.dependency_access,
        ]
        # Geometric mean punishes one missing enabling factor more strongly than
        # an arithmetic mean and stays in [0, 1].
        if any(value == 0 for value in values):
            return 0.0
        return round(math.prod(values) ** (1.0 / len(values)), 6)

    @property
    def discovery_barrier(self) -> float:
        return round(1.0 - self.accessibility, 6)


@dataclass(frozen=True, slots=True)
class QuestionCandidate:
    question_id: str
    text: str
    information_gain: float
    fertility: float
    transfer: float
    cost: float
    risk: float
    uncertainty: float

    @property
    def value(self) -> float:
        numerator = max(0.0, self.information_gain) * max(0.0, self.fertility) * max(0.0, self.transfer)
        denominator = max(1e-9, self.cost + self.risk + self.uncertainty)
        return round(numerator / denominator, 6)


@dataclass(frozen=True, slots=True)
class DigitalTwinState:
    sage_id: str
    year: int
    model_not_person: bool
    knowledge_snapshot: TimeMachineSnapshot
    visible_discovery_ids: tuple[str, ...]
    operator_ids: tuple[str, ...]
    uncertainty_notes: tuple[str, ...]


GAUSS_TIMED_KNOWLEDGE: tuple[TimedKnowledge, ...] = (
    TimedKnowledge(
        "symmetry_pairing",
        "Symmetry can compress repeated arithmetic work",
        KnowledgeLayer.PUBLIC,
        TemporalVector(world=1787, accessible=1787),
        domains=("arithmetic",),
        claim_class=ClaimClass.RECONSTRUCTION,
    ),
    TimedKnowledge(
        "prime_density_interest",
        "Empirical study of prime-number frequency",
        KnowledgeLayer.PRIVATE,
        TemporalVector(world=1792, accessible=1792, understood=1792),
        domains=("number_theory",),
        provenance=(ProvenanceTensor("gauss_bio_goettingen", "secondary", directness=0.55, certainty=0.75, interpretation_depth=1),),
    ),
    TimedKnowledge(
        "cyclotomy_seed",
        "Division of the circle and roots of unity as linked representations",
        KnowledgeLayer.PRIVATE,
        TemporalVector(world=1796, accessible=1796, discovered=1796, written=1796, published=1801),
        domains=("number_theory", "geometry", "algebra"),
        notation_ids=("algebraic_symbolism_1790s",),
        provenance=(ProvenanceTensor("gauss_bio_goettingen", "secondary", directness=0.6, certainty=0.85, interpretation_depth=1),),
    ),
    TimedKnowledge(
        "congruence_language",
        "Congruence notation and arithmetic modulo an integer",
        KnowledgeLayer.PUBLIC,
        TemporalVector(world=1801, accessible=1801, published=1801),
        domains=("number_theory",),
        notation_ids=("gaussian_congruence_notation",),
        provenance=(ProvenanceTensor("gauss_chronology_utk", "secondary", directness=0.55, certainty=0.85, interpretation_depth=1),),
    ),
    TimedKnowledge(
        "orbit_inference",
        "Infer an orbit from sparse astronomical observations",
        KnowledgeLayer.PUBLIC,
        TemporalVector(world=1801, accessible=1801, understood=1801, discovered=1801, written=1801),
        domains=("astronomy", "inverse_problems"),
        instrument_ids=("optical_astronomy_observations",),
        provenance=(ProvenanceTensor("gauss_bio_goettingen", "secondary", directness=0.6, certainty=0.9, interpretation_depth=1),),
    ),
    TimedKnowledge(
        "least_squares_public",
        "Least-squares estimation in published astronomical work",
        KnowledgeLayer.PUBLIC,
        TemporalVector(world=1809, accessible=1809, published=1809),
        domains=("statistics", "astronomy"),
        provenance=(ProvenanceTensor("gauss_chronology_utk", "secondary", directness=0.55, certainty=0.9, interpretation_depth=1),),
    ),
    TimedKnowledge(
        "intrinsic_curvature",
        "Surface curvature can be characterized intrinsically",
        KnowledgeLayer.PUBLIC,
        TemporalVector(world=1827, accessible=1827, published=1827),
        domains=("geometry", "geodesy"),
        provenance=(ProvenanceTensor("gauss_chronology_utk", "secondary", directness=0.55, certainty=0.9, interpretation_depth=1),),
    ),
    TimedKnowledge(
        "gauss_latent_invariant_operator",
        "Interpreted recurring tendency to search for invariants across representations",
        KnowledgeLayer.LATENT,
        TemporalVector(world=1827),
        domains=("meta_reasoning",),
        claim_class=ClaimClass.RECONSTRUCTION,
    ),
    TimedKnowledge(
        "gauss_2026_counterfactual_tooling",
        "Counterfactual access to modern symbolic/numeric/formal tools",
        KnowledgeLayer.COUNTERFACTUAL,
        TemporalVector(world=2026, accessible=2026),
        domains=("computation",),
        claim_class=ClaimClass.COUNTERFACTUAL,
    ),
)


GAUSS_NOTATIONS: tuple[NotationSystem, ...] = (
    NotationSystem("algebraic_symbolism_1790s", "Late-18th-century algebraic symbolism", 1790, ("algebra",), ("symbolic_manipulation",)),
    NotationSystem("gaussian_congruence_notation", "Gauss-style congruence notation", 1801, ("number_theory",), ("equivalence_classes", "modular_arithmetic")),
    NotationSystem("modern_linear_algebra", "Modern matrix/vector notation", 1900, ("linear_algebra",), ("compact_system_representation",)),
)


GAUSS_INSTRUMENTS: tuple[InstrumentCapability, ...] = (
    InstrumentCapability("optical_astronomy_observations", "Historical optical astronomical observations", 1801, ("angular_position", "time")),
    InstrumentCapability("geodetic_triangulation", "Geodetic triangulation instrumentation", 1818, ("angles", "baseline_distance")),
    InstrumentCapability("gauss_weber_magnetometer", "Gauss-Weber magnetic measurement apparatus", 1832, ("magnetic_field", "oscillation_period")),
    InstrumentCapability("modern_computer", "Modern digital computation", 1940, ("symbolic_expression", "numerical_state")),
)


GAUSS_OPERATORS: tuple[CognitiveOperator, ...] = (
    CognitiveOperator("symmetry_compression", "Symmetry compression", "Search pairings/group actions that reduce repeated work.", ("gauss_1796_17gon",), confidence=0.6, counter_operator_id="anti_symmetry_expand"),
    CognitiveOperator("representation_switch", "Representation switch", "Map a stubborn problem into a representation exposing simpler invariants.", ("gauss_1796_17gon", "gauss_1801_disquisitiones"), confidence=0.8, counter_operator_id="anti_switch_stay_native"),
    CognitiveOperator("invariant_search", "Invariant search", "Search quantities preserved under allowed transformations.", ("gauss_1827_surfaces",), confidence=0.8, counter_operator_id="anti_invariant_residual"),
    CognitiveOperator("approximation_residual", "Approximation and residual control", "Fit latent models and audit residual error against observations.", ("gauss_1801_ceres", "gauss_1809_theoria_motus"), confidence=0.8, counter_operator_id="anti_fit_exact_structure"),
    CognitiveOperator("anti_symmetry_expand", "Anti-symmetry expansion", "Refuse premature symmetry compression and inspect asymmetric residual structure.", (), confidence=0.4, counter_operator_id="symmetry_compression"),
    CognitiveOperator("anti_switch_stay_native", "Native-representation adversary", "Test whether a representation switch hides structure or injects anachronistic machinery.", (), confidence=0.4, counter_operator_id="representation_switch"),
    CognitiveOperator("anti_invariant_residual", "Non-invariant residual hunter", "Search information discarded by an invariant representation.", (), confidence=0.4, counter_operator_id="invariant_search"),
    CognitiveOperator("anti_fit_exact_structure", "Exact-structure adversary", "Test whether fitting masks an exact discrete or algebraic relation.", (), confidence=0.4, counter_operator_id="approximation_residual"),
)


def _timed_lookup(profile: SageProfile) -> tuple[TimedKnowledge, ...]:
    if profile.sage_id == "gauss":
        return GAUSS_TIMED_KNOWLEDGE
    # Safe generic fallback: public accessibility equals the R0.1 seed year.
    return tuple(
        TimedKnowledge(
            atom.atom_id,
            atom.label,
            KnowledgeLayer.PUBLIC,
            TemporalVector(world=atom.available_from_year, accessible=atom.available_from_year),
            domains=atom.domains,
            claim_class=atom.claim_class,
        )
        for atom in profile.knowledge
    )


def _notation_lookup(profile: SageProfile) -> tuple[NotationSystem, ...]:
    return GAUSS_NOTATIONS if profile.sage_id == "gauss" else ()


def _instrument_lookup(profile: SageProfile) -> tuple[InstrumentCapability, ...]:
    return GAUSS_INSTRUMENTS if profile.sage_id == "gauss" else ()


def _operator_lookup(profile: SageProfile) -> tuple[CognitiveOperator, ...]:
    if profile.sage_id == "gauss":
        return GAUSS_OPERATORS
    return tuple(
        CognitiveOperator(operator_id=value, label=value.replace("_", " ").title(), action="Profile-declared candidate operator.", evidence_discovery_ids=(), confidence=0.3)
        for value in profile.cognitive_operators
    )


def default_context(profile: SageProfile, year: int, *, axis: TemporalAxis = TemporalAxis.ACCESSIBLE) -> HistoricalContext:
    notations = frozenset(item.notation_id for item in _notation_lookup(profile) if item.available_from_year <= year)
    instruments = frozenset(item.instrument_id for item in _instrument_lookup(profile) if item.available_from_year <= year)
    return HistoricalContext(year=year, axis=axis, notation_ids=notations, instrument_ids=instruments)


def time_machine_snapshot(profile: SageProfile, context: HistoricalContext) -> TimeMachineSnapshot:
    allowed: list[str] = []
    blocked: list[str] = []
    unknown: list[str] = []
    blocked_layer: list[str] = []
    for atom in _timed_lookup(profile):
        status = atom.admitted(context.year, axis=context.axis, layers=context.allowed_layers)
        if status is Admissibility.ALLOWED:
            # Knowledge requiring a notation or instrument is blocked if the
            # context does not contain every declared enabling capability.
            if atom.notation_ids and not set(atom.notation_ids) <= set(context.notation_ids):
                blocked.append(atom.atom_id)
            elif atom.instrument_ids and not set(atom.instrument_ids) <= set(context.instrument_ids):
                blocked.append(atom.atom_id)
            else:
                allowed.append(atom.atom_id)
        elif status is Admissibility.UNKNOWN:
            unknown.append(atom.atom_id)
        elif status is Admissibility.BLOCKED_LAYER:
            blocked_layer.append(atom.atom_id)
        else:
            blocked.append(atom.atom_id)
    overlap = set(allowed) & (set(blocked) | set(unknown) | set(blocked_layer))
    return TimeMachineSnapshot(
        sage_id=profile.sage_id,
        context=context,
        allowed_atom_ids=tuple(sorted(allowed)),
        blocked_atom_ids=tuple(sorted(blocked)),
        unknown_timing_atom_ids=tuple(sorted(unknown)),
        blocked_by_layer_atom_ids=tuple(sorted(blocked_layer)),
        leakage_free=not overlap,
    )


def discovery_descendants(profile: SageProfile, discovery_id: str) -> tuple[str, ...]:
    discovery_by_id(profile, discovery_id)
    children: dict[str, set[str]] = {item.discovery_id: set() for item in profile.discoveries}
    for item in profile.discoveries:
        for prerequisite in item.prerequisite_ids:
            children.setdefault(prerequisite, set()).add(item.discovery_id)
    seen: set[str] = set()
    frontier = list(children.get(discovery_id, ()))
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        frontier.extend(children.get(current, ()))
    return tuple(sorted(seen))


def causal_leakage_firewall(profile: SageProfile, discovery_id: str, *, year: int | None = None) -> CausalFirewall:
    target = discovery_by_id(profile, discovery_id)
    gate_year = target.year - 1 if year is None else year
    descendants = set(discovery_descendants(profile, discovery_id))
    masked = {discovery_id, *descendants}
    # Also mask every discovery dated after the gate: descendants are necessary
    # but not sufficient protection against hindsight leakage.
    masked.update(item.discovery_id for item in profile.discoveries if item.year > gate_year)
    visible = tuple(sorted(item.discovery_id for item in profile.discoveries if item.discovery_id not in masked and item.year <= gate_year))
    return CausalFirewall(
        target_discovery_id=discovery_id,
        masked_discovery_ids=tuple(sorted(masked)),
        visible_discovery_ids=visible,
        descendants_masked=tuple(sorted(descendants)),
        target_masked=discovery_id in masked,
    )


def notation_admissibility(profile: SageProfile, notation_id: str, year: int) -> Admissibility:
    for item in _notation_lookup(profile):
        if item.notation_id == notation_id:
            return Admissibility.ALLOWED if item.available_from_year <= year else Admissibility.BLOCKED_NOTATION
    return Admissibility.UNKNOWN


def instrument_admissibility(profile: SageProfile, instrument_id: str, year: int) -> Admissibility:
    for item in _instrument_lookup(profile):
        if item.instrument_id == instrument_id:
            return Admissibility.ALLOWED if item.available_from_year <= year else Admissibility.BLOCKED_INSTRUMENT
    return Admissibility.UNKNOWN


def compose_mirrors(*operations: MirrorKind) -> MirrorExpression:
    return MirrorExpression(tuple(operations))


def genome_from_discovery(profile: SageProfile, discovery_id: str) -> DiscoveryGenome:
    item = discovery_by_id(profile, discovery_id)
    return DiscoveryGenome(
        discovery_id=item.discovery_id,
        problems=(item.problem,),
        observations=("source-traced evidence required",),
        representations=item.representations,
        symmetries=tuple(value for value in item.representations if "sym" in value.lower() or "cycl" in value.lower()),
        invariants=(item.compressed_invariant,),
        constraints=tuple(f"prerequisite:{value}" for value in item.prerequisite_ids),
        algorithms=("compile executable reconstruction only after representation/proof audit",),
        evidence=tuple(f"source:{value}" for value in item.source_ids),
        failures=("historical path incompletely observed",),
        uncertainties=("dependency edges are replay-model dependencies, not unique historical causation",),
        positive_memory=("retain representation and invariant transformations that survive OAK tests",),
        negative_memory=("reject hindsight leakage and novelty inflation",),
    )


def genome_distance(left: DiscoveryGenome, right: DiscoveryGenome) -> float:
    a = left.feature_set()
    b = right.feature_set()
    if not a and not b:
        return 0.0
    union = a | b
    intersection = a & b
    return round(1.0 - len(intersection) / len(union), 6)


def structural_transfer_candidates(profile: SageProfile, source_discovery_id: str) -> tuple[tuple[str, float], ...]:
    source = genome_from_discovery(profile, source_discovery_id)
    candidates = []
    for item in profile.discoveries:
        if item.discovery_id == source_discovery_id:
            continue
        distance = genome_distance(source, genome_from_discovery(profile, item.discovery_id))
        candidates.append((item.discovery_id, distance))
    return tuple(sorted(candidates, key=lambda pair: (pair[1], pair[0])))


def operator_registry(profile: SageProfile) -> Mapping[str, CognitiveOperator]:
    return {item.operator_id: item for item in _operator_lookup(profile)}


def compile_operator_program(profile: SageProfile, operator_ids: Sequence[str]) -> OperatorProgram:
    registry = operator_registry(profile)
    unknown = sorted(set(operator_ids) - set(registry))
    if unknown:
        raise KeyError(f"unknown operator ids: {unknown}")
    return OperatorProgram(tuple(operator_ids))


def minimal_discovery_set(profile: SageProfile, discovery_id: str) -> tuple[str, ...]:
    target = discovery_by_id(profile, discovery_id)
    lookup = {item.discovery_id: item for item in profile.discoveries}
    required: set[str] = set()
    frontier = list(target.prerequisite_ids)
    while frontier:
        current = frontier.pop()
        if current in required:
            continue
        required.add(current)
        frontier.extend(lookup[current].prerequisite_ids)
    return tuple(sorted(required))


def knowledge_field(profile: SageProfile, year: int) -> KnowledgeField:
    known = {item.discovery_id for item in profile.discoveries if item.year <= year}
    frontier = {
        item.discovery_id
        for item in profile.discoveries
        if item.year > year and set(item.prerequisite_ids) <= known
    }
    unknown = {item.discovery_id for item in profile.discoveries} - known - frontier
    return KnowledgeField(tuple(sorted(known)), tuple(sorted(frontier)), tuple(sorted(unknown)))


def estimate_discovery_potential(profile: SageProfile, discovery_id: str, *, year: int) -> DiscoveryPotential:
    item = discovery_by_id(profile, discovery_id)
    known = {d.discovery_id for d in profile.discoveries if d.year <= year}
    dependency_access = 1.0 if set(item.prerequisite_ids) <= known else 0.25
    representation_access = min(1.0, 0.25 + 0.15 * len(item.representations))
    notation_access = 1.0 if _notation_lookup(profile) else 0.6
    instrument_access = 1.0 if not (set(item.domains) & {"astronomy", "physics", "geodesy"}) else (0.8 if _instrument_lookup(profile) else 0.35)
    temporal_gap = max(0, item.year - year)
    proximity = 1.0 / (1.0 + temporal_gap / 10.0)
    return DiscoveryPotential(
        problem_id=item.discovery_id,
        proximity=round(proximity, 6),
        representation_access=representation_access,
        data_access=0.7 if "astronomy" in item.domains else 0.8,
        proof_access=0.65 if "geometry" in item.domains or "number_theory" in item.domains else 0.75,
        invariant_access=0.75,
        instrument_access=instrument_access,
        notation_access=notation_access,
        dependency_access=dependency_access,
    )


def rank_questions(candidates: Iterable[QuestionCandidate]) -> tuple[QuestionCandidate, ...]:
    return tuple(sorted(candidates, key=lambda item: (-item.value, item.question_id)))


def epistemic_debt_for_discovery(profile: SageProfile, discovery_id: str) -> EpistemicDebt:
    item = discovery_by_id(profile, discovery_id)
    provenance_records = [
        tensor
        for atom in _timed_lookup(profile)
        for tensor in atom.provenance
        if tensor.source_id in set(item.source_ids)
    ]
    if provenance_records:
        mean_weight = sum(record.evidence_weight for record in provenance_records) / len(provenance_records)
        provenance_penalty = max(0.0, 2.0 * (1.0 - mean_weight))
    else:
        provenance_penalty = 2.0
    return EpistemicDebt(
        untested_assumptions=1,
        weak_dependencies=len(item.prerequisite_ids),
        uncertain_attributions=0 if item.source_ids else 1,
        missing_reproductions=1,
        unresolved_counterexamples=0,
        provenance_penalty=round(provenance_penalty, 6),
    )


def lineage_receipt(profile: SageProfile, discovery_id: str, *, mirror: MirrorExpression | None = None, operator_ids: Sequence[str] = ()) -> LineageReceipt:
    item = discovery_by_id(profile, discovery_id)
    transformations = (mirror.expression,) if mirror is not None else ("historical_seed_to_discovery_genome",)
    claim_class = mirror.claim_class if mirror is not None else item.claim_class
    return LineageReceipt(
        artifact_id=f"greatsages::{profile.sage_id}::{discovery_id}",
        source_ids=item.source_ids,
        operator_ids=tuple(operator_ids),
        transformations=transformations,
        tests=("causal_leakage_firewall", "epistemic_separation", "deterministic_lineage_hash"),
        claim_class=claim_class,
    )


def digital_twin(profile: SageProfile, year: int) -> DigitalTwinState:
    context = default_context(profile, year)
    snapshot = time_machine_snapshot(profile, context)
    visible = tuple(sorted(item.discovery_id for item in profile.discoveries if item.year <= year))
    return DigitalTwinState(
        sage_id=profile.sage_id,
        year=year,
        model_not_person=True,
        knowledge_snapshot=snapshot,
        visible_discovery_ids=visible,
        operator_ids=tuple(sorted(operator_registry(profile))),
        uncertainty_notes=(
            "This is an auditable model of allowed knowledge and candidate operators, not a simulation of a person's mind.",
            "Private/latent timing is unknown unless source-traced; absence of evidence is not treated as evidence of absence.",
        ),
    )


def compile_r02_report(profile: SageProfile, year: int, *, discovery_id: str | None = None) -> dict[str, object]:
    context = default_context(profile, year)
    snapshot = time_machine_snapshot(profile, context)
    payload: dict[str, object] = {
        "engine": "Ω-GREATSAGES-TIME-MACHINE-T∞",
        "release": "R0.2",
        "sage_id": profile.sage_id,
        "year": year,
        "time_machine_snapshot": asdict(snapshot),
        "knowledge_field": asdict(knowledge_field(profile, year)),
        "notation_ids": tuple(sorted(context.notation_ids)),
        "instrument_ids": tuple(sorted(context.instrument_ids)),
        "operator_ids": tuple(sorted(operator_registry(profile))),
        "model_not_person": True,
        "historical_truth_certified": False,
        "counterfactuals_are_history": False,
        "oak_note": "world/public/private/latent/counterfactual layers and historical/reconstruction/hypothesis classes must remain separated",
    }
    if discovery_id:
        genome = genome_from_discovery(profile, discovery_id)
        mirror = compose_mirrors(MirrorKind.OAK, MirrorKind.TRISTAN, MirrorKind.COMPUTATIONAL)
        receipt = lineage_receipt(profile, discovery_id, mirror=mirror, operator_ids=("representation_switch", "invariant_search"))
        payload.update(
            {
                "firewall": asdict(causal_leakage_firewall(profile, discovery_id)),
                "minimal_discovery_set": minimal_discovery_set(profile, discovery_id),
                "genome": asdict(genome),
                "transfer_candidates": structural_transfer_candidates(profile, discovery_id),
                "mirror_expression": asdict(mirror),
                "mirror_expression_text": mirror.expression,
                "mirror_claim_class": mirror.claim_class.value,
                "epistemic_debt": {**asdict(epistemic_debt_for_discovery(profile, discovery_id)), "score": epistemic_debt_for_discovery(profile, discovery_id).score},
                "discovery_potential": {**asdict(estimate_discovery_potential(profile, discovery_id, year=year)), "accessibility": estimate_discovery_potential(profile, discovery_id, year=year).accessibility, "discovery_barrier": estimate_discovery_potential(profile, discovery_id, year=year).discovery_barrier},
                "lineage": {**asdict(receipt), "lineage_hash": receipt.lineage_hash},
            }
        )
    return payload


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, frozenset):
        return sorted(_jsonable(item) for item in value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ω-GreatSages Time Machine R0.2")
    parser.add_argument("--sage", default="gauss")
    parser.add_argument("--year", type=int, default=1801)
    parser.add_argument("--discovery")
    parser.add_argument("--twin", action="store_true")
    args = parser.parse_args(argv)
    profile = get_profile(args.sage)
    payload: dict[str, object] = {"report": compile_r02_report(profile, args.year, discovery_id=args.discovery)}
    if args.twin:
        payload["digital_twin"] = asdict(digital_twin(profile, args.year))
    print(json.dumps(_jsonable(payload), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
