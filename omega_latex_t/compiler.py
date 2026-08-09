from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .ast import Command, Environment, Raw, Sequence, Text
from .audit import AuditReport, audit_document
from .bibliography import bibliography_latex, bibliography_report, source_key
from .evidence import evidence_matrix
from .figure_ir import figure_manifest, render_figure_ir
from .math_ir import render_math
from .models import DocumentIR, Node, NodeKind
from .notation import notation_registry, notation_rename_plan
from .uncertainty import render_result_latex, uncertainty_ledger
from .verifier_receipts import verifier_receipt_report

COMPILER_VERSION="0.8.0"

@dataclass(frozen=True)
class BuildArtifact:
    latex:str; audit:AuditReport; semantic_hash:str; latex_hash:str; cache_receipt:Mapping[str,Any]|None=None
    def manifest(self):
        payload={"compiler":"omega_latex_t","version":COMPILER_VERSION,"semantic_hash":self.semantic_hash,"latex_sha256":self.latex_hash,"oak_passed":self.audit.passed,"audit_counts":self.audit.to_mapping()["counts"]}
        if self.cache_receipt is not None: payload["cache"]=dict(self.cache_receipt)
        return payload

class DocumentCompiler:
    theorem_envs={NodeKind.DEFINITION:"definition",NodeKind.AXIOM:"axiom",NodeKind.CONJECTURE:"conjecture",NodeKind.LEMMA:"lemma",NodeKind.PROPOSITION:"proposition",NodeKind.THEOREM:"theorem",NodeKind.COROLLARY:"corollary"}
    def __init__(self,*,fail_on_audit_error=True): self.fail_on_audit_error=fail_on_audit_error
    def topological_nodes(self,doc):
        by_id={n.id:n for n in doc.nodes}; order={n.id:i for i,n in enumerate(doc.nodes)}; indegree={n.id:0 for n in doc.nodes}; children={n.id:[] for n in doc.nodes}
        for node in doc.nodes:
            for dep in node.dependencies:
                if dep in by_id: indegree[node.id]+=1; children[dep].append(node.id)
        ready=sorted((i for i,d in indegree.items() if d==0),key=order.get); result=[]
        while ready:
            current=ready.pop(0); result.append(by_id[current])
            for child in sorted(children[current],key=order.get):
                indegree[child]-=1
                if indegree[child]==0: ready.append(child); ready.sort(key=order.get)
        if len(result)!=len(doc.nodes): raise ValueError("dependency graph contains a cycle")
        return tuple(result)
    @staticmethod
    def _label_id(node_id): return "omega:"+"".join(ch if ch.isalnum() or ch in ":.-" else "-" for ch in node_id)
    @classmethod
    def _label(cls,node): return cls._label_id(node.id)
    @staticmethod
    def _result_definitions(doc):
        lines=[r"\makeatletter",r"\newcommand{\Result}[1]{\@ifundefined{omegaresult@#1}{\textbf{??}}{\csname omegaresult@#1\endcsname}}"]
        for key,value in sorted(doc.results.items()): lines.append(rf"\expandafter\def\csname omegaresult@{key}\endcsname{{{render_result_latex(value)}}}")
        lines.append(r"\makeatother"); return "\n".join(lines)
    @staticmethod
    def _source_refs(node):
        if not node.sources:return Raw("")
        rendered=[]
        for source_id in node.sources:
            locator=str(node.source_locators.get(source_id,"")).strip()
            rendered.append(rf"\cite[{Text(locator).render()}]{{{source_key(source_id)}}}" if locator else rf"\cite{{{source_key(source_id)}}}")
        return Raw(r"\par\smallskip\noindent\textit{Sources:} "+", ".join(rendered))
    def render_node(self,node,doc=None): return self._node_ast(node).render()
    def _node_ast(self,node):
        label=Raw(rf"\label{{{self._label(node)}}}"); status=Raw(rf"\texttt{{status={Text(node.status).render()}}}"); deps=Raw(r"\par\smallskip\noindent\textit{Dependencies:} "+", ".join(rf"\ref{{{self._label_id(x)}}}" for x in node.dependencies)) if node.dependencies else Raw(""); sources=self._source_refs(node)
        if node.kind==NodeKind.SECTION:return Sequence.of((Command("section",(Text(node.title or node.content),)),label))
        if node.kind==NodeKind.APPENDIX:return Sequence.of((Raw(r"\appendix"),Command("section",(Text(node.title or node.content),)),label))
        if node.kind==NodeKind.PARAGRAPH:
            title=Command("paragraph",(Text(node.title),)) if node.title else Raw(""); return Sequence.of((title,label,Text(node.content),deps,sources))
        if node.kind==NodeKind.EQUATION:
            equation=render_math(node.math_ir) if node.math_ir else node.content; return Sequence.of((Environment("equation",(Raw(equation),Raw(rf"\label{{{self._label(node)}}}"))),deps,sources))
        if node.kind==NodeKind.FIGURE and node.figure_ir:return Sequence.of((label,Raw(render_figure_ir(node.figure_ir,node_id=node.id,title=node.title)),deps,sources))
        if node.kind in self.theorem_envs:
            body=[label,Text(node.content),Raw(r"\par\smallskip"),status]
            if node.dependencies:body.append(deps)
            if node.sources:body.append(sources)
            return Environment(self.theorem_envs[node.kind],tuple(body),(Text(node.title).render(),) if node.title else ())
        if node.kind in {NodeKind.PROOF,NodeKind.PROOF_SKETCH}:
            head=Raw(r"\textit{Proof sketch.}") if node.kind==NodeKind.PROOF_SKETCH else Raw(""); return Environment("proof",(head,label,Text(node.content),deps,sources))
        if node.kind==NodeKind.WARNING:return Sequence.of((Raw(r"\begin{quote}\textbf{OAK warning.}"),label,Text(node.content),Raw(r"\end{quote}")))
        if node.kind==NodeKind.RESULT:
            title=node.title or "Result"; value=Raw(rf"\Result{{{node.result_key}}}") if node.result_key else Raw(r"\textbf{??}"); return Sequence.of((Command("subsection",(Text(title),)),label,Text(node.content),Raw(r"\par\smallskip\noindent\textbf{Value:} "),value,status,deps,sources))
        title=node.title or node.kind.value.replace("_"," ").title(); return Sequence.of((Command("subsection",(Text(title),)),label,Text(node.content),status,deps,sources))
    def _preamble(self,doc):
        language_pkg="french" if doc.meta.language.lower().startswith("fr") else "english"; items=[r"\documentclass[11pt]{article}",r"\usepackage[T1]{fontenc}",r"\usepackage[utf8]{inputenc}",rf"\usepackage[{language_pkg}]{{babel}}",r"\usepackage{amsmath,amssymb,amsthm}",r"\usepackage{hyperref}",r"\usepackage{geometry}",r"\geometry{margin=1in}"]
        if any(node.kind==NodeKind.FIGURE and node.figure_ir for node in doc.nodes):items += [r"\usepackage{tikz}",r"\usepackage{pgfplots}",r"\pgfplotsset{compat=1.18}"]
        items += [r"\newtheorem{definition}{Definition}[section]",r"\newtheorem{axiom}[definition]{Axiom}",r"\newtheorem{conjecture}[definition]{Conjecture}",r"\newtheorem{lemma}[definition]{Lemma}",r"\newtheorem{proposition}[definition]{Proposition}",r"\newtheorem{theorem}[definition]{Theorem}",r"\newtheorem{corollary}[definition]{Corollary}",self._result_definitions(doc),Command("title",(Text(doc.meta.title),)).render(),Command("author",(Text(doc.meta.author),)).render() if doc.meta.author else "",Command("date",(Text(doc.meta.date),)).render() if doc.meta.date else r"\date{}"]
        return items
    def assemble(self,doc,fragments,audit):
        if self.fail_on_audit_error and not audit.passed: raise ValueError("OAK audit failed: "+", ".join(x.code for x in audit.errors))
        body=[r"\begin{document}",r"\maketitle",rf"\noindent\texttt{{semantic-hash: {doc.semantic_hash()}}}"]+[fragments[node.id] for node in self.topological_nodes(doc)]; bib=bibliography_latex(doc)
        if bib:body.append(bib)
        body.append(r"\end{document}"); latex="\n".join(x for x in self._preamble(doc)+body if x!="")+"\n"; return BuildArtifact(latex,audit,doc.semantic_hash(),sha256(latex.encode("utf-8")).hexdigest())
    def render(self,doc):
        audit=audit_document(doc); return self.assemble(doc,{node.id:self.render_node(node,doc) for node in self.topological_nodes(doc)},audit)
    def render_incremental(self,doc,cache_dir,*,force_node_ids=()):
        from .incremental import incremental_fragments
        audit=audit_document(doc); fragments,receipt=incremental_fragments(self,doc,cache_dir,force_node_ids=force_node_ids); artifact=self.assemble(doc,fragments,audit); return BuildArtifact(artifact.latex,artifact.audit,artifact.semantic_hash,artifact.latex_hash,receipt.to_mapping())
    @staticmethod
    def _write_sidecars(doc,artifact,out):
        (out/"document.tex").write_text(artifact.latex,encoding="utf-8"); sidecars={"docir.json":doc.to_mapping(),"oak-report.json":artifact.audit.to_mapping(),"manifest.json":artifact.manifest(),"notation-registry.json":notation_registry(doc),"notation-rename-plan.json":notation_rename_plan(doc),"evidence-matrix.json":evidence_matrix(doc),"bibliography-report.json":bibliography_report(doc),"figure-manifest.json":figure_manifest(doc),"uncertainty-ledger.json":uncertainty_ledger(doc),"verifier-receipts.json":verifier_receipt_report(doc)}
        for name,payload in sidecars.items():(out/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        m_minus=[{"code":f.code,"severity":f.severity,"node_id":f.node_id,"message":f.message,"semantic_hash":doc.semantic_hash()} for f in artifact.audit.findings]; (out/"m_minus.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in m_minus),encoding="utf-8")
    def build_to(self,doc,output_dir):
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); artifact=self.render(doc); self._write_sidecars(doc,artifact,out); return artifact
    def build_incremental_to(self,doc,output_dir,cache_dir,*,force_node_ids=()):
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); artifact=self.render_incremental(doc,cache_dir,force_node_ids=force_node_ids); self._write_sidecars(doc,artifact,out); return artifact
