from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Iterable, Iterator, Mapping, Sequence

from .models import Intent, Requirement, WorkUnit, stable_digest, slugify


OUTPUT_BLUEPRINTS: Mapping[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "theory_documents": ("document", ("source_traceability", "epistemic_status"), ("documents/theory.md",)),
    "mathematical_specifications": ("specification", ("definitions_present", "domains_declared"), ("documents/mathematical_specification.md",)),
    "architecture": ("architecture", ("interfaces_declared", "dependencies_acyclic"), ("documents/architecture.md",)),
    "code": ("implementation", ("imports_successfully", "static_checks"), ("src/{language}/generated_core",)),
    "python_package": ("implementation", ("imports_successfully", "unit_tests"), ("src/python/generated_package",)),
    "rust_package": ("implementation", ("cargo_check", "unit_tests"), ("src/rust/generated_crate",)),
    "cpp_package": ("implementation", ("cmake_configure", "unit_tests"), ("src/cpp/generated_library",)),
    "tests": ("test", ("tests_collected", "negative_fixture_present"), ("tests/generated",)),
    "benchmarks": ("benchmark", ("baseline_present", "metrics_recorded"), ("benchmarks/generated",)),
    "examples": ("example", ("example_runs",), ("examples/generated",)),
    "datasets": ("dataset", ("provenance_present", "license_status_present"), ("data/generated",)),
    "reports": ("report", ("oak_report_present", "residuals_declared"), ("reports/executive.md", "reports/oak.json")),
    "product_analysis": ("product", ("user_problem_defined", "payment_hypothesis_explicit"), ("documents/product_hypotheses.md",)),
    "ip_analysis": ("ip", ("publication_gate_present", "license_gate_present"), ("documents/ip_strategy.md",)),
}


@dataclass(frozen=True)
class LogicalAddress:
    domain: str
    output: str
    language: str
    variant: str
    gate: str
    scale: str

    def to_dict(self) -> dict[str, str]:
        return {
            "domain": self.domain,
            "output": self.output,
            "language": self.language,
            "variant": self.variant,
            "gate": self.gate,
            "scale": self.scale,
        }


class LogicalFrontier:
    """Mixed-radix address space; large logical capacity without materialization."""

    DEFAULT_DIMENSIONS = {
        "domain": tuple(f"domain-{index:04d}" for index in range(1024)),
        "output": tuple(OUTPUT_BLUEPRINTS),
        "language": ("python", "rust", "cpp", "c", "julia", "typescript", "cuda", "wasm"),
        "variant": (
            "reference", "optimized", "streaming", "distributed", "low-memory",
            "high-precision", "gpu", "symbolic", "differentiable", "embedded",
        ),
        "gate": ("syntax", "types", "unit", "integration", "benchmark", "oak", "security", "ip"),
        "scale": tuple(f"scale-{index:03d}" for index in range(128)),
    }

    def __init__(self, dimensions: Mapping[str, Sequence[str]] | None = None) -> None:
        raw = dimensions or self.DEFAULT_DIMENSIONS
        self.names = ("domain", "output", "language", "variant", "gate", "scale")
        self.values = tuple(tuple(raw[name]) for name in self.names)
        if any(not values for values in self.values):
            raise ValueError("frontier dimensions cannot be empty")
        self.radices = tuple(len(values) for values in self.values)
        self.size = prod(self.radices)

    def decode(self, index: int) -> LogicalAddress:
        if index < 0 or index >= self.size:
            raise IndexError(f"frontier index out of range: {index}")
        coordinates: list[int] = []
        remainder = index
        for radix in reversed(self.radices):
            coordinates.append(remainder % radix)
            remainder //= radix
        coordinates.reverse()
        payload = {name: values[position] for name, values, position in zip(self.names, self.values, coordinates)}
        return LogicalAddress(**payload)

    def encode(self, address: LogicalAddress) -> int:
        index = 0
        payload = address.to_dict()
        for name, values, radix in zip(self.names, self.values, self.radices):
            index = index * radix + values.index(payload[name])
        return index

    def iter_range(self, offset: int, count: int) -> Iterator[tuple[int, LogicalAddress]]:
        if offset < 0 or count < 0:
            raise ValueError("offset and count must be non-negative")
        stop = min(self.size, offset + count)
        for index in range(offset, stop):
            yield index, self.decode(index)

    def manifest(self) -> dict[str, object]:
        return {
            "schema": "omega-intent-logical-frontier/v1",
            "dimensions": {name: len(values) for name, values in zip(self.names, self.values)},
            "logical_frontier_size": self.size,
            "permanent_total_cap": None,
            "materialized_items": 0,
            "boundary": "addressable plans are not executed or validated artifacts",
        }


