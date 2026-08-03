from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .hashing import sha256_hex, stable_id
from .models import (
    ConstraintSpec,
    EvidenceStatus,
    FrontierCell,
    MetamorphicRelation,
    ProvenanceRecord,
    TaskIR,
)


@dataclass(frozen=True)
class TaskTemplate:
    template_id: str
    title_pattern: str
    statement_pattern: str
    function_name: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any]
    invariants: tuple[str, ...]
    forbidden_assumptions: tuple[str, ...]
    metamorphic_relations: tuple[MetamorphicRelation, ...]
    skill_dependencies: tuple[str, ...]


DEFAULT_TEMPLATE = TaskTemplate(
    template_id="omega.generic.sequence.v1",
    title_pattern="{archetype} challenge in {domain}",
    statement_pattern=(
        "Construct an original {archetype} algorithm for the {domain} domain. "
        "The implementation target is {language}; evaluation regime is {regime}; "
        "the primary adversarial mutation family is {mutation}."
    ),
    function_name="solve",
    input_schema={"type": "array", "items": {"type": "integer"}},
    output_schema={"type": "integer"},
    invariants=(
        "the output is deterministic for identical inputs",
        "the implementation does not mutate its input unless explicitly declared",
        "all declared boundary cases are handled",
    ),
    forbidden_assumptions=(
        "inputs are non-empty unless constrained",
        "machine integers cannot overflow",
        "iteration order of unordered containers is semantically stable",
    ),
    metamorphic_relations=(
        MetamorphicRelation(
            relation_id="mr.identity-copy",
            description="Copying the input preserves the answer.",
            transformation="deep_copy(input)",
            expectation="output is unchanged",
        ),
        MetamorphicRelation(
            relation_id="mr.replay",
            description="Replaying the same case is deterministic.",
            transformation="repeat(input)",
            expectation="all outputs are equal",
        ),
    ),
    skill_dependencies=("specification", "boundary_analysis", "algorithm_design"),
)


class TaskIRCompiler:
    def __init__(self, template: TaskTemplate = DEFAULT_TEMPLATE) -> None:
        self.template = template

    def compile(
        self,
        cell: FrontierCell,
        provenance: ProvenanceRecord,
        ordinal: int,
    ) -> TaskIR:
        seed = {
            "template_id": self.template.template_id,
            "cell": cell.to_dict(),
            "ordinal": ordinal,
            "source_hash": provenance.content_hash,
        }
        task_id = stable_id("omega-task", seed, length=20)
        difficulty_index = _suffix_index(cell.difficulty_band)
        difficulty = min(1.0, max(0.0, (difficulty_index + 1) / 32.0))
        return TaskIR(
            task_id=task_id,
            version=2,
            title=self.template.title_pattern.format(
                archetype=cell.archetype, domain=cell.domain
            ),
            domain=cell.domain,
            archetype=cell.archetype,
            statement=self.template.statement_pattern.format(
                archetype=cell.archetype,
                domain=cell.domain,
                language=cell.language,
                regime=cell.execution_regime,
                mutation=cell.mutation_family,
            ),
            function_name=self.template.function_name,
            input_schema=dict(self.template.input_schema),
            output_schema=dict(self.template.output_schema),
            constraints=(
                ConstraintSpec("finite-input", "The serialized input must be finite."),
                ConstraintSpec(
                    "resource-accounting",
                    "Runtime and memory measurements must include environment metadata.",
                ),
                ConstraintSpec(
                    "mutation-target",
                    f"Tests should reject the {cell.mutation_family} mutation family.",
                ),
            ),
            invariants=self.template.invariants,
            forbidden_assumptions=self.template.forbidden_assumptions,
            metamorphic_relations=self.template.metamorphic_relations,
            mutation_families=(cell.mutation_family,),
            skill_dependencies=self.template.skill_dependencies
            + (f"domain:{cell.domain}", f"language:{cell.language}"),
            difficulty_vector={
                "conceptual": difficulty,
                "implementation": min(1.0, difficulty * 0.9 + 0.05),
                "proof": min(1.0, difficulty * 0.8 + 0.1),
                "adversarial": min(1.0, difficulty * 0.7 + 0.15),
            },
            provenance=provenance,
            evidence_status=EvidenceStatus.GENERATED,
            tags=(
                cell.domain,
                cell.archetype,
                cell.language,
                cell.execution_regime,
                cell.mutation_family,
            ),
        )

    @staticmethod
    def validate(task: TaskIR) -> tuple[str, ...]:
        errors: list[str] = []
        if task.version < 1:
            errors.append("version must be positive")
        if not task.task_id.startswith("omega-task-"):
            errors.append("task_id must use the omega-task prefix")
        if not task.constraints:
            errors.append("at least one constraint is required")
        if not task.invariants:
            errors.append("at least one invariant is required")
        if not task.mutation_families:
            errors.append("at least one mutation family is required")
        if not task.provenance.content_hash:
            errors.append("provenance content hash is required")
        return tuple(errors)

    @staticmethod
    def digest(task: TaskIR) -> str:
        return sha256_hex(task.to_dict())


def _suffix_index(value: str) -> int:
    try:
        return int(value.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 0
