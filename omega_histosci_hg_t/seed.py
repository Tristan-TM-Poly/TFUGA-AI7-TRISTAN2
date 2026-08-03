"""Deterministic R0.1 seed spanning the principal science families."""
from __future__ import annotations

from itertools import count

from .graph import HistoricalHypergraph
from .models import (
    BranchRecord,
    EdgeKind,
    EpistemicStatus,
    HistoricalHyperedge,
    HistoricalNode,
    NegativeMemoryRecord,
    NodeKind,
    SourceReference,
    TemporalLayer,
)
from .registry import HistoryRegistry


MACRO_BRANCHES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("science.formal", "Sciences formelles", ("formaliser les structures, inférences et calculs",)),
    ("science.physics", "Physique", ("décrire quantitativement matière, énergie, espace et temps",)),
    ("science.chemistry", "Chimie", ("identifier, transformer et expliquer les substances",)),
    ("science.earth_space", "Sciences de la Terre et de l’espace", ("comprendre la Terre, son environnement et le cosmos",)),
    ("science.life", "Sciences de la vie", ("décrire l’organisation, l’évolution et les fonctions du vivant",)),
    ("science.medicine", "Médecine et santé", ("prévenir, comprendre et traiter les atteintes à la santé",)),
    ("science.computing", "Informatique et information", ("représenter, transformer, transmettre et automatiser l’information",)),
    ("science.engineering", "Ingénieries", ("concevoir des systèmes satisfaisant des besoins sous contraintes",)),
    ("science.social", "Sciences humaines, sociales et comportementales", ("comprendre les humains, cultures, institutions et comportements",)),
    ("science.metascience", "Métasciences", ("étudier la production, validation et circulation des connaissances",)),
)

