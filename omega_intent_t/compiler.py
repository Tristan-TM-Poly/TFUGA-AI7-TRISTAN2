from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .generators import (
    DocumentGenerator,
    GeneratedArtifact,
    MetaGenerator,
    ScaffoldGenerator,
    addition_records,
)
from .graph import EvidenceHypergraph
from .models import (
    Claim,
    GeneratorSpec,
    GraphEdge,
    GraphNode,
    Intent,
    OakReport,
    Requirement,
    WorkUnit,
    canonical_json,
    stable_digest,
)
from .oak import run_oak_gate
from .planner import LogicalFrontier, WorkPlanner


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(dict(row)) + "\n")
            count += 1
    return count


@dataclass(frozen=True)
class CompilationResult:
    output_dir: str
    intent: Intent
    requirements: tuple[Requirement, ...]
    claims: tuple[Claim, ...]
    work_units: tuple[WorkUnit, ...]
    generators: tuple[GeneratorSpec, ...]
    artifacts: tuple[GeneratedArtifact, ...]
    oak_report: OakReport
    topological_batches: tuple[tuple[str, ...], ...]
    additions: int
    github_plan: Mapping[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "omega-intent-compilation-result/v1",
            "output_dir": self.output_dir,
            "intent_id": self.intent.intent_id,
            "requirements": len(self.requirements),
            "claims": len(self.claims),
            "work_units": len(self.work_units),
            "generators": len(self.generators),
            "artifacts": len(self.artifacts),
            "execution_batches": len(self.topological_batches),
            "logical_additions": self.additions,
            "oak_passed": self.oak_report.passed,
            "github_plan": dict(self.github_plan) if self.github_plan is not None else None,
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
            "automatic_merge": False,
        }


