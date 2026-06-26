# Ω-AUTO²-Kernel v0.3

**Automatisation de l’Automatisation de TRISTAN** — noyau prototype pour transformer une friction répétée en workflow généré, simulé, validé par OAK, mesuré, mémorisé, prouvé et amélioré en draft.

> ZÉRO-TOUCH maximal, jamais zéro-contrôle.

## Statut OAK

| Dimension | Statut |
|---|---|
| Nature | Prototype logiciel / architecture de recherche |
| Niveau | Draft contrôlé |
| Actions externes | Interdites par défaut |
| Suppression / publication / email / argent | Verrou humain obligatoire |
| Objectif | Générer des workflows OAK-safe à partir de descriptions de tâches |

## Boucle canonique

```text
Friction → LOG/CVCD → Workflow DNA → WorkflowSynth → Sandbox/Dry-run → OAKGate → MaxCap → Telemetry → Proof → ImproveDraft → M⁺/M⁻
```

## Nouveautés v0.2-v0.3

v0.2 ajoute :

- `sandbox.py` : preview dry-run sans effet externe;
- export API `dry_run_workflow`;
- tests sandbox;
- GitHub Actions CI `omega-auto2-ci`;
- documentation `docs/V0_2_SANDBOX_CI.md`.

v0.3 ajoute :

- `telemetry.py` : mesures de succès, valeur, bruit, coût;
- `proof.py` : Proof-of-Workflow minimal;
- `improver.py` : amélioration draft sans exécution;
- tests telemetry/proof/improver.

## Couche MaxCap

La couche **MaxCap** définit et dépasse les capacités de façon mesurée :

```text
Capacity Vector = [scope, autonomy, reversibility, safety, usefulness, reliability, cost_control, learning, integration, value_creation]
```

Elle produit : niveau C0-C7, score global, Anti-Chaos Index, prochaines étapes OAK-safe et blocage si red lock.

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
    assess_capability,
    dry_run_workflow,
    forge_workflow_from_task,
    improve_draft,
    prove_workflow,
)

workflow = forge_workflow_from_task("créer un dépôt GitHub OAK-safe")
telemetry = TelemetrySnapshot(runs=5, successes=5, manual_steps_removed=10, artifacts_created=4, time_saved_minutes=90)

assessment = assess_capability(workflow)
preview = dry_run_workflow(workflow)
proof = prove_workflow(workflow, telemetry)
improved = improve_draft(workflow)

print(assessment.level)
print(preview.to_dict())
print(proof.to_dict())
print(len(improved.steps))
```

## Règles rouges

Ce noyau ne doit jamais autoriser automatiquement : suppression sans backup, publication publique sans OAK/IP check, divulgation de secrets, envoi externe sans consentement, transaction financière, boucle récursive non bornée, expérimentation physique dangereuse, décision médicale/légale autonome.

## Roadmap

1. **v0.1** : schéma + OAKGate + friction score + exemples + MaxCap initial.
2. **v0.2** : sandbox/dry-run + CI GitHub Actions.
3. **v0.3** : telemetry + proof-of-workflow + draft improver.
4. **v0.4** : OAKBench exécutable complet en modules courts.
5. **v0.5** : intégration GitHub/Drive en mode draft only.
6. **v1.0** : AUTO²-Orchestrator avec Human Sovereignty Layer.
