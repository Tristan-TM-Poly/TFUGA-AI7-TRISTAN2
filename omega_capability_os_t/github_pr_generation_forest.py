from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from math import gcd
from typing import Any, Mapping, Sequence
import argparse
import json

from .github_memory import CapabilityRequest, _stable_digest

GENERATION_SCHEMA_VERSION = "0.1.0"
DEFAULT_SEED_COUNT = 5_000
DEFAULT_MATERIALIZATION_BUDGET = 64

SEED_FAMILIES: tuple[tuple[str, float], ...] = (
    ("reuse", 0.20),
    ("code", 0.16),
    ("test", 0.14),
    ("benchmark", 0.10),
    ("contract", 0.10),
    ("documentation", 0.08),
    ("provenance", 0.08),
    ("oak", 0.06),
    ("simplify", 0.04),
    ("alternative", 0.04),
)

# value, information, reuse, testability, leverage, cost, debt, risk
_FAMILY_PRIORS: Mapping[str, tuple[float, float, float, float, float, float, float, float]] = {
    "reuse": (0.84, 0.62, 0.96, 0.72, 0.86, 0.28, 0.20, 0.20),
    "code": (0.78, 0.58, 0.42, 0.55, 0.88, 0.55, 0.48, 0.38),
    "test": (0.76, 0.88, 0.46, 0.98, 0.72, 0.38, 0.16, 0.14),
    "benchmark": (0.72, 0.94, 0.36, 0.92, 0.70, 0.46, 0.18, 0.16),
    "contract": (0.80, 0.70, 0.82, 0.86, 0.80, 0.34, 0.20, 0.18),
    "documentation": (0.58, 0.54, 0.62, 0.32, 0.52, 0.18, 0.24, 0.10),
    "provenance": (0.66, 0.82, 0.70, 0.78, 0.60, 0.28, 0.12, 0.12),
    "oak": (0.74, 0.92, 0.58, 0.90, 0.64, 0.36, 0.10, 0.08),
    "simplify": (0.82, 0.64, 0.90, 0.68, 0.86, 0.24, 0.08, 0.12),
    "alternative": (0.62, 0.84, 0.34, 0.62, 0.68, 0.44, 0.34, 0.30),
}

_ACTIONS: Mapping[str, tuple[str, str]] = {
    "reuse": (
        "Inspect and compose an existing capability before creating new implementation.",
        "Falsify the proposed reuse by locating incompatibilities, stale assumptions, or missing behavior.",
    ),
    "code": (
        "Generate the smallest residual implementation needed for the target.",
        "Search for a simpler implementation or evidence that no new implementation is needed.",
    ),
    "test": (
        "Add a focused regression/property test that exercises the target behavior.",
        "Construct a counterexample or adversarial test that can break the current hypothesis.",
    ),
    "benchmark": (
        "Measure the candidate against an explicit baseline on a bounded reproducible fixture.",
        "Design a negative-control benchmark able to reveal a false speedup or proxy advantage.",
    ),
    "contract": (
        "Strengthen the typed contract, schema, invariant, or capability boundary.",
        "Attack the contract for ambiguity, incompatibility, or unverifiable obligations.",
    ),
    "documentation": (
        "Document the reusable interface, evidence boundary, and residual work.",
        "Remove or rewrite documentation that overstates implementation, evidence, or authority.",
    ),
    "provenance": (
        "Attach source, lineage, fingerprint, and evidence references to the proposed change.",
        "Find provenance gaps, stale evidence, or unsupported lineage assumptions.",
    ),
    "oak": (
        "Add an OAK gate, falsifier, uncertainty record, or M-minus rule.",
        "Attempt to make the claim fail under a deterministic negative control.",
    ),
    "simplify": (
        "Delete, consolidate, or refactor duplicate structure while preserving tested behavior.",
        "Prove the simplification does not silently remove required capability or evidence.",
    ),
    "alternative": (
        "Compile an independent alternative representation or implementation candidate.",
        "Construct the strongest competing explanation or design and compare it fairly.",
    ),
}