class IntentCompiler:
    """Compile a human intention into deterministic, reviewable execution assets."""

    def __init__(self) -> None:
        self.work_planner = WorkPlanner()
        self.meta_generator = MetaGenerator()
        self.document_generator = DocumentGenerator()
        self.scaffold_generator = ScaffoldGenerator()

    def compile(
        self,
        intent: Intent,
        output_dir: str | Path,
        *,
        materialize_scaffolds: bool = False,
        github_plan: bool = False,
        proposed_branch: str = "feat/omega-intent-generated",
        require_provenance: bool = True,
    ) -> CompilationResult:
        root = Path(output_dir)
        if root.exists() and any(root.iterdir()):
            raise FileExistsError(f"output directory is not empty: {root}")
        root.mkdir(parents=True, exist_ok=True)

        requirements = self.work_planner.derive_requirements(intent)
        work_units = self.work_planner.plan(intent, requirements)
        batches = self.work_planner.topological_batches(work_units)
        generators = self.meta_generator.compile(work_units)
        claims = self._derive_claims(requirements)
        documents = self.document_generator.generate(intent, requirements, work_units, batches)
        scaffolds = self.scaffold_generator.generate(intent, work_units) if materialize_scaffolds else ()
        artifacts = (*documents, *scaffolds)
        graph = self._build_graph(intent, requirements, claims, work_units, generators, artifacts)
        oak_report = run_oak_gate(intent, requirements, work_units, graph)

        self._write_bundle(
            root,
            intent=intent,
            requirements=requirements,
            claims=claims,
            work_units=work_units,
            generators=generators,
            artifacts=artifacts,
            graph=graph,
            batches=batches,
            oak_report=oak_report,
        )
        additions_path = root / "additions.jsonl"
        additions = _write_jsonl(
            additions_path,
            addition_records(intent, requirements, work_units, generators, artifacts),
        )
        github_report = self._compile_github_plan(
            additions_path,
            root / "github-plan",
            proposed_branch=proposed_branch,
            require_provenance=require_provenance,
        ) if github_plan else None

        result = CompilationResult(
            output_dir=str(root),
            intent=intent,
            requirements=requirements,
            claims=claims,
            work_units=work_units,
            generators=generators,
            artifacts=tuple(artifacts),
            oak_report=oak_report,
            topological_batches=batches,
            additions=additions,
            github_plan=github_report,
        )
        _write_json(root / "compilation-result.json", result.to_dict())
        return result

    @staticmethod
    def _derive_claims(requirements: Sequence[Requirement]) -> tuple[Claim, ...]:
        return tuple(
            Claim(
                claim_id=f"CLAIM-{stable_digest((req.requirement_id, req.statement))[:16].upper()}",
                statement=f"The requirement {req.requirement_id} is satisfiable by a generated and validated artifact.",
                status="FERTILE",
                evidence_required=tuple(req.acceptance),
                source_requirement_ids=(req.requirement_id,),
            )
            for req in requirements
        )

    @staticmethod
    def _build_graph(
        intent: Intent,
        requirements: Sequence[Requirement],
        claims: Sequence[Claim],
        work_units: Sequence[WorkUnit],
        generators: Sequence[GeneratorSpec],
        artifacts: Sequence[GeneratedArtifact],
    ) -> EvidenceHypergraph:
        graph = EvidenceHypergraph()
        graph.add_node(GraphNode(intent.intent_id, "intent", intent.objective, {"mode": intent.mode}))
        for req in requirements:
            graph.add_node(GraphNode(req.requirement_id, "requirement", req.statement, {"category": req.category}))
            graph.add_edge(GraphEdge(intent.intent_id, "decomposes_into", req.requirement_id))
        for claim in claims:
            graph.add_node(GraphNode(claim.claim_id, "claim", claim.statement, {"status": claim.status}))
            for req_id in claim.source_requirement_ids:
                graph.add_edge(GraphEdge(req_id, "gives_rise_to", claim.claim_id))
        for unit in work_units:
            graph.add_node(GraphNode(unit.work_unit_id, "work_unit", unit.objective, {"kind": unit.kind}))
            for req_id in unit.requirement_ids:
                graph.add_edge(GraphEdge(req_id, "implemented_by", unit.work_unit_id))
            for dep_id in unit.dependency_ids:
                graph.add_edge(GraphEdge(unit.work_unit_id, "depends_on", dep_id))
        for spec in generators:
            graph.add_node(GraphNode(spec.generator_id, "generator", spec.generator_type, {"template": spec.template}))
            graph.add_edge(GraphEdge(spec.work_unit_id, "compiled_into_generator", spec.generator_id))
        for artifact in artifacts:
            artifact_id = f"ART-{artifact.sha256[:16].upper()}"
            graph.add_node(GraphNode(artifact_id, "artifact", artifact.path, artifact.to_dict()))
            graph.add_edge(GraphEdge(intent.intent_id, "produces", artifact_id))
        return graph

    @staticmethod
    def _write_bundle(
        root: Path,
        *,
        intent: Intent,
        requirements: Sequence[Requirement],
        claims: Sequence[Claim],
        work_units: Sequence[WorkUnit],
        generators: Sequence[GeneratorSpec],
        artifacts: Sequence[GeneratedArtifact],
        graph: EvidenceHypergraph,
        batches: Sequence[Sequence[str]],
        oak_report: OakReport,
    ) -> None:
        _write_json(root / "intent.json", intent.to_dict())
        _write_jsonl(root / "requirements.jsonl", (item.to_dict() for item in requirements))
        _write_jsonl(root / "claims.jsonl", (item.to_dict() for item in claims))
        _write_jsonl(root / "work-units.jsonl", (item.to_dict() for item in work_units))
        _write_jsonl(root / "generator-specs.jsonl", (item.to_dict() for item in generators))
        _write_json(root / "execution-plan.json", {
            "schema": "omega-intent-execution-plan/v1",
            "batches": [list(batch) for batch in batches],
            "work_units": len(work_units),
            "remote_mutations": 0,
            "automatic_merge": False,
        })
        _write_json(root / "hypergraph.json", graph.to_dict())
        (root / "hypergraph.graphml").write_text(graph.to_graphml(), encoding="utf-8")
        for artifact in artifacts:
            path = root / artifact.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(artifact.content, encoding="utf-8")
        _write_json(root / "artifact-manifest.json", {
            "schema": "omega-intent-artifact-manifest/v1",
            "artifacts": [artifact.to_dict() for artifact in artifacts],
        })
        _write_json(root / "reports" / "oak.json", oak_report.to_dict())
        (root / "reports" / "executive.md").write_text(
            IntentCompiler._executive_report(intent, requirements, work_units, generators, artifacts, oak_report),
            encoding="utf-8",
        )
        _write_json(root / "next-intent.json", IntentCompiler._next_intent(intent, oak_report))
        _write_json(root / "checkpoint.json", {
            "schema": "omega-intent-checkpoint/v1",
            "intent_id": intent.intent_id,
            "state": "compiled" if oak_report.passed else "blocked_by_oak",
            "completed_work_units": [],
            "planned_work_units": [unit.work_unit_id for unit in work_units],
            "resume_from_batch": 0,
            "bundle_digest": stable_digest({
                "intent": intent.to_dict(),
                "requirements": [item.to_dict() for item in requirements],
                "work_units": [item.to_dict() for item in work_units],
            }),
        })
        _write_json(root / "frontier-manifest.json", LogicalFrontier().manifest())

    @staticmethod
    def _executive_report(
        intent: Intent,
        requirements: Sequence[Requirement],
        work_units: Sequence[WorkUnit],
        generators: Sequence[GeneratorSpec],
        artifacts: Sequence[GeneratedArtifact],
        oak_report: OakReport,
    ) -> str:
        status = "PASSED" if oak_report.passed else "BLOCKED"
        return f"""# Ω-INTENT-TO-EVERYTHING-T∞ compilation report

## Executive status

- Intent: `{intent.intent_id}`
- OAK gate: **{status}**
- Requirements: **{len(requirements)}**
- Work units: **{len(work_units)}**
- Generator specifications: **{len(generators)}**
- Materialized artifacts: **{len(artifacts)}**
- Remote mutations: **0**
- Automatic merge: **false**

## Objective

{intent.objective}

## Epistemic boundary

This compilation proves that the intent can be normalized, decomposed, traced,
planned and rendered into reviewable contracts. It does not prove that generated
scientific theories are true, that scaffolds are complete implementations, or
that performance, product-market fit or patentability has been established.

## Residual policy

Failures, missing evidence, blocked IP decisions and regressions must become
traceable corrective intentions and M-minus entries rather than being hidden.
"""

    @staticmethod
    def _next_intent(intent: Intent, oak_report: OakReport) -> dict[str, Any]:
        failed = [check for check in oak_report.checks if not check.passed]
        objective = (
            f"Correct the failed OAK checks for {intent.intent_id}: "
            + "; ".join(check.check_id for check in failed)
            if failed
            else f"Execute and validate the planned work units for {intent.intent_id}, then promote only evidence-backed outputs."
        )
        return Intent.from_mapping({
            "objective": objective,
            "expected_outputs": ["code", "tests", "benchmarks", "reports"],
            "epistemic_constraints": list(intent.epistemic_constraints),
            "completion_conditions": ["all_planned_work_units_resolved", "oak_gate_passes", "residuals_declared"],
            "languages": list(intent.languages),
            "mode": "focused",
            "metadata": {"parent_intent_id": intent.intent_id, "generated_by": "omega_intent_t"},
        }).to_dict()

    @staticmethod
    def _compile_github_plan(
        additions_path: Path,
        output_dir: Path,
        *,
        proposed_branch: str,
        require_provenance: bool,
    ) -> Mapping[str, Any]:
        from omega_unbounded_t.github_planner import GitHubDryRunPlanner, GitHubPlanPolicy, iter_jsonl

        planner = GitHubDryRunPlanner(
            output_dir,
            policy=GitHubPlanPolicy(require_provenance=require_provenance),
            proposed_branch=proposed_branch,
        )
        return planner.plan(iter_jsonl(additions_path)).to_dict()


def load_intent(path_or_text: str, *, languages: Sequence[str] = ("python",), mode: str = "expansive") -> Intent:
    path = Path(path_or_text)
    try:
        exists = path.exists()
    except OSError:
        exists = False
    if exists:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            raw = json.loads(text)
            if not isinstance(raw, Mapping):
                raise TypeError("intent JSON must contain an object")
            return Intent.from_mapping(raw)
        return Intent.from_text(text, languages=languages, mode=mode)
    return Intent.from_text(path_or_text, languages=languages, mode=mode)
