"""Dashboard helpers for Daily Omega Intelligence OS.

This module converts compiled SignalGenome++ objects into compact dashboard
exports. It is local-only: no network calls, no GitHub calls, and no public
issue creation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from sage_tristan.daily_omega_batch import build_batch_from_directory
from sage_tristan.daily_omega_intelligence_os import SignalGenome, build_daily_dashboard


@dataclass(frozen=True)
class DashboardResult:
    """Dashboard plus the genomes it was derived from."""

    briefing_date: date
    timezone: str
    dashboard: dict[str, Any]
    genomes: tuple[SignalGenome, ...]

    def dashboard_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.dashboard, indent=indent, ensure_ascii=False)

    def genomes_json(self, *, indent: int = 2) -> str:
        return json.dumps([genome.to_dict() for genome in self.genomes], indent=indent, ensure_ascii=False)


def build_dashboard_result(
    genomes: Iterable[SignalGenome],
    *,
    briefing_date: date,
    timezone: str,
) -> DashboardResult:
    """Build a dashboard result from already compiled genomes."""

    genome_tuple = tuple(genomes)
    return DashboardResult(
        briefing_date=briefing_date,
        timezone=timezone,
        dashboard=build_daily_dashboard(genome_tuple),
        genomes=genome_tuple,
    )


def build_dashboard_from_directory(
    directory: str,
    *,
    briefing_date: date,
    timezone: str,
    limit: int = 5,
    dry_run: bool = True,
) -> DashboardResult:
    """Load a signal directory, compile genomes, and return a dashboard result."""

    batch = build_batch_from_directory(
        directory,
        briefing_date=briefing_date,
        timezone=timezone,
        limit=limit,
        dry_run=dry_run,
    )
    return build_dashboard_result(batch.genomes, briefing_date=briefing_date, timezone=timezone)


def render_dashboard_markdown(result: DashboardResult) -> str:
    """Render the compact Daily Omega dashboard as Markdown."""

    lines = [
        f"# Daily Ω Dashboard — {result.briefing_date.isoformat()}",
        "",
        f"Timezone: `{result.timezone}`",
        "",
        "## Strategic compression",
        "",
    ]
    for key, value in result.dashboard.items():
        lines.append(f"- **{key}:** {value if value is not None else 'None'}")
    lines.extend(["", "## Genome count", "", f"{len(result.genomes)} compiled SignalGenome++ object(s).", ""])
    return "\n".join(lines)


__all__ = [
    "DashboardResult",
    "build_dashboard_from_directory",
    "build_dashboard_result",
    "render_dashboard_markdown",
]