class WorkPlanner:
    def derive_requirements(self, intent: Intent) -> tuple[Requirement, ...]:
        requirements: list[Requirement] = []
        for index, output in enumerate(intent.expected_outputs, start=1):
            blueprint = OUTPUT_BLUEPRINTS.get(output, ("artifact", ("artifact_exists",), (f"generated/{slugify(output)}",)))
            _, checks, _ = blueprint
            rid = f"REQ-{index:05d}-{stable_digest((intent.intent_id, output))[:8].upper()}"
            requirements.append(Requirement(
                requirement_id=rid,
                statement=f"Produce {output} for: {intent.objective}",
                category=output,
                verification_method=";".join(checks),
                acceptance=tuple(checks),
                source_intent_id=intent.intent_id,
                risk="ip_sensitive" if output == "ip_analysis" else "normal",
            ))
        for index, constraint in enumerate(intent.epistemic_constraints, start=len(requirements) + 1):
            rid = f"REQ-{index:05d}-{stable_digest((intent.intent_id, constraint))[:8].upper()}"
            requirements.append(Requirement(
                requirement_id=rid,
                statement=f"Enforce epistemic constraint: {constraint}",
                category="governance",
                verification_method="oak_policy_check",
                acceptance=(constraint,),
                source_intent_id=intent.intent_id,
            ))
        return tuple(requirements)

    def plan(self, intent: Intent, requirements: Sequence[Requirement]) -> tuple[WorkUnit, ...]:
        output_requirements = [r for r in requirements if r.category != "governance"]
        governance = tuple(r.requirement_id for r in requirements if r.category == "governance")
        units: list[WorkUnit] = []
        prior_ids: list[str] = []
        for requirement in output_requirements:
            kind, validations, paths = OUTPUT_BLUEPRINTS.get(
                requirement.category,
                ("artifact", ("artifact_exists",), (f"generated/{slugify(requirement.category)}",)),
            )
            language_variants: Iterable[str | None]
            if kind == "implementation":
                requested = intent.languages
                category_language = requirement.category.removesuffix("_package")
                language_variants = (category_language,) if requirement.category.endswith("_package") else requested
            else:
                language_variants = (None,)
            for language in language_variants:
                output_paths = tuple(path.format(language=language or "neutral") for path in paths)
                identity = (requirement.requirement_id, kind, language, output_paths)
                work_id = f"WU-{stable_digest(identity)[:16].upper()}"
                dependencies: tuple[str, ...] = ()
                if kind in {"test", "benchmark", "example", "report"}:
                    dependencies = tuple(prior_ids)
                units.append(WorkUnit(
                    work_unit_id=work_id,
                    kind=kind,
                    objective=requirement.statement,
                    requirement_ids=(requirement.requirement_id, *governance),
                    dependency_ids=dependencies,
                    outputs=output_paths,
                    validations=tuple(validations),
                    language=language,
                    risk=requirement.risk,
                    generator=f"{kind}_generator",
                ))
                prior_ids.append(work_id)
        return tuple(units)

    @staticmethod
    def topological_batches(work_units: Sequence[WorkUnit]) -> tuple[tuple[str, ...], ...]:
        by_id = {unit.work_unit_id: unit for unit in work_units}
        missing = sorted({dep for unit in work_units for dep in unit.dependency_ids if dep not in by_id})
        if missing:
            raise ValueError(f"missing work-unit dependencies: {missing}")
        remaining = set(by_id)
        completed: set[str] = set()
        batches: list[tuple[str, ...]] = []
        while remaining:
            ready = tuple(sorted(
                work_id for work_id in remaining
                if set(by_id[work_id].dependency_ids).issubset(completed)
            ))
            if not ready:
                raise ValueError(f"work-unit dependency cycle: {sorted(remaining)}")
            batches.append(ready)
            completed.update(ready)
            remaining.difference_update(ready)
        return tuple(batches)
