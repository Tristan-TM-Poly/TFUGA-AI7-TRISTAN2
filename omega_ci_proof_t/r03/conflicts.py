from __future__ import annotations

from collections import defaultdict

from .graph import EpistemicGraphEngine
from .models import ConflictReport, EvidenceConflict


class EvidenceConflictEngine:
    def analyze(self, engine: EpistemicGraphEngine) -> ConflictReport:
        supports: dict[str, list[str]] = defaultdict(list)
        contradicts: dict[str, list[str]] = defaultdict(list)
        for edge in engine.graph.edges:
            if edge.relation == "supported_by":
                supports[edge.source].append(edge.target)
            elif edge.relation == "contradicted_by":
                contradicts[edge.source].append(edge.target)
        conflicts: list[EvidenceConflict] = []
        for claim_id in sorted(set(supports).intersection(contradicts)):
            claim = engine.nodes[claim_id]
            metadata = dict(claim.metadata)
            experiments = tuple(str(value) for value in metadata.get("discriminating_experiments", ())) or (
                f"EXP-CROSS-VALIDATE-{claim_id}",
            )
            hypotheses = tuple(str(value) for value in metadata.get("conflict_hypotheses", ())) or (
                "environment_or_scope_interaction",
                "measurement_or_fixture_difference",
                "claim_is_too_broad",
            )
            severity = "critical" if claim.criticality >= 5 else "high" if claim.criticality >= 4 else "medium"
            conflicts.append(EvidenceConflict(
                claim_id=claim_id,
                supporting_node_ids=tuple(sorted(supports[claim_id])),
                contradicting_node_ids=tuple(sorted(contradicts[claim_id])),
                severity=severity,
                hypotheses=hypotheses,
                discriminating_experiments=experiments,
            ))
        return ConflictReport(
            conflicts=tuple(conflicts),
            open_conflicts=len(conflicts),
            critical_conflicts=sum(item.severity == "critical" for item in conflicts),
            graph_id=engine.graph.graph_id,
        )
