from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ArtifactType(str, Enum):
    THEOREM = "theorem"
    PROOF = "proof"
    BENCHMARK = "benchmark"
    LIBRARY = "library"
    CLI = "cli"
    DATASET = "dataset"
    EXPERIMENT = "experiment"
    PAPER = "paper"
    PATENT_CANDIDATE = "patent_candidate"
    API = "api"
    SERVICE = "service"
    PRODUCT = "product"
    PROTOTYPE = "prototype"


@dataclass(frozen=True)
class CrystallizationRecord:
    artifact_type: ArtifactType
    spec: str
    implementation: str
    test: str
    baseline: str
    result: str
    provenance: str
    limitations: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["artifact_type"] = self.artifact_type.value
        return data


@dataclass(frozen=True)
class CrystallizationReport:
    is_clear: bool
    missing: tuple[str, ...]
    record: CrystallizationRecord | None = None


_REQUIRED = ("spec", "implementation", "test", "baseline", "result", "provenance", "limitations")


def validate_crystallization(payload: dict[str, Any]) -> CrystallizationReport:
    missing = tuple(name for name in _REQUIRED if not str(payload.get(name, "")).strip())
    raw_type = str(payload.get("artifact_type", ArtifactType.PROTOTYPE.value))
    try:
        artifact_type = ArtifactType(raw_type)
    except ValueError:
        missing = tuple((*missing, "artifact_type(valid)"))
        return CrystallizationReport(False, missing)
    if missing:
        return CrystallizationReport(False, missing)
    record = CrystallizationRecord(
        artifact_type=artifact_type,
        spec=str(payload["spec"]),
        implementation=str(payload["implementation"]),
        test=str(payload["test"]),
        baseline=str(payload["baseline"]),
        result=str(payload["result"]),
        provenance=str(payload["provenance"]),
        limitations=str(payload["limitations"]),
    )
    return CrystallizationReport(True, (), record)
