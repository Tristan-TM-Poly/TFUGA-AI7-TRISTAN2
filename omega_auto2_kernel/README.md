# Ω-AUTO²-Kernel v0.4

**Automatisation de l’Automatisation de TRISTAN** — noyau prototype pour transformer une friction répétée en workflow généré, simulé, validé par OAK, mesuré, prouvé, amélioré et benché.

> ZÉRO-TOUCH maximal, jamais zéro-contrôle.

## Statut OAK

| Dimension | Statut |
|---|---|
| Nature | Prototype logiciel / architecture de recherche |
| Niveau | Draft contrôlé |
| Actions externes | Interdites par défaut |
| Suppression / publication / email / argent | Verrou humain obligatoire |
| Objectif | Générer, prévisualiser, mesurer et benchmarker des workflows OAK-safe |

## Boucle canonique

```text
Friction → LOG/CVCD → Workflow DNA → WorkflowSynth → Sandbox/Dry-run → OAKGate → MaxCap → Telemetry → Proof → Bench → Report → ImproveDraft → M⁺/M⁻
```

## Nouveautés v0.2-v0.4

v0.2 ajoute `sandbox.py`, `dry_run_workflow`, tests sandbox, GitHub Actions CI et docs CI.

v0.3 ajoute `telemetry.py`, `proof.py`, `improver.py` et tests telemetry/proof/improver.

v0.4 ajoute :

- `bench.py` : `run_bench`, `run_suite`, `BenchResult`;
- `report.py` : `build_markdown_report`;
- tests bench/report;
- documentation `docs/V0_4_BENCH_REPORTS.md`.

## Couche MaxCap

```text
Capacity Vector = [scope, autonomy, reversibility, safety, usefulness, reliability, cost_control, learning, integration, value_creation]
```

La capacité n'est canonique que si elle reste OAK-safe, mesurable, réversible ou contrôlée.

## Modules inclus

```text
omega_auto2_kernel/
├── omega_auto2/
│   ├── models.py
│   ├── friction.py
│   ├── workflow_synth.py
│   ├── oak_gate.py
│   ├── capabilities.py
│   ├── sandbox.py
│   ├── telemetry.py
│   ├── proof.py
│   ├── bench.py
│   ├── report.py
│   ├── improver.py
│   ├── memory.py
│   └── cli.py
├── schemas/
├── examples/
├── tests/
├── docs/
└── m_minus_registry.json
```

## Installation locale

```bash
cd omega_auto2_kernel
python -m pip install -e .
pytest
```

## Exemple d’usage

```python
from omega_auto2 import (
    TelemetrySnapshot,
    build_markdown_report,
    forge_workflow_from_task,
    run_bench,
)

workflow = forge_workflow_from_task("créer un dépôt GitHub OAK-safe")
telemetry = TelemetrySnapshot(runs=5, successes=5, manual_steps_removed=10, artifacts_created=4, time_saved_minutes=90)

result = run_bench(workflow, telemetry)
report = build_markdown_report([workflow], telemetry)

print(result.to_dict())
print(report)
```

## Règles rouges

Ce noyau ne doit jamais autoriser automatiquement : suppression sans backup, publication publique sans OAK/IP check, divulgation de secrets, envoi externe sans consentement, transaction financière, boucle récursive non bornée, expérimentation physique dangereuse, décision médicale/légale autonome.

## Roadmap

1. **v0.1** : schéma + OAKGate + friction score + exemples + MaxCap initial.
2. **v0.2** : sandbox/dry-run + CI GitHub Actions.
3. **v0.3** : telemetry + proof-of-workflow + draft improver.
4. **v0.4** : bench suite + markdown reports.
5. **v0.5** : workflows canoniques benchés + exports JSON/Markdown enrichis.
6. **v1.0** : AUTO²-Orchestrator avec Human Sovereignty Layer.
