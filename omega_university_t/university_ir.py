from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable, Mapping, Sequence


class CurriculumError(ValueError):
    """Raised when a curriculum dependency request is not safely compilable."""


@dataclass(frozen=True)
class CurriculumPlan:
    targets: tuple[str, ...]
    already_verified: tuple[str, ...]
    missing: tuple[str, ...]
    ordered: tuple[str, ...]
    authority: str = "PLAN_ONLY"
    external_action_authorized: bool = False
    credential_awarded: bool = False
    scientific_claim_proven: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalized_graph(
    graph: Mapping[str, Sequence[str] | Iterable[str]],
) -> dict[str, tuple[str, ...]]:
    normalized: dict[str, tuple[str, ...]] = {}
    for capability_id, prerequisites in graph.items():
        if not isinstance(capability_id, str) or not capability_id.strip():
            raise CurriculumError("capability identifiers must be non-empty strings")
        clean = tuple(sorted({str(p).strip() for p in prerequisites if str(p).strip()}))
        if capability_id in clean:
            raise CurriculumError(f"self-cycle detected for {capability_id!r}")
        normalized[capability_id] = clean
    return normalized


def compile_curriculum(
    graph: Mapping[str, Sequence[str] | Iterable[str]],
    targets: Iterable[str],
    verified: Iterable[str] = (),
) -> CurriculumPlan:
    """Compile a deterministic prerequisite plan for missing target capabilities.

    The function is deliberately conservative. It plans dependency traversal only;
    it does not teach, assess, award credentials, or authorize external actions.
    """

    normalized = _normalized_graph(graph)
    target_set = {str(target).strip() for target in targets if str(target).strip()}
    verified_set = {str(cap).strip() for cap in verified if str(cap).strip()}

    if not target_set:
        raise CurriculumError("at least one target capability is required")

    unknown_targets = sorted(target_set.difference(normalized))
    if unknown_targets:
        raise CurriculumError(f"unknown target capabilities: {unknown_targets}")

    order: list[str] = []
    permanent: set[str] = set()
    temporary: set[str] = set()
    encountered_verified: set[str] = set()

    def visit(capability_id: str) -> None:
        if capability_id in verified_set:
            encountered_verified.add(capability_id)
            return
        if capability_id in permanent:
            return
        if capability_id in temporary:
            raise CurriculumError(f"cycle detected at {capability_id!r}")
        if capability_id not in normalized:
            raise CurriculumError(
                f"unresolved prerequisite {capability_id!r}; "
                "declare it in the graph or provide it as already verified"
            )

        temporary.add(capability_id)
        for prerequisite in normalized[capability_id]:
            visit(prerequisite)
        temporary.remove(capability_id)
        permanent.add(capability_id)
        order.append(capability_id)

    for target in sorted(target_set):
        visit(target)

    ordered = tuple(order)
    return CurriculumPlan(
        targets=tuple(sorted(target_set)),
        already_verified=tuple(sorted(encountered_verified)),
        missing=ordered,
        ordered=ordered,
    )


def make_receipt(plan: CurriculumPlan, *, graph_version: str) -> dict[str, object]:
    """Return a deterministic proof-carrying planning receipt.

    The SHA-256 binds only the serialized planning payload. It is provenance for
    software state, not proof of educational effectiveness or credential validity.
    """

    if not graph_version.strip():
        raise CurriculumError("graph_version must be a non-empty string")

    payload = {
        "kind": "omega.university.curriculum-plan.r0.1",
        "graph_version": graph_version,
        "plan": plan.to_dict(),
        "boundaries": {
            "generated_is_verified": False,
            "plan_is_learning": False,
            "learning_is_credential": False,
            "external_action_authorized": False,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {
        **payload,
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }
