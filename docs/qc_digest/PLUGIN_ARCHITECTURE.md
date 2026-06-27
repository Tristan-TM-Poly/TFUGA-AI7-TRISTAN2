# Plugin Architecture

Issue: #54

Module: `local_digest.pipeline`

## Core interfaces

- `SourceAdapter`: loads local records.
- `DigestStage`: transforms or scores records.
- `Exporter`: writes local artifacts.

## Stable data objects

- `DigestRecord`
- `DigestBundle`
- `ExportResult`

## Built-in local plugins

- `InMemoryAdapter`
- `TopicScoreStage`
- `JsonExporter`
- `MarkdownExporter`

## Pipeline

`run_pipeline(adapter, stages, exporters, output_dir)`

The pipeline loads one bundle, applies stages in order, then runs exporters.

## Boundary

This is a local-first plugin scaffold. It is not a live source connector and does not publish outputs automatically.

## Tests

`tests/test_local_digest_pipeline.py`
