"""Ω-PROBLEM-ATLAS-T∞ R0.3 MAX engine.

The MAX layer turns each conservative problem family into a portfolio of
explicit research targets and evidence-bearing work cells.  It replaces
hash-derived priorities with transparent profiles, enforces domain diversity,
and emits file-level receipts that can be independently audited.

The engine does not certify that a problem is open and never claims a proof or
solution.  Unverified source status lowers routing priority instead of being
silently treated as current fact.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import unicodedata
from typing import Any, Iterable, Mapping, Sequence

from .atlas import (
    ATTACK_MODES,
    FRONTS,
    DEFAULT_SOURCE_REGISTRY,
    ProblemRecord,
    build_seed_records,
    ingest_jsonl,
    load_source_registry,
    stable_digest,
)


TARGET_KINDS: tuple[str, ...] = (
    "canonical_statement",
    "literature_status_audit",
    "equivalent_form",
    "known_case_reconstruction",
    "toy_model",
    "finite_case",
    "weakened_form",
    "conditional_theorem",
    "barrier_or_no_go_test",
    "counterexample_frontier",
    "computational_certificate",
    "formalization_target",
)

METHOD_FAMILIES: tuple[str, ...] = (
    "algebraic_geometry",
    "algebraic_topology",
    "analytic_number_theory",
    "automatic_differentiation",
    "bayesian_inference",
    "category_theory",
    "certified_numerics",
    "combinatorial_optimization",
    "complex_analysis",
    "computational_algebra",
    "convex_analysis",
    "differential_geometry",
    "dynamic_programming",
    "energy_entropy_methods",
    "finite_model_search",
    "formal_proof_assistants",
    "fourier_harmonic_analysis",
    "graph_hypergraph_methods",
    "information_theory",
    "integer_linear_programming",
    "interval_arithmetic",
    "lie_groups_representations",
    "machine_learning_for_conjectures",
    "monte_carlo",
    "operator_algebras",
    "probabilistic_method",
    "representation_theory",
    "sat_smt_constraint_solving",
    "scientific_computing",
    "spectral_methods",
    "symbolic_computation",
    "variational_methods",
)

_DEFAULT_METHODS = (
    "symbolic_computation",
    "certified_numerics",
    "formal_proof_assistants",
    "finite_model_search",
)

FRONT_METHODS: Mapping[str, tuple[str, ...]] = {
    "analytic_number_theory": ("analytic_number_theory", "complex_analysis", "spectral_methods", "symbolic_computation"),
    "algebraic_diophantine_geometry": ("algebraic_geometry", "computational_algebra", "analytic_number_theory", "formal_proof_assistants"),
    "additive_combinatorics": ("probabilistic_method", "fourier_harmonic_analysis", "graph_hypergraph_methods", "finite_model_search"),
    "graphs_hypergraphs": ("graph_hypergraph_methods", "sat_smt_constraint_solving", "combinatorial_optimization", "spectral_methods"),
    "discrete_geometry": ("combinatorial_optimization", "sat_smt_constraint_solving", "computational_algebra", "certified_numerics"),
    "algebraic_geometry": ("algebraic_geometry", "category_theory", "computational_algebra", "formal_proof_assistants"),
    "topology_differential_geometry": ("algebraic_topology", "differential_geometry", "variational_methods", "formal_proof_assistants"),
    "harmonic_analysis": ("fourier_harmonic_analysis", "complex_analysis", "spectral_methods", "energy_entropy_methods"),
    "partial_differential_equations": ("energy_entropy_methods", "variational_methods", "certified_numerics", "spectral_methods"),
    "dynamical_systems": ("spectral_methods", "scientific_computing", "interval_arithmetic", "bayesian_inference"),
    "probability_random_structures": ("probabilistic_method", "monte_carlo", "spectral_methods", "bayesian_inference"),
    "optimization_operations_research": ("convex_analysis", "integer_linear_programming", "dynamic_programming", "combinatorial_optimization"),
    "algebra_representation_theory": ("representation_theory", "lie_groups_representations", "computational_algebra", "category_theory"),
    "logic_foundations": ("formal_proof_assistants", "finite_model_search", "sat_smt_constraint_solving", "category_theory"),
    "computational_complexity": ("combinatorial_optimization", "information_theory", "sat_smt_constraint_solving", "probabilistic_method"),
    "quantum_computation": ("operator_algebras", "information_theory", "spectral_methods", "scientific_computing"),
    "quantum_information": ("operator_algebras", "information_theory", "convex_analysis", "computational_algebra"),
    "mathematical_physics": ("lie_groups_representations", "operator_algebras", "variational_methods", "certified_numerics"),
    "information_coding": ("information_theory", "graph_hypergraph_methods", "integer_linear_programming", "probabilistic_method"),
    "numerical_mathematics": ("certified_numerics", "interval_arithmetic", "scientific_computing", "automatic_differentiation"),
    "computational_geometry": ("combinatorial_optimization", "integer_linear_programming", "finite_model_search", "certified_numerics"),
    "mathematical_biology": ("dynamical_systems" if "dynamical_systems" in METHOD_FAMILIES else "scientific_computing", "bayesian_inference", "variational_methods", "machine_learning_for_conjectures"),
    "mathematics_of_ai": ("information_theory", "convex_analysis", "machine_learning_for_conjectures", "formal_proof_assistants"),
    "tristan_generated_mathematics": ("graph_hypergraph_methods", "information_theory", "certified_numerics", "formal_proof_assistants"),
}

TARGET_PROFILE: Mapping[str, tuple[float, float, float, float]] = {
    "canonical_statement": (0.70, 0.92, 0.95, 0.90),
    "literature_status_audit": (0.65, 0.88, 0.98, 0.55),
    "equivalent_form": (0.86, 0.96, 0.68, 0.78),
    "known_case_reconstruction": (0.78, 0.84, 0.96, 0.94),
    "toy_model": (0.74, 0.70, 0.98, 0.82),
    "finite_case": (0.72, 0.76, 0.99, 0.84),
    "weakened_form": (0.88, 0.90, 0.78, 0.82),
    "conditional_theorem": (0.91, 0.93, 0.72, 0.86),
    "barrier_or_no_go_test": (0.90, 0.95, 0.92, 0.72),
    "counterexample_frontier": (0.82, 0.86, 0.98, 0.68),
    "computational_certificate": (0.76, 0.82, 0.99, 0.88),
    "formalization_target": (0.80, 0.90, 0.92, 0.99),
}

MODE_PROFILE: Mapping[str, tuple[float, float, float, float, float]] = {
    "statement_and_provenance_audit": (0.62, 0.90, 0.99, 0.72, 0.16),
    "toy_model": (0.70, 0.72, 0.98, 0.80, 0.30),
    "finite_or_low_dimensional_case": (0.72, 0.78, 0.99, 0.86, 0.28),
    "weakened_or_restricted_form": (0.84, 0.88, 0.82, 0.84, 0.38),
    "conditional_implication": (0.88, 0.92, 0.74, 0.88, 0.42),
    "counterexample_search": (0.80, 0.84, 0.99, 0.66, 0.46),
    "formalization_skeleton": (0.76, 0.90, 0.88, 0.99, 0.24),
    "numerical_or_symbolic_benchmark": (0.74, 0.82, 0.99, 0.80, 0.50),
}


@dataclass(frozen=True)
class ResearchTarget:
    target_id: str
    problem_id: str
    front: str
    target_kind: str
    objective: str
    required_evidence: tuple[str, ...]
    falsifier: str
    status: str = "candidate"
    proof_claimed: bool = False
    solution_claimed: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.target_kind not in TARGET_KINDS:
            errors.append("unknown target_kind")
        if self.front not in FRONTS:
            errors.append("unknown front")
        if not self.target_id or not self.problem_id or not self.objective:
            errors.append("blank target identity or objective")
        if not self.required_evidence:
            errors.append("required_evidence is empty")
        if not self.falsifier:
            errors.append("falsifier is empty")
        if self.proof_claimed or self.solution_claimed:
            errors.append("candidate targets cannot claim proof or solution")
        return tuple(errors)


@dataclass(frozen=True)
class MaxResearchCell:
    cell_id: str
    target_id: str
    problem_id: str
    front: str
    attack_mode: str
    methods: tuple[str, ...]
    objective: str
    fertility: float
    transferability: float
    testability: float
    formalizability: float
    evidence_readiness: float
    uncertainty: float
    false_progress_risk: float
    priority_score: float
    scoring_basis: str = "transparent_profile_v1"
    status: str = "candidate"
    proof_claimed: bool = False
    solution_claimed: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.attack_mode not in ATTACK_MODES:
            errors.append("unknown attack_mode")
        if self.front not in FRONTS:
            errors.append("unknown front")
        if not self.methods or set(self.methods) - set(METHOD_FAMILIES):
            errors.append("unknown or empty methods")
        for name in (
            "fertility", "transferability", "testability", "formalizability",
            "evidence_readiness", "uncertainty", "false_progress_risk",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                errors.append(f"{name} outside [0, 1]")
        if self.priority_score < 0:
            errors.append("negative priority_score")
        if self.proof_claimed or self.solution_claimed:
            errors.append("candidate cells cannot claim proof or solution")
        return tuple(errors)


def unicode_canonical_key(title: str) -> str:
    """Normalize while retaining meaningful non-ASCII letters such as ő or ζ."""
    normalized = unicodedata.normalize("NFKC", title).casefold()
    tokens: list[str] = []
    current: list[str] = []
    for char in normalized:
        if char.isalnum():
            current.append(char)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return " ".join(tokens)


def deduplicate_records_max(records: Iterable[ProblemRecord]) -> tuple[ProblemRecord, ...]:
    """Deduplicate by Unicode title key and prefer stronger provenance."""
    selected: dict[str, ProblemRecord] = {}
    for original in records:
        record = replace(original, canonical_key=unicode_canonical_key(original.title))
        key = record.canonical_key
        current = selected.get(key)
        if current is None:
            selected[key] = record
            continue
        current_rank = (
            bool(current.source_verified_at),
            bool(current.source_locator),
            current.source_id not in {"requires_source_resolution", "external_import"},
            bool(current.statement),
            current.provenance_digest,
        )
        candidate_rank = (
            bool(record.source_verified_at),
            bool(record.source_locator),
            record.source_id not in {"requires_source_resolution", "external_import"},
            bool(record.statement),
            record.provenance_digest,
        )
        if candidate_rank > current_rank:
            selected[key] = record
    return tuple(sorted(selected.values(), key=lambda item: (item.front, item.problem_id)))


def _target_text(record: ProblemRecord, target_kind: str) -> tuple[str, tuple[str, ...], str]:
    title = record.title
    specs: Mapping[str, tuple[str, tuple[str, ...], str]] = {
        "canonical_statement": (
            f"Recover a typed, quantified and source-pinned statement for {title}.",
            ("primary source locator", "quantifier and domain audit"),
            "Two accepted sources encode materially different claims.",
        ),
        "literature_status_audit": (
            f"Determine the dated literature status and strongest verified partial results for {title}.",
            ("dated search record", "primary literature references"),
            "A newer source contradicts the recorded status or bound.",
        ),
        "equivalent_form": (
            f"Prove or refute both directions of a useful equivalent formulation of {title}.",
            ("two directional implication records", "assumption ledger"),
            "One direction fails or requires an omitted assumption.",
        ),
        "known_case_reconstruction": (
            f"Independently reconstruct a known solved case adjacent to {title}.",
            ("reproducible derivation", "comparison with accepted proof"),
            "The reconstruction fails on an accepted dependency or boundary case.",
        ),
        "toy_model": (
            f"Define the smallest nontrivial toy model preserving a core obstruction of {title}.",
            ("explicit model", "mapping to and limits against the original problem"),
            "The toy model removes the obstruction it was intended to preserve.",
        ),
        "finite_case": (
            f"Classify or certify a finite or low-dimensional frontier for {title}.",
            ("complete search specification", "independently checkable certificate"),
            "A missed case or non-reproducible certificate invalidates completeness.",
        ),
        "weakened_form": (
            f"State and attack a strictly weaker but transferable theorem related to {title}.",
            ("logical comparison to original", "proof or counterexample for restricted scope"),
            "The proposed statement is not actually weaker or does not transfer.",
        ),
        "conditional_theorem": (
            f"Derive a non-circular conditional implication advancing {title}.",
            ("dependency graph", "explicit undischarged assumptions"),
            "The conclusion is hidden in an assumption or dependency cycle.",
        ),
        "barrier_or_no_go_test": (
            f"Test a known or candidate methodological barrier around {title}.",
            ("method class definition", "adversarial witness or separation"),
            "The tested method lies outside the declared barrier class.",
        ),
        "counterexample_frontier": (
            f"Search adversarially for counterexamples to restricted claims around {title}.",
            ("search space contract", "witness verifier"),
            "The verifier rejects the witness or the search silently excludes valid objects.",
        ),
        "computational_certificate": (
            f"Produce a deterministic, independently verifiable computation relevant to {title}.",
            ("code and environment receipt", "exact or interval certificate"),
            "Independent replay changes the result or exceeds declared error bounds.",
        ),
        "formalization_target": (
            f"Formalize a scoped definition or lemma relevant to {title} without placeholders.",
            ("kernel-checked artifact", "source-to-formal statement correspondence"),
            "The kernel rejects the artifact or the formal statement drifts from the source.",
        ),
    }
    return specs[target_kind]


def expand_research_targets(records: Sequence[ProblemRecord]) -> tuple[ResearchTarget, ...]:
    targets: list[ResearchTarget] = []
    for record in records:
        for target_kind in TARGET_KINDS:
            objective, evidence, falsifier = _target_text(record, target_kind)
            target = ResearchTarget(
                target_id=f"{record.problem_id}::{target_kind}",
                problem_id=record.problem_id,
                front=record.front,
                target_kind=target_kind,
                objective=objective,
                required_evidence=evidence,
                falsifier=falsifier,
            )
            errors = target.validate()
            if errors:
                raise ValueError(f"invalid target {target.target_id}: {errors}")
            targets.append(target)
    return tuple(sorted(targets, key=lambda target: target.target_id))


def _methods(front: str, mode: str) -> tuple[str, ...]:
    methods = list(FRONT_METHODS.get(front, _DEFAULT_METHODS))
    if mode == "formalization_skeleton":
        methods.append("formal_proof_assistants")
    if mode == "counterexample_search":
        methods.extend(("sat_smt_constraint_solving", "finite_model_search"))
    if mode == "numerical_or_symbolic_benchmark":
        methods.extend(("certified_numerics", "symbolic_computation"))
    return tuple(dict.fromkeys(methods))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def expand_max_cells(
    records: Sequence[ProblemRecord], targets: Sequence[ResearchTarget]
) -> tuple[MaxResearchCell, ...]:
    record_by_id = {record.problem_id: record for record in records}
    cells: list[MaxResearchCell] = []
    for target in targets:
        record = record_by_id[target.problem_id]
        target_profile = TARGET_PROFILE[target.target_kind]
        for mode in ATTACK_MODES:
            mode_profile = MODE_PROFILE[mode]
            fertility = round((target_profile[0] + mode_profile[0]) / 2.0, 6)
            transferability = round((target_profile[1] + mode_profile[1]) / 2.0, 6)
            testability = round((target_profile[2] + mode_profile[2]) / 2.0, 6)
            formalizability = round((target_profile[3] + mode_profile[3]) / 2.0, 6)
            evidence_readiness = 0.96 if record.source_verified_at else 0.52
            if record.status == "solved_benchmark":
                evidence_readiness = max(evidence_readiness, 0.88)
            uncertainty = 0.24 if record.source_verified_at else 0.68
            if record.source_id in {"requires_source_resolution", "external_import"}:
                uncertainty += 0.10
            if record.source_id == "tristan_internal":
                uncertainty += 0.12
            uncertainty = round(_clamp(uncertainty), 6)
            false_progress_risk = round(_clamp(mode_profile[4] + (0.12 if not record.statement else 0.0)), 6)
            benefit = (
                0.30 * fertility
                + 0.30 * transferability
                + 0.20 * testability
                + 0.20 * formalizability
            )
            priority = round(
                benefit * evidence_readiness / (0.45 + uncertainty + false_progress_risk),
                9,
            )
            cell = MaxResearchCell(
                cell_id=f"{target.target_id}::{mode}",
                target_id=target.target_id,
                problem_id=target.problem_id,
                front=target.front,
                attack_mode=mode,
                methods=_methods(target.front, mode),
                objective=f"{target.objective} Attack mode: {mode.replace('_', ' ')}.",
                fertility=fertility,
                transferability=transferability,
                testability=testability,
                formalizability=formalizability,
                evidence_readiness=evidence_readiness,
                uncertainty=uncertainty,
                false_progress_risk=false_progress_risk,
                priority_score=priority,
            )
            errors = cell.validate()
            if errors:
                raise ValueError(f"invalid MAX cell {cell.cell_id}: {errors}")
            cells.append(cell)
    return tuple(sorted(cells, key=lambda cell: cell.cell_id))


def _balanced_select(
    cells: Sequence[MaxResearchCell],
    budget: int,
    *,
    excluded_ids: set[str] | None = None,
    max_per_problem: int = 1,
    max_per_target: int = 1,
) -> list[MaxResearchCell]:
    if budget < 0:
        raise ValueError("budget must be non-negative")
    excluded = excluded_ids or set()
    ranked_by_front: dict[str, list[MaxResearchCell]] = defaultdict(list)
    for cell in sorted(cells, key=lambda item: (-item.priority_score, item.cell_id)):
        if cell.cell_id not in excluded:
            ranked_by_front[cell.front].append(cell)
    selected: list[MaxResearchCell] = []
    problem_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    cursors: Counter[str] = Counter()
    while len(selected) < budget:
        progress = False
        for front in FRONTS:
            items = ranked_by_front.get(front, [])
            while cursors[front] < len(items):
                candidate = items[cursors[front]]
                cursors[front] += 1
                if problem_counts[candidate.problem_id] >= max_per_problem:
                    continue
                if target_counts[candidate.target_id] >= max_per_target:
                    continue
                selected.append(candidate)
                problem_counts[candidate.problem_id] += 1
                target_counts[candidate.target_id] += 1
                progress = True
                break
            if len(selected) >= budget:
                break
        if not progress:
            break
    return selected


def select_balanced_portfolio(
    cells: Sequence[MaxResearchCell],
    *,
    primary_budget: int = 24,
    secondary_budget: int = 72,
    experiment_budget: int = 256,
) -> dict[str, Any]:
    primary = _balanced_select(cells, primary_budget, max_per_problem=1, max_per_target=1)
    primary_ids = {cell.cell_id for cell in primary}
    secondary = _balanced_select(
        cells,
        secondary_budget,
        excluded_ids=primary_ids,
        max_per_problem=2,
        max_per_target=1,
    )
    excluded = primary_ids | {cell.cell_id for cell in secondary}
    experiments = _balanced_select(
        cells,
        experiment_budget,
        excluded_ids=excluded,
        max_per_problem=8,
        max_per_target=2,
    )
    selected = [*primary, *secondary, *experiments]
    return {
        "schema": "omega-problem-portfolio-max/3",
        "primary_budget": primary_budget,
        "secondary_budget": secondary_budget,
        "experiment_budget": experiment_budget,
        "primary": [asdict(cell) for cell in primary],
        "secondary": [asdict(cell) for cell in secondary],
        "experiments": [asdict(cell) for cell in experiments],
        "coverage": {
            "fronts": len({cell.front for cell in selected}),
            "problems": len({cell.problem_id for cell in selected}),
            "targets": len({cell.target_id for cell in selected}),
            "methods": len({method for cell in selected for method in cell.methods}),
        },
        "scoring_basis": "transparent_profile_v1",
        "finite_budget_is_not_permanent_cap": True,
        "permanent_total_cap": None,
        "solution_claimed": False,
        "proof_claimed": False,
    }


def build_transfer_hyperedges(
    targets: Sequence[ResearchTarget], cells: Sequence[MaxResearchCell]
) -> tuple[dict[str, Any], ...]:
    edges: list[dict[str, Any]] = []
    canonical_by_problem = {
        target.problem_id: target.target_id
        for target in targets
        if target.target_kind == "canonical_statement"
    }
    for target in targets:
        edges.append({
            "edge_id": f"problem-target::{target.target_id}",
            "premises": [target.problem_id],
            "conclusion": target.target_id,
            "semantic": "decomposes_into_target",
            "oak_level": 1,
        })
        canonical = canonical_by_problem[target.problem_id]
        if target.target_id != canonical:
            edges.append({
                "edge_id": f"canonical-dependency::{target.target_id}",
                "premises": [canonical],
                "conclusion": target.target_id,
                "semantic": "requires_statement_alignment",
                "oak_level": 1,
            })
    for cell in cells:
        edges.append({
            "edge_id": f"target-cell::{cell.cell_id}",
            "premises": [cell.target_id, cell.attack_mode, *cell.methods],
            "conclusion": cell.cell_id,
            "semantic": "materializes_evidence_work_cell",
            "oak_level": 1,
        })
    return tuple(sorted(edges, key=lambda edge: edge["edge_id"]))


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def _receipt(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    rows = None
    if path.suffix == ".jsonl":
        rows = sum(1 for line in data.splitlines() if line.strip())
    return {
        "path": path.name,
        "sha256": sha256(data).hexdigest(),
        "bytes": len(data),
        "rows": rows,
    }


def compile_max_atlas(
    output_dir: str | Path,
    *,
    source_registry: str | Path = DEFAULT_SOURCE_REGISTRY,
    import_paths: Iterable[str | Path] = (),
    primary_budget: int = 24,
    secondary_budget: int = 72,
    experiment_budget: int = 256,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    sources = load_source_registry(source_registry)
    seeds = build_seed_records()
    imports = ingest_jsonl(import_paths)
    records = deduplicate_records_max((*seeds, *imports))
    targets = expand_research_targets(records)
    cells = expand_max_cells(records, targets)
    hyperedges = build_transfer_hyperedges(targets, cells)
    portfolio = select_balanced_portfolio(
        cells,
        primary_budget=primary_budget,
        secondary_budget=secondary_budget,
        experiment_budget=experiment_budget,
    )

    rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]] = {
        "sources.jsonl": [asdict(source) for source in sources],
        "problems.jsonl": [asdict(record) for record in records],
        "research_targets.jsonl": [asdict(target) for target in targets],
        "research_cells.jsonl": [asdict(cell) for cell in cells],
        "hyperedges.jsonl": list(hyperedges),
        "methods.jsonl": [{"method_id": method} for method in METHOD_FAMILIES],
    }
    for name, rows in rows_by_file.items():
        _write_jsonl(output / name, rows)
    (output / "portfolio.json").write_text(
        json.dumps(portfolio, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    artifact_names = [*rows_by_file.keys(), "portfolio.json"]
    manifest = {
        "schema": "omega-problem-atlas-manifest-max/3",
        "artifacts": [_receipt(output / name) for name in artifact_names],
        "permanent_total_cap": None,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest_digest = stable_digest(manifest)
    source_ids = {source.source_id for source in sources}
    report = {
        "schema": "omega-problem-atlas-report-max/3",
        "status": "CERTIFIED_SOFTWARE_RESEARCH_FIXTURE_R0_3_MAX",
        "source_count": len(sources),
        "seed_problem_count": len(seeds),
        "imported_problem_count": len(imports),
        "deduplicated_problem_count": len(records),
        "front_count": len({record.front for record in records}),
        "target_kind_count": len(TARGET_KINDS),
        "research_target_count": len(targets),
        "attack_mode_count": len(ATTACK_MODES),
        "research_cell_count": len(cells),
        "method_family_count": len(METHOD_FAMILIES),
        "hyperedge_count": len(hyperedges),
        "unresolved_source_ids": sorted({record.source_id for record in records if record.source_id not in source_ids}),
        "records_requiring_status_refresh": sum(record.source_verified_at is None and record.status != "solved_benchmark" for record in records),
        "records_claiming_current_open_status": sum(record.current_open_status_claimed for record in records),
        "records_claiming_solution": sum(record.solution_claimed for record in records),
        "targets_claiming_proof_or_solution": sum(target.proof_claimed or target.solution_claimed for target in targets),
        "cells_claiming_proof_or_solution": sum(cell.proof_claimed or cell.solution_claimed for cell in cells),
        "portfolio_coverage": portfolio["coverage"],
        "scoring_basis": "transparent_profile_v1",
        "manifest_digest": manifest_digest,
        "logical_frontier_formula": "problems × target_kinds × attack_modes × methods × parameterizations × evidence_states",
        "permanent_total_cap": None,
        "finite_materialization_is_not_proof": True,
        "current_status_certification_claimed": False,
        "solution_claimed": False,
        "formal_proof_claimed": False,
        "scientific_validation_claimed": False,
    }
    report["digest"] = stable_digest(report)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit_max_output(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    errors: list[str] = []
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if stable_digest(manifest) != report.get("manifest_digest"):
        errors.append("manifest digest mismatch")
    for expected in manifest.get("artifacts", []):
        path = output / expected["path"]
        if not path.exists():
            errors.append(f"missing artifact: {expected['path']}")
            continue
        actual = _receipt(path)
        for field in ("sha256", "bytes", "rows"):
            if actual[field] != expected[field]:
                errors.append(f"{expected['path']}: {field} mismatch")

    problems = _read_jsonl(output / "problems.jsonl")
    targets = _read_jsonl(output / "research_targets.jsonl")
    cells = _read_jsonl(output / "research_cells.jsonl")
    edges = _read_jsonl(output / "hyperedges.jsonl")
    methods = _read_jsonl(output / "methods.jsonl")
    portfolio = json.loads((output / "portfolio.json").read_text(encoding="utf-8"))

    def unique(rows: Sequence[Mapping[str, Any]], key: str, label: str) -> set[str]:
        values = [str(row[key]) for row in rows]
        if len(values) != len(set(values)):
            errors.append(f"duplicate {label}")
        return set(values)

    problem_ids = unique(problems, "problem_id", "problem ids")
    target_ids = unique(targets, "target_id", "target ids")
    cell_ids = unique(cells, "cell_id", "cell ids")
    unique(edges, "edge_id", "hyperedge ids")
    method_ids = unique(methods, "method_id", "method ids")

    for target in targets:
        if target["problem_id"] not in problem_ids:
            errors.append(f"target references unknown problem: {target['target_id']}")
        if target.get("proof_claimed") or target.get("solution_claimed"):
            errors.append(f"target makes forbidden claim: {target['target_id']}")
    for cell in cells:
        if cell["problem_id"] not in problem_ids or cell["target_id"] not in target_ids:
            errors.append(f"cell has broken reference: {cell['cell_id']}")
        if set(cell["methods"]) - method_ids:
            errors.append(f"cell references unknown method: {cell['cell_id']}")
        if cell.get("proof_claimed") or cell.get("solution_claimed"):
            errors.append(f"cell makes forbidden claim: {cell['cell_id']}")
        if cell.get("scoring_basis") != "transparent_profile_v1":
            errors.append(f"opaque scoring basis: {cell['cell_id']}")

    count_contract = {
        "deduplicated_problem_count": len(problems),
        "research_target_count": len(targets),
        "research_cell_count": len(cells),
        "hyperedge_count": len(edges),
        "method_family_count": len(methods),
    }
    for field, actual in count_contract.items():
        if report.get(field) != actual:
            errors.append(f"{field}: expected {report.get(field)}, got {actual}")
    for bucket, budget_field in (
        ("primary", "primary_budget"),
        ("secondary", "secondary_budget"),
        ("experiments", "experiment_budget"),
    ):
        if len(portfolio.get(bucket, [])) > portfolio.get(budget_field, -1):
            errors.append(f"{bucket} exceeds budget")
    selected_ids = [item["cell_id"] for bucket in ("primary", "secondary", "experiments") for item in portfolio.get(bucket, [])]
    if len(selected_ids) != len(set(selected_ids)):
        errors.append("portfolio buckets overlap")
    if set(selected_ids) - cell_ids:
        errors.append("portfolio references unknown cells")

    for forbidden in (
        "solution_claimed", "formal_proof_claimed", "scientific_validation_claimed",
        "current_status_certification_claimed",
    ):
        if report.get(forbidden) is not False:
            errors.append(f"{forbidden} must be false")
    if report.get("permanent_total_cap", "missing") is not None:
        errors.append("permanent_total_cap must be null")
    if report.get("records_claiming_solution") != 0:
        errors.append("problem layer contains solution claims")

    return {
        "schema": "omega-problem-atlas-audit-max/3",
        "valid": not errors,
        "errors": errors,
        "counts": count_contract,
        "portfolio_coverage": portfolio.get("coverage", {}),
        "report_digest": report.get("digest"),
        "manifest_digest": report.get("manifest_digest"),
        "solution_claimed": False,
        "proof_claimed": False,
    }
