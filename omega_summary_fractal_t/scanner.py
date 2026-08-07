from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .models import EvidenceRef, SummaryEdge, SummaryNode

DEFAULT_EXCLUDES = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}
SYSTEM_PREFIXES = ("omega_", "tfuga_", "sage_", "ecc_", "ait_")
TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".rst",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".csv",
    ".tsv",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
    ".lean",
    ".tex",
}
BINARY_EXTENSIONS = {".zip", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bin"}
GENERIC_SYSTEM_TOKENS = {
    "omega",
    "tfuga",
    "sage",
    "ecc",
    "ait",
    "tristan",
    "system",
    "systems",
    "test",
    "tests",
    "schema",
    "schemas",
    "workflow",
    "workflows",
}
TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


@dataclass
class ScanResult:
    nodes: list[SummaryNode] = field(default_factory=list)
    edges: list[SummaryEdge] = field(default_factory=list)
    file_hashes: dict[str, str] = field(default_factory=dict)
    readme_text: dict[str, str] = field(default_factory=dict)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def slug(value: str) -> str:
    value = value.replace("Ω", "omega").replace("∞", "infinity")
    value = re.sub(r"[^A-Za-z0-9_.:/-]+", "-", value)
    return value.strip("-").lower() or "root"


def first_summary_line(text: str, fallback: str) -> str:
    in_fence = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        if line.startswith(("#", "!", "[", "<", "|", "---", "===")):
            continue
        line = re.sub(r"\s+", " ", line)
        if len(line) > 220:
            line = line[:217].rstrip() + "..."
        return line
    return fallback


def classify(path: Path, rel: str) -> str:
    name = path.name.lower()
    rel_lower = rel.lower()
    if path.is_dir():
        return "system" if path.name.startswith(SYSTEM_PREFIXES) else "directory"
    if name.startswith("test_") or "/tests/" in f"/{rel_lower}/":
        return "test"
    if rel_lower.startswith(".github/workflows/") or (
        name.endswith((".yaml", ".yml")) and "workflow" in rel_lower
    ):
        return "workflow"
    if "schema" in rel_lower and path.suffix.lower() == ".json":
        return "schema"
    if path.suffix.lower() == ".py":
        return "code"
    if path.suffix.lower() in {".md", ".rst", ".tex"}:
        return "document"
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return "binary"
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return "data"
    return "other"


def _iter_paths(root: Path, excludes: set[str], max_files: int) -> Iterable[Path]:
    count = 0
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in excludes)
        for filename in sorted(filenames):
            if count >= max_files:
                return
            yield Path(current) / filename
            count += 1


def _meaningful_tokens(value: str) -> set[str]:
    return {
        token
        for token in TOKEN_RE.findall(value.casefold().replace("-", "_"))
        if len(token) >= 2 and token not in GENERIC_SYSTEM_TOKENS and token != "t"
    }


def _git_first_seen(root: Path) -> dict[str, str]:
    """Return first observed commit timestamp for files and top-level systems.

    This is best-effort provenance. A shallow clone produces a bounded/partial
    chronology rather than a fabricated date. Callers can inspect
    ``chronology_source`` on system metrics.
    """

    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                "--reverse",
                "--date=iso-strict",
                "--format=__COMMIT__%aI",
                "--name-only",
                "--",
                ".",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if proc.returncode != 0:
        return {}

    current = ""
    first_seen: dict[str, str] = {}
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("__COMMIT__"):
            current = line.removeprefix("__COMMIT__")
            continue
        rel = line.replace("\\", "/")
        if current:
            first_seen.setdefault(rel, current)
            top = rel.split("/", 1)[0]
            if top.startswith(SYSTEM_PREFIXES):
                first_seen.setdefault(top, current)
    return first_seen


