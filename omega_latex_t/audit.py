from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Mapping

from .bibliography import validate_bibliography
from .figure_ir import validate_figure_ir
from .math_ir import DimensionError, MathIRError, infer_dimension, render_math, symbol_units_from_specs
from .models import DocumentIR, NodeKind
from .uncertainty import validate_result
from .verifier_receipts import verifier_receipt_report


@dataclass(frozen=True)
class AuditFinding:
    code: str
    severity: str
    message: str
    node_id: str = ""
    def to_mapping(self): return asdict(self)

@dataclass(frozen=True)
class AuditReport:
    findings: tuple[AuditFinding,...]
    semantic_hash: str
    @property
    def errors(self): return tuple(x for x in self.findings if x.severity=="error")
    @property
    def warnings(self): return tuple(x for x in self.findings if x.severity=="warning")
    @property
    def passed(self): return not self.errors
    def to_mapping(self): return {"passed":self.passed,"semantic_hash":self.semantic_hash,"counts":{"errors":len(self.errors),"warnings":len(self.warnings),"total":len(self.findings)},"findings":[x.to_mapping() for x in self.findings]}

def _balanced_braces(value):
    depth=0; escaped=False
    for ch in value:
        if escaped: escaped=False; continue
        if ch=="\\": escaped=True; continue
        if ch=="{": depth+=1
        elif ch=="}":
            depth-=1
            if depth<0:return False
    return depth==0

def _environment_pairs(value):
    stack=[]
    for token in re.finditer(r"\\(begin|end)\{([^}]+)\}",value):
        mode,name=token.groups()
        if mode=="begin": stack.append(name)
        elif not stack or stack.pop()!=name:return False
    return not stack

def _cycle(doc):
    by_id={n.id:n for n in doc.nodes}; state={}; stack=[]
    def visit(node_id):
        state[node_id]=1; stack.append(node_id)
        for dep in by_id[node_id].dependencies:
            if dep not in by_id: continue
            if state.get(dep)==1:
                i=stack.index(dep); return tuple(stack[i:]+[dep])
            if state.get(dep,0)==0:
                found=visit(dep)
                if found:return found
        stack.pop(); state[node_id]=2; return ()
    for node_id in by_id:
        if state.get(node_id,0)==0:
            found=visit(node_id)
            if found:return found
    return ()

def _support_reviewed(node,source_ids):
    support=node.metadata.get("support",()) if isinstance(node.metadata,Mapping) else ()
    if not isinstance(support,(list,tuple)):return False
    for item in support:
        if not isinstance(item,Mapping):continue
        relation=str(item.get("relation","")).lower(); source=str(item.get("source",""))
        if item.get("reviewed") is True and relation in {"supports","derives","measures","verifies"} and source in source_ids:return True
    return False

