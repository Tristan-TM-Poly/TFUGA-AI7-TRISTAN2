"""Report writer for Omega absorb v1.9."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Tuple

from .report_atlas import build_report_atlas, render_report_atlas


@dataclass(frozen=True)
class WrittenReport:
    path: str
    kind: str
    bytes_written: int


@dataclass(frozen=True)
class ReportWriteResult:
    files: Tuple[WrittenReport, ...]
    next_action: str


def default_report_contents() -> Mapping[str, str]:
    return {
        "report_atlas.md": render_report_atlas(),
        "status.md": "# Status\n\nGenerated status report placeholder.\n",
        "health.md": "# Health\n\nGenerated health report placeholder.\n",
        "changelog.md": "# Changelog Plus\n\nGenerated changelog plus placeholder.\n",
        "oak_ledger.md": "# OAK Ledger\n\nGenerated ledger placeholder.\n",
    }


def write_reports(output_dir: str | Path = "generated/omega_absorb_poly_prof_v19/reports", contents: Mapping[str, str] | None = None) -> ReportWriteResult:
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    contents = contents or default_report_contents()
    files = []
    for filename, text in contents.items():
        path = base / filename
        path.write_text(text, encoding="utf-8")
        files.append(WrittenReport(str(path), path.suffix.lstrip(".") or "text", len(text.encode("utf-8"))))
    atlas = build_report_atlas()
    return ReportWriteResult(tuple(files), atlas.next_action)
