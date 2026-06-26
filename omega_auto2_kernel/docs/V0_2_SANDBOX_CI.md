# Ω-AUTO²-Kernel v0.2 — Sandbox + CI

## Objectif

Transformer v0.1 en noyau plus vérifiable avec :

- preview dry-run sans effet externe;
- CI GitHub Actions;
- tests automatiques;
- API exportée pour `dry_run_workflow`.

## Dry-run

Le dry-run retourne :

```text
workflow_id
ok
planned_steps
notes
estimated_cost_units
```

Il ne modifie rien. Il prévisualise seulement les étapes, les notes OAK et le coût abstrait estimé.

## CI

Le workflow GitHub Actions `omega-auto2-ci` exécute :

```bash
cd omega_auto2_kernel
python -m pip install -e .[dev]
pytest -q
```

Il s'active sur pull request et push vers `main` lorsque le module AUTO² change.

## Règle OAK

v0.2 n'ajoute aucune action externe autonome. La progression est strictement :

```text
v0.1 théorie + schémas + MaxCap
v0.2 preview dry-run + CI
v0.3 OAKBench exécutable complet
v0.4 telemetry + proof-of-workflow
```
