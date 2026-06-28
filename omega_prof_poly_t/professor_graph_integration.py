"""Integrate absorbed research into ProfessorGraph-Poly."""

from __future__ import annotations

from typing import Iterable

from .professor_graph import HyperEdge, Node, ProfessorGraph
from .research_atom import ResearchAtom


def research_atoms_to_professor_graph(atoms: Iterable[ResearchAtom]) -> ProfessorGraph:
    graph = ProfessorGraph()
    atoms_tuple = tuple(atoms)
    for atom in atoms_tuple:
        atom_node_id = f"atom:{atom.atom_id}"
        graph.add_node(Node(atom_node_id, "research_atom", atom.title, {"source": atom.source, "link": atom.link}))
        for professor in atom.professors or atom.authors:
            prof_id = f"professor:{professor}"
            if prof_id not in graph.nodes:
                graph.add_node(Node(prof_id, "professor", professor))
            graph.add_edge(HyperEdge(f"edge:{prof_id}:{atom_node_id}", "authored_or_linked", (prof_id, atom_node_id), 0.9))
        for method in atom.methods:
            method_id = f"method:{method}"
            if method_id not in graph.nodes:
                graph.add_node(Node(method_id, "method", method))
            graph.add_edge(HyperEdge(f"edge:{atom_node_id}:{method_id}", "uses_method", (atom_node_id, method_id), 0.75))
        for keyword in atom.keywords:
            keyword_id = f"keyword:{keyword}"
            if keyword_id not in graph.nodes:
                graph.add_node(Node(keyword_id, "keyword", keyword))
            graph.add_edge(HyperEdge(f"edge:{atom_node_id}:{keyword_id}", "has_keyword", (atom_node_id, keyword_id), 0.55))
    return graph
