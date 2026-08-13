"""Ω-REPRESENTATION-NOETHER-COMPILER-T∞ — R0.5.

This module treats a change of representation as an auditable software
morphism.  It measures declared proxy complexity, information retention,
invariant defects, residuals, uncertainty, risk, and reversibility.

"Noether" is used here as an architectural analogy: the compiler searches for
quantities that remain stable across a declared transformation.  Nothing in
this module claims a physical conservation law, historical cognitive law, or
mathematical theorem merely because an invariant audit passes.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Sequence

from sage_tristan.discovery_path_ir import DiscoveryPath, gauss_ceres_reconstruction
from sage_tristan.greatsages import ClaimClass, get_profile
from sage_tristan.greatsages_time_machine import RepresentationMorphism as LegacyRepresentationMorphism


EPS = 1e-12


class MetricKind(str, Enum):
    BENCHMARK_PROXY = "benchmark_proxy"
    EMPIRICAL_MEASUREMENT = "empirical_measurement"
    FORMAL_PROPERTY = "formal_property"


class MorphismStatus(str, Enum):
    ADMISSIBLE_SOFTWARE_MODEL = "admissible_software_model"
    QUARANTINE = "quarantine"


class InvariantStatus(str, Enum):
    CONSERVED_WITHIN_TOLERANCE = "conserved_within_tolerance"
    BROKEN = "broken"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class RepresentationBundle:
    representation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.representation_ids:
            raise ValueError("representation bundle cannot be empty")
        if len(self.representation_ids) != len(set(self.representation_ids)):
            raise ValueError("duplicate representation id")

    @property
    def canonical(self) -> tuple[str, ...]:
        return tuple(sorted(self.representation_ids))

    @property
    def bundle_id(self) -> str:
        raw = json.dumps(self.canonical, separators=(",", ":"))
        return "rep_" + sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class InvariantMeasurement:
    invariant_id: str
    source_value: float
    target_value: float
    scale: float = 1.0
    tolerance: float = 0.05
    weight: float = 1.0
    confidence: float = 1.0
    metric_kind: MetricKind = MetricKind.BENCHMARK_PROXY
    note: str = ""

    def __post_init__(self) -> None:
        if self.scale <= 0:
            raise ValueError("invariant scale must be positive")
        if self.tolerance < 0:
            raise ValueError("invariant tolerance must be non-negative")
        if self.weight < 0:
            raise ValueError("invariant weight must be non-negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("invariant confidence must be in [0, 1]")

    @property
    def defect(self) -> float:
        return round(abs(self.target_value - self.source_value) / self.scale, 6)

    @property
    def status(self) -> InvariantStatus:
        if self.confidence <= 0:
            return InvariantStatus.INDETERMINATE
        if self.defect <= self.tolerance:
            return InvariantStatus.CONSERVED_WITHIN_TOLERANCE
        return InvariantStatus.BROKEN


@dataclass(frozen=True, slots=True)
class RepresentationMorphismR05:
    morphism_id: str
    source: RepresentationBundle
    target: RepresentationBundle
    complexity_before: float
    complexity_after: float
    information_before: float
    information_after: float
    invariants: tuple[InvariantMeasurement, ...] = ()
    residual: float = 0.0
    uncertainty: float = 0.0
    risk: float = 0.0
    reversible: bool = False
    claim_class: ClaimClass = ClaimClass.RECONSTRUCTION
    metric_kind: MetricKind = MetricKind.BENCHMARK_PROXY
    provenance_ids: tuple[str, ...] = ()
    note: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("complexity_before", self.complexity_before),
            ("complexity_after", self.complexity_after),
            ("information_before", self.information_before),
            ("information_after", self.information_after),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        for name, value in (
            ("residual", self.residual),
            ("uncertainty", self.uncertainty),
            ("risk", self.risk),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        ids = [item.invariant_id for item in self.invariants]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate invariant measurement id")

    @property
    def normalized_complexity_gain(self) -> float:
        if self.complexity_before <= EPS:
            return 0.0 if self.complexity_after <= EPS else -1.0
        return round((self.complexity_before - self.complexity_after) / self.complexity_before, 6)

    @property
    def information_loss(self) -> float:
        if self.information_before <= EPS:
            return 0.0
        return round(max(0.0, self.information_before - self.information_after) / self.information_before, 6)

    @property
    def information_inflation(self) -> float:
        if self.information_before <= EPS:
            return 0.0 if self.information_after <= EPS else 1.0
        return round(max(0.0, self.information_after - self.information_before) / self.information_before, 6)

    @property
    def invariant_defect(self) -> float:
        weighted = [
            (item.defect, item.weight * item.confidence)
            for item in self.invariants
            if item.confidence > 0 and item.weight > 0
        ]
        if not weighted:
            return 0.0
        denominator = sum(weight for _, weight in weighted)
        return round(sum(defect * weight for defect, weight in weighted) / denominator, 6)

    @property
    def broken_invariant_ids(self) -> tuple[str, ...]:
        return tuple(sorted(item.invariant_id for item in self.invariants if item.status is InvariantStatus.BROKEN))

    @property
    def conserved_invariant_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                item.invariant_id
                for item in self.invariants
                if item.status is InvariantStatus.CONSERVED_WITHIN_TOLERANCE
            )
        )

    @property
    def penalty(self) -> float:
        # Dimensionless software score. Coefficients are declared policy weights,
        # not learned historical or physical constants.
        value = (
            1.20 * self.information_loss
            + 1.40 * self.invariant_defect
            + 0.90 * self.residual
            + 0.80 * self.uncertainty
            + 0.70 * self.risk
            + (0.15 if self.information_inflation > 0 else 0.0)
        )
        return round(value, 6)

    @property
    def utility(self) -> float:
        return round(self.normalized_complexity_gain - self.penalty, 6)

    @property
    def status(self) -> MorphismStatus:
        if self.broken_invariant_ids:
            return MorphismStatus.QUARANTINE
        if self.information_loss > 0.5 or self.residual > 0.5 or self.uncertainty > 0.75:
            return MorphismStatus.QUARANTINE
        return MorphismStatus.ADMISSIBLE_SOFTWARE_MODEL


@dataclass(frozen=True, slots=True)
class NoetherAuditReceipt:
    morphism_id: str
    conserved_invariant_ids: tuple[str, ...]
    broken_invariant_ids: tuple[str, ...]
    invariant_defect: float
    information_loss: float
    normalized_complexity_gain: float
    residual: float
    uncertainty: float
    utility: float
    status: MorphismStatus
    physical_conservation_law_claimed: bool = False
    mathematical_theorem_claimed: bool = False


@dataclass(frozen=True, slots=True)
class MorphismPath:
    morphism_ids: tuple[str, ...]
    source_bundle_id: str
    target_bundle_id: str
    total_utility: float
    total_information_loss: float
    total_invariant_defect: float
    total_residual: float
    quarantined: bool


@dataclass(frozen=True, slots=True)
class DiscoveryRepresentationAudit:
    path_id: str
    changing_step_ids: tuple[str, ...]
    covered_step_ids: tuple[str, ...]
    uncovered_step_ids: tuple[str, ...]
    quarantined_morphism_ids: tuple[str, ...]
    total_information_loss: float
    total_invariant_defect: float
    all_changes_covered: bool
    promotable: bool
    noether_is_architectural_analogy: bool = True


@dataclass(frozen=True, slots=True)
class RepresentationCompiler:
    morphisms: tuple[RepresentationMorphismR05, ...]

    def __post_init__(self) -> None:
        ids = [item.morphism_id for item in self.morphisms]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate morphism id")

    def morphism(self, morphism_id: str) -> RepresentationMorphismR05:
        for item in self.morphisms:
            if item.morphism_id == morphism_id:
                return item
        raise KeyError(morphism_id)

    def matching(self, source: Sequence[str], target: Sequence[str]) -> tuple[RepresentationMorphismR05, ...]:
        source_key = tuple(sorted(source))
        target_key = tuple(sorted(target))
        return tuple(
            sorted(
                (
                    item
                    for item in self.morphisms
                    if item.source.canonical == source_key and item.target.canonical == target_key
                ),
                key=lambda item: (-item.utility, item.morphism_id),
            )
        )

    def rank_direct(self, source: Sequence[str], target: Sequence[str]) -> tuple[NoetherAuditReceipt, ...]:
        return tuple(noether_audit(item) for item in self.matching(source, target))

    def enumerate_paths(
        self,
        source: Sequence[str],
        target: Sequence[str],
        *,
        max_depth: int = 4,
    ) -> tuple[MorphismPath, ...]:
        if max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        source_bundle = RepresentationBundle(tuple(source))
        target_bundle = RepresentationBundle(tuple(target))
        target_key = target_bundle.canonical
        results: list[MorphismPath] = []

        def visit(
            current: RepresentationBundle,
            path: tuple[RepresentationMorphismR05, ...],
            visited: frozenset[tuple[str, ...]],
        ) -> None:
            if len(path) >= max_depth:
                return
            outgoing = tuple(item for item in self.morphisms if item.source.canonical == current.canonical)
            for edge in outgoing:
                key = edge.target.canonical
                if key in visited:
                    continue
                candidate = path + (edge,)
                if key == target_key:
                    results.append(_summarize_morphism_path(source_bundle, target_bundle, candidate))
                visit(edge.target, candidate, visited | {key})

        if source_bundle.canonical == target_key:
            return (
                MorphismPath((), source_bundle.bundle_id, target_bundle.bundle_id, 0.0, 0.0, 0.0, 0.0, False),
            )
        visit(source_bundle, (), frozenset({source_bundle.canonical}))
        results.sort(key=lambda item: (item.quarantined, -item.total_utility, item.morphism_ids))
        return tuple(results)

    def best_path(self, source: Sequence[str], target: Sequence[str], *, max_depth: int = 4) -> MorphismPath | None:
        candidates = self.enumerate_paths(source, target, max_depth=max_depth)
        return candidates[0] if candidates else None


def noether_audit(morphism: RepresentationMorphismR05) -> NoetherAuditReceipt:
    return NoetherAuditReceipt(
        morphism_id=morphism.morphism_id,
        conserved_invariant_ids=morphism.conserved_invariant_ids,
        broken_invariant_ids=morphism.broken_invariant_ids,
        invariant_defect=morphism.invariant_defect,
        information_loss=morphism.information_loss,
        normalized_complexity_gain=morphism.normalized_complexity_gain,
        residual=morphism.residual,
        uncertainty=morphism.uncertainty,
        utility=morphism.utility,
        status=morphism.status,
    )


def _summarize_morphism_path(
    source: RepresentationBundle,
    target: RepresentationBundle,
    morphisms: Sequence[RepresentationMorphismR05],
) -> MorphismPath:
    return MorphismPath(
        morphism_ids=tuple(item.morphism_id for item in morphisms),
        source_bundle_id=source.bundle_id,
        target_bundle_id=target.bundle_id,
        total_utility=round(sum(item.utility for item in morphisms), 6),
        total_information_loss=round(sum(item.information_loss for item in morphisms), 6),
        total_invariant_defect=round(sum(item.invariant_defect for item in morphisms), 6),
        total_residual=round(sum(item.residual for item in morphisms), 6),
        quarantined=any(item.status is MorphismStatus.QUARANTINE for item in morphisms),
    )


def legacy_morphism_to_r05(
    morphism: LegacyRepresentationMorphism,
    *,
    information_before: float = 1.0,
    information_after: float = 1.0,
) -> RepresentationMorphismR05:
    invariants = tuple(
        InvariantMeasurement(
            invariant_id=item,
            source_value=1.0,
            target_value=1.0,
            scale=1.0,
            tolerance=0.0,
            metric_kind=MetricKind.BENCHMARK_PROXY,
            note="Legacy preserved_invariants declaration migrated as an exact software assertion.",
        )
        for item in morphism.preserved_invariants
    )
    return RepresentationMorphismR05(
        morphism_id=morphism.morphism_id,
        source=RepresentationBundle((morphism.source_representation,)),
        target=RepresentationBundle((morphism.target_representation,)),
        complexity_before=morphism.complexity_before,
        complexity_after=morphism.complexity_after,
        information_before=information_before,
        information_after=information_after,
        invariants=invariants,
        reversible=morphism.reversible,
        claim_class=morphism.claim_class,
        metric_kind=MetricKind.BENCHMARK_PROXY,
        note="Compatibility migration from R0.2 RepresentationMorphism.",
    )


def audit_discovery_path_representations(
    path: DiscoveryPath,
    compiler: RepresentationCompiler,
) -> DiscoveryRepresentationAudit:
    changing = []
    covered = []
    uncovered = []
    used: list[RepresentationMorphismR05] = []
    for step in path.steps:
        before = tuple(sorted(step.representation_before))
        after = tuple(sorted(step.representation_after))
        if before == after:
            continue
        changing.append(step.step_id)
        matches = compiler.matching(before, after)
        if not matches:
            uncovered.append(step.step_id)
            continue
        best = matches[0]
        covered.append(step.step_id)
        used.append(best)
    quarantined = tuple(sorted(item.morphism_id for item in used if item.status is MorphismStatus.QUARANTINE))
    all_covered = not uncovered
    return DiscoveryRepresentationAudit(
        path_id=path.path_id,
        changing_step_ids=tuple(changing),
        covered_step_ids=tuple(covered),
        uncovered_step_ids=tuple(uncovered),
        quarantined_morphism_ids=quarantined,
        total_information_loss=round(sum(item.information_loss for item in used), 6),
        total_invariant_defect=round(sum(item.invariant_defect for item in used), 6),
        all_changes_covered=all_covered,
        promotable=all_covered and not quarantined,
    )


def ceres_representation_compiler() -> RepresentationCompiler:
    """Deterministic R0.5 benchmark fixture for the R0.4 Ceres path.

    Complexity/information values are declared benchmark proxies. They are not
    measurements of Gauss's cognition or universal representation complexity.
    """
    shared_problem = InvariantMeasurement(
        "target_problem_identity",
        1.0,
        1.0,
        tolerance=0.0,
        note="The encoded target problem remains the same across the software morphism.",
    )
    evidence_scope = InvariantMeasurement(
        "evidence_scope",
        1.0,
        0.99,
        tolerance=0.02,
        note="Proxy for preserving the admissible evidence scope.",
    )
    model_identity = InvariantMeasurement(
        "latent_model_identity",
        1.0,
        0.98,
        tolerance=0.03,
        note="Proxy continuity of the latent-model object across residualization.",
    )
    residual_target = InvariantMeasurement(
        "target_problem_identity",
        1.0,
        1.0,
        tolerance=0.0,
    )
    return RepresentationCompiler(
        (
            RepresentationMorphismR05(
                "ceres_rep_switch_r05",
                RepresentationBundle(("historical_problem_statement",)),
                RepresentationBundle(("latent_model", "inverse_problem")),
                complexity_before=1.0,
                complexity_after=0.72,
                information_before=1.0,
                information_after=0.96,
                invariants=(shared_problem, evidence_scope),
                residual=0.12,
                uncertainty=0.20,
                risk=0.08,
                claim_class=ClaimClass.RECONSTRUCTION,
                note="Benchmark proxy for R0.4 representation_switch step.",
            ),
            RepresentationMorphismR05(
                "ceres_residualize_r05",
                RepresentationBundle(("latent_model", "inverse_problem")),
                RepresentationBundle(("latent_model", "residual_space")),
                complexity_before=0.72,
                complexity_after=0.58,
                information_before=0.96,
                information_after=0.94,
                invariants=(shared_problem, model_identity),
                residual=0.10,
                uncertainty=0.16,
                risk=0.05,
                claim_class=ClaimClass.RECONSTRUCTION,
                note="Benchmark proxy for residual-space reformulation.",
            ),
            RepresentationMorphismR05(
                "ceres_orbit_reconstruction_r05",
                RepresentationBundle(("latent_model", "residual_space")),
                RepresentationBundle(("orbit_reconstruction", "residual_space")),
                complexity_before=0.58,
                complexity_after=0.50,
                information_before=0.94,
                information_after=0.93,
                invariants=(residual_target, model_identity),
                residual=0.08,
                uncertainty=0.12,
                risk=0.05,
                claim_class=ClaimClass.RECONSTRUCTION,
                note="Benchmark proxy for terminal orbit-reconstruction representation.",
            ),
            # Deliberately bad direct alternative used by OAKBench ranking/quarantine tests.
            RepresentationMorphismR05(
                "ceres_lossy_shortcut_r05",
                RepresentationBundle(("historical_problem_statement",)),
                RepresentationBundle(("orbit_reconstruction", "residual_space")),
                complexity_before=1.0,
                complexity_after=0.30,
                information_before=1.0,
                information_after=0.35,
                invariants=(
                    InvariantMeasurement(
                        "target_problem_identity",
                        1.0,
                        0.50,
                        tolerance=0.05,
                        note="Synthetic broken-invariant control.",
                    ),
                ),
                residual=0.65,
                uncertainty=0.80,
                risk=0.45,
                claim_class=ClaimClass.RECONSTRUCTION,
                note="Negative control: attractive compression but destructive loss/residuals.",
            ),
        )
    )


def compile_report() -> dict[str, object]:
    path = gauss_ceres_reconstruction(get_profile("gauss"))
    compiler = ceres_representation_compiler()
    audit = audit_discovery_path_representations(path, compiler)
    best = compiler.best_path(path.initial_state.representation_ids, path.terminal_state.representation_ids, max_depth=4)
    direct_bad = noether_audit(compiler.morphism("ceres_lossy_shortcut_r05"))
    return {
        "engine": "Ω-REPRESENTATION-NOETHER-COMPILER-T∞",
        "release": "R0.5",
        "discovery_path_id": path.path_id,
        "representation_audit": asdict(audit),
        "best_morphism_path": asdict(best) if best else None,
        "negative_control": asdict(direct_bad),
        "morphisms": [asdict(item) for item in compiler.morphisms],
        "noether_is_architectural_analogy": True,
        "physical_conservation_law_claimed": False,
        "historical_cognitive_metric_claimed": False,
        "proxy_metrics_are_universal": False,
        "scientific_superiority_certified": False,
        "oak_note": (
            "Utility compares declared proxy metrics under this fixture only. "
            "Transfer gain, causal effectiveness and scientific value require external benchmarks."
        ),
    }


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Representation / Noether compiler R0.5")
    parser.add_argument("--report", action="store_true", help="Emit the deterministic R0.5 benchmark report")
    parser.parse_args(argv)
    print(json.dumps(_jsonable(compile_report()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
