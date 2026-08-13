from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import os
import re
import sys

# Direct execution as `python tools/compile_pr_5k2n_event.py` places only
# `tools/` on sys.path. Restore the repository root explicitly so the
# canonical package is imported without requiring installation.
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from omega_capability_os_t.github_memory import CapabilityRequest
from omega_capability_os_t.github_pr_generation_forest import compile_pr_generation_forest

_CONCEPT_RE = re.compile(r"(?:Ω|OMEGA)[-A-Za-z0-9_∞²³]+")


def compile_event(event: dict[str, Any], *, generation: int, budget: int) -> dict[str, Any]:
    pr = event.get("pull_request") or {}
    repo = (event.get("repository") or {}).get("full_name") or os.environ.get("GITHUB_REPOSITORY", "unknown/unknown")
    number = int(pr.get("number") or event.get("number") or 0)
    title = str(pr.get("title") or "")
    body = str(pr.get("body") or "")
    head = pr.get("head") if isinstance(pr.get("head"), dict) else {}
    request = CapabilityRequest(
        request_id=f"pr-{repo}-{number}",
        description=title,
        domains=("github", "pull-request"),
        consumes=("pr-event", "historical-memory-required-before-materialization"),
        produces=("implementation", "tests", "evidence", "documentation"),
    )
    genome = {
        "ref": f"pr:{repo}#{number}",
        "repository": repo,
        "number": number,
        "lifecycle": "DRAFT" if pr.get("draft") else str(pr.get("state") or "OPEN").upper(),
        "head_sha": head.get("sha"),
        "changed_files": [],
        "named_concepts": sorted(set(_CONCEPT_RE.findall(f"{title}\n{body}"))),
        "intent_tokens": [],
        "boundary": (
            "Event-only PR genome: changed-file/static-symbol/history enrichment must come from "
            "the cumulative-memory stack before physical patch materialization."
        ),
    }
    report = compile_pr_generation_forest(
        request,
        genome,
        generation=generation,
        residual_outputs=request.produces,
        reuse_coverage_ratio=0.0,
        materialization_budget=budget,
    )
    report["event_context"] = {
        "event_only": True,
        "history_enriched": False,
        "physical_materialization_blocked_until_reuse_inspection": True,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--generation", type=int, default=0)
    parser.add_argument("--budget", type=int, default=32)
    args = parser.parse_args()
    if not args.event:
        raise SystemExit("missing --event or GITHUB_EVENT_PATH")
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    report = compile_event(event, generation=args.generation, budget=args.budget)
    Path(args.output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
