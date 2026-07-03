from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FunctionPattern:
    name: str
    args: tuple[str, ...]
    decorators: tuple[str, ...]
    docstring: str | None
    complexity_hint: int


@dataclass(frozen=True)
class CvcdDigest:
    file: str
    imports: tuple[str, ...]
    functions: tuple[FunctionPattern, ...]
    classes: tuple[str, ...]
    invariants: tuple[str, ...]


def _names_from_import(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        prefix = "." * node.level + (node.module or "")
        return [f"{prefix}.{alias.name}" for alias in node.names]
    return []


def digest_python_file(path: str | Path) -> CvcdDigest:
    p = Path(path)
    tree = ast.parse(p.read_text(encoding="utf-8"))
    imports: list[str] = []
    functions: list[FunctionPattern] = []
    classes: list[str] = []
    invariants: set[str] = set()

    for node in ast.walk(tree):
        imports.extend(_names_from_import(node))
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
            invariants.add("class-bound API surface")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = tuple(arg.arg for arg in node.args.args)
            decorators = tuple(ast.unparse(d) for d in node.decorator_list)
            branches = sum(isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.Match)) for n in ast.walk(node))
            functions.append(FunctionPattern(node.name, args, decorators, ast.get_docstring(node), branches))
            if node.name.startswith("test_"):
                invariants.add("testable behavior encoded")
            if any(keyword in node.name.lower() for keyword in ["score", "rank", "classify", "detect", "validate"]):
                invariants.add("decision function / classifier")
            if branches > 4:
                invariants.add("branch-heavy logic requires targeted tests")

    if imports:
        invariants.add("external dependency/API surface")
    if not functions and not classes:
        invariants.add("data/config/documentation source")

    return CvcdDigest(
        str(p),
        tuple(sorted(set(imports))),
        tuple(functions),
        tuple(classes),
        tuple(sorted(invariants)),
    )
