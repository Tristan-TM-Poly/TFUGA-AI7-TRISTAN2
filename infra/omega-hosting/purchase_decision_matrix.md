# Ω-HOSTING-T — matrice décisionnelle d'achat Hostinger KVM 8

## Verdict technique

Le plan KVM 8 est pertinent pour :

- n8n ;
- webhooks ;
- API légères ;
- agents AIT légers ;
- orchestration GitHub ;
- petits dashboards ;
- prototypes serveur.

Il n'est pas destiné à :

- GPU ;
- gros modèles locaux ;
- données hautement sensibles sans chiffrement ;
- base critique unique ;
- autonomie externe sans approbation.

## Feu vert / feu rouge

| Condition | Feu |
|---|---|
| GitHub workflows verts | vert |
| Runbook présent | vert |
| Bootstrap prudent | vert |
| Pas de valeurs privées dans Git | vert |
| Prix final non vérifié | jaune |
| Renouvellement non vérifié | jaune |
| Backups Hostinger non vérifiés | jaune |
| OS autre que Ubuntu 24.04 | jaune/rouge |
| Intention de stocker données critiques sans plan | rouge |
| Intention d'automatiser emails/paiements sans approbation | rouge |

## Décision finale

```text
Acheter = seulement si vert technique + budget réel accepté + OS Ubuntu 24.04 + stratégie backup.
```

## Après achat

Ouvrir l'issue template `Ω-HOSTING-T / VPS intake` avec seulement les détails non sensibles.
