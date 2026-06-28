"""Command line dry-run interface for omega_action_ext_t."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .core import ActionDNA, RiskTensor
from .policy import OAKGate


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def action_from_dict(data: dict[str, Any]) -> ActionDNA:
    risk_data = data.get("risk", {}) or {}
    risk = RiskTensor(
        legal=int(risk_data.get("legal", 0)),
        ip=int(risk_data.get("ip", 0)),
        finance=int(risk_data.get("finance", 0)),
        safety=int(risk_data.get("safety", 0)),
        privacy=int(risk_data.get("privacy", 0)),
        reputation=int(risk_data.get("reputation", 0)),
        irreversibility=int(risk_data.get("irreversibility", 0)),
    )
    return ActionDNA(
        name=str(data["name"]),
        system=str(data["system"]),
        action_type=str(data["action_type"]),
        intent=str(data.get("intent", "")),
        target=data.get("target"),
        risk=risk,
        reversible=bool(data.get("reversible", False)),
        rollback=data.get("rollback"),
        approved=bool(data.get("approved", False)),
        public=bool(data.get("public", False)),
        destructive=bool(data.get("destructive", False)),
        touches_humans=bool(data.get("touches_humans", False)),
        touches_money=bool(data.get("touches_money", False)),
        touches_ip=bool(data.get("touches_ip", False)),
        touches_health=bool(data.get("touches_health", False)),
        touches_safety=bool(data.get("touches_safety", False)),
        metadata=dict(data.get("metadata", {}) or {}),
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: omega-action ACTION.json", file=sys.stderr)
        return 2

    action = action_from_dict(_load_json(Path(argv[0])))
    report = OAKGate().dry_run(action)
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
