# Ω-AUTO² MaxCap Capability Map

## But

Définir les capacités maximales de Ω-AUTO²-Kernel, mesurer leurs limites et proposer des dépassements contrôlés qui augmentent la puissance sans casser OAK.

## Principe

Une capacité n'est pas seulement une action possible. C'est une action avec :

- objectif clair;
- entrées et sorties définies;
- niveau de confiance;
- coût borné;
- permissions minimales;
- rollback ou validation humaine;
- preuve de valeur.

## Capacity Vector

Chaque workflow reçoit un vecteur :

```text
C = [scope, autonomy, reversibility, safety, usefulness, reliability, cost_control, learning, integration, value_creation]
```

Toutes les dimensions sont entre 0 et 1.

## Niveaux de capacité

| Niveau | Nom | Définition | Autorisation |
|---|---|---|---|
| C0 | inert | description seulement | aucun effet |
| C1 | draft | génère un brouillon | écriture locale/draft |
| C2 | dry-run | simule actions et diff | aucun effet externe |
| C3 | local | écrit artefacts locaux | rollback obligatoire |
| C4 | connected-draft | prépare PR/draft/email draft | validation humaine |
| C5 | controlled-action | action réelle bornée | approbation explicite |
| C6 | self-healing | corrige automatiquement erreurs faibles | budget/rollback strict |
| C7 | generator | génère de nouveaux workflows | sandbox obligatoire |
| C8 | ecosystem | orchestre plusieurs agents | Trust Kernel + OAKBench |

## Dépassement OAK-safe

Un dépassement est permis seulement si :

```text
capability_after > capability_before
AND oak_score_after >= oak_score_before
AND anti_chaos_after >= anti_chaos_before
AND red_locks_violated = 0
```

## Red Locks

Aucun dépassement automatique pour :

- suppression de données;
- publication publique;
- email externe;
- transfert d'argent;
- modification de permissions;
- divulgation IP;
- engagement légal;
- décision médicale;
- expérimentation physique risquée.

## Axes plus ultra

1. Génération automatique de workflows à partir d'une friction.
2. Génération automatique de tests pour chaque workflow.
3. Génération automatique d'OAKBench.
4. Mesure de valeur réelle par Proof-of-Workflow.
5. Regenerator qui propose améliorations sans augmenter le risque.
6. Capability Ledger pour savoir ce que chaque agent peut faire.
7. Trust Kernel pour décider ce qui reste draft, dry-run ou contrôlé.
8. Anti-Chaos Index pour couper les automatisations qui créent du bruit.

## Définition du succès

AUTO² dépasse ses capacités quand il produit plus d'artefacts vérifiés, moins d'étapes manuelles, moins d'erreurs, moins de chaos et plus de valeur mesurée, sans réduire la souveraineté humaine.
