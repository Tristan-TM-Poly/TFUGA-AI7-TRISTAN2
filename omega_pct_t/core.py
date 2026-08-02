from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import math


class EpistemicStatus(str, Enum):
    ESTABLISHED = "established"
    EFFECTIVE = "effective"
    PARAMETRIZATION = "parametrization"
    HYPOTHESIS = "hypothesis"
    EXPLORATORY = "exploratory"
    EXCLUDED = "excluded"
    UNKNOWN = "unknown"


class OntologyLevel(str, Enum):
    FUNDAMENTAL = "fundamental"
    COMPOSITE = "composite"
    EFFECTIVE = "effective"
    COLLECTIVE = "collective"
    TOPOLOGICAL = "topological"
    HYPOTHETICAL = "hypothetical"
    MEASUREMENT = "measurement"


class SpinClass(str, Enum):
    SCALAR = "scalar"
    FERMION = "fermion"
    VECTOR = "vector"
    TENSOR = "tensor"
    ANYONIC = "anyonic"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"
    path: str = ""


@dataclass(frozen=True)
class EvidenceRef:
    identifier: str
    title: str
    source_type: str
    locator: str = ""
    status: EpistemicStatus = EpistemicStatus.UNKNOWN
    notes: str = ""

    def validate(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not self.identifier.strip():
            issues.append(ValidationIssue("evidence.identifier.empty", "Evidence identifier is required."))
        if not self.title.strip():
            issues.append(ValidationIssue("evidence.title.empty", "Evidence title is required."))
        return issues


@dataclass(frozen=True)
class QuantumNumbers:
    electric_charge_e: float = 0.0
    baryon_number: float = 0.0
    lepton_numbers: Mapping[str, float] = field(default_factory=dict)
    color_representation: str = "1"
    weak_isospin: float | None = None
    weak_hypercharge: float | None = None
    parity: str | None = None
    c_parity: str | None = None
    cp: str | None = None

    def additive_vector(self) -> dict[str, float]:
        values = {
            "electric_charge_e": float(self.electric_charge_e),
            "baryon_number": float(self.baryon_number),
        }
        for family, value in self.lepton_numbers.items():
            values[f"lepton:{family}"] = float(value)
        return values


@dataclass(frozen=True)
class FieldSpec:
    id: str
    name: str
    symbol: str
    spin_class: SpinClass
    lorentz_representation: str
    gauge_representations: Mapping[str, str]
    mass_dimension: float
    ontology_level: OntologyLevel = OntologyLevel.FUNDAMENTAL
    status: EpistemicStatus = EpistemicStatus.ESTABLISHED
    description: str = ""
    evidence: tuple[EvidenceRef, ...] = ()
    tags: tuple[str, ...] = ()

    def validate(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not self.id or any(ch.isspace() for ch in self.id):
            issues.append(ValidationIssue("field.id.invalid", "Field id must be non-empty and whitespace-free.", path=self.id))
        if not math.isfinite(self.mass_dimension):
            issues.append(ValidationIssue("field.dimension.nonfinite", "Field mass dimension must be finite.", path=self.id))
        if self.mass_dimension < 0:
            issues.append(ValidationIssue("field.dimension.negative", "Negative field mass dimension requires explicit model justification.", "warning", self.id))
        for item in self.evidence:
            issues.extend(item.validate())
        return issues


@dataclass(frozen=True)
class ParticleSpec:
    id: str
    name: str
    symbol: str
    field_ids: tuple[str, ...]
    ontology_level: OntologyLevel
    spin: float | None
    spin_class: SpinClass
    quantum_numbers: QuantumNumbers = field(default_factory=QuantumNumbers)
    antiparticle_id: str | None = None
    mass_gev: float | None = None
    width_gev: float | None = None
    stable_in_vacuum: bool | None = None
    composition: tuple[str, ...] = ()
    dispersion_relation: str = "E^2=p^2+m^2"
    status: EpistemicStatus = EpistemicStatus.ESTABLISHED
    confidence: float = 1.0
    scale_min_gev: float | None = None
    scale_max_gev: float | None = None
    evidence: tuple[EvidenceRef, ...] = ()
    tags: tuple[str, ...] = ()
    notes: str = ""

    def validate(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not self.id or any(ch.isspace() for ch in self.id):
            issues.append(ValidationIssue("particle.id.invalid", "Particle id must be non-empty and whitespace-free.", path=self.id))
        if not 0.0 <= self.confidence <= 1.0:
            issues.append(ValidationIssue("particle.confidence.range", "Confidence must be in [0, 1].", path=self.id))
        if self.mass_gev is not None and self.mass_gev < 0:
            issues.append(ValidationIssue("particle.mass.negative", "Mass cannot be negative in this registry representation.", path=self.id))
        if self.width_gev is not None and self.width_gev < 0:
            issues.append(ValidationIssue("particle.width.negative", "Width cannot be negative.", path=self.id))
        if self.ontology_level is OntologyLevel.FUNDAMENTAL and self.composition:
            issues.append(ValidationIssue("particle.composition.fundamental", "A fundamental entry should not declare physical constituents.", "warning", self.id))
        for item in self.evidence:
            issues.extend(item.validate())
        return issues


@dataclass(frozen=True)
class InteractionLeg:
    particle_id: str
    direction: str
    multiplicity: int = 1

    def signed_multiplicity(self) -> int:
        if self.direction == "in":
            return -self.multiplicity
        if self.direction == "out":
            return self.multiplicity
        raise ValueError(f"Unsupported interaction direction: {self.direction}")


@dataclass(frozen=True)
class InteractionSpec:
    id: str
    name: str
    legs: tuple[InteractionLeg, ...]
    mediator_ids: tuple[str, ...] = ()
    coupling_symbol: str = ""
    operator_dimension: int = 4
    perturbative_order: str = "tree"
    status: EpistemicStatus = EpistemicStatus.ESTABLISHED
    validity: str = ""
    expected_conservation: tuple[str, ...] = ("electric_charge_e",)
    evidence: tuple[EvidenceRef, ...] = ()
    tags: tuple[str, ...] = ()

    def incoming(self) -> tuple[InteractionLeg, ...]:
        return tuple(leg for leg in self.legs if leg.direction == "in")

    def outgoing(self) -> tuple[InteractionLeg, ...]:
        return tuple(leg for leg in self.legs if leg.direction == "out")

    def validate(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not self.id:
            issues.append(ValidationIssue("interaction.id.empty", "Interaction id is required."))
        if not self.incoming() or not self.outgoing():
            issues.append(ValidationIssue("interaction.legs.sides", "Interaction requires incoming and outgoing legs.", path=self.id))
        if self.operator_dimension < 0:
            issues.append(ValidationIssue("interaction.operator_dimension", "Operator dimension must be non-negative.", path=self.id))
        return issues


@dataclass(frozen=True)
class HyperNode:
    id: str
    kind: str
    label: str
    status: EpistemicStatus
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HyperEdge:
    id: str
    relation: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    status: EpistemicStatus
    payload: Mapping[str, Any] = field(default_factory=dict)


class ParticleFieldHypergraph:
    def __init__(self) -> None:
        self.nodes: dict[str, HyperNode] = {}
        self.edges: dict[str, HyperEdge] = {}

    def add_node(self, node: HyperNode) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Duplicate node id: {node.id}")
        self.nodes[node.id] = node

    def upsert_node(self, node: HyperNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: HyperEdge, *, require_nodes: bool = True) -> None:
        if edge.id in self.edges:
            raise ValueError(f"Duplicate edge id: {edge.id}")
        if require_nodes:
            missing = [node for node in (*edge.sources, *edge.targets) if node not in self.nodes]
            if missing:
                raise KeyError(f"Unknown nodes for edge {edge.id}: {missing}")
        self.edges[edge.id] = edge

    def neighborhood(self, node_id: str) -> dict[str, list[str]]:
        incoming: list[str] = []
        outgoing: list[str] = []
        for edge in self.edges.values():
            if node_id in edge.targets:
                incoming.append(edge.id)
            if node_id in edge.sources:
                outgoing.append(edge.id)
        return {"incoming": sorted(incoming), "outgoing": sorted(outgoing)}

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [asdict(self.nodes[key]) for key in sorted(self.nodes)],
            "hyperedges": [asdict(self.edges[key]) for key in sorted(self.edges)],
        }

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()

    def to_graphml(self) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '<graph id="omega_pct" edgedefault="directed">',
        ]
        for node in sorted(self.nodes.values(), key=lambda item: item.id):
            label = _xml_escape(node.label)
            lines.append(f'<node id="{_xml_escape(node.id)}"><data key="label">{label}</data><data key="kind">{_xml_escape(node.kind)}</data></node>')
        for edge in sorted(self.edges.values(), key=lambda item: item.id):
            junction = f"hyperedge::{edge.id}"
            lines.append(f'<node id="{_xml_escape(junction)}"><data key="kind">hyperedge</data><data key="label">{_xml_escape(edge.relation)}</data></node>')
            for index, source in enumerate(edge.sources):
                lines.append(f'<edge id="{_xml_escape(edge.id)}::in::{index}" source="{_xml_escape(source)}" target="{_xml_escape(junction)}"/>')
            for index, target in enumerate(edge.targets):
                lines.append(f'<edge id="{_xml_escape(edge.id)}::out::{index}" source="{_xml_escape(junction)}" target="{_xml_escape(target)}"/>')
        lines.extend(["</graph>", "</graphml>"])
        return "\n".join(lines) + "\n"


def _xml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


class ModelRegistry:
    def __init__(self) -> None:
        self.fields: dict[str, FieldSpec] = {}
        self.particles: dict[str, ParticleSpec] = {}
        self.interactions: dict[str, InteractionSpec] = {}
        self.evidence: dict[str, EvidenceRef] = {}

    def add_field(self, value: FieldSpec) -> None:
        _insert_unique(self.fields, value.id, value)

    def add_particle(self, value: ParticleSpec) -> None:
        _insert_unique(self.particles, value.id, value)

    def add_interaction(self, value: InteractionSpec) -> None:
        _insert_unique(self.interactions, value.id, value)

    def add_evidence(self, value: EvidenceRef) -> None:
        _insert_unique(self.evidence, value.identifier, value)

    def validate(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for value in self.fields.values():
            issues.extend(value.validate())
        for value in self.particles.values():
            issues.extend(value.validate())
            for field_id in value.field_ids:
                if field_id not in self.fields:
                    issues.append(ValidationIssue("particle.field.missing", f"Particle {value.id} references unknown field {field_id}.", path=value.id))
            if value.antiparticle_id and value.antiparticle_id not in self.particles:
                issues.append(ValidationIssue("particle.antiparticle.missing", f"Unknown antiparticle {value.antiparticle_id}.", path=value.id))
        for value in self.interactions.values():
            issues.extend(value.validate())
            for leg in value.legs:
                if leg.particle_id not in self.particles:
                    issues.append(ValidationIssue("interaction.particle.missing", f"Interaction {value.id} references unknown particle {leg.particle_id}.", path=value.id))
            for mediator in value.mediator_ids:
                if mediator not in self.particles and mediator not in self.fields:
                    issues.append(ValidationIssue("interaction.mediator.missing", f"Unknown mediator {mediator}.", path=value.id))
        return issues

    def interaction_balance(self, interaction_id: str) -> dict[str, float]:
        interaction = self.interactions[interaction_id]
        balance: dict[str, float] = {}
        for leg in interaction.legs:
            particle = self.particles[leg.particle_id]
            sign = leg.signed_multiplicity()
            for key, value in particle.quantum_numbers.additive_vector().items():
                balance[key] = balance.get(key, 0.0) + sign * value
        return {key: value for key, value in sorted(balance.items()) if abs(value) > 1e-12}

    def build_hypergraph(self) -> ParticleFieldHypergraph:
        graph = ParticleFieldHypergraph()
        for value in self.fields.values():
            graph.add_node(HyperNode(value.id, "field", value.name, value.status, {"symbol": value.symbol, "ontology": value.ontology_level.value}))
        for value in self.particles.values():
            graph.add_node(HyperNode(value.id, "particle", value.name, value.status, {"symbol": value.symbol, "ontology": value.ontology_level.value}))
            for field_id in value.field_ids:
                graph.add_edge(HyperEdge(f"excitation::{field_id}::{value.id}", "excitation_of", (field_id,), (value.id,), value.status))
            component_counts: dict[str, int] = {}
            for component in value.composition:
                if component in graph.nodes:
                    occurrence = component_counts.get(component, 0)
                    component_counts[component] = occurrence + 1
                    graph.add_edge(HyperEdge(
                        f"component::{component}::{value.id}::{occurrence}",
                        "component_of",
                        (component,),
                        (value.id,),
                        value.status,
                        {"occurrence": occurrence, "multiplicity": value.composition.count(component)},
                    ))
        for value in self.interactions.values():
            graph.add_edge(HyperEdge(value.id, "interaction", tuple(leg.particle_id for leg in value.incoming()), tuple(leg.particle_id for leg in value.outgoing()), value.status, {"mediators": list(value.mediator_ids), "coupling": value.coupling_symbol}))
        return graph

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": [_dataclass_to_json(self.fields[key]) for key in sorted(self.fields)],
            "particles": [_dataclass_to_json(self.particles[key]) for key in sorted(self.particles)],
            "interactions": [_dataclass_to_json(self.interactions[key]) for key in sorted(self.interactions)],
            "evidence": [_dataclass_to_json(self.evidence[key]) for key in sorted(self.evidence)],
        }

    @classmethod
    def from_catalog(cls, path: str | Path) -> "ModelRegistry":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        registry = cls()
        evidence_by_id: dict[str, EvidenceRef] = {}
        for item in raw.get("evidence", []):
            ref = EvidenceRef(
                identifier=item["identifier"], title=item["title"], source_type=item["source_type"],
                locator=item.get("locator", ""), status=EpistemicStatus(item.get("status", "unknown")), notes=item.get("notes", ""),
            )
            registry.add_evidence(ref)
            evidence_by_id[ref.identifier] = ref
        def refs(ids: Sequence[str]) -> tuple[EvidenceRef, ...]:
            return tuple(evidence_by_id[item] for item in ids if item in evidence_by_id)
        for item in raw.get("fields", []):
            registry.add_field(FieldSpec(
                id=item["id"], name=item["name"], symbol=item["symbol"], spin_class=SpinClass(item["spin_class"]),
                lorentz_representation=item["lorentz_representation"], gauge_representations=item.get("gauge_representations", {}),
                mass_dimension=float(item["mass_dimension"]), ontology_level=OntologyLevel(item.get("ontology_level", "fundamental")),
                status=EpistemicStatus(item.get("status", "established")), description=item.get("description", ""),
                evidence=refs(item.get("evidence_ids", [])), tags=tuple(item.get("tags", [])),
            ))
        for item in raw.get("particles", []):
            qn = item.get("quantum_numbers", {})
            registry.add_particle(ParticleSpec(
                id=item["id"], name=item["name"], symbol=item["symbol"], field_ids=tuple(item.get("field_ids", [])),
                ontology_level=OntologyLevel(item["ontology_level"]), spin=item.get("spin"), spin_class=SpinClass(item["spin_class"]),
                quantum_numbers=QuantumNumbers(
                    electric_charge_e=float(qn.get("electric_charge_e", 0.0)), baryon_number=float(qn.get("baryon_number", 0.0)),
                    lepton_numbers=qn.get("lepton_numbers", {}), color_representation=qn.get("color_representation", "1"),
                    weak_isospin=qn.get("weak_isospin"), weak_hypercharge=qn.get("weak_hypercharge"), parity=qn.get("parity"),
                    c_parity=qn.get("c_parity"), cp=qn.get("cp"),
                ),
                antiparticle_id=item.get("antiparticle_id"), mass_gev=item.get("mass_gev"), width_gev=item.get("width_gev"),
                stable_in_vacuum=item.get("stable_in_vacuum"), composition=tuple(item.get("composition", [])),
                dispersion_relation=item.get("dispersion_relation", "E^2=p^2+m^2"), status=EpistemicStatus(item.get("status", "established")),
                confidence=float(item.get("confidence", 1.0)), scale_min_gev=item.get("scale_min_gev"), scale_max_gev=item.get("scale_max_gev"),
                evidence=refs(item.get("evidence_ids", [])), tags=tuple(item.get("tags", [])), notes=item.get("notes", ""),
            ))
        for item in raw.get("interactions", []):
            registry.add_interaction(InteractionSpec(
                id=item["id"], name=item["name"], legs=tuple(InteractionLeg(**leg) for leg in item["legs"]),
                mediator_ids=tuple(item.get("mediator_ids", [])), coupling_symbol=item.get("coupling_symbol", ""),
                operator_dimension=int(item.get("operator_dimension", 4)), perturbative_order=item.get("perturbative_order", "tree"),
                status=EpistemicStatus(item.get("status", "established")), validity=item.get("validity", ""),
                expected_conservation=tuple(item.get("expected_conservation", ["electric_charge_e"])),
                evidence=refs(item.get("evidence_ids", [])), tags=tuple(item.get("tags", [])),
            ))
        return registry


def _insert_unique(mapping: dict[str, Any], key: str, value: Any) -> None:
    if key in mapping:
        raise ValueError(f"Duplicate registry id: {key}")
    mapping[key] = value


def _dataclass_to_json(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: _dataclass_to_json(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _dataclass_to_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_dataclass_to_json(item) for item in value]
    return value


@dataclass(frozen=True)
class DimensionVector:
    mass: int = 0
    length: int = 0
    time: int = 0
    charge: int = 0
    temperature: int = 0

    def __add__(self, other: "DimensionVector") -> "DimensionVector":
        return DimensionVector(*(a + b for a, b in zip(self.as_tuple(), other.as_tuple())))

    def __sub__(self, other: "DimensionVector") -> "DimensionVector":
        return DimensionVector(*(a - b for a, b in zip(self.as_tuple(), other.as_tuple())))

    def scaled(self, factor: int) -> "DimensionVector":
        return DimensionVector(*(factor * value for value in self.as_tuple()))

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        return (self.mass, self.length, self.time, self.charge, self.temperature)

    @property
    def dimensionless(self) -> bool:
        return self.as_tuple() == (0, 0, 0, 0, 0)


@dataclass(frozen=True)
class SymbolicTerm:
    coefficient: str
    factors: Mapping[str, int]
    dimension: DimensionVector
    hermitian_partner: str | None = None
    status: EpistemicStatus = EpistemicStatus.PARAMETRIZATION


@dataclass(frozen=True)
class LagrangianModel:
    id: str
    fields: tuple[str, ...]
    symmetries: tuple[str, ...]
    terms: tuple[SymbolicTerm, ...]
    cutoff_gev: float | None = None
    status: EpistemicStatus = EpistemicStatus.PARAMETRIZATION

    def validate_dimensions(self, target: DimensionVector) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for index, term in enumerate(self.terms):
            if term.dimension != target:
                issues.append(ValidationIssue("lagrangian.dimension.mismatch", f"Term {index} has dimension {term.dimension.as_tuple()}, expected {target.as_tuple()}.", path=f"{self.id}.terms[{index}]"))
        return issues

    def effective_orders(self) -> list[int]:
        return [term.dimension.mass for term in self.terms]


class JsonlLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: Mapping[str, Any]) -> str:
        canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = sha256(canonical.encode("utf-8")).hexdigest()
        envelope = {"sha256": digest, "record": record}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n")
        return digest

    def verify(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not self.path.exists():
            return issues
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                envelope = json.loads(line)
                canonical = json.dumps(envelope["record"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                digest = sha256(canonical.encode("utf-8")).hexdigest()
                if digest != envelope.get("sha256"):
                    issues.append(ValidationIssue("ledger.digest.mismatch", "Ledger record digest mismatch.", path=f"{self.path}:{line_number}"))
        return issues
