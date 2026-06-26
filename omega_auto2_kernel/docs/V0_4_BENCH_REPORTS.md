# Ω-AUTO²-Kernel v0.4 — Bench + Reports

## Objectif

v0.4 ajoute un banc de validation compact et un générateur de rapport Markdown.

## Modules

- `bench.py` : `run_bench`, `run_suite`, `BenchResult`
- `report.py` : `build_markdown_report`

## Principe

Un workflow est évalué par :

```text
Workflow → MaxCap → Dry-run → Proof-of-Workflow → BenchResult
```

Le bench mesure :

- `capacity_score`
- `proof_score`
- `dry_run_ok`
- `passed`
- `notes`

## Exemple

```python
from omega_auto2 import TelemetrySnapshot, build_markdown_report, forge_workflow_from_task, run_bench

workflow = forge_workflow_from_task("créer un dépôt GitHub OAK-safe")
telemetry = TelemetrySnapshot(runs=3, successes=3, manual_steps_removed=5, artifacts_created=2, time_saved_minutes=30)

result = run_bench(workflow, telemetry)
report = build_markdown_report([workflow], telemetry)
```

## OAK

v0.4 ne déclenche aucune action externe. Il ne fait que mesurer, scorer et produire un rapport local/draft.

## Prochaine étape

v0.5 pourra ajouter un export JSON/Markdown plus riche et un benchmark suite pour workflows canoniques : Daily Briefing, GitHub Factory, MaxCap Assessment, DriveBrain Draft.
