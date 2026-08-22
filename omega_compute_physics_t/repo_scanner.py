"""Universal static repository scanner for Ω-META-COMPUTE-PHYSICS-T∞.

The scanner turns Python source into a bounded Workload Genome that can seed
benchmark design across repositories. Structural loop-depth labels are heuristic
candidates only; they are never promoted to Big-O/Theta proofs.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class FunctionGenome:
    module: str
    qualified_name: str
    line_start: int
    line_end: int
    loc: int
    arguments: int
    loops: int
    max_loop_depth: int
    branches: int
    calls: int
    comprehensions: int
    allocations: int
    awaits: int
    yields: int
    direct_recursion: bool
    async_function: bool
    structural_scaling_candidate: str
    status: str = "static-workload-genome"
    oak_warning: str = (
        "Loop depth and AST structure are static hints only. They do not prove "
        "runtime Big-O/Theta complexity because iteration counts, called "
        "functions, data dependence, compiler effects and hardware are omitted."
    )

    def vector(self) -> tuple[float, ...]:
        return (
            float(self.loc),
            float(self.arguments),
            float(self.loops),
            float(self.max_loop_depth),
            float(self.branches),
            float(self.calls),
            float(self.comprehensions),
            float(self.allocations),
            float(self.awaits),
            float(self.yields),
            float(self.direct_recursion),
            float(self.async_function),
        )


@dataclass(frozen=True)
class ModuleGenome:
    path: str
    functions: tuple[FunctionGenome, ...]
    imports: tuple[str, ...]
    parse_error: str | None = None


@dataclass(frozen=True)
class RepositoryGenome:
    root: str
    modules: tuple[ModuleGenome, ...]
    python_files: int
    functions: int
    total_loc: int
    max_loop_depth: int
    recursive_functions: int
    async_functions: int
    status: str = "static-repository-genome"
    oak_warning: str = (
        "Repository Genome is a static inventory used to plan measurements. "
        "Dynamic resource claims require actual profiling and OAK validation."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "modules": [
                {
                    **asdict(module),
                    "functions": [asdict(function) for function in module.functions],
                }
                for module in self.modules
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


class _FunctionVisitor(ast.NodeVisitor):
    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self.loops = 0
        self.max_loop_depth = 0
        self._loop_depth = 0
        self.branches = 0
        self.calls = 0
        self.comprehensions = 0
        self.allocations = 0
        self.awaits = 0
        self.yields = 0
        self.direct_recursion = False

    def _visit_loop(self, node: ast.AST) -> None:
        self.loops += 1
        self._loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self._loop_depth)
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_For(self, node: ast.For) -> None:
        self._visit_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_loop(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_loop(node)

    def visit_If(self, node: ast.If) -> None:
        self.branches += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.branches += 1
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.branches += max(1, len(node.cases))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self.calls += 1
        if isinstance(node.func, ast.Name) and node.func.id == self.function_name:
            self.direct_recursion = True
        if isinstance(node.func, ast.Name) and node.func.id in {
            "list", "dict", "set", "tuple", "bytearray", "bytes"
        }:
            self.allocations += 1
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.comprehensions += 1
        self.allocations += 1
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.comprehensions += 1
        self.allocations += 1
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.comprehensions += 1
        self.allocations += 1
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.comprehensions += 1
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        self.awaits += 1
        self.generic_visit(node)

    def visit_Yield(self, node: ast.Yield) -> None:
        self.yields += 1
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        self.yields += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Do not include nested-function internals in the parent's genome.
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return


def _structural_scaling_candidate(visitor: _FunctionVisitor) -> str:
    if visitor.direct_recursion:
        return "recursive/unknown static candidate"
    if visitor.max_loop_depth <= 0 and visitor.comprehensions <= 0:
        return "O(1) structural candidate"
    depth = max(visitor.max_loop_depth, 1 if visitor.comprehensions else 0)
    if depth == 1:
        return "O(n) loop-depth candidate"
    return f"O(n^{depth}) loop-depth candidate"


def _function_genome(module: str, prefix: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionGenome:
    visitor = _FunctionVisitor(node.name)
    for statement in node.body:
        visitor.visit(statement)
    line_end = int(getattr(node, "end_lineno", node.lineno))
    arguments = (
        len(node.args.posonlyargs)
        + len(node.args.args)
        + len(node.args.kwonlyargs)
        + int(node.args.vararg is not None)
        + int(node.args.kwarg is not None)
    )
    qualified_name = f"{prefix}.{node.name}" if prefix else node.name
    return FunctionGenome(
        module=module,
        qualified_name=qualified_name,
        line_start=node.lineno,
        line_end=line_end,
        loc=max(1, line_end - node.lineno + 1),
        arguments=arguments,
        loops=visitor.loops,
        max_loop_depth=visitor.max_loop_depth,
        branches=visitor.branches,
        calls=visitor.calls,
        comprehensions=visitor.comprehensions,
        allocations=visitor.allocations,
        awaits=visitor.awaits,
        yields=visitor.yields,
        direct_recursion=visitor.direct_recursion,
        async_function=isinstance(node, ast.AsyncFunctionDef),
        structural_scaling_candidate=_structural_scaling_candidate(visitor),
    )


def _walk_functions(module: str, body: Sequence[ast.stmt], prefix: str = "") -> list[FunctionGenome]:
    rows: list[FunctionGenome] = []
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rows.append(_function_genome(module, prefix, node))
            rows.extend(_walk_functions(module, node.body, f"{prefix}.{node.name}" if prefix else node.name))
        elif isinstance(node, ast.ClassDef):
            class_prefix = f"{prefix}.{node.name}" if prefix else node.name
            rows.extend(_walk_functions(module, node.body, class_prefix))
    return rows


def scan_python_source(source: str, *, module: str = "<memory>") -> ModuleGenome:
    """Scan one source string without executing it."""

    try:
        tree = ast.parse(source, filename=module)
    except SyntaxError as exc:
        return ModuleGenome(path=module, functions=(), imports=(), parse_error=f"SyntaxError: {exc}")
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return ModuleGenome(
        path=module,
        functions=tuple(_walk_functions(module, tree.body)),
        imports=tuple(sorted(imports)),
    )


def _iter_python_files(root: Path, exclude_dirs: set[str]) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part in exclude_dirs for part in path.parts):
            continue
        if path.is_file():
            yield path


def scan_repository(
    root: str | Path,
    *,
    exclude_dirs: Sequence[str] = (
        ".git", ".venv", "venv", "node_modules", "build", "dist", "__pycache__"
    ),
    max_file_bytes: int = 2_000_000,
) -> RepositoryGenome:
    """Create a static workload inventory for a local repository checkout."""

    root_path = Path(root).resolve()
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(f"repository root does not exist: {root_path}")
    modules: list[ModuleGenome] = []
    total_loc = 0
    for path in sorted(_iter_python_files(root_path, set(exclude_dirs))):
        if path.stat().st_size > max_file_bytes:
            modules.append(
                ModuleGenome(
                    path=str(path.relative_to(root_path)),
                    functions=(),
                    imports=(),
                    parse_error=f"skipped: file exceeds {max_file_bytes} bytes",
                )
            )
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            modules.append(
                ModuleGenome(
                    path=str(path.relative_to(root_path)),
                    functions=(),
                    imports=(),
                    parse_error="skipped: non-UTF-8 source",
                )
            )
            continue
        total_loc += len(source.splitlines())
        modules.append(scan_python_source(source, module=str(path.relative_to(root_path))))

    functions = [function for module in modules for function in module.functions]
    return RepositoryGenome(
        root=str(root_path),
        modules=tuple(modules),
        python_files=len(modules),
        functions=len(functions),
        total_loc=total_loc,
        max_loop_depth=max((function.max_loop_depth for function in functions), default=0),
        recursive_functions=sum(function.direct_recursion for function in functions),
        async_functions=sum(function.async_function for function in functions),
    )


def benchmark_priority(
    genome: RepositoryGenome,
    *,
    limit: int = 50,
) -> tuple[FunctionGenome, ...]:
    """Rank functions for first dynamic profiling campaigns.

    Priority is a transparent static heuristic favouring nested loops, large
    functions, branches, calls and recursion. It estimates *measurement value*,
    not runtime cost.
    """

    def score(function: FunctionGenome) -> tuple[float, str]:
        value = (
            8.0 * function.max_loop_depth
            + 2.0 * function.loops
            + 1.5 * function.branches
            + 0.5 * function.calls
            + 0.15 * function.loc
            + 8.0 * function.direct_recursion
            + 2.0 * function.async_function
        )
        return -value, function.qualified_name

    return tuple(sorted((f for m in genome.modules for f in m.functions), key=score)[:limit])
