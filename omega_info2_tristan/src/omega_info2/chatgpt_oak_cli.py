"""Command-line interface for the M-CHATGPT-OAK gate."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from typing import Any

from .chatgpt_oak_gate import ChatGPTOAKGate, GitHubRunContext


_BOOL_FIELDS = {
    "requested_go_github",
    "pr_open",
    "ci_green",
    "mergeable",
    "merged",
    "human_approval_required",
    "used_fresh_head_sha",
    "summary_after_merge",
}


def context_from_mapping(data: dict[str, Any]) -> GitHubRunContext:
    """Build a GitHubRunContext from a dict, ignoring unknown keys."""
    allowed = {field.name for field in fields(GitHubRunContext)}
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if key not in allowed:
            continue
        if key in _BOOL_FIELDS:
            cleaned[key] = _as_bool(value)
        elif key == "checks_per_head_sha":
            cleaned[key] = int(value)
        elif key == "real_blocker":
            cleaned[key] = None if value in (None, "", "null") else str(value)
        else:
            cleaned[key] = value
    return GitHubRunContext(**cleaned)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _read_json(path: str | None) -> dict[str, Any]:
    if path in (None, "-"):
        raw = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    if not raw.strip():
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Context JSON must be an object.")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a Tristan Go GitHub workflow context with M-CHATGPT-OAK.")
    parser.add_argument("--context", help="Path to context JSON. Use '-' or omit to read stdin.")
    parser.add_argument("--rules", action="store_true", help="Print the negative-memory rules as Markdown.")
    parser.add_argument("--exit-nonzero-on-fail", action="store_true", help="Exit with code 2 when the gate fails.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    gate = ChatGPTOAKGate()

    if args.rules:
        print(gate.rules_as_markdown())
        return 0

    context = context_from_mapping(_read_json(args.context))
    decision = gate.evaluate_github_context(context)
    print(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    if args.exit_nonzero_on_fail and not decision.passed:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
