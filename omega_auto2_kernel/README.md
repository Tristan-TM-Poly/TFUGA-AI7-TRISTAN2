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
Friction → LOG/CVCD → Workflow DNA → WorkflowSynth → Sandbox/Dry-run → OAKGate → Telemetry → M⁺/M⁻ → Regenerator
```

## Modules inclus

```text
omega_auto2_kernel/
├── omega_auto2/
│   ├── models.py          # structures minimales
│   ├── friction.py        # score de priorité d’automatisation
│   ├── workflow_synth.py  # génération workflow depuis tâche
│   ├── oak_gate.py        # validation sécurité/OAK
│   ├── memory.py          # M⁺/M⁻ minimal
│   └── cli.py             # interface CLI prototype
├── schemas/               # contrats YAML
├── examples/              # workflows exemples
├── tests/                 # tests unitaires
├── docs/                  # théorie canonique
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

Sortie attendue :

```yaml
workflow:
  name: generated_workflow
  mode: dry_run_first
  oak_status: draft
  human_approval_required_for:
    - external_email
    - public_publish
    - delete_files
    - spend_money
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

1. **v0.1** : schéma + OAKGate + friction score + exemples.
2. **v0.2** : sandbox/dry-run avec diff preview.
3. **v0.3** : générateur de tests automatique.
4. **v0.4** : telemetry + preuve de workflow.
5. **v0.5** : intégration GitHub/Drive en mode draft only.
6. **v1.0** : AUTO²-Orchestrator avec Human Sovereignty Layer.
