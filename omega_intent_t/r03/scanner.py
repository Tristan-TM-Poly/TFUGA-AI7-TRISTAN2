from __future__ import annotations

import ast
from fnmatch import fnmatch
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable

from .models import FileRecord, RepoTwinManifest, WorkflowRule

DEFAULT_IGNORES = (
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
)

GENERATED_PREFIXES = ("generated/", "reports/", "dist/", "build/")


def _normalize(path: Path) -> str:
    value = path.as_posix()
    while value.startswith("./"):
        value = value[2:]
    return value


def _kind(path: str) -> str:
    if path.startswith(".github/workflows/"):
        return "workflow"
    if path.startswith("tests/") or "/tests/" in path or Path(path).name.startswith("test_"):
        return "test"
    if path.startswith("docs/") or path.endswith((".md", ".rst")):
        return "document"
    if path.startswith("schemas/") or path.endswith((".schema.json", ".jsonschema")):
        return "schema"
    if path.endswith(".py"):
        return "python"
    if path.endswith((".rs", ".cpp", ".cc", ".c", ".h", ".hpp")):
        return "native_code"
    if path.endswith((".yml", ".yaml", ".toml", ".ini", ".cfg")):
        return "configuration"
    return "asset"


def package_for_path(path: str) -> str:
    parts = Path(path).parts
    if not parts:
        return "root"
    if parts[0] in {"tests", "docs", "schemas", "examples", ".github"}:
        return parts[0]
    if len(parts) == 1:
        return "root"
    return parts[0]


def _python_imports(content: bytes) -> tuple[str, ...]:
    try:
        tree = ast.parse(content.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return ()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return tuple(sorted(imports))


def _workflow_rule(path: Path, relative: str, content: str) -> WorkflowRule:
    name_match = re.search(r"(?m)^name:\s*[\"']?(.+?)[\"']?\s*$", content)
    name = name_match.group(1).strip() if name_match else Path(relative).stem
    patterns: list[str] = []
    lines = content.splitlines()
    collecting = False
    base_indent = 0
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped == "paths:":
            collecting = True
            base_indent = indent
            continue
        if collecting:
            if stripped and indent <= base_indent and not stripped.startswith("-"):
                collecting = False
                continue
            match = re.match(r"\s*-\s*[\"']?(.+?)[\"']?\s*$", line)
            if match:
                patterns.append(match.group(1).strip())
    cancellation = "cancel-in-progress: true" in content.lower()
    return WorkflowRule(
        name=name,
        path=relative,
        path_patterns=tuple(sorted(set(patterns))),
        has_concurrency_cancellation=cancellation,
    )


class RepoTwinScanner:
    def __init__(self, ignored_directories: Iterable[str] = DEFAULT_IGNORES) -> None:
        self.ignored_directories = tuple(sorted(set(ignored_directories)))

    def scan(self, root: str | Path) -> RepoTwinManifest:
        root_path = Path(root).resolve()
        if not root_path.is_dir():
            raise NotADirectoryError(root_path)
        records: list[FileRecord] = []
        workflows: list[WorkflowRule] = []
        dependency_edges: set[tuple[str, str]] = set()
        test_edges: set[tuple[str, str]] = set()

        for path in sorted(root_path.rglob("*")):
            if not path.is_file():
                continue
            relative = _normalize(path.relative_to(root_path))
            if any(part in self.ignored_directories for part in Path(relative).parts):
                continue
            content = path.read_bytes()
            imports = _python_imports(content) if relative.endswith(".py") else ()
            package = package_for_path(relative)
            kind = _kind(relative)
            record = FileRecord(
                path=relative,
                size_bytes=len(content),
                sha256=sha256(content).hexdigest(),
                kind=kind,
                package=package,
                imports=imports,
                generated=relative.startswith(GENERATED_PREFIXES),
            )
            records.append(record)
            if kind == "workflow":
                try:
                    workflows.append(_workflow_rule(path, relative, content.decode("utf-8")))
                except UnicodeDecodeError:
                    workflows.append(WorkflowRule(Path(relative).stem, relative, (), False))
            for imported in imports:
                if imported != package:
                    dependency_edges.add((package, imported))
                if kind == "test":
                    test_edges.add((relative, imported))

        return RepoTwinManifest(
            root=str(root_path),
            files=tuple(records),
            workflows=tuple(sorted(workflows, key=lambda item: item.path)),
            dependency_edges=tuple(sorted(dependency_edges)),
            test_edges=tuple(sorted(test_edges)),
            ignored_directories=self.ignored_directories,
        )


def workflow_matches(rule: WorkflowRule, changed_path: str) -> bool:
    normalized = changed_path
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized == rule.path:
        return True
    if not rule.path_patterns:
        return False
    included = False
    for pattern in rule.path_patterns:
        if pattern.startswith("!"):
            if fnmatch(normalized, pattern[1:]):
                return False
        elif fnmatch(normalized, pattern):
            included = True
    return included
