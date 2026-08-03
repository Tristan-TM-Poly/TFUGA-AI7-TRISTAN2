#!/usr/bin/env python3
"""AI-PANTHEO^n bounded agent registry prototype."""
from __future__ import annotations
import json

AGENTS = {
    "FORGE-PRIME": {
        "role": "generation and projection",
        "allowed": ["draft", "local_patch", "code_stub", "chapter_outline"],
        "blocked": ["deploy", "payment", "self_replication", "credential_access"]
    },
    "EVIDENCE-OAK": {
        "role": "evidence and promotion",
        "allowed": ["power_real", "r0_r5_status", "gate_decision"],
        "blocked": ["bypass_measurement", "promote_without_evidence"]
    },
    "RED-SHADOW": {
        "role": "adversarial review",
        "allowed": ["risk_report", "failure_mode", "redteam_questions"],
        "blocked": ["destructive_execution", "external_attack"]
    },
    "OUROBOROS-OMEGA": {
        "role": "loop and approval guard",
        "allowed": ["changelog", "rollback_plan", "approval_check"],
        "blocked": ["autonomous_external_mutation", "push_to_main_without_review"]
    }
}


def main() -> int:
    print(json.dumps({"mode": "local_patch_only", "agents": AGENTS}, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
