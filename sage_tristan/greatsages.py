"""AIT-GreatSages: chronological, source-aware sage reconstruction engine.

R0.1 uses Carl Friedrich Gauss as the first executable seed.  The engine does
not impersonate a historical person and does not certify historical truth.  It
builds auditable knowledge snapshots, guards against chronological leakage,
compiles discovery dependencies, generates explicit mirror families, and can
hand a snapshot-specific mission to the existing AIT-PANTHEON-OMEGA engine.

The generic data model is intentionally sage-agnostic so later releases can
zoom out from Gauss to a much larger historical pantheon without rewriting the
runtime.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
import json
from typing import Iterable, Sequence

from omega_histosci_hg_t.graph import HistoricalHypergraph
from omega_histosci_hg_t.models import (
    EdgeKind,
    EpistemicStatus,
    HistoricalHyperedge,
    HistoricalNode,
    NodeKind,
    TemporalLayer,
)
from sage_tristan.ait_pantheon import run_ait_cycle


class ClaimClass(str, Enum):
    """Epistemic class used by GreatSages outputs."""

    ESTABLISHED = "established"
    SOURCE_REPORTED = "source_reported"
    RECONSTRUCTION = "reconstruction"
    COUNTERFACTUAL = "counterfactual"
    FERTILE_HYPOTHESIS = "fertile_hypothesis"


class MirrorKind(str, Enum):
    HISTORICAL = "historical"
    MODERN = "modern"
    INVERSE = "inverse"
    COMPUTATIONAL = "computational"
    DOMAIN = "domain"
    TRISTAN = "tristan"
    OAK = "oak"
    FUTURE = "future"


@dataclass(frozen=True, slots=True)
class Source:
    source_id: str
    title: str
    url: str
    source_type: str = "reference"
    note: str = ""


@dataclass(frozen=True, slots=True)
class KnowledgeAtom:
    atom_id: str
    label: str
    available_from_year: int
    domains: tuple[str, ...]
    claim_class: ClaimClass = ClaimClass.SOURCE_REPORTED
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Discovery:
    discovery_id: str
    year: int
    title: str
    problem: str
    compressed_invariant: str
    representations: tuple[str, ...]
    prerequisite_ids: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    claim_class: ClaimClass = ClaimClass.SOURCE_REPORTED


@dataclass(frozen=True, slots=True)
class SageProfile:
    sage_id: str
    canonical_name: str
    birth_year: int
    death_year: int
    sources: tuple[Source, ...]
    knowledge: tuple[KnowledgeAtom, ...]
    discoveries: tuple[Discovery, ...]
    cognitive_operators: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Snapshot:
    sage_id: str
    year: int
    available_atom_ids: tuple[str, ...]
    blocked_atom_ids: tuple[str, ...]
    available_discovery_ids: tuple[str, ...]
    blocked_discovery_ids: tuple[str, ...]
    leakage_free: bool


@dataclass(frozen=True, slots=True)
class ReplayCard:
    discovery_id: str
    year: int
    allowed_atom_ids: tuple[str, ...]
    blocked_future_atom_ids: tuple[str, ...]
    prerequisite_ids: tuple[str, ...]
    prerequisites_available: bool
    target_withheld: bool
    claim_class: ClaimClass = ClaimClass.RECONSTRUCTION


@dataclass(frozen=True, slots=True)
class MirrorCard:
    discovery_id: str
    mirror_kind: MirrorKind
    prompt: str
    claim_class: ClaimClass


GAUSS_SOURCES: tuple[Source, ...] = (
    Source(
        "gauss_bio_goettingen",
        "Carl Friedrich Gauss biography / chronology — Gauss Society Goettingen",
        "https://www.gauss-gesellschaft-goettingen.de/gaussbio.html",
        note="Chronology reference; individual claims still require source-level audit.",
    ),
    Source(
        "gauss_chronology_utk",
        "C. F. Gauss chronology",
        "https://web.math.utk.edu/~freire/m400su06/C.F.%20Gauss%20chronology.pdf",
        note="Secondary chronology reference used only as a seed, not as a truth oracle.",
    ),
)


GAUSS_KNOWLEDGE: tuple[KnowledgeAtom, ...] = (
    KnowledgeAtom("symmetry_pairing", "Symmetry can compress repeated arithmetic work", 1787, ("arithmetic",)),
    KnowledgeAtom("prime_density_interest", "Empirical study of prime-number frequency", 1792, ("number_theory",), source_ids=("gauss_bio_goettingen",)),
    KnowledgeAtom("cyclotomy_seed", "Division of the circle and roots of unity as linked representations", 1796, ("number_theory", "geometry", "algebra"), source_ids=("gauss_bio_goettingen",)),
    KnowledgeAtom("congruence_language", "Congruence notation and arithmetic modulo an integer", 1801, ("number_theory",), source_ids=("gauss_chronology_utk",)),
    KnowledgeAtom("quadratic_forms", "Binary quadratic forms and arithmetic classification", 1801, ("number_theory", "algebra"), source_ids=("gauss_chronology_utk",)),
    KnowledgeAtom("orbit_inference", "Infer an orbit from sparse astronomical observations", 1801, ("astronomy", "inverse_problems"), source_ids=("gauss_bio_goettingen",)),
    KnowledgeAtom("least_squares_public", "Least-squares estimation in published astronomical work", 1809, ("statistics", "astronomy"), source_ids=("gauss_chronology_utk",)),
    KnowledgeAtom("intrinsic_curvature", "Surface curvature can be characterized intrinsically", 1827, ("geometry", "geodesy"), source_ids=("gauss_chronology_utk",)),
    KnowledgeAtom("magnetic_measurement", "Absolute magnetic measurement and field modeling", 1832, ("physics", "metrology"), source_ids=("gauss_bio_goettingen",)),
)


GAUSS_DISCOVERIES: tuple[Discovery, ...] = (
    Discovery(
        "gauss_1796_17gon",
        1796,
        "Constructibility of the regular 17-gon",
        "Determine when a regular polygon can be constructed with straightedge and compass.",
        "Change representation from geometry to algebraic/cyclotomic structure and exploit symmetry.",
        ("geometry", "roots_of_unity", "cyclotomy", "number_theory"),
        domains=("geometry", "number_theory"),
        source_ids=("gauss_bio_goettingen",),
    ),
    Discovery(
        "gauss_1799_fta",
        1799,
        "Doctoral work on the fundamental theorem of algebra",
        "Establish existence of complex roots for nonconstant complex polynomials.",
        "A proof object can be revisited through multiple representations and strengthened over time.",
        ("polynomials", "complex_plane", "proof"),
        domains=("algebra", "analysis"),
        source_ids=("gauss_chronology_utk",),
    ),
    Discovery(
        "gauss_1801_disquisitiones",
        1801,
        "Disquisitiones Arithmeticae",
        "Unify and systematize major parts of arithmetic and number theory.",
        "Introduce reusable structural language so many arithmetic problems become transformations of common invariants.",
        ("congruences", "quadratic_residues", "quadratic_forms", "cyclotomy"),
        prerequisite_ids=("gauss_1796_17gon",),
        domains=("number_theory",),
        source_ids=("gauss_chronology_utk",),
    ),
    Discovery(
        "gauss_1801_ceres",
        1801,
        "Orbit reconstruction for Ceres",
        "Predict a celestial orbit from a short and incomplete observation arc.",
        "Sparse noisy observations can constrain a latent dynamical model strongly enough for prediction.",
        ("observations", "orbital_model", "parameter_estimation", "prediction"),
        domains=("astronomy", "inverse_problems"),
        source_ids=("gauss_bio_goettingen",),
    ),
    Discovery(
        "gauss_1809_theoria_motus",
        1809,
        "Theoria Motus",
        "Determine celestial motion and orbital parameters from observations.",
        "Combine dynamics, estimation and residual minimization into a reproducible inference workflow.",
        ("celestial_mechanics", "least_squares", "estimation"),
        prerequisite_ids=("gauss_1801_ceres",),
        domains=("astronomy", "statistics"),
        source_ids=("gauss_chronology_utk",),
    ),
    Discovery(
        "gauss_1827_surfaces",
        1827,
        "General investigations of curved surfaces",
        "Characterize curved surfaces independently of an embedding-dependent description.",
        "Search for quantities invariant under allowed transformations of representation.",
        ("surface", "metric", "curvature", "intrinsic_geometry"),
        domains=("geometry", "geodesy"),
        source_ids=("gauss_chronology_utk",),
    ),
    Discovery(
        "gauss_1830s_magnetism",
        1832,
        "Magnetic measurement and terrestrial magnetism program",
        "Turn magnetic phenomena into comparable quantitative observations and field models.",
        "Instrument, calibration, units, observation and model form one causal measurement system.",
        ("instrument", "measurement", "units", "field_model"),
        domains=("physics", "metrology"),
        source_ids=("gauss_bio_goettingen",),
    ),
)


GAUSS = SageProfile(
    sage_id="gauss",
    canonical_name="Carl Friedrich Gauss",
    birth_year=1777,
    death_year=1855,
    sources=GAUSS_SOURCES,
    knowledge=GAUSS_KNOWLEDGE,
    discoveries=GAUSS_DISCOVERIES,
    cognitive_operators=(
        "symmetry_compression",
        "representation_switch",
        "invariant_search",
        "generalization",
        "approximation_and_residuals",
        "measurement_model_loop",
        "proof_revision",
    ),
)


MIRROR_PROMPTS: dict[MirrorKind, str] = {
    MirrorKind.HISTORICAL: "Reconstruct the problem using only knowledge available by {year}; separate documented history from reconstruction.",
    MirrorKind.MODERN: "Translate the invariant into modern notation, theory and standard terminology without claiming novelty.",
    MirrorKind.INVERSE: "Start from the result and infer minimal natural problems/evidence that could motivate its discovery.",
    MirrorKind.COMPUTATIONAL: "Compile the invariant into an executable algorithm, benchmark and reproducible test.",
    MirrorKind.DOMAIN: "Search other domains for problems with the same abstract problem DNA and state the analogy limits.",
    MirrorKind.TRISTAN: "Map the invariant through HGFM + CVCD + LOG/EXP + OAK + Bayes-Tristan and propose falsifiable descendants.",
    MirrorKind.OAK: "Attack chronology, attribution, assumptions, counterexamples, leakage, hype and unsupported novelty claims.",
    MirrorKind.FUTURE: "Explore 2026-era extensions with modern tools; mark every counterfactual or speculative claim explicitly.",
}


def get_profile(sage_id: str) -> SageProfile:
    if sage_id.lower() == "gauss":
        return GAUSS
    raise KeyError(f"unknown sage_id: {sage_id}")


def knowledge_snapshot(profile: SageProfile, year: int) -> Snapshot:
    if year < profile.birth_year or year > profile.death_year:
        raise ValueError(f"year must be inside {profile.birth_year}..{profile.death_year}")
    available_atoms = tuple(sorted(atom.atom_id for atom in profile.knowledge if atom.available_from_year <= year))
    blocked_atoms = tuple(sorted(atom.atom_id for atom in profile.knowledge if atom.available_from_year > year))
    available_discoveries = tuple(sorted(item.discovery_id for item in profile.discoveries if item.year <= year))
    blocked_discoveries = tuple(sorted(item.discovery_id for item in profile.discoveries if item.year > year))
    return Snapshot(
        sage_id=profile.sage_id,
        year=year,
        available_atom_ids=available_atoms,
        blocked_atom_ids=blocked_atoms,
        available_discovery_ids=available_discoveries,
        blocked_discovery_ids=blocked_discoveries,
        leakage_free=not (set(available_atoms) & set(blocked_atoms)) and not (set(available_discoveries) & set(blocked_discoveries)),
    )


def discovery_by_id(profile: SageProfile, discovery_id: str) -> Discovery:
    for item in profile.discoveries:
        if item.discovery_id == discovery_id:
            return item
    raise KeyError(discovery_id)


def replay_card(profile: SageProfile, discovery_id: str) -> ReplayCard:
    target = discovery_by_id(profile, discovery_id)
    # Replay snapshot is taken immediately before the target discovery year so
    # the target itself cannot leak into the allowed discovery set.
    gate_year = max(profile.birth_year, target.year - 1)
    snapshot = knowledge_snapshot(profile, gate_year)
    available_prerequisites = set(snapshot.available_discovery_ids)
    return ReplayCard(
        discovery_id=target.discovery_id,
        year=target.year,
        allowed_atom_ids=snapshot.available_atom_ids,
        blocked_future_atom_ids=snapshot.blocked_atom_ids,
        prerequisite_ids=target.prerequisite_ids,
        prerequisites_available=set(target.prerequisite_ids) <= available_prerequisites,
        target_withheld=target.discovery_id not in snapshot.available_discovery_ids,
    )


def mirrors(profile: SageProfile, discovery_id: str) -> tuple[MirrorCard, ...]:
    target = discovery_by_id(profile, discovery_id)
    cards = []
    for kind in MirrorKind:
        claim_class = ClaimClass.RECONSTRUCTION
        if kind is MirrorKind.FUTURE:
            claim_class = ClaimClass.COUNTERFACTUAL
        elif kind is MirrorKind.TRISTAN:
            claim_class = ClaimClass.FERTILE_HYPOTHESIS
        cards.append(
            MirrorCard(
                discovery_id=discovery_id,
                mirror_kind=kind,
                prompt=MIRROR_PROMPTS[kind].format(year=target.year),
                claim_class=claim_class,
            )
        )
    return tuple(cards)


def dependency_layers(profile: SageProfile) -> tuple[tuple[str, ...], ...]:
    """Return a deterministic topological layering of the discovery DAG."""
    remaining = {item.discovery_id: set(item.prerequisite_ids) for item in profile.discoveries}
    known = set(remaining)
    unknown = sorted({dep for deps in remaining.values() for dep in deps if dep not in known})
    if unknown:
        raise ValueError(f"unknown discovery prerequisites: {unknown}")
    layers: list[tuple[str, ...]] = []
    emitted: set[str] = set()
    while remaining:
        ready = tuple(sorted(node for node, deps in remaining.items() if deps <= emitted))
        if not ready:
            raise ValueError("discovery dependency graph contains a cycle")
        layers.append(ready)
        for node in ready:
            remaining.pop(node)
        emitted.update(ready)
    return tuple(layers)


def to_histoscience_graph(profile: SageProfile) -> HistoricalHypergraph:
    """Compile a GreatSage profile into the existing Histoscience HG runtime."""
    graph = HistoricalHypergraph()
    graph.add_node(
        HistoricalNode(
            node_id=f"sage::{profile.sage_id}",
            label=profile.canonical_name,
            kind=NodeKind.PERSON,
            status=EpistemicStatus.SOURCE_REPORTED,
            temporal_layers=(TemporalLayer.EXPERIMENTAL_MATHEMATIZED, TemporalLayer.INDUSTRIALIZED_SCIENCE),
            tags=("greatsage", profile.sage_id),
        )
    )
    for source in profile.sources:
        graph.add_node(
            HistoricalNode(
                node_id=f"source::{source.source_id}",
                label=source.title,
                kind=NodeKind.SOURCE,
                status=EpistemicStatus.SOURCE_REPORTED,
                tags=("greatsage_source",),
                metadata={"url": source.url, "source_type": source.source_type, "note": source.note},
            )
        )
    for discovery in profile.discoveries:
        node_id = f"discovery::{discovery.discovery_id}"
        graph.add_node(
            HistoricalNode(
                node_id=node_id,
                label=discovery.title,
                kind=NodeKind.EVENT,
                status=EpistemicStatus.SOURCE_REPORTED,
                descriptions=(discovery.problem, discovery.compressed_invariant),
                source_ids=discovery.source_ids,
                tags=("greatsage_discovery", *discovery.domains),
                metadata={"year": discovery.year, "representations": discovery.representations},
            )
        )
        graph.add_edge(
            HistoricalHyperedge(
                edge_id=f"actor::{profile.sage_id}::{discovery.discovery_id}",
                kind=EdgeKind.FORMALIZED_BY,
                source_node_ids=(node_id,),
                target_node_ids=(f"sage::{profile.sage_id}",),
                status=EpistemicStatus.SOURCE_REPORTED,
                source_ids=discovery.source_ids,
                valid_from_year=discovery.year,
                valid_to_year=discovery.year,
                rationale="GreatSages seed attribution; source audit remains required.",
            )
        )
        for source_id in discovery.source_ids:
            graph.add_edge(
                HistoricalHyperedge(
                    edge_id=f"doc::{discovery.discovery_id}::{source_id}",
                    kind=EdgeKind.DOCUMENTED_BY,
                    source_node_ids=(node_id,),
                    target_node_ids=(f"source::{source_id}",),
                    status=EpistemicStatus.SOURCE_REPORTED,
                    source_ids=(source_id,),
                )
            )
    for discovery in profile.discoveries:
        for prerequisite in discovery.prerequisite_ids:
            graph.add_edge(
                HistoricalHyperedge(
                    edge_id=f"precursor::{prerequisite}::{discovery.discovery_id}",
                    kind=EdgeKind.PRECURSOR,
                    source_node_ids=(f"discovery::{prerequisite}",),
                    target_node_ids=(f"discovery::{discovery.discovery_id}",),
                    status=EpistemicStatus.SOURCE_REPORTED,
                    rationale="Explicit GreatSages dependency used for replay; not a claim of unique historical causation.",
                )
            )
    return graph


def pantheon_cycle(profile: SageProfile, year: int, *, cycles: int = 1, salt: str = "greatsages") -> dict[str, object]:
    snapshot = knowledge_snapshot(profile, year)
    mission = (
        f"AIT-GreatSages {profile.canonical_name} @ {year}: reason only from allowed historical snapshot; "
        "generate mirrors, tests and OAK attacks without chronological leakage or novelty inflation. "
        f"Available atoms={','.join(snapshot.available_atom_ids) or 'none'}; "
        f"available discoveries={','.join(snapshot.available_discovery_ids) or 'none'}."
    )
    return run_ait_cycle(mission, cycles=cycles, salt=salt)


def compile_report(profile: SageProfile, year: int) -> dict[str, object]:
    snapshot = knowledge_snapshot(profile, year)
    graph_audit = to_histoscience_graph(profile).audit()
    return {
        "engine": "AIT-GreatSages",
        "release": "R0.1",
        "sage": profile.canonical_name,
        "sage_id": profile.sage_id,
        "year": year,
        "snapshot": asdict(snapshot),
        "dependency_layers": dependency_layers(profile),
        "cognitive_operators": profile.cognitive_operators,
        "discovery_count": len(profile.discoveries),
        "mirror_kinds": tuple(kind.value for kind in MirrorKind),
        "histoscience_graph": asdict(graph_audit),
        "historical_truth_certified": False,
        "historical_impersonation_claimed": False,
        "counterfactuals_are_history": False,
        "oak_note": "Source-backed history, reconstruction, counterfactuals and Tristan hypotheses must remain explicitly separated.",
    }


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="AIT-GreatSages chronological reconstruction and mirror compiler")
    parser.add_argument("--sage", default="gauss")
    parser.add_argument("--year", type=int, default=1801)
    parser.add_argument("--discovery")
    parser.add_argument("--pantheon", action="store_true", help="also run the existing AIT-PANTHEON cycle on the gated snapshot")
    parser.add_argument("--cycles", type=int, default=1)
    args = parser.parse_args(argv)

    profile = get_profile(args.sage)
    payload: dict[str, object] = {"report": compile_report(profile, args.year)}
    if args.discovery:
        payload["replay"] = asdict(replay_card(profile, args.discovery))
        payload["mirrors"] = [asdict(card) for card in mirrors(profile, args.discovery)]
    if args.pantheon:
        payload["pantheon"] = pantheon_cycle(profile, args.year, cycles=args.cycles)
    print(json.dumps(_jsonable(payload), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
