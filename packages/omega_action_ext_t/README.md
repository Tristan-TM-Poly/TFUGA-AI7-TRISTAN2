# omega_action_ext_t

MVP de **Ω-ACTION-EXT-T / Actions Externes de Tristan**.

Ce package transforme une intention d'action externe en objet vérifiable :

```text
Intent → ActionDNA → RiskTensor → OAKGate → DryRunReport → Approval/Execution/Proof → M⁺/M⁻
```

## Principe

> Automatiser l'action, pas automatiser l'irresponsabilité.

Le comportement par défaut est prudent :

- `send_email` sans approbation devient `ALLOW_DRAFT`, pas envoi direct ;
- action publique avec IP non approuvée devient `NEEDS_APPROVAL` ;
- risque critique devient `REQUIRE_EXPERT` ou `BLOCK` ;
- action faible risque et réversible peut devenir `ALLOW_AUTO` ;
- action destructive sans rollback est bloquée.

## Exemple CLI

```bash
python -m omega_action_ext_t.cli examples/professor_outreach.json
```

Sortie attendue : un rapport JSON indiquant la décision OAK, les raisons, les garde-fous et la preuve attendue.

## Exemple Python

```python
from omega_action_ext_t import ActionDNA, RiskTensor, OAKGate

action = ActionDNA(
    name="Contact professor",
    system="gmail",
    action_type="send_email",
    risk=RiskTensor(ip=2, reputation=2, privacy=1),
    touches_humans=True,
    touches_ip=True,
    approved=False,
)

report = OAKGate().dry_run(action)
print(report.decision.value)
# allow_draft
```

## Statut

Prototype local/canonique. Aucune exécution externe réelle n'est incluse dans ce MVP. Les connecteurs doivent rester `dry-run-first` jusqu'à intégration OAK complète.
