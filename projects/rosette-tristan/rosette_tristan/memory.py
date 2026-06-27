from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass
class RosetteMemory:
    validated_patterns: list[str] = field(default_factory=list)
    failure_patterns: list[str] = field(default_factory=list)
    repair_hints: list[str] = field(default_factory=list)

    def add_success(self, pattern: str) -> None:
        if pattern not in self.validated_patterns:
            self.validated_patterns.append(pattern)

    def add_failure(self, pattern: str, repair_hint: str | None = None) -> None:
        if pattern not in self.failure_patterns:
            self.failure_patterns.append(pattern)
        if repair_hint and repair_hint not in self.repair_hints:
            self.repair_hints.append(repair_hint)

    def to_dict(self) -> dict:
        return asdict(self)

    def write(self, out: str | Path) -> None:
        Path(out).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def default_rosette_memory() -> RosetteMemory:
    memory = RosetteMemory()
    memory.add_success("page markers preserve source refs in text fixtures")
    memory.add_success("equation dedup works for repeated display math spans")
    memory.add_failure("equation without page ref", "use PDF page extraction or page markers")
    memory.add_failure("claim without evidence", "build claim-evidence links before certification")
    memory.add_failure("figure data unavailable", "mark reproduction_status as missing_data")
    memory.add_failure("OCR hallucinated reference", "cross-check DOI or bibliography source")
    return memory
