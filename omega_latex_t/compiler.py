from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .ast import Command, Environment, Raw, Sequence, Text
from .audit import AuditReport, audit_document
from .evidence import evidence_matrix
from .math_ir import render_math
from .models import DocumentIR, Node, NodeKind
from .notation import notation_registry, notation_rename_plan


COMPILER_VERSION = "0.5.0"


@dataclass(frozen=True)
class BuildArtifact:
    latex: str
    audit: AuditReport
    semantic_hash: str
    latex_hash: str
    cache_receipt: Mapping[str, Any] | None = None

    def manifest(self) -> dict[str, Any]:
        payload = {
            "compiler": "omega_latex_t",
            "version": COMPILER_VERSION,
            "semantic_hash": self.semantic_hash,
            "latex_sha256": self.latex_hash,
            "oak_passed": self.audit.passed,
            "audit_counts": self.audit.to_mapping()["counts"],
        }
        if self.cache_receipt is not None:
            payload["cache"] = dict(self.cache_receipt)
        return payload


class DocumentCompiler:
    theorem_envs = {
        NodeKind.DEFINITION: "definition",
        NodeKind.AXIOM: "axiom",
        NodeKind.CONJECTURE: "conjecture",
        NodeKind.LEMMA: "lemma",
        NodeKind.PROPOSITION: "proposition",
        NodeKind.THEOREM: "theorem",
        NodeKind.COROLLARY: "corollary",
    }

    def __init__(self, *, fail_on_audit_error: bool = True):
        self.fail_on_audit_error = fail_on_audit_error

    def topological_nodes(self, doc: DocumentIR) -> tuple[Node, ...]:
        by_id = {n.id: n for n in doc.nodes}
        order = {n.id: i for i, n in enumerate(doc.nodes)}
        indegree = {n.id: 0 for n in doc.nodes}
        children: dict[str, list[str]] = {n.id: [] for n in doc.nodes}
        for node in doc.nodes:
            for dep in node.dependencies:
                if dep in by_id:
                    indegree[node.id] += 1
                    children[dep].append(node.id)
        ready = sorted((i for i, d in indegree.items() if d == 0), key=order.get)
        result: list[Node] = []
        while ready:
            current = ready.pop(0)
            result.append(by_id[current])
            for child in sorted(children[current], key=order.get):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
                    ready.sort(key=order.get)
        if len(result) != len(doc.nodes):
            raise ValueError("dependency graph contains a cycle")
        return tuple(result)

    @staticmethod
    def _label_id(node_id: str) -> str:
        safe = "".join(ch if ch.isalnum() or ch in ":-." else "-" for ch in node_id)
        return f"omega:{safe}"

    @classmethod
    def _label(cls, node: Node) -> str:
        return cls._label_id(node.id)

    @staticmethod
    def _result_definitions(doc: DocumentIR) -> str:
        lines = [
            r"\makeatletter",
            r"\newcommand{\Result}[1]{\@ifundefined{omegaresult@#1}{\textbf{??}}{\csname omegaresult@#1\endcsname}}",
        ]
        for key, value in sorted(doc.results.items()):
            lines.append(
                rf"\expandafter\def\csname omegaresult@{key}\endcsname{{{Text(str(value)).render()}}}"
            )
        lines.append(r"\makeatother")
        return "\n".join(lines)

    def render_node(self, node: Node, doc: DocumentIR | None = None) -> str:
        return self._node_ast(node).render()

    def _node_ast(self, node: Node):
        label = Raw(rf"\label{{{self._label(node)}}}")
        status = Raw(rf"\texttt{{status={Text(node.status).render()}}}")
        deps = (
            Raw(
                r"\par\smallskip\noindent\textit{Dependencies:} "
                + ", ".join(rf"\ref{{{self._label_id(x)}}}" for x in node.dependencies)
            )
            if node.dependencies
            else Raw("")
        )
        sources = (
            Raw(
                r"\par\smallskip\noindent\textit{Sources:} "
                + ", ".join(Text(x).render() for x in node.sources)
            )
            if node.sources
            else Raw("")
        )
        if node.kind == NodeKind.SECTION:
            return Sequence.of((Command("section", (Text(node.title or node.content),)), label))
        if node.kind == NodeKind.APPENDIX:
            return Sequence.of(
                (Raw(r"\appendix"), Command("section", (Text(node.title or node.content),)), label)
            )
        if node.kind == NodeKind.PARAGRAPH:
            title = Command("paragraph", (Text(node.title),)) if node.title else Raw("")
            return Sequence.of((title, label, Text(node.content), deps, sources))
        if node.kind == NodeKind.EQUATION:
            equation = render_math(node.math_ir) if node.math_ir else node.content
            return Sequence.of(
                (
                    Environment("equation", (Raw(equation), Raw(rf"\label{{{self._label(node)}}}"))),
                    deps,
                    sources,
                )
            )
        if node.kind in self.theorem_envs:
            body = [label, Text(node.content), Raw(r"\par\smallskip"), status]
            if node.dependencies:
                body.append(deps)
            if node.sources:
                body.append(sources)
            return Environment(
                self.theorem_envs[node.kind],
                tuple(body),
                (Text(node.title).render(),) if node.title else (),
            )
        if node.kind in {NodeKind.PROOF, NodeKind.PROOF_SKETCH}:
            head = Raw(r"\textit{Proof sketch.}") if node.kind == NodeKind.PROOF_SKETCH else Raw("")
            return Environment("proof", (head, label, Text(node.content), deps, sources))
        if node.kind == NodeKind.WARNING:
            return Sequence.of(
                (
                    Raw(r"\begin{quote}\textbf{OAK warning.}"),
                    label,
                    Text(node.content),
                    Raw(r"\end{quote}"),
                )
            )
        if node.kind == NodeKind.RESULT:
            title = node.title or "Result"
            value = Raw(rf"\Result{{{node.result_key}}}") if node.result_key else Raw(r"\textbf{??}")
            return Sequence.of(
                (
                    Command("subsection", (Text(title),)),
                    label,
                    Text(node.content),
                    Raw(r"\par\smallskip\noindent\textbf{Value:} "),
                    value,
                    status,
                    deps,
                    sources,
                )
            )
        title = node.title or node.kind.value.replace("_", " ").title()
        return Sequence.of(
            (Command("subsection", (Text(title),)), label, Text(node.content), status, deps, sources)
        )

    def _preamble(self, doc: DocumentIR) -> list[str]:
        language_pkg = "french" if doc.meta.language.lower().startswith("fr") else "english"
        return [
            r"\documentclass[11pt]{article}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage[utf8]{inputenc}",
            rf"\usepackage[{language_pkg}]{{babel}}",
            r"\usepackage{amsmath,amssymb,amsthm}",
            r"\usepackage{hyperref}",
            r"\usepackage{geometry}",
            r"\geometry{margin=1in}",
            r"\newtheorem{definition}{Definition}[section]",
            r"\newtheorem{axiom}[definition]{Axiom}",
            r"\newtheorem{conjecture}[definition]{Conjecture}",
            r"\newtheorem{lemma}[definition]{Lemma}",
            r"\newtheorem{proposition}[definition]{Proposition}",
            r"\newtheorem{theorem}[definition]{Theorem}",
            r"\newtheorem{corollary}[definition]{Corollary}",
            self._result_definitions(doc),
            Command("title", (Text(doc.meta.title),)).render(),
            Command("author", (Text(doc.meta.author),)).render() if doc.meta.author else "",
            Command("date", (Text(doc.meta.date),)).render() if doc.meta.date else r"\date{}",
        ]

    def assemble(self, doc: DocumentIR, fragments: Mapping[str, str], audit: AuditReport) -> BuildArtifact:
        if self.fail_on_audit_error and not audit.passed:
            raise ValueError("OAK audit failed: " + ", ".join(x.code for x in audit.errors))
        body = [
            r"\begin{document}",
            r"\maketitle",
            rf"\noindent\texttt{{semantic-hash: {doc.semantic_hash()}}}",
        ]
        for node in self.topological_nodes(doc):
            body.append(fragments[node.id])
        body.append(r"\end{document}")
        latex = "\n".join(x for x in self._preamble(doc) + body if x != "") + "\n"
        return BuildArtifact(
            latex=latex,
            audit=audit,
            semantic_hash=doc.semantic_hash(),
            latex_hash=sha256(latex.encode("utf-8")).hexdigest(),
        )

    def render(self, doc: DocumentIR) -> BuildArtifact:
        audit = audit_document(doc)
        fragments = {node.id: self.render_node(node, doc) for node in self.topological_nodes(doc)}
        return self.assemble(doc, fragments, audit)

    def render_incremental(
        self,
        doc: DocumentIR,
        cache_dir: str | Path,
        *,
        force_node_ids: tuple[str, ...] = (),
    ) -> BuildArtifact:
        from .incremental import incremental_fragments

        audit = audit_document(doc)
        fragments, receipt = incremental_fragments(
            self,
            doc,
            cache_dir,
            force_node_ids=force_node_ids,
        )
        artifact = self.assemble(doc, fragments, audit)
        return BuildArtifact(
            latex=artifact.latex,
            audit=artifact.audit,
            semantic_hash=artifact.semantic_hash,
            latex_hash=artifact.latex_hash,
            cache_receipt=receipt.to_mapping(),
        )

    @staticmethod
    def _write_sidecars(doc: DocumentIR, artifact: BuildArtifact, out: Path) -> None:
        (out / "document.tex").write_text(artifact.latex, encoding="utf-8")
        (out / "docir.json").write_text(
            json.dumps(doc.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out / "oak-report.json").write_text(
            json.dumps(artifact.audit.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out / "manifest.json").write_text(
            json.dumps(artifact.manifest(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out / "notation-registry.json").write_text(
            json.dumps(notation_registry(doc), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out / "notation-rename-plan.json").write_text(
            json.dumps(notation_rename_plan(doc), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out / "evidence-matrix.json").write_text(
            json.dumps(evidence_matrix(doc), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        m_minus = [
            {
                "code": finding.code,
                "severity": finding.severity,
                "node_id": finding.node_id,
                "message": finding.message,
                "semantic_hash": doc.semantic_hash(),
            }
            for finding in artifact.audit.findings
        ]
        (out / "m_minus.jsonl").write_text(
            "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in m_minus),
            encoding="utf-8",
        )

    def build_to(self, doc: DocumentIR, output_dir: str | Path) -> BuildArtifact:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        artifact = self.render(doc)
        self._write_sidecars(doc, artifact, out)
        return artifact

    def build_incremental_to(
        self,
        doc: DocumentIR,
        output_dir: str | Path,
        cache_dir: str | Path,
        *,
        force_node_ids: tuple[str, ...] = (),
    ) -> BuildArtifact:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        artifact = self.render_incremental(doc, cache_dir, force_node_ids=force_node_ids)
        self._write_sidecars(doc, artifact, out)
        return artifact
