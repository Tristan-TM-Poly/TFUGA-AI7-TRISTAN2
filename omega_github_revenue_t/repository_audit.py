from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .authorization import AuditAuthorization, Operation, require_local_repository_match
from .privacy import PrivacyFinding, scan_text, summarize_findings
from .transparency import digest_payload


_TEXT_SUFFIXES = {
    ".py", ".md", ".rst", ".txt", ".json", ".jsonl", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".sh", ".ps1", ".js", ".ts", ".tsx",
    ".jsx", ".java", ".c", ".h", ".cpp", ".hpp", ".rs", ".go", ".rb",
    ".php", ".swift", ".kt", ".sql", ".graphql", ".html", ".css",
}
_CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".h", ".cpp",
    ".hpp", ".rs", ".go", ".rb", ".php", ".swift", ".kt", ".sh", ".ps1",
}
_SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__"}
_LICENSE_NAMES = {"license", "license.md", "license.txt", "copying", "copying.md"}
_DOC_NAMES = {"readme.md", "readme.rst", "contributing.md", "code_of_conduct.md", "security.md"}


@dataclass(frozen=True)
class AuditPolicy:
    max_text_file_bytes: int = 2_000_000
    include_hidden: bool = False
    scan_secret_patterns: bool = True
    hash_files: bool = True
    excluded_directories: tuple[str, ...] = tuple(sorted(_SKIP_DIRS))

    def validate(self) -> None:
        if self.max_text_file_bytes <= 0:
            raise ValueError("max_text_file_bytes must be positive")


@dataclass(frozen=True)
class AuditFinding:
    finding_id: str
    category: str
    severity: str
    message: str
    path: str | None = None
    evidence: tuple[str, ...] = ()
    recommendation: str = ""


@dataclass(frozen=True)
class RepositoryAuditReport:
    repository_id: str
    authorization_id: str
    files_seen: int
    bytes_seen: int
    text_files_scanned: int
    lines_seen: int
    code_files: int
    test_files: int
    workflow_files: int
    documentation_files: int
    has_license: bool
    has_funding: bool
    findings: tuple[AuditFinding, ...]
    privacy_summary: dict[str, int]
    quality_score: float
    report_hash: str
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            **{key: value for key, value in asdict(self).items() if key != "findings"},
            "findings": [asdict(item) for item in self.findings],
        }


def _iter_files(root: Path, policy: AuditPolicy) -> Iterable[Path]:
    excluded = set(policy.excluded_directories)
    for current, directories, filenames in os.walk(root):
        directories[:] = sorted(
            item for item in directories
            if item not in excluded and (policy.include_hidden or not item.startswith(".") or item == ".github")
        )
        for filename in sorted(filenames):
            if not policy.include_hidden and filename.startswith(".") and filename != ".gitignore":
                continue
            path = Path(current) / filename
            if path.is_symlink() or not path.is_file():
                continue
            yield path


def _finding(
    category: str,
    severity: str,
    message: str,
    *,
    path: str | None = None,
    evidence: tuple[str, ...] = (),
    recommendation: str = "",
) -> AuditFinding:
    body = {"category": category, "severity": severity, "message": message, "path": path}
    return AuditFinding(
        finding_id=f"OAK-{digest_payload(body)[:12]}",
        category=category,
        severity=severity,
        message=message,
        path=path,
        evidence=evidence,
        recommendation=recommendation,
    )


def _quality_score(
    *,
    has_readme: bool,
    has_license: bool,
    has_tests: bool,
    has_workflows: bool,
    has_security: bool,
    privacy_critical: int,
    large_unscanned: int,
) -> float:
    positive = (
        0.24 * float(has_readme)
        + 0.18 * float(has_license)
        + 0.24 * float(has_tests)
        + 0.16 * float(has_workflows)
        + 0.18 * float(has_security)
    )
    penalty = min(0.65, privacy_critical * 0.20 + large_unscanned * 0.01)
    return round(max(0.0, min(1.0, positive * (1.0 - penalty))), 6)