def audit_document(doc:DocumentIR)->AuditReport:
    out=[]; ids=[n.id for n in doc.nodes]; known=set(ids); source_ids={s.id for s in doc.sources}
    if len(ids)!=len(known): out.append(AuditFinding("DOCIR_DUPLICATE_ID","error","Node IDs must be unique."))
    for finding in validate_bibliography(doc): out.append(AuditFinding(finding["code"],finding["severity"],finding["message"]))
    for node in doc.nodes:
        for dep in node.dependencies:
            if dep not in known: out.append(AuditFinding("DOCIR_MISSING_DEPENDENCY","error",f"Dependency {dep!r} does not exist.",node.id))
        for src in node.sources:
            if src not in source_ids: out.append(AuditFinding("PROVENANCE_UNKNOWN_SOURCE","error",f"Source {src!r} is not registered.",node.id))
        for src,locator in node.source_locators.items():
            if src not in node.sources: out.append(AuditFinding("SOURCE_LOCATOR_ORPHAN","error",f"Locator supplied for source {src!r} that is not attached to node.",node.id))
            if not str(locator).strip(): out.append(AuditFinding("SOURCE_LOCATOR_EMPTY","error",f"Locator for source {src!r} is empty.",node.id))
        equation_latex=node.content
        if node.kind==NodeKind.EQUATION and node.math_ir:
            try: equation_latex=render_math(node.math_ir)
            except MathIRError as exc: out.append(AuditFinding("MATH_IR_INVALID","error",str(exc),node.id)); equation_latex=""
            if equation_latex:
                try: infer_dimension(node.math_ir,symbol_units_from_specs(node.symbols))
                except DimensionError as exc:
                    message=str(exc); severity="warning" if "unit unknown" in message else "error"; out.append(AuditFinding("MATH_DIMENSION_UNKNOWN" if severity=="warning" else "MATH_DIMENSION_MISMATCH",severity,message,node.id))
        if node.kind==NodeKind.EQUATION and equation_latex and (not _balanced_braces(equation_latex) or not _environment_pairs(equation_latex)): out.append(AuditFinding("LATEX_UNBALANCED","error","Equation contains unbalanced braces or environments.",node.id))
        if node.dimension_lhs and node.dimension_rhs and node.dimension_lhs!=node.dimension_rhs: out.append(AuditFinding("DIMENSION_MISMATCH","error",f"Declared dimensions differ: {node.dimension_lhs!r} != {node.dimension_rhs!r}.",node.id))
        if node.kind==NodeKind.FIGURE and node.figure_ir:
            for finding in validate_figure_ir(node.figure_ir): out.append(AuditFinding(finding["code"],finding["severity"],finding["message"],node.id))
        strong=node.status.lower() in {"proven","established","measured","certified"}
        if strong and node.kind in {NodeKind.CLAIM,NodeKind.THEOREM,NodeKind.RESULT,NodeKind.EXPERIMENT}:
            if not node.sources and not node.dependencies: out.append(AuditFinding("EVIDENCE_BOUNDARY","warning","Strong status has neither registered sources nor dependencies.",node.id))
            if node.sources and not _support_reviewed(node,source_ids): out.append(AuditFinding("SOURCE_SUPPORT_UNREVIEWED","warning","Registered source is not yet marked as reviewed support/derivation/measurement/verification.",node.id))
            missing_locators=[src for src in node.sources if src not in node.source_locators and not next((s.locator for s in doc.sources if s.id==src),"")]
            if missing_locators: out.append(AuditFinding("SOURCE_LOCATOR_MISSING","warning",f"Strong node has sources without precise locator metadata: {sorted(missing_locators)}",node.id))
        if node.kind==NodeKind.THEOREM and node.status.lower()=="proven":
            proof_deps=[x for x in node.dependencies if x in known and next(n for n in doc.nodes if n.id==x).kind==NodeKind.PROOF]; reverse_proofs=[n.id for n in doc.nodes if n.kind==NodeKind.PROOF and node.id in n.dependencies]
            if not proof_deps and not reverse_proofs: out.append(AuditFinding("PROOF_MISSING","error","A theorem marked proven must be linked to a proof node.",node.id))
        if node.min_depth is not None and node.min_depth<0: out.append(AuditFinding("DEPTH_INVALID","error","min_depth must be >= 0.",node.id))
        if node.max_depth is not None and node.max_depth<0: out.append(AuditFinding("DEPTH_INVALID","error","max_depth must be >= 0.",node.id))
        if node.min_depth is not None and node.max_depth is not None and node.min_depth>node.max_depth: out.append(AuditFinding("DEPTH_RANGE_INVALID","error","min_depth cannot exceed max_depth.",node.id))
    cyc=_cycle(doc)
    if cyc: out.append(AuditFinding("DEPENDENCY_CYCLE","error","Dependency cycle: "+" -> ".join(cyc)))
    registry={}
    for node in doc.nodes:
        for spec in node.symbols:
            bucket=registry.setdefault((spec.scope,spec.symbol),{"meanings":set(),"units":set()})
            if spec.meaning.strip():bucket["meanings"].add(spec.meaning.strip())
            if spec.unit.strip():bucket["units"].add(spec.unit.strip())
    for (scope,symbol),bucket in sorted(registry.items()):
        if len(bucket["meanings"])>1: out.append(AuditFinding("SYMBOL_COLLISION","warning",f"{symbol!r} has multiple meanings in scope {scope!r}: {sorted(bucket['meanings'])}"))
        if len(bucket["units"])>1: out.append(AuditFinding("SYMBOL_UNIT_COLLISION","warning",f"{symbol!r} has multiple units in scope {scope!r}: {sorted(bucket['units'])}"))
    for key in sorted(doc.results):
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+",key): out.append(AuditFinding("RESULT_KEY_UNSAFE","error",f"Result key {key!r} contains unsupported characters."))
        for finding in validate_result(doc.results[key]): out.append(AuditFinding(finding["code"],finding["severity"],finding["message"],key))
    receipt_report=verifier_receipt_report(doc)
    for item in receipt_report["entries"]:
        if item.get("valid_receipt") is False: out.append(AuditFinding("VERIFIER_RECEIPT_INVALID","error","; ".join(item.get("reasons",[]))))
        elif item.get("verified_match") is False: out.append(AuditFinding("VERIFIER_RECEIPT_UNMATCHED","warning","; ".join(item.get("reasons",[]))))
    return AuditReport(tuple(out),doc.semantic_hash())
