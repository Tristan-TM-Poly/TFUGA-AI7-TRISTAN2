# Ω-PCT∞ — Frontière 100k+ sans plafond arbitraire

`100000` est un test de charge possible, jamais une constante de vérité ni une limite permanente. Le flux synthétique peut continuer indéfiniment; chaque exécution est arrêtée par un budget réel.

## Contrôleur

```text
source lazy → lot adaptatif → schéma → déduplication → qualité → sérialisation
            ↘ télémétrie ↘ M⁻ ↘ checkpoint ↘ backpressure ↘ redesign
```

## Budgets admissibles

- temps mural;
- mémoire résidente;
- espace disque et taille de shard;
- quotas GitHub/API/CI;
- coûts monétaires et énergétiques;
- nombre d'échecs consécutifs;
- qualité minimale;
- temps maximal de rollback;
- risque de divulgation IP;
- taux de duplication;
- couverture de tests.

## Réactions à saturation

| Saturation | Réaction immédiate | Redesign possible |
|---|---|---|
| mémoire | réduire lot, libérer cache | streaming, index disque, partitionnement |
| taille de commit | fermer shard | arbres Git, commits hiérarchiques, manifestes |
| CI | route différentielle | matrices, cache, échantillonnage + preuve |
| API | backoff et checkpoint | files, batch API, fenêtres de quota |
| qualité | quarantaine | validateurs spécialisés, active learning |
| duplication | registre de hash | signatures sémantiques, canonicalisation |
| coût | StopGate | budgets par valeur marginale |
| rollback | bloquer promotion | commits atomiques, canary, preuve de restauration |

## Règle scientifique

La génération de 10 000, 100 000 ou 10 millions de candidats n'augmente pas leur probabilité de vérité. Elle augmente l'espace exploré. La couche OAK doit donc croître avec la génération : provenance, contrôles négatifs, correction du multiple testing, réplication et mémoire négative.
