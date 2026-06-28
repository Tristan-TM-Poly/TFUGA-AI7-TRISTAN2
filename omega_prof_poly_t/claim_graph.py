"""ClaimGraph for Ω-ABSORB-POLY-PROF-T v0.4.

ClaimGraph converts public ResearchAtoms into claim/evidence/method/limit/test
nodes without treating claims as truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple

from .research_atom import ResearchAtom


@dataclass(frozen=True)
class ClaimNode:
    claim_id: str
    atom_id: str
    claim: str
    evidence: Tuple[str, ...] = ()
    methods: Tuple[str, ...] = ()
    limitations: Tuple[str, ...] = ()
    tests: Tuple[str, ...] = ()
    status: str = "exploratory"


@dataclass(frozen=True)
class ClaimGraph:
    claims: Tuple[ClaimNode, ...]
    warnings: Tuple[str, ...]
    next_action: str

    def claims_by_atom(self) -> Dict[str, Tuple[ClaimNode, ...]]:
        grouped: Dict[str, list[ClaimNode]] = {}
        for claim in self.claims:
            grouped.setdefault(claim.atom_id, []).append(claim)
        return {atom_id: tuple(nodes) for atom_id, nodes in grouped.items()}


def build_claim_graph(atoms: Iterable[ResearchAtom]) -> ClaimGraph:
    nodes = []
    warnings = []
    for atom in atoms:
        if not atom.claims:
            warnings.append(f"no_claims:{atom.atom_id}")
        for index, claim in enumerate(atom.claims or (f"implicit_claim_from:{atom.title}",), start=1):
            limitations = atom.limitations or ("limitation_not_extracted",)
            tests = tuple(f"test_claim_{index}_with_{method}" for method in atom.methods) or ("define_reproduction_test",)
            status = "prototype" if atom.methods and atom.limitations else "exploratory"
            nodes.append(
                ClaimNode(
                    claim_id=f"{atom.atom_id}:claim:{index}",
                    atom_id=atom.atom_id,
                    claim=str(claim),
                    evidence=(atom.link or atom.source,),
                    methods=atom.methods,
                    limitations=limitations,
                    tests=tests,
                    status=status,
                )
            )
    return ClaimGraph(
        claims=tuple(nodes),
        warnings=tuple(warnings),
        next_action="compile_claims_to_tests_and_research_opportunities",
    )
