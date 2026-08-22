"""Ω-GREATSAGES-POLYCENTRIC-T∞ — strict access/provenance kernel.

This module prepares GreatSages for a civilization-scale dezoom without
collapsing human intellectual history into a single timeline or ranking.

Core rule:

    knowledge existing in the world != knowledge accessible to an actor

Access must therefore be represented by an explicit, source-auditable edge.
Missing access evidence remains UNKNOWN; it is never inferred from world
existence alone.  Persons, collectives, schools, institutions, traditions,
networks and anonymous communities are first-class carriers.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
import json
from typing import Iterable, Sequence

from sage_tristan.greatsages import ClaimClass


class ActorKind(str, Enum):
    PERSON = "person"
    COLLECTIVE = "collective"
    SCHOOL = "school"
    INSTITUTION = "institution"
    TRADITION = "tradition"
    CIVILIZATION = "civilization"
    NETWORK = "network"
    ANONYMOUS_COMMUNITY = "anonymous_community"


class AccessDecision(str, Enum):
    ALLOWED = "allowed"
    BLOCKED_FUTURE = "blocked_future"
    UNKNOWN_ACCESS = "unknown_access"
    BLOCKED_LANGUAGE = "blocked_language"
    BLOCKED_TRANSLATION = "blocked_translation"


class AttributionRole(str, Enum):
    FIRST_KNOWN_EVIDENCE = "first_known_evidence"
    INDEPENDENT_DISCOVERY = "independent_discovery"
    PUBLICATION = "publication"
    FORMALIZATION = "formalization"
    POPULARIZATION = "popularization"
    PRESERVATION = "preservation"
    TRANSLATION = "translation"
    INSTRUMENTAL_ENABLEMENT = "instrumental_enablement"


@dataclass(frozen=True, slots=True)
class KnowledgeActor:
    actor_id: str
    label: str
    kind: ActorKind
    active_from_year: int | None = None
    active_to_year: int | None = None
    languages: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PolycentricKnowledgeAtom:
    atom_id: str
    label: str
    world_from_year: int
    domains: tuple[str, ...]
    source_ids: tuple[str, ...] = ()
    claim_class: ClaimClass = ClaimClass.SOURCE_REPORTED


@dataclass(frozen=True, slots=True)
class AccessibilityEdge:
    edge_id: str
    actor_id: str
    atom_id: str
    accessible_from_year: int
    language: str | None = None
    translation_bridge_id: str | None = None
    directness: float = 0.5
    certainty: float = 0.5
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.directness <= 1.0:
            raise ValueError("directness must be between 0 and 1")
        if not 0.0 <= self.certainty <= 1.0:
            raise ValueError("certainty must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class TranslationLossTensor:
    lexical_loss: float
    semantic_ambiguity: float
    notation_shift: float
    context_loss: float

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    @property
    def aggregate_loss(self) -> float:
        return round(
            0.20 * self.lexical_loss
            + 0.35 * self.semantic_ambiguity
            + 0.20 * self.notation_shift
            + 0.25 * self.context_loss,
            6,
        )


@dataclass(frozen=True, slots=True)
class TranslationBridge:
    bridge_id: str
    source_language: str
    target_language: str
    available_from_year: int
    loss: TranslationLossTensor
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AttributionFacet:
    facet_id: str
    atom_id: str
    actor_id: str
    role: AttributionRole
    year: int | None = None
    certainty: float = 0.5
    source_ids: tuple[str, ...] = ()
    note: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.certainty <= 1.0:
            raise ValueError("certainty must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class CivilizationZoomTensor:
    time: int | None = None
    actor_ids: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    attribution_roles: tuple[AttributionRole, ...] = ()


@dataclass(frozen=True, slots=True)
class AccessReceipt:
    actor_id: str
    atom_id: str
    year: int
    decision: AccessDecision
    matched_edge_ids: tuple[str, ...]
    evidence_score: float
    translation_loss: float | None
    world_existence_implies_access: bool = False


@dataclass(frozen=True, slots=True)
class PolycentricAtlas:
    actors: tuple[KnowledgeActor, ...]
    atoms: tuple[PolycentricKnowledgeAtom, ...]
    access_edges: tuple[AccessibilityEdge, ...]
    translations: tuple[TranslationBridge, ...] = ()
    attributions: tuple[AttributionFacet, ...] = ()

    def __post_init__(self) -> None:
        actor_ids = [item.actor_id for item in self.actors]
        atom_ids = [item.atom_id for item in self.atoms]
        edge_ids = [item.edge_id for item in self.access_edges]
        bridge_ids = [item.bridge_id for item in self.translations]
        facet_ids = [item.facet_id for item in self.attributions]
        for name, values in (
            ("actor", actor_ids),
            ("atom", atom_ids),
            ("edge", edge_ids),
            ("translation", bridge_ids),
            ("facet", facet_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {name} id")
        known_actors = set(actor_ids)
        known_atoms = set(atom_ids)
        known_bridges = set(bridge_ids)
        for edge in self.access_edges:
            if edge.actor_id not in known_actors or edge.atom_id not in known_atoms:
                raise ValueError("access edge references unknown actor/atom")
            if edge.translation_bridge_id and edge.translation_bridge_id not in known_bridges:
                raise ValueError("access edge references unknown translation bridge")
        for facet in self.attributions:
            if facet.actor_id not in known_actors or facet.atom_id not in known_atoms:
                raise ValueError("attribution facet references unknown actor/atom")

    def actor(self, actor_id: str) -> KnowledgeActor:
        for item in self.actors:
            if item.actor_id == actor_id:
                return item
        raise KeyError(actor_id)

    def atom(self, atom_id: str) -> PolycentricKnowledgeAtom:
        for item in self.atoms:
            if item.atom_id == atom_id:
                return item
        raise KeyError(atom_id)

    def translation(self, bridge_id: str) -> TranslationBridge:
        for item in self.translations:
            if item.bridge_id == bridge_id:
                return item
        raise KeyError(bridge_id)

    def access(self, actor_id: str, atom_id: str, year: int) -> AccessReceipt:
        actor = self.actor(actor_id)
        atom = self.atom(atom_id)
        if atom.world_from_year > year:
            return AccessReceipt(actor_id, atom_id, year, AccessDecision.BLOCKED_FUTURE, (), 0.0, None)

        candidates = tuple(
            edge
            for edge in self.access_edges
            if edge.actor_id == actor_id and edge.atom_id == atom_id and edge.accessible_from_year <= year
        )
        if not candidates:
            return AccessReceipt(actor_id, atom_id, year, AccessDecision.UNKNOWN_ACCESS, (), 0.0, None)

        admissible: list[tuple[AccessibilityEdge, float | None]] = []
        language_blocked = False
        translation_blocked = False
        for edge in candidates:
            loss: float | None = None
            if edge.language and actor.languages and edge.language not in actor.languages:
                if edge.translation_bridge_id is None:
                    language_blocked = True
                    continue
                bridge = self.translation(edge.translation_bridge_id)
                if bridge.available_from_year > year or bridge.target_language not in actor.languages:
                    translation_blocked = True
                    continue
                loss = bridge.loss.aggregate_loss
            admissible.append((edge, loss))

        if not admissible:
            decision = AccessDecision.BLOCKED_TRANSLATION if translation_blocked else AccessDecision.BLOCKED_LANGUAGE
            return AccessReceipt(actor_id, atom_id, year, decision, (), 0.0, None)

        matched_ids = tuple(sorted(edge.edge_id for edge, _ in admissible))
        evidence = max(edge.directness * edge.certainty for edge, _ in admissible)
        losses = [loss for _, loss in admissible if loss is not None]
        translation_loss = min(losses) if losses else None
        return AccessReceipt(
            actor_id,
            atom_id,
            year,
            AccessDecision.ALLOWED,
            matched_ids,
            round(evidence, 6),
            translation_loss,
        )

    def attribution_parallax(self, atom_id: str) -> tuple[AttributionFacet, ...]:
        self.atom(atom_id)
        return tuple(
            sorted(
                (facet for facet in self.attributions if facet.atom_id == atom_id),
                key=lambda item: (item.role.value, item.year if item.year is not None else 10**9, item.actor_id),
            )
        )

    def zoom(self, tensor: CivilizationZoomTensor) -> dict[str, tuple[str, ...]]:
        selected_actors = []
        for actor in self.actors:
            if tensor.actor_ids and actor.actor_id not in set(tensor.actor_ids):
                continue
            if tensor.regions and not set(actor.regions) & set(tensor.regions):
                continue
            if tensor.languages and not set(actor.languages) & set(tensor.languages):
                continue
            if tensor.time is not None:
                if actor.active_from_year is not None and actor.active_from_year > tensor.time:
                    continue
                if actor.active_to_year is not None and actor.active_to_year < tensor.time:
                    continue
            selected_actors.append(actor.actor_id)

        selected_atoms = []
        for atom in self.atoms:
            if tensor.time is not None and atom.world_from_year > tensor.time:
                continue
            if tensor.domains and not set(atom.domains) & set(tensor.domains):
                continue
            selected_atoms.append(atom.atom_id)

        selected_facets = []
        for facet in self.attributions:
            if facet.actor_id not in set(selected_actors) or facet.atom_id not in set(selected_atoms):
                continue
            if tensor.attribution_roles and facet.role not in set(tensor.attribution_roles):
                continue
            selected_facets.append(facet.facet_id)

        return {
            "actor_ids": tuple(sorted(selected_actors)),
            "atom_ids": tuple(sorted(selected_atoms)),
            "attribution_facet_ids": tuple(sorted(selected_facets)),
        }


def software_fixture() -> PolycentricAtlas:
    """Synthetic fixture only; labels deliberately avoid historical claims."""
    actors = (
        KnowledgeActor("fixture_person_a", "Fixture Person A", ActorKind.PERSON, 100, 180, ("lang_a",), ("region_a",)),
        KnowledgeActor("fixture_school_b", "Fixture School B", ActorKind.SCHOOL, 120, 220, ("lang_b",), ("region_b",)),
        KnowledgeActor("fixture_network_c", "Fixture Network C", ActorKind.NETWORK, 130, 230, ("lang_b",), ("region_a", "region_b")),
    )
    atoms = (
        PolycentricKnowledgeAtom("fixture_atom_1", "Fixture knowledge 1", 110, ("mathematics",)),
        PolycentricKnowledgeAtom("fixture_atom_2", "Fixture knowledge 2", 150, ("astronomy",)),
    )
    translation = TranslationBridge(
        "fixture_translate_a_b",
        "lang_a",
        "lang_b",
        160,
        TranslationLossTensor(0.1, 0.2, 0.1, 0.3),
    )
    edges = (
        AccessibilityEdge("access_a_1", "fixture_person_a", "fixture_atom_1", 115, "lang_a", directness=0.9, certainty=0.9),
        AccessibilityEdge("access_b_1", "fixture_school_b", "fixture_atom_1", 165, "lang_a", "fixture_translate_a_b", 0.7, 0.8),
        AccessibilityEdge("access_c_2", "fixture_network_c", "fixture_atom_2", 155, "lang_b", directness=0.8, certainty=0.8),
    )
    facets = (
        AttributionFacet("facet_a_first", "fixture_atom_1", "fixture_person_a", AttributionRole.FIRST_KNOWN_EVIDENCE, 115, 0.8),
        AttributionFacet("facet_b_translation", "fixture_atom_1", "fixture_school_b", AttributionRole.TRANSLATION, 165, 0.7),
        AttributionFacet("facet_c_independent", "fixture_atom_2", "fixture_network_c", AttributionRole.INDEPENDENT_DISCOVERY, 155, 0.6),
    )
    return PolycentricAtlas(actors, atoms, edges, (translation,), facets)


def compile_report(atlas: PolycentricAtlas, *, year: int) -> dict[str, object]:
    decisions = []
    for actor in atlas.actors:
        for atom in atlas.atoms:
            decisions.append(asdict(atlas.access(actor.actor_id, atom.atom_id, year)))
    return {
        "engine": "Ω-GREATSAGES-POLYCENTRIC-T∞",
        "release": "R0.3-contract",
        "year": year,
        "actor_kinds": tuple(kind.value for kind in ActorKind),
        "access_decisions": tuple(decisions),
        "world_existence_implies_access": False,
        "culture_or_person_ranking_performed": False,
        "single_line_history_assumed": False,
        "historical_truth_certified": False,
        "oak_note": "Missing access evidence stays UNKNOWN; attribution is multi-facet and translation loss is explicit.",
    }


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="GreatSages polycentric contract kernel")
    parser.add_argument("--year", type=int, default=170)
    args = parser.parse_args(argv)
    print(json.dumps(_jsonable(compile_report(software_fixture(), year=args.year)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
