"""Batch processing and report writing for Daily Omega signals.

This module turns a folder of portable signal JSON files into a ranked Daily
Omega War Room report plus machine-readable decision exports. It is local and
side-effect limited: it reads files and optionally writes local output files,
but never calls GitHub or publishes anything.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from sage_tristan.daily_omega_briefing import BriefingItem, rank_items, render_markdown
from sage_tristan.daily_omega_io import export_decision_dict, load_item_json
from sage_tristan.daily_omega_router import render_war_room_markdown

SIGNAL_REQUIRED_KEYS = frozenset(
    {
        "title",
        "topic_anchor",
        "why_it_matters",
        "actionable_opportunity",
        "oak_check",
        "sources",
        "next_action",
        "scores",
    }
)
METADATA_FILE_NAMES = frozenset({"manifest.json", "metadata.json", "index.json"})


@dataclass(frozen=True)
class BatchResult:
    """Ranked items and reusable exports from a Daily Omega batch."""

    items: tuple[BriefingItem, ...]
    markdown_report: str
    decisions: tuple[dict, ...]

    def decisions_json(self, *, indent: int = 2) -> str:
        return json.dumps(list(self.decisions), indent=indent, ensure_ascii=False)


def is_signal_json_file(path: str | Path) -> bool:
    """Return whether a JSON file appears to be a Daily Omega signal.

    Dated signal directories can contain metadata files such as `manifest.json`.
    Those files must not be loaded as signals. A valid signal needs the minimal
    portable signal contract, otherwise it is skipped as metadata.
    """

    file_path = Path(path)
    if file_path.name in METADATA_FILE_NAMES or not file_path.is_file() or file_path.suffix != ".json":
        return False
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and SIGNAL_REQUIRED_KEYS.issubset(payload.keys())


def discover_signal_files(directory: str | Path) -> list[Path]:
    """Return JSON signal files from a directory in deterministic order."""

    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"signal directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"signal path is not a directory: {root}")
    return sorted(path for path in root.glob("*.json") if is_signal_json_file(path))


def load_items_from_directory(directory: str | Path) -> list[BriefingItem]:
    """Load all portable Daily Omega JSON signals from a directory."""

    files = discover_signal_files(directory)
    if not files:
        raise ValueError(f"no JSON signal files found in {directory}")
    return [load_item_json(path) for path in files]


def build_batch_result(
    items: Iterable[BriefingItem],
    *,
    briefing_date: date,
    timezone: str = "Europe/Berlin",
    limit: int = 5,
    dry_run: bool = True,
) -> BatchResult:
    """Rank items and create Markdown plus JSON-safe supervision exports."""

    ranked = tuple(rank_items(list(items), limit=limit))
    briefing = render_markdown(briefing_date, timezone, ranked)
    war_room = render_war_room_markdown(ranked)
    markdown_report = briefing.rstrip() + "\n\n---\n\n" + war_room
    decisions = tuple(export_decision_dict(item, dry_run=dry_run) for item in ranked)
    return BatchResult(items=ranked, markdown_report=markdown_report, decisions=decisions)


def build_batch_from_directory(
    directory: str | Path,
    *,
    briefing_date: date,
    timezone: str = "Europe/Berlin",
    limit: int = 5,
    dry_run: bool = True,
) -> BatchResult:
    """Load a directory of signal JSON files and build a ranked batch result."""

    return build_batch_result(
        load_items_from_directory(directory),
        briefing_date=briefing_date,
        timezone=timezone,
        limit=limit,
        dry_run=dry_run,
    )


def write_batch_outputs(
    result: BatchResult,
    output_directory: str | Path,
    *,
    stem: str,
) -> tuple[Path, Path]:
    """Write Markdown report and JSON decisions to `output_directory`.

    Returns `(markdown_path, json_path)`.
    """

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    markdown_path = output / f"{stem}.md"
    json_path = output / f"{stem}.decisions.json"
    markdown_path.write_text(result.markdown_report, encoding="utf-8")
    json_path.write_text(result.decisions_json(), encoding="utf-8")
    return markdown_path, json_path


def summarize_batch(result: BatchResult) -> str:
    """Return a compact console summary for a batch result."""

    lines = [f"Daily Omega batch: {len(result.items)} ranked item(s)"]
    for item in result.items:
        rank = item.rank if item.rank is not None else "?"
        lines.append(f"{rank}. {item.title} — score {item.final_score}")
    return "\n".join(lines) + "\n"


__all__ = [
    "BatchResult",
    "SIGNAL_REQUIRED_KEYS",
    "build_batch_from_directory",
    "build_batch_result",
    "discover_signal_files",
    "is_signal_json_file",
    "load_items_from_directory",
    "summarize_batch",
    "write_batch_outputs",
]
