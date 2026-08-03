"""Evidence-oriented JSON and Markdown report compiler for R∞ MAX."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ReportSection:
    section_id: str
    title: str
    status: str
    summary: str
    facts: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    metrics: Mapping[str, Any] = field(default_factory=dict)
    tables: tuple[tuple[str, tuple[Mapping[str, Any], ...]], ...] = ()

    def __post_init__(self) -> None:
        if not self.section_id or not self.title:
            raise ValueError("section ID and title are required")
        if self.status not in {
            "planned",
            "implemented",
            "tested",
            "partially_validated",
            "validated_fixture",
            "blocked",
            "falsified",
            "proved",
            "formally_proved",
        }:
            raise ValueError(f"unsupported status: {self.status}")

    def to_dict(self) -> dict[str, object]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "status": self.status,
            "summary": self.summary,
            "facts": list(self.facts),
            "limitations": list(self.limitations),
            "evidence_ids": list(self.evidence_ids),
            "metrics": dict(self.metrics),
            "tables": [
                {"title": title, "rows": [dict(row) for row in rows]}
                for title, rows in self.tables
            ],
        }


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    kind: str
    digest: str
    provenance: str
    statement: str
    reproducible: bool
    independent: bool = False

    def __post_init__(self) -> None:
        if len(self.digest) != 64:
            raise ValueError("evidence digest must have SHA-256 length")

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "kind": self.kind,
            "digest": self.digest,
            "provenance": self.provenance,
            "statement": self.statement,
            "reproducible": self.reproducible,
            "independent": self.independent,
        }


@dataclass
class MaxReport:
    report_id: str
    title: str
    version: str
    scope: str
    sections: list[ReportSection] = field(default_factory=list)
    evidence: dict[str, EvidenceReference] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    global_identity_proved: bool = False
    formal_proof_completed: bool = False

    def __post_init__(self) -> None:
        if self.global_identity_proved or self.formal_proof_completed:
            raise ValueError(
                "automatic MAX report construction cannot assert proof completion; "
                "attach an independently reviewed proof artifact through a dedicated promotion path"
            )

    def add_evidence(self, reference: EvidenceReference) -> None:
        existing = self.evidence.get(reference.evidence_id)
        if existing is not None and existing != reference:
            raise ValueError(f"evidence ID collision: {reference.evidence_id}")
        self.evidence[reference.evidence_id] = reference

    def add_section(self, section: ReportSection) -> None:
        if any(existing.section_id == section.section_id for existing in self.sections):
            raise ValueError(f"duplicate section: {section.section_id}")
        unknown = [evidence_id for evidence_id in section.evidence_ids if evidence_id not in self.evidence]
        if unknown:
            raise KeyError(f"section references unknown evidence: {unknown}")
        self.sections.append(section)

    def validate(self) -> list[str]:
        errors = []
        section_ids = [section.section_id for section in self.sections]
        if len(section_ids) != len(set(section_ids)):
            errors.append("duplicate section IDs")
        for section in self.sections:
            for evidence_id in section.evidence_ids:
                if evidence_id not in self.evidence:
                    errors.append(f"{section.section_id}: unknown evidence {evidence_id}")
            if section.status in {"proved", "formally_proved"}:
                errors.append(
                    f"{section.section_id}: automatic report cannot promote section to {section.status}"
                )
        if self.formal_proof_completed and not self.global_identity_proved:
            errors.append("formal proof flag without global proof flag")
        return errors

    def to_dict(self) -> dict[str, object]:
        payload = {
            "schema": "omega-sequence-forms-max-report/1",
            "report_id": self.report_id,
            "title": self.title,
            "version": self.version,
            "scope": self.scope,
            "sections": [section.to_dict() for section in self.sections],
            "evidence": [self.evidence[key].to_dict() for key in sorted(self.evidence)],
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
            "validation_errors": self.validate(),
            "global_identity_proved": False,
            "formal_proof_completed": False,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload["report_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload

    def markdown(self) -> str:
        payload = self.to_dict()
        lines = [
            f"# {self.title}",
            "",
            f"- **Report ID:** `{self.report_id}`",
            f"- **Version:** `{self.version}`",
            f"- **Scope:** {self.scope}",
            f"- **Digest:** `{payload['report_digest']}`",
            "- **Global identity proved:** `false`",
            "- **Formal proof completed:** `false`",
            "",
        ]
        if self.warnings:
            lines.extend(["## OAK warnings", ""])
            lines.extend(f"- {warning}" for warning in self.warnings)
            lines.append("")
        for section in self.sections:
            lines.extend(
                [
                    f"## {section.title}",
                    "",
                    f"**Status:** `{section.status}`",
                    "",
                    section.summary,
                    "",
                ]
            )
            if section.facts:
                lines.append("### Verified facts")
                lines.append("")
                lines.extend(f"- {fact}" for fact in section.facts)
                lines.append("")
            if section.metrics:
                lines.append("### Metrics")
                lines.append("")
                lines.append("| Metric | Value |")
                lines.append("|---|---:|")
                for key, value in sorted(section.metrics.items()):
                    lines.append(f"| `{key}` | `{_markdown_value(value)}` |")
                lines.append("")
            for table_title, rows in section.tables:
                lines.append(f"### {table_title}")
                lines.append("")
                lines.extend(_markdown_table(rows))
                lines.append("")
            if section.evidence_ids:
                lines.append("### Evidence")
                lines.append("")
                for evidence_id in section.evidence_ids:
                    evidence = self.evidence[evidence_id]
                    lines.append(
                        f"- `{evidence.evidence_id}` — {evidence.statement} "
                        f"(digest `{evidence.digest}`, provenance `{evidence.provenance}`)"
                    )
                lines.append("")
            if section.limitations:
                lines.append("### Limitations")
                lines.append("")
                lines.extend(f"- {limitation}" for limitation in section.limitations)
                lines.append("")
        lines.extend(
            [
                "## Epistemic boundary",
                "",
                "> Finite-prefix agreement, generated volume, benchmark success and symbolic elegance do not replace a global mathematical proof.",
                "",
            ]
        )
        return "\n".join(lines)

    def write(self, directory: str | Path) -> dict[str, object]:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        json_path = root / "report.json"
        markdown_path = root / "REPORT.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        markdown_path.write_text(self.markdown(), encoding="utf-8")
        return {
            "report_id": self.report_id,
            "report_digest": payload["report_digest"],
            "json_path": str(json_path),
            "markdown_path": str(markdown_path),
            "json_sha256": sha256(json_path.read_bytes()).hexdigest(),
            "markdown_sha256": sha256(markdown_path.read_bytes()).hexdigest(),
        }


def _markdown_value(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("|", "\\|")


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    if not rows:
        return ["_No rows._"]
    columns = sorted({str(key) for row in rows for key in row})
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(_markdown_value(row.get(column, "")) for column in columns)
            + " |"
        )
    return lines


def evidence_from_payload(
    *,
    evidence_id: str,
    kind: str,
    payload: Mapping[str, Any],
    provenance: str,
    statement: str,
    reproducible: bool = True,
    independent: bool = False,
) -> EvidenceReference:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return EvidenceReference(
        evidence_id=evidence_id,
        kind=kind,
        digest=sha256(canonical.encode("utf-8")).hexdigest(),
        provenance=provenance,
        statement=statement,
        reproducible=reproducible,
        independent=independent,
    )


def build_rinf_max_report(
    *,
    catalog_receipt: Mapping[str, Any],
    benchmark_receipt: Mapping[str, Any],
    campaign_receipt: Mapping[str, Any] | None = None,
    theorem_report: Mapping[str, Any] | None = None,
) -> MaxReport:
    report = MaxReport(
        report_id="omega-sequence-forms-rinf-max",
        title="Ω-SUITE-FORM-T∞ R∞ MAX Evidence Report",
        version="RINF-MAX-1",
        scope="Computational discovery of analytic sequence representations",
        warnings=[
            "A finite prefix is compatible with infinitely many continuations.",
            "Logical cells are research addresses, not completed experiments.",
            "Generated native code needs independent build and test receipts.",
            "No automatic section is promoted to mathematical or formal proof.",
        ],
        metadata={"permanent_total_cap": None},
    )
    catalog_evidence = evidence_from_payload(
        evidence_id="evidence.catalog",
        kind="catalog_receipt",
        payload=catalog_receipt,
        provenance="omega_sequence_forms_t.rinf",
        statement="The deterministic catalog receipt was generated.",
    )
    benchmark_evidence = evidence_from_payload(
        evidence_id="evidence.benchmark",
        kind="benchmark_receipt",
        payload=benchmark_receipt,
        provenance="omega_sequence_forms_t.rinf",
        statement="The software fixture benchmark receipt was generated.",
    )
    report.add_evidence(catalog_evidence)
    report.add_evidence(benchmark_evidence)
    report.add_section(
        ReportSection(
            section_id="catalog",
            title="Logical research atlas",
            status="implemented",
            summary="The catalog exposes analytic families, transformations and OAK anti-patterns through deterministic identifiers.",
            facts=(
                "Catalog records have deterministic hashes.",
                "The logical address space is traversed without full in-memory materialization.",
            ),
            limitations=(
                "Catalog presence does not imply detector implementation.",
                "Logical cells are not experimental results.",
            ),
            evidence_ids=(catalog_evidence.evidence_id,),
            metrics={
                "families": catalog_receipt.get("counts", {}).get("families"),
                "transformations": catalog_receipt.get("counts", {}).get("transformations"),
                "antipatterns": catalog_receipt.get("counts", {}).get("antipatterns"),
            },
        )
    )
    report.add_section(
        ReportSection(
            section_id="benchmark",
            title="OAKBench fixtures",
            status="validated_fixture" if benchmark_receipt.get("passed") else "blocked",
            summary="Synthetic fixtures test recovery, held-out prediction, adversarial demotion and deterministic receipts.",
            limitations=(
                "Synthetic fixtures are not independent scientific validation.",
                "Passing fixtures do not prove all future inputs are handled correctly.",
            ),
            evidence_ids=(benchmark_evidence.evidence_id,),
            metrics={
                "passed": benchmark_receipt.get("passed"),
                "global_identity_proved": benchmark_receipt.get("global_identity_proved", False),
            },
        )
    )
    if campaign_receipt is not None:
        evidence = evidence_from_payload(
            evidence_id="evidence.campaign",
            kind="campaign_receipt",
            payload=campaign_receipt,
            provenance="omega_sequence_forms_t.rinf",
            statement="A finite adaptive campaign was executed.",
        )
        report.add_evidence(evidence)
        report.add_section(
            ReportSection(
                section_id="campaign",
                title="Adaptive campaign",
                status="tested",
                summary="A finite resource-bounded slice of the logical space was selected and recorded.",
                limitations=("A campaign budget is finite even when the long-run research program has no permanent cell cap.",),
                evidence_ids=(evidence.evidence_id,),
                metrics={
                    "executed_cells": campaign_receipt.get("executed_cells"),
                    "stop_reason": campaign_receipt.get("stop_reason"),
                    "permanent_total_cap": campaign_receipt.get("permanent_total_cap"),
                },
            )
        )
    if theorem_report is not None:
        evidence = evidence_from_payload(
            evidence_id="evidence.theorem-miner",
            kind="conjecture_report",
            payload=theorem_report,
            provenance="omega_sequence_forms_t.rinf.theorem_miner",
            statement="Finite-prefix relation candidates were mined.",
        )
        report.add_evidence(evidence)
        report.add_section(
            ReportSection(
                section_id="relations",
                title="Relation and theorem candidates",
                status="partially_validated",
                summary="Exact relations were searched over observed and held-out indices.",
                limitations=(
                    "Every relation remains a conjecture until a global argument is supplied.",
                    "Polynomial lifts can generate high-complexity overfits.",
                ),
                evidence_ids=(evidence.evidence_id,),
                metrics={"relation_count": theorem_report.get("relation_count", 0)},
            )
        )
    return report
