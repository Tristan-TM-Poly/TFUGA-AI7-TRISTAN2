from __future__ import annotations

import ast
import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .models import EvidenceRef, SummaryEdge, SummaryNode

DEFAULT_EXCLUDES = {
    ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".venv", "venv",
    "__pycache__", "node_modules", "dist", "build",
}
SYSTEM_PREFIXES = ("omega_", "tfuga_", "sage_", "ecc_", "ait_")
TEXT_EXTENSIONS = {".py", ".md", ".rst", ".txt", ".toml", ".yaml", ".yml", ".json", ".csv", ".tsv", ".ini", ".cfg", ".sh", ".ps1", ".lean", ".tex"}
BINARY_EXTENSIONS = {".zip", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bin"}


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
    name = path.name.lower(); rel_lower = rel.lower()
    if path.is_dir():
        return "system" if path.name.startswith(SYSTEM_PREFIXES) else "directory"
    if name.startswith("test_") or "/tests/" in f"/{rel_lower}/": return "test"
    if rel_lower.startswith(".github/workflows/") or name.endswith((".yaml", ".yml")) and "workflow" in rel_lower: return "workflow"
    if "schema" in rel_lower and path.suffix.lower() == ".json": return "schema"
    if path.suffix.lower() == ".py": return "code"
    if path.suffix.lower() in {".md", ".rst", ".tex"}: return "document"
    if path.suffix.lower() in BINARY_EXTENSIONS: return "binary"
    if path.suffix.lower() in TEXT_EXTENSIONS: return "data"
    return "other"


def _iter_paths(root: Path, excludes: set[str], max_files: int) -> Iterable[Path]:
    count = 0
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in excludes)
        for filename in sorted(filenames):
            if count >= max_files: return
            yield Path(current) / filename
            count += 1


class RepositoryScanner:
    def __init__(self, root: str | Path, *, excludes: Iterable[str] = (), max_files: int = 20000, max_text_bytes: int = 512_000, max_symbols_per_file: int = 200) -> None:
        self.root = Path(root).resolve(); self.excludes = DEFAULT_EXCLUDES | set(excludes)
        self.max_files = max_files; self.max_text_bytes = max_text_bytes; self.max_symbols_per_file = max_symbols_per_file

    def scan(self, *, include_symbols: bool = True) -> ScanResult:
        result = ScanResult(); root_id = "repo:" + slug(self.root.name)
        root_node = SummaryNode(root_id, "repository", ".", self.root.name, f"Repository {self.root.name}")
        result.nodes.append(root_node); system_nodes = {}; files_by_system = {}
        for path in _iter_paths(self.root, self.excludes, self.max_files):
            try:
                rel = path.relative_to(self.root).as_posix(); stat = path.stat()
            except (OSError, ValueError): continue
            kind = classify(path, rel); digest = sha256_file(path); result.file_hashes[rel] = digest
            text = ""
            if path.suffix.lower() in TEXT_EXTENSIONS and stat.st_size <= self.max_text_bytes:
                try: text = path.read_text(encoding="utf-8", errors="replace")
                except OSError: text = ""
            top = rel.split("/", 1)[0]; system_key = top if top.startswith(SYSTEM_PREFIXES) else ""
            if system_key and system_key not in system_nodes:
                sys_path = self.root / system_key; readme = sys_path / "README.md"; readme_text = ""
                if readme.exists() and readme.stat().st_size <= self.max_text_bytes:
                    try: readme_text = readme.read_text(encoding="utf-8", errors="replace")
                    except OSError: pass
                title = system_key
                for line in readme_text.splitlines():
                    if line.startswith("#"):
                        title = line.lstrip("#").strip() or system_key; break
                node = SummaryNode("system:" + slug(system_key), "system", system_key, title, first_summary_line(readme_text, f"System {system_key}"), "documented" if readme_text else "observed")
                system_nodes[system_key] = node; files_by_system[system_key] = []; result.nodes.append(node); result.edges.append(SummaryEdge(root_id, node.id, "CONTAINS"))
                if readme_text: result.readme_text[system_key] = readme_text
            file_node = SummaryNode("file:" + slug(rel), kind, rel, path.name, first_summary_line(text, f"{kind} file {path.name}") if text else f"{kind} file {path.name}", "observed", metrics={"bytes": stat.st_size}, evidence=[EvidenceRef(rel, kind, "observed", digest)])
            result.nodes.append(file_node); parent_id = system_nodes[system_key].id if system_key else root_id; result.edges.append(SummaryEdge(parent_id, file_node.id, "CONTAINS"))
            if system_key: files_by_system[system_key].append(file_node)
            if include_symbols and kind == "code" and text:
                for symbol in self._python_symbols(text, rel)[:self.max_symbols_per_file]: result.nodes.append(symbol); result.edges.append(SummaryEdge(file_node.id, symbol.id, "DECLARES"))
        self._annotate_systems(system_nodes, files_by_system); root_node.metrics = self._aggregate_metrics(result.nodes)
        root_node.one_line = f"{root_node.metrics.get('systems', 0)} systems, {root_node.metrics.get('code_files', 0)} code files, {root_node.metrics.get('tests', 0)} tests and {root_node.metrics.get('documents', 0)} documents observed."
        return result

    def _python_symbols(self, text: str, rel: str) -> list[SummaryNode]:
        try: tree = ast.parse(text)
        except SyntaxError: return []
        symbols = []
        for item in tree.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(item, ast.ClassDef) else "function"; doc = ast.get_docstring(item) or ""
                symbols.append(SummaryNode(f"symbol:{slug(rel)}:{slug(item.name)}", kind, f"{rel}:{item.lineno}", item.name, first_summary_line(doc, f"{kind} {item.name}"), "implemented", metrics={"line": item.lineno}))
        return symbols

    def _annotate_systems(self, system_nodes, files_by_system) -> None:
        for key, node in system_nodes.items():
            files = files_by_system.get(key, []); kinds = [item.kind for item in files]
            has_code = "code" in kinds; has_tests = "test" in kinds; has_docs = any(k == "document" for k in kinds); has_schema = "schema" in kinds
            node.status = "tested" if has_code and has_tests else "implemented" if has_code else "documented" if has_docs else "observed"
            node.metrics = {"files": len(files), "code_files": sum(k == "code" for k in kinds), "tests": sum(k == "test" for k in kinds), "documents": sum(k == "document" for k in kinds), "schemas": sum(k == "schema" for k in kinds), "implemented": has_code, "tested": has_code and has_tests, "documented": has_docs, "schema_backed": has_schema}
            node.evidence = [EvidenceRef(item.path, item.kind, item.status, item.evidence[0].sha256) for item in files[:20] if item.evidence]

    @staticmethod
    def _aggregate_metrics(nodes: list[SummaryNode]) -> dict[str, int]:
        return {"systems": sum(n.kind == "system" for n in nodes), "code_files": sum(n.kind == "code" for n in nodes), "tests": sum(n.kind == "test" for n in nodes), "documents": sum(n.kind == "document" for n in nodes), "workflows": sum(n.kind == "workflow" for n in nodes), "schemas": sum(n.kind == "schema" for n in nodes), "symbols": sum(n.kind in {"class", "function"} for n in nodes), "binary_files": sum(n.kind == "binary" for n in nodes)}
