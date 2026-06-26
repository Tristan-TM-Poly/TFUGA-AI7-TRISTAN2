from __future__ import annotations

import json
import sys

from .oak_gate import evaluate_workflow
from .workflow_synth import forge_workflow_from_task


def main() -> int:
    task = " ".join(sys.argv[1:]).strip()
    if not task:
        task = "résumer une friction répétée et générer un workflow OAK-safe"

    workflow = forge_workflow_from_task(task)
    report = evaluate_workflow(workflow)
    payload = {}
    payload.update(workflow.to_dict())
    payload.update(report.to_dict())
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    main()
