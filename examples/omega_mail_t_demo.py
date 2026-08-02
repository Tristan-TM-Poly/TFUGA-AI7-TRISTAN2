"""Run the checked-in Ω-MAIL-T support scenario."""
from __future__ import annotations

import json
from pathlib import Path

from omega_mail_t.engine import run_scenario


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = run_scenario(root / "scenarios" / "omega_mail_t" / "intercompany_support.yaml")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["passed"] else 1)
