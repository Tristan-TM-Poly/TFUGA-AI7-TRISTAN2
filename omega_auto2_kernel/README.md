# Ω-AUTO²-Kernel v0.1

**Automatisation de l’Automatisation de TRISTAN** — noyau prototype pour transformer une friction répétée en workflow généré, simulé, validé par OAK, mesuré, mémorisé et régénéré.

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
Friction → LOG/CVCD → Workflow DNA → WorkflowSynth → Sandbox/Dry-run → OAKGate → MaxCap → Telemetry → M⁺/M⁻ → Regenerator
```

## Couche MaxCap

La couche **MaxCap** définit et dépasse les capacités de façon mesurée :

```text
Capacity Vector = [scope, autonomy, reversibility, safety, usefulness, reliability, cost_control, learning, integration, value_creation]
```

Elle produit :

- un niveau de capacité `C0` à `C7`;
- un score global normalisé;
- un Anti-Chaos Index;
- une liste de prochaines étapes de dépassement OAK-safe;
- un blocage si un red lock est touché.

Un dépassement est valide seulement si :

```text
capability_after > capability_before
AND oak_score_after >= oak_score_before
AND anti_chaos_after >= anti_chaos_before
AND red_locks_violated = 0
```

## Modules inclus

```text
omega_auto2_kernel/
├── omega_auto2/
│   ├── models.py          # structures minimales
│   ├── friction.py        # score de priorité d’automatisation
│   ├── workflow_synth.py  # génération workflow depuis tâche
│   ├── oak_gate.py        # validation sécurité/OAK
│   ├── capabilities.py    # MaxCap: capacité, dépassement, Anti-Chaos
│   ├── memory.py          # M⁺/M⁻ minimal
│   └── cli.py             # interface CLI prototype
├── schemas/               # contrats YAML
├── examples/              # workflows exemples
├── tests/                 # tests unitaires
├── docs/                  # théorie canonique + MaxCap
└── m_minus_registry.json  # anti-patterns initiaux
```

## Installation locale

```bash
cd omega_auto2_kernel
python -m pip install -e .
pytest
```

## Exemple d’usage

```bash
python -m omega_auto2.cli forge "résumer chaque matin mes sujets importants et proposer 3 actions OAK-safe"
```

Exemple Python MaxCap :

```python
from omega_auto2 import forge_workflow_from_task, assess_capability

workflow = forge_workflow_from_task("créer un dépôt GitHub OAK-safe")
assessment = assess_capability(workflow)
print(assessment.level)
print(assessment.vector.score())
print(assessment.next_safe_exceed_steps)
```

## Règles rouges

Ce noyau ne doit jamais autoriser automatiquement :

- suppression sans backup;
- publication publique sans OAK/IP check;
- divulgation de secrets;
- envoi externe sans consentement;
- transaction financière;
- boucle récursive non bornée;
- expérimentation physique dangereuse;
- décision médicale/légale autonome.

## Roadmap

1. **v0.1** : schéma + OAKGate + friction score + exemples + MaxCap initial.
2. **v0.2** : sandbox/dry-run avec diff preview.
3. **v0.3** : générateur de tests automatique.
4. **v0.4** : telemetry + preuve de workflow.
5. **v0.5** : intégration GitHub/Drive en mode draft only.
6. **v1.0** : AUTO²-Orchestrator avec Human Sovereignty Layer.
