from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

from omega_morphogenesis import (
    AuthorityEnvelope,
    CapabilityCrystal,
    EpistemicStatus,
    MorphogenesisKernel,
    ProofCarryingTransformation,
    TransformationMetrics,
)


_MEMORY_KINDS = frozenset({"M+", "M-", "M?"})


@dataclass(frozen=True)
class MorphGenome:
    """Generic genome for a theory, workflow, agent, institution, product, or compiler.

    It is descriptive only: a genome never grants execution authority by itself.
    """

    id: str
    purpose: str
    state_schema: str = "TristanIR"
    operators: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    evidence_contracts: tuple[str, ...] = ()
    resources: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    memory_refs: tuple[str, ...] = ()
    regeneration_rules: tuple[str, ...] = ()
    parent_ids: tuple[str, ...] = ()
    version: str = "0.1.0"

    def digest(self) -> str:
        payload = {
            "id": self.id,
            "purpose": self.purpose,
            "state_schema": self.state_schema,
            "operators": self.operators,
            "constraints": self.constraints,
            "evidence_contracts": self.evidence_contracts,
            "resources": self.resources,
            "permissions": self.permissions,
            "memory_refs": self.memory_refs,
            "regeneration_rules": self.regeneration_rules,
            "parent_ids": self.parent_ids,
            "version": self.version,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MemoryEntry:
    id: str
    kind: str
    context: str
    decision: str
    reason: str
    outcome: str
    evidence_refs: tuple[str, ...] = ()
    residual_refs: tuple[str, ...] = ()
    generalization: str = ""

    def __post_init__(self) -> None:
        if self.kind not in _MEMORY_KINDS:
            raise ValueError("memory kind must be one of M+, M-, M?")


@dataclass
class CausalMemory:
    entries: list[MemoryEntry] = field(default_factory=list)

    def record(self, entry: MemoryEntry) -> None:
        self.entries.append(entry)

    def by_kind(self, kind: str) -> tuple[MemoryEntry, ...]:
        if kind not in _MEMORY_KINDS:
            raise ValueError("memory kind must be one of M+, M-, M?")
        return tuple(entry for entry in self.entries if entry.kind == kind)

    def negative_invariants(self) -> tuple[str, ...]:
        """Compress repeated failure memory into reusable explicit rules.

        This deliberately does not infer new causal laws. It returns only declared
        generalizations already attached to M- records.
        """
        return tuple(
            sorted(
                {
                    entry.generalization.strip()
                    for entry in self.by_kind("M-")
                    if entry.generalization.strip()
                }
            )
        )


@dataclass(frozen=True)
class MorphogenesisReceipt:
    receipt_id: str
    before_hash: str
    after_hash: str
    transformation: str
    generator_id: str
    verifier_id: str
    accepted: bool
    persist: bool
    reasons: tuple[str, ...]
    utility: float
    evidence_refs: tuple[str, ...]
    tests: tuple[str, ...]
    uncertainty: float
    authority: tuple[str, ...]
    rollback: str | None
    external_action_performed: bool = False
    auto_promoted: bool = False


@dataclass(frozen=True)
class RetentionDecision:
    disposition: str
    reason: str
    automatic_delete: bool = False


class MetaMorphogenesisEngine:
    """Meta-layer court that reuses the canonical omega_morphogenesis kernel.

    The engine can evaluate and crystallize candidates, but it never executes
    external actions, self-grants permissions, or auto-deletes artifacts.
    """

    def __init__(self, kernel: MorphogenesisKernel | None = None) -> None:
        self.kernel = kernel or MorphogenesisKernel()

    def evaluate_transition(
        self,
        before: MorphGenome,
        after: MorphGenome,
        *,
        transformation: str,
        generator_id: str,
        verifier_id: str,
        action: str,
        authority_actions: Sequence[str],
        input_status: EpistemicStatus,
        output_status: EpistemicStatus,
        evidence_status: EpistemicStatus,
        provenance: Iterable[str],
        tests: Iterable[str],
        evidence_refs: Iterable[str] = (),
        assumptions: Iterable[str] = (),
        rollback: str | None = None,
        compensation: str | None = None,
        risk_score: float = 0.0,
        uncertainty: float = 0.0,
        metrics: TransformationMetrics | None = None,
    ) -> MorphogenesisReceipt:
        tx = ProofCarryingTransformation(
            transformation_id=transformation,
            before_hash=before.digest(),
            after_hash=after.digest(),
            generator_id=generator_id,
            verifier_id=verifier_id,
            action=action,
            authority=AuthorityEnvelope.from_actions(*authority_actions),
            input_status=input_status,
            output_status=output_status,
            evidence_status=evidence_status,
            provenance=tuple(provenance),
            assumptions=tuple(assumptions),
            tests=tuple(tests),
            rollback=rollback,
            compensation=compensation,
            risk_score=risk_score,
            metrics=metrics or TransformationMetrics(),
        )
        decision = self.kernel.validate(tx)
        payload = {
            "before": tx.before_hash,
            "after": tx.after_hash,
            "transformation": transformation,
            "generator": generator_id,
            "verifier": verifier_id,
            "accepted": decision.accepted,
            "persist": decision.persist,
            "evidence": tuple(evidence_refs),
            "tests": tx.tests,
        }
        receipt_id = "morph-" + sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:20]
        return MorphogenesisReceipt(
            receipt_id=receipt_id,
            before_hash=tx.before_hash,
            after_hash=tx.after_hash,
            transformation=transformation,
            generator_id=generator_id,
            verifier_id=verifier_id,
            accepted=decision.accepted,
            persist=decision.persist,
            reasons=decision.reasons,
            utility=decision.utility,
            evidence_refs=tuple(evidence_refs),
            tests=tx.tests,
            uncertainty=uncertainty,
            authority=tuple(sorted(tx.authority.allowed_actions)),
            rollback=rollback,
        )

    def crystallize(
        self,
        receipt: MorphogenesisReceipt,
        *,
        name: str,
        contract: str,
        inputs: Sequence[str],
        outputs: Sequence[str],
        dependencies: Sequence[str] = (),
        provenance: Sequence[str] = (),
    ) -> CapabilityCrystal:
        if not receipt.accepted:
            raise ValueError("rejected morphogenesis cannot crystallize")
        if not receipt.persist:
            raise ValueError("candidate did not pay complexity rent")
        if not receipt.evidence_refs:
            raise ValueError("crystal requires evidence")
        if not receipt.tests:
            raise ValueError("crystal requires tests")
        return CapabilityCrystal(
            name=name,
            contract=contract,
            inputs=tuple(inputs),
            outputs=tuple(outputs),
            generator=receipt.generator_id,
            evidence=receipt.evidence_refs,
            tests=receipt.tests,
            dependencies=tuple(dependencies),
            provenance=tuple(provenance),
        )

    def apoptosis_review(
        self,
        *,
        component: str,
        marginal_verified_capability: float,
        maintenance: float,
        complexity: float,
        risk: float,
        regeneration_closure: float,
        preserves_evidence: bool,
        preserves_provenance: bool,
        survival_threshold: float = 0.5,
    ) -> RetentionDecision:
        if not 0.0 <= regeneration_closure <= 1.0:
            raise ValueError("regeneration_closure must be in [0,1]")
        if regeneration_closure < 1.0:
            return RetentionDecision("KEEP", f"{component}: regeneration closure is incomplete")
        if not preserves_evidence or not preserves_provenance:
            return RetentionDecision("KEEP", f"{component}: evidence/provenance would be lost")
        denominator = 1.0 + max(maintenance, 0.0) + max(complexity, 0.0) + max(risk, 0.0)
        survival_score = max(marginal_verified_capability, 0.0) / denominator
        if survival_score < survival_threshold:
            return RetentionDecision(
                "ELIGIBLE_FOR_REVIEW",
                f"{component}: survival_score={survival_score:.6f} < {survival_threshold:.6f}",
            )
        return RetentionDecision(
            "KEEP",
            f"{component}: survival_score={survival_score:.6f} >= {survival_threshold:.6f}",
        )

    def forget_plus_review(
        self,
        *,
        component: str,
        regeneration_closure: float,
        preserves_evidence: bool,
        preserves_provenance: bool,
        threshold: float = 0.999,
    ) -> RetentionDecision:
        if regeneration_closure >= threshold and preserves_evidence and preserves_provenance:
            return RetentionDecision(
                "REGENERATE_ON_DEMAND",
                f"{component}: reconstructible with preserved evidence/provenance",
            )
        return RetentionDecision("KEEP", f"{component}: destructive forgetting is not justified")

    def evidence_blast_radius(
        self,
        dependency_graph: Mapping[str, Iterable[str]],
        invalidated_evidence: str,
    ) -> tuple[str, ...]:
        return self.kernel.evidence_dependency_blast_radius(dependency_graph, invalidated_evidence)
