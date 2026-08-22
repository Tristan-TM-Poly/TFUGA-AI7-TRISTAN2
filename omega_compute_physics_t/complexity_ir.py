"""Hardware-independent static Complexity-IR for Omega Compute Physics R0.5.

The IR is an auditable structural representation, not a cycle/FLOP oracle. It
can seed measurement design and later be calibrated against MachineGenome data.
"""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class IROp:
    kind: str
    count: int


@dataclass(frozen=True)
class FunctionIR:
    module: str
    qualified_name: str
    operations: tuple[IROp, ...]
    max_loop_depth: int
    call_targets: tuple[str, ...]
    status: str = "static-complexity-ir"
    oak_warning: str = (
        "Complexity-IR counts syntax-level operation classes. It does not directly "
        "equal FLOPs, bytes, runtime, memory traffic or asymptotic complexity."
    )

    def op_count(self, kind: str) -> int:
        return next((row.count for row in self.operations if row.kind == kind), 0)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _IRVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.calls: set[str] = set()
        self.depth = 0
        self.max_loop_depth = 0

    def bump(self, kind: str, amount: int = 1) -> None:
        self.counts[kind] = self.counts.get(kind, 0) + amount

    def _loop(self, node: ast.AST) -> None:
        self.bump("LOOP")
        self.depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.depth)
        self.generic_visit(node)
        self.depth -= 1

    def visit_For(self, node: ast.For) -> None: self._loop(node)
    def visit_AsyncFor(self, node: ast.AsyncFor) -> None: self._loop(node)
    def visit_While(self, node: ast.While) -> None: self._loop(node)

    def visit_If(self, node: ast.If) -> None:
        self.bump("BRANCH")
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.bump("BRANCH", max(1, len(node.cases)))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self.bump("CALL")
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        self.bump("ARITH")
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        self.bump("COMPARE", len(node.ops))
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.bump("INDEX")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.bump("STORE", max(1, len(node.targets)))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.bump("STORE")
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.bump("LOAD")
        self.bump("ARITH")
        self.bump("STORE")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load): self.bump("LOAD")
        elif isinstance(node.ctx, ast.Store): self.bump("STORE")

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.bump("ALLOC")
        self.bump("COMPREHENSION")
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.bump("ALLOC")
        self.bump("COMPREHENSION")
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.bump("ALLOC")
        self.bump("COMPREHENSION")
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        self.bump("AWAIT")
        self.generic_visit(node)

    def visit_Yield(self, node: ast.Yield) -> None:
        self.bump("YIELD")
        self.generic_visit(node)


def function_ir_from_node(module: str, qualified_name: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionIR:
    visitor = _IRVisitor()
    for statement in node.body:
        visitor.visit(statement)
    return FunctionIR(
        module=module,
        qualified_name=qualified_name,
        operations=tuple(IROp(kind, visitor.counts[kind]) for kind in sorted(visitor.counts)),
        max_loop_depth=visitor.max_loop_depth,
        call_targets=tuple(sorted(visitor.calls)),
    )


def compile_source_ir(source: str, *, module: str = "<memory>") -> tuple[FunctionIR, ...]:
    tree = ast.parse(source, filename=module)
    rows: list[FunctionIR] = []

    def walk(body: Sequence[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qn = f"{prefix}.{node.name}" if prefix else node.name
                rows.append(function_ir_from_node(module, qn, node))
                walk(node.body, qn)
            elif isinstance(node, ast.ClassDef):
                walk(node.body, f"{prefix}.{node.name}" if prefix else node.name)
    walk(tree.body)
    return tuple(rows)
