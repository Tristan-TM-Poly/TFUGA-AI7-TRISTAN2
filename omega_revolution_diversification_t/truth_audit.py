"""Structured repository truth audit.

The audit compares declared documentation claims against a normalized snapshot
of code symbols, tests, benchmarks and version metadata.  Findings are review
candidates; they are not proof of developer intent or legal wrongdoing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import math
import re
from typing import Any, Iterable, Mapping, Sequence

from .models import stable_id


class FindingSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKING = "BLOCKING"


@dataclass(frozen=True)
class DocumentationClaim:
    text: str
    claim_type: str
    subject: str
    expected_value: str | float | None = None
    source_path: str = "README.md"
    line: int | None = None
    claim_id: str = ""

    def __post_init__(self) -> None:
        if not self.claim_id:
            object.__setattr__(
                self,
                "claim_id",
                stable_id(
                    "repo-claim",
                    {
                        "text": self.text,
                        "claim_type": self.claim_type,
                        "subject": self.subject,
                        "source_path": self.source_path,
                        "line": self.line,
                    },
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BenchmarkObservation:
    subject: str
    input_size: float
    elapsed_seconds: float
    memory_bytes: int = 0
    repetitions: int = 1

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.input_size <= 0 or not math.isfinite(self.input_size):
            errors.append("benchmark input_size must be finite and positive")
        if self.elapsed_seconds <= 0 or not math.isfinite(self.elapsed_seconds):
            errors.append("benchmark elapsed_seconds must be finite and positive")
        if self.memory_bytes < 0:
            errors.append("benchmark memory_bytes must be non-negative")
        if self.repetitions < 1:
            errors.append("benchmark repetitions must be at least one")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepositorySnapshot:
    repository: str
    version: str
    documented_version: str
    public_symbols: set[str]
    tested_symbols: set[str]
    deprecated_symbols: set[str] = field(default_factory=set)
    documentation_claims: list[DocumentationClaim] = field(default_factory=list)
    benchmarks: list[BenchmarkObservation] = field(default_factory=list)
    dependency_versions: dict[str, str] = field(default_factory=dict)
    documented_dependency_versions: dict[str, str] = field(default_factory=dict)
    source_paths: set[str] = field(default_factory=set)
    documentation_paths: set[str] = field(default_factory=set)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.repository.strip():
            errors.append("repository name is required")
        if not self.version.strip():
            errors.append("repository version is required")
        for benchmark in self.benchmarks:
            errors.extend(benchmark.validate())
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "version": self.version,
            "documented_version": self.documented_version,
            "public_symbols": sorted(self.public_symbols),
            "tested_symbols": sorted(self.tested_symbols),
            "deprecated_symbols": sorted(self.deprecated_symbols),
            "documentation_claims": [claim.to_dict() for claim in self.documentation_claims],
            "benchmarks": [benchmark.to_dict() for benchmark in self.benchmarks],
            "dependency_versions": dict(sorted(self.dependency_versions.items())),
            "documented_dependency_versions": dict(
                sorted(self.documented_dependency_versions.items())
            ),
            "source_paths": sorted(self.source_paths),
            "documentation_paths": sorted(self.documentation_paths),
        }


@dataclass(frozen=True)
class AuditFinding:
    code: str
    severity: FindingSeverity
    title: str
    detail: str
    subject: str
    evidence: tuple[str, ...]
    suggested_test: str
    finding_id: str = ""

    def __post_init__(self) -> None:
        if not self.finding_id:
            object.__setattr__(
                self,
                "finding_id",
                stable_id(
                    "truth-audit-finding",
                    {
                        "code": self.code,
                        "subject": self.subject,
                        "detail": self.detail,
                    },
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass(frozen=True)
class TruthAuditReport:
    repository: str
    finding_count: int
    findings: tuple[AuditFinding, ...]
    tested_symbol_coverage: float
    documentation_symbol_precision: float
    blocking: bool
    boundary: str = (
        "Findings are structured divergence candidates. They require review of "
        "source context and do not establish intent, fraud, or legal liability."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "finding_count": self.finding_count,
            "findings": [finding.to_dict() for finding in self.findings],
            "tested_symbol_coverage": self.tested_symbol_coverage,
            "documentation_symbol_precision": self.documentation_symbol_precision,
            "blocking": self.blocking,
            "boundary": self.boundary,
        }


_COMPLEXITY_PATTERNS: tuple[tuple[re.Pattern[str], float], ...] = (
    (re.compile(r"\bo\s*\(\s*1\s*\)", re.I), 0.0),
    (re.compile(r"\bo\s*\(\s*log\s*n\s*\)", re.I), 0.25),
    (re.compile(r"\bo\s*\(\s*n\s*\)", re.I), 1.0),
    (re.compile(r"\bo\s*\(\s*n\s*log\s*n\s*\)", re.I), 1.25),
    (re.compile(r"\bo\s*\(\s*n\s*\^\s*2\s*\)", re.I), 2.0),
    (re.compile(r"\bo\s*\(\s*n²\s*\)", re.I), 2.0),
    (re.compile(r"\bo\s*\(\s*n\s*\^\s*3\s*\)", re.I), 3.0),
)


def estimate_empirical_exponent(observations: Sequence[BenchmarkObservation]) -> float | None:
    points = sorted((b.input_size, b.elapsed_seconds) for b in observations)
    if len(points) < 2:
        return None
    xs = [math.log(size) for size, _ in points]
    ys = [math.log(elapsed) for _, elapsed in points]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator <= 1e-15:
        return None
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator


def expected_complexity_exponent(text: str) -> float | None:
    normalized = text.replace(" ", "")
    for pattern, exponent in _COMPLEXITY_PATTERNS:
        if pattern.search(normalized):
            return exponent
    return None


def _finding(
    code: str,
    severity: FindingSeverity,
    title: str,
    detail: str,
    subject: str,
    evidence: Iterable[str],
    suggested_test: str,
) -> AuditFinding:
    return AuditFinding(
        code=code,
        severity=severity,
        title=title,
        detail=detail,
        subject=subject,
        evidence=tuple(evidence),
        suggested_test=suggested_test,
    )


def audit_repository(snapshot: RepositorySnapshot) -> TruthAuditReport:
    errors = snapshot.validate()
    if errors:
        raise ValueError("; ".join(errors))
    findings: list[AuditFinding] = []

    if snapshot.version != snapshot.documented_version:
        findings.append(
            _finding(
                "VERSION_DIVERGENCE",
                FindingSeverity.HIGH,
                "Documented version differs from code version",
                f"code={snapshot.version}, docs={snapshot.documented_version}",
                snapshot.repository,
                ("package metadata", "documentation metadata"),
                "Generate documentation from the same version source used by packaging.",
            )
        )

    missing_tests = sorted(snapshot.public_symbols - snapshot.tested_symbols)
    for symbol in missing_tests:
        severity = (
            FindingSeverity.HIGH
            if symbol not in snapshot.deprecated_symbols
            else FindingSeverity.LOW
        )
        findings.append(
            _finding(
                "PUBLIC_SYMBOL_WITHOUT_TEST",
                severity,
                "Public symbol lacks direct test coverage",
                f"{symbol} is public but absent from the normalized tested-symbol set.",
                symbol,
                ("public API inventory", "test symbol inventory"),
                f"Add a positive and negative behavioral test for {symbol}.",
            )
        )

    benchmark_map: dict[str, list[BenchmarkObservation]] = {}
    for benchmark in snapshot.benchmarks:
        benchmark_map.setdefault(benchmark.subject, []).append(benchmark)

    documented_subjects: set[str] = set()
    for claim in snapshot.documentation_claims:
        documented_subjects.add(claim.subject)
        if claim.claim_type == "symbol_exists":
            if claim.subject not in snapshot.public_symbols:
                findings.append(
                    _finding(
                        "DOCUMENTED_SYMBOL_MISSING",
                        FindingSeverity.BLOCKING,
                        "Documentation names a missing public symbol",
                        claim.text,
                        claim.subject,
                        (claim.source_path,),
                        "Resolve whether the symbol was renamed, removed, or never implemented.",
                    )
                )
            elif claim.subject in snapshot.deprecated_symbols:
                findings.append(
                    _finding(
                        "DOCUMENTED_SYMBOL_DEPRECATED",
                        FindingSeverity.MEDIUM,
                        "Documentation promotes a deprecated symbol",
                        claim.text,
                        claim.subject,
                        (claim.source_path,),
                        "Replace the example with the supported API and add migration notes.",
                    )
                )
        elif claim.claim_type == "tested":
            if claim.subject not in snapshot.tested_symbols:
                findings.append(
                    _finding(
                        "DOCUMENTED_TEST_CLAIM_UNSUPPORTED",
                        FindingSeverity.HIGH,
                        "Documentation claims testing not visible in snapshot",
                        claim.text,
                        claim.subject,
                        (claim.source_path,),
                        "Link the exact test or weaken the documentation claim.",
                    )
                )
        elif claim.claim_type == "complexity":
            expected = (
                float(claim.expected_value)
                if isinstance(claim.expected_value, (int, float))
                else expected_complexity_exponent(claim.text)
            )
            observed = estimate_empirical_exponent(benchmark_map.get(claim.subject, []))
            if expected is None:
                findings.append(
                    _finding(
                        "COMPLEXITY_CLAIM_UNPARSED",
                        FindingSeverity.INFO,
                        "Complexity claim could not be normalized",
                        claim.text,
                        claim.subject,
                        (claim.source_path,),
                        "Store the expected exponent explicitly in the claim record.",
                    )
                )
            elif observed is None:
                findings.append(
                    _finding(
                        "COMPLEXITY_CLAIM_UNBENCHMARKED",
                        FindingSeverity.MEDIUM,
                        "Complexity claim lacks sufficient benchmark points",
                        f"expected exponent≈{expected}",
                        claim.subject,
                        (claim.source_path,),
                        "Benchmark at three or more geometrically increasing input sizes.",
                    )
                )
            elif observed - expected > 0.55:
                findings.append(
                    _finding(
                        "COMPLEXITY_DIVERGENCE",
                        FindingSeverity.HIGH,
                        "Empirical scaling is materially worse than documented",
                        f"expected exponent≈{expected:.3f}, observed≈{observed:.3f}",
                        claim.subject,
                        (claim.source_path, "benchmark observations"),
                        "Repeat benchmarks with controlled environment and profile nested work.",
                    )
                )
        elif claim.claim_type == "path_exists":
            if claim.subject not in snapshot.source_paths:
                findings.append(
                    _finding(
                        "DOCUMENTED_PATH_MISSING",
                        FindingSeverity.HIGH,
                        "Documentation references a missing repository path",
                        claim.text,
                        claim.subject,
                        (claim.source_path,),
                        "Correct the path or restore the referenced artifact.",
                    )
                )

    undocumented_public = sorted(snapshot.public_symbols - documented_subjects)
    for symbol in undocumented_public:
        findings.append(
            _finding(
                "PUBLIC_SYMBOL_UNDOCUMENTED",
                FindingSeverity.LOW,
                "Public symbol lacks a normalized documentation claim",
                f"{symbol} is public but has no structured documentation claim.",
                symbol,
                ("public API inventory",),
                "Add a minimal contract, example, failure mode and status.",
            )
        )

    dependency_names = set(snapshot.dependency_versions) | set(
        snapshot.documented_dependency_versions
    )
    for dependency in sorted(dependency_names):
        actual = snapshot.dependency_versions.get(dependency)
        documented = snapshot.documented_dependency_versions.get(dependency)
        if actual != documented:
            findings.append(
                _finding(
                    "DEPENDENCY_VERSION_DIVERGENCE",
                    FindingSeverity.MEDIUM,
                    "Documented dependency version differs from implementation",
                    f"{dependency}: actual={actual!r}, documented={documented!r}",
                    dependency,
                    ("dependency manifest", "documentation"),
                    "Generate dependency documentation from a locked manifest.",
                )
            )

    findings.sort(
        key=lambda finding: (
            -list(FindingSeverity).index(finding.severity),
            finding.code,
            finding.subject,
        )
    )
    tested_coverage = len(snapshot.public_symbols & snapshot.tested_symbols) / max(
        len(snapshot.public_symbols), 1
    )
    valid_doc_symbols = sum(
        claim.claim_type != "symbol_exists" or claim.subject in snapshot.public_symbols
        for claim in snapshot.documentation_claims
    )
    doc_precision = valid_doc_symbols / max(len(snapshot.documentation_claims), 1)
    blocking = any(
        finding.severity in {FindingSeverity.BLOCKING, FindingSeverity.HIGH}
        for finding in findings
    )
    return TruthAuditReport(
        repository=snapshot.repository,
        finding_count=len(findings),
        findings=tuple(findings),
        tested_symbol_coverage=tested_coverage,
        documentation_symbol_precision=doc_precision,
        blocking=blocking,
    )


def canonical_truth_audit_fixture() -> RepositorySnapshot:
    return RepositorySnapshot(
        repository="example/research-tool",
        version="0.4.0",
        documented_version="0.3.0",
        public_symbols={"compile_cell", "audit_repo", "legacy_scan", "fast_transform"},
        tested_symbols={"compile_cell", "fast_transform"},
        deprecated_symbols={"legacy_scan"},
        documentation_claims=[
            DocumentationClaim(
                text="Use compile_cell to compile an auditable cell.",
                claim_type="symbol_exists",
                subject="compile_cell",
            ),
            DocumentationClaim(
                text="Use missing_api for autonomous publication.",
                claim_type="symbol_exists",
                subject="missing_api",
            ),
            DocumentationClaim(
                text="audit_repo is fully tested.",
                claim_type="tested",
                subject="audit_repo",
            ),
            DocumentationClaim(
                text="fast_transform runs in O(n log n).",
                claim_type="complexity",
                subject="fast_transform",
                expected_value=1.25,
            ),
            DocumentationClaim(
                text="Load examples/deleted_demo.py.",
                claim_type="path_exists",
                subject="examples/deleted_demo.py",
            ),
        ],
        benchmarks=[
            BenchmarkObservation("fast_transform", 100.0, 0.01),
            BenchmarkObservation("fast_transform", 200.0, 0.04),
            BenchmarkObservation("fast_transform", 400.0, 0.16),
            BenchmarkObservation("fast_transform", 800.0, 0.64),
        ],
        dependency_versions={"jsonschema": "4.26", "numpy": "2.3"},
        documented_dependency_versions={"jsonschema": "4.20", "numpy": "2.3"},
        source_paths={"examples/current_demo.py", "src/core.py"},
        documentation_paths={"README.md"},
    )