SUBBRANCHES: dict[str, tuple[tuple[str, str], ...]] = {
    "science.formal": (
        ("mathematics.number_theory", "Arithmétique et théorie des nombres"),
        ("mathematics.geometry", "Géométrie"),
        ("mathematics.topology", "Topologie"),
        ("mathematics.algebra", "Algèbre"),
        ("mathematics.analysis", "Analyse et calcul"),
        ("mathematics.probability_statistics", "Probabilités et statistique"),
        ("mathematics.discrete", "Mathématiques discrètes"),
        ("mathematics.logic_foundations", "Logique et fondements"),
    ),
    "science.physics": (
        ("physics.mechanics", "Mécanique"),
        ("physics.gravity_relativity", "Gravitation et relativité"),
        ("physics.thermodynamics_statistical", "Thermodynamique et physique statistique"),
        ("physics.electromagnetism", "Électricité et magnétisme"),
        ("physics.optics", "Optique et photonique"),
        ("physics.acoustics", "Acoustique"),
        ("physics.quantum", "Physique quantique"),
        ("physics.amo", "Physique atomique, moléculaire et optique"),
        ("physics.nuclear_particle", "Physique nucléaire et des particules"),
        ("physics.condensed_matter", "Matière condensée et matériaux"),
        ("physics.fluids_plasmas", "Fluides et plasmas"),
    ),
    "science.chemistry": (
        ("chemistry.proto", "Protochimie, alchimie et arts matériels"),
        ("chemistry.analytical", "Chimie analytique"),
        ("chemistry.physical", "Chimie physique"),
        ("chemistry.organic", "Chimie organique"),
        ("chemistry.inorganic", "Chimie inorganique"),
        ("chemistry.biochemistry", "Biochimie"),
        ("chemistry.materials_polymers", "Matériaux et polymères"),
        ("chemistry.computational", "Chimie computationnelle"),
    ),
    "science.earth_space": (
        ("earth_space.astronomy_astrophysics", "Astronomie et astrophysique"),
        ("earth_space.geology", "Géologie"),
        ("earth_space.geophysics", "Géophysique"),
        ("earth_space.meteorology_climate", "Météorologie et climatologie"),
        ("earth_space.oceanography", "Océanographie"),
        ("earth_space.hydrology_cryosphere", "Hydrologie et cryosphère"),
        ("earth_space.environment", "Sciences environnementales"),
    ),
    "science.life": (
        ("life.natural_history_taxonomy", "Histoire naturelle et taxonomie"),
        ("life.evolution", "Évolution"),
        ("life.cell_biology", "Biologie cellulaire"),
        ("life.genetics_genomics", "Génétique et génomique"),
        ("life.molecular_biology", "Biologie moléculaire"),
        ("life.microbiology", "Microbiologie"),
        ("life.immunology", "Immunologie"),
        ("life.physiology", "Physiologie"),
        ("life.development", "Développement et morphogenèse"),
        ("life.neuroscience", "Neurosciences"),
        ("life.ecology", "Écologie"),
        ("life.systems_synthetic", "Biologie des systèmes et synthétique"),
    ),
    "science.medicine": (
        ("medicine.anatomy", "Anatomie"),
        ("medicine.pathology", "Pathologie"),
        ("medicine.infectious_disease", "Infectiologie"),
        ("medicine.surgery", "Chirurgie"),
        ("medicine.pharmacology", "Pharmacologie"),
        ("medicine.epidemiology", "Épidémiologie"),
        ("medicine.public_health", "Santé publique"),
        ("medicine.imaging", "Imagerie médicale"),
        ("medicine.laboratory", "Médecine de laboratoire"),
        ("medicine.psychiatry", "Psychiatrie"),
        ("medicine.rehabilitation", "Réadaptation"),
        ("medicine.nutrition", "Nutrition"),
        ("medicine.personalized", "Médecine personnalisée"),
    ),
    "science.computing": (
        ("computing.algorithms", "Calcul et algorithmes"),
        ("computing.hardware", "Architecture matérielle"),
        ("computing.software", "Langages et génie logiciel"),
        ("computing.systems", "Systèmes informatiques"),
        ("computing.ai", "Intelligence artificielle"),
        ("computing.information_communication", "Information et communication"),
        ("computing.cybersecurity", "Cybersécurité"),
    ),
    "science.engineering": (
        ("engineering.civil", "Génie civil"),
        ("engineering.mechanical", "Génie mécanique"),
        ("engineering.electrical", "Génie électrique"),
        ("engineering.chemical", "Génie chimique"),
        ("engineering.physical", "Génie physique"),
        ("engineering.materials", "Génie des matériaux"),
        ("engineering.computer", "Génie informatique"),
        ("engineering.software", "Génie logiciel"),
        ("engineering.industrial", "Génie industriel"),
        ("engineering.biomedical", "Génie biomédical"),
        ("engineering.environmental", "Génie environnemental"),
        ("engineering.aerospace", "Génie aérospatial"),
        ("engineering.nuclear", "Génie nucléaire"),
        ("engineering.robotics", "Robotique et mécatronique"),
        ("engineering.micro_nano", "Microfabrication et nanotechnologies"),
        ("engineering.photonics", "Génie photonique"),
        ("engineering.energy", "Génie énergétique"),
    ),
    "science.social": (
        ("social.psychology", "Psychologie"),
        ("social.sociology", "Sociologie"),
        ("social.anthropology", "Anthropologie"),
        ("social.economics", "Économie"),
        ("social.political_science", "Science politique"),
        ("social.linguistics", "Linguistique"),
        ("social.human_geography", "Géographie humaine"),
        ("social.education", "Sciences de l’éducation"),
        ("social.history_archaeology", "Histoire et archéologie"),
    ),
    "science.metascience": (
        ("metascience.history_science", "Histoire des sciences"),
        ("metascience.philosophy", "Philosophie des sciences"),
        ("metascience.sociology_science", "Sociologie des sciences"),
        ("metascience.scientometrics", "Scientométrie et bibliométrie"),
        ("metascience.metrology", "Métrologie"),
        ("metascience.methodology", "Méthodologie"),
        ("metascience.ethics_integrity", "Éthique et intégrité scientifique"),
        ("metascience.reproducibility", "Reproductibilité"),
        ("metascience.open_science", "Science ouverte"),
        ("metascience.policy", "Politique scientifique"),
        ("metascience.science_of_science", "Science de la science"),
    ),
}


