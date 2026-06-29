"""EvidenceGraph compiler for Daily Omega Intelligence OS.

This module converts compiled SignalGenome++ objects into an OAK-safe evidence
structure: factual claims, strategic inferences, counter-hypotheses, evidence
scores, and promotion blockers.

It is local-only: no network calls, no GitHub calls, no issue creation, and no
canon promotion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from sage_tristan.daily_omega_batch import DEFAULT_TIMEZONE, build_batch_from_directory
from sage_tristan.daily_omega_intelligence_os import SignalGenome

LOW_SUPPORT_LEVELS = frozenset({"none", "weak"})


@dataclass(frozen=True)
class EvidenceClaim:
    """One claim with source support and residue."""

    claim_type: str
    text: str
    support_level: str
    contradiction_level: str
    source_refs: tuple[str, ...]
    residue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_type": self.claim_type,
            "text": self.text,
            "support_level": self.support_level,
            "contradiction_level": self.contradiction_level,
            "source_refs": list(self.source_refs),
            "residue": self.residue,
        }


@dataclass(frozen=True)
class CounterHypothesis:
    """A rival hypothesis and the test that could falsify or weaken the signal."""

    hypothesis: str
    falsification_test: str
    priority: str

    def to_dict(self) -> dict[str, str]:
        return {
            "hypothesis": self.hypothesis,
            "falsification_test": self.falsification_test,
            "priority": self.priority,
        }


@dataclass(frozen=True)
class EvidenceScore:
    """Compact score vector for OAK evidence review."""

    source_quality: int
    corroboration: int
    specificity: int
    reproducibility: int
    contradiction_risk: int

    def to_dict(self) -> dict[str, int]:
        return {
            "source_quality": self.source_quality,
            "corroboration": self.corroboration,
            "specificity": self.specificity,
            "reproducibility": self.reproducibility,
            "contradiction_risk": self.contradiction_risk,
        }


@dataclass(frozen=True)
class EvidenceGraph:
    """Evidence graph for one SignalGenome++."""

    signal_title: str
    factual_claims: tuple[EvidenceClaim, ...]
    strategic_inferences: tuple[EvidenceClaim, ...]
    counter_hypotheses: tuple[CounterHypothesis, ...]
    evidence_score: EvidenceScore
    promotion_blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_title": self.signal_title,
            "factual_claims": [claim.to_dict() for claim in self.factual_claims],
            "strategic_inferences": [claim.to_dict() for claim in self.strategic_inferences],
            "counter_hypotheses": [hypothesis.to_dict() for hypothesis in self.counter_hypotheses],
            "evidence_score": self.evidence_score.to_dict(),
            "promotion_blockers": list(self.promotion_blockers),
        }


@dataclass(frozen=True)
class EvidenceResult:
    """Batch-level EvidenceGraph export."""

    briefing_date: date
    timezone: str
    graphs: tuple[EvidenceGraph, ...]

    @property
    def is_clear(self) -> bool:
        return not any(graph.promotion_blockers for graph in self.graphs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "briefing_date": self.briefing_date.isoformat(),
            "timezone": self.timezone,
            "is_clear": self.is_clear,
            "graphs": [graph.to_dict() for graph in self.graphs],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def _bounded_score(value: int) -> int:
    return max(0, min(5, int(value)))


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


def infer_support_level(genome: SignalGenome) -> str:
    """Infer conservative source support for claims in a genome."""

    statuses = {entry.verification_status for entry in genome.source_ledger}
    if not statuses:
        return "none"
    if "source_placeholder" in statuses or "source_required" in statuses:
        return "weak"
    if "source_found" in statuses:
        return "medium"
    if statuses == {"source_verified"}:
        return "strong"
    return "medium"


def infer_contradiction_level(genome: SignalGenome) -> str:
    """Infer contradiction risk from OAK residue and blockers.

    This does not claim that contradictions were found; it only encodes how much
    contradiction search is still needed.
    """

    if genome.oak_validation_route.blocking_check != "none":
        return "medium"
    if genome.evidence_matrix.risk <= 2:
        return "medium"
    if genome.evidence_matrix.source <= 2:
        return "weak"
    return "none"


def source_refs(genome: SignalGenome) -> tuple[str, ...]:
    """Return compact source references for a genome."""

    return tuple(f"{entry.title}::{entry.url_or_identifier}" for entry in genome.source_ledger)


def build_evidence_claims(genome: SignalGenome) -> tuple[tuple[EvidenceClaim, ...], tuple[EvidenceClaim, ...]]:
    """Split claim nodes into factual claims and strategic inferences."""

    support = infer_support_level(genome)
    contradiction = infer_contradiction_level(genome)
    refs = source_refs(genome)
    factual: list[EvidenceClaim] = []
    strategic: list[EvidenceClaim] = []
    for claim in genome.claim_graph:
        evidence_claim = EvidenceClaim(
            claim_type=claim.claim_type,
            text=claim.text,
            support_level=support if claim.claim_type == "factual_claim" else "testable",
            contradiction_level=contradiction,
            source_refs=refs,
            residue=claim.oak_status,
        )
        if claim.claim_type == "factual_claim":
            factual.append(evidence_claim)
        else:
            strategic.append(evidence_claim)
    return tuple(factual), tuple(strategic)


def build_counter_hypotheses(genome: SignalGenome) -> tuple[CounterHypothesis, ...]:
    """Generate conservative counter-hypotheses for an evidence graph."""

    hypotheses: list[CounterHypothesis] = []
    if infer_support_level(genome) in LOW_SUPPORT_LEVELS:
        hypotheses.append(
            CounterHypothesis(
                hypothesis="The central factual signal may be unsupported or overstated.",
                falsification_test="Replace placeholder or weak source with a primary source or credible corroboration.",
                priority="high",
            )
        )
    if genome.oak_validation_route.blocking_check != "none":
        hypotheses.append(
            CounterHypothesis(
                hypothesis="The signal may be strategically attractive but blocked by an unresolved OAK gate.",
                falsification_test=f"Resolve `{genome.oak_validation_route.blocking_check}` before promotion.",
                priority="high",
            )
        )
    if genome.ip_risk_level in {"medium_prior_art_needed", "high_confidential_invention", "danger_do_not_disclose"}:
        hypotheses.append(
            CounterHypothesis(
                hypothesis="The public framing may damage IP position or collide with prior art.",
                falsification_test="Run IP/prior-art review and produce separate public-safe/private notes.",
                priority="medium",
            )
        )
    if genome.agent_security_ledger.permission_scope != "none":
        hypotheses.append(
            CounterHypothesis(
                hypothesis="The agentic route may fail through unsafe permissions or missing observability.",
                falsification_test="Require least privilege, audit logs, rollback, and task-success metrics.",
                priority="medium",
            )
        )
    if genome.infrastructure_dependency.risk_level in {"medium", "high"}:
        hypotheses.append(
            CounterHypothesis(
                hypothesis="The opportunity may depend on fragile infrastructure or supply-chain assumptions.",
                falsification_test="Map cloud, compute, energy, jurisdiction, and material dependencies.",
                priority="medium",
            )
        )
    if not hypotheses:
        hypotheses.append(
            CounterHypothesis(
                hypothesis="The signal may still fail to outperform simpler alternatives.",
                falsification_test="Compare the proposed action against a baseline, manual workflow, or no-action option.",
                priority="low",
            )
        )
    return tuple(hypotheses)


def build_evidence_score(genome: SignalGenome) -> EvidenceScore:
    """Build a compact EvidenceScore from a genome."""

    verified_count = sum(1 for entry in genome.source_ledger if entry.verification_status == "source_verified")
    corroboration = 0
    if verified_count >= 2:
        corroboration = 5
    elif verified_count == 1 and len(genome.source_ledger) >= 2:
        corroboration = 3
    elif verified_count == 1:
        corroboration = 2
    specificity = 5 if genome.prototype_horizon != "none" and genome.next_action else 3 if genome.next_action else 1
    reproducibility = 5 if "prototype_check" in genome.oak_validation_route.checks else 3 if genome.prototype_horizon != "none" else 1
    contradiction_risk = 5 if infer_contradiction_level(genome) == "medium" else 2 if infer_contradiction_level(genome) == "weak" else 0
    return EvidenceScore(
        source_quality=_bounded_score(genome.evidence_matrix.source),
        corroboration=_bounded_score(corroboration),
        specificity=_bounded_score(specificity),
        reproducibility=_bounded_score(reproducibility),
        contradiction_risk=_bounded_score(contradiction_risk),
    )


def find_promotion_blockers(genome: SignalGenome, factual_claims: tuple[EvidenceClaim, ...]) -> tuple[str, ...]:
    """Return blockers that prevent canon/public/business promotion."""

    blockers: list[str] = []
    if any(claim.support_level in LOW_SUPPORT_LEVELS for claim in factual_claims):
        blockers.append("claim_support_gap")
    if genome.oak_validation_route.blocking_check != "none":
        blockers.append(genome.oak_validation_route.blocking_check)
    if genome.ip_risk_level in {"high_confidential_invention", "danger_do_not_disclose"}:
        blockers.append("ip_public_disclosure_block")
    if genome.agent_security_ledger.permission_scope != "none" and not genome.agent_security_ledger.audit_logs_required:
        blockers.append("agent_observability_gap")
    return _dedupe(blockers)


def build_evidence_graph(genome: SignalGenome) -> EvidenceGraph:
    """Compile one SignalGenome++ into an EvidenceGraph."""

    factual_claims, strategic_inferences = build_evidence_claims(genome)
    return EvidenceGraph(
        signal_title=genome.title,
        factual_claims=factual_claims,
        strategic_inferences=strategic_inferences,
        counter_hypotheses=build_counter_hypotheses(genome),
        evidence_score=build_evidence_score(genome),
        promotion_blockers=find_promotion_blockers(genome, factual_claims),
    )


def build_evidence_result(
    genomes: Iterable[SignalGenome],
    *,
    briefing_date: date,
    timezone: str = DEFAULT_TIMEZONE,
) -> EvidenceResult:
    """Build an EvidenceResult from compiled genomes."""

    return EvidenceResult(
        briefing_date=briefing_date,
        timezone=timezone,
        graphs=tuple(build_evidence_graph(genome) for genome in genomes),
    )


def build_evidence_from_directory(
    directory: str,
    *,
    briefing_date: date,
    timezone: str = DEFAULT_TIMEZONE,
    limit: int = 5,
    dry_run: bool = True,
) -> EvidenceResult:
    """Load signals, compile genomes, and return EvidenceGraphs."""

    batch = build_batch_from_directory(
        directory,
        briefing_date=briefing_date,
        timezone=timezone,
        limit=limit,
        dry_run=dry_run,
    )
    return build_evidence_result(batch.genomes, briefing_date=briefing_date, timezone=timezone)


def find_claim_gaps(graph: EvidenceGraph) -> tuple[str, ...]:
    """Return claim-level support gaps from an EvidenceGraph."""

    gaps: list[str] = []
    for claim in graph.factual_claims:
        if claim.support_level in LOW_SUPPORT_LEVELS:
            gaps.append(f"{graph.signal_title}: factual claim has {claim.support_level} support")
    if not graph.factual_claims:
        gaps.append(f"{graph.signal_title}: no factual claim found")
    return tuple(gaps)


def find_counter_hypothesis_gaps(graph: EvidenceGraph) -> tuple[str, ...]:
    """Return counter-hypothesis gaps from an EvidenceGraph."""

    if not graph.counter_hypotheses:
        return (f"{graph.signal_title}: no counter-hypothesis found",)
    if all(hypothesis.priority == "low" for hypothesis in graph.counter_hypotheses):
        return (f"{graph.signal_title}: only low-priority generic counter-hypothesis found",)
    return ()


def render_evidence_markdown(result: EvidenceResult) -> str:
    """Render EvidenceGraphs as Markdown."""

    lines = [
        f"# Daily Ω EvidenceGraph — {result.briefing_date.isoformat()}",
        "",
        f"Timezone: `{result.timezone}`",
        f"Clear for promotion: `{str(result.is_clear).lower()}`",
        "",
    ]
    for index, graph in enumerate(result.graphs, start=1):
        lines.extend(
            [
                f"## {index}. {graph.signal_title}",
                f"- **Promotion blockers:** {', '.join(graph.promotion_blockers) or 'none'}",
                f"- **Evidence score:** source={graph.evidence_score.source_quality}, corroboration={graph.evidence_score.corroboration}, specificity={graph.evidence_score.specificity}, reproducibility={graph.evidence_score.reproducibility}, contradiction_risk={graph.evidence_score.contradiction_risk}",
                "",
                "### Factual claims",
                "",
            ]
        )
        for claim in graph.factual_claims:
            lines.extend(
                [
                    f"- **{claim.support_level} support / contradiction {claim.contradiction_level}:** {claim.text}",
                    f"  - residue: `{claim.residue}`",
                ]
            )
        lines.extend(["", "### Strategic inferences", ""])
        for claim in graph.strategic_inferences:
            lines.extend(
                [
                    f"- **{claim.claim_type}:** {claim.text}",
                    f"  - status: `{claim.residue}`",
                ]
            )
        lines.extend(["", "### Counter-hypotheses", ""])
        for hypothesis in graph.counter_hypotheses:
            lines.extend(
                [
                    f"- **{hypothesis.priority}:** {hypothesis.hypothesis}",
                    f"  - test: {hypothesis.falsification_test}",
                ]
            )
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "CounterHypothesis",
    "EvidenceClaim",
    "EvidenceGraph",
    "EvidenceResult",
    "EvidenceScore",
    "LOW_SUPPORT_LEVELS",
    "build_counter_hypotheses",
    "build_evidence_claims",
    "build_evidence_from_directory",
    "build_evidence_graph",
    "build_evidence_result",
    "build_evidence_score",
    "find_claim_gaps",
    "find_counter_hypothesis_gaps",
    "find_promotion_blockers",
    "infer_contradiction_level",
    "infer_support_level",
    "render_evidence_markdown",
]
