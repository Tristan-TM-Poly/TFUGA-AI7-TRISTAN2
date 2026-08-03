"""Repository scanner that compiles artifacts into CreationDNA records."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from .models import Capability, CreationDNA, EvidenceRecord, Need, SynergyStage, stable_id
from .ontology import (
    evidence_strength,
    extract_system_ids,
    extract_transformations,
    infer_domains,
    infer_needs,
    infer_risks,
    tokenize,
)

DEFAULT_SUFFIXES = {".md", ".py", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".txt", ".csv"}
DEFAULT_IGNORE = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}


@dataclass(slots=True)
class ScannerPolicy:
    suffixes: set[str] = field(default_factory=lambda: set(DEFAULT_SUFFIXES))
    ignore: set[str] = field(default_factory=lambda: set(DEFAULT_IGNORE))
    max_file_bytes: int = 1_000_000
    max_text_chars: int = 60_000
    max_nodes: int = 800


@dataclass(slots=True)
class ScanResult:
    creations: list[CreationDNA]
    file_systems: dict[str, list[str]]
    diagnostics: list[str]


def iter_files(root: Path, policy: ScannerPolicy) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in policy.suffixes:
            continue
        relative = path.relative_to(root)
        if any(part in policy.ignore for part in relative.parts):
            continue
        try:
            if path.stat().st_size <= policy.max_file_bytes:
                yield path
        except OSError:
            continue


def _repository_name(root: Path) -> str:
    return root.resolve().name


def scan_repositories(roots: Iterable[Path], policy: ScannerPolicy | None = None) -> ScanResult:
    policy = policy or ScannerPolicy()
    aggregate: dict[str, dict] = {}
    file_systems: dict[str, list[str]] = {}
    diagnostics: list[str] = []

    for unresolved_root in roots:
        root = unresolved_root.resolve()
        if not root.exists():
            diagnostics.append(f"missing_root:{root}")
            continue
        repo = _repository_name(root)
        for path in iter_files(root, policy):
            relative = path.relative_to(root)
            key = f"{repo}/{relative.as_posix()}"
            try:
                text = path.read_text(encoding="utf-8", errors="replace")[: policy.max_text_chars]
            except OSError as exc:
                diagnostics.append(f"read_error:{key}:{exc.__class__.__name__}")
                continue
            systems = sorted(extract_system_ids(text))
            if not systems:
                continue
            file_systems[key] = systems
            domains = infer_domains(f"{key}\n{text}")
            tokens = tokenize(f"{key}\n{text}")
            transformations = extract_transformations(text)
            inferred_needs = infer_needs(text)
            risks = infer_risks(text)

            for system in systems:
                record = aggregate.setdefault(
                    system,
                    {
                        "repository": repo,
                        "paths": set(),
                        "mentions": 0,
                        "domains": Counter(),
                        "tokens": Counter(),
                        "capabilities": {},
                        "needs": {},
                        "evidence": [],
                        "risks": defaultdict(float),
                    },
                )
                mentions = text.lower().count(system.lower()) or 1
                record["paths"].add(key)
                record["mentions"] += mentions
                record["domains"].update(domains)
                record["tokens"].update(tokens)
                for category, value in risks.items():
                    record["risks"][category] = max(record["risks"][category], value)

                strength = evidence_strength(relative.as_posix(), mentions, text)
                kind = "test" if "test" in relative.as_posix().lower() else "artifact"
                if "schema" in relative.as_posix().lower():
                    kind = "schema"
                elif "report" in relative.as_posix().lower() or "oak" in relative.as_posix().lower():
                    kind = "audit"
                record["evidence"].append(
                    EvidenceRecord(kind=kind, source=key, strength=strength, claim=f"{system} is present in {key}")
                )

                for transformation in transformations:
                    if transformation.need:
                        need_id = stable_id("NED", system, key, transformation.raw)
                        record["needs"][need_id] = Need(
                            id=need_id,
                            name=transformation.raw,
                            input_types=[transformation.source],
                            desired_output_types=[transformation.target],
                            domains=sorted(domains),
                            priority=0.65,
                            provenance=[f"{key}:{transformation.line_number}"],
                            acceptance_criteria=["interface_contract", "baseline", "provenance_preserved"],
                        )
                    else:
                        capability_id = stable_id("CAP", system, key, transformation.raw)
                        record["capabilities"][capability_id] = Capability(
                            id=capability_id,
                            name=transformation.raw,
                            input_types=[transformation.source],
                            output_types=[transformation.target],
                            domains=sorted(domains),
                            confidence=strength,
                            provenance=[f"{key}:{transformation.line_number}"],
                            invariants=["provenance_preservation"],
                        )

                for input_type, output_type, line_number in inferred_needs:
                    need_id = stable_id("NED", system, key, line_number, output_type)
                    record["needs"].setdefault(
                        need_id,
                        Need(
                            id=need_id,
                            name=f"Resolve documented need for {output_type}",
                            input_types=[input_type],
                            desired_output_types=[output_type],
                            domains=sorted(domains),
                            priority=0.5,
                            provenance=[f"{key}:{line_number}"],
                            acceptance_criteria=["testable_resolution"],
                        ),
                    )

    creations: list[CreationDNA] = []
    for system, record in aggregate.items():
        evidence_records = sorted(record["evidence"], key=lambda item: (-item.strength, item.source))[:40]
        capabilities = sorted(record["capabilities"].values(), key=lambda item: item.id)
        needs = sorted(record["needs"].values(), key=lambda item: (-item.priority, item.id))
        maturity = SynergyStage.S2_COMPLEMENTARITY if capabilities or needs else SynergyStage.S1_RESONANCE
        creations.append(
            CreationDNA(
                id=stable_id("CRN", system, record["repository"]),
                name=system,
                repository=record["repository"],
                paths=sorted(record["paths"]),
                mentions=record["mentions"],
                domains=[name for name, _ in record["domains"].most_common(8)],
                tokens=[name for name, _ in record["tokens"].most_common(80)],
                capabilities=capabilities,
                needs=needs,
                evidence=evidence_records,
                risks=dict(record["risks"]),
                permissions={"remote_mutation": "human_approval_required"},
                maturity=maturity,
                expansion_options=["adapter", "benchmark", "experiment", "product_hypothesis"],
                uncertainty={"extraction": 0.35 if capabilities or needs else 0.55, "causal": 1.0},
            )
        )

    creations.sort(key=lambda item: (-item.evidence_score, -item.mentions, item.name))
    return ScanResult(creations=creations[: policy.max_nodes], file_systems=file_systems, diagnostics=diagnostics)
