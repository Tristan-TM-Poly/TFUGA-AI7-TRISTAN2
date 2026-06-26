# Ω-AUTO²-Kernel v0.5

**Automatisation de l’Automatisation de TRISTAN** — noyau prototype pour transformer une friction répétée en workflow généré, simulé, validé par OAK, mesuré, prouvé, amélioré, benché et exporté.

> ZÉRO-TOUCH maximal, jamais zéro-contrôle.

## Statut OAK

| Dimension | Statut |
|---|---|
| Nature | Prototype logiciel / architecture de recherche |
| Niveau | Draft contrôlé |
| Actions externes | Interdites par défaut |
| Suppression / publication / email / argent | Verrou humain obligatoire |
| Objectif | Générer, prévisualiser, mesurer, benchmarker et exporter des workflows OAK-safe |

## Boucle canonique

```text
Friction → LOG/CVCD → Workflow DNA → WorkflowSynth → Sandbox/Dry-run → OAKGate → MaxCap → Telemetry → Proof → Bench → Export → Report → ImproveDraft → M⁺/M⁻
```

## Nouveautés v0.5

v0.5 ajoute :

- `canonical.py` : workflows canoniques Daily, GitHub, MaxCap, DriveBrain;
- `exporters.py` : exports JSON et Markdown;
- tests canonical/export;
- documentation `docs/V0_5_CANONICAL_BENCHMARKS.md`.

## Workflows canoniques

```text
daily_briefing
github_factory
maxcap_assessment
drivebrain_draft
```

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
│   ├── canonical.py
│   ├── exporters.py
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
from omega_auto2 import canonical_workflows, suite_json, suite_markdown

workflows = canonical_workflows()
json_report = suite_json(workflows)
markdown_report = suite_markdown(workflows)

print(json_report)
print(markdown_report)
```

## Règles rouges

Ce noyau ne doit jamais autoriser automatiquement : suppression sans backup, publication publique sans OAK/IP check, divulgation de secrets, envoi externe sans consentement, transaction financière, boucle récursive non bornée, expérimentation physique dangereuse, décision médicale/légale autonome.

## Roadmap

1. **v0.1** : schéma + OAKGate + friction score + exemples + MaxCap initial.
2. **v0.2** : sandbox/dry-run + CI GitHub Actions.
3. **v0.3** : telemetry + proof-of-workflow + draft improver.
4. **v0.4** : bench suite + markdown reports.
5. **v0.5** : workflows canoniques benchés + exports JSON/Markdown enrichis.
6. **v0.6** : CLI bench canonique + fixtures de référence.
7. **v1.0** : AUTO²-Orchestrator avec Human Sovereignty Layer.
