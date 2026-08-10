from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from omega_intent_t.models import WorkUnit

from .core import Capability, Intent, stable_digest


def _artifact_token(path: str) -> str:
    return f"artifact:{path}"


def _validation_token(name: str) -> str:
    return f"validation:{name}"


def _dependency_token(work_unit_id: str) -> str:
    return f"dependency:{work_unit_id}:complete"


def _default_authority(work_unit: WorkUnit) -> str:
    if work_unit.risk == "irreversible":
        return "irreversible"
    if work_unit.risk in {"elevated", "public"}:
        return "write"
    return "draft"


@dataclass(frozen=True)
class WorkUnitBridge:
    work_unit_id: str
    intent: Intent
    capabilities: tuple[Capability, ...]
    artifact_tokens: tuple[str, ...]
    validation_tokens: tuple[str, ...]
    dependency_tokens: tuple[str, ...]
    initial_values: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "omega-capability-workunit-bridge/v1",
            "work_unit_id": self.work_unit_id,
            "intent": {
                "intent_id": self.intent.intent_id,
                "available_inputs": list(self.intent.available_inputs),
                "required_outputs": list(self.intent.required_outputs),
                "domains": list(self.intent.domains),
                "allow_mutation": self.intent.allow_mutation,
                "allow_irreversible": self.intent.allow_irreversible,
                "max_steps": self.intent.max_steps,
            },
            "capabilities": [
                {
                    "id": cap.capability_id,
                    "domains": list(cap.domains),
                    "consumes": list(cap.consumes),
                    "produces": list(cap.produces),
                    "authority": cap.authority,
                    "alternatives": list(cap.alternatives),
                    "failure_modes": list(cap.failure_modes),
                }
                for cap in self.capabilities
            ],
            "artifact_tokens": list(self.artifact_tokens),
            "validation_tokens": list(self.validation_tokens),
            "dependency_tokens": list(self.dependency_tokens),
            "initial_values": dict(self.initial_values),
        }


def workunit_from_mapping(raw: Mapping[str, Any]) -> WorkUnit:
    return WorkUnit(
        work_unit_id=str(raw["work_unit_id"]),
        kind=str(raw["kind"]),
        objective=str(raw["objective"]),
        requirement_ids=tuple(map(str, raw.get("requirement_ids", []))),
        dependency_ids=tuple(map(str, raw.get("dependency_ids", []))),
        outputs=tuple(map(str, raw.get("outputs", []))),
        validations=tuple(map(str, raw.get("validations", []))),
        language=str(raw["language"]) if raw.get("language") is not None else None,
        risk=str(raw.get("risk", "normal")),
        generator=str(raw.get("generator", "deterministic_template")),
        status=str(raw.get("status", "planned")),
    )


def compile_workunit(
    work_unit: WorkUnit,
    *,
    completed_dependencies: Iterable[str] = (),
    allow_mutation: bool = False,
    allow_irreversible: bool = False,
    authority: str | None = None,
) -> WorkUnitBridge:
    completed = set(map(str, completed_dependencies))
    artifact_tokens = tuple(_artifact_token(path) for path in work_unit.outputs)
    validation_tokens = tuple(_validation_token(name) for name in work_unit.validations)
    dependency_tokens = tuple(_dependency_token(dep) for dep in work_unit.dependency_ids)
    spec_token = f"workunit:{work_unit.work_unit_id}:spec"
    complete_token = f"workunit:{work_unit.work_unit_id}:complete"

    available = [spec_token]
    available.extend(_dependency_token(dep) for dep in work_unit.dependency_ids if dep in completed)
    initial_values: dict[str, Any] = {spec_token: work_unit.to_dict()}
    for dep in work_unit.dependency_ids:
        if dep in completed:
            initial_values[_dependency_token(dep)] = {"work_unit_id": dep, "status": "complete"}

    execution_authority = authority or _default_authority(work_unit)
    generator_id = f"workunit.generate.{work_unit.work_unit_id}"
    generator = Capability(
        capability_id=generator_id,
        domains=("workunit", work_unit.kind, *(("lang:" + work_unit.language,) if work_unit.language else ())),
        consumes=(spec_token, *dependency_tokens),
        produces=artifact_tokens or (complete_token,),
        authority=execution_authority,
        quality=0.75,
        information_gain=0.55,
        verifiability=0.70,
        reuse=0.80,
        cost=0.40,
        latency=0.40,
        risk=0.75 if execution_authority in {"write", "irreversible"} else 0.25,
        failure_modes=("generator_failure", "dependency_missing", "declared_output_missing"),
    )

    validators: list[Capability] = []
    validator_input = artifact_tokens or (complete_token,)
    for index, validation in enumerate(work_unit.validations, start=1):
        validators.append(
            Capability(
                capability_id=f"workunit.validate.{work_unit.work_unit_id}.{index:03d}.{stable_digest(validation)[:8]}",
                domains=("workunit", "validation", work_unit.kind),
                consumes=validator_input,
                produces=(_validation_token(validation),),
                authority="read",
                quality=0.80,
                information_gain=0.70,
                verifiability=0.90,
                reuse=0.70,
                cost=0.25,
                latency=0.25,
                risk=0.10,
                failure_modes=("validator_failure", "artifact_unavailable"),
            )
        )

    required = (*artifact_tokens, *validation_tokens)
    if not required:
        required = (complete_token,)

    intent = Intent(
        intent_id=f"CAP-{work_unit.work_unit_id}",
        available_inputs=tuple(available),
        required_outputs=tuple(required),
        domains=("workunit", work_unit.kind),
        allow_mutation=allow_mutation,
        allow_irreversible=allow_irreversible,
        max_steps=max(4, 1 + len(validators) + len(work_unit.dependency_ids)),
    )
    return WorkUnitBridge(
        work_unit_id=work_unit.work_unit_id,
        intent=intent,
        capabilities=(generator, *validators),
        artifact_tokens=artifact_tokens,
        validation_tokens=validation_tokens,
        dependency_tokens=dependency_tokens,
        initial_values=initial_values,
    )
