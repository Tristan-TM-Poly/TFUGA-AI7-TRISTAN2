from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .models import GeneratorSpec, Intent, Requirement, WorkUnit, stable_digest, slugify


@dataclass(frozen=True)
class GeneratedArtifact:
    path: str
    content: str
    media_type: str
    status: str = "generated_scaffold"

    @property
    def sha256(self) -> str:
        return stable_digest(self.content)

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "media_type": self.media_type,
            "status": self.status,
            "sha256": self.sha256,
        }


class MetaGenerator:
    """Compile work units into explicit generator recipes before materialization."""

    def compile(self, work_units: Sequence[WorkUnit]) -> tuple[GeneratorSpec, ...]:
        specs: list[GeneratorSpec] = []
        for unit in work_units:
            generator_type = {
                "implementation": "source_scaffold_generator",
                "test": "test_contract_generator",
                "benchmark": "benchmark_contract_generator",
                "document": "document_generator",
                "specification": "specification_generator",
                "architecture": "architecture_generator",
                "report": "report_generator",
            }.get(unit.kind, "artifact_manifest_generator")
            specs.append(GeneratorSpec(
                generator_id=f"GEN-{stable_digest((unit.work_unit_id, generator_type))[:16].upper()}",
                generator_type=generator_type,
                work_unit_id=unit.work_unit_id,
                template=f"omega-intent/{generator_type}/v1",
                inputs=tuple(unit.requirement_ids),
                outputs=tuple(unit.outputs),
                parameters={
                    "language": unit.language,
                    "validations": list(unit.validations),
                    "risk": unit.risk,
                    "status": "scaffold_not_implementation" if unit.kind == "implementation" else "planned_artifact",
                },
            ))
        return tuple(specs)


class DocumentGenerator:
    def generate(
        self,
        intent: Intent,
        requirements: Sequence[Requirement],
        work_units: Sequence[WorkUnit],
        batches: Sequence[Sequence[str]],
    ) -> tuple[GeneratedArtifact, ...]:
        req_lines = "\n".join(
            f"- `{item.requirement_id}` — {item.statement}  \n  Verification: `{item.verification_method}`"
            for item in requirements
        )
        work_lines = "\n".join(
            f"- `{item.work_unit_id}` [{item.kind}] {item.objective} → {', '.join(item.outputs)}"
            for item in work_units
        )
        batch_lines = "\n".join(
            f"{index}. {', '.join(batch)}" for index, batch in enumerate(batches, start=1)
        )
        outputs = "\n".join(f"- `{output}`" for output in intent.expected_outputs)
        constraints = "\n".join(f"- `{constraint}`" for constraint in intent.epistemic_constraints)
        completion = "\n".join(f"- `{condition}`" for condition in intent.completion_conditions)
        docs = {
            "documents/intention.md": f"""# Intention {intent.intent_id}

## Objective

{intent.objective}

## Expected outputs

{outputs}

## Languages

{', '.join(intent.languages)}

## Mode

`{intent.mode}`
""",
            "documents/requirements.md": f"""# Executable requirements

{req_lines}
""",
            "documents/architecture.md": f"""# Ω-INTENT-TO-EVERYTHING-T∞ architecture

```text
intent
→ normalized contract
→ executable documents
→ evidence hypergraph
→ dependency-aware work units
→ generator specifications
→ generated artifacts and addition stream
→ OAK validation
→ detailed reports
→ corrective next intent
```

## Work units

{work_lines}

## Topological execution batches

{batch_lines}
""",
            "documents/acceptance_criteria.md": f"""# Acceptance criteria

## Epistemic constraints

{constraints}

## Completion conditions

{completion}

Completion is relative to the accepted scope. Unresolved, blocked and refuted items remain explicit residuals.
""",
            "documents/risk_register.md": """# Risk register

| Risk | Default control |
|---|---|
| Generated volume without value | OAK evidence and marginal-value gates |
| Duplicate artifacts | Stable hashes and semantic deduplication |
| Unsupported scientific claims | Explicit OAK status and evidence path |
| Dependency cycles | DAG validation before execution |
| IP disclosure | IP-sensitive work requires human approval |
| Irreversible GitHub mutation | Dry-run plans and explicit authorization gates |
| Resource saturation | Adaptive sharding, checkpoints and backpressure |
""",
        }
        return tuple(
            GeneratedArtifact(path=path, content=content.rstrip() + "\n", media_type="text/markdown")
            for path, content in docs.items()
        )


