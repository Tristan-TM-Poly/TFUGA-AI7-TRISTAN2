from __future__ import annotations

from dataclasses import asdict, dataclass
import re

from .models import DocumentIR, NodeKind


@dataclass(frozen=True)
class AuditFinding:
    code: str
    severity: str
    message: str
    node_id: str = ""

    def to_mapping(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class AuditReport:
    findings: tuple[AuditFinding, ...]
    semantic_hash: str

    @property
    def errors(self) -> tuple[AuditFinding, ...]:
        return tuple(x for x in self.findings if x.severity == "error")

    @property
    def warnings(self) -> tuple[AuditFinding, ...]:
        return tuple(x for x in self.findings if x.severity == "warning")

    @property
    def passed(self) -> bool:
        return not self.errors

    def to_mapping(self) -> dict:
        return {"passed": self.passed, "semantic_hash": self.semantic_hash, "counts": {"errors": len(self.errors), "warnings": len(self.warnings), "total": len(self.findings)}, "findings": [x.to_mapping() for x in self.findings]}


def _balanced_braces(value: str) -> bool:
    depth = 0
    escaped = False
    for ch in value:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def _environment_pairs(value: str) -> bool:
    stack: list[str] = []
    for token in re.finditer(r"\\(begin|end)\{([^}]+)\}", value):
        mode, name = token.groups()
        if mode == "begin":
            stack.append(name)
        elif not stack or stack.pop() != name:
            return False
    return not stack


def _cycle(doc: DocumentIR) -> tuple[str, ...]:
    by_id = {n.id: n for n in doc.nodes}
    state: dict[str, int] = {}
    stack: list[str] = []
    def visit(node_id: str) -> tuple[str, ...]:
        state[node_id] = 1
        stack.append(node_id)
        for dep in by_id[node_id].dependencies:
            if dep not in by_id:
                continue
            if state.get(dep) == 1:
                i = stack.index(dep)
                return tuple(stack[i:] + [dep])
            if state.get(dep, 0) == 0:
                found = visit(dep)
                if found:
                    return found
        stack.pop()
        state[node_id] = 2
        return ()
    for node_id in by_id:
        if state.get(node_id, 0) == 0:
            found = visit(node_id)
            if found:
                return found
    return ()


def audit_document(doc: DocumentIR) -> AuditReport:
    out: list[AuditFinding] = []
    ids = [n.id for n in doc.nodes]
    known = set(ids)
    source_ids = {s.id for s in doc.sources}
    if len(ids) != len(known):
        out.append(AuditFinding("DOCIR_DUPLICATE_ID", "error", "Node IDs must be unique."))
    for node in doc.nodes:
        for dep in node.dependencies:
            if dep not in known:
                out.append(AuditFinding("DOCIR_MISSING_DEPENDENCY", "error", f"Dependency {dep!r} does not exist.", node.id))
        for src in node.sources:
            if src not in source_ids:
                out.append(AuditFinding("PROVENANCE_UNKNOWN_SOURCE", "error", f"Source {src!r} is not registered.", node.id))
        if node.kind == NodeKind.EQUATION and (not _balanced_braces(node.content) or not _environment_pairs(node.content)):
            out.append(AuditFinding("LATEX_UNBALANCED", "error", "Equation contains unbalanced braces or environments.", node.id))
        if node.dimension_lhs and node.dimension_rhs and node.dimension_lhs != node.dimension_rhs:
            out.append(AuditFinding("DIMENSION_MISMATCH", "error", f"Declared dimensions differ: {node.dimension_lhs!r} != {node.dimension_rhs!r}.", node.id))
        strong = node.status.lower() in {"proven", "established", "measured", "certified"}
        if strong and node.kind in {NodeKind.CLAIM, NodeKind.THEOREM, NodeKind.RESULT, NodeKind.EXPERIMENT} and not node.sources and not node.dependencies:
            out.append(AuditFinding("EVIDENCE_BOUNDARY", "warning", "Strong status has neither registered sources nor dependencies.", node.id))
        if node.kind == NodeKind.THEOREM and node.status.lower() == "proven":
            proof_deps = [x for x in node.dependencies if x in known and next(n for n in doc.nodes if n.id == x).kind == NodeKind.PROOF]
            reverse_proofs = [n.id for n in doc.nodes if n.kind == NodeKind.PROOF and node.id in n.dependencies]
            if not proof_deps and not reverse_proofs:
                out.append(AuditFinding("PROOF_MISSING", "error", "A theorem marked proven must be linked to a proof node.", node.id))
    cyc = _cycle(doc)
    if cyc:
        out.append(AuditFinding("DEPENDENCY_CYCLE", "error", "Dependency cycle: " + " -> ".join(cyc)))
    registry: dict[tuple[str, str], set[str]] = {}
    for node in doc.nodes:
        for spec in node.symbols:
            registry.setdefault((spec.scope, spec.symbol), set()).add(spec.meaning.strip())
    for (scope, symbol), meanings in sorted(registry.items()):
        meanings.discard("")
        if len(meanings) > 1:
            out.append(AuditFinding("SYMBOL_COLLISION", "warning", f"{symbol!r} has multiple meanings in scope {scope!r}: {sorted(meanings)}"))
    for key in sorted(doc.results):
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", key):
            out.append(AuditFinding("RESULT_KEY_UNSAFE", "error", f"Result key {key!r} contains unsupported characters."))
    return AuditReport(tuple(out), doc.semantic_hash())