def logical_cardinality(seed_count: int, generation: int) -> int:
    if seed_count <= 0:
        raise ValueError("seed_count must be positive")
    if generation < 0:
        raise ValueError("generation must be >= 0")
    return seed_count * (1 << generation)


def _family_for_seed(seed_id: int, seed_count: int) -> str:
    fraction = (seed_id + 0.5) / seed_count
    cumulative = 0.0
    for family, weight in SEED_FAMILIES:
        cumulative += weight
        if fraction <= cumulative + 1e-12:
            return family
    return SEED_FAMILIES[-1][0]


def _digest_int(*parts: Any) -> int:
    encoded = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return int(sha256(encoded.encode("utf-8")).hexdigest(), 16)


def _bounded_unit(*parts: Any) -> float:
    return (_digest_int(*parts) % 10_000) / 10_000.0


@dataclass(frozen=True)
class VirtualAdditionAddress:
    generation: int
    logical_index: int
    seed_id: int
    family: str
    polarity: str
    route_integer: str
    route_preview: str
    route_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdditionCandidate:
    candidate_id: str
    address: VirtualAdditionAddress
    target: str
    action: str
    pattern_signature: str
    value_proxy: float
    information_proxy: float
    reuse_proxy: float
    testability_proxy: float
    leverage_proxy: float
    cost_proxy: float
    debt_proxy: float
    risk_proxy: float
    go_gradient_proxy: float
    proof_required: bool = True
    materialization_status: str = "SPEC_ONLY"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["address"] = self.address.to_dict()
        return payload


