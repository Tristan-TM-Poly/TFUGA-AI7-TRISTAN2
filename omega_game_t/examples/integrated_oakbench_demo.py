from __future__ import annotations

import json

from omega_game.engines.integrated_oakbench import run_integrated_oakbench


def main() -> int:
    report = run_integrated_oakbench()
    print(json.dumps(report.to_dict(), sort_keys=True, ensure_ascii=False, indent=2))
    return 0 if report.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
