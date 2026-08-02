# M− — Baseline synthétique R0.3 imparfaite

## Observation

Sur 8 388 608 scénarios synthétiques couvrant bruit, marqueurs manquants, contre-signatures et abstention, la baseline atteint 64,3157 % de précision hors abstention avec 80,3862 % de couverture.

## Interprétation correcte

- ce résultat n'est pas une performance chimique;
- le modèle synthétique agrège encore trop brutalement les niveaux de bruit, de source et de contradiction;
- la confiance numérique n'est pas encore calibrée par famille et modalité;
- une règle familiale large confond plusieurs sous-familles et environnements;
- l'abstention améliore la sécurité mais doit être optimisée séparément de l'exactitude.

## Anti-règles

1. ne pas augmenter artificiellement la précision en simplifiant le benchmark;
2. publier précision, couverture, abstention et métriques par strate ensemble;
3. séparer données de réglage et données de validation;
4. comparer aux baselines nearest-rule, probabiliste et mélange;
5. ne pas promouvoir un modèle sur données réelles à partir de ce benchmark synthétique.

## Action R0.4

Ajouter calibration par modalité, coûts asymétriques des erreurs, reconnaissance de l'inconnu, références expérimentales ouvertes et validation externe.
