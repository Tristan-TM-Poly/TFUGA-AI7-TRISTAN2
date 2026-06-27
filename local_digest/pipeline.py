from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol, Sequence


@dataclass(frozen=True)
class DigestRecord:
    record_id: str
    record_type: str
    title: str
    year: int | None = None
    source: str = "local"
    topics: tuple[str, ...] = ()
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DigestBundle:
    records: tuple[DigestRecord, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"records": [record.to_dict() for record in self.records], "metadata": self.metadata}


@dataclass(frozen=True)
class ExportResult:
    path: str
    format: str
    record_count: int


class SourceAdapter(Protocol):
    name: str

    def load(self) -> DigestBundle:
        """Load records from a source into a stable local bundle."""


class DigestStage(Protocol):
    name: str

    def run(self, bundle: DigestBundle) -> DigestBundle:
        """Transform or score a bundle without changing the adapter contract."""


class Exporter(Protocol):
    name: str
    output_format: str

    def export(self, bundle: DigestBundle, output_dir: str | Path) -> ExportResult:
        """Write a local artifact and return a small result object."""


@dataclass(frozen=True)
class InMemoryAdapter:
    records: Sequence[DigestRecord]
    name: str = "memory"

    def load(self) -> DigestBundle:
        return DigestBundle(records=tuple(self.records), metadata={"adapter": self.name})


@dataclass(frozen=True)
class TopicScoreStage:
    name: str = "topic_score"

    def run(self, bundle: DigestBundle) -> DigestBundle:
        scored: list[DigestRecord] = []
        for record in bundle.records:
            score = round(min(1.0, 0.25 + 0.15 * len(record.topics) + 0.05 * len(record.title.split())), 4)
            data = dict(record.data)
            data["topic_score"] = score
            scored.append(
                DigestRecord(
                    record_id=record.record_id,
                    record_type=record.record_type,
                    title=record.title,
                    year=record.year,
                    source=record.source,
                    topics=record.topics,
                    data=data,
                )
            )
        metadata = dict(bundle.metadata)
        metadata["stage"] = self.name
        return DigestBundle(records=tuple(scored), metadata=metadata)


@dataclass(frozen=True)
class JsonExporter:
    name: str = "json"
    output_format: str = "json"
    filename: str = "digest_records.json"

    def export(self, bundle: DigestBundle, output_dir: str | Path) -> ExportResult:
        output_path = Path(output_dir) / self.filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return ExportResult(path=str(output_path), format=self.output_format, record_count=len(bundle.records))


@dataclass(frozen=True)
class MarkdownExporter:
    name: str = "markdown"
    output_format: str = "markdown"
    filename: str = "digest_report.md"

    def export(self, bundle: DigestBundle, output_dir: str | Path) -> ExportResult:
        output_path = Path(output_dir) / self.filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Local Digest Report", "", f"Records: {len(bundle.records)}", ""]
        for record in bundle.records:
            year = record.year if record.year is not None else "unknown"
            topics = ", ".join(record.topics) if record.topics else "none"
            lines.append(f"- **{record.title}** ({year}) — {record.record_type}; topics: {topics}")
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return ExportResult(path=str(output_path), format=self.output_format, record_count=len(bundle.records))


def run_pipeline(
    adapter: SourceAdapter,
    stages: Sequence[DigestStage] = (),
    exporters: Sequence[Exporter] = (),
    output_dir: str | Path = "outputs/local_digest",
) -> list[ExportResult]:
    bundle = adapter.load()
    for stage in stages:
        bundle = stage.run(bundle)
    return [exporter.export(bundle, output_dir) for exporter in exporters]
