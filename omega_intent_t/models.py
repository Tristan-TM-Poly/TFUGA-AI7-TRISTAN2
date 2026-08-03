from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping


OAK_STATUSES = (
    "PROVEN",
    "MEASURED",
    "SIMULATED",
    "PROTOTYPED",
    "FERTILE",
    "UNCERTAIN",
    "REFUTED",
    "BLOCKED",
)

RISK_LEVELS = ("low", "normal", "elevated", "ip_sensitive", "public", "irreversible")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    value = re.sub(r"[^\w.-]+", "-", value.strip(), flags=re.UNICODE).strip("-._")
    return value or "untitled"


def _tuple_of_strings(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        value = (value,)
    if not isinstance(value, Iterable) or isinstance(value, (bytes, bytearray, Mapping)):
        raise TypeError(f"{field_name} must be a string or iterable of strings")
    normalized = tuple(str(item).strip() for item in value if str(item).strip())
    return tuple(dict.fromkeys(normalized))


@dataclass(frozen=True)
class Intent:
    objective: str
    expected_outputs: tuple[str, ...]
    epistemic_constraints: tuple[str, ...]
    completion_conditions: tuple[str, ...]
    languages: tuple[str, ...] = ("python",)
    mode: str = "expansive"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    intent_id: str = ""

    def __post_init__(self) -> None:
        objective = self.objective.strip()
        if not objective:
            raise ValueError("intent objective cannot be empty")
        if not self.expected_outputs:
            raise ValueError("intent requires at least one expected output")
        if self.mode not in {"focused", "expansive", "frontier"}:
            raise ValueError("mode must be focused, expansive, or frontier")
        object.__setattr__(self, "objective", objective)
        if not self.intent_id:
            object.__setattr__(self, "intent_id", f"INTENT-{stable_digest(self.identity_payload())[:16].upper()}")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "Intent":
        objective = str(raw.get("objective") or raw.get("text") or "").strip()
        outputs = _tuple_of_strings(
            raw.get("expected_outputs")
            or (
                "theory_documents",
                "mathematical_specifications",
                "code",
                "tests",
                "benchmarks",
                "reports",
            ),
            field_name="expected_outputs",
        )
        constraints = _tuple_of_strings(
            raw.get("epistemic_constraints")
            or (
                "distinguish_established_results_from_extensions",
                "no_unverified_performance_claims",
                "compare_against_baselines",
            ),
            field_name="epistemic_constraints",
        )
        conditions = _tuple_of_strings(
            raw.get("completion_conditions")
            or (
                "artifacts_generated",
                "tests_defined",
                "claims_have_evidence_paths",
                "documentation_matches_plan",
                "oak_gate_passes",
            ),
            field_name="completion_conditions",
        )
        languages = _tuple_of_strings(raw.get("languages") or ("python",), field_name="languages")
        metadata = raw.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TypeError("metadata must be an object")
        return cls(
            objective=objective,
            expected_outputs=outputs,
            epistemic_constraints=constraints,
            completion_conditions=conditions,
            languages=languages,
            mode=str(raw.get("mode") or "expansive").strip().lower(),
            metadata=dict(metadata),
            intent_id=str(raw.get("id") or raw.get("intent_id") or "").strip(),
        )

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        languages: Iterable[str] = ("python",),
        mode: str = "expansive",
        expected_outputs: Iterable[str] | None = None,
    ) -> "Intent":
        raw: dict[str, Any] = {
            "objective": text,
            "languages": list(languages),
            "mode": mode,
        }
        if expected_outputs is not None:
            raw["expected_outputs"] = list(expected_outputs)
        return cls.from_mapping(raw)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "expected_outputs": list(self.expected_outputs),
            "epistemic_constraints": list(self.epistemic_constraints),
            "completion_conditions": list(self.completion_conditions),
            "languages": list(self.languages),
            "mode": self.mode,
            "metadata": dict(self.metadata),
        }

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.intent_id, **self.identity_payload()}


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    statement: str
    category: str
    verification_method: str
    acceptance: tuple[str, ...]
    source_intent_id: str
    risk: str = "normal"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["acceptance"] = list(self.acceptance)
        return payload


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    status: str
    evidence_required: tuple[str, ...]
    source_requirement_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in OAK_STATUSES:
            raise ValueError(f"unknown OAK status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_required"] = list(self.evidence_required)
        payload["source_requirement_ids"] = list(self.source_requirement_ids)
        return payload


@dataclass(frozen=True)
class WorkUnit:
    work_unit_id: str
    kind: str
    objective: str
    requirement_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    outputs: tuple[str, ...]
    validations: tuple[str, ...]
    language: str | None = None
    risk: str = "normal"
    generator: str = "deterministic_template"
    status: str = "planned"

    def __post_init__(self) -> None:
        if self.risk not in RISK_LEVELS:
            raise ValueError(f"unknown risk level: {self.risk}")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("requirement_ids", "dependency_ids", "outputs", "validations"):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class GeneratorSpec:
    generator_id: str
    generator_type: str
    work_unit_id: str
    template: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    parameters: Mapping[str, Any]
    claim_boundary: str = "scaffold_or_plan_not_validated_result"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["inputs"] = list(self.inputs)
        payload["outputs"] = list(self.outputs)
        payload["parameters"] = dict(self.parameters)
        return payload


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    label: str
    data: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.node_id,
            "type": self.node_type,
            "label": self.label,
            "data": dict(self.data),
        }


@dataclass(frozen=True)
class GraphEdge:
    source: str
    relation: str
    target: str
    data: Mapping[str, Any] = field(default_factory=dict)

    @property
    def edge_id(self) -> str:
        return f"EDGE-{stable_digest((self.source, self.relation, self.target, dict(self.data)))[:16].upper()}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.edge_id,
            "source": self.source,
            "relation": self.relation,
            "target": self.target,
            "data": dict(self.data),
        }


@dataclass(frozen=True)
class OakCheck:
    check_id: str
    passed: bool
    message: str
    evidence: tuple[str, ...] = ()
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = list(self.evidence)
        return payload


@dataclass(frozen=True)
class OakReport:
    intent_id: str
    passed: bool
    checks: tuple[OakCheck, ...]
    warnings: tuple[str, ...]
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False
    remote_mutations: int = 0
    automatic_merge: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "passed": self.passed,
            "checks": [check.to_dict() for check in self.checks],
            "warnings": list(self.warnings),
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": self.formal_proof_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
            "remote_mutations": self.remote_mutations,
            "automatic_merge": self.automatic_merge,
        }