class FractalPRGenerationCompiler:
    """Bounded compiler over the logical 5K*2^n addition space."""

    def __init__(
        self,
        *,
        seed_count: int = DEFAULT_SEED_COUNT,
        materialization_budget: int = DEFAULT_MATERIALIZATION_BUDGET,
        min_go_gradient: float = 1.0,
        sample_multiplier: int = 8,
    ) -> None:
        if seed_count <= 0:
            raise ValueError("seed_count must be positive")
        if materialization_budget <= 0:
            raise ValueError("materialization_budget must be positive")
        if sample_multiplier <= 0:
            raise ValueError("sample_multiplier must be positive")
        self.seed_count = seed_count
        self.materialization_budget = materialization_budget
        self.min_go_gradient = float(min_go_gradient)
        self.sample_multiplier = sample_multiplier

    def address(self, logical_index: int, generation: int) -> VirtualAdditionAddress:
        total = logical_cardinality(self.seed_count, generation)
        if logical_index < 0 or logical_index >= total:
            raise IndexError("logical_index outside virtual population")
        if generation == 0:
            seed_id = logical_index
            route = 0
            polarity = "seed"
            preview = ""
        else:
            route_mask = (1 << generation) - 1
            route = logical_index & route_mask
            seed_id = logical_index >> generation
            polarity = "explorer" if (route & 1) == 0 else "prosecutor"
            if generation <= 32:
                preview = format(route, f"0{generation}b")
            else:
                prefix = route >> (generation - 16)
                suffix = route & 0xFFFF
                preview = f"{prefix:016b}…{suffix:016b}"
        return VirtualAdditionAddress(
            generation=generation,
            logical_index=logical_index,
            seed_id=seed_id,
            family=_family_for_seed(seed_id, self.seed_count),
            polarity=polarity,
            route_integer=str(route),
            route_preview=preview,
            route_digest=sha256(f"{generation}:{route}".encode("utf-8")).hexdigest(),
        )

    def _sample_indices(self, request_id: str, genome_ref: str, generation: int) -> tuple[int, ...]:
        total = logical_cardinality(self.seed_count, generation)
        sample_size = min(total, max(128, self.materialization_budget * self.sample_multiplier))
        if sample_size == total:
            return tuple(range(total))
        offset = _digest_int("offset", request_id, genome_ref, generation) % total
        stride = (_digest_int("stride", request_id, genome_ref, generation) % max(total - 1, 1)) + 1
        if stride % 2 == 0:
            stride += 1
        while gcd(stride, total) != 1:
            stride += 2
            if stride >= total:
                stride = 1
        return tuple((offset + i * stride) % total for i in range(sample_size))

    @staticmethod
    def _genome_dict(genome: Mapping[str, Any] | Any) -> dict[str, Any]:
        if hasattr(genome, "to_dict"):
            payload = dict(genome.to_dict())
        elif isinstance(genome, Mapping):
            payload = dict(genome)
        else:
            raise TypeError("pr_genome must be a mapping or expose to_dict()")
        payload.setdefault("ref", "pr:unknown#0")
        payload.setdefault("changed_files", [])
        payload.setdefault("named_concepts", [])
        return payload

    @staticmethod
    def _targets(request: CapabilityRequest, genome: Mapping[str, Any], residual_outputs: Sequence[str]) -> tuple[str, ...]:
        rows = [
            *map(str, residual_outputs),
            *map(str, genome.get("changed_files", [])),
            *map(str, request.produces),
            *map(str, genome.get("named_concepts", [])),
        ]
        return tuple(dict.fromkeys(row for row in rows if row)) or ("PR-wide residual",)

    def _candidate(
        self,
        request: CapabilityRequest,
        genome: Mapping[str, Any],
        address: VirtualAdditionAddress,
        targets: Sequence[str],
        reuse_coverage_ratio: float,
    ) -> AdditionCandidate:
        family = address.family
        target = targets[_digest_int(address.logical_index, address.route_digest, "target") % len(targets)]
        explorer_text, prosecutor_text = _ACTIONS[family]
        action = explorer_text if address.polarity != "prosecutor" else prosecutor_text
        priors = list(_FAMILY_PRIORS[family])
        reuse_coverage_ratio = min(1.0, max(0.0, float(reuse_coverage_ratio)))
        priors[2] = min(1.0, priors[2] + 0.12 * reuse_coverage_ratio)
        priors[6] = max(0.0, priors[6] - 0.08 * reuse_coverage_ratio)
        jitter = (_bounded_unit(request.request_id, genome["ref"], address.logical_index) - 0.5) * 0.06
        values = [min(1.0, max(0.0, x + jitter)) for x in priors]
        value, information, reuse, testability, leverage, cost, debt, risk = values
        if address.polarity == "prosecutor":
            information = min(1.0, information + 0.06)
            testability = min(1.0, testability + 0.06)
            risk = max(0.0, risk - 0.02)
        go_gradient = value + information + reuse + testability + leverage - cost - debt - risk
        pattern_signature = _stable_digest(
            {"family": family, "polarity": address.polarity, "target": target, "action": action}
        )
        return AdditionCandidate(
            candidate_id=f"addatom:{address.generation}:{address.logical_index}:{pattern_signature[:12]}",
            address=address,
            target=target,
            action=action,
            pattern_signature=pattern_signature,
            value_proxy=round(value, 6),
            information_proxy=round(information, 6),
            reuse_proxy=round(reuse, 6),
            testability_proxy=round(testability, 6),
            leverage_proxy=round(leverage, 6),
            cost_proxy=round(cost, 6),
            debt_proxy=round(debt, 6),
            risk_proxy=round(risk, 6),
            go_gradient_proxy=round(go_gradient, 6),
        )

    def compile(
        self,
        request: CapabilityRequest,
        pr_genome: Mapping[str, Any] | Any,
        *,
        generation: int = 0,
        residual_outputs: Sequence[str] = (),
        reuse_coverage_ratio: float = 0.0,
    ) -> dict[str, Any]:
        genome = self._genome_dict(pr_genome)
        total = logical_cardinality(self.seed_count, generation)
        targets = self._targets(request, genome, residual_outputs)
        sampled = [
            self._candidate(request, genome, self.address(index, generation), targets, reuse_coverage_ratio)
            for index in self._sample_indices(request.request_id, str(genome["ref"]), generation)
        ]
        sampled.sort(key=lambda row: (-row.go_gradient_proxy, row.address.family, row.target, row.candidate_id))

        selected: list[AdditionCandidate] = []
        seen_patterns: set[str] = set()
        for row in sampled:
            if row.go_gradient_proxy < self.min_go_gradient or row.pattern_signature in seen_patterns:
                continue
            seen_patterns.add(row.pattern_signature)
            selected.append(row)
            if len(selected) >= self.materialization_budget:
                break

        support: dict[str, int] = {}
        exemplar: dict[str, AdditionCandidate] = {}
        for row in sampled:
            support[row.pattern_signature] = support.get(row.pattern_signature, 0) + 1
            exemplar[row.pattern_signature] = row
        patterns = [
            {
                "pattern_signature": signature,
                "sample_support_count": count,
                "family": exemplar[signature].address.family,
                "polarity": exemplar[signature].address.polarity,
                "target": exemplar[signature].target,
                "boundary": "support count is within the bounded deterministic sample only",
            }
            for signature, count in sorted(support.items(), key=lambda item: (-item[1], item[0]))
        ]

        best = max((row.go_gradient_proxy for row in sampled), default=float("-inf"))
        keep_going = bool(selected) and best >= self.min_go_gradient
        payload: dict[str, Any] = {
            "schema": f"omega-pr-5k2n-generation/v{GENERATION_SCHEMA_VERSION}",
            "request_id": request.request_id,
            "pr_ref": str(genome["ref"]),
            "generation": generation,
            "law": "C_n = seed_count * 2^n",
            "seed_count": self.seed_count,
            "logical_cardinality_decimal": str(total),
            "logical_population_materialized": False,
            "sampled_candidate_count": len(sampled),
            "compiled_addition_count": len(selected),
            "compiled_additions": [row.to_dict() for row in selected],
            "cvcd_sample_patterns": patterns,
            "cvcd_sample_compression_ratio": round(len(sampled) / max(len(patterns), 1), 6),
            "adaptive_continuation": {
                "architecture_hard_cap": False,
                "current_generation": generation,
                "continue": keep_going,
                "next_generation_candidate": generation + 1 if keep_going else None,
                "best_go_gradient_proxy": best,
                "min_go_gradient_proxy": self.min_go_gradient,
                "rule": (
                    "No fixed architectural N_max. Each finite run stops when bounded evidence/utility "
                    "does not justify another generation or when an external resource/review budget stops it."
                ),
            },
            "physical_patch_compiler": {
                "logical_addition_is_physical_patch": False,
                "compiled_addition_is_code_change": False,
                "write_authority_granted": False,
                "automatic_commit_allowed": False,
                "automatic_merge_allowed": False,
                "human_review_required": True,
                "materialization_budget": self.materialization_budget,
            },
            "oak_boundaries": [
                "5K*2^n logical candidates != 5K*2^n files or lines",
                "generated candidate != useful change",
                "proxy score != measured engineering value",
                "sample pattern support != full-population frequency",
                "reuse similarity != implementation compatibility",
                "compiled addition spec != tested patch",
                "no fixed architectural N_max != infinite physical compute",
                "many additions != progress",
            ],
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload

    def compile_campaign(
        self,
        request: CapabilityRequest,
        pr_genome: Mapping[str, Any] | Any,
        *,
        start_generation: int = 0,
        generation_budget: int = 4,
        residual_outputs: Sequence[str] = (),
        reuse_coverage_ratio: float = 0.0,
    ) -> dict[str, Any]:
        if start_generation < 0:
            raise ValueError("start_generation must be >= 0")
        if generation_budget <= 0:
            raise ValueError("generation_budget must be positive")
        generations: list[dict[str, Any]] = []
        for generation in range(start_generation, start_generation + generation_budget):
            receipt = self.compile(
                request,
                pr_genome,
                generation=generation,
                residual_outputs=residual_outputs,
                reuse_coverage_ratio=reuse_coverage_ratio,
            )
            generations.append(receipt)
            if not receipt["adaptive_continuation"]["continue"]:
                break
        last = generations[-1]
        payload: dict[str, Any] = {
            "schema": f"omega-pr-5k2n-campaign/v{GENERATION_SCHEMA_VERSION}",
            "request_id": request.request_id,
            "pr_ref": last["pr_ref"],
            "law": "C_n = seed_count * 2^n",
            "seed_count": self.seed_count,
            "start_generation": start_generation,
            "generation_budget": generation_budget,
            "generation_budget_is_runtime_budget": True,
            "architecture_hard_cap": False,
            "generation_count": len(generations),
            "last_generation": last["generation"],
            "next_generation_candidate": last["adaptive_continuation"]["next_generation_candidate"],
            "generations": generations,
            "total_compiled_addition_specs": sum(row["compiled_addition_count"] for row in generations),
            "boundary": (
                "The campaign budget is a finite execution/review budget, not a permanent N_max. "
                "A later authorized run may continue from next_generation_candidate."
            ),
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload


def compile_pr_generation_forest(
    request: CapabilityRequest,
    pr_genome: Mapping[str, Any] | Any,
    *,
    generation: int = 0,
    residual_outputs: Sequence[str] = (),
    reuse_coverage_ratio: float = 0.0,
    seed_count: int = DEFAULT_SEED_COUNT,
    materialization_budget: int = DEFAULT_MATERIALIZATION_BUDGET,
    min_go_gradient: float = 1.0,
) -> dict[str, Any]:
    return FractalPRGenerationCompiler(
        seed_count=seed_count,
        materialization_budget=materialization_budget,
        min_go_gradient=min_go_gradient,
    ).compile(
        request,
        pr_genome,
        generation=generation,
        residual_outputs=residual_outputs,
        reuse_coverage_ratio=reuse_coverage_ratio,
    )


def compile_pr_generation_campaign(
    request: CapabilityRequest,
    pr_genome: Mapping[str, Any] | Any,
    *,
    start_generation: int = 0,
    generation_budget: int = 4,
    residual_outputs: Sequence[str] = (),
    reuse_coverage_ratio: float = 0.0,
    seed_count: int = DEFAULT_SEED_COUNT,
    materialization_budget: int = DEFAULT_MATERIALIZATION_BUDGET,
    min_go_gradient: float = 1.0,
) -> dict[str, Any]:
    return FractalPRGenerationCompiler(
        seed_count=seed_count,
        materialization_budget=materialization_budget,
        min_go_gradient=min_go_gradient,
    ).compile_campaign(
        request,
        pr_genome,
        start_generation=start_generation,
        generation_budget=generation_budget,
        residual_outputs=residual_outputs,
        reuse_coverage_ratio=reuse_coverage_ratio,
    )


def _load_payload(path: str) -> Mapping[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("input JSON must be an object")
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile bounded Omega PR 5K2N generation receipts.")
    parser.add_argument("input")
    parser.add_argument("--output", default="-")
    parser.add_argument("--generation", type=int, default=None)
    parser.add_argument("--materialization-budget", type=int, default=None)
    parser.add_argument("--campaign-generations", type=int, default=0)
    args = parser.parse_args(argv)

    payload = _load_payload(args.input)
    request = CapabilityRequest.from_dict(payload.get("request", {}))
    generation = args.generation if args.generation is not None else int(payload.get("generation", 0))
    budget = args.materialization_budget or int(payload.get("materialization_budget", DEFAULT_MATERIALIZATION_BUDGET))
    common = dict(
        residual_outputs=tuple(map(str, payload.get("residual_outputs", []))),
        reuse_coverage_ratio=float(payload.get("reuse_coverage_ratio", 0.0)),
        seed_count=int(payload.get("seed_count", DEFAULT_SEED_COUNT)),
        materialization_budget=budget,
        min_go_gradient=float(payload.get("min_go_gradient", 1.0)),
    )
    if args.campaign_generations:
        result = compile_pr_generation_campaign(
            request,
            payload.get("pr_genome", {}),
            start_generation=generation,
            generation_budget=args.campaign_generations,
            **common,
        )
    else:
        result = compile_pr_generation_forest(
            request,
            payload.get("pr_genome", {}),
            generation=generation,
            **common,
        )
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(encoded, end="")
    else:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
