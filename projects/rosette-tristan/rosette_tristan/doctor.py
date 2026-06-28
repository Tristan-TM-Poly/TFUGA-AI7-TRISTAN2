from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROSETTE_COMMANDS = [
    "rosette",
    "rosette-fidelity",
    "rosette-hyper",
    "rosette-render",
    "rosette-real-render",
    "rosette-source-crop",
    "rosette-visual-oak",
    "rosette-bench",
    "rosette-bench-corpus",
    "rosette-corpus-bench",
    "rosette-doctor",
]

OPTIONAL_MODULES = {
    "matplotlib": "render/visual/bench support",
    "fitz": "PDF crop support via PyMuPDF",
}


@dataclass
class CommandCheck:
    name: str
    available: bool
    path: str | None = None


@dataclass
class ModuleCheck:
    module: str
    available: bool
    purpose: str


@dataclass
class DoctorReport:
    python_version: str
    platform: str
    commands: list[CommandCheck]
    optional_modules: list[ModuleCheck]
    oak_status: str
    warnings: list[str] = field(default_factory=list)
    required_next_check: list[str] = field(default_factory=lambda: ["run_ci", "run_rosette_bench", "validate_real_corpus"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "python_version": self.python_version,
            "platform": self.platform,
            "commands": [asdict(command) for command in self.commands],
            "optional_modules": [asdict(module) for module in self.optional_modules],
            "oak_status": self.oak_status,
            "warnings": self.warnings,
            "required_next_check": self.required_next_check,
        }


def check_commands(commands: list[str] | None = None) -> list[CommandCheck]:
    checks: list[CommandCheck] = []
    for command in commands or ROSETTE_COMMANDS:
        path = shutil.which(command)
        checks.append(CommandCheck(name=command, available=path is not None, path=path))
    return checks


def check_optional_modules(modules: dict[str, str] | None = None) -> list[ModuleCheck]:
    checks: list[ModuleCheck] = []
    for module, purpose in (modules or OPTIONAL_MODULES).items():
        checks.append(ModuleCheck(module=module, available=importlib.util.find_spec(module) is not None, purpose=purpose))
    return checks


def run_doctor(require_all_commands: bool = False) -> DoctorReport:
    commands = check_commands()
    modules = check_optional_modules()
    warnings: list[str] = []

    missing_commands = [command.name for command in commands if not command.available]
    missing_modules = [module.module for module in modules if not module.available]
    if missing_commands:
        warnings.append(f"missing commands: {', '.join(missing_commands)}")
    if missing_modules:
        warnings.append(f"missing optional modules: {', '.join(missing_modules)}")
    if require_all_commands and missing_commands:
        oak_status = "doctor_failed_missing_commands"
    elif any(module.module == "matplotlib" and not module.available for module in modules):
        oak_status = "doctor_review_needed_optional_render_missing"
    else:
        oak_status = "doctor_passed_not_certified"

    return DoctorReport(
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        commands=commands,
        optional_modules=modules,
        oak_status=oak_status,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-doctor")
    parser.add_argument("--out", default=None, help="Write doctor report JSON to this path")
    parser.add_argument("--require-all-commands", action="store_true", help="Fail if a Rosette command is not on PATH")
    args = parser.parse_args(argv)
    report = run_doctor(require_all_commands=args.require_all_commands)
    payload = report.to_dict()
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if not report.oak_status.startswith("doctor_failed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