class RepositoryScanner:
    def __init__(
        self,
        root: str | Path,
        *,
        excludes: Iterable[str] = (),
        max_files: int = 20000,
        max_text_bytes: int = 512_000,
        max_symbols_per_file: int = 200,
    ) -> None:
        self.root = Path(root).resolve()
        self.excludes = DEFAULT_EXCLUDES | set(excludes)
        self.max_files = max_files
        self.max_text_bytes = max_text_bytes
        self.max_symbols_per_file = max_symbols_per_file

    def scan(self, *, include_symbols: bool = True) -> ScanResult:
        result = ScanResult()
        root_id = "repo:" + slug(self.root.name)
        root_node = SummaryNode(root_id, "repository", ".", self.root.name, f"Repository {self.root.name}")
        result.nodes.append(root_node)

        first_seen = _git_first_seen(self.root)
        system_nodes: dict[str, SummaryNode] = {}
        files_by_system: dict[str, list[SummaryNode]] = {}
        file_text: dict[str, str] = {}
        direct_system_for_file: dict[str, str] = {}

        for path in _iter_paths(self.root, self.excludes, self.max_files):
            try:
                rel = path.relative_to(self.root).as_posix()
                stat = path.stat()
            except (OSError, ValueError):
                continue

            kind = classify(path, rel)
            digest = sha256_file(path)
            result.file_hashes[rel] = digest
            text = ""
            if path.suffix.lower() in TEXT_EXTENSIONS and stat.st_size <= self.max_text_bytes:
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    text = ""
            if text:
                file_text[rel] = text

            top = rel.split("/", 1)[0]
            system_key = top if top.startswith(SYSTEM_PREFIXES) else ""
            if system_key and system_key not in system_nodes:
                node = self._system_node(system_key, first_seen.get(system_key, ""))
                system_nodes[system_key] = node
                files_by_system[system_key] = []
                result.nodes.append(node)
                result.edges.append(SummaryEdge(root_id, node.id, "CONTAINS"))
                if node.metrics.get("readme_present"):
                    result.readme_text[system_key] = (self.root / system_key / "README.md").read_text(
                        encoding="utf-8", errors="replace"
                    )

            file_node = SummaryNode(
                "file:" + slug(rel),
                kind,
                rel,
                path.name,
                first_summary_line(text, f"{kind} file {path.name}") if text else f"{kind} file {path.name}",
                "observed",
                metrics={"bytes": stat.st_size, "first_seen": first_seen.get(rel, "")},
                evidence=[EvidenceRef(rel, kind, "observed", digest)],
            )
            result.nodes.append(file_node)
            parent_id = system_nodes[system_key].id if system_key else root_id
            result.edges.append(SummaryEdge(parent_id, file_node.id, "CONTAINS"))
            if system_key:
                files_by_system[system_key].append(file_node)
                direct_system_for_file[rel] = system_key

            if include_symbols and kind == "code" and text:
                for symbol in self._python_symbols(text, rel)[: self.max_symbols_per_file]:
                    result.nodes.append(symbol)
                    result.edges.append(SummaryEdge(file_node.id, symbol.id, "DECLARES"))

        self._link_root_artifacts(
            result,
            system_nodes,
            files_by_system,
            file_text,
            direct_system_for_file,
        )
        self._link_python_dependencies(result, system_nodes, file_text, direct_system_for_file)
        self._annotate_systems(system_nodes, files_by_system)
        self._rank_chronology(system_nodes)

        root_node.metrics = self._aggregate_metrics(result.nodes)
        root_node.metrics["relation_edges"] = sum(edge.relation != "CONTAINS" for edge in result.edges)
        root_node.one_line = (
            f"{root_node.metrics.get('systems', 0)} systems, "
            f"{root_node.metrics.get('code_files', 0)} code files, "
            f"{root_node.metrics.get('tests', 0)} tests and "
            f"{root_node.metrics.get('documents', 0)} documents observed."
        )
        return result

    def _system_node(self, system_key: str, first_seen: str) -> SummaryNode:
        sys_path = self.root / system_key
        readme = sys_path / "README.md"
        readme_text = ""
        if readme.exists() and readme.stat().st_size <= self.max_text_bytes:
            try:
                readme_text = readme.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
        title = system_key
        for line in readme_text.splitlines():
            if line.startswith("#"):
                title = line.lstrip("#").strip() or system_key
                break
        return SummaryNode(
            "system:" + slug(system_key),
            "system",
            system_key,
            title,
            first_summary_line(readme_text, f"System {system_key}"),
            "documented" if readme_text else "observed",
            metrics={
                "first_seen": first_seen,
                "chronology_source": "git_history" if first_seen else "unavailable",
                "readme_present": bool(readme_text),
            },
        )

    def _python_symbols(self, text: str, rel: str) -> list[SummaryNode]:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return []
        symbols = []
        for item in tree.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(item, ast.ClassDef) else "function"
                doc = ast.get_docstring(item) or ""
                symbols.append(
                    SummaryNode(
                        f"symbol:{slug(rel)}:{slug(item.name)}",
                        kind,
                        f"{rel}:{item.lineno}",
                        item.name,
                        first_summary_line(doc, f"{kind} {item.name}"),
                        "implemented",
                        metrics={"line": item.lineno},
                    )
                )
        return symbols

    def _artifact_matches(self, rel: str, text: str, system_key: str) -> float:
        """Deterministic lexical linkage for repository-level validation artifacts."""

        system_tokens = _meaningful_tokens(system_key)
        if not system_tokens:
            return 0.0
        normalized_rel = rel.casefold().replace("-", "_")
        if system_key.casefold() in normalized_rel:
            return 1.0
        artifact_tokens = _meaningful_tokens(rel + " " + text[:8000])
        if not artifact_tokens:
            return 0.0
        overlap = len(system_tokens & artifact_tokens)
        return overlap / len(system_tokens)

    def _link_root_artifacts(
        self,
        result: ScanResult,
        system_nodes: dict[str, SummaryNode],
        files_by_system: dict[str, list[SummaryNode]],
        file_text: dict[str, str],
        direct_system_for_file: dict[str, str],
    ) -> None:
        relation_by_kind = {
            "test": "TESTS",
            "workflow": "VALIDATES",
            "schema": "CONFORMS_TO",
            "document": "SUPPORTS",
        }
        file_nodes = [node for node in result.nodes if node.id.startswith("file:")]
        for file_node in file_nodes:
            if file_node.path in direct_system_for_file:
                continue
            relation = relation_by_kind.get(file_node.kind)
            if not relation:
                continue
            text = file_text.get(file_node.path, "")
            scored = []
            for system_key in system_nodes:
                score = self._artifact_matches(file_node.path, text, system_key)
                if score >= 0.5:
                    scored.append((score, system_key))
            if not scored:
                continue
            best = max(score for score, _ in scored)
            # Avoid linking generic documents to a large fraction of the corpus.
            winners = [key for score, key in scored if score == best and (best >= 0.75 or len(scored) <= 3)]
            for system_key in sorted(winners):
                system_node = system_nodes[system_key]
                result.edges.append(SummaryEdge(system_node.id, file_node.id, relation))
                if file_node not in files_by_system[system_key]:
                    files_by_system[system_key].append(file_node)

    def _link_python_dependencies(
        self,
        result: ScanResult,
        system_nodes: dict[str, SummaryNode],
        file_text: dict[str, str],
        direct_system_for_file: dict[str, str],
    ) -> None:
        dependencies: set[tuple[str, str]] = set()
        for rel, source_system in direct_system_for_file.items():
            if not rel.endswith(".py"):
                continue
            text = file_text.get(rel, "")
            if not text:
                continue
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            imported: set[str] = set()
            for item in ast.walk(tree):
                if isinstance(item, ast.Import):
                    imported.update(alias.name.split(".", 1)[0] for alias in item.names)
                elif isinstance(item, ast.ImportFrom) and item.module:
                    imported.add(item.module.split(".", 1)[0])
            for target in imported:
                if target in system_nodes and target != source_system:
                    dependencies.add((source_system, target))
        for source, target in sorted(dependencies):
            result.edges.append(
                SummaryEdge(system_nodes[source].id, system_nodes[target].id, "DEPENDS_ON")
            )

    def _annotate_systems(
        self,
        system_nodes: dict[str, SummaryNode],
        files_by_system: dict[str, list[SummaryNode]],
    ) -> None:
        for key, node in system_nodes.items():
            files = files_by_system.get(key, [])
            kinds = [item.kind for item in files]
            has_code = "code" in kinds
            has_tests = "test" in kinds
            has_docs = any(kind == "document" for kind in kinds)
            has_schema = "schema" in kinds
            node.status = (
                "tested"
                if has_code and has_tests
                else "implemented"
                if has_code
                else "documented"
                if has_docs
                else "observed"
            )
            chronology = {
                "first_seen": node.metrics.get("first_seen", ""),
                "chronology_source": node.metrics.get("chronology_source", "unavailable"),
                "readme_present": node.metrics.get("readme_present", False),
            }
            node.metrics = {
                **chronology,
                "files": len(files),
                "code_files": sum(kind == "code" for kind in kinds),
                "tests": sum(kind == "test" for kind in kinds),
                "documents": sum(kind == "document" for kind in kinds),
                "schemas": sum(kind == "schema" for kind in kinds),
                "workflows": sum(kind == "workflow" for kind in kinds),
                "implemented": has_code,
                "tested": has_code and has_tests,
                "documented": has_docs,
                "schema_backed": has_schema,
            }
            node.evidence = [
                EvidenceRef(item.path, item.kind, item.status, item.evidence[0].sha256)
                for item in files[:30]
                if item.evidence
            ]

    @staticmethod
    def _rank_chronology(system_nodes: dict[str, SummaryNode]) -> None:
        ordered = sorted(
            system_nodes.values(),
            key=lambda node: (
                not bool(node.metrics.get("first_seen")),
                str(node.metrics.get("first_seen", "")),
                node.path,
            ),
        )
        for rank, node in enumerate(ordered, start=1):
            node.metrics["chronology_rank"] = rank

    @staticmethod
    def _aggregate_metrics(nodes: list[SummaryNode]) -> dict[str, int]:
        return {
            "systems": sum(node.kind == "system" for node in nodes),
            "code_files": sum(node.kind == "code" for node in nodes),
            "tests": sum(node.kind == "test" for node in nodes),
            "documents": sum(node.kind == "document" for node in nodes),
            "workflows": sum(node.kind == "workflow" for node in nodes),
            "schemas": sum(node.kind == "schema" for node in nodes),
            "symbols": sum(node.kind in {"class", "function"} for node in nodes),
            "binary_files": sum(node.kind == "binary" for node in nodes),
        }