def audit_repository(
    root: str | Path,
    authorization: AuditAuthorization,
    *,
    policy: AuditPolicy | None = None,
) -> RepositoryAuditReport:
    policy = policy or AuditPolicy()
    policy.validate()
    authorization.require(
        Operation.READ_METADATA,
        Operation.READ_TEXT,
        Operation.COUNT_LINES,
        Operation.GENERATE_REPORT,
    )
    repository = require_local_repository_match(root, authorization)

    files_seen = bytes_seen = text_files_scanned = lines_seen = 0
    code_files = test_files = workflow_files = documentation_files = 0
    names: set[str] = set()
    privacy_findings: list[PrivacyFinding] = []
    findings: list[AuditFinding] = []
    large_unscanned = 0

    for path in _iter_files(repository, policy):
        relative = path.relative_to(repository).as_posix()
        name = path.name.lower()
        names.add(name)
        size = path.stat().st_size
        files_seen += 1
        bytes_seen += size
        suffix = path.suffix.lower()
        if suffix in _CODE_SUFFIXES:
            code_files += 1
        if "test" in name or any(part in {"test", "tests"} for part in path.parts):
            test_files += 1
        if relative.startswith(".github/workflows/") and suffix in {".yml", ".yaml"}:
            workflow_files += 1
        if name in _DOC_NAMES or relative.startswith("docs/"):
            documentation_files += 1
        if suffix not in _TEXT_SUFFIXES and name not in {"dockerfile", "makefile"}:
            continue
        if size > policy.max_text_file_bytes:
            large_unscanned += 1
            findings.append(
                _finding(
                    "large_text_file",
                    "review",
                    "Text file exceeded the per-file scan budget.",
                    path=relative,
                    evidence=(f"size={size}",),
                    recommendation=(
                        "Review or split the file; increase the explicit run budget only when justified."
                    ),
                )
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(
                _finding(
                    "encoding",
                    "info",
                    "File could not be decoded as UTF-8.",
                    path=relative,
                    recommendation="Declare or normalize text encoding if the file is intended for tooling.",
                )
            )
            continue
        text_files_scanned += 1
        lines_seen += text.count("\n") + bool(text)
        if policy.scan_secret_patterns:
            privacy_findings.extend(scan_text(text, path=relative))

    has_license = bool(names & _LICENSE_NAMES)
    has_readme = "readme.md" in names or "readme.rst" in names
    has_security = "security.md" in names
    has_funding = (repository / ".github" / "FUNDING.yml").is_file()

    if not has_readme:
        findings.append(
            _finding(
                "documentation",
                "high",
                "No top-level README was detected.",
                recommendation="Add a bounded quick start, scope, evidence, and limitations.",
            )
        )
    if not has_license:
        findings.append(
            _finding(
                "licensing",
                "high",
                "No recognizable license file was detected.",
                recommendation=(
                    "Choose a license only after confirming IP ownership and disclosure intent."
                ),
            )
        )
    if test_files == 0:
        findings.append(
            _finding(
                "testing",
                "high",
                "No test files were detected.",
                recommendation="Add reproducible tests for the highest-value claims.",
            )
        )
    if workflow_files == 0:
        findings.append(
            _finding(
                "ci",
                "medium",
                "No GitHub Actions workflow was detected.",
                recommendation="Add minimal exact-head validation for supported runtimes.",
            )
        )
    if not has_security:
        findings.append(
            _finding(
                "security",
                "medium",
                "No SECURITY.md was detected.",
                recommendation="Document private vulnerability reporting and supported versions.",
            )
        )
    critical_privacy = sum(item.severity == "critical" for item in privacy_findings)
    if critical_privacy:
        findings.append(
            _finding(
                "privacy",
                "critical",
                "Secret-like values were detected; values are not included in this report.",
                evidence=(f"critical_fingerprints={critical_privacy}",),
                recommendation=(
                    "Revoke exposed credentials, purge history when required, and use repository secrets."
                ),
            )
        )

    findings.sort(key=lambda item: (item.severity, item.category, item.path or "", item.finding_id))
    score = _quality_score(
        has_readme=has_readme,
        has_license=has_license,
        has_tests=test_files > 0,
        has_workflows=workflow_files > 0,
        has_security=has_security,
        privacy_critical=critical_privacy,
        large_unscanned=large_unscanned,
    )
    body = {
        "repository_id": authorization.repository_id,
        "authorization_id": authorization.authorization_id,
        "metrics": {
            "files_seen": files_seen,
            "bytes_seen": bytes_seen,
            "text_files_scanned": text_files_scanned,
            "lines_seen": lines_seen,
            "code_files": code_files,
            "test_files": test_files,
            "workflow_files": workflow_files,
            "documentation_files": documentation_files,
            "has_license": has_license,
            "has_funding": has_funding,
        },
        "findings": [asdict(item) for item in findings],
        "privacy_summary": summarize_findings(privacy_findings),
        "quality_score": score,
    }
    return RepositoryAuditReport(
        repository_id=authorization.repository_id,
        authorization_id=authorization.authorization_id,
        files_seen=files_seen,
        bytes_seen=bytes_seen,
        text_files_scanned=text_files_scanned,
        lines_seen=lines_seen,
        code_files=code_files,
        test_files=test_files,
        workflow_files=workflow_files,
        documentation_files=documentation_files,
        has_license=has_license,
        has_funding=has_funding,
        findings=tuple(findings),
        privacy_summary=summarize_findings(privacy_findings),
        quality_score=score,
        report_hash=digest_payload(body),
        limitations=(
            "static text and metadata audit only",
            "no inaccessible systems, network calls, dependency execution, or security certification",
            "pattern findings may contain false positives and require human review",
            "quality_score is a routing heuristic, not a truth or business-value probability",
        ),
    )


def render_markdown(report: RepositoryAuditReport) -> str:
    lines = [
        "# OAKGate Repository Audit",
        "",
        f"- Repository: `{report.repository_id}`",
        f"- Authorization: `{report.authorization_id}`",
        f"- Report hash: `{report.report_hash}`",
        f"- Quality routing score: `{report.quality_score:.3f}`",
        "",
        "## Metrics",
        "",
        f"- Files seen: {report.files_seen}",
        f"- Bytes seen: {report.bytes_seen}",
        f"- Text files scanned: {report.text_files_scanned}",
        f"- Lines seen: {report.lines_seen}",
        f"- Code files: {report.code_files}",
        f"- Test files: {report.test_files}",
        f"- Workflow files: {report.workflow_files}",
        f"- Documentation files: {report.documentation_files}",
        f"- License detected: {report.has_license}",
        f"- Funding configuration detected: {report.has_funding}",
        "",
        "## Findings",
        "",
    ]
    if not report.findings:
        lines.append("No rule-based finding was emitted by this bounded audit.")
    for finding in report.findings:
        location = f" (`{finding.path}`)" if finding.path else ""
        lines.extend(
            [
                f"### {finding.severity.upper()} — {finding.category}{location}",
                "",
                finding.message,
                "",
            ]
        )
        if finding.recommendation:
            lines.extend([f"**Next action:** {finding.recommendation}", ""])
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in report.limitations)
    lines.extend(["", "## Machine-readable report hash", "", f"`{report.report_hash}`", ""])
    return "\n".join(lines)


def write_report_bundle(
    report: RepositoryAuditReport,
    output_dir: str | Path,
) -> dict[str, str]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "audit-report.json"
    markdown_path = destination / "audit-report.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(markdown_path),
        "report_hash": report.report_hash,
    }
