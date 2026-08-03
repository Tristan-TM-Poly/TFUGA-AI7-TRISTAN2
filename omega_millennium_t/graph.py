"""Hypergraph-like dependency engine for candidate proofs."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict
import hashlib
import json
from typing import Iterable, Mapping

from .models import Claim, EdgeKind, OAKLevel, ProblemId, ProofEdge, ValidationReport


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


class ProofGraph:
    """A deterministic, fail-closed proof dependency graph.

    A proof edge may have several premises, so it is represented explicitly
    rather than flattened into pairwise edges.  A conclusion becomes reachable
    only when every premise of at least one sufficiently certified edge is
    reachable.
    """

    def __init__(self, problem_id: ProblemId | str) -> None:
        self.problem_id = ProblemId(problem_id)
        self._claims: dict[str, Claim] = {}
        self._edges: dict[str, ProofEdge] = {}

    @property
    def claims(self) -> Mapping[str, Claim]:
        return dict(self._claims)

    @property
    def edges(self) -> Mapping[str, ProofEdge]:
        return dict(self._edges)

    def add_claim(self, claim: Claim) -> None:
        if claim.problem_id != self.problem_id:
            raise ValueError("claim problem_id does not match graph")
        errors = claim.validate()
        if errors:
            raise ValueError("; ".join(errors))
        if claim.claim_id in self._claims:
            raise ValueError(f"duplicate claim_id: {claim.claim_id}")
        self._claims[claim.claim_id] = claim

    def add_edge(self, edge: ProofEdge) -> None:
        if edge.problem_id != self.problem_id:
            raise ValueError("edge problem_id does not match graph")
        errors = edge.validate()
        if errors:
            raise ValueError("; ".join(errors))
        if edge.edge_id in self._edges:
            raise ValueError(f"duplicate edge_id: {edge.edge_id}")
        unknown = [node for node in (*edge.premises, edge.conclusion) if node not in self._claims]
        if unknown:
            raise ValueError(f"edge references unknown claims: {unknown}")
        self._edges[edge.edge_id] = edge

    def validate(self) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        for claim in self._claims.values():
            errors.extend(f"claim {claim.claim_id}: {error}" for error in claim.validate())
            unknown = [item for item in claim.dependencies if item not in self._claims]
            if unknown:
                errors.append(f"claim {claim.claim_id} has unknown dependencies {unknown}")
        for edge in self._edges.values():
            errors.extend(f"edge {edge.edge_id}: {error}" for error in edge.validate())
            unknown = [node for node in (*edge.premises, edge.conclusion) if node not in self._claims]
            if unknown:
                errors.append(f"edge {edge.edge_id} has unknown nodes {unknown}")
            conclusion = self._claims.get(edge.conclusion)
            if conclusion and edge.oak_level > conclusion.oak_level:
                warnings.append(
                    f"edge {edge.edge_id} is more certified than conclusion {edge.conclusion}; "
                    "promotion still requires OAK evaluation"
                )
        cycles = self._dependency_cycles()
        if cycles:
            warnings.extend(f"dependency cycle detected: {' -> '.join(cycle)}" for cycle in cycles)
        return ValidationReport(
            valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
            metrics={
                "claims": len(self._claims),
                "edges": len(self._edges),
                "cycles": len(cycles),
                "digest": self.digest(),
            },
        )

    def digest(self) -> str:
        payload = {
            "problem_id": self.problem_id.value,
            "claims": [asdict(self._claims[key]) for key in sorted(self._claims)],
            "edges": [asdict(self._edges[key]) for key in sorted(self._edges)],
        }
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()

    def reachable_claims(
        self,
        seed_claim_ids: Iterable[str],
        *,
        minimum_level: OAKLevel = OAKLevel.WELL_TYPED,
    ) -> frozenset[str]:
        reached = set(seed_claim_ids)
        unknown = reached - self._claims.keys()
        if unknown:
            raise ValueError(f"unknown seed claims: {sorted(unknown)}")
        changed = True
        while changed:
            changed = False
            for edge in self._edges.values():
                if edge.kind == EdgeKind.REFUTES or edge.oak_level < minimum_level:
                    continue
                if edge.conclusion in reached:
                    continue
                if all(premise in reached for premise in edge.premises):
                    reached.add(edge.conclusion)
                    changed = True
        return frozenset(reached)

    def missing_premises(
        self,
        target_claim_id: str,
        seed_claim_ids: Iterable[str],
        *,
        minimum_level: OAKLevel = OAKLevel.WELL_TYPED,
    ) -> tuple[tuple[str, ...], ...]:
        if target_claim_id not in self._claims:
            raise ValueError(f"unknown target claim: {target_claim_id}")
        reached = self.reachable_claims(seed_claim_ids, minimum_level=minimum_level)
        if target_claim_id in reached:
            return ()
        candidates: list[tuple[str, ...]] = []
        for edge in self._edges.values():
            if edge.conclusion != target_claim_id or edge.oak_level < minimum_level:
                continue
            missing = tuple(sorted(set(edge.premises) - reached))
            if missing:
                candidates.append(missing)
        return tuple(sorted(set(candidates), key=lambda item: (len(item), item)))

    def minimal_frontier(
        self,
        target_claim_id: str,
        seed_claim_ids: Iterable[str],
        *,
        minimum_level: OAKLevel = OAKLevel.WELL_TYPED,
    ) -> tuple[str, ...]:
        """Return a deterministic local lemma frontier.

        This is intentionally a local cut heuristic, not a claim of globally
        minimum proof complexity.
        """
        options = self.missing_premises(target_claim_id, seed_claim_ids, minimum_level=minimum_level)
        if not options:
            return ()
        return options[0]

    def refutations_of(self, claim_id: str) -> tuple[ProofEdge, ...]:
        return tuple(
            edge for edge in self._edges.values()
            if edge.kind == EdgeKind.REFUTES and edge.conclusion == claim_id
        )

    def incoming_edges(self, claim_id: str) -> tuple[ProofEdge, ...]:
        return tuple(edge for edge in self._edges.values() if edge.conclusion == claim_id)

    def _dependency_cycles(self) -> tuple[tuple[str, ...], ...]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        indegree: dict[str, int] = {claim_id: 0 for claim_id in self._claims}
        for edge in self._edges.values():
            if edge.kind == EdgeKind.REFUTES:
                continue
            for premise in edge.premises:
                if edge.conclusion not in adjacency[premise]:
                    adjacency[premise].add(edge.conclusion)
                    indegree[edge.conclusion] += 1
        queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
        visited: list[str] = []
        while queue:
            node = queue.popleft()
            visited.append(node)
            for nxt in sorted(adjacency[node]):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        if len(visited) == len(indegree):
            return ()
        residual = tuple(sorted(node for node, degree in indegree.items() if degree > 0))
        return (residual,)