class ScaffoldGenerator:
    """Generate reviewable scaffolds, never pretend they are completed implementations."""

    def generate(self, intent: Intent, work_units: Sequence[WorkUnit]) -> tuple[GeneratedArtifact, ...]:
        artifacts: list[GeneratedArtifact] = []
        for unit in work_units:
            if unit.kind != "implementation":
                continue
            language = unit.language or "neutral"
            name = slugify(unit.work_unit_id.lower())
            if language == "python":
                path = f"scaffolds/python/{name}.py"
                content = f'''"""Generated scaffold for {unit.work_unit_id}.

Intent: {intent.intent_id}
Status: scaffold only; implementation and scientific claims remain unvalidated.
"""
from __future__ import annotations

WORK_UNIT_ID = "{unit.work_unit_id}"
OAK_STATUS = "FERTILE"


def execute(*args: object, **kwargs: object) -> object:
    """Implementation contract generated from the intent graph."""
    raise NotImplementedError(
        "Generated scaffold: implement, test against baselines, and pass OAK before promotion"
    )
'''
                media_type = "text/x-python"
            elif language == "rust":
                path = f"scaffolds/rust/{name}.rs"
                content = f'''//! Generated scaffold for {unit.work_unit_id}.
//! Status: scaffold only; no validated result is claimed.

pub const WORK_UNIT_ID: &str = "{unit.work_unit_id}";
pub const OAK_STATUS: &str = "FERTILE";

pub fn execute() -> Result<(), &'static str> {{
    Err("Generated scaffold: implementation and OAK validation required")
}}
'''
                media_type = "text/x-rust"
            elif language in {"cpp", "c++"}:
                path = f"scaffolds/cpp/{name}.cpp"
                content = f'''// Generated scaffold for {unit.work_unit_id}.
// Status: scaffold only; no validated result is claimed.
#include <stdexcept>
#include <string_view>

constexpr std::string_view WORK_UNIT_ID = "{unit.work_unit_id}";
constexpr std::string_view OAK_STATUS = "FERTILE";

void execute() {{
    throw std::logic_error("Generated scaffold: implementation and OAK validation required");
}}
'''
                media_type = "text/x-c++src"
            elif language == "c":
                path = f"scaffolds/c/{name}.c"
                content = f'''/* Generated scaffold for {unit.work_unit_id}.
 * Status: scaffold only; no validated result is claimed.
 */
#include <stddef.h>

const char *OMEGA_WORK_UNIT_ID = "{unit.work_unit_id}";
const char *OMEGA_OAK_STATUS = "FERTILE";

int omega_execute(void) {{
    return -1; /* implementation and OAK validation required */
}}
'''
                media_type = "text/x-c"
            else:
                path = f"scaffolds/{slugify(language)}/{name}.txt"
                content = (
                    f"work_unit_id={unit.work_unit_id}\n"
                    f"language={language}\n"
                    "status=scaffold_only\n"
                    "next=implement_test_benchmark_oak\n"
                )
                media_type = "text/plain"
            artifacts.append(GeneratedArtifact(path=path, content=content, media_type=media_type))
        return tuple(artifacts)


def addition_records(
    intent: Intent,
    requirements: Sequence[Requirement],
    work_units: Sequence[WorkUnit],
    generators: Sequence[GeneratorSpec],
    artifacts: Sequence[GeneratedArtifact],
) -> Iterable[dict[str, Any]]:
    provenance = [f"intent:{intent.intent_id}"]
    for requirement in requirements:
        yield {
            "addition_id": requirement.requirement_id,
            "namespace": "omega-intent/requirements",
            "kind": "requirement",
            "payload": requirement.to_dict(),
            "provenance": provenance,
            "risk": requirement.risk,
        }
    for unit in work_units:
        yield {
            "addition_id": unit.work_unit_id,
            "namespace": f"omega-intent/work/{unit.kind}",
            "kind": "work_unit",
            "payload": unit.to_dict(),
            "provenance": [*provenance, *[f"requirement:{rid}" for rid in unit.requirement_ids]],
            "risk": unit.risk,
        }
    for spec in generators:
        yield {
            "addition_id": spec.generator_id,
            "namespace": f"omega-intent/generators/{spec.generator_type}",
            "kind": "generator_spec",
            "payload": spec.to_dict(),
            "provenance": [*provenance, f"work_unit:{spec.work_unit_id}"],
            "risk": str(spec.parameters.get("risk", "normal")),
        }
    for artifact in artifacts:
        yield {
            "addition_id": f"ART-{artifact.sha256[:16].upper()}",
            "namespace": "omega-intent/artifacts",
            "kind": "generated_artifact",
            "payload": artifact.to_dict(),
            "provenance": provenance,
            "risk": "normal",
        }
