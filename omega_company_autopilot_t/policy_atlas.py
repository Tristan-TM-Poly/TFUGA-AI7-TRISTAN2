"""Deterministic CVCD policy atlas for corporate autonomy decisions."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterator, Sequence

DIVISIONS = (
    "oak_systems", "software_labs", "research_foundry", "spectroscopy",
    "materials", "energy_systems", "quantum_labs", "crystal_systems",
    "mail_systems", "audit_services", "legal_ip", "finance",
    "security", "education", "game_worlds", "holding",
)
PROCESSES = (
    "internal_reporting", "mail_and_support", "customer_onboarding", "invoice_and_receivables",
    "vendor_and_payables", "treasury", "contracts", "government_registry",
    "tax", "banking", "shareholders", "intellectual_property",
    "privacy", "security", "human_resources", "domain_and_dns",
    "sales", "marketing", "research", "product_release",
    "incident_response", "records_retention", "board_governance", "spinout_review",
)
RISK_MODES = (
    "low_reversible_internal", "moderate_reversible_internal", "high_internal", "low_external",
    "moderate_external", "high_external", "critical_external", "irreversible",
)
LAYERS = ("plan", "gate", "evidence")


@dataclass(frozen=True, slots=True)
class AtlasCell:
    layer: str
    division: str
    process: str
    risk_mode: str
    autonomy_level: int
    cell_id: str


class PolicyAtlas:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))

    def decode(self, path: Path, line_number: int) -> AtlasCell:
        relative = path.relative_to(self.root)
        if len(relative.parts) != 3:
            raise ValueError("invalid_atlas_path")
        layer, division_code, filename = relative.parts
        process_code = filename.removesuffix(".cells")
        risk_code, autonomy_code = path.read_text(encoding="utf-8").splitlines()[line_number - 1].split("|")
        return AtlasCell(
            layer=layer,
            division=self.manifest["division_codes"][division_code],
            process=self.manifest["process_codes"][process_code],
            risk_mode=self.manifest["risk_codes"][risk_code],
            autonomy_level=int(autonomy_code[1:]),
            cell_id=f"company:{layer}:{division_code}:{process_code}:{risk_code}:{autonomy_code}",
        )

    def iter_cells(self, *, layer: str | None = None) -> Iterator[AtlasCell]:
        layers = [layer] if layer else list(self.manifest["layers"])
        for layer_name in layers:
            for division_code in self.manifest["division_codes"]:
                for process_code in self.manifest["process_codes"]:
                    path = self.root / layer_name / division_code / f"{process_code}.cells"
                    for line_number in range(1, self.manifest["cells_per_file"] + 1):
                        yield self.decode(path, line_number)

    def audit(self) -> dict[str, object]:
        missing: list[str] = []
        malformed: list[str] = []
        expected_lines = self.manifest["cells_per_file"]
        file_count = 0
        for layer in self.manifest["layers"]:
            for division_code in self.manifest["division_codes"]:
                for process_code in self.manifest["process_codes"]:
                    path = self.root / layer / division_code / f"{process_code}.cells"
                    if not path.exists():
                        missing.append(str(path.relative_to(self.root)))
                        continue
                    file_count += 1
                    if len(path.read_text(encoding="utf-8").splitlines()) != expected_lines:
                        malformed.append(str(path.relative_to(self.root)))
        return {"passed": not missing and not malformed, "file_count": file_count, "record_count": file_count * expected_lines, "missing": missing, "malformed": malformed}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-company-policy-atlas")
    parser.add_argument("root", type=Path)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--layer", choices=LAYERS)
    parser.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    atlas = PolicyAtlas(args.root)
    if args.audit:
        report = atlas.audit()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["passed"] else 1
    rows = []
    for index, cell in enumerate(atlas.iter_cells(layer=args.layer)):
        if index >= args.limit: break
        rows.append({"layer": cell.layer, "division": cell.division, "process": cell.process, "risk_mode": cell.risk_mode, "autonomy_level": cell.autonomy_level, "cell_id": cell.cell_id})
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