def build_seed() -> tuple[HistoricalHypergraph, HistoryRegistry]:
    graph = HistoricalHypergraph()
    registry = HistoryRegistry()

    seed_source = SourceReference(
        source_id="source.seed.architecture.r01",
        title="Ω-HISTOSCI-HG-T∞ R0.1 architecture seed",
        source_type="software_fixture",
        authors=("Tristan Tardif-Morency",),
        year=2026,
        language="fr",
        primary_source=True,
        notes="Architecture supplied by the project author; not an independent historical source.",
    )
    registry.add_source(seed_source)

    for branch_id, label, problems in MACRO_BRANCHES:
        registry.add_branch(
            BranchRecord(
                branch_id=branch_id,
                canonical_name=label,
                parent_branch_ids=(),
                origin_problems=problems,
                source_ids=(seed_source.source_id,),
                tags=("macro", "seed", "requires_external_sources"),
            )
        )
        graph.add_node(
            HistoricalNode(
                node_id=f"branch::{branch_id}",
                label=label,
                kind=NodeKind.BRANCH,
                status=EpistemicStatus.SOFTWARE_FIXTURE,
                temporal_layers=tuple(TemporalLayer),
                source_ids=(seed_source.source_id,),
                tags=("macro",),
            )
        )

    edge_counter = count(1)
    for parent_id, children in SUBBRANCHES.items():
        for branch_id, label in children:
            registry.add_branch(
                BranchRecord(
                    branch_id=branch_id,
                    canonical_name=label,
                    parent_branch_ids=(parent_id,),
                    origin_problems=(f"développer l’histoire causale et instrumentale de {label}",),
                    source_ids=(seed_source.source_id,),
                    tags=("seed", "requires_external_sources"),
                )
            )
            node_id = f"branch::{branch_id}"
            graph.add_node(
                HistoricalNode(
                    node_id=node_id,
                    label=label,
                    kind=NodeKind.BRANCH,
                    status=EpistemicStatus.SOFTWARE_FIXTURE,
                    temporal_layers=tuple(TemporalLayer),
                    source_ids=(seed_source.source_id,),
                )
            )
            graph.add_edge(
                HistoricalHyperedge(
                    edge_id=f"edge.parent.{next(edge_counter):04d}",
                    kind=EdgeKind.PARENT_BRANCH,
                    source_node_ids=(f"branch::{parent_id}",),
                    target_node_ids=(node_id,),
                    status=EpistemicStatus.SOFTWARE_FIXTURE,
                    source_ids=(seed_source.source_id,),
                    rationale="Taxonomic seed relation pending historiographic enrichment.",
                )
            )

    _add_spectroscopy_fixture(graph, registry, edge_counter, seed_source.source_id)
    _add_negative_memory_fixture(registry, seed_source.source_id)
    return graph, registry


