"""Source verification helpers for Daily Omega Intelligence OS.

This module extracts source-verification gaps from compiled SignalGenome++
objects. It is local-only: no network calls, no GitHub calls, no issue creation,
and no canon promotion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from sage_tristan.daily_omega_batch import DEFAULT_TIMEZONE, build_batch_from_directory
from sage_tristan.daily_omega_intelligence_os import SignalGenome

UNVERIFIED_SOURCE_STATUSES = frozenset({"source_placeholder", "source_required", "source_found"})


@dataclass(frozen=True)
class VerificationGap:
    """One source or OAK blocker that must be resolved before promotion."""

    signal_title: str
    source_title: str
    source_type: str
    url_or_identifier: str
    verification_status: str
    residue: str
    blocking: bool
    next_check: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_title": self.signal_title,
            "source_title": self.source_title,
            "source_type": self.source_type,
            "url_or_identifier": self.url_or_identifier,
            "verification_status": self.verification_status,
            "residue": self.residue,
            "blocking": self.blocking,
            "next_check": self.next_check,
        }


@dataclass(frozen=True)
class VerificationResult:
    """Source verification report for a Daily Omega batch."""

    briefing_date: date
    timezone: str
    gaps: tuple[VerificationGap, ...]
    checked_signals: int

    @property
    def is_clear(self) -> bool:
        return not any(gap.blocking for gap in self.gaps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "briefing_date": self.briefing_date.isoformat(),
            "timezone": self.timezone,
            "checked_signals": self.checked_signals,
            "is_clear": self.is_clear,
            "gaps": [gap.to_dict() for gap in self.gaps],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def next_source_check(status: str, identifier: str) -> str:
    """Return the next verification action for a source status."""

    if status == "source_placeholder" or identifier.startswith("source_required:"):
        return "Replace placeholder with a primary source or credible secondary source."
    if status == "source_required":
        return "Find a stronger source and corroborate the claim before promotion."
    if status == "source_found":
        return "Corroborate with another credible source or primary artifact."
    return "Record source as reviewed; keep normal OAK residue tracking."


def find_source_gaps(genome: SignalGenome) -> tuple[VerificationGap, ...]:
    """Return source-verification gaps for one genome."""

    gaps: list[VerificationGap] = []
    for entry in genome.source_ledger:
        if entry.verification_status in UNVERIFIED_SOURCE_STATUSES:
            gaps.append(
                VerificationGap(
                    signal_title=genome.title,
                    source_title=entry.title,
                    source_type=entry.source_type,
                    url_or_identifier=entry.url_or_identifier,
                    verification_status=entry.verification_status,
                    residue=entry.residue,
                    blocking=entry.verification_status in {"source_placeholder", "source_required"},
                    next_check=next_source_check(entry.verification_status, entry.url_or_identifier),
                )
            )
    return tuple(gaps)


def build_verification_result(
    genomes: Iterable[SignalGenome],
    *,
    briefing_date: date,
    timezone: str = DEFAULT_TIMEZONE,
) -> VerificationResult:
    """Build a source verification report from compiled genomes."""

    genome_tuple = tuple(genomes)
    gaps: list[VerificationGap] = []
    for genome in genome_tuple:
        gaps.extend(find_source_gaps(genome))
    return VerificationResult(
        briefing_date=briefing_date,
        timezone=timezone,
        gaps=tuple(gaps),
        checked_signals=len(genome_tuple),
    )


def build_verification_from_directory(
    directory: str,
    *,
    briefing_date: date,
    timezone: str = DEFAULT_TIMEZONE,
    limit: int = 5,
    dry_run: bool = True,
) -> VerificationResult:
    """Load signals, compile genomes, and return source verification gaps."""

    batch = build_batch_from_directory(
        directory,
        briefing_date=briefing_date,
        timezone=timezone,
        limit=limit,
        dry_run=dry_run,
    )
    return build_verification_result(batch.genomes, briefing_date=briefing_date, timezone=timezone)


def render_verification_markdown(result: VerificationResult) -> str:
    """Render a Markdown source verification checklist."""

    lines = [
        f"# Daily Ω Source Verification — {result.briefing_date.isoformat()}",
        "",
        f"Timezone: `{result.timezone}`",
        f"Checked signals: `{result.checked_signals}`",
        f"Clear for promotion: `{str(result.is_clear).lower()}`",
        "",
    ]
    if not result.gaps:
        lines.extend(["## No source gaps detected", "", "All compiled SignalGenome++ sources are at least review-ready.", ""])
        return "\n".join(lines)

    lines.extend(["## Verification gaps", ""])
    for index, gap in enumerate(result.gaps, start=1):
        lines.extend(
            [
                f"### {index}. {gap.signal_title}",
                f"- **Source:** {gap.source_title}",
                f"- **Type:** {gap.source_type}",
                f"- **Identifier:** `{gap.url_or_identifier}`",
                f"- **Status:** `{gap.verification_status}`",
                f"- **Blocking:** `{str(gap.blocking).lower()}`",
                f"- **Residue:** {gap.residue}",
                f"- **Next check:** {gap.next_check}",
                "",
            ]
        )
    return "\n".join(lines)


__all__ = [
    "UNVERIFIED_SOURCE_STATUSES",
    "VerificationGap",
    "VerificationResult",
    "build_verification_from_directory",
    "build_verification_result",
    "find_source_gaps",
    "next_source_check",
    "render_verification_markdown",
]
