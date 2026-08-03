from __future__ import annotations

from dataclasses import replace

from .curriculum import ActiveCurriculum
from .frontier import DEFAULT_FRONTIER, LogicalFrontier
from .generators import DEFAULT_GENERATORS, GeneratorRegistry
from .hashing import sha256_hex, stable_id
from .models import (
    CampaignObservation,
    CampaignPolicy,
    CampaignReceipt,
    EvidenceStatus,
    ProvenanceRecord,
    StopReason,
)
from .mutation import MutationRegistry
from .provenance import IPGate


class CampaignEngine:
    """Finite campaign executor over an extensible logical frontier.

    A campaign always has a local materialization budget. The architecture has no
    permanent total cap unless a caller explicitly supplies one in CampaignPolicy.
    """

    def __init__(
        self,
        frontier: LogicalFrontier = DEFAULT_FRONTIER,
        curriculum: ActiveCurriculum | None = None,
        generators: GeneratorRegistry = DEFAULT_GENERATORS,
        mutations: MutationRegistry | None = None,
        ip_gate: IPGate | None = None,
    ) -> None:
        self.frontier = frontier
        self.curriculum = curriculum or ActiveCurriculum()
        self.generators = generators
        self.mutations = mutations or MutationRegistry()
        self.ip_gate = ip_gate or IPGate()
        self.seen_addresses: set[str] = set()

    def _candidate_ordinals(self, policy: CampaignPolicy) -> tuple[int, ...]:
        count = self.frontier.logical_cell_count
        oversample = min(count, max(policy.materialization_budget * 8, 64))
        stride = 2_654_435_761 % count
        if stride == 0:
            stride = 1
        start = int(sha256_hex(policy.to_dict())[:16], 16) % count
        ordinals: list[int] = []
        current = start
        seen: set[int] = set()
        while len(ordinals) < oversample:
            if current not in seen:
                ordinals.append(current)
                seen.add(current)
            current = (current + stride) % count
            if len(seen) == count:
                break
        return tuple(ordinals)

    def run(
        self,
        policy: CampaignPolicy,
        provenance: ProvenanceRecord,
    ) -> CampaignReceipt:
        gate = self.ip_gate.evaluate(provenance, "train")
        if gate.decision.value == "block":
            return self._empty_receipt(
                policy,
                provenance_decisions={provenance.source_id: gate.decision.value},
                reason=StopReason.SAFETY_GATE,
            )

        ordinals = self._candidate_ordinals(policy)
        cells = tuple(self.frontier.cell_at(ordinal) for ordinal in ordinals)
        ranked = self.curriculum.rank(
            cells,
            self.seen_addresses,
            min(policy.materialization_budget, len(cells)),
        )

        observations: list[CampaignObservation] = []
        allocated = 0
        novelty_history: list[float] = []
        stop_reason = StopReason.BUDGET_EXHAUSTED

        ordinal_lookup = {cell.address: ordinal for ordinal, cell in zip(ordinals, cells)}
        for cell, utility in ranked:
            if policy.permanent_cap is not None and len(self.seen_addresses) >= policy.permanent_cap:
                stop_reason = StopReason.COST_GATE
                break

            ordinal = ordinal_lookup[cell.address]
            task = self.generators.select(cell).generate(cell, provenance, ordinal)
            validation_errors = TaskValidationFacade.validate(task)
            outcome = self.mutations.evaluate_fixture(task, cell.mutation_family)
            mutation_score = self.mutations.score((outcome,))
            success = not validation_errors and mutation_score >= 1.0
            evidence_status = (
                EvidenceStatus.CERTIFIED_FIXTURE if success else EvidenceStatus.FALSIFIED
            )
            failure_signatures = tuple(validation_errors)
            if not outcome.killed:
                failure_signatures += (f"surviving_mutant:{outcome.operator_id}",)

            novelty = 0.0 if cell.address in self.seen_addresses else utility.novelty
            information_gain = utility.information_gain * (1.0 if success else 0.5)
            cost_units = max(1, int(round(1 + utility.cost * 9)))
            allocated += cost_units
            observation = CampaignObservation(
                cell=cell,
                task_id=task.task_id,
                success=success,
                novelty=novelty,
                mutation_score=mutation_score,
                information_gain=information_gain,
                cost_units=cost_units,
                evidence_status=evidence_status,
                failure_signatures=failure_signatures,
            )
            observations.append(observation)
            self.seen_addresses.add(cell.address)
            self.curriculum.update_from_outcome(cell, success, mutation_score)
            novelty_history.append(novelty)

            window = policy.novelty_plateau_window
            if len(novelty_history) >= window:
                recent = novelty_history[-window:]
                if sum(recent) / len(recent) <= policy.novelty_plateau_threshold:
                    stop_reason = StopReason.NOVELTY_PLATEAU
                    break

        campaign_id = stable_id(
            "campaign",
            {
                "policy": policy.to_dict(),
                "provenance": provenance.to_dict(),
                "observations": [item.to_dict() for item in observations],
            },
            length=20,
        )
        receipt = CampaignReceipt(
            campaign_id=campaign_id,
            system_version="R0.2",
            logical_frontier_cells=self.frontier.logical_cell_count,
            materialized_cells=len(observations),
            allocated_units=allocated,
            permanent_total_cap=policy.permanent_cap,
            stop_reason=stop_reason,
            observations=tuple(observations),
            skill_posteriors=self.curriculum.skills.snapshot(),
            provenance_decisions={provenance.source_id: gate.decision.value},
            claims={
                "neural_training_claimed": False,
                "codewars_affiliation_claimed": False,
                "general_solver_optimality_claimed": False,
                "scientific_validation_claimed": False,
                "fixture_determinism_claimed": True,
                "no_permanent_cap_claimed": policy.permanent_cap is None,
            },
        )
        digest = sha256_hex(receipt.to_dict(include_hash=False))
        return replace(receipt, receipt_sha256=digest)

    def _empty_receipt(
        self,
        policy: CampaignPolicy,
        provenance_decisions: dict[str, str],
        reason: StopReason,
    ) -> CampaignReceipt:
        receipt = CampaignReceipt(
            campaign_id=stable_id("campaign-blocked", policy.to_dict(), length=20),
            system_version="R0.2",
            logical_frontier_cells=self.frontier.logical_cell_count,
            materialized_cells=0,
            allocated_units=0,
            permanent_total_cap=policy.permanent_cap,
            stop_reason=reason,
            observations=(),
            skill_posteriors=(),
            provenance_decisions=provenance_decisions,
            claims={
                "neural_training_claimed": False,
                "codewars_affiliation_claimed": False,
                "general_solver_optimality_claimed": False,
                "scientific_validation_claimed": False,
                "fixture_determinism_claimed": True,
                "no_permanent_cap_claimed": policy.permanent_cap is None,
            },
        )
        return replace(
            receipt,
            receipt_sha256=sha256_hex(receipt.to_dict(include_hash=False)),
        )


class TaskValidationFacade:
    @staticmethod
    def validate(task: object) -> tuple[str, ...]:
        from .task_ir import TaskIRCompiler

        return TaskIRCompiler.validate(task)  # type: ignore[arg-type]
