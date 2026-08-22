from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Sequence

from .models import Candidate, Residual, stable_hash


@dataclass(frozen=True)
class AuthorityEnvelope:
    allowed_actions: tuple[str, ...] = ("READ", "SIMULATE", "TEST")
    external_write: bool = False
    financial: bool = False
    safety_critical: bool = False

    def allows(self, action: str) -> bool:
        return action in self.allowed_actions


@dataclass(frozen=True)
class WorkflowGenome:
    goal: str
    steps: tuple[str, ...]
    required_authority: tuple[str, ...]
    residual_targets: tuple[str, ...]
    rollback: str = "abort workflow and preserve last verified state"

    @property
    def id(self) -> str:
        return stable_hash(self.__dict__)[:16]


@dataclass(frozen=True)
class QuestionCandidate:
    question: str
    source_residual: str
    expected_information_gain: float
    probe: str


class RegenerationDepth(IntEnum):
    R0_NON_REGENERABLE = 0
    R1_FILES = 1
    R2_ARTIFACT = 2
    R3_WORKFLOW = 3
    R4_GENERATOR = 4
    R5_ECOSYSTEM = 5


@dataclass(frozen=True)
class ForgetReceipt:
    object_id: str
    reason: str
    ablation_gain: float
    regenerable: bool
    regeneration_depth: RegenerationDepth


class MetaController:
    """Meta-operations subordinate to verifier and authority gates."""

    def compile_workflow(self, goal: str, residuals: Sequence[Residual], authority: AuthorityEnvelope) -> WorkflowGenome:
        steps = ["OBSERVE", "RESIDUALIZE", "GENERATE", "VERIFY"]
        required = ["READ", "SIMULATE", "TEST"]
        if authority.external_write and authority.allows("EXTERNAL_WRITE"):
            steps.append("PROPOSE_EXTERNAL_WRITE")
            required.append("EXTERNAL_WRITE")
        steps.extend(["DISTILL", "REGENERATE"])
        return WorkflowGenome(goal, tuple(steps), tuple(required), tuple(r.name for r in residuals))

    def countergenerate(self, candidate: Candidate) -> tuple[dict, ...]:
        return (
            {"kind": "null", "claim": "no structural change is needed", "against": candidate.candidate_id},
            {"kind": "simple-baseline", "claim": f"a simpler representation beats {candidate.representation}", "against": candidate.candidate_id},
            {"kind": "adversarial", "claim": "reported gain is scoring artefact or overfit", "against": candidate.candidate_id},
        )

    def generate_questions(self, residuals: Sequence[Residual]) -> list[QuestionCandidate]:
        out: list[QuestionCandidate] = []
        for r in sorted(residuals, key=lambda x: x.magnitude * (1 + x.uncertainty), reverse=True):
            out.append(QuestionCandidate(
                question=f"Which unmeasured variable most reduces residual '{r.name}'?",
                source_residual=r.name,
                expected_information_gain=r.magnitude * (0.5 + r.uncertainty),
                probe=f"design independent probe for {r.domain}:{r.name}",
            ))
        return out

    def apoptosis(self, object_id: str, ablation_gain: float, regenerable: bool,
                  regeneration_depth: RegenerationDepth, epsilon: float = 0.05) -> ForgetReceipt | None:
        if abs(ablation_gain) <= epsilon and regenerable:
            return ForgetReceipt(object_id, "no verified marginal contribution under ablation", ablation_gain,
                                 True, regeneration_depth)
        return None
