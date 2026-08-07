"""Ω-PROBLEM-ATLAS-T∞ R0.3 core.

This module materializes a finite, reviewable research atlas from a source
registry and a deterministic seed constellation.  It deliberately separates:

- a problem title from a verified current open status;
- a numerical experiment from a proof;
- a formal skeleton from a kernel-checked theorem;
- a finite campaign budget from a permanent system ceiling.

No function in this module claims to solve or certify an open problem.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_REGISTRY = PACKAGE_ROOT / "data" / "omega_problem_atlas_r03" / "sources.json"


FRONTS: tuple[str, ...] = (
    "analytic_number_theory",
    "algebraic_diophantine_geometry",
    "additive_combinatorics",
    "graphs_hypergraphs",
    "discrete_geometry",
    "algebraic_geometry",
    "topology_differential_geometry",
    "harmonic_analysis",
    "partial_differential_equations",
    "dynamical_systems",
    "probability_random_structures",
    "optimization_operations_research",
    "algebra_representation_theory",
    "logic_foundations",
    "computational_complexity",
    "quantum_computation",
    "quantum_information",
    "mathematical_physics",
    "information_coding",
    "numerical_mathematics",
    "computational_geometry",
    "mathematical_biology",
    "mathematics_of_ai",
    "tristan_generated_mathematics",
)


ATTACK_MODES: tuple[str, ...] = (
    "statement_and_provenance_audit",
    "toy_model",
    "finite_or_low_dimensional_case",
    "weakened_or_restricted_form",
    "conditional_implication",
    "counterexample_search",
    "formalization_skeleton",
    "numerical_or_symbolic_benchmark",
)


# Three anchors per front: 24 × 3 = 72 problem families.  The status strings
# are intentionally conservative.  Most entries require a fresh primary-source
# check before the repository may assert that they are currently open.
_SEED_ROWS: tuple[tuple[str, str, str, str, str], ...] = (
    ("riemann_hypothesis", "Riemann hypothesis", FRONTS[0], "clay_open_requires_refresh", "clay"),
    ("lindelof_hypothesis", "Lindelöf hypothesis", FRONTS[0], "open_status_requires_refresh", "requires_source_resolution"),
    ("twin_prime_conjecture", "Twin prime conjecture", FRONTS[0], "open_status_requires_refresh", "requires_source_resolution"),

    ("birch_swinnerton_dyer", "Birch and Swinnerton-Dyer conjecture", FRONTS[1], "clay_open_requires_refresh", "clay"),
    ("abc_conjecture", "abc conjecture and verification frontier", FRONTS[1], "status_or_acceptance_requires_refresh", "requires_source_resolution"),
    ("hilbert_tenth_over_q", "Hilbert's tenth problem over the rationals", FRONTS[1], "open_status_requires_refresh", "requires_source_resolution"),

    ("polynomial_freiman_riesz", "Polynomial Freiman-Ruzsa frontier", FRONTS[2], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("chowla_conjecture", "Chowla conjecture variants", FRONTS[2], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("sunflower_conjecture", "Sunflower conjecture quantitative frontier", FRONTS[2], "statement_variant_requires_refresh", "requires_source_resolution"),

    ("hadwiger_conjecture", "Hadwiger conjecture", FRONTS[3], "open_status_requires_refresh", "requires_source_resolution"),
    ("reconstruction_conjecture", "Graph reconstruction conjecture", FRONTS[3], "open_status_requires_refresh", "requires_source_resolution"),
    ("erdos_hajnal_conjecture", "Erdős-Hajnal conjecture", FRONTS[3], "open_status_requires_refresh", "requires_source_resolution"),

    ("hadwiger_nelson", "Hadwiger-Nelson chromatic number problem", FRONTS[4], "bounds_require_refresh", "requires_source_resolution"),
    ("illumination_conjecture", "Illumination conjecture", FRONTS[4], "open_status_requires_refresh", "requires_source_resolution"),
    ("erdos_unit_distance", "Erdős unit distance problem", FRONTS[4], "bounds_require_refresh", "requires_source_resolution"),

    ("hodge_conjecture", "Hodge conjecture", FRONTS[5], "clay_open_requires_refresh", "clay"),
    ("tate_conjecture", "Tate conjecture", FRONTS[5], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("bombieri_lang", "Bombieri-Lang conjecture", FRONTS[5], "statement_variant_requires_refresh", "requires_source_resolution"),

    ("poincare_benchmark", "Poincaré conjecture accepted-proof reconstruction benchmark", FRONTS[6], "solved_benchmark", "clay"),
    ("smooth_4d_poincare", "Smooth four-dimensional Poincaré conjecture", FRONTS[6], "open_status_requires_refresh", "requires_source_resolution"),
    ("slice_ribbon", "Slice-ribbon conjecture", FRONTS[6], "open_status_requires_refresh", "requires_source_resolution"),

    ("restriction_conjecture", "Fourier restriction conjecture", FRONTS[7], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("bochner_riesz", "Bochner-Riesz conjecture", FRONTS[7], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("kakeya_maximal", "Kakeya maximal function conjecture", FRONTS[7], "statement_variant_requires_refresh", "requires_source_resolution"),

    ("navier_stokes", "Navier-Stokes existence and smoothness", FRONTS[8], "clay_open_requires_refresh", "clay"),
    ("euler_3d_blowup", "Three-dimensional Euler singularity problem", FRONTS[8], "open_status_requires_refresh", "requires_source_resolution"),
    ("critical_sqg_regular", "Critical surface quasi-geostrophic regularity frontier", FRONTS[8], "statement_variant_requires_refresh", "requires_source_resolution"),

    ("birkhoff_billiards", "Birkhoff conjecture for convex billiards", FRONTS[9], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("zimmer_frontier", "Zimmer program unresolved cases", FRONTS[9], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("palis_global_dynamics", "Palis global dynamics conjectural frontier", FRONTS[9], "statement_variant_requires_refresh", "requires_source_resolution"),

    ("self_avoiding_walk", "Self-avoiding walk critical exponent frontier", FRONTS[10], "dimension_and_model_require_refresh", "requires_source_resolution"),
    ("kpz_universality", "KPZ universality mathematical frontier", FRONTS[10], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("percolation_critical", "Percolation critical behavior unresolved cases", FRONTS[10], "dimension_and_model_require_refresh", "requires_source_resolution"),

    ("unique_games", "Unique Games Conjecture", FRONTS[11], "open_status_requires_refresh", "requires_source_resolution"),
    ("simplex_pivot_rule", "Strongly polynomial simplex pivot rule problem", FRONTS[11], "open_status_requires_refresh", "requires_source_resolution"),
    ("nonconvex_landscapes", "Global guarantees for structured nonconvex landscapes", FRONTS[11], "research_frontier_requires_statement", "requires_source_resolution"),

    ("jacobian_conjecture", "Jacobian conjecture", FRONTS[12], "open_status_requires_refresh", "requires_source_resolution"),
    ("inverse_galois", "Inverse Galois problem over the rationals", FRONTS[12], "open_status_requires_refresh", "requires_source_resolution"),
    ("kaplansky_zero_divisor", "Kaplansky zero-divisor conjecture", FRONTS[12], "statement_variant_requires_refresh", "requires_source_resolution"),

    ("vaught_conjecture", "Vaught conjecture", FRONTS[13], "open_status_requires_refresh", "requires_source_resolution"),
    ("borel_determinacy_strength", "Exact proof-theoretic strength frontiers for determinacy", FRONTS[13], "research_frontier_requires_statement", "requires_source_resolution"),
    ("automated_theorem_limits", "Limits of automated theorem discovery under formal verification", FRONTS[13], "research_frontier_requires_statement", "requires_source_resolution"),

    ("p_vs_np", "P versus NP", FRONTS[14], "clay_open_requires_refresh", "clay"),
    ("vp_vs_vnp", "VP versus VNP", FRONTS[14], "open_status_requires_refresh", "requires_source_resolution"),
    ("bpp_vs_p", "BPP versus P", FRONTS[14], "open_status_requires_refresh", "requires_source_resolution"),

    ("quantum_pcp", "Quantum PCP conjecture", FRONTS[15], "statement_variant_requires_refresh", "open_quantum_problems"),
    ("qma_vs_qcma", "QMA versus QCMA", FRONTS[15], "open_status_requires_refresh", "open_quantum_problems"),
    ("bqp_vs_ph", "BQP versus the polynomial hierarchy", FRONTS[15], "statement_variant_requires_refresh", "open_quantum_problems"),

    ("sic_povm", "Existence of SIC-POVMs in all finite dimensions", FRONTS[16], "open_status_requires_refresh", "open_quantum_problems"),
    ("mub_dimension_6", "Complete mutually unbiased bases in dimension six", FRONTS[16], "open_status_requires_refresh", "open_quantum_problems"),
    ("npt_bound_entanglement", "NPT bound entanglement problem", FRONTS[16], "open_status_requires_refresh", "open_quantum_problems"),

    ("yang_mills_mass_gap", "Yang-Mills existence and mass gap", FRONTS[17], "clay_open_requires_refresh", "clay"),
    ("constructive_qft_4d", "Constructive interacting quantum field theory in four dimensions", FRONTS[17], "research_frontier_requires_statement", "requires_source_resolution"),
    ("turbulence_intermit", "Turbulence intermittency exponent frontier", FRONTS[17], "research_frontier_requires_statement", "requires_source_resolution"),

    ("quantum_ldpc_bounds", "Quantum LDPC optimal tradeoff frontier", FRONTS[18], "bounds_require_refresh", "requires_source_resolution"),
    ("locally_correctable_codes", "Locally correctable code lower-bound frontier", FRONTS[18], "bounds_require_refresh", "requires_source_resolution"),
    ("network_coding_capacity", "Network coding capacity and insufficiency frontiers", FRONTS[18], "statement_variant_requires_refresh", "requires_source_resolution"),

    ("matrix_multiplication_omega", "Matrix multiplication exponent frontier", FRONTS[19], "best_bound_requires_refresh", "requires_source_resolution"),
    ("certified_pde_continuation", "Certified continuation for nonlinear PDE singularity exclusion", FRONTS[19], "research_frontier_requires_statement", "requires_source_resolution"),
    ("high_dimensional_quadrature", "Deterministic high-dimensional quadrature complexity frontier", FRONTS[19], "research_frontier_requires_statement", "requires_source_resolution"),

    ("minimum_weight_triangulation", "Minimum-weight triangulation complexity", FRONTS[20], "open_status_requires_refresh", "requires_source_resolution"),
    ("art_gallery_variants", "Art gallery problem unresolved variants", FRONTS[20], "statement_variant_requires_refresh", "requires_source_resolution"),
    ("unit_disk_recognition", "Unit disk graph recognition complexity frontier", FRONTS[20], "status_requires_refresh", "requires_source_resolution"),

    ("protein_folding_math", "Mathematical identifiability of protein folding landscapes", FRONTS[21], "research_frontier_requires_statement", "requires_source_resolution"),
    ("morphogenesis_inverse", "Inverse problems for morphogenetic pattern formation", FRONTS[21], "research_frontier_requires_statement", "requires_source_resolution"),
    ("phylogenetic_network_id", "Identifiability of phylogenetic networks", FRONTS[21], "statement_variant_requires_refresh", "requires_source_resolution"),

    ("neural_generalization", "Mechanistic theory of neural-network generalization", FRONTS[22], "research_frontier_requires_statement", "requires_source_resolution"),
    ("representation_identifiability", "Identifiability of learned representations", FRONTS[22], "research_frontier_requires_statement", "requires_source_resolution"),
    ("continual_learning", "Stability-plasticity limits in continual learning", FRONTS[22], "research_frontier_requires_statement", "requires_source_resolution"),

    ("ffwt_stability", "FFWT stability and reconstruction theorem program", FRONTS[23], "tristan_hypothesis_unvalidated", "tristan_internal"),
    ("hgfm_identifiability", "HGFM identifiability and equivalence theorem program", FRONTS[23], "tristan_hypothesis_unvalidated", "tristan_internal"),
    ("cvcd_error_bounds", "CVCD compression-decompression error-bound theorem program", FRONTS[23], "tristan_hypothesis_unvalidated", "tristan_internal"),
)


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    name: str
    kind: str
    primary_url: str
    trust_tier: str
    refresh_policy: str
    ingestion_mode: str
    status_policy: str
    license_note: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.source_id.strip():
            errors.append("blank source_id")
        if not self.name.strip():
            errors.append("blank source name")
        if not self.primary_url.startswith("https://"):
            errors.append("primary_url must be https")
        if self.trust_tier not in {"primary", "curated", "community", "competition"}:
            errors.append("unknown trust_tier")
        if "refresh" not in self.status_policy.lower() and "verify" not in self.status_policy.lower():
            errors.append("status_policy must require refresh or verification")
        return tuple(errors)


@dataclass(frozen=True)
class ProblemRecord:
    problem_id: str
    title: str
    canonical_key: str
    front: str
    status: str
    source_id: str
    source_locator: str | None
    source_verified_at: str | None
    statement: str | None
    provenance_digest: str
    solution_claimed: bool = False
    current_open_status_claimed: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.problem_id or not self.title or not self.canonical_key:
            errors.append("blank identity field")
        if self.front not in FRONTS:
            errors.append("unknown front")
        if self.solution_claimed:
            errors.append("solution claims are forbidden in the atlas seed layer")
        if self.current_open_status_claimed and not self.source_verified_at:
            errors.append("open status claimed without source_verified_at")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_\-]*", self.problem_id):
            errors.append("problem_id is not slug-safe")
        return tuple(errors)


@dataclass(frozen=True)
class ResearchCell:
    cell_id: str
    problem_id: str
    front: str
    attack_mode: str
    scope: str
    fertility: float
    transferability: float
    testability: float
    formalizability: float
    uncertainty: float
    false_progress_risk: float
    priority_score: float
    status: str = "candidate"
    proof_claimed: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.attack_mode not in ATTACK_MODES:
            errors.append("unknown attack mode")
        if self.front not in FRONTS:
            errors.append("unknown front")
        for name in (
            "fertility",
            "transferability",
            "testability",
            "formalizability",
            "uncertainty",
            "false_progress_risk",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                errors.append(f"{name} outside [0,1]")
        if self.proof_claimed:
            errors.append("research cells cannot claim proof")
        return tuple(errors)


def canonicalize_title(title: str) -> str:
    normalized = title.casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _stable_fraction(key: str, salt: str) -> float:
    raw = sha256(f"{salt}:{key}".encode("utf-8")).digest()[:8]
    return int.from_bytes(raw, "big") / float((1 << 64) - 1)


def load_source_registry(path: str | Path = DEFAULT_SOURCE_REGISTRY) -> tuple[SourceSpec, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != "omega-problem-source-registry/3":
        raise ValueError("unsupported source registry schema")
    sources = tuple(SourceSpec(**item) for item in payload["sources"])
    errors = [f"{source.source_id}: {error}" for source in sources for error in source.validate()]
    ids = [source.source_id for source in sources]
    if len(ids) != len(set(ids)):
        errors.append("duplicate source ids")
    if errors:
        raise ValueError("; ".join(errors))
    return tuple(sorted(sources, key=lambda source: source.source_id))


def build_seed_records() -> tuple[ProblemRecord, ...]:
    records: list[ProblemRecord] = []
    for problem_id, title, front, status, source_id in _SEED_ROWS:
        base = {
            "problem_id": problem_id,
            "title": title,
            "front": front,
            "status": status,
            "source_id": source_id,
        }
        record = ProblemRecord(
            problem_id=problem_id,
            title=title,
            canonical_key=canonicalize_title(title),
            front=front,
            status=status,
            source_id=source_id,
            source_locator=None,
            source_verified_at=None,
            statement=None,
            provenance_digest=stable_digest(base),
            solution_claimed=False,
            current_open_status_claimed=False,
        )
        if record.validate():
            raise ValueError(f"invalid seed {problem_id}: {record.validate()}")
        records.append(record)
    if len(records) != 72:
        raise AssertionError(f"expected 72 seeds, found {len(records)}")
    if len({record.front for record in records}) != len(FRONTS):
        raise AssertionError("every front must be represented")
    return tuple(records)


def _record_from_mapping(item: Mapping[str, Any], source_path: str) -> ProblemRecord:
    title = str(item["title"]).strip()
    problem_id = str(item.get("problem_id") or canonicalize_title(title).replace(" ", "_"))
    front = str(item["front"])
    status = str(item.get("status", "status_requires_refresh"))
    source_id = str(item.get("source_id", "external_import"))
    source_locator = item.get("source_locator")
    source_verified_at = item.get("source_verified_at")
    statement = item.get("statement")
    open_claim = bool(item.get("current_open_status_claimed", False))
    source_payload = {
        "source_path": source_path,
        "item": dict(item),
    }
    record = ProblemRecord(
        problem_id=problem_id,
        title=title,
        canonical_key=canonicalize_title(title),
        front=front,
        status=status,
        source_id=source_id,
        source_locator=str(source_locator) if source_locator is not None else None,
        source_verified_at=str(source_verified_at) if source_verified_at is not None else None,
        statement=str(statement) if statement is not None else None,
        provenance_digest=stable_digest(source_payload),
        solution_claimed=bool(item.get("solution_claimed", False)),
        current_open_status_claimed=open_claim,
    )
    errors = record.validate()
    if errors:
        raise ValueError(f"invalid imported record {problem_id}: {errors}")
    return record


def ingest_jsonl(paths: Iterable[str | Path]) -> tuple[ProblemRecord, ...]:
    records: list[ProblemRecord] = []
    for path_like in paths:
        path = Path(path_like)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            try:
                records.append(_record_from_mapping(item, f"{path}:{line_number}"))
            except Exception as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return tuple(records)


def deduplicate_records(records: Iterable[ProblemRecord]) -> tuple[ProblemRecord, ...]:
    selected: dict[str, ProblemRecord] = {}
    for record in records:
        current = selected.get(record.canonical_key)
        if current is None:
            selected[record.canonical_key] = record
            continue
        current_rank = (
            bool(current.source_verified_at),
            current.source_id not in {"requires_source_resolution", "external_import"},
            bool(current.statement),
            current.problem_id,
        )
        candidate_rank = (
            bool(record.source_verified_at),
            record.source_id not in {"requires_source_resolution", "external_import"},
            bool(record.statement),
            record.problem_id,
        )
        if candidate_rank > current_rank:
            selected[record.canonical_key] = record
    return tuple(sorted(selected.values(), key=lambda item: (item.front, item.problem_id)))


def expand_research_cells(records: Sequence[ProblemRecord]) -> tuple[ResearchCell, ...]:
    cells: list[ResearchCell] = []
    for record in records:
        for mode in ATTACK_MODES:
            key = f"{record.problem_id}:{mode}"
            fertility = round(0.45 + 0.5 * _stable_fraction(key, "fertility"), 6)
            transferability = round(0.35 + 0.6 * _stable_fraction(key, "transfer"), 6)
            testability = round(0.25 + 0.7 * _stable_fraction(key, "test"), 6)
            formalizability = round(0.25 + 0.7 * _stable_fraction(key, "formal"), 6)
            uncertainty = round(0.35 + 0.6 * _stable_fraction(key, "uncertainty"), 6)
            false_progress_risk = round(0.25 + 0.7 * _stable_fraction(key, "risk"), 6)
            numerator = fertility * transferability * testability * formalizability
            denominator = (0.2 + uncertainty) * (0.2 + false_progress_risk)
            priority = round(numerator / denominator, 9)
            cell = ResearchCell(
                cell_id=f"{record.problem_id}::{mode}",
                problem_id=record.problem_id,
                front=record.front,
                attack_mode=mode,
                scope=f"{record.title} — {mode.replace('_', ' ')}",
                fertility=fertility,
                transferability=transferability,
                testability=testability,
                formalizability=formalizability,
                uncertainty=uncertainty,
                false_progress_risk=false_progress_risk,
                priority_score=priority,
            )
            errors = cell.validate()
            if errors:
                raise ValueError(f"invalid research cell {cell.cell_id}: {errors}")
            cells.append(cell)
    return tuple(sorted(cells, key=lambda cell: cell.cell_id))


def select_portfolio(
    cells: Sequence[ResearchCell],
    *,
    primary_budget: int = 6,
    secondary_budget: int = 24,
    experiment_budget: int = 64,
) -> dict[str, Any]:
    for name, value in (
        ("primary_budget", primary_budget),
        ("secondary_budget", secondary_budget),
        ("experiment_budget", experiment_budget),
    ):
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    ranked = sorted(cells, key=lambda cell: (-cell.priority_score, cell.cell_id))
    by_problem: dict[str, ResearchCell] = {}
    for cell in ranked:
        by_problem.setdefault(cell.problem_id, cell)
    problem_rank = list(by_problem.values())
    primary = problem_rank[:primary_budget]
    secondary = problem_rank[primary_budget : primary_budget + secondary_budget]
    experiments = ranked[:experiment_budget]
    return {
        "schema": "omega-problem-portfolio/3",
        "primary_budget": primary_budget,
        "secondary_budget": secondary_budget,
        "experiment_budget": experiment_budget,
        "primary": [asdict(cell) for cell in primary],
        "secondary": [asdict(cell) for cell in secondary],
        "experiments": [asdict(cell) for cell in experiments],
        "finite_budget_is_not_permanent_cap": True,
        "permanent_total_cap": None,
        "solution_claimed": False,
        "proof_claimed": False,
    }


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def compile_atlas(
    output_dir: str | Path,
    *,
    source_registry: str | Path = DEFAULT_SOURCE_REGISTRY,
    import_paths: Iterable[str | Path] = (),
    primary_budget: int = 6,
    secondary_budget: int = 24,
    experiment_budget: int = 64,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    sources = load_source_registry(source_registry)
    seeds = build_seed_records()
    imports = ingest_jsonl(import_paths)
    records = deduplicate_records((*seeds, *imports))
    cells = expand_research_cells(records)
    portfolio = select_portfolio(
        cells,
        primary_budget=primary_budget,
        secondary_budget=secondary_budget,
        experiment_budget=experiment_budget,
    )

    source_ids = {source.source_id for source in sources}
    unresolved_sources = sorted(
        {
            record.source_id
            for record in records
            if record.source_id not in source_ids
        }
    )
    hyperedges = [
        {
            "edge_id": f"edge::{cell.cell_id}",
            "premises": [cell.problem_id, cell.attack_mode],
            "conclusion": cell.cell_id,
            "semantic": "materializes_research_cell",
            "oak_level": 1,
        }
        for cell in cells
    ]

    source_rows = [asdict(source) for source in sources]
    problem_rows = [asdict(record) for record in records]
    cell_rows = [asdict(cell) for cell in cells]

    _write_jsonl(output / "sources.jsonl", source_rows)
    _write_jsonl(output / "problems.jsonl", problem_rows)
    _write_jsonl(output / "research_cells.jsonl", cell_rows)
    _write_jsonl(output / "hyperedges.jsonl", hyperedges)
    (output / "portfolio.json").write_text(
        json.dumps(portfolio, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    digest_payload = {
        "sources": source_rows,
        "problems": problem_rows,
        "research_cells": cell_rows,
        "hyperedges": hyperedges,
        "portfolio": portfolio,
    }
    report = {
        "schema": "omega-problem-atlas-report/3",
        "status": "CERTIFIED_SOFTWARE_RESEARCH_FIXTURE_R0_3",
        "source_count": len(sources),
        "seed_problem_count": len(seeds),
        "imported_problem_count": len(imports),
        "deduplicated_problem_count": len(records),
        "front_count": len({record.front for record in records}),
        "attack_mode_count": len(ATTACK_MODES),
        "materialized_research_cell_count": len(cells),
        "materialized_hyperedge_count": len(hyperedges),
        "expected_seed_research_cells": len(seeds) * len(ATTACK_MODES),
        "unresolved_source_ids": unresolved_sources,
        "records_requiring_status_refresh": sum(
            record.source_verified_at is None and record.status != "solved_benchmark"
            for record in records
        ),
        "records_claiming_current_open_status": sum(
            record.current_open_status_claimed for record in records
        ),
        "records_claiming_solution": sum(record.solution_claimed for record in records),
        "research_cells_claiming_proof": sum(cell.proof_claimed for cell in cells),
        "logical_frontier_formula": (
            "problems × attack_modes × parameterizations × methods × evidence_states"
        ),
        "permanent_total_cap": None,
        "finite_materialization_is_not_proof": True,
        "current_status_certification_claimed": False,
        "solution_claimed": False,
        "formal_proof_claimed": False,
        "scientific_validation_claimed": False,
        "digest": stable_digest(digest_payload),
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def audit_output(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))

    def count_lines(name: str) -> int:
        return sum(1 for line in (output / name).read_text(encoding="utf-8").splitlines() if line.strip())

    actual = {
        "sources": count_lines("sources.jsonl"),
        "problems": count_lines("problems.jsonl"),
        "research_cells": count_lines("research_cells.jsonl"),
        "hyperedges": count_lines("hyperedges.jsonl"),
    }
    errors: list[str] = []
    expected = {
        "sources": report["source_count"],
        "problems": report["deduplicated_problem_count"],
        "research_cells": report["materialized_research_cell_count"],
        "hyperedges": report["materialized_hyperedge_count"],
    }
    for name, value in expected.items():
        if actual[name] != value:
            errors.append(f"{name}: expected {value}, got {actual[name]}")
    for forbidden in (
        "solution_claimed",
        "formal_proof_claimed",
        "scientific_validation_claimed",
        "current_status_certification_claimed",
    ):
        if report.get(forbidden) is not False:
            errors.append(f"{forbidden} must be false")
    if report.get("permanent_total_cap", "missing") is not None:
        errors.append("permanent_total_cap must be null")
    if report.get("records_claiming_solution") != 0:
        errors.append("seed/import layer contains solution claims")
    if report.get("research_cells_claiming_proof") != 0:
        errors.append("research cell layer contains proof claims")

    return {
        "schema": "omega-problem-atlas-audit/3",
        "valid": not errors,
        "errors": errors,
        "actual_counts": actual,
        "expected_counts": expected,
        "report_digest": report["digest"],
        "solution_claimed": False,
        "proof_claimed": False,
    }
