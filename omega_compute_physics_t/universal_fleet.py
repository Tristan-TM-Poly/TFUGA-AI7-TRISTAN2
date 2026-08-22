"""Universal static fleet scan for Omega Compute Physics R0.6.

Combines commit-addressed file snapshots, multi-language source fingerprints,
Python Complexity-IR and static call-graph evidence without importing or
executing repository code.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .call_graph import CallGraphReport, build_call_graph
from .complexity_ir import FunctionIR, compile_source_ir
from .language_adapters import SourceGenome, default_language_registry
from .snapshot_ledger import RepositorySnapshot, snapshot_checkout


_DEFAULT_EXCLUDES = {".git", ".venv", "venv", "node_modules", "build", "dist", "__pycache__"}


@dataclass(frozen=True)
class UniversalRepositoryReport:
    repository: str
    commit_sha: str
    snapshot: RepositorySnapshot
    source_genomes: tuple[SourceGenome, ...]
    language_counts: Mapping[str, int]
    python_functions_ir: int
    call_graph: CallGraphReport
    unsupported_files: int
    parse_errors: tuple[str, ...]
    status: str = "universal-repository-static-atlas"
    oak_warning: str = (
        "Universal fleet scanning is static. Python uses AST-level structure while other "
        "languages may use lexical heuristics; neither constitutes runtime evidence."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "commit_sha": self.commit_sha,
            "snapshot": self.snapshot.to_dict(),
            "source_genomes": [row.to_dict() for row in self.source_genomes],
            "language_counts": dict(sorted(self.language_counts.items())),
            "python_functions_ir": self.python_functions_ir,
            "call_graph": self.call_graph.to_dict(),
            "unsupported_files": self.unsupported_files,
            "parse_errors": list(self.parse_errors),
            "status": self.status,
            "oak_warning": self.oak_warning,
        }


@dataclass(frozen=True)
class UniversalFleetReport:
    repositories: tuple[UniversalRepositoryReport, ...]
    total_source_files: int
    total_python_functions_ir: int
    language_counts: Mapping[str, int]
    status: str = "universal-fleet-static-atlas"
    oak_warning: str = (
        "Cross-repository static fingerprints are planning evidence only. Cross-language "
        "similarity is not semantic equivalence or a universality-class proof."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "repositories": [row.to_dict() for row in self.repositories],
            "total_source_files": self.total_source_files,
            "total_python_functions_ir": self.total_python_functions_ir,
            "language_counts": dict(sorted(self.language_counts.items())),
            "status": self.status,
            "oak_warning": self.oak_warning,
        }


def _iter_files(root: Path, excludes: set[str]):
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root)
        if any(part in excludes for part in relative.parts):
            continue
        yield path, str(relative)


def scan_universal_checkout(
    root: str | Path,
    *,
    repository: str,
    commit_sha: str,
    max_source_bytes: int = 2_000_000,
) -> UniversalRepositoryReport:
    root_path = Path(root).resolve()
    registry = default_language_registry()
    snapshot = snapshot_checkout(root_path, repository=repository, commit_sha=commit_sha)
    source_rows: list[SourceGenome] = []
    python_ir: list[FunctionIR] = []
    errors: list[str] = []
    unsupported = 0
    language_counts: dict[str, int] = {}

    for path, relative in _iter_files(root_path, _DEFAULT_EXCLUDES):
        adapter = registry.adapter_for(relative)
        if adapter is None:
            unsupported += 1
            continue
        if path.stat().st_size > max_source_bytes:
            errors.append(f"{relative}: skipped source > {max_source_bytes} bytes")
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{relative}: non-UTF-8 source skipped")
            continue
        try:
            genome = adapter.scan(source, path=relative)
            source_rows.append(genome)
            language_counts[genome.language] = language_counts.get(genome.language, 0) + 1
            if genome.language == "python":
                python_ir.extend(compile_source_ir(source, module=relative))
        except (SyntaxError, ValueError) as exc:
            errors.append(f"{relative}: {type(exc).__name__}: {exc}")

    call_graph = build_call_graph(python_ir)
    return UniversalRepositoryReport(
        repository=repository,
        commit_sha=commit_sha,
        snapshot=snapshot,
        source_genomes=tuple(source_rows),
        language_counts=language_counts,
        python_functions_ir=len(python_ir),
        call_graph=call_graph,
        unsupported_files=unsupported,
        parse_errors=tuple(errors),
    )


def scan_universal_fleet(
    checkouts: Mapping[str, tuple[str | Path, str]],
) -> UniversalFleetReport:
    """Scan mapping ``repository -> (checkout_root, commit_sha)`` statically."""
    if not checkouts:
        raise ValueError("at least one repository checkout is required")
    reports = tuple(
        scan_universal_checkout(root, repository=repository, commit_sha=commit_sha)
        for repository, (root, commit_sha) in sorted(checkouts.items())
    )
    languages: dict[str, int] = {}
    for report in reports:
        for language, count in report.language_counts.items():
            languages[language] = languages.get(language, 0) + count
    return UniversalFleetReport(
        repositories=reports,
        total_source_files=sum(len(row.source_genomes) for row in reports),
        total_python_functions_ir=sum(row.python_functions_ir for row in reports),
        language_counts=languages,
    )
