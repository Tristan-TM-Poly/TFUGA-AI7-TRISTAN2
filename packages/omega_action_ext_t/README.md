# omega_action_ext_t

MVP **plus ultra** de **Ω-ACTION-EXT-T / Actions Externes de Tristan**.

Ce package transforme une intention d'action externe en objet vérifiable :

```text
Intent → ActionDNA → RiskTensor → OAKGate → DryRunReport → ActionManifest → ApprovalQueue → ProofLedger → M⁺/M⁻
```

## Principe

> Automatiser l'action, pas automatiser l'irresponsabilité.

Le comportement par défaut est prudent :

- `send_email` sans approbation devient `ALLOW_DRAFT`, pas envoi direct ;
- action publique avec IP non approuvée devient `NEEDS_APPROVAL` ;
- risque critique devient `REQUIRE_EXPERT` ou `BLOCK` ;
- action faible risque et réversible peut devenir `ALLOW_AUTO` ;
- action destructive sans rollback est bloquée ;
- les connecteurs du MVP sont **dry-run-only**.

## Modules

| Module | Rôle |
|---|---|
| `core.py` | `ActionDNA`, `RiskTensor`, décisions, rapports |
| `policy.py` | `OAKGate` conservateur |
| `manifest.py` | manifeste hashé et reviewable |
| `approval_queue.py` | file locale d'approbation souveraine |
| `ledger.py` | ledger JSONL append-only avec hash chain |
| `incident_codex.py` | mémoire négative M⁻ en anti-règles testables |
| `oakbench.py` | scoring heuristique de sûreté/fertilité |
| `connectors/` | plans de connecteurs sans mutation externe |

## Exemple CLI

```bash
python -m omega_action_ext_t.cli examples/professor_outreach.json
```

Sortie attendue : un rapport JSON indiquant la décision OAK, les raisons, les garde-fous et la preuve attendue.

## Exemple Python

```python
from omega_action_ext_t import ActionDNA, ActionManifest, RiskTensor, OAKGate, score_report

action = ActionDNA(
    name="Contact professor",
    system="gmail",
    action_type="send_email",
    risk=RiskTensor(ip=2, reputation=2, privacy=1),
    touches_humans=True,
    touches_ip=True,
    approved=False,
)

manifest = ActionManifest.compile(action, OAKGate())
print(manifest.dry_run.decision.value)
# allow_draft

print(score_report(manifest.dry_run).to_dict())
```

## Statut OAK

Prototype local/canonique. Aucune exécution externe réelle n'est incluse dans ce MVP. Les connecteurs doivent rester `dry-run-first` jusqu'à intégration OAK complète : manifeste approuvé, scopes minimaux, ledger, preuve d'exécution, rollback/compensation et M⁻.
