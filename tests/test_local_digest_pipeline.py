from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from local_digest.pipeline import (
    DigestBundle,
    DigestRecord,
    ExportResult,
    InMemoryAdapter,
    JsonExporter,
    MarkdownExporter,
    TopicScoreStage,
    run_pipeline,
)


def sample_records() -> list[DigestRecord]:
    return [
        DigestRecord(
            record_id="r1",
            record_type="publication",
            title="Generated local workflow study",
            year=2026,
            source="fixture",
            topics=("automation", "workflow"),
        ),
        DigestRecord(
            record_id="r2",
            record_type="invention_record",
            title="Generated manifest system",
            year=2026,
            source="fixture",
            topics=("manifest",),
        ),
    ]


def test_memory_adapter_loads_stable_bundle() -> None:
    adapter = InMemoryAdapter(records=sample_records(), name="fixture")
    bundle = adapter.load()

    assert isinstance(bundle, DigestBundle)
    assert len(bundle.records) == 2
    assert bundle.metadata["adapter"] == "fixture"


def test_stage_can_be_plugged_without_changing_pipeline() -> None:
    adapter = InMemoryAdapter(records=sample_records())
    bundle = TopicScoreStage().run(adapter.load())

    assert bundle.metadata["stage"] == "topic_score"
    assert all("topic_score" in record.data for record in bundle.records)


def test_json_and_markdown_exporters(tmp_path) -> None:
    results = run_pipeline(
        InMemoryAdapter(records=sample_records()),
        stages=[TopicScoreStage()],
        exporters=[JsonExporter(), MarkdownExporter()],
        output_dir=tmp_path,
    )

    assert [result.format for result in results] == ["json", "markdown"]
    json_payload = json.loads((tmp_path / "digest_records.json").read_text(encoding="utf-8"))
    md_payload = (tmp_path / "digest_report.md").read_text(encoding="utf-8")

    assert len(json_payload["records"]) == 2
    assert "Generated local workflow study" in md_payload


def test_custom_exporter_can_be_plugged_in(tmp_path) -> None:
    @dataclass(frozen=True)
    class CountExporter:
        name: str = "count"
        output_format: str = "txt"

        def export(self, bundle: DigestBundle, output_dir: str | Path) -> ExportResult:
            path = Path(output_dir) / "count.txt"
            path.write_text(str(len(bundle.records)), encoding="utf-8")
            return ExportResult(path=str(path), format=self.output_format, record_count=len(bundle.records))

    results = run_pipeline(InMemoryAdapter(records=sample_records()), exporters=[CountExporter()], output_dir=tmp_path)

    assert results[0].record_count == 2
    assert (tmp_path / "count.txt").read_text(encoding="utf-8") == "2"