def _add_spectroscopy_fixture(
    graph: HistoricalHypergraph,
    registry: HistoryRegistry,
    edge_counter: count,
    source_id: str,
) -> None:
    branch_id = "physics.optics.spectroscopy"
    registry.add_branch(
        BranchRecord(
            branch_id=branch_id,
            canonical_name="Spectroscopie",
            parent_branch_ids=("physics.optics", "chemistry.analytical"),
            origin_problems=(
                "relier la lumière émise ou absorbée à la matière",
                "identifier quantitativement des substances et états physiques",
            ),
            precursor_node_ids=("concept::light", "instrument::prism", "observation::spectral_lines"),
            key_concept_node_ids=("concept::spectrum", "concept::transition_energy"),
            instrument_node_ids=("instrument::spectroscope",),
            method_node_ids=("method::spectral_calibration", "method::peak_analysis"),
            split_branch_ids=(
                "physics.optics.spectroscopy.absorption",
                "physics.optics.spectroscopy.emission",
                "physics.optics.spectroscopy.raman",
            ),
            negative_memory_ids=("mminus.spectroscopy.overfit",),
            active_research=("ultrafast spectroscopy", "multidimensional spectroscopy", "inverse spectral models"),
            speculative_extensions=("FFWT-HAC-CVCD comparative benchmark",),
            source_ids=(source_id,),
            tags=("cross-disciplinary", "executable_fixture", "requires_external_sources"),
        )
    )
    nodes = (
        HistoricalNode("branch::physics.optics.spectroscopy", "Spectroscopie", NodeKind.BRANCH, EpistemicStatus.SOFTWARE_FIXTURE, tuple(TemporalLayer), source_ids=(source_id,)),
        HistoricalNode("concept::light", "Lumière", NodeKind.CONCEPT, EpistemicStatus.SOURCE_REPORTED, tuple(TemporalLayer), source_ids=(source_id,)),
        HistoricalNode("instrument::prism", "Prisme", NodeKind.INSTRUMENT, EpistemicStatus.SOURCE_REPORTED, (TemporalLayer.ANCIENT_CIVILIZATIONS, TemporalLayer.EXPERIMENTAL_MATHEMATIZED), source_ids=(source_id,)),
        HistoricalNode("observation::spectral_lines", "Raies spectrales", NodeKind.OBSERVATION, EpistemicStatus.SOURCE_REPORTED, (TemporalLayer.EXPERIMENTAL_MATHEMATIZED,), source_ids=(source_id,)),
        HistoricalNode("concept::spectrum", "Spectre quantifié", NodeKind.CONCEPT, EpistemicStatus.SOURCE_REPORTED, (TemporalLayer.EXPERIMENTAL_MATHEMATIZED,), source_ids=(source_id,)),
        HistoricalNode("concept::transition_energy", "Transition d’énergie", NodeKind.CONCEPT, EpistemicStatus.SOURCE_REPORTED, (TemporalLayer.TWENTIETH_CENTURY,), source_ids=(source_id,)),
        HistoricalNode("instrument::spectroscope", "Spectroscope", NodeKind.INSTRUMENT, EpistemicStatus.SOURCE_REPORTED, (TemporalLayer.EXPERIMENTAL_MATHEMATIZED, TemporalLayer.INDUSTRIALIZED_SCIENCE), source_ids=(source_id,)),
        HistoricalNode("method::spectral_calibration", "Calibration spectrale", NodeKind.METHOD, EpistemicStatus.SOURCE_REPORTED, (TemporalLayer.INDUSTRIALIZED_SCIENCE, TemporalLayer.DIGITAL_INSTRUMENTED), source_ids=(source_id,)),
        HistoricalNode("method::peak_analysis", "Analyse de pics", NodeKind.METHOD, EpistemicStatus.SOURCE_REPORTED, (TemporalLayer.INDUSTRIALIZED_SCIENCE, TemporalLayer.DIGITAL_INSTRUMENTED), source_ids=(source_id,)),
        HistoricalNode("branch::physics.quantum.mechanics", "Mécanique quantique", NodeKind.BRANCH, EpistemicStatus.SOURCE_REPORTED, (TemporalLayer.TWENTIETH_CENTURY,), source_ids=(source_id,)),
    )
    existing_node_ids = {existing.node_id for existing in graph.nodes}
    for node in nodes:
        if node.node_id not in existing_node_ids:
            graph.add_node(node)
            existing_node_ids.add(node.node_id)

    relations = (
        (EdgeKind.ENABLED_BY, ("instrument::prism", "concept::light"), ("instrument::spectroscope",)),
        (EdgeKind.MEASURED_WITH, ("observation::spectral_lines",), ("instrument::spectroscope",)),
        (EdgeKind.FORMALIZED_BY, ("observation::spectral_lines",), ("concept::spectrum",)),
        (EdgeKind.ENABLED_BY, ("concept::spectrum", "observation::spectral_lines"), ("branch::physics.quantum.mechanics",)),
        (EdgeKind.FORMALIZED_BY, ("branch::physics.quantum.mechanics",), ("concept::transition_energy",)),
        (EdgeKind.APPLIED_TO, ("concept::transition_energy", "instrument::spectroscope"), ("branch::physics.optics.spectroscopy",)),
        (EdgeKind.ENABLED_BY, ("method::spectral_calibration", "method::peak_analysis"), ("branch::physics.optics.spectroscopy",)),
    )
    for kind, sources, targets in relations:
        graph.add_edge(
            HistoricalHyperedge(
                edge_id=f"edge.spectroscopy.{next(edge_counter):04d}",
                kind=kind,
                source_node_ids=sources,
                target_node_ids=targets,
                status=EpistemicStatus.SOFTWARE_FIXTURE,
                source_ids=(source_id,),
                rationale="Executable topology fixture; historical dates and attribution require sourced records.",
            )
        )


def _add_negative_memory_fixture(registry: HistoryRegistry, source_id: str) -> None:
    registry.add_negative_memory(
        NegativeMemoryRecord(
            memory_id="mminus.spectroscopy.overfit",
            claim="A fitted decomposition uniquely identifies the physical components of a spectrum.",
            plausibility_reason="The numerical residual can be small and the visual fit convincing.",
            test_or_challenge="Perturb initialization, line-shape family, baseline, noise model, and component count.",
            failure="Multiple incompatible decompositions can explain the same finite noisy spectrum.",
            cause="Non-identifiability, model misspecification, and overfitting.",
            lesson="Report uncertainty, identifiability, alternate models, controls, and physical constraints.",
            recurrence_risk="High when automated fitting is treated as causal identification.",
            source_ids=(source_id,),
            related_node_ids=("branch::physics.optics.spectroscopy", "method::peak_analysis"),
            fertile_for_method=True,
        )
    )
