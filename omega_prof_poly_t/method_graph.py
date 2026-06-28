"""MethodGraph for Ω-ABSORB-POLY-PROF-T v0.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .research_atom import ResearchAtom


@dataclass(frozen=True)
class MethodNode:
    method_id: str
    method: str
    atom_ids: Tuple[str, ...]
    keywords: Tuple[str, ...]
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    assumptions: Tuple[str, ...]
    reproducibility_score: float
    domains: Tuple[str, ...]


@dataclass(frozen=True)
class MethodGraph:
    methods: Tuple[MethodNode, ...]
    reusable_methods: Tuple[str, ...]
    missing_reproducibility: Tuple[str, ...]
    next_action: str

    def methods_by_domain(self) -> Dict[str, Tuple[MethodNode, ...]]:
        grouped: Dict[str, list[MethodNode]] = {}
        for method in self.methods:
            for domain in method.domains:
                grouped.setdefault(domain, []).append(method)
        return {domain: tuple(nodes) for domain, nodes in grouped.items()}


def build_method_graph(atoms: Iterable[ResearchAtom]) -> MethodGraph:
    atoms_tuple = tuple(atoms)
    method_to_atoms: Dict[str, list[ResearchAtom]] = {}
    for atom in atoms_tuple:
        for method in atom.methods:
            method_to_atoms.setdefault(method, []).append(atom)

    nodes = []
    reusable = []
    missing = []
    for index, (method, method_atoms) in enumerate(sorted(method_to_atoms.items()), start=1):
        atom_ids = tuple(atom.atom_id for atom in method_atoms)
        keywords = tuple(dict.fromkeys(keyword for atom in method_atoms for keyword in atom.keywords))
        domains = tuple(dict.fromkeys(dept for atom in method_atoms for dept in atom.departments))
        has_data = any(atom.datasets for atom in method_atoms)
        has_code = any(atom.code_links for atom in method_atoms)
        reproducibility_score = round(0.35 + 0.25 * has_data + 0.30 * has_code + 0.10 * min(1, len(method_atoms) / 2), 4)
        if reproducibility_score >= 0.70:
            reusable.append(method)
        else:
            missing.append(method)
        nodes.append(
            MethodNode(
                method_id=f"method:{index}",
                method=method,
                atom_ids=atom_ids,
                keywords=keywords,
                inputs=("public_metadata", "abstract", "method_description"),
                outputs=("course_module", "lab_seed", "project_seed", "prototype_seed"),
                assumptions=("source_grounded", "domain_limits_required"),
                reproducibility_score=reproducibility_score,
                domains=domains,
            )
        )
    return MethodGraph(
        methods=tuple(nodes),
        reusable_methods=tuple(reusable),
        missing_reproducibility=tuple(missing),
        next_action="route_reusable_methods_to_course_lab_project_compilers",
    )
