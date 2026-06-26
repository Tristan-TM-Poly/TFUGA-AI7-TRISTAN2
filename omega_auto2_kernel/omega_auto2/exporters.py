from __future__ import annotations

import json

from .bench import run_suite
from .models import Workflow
from .report import build_markdown_report
from .telemetry import TelemetrySnapshot


def suite_json(workflows: list[Workflow], telemetry: TelemetrySnapshot | None = None) -> str:
    return json.dumps(run_suite(workflows, telemetry), ensure_ascii=False, indent=2)


def suite_markdown(workflows: list[Workflow], telemetry: TelemetrySnapshot | None = None) -> str:
    return build_markdown_report(workflows, telemetry)
