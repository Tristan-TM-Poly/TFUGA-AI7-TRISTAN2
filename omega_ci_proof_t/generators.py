from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from .models import MMinusRule


class MMinusRegressionGenerator:
    def generate(self, rules: Iterable[MMinusRule]) -> str:
        ordered = sorted(rules, key=lambda item: item.rule_id)
        imports = sorted({rule.import_line.strip() for rule in ordered if rule.import_line.strip()})
        lines = [
            '"""Generated regression candidates from Ω-CI M-minus rules.',
            '',
            'Do not promote these tests without reviewing their claim alignment.',
            '"""',
            'from __future__ import annotations',
            '',
            *imports,
            '',
        ]
        for rule in ordered:
            lines.extend([
                f"# Source: {rule.source_failure_id} / {rule.rule_id}",
                f"def {rule.test_name}():",
            ])
            if not rule.assertions:
                lines.append('    raise AssertionError("M-minus rule has no assertions")')
            else:
                lines.extend(f"    {assertion}" for assertion in rule.assertions)
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def load(path: str | Path) -> tuple[MMinusRule, ...]:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, Mapping) or not isinstance(raw.get("rules"), list):
            raise TypeError("M-minus registry must contain a rules list")
        return tuple(MMinusRule(
            rule_id=str(item["rule_id"]),
            failure_summary=str(item["failure_summary"]),
            test_name=str(item["test_name"]),
            import_line=str(item["import_line"]),
            assertions=tuple(str(value) for value in item.get("assertions", [])),
            source_failure_id=str(item["source_failure_id"]),
            risk=str(item.get("risk", "normal")),
        ) for item in raw["rules"])
